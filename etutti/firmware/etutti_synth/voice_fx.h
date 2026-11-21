// Student V4 voice effects (SPEC R3V4, item 6): the microphone played together with the keyboard.
//
// The Teensy Audio Library has no vocoder, so the three objects below are our own:
//   VoiceInput  - the codec's microphone: high-pass, gain, noise gate (so an idle
//                 microphone adds neither hiss to the vocoder nor feedback to the speaker).
//   VocoderFx   - channel vocoder: the voice shapes the keyboard (two inputs: voice, keyboard).
//   VoiceEcho   - echo with a darkening feedback loop, in a buffer of its own.
// The pitch shifter ("harmonizer") is the library's AudioEffectGranular, the reverb is the
// keyboard's own AudioEffectFreeverb (the voice is sent into it), the mixes are AudioMixer4.
//
// All the filters are float biquads (never the library's state-variable filter: it went
// unstable near its top frequency). Written for the Cortex-M7's FPU; with the loops
// band-outer the filter states stay in registers for the whole 128-sample block.
// Nothing here has run on a board: CPU figures are estimates (see student_v04/FIRMWARE.md).
#pragma once
#include <Arduino.h>
#include <AudioStream.h>
#include <math.h>

namespace vfx {

// Second-order sections in transposed direct form II. Coefficients from the RBJ cookbook.
struct Biquad {
  float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0, z1 = 0, z2 = 0;
  void bandpass(float fc, float q) {            // constant 0 dB peak gain
    float w = 2.0f * (float)M_PI * fc / AUDIO_SAMPLE_RATE_EXACT;
    float alpha = sinf(w) / (2.0f * q);
    float a0 = 1.0f + alpha;
    b0 = alpha / a0; b1 = 0; b2 = -alpha / a0;
    a1 = -2.0f * cosf(w) / a0; a2 = (1.0f - alpha) / a0;
  }
  void highpass(float fc, float q) {
    float w = 2.0f * (float)M_PI * fc / AUDIO_SAMPLE_RATE_EXACT;
    float alpha = sinf(w) / (2.0f * q);
    float a0 = 1.0f + alpha, c = cosf(w);
    b0 = (1.0f + c) * 0.5f / a0; b1 = -(1.0f + c) / a0; b2 = b0;
    a1 = -2.0f * c / a0; a2 = (1.0f - alpha) / a0;
  }
  void clearState() { z1 = z2 = 0; }
  void flush() { if (fabsf(z1) < 1e-15f) z1 = 0; if (fabsf(z2) < 1e-15f) z2 = 0; }   // no subnormals
};

inline int16_t toS16(float x) {
  if (x > 32767.0f) return 32767;
  if (x < -32768.0f) return -32768;
  return (int16_t)x;
}

// Gentle limiter for the vocoder's sum (a loud voice over a loud chord): linear up to
// 20000, then a knee that approaches full scale instead of clipping flat.
inline float softLimit(float x) {
  float a = fabsf(x);
  if (a <= 20000.0f) return x;
  float over = a - 20000.0f;
  float y = 20000.0f + over / (1.0f + over * (1.0f / 12768.0f));
  return x < 0 ? -y : y;
}

// ---------------------------------------------------------------------------------------
// Microphone conditioning: 90 Hz high-pass, gain, gate.
class VoiceInput : public AudioStream {
public:
  VoiceInput() : AudioStream(1, queue) { hp.highpass(90.0f, 0.707f); }
  void setActive(bool on) { active = on; }
  void setGain(float g) { gain = g; }
  // Gate: opens above `open` (int16 units, on the rectified, smoothed signal), closes under 60 % of it.
  void setGate(float open) { openAt = open; closeAt = open * 0.6f; }
  virtual void update(void) {
    audio_block_t *in = receiveReadOnly(0);
    if (!in) return;
    if (!active) { release(in); return; }
    audio_block_t *out = allocate();
    if (!out) { release(in); return; }
    Biquad f = hp;
    float e = env, g = gateGain;
    bool op = open;
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      float x = in->data[i];
      float y = f.b0 * x + f.z1;
      f.z1 = f.b1 * x - f.a1 * y + f.z2;
      f.z2 = f.b2 * x - f.a2 * y;
      y *= gain;
      float a = fabsf(y);
      e += (a - e) * (a > e ? 0.02f : 0.0008f);          // ~1 ms attack, ~25 ms release
      if (!op && e > openAt) op = true;
      else if (op && e < closeAt) op = false;
      g += ((op ? 1.0f : 0.0f) - g) * (op ? 0.01f : 0.0015f);   // ~2 ms open, ~15 ms close
      out->data[i] = toS16(y * g);
    }
    f.flush();
    hp = f; env = e; gateGain = g; open = op;
    transmit(out);
    release(out);
    release(in);
  }
private:
  audio_block_t *queue[1];
  Biquad hp;
  float gain = 1.0f, openAt = 150.0f, closeAt = 90.0f;
  float env = 0, gateGain = 0;
  bool open = false;
  volatile bool active = false;
};

// ---------------------------------------------------------------------------------------
// Channel vocoder. Input 0 = modulator (the voice), input 1 = carrier (the keyboard).
// BANDS band-pass pairs (same centre frequencies) from 150 Hz to 5.5 kHz, log-spaced. Each
// modulator band is rectified and smoothed (fast attack, slower release); that envelope
// scales the carrier's same band. A noise burst shaped by the voice's > 5 kHz energy stands
// in for the consonants (s, t, f), which a band-pass vocoder otherwise loses.
#ifndef VOCODER_BANDS
#define VOCODER_BANDS 10
#endif
class VocoderFx : public AudioStream {
public:
  VocoderFx() : AudioStream(2, queue) {
    const float lo = 150.0f, hi = 5500.0f;
    for (int k = 0; k < VOCODER_BANDS; k++) {
      float fc = lo * powf(hi / lo, (float)k / (VOCODER_BANDS - 1));
      mod[k].bandpass(fc, 3.0f);
      car[k].bandpass(fc, 3.0f);
    }
    sibHp.highpass(5000.0f, 0.707f);
    noiseHp.highpass(5000.0f, 0.707f);
    setSpeed(4.0f, 25.0f);
  }
  void setActive(bool on) {
    if (on && !active) clearStates();
    active = on;
  }
  void setLevel(float l) { level = l; }
  // attack and release times of the envelopes, in ms
  void setSpeed(float attackMs, float releaseMs) {
    atk = 1.0f - expf(-1000.0f / (attackMs * AUDIO_SAMPLE_RATE_EXACT));
    rel = 1.0f - expf(-1000.0f / (releaseMs * AUDIO_SAMPLE_RATE_EXACT));
  }
  virtual void update(void) {
    audio_block_t *vo = receiveReadOnly(0);
    audio_block_t *ke = receiveReadOnly(1);
    if (!active || !vo || !ke) {                       // no voice or no keys: nothing to say
      if (vo) release(vo);
      if (ke) release(ke);
      return;
    }
    audio_block_t *out = allocate();
    if (!out) { release(vo); release(ke); return; }
    float xm[AUDIO_BLOCK_SAMPLES], xc[AUDIO_BLOCK_SAMPLES], acc[AUDIO_BLOCK_SAMPLES];
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      xm[i] = vo->data[i];
      xc[i] = ke->data[i];
      acc[i] = 0.0f;
    }
    const float scale = level * (1.0f / 32768.0f) * MAKEUP;
    for (int k = 0; k < VOCODER_BANDS; k++) {
      Biquad m = mod[k], c = car[k];
      float e = env[k];
      for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
        float ym = m.b0 * xm[i] + m.z1;                 // modulator band
        m.z1 = -m.a1 * ym + m.z2;
        m.z2 = -m.b0 * xm[i] - m.a2 * ym;
        float a = fabsf(ym);
        e += (a - e) * (a > e ? atk : rel);
        float yc = c.b0 * xc[i] + c.z1;                 // carrier band (b1 = 0, b2 = -b0)
        c.z1 = -c.a1 * yc + c.z2;
        c.z2 = -c.b0 * xc[i] - c.a2 * yc;
        acc[i] += yc * e;
      }
      m.flush(); c.flush();
      if (e < 1e-10f) e = 0;
      mod[k] = m; car[k] = c; env[k] = e;
    }
    // consonants: high-passed noise scaled by the voice's energy above 5 kHz
    {
      Biquad s = sibHp, n = noiseHp;
      float e = sibEnv;
      uint32_t r = rng;
      for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
        float ys = s.b0 * xm[i] + s.z1;
        s.z1 = s.b1 * xm[i] - s.a1 * ys + s.z2;
        s.z2 = s.b2 * xm[i] - s.a2 * ys;
        float a = fabsf(ys);
        e += (a - e) * (a > e ? atk : rel);
        r = r * 1664525u + 1013904223u;
        float w = (float)((int32_t)r >> 16);            // white, +-32768
        float yn = n.b0 * w + n.z1;
        n.z1 = n.b1 * w - n.a1 * yn + n.z2;
        n.z2 = n.b2 * w - n.a2 * yn;
        acc[i] += yn * e * SIBILANCE;
      }
      s.flush(); n.flush();
      if (e < 1e-10f) e = 0;
      sibHp = s; noiseHp = n; sibEnv = e; rng = r;
    }
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) out->data[i] = toS16(softLimit(acc[i] * scale));
    transmit(out);
    release(out);
    release(vo);
    release(ke);
  }
private:
  static constexpr float MAKEUP = 8.0f;      // simulated (numpy twin of this loop): a voice at 2300 rms over a chord at 4200 rms gives ~2900 rms out
  static constexpr float SIBILANCE = 0.5f;
  void clearStates() {
    for (int k = 0; k < VOCODER_BANDS; k++) { mod[k].clearState(); car[k].clearState(); env[k] = 0; }
    sibHp.clearState(); noiseHp.clearState(); sibEnv = 0;
  }
  audio_block_t *queue[2];
  Biquad mod[VOCODER_BANDS], car[VOCODER_BANDS];
  float env[VOCODER_BANDS] = {0};
  Biquad sibHp, noiseHp;
  float sibEnv = 0;
  uint32_t rng = 12345;
  float atk = 0.01f, rel = 0.001f, level = 1.0f;
  volatile bool active = false;
};

// ---------------------------------------------------------------------------------------
// Echo: the output is the delayed signal only (the mixer sets how much of it is heard).
// The repeats pass through a one-pole low-pass, so each one is darker than the last.
class VoiceEcho : public AudioStream {
public:
  VoiceEcho() : AudioStream(1, queue) {}
  // `mem` must hold `len` samples; it is cleared here.
  void begin(int16_t *mem, uint32_t len) {
    buf = mem; cap = len;
    memset(buf, 0, len * sizeof(int16_t));
    wr = 0;
    setDelayMs(300.0f);
    setFeedback(0.4f);
    setTone(3000.0f);
  }
  void setDelayMs(float ms) {
    uint32_t d = (uint32_t)(ms * AUDIO_SAMPLE_RATE_EXACT / 1000.0f);
    delaySamples = constrain(d, (uint32_t)AUDIO_BLOCK_SAMPLES, cap ? cap - 1 : (uint32_t)AUDIO_BLOCK_SAMPLES);
    updateTail();
  }
  void setFeedback(float f) { fb = constrain(f, 0.0f, 0.9f); updateTail(); }
  void setTone(float hz) { lpCoef = 1.0f - expf(-2.0f * (float)M_PI * hz / AUDIO_SAMPLE_RATE_EXACT); }
  virtual void update(void) {
    audio_block_t *in = receiveReadOnly(0);
    if (!buf) { if (in) release(in); return; }
    if (in) tail = tailBlocks;
    else if (tail > 0) tail--;
    else return;                                       // nothing sounding, nothing to do
    audio_block_t *out = allocate();
    if (!out) { if (in) release(in); return; }
    uint32_t w = wr, d = delaySamples;
    float lp = lpState;
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      uint32_t r = w >= d ? w - d : w + cap - d;
      float y = buf[r];
      lp += (y - lp) * lpCoef;
      buf[w] = toS16((in ? in->data[i] : 0) + lp * fb);
      out->data[i] = (int16_t)y;
      if (++w >= cap) w = 0;
    }
    wr = w;
    lpState = fabsf(lp) < 1e-6f ? 0 : lp;
    transmit(out);
    release(out);
    if (in) release(in);
  }
private:
  void updateTail() {                                  // blocks until the repeats fall below -60 dB
    float f = max(fb, 0.05f);
    float repeats = logf(0.001f) / logf(f);
    tailBlocks = (uint32_t)(repeats * (float)delaySamples / AUDIO_BLOCK_SAMPLES) + 4;
  }
  audio_block_t *queue[1];
  int16_t *buf = nullptr;
  uint32_t cap = 0, wr = 0, delaySamples = 13230;
  float fb = 0.4f, lpCoef = 0.3f, lpState = 0;
  uint32_t tail = 0, tailBlocks = 1000;
};

}  // namespace vfx
