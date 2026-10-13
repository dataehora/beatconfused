"""eTuttino case, parametric (CadQuery): the "Seixo" (plastic) and "Madeira"
(white oak) versions from SPEC.md. Both have the same outside; only the
wall thickness, the LED window and how the bottom closes differ.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe case.py

writes into out/:
  seixo_tampa.step/.stl      top shell (resin or MJF, one colour)
  seixo_fundo.step/.stl      bottom plate, screwed on from below
  madeira_corpo.step/.stl    the oak body (3-axis CNC)
  madeira_fundo.step/.stl    the thin bottom cover
  insert.step/.stl           black connector insert (USB + headphones), left face
  plate.step/.dxf            1.5 mm black switch plate (MX 14 x 14 holes)

keycap.py makes the button caps, fit_check.py checks the electronics
(SPEC item 9), render.py makes the PNGs. They all import this file.

Coordinates (SPEC 1): x from the left face (x = 0) to the right, y from the
back (y = 0) to the player (y = 100), z up from the table. Millimetres.
Values marked "conferir" in the SPEC are marked CHECK here.

That system is left-handed (x right, y towards you, z up), and a CAD
program is right-handed: built literally, the instrument comes out
mirrored, with the interface on the player's right. So everything is
modelled in SPEC coordinates and mirrored on export: in the STEP/STL files
y_file = 100 - y_spec, i.e. x right, y away from the player, z up.
"""
import math
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------- parameters
# keyboard (SPEC 2)
P = 19.05                     # button pitch
D_BTN = 15.0                  # button (dome) diameter
D_SKIRT = 17.0                # keycap skirt at its base
O_KEYS = 104.0                # x of xp = 0
ROW_Y = {1: 74.8, 2: 58.3, 3: 41.8, 4: 25.3}   # row 1 nearest the player
N_KEYS = 34                   # G3 (n = 0) .. E6 (n = 33)

# keyboard opening (SPEC 3)
CLR_SIDE = 15.0               # button edge to the opening, sides (perpendicular to the "<")
CLR_FB = 7.5                  # button edge to the opening, front and back
SIDE_ANGLE = 30.0             # the "<" and ">" lean 30 deg from the y axis
R_OPEN_CORNER = 6.0           # the four 120 deg corners (the lateral vertices are concentric)
CHAMFER_W = 4.0               # rounded edge round the opening, in plan
CHAMFER_DROP = 2.0            # ...and its drop; the last LID_T - CHAMFER_DROP is a vertical land

# box (SPEC 4)
WIDTH = 100.0
BOX_OFF = 10.3                # right/front/back: box = opening + 10.3
R_LEFT = 16.0                 # left corners
TRANS_TOP_OFF = 10.3          # top edge of the interface->keyboard slope = opening + this
                              # (SPEC 4 says "+20.3" but gives the vertex (56.6; 58.3),
                              # which is +10.3 -- the mirror of the right side. The vertex wins.)
Z_DECK = 15.7                 # top of the lid round the keys
Z_IF_BACK, Z_IF_FRONT = 33.0, 28.0   # interface top, sloping towards the player

# stack-up inside (same as the current board, etutti/hardware/assembly3d.py)
FLOOR_T = 2.0                 # bottom plate
UNDER_PCB = 4.5               # bottom plate to board: parts on the back + header legs
PCB_T = 1.2
Z_PCB_BOT = FLOOR_T + UNDER_PCB           # 6.5
Z_PCB_TOP = Z_PCB_BOT + PCB_T             # 7.7
PLATE_T = 1.5
Z_PLATE_TOP = Z_PCB_TOP + 5.0             # MX: plate top 5 mm above the board -> 12.7
LID_T = Z_DECK - Z_PLATE_TOP              # 3.0: the lid rests on the plate's edge
Z_KEY_TOP = 26.5
PLATE_OVERLAP = 3.0           # plate edge under the lid, beyond the opening

# interface area (SPEC 5)
SCREEN_ZONE = (10.0, 5.0, 64.0, 35.0)     # x0, y0, x1, y1
SCREEN_R = 3.0
SCREEN_MODE = "recess"        # "recess" (sticker/engraving, eTuttino), "window" (real screen), "none"
SCREEN_RECESS = 1.5           # CHECK
SCREEN_ACTIVE = (42.72, 22.70)            # Waveshare 1.9" 170x320, active area (x, y)
VOLUME_XY = (20.0, 45.0)
SELECT_XY = (37.0, 45.0)
SHAFT_HOLE_D = 6.8            # 6 mm shafts
LED_XY, LED_HOLE_D = (52.0, 45.0), 3.5
GHOST_SKIN = 0.8              # Madeira: wood left over the LED
GRILLE = [(13, 60), (55, 60), (58, 63), (75.5, 89), (73, 92), (13, 92), (10, 89), (10, 63)]
GRILLE_D, GRILLE_PITCH = 1.9, 4.0
GRILLE_KEEP = 1.0             # hole edge to the top edge of the slope (the SPEC outline crosses it by ~1.2 mm)

# connectors (SPEC 6)
USB_YZ, JACK_YZ = (36.0, 19.5), (56.0, 19.5)
INSERT = (36.0, 11.0)         # y, z size of the black insert in the left face
INSERT_CLR = 0.15
USB_PLUG_CUT = (11.5, 8.0)    # opening for the plug's overmould (y, z) -- CHECK the panel socket
JACK_HOLE_D = 6.2             # M6 panel jack -- CHECK
INSERT_FLANGE = 2.0           # flange behind the wall that stops the insert falling out
INSERT_WALL = 2.5             # the wall is thinned to this round the insert (Madeira's 4 mm
                              # wall would push the panel parts into the volume pot)

# versions (SPEC 8)
VERSIONS = {
    "seixo": {"wall": 2.5, "top": 2.5},     # resin / MJF
    "madeira": {"wall": 4.0, "top": 3.0},   # oak, 3-axis CNC
}
FUNDO_CLR = 0.3               # bottom plate to the walls
BOSS_D, PILOT_D = 6.0, 2.2    # M2.5 self-tapping (or a heat-set / wood insert)
SCREW_CLR_D, HEAD_D, HEAD_DEPTH = 2.9, 5.2, 1.4
PILLAR_D = 4.0                # board supports on the bottom plate
FOOT_D, FOOT_DEPTH = 10.5, 0.6

# ---------------------------------------------------------------- keyboard


def note_name(n):
    names = ["G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#"]
    return names[n % 12] + str(3 + (n + 7) // 12)


def keys():
    """Every button: (n, row, x, y, kind). kind: natural / sharp / cf (C or F)."""
    out = []
    for n in range(N_KEYS):
        rows = []
        if n % 3 == 2 and n <= 32:
            rows.append((1, (n - 2) / 3))
        if n % 3 == 0 and n <= 33:
            rows.append((2, n / 3 - 0.5))
        if n % 3 == 1 and n <= 31:
            rows.append((3, (n - 1) / 3))
        if n % 3 == 2 and 2 <= n <= 29:
            rows.append((4, (n - 2) / 3 + 0.5))
        for row, xp in rows:
            if (n + 7) % 12 in (1, 3, 6, 8, 10):
                kind = "sharp"
            elif n in (5, 10, 17, 22, 29):
                kind = "cf"
            else:
                kind = "natural"
            out.append((n, row, O_KEYS + xp * P, ROW_Y[row], kind))
    return out


ROW2_X = (O_KEYS - 0.5 * P, O_KEYS + 10.5 * P)     # end buttons of row 2: 94.475, 304.025

# ---------------------------------------------------------------- 2D contours
TAN = math.tan(math.radians(SIDE_ANGLE))
COS = math.cos(math.radians(SIDE_ANGLE))


def hex_contour(d):
    """The keyboard opening grown by d: [(vertex, radius)], clockwise in
    plan starting at the back-left corner. Sharp vertices as in SPEC 3."""
    ytop = ROW_Y[4] - D_BTN / 2 - CLR_FB - d
    ybot = ROW_Y[1] + D_BTN / 2 + CLR_FB + d
    side = D_BTN / 2 + CLR_SIDE + d
    yl = ROW_Y[2]
    xl = ROW2_X[0] - side / COS
    xr = ROW2_X[1] + side / COS
    return [((xl + (yl - ytop) * TAN, ytop), R_OPEN_CORNER + d),
            ((xr - (yl - ytop) * TAN, ytop), R_OPEN_CORNER + d),
            ((xr, yl), side),
            ((xr - (ybot - yl) * TAN, ybot), R_OPEN_CORNER + d),
            ((xl + (ybot - yl) * TAN, ybot), R_OPEN_CORNER + d),
            ((xl, yl), side)]


def box_contour():
    """Plan outline (SPEC 4): the opening + BOX_OFF on the right, front and
    back (front/back clamped to y = 0 / WIDTH), a straight left face."""
    h = hex_contour(BOX_OFF)
    (xr, yr), rr = h[2]
    front = (xr - (WIDTH - yr) * TAN, WIDTH)
    back = (xr - (yr - 0.0) * TAN, 0.0)
    return [((0.0, 0.0), R_LEFT), (back, h[1][1]), h[2], (front, h[3][1]), ((0.0, WIDTH), R_LEFT)]


def _fillet(prev, v, nxt, r):
    """Tangent points, arc midpoint and centre of a fillet of radius r at v."""
    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        return dx / L, dy / L
    u1, u2 = unit(v, prev), unit(v, nxt)
    theta = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
    t = r / math.tan(theta / 2)
    bx, by = u1[0] + u2[0], u1[1] + u2[1]
    bl = math.hypot(bx, by)
    bx, by = bx / bl, by / bl
    c = r / math.sin(theta / 2)
    centre = (v[0] + bx * c, v[1] + by * c)
    return ((v[0] + u1[0] * t, v[1] + u1[1] * t), (centre[0] - bx * r, centre[1] - by * r),
            (v[0] + u2[0] * t, v[1] + u2[1] * t), centre)


def fillets(contour):
    n = len(contour)
    return [_fillet(contour[i - 1][0], contour[i][0], contour[(i + 1) % n][0], contour[i][1])
            for i in range(n)]


def contour_wp(contour, z=0.0):
    """A closed CadQuery wire (lines + true arcs) on the plane z."""
    f = fillets(contour)
    wp = cq.Workplane("XY", origin=(0, 0, z)).moveTo(*f[0][2])
    for i in range(1, len(f) + 1):
        a_in, mid, a_out, _ = f[i % len(f)]
        wp = wp.lineTo(*a_in).threePointArc(mid, a_out)
    return wp.close()


def contour_points(contour, seg=1.0):
    """The same outline as a polygon (arcs split into ~seg mm chords)."""
    pts = []
    for a_in, mid, a_out, c in fillets(contour):
        r = math.hypot(a_in[0] - c[0], a_in[1] - c[1])
        a0 = math.atan2(a_in[1] - c[1], a_in[0] - c[0])
        a1 = math.atan2(a_out[1] - c[1], a_out[0] - c[0])
        am = math.atan2(mid[1] - c[1], mid[0] - c[0])
        # go the way that passes the midpoint
        da = (a1 - a0) % (2 * math.pi)
        if (am - a0) % (2 * math.pi) > da:
            da -= 2 * math.pi
        k = max(2, int(abs(da) * r / seg))
        pts += [(c[0] + r * math.cos(a0 + da * i / k), c[1] + r * math.sin(a0 + da * i / k))
                for i in range(k + 1)]
    return pts


def prism(contour, z0, z1):
    return contour_wp(contour, z0).extrude(z1 - z0).val()


def point_in_poly(p, poly):
    x, y = p
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def dist_to_poly(p, poly):
    best = 1e9
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((p[0] - x0) * dx + (p[1] - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - x0 - t * dx, p[1] - y0 - t * dy))
    return best


def z_interface(y, dz=0.0):
    return Z_IF_BACK + (Z_IF_FRONT - Z_IF_BACK) * y / WIDTH - dz


def opening_offset(p):
    """How far outside the keyboard opening a plan point is (negative inside)."""
    poly = contour_points(hex_contour(0.0), 0.5)
    d = dist_to_poly(p, poly)
    return -d if point_in_poly(p, poly) else d

# ---------------------------------------------------------------- 3D helpers


def box3(x0, y0, z0, x1, y1, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cyl(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0))


def fuse(shapes):
    out = shapes[0]
    if len(shapes) > 1:
        out = out.fuse(*shapes[1:])
    return out.clean()


def below_plane(dz=0.0, x0=-50, x1=450):
    """Everything under the interface's sloping top (lowered by dz)."""
    y0, y1 = -50.0, WIDTH + 50.0
    wp = (cq.Workplane("YZ", origin=(x0, 0, 0))
          .polyline([(y0, -10), (y1, -10), (y1, z_interface(y1, dz)), (y0, z_interface(y0, dz))])
          .close().extrude(x1 - x0))
    return wp.val()


def left_lines(d, y_from=-30.0, y_to=WIDTH + 30.0):
    """The "<" of the opening grown by d, as a polyline from behind the box
    to in front of it (lateral fillet sampled), plus outward normals."""
    c = hex_contour(d)
    # the left lateral arc is round vertex 5; keep the points left of the corners' x
    a_in, mid, a_out, centre = fillets(c)[5]
    r = c[5][1]
    a0 = math.atan2(a_in[1] - centre[1], a_in[0] - centre[0])
    a1 = math.atan2(a_out[1] - centre[1], a_out[0] - centre[0])
    if a1 < a0:
        a1 += 2 * math.pi
    k = 36
    arc = [(centre[0] + r * math.cos(a0 + (a1 - a0) * i / k), centre[1] + r * math.sin(a0 + (a1 - a0) * i / k))
           for i in range(k + 1)]
    # arc runs front (a_in, from the bottom-left corner) -> back (a_out); make it back -> front
    arc = arc[::-1]
    normals = [((x - centre[0]) / r, (y - centre[1]) / r) for x, y in arc]
    # extend the straight sides to y_from / y_to
    (xb, yb), (xf, yf) = arc[0], arc[-1]
    back = (xb + (yb - y_from) * TAN, y_from)
    front = (xf + (y_to - yf) * TAN, y_to)
    return [back] + arc + [front], [normals[0]] + normals + [normals[-1]]


def raised_region(foot_d, z_foot, top_d, dz_top, z_hi=60.0):
    """The interface block with its "<" slope: the ruled surface from the
    opening+foot_d line (at z_foot) up to the opening+top_d line (on the
    sloping top lowered by dz_top), extended to z_hi; everything left of
    it, below the sloping top. Returned as a solid to intersect with the
    box."""
    foot, normals = left_lines(foot_d)
    lo, hi = [], []
    for (x, y), (nx, ny) in zip(foot, normals):
        qx, qy = x + nx * (top_d - foot_d), y + ny * (top_d - foot_d)
        zq = z_interface(qy, dz_top)
        s = (z_hi - z_foot) / (zq - z_foot)
        lo.append(cq.Vector(x, y, z_foot))
        hi.append(cq.Vector(x + (qx - x) * s, y + (qy - y) * s, z_hi))
    far = -60.0
    lo += [cq.Vector(far, lo[-1].y, z_foot), cq.Vector(far, lo[0].y, z_foot)]
    hi += [cq.Vector(far, hi[-1].y, z_hi), cq.Vector(far, hi[0].y, z_hi)]
    w_lo = cq.Wire.makePolygon(lo, close=True)
    w_hi = cq.Wire.makePolygon(hi, close=True)
    loft = cq.Solid.makeLoft([w_lo, w_hi], ruled=True)
    return loft.intersect(below_plane(dz_top))


def rounded_opening_cutter():
    """The keyboard opening with its 4 mm rounded edge (quarter ellipse,
    CHAMFER_W across, CHAMFER_DROP down, then a vertical land to the
    plate), as one solid to cut from the lid."""
    secs = []
    n = 8
    z_land = Z_DECK - CHAMFER_DROP
    for i in range(n + 1):
        phi = math.pi / 2 * i / n
        d = CHAMFER_W * (1 - math.cos(phi))
        z = z_land + CHAMFER_DROP * math.sin(phi)
        secs.append(contour_wp(hex_contour(d), z).wire().val())
    loft = cq.Solid.makeLoft(secs, ruled=False)
    below = prism(hex_contour(0.0), Z_PLATE_TOP - 3.0, z_land + 0.001)
    above = prism(hex_contour(CHAMFER_W), Z_DECK - 0.001, Z_DECK + 5.0)
    return fuse([loft, below, above])

# ---------------------------------------------------------------- fixings


def screw_points():
    """Bosses for the screws from below (both versions): along the walls,
    clear of the keys, the plate edge (notched round them), the stack and
    the connector insert."""
    return [(7.0, 8.0), (7.0, 92.0),                  # left corners, clear of the screen module
            (78.0, 7.0), (78.0, 93.0),                # under the slope, back and front
            (165.0, 6.0), (165.0, 94.0),
            (255.0, 6.0), (255.0, 94.0),
            (332.0, ROW_Y[2])]                        # right vertex, merged into the wall


def pillar_points():
    """Board supports: the centres of triangles of three neighbouring
    buttons (11 mm from each sensor), every third column, between each
    pair of rows; plus a few under the interface area."""
    pts = []
    for (ra, rb) in ((1, 2), (2, 3), (3, 4)):
        ya, yb = ROW_Y[ra], ROW_Y[rb]
        # rows 1 and 3 have xp = 0, 1, ..; 2 and 4 are half a pitch off
        for i in range(0, 11, 3):
            x = O_KEYS + i * P + (0.0 if rb != 2 else 0.0)
            # triangle (x, ya) (x +- P/2, yb): centroid
            pts.append((x, ya + (yb - ya) * 2 / 3) if ra in (1, 3) else (x + P / 2, ya + (yb - ya) / 3))
    pts += [(30.0, 60.0), (60.0, 75.0), (12.0, 70.0)]
    return pts

# ---------------------------------------------------------------- parts


def outer_body():
    """The solid outside shape (SPEC 4): box to the deck height, the
    raised interface block with its "<" slope, the rounded keyboard opening."""
    outline = box_contour()
    base = prism(outline, 0.0, Z_DECK)
    tall = prism(outline, 0.0, Z_IF_BACK + 5.0)
    raised = raised_region(CHAMFER_W, Z_DECK, TRANS_TOP_OFF, 0.0).intersect(tall)
    return base.fuse(raised).clean()


def cavity(v):
    """The inside: walls v["wall"], lid v["top"] under the interface (the
    keyboard lid is LID_T, set by the plate), open at the bottom."""
    wall, top = v["wall"], v["top"]
    inner = contour_wp(box_contour()).offset2D(-wall).wires().val()
    inner_wp = lambda z0, z1: cq.Workplane("XY", origin=(0, 0, z0)).add(inner.translate(cq.Vector(0, 0, z0))).toPending().extrude(z1 - z0).val()
    low = inner_wp(-1.0, Z_PLATE_TOP)
    tall = inner_wp(-1.0, Z_IF_BACK)
    # the inside of the slope: its foot (at the lid's underside) and top
    # edge pulled left by the wall thickness
    raised = raised_region(CHAMFER_W + wall, Z_PLATE_TOP, TRANS_TOP_OFF + wall, top).intersect(tall)
    return low.fuse(raised).clean()


def grille_holes():
    poly = [tuple(map(float, p)) for p in GRILLE]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    out = []
    r = GRILLE_D / 2
    y = min(ys) + 2.0
    while y <= max(ys) - 1.9:
        x = min(xs) + 2.0
        while x <= max(xs):
            ok = point_in_poly((x, y), poly) and dist_to_poly((x, y), poly) >= r + 0.6
            ok = ok and opening_offset((x, y)) >= TRANS_TOP_OFF + r + GRILLE_KEEP
            if ok:
                out.append((x, y))
            x += GRILLE_PITCH
        y += GRILLE_PITCH
    return out


def rrect(x0, y0, x1, y1, r, z0, z1):
    return (cq.Workplane("XY", origin=(0, 0, z0)).center((x0 + x1) / 2, (y0 + y1) / 2)
            .rect(x1 - x0, y1 - y0).extrude(z1 - z0).edges("|Z").fillet(r).val())


def top_features(v, ghost_led=False):
    """Cuts in the top: screen recess/window, shafts, LED, grille."""
    cuts = []
    x0, y0, x1, y1 = SCREEN_ZONE
    if SCREEN_MODE in ("recess", "window"):
        zone = rrect(x0, y0, x1, y1, SCREEN_R, 0, 50)
        cuts.append(zone.cut(below_plane(SCREEN_RECESS)))
    if SCREEN_MODE == "window":
        aw, ah = SCREEN_ACTIVE
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        cuts.append(rrect(cx - aw / 2 - 0.5, cy - ah / 2 - 0.5, cx + aw / 2 + 0.5, cy + ah / 2 + 0.5, 1.0, 0, 50))
    for x, y in (VOLUME_XY, SELECT_XY):
        cuts.append(cyl(x, y, 0, 50, SHAFT_HOLE_D))
    lx, ly = LED_XY
    if ghost_led:
        cuts.append(cyl(lx, ly, 0, z_interface(ly) - GHOST_SKIN, LED_HOLE_D))
    else:
        cuts.append(cyl(lx, ly, 0, 50, LED_HOLE_D))
    cuts += [cyl(x, y, 0, 50, GRILLE_D) for x, y in grille_holes()]
    return cuts


def insert_cut(v):
    w, h = INSERT
    (yc, zc) = (USB_YZ[0] + JACK_YZ[0]) / 2, USB_YZ[1]
    c = INSERT_CLR
    hole = box3(-1, yc - w / 2 - c, zc - h / 2 - c, 10, yc + w / 2 + c, zc + h / 2 + c)
    if v["wall"] <= INSERT_WALL:
        return hole
    m = INSERT_FLANGE + 2.0     # pocket from inside, round the flange
    return hole.fuse(box3(INSERT_WALL, yc - w / 2 - m, zc - h / 2 - m, v["wall"] + 0.5, yc + w / 2 + m, zc + h / 2 + m))


def bosses(v, body):
    """Screw columns: from the bottom plate up into the top, inside the
    wall line, trimmed to the outside shape."""
    out = []
    for x, y in screw_points():
        col = cyl(x, y, FLOOR_T, 60, BOSS_D).intersect(body)
        out.append(col)
    return out


def shell(v, ghost_led=False):
    body = outer_body()
    s = body.cut(cavity(v))
    s = s.fuse(*bosses(v, body)).clean()
    cuts = [rounded_opening_cutter(), insert_cut(v)] + top_features(v, ghost_led)
    cuts += [cyl(x, y, FLOOR_T - 0.01, FLOOR_T + 9.0, PILOT_D) for x, y in screw_points()]
    s = s.cut(fuse(cuts))
    # flush bottom plate sits inside the walls
    return s.clean()


def fundo(v, t=FLOOR_T):
    """Bottom plate, inside the walls, flush with their bottom edge."""
    inner = contour_wp(box_contour()).offset2D(-v["wall"] - FUNDO_CLR).wires().val()
    plate = cq.Workplane("XY").add(inner).toPending().extrude(t).val()
    adds = [cyl(x, y, t - 0.01, Z_PCB_BOT, PILLAR_D) for x, y in pillar_points()]
    plate = plate.fuse(*adds)
    cuts = []
    for x, y in screw_points():
        cuts.append(cyl(x, y, -1, t + 1, SCREW_CLR_D))
        cuts.append(cyl(x, y, -1, HEAD_DEPTH, HEAD_D))
    for fx, fy in ((25, 14), (25, 86), (300, 14), (300, 86)):
        cuts.append(cyl(fx, fy, -1, FOOT_DEPTH, FOOT_D))
    return plate.cut(fuse(cuts)).clean()


def switch_plate():
    """1.5 mm black plate: the opening plus PLATE_OVERLAP, MX holes, notched
    round the screw bosses."""
    p = prism(hex_contour(PLATE_OVERLAP), Z_PLATE_TOP - PLATE_T, Z_PLATE_TOP)
    cuts = [box3(x - 7, y - 7, 0, x + 7, y + 7, 30) for _, _, x, y, _ in keys()]
    cuts += [cyl(x, y, 0, 30, BOSS_D + 1.0) for x, y in screw_points()]
    return p.cut(fuse(cuts)).clean()


def connector_insert():
    """Black insert for the left face: flush outside, with a flange inside."""
    w, h = INSERT
    yc, zc = (USB_YZ[0] + JACK_YZ[0]) / 2, USB_YZ[1]
    t = INSERT_WALL
    body = box3(0.0, yc - w / 2, zc - h / 2, t, yc + w / 2, zc + h / 2)
    flange = box3(t, yc - w / 2 - INSERT_FLANGE, zc - h / 2 - INSERT_FLANGE / 2,
                  t + 1.5, yc + w / 2 + INSERT_FLANGE, zc + h / 2 + INSERT_FLANGE / 2)
    ins = body.fuse(flange)
    pw, ph = USB_PLUG_CUT
    ins = ins.cut(box3(-1, USB_YZ[0] - pw / 2, zc - ph / 2, 10, USB_YZ[0] + pw / 2, zc + ph / 2))
    ins = ins.cut(cq.Solid.makeCylinder(JACK_HOLE_D / 2, 10, cq.Vector(-1, JACK_YZ[0], JACK_YZ[1]), cq.Vector(1, 0, 0)))
    return ins.clean()


def madeira_body():
    """One oak block: same outside, thicker walls, ghost LED, a rebate in
    the bottom for the thin cover."""
    return shell(VERSIONS["madeira"], ghost_led=True)

# ---------------------------------------------------------------- export


def to_file(shape):
    """SPEC coordinates -> the files' right-handed ones (see the top)."""
    return shape.mirror("XZ", (0, WIDTH / 2, 0))


def export(shape, name, tol=0.05, mirror=True):
    os.makedirs(OUT, exist_ok=True)
    assert shape.isValid(), name
    if mirror:
        shape = to_file(shape)
    cq.exporters.export(cq.Workplane().add(shape), os.path.join(OUT, name + ".step"))
    cq.exporters.export(cq.Workplane().add(shape), os.path.join(OUT, name + ".stl"),
                        tolerance=tol, angularTolerance=0.2)
    bb = shape.BoundingBox()
    print("%-16s %6.1f x %5.1f x %4.1f mm  %6.1f cm3" % (name, bb.xlen, bb.ylen, bb.zlen, shape.Volume() / 1000))


def build_all():
    seixo, madeira = VERSIONS["seixo"], VERSIONS["madeira"]
    parts = {
        "seixo_tampa": shell(seixo),
        "seixo_fundo": fundo(seixo),
        "madeira_corpo": madeira_body(),
        "madeira_fundo": fundo(madeira, t=FLOOR_T),
        "insert": connector_insert(),
        "plate": switch_plate(),
    }
    return parts


def main():
    print("length %.2f mm (SPEC ~336.8)" % (ROW2_X[1] + D_BTN / 2 + CLR_SIDE + BOX_OFF))
    for name, shape in build_all().items():
        export(shape, name)
    # the plate as a 2D drawing for laser/waterjet cutting (mm, top view)
    flat = cq.Workplane().add(to_file(switch_plate())).faces("<Z")
    cq.exporters.export(flat, os.path.join(OUT, "plate.dxf"))


if __name__ == "__main__":
    main()
