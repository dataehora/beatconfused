"""eTutti Student V4 (R4V4): the side section through the interface, cut from the real solids of case_r4.py.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/corte_v4.py

Writes case/renders/corte_interface_v4.png: A = plane x = 37 (module, battery, speaker, box, OLED, board, lid, tray), B = plane x = 28 (knob).
"""
import os
import sys

import cadquery as cq
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


def polys(solid, x0):
    """Section of a solid by the plane x = x0 as a list of rings [(y, z), ...] (outer and inner, even-odd)."""
    slab = R.box(x0 - 0.005, x0 + 0.005, -5, 105, -20, 40)
    try:
        inter = solid.intersect(slab)
    except Exception:
        return []
    rings = []
    for f in inter.faces().vals():
        c = f.Center()
        n = f.normalAt()
        if abs(abs(n.x) - 1) > 1e-6 or abs(c.x - (x0 - 0.005)) > 1e-4:
            continue
        for w in f.Wires():
            segs = []
            for e in w.Edges():
                k = 1 if e.geomType() == "LINE" else 24
                segs.append([(p.y, p.z) for p in (e.positionAt(i / k) for i in range(k + 1))])
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


def panel(ax, x0, parts, ylim):
    for name, solid, col in parts:
        fill(ax, polys(solid, x0), fc=col, ec="#222222", lw=0.5, alpha=0.9)
    ax.set_xlim(*ylim)
    ax.set_ylim(-11.5, 28)
    ax.set_aspect("equal")
    ax.axhline(0, color="#3B6D11", lw=0.4, ls=":")
    ax.set_xlabel("y (mm)  ->  frente (jogador)")
    ax.set_ylabel("z (mm), 0 = topo da placa")


def main():
    lid, tray, brd, mdl, bat, spk = R.lid(0), R.tray(0), R.board(), R.module(), R.battery(), R.speaker()
    bx, _ = R.acoustic_box()
    ole = R.oled()
    knob = [R.knob(x, y) for x, y in L.KNOBS]
    enc = [R.encoder(x, y) for x, y in L.KNOBS]
    bots = R.bottom_parts()
    parts_a = [("tampa", lid, "#D3D1C7"), ("bandeja", tray, "#9CA3AF"), ("placa", brd, "#86EFAC"), ("módulo", mdl, "#A5B4FC"), ("bateria", bat, "#FDBA74"),
               ("falante", spk, "#67E8F9"), ("caixa", bx, "#A5F3FC"), ("OLED", ole, "#93C5FD")]
    parts_b = [("tampa", lid, "#D3D1C7"), ("placa", brd, "#86EFAC"), ("encoder", enc[0], "#FCD34D"), ("knob", knob[0], "#FEF3C7")]
    for ref in ("J401", "U501", "SW403", "U301"):
        if ref in bots:
            parts_a.append((ref, bots[ref], "#E5E7EB"))
    fig, axs = plt.subplots(2, 1, figsize=(15, 13), gridspec_kw={"height_ratios": [1.0, 1.0]})
    panel(axs[0], 37.0, parts_a, (-2, 102))
    axs[0].set_title("Corte A-A em x = 37 mm: tampa, caixa acústica, alto-falante, OLED, placa, módulo, bateria e bandeja (R4V4)", fontsize=10)
    panel(axs[1], 28.0, parts_b, (-2, 102))
    axs[1].set_title("Corte B-B em x = 28 mm (eixo do knob de volume; o de registro está em x = 46, igual)", fontsize=10)
    a = axs[0]
    notes = [(L.Z_BOT, "fundo da caixa -10,1"), (L.Z_FLOOR, "piso da bandeja -8,1"), (L.Z_FLOOR + 5, "topo da bateria -3,1 (5 mm)"),
             (-L.T_PCB, "fundo da placa -1,2"), (0.0, "topo da placa 0"), (6.8, "fundo do falante 6,8"), (11.3, "frente do falante 11,3"),
             (L.CEILING, "teto 12,6"), (L.ROOF_TOP, "topo da tampa 14,6")]
    for z, t in notes:
        a.annotate(t, xy=(101, z), xytext=(103, z), fontsize=6.5, va="center", annotation_clip=False)
    a.annotate("módulo: fundo em -5,9", xy=(18, -5.9), xytext=(4, -9.4), fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=0.5))
    a.annotate("OLED 9,4 a 12,5", xy=(10, 11), xytext=(-1, 17), fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=0.5))
    a.annotate("caixa: 0,3 a 12,0", xy=(60, 6), xytext=(60, 18), fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=0.5))
    b = axs[1]
    for z, t in ((11.5, "bucha do encoder 11,5"), (24.5, "ponta do eixo 24,5"), (25.9, "topo do knob 25,9"), (14.6, "topo da tampa 14,6")):
        b.annotate(t, xy=(101, z), xytext=(103, z), fontsize=6.5, va="center", annotation_clip=False)
    fig.tight_layout()
    fig.subplots_adjust(right=0.88)
    fig.savefig(os.path.join(REN, "corte_interface_v4.png"), dpi=140)
    print("ok")


if __name__ == "__main__":
    main()
