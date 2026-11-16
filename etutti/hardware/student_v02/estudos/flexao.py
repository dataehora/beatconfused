"""eTutti Student V2: how far the board and the keyboard grid bend (SPEC v1, section 3).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/estudos/flexao.py

The model is the Viaggio J1's (viaggio_j1/mechanics.py, imported): a grillage of beams on a 4 mm
mesh, FR-4 E = 18 GPa, no twisting stiffness, one key pressed at a time. In the V2 no plate
helps the board (the switches stand on it), so the bare board is the real structure.

Board, 1.2 mm, 3 N on each key (a firm press; 10 N = a hard hit is the same result x 3.33):
  A  held only on its edge: the 10 screws of the grid and the 6 of the lid;
  B  A + the SPEC's proposal, three pins in row 2 (x 116.95 / 153.95 / 190.95, y 58.01);
  C  A + four pins in the V1's holes between the keys (H5-H8), which also locate the board;
  D  C + pillars added one by one where the back of the board is free, until every key bends
     0.05 mm or less (the eTuttino's and the J1's target).
A pin holds the board from below only; the model pins it both ways, so a point far from the
pressed key that would lift is held down: the numbers are slightly optimistic there.

Grid, 1.6 mm, on its 10 screws, a finger pressing 5 N between the buttons, for three materials.
The grid is 0.4 mm above the switch housings: when it bends more than that it rests on them.

Writes estudos/flexao.json, estudos/apoios.json (the pillars the case models) and
estudos/flexao.png.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, V2)
sys.path.insert(0, os.path.normpath(os.path.join(V2, "..", "viaggio_j1")))
import geometria as G      # noqa: E402
import mechanics as M      # noqa: E402

M.BOARD = os.path.join(V2, "kicad", "student_v02.kicad_pcb")
TARGET = 0.05
PIN_D = 5.0
SPEC_PINS = [(116.95, 58.01), (153.95, 58.01), (190.95, 58.01)]
KEEP_OUT_X = 66.0          # left of this: battery, speaker box, module (no pillar)


def board_supports(b):
    import pcbnew
    holes = {}
    for fp in b.GetFootprints():
        r = fp.GetReference()
        if "MountingHole" in fp.GetFPIDAsString():
            holes[r] = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
    return holes


def grid_sag(E, loads):
    """The grid as a plate on its 10 screws. Net section: a 6.2 mm hole every 18.5 mm."""
    pts = G.offset(G.GRID_EDGE, 1.0)
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    keep = (M.X0, M.Y0, M.X1, M.Y1, M.E_FR4)
    M.X0, M.Y0, M.X1, M.Y1 = x0, y0, x1, y1
    M.E_FR4 = E * (1 - 6.2 / 18.5)
    gr = M.Grillage(t=1.6)
    s = gr.sag(G.grid_screws(), loads)
    M.X0, M.Y0, M.X1, M.Y1, M.E_FR4 = keep
    return s


def main():
    b, keys, _ = M.board_geometry()
    holes = board_supports(b)
    edge = [holes[k] for k in sorted(holes) if k.startswith("HG") or k in ("H1", "H2", "H3", "H4", "H9", "H10")]
    pins = [holes[k] for k in ("H5", "H6", "H7", "H8")]
    loads = [(x, y) for _r, x, y in keys]
    gr = M.Grillage()

    def case(sup):
        s = gr.sag(sup, loads)
        w = max(range(len(s)), key=lambda i: s[i])
        return {"max_mm": round(max(s), 4), "pior_tecla": keys[w][0], "media_mm": round(sum(s) / len(s), 4),
                "teclas_acima_do_alvo": sum(1 for v in s if v > TARGET),
                "por_tecla_mm": {k[0]: round(v, 4) for k, v in zip(keys, s)}}, s

    res = {"modelo": "grelha de vigas 4 mm, placa nua de 1,2 mm (FR-4, E = 18 GPa), sem rigidez a torcao; 3 N numa tecla de cada vez",
           "alvo_mm": TARGET, "placa": {}}
    res["placa"]["A_so_a_borda"], sA = case(edge)
    res["placa"]["B_tres_pinos_da_SPEC"], sB = case(edge + SPEC_PINS)
    res["placa"]["C_quatro_pinos_H5_H8"], sC = case(edge + pins)

    # D: add pillars where the back is free
    boxes = M.obstacles(b)
    ring = [(k, x, y) for k, (x, y) in holes.items()]
    spots = [p for p in M.free_spots(boxes, ring) if p[0] > KEEP_OUT_X]
    pillars, s = [], list(sC)
    while max(s) > TARGET and len(pillars) < 40:
        w = max(range(len(keys)), key=lambda i: s[i])
        kx, ky = loads[w]
        cands = sorted(spots, key=lambda p: math.hypot(p[0] - kx, p[1] - ky))
        pick = next((p for p in cands if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 8.0 for q in pillars)), None)
        if pick is None:
            break
        pillars.append(pick)
        s = gr.sag(edge + pins + pillars, loads)
    res["placa"]["D_pinos_e_pilares"], sD = case(edge + pins + pillars)
    res["placa"]["D_pinos_e_pilares"]["pilares"] = [list(p) for p in pillars]
    res["placa"]["D_pinos_e_pilares"]["com_10_N_max_mm"] = round(max(sD) * 10 / 3, 3)
    res["placa"]["apoios_na_borda"] = len(edge)
    res["placa"]["pinos"] = {"diametro_mm": PIN_D, "ponta_mm": 2.0, "furos": {k: list(holes[k]) for k in ("H5", "H6", "H7", "H8")}}
    res["placa"]["pilares"] = {"diametro_mm": M.PILLAR_D, "folga_mm": M.PILLAR_CLEAR, "lugares_livres": len(spots)}
    # is the SPEC's proposal free on the back?
    need = PIN_D / 2 + M.PILLAR_CLEAR
    res["placa"]["B_tres_pinos_da_SPEC"]["folga_no_verso_mm"] = [round(M.clearance(x, y, boxes) - PIN_D / 2, 2) for x, y in SPEC_PINS]
    res["placa"]["B_tres_pinos_da_SPEC"]["livres"] = [M.clearance(x, y, boxes) >= need for x, y in SPEC_PINS]

    # the pressure a pin puts on the board (bearing) and its own shortening
    area = math.pi * (PIN_D ** 2 - 2.2 ** 2) / 4
    res["placa"]["pino_pressao_MPa_a_10_N"] = round(10 / area, 2)

    # the grid
    mids = [((a[1] + b_[1]) / 2, (a[2] + b_[2]) / 2) for a in keys for b_ in keys
            if a[0] < b_[0] and abs(math.hypot(a[1] - b_[1], a[2] - b_[2]) - 18.5) < 0.2]
    res["grade"] = {"carga_N": 5.0, "folga_ate_as_teclas_mm": 0.4, "materiais": {}}
    for name, E in (("impressa (PETG, E = 2,0 GPa)", 2000.0), ("FR-4 (E = 18 GPa)", 18000.0), ("aluminio (E = 69 GPa)", 69000.0)):
        s = [v * 5.0 / M.PRESS_N for v in grid_sag(E, mids)]
        res["grade"]["materiais"][name] = {"max_mm": round(max(s), 3), "media_mm": round(sum(s) / len(s), 3),
                                           "encosta_nas_teclas": max(s) > 0.4}
    json.dump(res, open(os.path.join(HERE, "flexao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"pilares": [list(p) for p in pillars], "pinos": [list(p) for p in pins]},
              open(os.path.join(HERE, "apoios.json"), "w", encoding="utf-8"), indent=1)

    # picture
    from PIL import Image, ImageDraw, ImageFont
    S = 5.0
    W, H = int(254 * S), int(102 * S) + 46
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arial.ttf", 13)
        fs = ImageFont.truetype("arial.ttf", 10)
    except OSError:
        f = fs = ImageFont.load_default()

    def P(x, y):
        return (x * S, y * S + 46)
    d.text((6, 4), "Student V2 - flexao da placa a 3 N por tecla, vista de cima. Azul: parafusos na borda (grade e tampa). "
           "Verde: pinos nos furos H5-H8. Vermelho: pilares propostos. Laranja tracejado: pinos da SPEC.", fill=(0, 0, 0), font=f)
    d.text((6, 22), "Em cada tecla, em centesimos de mm: so a borda / 3 pinos da SPEC / 4 pinos H5-H8 / pinos + pilares.",
           fill=(0, 0, 0), font=f)
    d.rectangle([P(M.X0, M.Y0), P(M.X1, M.Y1)], outline=(0, 0, 0), width=2)
    for x, y in spots:
        d.point(P(x, y), fill=(200, 200, 200))
    for x, y in edge:
        q = P(x, y)
        d.ellipse([q[0] - 8, q[1] - 8, q[0] + 8, q[1] + 8], outline=(0, 90, 200), width=3)
    for x, y in SPEC_PINS:
        q = P(x, y)
        d.ellipse([q[0] - 12, q[1] - 12, q[0] + 12, q[1] + 12], outline=(230, 130, 0), width=2)
    for x, y in pins:
        q = P(x, y)
        d.ellipse([q[0] - 12, q[1] - 12, q[0] + 12, q[1] + 12], fill=(0, 150, 60))
    for x, y in pillars:
        q = P(x, y)
        d.ellipse([q[0] - 10, q[1] - 10, q[0] + 10, q[1] + 10], fill=(220, 40, 40))
    for k, (r, x, y) in enumerate(keys):
        q = P(x, y)
        d.ellipse([q[0] - 37, q[1] - 37, q[0] + 37, q[1] + 37], outline=(150, 150, 150))
        d.text((q[0] - 30, q[1] - 14), "%.0f / %.0f" % (sA[k] * 100, sB[k] * 100), fill=(120, 120, 120), font=fs)
        d.text((q[0] - 30, q[1]), "%.0f / %.1f" % (sC[k] * 100, sD[k] * 100),
               fill=(0, 140, 0) if sD[k] <= TARGET else (200, 0, 0), font=fs)
    img.save(os.path.join(HERE, "flexao.png"))
    for k, v in res["placa"].items():
        if isinstance(v, dict) and "max_mm" in v:
            print(k, v["max_mm"], v["pior_tecla"], "media", v["media_mm"], "acima do alvo:", v["teclas_acima_do_alvo"])
    print("SPEC pins:", res["placa"]["B_tres_pinos_da_SPEC"]["folga_no_verso_mm"])
    print("pilares:", pillars)
    print("grade:", res["grade"]["materiais"])


if __name__ == "__main__":
    main()
