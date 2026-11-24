"""R14V4 task 1 (done in the R15V4 round): where the ruler's M2 bolts sit, to scale. A row-1 R8 seen from above (left half: KS-20 mounted; right half: no keys, the grade
seen through, holes, sensors, 74HC595, J1, bolt heads), with the distances head -> housing, head -> grade window edge, head -> rail, the note name of every key position, and two
sections through the bolt axis (XZ along the bolt line v +5.2, YZ across the ruler at u 18.5) showing ruler, grade, head, nut in its hex pocket with the crush ribs, rail, boss.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/regua_parafusos_r14.py   -> case/renders/regua_parafusos_r14.png
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("ETUTTI_CRADLE", "1")
import layout_r4 as L    # noqa: E402
import ligacao_h as H    # noqa: E402

ROW = 1
PITCH = L.PITCH
HEAD_D, HEAD_MAX, HEAD_K = 3.8, 4.0, 1.6
GRADE_Z0, GRADE_Z1, GRADE_W, WIN = 3.4, 5.0, 16.0, 14.0
SH = H.RULER["pecas"]


def hexpts(cx, cy, af):
    r = af / math.sqrt(3.0)
    return [(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i))) for i in range(6)]


def main():
    fig = plt.figure(figsize=(26, 17))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1.0, 0.1], hspace=0.28, wspace=0.12)
    ax = fig.add_subplot(gs[0, :])
    ax.set_aspect("equal")
    holes = L.M2_BY_ROW[ROW]
    ax.add_patch(Rectangle((0.2, -7), 147.6, 14, fc="#e8dcc0", ec="k", lw=1.2))                          # ruler FR-4 (seen from above)
    ax.add_patch(Rectangle((0.2, -8), 147.6, 16, fc="#303030", ec="k", lw=0.8, alpha=0.18))              # grade 16 mm wide (thin film, seen through)
    for i in range(8):
        xc = PITCH / 2 + i * PITCH
        nm = L.note_name(ROW, i)
        mounted = i < 4
        ax.add_patch(Rectangle((xc - 7, -7), 14, 14, fc="white" if not mounted else "#ffffff", ec="#444", lw=0.8, ls="-" if mounted else ":"))     # grade window 14.00
        for dx in (-L.PEG_DX, L.PEG_DX):
            ax.add_patch(Circle((xc + dx, 0), 0.85, fc="#c0c0c0", ec="k", lw=0.6))
        ax.add_patch(Rectangle((xc - 0.9, -1.1), 1.8, 2.2, fc="none", ec="#1d4ed8", lw=0.8, ls="--"))     # TMAG5253 under the ruler
        if mounted:
            ax.add_patch(Rectangle((xc - 7.7, -7.55), 15.4, 15.1, fc="#f3f3f3" if not L.is_cf(nm) else "#fde68a", ec="#222", lw=1.0, alpha=0.85))   # KS-20 cover 15.4 x 15.1
            ax.add_patch(Rectangle((xc - 7.0, -7.0), 14, 14, fc="none", ec="#222", lw=0.6, ls=":"))
        ax.text(xc, 0, nm, ha="center", va="center", fontsize=13, fontweight="bold", color="#111")
    # parts under the ruler (bottom side, dashed)
    for ref, (u0, v0, u1, v1), h in H.UNDER_PARTS:
        if ref.startswith("U") and ref != "U9":
            continue
        if ref in ("J2", "R1"):
            continue
        ax.add_patch(Rectangle((u0, v0), u1 - u0, v1 - v0, fc="none", ec="#7c3aed" if ref in ("J1", "U9") else "#999", lw=1.0, ls="--"))
        if ref in ("J1", "U9"):
            ax.text((u0 + u1) / 2, v1 + 0.9 if ref == "U9" else v0 - 1.0, "J1 (IN)" if ref == "J1" else "74HC595", ha="center", va="top" if ref == "J1" else "bottom", fontsize=10, color="#7c3aed")
    # bolt heads and holes
    for u in holes:
        v = 5.2
        ax.add_patch(Circle((u, v), 1.1, fc="#ffffff", ec="k", lw=0.8))
        ax.add_patch(Circle((u, v), HEAD_D / 2, fc="#9ca3af" if u > 74 else "none", ec="#b91c1c", lw=1.6, ls="-" if u > 74 else "--", alpha=0.9))
        ax.plot([u - 0.8, u + 0.8], [v, v], color="#b91c1c", lw=1.2)
        ax.plot([u, u], [v - 0.8, v + 0.8], color="#b91c1c", lw=1.2)
    # dimensions at the right-hand bolt (u 129.5): head -> neighbouring housing / window edge, head -> ruler front edge (rail), head -> rail inner edge
    u = 129.5
    def dim(x0, y0, x1, y1, txt, dy=0.0, dx=0.0, col="#b91c1c"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="<->", color=col, lw=1.1))
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, txt, color=col, fontsize=10, ha="center", va="bottom", fontweight="bold")
    xc_l, xc_r = 9.25 + 18.5 * 6, 9.25 + 18.5 * 7                  # the two keys either side of u 129.5
    dim(xc_l + 7.0, 5.2, u - HEAD_D / 2, 5.2, "", dy=0)
    ax.text(xc_l + 7.0 + 0.1, 8.6, "carcaça/janela 14,00 -> cabeça: 0,35", color="#b91c1c", fontsize=10, ha="left")
    ax.annotate("", xy=(u + HEAD_D / 2, 5.2), xytext=(xc_r - 7.0, 5.2), arrowprops=dict(arrowstyle="<->", color="#b91c1c", lw=1.1))
    ax.plot([u, u + 9.5], [5.2, 12.0], color="#b91c1c", lw=0.6)
    ax.text(u + 9.6, 12.0, "vão entre as carcaças (corpo 14): 4,50; cabeça Ø3,8 (máx. 4,0): sobra 0,35 (0,25) de cada lado", color="#b91c1c", fontsize=10, ha="left")
    ax.annotate("", xy=(u + 6.5, 7.0), xytext=(u + 6.5, 5.2 + HEAD_D / 2 - 0.0), arrowprops=dict(arrowstyle="<->", color="#0e7490", lw=1.1))
    ax.text(u + 7.0, 6.9, "borda da régua (v +7,0): a cabeça passa 0,1 (Ø4,0: 0,2)", color="#0e7490", fontsize=9.5, ha="left", va="center")
    ax.annotate("", xy=(u - 5.2, 4.2), xytext=(u - 5.2, 5.2), arrowprops=dict(arrowstyle="<->", color="#15803d", lw=1.1))
    ax.text(u - 5.6, 4.3, "eixo -> borda de dentro do trilho (v +4,2): 1,0;\nborda de fora do trilho: 1,8; a bossa D6 sustenta a cabeça", color="#15803d", fontsize=9.5, ha="right", va="top")
    ax.set_xlim(-4, 152)
    ax.set_ylim(-10.5, 17)
    ax.invert_yaxis()
    ax.set_title("R8 da fileira 1, vista de cima, 1:1 (mm). Esquerda: 4 KS-20 montadas sobre a grade (cabeças tracejadas = ocultas pela grade). Direita: sem teclas (grade vista por transparência), "
                 "furos Ø2,2 em u 18,5 e 129,5 (v +5,2), pinos Ø1,7, sensores (tracejado azul, face de baixo), 74HC595 e J1 (roxo, face de baixo)", fontsize=11)
    ax.set_xlabel("u (mm ao longo da régua, a partir da ponta esquerda)    v: + para o jogador")
    # ---- section 1: XZ along the bolt line (v +5.2) at the u 129.5 bolt: head between two housings
    a1 = fig.add_subplot(gs[1, 0])
    a1.set_aspect("equal")
    ub = 129.5
    z0 = 0.0
    for xc in (xc_l, xc_r):
        a1.add_patch(Rectangle((xc - 7.0, z0), 14, 5.0, fc="#e5e7eb", ec="k"))                          # housing body 14 x 5
        a1.add_patch(Rectangle((xc - 7.7, 5.0), 15.4, 3.6, fc="#d1d5db", ec="k"))                          # cover 15.4
        a1.add_patch(Polygon([(xc - 7.7, 8.6), (xc + 7.7, 8.6), (xc + 6.75, 10.6), (xc - 6.75, 10.6)], fc="#d1d5db", ec="k"))
    a1.add_patch(Rectangle((xc_l - 7.0 - 3, -1.2), 2 * 18.5 + 14 + 6, 1.2, fc="#e8dcc0", ec="k"))        # ruler
    a1.add_patch(Rectangle((xc_l - 7.0 - 3, GRADE_Z0), 3 + 0.0, GRADE_Z1 - GRADE_Z0, fc="#374151", ec="k"))
    a1.add_patch(Rectangle((xc_l + 7.0, GRADE_Z0), 4.5, GRADE_Z1 - GRADE_Z0, fc="#374151", ec="k"))     # grade web between two windows (4.5 wide)
    a1.add_patch(Rectangle((xc_r + 7.0, GRADE_Z0), 3, GRADE_Z1 - GRADE_Z0, fc="#374151", ec="k"))
    a1.add_patch(Rectangle((ub - HEAD_D / 2, 0), HEAD_D, HEAD_K, fc="#9ca3af", ec="#b91c1c", lw=1.6))
    a1.add_patch(Rectangle((ub - 1.0, -10.0), 2.0, 10.0, fc="#9ca3af", ec="k"))
    a1.add_patch(Rectangle((ub - 3.0, -8.1), 6.0, 6.9, fc="#fde68a", ec="k", alpha=0.7))               # boss D6 (to the ruler's underside)
    a1.add_patch(Rectangle((ub - 3.0 - 2, -10.1), 12, 2.0, fc="#fde68a", ec="k", alpha=0.7))
    a1.annotate("", xy=(ub - HEAD_D / 2, 0.8), xytext=(xc_l + 7.0, 0.8), arrowprops=dict(arrowstyle="<->", color="#b91c1c"))
    a1.text(xc_l + 7.1, 1.1, "0,35", color="#b91c1c", fontsize=11, ha="left")
    a1.annotate("", xy=(ub + HEAD_D / 2, 0.8), xytext=(xc_r - 7.0, 0.8), arrowprops=dict(arrowstyle="<->", color="#b91c1c"))
    a1.annotate("", xy=(ub, 1.6), xytext=(ub, GRADE_Z0), arrowprops=dict(arrowstyle="<->", color="#0e7490"))
    a1.text(ub + 0.2, 2.6, "1,8 até a grade", color="#0e7490", fontsize=10)
    a1.text(xc_l + 7.1, 6.6, "acima da grade o vão entre\ncoberturas é 3,1 (não passa nada)", fontsize=10, color="#374151", ha="left")
    a1.set_xlim(xc_l - 9, xc_r + 9)
    a1.set_ylim(-11, 12)
    a1.set_title("Corte A-A: ao longo da linha dos parafusos (v +5,2) no furo u 129,5 — a cabeça (z 0 a 1,6) fica ABAIXO da grade (z 3,4 a 5,0) e entre os dois corpos de 14", fontsize=10)
    # ---- section 2: YZ across the ruler at u 18.5 (bolt axis): ruler, grade, head, rail, boss, nut in the hex pocket with ribs
    a2 = fig.add_subplot(gs[1, 1])
    a2.set_aspect("equal")
    vb = 5.2
    a2.add_patch(Rectangle((-7, -1.2), 14, 1.2, fc="#e8dcc0", ec="k"))                                    # ruler
    a2.add_patch(Rectangle((-8, GRADE_Z0), 16, GRADE_Z1 - GRADE_Z0, fc="#374151", ec="k"))               # grade web (solid across v at this u)
    a2.add_patch(Rectangle((vb - HEAD_D / 2, 0), HEAD_D, HEAD_K, fc="#9ca3af", ec="#b91c1c", lw=1.6))
    a2.add_patch(Rectangle((vb - 1.0, -10.0), 2.0, 10.0, fc="#9ca3af", ec="k"))
    a2.add_patch(Rectangle((4.2, -8.1), 2.8, 6.9, fc="#fde68a", ec="k", alpha=0.7))                       # front rail
    a2.add_patch(Rectangle((-7.0, -8.1), 2.8, 6.9, fc="#fde68a", ec="k", alpha=0.7))                      # back rail
    a2.add_patch(Rectangle((vb - 3.0, -8.1), 6.0, 6.9, fc="#fcd34d", ec="k", alpha=0.8))                  # boss D6
    a2.add_patch(Rectangle((-9, -10.1), 22, 2.0, fc="#fde68a", ec="k", alpha=0.7))                        # floor
    nut = Rectangle((vb - 2.0, -9.9), 4.0, 1.6, fc="#6b7280", ec="k")                                     # M2 nut AF 4.0 x 1.6 (row 1), pocket 4.2, top at -8.3
    a2.add_patch(Rectangle((vb - 2.1, -10.1), 4.2, 1.8, fc="white", ec="k", lw=0.8, zorder=1))
    a2.add_patch(nut)
    for sx in (-1, 1):                                                                                    # the crush ribs (seen in section: 0.2 mm off the flat, 0.4 wide)
        a2.add_patch(Rectangle((vb + sx * 2.1 - (0.2 if sx > 0 else 0.0), -9.8), 0.2, 1.5, fc="#b91c1c", ec="none", zorder=3))
    a2.text(vb + 2.5, -9.7, "costelas de pressão\n(0,2 de saliência, 0,1 de interferência)", fontsize=9, color="#b91c1c", va="center")
    a2.text(vb + 3.3, -4.5, "bossa D6", fontsize=10)
    a2.text(7.3, -6.0, "trilho\nda frente", fontsize=10)
    a2.text(-6.5, -4.0, "trilho\nde trás", fontsize=10)
    a2.text(-7.5, 4.0, "grade 1,6", fontsize=10, color="white")
    a2.set_xlim(-10, 14)
    a2.set_ylim(-11, 7)
    a2.set_title("Corte B-B: através da régua no eixo do parafuso (u 18,5), M2 x 10 da fileira 1, porca de 1,6 no bolso sextavado AF 4,2", fontsize=10)
    fig.text(0.01, 0.015, "Chave de fenda: Phillips #0 (parafuso M2 de cabeça panela com fenda em cruz, ISO 7045, não magnética). Com a grade e as teclas no lugar a cabeça não é alcançável (a grade cobre o vão de 4,5 e acima dele o vão entre coberturas é 3,1): "
             "por isso os parafusos entram ANTES das teclas (a régua é parafusada na base, e só depois a grade com as 4 teclas desce nos pinos).", fontsize=11)
    out = os.path.join(HERE, "renders", "regua_parafusos_r14.png")
    fig.savefig(out, dpi=100, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
