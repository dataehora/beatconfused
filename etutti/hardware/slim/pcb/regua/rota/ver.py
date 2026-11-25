"""Draw a window of a routed board (copper, pads, vias).  Two steps because matplotlib lives in the CadQuery venv, pcbnew in KiCad's python:
   KiCad python:  ver.py dump board.kicad_pcb out.json
   venv python:   ver.py draw out.json out.png x0 y0 x1 y1
"""
import json, sys
mm = 1e-6
def dump(pcb, out):
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    d = {"tracks": [], "vias": [], "pads": [], "zones": []}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); d["vias"].append([p.x*mm, p.y*mm, t.GetWidth(pcbnew.F_Cu)*mm, t.GetDrillValue()*mm, t.GetNetname()])
        else:
            a, e = t.GetStart(), t.GetEnd()
            d["tracks"].append([a.x*mm, a.y*mm, e.x*mm, e.y*mm, t.GetWidth()*mm, "F" if t.GetLayer() == pcbnew.F_Cu else "B", t.GetNetname()])
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            f, bk = p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)
            d["pads"].append([bb.GetX()*mm, bb.GetY()*mm, bb.GetWidth()*mm, bb.GetHeight()*mm, ("T" if f and bk else "F" if f else "B"), p.GetNetname(), p.GetDrillSize().x*mm])
    json.dump(d, open(out, "w"))
def draw(js, out, x0, y0, x1, y1):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    d = json.load(open(js))
    W = 16; fig, ax = plt.subplots(figsize=(W, W * (y1 - y0) / (x1 - x0)))
    COL = {"F": "#d03030", "B": "#3050d0", "T": "k"}
    pt = W * 72 / (x1 - x0)
    for a, b_, c, e, w, L, n in d["tracks"]:
        ax.plot([a, c], [b_, e], color=COL[L], lw=w * pt, solid_capstyle="round", alpha=.55, zorder=3 if L == "B" else 4)
    for x, y, dia, dr, n in d["vias"]:
        ax.add_patch(Circle((x, y), dia / 2, fc="#999", ec="k", lw=.5, zorder=5)); ax.add_patch(Circle((x, y), dr / 2, fc="w", ec="none", zorder=6))
    for x, y, w, h, L, n, dr in d["pads"]:
        ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=COL[L], lw=1, zorder=4))
        if x0 < x + w / 2 < x1 and y0 < y + h / 2 < y1 and n:
            ax.text(x + w / 2, y + h / 2, n[:5], fontsize=6, ha="center", va="center", zorder=7)
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
    fig.savefig(out, dpi=70, bbox_inches="tight")
if __name__ == "__main__":
    if sys.argv[1] == "dump": dump(sys.argv[2], sys.argv[3])
    else: draw(sys.argv[2], sys.argv[3], *map(float, sys.argv[4:8]))
