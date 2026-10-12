"""Clearance check for the case (run with FreeCAD's Python after case.py):
the case must not touch any keycap over its whole travel, any switch, the
plate's keys area, or the Teensy + Audio Board stack -- the stack is held
only by its header legs. Prints the overlap volume of each pair; all must
be zero. Exits non-zero otherwise."""
import os
import sys

import FreeCAD  # noqa: F401  (loads Part for case.py)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402  (case.py builds only when run as a script)
import generate as G  # noqa: E402

TRAVEL = 4.0
GAP = 0.3                # what has to stay free around the moving and the hand-soldered parts


def keyparts():
    out = []
    for k in G.keys():
        x, y = k["cx"], k["cy"]
        # keycap anywhere between rest and bottomed out, plus a little play
        out.append(("keycap " + k["ref"], C.cyl(x, y, 11.8 - TRAVEL, 18.8, 8.6 + GAP)))
        out.append(("switch " + k["ref"], C.box(x - 7.8 - GAP, y - 7.8 - GAP, 5.0, x + 7.8 + GAP, y + 7.8 + GAP, 11.4)))
    return out


def stackparts():
    zx0, zy0, zx1, zy1 = G.STACK_ZONE
    cx, cy = G.STACK_CX, G.STACK_CY
    zt = 3.0 + 1.6
    tz = zt + 8.5 + 2.5
    jy = cy + 7.62 + 7.2
    g = GAP
    return [
        ("audio board", C.box(zx0 - g, zy0 - g, 3.0 - g, zx1 + g, zy1 + g, zt + 1.0)),   # + its ~1 mm parts
        ("headers", C.box(cx - 17.78 - g, cy - 8.89 - g, zt, cx + 17.78 + g, cy + 8.89 + g, tz)),
        ("teensy", C.box(cx - 17.78 - g, cy - 8.89 - g, tz, cx + 17.78 + g, cy + 8.89 + g, tz + 1.6 + 1.4 + 0.5)),
        ("usb", C.box(cx - 18.8 - g, cy - 3.8 - g, tz + 1.6, cx - 13.5 + g, cy + 3.8 + g, tz + 1.6 + 2.6 + g)),
        ("jack", C.box(zx0 + 0.5 - g, jy - 3.0 - g, zt, zx0 + 13.0 + g, jy + 3.0 + g, zt + 5.0 + g)),
    ]


def main():
    import json
    sup = json.load(open(os.path.join(G.BUILD, "etuttino_supports.json"), encoding="utf-8"))
    top = C.top_shell(sup)
    tray = C.bottom_tray(sup)
    bad = 0
    for name, solid in keyparts() + stackparts():
        for part_name, part in (("top", top), ("tray", tray)):
            v = part.common(solid).Volume
            if v > 1e-3:
                bad += 1
                print("  TOUCHES: %s / case %s: %.2f mm3" % (name, part_name, v))
    print("case clearance check: %d collisions (keycaps over %.0f mm travel, switches, Teensy, Audio Board, jack, USB; %.1f mm margin)" % (bad, TRAVEL, GAP))
    sys.exit(1 if bad else 0)


main()
