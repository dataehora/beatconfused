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
P = 18.5                      # button pitch, the same to all six neighbours (the user's
                              # choice after SPEC v5, which still says 19.05)
D_BTN = 15.0                  # button (dome) diameter
D_SKIRT = 16.5                # keycap skirt at its base (v6: 2 mm between neighbours)
O_KEYS = 104.0                # x of xp = 0
ROW_PITCH = P * math.cos(math.radians(30))     # 16.02: rows half a pitch apart in x -> equilateral
KEYS_CY = 50.0                                 # keys centred front to back
ROW_Y = {r: KEYS_CY + (2.5 - r) * ROW_PITCH for r in (1, 2, 3, 4)}   # row 1 nearest the player
# (74.03 / 58.01 / 41.99 / 25.97 at 18.5; SPEC v5's 74.8 / 58.3 / 41.8 / 25.3 are for 19.05)
N_KEYS = 34                   # G3 (n = 0) .. E6 (n = 33)

# keyboard opening (SPEC 3)
CLR_SIDE = 15.0               # button edge to the opening, sides (perpendicular to the "<")
CLR_FB = None                 # button edge to the opening, front and back: set below so the
                              # deck round the keys stays BOX_OFF wide in the 100 mm box (8.17)
SIDE_ANGLE = 30.0             # the "<" and ">" lean 30 deg from the y axis
R_OPEN_CORNER = 6.0           # the four 120 deg corners (the lateral vertices are concentric)
CHAMFER_W = 4.0               # rounded edge round the opening, in plan
CHAMFER_DROP = 2.0            # ...and its drop; the rest, LID_T - CHAMFER_DROP (2.7), is a vertical land

# box (SPEC 4)
WIDTH = 100.0
BOX_OFF = 10.3                # right/front/back: box = opening + 10.3
R_LEFT = 16.0                 # left corners
CLR_FB = WIDTH / 2 - BOX_OFF - 1.5 * ROW_PITCH - D_BTN / 2
Z_DECK = 17.4                 # top of the lid round the keys (v6; was 15.7): hides more of the switch
# interface top (SPEC v5 4): flat at Z_IF to the crease, then down at IF_SLOPE to the front
Z_IF = 33.0
IF_CREASE_Y = 55.0
IF_SLOPE = 13.0               # degrees
IF_CREASE_R = 10.0            # the rounded crease -- SPEC gives no radius: CHECK
# the ramp from the interface down to the keyboard deck (SPEC v5 4)
RAMP_TOP_OFF = 12.7           # top edge = opening + 12.7 in the back half (R 35.2 round G3)
RAMP_FOOT_OFF = 4.0           # bottom edge = the chamfer's outer edge (opening + 4, R 26.5)
RAMP_STRAIGHT_TO = 86.0       # front half: both edges run straight (along y) to here...
RAMP_FRONT_R = 14.0           # ...then curve with R 14 towards the front face
RAMP_FRONT_SWEEP = 75.0       # degrees of that curve; it leaves straight from there and meets the
                              # face at 15 deg (a full 90 deg meets it tangentially, and OCC can't
                              # round the ramp's foot where it runs along the wall)
RAMP_EDGE_R = 5.0             # both ramp edges rounded

# stack-up inside (same as the current board, etutti/hardware/assembly3d.py)
FLOOR_T = 2.0                 # bottom plate
UNDER_PCB = 4.5               # bottom plate to board: parts on the back + header legs
PCB_T = 1.2
Z_PCB_BOT = FLOOR_T + UNDER_PCB           # 6.5
Z_PCB_TOP = Z_PCB_BOT + PCB_T             # 7.7
PLATE_T = 1.6                 # FR-4 (v8): the fab's standard; MX expects 1.5
SWITCH_UNDER_PLATE = 3.5      # MX bottom housing: board to the plate's underside
Z_PLATE_TOP = Z_PCB_TOP + SWITCH_UNDER_PLATE + PLATE_T   # 12.8 (12.7 with a 1.5 plate)
LID_T = Z_DECK - Z_PLATE_TOP              # 4.6: the lid rests on the plate's edge
Z_KEY_TOP = 26.5 + (PLATE_T - 1.5)        # the buttons ride up with the plate: 26.6
PLATE_OVERLAP = 3.0           # plate edge under the lid, beyond the opening

# interface area (SPEC 5)
SCREEN_ZONE = (8.0, 5.0, 62.0, 35.0)      # x0, y0, x1, y1
SCREEN_R = 3.0
SCREEN_MODE = "recess"        # "recess" (sticker/engraving, eTuttino), "window" (real screen), "none"
SCREEN_RECESS = 1.5           # CHECK
SCREEN_ACTIVE = (42.72, 22.70)            # Waveshare 1.9" 170x320, active area (x, y)
VOLUME_XY = (20.0, 45.0)
SELECT_XY = (37.0, 45.0)
SHAFT_HOLE_D = 6.8            # 6 mm shafts
LED_XY, LED_HOLE_D = (52.0, 45.0), 3.5
LIGHT_PIPE_D, LIGHT_PIPE_HOLE = 3.0, 3.1   # Madeira (v7): a bought 3 mm round light pipe, tip sanded flush -- CHECK
LIGHT_PIPE_L = 6.0            # its length down to just above the LED -- CHECK the part bought
GRILLE_RECT = (8.0, 61.0, 53.0, 94.0)     # on the 13 deg slope; corners R 3,
GRILLE_R, GRILLE_R_FR = 3.0, 8.0          # the front-right one R 8 (concentric with the ramp's curve)
GRILLE_D, GRILLE_PITCH = 1.9, 4.0         # pitch measured on the sloping surface

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
    "madeira": {"wall": 4.0, "top": 3.0, "led_hole": LIGHT_PIPE_HOLE},   # oak, 3-axis CNC
}
FUNDO_CLR = 0.3               # bottom plate to the walls
BOSS_D, PILOT_D = 6.0, 2.2    # M2.5 self-tapping (or a heat-set / wood insert)
SCREW_CLR_D, HEAD_D, HEAD_DEPTH = 2.9, 5.2, 1.4
PILLAR_D = 4.0                # board supports on the bottom plate
# v8: the board is screwed down under the interface, M2 from below through
# these two pillars (made fatter), a nut on top of the board
SCREW_PILLARS = [(30.0, 60.0), (12.0, 70.0)]
SCREW_PILLAR_D = 6.0
M2_CLR_D, M2_HEAD_D, M2_HEAD_DEPTH = 2.4, 4.2, 1.4
# v8: the controls board (etutti/hardware/controls_pcb.py) hangs under the
# interface lid on two posts; its parts' tops touch the lid's underside
CONTROLS = {
    "rect": (14.5, 35.5, 56.0, 61.0),           # x0, y0, x1, y1 (front edge clear of the Chorus speaker)
    "pot": (20.0, 45.0), "pot_rot": 180,        # RK09K, pins to the right
    "encoder": (37.0, 45.0), "encoder_rot": 270,  # EC11E, A/B/C to the back, switch legs to the front
    "led": (52.0, 45.0),
    "jst": (37.0, 55.5), "jst_rot": 0,          # B8B-PH-K on the back, facing down: the cable drops to J3
    "holes": [(17.0, 58.5), (53.0, 40.0)],      # M2 into the lid's posts
    "thickness": 1.6,
    "body_h": 6.5,                              # pot / encoder bodies above the board
    "body_front_y": 51.6,                       # their front edge (the lid is lowest there)
}
POST_D, POST_PILOT_D, POST_PILOT_DEPTH = 5.0, 1.7, 6.0
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


TAN_IF = math.tan(math.radians(IF_SLOPE))
COS_IF = math.cos(math.radians(IF_SLOPE))


def z_interface(y, dz=0.0):
    """Height of the interface top at y (the crease's rounding ignored), or
    of the lid's underside when dz is the lid thickness."""
    flat = Z_IF - dz
    slope = Z_IF - (y - IF_CREASE_Y) * TAN_IF - dz / COS_IF
    return min(flat, slope)


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
    """Everything under the interface's top (flat, rounded crease, 13 deg
    down to the front), lowered by dz (the same profile offset: the lid
    keeps its thickness round the crease)."""
    y0, y1 = -50.0, WIDTH + 50.0
    yc = IF_CREASE_Y - dz * (1 / COS_IF - 1) / TAN_IF          # the offset lines' corner
    corner = (yc, Z_IF - dz)
    a = (y0, Z_IF - dz)
    b = (y1, z_interface(y1, dz))
    t1, mid, t2, _ = _fillet(a, corner, b, max(IF_CREASE_R - dz, 0.5))
    wp = (cq.Workplane("YZ", origin=(x0, 0, 0)).moveTo(y0, -10).lineTo(*a).lineTo(*t1)
          .threePointArc(mid, t2).lineTo(*b).lineTo(y1, -10).close().extrude(x1 - x0))
    return wp.val()


def ramp_segments(d, r_front, y_from=-30.0, n_back=40, n_str=14, k_arc=24):
    """One edge of the ramp in plan, back to front, as five tangent pieces:
    the opening's "<" grown by d (straight, then the arc round G3 down to
    row 2), straight along y to RAMP_STRAIGHT_TO, an arc of r_front through
    RAMP_FRONT_SWEEP, then straight on out through the front face. Each
    piece is (kind, points); the two edges (foot and top) have the same
    pieces and the same (fixed) point counts, so their points pair up one
    to one."""
    c = hex_contour(d)
    a_in, mid, a_out, centre = fillets(c)[5]
    r = c[5][1]
    a_back = math.atan2(a_out[1] - centre[1], a_out[0] - centre[0]) % (2 * math.pi)   # ~210 deg

    def line(p, q, n):
        return [(p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n) for i in range(n + 1)]
    xb, yb = a_out
    start = (xb + (yb - y_from) * TAN, y_from)
    segs = [("line", line(start, a_out, n_back))]
    segs.append(("arc", [(centre[0] + r * math.cos(a_back + (math.pi - a_back) * i / k_arc),
                          centre[1] + r * math.sin(a_back + (math.pi - a_back) * i / k_arc)) for i in range(k_arc + 1)]))
    xv = centre[0] - r
    segs.append(("line", line((xv, centre[1]), (xv, RAMP_STRAIGHT_TO), n_str)))
    cx = xv - r_front
    sweep = math.radians(RAMP_FRONT_SWEEP)
    segs.append(("arc", [(cx + r_front * math.cos(sweep * i / k_arc), RAMP_STRAIGHT_TO + r_front * math.sin(sweep * i / k_arc))
                         for i in range(k_arc + 1)]))
    x, y = segs[-1][1][-1]
    L = (WIDTH + 6.0 - y) / math.cos(sweep)      # just past the front face (far out, it ran into the closing edges)
    segs.append(("line", line((x, y), (x - L * math.sin(sweep), y + L * math.cos(sweep)), 8)))
    return segs


def ramp_edge(d, r_front):
    """ramp_segments() as one list of points (joints not repeated)."""
    pts = []
    for _, seg in ramp_segments(d, r_front):
        pts += seg[1:] if pts else seg
    return pts


def raised_region(foot_d, z_foot, top_d, dz_top, r_front=RAMP_FRONT_R, z_hi=40.0):
    """The interface block and its ramp: the ruled surface from the foot
    edge (at z_foot) up through the top edge (on the interface top lowered
    by dz_top), extended to z_hi; everything left of it, under the top."""
    foot = ramp_edge(foot_d, r_front)
    top = ramp_edge(top_d, r_front)
    lo, hi = [], []
    for (x, y), (qx, qy) in zip(foot, top):
        zq = z_interface(min(qy, WIDTH), dz_top)   # past the front face: keep the front's height
        s_ = (z_hi - z_foot) / (zq - z_foot)
        lo.append(cq.Vector(x, y, z_foot))
        hi.append(cq.Vector(x + (qx - x) * s_, y + (qy - y) * s_, z_hi))
    # one spline per edge through densely, evenly paired points: a single
    # smooth ramp face (exact lines + arcs here make OCC's fillets invalid)
    lo_edges, hi_edges = [cq.Edge.makeSpline(lo)], [cq.Edge.makeSpline(hi)]
    far = -60.0

    def close(edges, z):
        a = edges[-1].endPoint()
        b = edges[0].startPoint()
        tail = [a, cq.Vector(far, a.y, z), cq.Vector(far, b.y, z), b]
        return cq.Wire.assembleEdges(edges + [cq.Edge.makeLine(p, q) for p, q in zip(tail, tail[1:])])
    loft = cq.Solid.makeLoft([close(lo_edges, z_foot), close(hi_edges, z_hi)], ruled=True)
    return loft.intersect(below_plane(dz_top))


def rounded_opening_cutter():
    """The keyboard opening with its 4 mm rounded edge (quarter ellipse,
    CHAMFER_W across, CHAMFER_DROP down, then a vertical land to the
    plate), as ONE ruled loft through stacked opening contours: straight
    down through the lid, the rounding in 16 steps (0.02 mm off a true
    ellipse), and on up above the deck. One solid, one cut: a separate
    prism and loft, fused or cut in turn, left films or split pieces."""
    z_land = Z_DECK - CHAMFER_DROP
    levels = [(0.0, Z_PLATE_TOP - 3.0), (0.0, z_land)]
    n = 16
    for i in range(1, n + 1):
        phi = math.pi / 2 * i / n
        levels.append((CHAMFER_W * (1 - math.cos(phi)), z_land + CHAMFER_DROP * math.sin(phi)))
    levels.append((CHAMFER_W, Z_DECK + 5.0))
    secs = [contour_wp(hex_contour(d), z).wire().val() for d, z in levels]
    return [cq.Solid.makeLoft(secs, ruled=True)]


# ---------------------------------------------------------------- fixings


def screw_points():
    """Bosses for the screws from below (both versions): along the walls,
    clear of the keys, the plate edge (notched round them), the stack and
    the connector insert."""
    return [(7.0, 8.0), (7.0, 92.0),                  # left corners, clear of the screen module
            (78.0, 7.0), (76.0, 93.0),                # under the ramp / the deck left of row 1
            (165.0, 6.0), (165.0, 94.0),
            (255.0, 6.0), (255.0, 94.0),
            (ROW2_X[1] + 28.0, ROW_Y[2])]            # right vertex, merged into the wall


# bosses that stop short of the lid (they hang on the walls instead): the
# back-left one would otherwise run up through the screen module (x 9.4..60.6)
BOSS_TOP = {(7.0, 8.0): 24.5,       # ...and the front-left one under the grille
            (7.0, 92.0): 18.0}


def pillar_points():
    """Board supports on the bottom plate: the centre of every triangle of
    three neighbouring buttons (10.7 mm from each one's Hall sensor, clear
    of its parts on the back of the board), plus three under the interface.
    With all of them the board sags ~0.01 mm under a firm 3 N press (the
    PCB's mechanics check), against ~0.37 mm with one every third column."""
    ks = [(row, x, y) for _, row, x, y, _ in keys()]
    have = {(row, round(x, 3)) for row, x, _ in ks}
    pts = set()
    for row, x, y in ks:
        for other in (row - 1, row + 1):
            if other not in ROW_Y:
                continue
            # this key, its right-hand neighbour in the row, and the key
            # between them in the next row: a triangle of three real keys
            if (row, round(x + P, 3)) in have and (other, round(x + P / 2, 3)) in have:
                pts.add((round(x + P / 2, 3), round(y + (ROW_Y[other] - y) / 3, 3)))
    pts = sorted(pts, key=lambda p: (p[1], p[0]))
    pts += [(30.0, 60.0), (60.0, 75.0), (12.0, 70.0)]
    return pts

# ---------------------------------------------------------------- parts


def outer_body():
    """The solid outside shape (SPEC 4): box to the deck height, the
    raised interface block with its ramp, both ramp edges rounded R 5."""
    outline = box_contour()
    base = prism(outline, 0.0, Z_DECK)
    tall = prism(outline, 0.0, Z_IF + 5.0)
    raised = raised_region(RAMP_FOOT_OFF, Z_DECK, RAMP_TOP_OFF, 0.0).intersect(tall)
    body = base.fuse(raised).clean()
    return round_ramp(body)


def round_ramp(body):
    """R 5 on the ramp's bottom and top edges: the edges the ramp shares with
    the deck and with the interface top. One after the other (OCC can do
    each alone, not both at once)."""
    if RAMP_EDGE_R <= 0:
        return body

    def is_ramp(f):
        c = f.Center()
        if c.x > 130 or c.z < Z_DECK + 0.5 or abs(c.z - z_interface(c.y)) < 0.5:
            return False                  # far right, the deck, or the interface top
        n = f.normalAt(c)
        return 0.05 < abs(n.z) < 0.98     # sloping: not the walls, not the flat tops

    def edges(b, where):
        out = []
        for f in b.Faces():
            if not is_ramp(f):
                continue
            for e in f.Edges():
                c = e.Center()
                if c.x < 0.5 or c.y < 0.5 or c.y > WIDTH - 0.5:
                    continue              # the outer walls: no rounding there
                if where(c) and not any(e.isSame(o) for o in out):
                    out.append(e)
        return out
    for where in (lambda c: abs(c.z - Z_DECK) < 0.05,
                  lambda c: abs(c.z - z_interface(c.y)) < 0.3):
        try:
            nb = body.fillet(RAMP_EDGE_R, edges(body, where))
            assert nb.isValid(), "invalid result"
            body = nb
        except Exception as exc:  # keep going without that rounding, but say so
            print("ramp fillet failed (%s): edges left sharp" % exc)
    return body


def cavity(v):
    """The inside: walls v["wall"], lid v["top"] under the interface (the
    keyboard lid is LID_T, set by the plate), open at the bottom."""
    wall, top = v["wall"], v["top"]
    inner = contour_wp(box_contour()).offset2D(-wall).wires().val()
    inner_wp = lambda z0, z1: cq.Workplane("XY", origin=(0, 0, z0)).add(inner.translate(cq.Vector(0, 0, z0))).toPending().extrude(z1 - z0).val()
    low = inner_wp(-1.0, Z_PLATE_TOP)
    tall = inner_wp(-1.0, Z_IF)
    # the inside of the ramp: its foot (at the lid's underside) and top
    # edge pulled towards the interface by the wall thickness
    raised = raised_region(RAMP_FOOT_OFF + wall, Z_PLATE_TOP, RAMP_TOP_OFF + wall, top,
                           r_front=RAMP_FRONT_R - wall).intersect(tall)
    return low.fuse(raised).clean()


def grille_outline():
    x0, y0, x1, y1 = GRILLE_RECT
    return [((x0, y0), GRILLE_R), ((x1, y0), GRILLE_R), ((x1, y1), GRILLE_R_FR), ((x0, y1), GRILLE_R)]


def grille_holes():
    """Holes on a GRILLE_PITCH grid measured on the 13 deg surface (so a
    little closer in plan from back to front), centred in the outline."""
    poly = contour_points(grille_outline(), 0.3)
    x0, y0, x1, y1 = GRILLE_RECT
    r = GRILLE_D / 2
    px, py = GRILLE_PITCH, GRILLE_PITCH * COS_IF
    nx = int((x1 - x0 - 2 * (r + 0.8)) / px)
    ny = int((y1 - y0 - 2 * (r + 0.8)) / py)
    sx = (x0 + x1) / 2 - nx * px / 2
    sy = (y0 + y1) / 2 - ny * py / 2
    out = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            p = (sx + i * px, sy + j * py)
            if point_in_poly(p, poly) and dist_to_poly(p, poly) >= r + 0.8:
                out.append(p)
    return out


def rrect(x0, y0, x1, y1, r, z0, z1):
    return (cq.Workplane("XY", origin=(0, 0, z0)).center((x0 + x1) / 2, (y0 + y1) / 2)
            .rect(x1 - x0, y1 - y0).extrude(z1 - z0).edges("|Z").fillet(r).val())


def top_features(v):
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
    cuts.append(cyl(lx, ly, 0, 50, v.get("led_hole", LED_HOLE_D)))
    cuts += [cyl(x, y, 19.0, 50, GRILLE_D) for x, y in grille_holes()]     # through the lid only
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


def controls_top(v):
    """z of the controls board's top face in version v (the lid's underside
    over the parts' front edge, less 0.2, less the bodies' height)."""
    return z_interface(CONTROLS["body_front_y"], v["top"]) - 0.2 - CONTROLS["body_h"]


def controls_posts(v, body):
    return [cyl(x, y, controls_top(v), 60, POST_D).intersect(body) for x, y in CONTROLS["holes"]]


def bosses(v, body):
    """Screw columns: from the bottom plate up into the top, inside the
    wall line, trimmed to the outside shape."""
    out = []
    for x, y in screw_points():
        col = cyl(x, y, FLOOR_T, BOSS_TOP.get((x, y), 60), BOSS_D).intersect(body)
        out.append(col)
    return out


def shell(v):
    body = outer_body()
    s = body.cut(cavity(v))
    s = s.fuse(*bosses(v, body), *controls_posts(v, body)).clean()
    for c in rounded_opening_cutter():
        s = s.cut(c)
    # OCC sometimes splits a cut-away piece off as a second solid instead of
    # removing it: keep the shell itself
    s = sorted(s.Solids(), key=lambda x: x.Volume(), reverse=True)[0]
    cuts = [insert_cut(v)] + top_features(v)
    cuts += [cyl(x, y, FLOOR_T - 0.01, FLOOR_T + 9.0, PILOT_D) for x, y in screw_points()]
    cuts += [cyl(x, y, controls_top(v) - 0.01, controls_top(v) + POST_PILOT_DEPTH, POST_PILOT_D) for x, y in CONTROLS["holes"]]
    s = s.cut(fuse(cuts))
    # flush bottom plate sits inside the walls
    return s.clean()


def fundo(v, t=FLOOR_T):
    """Bottom plate, inside the walls, flush with their bottom edge."""
    inner = contour_wp(box_contour()).offset2D(-v["wall"] - FUNDO_CLR).wires().val()
    plate = cq.Workplane("XY").add(inner).toPending().extrude(t).val()
    adds = [cyl(x, y, t - 0.01, Z_PCB_BOT, SCREW_PILLAR_D if (x, y) in SCREW_PILLARS else PILLAR_D)
            for x, y in pillar_points()]
    plate = plate.fuse(*adds)
    cuts = []
    for x, y in SCREW_PILLARS:            # M2 from below, through the pillar and the board
        cuts.append(cyl(x, y, -1, Z_PCB_BOT + 1, M2_CLR_D))
        cuts.append(cyl(x, y, -1, M2_HEAD_DEPTH, M2_HEAD_D))
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
    """One oak block: same outside, thicker walls, a hole for the LED's
    light pipe."""
    return shell(VERSIONS["madeira"])


def light_pipe():
    """Madeira: stand-in for the bought 3 mm light pipe, flush with the top
    (for the renders and the fit check; not a part to make)."""
    lx, ly = LED_XY
    z1 = z_interface(ly)
    return cyl(lx, ly, z1 - LIGHT_PIPE_L, z1, LIGHT_PIPE_D)

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
    print("length %.2f mm" % (ROW2_X[1] + D_BTN / 2 + CLR_SIDE + BOX_OFF))
    for name, shape in build_all().items():
        export(shape, name)
    # the plate as a 2D drawing for laser/waterjet cutting (mm, top view)
    flat = cq.Workplane().add(to_file(switch_plate())).faces("<Z")
    cq.exporters.export(flat, os.path.join(OUT, "plate.dxf"))


if __name__ == "__main__":
    main()
