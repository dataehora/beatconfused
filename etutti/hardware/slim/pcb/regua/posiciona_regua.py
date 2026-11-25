"""eTutti Slim (R3SL, stage 2a): the R8 ruler and its grade PLACED, with NO tracks. KiCad python.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/slim/pcb/regua/schematic_regua.py   (plain python, writes the netlist)
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/slim/pcb/regua/posiciona_regua.py

Reads: pcb/regua/build/{partes_regua.json, regua_netlist.net} (schematic_regua.py), case/envelope_regua.json (the Design's contract).
Writes: pcb/kicad_regua/slim_regua.kicad_pcb (+ .kicad_pro, .kicad_dru), pcb/kicad_regua/slim_grade.kicad_pcb, pcb/regua/posicao_regua.json (positions, pads, holes,
corridors: the input of the plan, the 3D scene and the routing stage). Never routes.

Frame: u along the ruler from its LEFT end (0..160), v across, +v towards the player (front edge), 0 on the row's centre line; board x = OX + u, y = OY + v.
Everything electrical is on the BOTTOM (JLCPCB bottom assembly); the key side (top) carries only the GND pour and the holes.
  * 8 TMAG5253 at (u_key, +4.3): the Hall sensor sits 4.3 mm from the key centre on the magnet side; the switch is turned so that side faces the player.
    Orientation: OUT (pin 4) and VCC (pin 1) towards the back, EN (pin 3) and GND (pin 2) towards the front, so the EN bus runs along the front band and
    the analogue OUT bus along the back band.
  * the tail (u < 14): FFC (mouth towards -u at the left edge), the 74HC595 and its two capacitors.
  * 100 nF at every sensor, across VCC / GND, on the tail side of the sensor.
Never run over a board that has been routed: it rebuilds the files.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(PCB, ".."))
sys.path.insert(0, PCB)
import sexpr as S  # noqa: E402

KD = os.path.join(PCB, "kicad_regua")
BUILD = os.path.join(HERE, "build")
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
ENV = json.load(open(os.path.join(HW, "case", "envelope_regua.json"), encoding="utf-8"))
M, T = pcbnew.FromMM, pcbnew.ToMM
GRAVE = []

OX, OY = 20.0, 30.0
RL, RW = ENV["regua"]["comprimento"], ENV["regua"]["largura"]
VB, VF = -RW / 2, RW / 2
KEYS_U = ENV["regua"]["u_teclas"]
SENS_V = ENV["regua"]["sensor_v"]
M2_U, M2_D = ENV["regua"]["m2_u"], ENV["regua"]["m2_d"]
M2_V = ENV["regua"]["m2_v"]                              # R9SL: the two M2 sit at the right end, at v = -/+ 3.6
PEG_DX, PEG_D, POST_D = ENV["regua"]["furos_switch"]["pino_dx"], ENV["regua"]["furos_switch"]["pino_d"], ENV["regua"]["furos_switch"]["poste_d"]
FFC_U = ENV["regua"]["ffc"]["u_origem"]
EDGE = 0.25


def X(u):
    return OX + u


def Y(v):
    return OY + v


def VEC(x, y):
    return pcbnew.VECTOR2I(M(x), M(y))


def netlist(path):
    tree = S.parse(open(path, encoding="utf-8").read())
    got = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        for x in S.find(n, "node"):
            got.setdefault(S.first(x, "ref")[1], {})[S.first(x, "pin")[1]] = name
    return got


def pad_xy(fp, num):
    p = fp.FindPadByNumber(num).GetPosition()
    return (T(p.x), T(p.y))


def to_bottom(fp):
    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)


def set_pose(fp, x, y, rot):
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    fp.SetPosition(VEC(x, y))


def court(fp):
    layer = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
    bb = fp.GetCourtyard(layer).BBox()
    return (T(bb.GetX()), T(bb.GetY()), T(bb.GetX() + bb.GetWidth()), T(bb.GetY() + bb.GetHeight()))


def seg(b, x0, y0, x1, y1, layer, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VEC(x0, y0)); s.SetEnd(VEC(x1, y1))
    s.SetLayer(layer); s.SetWidth(M(w))
    b.Add(s)


def rect_edges(b, x0, y0, x1, y1, layer=pcbnew.Edge_Cuts, w=0.1, r=0.0):
    if r <= 0:
        for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            seg(b, a[0], a[1], c[0], c[1], layer, w)
        return
    seg(b, x0 + r, y0, x1 - r, y0, layer, w); seg(b, x1, y0 + r, x1, y1 - r, layer, w)
    seg(b, x1 - r, y1, x0 + r, y1, layer, w); seg(b, x0, y1 - r, x0, y0 + r, layer, w)
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        arc = pcbnew.PCB_SHAPE(b)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        a = math.radians(a0)
        arc.SetCenter(VEC(cx, cy))
        arc.SetStart(VEC(cx + r * math.cos(a), cy + r * math.sin(a)))
        arc.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        arc.SetLayer(layer); arc.SetWidth(M(w))
        b.Add(arc)


def text(b, s, x, y, layer, size=1.0, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetLayer(layer); t.SetPosition(VEC(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(M(size), M(size))); t.SetTextThickness(M(0.15))
    t.SetMirrored(mirror); t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    b.Add(t)


def add_rule_area(b, layers, pts, name, no_tracks=True, no_vias=True, no_fill=True, no_fp=False):
    z = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(no_tracks); z.SetDoNotAllowVias(no_vias); z.SetDoNotAllowZoneFills(no_fill)
    z.SetDoNotAllowFootprints(no_fp); z.SetDoNotAllowPads(False)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(M(x), M(y))
    b.Add(z)


def square(cx, cy, h):
    return [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]


def hole_fp(b, fps, ref, x, y, d):
    fp = pcbnew.FootprintLoad(KICAD_FP + "/MountingHole.pretty", "MountingHole_2.2mm_M2")
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
    fp.SetReference(ref)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetPosition(VEC(x, y))
    for pad in fp.Pads():
        pad.SetSize(pcbnew.VECTOR2I(M(d), M(d))); pad.SetDrillSize(pcbnew.VECTOR2I(M(d), M(d)))
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
    for d_ in list(fp.GraphicalItems()):                      # the M2 holes sit in the gaps between the key bodies: no courtyard of their own
        if d_.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            fp.Remove(d_)
            GRAVE.append(d_)
    b.Add(fp)
    fps[ref] = fp
    return fp


def best_orientation(fp, x, y, ok):
    """Try the four orientations on the bottom face; the first for which ok(fp) holds."""
    for rot in (0, 90, 180, 270):
        set_pose(fp, x, y, rot)
        if ok(fp):
            return rot
    return None


def main():
    parts = json.load(open(os.path.join(BUILD, "partes_regua.json"), encoding="utf-8"))
    nl = netlist(os.path.join(BUILD, "regua_netlist.net"))
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    rect_edges(b, X(0), Y(VB), X(RL), Y(VF))
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
        libdir = os.path.join(KD, lib + ".pretty") if lib == "slim" else KICAD_FP + "/" + lib + ".pretty"
        fp = pcbnew.FootprintLoad(libdir, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(p["ref"]); fp.SetValue(p["value"])
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH(p["path"]))
        h = {"J1": "1.0", "U9": "1.03", "C10": "1.45"}.get(p["ref"], "0.41" if p["ref"] in ("U%d" % i for i in range(1, 9)) else "0.55")
        for k, v in (("Codigo", p["code"]), ("LCSC", p["lcsc"]), ("Montagem", p["mount"]), ("Description", p["note"]),
                     ("Datasheet", p.get("datasheet", "")), ("Altura_mm", h)):
            fp.SetField(k, v or "")
        for f_ in fp.GetFields():
            f_.SetVisible(False)
        for pad in fp.Pads():
            n = nl.get(p["ref"], {}).get(pad.GetNumber())
            if n:
                pad.SetNet(net_of(n))
        b.Add(fp)
        fps[p["ref"]] = fp
        to_bottom(fp)

    # ---- holes (footprints of their own: DRC and the 3D scene see them)
    for k, u in enumerate(KEYS_U):
        fp = pcbnew.FootprintLoad(KD + "/slim.pretty", "KS33D_holes")
        fp.SetFPID(pcbnew.LIB_ID("slim", "KS33D_holes"))
        fp.SetReference("SW%d" % (k + 1)); fp.SetValue("KS-33D (furos)")
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        for d_ in list(fp.GraphicalItems()):                  # courtyard = the switch body 14.0 (the library's 14.8 would touch the M2 holes' ring)
            if d_.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                fp.Remove(d_)
                GRAVE.append(d_)
        sh = pcbnew.PCB_SHAPE(fp)
        sh.SetShape(pcbnew.SHAPE_T_RECT)
        sh.SetStart(VEC(-7.0, -7.0)); sh.SetEnd(VEC(7.0, 7.0))
        sh.SetLayer(pcbnew.F_CrtYd); sh.SetWidth(M(0.05))
        fp.Add(sh)
        fp.SetPosition(VEC(X(u), Y(0.0)))
        b.Add(fp)
        fps["SW%d" % (k + 1)] = fp
    for i, (u, v) in enumerate(zip(M2_U, M2_V)):
        hole_fp(b, fps, "H%d" % (i + 1), X(u), Y(v), M2_D)

    # ---- sensors: the EasyEDA orientation (rows along u, 0.5 mm apart in v): VCC/GND row at the BACK, EN/OUT row at the FRONT
    def sensor_ok(fp):
        p1, p2, p3, p4 = (pad_xy(fp, n) for n in ("1", "2", "3", "4"))
        return p1[1] < p4[1] - 0.3 and abs(p1[0] - p4[0]) < 0.1 and abs(p2[1] - p1[1]) < 0.1

    rot_s = None
    for k in range(8):
        fp = fps["U%d" % (k + 1)]
        rot = best_orientation(fp, X(KEYS_U[k]), Y(SENS_V), sensor_ok)
        if rot is None:
            raise SystemExit("U%d: no orientation with VCC/GND behind EN/OUT" % (k + 1))
        rot_s = rot
    side_vcc = 1 if pad_xy(fps["U1"], "1")[0] > X(KEYS_U[0]) else -1     # the VCC pad's side (u)
    # ---- decoupling caps: pad 1 (+3V3) next to the VCC pad, pad 2 (GND, with a via to the top pour) further out, on the same row
    for k in range(8):
        c = fps["C%d" % (k + 1)]
        sx = X(KEYS_U[k])

        def cap_ok(fp, sx=sx):
            a, bb = pad_xy(fp, "1"), pad_xy(fp, "2")
            return abs(a[1] - bb[1]) < 0.1 and abs(a[0] - sx) < abs(bb[0] - sx) - 0.5
        rot = best_orientation(c, sx + side_vcc * 2.0, Y(SENS_V - 0.25), cap_ok)
        if rot is None:
            raise SystemExit("C%d: no horizontal orientation" % (k + 1))

    # ---- the tail
    j1 = fps["J1"]

    def ffc_ok(fp):          # mouth (towards the hold-down pads) towards -u; pad 1 towards the back (OUT, pad 3, then near the back band)
        sig = [pad_xy(fp, str(n)) for n in range(1, 9)]
        mp = [(T(pd.GetPosition().x), T(pd.GetPosition().y)) for pd in fp.Pads() if pd.GetNumber() == "MP"]
        sx = sum(p[0] for p in sig) / 8.0
        mx = sum(p[0] for p in mp) / 2.0
        return mx < sx - 1.0 and sig[0][1] < sig[7][1]

    rot_j = best_orientation(j1, X(FFC_U), Y(0.0), ffc_ok)
    ffc_pin1_back = True
    if rot_j is None:
        def ffc_ok2(fp):
            sig = [pad_xy(fp, str(n)) for n in range(1, 9)]
            mp = [(T(pd.GetPosition().x), T(pd.GetPosition().y)) for pd in fp.Pads() if pd.GetNumber() == "MP"]
            return sum(p[0] for p in mp) / 2.0 < sum(p[0] for p in sig) / 8.0 - 1.0
        rot_j = best_orientation(j1, X(FFC_U), Y(0.0), ffc_ok2)
        ffc_pin1_back = False
        if rot_j is None:
            raise SystemExit("J1: no orientation with the mouth towards -u")

    u9 = fps["U9"]

    def u9_ok(fp):           # the Q row (pins 2..7) towards the front
        return pad_xy(fp, "4")[1] > pad_xy(fp, "13")[1] + 1.0

    rot_u9 = best_orientation(u9, X(9.2), Y(0.0), u9_ok)
    if rot_u9 is None:
        raise SystemExit("U9: no orientation with the Q row to the front")
    set_pose(fps["C9"], X(6.0), Y(-3.4), 90)
    set_pose(fps["C10"], X(11.6), Y(-4.9), 0)

    # ---- keep-outs: the M2 nut under the ruler (D5.4, bottom), the bolt head on top (D4.8)
    for u, v in zip(M2_U, M2_V):
        add_rule_area(b, [pcbnew.B_Cu], square(X(u), Y(v), 2.7), "M2 porca (D5,4)")
        add_rule_area(b, [pcbnew.F_Cu], square(X(u), Y(v), 2.4), "M2 cabeca (D4,8)")
    # silkscreen / drawings
    for k, u in enumerate(KEYS_U):
        text(b, "tecla %d" % (k + 1), X(u), Y(-5.2), pcbnew.F_SilkS, 0.8)
    text(b, "SLIM R8 R3SL - FRENTE (jogador) EM BAIXO", X(RL / 2 + 9.25), Y(6.5), pcbnew.F_SilkS, 0.8)
    text(b, "FFC", X(1.2), Y(-5.0), pcbnew.B_SilkS, 0.8, mirror=True)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    os.makedirs(KD, exist_ok=True)
    out_pcb = os.path.join(KD, "slim_regua.kicad_pcb")
    pcbnew.SaveBoard(out_pcb, b)

    # ---- project and rules
    pro_path = os.path.join(KD, "slim_regua.kicad_pro")
    pro = json.load(open(pro_path)) if os.path.exists(pro_path) else {"meta": {"filename": "slim_regua.kicad_pro", "version": 3}}
    pro["board"] = {"design_settings": {"rules": {"min_clearance": 0.1, "min_copper_edge_clearance": EDGE, "min_hole_clearance": 0.25,
                                                  "min_hole_to_hole": 0.25, "min_through_hole_diameter": 0.3, "min_track_width": 0.15,
                                                  "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_text_height": 0.8,
                                                  "min_text_thickness": 0.12, "min_silk_clearance": 0.0, "min_connection": 0.1},
                                    "rule_severities": {"lib_footprint_mismatch": "ignore"}}}
    pro["net_settings"] = {"classes": [{"name": "Default", "clearance": 0.1, "track_width": 0.2, "via_diameter": 0.5, "via_drill": 0.3, "diff_pair_width": 0.2,
                                        "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                                        "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)"}],
                           "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []}
    json.dump(pro, open(pro_path, "w"), indent=2)
    open(os.path.join(KD, "slim_regua.kicad_dru"), "w", newline="\n").write("""(version 1)
# eTutti Slim ruler R8 -- custom rules (R3SL, stage 2a). Routing (stage 3) works under these.
(rule "Vias 0,5 / furo 0,3"
    (condition "A.Type == 'via'")
    (constraint via_diameter (min 0.5mm))
    (constraint hole_size (min 0.3mm)))
(rule "Trilhas: minimo 0,15; preferida 0,2"
    (condition "A.Type == 'track'")
    (constraint track_width (min 0.15mm) (opt 0.2mm)))
(rule "OUT (analogico) a 0,3 mm de DADO/CLOCK/LATCH (diafonia na leitura)"
    (condition "A.Type == 'track' && A.NetName == 'OUT' && (B.NetName == 'DATA' || B.NetName == 'CLK' || B.NetName == 'LATCH')")
    (constraint clearance (min 0.3mm)))
(rule "Nada no topo (lado das teclas): so cobre de trilha e plano, nenhuma peca"
    (condition "A.Type == 'Footprint' && A.Layer == 'F.Cu' && !A.Reference.startsWith('SW') && !A.Reference.startsWith('H')")
    (constraint disallow footprint))
""")

    # ---- dump
    rec = {"revisao": "R3SL", "origem": [OX, OY], "quadro": "x = OX + u, y = OY + v; +v para o jogador (borda da frente, y para baixo no KiCad)",
           "pcb_mm": [RL, RW], "pecas": {}, "pads": [], "furos": [], "teclas_u": KEYS_U,
           "orientacao": {"sensor_rot": rot_s, "lado_do_pad_vcc": side_vcc, "ffc_rot": rot_j, "ffc_pino1_atras": ffc_pin1_back, "u9_rot": rot_u9},
           "corredores": {"EN": {"v": [5.15, 7.25], "nota": "oito lanes EN1..EN8 da cauda aos sensores, faixa da frente, a camada de CIMA (um via por sensor)"},
                          "OUT": {"v": [5.15, 7.25], "nota": "barramento analogico OUT, faixa da frente, camada de BAIXO, longe de DADO/CLOCK/LATCH (>= 0,3 mm)"},
                          "VCC": {"v": [3.1, 3.5], "nota": "+3V3 em trilha de 0,3 mm na face de baixo, atras dos sensores (entre o furo do poste e a fileira VCC/GND)"}, "GND": {"nota": "plano na face de cima (lado das teclas), costurado com vias"}}}
    for ref, fp in fps.items():
        c = court(fp)
        rec["pecas"][ref] = {"u": round(T(fp.GetX()) - OX, 3), "v": round(T(fp.GetY()) - OY, 3), "rot": round(fp.GetOrientationDegrees(), 1),
                             "lado": "baixo" if fp.GetLayer() == pcbnew.B_Cu else "cima", "patio_uv": [round(c[0] - OX, 2), round(c[1] - OY, 2), round(c[2] - OX, 2), round(c[3] - OY, 2)],
                             "altura_mm": ({f.GetName(): f.GetText() for f in fp.GetFields()}).get("Altura_mm", ""), "fp": str(fp.GetFPID().GetLibItemName())}
        for pd in fp.Pads():
            sz = pd.GetSize()
            rec["pads"].append({"ref": ref, "n": pd.GetNumber(), "net": pd.GetNetname(), "u": round(T(pd.GetPosition().x) - OX, 3), "v": round(T(pd.GetPosition().y) - OY, 3),
                                "w": round(T(sz.x), 3), "h": round(T(sz.y), 3), "rot": round(pd.GetOrientationDegrees(), 1),
                                "furo": round(T(pd.GetDrillSize().x), 2)})
    json.dump(rec, open(os.path.join(HERE, "posicao_regua.json"), "w", encoding="utf-8"), indent=1)

    build_grade()
    for ref in ["U1", "U9", "J1", "C1", "C9", "C10"]:
        q = rec["pecas"][ref]
        print("%-3s u %7.2f v %6.2f rot %5.1f lado %s" % (ref, q["u"], q["v"], q["rot"], q["lado"]))
    print("orientacao", rec["orientacao"])


def dogbone_hole(b, cx, cy, h, inset, r, step_deg=4.0):
    """A square hole (half side h) with a dog-bone relief circle (radius r, centre inset mm in from the corner along both edges) in every corner: a closed polyline on Edge.Cuts."""
    d = math.sqrt(r * r - inset * inset)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):                 # corners, clockwise on the page (y down)
        ccx, ccy = sx * (h - inset), sy * (h - inset)
        a = (sx * h, ccy - sy * d)                                     # on the vertical edge, inner intersection
        bb = (ccx - sx * d, sy * h)                                    # on the horizontal edge, inner intersection
        ang_a = math.atan2(a[1] - ccy, a[0] - ccx)
        ang_b = math.atan2(bb[1] - ccy, bb[0] - ccx)
        mid = math.atan2(sy, sx)
        # sweep from A to B through the outward diagonal
        def norm(x):
            return (x + math.pi) % (2 * math.pi) - math.pi
        da = norm(mid - ang_a)
        db = norm(ang_b - mid)
        n = max(int((abs(da) + abs(db)) / math.radians(step_deg)), 6)
        seq = []
        for i in range(n + 1):
            t = i / n
            ang = ang_a + (da + db) * t
            seq.append((ccx + r * math.cos(ang), ccy + r * math.sin(ang)))
        pts.append(seq)
    # order: the corners come as (-,-),(+,-),(+,+),(-,+): on the page that is clockwise; each corner's arc runs from its vertical-edge point to its horizontal-edge point,
    # so for the clockwise walk we need, per corner, the arc reversed when the walk arrives along the horizontal edge. Build by walking: start at corner 0's B point.
    loop = []
    walk = [(0, False), (1, True), (2, False), (3, True)]
    for ci, rev in walk:
        seq = pts[ci]
        loop += list(reversed(seq)) if rev else seq
    for (x0, y0), (x1, y1) in zip(loop, loop[1:] + loop[:1]):
        seg(b, cx + x0, cy + y0, cx + x1, cy + y1, pcbnew.Edge_Cuts, 0.1)


def build_grade():
    """The grade: FR-4 1.2 mm, 155.5 x 16, eight 14.00 square holes with dog-bone corner reliefs (R4SL), two M2 holes at the right end (R9SL: NO countersink: pan head D3.8 on top). Its own board."""
    g = ENV["grade"]
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    gx0, gx1 = X(g["u0"]), X(g["u1"])
    gy0, gy1 = Y(-g["largura"] / 2), Y(g["largura"] / 2)
    rect_edges(b, gx0, gy0, gx1, gy1)
    h = g["furo"] / 2
    for u in KEYS_U:
        dogbone_hole(b, X(u), Y(0), h, g["dogbone"]["recuo"], g["dogbone"]["raio"])
    for u, v in zip(g["m2_u"], g["m2_v"]):
        fp = pcbnew.FootprintLoad(KICAD_FP + "/MountingHole.pretty", "MountingHole_2.2mm_M2")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
        fp.SetReference("H%d" % (g["m2_u"].index(u) + 1))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetPosition(VEC(X(u), Y(v)))
        for pad in fp.Pads():
            pad.SetSize(pcbnew.VECTOR2I(M(g["m2_d"]), M(g["m2_d"]))); pad.SetDrillSize(pcbnew.VECTOR2I(M(g["m2_d"]), M(g["m2_d"])))
        b.Add(fp)
    for u, v in zip(g["m2_u"], g["m2_v"]):
        text(b, "M2 cabeca cilindrica D3,8 (sem escareado)", X(u), Y(v + 3.2), pcbnew.Cmts_User, 0.6)
    pcbnew.SaveBoard(os.path.join(KD, "slim_grade.kicad_pcb"), b)


if __name__ == "__main__":
    main()
