#!/usr/bin/env python3
"""eTuttino PCB/plate generator — single source of truth for the geometry.

Run:  python generate.py        (no third-party packages needed)

Writes, next to this file:
  build/etuttino_keys.csv          every key: switch, sensor, note, mux channel, x/y in mm
  build/etuttino_plate.dxf         switch plate for laser cutting (mm)
  build/etuttino_pcb_preview.svg   top view: outline, keys, sensors, muxes, Teensy zone

The routed KiCad board and the fabrication files come from build_pcb.py,
which imports this module (run it with KiCad's Python).

Layout: chromatic button accordion, C-griff, laid out like the Castagnari
Magica K2's treble keyboard: rows 1-3 run from A3 / G3 / G#3 up to D#6 /
G6 / D6, row 4 repeats row 1 from A3 to C5 (41 keys). The keys are Gateron
magnetic (Hall-effect) switches: every key has a TI DRV5056 linear Hall
sensor on the BACK of the board, straight under the switch's magnet; three
CD74HC4067 16:1 analog multiplexers feed the 41 sensor voltages to three
Teensy ADC pins, so the firmware knows how far down each key is (and so
how fast it was pressed: velocity).

Size: the board is only as tall as the four key rows. Row 4 is short, so
the space behind rows 3-4 at the right end is free: the Teensy 4.0 + Audio
Board stack sits there, USB and headphone jack facing the right edge,
which only adds about a centimetre to the length.

Keep in sync with ROWS in etutti/script.js and FIRST_NOTE / FIRST_COL /
KEY_INPUT in etutti/firmware/etutti_synth/etutti_synth.ino
(`python generate.py` prints the KEY_INPUT table the firmware needs;
build_pcb.py checks the routed board against the firmware's copy).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

U = 19.05                 # MX key pitch (mm)
MARGIN = 6.0              # PCB edge to key grid (left, top, bottom)
CUTOUT = 14.0             # MX plate cutout
PLATE_MARGIN = 6.0        # plate edge to key grid
HOLE_D = 2.2              # M2 clearance
PCB_THICKNESS = 1.2       # thinner board = sensor closer to the magnet

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (first MIDI note, key count, x offset in key units, first column).
# "Row"/"column" are the note grid the firmware and the page share (there
# is no electrical matrix: every key has its own sensor). Rows 2 sits half
# a key left of the others; within a row the column goes up by one per key.
ROWS = [
    (57, 11, 0.0, 1),   # row 1: A3 .. D#6
    (55, 13, -0.5, 0),  # row 2: G3 .. G6
    (56, 11, 0.0, 1),   # row 3: G#3 .. D6
    (57, 6, 0.0, 1),    # row 4: A3 .. C5 (repeats the start of row 1)
]
GRID_COLS = 13            # note-grid columns (row 2 has 13 keys)
GRID_UNITS = 13           # key area width in key units (x = -0.5 .. 11.5)

# Teensy 4.0 edge pins, top view with USB up. Left column top->bottom,
# right column top->bottom (pad 1 = top).
TEENSY_LEFT = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
TEENSY_RIGHT = ["VIN", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13"]
# Teensy pins (all on the two edge headers, clear of the Audio Board Rev D:
# 7, 8, 18-21, 23, and of its SD card, 10-13):
SEL_PINS = ["0", "1", "2", "3"]        # multiplexer address S0..S3, shared by all three
COM_PINS = ["14", "15", "16"]          # multiplexer 1..3 output -> A0, A1, A2
AUDIO_PINS = {"7", "8", "18", "19", "20", "21", "23"}  # Audio Board Rev D

# CD74HC4067 pin functions (SOIC-24). Channel n is "I<n>".
MUX_PINS = {1: "COM", 2: "I7", 3: "I6", 4: "I5", 5: "I4", 6: "I3", 7: "I2", 8: "I1", 9: "I0",
            10: "S0", 11: "S1", 12: "GND", 13: "S3", 14: "S2", 15: "E", 16: "I15", 17: "I14",
            18: "I13", 19: "I12", 20: "I11", 21: "I10", 22: "I9", 23: "I8", 24: "VCC"}
MUX_CHANNELS = 16

PCB_H = MARGIN + 4 * U + MARGIN
GRID_X0 = MARGIN
GRID_Y0 = MARGIN


def row_slot(r):
    """Vertical slot (0 = top) of accordion row r+1: row 1 at the bottom."""
    return len(ROWS) - 1 - r


def key_right_edge(r):
    first, count, x0, col0 = ROWS[r]
    return GRID_X0 + (x0 + count - 1 + 1.5) * U


# The plate stops just past row 3's last key in the top two slots (rows 4
# and 3); the Teensy + Audio Board stack sits in that notch.
NOTCH_X = key_right_edge(2) + 0.6
NOTCH_Y = GRID_Y0 + 2 * U          # bottom of slot 1 (row 3)

# Teensy + Audio Board stack: pin rows horizontal, USB (and the Audio
# Board's headphone jack, which sits beside the 0-12 pin row at the USB
# end) facing the right edge. Audio Board outline relative to the header
# (read off PJRC's pin diagram): 5 mm past pin 1 at the USB end, 2 mm past
# pin 14, 14 mm beyond the 0-12 row (jack side), 9.5 mm beyond the VIN row.
AUDIO_PAST_USB, AUDIO_PAST_END, AUDIO_PAST_JACK, AUDIO_PAST_VIN = 5.0, 2.0, 14.0, 9.5
STACK_CY = 23.5
STACK_CX = round(NOTCH_X + 0.8 + 6.5 * 2.54 + AUDIO_PAST_END, 2)
PCB_W = round(STACK_CX + 6.5 * 2.54 + AUDIO_PAST_USB + 0.5, 2)

# Audio Board keep-out on the top side (x0, y0, x1, y1).
STACK_ZONE = (STACK_CX - 6.5 * 2.54 - AUDIO_PAST_END, STACK_CY - 7.62 - AUDIO_PAST_JACK,
              STACK_CX + 6.5 * 2.54 + AUDIO_PAST_USB, STACK_CY + 7.62 + AUDIO_PAST_VIN)

# Multiplexers: on the back, behind the empty right part of row 4. Each
# serves a band of half-key columns (k = 1..25, see half_col()). Placed
# upside down (rotated 180 deg) so the address pins face the top edge.
ROW4_END = key_right_edge(3)
MUXES = [
    {"ref": "U51", "x": ROW4_END + 17.5, "y": 16.5, "cols": range(1, 8)},
    {"ref": "U52", "x": ROW4_END + 47.5, "y": 16.5, "cols": range(8, 15)},
    {"ref": "U53", "x": ROW4_END + 77.0, "y": 16.5, "cols": range(15, 26)},
]
# 3.3 V regulator for the sensors and multiplexers (41 sensors x 6 mA is
# more than the Teensy's own 3.3 V pin should supply): on the back, under
# the stack, between the two pin rows. Fed from VIN (USB 5 V).
LDO = {"ref": "U60", "x": STACK_CX + 2.0, "y": STACK_CY}


def note_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def half_col(cx):
    """Half-key column of a key centre: 1 (leftmost, row 2) .. 25."""
    return int(round((cx - GRID_X0) / (U / 2)))


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
            x = x0 + i
            out.append({
                "ref": f"SW{n}",
                "sensor": f"U{n}",
                "cap": f"C{n}",
                "row": r,
                "col": col0 + i,
                "note": first + 3 * i,
                "cx": GRID_X0 + (x + 1.0) * U,   # x = -0.5 -> half a key in
                "cy": GRID_Y0 + (row_slot(r) + 0.5) * U,
            })
    assign_channels(out)
    return out


def assign_channels(ks):
    """Gives every key a multiplexer and a channel. Keys left of a
    multiplexer go to the channels on its left side, the rest to its right
    side (at most 8 a side). On each side the key furthest out gets the
    channel pin nearest the top, so traces coming in from the keys can
    turn towards the chip without crossing."""
    for m, mux in enumerate(MUXES):
        group = [k for k in ks if half_col(k["cx"]) in mux["cols"]]
        assert len(group) <= MUX_CHANNELS, (mux["ref"], len(group))
        group.sort(key=lambda k: (k["cx"], k["cy"]))
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
    """The plate as a closed polygon: the key area plus margin, with a notch
    at the top right for the Teensy + Audio Board stack."""
    x0 = GRID_X0 - PLATE_MARGIN
    y0 = GRID_Y0 - PLATE_MARGIN
    x1 = GRID_X0 + GRID_UNITS * U + PLATE_MARGIN
    y1 = GRID_Y0 + 4 * U + PLATE_MARGIN
    return [(x0, y0), (NOTCH_X, y0), (NOTCH_X, NOTCH_Y), (x1, NOTCH_Y), (x1, y1), (x0, y1), (x0, y0)]


def in_plate(x, y):
    x0, y0 = GRID_X0 - PLATE_MARGIN, GRID_Y0 - PLATE_MARGIN
    x1 = GRID_X0 + GRID_UNITS * U + PLATE_MARGIN
    y1 = GRID_Y0 + 4 * U + PLATE_MARGIN
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    return not (x > NOTCH_X and y < NOTCH_Y)


def mounting_holes():
    """M2 holes (2.2 mm). Shared by plate and PCB: the plate's corners, the
    half-key gaps at the ends of rows 1 and 3, and two in the empty right
    part of row 4. PCB only (for the case): two at the far right."""
    m = MARGIN / 2
    x_plate_r = GRID_X0 + GRID_UNITS * U + PLATE_MARGIN - m
    slot = lambda r: GRID_Y0 + (row_slot(r) + 0.5) * U
    return [
        (m, m),                                   # plate + PCB
        (m, PCB_H - m),
        (NOTCH_X - m, m),
        (x_plate_r, NOTCH_Y + m),
        (x_plate_r, PCB_H - m),
        (GRID_X0 + 0.25 * U, slot(0)),            # rows 1 / 3, left gaps
        (GRID_X0 + 0.25 * U, slot(2)),
        (key_right_edge(0) + 0.5 * U, slot(0)),   # row 1, right gap
        (ROW4_END + 4.8, slot(3)),                # row 4, empty part
        (NOTCH_X - 7.5, slot(3)),
        (PCB_W - m, PCB_H - m),                   # PCB only
        (PCB_W - m, STACK_ZONE[3] + 3.2),
    ]


def stack_pins():
    """(socket, pad, teensy_pin, x, y) for the two 1x14 rows.
    Rotating the USB-up top view 90 deg clockwise puts USB to the right:
    the left column becomes the top row (pad 1 at the right end), the right
    column the bottom row."""
    out = []
    for i in range(14):
        x = STACK_CX + 6.5 * 2.54 - i * 2.54
        out.append(("J1", i + 1, TEENSY_LEFT[i], x, STACK_CY - 7.62))
        out.append(("J2", i + 1, TEENSY_RIGHT[i], x, STACK_CY + 7.62))
    return out


def pin_net(pin):
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
    """Plain DXF R12 (LINE + CIRCLE only) — opens in any laser/CNC tool."""
    ox = GRID_X0 - PLATE_MARGIN
    oy = GRID_Y0 - PLATE_MARGIN
    ph = 4 * U + 2 * PLATE_MARGIN
    pw = GRID_UNITS * U + 2 * PLATE_MARGIN
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
    for hx, hy in mounting_holes():
        if in_plate(hx, hy):
            ents.append(f"0\nCIRCLE\n8\nHOLES\n10\n{hx - ox:.4f}\n20\n{ph - (hy - oy):.4f}\n30\n0\n40\n{HOLE_D / 2:.4f}\n")

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
    legend_h = 150
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 20:.0f} {h + 20 + legend_h:.0f}" font-family="Inter, Arial, sans-serif">')
    o.append(f'<rect x="0" y="0" width="{w + 20:.0f}" height="{h + 20 + legend_h:.0f}" fill="#f6f1e8"/>')
    o.append('<g transform="translate(10 10)">')
    o.append(f'<rect width="{w:.1f}" height="{h:.1f}" rx="{3 * s}" fill="#1f5e3a" stroke="#0d2c1b" stroke-width="2"/>')
    pts = " ".join(f"{x * s:.1f},{y * s:.1f}" for x, y in plate_outline())
    o.append(f'<polyline points="{pts}" fill="none" stroke="#9fc3ad" stroke-width="2" stroke-dasharray="10 6"/>')
    zx0, zy0, zx1, zy1 = STACK_ZONE
    o.append(f'<rect x="{zx0 * s:.1f}" y="{zy0 * s:.1f}" width="{(zx1 - zx0) * s:.1f}" height="{(zy1 - zy0) * s:.1f}" rx="6" fill="none" stroke="#e8d9a8" stroke-dasharray="8 6" stroke-width="2"/>')
    o.append(f'<text x="{(zx0 + 1.5) * s:.1f}" y="{(zy1 - 2.2) * s:.1f}" font-size="12" fill="#e8d9a8">Teensy 4.0 + Audio Rev D</text>')
    o.append(f'<text x="{(zx1 - 1.5) * s:.1f}" y="{(zy0 + 4) * s:.1f}" font-size="11" fill="#e8d9a8" text-anchor="end">jack + USB →</text>')
    for sock, pad, pin, x, y in stack_pins():
        net = pin_net(pin)
        color = "#f2c27a" if net and net not in ("GND", "VIN") else ("#7aa0c8" if pin in AUDIO_PINS else "#b9c4bd")
        o.append(f'<circle cx="{x * s:.1f}" cy="{y * s:.1f}" r="4.5" fill="{color}"/>')
        o.append(f'<text x="{x * s:.1f}" y="{(y + (-2.6 if sock == "J1" else 4.6)) * s:.1f}" font-size="8" fill="#f6f1e8" text-anchor="middle">{pin}</text>')
    for k in ks:
        x, y = (k["cx"] - U / 2) * s, (k["cy"] - U / 2) * s
        sharp = "#" in note_name(k["note"])
        o.append(f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{U * s - 4:.1f}" height="{U * s - 4:.1f}" rx="{U * s / 2 - 2:.1f}" fill="{"#3a3d42" if sharp else "#f4efe6"}" stroke="#0d2c1b"/>')
        tc = "#f4efe6" if sharp else "#2f2218"
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] - 1.5) * s:.1f}" font-size="17" font-weight="700" fill="{tc}" text-anchor="middle">{note_name(k["note"])}</text>')
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] + 4.2) * s:.1f}" font-size="10" fill="{tc}" text-anchor="middle" opacity="0.7">{k["ref"]} · M{k["mux"] + 1}/{k["ch"]}</text>')
    for i, mux in enumerate(MUXES):
        o.append(f'<rect x="{(mux["x"] - 3.75) * s:.1f}" y="{(mux["y"] - 7.7) * s:.1f}" width="{7.5 * s}" height="{15.4 * s}" rx="3" fill="#2b2b2b" stroke="#e8d9a8" stroke-dasharray="5 4"/>')
        o.append(f'<text x="{mux["x"] * s:.1f}" y="{(mux["y"] - 1) * s:.1f}" font-size="12" fill="#e8d9a8" text-anchor="middle">MUX{i + 1}</text>')
        o.append(f'<text x="{mux["x"] * s:.1f}" y="{(mux["y"] + 2.5) * s:.1f}" font-size="10" fill="#e8d9a8" text-anchor="middle">{mux["ref"]}</text>')
    o.append(f'<rect x="{(LDO["x"] - 3.3) * s:.1f}" y="{(LDO["y"] - 1.8) * s:.1f}" width="{6.6 * s}" height="{3.6 * s}" rx="3" fill="#2b2b2b" stroke="#e8d9a8" stroke-dasharray="5 4"/>')
    o.append(f'<text x="{LDO["x"] * s:.1f}" y="{(LDO["y"] + 1) * s:.1f}" font-size="9" fill="#e8d9a8" text-anchor="middle">3.3 V</text>')
    for hx, hy in mounting_holes():
        o.append(f'<circle cx="{hx * s:.1f}" cy="{hy * s:.1f}" r="{HOLE_D / 2 * s:.1f}" fill="#f6f1e8" stroke="#c9a227" stroke-width="2"/>')
    o.append("</g>")
    lines = [
        ("eTuttino PCB (Hall effect) — top view", 18, "700"),
        (f"{PCB_W:.1f} × {PCB_H:.1f} × {PCB_THICKNESS} mm · {len(ks)} keys · Castagnari Magica K2 layout (C-griff)", 13, "400"),
        (f"{len(ks)} × Gateron magnetic switch (no pins) · {len(ks)} × DRV5056A3 sensor on the BACK, under each switch", 13, "400"),
        ("3 × CD74HC4067 analog mux + AMS1117-3.3 regulator on the back (dashed: seen through the board)", 13, "400"),
        ("Key label: switch · MUX/channel     - - - plate outline (notched for the Teensy + Audio Board)", 13, "400"),
        ("Mux address S0..S3 → pins " + ", ".join(SEL_PINS) + " · MUX1/2/3 output → pins " + ", ".join(COM_PINS) + " (A0, A1, A2)", 13, "400"),
        ("● pin used by the eTuttino   ● Audio Board pin   ○ M2 mounting hole", 13, "400"),
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
    assert len(ks) == 41
    assert len({(k["row"], k["col"]) for k in ks}) == len(ks)       # one key per grid cell
    assert len({(k["mux"], k["ch"]) for k in ks}) == len(ks)        # one sensor per mux channel
    assert not (set(SEL_PINS + COM_PINS) & AUDIO_PINS)            # no clash with the Audio Board
    # the stack stays clear of the keys: right of row 3's last key, above row 2
    assert STACK_ZONE[0] > key_right_edge(2) and STACK_ZONE[3] < GRID_Y0 + 2 * U and STACK_ZONE[1] > 0
    print(write_csv(ks))
    dxf, pw, ph = write_dxf(ks)
    print(dxf, f"(plate {pw:.2f} x {ph:.2f} mm, notched)")
    print(write_svg(ks))
    sharps = sum(1 for k in ks if "#" in note_name(k["note"]))
    print(f"PCB {PCB_W:.2f} x {PCB_H:.2f} mm; keycaps: {len(ks) - sharps} light, {sharps} dark")
    for m, mux in enumerate(MUXES):
        print(mux["ref"], "keys:", sum(1 for k in ks if k["mux"] == m))
    print(firmware_key_table(ks))


if __name__ == "__main__":
    main()
