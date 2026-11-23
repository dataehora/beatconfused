"""eTutti Student V4 (R3V4): the main board (interface only) PLACED, with NO tracks (portao P, parte 1).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/posiciona_v4.py

Run pcb/schematic.py first (it writes pcb/build/partes_v4.json and the netlist). Reads, never writes:
  student_v03/kicad/student_v03.kicad_pcb  (positions of the parts that stay, copper fields, board setup/stackup)
Writes:
  kicad/student_v04.kicad_pcb               (outline, parts on their sides, zones, rule areas; no track, no via)
  pcb/posicao_v4.json                       (positions, metrics, courtyards: input of pcb/vistas_v4.py and POSICIONAMENTO.md)

What is different from the V3 board (all by script, never by hand):
  * only the interface zone: outline 75 x 95.1 mm (x 2.45..77.5), rounded R 3; no key, no sensor, no multiplexer, no grid hole;
  * every JLCPCB part on the BOTTOM (only the two encoders and the speaker's wire pads are on top);
  * J101 (M.2) and the parts that follow it move left by DX so the USB-C, kept on the left wall, ends 6.7 mm from pads 3/5
    (USB pair <= 10 mm); the USB-C moves to y = 10.0 so its B6/A7 pads are level with pads 3/5 (R3V4, item 7);
  * J601..J604: the four row connectors (JST SH 6 way) on the right edge, mouths to +x, at the rows' y;
  * In2 = GND over the whole board (no island, no keep-out), In1 = +3V3, F.Cu and B.Cu GND pours (as the V3);
  * rule areas: copper-free ring round each M2 hole, the module card (parts under it <= 1.9 mm), the screen cable slot,
    the plug of row 2's connector.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr as S  # noqa: E402

HW = os.path.normpath(os.path.join(HERE, "..", ".."))
KD = os.path.normpath(os.path.join(HERE, "..", "kicad"))
V3PCB = os.path.join(HW, "student_v03", "kicad", "student_v03.kicad_pcb")
OUT = os.path.join(KD, "student_v04.kicad_pcb")
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
M, T = pcbnew.FromMM, pcbnew.ToMM
GRAVE = []

# ----------------------------------------------------------------------------- geometry (SPEC frame = KiCad x, y)
X0, Y0, X1, Y1 = 2.45, 2.45, 77.5, 97.55
CORNER_R = 3.0
DX = -5.5                       # J101 and its cluster: pads 3/5 end 6.74 mm from the USB-C pad row
# R12V4 (roteamento's request, 2nd run): U301 +2.0 mm in x (and its east-side decoupling with it) and R105 +1.5 mm in y: opens the ring of OUT/SCAN beams west of the codec
# (x 17..21, y 28..45); C304, C305, R305, C309, R306 (west side) stay.
R12_DELTA = {"U301": (2.0, 0.0), "C301": (2.0, 0.0), "C302": (2.0, 0.0), "C306": (3.5, 0.0), "C307": (2.0, 0.0), "FB301": (3.2, 0.0),
             "C310": (2.0, 0.0), "R105": (0.0, 1.5),
             "R605": (0.0, 0.0), "C305": (-1.0, 0.0), "C303": (0.0, 0.5), "C209": (0.0, -0.8), "R216": (0.0, -0.8)}      # 3rd run: C306 +1.5 and FB301 +1.0 more (north channel of U301 pins 16/18), R605 -1.0 x, C209 -0.8 y
R12_ROT = {"R605": 90.0}      # 4th run: R605 turned 90 deg (its courtyard then ends 0.5 mm nearer the J101 pad)
CLUSTER = {"J101", "H101", "TP101", "C101", "C102", "R301", "R302", "R105"}
USB_Y = 10.0                    # B6 (DP) and A7 (DN) level with pads 3/5 (y 9.25 / 9.75)
ROW_Y = {1: 74.03, 2: 58.01, 3: 41.99, 4: 25.97}      # the rows' centres (geometria.py)
RULER_X0 = {1: 89.2, 2: 79.95, 3: 89.2, 4: 98.45}      # first ruler's left end per row (case_f2.rulers)
RULER_IN_POCKET = True         # R4V4: the ruler's input connector is under the ruler, in the pocket: every row connector sits on the edge (row 2 too)
PLUG_GAP = 9.0                  # two SH plugs face to face + the cable's bend (estimate, CONFERIR)
MARGIN = 0.25
MIN_X_EDGE = 0.6                # parts keep this much from the outline (courtyard)
RING = 3.5                      # copper-free radius round the M2 holes (CLAUDE.md)
HOLES = {"H2": (74.0, 93.0), "H3": (6.5, 48.5), "H4": (8.0, 91.5), "H1": (62.0, 48.0)}
# routing corridors reserved at placement (R3V4, item 7): name -> (x0, y0, x1, y1, layers, what). Drawn on Cmts.User; the
# 'roteamento' agent routes the listed nets inside them and never moves a part.
CORRIDORS = {
    "USB": (11.0, 8.2, 16.0, 11.2, "B.Cu", "par D+/D- (USB_DP/USB_DN), 0,24/0,15 mm, sem via, In2 = GND por baixo"),
    "BUS_desce": (25.5, 8.0, 34.0, 54.0, "F.Cu+B.Cu", "OUT_R1..R4, SCAN_CLK_P/SCAN_DATA_P: do lado leste do J101 ate a faixa de baixo (F.Cu quase livre)"),
    "BUS_faixa": (25.5, 54.0, 70.0, 57.0, "F.Cu", "faixa horizontal OUT_R*, SCAN_CLK, SCAN_DATA ate a espinha"),
    "BUS_espinha": (68.5, 24.0, 71.0, 77.0, "F.Cu", "espinha vertical ate os 4 conectores de fileira (vias para os pads do fundo)"),
    "I2S_codec": (19.0, 20.0, 30.0, 34.0, "B.Cu", "I2S_BCLK/LRCLK/TX/RX, AUD_MCLK: J101 -> SGTL5000 (12 mm)"),
    "I2S_amp": (26.0, 58.0, 54.0, 86.0, "F.Cu", "I2S_BCLK/LRCLK/TX: J101 -> MAX98357A (U501), longos; guarda de GND"),
    "audio_fone": (6.0, 28.0, 26.0, 62.0, "B.Cu", "HP_L/HP_R/HP_VGND do SGTL5000 ao J301, MIC_J/MIC_BIAS ao J302 (HP_VGND nunca no GND)"),
    "energia": (50.0, 3.0, 77.0, 20.0, "B.Cu", "VBUS, VSYS, VBAT, BB_L1/L2 (classe Corrente, 0,8 mm)"),
    "VSYS_amp": (55.0, 20.0, 58.0, 86.0, "F.Cu", "VSYS ate o MAX98357A (0,8 mm), longo"),
}
MODULE_CARD = (30.2 + DX, 7.0, 49.5 + DX, 29.0)         # the 22 x 22 card (parts under it: Cabe_sob_cartao = sim)


def V(x, y):
    return pcbnew.VECTOR2I(M(x), M(y))


# ----------------------------------------------------------------------------- small helpers
def netlist(path):
    """{ref: {pin: net}} from kicad-cli's netlist (the same text schematic.py checks)."""
    tree = S.parse(open(path, encoding="utf-8").read())
    got = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        for x in S.find(n, "node"):
            got.setdefault(S.first(x, "ref")[1], {})[S.first(x, "pin")[1]] = name
    return got


def court(fp):
    layer = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
    try:
        bb = fp.GetCourtyard(layer).BBox()
        if bb.GetWidth() > 0:
            return (T(bb.GetX()), T(bb.GetY()), T(bb.GetX() + bb.GetWidth()), T(bb.GetY() + bb.GetHeight()))
    except Exception:
        pass
    bb = fp.GetBoundingBox(False)
    return (T(bb.GetX()), T(bb.GetY()), T(bb.GetX() + bb.GetWidth()), T(bb.GetY() + bb.GetHeight()))


def hole_boxes(fp, grow=0.7):
    out = []
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            bb = p.GetBoundingBox()
            out.append((T(bb.GetX()) - grow, T(bb.GetY()) - grow, T(bb.GetX() + bb.GetWidth()) + grow,
                        T(bb.GetY() + bb.GetHeight()) + grow))
    return out


def overlap(a, b, m=0.0):
    return a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m


def shifted(bb, dx, dy):
    return (bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy)


def side_of(fp):
    return "F" if fp.GetLayer() == pcbnew.F_Cu else "B"


def to_bottom(fp):
    pos = fp.GetPosition()
    try:
        fp.Flip(pos, pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    except Exception:
        fp.Flip(pos, False)


def set_pose(fp, x, y, rot):
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    fp.SetPosition(V(x, y))


def pad_xy(fp, num):
    return [(T(p.GetPosition().x), T(p.GetPosition().y)) for p in fp.Pads() if p.GetNumber() == num]


def mouth_dir(fp, kind):
    """Unit vector of the plug's mouth in board coordinates. USB-C: from the signal pads to the shield pads.
    SH side entry: opposite to the signal pads (towards the mounting pads)."""
    sig, oth = [], []
    for p in fp.Pads():
        x, y = T(p.GetPosition().x), T(p.GetPosition().y)
        n = p.GetNumber()
        if kind == "usbc":
            (oth if n in ("SH", "") else sig).append((x, y))
        else:
            (oth if n == "MP" else sig).append((x, y))
    cx = lambda l: (sum(p[0] for p in l) / len(l), sum(p[1] for p in l) / len(l))   # noqa: E731
    a, b = cx(sig), cx(oth)
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (dx / d, dy / d)


def orient_mouth(fp, kind, want):
    base = fp.GetOrientationDegrees()
    best = None
    for dr in (0, 90, 180, 270):
        fp.SetOrientation(pcbnew.EDA_ANGLE(base + dr, pcbnew.DEGREES_T))
        d = mouth_dir(fp, kind)
        s = d[0] * want[0] + d[1] * want[1]
        if best is None or s > best[0]:
            best = (s, base + dr)
    fp.SetOrientation(pcbnew.EDA_ANGLE(best[1], pcbnew.DEGREES_T))
    return best[0]


# ----------------------------------------------------------------------------- board
def new_board():
    old = pcbnew.LoadBoard(V3PCB)
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    b.SetDesignSettings(old.GetDesignSettings())
    return b, old


def outline(b):
    """Rounded rectangle on Edge.Cuts."""
    r = CORNER_R

    def seg(x0, y0, x1, y1):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(M(0.1))
        b.Add(s)

    def arc(cx, cy, a0):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        m = math.radians(a0 + 45)
        s.SetArcGeometry(V(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))),
                         V(cx + r * math.cos(m), cy + r * math.sin(m)),
                         V(cx + r * math.cos(math.radians(a0 + 90)), cy + r * math.sin(math.radians(a0 + 90))))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(M(0.1))
        b.Add(s)
    seg(X0 + r, Y0, X1 - r, Y0)
    seg(X1, Y0 + r, X1, Y1 - r)
    seg(X1 - r, Y1, X0 + r, Y1)
    seg(X0, Y1 - r, X0, Y0 + r)
    arc(X1 - r, Y0 + r, 270)
    arc(X1 - r, Y1 - r, 0)
    arc(X0 + r, Y1 - r, 90)
    arc(X0 + r, Y0 + r, 180)


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def add_zone(b, layers, pts, name, net=None, rule=False, no_tracks=False, no_vias=False, no_fill=False, no_fp=False,
             clearance=0.2):
    z = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    if not rule and net is not None:
        z.SetNet(net)
    z.SetZoneName(name)
    if rule:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(no_tracks)
        z.SetDoNotAllowVias(no_vias)
        z.SetDoNotAllowZoneFills(no_fill)
        z.SetDoNotAllowFootprints(no_fp)
        z.SetDoNotAllowPads(False)
    else:
        z.SetLocalClearance(M(clearance))
        z.SetMinThickness(M(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetAssignedPriority(0)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(M(x), M(y))
    b.Add(z)
    return z


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    parts = json.load(open(os.path.join(HERE, "build", "partes_v4.json"), encoding="utf-8"))
    nl = netlist(os.path.join(HERE, "build", "student_v04_netlist.net"))
    b, old = new_board()
    outline(b)
    netinfo = {}

    def net_of(name):
        if name not in netinfo:
            ni = pcbnew.NETINFO_ITEM(b, name)
            b.Add(ni)
            netinfo[name] = ni
        return netinfo[name]

    v3 = {}
    for fp in old.GetFootprints():
        fields = {f.GetName(): f.GetText() for f in fp.GetFields()}
        v3[fp.GetReference()] = dict(x=T(fp.GetX()), y=T(fp.GetY()), rot=fp.GetOrientationDegrees(), side=side_of(fp),
                                     fields=fields)

    fps, rec = {}, {"pecas": {}, "movidas": {}, "metricas": {}}

    def make(ref, libname, value, nets, path, code, lcsc, mount, extra, note="", dsheet=""):
        lib, name = libname.split(":")
        libdir = os.path.join(KD, lib + ".pretty") if lib == "viaggio_micromod" else os.path.join(KICAD_FP, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        if path:
            fp.SetPath(pcbnew.KIID_PATH(path))
        for k, v in (("Codigo", code), ("LCSC", lcsc), ("Montagem", mount), ("Description", note), ("Datasheet", dsheet))                 + tuple(extra.items()):
            fp.SetField(k, v or "")
        pins = nl.get(ref, {})
        for p in fp.Pads():
            n = pins.get(p.GetNumber())
            if n:
                p.SetNet(net_of(n))
        b.Add(fp)
        fps[ref] = fp
        return fp

    topside = {"SW401", "SW402", "J501"}
    for p in parts:
        ref = p["ref"]
        src = v3.get(ref, {})
        extra = {}
        for k in ("Altura_mm", "Cabe_sob_cartao"):
            if k in src.get("fields", {}):
                extra[k] = src["fields"][k]
        if ref.startswith(("J60", "R60", "C310", "R306", "C311")) or ref == "J401":
            if ref.startswith("J60") or ref == "J401":
                extra = {"Altura_mm": "4.3", "Cabe_sob_cartao": "nao"}
            else:
                extra = {"Altura_mm": "0.4", "Cabe_sob_cartao": "sim"}
        fp = make(ref, p["fp"], p["value"], None, p["path"], p["code"], p["lcsc"], p["mount"], extra, p["note"], p.get("datasheet", ""))
        if ref not in topside:
            to_bottom(fp)
        s = src.get("rot", 0)
        set_pose(fp, src.get("x", 40.0), src.get("y", 50.0), s)
    # the M2 holes and H101 (plain holes, as the V3)
    for ref, (x, y) in list(HOLES.items()) + [("H101", (47.5 + DX, 14.0))]:
        lib = "MountingHole"
        name = "MountingHole_2.7mm_M2.5" if ref == "H101" else "MountingHole_2.2mm_M2"
        fp = pcbnew.FootprintLoad(os.path.join(KICAD_FP, lib + ".pretty"), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(V(x, y))
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        b.Add(fp)
        fps[ref] = fp

    # --------------------------------------------------------------- phase 1: V3 positions (+ the cluster shift)
    for ref, fp in fps.items():
        if ref in v3 and ref in CLUSTER:
            set_pose(fp, v3[ref]["x"] + DX, v3[ref]["y"], v3[ref]["rot"])
    for ref in ("H1", "H2", "H3", "H4"):
        set_pose(fps[ref], *HOLES[ref], 0)

    # --------------------------------------------------------------- fixed new parts: USB-C and the row connectors
    j201 = fps["J201"]
    orient_mouth(j201, "usbc", (-1.0, 0.0))
    set_pose(j201, 5.95, USB_Y, j201.GetOrientationDegrees())
    mouth_x = {}
    for k in range(1, 5):
        j = fps["J60%d" % k]
        orient_mouth(j, "sh", (1.0, 0.0))
        j.SetPosition(V(50.0, ROW_Y[k]))
        cb = court(j)
        mx = (X1 - 0.1) if (RULER_IN_POCKET or RULER_X0[k] - X1 >= PLUG_GAP) else (RULER_X0[k] - PLUG_GAP)
        mouth_x[k] = mx
        j.SetPosition(V(50.0 + (mx - cb[2]), ROW_Y[k]))
    fixed = {"J201"} | {"J60%d" % k for k in range(1, 5)} | set(HOLES) | {"H101"}

    # rule areas (also obstacles for the search)
    ob_extra = []         # (box, applies to 'F','B' or 'both')
    for ref in list(HOLES) + ["H101"]:
        x, y = (T(fps[ref].GetX()), T(fps[ref].GetY()))
        ob_extra.append(((x - RING, y - RING, x + RING, y + RING), "both"))
    plug_boxes = {}
    for k in range(1, 5):
        if mouth_x[k] < X1 - 1.0:
            plug_boxes[k] = (mouth_x[k], ROW_Y[k] - 5.2, X1 - 0.3, ROW_Y[k] + 5.2)
            ob_extra.append((plug_boxes[k], "B"))
    card = MODULE_CARD

    def height_ok(ref, box):
        if not overlap(box, card):
            return True
        f = fps[ref]
        if ref in ("J101", "H101"):
            return True
        return f.GetFieldText("Cabe_sob_cartao") == "sim"

    def obstacles(skip):
        ob = {"F": [], "B": []}
        for ref, fp in fps.items():
            if ref in skip:
                continue
            if ref.startswith("H") and ref[1:].isdigit():
                continue                       # holes are in ob_extra
            side = side_of(fp)
            ob[side].append(court(fp))
            for hb in hole_boxes(fp):
                ob["F"].append(hb)
                ob["B"].append(hb)
        for box, s in ob_extra:
            for q in ("F", "B"):
                if s in ("both", q):
                    ob[q].append(box)
        return ob

    wall = {"J201", "J301", "J302", "J601", "J602", "J603", "J604"}      # the plug's mouth reaches the outline

    def free(ref, box, ob, margin=None):
        side = side_of(fps[ref])
        if ref in wall:
            pass
        elif box[0] < X0 + MIN_X_EDGE or box[1] < Y0 + MIN_X_EDGE or box[2] > X1 - MIN_X_EDGE or box[3] > Y1 - MIN_X_EDGE:
            return False
        if not height_ok(ref, box):
            return False
        return not any(overlap(box, o, MARGIN if margin is None else margin) for o in ob[side])

    offs = sorted(((i * 0.25, j * 0.25) for i in range(-160, 161) for j in range(-160, 161)),
                  key=lambda d: d[0] * d[0] + d[1] * d[1])

    def settle(ref, ax, ay, skip):
        """Move ref to the nearest free spot to (ax, ay); returns the shift from where it was."""
        fp = fps[ref]
        x0, y0 = T(fp.GetX()), T(fp.GetY())
        set_pose(fp, ax, ay, fp.GetOrientationDegrees())
        ob = obstacles(skip | {ref})
        c = court(fp)
        for dx, dy in offs:
            if free(ref, shifted(c, dx, dy), ob):
                set_pose(fp, ax + dx, ay + dy, fp.GetOrientationDegrees())
                return (ax + dx - x0, ay + dy - y0)
        raise SystemExit("%s: no free spot" % ref)

    # --------------------------------------------------------------- who is in the way of the fixed parts?
    def conflicts(ref):
        fp = fps[ref]
        box = court(fp)
        ob = obstacles({ref})
        side = side_of(fp)
        if not height_ok(ref, box):
            return True
        return any(overlap(box, o, MARGIN) for o in ob[side])

    for ref_, (dx_, dy_) in R12_DELTA.items():           # R12V4: the codec group and R105 start from their displaced spots (a part still free there stays; the others settle nearby)
        if ref_ in fps and ref_ not in fixed:
            f_ = fps[ref_]
            set_pose(f_, T(f_.GetX()) + dx_, T(f_.GetY()) + dy_, R12_ROT.get(ref_, f_.GetOrientationDegrees()))
    keep_order = [r for r in fps if r not in fixed]
    # (1) everything already on the board but in the way of a fixed part or of another part moves
    placed = set(fixed)
    pending = []
    for ref in keep_order:
        if ref in ("U201", "R201", "R202", "D201", "J401") or ref.startswith(("J60", "R60", "C310", "R306", "C311")):
            pending.append(ref)
            continue
        fp = fps[ref]
        box = court(fp)
        ob = obstacles(set(fps) - placed)         # only what is already settled
        if ref in v3 and free(ref, box, ob, -0.15) or ref in ("J101",):
            placed.add(ref)
        else:
            pending.append(ref)
    for ref in pending:
        # preferred spot = where it was in the V3 (shifted if it is of the cluster), or an anchor set below
        pass

    # --------------------------------------------------------------- anchors for the movers
    def anchor_of(ref):
        if ref in ("R601", "R602", "R603", "R604"):
            j = fps["J60%s" % ref[-1]]
            return (T(j.GetX()) - 8.0, T(j.GetY()))
        if ref in ("R605", "R606"):
            n = "47" if ref == "R606" else "32"        # SCAN_DATA_P pad 47, SCAN_CLK_P pad 32
            px_, py_ = pad_xy(fps["J101"], n)[0]
            return (px_ + R12_DELTA.get(ref, (0.0, 0.0))[0], py_ + R12_DELTA.get(ref, (0.0, 0.0))[1])
        if ref == "C310":
            u = fps["U301"]
            return (T(u.GetX()), T(u.GetY()) + 3.0)
        if ref in ("R306", "C311"):          # R6V4: next to C309 (the MIC_J node)
            c9 = fps["C309"]
            return (T(c9.GetX()) + (2.0 if ref == "R306" else 4.0), T(c9.GetY()) + 2.5)
        if ref == "J401":
            return (35.5 + DX * 0.6, 37.5)
        if ref in v3:
            dxr, dyr = R12_DELTA.get(ref, (0.0, 0.0))
            return (v3[ref]["x"] + (DX if ref in CLUSTER else 0.0) + dxr, v3[ref]["y"] + dyr)
        return (40.0, 50.0)

    for ref in [r for r in pending if r not in ("U201", "R201", "R202", "D201", "J401")]:
        ax, ay = anchor_of(ref)
        d = settle(ref, ax, ay, set(fps) - placed)
        placed.add(ref)
        if ref in v3:
            rec["movidas"][ref] = [round(d[0], 2), round(d[1], 2)]

    # --------------------------------------------------------------- the USB group: search for the shortest D+/D- path
    jm = fps["J101"]
    m2 = {"DP": pad_xy(jm, "3")[0], "DN": pad_xy(jm, "5")[0]}
    usb = {"DP": pad_xy(j201, "B6") + pad_xy(j201, "A6"), "DN": pad_xy(j201, "A7") + pad_xy(j201, "B7")}
    u = fps["U201"]
    best = None
    ob = obstacles(set(fps) - placed - {"U201"})
    cj = court(jm)
    USB_ROTS = tuple(int(x) for x in os.environ.get("U201_ROTS", "0,180").split(","))   # R12V4 (roteamento's request): U201 turned 90 deg from the R3V4 choice (90): D+ (pins 1/6) and D- (3/4) then run straight across the chip
    for rot in USB_ROTS:
        u.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        for ix in range(int((11.0) / 0.25), int((cj[0] + 2) / 0.25)):
            for iy in range(int(4.5 / 0.25), int(22.0 / 0.25)):
                x, y = ix * 0.25, iy * 0.25
                u.SetPosition(V(x, y))
                box = court(u)
                if not free("U201", box, ob):
                    continue
                cost = 0.0
                for net, pins in (("DP", ("1", "6")), ("DN", ("3", "4"))):
                    a, bb_ = pad_xy(u, pins[0])[0], pad_xy(u, pins[1])[0]
                    c1 = min(math.hypot(q[0] - a[0], q[1] - a[1]) + math.hypot(bb_[0] - m2[net][0], bb_[1] - m2[net][1])
                             for q in usb[net])
                    c2 = min(math.hypot(q[0] - bb_[0], q[1] - bb_[1]) + math.hypot(a[0] - m2[net][0], a[1] - m2[net][1])
                             for q in usb[net])
                    cost = max(cost, min(c1, c2))
                if best is None or cost < best[0]:
                    best = (cost, x, y, rot)
    if best is None:
        raise SystemExit("U201: no spot")
    # R12V4: the pair goes STRAIGHT through the chip: rot 0/180 (pins 1,2,3 in one column... D+ pins 1 and 6 on opposite columns), centred on the pair's line
    # (y 9.5, between the USB-C pads and the M.2's 3/5), D+ row to the north (M.2 pad 3 is the northern one). The courtyard is 4.19 mm wide and the gap between
    # J201's and J101's courtyards 4.34 mm: the 0.25 mm grid search cannot find it, so it is placed by hand (checked below against the courtyards).
    ux = (court(j201)[2] + court(jm)[0]) / 2
    for rot in (0, 180):
        set_pose(u, ux, 9.5, rot)
        if pad_xy(u, "1")[0][1] < pad_xy(u, "3")[0][1]:
            break
    bx = court(u)
    if bx[0] < court(j201)[2] or bx[2] > court(jm)[0]:
        raise SystemExit("U201 straight-through does not fit between J201 and J101: %s" % (bx,))
    best = (0.0, ux, 9.5, rot)
    set_pose(u, best[1], best[2], best[3])
    placed.add("U201")
    rec["metricas"]["usb_par_estimado_mm"] = round(best[0], 2)
    for ref in ("R201", "R202", "D201"):
        pins = {"R201": "A5", "R202": "B5", "D201": "A4"}[ref]
        ax, ay = pad_xy(j201, pins)[0]
        settle(ref, ax + 3.5, ay, set(fps) - placed)
        placed.add(ref)

    # --------------------------------------------------------------- screen connector + the cable slot
    j = fps["J401"]
    orient_mouth(j, "sh", (0.0, -1.0))
    ax, ay = anchor_of("J401")
    ob = obstacles(set(fps) - placed - {"J401"})
    slot = None
    base_c = None
    set_pose(j, ax, ay, j.GetOrientationDegrees())
    base_c = court(j)
    for dx, dy in offs[:20000]:
        box = shifted(base_c, dx, dy)
        if not free("J401", box, ob):
            continue
        # slot 7 x 2.5 mm just in front of the mouth (towards -y), >= 1.5 mm from the connector
        # R4V4: the SH plug (7.6 x 5.0) sits in front of the mouth and the wires leave its far end, so the slot goes BEYOND the plug
        cx_ = (box[0] + box[2]) / 2
        plug = (cx_ - 3.8, box[1] - 5.0, cx_ + 3.8, box[1])
        if not free("J401", plug, ob):
            continue
        for gap in (5.5, 6.0, 6.5, 7.0):
            sb = (cx_ - 3.5, box[1] - gap - 2.5, cx_ + 3.5, box[1] - gap)
            if free("J401", sb, ob) and not overlap(sb, box, 0.3):
                slot = sb
                break
        if slot:
            set_pose(j, T(j.GetX()) + dx, T(j.GetY()) + dy, j.GetOrientationDegrees())
            break
    if not slot:
        raise SystemExit("J401: no spot with a slot")
    placed.add("J401")
    pts = [(slot[0], slot[1]), (slot[2], slot[1]), (slot[2], slot[3]), (slot[0], slot[3])]
    for i in range(4):
        sh = pcbnew.PCB_SHAPE(b)
        sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(V(*pts[i]))
        sh.SetEnd(V(*pts[(i + 1) % 4]))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(M(0.1))
        b.Add(sh)
    rec["metricas"]["fenda_do_cabo"] = [round(v, 2) for v in slot]

    # --------------------------------------------------------------- zones
    gnd, v33 = net_of("GND"), net_of("+3V3")
    board_pts = rect_pts(X0, Y0, X1, Y1)
    # the F.Cu / B.Cu GND pours come with the routing (the 'roteamento' agent); a pour without tracks only starves its pads
    add_zone(b, [pcbnew.In1_Cu], board_pts, "L2 +3V3", v33)
    add_zone(b, [pcbnew.In2_Cu], board_pts, "L3 GND inteira (referencia do par USB)", gnd)
    allcu = [pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu]
    for ref in list(HOLES) + ["H101"]:
        x, y = T(fps[ref].GetX()), T(fps[ref].GetY())
        r_ = RING if ref != "H101" else RING
        add_zone(b, allcu, rect_pts(x - r_, y - r_, x + r_, y + r_), "M2 " + ref, rule=True, no_tracks=True,
                 no_vias=True, no_fill=True)
    add_zone(b, [pcbnew.B_Cu], rect_pts(*card), "cartao_MicroMod", rule=True)
    # R12V4: marker for the .kicad_dru: VSYS may be 0.5 mm (not 0.8) between C206, U204 and C210, where the outline of the power block leaves no room (marker only: nothing is forbidden)
    add_zone(b, [pcbnew.B_Cu, pcbnew.F_Cu], rect_pts(63.0, 6.5, 72.5, 15.5), "vsys_estreito", rule=True)
    add_zone(b, allcu, rect_pts(*slot), "fenda do cabo da tela", rule=True, no_tracks=True, no_vias=True, no_fill=True)
    for k, pb in plug_boxes.items():
        add_zone(b, [pcbnew.B_Cu], rect_pts(*pb), "plugue J60%d (cabo SH)" % k, rule=True, no_fp=True)

    for name, (cx0, cy0, cx1, cy1, lay, what) in CORRIDORS.items():
        for (ax_, ay_, bx_, by_) in ((cx0, cy0, cx1, cy0), (cx1, cy0, cx1, cy1), (cx1, cy1, cx0, cy1), (cx0, cy1, cx0, cy0)):
            sh = pcbnew.PCB_SHAPE(b)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(V(ax_, ay_))
            sh.SetEnd(V(bx_, by_))
            sh.SetLayer(pcbnew.Cmts_User)
            sh.SetWidth(M(0.1))
            b.Add(sh)
        tx = pcbnew.PCB_TEXT(b)
        tx.SetText("corredor " + name)
        tx.SetLayer(pcbnew.Cmts_User)
        tx.SetPosition(V(cx0 + 0.5, cy0 + 0.8))
        tx.SetTextSize(pcbnew.VECTOR2I(M(0.8), M(0.8)))
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        b.Add(tx)
    rec["corredores"] = {k: list(v) for k, v in CORRIDORS.items()}

    # --------------------------------------------------------------- metrics, dump
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    pcbnew.SaveBoard(OUT, b)
    usbc_pads = [q for n in ("B6", "A7", "A6", "B7") for q in pad_xy(j201, n)]
    ux = sum(q[0] for q in usbc_pads) / 4
    uy = sum(q[1] for q in usbc_pads) / 4
    m35 = ((m2["DP"][0] + m2["DN"][0]) / 2, (m2["DP"][1] + m2["DN"][1]) / 2)
    rec["metricas"]["usbc_a_pads_3_5_mm"] = round(math.hypot(ux - m35[0], uy - m35[1]), 2)
    rec["metricas"]["usbc_pads_xy"] = [round(ux, 2), round(uy, 2)]
    rec["metricas"]["pads_3_5_xy"] = [round(m35[0], 2), round(m35[1], 2)]
    rec["metricas"]["contorno_mm"] = [round(X1 - X0, 2), round(Y1 - Y0, 2)]
    rec["metricas"]["mouth_x_fileiras"] = {str(k): round(v, 2) for k, v in mouth_x.items()}
    for ref, fp in fps.items():
        rec["pecas"][ref] = {"x": round(T(fp.GetX()), 3), "y": round(T(fp.GetY()), 3), "rot": round(fp.GetOrientationDegrees(), 1),
                             "lado": side_of(fp), "patio": [round(v, 2) for v in court(fp)]}
    rec["pads"] = []
    for ref, fp in fps.items():
        for pd in fp.Pads():
            sz = pd.GetSize()
            rec["pads"].append({"ref": ref, "n": pd.GetNumber(), "net": pd.GetNetname(), "x": round(T(pd.GetPosition().x), 3),
                                "y": round(T(pd.GetPosition().y), 3), "w": round(T(sz.x), 3), "h": round(T(sz.y), 3),
                                "rot": round(pd.GetOrientationDegrees(), 1),
                                "th": pd.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH),
                                "lado": side_of(fp)})
    rec["zonas"] = {"cartao": list(card), "plugues": {str(k): v for k, v in plug_boxes.items()}, "aneis_furos": RING}
    rec["contorno"] = [X0, Y0, X1, Y1]
    json.dump(rec, open(os.path.join(HERE, "posicao_v4.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(rec["metricas"], indent=1))
    print("movidas:", rec["movidas"])


if __name__ == "__main__":
    main()
