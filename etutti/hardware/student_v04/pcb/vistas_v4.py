"""Top and bottom pictures of the placed V4 main board + ratsnest density (CadQuery venv: matplotlib, numpy).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/vistas_v4.py

Reads pcb/posicao_v4.json (written by posiciona_v4.py); writes pcb/img/{topo,fundo,ratsnest}.png and pcb/roteabilidade_v4.json.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
d = json.load(open(os.path.join(HERE, "posicao_v4.json"), encoding="utf-8"))
x0, y0, x1, y1 = d["contorno"]
PLANE = {"GND", "+3V3"}
COL = {"USB_DP": "#d62728", "USB_DN": "#1f77b4", "VBUS": "#ff7f0e", "VSYS": "#e377c2", "VBAT": "#9467bd"}


def frame(ax, title):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="k", lw=1.2))
    ax.set_xlim(x0 - 3, x1 + 12)
    ax.set_ylim(y1 + 3, y0 - 3)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    ax.grid(True, lw=0.15)


def zones(ax, side):
    c = d["zonas"]["cartao"]
    if side == "B":
        ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=True, fc="#fff3b0", ec="#c9a800", lw=0.8, alpha=0.5, zorder=0))
        ax.text(c[0] + 0.5, c[1] + 1.0, "cartao MicroMod 22x22\n(pecas <= 1,9 mm)", fontsize=5.5, color="#7a6500")
        for k, p in d["zonas"]["plugues"].items():
            ax.add_patch(Rectangle((p[0], p[1]), p[2] - p[0], p[3] - p[1], fill=True, fc="#d9f0ff", ec="#2a7fb8", lw=0.6, alpha=0.6, zorder=0))
            ax.text(p[0] + 0.3, p[1] + 1.0, "plugue SH\nfileira " + k, fontsize=5, color="#1d5d86")


def corridors(ax, side):
    for k, c in d["corredores"].items():
        if side == "F" and "F.Cu" not in c[4]:
            continue
        if side == "B" and "B.Cu" not in c[4]:
            continue
        ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=True, fc="#c8f7c5", ec="#2e8b57", lw=0.7, alpha=0.35, zorder=0))
        ax.text(c[0] + 0.3, c[1] + 0.9, k, fontsize=5.5, color="#1c5e3a")


def draw_side(side, out):
    fig, ax = plt.subplots(figsize=(9, 9 * (y1 - y0 + 6) / (x1 - x0 + 15)))
    frame(ax, "Placa principal V4 (R3V4), vista de %s (KiCad x, y; y para o jogador)" % ("cima" if side == "F" else "baixo (JLCPCB)"))
    zones(ax, side)
    corridors(ax, side)
    for ref, p in d["pecas"].items():
        if p["lado"] != side:
            continue
        a = p["patio"]
        ax.add_patch(Rectangle((a[0], a[1]), a[2] - a[0], a[3] - a[1], fill=False, ec="#888", lw=0.5, ls="--"))
        ax.text((a[0] + a[2]) / 2, (a[1] + a[3]) / 2, ref, fontsize=4.2 if (a[2] - a[0]) < 5 else 6, ha="center", va="center", color="#222")
    for pd in d["pads"]:
        if pd["lado"] != side and not pd["th"]:
            continue
        w, h = (pd["w"], pd["h"]) if round(pd["rot"]) % 180 == 0 else (pd["h"], pd["w"])
        ax.add_patch(Rectangle((pd["x"] - w / 2, pd["y"] - h / 2), w, h, fc=COL.get(pd["net"], "#bbb"), ec="none", alpha=0.7))
    for ref, (x, y) in {"H1": (62.0, 48.0)}.items():
        pass
    ax.set_xlabel("x (mm)")
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print("png:", out)


def mst(pts):
    n = len(pts)
    if n < 2:
        return []
    inn = [0]
    edges = []
    dist = [math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]) for i in range(n)]
    par = [0] * n
    used = [False] * n
    used[0] = True
    for _ in range(n - 1):
        j = min((i for i in range(n) if not used[i]), key=lambda i: dist[i])
        edges.append((pts[par[j]], pts[j]))
        used[j] = True
        for i in range(n):
            if not used[i]:
                dd = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                if dd < dist[i]:
                    dist[i], par[i] = dd, j
    return edges


nets = {}
for pd in d["pads"]:
    if pd["net"] and not pd["net"].startswith("unconnected") and pd["net"] not in PLANE:
        nets.setdefault(pd["net"], []).append((pd["x"], pd["y"]))
edges = []
for n, pts in nets.items():
    for a, b in mst(pts):
        edges.append((n, a, b))
tot = sum(math.hypot(a[0] - b[0], a[1] - b[1]) for _, a, b in edges)
G = 5.0
nx, ny = int(math.ceil((x1 - x0) / G)), int(math.ceil((y1 - y0) / G))
heat = np.zeros((ny, nx))
for n, a, b in edges:
    L = math.hypot(a[0] - b[0], a[1] - b[1])
    k = max(2, int(L / 0.5))
    for i in range(k + 1):
        x = a[0] + (b[0] - a[0]) * i / k
        y = a[1] + (b[1] - a[1]) * i / k
        ix, iy = min(nx - 1, int((x - x0) / G)), min(ny - 1, int((y - y0) / G))
        heat[iy, ix] += L / k
fig, ax = plt.subplots(figsize=(9, 9 * (y1 - y0 + 6) / (x1 - x0 + 15)))
frame(ax, "Ratsnest (MST por rede; GND e +3V3 vao pelos planos) e densidade em mm de fio por celula de 5 x 5 mm")
im = ax.imshow(heat, extent=(x0, x0 + nx * G, y0 + ny * G, y0), cmap="YlOrRd", alpha=0.55, zorder=0, vmin=0)
for n, a, b in edges:
    ax.plot([a[0], b[0]], [a[1], b[1]], color=COL.get(n, "#3a6ea5"), lw=0.35, alpha=0.8)
fig.colorbar(im, ax=ax, shrink=0.5, label="mm de ratsnest por celula de 25 mm2")
fig.savefig(os.path.join(IMG, "ratsnest.png"), dpi=140, bbox_inches="tight")
plt.close(fig)
draw_side("F", os.path.join(IMG, "topo.png"))
draw_side("B", os.path.join(IMG, "fundo.png"))
area = (x1 - x0) * (y1 - y0)
info = {"redes_roteadas": len(nets), "ligacoes_MST": len(edges), "comprimento_total_mm": round(tot, 1),
        "maior_celula_mm": round(float(heat.max()), 1), "celula_media_mm": round(float(heat.mean()), 2),
        "mm_por_cm2": round(tot / (area / 100.0), 2),
        "maiores_redes": sorted(((round(sum(math.hypot(a[0] - b[0], a[1] - b[1]) for nn, a, b in edges if nn == n), 1), n) for n in nets), reverse=True)[:8]}
json.dump(info, open(os.path.join(HERE, "roteabilidade_v4.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(info, indent=1))
