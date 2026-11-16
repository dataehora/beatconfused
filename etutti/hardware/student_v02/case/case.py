"""eTutti Student V2: the case in separate, printable pieces (SPEC v1, finish Retro).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v02/case/case.py

Frame of the model: x right, y = -y of the SPEC (the SPEC's y runs towards the player), z up,
z = 0 at the board's top. Every function below takes the SPEC's x, y.

  base       grey tray, z -10.1 to -4.0: floor, low wall with a lip that enters the lid, a boss
             under each of the 6 lid screws, a cup under each of the 10 grid screws (the screw ends
             in a nut under the board, so the base comes off with 6 screws), 4 locating pins
             (into the board's holes H5-H8, between the keys), the support pillars under the
             keyboard, the battery's cradle, a tongue under each connector.
  tampa      cream lid, z -4.0 to 18.2: vertical walls, 30 deg chamfer 6 x 3.5 with R 1.5 on both
             edges, three grooves, the well of the keyboard (its wall is a flange that stops
             0.2 mm above the grid), window of the screen, holes of the two knobs, the speaker's
             slots, 6 posts for the screws, 2 bosses for the acoustic box, 4 clips' posts of the
             screen, openings of USB-C, OUT and IN.
  grade      keyboard grid, a flat 1.6 mm plate, z 11.6 to 13.2, one 6.2 mm hole per button,
             held by 10 M2 screws on its edge, under the lid.
  espacador  tube between board and grid (print 10).
  botao_<tipo>_f<fileira>   12 buttons: branco, preto, pontos x rows 1-4 (stem length).
  knob       hat knob for the EC11E with 20 mm shaft (print 2).
  caixa_acustica   the speaker's ring and closed back box, one piece.
  janela     the screen's window pane (cut from 1 mm smoked acrylic, or printed clear).

Writes out/*.step, out/*.stl and out/case.json (the numbers the fit check and the renders read).
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

OUT = os.path.join(HERE, "out")
BOARD_JSON = os.path.join(HERE, "..", "pcb", "board.json")
SUPPORTS_JSON = os.path.join(HERE, "..", "estudos", "apoios.json")

# ---- levels (z = 0 at the board's top)
Z0, ZS, ZT = G.Z_BASE, G.Z_SPLIT, G.Z_TOP          # -10.1, -4.0, 18.2
WALL, FLOOR, LID_T = 2.0, 2.0, 2.0
T_PCB = G.T_PCB
HOUSING_TOP = 11.2            # top of a switch's housing
STEM_TOP = 14.8               # top of a switch's cross, key up
TRAVEL = 4.1
GRID_Z0, GRID_T = 11.6, 1.6   # the grid: 0.4 above the housings
GRID_Z1 = GRID_Z0 + GRID_T    # 13.2 = the well's floor
FLANGE_GAP = 0.2
CHAMFER = (6.0, 3.5)          # horizontal, vertical
EDGE_R = 1.5
GROOVES = (8.0, 10.2, 12.4)   # centres
GROOVE_W, GROOVE_D = 0.8, 0.6
BASE_CHAMFER = 1.5
LIP_T, LIP_H, LIP_GAP = 1.2, 1.3, 0.15     # the lip stops 1.5 mm under the board: parts sit near its edge

# ---- keyboard
BUTTON_D, DOME_H, SKIRT_H, STEM_D = 15.0, 2.3, 1.2, 5.6
ROW_TOP = {1: 21.9, 2: 23.9, 3: 25.9, 4: 28.9}
GRID_HOLE, GRID_HOLE_CHAMFER = 6.2, 0.3
CROSS = (4.15, 1.30, 3.8)     # MX cross socket: arm length, arm width, depth
DIMPLE_D, DIMPLE_PITCH, DIMPLE_DEPTH = 0.66, 1.4, 0.22
WELL_R_TOP, WELL_R_BOTTOM = 2.5, 1.0
SPACER_D, SCREW_CLEAR, PILOT = 5.0, 2.3, 1.7
NOTES = {1: ["A3", "C4", "D#4", "F#4", "A4", "C5", "D#5"], 2: ["G3", "A#3", "C#4", "E4", "G4", "A#4", "C#5", "E5"],
         3: ["G#3", "B3", "D4", "F4", "G#4", "B4", "D5"], 4: ["A3", "C4", "D#4", "F#4", "A4", "C5"]}

# ---- interface
WINDOW = G.OLED_WINDOW
WINDOW_PANE_T, WINDOW_LEDGE = 1.0, 1.0
OLED_PCB = (27.3, 27.8, 1.6)      # the common 0.96 in module: board x, y, thickness
OLED_GLASS_T = 1.5
KNOB_HOLE = 9.2
KNOB = {"skirt_d": 12.0, "body_d": 9.0, "gap": 0.8, "top": ZT + 7.0, "sleeve_d": 8.2, "sleeve_z0": 13.6,
        "shaft_d": 6.0, "shaft_flat": 4.5, "shaft_top": 20.0, "bore_clear": 0.1}
SPK = G.SPEAKER
SPK_D, SPK_H = G.SPEAKER_D, 5.0
MESH_T, FOAM_T = 0.3, 1.0
BOX_WALL, BOX_FLOOR = 1.5, 1.2
BOX_Z0 = 1.4                   # outside bottom of the acoustic box (its inside starts at 2.6)
BOX_LEDGE = 1.2                # the speaker's rim sits on it
EAR_T, EAR_D = 2.0, 6.0
POST_D, POST_PILOT = 4.6, 1.6
BOSS_D, BOSS_HOLE, HEAD_D, HEAD_DEPTH = 6.0, 2.4, 4.4, 2.2
PILLAR_D, PIN_D, PIN_TIP_D, PIN_TIP_H = 4.0, 5.0, 2.0, 1.2 + 0.8
NUT_BOSS_D, NUT_POCKET_D, NUT_POCKET_H = 7.4, 5.2, 3.2      # M2 nut (4.6 across corners, 1.6 thick) and the screw's end
USB = {"y": G.USB_Y, "z": G.USB_Z, "w": 9.6, "h": 3.9}      # the canvas draws 9.2 x 3.6: the shell is 8.94 x 3.16
JACK_D = 6.8
BATTERY = (13.0, 56.0, 63.0, 90.0, 5.2)       # x0, y0, x1, y1, thickness (503450 with margin)
PROGRAM = (52.0, 36.0)


def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


BOARD = load(BOARD_JSON, {})
HOLES = BOARD.get("furos", {})
LID_HOLES = [tuple(v) for v in HOLES.get("tampa", {}).values()] or \
    [(88.0, 6.5), (74.0, 93.0), (6.5, 48.5), (8.0, 91.5), (238.0, 9.0), (238.0, 91.0)]
GRID_SCREWS = [tuple(p) for p in G.grid_screws()]
PINS = [tuple(v) for v in HOLES.get("pinos da base", {}).values()] or \
    [(98.45, 52.67), (153.95, 31.31), (153.95, 63.35), (209.45, 52.67)]
PILLARS = [tuple(p) for p in load(SUPPORTS_JSON, {}).get("pilares", [])]


# ------------------------------------------------------------------ helpers (SPEC x, y)
def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, -y).circle(d / 2).extrude(z1 - z0)


def box(x0, y0, x1, y1, z0, z1, r=0):
    w = (cq.Workplane("XY").workplane(offset=z0).center((x0 + x1) / 2, -(y0 + y1) / 2)
         .rect(x1 - x0, y1 - y0).extrude(z1 - z0))
    return w.edges("|Z").fillet(r) if r > 0 else w


def union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


def hull_wire(d):
    """The keyboard's hull grown by d, as a wire of 6 lines and 6 arcs (exact, so OCC can fillet it)."""
    H = G.HULL
    n = len(H)
    area = sum(H[i][0] * H[(i + 1) % n][1] - H[(i + 1) % n][0] * H[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    segs = []
    for i in range(n):
        a, b, c = H[i - 1], H[i], H[(i + 1) % n]

        def normal(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            return sgn * dy / L, -sgn * dx / L
        n1, n2 = normal(a, b), normal(b, c)
        m = (n1[0] + n2[0], n1[1] + n2[1])
        L = math.hypot(*m)
        segs.append(((b[0] + d * n1[0], b[1] + d * n1[1]), (b[0] + d * m[0] / L, b[1] + d * m[1] / L),
                     (b[0] + d * n2[0], b[1] + d * n2[1]), (c[0] + d * n2[0], c[1] + d * n2[1])))
    w = cq.Workplane("XY").moveTo(segs[0][0][0], -segs[0][0][1])
    for p0, pm, p1, pnext in segs:
        w = w.threePointArc((pm[0], -pm[1]), (p1[0], -p1[1])).lineTo(pnext[0], -pnext[1])
    return w.close()


def hull_prism(d, z0, z1):
    return hull_wire(d).extrude(z1 - z0).translate((0, 0, z0))


def outer(z0, z1, inset=0.0):
    r = G.CASE_R - inset
    return box(inset, inset, G.CASE[0] - inset, G.CASE[1] - inset, z0, z1, r)


# ------------------------------------------------------------------ lid
def chamfer_inner():
    """The lid's inside under the chamfer: the outside plane moved 2 mm inwards."""
    ang = math.atan2(CHAMFER[1], CHAMFER[0])
    drop = LID_T / math.cos(ang)
    slope = CHAMFER[1] / CHAMFER[0]
    z_at_wall = ZT - CHAMFER[1] + WALL * slope - drop          # where the inner plane meets the inner wall
    ceiling = ZT - LID_T
    return (ceiling - z_at_wall) / slope, ceiling - z_at_wall     # horizontal, vertical


def tampa():
    body = outer(ZS, ZT)
    body = body.faces(">Z").edges().chamfer(CHAMFER[1], CHAMFER[0])
    # R 1.5 on the chamfer's two edges
    body = body.edges(cq.selectors.BoxSelector((-1, -G.CASE[1] - 1, ZT - CHAMFER[1] - 0.2),
                                               (G.CASE[0] + 1, 1, ZT + 0.1))).fillet(EDGE_R)
    ch, cv = chamfer_inner()
    cav = outer(ZS - 1, ZT - LID_T, WALL).faces(">Z").edges().chamfer(cv, ch)
    body = body.cut(cav)
    # grooves all round
    for zc in GROOVES:
        ring = outer(zc - GROOVE_W / 2, zc + GROOVE_W / 2).cut(outer(zc - 1, zc + 1, GROOVE_D))
        body = body.cut(ring)
    ceiling = ZT - LID_T
    # the well: a flange down to just above the grid, then the opening
    flange_z0 = GRID_Z1 + FLANGE_GAP
    body = body.union(hull_prism(G.WELL_WALL + LID_T, flange_z0, ceiling + 0.01))
    body = body.cut(hull_prism(G.WELL_WALL, flange_z0 - 1, ZT + 1))
    sel_top = cq.selectors.BoxSelector((60, -100, ZT - 0.05), (245, 0, ZT + 0.05))
    body = body.edges(sel_top).fillet(WELL_R_TOP)
    sel_bot = cq.selectors.BoxSelector((60, -100, flange_z0 - 0.05), (245, 0, flange_z0 + 0.05))
    inner_bot = body.edges(sel_bot).edges(cq.selectors.RadiusNthSelector(0, directionMax=False)) if False else None
    try:
        body2 = body.faces(cq.selectors.BoxSelector((60, -100, flange_z0 - 0.05), (245, 0, flange_z0 + 0.05))).edges().fillet(WELL_R_BOTTOM * 0.95)
        body = body2
        bottom_r = WELL_R_BOTTOM * 0.95
    except Exception:
        bottom_r = 0.0
    # posts for the lid screws
    for x, y in LID_HOLES:
        body = body.union(cyl(x, y, 0.0, ceiling + 0.01, POST_D).intersect(outer(ZS, ZT)))
    # speaker: slots, and two bosses for the acoustic box
    g = G.GRILLE
    for i in range(g["n"]):
        y0 = g["y0"] + i * g["pitch"]
        body = body.cut(box(g["x0"], y0, g["x1"], y0 + g["slot"], ceiling - 1, ZT + 1, g["slot"] / 2 - 0.01))
    ear_top = box_levels()["ear_top"]
    for x, y in G.SPEAKER_SCREWS:
        body = body.union(cyl(x, y, ear_top, ceiling + 0.01, 5.0).cut(cyl(x, y, ear_top - 1, ceiling - 0.6, POST_PILOT)))
    # screen: window with a ledge for the pane, four posts with a step that hold the module's board
    wx0, wy0, wx1, wy1 = WINDOW
    body = body.cut(box(wx0, wy0, wx1, wy1, ceiling - 1, ZT + 1, 0.8))
    body = body.cut(box(wx0 - WINDOW_LEDGE, wy0 - WINDOW_LEDGE, wx1 + WINDOW_LEDGE, wy1 + WINDOW_LEDGE,
                        ceiling - 0.01, ceiling + WINDOW_PANE_T, 1.2))
    for (x, y) in oled_posts():
        body = body.union(cyl(x, y, oled_levels()["pcb_top"], ceiling + 0.01, 3.2)
                          .cut(cyl(x, y, oled_levels()["pcb_top"] - 1, ceiling - 0.8, 1.5)))
    # knobs
    for x, y in G.KNOBS:
        body = body.cut(cyl(x, y, ceiling - 1, ZT + 1, KNOB_HOLE))
    # screw pilots
    for x, y in LID_HOLES:
        body = body.cut(cyl(x, y, -0.01, ceiling - 1.0, POST_PILOT))
    # connectors: openings in the left wall, open downwards (the lid drops over the sockets)
    body = body.cut(box(-1, USB["y"] - USB["w"] / 2, WALL + 0.6, USB["y"] + USB["w"] / 2, ZS - 1, USB["z"] + USB["h"] / 2 - 0.9, 0))
    body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(-USB["y"], USB["z"])
                    .rect(USB["w"], USB["h"]).extrude(WALL + 1.6).edges("|X").fillet(USB["h"] / 2 - 0.05))
    for yc in (G.OUT_Y, G.IN_Y):
        body = body.cut(box(-1, yc - JACK_D / 2, WALL + 0.6, yc + JACK_D / 2, ZS - 1, G.JACK_Z, 0))
        body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(-yc, G.JACK_Z).circle(JACK_D / 2).extrude(WALL + 1.6))
    return body, bottom_r


def oled_levels():
    ceiling = ZT - LID_T
    glass_top = ceiling - 0.1                     # the glass 0.1 under the pane's ledge
    pcb_top = glass_top - OLED_GLASS_T
    return {"glass_top": glass_top, "pcb_top": pcb_top, "pcb_bottom": pcb_top - OLED_PCB[2]}


def oled_centre():
    wx0, wy0, wx1, wy1 = WINDOW
    # the module's active area is about 1.9 mm nearer its pin edge (the back) than the middle of its board
    return (wx0 + wx1) / 2, (wy0 + wy1) / 2 + 1.9


def oled_posts():
    cx, cy = oled_centre()
    dx, dy = OLED_PCB[0] / 2 - 2.0, OLED_PCB[1] / 2 - 2.0       # the module's four 2 mm holes
    return [(cx - dx, cy - dy), (cx + dx, cy - dy), (cx - dx, cy + dy), (cx + dx, cy + dy)]


# ------------------------------------------------------------------ base
def base():
    zf = Z0 + FLOOR
    body = outer(Z0, ZS).faces("<Z").edges().chamfer(BASE_CHAMFER)
    body = body.cut(outer(zf, ZS + 1, WALL))
    # lip that enters the lid
    lip = outer(ZS - 0.01, ZS + LIP_H, WALL + LIP_GAP).cut(outer(ZS - 1, ZS + LIP_H + 1, WALL + LIP_GAP + LIP_T))
    body = body.union(lip).union(outer(zf, ZS, WALL).cut(outer(zf - 1, ZS + 1, WALL + LIP_GAP + LIP_T)))
    under = -T_PCB
    for x, y in LID_HOLES:
        body = body.union(cyl(x, y, zf - 0.01, under, BOSS_D))
    for x, y in GRID_SCREWS:          # a cup under each grid screw: the board rests on its rim, the nut sits inside
        body = body.union(cyl(x, y, zf - 0.01, under, NUT_BOSS_D))
    for x, y in PINS:
        body = body.union(cyl(x, y, zf - 0.01, under, PIN_D)).union(cyl(x, y, under - 0.01, under + PIN_TIP_H, PIN_TIP_D)
                                                                    .faces(">Z").chamfer(0.4))
    for x, y in PILLARS:
        body = body.union(cyl(x, y, zf - 0.01, under, PILLAR_D))
    # battery cradle: low ribs on the back and the two ends
    bx0, by0, bx1, by1, _bt = BATTERY
    rib, h = 1.2, 2.0
    for r in ((bx0 - rib - 0.3, by0 - rib - 0.3, bx1 + rib + 0.3, by0 - 0.3),
              (bx0 - rib - 0.3, by0 - 0.3, bx0 - 0.3, by1 - 6), (bx1 + 0.3, by0 - 0.3, bx1 + rib + 0.3, by1 - 6)):
        body = body.union(box(r[0], r[1], r[2], r[3], zf - 0.01, zf + h))
    # tongues that close the lid's openings under the connectors
    t = box(0, USB["y"] - USB["w"] / 2 + 0.15, WALL, USB["y"] + USB["w"] / 2 - 0.15, ZS - 0.01, USB["z"] - USB["h"] / 2 - 0.1)
    body = body.union(t)
    for yc in (G.OUT_Y, G.IN_Y):
        t = box(0, yc - JACK_D / 2 + 0.15, WALL, yc + JACK_D / 2 - 0.15, ZS - 0.01, G.JACK_Z)
        t = t.cut(cq.Workplane("YZ").workplane(offset=-1).center(-yc, G.JACK_Z).circle(JACK_D / 2 + 0.1).extrude(WALL + 2))
        body = body.union(t)
    # holes
    for x, y in LID_HOLES:
        body = body.cut(cyl(x, y, Z0 - 1, 1, BOSS_HOLE)).cut(cyl(x, y, Z0 - 0.01, Z0 + HEAD_DEPTH, HEAD_D))
    for x, y in GRID_SCREWS:
        body = body.cut(cyl(x, y, under - NUT_POCKET_H, 1, NUT_POCKET_D))
    body = body.cut(cyl(PROGRAM[0], PROGRAM[1], Z0 - 1, zf + 1, 3.0))
    return body


# ------------------------------------------------------------------ grid, spacer
def grade():
    body = hull_prism(G.GRID_EDGE, GRID_Z0, GRID_Z1)
    pts = [(x, -y) for _, x, y in G.KEYS]
    body = body.cut(cq.Workplane("XY").workplane(offset=GRID_Z0 - 1).pushPoints(pts).circle(GRID_HOLE / 2).extrude(GRID_T + 2))
    for px, py in pts:
        cone = cq.Solid.makeCone(GRID_HOLE / 2, GRID_HOLE / 2 + GRID_HOLE_CHAMFER + 0.01, GRID_HOLE_CHAMFER + 0.01,
                                 pnt=cq.Vector(px, py, GRID_Z1 - GRID_HOLE_CHAMFER))
        body = body.cut(cq.Workplane("XY").add(cone))
    body = body.cut(cq.Workplane("XY").workplane(offset=GRID_Z0 - 1).pushPoints([(x, -y) for x, y in GRID_SCREWS])
                    .circle(SCREW_CLEAR / 2).extrude(GRID_T + 2))
    return body


def espacador():
    return cyl(0, 0, 0, GRID_Z0, SPACER_D).cut(cyl(0, 0, -1, GRID_Z0 + 1, SCREW_CLEAR))


# ------------------------------------------------------------------ buttons
def kind_of(note):
    if "#" in note:
        return "preto"
    return "pontos" if note[0] in "CF" else "branco"


def botao(kind, row):
    """A button, key up, at x = y = 0: stem foot on the switch housing, head top at the row's height."""
    top = ROW_TOP[row]
    under = top - DOME_H - SKIRT_H
    z0 = HOUSING_TOP
    stem = cq.Workplane("XY").workplane(offset=z0).circle(STEM_D / 2).extrude(under - z0 + 0.3)
    stem = stem.faces("<Z").chamfer(0.3)
    skirt = cq.Workplane("XY").workplane(offset=under).circle(BUTTON_D / 2).extrude(SKIRT_H)
    skirt = skirt.faces("<Z").edges().chamfer(0.3)
    r = (BUTTON_D ** 2 / 4 + DOME_H ** 2) / (2 * DOME_H)
    zc = top - r
    dome = cq.Workplane("XY").sphere(r).translate((0, 0, zc)).intersect(
        cq.Workplane("XY").workplane(offset=under + SKIRT_H - 0.001).circle(BUTTON_D).extrude(DOME_H + 1))
    body = stem.union(skirt).union(dome)
    L, w, d = CROSS
    cross = (cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(L, w).extrude(d)
             .union(cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(w, L).extrude(d)))
    body = body.cut(cross)
    n = 0
    if kind == "pontos":
        # dimples on a square grid turned 45 deg, all over the dome
        step = DIMPLE_PITCH
        rd = DIMPLE_D / 2
        rs = (rd ** 2 + DIMPLE_DEPTH ** 2) / (2 * DIMPLE_DEPTH)        # sphere that makes a dimple of this width and depth
        balls = None
        k = int(BUTTON_D / step) + 2
        for i in range(-k, k + 1):
            for j in range(-k, k + 1):
                u, v = (i + j) * step / math.sqrt(2), (i - j) * step / math.sqrt(2)
                if math.hypot(u, v) > BUTTON_D / 2 - 0.9:
                    continue
                zs = zc + math.sqrt(r * r - u * u - v * v)
                nx, ny, nz = u / r, v / r, (zs - zc) / r
                c = (u + nx * (rs - DIMPLE_DEPTH), v + ny * (rs - DIMPLE_DEPTH), zs + nz * (rs - DIMPLE_DEPTH))
                s = cq.Workplane("XY").sphere(rs).translate(c)
                balls = s if balls is None else balls.union(s)
                n += 1
        body = body.cut(balls)
    return body, {"topo": top, "cabeca_por_baixo": round(under, 2), "haste_mm": round(under - z0, 2), "covinhas": n}


# ------------------------------------------------------------------ knob
def knob():
    k = KNOB
    z_under = ZT + k["gap"]
    prof = [(0, z_under), (k["skirt_d"] / 2, z_under), (k["skirt_d"] / 2, z_under + 1.0),
            (k["body_d"] / 2, z_under + 1.8), (k["body_d"] / 2 - 0.3, k["top"] - 0.6), (k["body_d"] / 2 - 0.9, k["top"]),
            (0, k["top"])]
    hat = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    sleeve = cq.Workplane("XY").workplane(offset=k["sleeve_z0"]).circle(k["sleeve_d"] / 2).extrude(z_under - k["sleeve_z0"] + 0.01)
    body = hat.union(sleeve)
    # D bore for the shaft, from the sleeve's foot to 0.3 above the shaft's tip
    rb = k["shaft_d"] / 2 + k["bore_clear"]
    bore = cq.Workplane("XY").workplane(offset=k["sleeve_z0"] - 1).circle(rb).extrude(k["shaft_top"] + 0.3 - k["sleeve_z0"] + 1)
    flat_x = k["shaft_flat"] - k["shaft_d"] / 2 + k["bore_clear"]       # the flat's distance from the axis
    keep = (cq.Workplane("XY").workplane(offset=k["sleeve_z0"] - 2).center(flat_x + 5, 0).rect(10, 20)
            .extrude(k["shaft_top"] + 5))
    bore = bore.cut(keep)
    body = body.cut(bore)
    # the cream mark: a groove 0.8 wide on top, from the edge towards the middle (to be filled with paint)
    mark = cq.Workplane("XY").workplane(offset=k["top"] - 0.4).center(0, k["body_d"] / 4 + 0.3).rect(0.8, k["body_d"] / 2).extrude(1)
    body = body.cut(mark)
    return body, {"por_baixo": z_under, "topo": k["top"], "luva_ate": k["sleeve_z0"], "furo_ate": k["shaft_top"] + 0.3}


# ------------------------------------------------------------------ acoustic box
def box_levels():
    ceiling = ZT - LID_T
    front = ceiling - MESH_T - FOAM_T          # the speaker's front face
    back = front - SPK_H
    return {"front": front, "back": back, "inside_z0": BOX_Z0 + BOX_FLOOR, "ear_top": back + 0.6 + EAR_T,
            "rim_top": front - 0.5}


def caixa_acustica():
    lv = box_levels()
    x, y = SPK
    ri = SPK_D / 2 + 0.2                       # the speaker enters the upper part
    ro = ri + BOX_WALL
    body = cyl(x, y, BOX_Z0, lv["rim_top"], 2 * ro)
    # chamber below the ledge, speaker seat above it
    body = body.cut(cyl(x, y, lv["inside_z0"], lv["back"], 2 * (ri - BOX_LEDGE)))
    body = body.cut(cyl(x, y, lv["back"], lv["rim_top"] + 1, 2 * ri))
    for sx, sy in G.SPEAKER_SCREWS:
        ear = (cq.Workplane("XY").workplane(offset=lv["ear_top"] - EAR_T).center(sx, -(sy + y) / 2)
               .rect(EAR_D, abs(sy - y)).extrude(EAR_T)).union(cyl(sx, sy, lv["ear_top"] - EAR_T, lv["ear_top"], EAR_D))
        ear = ear.cut(cyl(x, y, BOX_Z0 - 1, lv["rim_top"] + 1, 2 * ri))
        body = body.union(ear).cut(cyl(sx, sy, lv["ear_top"] - EAR_T - 1, lv["ear_top"] + 1, 2.3))
    # the wires' hole, towards J501 (to be closed with a drop of silicone after the wires pass)
    ang = math.atan2(-(79.0 - y), 55.5 - x)
    hole = (cq.Workplane("XY").workplane(offset=lv["inside_z0"] + 2.0).center(x, -y)
            .transformed(rotate=(0, 90, 0)).circle(0.8).extrude(ro + 2).rotate((x, -y, 0), (x, -y, 1), math.degrees(ang)))
    body = body.cut(hole)
    chamber = math.pi * (ri - BOX_LEDGE) ** 2 * (lv["back"] - lv["inside_z0"]) / 1000
    return body, {"camara_cm3": round(chamber, 2), "interior_z": [lv["inside_z0"], lv["back"]], "fora_d": round(2 * ro, 1),
                  "fundo_por_fora_z": BOX_Z0, "frente_do_falante_z": lv["front"], "orelha_z": [lv["ear_top"] - EAR_T, lv["ear_top"]]}


def janela():
    wx0, wy0, wx1, wy1 = WINDOW
    c = 0.15
    return box(wx0 - WINDOW_LEDGE + c, wy0 - WINDOW_LEDGE + c, wx1 + WINDOW_LEDGE - c, wy1 + WINDOW_LEDGE - c,
               ZT - LID_T, ZT - LID_T + WINDOW_PANE_T, 1.0)


# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    info = {"pecas": {}}

    def export(name, w, extra=None):
        solids = w.solids().vals()
        bb = w.val().BoundingBox()
        vol = sum(s.Volume() for s in solids)
        info["pecas"][name] = dict({"solidos": len(solids), "volume_cm3": round(vol / 1000, 2),
                                    "caixa_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
                                    "z": [round(bb.zmin, 2), round(bb.zmax, 2)]}, **(extra or {}))
        cq.exporters.export(w, os.path.join(OUT, name + ".step"))
        cq.exporters.export(w, os.path.join(OUT, name + ".stl"), tolerance=0.02, angularTolerance=0.15)
        print(name, info["pecas"][name], flush=True)

    t, bottom_r = tampa()
    export("tampa", t, {"raio_de_baixo_da_aba": bottom_r})
    export("base", base())
    export("grade", grade())
    export("espacador", espacador())
    counts = {}
    for row, notes in NOTES.items():
        for n in notes:
            counts[(kind_of(n), row)] = counts.get((kind_of(n), row), 0) + 1
    for kind in ("branco", "preto", "pontos"):
        for row in (1, 2, 3, 4):
            w, d = botao(kind, row)
            export("botao_%s_f%d" % (kind, row), w, dict(d, imprimir=counts.get((kind, row), 0)))
    k, d = knob()
    export("knob", k, d)
    c, d = caixa_acustica()
    export("caixa_acustica", c, d)
    export("janela", janela())
    info["teclas"] = [{"fileira": r, "x": x, "y": y, "nota": NOTES[r][[k[1] for k in G.KEYS if k[0] == r].index(x)],
                       "tipo": kind_of(NOTES[r][[k[1] for k in G.KEYS if k[0] == r].index(x)])} for r, x, y in G.KEYS]
    info["niveis"] = {"base": Z0, "divisa": ZS, "tampo": ZT, "teto_da_tampa": ZT - LID_T, "grade": [GRID_Z0, GRID_Z1],
                      "aba_do_poco_ate": GRID_Z1 + FLANGE_GAP, "alojamento_da_tecla": HOUSING_TOP, "curso": TRAVEL,
                      "topo_dos_botoes": ROW_TOP, "piso_interno": Z0 + FLOOR, "oled": oled_levels(),
                      "chanfro_interno": [round(v, 2) for v in chamfer_inner()]}
    info["posicoes"] = {"parafusos_da_tampa": LID_HOLES, "parafusos_da_grade": GRID_SCREWS, "pinos": PINS, "pilares": PILLARS,
                        "bateria": BATTERY, "oled_centro": oled_centre(), "oled_postes": oled_posts(),
                        "falante": SPK, "parafusos_da_caixa": G.SPEAKER_SCREWS, "knobs": G.KNOBS}
    json.dump(info, open(os.path.join(OUT, "case.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
