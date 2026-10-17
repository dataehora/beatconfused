"""How far the Pocket's main board bends when a key is pressed, on the case's
pillars (SPEC v3: <= 0.05 mm at 3 N, as the eTuttino):

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/mechanics.py

The eTuttino's method (etutti/hardware/mechanics.py): a grillage of the bare
FR-4 board (beam elements on a square mesh, no twisting stiffness, the
switch plate's help ignored, so the real board bends less), here on the
board's real outline from out/pcb_envelope.json instead of its bounding box,
with scipy's sparse solver. The board rests on the bottom plate's pillars
(supports + mounting holes) and is pinned by the stack's 28 header legs.
Writes out/board_sag.json.
"""
import json
import math
import os
import sys

import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
E_FR4 = 18000.0          # N/mm^2
PRESS_N = 3.0
GRID_H = 2.0
TARGET_MM = 0.05


def inside(poly, x, y):
    res = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            res = not res
    return res


def solve(outline, supports, loads, t, h=GRID_H):
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    x0, y0 = min(xs), min(ys)
    nx = int(math.ceil((max(xs) - x0) / h)) + 1
    ny = int(math.ceil((max(ys) - y0) / h)) + 1
    idx = -np.ones((ny, nx), dtype=int)
    n = 0
    for j in range(ny):
        for i in range(nx):
            if inside(outline, x0 + i * h, y0 + j * h):
                idx[j, i] = n
                n += 1
    K = lil_matrix((3 * n, 3 * n))
    EI = E_FR4 * h * t ** 3 / 12

    def beam(a, b, rot):
        k = EI / h ** 3 * np.array([[12, 6 * h, -12, 6 * h], [6 * h, 4 * h * h, -6 * h, 2 * h * h],
                                    [-12, -6 * h, 12, -6 * h], [6 * h, 2 * h * h, -6 * h, 4 * h * h]])
        d = [3 * a, 3 * a + rot, 3 * b, 3 * b + rot]
        for p in range(4):
            for q in range(4):
                K[d[p], d[q]] += k[p, q]
    for j in range(ny):
        for i in range(nx):
            a = idx[j, i]
            if a < 0:
                continue
            if i + 1 < nx and idx[j, i + 1] >= 0:
                beam(a, idx[j, i + 1], 1)
            if j + 1 < ny and idx[j + 1, i] >= 0:
                beam(a, idx[j + 1, i], 2)
    # rotations of nodes with no beam in a direction are free and singular: pin them
    K = K.tocsr()
    diag = K.diagonal()

    def nearest(x, y):
        i = int(round((x - x0) / h))
        j = int(round((y - y0) / h))
        best = None
        for dj in range(-2, 3):
            for di in range(-2, 3):
                jj, ii = j + dj, i + di
                if 0 <= jj < ny and 0 <= ii < nx and idx[jj, ii] >= 0:
                    d = math.hypot(x0 + ii * h - x, y0 + jj * h - y)
                    if best is None or d < best[0]:
                        best = (d, idx[jj, ii])
        return best[1]
    fixed = set(3 * nearest(x, y) for x, y in supports)
    fixed |= set(int(d) for d in np.where(diag == 0)[0])
    free = np.array(sorted(set(range(3 * n)) - fixed))
    pos = -np.ones(3 * n, dtype=int)
    pos[free] = np.arange(len(free))
    Kf = K[free][:, free].tocsc()
    out = []
    for x, y in loads:
        f = np.zeros(len(free))
        d = 3 * nearest(x, y)
        if pos[d] < 0:
            out.append(0.0)
            continue
        f[pos[d]] = PRESS_N
        u = spsolve(Kf, f)
        out.append(float(u[pos[d]]))
    return out


def main():
    with open(os.path.join(OUT, "pcb_envelope.json"), encoding="utf-8") as f:
        env = json.load(f)
    sys.path.insert(0, HERE)
    import case as C
    outline = [tuple(p) for p in env["outline"]]
    pillars = [(s["x"], s["y"]) for s in env["supports"]]
    legs = C.stack_pin_centres()
    keys = env["keys"]
    loads = [(k["x"], k["y"]) for k in keys]
    t = env["pcb_thickness"]
    sag = solve(outline, pillars + legs, loads, t)
    bare = solve(outline, [(m["x"], m["y"]) for m in env["mounting_holes"]] + legs, loads, t)
    worst = max(range(len(keys)), key=lambda i: sag[i])
    res = {
        "press_n": PRESS_N, "pcb_thickness": t, "grid_mm": GRID_H,
        "model": "grillage of the bare %.1f mm FR-4 board on its real outline, %.0f mm mesh, E = %.0f MPa, "
                 "no twisting stiffness, plate ignored" % (t, GRID_H, E_FR4),
        "pillars": len(pillars), "stack_legs": len(legs),
        "max_mm": round(max(sag), 4), "mean_mm": round(sum(sag) / len(sag), 4),
        "worst_key": "%s row %d" % (keys[worst]["note"], keys[worst]["row"]),
        "mounting_holes_only_max_mm": round(max(bare), 3),
        "per_key_mm": {"%s r%d" % (k["note"], k["row"]): round(s, 4) for k, s in zip(keys, sag)},
        "target_mm": TARGET_MM, "ok": max(sag) <= TARGET_MM,
    }
    with open(os.path.join(OUT, "board_sag.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("%d pillars + %d legs: sag under %.0f N %.4f mm at worst (%s), mean %.4f; holes only %.3f -- %s" % (
        len(pillars), len(legs), PRESS_N, res["max_mm"], res["worst_key"], res["mean_mm"],
        res["mounting_holes_only_max_mm"], "OK" if res["ok"] else "ABOVE %.2f" % TARGET_MM))


if __name__ == "__main__":
    main()
