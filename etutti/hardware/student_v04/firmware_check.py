"""Checks the Student V4 sketch against the main board (R12V4, item 3).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/firmware_check.py [board.kicad_pcb]

Without an argument it reads kicad/student_v04_roteada.kicad_pcb when it exists, else the placed
kicad/student_v04.kicad_pcb (nets and pins do not change with the routing).

1. Every pin the sketch names (student_v4.ino) must carry, in pcb/PINOS.md, the net its name stands for.
2. The pad of the module connector J101 that PINOS.md gives for that pin must be on that net, on the board
   AND in the schematic's netlist (pcb/build/student_v04_netlist.net).
   (SCAN_DATA / SCAN_CLK reach the pad through a series resistor: the pad's net is SCAN_DATA_P / SCAN_CLK_P.)
3. The audio library's fixed pins (I2S 7/8/20/21/23, I2C 18/19) are on their nets.
4. Keyboard constants (4 x R8, no OUT, 9 pulses, column = stage, FIRST_NOTE), the OLED (0x3D, fallback 0x3C,
   rotated 180 deg), the microphone menu / bias register and thresholds, and the parts around the jack IN
   (R305 = 0 ohm, C310 not fitted, R306 100 k and C311 100 nF on MIC_DET) are checked against the sketch's text.

Exits non-zero on any difference and writes firmware_check.json.
"""
import json
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SKETCH = os.path.join(REPO, "etutti", "firmware", "student_v4", "student_v4.ino")
PINOS = os.path.join(HERE, "pcb", "PINOS.md")
NETLIST = os.path.join(HERE, "pcb", "build", "student_v04_netlist.net")
ROUTED = os.path.join(HERE, "kicad", "student_v04_roteada.kicad_pcb")
PLACED = os.path.join(HERE, "kicad", "student_v04.kicad_pcb")

# sketch constant -> nets, in the order of its values
EXPECT = {"ROW_OUT_PINS": ["OUT_R1", "OUT_R2", "OUT_R3", "OUT_R4"], "SR_DATA_PIN": ["SCAN_DATA"], "SR_CLK_PIN": ["SCAN_CLK"],
          "VOL_A_PIN": ["VOL_A"], "VOL_B_PIN": ["VOL_B"], "VOL_SW_PIN": ["VOL_SW"], "ENC_A_PIN": ["SEL_A"],
          "ENC_B_PIN": ["SEL_B"], "ENC_SW_PIN": ["SEL_SW"], "KEEP_PIN": ["KEEP"], "AMP_SD_PIN": ["AMP_SD"],
          "VBAT_PIN": ["VBAT_S"], "HP_DET_PIN": ["HP_DET"], "CHG_STAT_PIN": ["CHG_STAT"], "MIC_DET_PIN": ["MIC_DET"]}
LIBRARY = {7: "I2S_TX", 8: "I2S_RX", 20: "I2S_LRCLK", 21: "I2S_BCLK", 23: "AUD_MCLK_P", 18: "I2C_SDA", 19: "I2C_SCL"}
# the pad's net on the board when a series part sits between the pad and the signal
BOARD_ALIAS = {"SCAN_DATA": "SCAN_DATA_P", "SCAN_CLK": "SCAN_CLK_P"}


def netlist_j101():
    text = open(NETLIST, encoding="utf-8").read()
    out = {}
    for blk in re.split(r"\n\t\t\(net\n", text)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', blk).group(1).lstrip("/")
        for ref, pin in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', blk):
            if ref == "J101":
                out[pin] = name
    return out


def main():
    src = open(SKETCH, encoding="utf-8").read()
    pinos = open(PINOS, encoding="utf-8").read()
    boardfile = sys.argv[1] if len(sys.argv) > 1 else (ROUTED if os.path.exists(ROUTED) else PLACED)
    board = pcbnew.LoadBoard(boardfile)
    j101 = {p.GetNumber(): p.GetNetname().lstrip("/") for p in board.FindFootprintByReference("J101").Pads()}
    nl = netlist_j101()
    problems, checked, notes = [], [], []

    pinmap = {}                                    # pin -> (pad, net)
    for row in re.findall(r"^\| \**(\d+)[^|]*\| \**(\d+)[^|]*\|\s*\**([A-Za-z0-9_]+|-)\**[^|]*\|", pinos, re.M):
        pinmap[int(row[0])] = (row[1], row[2])

    def check(name, pin, net):
        pad, pnet = pinmap.get(pin, (None, None))
        want = BOARD_ALIAS.get(net, net)
        on_board, on_nl = j101.get(pad), nl.get(pad)
        ok = pnet == net and on_board == want and on_nl == want
        checked.append({"firmware": name, "pino": pin, "rede": net, "pad_J101": pad, "rede_na_placa": on_board,
                        "rede_no_netlist": on_nl, "ok": ok})
        if not ok:
            problems.append("%s: pin %d should be %s; PINOS.md says %s, pad %s is %s on the board and %s in the netlist" % (
                name, pin, net, pnet, pad, on_board, on_nl))

    for name, nets in EXPECT.items():
        m = (re.search(r"\b%s\[[^\]]*\]\s*=\s*\{([^}]*)\}" % name, src) or re.search(r"\b%s\s*=\s*(\d+)" % name, src))
        if not m:
            problems.append("%s not found in the sketch" % name)
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
    # LED pins: 13 (also the module's LED) and 5 are free pads, no net on the board (the sketch's LED is the module's own)
    m = re.search(r"LED_PINS\[2\]\s*=\s*\{(\d+),\s*(\d+)\}", src)
    led = [int(v) for v in m.groups()] if m else []
    for p in led:
        pad = pinmap.get(p, (None, None))[0]
        notes.append("LED pin %d: pad %s, net on the board %r (free pad)" % (p, pad, j101.get(pad)))
        if p in used:
            problems.append("LED pin %d is also used as a signal" % p)

    # ---- (b) keyboard ----
    def const(name):
        return int(re.search(r"const int %s\s*=\s*(\d+)" % name, src).group(1))

    def expect(cond, msg):
        if not cond:
            problems.append(msg)
        return cond

    expect(const("RULERS_R8") == 1 and const("RULERS_R4") == 0, "keyboard: expected 1 R8 and 0 R4 per row")
    expect("static_assert(V4_KEYS == 32" in src, "keyboard: no static_assert for 32 keys")
    expect(re.search(r"SR_STAGES\s*=\s*8 \* \(RULERS_R8 \+ RULERS_R4\)", src) is not None, "SR_STAGES is not 8 per ruler")
    expect("srPulse(SR_STAGES - 1 - k == target)" in src, "srSelect: column = stage mapping changed")
    expect("for (int i = 0; i <= SR_STAGES; i++) srPulse(0);" in src, "srClear: not SR_STAGES + 1 pulses")
    # Simulation of the sketch's srSelect on a chain of 8 stages (SRCLK and RCLK tied: output = state before the pulse)
    stages = 8

    def select(c):
        reg = [0] * stages
        out = None
        for bit in [1 if stages - 1 - k == c else 0 for k in range(stages)] + [0]:
            out = list(reg)                       # the output register takes the state BEFORE this clock's shift
            reg = [bit] + reg[:-1]
        return out, stages + 1

    sim_ok = True
    for c in range(stages):
        out, pulses = select(c)
        if out != [1 if i == c else 0 for i in range(stages)] or pulses != 9:
            sim_ok = False
    expect(sim_ok, "scan simulation: column c is not stage c with 9 pulses")
    m = re.search(r"FIRST_NOTE\[2\]\[LAYOUT_ROWS\]\s*=\s*\{\s*\{([^}]*)\},[^{]*\{([^}]*)\}", src)
    fn = [[int(v) for v in re.findall(r"-?\d+", g)] for g in m.groups()]
    expect(fn[0] == [57, 55, 56, 54] and fn[1] == [56, 55, 57, 53], "FIRST_NOTE differs from PINOS.md (C: 57 55 56 54; B: 56 55 57 53)")
    expect("FIRST_COL[LAYOUT_ROWS] = {0, 0, 0, 0}" in src, "FIRST_COL is not 0 0 0 0")
    expect("const uint32_t SR_HALF_PERIOD_NS" in src, "SR half period missing")

    # ---- (c) OLED ----
    expect("uint8_t OLED_ADDR = 0x3D;" in src, "OLED: first address is not 0x3D")
    expect(re.search(r"OLED_ADDR = 0x3C;", src) is not None, "OLED: no 0x3C fallback")
    expect("const int OLED_ROTATION = 2;" in src, "OLED: not rotated 180 deg")
    expect("#define OLED_SH1106 0" in src, "OLED: controller is not SSD1306 by default")
    expect("oledCmd(OLED_ROTATION == 2 ? 0xA0 : 0xA1);" in src and "oledCmd(OLED_ROTATION == 2 ? 0xC0 : 0xC8);" in src,
           "OLED: rotation commands (segment remap 0xA0 + COM scan 0xC0)")
    expect(re.search(r"0xA8, 0x3F", src) is not None, "OLED: not 64 rows (0xA8 0x3F)")
    jv = {p.GetNumber(): p.GetNetname().lstrip("/") for p in board.FindFootprintByReference("J401").Pads()}
    expect([jv.get(str(i)) for i in range(1, 5)] == ["GND", "+3V3", "I2C_SDA", "I2C_SCL"], "J401 is not GND, +3V3, SDA, SCL (Qwiic order)")
    expect(j101.get(pinmap[18][0]) == jv.get("3") and j101.get(pinmap[19][0]) == jv.get("4"), "J401 SDA/SCL are not Teensy 18/19")

    # ---- (d) microphone ----
    expect('{{"Tipo mic", "Mic type"}, MK_ENUM, M_MIC_TYPE' in src, 'menu "Tipo mic" missing')
    expect("write(0x002A, (bias ? 0x0170 : 0x0070) | pre)" in src, "CHIP_MIC_CTRL (0x002A): bias bits (0x0170 = 2 k + 3.0 V) changed")
    expect("MIC_SHORT_V = 0.10f, MIC_OPEN_V = 2.85f" in src, "MIC_DET short / open thresholds are not 0.10 V / 2.85 V")
    expect("MIC_DYN_UP_V = 0.85f, MIC_DYN_DOWN_V = 0.95f" in src, "MIC_DET dynamic / electret thresholds are not 0.85 V / 0.95 V")
    parts = {}
    for ref in ("R305", "R306", "C310", "C311"):
        f = board.FindFootprintByReference(ref)
        parts[ref] = (f.GetValue(), f.GetFieldText("Montagem"), {p.GetNumber(): p.GetNetname() for p in f.Pads()})
    expect(parts["R305"][0] == "0" and parts["R305"][2] == {"1": "MIC_BIAS", "2": "MIC_J"}, "R305 is not 0 ohm between MIC_BIAS and MIC_J")
    expect(parts["C310"][1] == "nao montar", "C310 is not marked 'nao montar'")
    expect(parts["R306"][0] == "100k" and set(parts["R306"][2].values()) == {"MIC_J", "MIC_DET"}, "R306 is not 100 k MIC_J-MIC_DET")
    expect(parts["C311"][0] == "100nF" and set(parts["C311"][2].values()) == {"MIC_DET", "GND"}, "C311 is not 100 nF on MIC_DET")
    # divider arithmetic with R305 = 0: tip = 3.0 V - 2 k x I ; dynamic coil Rc: 3.0 x Rc / (2 k + Rc)
    notes.append("tip voltage, 2 k only: electret 0.1/0.3/0.5/1 mA = %s V; coil 150/300/600 ohm = %s V" % (
        "/".join("%.1f" % (3.0 - 2000 * i * 1e-3) for i in (0.1, 0.3, 0.5, 1.0)),
        "/".join("%.2f" % (3.0 * r / (2000 + r)) for r in (150, 300, 600))))
    notes.append("MIC_DET filter R306 x C311 = %.0f ms" % (100e3 * 100e-9 * 1e3))

    ok = not problems
    out = {"placa": os.path.relpath(boardfile, HERE), "pinos_conferidos": len(checked), "pinos_ok": sum(c["ok"] for c in checked),
           "problemas": problems, "notas": notes, "pinos": checked}
    json.dump(out, open(os.path.join(HERE, "firmware_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("board: %s" % out["placa"])
    print("%d/%d pins checked (sketch x PINOS.md x board x netlist), %d problems" % (out["pinos_ok"], out["pinos_conferidos"], len(problems)))
    for n in notes:
        print("  note:", n)
    for p in problems:
        print("  PROBLEM:", p)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
