"""Button caps for the eTuttino (SPEC 7): one low dome with a skirt and an
MX cross socket, in three files:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe keycap.py

  out/keycap_natural.stl   white (Seixo) / mother-of-pearl (Madeira)
  out/keycap_sharp.stl     black / ebony
  out/keycap_cf.stl        C and F: natural with a raised diagonal chequer on top
  out/keycap_test_4.stl    the four-switch print test: 2 natural, 1 sharp, 1 C/F,
                           laid out like four neighbouring buttons (19.05 mm hex)
  out/switches.stl         stand-in Gateron switches (for the renders and fit_check.py)

Each cap is modelled in place (z = height in the instrument, the button
centre at x = y = 0) so case.py's Z_KEY_TOP holds. The switch numbers are
MX nominal values -- CHECK them against the Gateron KS-20 actually bought;
printing keycap_test_4 on four real switches is the test for exactly that.

Why the skirt stops where it does: a round Ø17 skirt (Ø15.4 inside) over a
square MX top housing. Pressed down by the full travel, the skirt's bottom
edge must stay above the height where the housing's corners stick out
past the skirt's inside. skirt_base_z() finds that height.
"""
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402

# switch (MX nominal -- CHECK the Gateron KS-20 datasheet)
HOUSING_H = 6.6           # top housing above the plate
HOUSING_W_BOT = 15.0      # its width just above the plate
HOUSING_W_TOP = 11.4      # ...and at its top
HOUSING_CHAMFER = 1.2     # corner chamfer (45 deg) of the top housing
STEM_ABOVE = 3.6          # cross stem above the top housing, key up
TRAVEL = 4.0              # total travel
BOTTOM_W = 14.0           # bottom housing (through the plate)

# cap
SKIRT_WALL = 0.8
SKIRT_H = 1.2             # straight-ish flare from Ø17 to Ø15
SKIRT_CLEAR = 0.3         # pressed: skirt inside to housing corner
SOCKET_D = 5.6            # stem socket tube
CROSS = (4.15, 1.30)      # MX cross 4.0 x 1.17 + print allowance -- CHECK with the printer
SOCKET_DEPTH = 3.6
CHEQUER_CELL, CHEQUER_H, CHEQUER_R = 1.6, 0.35, 5.0


def z_housing_top():
    return C.Z_PLATE_TOP + HOUSING_H


def z_stem_top():
    return z_housing_top() + STEM_ABOVE


def housing_corner_r(h):
    """Distance from the switch axis to a top-housing corner, h above the plate."""
    w = HOUSING_W_BOT / 2 - (HOUSING_W_BOT - HOUSING_W_TOP) / 2 * min(h, HOUSING_H) / HOUSING_H
    return math.sqrt(2) * w - HOUSING_CHAMFER / math.sqrt(2)


def skirt_base_z():
    """Lowest skirt bottom (key up) for which, pressed, the skirt clears the
    housing corners. Above the housing top the corners don't matter."""
    r_in = C.D_SKIRT / 2 - SKIRT_WALL - SKIRT_CLEAR
    h = 0.0
    while h < HOUSING_H and housing_corner_r(h) > r_in:
        h += 0.01
    return C.Z_PLATE_TOP + h + TRAVEL


def cap(kind):
    zb = skirt_base_z()
    zt = C.Z_KEY_TOP - (CHEQUER_H if kind == "cf" else 0.0)
    rs, rd = C.D_SKIRT / 2, C.D_BTN / 2
    zs = zb + SKIRT_H
    # dome: circular arc through (rd, zs) and the apex (0, zt)
    sag = zt - zs
    R = (rd * rd + sag * sag) / (2 * sag)
    mid_a = math.asin(rd / R) / 2
    mid = (R * math.sin(mid_a), zt - R + R * math.cos(mid_a))
    prof = (cq.Workplane("XZ").moveTo(0, zb).lineTo(rs, zb).lineTo(rd, zs)
            .threePointArc(mid, (0, zt)).close())
    body = prof.revolve(360, (0, 0, 0), (0, 1, 0)).val()
    # the stem socket hangs below (the cross stem's top sits below the skirt)
    zst = z_stem_top()
    tube = C.cyl(0, 0, zst - SOCKET_DEPTH, zb + 0.01, SOCKET_D)
    body = body.fuse(tube)
    cross = C.box3(-CROSS[0] / 2, -CROSS[1] / 2, zst - SOCKET_DEPTH - 1, CROSS[0] / 2, CROSS[1] / 2, zst)
    cross = cross.fuse(C.box3(-CROSS[1] / 2, -CROSS[0] / 2, zst - SOCKET_DEPTH - 1, CROSS[1] / 2, CROSS[0] / 2, zst))
    body = body.cut(cross)
    if kind == "cf":
        # a raised diagonal chequer, following the dome
        raised = (cq.Workplane("XZ").moveTo(0, zb).lineTo(rs, zb).lineTo(rd, zs)
                  .threePointArc((mid[0], mid[1] + CHEQUER_H), (0, zt + CHEQUER_H)).close()
                  .revolve(360, (0, 0, 0), (0, 1, 0)).val())
        squares = []
        s = CHEQUER_CELL
        n = int(CHEQUER_R / s) + 2
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                if (i + j) % 2:
                    continue
                cx, cy = i * s, j * s
                if math.hypot(cx, cy) > CHEQUER_R - s / 2:
                    continue
                sq = (cq.Workplane("XY", origin=(0, 0, zt - 1.5)).center(cx, cy).rect(s, s)
                      .extrude(CHEQUER_H + 2).val())
                squares.append(sq)
        pattern = C.fuse(squares).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 45)
        body = body.fuse(pattern.intersect(raised))
    return body.clean()


def switch(x=0.0, y=0.0):
    """Stand-in switch: bottom housing, top housing (frustum), stem."""
    zp = C.Z_PLATE_TOP
    bot = C.box3(x - BOTTOM_W / 2, y - BOTTOM_W / 2, C.Z_PCB_TOP, x + BOTTOM_W / 2, y + BOTTOM_W / 2, zp - C.PLATE_T)
    top = cq.Solid.makeLoft([
        cq.Wire.makePolygon([cq.Vector(x + sx * HOUSING_W_BOT / 2, y + sy * HOUSING_W_BOT / 2, zp - C.PLATE_T)
                             for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))], close=True),
        cq.Wire.makePolygon([cq.Vector(x + sx * HOUSING_W_TOP / 2, y + sy * HOUSING_W_TOP / 2, z_housing_top())
                             for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))], close=True)])
    stem = C.cyl(x, y, z_housing_top(), z_stem_top(), 5.4)
    return bot.fuse(top, stem)


def all_switches():
    return cq.Compound.makeCompound([switch(x, y) for _, _, x, y, _ in C.keys()])


def test_print():
    """Four caps as four neighbouring buttons: a natural, a sharp, a C/F and
    another natural (rows 2/3 of the hex grid), joined by thin sprues so
    they print as one job. Cut the sprues off before fitting."""
    pos = [(0, 0, "natural"), (C.P, 0, "sharp"), (C.P / 2, -16.5, "cf"), (C.P * 1.5, -16.5, "natural")]
    caps = [cap(k).translate(cq.Vector(x, y, 0)) for x, y, k in pos]
    zb = skirt_base_z()
    sprues = [C.box3(C.D_SKIRT / 2 - 0.5, -0.6, zb, C.P - C.D_SKIRT / 2 + 0.5, 0.6, zb + 0.8),
              C.box3(C.P / 2 + C.D_SKIRT / 2 - 0.5, -16.5 - 0.6, zb, C.P * 1.5 - C.D_SKIRT / 2 + 0.5, -16.5 + 0.6, zb + 0.8)]
    return C.fuse(caps + sprues)


def report():
    zb = skirt_base_z()
    print("skirt bottom z %.2f (key up) = %.2f above the plate; pressed %.2f above the plate" % (
        zb, zb - C.Z_PLATE_TOP, zb - C.Z_PLATE_TOP - TRAVEL))
    print("cap height %.2f (skirt bottom to top), stem top z %.2f, socket tube from z %.2f" % (
        C.Z_KEY_TOP - zb, z_stem_top(), z_stem_top() - SOCKET_DEPTH))
    print("neighbouring skirts: %.2f mm apart (pitch %.2f, D%.0f)" % (C.P - C.D_SKIRT, C.P, C.D_SKIRT))


def main():
    report()
    for kind in ("natural", "sharp", "cf"):
        C.export(cap(kind), "keycap_" + kind, tol=0.01, mirror=False)
    C.export(test_print(), "keycap_test_4", tol=0.01, mirror=False)
    sw = C.to_file(all_switches())
    cq.exporters.export(cq.Workplane().add(sw), os.path.join(C.OUT, "switches.stl"), tolerance=0.05)


if __name__ == "__main__":
    main()
