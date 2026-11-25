"""eTutti Slim (R3SL): the case model (base + lid + LED ring) with the R3SL decisions applied. CadQuery.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/case.py

Frame (SPEC 1): x right, y towards the BACK, z up from the bottom of the base (right-handed: no mirroring on export). Writes case/out/{base,tampo,anel_led}.{step,stl}
and case/out/numeros.json (volumes, heights). Decisions applied (SPEC R3SL):
  * plan 249.5 x 89.1: B3 battery, +10.5 mm to the LEFT (x -100.5 .. 149);
  * main board bottom face z 6.8 (the P2 sets it) + a 0.6 mm pocket in the floor under the P2; USB-C hole (back wall, x -66, z 5.2), P2 hole (left wall, y 59.5, z 4.0);
  * registers platform +1.0 mm (the keys do not change); volume platform on the surface; wells D17.6 x 1.2; bearing collar; translucent LED ring D23.2/D20.8 x 1.5;
  * ruler support: two continuous rails per row (1.5 mm wide at |v| = 6.0..7.5), same type on the four rows, no holes in the floor, a pocket under each post of row 1.
Simplified on purpose: the walls are 2.0 mm, the lid skirt starts at the split z 8.0, the main board's own posts and the battery's pillars come with the main board (2b).
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_slim as L  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

LEFT, RIGHT, FRONT, BACK = -100.5, 149.0, -18.5, 70.6      # R3SL: +10.5 mm to the left (B3)
CORNER_R, WALL, SKIN = 6.0, 2.0, 1.5
SPLIT = L.SPLIT_Z
BOARD_BOT, BOARD_T = 6.8, 1.2
REG = (-46.0, 0.0)
VOL = (-46.0, 3 * L.D)
PLAT_R = 13.0
WELL_D, WELL_DEPTH, BEAR_D = 17.6, 1.2, 5.4
COLLAR_OD, COLLAR_H = 9.0, 3.0
RING_OD, RING_ID, RING_H = 23.2, 20.8, 1.5
USB = (-66.0, 5.2, 9.0, 3.6)                                 # x, z, width, height (back wall)
P2 = (59.5, 4.0, 6.2)                                       # y, z, diameter (left wall)
P2_POCKET = (-100.5 + 2.0, 55.0, -100.5 + 2.0 + 15.0, 64.0, 0.6)   # x0, y0, x1, y1, depth: under the P2
BAY = (-98.5, -14.5, -60.0, 54.0)                           # B3 bay x0, y0, x1, y1 (38.5 x 68.5)

# ---- the lid's top surface (SPEC 3 / conceito wave5 + sec7), independent copy
ROWZ = [10.6, 12.6, 14.6, 17.6]
SL = (ROWZ[1] - ROWZ[0]) / L.D
DSTEP = ROWZ[3] - (ROWZ[0] + SL * 3 * L.D)
Y0S, WS, YC, LC = 38.3, 3.6, 50.0, 12.0
OFF = L.HOUSING_TOP[0] + 3.16 - ROWZ[0]


def _ss(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def H(y):
    z = ROWZ[0] + SL * y + DSTEP * _ss((y - Y0S) / WS)
    if y > YC:
        u = min(y - YC, LC)
        z -= SL * u * u / (2 * LC) + (SL * (y - YC - LC) if y > YC + LC else 0)
    return z


def S(y):
    z = H(y) + OFF
    if y < FRONT + 4:
        t = (FRONT + 4 - y) / 4
        z -= 1.2 * (1 - math.sqrt(max(0, 1 - t * t)))
    if y > BACK - 6:
        t = (y - (BACK - 6)) / 6
        z -= 2.0 * (1 - math.sqrt(max(0, 1 - t * t)))
    return z


def plan(inset=0.0, z0=0.0, h=1.0):
    w, d = RIGHT - LEFT - 2 * inset, BACK - FRONT - 2 * inset
    return (cq.Workplane("XY").workplane(offset=z0).center((LEFT + RIGHT) / 2, (FRONT + BACK) / 2).rect(w, d).extrude(h)
            .edges("|Z").fillet(max(CORNER_R - inset, 0.5)))


def profile_solid(fn, z_min=0.0, inset=0.0, n=260):
    """Solid whose top is z = fn(y) (and bottom z_min), extruded along x over the plan, intersected with the plan outline."""
    y0, y1 = FRONT + inset, BACK - inset
    ys = [y0 + (y1 - y0) * i / n for i in range(n + 1)]
    pts = [(y, fn(y)) for y in ys] + [(y1, z_min), (y0, z_min)]
    prof = cq.Workplane("YZ").workplane(offset=LEFT - 1).polyline(pts).close().extrude(RIGHT - LEFT + 2)
    return prof.intersect(plan(inset, z_min - 1, 60))


def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(z1 - z0)


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def key_xy():
    for r in range(4):
        for k in range(L.NKEYS):
            yield r, k, L.ROW_X0[r] + L.P * k, L.ROW_Y[r]


# ====================================================================== base
def build_base():
    outer = plan(0, 0, SPLIT)
    inner = plan(WALL, L.FLOOR_T, SPLIT)                       # the cavity: floor 1.6, walls 2.0
    base = outer.cut(inner)
    # continuous support rails (|v| = 6.0 .. 7.5) under the long edges of every ruler, up to the ruler's bottom face
    for r in range(4):
        x0, x1 = L.ROW_X0[r] - L.U_KEY1, L.ROW_X0[r] - L.U_KEY1 + L.RULER_L
        zb = L.RULER_BOT[r]
        for sgn in (-1, 1):
            va, vb = 6.0, 6.0 + L.RAIL_W
            ya, yb = (L.ROW_Y[r] + sgn * va, L.ROW_Y[r] + sgn * vb)
            base = base.union(box(x0, min(ya, yb), L.FLOOR_T - 0.05, x1, max(ya, yb), zb))
    # pockets under the posts of row 1 (the post reaches z 1.3; floor under the pocket >= 1.0)
    for r, k, x, y in key_xy():
        if r == 0:
            base = base.cut(cyl(x, y, L.POST_BOTTOM, L.FLOOR_T + 0.1, L.POST_POCKET_D))
    # battery bay (B3, 38.5 x 68.5): low walls on its right and back sides
    base = base.union(box(BAY[2], BAY[1], L.FLOOR_T - 0.05, BAY[2] + 1.2, BAY[3] + 1.2, 7.0))
    base = base.union(box(BAY[0], BAY[3], L.FLOOR_T - 0.05, BAY[2] + 1.2, BAY[3] + 1.2, 7.0))
    # pocket under the P2 (0.6 mm into the floor: the floor under it is 1.0)
    x0, y0, x1, y1, dp = P2_POCKET
    base = base.cut(box(x0, y0, L.FLOOR_T - dp, x1, y1, L.FLOOR_T + 0.1))
    # wall holes: USB-C (back wall) and P2 (left wall)
    base = base.cut(box(USB[0] - USB[2] / 2, BACK - WALL - 1, USB[1] - USB[3] / 2, USB[0] + USB[2] / 2, BACK + 1, USB[1] + USB[3] / 2))
    base = base.cut(cq.Workplane("YZ").workplane(offset=LEFT - 1).center(P2[0], P2[1]).circle(P2[2] / 2).extrude(WALL + 2))
    return base


# ====================================================================== lid
def build_lid():
    top = profile_solid(S, SPLIT - 0.0)
    skin = profile_solid(lambda y: S(y) - SKIN, SPLIT - 0.0, inset=WALL)
    lid = top.cut(skin)
    lid = lid.cut(plan(0, -1, SPLIT + 1))                       # nothing below the split
    # per-key ceiling: down to the housing top + 0.3 (SPEC 3), disc D20 under every key
    for r, k, x, y in key_xy():
        ceil = L.HOUSING_TOP[r] + 0.3
        lid = lid.union(cyl(x, y, ceil, S(y) - SKIN + 0.05, 20.0))
    # platforms: flat discs; registers +1.0 mm
    zr = S(REG[1]) + 1.0
    zv = S(VOL[1])
    for (cx, cy), zp in ((REG, zr), (VOL, zv)):
        lid = lid.union(cyl(cx, cy, zp - 2.7, zp, 2 * PLAT_R)).cut(cyl(cx, cy, zp, zp + 12, 2 * PLAT_R + 0.1))
        lid = lid.union(cyl(cx, cy, zp - 2.7, zp - 2.0, 18.5))      # keeps 1.5 mm under the well floor (underside at zp - 2.7)
        lid = lid.cut(cyl(cx, cy, zp - WELL_DEPTH, zp + 1, WELL_D))
        lid = lid.union(cyl(cx, cy, zp - WELL_DEPTH - 0.01, zp - WELL_DEPTH + COLLAR_H, COLLAR_OD))
        lid = lid.cut(cyl(cx, cy, zp - 4.0, zp + 6, BEAR_D))
    # key holes: D16 through, D17 counterbore down to the housing top + 1.8
    for r, k, x, y in key_xy():
        lid = lid.cut(cyl(x, y, L.HOUSING_TOP[r] - 1.0, S(y) + 3, 16.0))
        lid = lid.cut(cyl(x, y, L.HOUSING_TOP[r] + 1.8, S(y) + 3, 17.0))
    # LED ring window around the volume knob (through slot, the ring sits at the top)
    ring_slot = cyl(VOL[0], VOL[1], zv - 3.0, zv + 1, RING_OD).cut(cyl(VOL[0], VOL[1], zv - 3.1, zv + 1.1, RING_ID))
    lid = lid.cut(ring_slot)
    return lid, zr, zv, ring_slot


def build_ring(zv):
    ring = cyl(VOL[0], VOL[1], zv - RING_H, zv, RING_OD).cut(cyl(VOL[0], VOL[1], zv - RING_H - 0.1, zv + 0.1, RING_ID))
    return ring


def export(name, wp):
    cq.exporters.export(wp, os.path.join(OUT, name + ".step"))
    cq.exporters.export(wp, os.path.join(OUT, name + ".stl"), tolerance=0.05, angularTolerance=0.1)


def main():
    base = build_base()
    lid, zr, zv, slot = build_lid()
    ring = build_ring(zv)
    export("base", base)
    export("tampo", lid)
    export("anel_led", ring)
    nums = {"planta": [RIGHT - LEFT, BACK - FRONT], "x": [LEFT, RIGHT], "y": [FRONT, BACK], "split_z": SPLIT,
            "tampo_z_centro_fileira": [round(S(y), 3) for y in L.ROW_Y], "plataforma_registros_z": round(zr, 3), "plataforma_volume_z": round(zv, 3),
            "poco_fundo_registros": round(zr - WELL_DEPTH, 3), "poco_fundo_volume": round(zv - WELL_DEPTH, 3),
            "face_de_baixo_sob_poco_registros": round(zr - 2.7, 3), "face_de_baixo_sob_poco_volume": round(zv - 2.7, 3),
            "tampo_borda_frente": round(S(FRONT + 0.5), 3), "tampo_max": round(max(S(FRONT + i * 0.3) for i in range(int((BACK - FRONT) / 0.3))), 3),
            "volume_cm3": {"base": round(base.val().Volume() / 1000, 2), "tampo": round(lid.val().Volume() / 1000, 2), "anel": round(ring.val().Volume() / 1000, 3)},
            "base_valida": base.val().isValid(), "tampo_valido": lid.val().isValid()}
    json.dump(nums, open(os.path.join(OUT, "numeros.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(nums, indent=1))


if __name__ == "__main__":
    main()
