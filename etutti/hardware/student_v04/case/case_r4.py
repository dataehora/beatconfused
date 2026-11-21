"""eTutti Student V4 (R4V4): the case with the real interface (battery, speaker, box, OLED, knobs, sockets), the T3-G keyboard
and the rulers' connectors, parametric in the number of modules.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/case_r4.py [modules ...]   (default 0)

Builds on case_t3g.py / case_f2.py (their constants are patched) and layout_r4.py (the positions). What R4V4 adds or changes:
  * interface: lid posts on the board's holes H1..H4 (D6, M2 insert), the sockets' holes in the left wall (USB-C at y 10), knob holes,
    the OLED window, the speaker's slots; the tray's bosses under H1..H4, the battery cradle, the module's recess (42; 14), the PROG hole;
  * keyboard: M2 positions per row (so no M2 boss meets a connector's notch), real D6 bosses with the insert's pilot (R3V4 had only
    the 2.8 mm rail), interior posts never on a ruler's junction;
  * connectors (task 3): header + plug + notches, in the back lane of every ruler.
Out (case/out/, ignored by git): r4_<n>_*.stl, r4_<n>.json. The numbers worth keeping are copied to estudos/r4v4.json.
"""
import json
import math
import os
import sys
import time

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402
import case_t3g as T     # noqa: E402
import case_f2 as F      # noqa: E402
import case as C3        # noqa: E402  (the V3 case's functions: knob and acoustic box, patched below)

OUT = F.OUT
G = L.G
box, cyl, vol, inter, mirror = F.box, F.cyl, F.vol, F.inter, F.mirror

# ---- the V3 functions read module globals: bring them to the R4V4 levels
C3.ZT = L.ROOF_TOP
C3.SPK_H = L.SPK_H
C3.KNOB["top"] = L.ROOF_TOP + 11.3
C3.KNOB["sleeve_z0"] = L.ROOF_TOP + 0.8
# ---- the keyboard: posts and M2 positions
F.pick_posts = L.pick_posts
F.wall_posts = L.wall_posts
T.pick_posts = L.pick_posts
# R5V4: 32 keys (rulers always full) and the shorter case
F.ROWS = L.ROWS
F.length = L.length
CHAMFER_TOP, CHAMFER_BOT = 2.0, 1.0       # R5V4: 45 deg chamfer on the outer top edge (where the hand rests) and a small one on the bottom edge
R_OUT, R_IN = L.CASE_R, L.CASE_R - L.WALL

USB = {"y": L.USB_Y, "z": G.USB_Z, "w": G.USB_OPENING[0], "h": G.USB_OPENING[1], "r": G.USB_OPENING[2]}
JACK_D, JACK_Z = G.JACK_OPENING_D, G.JACK_Z
KNOB_HOLE = C3.KNOB_HOLE
POST_D = 5.4                  # the V3 had 4.6; 5.4 keeps 1.1 mm round the insert's pilot and 0.2 mm clear of the acoustic box at H4
BOARD_Z = (-L.T_PCB, 0.0)
GRADE_W = 16.0                # the electronics' grade-regua strip (1 mm of border each side of the 14.00 openings)


# ------------------------------------------------------------------ plan corners and chamfers (R5V4)
def _tri_x(x0, x1, z, c, left):
    """Wedge along y direction: triangle in (x, z) (extruded later along y). left: edge at x = x0; else edge at x = x1."""
    if left:
        return [(x0 - 1, z - c - 1), (x0 + c + 1, z + 1), (x0 - 1, z + 1)]
    return [(x1 + 1, z - c - 1), (x1 - c - 1, z + 1), (x1 + 1, z + 1)]


def chamfer_cutters(mod, c, top_of, flat=False, up=True):
    """Solids to cut from an outer shell so that its outer edge gets a c x c, 45 degree chamfer, following the outline (plan R_OUT corners).
    top_of(x, y) = the shell's top level near that edge point. flat=True: one level everywhere (the bottom edge, drawn mirrored)."""
    Lx = L.length(mod)
    R = R_OUT
    cut = []
    # straight edges
    xs = [R, Lx - R]
    ys = [R, L.CASE[1] - R]
    # left edge (x = 0): interface roof
    z = top_of(1.0, 50.0)
    cut.append(cq.Workplane("XZ").polyline(_tri_x(0, 0, z, c, True)).close().extrude(-(ys[1] - ys[0])).translate((0, ys[0], 0)))
    # front edge (y = 100): flat
    z = top_of(150.0, 99.0)
    tri = [(L.CASE[1] + 1, z - c - 1), (L.CASE[1] - c - 1, z + 1), (L.CASE[1] + 1, z + 1)]
    cut.append(cq.Workplane("YZ").workplane(offset=xs[0]).polyline(tri).close().extrude(xs[1] - xs[0]))
    # back edge (y = 0): two levels (interface roof, keyboard back deck)
    for xa, xb in ((xs[0], L.X_IF), (L.X_IF, xs[1])):
        z = top_of((xa + xb) / 2, 1.0)
        tri = [(-1, z - c - 1), (c + 1, z + 1), (-1, z + 1)]
        cut.append(cq.Workplane("YZ").workplane(offset=xa).polyline(tri).close().extrude(xb - xa))
    # right end (x = L): follows the deck's profile: ONE ruled loft between a sliver above the profile and the full wedge
    prof = [(y, z) for y, z in F.deck_profile()] if not flat else [(0.0, 0.0), (L.CASE[1], 0.0)]
    pts = [(ys[0], None)] + [p for p in prof if ys[0] < p[0] < ys[1]] + [(ys[1], None)]

    def zat(y):
        for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
            if ya <= y <= yb:
                return za + (zb - za) * (y - ya) / (yb - ya) if yb > ya else za
        return prof[-1][1]
    pts = [(y, zat(y) if z is None else z) for y, z in pts]
    x1, x2 = Lx - c - 0.2, Lx + 1.0

    def poly(x):
        s = x - (Lx - c)
        return [(y, z - s) for y, z in pts] + [(y, z + 3.0) for y, z in reversed(pts)]
    w = (cq.Workplane("YZ").workplane(offset=x1).polyline(poly(x1)).close()
         .workplane(offset=x2 - x1).polyline(poly(x2)).close().loft(ruled=True))
    cut.append(w)
    # corners: a cone each (revolved triangle) limited to its quadrant
    for cx, cy, sx, sy in ((R, R, -1, -1), (Lx - R, R, 1, -1), (R, L.CASE[1] - R, -1, 1), (Lx - R, L.CASE[1] - R, 1, 1)):
        z = top_of(cx, cy) if not flat else 0.0
        tri = [(R - c - 1, z + 1), (R + 1, z - c - 1), (R + 1, z + 1)]
        cone = cq.Workplane("XZ").polyline(tri).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((cx, cy, 0))
        quad = box(min(cx, cx + sx * (R + 2)), max(cx, cx + sx * (R + 2)), min(cy, cy + sy * (R + 2)), max(cy, cy + sy * (R + 2)), z - c - 3, z + 3)
        cut.append(cone.intersect(quad))
    return cut


def top_level(x, y):
    """Outer top of the lid near the point (x, y), used for the top chamfer: interface roof, row 1's deck in front, row 4's at the back."""
    if x < L.X_IF:
        return L.ROOF_TOP
    return F.ZR[3] + F.DECK_TOP if y < 20.0 else F.ZR[0] + F.DECK_TOP


def round_and_chamfer_lid(body, mod):
    """Plan corners R_OUT outside / R_IN inside, then the chamfers (top c = CHAMFER_TOP following the deck, bottom c = CHAMFER_BOT)."""
    Lx, W = L.length(mod), L.CASE[1]
    zlo, zhi = L.Z_BOT - 1.0, 40.0
    outer = box(0, Lx, 0, W, zlo, zhi).edges("|Z").fillet(R_OUT)
    body = body.intersect(outer)
    for cx, cy, sx, sy in ((R_OUT, R_OUT, -1, -1), (Lx - R_OUT, R_OUT, 1, -1), (R_OUT, W - R_OUT, -1, 1), (Lx - R_OUT, W - R_OUT, 1, 1)):
        # the inner corner: square from the wall's inner faces to the arc centre, minus the R_IN circle
        a0, a1 = sorted((cx + sx * R_OUT, cx))
        b0, b1 = sorted((cy + sy * R_OUT, cy))
        sq = box(a0 + (L.WALL if sx < 0 else 0), a1 - (L.WALL if sx > 0 else 0), b0 + (L.WALL if sy < 0 else 0), b1 - (L.WALL if sy > 0 else 0), L.Z_BOT, top_level(cx, cy) - 0.5)
        body = body.union(sq.cut(cyl(cx, cy, L.Z_BOT - 1, top_level(cx, cy) + 1, 2 * R_IN)))
    for w in chamfer_cutters(mod, CHAMFER_TOP, top_level):
        body = body.cut(w)
    for w in chamfer_cutters(mod, CHAMFER_BOT, lambda x, y: 0.0, flat=True):
        body = body.cut(w.mirror("XY").translate((0, 0, L.Z_BOT)))
    return body


def round_tray(b, mod):
    Lx, W, g = L.length(mod), L.CASE[1], 0.15
    rr = box(L.WALL + g, Lx - L.WALL - g, L.WALL + g, W - L.WALL - g, L.Z_BOT - 1, 40).edges("|Z").fillet(R_IN - g)
    return b.intersect(rr)


# ------------------------------------------------------------------ the lid
def lid(mod):
    body = round_and_chamfer_lid(F.lid(mod), mod)
    ceiling = L.CEILING
    # sockets in the left wall (closed holes; the board goes into the lid from below)
    body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(USB["y"], USB["z"]).rect(USB["w"], USB["h"])
                    .extrude(L.WALL + 3.5).edges("|X").fillet(min(USB["r"], USB["h"] / 2 - 0.01)))
    for yc in (L.OUT_Y, L.IN_Y):
        body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(yc, JACK_Z).circle(JACK_D / 2).extrude(L.WALL + 1.6))
    # knobs
    for x, y in L.KNOBS:
        body = body.cut(cyl(x, y, ceiling - 1, L.ROOF_TOP + 1, KNOB_HOLE))
    # screen: window and the ledge for the pane
    wx0, wy0, wx1, wy1 = C3.WINDOW
    body = body.cut(box(wx0, wx1, wy0, wy1, ceiling - 1, L.ROOF_TOP + 1))
    body = body.cut(box(wx0 - C3.WINDOW_LEDGE, wx1 + C3.WINDOW_LEDGE, wy0 - C3.WINDOW_LEDGE, wy1 + C3.WINDOW_LEDGE,
                        ceiling - 0.01, ceiling + C3.WINDOW_PANE_T))
    for (x, y) in oled_posts():
        body = body.union(cyl(x, y, C3.oled_levels()["pcb_top"], ceiling + 0.01, 3.2).cut(cyl(x, y, C3.oled_levels()["pcb_top"] - 1, ceiling - 0.8, 1.5)))
    # speaker slots and the two posts for the acoustic box
    g = G.GRILLE
    for i in range(g["n"]):
        y0 = g["y0"] + i * g["pitch"]
        body = body.cut(box(g["x0"], g["x1"], y0, y0 + g["slot"], ceiling - 1, L.ROOF_TOP + 1))
    ear_top = C3.box_levels()["ear_top"]
    for x, y in G.SPEAKER_SCREWS:
        body = body.union(cyl(x, y, ear_top, ceiling + 0.01, 5.0).cut(cyl(x, y, ear_top - 1, ceiling - 0.6, C3.POST_PILOT)))
    # the interface's four posts: on the board's mounting holes H1..H4 (stand on the board's top), pilot for the M2 insert
    for x, y in L.LID_POSTS:
        body = body.union(cyl(x, y, 0.0, ceiling + 0.01, POST_D).cut(cyl(x, y, -0.01, 6.0, T.SCREW_PILOT)))
    return body


def oled_posts():
    cx, cy = oled_centre()
    dx, dy = C3.OLED_PCB[0] / 2 - 2.0, C3.OLED_PCB[1] / 2 - 2.0
    return [(cx - dx, cy - dy), (cx + dx, cy - dy), (cx - dx, cy + dy), (cx + dx, cy + dy)]


def oled_centre():
    wx0, wy0, wx1, wy1 = C3.WINDOW
    return (wx0 + wx1) / 2, (wy0 + wy1) / 2 - 1.9       # SPEC y: the module is turned 180 deg, its board centre is 1.9 mm BEHIND the window centre


# ------------------------------------------------------------------ the tray
def tray(mod):
    Lx = L.length(mod)
    gap = 0.15
    b = box(L.WALL + gap, Lx - L.WALL - gap, L.WALL + gap, L.CASE[1] - L.WALL - gap, L.Z_BOT, L.Z_FLOOR)
    # rails under the rulers (two per row)
    for ru in L.rulers(mod):
        z1 = L.ZR[ru["row"] - 1] - L.RULER_T
        for sgn in (-1, 1):
            ya, yb = sorted((ru["y"] + sgn * L.RAIL_IN, ru["y"] + sgn * L.RAIL_OUT))
            b = b.union(box(ru["x0"] + 0.2, ru["x0"] + L.RULER_L - 0.2, ya, yb, L.Z_FLOOR, z1))
        # real bosses D6 under the M2 points (R3V4 had only the 2.8 mm rail): from the floor to the ruler's underside
        for mx, my in L.m2_points(ru):
            b = b.union(cyl(mx, my, L.Z_FLOOR, z1, L.M2_BOSS_D))
    # the interior posts come down through the tray: clear the rails round them, drill the screw holes
    for x, y in L.pick_posts(mod):
        b = b.cut(cyl(x, y, L.Z_FLOOR - 0.1, L.Z_FLOOR + 30, F.POST_D + 0.8)).cut(box(x - 1.1, x + 1.1, y - 1.66 - 0.3, y + 2.34 + 0.3, L.Z_FLOOR - 0.1, L.Z_FLOOR + 30))
    cut = None
    for x, y in L.pick_posts(mod) + L.wall_posts(mod):
        h = cyl(x, y, L.Z_BOT - 0.1, L.Z_FLOOR + 0.1, 2.4).union(cyl(x, y, L.Z_BOT - 0.1, L.Z_BOT + 1.0, 4.2))
        cut = h if cut is None else cut.union(h)
    b = b.cut(cut)
    # M2 pilots (insert) in the bosses
    for ru in L.rulers(mod):
        z1 = L.ZR[ru["row"] - 1] - L.RULER_T
        for mx, my in L.m2_points(ru):
            b = b.cut(cyl(mx, my, z1 - 6.0, z1 + 0.1, T.SCREW_PILOT))
    # connectors: the notches in the rails (the plug passes under the next, higher ruler)
    for nt in L.notches(mod):
        z1 = L.ZR[nt["row"] - 1] - L.RULER_T
        b = b.cut(box(nt["x0"], nt["x1"], nt["y0"], nt["y1"], L.Z_FLOOR, z1 + 0.1))
    # interface: bosses under H1..H4 up to the board's underside, with the screw's hole and head recess
    for x, y in L.LID_POSTS:
        b = b.union(cyl(x, y, L.Z_FLOOR - 0.01, -L.T_PCB, 6.0))
    for x, y in L.LID_POSTS:
        b = b.cut(cyl(x, y, L.Z_BOT - 1, 1.0, 2.4)).cut(cyl(x, y, L.Z_BOT - 0.01, L.Z_BOT + 2.2, 4.4))
    # battery cradle: low ribs behind and at the two ends (the front is open for the cell and its wires)
    bx0, by0 = L.BATTERY_XY
    bx1, by1 = bx0 + L.BATTERY_CELL[0], by0 + L.BATTERY_CELL[1]
    rib, h, m = 1.2, 2.0, 0.5
    for r in ((bx0 - m - rib, by1 + m, bx1 + m + rib, by1 + m + rib),            # the end opposite to the wires
              (bx1 + m, by0 + 6.0, bx1 + m + rib, by1 + m),                      # right side
              (bx0 - m - rib, 66.0, bx0 - m, by1 + m)):                          # left side, only beyond the jack IN (J302, y 54.8..65.2)
        b = b.union(box(r[0], r[2], r[1], r[3], L.Z_FLOOR - 0.01, L.Z_FLOOR + h))
    # the module's screw: a recess under H101; the PROG button's hole
    b = b.cut(cyl(L.H101[0], L.H101[1], L.Z_FLOOR - 1.0, L.Z_FLOOR + 1, 8.0))
    b = b.cut(cyl(L.PROG[0], L.PROG[1], L.Z_BOT - 1, L.Z_FLOOR + 1, 3.0))
    return round_tray(b, mod)


# ------------------------------------------------------------------ the keyboard's thin parts (M2 per row)
def rulers_solid(mod):
    res = None
    posts = L.pick_posts(mod)
    for ru in L.rulers(mod):
        x0, y, z1 = ru["x0"], ru["y"], L.ZR[ru["row"] - 1]
        w = box(x0 + 0.2, x0 + L.RULER_L - 0.2, y - L.RULER_W / 2, y + L.RULER_W / 2, z1 - L.RULER_T, z1)
        for mx, my in L.m2_points(ru):
            w = w.cut(cyl(mx, my, z1 - 2, z1 + 1, T.SCREW_D))
        for px, py in posts:
            if abs(py - (y - L.ROWP / 3.0)) < 0.05 and x0 - 3 < px < x0 + L.RULER_L + 3:
                w = w.cut(box(px - 1.0, px + 1.0, y - 7.1, y - 2.7, z1 - 2, z1 + 1))
        res = w if res is None else res.union(w)
    return res


def grades(mod):
    res = None
    posts = L.pick_posts(mod)
    for ru in L.rulers(mod):
        x0, y, z1 = ru["x0"], ru["y"], L.ZR[ru["row"] - 1] + 5.0
        g = box(x0 + 0.2, x0 + L.RULER_L - 0.2, y - GRADE_W / 2, y + GRADE_W / 2, z1 - T.GRADE_T, z1)
        for i in range(4):
            xc = x0 + L.PITCH / 2 + i * L.PITCH
            g = g.cut(box(xc - T.GRADE_OPEN / 2, xc + T.GRADE_OPEN / 2, y - T.GRADE_OPEN / 2, y + T.GRADE_OPEN / 2, z1 - 2, z1 + 1))
        for px, py in posts:
            if abs(py - (y - L.ROWP / 3.0)) < 0.05 and x0 - 3 < px < x0 + L.RULER_L + 3:
                g = g.cut(box(px - 1.0, px + 1.0, y - GRADE_W / 2 - 0.1, y - 2.7, z1 - 2, z1 + 1))
        res = g if res is None else res.union(g)
    return res


def screws(mod):
    res = None
    for ru in L.rulers(mod):
        z0 = L.ZR[ru["row"] - 1]
        for mx, my in L.m2_points(ru):
            s = cyl(mx, my, z0 - L.RULER_T - 4, z0 + 1.6, 2.0).union(cyl(mx, my, z0, z0 + 1.6, T.SCREW_HEAD))
            res = s if res is None else res.union(s)
    return res


def connectors(mod):
    """Headers and plugs of every ruler (envelopes, absolute z) plus the pegs and the sensors' pockets for the clearance check."""
    parts = {"cabecalhos": None, "plugues": None, "pinos": None, "sensores": None, "elos": None}
    if L.LINK == "D":
        for r, xj, y in L.solder_links(mod):
            a, b, ya, yb, za, zb = L.link_box(xj, y, L.ZR[r - 1])
            s = box(a, b, ya, yb, za, zb)
            parts["elos"] = s if parts["elos"] is None else parts["elos"].union(s)
    for ru in L.rulers(mod):
        z0 = L.ZR[ru["row"] - 1]
        for name, xa, xb, ya, yb, za, zb in L.conn_boxes(ru):
            s = box(xa, xb, ya, yb, z0 + za, z0 + zb)
            k = "cabecalhos" if name.endswith("header") else "plugues"
            parts[k] = s if parts[k] is None else parts[k].union(s)
        for i in range(4):
            xc = ru["x0"] + L.PITCH / 2 + i * L.PITCH
            for dx in (-L.PEG_DX, L.PEG_DX):
                p = cyl(xc + dx, ru["y"], z0 - L.RULER_T - L.PEG_BELOW, z0 - L.RULER_T, L.PEG_D)
                parts["pinos"] = p if parts["pinos"] is None else parts["pinos"].union(p)
            sn = box(xc - 0.9, xc + 0.9, ru["y"] - 1.1, ru["y"] + 1.1, z0 - L.RULER_T - 0.8, z0 - L.RULER_T)
            parts["sensores"] = sn if parts["sensores"] is None else parts["sensores"].union(sn)
    return parts


# ------------------------------------------------------------------ the interface's parts
def board():
    x0, y0, x1, y1 = L.BOARD_OUT
    w = box(x0, x1, y0, y1, -L.T_PCB, 0.0).edges("|Z").fillet(L.BOARD_R)
    for x, y in list(L.HOLES.values()):
        w = w.cut(cyl(x, y, -2, 1, 2.4 if (x, y) != L.H101 else 2.7))
    sx0, sy0, sx1, sy1 = L.SLIT
    return w.cut(box(sx0, sx1, sy0, sy1, -2, 1))


def module():
    x0, y0, x1, y1 = L.CARD
    return box(x0, x1, y0, y1, -L.T_PCB - L.CARD_BELOW, -L.T_PCB - L.CARD_BELOW + 1.0).union(
        box(x0 + 4, x1 - 2, y0 + 3, y1 - 3, -L.T_PCB - L.CARD_BELOW + 1.0, -L.T_PCB - L.CARD_BELOW + 2.6))


def battery():
    bx0, by0 = L.BATTERY_XY
    return box(bx0, bx0 + L.BATTERY_CELL[0], by0, by0 + L.BATTERY_CELL[1], L.Z_FLOOR, L.Z_FLOOR + L.BATTERY_CELL[2])


def speaker():
    lv = C3.box_levels()
    x, y = L.SPEAKER
    return cyl(x, y, lv["back"], lv["front"], L.SPK_D)


def acoustic_box():
    c, info = C3.caixa_acustica()
    return mirror(c), info


def oled():
    cx, cy = oled_centre()
    lv = C3.oled_levels()
    pcb = box(cx - C3.OLED_PCB[0] / 2, cx + C3.OLED_PCB[0] / 2, cy - C3.OLED_PCB[1] / 2, cy + C3.OLED_PCB[1] / 2, lv["pcb_bottom"], lv["pcb_top"])
    glass = box(cx - 13.0, cx + 13.0, cy - 8.0, cy + 8.0, lv["pcb_top"], lv["glass_top"])
    return pcb.union(glass)


def encoder(x, y):
    body = box(x - 6.0, x + 6.0, y - 6.7, y + 6.7, 0.0, 4.5)
    shaft = cyl(x, y, 11.5, 24.5, 6.0).cut(box(x + 1.5, x + 4.0, y - 4.0, y + 4.0, 11.0, 25.0))      # the D flat: 4.5 across flats
    return body.union(cyl(x, y, 4.5, 11.5, 7.0)).union(shaft)


def knob(x, y):
    k, _info = C3.knob()
    return mirror(k).translate((x, y, 0))


# bottom-side parts: (height, ref prefix) for the tall ones; everything else is taken as 1.0 mm
TALL = {"J201": 3.3, "J301": 5.2, "J302": 5.2, "J202": 6.0, "J101": 4.2, "J401": 4.25, "J601": 4.25, "J602": 4.25, "J603": 4.25, "J604": 4.25,
        "SW403": 3.5, "U501": 0.9}


def bottom_parts():
    out = {}
    for ref, p in L.P.items():
        if p["lado"] != "B" or ref in ("J101",):
            continue
        x0, y0, x1, y1 = (v + d for v, d in zip(p["patio"], (0.25, 0.25, -0.25, -0.25)))     # the courtyard shrunk to about the body
        h = TALL.get(ref, 1.0)
        out[ref] = box(x0, x1, y0, y1, -L.T_PCB - h, -L.T_PCB)
    return out


def top_parts():
    """Parts on the board's top besides the encoders: the speaker's wire pads (a 6 mm box 2 mm high)."""
    x0, y0, x1, y1 = L.P["J501"]["patio"]
    return {"J501_pads": box(x0, x1, y0, y1, 0.0, 2.0)}


def build(mod):
    t0 = time.time()
    n = 32 + 16 * mod
    Lx = L.length(mod)
    lid_, tray_, ru, gr, sc = lid(mod), tray(mod), rulers_solid(mod), grades(mod), screws(mod)
    keys0 = T.key_bodies(mod, 0.0)
    keys5 = T.key_bodies(mod, 0.5, False)
    keys8 = T.key_bodies(mod, 0.8, False)
    cn = connectors(mod)
    brd, mdl, bat, spk, (bx, bxinfo), ole = board(), module(), battery(), speaker(), acoustic_box(), oled()
    encs = [encoder(x, y) for x, y in L.KNOBS]
    knobs = [knob(x, y) for x, y in L.KNOBS]
    bots, tops = bottom_parts(), top_parts()
    info = {"teclas": n, "modulos": mod, "comprimento_mm": Lx, "largura_mm": L.CASE[1], "grade_mm": T.GRADE_T, "folga_deck_mm": T.GAP, "deck_mm": F.DECK_T,
            "haste_cabeca_topo": T.CAP_TOP, "teto_interface_z": L.CEILING, "topo_interface_z": L.ROOF_TOP,
            "z_topo_tampa": F.ZR[3] + F.DECK_TOP, "altura_atras_mm": round(F.ZR[3] + F.DECK_TOP - F.Z_BOT, 2),
            "altura_frente_mm": round(F.ZR[0] + F.DECK_TOP - F.Z_BOT, 2), "reguas": len(L.rulers(mod)),
            "postes_internos": len(L.pick_posts(mod)), "postes": L.pick_posts(mod), "bossas_de_parede": len(L.wall_posts(mod)),
            "parafusos_M2": 2 * len(L.rulers(mod)), "m2_por_fileira": {str(k): v for k, v in L.M2_BY_ROW.items()},
            "volume_cm3": {"tampa": round(vol(lid_) / 1000, 1), "base": round(vol(tray_) / 1000, 1)},
            "caixa_acustica": bxinfo}
    I = {}
    # ---- keyboard (as the R3V4 table)
    I["teclado"] = {
        "tampa x teclas (nominal)": round(inter(lid_, keys0), 2),
        "tampa x carcacas (+0,5 mm, sem botao)": round(inter(lid_, keys5), 2),
        "tampa x carcacas (+0,8 mm, sem botao)": round(inter(lid_, keys8), 2),
        "tampa x grades": round(inter(lid_, gr), 2), "tampa x reguas": round(inter(lid_, ru), 2), "tampa x parafusos": round(inter(lid_, sc), 2),
        "base x teclas": round(inter(tray_, keys0), 2), "base x reguas": round(inter(tray_, ru), 2), "base x grades": round(inter(tray_, gr), 2),
        "base x parafusos (cabeca)": round(inter(tray_, sc), 2), "grades x teclas": round(inter(gr, keys0), 2),
        "grades x reguas": round(inter(gr, ru), 2), "grades x parafusos": round(inter(gr, sc), 2), "teclas x parafusos": round(inter(keys0, sc), 2)}
    # ---- connectors, pegs and sensors
    I["conectores"] = {
        "cabecalhos x base": round(inter(cn["cabecalhos"], tray_), 2), "plugues x base": round(inter(cn["plugues"], tray_), 2),
        "cabecalhos x pinos das teclas": round(inter(cn["cabecalhos"], cn["pinos"]), 2), "plugues x pinos": round(inter(cn["plugues"], cn["pinos"]), 2),
        "cabecalhos x sensores": round(inter(cn["cabecalhos"], cn["sensores"]), 2), "plugues x sensores": round(inter(cn["plugues"], cn["sensores"]), 2),
        "cabecalhos x reguas (so o topo toca: 0)": round(inter(cn["cabecalhos"], ru), 2), "plugues x reguas": round(inter(cn["plugues"], ru), 2),
        "plugues x cabecalhos": round(inter(cn["plugues"], cn["cabecalhos"]), 2), "plugues x parafusos": round(inter(cn["plugues"], sc), 2)}
    if cn["elos"] is not None:
        I["conectores"].update({"elos x base": round(inter(cn["elos"], tray_), 2), "elos x pinos": round(inter(cn["elos"], cn["pinos"]), 2),
                                "elos x sensores": round(inter(cn["elos"], cn["sensores"]), 2), "elos x parafusos": round(inter(cn["elos"], sc), 2),
                                "elos x cabecalhos": round(inter(cn["elos"], cn["cabecalhos"]), 2), "elos x reguas": round(inter(cn["elos"], ru), 2)})
    # ---- interface
    comp = {"placa": brd, "modulo": mdl, "bateria": bat, "alto-falante": spk, "caixa acustica": bx, "OLED": ole,
            "encoder 1": encs[0], "encoder 2": encs[1], "knob 1": knobs[0], "knob 2": knobs[1]}
    names = list(comp)
    ifc = {}
    for nm in names:
        ifc["tampa x " + nm] = round(inter(lid_, comp[nm]), 2)
        ifc["base x " + nm] = round(inter(tray_, comp[nm]), 2)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = round(inter(comp[a], comp[b]), 2)
            if v:
                ifc[a + " x " + b] = v
    for ref, s in list(bots.items()) + list(tops.items()):
        for nm in ("bateria", "modulo", "caixa acustica", "OLED", "alto-falante"):
            v = round(inter(s, comp[nm]), 2)
            if v:
                ifc[ref + " x " + nm] = v
        for part, nm in ((lid_, "tampa"), (tray_, "base")):
            v = round(inter(s, part), 2)
            if v:
                ifc[ref + " x " + nm] = v
    I["interface"] = ifc
    info["interferencias_mm3"] = I
    info["lugar"] = {"bateria": [L.BATTERY_XY[0], L.BATTERY_XY[1], L.BATTERY_XY[0] + L.BATTERY_CELL[0], L.BATTERY_XY[1] + L.BATTERY_CELL[1]],
                     "bateria_z": [L.Z_FLOOR, L.Z_FLOOR + L.BATTERY_CELL[2]], "falante_z": [C3.box_levels()["back"], C3.box_levels()["front"]],
                     "oled_z": [C3.oled_levels()["pcb_bottom"], C3.oled_levels()["glass_top"]], "oled_centro": list(oled_centre()),
                     "modulo_z": [-L.T_PCB - L.CARD_BELOW, -L.T_PCB], "encoder_topo_do_eixo": 24.5, "knob_topo": C3.KNOB["top"]}
    for name, w in (("tampa", lid_), ("base", tray_), ("reguas", ru), ("grades", gr), ("teclas", keys0), ("parafusos", sc)) + tuple(
            (k, w_) for k, w_ in comp.items()):
        fn = name.replace(" ", "_")
        cq.exporters.export(mirror(w), os.path.join(OUT, "r4_%d_%s.stl" % (n, fn)), tolerance=0.05, angularTolerance=0.2)
        if name in ("tampa", "base") and mod == 0:
            cq.exporters.export(mirror(w), os.path.join(OUT, "r4_%d_%s.step" % (n, name)))
    info["segundos"] = round(time.time() - t0, 1)
    json.dump(info, open(os.path.join(OUT, "r4_%d.json" % n), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(info, indent=1, ensure_ascii=False), flush=True)
    return info


if __name__ == "__main__":
    for m in [int(a) for a in sys.argv[1:]] or [0]:
        build(m)
