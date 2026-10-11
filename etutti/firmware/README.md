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
- Both engines feed a tone filter and a light room reverb (CC 91).
- Measured on a Teensy 4.0 with the worst case (8 notes × 4 reeds plus
  reverb): about 9 % CPU and 32 audio blocks.

## MIDI implementation

The synth listens on every channel.

| Message | Effect |
| --- | --- |
| Note On / Off | play / release; velocity sets loudness |
| CC 7 | volume |
| CC 24 | key layout of the physical keys: 0–63 C-griff, 64–127 B-griff |
| CC 25 | instrument: 0–31 accordion, 32–63 piano, 64–95 bass, 96–127 guitar |
| CC 26 | accordion register, bit mask: 1 = 16', 2 = 8' M1 (open), 4 = 8' M2 (cassotto), 8 = 4' |
| CC 27 | reed tuning: M2 detune in cents, 0 = dry … 30 = very wet |
| CC 72 | release, accordion (0–3000 ms) |
| CC 73 | attack, accordion (0–2000 ms) |
| CC 74 | tone: low-pass 40 Hz – ~17 kHz |
| CC 91 | ambience (room reverb) |
| CC 120 | all sound off |
| CC 123 | all notes off |

The CC numbers are duplicated in `etutti/script.js` (`CC`). Change both
together.
