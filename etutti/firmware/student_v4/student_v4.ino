/* ============================================================
   eTutti Student V4 — Teensy MicroMod firmware (SPEC R10V4)
   etutti/hardware/student_v04/FIRMWARE.md is the report; student_v04/pcb/PINOS.md
   is the pin contract. This sketch is the Student V4 only: 32 keys in the modular
   keyboard, nothing of any other instrument.

   Hardware: SparkFun MicroMod Teensy (i.MX RT1062), SGTL5000 codec (headphones,
   microphone IN, speaker amplifier MAX98357A on the same I2S), SSD1306 OLED (J401),
   two encoders with a push switch (volume, selector), LiPo + charger, USB MIDI.
   Keys: one sensor ruler R8 (8 TMAG5253 + one 74HC595, all 8 stages) per row, 4 rows = 32 keys; one "1"
   in the chain switches one column on; 4 analogue OUT lines (14, 15,
   26, 27) are read by both ADCs. The key's travel comes from the cube root of the
   field, its velocity from the time it took to go from 12 % to 45 % travel.

   Build: arduino-cli compile --fqbn teensy:avr:teensyMM:usb=midi,speed=396 etutti/firmware/student_v4
   (Tools > Board: Teensy MicroMod, USB Type: MIDI, CPU speed 396 MHz).

   Sound: accordion, 8 voices, four reeds per note (16', 8' M1, 8' M2, 4') chosen
   by seven registers. With reed_samples.cpp/.h next to the sketch (not in the
   repository: licensed recordings) the reeds are sampled; without them they come
   from additive-synthesis tables (band-limited: no raw saw or square, they alias).
   Then: tone filter (biquad, never the state-variable one), light reverb, the
   voice effects (microphone: expander, vocoder, harmonizer in 3 modes with up to 4
   voices, echo, feedback suppressor; only with a microphone in IN), the speaker
   equaliser, the OLED menu (Portuguese / English).

   MIDI implementation (any channel):
     Note On / Note Off      play / release (velocity -> loudness and brightness)
     CC 7   Volume           also sent back when the volume knob turns
     CC 9   Key velocity     value / 32: 0 fixed (100), 1 soft, 2 normal, 3 hard
     CC 14  Calibrate keys   64-127: forget the learnt key travel, learn it again
     CC 15  Key test         64-127: stream every key's position (Poly AT on ch 16,
                             data 1 = key index row by row from row 1, data 2 = 0..127)
     CC 24  Key layout       0-63 C-griff, 64-127 B-griff
     CC 26  Register         bit mask: 1 = 16', 2 = 8' M1, 4 = 8' M2, 8 = 4' (also sent back)
     CC 27  Reed tuning      M2 detune in cents: 0 = dry ... 30 = very wet
     CC 72  Release  CC 73  Attack  CC 74  Tone  CC 91  Ambience
     CC 120 All sound off    CC 123 All notes off
     Voice effects, speaker equaliser and harmonizer: see "Voice effects: controls" below.
   Knobs: volume turn = volume, click held 2 s = on / off; selector turn = register
   (seven, in order), click after turning = keep it for the next start, click
   otherwise = back to the default sound; selector long click = the menu.
   ============================================================ */
#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include <EEPROM.h>
#include <ADC.h>
#include "reed_sampler.h"
#include "voice_fx.h"
#include "ui_text.h"

// usbMIDI only exists when the USB Type includes MIDI. Without this check
// the compiler only says "'usbMIDI' was not declared in this scope".
#if !defined(MIDI_INTERFACE)
#error "In the Arduino IDE choose Tools > USB Type > MIDI (or Serial + MIDI), then upload again."
#endif
#if !defined(ARDUINO_TEENSY_MICROMOD)
#error "This sketch is for the Teensy MicroMod (Tools > Board > Teensy MicroMod)."
#endif

const int NUM_VOICES = 8;

// ---- Pins (student_v04/pcb/PINOS.md) ----
const uint32_t SENSOR_WAKE_US = 60;                    // TMAG5253BA3 is ready 45 us after its EN rises (max); 60 = margin
const uint8_t LED_PINS[2] = {13, 5};                   // red (also the module's blue LED), green
const uint32_t LED_STARTUP_MS = 600;
// Two encoders with a push switch (to GND, pull-ups here): volume and selector.
const uint8_t VOL_A_PIN = 22, VOL_B_PIN = 24;
const uint8_t VOL_SW_PIN = 4;           // the volume click is also the power switch (R6V4: pin 4; 25 is MIC_DET)
const uint8_t ENC_A_PIN = 11, ENC_B_PIN = 9, ENC_SW_PIN = 6;     // selector
const int ENC_STEPS_PER_DETENT = 2;     // EC11E18244A5: 18 pulses, 36 detents per turn
const uint8_t KEEP_PIN = 10;            // high holds the 3.3 V supply on
const uint8_t AMP_SD_PIN = 12;          // high = speaker amplifier on
const uint8_t VBAT_PIN = 16;            // battery / 2
const uint8_t HP_DET_PIN = 17;          // headphones in: ~0 V; out: ~1.4 V

// ---- Keyboard: modular, rulers R8 (and R4 at the treble end) along each row (SPEC R10V4) ----
// A ruler = sensors at pitch 18.5 mm + one 74HC595 that switches one sensor on at a time: the R8 has 8 sensors
// (all 8 stages QA..QH), the R4 has 4 (QA..QD; QE..QH unused). Rulers are chained along each row; the 4 rows carry the
// same DATA/CLK, so a single "1" walking along the chain switches ONE COLUMN on, i.e. 4 sensors (one per row) at once.
// Each row's sensors share one analogue OUT line (a switched-off TMAG5253 leaves OUT high impedance), 4 lines in all.
// The detailed build is ONE R8 per row = 32 keys, 8 columns, one stage per column. The R4, when there is one, is always
// the LAST ruler of the row (treble end): its unused stages come after the last column, so the "1" never crosses a
// dead stage and the column number is the stage number (48 keys = R8 + R4, 64 = R8 + R8, 80 = R8 + R8 + R4).
// Only these two constants change with the keyboard's size (concept check of the modular system, FIRMWARE.md).
const int RULERS_R8 = 1;                      // per row
const int RULERS_R4 = 0;                      // per row, at the treble end
const int LAYOUT_ROWS = 4;
const int LAYOUT_COLS = 8 * RULERS_R8 + 4 * RULERS_R4;
const int V4_KEYS = LAYOUT_ROWS * LAYOUT_COLS;
static_assert(V4_KEYS == 32, "the detailed Student V4 has 32 keys (4 x R8)");
const uint8_t ROW_OUT_PINS[LAYOUT_ROWS] = {14, 15, 26, 27};   // OUT_R1..R4 (A0, A1, A12, A13); no internal pull: 100 kohm to GND on the board
const uint8_t SR_DATA_PIN = 2, SR_CLK_PIN = 3;                // SCAN_DATA, SCAN_CLK (SRCLK and RCLK of every 595 tied together)
const uint8_t CHG_STAT_PIN = 0;         // low = charging, only with USB power
const int SR_STAGES = 8 * (RULERS_R8 + RULERS_R4);   // every ruler's 595 has 8 stages (an R4 uses only the first 4, at the end of the chain)
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
const uint32_t SCAN_TICK_US = 12;             // scanTick() runs this often (it returns at once until the sensors are awake)
const int SCAN_PRIORITY = 96;                 // NVIC: lower = more urgent. USB 112, DMA 128 (I2S), audio update 208
const uint32_t PASS_NOMINAL_US = (uint32_t)(LAYOUT_COLS * 72);   // one pass with no hot reads: 60 us wake + ~12 us work
// OLED: 128 x 64 SSD1306 on I2C 0x3D or 0x3C (J401, the I2C is shared with the codec). USB runs at 12 Mbit/s
// (startup_late_hook, untested on a board). Microphone: pin 8 = I2S_RX, the codec's MIC input.
// R10V4 item 5: ELECTRET (plug-in power) and DYNAMIC microphones, only through the 3.5 mm jack IN (J302). The voice effects
// (expander, harmonizer, feedback suppressor, vocoder, echo, voice reverb) only work with a microphone detected or declared in
// the menu ("Tipo mic"); without one the voice items leave the menu and the effects are silent.
// Detection (PINOS.md, R6V4): MIC_DET = pin 25 (ADC) reads the DC voltage of the jack's tip (MIC_J) through R306 100 k + C311
// 100 nF, with the codec's MIC_BIAS ON (3.0 V behind its internal 2 k BIAS_RESISTOR; R305 = 0 ohm since R8V4):
//   v >= 2.85 V          nothing plugged, or a line plug (no DC load)                 -> no microphone
//   v <= 0.10 V          short, or a DC-coupled low-impedance source (< ~70 ohm)       -> no microphone
//   0.10 < v < ~0.85 V   a dynamic coil of 70 .. ~600 ohm (3.0 V x Rc / (2 k + Rc): 150 / 300 / 600 ohm = 0.21 / 0.39 / 0.69 V)
//   ~0.95 .. 2.85 V      an electret capsule (0.1 / 0.3 / 0.5 / 1 mA = 2.8 / 2.4 / 2.0 / 1.0 V)
// The two microphone bands touch (a 600-700 ohm coil, the 2 k resistor's tolerance, an electret at >1 mA), so the TYPE is
// not trusted for the bias: "Tipo mic" = Auto (default: bias ALWAYS on, because the detector needs it; the reading only picks the
// factory gain), Eletreto (bias on) or Dinâmico (bias OFF, declared: MIC_DET reads 0 V with the bias off, so nothing is detected
// and the voice stays enabled until the type is changed). A bias left on a 150-600 ohm coil by mistake does no harm: 1.15-1.4 mA,
// ~0.3 mW in the coil, blocked from the codec by C309; it costs 1-2 dB of signal and ~0.1 uV of noise (FIRMWARE.md).
const uint8_t MIC_DET_PIN = 25;          // R6V4: MIC_DET (ADC). VOL_SW moved to pin 4 in the same revision
const float MIC_SHORT_V = 0.10f, MIC_OPEN_V = 2.85f;
const float MIC_DYN_UP_V = 0.85f, MIC_DYN_DOWN_V = 0.95f;   // R10V4 (electronics): below 0.85 V dynamic; once dynamic, back to electret above 0.95 V (hysteresis)
// R11V4: Adafruit 326 (SSD1306 128 x 64): 0x3D from the factory, 0x3C with its address jumper closed (PINOS.md). Tried in this order.
uint8_t OLED_ADDR = 0x3D;
const int OLED_ROTATION = 2;             // as Adafruit_SSD1306::setRotation(2): upside down
// R11V4 item 1: the controller of the real module. 0 = SSD1306 (the usual 0.96" 128 x 64, active area 21.74 x 10.86 mm), 1 = SH1106
// (the 1.3" modules: 132 columns, the glass starts at column 2, no horizontal addressing, so the frame goes page by page). Same 128 x 64
// menu either way. Change this line (or build with -DOLED_SH1106=1) once the module is chosen.
#ifndef OLED_SH1106
#define OLED_SH1106 0
#endif
const int OLED_COL_OFFSET = OLED_SH1106 ? 2 : 0;

// Chromatic button accordion (C-griff). Along a row each key is a minor third (+3) above the previous one.
// B-griff is the mirror image of C-griff: rows 1 and 3 swap places, so a diagonal step goes the other way.
// R5V4: row 4 sits on row 2's columns, one semitone below row 2 in each (F#3 under G3); it is row 1's
// pitch class one column to the left. B-griff swaps rows 1 and 3 and row 4 follows row 1 (F3).
const int8_t FIRST_NOTE[2][LAYOUT_ROWS] = {
  {57, 55, 56, 54},   // C-griff: A3, G3, G#3, F#3
  {56, 55, 57, 53},   // B-griff: G#3, G3, A3, F3
};
const uint8_t FIRST_COL[LAYOUT_ROWS] = {0, 0, 0, 0};   // each ruler starts at the row's first key
int layoutSystem = 0;   // 0 = C-griff, 1 = B-griff

// Modular note map: the keyboard grows to the right by 4 columns (= one octave) per module: an R4 (+4) or the second R8
// (+8 = two modules). The 1st extra module adds treble and the 2nd bass, and so on; adding bass shifts every key down an
// octave. With the detailed 32 keys (one R8, 8 columns) there are no extra modules: F#3-F#5 (25 notes).
const int EXTRA_MODULES = (LAYOUT_COLS - 8) / 4;
const int BASS_MODULES = EXTRA_MODULES / 2;
int noteShift = -12 * BASS_MODULES;   // semitones

// Every column of every ruler carries a key (the rulers are always full).
inline bool keyExists(int r, int c) { return r >= 0 && c >= 0; }

int noteAt(int r, int c) {
  if (c < FIRST_COL[r]) return -1;
  int n = FIRST_NOTE[layoutSystem][r] + 3 * (c - FIRST_COL[r]);
  n += noteShift;
  return n;
}

// ---- Key sensing ----
// The sensor is a TMAG5253BA3: 1.65 V with no field and 15 mV per mT, up or down
// according to the magnet's pole (it reads both). The magnet's field falls off roughly
// as 1/distance^3, so the key's travel is recovered from the cube root of the field
// (above the sensor's 1.65 V zero), scaled between that key's reading at rest and at the
// bottom. The rest reading is measured at start-up and then follows slow drift; the
// bottom is learnt from the deepest press seen and kept in EEPROM. Each key's direction
// is taken from its reading at rest, where the magnet already gives about 10 mT (0.15 V),
// and readings that fall are mirrored about 1.65 V, so everything below sees a voltage
// that rises with the press.
const int MAX_KEYS = LAYOUT_ROWS * LAYOUT_COLS;
const float ADC_PER_VOLT = 4095.0f / 3.3f;
const float SENSOR_ZERO = 1.65f * ADC_PER_VOLT;  // TMAG5253 output at 0 mT
const float SIGN_MIN = 0.04f * ADC_PER_VOLT;     // rest must be this far from 1.65 V to tell the direction
const int DEFAULT_SIGN = 1;                      // direction assumed when it cannot be told (unverified: no board yet)
const uint32_t EEPROM_MAGIC = 0xE7770108;        // bump when the key count/order changes (row by row from row 1)
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
  uint8_t outLine, column;  // the row's OUT line and the column
  int8_t sign;              // +1: the reading rises with the press, -1: it falls
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
  float restAtModel;        // rest when the model was last built (skips needless cube roots)
  bool rising;              // the last reading was higher than the one before
  uint32_t hotUntil;        // the key counts as rising until this time (micros), see HOT_HOLD_US
};
Key keyState[MAX_KEYS];
volatile bool scanPaused = false;   // scan interrupt: set while loop() uses ADC1 or rewrites the keys' calibration
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
uint32_t lastActivityAt = 0;   // last key, knob or MIDI message (rest and switch-off timers)
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
// Common: sum -> tone filter -> dry + reverb -> both channels.
AudioMixer4              engines;             // accA, accB
AudioFilterBiquad        toneFilter;
AudioEffectFreeverb      room;
AudioMixer4              master;              // dry, reverb
AudioAmplifier           outAmp;              // the volume (see setVolume): the speaker amplifier has none of its own
AudioOutputI2S           i2sOut;
// R10V4 item 5: the library's micGain() always writes CHIP_MIC_CTRL with the bias block ON (2 kohm, 3.0 V). The same
// arithmetic here, but the bias can be switched off (BIAS_RESISTOR = 0 powers the block down) for a dynamic microphone.
// CHIP_MIC_CTRL (0x002A): bits 9:8 BIAS_RESISTOR (0 off, 1 = 2 k, 2 = 4 k, 3 = 8 k), 6:4 BIAS_VOLT (1.25 V + 0.25 V x n; 7 = 3.0 V),
// 1:0 GAIN (0 / +20 / +30 / +40 dB); CHIP_ANA_ADC_CTRL (0x0020): ADC gain 0..22.5 dB in 1.5 dB steps, both channels.
class MicCodec : public AudioControlSGTL5000 {
 public:
  bool micSetup(unsigned int dB, bool bias) {
    unsigned int pre = 0;
    if (dB >= 40) { pre = 3; dB -= 40; }
    else if (dB >= 30) { pre = 2; dB -= 30; }
    else if (dB >= 20) { pre = 1; dB -= 20; }
    unsigned int adc = min((dB * 2) / 3, 15u);
    return write(0x002A, (bias ? 0x0170 : 0x0070) | pre) && write(0x0020, (adc << 4) | adc);
  }
};
MicCodec                 codec;
// Microphone through the codec's MIC input (I2S RX, pin 8); here only a level meter for the OLED.
AudioInputI2S            i2sIn;
AudioAnalyzePeak         micPeak;
AudioConnection          pmic(i2sIn, 0, micPeak, 0);
// Voice effects (R3V4 item 6, R4V4 item 4, voice_fx.h): mic -> VoiceInput (high-pass, gain, expander, notches), then
//   vin -> vocoder voice input; the keyboard (toneFilter) is its carrier,
//   vin -> four pitch shifters (AudioEffectGranular; 3 or 4 in use), fixed interval or following the keys' notes,
//   vin -> pitch tracker (YIN), vin -> FFT (feedback suppressor),
//   vin + shifted -> echo,
//   vin, shifted, echo -> voiceBus -> master (and into the reverb together with the keys).
const int VOICE_HARM_SAMPLES = 12800;           // grain memory of one pitch shifter (library example size)
const int VOICE_HARM_N = 4;                     // pitch shifters: one per note the harmonizer follows (R4V4: 3, R6V4: up to 4, 3 or 4 chosen in the menu)
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
AudioConnection          pvh3(vin, 0, harm[3], 0);
AudioConnection          phm0(harm[0], 0, harmMix, 0);
AudioConnection          phm1(harm[1], 0, harmMix, 1);
AudioConnection          phm2(harm[2], 0, harmMix, 2);
AudioConnection          phm3(harm[3], 0, harmMix, 3);
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
// Automatic feedback suppressor (R4V4): a 1024-point FFT of the conditioned voice, watched in loop()
// (vfx::FeedbackWatch); it is only connected while the menu option is on.
AudioAnalyzeFFT1024      fftIn;
AudioConnection          pfft(vin, 0, fftIn, 0);
AudioConnection          pmo(voc, 0, master, 3);

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
AudioConnection pe0(accA, 0, engines, 0);
AudioConnection pe1(accB, 0, engines, 1);
AudioConnection pt(engines, 0, toneFilter, 0);
AudioConnection pd(toneFilter, 0, master, 0);       // dry (low-pass output)
AudioConnection pv(roomIn, 0, room, 0);
AudioConnection pw(room, 0, master, 1);       // reverb
AudioConnection po(master, 0, outAmp, 0);
AudioConnection pl(outAmp, 0, i2sOut, 0);
AudioConnection pr(outAmp, 0, i2sOut, 1);
// R5V4: the speaker's equalizer sits between the volume and the I2S. The MAX98357A and the codec share the
// I2S stream, so "speaker only" = "no headphones plugged" (the amplifier is on only then): with a plug in, the
// equalizer is disconnected (pl/pr direct) and costs nothing; without, pl/pr are cut and the signal goes through it.
AudioFilterBiquad spkEq;
AudioConnection pq0(outAmp, 0, spkEq, 0);
AudioConnection pq1(spkEq, 0, i2sOut, 0);
AudioConnection pq2(spkEq, 0, i2sOut, 1);
bool spkEqRouted = false;    // false: pl/pr (direct) carry the sound; pq0..pq2 are created connected and cut on the first apply

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
  return HAVE_REED_SAMPLES;
}

byte attackCC = 14, releaseCC = 21;

float noteToFreq(float note) {
  return 440.0f * powf(2.0f, (note - 69.0f) / 12.0f);
}

float quadraticMs(byte value, float maxMs) {
  float t = value / 127.0f;
  return t * t * maxMs;
}

void tuneVoice(int v, int note) {
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

// Per-oscillator gains: the register.
void applyOscGains() {
  for (int v = 0; v < NUM_VOICES; v++) {
    for (int r = 0; r < NUM_REEDS; r++) {
      reedMix[v].gain(r, (registerMask & (1 << r)) ? reedGain[r] : 0.0f);
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
    // A reed sounds steadily while held.
    bellows[v].decay(0.0f);
    bellows[v].sustain(1.0f);
  }
}

void configureOscillators() {
  for (int v = 0; v < NUM_VOICES; v++) {
    for (int r = 0; r < NUM_REEDS; r++) reed[r][v].begin(WAVEFORM_ARBITRARY);
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
  return bellows[i].isActive();
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
      bellows[i].noteOff();
      reedSmp[i].noteOff(quadraticMs(releaseCC, 3000));
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
  float amp = accordionLevel(velocity);
  AudioNoInterrupts();
  if (sampledReeds()) {
    reedSmp[v].noteOn(note, wetCents, amp, accordionBrightness(velocity, note));
  } else {
    tuneVoice(v, note);
    for (int r = 0; r < NUM_REEDS; r++) reed[r][v].amplitude(amp);
  }
  bellows[v].noteOn();
  AudioInterrupts();
}

void silenceAll() {
  AudioNoInterrupts();
  for (int i = 0; i < NUM_VOICES; i++) {
    for (int r = 0; r < NUM_REEDS; r++) reed[r][i].amplitude(0);
    reedSmp[i].stop();
    bellows[i].noteOff();
    voices[i].note = -1;
    voices[i].lastNote = -1;
  }
  AudioInterrupts();
}

void releaseAll() {
  for (int i = 0; i < NUM_VOICES; i++) {
    bellows[i].noteOff();
    reedSmp[i].noteOff(quadraticMs(releaseCC, 3000));
    voices[i].note = -1;
  }
}

void setTone(byte value) {
  // 40 Hz .. 20 kHz on an exponential curve, capped at 16 kHz where the
  // biquad is still well-behaved; Q 0.707 = no resonant peak.
  float hz = 40.0f * powf(2.0f, 9.0f * value / 127.0f);
  toneFilter.setLowpass(0, min(hz, 16000.0f), 0.707f);
}

float keysLevel = 1.0f;                 // the keyboard's share of the mix (CC 83)
void setAmbience(byte value) {
  float wet = value / 127.0f;
  master.gain(0, (1.0f - 0.35f * wet) * keysLevel);
  master.gain(1, 0.6f * wet);
}
byte ambienceNow = 25;

// Volume, 0..127: a gain before the I2S output, because the speaker amplifier takes the same
// I2S signal as the codec and has no volume of its own.
int volumeNow = 90;
void setVolume(int v) {
  volumeNow = constrain(v, 0, 127);
  float x = volumeNow / 127.0f;
  outAmp.gain(x * x);
}

void registerChanged();   // keeps the selector in step with a register set over MIDI

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
// R6V4 (harmonizer that follows the keys, 3 modes, 3 or 4 voices):
//   CC 108 follow mode, value / 32: 0 exact, 1 assist, 2 interval (CC 95 still switches "follow" on / off)
//   CC 109 assist strength 0..127 (how far the voice is pulled towards the held note; 127 = exact)
//   CC 110 harmonizer voices: >= 64 four, otherwise three
// The menu on the OLED (two knobs) drives the same state and sends the CCs back, so a page can follow.
// The numbers are in the sketch only for now: the page (script.js) has no V4 model yet, and the
// CC map has to change in both together.
extern bool headphones;                 // defined with the other jack state, further down
extern bool micPlugged;                 // R6V4: a microphone sits in the IN jack (J302) (= micKind != MIC_NONE); defined with the jack state
// R10V4 item 5: electret (plug-in power, 2-5 V) and dynamic microphones, only through the 3.5 mm jack J302.
enum { MIC_NONE, MIC_ELECTRET, MIC_DYNAMIC };            // what the jack holds (micKind)
enum { MICTYPE_AUTO, MICTYPE_ELECTRET, MICTYPE_DYNAMIC }; // the menu "Tipo mic" / CC 111 (value / 43)
uint8_t micKind = MIC_NONE;             // from MIC_DET (auto, electret) or the menu (dynamic: declared, nothing to detect)
uint8_t micType = MICTYPE_AUTO;         // kept in EEPROM at once
inline bool micBiasWanted() { return micType != MICTYPE_DYNAMIC; }   // bias ON for electret and for auto (the detection needs it)
inline int micSlot() { return micKind == MIC_DYNAMIC ? 1 : 0; }     // gain slot: 0 electret, 1 dynamic
// Factory gain per type (CC 82 scale 0..127 = 0..60 dB), from the dBFS calculation in FIRMWARE.md (R10V4): singing at 2 cm
// ~105 dB SPL (3.5 Pa), target ~ -22 dBFS rms (between -26 and the electronics' -18). Electret -42 dBV/Pa -> 9 dB; dynamic 0.45 mV/Pa -> 34 dB,
// 1.7 mV/Pa -> 22 dB: the dynamic default is the middle, 28 dB (-6 / +6 dB off the target for the two reference headsets).
const uint8_t MICGAIN_ELECTRET = 19, MICGAIN_DYNAMIC = 59;
uint8_t micGainSlot[2] = {MICGAIN_ELECTRET, MICGAIN_DYNAMIC};
inline int micDb(uint8_t v) { return (v * 60 + 63) / 127; }          // 0 .. 60 dB
enum { FM_EXACT, FM_ASSIST, FM_INTERVAL };   // harmonizer follow modes (CC 108)
uint8_t keysCC = 127;                   // CC 83, as sent (the menu shows it)
uint32_t speakerWarnAt = 0;             // millis() when the voice was sent to the speaker (the screen warns), 0 = nothing pending
struct VoiceFx {
  uint8_t voice = 0, vocoder = 0, harm = 0, interval = 64, echo = 0, echoTime = 40, echoFb = 40;
  uint8_t reverb = 40;
  // R6V4 item 5, factory values for a HEADSET microphone 2-3 cm from the mouth (calculation, not heard: FIRMWARE.md);
  // R10V4: the gain follows the microphone type (micGainSlot), here the electret's 6 dB; the rest as before: expander threshold ~550 (int16 units on the rectified level), ratio "hard" (cube), 1.2 ms attack,
  // ~78 ms hold, ~117 ms release, high-pass 167 Hz (the proximity effect boosts the lows).
  uint8_t gate = 32, micGain = MICGAIN_ELECTRET;
  uint8_t gateAtk = 20, gateHold = 50, gateRel = 40, gateRatio = 2, hpf = 40;
  bool antiFb = false, harmFollow = false, harmFold = true, speaker = false;   // suppressor off and speaker off by default
  uint8_t followMode = FM_EXACT, helpAmt = 80;   // R6V4: how the harmonizer follows the keys; assist strength
  bool harm4 = false;                   // R6V4: 3 (default) or 4 harmony voices
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
// R6V4: the voice effects need a microphone in IN as well: without one everything of the voice is silent.
uint32_t micMuteUntil = 0;              // R10V4: the voice is silent ~150 ms after the bias block is switched (the DC step)
inline bool voiceBlocked() { return speakerMutesVoice() || !micPlugged || (micMuteUntil && (int32_t)(micMuteUntil - millis()) > 0); }
float helpDryScale = 1.0f;              // assist mode takes the dry voice away while the assisted voice sounds (crossfade)
inline int harmVoicesWanted() { return vfxState.harm4 ? 4 : 3; }

inline float eqCutHz(uint8_t v) { return 150.0f + v * (300.0f / 127.0f); }
inline float eqDipDb(uint8_t v) { return v * (12.0f / 127.0f); }

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

static bool shifterOn[VOICE_HARM_N] = {false, false, false, false};
vfx::FeedbackWatch fbWatch;
bool fbConnected = true;                // pfft starts connected

void voiceFxApply() {
  VoiceFx &f = vfxState;
  speakerEqApply();
  bool duck = voiceBlocked();
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
    bool want = harmOn && (k == 0 || (f.harmFollow && k < harmVoicesWanted()));
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
    for (int k = 1; k < VOICE_HARM_N; k++) harmMix.gain(k, 0.0f);
  } else {                                                           // harmFollowUpdate() sets these
    for (int k = 0; k < VOICE_HARM_N; k++) harmMix.gain(k, 0.0f);
  }
  pitchTrk.setActive(harmOn && f.harmFollow);
  echo.setDelayMs(60.0f + f.echoTime * (680.0f / 127.0f));
  echo.setFeedback(f.echoFb * (0.85f / 127.0f));
  echoSrc.gain(0, 1.0f);
  echoSrc.gain(1, f.harm > 0 ? 1.0f : 0.0f);                       // the shifter passes the voice through when it is off
  voiceBus.gain(0, vfxCurve(f.voice) * 1.5f * live * helpDryScale);
  voiceBus.gain(1, vfxCurve(f.harm) * 1.5f * live);
  voiceBus.gain(2, vfxCurve(f.echo) * 1.5f * live);
  roomIn.gain(0, 1.0f);
  roomIn.gain(1, vfxCurve(f.reverb));
  roomIn.gain(2, vfxCurve(f.reverb));
  master.gain(2, 1.0f);
  master.gain(3, 1.0f);
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
}

void voiceFxMicGain() {
  static int8_t lastBias = -1;
  bool bias = micBiasWanted();
  codec.micSetup(micDb(vfxState.micGain), bias);
  if (lastBias >= 0 && lastBias != (int8_t)bias) { micMuteUntil = millis() + 150; voiceFxApply(); }   // silence the DC step of the bias switching
  lastBias = bias;
}   // 0 .. 60 dB and the bias (I2C: only when it changes)

void micTypeChanged();                  // R10V4: defined below, after the EEPROM code

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
    case 82: f.micGain = value; micGainSlot[micSlot()] = value; voiceFxMicGain(); break;
    case 111: micType = min(value / 43, 2); micTypeChanged(); return true;     // R10V4: 0 auto, 1 electret, 2 dynamic
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
    case 108: f.followMode = min(value / 32, 2); break;        // R6V4: exact / assist / interval
    case 109: f.helpAmt = value; break;                        // R6V4: assist strength
    case 110: f.harm4 = value >= 64; break;                    // R6V4: 3 or 4 harmony voices
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

// "Mic padrão" action (menu): the input settings back to the factory values for the microphone type in use, 2-3 cm from the mouth
// (R6V4 item 5; the same values VoiceFx starts with).
void voiceFxHeadsetMic() {
  VoiceFx d;
  VoiceFx &f = vfxState;
  f.gate = d.gate; f.gateRatio = d.gateRatio; f.gateAtk = d.gateAtk; f.gateHold = d.gateHold; f.gateRel = d.gateRel;
  f.hpf = d.hpf;
  micGainSlot[micSlot()] = micSlot() ? MICGAIN_DYNAMIC : MICGAIN_ELECTRET;
  f.micGain = micGainSlot[micSlot()];
  voiceFxMicGain();
  voiceFxApply();
}

void voiceFxClearNotches() {
  fbWatch.clear();
  for (int i = 0; i < vfx::VoiceInput::NOTCHES; i++) vin.clearNotch(i);
}

// ---- settings kept in EEPROM (menu "SAVE"). The speaker option is never kept: the voice is on
// the headphones / AUX at every start. ----
const int EEPROM_VOICE = 210;           // after the register (200..201)
const uint8_t VOICE_MAGIC = 0xA8, EQ_MAGIC = 0xE5, HARM_MAGIC = 0xE6;
void voiceFxSave() {
  VoiceFx &f = vfxState;
  uint8_t b[30] = {VOICE_MAGIC, f.voice, f.vocoder, f.harm, f.interval, f.echo, f.echoTime, f.echoFb, f.reverb, f.gate,
                   f.micGain, f.gateAtk, f.gateHold, f.gateRel, f.gateRatio, f.hpf, (uint8_t)f.antiFb,
                   (uint8_t)f.harmFollow, (uint8_t)f.harmFold, keysCC, 0, 0,
                   EQ_MAGIC, (uint8_t)f.eq, f.eqCut, f.eqDip,           // R5V4: the equalizer, after its own marker
                   HARM_MAGIC, f.followMode, f.helpAmt, (uint8_t)f.harm4};   // R6V4: harmonizer mode, assist strength, 3/4 voices
  for (int i = 0; i < 30; i++) EEPROM.write(EEPROM_VOICE + i, b[i]);
}

void voiceFxLoad() {
  if (EEPROM.read(EEPROM_VOICE) != VOICE_MAGIC) return;
  uint8_t b[30];
  for (int i = 0; i < 30; i++) b[i] = EEPROM.read(EEPROM_VOICE + i);
  VoiceFx &f = vfxState;
  f.voice = min(b[1], (uint8_t)127); f.vocoder = min(b[2], (uint8_t)127); f.harm = min(b[3], (uint8_t)127);
  f.interval = min(b[4], (uint8_t)127); f.echo = min(b[5], (uint8_t)127); f.echoTime = min(b[6], (uint8_t)127);
  f.echoFb = min(b[7], (uint8_t)127); f.reverb = min(b[8], (uint8_t)127); f.gate = min(b[9], (uint8_t)127);
  f.gateAtk = min(b[11], (uint8_t)127); f.gateHold = min(b[12], (uint8_t)127);
  f.gateRel = min(b[13], (uint8_t)127); f.gateRatio = min(b[14], (uint8_t)3); f.hpf = min(b[15], (uint8_t)127);
  f.antiFb = b[16] != 0; f.harmFollow = b[17] != 0; f.harmFold = b[18] != 0;
  keysCC = min(b[19], (uint8_t)127);
  keysLevel = keysCC / 127.0f;
  if (b[22] == EQ_MAGIC) { f.eq = b[23] != 0; f.eqCut = min(b[24], (uint8_t)127); f.eqDip = min(b[25], (uint8_t)127); }
  if (b[26] == HARM_MAGIC) { f.followMode = min(b[27], (uint8_t)FM_INTERVAL); f.helpAmt = min(b[28], (uint8_t)127); f.harm4 = b[29] != 0; }
}

void voiceFxDefaults() {
  vfxState = VoiceFx();
  micGainSlot[0] = MICGAIN_ELECTRET;
  micGainSlot[1] = MICGAIN_DYNAMIC;
  vfxState.micGain = micGainSlot[micSlot()];
  keysCC = 127;
  keysLevel = 1.0f;
  setAmbience(ambienceNow);
  voiceFxApply();
  voiceFxMicGain();
}

// Microphone type and the gain of each type (R10V4): kept at once when the type changes and with "Salvar".
const int EEPROM_MIC = 256;             // after the language (250..251)
const uint8_t MIC_MAGIC = 0xB2;
void micSave() {
  EEPROM.write(EEPROM_MIC, MIC_MAGIC);
  EEPROM.write(EEPROM_MIC + 1, micType);
  EEPROM.write(EEPROM_MIC + 2, micGainSlot[0]);
  EEPROM.write(EEPROM_MIC + 3, micGainSlot[1]);
}
void micLoad() {
  if (EEPROM.read(EEPROM_MIC) != MIC_MAGIC) return;
  micType = min((int)EEPROM.read(EEPROM_MIC + 1), 2);
  micGainSlot[0] = min((int)EEPROM.read(EEPROM_MIC + 2), 127);
  micGainSlot[1] = min((int)EEPROM.read(EEPROM_MIC + 3), 127);
}
// The type, or what the jack holds, changed: the gain of that type, the bias block, the voice chain.
void micTypeChanged() {
  if (micType == MICTYPE_DYNAMIC) micKind = MIC_DYNAMIC;        // declared: nothing to detect (the bias is off, MIC_DET reads 0 V)
  else if (micKind == MIC_DYNAMIC) micKind = MIC_NONE;          // leaving "dynamic": the detector decides again
  vfxState.micGain = micGainSlot[micSlot()];
  micPlugged = micKind != MIC_NONE;
  voiceFxMicGain();
  voiceFxApply();
  micSave();
}

// ---- harmonizer that follows the keys (R4V4, three modes and up to four voices in R6V4) ----
// The voice's pitch comes from the YIN tracker (pitchTrk). Every 12 ms the notes held on the keyboard (newest
// first) are shared out among the pitch shifters (the library's AudioEffectGranular), whose speed is set by the mode:
//   EXACT     each held note gets a shifter that puts the voice exactly on that note: speed = note Hz / voice Hz
//             (the voice's own vibrato and out-of-tune drift are taken out, "autotune"). Several notes = a sung chord.
//   ASSIST    one shifter: the held note nearest to the voice (within 3 semitones, octaves ignored) pulls the voice
//             only part of the way: shift = strength x (note - voice) in semitones, strength = CC 109 (127 = exact).
//             While it sounds the dry voice is crossfaded out (helpDryScale), so only the pulled voice is heard.
//   INTERVAL  the voice stays natural: the held note nearest to the voice is the one it "is on" (the reference) and every
//             other held note gets a shifter moved by exactly (that note - the reference) semitones: the distances
//             between the keys are kept, the voice's own intonation and vibrato are not touched.
// "Octave near" (CC 97, default) keeps the shift inside +-6 semitones (exact: ratio 0.71..1.41); off, an interval may
// go up to +-12 semitones (exact: ratio 0.25..4). The shifter ratio is smoothed (about 25 ms) while it follows the singer.
// Nothing held, or the voice unpitched for 300 ms: the harmony is silent. Up to harmVoicesWanted() (3 or 4) shifters work.
static int harmKey[VOICE_HARM_N] = {-1, -1, -1, -1};
static float harmRatio[VOICE_HARM_N] = {1, 1, 1, 1};
float voiceHzShown = 0;                 // last pitch the tracker found (for the screen)

// d (semitones) folded to the nearest octave: -6..+6
static inline float foldSemis(float d) { return d - 12.0f * roundf(d / 12.0f); }

void harmFollowUpdate() {
  VoiceFx &f = vfxState;
  static uint32_t lastAt = 0, seenAt = 0;
  static float lastF0 = 0;
  uint32_t now = millis();
  if (now - lastAt < 12) return;
  lastAt = now;
  bool active = f.harmFollow && f.harm > 0 && !voiceBlocked();
  if (!active) {
    if (helpDryScale != 1.0f) { helpDryScale = 1.0f; voiceFxApply(); }   // leaving the assist mode: the dry voice comes back
    return;
  }
  float f0 = pitchTrk.pitch();
  if (f0 > 0) { seenAt = now; lastF0 = f0; voiceHzShown = f0; }
  bool voiced = seenAt != 0 && now - seenAt < 300 && lastF0 > 0;
  const int nv = harmVoicesWanted();
  int mode = f.followMode;
  // the held notes, newest first, without repeats (interval mode needs one more: the reference note)
  int notes[VOICE_HARM_N + 1];
  int n = 0;
  int limit = mode == FM_INTERVAL ? nv + 1 : nv;
  for (int k = 0; k < limit; k++) {
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
  float voiceMidi = voiced ? 69.0f + 12.0f * log2f(lastF0 / 440.0f) : 0.0f;
  // the note nearest to the voice (octaves ignored), for assist and interval
  int ref = -1;
  float refDist = 99.0f;
  if (voiced) {
    for (int j = 0; j < n; j++) {
      float d = fabsf(foldSemis(notes[j] - voiceMidi));
      if (d < refDist) { refDist = d; ref = j; }
    }
  }
  // the shifters to run: key (identity, to jump the ratio when it changes), target ratio, share of the mix
  int key[VOICE_HARM_N];
  float target[VOICE_HARM_N];
  int count = 0;
  bool assisted = false;
  if (voiced && n > 0) {
    if (mode == FM_EXACT) {
      for (int j = 0; j < n && count < nv; j++) {
        float r = 440.0f * powf(2.0f, (notes[j] - 69) / 12.0f) / lastF0;
        if (f.harmFold) {
          while (r > 1.4142f) r *= 0.5f;
          while (r < 0.7071f) r *= 2.0f;
        } else {
          r = constrain(r, 0.25f, 4.0f);
        }
        key[count] = notes[j]; target[count++] = r;
      }
    } else if (mode == FM_ASSIST) {
      if (ref >= 0 && refDist <= 3.0f) {
        float d = foldSemis(notes[ref] - voiceMidi);
        key[0] = notes[ref];
        target[0] = powf(2.0f, d * (f.helpAmt / 127.0f) / 12.0f);
        count = 1;
        assisted = true;
      }
    } else if (ref >= 0) {                                              // interval
      for (int j = 0; j < n && count < nv; j++) {
        if (j == ref) continue;
        float d = notes[j] - notes[ref];
        if (f.harmFold) d = foldSemis(d);
        else d -= 24.0f * roundf(d / 24.0f);                              // -12..+12
        key[count] = notes[j] * 128 + notes[ref];
        target[count++] = powf(2.0f, d / 12.0f);
      }
    }
  }
  float share = count > 0 ? (mode == FM_ASSIST ? 1.0f : 1.0f / sqrtf((float)count)) : 0.0f;
  for (int k = 0; k < VOICE_HARM_N; k++) {
    if (k < count) {
      if (harmKey[k] != key[k]) harmRatio[k] = target[k];
      else harmRatio[k] += (target[k] - harmRatio[k]) * 0.4f;
      harmKey[k] = key[k];
      AudioNoInterrupts();
      harm[k].setSpeed(harmRatio[k]);
      AudioInterrupts();
      harmMix.gain(k, share);
    } else {
      harmMix.gain(k, 0.0f);
      harmKey[k] = -1;
    }
  }
  // assist: the dry voice goes out while the assisted voice sounds (smoothed, the mixer's gain steps are audible)
  float dryTarget = assisted ? 0.0f : 1.0f;
  if (fabsf(dryTarget - helpDryScale) > 0.001f) {
    helpDryScale += (dryTarget - helpDryScale) * 0.35f;
    if (fabsf(dryTarget - helpDryScale) < 0.02f) helpDryScale = dryTarget;
    voiceBus.gain(0, vfxCurve(f.voice) * 1.5f * helpDryScale);
  }
}

void feedbackUpdate() {
  if (!vfxState.antiFb || !fbConnected || !fftIn.available()) return;
  float mag[512];
  for (int i = 0; i < 512; i++) mag[i] = fftIn.read(i);
  int idx = fbWatch.feed(mag);
  if (idx >= 0) vin.setNotch(idx, fbWatch.freq[idx], fbWatch.depth[idx]);
}

// Called from loop().
void voiceFxUpdate() {
  harmFollowUpdate();
  feedbackUpdate();
}

void voiceFxBegin() {
  echo.begin(echoMem, VOICE_ECHO_SAMPLES);
  for (int k = 0; k < VOICE_HARM_N; k++) {
    harm[k].begin(harmMem[k], VOICE_HARM_SAMPLES);
    harm[k].stop();
  }
  pfft.disconnect();                    // switched on in the menu
  fbConnected = false;
  voc.setSpeed(4.0f, 25.0f);
  voiceFxLoad();
  voiceFxApply();
  voiceFxMicGain();
}

void handleControlChange(byte channel, byte control, byte value) {
  if (voiceFxControl(control, value)) return;
  switch (control) {
    case 7:
      setVolume(value);
      break;
    case 9:
      velocityCurve = min(value / 32, 3);
      break;
    case 14:
      if (value >= 64) {
        scanPaused = true;                          // the scan interrupt reads the models resetCalibration() rewrites
        resetCalibration();
        scanPaused = false;
      }
      break;
    case 15:
      keyTest = value >= 64;
      for (int i = 0; i < keyCount; i++) keyState[i].sentPosition = 255;
      break;
    case 24:
      layoutSystem = value < 64 ? 0 : 1;
      break;
    case 26:
      registerMask = value & 0x0F;
      applyOscGains();
      registerChanged();
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

// ---- Sensor scan ----
// A "1" in the chain of 74HC595 switches ON the sensor at that stage (EN high); everything
// else is off, so the OUT lines stay free. Contract from PINOS.md:
//  - SRCLK and RCLK share one line, so the OUTPUT lags the shift by one pulse (it shows the
//    state before the pulse);
//  - R10V4: an R8 uses all 8 stages and an R4 (always the last ruler of the row) the first 4 of its own, so column c =
//    stage c (stage 0 = the first ruler's QA, nearest DATA) and the next column is always 1 pulse away (no dead stage
//    between two columns, R10V4; the R7V4 chain of R4 rulers had 4 of them between rulers);
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

// Switches column c on. The next column in order is 1 pulse away. Anywhere else (random access, the hot
// reads and the wrap from the last column to the first): push the whole pattern (the first bit sent ends in the
// LAST stage), plus one pulse to latch it: SR_STAGES + 1 pulses = 9 with one R8 per row (~1.8 us at 5 MHz).
void srSelect(int c) {
  if (srPos >= 0 && c == srPos + 1) {
    srPulse(0);
  } else {
    int target = c;                                       // stage = column
    for (int k = 0; k < SR_STAGES; k++) srPulse(SR_STAGES - 1 - k == target);
    srPulse(0);
  }
  srPos = c;
  srOnAt = micros();
}

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

// Reads the sensors of the selected column (after the wake-up), one per row, with
// the time of each reading. Rows with no key there are skipped.
// Rows 1 and 2 (pins 14, 15) are read on ADC1 and rows 3 and 4 (26, 27: ADC2 only) on ADC2, at
// the same time: two pairs, about 2 x 3 us instead of 4 x 5.6 us one after the other.
void readColumn(int c, uint16_t *raw, uint32_t *at) {
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

void setupKeys() {
  pinMode(SR_DATA_PIN, OUTPUT);
  pinMode(SR_CLK_PIN, OUTPUT);
  digitalWriteFast(SR_CLK_PIN, LOW);
  for (int r = 0; r < LAYOUT_ROWS; r++) pinMode(ROW_OUT_PINS[r], INPUT_DISABLE);   // the board's 100 kohm pull-down makes a missing sensor read 0 V
  memset(colKey, 255, sizeof(colKey));
  srClear();
  analogReadResolution(12);
  analogReadAveraging(1);
  setupAdc();
  keyCount = 0;
  for (int r = 0; r < LAYOUT_ROWS; r++) {
    for (int c = 0; c < LAYOUT_COLS; c++) {
      if (!keyExists(r, c) || keyCount == MAX_KEYS) continue;
      Key &k = keyState[keyCount++];
      memset(&k, 0, sizeof(k));
      k.row = r;
      k.col = c;
      k.outLine = r;
      k.column = c;
      colKey[c][r] = keyCount - 1;
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
    // Which way this key's sensor goes: the magnet at rest already pushes
    // the reading off 1.65 V, up or down.
    float off = keyState[i].rest - SENSOR_ZERO;
    keyState[i].sign = off > SIGN_MIN ? 1 : (off < -SIGN_MIN ? -1 : DEFAULT_SIGN);
    if (keyState[i].sign < 0) keyState[i].rest = 4095.0f - keyState[i].rest;
  }
  loadCalibration();
}

// Time (in micros) at which the travel crossed `level`, interpolated
// between the previous scan and this one.
uint32_t crossingTime(const Key &k, float prev, float now, float level, uint32_t nowMicros) {
  float f = (level - prev) / max(now - prev, 1e-4f);
  return k.prevMicros + (uint32_t)(constrain(f, 0.0f, 1.0f) * (float)(nowMicros - k.prevMicros));
}

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
    if (fabsf(k.rest - k.restAtModel) > 0.5f) updateModel(k);   // do not take cube roots every pass
  }
  if (raw > k.bottom + 4 && raw > k.rest + MIN_SPAN) {
    k.bottom = raw;
    updateModel(k);
    calibrationDirty = true;
    calibrationChangedAt = millis();
  }
  float t = keyTravel(k, raw);
  k.rising = t > k.travel + 0.002f;
  if (k.rising) k.hotUntil = now + HOT_HOLD_US;
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

// ---- Scan in a timer interrupt ----
// The scan used to be loop() itself, so everything else in loop() (MIDI, knobs, screen, voice
// control) and every audio interrupt delayed it. Now an IntervalTimer calls scanTick() every
// SCAN_TICK_US at a priority ABOVE the audio's (and USB's, and the DMA's): the audio can
// not stretch a pass, and loop() is free of the busy waiting (it only drains the event queue).
// scanTick() never waits: it reads the column whose sensors have been awake for SENSOR_WAKE_US,
// switches the next one on, processes the readings, and returns. Key events (note on / off
// with velocity, key-test positions) go into a queue, because the voices and usbMIDI belong to
// loop(). The hot reads (see HOT_FROM) work as before, round robin among the columns with a rising key.
IntervalTimer scanTimer;
volatile uint32_t lastPassUs = 0;       // the last full pass (microseconds)
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

// The page's "Reset to default": classic accordion, register MM, dry.
void defaultSound() {
  registerMask = 0b0110;
  wetCents = 0;
  applyOscGains();
  retuneAll();
}

bool registerPending = false;           // a knob choice made, not yet kept with a click

// ============================================================
// Power, battery, speaker and the two knobs. NOT yet run on a board:
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
// ============================================================
const uint8_t REGISTERS[7] = {1, 3, 6, 10, 8, 9, 2};   // CC 26 masks, in the selector's order
const int DEFAULT_REGISTER = 2;                         // MM
const int VOLUME_PER_DETENT = 3;
const uint32_t POWER_HOLD_MS = 2000;
const uint32_t IDLE_REST_MS = 5UL * 60 * 1000;
const uint32_t IDLE_OFF_MS = 15UL * 60 * 1000;
const float BATTERY_LOW_V = 3.5f;
const float BATTERY_EMPTY_V = 3.3f;
const int EEPROM_REGISTER = 200;        // after the key calibration (4 + 2 * 80 bytes at most)
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
bool micPlugged = false;                // set by updatePower() from MIC_DET
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
void oledOff();
void powerOff() {
  silenceAll();
  digitalWriteFast(AMP_SD_PIN, LOW);
  scanEnd();
  srClear();
  oledOff();
  if (calibrationDirty) saveCalibration();
  setLed(true, false);
  delay(250);
  setLed(false, false);                 // LED out: the click can be let go
  digitalWriteFast(KEEP_PIN, LOW);
  // Nothing cuts the 3.3 V while USB is plugged in (PWR_EN is not wired),
  // so "off" is a soft off: everything above is already dark. A click, or unplugging
  // the cable (the supply then falls by itself), ends it; the click restarts the processor.
  while (usbPower() && digitalReadFast(VOL_SW_PIN) == HIGH) delay(20);
  SCB_AIRCR = 0x05FA0004;               // system reset
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
  pinMode(MIC_DET_PIN, INPUT_DISABLE);
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
void menuMicChanged();

void updateControls() {
  uint32_t now = millis();
  // volume knob
  noInterrupts();
  int turned = volSteps / ENC_STEPS_PER_DETENT;
  volSteps -= turned * ENC_STEPS_PER_DETENT;
  interrupts();
  if (turned) {
    oledWarnUntil = 0;
    menuLastInput = now;
    if (menuOpen) menuAdjust(turned);
    else
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
    if (down) volPressAt = now;
    if (!down && !volIgnoreHold) {
      oledWarnUntil = 0;
      menuLastInput = now;
      if (menuOpen) menuBack();
    }
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
    oledWarnUntil = 0;
    menuLastInput = now;
    if (menuOpen) menuTurn(detents);
    else
    {
      applyRegister(registerIndex + detents, true);
      registerPending = true;
    }
    lastActivityAt = now;
  }
  down = digitalReadFast(ENC_SW_PIN) == LOW;
  if (down != selDown && now - selChangedAt > 20) {
    selDown = down;
    selChangedAt = now;
    lastActivityAt = now;
    if (down) {
      selPressAt = now;
      selLongFired = false;
    } else if (!selLongFired) {                         // short click, on release
      oledWarnUntil = 0;
      menuLastInput = now;
      if (menuOpen) menuClick();
      else if (registerPending) {
        saveRegister(registerIndex);                    // the one to start with next time
        registerPending = false;
      } else {
        defaultSound();
        registerIndex = DEFAULT_REGISTER;
        saveRegister(DEFAULT_REGISTER);
        usbMIDI.sendControlChange(26, registerMask, 1);
      }
    }
  }
  if (selDown && !selLongFired && now - selPressAt >= MENU_LONG_MS) {   // long click: the menu
    selLongFired = true;
    oledWarnUntil = 0;
    menuLastInput = now;
    menuToggle();
  }
  if (menuOpen && now - menuLastInput > MENU_IDLE_MS) menuToggle();
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
  {                                          // R6V4: is a microphone in the IN jack? (debounced: 3 equal reads, 50 ms apart)
    static uint32_t micReadAt = 0;
    static uint8_t micSame = 0;
    static uint8_t micRaw = MIC_NONE;
    static bool micInit = false;
    if (now - micReadAt >= 50) {
      micReadAt = now;
      uint8_t raw;
      float v = analogReadSlow(MIC_DET_PIN) / ADC_PER_VOLT;
      if (v <= MIC_SHORT_V || v >= MIC_OPEN_V) raw = MIC_NONE;
      else if (micType == MICTYPE_ELECTRET) raw = MIC_ELECTRET;           // declared: any microphone-like load is the electret
      else raw = v < (micKind == MIC_DYNAMIC ? MIC_DYN_DOWN_V : MIC_DYN_UP_V) ? MIC_DYNAMIC : MIC_ELECTRET;
      if (micType == MICTYPE_DYNAMIC) raw = MIC_DYNAMIC;                  // declared: the bias is off, the detector is blind
      micSame = (micInit && raw == micRaw) ? min(micSame + 1, 3) : 1;
      micRaw = raw;
      micInit = true;
      if (micSame >= 3 && raw != micKind) {
        micKind = raw;                                                    // the gain of this kind (the bias does not change in auto)
        micPlugged = micKind != MIC_NONE;
        vfxState.micGain = micGainSlot[micSlot()];
        voiceFxMicGain();
      }
    }
  }
  static bool lastHeadphones = headphones, lastMic = micPlugged;
  static uint8_t lastKind = micKind;
  if (lastHeadphones != headphones || lastMic != micPlugged || lastKind != micKind) {   // the voice follows the jack (headphones / AUX in, speaker out, R4V4) and the microphone (R6V4)
    lastHeadphones = headphones;
    lastMic = micPlugged;
    lastKind = micKind;
    voiceFxApply();
    menuMicChanged();
  }
  if (micMuteUntil && (int32_t)(now - micMuteUntil) >= 0) { micMuteUntil = 0; voiceFxApply(); }
  resting = now - lastActivityAt > IDLE_REST_MS;
  if (now - lastActivityAt > IDLE_OFF_MS) powerOff();
  digitalWriteFast(AMP_SD_PIN, !headphones && !resting);
}

// ---- OLED: 128 x 64 SSD1306 on I2C ----
// No library is installed with Teensyduino for it, so this is a small driver of its own:
// a 1 KB frame buffer, a 5 x 7 font (digits and capitals), sent to the panel in 16-byte
// pieces, one per loop pass, and only while no key is moving: I2C is blocking and a piece
// takes ~0.4 ms. OLED_ROTATION 2 = what Adafruit_SSD1306::setRotation(2) does (the
// panel mounted upside down), done by the controller's segment remap + COM scan direction.
uint8_t oledBuf[1024];
bool oledPresent = false;
int oledSent = 1024;                    // bytes of the frame already sent (1024 = idle)
uint32_t oledSig = 0xFFFFFFFF, oledDrawnAt = 0;

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

// R6V4 item 7: a 5 x 10 font with lower case and accents (oled_font.h, made by tools/oled_font/make_font.py) and UTF-8
// strings. The cell is 10 rows high: capitals sit on rows 2..8, lower-case x-height on rows 4..8, accents above, and a
// one-row descender (row 9). Text coordinates (x, y) are the top-left corner of the cell; at scale 1 a menu line is 10 px.
#include "oled_font.h"

const uint16_t *oledGlyph(uint32_t cp) {
  if (cp >= 32 && cp <= 126) return OLED_FONT_ASCII[cp - 32];
  int lo = 0, hi = OLED_FONT_EXT_COUNT - 1;
  while (lo <= hi) {                                    // OLED_FONT_EXT is sorted by code point
    int mid = (lo + hi) / 2;
    if (OLED_FONT_EXT[mid].cp == cp) return OLED_FONT_EXT[mid].col;
    if (OLED_FONT_EXT[mid].cp < cp) lo = mid + 1; else hi = mid - 1;
  }
  return OLED_FONT_ASCII['?' - 32];
}

// The next Unicode code point of a UTF-8 string (advances s); bad bytes come out as '?'.
uint32_t utf8Next(const char *&s) {
  uint8_t c = (uint8_t)*s++;
  if (c < 0x80) return c;
  int extra = (c >= 0xF0) ? 3 : (c >= 0xE0) ? 2 : (c >= 0xC0) ? 1 : -1;
  if (extra < 0) return '?';
  uint32_t cp = c & (0x3F >> extra);
  for (int i = 0; i < extra; i++) {
    if (((uint8_t)*s & 0xC0) != 0x80) return '?';
    cp = (cp << 6) | ((uint8_t)*s++ & 0x3F);
  }
  return cp;
}

int oledTextLen(const char *s) {                        // glyphs in a UTF-8 string
  int n = 0;
  while (*s) { utf8Next(s); n++; }
  return n;
}

// Text with a colour: on = false draws black on a white bar (the highlighted menu line).
void oledTextOn(int x, int y, const char *str, int scale, bool on) {
  while (*str) {
    const uint16_t *g = oledGlyph(utf8Next(str));
    for (int col = 0; col < 5; col++) {
      uint16_t bits = g[col];
      for (int row = 0; row < 10; row++) {
        if (bits & (1 << row)) oledRect(x + col * scale, y + row * scale, scale, scale, on);
      }
    }
    x += 6 * scale;
  }
}

void oledTextRight(int xRight, int y, const char *str, bool on) {
  oledTextOn(xRight - 6 * oledTextLen(str), y, str, 1, on);
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

void oledSetup() {
  Wire.setClock(400000);
  Wire.beginTransmission(OLED_ADDR);
  oledPresent = Wire.endTransmission() == 0;
  if (!oledPresent) {
    OLED_ADDR = 0x3C;
    Wire.beginTransmission(OLED_ADDR);
    oledPresent = Wire.endTransmission() == 0;
  }
  if (!oledPresent) return;
  static const uint8_t init[] = {0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00,
                                 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6};
  for (unsigned i = 0; i < sizeof(init); i++) {
    if (OLED_SH1106 && (i == 10 || i == 11)) continue;                        // 0x20 0x00: the SH1106 has no addressing-mode command
    oledCmd(init[i]);
  }
  if (OLED_SH1106) { oledCmd(0xAD); oledCmd(0x8B); }                          // internal DC-DC on
  // Rotation 0 as Adafruit_SSD1306 starts it = segment remap + COM scan decrement; rotation 2 = both off.
  oledCmd(OLED_ROTATION == 2 ? 0xA0 : 0xA1);
  oledCmd(OLED_ROTATION == 2 ? 0xC0 : 0xC8);
  oledCmd(0xAF);
}

void oledOff() {
  if (oledPresent) oledCmd(0xAE);
}

// ---- Screen texts (R6V4 item 7): Portuguese and English, lower case with accents. Every text of the screen is in
// this section: STR[] (single strings) and the Txt tables of the menu. To add a language: add its name to LANG_NAME and an
// entry in LANG_COUNT's enum, then add one more string to every Txt initializer below (a missing one falls back to English).
// The strings are UTF-8; the characters must exist in oled_font.h (ASCII and the Latin-1 letters with accents).
const int EEPROM_LANG = 250;            // after the voice settings (210..239)
const uint8_t LANG_MAGIC = 0xB1;
void uiLangSave() { EEPROM.write(EEPROM_LANG, LANG_MAGIC); EEPROM.write(EEPROM_LANG + 1, uiLang); }
void uiLangLoad() {
  if (EEPROM.read(EEPROM_LANG) == LANG_MAGIC && EEPROM.read(EEPROM_LANG + 1) < LANG_COUNT) uiLang = EEPROM.read(EEPROM_LANG + 1);
}

// ---- Menu (R4V4 item 4): drawn on the OLED, driven by the two knobs ----
// Layout: 21 columns. A level line is a label (up to 11 characters), a 19-pixel bar and a value of up to 6 characters;
// a choice line is a label and a value, together up to 21 characters.
const MenuItem ITEMS_MAIN[] = {
  {{"Voz", "Voice"}, MK_SUB, PG_VOICE, true}, {{"Captação", "Input"}, MK_SUB, PG_INPUT, true},
  {{"Saída", "Output"}, MK_SUB, PG_OUTPUT, false}, {{"Som", "Sound"}, MK_SUB, PG_SOUND, false},
  {{"Sistema", "System"}, MK_SUB, PG_SYSTEM, false}};
const MenuItem ITEMS_VOICE[] = {
  {{"Voz seca", "Dry voice"}, MK_LEVEL, M_VOICE_DRY, true}, {{"Vocoder", "Vocoder"}, MK_LEVEL, M_VOCODER, true},
  {{"Harmoniz.", "Harmonizer"}, MK_LEVEL, M_HARM, true}, {{"Modo harm.", "Harm mode"}, MK_ENUM, M_HARM_MODE, true},
  {{"Intervalo", "Interval"}, MK_LEVEL, M_HARM_INT, true}, {{"Intensidade", "Strength"}, MK_LEVEL, M_HARM_HELP, true},
  {{"Vozes", "Voices"}, MK_ENUM, M_HARM_VOICES, true}, {{"Oitava", "Octave"}, MK_ENUM, M_HARM_FOLD, true},
  {{"Eco", "Echo"}, MK_LEVEL, M_ECHO, true}, {{"Tempo eco", "Echo time"}, MK_LEVEL, M_ECHO_TIME, true},
  {{"Realim. eco", "Echo fdbk"}, MK_LEVEL, M_ECHO_FB, true}, {{"Reverb voz", "Voice rev"}, MK_LEVEL, M_VOICE_REV, true}};
const MenuItem ITEMS_INPUT[] = {
  {{"Ganho mic", "Mic gain"}, MK_LEVEL, M_MIC_GAIN, true}, {{"Limiar", "Threshold"}, MK_LEVEL, M_GATE_THR, true},
  {{"Razão", "Ratio"}, MK_ENUM, M_GATE_RATIO, true}, {{"Ataque", "Attack"}, MK_LEVEL, M_GATE_ATK, true},
  {{"Retenção", "Hold"}, MK_LEVEL, M_GATE_HOLD, true}, {{"Soltura", "Release"}, MK_LEVEL, M_GATE_REL, true},
  {{"Passa-altas", "High-pass"}, MK_LEVEL, M_HPF, true}, {{"Mic padrão", "Mic default"}, MK_ACTION, M_CLOSE_MIC, true},
  {{"Antimicrof.", "Anti-feedbk"}, MK_ENUM, M_ANTI_FB, true}, {{"Limpar notch", "Clear notch"}, MK_ACTION, M_CLEAR_NOTCH, true}};
const MenuItem ITEMS_OUTPUT[] = {
  {{"Volume", "Volume"}, MK_LEVEL, M_VOLUME, false}, {{"Saída voz", "Voice out"}, MK_ENUM, M_VOICE_OUT, true},
  {{"Teclas", "Keys"}, MK_LEVEL, M_KEYS_LEVEL, true}, {{"EQ alto-f.", "Speaker EQ"}, MK_ENUM, M_SPK_EQ, false},
  {{"Corte", "Cutoff"}, MK_LEVEL, M_EQ_CUT, false}, {{"Pico 1k", "1k dip"}, MK_LEVEL, M_EQ_DIP, false}};
const MenuItem ITEMS_SOUND[] = {
  {{"Registro", "Register"}, MK_ENUM, M_REGISTER, false},
  {{"Reverb", "Reverb"}, MK_LEVEL, M_AMBIENCE, false}, {{"Curva vel.", "Vel curve"}, MK_ENUM, M_VEL_CURVE, false}};
const MenuItem ITEMS_SYSTEM[] = {
  {{"Salvar", "Save"}, MK_ACTION, M_SAVE, false}, {{"Zerar voz", "Reset voice"}, MK_ACTION, M_RESET_VOICE, false},
  {{"Calibrar", "Calibrate"}, MK_ACTION, M_CAL_KEYS, false}, {{"Teste tec.", "Key test"}, MK_ENUM, M_KEY_TEST, false},
  {{"Tipo mic", "Mic type"}, MK_ENUM, M_MIC_TYPE, false}, {{"Idioma", "Language"}, MK_ENUM, M_LANGUAGE, false}};
#define PAGE_OF(name, arr) {name, arr, (uint8_t)(sizeof(arr) / sizeof(arr[0]))}
const MenuPage MENU_PAGES[PG_COUNT] = {
  PAGE_OF((Txt{{"Menu", "Menu"}}), ITEMS_MAIN), PAGE_OF((Txt{{"Voz", "Voice"}}), ITEMS_VOICE),
  PAGE_OF((Txt{{"Captação", "Input"}}), ITEMS_INPUT), PAGE_OF((Txt{{"Saída", "Output"}}), ITEMS_OUTPUT),
  PAGE_OF((Txt{{"Som", "Sound"}}), ITEMS_SOUND), PAGE_OF((Txt{{"Sistema", "System"}}), ITEMS_SYSTEM)};

uint8_t menuPage = PG_MAIN;
int menuCursor = 0, menuScroll = 0;         // cursor and scroll count VISIBLE lines only
uint8_t menuDepth = 0;
struct MenuFrame { uint8_t page; int cursor, scroll; } menuStack[3];
const char *menuToast = nullptr;
uint32_t menuToastAt = 0;

// Is a line on the menu now? Needs a microphone, or depends on the harmonizer's mode.
bool menuShown(const MenuItem &it) {
  if (it.needsMic && !micPlugged) return false;
  if (it.kind == MK_SUB) return true;
  const VoiceFx &f = vfxState;
  switch (it.id) {
    case M_HARM_INT: return !f.harmFollow;                           // fixed interval: only when the harmonizer does not follow
    case M_HARM_HELP: return f.harmFollow && f.followMode == FM_ASSIST;
    case M_HARM_VOICES: return f.harmFollow;
    case M_HARM_FOLD: return f.harmFollow && f.followMode != FM_ASSIST;
  }
  return true;
}
int menuCount(int page) {
  int n = 0;
  for (int i = 0; i < MENU_PAGES[page].count; i++) n += menuShown(MENU_PAGES[page].items[i]);
  return n;
}
const MenuItem &menuLine(int page, int vi) {                          // the vi-th visible line
  const MenuPage &pg = MENU_PAGES[page];
  for (int i = 0; i < pg.count; i++) {
    if (!menuShown(pg.items[i])) continue;
    if (vi-- == 0) return pg.items[i];
  }
  return pg.items[0];
}
void menuClamp() {
  int count = menuCount(menuPage);
  if (menuCursor >= count) menuCursor = max(count - 1, 0);
  if (menuScroll > menuCursor) menuScroll = menuCursor;
  if (menuCursor > menuScroll + 4) menuScroll = menuCursor - 4;
  if (menuScroll < 0) menuScroll = 0;
}

// The CC and the current value of a level line (volume: copied, it is an int).
bool menuLevelRef(uint8_t id, uint8_t *&p, uint8_t &cc) {
  static uint8_t tmp;
  VoiceFx &f = vfxState;
  switch (id) {
    case M_VOICE_DRY: p = &f.voice; cc = 16; return true;
    case M_VOCODER: p = &f.vocoder; cc = 17; return true;
    case M_HARM: p = &f.harm; cc = 18; return true;
    case M_HARM_INT: p = &f.interval; cc = 19; return true;
    case M_HARM_HELP: p = &f.helpAmt; cc = 109; return true;
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

// The text of a line's value (at most 9 characters; level lines at most 6).
void menuValueText(uint8_t id, char *b, size_t n) {
  VoiceFx &f = vfxState;
  uint8_t *p;
  uint8_t cc;
  b[0] = 0;
  switch (id) {
    case M_HARM_INT: { int st = lroundf(((int)f.interval - 64) * 12.0f / 64.0f); snprintf(b, n, "%+d st", st); return; }
    case M_ECHO_TIME: snprintf(b, n, "%d ms", (int)lroundf(60.0f + f.echoTime * (680.0f / 127.0f))); return;
    case M_MIC_GAIN: snprintf(b, n, "%d dB", micDb(f.micGain)); return;
    case M_MIC_TYPE: snprintf(b, n, "%s", tr(MIC_TYPE_NAMES[micType])); return;
    case M_GATE_ATK: snprintf(b, n, "%.1f ms", gateAtkMs(f.gateAtk)); return;
    case M_GATE_HOLD: snprintf(b, n, "%d ms", (int)gateHoldMs(f.gateHold)); return;
    case M_GATE_REL: snprintf(b, n, "%d ms", (int)gateRelMs(f.gateRel)); return;
    case M_HPF: snprintf(b, n, "%d Hz", (int)hpfHz(f.hpf)); return;
    case M_EQ_CUT: snprintf(b, n, "%d Hz", (int)lroundf(eqCutHz(f.eqCut))); return;
    case M_EQ_DIP: snprintf(b, n, "-%d dB", (int)lroundf(eqDipDb(f.eqDip))); return;
    case M_SPK_EQ: snprintf(b, n, "%s", tx(f.eq ? S_ON : S_OFF)); return;
    case M_HARM_MODE: snprintf(b, n, "%s", tr(HARM_MODES[f.harmFollow ? 1 + f.followMode : 0])); return;
    case M_HARM_VOICES: snprintf(b, n, "%d", harmVoicesWanted()); return;
    case M_HARM_FOLD: snprintf(b, n, "%s", tr(FOLD_NAMES[f.harmFold ? 1 : 0])); return;
    case M_GATE_RATIO: snprintf(b, n, "%s", tr(RATIO_NAMES[f.gateRatio])); return;
    case M_ANTI_FB: snprintf(b, n, "%s", tx(f.antiFb ? S_ON : S_OFF)); return;
    case M_VOICE_OUT: snprintf(b, n, "%s", tx(f.speaker ? S_SPEAKER_ON : S_PHONES)); return;
    case M_REGISTER: snprintf(b, n, "%s", REGISTER_NAMES[registerIndex]); return;
    case M_VEL_CURVE: snprintf(b, n, "%s", tr(CURVE_NAMES[velocityCurve])); return;
    case M_KEY_TEST: snprintf(b, n, "%s", tx(keyTest ? S_ON : S_OFF)); return;
    case M_LANGUAGE: snprintf(b, n, "%s", LANG_NAME[uiLang]); return;
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

// The microphone was plugged or pulled out: the voice pages appear or go away. If the cursor was in one, back to the top.
void menuMicChanged() {
  if (!menuOpen) return;
  if (!micPlugged && (menuPage == PG_VOICE || menuPage == PG_INPUT)) { menuPage = PG_MAIN; menuDepth = 0; menuCursor = menuScroll = 0; }
  menuClamp();
}

void menuTurn(int d) {
  int count = menuCount(menuPage);
  if (count < 1) return;
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
  menuClamp();
}

void menuSetCC(uint8_t cc, uint8_t value) {
  handleControlChange(1, cc, value);                    // the same path as a CC from the page
  usbMIDI.sendControlChange(cc, value, 1);              // and the page can follow the menu
}

// Volume knob: the value of the line under the cursor, one step per detent.
void menuAdjust(int d) {
  const MenuItem &it = menuLine(menuPage, menuCursor);
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
    case M_HARM_MODE: {                                 // fixed, exact, assist, interval
      int cur = f.harmFollow ? 1 + f.followMode : 0;
      int next = ((cur + d) % 4 + 4) % 4;
      if (next == 0) menuSetCC(95, 0);
      else { menuSetCC(108, (uint8_t)((next - 1) * 32)); menuSetCC(95, 127); }
      break;
    }
    case M_HARM_VOICES: menuSetCC(110, f.harm4 ? 0 : 127); break;
    case M_HARM_FOLD: menuSetCC(97, f.harmFold ? 0 : 127); break;
    case M_GATE_RATIO: menuSetCC(93, (uint8_t)(constrain((int)f.gateRatio + d, 0, 3) * 32)); break;
    case M_ANTI_FB: menuSetCC(94, f.antiFb ? 0 : 127); break;
    case M_VOICE_OUT: menuSetCC(96, f.speaker ? 0 : 127); break;
    case M_SPK_EQ: menuSetCC(105, f.eq ? 0 : 127); break;
    case M_REGISTER: applyRegister(registerIndex + d, true); registerPending = false; break;
    case M_VEL_CURVE: menuSetCC(9, (uint8_t)((((velocityCurve + d) % 4 + 4) % 4) * 32)); break;
    case M_KEY_TEST: menuSetCC(15, keyTest ? 0 : 127); break;
    case M_MIC_TYPE: menuSetCC(111, (uint8_t)((((micType + d) % 3 + 3) % 3) * 43)); break;    // kept in EEPROM at once
    case M_LANGUAGE: uiLang = (uiLang + d + LANG_COUNT * 4) % LANG_COUNT; uiLangSave(); break;   // kept at once, no "Save" needed
  }
  menuClamp();                                          // a change of mode can add or remove lines
}

// Selector click.
void menuClick() {
  const MenuItem &it = menuLine(menuPage, menuCursor);
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
        case M_CLOSE_MIC: voiceFxHeadsetMic(); menuToast = tx(S_T_HEADSET); break;
        case M_CLEAR_NOTCH: voiceFxClearNotches(); menuToast = tx(S_T_NOTCH); break;
        case M_SAVE: voiceFxSave(); micSave(); saveRegister(registerIndex); menuToast = tx(S_T_SAVED); break;
        case M_RESET_VOICE: voiceFxDefaults(); menuToast = tx(S_T_RESET); break;
        case M_CAL_KEYS: handleControlChange(1, 14, 127); menuToast = tx(S_T_CAL); break;
      }
      menuToastAt = millis();
      break;
  }
}

void drawMenu() {
  const MenuPage &pg = MENU_PAGES[menuPage];
  oledRect(0, 0, 128, 10, true);                        // title bar
  char line[40];
  if (menuToast && millis() - menuToastAt < 1500) {
    oledTextOn(2, 0, menuToast, 1, false);
  } else if (menuPage == PG_MAIN) {
    oledTextOn(2, 0, tx(S_MENU), 1, false);
  } else {
    snprintf(line, sizeof(line), "%s > %s", tx(S_MENU), tr(pg.name));
    oledTextOn(2, 0, line, 1, false);
  }
  int count = menuCount(menuPage);
  snprintf(line, sizeof(line), "%d/%d", menuCursor + 1, count);
  oledTextRight(126, 0, line, false);
  for (int r = 0; r < 5; r++) {
    int idx = menuScroll + r;
    if (idx >= count) break;
    const MenuItem &it = menuLine(menuPage, idx);
    int y = 11 + r * 10;                                // top of a 10-row line
    bool sel = idx == menuCursor;
    if (sel) oledRect(0, y, 128, 10, true);
    oledTextOn(2, y, tr(it.name), 1, !sel);
    if (it.kind == MK_SUB) {
      oledTextRight(126, y, ">", !sel);
    } else if (it.kind == MK_LEVEL) {
      uint8_t *p;
      uint8_t cc;
      if (menuLevelRef(it.id, p, cc)) {
        int fill = *p * 15 / 127;                       // bar 70..88, 19 px wide
        bool on = !sel;
        oledRect(70, y + 3, 19, 1, on); oledRect(70, y + 8, 19, 1, on);
        oledRect(70, y + 3, 1, 6, on); oledRect(88, y + 3, 1, 6, on);
        oledRect(72, y + 5, fill, 2, on);
      }
      menuValueText(it.id, line, sizeof(line));
      oledTextRight(126, y, line, !sel);
    } else if (it.kind == MK_ENUM) {
      menuValueText(it.id, line, sizeof(line));
      oledTextRight(126, y, line, !sel);
    }
  }
}

// The speaker warning: the voice is going to the speaker, next to the microphone.
void drawWarning(uint32_t now) {
  bool blink = (now / 350) % 2 == 0;
  if (blink) { oledRect(0, 0, 128, 64, true); oledRect(2, 2, 124, 60, false); }
  else { oledRect(0, 0, 128, 1, true); oledRect(0, 63, 128, 1, true); }
  int w = 12 * oledTextLen(tx(S_WARN_TITLE));
  oledTextOn((128 - w) / 2, 2, tx(S_WARN_TITLE), 2, true);
  oledTextOn(4, 24, tx(S_WARN_1), 1, true);
  oledTextOn(4, 34, tx(S_WARN_2), 1, true);
  oledTextOn(4, 44, tx(S_WARN_3), 1, true);
  oledTextOn(4, 52, tx(S_WARN_4), 1, true);
}

// The ordinary screen: battery, register, volume, output, microphone level.
void drawStatus(uint32_t now) {
  bool usb = usbPower();
  bool charging = usb && digitalReadFast(CHG_STAT_PIN) == LOW;
  int pct = batteryPercent(batteryVolts);
  int mic = 0;
  if (micPeak.available()) mic = (int)(micPeak.read() * 8.0f);   // 0..8
  char line[40];
  snprintf(line, sizeof(line), "%s %d%%", charging ? "CHG" : (usb ? "USB" : "BAT"), pct);
  oledTextOn(0, 0, line, 2, true);
  oledTextOn(0, 20, REGISTER_NAMES[registerIndex], 2, true);
  // voice status, right of the volume line
  char vs[24] = "";
  VoiceFx &f = vfxState;
  if (f.voice || f.vocoder || f.harm || f.echo) {
    if (!micPlugged) snprintf(vs, sizeof(vs), "%s", tx(S_NO_MIC));
    else if (speakerMutesVoice()) snprintf(vs, sizeof(vs), "%s", tx(S_VOICE_OFF));
    else if (!headphones && (now / 400) % 2 == 0) snprintf(vs, sizeof(vs), "%s", tx(S_FEEDBACK));
    else if (!headphones) vs[0] = 0;
    else if (f.harmFollow && f.harm > 0 && voiceHzShown > 0) {
      static const char *const names[12] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
      int m = (int)lroundf(69.0f + 12.0f * log2f(voiceHzShown / 440.0f));
      snprintf(vs, sizeof(vs), "%s %s%d", tx(S_VOICE), names[((m % 12) + 12) % 12], m / 12 - 1);
    } else snprintf(vs, sizeof(vs), "%s%s", tx(S_VOICE), vin.isOpen() ? " *" : "");
  }
  bool showRest = resting && !vs[0];
  snprintf(line, sizeof(line), "%s %d %s%s%s", tx(S_VOL), volumeNow, headphones ? tx(S_HP) : tx(S_SPK), showRest ? " " : "",
           showRest ? tx(S_REST) : "");
  oledTextOn(0, 41, line, 1, true);
  if (vs[0]) oledTextRight(127, 41, vs, true);
  oledRect(0, 54, 82, 1, true);         // battery bar
  oledRect(0, 63, 82, 1, true);
  oledRect(0, 54, 1, 10, true);
  oledRect(81, 54, 1, 10, true);
  oledRect(2, 56, pct * 78 / 100, 6, true);
  if (!micPlugged) oledTextOn(86, 54, tx(S_NO_MIC), 1, true);
  else
  {
    oledTextOn(88, 54, tx(S_MIC), 1, true);
    oledRect(112, 56, mic * 2, 6, true);
  }
}

// Redraws (the menu and the warning quickly, the status screen 4 times a second) and, when the
// picture changed, sends it in pieces: one 16-byte piece per loop pass.
uint32_t oledHash = 0xFFFFFFFF;
void updateOled() {
  if (!oledPresent) return;
  if (oledSent < 1024) {
    if (OLED_SH1106 && (oledSent & 127) == 0) {      // a new page: page address + start column (2)
      oledCmd(0xB0 | (oledSent >> 7)); oledCmd(OLED_COL_OFFSET & 15); oledCmd(0x10 | (OLED_COL_OFFSET >> 4));
    }
    Wire.beginTransmission(OLED_ADDR);
    Wire.write(0x40);
    for (int i = 0; i < 16; i++) Wire.write(oledBuf[oledSent + i]);
    Wire.endTransmission();
    oledSent += 16;
    return;
  }
  uint32_t now = millis();
  if (speakerWarnAt) {
    oledWarnUntil = now + 4000;
    speakerWarnAt = 0;
  }
  bool warn = oledWarnUntil && (int32_t)(oledWarnUntil - now) > 0;
  if (!warn) oledWarnUntil = 0;
  bool fast = warn;
  fast |= menuOpen;
  if (now - oledDrawnAt < (fast ? 70 : 250)) return;
  oledDrawnAt = now;
  memset(oledBuf, 0, sizeof(oledBuf));
  if (warn) drawWarning(now);
  else
  if (menuOpen) drawMenu();
  else
  drawStatus(now);
  uint32_t h = 2166136261u;
  for (int i = 0; i < 1024; i++) h = (h ^ oledBuf[i]) * 16777619u;
  if (h == oledHash) return;
  oledHash = h;
  oledSent = 0;
  if (!OLED_SH1106) {
    oledCmd(0x21); oledCmd(0); oledCmd(127);   // column window
    oledCmd(0x22); oledCmd(0); oledCmd(7);     // page window
  }
}

void updateLed() {
  uint32_t now = millis();
  if (!codecOk || missingKeys > 0) setLed((now / 250) % 2 == 0, false);
  else if (!usbPower() && batteryVolts < BATTERY_LOW_V) setLed((now / 1000) % 2 == 0, false);
  else if (registerPending) setLed(false, (now / 300) % 2 == 0);
  else if (resting) setLed(false, now % 2000 < 60);
  else if (usbPower() && digitalReadFast(CHG_STAT_PIN) == LOW) setLed(true, true);
  else setLed(false, true);
}

// R1V4 5.4, item 3: run the USB port at 12 Mbit/s. The core calls this right after usb_init()
// (the line "USB1_PORTSC1 |= USB_PORTSC1_PFSC; // force 12 Mbit/sec" sits commented out at the
// end of usb_init() in Teensyduino's usb.c); the host's bus reset comes ~100 ms later. The core
// already copes with a full-speed link (usb_high_speed = 0, 64-byte MIDI packets).
extern "C" void startup_late_hook(void) {
  USB1_PORTSC1 |= USB_PORTSC1_PFSC;
}



void setup() {
  for (int i = 0; i < 2; i++) pinMode(LED_PINS[i], OUTPUT);
  powerBegin();                                  // stays on only if the click was held 2 s
  setLed(true, true);                            // orange: reading the keys
  uint32_t started = millis();
  AudioMemory(104);  // reeds + the voice chain, four shifters, tracker and FFT (see student_v04/FIRMWARE.md)
  setupKeys();

  codecOk = codec.enable();
  codec.volume(0.7f);                            // fixed: the volume knob works before the I2S output
  codec.inputSelect(AUDIO_INPUT_MIC);            // the codec's MIC input (J302 through C309)
  micLoad();                                     // R10V4: microphone type and the gain of each type
  micKind = micType == MICTYPE_DYNAMIC ? MIC_DYNAMIC : MIC_NONE;
  micPlugged = micKind != MIC_NONE;
  vfxState.micGain = micGainSlot[micSlot()];
  voiceFxBegin();                                // (ends with the codec's gain and bias)                                // all the voice effects start off
  oledSetup();
  uiLangLoad();
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
  }
  configureOscillators();

  // Synthesised accordion voice peaks at 1.56 (all four reeds): 4 voices x
  // 1.56 x 0.16 per bank, banks at 0.5 — a full chord stays under full
  // scale. The bank gains themselves are set in applyOscGains().
  engines.gain(0, 0.5f);
  engines.gain(1, 0.5f);
  engines.gain(2, 0.5f);
  engines.gain(3, 0.5f);

  setTone(110);
  room.roomsize(0.55f);
  room.damping(0.6f);
  setAmbience(ambienceNow);

  setupControls();
  applyRegister(savedRegister(), false);   // the last register kept with the selector

  usbMIDI.setHandleNoteOn(handleNoteOn);
  usbMIDI.setHandleNoteOff(handleNoteOff);
  usbMIDI.setHandleControlChange(handleControlChange);
  while (millis() - started < LED_STARTUP_MS) {
  }
  updateLed();
  scanBegin();                       // from here on the keys are read by the timer interrupt
}

void loop() {
  // Drain every pending USB MIDI message; each one calls a handler above.
  while (usbMIDI.read()) {
    lastActivityAt = millis();
  }
  drainKeyEvents();
  updateControls();
  voiceFxUpdate();
  updatePower();
  updateOled();
  updateLed();
}
