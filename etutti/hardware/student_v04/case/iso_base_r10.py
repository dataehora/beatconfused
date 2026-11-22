"""R10V4: isometric views of the robust base (tray) of the 32-key Student V4 (4 x R8), from the official model (case/case_r4.py). Same style as the Chat's spec_img/iso_base_r9.py.

    python etutti/hardware/student_v04/case/iso_base_r10.py     -> case/renders/iso_base_r10.png

Needs cadquery + matplotlib only. The SPEC frame is left-handed (y towards the player); the plot uses y_plot = -y so the picture
is not mirrored. Panel A: the tray alone (floor, rails, D6 bosses, posts' holes, recesses). Panel B: the same with the rulers
(translucent), SH headers/plugs and the cable envelopes, and the note name over every key.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = HERE
sys.path.insert(0, CASE)
import case_r4 as R      # noqa: E402
import layout_r4 as L    # noqa: E402

LIGHT = np.array([-0.4, 0.5, 0.75])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def mesh(shape, tol=0.08):
    vs, tris = shape.val().tessellate(tol, 0.3) if hasattr(shape, "val") else shape.tessellate(tol, 0.3)
    v = np.array([(p.x, -p.y, p.z) for p in vs])
    return v, np.array(tris)


SCENE = []


def add(ax, shape, color, alpha=1.0, tol=0.08, edge=False):
    v, t = mesh(shape, tol)
    if len(t) == 0:
        return
    tri = v[t]
    SCENE.append((tri, color, alpha))


def flush(ax):
    tris, cols = [], []
    for tri, color, alpha in SCENE:
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        shade = 0.35 + 0.65 * np.clip(np.abs(n @ LIGHT), 0, 1)
        base = np.array(matplotlib.colors.to_rgb(color))
        c = np.clip(base[None, :] * shade[:, None], 0, 1)
        tris.append(tri); cols.append(np.c_[c, np.full(len(c), alpha)])
    SCENE.clear()
    pc = Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), linewidths=0.08, edgecolors=(0, 0, 0, 0.12))
    ax.add_collection3d(pc)


def _unused(tri, color, alpha, edge, ax):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    shade = 0.45 + 0.55 * np.clip(np.abs(n @ LIGHT), 0, 1)
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(base[None, :] * shade[:, None], 0, 1)
    pc = Poly3DCollection(tri, facecolors=np.c_[cols, np.full(len(cols), alpha)], linewidths=0.05 if edge else 0,
                          edgecolors=(0, 0, 0, 0.15) if edge else None)
    ax.add_collection3d(pc)


def frame(ax, xlim, ylim, zlim, elev=34, azim=-58, zoom=1.12):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_zlim(*zlim)
    ax.set_box_aspect((xlim[1] - xlim[0], ylim[1] - ylim[0], (zlim[1] - zlim[0]) * 1.6), zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def labels(ax, mod=0):
    for r, y, x0, n in L.ROWS:
        for i in range(n + 4 * mod):
            name = L.note_name(r, i)
            sharp = "#" in name
            z = L.ZR[r - 1] + 1.0
            ax.text(x0 + i * L.PITCH, -y, z, name, ha="center", va="center", fontsize=6.5, fontweight="bold", zorder=50,
                    color="white" if sharp else "black",
                    bbox=dict(boxstyle="round,pad=0.15", fc="black" if sharp else ("#ffe08a" if L.is_cf(name) else "white"), ec="black", lw=0.4))


def main():
    mod = 0
    tray = R.tray(mod)
    ru = R.rulers_solid(mod)
    cn = R.connectors(mod)
    cab = R.cabos(mod, L.CABLE_FREE_MM[0], False)
    sc = R.screws(mod)
    Lx = L.length(mod)
    xl, yl, zl = (-2, Lx + 2), (-L.Y_FRONT - 2, -L.Y_BACK + 2), (L.Z_BOT - 1, 14)

    fig = plt.figure(figsize=(20, 17))
    ax = fig.add_subplot(2, 1, 1, projection="3d")
    add(ax, tray, "#c9c3b4", edge=True)
    flush(ax)
    frame(ax, xl, yl, zl)
    ax.set_title("A · Base robusta (bandeja) das 32 teclas, sem réguas: piso de 2 mm, um montante contínuo por fileira, a frente de cada degrau fechada (riser até o degrau vizinho),\n"
                 "paredes de ponta, 8 bossas D6 dos M2 (2 por fileira), túneis dos 4 cabos da placa, recortes dos cabeçalhos / plugues / 595", fontsize=11, loc="left")

    ax = fig.add_subplot(2, 1, 2, projection="3d")
    add(ax, tray, "#c9c3b4")
    add(ax, cab, "#d9534f", 0.9)
    add(ax, cn["cabecalhos"], "#333333")
    add(ax, cn["plugues"], "#f0f0f0")
    add(ax, sc, "#8a8a8a")
    add(ax, ru, "#3f9f6f", 0.55)
    flush(ax)
    labels(ax, mod)
    frame(ax, xl, yl, zl)
    ax.set_title("B · A mesma base com as 4 réguas R8 (verde, transparente), cabeçalhos SH IN e OUT (preto), plugues IN (branco), os 4 cabos da placa de 45,8 mm (vermelho)\n"
                 "e os 8 M2 (cinza); nome da nota sobre cada tecla (C e F em amarelo); o OUT da R8 fica sem cabo no modelo de 32", fontsize=11, loc="left")

    fig.text(0.01, 0.01, "Fonte: modelo oficial case/case_r4.py (R10V4). Vista isométrica de cima, pela frente-esquerda. Fileira 1 = frente (jogador), fileira 4 = trás. Interface à esquerda.", fontsize=9)
    
    out = os.path.join(HERE, "renders", "iso_base_r10.png")
    fig.savefig(out, dpi=110, bbox_inches='tight')
    fig2 = plt.figure(figsize=(16, 9))
    ax = fig2.add_subplot(1, 1, 1, projection="3d")
    add(ax, tray, "#c9c3b4", edge=True)
    flush(ax)
    frame(ax, (80, 160), (-L.Y_FRONT + 10, -L.Y_BACK - 30), (L.Z_BOT - 1, 14), elev=28, azim=-35, zoom=1.12)
    ax.set_title("C · Detalhe da base (x 80 a 160), visto de frente-esquerda mais baixo: a frente de cada degrau é uma parede cheia ligando trilhos, riser e piso;\n"
                 "a abertura é só onde passam o plugue IN (7,4 mm) e o cabo da placa", fontsize=11, loc="left")
    fig2.savefig(os.path.join(HERE, "renders", "iso_base_r10_detalhe.png"), dpi=110, bbox_inches='tight')
    print(out)


if __name__ == "__main__":
    main()
