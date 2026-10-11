#!/usr/bin/env python3
"""eTuttino PCB/plate generator — single source of truth for the geometry.

Run:  python generate.py        (no third-party packages needed)

Writes, next to this file:
  build/etuttino_keys.csv          every switch: ref, row/col, note, x/y in mm
  build/etuttino_plate.dxf         switch plate for laser cutting (mm)
  build/etuttino_pcb_preview.svg   top view: outline, keys, matrix, Teensy zone

The routed KiCad board and the fabrication files come from build_pcb.py,
which imports this module (run it with KiCad's Python).

Layout: chromatic button accordion, C-griff, G3-G5 (34 keys), 4 x 9 matrix.
Keep in sync with ROWS in etutti/script.js and NOTE_MAP in
etutti/firmware/etutti_synth/etutti_synth.ino.
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

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# (first MIDI note, key count, x offset in key units, first matrix column)
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
# Matrix row r = accordion row r+1. Row 1 sits at the bottom (nearest the
# player), so the top row (4) gets pin 0, the J1 pad nearest the routing
# channel — that ordering is what lets the row traces nest without
# crossing (see build_pcb.py).
ROW_PINS = ["3", "2", "1", "0"]
COL_PINS = ["4", "5", "6", "9", "14", "15", "16", "17", "22"]
AUDIO_PINS = {"7", "8", "18", "19", "20", "21", "23"}  # Audio Board Rev D

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


def keys():
    out = []
    n = 0
    for r, (first, count, x0, col0) in enumerate(ROWS):
        for i in range(count):
            n += 1
            x = x0 + i
            out.append({
                "ref": f"SW{n}",
                "diode": f"D{n}",
                "row": r,
                "col": col0 + i,
                "note": first + 3 * i,
                "cx": GRID_X0 + (x + 1.0) * U,   # x = -0.5 -> half a key in
                "cy": GRID_Y0 + (row_slot(r) + 0.5) * U,
            })
    return out


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
    if pin in ROW_PINS:
        return f"ROW{ROW_PINS.index(pin)}"
    if pin in COL_PINS:
        return f"COL{COL_PINS.index(pin)}"
    if pin == "GND":
        return "GND"
    return None


# ---------------------------------------------------------------- outputs
def write_csv(ks):
    path = os.path.join(BUILD, "etuttino_keys.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["switch", "diode", "matrix_row", "matrix_col", "row_pin", "col_pin", "midi", "note", "x_mm", "y_mm"])
        for k in ks:
            w.writerow([k["ref"], k["diode"], k["row"], k["col"], ROW_PINS[k["row"]], COL_PINS[k["col"]],
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
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 260:.0f} {h + 20:.0f}" font-family="Inter, Arial, sans-serif">')
    o.append(f'<rect x="0" y="0" width="{w + 260:.0f}" height="{h + 20:.0f}" fill="#f6f1e8"/>')
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
        color = "#f2c27a" if net and net != "GND" else ("#7aa0c8" if pin in AUDIO_PINS else "#b9c4bd")
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
        o.append(f'<text x="{k["cx"] * s:.1f}" y="{(k["cy"] + 4.5) * s:.1f}" font-size="11" fill="{tc}" text-anchor="middle" opacity="0.7">{k["ref"]} · R{k["row"]}C{k["col"]}</text>')
    for hx, hy in mounting_holes():
        o.append(f'<circle cx="{hx * s:.1f}" cy="{hy * s:.1f}" r="{HOLE_D / 2 * s:.1f}" fill="#f6f1e8" stroke="#c9a227" stroke-width="2"/>')
    o.append("</g>")
    # Legend
    lx = w + 30
    lines = [
        ("eTuttino PCB — top view", 18, "700"),
        (f"{PCB_W:.1f} × {PCB_H:.1f} mm", 14, "400"),
        ("34 × MX hot-swap (Kailh), back side", 13, "400"),
        ("34 × 1N4148W SOD-123, back side", 13, "400"),
        ("matrix 4 rows × 9 cols", 13, "400"),
        ("", 10, "400"),
        ("Rows  (cathode side):", 13, "700"),
    ] + [(f"  ROW{i} → pin {p}", 13, "400") for i, p in enumerate(ROW_PINS)] + [
        ("Cols  (switch side):", 13, "700"),
    ] + [(f"  COL{i} → pin {p}", 13, "400") for i, p in enumerate(COL_PINS)] + [
        ("", 10, "400"),
        ("● matrix pin", 13, "400"),
        ("● Audio Board pin", 13, "400"),
        ("○ M2 mounting hole", 13, "400"),
    ]
    y = 40
    for text, size, weight in lines:
        fill = "#2f2218"
        if text.startswith("● matrix"):
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
    assert len({(k["row"], k["col"]) for k in ks}) == 34          # one switch per matrix cell
    assert not (set(ROW_PINS + COL_PINS) & AUDIO_PINS)            # no clash with the Audio Board
    print(write_csv(ks))
    dxf, pw, ph = write_dxf(ks)
    print(dxf, f"(plate {pw:.2f} x {ph:.2f} mm)")
    print(write_svg(ks))
    sharps = sum(1 for k in ks if "#" in note_name(k["note"]))
    print(f"PCB {PCB_W:.2f} x {PCB_H:.2f} mm; keycaps: {len(ks) - sharps} light, {sharps} dark")


if __name__ == "__main__":
    main()
