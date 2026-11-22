"""eTutti Student V4 (R1V4 D2, R2V4 F2): the conceptual case with stepped rulers, parametric in the number of modules.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/case_f2.py [modules ...]   (default 0 1 2 3)

modules = 0, 1, 2, 3  ->  28, 44, 60, 76 keys; each module adds 4 keys to every row (4 x 18.5 = 74 mm).
No finish, no logo, no lettering (R1V4 decision 16): the interface is only an envelope. Frame: x right, y_spec towards the player,
z = 0 at the main board's top = the top of the ruler of row 1. Built with y_spec and mirrored (y -> -y) at the end so the
solids are right-handed.

Pieces (out/):
  f2_<n>_tampa      the lid: walls, the stepped deck (3 mm, 60 deg ramps, key holes) and the interface roof, posts for the fixing screws
  f2_<n>_base       the tray: 2 mm floor, two rails per row (ruler supports), ruler locating pins
  f2_<n>_reguas     the rulers (1.2 mm FR-4, 74 x 15.6, two pin holes, notches at the posts)
  f2_<n>_teclas     KS-20 stand-ins (housing, stem) + the pressed caps, for the fit check only
  f2_<n>_espuma     the foam rings (1.0 mm compressed)
  f2_<n>.json       numbers: volumes, boxes, clearances
"""
import json
import math
import os
import sys
import time

import cadquery as cq
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

PITCH, ROWP = G.PITCH, G.ROW_PITCH
ROWS = G.ROWS                         # (row, y, first x, keys); row 1 is the front one
CASE_W = 100.0                        # y of the front outer face
Y0 = 0.0                              # y of the back outer face (R8V4: case_r4 sets -2.0, a 102 mm deep case)
WALL, FLOOR = 2.0, 2.0
Z_BOT = -10.1                         # V3's outer bottom (SPEC v4); the interface keeps its depth
Z_FLOOR = Z_BOT + FLOOR               # = -8.1: tray top, boss bottoms (the reference plane Pm of the stack)
ZR = [0.0, 2.0, 4.0, 7.0]             # ruler tops (row 1..4): steps of 2, 2, 3 mm (R2V4)
RULER_T, RULER_L, RULER_W = 1.2, 4 * PITCH, 14.0
HOUSING_H = 11.10                     # KS-20 seat to top (drawing KS-20TF10B045NW-X72)
FOAM = 1.0                            # compressed foam between the housing top and the deck
DECK_T = 3.0                          # 3 mm deck (the study: t3_deck.py)
DECK_UNDER = HOUSING_H + FOAM         # 12.1 above the ruler top
DECK_TOP = DECK_UNDER + DECK_T        # 15.1
RAMP_START = 8.6                      # the ramp starts this far behind the lower row's centre (clears the pressed cap: r 8.25)
RAMP_TAN = math.tan(math.radians(60))  # 60 deg ramps: steeper than 45 so the underside clears the next row's housing (s = 3 mm)
KEY_HOLE = 8.0
X_IF = 79.0                           # interface | keyboard
IF_ROOF_TOP, IF_ROOF_T = DECK_TOP, 2.0
POST_D, POST_PILOT, BOSS_WALL_D = 5.0, 3.2, 6.0
BLADE_W = 1.4                         # the post's blade between two keys of a row (the corridor is 18.5 - 15.4 = 3.1 mm)
RAIL_IN, RAIL_OUT = 4.2, 7.0          # rail from |y| = 4.2 to 7.0 from the row centre (ruler 14.0 wide)
PIN_D, PIN_H, PIN_HOLE = 2.0, 2.5, 2.4
STEM_PLUS = 1.0                       # the single button's stem is 1 mm longer than the V3's (deck 3 mm); head top at ZR + 22.9
CAP_TOP, CAP_TRAVEL = 22.9, 4.1


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(z1 - z0)


def mirror(w):
    return w.mirror("XZ")


def length(mod):
    return 252.0 + 74.0 * mod


def key_list(mod):
    return [(r, x0 + i * PITCH, y) for r, y, x0, n in ROWS for i in range(n + 4 * mod)]


def rulers(mod):
    """(row, x start, y centre): ceil(n/4) rulers per row, each 4 positions (R2V4)."""
    out = []
    for r, y, x0, n in ROWS:
        n += 4 * mod
        for k in range(int(math.ceil(n / 4.0))):
            out.append((r, x0 - PITCH / 2 + k * RULER_L, y))
    return out


def triangles(mod):
    """Centroids of the 'type a' three-key triangles (two keys of row r, one of row r+1): free spots for a post, always on the
    back edge of a ruler (y centre - 5.34), at ruler x offsets 0, 18.5, 37, 55.5."""
    out = []
    for r in range(1, 4):
        _, y1, xa, na = ROWS[r - 1]
        _, y2, xb, nb = ROWS[r]
        na += 4 * mod
        nb += 4 * mod
        for i in range(na - 1):
            xm = xa + (i + 0.5) * PITCH
            j = (xm - xb) / PITCH
            if abs(j - round(j)) < 1e-6 and 0 <= round(j) < nb:
                out.append((round(xm, 3), round(y1 - ROWP / 3.0, 3)))
    return out


def pick_posts(mod):
    tri = [t for t in triangles(mod) if t[0] > X_IF + 8]
    n = {0: 10, 1: 16, 2: 22, 3: 28}[mod]
    idx = np.linspace(0, len(tri) - 1, n).astype(int)
    return [tri[i] for i in sorted(set(idx))]


def wall_posts(mod):
    """Perimeter bosses (every <= 80 mm along the long walls, plus the corners), centred 5 mm from the inner wall face."""
    L = length(mod)
    xs = [X_IF + 10.0, L - 8.0]
    n = int(math.ceil((xs[1] - xs[0]) / 80.0))
    xs = [xs[0] + (xs[1] - xs[0]) * k / n for k in range(n + 1)]
    pts = [(x, Y0 + 7.0) for x in xs] + [(x, CASE_W - 7.0) for x in xs]
    pts += [(7.0, Y0 + 12.0), (7.0, CASE_W - 12.0)]                  # interface side
    return pts


def deck_profile():
    """Top profile of the lid over the keyboard, y ascending from 0 to 100: (y, z)."""
    c = [r[1] for r in ROWS]
    s = [ZR[i + 1] - ZR[i] for i in range(3)]
    pts = [(CASE_W, ZR[0] + DECK_TOP)]
    for i in range(3):
        y0 = c[i] - RAMP_START
        pts += [(y0, ZR[i] + DECK_TOP), (y0 - s[i] / RAMP_TAN, ZR[i + 1] + DECK_TOP)]
    pts.append((Y0, ZR[3] + DECK_TOP))
    return sorted(pts)


def prism_yz(poly, x0, x1):
    """polygon in (y, z) extruded along x from x0 to x1."""
    return cq.Workplane("YZ").workplane(offset=x0).polyline(poly).close().extrude(x1 - x0)


def lid(mod):
    L = length(mod)
    top = deck_profile()
    # outer: from the bottom plane up to the top profile; inner (cavity): walls 2 mm, roof = profile - DECK_T
    outer_poly = [(Y0, Z_BOT)] + top + [(CASE_W, Z_BOT)]
    outer = prism_yz(outer_poly, X_IF, L)
    inner_top = [(max(Y0 + WALL, min(CASE_W - WALL, y)), z - DECK_T) for y, z in top]
    inner_top = [(y, z) for y, z in inner_top]
    # keep strictly increasing y after the clamp
    dedup = []
    for p in inner_top:
        if not dedup or p[0] > dedup[-1][0] + 1e-6:
            dedup.append(p)
        else:
            dedup[-1] = (dedup[-1][0], max(dedup[-1][1], p[1]))
    inner_poly = [(Y0 + WALL, Z_BOT - 1)] + dedup + [(CASE_W - WALL, Z_BOT - 1)]
    inner = prism_yz(inner_poly, X_IF - 0.0, L - WALL)
    kb = outer.cut(inner)
    # interface block: flat roof
    ifo = box(0, X_IF, Y0, CASE_W, Z_BOT, IF_ROOF_TOP)
    ifi = box(WALL, X_IF + 0.1, Y0 + WALL, CASE_W - WALL, Z_BOT - 1, IF_ROOF_TOP - IF_ROOF_T)
    ifb = ifo.cut(ifi)
    body = kb.union(ifb)
    # open the wall between interface and keyboard where the bands start (the cavity is continuous)
    # posts (interior at triangles, perimeter bosses)
    posts = [(x, y, ZR[0]) for x, y in pick_posts(mod)]
    for x, y in pick_posts(mod):
        ri = [r for r in range(1, 4) if abs(y - (ROWS[r - 1][1] - ROWP / 3.0)) < 0.05][0] - 1
        zt = ZR[ri] + DECK_UNDER + 0.5
        zb = ZR[ri] - RULER_T - 0.3                       # the round boss stops under the ruler; above it only the blade fits the 3.1 mm corridor
        body = body.union(cyl(x, y, Z_FLOOR, zb, POST_D)).union(box(x - BLADE_W / 2, x + BLADE_W / 2, y - 1.66, y + 2.34, zb - 0.5, zt))
    for x, y in wall_posts(mod):
        zt = IF_ROOF_TOP - IF_ROOF_T + 0.5 if x < X_IF else ZR[0] + DECK_UNDER + 0.5
        # perimeter bosses: up to the local roof underside (conservative: row 1 deck underside; the back wall posts reach the local one)
        zt = (ZR[3] + DECK_UNDER + 0.5) if (y < 18 and x >= X_IF) else zt
        body = body.union(cyl(x, y, Z_FLOOR, zt, BOSS_WALL_D))
    # key holes through the deck
    holes = None
    for r, x, y in key_list(mod):
        h = cyl(x, y, ZR[r - 1] + DECK_UNDER - 1.0, ZR[r - 1] + DECK_TOP + 1.0, KEY_HOLE)
        holes = h if holes is None else holes.union(h)
    body = body.cut(holes)
    # pilot holes in the posts (inserts from below, 6 mm deep)
    pil = None
    for x, y in pick_posts(mod) + wall_posts(mod):
        h = cyl(x, y, Z_FLOOR - 0.1, Z_FLOOR + 6.0, POST_PILOT)
        pil = h if pil is None else pil.union(h)
    body = body.cut(pil)
    return body


def base(mod):
    L = length(mod)
    gap = 0.15
    fl = box(WALL + gap, L - WALL - gap, Y0 + WALL + gap, CASE_W - WALL - gap, Z_BOT, Z_FLOOR)
    b = fl
    rail_cut = []
    for r, x0, y in rulers(mod):
        z1 = ZR[r - 1] - RULER_T
        for sgn in (-1, 1):
            ya, yb = sorted((y + sgn * RAIL_IN, y + sgn * RAIL_OUT))
            b = b.union(box(x0 + 0.2, x0 + RULER_L - 0.2, ya, yb, Z_FLOOR, z1))
        # two locating pins on the front rail, in the gaps between keys (start + 18.5 and start + 55.5)
        b = b.union(cyl(x0 + PITCH, y + 5.2, z1, z1 + PIN_H, PIN_D)).union(cyl(x0 + 3 * PITCH, y + 5.2, z1, z1 + PIN_H, PIN_D))
    # clear the rails where a post comes down (the post is 5 mm; 0.4 mm clearance) and drill the screw holes
    for x, y in pick_posts(mod):
        b = b.cut(cyl(x, y, Z_FLOOR - 0.1, Z_FLOOR + 30, POST_D + 0.8)).cut(box(x - 1.1, x + 1.1, y - 1.66 - 0.3, y + 2.34 + 0.3, Z_FLOOR - 0.1, Z_FLOOR + 30))
    cut = None
    for x, y in pick_posts(mod) + wall_posts(mod):
        h = cyl(x, y, Z_BOT - 0.1, Z_FLOOR + 0.1, 2.4).union(cyl(x, y, Z_BOT - 0.1, Z_BOT + 1.0, 4.2))
        cut = h if cut is None else cut.union(h)
    return b.cut(cut)


def rulers_solid(mod):
    res = None
    posts = pick_posts(mod)
    for r, x0, y in rulers(mod):
        z1 = ZR[r - 1]
        w = box(x0 + 0.2, x0 + RULER_L - 0.2, y - RULER_W / 2, y + RULER_W / 2, z1 - RULER_T, z1)
        w = w.cut(cyl(x0 + PITCH, y + 5.2, z1 - 2, z1 + 1, PIN_HOLE)).cut(cyl(x0 + 3 * PITCH, y + 5.2, z1 - 2, z1 + 1, PIN_HOLE))
        for px, py in posts:
            if abs(py - (y - ROWP / 3.0)) < 0.05 and x0 - 3 < px < x0 + RULER_L + 3:
                w = w.cut(box(px - 1.0, px + 1.0, y - 7.1, y - 2.7, z1 - 2, z1 + 1))
        res = w if res is None else res.union(w)
    return res


def key_bodies(mod, dz=0.0, with_cap=True):
    """KS-20 stand-ins on the rulers: bottom body 14 x 14 (0..5), housing 15.4 x 15.1 up to 8.4, tapered to 11.4 x 11.4 at 11.1,
    stem to 14.7; and the cap pressed (head top at ZR + 22.9 - 4.1)."""
    res = None
    for r, x, y in key_list(mod):
        z0 = ZR[r - 1] + dz
        k = box(x - 7.0, x + 7.0, y - 7.0, y + 7.0, z0, z0 + 5.0)
        k = k.union(box(x - 7.7, x + 7.7, y - 7.55, y + 7.55, z0 + 5.0, z0 + 8.4))
        top = (cq.Workplane("XY").workplane(offset=z0 + 8.4).center(x, y).rect(15.4, 15.1)
               .workplane(offset=2.7).rect(11.4, 11.4).loft(ruled=True))
        k = k.union(top).union(cyl(x, y, z0 + 11.1, z0 + 14.7, 4.2))
        if with_cap:
            zt = z0 + CAP_TOP - CAP_TRAVEL
            cap = cyl(x, y, zt - 3.5, zt - 2.3, 16.5).union(cyl(x, y, zt - 2.3, zt - 0.0, 15.0)).union(cyl(x, y, z0 + 11.1 - CAP_TRAVEL + 3.0, zt - 3.5, 5.6))
            k = k.union(cap)
        res = k if res is None else res.union(k)
    return res


def foam_rings(mod):
    res = None
    for r, x, y in key_list(mod):
        z0 = ZR[r - 1] + HOUSING_H
        f = box(x - 5.5, x + 5.5, y - 5.5, y + 5.5, z0, z0 + FOAM).cut(cyl(x, y, z0 - 1, z0 + FOAM + 1, 8.4))
        res = f if res is None else res.union(f)
    return res


def vol(w):
    return sum(s.Volume() for s in w.solids().vals())


def inter(a, b):
    try:
        return vol(a.intersect(b))
    except Exception as e:      # noqa: BLE001
        return float("nan")


def build(mod):
    t0 = time.time()
    n = 28 + 16 * mod
    L = length(mod)
    lid_ = lid(mod)
    base_ = base(mod)
    ru = rulers_solid(mod)
    foam = foam_rings(mod)
    info = {"teclas": n, "modulos": mod, "comprimento_mm": L, "largura_mm": CASE_W,
            "z_baixo": Z_BOT, "z_topo_tampa": ZR[3] + DECK_TOP, "altura_atras_mm": round(ZR[3] + DECK_TOP - Z_BOT, 2),
            "altura_frente_mm": round(ZR[0] + DECK_TOP - Z_BOT, 2),
            "reguas": len(rulers(mod)), "posicoes_de_regua": 4 * len(rulers(mod)),
            "postes_internos": len(pick_posts(mod)), "bossas_de_parede": len(wall_posts(mod)),
            "volume_cm3": {"tampa": round(vol(lid_) / 1000, 1), "base": round(vol(base_) / 1000, 1)}}
    # fit check, at nominal and with the housings 0.5 mm too tall (a +0.4 housing + ruler)
    keys0 = key_bodies(mod, 0.0)
    keys5 = key_bodies(mod, 0.5)
    info["interferencias_mm3"] = {
        "tampa x teclas (nominal)": round(inter(lid_, keys0), 2), "tampa x teclas (+0,5 mm)": round(inter(lid_, keys5), 2),
        "base x teclas": round(inter(base_, keys0), 2), "base x reguas": round(inter(base_, ru), 2),
        "tampa x reguas": round(inter(lid_, ru), 2), "tampa x base": round(inter(lid_, base_), 2)}
    # export (mirrored: right-handed)
    for name, w in (("tampa", lid_), ("base", base_), ("reguas", ru), ("teclas", keys0), ("espuma", foam)):
        m = mirror(w)
        cq.exporters.export(m, os.path.join(OUT, "f2_%d_%s.stl" % (n, name)), tolerance=0.05, angularTolerance=0.2)
        if name in ("tampa", "base") and mod in (0, 3):
            cq.exporters.export(m, os.path.join(OUT, "f2_%d_%s.step" % (n, name)))
    info["segundos"] = round(time.time() - t0, 1)
    json.dump(info, open(os.path.join(OUT, "f2_%d.json" % n), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(info, indent=1, ensure_ascii=False), flush=True)
    return info


if __name__ == "__main__":
    mods = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3]
    for m in mods:
        build(m)
