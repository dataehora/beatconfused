"""Student V4 (R10V4): the R8 panel arrangements against the R4 panel and the 100 x 100 mm tier (CadQuery venv: matplotlib).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/regua/painel_r8.py

Writes pcb/regua/img/regua8_painel.png. Geometry only (strip outlines with the post notches from posicao_regua8.json / posicao_regua.json,
5 mm rails, 2 mm gaps, two 3 mm tabs per long edge): nothing is ordered, no Gerber is written for the R8 panel in this revision.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
RAIL, GAP = 5.0, 2.0
r8 = json.load(open(os.path.join(HERE, "posicao_regua8.json"), encoding="utf-8"))
r4 = json.load(open(os.path.join(HERE, "posicao_regua.json"), encoding="utf-8"))


def draw(ax, x0, y0, d, n, label, over):
    u0 = d["contorno_uv"][0][0]
    L = d["pcb_mm"][0] + 0.4
    w = RAIL + GAP + (L - 0.4) + GAP + RAIL
    h = RAIL + GAP + n * 14 + (n - 1) * GAP + GAP + RAIL
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#f3efe2", ec="#a33" if over else "#333", lw=1.4))
    for (cx, cy) in ((RAIL / 2, RAIL / 2), (w - RAIL / 2, RAIL / 2), (RAIL / 2, h - RAIL / 2), (w - RAIL / 2, h - RAIL / 2)):
        ax.add_patch(Circle((x0 + cx, y0 + cy), 1.0, fc="white", ec="k", lw=0.5))
    for i in range(n):
        sx, sy = x0 + RAIL + GAP, y0 + RAIL + GAP + i * (14 + GAP)
        pts = [(sx + (u - u0), sy + (v + 7.0)) for (u, v) in d["contorno_uv"]]
        ax.add_patch(Polygon(pts, closed=True, fc="#e9f2e0", ec="#2f5d1c", lw=0.8))
        for tc in ((10.0, 65.0) if L < 100 else (10.0, L - 9.0)):
            for ey in (sy, sy + 14):
                ax.add_patch(Rectangle((sx + tc - 1.5, ey - GAP / 2 - (0 if ey == sy else -0.0)), 3.0, GAP / 1.0, fc="#caa", ec="none", alpha=0.5) if False else Rectangle((sx + tc - 1.5, ey - (GAP if ey == sy else 0)), 3.0, GAP, fc="#caa", ec="none", alpha=0.6))
    ax.text(x0 + w / 2, y0 + h + 2.0, "%s: %.1f x %.1f mm = %.0f cm2%s" % (label, w, h, w * h / 100, "  (passa de 100 x 100)" if over else ""),
            ha="center", fontsize=8)
    return w, h


fig, ax = plt.subplots(figsize=(15, 7.5))
ax.add_patch(Rectangle((0, 0), 100, 100, fill=False, ec="#2a7fb8", ls="--", lw=1.2))
ax.text(50, 50, "100 x 100 mm\n(faixa barata da JLCPCB)", ha="center", color="#2a7fb8", fontsize=9)
draw(ax, 0, 0, r4, 5, "R4 hoje, 5 tiras (88 x 84)", False)
x = 110
draw(ax, x, 0, r8, 2, "R8 A: 2 tiras (recomendada; 4 R8 em 2 paineis montados)", True)
draw(ax, x, 62, r8, 4, "R8 B: 4 tiras (lado menor >= 70 mm; 8 R8 em 2 paineis montados)", True)
ax.set_xlim(-5, x + 170)
ax.set_ylim(-5, 160)
ax.set_aspect("equal")
ax.set_title("Paineis das reguas, mesma escala (R10V4). Verde = regua, rosa = abas com microfuros, circulos = furos de ferramenta. Pecas nao desenhadas; nada encomendado.", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "regua8_painel.png"), dpi=120)
print("ok")
