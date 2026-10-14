"""How far the eTuttino board bends when a key is pressed (run with
KiCad's Python, which has numpy):

    "C:/Program Files/KiCad/10.0/bin/python.exe" mechanics.py

checks the v7 board on the bottom plate's pillars (case/pcb_envelope.json,
generate.SUPPORTS) and writes build/etuttino_supports.json.

write_supports() / choose_pillars() are the #78 board's: they picked
pillar spots for its rectangular board and old case and are kept for the
model only; on the v7 board the case decides the pillars (one at the
centre of every three-key triangle) and this file checks them.

The switches are plate-mounted but sit right on the PCB, so a key press
ends up pushing the 1.2 mm board down under that key. Screwed only at its
mounting holes, which are all near the edges, the middle of a 267 mm board
would sag noticeably. So the case's bottom tray has, besides a boss under
every mounting hole, small round pillars that touch the back of the board
where it carries nothing but solder-masked traces (no pads, no vias, no
parts), on a grid along the gaps between key rows.

The deflection is estimated with a grillage model of the bare 1.2 mm PCB
(beam elements on a 4 mm grid, no twisting stiffness, the plate's help
ignored), so the real board bends less than the numbers say.

Writes build/etuttino_supports.json:
  pillars   [[x, y], ...]          board mm, pillar centres
  bosses    [[x, y, kind], ...]    under the mounting holes
  deflection                       max sag per key press, with and without pillars
"""
import json
import math
import os

import numpy as np

import generate as G

E_FR4 = 18000.0          # N/mm^2, FR-4 flexural modulus
PRESS_N = 3.0            # a firm press, bottomed out (the switch needs ~0.4 N)
PILLAR_D = 4.0           # pillar tip diameter
PILLAR_CLEAR = 0.6       # pillar edge to the nearest pad / via / part
PILLAR_PITCH = 33.0      # target spacing along each line
GRID_H = 4.0             # grillage mesh size (mm)
TARGET_MM = 0.05         # what we aim for under one firm press

SUPPORTS_PATH = os.path.join(G.BUILD, "etuttino_supports.json")


def obstacles(board_path):
    """(x0, y0, x1, y1) boxes on the back a pillar must not touch: every
    pad on the back copper or through the board, every via, every part on
    the back (its pads' box grown by 0.8 mm for the body)."""
    import pcbnew
    b = pcbnew.LoadBoard(board_path)
    mmv = pcbnew.ToMM
    out = []
    for fp in b.GetFootprints():
        boxes = []
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                bb = p.GetBoundingBox()
                boxes.append((mmv(bb.GetLeft()), mmv(bb.GetTop()), mmv(bb.GetRight()), mmv(bb.GetBottom())))
        out += boxes
        if fp.IsFlipped() and boxes:
            out.append((min(b[0] for b in boxes) - 0.8, min(b[1] for b in boxes) - 0.8,
                        max(b[2] for b in boxes) + 0.8, max(b[3] for b in boxes) + 0.8))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            x, y = mmv(t.GetPosition().x), mmv(t.GetPosition().y)
            r = mmv(t.GetWidth(pcbnew.F_Cu)) / 2
            out.append((x - r, y - r, x + r, y + r))
    return out


def clearance(x, y, boxes):
    d = 1e9
    for x0, y0, x1, y1 in boxes:
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        d = min(d, math.hypot(dx, dy))
    return d


def choose_pillars(boxes):
    """Pillars along the three gaps between key rows and along the front
    and back margins, about PILLAR_PITCH apart, each nudged to the nearest
    spot with room for it. None under the Teensy stack (its 28 legs hold
    it) or next to a mounting hole (that has a boss)."""
    need = PILLAR_D / 2 + PILLAR_CLEAR
    holes = G.mounting_holes()
    lines = [G.GRID_Y0 + k * G.U for k in (1, 2, 3)] + [G.PCB_H - 3.0, G.GRID_Y0 / 2]
    x_lo, x_hi = 8.0, G.PCB_W - 8.0
    picks = []
    for y in lines:
        n = max(2, int(round((x_hi - x_lo) / PILLAR_PITCH)) + 1)
        for i in range(n):
            x = x_lo + (x_hi - x_lo) * i / (n - 1)
            best = None
            for dx in np.arange(-9.0, 9.01, 0.5):
                for dy in np.arange(-3.0, 3.01, 0.5):
                    px, py = x + dx, y + dy
                    if not (need <= px <= G.PCB_W - need and need <= py <= G.PCB_H - need):
                        continue
                    if any(math.hypot(px - hx, py - hy) < 8.0 for hx, hy in holes):
                        continue
                    if any(math.hypot(px - qx, py - qy) < 12.0 for qx, qy in picks):
                        continue
                    zx0, zy0, zx1, zy1 = G.STACK_ZONE
                    if zx0 - 2 < px < zx1 + 2 and zy0 - 2 < py < zy1 + 2:
                        continue
                    if clearance(px, py, boxes) < need:
                        continue
                    cost = math.hypot(dx, dy * 2)
                    if best is None or cost < best[0]:
                        best = (cost, round(float(px), 2), round(float(py), 2))
            if best:
                picks.append((best[1], best[2]))
    return picks


def deflections(supports, loads, t=G.PCB_THICKNESS):
    """Sag (mm) at each load point for PRESS_N there, alone, on a grillage
    of the board resting on `supports` (points pinned at w = 0)."""
    nx = int(math.ceil(G.PCB_W / GRID_H)) + 1
    ny = int(math.ceil(G.PCB_H / GRID_H)) + 1
    hx = G.PCB_W / (nx - 1)
    hy = G.PCB_H / (ny - 1)
    N = nx * ny
    K = np.zeros((3 * N, 3 * N))
    node = lambda i, j: j * nx + i

    def beam(a, b, L, EI, rot):
        k = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L],
                                    [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                    [-12, -6 * L, 12, -6 * L],
                                    [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        dofs = [3 * a, 3 * a + rot, 3 * b, 3 * b + rot]
        K[np.ix_(dofs, dofs)] += k

    for j in range(ny):
        for i in range(nx):
            # strip widths: half a cell at the edges
            wy = hy * (0.5 if j in (0, ny - 1) else 1.0)
            wx = hx * (0.5 if i in (0, nx - 1) else 1.0)
            if i + 1 < nx:
                beam(node(i, j), node(i + 1, j), hx, E_FR4 * wy * t ** 3 / 12, 1)
            if j + 1 < ny:
                beam(node(i, j), node(i, j + 1), hy, E_FR4 * wx * t ** 3 / 12, 2)
    nearest = lambda x, y: node(int(round(x / hx)), int(round(y / hy)))
    fixed = sorted({3 * nearest(x, y) for x, y in supports})
    free = np.setdiff1d(np.arange(3 * N), fixed)
    Kf = K[np.ix_(free, free)]
    pos = {d: n for n, d in enumerate(free)}
    F = np.zeros((len(free), len(loads)))
    rows = []
    for c, (x, y) in enumerate(loads):
        d = 3 * nearest(x, y)
        rows.append(pos[d])
        F[pos[d], c] = PRESS_N
    U = np.linalg.solve(Kf, F)
    return [float(U[r, c]) for c, r in enumerate(rows)]


def write_supports(board_path):
    boxes = obstacles(board_path)
    pillars = choose_pillars(boxes)
    holes = G.mounting_holes()
    ks = G.keys()
    loads = [(k["cx"], k["cy"]) for k in ks]
    # The 28 stacking-header legs pin the board under the stack too.
    stack = [(p[3], p[4]) for p in G.stack_pins()]
    bare = deflections(holes + stack, loads)
    cased = deflections(holes + stack + pillars, loads)
    worst = max(range(len(ks)), key=lambda i: cased[i])
    worst_bare = max(range(len(ks)), key=lambda i: bare[i])
    n_plate = sum(1 for h in holes if G.in_plate(*h))
    result = {
        "pillars": [list(p) for p in pillars],
        "bosses": [[x, y, "plate" if G.in_plate(x, y) else "pcb"] for x, y in holes],
        "pillar_d": PILLAR_D,
        "deflection": {
            "press_n": PRESS_N,
            "model": "grillage of the bare 1.2 mm FR-4 PCB, %.0f mm mesh, E = %.0f MPa, no twisting stiffness, plate ignored" % (GRID_H, E_FR4),
            "holes_only_max_mm": round(max(bare), 3),
            "holes_only_worst_key": G.note_name(ks[worst_bare]["note"]) + " row %d" % (ks[worst_bare]["row"] + 1),
            "with_case_max_mm": round(max(cased), 3),
            "with_case_mean_mm": round(sum(cased) / len(cased), 3),
            "with_case_worst_key": G.note_name(ks[worst]["note"]) + " row %d" % (ks[worst]["row"] + 1),
            "per_key_mm": {k["ref"]: round(d, 4) for k, d in zip(ks, cased)},
        },
    }
    os.makedirs(G.BUILD, exist_ok=True)
    with open(SUPPORTS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    d = result["deflection"]
    print("case supports: %d pillars + %d bosses (%d under the plate)" % (len(pillars), len(holes), n_plate))
    print("board sag under a %.0f N press: %.3f mm on the mounting holes alone (worst %s), "
          "%.3f mm in the case (worst %s, mean %.3f)" % (
              PRESS_N, d["holes_only_max_mm"], d["holes_only_worst_key"],
              d["with_case_max_mm"], d["with_case_worst_key"], d["with_case_mean_mm"]))
    if d["with_case_max_mm"] > TARGET_MM:
        print("  WARNING: above the %.2f mm target" % TARGET_MM)
    return result


def check_case_supports():
    """The v7 board on the case's pillars (plus the stack's 28 header legs):
    sag per key under PRESS_N."""
    ks = G.keys()
    loads = [(k["cx"], k["cy"]) for k in ks]
    stack = [(p[3], p[4]) for p in G.stack_pins()]
    pillars = [(x, y) for x, y, _ in G.SUPPORTS]
    sag = deflections(pillars + stack, loads)
    worst = max(range(len(ks)), key=lambda i: sag[i])
    result = {
        "pillars": [list(p) for p in pillars],
        "deflection": {
            "press_n": PRESS_N,
            "model": "grillage of the bare %.1f mm FR-4 board's bounding box, %.0f mm mesh, E = %.0f MPa, no twisting stiffness, plate ignored" % (G.PCB_THICKNESS, GRID_H, E_FR4),
            "max_mm": round(max(sag), 3),
            "mean_mm": round(sum(sag) / len(sag), 3),
            "worst_key": G.note_name(ks[worst]["note"]) + " row %d" % (ks[worst]["row"] + 1),
            "per_key_mm": {k["ref"]: round(d, 4) for k, d in zip(ks, sag)},
        },
    }
    os.makedirs(G.BUILD, exist_ok=True)
    with open(SUPPORTS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    d = result["deflection"]
    print("%d pillars: board sag under a %.0f N press %.3f mm at worst (%s), %.3f mean%s" % (
        len(pillars), PRESS_N, d["max_mm"], d["worst_key"], d["mean_mm"],
        "" if d["max_mm"] <= TARGET_MM else "  -- ABOVE the %.2f mm target" % TARGET_MM))
    return result


if __name__ == "__main__":
    check_case_supports()
