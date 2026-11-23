"""Desenha a placa inteira (ou uma janela) com as redes escolhidas em destaque: B.Cu cheio, F.Cu tracejado, vias em circulo.
    "C:/Program Files/KiCad/10.0/bin/python.exe" vista.py dump <placa.kicad_pcb> build/vista.json
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" vista_redes.py saida.png x0 y0 x1 y1 REDE1,REDE2 [json]   (REDE vazia = todas, cores por rede)
y para baixo, x como na placa (sem espelhar): como as figuras do posicionamento 'vistas de cima' (topo) menos o espelho do fundo."""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6])
sel = [s for s in sys.argv[6].split(",") if s] if len(sys.argv) > 6 else []
d = json.load(open(sys.argv[7] if len(sys.argv) > 7 else os.path.join(HERE, "build", "vista.json")))
pal = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#ff7f0e", "#7f7f7f"]
cores = {}
def col(n):
    if n == "GND": return "#bbbbbb"
    if n not in cores: cores[n] = pal[len(cores) % len(pal)]
    return cores[n]
def forte(n): return (not sel) or n in sel
w_in = 14.0
fig, ax = plt.subplots(figsize=(w_in, w_in * (y1 - y0) / (x1 - x0)))
k = w_in * 72 / (x1 - x0)
for p in d["parts"]:
    if p["x1"] > x0 and p["x0"] < x1 and p["y1"] > y0 and p["y0"] < y1:
        ax.add_patch(Rectangle((p["x0"], p["y0"]), p["x1"] - p["x0"], p["y1"] - p["y0"], fill=False, ec="#999", lw=0.5, ls="--"))
        ax.text(p["px"], p["py"], p["ref"], fontsize=6, color="#555", ha="center")
for t in d["tracks"]:
    if max(t["x0"], t["x1"]) < x0 or min(t["x0"], t["x1"]) > x1 or max(t["y0"], t["y1"]) < y0 or min(t["y0"], t["y1"]) > y1: continue
    f = forte(t["net"])
    if os.environ.get('CAMADA') and t['layer'] != os.environ['CAMADA']: continue
    ax.plot([t["x0"], t["x1"]], [t["y0"], t["y1"]], color=col(t["net"]) if f else "#cccccc", lw=max(0.4, t["w"] * k), solid_capstyle="round",
            alpha=0.9 if f else 0.4, ls="-" if t["layer"] == "B.Cu" else (0, (2, 1.2)))
for p in d["pads"]:
    if x0 - 3 < p["x"] < x1 + 3 and y0 - 3 < p["y"] < y1 + 3:
        w, h = (p["w"], p["h"]) if round(p["rot"]) % 180 == 0 else (p["h"], p["w"])
        ax.add_patch(Rectangle((p["x"] - w / 2, p["y"] - h / 2), w, h, fc=col(p["net"]) if forte(p["net"]) else "#e8e8e8", ec="k", lw=0.3, alpha=0.6))
        if forte(p["net"]) and sel and p["w"] > 0.3:
            ax.text(p["x"], p["y"], "%s.%s" % (p["ref"], p["n"]), fontsize=5, ha="center", va="center")
for v in d["vias"]:
    ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, fc="none", ec=col(v["net"]) if forte(v["net"]) else "#aaaaaa", lw=0.9))
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal"); ax.grid(True, lw=0.2)
ax.set_title("%s  [cheio = B.Cu, tracejado = F.Cu]" % (",".join(sel) or "todas as redes"))
fig.savefig(out, dpi=100, bbox_inches="tight"); print("png:", out)
