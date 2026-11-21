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

   MIDI implementation (any channel; keep in sync with CC in etutti/etuttino/script.js):
     Note On / Note Off      play / release (velocity -> loudness; accordion: also brightness)
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
   Controls board (etutti/hardware/controls_pcb.py, on the main board's J3):
     volume pot (pin 22 / A8)   sets the headphone volume, like CC 7 (and sends
                                CC 7 back); only when it moves, so the page's
                                CC 7 holds until the pot is turned. With no
                                controls board plugged in it is ignored.
     encoder (pins 17 / 9)      turning steps through the instruments
                                (accordion, piano, bass, guitar, synth) and
                                plays the new one at once; the LED blinks green
                                until it is confirmed. Sends CC 25 back.
     encoder button (pin 6)     after turning: confirms, and that instrument
                                is the one the eTuttino starts with next time;
                                otherwise: back to the default sound (classic
                                accordion, register MM, dry).
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
#include "reed_sampler.h"

// usbMIDI only exists when the USB Type includes MIDI. Without this check
// the compiler only says "'usbMIDI' was not declared in this scope".
#if !defined(MIDI_INTERFACE)
#error "In the Arduino IDE choose Tools > USB Type > MIDI (or Serial + MIDI), then upload again."
#endif

const int NUM_VOICES = 8;

// One sketch, two instruments, chosen by the board it is compiled for:
//   Teensy 4.0       -> eTuttino (44 keys, Audio Board, controls board)
//   Teensy MicroMod  -> eTutti Student V01 (28 keys, everything on one board,
//                       battery, speaker; see "Student V01" further down)
#if defined(ARDUINO_TEENSY_MICROMOD)
#define ETUTTI_STUDENT 1
#else
#define ETUTTI_STUDENT 0
#endif

// Student V4 (SPEC R1V4 + R2V4, etutti/hardware/student_v04/): the same Teensy
// MicroMod build, but with the row-scan keyboard (4 analogue OUT lines + a shift
// register chain that switches one column on at a time), up to 76 keys, an OLED
// and a microphone. Switch it on here (or with -DETUTTI_STUDENT_V4=1); it stays
// off by default so the MicroMod build is still the Student V01 one.
#ifndef ETUTTI_STUDENT_V4
#define ETUTTI_STUDENT_V4 0
#endif
#define ETUTTI_V4 (ETUTTI_STUDENT && ETUTTI_STUDENT_V4)

#if ETUTTI_STUDENT
// ---- eTutti Student V01 / V4: the pins both have in common (V01: etutti/hardware/
// student_v01/, pins from etutti/hardware/viaggio_micromod/pcb/PINOS.md) ----
const uint32_t SENSOR_WAKE_US = 60;                    // TMAG5253BA3 is ready 45 us after its EN rises (max); 60 = margin
const uint8_t LED_PINS[2] = {13, 5};                   // red (also the module's blue LED), green
const uint32_t LED_STARTUP_MS = 600;
// Two encoders with a push switch (to GND, pull-ups here): volume and selector.
const uint8_t VOL_A_PIN = 22, VOL_B_PIN = 24, VOL_SW_PIN = 25;   // the volume click is also the power switch
const uint8_t ENC_A_PIN = 11, ENC_B_PIN = 9, ENC_SW_PIN = 6;     // selector
const int ENC_STEPS_PER_DETENT = 2;     // EC11E18244A5: 18 pulses, 36 detents per turn
const uint8_t KEEP_PIN = 10;            // high holds the 3.3 V supply on
const uint8_t PWR_EN_PIN = 28;          // left as an input (the board pulls it up); driven low = off, also on USB
const uint8_t AMP_SD_PIN = 12;          // high = speaker amplifier on
const uint8_t VBAT_PIN = 16;            // battery / 2
const uint8_t HP_DET_PIN = 17;          // headphones in: ~0 V; out: ~1.4 V
#endif

#if ETUTTI_STUDENT && !ETUTTI_STUDENT_V4
// ---- Student V01 keys: 28 keys on a 4 x 8 grid, two multiplexers. KEY_INPUT is the table the
// board check (viaggio_j1/m3.py) read from the routed board, 28/28.
// Multiplexer 0 = right half (COM on pin 14), 1 = left half (pin 15).
// Channels 0-7 are rows 1 and 3, channels 8-15 rows 2 and 4: address line S3
// also switches on that half of the sensors (EN_A / EN_B), so only 14 of
// the 28 draw current at a time.
const int LAYOUT_ROWS = 4;
const int LAYOUT_COLS = 8;
const int MUX_COUNT = 2;
const uint8_t MUX_SEL_PINS[4] = {0, 1, 2, 3};          // S0..S3, shared
const uint8_t MUX_COM_PINS[MUX_COUNT] = {14, 15};      // A0, A1
const uint8_t SENS_EN_PIN = 4;                         // high = sensors powered
const uint8_t CHG_STAT_PIN = 26;        // low = charging (only meaningful with USB power)
const int8_t KEY_INPUT[LAYOUT_ROWS][LAYOUT_COLS] = {
  { -1,  21,  20,  17,  19,   2,   1,   0},
  { 25,  26,  31,  29,  13,  11,  14,  15},
  { -1,  18,  23,  22,   4,   6,   5,   3},
  { -1,  28,  27,  24,   9,   8,  10,  -1},
};
#elif ETUTTI_V4
// ---- Student V4 keyboard (R2V4, F2: sensor strips on steps in the lower case) ----
// Pins and scan contract: student_v04/pcb/PINOS.md (DRAFT of the electronics agent, R2V4 E2/E5).
//
// One universal strip = 4 sensors (pitch 18.5 mm) + one 74HC595 that switches one
// sensor on at a time. Strips are chained along each row: the 4 rows carry the same
// DATA/CLK, so a single "1" walking along the chain switches ONE COLUMN on, i.e.
// 4 sensors (one per row) at once. Each row's
// sensors share one analogue OUT line (a switched-off TMAG5253 leaves OUT high
// impedance), 4 lines in all.
//   28 keys = 2 strips per row (8 columns), 44 = 3 (12), 60 = 4 (16), 76 = 5 (20).
#define V4_KEYS 28                       // 28, 44, 60 or 76: the number of keys fitted
#if V4_KEYS != 28 && V4_KEYS != 44 && V4_KEYS != 60 && V4_KEYS != 76
#error "V4_KEYS must be 28, 44, 60 or 76"
#endif
const int V4_STRIPS_PER_ROW = (V4_KEYS - 28) / 16 + 2;
const int LAYOUT_ROWS = 4;
const int LAYOUT_COLS = 4 * V4_STRIPS_PER_ROW;
const uint8_t ROW_OUT_PINS[LAYOUT_ROWS] = {14, 15, 26, 27};   // OUT_R1..R4 (A0, A1, A12, A13); no internal pull: 100 kohm to GND on the board
const uint8_t SR_DATA_PIN = 2, SR_CLK_PIN = 3;                // SCAN_DATA, SCAN_CLK (SRCLK and RCLK of every 595 tied together)
const uint8_t CHG_STAT_PIN = 0;         // moved off 26 (now OUT_R3); low = charging, only with USB power
const int SR_STAGES = 8 * V4_STRIPS_PER_ROW;   // each strip's 595 has 8 stages, only QA..QD (the first 4) carry sensors
const uint32_t SR_HALF_PERIOD_NS = 100;        // 74HC595 at 3.3 V: CLK up to 5 MHz
// Hot scan: a key that has just started to move is read again on its own (about
// 70 us per column instead of a whole pass) until it passes the note-on level.
const uint32_t HOT_BUDGET_US = 3000;
const float HOT_FROM = 0.03f;
// V4 switches (TODO = depends on a decision of the electronics agent):
#define V4_FORCE_FULL_SPEED 1            // USB at 12 Mbit/s (R1V4 5.4 item 3); untested on a board
#define V4_HAVE_OLED 1                   // 128 x 64 SSD1306 on I2C 0x3C (J401, I2C shared with the codec)
#define V4_HAVE_MIC 1                    // PINOS: pin 8 = I2S_RX, "microphone IN" of the codec
const uint8_t OLED_ADDR = 0x3C;
const int OLED_ROTATION = 2;             // as Adafruit_SSD1306::setRotation(2): upside down
#else
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
// Controls board (through J3): volume pot, instrument encoder with a push
// switch (to GND, Teensy pull-ups). The pins stay clear of the Audio Board;
// 6 is its optional memory chip's select, which the eTuttino doesn't fit.
const uint8_t POT_PIN = 22;                            // A8
const uint8_t ENC_A_PIN = 17, ENC_B_PIN = 9, ENC_SW_PIN = 6;
const int ENC_STEPS_PER_DETENT = 4;     // EC11E 15 pulses / 15 detents (SPEC v9): one full Gray cycle per click
const int8_t KEY_INPUT[LAYOUT_ROWS][LAYOUT_COLS] = {
  { -1,  12,  11,  10,   9,   7,   6,   5,   4,   3,   2,   1},
  { 15,  14,  13,   8,   0,  30,  41,  42,  38,  43,  45,  46},
  { -1,  24,  25,  27,  29,  18,  17,  39,  35,  36,  44,  32},
  { -1,  23,  28,  22,  26,  31,  37,  40,  47,  34,  33,  -1},
};
#endif

// Chromatic button accordion layouts. Along a row each key is a minor
// third (+3) above the previous one. On the eTuttino rows 1 and 3 have 11 keys starting at
// column 1 (A3 .. D#6, G#3 .. D6); row 2 has 12 starting at column 0, half
// a key further left (G3 .. E6); row 4 sits on row 2's columns, half a key
// left of row 3, and runs A3 .. C6 (10 keys, column 1 on).
// B-griff is the mirror image of C-griff: rows 1 and 3 swap places, so a
// diagonal step goes the other way. Keep in sync with etutti/etuttino/script.js.
const int8_t FIRST_NOTE[2][LAYOUT_ROWS] = {
  {57, 55, 56, 57},   // C-griff: A3, G3, G#3, A3
  {56, 55, 57, 56},   // B-griff: G#3, G3, A3, G#3
};
const uint8_t FIRST_COL[LAYOUT_ROWS] = {1, 0, 1, 1};
int layoutSystem = 0;   // 0 = C-griff, 1 = B-griff

#if ETUTTI_V4
// Module note map (R1V4 4.4): the keyboard grows to the right in modules of 16
// keys (4 columns = one octave). By default the 1st extra module adds treble
// and the 2nd bass, and so on: 28 = G3-E5, 44 = G3-E6, 60 = G2-E6, 76 = G2-E7.
// Adding bass shifts every key down an octave, so the notes at the left grow lower.
// The user's own map is a TODO (it would be a CC and a place in EEPROM).
const int V4_EXTRA_MODULES = (V4_KEYS - 28) / 16;
const int V4_BASS_MODULES = V4_EXTRA_MODULES / 2;
int noteShift = -12 * V4_BASS_MODULES;   // semitones

// Where the keys are: rows 1 and 3 start at column 1, row 2 fills the width, row 4 stops
// one short (28: 7 + 8 + 7 + 6; each module adds 4 to every row).
bool v4HasKey(int r, int c) {
  if (c < FIRST_COL[r]) return false;
  return r == 3 ? c <= LAYOUT_COLS - 2 : true;
}
#endif

int noteAt(int r, int c) {
  if (c < FIRST_COL[r]) return -1;
  int n = FIRST_NOTE[layoutSystem][r] + 3 * (c - FIRST_COL[r]);
#if ETUTTI_V4
  n += noteShift;
#endif
  return n;
}

// ---- Key sensing ----
// A DRV5056A3 at 3.3 V gives 0.6 V with no field plus 30 mV per mT. The
// magnet's field falls off roughly as 1/distance^3, so the key's travel is
// recovered from the cube root of the field (above the sensor's 0.6 V
// zero), scaled between that key's reading at rest and at the bottom. The
// rest reading is measured at start-up and then follows slow drift; the
// bottom is learnt from the deepest press seen and kept in EEPROM.
//
// The Student V01's sensor is a TMAG5253BA3: 1.65 V with no field and 15 mV
// per mT, up or down according to the magnet's pole (it reads both). Each
// key's direction is taken from its reading at rest, where the magnet
// already gives about 10 mT (0.15 V), and readings that fall are mirrored
// about 1.65 V, so everything below sees a voltage that rises with the
// press, as on the eTuttino.
#if ETUTTI_V4
const int MAX_KEYS = 76;
#else
const int MAX_KEYS = 44;
#endif
const float ADC_PER_VOLT = 4095.0f / 3.3f;
#if ETUTTI_STUDENT
const float SENSOR_ZERO = 1.65f * ADC_PER_VOLT;  // TMAG5253 output at 0 mT
const float SIGN_MIN = 0.04f * ADC_PER_VOLT;     // rest must be this far from 1.65 V to tell the direction
const int DEFAULT_SIGN = 1;                      // direction assumed when it cannot be told (unverified: no board yet)
#if ETUTTI_V4
const uint32_t EEPROM_MAGIC = 0xE7770106;        // V4: key order = row by row from row 1, V4_KEYS keys
#else
const uint32_t EEPROM_MAGIC = 0xE7770105;        // bump when the key count/order changes
#endif
#else
const float SENSOR_ZERO = 0.6f * ADC_PER_VOLT;   // DRV5056 output at 0 mT
const uint32_t EEPROM_MAGIC = 0xE7770004;   // bump when the key count/order changes
#endif
const int MIN_SPAN = 120;          // ADC counts: the least a key is assumed to swing
const float PRESENT_MIN = 0.4f * ADC_PER_VOLT;   // below this, no sensor answered
const float VEL_START = 0.12f;     // travel where the velocity timer starts
const float NOTE_ON_AT = 0.45f;    // note on (about 1.8 mm of the 4.1 mm travel)
const float NOTE_OFF_AT = 0.30f;   // note off (hysteresis against chatter)
const float FAST_MS = 1.0f;        // VEL_START -> NOTE_ON_AT (~1.4 mm) time for velocity 127
const float SLOW_MS = 80.0f;       // ... and for velocity 1
const uint8_t FIXED_VELOCITY = 100;

struct Key {
  int8_t row, col;          // note grid
  uint8_t mux, channel;     // V4: mux = row (OUT line), channel = column
  int8_t sign;              // +1: the reading rises with the press, -1: it falls (Student V01)
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
  float restAtModel;        // V4: rest when the model was last built (skips needless cube roots)
  bool rising;              // V4: the last reading was higher than the one before
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
uint32_t lastActivityAt = 0;   // last key, knob or MIDI message (Student V01: rest and switch-off timers)
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
// Sampled reeds, when reed_samples.cpp is present (see reed_sampler.h): the
// accordion then plays these and the oscillators stay silent.
ReedSampler              reedSmp[NUM_VOICES];
AudioMixer4              voiceMix[NUM_VOICES];   // oscillators, sampled reeds
const bool HAVE_REED_SAMPLES = REED_SAMPLES_PER_RANK > 0;
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
AudioAmplifier           outAmp;              // Student V01: the volume (see setVolume); eTuttino: gain 1
AudioOutputI2S           i2sOut;
AudioControlSGTL5000     codec;
#if ETUTTI_V4 && V4_HAVE_MIC
// Microphone through the codec's MIC input (I2S RX, pin 8); here only a level meter for the OLED.
AudioInputI2S            i2sIn;
AudioAnalyzePeak         micPeak;
AudioConnection          pmic(i2sIn, 0, micPeak, 0);
#endif

#define REED_PATCH(v) \
  AudioConnection pr16_##v(reed[REED_16][v], 0, reedMix[v], 0); \
  AudioConnection prM1_##v(reed[REED_M1][v], 0, reedMix[v], 1); \
  AudioConnection prM2_##v(reed[REED_M2][v], 0, reedMix[v], 2); \
  AudioConnection pr4_##v(reed[REED_4][v], 0, reedMix[v], 3); \
  AudioConnection pm_##v(reedMix[v], 0, voiceMix[v], 0);   AudioConnection pq_##v(reedSmp[v], 0, voiceMix[v], 1);   AudioConnection pb_##v(voiceMix[v], bellows[v]);
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
AudioConnection po(master, 0, outAmp, 0);
AudioConnection pl(outAmp, 0, i2sOut, 0);
AudioConnection pr(outAmp, 0, i2sOut, 1);

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
// The recordings are all stored at the same loudness; these set the balance
// between ranks. The four together must stay under full scale (the samples
// peak at up to 0.98), so they are low and the voice banks make it up.
const float SAMPLED_REED_GAIN[NUM_REEDS] = {0.30f, 0.30f, 0.30f, 0.22f};
const float BANK_GAIN = 0.16f;
const float SAMPLED_BANK_GAIN = 0.80f;   // measured: 8 notes, all four ranks, velocity 127, peak 0.48

// How hard a key is played stands for the bellows pressure: the accordion
// gets louder over 24 dB and, with sampled reeds, brighter (a low-pass from
// 700 Hz at the softest to 16 kHz at the hardest, never under 3x the note).
// Measured on the Teensy, G3 in MM: 27 dB between velocity 4 and 127, of
// which 4 dB is the filter.
const float ACCORDION_DYNAMIC_DB = 24.0f;
float accordionLevel(byte velocity) {
  return powf(10.0f, -ACCORDION_DYNAMIC_DB / 20.0f * (1.0f - velocity / 127.0f));
}
float accordionBrightness(byte velocity, int note) {
  return max(700.0f * powf(2.0f, 4.5f * velocity / 127.0f), 3.0f * noteToFreq(note));
}

bool sampledReeds() {
  return HAVE_REED_SAMPLES && instrument == INST_ACCORDION;
}

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
  if (sampledReeds()) {
    reedSmp[v].retune(note, wetCents);
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
      reedSmp[v].gain(r, (registerMask & (1 << r)) ? SAMPLED_REED_GAIN[r] : 0.0f);
    }
  }
  for (int ch = 0; ch < 4; ch++) {
    accA.gain(ch, sampledReeds() ? SAMPLED_BANK_GAIN : BANK_GAIN);
    accB.gain(ch, sampledReeds() ? SAMPLED_BANK_GAIN : BANK_GAIN);
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
      if (usesOscillators()) {
        bellows[i].noteOff();
        reedSmp[i].noteOff(quadraticMs(releaseCC, 3000));
      } else sampler[i].stop();
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
    float amp = instrument == INST_ACCORDION ? accordionLevel(velocity)
                                             : 0.2f + 0.8f * (velocity / 127.0f);
    AudioNoInterrupts();
    if (sampledReeds()) {
      reedSmp[v].noteOn(note, wetCents, amp, accordionBrightness(velocity, note));
    } else {
      tuneVoice(v, note);
      for (int r = 0; r < NUM_REEDS; r++) reed[r][v].amplitude(amp);
    }
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
    reedSmp[i].stop();
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
    reedSmp[i].noteOff(quadraticMs(releaseCC, 3000));
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

// Volume, 0..127. eTuttino: the codec's headphone amplifier. Student V01: a
// gain before the I2S output, because the speaker amplifier takes the same
// I2S signal as the codec and has no volume of its own.
int volumeNow = 90;
void setVolume(int v) {
  volumeNow = constrain(v, 0, 127);
#if ETUTTI_STUDENT
  float x = volumeNow / 127.0f;
  outAmp.gain(x * x);
#else
  codec.volume(0.8f * volumeNow / 127.0f);
#endif
}

#if ETUTTI_STUDENT
void registerChanged();   // keeps the selector in step with a register set over MIDI
#endif

void handleControlChange(byte channel, byte control, byte value) {
  switch (control) {
    case 7:
      setVolume(value);
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
#if ETUTTI_STUDENT
      registerChanged();
#endif
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

#if !ETUTTI_V4
void selectChannel(int ch) {
  for (int b = 0; b < 4; b++) digitalWriteFast(MUX_SEL_PINS[b], (ch >> b) & 1);
}
#endif

float fieldInv(float reading) {
  return 1.0f / cbrtf(max(reading - SENSOR_ZERO, 4.0f));
}

void updateModel(Key &k) {
  float bottom = max(k.bottom, k.rest + MIN_SPAN);
  k.restAtModel = k.rest;
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

#if ETUTTI_V4
// ---- Student V4 sensor scan (R2V4) ----
// A "1" in the chain of 74HC595 switches ON the sensor at that stage (EN high); everything
// else is off, so the OUT lines stay free. Contract from PINOS.md:
//  - SRCLK and RCLK share one line, so the OUTPUT lags the shift by one pulse (it shows the
//    state before the pulse);
//  - each strip has 8 stages but only QA..QD carry sensors: global column c = strip c/4,
//    sensor c%4 = stage 8 * (c/4) + c%4 (stage 0 = first strip's QA, nearest DATA); between
//    strips the "1" passes 4 dead stages (columns 3 -> 4 take 5 pulses, others 1);
//  - the outputs are not high-impedance at power-up: srClear() shifts zeros through every stage.
int srPos = -1;                         // column switched on, -1 = none known
uint8_t colKey[LAYOUT_COLS][LAYOUT_ROWS];   // key index at (column, row), 255 = none

inline void srPulse(bool bit) {
  digitalWriteFast(SR_DATA_PIN, bit);
  delayNanoseconds(SR_HALF_PERIOD_NS);
  digitalWriteFast(SR_CLK_PIN, HIGH);
  delayNanoseconds(SR_HALF_PERIOD_NS);
  digitalWriteFast(SR_CLK_PIN, LOW);
}

void srClear() {                        // every sensor off (SR_STAGES zeros + the pulse that latches them)
  for (int i = 0; i <= SR_STAGES; i++) srPulse(0);
  srPos = -1;
}

// Switches column c on. The next column in order is 1 pulse away (5 across a strip boundary).
// Anywhere else: push the whole pattern (the first bit sent ends in the LAST stage), plus one
// pulse to latch it: SR_STAGES + 1 pulses, ~10 us with 76 keys.
void srSelect(int c) {
  if (srPos >= 0 && c == srPos + 1) {
    int pulses = (c % 4 == 0) ? 5 : 1;
    for (int i = 0; i < pulses; i++) srPulse(0);
  } else {
    int target = 8 * (c / 4) + c % 4;
    for (int k = 0; k < SR_STAGES; k++) srPulse(SR_STAGES - 1 - k == target);
    srPulse(0);
  }
  srPos = c;
}

// Reads the sensors of the selected column (after the wake-up), one per row, with
// the time of each reading. Rows with no key there are skipped (5.6 us each).
void readColumn(int c, uint16_t *raw, uint32_t *at) {
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    uint8_t i = colKey[c][r];
    if (i == 255) continue;
    uint16_t v = analogRead(ROW_OUT_PINS[r]);
    at[r] = micros();
    raw[r] = keyState[i].sign < 0 ? 4095 - v : v;   // falling readings mirrored about mid-scale
  }
}

// Whole pass, no tricks, one column at a time (used for the rest readings at start-up).
void readSensors(uint16_t *readings) {
  uint16_t raw[LAYOUT_ROWS];
  uint32_t at[LAYOUT_ROWS];
  for (int c = 0; c < LAYOUT_COLS; c++) {
    srSelect(c);
    delayMicroseconds(SENSOR_WAKE_US);
    readColumn(c, raw, at);
    for (int r = 0; r < LAYOUT_ROWS; r++) if (colKey[c][r] != 255) readings[colKey[c][r]] = raw[r];
  }
}
#else
// Reads every sensor once into readings[] (key order), one multiplexer
// channel at a time: all three multiplexers share the address lines.
void readSensors(uint16_t *readings) {
#if ETUTTI_STUDENT
  static int group = -1;                        // which half of the sensors is powered (S3)
#endif
  for (int ch = 0; ch < 16; ch++) {
    bool any = false;
    for (int i = 0; i < keyCount; i++) any |= keyState[i].channel == ch;
    if (!any) continue;
    selectChannel(ch);
#if ETUTTI_STUDENT
    if ((ch >> 3) != group) {                   // S3 changed: the other half is waking up
      group = ch >> 3;
      delayMicroseconds(SENSOR_WAKE_US);
    } else
#endif
    delayMicroseconds(3);                       // let the multiplexer settle
    for (int i = 0; i < keyCount; i++) {
      if (keyState[i].channel != ch) continue;
      uint16_t raw = analogRead(MUX_COM_PINS[keyState[i].mux]);
      readings[i] = keyState[i].sign < 0 ? 4095 - raw : raw;   // falling readings mirrored about mid-scale
    }
  }
}
#endif

void setupKeys() {
#if ETUTTI_V4
  pinMode(SR_DATA_PIN, OUTPUT);
  pinMode(SR_CLK_PIN, OUTPUT);
  digitalWriteFast(SR_CLK_PIN, LOW);
  for (int r = 0; r < LAYOUT_ROWS; r++) pinMode(ROW_OUT_PINS[r], INPUT_DISABLE);   // the board's 100 kohm pull-down makes a missing sensor read 0 V
  memset(colKey, 255, sizeof(colKey));
  srClear();
#elif ETUTTI_STUDENT
  pinMode(SENS_EN_PIN, OUTPUT);
  digitalWriteFast(SENS_EN_PIN, HIGH);
#endif
#if !ETUTTI_V4
  for (int b = 0; b < 4; b++) pinMode(MUX_SEL_PINS[b], OUTPUT);
  // A sensor drives its line to 0.6 V or more. With the pull-downs, a
  // missing board, multiplexer or sensor reads 0 V instead of floating
  // (which would play random notes), and that key is left out.
  for (int m = 0; m < MUX_COUNT; m++) pinMode(MUX_COM_PINS[m], INPUT_PULLDOWN);
#endif
  analogReadResolution(12);
  analogReadAveraging(1);
  keyCount = 0;
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    for (int c = 0; c < LAYOUT_COLS; c++) {
#if ETUTTI_V4
      if (!v4HasKey(r, c) || keyCount == MAX_KEYS) continue;
#else
      if (KEY_INPUT[r][c] < 0 || keyCount == MAX_KEYS) continue;
#endif
      Key &k = keyState[keyCount++];
      memset(&k, 0, sizeof(k));
      k.row = r;
      k.col = c;
#if ETUTTI_V4
      k.mux = r;
      k.channel = c;
      colKey[c][r] = keyCount - 1;
#else
      k.mux = KEY_INPUT[r][c] / 16;
      k.channel = KEY_INPUT[r][c] % 16;
#endif
      k.note = -1;
      k.sentPosition = 255;
      k.sign = 1;
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
#if ETUTTI_STUDENT
    // Which way this key's sensor goes: the magnet at rest already pushes
    // the reading off 1.65 V, up or down.
    float off = keyState[i].rest - SENSOR_ZERO;
    keyState[i].sign = off > SIGN_MIN ? 1 : (off < -SIGN_MIN ? -1 : DEFAULT_SIGN);
    if (keyState[i].sign < 0) keyState[i].rest = 4095.0f - keyState[i].rest;
#endif
  }
  loadCalibration();
}

// Time (in micros) at which the travel crossed `level`, interpolated
// between the previous scan and this one.
uint32_t crossingTime(const Key &k, float prev, float now, float level, uint32_t nowMicros) {
  float f = (level - prev) / max(now - prev, 1e-4f);
  return k.prevMicros + (uint32_t)(constrain(f, 0.0f, 1.0f) * (float)(nowMicros - k.prevMicros));
}

// One key, one reading (taken at `now`, in micros): calibration, note on/off with
// velocity, and the key test stream. Returns true if something was sent.
bool processKey(int i, float raw, uint32_t now) {
  bool changed = false;
  Key &k = keyState[i];
  if (!k.present) return false;
  // Calibration. A reading below rest means rest was measured with the
  // key held, or has drifted: take it. While the key is up, follow slow
  // drift. The deepest press seen sets the bottom (saved after 5 s).
  if (raw < k.rest - 2 && raw >= PRESENT_MIN) {
    k.rest = raw;
    updateModel(k);
  } else if (!k.down && k.travel < 0.05f) {
    k.rest += (raw - k.rest) * 0.002f;
#if ETUTTI_V4
    if (fabsf(k.rest - k.restAtModel) > 0.5f) updateModel(k);   // 76 keys: do not take cube roots every pass
#else
    updateModel(k);
#endif
  }
  if (raw > k.bottom + 4 && raw > k.rest + MIN_SPAN) {
    k.bottom = raw;
    updateModel(k);
    calibrationDirty = true;
    calibrationChangedAt = millis();
  }
  float t = keyTravel(k, raw);
  k.rising = t > k.travel + 0.002f;
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
  return changed;
}

// After a pass: save the calibration once it has settled, flush the MIDI messages.
void finishScan(bool changed) {
  if (calibrationDirty && millis() - calibrationChangedAt > 5000) saveCalibration();
  if (changed) {
    usbMIDI.send_now();
    lastActivityAt = millis();
  }
}

#if ETUTTI_V4
bool keysBusy = false;   // some key is off its rest position (the OLED waits, I2C would stall the scan)

// One pass over all the keys, a column at a time. While the next column's sensors
// wake up (SENSOR_WAKE_US) the previous column's readings are processed, so the
// wake-up costs no extra time for the arithmetic. Then the "hot scan".
void scanKeys() {
  uint16_t raw[LAYOUT_ROWS];
  uint32_t at[LAYOUT_ROWS];
  bool changed = false;
  srSelect(0);
  uint32_t ready = micros() + SENSOR_WAKE_US;
  for (int c = 0; c < LAYOUT_COLS; c++) {
    while ((int32_t)(micros() - ready) < 0) {
    }
    readColumn(c, raw, at);
    if (c + 1 < LAYOUT_COLS) {
      srSelect(c + 1);
      ready = micros() + SENSOR_WAKE_US;
    }
    for (int r = 0; r < LAYOUT_ROWS; r++) {
      if (colKey[c][r] != 255) changed |= processKey(colKey[c][r], raw[r], at[r]);
    }
  }
  // Hot scan: keys that are travelling up towards the note-on level are read again,
  // their column alone, so a fast press is timed finely however many keys there are.
  uint32_t hotStart = micros();
  while (micros() - hotStart < HOT_BUDGET_US) {
    int hotColumn = -1;
    for (int i = 0; i < keyCount && hotColumn < 0; i++) {
      const Key &k = keyState[i];
      if (k.present && !k.down && k.rising && k.travel >= HOT_FROM && k.travel < NOTE_ON_AT) hotColumn = k.col;
    }
    if (hotColumn < 0) break;
    srSelect(hotColumn);
    delayMicroseconds(SENSOR_WAKE_US);
    readColumn(hotColumn, raw, at);
    for (int r = 0; r < LAYOUT_ROWS; r++) {
      if (colKey[hotColumn][r] != 255) changed |= processKey(colKey[hotColumn][r], raw[r], at[r]);
    }
  }
  keysBusy = false;
  for (int i = 0; i < keyCount; i++) keysBusy |= keyState[i].down || keyState[i].travel > 0.02f;
  finishScan(changed);
}
#else
// One pass over all the sensors (~3.3 kHz with 44): calibration, note on/off with
// velocity, and the key test stream.
void scanKeys() {
  uint16_t readings[MAX_KEYS];
  readSensors(readings);
  uint32_t now = micros();
  bool changed = false;
  for (int i = 0; i < keyCount; i++) changed |= processKey(i, readings[i], now);
  finishScan(changed);
}
#endif

// The page's "Reset to default": classic accordion, register MM, dry.
void defaultSound() {
  setInstrument(INST_ACCORDION);
  registerMask = 0b0110;
  wetCents = 0;
  applyOscGains();
  retuneAll();
}

bool instrumentPending = false;         // a knob choice made, not yet kept with a click

#if !ETUTTI_STUDENT
// ---- Controls board: volume pot and instrument encoder ----
bool potPresent = false;
float potFiltered = 0;
int potVolume = -1;                     // last volume the pot set (0..127)
uint32_t potReadAt = 0;
volatile int16_t encSteps = 0;          // quarter steps, counted in the interrupt
volatile uint8_t encPrev = 0;
bool swDown = false;
uint32_t swChangedAt = 0;
const int EEPROM_INSTRUMENT = 200;      // after the key calibration (4 + 2 * 44 bytes)
const uint8_t INSTRUMENT_MAGIC = 0xA5;

void encoderIsr() {
  // Gray-code state table: +1 / -1 per valid transition, 0 for bounces.
  static const int8_t table[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
  uint8_t s = (digitalReadFast(ENC_A_PIN) << 1) | digitalReadFast(ENC_B_PIN);
  encSteps += table[(encPrev << 2) | s];
  encPrev = s;
}

void saveInstrument(int inst) {
  EEPROM.write(EEPROM_INSTRUMENT, INSTRUMENT_MAGIC);
  EEPROM.write(EEPROM_INSTRUMENT + 1, (uint8_t)inst);
}

int savedInstrument() {
  if (EEPROM.read(EEPROM_INSTRUMENT) != INSTRUMENT_MAGIC) return INST_ACCORDION;
  return min((int)EEPROM.read(EEPROM_INSTRUMENT + 1), INST_SYNTH);
}

void setupControls() {
  // A pot holds its pin against the Teensy's weak pull-up / pull-down; with
  // nothing on J3 the pin simply follows them.
  pinMode(POT_PIN, INPUT_PULLUP);
  delayMicroseconds(200);
  int up = analogRead(POT_PIN);
  pinMode(POT_PIN, INPUT_PULLDOWN);
  delayMicroseconds(200);
  int down = analogRead(POT_PIN);
  pinMode(POT_PIN, INPUT_DISABLE);
  potPresent = !(up > 3900 && down < 200);
  if (potPresent) {
    potFiltered = analogRead(POT_PIN);
    potVolume = lroundf(potFiltered * 127.0f / 4095.0f);
    codec.volume(0.8f * potVolume / 127.0f);
  }
  pinMode(ENC_A_PIN, INPUT_PULLUP);
  pinMode(ENC_B_PIN, INPUT_PULLUP);
  pinMode(ENC_SW_PIN, INPUT_PULLUP);
  encPrev = (digitalReadFast(ENC_A_PIN) << 1) | digitalReadFast(ENC_B_PIN);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PIN), encoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B_PIN), encoderIsr, CHANGE);
}

void updateControls() {
  uint32_t now = millis();
  // volume pot, every 5 ms, smoothed; only moves of 2 steps or more count
  if (potPresent && now - potReadAt >= 5) {
    potReadAt = now;
    potFiltered += (analogRead(POT_PIN) - potFiltered) * 0.15f;
    int v = lroundf(potFiltered * 127.0f / 4095.0f);
    if (abs(v - potVolume) >= 2 || ((v == 0 || v == 127) && v != potVolume)) {
      potVolume = v;
      codec.volume(0.8f * v / 127.0f);
      usbMIDI.sendControlChange(7, v, 1);
    }
  }
  // encoder: whole detents only
  noInterrupts();
  int detents = encSteps / ENC_STEPS_PER_DETENT;
  encSteps -= detents * ENC_STEPS_PER_DETENT;
  interrupts();
  if (detents) {
    int next = ((instrument + detents) % 5 + 5) % 5;
    setInstrument(next);
    instrumentPending = true;
    usbMIDI.sendControlChange(25, next * 16 + 8, 1);
  }
  // push switch, debounced: act on the press
  bool down = digitalReadFast(ENC_SW_PIN) == LOW;
  if (down != swDown && now - swChangedAt > 20) {
    swDown = down;
    swChangedAt = now;
    if (down) {
      if (instrumentPending) {
        saveInstrument(instrument);           // the one to start with next time
        instrumentPending = false;
      } else {
        defaultSound();
        saveInstrument(INST_ACCORDION);
        usbMIDI.sendControlChange(25, INST_ACCORDION * 16 + 8, 1);
      }
    }
  }
}

void setLed(bool red, bool green) {
  digitalWriteFast(LED_PINS[0], red);
  digitalWriteFast(LED_PINS[1], green);
}

// Green while all is well (blinking slowly while a new instrument picked
// with the encoder waits for its click); red, blinking twice a second, on
// an error.
void updateLed() {
  if (codecOk && missingKeys == 0) setLed(false, !instrumentPending || (millis() / 300) % 2 == 0);
  else setLed((millis() / 250) % 2 == 0, false);
}

#else
// ============================================================
// Student V01: power, battery, speaker and the two knobs.
// Written against the pin map and the power notes of
// etutti/hardware/viaggio_micromod/pcb/PINOS.md. NOT yet run on a board:
// every threshold and time here is a first value.
//
//   volume knob    turn: volume (sends CC 7 back)
//                  click held 2 s: on / off
//   selector knob  turn: the seven accordion registers, in this order:
//                  L Bassoon, ML Bandoneon, MM Violin, MH Oboe, H Piccolo,
//                  LH Organ, M Clarinet (sends CC 26 back); the LED blinks
//                  green until the choice is kept
//                  click after turning: keep it, and start with it next time
//                  click otherwise: back to MM, dry
//   LED            orange  starting up; charging while switched on
//                  green   on (blinking: a register waits for its click;
//                          a short flash every 2 s: resting, speaker off)
//                  red     slow blink: battery low; fast blink: the codec or
//                          a key's sensor did not answer
//   speaker        on when no headphones are plugged in
//   battery        off by itself when nearly empty, and after 15 minutes
//                  without a key, a knob or a MIDI message (5 minutes: the
//                  speaker amplifier rests). Never while USB power is there.
// The other instruments (piano, bass, guitar, synth) still answer to CC 25
// from the page.
// ============================================================
const uint8_t REGISTERS[7] = {1, 3, 6, 10, 8, 9, 2};   // CC 26 masks, in the selector's order
const int DEFAULT_REGISTER = 2;                         // MM
const int VOLUME_PER_DETENT = 3;
const uint32_t POWER_HOLD_MS = 2000;
const uint32_t IDLE_REST_MS = 5UL * 60 * 1000;
const uint32_t IDLE_OFF_MS = 15UL * 60 * 1000;
const float BATTERY_LOW_V = 3.5f;
const float BATTERY_EMPTY_V = 3.3f;
const int EEPROM_REGISTER = 200;        // after the key calibration (4 + 2 * 28 bytes)
const uint8_t REGISTER_MAGIC = 0xA6;

int registerIndex = DEFAULT_REGISTER;
volatile int16_t encSteps = 0, volSteps = 0;   // quarter steps, counted in the interrupts
volatile uint8_t encPrev = 0, volPrev = 0;
bool selDown = false, volDown = false;
uint32_t selChangedAt = 0, volChangedAt = 0;
bool volIgnoreHold = false;             // the hold that switched it on must not switch it off again
float batteryVolts = 4.0f;
uint32_t batteryReadAt = 0, batteryEmptySince = 0;
bool headphones = false, resting = false;
uint32_t jackReadAt = 0;

// Gray-code state table: +1 / -1 per valid transition, 0 for bounces.
const int8_t GRAY_STEP[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};

void encoderIsr() {
  uint8_t s = (digitalReadFast(ENC_A_PIN) << 1) | digitalReadFast(ENC_B_PIN);
  encSteps += GRAY_STEP[(encPrev << 2) | s];
  encPrev = s;
}

void volumeIsr() {
  uint8_t s = (digitalReadFast(VOL_A_PIN) << 1) | digitalReadFast(VOL_B_PIN);
  volSteps += GRAY_STEP[(volPrev << 2) | s];
  volPrev = s;
}

void setLed(bool red, bool green) {
  digitalWriteFast(LED_PINS[0], red);
  digitalWriteFast(LED_PINS[1], green);
}

// True while the USB socket has power (the module's USB1 sees VBUS).
bool usbPower() {
  return (USB1_OTGSC & (1 << 11)) != 0;   // BSV: B-session (VBUS) valid
}

// Everything off. The 3.3 V supply falls as soon as the volume click is let
// go (at once if it is not held); pin 28 low makes that true on USB power
// too, where only the charger stays alive.
#if ETUTTI_V4
void oledOff();
#endif
void powerOff() {
  silenceAll();
  digitalWriteFast(AMP_SD_PIN, LOW);
#if ETUTTI_V4
  srClear();
  oledOff();
#else
  digitalWriteFast(SENS_EN_PIN, LOW);
#endif
  if (calibrationDirty) saveCalibration();
  setLed(true, false);
  delay(250);
  setLed(false, false);                 // LED out: the click can be let go
  digitalWriteFast(KEEP_PIN, LOW);
#if ETUTTI_V4
  // V4: nothing cuts the 3.3 V while USB is plugged in (PWR_EN is not wired in V3/V4),
  // so "off" is a soft off: everything above is already dark. A click, or unplugging
  // the cable (the supply then falls by itself), ends it; the click restarts the processor.
  while (usbPower() && digitalReadFast(VOL_SW_PIN) == HIGH) delay(20);
  SCB_AIRCR = 0x05FA0004;               // system reset
#else
  pinMode(PWR_EN_PIN, OUTPUT);
  digitalWriteFast(PWR_EN_PIN, LOW);
#endif
  while (true) {
  }
}

// First thing in setup(). Switched on with the click, the board only stays
// on if the click is still down 2 s after power-up; let go sooner, it goes
// off again. With no click at all the processor was restarted while USB
// held the supply (a firmware upload): stay on.
void powerBegin() {
  pinMode(KEEP_PIN, OUTPUT);
  digitalWriteFast(KEEP_PIN, LOW);
  pinMode(AMP_SD_PIN, OUTPUT);
  digitalWriteFast(AMP_SD_PIN, LOW);
#if !ETUTTI_V4
  pinMode(SENS_EN_PIN, OUTPUT);
  digitalWriteFast(SENS_EN_PIN, LOW);
#endif
  pinMode(VOL_SW_PIN, INPUT_PULLUP);
  pinMode(CHG_STAT_PIN, INPUT_PULLUP);
  // The click also reaches the processor's ONOFF pin: held 10 s it cuts the
  // processor's own supply, whatever this firmware is doing.
  SNVS_LPCR = (SNVS_LPCR & ~(3 << 16)) | (1 << 16);
  delay(5);
  if (digitalReadFast(VOL_SW_PIN) == HIGH) {
    digitalWriteFast(KEEP_PIN, HIGH);
    return;
  }
  while (millis() < POWER_HOLD_MS) {
    if (digitalReadFast(VOL_SW_PIN) == HIGH) powerOff();
    setLed((millis() / 150) % 2 == 0, (millis() / 150) % 2 == 0);
  }
  digitalWriteFast(KEEP_PIN, HIGH);
  volIgnoreHold = true;
}

void applyRegister(int index, bool tell) {
  registerIndex = ((index % 7) + 7) % 7;
  if (instrument != INST_ACCORDION) setInstrument(INST_ACCORDION);
  registerMask = REGISTERS[registerIndex];
  applyOscGains();
  if (tell) usbMIDI.sendControlChange(26, registerMask, 1);
}

// A register set over MIDI (CC 26): the selector carries on from it.
void registerChanged() {
  for (int i = 0; i < 7; i++) {
    if (REGISTERS[i] == registerMask) registerIndex = i;
  }
}

int savedRegister() {
  if (EEPROM.read(EEPROM_REGISTER) != REGISTER_MAGIC) return DEFAULT_REGISTER;
  return min((int)EEPROM.read(EEPROM_REGISTER + 1), 6);
}

void saveRegister(int index) {
  EEPROM.write(EEPROM_REGISTER, REGISTER_MAGIC);
  EEPROM.write(EEPROM_REGISTER + 1, (uint8_t)index);
}

void setupControls() {
  pinMode(VOL_A_PIN, INPUT_PULLUP);
  pinMode(VOL_B_PIN, INPUT_PULLUP);
  pinMode(ENC_A_PIN, INPUT_PULLUP);
  pinMode(ENC_B_PIN, INPUT_PULLUP);
  pinMode(ENC_SW_PIN, INPUT_PULLUP);
  pinMode(HP_DET_PIN, INPUT_DISABLE);
  pinMode(VBAT_PIN, INPUT_DISABLE);
  volPrev = (digitalReadFast(VOL_A_PIN) << 1) | digitalReadFast(VOL_B_PIN);
  encPrev = (digitalReadFast(ENC_A_PIN) << 1) | digitalReadFast(ENC_B_PIN);
  attachInterrupt(digitalPinToInterrupt(VOL_A_PIN), volumeIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(VOL_B_PIN), volumeIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PIN), encoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B_PIN), encoderIsr, CHANGE);
  batteryVolts = analogRead(VBAT_PIN) * 2.0f / ADC_PER_VOLT;
  volDown = digitalReadFast(VOL_SW_PIN) == LOW;
}

void updateControls() {
  uint32_t now = millis();
  // volume knob
  noInterrupts();
  int turned = volSteps / ENC_STEPS_PER_DETENT;
  volSteps -= turned * ENC_STEPS_PER_DETENT;
  interrupts();
  if (turned) {
    setVolume(volumeNow + turned * VOLUME_PER_DETENT);
    usbMIDI.sendControlChange(7, volumeNow, 1);
    lastActivityAt = now;
  }
  // volume click: held 2 s = off
  bool down = digitalReadFast(VOL_SW_PIN) == LOW;
  if (down != volDown && now - volChangedAt > 20) {
    volDown = down;
    volChangedAt = now;
    if (!down) volIgnoreHold = false;
    lastActivityAt = now;
  }
  if (volDown && !volIgnoreHold && now - volChangedAt >= POWER_HOLD_MS) powerOff();
  // selector knob: whole detents only
  noInterrupts();
  int detents = encSteps / ENC_STEPS_PER_DETENT;
  encSteps -= detents * ENC_STEPS_PER_DETENT;
  interrupts();
  if (detents) {
    applyRegister(registerIndex + detents, true);
    instrumentPending = true;
    lastActivityAt = now;
  }
  down = digitalReadFast(ENC_SW_PIN) == LOW;
  if (down != selDown && now - selChangedAt > 20) {
    selDown = down;
    selChangedAt = now;
    lastActivityAt = now;
    if (down) {
      if (instrumentPending) {
        saveRegister(registerIndex);        // the one to start with next time
        instrumentPending = false;
      } else {
        defaultSound();
        registerIndex = DEFAULT_REGISTER;
        saveRegister(DEFAULT_REGISTER);
        usbMIDI.sendControlChange(26, registerMask, 1);
      }
    }
  }
}

// Battery, headphone socket and the rest / switch-off timers.
void updatePower() {
  uint32_t now = millis();
  bool usb = usbPower();
  if (now - batteryReadAt >= 500) {
    batteryReadAt = now;
    batteryVolts += (analogRead(VBAT_PIN) * 2.0f / ADC_PER_VOLT - batteryVolts) * 0.1f;
    if (usb || batteryVolts >= BATTERY_EMPTY_V) batteryEmptySince = 0;
    else if (batteryEmptySince == 0) batteryEmptySince = now | 1;
    else if (now - batteryEmptySince > 10000) powerOff();
  }
  if (now - jackReadAt >= 50) {
    jackReadAt = now;
    float volts = analogRead(HP_DET_PIN) / ADC_PER_VOLT;
    if (volts < 0.5f) headphones = true;
    else if (volts > 0.9f) headphones = false;
  }
#if !ETUTTI_V4
  if (usb) lastActivityAt = now;        // V01: never off while the cable is in
#endif
  resting = now - lastActivityAt > IDLE_REST_MS;
  if (now - lastActivityAt > IDLE_OFF_MS) powerOff();
  digitalWriteFast(AMP_SD_PIN, !headphones && !resting);
}

#if ETUTTI_V4 && V4_HAVE_OLED
// ---- Student V4 OLED: 128 x 64 SSD1306 on I2C ----
// No library is installed with Teensyduino for it, so this is a small driver of its own:
// a 1 KB frame buffer, a 5 x 7 font (digits and capitals), sent to the panel in 16-byte
// pieces, one per loop pass, and only while no key is moving: I2C is blocking and a piece
// takes ~0.4 ms. OLED_ROTATION 2 = what Adafruit_SSD1306::setRotation(2) does (the
// panel mounted upside down), done by the controller's segment remap + COM scan direction.
uint8_t oledBuf[1024];
bool oledPresent = false;
int oledSent = 1024;                    // bytes of the frame already sent (1024 = idle)
uint32_t oledSig = 0xFFFFFFFF, oledDrawnAt = 0;

const uint8_t FONT5X7[59][5] = {        // ASCII 32 (space) .. 90 (Z)
  {0x00,0x00,0x00,0x00,0x00},{0x00,0x00,0x5F,0x00,0x00},{0x00,0x07,0x00,0x07,0x00},{0x14,0x7F,0x14,0x7F,0x14},
  {0x24,0x2A,0x7F,0x2A,0x12},{0x23,0x13,0x08,0x64,0x62},{0x36,0x49,0x55,0x22,0x50},{0x00,0x05,0x03,0x00,0x00},
  {0x00,0x1C,0x22,0x41,0x00},{0x00,0x41,0x22,0x1C,0x00},{0x14,0x08,0x3E,0x08,0x14},{0x08,0x08,0x3E,0x08,0x08},
  {0x00,0x50,0x30,0x00,0x00},{0x08,0x08,0x08,0x08,0x08},{0x00,0x60,0x60,0x00,0x00},{0x20,0x10,0x08,0x04,0x02},
  {0x3E,0x51,0x49,0x45,0x3E},{0x00,0x42,0x7F,0x40,0x00},{0x42,0x61,0x51,0x49,0x46},{0x21,0x41,0x45,0x4B,0x31},
  {0x18,0x14,0x12,0x7F,0x10},{0x27,0x45,0x45,0x45,0x39},{0x3C,0x4A,0x49,0x49,0x30},{0x01,0x71,0x09,0x05,0x03},
  {0x36,0x49,0x49,0x49,0x36},{0x06,0x49,0x49,0x29,0x1E},{0x00,0x36,0x36,0x00,0x00},{0x00,0x56,0x36,0x00,0x00},
  {0x08,0x14,0x22,0x41,0x00},{0x14,0x14,0x14,0x14,0x14},{0x00,0x41,0x22,0x14,0x08},{0x02,0x01,0x51,0x09,0x06},
  {0x32,0x49,0x79,0x41,0x3E},{0x7E,0x11,0x11,0x11,0x7E},{0x7F,0x49,0x49,0x49,0x36},{0x3E,0x41,0x41,0x41,0x22},
  {0x7F,0x41,0x41,0x22,0x1C},{0x7F,0x49,0x49,0x49,0x41},{0x7F,0x09,0x09,0x09,0x01},{0x3E,0x41,0x49,0x49,0x7A},
  {0x7F,0x08,0x08,0x08,0x7F},{0x00,0x41,0x7F,0x41,0x00},{0x20,0x40,0x41,0x3F,0x01},{0x7F,0x08,0x14,0x22,0x41},
  {0x7F,0x40,0x40,0x40,0x40},{0x7F,0x02,0x0C,0x02,0x7F},{0x7F,0x04,0x08,0x10,0x7F},{0x3E,0x41,0x41,0x41,0x3E},
  {0x7F,0x09,0x09,0x09,0x06},{0x3E,0x41,0x51,0x21,0x5E},{0x7F,0x09,0x19,0x29,0x46},{0x46,0x49,0x49,0x49,0x31},
  {0x01,0x01,0x7F,0x01,0x01},{0x3F,0x40,0x40,0x40,0x3F},{0x1F,0x20,0x40,0x20,0x1F},{0x3F,0x40,0x38,0x40,0x3F},
  {0x63,0x14,0x08,0x14,0x63},{0x07,0x08,0x70,0x08,0x07},{0x61,0x51,0x49,0x45,0x43}
};

void oledCmd(uint8_t c) {
  Wire.beginTransmission(OLED_ADDR);
  Wire.write(0x00);
  Wire.write(c);
  Wire.endTransmission();
}

void oledPixel(int x, int y, bool on) {
  if (x < 0 || x > 127 || y < 0 || y > 63) return;
  if (on) oledBuf[x + (y >> 3) * 128] |= 1 << (y & 7);
  else oledBuf[x + (y >> 3) * 128] &= ~(1 << (y & 7));
}

void oledRect(int x, int y, int w, int h, bool on) {
  for (int j = 0; j < h; j++) for (int i = 0; i < w; i++) oledPixel(x + i, y + j, on);
}

// Capitals, digits and a little punctuation only (ASCII 32..90); lower case is shown as capitals.
void oledText(int x, int y, const char *str, int scale) {
  for (; *str; str++) {
    int ch = *str;
    if (ch >= 'a' && ch <= 'z') ch -= 32;
    if (ch < 32 || ch > 90) ch = '?';
    for (int col = 0; col < 5; col++) {
      uint8_t bits = FONT5X7[ch - 32][col];
      for (int row = 0; row < 7; row++) {
        if (bits & (1 << row)) oledRect(x + col * scale, y + row * scale, scale, scale, true);
      }
    }
    x += 6 * scale;
  }
}

// Battery charge from its voltage at rest (a first, typical LiPo curve; 4.2 V full).
int batteryPercent(float v) {
  static const float volts[] = {3.30f, 3.40f, 3.55f, 3.65f, 3.70f, 3.75f, 3.80f, 3.85f, 3.92f, 4.00f, 4.10f, 4.20f};
  static const int pct[]     = {0,     3,     10,    20,    30,    40,    50,    60,    70,    80,    90,    100};
  if (v <= volts[0]) return 0;
  for (int i = 1; i < 12; i++) {
    if (v <= volts[i]) return pct[i - 1] + (int)((pct[i] - pct[i - 1]) * (v - volts[i - 1]) / (volts[i] - volts[i - 1]));
  }
  return 100;
}

const char *const REGISTER_NAMES[7] = {"BASSOON", "BANDONEON", "VIOLIN", "OBOE", "PICCOLO", "ORGAN", "CLARINET"};
const char *const INSTRUMENT_NAMES[5] = {"ACCORDION", "PIANO", "BASS", "GUITAR", "SYNTH"};

void oledSetup() {
  Wire.setClock(400000);
  Wire.beginTransmission(OLED_ADDR);
  oledPresent = Wire.endTransmission() == 0;
  if (!oledPresent) return;
  static const uint8_t init[] = {0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00,
                                 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6};
  for (uint8_t c : init) oledCmd(c);
  // Rotation 0 as Adafruit_SSD1306 starts it = segment remap + COM scan decrement; rotation 2 = both off.
  oledCmd(OLED_ROTATION == 2 ? 0xA0 : 0xA1);
  oledCmd(OLED_ROTATION == 2 ? 0xC0 : 0xC8);
  oledCmd(0xAF);
}

void oledOff() {
  if (oledPresent) oledCmd(0xAE);
}

// Redraws when what is shown has changed (at most 4 times a second), then sends it in pieces.
void updateOled() {
  if (!oledPresent) return;
  if (oledSent < 1024) {
    if (keysBusy) return;               // do not stall the key scan
    Wire.beginTransmission(OLED_ADDR);
    Wire.write(0x40);
    for (int i = 0; i < 16; i++) Wire.write(oledBuf[oledSent + i]);
    Wire.endTransmission();
    oledSent += 16;
    return;
  }
  uint32_t now = millis();
  if (now - oledDrawnAt < 250) return;
  oledDrawnAt = now;
  bool usb = usbPower();
  bool charging = usb && digitalReadFast(CHG_STAT_PIN) == LOW;
  int pct = batteryPercent(batteryVolts);
  int mic = 0;
#if V4_HAVE_MIC
  if (micPeak.available()) mic = (int)(micPeak.read() * 8.0f);   // 0..8
#endif
  uint32_t sig = pct | (volumeNow << 8) | (headphones << 16) | (usb << 17) | (charging << 18)
               | (registerIndex << 19) | (instrument << 22) | (mic << 25) | (resting << 29);
  if (sig == oledSig) return;
  oledSig = sig;
  memset(oledBuf, 0, sizeof(oledBuf));
  char line[24];
  snprintf(line, sizeof(line), "%s %d%%", charging ? "CHG" : (usb ? "USB" : "BAT"), pct);
  oledText(0, 0, line, 2);
  oledText(0, 20, instrument == INST_ACCORDION ? REGISTER_NAMES[registerIndex] : INSTRUMENT_NAMES[instrument], 2);
  snprintf(line, sizeof(line), "VOL %d  %s%s", volumeNow, headphones ? "HP" : "SPK", resting ? "  REST" : "");
  oledText(0, 42, line, 1);
  oledRect(0, 54, 82, 1, true);         // battery bar
  oledRect(0, 63, 82, 1, true);
  oledRect(0, 54, 1, 10, true);
  oledRect(81, 54, 1, 10, true);
  oledRect(2, 56, pct * 78 / 100, 6, true);
  oledText(90, 55, "MIC", 1);
  oledRect(112, 56, mic * 2, 6, true);
  oledSent = 0;
  oledCmd(0x21); oledCmd(0); oledCmd(127);   // column window
  oledCmd(0x22); oledCmd(0); oledCmd(7);     // page window
}
#else
void oledOff() {}
#endif

void updateLed() {
  uint32_t now = millis();
  if (!codecOk || missingKeys > 0) setLed((now / 250) % 2 == 0, false);
  else if (!usbPower() && batteryVolts < BATTERY_LOW_V) setLed((now / 1000) % 2 == 0, false);
  else if (instrumentPending) setLed(false, (now / 300) % 2 == 0);
  else if (resting) setLed(false, now % 2000 < 60);
  else if (usbPower() && digitalReadFast(CHG_STAT_PIN) == LOW) setLed(true, true);
  else setLed(false, true);
}
#endif

#if ETUTTI_V4 && V4_FORCE_FULL_SPEED
// R1V4 5.4, item 3: run the USB port at 12 Mbit/s. The core calls this right after usb_init()
// (the line "USB1_PORTSC1 |= USB_PORTSC1_PFSC; // force 12 Mbit/sec" sits commented out at the
// end of usb_init() in Teensyduino's usb.c); the host's bus reset comes ~100 ms later. The core
// already copes with a full-speed link (usb_high_speed = 0, 64-byte MIDI packets).
extern "C" void startup_late_hook(void) {
  USB1_PORTSC1 |= USB_PORTSC1_PFSC;
}
#endif

void setup() {
  for (int i = 0; i < 2; i++) pinMode(LED_PINS[i], OUTPUT);
#if ETUTTI_STUDENT
  powerBegin();                                  // stays on only if the click was held 2 s
#endif
  setLed(true, true);                            // orange: reading the keys
  uint32_t started = millis();
  AudioMemory(60);   // measured peak: 32 blocks (8 voices x 4 reeds + reverb); 8 with sampled reeds
  setupKeys();

  codecOk = codec.enable();
#if ETUTTI_STUDENT
  codec.volume(0.7f);                            // fixed: the volume knob works before the I2S output
#endif
#if ETUTTI_V4 && V4_HAVE_MIC
  codec.inputSelect(AUDIO_INPUT_MIC);            // TODO(PINOS): the V4 board's microphone input
  codec.micGain(36);
#endif
#if ETUTTI_V4 && V4_HAVE_OLED
  oledSetup();
#endif
  setVolume(90);

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

  // Synthesised accordion voice peaks at 1.56 (all four reeds): 4 voices x
  // 1.56 x 0.16 per bank, banks at 0.5 — a full chord stays under full
  // scale. The bank gains themselves are set in applyOscGains().
  for (int ch = 0; ch < 4; ch++) {
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

#if ETUTTI_STUDENT
  setupControls();
  applyRegister(savedRegister(), false);   // the last register kept with the selector
#else
  setupControls();                   // the pot, if fitted, sets the volume
  setInstrument(savedInstrument());  // the last instrument confirmed with the encoder
#endif

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
    lastActivityAt = millis();
  }
  scanKeys();
  updateControls();
#if ETUTTI_STUDENT
  updatePower();
#endif
#if ETUTTI_V4 && V4_HAVE_OLED
  updateOled();
#endif
  updateLed();
}
