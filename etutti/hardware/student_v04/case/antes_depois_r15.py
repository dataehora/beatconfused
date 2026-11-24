"""R15V4: BEFORE / AFTER of the regions that had the thin walls: top views (height map of the tray, 0.25 mm) of the left ends of the four ruler steps (x 76-126) and of the right ends
(x 170-245), the flagged pieces of the scan boxed in red on the BEFORE panels. -> renders/base_antes_depois_r15.png"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import varredura_r15 as V
import varredura_fig_r15 as VF
OUT = os.path.join(HERE, "out")
def load(tag):
    ox, oy, h = VF.heightmap(os.path.join(OUT, "r4_32_base_%s.stl" % tag), os.path.join(OUT, "hm_base_%s.npy" % tag))
    h = h[0] if h.ndim == 3 else h
    ox, oy = float(np.ravel(ox)[0]), float(np.ravel(oy)[0])
    nx, ny = h.shape
    return ox + np.arange(nx) * V.VOX, -(oy + np.arange(ny) * V.VOX), h
def main():
    fig, axs = plt.subplots(2, 2, figsize=(22, 16))
    wins = [(76, 126, -2, 100, "pontas esquerdas das 4 réguas"), (170, 245, -2, 100, "pontas direitas e túneis")]
    sc = {t: json.load(open(os.path.join(OUT, "varredura_r15_%s.json" % t)))[0]["finas"] for t in ("antes", "depois")}
    for c, (x0, x1, y0, y1, nm) in enumerate(wins):
        for r, tag in enumerate(("antes", "depois")):
            x, y, h = load(tag)
            ax = axs[r, c]
            ax.pcolormesh(x, y, h.T, cmap="Greys", vmin=-12, vmax=8, shading="auto")
            ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
            for f in sc[tag]:
                if f["x"][1] >= x0 and f["x"][0] <= x1 and f["x"][0] >= 79 and f["z"][0] < 0:
                    ax.add_patch(Rectangle((f["x"][0] - 0.5, f["y"][0] - 0.5), f["x"][1] - f["x"][0] + 1, f["y"][1] - f["y"][0] + 1, fill=False, ec="red", lw=1.4))
            ax.set_title("%s: %s (cinza mais escuro = mais baixo; vermelho = parede/haste < 1,5 mm achada pela varredura)" % (tag.upper(), nm), fontsize=11)
    fp = os.path.join(HERE, "renders", "base_antes_depois_r15.png")
    plt.tight_layout(); plt.savefig(fp, dpi=90); print(fp)
main()
