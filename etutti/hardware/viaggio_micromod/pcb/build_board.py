"""Build the eTutti Viaggio MicroMod main board for routing by hand (SPEC v2.3, step M2).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/build_board.py

Run schematic.py first (it writes build/viaggio_micromod_netlist.net, the
footprints and the project). NOTHING HERE ROUTES: no track, no via, no router
(the Viaggio v2.1's router.py is not used). J routes the board in KiCad with
the Freerouting plugin (SPEC v2.2 section 7). This one script does what the
v2.1 did in build_board.py + handoff_freerouting.py:

  1. reads the netlist (kicad-cli has no "update PCB from schematic"): every
     component with its footprint, its Codigo (SPEC section 3), its sheet and
     symbol UUID; every pad's net, the unconnected ones included;
  2. builds the 4-layer 1.2 mm board (JLCPCB JLC04121H-7628): rectangle
     x 2.5-249, y 2.5-97.5, R 5 corners; the 8 M2 holes of the contract with a
     3.5 mm copper-free ring; silkscreen (profile A dotted, the v1 places of E1
     and F2 dashed, the logo area, the codes P1 ... T4);
  3. places every part from concept/out/viaggio_micromod.json: the main part
     of each code at its spot, the passives next to their chip, the 28
     TMAG5253 under the keys as on the Pocket, the 28 Gateron footprints;
     P1 = J101 (M.2 socket) + H101 (standoff) on the back, turned so the USB
     and I2S pads face E2 and F1 (see PLACE_P1); a named rule area
     "cartao_MicroMod" over the 22 x 22 card, and a check that nothing taller
     than 1.9 mm sits under it (HEIGHT_MM);
  4. links every footprint to its schematic symbol (F8 and the DRC's
     schematic parity are clean), nudges the few parts whose courtyards
     overlap, sets In1 = GND power plane (one whole GND zone), In2 = signal
     (no zone: SPEC v2.3), writes net classes, rules (kicad_pro), the custom
     rules (kicad_dru) and the stack-up;
  5. fills the zones, runs KiCad's DRC with schematic parity, writes
     build/viaggio_micromod.dsn, build/viaggio_micromod_handoff.json and the
     pictures build/viaggio_micromod_top.png / _bottom.png.

Exits non-zero on any DRC error (unrouted connections are expected: they are
J's job), a parity error, a rules-file error or a tall part under the card.

DO NOT run this over a board J has started routing: it rebuilds
kicad/viaggio_micromod.kicad_pcb from scratch.
"""
import csv
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pcbnew  # noqa: E402

import footprints as FPS  # noqa: E402
import sexpr as S  # noqa: E402

KICAD_BIN = os.path.dirname(sys.executable)
KICAD_CLI = os.path.join(KICAD_BIN, "kicad-cli.exe" if os.name == "nt" else "kicad-cli")
FP_ROOT = os.path.normpath(os.path.join(KICAD_BIN, "..", "share", "kicad", "footprints"))
NAME = "viaggio_micromod"
KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
LOCAL_PRETTY = os.path.join(KDIR, NAME + ".pretty")
BOARD_PATH = os.path.join(KDIR, NAME + ".kicad_pcb")
PRO_PATH = os.path.join(KDIR, NAME + ".kicad_pro")
DRU_PATH = os.path.join(KDIR, NAME + ".kicad_dru")
NETLIST = os.path.join(BUILD, NAME + "_netlist.net")
DRC_OUT = os.path.join(BUILD, NAME + "_drc.json")
MM = os.path.normpath(os.path.join(HERE, ".."))
PLAN = json.load(open(os.path.join(MM, "concept", "out", "viaggio_micromod.json"), encoding="utf-8"))
# the v1 places of E1/F2 (dashed on the silkscreen) live only in the archived Viaggio (read only)
CONCEPT_V1 = json.load(open(os.path.normpath(os.path.join(MM, "..", "viaggio", "concept", "out",
                                                          "viaggio_concept.json")), encoding="utf-8"))
POCKET_KEYS = os.path.normpath(os.path.join(MM, "..", "pocket", "pcb", "build", "pocket_keys.csv"))
IMPEDANCE = json.load(open(os.path.join(BUILD, "impedance.json")))

# ------------------------------------------------------------------ rules (mm)
THICKNESS = 1.2
CLEAR = 0.1                 # copper to copper (JLCPCB 4-layer minimum: 0.09)
TRACK = 0.2                 # signals (SPEC section 4, 8th)
THIN = 0.15                 # signals at the entry of fine-pitch pins (SPEC v2.3)
POWER_W = 0.8               # Corrente class (SPEC section 4, 3rd)
VIA_D, VIA_DRILL = 0.5, 0.3  # every class (SPEC v2.2: a 0.2 hole doubles the price)
HOLE_CLEAR = 0.2
EDGE_CLEAR = 0.3
USB_W = IMPEDANCE["usb"]["w"]   # 0.24 on F.Cu over In1 GND: Zdiff 91.2 ohm (impedance.py)
USB_S = IMPEDANCE["usb"]["s"]   # 0.15
M2_KEEP = 3.5               # copper-free radius round each M2 hole (SPEC section 2)
HEAD_R = 1.9                # M2 screw head (courtyard of the holes)
CARD_MAX_H = 1.9            # parts under the MicroMod card (Designing with MicroMod, 4.2 mm socket)

POWER_NETS = ["VBUS", "VSYS", "VBAT", "BB_L1", "BB_L2"]
POWER_PADS = ["J201", "U202", "U204", "J202", "U501", "J101"]    # E1, E3, E4, E6, A1, P1: thin entry allowed

# P1 (SPEC v2.3: orientation free, shortest USB and I2S). The socket's pin row runs along y on the
# left edge of sector P, pin 1 (USB pads 3/5) at the back towards E2, the card towards +x:
#   origin = centre of the pin field on the locating holes' line.
PLACE_P1 = (27.5, 18.0)

# heights above the board, mm (datasheets / KiCad 3D models; (conferir) in ELETRONICA.md)
HEIGHT_MM = [("J101", 4.2), ("H101", 2.5), ("SW40", 20.0), ("J201", 3.3), ("J301", 5.1), ("J202", 6.0),
             ("J501", 0.0), ("TP", 0.0), ("SW403", 1.5), ("SW", 11.6), ("H", 0.0), ("L201", 2.0), ("D401", 0.6),
             ("C_0805", 1.45), ("C_0603", 0.95), ("C_0402", 0.55), ("R_0402", 0.4), ("L_0603", 0.95),
             ("SOT-23", 1.45), ("SOD-123F", 1.1), ("QFN", 1.0), ("TQFN", 0.8), ("VQFN", 1.0), ("DRC0010J", 1.0),
             ("TSSOP", 1.2), ("X2SON", 0.4)]


def height_of(fp):
    ref, fpid = fp.GetReference(), fp.GetFPIDAsString()
    for key, h in HEIGHT_MM:
        if ref.startswith(key) or key in fpid:
            return h
    return 99.0


# ======================================================================= netlist
def load_netlist():
    tree = S.parse(open(NETLIST, encoding="utf-8").read())
    comps = {}
    for c in S.find(S.first(tree, "components"), "comp"):
        ref = S.first(c, "ref")[1]
        props = {}
        for p in S.find(c, "property"):
            v = S.first(p, "value")
            props[S.first(p, "name")[1]] = v[1] if v else ""
        for f in S.find(S.first(c, "fields") or [], "field"):
            vals = [x for x in f[1:] if not isinstance(x, list)]
            props[S.first(f, "name")[1]] = vals[0] if vals else ""
        sheet = S.first(S.first(c, "sheetpath"), "tstamps")[1]
        stamp = S.first(c, "tstamps")[1].split()[0]
        comps[ref] = dict(ref=ref, value=S.first(c, "value")[1], fp=S.first(c, "footprint")[1],
                          code=props.get("Codigo", ""), props=props, path=sheet + stamp)
    pads = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1]
        if not name.startswith("unconnected-"):
            name = name.lstrip("/")
        for nd in S.find(n, "node"):
            pads[(S.first(nd, "ref")[1], S.first(nd, "pin")[1])] = name
    return comps, pads


# ======================================================================= board helpers
board = None
nets = {}


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def xy(v):
    return (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = LOCAL_PRETTY if lib == NAME else os.path.join(FP_ROOT, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint not found: %s" % fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def place(fpid, ref, x, y, rot=0, back=False, value=None):
    fp = load_fp(fpid)
    fp.SetReference(ref)
    if value:
        fp.SetValue(value)
    fp.SetPosition(mm(x, y))
    board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    if rot:
        fp.SetOrientationDegrees((fp.GetOrientationDegrees() + rot) % 360)
    fp.Value().SetVisible(False)
    fp.Reference().SetVisible(False)
    return fp


def pad_of(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError((fp.GetReference(), num))


def fp_box(fp):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = g.GetBoundingBox()
            xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
            ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    if not xs:
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
            ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    return (min(xs), min(ys), max(xs), max(ys))


def seg(layer, a, b, w=0.12):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(mm(*a))
    s.SetEnd(mm(*b))
    s.SetLayer(layer)
    s.SetWidth(pcbnew.FromMM(w))
    board.Add(s)


def text(s, x, y, size=1.0, layer=None, rot=0, bold=False):
    layer = pcbnew.F_SilkS if layer is None else layer
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(mm(x, y))
    t.SetLayer(layer)
    t.SetTextSize(mm(size, size))
    t.SetTextThickness(pcbnew.FromMM(size * (0.2 if bold else 0.15)))
    if rot:
        t.SetTextAngleDegrees(rot)
    if layer in (pcbnew.B_SilkS, pcbnew.B_Fab):
        t.SetMirrored(True)
    board.Add(t)
    return t


def dashed(layer, pts, dash, gap, w=0.12, closed=False):
    """Own dash pattern (plotted as plain segments, so every Gerber viewer shows it)."""
    pts = list(pts) + ([pts[0]] if closed else [])
    on, left = True, dash
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < L - 1e-9:
            step = min(left, L - t)
            a = (x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L)
            b = (x0 + (x1 - x0) * (t + step) / L, y0 + (y1 - y0) * (t + step) / L)
            if on:
                seg(layer, a, b, w)
            t += step
            left -= step
            if left <= 1e-9:
                on = not on
                left = dash if on else gap


def point_in_poly(p, poly):
    x, y = p
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


PROFILE = [tuple(p) for p in PLAN["profile_a"]]


def box_in_profile(b):
    return all(point_in_poly(c, PROFILE) for c in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])))


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# ======================================================================= P1 frame
def socket_frame(j):
    """Affine map footprint (mm) -> board (mm) of the placed J101, from three of its pads."""
    p1 = xy(pad_of(j, "1").GetPosition())
    p75 = xy(pad_of(j, "75").GetPosition())
    p2 = xy(pad_of(j, "2").GetPosition())
    ex = ((p1[0] - p75[0]) / 18.5, (p1[1] - p75[1]) / 18.5)
    ey = ((p1[0] - p2[0] - 0.25 * ex[0]) / (FPS.M2_ODD_Y - FPS.M2_EVEN_Y),
          (p1[1] - p2[1] - 0.25 * ex[1]) / (FPS.M2_ODD_Y - FPS.M2_EVEN_Y))
    o = (p1[0] - 9.25 * ex[0] - FPS.M2_ODD_Y * ey[0], p1[1] - 9.25 * ex[1] - FPS.M2_ODD_Y * ey[1])
    return lambda u, v: (round(o[0] + u * ex[0] + v * ey[0], 4), round(o[1] + u * ex[1] + v * ey[1], 4))


CARD = {}                   # "rect": card outline on the board, "standoff": H101 centre


# ======================================================================= placement
def place_all(comps, pads):
    """Returns ({ref: footprint}, keys, deviations)."""
    fps = {}
    dev = []                                   # where a part left its JSON spot, and why
    codes = {p["code"]: p for p in PLAN["parts"] if "code" in p}

    def put(ref, x, y, rot, side):
        c = comps[ref]
        f = place(c["fp"], ref, x, y, rot, back=(side == "B"), value=c["value"])
        for p in f.Pads():
            n = pads.get((ref, p.GetNumber()))
            if n:
                p.SetNet(net(n))
        fps[ref] = f
        return f

    def centre_on(f, x, y):
        x0, y0, x1, y1 = fp_box(f)
        fx, fy = xy(f.GetPosition())
        f.SetPosition(mm(fx + x - (x0 + x1) / 2, fy + y - (y0 + y1) / 2))

    # ---- P1: J101 on the back, pin 1 at the back (small y), card towards +x ----
    j = None
    for rot in (0, 90, 180, 270):
        j = put("J101", PLACE_P1[0], PLACE_P1[1], rot, "B")
        p1, p75, p2 = (xy(pad_of(j, n).GetPosition()) for n in ("1", "75", "2"))
        if p2[0] > p1[0] + 5 and p1[1] < p75[1]:
            break
        board.Remove(j)
    T = socket_frame(j)
    corners = [T(FPS.M2_CARD[0], FPS.M2_CARD[1]), T(FPS.M2_CARD[2], FPS.M2_CARD[3])]
    CARD["rect"] = (min(c[0] for c in corners), min(c[1] for c in corners),
                    max(c[0] for c in corners), max(c[1] for c in corners))
    CARD["standoff"] = T(*FPS.M2_STANDOFF)
    put("H101", CARD["standoff"][0], CARD["standoff"][1], 0, "B")
    bj = fp_box(j)
    sp = codes["P1"]
    dev.append(("P1 (J101 + cartao)", "(%.1f; %.1f), %.0f x %.0f, conector ao longo de x" %
                (sp["x"], sp["y"], sp["w"], sp["h"]),
                "conector ao longo de y na borda esquerda do setor (x %.1f-%.1f, y %.1f-%.1f), pino 1 atras, "
                "cartao para +x (x %.1f-%.1f, y %.1f-%.1f)" % ((bj[0], bj[2], bj[1], bj[3]) + tuple(
                    CARD["rect"][i] for i in (0, 2, 1, 3))),
                "USB (pads 3/5) de frente para o E2: par E1-E2-J101 com ~15 mm em vez de ~25; I2S (pads 50-58) a ~14 mm do F1"))

    # ---- main part of every other code at its JSON spot ----
    main = {"E1": ["J201"], "E2": ["U201"], "E3": ["U202"], "E4": ["U204", "L201"], "E6": ["J202"],
            "F1": ["U301"], "F2": ["J301"], "I1": ["SW401"], "I2": ["SW402"], "I3": ["D401"], "I4": ["SW403"],
            "A1": ["U501"], "T1": ["U601"], "T2": ["U602"], "T3": ["U603", "U604", "U605"]}
    side_of = {"E2": "T"}                      # SPEC v2.3: E2 on the top, next to the USB-C (JSON: bot)
    for code, refs in main.items():
        spec = codes[code]
        side = side_of.get(code, "B" if spec["side"] == "bot" else "T")
        if code in side_of:
            dev.append((code, "lado %s no JSON (v2.2)" % spec["side"], "lado de cima",
                        "SPEC v2.3: E2 no lado de cima, junto do USB-C; USB em F.Cu sobre o In1"))
        for ref in refs:
            rot = 0
            if ref == "J201":
                rot = 270           # mouth to -x (left edge)
            elif ref == "J301":
                rot = 90            # mouth to -x
            elif ref == "U201":
                rot = 180           # D- row (pads 3/4) on top, the order the pair leaves J201 in: the
                                    # USB pair runs straight J201 -> U201 -> J101 (route_usb.py)
            elif code in ("T1", "T2"):
                rot = 90            # long side along x (JSON box 7.8 x 4.4)
            elif code in ("I1", "I2"):
                rot = 90
            f = put(ref, spec["x"], spec["y"], rot, side)
            centre_on(f, spec["x"], spec["y"])
        if len(refs) > 1:           # side by side, 0.4 mm apart, the group centred on the JSON spot
            boxes = [fp_box(fps[r]) for r in refs]
            total = sum(b[2] - b[0] for b in boxes) + 0.4 * (len(refs) - 1)
            x = spec["x"] - total / 2
            for r, b in zip(refs, boxes):
                w = b[2] - b[0]
                centre_on(fps[r], x + w / 2, spec["y"])
                x += w + 0.4
    # E1, F2: mouth flush with the left edge of the rectangle (x 2.5)
    for ref in ("J201", "J301"):
        f = fps[ref]
        x0 = min(pcbnew.ToMM(p.GetBoundingBox().GetLeft()) for p in f.Pads())
        fx, fy = xy(f.GetPosition())
        f.SetPosition(mm(fx + (2.5 + EDGE_CLEAR + 0.05) - x0, fy))
    # E2 on the USB pair's line, between E1 and J101's pads 3/5, moved right until inside profile A
    jb7 = xy(pad_of(fps["J201"], "B7").GetPosition())
    u = fps["U201"]
    ex = codes["E2"]["x"]
    centre_on(u, ex, jb7[1])
    while not box_in_profile(fp_box(u)):
        ex += 0.1
        centre_on(u, ex, jb7[1])
    dev.append(("E2 (U201)", "(%.1f; %.1f)" % (codes["E2"]["x"], codes["E2"]["y"]), "(%.1f; %.1f), em cima" % (ex, jb7[1]),
                "dentro do perfil A (SPEC 2: so E1 e F2 ficam fora), na linha do par USB do E1"))
    # A2: the speaker's two wire pads, near A1 (the speaker itself sits in the case)
    put("J501", 46.5, 84.0, 0, "T")
    dev.append(("A2 (J501)", "(31; 78), o alto-falante", "pads dos fios em (46,5; 84), em cima",
                "o alto-falante fica no case; os fios saem junto do A1, como no v2.1"))
    # ---- T4: TMAG5253 under each key, 100 nF above it (the Pocket's orientation) ----
    keys = list(csv.DictReader(open(POCKET_KEYS)))
    for k in keys:
        n = int(k["switch"][2:])
        cx, cy = float(k["x_mm"]), float(k["y_mm"])
        s = put("U7%02d" % n, cx, cy, 0, "B")
        p1 = xy(pad_of(s, "1").GetPosition())
        assert abs(p1[0] - cx - 0.25) < 0.01 and abs(p1[1] - cy + 0.775) < 0.01, ("sensor orientation", p1)
        c = put("C7%02d" % n, cx, cy - 3.0, 180, "B")
        a = xy(pad_of(c, "1").GetPosition())      # +3V3 pad, left, over the sensor's VCC pad
        c.SetPosition(mm(cx + (cx + 0.25 - a[0]), cy - 3.0))
        sw = place("%s:Gateron_Magnetic_MX_1u" % NAME, "SW%d" % n, cx, cy)
        fps["SW%d" % n] = sw
    jk = {(round(k["x"], 2), round(k["y"], 2)) for k in PLAN["keys"]}
    pk = {(round(float(k["x_mm"]), 2), round(float(k["y_mm"]), 2)) for k in keys}
    if jk != pk:
        raise SystemExit("keys of pocket_keys.csv differ from viaggio_micromod.json")

    # ---- the other passives: next to the main part of their code ----
    occupied = {"T": [], "B": []}
    for f in fps.values():
        occupied["B" if f.IsFlipped() else "T"].append(fp_box(f))
    main_of = {code: refs[0] for code, refs in main.items()}
    main_of.update({"P1": "J101", "A2": "J501"})
    rest = [r for r in sorted(comps) if r not in fps]
    for ref in rest:
        c = comps[ref]
        code = c["code"]
        anchor = fps[main_of[code]]
        side = "B" if anchor.IsFlipped() else "T"
        if code in ("A2", "I1", "I2", "I3", "E1"):
            side = "B"      # the encoders' / LED's / CC resistors on the back: the top stays for the knobs and USB
        nets_here = {pads.get((ref, k)) for k in ("1", "2", "3", "4", "5")} - {None, "GND", "+3V3"}
        tx, ty, cnt = 0.0, 0.0, 0
        for f in fps.values():
            if f.GetReference().startswith("SW") or f.GetReference().startswith("U7"):
                continue
            for p in f.Pads():
                if p.GetNetname() in nets_here:
                    px, py = xy(p.GetPosition())
                    ax, ay = xy(anchor.GetPosition())
                    if math.hypot(px - ax, py - ay) < 25:
                        tx, ty, cnt = tx + px, ty + py, cnt + 1
        if cnt:
            tx, ty = tx / cnt, ty / cnt
        else:
            tx, ty = xy(anchor.GetPosition())
        if ref in ("C101", "C102"):             # +3V3 of the socket: at pads 2 / 74
            tx, ty = xy(pad_of(fps["J101"], "2" if ref == "C102" else "74").GetPosition())
        f = put(ref, tx, ty, 0, side)
        tall = height_of(f) > CARD_MAX_H or ref.startswith("TP")    # the test pad must stay reachable
        best = None
        for r in range(0, 160):
            rr = 0.6 + r * 0.3
            nk = max(8, int(rr * 6))
            for k in range(nk):
                a = 2 * math.pi * k / nk
                for rot in (0, 90):
                    x, y = tx + rr * math.cos(a), ty + rr * math.sin(a)
                    f.SetOrientationDegrees(rot)
                    f.SetPosition(mm(x, y))
                    b = fp_box(f)
                    b = (b[0] - 0.15, b[1] - 0.15, b[2] + 0.15, b[3] + 0.15)
                    if not box_in_profile(b):
                        continue
                    if any(overlaps(b, o) for o in occupied[side]):
                        continue
                    if side == "B" and tall and overlaps(b, CARD["rect"]):
                        continue
                    if any(math.hypot(min(max(hx, b[0]), b[2]) - hx, min(max(hy, b[1]), b[3]) - hy) < M2_KEEP
                           for hx, hy in PLAN["holes_m2"]):
                        continue
                    if side == "T" and any(abs(x - float(k["x_mm"])) < 9.5 and abs(y - float(k["y_mm"])) < 9.5
                                           for k in keys):
                        continue
                    best = (x, y, rot)
                    break
                if best:
                    break
            if best:
                break
        if best is None:
            raise SystemExit("no room for %s" % ref)
        f.SetOrientationDegrees(best[2])
        f.SetPosition(mm(best[0], best[1]))
        occupied[side].append(fp_box(f))
    return fps, keys, dev


# ======================================================================= areas, zones, silkscreen
def rule_area(poly, layers, name, tracks=False, vias=False, fills=False):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(fills)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    if name:
        z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    board.Add(z)
    return z


def keep_circle(cx, cy, r, name):
    poly = [(cx + r * math.cos(2 * math.pi * k / 32), cy + r * math.sin(2 * math.pi * k / 32)) for k in range(32)]
    rule_area(poly, (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu), name, True, True, True)


def zone(layer, n, poly, prio=0, clearance=0.2, min_w=0.2, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net(n))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    z.SetLocalClearance(pcbnew.FromMM(clearance))
    z.SetMinThickness(pcbnew.FromMM(min_w))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(prio)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


LOGO = (52.0, 15.0, 40.0, 14.0)     # concept/layout.py part 7 "Area do logo" (not exported in the JSON)


def silkscreen(fps, comps):
    dashed(pcbnew.F_SilkS, PROFILE, 0.25, 0.75, 0.15, closed=True)          # profile A, dotted
    for p in CONCEPT_V1["parts"]:                                            # E1 and F2 of v1, dashed
        if p["n"] in (1, 2):
            cx, cy, w, h, a = p["cx"], p["cy"], p["w"], p["h"], math.radians(p["rot"])
            corners = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                dx, dy = sx * w / 2, sy * h / 2
                corners.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
            dashed(pcbnew.F_SilkS, corners, 1.2, 0.8, 0.12, closed=True)
            text("%s v1" % ("E1" if p["n"] == 1 else "F2"), cx, cy, 0.8, rot=-p["rot"])
    lx, ly, lw, lh = LOGO
    dashed(pcbnew.F_SilkS, rect_poly(lx - lw / 2, ly - lh / 2, lx + lw / 2, ly + lh / 2), 0.6, 0.6, 0.12, closed=True)
    text("area do logo", lx + lw / 2 - 6.5, ly + lh / 2 - 1.2, 0.8)
    # the MicroMod card, on the back silkscreen
    x0, y0, x1, y1 = CARD["rect"]
    dashed(pcbnew.B_SilkS, rect_poly(x0, y0, x1, y1), 1.0, 0.6, 0.12, closed=True)
    text("MicroMod 22x22 - pecas <= 1,9 mm", (x0 + x1) / 2, y1 - 1.5, 0.8, pcbnew.B_SilkS)
    # codes beside the parts (one label per code; T4 beside every sensor)
    done = set()
    order = sorted(fps.values(), key=lambda f: (comps.get(f.GetReference(), {}).get("code", "zz"),
                                                -len(list(f.Pads()))))
    for f in order:
        ref = f.GetReference()
        c = comps.get(ref)
        if not c or not c["code"]:
            continue
        code = c["code"]
        if code in done and code != "T4":
            continue
        if code == "T4" and not ref.startswith("U7"):
            continue
        done.add(code)
        x0, y0, x1, y1 = fp_box(f)
        back = f.IsFlipped()
        size = 0.8 if code == "T4" else 1.0
        tx, ty = (x0 + x1) / 2, y0 - 0.9
        if code == "T4":
            tx, ty = x1 + 1.0, (y0 + y1) / 2 + 1.6
        if code == "P1":
            tx, ty = x0 - 1.4, (y0 + y1) / 2
        text(code, tx, ty, size, pcbnew.B_SilkS if back else pcbnew.F_SilkS, bold=True)
    text("eTutti Viaggio MicroMod - placa principal - SPEC v2.3 passo M2", 150.0, 92.0, 1.2)
    text("eTutti Viaggio MicroMod - verso: modulo, chips, sensores TMAG5253", 150.0, 92.0, 1.2, pcbnew.B_SilkS)


# ======================================================================= schematic link
def link(comps, pads):
    netinfo = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = comps.get(ref)
        if c is None:
            fp.SetBoardOnly(True)            # Gateron switches, M2 holes: mechanical only
            continue
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetSheetname(c["props"].get("Sheetname", ""))
        fp.SetSheetfile(c["props"].get("Sheetfile", ""))
        for key in ("Codigo", "LCSC", "Montagem", "Datasheet", "Description"):
            val = c["props"].get(key, "")
            f = fp.GetField(key)
            if f is None:
                f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), key)
                f.SetVisible(False)
                f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                fp.Add(f)
            f.SetText(val)
        for p in fp.Pads():
            n = pads.get((ref, p.GetNumber()))
            if n and n.startswith("unconnected-") and p.GetNetname() == "":
                if n not in netinfo:
                    ni = pcbnew.NETINFO_ITEM(board, n)
                    board.Add(ni)
                    netinfo[n] = ni
                p.SetNet(netinfo[n])


def hole_courtyard(h, hx, hy):
    for g in [g for g in h.GraphicalItems() if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)]:
        h.Remove(g)
    c = pcbnew.PCB_SHAPE(h, pcbnew.SHAPE_T_CIRCLE)
    c.SetCenter(mm(hx, hy))
    c.SetEnd(mm(hx + HEAD_R, hy))
    c.SetLayer(pcbnew.F_CrtYd)
    c.SetWidth(pcbnew.FromMM(0.05))
    h.Add(c)


# ======================================================================= main build
def build():
    global board
    comps, pads = load_netlist()
    board = pcbnew.BOARD()
    nets.clear()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(pcbnew.FromMM(THICKNESS))
    fps, keys, dev = place_all(comps, pads)
    x0, y0, x1, y1 = PLAN["board"]["rect"]
    r = PLAN["board"]["corner_radius"]
    for a, b in (((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)), ((x1 - r, y1), (x0 + r, y1)),
                 ((x0, y1 - r), (x0, y0 + r))):
        seg(pcbnew.Edge_Cuts, a, b, 0.1)
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        p = [(cx + r * math.cos(math.radians(a0 + d)), cy + r * math.sin(math.radians(a0 + d))) for d in (0, 45, 90)]
        s.SetArcGeometry(mm(*p[0]), mm(*p[1]), mm(*p[2]))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)
    for i, (hx, hy) in enumerate(PLAN["holes_m2"], 1):
        h = place("MountingHole:MountingHole_2.2mm_M2", "H%d" % i, hx, hy)
        hole_courtyard(h, hx, hy)
        fps["H%d" % i] = h
        keep_circle(hx, hy, M2_KEEP, "M2 H%d" % i)
    silkscreen(fps, comps)
    # the MicroMod card: a named rule area for the custom rules (height under the card)
    rule_area(rect_poly(*CARD["rect"]), (pcbnew.B_Cu,), "cartao_MicroMod")
    # In1: GND whole (SPEC section 5); In2: signal, no zone in M2 (its GND / 3V3 areas come in M3)
    zone(pcbnew.In1_Cu, "GND", rect_poly(x0, y0, x1, y1), 0, name="L2 GND")
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL)
    link(comps, pads)
    os.makedirs(KDIR, exist_ok=True)
    pcbnew.SaveBoard(BOARD_PATH, board)
    return fps, comps, pads, dev


# ======================================================================= project, rules, stack-up
def write_project():
    pro = json.load(open(PRO_PATH, encoding="utf-8")) if os.path.exists(PRO_PATH) else {}
    b = pro.setdefault("board", {})
    dsj = b.setdefault("design_settings", {})
    dsj.setdefault("defaults", {})
    dsj["rules"] = {
        "max_error": 0.005, "min_clearance": CLEAR, "min_connection": 0.0, "min_copper_edge_clearance": EDGE_CLEAR,
        "min_groove_width": 0.0, "min_hole_clearance": HOLE_CLEAR, "min_hole_to_hole": 0.25,
        "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 2,
        "min_silk_clearance": 0.0, "min_text_height": 0.6, "min_text_thickness": 0.08,
        "min_through_hole_diameter": VIA_DRILL, "min_track_width": THIN, "min_via_annular_width": 0.1,
        "min_via_diameter": VIA_D, "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True}
    dsj["track_widths"] = [0.0, THIN, TRACK, USB_W, 0.3, 0.5, POWER_W, 1.0]
    dsj["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": VIA_D, "drill": VIA_DRILL}]
    dsj["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0},
                                   {"gap": USB_S, "via_gap": 0.25, "width": USB_W}]
    sev = dsj.setdefault("rule_severities", {})
    sev.update({"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore", "silk_overlap": "ignore",
                "silk_over_copper": "ignore", "silk_edge_clearance": "ignore", "text_height": "ignore",
                "text_thickness": "ignore", "footprint_symbol_mismatch": "ignore",
                "nonmirrored_text_on_back_layer": "ignore"})

    def cls(name, w, clr=CLEAR):
        return {"bus_width": 12, "clearance": clr, "diff_pair_gap": USB_S, "diff_pair_via_gap": 0.25,
                "diff_pair_width": USB_W, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": w, "via_diameter": VIA_D, "via_drill": VIA_DRILL, "wire_width": 6,
                "priority": 2147483647 if name == "Default" else len(name)}
    pro["net_settings"] = {
        "classes": [cls("Default", TRACK), cls("USB", USB_W), cls("Corrente", POWER_W, 0.2)],
        "meta": {"version": 5}, "net_colors": {}, "netclass_assignments": {},
        "netclass_patterns": [{"netclass": "USB", "pattern": "USB_D[PN]"}] +
                             [{"netclass": "Corrente", "pattern": n} for n in POWER_NETS]}
    json.dump(pro, open(PRO_PATH, "w", encoding="utf-8"), indent=2)
    outside = " && ".join("!A.intersectsCourtyard('%s')" % r for r in POWER_PADS)
    dru = """(version 1)
# eTutti Viaggio MicroMod -- custom rules (written by build_board.py, SPEC v2.3 step M2)
# Every number carries its unit; no rule names the "Default" class.
(rule "Vias 0,5 / furo 0,3 em todas as classes"
    (condition "A.Type == 'via'")
    (constraint via_diameter (min %(via_d)smm))
    (constraint hole_size (min %(via_h)smm)))
(rule "Sinais: minimo 0,15 (afinacao na entrada de pinos finos)"
    (condition "A.Type == 'track' && A.NetClass != 'USB' && A.NetClass != 'Corrente'")
    (constraint track_width (min %(thin)smm) (opt %(track)smm)))
(rule "USB 90 ohm: 0,24 / vao 0,15 em F.Cu sobre o GND do In1"
    (condition "A.NetClass == 'USB' && A.Type == 'track' && !A.intersectsCourtyard('J201') && !A.intersectsCourtyard('U201') && !A.intersectsCourtyard('J101')")
    (constraint track_width (min %(usbw_min)smm) (opt %(usbw)smm) (max %(usbw_max)smm))
    (constraint diff_pair_gap (min %(usbs_min)smm) (opt %(usbs)smm) (max %(usbs_max)smm)))
(rule "USB: so em F.Cu fora dos patios (desce junto do J101)"
    (condition "A.NetClass == 'USB' && A.Type == 'track' && A.Layer != 'F.Cu' && !A.intersectsCourtyard('J101')")
    (constraint disallow track))
(rule "Corrente: minimo 0,8 fora dos patios de E1, E3, E4, E6, A1 e J101"
    (condition "A.Type == 'track' && A.NetClass == 'Corrente' && %(outside)s")
    (constraint track_width (min %(power)smm)))
(rule "Corrente: afinacao na entrada dos pinos (patios)"
    (condition "A.Type == 'track' && A.NetClass == 'Corrente' && !(%(outside)s)")
    (constraint track_width (min %(thin)smm)))
(rule "Sob o cartao MicroMod: so pecas de ate 1,9 mm (campo Cabe_sob_cartao, de Altura_mm)"
    (condition "A.Type == 'Footprint' && A.Layer == 'B.Cu' && A.intersectsArea('cartao_MicroMod') && A.Reference != 'J101' && A.Reference != 'H101'")
    (constraint assertion "A.getField('Cabe_sob_cartao') == 'sim'"))
""" % dict(via_d=VIA_D, via_h=VIA_DRILL, thin=THIN, track=TRACK, usbw=USB_W, usbw_min=round(USB_W - 0.02, 3),
           usbw_max=round(USB_W + 0.02, 3), usbs=USB_S, usbs_min=round(USB_S - 0.01, 3),
           usbs_max=round(USB_S + 0.05, 3), power=POWER_W, outside=outside)
    open(DRU_PATH, "w", encoding="utf-8", newline="\n").write(dru)


def write_stackup():
    """pcbnew has no simple API for the physical stack-up: write it into the file."""
    s = open(BOARD_PATH, encoding="utf-8").read()
    L = IMPEDANCE["layers"]
    stack = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.015) (epsilon_r 3.8))
			(layer "F.Cu" (type "copper") (thickness %s))
			(layer "dielectric 1" (type "prepreg") (thickness %s) (material "7628") (epsilon_r %s) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness %s))
			(layer "dielectric 2" (type "core") (thickness %s) (material "FR4 NP-155F") (epsilon_r %s) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness %s))
			(layer "dielectric 3" (type "prepreg") (thickness %s) (material "7628") (epsilon_r %s) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness %s))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.015) (epsilon_r 3.8))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "HAL lead-free")
			(dielectric_constraints yes)
		)
""" % (L[0][2], L[1][2], L[1][3], L[2][2], L[3][2], L[3][3], L[4][2], L[5][2], L[5][3], L[6][2])
    s = re.sub(r"\t\t\(stackup\n.*?\n\t\t\)\n", "", s, flags=re.S)
    s = s.replace("\t(setup\n", "\t(setup\n" + stack, 1)
    open(BOARD_PATH, "w", encoding="utf-8", newline="\n").write(s)


# ======================================================================= checks, nudges, outputs
def drc(parity=True):
    cmd = [KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--output", DRC_OUT]
    if parity:
        cmd.append("--schematic-parity")
    r = subprocess.run(cmd + [BOARD_PATH], capture_output=True, text=True)
    return json.load(open(DRC_OUT, encoding="utf-8")), r.stdout + r.stderr


FIXED = {"J101", "H101", "J201", "J301", "SW401", "SW402", "SW403", "D401", "U201"}
STEP = 0.1


def area(fp):
    bb = fp.GetBoundingBox(False)
    return pcbnew.ToMM(bb.GetWidth()) * pcbnew.ToMM(bb.GetHeight())


def nudge_overlaps():
    moved = {}
    for _ in range(60):
        d, _out = drc(parity=False)
        pairs = [[i["description"].split()[-1] for i in v["items"]] for v in d.get("violations", [])
                 if v["type"] == "courtyards_overlap"]
        if not pairs:
            break
        b = pcbnew.LoadBoard(BOARD_PATH)
        for a, c in pairs:
            fa, fb = b.FindFootprintByReference(a), b.FindFootprintByReference(c)
            if c in FIXED or (a not in FIXED and area(fa) < area(fb)):
                fa, fb = fb, fa
            if fb.GetReference() in FIXED:
                continue
            pa, pb = fa.GetPosition(), fb.GetPosition()
            dx, dy = pcbnew.ToMM(pb.x - pa.x), pcbnew.ToMM(pb.y - pa.y)
            L = math.hypot(dx, dy) or 1.0
            ux, uy = round(dx / L * STEP, 3), round(dy / L * STEP, 3)
            fb.SetPosition(pcbnew.VECTOR2I(pb.x + pcbnew.FromMM(ux), pb.y + pcbnew.FromMM(uy)))
            r = fb.GetReference()
            ox, oy = moved.get(r, (0.0, 0.0))
            moved[r] = (round(ox + ux, 2), round(oy + uy, 2))
        pcbnew.SaveBoard(BOARD_PATH, b)
    return moved


def card_check(b):
    """Back-side footprints whose courtyard meets the card: heights, and the Altura_mm field for the DRC."""
    rows, bad = [], []
    for fp in b.GetFootprints():
        h = height_of(fp)
        f = fp.GetField("Altura_mm")
        if f is None:
            f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), "Altura_mm")
            f.SetVisible(False)
            f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
            fp.Add(f)
        f.SetText("%g" % h)
        g = fp.GetField("Cabe_sob_cartao")       # KiCad 10's assertion compares text, not numbers
        if g is None:
            g = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), "Cabe_sob_cartao")
            g.SetVisible(False)
            g.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
            fp.Add(g)
        g.SetText("sim" if h <= CARD_MAX_H else "nao")
        if not fp.IsFlipped() or fp.GetReference() in ("J101", "H101"):
            continue
        if overlaps(fp_box(fp), CARD["rect"]):
            rows.append((fp.GetReference(), h))
            if h > CARD_MAX_H:
                bad.append((fp.GetReference(), h))
    return sorted(rows), bad


def pictures():
    shots = []
    for side in ("top", "bottom"):
        out = os.path.join(BUILD, "%s_%s.png" % (NAME, side))
        r = subprocess.run([KICAD_CLI, "pcb", "render", "--side", side, "--width", "2400", "--height", "1000",
                            "--quality", "basic", "--zoom", "2.3", "--output", out, BOARD_PATH], capture_output=True)
        shots.append((os.path.basename(out), r.returncode))
    out = os.path.join(BUILD, NAME + "_posicionamento.svg")
    r = subprocess.run([KICAD_CLI, "pcb", "export", "svg", "--layers",
                        "Edge.Cuts,F.SilkS,B.SilkS,F.Fab,B.Fab,F.CrtYd,B.CrtYd", "--mode-single",
                        "--page-size-mode", "2", "--exclude-drawing-sheet", "--output", out, BOARD_PATH],
                       capture_output=True)
    shots.append((os.path.basename(out), r.returncode))
    return shots


def main():
    os.makedirs(BUILD, exist_ok=True)
    fps, comps, pads, dev = build()
    write_stackup()
    write_project()
    moved = nudge_overlaps()
    b = pcbnew.LoadBoard(BOARD_PATH)
    under, bad_h = card_check(b)
    if len(list(b.GetTracks())):
        raise SystemExit("tracks or vias on the board: this script must not route")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(BOARD_PATH, b)
    write_stackup()                      # SaveBoard keeps it; rewritten to be sure
    b = pcbnew.LoadBoard(BOARD_PATH)
    ok_dsn = pcbnew.ExportSpecctraDSN(b, os.path.join(BUILD, NAME + ".dsn"))
    d, out = drc(parity=True)
    vio = d.get("violations", [])
    par = d.get("schematic_parity", [])
    kinds = {}
    for v in vio + par:
        k = "%s/%s" % (v["severity"], v["type"])
        kinds[k] = kinds.get(k, 0) + 1
    code = {r: c["code"] for r, c in comps.items()}
    per = {}
    for u in d.get("unconnected_items", []):
        sec = sorted({(code.get(i["description"].split(" of ")[-1].split()[0], "") or "?")[:1]
                      for i in u.get("items", [])})
        per["-".join(sec)] = per.get("-".join(sec), 0) + 1
    rule_errors = [l for l in out.splitlines() if "rule" in l.lower() and ("error" in l.lower() or "erro" in l.lower())]
    errors = [v for v in vio + par if v["severity"] == "error"]
    summary = {"spec": "v2.3 passo M2", "tracks": 0, "vias": 0,
               "drc_errors": len(errors), "drc_warnings": len([v for v in vio + par if v["severity"] == "warning"]),
               "violations": kinds, "schematic_parity": len(par),
               "unrouted": len(d.get("unconnected_items", [])), "unrouted_by_sector": dict(sorted(per.items())),
               "dsn": bool(ok_dsn), "rules_file_messages": rule_errors,
               "card_rect": [round(v, 2) for v in CARD["rect"]], "standoff": CARD["standoff"],
               "under_card": under, "too_tall_under_card": bad_h,
               "moved_mm": moved, "deviations": dev,
               "positions": {r: [round(pcbnew.ToMM(f.GetPosition().x), 2), round(pcbnew.ToMM(f.GetPosition().y), 2),
                                 round(f.GetOrientationDegrees(), 1), "B" if f.IsFlipped() else "T"]
                             for r, f in sorted((f.GetReference(), f) for f in b.GetFootprints())}}
    outside_a = []                       # SPEC section 2: everything inside profile A but E1 and F2
    for f in b.GetFootprints():
        r = f.GetReference()
        if comps.get(r, {}).get("code") in ("E1", "F2") or r.startswith("SW") and r[2:].isdigit() or r.startswith("H"):
            continue
        if not box_in_profile(fp_box(f)):
            outside_a.append(r)
    summary["outside_profile_a"] = sorted(outside_a)
    summary["pictures"] = pictures()
    json.dump(summary, open(os.path.join(BUILD, NAME + "_handoff.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    for k in ("drc_errors", "drc_warnings", "violations", "schematic_parity", "unrouted", "unrouted_by_sector",
              "dsn", "rules_file_messages", "outside_profile_a", "card_rect", "standoff", "under_card", "too_tall_under_card", "moved_mm",
              "pictures"):
        print("%s: %s" % (k, summary[k]))
    for v in errors[:20]:
        print("  [error] %s %s" % (v["type"], v["description"]), [i["description"] for i in v.get("items", [])][:2])
    sys.exit(1 if errors or bad_h or rule_errors or not ok_dsn else 0)


if __name__ == "__main__":
    main()
