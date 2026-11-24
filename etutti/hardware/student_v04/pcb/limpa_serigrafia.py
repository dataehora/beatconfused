"""eTutti Student V4 (R15V4, item 1): cleans the silkscreen of the MAIN board. Silkscreen ONLY: no track, pad, via, zone or position is touched.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/limpa_serigrafia.py [board.kicad_pcb ...]

Default boards: kicad/student_v04.kicad_pcb and kicad/student_v04_roteada.kicad_pcb (the *_3d copy is made again by pcb/liga_modelos.py).
Idempotent (run twice = same result). What it does:
  1. every custom field of every footprint (Codigo, LCSC, Montagem, Altura_mm, Cabe_sob_cartao, ...) and the Reference/Value fields go to the
     Fab layer of the footprint's side (F.Fab / B.Fab) and are hidden (data stays in the file, BOM/CPL and assembly drawings read it);
  2. silkscreen lines of the footprints below JLCPCB's 0.15 mm minimum line width are widened to 0.15 mm;
  3. all board-level silkscreen text is removed and the wanted labels are added (name/version, connector labels, SPK +/-, PROG), each placed
     by a search on a 0.25 mm grid around its anchor, where it touches no pad (0.3 mm clear; JLCPCB asks 0.15), no hole, no other silkscreen item,
     no other label and stays 1.5 mm inside the outline. Text 1.0 mm high, 0.15 mm stroke (JLCPCB minimums: height 1.0 mm, stroke 0.15 mm).
"""
import os
import sys
import json
import math

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.normpath(os.path.join(HERE, "..", "kicad"))
DEFAULT = [os.path.join(KI, "student_v04.kicad_pcb"), os.path.join(KI, "student_v04_roteada.kicad_pcb")]
MM = pcbnew.FromMM
GRAVE = []
H = 1.0          # text height, JLCPCB minimum
T = 0.15         # stroke, JLCPCB minimum
MIN_LINE = 0.15
PAD_CLEAR = 0.30
EDGE = 1.5

# (text, anchor reference or (x, y), side, allowed angles); the search moves each label to the nearest free spot
LABELS = [
    ("FILEIRA 1\nROW 1", "J601", "B", (0, 90)),
    ("FILEIRA 2\nROW 2", "J602", "B", (0, 90)),
    ("FILEIRA 3\nROW 3", "J603", "B", (0, 90)),
    ("FILEIRA 4\nROW 4", (74.0, 16.0), "B", (90, 0)),   # beside J604 there is J202: the label goes just above the connector
    ("OLED", "J401", "B", (0, 90)),
    ("BAT", "J202", "B", (0, 90)),
    ("USB", "J201", "B", (0, 90)),
    ("FONE\nPHONES", "J301", "B", (0, 90)),
    ("ENTRADA\nIN (MIC)", "J302", "B", (0, 90)),
    ("PROG", "SW403", "B", (0, 90)),
    ("+", (47.0, 91.5), "F", (0,)),
    ("-", (53.0, 91.5), "F", (0,)),
    ("SPK", (50.0, 90.5), "F", (0,)),
    ("eTutti Student V4\nplaca principal", (41.0, 72.0), "F", (0,)),
    ("STUDENT V4", (41.0, 72.0), "B", (0,)),
]


def sil(side):
    return pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS


def make_text(b, txt, side, ang, x, y):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(sil(side))
    t.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H)))
    t.SetTextThickness(MM(T))
    t.SetMirrored(side == "B")
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetTextAngleDegrees(ang)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    return t


def rect_of(bb, grow=0.0):
    g = MM(grow)
    return (bb.GetX() - g, bb.GetY() - g, bb.GetX() + bb.GetWidth() + g, bb.GetY() + bb.GetHeight() + g)


def hit(a, c):
    return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])


def obstacles(b, side):
    """rectangles (nm) a label on that side must not touch"""
    cu = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
    out = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(cu) or p.GetDrillSizeX() > 0:
                out.append(rect_of(p.GetBoundingBox(), PAD_CLEAR))
        for g in fp.GraphicalItems():
            if g.GetLayer() == sil(side) and g.GetClass() == "PCB_SHAPE":
                out.append(rect_of(g.GetBoundingBox(), 0.2))
    for t in b.Tracks():
        if t.GetClass() == "PCB_VIA":
            out.append(rect_of(t.GetBoundingBox(), 0.2))
    return out


def inside(b, r, margin):
    bb = b.GetBoardEdgesBoundingBox()
    m = MM(margin)
    if not (r[0] >= bb.GetX() + m and r[1] >= bb.GetY() + m and r[2] <= bb.GetRight() - m and r[3] <= bb.GetBottom() - m):
        return False
    # rounded corners: keep the four corners of the rectangle away from the corner arcs (radius 6 mm, board R6)
    rad = MM(6.0)
    for cx, cy, sx, sy in ((bb.GetX(), bb.GetY(), 1, 1), (bb.GetRight(), bb.GetY(), -1, 1), (bb.GetX(), bb.GetBottom(), 1, -1), (bb.GetRight(), bb.GetBottom(), -1, -1)):
        px = r[0] if sx > 0 else r[2]
        py = r[1] if sy > 0 else r[3]
        dx, dy = (px - cx) * sx, (py - cy) * sy
        if dx < rad and dy < rad:
            ccx, ccy = rad, rad
            if math.hypot(dx - ccx, dy - ccy) > rad - MM(margin) and (dx < ccx and dy < ccy):
                return False
    return True


def place(b, txt, anchor, side, angles, placed):
    if isinstance(anchor, str):
        a = b.FindFootprintByReference(anchor).GetPosition()
        ax, ay = pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)
    else:
        ax, ay = anchor
    obs = obstacles(b, side) + placed.get(side, [])
    best = None
    n = 120
    for iy in range(-n, n + 1):
        for ix in range(-n, n + 1):
            x, y = ax + ix * 0.25, ay + iy * 0.25
            d = math.hypot(x - ax, y - ay)
            if best and d >= best[0]:
                continue
            for ang in angles:
                t = make_text(b, txt, side, ang, x, y)
                r = rect_of(t.GetBoundingBox(), 0.15)
                if not inside(b, r, EDGE) or any(hit(r, o) for o in obs):
                    continue
                best = (d, x, y, ang, r)
                break
    if best is None:
        raise SystemExit("no free spot for label %r" % txt)
    return best


def fix_library_silk(b):
    """two library silk items the KiCad silkscreen checks flag: J201's outline pokes past the board edge (trimmed), J101's pin-1 dot sits on
    U201's pad 1 (moved to the nearest spot clear of every pad, still beside J101 pad 1)"""
    j = b.FindFootprintByReference("J201")
    edge = b.GetBoardEdgesBoundingBox().GetX() + MM(0.7)
    for g in list(j.GraphicalItems()):
        if g.GetClass() == "PCB_SHAPE" and g.GetLayer() == pcbnew.B_SilkS and g.GetBoundingBox().GetX() < edge:
            j.Remove(g)
            GRAVE.append(g)   # pcbnew gotcha: keep removed items alive
    j = b.FindFootprintByReference("J101")
    pad1 = next(p for p in j.Pads() if p.GetNumber() == "1")
    for g in j.GraphicalItems():
        if g.GetClass() == "PCB_SHAPE" and g.GetShape() == pcbnew.SHAPE_T_CIRCLE and g.GetLayer() == pcbnew.B_SilkS:
            r = g.GetRadius()
            obs = obstacles(b, "B")
            best = None
            for iy in range(-16, 17):
                for ix in range(-16, 17):
                    cx, cy = pad1.GetX() + MM(ix * 0.25) - MM(1.5), pad1.GetY() + MM(iy * 0.25)
                    box = (cx - r - MM(0.15), cy - r - MM(0.15), cx + r + MM(0.15), cy + r + MM(0.15))
                    if any(hit(box, o) for o in obs):
                        continue
                    d = math.hypot(cx - pad1.GetX(), cy - pad1.GetY())
                    if best is None or d < best[0]:
                        best = (d, cx, cy)
            if best is None:
                raise SystemExit("no spot for J101 pin 1 dot")
            g.SetStart(pcbnew.VECTOR2I(int(best[1]), int(best[2])))
            g.SetEnd(pcbnew.VECTOR2I(int(best[1]), int(best[2] + r)))


def clean(path, report):
    b = pcbnew.LoadBoard(path)
    n_fields = n_lines = 0
    for fp in b.GetFootprints():
        fab = pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab
        for f in fp.GetFields():
            if f.GetName() in ("Datasheet", "Description"):
                continue
            if f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) or f.IsVisible():
                if f.GetName() not in ("Reference", "Value") or f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    f.SetLayer(fab)
                    f.SetVisible(False)
                    n_fields += 1
        for g in fp.GraphicalItems():
            if g.GetClass() == "PCB_SHAPE" and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and g.GetWidth() < MM(MIN_LINE):
                g.SetWidth(MM(MIN_LINE))
                n_lines += 1
    fix_library_silk(b)
    # board-level silkscreen text: remove, then add the wanted labels
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Remove(d)
            GRAVE.append(d)
    placed, rows = {}, []
    for txt, anchor, side, angs in LABELS:
        d, x, y, ang, r = place(b, txt, anchor, side, angs, placed)
        t = make_text(b, txt, side, ang, x, y)
        b.Add(t)
        placed.setdefault(side, []).append(rect_of(t.GetBoundingBox(), 0.3))
        rows.append({"texto": txt.replace("\n", " / "), "lado": side, "x": round(x, 2), "y": round(y, 2), "angulo": ang,
                     "ancora": anchor if isinstance(anchor, str) else list(anchor), "deslocamento_mm": round(d, 2)})
    b.Save(path)
    report[os.path.basename(path)] = {"campos_para_Fab": n_fields, "linhas_alargadas": n_lines, "rotulos": rows}


def main():
    boards = sys.argv[1:] or DEFAULT
    report = {}
    for p in boards:
        clean(p, report)
    json.dump(report, open(os.path.join(HERE, "build", "limpa_serigrafia.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
