"""Close-up pictures of a region of the V3 board (pads, tracks, vias, outlines), for looking at the routing.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/vista.py dump [board] [out.json]
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v03/pcb/vista.py draw x0 y0 x1 y1 out.png [layer] [json]

dump writes every pad / track / via / courtyard of the board to JSON (KiCad's python); draw plots one copper layer
(B.Cu default) of a window (mm, KiCad coordinates, y down) with matplotlib (the CadQuery venv).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "kicad", "student_v03.kicad_pcb")
DUMP = os.path.join(HERE, "build", "vista.json")


def dump(board=BOARD, out=DUMP):
    import pcbnew
    M = pcbnew.ToMM
    b = pcbnew.LoadBoard(board)
    d = {"pads": [], "tracks": [], "vias": [], "parts": [], "zones": []}
    for fp in b.GetFootprints():
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if fp.GetSide() == pcbnew.B_Cu else pcbnew.F_CrtYd).BBox()
        d["parts"].append({"ref": fp.GetReference(), "side": fp.GetLayerName(), "x0": M(bb.GetX()), "y0": M(bb.GetY()),
                           "x1": M(bb.GetRight()), "y1": M(bb.GetBottom()), "px": M(fp.GetPosition().x), "py": M(fp.GetPosition().y)})
        for p in fp.Pads():
            sz = p.GetSize()
            d["pads"].append({"ref": fp.GetReference(), "n": p.GetNumber(), "net": p.GetNetname(), "x": M(p.GetPosition().x),
                              "y": M(p.GetPosition().y), "w": M(sz.x), "h": M(sz.y), "rot": p.GetOrientationDegrees(),
                              "layers": [pcbnew.BOARD_GetStandardLayerName(l) if hasattr(pcbnew, "BOARD_GetStandardLayerName") else b.GetLayerName(l)
                                         for l in p.GetLayerSet().Seq()], "drill": M(p.GetDrillSize().x)})
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            d["vias"].append({"net": t.GetNetname(), "x": M(t.GetPosition().x), "y": M(t.GetPosition().y), "d": M(t.GetWidth(pcbnew.F_Cu)),
                              "drill": M(t.GetDrillValue())})
        else:
            d["tracks"].append({"net": t.GetNetname(), "layer": t.GetLayerName(), "x0": M(t.GetStart().x), "y0": M(t.GetStart().y),
                                "x1": M(t.GetEnd().x), "y1": M(t.GetEnd().y), "w": M(t.GetWidth())})
    json.dump(d, open(out, "w"))
    print("dump:", {k: len(v) for k, v in d.items()}, "->", out)


def draw(x0, y0, x1, y1, out, layer="B.Cu", src=DUMP):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    d = json.load(open(src))
    colors = {}
    pal = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#ff7f0e", "#7f7f7f"]
    key = {"GND": "#999999", "USB_DP": "#d62728", "USB_DN": "#1f77b4", "VBUS": "#ff7f0e"}

    def col(n):
        if n in key:
            return key[n]
        if n not in colors:
            colors[n] = pal[len(colors) % len(pal)]
        return colors[n]
    w_in = 14.0
    fig, ax = plt.subplots(figsize=(w_in, w_in * (y1 - y0) / (x1 - x0)))
    for p in d["parts"]:
        if p["side"] == ("B.Cu" if layer == "B.Cu" else "F.Cu"):
            if p["x1"] > x0 and p["x0"] < x1 and p["y1"] > y0 and p["y0"] < y1:
                ax.add_patch(Rectangle((p["x0"], p["y0"]), p["x1"] - p["x0"], p["y1"] - p["y0"], fill=False, ec="#888", lw=0.6, ls="--"))
                ax.text(p["px"], p["py"], p["ref"], fontsize=7, color="#444", ha="center")
    for t in d["tracks"]:
        if t["layer"] == layer:
            ax.plot([t["x0"], t["x1"]], [t["y0"], t["y1"]], color=col(t["net"]), lw=t["w"] * w_in * 72 / (x1 - x0),
                    solid_capstyle="round", alpha=0.85)
    for p in d["pads"]:
        if layer in p["layers"] and x0 - 3 < p["x"] < x1 + 3 and y0 - 3 < p["y"] < y1 + 3:
            w, h = (p["w"], p["h"]) if round(p["rot"]) % 180 == 0 else (p["h"], p["w"])
            ax.add_patch(Rectangle((p["x"] - w / 2, p["y"] - h / 2), w, h, fc=col(p["net"]), ec="k", lw=0.3, alpha=0.55))
            if p["w"] > 0.3:
                ax.text(p["x"], p["y"], "%s.%s" % (p["ref"], p["n"]), fontsize=4.5, ha="center", va="center")
    for v in d["vias"]:
        ax.add_patch(Circle((v["x"], v["y"]), v["d"] / 2, fc="none", ec=col(v["net"]), lw=1))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.2)
    ax.set_title("%s (%g..%g, %g..%g mm)" % (layer, x0, x1, y0, y1))
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print("png:", out)


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(*sys.argv[2:4])
    else:
        a = sys.argv[2:]
        draw(float(a[0]), float(a[1]), float(a[2]), float(a[3]), a[4], a[5] if len(a) > 5 else "B.Cu", a[6] if len(a) > 6 else DUMP)
