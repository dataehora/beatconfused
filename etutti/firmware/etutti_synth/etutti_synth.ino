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
// register chain that switches one column on at a time), up to 80 keys, an OLED
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

// Student V4 options (SPEC R3V4). All of them only exist in the V4 build.
#if ETUTTI_V4
// Both ADCs at once (Teensyduino's ADC library): the four row lines are read two at a
// time, rows 1+3 together, then rows 2+4 (pins 14/15 reach ADC1 and ADC2, 26/27 only ADC2).
#define V4_ADC_DUAL 1
// Voice effects (R3V4 item 6): vocoder with the keyboard as carrier, pitch shifter,
// echo, voice into the reverb, voice + keyboard mix. Everything starts switched off.
#define V4_VOICE_FX 1
// R4V4 item 4: the voice is heard only on the headphone / AUX jack by default; the speaker is an
// option of the menu (CC 96) and the screen then warns about feedback (no compile switch any more).
// 1 = the key scan runs in a timer interrupt above the audio's priority (see scanTick); 0 = in loop().
#define V4_SCAN_TIMER 1
// 1 = automatic feedback suppressor (FFT of the voice + notches, see voice_fx.h), off until the menu turns it on.
#define V4_FEEDBACK_SUPPRESSOR 1
// R5V4: "study speaker" equalizer on the speaker path only (no headphones plugged): 24 dB/oct high-pass at
// ~300 Hz and a dip near 1 kHz (4 biquad stages). Bypassed (disconnected) with headphones / AUX in.
#define V4_SPEAKER_EQ 1
// Throwaway measuring build, NOT for use: plays 8 notes by itself, steps through the voice
// effects every 6 s and prints the audio CPU, the audio blocks and the time of a key pass on the
// serial port (115200). Build with usb=serialmidi (arduino-cli ... teensyMM:usb=serialmidi,speed=396).
#define V4_BENCH 0
#if V4_ADC_DUAL
#include <ADC.h>
#endif
#if V4_VOICE_FX
#include "voice_fx.h"
#endif
#endif
#if !(ETUTTI_V4 && V4_ADC_DUAL)
inline int analogReadSlow(uint8_t pin) { return analogRead(pin); }   // V4 with the ADC library has its own (below)
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
//   R5V4: every strip is full (all 4 positions carry a key), so 32 keys = 2 strips per row
//   (8 columns), 48 = 3 (12), 64 = 4 (16), 80 = 5 (20).
#define V4_KEYS 32                       // 32, 48, 64 or 80: the number of keys fitted
#if V4_KEYS != 32 && V4_KEYS != 48 && V4_KEYS != 64 && V4_KEYS != 80
#error "V4_KEYS must be 32, 48, 64 or 80"
#endif
const int V4_STRIPS_PER_ROW = (V4_KEYS - 32) / 16 + 2;
const int LAYOUT_ROWS = 4;
const int LAYOUT_COLS = 4 * V4_STRIPS_PER_ROW;
const uint8_t ROW_OUT_PINS[LAYOUT_ROWS] = {14, 15, 26, 27};   // OUT_R1..R4 (A0, A1, A12, A13); no internal pull: 100 kohm to GND on the board
const uint8_t SR_DATA_PIN = 2, SR_CLK_PIN = 3;                // SCAN_DATA, SCAN_CLK (SRCLK and RCLK of every 595 tied together)
const uint8_t CHG_STAT_PIN = 0;         // moved off 26 (now OUT_R3); low = charging, only with USB power
const int SR_STAGES = 8 * V4_STRIPS_PER_ROW;   // each strip's 595 has 8 stages, only QA..QD (the first 4) carry sensors
const uint32_t SR_HALF_PERIOD_NS = 100;        // 74HC595 at 3.3 V: CLK up to 5 MHz
// Hot scan (R3V4 item 5): a key that has started to move up is read again on its own
// column (~85 us per column change, ~56 us for the same column again, instead of a whole
// pass) until it passes the note-on level. All the columns with a moving key take turns,
// the one read longest ago first (round robin), so in a chord the second note gets a
// velocity too. Every key is still read once per pass, and the hot reads of a pass are
// limited (hotBudgetUs) so that no key waits much longer than MAX_KEY_GAP_US between two
// readings: the audio interrupts take (1 - u) of the loop's time, u = AudioProcessorUsage(),
// so the budget shrinks as the sound gets heavier (never below HOT_BUDGET_MIN_US).
const float HOT_FROM = 0.03f;                 // travel where a rising key becomes "hot"
const uint32_t HOT_WINDOW_US = 15000;         // a press slower than this (from VEL_START) is not worth fast reads
const uint32_t HOT_HOLD_US = 2000;            // "rising" is remembered this long (slow, noisy presses)
const uint32_t HOT_MIN_GAP_US = 40;           // least time between two reads of the same column in a burst
const uint32_t MAX_KEY_GAP_US = 2200;         // the target for any key
const uint32_t HOT_BUDGET_MIN_US = 300;       // a few rounds even when the pass alone is already long
#if V4_SCAN_TIMER
const uint32_t SCAN_TICK_US = 12;             // scanTick() runs this often (it returns at once until the sensors are awake)
const int SCAN_PRIORITY = 96;                 // NVIC: lower = more urgent. USB 112, DMA 128 (I2S), audio update 208
const uint32_t PASS_NOMINAL_US = (uint32_t)(LAYOUT_COLS * 72);   // one pass with no hot reads: 60 us wake + ~12 us work
#else
const uint32_t PASS_NOMINAL_US = (uint32_t)(LAYOUT_COLS * 67 + 40);   // one pass with no hot reads, no audio (ADC dual: 60 + 6 + 1)
#endif
// V4 switches (TODO = depends on a decision of the electronics agent):
#define V4_FORCE_FULL_SPEED 1            // USB at 12 Mbit/s (R1V4 5.4 item 3); untested on a board
#define V4_HAVE_OLED 1                   // 128 x 64 SSD1306 on I2C 0x3C (J401, I2C shared with the codec)
#define V4_HAVE_MIC 1                    // PINOS: pin 8 = I2S_RX, "microphone IN" of the codec
#if V4_VOICE_FX && !V4_HAVE_MIC
#error "V4_VOICE_FX needs V4_HAVE_MIC"
#endif
const uint8_t OLED_ADDR = 0x3C;
const int OLED_ROTATION = 2;             // as Adafruit_SSD1306::setRotation(2): upside down
#if V4_HAVE_OLED && V4_VOICE_FX
#define V4_MENU 1                        // R4V4 item 4: the menu on the OLED, driven by the two knobs
#endif
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

#ifndef V4_MENU
#define V4_MENU 0
#endif

// Chromatic button accordion layouts. Along a row each key is a minor
// third (+3) above the previous one. On the eTuttino rows 1 and 3 have 11 keys starting at
// column 1 (A3 .. D#6, G#3 .. D6); row 2 has 12 starting at column 0, half
// a key further left (G3 .. E6); row 4 sits on row 2's columns, half a key
// left of row 3, and runs A3 .. C6 (10 keys, column 1 on).
// B-griff is the mirror image of C-griff: rows 1 and 3 swap places, so a
// diagonal step goes the other way. Keep in sync with etutti/etuttino/script.js.
#if ETUTTI_V4
// R5V4: row 4 sits on row 2's columns, one semitone below row 2 in each (F#3 under G3); it is row 1's
// pitch class one column to the left. B-griff swaps rows 1 and 3 and row 4 follows row 1 (F3).
const int8_t FIRST_NOTE[2][LAYOUT_ROWS] = {
  {57, 55, 56, 54},   // C-griff: A3, G3, G#3, F#3
  {56, 55, 57, 53},   // B-griff: G#3, G3, A3, F3
};
#else
const int8_t FIRST_NOTE[2][LAYOUT_ROWS] = {
  {57, 55, 56, 57},   // C-griff: A3, G3, G#3, A3
  {56, 55, 57, 56},   // B-griff: G#3, G3, A3, G#3
};
#endif
#if ETUTTI_V4
const uint8_t FIRST_COL[LAYOUT_ROWS] = {0, 0, 0, 0};   // R3V4 (PINOS.md): each strip starts at the row's first key; the empty spots are at the END of the row
#else
const uint8_t FIRST_COL[LAYOUT_ROWS] = {1, 0, 1, 1};
#endif
int layoutSystem = 0;   // 0 = C-griff, 1 = B-griff

#if ETUTTI_V4
// Module note map (R1V4 4.4): the keyboard grows to the right in modules of 16
// keys (4 columns = one octave). By default the 1st extra module adds treble
// and the 2nd bass, and so on (R5V4, full strips, rows 2's range): 32 = G3-E5, 48 = G3-E6, 64 = G2-E6, 80 = G2-E7
// (the lowest key of the 4th row is a semitone lower: F#3 / F#2).
// Adding bass shifts every key down an octave, so the notes at the left grow lower.
// The user's own map is a TODO (it would be a CC and a place in EEPROM).
const int V4_EXTRA_MODULES = (V4_KEYS - 32) / 16;
const int V4_BASS_MODULES = V4_EXTRA_MODULES / 2;
int noteShift = -12 * V4_BASS_MODULES;   // semitones

// Where the keys are (R5V4): the strips are always full, so every column of every row has a key
// (32 = 8 + 8 + 8 + 8; each module adds 4 to every row).
inline bool v4HasKey(int r, int c) { return r >= 0 && c >= 0; }
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
const int MAX_KEYS = 80;
#else
const int MAX_KEYS = 44;
#endif
const float ADC_PER_VOLT = 4095.0f / 3.3f;
#if ETUTTI_STUDENT
const float SENSOR_ZERO = 1.65f * ADC_PER_VOLT;  // TMAG5253 output at 0 mT
const float SIGN_MIN = 0.04f * ADC_PER_VOLT;     // rest must be this far from 1.65 V to tell the direction
const int DEFAULT_SIGN = 1;                      // direction assumed when it cannot be told (unverified: no board yet)
#if ETUTTI_V4
const uint32_t EEPROM_MAGIC = 0xE7770107;        // V4 (R5V4: full strips, 32..80 keys): key order = row by row from row 1
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
  uint32_t hotUntil;        // V4: the key counts as rising until this time (micros), see HOT_HOLD_US
};
Key keyState[MAX_KEYS];
volatile bool scanPaused = false;   // V4 scan interrupt: set while loop() uses ADC1 or rewrites the keys' calibration
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
bool keyIsHot(const Key &k, uint32_t now);

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
#if V4_VOICE_FX
// Voice effects (R3V4 item 6, R4V4 item 4, voice_fx.h): mic -> VoiceInput (high-pass, gain, expander, notches), then
//   vin -> vocoder voice input; the keyboard (toneFilter) is its carrier,
//   vin -> three pitch shifters (AudioEffectGranular), fixed interval or following the keys' notes,
//   vin -> pitch tracker (YIN), vin -> FFT (feedback suppressor),
//   vin + shifted -> echo,
//   vin, shifted, echo -> voiceBus -> master (and into the reverb together with the keys).
const int VOICE_HARM_SAMPLES = 12800;           // grain memory of one pitch shifter (library example size)
const int VOICE_HARM_N = 3;                     // pitch shifters: one per note the harmonizer follows (R4V4)
const int VOICE_ECHO_SAMPLES = 32768;           // 743 ms
DMAMEM int16_t harmMem[VOICE_HARM_N][VOICE_HARM_SAMPLES];
DMAMEM int16_t echoMem[VOICE_ECHO_SAMPLES];
vfx::VoiceInput          vin;
AudioEffectGranular      harm[VOICE_HARM_N];
AudioMixer4              harmMix;               // the shifters together (interval mode: only the first one)
vfx::PitchTracker        pitchTrk;              // YIN on the voice, for the harmonizer that follows the keys
vfx::VoiceEcho           echo;
vfx::VocoderFx           voc;
AudioMixer4              echoSrc;               // vin, shifted voice
AudioMixer4              voiceBus;              // vin, shifted voice, echo
AudioMixer4              roomIn;                // keys, voiceBus, vocoder: what the reverb hears
AudioConnection          pvi(i2sIn, 0, vin, 0);
AudioConnection          pvh0(vin, 0, harm[0], 0);
AudioConnection          pvh1(vin, 0, harm[1], 0);
AudioConnection          pvh2(vin, 0, harm[2], 0);
AudioConnection          phm0(harm[0], 0, harmMix, 0);
AudioConnection          phm1(harm[1], 0, harmMix, 1);
AudioConnection          phm2(harm[2], 0, harmMix, 2);
AudioConnection          ppt(vin, 0, pitchTrk, 0);
AudioConnection          pes0(vin, 0, echoSrc, 0);
AudioConnection          pes1(harmMix, 0, echoSrc, 1);
AudioConnection          pec(echoSrc, 0, echo, 0);
AudioConnection          pvb0(vin, 0, voiceBus, 0);
AudioConnection          pvb1(harmMix, 0, voiceBus, 1);
AudioConnection          pvb2(echo, 0, voiceBus, 2);
AudioConnection          pvo0(vin, 0, voc, 0);
AudioConnection          pvo1(toneFilter, 0, voc, 1);
AudioConnection          prm0(toneFilter, 0, roomIn, 0);
AudioConnection          prm1(voiceBus, 0, roomIn, 1);
AudioConnection          prm2(voc, 0, roomIn, 2);
AudioConnection          pmv(voiceBus, 0, master, 2);
#if V4_FEEDBACK_SUPPRESSOR
// Automatic feedback suppressor (R4V4): a 1024-point FFT of the conditioned voice, watched in loop()
// (vfx::FeedbackWatch); it is only connected while the menu option is on.
AudioAnalyzeFFT1024      fftIn;
AudioConnection          pfft(vin, 0, fftIn, 0);
#endif
AudioConnection          pmo(voc, 0, master, 3);
#endif
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
#if ETUTTI_V4 && V4_VOICE_FX
AudioConnection pv(roomIn, 0, room, 0);
#else
AudioConnection pv(toneFilter, 0, room, 0);
#endif
AudioConnection pw(room, 0, master, 1);       // reverb
AudioConnection po(master, 0, outAmp, 0);
AudioConnection pl(outAmp, 0, i2sOut, 0);
AudioConnection pr(outAmp, 0, i2sOut, 1);
#if ETUTTI_V4 && V4_SPEAKER_EQ
// R5V4: the speaker's equalizer sits between the volume and the I2S. The MAX98357A and the codec share the
// I2S stream, so "speaker only" = "no headphones plugged" (the amplifier is on only then): with a plug in, the
// equalizer is disconnected (pl/pr direct) and costs nothing; without, pl/pr are cut and the signal goes through it.
AudioFilterBiquad spkEq;
AudioConnection pq0(outAmp, 0, spkEq, 0);
AudioConnection pq1(spkEq, 0, i2sOut, 0);
AudioConnection pq2(spkEq, 0, i2sOut, 1);
bool spkEqRouted = false;    // false: pl/pr (direct) carry the sound; pq0..pq2 are created connected and cut on the first apply
#endif

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

#if ETUTTI_V4 && V4_VOICE_FX
float keysLevel = 1.0f;                 // the keyboard's share of the mix (CC 83)
#endif
void setAmbience(byte value) {
  float wet = value / 127.0f;
#if ETUTTI_V4 && V4_VOICE_FX
  master.gain(0, (1.0f - 0.35f * wet) * keysLevel);
#else
  master.gain(0, 1.0f - 0.35f * wet);
#endif
  master.gain(1, 0.6f * wet);
}
byte ambienceNow = 25;

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

#if ETUTTI_V4 && V4_VOICE_FX
// ---- Voice effects: controls (R3V4 item 6, R4V4 item 4) ----
// Everything starts off (all the levels 0): the microphone is not even read until one is raised.
//   CC 16 voice (dry)        0..127   CC 76 echo level   CC 80 voice into the reverb
//   CC 17 vocoder level      0..127   CC 77 echo time    60..740 ms
//   CC 18 pitch shifter level         CC 78 echo feedback 0..0.85
//   CC 19 pitch shift         -12..+12 semitones (64 = none)   CC 81 gate threshold
//   CC 82 microphone gain (codec)     CC 83 keyboard level (0 = voice only)
// R4V4:
//   CC 84 gate attack 0.5..30 ms      CC 92 high-pass 60..400 Hz (default 90)
//   CC 89 gate hold 0..500 ms         CC 93 expander ratio, value / 32 = 0 soft .. 3 hard gate
//   CC 90 gate release 20..1000 ms    CC 94 automatic feedback notches (>= 64 on)
//   CC 95 harmonizer follows the keys (>= 64; otherwise the fixed interval of CC 19)
//   CC 96 voice also on the SPEAKER (>= 64; off at every start; the screen warns about feedback)
//   CC 97 followed notes folded to the voice's own octave (>= 64, the default) or exact
// R5V4 (speaker equalizer, only with no headphones plugged):
//   CC 105 on / off (>= 64, default on)  CC 106 high-pass corner 150..450 Hz (63 = 300)  CC 107 dip at 1 kHz 0..-12 dB (63 = -6)
// The menu on the OLED (two knobs) drives the same state and sends the CCs back, so a page can follow.
// The numbers are in the sketch only for now: the page (script.js) has no V4 model yet, and the
// CC map has to change in both together.
extern bool headphones;                 // defined with the other jack state, further down
uint8_t keysCC = 127;                   // CC 83, as sent (the menu shows it)
uint32_t speakerWarnAt = 0;             // millis() when the voice was sent to the speaker (the screen warns), 0 = nothing pending
struct VoiceFx {
  uint8_t voice = 0, vocoder = 0, harm = 0, interval = 64, echo = 0, echoTime = 40, echoFb = 40;
  uint8_t reverb = 40, gate = 20, micGain = 60;
  uint8_t gateAtk = 30, gateHold = 45, gateRel = 45, gateRatio = 2, hpf = 11;
  bool antiFb = false, harmFollow = false, harmFold = true, speaker = false;
  bool eq = true;                       // R5V4 speaker equalizer: on by default (it does nothing with headphones)
  uint8_t eqCut = 63, eqDip = 63;       // CC 106: 150..450 Hz (63 = ~300); CC 107: 0..-12 dB at 1 kHz (63 = -6)
} vfxState;

inline float vfxCurve(uint8_t v) { float x = v / 127.0f; return x * sqrtf(x); }   // x^1.5: finer near zero
inline float gateThr(uint8_t v) { return 40.0f + v * v * 0.5f; }                  // 40 .. ~8100 (int16 units)
inline float gateAtkMs(uint8_t v) { return 0.5f + v * v * (29.5f / 16129.0f); }
inline float gateHoldMs(uint8_t v) { return v * v * (500.0f / 16129.0f); }
inline float gateRelMs(uint8_t v) { return 20.0f + v * v * (980.0f / 16129.0f); }
inline float hpfHz(uint8_t v) { return 60.0f + v * (340.0f / 127.0f); }

// Voice goes to the headphone / AUX jack by default: with no jack plugged the voice is muted
// (the speaker is the output), unless the user switched the speaker on.
inline bool speakerMutesVoice() { return !headphones && !vfxState.speaker; }

inline float eqCutHz(uint8_t v) { return 150.0f + v * (300.0f / 127.0f); }
inline float eqDipDb(uint8_t v) { return v * (12.0f / 127.0f); }

#if V4_SPEAKER_EQ
// Study-speaker equalizer: the 28 mm driver in a 10 cm3 box has nothing useful below ~300 Hz and a peak near 1 kHz
// (estudos/acustica.py); the full sound is for the headphones / AUX. Stages: 2 x high-pass (4th order Butterworth,
// Q 0.5412 and 1.3066), 1 x peaking cut at 1 kHz (Q 1.2, RBJ cookbook), 1 x pass-through.
void spkEqPeaking(int stage, float f0, float q, float dbGain) {
  double A = pow(10.0, dbGain / 40.0), w0 = 2.0 * 3.14159265358979 * f0 / AUDIO_SAMPLE_RATE_EXACT;
  double alpha = sin(w0) / (2.0 * q), c = cos(w0), a0 = 1.0 + alpha / A;
  double co[5] = {(1.0 + alpha * A) / a0, -2.0 * c / a0, (1.0 - alpha * A) / a0, -2.0 * c / a0, (1.0 - alpha / A) / a0};
  spkEq.setCoefficients(stage, co);
}
void speakerEqApply() {
  VoiceFx &f = vfxState;
  bool want = f.eq && !headphones;                    // equalizer only on the speaker's path
  static bool first = true;
  if (first) { first = false; pq0.disconnect(); pq1.disconnect(); pq2.disconnect(); }   // created connected: start direct
  if (want) {
    float fc = eqCutHz(f.eqCut);
    spkEq.setHighpass(0, fc, 0.5412f);
    spkEq.setHighpass(1, fc, 1.3066f);
    spkEqPeaking(2, 1000.0f, 1.2f, -eqDipDb(f.eqDip));
    static const double thru[5] = {1, 0, 0, 0, 0};
    spkEq.setCoefficients(3, thru);
  }
  if (want != spkEqRouted) {
    if (want) { pl.disconnect(); pr.disconnect(); pq0.connect(); pq1.connect(); pq2.connect(); }
    else { pq0.disconnect(); pq1.disconnect(); pq2.disconnect(); pl.connect(); pr.connect(); }
    spkEqRouted = want;
  }
}
#endif

static bool shifterOn[VOICE_HARM_N] = {false, false, false};
#if V4_FEEDBACK_SUPPRESSOR
vfx::FeedbackWatch fbWatch;
bool fbConnected = true;                // pfft starts connected
#endif

void voiceFxApply() {
  VoiceFx &f = vfxState;
#if V4_SPEAKER_EQ
  speakerEqApply();
#endif
  bool duck = speakerMutesVoice();
  float live = duck ? 0.0f : 1.0f;
  bool any = f.voice || f.vocoder || f.harm || f.echo;
  bool vinOn = any && !duck;
  vin.setActive(vinOn);
  vin.setGain(1.0f);
  vin.setHighpass(hpfHz(f.hpf));
  vin.setExpander(gateThr(f.gate), f.gateRatio, gateAtkMs(f.gateAtk), gateHoldMs(f.gateHold), gateRelMs(f.gateRel));
  voc.setActive(f.vocoder > 0 && !duck);
  voc.setLevel(vfxCurve(f.vocoder) * 1.5f);
  bool harmOn = f.harm > 0 && vinOn;
  for (int k = 0; k < VOICE_HARM_N; k++) {
    bool want = harmOn && (k == 0 || f.harmFollow);
    if (want && !shifterOn[k]) {
      harm[k].begin(harmMem[k], VOICE_HARM_SAMPLES);
      harm[k].beginPitchShift(25.0f);
      shifterOn[k] = true;
    } else if (!want && shifterOn[k]) {
      harm[k].stop();
      shifterOn[k] = false;
    }
  }
  if (!f.harmFollow) {
    harm[0].setSpeed(powf(2.0f, ((int)f.interval - 64) / 64.0f));    // -12 .. +12 semitones
    harmMix.gain(0, 1.0f);
    harmMix.gain(1, 0.0f);
    harmMix.gain(2, 0.0f);
  } else {                                                           // harmFollowUpdate() sets these
    for (int k = 0; k < VOICE_HARM_N; k++) harmMix.gain(k, 0.0f);
  }
  harmMix.gain(3, 0.0f);
  pitchTrk.setActive(harmOn && f.harmFollow);
  echo.setDelayMs(60.0f + f.echoTime * (680.0f / 127.0f));
  echo.setFeedback(f.echoFb * (0.85f / 127.0f));
  echoSrc.gain(0, 1.0f);
  echoSrc.gain(1, f.harm > 0 ? 1.0f : 0.0f);                       // the shifter passes the voice through when it is off
  voiceBus.gain(0, vfxCurve(f.voice) * 1.5f * live);
  voiceBus.gain(1, vfxCurve(f.harm) * 1.5f * live);
  voiceBus.gain(2, vfxCurve(f.echo) * 1.5f * live);
  roomIn.gain(0, 1.0f);
  roomIn.gain(1, vfxCurve(f.reverb));
  roomIn.gain(2, vfxCurve(f.reverb));
  master.gain(2, 1.0f);
  master.gain(3, 1.0f);
#if V4_FEEDBACK_SUPPRESSOR
  bool wantFb = f.antiFb && vinOn;
  if (wantFb && !fbConnected) { pfft.connect(); fbConnected = true; }
  else if (!wantFb && fbConnected) { pfft.disconnect(); fbConnected = false; }
  static bool wasFb = false;
  if (f.antiFb != wasFb) {                                           // switched off: the notches go
    wasFb = f.antiFb;
    if (!f.antiFb) {
      fbWatch.clear();
      for (int i = 0; i < vfx::VoiceInput::NOTCHES; i++) vin.clearNotch(i);
    }
  }
#endif
}

void voiceFxMicGain() { codec.micGain(20 + (vfxState.micGain * 32) / 127); }   // 20 .. 52 dB (I2C: only when it changes)

bool voiceFxControl(byte control, byte value) {
  VoiceFx &f = vfxState;
  switch (control) {
    case 16: f.voice = value; break;
    case 17: f.vocoder = value; break;
    case 18: f.harm = value; break;
    case 19: f.interval = value; break;
    case 76: f.echo = value; break;
    case 77: f.echoTime = value; break;
    case 78: f.echoFb = value; break;
    case 80: f.reverb = value; break;
    case 81: f.gate = value; break;
    case 82: f.micGain = value; voiceFxMicGain(); break;
    case 84: f.gateAtk = value; break;
    case 89: f.gateHold = value; break;
    case 90: f.gateRel = value; break;
    case 92: f.hpf = value; break;
    case 93: f.gateRatio = min(value / 32, 3); break;
    case 94: f.antiFb = value >= 64; break;
    case 95: f.harmFollow = value >= 64; break;
    case 96:
      if (value >= 64 && !f.speaker) speakerWarnAt = millis() | 1;
      f.speaker = value >= 64;
      break;
    case 97: f.harmFold = value >= 64; break;
    case 105: f.eq = value >= 64; break;                       // R5V4 speaker equalizer on / off
    case 106: f.eqCut = value; break;                          // 150..450 Hz
    case 107: f.eqDip = value; break;                          // 0..-12 dB at 1 kHz
    case 83:
      keysCC = value;
      keysLevel = value / 127.0f;
      setAmbience(ambienceNow);
      return true;
    default: return false;
  }
  voiceFxApply();
  return true;
}

// "Close microphone" preset: only a voice a few centimetres from the capsule passes.
void voiceFxCloseMic() {
  VoiceFx &f = vfxState;
  f.gate = 90; f.gateRatio = 3; f.gateAtk = 20; f.gateHold = 50; f.gateRel = 40; f.hpf = 40;
  voiceFxApply();
}

void voiceFxClearNotches() {
#if V4_FEEDBACK_SUPPRESSOR
  fbWatch.clear();
  for (int i = 0; i < vfx::VoiceInput::NOTCHES; i++) vin.clearNotch(i);
#endif
}

// ---- settings kept in EEPROM (menu "SAVE"). The speaker option is never kept: the voice is on
// the headphones / AUX at every start. ----
const int EEPROM_VOICE = 210;           // after the register (200..201)
const uint8_t VOICE_MAGIC = 0xA7, EQ_MAGIC = 0xE5;
void voiceFxSave() {
  VoiceFx &f = vfxState;
  uint8_t b[26] = {VOICE_MAGIC, f.voice, f.vocoder, f.harm, f.interval, f.echo, f.echoTime, f.echoFb, f.reverb, f.gate,
                   f.micGain, f.gateAtk, f.gateHold, f.gateRel, f.gateRatio, f.hpf, (uint8_t)f.antiFb,
                   (uint8_t)f.harmFollow, (uint8_t)f.harmFold, keysCC, 0, 0,
                   EQ_MAGIC, (uint8_t)f.eq, f.eqCut, f.eqDip};          // R5V4: the equalizer, after its own marker
  for (int i = 0; i < 26; i++) EEPROM.write(EEPROM_VOICE + i, b[i]);
}

void voiceFxLoad() {
  if (EEPROM.read(EEPROM_VOICE) != VOICE_MAGIC) return;
  uint8_t b[26];
  for (int i = 0; i < 26; i++) b[i] = EEPROM.read(EEPROM_VOICE + i);
  VoiceFx &f = vfxState;
  f.voice = min(b[1], (uint8_t)127); f.vocoder = min(b[2], (uint8_t)127); f.harm = min(b[3], (uint8_t)127);
  f.interval = min(b[4], (uint8_t)127); f.echo = min(b[5], (uint8_t)127); f.echoTime = min(b[6], (uint8_t)127);
  f.echoFb = min(b[7], (uint8_t)127); f.reverb = min(b[8], (uint8_t)127); f.gate = min(b[9], (uint8_t)127);
  f.micGain = min(b[10], (uint8_t)127); f.gateAtk = min(b[11], (uint8_t)127); f.gateHold = min(b[12], (uint8_t)127);
  f.gateRel = min(b[13], (uint8_t)127); f.gateRatio = min(b[14], (uint8_t)3); f.hpf = min(b[15], (uint8_t)127);
  f.antiFb = b[16] != 0; f.harmFollow = b[17] != 0; f.harmFold = b[18] != 0;
  keysCC = min(b[19], (uint8_t)127);
  keysLevel = keysCC / 127.0f;
  if (b[22] == EQ_MAGIC) { f.eq = b[23] != 0; f.eqCut = min(b[24], (uint8_t)127); f.eqDip = min(b[25], (uint8_t)127); }
}

void voiceFxDefaults() {
  vfxState = VoiceFx();
  keysCC = 127;
  keysLevel = 1.0f;
  setAmbience(ambienceNow);
  voiceFxApply();
  voiceFxMicGain();
}

// ---- harmonizer that follows the keys (R4V4) ----
// The voice's pitch comes from the YIN tracker (pitchTrk); every 12 ms each note held on the
// keyboard (newest first, up to VOICE_HARM_N of them) gets a pitch shifter whose speed is
// note frequency / voice frequency. With "octave near" (the default) the ratio is folded into
// 0.71 .. 1.41, i.e. the note is taken in the octave closest to the voice: small shifts, far
// fewer artefacts. The ratio follows the singer smoothly (about 25 ms), so a little of the vibrato
// stays. Nothing held, or the voice unpitched for 300 ms: the harmony is silent.
static int harmNote[VOICE_HARM_N] = {-1, -1, -1};
static float harmRatio[VOICE_HARM_N] = {1, 1, 1};
float voiceHzShown = 0;                 // last pitch the tracker found (for the screen)

void harmFollowUpdate() {
  VoiceFx &f = vfxState;
  static uint32_t lastAt = 0, seenAt = 0;
  static float lastF0 = 0;
  uint32_t now = millis();
  if (now - lastAt < 12) return;
  lastAt = now;
  if (!f.harmFollow || f.harm == 0 || speakerMutesVoice()) return;
  float f0 = pitchTrk.pitch();
  if (f0 > 0) { seenAt = now; lastF0 = f0; voiceHzShown = f0; }
  bool voiced = seenAt != 0 && now - seenAt < 300 && lastF0 > 0;
  int notes[VOICE_HARM_N];
  int n = 0;
  for (int k = 0; k < VOICE_HARM_N; k++) {                           // newest notes first, no repeats
    int best = -1;
    for (int v = 0; v < NUM_VOICES; v++) {
      if (voices[v].note < 0) continue;
      bool dup = false;
      for (int j = 0; j < n; j++) dup |= notes[j] == voices[v].note;
      if (!dup && (best < 0 || voices[v].age > voices[best].age)) best = v;
    }
    if (best < 0) break;
    notes[n++] = voices[best].note;
  }
  float share = n > 0 ? 1.0f / sqrtf((float)n) : 0.0f;
  for (int k = 0; k < VOICE_HARM_N; k++) {
    if (k < n && voiced) {
      float target = 440.0f * powf(2.0f, (notes[k] - 69) / 12.0f) / lastF0;
      if (f.harmFold) {
        while (target > 1.4142f) target *= 0.5f;
        while (target < 0.7071f) target *= 2.0f;
      } else {
        target = constrain(target, 0.25f, 4.0f);
      }
      if (harmNote[k] != notes[k]) harmRatio[k] = target;
      else harmRatio[k] += (target - harmRatio[k]) * 0.4f;
      harmNote[k] = notes[k];
      AudioNoInterrupts();
      harm[k].setSpeed(harmRatio[k]);
      AudioInterrupts();
      harmMix.gain(k, share);
    } else {
      harmMix.gain(k, 0.0f);
      harmNote[k] = -1;
    }
  }
}

#if V4_FEEDBACK_SUPPRESSOR
void feedbackUpdate() {
  if (!vfxState.antiFb || !fbConnected || !fftIn.available()) return;
  float mag[512];
  for (int i = 0; i < 512; i++) mag[i] = fftIn.read(i);
  int idx = fbWatch.feed(mag);
  if (idx >= 0) vin.setNotch(idx, fbWatch.freq[idx], fbWatch.depth[idx]);
}
#endif

// Called from loop().
void voiceFxUpdate() {
  harmFollowUpdate();
#if V4_FEEDBACK_SUPPRESSOR
  feedbackUpdate();
#endif
}

void voiceFxBegin() {
  echo.begin(echoMem, VOICE_ECHO_SAMPLES);
  for (int k = 0; k < VOICE_HARM_N; k++) {
    harm[k].begin(harmMem[k], VOICE_HARM_SAMPLES);
    harm[k].stop();
  }
#if V4_FEEDBACK_SUPPRESSOR
  pfft.disconnect();                    // switched on in the menu
  fbConnected = false;
#endif
  voc.setSpeed(4.0f, 25.0f);
  voiceFxLoad();
  voiceFxApply();
  voiceFxMicGain();
}
#endif

void handleControlChange(byte channel, byte control, byte value) {
#if ETUTTI_V4 && V4_VOICE_FX
  if (voiceFxControl(control, value)) return;
#endif
  switch (control) {
    case 7:
      setVolume(value);
      break;
    case 9:
      velocityCurve = min(value / 32, 3);
      break;
    case 14:
      if (value >= 64) {
#if ETUTTI_V4 && V4_SCAN_TIMER
        scanPaused = true;                          // the scan interrupt reads the models resetCalibration() rewrites
#endif
        resetCalibration();
#if ETUTTI_V4 && V4_SCAN_TIMER
        scanPaused = false;
#endif
      }
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
      ambienceNow = value;
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
uint32_t srOnAt = 0;                    // micros() when it was switched on (the sensors need SENSOR_WAKE_US)
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
// pulse to latch it: SR_STAGES + 1 pulses, ~10 us with 80 keys.
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
  srOnAt = micros();
}

#if V4_ADC_DUAL
ADC *adcLib = new ADC();                // Teensyduino's ADC library: ADC1 = adc0, ADC2 = adc1

void setupAdc() {
  // 12 bits, no averaging. Fast conversion, medium sampling time: the sensors' OUT is a driven,
  // low-impedance output (1.27 ohm), unlike the battery divider (see analogReadSlow).
  for (int a = 0; a < 2; a++) {
    ADC_Module *m = a == 0 ? adcLib->adc0 : adcLib->adc1;
    m->setResolution(12);
    m->setAveraging(1);
    m->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
    m->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED);
  }
}

// For the high-impedance pins (battery divider 2 x 100 kohm, headphone detect): the slowest
// sampling time, as Teensyduino's own analogRead() uses.
int analogReadSlow(uint8_t pin) {
  scanPaused = true;                    // the scan interrupt uses ADC1 too: it waits (a few tens of us)
  adcLib->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::VERY_LOW_SPEED);
  int v = adcLib->adc0->analogRead(pin);
  adcLib->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED);
  scanPaused = false;
  return v;
}
#endif

// Reads the sensors of the selected column (after the wake-up), one per row, with
// the time of each reading. Rows with no key there are skipped.
// Rows 1 and 2 (pins 14, 15) are read on ADC1 and rows 3 and 4 (26, 27: ADC2 only) on ADC2, at
// the same time: two pairs, about 2 x 3 us instead of 4 x 5.6 us one after the other.
void readColumn(int c, uint16_t *raw, uint32_t *at) {
#if V4_ADC_DUAL
  for (int p = 0; p < 2; p++) {
    int ia = colKey[c][p], ib = colKey[c][p + 2];
    if (ia != 255) adcLib->adc0->startSingleRead(ROW_OUT_PINS[p]);
    if (ib != 255) adcLib->adc1->startSingleRead(ROW_OUT_PINS[p + 2]);
    if (ia != 255) {
      while (!adcLib->adc0->isComplete()) {
      }
      uint16_t v = adcLib->adc0->readSingle();
      at[p] = micros();
      raw[p] = keyState[ia].sign < 0 ? 4095 - v : v;      // falling readings mirrored about mid-scale
    }
    if (ib != 255) {
      while (!adcLib->adc1->isComplete()) {
      }
      uint16_t v = adcLib->adc1->readSingle();
      at[p + 2] = micros();
      raw[p + 2] = keyState[ib].sign < 0 ? 4095 - v : v;
    }
  }
#else
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    uint8_t i = colKey[c][r];
    if (i == 255) continue;
    uint16_t v = analogRead(ROW_OUT_PINS[r]);
    at[r] = micros();
    raw[r] = keyState[i].sign < 0 ? 4095 - v : v;   // falling readings mirrored about mid-scale
  }
#endif
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
#if ETUTTI_V4 && V4_ADC_DUAL
  setupAdc();
#endif
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

#if ETUTTI_V4 && V4_SCAN_TIMER
// Key events from the scan interrupt to loop() (single producer, single consumer, no locks).
// type 0 = note on (a = note, b = velocity), 1 = note off (a = note), 2 = key-test position (a = key, b = position)
const uint16_t EVQ = 128;
volatile uint8_t evType[EVQ], evA[EVQ], evB[EVQ];
volatile uint16_t evHead = 0, evTail = 0;
void evPush(uint8_t type, uint8_t a, uint8_t b) {
  uint16_t h = evHead;
  if ((uint16_t)(h - evTail) >= EVQ) return;            // full: loop() is stuck (never seen), drop
  evType[h & (EVQ - 1)] = type;
  evA[h & (EVQ - 1)] = a;
  evB[h & (EVQ - 1)] = b;
  __asm volatile("dmb" ::: "memory");
  evHead = h + 1;
}
inline void keyNoteOn(uint8_t note, uint8_t velocity) { evPush(0, note, velocity); }
inline void keyNoteOff(uint8_t note) { evPush(1, note, 0); }
inline void keyPressure(uint8_t key, uint8_t pos) { evPush(2, key, pos); }
#else
inline void keyNoteOn(uint8_t note, uint8_t velocity) { localNoteOn(note, velocity); }
inline void keyNoteOff(uint8_t note) { localNoteOff(note); }
inline void keyPressure(uint8_t key, uint8_t pos) { usbMIDI.sendPolyPressure(key, pos, 16); }
#endif

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
    if (fabsf(k.rest - k.restAtModel) > 0.5f) updateModel(k);   // 80 keys: do not take cube roots every pass
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
#if ETUTTI_V4
  if (k.rising) k.hotUntil = now + HOT_HOLD_US;
#endif
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
      if (k.note >= 0) keyNoteOn(k.note, velocityFor((at - k.startMicros) / 1000.0f));
      changed = true;
    }
  } else if (t < NOTE_OFF_AT) {
    k.down = false;
    k.startMicros = 0;
    if (k.note >= 0) keyNoteOff(k.note);    // the note it started, even after a layout switch
    k.note = -1;
    changed = true;
  }
  k.travel = t;
  k.prevMicros = now;
  if (keyTest) {
    uint8_t pos = (uint8_t)roundf(t * 127.0f);
    if (pos != k.sentPosition && (abs((int)pos - (int)k.sentPosition) >= 2 || pos == 0 || pos == 127)) {
      keyPressure(i, pos);
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
uint32_t colReadAt[LAYOUT_COLS];   // micros() of each column's last reading
uint32_t hotCols = 0;              // bit c: column c holds a key that wants fast readings

// A key that is on its way up, between HOT_FROM and the note-on level, and still moving or slow
// enough to matter: its velocity is being timed, so it is read as often as possible.
bool keyIsHot(const Key &k, uint32_t now) {
  if (!k.present || k.down || k.travel < HOT_FROM || k.travel >= NOTE_ON_AT) return false;
  if ((int32_t)(k.hotUntil - now) <= 0) return false;
  if (k.startMicros && now - k.startMicros > HOT_WINDOW_US) return false;
  return true;
}

// Handles the readings of one column (4 keys at most) and updates its "hot" bit.
bool processColumn(int c, const uint16_t *raw, const uint32_t *at) {
  bool changed = false;
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    if (colKey[c][r] != 255) changed |= processKey(colKey[c][r], raw[r], at[r]);
  }
  uint32_t now = micros();
  bool hot = false;
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    if (colKey[c][r] != 255) hot |= keyIsHot(keyState[colKey[c][r]], now);
  }
  if (hot) hotCols |= 1UL << c;
  else hotCols &= ~(1UL << c);
  return changed;
}

// Switches column c on if it is not, and waits until its sensors have woken up.
inline void wakeColumn(int c) {
  if (srPos != c) srSelect(c);
  int32_t left = (int32_t)SENSOR_WAKE_US - (int32_t)(micros() - srOnAt);
  if (left > 0) delayMicroseconds(left);
}

#if !V4_SCAN_TIMER
// Hot reads, in turns: while some column has a key being timed, the one read longest ago is
// read next (round robin), for at most `budget` us. A column that is still on from the last
// turn needs no new wake-up, only HOT_MIN_GAP_US between readings.
bool hotBurst(uint32_t budget) {
  uint16_t raw[LAYOUT_ROWS];
  uint32_t at[LAYOUT_ROWS];
  bool changed = false;
  uint32_t start = micros();
  while (hotCols && micros() - start < budget) {
    uint32_t now = micros();
    int best = -1;
    uint32_t bestAge = 0;
    for (uint32_t m = hotCols; m; m &= m - 1) {
      int c = __builtin_ctz(m);
      uint32_t age = now - colReadAt[c];
      if (best < 0 || age > bestAge) {
        best = c;
        bestAge = age;
      }
    }
    wakeColumn(best);
    while (micros() - colReadAt[best] < HOT_MIN_GAP_US) {
    }
    readColumn(best, raw, at);
    colReadAt[best] = micros();
    changed |= processColumn(best, raw, at);
  }
  return changed;
}

// One pass over all the keys, a column at a time. While the next column's sensors wake up
// (SENSOR_WAKE_US) the previous column's readings are processed, so the wake-up costs no extra
// time for the arithmetic. Whenever a key starts to move up, the hot reads (round robin over
// the moving keys' columns) run at once, up to the pass's hot budget.
void scanKeys() {
  uint16_t raw[LAYOUT_ROWS];
  uint32_t at[LAYOUT_ROWS];
  bool changed = false;
  float u = constrain(AudioProcessorUsage() * 0.01f, 0.0f, 0.8f);   // share of the time the audio interrupts take
  int32_t room = (int32_t)MAX_KEY_GAP_US - (int32_t)(PASS_NOMINAL_US / (1.0f - u));
  uint32_t hotLeft = room > (int32_t)HOT_BUDGET_MIN_US ? (uint32_t)room : HOT_BUDGET_MIN_US;
  for (int c = 0; c < LAYOUT_COLS; c++) {
    wakeColumn(c);
    readColumn(c, raw, at);
    colReadAt[c] = micros();
    if (c + 1 < LAYOUT_COLS) srSelect(c + 1);
    changed |= processColumn(c, raw, at);
    if (hotCols && hotLeft) {
      uint32_t t0 = micros();
      changed |= hotBurst(hotLeft);
      uint32_t used = micros() - t0;
      hotLeft = used >= hotLeft ? 0 : hotLeft - used;
    }
  }
  keysBusy = false;
  for (int i = 0; i < keyCount; i++) keysBusy |= keyState[i].down || keyState[i].travel > 0.02f;
  finishScan(changed);
}
#else   // V4_SCAN_TIMER
// ---- Student V4 scan in a timer interrupt (R4V4) ----
// The scan used to be loop() itself, so everything else in loop() (MIDI, knobs, screen, voice
// control) and every audio interrupt delayed it. Now an IntervalTimer calls scanTick() every
// SCAN_TICK_US at a priority ABOVE the audio's (and USB's, and the DMA's): the audio can
// not stretch a pass, and loop() is free of the busy waiting (it only drains the event queue).
// scanTick() never waits: it reads the column whose sensors have been awake for SENSOR_WAKE_US,
// switches the next one on, processes the readings, and returns. Key events (note on / off
// with velocity, key-test positions) go into a queue, because the voices and usbMIDI belong to
// loop(). The hot reads (see HOT_FROM) work as before, round robin among the columns with a rising key.
IntervalTimer scanTimer;
volatile uint32_t lastPassUs = 0;       // the last full pass, for the bench
uint32_t scanPassStart = 0, scanLastRead = 0, scanHotLeft = 0;
int scanSeqNext = 0;                    // the next column of the ordinary pass
bool scanCurSeq = true;                 // the column now switched on is an ordinary read (not a hot repeat)

inline uint32_t scanHotBudget() {
  int32_t room = (int32_t)MAX_KEY_GAP_US - (int32_t)PASS_NOMINAL_US;
  return room > (int32_t)HOT_BUDGET_MIN_US ? (uint32_t)room : HOT_BUDGET_MIN_US;
}

int scanOldestHot(uint32_t now) {
  int best = -1;
  uint32_t bestAge = 0;
  for (uint32_t m = hotCols; m; m &= m - 1) {
    int c = __builtin_ctz(m);
    uint32_t age = now - colReadAt[c];
    if (best < 0 || age > bestAge) {
      best = c;
      bestAge = age;
    }
  }
  return best;
}

void scanTick() {
  if (scanPaused) return;
  if (srPos < 0) {                                      // nothing switched on yet
    scanSeqNext = 0;
    scanCurSeq = true;
    srSelect(0);
    return;
  }
  uint32_t now = micros();
  int c = srPos;
  if (now - srOnAt < SENSOR_WAKE_US) return;            // still waking up
  if (now - colReadAt[c] < HOT_MIN_GAP_US) return;      // a hot repeat of the same column: not too soon
  uint16_t raw[LAYOUT_ROWS];
  uint32_t at[LAYOUT_ROWS];
  readColumn(c, raw, at);
  uint32_t t = micros();
  colReadAt[c] = t;
  if (scanCurSeq) {
    scanSeqNext = c + 1;
    if (scanSeqNext >= LAYOUT_COLS) {                   // a pass is complete
      scanSeqNext = 0;
      lastPassUs = t - scanPassStart;
      scanPassStart = t;
      scanHotLeft = scanHotBudget();
      bool busy = false;
      for (int i = 0; i < keyCount; i++) busy |= keyState[i].down || keyState[i].travel > 0.02f;
      keysBusy = busy;
    }
  } else {
    uint32_t used = t - scanLastRead;
    scanHotLeft = used >= scanHotLeft ? 0 : scanHotLeft - used;
  }
  scanLastRead = t;
  if (!hotCols) srSelect(scanSeqNext);                  // the next column wakes up while this one is processed
  processColumn(c, raw, at);
  int want;
  bool seq;
  if (hotCols && scanHotLeft >= HOT_MIN_GAP_US) {
    want = scanOldestHot(micros());
    seq = false;
  } else {
    want = scanSeqNext;
    seq = true;
  }
  if (want != srPos) srSelect(want);
  scanCurSeq = seq;
}

void scanBegin() {
  scanPassStart = scanLastRead = micros();
  scanHotLeft = scanHotBudget();
  scanSeqNext = 0;
  scanCurSeq = true;
  srSelect(0);
  scanTimer.begin(scanTick, SCAN_TICK_US);
  scanTimer.priority(SCAN_PRIORITY);
}

void scanEnd() {
  scanTimer.end();
}

// loop(): hands the queued key events to the voices and to USB, saves the calibration once it
// has settled, flushes the MIDI messages.
void drainKeyEvents() {
  bool any = false;
  while (evTail != evHead) {
    uint16_t i = evTail & (EVQ - 1);
    uint8_t type = evType[i], a = evA[i], b = evB[i];
    __asm volatile("dmb" ::: "memory");
    evTail = evTail + 1;
    if (type == 0) localNoteOn(a, b);
    else if (type == 1) localNoteOff(a);
    else usbMIDI.sendPolyPressure(a, b, 16);
    any = true;
  }
  if (calibrationDirty && millis() - calibrationChangedAt > 5000) saveCalibration();
  if (any) {
    usbMIDI.send_now();
    lastActivityAt = millis();
  }
}
#endif
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
#if V4_SCAN_TIMER
  scanEnd();
#endif
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
  batteryVolts = analogReadSlow(VBAT_PIN) * 2.0f / ADC_PER_VOLT;
  volDown = digitalReadFast(VOL_SW_PIN) == LOW;
}

#if V4_MENU
// R4V4 item 4: the menu on the OLED, driven by the two knobs (menu code: with the OLED, below).
//   selector, long click (0.7 s)   opens / closes the menu
//   selector turn                  moves the cursor
//   selector click                 enters a submenu, flips an on/off or a choice, runs an action
//   volume turn                    changes the value of the line the cursor is on
//   volume click                   back (closes the menu from the first level)
//   volume click held 2 s          still switches the instrument off, menu or not
// Outside the menu nothing changes, except that the selector's short click (keep the register /
// back to the default sound) now acts when the button is let go, to tell it from the long click.
bool menuOpen = false;
uint32_t menuLastInput = 0;
uint32_t oledWarnUntil = 0;             // the speaker warning is on the screen until then
const uint32_t MENU_LONG_MS = 700;
const uint32_t MENU_IDLE_MS = 30000;    // the menu closes by itself
bool selLongFired = false;
uint32_t selPressAt = 0, volPressAt = 0;
void menuToggle();
void menuTurn(int d);
void menuAdjust(int d);
void menuClick();
void menuBack();
#endif

void updateControls() {
  uint32_t now = millis();
  // volume knob
  noInterrupts();
  int turned = volSteps / ENC_STEPS_PER_DETENT;
  volSteps -= turned * ENC_STEPS_PER_DETENT;
  interrupts();
  if (turned) {
#if V4_MENU
    oledWarnUntil = 0;
    menuLastInput = now;
    if (menuOpen) menuAdjust(turned);
    else
#endif
    {
      setVolume(volumeNow + turned * VOLUME_PER_DETENT);
      usbMIDI.sendControlChange(7, volumeNow, 1);
    }
    lastActivityAt = now;
  }
  // volume click: held 2 s = off; in the menu a short click is "back"
  bool down = digitalReadFast(VOL_SW_PIN) == LOW;
  if (down != volDown && now - volChangedAt > 20) {
    volDown = down;
    volChangedAt = now;
#if V4_MENU
    if (down) volPressAt = now;
    if (!down && !volIgnoreHold) {
      oledWarnUntil = 0;
      menuLastInput = now;
      if (menuOpen) menuBack();
    }
#endif
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
#if V4_MENU
    oledWarnUntil = 0;
    menuLastInput = now;
    if (menuOpen) menuTurn(detents);
    else
#endif
    {
      applyRegister(registerIndex + detents, true);
      instrumentPending = true;
    }
    lastActivityAt = now;
  }
  down = digitalReadFast(ENC_SW_PIN) == LOW;
  if (down != selDown && now - selChangedAt > 20) {
    selDown = down;
    selChangedAt = now;
    lastActivityAt = now;
#if V4_MENU
    if (down) {
      selPressAt = now;
      selLongFired = false;
    } else if (!selLongFired) {                         // short click, on release
      oledWarnUntil = 0;
      menuLastInput = now;
      if (menuOpen) menuClick();
      else if (instrumentPending) {
        saveRegister(registerIndex);                    // the one to start with next time
        instrumentPending = false;
      } else {
        defaultSound();
        registerIndex = DEFAULT_REGISTER;
        saveRegister(DEFAULT_REGISTER);
        usbMIDI.sendControlChange(26, registerMask, 1);
      }
    }
#else
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
#endif
  }
#if V4_MENU
  if (selDown && !selLongFired && now - selPressAt >= MENU_LONG_MS) {   // long click: the menu
    selLongFired = true;
    oledWarnUntil = 0;
    menuLastInput = now;
    menuToggle();
  }
  if (menuOpen && now - menuLastInput > MENU_IDLE_MS) menuToggle();
#endif
}

// Battery, headphone socket and the rest / switch-off timers.
void updatePower() {
  uint32_t now = millis();
  bool usb = usbPower();
  if (now - batteryReadAt >= 500) {
    batteryReadAt = now;
    batteryVolts += (analogReadSlow(VBAT_PIN) * 2.0f / ADC_PER_VOLT - batteryVolts) * 0.1f;
    if (usb || batteryVolts >= BATTERY_EMPTY_V) batteryEmptySince = 0;
    else if (batteryEmptySince == 0) batteryEmptySince = now | 1;
    else if (now - batteryEmptySince > 10000) powerOff();
  }
  if (now - jackReadAt >= 50) {
    jackReadAt = now;
    float volts = analogReadSlow(HP_DET_PIN) / ADC_PER_VOLT;
    if (volts < 0.5f) headphones = true;
    else if (volts > 0.9f) headphones = false;
  }
#if ETUTTI_V4 && V4_VOICE_FX
  static bool lastHeadphones = headphones;
  if (lastHeadphones != headphones) {       // the voice follows the jack: headphones / AUX in, speaker out (R4V4)
    lastHeadphones = headphones;
    voiceFxApply();
  }
#endif
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

// Text with a colour: on = false draws black on a white bar (the highlighted menu line).
void oledTextOn(int x, int y, const char *str, int scale, bool on) {
  for (; *str; str++) {
    int ch = *str;
    if (ch >= 'a' && ch <= 'z') ch -= 32;
    if (ch < 32 || ch > 90) ch = '?';
    for (int col = 0; col < 5; col++) {
      uint8_t bits = FONT5X7[ch - 32][col];
      for (int row = 0; row < 7; row++) {
        if (bits & (1 << row)) oledRect(x + col * scale, y + row * scale, scale, scale, on);
      }
    }
    x += 6 * scale;
  }
}

void oledTextRight(int xRight, int y, const char *str, bool on) {
  oledTextOn(xRight - 6 * (int)strlen(str), y, str, 1, on);
}

// The text of the menu and the warning is in Portuguese (MENU_LANG_PT 1) or English (0); the font has no accents.
#define MENU_LANG_PT 1
#define TXT(pt, en) (MENU_LANG_PT ? (pt) : (en))
#if V4_MENU
// ---- Student V4 menu (R4V4 item 4): drawn on the OLED, driven by the two knobs ----
enum { PG_MAIN, PG_VOICE, PG_INPUT, PG_OUTPUT, PG_SOUND, PG_SYSTEM, PG_COUNT };
enum { MK_SUB, MK_LEVEL, MK_ENUM, MK_ACTION };
enum {
  M_VOICE_DRY, M_VOCODER, M_HARM, M_HARM_MODE, M_HARM_INT, M_HARM_FOLD, M_ECHO, M_ECHO_TIME, M_ECHO_FB, M_VOICE_REV,
  M_MIC_GAIN, M_GATE_THR, M_GATE_RATIO, M_GATE_ATK, M_GATE_HOLD, M_GATE_REL, M_HPF, M_CLOSE_MIC, M_ANTI_FB, M_CLEAR_NOTCH,
  M_VOLUME, M_VOICE_OUT, M_KEYS_LEVEL, M_SPK_EQ, M_EQ_CUT, M_EQ_DIP,
  M_REGISTER, M_INSTRUMENT, M_AMBIENCE, M_VEL_CURVE,
  M_SAVE, M_RESET_VOICE, M_CAL_KEYS, M_KEY_TEST
};
struct MenuItem { const char *pt; const char *en; uint8_t kind; uint8_t id; };   // SUB: id = the page
struct MenuPage { const char *pt; const char *en; const MenuItem *items; uint8_t count; };

const MenuItem ITEMS_MAIN[] = {
  {"VOZ", "VOICE", MK_SUB, PG_VOICE}, {"CAPTACAO", "INPUT", MK_SUB, PG_INPUT}, {"SAIDA", "OUTPUT", MK_SUB, PG_OUTPUT},
  {"SOM", "SOUND", MK_SUB, PG_SOUND}, {"SISTEMA", "SYSTEM", MK_SUB, PG_SYSTEM}};
const MenuItem ITEMS_VOICE[] = {
  {"VOZ SECA", "DRY VOICE", MK_LEVEL, M_VOICE_DRY}, {"VOCODER", "VOCODER", MK_LEVEL, M_VOCODER},
  {"HARMONIZ.", "HARMONIZER", MK_LEVEL, M_HARM}, {"MODO HARM", "HARM MODE", MK_ENUM, M_HARM_MODE},
  {"INTERVALO", "INTERVAL", MK_LEVEL, M_HARM_INT}, {"OITAVA", "OCTAVE", MK_ENUM, M_HARM_FOLD},
  {"ECO", "ECHO", MK_LEVEL, M_ECHO}, {"TEMPO ECO", "ECHO TIME", MK_LEVEL, M_ECHO_TIME},
  {"REALIM ECO", "ECHO FDBK", MK_LEVEL, M_ECHO_FB}, {"REVERB VOZ", "VOICE REV", MK_LEVEL, M_VOICE_REV}};
const MenuItem ITEMS_INPUT[] = {
  {"GANHO MIC", "MIC GAIN", MK_LEVEL, M_MIC_GAIN}, {"LIMIAR", "THRESHOLD", MK_LEVEL, M_GATE_THR},
  {"RAZAO", "RATIO", MK_ENUM, M_GATE_RATIO}, {"ATAQUE", "ATTACK", MK_LEVEL, M_GATE_ATK},
  {"RETENCAO", "HOLD", MK_LEVEL, M_GATE_HOLD}, {"SOLTURA", "RELEASE", MK_LEVEL, M_GATE_REL},
  {"PASSA-ALTAS", "HIGH-PASS", MK_LEVEL, M_HPF}, {"MIC PERTO", "CLOSE MIC", MK_ACTION, M_CLOSE_MIC},
  {"ANTIMICROF.", "ANTI-FEEDBK", MK_ENUM, M_ANTI_FB}, {"LIMPAR NOTCH", "CLEAR NOTCH", MK_ACTION, M_CLEAR_NOTCH}};
const MenuItem ITEMS_OUTPUT[] = {
  {"VOLUME", "VOLUME", MK_LEVEL, M_VOLUME}, {"SAIDA VOZ", "VOICE OUT", MK_ENUM, M_VOICE_OUT},
  {"TECLAS", "KEYS", MK_LEVEL, M_KEYS_LEVEL}, {"EQ ALTOF.", "SPK EQ", MK_ENUM, M_SPK_EQ},
  {"CORTE", "CUTOFF", MK_LEVEL, M_EQ_CUT}, {"PICO 1K", "1K DIP", MK_LEVEL, M_EQ_DIP}};
const MenuItem ITEMS_SOUND[] = {
  {"REGISTRO", "REGISTER", MK_ENUM, M_REGISTER}, {"INSTRUMENTO", "INSTRUMENT", MK_ENUM, M_INSTRUMENT},
  {"REVERB", "REVERB", MK_LEVEL, M_AMBIENCE}, {"CURVA VEL.", "VEL CURVE", MK_ENUM, M_VEL_CURVE}};
const MenuItem ITEMS_SYSTEM[] = {
  {"SALVAR", "SAVE", MK_ACTION, M_SAVE}, {"ZERAR VOZ", "RESET VOICE", MK_ACTION, M_RESET_VOICE},
  {"CALIBRAR", "CALIBRATE", MK_ACTION, M_CAL_KEYS}, {"TESTE TECLAS", "KEY TEST", MK_ENUM, M_KEY_TEST}};
#define PAGE_OF(name, pt, en, arr) {pt, en, arr, (uint8_t)(sizeof(arr) / sizeof(arr[0]))}
const MenuPage MENU_PAGES[PG_COUNT] = {
  PAGE_OF(main, "MENU", "MENU", ITEMS_MAIN), PAGE_OF(voice, "VOZ", "VOICE", ITEMS_VOICE),
  PAGE_OF(input, "CAPTACAO", "INPUT", ITEMS_INPUT), PAGE_OF(output, "SAIDA", "OUTPUT", ITEMS_OUTPUT),
  PAGE_OF(sound, "SOM", "SOUND", ITEMS_SOUND), PAGE_OF(system, "SISTEMA", "SYSTEM", ITEMS_SYSTEM)};

uint8_t menuPage = PG_MAIN;
int menuCursor = 0, menuScroll = 0;
uint8_t menuDepth = 0;
struct MenuFrame { uint8_t page; int cursor, scroll; } menuStack[3];
const char *menuToast = nullptr;
uint32_t menuToastAt = 0;

const char *const RATIO_NAMES_PT[4] = {"SUAVE", "MEDIA", "FORTE", "PORTA"};
const char *const RATIO_NAMES_EN[4] = {"SOFT", "MEDIUM", "HARD", "GATE"};
const char *const CURVE_NAMES_PT[4] = {"FIXA", "SUAVE", "NORMAL", "DURA"};
const char *const CURVE_NAMES_EN[4] = {"FIXED", "SOFT", "NORMAL", "HARD"};

// The CC and the current value of a level line (volume: copied, it is an int).
bool menuLevelRef(uint8_t id, uint8_t *&p, uint8_t &cc) {
  static uint8_t tmp;
  VoiceFx &f = vfxState;
  switch (id) {
    case M_VOICE_DRY: p = &f.voice; cc = 16; return true;
    case M_VOCODER: p = &f.vocoder; cc = 17; return true;
    case M_HARM: p = &f.harm; cc = 18; return true;
    case M_HARM_INT: p = &f.interval; cc = 19; return true;
    case M_ECHO: p = &f.echo; cc = 76; return true;
    case M_ECHO_TIME: p = &f.echoTime; cc = 77; return true;
    case M_ECHO_FB: p = &f.echoFb; cc = 78; return true;
    case M_VOICE_REV: p = &f.reverb; cc = 80; return true;
    case M_MIC_GAIN: p = &f.micGain; cc = 82; return true;
    case M_GATE_THR: p = &f.gate; cc = 81; return true;
    case M_GATE_ATK: p = &f.gateAtk; cc = 84; return true;
    case M_GATE_HOLD: p = &f.gateHold; cc = 89; return true;
    case M_GATE_REL: p = &f.gateRel; cc = 90; return true;
    case M_HPF: p = &f.hpf; cc = 92; return true;
    case M_KEYS_LEVEL: p = &keysCC; cc = 83; return true;
    case M_EQ_CUT: p = &f.eqCut; cc = 106; return true;
    case M_EQ_DIP: p = &f.eqDip; cc = 107; return true;
    case M_AMBIENCE: p = &ambienceNow; cc = 91; return true;
    case M_VOLUME: tmp = (uint8_t)volumeNow; p = &tmp; cc = 7; return true;
  }
  return false;
}

// The text of a line's value (at most 9 characters).
void menuValueText(uint8_t id, char *b, size_t n) {
  VoiceFx &f = vfxState;
  uint8_t *p;
  uint8_t cc;
  b[0] = 0;
  switch (id) {
    case M_HARM_INT: { int st = lroundf(((int)f.interval - 64) * 12.0f / 64.0f); snprintf(b, n, "%+d ST", st); return; }
    case M_ECHO_TIME: snprintf(b, n, "%d MS", (int)lroundf(60.0f + f.echoTime * (680.0f / 127.0f))); return;
    case M_MIC_GAIN: snprintf(b, n, "%d DB", 20 + (f.micGain * 32) / 127); return;
    case M_GATE_ATK: snprintf(b, n, "%.1f MS", gateAtkMs(f.gateAtk)); return;
    case M_GATE_HOLD: snprintf(b, n, "%d MS", (int)gateHoldMs(f.gateHold)); return;
    case M_GATE_REL: snprintf(b, n, "%d MS", (int)gateRelMs(f.gateRel)); return;
    case M_HPF: snprintf(b, n, "%d HZ", (int)hpfHz(f.hpf)); return;
    case M_EQ_CUT: snprintf(b, n, "%d HZ", (int)lroundf(eqCutHz(f.eqCut))); return;
    case M_EQ_DIP: snprintf(b, n, "-%d DB", (int)lroundf(eqDipDb(f.eqDip))); return;
    case M_SPK_EQ: snprintf(b, n, "%s", f.eq ? TXT("LIGADO", "ON") : TXT("DESLIG", "OFF")); return;
    case M_HARM_MODE: snprintf(b, n, "%s", f.harmFollow ? TXT("TECLA", "KEY") : TXT("FIXO", "FIXED")); return;
    case M_HARM_FOLD: snprintf(b, n, "%s", f.harmFold ? TXT("PERTO", "NEAR") : TXT("EXATA", "EXACT")); return;
    case M_GATE_RATIO: snprintf(b, n, "%s", (MENU_LANG_PT ? RATIO_NAMES_PT : RATIO_NAMES_EN)[f.gateRatio]); return;
    case M_ANTI_FB: snprintf(b, n, "%s", f.antiFb ? TXT("LIGADO", "ON") : TXT("DESLIG", "OFF")); return;
    case M_VOICE_OUT: snprintf(b, n, "%s", f.speaker ? TXT("+ ALTOFAL", "+ SPEAKER") : TXT("FONE/AUX", "PHONES")); return;
    case M_REGISTER: snprintf(b, n, "%s", REGISTER_NAMES[registerIndex]); return;
    case M_INSTRUMENT: snprintf(b, n, "%s", INSTRUMENT_NAMES[instrument]); return;
    case M_VEL_CURVE: snprintf(b, n, "%s", (MENU_LANG_PT ? CURVE_NAMES_PT : CURVE_NAMES_EN)[velocityCurve]); return;
    case M_KEY_TEST: snprintf(b, n, "%s", keyTest ? TXT("LIGADO", "ON") : TXT("DESLIG", "OFF")); return;
  }
  if (menuLevelRef(id, p, cc)) snprintf(b, n, "%d%%", (*p * 100 + 63) / 127);
}

void menuToggle() {
  if (menuOpen) {
    menuOpen = false;
  } else {
    menuOpen = true;
    menuPage = PG_MAIN;
    menuCursor = menuScroll = 0;
    menuDepth = 0;
  }
  menuToast = nullptr;
}

void menuTurn(int d) {
  int count = MENU_PAGES[menuPage].count;
  menuCursor = ((menuCursor + d) % count + count) % count;
  if (menuCursor < menuScroll) menuScroll = menuCursor;
  if (menuCursor > menuScroll + 4) menuScroll = menuCursor - 4;
}

void menuBack() {
  if (menuDepth == 0) {
    menuToggle();
    return;
  }
  MenuFrame &fr = menuStack[--menuDepth];
  menuPage = fr.page;
  menuCursor = fr.cursor;
  menuScroll = fr.scroll;
}

void menuSetCC(uint8_t cc, uint8_t value) {
  handleControlChange(1, cc, value);                    // the same path as a CC from the page
  usbMIDI.sendControlChange(cc, value, 1);              // and the page can follow the menu
}

// Volume knob: the value of the line under the cursor, one step per detent.
void menuAdjust(int d) {
  const MenuItem &it = MENU_PAGES[menuPage].items[menuCursor];
  VoiceFx &f = vfxState;
  uint8_t *p;
  uint8_t cc;
  if (it.kind == MK_LEVEL && menuLevelRef(it.id, p, cc)) {
    int v = *p;
    if (it.id == M_HARM_INT) {                          // whole semitones
      int st = lroundf((v - 64) * 12.0f / 64.0f) + d;
      v = 64 + (int)lroundf(constrain(st, -12, 12) * 64.0f / 12.0f);
    } else {
      v += d * 4;
    }
    menuSetCC(cc, (uint8_t)constrain(v, 0, 127));
    return;
  }
  switch (it.id) {
    case M_HARM_MODE: menuSetCC(95, f.harmFollow ? 0 : 127); break;
    case M_HARM_FOLD: menuSetCC(97, f.harmFold ? 0 : 127); break;
    case M_GATE_RATIO: menuSetCC(93, (uint8_t)(constrain((int)f.gateRatio + d, 0, 3) * 32)); break;
    case M_ANTI_FB: menuSetCC(94, f.antiFb ? 0 : 127); break;
    case M_VOICE_OUT: menuSetCC(96, f.speaker ? 0 : 127); break;
    case M_SPK_EQ: menuSetCC(105, f.eq ? 0 : 127); break;
    case M_REGISTER: applyRegister(registerIndex + d, true); instrumentPending = false; break;
    case M_INSTRUMENT: {
      int next = ((instrument + d) % 5 + 5) % 5;
      setInstrument(next);
      usbMIDI.sendControlChange(25, next * 16 + 8, 1);
      instrumentPending = false;
      break;
    }
    case M_VEL_CURVE: menuSetCC(9, (uint8_t)((((velocityCurve + d) % 4 + 4) % 4) * 32)); break;
    case M_KEY_TEST: menuSetCC(15, keyTest ? 0 : 127); break;
  }
}

// Selector click.
void menuClick() {
  const MenuItem &it = MENU_PAGES[menuPage].items[menuCursor];
  switch (it.kind) {
    case MK_SUB:
      if (menuDepth < 3) {
        menuStack[menuDepth++] = {menuPage, menuCursor, menuScroll};
        menuPage = it.id;
        menuCursor = menuScroll = 0;
      }
      break;
    case MK_ENUM: menuAdjust(1); break;
    case MK_ACTION:
      switch (it.id) {
        case M_CLOSE_MIC: voiceFxCloseMic(); menuToast = TXT("MIC PERTO", "CLOSE MIC"); break;
        case M_CLEAR_NOTCH: voiceFxClearNotches(); menuToast = TXT("NOTCH LIMPOS", "NOTCH CLEARED"); break;
        case M_SAVE: voiceFxSave(); saveRegister(registerIndex); menuToast = TXT("SALVO", "SAVED"); break;
        case M_RESET_VOICE: voiceFxDefaults(); menuToast = TXT("VOZ ZERADA", "VOICE RESET"); break;
        case M_CAL_KEYS: handleControlChange(1, 14, 127); menuToast = TXT("CALIBRADO", "CALIBRATED"); break;
      }
      menuToastAt = millis();
      break;
  }
}

void drawMenu() {
  const MenuPage &pg = MENU_PAGES[menuPage];
  oledRect(0, 0, 128, 10, true);                        // title bar
  char line[24];
  if (menuToast && millis() - menuToastAt < 1500) {
    oledTextOn(2, 1, menuToast, 1, false);
  } else {
    snprintf(line, sizeof(line), "%s%s", menuPage == PG_MAIN ? "" : "MENU > ", MENU_LANG_PT ? pg.pt : pg.en);
    oledTextOn(2, 1, line, 1, false);
  }
  snprintf(line, sizeof(line), "%d/%d", menuCursor + 1, pg.count);
  oledTextRight(126, 1, line, false);
  for (int r = 0; r < 5; r++) {
    int idx = menuScroll + r;
    if (idx >= pg.count) break;
    const MenuItem &it = pg.items[idx];
    int y = 12 + r * 10;
    bool sel = idx == menuCursor;
    if (sel) oledRect(0, y - 1, 128, 10, true);
    oledTextOn(2, y, MENU_LANG_PT ? it.pt : it.en, 1, !sel);
    if (it.kind == MK_SUB) {
      oledTextRight(126, y, ">", !sel);
    } else if (it.kind == MK_LEVEL) {
      uint8_t *p;
      uint8_t cc;
      if (menuLevelRef(it.id, p, cc)) {
        int fill = *p * 26 / 127;                       // bar, 28 px wide
        bool on = !sel;
        oledRect(70, y + 1, 28, 1, on); oledRect(70, y + 6, 28, 1, on);
        oledRect(70, y + 1, 1, 6, on); oledRect(97, y + 1, 1, 6, on);
        oledRect(71, y + 3, fill, 2, on);
      }
      menuValueText(it.id, line, sizeof(line));
      oledTextRight(126, y, line, !sel);
    } else if (it.kind == MK_ENUM) {
      menuValueText(it.id, line, sizeof(line));
      oledTextRight(126, y, line, !sel);
    }
  }
}
#endif

// The speaker warning: the voice is going to the speaker, next to the microphone.
#if V4_VOICE_FX
void drawWarning(uint32_t now) {
  bool blink = (now / 350) % 2 == 0;
  if (blink) { oledRect(0, 0, 128, 64, true); oledRect(2, 2, 124, 60, false); }
  else { oledRect(0, 0, 128, 1, true); oledRect(0, 63, 128, 1, true); }
  oledTextOn(34, 6, TXT("AVISO", "WARNING"), 2, true);
  oledTextOn(8, 26, TXT("VOZ NO ALTO-FALANTE", "VOICE ON SPEAKER"), 1, true);
  oledTextOn(8, 36, TXT("PODE DAR MICROFONIA", "MAY CAUSE FEEDBACK"), 1, true);
  oledTextOn(8, 46, TXT("MIC PERTO DA BOCA E", "MIC AT THE MOUTH"), 1, true);
  oledTextOn(8, 54, TXT("VOLUME BAIXO", "VOLUME LOW"), 1, true);
}
#endif

// The ordinary screen: battery, register, volume, output, microphone level.
void drawStatus(uint32_t now) {
  bool usb = usbPower();
  bool charging = usb && digitalReadFast(CHG_STAT_PIN) == LOW;
  int pct = batteryPercent(batteryVolts);
  int mic = 0;
#if V4_HAVE_MIC
  if (micPeak.available()) mic = (int)(micPeak.read() * 8.0f);   // 0..8
#endif
  char line[24];
  snprintf(line, sizeof(line), "%s %d%%", charging ? "CHG" : (usb ? "USB" : "BAT"), pct);
  oledTextOn(0, 0, line, 2, true);
  oledTextOn(0, 20, instrument == INST_ACCORDION ? REGISTER_NAMES[registerIndex] : INSTRUMENT_NAMES[instrument], 2, true);
  // voice status, right of the volume line
  char vs[16] = "";
#if V4_VOICE_FX
  VoiceFx &f = vfxState;
  if (f.voice || f.vocoder || f.harm || f.echo) {
    if (speakerMutesVoice()) snprintf(vs, sizeof(vs), "%s", TXT("VOZ MUDA", "VOICE OFF"));
    else if (!headphones && (now / 400) % 2 == 0) snprintf(vs, sizeof(vs), "%s", TXT("!MICROFONIA", "!FEEDBACK"));
    else if (!headphones) vs[0] = 0;
    else if (f.harmFollow && f.harm > 0 && voiceHzShown > 0) {
      static const char *const names[12] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
      int m = (int)lroundf(69.0f + 12.0f * log2f(voiceHzShown / 440.0f));
      snprintf(vs, sizeof(vs), "VOZ %s%d", names[((m % 12) + 12) % 12], m / 12 - 1);
    } else snprintf(vs, sizeof(vs), "%s", vin.isOpen() ? TXT("VOZ *", "VOICE *") : TXT("VOZ", "VOICE"));
  }
#endif
  snprintf(line, sizeof(line), "VOL %d %s%s", volumeNow, headphones ? "HP" : "SPK", (resting && !vs[0]) ? " REST" : "");
  oledTextOn(0, 42, line, 1, true);
  if (vs[0]) oledTextRight(127, 42, vs, true);
  oledRect(0, 54, 82, 1, true);         // battery bar
  oledRect(0, 63, 82, 1, true);
  oledRect(0, 54, 1, 10, true);
  oledRect(81, 54, 1, 10, true);
  oledRect(2, 56, pct * 78 / 100, 6, true);
  oledTextOn(90, 55, "MIC", 1, true);
  oledRect(112, 56, mic * 2, 6, true);
}

// Redraws (the menu and the warning quickly, the status screen 4 times a second) and, when the
// picture changed, sends it in pieces: one 16-byte piece per loop pass.
uint32_t oledHash = 0xFFFFFFFF;
void updateOled() {
  if (!oledPresent) return;
  if (oledSent < 1024) {
#if !V4_SCAN_TIMER
    if (keysBusy) return;               // do not stall the key scan
#endif
    Wire.beginTransmission(OLED_ADDR);
    Wire.write(0x40);
    for (int i = 0; i < 16; i++) Wire.write(oledBuf[oledSent + i]);
    Wire.endTransmission();
    oledSent += 16;
    return;
  }
  uint32_t now = millis();
#if V4_VOICE_FX
  if (speakerWarnAt) {
    oledWarnUntil = now + 4000;
    speakerWarnAt = 0;
  }
#endif
  bool warn = oledWarnUntil && (int32_t)(oledWarnUntil - now) > 0;
  if (!warn) oledWarnUntil = 0;
  bool fast = warn;
#if V4_MENU
  fast |= menuOpen;
#endif
  if (now - oledDrawnAt < (fast ? 70 : 250)) return;
  oledDrawnAt = now;
  memset(oledBuf, 0, sizeof(oledBuf));
#if V4_VOICE_FX
  if (warn) drawWarning(now);
  else
#endif
#if V4_MENU
  if (menuOpen) drawMenu();
  else
#endif
  drawStatus(now);
  uint32_t h = 2166136261u;
  for (int i = 0; i < 1024; i++) h = (h ^ oledBuf[i]) * 16777619u;
  if (h == oledHash) return;
  oledHash = h;
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


#if ETUTTI_V4 && V4_BENCH
#if !defined(USB_MIDI_SERIAL)
#error "V4_BENCH prints on the serial port: build with usb=serialmidi"
#endif
// ---- measuring build: see V4_BENCH ----
struct BenchStep { const char *name; uint8_t reg, voice, vocoder, harm, echo, reverb, follow, antiFb; };
const BenchStep BENCH_STEPS[] = {
  {"MM keys only      ", 0b0110, 0, 0, 0, 0, 0, 0, 0},
  {"+ voice dry       ", 0b0110, 100, 0, 0, 0, 0, 0, 0},
  {"+ vocoder         ", 0b0110, 0, 100, 0, 0, 0, 0, 0},
  {"+ pitch shifter   ", 0b0110, 0, 0, 100, 0, 0, 0, 0},
  {"+ harm follows key", 0b0110, 0, 0, 100, 0, 0, 1, 0},
  {"+ anti-feedback   ", 0b0110, 100, 0, 0, 0, 0, 0, 1},
  {"+ echo            ", 0b0110, 0, 0, 0, 90, 0, 0, 0},
  {"+ reverb send     ", 0b0110, 100, 0, 0, 0, 100, 0, 0},
  {"ALL voice fx      ", 0b0110, 100, 100, 100, 90, 100, 1, 1},
  {"4 ranks keys only ", 0b1111, 0, 0, 0, 0, 0, 0, 0},
  {"4 ranks ALL fx    ", 0b1111, 100, 100, 100, 90, 100, 1, 1},
};
const int BENCH_COUNT = sizeof(BENCH_STEPS) / sizeof(BENCH_STEPS[0]);
const uint32_t BENCH_STEP_MS = 6000;
int benchStep = -1;
uint32_t benchStepAt = 0, benchScanSum = 0, benchScanMax = 0, benchScanN = 0, benchUsageN = 0, benchUsageAt = 0;
float benchUsageSum = 0;

void benchApply(int step) {
  const BenchStep &b = BENCH_STEPS[step];
  registerMask = b.reg;
  applyOscGains();
  handleControlChange(1, 16, b.voice);
  handleControlChange(1, 17, b.vocoder);
  handleControlChange(1, 18, b.harm);
  handleControlChange(1, 19, 64 + 21);                // +4 semitones
  handleControlChange(1, 76, b.echo);
  handleControlChange(1, 77, 60);
  handleControlChange(1, 78, 60);
  handleControlChange(1, 80, b.reverb);
  handleControlChange(1, 81, 0);                      // gate wide open
  handleControlChange(1, 95, b.follow ? 127 : 0);
  handleControlChange(1, 94, b.antiFb ? 127 : 0);
  handleControlChange(1, 96, 127);                    // the bench has no jack: the voice goes to the speaker
}

void benchReport() {
  const BenchStep &b = BENCH_STEPS[benchStep];
  Serial.printf("%s audio CPU avg %5.1f %%  max %5.1f %%  blocks max %2d  key pass avg %5.0f us  max %5lu us  (%lu passes)\n", b.name,
                benchUsageN ? benchUsageSum / benchUsageN : 0.0f, AudioProcessorUsageMax(), AudioMemoryUsageMax(),
                benchScanN ? (float)benchScanSum / benchScanN : 0.0f, (unsigned long)benchScanMax, (unsigned long)benchScanN);
}

void benchUpdate(uint32_t scanUs) {
  uint32_t now = millis();
  if (benchStep < 0 || now - benchStepAt >= BENCH_STEP_MS) {
    if (benchStep >= 0) benchReport();
    benchStep = (benchStep + 1) % BENCH_COUNT;
    if (benchStep == 0) Serial.println("---- V4 bench: 8 notes held, steps of 6 s ----");
    benchStepAt = now;
    benchScanSum = benchScanMax = benchScanN = benchUsageN = 0;
    benchUsageSum = 0;
    benchApply(benchStep);
    AudioProcessorUsageMaxReset();
    AudioMemoryUsageMaxReset();
  }
  if (now - benchStepAt > 1000) {                     // skip the first second of each step
    benchScanSum += scanUs;
    benchScanMax = max(benchScanMax, scanUs);
    benchScanN++;
    if (now - benchUsageAt >= 50) {
      benchUsageAt = now;
      benchUsageSum += AudioProcessorUsage();
      benchUsageN++;
    }
  }
}
#endif

void setup() {
  for (int i = 0; i < 2; i++) pinMode(LED_PINS[i], OUTPUT);
#if ETUTTI_STUDENT
  powerBegin();                                  // stays on only if the click was held 2 s
#endif
  setLed(true, true);                            // orange: reading the keys
  uint32_t started = millis();
#if ETUTTI_V4 && V4_VOICE_FX
  AudioMemory(100);  // + the voice chain, three shifters, tracker and FFT: ~30 more blocks in flight (estimate, see student_v04/FIRMWARE.md)
#else
  AudioMemory(60);   // measured peak: 32 blocks (8 voices x 4 reeds + reverb); 8 with sampled reeds
#endif
  setupKeys();

  codecOk = codec.enable();
#if ETUTTI_STUDENT
  codec.volume(0.7f);                            // fixed: the volume knob works before the I2S output
#endif
#if ETUTTI_V4 && V4_HAVE_MIC
  codec.inputSelect(AUDIO_INPUT_MIC);            // TODO(PINOS): the V4 board's microphone input
  codec.micGain(36);
#if V4_VOICE_FX
  voiceFxBegin();                                // all the voice effects start off
#endif
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
  setAmbience(ambienceNow);

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
#if ETUTTI_V4 && V4_SCAN_TIMER
  scanBegin();                       // from here on the keys are read by the timer interrupt
#endif
#if ETUTTI_V4 && V4_BENCH
  Serial.begin(115200);
  static const uint8_t chord[8] = {48, 52, 55, 60, 64, 67, 72, 76};
  for (int i = 0; i < 8; i++) handleNoteOn(1, chord[i], 100);
#endif
}

void loop() {
  // Drain every pending USB MIDI message; each one calls a handler above.
  while (usbMIDI.read()) {
    lastActivityAt = millis();
  }
#if ETUTTI_V4 && V4_BENCH
  uint32_t scanStart = micros();
#endif
#if ETUTTI_V4 && V4_SCAN_TIMER
  drainKeyEvents();
#else
  scanKeys();
#endif
#if ETUTTI_V4 && V4_BENCH
#if V4_SCAN_TIMER
  benchUpdate(lastPassUs);
#else
  benchUpdate(micros() - scanStart);
#endif
#endif
  updateControls();
#if ETUTTI_V4 && V4_VOICE_FX
  voiceFxUpdate();
#endif
#if ETUTTI_STUDENT
  updatePower();
#endif
#if ETUTTI_V4 && V4_HAVE_OLED
  updateOled();
#endif
  updateLed();
}
