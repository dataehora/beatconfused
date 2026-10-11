/* ============================================================
   eTutti synth — Teensy firmware for https://beatconfused.com/etutti/

   Hardware: Teensy 4.0 + PJRC Audio Adaptor Board Rev D (SGTL5000), on
   the eTuttino PCB (etutti/hardware/). Sound comes out of the Audio
   Board's headphone jack and line out. The 34 MX switches form a 4 x 9
   key matrix (one 1N4148 per switch, anode on the switch side, cathode
   on the row): rows are driven low one at a time, columns are read with
   pull-ups. Every key plays the internal synth AND is sent over USB MIDI,
   so the device works standalone or with the web page.

   Arduino IDE + Teensyduino settings:
     Tools > Board:    Teensy 4.0
     Tools > USB Type: "MIDI" (or "Serial + MIDI" to also get Serial)

   The Teensy shows up as a USB MIDI device called "eTutti" (see name.c)
   and plays an 8-voice polyphonic synth. Each voice has two oscillators
   ("reeds") — the second one detunable and shiftable by an octave, like
   the voices of an accordion — through an ADSR envelope; all voices then
   share a state-variable low-pass filter (the "cassotto"):
     8 x (osc1 + osc2 -> mixer -> ADSR) -> mixers -> low-pass -> L + R

   MIDI implementation (any channel; keep in sync with CC in etutti/script.js):
     Note On / Note Off      play / release (velocity -> loudness)
     CC 7   Volume           headphone volume
     CC 20  Voice 2 waveform 0-31 sine, 32-63 saw, 64-95 square, 96-127 triangle
     CC 21  Voice 2 level    0 .. 100 % of voice 1
     CC 22  Voice 2 detune   64 = in tune, 0 / 127 = -50 / +50 cents
     CC 23  Voice 2 octave   0-42 one octave down, 43-84 unison, 85-127 up
     CC 24  Key layout       0-63 C-griff, 64-127 B-griff (the physical keys)
     CC 70  Voice 1 waveform as CC 20
     CC 71  Resonance        0.7 .. 5.0
     CC 72  Release          0 .. 3000 ms (quadratic curve)
     CC 73  Attack           0 .. 2000 ms (quadratic curve)
     CC 74  Filter cutoff    40 Hz .. ~17 kHz (exponential)
     CC 75  Decay            0 .. 2000 ms (quadratic curve)
     CC 79  Sustain level    0 .. 100 %
     CC 120 All sound off    instant silence
     CC 123 All notes off    release every voice
   ============================================================ */
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>

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
AudioSynthWaveform       osc1[NUM_VOICES];
AudioSynthWaveform       osc2[NUM_VOICES];
AudioMixer4              voiceMix[NUM_VOICES];
AudioEffectEnvelope      env[NUM_VOICES];
AudioMixer4              mixA;      // voices 0-3
AudioMixer4              mixB;      // voices 4-7
AudioMixer4              mixMain;   // mixA + mixB
AudioFilterStateVariable filter;
AudioOutputI2S           i2sOut;
AudioControlSGTL5000     codec;

AudioConnection c1a(osc1[0], 0, voiceMix[0], 0);
AudioConnection c1b(osc1[1], 0, voiceMix[1], 0);
AudioConnection c1c(osc1[2], 0, voiceMix[2], 0);
AudioConnection c1d(osc1[3], 0, voiceMix[3], 0);
AudioConnection c1e(osc1[4], 0, voiceMix[4], 0);
AudioConnection c1f(osc1[5], 0, voiceMix[5], 0);
AudioConnection c1g(osc1[6], 0, voiceMix[6], 0);
AudioConnection c1h(osc1[7], 0, voiceMix[7], 0);
AudioConnection c2a(osc2[0], 0, voiceMix[0], 1);
AudioConnection c2b(osc2[1], 0, voiceMix[1], 1);
AudioConnection c2c(osc2[2], 0, voiceMix[2], 1);
AudioConnection c2d(osc2[3], 0, voiceMix[3], 1);
AudioConnection c2e(osc2[4], 0, voiceMix[4], 1);
AudioConnection c2f(osc2[5], 0, voiceMix[5], 1);
AudioConnection c2g(osc2[6], 0, voiceMix[6], 1);
AudioConnection c2h(osc2[7], 0, voiceMix[7], 1);
AudioConnection cva(voiceMix[0], env[0]);
AudioConnection cvb(voiceMix[1], env[1]);
AudioConnection cvc(voiceMix[2], env[2]);
AudioConnection cvd(voiceMix[3], env[3]);
AudioConnection cve(voiceMix[4], env[4]);
AudioConnection cvf(voiceMix[5], env[5]);
AudioConnection cvg(voiceMix[6], env[6]);
AudioConnection cvh(voiceMix[7], env[7]);
AudioConnection cea(env[0], 0, mixA, 0);
AudioConnection ceb(env[1], 0, mixA, 1);
AudioConnection cec(env[2], 0, mixA, 2);
AudioConnection ced(env[3], 0, mixA, 3);
AudioConnection cee(env[4], 0, mixB, 0);
AudioConnection cef(env[5], 0, mixB, 1);
AudioConnection ceg(env[6], 0, mixB, 2);
AudioConnection ceh(env[7], 0, mixB, 3);
AudioConnection cma(mixA, 0, mixMain, 0);
AudioConnection cmb(mixB, 0, mixMain, 1);
AudioConnection cf(mixMain, 0, filter, 0);
AudioConnection cl(filter, 0, i2sOut, 0);   // low-pass output -> left
AudioConnection cr(filter, 0, i2sOut, 1);   //                 -> right

// ---- Voice allocation ----
struct Voice {
  int note;            // MIDI note held, or -1 when free / releasing
  int lastNote;        // note it last played (kept while releasing, for retuning)
  unsigned long age;   // allocation order, for stealing the oldest
};
Voice voices[NUM_VOICES];
unsigned long voiceCounter = 0;

// ---- Current synth settings — the defaults are the page's "Classic
// accordion" preset: two reeds almost in tune, in a soft cassotto. ----
const short WAVE_TYPES[4] = { WAVEFORM_SINE, WAVEFORM_SAWTOOTH, WAVEFORM_SQUARE, WAVEFORM_TRIANGLE };
short wave1Type = WAVEFORM_SAWTOOTH;
short wave2Type = WAVEFORM_SAWTOOTH;
float voice2Level = 100 / 127.0f;
float voice2Detune = (69 - 64) / 64.0f * 50.0f;   // cents
int voice2Octave = 0;

float noteToFreq(float note) {
  return 440.0f * powf(2.0f, (note - 69.0f) / 12.0f);
}

float quadraticMs(byte value, float maxMs) {
  float t = value / 127.0f;
  return t * t * maxMs;
}

void tuneVoice(int v, int note) {
  osc1[v].frequency(noteToFreq(note));
  osc2[v].frequency(noteToFreq(note + 12.0f * voice2Octave + voice2Detune / 100.0f));
}

void applyVoiceMix() {
  // Voice 1 at 0.6, voice 2 at 0.6 x level: a full two-reed voice peaks at
  // 1.2, and eight of them through 0.2 x 0.5 stay just under full scale.
  for (int i = 0; i < NUM_VOICES; i++) {
    voiceMix[i].gain(0, 0.6f);
    voiceMix[i].gain(1, 0.6f * voice2Level);
  }
}

void retuneAll() {
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].lastNote >= 0) tuneVoice(i, voices[i].lastNote);
  }
}

int findVoiceForNote(int note) {
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].note == note) return i;        // retrigger the same note
  }
  for (int i = 0; i < NUM_VOICES; i++) {
    if (voices[i].note < 0 && !env[i].isActive()) return i;   // silent voice
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
      env[i].noteOff();
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
  float amp = 0.15f + 0.85f * (velocity / 127.0f);
  AudioNoInterrupts();
  tuneVoice(v, note);
  osc1[v].amplitude(amp);
  osc2[v].amplitude(amp);
  env[v].noteOn();
  AudioInterrupts();
}

void releaseAll() {
  for (int i = 0; i < NUM_VOICES; i++) {
    env[i].noteOff();
    voices[i].note = -1;
  }
}

void silenceAll() {
  AudioNoInterrupts();
  for (int i = 0; i < NUM_VOICES; i++) {
    osc1[i].amplitude(0);
    osc2[i].amplitude(0);
    env[i].noteOff();
    voices[i].note = -1;
  }
  AudioInterrupts();
}

short waveFromCC(byte value) {
  return WAVE_TYPES[min(value / 32, 3)];
}

void handleControlChange(byte channel, byte control, byte value) {
  switch (control) {
    case 7:
      codec.volume(0.8f * value / 127.0f);
      break;
    case 20:
      wave2Type = waveFromCC(value);
      AudioNoInterrupts();
      for (int i = 0; i < NUM_VOICES; i++) osc2[i].begin(wave2Type);
      AudioInterrupts();
      break;
    case 21:
      voice2Level = value / 127.0f;
      applyVoiceMix();
      break;
    case 22:
      voice2Detune = (value - 64) / 64.0f * 50.0f;
      retuneAll();
      break;
    case 23:
      voice2Octave = value < 43 ? -1 : (value < 85 ? 0 : 1);
      retuneAll();
      break;
    case 24:
      layoutSystem = value < 64 ? 0 : 1;
      break;
    case 70:
      wave1Type = waveFromCC(value);
      AudioNoInterrupts();
      for (int i = 0; i < NUM_VOICES; i++) osc1[i].begin(wave1Type);
      AudioInterrupts();
      break;
    case 71:
      filter.resonance(0.7f + 4.3f * value / 127.0f);
      break;
    case 72:
      for (int i = 0; i < NUM_VOICES; i++) env[i].release(quadraticMs(value, 3000));
      break;
    case 73:
      for (int i = 0; i < NUM_VOICES; i++) env[i].attack(quadraticMs(value, 2000));
      break;
    case 74: {
      // 40 Hz .. 20 kHz on an exponential curve, capped where the
      // state-variable filter stays stable (about samplerate / 2.5).
      float hz = 40.0f * powf(2.0f, 9.0f * value / 127.0f);
      filter.frequency(min(hz, 17000.0f));
      break;
    }
    case 75:
      for (int i = 0; i < NUM_VOICES; i++) env[i].decay(quadraticMs(value, 2000));
      break;
    case 79:
      for (int i = 0; i < NUM_VOICES; i++) env[i].sustain(value / 127.0f);
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
  AudioMemory(48);
  setupMatrix();

  codec.enable();
  codec.volume(0.8f * 90 / 127.0f);

  for (int i = 0; i < NUM_VOICES; i++) {
    voices[i].note = -1;
    voices[i].lastNote = -1;
    voices[i].age = 0;
    osc1[i].begin(0.0f, 440.0f, wave1Type);
    osc2[i].begin(0.0f, 440.0f, wave2Type);
    // Defaults equal to the page's "Classic accordion" preset.
    env[i].attack(quadraticMs(14, 2000));
    env[i].hold(0);
    env[i].decay(quadraticMs(30, 2000));
    env[i].sustain(1.0f);
    env[i].release(quadraticMs(21, 3000));
  }
  applyVoiceMix();

  for (int ch = 0; ch < 4; ch++) {
    mixA.gain(ch, 0.2f);
    mixB.gain(ch, 0.2f);
  }
  mixMain.gain(0, 0.5f);
  mixMain.gain(1, 0.5f);
  mixMain.gain(2, 0.0f);
  mixMain.gain(3, 0.0f);

  filter.frequency(40.0f * powf(2.0f, 9.0f * 82 / 127.0f));
  filter.resonance(0.7f);

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
