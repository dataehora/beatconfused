/* ============================================================
   eTutti Slim firmware (SPEC R8SL 8.2, gate F-1). Own sketch; the sound engine is COPIED from etutti_synth (frozen).

   Production: the Slim board's chip-down RT1062 ("Teensy 4.1 on the board"):
     arduino-cli compile --fqbn teensy:avr:teensy41:usb=midi,speed=396 etutti/firmware/slim
   Bench (no Slim board): the J's Teensy 4.0 + PJRC Audio Board Rev D. The Teensy 4.0 build switches SLIM_BANCADA on by itself:
     arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi,speed=396 etutti/firmware/slim
   (-DSLIM_BANCADA=0 / =1 forces either way.) In SLIM_BANCADA the key scan, the knobs and the power chain are replaced by simulated ones:
   an automatic pattern walks the 7 registers (then all four ranks at once) with 4..8 notes and velocities 20..127, it also plays the
   notes that arrive over USB MIDI, absent sensors are harmless (nothing is read, nothing hangs).

   Sound: accordion only. Sampled free reeds (reed_sampler.h, data reed_samples.cpp/.h: LICENSED, gitignored, never committed);
   without those two files the same sketch builds with the synthesised reed tables. 8 voices, four ranks per note (16', 8' M1, 8' M2, 4').
   Velocity = bellows pressure (accordionLevel / accordionBrightness, as in etutti_synth).

   Registers (SPEC 4, clockwise from bottom-left, 45 deg apart), CC 26 mask: 1 = 16', 2 = 8' M1, 4 = 8' M2, 8 = 4':
     1 L (Bassoon)  2 LM (Bandoneon)  3 M (Clarinet)  4 MM (Violin)  5 MH (Oboe)  6 LH (Organ)  7 H (Piccolo)

   MIDI out: notes (channel 1) with velocity, CC 7 volume and CC 26 register when the knobs change. MIDI in (any channel):
   CC 26 register, CC 14 recalibrate the keys, CC 120 / 123; SLIM_BANCADA also takes Note On/Off and CC 7.
   Keep CC 7 / 26 in step with etutti/etuttino/script.js.

   LED of the ring: COMMON ANODE (R7SL): the anodes sit on +3V3, the cathodes go to pins 13 (R) and 5 (G) through series resistors, so
   a pin LOW = lit, HIGH = dark; a pin left floating (reset, before setup()) lights nothing either (no path to ground).
   Pin map = pcb/PINOS.md (checked by check_pins.py, check_placa.py).
   ============================================================ */
#include <Audio.h>
#include <Wire.h>
#include <EEPROM.h>
#include "reed_sampler.h"

#if !defined(MIDI_INTERFACE)
#error "Choose USB Type: MIDI (usb=midi) or Serial + MIDI (usb=serialmidi)"
#endif

#ifndef SLIM_BANCADA
#if defined(ARDUINO_TEENSY40)
#define SLIM_BANCADA 1
#else
#define SLIM_BANCADA 0
#endif
#endif
#if SLIM_BANCADA
#pragma GCC diagnostic ignored "-Wunused-function"      // the real scan, knobs and EEPROM are compiled but unused on the bench
#pragma GCC diagnostic ignored "-Wunused-variable"
#endif
#ifndef SLIM_BENCH_PRINT            // measuring build: prints CPU, audio memory and output peak on the serial port (usb=serialmidi)
#define SLIM_BENCH_PRINT 0
#endif
#if SLIM_BENCH_PRINT && !defined(USB_MIDI_SERIAL)
#error "SLIM_BENCH_PRINT prints on the serial port: build with usb=serialmidi"
#endif

// ---------------------------------------------------------------- pins (Teensy 4.1 numbers)
#define PIN_CHG_STAT   0     // ~CHG of the BQ24075 (low = charging)
#define PIN_PGOOD_N    1     // ~PGOOD of the BQ24075 (low = USB present)
#define PIN_SCAN_DATA  2
#define PIN_SCAN_CLK   3
#define PIN_SCAN_LATCH 4
#define PIN_LED_G      5     // common anode: LOW = lit
#define PIN_KILL       10    // pulse high: resets the power latch (auto-off)
#define PIN_SET        6     // pulse high: sets the power latch
#define PIN_KNOB_N     25    // low = volume knob out of OFF (Hall switch, inverted by Q209)
#define PIN_LED_R      13    // common anode: LOW = lit
#define PIN_VBAT_S     16    // VBAT / 2
#define TMAG_REG_ADDR 0x35   // TMAG5273A2: register knob
#define TMAG_VOL_ADDR 0x22   // TMAG5273B2: volume knob
static const uint8_t PIN_OUT[4] = {14, 15, 26, 27};   // analog line of rows 1..4

// ---------------------------------------------------------------- keyboard (SPEC 1): rows x 8 keys, MIDI notes (C4 = 60)
#define NROWS 4
#define NCOLS 8
static const uint8_t NOTE[NROWS][NCOLS] = {
  {57, 60, 63, 66, 69, 72, 75, 78},   // row 1: A3 C4 D#4 F#4 A4 C5 D#5 F#5
  {55, 58, 61, 64, 67, 70, 73, 76},   // row 2: G3 A#3 C#4 E4 G4 A#4 C#5 E5
  {56, 59, 62, 65, 68, 71, 74, 77},   // row 3: G#3 B3 D4 F4 G#4 B4 D5 F5
  {54, 57, 60, 63, 66, 69, 72, 75},   // row 4: F#3 A3 C4 D#4 F#4 A4 C5 D#5
};
#define T_ON_US     60       // TMAG5253BA3 turn-on 20 us typ / 45 us max, plus ADC settling
#define ADC_BITS    12
#define NOTE_ON_AT  0.45f    // travel fractions (same model as the eTuttino)
#define NOTE_OFF_AT 0.30f
#define VEL_START   0.12f
#define FAST_MS     1.0f     // 1 ms = velocity 127
#define SLOW_MS     80.0f    // 80 ms = velocity 1
// Field model: reading deviation from rest ~ B; dipole B ~ 1/d^3; datasheet fluxes 75 Gs (rest) .. 680 Gs (bottom).
#define COUNTS_PER_GS 1.86f  // 1.5 mV/Gs * 4096 / 3.3 V (estimate; the bottom of each key is learnt)
#define REST_GS     75.0f
#define BOTTOM_GS   680.0f

struct Key {
  float rest;        // raw reading at rest (measured at boot)
  float bottom;      // deviation at the bottom of the travel (counts from rest), learnt, kept in EEPROM
  uint32_t tStart;   // micros when the travel crossed VEL_START going down
  bool armed, on, present;
};
static Key keys[NROWS][NCOLS];
static uint16_t rawNow[NROWS][NCOLS];
static uint8_t noteHolders[128];                 // row 4 doubles row 1: a note starts on the first key down and stops on the last up

// travel fraction 0..1 from the deviation (counts): d ~ B(z) = k / (z + z0)^3, normalised so rest = 0, bottom = 1
static float travel(const Key &k, float dev) {
  float bRest = REST_GS * COUNTS_PER_GS;
  float sRest = 1.0f / cbrtf(bRest), sNow = 1.0f / cbrtf(bRest + dev), sBot = 1.0f / cbrtf(bRest + k.bottom);
  float t = (sRest - sNow) / (sRest - sBot);
  return t < 0 ? 0 : (t > 1.2f ? 1.2f : t);
}

// ---------------------------------------------------------------- scan: one 1 walks through the 595 chain (DATA = 1 only at the first pulse)
static inline void pulse(uint8_t pin) { digitalWriteFast(pin, HIGH); delayNanoseconds(40); digitalWriteFast(pin, LOW); }
static void scanClear() {                       // 8 pulses with DATA = 0 clear the chain; the 9th is spare
  digitalWriteFast(PIN_SCAN_DATA, LOW);
  for (int i = 0; i < NCOLS + 1; i++) pulse(PIN_SCAN_CLK);
  pulse(PIN_SCAN_LATCH);
}
static void scanStep(int col) {                 // enable column `col` (0 = first key of every ruler)
  digitalWriteFast(PIN_SCAN_DATA, col == 0 ? HIGH : LOW);
  pulse(PIN_SCAN_CLK);
  pulse(PIN_SCAN_LATCH);
}
static void readColumn(int col) {
  delayMicroseconds(T_ON_US);
  for (int r = 0; r < NROWS; r++) rawNow[r][col] = analogRead(PIN_OUT[r]);
}
static void scanFrame() {
  for (int c = 0; c < NCOLS; c++) { scanStep(c); readColumn(c); }
  scanClear();
}

// ---------------------------------------------------------------- audio graph (the eTuttino's accordion, copied)
const int NUM_VOICES = 8;
enum { REED_16, REED_M1, REED_M2, REED_4, NUM_REEDS };
AudioSynthWaveform       reed[NUM_REEDS][NUM_VOICES];   // synthesised reeds: only used without reed_samples.cpp
AudioMixer4              reedMix[NUM_VOICES];
ReedSampler              reedSmp[NUM_VOICES];           // sampled reeds, four ranks per voice
AudioMixer4              voiceMix[NUM_VOICES];
const bool HAVE_REED_SAMPLES = REED_SAMPLES_PER_RANK > 0;
AudioEffectEnvelope      bellows[NUM_VOICES];
AudioMixer4              accA, accB, engines;
AudioEffectFreeverb      room;
AudioMixer4              master;                        // dry, reverb
AudioOutputI2S           i2sOut;
AudioControlSGTL5000     codec;
#if SLIM_BENCH_PRINT
AudioAnalyzePeak         outPeak;
AudioConnection          ppk(master, 0, outPeak, 0);
#endif

#define REED_PATCH(v) \
  AudioConnection pr16_##v(reed[REED_16][v], 0, reedMix[v], 0); \
  AudioConnection prM1_##v(reed[REED_M1][v], 0, reedMix[v], 1); \
  AudioConnection prM2_##v(reed[REED_M2][v], 0, reedMix[v], 2); \
  AudioConnection pr4_##v(reed[REED_4][v], 0, reedMix[v], 3); \
  AudioConnection pm_##v(reedMix[v], 0, voiceMix[v], 0); \
  AudioConnection pq_##v(reedSmp[v], 0, voiceMix[v], 1); \
  AudioConnection pb_##v(voiceMix[v], bellows[v]);
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
AudioConnection pd(engines, 0, master, 0);              // dry
AudioConnection pv(engines, 0, room, 0);
AudioConnection pw(room, 0, master, 1);                 // reverb
AudioConnection pl(master, 0, i2sOut, 0);
AudioConnection pr(master, 0, i2sOut, 1);

// Reed waveforms for the synthesised fallback (additive, band-limited; never raw saw/square).
static int16_t tableOpen[256], tableCassotto[256], tablePiccolo[256];
static int16_t tableOpenHigh[256], tableCassottoHigh[256], tablePiccoloHigh[256];
static const int HIGH_TABLE_FROM = 73;          // sounding notes above C5 use tables with fewer harmonics (no aliasing)
static void buildReedTable(int16_t *table, int harmonics, float rolloff, float ripple) {
  float buf[256], peak = 0;
  for (int i = 0; i < 256; i++) buf[i] = 0;
  for (int n = 1; n <= harmonics; n++) {
    float amp = powf((float)n, -rolloff) * (1.0f + ripple * cosf(n * 1.3f));
    float phase = 0.7f * n * n;
    for (int i = 0; i < 256; i++) buf[i] += amp * sinf(2.0f * PI * n * i / 256.0f + phase);
  }
  for (int i = 0; i < 256; i++) peak = max(peak, fabsf(buf[i]));
  for (int i = 0; i < 256; i++) table[i] = (int16_t)(buf[i] / peak * 30000.0f);
}

struct Voice { int note; unsigned long age; };
static Voice voices[NUM_VOICES];
static unsigned long voiceCounter = 0;
static uint8_t registerMask = 0b0110;            // bit0 16', bit1 8' M1, bit2 8' M2, bit3 4'
static const float wetCents = 0;                 // tremolo off (the classic dry MM); CC 27 is not used by the Slim
static float reedGain[NUM_REEDS] = {0.42f, 0.42f, 0.42f, 0.30f};
// Rank balance of the sampled reeds (the samples are stored at one loudness; the four together stay under full scale).
static const float SAMPLED_REED_GAIN[NUM_REEDS] = {0.30f, 0.30f, 0.30f, 0.22f};
static const float BANK_GAIN = 0.16f, SAMPLED_BANK_GAIN = 0.80f;
static const float ATTACK_MS = 24.0f, RELEASE_MS = 82.0f;     // = the eTuttino's CC 73 = 14, CC 72 = 21
static byte ambience = 25;

// Velocity stands for the bellows pressure: 24 dB of loudness, plus (sampled reeds) a low-pass from 700 Hz to 16 kHz, never under 3x the note.
static const float ACCORDION_DYNAMIC_DB = 24.0f;
static float noteToFreq(float note) { return 440.0f * powf(2.0f, (note - 69.0f) / 12.0f); }
static float accordionLevel(byte velocity) { return powf(10.0f, -ACCORDION_DYNAMIC_DB / 20.0f * (1.0f - velocity / 127.0f)); }
static float accordionBrightness(byte velocity, int note) { return max(700.0f * powf(2.0f, 4.5f * velocity / 127.0f), 3.0f * noteToFreq(note)); }

static void tuneVoice(int v, int note) {         // synthesised fallback
  reed[REED_16][v].arbitraryWaveform(note - 12 >= HIGH_TABLE_FROM ? tableCassottoHigh : tableCassotto, 16000.0f);
  reed[REED_M1][v].arbitraryWaveform(note >= HIGH_TABLE_FROM ? tableOpenHigh : tableOpen, 16000.0f);
  reed[REED_M2][v].arbitraryWaveform(note >= HIGH_TABLE_FROM ? tableCassottoHigh : tableCassotto, 16000.0f);
  reed[REED_4][v].arbitraryWaveform(note + 12 >= HIGH_TABLE_FROM ? tablePiccoloHigh : tablePiccolo, 16000.0f);
  reed[REED_16][v].frequency(noteToFreq(note - 12));
  reed[REED_M1][v].frequency(noteToFreq(note));
  reed[REED_M2][v].frequency(noteToFreq(note + wetCents / 100.0f));
  reed[REED_4][v].frequency(noteToFreq(note + 12));
}
static void applyGains() {
  for (int v = 0; v < NUM_VOICES; v++)
    for (int r = 0; r < NUM_REEDS; r++) {
      bool on = registerMask & (1 << r);
      reedMix[v].gain(r, on ? reedGain[r] : 0.0f);
      reedSmp[v].gain(r, on ? SAMPLED_REED_GAIN[r] : 0.0f);
    }
  for (int ch = 0; ch < 4; ch++) {
    accA.gain(ch, HAVE_REED_SAMPLES ? SAMPLED_BANK_GAIN : BANK_GAIN);
    accB.gain(ch, HAVE_REED_SAMPLES ? SAMPLED_BANK_GAIN : BANK_GAIN);
  }
}
static void setRegister(uint8_t mask) {
  registerMask = mask & 0x0F;
  AudioNoInterrupts(); applyGains(); AudioInterrupts();
}
static void setAmbience(byte value) {
  float wet = value / 127.0f;
  master.gain(0, 1.0f - 0.35f * wet);
  master.gain(1, 0.6f * wet);
}
static bool voiceBusy(int i) { return bellows[i].isActive(); }
static int findVoiceForNote(int note) {
  for (int i = 0; i < NUM_VOICES; i++) if (voices[i].note == note) return i;
  for (int i = 0; i < NUM_VOICES; i++) if (voices[i].note < 0 && !voiceBusy(i)) return i;
  int oldest = 0; bool oldestReleasing = false;
  for (int i = 0; i < NUM_VOICES; i++) {
    bool releasing = voices[i].note < 0;
    if ((releasing && !oldestReleasing) || (releasing == oldestReleasing && voices[i].age < voices[oldest].age)) { oldest = i; oldestReleasing = releasing; }
  }
  return oldest;
}
static void soundOn(int note, int velocity) {
  int v = findVoiceForNote(note);
  voices[v].note = note; voices[v].age = ++voiceCounter;
  float amp = accordionLevel(velocity);
  AudioNoInterrupts();
  if (HAVE_REED_SAMPLES) reedSmp[v].noteOn(note, wetCents, amp, accordionBrightness(velocity, note));
  else { tuneVoice(v, note); for (int r = 0; r < NUM_REEDS; r++) reed[r][v].amplitude(amp); }
  bellows[v].noteOn();
  AudioInterrupts();
}
static void soundOff(int note) {
  for (int i = 0; i < NUM_VOICES; i++)
    if (voices[i].note == note) { bellows[i].noteOff(); reedSmp[i].noteOff(RELEASE_MS); voices[i].note = -1; }
}
static void allSoundOff() {
  AudioNoInterrupts();
  for (int i = 0; i < NUM_VOICES; i++) {
    for (int r = 0; r < NUM_REEDS; r++) reed[r][i].amplitude(0);
    reedSmp[i].stop(); bellows[i].noteOff(); voices[i].note = -1;
  }
  AudioInterrupts();
  memset(noteHolders, 0, sizeof noteHolders);
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) keys[r][c].on = keys[r][c].armed = false;
}
static bool anyNoteDown() { for (int i = 0; i < NUM_VOICES; i++) if (voices[i].note >= 0) return true; return false; }

// A key goes down / up (real or simulated): sound + MIDI out.
static uint32_t lastActivity = 0;
static void keyDown(int note, int vel) {
  if (noteHolders[note]++ == 0) { usbMIDI.sendNoteOn(note, vel, 1); soundOn(note, vel); }
  lastActivity = millis();
}
static void keyUp(int note) {
  if (noteHolders[note] && --noteHolders[note] == 0) { usbMIDI.sendNoteOff(note, 0, 1); soundOff(note); }
  lastActivity = millis();
}

// ---------------------------------------------------------------- registers: 7 positions
static const uint8_t REG_MASK[7] = {0b0001, 0b0011, 0b0010, 0b0110, 0b1010, 0b1001, 0b1000};  // L, LM, M, MM, MH, LH, H
static const char *const REG_NAME[7] = {"L Bassoon", "ML Bandoneon", "M Clarinet", "MM Violin", "MH Oboe", "LH Organ", "H Piccolo"};
static int regPos = 3;                           // MM (the classic accordion) until the knob or the EEPROM says otherwise

// ---------------------------------------------------------------- EEPROM: register position + the learnt bottom of every key
#define EE_MAGIC  0xE7570001u                    // bump when the key count or order changes
#define EE_ADDR_MAGIC 0
#define EE_ADDR_REG   4
#define EE_ADDR_BOT   8
static bool bottomsDirty = false;
static uint32_t bottomsChangedAt = 0;
static bool eeValid() { uint32_t m; EEPROM.get(EE_ADDR_MAGIC, m); return m == EE_MAGIC; }
static void eeLoad() {
  if (!eeValid()) return;
  uint8_t p = EEPROM.read(EE_ADDR_REG);
  if (p < 7) regPos = p;
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) {
    float b; EEPROM.get(EE_ADDR_BOT + 4 * (r * NCOLS + c), b);
    if (b > 20.0f && b < 4000.0f) keys[r][c].bottom = b;
  }
}
static void eeInit() { if (!eeValid()) { EEPROM.put(EE_ADDR_MAGIC, (uint32_t)EE_MAGIC); EEPROM.write(EE_ADDR_REG, regPos); } }
static void eeSaveReg() { eeInit(); EEPROM.update(EE_ADDR_REG, regPos); }
static void eeSaveBottoms() {
  eeInit();
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) EEPROM.put(EE_ADDR_BOT + 4 * (r * NCOLS + c), keys[r][c].bottom);   // put() writes only changed bytes
  bottomsDirty = false;
}

// ---------------------------------------------------------------- knobs: two TMAG5273 angle sensors (I2C), magnet on the knob stem
// Registers: 7 absolute positions every 45 deg, clockwise from bottom-left, with hysteresis; the zone between 7 and 1 keeps the last one.
// Volume: continuous angle between the OFF click and the end stop. REG_A0 / VOL_A_* are the sensor-frame angles of those mechanical points:
// set with the first knob (the sensor frame depends on how the chip sits). Defaults below are placeholders.
#define REG_A0       225.0f   // sensor angle of position 1 (deg)
#define REG_HYST     8.0f     // a new position needs to be within 22.5 - REG_HYST deg of its centre
#define VOL_A_MIN    40.0f    // sensor angle just after the OFF click (volume 0)
#define VOL_A_MAX    300.0f   // end stop (volume 1)
static bool tmagOk[2] = {false, false};
static uint32_t tmagRetryAt = 0;
static bool tmagWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr); Wire.write(reg); Wire.write(val); return Wire.endTransmission() == 0;
}
static bool tmagInit(uint8_t addr) {
  bool ok = tmagWrite(addr, 0x02, 0x30);        // SENSOR_CONFIG_1: MAG_CH_EN = X and Y
  ok &= tmagWrite(addr, 0x03, 0x07);            // SENSOR_CONFIG_2: ANGLE_EN = X 1st, Y 2nd; +-266 mT range (the magnet gives 80-150 mT at the die)
  ok &= tmagWrite(addr, 0x01, 0x02);            // DEVICE_CONFIG_2: continuous measure (~2.3 mA); wake-and-sleep (mode 3) is a later saving
  return ok;
}
static bool tmagAngle(uint8_t addr, float &deg) {   // ANGLE_RESULT_MSB/LSB at 0x19/0x1A: 13 bits, 4 fractional (xxxx/16)
  Wire.beginTransmission(addr); Wire.write(0x19);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)addr, 2) != 2) return false;
  uint16_t v = (Wire.read() << 8); v |= Wire.read();
  deg = (v & 0x1FFF) / 16.0f;
  return true;
}
static void updateRegister() {
  float a;
  if (!tmagOk[0] || !tmagAngle(TMAG_REG_ADDR, a)) return;
  float rel = fmodf(a - REG_A0 + 720.0f, 360.0f);                 // clockwise from position 1
  int p = (int)((rel + 22.5f) / 45.0f);
  if (p > 6) return;                                              // dead zone between 7 and 1: keep the last one
  float off = rel - 45.0f * p;
  if (p != regPos && fabsf(off) <= 22.5f - REG_HYST) {            // hysteresis
    regPos = p; setRegister(REG_MASK[p]); eeSaveReg();
    usbMIDI.sendControlChange(26, registerMask, 1);
    lastActivity = millis();
  }
}
static float volSm = 0;
static bool readVolume(float &out) {
  float a;
  if (!tmagOk[1] || !tmagAngle(TMAG_VOL_ADDR, a)) return false;
  float rel = fmodf(a - VOL_A_MIN + 720.0f, 360.0f);
  float x = rel / (VOL_A_MAX - VOL_A_MIN);
  if (rel > 330.0f) x = 0;                                        // just before the OFF click: the sensor wraps, treat as 0
  x = x < 0 ? 0 : (x > 1 ? 1 : x);
  volSm += 0.2f * (x - volSm);
  out = volSm;
  return true;
}

// ---------------------------------------------------------------- battery, knob, power
#if SLIM_BANCADA
static float batteryV() { return 3.9f; }
static bool knobOn() { return true; }
static bool usbPresent() { return true; }
static bool charging() { return false; }
static void pulsePin(uint8_t, uint32_t) {}       // no latch on the bench: never touch the pins
#else
static float batteryV() { return analogRead(PIN_VBAT_S) * 3.3f / 4095.0f * 2.0f; }
static bool knobOn() { return digitalRead(PIN_KNOB_N) == LOW; }   // Hall switch: low = knob out of OFF
static bool usbPresent() { return digitalRead(PIN_PGOOD_N) == LOW; }
static bool charging() { return digitalRead(PIN_CHG_STAT) == LOW; }
static void pulsePin(uint8_t pin, uint32_t ms) { digitalWrite(pin, HIGH); delay(ms); digitalWrite(pin, LOW); }
#endif
static uint32_t bootMs = 0, lowSince = 0;
static bool softOff = false;                     // knob OFF with the cable in: silent, charging, MIDI still alive
static bool rulerFault = false;

// ---------------------------------------------------------------- LED (R/G, orange = both), COMMON ANODE: pin LOW = lit
static void led(bool r, bool g) { digitalWriteFast(PIN_LED_R, r ? LOW : HIGH); digitalWriteFast(PIN_LED_G, g ? LOW : HIGH); }
static bool codecOk = false;
static void updateLed(uint32_t now) {
  bool sensorFault = !codecOk || rulerFault || (!SLIM_BANCADA && !(tmagOk[0] && tmagOk[1]));
  if (sensorFault) { led((now / 150) & 1, false); return; }                                            // fast red: codec, ruler or knob sensor silent
  if (batteryV() < 3.45f && !usbPresent()) { led(((now / 1000) % 3) == 0, false); return; }            // slow red: low battery
  if (now - bootMs < 600) { led(true, true); return; }                                                 // orange: reading the keys at start
  if (usbPresent() && charging()) { led(true, true); return; }                                         // orange: charging
  if (softOff) { led(false, usbPresent() && !charging()); return; }                                    // cable, knob off: green when full
  if (anyNoteDown()) { led(false, true); return; }                                                     // green: playing
  led(false, (now % 2000) < 60);                                                                       // short green every 2 s at rest
}

// ---------------------------------------------------------------- key processing (real scan)
static void processKeys() {
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) {
    Key &k = keys[r][c];
    if (!k.present) continue;
    float dev = fabsf((float)rawNow[r][c] - k.rest);
    if (dev > 0.6f * k.bottom && dev > k.bottom * 1.02f && dev < 4000) { k.bottom = dev; bottomsDirty = true; bottomsChangedAt = millis(); }   // learn the bottom
    float t = travel(k, dev);
    uint32_t us = micros();
    if (!k.on) {
      if (t >= VEL_START && !k.armed) { k.armed = true; k.tStart = us; }
      if (t < VEL_START * 0.5f) k.armed = false;
      if (k.armed && t >= NOTE_ON_AT) {
        float ms = (us - k.tStart) / 1000.0f;
        if (ms < FAST_MS) ms = FAST_MS;
        float x = logf(ms / FAST_MS) / logf(SLOW_MS / FAST_MS);
        if (x > 1) x = 1;
        int vel = 127 - (int)(126.0f * x);
        k.on = true; k.armed = false;
        keyDown(NOTE[r][c], vel);
      }
    } else if (t <= NOTE_OFF_AT) {
      k.on = false;
      keyUp(NOTE[r][c]);
    }
  }
}

static void calibrateRest() {                    // every key at rest at power-up: 16 frames averaged
  static float acc[NROWS][NCOLS];
  memset(acc, 0, sizeof acc);
  for (int f = 0; f < 16; f++) { scanFrame(); for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) acc[r][c] += rawNow[r][c]; }
  int alive = 0;
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) {
    Key &k = keys[r][c];
    k.rest = acc[r][c] / 16.0f;
    k.present = k.rest > 100 && k.rest < 4000;   // a rail reading = no sensor on the line
    k.on = k.armed = false;
    alive += k.present;
  }
  rulerFault = alive < NROWS * NCOLS;            // any silent sensor: fast red (SPEC 4)
}
static void defaultBottoms() { for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) keys[r][c].bottom = (BOTTOM_GS - REST_GS) * COUNTS_PER_GS; }
static bool recalRequested = false;

// ---------------------------------------------------------------- bench: simulated keys and knob (SLIM_BANCADA)
#if SLIM_BANCADA
// Segments of BENCH_SEG_MS: the 7 registers in knob order, then the 8th = all four ranks at once (worst case for the CPU).
// Inside a segment, an arpeggio of 4 notes (velocity 30..127) and then 4 more together: 8 notes at once.
#define BENCH_SEG_MS 7000
static const uint8_t BENCH_NOTE[8] = {55, 62, 69, 76, 57, 64, 71, 78};
static const uint8_t BENCH_VEL[8]  = {30, 70, 110, 127, 20, 60, 95, 127};
static int benchSeg = -1;
static bool benchOn[8];
static uint32_t benchT0 = 0;
static bool benchStarted = false;
static void benchTick(uint32_t now) {
  if (!benchStarted) { benchStarted = true; benchT0 = now; benchSeg = -1; }
  uint32_t t = now - benchT0;
  int seg = (t / BENCH_SEG_MS) % 8;
  uint32_t u = t % BENCH_SEG_MS;
  if (seg != benchSeg) {                         // the "knob" moves to the next register
    for (int i = 0; i < 8; i++) if (benchOn[i]) { benchOn[i] = false; keyUp(BENCH_NOTE[i]); }
    benchSeg = seg;
    if (seg < 7) { regPos = seg; setRegister(REG_MASK[seg]); } else { regPos = -1; setRegister(0b1111); }
    usbMIDI.sendControlChange(26, registerMask, 1);
  }
  for (int i = 0; i < 8; i++) {
    uint32_t on = i < 4 ? 400 + 500 * i : 3000 + 400 * (i - 4);
    bool want = u >= on && u < 6200;
    if (want && !benchOn[i]) { benchOn[i] = true; keyDown(BENCH_NOTE[i], BENCH_VEL[i]); }
    if (!want && benchOn[i]) { benchOn[i] = false; keyUp(BENCH_NOTE[i]); }
  }
}
#endif

// ---------------------------------------------------------------- MIDI in
static void onCC(byte ch, byte cc, byte val) {
  (void)ch;
  if (cc == 26) { setRegister(val); }
  else if (cc == 14 && val >= 64) recalRequested = true;       // forget the learnt bottoms and the rest, learn again
  else if (cc == 120) allSoundOff();
  else if (cc == 123) { for (int i = 0; i < NUM_VOICES; i++) { bellows[i].noteOff(); reedSmp[i].noteOff(RELEASE_MS); voices[i].note = -1; } }
#if SLIM_BANCADA
  else if (cc == 7) codec.volume(0.8f * val / 127.0f);
#endif
}
#if SLIM_BANCADA
static void onNoteOn(byte ch, byte note, byte vel) { (void)ch; if (vel == 0) keyUp(note); else keyDown(note, vel); }
static void onNoteOff(byte ch, byte note, byte vel) { (void)ch; (void)vel; keyUp(note); }
#endif

// USB at 12 Mbit/s, forced (SPEC 4: the 30-35 mm pair is not controlled-impedance). The core calls this hook 300 ms after usb_init()
// (core 1.62: 20 ms + 280 ms of delay); by then a host has long finished its first reset and the port runs at High Speed, so setting
// PFSC alone changes nothing (measured on the bench: PSPD still 2 = High Speed). The hook therefore does a soft disconnect (RS = 0),
// sets PFSC and reconnects: the host enumerates again, now at 12 Mbit/s (64-byte MIDI packets, which the core handles).
// The device shows up twice on the bus during the first ~0.4 s; the Student V4 sketch's plain "PFSC |= " is not enough.
extern "C" void startup_late_hook(void) {
  USB1_USBCMD &= ~USB_USBCMD_RS;
  USB1_PORTSC1 |= USB_PORTSC1_PFSC;
  uint32_t t = millis();
  while (millis() - t < 60) {}
  USB1_USBCMD |= USB_USBCMD_RS;
}

void setup() {
#if !SLIM_BANCADA
  pinMode(PIN_KILL, OUTPUT); digitalWrite(PIN_KILL, LOW);
  pinMode(PIN_SET, OUTPUT); digitalWrite(PIN_SET, LOW);
  pinMode(PIN_KNOB_N, INPUT);
  pinMode(PIN_CHG_STAT, INPUT); pinMode(PIN_PGOOD_N, INPUT);
  pinMode(PIN_SCAN_DATA, OUTPUT); pinMode(PIN_SCAN_CLK, OUTPUT); pinMode(PIN_SCAN_LATCH, OUTPUT);
  digitalWriteFast(PIN_SCAN_CLK, LOW); digitalWriteFast(PIN_SCAN_LATCH, LOW);
  analogReadResolution(ADC_BITS);
  analogReadAveraging(1);
#endif
  digitalWrite(PIN_LED_R, HIGH); digitalWrite(PIN_LED_G, HIGH);   // common anode: HIGH = dark; set the level before the pin becomes an output
  pinMode(PIN_LED_R, OUTPUT); pinMode(PIN_LED_G, OUTPUT);
  bootMs = millis();
  led(true, true);
  AudioMemory(60);                               // measured peak: 8 blocks with sampled reeds (32 with the synthesised ones: see FIRMWARE.md)
  Wire.begin(); Wire.setClock(400000);
#if !SLIM_BANCADA
  if (knobOn()) pulsePin(PIN_SET, 10);           // started from USB with the knob already on: arm the latch so the battery takes over when the cable goes
  tmagOk[0] = tmagInit(TMAG_REG_ADDR); tmagOk[1] = tmagInit(TMAG_VOL_ADDR);
#endif
  codecOk = codec.enable();                      // I2C 0x0A; false if the codec does not answer
  codec.volume(0.0f);
  buildReedTable(tableOpen, 20, 1.05f, 0.25f);
  buildReedTable(tableCassotto, 14, 1.85f, 0.20f);
  buildReedTable(tablePiccolo, 10, 1.20f, 0.20f);
  buildReedTable(tableOpenHigh, 12, 1.05f, 0.25f);
  buildReedTable(tableCassottoHigh, 12, 1.85f, 0.20f);
  buildReedTable(tablePiccoloHigh, 6, 1.20f, 0.20f);
  const int16_t *tables[NUM_REEDS] = {tableCassotto, tableOpen, tableCassotto, tablePiccolo};
  for (int v = 0; v < NUM_VOICES; v++) {
    voices[v].note = -1; voices[v].age = 0;
    for (int r = 0; r < NUM_REEDS; r++) { reed[r][v].arbitraryWaveform(tables[r], 16000.0f); reed[r][v].begin(0.0f, 440.0f, WAVEFORM_ARBITRARY); }
    bellows[v].attack(ATTACK_MS); bellows[v].hold(0); bellows[v].decay(0); bellows[v].sustain(1.0f); bellows[v].release(RELEASE_MS);
    voiceMix[v].gain(0, 1.0f); voiceMix[v].gain(1, 1.0f);
  }
  engines.gain(0, 0.5f); engines.gain(1, 0.5f);
  room.roomsize(0.55f); room.damping(0.6f);
  setAmbience(ambience);
  defaultBottoms();
#if !SLIM_BANCADA
  eeLoad();
#endif
  setRegister(REG_MASK[regPos < 0 ? 3 : regPos]);
  usbMIDI.setHandleControlChange(onCC);
#if SLIM_BANCADA
  usbMIDI.setHandleNoteOn(onNoteOn); usbMIDI.setHandleNoteOff(onNoteOff);
  codec.volume(0.35f);                           // bench: moderate fixed volume (CC 7 changes it)
#else
  scanClear();
  calibrateRest();
#endif
#if SLIM_BENCH_PRINT
  Serial.begin(115200);
#endif
  lastActivity = millis();
}

#if SLIM_BENCH_PRINT
static void benchPrint(uint32_t now) {
  static uint32_t last = 0;
  static float peakSeg = 0;
  float pk = outPeak.available() ? outPeak.read() : 0;
  if (pk > peakSeg) peakSeg = pk;
  if (now - last < 1000) return;
  last = now;
  int regIdx = regPos;
  Serial.printf("t=%lus seg=%d reg=%s mask=%X cpu=%.1f/%.1f mem=%d/%d peak=%.3f(seg max %.3f) usbspeed=%d eeprom=%u samples=%d\n",
                (unsigned long)(now / 1000),
#if SLIM_BANCADA
                benchSeg,
#else
                0,
#endif
                regIdx >= 0 ? REG_NAME[regIdx] : "ALL 4 ranks", registerMask,
                AudioProcessorUsage(), AudioProcessorUsageMax(), AudioMemoryUsage(), AudioMemoryUsageMax(), pk, peakSeg,
                (int)((USB1_PORTSC1 >> 26) & 3), (unsigned)EEPROM.length(), (int)REED_SAMPLES_PER_RANK);
  peakSeg = 0;
}
#endif

void loop() {
  uint32_t now = millis();
  while (usbMIDI.read()) {}
#if SLIM_BANCADA
  benchTick(now);
#else
  scanFrame();
  processKeys();
  if (recalRequested && !anyNoteDown()) { recalRequested = false; defaultBottoms(); calibrateRest(); bottomsDirty = true; bottomsChangedAt = now; }
  if (bottomsDirty && now - bottomsChangedAt > 5000 && !anyNoteDown()) eeSaveBottoms();   // flash is written only after the playing stops
#endif
  static uint32_t slow = 0;
  if (now - slow >= 20) {                        // 50 Hz: knobs, power, LED
    slow = now;
#if !SLIM_BANCADA
    if (!(tmagOk[0] && tmagOk[1]) && now > tmagRetryAt) {   // an absent sensor is retried once a second, never blocks
      tmagRetryAt = now + 1000;
      if (!tmagOk[0]) tmagOk[0] = tmagInit(TMAG_REG_ADDR);
      if (!tmagOk[1]) tmagOk[1] = tmagInit(TMAG_VOL_ADDR);
    }
    updateRegister();
    float v = volSm;
    if (readVolume(v)) {
      int cc = (int)(v * 127.0f + 0.5f);
      static int lastCC = -1;
      if (cc != lastCC) { if (lastCC >= 0) lastActivity = now; lastCC = cc; usbMIDI.sendControlChange(7, cc, 1); }
    }
    bool on = knobOn(), usb = usbPresent();
    softOff = usb && !on;
    if (codecOk) codec.volume(softOff ? 0.0f : v * 0.8f);
    if (!on) allSoundOff();
    // power: the Hall switch drops the battery path in hardware when the knob goes to OFF. The firmware only handles the automatic switch-off.
    bool idle = !usb && (now - lastActivity > 15UL * 60UL * 1000UL);
    if (batteryV() < 3.3f && !usb) { if (!lowSince) lowSince = now; } else lowSince = 0;
    bool empty = lowSince && (now - lowSince > 5000);
    if ((idle || empty) && !usb) { allSoundOff(); codec.volume(0); pulsePin(PIN_KILL, 50); }   // resets the latch: SYSOFF is released, the battery is disconnected, the board dies
#endif
    updateLed(now);
  }
#if SLIM_BENCH_PRINT
  benchPrint(now);
#endif
  usbMIDI.send_now();
}
