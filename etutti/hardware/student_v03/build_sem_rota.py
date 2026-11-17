"""eTutti Student V3: the V2 board re-placed for JLCPCB bottom-side assembly, WITHOUT routing (for approval).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/build_sem_rota.py

Reads the routed V2 board (student_v02/kicad/student_v02.kicad_pcb, never written) and writes
student_v03/kicad/student_v03_sem_rota.kicad_pcb. What it does (all by script, never by hand):

  1. every track and via is removed (the zones are kept, unfilled): the board is shown as a ratsnest;
  2. the dotted outline that followed the keyboard and the inner I/O curve, the V1 alternative USB/AUX
     positions ("E1 v1", "F2 v1") and all the V1 sector labels are removed from the silkscreen;
     "eTutti Student V2" becomes "eTutti Student V3";
  3. everything that was on the top side except the two encoders (and the speaker's wire pads, which are
     plain pads) goes to the BOTTOM: USB-C, the two jacks, the ESD chip, the TVS diode, 4 passives and
     J401 (the screen's connector). The connectors keep their x (they stay at the left edge, facing
     out), the rest is moved to the nearest free spot on the bottom (courtyards, holes, keep-outs);
  4. J401 keeps the cable's exit through a slot in the board (Edge.Cuts) next to the connector;
  5. H101 (Wurth SMT standoff, refused by JLCPCB Economic PCBA) becomes a plain 2.7 mm hole: M2.5 screw
     from the top, 2.5 mm nylon spacer, module, nut;
  6. values: R203 1.8k->2.2k, R501 680k->1M, C307 150nF->100nF (Basic, same 0402 footprints) and the four
     BAT54C -> BAV70 (Basic, same SOT-23 pins: 1 A1, 2 A2, 3 common cathode).
Also writes student_v03/pcb/colocacao.json (what moved where).
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
V2 = os.path.join(HW, "student_v02")
SRC = os.path.join(V2, "kicad", "student_v02.kicad_pcb")
OUT = os.path.join(HERE, "kicad", "student_v03_sem_rota.kicad_pcb")
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
MM = pcbnew.FromMM
TOMM = pcbnew.ToMM
GRAVE = []

TO_BOTTOM = ["J201", "U201", "D201", "J301", "J302", "C308", "R303", "R304", "C210"]
CONNECTORS = {"J201", "J301", "J302"}          # keep x (left edge), search along y only
VALUES = {"R203": ("2.2k", "C25879"), "R501": ("1M", "C26083"), "C307": ("100nF", "C1525"),
          "D202": ("BAV70", "C68978"), "D203": ("BAV70", "C68978"), "D204": ("BAV70", "C68978"),
          "D205": ("BAV70", "C68978")}
MARGIN = 0.3


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def court(fp):
    layer = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
    try:
        bb = fp.GetCourtyard(layer).BBox()
        if bb.GetWidth() > 0:
            return (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetX() + bb.GetWidth()), TOMM(bb.GetY() + bb.GetHeight()))
    except Exception:
        pass
    bb = fp.GetBoundingBox(False)
    return (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetX() + bb.GetWidth()), TOMM(bb.GetY() + bb.GetHeight()))


def hole_boxes(fp, grow=0.7):
    """Through pads and holes reach both sides."""
    out = []
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            bb = p.GetBoundingBox()
            out.append((TOMM(bb.GetX()) - grow, TOMM(bb.GetY()) - grow, TOMM(bb.GetX() + bb.GetWidth()) + grow,
                        TOMM(bb.GetY() + bb.GetHeight()) + grow))
    return out


def overlap(a, b, m=0.0):
    return a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m


def shifted(bb, dx, dy):
    return (bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy)


def obstacles(b, skip):
    """{'F': [boxes], 'B': [boxes]}: courtyards of every part on its side, through holes on both."""
    ob = {"F": [], "B": []}
    for fp in b.GetFootprints():
        r = fp.GetReference()
        if r in skip:
            continue
        if r.startswith(("H", "HG")) and "MountingHole" in str(fp.GetFPID().GetLibItemName()):
            x, y = TOMM(fp.GetX()), TOMM(fp.GetY())
            rad = 3.5           # copper-free ring round the pillars (CLAUDE.md)
            box = (x - rad, y - rad, x + rad, y + rad)
            ob["F"].append(box)
            ob["B"].append(box)
            continue
        side = "F" if fp.GetLayer() == pcbnew.F_Cu else "B"
        ob[side].append(court(fp))
        for hb in hole_boxes(fp):
            ob["F"].append(hb)
            ob["B"].append(hb)
    for z in b.Zones():
        if z.GetIsRuleArea():
            bb = z.GetBoundingBox()
            box = (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetX() + bb.GetWidth()), TOMM(bb.GetY() + bb.GetHeight()))
            ob["F"].append(box)
            ob["B"].append(box)
    return ob


def board_box(b):
    bb = b.GetBoardEdgesBoundingBox()
    return (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetX() + bb.GetWidth()), TOMM(bb.GetY() + bb.GetHeight()))


def flip(fp):
    pos = fp.GetPosition()
    try:
        fp.Flip(pos, pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    except Exception:
        fp.Flip(pos, False)


def main():
    os.makedirs(os.path.join(HERE, "kicad"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "pcb"), exist_ok=True)
    b = pcbnew.LoadBoard(SRC)
    rec = {"moves": {}, "removed": {}}

    # 1. routing out
    n = 0
    for t in list(b.GetTracks()):
        b.Remove(t)
        GRAVE.append(t)
        n += 1
    for z in b.Zones():
        z.UnFill()
    rec["removed"]["trilhas_e_vias"] = n

    # 2. dotted outlines, V1 alternatives, sector labels
    keep_box = (27.0, 13.0, 53.0, 40.0)         # the MicroMod keep-out drawing on B.Silkscreen
    nshape = ntext = 0
    for d in list(b.GetDrawings()):
        L = d.GetLayer()
        kind = type(d).__name__
        if L == pcbnew.Edge_Cuts:
            continue
        if kind == "PCB_TEXT":
            t = d.GetText()
            if t.startswith("eTutti Student"):
                d.SetText("eTutti Student V3")
                continue
            if t.startswith("MicroMod"):
                continue
            b.Remove(d)
            GRAVE.append(d)
            ntext += 1
        elif kind == "PCB_SHAPE" and L == pcbnew.F_SilkS:
            b.Remove(d)
            GRAVE.append(d)
            nshape += 1
        elif kind == "PCB_SHAPE" and L == pcbnew.B_SilkS:
            bb = d.GetBoundingBox()
            box = (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetX() + bb.GetWidth()), TOMM(bb.GetY() + bb.GetHeight()))
            if not overlap(box, keep_box):
                b.Remove(d)
                GRAVE.append(d)
                nshape += 1
    rec["removed"]["tracejados_e_formas"] = nshape
    rec["removed"]["rotulos"] = ntext

    # 6. values (before placement: nothing moves)
    for ref, (val, code) in VALUES.items():
        fp = b.FindFootprintByReference(ref)
        fp.SetValue(val)
        if fp.HasField("Codigo"):
            fp.SetField("Codigo", code)
        rec.setdefault("valores", {})[ref] = [val, code]

    # 5. H101 -> plain hole
    old = b.FindFootprintByReference("H101")
    pos, = [old.GetPosition()]
    b.Remove(old)
    GRAVE.append(old)
    hole = pcbnew.FootprintLoad(os.path.join(KICAD_FP, "MountingHole.pretty"), "MountingHole_2.7mm_M2.5")
    hole.SetReference("H101")
    hole.Reference().SetVisible(False)
    hole.Value().SetVisible(False)
    hole.SetPosition(pos)
    b.Add(hole)
    rec["H101"] = {"x": TOMM(pos.x), "y": TOMM(pos.y), "furo_mm": 2.7}

    # 3. to the bottom
    bx = board_box(b)
    skip = set(TO_BOTTOM)
    placed = []
    for ref in TO_BOTTOM:
        fp = b.FindFootprintByReference(ref)
        x0, y0 = TOMM(fp.GetX()), TOMM(fp.GetY())
        flip(fp)
        ob = obstacles(b, skip - set(placed) | {ref})
        # courtyard of the flipped part at its current position
        c = court(fp)
        best = None
        ring = 0.0
        step = 0.25
        maxr = 60.0
        while ring <= maxr and best is None:
            cands = []
            if ring == 0:
                cands = [(0.0, 0.0)]
            else:
                k = int(ring / step)
                for i in range(-k, k + 1):
                    for sgn in (-1, 1):
                        cands += [(i * step, sgn * ring), (sgn * ring, i * step)]
            for dx, dy in cands:
                if ref in CONNECTORS and abs(dx) > 1e-9:
                    continue
                box = shifted(c, dx, dy)
                lim = (bx[0] - (6 if ref in CONNECTORS else -0.6), bx[1] + 0.6, bx[2] - 0.6, bx[3] - 0.6)
                if box[0] < lim[0] or box[1] < lim[1] or box[2] > lim[2] or box[3] > lim[3]:
                    continue
                if any(overlap(box, o, MARGIN) for o in ob["B"]):
                    continue
                best = (dx, dy)
                break
            ring += step
        if best is None:
            rec["moves"][ref] = {"erro": "sem lugar no fundo"}
            print(ref, "SEM LUGAR")
            continue
        fp.SetPosition(V(x0 + best[0], y0 + best[1]))
        placed.append(ref)
        rec["moves"][ref] = {"de": [round(x0, 2), round(y0, 2), "topo"], "para": [round(x0 + best[0], 2), round(y0 + best[1], 2), "fundo"],
                             "deslocamento_mm": round(math.hypot(*best), 2), "rot": fp.GetOrientationDegrees()}
        print("%-5s (%.2f, %.2f) topo -> (%.2f, %.2f) fundo  d=%.2f mm" % (ref, x0, y0, x0 + best[0], y0 + best[1], math.hypot(*best)))

    # 4. J401 (screen connector) + the slot for its cable. The connector is flipped, then tried at the 4
    # rotations; for each, the nearest free spot (<= 14 mm from where it was) with a free 7 x 2.5 mm slot
    # one cable-length in front of its mouth, on the OLED side (towards smaller y), is taken.
    j = b.FindFootprintByReference("J401")
    x0, y0 = TOMM(j.GetX()), TOMM(j.GetY())
    rot0 = j.GetOrientationDegrees()
    flip(j)
    ob = obstacles(b, {"J401"})
    obs_all = ob["F"] + ob["B"]
    SLOT_W, SLOT_H = 7.0, 2.5
    best = None
    for dr in (0, 90, 180, 270):
        j.SetOrientationDegrees(rot0 + dr) if False else None
        j.SetOrientation(pcbnew.EDA_ANGLE(j.GetOrientationDegrees() + 0, pcbnew.DEGREES_T))
    base_rot = j.GetOrientationDegrees()
    for dr in (0, 90, 180, 270):
        j.SetOrientation(pcbnew.EDA_ANGLE(base_rot + dr, pcbnew.DEGREES_T))
        j.SetPosition(V(x0, y0))
        pads = [p for p in j.Pads() if p.GetNumber() in ("1", "2", "3", "4")]
        px = sum(TOMM(p.GetPosition().x) for p in pads) / 4 - x0
        py = sum(TOMM(p.GetPosition().y) for p in pads) / 4 - y0
        cbx = court(j)
        mid = ((cbx[0] + cbx[2]) / 2 - x0, (cbx[1] + cbx[3]) / 2 - y0)
        dv = (mid[0] - px, mid[1] - py)
        Ld = math.hypot(*dv) or 1.0
        dv = (dv[0] / Ld, dv[1] / Ld)
        half = (abs(dv[0]) * (cbx[2] - cbx[0]) / 2 + abs(dv[1]) * (cbx[3] - cbx[1]) / 2)
        ring = 0.0
        while ring <= 14 and best is None or (best is not None and ring <= best[0] and ring <= 14):
            k = int(ring / 0.5)
            cands = [(0.0, 0.0)] if ring == 0 else [(i * 0.5, sg * ring) for i in range(-k, k + 1) for sg in (-1, 1)] + [(sg * ring, i * 0.5) for i in range(-k, k + 1) for sg in (-1, 1)]
            for dx, dy in cands:
                box = shifted(cbx, dx, dy)
                if box[0] < bx[0] + 0.6 or box[1] < bx[1] + 0.6 or box[2] > bx[2] - 0.6 or box[3] > bx[3] - 0.6:
                    continue
                if any(overlap(box, o, MARGIN) for o in ob["B"]):
                    continue
                # slot in front of the mouth
                for dist in [t * 0.5 for t in range(4, 20)]:
                    sx = x0 + dx + dv[0] * (half + dist)
                    sy = y0 + dy + dv[1] * (half + dist)
                    if abs(dv[1]) > abs(dv[0]):
                        sb = (sx - SLOT_W / 2, sy - SLOT_H / 2, sx + SLOT_W / 2, sy + SLOT_H / 2)
                    else:
                        sb = (sx - SLOT_H / 2, sy - SLOT_W / 2, sx + SLOT_H / 2, sy + SLOT_W / 2)
                    if sb[0] < bx[0] + 1 or sb[2] > bx[2] - 1 or sb[1] < bx[1] + 1 or sb[3] > bx[3] - 1:
                        continue
                    if any(overlap(sb, o, 0.5) for o in obs_all) or overlap(sb, box, 0.3):
                        continue
                    best = (math.hypot(dx, dy), dr, dx, dy, sb, dv)
                    break
                if best:
                    break
            if best:
                break
            ring += 0.5
        if best:
            break
    if best:
        _, dr, dx, dy, sb, dv = best
        j.SetOrientation(pcbnew.EDA_ANGLE(base_rot + dr, pcbnew.DEGREES_T))
        j.SetPosition(V(x0 + dx, y0 + dy))
        pts = [(sb[0], sb[1]), (sb[2], sb[1]), (sb[2], sb[3]), (sb[0], sb[3])]
        for i2 in range(4):
            sh = pcbnew.PCB_SHAPE(b)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(V(*pts[i2]))
            sh.SetEnd(V(*pts[(i2 + 1) % 4]))
            sh.SetLayer(pcbnew.Edge_Cuts)
            sh.SetWidth(MM(0.1))
            b.Add(sh)
        rec["J401"] = {"de": [round(x0, 2), round(y0, 2), "topo"], "para": [round(x0 + dx, 2), round(y0 + dy, 2), "fundo"],
                       "rotacao_extra": dr, "boca": [round(dv[0], 2), round(dv[1], 2)]}
        rec["fenda_do_cabo"] = {"caixa_mm": [round(v, 2) for v in sb], "tamanho_mm": [SLOT_W, SLOT_H]}
        print("J401 ->", rec["J401"], "slot", rec["fenda_do_cabo"])
    else:
        rec["J401"] = {"erro": "sem lugar para conector e fenda"}
        print("J401: SEM LUGAR")

    pcbnew.SaveBoard(OUT, b)
    json.dump(rec, open(os.path.join(HERE, "pcb", "colocacao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec["removed"]))


if __name__ == "__main__":
    main()
