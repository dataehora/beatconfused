"""R15V4 item 4.1: figure of the scan: top view (height map of the solid) of the base and the lid with every flagged group boxed and numbered.
    C:/Users/julia/.venvs/cadquery/Scripts/python.exe case/varredura_fig_r15.py <tag> [x0 x1 y0 y1]     tag: antes | depois  (reads out/varredura_r15_<tag>.json and the STLs)"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import varredura_r15 as V
OUT = os.path.join(HERE, "out")


def heightmap(path, cache):
    if os.path.exists(cache):
        z = np.load(cache)
        return z[0], z[1], z[2:]
    a, org = V.voxelise(path)
    n = a.shape[2]
    zi = np.where(a.any(axis=2), n - 1 - np.argmax(a[:, :, ::-1], axis=2), -1)
    h = np.where(zi >= 0, org[2] + (zi + 0.5) * V.VOX, np.nan)
    np.save(cache, np.stack([np.full(h.shape, org[0]), np.full(h.shape, org[1]), h]))
    return org[0], org[1], np.array([h])


def main():
    tag = sys.argv[1]
    win = [float(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else None
    res = json.load(open(os.path.join(OUT, "varredura_r15_%s.json" % tag), encoding="utf-8"))
    fig, axs = plt.subplots(2, 1, figsize=(24, 20)) if win is None else plt.subplots(1, 1, figsize=(16, 10))
    axs = np.atleast_1d(axs)
    for ax, r in zip(axs, res if win is None else res[:1]):
        nm = r["peca"]
        p = os.path.join(OUT, "r4_32_%s_%s.stl" % (nm, tag)) if tag in ("antes", "depois") else os.path.join(OUT, "r4_32_%s.stl" % nm)
        cache = os.path.join(OUT, "hm_%s_%s.npy" % (nm, tag))
        ox, oy, h = heightmap(p, cache)
        h = h[0] if h.ndim == 3 else h
        nx, ny = h.shape
        x = ox + np.arange(nx) * V.VOX
        y = -(oy + np.arange(ny) * V.VOX)
        ax.pcolormesh(x, y, h.T, cmap="Greys", vmin=-12, vmax=22, shading="auto")
        ax.set_aspect("equal")
        for f in r["finas"]:
            ax.add_patch(Rectangle((f["x"][0] - 0.4, f["y"][0] - 0.4), f["x"][1] - f["x"][0] + 0.8, f["y"][1] - f["y"][0] + 0.8, fill=False, ec="red", lw=1.2))
            ax.text(f["x"][0], f["y"][1] + 0.8, str(f["n"]), color="red", fontsize=9, fontweight="bold")
        for f in r["esbeltas"]:
            ax.add_patch(Rectangle((f["x"][0], f["y"][0]), f["x"][1] - f["x"][0], f["y"][1] - f["y"][0], fill=False, ec="blue", lw=1.5, ls="--"))
        ax.set_title("%s (%s): vermelho = parede/pino < 1,5 mm (numerado); azul tracejado = poste esbelto (altura > 3 x largura). Vista de cima, y para o jogador" % (nm, tag))
        ax.invert_yaxis()
        if win:
            ax.set_xlim(win[0], win[1]); ax.set_ylim(win[3], win[2])
    plt.tight_layout()
    suf = "" if win is None else "_zoom"
    fp = os.path.join(HERE, "renders", "varredura_r15_%s%s.png" % (tag, suf))
    plt.savefig(fp, dpi=110)
    print(fp)


if __name__ == "__main__":
    main()
