"""eTutti Student V4 (R5V4): sections through the keyboard area and the outer edges (chamfers), cut from the real solids of case_r4.py.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/corte_teclado_v5.py

Writes case/renders/corte_chanfro_v5.png:
  A = plane x = 172.45 (a column of rows 1 and 3: front edge with the chamfer, the stepped deck, keys with the pressed cap, rulers, grades, tray, back edge),
  B = plane y = 74.03 (row 1's axis) at the right end: end wall, chamfers, the last ruler and key,
  C = plane y = 50 at the interface's left wall: chamfers and the board.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.path import Path                       # noqa: E402
from matplotlib.patches import PathPatch               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R    # noqa: E402

L = R.L
REN = os.path.join(HERE, "renders")


def sect(solid, axis, v):
    """Rings of the section of `solid` by the plane axis = v: axis 'x' -> (y, z) pairs, axis 'y' -> (x, z) pairs."""
    if axis == "x":
        slab = R.box(v - 0.005, v + 0.005, -5, 105, -20, 45)
    else:
        slab = R.box(-5, 500, v - 0.005, v + 0.005, -20, 45)
    try:
        inter = solid.intersect(slab)
    except Exception:
        return []
    rings = []
    for f in inter.faces().vals():
        n = f.normalAt()
        c = f.Center()
        if axis == "x" and (abs(abs(n.x) - 1) > 1e-6 or abs(c.x - (v - 0.005)) > 1e-4):
            continue
        if axis == "y" and (abs(abs(n.y) - 1) > 1e-6 or abs(c.y - (v - 0.005)) > 1e-4):
            continue
        for w in f.Wires():
            segs = []
            for e in w.Edges():
                k = 1 if e.geomType() == "LINE" else 24
                pts = [e.positionAt(i / k) for i in range(k + 1)]
                segs.append([((p.y, p.z) if axis == "x" else (p.x, p.z)) for p in pts])
            chain = segs.pop(0)
            while segs:
                d = lambda a, b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                i, rev = min(((i, r) for i in range(len(segs)) for r in (False, True)),
                             key=lambda ir: d(segs[ir[0]][-1 if ir[1] else 0], chain[-1]))
                nxt = segs.pop(i)
                chain += (nxt[::-1] if rev else nxt)[1:]
            rings.append(chain)
    return rings


def fill(ax, rings, **kw):
    verts, codes = [], []
    for r in rings:
        verts += r + [r[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY]
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def panel(ax, axis, v, parts, xlim, ylim):
    for name, solid, col in parts:
        fill(ax, sect(solid, axis, v), fc=col, ec="#222222", lw=0.5, alpha=0.92)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axhline(0, color="#3B6D11", lw=0.4, ls=":")
    ax.set_ylabel("z (mm), 0 = topo da placa")


def main():
    mod = 0
    lid, tray, ru, gr = R.lid(mod), R.tray(mod), R.rulers_solid(mod), R.grades(mod)
    keys = R.T.key_bodies(mod, 0.0, True)
    brd = R.board()
    parts = [("tampa", lid, "#D3D1C7"), ("bandeja", tray, "#9CA3AF"), ("réguas", ru, "#34D399"), ("grades", gr, "#FBBF24"), ("teclas", keys, "#FFFFFF")]
    Lx = L.length(mod)
    fig = plt.figure(figsize=(16, 15))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1.0, 1.0], hspace=0.28)
    a = fig.add_subplot(gs[0, :])
    panel(a, "x", 172.45, parts, (-3, 103), (-12, 35))
    a.set_title("A. Corte em x = 172,45 (coluna das fileiras 1 e 3): borda da frente e de trás com o chanfro, deck escalonado, teclas com o botão apertado, réguas e grades", fontsize=9.5)
    a.set_xlabel("y (mm)  ->  frente (jogador)")
    top_f, top_b = F_top(0), F_top(3)
    a.annotate("chanfro externo 2,0 x 2,0 (45 graus)", xy=(99.0, top_f - 1.0), xytext=(70, 33), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    a.annotate("chanfro externo 2,0 x 2,0", xy=(1.0, top_b - 1.0), xytext=(8, 33), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    a.annotate("chanfro inferior 1,0 x 1,0", xy=(0.6, L.Z_BOT + 0.5), xytext=(6, -11.2), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    a.annotate("topo da frente %.1f" % top_f, xy=(103, top_f), xytext=(104, top_f), fontsize=7, va="center", annotation_clip=False)
    a.annotate("topo de trás %.1f" % top_b, xy=(-3, top_b), xytext=(8, top_b + 3.5), fontsize=7, va="center", annotation_clip=False)
    b = fig.add_subplot(gs[1, 0])
    panel(b, "y", 74.03, parts, (196, 243), (-12, 28))
    b.set_title("B. Corte em y = 74,03 (eixo da fileira 1), ponta direita: parede, chanfro, última régua (até 237,0) e tecla F#5", fontsize=9)
    b.set_xlabel("x (mm)")
    b.annotate("chanfro 2,0 x 2,0", xy=(Lx - 1.0, top_f - 1.0), xytext=(222, 20), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    b.annotate("ponta da régua 237,0\nfolga 1,0 até a parede (x 238)", xy=(237.0, -0.6), xytext=(203, -5.0), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    c = fig.add_subplot(gs[1, 1])
    parts_c = [("tampa", lid, "#D3D1C7"), ("bandeja", tray, "#9CA3AF"), ("placa", brd, "#86EFAC")]
    panel(c, "y", 50.0, parts_c, (-3, 46), (-12, 18))
    c.set_title("C. Corte em y = 50, parede esquerda da interface", fontsize=9)
    c.set_xlabel("x (mm)")
    c.annotate("chanfro 2,0 x 2,0", xy=(1.0, L.ROOF_TOP - 1.0), xytext=(8, 16.5), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
    # D: the corner in plan, as a note: plan corner R6 (outside) / R4 (inside)
    d = fig.add_subplot(gs[2, :])
    panel(d, "y", 94.0, parts, (190, 243), (-12, 28))
    d.set_title("D. Corte em y = 94 (por cima da fileira 1, atrás dela só há a parede e o canto R6): o chanfro segue o canto em arco", fontsize=9)
    d.set_xlabel("x (mm)")
    fig.savefig(os.path.join(REN, "corte_chanfro_v5.png"), dpi=130, bbox_inches="tight")
    print("ok")


def F_top(i):
    return R.F.ZR[i] + R.F.DECK_TOP


if __name__ == "__main__":
    main()
