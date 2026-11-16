"""eTutti Student V2: the geometry shared by the board and the case (SPEC v1).

    python etutti/hardware/student_v02/geometria.py        (writes layout.json)

Plain Python. Frame of the SPEC: origin at the case's back-left corner, x right (0-252),
y towards the player (0-100), z = 0 at the board's top. KiCad uses the same x, y.

The keyboard is the Student V1's: 28 keys, 18.5 mm along a row, 16.02 mm between rows.
Everything round it is an offset of the convex hull of the key centres:

    12.5 mm   the well's wall (5 mm from a 15 mm button)
    15.5 mm   the well's edge on the lid's top (canvas)
    18.5 mm   the 10 M2 screws of the keyboard grid
    21.5 mm   the grid's edge (6 mm past the opening, under the lid)
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CASE = (252.0, 100.0)
CASE_R = 9.0
Z_BASE, Z_SPLIT, Z_TOP = -10.1, -4.0, 18.2
WALL = 2.0
BOARD = (2.5, 2.5, 249.0, 97.5)       # the V1 board's edges, kept
BOARD_R = 6.5                         # V1 had 5.0: 6.5 keeps 0.5 mm from the case's R 7 inner corner
T_PCB = 1.2

PITCH, ROW_PITCH = 18.5, 16.02
ROWS = [  # (row, y, first x, keys); row 1 is the front one
    (1, 74.03, 98.45, 7), (2, 58.01, 89.2, 8), (3, 41.99, 98.45, 7), (4, 25.97, 107.7, 6)]
KEYS = [(r, round(x0 + i * PITCH, 3), y) for r, y, x0, n in ROWS for i in range(n)]

WELL_WALL, WELL_EDGE, GRID_SCREW, GRID_EDGE = 12.5, 15.5, 18.5, 21.5
N_GRID_SCREWS = 10

# interface (SPEC section 4-6)
OLED_WINDOW = (22.0, 14.5, 52.0, 29.5)
KNOBS = [(28.0, 44.5), (46.0, 44.5)]
SPEAKER = (37.0, 73.1)
SPEAKER_D = 28.0
SPEAKER_SCREWS = [(37.0, 73.1 - 18.6), (37.0, 73.1 + 18.6)]
GRILLE = {"x0": 21.0, "x1": 53.0, "y0": 61.5, "pitch": 3.6, "slot": 1.6, "n": 7}
USB_Y, OUT_Y, IN_Y = 16.0, 36.0, 60.0
USB_Z, JACK_Z = 1.7, 2.8


def hull(points):
    pts = sorted(set(points))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(reversed(pts))


HULL = hull([(x, y) for _, x, y in KEYS])       # counter-clockwise in a y-up frame


def offset(d, step=0.25):
    """The hull grown by d: a closed list of points (straight sides and round corners), about
    `step` mm apart, starting above the first key of row 4 and going towards -x (as the canvas)."""
    n = len(HULL)
    area = sum(HULL[i][0] * HULL[(i + 1) % n][1] - HULL[(i + 1) % n][0] * HULL[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    pts = []
    for i in range(n):
        a, b, c = HULL[i - 1], HULL[i], HULL[(i + 1) % n]

        def normal(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            return sgn * dy / L, -sgn * dx / L
        n1, n2 = normal(a, b), normal(b, c)
        a1, a2 = math.atan2(n1[1], n1[0]), math.atan2(n2[1], n2[0])
        da = (a2 - a1) * sgn
        while da < 0:
            da += 2 * math.pi
        k = max(2, int(da * d / step))
        for j in range(k + 1):
            ang = a1 + sgn * da * j / k
            pts.append((b[0] + d * math.cos(ang), b[1] + d * math.sin(ang)))
        # the straight side to the next corner
        L = math.hypot(c[0] - b[0], c[1] - b[1])
        m = max(1, int(L / step))
        for j in range(1, m):
            t = j / m
            pts.append((b[0] + (c[0] - b[0]) * t + d * n2[0], b[1] + (c[1] - b[1]) * t + d * n2[1]))
    # start at the point above the first key of row 4
    x4 = ROWS[3][2]
    y4 = ROWS[3][1] - d
    i0 = min(range(len(pts)), key=lambda i: (pts[i][0] - x4) ** 2 + (pts[i][1] - y4) ** 2)
    pts = pts[i0:] + pts[:i0]
    if pts[1][0] > pts[0][0]:
        pts = [pts[0]] + pts[:0:-1]
    return pts


def along(pts, n, shifts=None):
    """n points equally spaced along the closed line pts, from its first point; shifts moves
    single points along the line (mm)."""
    seg = [math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0], pts[(i + 1) % len(pts)][1] - pts[i][1])
           for i in range(len(pts))]
    total = sum(seg)
    out = []
    for k in range(n):
        s = (k * total / n + (shifts or {}).get(k, 0.0)) % total
        i = 0
        while s > seg[i]:
            s -= seg[i]
            i += 1
        a, b = pts[i], pts[(i + 1) % len(pts)]
        t = s / seg[i] if seg[i] else 0
        out.append((round(a[0] + (b[0] - a[0]) * t, 2), round(a[1] + (b[1] - a[1]) * t, 2)))
    return out


def inside(poly, p):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c


# Screws of the keyboard grid: equally spaced along the 18.5 mm line, as on the canvas. A screw is
# moved along the line only where the V1 board has a part or a track that cannot move (pcb/
# build_board.py checks every one and says which); the moves are listed here.
GRID_SCREW_SHIFT = {}
if os.path.exists(os.path.join(HERE, "pcb", "grid_screw_shift.json")):
    GRID_SCREW_SHIFT = {int(k): v for k, v in
                        json.load(open(os.path.join(HERE, "pcb", "grid_screw_shift.json"))).items()}


def grid_screws():
    return along(offset(GRID_SCREW), N_GRID_SCREWS, GRID_SCREW_SHIFT)


def main():
    out = {
        "caixa": {"x": CASE[0], "y": CASE[1], "raio": CASE_R, "z_base": Z_BASE, "z_divisa": Z_SPLIT, "z_tampo": Z_TOP},
        "placa": {"contorno": list(BOARD), "raio": BOARD_R, "espessura": T_PCB},
        "teclas": [{"fileira": r, "x": x, "y": y} for r, x, y in KEYS],
        "casco": [list(p) for p in HULL],
        "poco_parede": [[round(v, 3) for v in p] for p in offset(WELL_WALL, 1.0)],
        "poco_borda": [[round(v, 3) for v in p] for p in offset(WELL_EDGE, 1.0)],
        "grade_contorno": [[round(v, 3) for v in p] for p in offset(GRID_EDGE, 1.0)],
        "grade_parafusos": [list(p) for p in grid_screws()],
        "grade_parafusos_deslocados_mm": GRID_SCREW_SHIFT,
    }
    json.dump(out, open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8"), indent=1)
    print("casco:", HULL)
    print("parafusos da grade:", out["grade_parafusos"])


if __name__ == "__main__":
    main()
