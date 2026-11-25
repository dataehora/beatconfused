// Sampled accordion reeds: one object per voice plays the four reed ranks
// (16', 8', 8' second reed, 4') from looped recordings and mixes them by
// the register's gains.
//
// The recordings are in reed_samples.cpp / reed_samples.h, written by
// tools/accordion_samples/build_samples.py. Those two files are not in the
// repository; without them the sketch still builds and the accordion uses
// the synthesised reed tables instead.
#pragma once
#include <Arduino.h>
#include <AudioStream.h>

#define REED_RANKS 4

struct ReedSample {
  const int16_t *data;   // the note's start, then the loop, then 3 repeated samples
  uint32_t loopEnd;      // index one past the loop's last sample
  uint32_t loopStart;
  float rootNote;        // pitch of the recording, as a fractional MIDI note
  float rate;            // sample rate of the data
};

#if __has_include("reed_samples.h")
#include "reed_samples.h"
extern const ReedSample reedSamples[REED_RANKS][REED_SAMPLES_PER_RANK];
#else
#define REED_SAMPLES_PER_RANK 0
#endif

class ReedSampler : public AudioStream {
public:
  ReedSampler() : AudioStream(0, NULL) {}

  // Starts the four ranks for a key. `note` is the 8' pitch; the 16' rank
  // plays an octave below, the 4' an octave above, and the second 8' reed
  // `wetCents` sharp. `level` is the loudness (0..1) and `brightnessHz` the
  // corner of the low-pass that follows the mix: together they stand for
  // the bellows pressure, which makes a reed both louder and brighter.
  void noteOn(float note, float wetCents, float level, float brightnessHz) {
    __disable_irq();
    for (int r = 0; r < REED_RANKS; r++) {
      rank[r].sample = pick(r, rankNote(r, note, wetCents));
      rank[r].pos = 0;
    }
    setIncrements(note, wetCents);
    this->level = level;
    lowpass = 1.0f - expf(-2.0f * PI * brightnessHz / AUDIO_SAMPLE_RATE_EXACT);
    blocksLeft = 0;
    active = REED_SAMPLES_PER_RANK > 0;
    __enable_irq();
  }

  // Keeps playing for `ms` more (the bellows envelope's release), then stops.
  void noteOff(float ms) {
    blocksLeft = (uint32_t)(ms * AUDIO_SAMPLE_RATE_EXACT / 1000.0f / AUDIO_BLOCK_SAMPLES) + 2;
  }

  void stop() { active = false; }

  // New tuning for the note already sounding (the tremolo amount changed).
  void retune(float note, float wetCents) {
    __disable_irq();
    setIncrements(note, wetCents);
    __enable_irq();
  }

  void gain(int r, float g) { rank[r].gain = g; }

  virtual void update(void) {
    if (!active) return;
    audio_block_t *block = allocate();
    if (!block) return;
    float sum[AUDIO_BLOCK_SAMPLES];
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) sum[i] = 0.0f;

    for (int r = 0; r < REED_RANKS; r++) {
      Rank &k = rank[r];
      if (!k.sample) continue;
      const uint64_t end = (uint64_t)k.sample->loopEnd << 32;
      const uint64_t loop = (uint64_t)(k.sample->loopEnd - k.sample->loopStart) << 32;
      uint64_t pos = k.pos;
      const float g = k.gain * level;
      if (g <= 0.0f) {
        // A rank the register leaves out only keeps its place in the loop,
        // so it is in step if the register brings it in mid-note.
        pos += k.inc * AUDIO_BLOCK_SAMPLES;
        while (pos >= end) pos -= loop;
        k.pos = pos;
        continue;
      }
      const int16_t *d = k.sample->data;
      for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
        uint32_t n = pos >> 32;
        float t = (uint32_t)pos * (1.0f / 4294967296.0f);
        float p0 = d[n ? n - 1 : 0], p1 = d[n], p2 = d[n + 1], p3 = d[n + 2];
        // Catmull-Rom interpolation between p1 and p2
        float v = p1 + 0.5f * t * (p2 - p0 + t * (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3
                  + t * (3.0f * (p1 - p2) + p3 - p0)));
        sum[i] += g * v;
        pos += k.inc;
        if (pos >= end) pos -= loop;
      }
      k.pos = pos;
    }

    float y = filtered;
    const float a = lowpass;
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      y += a * (sum[i] - y);
      float v = y;
      block->data[i] = v > 32767.0f ? 32767 : (v < -32767.0f ? -32767 : (int16_t)v);
    }
    filtered = y;
    transmit(block);
    release(block);
    if (blocksLeft && --blocksLeft == 0) active = false;
  }

private:
  struct Rank {
    const ReedSample *sample = nullptr;
    uint64_t pos = 0;      // 32.32 fixed point, in samples of the recording
    uint64_t inc = 0;
    float gain = 0.0f;
  };
  Rank rank[REED_RANKS];
  float level = 1.0f;
  float lowpass = 1.0f;    // one-pole coefficient, 1 = no filtering
  float filtered = 0.0f;
  volatile bool active = false;
  volatile uint32_t blocksLeft = 0;

  static float rankNote(int r, float note, float wetCents) {
    if (r == 0) return note - 12.0f;
    if (r == 2) return note + wetCents / 100.0f;
    if (r == 3) return note + 12.0f;
    return note;
  }

  // The recording closest in pitch, so it is shifted as little as possible.
  static const ReedSample *pick(int r, float note) {
#if REED_SAMPLES_PER_RANK > 0
    const ReedSample *best = &reedSamples[r][0];
    for (int i = 1; i < REED_SAMPLES_PER_RANK; i++) {
      const ReedSample *s = &reedSamples[r][i];
      if (fabsf(s->rootNote - note) < fabsf(best->rootNote - note)) best = s;
    }
    return best;
#else
    return nullptr;
#endif
  }

  void setIncrements(float note, float wetCents) {
    for (int r = 0; r < REED_RANKS; r++) {
      const ReedSample *s = rank[r].sample;
      if (!s) continue;
      float ratio = s->rate / AUDIO_SAMPLE_RATE_EXACT
                    * powf(2.0f, (rankNote(r, note, wetCents) - s->rootNote) / 12.0f);
      rank[r].inc = (uint64_t)((double)ratio * 4294967296.0);
    }
  }
};
