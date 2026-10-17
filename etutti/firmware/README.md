# eTutti firmware

Teensy sketch for [beatconfused.com/etutti/etuttino](https://beatconfused.com/etutti/etuttino/):
an 8-voice polyphonic synth that the web page plays and controls over USB
MIDI. Sound comes out of the PJRC Audio Board.

## Hardware

- Teensy 4.0 + PJRC Audio Adaptor Board **Rev D** (SGTL5000)
- the eTuttino PCB with its 44 magnetic key switches and Hall sensors, see
  [`../hardware`](../hardware). Without the PCB the sketch still works as a
  USB MIDI synth driven by the web page: at start-up a key whose sensor
  doesn't answer is left out, so a bare Teensy plays no stray notes.
- Headphones or an amplifier on the Audio Board's headphone jack or line out

## Keys: Hall-effect sensing and velocity

Each key is a Gateron magnetic switch with a DRV5056A3 Hall sensor under it
(0.6 V with no field, +30 mV per mT at 3.3 V). Three CD74HC4067
multiplexers share the address lines on pins 0–3 (S0–S3); their outputs go
to pins 14, 15 and 16 (A0–A2), which have their pull-downs on so a missing
sensor reads 0 V rather than floating. `KEY_INPUT` maps each note-grid cell
to multiplexer × 16 + channel. It comes from `../hardware/generate.py`, and
`build_pcb.py` checks the routed board against this copy.

- **Scan:** 34 sensors took about 240 µs (measured on a Teensy 4.0; 44 should take about 310 µs), so
  about 4 kHz per key.
- **Travel:** the magnet's field falls off roughly as 1/distance³, so the
  travel is the cube root of the field above the sensor's 0.6 V zero,
  scaled between the key's rest reading and its bottomed-out reading. In
  simulation this tracks the real travel to within a couple of percent.
- **Calibration:**
  - Rest is measured at start-up (keys untouched) and then follows slow
    drift.
  - The bottom is the deepest press seen. It is saved to EEPROM 5 s after
    it last grew.
  - CC 14 forgets the learnt bottoms. The page's "Calibrate keys" button
    sends it.
- **Note on:** at 45 % of the travel, about 1.8 mm. Note off is at 30 %
  (hysteresis).
- **Velocity:** the time between passing 12 % and 45 % of the travel, with
  both crossings interpolated between scans. It is mapped on a log scale:
  1 ms or faster = 127, 80 ms or slower = 1. CC 9 bends the curve or fixes
  velocity at 100.
- **Key test (CC 15):** streams each key's position back as Polyphonic
  Aftertouch on channel 16 (data 1 = key index in grid order, data 2 =
  0–127). The page draws it as a ring around each on-screen key.

**Power LED** (pins 4 red, 5 green): orange while the keys are first read
at power-up (at least 0.6 s), green while playing, red blinking on an
error: the Audio Board's codec didn't answer, or a key's sensor didn't.
It blinks green slowly while an instrument picked with the encoder waits
to be confirmed.

**Controls board** (on the main board's J3; see `../hardware/README.md`):

- **Volume pot** (pin 22 / A8). It sets the headphone volume, like CC 7,
  and sends CC 7 back. It only acts when it is turned, so a CC 7 from the
  page holds until the pot moves. At power-up the firmware checks whether
  a pot is there at all: with nothing on J3, the pin just follows the
  Teensy's pull-up and pull-down. In that case the pot input is ignored
  and the volume doesn't wander.
- **Encoder** (pins 17 / 9). Turning steps through accordion → piano →
  bass → guitar → synth and plays the new instrument at once. It also
  sends CC 25 back. The page follows both CCs (its volume slider and
  instrument move) without sending them back.
- **Encoder button** (pin 6):
  - Pressed after turning, it confirms the new instrument. That
    instrument is then the one the eTuttino starts with (EEPROM).
  - Pressed without turning first, it goes back to the default sound:
    classic accordion, register MM, dry.
- `ENC_STEPS_PER_DETENT` is 4, for the EC11E with 15 pulses and 15
  detents (SPEC v9). Use 2 for the model with 15 pulses and 30 detents.

Every key plays the built-in synth and is also sent as USB MIDI (channel 1,
with its velocity), so the page lights the key up and any DAW can record it.

## Flashing

1. Install the [Arduino IDE](https://www.arduino.cc/en/software) and the
   Teensy board package
   ([Teensyduino](https://www.pjrc.com/teensy/td_download.html)). The Teensy
   Audio Library comes with it.
2. Open `etutti_synth/etutti_synth.ino`. Keep `name.c` in the same folder:
   it names the USB device "eTutti".
3. **Tools › Board**: your Teensy. **Tools › USB Type**: `MIDI` (or
   `Serial + MIDI` if you want `Serial.print` debugging too).
4. Upload. Then open the eTutti page in Chrome or Edge, press **Connect**,
   and allow MIDI access.

If compiling stops with *"In the Arduino IDE choose Tools > USB Type >
MIDI…"* (or, in older copies of the sketch, *"'usbMIDI' was not declared in
this scope"*), the USB Type is still on the default "Serial". Change it and
upload again.

The message *"Multiple libraries were found for SD.h"* is only a warning:
the Arduino IDE also has its own SD library installed, and it correctly
uses the Teensy one.

On Windows the old device name ("Teensy MIDI") can stick around after the
rename. Remove the device in Device Manager and plug it in again. The page
recognises either name.

## Sound engines

- **Accordion**: every note sounds up to four free reeds, chosen by the
  register (CC 26), as on a real accordion: 16' (low, in cassotto), 8' M1
  (open), 8' M2 (in cassotto) and 4' (piccolo). Each reed plays a waveform
  built at start-up by additive synthesis of a free reed's spectrum
  (brighter when open, rounder in cassotto). The spectrum is band-limited,
  so it doesn't alias, which is what made the old saw/square synth sound
  metallic. "Reed tuning" (CC 27) detunes M2 against M1: 0 = dry
  (classic), a few cents = wet (jazz).
- **Samples**: piano, nylon guitar, and the guitar's low strings two
  octaves down as an acoustic-bass stand-in. They play through
  `AudioSynthWavetable`. The sample data (`piano_samples.*`,
  `nylonstrgtr_samples.*`) comes from the Teensy Audio Library's
  `MidiSynthLarge` example. More instruments can be converted from any
  SoundFont with PJRC's SoundFont decoder.
- **Synth**: a subtractive synth that reuses three of each voice's
  oscillators. Each oscillator has a waveform (sine, triangle, and
  band-limited saw/square), a level, a detune and an octave. A full ADSR
  envelope follows.
- All engines feed a tone filter and a light room reverb (CC 91). The tone
  filter is a **biquad**. The state-variable filter used before blew up
  near its top frequency: with the tone wide open, piano and guitar came
  out as full-scale noise (measured on the Teensy: input 0.02, output
  pinned at 1.0).
- Measured on a Teensy 4.0:
  - accordion worst case (8 notes × 4 reeds + reverb): about 9–16 % CPU
  - synth (8 notes × 3 band-limited oscillators): about 17.5 %
  - samples: about 4–5 %
  - The peak was 32 audio blocks; `AudioMemory(60)`.

## MIDI implementation

The synth listens on every channel.

| Message | Effect |
| --- | --- |
| Note On / Off | play / release; velocity sets loudness |
| CC 7 | volume (also sent back when the controls board's pot moves) |
| CC 9 | velocity curve of the physical keys = value / 32: 0 fixed (100), 1 light touch, 2 normal, 3 firm touch |
| CC 14 | 64–127: restart the keys' calibration (forget the learnt bottoms) |
| CC 15 | key test: 64–127 on, streams key positions as Poly Aftertouch on channel 16 |
| CC 24 | key layout of the physical keys: 0–63 C-griff, 64–127 B-griff |
| CC 20–22 | synth oscillator 1–3 waveform: 0–31 sine, 32–63 triangle, 64–95 saw, 96–127 square |
| CC 25 | instrument = value / 16: 0 accordion, 1 piano, 2 bass, 3 guitar, 4 synth |
| CC 26 | accordion register, bit mask: 1 = 16', 2 = 8' M1 (open), 4 = 8' M2 (cassotto), 8 = 4' |
| CC 27 | reed tuning: M2 detune in cents, 0 = dry … 30 = very wet |
| CC 28–30 | synth oscillator 1–3 level |
| CC 72 | release, accordion + synth (0–3000 ms) |
| CC 73 | attack, accordion + synth (0–2000 ms) |
| CC 74 | tone: low-pass 40 Hz – 16 kHz (biquad) |
| CC 75 | decay, synth (0–2000 ms) |
| CC 79 | sustain, synth |
| CC 85–87 | synth oscillator 1–3 detune: 64 = in tune, 0 / 127 = −50 / +50 cents |
| CC 91 | ambience (room reverb) |
| CC 102–104 | synth oscillator 1–3 octave: 0–42 down, 43–84 unison, 85–127 up |
| CC 120 | all sound off |
| CC 123 | all notes off |

The CC numbers are duplicated in `etutti/etuttino/script.js` (`CC`). Change both
together.
