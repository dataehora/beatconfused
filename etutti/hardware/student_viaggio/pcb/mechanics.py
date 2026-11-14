"""How far the StudentViaggio board bends under a key press.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_viaggio/pcb/mechanics.py

The model is the Viaggio J1's (viaggio_j1/mechanics.py, imported, not copied): a grillage of
beams on a 4 mm grid, bare 1.2 mm FR-4, 3 N on one key at a time, the board pinned at its M2
holes; then case pillars (4 mm tips) are proposed on free spots of the back, one at a time,
until every key bends 0.05 mm or less.

Differences here: the keys are the 28 electrodes K01-K28 and the holes H1-H11 of
kicad/student_viaggio.kicad_pcb; the grid covers the board's bounding rectangle (2.5..212.5 x
2.5..97.5), so the two cut corners of the pointed end count as board (a little stiffer than
the real thing there; the pillars proposed near the tip make up for it). There is no switch
plate on this board, so nothing else stiffens it.

Writes pcb/flexao.json and img/flexao.png.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "viaggio_j1")))
import mechanics as M  # noqa: E402

BOARD = os.path.join(HERE, "kicad", "student_viaggio.kicad_pcb")
LAYOUT = json.load(open(os.path.join(HERE, "layout.json"), encoding="utf-8"))
M.X0, M.Y0, M.X1, M.Y1 = 2.5, 2.5, 212.5, 97.5


def inside(p, margin):
    poly = LAYOUT["poligono"]
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            c = not c
    if not c:
        return False
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        l2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        u = max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / l2))
        if math.hypot(a[0] + u * (b[0] - a[0]) - p[0], a[1] + u * (b[1] - a[1]) - p[1]) < margin:
            return False
    return True


def sag(gr, supports, loads):
    """M.Grillage.sag, plus keys that sit right on a support (0 mm). The back of this board is
    free under the keys, so a pillar can land on a key's own grid node; the J1's never could."""
    fixed = {gr.nearest(x, y) for x, y in supports}
    live = [i for i, p in enumerate(loads) if gr.nearest(*p) not in fixed]
    out = [0.0] * len(loads)
    for i, v in zip(live, gr.sag(supports, [loads[i] for i in live])):
        out[i] = v
    return out


def caption(path, n_holes):
    """M.picture writes the J1's caption: put this board's over it."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(path)
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle([0, 0, img.width, 38], fill=(255, 255, 255))
    d.text((6, 4), "StudentViaggio v0.2 - flexao a 3 N por tecla (grelha 4 mm, placa nua de 1,2 mm), vista de cima."
           " Azul: furos M2. Vermelho: pilares propostos.",
           fill=(0, 0, 0), font=f)
    d.text((6, 20), "Numero em cada tecla: flexao em centesimos de mm, so com os %d furos / com os pilares." % n_holes,
           fill=(0, 0, 0), font=f)
    img.save(path)


def main():
    import pcbnew
    b = pcbnew.LoadBoard(BOARD)
    mm = pcbnew.ToMM
    keys, holes = [], []
    for fp in b.GetFootprints():
        r = fp.GetReference()
        p = (mm(fp.GetPosition().x), mm(fp.GetPosition().y))
        if r.startswith("K") and "FSR_Comb" in fp.GetFPIDAsString():
            keys.append((r, p[0], p[1]))
        if r.startswith("H") and "MountingHole" in fp.GetFPIDAsString():
            holes.append((r, p[0], p[1]))
    keys.sort()
    holes.sort(key=lambda h: int(h[0][1:]))
    if len(keys) != 28 or len(holes) != len(LAYOUT["furos"]):
        raise SystemExit("esperava 28 teclas e %d furos: %d, %d" % (len(LAYOUT["furos"]), len(keys), len(holes)))
    boxes = M.obstacles(b)
    gr = M.Grillage()
    loads = [(x, y) for _r, x, y in keys]
    sup = [(x, y) for _r, x, y in holes]
    s0 = sag(gr, sup, loads)
    spots = [p for p in M.free_spots(boxes, holes) if inside(p, 3.0)]
    pillars, s = [], list(s0)
    while max(s) > M.TARGET_MM and len(pillars) < 60:
        w = max(range(len(keys)), key=lambda i: s[i])
        kx, ky = loads[w]
        cands = sorted(spots, key=lambda p: math.hypot(p[0] - kx, p[1] - ky))
        pick = next((p for p in cands if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 8.0 for q in pillars)), None)
        if pick is None:
            break
        pillars.append(pick)
        s = sag(gr, sup + pillars, loads)
    w0 = max(range(len(keys)), key=lambda i: s0[i])
    w1 = max(range(len(keys)), key=lambda i: s[i])
    res = {
        "modelo": "grelha de vigas %.0f mm, placa nua de %.1f mm (FR-4, E = %.0f MPa), sem rigidez a torcao; "
                  "%.0f N no centro de cada tecla, sozinha; retangulo 210 x 95 (os cantos cortados da ponta contam)"
                  % (M.GRID_H, M.THICKNESS, M.E_FR4, M.PRESS_N),
        "alvo_mm": M.TARGET_MM,
        "so_furos": {"apoios": [r for r, _x, _y in holes], "max_mm": round(max(s0), 4), "pior_tecla": keys[w0][0],
                     "media_mm": round(sum(s0) / len(s0), 4),
                     "por_tecla_mm": {k[0]: round(v, 4) for k, v in zip(keys, s0)}},
        "pilares_propostos": [list(p) for p in pillars],
        "com_pilares": {"max_mm": round(max(s), 4), "pior_tecla": keys[w1][0], "media_mm": round(sum(s) / len(s), 4),
                        "por_tecla_mm": {k[0]: round(v, 4) for k, v in zip(keys, s)}},
        "lugares_livres_no_verso": len(spots),
    }
    json.dump(res, open(os.path.join(HERE, "flexao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    png = os.path.join(HERE, "..", "img", "flexao.png")
    M.picture(keys, holes, pillars, s0, s, spots, png)
    caption(png, len(holes))
    print("so os %d furos: %.3f mm (pior %s); %d pilares propostos -> %.4f mm (pior %s); %d lugares livres"
          % (len(holes), max(s0), keys[w0][0], len(pillars), max(s), keys[w1][0], len(spots)))


if __name__ == "__main__":
    main()
