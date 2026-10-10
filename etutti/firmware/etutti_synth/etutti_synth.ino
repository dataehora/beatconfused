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
     Tools > Board:    your Teensy
     Tools > USB Type: "MIDI" (or "Serial + MIDI" to also get Serial)

   The Teensy shows up as a USB MIDI device called "eTutti" (see name.c)
   and plays an 8-voice polyphonic synth:
     8 x (oscillator -> ADSR envelope) -> mixer -> state-variable low-pass
     filter -> both channels of the Audio Board.

   MIDI implementation (any channel; keep in sync with etutti/script.js):
     Note On / Note Off      play / release (velocity -> loudness)
     CC 7   Volume           headphone volume
     CC 70  Waveform         0-31 sine, 32-63 saw, 64-95 square, 96-127 triangle
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
// volume pot, which the eTuttino doesn't fit.
const int MATRIX_ROWS = 4;
const int MATRIX_COLS = 9;
const uint8_t ROW_PINS[MATRIX_ROWS] = {0, 1, 2, 3};
const uint8_t COL_PINS[MATRIX_COLS] = {4, 5, 6, 9, 14, 15, 16, 17, 22};
const uint8_t KEY_VELOCITY = 100;   // MX switches are on/off: fixed velocity
const uint32_t DEBOUNCE_MS = 5;

// MIDI note for each [row][col]; -1 = no switch there. Chromatic accordion
// C-griff: +3 semitones along a row, rows staggered half a key, row 4 a
// copy of row 1 with F#3 in front. Keep in sync with ROWS in
// etutti/script.js.
const int8_t NOTE_MAP[MATRIX_ROWS][MATRIX_COLS] = {
  // col: 0    1    2    3    4    5    6    7    8
  {     -1,  57,  60,  63,  66,  69,  72,  75,  78 },  // row 1: A3 .. F#5
  {     55,  58,  61,  64,  67,  70,  73,  76,  79 },  // row 2: G3 .. G5
  {     -1,  56,  59,  62,  65,  68,  71,  74,  77 },  // row 3: G#3 .. F5
  {     54,  57,  60,  63,  66,  69,  72,  75,  78 },  // row 4: F#3 .. F#5
};

bool keyDown[MATRIX_ROWS][MATRIX_COLS];
uint32_t keyChangedAt[MATRIX_ROWS][MATRIX_COLS];
// How many physical keys hold each note (row 4 doubles row 1), so a note
// only starts on the first press and stops on the last release.
uint8_t noteHolders[128];

// ---- Audio graph ----
AudioSynthWaveform       wave[NUM_VOICES];
AudioEffectEnvelope      env[NUM_VOICES];
AudioMixer4              mixA;      // voices 0-3
AudioMixer4              mixB;      // voices 4-7
AudioMixer4              mixMain;   // mixA + mixB
AudioFilterStateVariable filter;
AudioOutputI2S           i2sOut;
AudioControlSGTL5000     codec;

AudioConnection patchW0(wave[0], env[0]);
AudioConnection patchW1(wave[1], env[1]);
AudioConnection patchW2(wave[2], env[2]);
AudioConnection patchW3(wave[3], env[3]);
AudioConnection patchW4(wave[4], env[4]);
AudioConnection patchW5(wave[5], env[5]);
AudioConnection patchW6(wave[6], env[6]);
AudioConnection patchW7(wave[7], env[7]);
AudioConnection patchE0(env[0], 0, mixA, 0);
AudioConnection patchE1(env[1], 0, mixA, 1);
AudioConnection patchE2(env[2], 0, mixA, 2);
AudioConnection patchE3(env[3], 0, mixA, 3);
AudioConnection patchE4(env[4], 0, mixB, 0);
AudioConnection patchE5(env[5], 0, mixB, 1);
AudioConnection patchE6(env[6], 0, mixB, 2);
AudioConnection patchE7(env[7], 0, mixB, 3);
AudioConnection patchMA(mixA, 0, mixMain, 0);
AudioConnection patchMB(mixB, 0, mixMain, 1);
AudioConnection patchF(mixMain, 0, filter, 0);
AudioConnection patchL(filter, 0, i2sOut, 0);   // low-pass output -> left
AudioConnection patchR(filter, 0, i2sOut, 1);   //                 -> right

// ---- Voice allocation ----
struct Voice {
  int note;            // MIDI note held, or -1 when free / releasing
  unsigned long age;   // allocation order, for stealing the oldest
};
Voice voices[NUM_VOICES];
unsigned long voiceCounter = 0;

// ---- Current synth settings (defaults match the page's sliders) ----
short waveformType = WAVEFORM_SAWTOOTH;

float noteToFreq(int note) {
  return 440.0f * powf(2.0f, (note - 69) / 12.0f);
}

float quadraticMs(byte value, float maxMs) {
  float t = value / 127.0f;
  return t * t * maxMs;
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
  voices[v].age = ++voiceCounter;
  AudioNoInterrupts();
  wave[v].frequency(noteToFreq(note));
  wave[v].amplitude(0.15f + 0.85f * (velocity / 127.0f));
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
    wave[i].amplitude(0);
    env[i].noteOff();
    voices[i].note = -1;
  }
  AudioInterrupts();
}

void setWaveform(byte value) {
  static const short TYPES[4] = {
    WAVEFORM_SINE, WAVEFORM_SAWTOOTH, WAVEFORM_SQUARE, WAVEFORM_TRIANGLE
  };
  waveformType = TYPES[min(value / 32, 3)];
  AudioNoInterrupts();
  for (int i = 0; i < NUM_VOICES; i++) wave[i].begin(waveformType);
  AudioInterrupts();
}

void handleControlChange(byte channel, byte control, byte value) {
  switch (control) {
    case 7:
      codec.volume(0.8f * value / 127.0f);
      break;
    case 70:
      setWaveform(value);
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
      int note = NOTE_MAP[r][c];
      if (note < 0) continue;
      bool pressed = digitalRead(COL_PINS[c]) == LOW;
      if (pressed != keyDown[r][c] && now - keyChangedAt[r][c] >= DEBOUNCE_MS) {
        keyDown[r][c] = pressed;
        keyChangedAt[r][c] = now;
        if (pressed) localNoteOn(note);
        else localNoteOff(note);
        changed = true;
      }
    }
    pinMode(ROW_PINS[r], INPUT);
  }
  if (changed) usbMIDI.send_now();
}

void setup() {
  AudioMemory(40);
  setupMatrix();

  codec.enable();
  codec.volume(0.6f);

  for (int i = 0; i < NUM_VOICES; i++) {
    voices[i].note = -1;
    voices[i].age = 0;
    wave[i].begin(0.0f, 440.0f, waveformType);
    // Defaults equal to the page's initial slider positions.
    env[i].attack(quadraticMs(10, 2000));
    env[i].hold(0);
    env[i].decay(quadraticMs(50, 2000));
    env[i].sustain(90 / 127.0f);
    env[i].release(quadraticMs(40, 3000));
  }

  // Each voice at most 1.0 * 0.25 * 0.5 -> eight full-velocity voices sum
  // to 1.0, so chords never clip.
  for (int ch = 0; ch < 4; ch++) {
    mixA.gain(ch, 0.25f);
    mixB.gain(ch, 0.25f);
  }
  mixMain.gain(0, 0.5f);
  mixMain.gain(1, 0.5f);
  mixMain.gain(2, 0.0f);
  mixMain.gain(3, 0.0f);

  filter.frequency(40.0f * powf(2.0f, 9.0f * 110 / 127.0f));
  filter.resonance(0.7f + 4.3f * 10 / 127.0f);

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
