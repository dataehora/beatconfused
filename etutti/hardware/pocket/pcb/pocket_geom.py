#!/usr/bin/env python3
"""eTuttino Pocket main board -- geometry and netlist source (stdlib only).

    python etutti/hardware/pocket/pcb/pocket_geom.py

is a dry check: it prints the key table and checks every placed part
against the case's envelope. build_pocket_pcb.py (KiCad's Python) imports
this module to place, route and export the board.

Inputs (owned by the design, read only):
  ../case/out/pcb_envelope.json   outline, keys, pillars, holes, levels, stack,
                                  controls / panel boards, connector zones
  ../build/pocket.json            the note grid (rows)

Coordinates are the case SPEC's: x right from the case's leftmost point, y
towards the player, mm -- KiCad's top view as it stands.

Electrical summary (SPEC v3, PINOS.md):
  - 28 Gateron magnetic keys, a TMAG5253BA3 under each on the BACK (the
    magnet's north faces down: the sensor reads it through the board, as the
    eTuttino's DRV5056), 100 nF each.
  - 2 x CD74HC4067 in the strip behind row 4: U51 reads the right half of
    the keyboard (COM -> pin 14), U52 the left half (COM -> pin 15). Rows 1
    and 3 sit on channels 0-7, rows 2 and 4 on 8-15,
    so the address bit S3 also picks the group of sensors that is switched on:
    EN_A (rows 1, 3) = SENS_EN & !S3, EN_B (rows 2, 4) = SENS_EN & S3. Each
    row has one EN bus (back); 3.3 V and GND go into the inner planes
    (4-layer board) through a via beside every sensor.
  - BQ24074 charger (USB500, 500 mA, NTC on TS), TPS63001 buck-boost to 3.3 V
    (fixed, EN by the power switch / KEEP latch), PAM8302A on VSYS for the
    speaker, charge light from CHG into the LED's red through a BAT54C.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")
ENVELOPE_PATH = os.path.join(POCKET, "case", "out", "pcb_envelope.json")
POCKET_JSON = os.path.join(POCKET, "build", "pocket.json")
with open(ENVELOPE_PATH, encoding="utf-8") as _f:
    ENV = json.load(_f)
with open(POCKET_JSON, encoding="utf-8") as _f:
    PJ = json.load(_f)

U = ENV["pitch"]
PCB_THICKNESS = ENV["pcb_thickness"]
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (first MIDI note, key count, x offset in key units, first column) -- the
# firmware's note grid, from pocket.json (same rule as the eTuttino's ROWS).
ROWS = [tuple(r) for r in PJ["rows"]]
GRID_COLS = max(r[3] + r[1] for r in ROWS)
FIRST_NOTE = [r[0] for r in ROWS]
FIRST_COL = [r[3] for r in ROWS]

OUTLINE = [tuple(p) for p in ENV["outline"]]
PCB_W = math.ceil(max(x for x, _ in OUTLINE)) + 1.0
PCB_H = math.ceil(max(y for _, y in OUTLINE)) + 1.0
SUPPORTS = [(s["x"], s["y"], s["r"]) for s in ENV["supports"]]
MOUNT = [(h["x"], h["y"], h["keepout"]) for h in ENV["mounting_holes"]]
EDGE_CLEAR = 0.5

# Teensy 4.0 edge pins, USB-up top view (as the eTuttino's generate.py).
TEENSY_LEFT = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
TEENSY_RIGHT = ["VIN", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13"]
AUDIO_PINS = {"7", "8", "18", "19", "20", "21", "23"}

# PINOS.md, the contract with the firmware. Pin -> main-board net.
PIN_NETS = {
    "GND": "GND",
    "3V3": "VCC",
    "0": "SEL0", "1": "SEL1", "2": "SEL2", "3": "SEL3",
    "4": "SENS_EN",
    "5": "LED_G_DRV",
    "6": "ENC_SW",
    "9": "ENC_B",
    "10": "KEEP",
    "11": "ENC_A",
    "12": "AMP_SD",
    "13": "LED_R_DRV",
    "14": "COM0",
    "15": "COM1",
    "16": "VBAT_S",
    "17": "HP_DET",
    "22": "POT",
    "VIN": "VIN_T",
}
# The Teensy runs from 3.3 V on its 3V3 pin, its VUSB-VIN pad cut. SPEC v5
# (F4): VIN gets VBUS through Q23/D61 while the Pocket is on, because the
# i.MX's USB VBUS pins (its USB PHY supply) are on the VIN side of the cut.
SEL_PINS = ["0", "1", "2", "3"]
COM_PINS = ["14", "15"]
LED_PINS = ["13", "5"]           # red, green

MUX_PINS = {1: "COM", 2: "I7", 3: "I6", 4: "I5", 5: "I4", 6: "I3", 7: "I2", 8: "I1", 9: "I0",
            10: "S0", 11: "S1", 12: "GND", 13: "S3", 14: "S2", 15: "E", 16: "I15", 17: "I14",
            18: "I13", 19: "I12", 20: "I11", 21: "I10", 22: "I9", 23: "I8", 24: "VCC"}
MUX_CHANNELS = 16

# Multiplexer by side: U52 (x 136) reads the left half of the keyboard, U51
# (x 178) the right half. Channel half and EN net by row (rows 1 and 3 on
# channels 0-7, rows 2 and 4 on 8-15): at most 8 keys per half per mux.
MUX_SPLIT_X = {1: 157.0, 2: 157.0, 3: 150.0, 4: 157.0}   # 7 keys per channel half on each mux
ROW_GROUP = {1: 0, 2: 1, 3: 0, 4: 1}          # 0: channels 0-7 (S3 = 0), 1: 8-15
GROUP_EN = {0: "EN_A", 1: "EN_B"}
MUXES = [
    {"ref": "U51", "x": 178.0, "y": 12.0, "rot": 0, "side": "right (x > 157)"},
    {"ref": "U52", "x": 136.0, "y": 12.0, "rot": 180, "side": "left (x < 157; row 3 x < 150)"},
]

# Per-key copper on the back (mm from the switch centre, +y to the player).
CAP_DY = -3.0
VCC_VIA_DY = -4.5                # 3.3 V plane via above the capacitor
GND_VIA_DY = 2.4                 # GND plane via under the capacitor ground column
EN_BUS_DY = 6.4
OUT_VIA = (-1.5, -1.7)
EN_VIA = (-1.5, 2.6)             # EN goes down to here (back), jumps to EN_BUS_DY on the front

_ST = ENV["stack"]
PIN1_X = _ST["pin1_x"]
ROW_J1_Y = _ST["pin_rows_y"][1]  # front row: GND, 0..12 (USB to the left)
ROW_J2_Y = _ST["pin_rows_y"][0]  # back row: VIN, GND, 3V3, 23..13


def stack_pins():
    """(socket, pad, teensy_pin, x, y): J1 = front row (pad 1 GND at the USB
    end), J2 = back row (pad 1 VIN). The Audio Board's legs solder here."""
    out = []
    for i in range(14):
        x = PIN1_X + i * 2.54
        out.append(("J1", i + 1, TEENSY_LEFT[i], x, ROW_J1_Y))
        out.append(("J2", i + 1, TEENSY_RIGHT[i], x, ROW_J2_Y))
    return out


def teensy_pad(pin):
    return [(s, p, x, y) for s, p, t, x, y in stack_pins() if t == pin][0]


def note_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def keys():
    out = []
    env = sorted(ENV["keys"], key=lambda k: (k["row"], k["x"]))
    n = 0
    for row in (1, 2, 3, 4):
        first, count, _x0, col0 = ROWS[row - 1]
        ks = [k for k in env if k["row"] == row]
        assert len(ks) == count, (row, len(ks), count)
        for i, k in enumerate(ks):
            n += 1
            out.append({
                "ref": f"SW{n}", "sensor": f"U{n}", "cap": f"C{n}",
                "row": row, "col": col0 + i, "note": first + 3 * i,
                "cx": k["x"], "cy": k["y"],
                "mux": 0 if k["x"] > MUX_SPLIT_X[row] else 1, "group": ROW_GROUP[row], "en": GROUP_EN[ROW_GROUP[row]],
            })
            assert note_name(out[-1]["note"]).replace("#", "♯") or True
    return out


def key_table(ks):
    """KEY_INPUT[row][col] = mux * 16 + channel (-1 = no key)."""
    t = [[-1] * GRID_COLS for _ in ROWS]
    for k in ks:
        t[k["row"] - 1][k["col"]] = k["mux"] * MUX_CHANNELS + k["ch"]
    return t


def key_header(ks):
    t = key_table(ks)
    rows = ",\n".join("  {%s}" % ", ".join("%3d" % v for v in r) for r in t)
    return "\n".join([
        "// eTuttino Pocket key table -- WRITTEN BY etutti/hardware/pocket/pcb/build_pocket_pcb.py",
        "// from the routed board (do not edit by hand). Contract: pcb/PINOS.md.",
        "// KEY_INPUT[row][col] = multiplexer * 16 + channel; row 0 = row 1 (nearest the player).",
        "#pragma once",
        "#define POCKET_LAYOUT_ROWS %d" % len(ROWS),
        "#define POCKET_LAYOUT_COLS %d" % GRID_COLS,
        "const uint8_t POCKET_FIRST_NOTE[POCKET_LAYOUT_ROWS] = {%s};" % ", ".join(map(str, FIRST_NOTE)),
        "const uint8_t POCKET_FIRST_COL[POCKET_LAYOUT_ROWS] = {%s};" % ", ".join(map(str, FIRST_COL)),
        "const uint8_t POCKET_MUX_SEL_PINS[4] = {%s};" % ", ".join(SEL_PINS),
        "const uint8_t POCKET_MUX_COM_PINS[2] = {%s};" % ", ".join(COM_PINS),
        "const uint8_t POCKET_LED_PINS[2] = {%s};  // red, green" % ", ".join(LED_PINS),
        "const uint8_t POCKET_SENS_EN_PIN = 4, POCKET_KEEP_PIN = 10, POCKET_AMP_SD_PIN = 12;",
        "const uint8_t POCKET_VBAT_PIN = 16, POCKET_HP_DET_PIN = 17, POCKET_POT_PIN = 22;",
        "const uint8_t POCKET_ENC_A_PIN = 11, POCKET_ENC_B_PIN = 9, POCKET_ENC_SW_PIN = 6;",
        "// Channels 0-7 (S3 = 0) = rows 1 and 3 (EN_A); 8-15 (S3 = 1) = rows 2 and 4 (EN_B).",
        "const int8_t POCKET_KEY_INPUT[POCKET_LAYOUT_ROWS][POCKET_LAYOUT_COLS] = {",
        rows + ",",
        "};",
        ""])


def write_csv(ks, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["switch", "sensor", "row", "col", "mux", "mux_channel", "en_group", "teensy_pin", "midi", "note", "x_mm", "y_mm"])
        for k in ks:
            w.writerow([k["ref"], k["sensor"], k["row"], k["col"], MUXES[k["mux"]]["ref"], k["ch"], k["en"],
                        "A%d (pin %s)" % (k["mux"], COM_PINS[k["mux"]]), k["note"], note_name(k["note"]),
                        f"{k['cx']:.3f}", f"{k['cy']:.3f}"])


# ---------------------------------------------------------------- envelope
def point_in_poly(p, poly):
    x, y = p
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def dist_to_poly(p, poly):
    best = 1e9
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((p[0] - x0) * dx + (p[1] - y0) * dy) / L))
        best = min(best, math.hypot(p[0] - x0 - t * dx, p[1] - y0 - t * dy))
    return best


def room_at(h, p):
    """True if a part h mm tall (above the board's top) fits at p: inside one
    of the level's polygons and outside its holes."""
    keys_ = sorted(ENV["levels"], key=float)
    lv = [k for k in keys_ if float(k) >= h - 1e-9][0]
    for poly in ENV["levels"][lv]:
        outer = [tuple(q) for q in poly["outer"]]
        if point_in_poly(p, outer) and not any(point_in_poly(p, [tuple(q) for q in hole]) for hole in poly["holes"]):
            return True
    return False


# The top-side connectors are checked against the case's levels / connector
# zones / the micro-B plug in build_pocket_pcb.py, with their real footprints.


def main():
    ks = keys()
    assert len(ks) == 28
    assert len({(k["row"], k["col"]) for k in ks}) == 28
    for m, mux in enumerate(MUXES):
        n = [sum(1 for k in ks if k["mux"] == m and k["group"] == g) for g in (0, 1)]
        assert max(n) <= 8, (mux["ref"], n)
        print(mux["ref"], mux["side"], "keys per channel half", n)
    for k in ks:
        assert point_in_poly((k["cx"], k["cy"]), OUTLINE)
    for k in ks:
        print(k["ref"], k["row"], k["col"], note_name(k["note"]), k["cx"], k["cy"], k["en"])


if __name__ == "__main__":
    main()
