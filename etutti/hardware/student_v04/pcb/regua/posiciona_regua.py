"""eTutti Student V4 (R4V4): the 4-key sensor ruler PLACED, with NO tracks (portao P, parte 2).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/regua/posiciona_regua.py

Run pcb/regua/schematic_regua.py first (it writes pcb/regua/build/{partes_regua.json,regua_netlist.net}).
Writes kicad/regua/student_v04_regua.kicad_pcb (+ .kicad_dru, .kicad_pro) and pcb/regua/posicao_regua.json (positions, pads,
keep-outs, the contract with the case: input of vistas_regua.py and POSICIONAMENTO.md part 2). Never routes.

Frame. u runs along the row (nominal ruler 0..74 mm = 4 x 18.5; the PCB is 73.6 mm: 0.2 mm short at each end for the chain), v across,
+v towards the player (front edge), 0 on the row's centre line. Board x = OX + u, y = OY + v.
Every part is on the BOTTOM (JLCPCB bottom assembly); nothing on the top, where the key sits. Key pegs (2 NPTH 1.70 at +-5.08 from the cell
centre, v = 0) and the two M2 holes (18.5 and 55.5, v = +5.2, 2.2 mm) are the only things drilled; the back edge has the 2.0 x 4.3 mm
post notches (u = 0, 18.5, 37, 55.5, 74; the end ones are halves).

Placement logic (what is where, and why):
  * TMAG5253 U1..U4 at the cell centres (9.25 + 18.5 k, 0): the sensor under the key's magnet.
  * the SH-6 side-entry connector J1 (IN; R5V4: no J2, the OUT end has 5 solder pads LK2, the IN end LK1 too) in the BACK half (v about -3.9), pins along u, mouth towards -v (the back
    edge): the central band (v = 0) is full of pegs and sensors, the front half is where the lower neighbour's ruler sits (a plug going
    that way would hit it, a plug going back passes over the higher neighbour's ruler: it only needs a window in the case's rail), and
    the 9.9 mm of the connector does not fit between two pegs. They sit between the post notches (u = 31.2 and 42.8, mirror images about u = 37).
  * the 74HC595 in the FRONT half (rotated 90, pins along u) between the connectors (u = 37): short SER / QH' / CLK.
  * 100 nF at each TMAG's VCC pin, 100 nF + 10 uF at the connector/595, the 100 ohm of QH' next to LK2: found by a small search.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, PCB)
import posiciona_v4 as P  # noqa: E402  (helpers only; its main() is not run)
import sexpr as S  # noqa: E402

HW = os.path.normpath(os.path.join(PCB, ".."))
KD = os.path.join(HW, "kicad", "regua")
NAME = "student_v04_regua"
OUT = os.path.join(KD, NAME + ".kicad_pcb")
KICAD_FP = P.KICAD_FP
M, T, V = P.M, P.T, P.V
GRAVE = []

OX, OY = 10.0, 17.0
U0, U1 = 0.2, 73.8                 # PCB ends (nominal ruler 0..74, 0.2 mm short at each end)
VB, VF = -7.0, 7.0                 # back / front edge
PITCH = 18.5
KEYS = [9.25 + PITCH * k for k in range(4)]
PEG_DX, PEG_D = 5.08, 1.70
M2_U, M2_V, M2_D = (18.5, 37.0, 55.5), 5.2, 2.2   # R4V4: each row uses two of the three (row 1: 18.5+55.5, row 2: 37+55.5, rows 3,4: 18.5+37)
NOTCH_U = (0.0, 18.5, 37.0, 55.5, 74.0)
NOTCH_W, NOTCH_D = 2.0, 4.3
CONN = {"J1": (5.9, -3.95), "J2": (68.1, -3.95)}   # R4V4 contract of the design: IN x 5.9, OUT x 68.1, back strip, mouth -v     # (u, v) of the connectors' origin (centre of the pin row), mouth -v
U5_POS = (27.75, 4.2)
LINK = {"LK1": (2.1, 1.6), "LK2": (71.9, 1.6)}   # R5V4: 5 solder pads (1.4 x 0.7, pitch 1.0) at each end, v -0.4..3.6, pin 1 towards the back
EDGE = 0.25                         # copper-to-edge


def X(u):
    return OX + u


def Y(v):
    return OY + v


def notch_polygon(VB=VB, VF=VF):
    """(u, v) polygon, counter-clockwise on screen (x right, y down: starts front-left, goes along the back edge, back to the front)."""
    pts = [(U0, VF)]
    # back edge, left to right (v = VB is the back, the smaller y)
    spans = []
    for nu in NOTCH_U:
        a, b = max(nu - NOTCH_W / 2, U0), min(nu + NOTCH_W / 2, U1)
        if b > a:
            spans.append((a, b))
    cur_u = U0
    for a, b in spans:
        if a <= U0 + 1e-9:                      # a half notch at the left end: the board starts under the notch
            pts += [(U0, VB + NOTCH_D), (b, VB + NOTCH_D), (b, VB)]
        elif b >= U1 - 1e-9:                    # a half notch at the right end
            pts += [(a, VB), (a, VB + NOTCH_D), (U1, VB + NOTCH_D)]
        else:
            pts += [(a, VB), (a, VB + NOTCH_D), (b, VB + NOTCH_D), (b, VB)]
    if not any(abs(p[0] - U0) < 1e-9 and p[1] == VB for p in pts) and spans and spans[0][0] > U0 + 1e-9:
        pass
    pts += [(U1, VF)]
    return pts


def poly_edges(b, pts, layer=pcbnew.Edge_Cuts, w=0.1):
    for i in range(len(pts)):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(X(pts[i][0]), Y(pts[i][1])))
        s.SetEnd(V(X(pts[(i + 1) % len(pts)][0]), Y(pts[(i + 1) % len(pts)][1])))
        s.SetLayer(layer)
        s.SetWidth(M(w))
        b.Add(s)


def set_courtyard(fp, x0, y0, x1, y1):
    """Replace the footprint's courtyard by a rectangle (footprint coordinates, mm): the library's ones carry a 0.25-0.55 mm margin
    that does not fit a 14 mm ruler; these hug the pads (+0.1)."""
    for d in list(fp.GraphicalItems()):
        if d.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            fp.Remove(d)
            GRAVE.append(d)
    sh = pcbnew.PCB_SHAPE(fp)
    sh.SetShape(pcbnew.SHAPE_T_RECT)
    sh.SetStart(V(x0, y0))
    sh.SetEnd(V(x1, y1))
    sh.SetLayer(pcbnew.F_CrtYd)
    sh.SetWidth(M(0.05))
    fp.Add(sh)


def box_of(u0, v0, u1, v1):
    return (X(u0), Y(v0), X(u1), Y(v1))


def text(b, s, u, v, layer, size=1.0, rot=0, mirror=False, just=pcbnew.GR_TEXT_H_ALIGN_CENTER):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetPosition(V(X(u), Y(v)))
    t.SetTextSize(pcbnew.VECTOR2I(M(size), M(size)))
    t.SetTextThickness(M(0.15))
    t.SetHorizJustify(just)
    t.SetMirrored(mirror)
    t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    b.Add(t)


def main():
    parts = json.load(open(os.path.join(HERE, "build", "partes_regua.json"), encoding="utf-8"))
    nl = P.netlist(os.path.join(HERE, "build", "regua_netlist.net"))
    main_board = pcbnew.LoadBoard(os.path.join(HW, "kicad", "student_v04.kicad_pcb"))
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    b.SetDesignSettings(main_board.GetDesignSettings())
    poly_edges(b, notch_polygon())
    netinfo = {}

    def net_of(name):
        if name not in netinfo:
            ni = pcbnew.NETINFO_ITEM(b, name)
            b.Add(ni)
            netinfo[name] = ni
        return netinfo[name]

    fps = {}
    for p in parts:
        lib, name = p["fp"].split(":")
        libdir = os.path.join(KD, lib + ".pretty") if lib == "viaggio_micromod" else os.path.join(KICAD_FP, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH(p["path"]))
        h = {"J1": "4.3", "J2": "4.3", "LK1": "0.05", "LK2": "0.05", "U5": "1.0", "C6": "1.45"}.get(p["ref"], "0.4" if p["ref"].startswith("U") else "0.55")
        for k, v in (("Codigo", p["code"]), ("LCSC", p["lcsc"]), ("Montagem", p["mount"]), ("Description", p["note"]),
                     ("Datasheet", p.get("datasheet", "")), ("Altura_mm", h)):
            fp.SetField(k, v or "")
        for f_ in fp.GetFields():
            f_.SetVisible(False)
        for pad in fp.Pads():
            n = nl.get(p["ref"], {}).get(pad.GetNumber())
            if n:
                pad.SetNet(net_of(n))
        if p["ref"] in ("J1", "J2"):
            set_courtyard(fp, -4.5, -2.85, 4.5, 2.9)
        elif p["ref"] in ("U1", "U2", "U3", "U4"):
            set_courtyard(fp, -0.6, -1.06, 0.6, 1.06)
        b.Add(fp)
        fps[p["ref"]] = fp
        P.to_bottom(fp)

    # ---- drilled things: key pegs (NPTH 1.70) and M2 holes (NPTH 2.2): footprints of their own, so DRC and CPL see them
    def hole_fp(ref, u, v, d, descr):
        fp = pcbnew.FootprintLoad(os.path.join(KICAD_FP, "MountingHole.pretty"), "MountingHole_2.2mm_M2")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
        fp.SetReference(ref)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(V(X(u), Y(v)))
        for pad in fp.Pads():
            pad.SetSize(pcbnew.VECTOR2I(M(d), M(d)))
            pad.SetDrillSize(pcbnew.VECTOR2I(M(d), M(d)))
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        # drop the footprint's own 'MountingHole' silk/fab circle (keep the pad); the courtyard stays
        b.Add(fp)
        fps[ref] = fp
        return fp

    pegs = []
    for k, uc in enumerate(KEYS):
        for s, sgn in (("a", -1), ("b", 1)):
            u = uc + sgn * PEG_DX
            pegs.append((u, 0.0))
            hole_fp("PEG%d%s" % (k + 1, s), u, 0.0, PEG_D, "furo do pino da tecla")
    for i, u in enumerate(M2_U):
        hole_fp("H%d" % (i + 1), u, M2_V, M2_D, "furo M2 da regua (parafuso no degrau)")

    # ---- fixed placements
    ob_fixed = []          # boxes no bottom part may overlap (holes with a margin, notches with a margin, M2 rings)
    for (u, v) in pegs:
        ob_fixed.append(box_of(u - PEG_D / 2 - 0.35, v - PEG_D / 2 - 0.35, u + PEG_D / 2 + 0.35, v + PEG_D / 2 + 0.35))
    for u in M2_U:
        ob_fixed.append(box_of(u - 3.2, M2_V - 3.2, u + 3.2, M2_V + 3.2))      # bottom keep-out 6.4 (the step's boss)
    notch_boxes = []
    for nu in NOTCH_U:
        a, b_ = max(nu - NOTCH_W / 2, U0) - EDGE, min(nu + NOTCH_W / 2, U1) + EDGE
        if b_ > a:
            notch_boxes.append(box_of(a, VB - 1.0, b_, VB + NOTCH_D + EDGE))
    ob_fixed += notch_boxes

    def pose(ref, u, v, rot):
        P.set_pose(fps[ref], X(u), Y(v), rot)

    for k in range(4):
        pose("U%d" % (k + 1), KEYS[k], 0.0, 0)
    # U1..U4 orientation: pins 1 (VCC) and 4 (OUT) towards the back (-v), where the connectors are
    for k in range(4):
        pins = {n: P.pad_xy(fps["U%d" % (k + 1)], n)[0] for n in ("1", "2", "3", "4")}
        if pins["1"][1] > pins["2"][1]:
            pose("U%d" % (k + 1), KEYS[k], 0.0, 180)

    def mouth_back(ref):
        fp = fps[ref]
        P.orient_mouth(fp, "sh", (0.0, -1.0))

    for ref, (u, v) in CONN.items():
        mouth_back(ref)
        P.set_pose(fps[ref], X(u), Y(v), fps[ref].GetOrientationDegrees())
    u5 = fps["U5"]
    pose("U5", U5_POS[0], U5_POS[1], 0)
    for ref, (u, v) in LINK.items():       # pads along v, pin 1 towards the back (-v): try both rotations after the flip to the bottom
        for rot in (0, 180):
            pose(ref, u, v, rot)
            ys = {pd.GetNumber(): pd.GetPosition().y for pd in fps[ref].Pads()}
            if ys["1"] < ys["5"]:
                break

    # ---- passives: search near an anchor (nearest free spot), in the order of importance
    placed = {"J1", "J2", "LK1", "LK2", "U5", "U1", "U2", "U3", "U4"}
    holes = [r for r in fps if r.startswith(("PEG", "H"))]

    def court_u(fp):
        c = P.court(fp)
        return (c[0], c[1], c[2], c[3])

    def free(ref, box, extra=()):
        for o in ob_fixed:
            if P.overlap(box, o, 0.0):
                return False
        for r in placed:
            if r == ref:
                continue
            if P.overlap(box, court_u(fps[r]), 0.05):
                return False
        for o in extra:
            if P.overlap(box, o, 0.0):
                return False
        # inside the board (courtyard), clear of the edges by EDGE
        if ref in ("C6", "R1") and box[3] > Y(4.2):      # R5V4: the elo/cable end stays inside the pocket (v <= 4.2), not on the front rail
            return False
        if box[0] < X(U0 + EDGE) or box[2] > X(U1 - EDGE) or box[3] > Y(VF - EDGE) or box[1] < Y(VB + EDGE):
            return False
        return True

    offs = sorted(((i * 0.1, j * 0.1) for i in range(-120, 121) for j in range(-120, 121)),
                  key=lambda d: d[0] * d[0] + d[1] * d[1])

    def settle(ref, anchor, rots=(0, 90)):
        fp = fps[ref]
        best = None
        for rot in rots:
            P.set_pose(fp, anchor[0], anchor[1], rot)
            c = court_u(fp)
            for dx, dy in offs:
                if free(ref, P.shifted(c, dx, dy)):
                    d = math.hypot(dx, dy)
                    if best is None or d < best[0] - 1e-9:
                        best = (d, rot, dx, dy)
                    break
        if best is None:
            raise SystemExit("%s: no free spot" % ref)
        P.set_pose(fp, anchor[0] + best[2], anchor[1] + best[3], best[1])
        placed.add(ref)
        return best

    anchors = {}
    for k in range(4):
        vcc = P.pad_xy(fps["U%d" % (k + 1)], "1")[0]
        anchors["C%d" % (k + 1)] = (vcc[0], vcc[1] + (-1.9 if True else 0))
    j1pin1 = P.pad_xy(fps["J1"], "1")[0]
    anchors["C6"] = (j1pin1[0] - 3.5, j1pin1[1] - 0.0)
    u5v = P.pad_xy(fps["U5"], "16")[0]
    anchors["C5"] = (u5v[0] + 2.5, u5v[1] + 2.0)
    lk2p5 = P.pad_xy(fps["LK2"], "5")[0]
    anchors["R1"] = (lk2p5[0] - 3.0, lk2p5[1] + 0.5)
    for ref in ("C1", "C2", "C3", "C4", "C6", "C5", "R1"):
        best = settle(ref, anchors[ref])

    # ---- keep-out areas (rule areas) and markings
    allcu = [pcbnew.F_Cu, pcbnew.B_Cu]
    for i, u in enumerate(M2_U):
        P.add_zone(b, [pcbnew.B_Cu], P.rect_pts(X(u) - 3.2, Y(M2_V) - 3.2, X(u) + 3.2, Y(M2_V) + 3.2), "M2 fundo (patamar 6,4)",
                   rule=True, no_fp=True)
    # silkscreen / drawings (top = the key side; bottom = the assembly side)
    for k, uc in enumerate(KEYS):
        for (a, c, d, e) in ((uc - 7, -7, uc + 7, -7), (uc + 7, -7, uc + 7, 7), (uc + 7, 7, uc - 7, 7), (uc - 7, 7, uc - 7, -7)):
            sh = pcbnew.PCB_SHAPE(b)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(V(X(a), Y(c)))
            sh.SetEnd(V(X(d), Y(e)))
            sh.SetLayer(pcbnew.Dwgs_User)
            sh.SetWidth(M(0.1))
            b.Add(sh)
        text(b, "tecla %d" % (k + 1), uc, 2.5, pcbnew.F_SilkS, 0.9)
    text(b, "STUDENT V4 REGUA R4V4 - FRENTE (jogador) em baixo", 37.0, 5.6, pcbnew.F_SilkS, 0.9)
    text(b, "J1 ENTRADA", CONN["J1"][0], -1.5, pcbnew.B_SilkS, 0.8, mirror=True)
    text(b, "J2 SAIDA", CONN["J2"][0], -1.5, pcbnew.B_SilkS, 0.8, mirror=True)
    text(b, "ELO IN", LINK["LK1"][0] + 0.2, 5.6, pcbnew.B_SilkS, 0.6, mirror=True)
    text(b, "ELO OUT", LINK["LK2"][0] - 0.2, 5.6, pcbnew.B_SilkS, 0.6, mirror=True)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    os.makedirs(KD, exist_ok=True)
    pcbnew.SaveBoard(OUT, b)

    # ---- the pro/dru
    pro_main = json.load(open(os.path.join(HW, "kicad", "student_v04.kicad_pro")))
    pro = json.load(open(os.path.join(KD, NAME + ".kicad_pro")))
    pro["board"] = pro_main["board"]
    pro["board"]["design_settings"]["rules"]["min_copper_edge_clearance"] = 0.25
    pro["net_settings"] = {"classes": [c for c in pro_main["net_settings"]["classes"] if c["name"] == "Default"],
                           "meta": pro_main["net_settings"].get("meta", {"version": 4}), "net_colors": None,
                           "netclass_assignments": None, "netclass_patterns": []}
    json.dump(pro, open(os.path.join(KD, NAME + ".kicad_pro"), "w"), indent=2)
    open(os.path.join(KD, NAME + ".kicad_dru"), "w", newline="\n").write("""(version 1)
# eTutti Student V4 ruler -- custom rules (R4V4)
(rule "Vias 0,5 / furo 0,3"
    (condition "A.Type == 'via'")
    (constraint via_diameter (min 0.5mm))
    (constraint hole_size (min 0.3mm)))
(rule "Trilhas: minimo 0,15; OUT e CLK 0,2"
    (condition "A.Type == 'track'")
    (constraint track_width (min 0.15mm) (opt 0.2mm)))
(rule "OUT (analogico) a 0,3 mm de CLK/SER/QHP (diafonia na leitura dos sensores)"
    (condition "A.Type == 'track' && A.NetName == 'OUT' && (B.NetName == 'CLK' || B.NetName == 'SER' || B.NetName == 'QHP' || B.NetName == 'QHP_J')")
    (constraint clearance (min 0.3mm)))
(rule "Nada no topo (onde fica a tecla): so cobre de trilha e plano, nenhuma peca"
    (condition "A.Type == 'Footprint' && A.Layer == 'F.Cu' && A.Reference != 'H1' && A.Reference != 'H2' && !A.Reference.startsWith('PEG')")
    (constraint disallow footprint))
""")

    # ---- dump
    rec = {"origem": [OX, OY], "u_v": "x = OX + u, y = OY + v; +v para o jogador (borda da frente)", "pcb_mm": [U1 - U0, VF - VB],
           "pecas": {}, "pads": [], "furos": [], "entalhes": [], "contorno_uv": notch_polygon(), "teclas_u": KEYS}
    for ref, fp in fps.items():
        c = P.court(fp)
        rec["pecas"][ref] = {"u": round(T(fp.GetX()) - OX, 3), "v": round(T(fp.GetY()) - OY, 3), "rot": round(fp.GetOrientationDegrees(), 1),
                             "lado": P.side_of(fp), "patio_uv": [round(c[0] - OX, 2), round(c[1] - OY, 2), round(c[2] - OX, 2), round(c[3] - OY, 2)],
                             "altura_mm": ({f.GetName(): f.GetText() for f in fp.GetFields()}).get("Altura_mm", "")}
        for pd in fp.Pads():
            sz = pd.GetSize()
            rec["pads"].append({"ref": ref, "n": pd.GetNumber(), "net": pd.GetNetname(), "u": round(T(pd.GetPosition().x) - OX, 3),
                                "v": round(T(pd.GetPosition().y) - OY, 3), "w": round(T(sz.x), 3), "h": round(T(sz.y), 3),
                                "rot": round(pd.GetOrientationDegrees(), 1),
                                "th": pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH), "lado": P.side_of(fp)})
    for (u, v) in pegs:
        rec["furos"].append({"u": u, "v": v, "d": PEG_D, "tipo": "pino da tecla"})
    for u in M2_U:
        rec["furos"].append({"u": u, "v": M2_V, "d": M2_D, "tipo": "M2"})
    for nu in NOTCH_U:
        rec["entalhes"].append([nu - NOTCH_W / 2, VB, nu + NOTCH_W / 2, VB + NOTCH_D])
    # contract with the case: plug windows beyond the back edge (mouth -v): u extent of the plug (7.0 housing), v from the edge to 4.6 past it
    rec["janelas_plugue"] = {r: [round(T(fps[r].GetX()) - OX - 3.8, 2), VB - 5.0, round(T(fps[r].GetX()) - OX + 3.8, 2), VB] for r in ("J1", "J2")}
    json.dump(rec, open(os.path.join(HERE, "posicao_regua.json"), "w", encoding="utf-8"), indent=1)
    for ref in ("U1", "U2", "U3", "U4", "U5", "J1", "J2", "LK1", "LK2", "C1", "C2", "C3", "C4", "C5", "C6", "R1"):
        q = rec["pecas"][ref]
        print("%-3s u %7.2f v %6.2f rot %5.1f  patio %s" % (ref, q["u"], q["v"], q["rot"], q["patio_uv"]))


if __name__ == "__main__":
    main()
