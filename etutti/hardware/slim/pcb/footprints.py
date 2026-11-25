"""Write the eTutti Viaggio's own footprints (SPEC v2.1, step 3.2, VE2b).

    python etutti/hardware/slim/pcb/footprints.py

Plain CPython (stdlib only). schematic.py imports and runs it first, so the
library always matches the schematic. Writes pcb/kicad/slim.pretty/:

  BGA-196_12x12mm_P0.8mm_RT1062   P1, NXP IMXRT1060CEC rev 4, figure 54
      (SOT1968-1, MAPBGA-196 12 x 12 x 1.37, 0.8 pitch, balls 0.38-0.48).
      Pads are NSMD copper discs of 0.35 mm with a 0.05 mm solder-mask
      margin (mask opening 0.45), the usual land for a 0.43 mm ball at
      0.8 mm pitch. Pad names = ball names (A1 ... P14, no I and no O),
      checked against rt1062_balls.json. Top view: A1 top-left, row A at
      the top, column 1 at the left (figure 54, "top view": A1 index).
  Jack_3.5mm_PJ-327A_SMD          F2, SHOU HAN PJ-327A 5JJ (LCSC C668605),
      5 SMD pads 3 x 2 mm + 2 locating holes 1.0 mm (drawing "PJ-327A 5JJ",
      PCB view). Pads: 1, 2 sleeve; 3 ring; 4 tip; 5 tip switch (normally
      closed against 4, opens when a plug is in). Mouth towards -y.
  LED_1615_RG_4pad                I3, TOGIALED TJ-S1615SW6TGLCRG-A5 (C273605),
      recommended pad layout 2.6 x 1.6: pads 0.85 x 0.55. Pads: 1 red
      anode, 2 red cathode, 3 green anode, 4 green cathode (datasheet
      symbol: 2 -|<- 1 red, 4 -|<- 3 green; cathode mark on the 2/4 side).
  Gateron_Magnetic_MX_1u          copy of etutti/hardware/etuttino.pretty.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(HERE, "kicad", "slim.pretty")
ROWS = "ABCDEFGHJKLMNP"          # 14 rows, JEDEC: no I, O
BGA_PITCH = 0.8
BGA_PAD = 0.35
BGA_MASK = 0.05


def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def head(name, descr, tags, attr="smd", ref_y=-7.5, val_y=7.5):
    return [
        '(footprint "%s"' % name,
        '\t(version 20241229)',
        '\t(generator "slim_footprints")',
        '\t(layer "F.Cu")',
        '\t(descr "%s")' % descr,
        '\t(tags "%s")' % tags,
        '\t(property "Reference" "REF**" (at 0 %s 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % f(ref_y),
        '\t(property "Value" "%s" (at 0 %s 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % (name, f(val_y)),
        '\t(attr %s)' % attr,
    ]


def line(x0, y0, x1, y1, layer, w):
    return '\t(fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))' % (
        f(x0), f(y0), f(x1), f(y1), f(w), layer)


def rect(x0, y0, x1, y1, layer, w):
    return '\t(fp_rect (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill no) (layer "%s"))' % (
        f(x0), f(y0), f(x1), f(y1), f(w), layer)


def write(name, lines):
    os.makedirs(PRETTY, exist_ok=True)
    with open(os.path.join(PRETTY, name + ".kicad_mod"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")


def bga_balls():
    """{ball name: (x, y)} in the footprint (top view, origin = package centre)."""
    out = {}
    for i, r in enumerate(ROWS):
        for c in range(1, 15):
            out["%s%d" % (r, c)] = (round(-5.2 + (c - 1) * BGA_PITCH, 4), round(-5.2 + i * BGA_PITCH, 4))
    return out


def bga():
    name = "BGA-196_12x12mm_P0.8mm_RT1062"
    L = head(name, "NXP MAPBGA-196 12x12x1.37 mm, 0.8 mm pitch (SOT1968-1, IMXRT1060CEC rev 4 fig. 54); "
                   "NSMD pads 0.35 mm, mask 0.45 mm", "BGA 196 0.8 RT1062 MIMXRT1062DVJ6B", ref_y=-7.2, val_y=7.2)
    L += [rect(-6, -6, 6, 6, "F.Fab", 0.1),
          line(-6, -5, -5, -6, "F.Fab", 0.1),
          rect(-6.1, -6.1, 6.1, 6.1, "F.CrtYd", 0.05)]
    # silk: corners only, A1 mark
    s, k = 6.11, 1.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.append(line(sx * s, sy * s, sx * (s - k), sy * s, "F.SilkS", 0.12))
            L.append(line(sx * s, sy * s, sx * s, sy * (s - k), "F.SilkS", 0.12))
    L.append('\t(fp_circle (center -6.6 -6.6) (end -6.4 -6.6) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))')
    L.append('\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    for ball, (x, y) in bga_balls().items():
        L.append('\t(pad "%s" smd circle (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask") '
                 '(solder_mask_margin %s))' % (ball, f(x), f(y), f(BGA_PAD), f(BGA_PAD), f(BGA_MASK)))
    write(name, L)
    return name


JACK_PADS = {"1": (3.4, 1.7), "2": (-3.4, 2.7), "3": (3.4, 5.4), "4": (-3.4, 9.7), "5": (3.4, 11.4)}


def jack():
    name = "Jack_3.5mm_PJ-327A_SMD"
    L = head(name, "3.5 mm stereo jack with tip switch, SMD, right angle, SHOU HAN PJ-327A 5JJ (LCSC C668605); "
                   "1/2 sleeve, 3 ring, 4 tip, 5 tip switch (NC to 4); mouth towards -y",
             "audio jack 3.5 PJ-327A", ref_y=-3.4, val_y=13.6)
    L += [rect(-3.0, 0.0, 3.0, 12.2, "F.Fab", 0.1), rect(-2.5, -2.0, 2.5, 0.0, "F.Fab", 0.1),
          rect(-5.15, -2.3, 5.15, 12.65, "F.CrtYd", 0.05),
          line(-3.11, 3.9, -3.11, 8.5, "F.SilkS", 0.12), line(3.11, 6.65, 3.11, 10.1, "F.SilkS", 0.12),
          line(-2.6, -2.1, 2.6, -2.1, "F.SilkS", 0.12)]
    for num, (x, y) in JACK_PADS.items():
        L.append('\t(pad "%s" smd rect (at %s %s) (size 3 2) (layers "F.Cu" "F.Paste" "F.Mask"))' % (num, f(x), f(y)))
    for y in (3.0, 9.0):
        L.append('\t(pad "" np_thru_hole circle (at 0 %s) (size 1 1) (drill 1) (layers "*.Cu" "*.Mask"))' % f(y))
    write(name, L)
    return name


LED_PADS = {"1": (0.875, -0.525), "2": (-0.875, -0.525), "3": (0.875, 0.525), "4": (-0.875, 0.525)}


def led():
    name = "LED_1615_RG_4pad"
    L = head(name, "LED 1.6 x 1.5 mm red/green, 4 pads, TOGIALED TJ-S1615SW6TGLCRG-A5 (LCSC C273605); "
                   "1 red A, 2 red K, 3 green A, 4 green K", "LED 1615 bicolor", ref_y=-1.6, val_y=1.6)
    L += [rect(-0.8, -0.75, 0.8, 0.75, "F.Fab", 0.1), line(-0.8, -0.2, -0.8, 0.2, "F.Fab", 0.3),
          rect(-1.55, -1.05, 1.55, 1.05, "F.CrtYd", 0.05),
          line(-1.5, -0.95, -1.5, 0.95, "F.SilkS", 0.12)]
    for num, (x, y) in LED_PADS.items():
        L.append('\t(pad "%s" smd rect (at %s %s) (size 0.85 0.55) (layers "F.Cu" "F.Paste" "F.Mask"))' % (num, f(x), f(y)))
    write(name, L)
    return name


def srbv():
    """Alps SRBV (7.5 mm thin vertical rotary switch). Hole pattern read off Alps catalogue p.141 (10 x D0.9 in two rows of 5,
    2.5 mm pitch, rows 16.2 mm apart; 2 x D2.0 mounting holes): APPROXIMATE, to be replaced by the maker's STEP/EasyEDA footprint at stage 2."""
    name = "Rotary_Alps_SRBV_7p5_Vertical"
    L = head(name, "Alps SRBV rotary switch, vertical, 10 pins (1 and 10 common, 2..9 positions); APPROXIMATE (stage 1 placeholder)",
             "rotary switch SRBV", attr="through_hole", ref_y=-10.5, val_y=10.5)
    L += [rect(-8.1, -9.2, 8.1, 9.2, "F.Fab", 0.1), rect(-8.6, -9.7, 8.6, 9.7, "F.CrtYd", 0.05)]
    for i in range(5):                     # terminals 1..5 along the bottom row, 10..6 along the top row
        x = 5.0 - 2.5 * i
        L.append('	(pad "%d" thru_hole circle (at %s 8.1) (size 1.5 1.5) (drill 0.9) (layers "*.Cu" "*.Mask"))' % (i + 1, f(x)))
        L.append('	(pad "%d" thru_hole circle (at %s -8.1) (size 1.5 1.5) (drill 0.9) (layers "*.Cu" "*.Mask"))' % (10 - i, f(x)))
    for x in (-8.0, 8.0):
        L.append('	(pad "" np_thru_hole circle (at %s 0) (size 2 2) (drill 2) (layers "*.Cu" "*.Mask"))' % f(x))
    write(name, L)
    return name


def _courtyard(x0, y0, x1, y1):
    return rect(x0, y0, x1, y1, "F.CrtYd", 0.05)


def tmag5253():
    """TMAG5253 X2SON-4 as EasyEDA / JLCPCB draw it (LCSC C22401868): pad 1 (+0.7, -0.25), 2 (-0.7, -0.25), 3 (-0.7, +0.25), 4 (+0.7, +0.25), 5 = EP."""
    name = "TMAG5253_X2SON4_EE"
    L = head(name, "TI TMAG5253 X2SON-4 1.4 x 1.1, pads as EasyEDA C22401868 (what JLCPCB places)", "X2SON TMAG5253", ref_y=-1.5, val_y=1.5)
    L += [rect(-0.7, -0.55, 0.7, 0.55, "F.Fab", 0.1), _courtyard(-0.95, -0.7, 0.95, 0.7)]
    for num, x, y in (("1", 0.7, -0.25), ("2", -0.7, -0.25), ("3", -0.7, 0.25), ("4", 0.7, 0.25)):
        L.append('	(pad "%s" smd rect (at %s %s) (size 0.22 0.4) (layers "F.Cu" "F.Paste" "F.Mask"))' % (num, f(x), f(y)))
    L.append('	(pad "5" smd rect (at 0 0) (size 0.8 0.6) (layers "F.Cu" "F.Paste" "F.Mask"))')
    write(name, L)
    return name


def hc595():
    """74HC595BQ DHVQFN-16 2.5 x 3.5 as EasyEDA draws it (LCSC C730243)."""
    name = "HC595_DHVQFN16_EE"
    L = head(name, "Nexperia 74HC595BQ DHVQFN-16, pads as EasyEDA C730243", "DHVQFN16 595", ref_y=-2.6, val_y=2.6)
    L += [rect(-1.75, -1.25, 1.75, 1.25, "F.Fab", 0.1), _courtyard(-2.2, -1.65, 2.2, 1.65)]
    pads = [("1", -1.658, 0.25, 0.665, 0.28), ("16", -1.658, -0.25, 0.665, 0.28), ("8", 1.658, 0.25, 0.665, 0.28), ("9", 1.658, -0.25, 0.665, 0.28)]
    for i, x in enumerate((-1.25, -0.75, -0.25, 0.25, 0.75, 1.25)):
        pads.append((str(2 + i), x, 1.157, 0.28, 0.665))
        pads.append((str(15 - i), x, -1.157, 0.28, 0.665))
    for num, x, y, w, h in pads:
        L.append('	(pad "%s" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask"))' % (num, f(x), f(y), f(w), f(h)))
    L.append('	(pad "17" smd rect (at 0 0) (size 2 1) (layers "F.Cu" "F.Paste" "F.Mask"))')
    write(name, L)
    return name


def ffc():
    """KH-FPC0.5-H1.0SMT-8P-QCHF (LCSC C3250113), pads as EasyEDA draws them: the 8 signal pads (0.3 x 0.8, 0.5 pitch) at y = -1.25 (the REAR),
    two hold-down pads (0.4 x 0.8, named MP) at (+-2.75, +1.25); the body is x +-3.0, y -1.0 .. +1.9; the cable mouth is at y = +1.9 (towards +y)."""
    name = "FFC_8P_0.5_KH-H1.0"
    L = head(name, "FFC/FPC 8P 0.5 mm, 1.0 mm high, flip lock, double-sided contacts, KH-FPC0.5-H1.0SMT-8P-QCHF; mouth towards +y", "FFC FPC 0.5 8P",
             ref_y=-2.6, val_y=3.0)
    L += [rect(-3.0, -1.0, 3.0, 1.9, "F.Fab", 0.1), _courtyard(-3.3, -1.8, 3.3, 2.1), line(-3.0, 1.9, 3.0, 1.9, "F.SilkS", 0.12)]
    for i in range(8):
        L.append('	(pad "%d" smd rect (at %s -1.25) (size 0.3 0.8) (layers "F.Cu" "F.Paste" "F.Mask"))' % (i + 1, f(-1.75 + 0.5 * i)))
    for x in (-2.75, 2.75):
        L.append('	(pad "MP" smd rect (at %s 1.25) (size 0.4 0.8) (layers "F.Cu" "F.Paste" "F.Mask"))' % f(x))
    write(name, L)
    return name


def ks33d():
    """The KS-33D's PCB holes (Gateron drawing 'Layout of PCB'): centre post D5.20 and two pegs D1.70 at +-5.075; no electrical pad."""
    name = "KS33D_holes"
    L = head(name, "Gateron KS-33D PCB holes: D5.20 centre, 2 x D1.70 at +-5.075 (10.15 apart); the Hall sensor is 4.3 mm from the centre (+y here)", "KS-33D holes",
             attr="through_hole", ref_y=-8.2, val_y=8.2)
    L += [rect(-7.3, -7.3, 7.3, 7.3, "F.Fab", 0.1), _courtyard(-7.4, -7.4, 7.4, 7.4)]
    L.append('	(pad "" np_thru_hole circle (at 0 0) (size 5.2 5.2) (drill 5.2) (layers "*.Cu" "*.Mask"))')
    for x in (-5.075, 5.075):
        L.append('	(pad "" np_thru_hole circle (at %s 0) (size 1.7 1.7) (drill 1.7) (layers "*.Cu" "*.Mask"))' % f(x))
    write(name, L)
    return name


def check_bga():
    balls = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
    mine = set(bga_balls())
    if mine != set(balls) or len(mine) != 196:
        raise SystemExit("BGA pads %d vs rt1062_balls.json %d: %s" % (len(mine), len(balls), sorted(mine ^ set(balls))[:8]))
    return len(mine)


def write_all():
    names = [bga(), jack(), led(), tmag5253(), hc595(), ffc(), ks33d()]
    n = check_bga()
    return names, n


if __name__ == "__main__":
    names, n = write_all()
    print("slim.pretty: %s (BGA %d pads = rt1062_balls.json)" % (", ".join(names), n))
