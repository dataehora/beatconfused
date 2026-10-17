"""eTuttino Pocket -- plan geometry of the case (stdlib only).

Shared by layout.py (the pocket.json contract), variants.py (the SPEC v2
D1 study of the left side) and, later, the CadQuery model (D2), which
should build its walls from `outline()` and its ramp from `opening()` /
`ramp_top()` so the plan and the solid agree.

Coordinates as in the eTuttino SPEC: x right from the case's leftmost
point, y from the back (0) to the player (100), z up from the table. mm.
The frame is left-handed; the CAD model mirrors on export as case.py does.

Every polygon here is convex: the keyboard opening and the ramp are convex
hulls of circles round the keys (the eTuttino's rule: 15 mm round each
button, 8.17 front/back, 12.7 more to the ramp's top edge), and the case
outline is the convex hull of the right end ("> " of the keyboard + 10.3)
and the left end of the chosen variant, with its convex corners rounded.
So inside/outside tests and distances stay simple and exact.
"""
import math

# ---- keyboard: the eTuttino's C-griff grid (case/case.py) ----
P = 18.5
D_BTN = 15.0
ROW_PITCH = P * math.cos(math.radians(30))           # 16.02
ROW_Y = {r: 50.0 + (2.5 - r) * ROW_PITCH for r in (1, 2, 3, 4)}
WIDTH = 100.0
CLR_SIDE = 15.0                                       # button edge -> opening, sides
BOX_OFF = 10.3                                        # opening -> outer wall (right, front, back)
R_OPEN = D_BTN / 2 + CLR_SIDE                         # 22.5
R_BOX = R_OPEN + BOX_OFF                              # 32.8
RAMP_FOOT_OFF = 4.0                                   # ramp foot = the chamfer's outer edge
RAMP_TOP_OFF = 12.7                                   # ramp top edge = opening + 12.7
R_RAMP = R_OPEN + RAMP_TOP_OFF                        # 35.2
CLR_FB = WIDTH / 2 - BOX_OFF - 1.5 * ROW_PITCH - D_BTN / 2   # 8.17
COS30, SIN30, TAN30 = math.cos(math.radians(30)), 0.5, math.tan(math.radians(30))

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
G3 = 55
POCKET_TOP = {1: "D#5", 2: "E5", 3: "D5", 4: "C5"}   # highest note per row (SPEC)
ETUTTINO_TOP = {1: "D#6", 2: "E6", 3: "D6", 4: "C6"}

# ---- heights (the eTuttino's stack-up, case/case.py; Seixo walls) ----
FLOOR_T = 2.0              # bottom plate
Z_PCB_BOT, Z_PCB_TOP = 6.5, 7.7
PLATE_T = 1.6
Z_PLATE_TOP = 12.8         # the lid's underside on the deck rests here
Z_PLATE_BOT = Z_PLATE_TOP - PLATE_T
PLATE_OVERLAP = 3.0        # plate edge = opening + 3
Z_DECK = 17.4
Z_KEY_TOP = 26.6
Z_IF = 33.0                # interface top, flat to the crease...
IF_CREASE_Y = 55.0
IF_CREASE_R = 10.0
IF_SLOPE = 13.0            # ...then down at 13 deg towards the player
WALL = 2.5                 # Seixo walls
TOP_T = 2.5                # Seixo lid over the interface
TAN_IF = math.tan(math.radians(IF_SLOPE))
COS_IF = math.cos(math.radians(IF_SLOPE))


def midi(name):
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTE_NAMES.index(pitch)


def note_name(m):
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


def keys_for(top, origin):
    """C-griff, n = semitones from G3. Row 4 repeats row 1 half a key right."""
    lim = {r: midi(t) - G3 for r, t in top.items()}
    out = []
    for n in range(0, max(lim.values()) + 1):
        if n % 3 == 2 and n <= lim[1]:
            out.append((n, 1, (n - 2) / 3))
        if n % 3 == 0 and n <= lim[2]:
            out.append((n, 2, n / 3 - 0.5))
        if n % 3 == 1 and n <= lim[3]:
            out.append((n, 3, (n - 1) / 3))
        if n % 3 == 2 and 2 <= n <= lim[4]:
            out.append((n, 4, (n - 2) / 3 + 0.5))
    keys = []
    for n, row, xp in out:
        m = G3 + n
        keys.append({
            "n": n, "midi": m, "note": note_name(m), "row": row, "xp": xp,
            "x": round(origin + xp * P, 2), "y": round(ROW_Y[row], 2),
            "sharp": (m % 12) in (1, 3, 6, 8, 10),
            "cf": (m % 12) in (0, 5),
        })
    return keys


def z_interface(y, dz=0.0):
    """Interface top at y (crease rounding ignored); dz = lid thickness gives its underside."""
    return min(Z_IF - dz, Z_IF - (y - IF_CREASE_Y) * TAN_IF - dz / COS_IF)


# ---- 2D helpers (convex polygons as lists of (x, y)) ----
def hull(points):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 1e-9:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 1e-9:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]          # counter-clockwise in a y-up frame


def circles(centres, r, y0=-1e9, y1=1e9, steps=96):
    pts = []
    for cx, cy in centres:
        for i in range(steps):
            a = 2 * math.pi * i / steps
            pts.append((cx + r * math.cos(a), min(y1, max(y0, cy + r * math.sin(a)))))
    return pts


def area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def inside(poly, p):
    x, y = p
    res = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            res = not res
    return res


def edge_dist(poly, p):
    """Distance from p to the polygon's boundary."""
    n = len(poly)
    return min(_seg_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n))


def depth(poly, p):
    """Signed: + distance to the boundary inside, - outside."""
    d = edge_dist(poly, p)
    return d if inside(poly, p) else -d


def _segs_cross(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) * o(a, b, d) < 0) and (o(c, d, a) * o(c, d, b) < 0)


def poly_gap(A, B):
    """Smallest distance between two polygons; 0 when they touch or overlap."""
    if any(inside(B, p) for p in A) or any(inside(A, p) for p in B):
        return 0.0
    na, nb = len(A), len(B)
    for i in range(na):
        for j in range(nb):
            if _segs_cross(A[i], A[(i + 1) % na], B[j], B[(j + 1) % nb]):
                return 0.0
    d1 = min(edge_dist(B, p) for p in A)
    d2 = min(edge_dist(A, p) for p in B)
    return min(d1, d2)


def clip_halfplane(poly, a, n, off=0.0):
    """Keep the part of poly where (p - a) . n >= off."""
    out = []
    m = len(poly)
    f = lambda p: (p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1] - off
    for i in range(m):
        p, q = poly[i], poly[(i + 1) % m]
        fp, fq = f(p), f(q)
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def erode(poly, r):
    """Inner parallel polygon of a convex polygon (every edge moved r inwards)."""
    poly = ccw(poly)
    out = list(poly)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        out = clip_halfplane(out, a, (-dy / L, dx / L), r)      # left of a->b is inside (ccw)
        if not out:
            return []
    return out


def round_corners(poly, r, steps=96):
    """Morphological opening of a convex polygon: every convex corner gets at least radius r."""
    core = erode(poly, r)
    return hull(circles(core, r, steps=steps)) if core else []


def offset(poly, d, steps=96):
    return hull(circles(poly, d, steps=steps))


def resample(poly, step):
    """The closed polygon's boundary as points about `step` apart."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    return out


def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rect(cx, cy, w, h, ang=0.0):
    """Rectangle w (along the angle) x h centred at (cx, cy), angle in degrees."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def local(cx, cy, ang, u0, v0, u1, v1):
    """Rectangle u0..u1, v0..v1 in a frame at (cx, cy) turned by ang (degrees)."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]


def circle_poly(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---- the case in plan ----
def opening(keys, extra=0.0):
    """Keyboard opening (eTuttino rule) grown by `extra`."""
    y_top = ROW_Y[4] - D_BTN / 2 - CLR_FB - extra
    y_bot = ROW_Y[1] + D_BTN / 2 + CLR_FB + extra
    return hull(circles([(k["x"], k["y"]) for k in keys], R_OPEN + extra, y_top, y_bot))


def ramp_top(keys):
    """The ramp's top edge (opening + 12.7), clipped to the 100 mm box."""
    return opening(keys, RAMP_TOP_OFF)


def right_end(keys):
    """The ">" end and the long walls: opening + 10.3 clamped to y 0..100 (v1 / eTuttino rule)."""
    return circles([(k["x"], k["y"]) for k in keys], R_BOX, 0.0, WIDTH)


def left_keys(keys):
    """The first key of rows 4, 2 and 1: they carry the "<" (all on 30 deg lines)."""
    first = {r: min((k for k in keys if k["row"] == r), key=lambda k: k["x"]) for r in (1, 2, 4)}
    return first[4], first[2], first[1]


# Left-side variants (SPEC v2 section 3). All three follow the keyboard's "<":
# their two left faces are the keyboard's 30 deg edges moved out by
#   R_RAMP + band   (band = interface width, perpendicular to the face).
#   nose:    radius at the tip of the "<" (None = concentric with the
#            ramp's own round tip: a constant-width interface, one big arc)
#   corner:  minimum radius of every other convex corner (left-back,
#            left-front, and the two right-hand ones)
#   bulge:   sagitta of each left face (0 = straight)
# Each band is the narrowest (1 mm steps) at which variants.py packs
# everything under the interface: what sets it is the Teensy + Audio Board
# stack with its 90 deg USB plug at the back-left, not the knobs (they
# would take ~44).
VARIANTS = {
    "A": {"name": "Chevron", "band": 51.0, "nose": 30.0, "corner": 18.0, "bulge": 0.0,
          "tagline": "\"<\" de faces retas, ponta R 30, quinas R 18"},
    "B": {"name": "Seixo", "band": 54.0, "nose": None, "corner": 24.0, "bulge": 0.0,
          "tagline": "curva contínua: o \"<\" vira um arco único, largura constante"},
    "C": {"name": "Arco", "band": 47.0, "nose": 24.0, "corner": 22.0, "bulge": 6.0,
          "tagline": "\"<\" de faces levemente curvas, ponta e quinas R 22-24"},
}


def left_end(keys, v):
    """Points of the variant's left end (sharp at y = 0 and 100; round_corners() does those)."""
    k4, k2, k1 = left_keys(keys)
    D = R_RAMP + v["band"]
    x2, y2 = k2["x"], k2["y"]
    V = (x2 - D / COS30, y2)                       # the sharp tip of the "<"
    B0 = (V[0] + y2 * TAN30, 0.0)                  # back face meets y = 0
    F0 = (V[0] + (WIDTH - y2) * TAN30, WIDTH)      # front face meets y = 100
    nose = D if v["nose"] is None else v["nose"]
    if v["bulge"] <= 0:
        c = (V[0] + nose / math.sin(math.radians(60)), y2)     # on the tip's bisector
        tip = arc(c[0], c[1], nose, math.radians(210), math.radians(150), 48)
        return [(x, min(WIDTH, max(0.0, y))) for x, y in [B0] + tip + [F0]]   # a big tip arc can pass y = 0 / 100

    # bulging faces: a circular arc through each face's two ends, sagitta `bulge`
    def bow(p, q, s, n=40):
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L       # left of p->q
        if nx > 0:                                            # we want the outward (-x) side
            nx, ny = -nx, -ny
        R = (L * L / 4 + s * s) / (2 * s)
        cx, cy = mx - nx * (R - s), my - ny * (R - s)
        a0 = math.atan2(p[1] - cy, p[0] - cx)
        a1 = math.atan2(q[1] - cy, q[0] - cx)
        d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        return [(cx + R * math.cos(a0 + d * i / n), cy + R * math.sin(a0 + d * i / n)) for i in range(n + 1)]
    return bow(B0, V, v["bulge"]) + bow(V, F0, v["bulge"])[1:]


def outline(keys, v):
    """The case in plan for variant v: convex, every corner rounded."""
    pts = right_end(keys) + left_end(keys, v)
    poly = hull(pts)
    if v["bulge"] > 0 and v["nose"]:
        poly = round_corners(poly, v["nose"])
    poly = round_corners(poly, v["corner"])
    return ccw(poly)


def place(v, top=POCKET_TOP):
    """Keys and outline for variant v with the case's leftmost point at x = 0."""
    keys = keys_for(top, 100.0)
    x_min = min(x for x, _ in outline(keys, v))
    origin = round(100.0 - x_min, 2)
    keys = keys_for(top, origin)
    return origin, keys, outline(keys, v)


def etuttino_outline(origin=104.0):
    """The eTuttino's plan (v1 hull rule: straight left face at x = origin - 104, R 16)."""
    keys = keys_for(ETUTTINO_TOP, origin)
    x0 = origin - 104.0
    pts = right_end(keys) + [(x0, 0.0), (x0, WIDTH)]
    return keys, ccw(round_corners(hull(pts), 16.0))
