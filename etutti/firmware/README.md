# eTutti firmware

Teensy sketch for [beatconfused.com/etutti](https://beatconfused.com/etutti/):
an 8-voice polyphonic synth that the web page plays and controls over USB
MIDI. Sound comes out of the PJRC Audio Board.

## Hardware

- Teensy 4.0 + PJRC Audio Adaptor Board **Rev D** (SGTL5000)
- the eTuttino PCB with its 34 key switches, see [`../hardware`](../hardware).
  Without the PCB the sketch still works as a USB MIDI synth driven by the
  web page.
- Headphones or an amplifier on the Audio Board's headphone jack or line out

The firmware scans the 4 × 9 key matrix (rows on pins 0–3; columns on
pins 4, 5, 6, 9, 14, 15, 16, 17 and 22). Every key plays the built-in synth
and is also sent as USB MIDI, so the page lights the key up.

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
| CC 7 | volume |
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

The CC numbers are duplicated in `etutti/script.js` (`CC`). Change both
together.
