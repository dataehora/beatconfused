#!/usr/bin/env python3
"""eTuttino PCB/plate generator — single source of truth for the geometry.

Run:  python generate.py        (no third-party packages needed)

Writes, next to this file:
  build/etuttino_keys.csv          every switch: ref, row/col, note, x/y in mm
  build/etuttino_plate.dxf         switch plate for laser cutting (mm)
  build/etuttino_pcb_preview.svg   top view: outline, keys, sensors, muxes, Teensy zone

The routed KiCad board and the fabrication files come from build_pcb.py,
which imports this module (run it with KiCad's Python).

Layout: chromatic button accordion, C-griff, G3-G5 (34 keys) on Gateron
magnetic (Hall-effect) switches. Every key has a TI DRV5056 linear Hall
sensor on the BACK of the board, straight under the switch's magnet; three
CD74HC4067 16:1 analog multiplexers feed the 34 sensor voltages to three
Teensy ADC pins, so the firmware knows how far down each key is (and so
how fast it was pressed: velocity).

Keep in sync with ROWS in etutti/script.js and FIRST_NOTE / FIRST_COL /
KEY_INPUT in etutti/firmware/etutti_synth/etutti_synth.ino
(`python generate.py` prints the KEY_INPUT table the firmware needs;
build_pcb.py checks the routed board against the firmware's copy).
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

U = 19.05                 # MX key pitch (mm)
MARGIN = 6.0              # PCB edge to key grid
ZONE_H = 44.0             # strip behind the keys for the Teensy + Audio Board
CUTOUT = 14.0             # MX plate cutout
PLATE_MARGIN = 6.0        # plate edge to key grid
HOLE_D = 2.2              # M2 clearance
PCB_THICKNESS = 1.2       # thinner board = sensor closer to the magnet

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (first MIDI note, key count, x offset in key units, first column).
# "Row"/"column" are the note grid the firmware and the page share (there
# is no electrical matrix any more: every key has its own sensor).
ROWS = [
    (57, 8, 0.0, 1),    # row 1: A3 .. F#5
    (55, 9, -0.5, 0),   # row 2: G3 .. G5
    (56, 8, 0.0, 1),    # row 3: G#3 .. F5
    (54, 9, -0.5, 0),   # row 4: F#3 .. F#5 (row 1 + F#3)
]

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

# Multiplexers: on the back, in the strip behind the keys, left of the
# Teensy. Each serves the keys of a band of half-key columns (k = 1..17,
# see half_col()). Placed upside down (rotated 180 deg) so the address
# pins face the top edge and COM / VCC face the keys.
MUXES = [
    {"ref": "U41", "x": 36.0, "y": 22.0, "cols": range(1, 6)},
    {"ref": "U42", "x": 84.5, "y": 22.0, "cols": range(6, 12)},
    {"ref": "U43", "x": 124.5, "y": 22.0, "cols": range(12, 18)},
]
# 3.3 V regulator for the sensors and multiplexers (34 sensors x 6 mA is
# more than the Teensy's own 3.3 V pin should supply): on the back, under
# the Teensy, between its two socket rows. Fed from VIN (USB 5 V).
LDO = {"ref": "U50", "x": 152.0, "y": 28.0}

PCB_W = 2 * MARGIN + 9 * U
PCB_H = MARGIN + ZONE_H + 4 * U + MARGIN
GRID_X0 = MARGIN
GRID_Y0 = MARGIN + ZONE_H

# Teensy+Audio stack: long axis horizontal, USB pointing at the right edge,
# right-aligned in the back strip. Centre of the 2 x 14 header footprint:
STACK_CX = PCB_W - MARGIN - 24.0
STACK_CY = MARGIN + ZONE_H / 2


def row_slot(r):
    """Vertical slot (0 = top) of accordion row r+1: row 1 at the bottom."""
    return len(ROWS) - 1 - r


def note_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def half_col(cx):
    """Half-key column of a key centre: 1 (leftmost, rows 2/4) .. 17."""
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
    channel pin nearest the top, so traces coming up from the keys can
    turn in towards the chip without crossing."""
    for m, mux in enumerate(MUXES):
        group = [k for k in ks if half_col(k["cx"]) in mux["cols"]]
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
    table = [[-1] * 9 for _ in ROWS]
    for k in ks:
        table[k["row"]][k["col"]] = k["mux"] * MUX_CHANNELS + k["ch"]
    rows = ",\n".join("  {%s}" % ", ".join("%3d" % v for v in row) for row in table)
    return "const int8_t KEY_INPUT[LAYOUT_ROWS][LAYOUT_COLS] = {\n%s,\n};" % rows


def mounting_holes():
    """M2 holes: the PCB's two back corners (case only), the plate's four
    corners (shared by plate, PCB and case), and the half-key gaps at both
    ends of rows 1 and 3 (those rows are half a key shorter on each side),
    which stiffen the middle of the plate."""
    m = MARGIN / 2
    holes = [
        (m, m),
        (PCB_W - m, m),
        (m, GRID_Y0 - PLATE_MARGIN + m),
        (PCB_W - m, GRID_Y0 - PLATE_MARGIN + m),
        (m, PCB_H - m),
        (PCB_W - m, PCB_H - m),
    ]
    for r in (0, 2):
        cy = GRID_Y0 + (row_slot(r) + 0.5) * U
        holes.append((GRID_X0 + 0.25 * U, cy))
        holes.append((GRID_X0 + 8.75 * U, cy))
    return holes


def stack_pins():
    """(socket, pad, teensy_pin, x, y) for the two 1x14 sockets.
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
    pw = 9 * U + 2 * PLATE_MARGIN
    ph = 4 * U + 2 * PLATE_MARGIN
    ents = []

    def line(x1, y1, x2, y2, layer):
        # DXF y grows upward: flip so the plate reads like the top view.
        ents.append(f"0\nLINE\n8\n{layer}\n10\n{x1:.4f}\n20\n{ph - y1:.4f}\n30\n0\n11\n{x2:.4f}\n21\n{ph - y2:.4f}\n31\n0\n")

    def rect(x, y, w, h, layer):
        line(x, y, x + w, y, layer)
        line(x + w, y, x + w, y + h, layer)
        line(x + w, y + h, x, y + h, layer)
        line(x, y + h, x, y, layer)

    rect(0, 0, pw, ph, "OUTLINE")
    for k in ks:
        rect(k["cx"] - ox - CUTOUT / 2, k["cy"] - oy - CUTOUT / 2, CUTOUT, CUTOUT, "CUTOUTS")
    for hx, hy in mounting_holes():
        if GRID_Y0 - PLATE_MARGIN <= hy <= GRID_Y0 + 4 * U + PLATE_MARGIN:
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
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 340:.0f} {h + 20:.0f}" font-family="Inter, Arial, sans-serif">')
    o.append(f'<rect x="0" y="0" width="{w + 340:.0f}" height="{h + 20:.0f}" fill="#f6f1e8"/>')
    o.append(f'<g transform="translate(10 10)">')
    o.append(f'<rect width="{w:.1f}" height="{h:.1f}" rx="{3 * s}" fill="#1f5e3a" stroke="#0d2c1b" stroke-width="2"/>')
    # Teensy + Audio zone
    zx, zy = (STACK_CX - 21) * s, (STACK_CY - 19) * s
    o.append(f'<rect x="{zx:.1f}" y="{zy:.1f}" width="{42 * s}" height="{38 * s}" rx="6" fill="none" stroke="#e8d9a8" stroke-dasharray="8 6" stroke-width="2"/>')
    # Labels below the J2 row, clear of the pin numbers.
    o.append(f'<text x="{zx + 6:.1f}" y="{zy + 33.5 * s:.1f}" font-size="14" fill="#e8d9a8">Teensy 4.0 + Audio Rev D</text>')
    o.append(f'<text x="{zx + 6:.1f}" y="{zy + 37 * s:.1f}" font-size="11" fill="#e8d9a8">USB → right edge</text>')
    for sock, pad, pin, x, y in stack_pins():
        net = pin_net(pin)
        color = "#f2c27a" if net and net not in ("GND", "VIN") else ("#7aa0c8" if pin in AUDIO_PINS else "#b9c4bd")
        o.append(f'<circle cx="{x * s:.1f}" cy="{y * s:.1f}" r="4.5" fill="{color}"/>')
        o.append(f'<text x="{x * s:.1f}" y="{(y + (-3 if sock == "J1" else 5)) * s:.1f}" font-size="9" fill="#f6f1e8" text-anchor="middle">{pin}</text>')
    # Keys
    for k in ks:
        x, y = (k["cx"] - U / 2) * s, (k["cy"] - U / 2) * s
        sharp = "#" in note_name(k["note"])
        o.append(f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{U * s - 4:.1f}" height="{U * s - 4:.1f}" rx="6" fill="{"#3a3d42" if sharp else "#f4efe6"}" stroke="#0d2c1b"/>')
        o.append(f'<rect x="{(k["cx"] - CUTOUT / 2) * s:.1f}" y="{(k["cy"] - CUTOUT / 2) * s:.1f}" width="{CUTOUT * s:.1f}" height="{CUTOUT * s:.1f}" fill="none" stroke="{"#8a8f96" if sharp else "#c9bfae"}" stroke-dasharray="4 3"/>')
        tc = "#f4efe6" if sharp else "#2f2218"
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] - 1) * s:.1f}" font-size="17" font-weight="700" fill="{tc}" text-anchor="middle">{note_name(k["note"])}</text>')
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] + 4.5) * s:.1f}" font-size="11" fill="{tc}" text-anchor="middle" opacity="0.7">{k["ref"]} · M{k["mux"] + 1}/{k["ch"]}</text>')
    # Back-side parts (seen through the board): multiplexers and regulator
    for i, mux in enumerate(MUXES):
        o.append(f'<rect x="{(mux["x"] - 3.75) * s:.1f}" y="{(mux["y"] - 7.7) * s:.1f}" width="{7.5 * s}" height="{15.4 * s}" rx="3" fill="#2b2b2b" stroke="#e8d9a8" stroke-dasharray="5 4"/>')
        o.append(f'<text x="{mux["x"] * s:.1f}" y="{mux["y"] * s:.1f}" font-size="12" fill="#e8d9a8" text-anchor="middle">MUX{i + 1}</text>')
        o.append(f'<text x="{mux["x"] * s:.1f}" y="{(mux["y"] + 3.5) * s:.1f}" font-size="10" fill="#e8d9a8" text-anchor="middle">{mux["ref"]} → A{i}</text>')
    o.append(f'<rect x="{(LDO["x"] - 3.3) * s:.1f}" y="{(LDO["y"] - 1.8) * s:.1f}" width="{6.6 * s}" height="{3.6 * s}" rx="3" fill="#2b2b2b" stroke="#e8d9a8" stroke-dasharray="5 4"/>')
    o.append(f'<text x="{LDO["x"] * s:.1f}" y="{(LDO["y"] + 1) * s:.1f}" font-size="10" fill="#e8d9a8" text-anchor="middle">3.3 V LDO</text>')
    for k in ks:
        o.append(f'<rect x="{(k["cx"] - 1.5) * s:.1f}" y="{(k["cy"] - 1.5) * s:.1f}" width="{3 * s}" height="{3 * s}" fill="none" stroke="#b5791f" stroke-width="1.5"/>')
    for hx, hy in mounting_holes():
        o.append(f'<circle cx="{hx * s:.1f}" cy="{hy * s:.1f}" r="{HOLE_D / 2 * s:.1f}" fill="#f6f1e8" stroke="#c9a227" stroke-width="2"/>')
    o.append("</g>")
    # Legend
    lx = w + 30
    lines = [
        ("eTuttino PCB (Hall effect) — top view", 18, "700"),
        (f"{PCB_W:.1f} × {PCB_H:.1f} × {PCB_THICKNESS} mm", 14, "400"),
        ("34 × Gateron magnetic switch (no pins)", 13, "400"),
        ("34 × DRV5056A3 sensor, BACK side,", 13, "400"),
        ("      under each switch centre (□)", 13, "400"),
        ("3 × CD74HC4067 analog mux, back side", 13, "400"),
        ("AMS1117-3.3 regulator, back side", 13, "400"),
        ("", 10, "400"),
        ("Key label: MUX/channel", 13, "700"),
        ("Mux address S0..S3 → pins " + ", ".join(SEL_PINS), 13, "400"),
    ] + [(f"  MUX{i + 1} output → pin {p} (A{i})", 13, "400") for i, p in enumerate(COM_PINS)] + [
        ("", 10, "400"),
        ("● pin used by the eTuttino", 13, "400"),
        ("● Audio Board pin", 13, "400"),
        ("○ M2 mounting hole", 13, "400"),
    ]
    y = 40
    for text, size, weight in lines:
        fill = "#2f2218"
        if text.startswith("● pin"):
            fill = "#b5791f"
        elif text.startswith("● Audio"):
            fill = "#3f6f9f"
        o.append(f'<text x="{lx}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}">{text}</text>')
        y += size + 8
    o.append("</svg>")
    path = os.path.join(BUILD, "etuttino_pcb_preview.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    return path


def main():
    os.makedirs(BUILD, exist_ok=True)
    ks = keys()
    assert len(ks) == 34
    assert len({(k["row"], k["col"]) for k in ks}) == 34          # one key per grid cell
    assert len({(k["mux"], k["ch"]) for k in ks}) == 34          # one sensor per mux channel
    assert not (set(SEL_PINS + COM_PINS) & AUDIO_PINS)            # no clash with the Audio Board
    print(write_csv(ks))
    dxf, pw, ph = write_dxf(ks)
    print(dxf, f"(plate {pw:.2f} x {ph:.2f} mm)")
    print(write_svg(ks))
    sharps = sum(1 for k in ks if "#" in note_name(k["note"]))
    print(f"PCB {PCB_W:.2f} x {PCB_H:.2f} mm; keycaps: {len(ks) - sharps} light, {sharps} dark")
    print(firmware_key_table(ks))


if __name__ == "__main__":
    main()
