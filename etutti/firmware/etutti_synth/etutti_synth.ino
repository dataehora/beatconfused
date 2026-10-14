/* ============================================================
   eTutti synth — Teensy firmware for https://beatconfused.com/etutti/

   Hardware: Teensy 4.0 + PJRC Audio Adaptor Board Rev D (SGTL5000), on
   the eTuttino PCB (etutti/hardware/). Sound comes out of the Audio
   Board's headphone jack and line out. The 44 keys are Gateron magnetic
   (Hall-effect) switches: under each one a DRV5056 sensor gives a voltage
   that rises as the key's magnet comes down. Three CD74HC4067
   multiplexers (address on pins 0-3) put the 44 sensors on three ADC pins
   (14, 15, 16), so the firmware knows how far down every key is and, from
   how fast it went down, the note's velocity. Every key plays the internal
   sound engine AND is sent over USB MIDI, so the device works standalone
   or with the web page.

   Arduino IDE + Teensyduino settings:
     Tools > Board:    Teensy 4.0
     Tools > USB Type: "MIDI" (or "Serial + MIDI" to also get Serial)

   Two sound engines, one active at a time (8 voices each):
     ACCORDION — every note sounds up to four free reeds, switched by the
       register (as on a real accordion):
         16'  low reed, in cassotto          (one octave down)
         8' M1 middle reed, open ("simple")
         8' M2 middle reed, in cassotto      (detuned by the "wet" amount)
         4'  piccolo reed, open              (one octave up)
       Each reed plays a waveform built by additive synthesis from a free
       reed's harmonic spectrum (bright when open, rounder in cassotto),
       band-limited to stay clear of aliasing — the raw saw/square of a
       basic synth is what made the old sound metallic.
     SAMPLES — real recorded instruments via AudioSynthWavetable: piano,
       nylon guitar, and the guitar's low strings two octaves down as an
       acoustic-bass stand-in (sample sets from the Teensy Audio Library's
       MidiSynthLarge example).
     SYNTH — a classic subtractive synth reusing three of each voice's
       oscillators: per oscillator a waveform (sine, triangle, and
       band-limited saw / square — never the raw ones, which alias and
       sound metallic), level, detune and octave, through a full ADSR.
   All feed a tone (low-pass) filter and a light room reverb. The tone
   filter is a biquad: the state-variable filter used before went unstable
   near its top frequency and turned piano/guitar (tone wide open) into
   full-scale noise.

   MIDI implementation (any channel; keep in sync with CC in etutti/script.js):
     Note On / Note Off      play / release (velocity -> loudness)
     CC 7   Volume           headphone volume
     CC 9   Key velocity     value / 32: 0 fixed (100), 1 soft, 2 normal, 3 hard
     CC 14  Calibrate keys   64-127: forget the learnt key travel, learn it again
     CC 15  Key test         64-127: stream every key's position (see below)
     CC 24  Key layout       0-63 C-griff, 64-127 B-griff (the physical keys)
     CC 20-22 Synth osc 1-3 waveform  0-31 sine, 32-63 triangle, 64-95 saw, 96-127 square
     CC 25  Instrument       value / 16: 0 accordion, 1 piano, 2 bass, 3 guitar, 4 synth
     CC 28-30 Synth osc 1-3 level     0 .. 100 %
     CC 26  Register         bit mask: 1 = 16', 2 = 8' M1, 4 = 8' M2, 8 = 4'
     CC 27  Reed tuning      M2 detune in cents: 0 = dry ... 30 = very wet
     CC 72  Release          0 .. 3000 ms (accordion + synth; quadratic curve)
     CC 73  Attack           0 .. 2000 ms (accordion + synth; quadratic curve)
     CC 74  Tone             low-pass 40 Hz .. 16 kHz (exponential)
     CC 75  Decay            0 .. 2000 ms (synth; quadratic curve)
     CC 79  Sustain          0 .. 100 % (synth)
     CC 85-87 Synth osc 1-3 detune    64 = in tune, 0 / 127 = -50 / +50 cents
     CC 91  Ambience         room reverb amount
     CC 102-104 Synth osc 1-3 octave  0-42 one down, 43-84 unison, 85-127 one up
     CC 120 All sound off    instant silence
     CC 123 All notes off    release every voice
   Sent back: the keys' notes (channel 1) and, in key test mode, each key's
   position as Polyphonic Aftertouch on channel 16: data 1 = key index
   (0-43, row by row from row 1, as in etutti/hardware/build/
   etuttino_keys.csv), data 2 = 0 (up) .. 127 (bottomed out).
   ============================================================ */
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include <EEPROM.h>
#include "piano_samples.h"
#include "nylonstrgtr_samples.h"

// usbMIDI only exists when the USB Type includes MIDI. Without this check
// the compiler only says "'usbMIDI' was not declared in this scope".
#if !defined(MIDI_INTERFACE)
#error "In the Arduino IDE choose Tools > USB Type > MIDI (or Serial + MIDI), then upload again."
#endif

const int NUM_VOICES = 8;

// ---- eTuttino keys (see etutti/hardware/README.md) ----
// The notes sit on a grid of 4 rows x 12 columns (row r = accordion row
// r+1; row 1 is the one nearest the player). KEY_INPUT says where each
// key's sensor is wired: multiplexer * 16 + channel, -1 = no key there.
// build_pcb.py writes it from the channels its router picked, then checks
// the routed board against this copy. The pins stay clear of the Audio Board
// Rev D (7, 8, 18-21, 23) and of its SD card (10-13); 15 is only used by
// the Audio Board's optional volume pot, which the eTuttino doesn't fit.
const int LAYOUT_ROWS = 4;
const int LAYOUT_COLS = 12;
const int MUX_COUNT = 3;
const uint8_t MUX_SEL_PINS[4] = {0, 1, 2, 3};          // S0..S3, shared
const uint8_t MUX_COM_PINS[MUX_COUNT] = {14, 15, 16};  // A0, A1, A2
// Power LED: a red/green LED (common cathode) through 330 ohm each.
//   orange (both) while the first reading of all keys runs at power-up,
//   green while playing, red blinking on an error: the Audio Board's
//   codec didn't answer, or a key's sensor didn't (see the key test).
const uint8_t LED_PINS[2] = {4, 5};                    // red, green
const uint32_t LED_STARTUP_MS = 600;                   // orange shows at least this long
const int8_t KEY_INPUT[LAYOUT_ROWS][LAYOUT_COLS] = {
  { -1,  12,  11,  10,   9,   7,   6,   5,   4,   3,   2,   1},
  { 15,  14,  13,   8,   0,  30,  41,  42,  38,  43,  45,  46},
  { -1,  24,  25,  27,  29,  18,  17,  39,  35,  36,  44,  32},
  { -1,  23,  28,  22,  26,  31,  37,  40,  47,  34,  33,  -1},
};

// Chromatic button accordion layouts. Along a row each key is a minor
// third (+3) above the previous one. Rows 1 and 3 have 11 keys starting at
// column 1 (A3 .. D#6, G#3 .. D6); row 2 has 12 starting at column 0, half
// a key further left (G3 .. E6); row 4 sits on row 2's columns, half a key
// left of row 3, and runs A3 .. C6 (10 keys, column 1 on).
// B-griff is the mirror image of C-griff: rows 1 and 3 swap places, so a
// diagonal step goes the other way. Keep in sync with etutti/script.js.
const int8_t FIRST_NOTE[2][LAYOUT_ROWS] = {
  {57, 55, 56, 57},   // C-griff: A3, G3, G#3, A3
  {56, 55, 57, 56},   // B-griff: G#3, G3, A3, G#3
};
const uint8_t FIRST_COL[LAYOUT_ROWS] = {1, 0, 1, 1};
int layoutSystem = 0;   // 0 = C-griff, 1 = B-griff

int noteAt(int r, int c) {
  if (c < FIRST_COL[r]) return -1;
  return FIRST_NOTE[layoutSystem][r] + 3 * (c - FIRST_COL[r]);
}

// ---- Key sensing ----
// A DRV5056A3 at 3.3 V gives 0.6 V with no field plus 30 mV per mT. The
// magnet's field falls off roughly as 1/distance^3, so the key's travel is
// recovered from the cube root of the field (above the sensor's 0.6 V
// zero), scaled between that key's reading at rest and at the bottom. The
// rest reading is measured at start-up and then follows slow drift; the
// bottom is learnt from the deepest press seen and kept in EEPROM.
const int MAX_KEYS = 44;
const float ADC_PER_VOLT = 4095.0f / 3.3f;
const float SENSOR_ZERO = 0.6f * ADC_PER_VOLT;   // DRV5056 output at 0 mT
const int MIN_SPAN = 120;          // ADC counts: the least a key is assumed to swing
const float PRESENT_MIN = 0.4f * ADC_PER_VOLT;   // below this, no sensor answered
const float VEL_START = 0.12f;     // travel where the velocity timer starts
const float NOTE_ON_AT = 0.45f;    // note on (about 1.8 mm of the 4.1 mm travel)
const float NOTE_OFF_AT = 0.30f;   // note off (hysteresis against chatter)
const float FAST_MS = 1.0f;        // VEL_START -> NOTE_ON_AT (~1.4 mm) time for velocity 127
const float SLOW_MS = 80.0f;       // ... and for velocity 1
const uint8_t FIXED_VELOCITY = 100;
const uint32_t EEPROM_MAGIC = 0xE7770004;   // bump when the key count/order changes

struct Key {
  int8_t row, col;          // note grid
  uint8_t mux, channel;
  float rest;               // ADC reading with the key up
  float bottom;             // deepest reading seen
  float restInv, spanInv;   // cube-root model, see keyTravel()
  float travel;             // 0 (up) .. 1 (bottomed out)
  uint32_t prevMicros;
  uint32_t startMicros;     // when the press passed VEL_START (0 = not yet)
  bool present;             // a sensor answered at start-up
  bool down;
  int8_t note;              // note it started (survives a layout switch)
  uint8_t sentPosition;     // last position sent in key test mode
};
Key keyState[MAX_KEYS];
int keyCount = 0;
int velocityCurve = 2;      // 0 fixed, 1 soft, 2 normal, 3 hard
bool keyTest = false;
bool calibrationDirty = false;
uint32_t calibrationChangedAt = 0;
// How many physical keys hold each note (row 4 doubles row 1), so a note
// only starts on the first press and stops on the last release.
uint8_t noteHolders[128];
bool codecOk = true;
int missingKeys = 0;
// Written out so the Arduino builder doesn't put its own prototypes for
// these above the Key struct.
void resetCalibration();
void updateModel(Key &k);
float keyTravel(const Key &k, float reading);
uint32_t crossingTime(const Key &k, float prev, float now, float level, uint32_t nowMicros);

// ---- Audio graph ----
// Accordion: 4 reeds per voice -> per-voice mixer -> bellows envelope.
enum { REED_16, REED_M1, REED_M2, REED_4, NUM_REEDS };
AudioSynthWaveform       reed[NUM_REEDS][NUM_VOICES];
AudioMixer4              reedMix[NUM_VOICES];
AudioEffectEnvelope      bellows[NUM_VOICES];
AudioMixer4              accA, accB;          // voices 0-3 / 4-7
// Samples: one wavetable player per voice.
AudioSynthWavetable      sampler[NUM_VOICES];
AudioMixer4              smpA, smpB;
// Common: sum -> tone filter -> dry + reverb -> both channels.
AudioMixer4              engines;             // accA, accB, smpA, smpB
AudioFilterBiquad        toneFilter;
AudioEffectFreeverb      room;
AudioMixer4              master;              // dry, reverb
AudioOutputI2S           i2sOut;
AudioControlSGTL5000     codec;

#define REED_PATCH(v) \
  AudioConnection pr16_##v(reed[REED_16][v], 0, reedMix[v], 0); \
  AudioConnection prM1_##v(reed[REED_M1][v], 0, reedMix[v], 1); \
  AudioConnection prM2_##v(reed[REED_M2][v], 0, reedMix[v], 2); \
  AudioConnection pr4_##v(reed[REED_4][v], 0, reedMix[v], 3); \
  AudioConnection pb_##v(reedMix[v], bellows[v]);
REED_PATCH(0) REED_PATCH(1) REED_PATCH(2) REED_PATCH(3)
REED_PATCH(4) REED_PATCH(5) REED_PATCH(6) REED_PATCH(7)

AudioConnection pa0(bellows[0], 0, accA, 0);
AudioConnection pa1(bellows[1], 0, accA, 1);
AudioConnection pa2(bellows[2], 0, accA, 2);
AudioConnection pa3(bellows[3], 0, accA, 3);
AudioConnection pa4(bellows[4], 0, accB, 0);
AudioConnection pa5(bellows[5], 0, accB, 1);
AudioConnection pa6(bellows[6], 0, accB, 2);
AudioConnection pa7(bellows[7], 0, accB, 3);
AudioConnection ps0(sampler[0], 0, smpA, 0);
AudioConnection ps1(sampler[1], 0, smpA, 1);
AudioConnection ps2(sampler[2], 0, smpA, 2);
AudioConnection ps3(sampler[3], 0, smpA, 3);
AudioConnection ps4(sampler[4], 0, smpB, 0);
AudioConnection ps5(sampler[5], 0, smpB, 1);
AudioConnection ps6(sampler[6], 0, smpB, 2);
AudioConnection ps7(sampler[7], 0, smpB, 3);
AudioConnection pe0(accA, 0, engines, 0);
AudioConnection pe1(accB, 0, engines, 1);
AudioConnection pe2(smpA, 0, engines, 2);
AudioConnection pe3(smpB, 0, engines, 3);
AudioConnection pt(engines, 0, toneFilter, 0);
AudioConnection pd(toneFilter, 0, master, 0);       // dry (low-pass output)
AudioConnection pv(toneFilter, 0, room, 0);
AudioConnection pw(room, 0, master, 1);       // reverb
AudioConnection pl(master, 0, i2sOut, 0);
AudioConnection pr(master, 0, i2sOut, 1);

// ---- Reed waveforms (built at start-up, see buildReedTable) ----
int16_t tableOpen[256];       // open reed: bright, many harmonics
int16_t tableCassotto[256];   // reed in the cassotto chamber: rounder
int16_t tablePiccolo[256];    // 4' reed: open, fewer harmonics (it sounds an octave up)
// Above C5 the full tables would put harmonics past the Nyquist frequency
// (E6 is 1319 Hz: 20 harmonics = 26 kHz) and alias, which sounds metallic,
// so high reeds use tables with fewer harmonics.
const int HIGH_TABLE_FROM = 73;   // sounding notes above C5
int16_t tableOpenHigh[256];
int16_t tableCassottoHigh[256];
int16_t tablePiccoloHigh[256];

// Additive synthesis of one period of a free reed. A free reed's
// spectrum has every harmonic, falling off roughly as 1/n^k (k bigger =
// mellower, which is what the cassotto does), with a gentle formant
// ripple; the per-harmonic phases are spread so the wave has no sharp
// saw-like edge. Harmonics are capped so the top keys stay below the
// Nyquist frequency (no aliasing — the main cause of a "metallic" tone).
void buildReedTable(int16_t *table, int harmonics, float rolloff, float ripple) {
  float buf[256];
  float peak = 0;
  for (int i = 0; i < 256; i++) buf[i] = 0;
  for (int n = 1; n <= harmonics; n++) {
    float amp = powf((float)n, -rolloff) * (1.0f + ripple * cosf(n * 1.3f));
    float phase = 0.7f * n * n;
    for (int i = 0; i < 256; i++) {
      buf[i] += amp * sinf(2.0f * PI * n * i / 256.0f + phase);
    }
  }
  for (int i = 0; i < 256; i++) peak = max(peak, fabsf(buf[i]));
  for (int i = 0; i < 256; i++) table[i] = (int16_t)(buf[i] / peak * 30000.0f);
}

// ---- Voice allocation ----
struct Voice {
  int note;            // MIDI note held, or -1 when free / releasing
  int lastNote;        // note it last played (kept while releasing, for retuning)
  unsigned long age;   // allocation order, for stealing the oldest
};
Voice voices[NUM_VOICES];
unsigned long voiceCounter = 0;

// ---- Current settings — defaults = the page's "Classic accordion"
// preset: dry tuning, register MM (both 8' reeds). ----
enum { INST_ACCORDION, INST_PIANO, INST_BASS, INST_GUITAR, INST_SYNTH };
int instrument = INST_ACCORDION;
uint8_t registerMask = 0b0110;   // M1 + M2
float wetCents = 0;
float reedGain[NUM_REEDS] = {0.42f, 0.42f, 0.42f, 0.30f};

// Synth: the first three oscillators of each voice, re-purposed. Defaults
// = the page's "Synth" preset.
const int SYNTH_OSCS = 3;
const short SYNTH_WAVES[4] = { WAVEFORM_SINE, WAVEFORM_TRIANGLE, WAVEFORM_BANDLIMIT_SAWTOOTH, WAVEFORM_BANDLIMIT_SQUARE };
struct SynthOsc {
  short wave;
  float level;
  float detune;   // cents
  int octave;
};
SynthOsc synthOsc[SYNTH_OSCS] = {
  { WAVEFORM_BANDLIMIT_SAWTOOTH, 100 / 127.0f, 0.0f, 0 },
  { WAVEFORM_BANDLIMIT_SAWTOOTH, 80 / 127.0f, 7.0f, 0 },
  { WAVEFORM_BANDLIMIT_SQUARE, 50 / 127.0f, 0.0f, -1 },
};
float synthDecayMs = 300.0f;
float synthSustain = 0.7f;
byte attackCC = 14, releaseCC = 21;

bool usesOscillators() {
  return instrument == INST_ACCORDION || instrument == INST_SYNTH;
}

float noteToFreq(float note) {
  return 440.0f * powf(2.0f, (note - 69.0f) / 12.0f);
}

float quadraticMs(byte value, float maxMs) {
  float t = value / 127.0f;
  return t * t * maxMs;
}

int sampleNote(int note) {
  // The bass plays the guitar's low strings two octaves down.
  return instrument == INST_BASS ? note - 24 : note;
}

void tuneVoice(int v, int note) {
  if (instrument == INST_SYNTH) {
    for (int o = 0; o < SYNTH_OSCS; o++) {
      reed[o][v].frequency(noteToFreq(note + 12.0f * synthOsc[o].octave + synthOsc[o].detune / 100.0f));
    }
    return;
  }
  reed[REED_16][v].arbitraryWaveform(note - 12 >= HIGH_TABLE_FROM ? tableCassottoHigh : tableCassotto, 16000.0f);
  reed[REED_M1][v].arbitraryWaveform(note >= HIGH_TABLE_FROM ? tableOpenHigh : tableOpen, 16000.0f);
  reed[REED_M2][v].arbitraryWaveform(note >= HIGH_TABLE_FROM ? tableCassottoHigh : tableCassotto, 16000.0f);
  reed[REED_4][v].arbitraryWaveform(note + 12 >= HIGH_TABLE_FROM ? tablePiccoloHigh : tablePiccolo, 16000.0f);
  reed[REED_16][v].frequency(noteToFreq(note - 12));
  reed[REED_M1][v].frequency(noteToFreq(note));
  reed[REED_M2][v].frequency(noteToFreq(note + wetCents / 100.0f));
  reed[REED_4][v].frequency(noteToFreq(note + 12));
}

// Per-oscillator gains: the register for the accordion, the oscillator
// levels for the synth (its 4th oscillator stays silent).
void applyOscGains() {
  for (int v = 0; v < NUM_VOICES; v++) {
    for (int r = 0; r < NUM_REEDS; r++) {
      float g;
      if (instrument == INST_SYNTH) g = r < SYNTH_OSCS ? 0.45f * synthOsc[r].level : 0.0f;
      else g = (registerMask & (1 << r)) ? reedGain[r] : 0.0f;
      reedMix[v].gain(r, g);
    }
  }
}

void applyEnvelope() {
  for (int v = 0; v < NUM_VOICES; v++) {
    bellows[v].attack(quadraticMs(attackCC, 2000));
    bellows[v].release(quadraticMs(releaseCC, 3000));
    // A reed sounds steadily while held; the synth gets a full ADSR.
    bellows[v].decay(instrument == INST_SYNTH ? synthDecayMs : 0.0f);
    bellows[v].sustain(instrument == INST_SYNTH ? synthSustain : 1.0f);
  }
}

// Switches every voice's oscillators between the reed tables and the
// synth waveforms.
void configureOscillators() {
  for (int v = 0; v < NUM_VOICES; v++) {
    for (int r = 0; r < NUM_REEDS; r++) {
      if (instrument == INST_SYNTH && r < SYNTH_OSCS) reed[r][v].begin(synthOsc[r].wave);
      else reed[r][v].begin(WAVEFORM_ARBITRARY);
    }
  }
  applyOscGains();
  applyEnvelope();
}

void retuneAll() {
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].lastNote >= 0) tuneVoice(i, voices[i].lastNote);
  }
}

bool voiceBusy(int i) {
  return usesOscillators() ? bellows[i].isActive() : sampler[i].isPlaying();
}

int findVoiceForNote(int note) {
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].note == note) return i;        // retrigger the same note
  }
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].note < 0 && !voiceBusy(i)) return i;   // silent voice
  }
  int oldest = 0;                                 // else: steal, preferring
  bool oldestReleasing = false;                   // voices already releasing
  for (int i = 0; i < NUM_VOICES; i++) {
    bool releasing = voices[i].note < 0;
    if ((releasing && !oldestReleasing) ||
        (releasing == oldestReleasing && voices[i].age < voices[oldest].age)) {
      oldest = i;
      oldestReleasing = releasing;
    }
  }
  return oldest;
}

void handleNoteOff(byte channel, byte note, byte velocity) {
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].note == note) {
      if (usesOscillators()) bellows[i].noteOff();
      else sampler[i].stop();
      voices[i].note = -1;
    }
  }
}

void handleNoteOn(byte channel, byte note, byte velocity) {
  if (velocity == 0) {                            // running-status Note Off
    handleNoteOff(channel, note, velocity);
    return;
  }
  int v = findVoiceForNote(note);
  voices[v].note = note;
  voices[v].lastNote = note;
  voices[v].age = ++voiceCounter;
  if (usesOscillators()) {
    float amp = 0.2f + 0.8f * (velocity / 127.0f);
    AudioNoInterrupts();
    tuneVoice(v, note);
    for (int r = 0; r < NUM_REEDS; r++) reed[r][v].amplitude(amp);
    bellows[v].noteOn();
    AudioInterrupts();
  } else {
    sampler[v].playNote(sampleNote(note), velocity);
  }
}

void silenceAll() {
  AudioNoInterrupts();
  for (int i = 0; i < NUM_VOICES; i++) {
    for (int r = 0; r < NUM_REEDS; r++) reed[r][i].amplitude(0);
    bellows[i].noteOff();
    sampler[i].stop();
    voices[i].note = -1;
    voices[i].lastNote = -1;
  }
  AudioInterrupts();
}

void releaseAll() {
  for (int i = 0; i < NUM_VOICES; i++) {
    bellows[i].noteOff();
    sampler[i].stop();
    voices[i].note = -1;
  }
}

void setInstrument(int inst) {
  if (inst == instrument) return;
  silenceAll();
  instrument = inst;
  if (!usesOscillators()) {
    const AudioSynthWavetable::instrument_data &data = (inst == INST_PIANO) ? piano : nylonstrgtr;
    for (int i = 0; i < NUM_VOICES; i++) sampler[i].setInstrument(data);
  }
  configureOscillators();
}

void setTone(byte value) {
  // 40 Hz .. 20 kHz on an exponential curve, capped at 16 kHz where the
  // biquad is still well-behaved; Q 0.707 = no resonant peak.
  float hz = 40.0f * powf(2.0f, 9.0f * value / 127.0f);
  toneFilter.setLowpass(0, min(hz, 16000.0f), 0.707f);
}

void setSynthWave(int o, byte value) {
  synthOsc[o].wave = SYNTH_WAVES[min(value / 32, 3)];
  if (instrument != INST_SYNTH) return;
  AudioNoInterrupts();
  for (int v = 0; v < NUM_VOICES; v++) reed[o][v].begin(synthOsc[o].wave);
  AudioInterrupts();
}

void setAmbience(byte value) {
  float wet = value / 127.0f;
  master.gain(0, 1.0f - 0.35f * wet);
  master.gain(1, 0.6f * wet);
}

void handleControlChange(byte channel, byte control, byte value) {
  switch (control) {
    case 7:
      codec.volume(0.8f * value / 127.0f);
      break;
    case 9:
      velocityCurve = min(value / 32, 3);
      break;
    case 14:
      if (value >= 64) resetCalibration();
      break;
    case 15:
      keyTest = value >= 64;
      for (int i = 0; i < keyCount; i++) keyState[i].sentPosition = 255;
      break;
    case 24:
      layoutSystem = value < 64 ? 0 : 1;
      break;
    case 20: case 21: case 22:
      setSynthWave(control - 20, value);
      break;
    case 25:
      setInstrument(min(value / 16, 4));
      break;
    case 26:
      registerMask = value & 0x0F;
      applyOscGains();
      break;
    case 28: case 29: case 30:
      synthOsc[control - 28].level = value / 127.0f;
      applyOscGains();
      break;
    case 85: case 86: case 87:
      synthOsc[control - 85].detune = (value - 64) / 64.0f * 50.0f;
      retuneAll();
      break;
    case 102: case 103: case 104:
      synthOsc[control - 102].octave = value < 43 ? -1 : (value < 85 ? 0 : 1);
      retuneAll();
      break;
    case 75:
      synthDecayMs = quadraticMs(value, 2000);
      applyEnvelope();
      break;
    case 79:
      synthSustain = value / 127.0f;
      applyEnvelope();
      break;
    case 27:
      wetCents = min((int)value, 30);
      retuneAll();
      break;
    case 72:
      releaseCC = value;
      applyEnvelope();
      break;
    case 73:
      attackCC = value;
      applyEnvelope();
      break;
    case 74:
      setTone(value);
      break;
    case 91:
      setAmbience(value);
      break;
    case 120:
      silenceAll();
      break;
    case 123:
      releaseAll();
      break;
  }
}

void localNoteOn(uint8_t note, uint8_t velocity) {
  if (noteHolders[note]++ > 0) return;
  handleNoteOn(1, note, velocity);
  usbMIDI.sendNoteOn(note, velocity, 1);
}

void localNoteOff(uint8_t note) {
  if (noteHolders[note] == 0 || --noteHolders[note] > 0) return;
  handleNoteOff(1, note, 0);
  usbMIDI.sendNoteOff(note, 0, 1);
}

void selectChannel(int ch) {
  for (int b = 0; b < 4; b++) digitalWriteFast(MUX_SEL_PINS[b], (ch >> b) & 1);
}

float fieldInv(float reading) {
  return 1.0f / cbrtf(max(reading - SENSOR_ZERO, 4.0f));
}

void updateModel(Key &k) {
  float bottom = max(k.bottom, k.rest + MIN_SPAN);
  k.restInv = fieldInv(k.rest);
  k.spanInv = 1.0f / max(k.restInv - fieldInv(bottom), 1e-6f);
}

// 0 at rest, 1 at the bottom: the magnet's distance from the cube root of
// the field, scaled between the key's two calibration points.
float keyTravel(const Key &k, float reading) {
  float t = (k.restInv - fieldInv(reading)) * k.spanInv;
  return constrain(t, 0.0f, 1.0f);
}

// Velocity from the time the key took between VEL_START and NOTE_ON_AT,
// on a log scale: FAST_MS or quicker = 127, SLOW_MS or slower = 1. The
// curve bends it: "soft" gives loud notes with a light touch, "hard" needs
// a firmer one.
uint8_t velocityFor(float ms) {
  if (velocityCurve == 0) return FIXED_VELOCITY;
  float x = (logf(SLOW_MS) - logf(max(ms, 0.1f))) / (logf(SLOW_MS) - logf(FAST_MS));
  x = constrain(x, 0.0f, 1.0f);
  const float exponent[4] = {1.0f, 0.6f, 1.0f, 1.6f};
  return (uint8_t)constrain((int)roundf(1.0f + 126.0f * powf(x, exponent[velocityCurve])), 1, 127);
}

// EEPROM: a magic number, then each key's learnt span (bottom - rest).
void saveCalibration() {
  EEPROM.put(0, EEPROM_MAGIC);
  for (int i = 0; i < keyCount; i++) {
    uint16_t span = (uint16_t)max(0.0f, keyState[i].bottom - keyState[i].rest);
    EEPROM.put(4 + 2 * i, span);
  }
  calibrationDirty = false;
}

void loadCalibration() {
  uint32_t magic;
  EEPROM.get(0, magic);
  for (int i = 0; i < keyCount; i++) {
    uint16_t span = 0;
    if (magic == EEPROM_MAGIC) EEPROM.get(4 + 2 * i, span);
    keyState[i].bottom = min(4095.0f, keyState[i].rest + max((int)span, MIN_SPAN));
    updateModel(keyState[i]);
  }
}

void resetCalibration() {
  for (int i = 0; i < keyCount; i++) {
    keyState[i].bottom = min(4095.0f, keyState[i].rest + MIN_SPAN);
    updateModel(keyState[i]);
  }
  saveCalibration();
}

// Reads every sensor once into readings[] (key order), one multiplexer
// channel at a time: all three multiplexers share the address lines.
void readSensors(uint16_t *readings) {
  for (int ch = 0; ch < 16; ch++) {
    bool any = false;
    for (int i = 0; i < keyCount; i++) any |= keyState[i].channel == ch;
    if (!any) continue;
    selectChannel(ch);
    delayMicroseconds(3);                       // let the multiplexer settle
    for (int i = 0; i < keyCount; i++) {
      if (keyState[i].channel == ch) readings[i] = analogRead(MUX_COM_PINS[keyState[i].mux]);
    }
  }
}

void setupKeys() {
  for (int b = 0; b < 4; b++) pinMode(MUX_SEL_PINS[b], OUTPUT);
  // A sensor drives its line to 0.6 V or more. With the pull-downs, a
  // missing board, multiplexer or sensor reads 0 V instead of floating
  // (which would play random notes), and that key is left out.
  for (int m = 0; m < MUX_COUNT; m++) pinMode(MUX_COM_PINS[m], INPUT_PULLDOWN);
  analogReadResolution(12);
  analogReadAveraging(1);
  keyCount = 0;
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    for (int c = 0; c < LAYOUT_COLS; c++) {
      if (KEY_INPUT[r][c] < 0 || keyCount == MAX_KEYS) continue;
      Key &k = keyState[keyCount++];
      memset(&k, 0, sizeof(k));
      k.row = r;
      k.col = c;
      k.mux = KEY_INPUT[r][c] / 16;
      k.channel = KEY_INPUT[r][c] % 16;
      k.note = -1;
      k.sentPosition = 255;
    }
  }
  // Rest readings: the average of a few dozen scans with the keys up.
  delay(50);                                    // the sensors take ~0.3 ms to wake up
  uint16_t readings[MAX_KEYS];
  float sum[MAX_KEYS] = {0};
  const int SCANS = 64;
  for (int s = 0; s < SCANS; s++) {
    readSensors(readings);
    for (int i = 0; i < keyCount; i++) sum[i] += readings[i];
  }
  for (int i = 0; i < keyCount; i++) {
    keyState[i].rest = sum[i] / SCANS;
    keyState[i].present = keyState[i].rest >= PRESENT_MIN;
    if (!keyState[i].present) missingKeys++;
  }
  loadCalibration();
}

// Time (in micros) at which the travel crossed `level`, interpolated
// between the previous scan and this one.
uint32_t crossingTime(const Key &k, float prev, float now, float level, uint32_t nowMicros) {
  float f = (level - prev) / max(now - prev, 1e-4f);
  return k.prevMicros + (uint32_t)(constrain(f, 0.0f, 1.0f) * (float)(nowMicros - k.prevMicros));
}

// One pass over all 44 sensors (~3.3 kHz): calibration, note on/off with
// velocity, and the key test stream.
void scanKeys() {
  uint16_t readings[MAX_KEYS];
  readSensors(readings);
  uint32_t now = micros();
  bool changed = false;
  for (int i = 0; i < keyCount; i++) {
    Key &k = keyState[i];
    if (!k.present) continue;
    float raw = readings[i];
    // Calibration. A reading below rest means rest was measured with the
    // key held, or has drifted: take it. While the key is up, follow slow
    // drift. The deepest press seen sets the bottom (saved after 5 s).
    if (raw < k.rest - 2 && raw >= PRESENT_MIN) {
      k.rest = raw;
      updateModel(k);
    } else if (!k.down && k.travel < 0.05f) {
      k.rest += (raw - k.rest) * 0.002f;
      updateModel(k);
    }
    if (raw > k.bottom + 4 && raw > k.rest + MIN_SPAN) {
      k.bottom = raw;
      updateModel(k);
      calibrationDirty = true;
      calibrationChangedAt = millis();
    }
    float t = keyTravel(k, raw);
    if (!k.down) {
      if (t < VEL_START) {
        k.startMicros = 0;
      } else if (k.startMicros == 0) {
        k.startMicros = crossingTime(k, k.travel, t, VEL_START, now) | 1;
      }
      if (t >= NOTE_ON_AT) {
        uint32_t at = crossingTime(k, k.travel, t, NOTE_ON_AT, now);
        k.down = true;
        k.note = noteAt(k.row, k.col);
        if (k.note >= 0) localNoteOn(k.note, velocityFor((at - k.startMicros) / 1000.0f));
        changed = true;
      }
    } else if (t < NOTE_OFF_AT) {
      k.down = false;
      k.startMicros = 0;
      if (k.note >= 0) localNoteOff(k.note);    // the note it started, even after a layout switch
      k.note = -1;
      changed = true;
    }
    k.travel = t;
    k.prevMicros = now;
    if (keyTest) {
      uint8_t pos = (uint8_t)roundf(t * 127.0f);
      if (pos != k.sentPosition && (abs((int)pos - (int)k.sentPosition) >= 2 || pos == 0 || pos == 127)) {
        usbMIDI.sendPolyPressure(i, pos, 16);
        k.sentPosition = pos;
        changed = true;
      }
    }
  }
  if (calibrationDirty && millis() - calibrationChangedAt > 5000) saveCalibration();
  if (changed) usbMIDI.send_now();
}

void setLed(bool red, bool green) {
  digitalWriteFast(LED_PINS[0], red);
  digitalWriteFast(LED_PINS[1], green);
}

// Green while all is well; red, blinking twice a second, on an error.
void updateLed() {
  if (codecOk && missingKeys == 0) setLed(false, true);
  else setLed((millis() / 250) % 2 == 0, false);
}

void setup() {
  for (int i = 0; i < 2; i++) pinMode(LED_PINS[i], OUTPUT);
  setLed(true, true);                            // orange: reading the keys
  uint32_t started = millis();
  AudioMemory(60);   // measured peak: 32 blocks (8 voices x 4 reeds + reverb)
  setupKeys();

  codecOk = codec.enable();
  codec.volume(0.8f * 90 / 127.0f);

  // Harmonic counts keep everything below ~16 kHz. Up to C5 (523 Hz):
  // 20 x 523 for the 8' reeds, 10 x 1047 for the piccolo. Above, up to E6
  // (1319 Hz): 12 harmonics for the 8' reeds, 6 for the piccolo.
  buildReedTable(tableOpen, 20, 1.05f, 0.25f);
  buildReedTable(tableCassotto, 14, 1.85f, 0.20f);
  buildReedTable(tablePiccolo, 10, 1.20f, 0.20f);
  buildReedTable(tableOpenHigh, 12, 1.05f, 0.25f);
  buildReedTable(tableCassottoHigh, 12, 1.85f, 0.20f);
  buildReedTable(tablePiccoloHigh, 6, 1.20f, 0.20f);

  const int16_t *tables[NUM_REEDS] = {tableCassotto, tableOpen, tableCassotto, tablePiccolo};
  for (int v = 0; v < NUM_VOICES; v++) {
    voices[v].note = -1;
    voices[v].lastNote = -1;
    voices[v].age = 0;
    for (int r = 0; r < NUM_REEDS; r++) {
      reed[r][v].arbitraryWaveform(tables[r], 16000.0f);
      reed[r][v].begin(0.0f, 440.0f, WAVEFORM_ARBITRARY);
    }
    // Bellows: a reed takes a few tens of ms to speak and to stop.
    bellows[v].hold(0);
    sampler[v].setInstrument(piano);
    sampler[v].amplitude(1.0f);
  }
  configureOscillators();

  // Accordion voice peaks at 1.56 (all four reeds): 4 voices x 1.56 x 0.16
  // per bank, banks at 0.5 — a full chord stays under full scale.
  for (int ch = 0; ch < 4; ch++) {
    accA.gain(ch, 0.16f);
    accB.gain(ch, 0.16f);
    // The wavetable samples come out ~2.5x quieter than a reed voice
    // (measured on the Teensy), so they get more gain.
    smpA.gain(ch, 0.8f);
    smpB.gain(ch, 0.8f);
  }
  engines.gain(0, 0.5f);
  engines.gain(1, 0.5f);
  engines.gain(2, 0.5f);
  engines.gain(3, 0.5f);

  setTone(110);
  room.roomsize(0.55f);
  room.damping(0.6f);
  setAmbience(25);

  usbMIDI.setHandleNoteOn(handleNoteOn);
  usbMIDI.setHandleNoteOff(handleNoteOff);
  usbMIDI.setHandleControlChange(handleControlChange);
  while (millis() - started < LED_STARTUP_MS) {
  }
  updateLed();
}

void loop() {
  // Drain every pending USB MIDI message; each one calls a handler above.
  while (usbMIDI.read()) {
  }
  scanKeys();
  updateLed();
}
