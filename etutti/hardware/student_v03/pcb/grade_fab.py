"""eTutti Student V3: the keyboard grid as a 1.6 mm FR-4 board (SPEC v2), with its own fab files.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/grade_fab.py

The grid is a finishing plate: no circuit. Its outline is the keyboard's hull grown by 21.5 mm
(geometria.py), with one 6.2 mm hole per button and a 2.3 mm hole for each of the 10 edge screws.
Both faces are a copper pour under the solder mask, so that the matte black mask has one even
colour (mask over bare laminate looks different from mask over copper). No silkscreen on the
visible face; the name is on the back.

To order: 2 layers, 1.6 mm, solder mask "matte black", any finish (no copper is exposed).

Writes kicad/student_v03_grade.kicad_pcb, fab/student_v03_grade_gerbers.zip and pcb/grade.json.
"""
import json
import math
import os
import subprocess
import sys
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, V2)
import geometria as G      # noqa: E402

KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
NAME = "student_v03_grade"
BOARD = os.path.join(V2, "kicad", NAME + ".kicad_pcb")
BUILD = os.path.join(HERE, "build")
FAB = os.path.join(V2, "fab")
T = 1.6
BUTTON_HOLE, SCREW_HOLE = 6.2, 2.3
COPPER_BACK = 0.5          # the pour stays this far from the edge and from every hole
CSK_COPPER_D = 4.4         # SPEC v6 item 2: no copper inside this diameter round the 10 screw holes (countersink mouth 3.8 + 0.2 + margin), both faces
MM = pcbnew.FromMM
GRAVE = []


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def outline(d):
    """The hull grown by d as (lines, arcs): arcs as (start, middle, end)."""
    H = G.HULL
    n = len(H)
    area = sum(H[i][0] * H[(i + 1) % n][1] - H[(i + 1) % n][0] * H[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    lines, arcs = [], []
    for i in range(n):
        a, b, c = H[i - 1], H[i], H[(i + 1) % n]

        def normal(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            return sgn * dy / L, -sgn * dx / L
        n1, n2 = normal(a, b), normal(b, c)
        m = (n1[0] + n2[0], n1[1] + n2[1])
        L = math.hypot(*m)
        arcs.append(((b[0] + d * n1[0], b[1] + d * n1[1]), (b[0] + d * m[0] / L, b[1] + d * m[1] / L),
                     (b[0] + d * n2[0], b[1] + d * n2[1])))
        lines.append(((b[0] + d * n2[0], b[1] + d * n2[1]), (c[0] + d * n2[0], c[1] + d * n2[1])))
    return lines, arcs


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(FAB, exist_ok=True)
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetBoardThickness(MM(T))
    lines, arcs = outline(G.GRID_EDGE)
    for a, e in lines:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a))
        s.SetEnd(V(*e))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        b.Add(s)
    for a, m, e in arcs:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(*a), V(*m), V(*e))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        b.Add(s)

    def hole(ref, x, y, d):
        fp = pcbnew.FootprintLoad(os.path.join(KICAD_FP, "MountingHole.pretty"), "MountingHole_2.2mm_M2")
        fp.SetReference(ref)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        for g in list(fp.GraphicalItems()):
            fp.Remove(g)                     # the library's courtyard and silk circles are for 2.2 mm
            GRAVE.append(g)                  # pcbnew: a removed item must stay alive in Python
        for pad in fp.Pads():
            pad.SetDrillSize(V(d, d))
            pad.SetSize(pcbnew.F_Cu, V(d, d))
        fp.SetPosition(V(x, y))
        b.Add(fp)

    for i, (_r, x, y) in enumerate(G.KEYS, 1):
        hole("B%d" % i, x, y, BUTTON_HOLE)
    screws = G.grid_screws()
    for i, (x, y) in enumerate(screws, 1):
        hole("HG%d" % i, x, y, SCREW_HOLE)

    pts = G.offset(G.GRID_EDGE - COPPER_BACK, 0.5)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetZoneName("cobre sob a mascara")
        z.SetLocalClearance(MM(COPPER_BACK))
        z.SetMinThickness(MM(0.25))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(MM(x), MM(y))
        b.Add(z)
    # keep-outs (copper) round the countersunk screw holes: a 64-gon whose inscribed circle is 4.4 mm
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        for i, (x, y) in enumerate(screws, 1):
            k = pcbnew.ZONE(b)
            k.SetIsRuleArea(True)
            k.SetDoNotAllowZoneFills(True)
            k.SetDoNotAllowTracks(True)
            k.SetDoNotAllowVias(True)
            k.SetDoNotAllowPads(False)
            k.SetDoNotAllowFootprints(False)
            k.SetLayer(layer)
            k.SetZoneName("sem cobre - escareado HG%d" % i)
            o = k.Outline()
            o.NewOutline()
            r = CSK_COPPER_D / 2 / math.cos(math.pi / 64)
            for j in range(64):
                a = 2 * math.pi * j / 64
                o.Append(MM(x + r * math.cos(a)), MM(y + r * math.sin(a)))
            b.Add(k)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    t = pcbnew.PCB_TEXT(b)
    t.SetText("eTutti Student V3 - grade do teclado, FR-4 1,6 mm")
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(V(1.2, 1.2))
    t.SetTextThickness(MM(0.18))
    t.SetPosition(V(160.0, 86.0))
    b.Add(t)
    tb = b.GetTitleBlock()
    tb.SetTitle("eTutti Student V3 · grade do teclado")
    tb.SetRevision("SPEC v6")
    pcbnew.SaveBoard(BOARD, b)

    drc = os.path.join(BUILD, NAME + "_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", drc, BOARD], check=False, capture_output=True)
    d = json.load(open(drc, encoding="utf-8"))
    errs = [(x["type"], x["description"]) for x in d.get("violations", []) if x["severity"] == "error"]
    gd = os.path.join(BUILD, "gerbers_" + NAME)
    os.makedirs(gd, exist_ok=True)
    for n in os.listdir(gd):
        os.remove(os.path.join(gd, n))
    subprocess.run([KICAD_CLI, "pcb", "export", "gerbers", "--output", gd + os.sep, "--layers",
                    "F.Cu,B.Cu,F.Mask,B.Mask,B.Silkscreen,Edge.Cuts", BOARD], check=True, capture_output=True)
    subprocess.run([KICAD_CLI, "pcb", "export", "drill", "--output", gd + os.sep, "--format", "excellon", "--excellon-separate-th",
                    "--excellon-units", "mm", BOARD], check=True, capture_output=True)
    zp = os.path.join(FAB, NAME + "_gerbers.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in sorted(os.listdir(gd)):
            zf.write(os.path.join(gd, n), n)
    png = os.path.join(FAB, NAME + "_top.png")
    subprocess.run([KICAD_CLI, "pcb", "render", "--side", "top", "--width", "2000", "--height", "1200", "--quality", "high",
                    "--output", png, BOARD], check=False, capture_output=True)
    bb = b.GetBoardEdgesBoundingBox()
    area = sum(z.GetFilledArea() for z in b.Zones() if not z.GetIsRuleArea()) / 1e12 / 2
    npth = [l for l in open(os.path.join(gd, NAME + "-NPTH.drl"), encoding="utf-8").read().splitlines()]
    rec = {"espessura_mm": T, "mascara": "preta fosca, nas duas faces", "camadas": 2,
           "caixa_mm": [round(pcbnew.ToMM(bb.GetWidth()), 2), round(pcbnew.ToMM(bb.GetHeight()), 2)],
           "furos_dos_botoes": {"qtd": len(G.KEYS), "d_mm": BUTTON_HOLE}, "furos_dos_parafusos": {"qtd": len(screws), "d_mm": SCREW_HOLE},
           "furos_no_arquivo_de_furacao": sum(1 for l in npth if l.startswith("X")),
           "cobre_por_face_mm2": round(area, 0), "cobre_recuado_mm": COPPER_BACK, "cobre_recuado_nos_escareados_d_mm": CSK_COPPER_D,
           "drc_erros": errs, "drc_avisos": sorted({x["type"] for x in d.get("violations", []) if x["severity"] != "error"}),
           "arquivos": sorted(os.listdir(gd)), "zip": os.path.basename(zp)}
    json.dump(rec, open(os.path.join(HERE, "grade.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec, indent=1, ensure_ascii=False))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
