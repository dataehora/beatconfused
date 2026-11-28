"""eTutti Slim (R4SL): the case model (base + lid + LED ring) with the R3SL and R4SL decisions applied. CadQuery.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/case.py

Frame (SPEC 1): x right, y towards the BACK, z up from the bottom of the base (right-handed: no mirroring on export). Writes case/out/{base,tampo,anel_led}.{step,stl}
and case/out/numeros.json (volumes, heights). Decisions applied (SPEC R3SL):
  * R4SL: the battery is the VARTA 56457 201 016 (LPP 523450, 34.5 x 52 x 5.35): bay 36.0 x 60.0, case +8.0 mm to the LEFT (x -98.0 .. 149, plan 247.0 x 89.1);
  * R4SL: platforms follow the lid (S2): top = lid + 1.0 (registers) / + 0 (volume), HORIZONTAL well floor, vertical bore, flat horizontal knob top;
  * main board bottom face z 6.8 (the P2 sets it) + a 0.6 mm pocket in the floor under the P2; USB-C hole (back wall, x -66, z 5.2), P2 hole (left wall, y 59.5, z 4.0);
  * registers platform +1.0 mm (the keys do not change); volume platform on the surface; wells D19.0 (R5SL: skirt D18.4); bearing collar; translucent LED ring D23.2/D20.8 x 1.5;
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
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import verificacao as V  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

LEFT, RIGHT, FRONT, BACK = -98.0, float(os.environ.get("SLIM_CASE_RIGHT", 149.0)), -18.5, 70.6       # R4SL: +8.0 mm to the left (battery 523450); R12SL: right wall at 149.0: plan 247.0 x 89.1; the keyboard moved 1.5 mm right (layout_slim.KEY_DX), so the longest rulers (rows 1 and 3) end at x 143.65: 3.35 mm to the wall's inner face (147.0)
CORNER_R, WALL, SKIN = 6.0, 2.0, 1.5
SPLIT = L.SPLIT_Z
BOARD_BOT, BOARD_T = 6.8, 1.2
REG = (-46.0, 0.0)
VOL = (-46.0, 3 * L.D)
PLAT_R = 13.0
WELL_D, WELL_DEPTH, BEAR_D = 19.0, 1.2, 5.4                  # R5SL: well D19.0 (was 17.6) takes the knob's skirt D18.4 (0.3 mm radial)
KNOB_SKIRT_D = 18.4
KEY_HOLE_D = 11.0                                            # R5SL: D11 through, no counterbore (only the button's D10 shank passes)
COLLAR_OD, COLLAR_H = 9.0, 3.0
RING_OD, RING_ID, RING_H = 23.2, 20.8, 1.5
S2_RISE_VOL = 1.0                                            # R4SL item 3: S2 = lid + 1.0 on both knobs
MAG_UNDER = 12.31                                            # underside of the lid under a knob: magnet top 11.0 + 0.5 skin + 0.8 axial play
USB = (-66.0, 5.2, 9.0, 3.6)                                 # x, z, width, height (back wall)
P2 = (59.5, 4.0, 6.2)                                       # y, z, diameter (left wall)
P2_POCKET = (LEFT + 2.0, 55.0, LEFT + 2.0 + 15.0, 64.0, 0.6)       # x0, y0, x1, y1, depth: under the P2
BAY = (-96.0, -14.5, -60.0, 45.5)                           # R4SL bay x0, y0, x1, y1 (36.0 x 60.0): 34.5 x 52 battery + 0.75 each side, wires/PCM end at the back
BATT = (34.5, 52.0, 5.35)                                    # VARTA 56457 201 016: width, length, thickness (datasheet 5.3, STEP 5.36)
WIRE_SLOT = (-82.0, -74.0, 3.0)                             # x0, x1, z0: notch in the bay's back wall for the three wires
POSTS = [(-55.5, -7.0), (-40.5, 8.5), (-40.0, 63.5), (-93.0, 52.0), (-75.0, 64.0)]   # R11SL: the two right-hand posts moved 1.5 mm left with the strip's edge (the rulers grew to the left)   # main-board supports (D6 from the floor to z 6.8)

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
    # R11SL: the rails (|v| = 6.0 .. 7.5) run exactly from one M2 axis to the other; at each M2 a centred GUIDE (pedestal D6.0 up to the ruler's bottom face) holds the nut in
    # a hex pocket (4.6 across corners, 1.6 deep) and a relief D2.6 for the screw's tip. Nothing of the ruler outside the two screws touches the base (the ends hang free).
    for r in range(4):
        x0 = L.ROW_X0[r] - L.U_KEY1
        zb = L.RULER_BOT[r]
        xa, xb = x0 + L.M2_ENDS[0], x0 + L.M2_ENDS[1]
        for sgn in (-1, 1):
            va, vb = 6.0, 6.0 + L.RAIL_W
            ya, yb = (L.ROW_Y[r] + sgn * va, L.ROW_Y[r] + sgn * vb)
            base = base.union(box(xa, min(ya, yb), L.FLOOR_T - 0.05, xb, max(ya, yb), zb))
        for xg in (xa, xb):
            base = base.union(cyl(xg, L.ROW_Y[r], L.FLOOR_T - 0.05, zb, L.GUIDE_D))
            hexp = cq.Workplane("XY").workplane(offset=zb - 1.6).center(xg, L.ROW_Y[r]).polygon(6, 4.7).extrude(1.7).rotate((xg, L.ROW_Y[r], 0), (xg, L.ROW_Y[r], 1), 30)   # flats face +-x
            base = base.cut(hexp).cut(cyl(xg, L.ROW_Y[r], L.FLOOR_T - 0.6, zb - 1.5, 2.6))
        # R12SL: relief on the face of the LEFT guide that looks at U9: a flat at 2.65 from the axis (the guide's radius is 3.0), so the guide stays >= 0.5 mm from U9's courtyard
        # (U9 ends at u 9.95, the flat is at u 10.45); the wall to the nut's pocket flat (2.035 from the axis) is then 0.615 mm
        base = base.cut(box(xa - 3.2, L.ROW_Y[r] - 3.2, L.FLOOR_T - 0.05, xa - L.GUIDE_FLAT, L.ROW_Y[r] + 3.2, zb + 0.01))
    # pockets under the posts of row 1 (the post reaches z 1.3; floor under the pocket >= 1.0)
    for r, k, x, y in key_xy():
        if r == 0:
            base = base.cut(cyl(x, y, L.POST_BOTTOM, L.FLOOR_T + 0.1, L.POST_POCKET_D))
    # battery bay (R4SL, 36.0 x 60.0): low walls on its right and back sides, a notch for the wires in the back wall
    base = base.union(box(BAY[2], BAY[1], L.FLOOR_T - 0.05, BAY[2] + 1.2, BAY[3] + 1.2, 7.0))
    back = box(BAY[0], BAY[3], L.FLOOR_T - 0.05, BAY[2] + 1.2, BAY[3] + 1.2, 7.0)
    back = back.cut(box(WIRE_SLOT[0], BAY[3] - 1, WIRE_SLOT[2], WIRE_SLOT[1], BAY[3] + 2.5, 8.0))
    base = base.union(back)
    # main-board supports: D6 posts from the floor to the board's bottom face (z 6.8), pilot D1.75 for a thread-forming M2
    for px, py in POSTS:
        base = base.union(cyl(px, py, L.FLOOR_T - 0.05, BOARD_BOT, 6.0)).cut(cyl(px, py, L.FLOOR_T + 1.0, BOARD_BOT + 0.1, 1.75))
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
    # platforms (R4SL, S2): the boss follows the lid (top = S(y) + raise), the well floor is HORIZONTAL (depth 1.2 at the axis, shallower in front, deeper
    # behind), the bore is vertical, the collar is a horizontal ring.  Registers: +1.0 mm; volume: on the lid (+0).
    zr = S(REG[1]) + 1.0
    zv = S(VOL[1]) + S2_RISE_VOL
    for (cx, cy), rise in ((REG, 1.0), (VOL, S2_RISE_VOL)):
        zc = S(cy) + rise
        zf = S(cy - WELL_D / 2) + rise - 0.1                 # horizontal floor: 0.1 mm deep at the front rim (registers: 13.81, as in the R3SL)
        boss = cyl(cx, cy, zf - 1.5, zc + 4.0, 2 * PLAT_R).intersect(profile_solid(lambda y, r=rise: S(y) + r, SPLIT))
        lid = lid.union(boss)
        lid = lid.cut(cyl(cx, cy, zf, zc + 8.0, WELL_D))
        lid = lid.union(cyl(cx, cy, zf - 0.01, zf + COLLAR_H, COLLAR_OD))
        if zf - 1.5 > MAG_UNDER + 0.5:                          # retention tube under the lid (volume): keeps the head's 0.8 mm axial play
            lid = lid.union(cyl(cx, cy, MAG_UNDER, zf - 1.4, COLLAR_OD))
        lid = lid.cut(cyl(cx, cy, zf - 4.0, zf + COLLAR_H + 1, BEAR_D))
    # key holes (R5SL): D11 straight through, no counterbore
    for r, k, x, y in key_xy():
        lid = lid.cut(cyl(x, y, L.HOUSING_TOP[r] - 1.0, S(y) + 3, KEY_HOLE_D))
    # LED ring window around the volume knob: a vertical annular slot through the boss (the ring follows the lid, 1.5 mm thick)
    ring_slot = cyl(VOL[0], VOL[1], SPLIT - 0.1, zv + 6, RING_OD).cut(cyl(VOL[0], VOL[1], SPLIT - 0.2, zv + 6.1, RING_ID))
    lid = lid.cut(ring_slot)
    return lid, zr, zv, ring_slot


def build_ring(zv):
    ann = cyl(VOL[0], VOL[1], SPLIT, zv + 6, RING_OD).cut(cyl(VOL[0], VOL[1], SPLIT - 0.1, zv + 6.1, RING_ID))
    top = ann.intersect(profile_solid(S, SPLIT - 0.5))
    return top.cut(ann.intersect(profile_solid(lambda y: S(y) - RING_H, SPLIT - 0.5)))


def export(name, wp):
    cq.exporters.export(wp, os.path.join(OUT, name + ".step"))
    cq.exporters.export(wp, os.path.join(OUT, name + ".stl"), tolerance=0.05, angularTolerance=0.1)


def main():
    T0 = V.inicio()
    if RIGHT <= LEFT + 50:
        V.falha("RIGHT = %s: case sem largura" % RIGHT)
    base = build_base()
    lid, zr, zv, slot = build_lid()
    ring = build_ring(zv)
    if not (base.val().isValid() and lid.val().isValid() and ring.val().isValid()):
        V.falha("sólido inválido: base %s, tampo %s, anel %s (nada foi gravado)" % (base.val().isValid(), lid.val().isValid(), ring.val().isValid()))
    V.forcar("case")
    export("base", base)
    export("tampo", lid)
    export("anel_led", ring)
    nums = {"planta": [RIGHT - LEFT, BACK - FRONT], "x": [LEFT, RIGHT], "y": [FRONT, BACK], "split_z": SPLIT,
            "tampo_z_centro_fileira": [round(S(y), 3) for y in L.ROW_Y], "plataforma_registros_z": round(zr, 3), "plataforma_volume_z": round(zv, 3),
            "poco_fundo_registros": round(S(REG[1] - WELL_D / 2) + 1.0 - 0.1, 3), "poco_fundo_volume": round(S(VOL[1] - WELL_D / 2) + S2_RISE_VOL - 0.1, 3),
            "face_de_baixo_sob_poco_registros": round(S(REG[1] - WELL_D / 2) + 1.0 - 1.6, 3), "face_de_baixo_sob_poco_volume": round(S(VOL[1] - WELL_D / 2) + S2_RISE_VOL - 1.6, 3),
            "bateria": {"modelo": "VARTA 56457 201 016", "baia": [BAY[2] - BAY[0], BAY[3] - BAY[1]], "crescimento_esquerda_mm": -90.0 - LEFT, "pilares_placa": POSTS},
            "tampo_borda_frente": round(S(FRONT + 0.5), 3), "tampo_max": round(max(S(FRONT + i * 0.3) for i in range(int((BACK - FRONT) / 0.3))), 3),
            "volume_cm3": {"base": round(base.val().Volume() / 1000, 2), "tampo": round(lid.val().Volume() / 1000, 2), "anel": round(ring.val().Volume() / 1000, 3)},
            "base_valida": base.val().isValid(), "tampo_valido": lid.val().isValid()}
    json.dump(nums, open(os.path.join(OUT, "numeros.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(nums, indent=1))
    V.exige([os.path.join(OUT, n) for n in ("base.step", "base.stl", "tampo.step", "tampo.stl", "anel_led.step", "numeros.json")], T0, "case")


if __name__ == "__main__":
    main()
