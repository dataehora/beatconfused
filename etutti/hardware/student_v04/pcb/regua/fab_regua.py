"""eTutti Student V4 (R4V4): the grade-regua (1.6 mm FR-4, no assembly) and the panels of 5 (grade-regua and ruler).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/regua/fab_regua.py

1. kicad/regua/student_v04_grade_regua.kicad_pcb (one strip) and ..._painel.kicad_pcb (5 strips, ready to order): 73.6 x 14.0 x 1.6 mm
   FR-4, 4 square openings 14.00 (R 0.5, the router's radius) at 9.25 + 18.5 k (nominal frame), the post notches of the ruler, bare FR-4 under the mask
   (no copper, no net, no assembly), name on the back. Gerbers + drill in fab/.
2. kicad/regua/student_v04_regua_painel.kicad_pcb: the ruler panel (5 strips, copies of the placed ruler with whatever tracks it has).
   NOT routed yet (the 'roteamento' agent routes the single ruler after the portao P; rerun this script to replicate the routing).
   Gerbers go to fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/ only as a geometry check.
Panel: 5 mm rails on four sides (3 mm on the grade-regua panel, which is not assembled and must stay under 100 mm), strips 2.0 mm apart held by two 3 mm tabs per long edge, 3 mouse bites (D 0.5, pitch 0.9) per tab,
4 tooling holes D 2.0 in the rails, 3 fiducials (1 mm copper, 2 mm mask) on the ruler panel's bottom rail. (conferir com a JLCPCB)
"""
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, PCB)
sys.path.insert(0, HERE)
import posiciona_regua as PR  # noqa: E402
if os.environ.get("REGUA_BOARD"):                     # R11V4: the routed board (posiciona_regua.py rebuilds the unrouted one from scratch: never over a routed board)
    PR.OUT = os.path.abspath(os.environ["REGUA_BOARD"])

HW = os.path.normpath(os.path.join(PCB, ".."))
KD = os.path.join(HW, "kicad", "regua")
FAB = os.path.join(HW, "fab")
BUILD = os.path.join(HERE, "build")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
V = PR.V
U0, U1, VB, VF = PR.U0, PR.U1, PR.VB, PR.VF
KEYS = PR.KEYS
RAIL, GAP, TABW = 5.0, 2.0, 3.0
# R11V4: R8 (REGUA_N=8) has 3 tabs per long edge (back edge flat spans [1+18.5k, 17.5+18.5k]; the front edge is flat); N = strips per panel
TAB_U = (16.0, 65.0) if PR.NPOS == 4 else (14.0, 83.0, 138.0)    # 14, not 10: the mouse bites at u 10 sat on J1's mounting pad (back edge)
N = int(os.environ.get("PAINEL_N", "5"))
MODO = os.environ.get("MODO", "ambos")      # grade | regua | ambos
TAGP = "R%d_painel_de_%d" % (PR.NPOS, N)
STRIP_W, STRIP_H = U1 - U0, VF - VB
PW = RAIL + GAP + STRIP_W + GAP + RAIL
PH = RAIL + GAP + N * STRIP_H + (N - 1) * GAP + GAP + RAIL
GRAVE = []


def cfg(vb, vf, rail=5.0):
    """The strip's width: the ruler is 14.0 (v -7..7); the grade-regua must be wider than its 14.00 openings (16.0, v -8..8)."""
    global VB, VF, STRIP_H, PH, PW, RAIL
    VB, VF, RAIL = vb, vf, rail
    PW = RAIL + GAP + STRIP_W + GAP + RAIL
    STRIP_H = VF - VB
    PH = RAIL + GAP + N * STRIP_H + (N - 1) * GAP + GAP + RAIL


def strip_xy(i):
    """Panel coordinates of strip i's (u = U0, v = VB) corner."""
    return RAIL + GAP, RAIL + GAP + i * (STRIP_H + GAP)


def seg(b, a, c, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a))
    s.SetEnd(V(*c))
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    b.Add(s)


def arc(b, cx, cy, r, a0, layer=pcbnew.Edge_Cuts):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    m = math.radians(a0 + 45)
    s.SetArcGeometry(V(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))),
                     V(cx + r * math.cos(m), cy + r * math.sin(m)),
                     V(cx + r * math.cos(math.radians(a0 + 90)), cy + r * math.sin(math.radians(a0 + 90))))
    s.SetLayer(layer)
    s.SetWidth(MM(0.1))
    b.Add(s)


def rounded_rect(b, x0, y0, x1, y1, r):
    seg(b, (x0 + r, y0), (x1 - r, y0))
    seg(b, (x1, y0 + r), (x1, y1 - r))
    seg(b, (x1 - r, y1), (x0 + r, y1))
    seg(b, (x0, y1 - r), (x0, y0 + r))
    arc(b, x1 - r, y0 + r, r, 270)
    arc(b, x1 - r, y1 - r, r, 0)
    arc(b, x0 + r, y1 - r, r, 90)
    arc(b, x0 + r, y0 + r, r, 180)


def in_tab(u, v_edge):
    return any(abs(u - tc) < TABW / 2 for tc in TAB_U)


def strip_outline(b, ox, oy, tabs):
    """The ruler's outline at panel offset (ox, oy) = position of (u, v) = (0, 0); with tabs: the long edges are open over the tab spans."""
    pts = PR.notch_polygon(VB, VF)
    n = len(pts)
    for k in range(n):
        a, c = pts[k], pts[(k + 1) % n]
        flat = abs(a[1] - c[1]) < 1e-9 and a[1] in (VB, VF)
        if flat and tabs:
            # split the flat edge around the tab spans
            lo, hi = sorted((a[0], c[0]))
            cuts = [lo]
            for tc in TAB_U:
                s0, s1 = tc - TABW / 2, tc + TABW / 2
                if s1 > lo and s0 < hi:
                    cuts += [max(s0, lo), min(s1, hi)]
            cuts.append(hi)
            for j in range(0, len(cuts), 2):
                if cuts[j + 1] - cuts[j] > 1e-9:
                    seg(b, (ox + cuts[j], oy + a[1]), (ox + cuts[j + 1], oy + a[1]))
        else:
            seg(b, (ox + a[0], oy + a[1]), (ox + c[0], oy + c[1]))


def frame(b, fiducials):
    """Panel rectangle, tooling holes, mouse bites; returns nothing."""
    rounded_rect(b, 0, 0, PW, PH, 1.0)
    for (x, y) in ((RAIL / 2, RAIL / 2), (PW - RAIL / 2, RAIL / 2), (RAIL / 2, PH - RAIL / 2), (PW - RAIL / 2, PH - RAIL / 2)):
        hole(b, "TL", x, y, 2.0)
    for i in range(N):
        sx, sy = strip_xy(i)
        ox, oy = sx - U0, sy - VB
        for tc in TAB_U:
            for ev in (VB, VF):
                for k in (-1, 0, 1):
                    x, y = ox + tc + 0.9 * k, oy + ev
                    hole(b, "MB", x, y, 0.5)
    if fiducials:
        for (x, y) in ((PW / 2 - 25, PH - 2.5), (PW / 2 + 25, PH - 2.5), (PW - 12.0, 2.5)):
            fid(b, x, y)


def hole(b, ref, x, y, d):
    fp = pcbnew.FootprintLoad(os.path.join(PR.KICAD_FP, "MountingHole.pretty"), "MountingHole_2.2mm_M2")
    fp.SetReference(ref)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for g in list(fp.GraphicalItems()):
        fp.Remove(g)
        GRAVE.append(g)
    for pad in fp.Pads():
        pad.SetDrillSize(V(d, d))
        pad.SetSize(pcbnew.F_Cu, V(d, d))
        pad.SetSize(pcbnew.B_Cu, V(d, d))
    fp.SetPosition(V(x, y))
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
    b.Add(fp)


def fid(b, x, y):
    fp = pcbnew.FootprintLoad(os.path.join(PR.KICAD_FP, "Fiducial.pretty"), "Fiducial_1mm_Mask2mm")
    fp.SetReference("FID")
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(V(x, y))
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
    b.Add(fp)
    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)


def pour(b, layer, ox, oy):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetZoneName("cobre sob a mascara")
    z.SetLocalClearance(MM(0.5))
    z.SetMinThickness(MM(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    o = z.Outline()
    o.NewOutline()
    for (x, y) in ((U0 + 0.5, VB + 0.5), (U1 - 0.5, VB + 0.5), (U1 - 0.5, VF - 0.5), (U0 + 0.5, VF - 0.5)):
        o.Append(MM(ox + x), MM(oy + y))
    b.Add(z)


def grade_strip(b, ox, oy, tabs):
    strip_outline(b, ox, oy, tabs)
    for uc in KEYS:
        rounded_rect(b, ox + uc - 7.0, oy - 7.0, ox + uc + 7.0, oy + 7.0, 0.5)
    # no copper pour: the grade-regua is hidden under the deck, bare FR-4 under the mask works the same (and DRC stays at 0 warnings)
    # keep the pour out of the openings and notches: the zone clearance (0.5) to the edge does it


def dup(x):
    try:
        return x.Duplicate()
    except TypeError:
        return x.Duplicate(False)


def run(cmd):
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def gerbers(board, tag, outdir, layers):
    gd = os.path.join(BUILD, "gerbers_" + tag)
    shutil.rmtree(gd, ignore_errors=True)
    os.makedirs(gd, exist_ok=True)
    for n in os.listdir(gd):
        os.remove(os.path.join(gd, n))
    run([KICAD_CLI, "pcb", "export", "gerbers", "--output", gd + os.sep, "--layers", layers, board])
    run([KICAD_CLI, "pcb", "export", "drill", "--output", gd + os.sep, "--format", "excellon", "--excellon-separate-th",
         "--excellon-units", "mm", board])
    os.makedirs(outdir, exist_ok=True)
    zp = os.path.join(outdir, tag + "_gerbers.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in sorted(os.listdir(gd)):
            zf.write(os.path.join(gd, n), n)
    return zp, sorted(os.listdir(gd))


def drc(board, tag):
    out = os.path.join(BUILD, tag + "_drc.json")
    run([KICAD_CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, board])
    d = json.load(open(out, encoding="utf-8"))
    return [(x["type"], x["severity"]) for x in d.get("violations", [])]


def text(b, s, x, y, layer, size=1.2, mirror=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetMirrored(mirror)
    t.SetTextSize(V(size, size))
    t.SetTextThickness(MM(0.18))
    t.SetPosition(V(x, y))
    b.Add(t)


def build_grade():
    cfg(-8.0, 8.0, 3.0)
    rec = {}
    # single strip
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetBoardThickness(MM(1.6))
    ox, oy = 10.0, 17.0
    grade_strip(b, ox, oy, False)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    text(b, "STUDENT V4 GRADE-REGUA R4V4 FR-4 1,6", ox + 37, oy + 7.5, pcbnew.B_SilkS, 0.6, True)
    single = os.path.join(KD, "student_v04_grade_regua.kicad_pcb")
    pcbnew.SaveBoard(single, b)
    rec["unitaria_drc"] = drc(single, "grade_regua")
    # panel
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetBoardThickness(MM(1.6))
    frame(b, False)
    for i in range(N):
        sx, sy = strip_xy(i)
        grade_strip(b, sx - U0, sy - VB, True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    text(b, "STUDENT V4 GRADE-REGUA R4V4  FR-4 1,6 mm  painel de 5", PW / 2, PH - 2.5, pcbnew.B_SilkS, 1.0, True)
    panel = os.path.join(KD, "student_v04_grade_regua_painel.kicad_pcb")
    pcbnew.SaveBoard(panel, b)
    rec["painel_drc"] = drc(panel, "grade_regua_painel")
    zp, files = gerbers(panel, "student_v04_grade_regua_painel", FAB, "F.Cu,B.Cu,F.Mask,B.Mask,B.Silkscreen,Edge.Cuts")
    rec.update({"painel_mm": [round(PW, 2), round(PH, 2)], "zip": os.path.relpath(zp, HW), "arquivos": files,
                "furos_painel": "4 de ferramenta D2,0 + %d microfuros D0,5" % (N * len(TAB_U) * 2 * 3)})
    run([KICAD_CLI, "pcb", "render", "--side", "top", "--width", "1800", "--height", "1800", "--quality", "basic",
         "--output", os.path.join(HERE, "img", "grade_regua_painel_topo.png"), panel])
    return rec


def build_regua_panel():
    cfg(-7.0, 7.0, 5.0)
    src = pcbnew.LoadBoard(PR.OUT)
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    b.SetDesignSettings(src.GetDesignSettings())
    frame(b, True)
    nets = {}
    for i in range(N):
        sx, sy = strip_xy(i)
        dx, dy = MM(sx - U0 - PR.OX + 0.0), MM(sy - VB - PR.OY)
        # u = U0 is board x = OX + U0 -> panel x = sx : offset = sx - (OX + U0)
        dx, dy = MM(sx - (PR.OX + U0)), MM(sy - (PR.OY + VB))
        off = pcbnew.VECTOR2I(dx, dy)

        def netfor(item):
            nm0 = item.GetNetname()
            nm = nm0 if nm0 == "" else "%s_%d" % (nm0, i + 1)       # one net set per strip (the strips are separate boards)
            if nm not in nets:
                ni = pcbnew.NETINFO_ITEM(b, nm)
                b.Add(ni)
                nets[nm] = ni
            return nets[nm]
        for d in src.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts:
                continue
            c = dup(d)
            c.Move(off)
            b.Add(c)
        for fp in src.GetFootprints():
            c = pcbnew.Cast_to_FOOTPRINT(dup(fp))
            c.Move(off)
            c.SetReference("%s-%d" % (fp.GetReference(), i + 1))
            c.SetPath(pcbnew.KIID_PATH())
            for pd in c.Pads():
                if pd.GetNetname():
                    pd.SetNet(netfor(pd))
            b.Add(c)
        for t in src.GetTracks():
            cls = t.GetClass()
            c = dup(t)
            c = {"PCB_VIA": pcbnew.Cast_to_PCB_VIA, "PCB_ARC": pcbnew.Cast_to_PCB_ARC}.get(cls, pcbnew.Cast_to_PCB_TRACK)(c)
            c.Move(off)
            c.SetNet(netfor(t))
            b.Add(c)
        for z in src.Zones():
            c = pcbnew.Cast_to_ZONE(dup(z))
            c.Move(off)
            if not z.GetIsRuleArea():
                c.SetNet(netfor(z))
            b.Add(c)
        # outline with tabs
        strip_outline(b, sx - U0, sy - VB, True)
    ROTEADA = bool(os.environ.get("REGUA_BOARD"))
    text(b, "STUDENT V4 REGUA R%d R11V4 painel de %d%s" % (PR.NPOS, N, "" if ROTEADA else " (SEM ROTA)"), PW / 2, 2.5, pcbnew.B_SilkS, 1.0, True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    panel = os.path.join(KD, "student_v04_regua_" + TAGP + ".kicad_pcb") if PR.NPOS != 4 or N != 5 else os.path.join(KD, "student_v04_regua_painel.kicad_pcb")
    pcbnew.SaveBoard(panel, b)
    rec = {"painel_mm": [round(PW, 2), round(PH, 2)], "tracks_copiadas": len(src.GetTracks())}
    pdir = os.path.join(FAB, "regua", "gerbers") if ROTEADA else os.path.join(FAB, "regua_painel_SEM_ROTA_NAO_ENCOMENDAR")
    zp, files = gerbers(panel, "student_v04_regua_" + TAGP + ("" if ROTEADA else "_SEM_ROTA"), pdir,
                        "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts")
    rec["zip"] = os.path.relpath(zp, HW)
    rec["drc_painel"] = drc(panel, "painel_" + TAGP)
    rec["arquivos"] = files
    # provisional BOM / CPL of the whole panel (positions from KiCad; rotations still to be fitted to the EasyEDA footprints by cpl_jlc.py after the gate)
    rows = []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if fp.GetLayer() != pcbnew.B_Cu or ref.startswith(("PEG", "H", "FID", "TL", "MB", "LK")):
            continue
        rows.append([ref, round(TOMM(fp.GetX()), 3), round(-TOMM(fp.GetY()), 3) if False else round(TOMM(fp.GetY()), 3), "Bottom",
                     round(fp.GetOrientationDegrees(), 1)])
    with open(os.path.join(FAB, "regua_painel_SEM_ROTA_NAO_ENCOMENDAR", "regua_%s_cpl_PROVISORIO.csv" % TAGP), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation(KiCad, sem ajuste EasyEDA)"])
        w.writerows(rows)
    rec["pecas_no_painel"] = len(rows)
    run([KICAD_CLI, "pcb", "render", "--side", "bottom", "--width", "1800", "--height", "1800", "--quality", "basic",
         "--output", os.path.join(HERE, "img", "regua_%s_fundo.png" % TAGP), panel])
    return rec


def main():
    os.makedirs(FAB, exist_ok=True)
    os.makedirs(os.path.join(HERE, "img"), exist_ok=True)
    out = {}
    if MODO in ("grade", "ambos"):
        out["grade"] = build_grade()
    if MODO in ("regua", "ambos"):
        out["regua"] = build_regua_panel()
    if MODO == "ambos":
        json.dump(out, open(os.path.join(HERE, "fab_regua.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
