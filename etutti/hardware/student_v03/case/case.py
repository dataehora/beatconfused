"""eTutti Student V3: the case in separate, printable pieces (SPEC v4, finish Retro).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/case.py

Frame of the model: x right, y = -y of the SPEC (the SPEC's y runs towards the player), z up,
z = 0 at the board's top. Every function below takes the SPEC's x, y.

  base       grey TRAY, z -10.1 to -8.1 (SPEC v4): a flat 2 mm plate that goes into the lid with 0.15 mm
             clearance a side, its underside flush with the lid's rim; a 1.2 mm rim along the lid's inner wall
             (top at z -6.6, lowered to -7.6 where the three sockets are), a boss under each of the 6 lid
             screws, a cup under each of the 10 grid screws (the screw ends in a nut under the board, so the
             tray comes off with 6 screws), 4 locating pins (into the board's holes H5-H8, between the keys), the
             support pillars under the keyboard, the battery's cradle, a recess for the module's nut (H101).
  tampa      cream lid, z -10.1 to 14.5 (SPEC v4): vertical walls all the way down (no seam), a 1.5 mm
             chamfer on the lower outer edge, 30 deg chamfer 6 x 3.5 with R 1.5 on both upper edges, three
             grooves, the keyboard's well (a 1.4 mm lid over the grid's edge, top edge R 1.2), window of the
             screen, holes of the two knobs, the speaker's slots, 6 posts for the screws, 2 bosses for the
             acoustic box, 4 posts of the screen; closed holes for USB-C, OUT and IN in the left wall (the
             sockets end 0.3 mm behind the wall, so the board goes into the lid from below); 0.4 mm recesses to
             be filled with paint: the logo, the line under the screen, "OUT" and "IN".
  grade      keyboard grid, a flat 1.6 mm plate, z 11.35 to 12.95, one 6.2 mm hole per button,
             held by 10 flat-head M2 screws (SPEC v4: countersunk holes, heads flush) on its edge, under the lid. Made of FR-4 with the board
             (pcb/grade_fab.py writes its Gerbers); the STEP/STL here is the same shape.
  espacador  tube between board and grid (print 10).
  botao_<tipo>_f<fileira>   12 buttons: branco, preto, pontos x rows 1-4 (stem length).
  knob       hat knob for the EC11E with 20 mm shaft, straight on the shaft, no sleeve (print 2).
  caixa_acustica   the speaker's ring and closed back box (L-shaped: low under the speaker, tall
             beside it), one piece.
  janela     the screen's window pane (cut from 1 mm smoked acrylic, or printed clear).

Writes out/*.step, out/*.stl and out/case.json (the numbers the fit check and the renders read).
"""
import json
import math
import os
import sys

import cadquery as cq

T0 = __import__("time").time()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

OUT = os.path.join(HERE, "out")
BOARD_JSON = os.path.join(HERE, "..", "pcb", "furos.json")
SUPPORTS_JSON = os.path.join(HERE, "..", "estudos", "apoios.json")

# ---- levels (z = 0 at the board's top)
Z0, ZT = G.Z_BASE, G.Z_TOP          # -10.1, 14.5
ZS = Z0                              # (no split any more: kept so the older helpers read)
WALL, FLOOR, LID_T = 2.0, 2.0, 2.0
T_PCB = G.T_PCB
HOUSING_TOP = 11.2            # top of a switch's housing
STEM_TOP = 14.8               # top of a switch's cross, key up
TRAVEL = 4.1
GRID_Z0, GRID_T = 11.35, 1.6  # the grid: 0.15 above the housings (SPEC v2)
GRID_Z1 = GRID_Z0 + GRID_T    # 12.95 = the well's floor
FLANGE_GAP = 0.15                # the lid over the grid's edge stops 0.15 above the grid (SPEC v3, v4)
GRID_ROOF = GRID_Z1 + FLANGE_GAP    # 13.1: under the 1.4 mm lid over the grid (SPEC v4 item 12)
CHAMFER = (6.0, 3.5)          # horizontal, vertical
EDGE_R = 1.5
GROOVES = (4.3, 6.5, 8.7)     # centres (SPEC v4: they came down 3.7 mm with the top)
GROOVE_W, GROOVE_D = 0.8, 0.6
BASE_CHAMFER = 1.5
TRAY_GAP, RIM_T = 0.15, 1.2           # the tray goes into the lid with 0.15 mm a side; its rim is 1.2 thick
RIM_TOP, RIM_LOW = -6.6, -7.6          # the rim's top; lowered at the three sockets (>= 1.3 under the jacks)
RIM_ZONES = ((9.0, 23.0), (30.0, 42.0), (54.0, 66.0))   # y of USB-C, OUT, IN
H101 = (47.5, 14.0)                    # the module's screw: a recess in the tray's floor under it
H101_RECESS = (8.0, 1.0)               # diameter, depth
CSK_D, CSK_ANGLE = 3.8, 90.0           # ISO 7046 M2 head

# ---- keyboard
BUTTON_D, DOME_H, SKIRT_H, STEM_D = 15.0, 2.3, 1.2, 5.6
ROW_TOP = {1: 21.9, 2: 23.9, 3: 25.9, 4: 28.9}
GRID_HOLE, GRID_HOLE_CHAMFER = 6.2, 0.0      # FR-4: a drilled hole has no chamfer
CROSS = (4.15, 1.30, 3.8)     # MX cross socket: arm length, arm width, depth
DIMPLE_D, DIMPLE_PITCH, DIMPLE_DEPTH = 0.66, 1.4, 0.22
WELL_R_TOP, WELL_R_BOTTOM = 1.2, 0.0
SPACER_D, SCREW_CLEAR, PILOT = 5.0, 2.3, 1.7
NOTES = {1: ["A3", "C4", "D#4", "F#4", "A4", "C5", "D#5"], 2: ["G3", "A#3", "C#4", "E4", "G4", "A#4", "C#5", "E5"],
         3: ["G#3", "B3", "D4", "F4", "G#4", "B4", "D5"], 4: ["A3", "C4", "D#4", "F#4", "A4", "C5"]}

# ---- interface
WINDOW = G.OLED_WINDOW
WINDOW_PANE_T, WINDOW_LEDGE = 1.0, 1.0
OLED_PCB = (27.3, 27.8, 1.6)      # the common 0.96 in module: board x, y, thickness
OLED_GLASS_T = 1.5
KNOB_HOLE = 9.2
KNOB = {"skirt_d": 12.0, "body_d": 9.0, "gap": 0.8, "top": ZT + 7.0, "sleeve_d": 0.0, "sleeve_z0": ZT + 0.8,
        "shaft_d": 6.0, "shaft_flat": 4.5, "shaft_top": 20.0, "bore_clear": 0.1}
SPK = G.SPEAKER
SPK_D, SPK_H = G.SPEAKER_D, 5.0
MESH_T, FOAM_T = 0.3, 1.0
BOX_WALL, BOX_FLOOR, BOX_ROOF, BOX_RIB = 1.5, 1.0, 1.2, 0.8
BOX_Z0 = 0.3                   # outside bottom of the acoustic box (SPEC v4: 0.3 above the board's top, was 0.8)
WIRE_X = 49.5
BOX_LEG2_X1 = 19.5            # the second tall block, left of the speaker's ring (its outer edge is x = 21.3)
BOX_RIBS_X = (28.0, 37.0, 46.0)   # ribs under the roof: it prints as bridges under 9 mm, and does not drum
BOX_LEDGE = 1.2                # the speaker's rim sits on it
EAR_T, EAR_D = 2.0, 6.0
POST_D, POST_PILOT = 4.6, 1.6
BOSS_D, BOSS_HOLE, HEAD_D, HEAD_DEPTH = 6.0, 2.4, 4.4, 2.2
PILLAR_D, PIN_D, PIN_TIP_D, PIN_TIP_H = 4.0, 5.0, 2.0, 1.2 + 0.8
NUT_BOSS_D, NUT_POCKET_D, NUT_POCKET_H = 7.4, 5.2, 3.2      # M2 nut (4.6 across corners, 1.6 thick) and the screw's end
USB = {"y": G.USB_Y, "z": G.USB_Z, "w": G.USB_OPENING[0], "h": G.USB_OPENING[1], "r": G.USB_OPENING[2]}
JACK_D = G.JACK_OPENING_D
ENGRAVE = 0.4                   # recesses for paint
STROKE_GROW = 0.1               # SPEC v3: "eTUTTI" outlines grown by 0.1 mm on each side
SMALL_GROW = 0.025              # SPEC v4 item 11: "STUDENT . V2" strokes from ~0.15 to 0.20 mm (0.025 a side)
PAINT_T = 0.05                  # the pad-printed "STUDENT · V2": a skin of paint, no recess
LINE_UNDER_WINDOW = (1.5, 0.5)  # gap below the window, width
LOGO = {"x0": 8.6, "box": 5.0, "y0": 8.0, "y1": 92.0, "gap": 1.4,
        "big": ("eTUTTI", 4.4, 0.5), "small": ("STUDENT · V2", 1.7, 0.6)}      # text, em size, letter spacing
LABEL_H, LABEL_GAP, LABEL_Z = 2.0, 1.8, -5.0    # "OUT" / "IN": cap height, distance from the hole, baseline (centred on the jacks' axis, z -5 to -3)
FONT_DIR = os.path.join(HERE, "fontes")
LOGO_FONTS = [os.path.join(FONT_DIR, "Michroma-Regular.ttf"), "C:/Windows/Fonts/Michroma-Regular.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]     # not Bahnschrift: its overlapping outlines do not cut cleanly
LABEL_FONTS = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
BATTERY = (19.5, 56.0, 69.5, 90.0, 5.2)       # x0, y0, x1, y1, thickness (503450 with margin); 6.5 mm to the right of the V2's: the jack IN is in the way
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
# stiffening ribs of the tray under the keyboard: a grid along x and y (SPEC v4 item 6; tops <= z -4.0, 2.8 mm under the board's bottom)
RIB_GRID = {"x0": 72.0, "y0": 6.0, "x1": 240.0, "y1": 94.0, "pitch": 12.0, "t": 1.2, "top": -4.0}


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


# ------------------------------------------------------------------ recessed lettering
def font(paths):
    return next(p for p in paths if os.path.exists(p))


def polygonised(shape, depth=1.0, step=0.06, grow=0.0):
    """A text solid made again from straight-sided outlines (points every `step` mm on the curves):
    OpenCascade does not finish cutting some glyphs' own spline edges out of the lid."""
    out = None
    for f in shape.faces("<Z").vals():
        def poly(wire):
            segs = []
            for e in wire.Edges():
                n = 1 if e.geomType() == "LINE" else max(2, int(e.Length() / step))
                segs.append([e.positionAt(i / n) for i in range(n + 1)])
            chain = segs.pop(0)
            while segs:          # the edges of a wire, each possibly running either way: chain by nearest end
                k, rev = min(((i, r) for i in range(len(segs)) for r in (False, True)),
                             key=lambda kr: (segs[kr[0]][-1 if kr[1] else 0] - chain[-1]).Length)
                nxt = segs.pop(k)
                chain += (list(reversed(nxt)) if rev else nxt)[1:]
            clean = [cq.Vector(chain[0].x, chain[0].y, 0)]
            for q in chain[1:]:
                q = cq.Vector(q.x, q.y, 0)
                if (q - clean[-1]).Length > 1e-4:
                    clean.append(q)
            if (clean[0] - clean[-1]).Length < 1e-4:
                clean.pop()
            return cq.Wire.makePolygon(clean + [clean[0]])
        if grow:
            def grown(w, d):        # offset a polygon outwards (d > 0) or inwards, whichever way it winds
                area = cq.Face.makeFromWires(w).Area()
                for sign in (1, -1):
                    r = w.offset2D(sign * d, "arc")[0]
                    if (cq.Face.makeFromWires(r).Area() > area) == (d > 0):
                        return r
                raise ValueError("offset did not change the outline")
            outer = grown(poly(f.outerWire()), grow)
            holes = [grown(poly(w), -grow) for w in f.innerWires()]
        else:
            outer, holes = poly(f.outerWire()), [poly(w) for w in f.innerWires()]
        face = cq.Face.makeFromWires(outer, holes)
        sol = cq.Workplane("XY").add(cq.Solid.extrudeLinear(face, cq.Vector(0, 0, depth)))
        out = sol if out is None else out.union(sol)
    return out


def letters(txt, size, spacing, path, depth=1.0, grow=0.0):
    """txt as solids on the XY plane: advance +x from x = 0, baseline y = 0, z 0 to 1.
    Letter by letter, so the letter spacing of the canvas can be given. Returns (shapes, length, height)."""
    out, x, top = [], 0.0, 0.0
    for ch in txt:
        if ch == " ":
            x += 0.35 * size + spacing
            continue
        if ch == "·":
            d = 0.16 * size
            g = cq.Workplane("XY").center(x + d / 2, 0.36 * size).rect(d, d).extrude(1.0)
            w = d
        else:
            g = cq.Workplane("XY").text(ch, size, 1.0, fontPath=path, halign="left", valign="bottom")
            bb = g.val().BoundingBox()
            g = polygonised(g, depth=depth, grow=grow).translate((x - bb.xmin, -bb.ymin, 0))
            w = bb.xlen
            top = max(top, bb.ylen)
        out.append(g)
        x += w + spacing + 0.08 * size
    return out, x - spacing - 0.08 * size, top


def logo_layout():
    """Both lines of the logo: "eTUTTI" (cutters for the recess, outlines grown by STROKE_GROW) and
    "STUDENT . V2" (a thin skin of paint, no recess), standing along the left edge, read from the front
    towards the back, centred between y 8 and 92, with LOGO["gap"] mm clear between the two lines."""
    path = font(LOGO_FONTS)
    big, lb, hb = letters(LOGO["big"][0], LOGO["big"][1], LOGO["big"][2], path, grow=STROKE_GROW)
    small, ls, hs = letters(LOGO["small"][0], LOGO["small"][1], LOGO["small"][2], path, depth=PAINT_T, grow=SMALL_GROW)
    g2 = STROKE_GROW
    lb_full = lb + 2 * g2                          # the grown "eTUTTI"
    s_small = lb_full + LOGO["gap"]                # where "STUDENT" starts, along the logo
    total = s_small + ls
    ymid = (LOGO["y0"] + LOGO["y1"]) / 2
    xc = LOGO["x0"] + LOGO["box"] / 2
    start = ymid + total / 2                       # SPEC y of the first letter's foot
    cut, paint = [], []
    for g in big:
        g = g.rotate((0, 0, 0), (0, 0, 1), 90)     # advance +y (model), tops towards -x
        cut.append(g.translate((xc + hb / 2, -(start - g2), ZT - ENGRAVE)))
    for g in small:
        g = g.rotate((0, 0, 0), (0, 0, 1), 90)
        paint.append(g.translate((xc + hs / 2, -(start - s_small), ZT)))
    y_of = lambda ws: (min(w.val().BoundingBox().ymin for w in ws), max(w.val().BoundingBox().ymax for w in ws))
    (b0, b1), (s0, s1) = y_of(cut), y_of(paint)
    gap = min(abs(s0 - b1), abs(b0 - s1))
    info = {"fonte_do_logo": os.path.basename(path), "fonte_e_a_da_SPEC": "Michroma" in os.path.basename(path),
            "logo_y": [round(start - total, 2), round(start, 2)], "altura_do_logo_mm": round(total, 2),
            "folga_entre_as_linhas_mm": round(gap, 2), "traco_engrossado_mm": STROKE_GROW,
            "altura_das_letras_mm": [round(hb + 2 * g2, 2), round(hs, 2)],
            "eTUTTI_x": [round(xc - hb / 2 - g2, 2), round(xc + hb / 2 + g2, 2)], "STUDENT_V2_so_tinta": True}
    return cut, paint, info


def logo_cutter():
    cut, _paint, info = logo_layout()
    return cut, info


def label_cutter(txt, y_start):
    """A label in the left wall's outside, read from outside: it starts at SPEC y = y_start and runs to the front."""
    path = font(LABEL_FONTS)
    probe = cq.Workplane("XY").text("O", 10.0, 1.0, fontPath=path, halign="left", valign="bottom").val().BoundingBox()
    size = 10.0 * LABEL_H / probe.ylen
    plane = cq.Plane(origin=(ENGRAVE, -y_start, LABEL_Z), xDir=(0, -1, 0), normal=(-1, 0, 0))
    flat, _len, _h = letters(txt, size, 0.3 - 0.08 * size, path)
    out = []
    for g in flat:           # local (advance, up, depth) -> world (-y, +z, -x), from x = ENGRAVE outwards
        sol = g.val().scale(1.0)
        m = cq.Matrix([[0, 0, -(ENGRAVE + 0.2), ENGRAVE], [-1, 0, 0, -y_start], [0, 1, 0, LABEL_Z], [0, 0, 0, 1]])
        out.append(cq.Workplane("XY").add(sol.transformGeometry(m)))
    return out


# ------------------------------------------------------------------ lid
def step(what):
    if os.environ.get("CASE_STEPS"):
        import time
        print("   %6.1f s  %s" % (time.time() - T0, what), flush=True)


def chamfer_inner():
    """The lid's inside under the chamfer: the outside plane moved 2 mm inwards."""
    ang = math.atan2(CHAMFER[1], CHAMFER[0])
    drop = LID_T / math.cos(ang)
    slope = CHAMFER[1] / CHAMFER[0]
    z_at_wall = ZT - CHAMFER[1] + WALL * slope - drop          # where the inner plane meets the inner wall
    ceiling = ZT - LID_T
    return (ceiling - z_at_wall) / slope, ceiling - z_at_wall     # horizontal, vertical


def tampa():
    body = outer(Z0, ZT)
    body = body.faces("<Z").edges().chamfer(BASE_CHAMFER)           # SPEC v4: the lower outer edge is the lid's
    body = body.faces(">Z").edges().chamfer(CHAMFER[1], CHAMFER[0])
    step("R 1.5 on the chamfer's two edges")
    # R 1.5 on the chamfer's two edges
    body = body.edges(cq.selectors.BoxSelector((-1, -G.CASE[1] - 1, ZT - CHAMFER[1] - 0.2),
                                               (G.CASE[0] + 1, 1, ZT + 0.1))).fillet(EDGE_R)
    # the recesses for paint go in now, while the lid is still a plain block (cut later, one glyph
    # did not end in OpenCascade)
    tampa.info = {}
    if not os.environ.get("CASE_NO_PAINT"):
        body = paint_recesses(body)
    ch, cv = chamfer_inner()
    cav = outer(Z0 - 1, ZT - LID_T, WALL).faces(">Z").edges().chamfer(cv, ch)
    body = body.cut(cav)
    step('grooves all round')
    # grooves all round
    for zc in GROOVES:
        ring = outer(zc - GROOVE_W / 2, zc + GROOVE_W / 2).cut(outer(zc - 1, zc + 1, GROOVE_D))
        body = body.cut(ring)
    ceiling = ZT - LID_T
    step('the lid over the keyboard grid: 1.4 mm, 0.15 above the grid')
    # over the grid's footprint the ceiling rises from 12.5 to 13.1 (the grid's top is 12.95): the lid is 1.4 mm there.
    # Cut from the grid's own level up: at the front and the back the grid (21.5 mm round the keys) reaches 4.5 mm from the
    # outer wall, where the 30 deg chamfer's inner plane is lower than the grid's top (report: the lid is only ~0.5 mm there)
    body = body.cut(hull_prism(G.GRID_EDGE + 0.1, GRID_Z0 - 0.3, GRID_ROOF))
    # the opening of the well: through the 1.4 mm lid, edge R 1.2
    body = body.cut(hull_prism(G.WELL_WALL, GRID_ROOF - 1, ZT + 1))
    sel_top = cq.selectors.BoxSelector((60, -100, ZT - 0.05), (245, 0, ZT + 0.05))
    body = body.edges(sel_top).fillet(WELL_R_TOP)
    bottom_r = 0.0
    step('posts for the lid screws')
    # posts for the lid screws
    for x, y in LID_HOLES:
        body = body.union(cyl(x, y, 0.0, ceiling + 0.01, POST_D).intersect(outer(Z0, ZT)))
    step('speaker: slots, and two bosses for the')
    # speaker: slots, and two bosses for the acoustic box
    g = G.GRILLE
    for i in range(g["n"]):
        y0 = g["y0"] + i * g["pitch"]
        body = body.cut(box(g["x0"], y0, g["x1"], y0 + g["slot"], ceiling - 1, ZT + 1, g["slot"] / 2 - 0.01))
    ear_top = box_levels()["ear_top"]
    for x, y in G.SPEAKER_SCREWS:
        body = body.union(cyl(x, y, ear_top, ceiling + 0.01, 5.0).cut(cyl(x, y, ear_top - 1, ceiling - 0.6, POST_PILOT)))
    step('screen: window with a ledge for the pa')
    # screen: window with a ledge for the pane, four posts with a step that hold the module's board
    wx0, wy0, wx1, wy1 = WINDOW
    body = body.cut(box(wx0, wy0, wx1, wy1, ceiling - 1, ZT + 1, 0.8))
    body = body.cut(box(wx0 - WINDOW_LEDGE, wy0 - WINDOW_LEDGE, wx1 + WINDOW_LEDGE, wy1 + WINDOW_LEDGE,
                        ceiling - 0.01, ceiling + WINDOW_PANE_T, 1.2))
    for (x, y) in oled_posts():
        body = body.union(cyl(x, y, oled_levels()["pcb_top"], ceiling + 0.01, 3.2)
                          .cut(cyl(x, y, oled_levels()["pcb_top"] - 1, ceiling - 0.8, 1.5)))
    step('knobs')
    # knobs
    for x, y in G.KNOBS:
        body = body.cut(cyl(x, y, ceiling - 1, ZT + 1, KNOB_HOLE))
    step('screw pilots')
    # screw pilots
    for x, y in LID_HOLES:
        body = body.cut(cyl(x, y, -0.01, ceiling - 1.0, POST_PILOT))
    step('connectors: closed holes in the left w')
    # connectors: closed holes in the left wall, sized for the plug's body
    body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(-USB["y"], USB["z"])
                    .rect(USB["w"], USB["h"]).extrude(WALL + 1.6).edges("|X").fillet(min(USB["r"], USB["h"] / 2 - 0.01)))
    for yc in (G.OUT_Y, G.IN_Y):
        body = body.cut(cq.Workplane("YZ").workplane(offset=-1).center(-yc, G.JACK_Z).circle(JACK_D / 2).extrude(WALL + 1.6))
    # SPEC v3: 0.5 x 45 deg on the outer mouth of the three holes, to guide the plug
    c, e = G.HOLE_CHAMFER, 0.02
    body = body.cut(cq.Workplane("YZ").workplane(offset=-e).center(-USB["y"], USB["z"])
                    .slot2D(USB["w"] + 2 * (c + e), USB["h"] + 2 * (c + e))
                    .workplane(offset=c + e).slot2D(USB["w"], USB["h"]).loft(combine=True))
    for yc in (G.OUT_Y, G.IN_Y):
        cone = cq.Solid.makeCone(JACK_D / 2 + c + e, JACK_D / 2, c + e, pnt=cq.Vector(-e, -yc, G.JACK_Z), dir=cq.Vector(1, 0, 0))
        body = body.cut(cq.Workplane("XY").add(cone))
    return body, bottom_r


def paint_recesses(body):
    """0.4 mm recesses to be filled with paint: the line under the screen, the logo, OUT and IN.
    Each letter is cut on its own: one cut with all of them at once does not end in OpenCascade."""
    wx0, wy0, wx1, wy1 = WINDOW
    ly = wy1 + LINE_UNDER_WINDOW[0]
    step("line under the window")
    body = body.cut(box(wx0, ly, wx1, ly + LINE_UNDER_WINDOW[1], ZT - ENGRAVE, ZT + 1))
    logo, tampa.info = logo_cutter()
    for k, g in enumerate(logo):
        step("logo %d" % k)
        body = body.cut(g)
    for txt, yc in (("OUT", G.OUT_Y), ("IN", G.IN_Y)):
        for k, g in enumerate(label_cutter(txt, yc + JACK_D / 2 + LABEL_GAP)):
            step("%s %d" % (txt, k))
            body = body.cut(g)
    return body


def oled_levels():
    ceiling = ZT - LID_T
    glass_top = ceiling - 0.1                     # the glass 0.1 under the pane's ledge
    pcb_top = glass_top - OLED_GLASS_T
    return {"glass_top": glass_top, "pcb_top": pcb_top, "pcb_bottom": pcb_top - OLED_PCB[2]}


def oled_centre():
    wx0, wy0, wx1, wy1 = WINDOW
    # SPEC v4 item 7: the module is turned 180 deg, its pin edge to the front; the active area is about 1.9 mm
    # nearer its pin edge than the middle of its board, so the board's centre is 1.9 mm BEHIND the window's
    return (wx0 + wx1) / 2, (wy0 + wy1) / 2 - 1.9


def oled_posts():
    cx, cy = oled_centre()
    dx, dy = OLED_PCB[0] / 2 - 2.0, OLED_PCB[1] / 2 - 2.0       # the module's four 2 mm holes
    return [(cx - dx, cy - dy), (cx + dx, cy - dy), (cx - dx, cy + dy), (cx + dx, cy + dy)]


# ------------------------------------------------------------------ base (the tray)
def tray_ribs():
    g = RIB_GRID
    out = []
    ny = int((g["y1"] - g["y0"]) // g["pitch"]) + 1
    nx = int((g["x1"] - g["x0"]) // g["pitch"]) + 1
    for j in range(ny):
        y = g["y0"] + j * g["pitch"]
        out.append((g["x0"], y - g["t"] / 2, g["x1"], y + g["t"] / 2))
    for i in range(nx):
        x = g["x0"] + i * g["pitch"]
        out.append((x - g["t"] / 2, g["y0"], x + g["t"] / 2, g["y1"]))
    return out


def base():
    zf = Z0 + FLOOR
    inset = WALL + TRAY_GAP
    body = outer(Z0, zf, inset)
    # rim along the lid's inner wall: 1.2 thick, top at RIM_TOP, lowered at the three sockets
    rim = outer(zf - 0.01, RIM_TOP, inset).cut(outer(zf - 1, RIM_TOP + 1, inset + RIM_T))
    for y0, y1 in RIM_ZONES:
        rim = rim.cut(box(0, y0, inset + RIM_T + 1, y1, RIM_LOW, RIM_TOP + 1))
    body = body.union(rim)
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
    for r in tray_ribs():             # stiffening ribs under the keyboard (the bending study: estudos/flexao.py)
        body = body.union(box(r[0], r[1], r[2], r[3], zf - 0.01, RIB_GRID["top"]))
    # battery cradle: low ribs on the back and the two ends
    bx0, by0, bx1, by1, _bt = BATTERY
    rib, h = 1.2, 2.0
    for r in ((bx0 - rib - 0.3, by0 - rib - 0.3, bx1 + rib + 0.3, by0 - 0.3),
              (bx0 - rib - 0.3, by0 - 0.3, bx0 - 0.3, by1 - 6), (bx1 + 0.3, by0 - 0.3, bx1 + rib + 0.3, by1 - 6)):
        body = body.union(box(r[0], r[1], r[2], r[3], zf - 0.01, zf + h))
    # holes
    for x, y in LID_HOLES:
        body = body.cut(cyl(x, y, Z0 - 1, 1, BOSS_HOLE)).cut(cyl(x, y, Z0 - 0.01, Z0 + HEAD_DEPTH, HEAD_D))
    for x, y in GRID_SCREWS:
        body = body.cut(cyl(x, y, under - NUT_POCKET_H, 1, NUT_POCKET_D))
    body = body.cut(cyl(PROGRAM[0], PROGRAM[1], Z0 - 1, zf + 1, 3.0))
    # the module's nut and the screw's end (SPEC v4 item 8): a recess in the floor, 1.0 left under it
    body = body.cut(cyl(H101[0], H101[1], zf - H101_RECESS[1], zf + 1, H101_RECESS[0]))
    return body


# ------------------------------------------------------------------ grid, spacer
def grade():
    body = hull_prism(G.GRID_EDGE, GRID_Z0, GRID_Z1)
    pts = [(x, -y) for _, x, y in G.KEYS]
    body = body.cut(cq.Workplane("XY").workplane(offset=GRID_Z0 - 1).pushPoints(pts).circle(GRID_HOLE / 2).extrude(GRID_T + 2))
    for px, py in (pts if GRID_HOLE_CHAMFER > 0 else []):
        cone = cq.Solid.makeCone(GRID_HOLE / 2, GRID_HOLE / 2 + GRID_HOLE_CHAMFER + 0.01, GRID_HOLE_CHAMFER + 0.01,
                                 pnt=cq.Vector(px, py, GRID_Z1 - GRID_HOLE_CHAMFER))
        body = body.cut(cq.Workplane("XY").add(cone))
    body = body.cut(cq.Workplane("XY").workplane(offset=GRID_Z0 - 1).pushPoints([(x, -y) for x, y in GRID_SCREWS])
                    .circle(SCREW_CLEAR / 2).extrude(GRID_T + 2))
    # SPEC v4 item 12: flat-head M2 screws (ISO 7046, head 3.8), flush with the grid's face: 90 deg countersinks
    depth = (CSK_D - SCREW_CLEAR) / 2 / math.tan(math.radians(CSK_ANGLE / 2))
    for sx, sy in GRID_SCREWS:
        cone = cq.Solid.makeCone(SCREW_CLEAR / 2, CSK_D / 2 + 0.01 + 0.0, depth + 0.01, pnt=cq.Vector(sx, -sy, GRID_Z1 - depth), dir=cq.Vector(0, 0, 1))
        body = body.cut(cq.Workplane("XY").add(cone))
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
    body = hat                      # SPEC v4 item 12: no sleeve, the 20 mm shaft reaches the knob itself
    # D bore for the shaft, from the sleeve's foot to 0.3 above the shaft's tip
    rb = k["shaft_d"] / 2 + k["bore_clear"]
    bore = cq.Workplane("XY").workplane(offset=z_under - 1).circle(rb).extrude(k["shaft_top"] + 0.3 - z_under + 1)
    flat_x = k["shaft_flat"] - k["shaft_d"] / 2 + k["bore_clear"]       # the flat's distance from the axis
    keep = (cq.Workplane("XY").workplane(offset=z_under - 2).center(flat_x + 5, 0).rect(10, 20)
            .extrude(k["shaft_top"] + 5))
    bore = bore.cut(keep)
    body = body.cut(bore)
    # the cream mark: a groove 0.8 wide on top, from the edge towards the middle (to be filled with paint)
    mark = cq.Workplane("XY").workplane(offset=k["top"] - 0.4).center(0, k["body_d"] / 4 + 0.3).rect(0.8, k["body_d"] / 2).extrude(1)
    body = body.cut(mark)
    return body, {"por_baixo": z_under, "topo": k["top"], "sem_luva": True, "encaixe_no_eixo_mm": round(k["shaft_top"] - z_under, 2), "furo_ate": k["shaft_top"] + 0.3}


# ------------------------------------------------------------------ acoustic box
def box_levels():
    ceiling = ZT - LID_T
    front = ceiling - MESH_T - FOAM_T          # the speaker's front face
    back = front - SPK_H
    return {"front": front, "back": back, "inside_z0": BOX_Z0 + BOX_FLOOR, "ear_top": back + 0.6 + EAR_T,
            "rim_top": front - 0.5}


def caixa_acustica():
    """The speaker's seat and its closed box, one piece. In plan a rectangle between the two screws
    (G.BOX_RECT); low under the speaker (the speaker's rim sits on its roof), tall beside it
    (x > G.BOX_LEG_X0): an L seen from the front. Ribs under the roof and under the tall part's wall."""
    lv = box_levels()
    x, y = SPK
    ceiling = ZT - LID_T
    x0, y0, x1, y1 = G.BOX_RECT
    xl = G.BOX_LEG_X0
    w = BOX_WALL
    zi = BOX_Z0 + BOX_FLOOR
    roof_top = lv["back"]
    roof_in = roof_top - BOX_ROOF
    leg_top = ceiling - 0.6
    leg_in = leg_top - BOX_ROOF
    ri = SPK_D / 2 + 0.2
    ro = ri + BOX_WALL
    x2 = BOX_LEG2_X1
    body = box(x0, y0, x1, y1, BOX_Z0, roof_top, 2.0).union(box(xl, y0, x1, y1, BOX_Z0, leg_top, 2.0))
    body = body.union(box(x0, y0, x2, y1, BOX_Z0, leg_top, 2.0))       # SPEC v4: tall also left of the speaker (volume)
    body = body.union(cyl(x, y, roof_top - 0.01, lv["rim_top"], 2 * ro))
    low = box(x0 + w, y0 + w, x1 - w, y1 - w, zi, roof_in, 0.8)
    tall = box(xl + w, y0 + w, x1 - w, y1 - w, zi, leg_in, 0.8)
    mouth = cyl(x, y, roof_in - 0.01, roof_top + 0.01, 2 * (ri - BOX_LEDGE))
    tall2 = box(x0 + w, y0 + w, x2 - w, y1 - w, zi, leg_in, 0.8)
    cavity = low.union(tall).union(tall2).union(mouth)
    # ribs: full height beside the speaker's mouth, 1.5 mm lower under it; two windows each join the cells
    ribs = None
    for rx, t in [(v, BOX_RIB) for v in BOX_RIBS_X] + [(xl + w / 2, w)]:
        r = box(rx - t / 2, y0 + w - 0.01, rx + t / 2, y1 - w + 0.01, zi - 0.01, roof_in + 0.01)
        r = r.cut(cyl(x, y, roof_in - 1.5, roof_in + 1, 2 * (ri - BOX_LEDGE) + 1.0))
        for wy in (y0 + (y1 - y0) * 0.3, y0 + (y1 - y0) * 0.7):
            r = r.cut(box(rx - t, wy - 4.0, rx + t, wy + 4.0, zi - 1, zi + 4.0))
        ribs = r if ribs is None else ribs.union(r)
    cavity = cavity.cut(ribs)
    body = body.cut(cavity)
    body = body.cut(cyl(x, y, roof_top, lv["rim_top"] + 1, 2 * ri))          # the speaker's seat
    for sx, sy in G.SPEAKER_SCREWS:
        ear = (cq.Workplane("XY").workplane(offset=lv["ear_top"] - EAR_T).center(sx, -(sy + y) / 2)
               .rect(EAR_D, abs(sy - y)).extrude(EAR_T)).union(cyl(sx, sy, lv["ear_top"] - EAR_T, lv["ear_top"], EAR_D))
        ear = ear.cut(cyl(x, y, BOX_Z0 - 1, lv["rim_top"] + 1, 2 * ri))
        body = body.union(ear).cut(cyl(sx, sy, lv["ear_top"] - EAR_T - 1, lv["ear_top"] + 1, 2.3))
    # the wires' hole in the front wall, towards J501 (closed with a drop of silicone after the wires pass)
    body = body.cut(cq.Workplane("XZ").workplane(offset=y1 - w - 1).center(WIRE_X, zi + 2.5).circle(0.8).extrude(-(w + 2)))
    # SPEC v4 item 10: grown to the left it meets the lid's inner chamfer plane: cut the box 0.4 mm under that plane
    ang = math.atan2(CHAMFER[1], CHAMFER[0])
    slope = CHAMFER[1] / CHAMFER[0]
    z_out0 = ZT - CHAMFER[1] - LID_T / math.cos(ang) - 0.4          # the plane at the outer wall's line, 0.4 mm lower
    xs = (ceiling - 0.4 - z_out0) / slope
    wedge = (cq.Workplane("XZ").workplane(offset=y0 - 1).polyline([(0, z_out0), (xs, ceiling - 0.4), (xs, ZT + 5), (0, ZT + 5)])
             .close().extrude(y1 - y0 + 2))
    body = body.cut(wedge)
    chamber = sum(s_.Volume() for s_ in cavity.solids().vals()) / 1000
    return body, {"camara_cm3": round(chamber, 2), "interior_z": [zi, roof_in], "interior_alto_z": [zi, leg_in],
                  "retangulo": list(G.BOX_RECT), "parte_alta_desde_x": xl, "topo_da_parte_alta_z": leg_top,
                  "nervuras_x": list(BOX_RIBS_X) + [xl + w / 2], "furo_dos_fios": [WIRE_X, y1],
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
    export("tampa", t, dict({"raio_de_baixo_da_aba": bottom_r}, **tampa.info))
    tray = base()
    export("base", tray)
    # SPEC v4 task 12: the wall coupon, the left 25 mm of the lid (three holes, labels, chamfers) and the tray's piece, to print
    # and try the first assembled board's sockets before the whole lid
    cut_l = box(-1, -1, 25, 101, Z0 - 1, ZT + 1)
    export("cupom_parede_tampa", t.intersect(cut_l))
    export("cupom_parede_bandeja", tray.intersect(cut_l))
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
    # the paint that fills the recesses, for the renders only (not a piece)
    wx0, wy0, wx1, wy1 = WINDOW
    ly = wy1 + LINE_UNDER_WINDOW[0]
    cut, paint, _info = logo_layout()
    ink = [box(wx0, ly, wx1, ly + LINE_UNDER_WINDOW[1], ZT - ENGRAVE, ZT - 0.05)] + cut
    for txt, yc in (("OUT", G.OUT_Y), ("IN", G.IN_Y)):
        ink += label_cutter(txt, yc + JACK_D / 2 + LABEL_GAP)
    for name, parts in (("tinta", ink), ("tinta_marrom", paint)):       # dark #2B2925 / brown #8A3A22
        comp = cq.Compound.makeCompound([s_ for g in parts for s_ in g.solids().vals()])
        cq.exporters.export(cq.Workplane("XY").add(comp), os.path.join(OUT, name + ".stl"), tolerance=0.01, angularTolerance=0.2)
    info["teclas"] = [{"fileira": r, "x": x, "y": y, "nota": NOTES[r][[k[1] for k in G.KEYS if k[0] == r].index(x)],
                       "tipo": kind_of(NOTES[r][[k[1] for k in G.KEYS if k[0] == r].index(x)])} for r, x, y in G.KEYS]
    info["niveis"] = {"base": Z0, "tampo": ZT, "fundo_da_bandeja": [Z0, Z0 + FLOOR], "borda_da_bandeja_ate": [RIM_TOP, RIM_LOW],
                      "tampa_sobre_a_grade": [GRID_ROOF, ZT], "teto_da_tampa": ZT - LID_T, "grade": [GRID_Z0, GRID_Z1],
                      "teto_sobre_a_grade": GRID_ROOF, "alojamento_da_tecla": HOUSING_TOP, "curso": TRAVEL,
                      "topo_dos_botoes": ROW_TOP, "piso_interno": Z0 + FLOOR, "oled": oled_levels(),
                      "chanfro_interno": [round(v, 2) for v in chamfer_inner()]}
    info["posicoes"] = {"nervuras_da_bandeja": RIB_GRID, "h101": H101, "parafusos_da_tampa": LID_HOLES, "parafusos_da_grade": GRID_SCREWS, "pinos": PINS, "pilares": PILLARS,
                        "bateria": BATTERY, "oled_centro": oled_centre(), "oled_postes": oled_posts(),
                        "falante": SPK, "parafusos_da_caixa": G.SPEAKER_SCREWS, "knobs": G.KNOBS}
    json.dump(info, open(os.path.join(OUT, "case.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
