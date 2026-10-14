#!/usr/bin/env python3
"""eTuttino PCB/plate generator — single source of truth for the geometry.

Run:  python generate.py        (no third-party packages needed)

Writes, next to this file:
  build/etuttino_keys.csv          every key: switch, sensor, note, mux channel, x/y in mm
  build/etuttino_plate.dxf         switch plate for laser cutting (mm)
  build/etuttino_pcb_preview.svg   top view: outline, keys, muxes, Teensy zone

The routed KiCad board and the fabrication files come from build_pcb.py,
which imports this module (run it with KiCad's Python).

Layout: chromatic button accordion, C-griff, 44 keys: row 1 A3..D#6,
row 2 G3..E6, row 3 G#3..D6, row 4 A3..C6 (row 4 sits on row 2's columns:
its A3 above row 2's A#3, its C6 above C#6). The keys are Gateron
magnetic (Hall-effect) switches: every key has a TI DRV5056 linear Hall
sensor on the BACK of the board, straight under the switch's magnet; three
CD74HC4067 16:1 analog multiplexers feed the 44 sensor voltages to three
Teensy ADC pins, so the firmware knows how far down each key is (and so
how fast it was pressed: velocity).

Geometry (case SPEC v7, etutti/hardware/case/): the keys sit on a
hexagonal grid, every button 18.5 mm from its six neighbours (rows 16.02
apart), and the board is the case's inner outline less 0.5 mm, notched
round the screw bosses. All of it comes from case/out/pcb_envelope.json,
which the case's pcb_envelope.py writes (CadQuery); this module only
reads it. Coordinates are the case SPEC's: x from the case's left face,
y towards the player, mm -- which is KiCad's top view as it stands.

The Teensy 4.0 + Audio Board stack sits in the back-left corner of the
interface area, USB to the left face, where case/fit_check.py placed and
checked it. The volume pot, the encoder and the power LED live on a small
controls board under the interface lid (not this board): it plugs into
J3 here. The three multiplexers lie on the back: U51 in front of the
interface, left of rows 1-2; U52 and U53 in the strip behind row 4.

Keep in sync with ROWS in etutti/script.js and FIRST_NOTE / FIRST_COL /
KEY_INPUT in etutti/firmware/etutti_synth/etutti_synth.ino
(`python generate.py` prints the KEY_INPUT table the firmware needs;
build_pcb.py checks the routed board against the firmware's copy).
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
ENVELOPE_PATH = os.path.join(HERE, "case", "out", "pcb_envelope.json")
with open(ENVELOPE_PATH, encoding="utf-8") as _f:
    ENV = json.load(_f)

U = ENV["pitch"]          # button pitch, the same to all six neighbours (18.5)
ROW_PITCH = ENV["row_pitch"]   # 16.02
CUTOUT = ENV["plate_cutout"]   # MX plate cutout
HOLE_D = 2.2              # M2 clearance
PCB_THICKNESS = ENV["pcb_thickness"]   # thinner board = sensor closer to the magnet

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (first MIDI note, key count, x offset in key units, first column).
# "Row"/"column" are the note grid the firmware and the page share (there
# is no electrical matrix: every key has its own sensor). Rows 2 and 4 sit
# half a key left / right of rows 1 and 3; within a row the column goes up
# by one per key.
ROWS = [
    (57, 11, 0.0, 1),   # row 1: A3 .. D#6
    (55, 12, -0.5, 0),  # row 2: G3 .. E6
    (56, 11, 0.0, 1),   # row 3: G#3 .. D6
    (57, 10, 0.5, 1),   # row 4: A3 .. C6, on row 2's columns (A3 above A#3, C6 above C#6)
]
GRID_COLS = 12            # note-grid columns (row 2 has 12 keys)

# Teensy 4.0 edge pins, top view with USB up. Left column top->bottom,
# right column top->bottom (pad 1 = top).
TEENSY_LEFT = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
TEENSY_RIGHT = ["VIN", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13"]
# Teensy pins (all on the two edge headers, clear of the Audio Board Rev D:
# 7, 8, 18-21, 23, and of its SD card, 10-13):
SEL_PINS = ["0", "1", "2", "3"]        # multiplexer address S0..S3, shared by all three
COM_PINS = ["14", "15", "16"]          # multiplexer 1..3 output -> A0, A1, A2
LED_PINS = {"4": "LED_R_DRV", "5": "LED_G_DRV"}  # bicolour power LED, through 330 ohm
# The controls board (pot, encoder, LED) under the interface lid, through
# J3. The firmware doesn't read the pot or encoder yet; these are the free
# pins kept for them (22 = A8 for the pot; 6 is the Audio Board's optional
# memory chip select: leave that chip unfitted).
CONTROL_PINS = {"22": "POT", "17": "ENC_A", "9": "ENC_B", "6": "ENC_SW"}
AUDIO_PINS = {"7", "8", "18", "19", "20", "21", "23"}  # Audio Board Rev D
# J3, JST PH 2.0 mm 8-pin vertical: pin -> net
J3_PINS = {1: "VCC", 2: "GND", 3: "POT", 4: "ENC_A", 5: "ENC_B", 6: "ENC_SW", 7: "LED_R", 8: "LED_G"}

# CD74HC4067 pin functions (SOIC-24). Channel n is "I<n>".
MUX_PINS = {1: "COM", 2: "I7", 3: "I6", 4: "I5", 5: "I4", 6: "I3", 7: "I2", 8: "I1", 9: "I0",
            10: "S0", 11: "S1", 12: "GND", 13: "S3", 14: "S2", 15: "E", 16: "I15", 17: "I14",
            18: "I13", 19: "I12", 20: "I11", 21: "I10", 22: "I9", 23: "I8", 24: "VCC"}
MUX_CHANNELS = 16

# ---- the board, from the case ----
OUTLINE = [tuple(p) for p in ENV["outline"]]               # closed polygon (last point != first)
PLATE_OUTLINE = [tuple(p) for p in ENV["plate_outline"]]
PCB_W = math.ceil(max(x for x, _ in OUTLINE)) + 1.0         # bounding box (grid, preview)
PCB_H = math.ceil(max(y for _, y in OUTLINE)) + 1.0
ROW_Y = {k["row"]: k["y"] for k in ENV["keys"]}             # accordion row 1..4 -> y
KEY_O = min(k["x"] for k in ENV["keys"] if k["row"] == 1)   # x of xp = 0 (row 1's A3)
SUPPORTS = [(s["x"], s["y"], s["r"]) for s in ENV["supports"]]   # bottom-plate pillars: no parts on the back
BOSSES = [(b["x"], b["y"], b["r"]) for b in ENV["boss_keepouts"]]


def level(h):
    """Polygons where parts on top up to h mm tall fit (case levels)."""
    keys_ = sorted(ENV["levels"], key=float)
    best = [k for k in keys_ if float(k) >= h - 1e-9]
    return [[tuple(p) for p in poly] for poly in ENV["levels"][best[0]]]


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
        t = max(0.0, min(1.0, ((p[0] - x0) * dx + (p[1] - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - x0 - t * dx, p[1] - y0 - t * dy))
    return best


# ---- the Teensy + Audio Board stack (case/fit_check.py's position) ----
_ST = ENV["stack"]
AUDIO_ZONE = tuple(_ST["audio_board"])                      # x0, y0, x1, y1
STACK_X0 = AUDIO_ZONE[0]
AUDIO_PAST_USB = round(_ST["pin1_x"] - AUDIO_ZONE[0], 3)    # Audio Board edge to pin 1, USB end
AUDIO_PAST_END = round(AUDIO_ZONE[2] - (_ST["pin1_x"] + 13 * 2.54), 3)
AUDIO_PAST_VIN = round(_ST["pin_rows_y"][0] - AUDIO_ZONE[1], 3)
AUDIO_PAST_JACK = round(AUDIO_ZONE[3] - _ST["pin_rows_y"][1], 3)
STACK_CX = round(_ST["pin1_x"] + 6.5 * 2.54, 3)
STACK_CY = round((_ST["pin_rows_y"][0] + _ST["pin_rows_y"][1]) / 2, 3)
STACK_ZONE = AUDIO_ZONE

# Multiplexers, on the back. U51 (rot 180: address pins up, towards the
# Teensy) in front of the interface, left of rows 1 and 2, takes row 1 and
# the left end of row 2. U52 and U53 lie sideways (rot 90) in the strip
# behind row 4 and take the rest, split left / right.
FIRST_X = {r: KEY_O + ROWS[r - 1][2] * U for r in (1, 2, 3, 4)}   # first key's x per accordion row
MUXES = [
    {"ref": "U51", "x": round(FIRST_X[2] - 17.5, 2), "y": round(ROW_Y[1] + 2.0, 2)},
    {"ref": "U52", "x": round(KEY_O + 2.25 * U, 2), "y": 0.0, "rot": 90, "cap": (10.0, 0.0, 90)},
    {"ref": "U53", "x": round(KEY_O + 7.25 * U, 2), "y": 0.0, "rot": 90, "cap": (10.0, 0.0, 90)},
]
_strip = (min(y for _, y in OUTLINE) + ROW_Y[4] - 5.0) / 2      # middle of the strip behind row 4's 3.3 V bus
MUXES[1]["y"] = MUXES[2]["y"] = round(_strip, 2)
FRONT_ROW2_KEYS = 5               # row 2 keys (leftmost) that go to U51 with row 1
U53_KEYS = 16                     # U53 takes the right 16
# The power LED is on the controls board; its 330 ohm resistors stay here,
# between the Teensy's pins 4 / 5 and J3.
LED_RES = {"x": round(STACK_CX + 6.0, 2), "y": round(AUDIO_ZONE[3] + 4.0, 2)}
# J3 to the controls board: in front of the Audio Board, under the lid
# (the JST PH housing and plug are ~6.5 mm tall).
J3 = {"ref": "J3", "x": round(AUDIO_ZONE[0] + 6.0, 2), "y": round(AUDIO_ZONE[3] + 6.5, 2), "height": 6.5}
# 3.3 V regulator for the sensors and multiplexers: on the back, under the
# stack, between the two pin rows, input pins towards the VIN row.
LDO = {"ref": "U60", "x": round(STACK_CX - 2.0, 2), "y": STACK_CY, "rot": 180}


def note_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def mux_pin_offset(pin):
    """(dx, dy) of a CD74HC4067 pad from the multiplexer centre, as placed:
    on the back (mirrored) and rotated 180 deg -- the net effect is a
    mirror about the horizontal axis of the stock SOIC-24W footprint
    (pins 1-12 down the left side top to bottom, 13-24 up the right).
    build_pcb.py asserts this against KiCad's real pad positions."""
    if pin <= 12:
        return (-4.65, 6.985 - (pin - 1) * 1.27)
    return (4.65, -6.985 + (pin - 13) * 1.27)


def channel_pin(ch):
    return [p for p, f in MUX_PINS.items() if f == "I%d" % ch][0]


def keys():
    out = []
    n = 0
    for r, (first, count, x0, col0) in enumerate(ROWS):
        for i in range(count):
            n += 1
            out.append({
                "ref": f"SW{n}",
                "sensor": f"U{n}",
                "cap": f"C{n}",
                "row": r,
                "col": col0 + i,
                "note": first + 3 * i,
                "cx": round(KEY_O + (x0 + i) * U, 4),
                "cy": ROW_Y[r + 1],
            })
    assign_channels(out)
    return out


def assign_channels(ks):
    """Gives every key a multiplexer and a provisional channel (the router
    in build_pcb.py then lets each sensor output take whichever free
    channel of its multiplexer it reaches best, and writes the final table
    into the firmware and the CSV). Keys left of a
    multiplexer go to the channels on its left side, the rest to its right
    side (at most 8 a side). On each side the key furthest out gets the
    channel pin nearest the top, so traces coming in from the keys can
    turn towards the chip without crossing."""
    row2 = sorted((k for k in ks if k["row"] == 1), key=lambda k: k["cx"])
    front = [k for k in ks if k["row"] == 0] + row2[:FRONT_ROW2_KEYS]
    rest = sorted((k for k in ks if k not in front), key=lambda k: (k["cx"], k["cy"]))
    split = len(rest) - U53_KEYS
    groups = [front, rest[:split], rest[split:]]  # U51, U52 (left), U53 (right)
    for m, mux in enumerate(MUXES):
        group = sorted(groups[m], key=lambda k: (k["cx"], k["cy"]))
        assert len(group) <= MUX_CHANNELS, (mux["ref"], len(group))
        n_left = sum(1 for k in group if k["cx"] < mux["x"])
        n_left = min(8, max(n_left, len(group) - 8))
        left, right = group[:n_left], group[n_left:][::-1]
        # left side, top to bottom: I0, I1, ..., I7; right: I15, I14, ..., I8
        for i, k in enumerate(left):
            k["mux"], k["ch"] = m, i
        for i, k in enumerate(right):
            k["mux"], k["ch"] = m, 15 - i
    assert all("mux" in k for k in ks), "a key has no multiplexer"


def firmware_key_table(ks):
    """The KEY_INPUT table for etutti_synth.ino: per note-grid cell,
    multiplexer * 16 + channel, or -1 where there is no key."""
    table = [[-1] * GRID_COLS for _ in ROWS]
    for k in ks:
        table[k["row"]][k["col"]] = k["mux"] * MUX_CHANNELS + k["ch"]
    rows = ",\n".join("  {%s}" % ", ".join("%3d" % v for v in row) for row in table)
    return "const int8_t KEY_INPUT[LAYOUT_ROWS][LAYOUT_COLS] = {\n%s,\n};" % rows


def plate_outline():
    """The plate as a closed polygon (the case's switch-plate edge)."""
    return PLATE_OUTLINE + PLATE_OUTLINE[:1]


def in_plate(x, y):
    return point_in_poly((x, y), PLATE_OUTLINE)


def mounting_holes():
    """None on the board: the case clamps it -- the lid presses the plate's
    edge, the plate the switches, the switches' bottom housings the board,
    and the board rests on the bottom plate's pillars (SUPPORTS). The board
    is notched round the case's screw bosses (OUTLINE)."""
    return []


def stack_pins():
    """(socket, pad, teensy_pin, x, y) for the two 1x14 rows.
    Rotating the USB-up top view 90 deg anticlockwise puts USB to the left:
    the left column becomes the front row (pad 1 at the left end), the
    right column the back row."""
    out = []
    for i in range(14):
        x = STACK_CX - 6.5 * 2.54 + i * 2.54
        out.append(("J1", i + 1, TEENSY_LEFT[i], x, STACK_CY + 7.62))
        out.append(("J2", i + 1, TEENSY_RIGHT[i], x, STACK_CY - 7.62))
    return out


def pin_net(pin):
    if pin in LED_PINS:
        return LED_PINS[pin]
    if pin in CONTROL_PINS:
        return CONTROL_PINS[pin]
    if pin in SEL_PINS:
        return f"SEL{SEL_PINS.index(pin)}"
    if pin in COM_PINS:
        return f"COM{COM_PINS.index(pin)}"
    if pin in ("GND", "VIN"):
        return pin
    return None


# ---------------------------------------------------------------- outputs
def write_csv(ks):
    path = os.path.join(BUILD, "etuttino_keys.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["switch", "sensor", "row", "col", "mux", "mux_channel", "mux_pin", "teensy_pin", "midi", "note", "x_mm", "y_mm"])
        for k in ks:
            w.writerow([k["ref"], k["sensor"], k["row"], k["col"], MUXES[k["mux"]]["ref"], k["ch"],
                        channel_pin(k["ch"]), "A%d (pin %s)" % (k["mux"], COM_PINS[k["mux"]]),
                        k["note"], note_name(k["note"]), f"{k['cx']:.3f}", f"{k['cy']:.3f}"])
    return path


def write_dxf(ks):
    """Plain DXF R12 (LINE only) — opens in any laser/CNC tool."""
    ox = min(x for x, _ in PLATE_OUTLINE)
    oy = min(y for _, y in PLATE_OUTLINE)
    ph = max(y for _, y in PLATE_OUTLINE) - oy
    pw = max(x for x, _ in PLATE_OUTLINE) - ox
    ents = []

    def line(x1, y1, x2, y2, layer):
        # DXF y grows upward: flip so the plate reads like the top view.
        ents.append(f"0\nLINE\n8\n{layer}\n10\n{x1 - ox:.4f}\n20\n{ph - (y1 - oy):.4f}\n30\n0\n11\n{x2 - ox:.4f}\n21\n{ph - (y2 - oy):.4f}\n31\n0\n")

    pts = plate_outline()
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        line(ax, ay, bx, by, "OUTLINE")
    for k in ks:
        x0, y0 = k["cx"] - CUTOUT / 2, k["cy"] - CUTOUT / 2
        x1, y1 = x0 + CUTOUT, y0 + CUTOUT
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            line(*a, *b, "CUTOUTS")
    path = os.path.join(BUILD, "etuttino_plate.dxf")
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write("0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n")
        f.write("0\nSECTION\n2\nENTITIES\n")
        f.write("".join(ents))
        f.write("0\nENDSEC\n0\nEOF\n")
    return path, pw, ph


def write_svg(ks):
    s = 4  # px per mm
    w, h = PCB_W * s, PCB_H * s
    legend_h = 130
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 20:.0f} {h + 20 + legend_h:.0f}" font-family="Inter, Arial, sans-serif">')
    o.append(f'<rect x="0" y="0" width="{w + 20:.0f}" height="{h + 20 + legend_h:.0f}" fill="#f6f1e8"/>')
    o.append('<g transform="translate(10 10)">')
    pts = " ".join(f"{x * s:.1f},{y * s:.1f}" for x, y in OUTLINE)
    o.append(f'<polygon points="{pts}" fill="#1f5e3a" stroke="#0d2c1b" stroke-width="2"/>')
    pts = " ".join(f"{x * s:.1f},{y * s:.1f}" for x, y in plate_outline())
    o.append(f'<polyline points="{pts}" fill="none" stroke="#9fc3ad" stroke-width="2" stroke-dasharray="10 6"/>')
    zx0, zy0, zx1, zy1 = STACK_ZONE
    o.append(f'<rect x="{zx0 * s:.1f}" y="{zy0 * s:.1f}" width="{(zx1 - zx0) * s:.1f}" height="{(zy1 - zy0) * s:.1f}" rx="6" fill="none" stroke="#e8d9a8" stroke-dasharray="8 6" stroke-width="2"/>')
    o.append(f'<text x="{(zx0 + 1.5) * s:.1f}" y="{(zy0 + 4.5) * s:.1f}" font-size="12" fill="#e8d9a8">Teensy 4.0 + Audio Rev D (USB to the left face)</text>')
    for sock, pad, pin, x, y in stack_pins():
        net = pin_net(pin)
        color = "#f2c27a" if net and net not in ("GND", "VIN") else ("#7aa0c8" if pin in AUDIO_PINS else "#b9c4bd")
        o.append(f'<circle cx="{x * s:.1f}" cy="{y * s:.1f}" r="4.5" fill="{color}"/>')
        o.append(f'<text x="{x * s:.1f}" y="{(y + (4.6 if sock == "J1" else -2.6)) * s:.1f}" font-size="8" fill="#f6f1e8" text-anchor="middle">{pin}</text>')
    for k in ks:
        sharp = "#" in note_name(k["note"])
        o.append(f'<circle cx="{k["cx"] * s:.1f}" cy="{k["cy"] * s:.1f}" r="{7.5 * s:.1f}" fill="{"#3a3d42" if sharp else "#f4efe6"}" stroke="#0d2c1b"/>')
        tc = "#f4efe6" if sharp else "#2f2218"
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] - 0.5) * s:.1f}" font-size="15" font-weight="700" fill="{tc}" text-anchor="middle">{note_name(k["note"])}</text>')
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] + 4.0) * s:.1f}" font-size="9" fill="{tc}" text-anchor="middle" opacity="0.7">{k["ref"]} · M{k["mux"] + 1}/{k["ch"]}</text>')
    for i, mux in enumerate(MUXES):
        hw, hh = (7.7, 5.2) if mux.get("rot", 180) in (90, 270) else (5.2, 7.7)
        o.append(f'<rect x="{(mux["x"] - hw) * s:.1f}" y="{(mux["y"] - hh) * s:.1f}" width="{2 * hw * s}" height="{2 * hh * s}" rx="3" fill="#2b2b2b" stroke="#e8d9a8" stroke-dasharray="5 4"/>')
        o.append(f'<text x="{mux["x"] * s:.1f}" y="{(mux["y"] + 1) * s:.1f}" font-size="12" fill="#e8d9a8" text-anchor="middle">{mux["ref"]}</text>')
    o.append(f'<rect x="{(J3["x"] - 1) * s:.1f}" y="{(J3["y"] - 2) * s:.1f}" width="{16 * s}" height="{4 * s}" fill="none" stroke="#e8d9a8"/>')
    o.append(f'<text x="{(J3["x"] + 7) * s:.1f}" y="{(J3["y"] + 6) * s:.1f}" font-size="10" fill="#e8d9a8" text-anchor="middle">J3 controls board</text>')
    for x, y, r in SUPPORTS:
        o.append(f'<circle cx="{x * s:.1f}" cy="{y * s:.1f}" r="{r * s:.1f}" fill="none" stroke="#7aa0c8" stroke-dasharray="4 3"/>')
    o.append("</g>")
    lines = [
        ("eTuttino PCB (Hall effect, case v7) — top view", 18, "700"),
        (f"{len(ks)} keys · C-griff G3–E6 · hex grid, pitch {U} mm, rows {ROW_PITCH:.2f} mm apart · board {PCB_THICKNESS} mm, shaped to the case", 13, "400"),
        (f"{len(ks)} × Gateron magnetic switch (no pins) · {len(ks)} × DRV5056A3 sensor on the BACK · 3 × CD74HC4067 + AMS1117-3.3 on the back (dashed)", 13, "400"),
        ("Key label: switch · MUX/channel · - - - plate edge · dashed blue: bottom-plate pillars (no parts on the back there)", 13, "400"),
        ("Mux address S0..S3 → pins " + ", ".join(SEL_PINS) + " · MUX1/2/3 output → pins " + ", ".join(COM_PINS) + " · J3: pot 22, encoder 17/9/6, LED 4/5", 13, "400"),
    ]
    y = h + 40
    for text, size, weight in lines:
        o.append(f'<text x="14" y="{y:.0f}" font-size="{size}" font-weight="{weight}" fill="#2f2218">{text}</text>')
        y += size + 7
    o.append("</svg>")
    path = os.path.join(BUILD, "etuttino_pcb_preview.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    return path


def main():
    os.makedirs(BUILD, exist_ok=True)
    ks = keys()
    assert len(ks) == 44
    assert len({(k["row"], k["col"]) for k in ks}) == len(ks)       # one key per grid cell
    assert len({(k["mux"], k["ch"]) for k in ks}) == len(ks)        # one sensor per mux channel
    assert not (set(SEL_PINS + COM_PINS) & AUDIO_PINS)            # no clash with the Audio Board
    assert not (set(CONTROL_PINS) & (AUDIO_PINS | set(SEL_PINS) | set(COM_PINS) | set(LED_PINS)))
    # the keys are the case's
    env_keys = {(k["row"], round(k["x"], 3)) for k in ENV["keys"]}
    assert {(k["row"] + 1, round(k["cx"], 3)) for k in ks} == env_keys, "keys differ from the case envelope"
    # everything placed lies inside the board, 0.6 mm clear of its edge
    # (boxes: the switch footprint, the multiplexers with their pads, the
    # sockets' pin rows, J3)
    boxes = [(k["ref"], k["cx"], k["cy"], 7.3, 7.3) for k in ks]
    boxes += [(mx["ref"], mx["x"], mx["y"], *((7.9, 5.4) if mx.get("rot", 180) in (90, 270) else (5.4, 7.9))) for mx in MUXES]
    boxes += [("J1/J2", STACK_CX, STACK_CY, 6.5 * 2.54 + 1.3, 7.62 + 1.3), ("J3", J3["x"] + 7.0, J3["y"], 9.0, 3.0)]
    for name, x, y, hw, hh in boxes:
        for px in (x - hw, x, x + hw):
            for py in (y - hh, y, y + hh):
                assert point_in_poly((px, py), OUTLINE) and dist_to_poly((px, py), OUTLINE) >= 0.6, (name, px, py)
    # the stack and J3 sit where the case leaves them room
    assert all(point_in_poly(p, level(17.0)[0]) for p in ((STACK_ZONE[0], STACK_ZONE[1]), (STACK_ZONE[2], STACK_ZONE[3]))), "stack"
    assert point_in_poly((J3["x"], J3["y"]), level(J3["height"])[0]), "J3"
    print(write_csv(ks))
    dxf, pw, ph = write_dxf(ks)
    print(dxf, f"(plate {pw:.2f} x {ph:.2f} mm)")
    print(write_svg(ks))
    sharps = sum(1 for k in ks if "#" in note_name(k["note"]))
    print(f"PCB bbox {PCB_W:.1f} x {PCB_H:.1f} mm; keycaps: {len(ks) - sharps} light, {sharps} dark")
    for m, mux in enumerate(MUXES):
        print(mux["ref"], (mux["x"], mux["y"]), "keys:", sum(1 for k in ks if k["mux"] == m))
    print(firmware_key_table(ks))


if __name__ == "__main__":
    main()
