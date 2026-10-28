"""How far the Viaggio J1 board bends under a key press (KiCad's Python, which has numpy):

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/mechanics.py

A copy of the eTuttino's etutti/hardware/mechanics.py (left untouched), adapted to the Viaggio
J1 board (SPEC v2.4, step M3):
  - geometry read from kicad/viaggio_micromod.kicad_pcb: the board rectangle (x 2.5-249,
    y 2.5-97.5, 1.2 mm), the 28 keys (SW1-SW28 centres) and the 8 M2 holes H1-H8;
  - the same grillage model (beam elements on a 4 mm grid, no twisting stiffness, FR-4
    E = 18 GPa, the 1.6 mm plate ignored, so the real board bends less), 3 N at each key centre,
    alone; supports pinned at the M2 holes (the case's screws);
  - when the 8 holes are not enough, it proposes case pillars (Ø4 tips, as the eTuttino's),
    one at a time, at the free spot on the back nearest the worst key, until every key is
    <= 0.05 mm. A spot is free when the pillar edge is >= 0.6 mm from every back-side pad,
    through-hole pad, via and back-side part body (the eTuttino's rule), off the M2 rings and
    off the MicroMod card area.

Writes the result into m3.json ("flexao") and build/m3_flexao.png; exits non-zero only on an
error (a board that needs pillars is a result, not an error).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "kicad", "viaggio_micromod.kicad_pcb")
BUILD = os.path.join(HERE, "build")
MANIFEST = os.path.join(HERE, "m3.json")

E_FR4 = 18000.0          # N/mm^2, FR-4 flexural modulus
PRESS_N = 3.0            # a firm press, bottomed out
PILLAR_D = 4.0           # pillar tip diameter
PILLAR_CLEAR = 0.6       # pillar edge to the nearest pad / via / part
GRID_H = 4.0             # grillage mesh size (mm)
TARGET_MM = 0.05         # SPEC v2.4: <= 0.05 mm at 3 N per key
THICKNESS = 1.2
X0, Y0, X1, Y1 = 2.5, 2.5, 249.0, 97.5      # board rectangle (KiCad frame)
CARD = (29.0, 6.0, 50.5, 30.0)              # MicroMod card + socket area on the back (no pillar)


def board_geometry():
    import pcbnew
    b = pcbnew.LoadBoard(BOARD)
    mm = pcbnew.ToMM
    keys, holes = [], []
    for fp in b.GetFootprints():
        r = fp.GetReference()
        p = (mm(fp.GetPosition().x), mm(fp.GetPosition().y))
        if r.startswith("SW") and "Gateron" in fp.GetFPIDAsString():
            keys.append((r, p[0], p[1]))
        if r.startswith("H") and "MountingHole" in fp.GetFPIDAsString():
            holes.append((r, p[0], p[1]))
    keys.sort(key=lambda k: int(k[0][2:]))
    holes.sort()
    return b, keys, holes


def obstacles(b):
    """(x0, y0, x1, y1) boxes on the back a pillar must not touch (eTuttino rule)."""
    import pcbnew
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
            out.append((min(q[0] for q in boxes) - 0.8, min(q[1] for q in boxes) - 0.8,
                        max(q[2] for q in boxes) + 0.8, max(q[3] for q in boxes) + 0.8))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            x, y = mmv(t.GetPosition().x), mmv(t.GetPosition().y)
            r = mmv(t.GetWidth(pcbnew.F_Cu)) / 2
            out.append((x - r, y - r, x + r, y + r))
    return np.array(out)


def clearance(x, y, boxes):
    dx = np.maximum(np.maximum(boxes[:, 0] - x, 0.0), x - boxes[:, 2])
    dy = np.maximum(np.maximum(boxes[:, 1] - y, 0.0), y - boxes[:, 3])
    return float(np.min(np.hypot(dx, dy)))


class Grillage:
    """The eTuttino's deflections() on the Viaggio rectangle, with the stiffness matrix built once
    and a solve per support set."""
    def __init__(self, t=THICKNESS):
        W, H = X1 - X0, Y1 - Y0
        self.nx = nx = int(math.ceil(W / GRID_H)) + 1
        self.ny = ny = int(math.ceil(H / GRID_H)) + 1
        self.hx, self.hy = W / (nx - 1), H / (ny - 1)
        N = nx * ny
        K = np.zeros((3 * N, 3 * N))

        def beam(a, b_, L, EI, rot):
            k = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L],
                                        [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                        [-12, -6 * L, 12, -6 * L],
                                        [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
            dofs = [3 * a, 3 * a + rot, 3 * b_, 3 * b_ + rot]
            K[np.ix_(dofs, dofs)] += k

        for j in range(ny):
            for i in range(nx):
                wy = self.hy * (0.5 if j in (0, ny - 1) else 1.0)
                wx = self.hx * (0.5 if i in (0, nx - 1) else 1.0)
                if i + 1 < nx:
                    beam(self.node(i, j), self.node(i + 1, j), self.hx, E_FR4 * wy * t ** 3 / 12, 1)
                if j + 1 < ny:
                    beam(self.node(i, j), self.node(i, j + 1), self.hy, E_FR4 * wx * t ** 3 / 12, 2)
        self.K, self.N = K, N

    def node(self, i, j):
        return j * self.nx + i

    def nearest(self, x, y):
        return self.node(int(round((x - X0) / self.hx)), int(round((y - Y0) / self.hy)))

    def sag(self, supports, loads):
        fixed = sorted({3 * self.nearest(x, y) for x, y in supports})
        free = np.setdiff1d(np.arange(3 * self.N), fixed)
        Kf = self.K[np.ix_(free, free)]
        pos = {d: n for n, d in enumerate(free)}
        F = np.zeros((len(free), len(loads)))
        rows = []
        for c, (x, y) in enumerate(loads):
            d = 3 * self.nearest(x, y)
            rows.append(pos[d])
            F[pos[d], c] = PRESS_N
        U = np.linalg.solve(Kf, F)
        return [float(U[r, c]) for c, r in enumerate(rows)]


def free_spots(boxes, holes, step=1.0):
    need = PILLAR_D / 2 + PILLAR_CLEAR
    out = []
    for x in np.arange(X0 + 3.0, X1 - 3.0 + 1e-9, step):
        for y in np.arange(Y0 + 3.0, Y1 - 3.0 + 1e-9, step):
            if any(math.hypot(x - hx, y - hy) < 1.75 + PILLAR_D / 2 + 0.5 for _r, hx, hy in holes):
                continue          # 3.5 mm copper-free ring of the M2 hole: the boss is there
            if CARD[0] <= x <= CARD[2] and CARD[1] <= y <= CARD[3]:
                continue
            if clearance(x, y, boxes) >= need:
                out.append((round(float(x), 2), round(float(y), 2)))
    return out


def picture(keys, holes, pillars, sag_holes, sag_final, spots, out):
    from PIL import Image, ImageDraw, ImageFont
    S = 5.0
    W, H = int((X1 - X0 + 10) * S), int((Y1 - Y0 + 10) * S) + 40
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arial.ttf", 13)
        fs = ImageFont.truetype("arial.ttf", 10)
    except OSError:
        f = fs = ImageFont.load_default()

    def P(x, y):
        return ((x - X0 + 5) * S, (y - Y0 + 5) * S + 40)
    d.text((6, 4), "Viaggio J1 - flexao a 3 N por tecla (grelha 4 mm, placa 1,2 mm, plate ignorado), vista de cima. "
           "Cinza: lugares livres no verso para pilar Ø4. Azul: furos M2. Vermelho: pilares propostos.", fill=(0, 0, 0), font=f)
    d.text((6, 20), "Numero em cada tecla: flexao em um centesimo de mm, so com os 8 furos / com os pilares.",
           fill=(0, 0, 0), font=f)
    a, e = P(X0, Y0), P(X1, Y1)
    d.rectangle([a, e], outline=(0, 0, 0), width=2)
    for x, y in spots:
        q = P(x, y)
        d.point(q, fill=(190, 190, 190))
    for r, x, y in holes:
        q = P(x, y)
        d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], outline=(0, 90, 200), width=3)
        d.text((q[0] + 10, q[1] - 6), r, fill=(0, 90, 200), font=fs)
    for k, (r, x, y) in enumerate(keys):
        q = P(x, y)
        c = (0, 140, 0) if sag_final[k] <= TARGET_MM else (200, 0, 0)
        d.ellipse([q[0] - 40, q[1] - 40, q[0] + 40, q[1] + 40], outline=(150, 150, 150))
        d.text((q[0] - 18, q[1] - 14), r, fill=(0, 0, 0), font=fs)
        d.text((q[0] - 24, q[1]), "%.0f / %.1f" % (sag_holes[k] * 100, sag_final[k] * 100), fill=c, font=fs)
    for n, (x, y) in enumerate(pillars):
        q = P(x, y)
        d.ellipse([q[0] - 10, q[1] - 10, q[0] + 10, q[1] + 10], fill=(220, 40, 40))
        d.text((q[0] + 11, q[1] - 6), "P%d" % (n + 1), fill=(200, 0, 0), font=fs)
    img.save(out)


def main():
    b, keys, holes = board_geometry()
    if len(keys) != 28 or len(holes) != 8:
        raise SystemExit("esperava 28 teclas e 8 furos M2: %d, %d" % (len(keys), len(holes)))
    boxes = obstacles(b)
    gr = Grillage()
    loads = [(x, y) for _r, x, y in keys]
    sup = [(x, y) for _r, x, y in holes]
    s0 = gr.sag(sup, loads)
    spots = free_spots(boxes, holes)
    pillars, s = [], list(s0)
    while max(s) > TARGET_MM and len(pillars) < 60:
        w = max(range(len(keys)), key=lambda i: s[i])
        kx, ky = loads[w]
        # the free spot nearest the worst key, not on an existing pillar (8 mm apart)
        cands = sorted(spots, key=lambda p: math.hypot(p[0] - kx, p[1] - ky))
        pick = next((p for p in cands if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 8.0 for q in pillars)), None)
        if pick is None:
            break
        pillars.append(pick)
        s = gr.sag(sup + pillars, loads)
    worst0 = max(range(len(keys)), key=lambda i: s0[i])
    worst = max(range(len(keys)), key=lambda i: s[i])
    res = {
        "modelo": "grelha de vigas %.0f mm na placa nua de %.1f mm (FR-4, E = %.0f MPa), sem rigidez a torcao, "
                  "plate de 1,6 mm ignorado; %.0f N no centro de cada tecla, sozinha" % (GRID_H, THICKNESS, E_FR4, PRESS_N),
        "alvo_mm": TARGET_MM,
        "so_furos": {"apoios": [r for r, _x, _y in holes], "max_mm": round(max(s0), 4),
                     "pior_tecla": keys[worst0][0], "media_mm": round(sum(s0) / len(s0), 4),
                     "por_tecla_mm": {k[0]: round(v, 4) for k, v in zip(keys, s0)}},
        "pilares_propostos": [list(p) for p in pillars],
        "com_pilares": {"max_mm": round(max(s), 4), "pior_tecla": keys[worst][0],
                        "media_mm": round(sum(s) / len(s), 4),
                        "por_tecla_mm": {k[0]: round(v, 4) for k, v in zip(keys, s)}},
        "lugares_livres_no_verso": len(spots),
        "regra_do_lugar": "borda do pilar Ø%.0f a >= %.1f mm de pad, via ou corpo de peca no verso; fora do anel "
                          "dos furos M2 e da area do cartao MicroMod" % (PILLAR_D, PILLAR_CLEAR),
    }
    m = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    m["flexao"] = res
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    picture(keys, holes, pillars, s0, s, spots, os.path.join(BUILD, "m3_flexao.png"))
    print("so os 8 furos: %.3f mm (pior %s); %d pilares propostos -> %.4f mm (pior %s); %d lugares livres"
          % (max(s0), keys[worst0][0], len(pillars), max(s), keys[worst][0], len(spots)))


if __name__ == "__main__":
    main()
