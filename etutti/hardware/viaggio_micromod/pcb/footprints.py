"""Write the eTutti Viaggio MicroMod's own footprints (SPEC v2.2, step M1).

    python etutti/hardware/viaggio_micromod/pcb/footprints.py

Plain CPython (stdlib only). schematic.py imports and runs it first, so the
library always matches the schematic. Writes pcb/kicad/viaggio_micromod.pretty/:

  M.2_Socket_E_H4.2_MicroMod      P1, M.2 Key E socket, 0.5 mm pitch, 67 pins,
      4.2 mm high (TE 2199230-4 customer drawing rev B3, sheet 3 "recommended
      PCB outline"; LOTES APCI0108-P001A, LCSC C841659, is the same M.2 land).
      Checked pad by pad against SparkFun's carrier footprint
      "M.2-CONNECTOR-E" (SparkFun-MicroMod library, as used on the MicroMod
      Data Logging and ATP carriers):
        - odd pins 1..23, 33..75: 34 pads 0.3 x 1.55 at y = +5.275
          (4.5 .. 6.05 from the alignment holes' line);
        - even pins 2..22, 32..74: 33 pads 0.3 x 1.55 at y = -2.275
          (1.5 .. 3.05 from that line);
        - pin n at x = 9.25 - 0.25 (n - 1); key E removes pins 24..31;
        - 2 solder pegs "MP" 1.2 x 2.75 at (+-10.35, +4.5);
        - NPTH 1.1 at (+10, 0) (pin 1 side) and 1.6 at (-10, 0).
      Origin = centre of the pin field on the alignment holes' line. The
      MicroMod card (22 x 22) lies towards -y; its M2.5 screw notch is at
      (+4.0, -20.0) from this origin (SparkFun carriers: standoff H5 at
      (4.06, 19.94) and (4.01, 19.99) in connector coordinates; conferir com
      a peca). Under the card only parts up to 1.9 mm (Designing with MicroMod).
  Standoff_SMD_M2.5_H2.5          P1, Wurth WA-SMSI 9774025151R (M2.5 internal
      thread, 2.5 mm high, flange 5.1, barrel 3.5 x 1.4); Wurth land: pad 6.0
      round, hole 3.7. Made a plated 6.0/3.7 pad (SparkFun uses 6.0/3.9 plated)
      so DRC has no NPTH inside a copper pad; net GND.
  Jack_3.5mm_PJ-327A_SMD          F2, SHOU HAN PJ-327A 5JJ (LCSC C668605),
      5 SMD pads 3 x 2 mm + 2 locating holes 1.0 mm (drawing "PJ-327A 5JJ",
      PCB view). Pads: 1, 2 sleeve; 3 ring; 4 tip; 5 tip switch (normally
      closed against 4, opens when a plug is in). Mouth towards -y.
  LED_1615_RG_4pad                I3, TOGIALED TJ-S1615SW6TGLCRG-A5 (C273605),
      recommended pad layout 2.6 x 1.6: pads 0.85 x 0.55. Pads: 1 red
      anode, 2 red cathode, 3 green anode, 4 green cathode.
  Gateron_Magnetic_MX_1u          copy of etutti/hardware/etuttino.pretty.

The Viaggio v2.1's BGA-196 (RT1062) footprint is gone: the processor is the
MicroMod module now.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = "viaggio_micromod"
PRETTY = os.path.join(HERE, "kicad", LIB + ".pretty")
ETUTTINO_PRETTY = os.path.normpath(os.path.join(HERE, "..", "..", "etuttino.pretty"))

M2_ODD_Y = 5.275
M2_EVEN_Y = -2.275
M2_PAD = (0.3, 1.55)
M2_PINS = [n for n in range(1, 76) if not 24 <= n <= 31]     # key E: 24..31 removed
M2_STANDOFF = (4.0, -20.0)


def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def head(name, descr, tags, attr="smd", ref_y=-7.5, val_y=7.5):
    return [
        '(footprint "%s"' % name,
        '\t(version 20241229)',
        '\t(generator "viaggio_micromod_footprints")',
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


def circle(x, y, r, layer, w):
    return '\t(fp_circle (center %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill no) (layer "%s"))' % (
        f(x), f(y), f(x + r), f(y), f(w), layer)


def text(s, x, y, layer, size=0.8):
    return '\t(fp_text user "%s" (at %s %s 0) (layer "%s") (effects (font (size %s %s) (thickness 0.1))))' % (
        s, f(x), f(y), layer, f(size), f(size))


def write(name, lines):
    os.makedirs(PRETTY, exist_ok=True)
    with open(os.path.join(PRETTY, name + ".kicad_mod"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")


def m2_pad_xy(n):
    return round(9.25 - 0.25 * (n - 1), 4), (M2_ODD_Y if n % 2 else M2_EVEN_Y)


def m2_socket():
    name = "M.2_Socket_E_H4.2_MicroMod"
    L = head(name, "M.2 Key E socket, 0.5 mm pitch, 67 pins, 4.2 mm high, for a SparkFun MicroMod 22x22 "
                   "processor board (TE 2199230-4 / LOTES APCI0108-P001A); card towards -y, M2.5 standoff at "
                   "(4.0, -20.0); parts under the card <= 1.9 mm", "M.2 NGFF key E MicroMod 2199230-4",
             ref_y=7.4, val_y=-23.6)
    # connector body (TE: 21.9 x ~7.75) and the module card on the fab layer
    L += [rect(-10.95, -2.5, 10.95, 5.25, "F.Fab", 0.1),
          rect(-11.0, -22.0, 11.0, -2.5, "F.Fab", 0.05),
          circle(M2_STANDOFF[0], M2_STANDOFF[1], 3.0, "F.Fab", 0.05),
          text("MicroMod 22x22 (pecas <= 1,9 mm)", 0, -12, "F.Fab"),
          text("standoff M2.5", M2_STANDOFF[0], M2_STANDOFF[1] + 4.0, "F.Fab", 0.6),
          rect(-11.3, -3.35, 11.3, 6.35, "F.CrtYd", 0.05),
          line(-11.05, -2.6, -11.05, 2.0, "F.SilkS", 0.12), line(11.05, -2.6, 11.05, 2.0, "F.SilkS", 0.12),
          line(-11.05, -2.6, -9.6, -2.6, "F.SilkS", 0.12), line(11.05, -2.6, 9.6, -2.6, "F.SilkS", 0.12),
          '\t(fp_circle (center 9.25 6.75) (end 9.45 6.75) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))',
          text("${REFERENCE}", 0, 1.5, "F.Fab", 1.0)]
    for n in M2_PINS:
        x, y = m2_pad_xy(n)
        L.append('\t(pad "%d" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask") '
                 '(solder_paste_margin -0.05))' % (n, f(x), f(y), f(M2_PAD[0]), f(M2_PAD[1])))
    for x in (10.35, -10.35):
        L.append('\t(pad "MP" smd rect (at %s 4.5) (size 1.2 2.75) (layers "F.Cu" "F.Paste" "F.Mask"))' % f(x))
    L.append('\t(pad "" np_thru_hole circle (at 10 0) (size 1.1 1.1) (drill 1.1) (layers "*.Cu" "*.Mask"))')
    L.append('\t(pad "" np_thru_hole circle (at -10 0) (size 1.6 1.6) (drill 1.6) (layers "*.Cu" "*.Mask"))')
    write(name, L)
    return name


def standoff():
    name = "Standoff_SMD_M2.5_H2.5"
    L = head(name, "SMD steel standoff M2.5 internal thread, 2.5 mm high, flange 5.1 mm, barrel 3.5 x 1.4 mm "
                   "(Wurth WA-SMSI 9774025151R); land 6.0 / hole 3.7", "standoff spacer M2.5 SMD MicroMod",
             attr="smd", ref_y=-4.0, val_y=4.0)
    L += ['\t(fp_circle (center 0 0) (end 2.55 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
          '\t(fp_circle (center 0 0) (end 3.25 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
          '\t(fp_circle (center 0 0) (end 3.2 0) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))',
          '\t(pad "1" thru_hole circle (at 0 0) (size 6 6) (drill 3.7) (layers "*.Cu" "*.Mask" "F.Paste"))']
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


def gateron():
    os.makedirs(PRETTY, exist_ok=True)
    shutil.copyfile(os.path.join(ETUTTINO_PRETTY, "Gateron_Magnetic_MX_1u.kicad_mod"),
                    os.path.join(PRETTY, "Gateron_Magnetic_MX_1u.kicad_mod"))
    return "Gateron_Magnetic_MX_1u"


def check_m2():
    """67 pins, 34 odd / 33 even, 0.5 mm pitch in each row, pin 1 next to the 1.1 mm hole."""
    odd = [n for n in M2_PINS if n % 2]
    even = [n for n in M2_PINS if not n % 2]
    if (len(M2_PINS), len(odd), len(even)) != (67, 34, 33):
        raise SystemExit("M.2 pin count %d (%d odd, %d even)" % (len(M2_PINS), len(odd), len(even)))
    if m2_pad_xy(1) != (9.25, M2_ODD_Y) or m2_pad_xy(75) != (-9.25, M2_ODD_Y) or m2_pad_xy(2) != (9.0, M2_EVEN_Y):
        raise SystemExit("M.2 pad positions off")
    return len(M2_PINS)


def write_all():
    names = [m2_socket(), standoff(), jack(), led(), gateron()]
    n = check_m2()
    return names, n


if __name__ == "__main__":
    names, n = write_all()
    print("%s.pretty: %s (M.2 %d pads)" % (LIB, ", ".join(names), n))
