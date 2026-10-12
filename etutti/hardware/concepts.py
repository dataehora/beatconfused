#!/usr/bin/env python3
"""Concept layouts for the eTutti family (the /etutti/models/ page) --
one parametric shape, three models built out of it:

  etuttino      the 44-key eTuttino keyboard (C-griff G3-E6) plus a grip at
                the left end: a taller block, as low as the Teensy 4.0 +
                Audio Board stack inside it allows, that the left hand holds
                the instrument by. It carries the LED, and the USB and
                headphone sockets on its left face. A ramp takes the case
                down to keyboard height a little before the first keys, so
                the playing hand has room.
  etutti        the same grip and key layout, each row one key longer:
                row 1 A3-F#6, row 2 G3-G6, row 3 G#3-F6, row 4 A3-D#6
                (48 keys, three octaves G3-G6).
  etutti_chorus the eTutti with a battery, a speaker and a screen, all in
                the grip: a 1.9" 320x170 screen on top towards the back
                (where the Corsair Vanguard 96 has its LCD), a discreet
                speaker grille in front of it, the battery underneath.

Pure Python (no third-party packages): `python concepts.py` writes the
top-view diagrams (etutti/models/img/<model>_plan.svg). The 3D pictures
come from concepts_cad.py (FreeCAD) and concepts_render.py (KiCad), which
import this module for every number.

Coordinates as in generate.py: mm, x to the right, y towards the player,
z up from the keyboard PCB's top surface.
"""
import os

import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.normpath(os.path.join(HERE, "..", "models", "img"))

U = G.U
NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]

# ---- the shared body ---------------------------------------------------
GRIP_W = 76.0            # grip length along the instrument: room for four fingers under it, the thumb on top
RAMP_W = 16.0            # grip top down to the keyboard deck
KEY_GAP = 6.0            # deck between the foot of the ramp and the first key cell
MARGIN = 12.0            # deck round the key cells (back, front, right)
FLOOR_Z = -7.7           # case bottom (as case.py: 2 mm floor, 4.5 mm under the PCB)
DECK_Z = 8.0             # keyboard deck top
PLATE_Z = 5.0            # plate top, seen through the key opening
SWITCH_TOP = 11.4
KEYCAP_Z = (11.8, 18.8)
CAP_R = 8.6
CAP_GAP = 0.6            # deck opening beyond each key's 19.05 mm cell
CORNER_R = 6.0

# The Teensy 4.0 + Audio Board Rev D, stacked as on the eTuttino board
# (Audio Board 3 mm up on its header legs, Teensy on its pin spacers): its
# top, USB connector included, is 19.8 mm above the PCB (assembly3d.py).
STACK_TOP = 19.8
STACK_L = 13 * 2.54 + G.AUDIO_PAST_USB + G.AUDIO_PAST_END     # along the pins (x): 40.0
STACK_D = 15.24 + G.AUDIO_PAST_JACK + G.AUDIO_PAST_VIN        # across (y): 38.7
GRIP_TOP = round(STACK_TOP + 1.0 + 2.0, 1)                    # 1 mm clear + 2 mm skin: 22.8

SCREEN = {"w": 52.0, "h": 30.0, "active": (42.6, 22.6)}       # 1.9" 320x170 IPS module and its glass
SPEAKER = {"r": 14.0, "hole_r": 0.85, "pitch": 2.8}           # round grille over a 28 mm, 2 W driver
BATTERY = (60.0, 40.0, 8.0)                                    # 3.7 V LiPo, ~2000 mAh (603450-size)


def rows_for(model):
    """(first MIDI note, key count, x offset in key units, first column),
    as generate.ROWS. The eTutti adds one key to every row."""
    if model == "etuttino":
        return list(G.ROWS)
    return [(first, count + 1, x0, col0) for first, count, x0, col0 in G.ROWS]


class Model:
    def __init__(self, name):
        self.name = name
        self.rows = rows_for(name)
        self.grid_units = max(x0 + count + 0.5 for _, count, x0, _ in self.rows)   # cells span x0 + 0.5 .. x0 + count + 0.5 keys
        self.grid_x0 = GRIP_W + RAMP_W + KEY_GAP
        self.grid_y0 = MARGIN
        self.length = round(self.grid_x0 + self.grid_units * U + MARGIN, 1)
        self.depth = round(MARGIN + 4 * U + MARGIN, 1)
        self.chorus = name == "etutti_chorus"

    # keys -------------------------------------------------------------
    def keys(self):
        out = []
        for r, (first, count, x0, col0) in enumerate(self.rows):
            slot = len(self.rows) - 1 - r          # row 1 nearest the player
            for i in range(count):
                note = first + 3 * i
                out.append({"row": r, "note": note, "name": note_name(note),
                            "cx": self.grid_x0 + (x0 + i + 1.0) * U,
                            "cy": self.grid_y0 + (slot + 0.5) * U})
        return out

    def row_cells(self):
        """(x0, y0, x1, y1) of each row's strip of key cells."""
        out = []
        for r, (first, count, x0, col0) in enumerate(self.rows):
            slot = len(self.rows) - 1 - r
            out.append((self.grid_x0 + (x0 + 0.5) * U, self.grid_y0 + slot * U,
                        self.grid_x0 + (x0 + count + 0.5) * U, self.grid_y0 + (slot + 1) * U))
        return out

    def range_text(self):
        ks = self.keys()
        lo = min(ks, key=lambda k: k["note"])["name"]
        hi = max(ks, key=lambda k: k["note"])["name"]
        return "%s–%s" % (lo, hi)

    # what goes in the grip ------------------------------------------
    def grip_parts(self):
        """Plan-view boxes (x0, y0, x1, y1, z0, z1, key) inside or on the
        grip. The same in every model: the stack in the front half against
        the left face (its USB and the Audio Board's jack come out there),
        the LED by the ramp; the back half is free. The Chorus fills it:
        the screen on top at the back, the battery under it, and a round
        speaker in front of the screen, beside the stack."""
        d = self.depth
        sy = d - 8.0 - STACK_D
        parts = [(1.0, sy, 1.0 + STACK_L, sy + STACK_D, 0.0, STACK_TOP, "stack"),
                 (GRIP_W - 12.0, d - 9.0, GRIP_W - 8.0, d - 5.0, GRIP_TOP - 1, GRIP_TOP + 0.4, "led")]
        if self.chorus:
            cx = GRIP_W / 2 + 2.0
            parts.append((cx - SCREEN["w"] / 2, 8.0, cx + SCREEN["w"] / 2, 8.0 + SCREEN["h"],
                          GRIP_TOP - 4.0, GRIP_TOP, "screen"))
            r = SPEAKER["r"]
            scx, scy = GRIP_W - 6.0 - r, sy + STACK_D / 2 - 2.0
            parts.append((scx - r, scy - r, scx + r, scy + r, GRIP_TOP - 6.0, GRIP_TOP, "speaker"))
            bw, bd, bh = BATTERY
            parts.append((cx - bw / 2, 5.0, cx + bw / 2, 5.0 + bd, FLOOR_Z + 2.0, FLOOR_Z + 2.0 + bh, "battery"))
        return parts

    def ports(self):
        """(name, y, z, w, h) of the openings in the grip's left face."""
        st = [p for p in self.grip_parts() if p[6] == "stack"][0]
        y0, y1 = st[1], st[3]
        # USB: Teensy's centre line; jack: beside the 0-12 row (the front one)
        usb_y = (y0 + y1) / 2 - (G.AUDIO_PAST_JACK - G.AUDIO_PAST_VIN) / 2
        jack_y = usb_y + 7.62 + 7.2
        out = [("usb", usb_y, 18.5, 12.0, 7.0), ("jack", jack_y, 7.1, 6.4, 6.4)]
        if self.chorus:
            out.append(("power", y0 - 8.0, 10.0, 4.0, 9.0))         # slide switch for the battery, behind the stack
        return out


def grille_holes(x0, y0, x1, y1):
    """Hole centres of the round speaker grille: one in the middle, then
    concentric rings a hole pitch apart, inside the circle that fits the
    box."""
    import math
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 - 1.5
    p = SPEAKER["pitch"]
    out = [(cx, cy)]
    k = 1
    while k * p <= r - SPEAKER["hole_r"]:
        n = int(round(2 * math.pi * k))
        for i in range(n):
            a = 2 * math.pi * i / n + (0.5 * 2 * math.pi / n if k % 2 else 0)
            out.append((round(cx + k * p * math.cos(a), 3), round(cy + k * p * math.sin(a), 3)))
        k += 1
    return out


def note_name(midi):
    return "%s%d" % (NOTE_NAMES[midi % 12], midi // 12 - 1)


MODELS = [Model("etuttino"), Model("etutti"), Model("etutti_chorus")]
TITLES = {"etuttino": "eTuttino", "etutti": "eTutti", "etutti_chorus": "eTuttiChorus"}


# ---- top-view diagrams --------------------------------------------------
def plan_svg(m):
    s = 3.0                       # px per mm
    pad = 30
    padl = 70                     # port labels on the left
    W = m.length * s + pad + padl
    H = m.depth * s + 2 * pad + 40
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" font-family="Inter, Arial, sans-serif" role="img">' % (W, H)]
    o.append('<title>%s, top view</title>' % TITLES[m.name])
    o.append('<g transform="translate(%d %d)">' % (padl, pad))
    o.append('<rect width="%.1f" height="%.1f" rx="%.1f" fill="#8a1f28" stroke="#4d0f15" stroke-width="2"/>' % (m.length * s, m.depth * s, CORNER_R * s))
    # grip, ramp
    o.append('<rect width="%.1f" height="%.1f" rx="%.1f" fill="#741a22"/>' % (GRIP_W * s, m.depth * s, CORNER_R * s))
    o.append('<rect x="%.1f" width="%.1f" height="%.1f" fill="url(#ramp)"/>' % (GRIP_W * s, RAMP_W * s, m.depth * s))
    o.append('<defs><linearGradient id="ramp"><stop offset="0" stop-color="#741a22"/><stop offset="1" stop-color="#8a1f28"/></linearGradient></defs>')
    # key opening
    for x0, y0, x1, y1 in m.row_cells():
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#16181d"/>' % (
            (x0 - CAP_GAP) * s, (y0 - CAP_GAP) * s, (x1 - x0 + 2 * CAP_GAP) * s, (y1 - y0 + 2 * CAP_GAP) * s))
    for k in m.keys():
        sharp = "♯" in k["name"]
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (k["cx"] * s, k["cy"] * s, CAP_R * s, "#3a3d42" if sharp else "#f4efe6"))
        o.append('<text x="%.1f" y="%.1f" font-size="11" font-weight="600" fill="%s" text-anchor="middle">%s</text>' % (
            k["cx"] * s, k["cy"] * s + 4, "#f4efe6" if sharp else "#2f2218", k["name"]))
    # grip contents (dashed: inside)
    labels = {"stack": "Teensy + Audio Board", "screen": '1.9" screen', "speaker": "speaker",
              "battery": "battery (under)", "led": ""}
    for x0, y0, x1, y1, z0, z1, key in m.grip_parts():
        if key == "led":
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#7ee08a" stroke="#1f5e3a"/>' % ((x0 + x1) / 2 * s, (y0 + y1) / 2 * s, 2.0 * s))
            o.append('<text x="%.1f" y="%.1f" font-size="10" fill="#f6efe4">LED</text>' % (((x0 + x1) / 2 + 3.5) * s, ((y0 + y1) / 2 + 1.2) * s))
            continue
        style = {"stack": ('none', '#e8d9a8', '6 4'), "battery": ('none', '#9fc3ad', '3 3'),
                 "screen": ('#121722', '#6f8bb3', ''), "speaker": ('none', '#c98a8f', '')}[key]
        rx = (x1 - x0) / 2 if key == "speaker" else 6.0 / s * s
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" stroke="%s" stroke-width="2" stroke-dasharray="%s"/>' % (
            x0 * s, y0 * s, (x1 - x0) * s, (y1 - y0) * s, rx * s if key == "speaker" else 6, style[0], style[1], style[2]))
        if key == "speaker":
            for hx, hy in grille_holes(x0, y0, x1, y1):
                o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#16181d"/>' % (hx * s, hy * s, SPEAKER["hole_r"] * s))
        ty = {"stack": y0 + 6.0, "battery": y1 - 2.0, "screen": (y0 + y1) / 2 + 1.5, "speaker": y0 - 2.0}[key]
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#f6efe4" text-anchor="middle">%s</text>' % (
            (x0 + x1) / 2 * s, ty * s, labels[key]))
    for name, y, z, w, h in m.ports():
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#16181d"/>' % (-1.5 * s, (y - w / 2) * s, 3 * s, w * s))
        o.append('<text x="%.1f" y="%.1f" font-size="10" fill="#57483b" text-anchor="end">%s</text>' % (-3.0 * s, (y + 1.2) * s,
                 {"usb": "USB", "jack": "audio out", "power": "power"}[name]))
    # dimensions
    o.append('<g stroke="#57483b" fill="#57483b" font-size="12">')
    yd = m.depth * s + 18
    o.append('<line x1="0" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (yd, m.length * s, yd))
    o.append('<text x="%.1f" y="%.1f" stroke="none" text-anchor="middle">%.0f mm</text>' % (m.length * s / 2, yd + 16, m.length))
    o.append('<line x1="0" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (yd - 8, GRIP_W * s, yd - 8))
    o.append('<text x="%.1f" y="%.1f" stroke="none" text-anchor="middle">grip %.0f mm</text>' % (GRIP_W * s / 2, yd + 4, GRIP_W))
    o.append('</g>')
    o.append('<text x="%.1f" y="-9" font-size="12" fill="#57483b" text-anchor="end">%.0f mm deep</text>' % (m.length * s, m.depth))
    o.append('</g></svg>')
    return "\n".join(o)


def specs(m):
    ks = m.keys()
    return {
        "keys": len(ks), "range": m.range_text(),
        "length": m.length, "depth": m.depth,
        "grip_h": round(GRIP_TOP - FLOOR_Z, 1), "deck_h": round(DECK_Z - FLOOR_Z, 1),
        "keys_h": round(KEYCAP_Z[1] - FLOOR_Z, 1),
    }


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    for m in MODELS:
        path = os.path.join(IMG_DIR, "%s_plan.svg" % m.name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(plan_svg(m))
        print(path, specs(m))


if __name__ == "__main__":
    main()
