"""Stage 6 of the ruler routing: pictures of the routed R8 ruler, front (key side) and back (parts side), with the NOTE NAME of every key.

    KiCad python:  imagens.py dump  board.kicad_pcb  build/regua_geom.json
    venv python:   imagens.py draw  build/regua_geom.json  ../img/            -> regua_frente.png, regua_verso.png, regua_cabeca_verso.png

One R8 ruler serves the four rows (SPEC R8SL); each key position k = 1..8 carries four notes, one per row (case/layout_slim.py NOTES):
the picture names the position (K1..K8) and lists the four notes under it ("F1 A3 / F2 G3 / F3 G#3 / F4 F#3": row, note).
Front = the ruler seen from above (the keys side): the GND pour, the key holes, the pegs, the M2 holes. Back = seen from below (mirrored left-right as a
turned-over board), the parts, the tracks, the vias. Copper colours: red F.Cu, blue B.Cu.
"""
import json
import os
import sys

mm = 1e-6
HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = [["A3", "C4", "D#4", "F#4", "A4", "C5", "D#5", "F#5"],
         ["G3", "A#3", "C#4", "E4", "G4", "A#4", "C#5", "E5"],
         ["G#3", "B3", "D4", "F4", "G#4", "B4", "D5", "F5"],
         ["F#3", "A3", "C4", "D#4", "F#4", "A4", "C5", "D#5"]]
SHARP = lambda n: "#" in n


def dump(pcb, out):
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    d = {"tracks": [], "vias": [], "pads": [], "refs": [], "zones": {"F": [], "B": []}, "outline": [0, 0, 0, 0]}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            d["vias"].append([p.x * mm, p.y * mm, t.GetWidth(pcbnew.F_Cu) * mm, t.GetDrillValue() * mm, t.GetNetname()])
        else:
            a, e = t.GetStart(), t.GetEnd()
            d["tracks"].append([a.x * mm, a.y * mm, e.x * mm, e.y * mm, t.GetWidth() * mm, "F" if t.GetLayer() == pcbnew.F_Cu else "B", t.GetNetname()])
    for fp in b.GetFootprints():
        c = fp.GetPosition()
        d["refs"].append([fp.GetReference(), c.x * mm, c.y * mm, "B" if fp.GetLayer() == pcbnew.B_Cu else "F"])
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            f, bk = p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)
            d["pads"].append([bb.GetX() * mm, bb.GetY() * mm, bb.GetWidth() * mm, bb.GetHeight() * mm, "T" if f and bk else "F" if f else "B", p.GetNetname(),
                              p.GetDrillSize().x * mm, p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH])
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        L = z.GetLayer()
        ps = z.GetFilledPolysList(L)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            pts = [[o.CPoint(k).x * mm, o.CPoint(k).y * mm] for k in range(o.PointCount())]
            holes = []
            for h in range(ps.HoleCount(i)):
                ho = ps.Hole(i, h)
                holes.append([[ho.CPoint(k).x * mm, ho.CPoint(k).y * mm] for k in range(ho.PointCount())])
            d["zones"]["F" if L == pcbnew.F_Cu else "B"].append([pts, holes])
    bb = b.GetBoardEdgesBoundingBox()
    d["outline"] = [bb.GetLeft() * mm, bb.GetTop() * mm, bb.GetRight() * mm, bb.GetBottom() * mm]
    json.dump(d, open(out, "w"))


def draw(js, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Polygon
    d = json.load(open(js))
    x0, y0, x1, y1 = d["outline"]
    keys = [r for r in d["refs"] if r[0].startswith("SW")]
    keys.sort(key=lambda r: r[1])
    os.makedirs(outdir, exist_ok=True)

    def canvas(title, window=None, w=20):
        wx0, wy0, wx1, wy1 = window or (x0 - 1, y0 - 1, x1 + 1, y1 + 1)
        fig, ax = plt.subplots(figsize=(w, w * (wy1 - wy0) / (wx1 - wx0) + 0.8))
        ax.set_title(title, fontsize=11, loc="left")
        return fig, ax, (wx0, wy0, wx1, wy1)

    def flip(x):  # back view: the board turned over left-right
        return x0 + x1 - x

    def frame(ax, win, back):
        wx0, wy0, wx1, wy1 = win
        if back:
            ax.set_xlim(wx1, wx0)          # turned over: the x axis runs right to left, the text stays readable
        else:
            ax.set_xlim(wx0, wx1)
        ax.set_ylim(wy1, wy0)
        ax.set_aspect("equal")
        ax.axis("off")

    def X(x, back):
        return x

    def key_label(ax, kx, ky, k, back):
        # notes of the 4 rows at this position, in the key square (pitch 18.5 -> 14 square hole)
        ax.add_patch(Rectangle((X(kx, back) - 7, ky - 7), 14, 14, fc="none", ec="#444", lw=0.8, ls="--", zorder=8))
        ax.text(X(kx, back), ky - 4.8, "posicao %d" % k, ha="center", va="center", fontsize=8, color="#222", zorder=9)
        for r in range(4):
            n = NOTES[r][k - 1]
            ax.text(X(kx, back), ky - 2.6 + r * 2.0, "fileira %d  %s" % (r + 1, n), ha="center", va="center", fontsize=8, zorder=9,
                    color="#fff" if SHARP(n) else "#111",
                    bbox=dict(boxstyle="round,pad=0.15", fc="#222" if SHARP(n) else "#fff", ec="#666", lw=0.4))

    def tracks(ax, back, layers):
        pt = 20 * 72 / (x1 - x0 + 2)
        for a, b, c, e, w, L, n in d["tracks"]:
            if L in layers:
                ax.plot([X(a, back), X(c, back)], [b, e], color="#d03030" if L == "F" else "#3050d0", lw=w * pt, solid_capstyle="round", alpha=0.85, zorder=4 if L == "B" else 3)
        for x, y, dia, dr, n in d["vias"]:
            ax.add_patch(Circle((X(x, back), y), dia / 2, fc="#bbb", ec="k", lw=0.4, zorder=6))
            ax.add_patch(Circle((X(x, back), y), dr / 2, fc="w", ec="none", zorder=7))

    def pads(ax, back, layer):
        for x, y, w, h, L, n, dr, npth in d["pads"]:
            if npth:
                ax.add_patch(Circle((X(x + w / 2, back), y + h / 2), dr / 2, fc="w", ec="#222", lw=0.8, zorder=7))
                continue
            if L in (layer, "T"):
                ax.add_patch(Rectangle((x, y), w, h, fc="#e7c36a", ec="#a07f1a", lw=0.3, zorder=5))

    def pour(ax, back, layer):
        for pts, holes in d["zones"][layer]:
            ax.add_patch(Polygon([(X(p[0], back), p[1]) for p in pts], fc="#f3b0b0" if layer == "F" else "#b0c0f3", ec="none", alpha=0.45, zorder=1))
            for h in holes:
                ax.add_patch(Polygon([(X(p[0], back), p[1]) for p in h], fc="w", ec="none", zorder=2))

    # ---- front (key side): the top, F.Cu: pour + tracks on F.Cu, key squares with the notes
    fig, ax, win = canvas("Regua R8 - FRENTE (lado das teclas, F.Cu). Quatro notas por posicao: uma regua serve as 4 fileiras (a fileira muda a altura do degrau, nao a regua).")
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f4f1e3", ec="#2a6", lw=1.2, zorder=0))
    pour(ax, False, "F")
    tracks(ax, False, ("F",))
    pads(ax, False, "F")
    for i, k in enumerate(keys):
        key_label(ax, k[1], k[2], i + 1, False)
    frame(ax, win, False)
    fig.savefig(os.path.join(outdir, "regua_frente.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    # ---- back (parts side), turned over left-right: B.Cu, pads, parts references
    fig, ax, win = canvas("Regua R8 - VERSO (lado das pecas, B.Cu), vista de baixo (placa virada: J1 a direita, posicao 1 a direita). Mesmas notas por posicao.")
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f4f1e3", ec="#2a6", lw=1.2, zorder=0))
    pour(ax, True, "B")
    tracks(ax, True, ("B", "F"))
    pads(ax, True, "B")
    for r in d["refs"]:
        if r[3] == "B" and r[0][0] in "UJ":
            ax.text(r[1], r[2] + (3.3 if r[0][0] == "U" and r[0] != "U9" else 4.8 if r[0] == "U9" else 0), r[0], fontsize=7, ha="center", color="#222", zorder=10)
    for i, k in enumerate(keys):
        key_label(ax, k[1], k[2], i + 1, True)
    frame(ax, win, True)
    fig.savefig(os.path.join(outdir, "regua_verso.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    # ---- zoom of the head (J1, U9) on the back, no mirror: for the review
    win = (20, 22.4, 48, 37.6)
    fig, ax, win = canvas("Cabeca da regua (J1, U9, C9, C10 e o 1o sensor) - verso, sem espelhar", win, 18)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f4f1e3", ec="#2a6", lw=1.2, zorder=0))
    pour(ax, False, "B")
    tracks_pt = 18 * 72 / (win[2] - win[0])
    for a, b, c, e, w, L, n in d["tracks"]:
        ax.plot([a, c], [b, e], color="#d03030" if L == "F" else "#3050d0", lw=w * tracks_pt, solid_capstyle="round", alpha=0.8, zorder=4 if L == "B" else 3)
    for x, y, dia, dr, n in d["vias"]:
        ax.add_patch(Circle((x, y), dia / 2, fc="#bbb", ec="k", lw=0.4, zorder=6))
        ax.add_patch(Circle((x, y), dr / 2, fc="w", ec="none", zorder=7))
    for x, y, w, h, L, n, dr, npth in d["pads"]:
        if npth:
            ax.add_patch(Circle((x + w / 2, y + h / 2), dr / 2, fc="w", ec="#222", lw=0.8, zorder=7))
        elif L in ("B", "T"):
            ax.add_patch(Rectangle((x, y), w, h, fc="#e7c36a", ec="#a07f1a", lw=0.3, zorder=5))
            if win[0] < x < win[2] and win[1] < y < win[3] and n:
                ax.text(x + w / 2, y + h / 2, n[:5], fontsize=5, ha="center", va="center", zorder=8)
    frame(ax, win, False)
    fig.savefig(os.path.join(outdir, "regua_cabeca_verso.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)
    # ---- the grade (FR-4 1.2 mm, 8 square holes with dog-bone reliefs, 2 M2 holes with the countersink) from build/grade_geom.json written by grade.py
    gj = os.path.join(HERE, "build", "grade_geom.json")
    if os.path.exists(gj):
        g = json.load(open(gj))
        fig, ax = plt.subplots(figsize=(20, 3.2))
        ax.set_title("Grade FR-4 1,2 mm, %.1f x %.1f (lado das teclas para cima): 8 furos quadrados de 14,00 com dog-bone nos cantos; %d furos M2 de 2,2 sem escareado; sem cobre" % (g["contorno"]["w"], g["contorno"]["h"], len(g["m2"])), fontsize=10, loc="left")
        cx0 = min(min(q[1], q[3]) for q in g["segs"]); cx1 = max(max(q[1], q[3]) for q in g["segs"]); cy0 = min(min(q[2], q[4]) for q in g["segs"]); cy1 = max(max(q[2], q[4]) for q in g["segs"])
        ax.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fc="#e9dfc5", ec="none"))
        for sh, a, b_, c, e in g["segs"]:
            ax.plot([a, c], [b_, e], color="#222", lw=0.7)
        for h in g["furos"]:
            ax.add_patch(Rectangle((h["cx"] - 7, h["cy"] - 7), 14, 14, fc="w", ec="none", zorder=0.5))
        for m in g["m2"]:
            ax.add_patch(Circle((m["x"], m["y"]), 2.2, fc="none", ec="#b33", lw=0.8, ls="--", zorder=3))
            ax.add_patch(Circle((m["x"], m["y"]), m["furo_mm"] / 2, fc="w", ec="#222", lw=0.8, zorder=3))
        ax.set_xlim(cx0 - 2, cx1 + 2); ax.set_ylim(cy1 + 2, cy0 - 2); ax.set_aspect("equal"); ax.axis("off")
        fig.savefig(os.path.join(outdir, "grade.png"), dpi=110, bbox_inches="tight")
        plt.close(fig)
    print("imagens em", outdir)


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
    else:
        draw(sys.argv[2], sys.argv[3])
