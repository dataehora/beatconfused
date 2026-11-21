// Student V4 voice effects (SPEC R3V4 item 6; R4V4 item 4: expander, feedback notches, pitch tracker): the microphone played together with the keyboard.
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
  void lowpass(float fc, float q) {
    float w = 2.0f * (float)M_PI * fc / AUDIO_SAMPLE_RATE_EXACT;
    float alpha = sinf(w) / (2.0f * q);
    float a0 = 1.0f + alpha, c = cosf(w);
    b0 = (1.0f - c) * 0.5f / a0; b1 = (1.0f - c) / a0; b2 = b0;
    a1 = -2.0f * c / a0; a2 = (1.0f - alpha) / a0;
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
// Microphone conditioning (R4V4): high-pass, gain, up to NOTCHES feedback notches, and a
// downward EXPANDER (noise gate with a soft knee) whose job is to let through only a voice
// from a microphone very close to the mouth: the speaker's sound reaching the capsule
// from a distance is far quieter, stays under the threshold and is expanded away.
//   threshold  level (int16 units, on the rectified, smoothed signal) above which all passes
//   ratio      below it the gain falls as (level / threshold)^n: n = 1 (gentle) .. 6 (hard gate)
//   attack     time the gain takes to open (ms)         hold   time it stays open after the
//   release    time it takes to close again (ms)        level falls under the threshold (ms)
// The notches are set by the feedback watcher (FeedbackWatch, below).
class VoiceInput : public AudioStream {
public:
  static const int NOTCHES = 4;
  VoiceInput() : AudioStream(1, queue) {
    setHighpass(90.0f);
    setExpander(250.0f, 2, 2.0f, 80.0f, 150.0f);
    for (int i = 0; i < NOTCHES; i++) clearNotch(i);
  }
  void setActive(bool on) { active = on; }
  void setGain(float g) { gain = g; }
  void setHighpass(float hz) {
    Biquad b; b.highpass(hz, 0.707f);
    AudioNoInterrupts();
    hpc[0] = b.b0; hpc[1] = b.b1; hpc[2] = b.b2; hpc[3] = b.a1; hpc[4] = b.a2;
    AudioInterrupts();
  }
  // n: 0..3 = expansion power 1, 2, 3, 6 (the last one is a hard gate)
  void setExpander(float thr, int n, float attackMs, float holdMs, float releaseMs) {
    static const uint8_t power[4] = {1, 2, 3, 6};
    float fs = AUDIO_SAMPLE_RATE_EXACT;
    AudioNoInterrupts();
    thrOpen = thr < 1.0f ? 1.0f : thr;
    invThr = 1.0f / thrOpen;
    expN = power[n < 0 ? 0 : (n > 3 ? 3 : n)];
    kAtk = 1.0f - expf(-1000.0f / (attackMs * fs));
    kRel = 1.0f - expf(-1000.0f / (releaseMs * fs));
    holdSamples = (int32_t)(holdMs * fs / 1000.0f);
    AudioInterrupts();
  }
  // Feedback notch i: peaking filter of -depthDb at fc (Q 30); depthDb <= 0.1 switches it off.
  void setNotch(int i, float fc, float depthDb) {
    if (i < 0 || i >= NOTCHES) return;
    if (depthDb < 0.1f) { clearNotch(i); return; }
    float w = 2.0f * (float)M_PI * fc / AUDIO_SAMPLE_RATE_EXACT;
    float alpha = sinf(w) / (2.0f * 30.0f);
    float A = powf(10.0f, -depthDb / 40.0f);
    float c = cosf(w), a0 = 1.0f + alpha / A;
    AudioNoInterrupts();
    nc[i][0] = (1.0f + alpha * A) / a0; nc[i][1] = -2.0f * c / a0; nc[i][2] = (1.0f - alpha * A) / a0;
    nc[i][3] = -2.0f * c / a0;          nc[i][4] = (1.0f - alpha / A) / a0;
    nOn |= 1u << i;
    AudioInterrupts();
  }
  void clearNotch(int i) {
    AudioNoInterrupts();
    nc[i][0] = 1; nc[i][1] = nc[i][2] = nc[i][3] = nc[i][4] = 0;
    nz[i][0] = nz[i][1] = 0;
    nOn &= ~(1u << i);
    AudioInterrupts();
  }
  bool isOpen() const { return gateGain > 0.5f; }   // for the screen
  virtual void update(void) {
    audio_block_t *in = receiveReadOnly(0);
    if (!in) return;
    if (!active) { release(in); return; }
    audio_block_t *out = allocate();
    if (!out) { release(in); return; }
    float z1 = hz1, z2 = hz2;
    float e = env, g = gateGain;
    int32_t hold = holdLeft;
    const float b0 = hpc[0], b1 = hpc[1], b2 = hpc[2], a1 = hpc[3], a2 = hpc[4];
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      float x = in->data[i];
      float y = b0 * x + z1;
      z1 = b1 * x - a1 * y + z2;
      z2 = b2 * x - a2 * y;
      for (uint32_t m = nOn; m; m &= m - 1) {              // feedback notches (none most of the time)
        int k = __builtin_ctz(m);
        float yn = nc[k][0] * y + nz[k][0];
        nz[k][0] = nc[k][1] * y - nc[k][3] * yn + nz[k][1];
        nz[k][1] = nc[k][2] * y - nc[k][4] * yn;
        y = yn;
      }
      y *= gain;
      float a = fabsf(y);
      e += (a - e) * (a > e ? 0.02f : 0.0008f);          // ~1 ms attack, ~25 ms release
      float target;
      if (e >= thrOpen) { target = 1.0f; hold = holdSamples; }
      else if (hold > 0) { hold--; target = 1.0f; }
      else {
        float r = e * invThr;
        target = r;
        for (int n = 1; n < expN; n++) target *= r;
      }
      g += (target - g) * (target > g ? kAtk : kRel);
      out->data[i] = toS16(y * g);
    }
    if (fabsf(z1) < 1e-15f) z1 = 0;
    if (fabsf(z2) < 1e-15f) z2 = 0;
    hz1 = z1; hz2 = z2;
    for (uint32_t m = nOn; m; m &= m - 1) {
      int k = __builtin_ctz(m);
      if (fabsf(nz[k][0]) < 1e-15f) nz[k][0] = 0;
      if (fabsf(nz[k][1]) < 1e-15f) nz[k][1] = 0;
    }
    env = e; gateGain = g; holdLeft = hold;
    transmit(out);
    release(out);
    release(in);
  }
private:
  audio_block_t *queue[1];
  float hpc[5], nc[NOTCHES][5], nz[NOTCHES][2];
  float hz1 = 0, hz2 = 0;
  volatile uint32_t nOn = 0;
  float gain = 1.0f, thrOpen = 250.0f, invThr = 0.004f, kAtk = 0.01f, kRel = 0.001f;
  int32_t holdSamples = 3500, holdLeft = 0;
  uint8_t expN = 3;
  float env = 0, gateGain = 0;
  volatile bool active = false;
};

// ---------------------------------------------------------------------------------------
// Pitch tracker for the voice (YIN, de Cheveigne and Kawahara 2002), for the harmonizer that
// follows the keys. It only listens (no output). The voice is low-passed at 1.8 kHz and
// decimated by 4 (11 kHz), then every HOP samples a window of W samples is searched for its
// period (lag 12..LAG_MAX = 920 .. 79 Hz). Cost: W x LAG_MAX = 27 k multiply-adds per 17.4 ms
// (estimate: about 1 % of the CPU at 396 MHz), latency: the window (17 ms) + up to one hop.
// pitch() = Hz of the voice (median of the last three frames), 0 = no pitched voice.
class PitchTracker : public AudioStream {
public:
  PitchTracker() : AudioStream(1, queue) { lp.lowpass(1800.0f, 0.707f); }
  void setActive(bool on) {
    if (on && !active) { memset(ring, 0, sizeof(ring)); f0 = 0; h[0] = h[1] = h[2] = 0; blocks = 0; lp.clearState(); }
    if (!on) f0 = 0;
    active = on;
  }
  float pitch() const { return f0; }
  uint32_t frames() const { return frameCount; }
  virtual void update(void) {
    audio_block_t *in = receiveReadOnly(0);
    if (!in) return;
    if (!active) { release(in); return; }
    Biquad f = lp;
    uint32_t w = wr;
    for (int i = 0; i < AUDIO_BLOCK_SAMPLES; i++) {
      float x = in->data[i];
      float y = f.b0 * x + f.z1;
      f.z1 = f.b1 * x - f.a1 * y + f.z2;
      f.z2 = f.b2 * x - f.a2 * y;
      if ((i & 3) == 3) ring[w++ & (RING - 1)] = y;
    }
    f.flush();
    lp.z1 = f.z1; lp.z2 = f.z2;
    wr = w;
    release(in);
    if (++blocks >= HOP / (AUDIO_BLOCK_SAMPLES / 4)) { blocks = 0; analyse(); }
  }
private:
  static const int W = 192, LAG_MAX = 140, LAG_MIN = 12, HOP = 192, RING = 512, N = W + LAG_MAX;
  void analyse() {
    float lin[N];
    uint32_t start = wr - N;
    float energy = 0;
    for (int i = 0; i < N; i++) lin[i] = ring[(start + i) & (RING - 1)];
    for (int i = N - W; i < N; i++) energy += lin[i] * lin[i];
    frameCount++;
    float cur = 0;
    if (energy / W > 60.0f * 60.0f) {                     // some signal (int16 rms 60)
      float dp[LAG_MAX + 1];
      float running = 0;
      dp[0] = 1.0f;
      for (int t = 1; t <= LAG_MAX; t++) {
        float s = 0;
        for (int j = 0; j < W; j++) { float d = lin[j] - lin[j + t]; s += d * d; }
        running += s;
        dp[t] = running > 0 ? s * t / running : 1.0f;
      }
      int best = -1;
      for (int t = LAG_MIN; t < LAG_MAX; t++) {
        if (dp[t] < 0.15f) {
          while (t + 1 < LAG_MAX && dp[t + 1] < dp[t]) t++;
          best = t;
          break;
        }
      }
      if (best < 0) {                                     // no clear dip: the deepest, if reasonably deep
        float m = 0.30f;
        for (int t = LAG_MIN; t < LAG_MAX; t++) if (dp[t] < m) { m = dp[t]; best = t; }
      }
      if (best > 0) {
        float s0 = dp[best - 1], s1 = dp[best], s2 = dp[best + 1 <= LAG_MAX ? best + 1 : best];
        float den = s0 - 2.0f * s1 + s2;
        float tau = best + (fabsf(den) > 1e-9f ? 0.5f * (s0 - s2) / den : 0.0f);
        cur = (AUDIO_SAMPLE_RATE_EXACT / 4.0f) / tau;
      }
    }
    h[0] = h[1]; h[1] = h[2]; h[2] = cur;
    // median of three; 0 (no voice) counts as a value: two unvoiced frames out of three = unvoiced
    float a = h[0], b = h[1], c = h[2];
    f0 = max(min(a, b), min(max(a, b), c));
  }
  audio_block_t *queue[1];
  Biquad lp;
  float ring[RING] = {0};
  uint32_t wr = 0;
  int blocks = 0;
  float h[3] = {0, 0, 0};
  volatile float f0 = 0;
  volatile uint32_t frameCount = 0;
  volatile bool active = false;
};

// ---------------------------------------------------------------------------------------
// Automatic feedback suppressor (R4V4 study). A 1024-point FFT of the voice (43 Hz bins, a new
// one every 11.6 ms, from AudioAnalyzeFFT1024) is watched for a narrow peak that stays on the
// same bin and either keeps growing (a feedback loop with gain above 1) or is far above the
// rest of the spectrum for ~0.5 s. The peak's frequency (parabolic interpolation) gets a notch
// of -18 dB (Q 30) in VoiceInput; seeing it again deepens that notch by 6 dB (to -36 dB).
// Up to VoiceInput::NOTCHES notches, the oldest replaced. Singing a pure sustained note can
// trip it (a narrow hole in a voice is barely audible): the menu can switch it off.
struct FeedbackWatch {
  static const int N = VoiceInput::NOTCHES;
  float freq[N] = {0};
  float depth[N] = {0};
  int next = 0;
  int trackBin = -1, trackCount = 0, cooldown = 0, misses = 0;
  float trackStartMag = 0;
  void clear() { for (int i = 0; i < N; i++) { freq[i] = 0; depth[i] = 0; } next = 0; trackBin = -1; trackCount = 0; }
  // mag: the 512 magnitudes of one FFT frame (0..1). Returns the notch to apply (index), or -1.
  int feed(const float *mag) {
    const int LO = 7, HI = 163;                           // 300 Hz .. 7 kHz
    if (cooldown > 0) { cooldown--; return -1; }
    int pk = LO;
    float sum = 0;
    for (int i = LO; i <= HI; i++) { sum += mag[i]; if (mag[i] > mag[pk]) pk = i; }
    float mean = (sum - mag[pk]) / (HI - LO);
    float par = mag[pk] / (mean + 1e-9f);                 // peak to average
    if (mag[pk] < 0.004f || par < 8.0f) {                 // nothing peaky: forget the track after a few misses
      if (++misses > 3) { trackBin = -1; trackCount = 0; }
      return -1;
    }
    misses = 0;
    if (trackBin >= 0 && abs(pk - trackBin) <= 1) { trackCount++; trackBin = pk; }
    else { trackBin = pk; trackCount = 1; trackStartMag = mag[pk]; }
    bool grows = trackCount >= 10 && mag[pk] > 1.8f * trackStartMag;
    bool steady = trackCount >= 40 && par > 30.0f;
    if (!grows && !steady) return -1;
    float a = logf(mag[pk - 1] + 1e-9f), b = logf(mag[pk] + 1e-9f), c = logf(mag[pk + 1] + 1e-9f);
    float den = a - 2.0f * b + c;
    float delta = fabsf(den) > 1e-9f ? 0.5f * (a - c) / den : 0.0f;
    float f = (pk + constrain(delta, -0.5f, 0.5f)) * (AUDIO_SAMPLE_RATE_EXACT / 1024.0f);
    trackBin = -1; trackCount = 0; cooldown = 20;
    for (int i = 0; i < N; i++) {                         // already notched: deepen it
      if (depth[i] > 0 && fabsf(freq[i] - f) < max(40.0f, f / 40.0f)) {
        depth[i] = min(depth[i] + 6.0f, 36.0f);
        return i;
      }
    }
    int i = next;
    next = (next + 1) % N;
    freq[i] = f; depth[i] = 18.0f;
    return i;
  }
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
