"""Writes capture_notes.mid: the note sequence used to record reference
audio of an accordion sample library, one reed rank (or register) per pass.

Play the file through the library in a DAW with one reed soloed, export the
audio, and save it in capturas/ (not tracked by git). The notes are the
eTuttino keys G3..E6 taken every 3 semitones, each held 3 s with 1.5 s of
silence after it, so the recording can be cut into notes afterwards.

Run:  python etutti/firmware/tools/accordion_samples/make_capture_midi.py
"""
import os
import struct

FIRST_NOTE = 55          # G3, the lowest eTuttino key
LAST_NOTE = 88           # E6, the highest
STEP = 3                 # semitones between captured notes
HOLD_S = 3.0             # note length
GAP_S = 1.5              # silence after each note
LEAD_IN_S = 1.0          # silence before the first note
VELOCITY = 100
MOD_WHEEL = 100          # bellows pressure when the library follows CC 1
PPQ = 480
BPM = 120                # 1 beat = 0.5 s

NOTES = list(range(FIRST_NOTE, LAST_NOTE + 1, STEP))


def ticks(seconds):
    return int(round(seconds * BPM / 60.0 * PPQ))


def varlen(value):
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def build():
    tempo = int(60_000_000 / BPM)
    track = bytearray()
    track += varlen(0) + bytes([0xFF, 0x51, 0x03]) + tempo.to_bytes(3, "big")
    track += varlen(0) + bytes([0xB0, 1, MOD_WHEEL])
    delta = ticks(LEAD_IN_S)
    for note in NOTES:
        track += varlen(delta) + bytes([0x90, note, VELOCITY])
        track += varlen(ticks(HOLD_S)) + bytes([0x80, note, 0])
        delta = ticks(GAP_S)
    track += varlen(delta) + bytes([0xFF, 0x2F, 0x00])
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
    return header + b"MTrk" + struct.pack(">I", len(track)) + bytes(track)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_notes.mid")
    with open(path, "wb") as f:
        f.write(build())
    total = LEAD_IN_S + len(NOTES) * (HOLD_S + GAP_S)
    print(f"{path}: {len(NOTES)} notes {NOTES}, {total:.1f} s")
