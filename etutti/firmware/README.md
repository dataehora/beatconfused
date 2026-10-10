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

On Windows the old device name ("Teensy MIDI") can stick around after the
rename. Remove the device in Device Manager and plug it in again. The page
recognises either name.

## MIDI implementation

The synth listens on every channel.

| Message | Effect |
| --- | --- |
| Note On / Off | play / release; velocity sets loudness |
| CC 7 | volume |
| CC 70 | waveform: 0–31 sine, 32–63 saw, 64–95 square, 96–127 triangle |
| CC 71 | filter resonance (0.7–5.0) |
| CC 72 | release (0–3000 ms) |
| CC 73 | attack (0–2000 ms) |
| CC 74 | filter cutoff (40 Hz – ~17 kHz) |
| CC 75 | decay (0–2000 ms) |
| CC 79 | sustain level |
| CC 120 | all sound off |
| CC 123 | all notes off |

The CC numbers are duplicated in `etutti/script.js` (`CC`). Change both
together.
