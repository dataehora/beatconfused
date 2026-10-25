"""Build the eTutti Viaggio main board (SPEC v2.1, step 3.2): placement + sector P.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio/pcb/build_board.py

Run schematic.py first (it writes build/viaggio_netlist.net, the footprints
and the project), and impedance.py once (build/impedance.json, the USB pair's
width and gap). This script:

  1. reads the netlist (kicad-cli has no "update PCB from schematic"): every
     component with its Footprint field and its "Codigo" (SPEC section 3),
     every pad's net;
  2. builds the 4-layer 1.2 mm board (JLCPCB JLC04121H-7628 stack-up):
     rectangle x 2.5-249, y 2.5-97.5, R 5 corners, M2 holes with a 3.5 mm
     copper-free ring, silkscreen (profile A dotted, the v1 places of E1 and
     F2 dashed, the logo area, the codes P1 ... T4 beside the parts),
     net classes and rules (kicad_pro + kicad_dru);
  3. places every part from concept/rev2/out/viaggio_rev2.json (parts, keys,
     holes): the main part of each code at its spot, its passives next to it
     (P1's decoupling capacitors on the top side, over the BGA), the 28
     TMAG5253 under the keys as on the Pocket, the 28 Gateron footprints;
  4. routes sector P only, in the order of SPEC section 4: clocks, the BGA's
     power fan-out and capacitors, the USB pair (C1), the memories, P1's
     internal DC-DC, MCLK's resistor, the rest of sector P, and last an
     escape of every signal that leaves the sector to the BGA's edge;
  5. fills the zones (In1 GND whole; In2 GND with the 3.3 V and VDD_SOC
     islands), runs KiCad's DRC, counts the unrouted connections per sector
     and exports the review pictures to build/.

Exits non-zero on a DRC violation or on an unrouted connection inside
sector P (connections from P to the other sectors are the next steps').
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

import numpy as np  # noqa: E402
import pcbnew  # noqa: E402

import router as RT  # noqa: E402
import sexpr as S  # noqa: E402

KICAD_BIN = os.path.dirname(sys.executable)
KICAD_CLI = os.path.join(KICAD_BIN, "kicad-cli.exe" if os.name == "nt" else "kicad-cli")
FP_ROOT = os.path.normpath(os.path.join(KICAD_BIN, "..", "share", "kicad", "footprints"))
KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
LOCAL_PRETTY = os.path.join(KDIR, "viaggio.pretty")
BOARD_PATH = os.path.join(KDIR, "viaggio.kicad_pcb")
PRO_PATH = os.path.join(KDIR, "viaggio.kicad_pro")
DRU_PATH = os.path.join(KDIR, "viaggio.kicad_dru")
NETLIST = os.path.join(BUILD, "viaggio_netlist.net")
VIAGGIO = os.path.normpath(os.path.join(HERE, ".."))
REV2 = json.load(open(os.path.join(VIAGGIO, "concept", "rev2", "out", "viaggio_rev2.json"), encoding="utf-8"))
CONCEPT_V1 = json.load(open(os.path.join(VIAGGIO, "concept", "out", "viaggio_concept.json"), encoding="utf-8"))
POCKET_KEYS = os.path.normpath(os.path.join(HERE, "..", "..", "pocket", "pcb", "build", "pocket_keys.csv"))
IMPEDANCE = json.load(open(os.path.join(BUILD, "impedance.json")))

# ------------------------------------------------------------------ rules (mm)
THICKNESS = 1.2
CLEAR = 0.1                 # copper to copper (JLCPCB 4-layer minimum: 0.09)
TRACK = 0.2                 # signals (SPEC section 4)
THIN = 0.1                  # inside the BGA only (0.8 mm pitch: one track between two balls)
POWER_W = 0.8               # current class (SPEC section 4, 6th)
CORE_W = 0.4                # P1's internal DC-DC (DCDC_IN, DCDC_LP, VDD_SOC) outside the BGA
VIA_D, VIA_DRILL = 0.45, 0.2   # JLCPCB: 0.2 mm holes cost nothing extra from a 0.45 mm diameter up
VIA_CLEAR = 0.12            # extra margin when the router drops a via (hole to hole >= 0.29)
HOLE_CLEAR = 0.2
EDGE_CLEAR = 0.3
USB_W = IMPEDANCE["usb"]["w"]
USB_S = IMPEDANCE["usb"]["s"]
M2_KEEP = 3.5               # copper-free radius round each M2 hole (SPEC section 2)

BGA_CX, BGA_CY, BGA_ROT = 34.0, 15.5, 270      # P1 on the back: row P to the left, column 1 at the front
BGA_HALF = 6.0
THIN_HALF = 6.25

POWER_NETS = {"VBUS", "VSYS", "VBAT", "BB_L1", "BB_L2"}
CORE_NETS = {"DCDC_IN", "DCDC_LP", "VDD_SOC"}
PLANE_NETS = {"GND", "+3V3", "VDD_SOC"}
DOGBONE_SIGNALS = {"POR_B", "PMIC_ON_REQ"}    # deep signal balls next to the USB vias: a via of their own early
CAP_NETS = {"NVCC_PLL", "VDD_HIGH_CAP", "VDD_SNVS_CAP", "VDD_SNVS_IN", "VDD_USB_CAP"}   # one ball + its capacitors

# hand placement of sector P (and its neighbours the USB pair runs past):
# ref -> (x, y, rot, side). Main parts of other codes come from viaggio_rev2.json.
PLACE_P = {
    "U101": (BGA_CX, BGA_CY, BGA_ROT, "B"),
    "U102": (37.05, 5.95, 0, "B"),         # P2 MKL02, over the bootloader balls (rev2: 46, 9)
    "C124": (40.4, 4.9, 90, "B"),         # P2's pins 1-4 (3V3, GND, PSWITCH, BOOT0) face +x on the back
    "R104": (40.4, 7.9, 90, "B"),
    "D103": (33.4, 4.3, 0, "B"),          # pins 9-12 (POR_B, PROG, LED, B0_13) face -x
    "R103": (33.4, 6.6, 0, "B"),
    "R101": (41.8, 15.9, 90, "B"),        # PMIC_ON_REQ pull-down, on the way to E5 (right)
    "U103": (23.0, 20.6, 0, "B"),        # P3 flash, left of the flash balls (rev2: 47.5, 18)
    "U104": (37.65, 24.0, 90, "B"),        # P4 PSRAM, under the PSRAM balls (rev2: 47.5, 26.5)
    "Y101": (25.7, 10.5, 0, "B"),         # P5 24 MHz, beside XTALI/XTALO (rev2: 26, 23)
    "Y102": (25.6, 13.55, 0, "B"),        # P5 32.768 kHz, beside RTC_XTALI/O
    "C120": (23.3, 9.6, 90, "B"),         # XTALO load
    "C121": (25.85, 8.0, 0, "B"),          # XTALI load
    "R102": (27.85, 8.0, 180, "B"),         # XTALI 2.2M (PJRC R5)
    "C123": (23.0, 13.55, 90, "B"),       # RTC_XTALI load
    "C122": (25.2, 15.7, 0, "B"),         # RTC_XTALO load
    "L102": (29.2, 23.7, 90, "B"),        # DC-DC of P1: inductor under DCDC_LP
    "C101": (31.4, 23.5, 90, "B"),
    "C102": (32.9, 23.5, 90, "B"),
    "C103": (32.5, 25.7, 0, "B"),
    "L101": (34.5, 23.5, 90, "B"),
    "C104": (26.6, 25.7, 0, "B"),
    "C105": (29.95, 26.5, 0, "B"),
    "U201": (15.6, 13.0, 180, "B"),       # E2 under the USB pair (rev2: 14, 13)
    "D201": (15.6, 16.6, 90, "B"),        # E2's TVS, out of the pair's way
    "R201": (11.6, 9.4, 0, "B"),          # E1's CC resistors on the back (the pair leaves on the top)
    "R202": (11.6, 16.6, 0, "B"),
}
# P1's capacitors on the top side, over the BGA: ref -> the ball they serve (None = the only
# ball of their net). Placed after the BGA's power fan-out, on the free spot nearest that ball.
TOP_CAPS = {
    "C106": "G6", "C107": "H9",                                   # VDD_SOC
    "C108": "E6", "C109": "J10", "C110": "F10", "C111": "K5",     # +3V3 (NVCC, VDD_HIGH_IN, ...)
    "C112": (27.3, 16.95, 0), "C113": (27.3, 17.9, 0),            # VDD_HIGH_CAP: fixed, beside P8's via
    "C114": None, "C115": None,                                   # NVCC_PLL
    "C116": None, "C117": None, "C118": None, "C119": None,       # SNVS, USB_CAP
}
PARK = (57.0, 33.0)          # top capacitors wait here (off the router's grid) until placed

# sites (interstitials) kept free for the USB pair on the top layer
USB_SITES = [(28.4, 14.7), (28.4, 15.5), (29.2, 14.7), (29.2, 15.5), (30.0, 15.5)]
USB_VIA = {"USB_DN": (30.0, 14.7), "USB_DP": (30.8, 15.5)}


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
        comps[ref] = dict(ref=ref, value=S.first(c, "value")[1], fp=S.first(c, "footprint")[1],
                          code=props.get("Codigo", ""), lcsc=props.get("LCSC", ""), mount=props.get("Montagem", ""))
    pads = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        if name.startswith("unconnected-"):
            continue
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
    path = LOCAL_PRETTY if lib == "viaggio" else os.path.join(FP_ROOT, lib + ".pretty")
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


# ======================================================================= router glue
G = None                    # RT.Grid
ROUTE_LOG = []              # (step, label, length mm, vias)
TRACK_LEN = {}              # net -> routed length


def thin_fn(X, Y):
    return (np.abs(X - BGA_CX) <= THIN_HALF) & (np.abs(Y - BGA_CY) <= THIN_HALF)


def in_thin(x, y):
    return abs(x - BGA_CX) <= THIN_HALF and abs(y - BGA_CY) <= THIN_HALF


def net_width(n):
    if n in POWER_NETS:
        return POWER_W
    if n in CORE_NETS:
        return CORE_W
    return TRACK


def net_thin(n):
    return 0.2 if n in CORE_NETS else THIN


LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


def add_track(pts, li, n, w, register=True):
    for a, b in zip(pts, pts[1:]):
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(mm(*a))
        t.SetEnd(mm(*b))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(LAYERS[li])
        t.SetNet(net(n))
        board.Add(t)
        TRACK_LEN[n] = TRACK_LEN.get(n, 0.0) + math.hypot(a[0] - b[0], a[1] - b[1])
        if register:
            G.mark_segment((li,), a, b, w / 2, n)


VIAS = []
HOLE_KEEP = 0.56            # centre to centre of two vias: 0.2 hole spacing + 2 x radius ... kept generous


def add_via(x, y, n, item=None):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(mm(x, y))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetNet(net(n))
    board.Add(v)
    VIAS.append((x, y, n))
    G.mark_segment((0, 1), (x, y), (x, y), VIA_D / 2, n, item=item)
    sl = G._win(x, y, x, y, HOLE_KEEP)
    sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
    G.novia[sl][np.hypot(G.X[sl] - x, G.Y[sl] - y) < HOLE_KEEP] = True
    iy, ix = G.cell(x, y)
    G.viacell[iy, ix] = G.nid(n)
    return v


def register_fp(fp):
    ref = fp.GetReference()
    for p in fp.Pads():
        n = p.GetNetname() or None
        bb = p.GetBoundingBox()
        x0, y0, x1, y1 = (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()),
                          pcbnew.ToMM(bb.GetBottom()))
        cx, cy = xy(p.GetPosition())
        if x1 < G.ox - 1 or y1 < G.oy - 1 or x0 > G.x(G.W - 1) + 1 or y0 > G.y(G.H - 1) + 1:
            continue
        attr = p.GetAttribute()
        if attr == pcbnew.PAD_ATTRIB_NPTH:
            G.mark_hole(cx, cy, pcbnew.ToMM(p.GetDrillSize().x) / 2 + HOLE_CLEAR)
            continue
        layers = [i for i, l in enumerate(LAYERS) if p.IsOnLayer(l)]
        circle = p.GetShape(pcbnew.PADSTACK.ALL_LAYERS) == pcbnew.PAD_SHAPE_CIRCLE
        item = (ref, p.GetNumber())
        if item in G.items:
            item = (ref, p.GetNumber() + "#%d" % len([k for k in G.items if k[0] == ref]))
        G.mark_pad(layers, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, n, item=item if n else None,
                   circle=circle, smd=(attr == pcbnew.PAD_ATTRIB_SMD), center=(round(cx, 4), round(cy, 4)))
        if attr == pcbnew.PAD_ATTRIB_PTH:
            G.mark_hole(cx, cy, pcbnew.ToMM(p.GetDrillSize().x) / 2 + HOLE_CLEAR - 0.1)


class RoutingFailed(Exception):
    pass


def path_to_copper(n, path, w, thin_w, via_ok_last=False):
    pts = [(G.x(ix), G.y(iy), l) for l, iy, ix in path]
    start = G.attach.get(path[0])
    end = G.attach.get(path[-1])
    runs = []
    nv = 0
    for x, y, l in pts:
        if runs and runs[-1][0] == l:
            runs[-1][1].append((x, y))
        else:
            if runs:
                iy, ix = G.cell(x, y)
                if int(G.viacell[iy, ix]) != G.nid(n):      # not through one of its own vias
                    add_via(x, y, n)
                    nv += 1
            runs.append((l, [(x, y)]))
    if start:
        runs[0][1].insert(0, start)
    if end:
        runs[-1][1].append(end)
    total = 0.0
    for l, run in runs:
        # drop collinear points, then give each piece its width (thin inside the BGA)
        simple = [run[0]]
        for i in range(1, len(run) - 1):
            ax, ay = simple[-1]
            bx, by = run[i]
            cx, cy = run[i + 1]
            if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                simple.append(run[i])
        simple.append(run[-1])
        for a, b in zip(simple, simple[1:]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            # a long piece that crosses the BGA's edge: split it there
            ww = thin_w if (in_thin(*a) or in_thin(*b) or in_thin(*mid)) else w
            add_track([a, b], l, n, ww)
            total += math.hypot(a[0] - b[0], a[1] - b[1])
    return total, nv


ROUTED = set()              # nets of sector P already joined
# The greedy router can wall a net in: on a failure main() starts again with that net first
# in its step (VIAGGIO_ROUTE_FIRST); DEFAULT_ROUTE_FIRST is the order the retries found last.
DEFAULT_ROUTE_FIRST = "FLASH_CLK,FLASH_D3,FLASH_D2,FLASH_D0,PSRAM_D2,BL_LED_N,BL_TMS,BL_TCK,BL_BOOT0,BL_B013,BL_MOD,PSWITCH,BL_TDI"
ROUTE_FIRST = [n for n in os.environ.get("VIAGGIO_ROUTE_FIRST", DEFAULT_ROUTE_FIRST).split(",") if n]
TREE = {}                   # net -> set of grid cells of copper connected so far (routed nets)


def copper_cells(n):
    nid = G.nid(n)
    out = set()
    for li in (0, 1):
        ys, xs = np.nonzero(G.copper[li] == nid)
        out |= {(li, int(a), int(b)) for a, b in zip(ys.tolist(), xs.tolist())}
    return out


def route(step, label, n, src, targets, w=None, thin_w=None, layers_ok=(0, 1), allow_via=True, window=None,
          via_cost=2.0, extra_ok=(), must=True):
    w = net_width(n) if w is None else w
    thin_w = net_thin(n) if thin_w is None else thin_w
    path = G.search(n, src, targets, w / 2, thin_w / 2, thin_fn, window=window, allow_via=allow_via,
                    layers_ok=layers_ok, via_cost=via_cost, extra_ok=extra_ok)
    if path is None:
        print("ROUTING FAILED: %s %s (%s)" % (step, label, n))
        if must:
            raise RoutingFailed(n)
        return None
    L, nv = path_to_copper(n, path, w, thin_w)
    ROUTE_LOG.append((step, label, n, round(L, 2), nv))
    return path


def item_cells(ref, num):
    out = set()
    for k, v in G.items.items():
        if k[0] == ref and (k[1] == num or k[1].startswith(num + "#")):
            out |= v
    return out


# ======================================================================= placement
def flip_side(side):
    return side == "B"


def place_all(comps, pads):
    """Returns {ref: footprint}."""
    fps = {}
    codes = {p["code"]: p for p in REV2["parts"]}
    by_code = {}
    for ref, c in comps.items():
        by_code.setdefault(c["code"], []).append(ref)

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

    # ---- main part of every code at its rev2 spot ----
    main = {"E1": ["J201"], "E2": [], "E3": ["U202"], "E4": ["U204", "L201"], "E5": ["U205", "U206"],
            "E6": ["J202"], "F1": ["U301"], "F2": ["J301"], "I1": ["SW401"], "I2": ["SW402"], "I3": ["D401"],
            "I4": ["SW403"], "A1": ["U501"], "A2": [], "T1": ["U601"], "T2": ["U602"],
            "T3": ["U603", "U604", "U605"]}
    for code, refs in main.items():
        spec = codes[code]
        side = "B" if spec["side"] == "bot" else "T"
        n = len(refs)
        for i, ref in enumerate(refs):
            if ref in PLACE_P:
                continue
            rot = 0
            if ref == "J201":
                rot = 270           # mouth to -x (left edge)
            elif ref == "J301":
                rot = 90            # mouth to -x
            elif code in ("T1", "T2"):
                rot = 90            # long side along x (rev2 box 7.8 x 4.4)
            elif code in ("I1", "I2"):
                rot = 90            # pins in rows along x: the two encoders, 16 mm apart, keep 1.5 mm of air
            f = put(ref, spec["x"], spec["y"], rot, side)
            centre_on(f, spec["x"], spec["y"])
        if n > 1:                   # side by side, 0.4 mm apart, the group centred on the rev2 spot
            boxes = [fp_box(fps[r]) for r in refs]
            total = sum(b[2] - b[0] for b in boxes) + 0.4 * (n - 1)
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
        f.SetPosition(mm(fx + (2.5 + EDGE_CLEAR + 0.05) - x0, fy))   # copper EDGE_CLEAR inside the edge
    for ref, (x, y, rot, side) in PLACE_P.items():
        if ref == "U201":
            j = fps["J201"]
            b7 = xy(pad_of(j, "B7").GetPosition())
            a6 = xy(pad_of(j, "A6").GetPosition())
            y = b7[1] + math.copysign((USB_W + USB_S) / 2, a6[1] - b7[1])
        put(ref, x, y, rot, side)
    for ref in TOP_CAPS:
        put(ref, PARK[0], PARK[1], 0, "T")
    # A2: the speaker's two wire pads, near A1 (the speaker itself sits in the case)
    put("J501", 46.5, 84.0, 0, "T")
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
        sw = place(os.path.join("viaggio:Gateron_Magnetic_MX_1u"), "SW%d" % n, cx, cy)
        fps["SW%d" % n] = sw
    # ---- the other passives: next to the main part of their code ----
    occupied = {"T": [], "B": []}
    for f in fps.values():
        occupied["B" if f.IsFlipped() else "T"].append(fp_box(f))
    main_of = {}
    for code, refs in main.items():
        if refs:
            main_of[code] = refs[0]
    main_of.update({"P1": "U101", "P2": "U102", "P3": "U103", "P4": "U104", "P5": "Y101", "E2": "U201",
                    "A2": "J501"})
    rest = [r for r in sorted(comps) if r not in fps]
    for ref in rest:
        c = comps[ref]
        code = c["code"]
        anchor = fps[main_of[code]]
        side = "B" if anchor.IsFlipped() else "T"
        if code == "A2" or code == "I3" or code in ("I1", "I2"):
            side = "B"
        # target: the anchor's pads that share a net with this part (not the planes), else its centre
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
        f = put(ref, tx, ty, 0, side)
        best = None
        for r in range(0, 120):
            rr = 0.6 + r * 0.3
            for k in range(max(8, int(rr * 6))):
                a = 2 * math.pi * k / max(8, int(rr * 6))
                for rot in (0, 90):
                    x, y = tx + rr * math.cos(a), ty + rr * math.sin(a)
                    f.SetOrientationDegrees(rot)
                    f.SetPosition(mm(x, y))
                    b = fp_box(f)
                    b = (b[0] - 0.15, b[1] - 0.15, b[2] + 0.15, b[3] + 0.15)
                    if not (3.2 < b[0] and b[2] < 248.3 and 3.2 < b[1] and b[3] < 96.8):
                        continue
                    if any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in occupied[side]):
                        continue
                    if any(math.hypot(min(max(hx, b[0]), b[2]) - hx, min(max(hy, b[1]), b[3]) - hy) < M2_KEEP
                           for hx, hy in REV2["holes_m2"]):
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
        f.SetOrientationDegrees(best[2])
        f.SetPosition(mm(best[0], best[1]))
        occupied[side].append(fp_box(f))
    # 2-pad parts of sector P: turn them so each pad faces its net
    return fps, keys


# ======================================================================= main build
def build():
    global board, G
    comps, pads = load_netlist()
    board = pcbnew.BOARD()
    nets.clear()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(pcbnew.FromMM(THICKNESS))
    fps, keys = place_all(comps, pads)
    # ---------------- outline: rectangle with R 5 corners
    x0, y0, x1, y1 = REV2["board"]["rect"]
    r = REV2["board"]["corner_radius"]
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
    # ---------------- M2 holes with a copper-free ring
    for i, (hx, hy) in enumerate(REV2["holes_m2"], 1):
        h = place("MountingHole:MountingHole_2.2mm_M2", "H%d" % i, hx, hy)
        for g in list(h.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                h.Remove(g)
        fps["H%d" % i] = h
        keep_circle(hx, hy, M2_KEEP)
    silkscreen(fps, comps)
    # ---------------- router grid over sector P and the USB's way in
    G = RT.Grid(0.0, 0.0, 60.0, 36.0, 0.1, CLEAR, VIA_D, VIA_CLEAR,
                classes=(THIN / 2, TRACK / 2, USB_W / 2, CORE_W / 2, USB_W + USB_S / 2 + 0.005, POWER_W / 2))
    # board edge + margin
    m = (G.X < x0 + EDGE_CLEAR + 0.05) | (G.X > x1 - EDGE_CLEAR - 0.05) | (G.Y < y0 + EDGE_CLEAR + 0.05) | \
        (G.Y > y1 - EDGE_CLEAR - 0.05)
    for arr in [G.owner] + list(G.cls.values()):
        arr[0][m] = RT.HARD
        arr[1][m] = RT.HARD
    G.novia[m] = True
    for f in fps.values():
        if f.GetReference() not in TOP_CAPS:
            register_fp(f)
    for hx, hy in REV2["holes_m2"]:
        if hx < 62 and hy < 38:
            G.mark_hole(hx, hy, M2_KEEP)
    route_sector_p(fps, comps, pads)
    zones(fps)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    os.makedirs(KDIR, exist_ok=True)
    pcbnew.SaveBoard(BOARD_PATH, board)
    return fps, comps, pads


def keep_circle(cx, cy, r):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(32):
        a = 2 * math.pi * k / 32
        ol.Append(pcbnew.FromMM(cx + r * math.cos(a)), pcbnew.FromMM(cy + r * math.sin(a)))
    board.Add(z)


def keepout_rect(poly, layers, name=""):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(False)
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


def silkscreen(fps, comps):
    # profile A, dotted
    prof = [tuple(p) for p in REV2["profile_a"]]
    dashed(pcbnew.F_SilkS, prof, 0.25, 0.75, 0.15, closed=True)
    # E1 and F2 of v1, dashed (rotated rectangles)
    for p in CONCEPT_V1["parts"]:
        if p["n"] in (1, 2):
            cx, cy, w, h, a = p["cx"], p["cy"], p["w"], p["h"], math.radians(p["rot"])
            corners = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                dx, dy = sx * w / 2, sy * h / 2
                corners.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
            dashed(pcbnew.F_SilkS, corners, 1.2, 0.8, 0.12, closed=True)
            text("%s v1" % ("E1" if p["n"] == 1 else "F2"), cx, cy, 0.8, rot=-p["rot"])
    # logo area
    logo = [p for p in REV2["parts"] if p.get("code", "").lower() == "logo" or "logo" in p.get("name", "").lower()]
    lx, ly, lw, lh = (52.0, 15.0, 40.0, 14.0)
    if logo:
        lx, ly, lw, lh = logo[0]["x"], logo[0]["y"], logo[0]["w"], logo[0]["h"]
    dashed(pcbnew.F_SilkS, rect_poly(lx - lw / 2, ly - lh / 2, lx + lw / 2, ly + lh / 2), 0.6, 0.6, 0.12, closed=True)
    text("area do logo", lx + lw / 2 - 6.5, ly + lh / 2 - 1.2, 0.8)
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
        text(code, tx, ty, size, pcbnew.B_SilkS if back else pcbnew.F_SilkS, bold=True)
    text("eTutti Viaggio - placa principal - SPEC v2.1 passo 3.2", 150.0, 92.0, 1.2)
    text("eTutti Viaggio - verso: chips, sensores TMAG5253", 150.0, 92.0, 1.2, pcbnew.B_SilkS)


# ======================================================================= sector P routing
BALL = {}                    # ball name -> (x, y)
P1_NET = {}


def interstitials():
    s = set()
    for i in range(13):
        for j in range(13):
            s.add((round(BGA_CX - 4.8 + 0.8 * i, 1), round(BGA_CY - 4.8 + 0.8 * j, 1)))
    return s


VDD_RECT = (32.6, 13.5, 35.4, 17.5)          # VDD_SOC island core (In2), see zones()


def in_rect(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def plus3_ok(p):
    return point_in_poly(p, P3V3_ISLAND) and not in_vdd(p)


def in_vdd(p):
    return point_in_poly(p, VDD_ISLAND)


VDD_ISLAND = [(32.6, 13.5), (35.4, 13.5), (35.4, 17.5), (34.0, 17.5), (34.0, 27.2), (26.6, 27.2), (26.6, 22.8),
              (32.6, 22.8)]
P3V3_ISLAND = [(27.9, 9.3), (33.0, 9.3), (33.0, 3.6), (41.2, 3.6), (41.2, 27.2), (39.7, 27.2), (39.7, 21.7),
               (36.0, 21.7), (36.0, 25.0), (34.0, 25.0), (34.0, 21.7), (27.9, 21.7)]


DOGBONE_CELLS = {}


def dogbones(fps):
    """Power balls (GND, 3.3 V, VDD_SOC): one via each on a free interstitial
    (bipartite matching), joined to the ball by a 0.2 mm track on the back.
    Signal balls are left to the router."""
    u = fps["U101"]
    for p in u.Pads():
        BALL[p.GetNumber()] = xy(p.GetPosition())
        P1_NET[p.GetNumber()] = p.GetNetname()
    sites = interstitials() - {tuple(s) for s in USB_SITES} - set(USB_VIA.values())
    want = {}
    for b, n in P1_NET.items():
        if n not in ("GND", "+3V3", "VDD_SOC") and n not in CAP_NETS and n not in DOGBONE_SIGNALS:
            continue
        bx, by = BALL[b]
        cands = []
        for dx in (-0.4, 0.4):
            for dy in (-0.4, 0.4):
                s = (round(bx + dx, 1), round(by + dy, 1))
                if s not in sites:
                    continue
                if n == "VDD_SOC" and not in_rect(s, VDD_RECT):
                    continue
                if n == "+3V3" and not plus3_ok(s):
                    continue
                if not via_free(s[0], s[1], n):
                    continue
                cands.append(s)
        # prefer pointing towards the BGA's centre: the channels near the edge stay free for signals
        cands.sort(key=lambda s: math.hypot(s[0] - BGA_CX, s[1] - BGA_CY))
        want[b] = cands
    match = {}                  # site -> ball

    def augment(b, seen, gnd_only):
        for s in want[b]:
            if s in seen:
                continue
            seen.add(s)
            if s not in match or ((not gnd_only or P1_NET[match[s]] == "GND") and augment(match[s], seen, gnd_only)):
                match[s] = b
                return True
        return False
    # the supplies and signals first; GND balls take the sites left (a GND ball without one is joined
    # on the back to a neighbour's GND)
    order = sorted(want, key=lambda b: (P1_NET[b] == "GND", len(want[b])))
    unplaced = []
    for b in order:
        if not augment(b, set(), P1_NET[b] == "GND"):
            if P1_NET[b] not in CAP_NETS | DOGBONE_SIGNALS:
                unplaced.append(b)
            else:
                print("no via site for", b, P1_NET[b])
    for s, b in match.items():
        n = P1_NET[b]
        add_track([BALL[b], s], 1, n, 0.2)
        add_via(s[0], s[1], n)
        iy, ix = G.cell(*s)
        DOGBONE_CELLS.setdefault(n, set()).update({(0, iy, ix), (1, iy, ix)})
    return unplaced


def via_free(vx, vy, n):
    nid = G.nid(n)
    iy, ix = G.cell(vx, vy)
    if not (0 <= iy < G.H and 0 <= ix < G.W) or G.novia[iy, ix]:
        return False
    for li in (0, 1):
        o = int(G.cls["via"][li][iy, ix])
        if o not in (RT.FREE, nid):
            return False
        r = int(G.res[li][iy, ix])
        if r not in (RT.FREE, nid):
            return False
    return True


def line_free(a, b, li, n, hw):
    """A straight track a-b of half-width hw on layer li keeps its clearances."""
    nid = G.nid(n)
    k = G.cls[G._klass(hw)][li]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    steps = max(1, int(L / 0.05))
    for i in range(steps + 1):
        x = a[0] + (b[0] - a[0]) * i / steps
        y = a[1] + (b[1] - a[1]) * i / steps
        iy, ix = G.cell(x, y)
        if int(k[iy, ix]) not in (RT.FREE, nid):
            # inside its own pad the cell may be marked by a neighbour's halo only if really close
            return False
    return True


class Checkpoint:
    """Undo point for trial placements: the grid, the logs and the copper added to the board."""
    def __init__(self):
        self.owner, self.copper, self.novia = G.owner.copy(), G.copper.copy(), G.novia.copy()
        self.cls = {k: v.copy() for k, v in G.cls.items()}
        self.viacell = G.viacell.copy()
        self.attach = dict(G.attach)
        self.items = {k: set(v) for k, v in G.items.items()}
        self.n_ids = (dict(G.net_ids), list(G.net_names))
        self.logs = (len(ROUTE_LOG), len(VIAS), dict(TRACK_LEN), set(ROUTED), {k: set(v) for k, v in TREE.items()})
        self.board_items = {t.m_Uuid.AsString() for t in board.GetTracks()}

    def restore(self):
        G.owner[...] = self.owner
        for k, v in self.cls.items():
            G.cls[k][...] = v
        G.viacell[...] = self.viacell
        G.copper[...] = self.copper
        G.novia[...] = self.novia
        G.attach = self.attach
        G.items = self.items
        G.net_ids, G.net_names = self.n_ids
        del ROUTE_LOG[self.logs[0]:]
        del VIAS[self.logs[1]:]
        TRACK_LEN.clear()
        TRACK_LEN.update(self.logs[2])
        ROUTED.clear()
        ROUTED.update(self.logs[3])
        TREE.clear()
        TREE.update(self.logs[4])
        for t in list(board.GetTracks()):
            if t.m_Uuid.AsString() not in self.board_items:
                board.Remove(t)


def connect_cap(f):
    for p in f.Pads():
        n = p.GetNetname()
        ok = False
        if n == "GND":
            ok = stitch(f, p.GetNumber(), n)
        elif n == "+3V3":
            ok = stitch(f, p.GetNumber(), n, need=plus3_ok)
        elif n == "VDD_SOC":
            ok = stitch(f, p.GetNumber(), n, need=in_vdd)
        if not ok:
            src = item_cells(f.GetReference(), p.GetNumber())
            if n == "GND":
                tgt = via_cells("GND")
            elif n in CAP_NETS:
                # the ball, its via and what is already joined to them -- not some other pad of the net
                tgt = set(TREE.get(n, set()))
                for b in [b for b, nn in P1_NET.items() if nn == n]:
                    tgt |= item_cells("U101", b)
                tgt |= via_cells(n)
                TREE.setdefault(n, set()).update(tgt)
            else:
                tgt = copper_cells(n) - src
            path = route("2 BGA", "%s.%s -> %s" % (f.GetReference(), p.GetNumber(), n), n, src, tgt, must=False)
            if not path:
                CAP_FAIL[(f.GetReference(), p.GetNumber(), n, len(tgt))] = CAP_FAIL.get((f.GetReference(), p.GetNumber(), n, len(tgt)), 0) + 1
                return False
            if ROUTE_LOG[-1][3] > CAP_ROUTE_MAX:          # a capacitor is only useful close by
                CAP_FAIL[(f.GetReference(), p.GetNumber(), n, "long")] = CAP_FAIL.get((f.GetReference(), p.GetNumber(), n, "long"), 0) + 1
                return False
            TREE.setdefault(n, set()).update(path)
            TREE[n] |= src
        ROUTED.add(n)
    return True


CAP_FAIL = {}
CAP_ROUTE_MAX = 4.5


def via_cells(n):
    out = set()
    for x, y, nn in VIAS:
        if nn == n:
            iy, ix = G.cell(x, y)
            out |= {(0, iy, ix), (1, iy, ix)}
    return out


PLACED_TOP = []


def place_top_caps(fps, which=None):
    """Each P1 capacitor on the top, over the BGA, on the free spot nearest its ball whose
    pads can be joined right away (tried in turn, undone when a join fails)."""
    placed = PLACED_TOP
    lanes = [(27.2, 14.2, 30.6, 16.0), (30.3, 14.9, 31.4, 16.0), (28.45, 16.5, 32.2, 20.8), (24.0, 17.3, 28.6, 23.0)]  # USB, flash balls and pins
    # one capacitor of every supply first, then the second ones (the big ones last)
    seen_net = {}
    rank = {}
    for r in sorted(TOP_CAPS):
        nn = [p.GetNetname() for p in fps[r].Pads() if p.GetNetname() != "GND"][0]
        rank[r] = seen_net.get(nn, 0)
        seen_net[nn] = rank[r] + 1
    order = sorted(TOP_CAPS, key=lambda r: (not isinstance(TOP_CAPS[r], tuple), TOP_CAPS[r] is not None, rank[r], r))
    if which is not None:
        order = [r for r in order if r in which]
    for ref in order:
        ball = TOP_CAPS[ref]
        f = fps[ref]
        if isinstance(ball, tuple):          # a fixed spot
            f.SetOrientationDegrees(ball[2])
            f.SetPosition(mm(ball[0], ball[1]))
            register_fp(f)
            if not connect_cap(f):
                raise RoutingFailed("fixed capacitor %s" % ref)
            placed.append(fp_box(f))
            continue
        nn = [p.GetNetname() for p in f.Pads()]
        sig = [n for n in nn if n != "GND"][0]
        if ball is None:
            ball = [b for b, n in P1_NET.items() if n == sig][0]
        bx, by = BALL[ball]
        spots = []
        for r in range(0, 30):
            rr = r * 0.2
            k = max(1, int(2 * math.pi * rr / 0.2))
            for t in range(k):
                a = 2 * math.pi * t / k
                x, y = round(bx + rr * math.cos(a), 1), round(by + rr * math.sin(a), 1)
                for rot in (0, 90):
                    f.SetOrientationDegrees(rot)
                    f.SetPosition(mm(x, y))
                    b = fp_box(f)
                    if any(b[0] < ln[2] and ln[0] < b[2] and b[1] < ln[3] and ln[1] < b[3] for ln in lanes):
                        continue
                    if b[0] < 26.5 or b[2] > 41.5 or b[1] < 7.0 or b[3] > 23.0:
                        continue
                    if any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in placed):
                        continue
                    if not pads_free(f, 0):
                        continue
                    spots.append((x, y, rot))
        done = False
        for x, y, rot in spots[:80]:
            cp = Checkpoint()
            f.SetOrientationDegrees(rot)
            f.SetPosition(mm(x, y))
            register_fp(f)
            if connect_cap(f):
                done = True
                break
            cp.restore()
        if not done:
            print("cap failures:", {k: v for k, v in CAP_FAIL.items() if k[0] == ref}, "spots", len(spots))
            raise RoutingFailed("no room on the top for %s" % ref)
        placed.append(fp_box(f))


def pads_free(f, li):
    """Every pad of f has only free cells / its own net round it on layer li (and room left for
    a via-free courtyard: no foreign via under the part)."""
    for p in f.Pads():
        nid = G.nid(p.GetNetname())
        bb = p.GetBoundingBox()
        x0, y0, x1, y1 = (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()),
                          pcbnew.ToMM(bb.GetBottom()))
        sl = G._win(x0, y0, x1, y1, 0.08)
        sl = (slice(sl[0], sl[1]), slice(sl[2], sl[3]))
        X, Y = G.X[sl], G.Y[sl]
        m = (X >= x0 - 0.08) & (X <= x1 + 0.08) & (Y >= y0 - 0.08) & (Y <= y1 + 0.08)
        o = G.owner[li][sl][m]
        if np.any((o != RT.FREE) & (o != nid)):
            return False
    return True


def free_spot_via(x, y, n, radius=2.5, need=None, layer=None, stub_hw=0.125):
    """Nearest spot for a via of net n around (x, y) reachable by a straight
    track on `layer` from (x, y)."""
    best = None
    nid = G.nid(n)
    r_v = VIA_D / 2 + VIA_CLEAR + 0.02
    for k in range(1, int(radius / 0.1) + 1):
        rr = k * 0.1
        cand = []
        for t in range(max(8, int(2 * math.pi * rr / 0.1))):
            a = 2 * math.pi * t / max(8, int(2 * math.pi * rr / 0.1))
            cand.append((round(x + rr * math.cos(a), 1), round(y + rr * math.sin(a), 1)))
        for vx, vy in cand:
            if need and not need((vx, vy)):
                continue
            if not via_free(vx, vy, n):
                continue
            # the stub from the pad to the via
            if layer is not None and not line_free((x, y), (vx, vy), layer, n, stub_hw):
                continue
            return (vx, vy)
    return best


def stitch(fp, num, n, need=None, w=0.25):
    """A pad of a plane net drops into its plane through a via beside it."""
    p = pad_of(fp, num)
    x, y = xy(p.GetPosition())
    li = 0 if p.IsOnLayer(pcbnew.F_Cu) else 1
    bb = p.GetBoundingBox()
    r0 = max(pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())) / 2
    s = free_spot_via(x, y, n, radius=r0 + 2.0, need=need, layer=li, stub_hw=w / 2)
    if s is None:
        return False
    add_track([(x, y), s], li, n, w)
    add_via(s[0], s[1], n)
    return True


def cells_near(x, y, r):
    out = set()
    iy, ix = G.cell(x, y)
    k = int(r / G.p) + 1
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            if math.hypot(dx * G.p, dy * G.p) <= r and 0 <= iy + dy < G.H and 0 <= ix + dx < G.W:
                out.add((iy + dy, ix + dx))
    return out


def route_pad_to_net(step, fp, num, n, **kw):
    """One pad to the copper of its net already on the board (any part of it). GND: to a via
    (In1 is whole). 3.3 V: to a ball of P1 or its via (the In2 island may be cut by antipads)."""
    src = item_cells(fp.GetReference(), num)
    if n == "GND":
        tgt = via_cells("GND") - src
    elif n == "+3V3":
        tgt = set()
        for b, nn in P1_NET.items():
            if nn == "+3V3":
                tgt |= item_cells("U101", b)
        tgt |= DOGBONE_CELLS.get("+3V3", set())
    else:
        tgt = copper_cells(n) - src
    return route(step, "%s.%s -> %s" % (fp.GetReference(), num, n), n, src, tgt, **kw)


def route_items(step, n, items, **kw):
    """Join pads [(fp, num)] of a net into one tree, nearest first."""
    done = [items[0]]
    rest = list(items[1:])
    while rest:
        def d(it):
            a = xy(pad_of(*it).GetPosition())
            return min(math.hypot(a[0] - xy(pad_of(*o).GetPosition())[0], a[1] - xy(pad_of(*o).GetPosition())[1])
                       for o in done)
        nxt = min(rest, key=d)
        rest.remove(nxt)
        src = item_cells(nxt[0].GetReference(), nxt[1])
        tgt = set()
        for o in done:
            tgt |= item_cells(o[0].GetReference(), o[1])
        tgt |= TREE.get(n, set())
        if not (src & tgt):
            path = route(step, "%s.%s -> %s" % (nxt[0].GetReference(), nxt[1], n), n, src, tgt, **kw)
            TREE.setdefault(n, set()).update((l, iy, ix) for l, iy, ix in path)
        done.append(nxt)
    ROUTED.add(n)


def offset_polyline(pts, d):
    """Offset a polyline by d (left of travel positive), miter joins."""
    out = []
    for i, p in enumerate(pts):
        if i == 0:
            a, b = pts[0], pts[1]
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            L = math.hypot(nx, ny)
            out.append((p[0] + d * nx / L, p[1] + d * ny / L))
        elif i == len(pts) - 1:
            a, b = pts[-2], pts[-1]
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            L = math.hypot(nx, ny)
            out.append((p[0] + d * nx / L, p[1] + d * ny / L))
        else:
            a, b, c = pts[i - 1], pts[i], pts[i + 1]
            n1 = (-(b[1] - a[1]), b[0] - a[0])
            n2 = (-(c[1] - b[1]), c[0] - b[0])
            l1, l2 = math.hypot(*n1), math.hypot(*n2)
            n1 = (n1[0] / l1, n1[1] / l1)
            n2 = (n2[0] / l2, n2[1] / l2)
            m = (n1[0] + n2[0], n1[1] + n2[1])
            lm = math.hypot(*m)
            m = (m[0] / lm, m[1] / lm)
            cosh = m[0] * n1[0] + m[1] * n1[1]
            out.append((p[0] + d * m[0] / cosh, p[1] + d * m[1] / cosh))
    return out


def simplify(pts):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        ax, ay = out[-1]
        bx, by = pts[i]
        cx, cy = pts[i + 1]
        if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
            out.append(pts[i])
    out.append(pts[-1])
    return out


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


USB_REPORT = {}


def route_usb(fps):
    """C1: USB-C (E1, top) -> E2 taps -> P1, an edge-coupled pair on F.Cu over
    the In1 GND plane, one pair of vias (at the BGA)."""
    j = fps["J201"]
    P = {num: xy(pad_of(j, num).GetPosition()) for num in ("A6", "B6", "A7", "B7")}
    ax, ay = xy(j.GetPosition())

    # local frame of the connector: u along the pad row (A6 -> B6), v from the mouth to the rear
    def L2B(u, v):
        # board = centre + u * eu + v * ev; eu from A6 to B6 direction, ev: rear direction
        return (ax + u * EU[0] + v * EV[0], ay + u * EU[1] + v * EV[1])
    a6, b6 = P["A6"], P["B6"]
    d = (b6[0] - a6[0], b6[1] - a6[1])
    Ld = math.hypot(*d)
    EU = (d[0] / Ld, d[1] / Ld)                 # +u: from A6 (u = -0.25) to B6 (u = +0.75)
    # rear = away from the mouth: the pads sit at the rear (local y -4.045)
    pc = ((a6[0] + b6[0]) / 2, (a6[1] + b6[1]) / 2)
    rv = (pc[0] - ax, pc[1] - ay)
    # component of rv perpendicular to EU
    dot = rv[0] * EU[0] + rv[1] * EU[1]
    perp = (rv[0] - dot * EU[0], rv[1] - dot * EU[1])
    Lp = math.hypot(*perp)
    EV = (perp[0] / Lp, perp[1] / Lp)            # +v: towards the rear (pads at v ~ +4.045)
    vpad = (P["A6"][0] - ax) * EV[0] + (P["A6"][1] - ay) * EV[1]
    u0 = (P["A6"][0] - ax) * EU[0] + (P["A6"][1] - ay) * EU[1] + 0.25   # local u of the pad row's middle
    vfront, vrear = vpad - 0.725, vpad + 0.725
    U = lambda u, v: L2B(u0 + u, v)              # noqa: E731
    w = USB_W
    # DN: B7 (u -0.75) and A7 (u +0.25) joined in front of A6, under the connector body
    vj = vfront - 0.12 - CLEAR - w / 2
    dn = [U(-0.75, vpad), U(-0.75, vj), U(0.25, vj), U(0.25, vpad)]
    add_track(dn, 0, "USB_DN", w)
    # DP: A6 (u -0.25) and B6 (u +0.75) joined behind A7
    vk = vrear + 0.12 + CLEAR + w / 2
    dp = [U(-0.25, vpad), U(-0.25, vk), U(0.75, vk), U(0.75, vpad)]
    add_track(dp, 0, "USB_DP", w)
    pitch = w + USB_S
    # exits: DN from B7's rear end straight back, DP from its joint; then they close to the pair pitch
    vexit = vk + 1.0
    dn_exit = [U(-0.75, vpad), U(-0.75, vexit)]
    mid_u = -0.75 + pitch                       # DP's lane once coupled
    dp_exit = [U(0.25, vk), U(0.25, vk + 0.3), U(mid_u, vk + 0.3 + (0.25 - mid_u)), U(mid_u, vexit)]
    add_track(dn_exit, 0, "USB_DN", w)
    add_track(dp_exit, 0, "USB_DP", w)
    centre_start = U(-0.75 + pitch / 2, vexit)
    # E2 (USBLC6) sits on the back right under the pair; its taps: DN row and DP row
    e2 = fps["U201"]
    ex, ey = xy(e2.GetPosition())
    # pair: straight from the connector exit to E2's centre line, then A* to the BGA
    dn_side = U(-0.75, vexit)
    ycen = centre_start[1]
    # E2 rows: pins 1/6 (DP) and 3/4 (DN) at ey -/+ 0.95 -> put the pair's centre on ey
    seg_a = [centre_start]
    # go along +x (the connector's rear direction) until 1.5 mm before E2, jog to ey, pass E2, 1.5 mm after
    xa = centre_start[0] + 0.8
    seg_a.append((xa, ycen))
    jog = abs(ey - ycen)
    seg_a.append((xa + jog, ey))
    seg_a.append((ex + 2.0, ey))
    # where is DN relative to the centre line? (left of travel = -y when travelling +x)
    dn_left = (dn_side[1] - ycen) < 0
    # A* for the rest: fat track (2w + s) on F.Cu only, from E2's far side to the BGA entry
    entry = (27.0, 15.1)
    hw_pair = w + USB_S / 2
    src = {(0,) + c for c in cells_near(seg_a[-1][0], seg_a[-1][1], 0.05)}
    tgt = {(0,) + c for c in cells_near(entry[0], entry[1], 0.05)}
    # the pair's own pieces must not block it: search as a pseudo-net
    path = G.search("USB_PAIR", src, tgt, hw_pair, None, None, allow_via=False, layers_ok=(0,),
                    extra_ok=("USB_DP", "USB_DN"))
    if path is None:
        raise RoutingFailed("USB pair")
    cl = simplify([(G.x(ix), G.y(iy)) for l, iy, ix in path])
    centre = simplify(seg_a + cl[1:])
    # left offset = DN if DN is on the left of travel
    sgn = 1 if dn_left else -1
    dn_line = offset_polyline(centre, -sgn * pitch / 2 * -1)
    dp_line = offset_polyline(centre, sgn * pitch / 2 * -1)
    # make sure DN really is the one that started at the DN exit
    if math.hypot(dn_line[0][0] - dn_side[0], dn_line[0][1] - dn_side[1]) > \
            math.hypot(dp_line[0][0] - dn_side[0], dp_line[0][1] - dn_side[1]):
        dn_line, dp_line = dp_line, dn_line
    # into the vias: DN (upper) -> USB_VIA["USB_DN"], DP (lower) -> USB_VIA["USB_DP"]
    dvx, dvy = USB_VIA["USB_DN"]
    pvx, pvy = USB_VIA["USB_DP"]
    dn_end = dn_line[-1]
    dp_end = dp_line[-1]
    dn_tail = [dn_end, (dvx - abs(dvy - dn_end[1]), dn_end[1]), (dvx, dvy)]
    dp_tail = [dp_end, (pvx - abs(pvy - dp_end[1]), dp_end[1]), (pvx, pvy)]
    add_track(simplify(dn_line + dn_tail[1:]), 0, "USB_DN", w)
    add_track(simplify(dp_line + dp_tail[1:]), 0, "USB_DP", w)
    # (the two vias and their tails to the balls were placed with the BGA's fan-out)
    # E2 taps: a via on each row's middle, a short stub up to its line; pins of a row joined on the back
    rows = {}
    for num in ("1", "6", "3", "4"):
        rows.setdefault(pad_of(e2, num).GetNetname(), []).append(xy(pad_of(e2, num).GetPosition()))
    for nn, pts in rows.items():
        pts.sort()
        add_track([pts[0], pts[1]], 1, nn, 0.25)
        vx, vy = (pts[0][0] + pts[1][0]) / 2, pts[0][1]
        add_via(vx, vy, nn)
        line = dn_line if nn == "USB_DN" else dp_line
        # vertical stub up to the line at x = vx
        ly = None
        for a, b in zip(line, line[1:]):
            if min(a[0], b[0]) - 1e-6 <= vx <= max(a[0], b[0]) + 1e-6 and abs(a[0] - b[0]) > 1e-6:
                ly = a[1] + (vx - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
                break
        add_track([(vx, vy), (vx, ly)], 0, nn, 0.2)
    ldn = plen(dn) / 2 + plen(dn_exit) + plen(simplify(dn_line + dn_tail[1:])) + 1.2
    ldp = plen(dp) / 2 + plen(dp_exit) + plen(simplify(dp_line + dp_tail[1:])) + 1.2
    USB_REPORT.update(dn=round(ldn, 2), dp=round(ldp, 2), skew=round(abs(ldn - ldp), 2), vias=1, w=w, s=USB_S,
                      zdiff=IMPEDANCE["usb"]["zdiff"])
    ROUTE_LOG.append(("3 USB", "E1 -> E2 -> P1 (par)", "USB_DP/DN", round((ldn + ldp) / 2, 2), 2))


BALL_BY_NET = {}


def route_sector_p(fps, comps, pads):
    for p in fps["U101"].Pads():
        if p.GetNetname():
            BALL_BY_NET.setdefault(p.GetNetname(), []).append(xy(p.GetPosition()))
    # keep the USB pair's lane on top free of everything else, and nothing over the crystals
    usb_block = []
    for s in USB_SITES:
        G.novia[G.cell(*s)] = True
    unplaced = dogbones(fps)
    for nn in ("USB_DN", "USB_DP"):        # C1's one pair of vias, next to its balls
        vx, vy = USB_VIA[nn]
        add_via(vx, vy, nn)
        add_track([(vx, vy), BALL_BY_NET[nn][0]], 1, nn, THIN)
    # P8 (VDD_HIGH_CAP) has every site under the USB pair: a short escape to a via just outside
    p8 = [b for b, n in P1_NET.items() if n == "VDD_HIGH_CAP"][0]
    bx, by = BALL[p8]
    add_track([(bx, by), (bx - 0.9, by), (bx - 0.9, by + 1.15)], 1, "VDD_HIGH_CAP", 0.2)
    add_via(bx - 0.9, by + 1.15, "VDD_HIGH_CAP")
    print("BGA power fan-out: %d vias, balls joined on the back instead: %s" % (len(VIAS), unplaced))
    cry = []
    for ref in ("Y101", "Y102"):
        b = fp_box(fps[ref])
        cry.append((b[0] - 0.3, b[1] - 0.3, b[2] + 0.3, b[3] + 0.3))
    # 1st: clocks (P5 -> P1), on the back, short, nothing over them on the top
    for r in cry:
        G.block_rect((0,), *r)
    # their ground pads into the GND plane first (the clock lines would wall them in)
    for ref in ("C120", "C121", "R102", "C122", "C123", "Y101"):
        for p in fps[ref].Pads():
            if p.GetNetname() == "GND":
                if not stitch(fps[ref], p.GetNumber(), "GND"):
                    route_pad_to_net("1 relogios", fps[ref], p.GetNumber(), "GND")
    for n in ("XTALI", "XTALO", "RTC_XTALI", "RTC_XTALO"):
        items = [(f, p.GetNumber()) for f in (fps["U101"], fps["Y101"], fps["Y102"]) for p in f.Pads()
                 if p.GetNetname() == n]
        route_items("1 relogios", n, items, layers_ok=(1,), allow_via=False)
    for ref in ("C120", "C121", "R102", "C122", "C123"):
        for p in fps[ref].Pads():
            if p.GetNetname() != "GND":
                route_pad_to_net("1 relogios", fps[ref], p.GetNumber(), p.GetNetname(), layers_ok=(1,),
                                 allow_via=False)
    # 2nd: BGA power and P1's capacitors (top side); USB lane reserved meanwhile
    lane = (27.4, 14.35, 30.45, 15.85)
    G.reserve((0,), *lane, "USB_PAIR")
    G.reserve((0,), 30.45, 15.05, 31.25, 15.85, "USB_PAIR")
    G.reserve((0,), 11.0, 11.6, 27.5, 16.4, "USB_PAIR")      # C1 from E1 past E2 to the BGA
    # P1's DC-DC way out (M1/M2 down to L102, L1/L2 to the caps): kept for step 5
    G.reserve((1,), 26.6, 21.0, 35.7, 27.6, "DCDC_LP")
    G.reserve((1,), 29.95, 19.55, 31.65, 21.0, "DCDC_LP")      # round M1/M2 (DCDC_LP), L1/L2 (DCDC_IN)
    # the memories' and the bootloader-free corners stay free for steps 4 (flash left, PSRAM right)
    G.reserve((1,), 18.8, 16.6, 27.9, 24.6, "FLASH_D1")
    G.reserve((1,), 27.9, 16.6, 31.75, 19.75, "FLASH_D1")      # the flash balls' own channels
    G.reserve((1,), 35.6, 21.6, 41.2, 26.8, "PSRAM_CS")
    G.reserve((1,), 35.6, 18.7, 39.65, 21.6, "PSRAM_CS")      # the PSRAM balls' own corner
    for b in unplaced:
        n = P1_NET[b]
        src = item_cells("U101", b)
        route("2 BGA", "U101.%s -> %s" % (b, n), n, src, (via_cells(n) | copper_cells(n)) - src, via_cost=4.0)
    # the BGA's other sector P signals (bootloader, PSWITCH, POR_B, SNVS ...), before the
    # capacitors take the top side
    p_refs = {r for r, c in comps.items() if c["code"].startswith("P")} | {"U101"}
    by_net = {}
    for f in fps.values():
        for p in f.Pads():
            n = p.GetNetname()
            if n:
                by_net.setdefault(n, []).append((f, p.GetNumber()))
    later = {"AUD_MCLK_P", "DCDC_IN", "DCDC_LP"} | CAP_NETS
    internal = []
    for n, items in by_net.items():
        if n in ("GND", "+3V3", "VDD_SOC") or n.startswith("USB_") or n.startswith("FLASH_") or                 n.startswith("PSRAM_") or n in ROUTED or n in later:
            continue
        p_items = [it for it in items if it[0].GetReference() in p_refs]
        if len(p_items) > 1:
            internal.append(n)
    # capacitors of the one-ball supplies first (they must sit right over their ball) ...
    place_top_caps(fps, [r for r, b in TOP_CAPS.items() if b is None or isinstance(b, tuple)])
    # the SNVS diodes (D101/D102) onto those supplies right away
    for n in ("VDD_SNVS_IN", "VDD_USB_CAP"):
        route_items("2 BGA", n, [it for it in by_net[n] if it[0].GetReference() in p_refs])
    for n in sorted(internal, key=lambda n: (n not in ROUTE_FIRST, ROUTE_FIRST.index(n) if n in ROUTE_FIRST else 0,
                                            len(by_net[n]))):
        route_items("2 BGA", n, [it for it in by_net[n] if it[0].GetReference() in p_refs])
    # ... the 3.3 V / VDD_SOC ones (they reach their plane anywhere) after the bootloader lines
    place_top_caps(fps, [r for r, b in TOP_CAPS.items() if isinstance(b, str)])
    G.release("USB_PAIR")
    # 3rd: USB
    route_usb(fps)
    # 4th: memories (flash P3, PSRAM P4): on the back, no vias if possible
    G.release("FLASH_D1")
    G.release("PSRAM_CS")
    # the memories' own supply pads into their planes first (they would be walled in by the lines)
    for ref in ("U103", "U104"):
        f = fps[ref]
        for p in f.Pads():
            n = p.GetNetname()
            if n in ("GND", "+3V3"):
                if not stitch(f, p.GetNumber(), n, need=plus3_ok if n == "+3V3" else None):
                    route_pad_to_net("4 memorias", f, p.GetNumber(), n)
    # inner balls first (they need the channels between the outer ones)
    mem = ["FLASH_D1", "FLASH_CS", "FLASH_CLK", "FLASH_D2", "FLASH_D0", "FLASH_D3",
           "PSRAM_CS", "PSRAM_CLK", "PSRAM_D0", "PSRAM_D1", "PSRAM_D2", "PSRAM_D3"]
    mem.sort(key=lambda n: (n[:5], n not in ROUTE_FIRST, ROUTE_FIRST.index(n) if n in ROUTE_FIRST else 0))
    for nn in mem:
        items = [(f, p.GetNumber()) for f in (fps["U101"], fps["U103"], fps["U104"]) for p in f.Pads()
                 if p.GetNetname() == nn]
        try:
            route_items("4 memorias", nn, items, layers_ok=(1,), allow_via=False)
        except RoutingFailed:
            route_items("4 memorias", nn, items, via_cost=6.0)
    # 5th: P1's DC-DC (DCDC_IN, DCDC_LP to L102, VDD_SOC into its island)
    for nn in ("DCDC_LP", "DCDC_IN"):
        if nn == "DCDC_IN":
            G.release("DCDC_LP")
        items = [(f, p.GetNumber()) for f in fps.values() if f.GetReference() in
                 ("U101", "L101", "L102", "C101", "C102", "C103") for p in f.Pads() if p.GetNetname() == nn]
        route_items("5 conversor", nn, items, layers_ok=(1,), allow_via=False)
    for ref in ("L102", "C104", "C105"):
        for p in fps[ref].Pads():
            if p.GetNetname() == "VDD_SOC":
                for _ in range(2 if ref == "L102" else 1):
                    if not stitch(fps[ref], p.GetNumber(), "VDD_SOC", need=in_vdd, w=0.4):
                        raise RoutingFailed("VDD_SOC stitch %s" % ref)
    # 6th: MCLK's 100 ohm beside P1
    route_items("6 MCLK", "AUD_MCLK_P", [(fps["U101"], [p.GetNumber() for p in fps["U101"].Pads()
                                                           if p.GetNetname() == "AUD_MCLK_P"][0]),
                                          (fps["R105"], [p.GetNumber() for p in fps["R105"].Pads()
                                                         if p.GetNetname() == "AUD_MCLK_P"][0])])
    # plane pads of sector P parts (not the BGA): a via each
    for f in fps.values():
        ref = f.GetReference()
        if ref not in p_refs or ref == "U101" or ref in TOP_CAPS:
            continue
        for p in f.Pads():
            n = p.GetNetname()
            if n not in ("GND", "+3V3"):
                continue
            if copper_touch(f, p):
                continue
            need = plus3_ok if n == "+3V3" else None
            if not stitch(f, p.GetNumber(), n, need=need):
                route_pad_to_net("7 setor P", f, p.GetNumber(), n)
    internal = []
    for n, items in by_net.items():
        if n in ("GND", "+3V3", "VDD_SOC") or n.startswith("USB_") or (n in ROUTED and n not in CAP_NETS):
            continue
        p_items = [it for it in items if it[0].GetReference() in p_refs]
        if len(p_items) > 1:
            internal.append(n)
    for n in sorted(internal, key=lambda n: (n not in ROUTE_FIRST, ROUTE_FIRST.index(n) if n in ROUTE_FIRST else 0,
                                            len(by_net[n]))):
        route_items("7 setor P", n, [it for it in by_net[n] if it[0].GetReference() in p_refs])
    # last: every signal that leaves sector P gets out of the BGA to its edge (a via there)
    escape(fps, comps, by_net, p_refs)


def copper_touch(f, p):
    """True when the pad already touches copper of its net routed earlier (a fan-out)."""
    return False


ESCAPES = {}


def escape(fps, comps, by_net, p_refs):
    ring = set()
    for iy in range(G.H):
        y = G.y(iy)
        for ix in range(G.W):
            x = G.x(ix)
            dx, dy = abs(x - BGA_CX), abs(y - BGA_CY)
            if max(dx, dy) < BGA_HALF + 0.9 or max(dx, dy) > BGA_HALF + 3.0:
                continue
            if not (21.0 <= x <= 53.5 and 3.5 <= y <= 31.0):
                continue
            ring.add((iy, ix))
    for n in sorted(by_net):
        if n in ("GND", "+3V3", "VDD_SOC", "VBUS") or n.startswith("USB_"):
            continue
        items = by_net[n]
        refs = {f.GetReference() for f, _ in items}
        if not (refs & p_refs) or refs <= p_refs:
            continue
        # sector P side of the net: the ball(s) and any P part's pads (already joined)
        p_items = [(f, num) for f, num in items if f.GetReference() in p_refs]
        src = set()
        for f, num in p_items:
            src |= item_cells(f.GetReference(), num)
        src |= copper_cells(n)
        # already outside? (a P passive on the net may sit outside the BGA)
        if any(max(abs(G.x(ix) - BGA_CX), abs(G.y(iy) - BGA_CY)) > BGA_HALF + 0.9 for l, iy, ix in src):
            ESCAPES[n] = "fora do BGA (passivo do P)"
            continue
        tgt = {(l, iy, ix) for (iy, ix) in ring for l in (0, 1)}
        path = route("8 saida do BGA", "%s -> borda" % n, n, src, tgt, w=TRACK, must=False)
        if path is None:
            ESCAPES[n] = "FALHOU"
            continue
        l, iy, ix = path[-1]
        x, y = G.x(ix), G.y(iy)
        ESCAPES[n] = (round(x, 2), round(y, 2), "F.Cu" if l == 0 else "B.Cu")


# ======================================================================= zones
def zone(layer, n, poly, prio=0, clearance=0.15, min_w=0.12, name=""):
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


def zones(fps):
    x0, y0, x1, y1 = REV2["board"]["rect"]
    whole = rect_poly(x0, y0, x1, y1)
    zone(pcbnew.In1_Cu, "GND", whole, 0, name="L2 GND")
    zone(pcbnew.In2_Cu, "GND", whole, 0, name="L3 GND")
    zone(pcbnew.In2_Cu, "+3V3", P3V3_ISLAND, 1, name="L3 3V3 (setor P)")
    zone(pcbnew.In2_Cu, "VDD_SOC", VDD_ISLAND, 2, name="L3 VDD_SOC")
    # GND round the crystals on the back
    b1, b2 = fp_box(fps["Y101"]), fp_box(fps["Y102"])
    zone(pcbnew.B_Cu, "GND", rect_poly(min(b1[0], b2[0]) - 2.2, min(b1[1], b2[1]) - 1.2, 28.25,
                                       max(b1[3], b2[3]) + 0.4), 0, clearance=0.2, min_w=0.2, name="GND cristais")
    # nothing over the crystals on F.Cu / In1 / In2 (tracks, vias)
    for ref in ("Y101", "Y102"):
        b = fp_box(fps[ref])
        keepout_rect(rect_poly(b[0], b[1], b[2], b[3]), (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu), "cristal %s" % ref)


# ======================================================================= project + stack-up
def write_project():
    pro = json.load(open(PRO_PATH, encoding="utf-8")) if os.path.exists(PRO_PATH) else {}
    b = pro.setdefault("board", {})
    dsj = b.setdefault("design_settings", {})
    dsj.setdefault("defaults", {})
    dsj["rules"] = {
        "max_error": 0.005, "min_clearance": CLEAR, "min_connection": 0.0, "min_copper_edge_clearance": EDGE_CLEAR,
        "min_groove_width": 0.0, "min_hole_clearance": HOLE_CLEAR, "min_hole_to_hole": 0.2,
        "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 2,
        "min_silk_clearance": 0.0, "min_text_height": 0.6, "min_text_thickness": 0.08,
        "min_through_hole_diameter": VIA_DRILL, "min_track_width": THIN, "min_via_annular_width": 0.075,
        "min_via_diameter": VIA_D, "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True}
    dsj["track_widths"] = [0.0, THIN, TRACK, USB_W, CORE_W, POWER_W]
    dsj["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": VIA_D, "drill": VIA_DRILL}]
    dsj["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0},
                                   {"gap": USB_S, "via_gap": 0.25, "width": USB_W}]
    sev = dsj.setdefault("rule_severities", {})
    sev.update({"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore", "silk_overlap": "ignore",
                "silk_over_copper": "ignore", "silk_edge_clearance": "ignore", "text_height": "ignore",
                "text_thickness": "ignore", "footprint_symbol_mismatch": "ignore", "nonmirrored_text_on_back_layer":
                "ignore",
                # the sector P escapes end at the BGA's edge on purpose (steps 3.3 / 3.4 take them on)
                "track_dangling": "ignore", "via_dangling": "ignore"})

    def cls(name, w, clr=CLEAR, extra=None):
        c = {"bus_width": 12, "clearance": clr, "diff_pair_gap": USB_S, "diff_pair_via_gap": 0.25,
             "diff_pair_width": USB_W, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
             "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
             "track_width": w, "via_diameter": VIA_D, "via_drill": VIA_DRILL, "wire_width": 6,
             "priority": 2147483647 if name == "Default" else len(name)}
        c.update(extra or {})
        return c
    pro["net_settings"] = {
        "classes": [cls("Default", TRACK), cls("USB", USB_W), cls("Corrente", POWER_W), cls("Nucleo", CORE_W)],
        "meta": {"version": 5}, "net_colors": {}, "netclass_assignments": {},
        "netclass_patterns": [{"netclass": "USB", "pattern": "USB_D[PN]"}] +
                             [{"netclass": "Corrente", "pattern": n} for n in sorted(POWER_NETS)] +
                             [{"netclass": "Nucleo", "pattern": n} for n in sorted(CORE_NETS)]}
    json.dump(pro, open(PRO_PATH, "w", encoding="utf-8"), indent=2)
    dru = """(version 1)
# eTutti Viaggio -- custom rules (written by build_board.py)
(rule "BGA: trilhas de 0,1 entre as bolas do P1"
    (condition "A.Type == 'track' && A.intersectsCourtyard('U101')")
    (constraint track_width (min %(thin)s)))
(rule "Sinais: 0,2 fora do BGA"
    (condition "A.Type == 'track' && A.NetClass == 'Default' && !A.intersectsCourtyard('U101')")
    (constraint track_width (min %(track)s)))
(rule "USB 90 ohm (par diferencial)"
    (condition "A.NetClass == 'USB' && A.Type == 'track' && !A.intersectsCourtyard('U101') && !A.intersectsCourtyard('J201') && !A.intersectsCourtyard('U201')")
    (constraint track_width (min %(usbw_min)s) (opt %(usbw)s) (max %(usbw_max)s))
    (constraint diff_pair_gap (min %(usbs_min)s) (opt %(usbs)s) (max %(usbs_max)s)))
(rule "Corrente: >= 0,8"
    (condition "A.Type == 'track' && A.NetClass == 'Corrente' && !A.intersectsCourtyard('U101')")
    (constraint track_width (min %(power)s)))
""" % dict(thin=THIN, track=TRACK, usbw=USB_W, usbw_min=round(USB_W - 0.04, 3), usbw_max=round(USB_W + 0.01, 3),
           usbs=USB_S, usbs_min=round(USB_S - 0.01, 3), usbs_max=round(USB_S + 0.05, 3), power=POWER_W)
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


# ======================================================================= checks + pictures
SECTOR_OF = {}


def sector_of_ref(ref, comps):
    if ref in comps and comps[ref]["code"]:
        return comps[ref]["code"][0]
    return "?"


def drc(comps):
    out = os.path.join(BUILD, "viaggio_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--output", out, BOARD_PATH],
                   check=False, capture_output=True)
    rep = json.load(open(out, encoding="utf-8"))
    vio = rep.get("violations", [])
    unc = rep.get("unconnected_items", [])
    pairs = {}
    for u in unc:
        secs = []
        for it in u.get("items", []):
            m = re.search(r"of (\w+)", it.get("description", ""))
            if m:
                secs.append(sector_of_ref(m.group(1), comps))
            else:
                p = it.get("pos", {})
                x, y = p.get("x", 0), p.get("y", 0)
                secs.append("P" if 21 <= x <= 53.5 and 3.5 <= y <= 31 else "?")
        key = "-".join(sorted(set(secs))) if secs else "?"
        pairs[key] = pairs.get(key, 0) + 1
    return vio, unc, pairs, rep


def pictures():
    shots = []
    for side in ("top", "bottom"):
        out = os.path.join(BUILD, "viaggio_%s.png" % side)
        r = subprocess.run([KICAD_CLI, "pcb", "render", "--side", side, "--width", "2400", "--height", "1000",
                            "--quality", "basic", "--output", out, BOARD_PATH], capture_output=True)
        shots.append((out, r.returncode))
    for name, layers in (("viaggio_P_F.Cu", "F.Cu,F.SilkS,Edge.Cuts"), ("viaggio_P_B.Cu", "B.Cu,B.SilkS,Edge.Cuts"),
                         ("viaggio_P_In1.Cu", "In1.Cu,Edge.Cuts"), ("viaggio_P_In2.Cu", "In2.Cu,Edge.Cuts"),
                         ("viaggio_P_todas", "F.Cu,B.Cu,In2.Cu,Edge.Cuts")):
        out = os.path.join(BUILD, name + ".svg")
        r = subprocess.run([KICAD_CLI, "pcb", "export", "svg", "--layers", layers, "--mode-single",
                            "--page-size-mode", "2", "--exclude-drawing-sheet", "--output", out, BOARD_PATH],
                           capture_output=True)
        shots.append((out, r.returncode))
    return shots


def main():
    os.makedirs(BUILD, exist_ok=True)
    try:
        fps, comps, pads = build()
    except RoutingFailed as e:
        pcbnew.SaveBoard(os.path.join(KDIR, "viaggio_failed.kicad_pcb"), board)
        print("routing failed:", e)
        sys.exit(3)
    write_stackup()
    write_project()
    vio, unc, pairs, rep = drc(comps)
    errors = [v for v in vio if v.get("severity") == "error"]
    print("DRC: %d errors, %d warnings, %d unconnected" % (len(errors), len(vio) - len(errors), len(unc)))
    kinds = {}
    for v in vio:
        kinds[v.get("type")] = kinds.get(v.get("type"), 0) + 1
    print("  violations by type:", kinds)
    for v in vio[:30]:
        print("  [%s] %s %s" % (v.get("severity"), v.get("type"), v.get("description")),
              [(i.get("description"), i.get("pos")) for i in v.get("items", [])[:2]])
    print("unconnected by sector pair:", dict(sorted(pairs.items())))
    summary = {"drc_errors": len(errors), "drc_warnings": len(vio) - len(errors), "unconnected": len(unc),
               "unconnected_by_sector": pairs, "usb": USB_REPORT, "escapes": ESCAPES,
               "route_log": ROUTE_LOG, "vias": len(VIAS),
               "lengths": {n: round(v, 2) for n, v in sorted(TRACK_LEN.items())}}
    json.dump(summary, open(os.path.join(BUILD, "viaggio_board_summary.json"), "w"), indent=1)
    shots = pictures()
    print("pictures:", shots)
    bad_p = pairs.get("P", 0)
    sys.exit(1 if vio or bad_p else 0)


def with_retries(max_attempts=20):
    first = list(ROUTE_FIRST)
    for attempt in range(max_attempts):
        env = dict(os.environ, VIAGGIO_ROUTE_FIRST=",".join(first), VIAGGIO_CHILD="1")
        r = subprocess.run([sys.executable, os.path.abspath(__file__)], env=env, capture_output=True, text=True)
        fails = [l for l in r.stdout.splitlines() if l.startswith("routing failed:")]
        if r.returncode != 3 or not fails:
            sys.stdout.write(r.stdout[-12000:])
            sys.stdout.write(r.stderr[-3000:])
            print("attempt %d: exit %d, route-first: %s" % (attempt + 1, r.returncode, ",".join(first) or "-"))
            return r.returncode
        f = fails[-1].split(":", 1)[1].strip()
        print("attempt %d: %s failed, again with it first" % (attempt + 1, f))
        if first and first[0] == f:
            print("it fails even when first: a physical blockage (see kicad/viaggio_failed.kicad_pcb)")
            return 3
        if f in first:
            first.remove(f)
        first.insert(0, f)
    return 3


if __name__ == "__main__":
    if os.environ.get("VIAGGIO_CHILD"):
        main()
    else:
        sys.exit(with_retries())
