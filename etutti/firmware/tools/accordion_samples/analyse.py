"""Cuts each recording in capturas/ into its notes and measures them.

For every file (one reed rank or register per file, recorded with
capture_notes.mid) it prints, per note: start and length, level, attack
time (10 % to 90 % of the steady level), fundamental and its offset in
cents from the played key, and the level of the first harmonics.

Run with a Python that has numpy and scipy:
  python analyse.py            (all files)
  python analyse.py L M2       (only these)
"""
import glob
import os
import sys

import numpy as np
from scipy.io import wavfile

from make_capture_midi import NOTES, SOUNDING_OFFSET

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURES = os.path.join(HERE, "capturas")


def load(name):
    """Mono float signal in -1..1 and its sample rate."""
    rate, data = wavfile.read(os.path.join(CAPTURES, name + ".wav"))
    if data.dtype.kind == "i":
        data = data.astype(np.float64) / float(2 ** (8 * data.dtype.itemsize - 1))
    else:
        data = data.astype(np.float64)
    if data.ndim == 2:
        data = data.mean(axis=1)
    return rate, data


def envelope(x, rate, win_ms=10.0):
    n = max(1, int(rate * win_ms / 1000.0))
    return np.sqrt(np.convolve(x * x, np.ones(n) / n, mode="same"))


def find_notes(x, rate):
    """(start, end) sample indices of each sounding stretch."""
    env = envelope(x, rate)
    gate = env > env.max() * 0.02
    edges = np.flatnonzero(np.diff(gate.astype(np.int8)))
    if gate[0]:
        edges = np.insert(edges, 0, 0)
    if gate[-1]:
        edges = np.append(edges, len(gate) - 1)
    spans = [(a, b) for a, b in zip(edges[0::2], edges[1::2])]
    merged = []
    for a, b in spans:                      # join stretches under 0.3 s apart
        if merged and a - merged[-1][1] < 0.3 * rate:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if b - a > 0.5 * rate], env


def fundamental(seg, rate, guess):
    """Fundamental near `guess` Hz, refined on the strongest low harmonics."""
    n = len(seg)
    win = np.hanning(n)
    pad = 1 << int(np.ceil(np.log2(n)) + 3)
    spec = np.abs(np.fft.rfft(seg * win, pad))
    freqs = np.fft.rfftfreq(pad, 1.0 / rate)

    def peak(f, width=0.04):
        lo, hi = np.searchsorted(freqs, [f * (1 - width), f * (1 + width)])
        k = lo + int(np.argmax(spec[lo:hi]))
        a, b, c = spec[k - 1], spec[k], spec[k + 1]
        shift = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
        return (k + shift) * freqs[1], b

    f0, _ = peak(guess)
    num = den = 0.0
    for h in range(1, 9):
        if f0 * h > rate * 0.45:
            break
        f, amp = peak(f0 * h, 0.02)
        num += amp * f / h
        den += amp
    f0 = num / den
    harm = []
    for h in range(1, 25):
        if f0 * h > rate * 0.45:
            break
        harm.append(peak(f0 * h, 0.015)[1])
    harm = np.array(harm)
    return f0, 20 * np.log10(harm / harm.max() + 1e-12)


def analyse(name):
    rate, x = load(name)
    notes, env = find_notes(x, rate)
    print(f"\n== {name}: {rate} Hz, {len(x) / rate:.1f} s, {len(notes)} notes, peak {20 * np.log10(np.abs(x).max()):.1f} dBFS")
    out = []
    for i, (a, b) in enumerate(notes):
        key = NOTES[i] if i < len(NOTES) else None
        mid = x[a + int(1.0 * rate): a + int(2.5 * rate)]
        level = np.sqrt(np.mean(mid * mid))
        e = env[a:b]
        steady = np.median(env[a + int(1.0 * rate): a + int(2.5 * rate)])
        t10 = np.argmax(e > 0.1 * steady) / rate
        t90 = np.argmax(e > 0.9 * steady) / rate
        tail = env[b - int(0.05 * rate):b + int(1.0 * rate)]
        rel = np.argmax(tail < 0.1 * steady) / rate
        guess = 440.0 * 2 ** ((key + SOUNDING_OFFSET - 69) / 12.0) if key else 440.0
        # L sounds an octave below the 8' reeds, H an octave above
        octave = {"L": 0.5, "H": 2.0}.get(name[0], 1.0)
        f0, harm = fundamental(mid, rate, guess * octave)
        cents = 1200 * np.log2(f0 / (guess * octave))
        out.append(dict(key=key, start=a, end=b, level=level, f0=f0, cents=cents,
                        octave=octave, attack=t90 - t10, release=rel, harm=harm))
        hs = " ".join(f"{h:4.0f}" for h in harm[:12])
        print(f"key {key} t={a / rate:5.2f}s len={(b - a) / rate:4.2f}s "
              f"lvl={20 * np.log10(level):6.1f}dB att={1000 * (t90 - t10):4.0f}ms "
              f"rel={1000 * rel:4.0f}ms f0={f0:8.2f}Hz x{octave} {cents:+6.1f}c | {hs}")
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(
        os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(CAPTURES, "*.wav")))
    for n in names:
        analyse(n)
