/* ============================================================
   eTutti synth — Teensy firmware for https://beatconfused.com/etutti/

   Hardware: Teensy 4.0 + PJRC Audio Adaptor Board Rev D (SGTL5000), on
   the eTuttino PCB (etutti/hardware/). Sound comes out of the Audio
   Board's headphone jack and line out. The 34 MX switches form a 4 x 9
   key matrix (one 1N4148 per switch, anode on the switch side, cathode
   on the row): rows are driven low one at a time, columns are read with
   pull-ups. Every key plays the internal sound engine AND is sent over
   USB MIDI, so the device works standalone or with the web page.

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
   ============================================================ */
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include "piano_samples.h"
#include "nylonstrgtr_samples.h"

// usbMIDI only exists when the USB Type includes MIDI. Without this check
// the compiler only says "'usbMIDI' was not declared in this scope".
#if !defined(MIDI_INTERFACE)
#error "In the Arduino IDE choose Tools > USB Type > MIDI (or Serial + MIDI), then upload again."
#endif

const int NUM_VOICES = 8;

// ---- eTuttino key matrix (see etutti/hardware/README.md) ----
// Pins chosen to stay clear of the Audio Board Rev D (7, 8, 18-21, 23)
// and of its SD card (10-13), so sample playback from SD stays possible.
// 6 and 15 are only used by the Audio Board's optional memory chip and
// volume pot, which the eTuttino doesn't fit. ROW_PINS[r] is accordion
// row r+1 (row 1 is the one nearest the player, at the bottom).
const int MATRIX_ROWS = 4;
const int MATRIX_COLS = 9;
const uint8_t ROW_PINS[MATRIX_ROWS] = {3, 2, 1, 0};
const uint8_t COL_PINS[MATRIX_COLS] = {4, 5, 6, 9, 14, 15, 16, 17, 22};
const uint8_t KEY_VELOCITY = 100;   // MX switches are on/off: fixed velocity
const uint32_t DEBOUNCE_MS = 5;

// Chromatic button accordion layouts. Along a row each key is a minor
// third (+3) above the previous one; rows 1 and 3 have 8 keys starting at
// matrix column 1, rows 2 and 4 have 9 starting at column 0 (they sit half
// a key further left). Row 4 repeats row 1 with one more key in front.
// B-griff is the mirror image of C-griff: rows 1 and 3 swap places, so a
// diagonal step goes the other way. Keep in sync with etutti/script.js.
const int8_t FIRST_NOTE[2][MATRIX_ROWS] = {
  {57, 55, 56, 54},   // C-griff: A3, G3, G#3, F#3
  {56, 55, 57, 53},   // B-griff: G#3, G3, A3, F3
};
const uint8_t FIRST_COL[MATRIX_ROWS] = {1, 0, 1, 0};
int layoutSystem = 0;   // 0 = C-griff, 1 = B-griff

int noteAt(int r, int c) {
  if (c < FIRST_COL[r]) return -1;
  return FIRST_NOTE[layoutSystem][r] + 3 * (c - FIRST_COL[r]);
}

bool keyDown[MATRIX_ROWS][MATRIX_COLS];
uint32_t keyChangedAt[MATRIX_ROWS][MATRIX_COLS];
int8_t keyNote[MATRIX_ROWS][MATRIX_COLS];   // note a held key started (survives a layout switch)
// How many physical keys hold each note (row 4 doubles row 1), so a note
// only starts on the first press and stops on the last release.
uint8_t noteHolders[128];

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

void localNoteOn(uint8_t note) {
  if (noteHolders[note]++ > 0) return;
  handleNoteOn(1, note, KEY_VELOCITY);
  usbMIDI.sendNoteOn(note, KEY_VELOCITY, 1);
}

void localNoteOff(uint8_t note) {
  if (noteHolders[note] == 0 || --noteHolders[note] > 0) return;
  handleNoteOff(1, note, 0);
  usbMIDI.sendNoteOff(note, 0, 1);
}

void setupMatrix() {
  for (int r = 0; r < MATRIX_ROWS; r++) pinMode(ROW_PINS[r], INPUT);   // idle rows float
  for (int c = 0; c < MATRIX_COLS; c++) pinMode(COL_PINS[c], INPUT_PULLUP);
}

// One full pass over the matrix. A key's new state is accepted only if it
// differs from the current one and the last accepted change is at least
// DEBOUNCE_MS old (switch bounce is a few ms of chatter on each edge).
void scanMatrix() {
  uint32_t now = millis();
  bool changed = false;
  for (int r = 0; r < MATRIX_ROWS; r++) {
    pinMode(ROW_PINS[r], OUTPUT);
    digitalWrite(ROW_PINS[r], LOW);
    delayMicroseconds(10);                       // let the line settle
    for (int c = 0; c < MATRIX_COLS; c++) {
      if (c < FIRST_COL[r]) continue;            // no switch in that cell
      bool pressed = digitalRead(COL_PINS[c]) == LOW;
      if (pressed != keyDown[r][c] && now - keyChangedAt[r][c] >= DEBOUNCE_MS) {
        keyDown[r][c] = pressed;
        keyChangedAt[r][c] = now;
        if (pressed) {
          keyNote[r][c] = noteAt(r, c);
          localNoteOn(keyNote[r][c]);
        } else {
          localNoteOff(keyNote[r][c]);           // the note it started, even after a layout switch
        }
        changed = true;
      }
    }
    pinMode(ROW_PINS[r], INPUT);
  }
  if (changed) usbMIDI.send_now();
}

void setup() {
  AudioMemory(60);   // measured peak: 32 blocks (8 voices x 4 reeds + reverb)
  setupMatrix();

  codec.enable();
  codec.volume(0.8f * 90 / 127.0f);

  // Harmonic counts keep G5 (784 Hz) below ~16 kHz: 20 x 784 for the 8'
  // reeds, 10 x 1568 for the piccolo; the 16' reed is lower still.
  buildReedTable(tableOpen, 20, 1.05f, 0.25f);
  buildReedTable(tableCassotto, 14, 1.85f, 0.20f);
  buildReedTable(tablePiccolo, 10, 1.20f, 0.20f);

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
}

void loop() {
  // Drain every pending USB MIDI message; each one calls a handler above.
  while (usbMIDI.read()) {
  }
  scanMatrix();
}
