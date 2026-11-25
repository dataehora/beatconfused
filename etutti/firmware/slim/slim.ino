// eTutti Slim (SPEC R2SL, stage 1): own sketch, Teensy 4.1 (the board's RT1062 chip-down runs the Teensy 4.1 core).
//   arduino-cli compile --fqbn teensy:avr:teensy41:usb=midi,speed=396 etutti/firmware/slim
// Independent of the Student V4 sketch. Stage-1 scope: pins, 32-key scan, key model + velocity, 7 registers, continuous volume,
// LED states, power logic (latch SET/KILL, Hall OFF switch, auto-off, battery), forced USB Full Speed, USB MIDI "eTutti". The sound engine is a placeholder (8 simple voices):
// the accordion engine (sampled reeds, licensed data) is NOT copied here; it comes in a later step.
// Pin map = pcb/PINOS.md (checked by check_pins.py).
#include <Audio.h>
#include <Wire.h>

#if !defined(USB_MIDI)
#error "Choose USB Type: MIDI (usb=midi)"
#endif

// ---------------------------------------------------------------- pins (Teensy 4.1 numbers)
#define PIN_CHG_STAT   0     // ~CHG of the BQ24075 (low = charging)
#define PIN_PGOOD_N    1     // ~PGOOD of the BQ24075 (low = USB present)
#define PIN_SCAN_DATA  2
#define PIN_SCAN_CLK   3
#define PIN_SCAN_LATCH 4
#define PIN_LED_G      5
#define PIN_KILL       10    // pulse high: resets the power latch (auto-off)
#define PIN_SET        6     // pulse high: sets the power latch
#define PIN_KNOB_N     25    // low = volume knob out of OFF (Hall switch, inverted by Q209)
#define PIN_LED_R      13
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
#define NOTE_ON_AT  0.45f    // travel fractions (same model as the V4 sketch)
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
  float bottom;      // deviation at the bottom of the travel (counts from rest), learnt
  uint32_t tStart;   // micros when the travel crossed VEL_START going down
  bool armed, on, present;
};
static Key keys[NROWS][NCOLS];
static uint16_t rawNow[NROWS][NCOLS];

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

// ---------------------------------------------------------------- audio (placeholder engine) + codec
AudioSynthWaveform voice[8];
AudioMixer4 mixA, mixB, mixOut;
AudioOutputI2S i2sOut;
AudioConnection c0(voice[0], 0, mixA, 0), c1(voice[1], 0, mixA, 1), c2(voice[2], 0, mixA, 2), c3(voice[3], 0, mixA, 3);
AudioConnection c4(voice[4], 0, mixB, 0), c5(voice[5], 0, mixB, 1), c6(voice[6], 0, mixB, 2), c7(voice[7], 0, mixB, 3);
AudioConnection c8(mixA, 0, mixOut, 0), c9(mixB, 0, mixOut, 1);
AudioConnection c10(mixOut, 0, i2sOut, 0), c11(mixOut, 0, i2sOut, 1);
AudioControlSGTL5000 codec;
static bool codecOk = false;
static int8_t voiceNote[8] = {-1, -1, -1, -1, -1, -1, -1, -1};
static uint8_t regMask = 0b0010;                // bit0 L, bit1 M-left, bit2 M-right, bit3 H (position 3 = M)

static float noteHz(int n) { return 440.0f * powf(2.0f, (n - 69) / 12.0f); }
static void soundOn(int note, int vel) {
  int v = 0;
  for (int i = 0; i < 8; i++) if (voiceNote[i] < 0) { v = i; break; }
  voiceNote[v] = note;
  float amp = 0.05f + 0.20f * (vel / 127.0f);
  voice[v].begin(amp, noteHz(note), (regMask & 0b1000) ? WAVEFORM_SINE : WAVEFORM_SAWTOOTH);
}
static void soundOff(int note) {
  for (int i = 0; i < 8; i++) if (voiceNote[i] == note) { voiceNote[i] = -1; voice[i].amplitude(0); }
}
static void allSoundOff() { for (int i = 0; i < 8; i++) { voiceNote[i] = -1; voice[i].amplitude(0); } }

// ---------------------------------------------------------------- knobs: two TMAG5273 angle sensors (I2C), magnet on the knob stem
// Registers: 7 absolute positions every 45 deg, clockwise from bottom-left; volume: continuous angle between the OFF click and the end stop.
// REG_A0 / VOL_A_* are the sensor-frame angles of those mechanical points: set when the first knob exists (the sensor frame depends on how
// the chip is placed). Defaults below are placeholders.
#define REG_A0       225.0f   // sensor angle of position 1 (deg)
#define REG_HYST     8.0f     // a new position needs to be within 22.5 - REG_HYST deg of its centre
#define VOL_A_MIN    40.0f    // sensor angle just after the OFF click (volume 0)
#define VOL_A_MAX    300.0f   // end stop (volume 1)
static const uint8_t REG_MASK[7] = {0b0001, 0b0011, 0b0010, 0b0110, 0b1010, 0b1001, 0b1000};  // L, LM, M, MM, MH, LH, H
static bool tmagOk[2] = {false, false};
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
static int regPos = 2;
static void updateRegister() {
  float a;
  if (!tmagAngle(TMAG_REG_ADDR, a)) return;
  float rel = fmodf(a - REG_A0 + 720.0f, 360.0f);                 // clockwise from position 1
  int p = (int)((rel + 22.5f) / 45.0f);
  if (p > 6) return;                                              // outside the 7 positions (dead zone between 7 and 1): keep the last one
  float off = rel - 45.0f * p;
  if (p != regPos && fabsf(off) <= 22.5f - REG_HYST) {            // hysteresis
    regPos = p; regMask = REG_MASK[p];
    usbMIDI.sendControlChange(26, regMask, 1);
  }
}
static float volSm = 0;
static bool readVolume(float &out) {
  float a;
  if (!tmagAngle(TMAG_VOL_ADDR, a)) return false;
  float rel = fmodf(a - VOL_A_MIN + 720.0f, 360.0f);
  float x = rel / (VOL_A_MAX - VOL_A_MIN);
  if (rel > 330.0f) x = 0;                                        // just before the OFF click: the sensor wraps, treat as 0
  x = x < 0 ? 0 : (x > 1 ? 1 : x);
  volSm += 0.2f * (x - volSm);
  out = volSm;
  return true;
}

// ---------------------------------------------------------------- battery, knob, power
static float batteryV() { return analogRead(PIN_VBAT_S) * 3.3f / 4095.0f * 2.0f; }
static bool knobOn() { return digitalRead(PIN_KNOB_N) == LOW; }   // Hall switch: low = knob out of OFF
static void pulsePin(uint8_t pin, uint32_t ms) { digitalWrite(pin, HIGH); delay(ms); digitalWrite(pin, LOW); }
static bool usbPresent() { return digitalRead(PIN_PGOOD_N) == LOW; }
static bool charging() { return digitalRead(PIN_CHG_STAT) == LOW; }
static uint32_t lastActivity = 0, bootMs = 0, lowSince = 0;
static bool softOff = false;                     // knob OFF with the cable in: silent, charging, MIDI still alive
static bool rulerFault = false;

// ---------------------------------------------------------------- LED (R/G, orange = both)
static void led(bool r, bool g) { digitalWriteFast(PIN_LED_R, r); digitalWriteFast(PIN_LED_G, g); }
static bool anyNoteDown() { for (int i = 0; i < 8; i++) if (voiceNote[i] >= 0) return true; return false; }
static void updateLed(uint32_t now) {
  if (!codecOk || rulerFault) { led((now / 150) & 1, false); return; }                                  // fast red: codec or ruler silent
  if (batteryV() < 3.45f && !usbPresent()) { led(((now / 1000) % 3) == 0, false); return; }            // slow red: low battery
  if (now - bootMs < 600) { led(true, true); return; }                                                 // orange: reading the keys at start
  if (usbPresent() && charging()) { led(true, true); return; }                                         // orange: charging
  if (softOff) { led(false, usbPresent() && !charging()); return; }                                    // cable, knob off: green when full
  if (anyNoteDown()) { led(false, true); return; }                                                     // green: playing
  led(false, (now % 2000) < 60);                                                                       // short green every 2 s at rest
}

// ---------------------------------------------------------------- key processing
static void processKeys() {
  for (int r = 0; r < NROWS; r++) for (int c = 0; c < NCOLS; c++) {
    Key &k = keys[r][c];
    if (!k.present) continue;
    float dev = fabsf((float)rawNow[r][c] - k.rest);
    if (dev > 0.6f * k.bottom && dev > k.bottom * 1.02f && dev < 4000) k.bottom = dev;   // learn the bottom
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
        usbMIDI.sendNoteOn(NOTE[r][c], vel, 1);
        soundOn(NOTE[r][c], vel);
        lastActivity = millis();
      }
    } else if (t <= NOTE_OFF_AT) {
      k.on = false;
      usbMIDI.sendNoteOff(NOTE[r][c], 0, 1);
      soundOff(NOTE[r][c]);
      lastActivity = millis();
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
    k.bottom = (BOTTOM_GS - REST_GS) * COUNTS_PER_GS;
    k.present = k.rest > 100 && k.rest < 4000;   // a rail reading = no sensor on the line
    k.on = k.armed = false;
    alive += k.present;
  }
  rulerFault = alive < NROWS * NCOLS;            // any silent sensor: fast red (SPEC 4)
}

// ---------------------------------------------------------------- MIDI in (CC 26 register from the page)
static void onCC(byte ch, byte cc, byte val) { (void)ch; if (cc == 26) regMask = val & 0x0F; }

void setup() {
  pinMode(PIN_KILL, OUTPUT); digitalWrite(PIN_KILL, LOW);
  pinMode(PIN_SET, OUTPUT); digitalWrite(PIN_SET, LOW);
  pinMode(PIN_KNOB_N, INPUT);
  USB1_PORTSC1 |= USB_PORTSC1_PFSC;              // force USB Full Speed (the 30-35 mm pair is not controlled-impedance); NOT verified on hardware
  analogReadResolution(ADC_BITS);
  analogReadAveraging(1);
  pinMode(PIN_LED_R, OUTPUT); pinMode(PIN_LED_G, OUTPUT);
  pinMode(PIN_CHG_STAT, INPUT); pinMode(PIN_PGOOD_N, INPUT);
  pinMode(PIN_SCAN_DATA, OUTPUT); pinMode(PIN_SCAN_CLK, OUTPUT); pinMode(PIN_SCAN_LATCH, OUTPUT);
  digitalWriteFast(PIN_SCAN_CLK, LOW); digitalWriteFast(PIN_SCAN_LATCH, LOW);
  bootMs = millis();
  led(true, true);
  AudioMemory(24);
  Wire.begin(); Wire.setClock(400000);
  if (knobOn()) pulsePin(PIN_SET, 10);           // started from USB with the knob already on: arm the latch so the battery takes over when the cable goes
  tmagOk[0] = tmagInit(TMAG_REG_ADDR); tmagOk[1] = tmagInit(TMAG_VOL_ADDR);
  codecOk = codec.enable();                      // I2C 0x0A; false if the codec does not answer
  codec.volume(0.0f);
  usbMIDI.setHandleControlChange(onCC);
  scanClear();
  calibrateRest();
  regPos = -1;                                   // force the first register read to be announced
  lastActivity = millis();
}

void loop() {
  uint32_t now = millis();
  while (usbMIDI.read()) {}
  scanFrame();
  processKeys();
  static uint32_t slow = 0;
  if (now - slow >= 20) {                        // 50 Hz: knobs, power, LED
    slow = now;
    updateRegister();
    float v = volSm;
    if (readVolume(v)) {
      int cc = (int)(v * 127.0f + 0.5f);
      static int lastCC = -1;
      if (cc != lastCC) { lastCC = cc; usbMIDI.sendControlChange(7, cc, 1); }
    }
    bool on = knobOn(), usb = usbPresent();
    softOff = usb && !on;
    if (codecOk) codec.volume(softOff ? 0.0f : v * 0.8f);
    updateLed(now);
    // power: the Hall switch drops the battery path in hardware when the knob goes to OFF. The firmware only handles the automatic switch-off.
    bool idle = !usb && (now - lastActivity > 15UL * 60UL * 1000UL);
    if (batteryV() < 3.3f && !usb) { if (!lowSince) lowSince = now; } else lowSince = 0;
    bool empty = lowSince && (now - lowSince > 5000);
    if (!on) allSoundOff();
    if ((idle || empty) && !usb) { allSoundOff(); codec.volume(0); pulsePin(PIN_KILL, 50); }   // resets the latch: SYSOFF is released, the battery is disconnected, the board dies
  }
  usbMIDI.send_now();
}
