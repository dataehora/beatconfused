"""Checks the Student V01 part of the firmware against the pin map and the routed board.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/firmware_check.py

1. Every pin the sketch names in its Student V01 block (and the fixed I2S / I2C pins of the audio
   library) must carry, in viaggio_micromod/pcb/PINOS.md, the net its name stands for.
2. On the board, the pad of the module connector J101 that PINOS.md gives for that pin must be on
   that net.
3. The sketch's KEY_INPUT table must equal the one in PINOS.md (read from the routed board, 28/28).

Exits non-zero on any difference and writes firmware_check.json.
"""
import json
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SKETCH = os.path.join(REPO, "etutti", "firmware", "etutti_synth", "etutti_synth.ino")
PINOS = os.path.join(REPO, "etutti", "hardware", "viaggio_micromod", "pcb", "PINOS.md")
BOARD = os.path.join(HERE, "kicad", "viaggio_micromod.kicad_pcb")

# sketch constant -> the net(s) it must be on, in the order of its values
EXPECT = {"MUX_SEL_PINS": ["MUX_S0", "MUX_S1", "MUX_S2", "MUX_S3"], "MUX_COM_PINS": ["MUX_R_COM", "MUX_L_COM"],
          "SENS_EN_PIN": ["SENS_EN"], "LED_PINS": ["LED_R", "LED_G"], "VOL_A_PIN": ["VOL_A"], "VOL_B_PIN": ["VOL_B"],
          "VOL_SW_PIN": ["VOL_SW"], "ENC_A_PIN": ["SEL_A"], "ENC_B_PIN": ["SEL_B"], "ENC_SW_PIN": ["SEL_SW"],
          "KEEP_PIN": ["KEEP"], "PWR_EN_PIN": ["PWR_EN"], "AMP_SD_PIN": ["AMP_SD"], "VBAT_PIN": ["VBAT_S"],
          "HP_DET_PIN": ["HP_DET"], "CHG_STAT_PIN": ["CHG_STAT"]}
# pins the Teensy audio library uses by itself on this processor
LIBRARY = {7: "I2S_TX", 20: "I2S_LRCLK", 21: "I2S_BCLK", 23: "AUD_MCLK_P", 18: "I2C_SDA", 19: "I2C_SCL"}


def student_block(text):
    a = text.index("#if ETUTTI_STUDENT\n// ---- eTutti Student V01")
    return text[a:text.index("#else", a)]


def table(text):
    m = re.search(r"KEY_INPUT\[[^\]]*\]\[[^\]]*\] = \{(.*?)\n\};", text, re.S)
    return [[int(v) for v in re.findall(r"-?\d+", row)] for row in re.findall(r"\{([^{}]*)\}", m.group(1))]


def main():
    sketch = open(SKETCH, encoding="utf-8").read()
    block = student_block(sketch)
    pinos = open(PINOS, encoding="utf-8").read()
    pinmap = {}                                   # pin -> (pad, net)
    for row in re.findall(r"^\| \**(\d+)\**[^|]*\| \**(\d+)[^|]*\|[^|]*\| \**([A-Za-z0-9_]+|—)\**", pinos, re.M):
        pinmap[int(row[0])] = (row[1], row[2])
    board = pcbnew.LoadBoard(BOARD)
    j101 = {p.GetNumber(): p.GetNetname().lstrip("/") for p in board.FindFootprintByReference("J101").Pads()}
    problems, checked = [], []

    def check(name, pin, net):
        pad, pnet = pinmap.get(pin, (None, None))
        on_board = j101.get(pad)
        ok = pnet == net and on_board == net
        checked.append({"firmware": name, "pino": pin, "rede": net, "pad_J101": pad, "rede_na_placa": on_board, "ok": ok})
        if not ok:
            problems.append("%s: pin %d should be %s; PINOS.md says %s, the board's pad %s is on %s" % (
                name, pin, net, pnet, pad, on_board))

    for name, nets in EXPECT.items():
        m = (re.search(r"\b%s\[[^\]]*\]\s*=\s*\{([^}]*)\}" % name, block)      # an array
             or re.search(r"\b%s\s*=\s*(\d+)" % name, block))                  # one pin (several may share a line)
        if not m:
            problems.append("%s not found in the sketch's Student V01 block" % name)
            continue
        pins = [int(v) for v in re.findall(r"\d+", m.group(1))]
        if len(pins) != len(nets):
            problems.append("%s: %d pins, %d expected" % (name, len(pins), len(nets)))
            continue
        for pin, net in zip(pins, nets):
            check(name, pin, net)
    for pin, net in LIBRARY.items():
        check("audio library", pin, net)
    used = [c["pino"] for c in checked]
    twice = sorted({p for p in used if used.count(p) > 1})
    if twice:
        problems.append("pins used twice: %s" % twice)

    fw, doc = table(block), table(pinos[pinos.index("BEGIN KEY_INPUT"):])
    keys = sum(1 for r in fw for v in r if v >= 0)
    if fw != doc:
        problems.append("KEY_INPUT in the sketch differs from PINOS.md")
    if keys != 28 or len({v for r in fw for v in r if v >= 0}) != 28:
        problems.append("KEY_INPUT: %d keys, 28 different inputs expected" % keys)

    out = {"pinos_conferidos": len(checked), "teclas": keys, "KEY_INPUT_igual_ao_PINOS": fw == doc,
           "problemas": problems, "pinos": checked}
    json.dump(out, open(os.path.join(HERE, "firmware_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("%d pins checked, %d keys, KEY_INPUT equal: %s, %d problems" % (len(checked), keys, fw == doc, len(problems)))
    for p in problems:
        print("  PROBLEM:", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
