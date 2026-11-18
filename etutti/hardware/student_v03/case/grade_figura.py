"""Student V3: the figure for the grid's countersink order (plan + section). Run with the CadQuery venv:
    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/grade_figura.py
Writes renders/grade_escareada.png. Positions from geometria.py, sizes from case.py."""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G
import case as K

fig = plt.figure(figsize=(15, 8.2))
ax = fig.add_axes([0.03, 0.34, 0.94, 0.62])
hull = G.offset(G.GRID_EDGE, 1.0)
ax.add_patch(Polygon(hull, closed=True, fc="#2b2925", ec="k", alpha=0.9))
for _r, x, y in G.KEYS:
    ax.add_patch(Circle((x, y), K.GRID_HOLE / 2, fc="white", ec="#888", lw=0.5))
for i, (x, y) in enumerate(G.grid_screws(), 1):
    ax.add_patch(Circle((x, y), 4.4 / 2, fc="none", ec="#e0a030", lw=1.2, ls="--"))
    ax.add_patch(Circle((x, y), K.CSK_D / 2, fc="#ffd27a", ec="#a05a00", lw=0.8))
    ax.add_patch(Circle((x, y), 2.3 / 2, fc="white", ec="k", lw=0.8))
    ax.text(x, y + 4.2, "%d" % i, ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
ax.set_xlim(min(p[0] for p in hull) - 3, max(p[0] for p in hull) + 3)
ax.set_ylim(max(p[1] for p in hull) + 3, min(p[1] for p in hull) - 3)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Student V3 - grade FR-4 1,6 mm, vista de cima (a mesma face do teclado): 10 furos NPTH com escareado cônico 90° (laranja). "
             "Tracejado = cobre recuado até Ø 4,4 nas duas faces.", fontsize=11)

sx = fig.add_axes([0.05, 0.04, 0.4, 0.26])
t, d = K.GRID_T, (K.CSK_D - 2.3) / 2          # 0.75 deep at 90 deg
w, h = 7.0, t
def side(sgn):
    pts = [(sgn * 3.5, t), (sgn * K.CSK_D / 2, t)]
    return pts
sx.add_patch(Polygon([(-w, 0), (-K.CSK_D / 2, 0), (-K.CSK_D / 2, 0), (-1.15, 0), (-1.15, t - d), (-K.CSK_D / 2, t), (-w, t)], closed=True, fc="#c9b37a", ec="k"))
sx.add_patch(Polygon([(w, 0), (1.15, 0), (1.15, t - d), (K.CSK_D / 2, t), (w, t)], closed=True, fc="#c9b37a", ec="k"))
sx.plot([-2.2, -2.2], [t, t + 0.3], c="#e0a030"); sx.plot([2.2, 2.2], [t, t + 0.3], c="#e0a030")
sx.annotate("", xy=(-K.CSK_D / 2, t + 0.25), xytext=(K.CSK_D / 2, t + 0.25), arrowprops=dict(arrowstyle="<->"))
sx.text(0, t + 0.32, "boca Ø 3,8", ha="center")
sx.annotate("", xy=(-1.15, -0.25), xytext=(1.15, -0.25), arrowprops=dict(arrowstyle="<->")); sx.text(0, -0.75, "furo Ø 2,3", ha="center")
sx.text(7.6, t - d / 2, "0,75 de profundidade\n(sobram 0,85 de 1,6)\n90° (cone)", va="center", fontsize=9)
sx.text(-6.8, t + 0.55, "face de cima", fontsize=9); sx.text(-6.8, -0.9, "face de baixo", fontsize=9)
sx.set_xlim(-7.5, 15); sx.set_ylim(-1.2, t + 1.2); sx.set_aspect("equal"); sx.axis("off")
sx.set_title("Corte de um furo (escala 1:1, em mm)", fontsize=10)

tx = fig.add_axes([0.5, 0.02, 0.48, 0.3]); tx.axis("off")
tx.text(0, 1, "Pedido (JLCPCB e PCBWay): ver GRADE_ESCAREADA.md\n\n"
        "- 10 furos NPTH Ø 2,3 mm, escareado cônico 90°, boca Ø 3,8 mm\n- pela face de cima (a do teclado), 0,75 mm de profundidade\n"
        "- cobre recuado até Ø 4,4 mm em volta, nas duas faces\n- demais 28 furos Ø 6,2 mm: lisos, sem escareado",
        va="top", fontsize=11, family="monospace")
os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
fig.savefig(os.path.join(HERE, "renders", "grade_escareada.png"), dpi=110)
print("ok")
