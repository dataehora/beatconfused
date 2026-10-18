"""Build the routed eTuttino Pocket main board and its fab files.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/pocket/pcb/build_pocket_pcb.py

Geometry and netlist come from pocket_geom.py (which reads the case's
pcb_envelope.json). The grid router, placement helpers and track/via code
are the eTuttino's (etutti/hardware/build_pcb.py), used through its module
globals exactly as controls_pcb.py does -- nothing in the eTuttino scripts
changes.

Writes (all under etutti/hardware/pocket/pcb/):
  kicad/pocket.kicad_pcb            the board
  fab/pocket_gerbers.zip            Gerbers + drills
  fab/pocket_bom.csv                JLCPCB BOM (TMAG5253 consigned / global sourcing)
  fab/pocket_cpl_bottom.csv         placement, back (all ICs and passives)
  fab/pocket_cpl_top.csv            placement, top (the two JST SH headers)
  fab/pocket_drc.json               KiCad DRC report
  fab/pocket_top.png / _bottom.png  renders
  build/pocket_keys.csv             every key: sensor, mux, channel, EN group
  pocket_keys.h                     KEY_INPUT + pins for the Pocket firmware (P1)

4 copper layers: In1 = GND plane, In2 = 3.3 V plane (every GND / 3.3 V pad
drops into its plane through a via beside it); the router uses F.Cu / B.Cu.

Exits non-zero on a DRC error / warning / unconnected item or a mismatch
between the board and pocket_keys.h.
"""
import json
import math
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ETUTTINO_HW = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(1, ETUTTINO_HW)

import pcbnew  # noqa: E402

import build_pcb as B  # noqa: E402  (the eTuttino's router; its own geometry is not used)
import jlc  # noqa: E402
import pocket_geom as G  # noqa: E402

KICAD_DIR = os.path.join(HERE, "kicad")
FAB_DIR = os.path.join(HERE, "fab")
BOARD_PATH = os.path.join(KICAD_DIR, "pocket.kicad_pcb")
HEADER_PATH = os.path.join(HERE, "pocket_keys.h")
SENSOR_W = 0.2                  # stubs at the X2SON's 0.5 mm pitch pads
LOCAL_W = 0.3

POWER = {"VCC", "GND", "VSYS", "VBUS", "BAT", "SPK_P", "SPK_N", "L1", "L2", "VINA"}
DEFAULT_ROUTE_FIRST = "PWR_A,SPK_P,SPK_N,SEL2,EN_B,SEL3,NS3,POT,EN_A,L1"
DEFAULT_OUT_FIRST = "OUT_U25,OUT_U17,OUT_U18"

# ---------------------------------------------------------------- parts
# (ref, library, footprint, value, x, y, rot, side, {pad: net}, lcsc)
# side "B" = back (JLCPCB assembly), "T" = top.
R0805, C0805 = ("Resistor_SMD", "R_0805_2012Metric"), ("Capacitor_SMD", "C_0805_2012Metric")
SOT23 = ("Package_TO_SOT_SMD", "SOT-23")
SOT235 = ("Package_TO_SOT_SMD", "SOT-23-5")


def two(a, b):
    return {"1": a, "2": b}


PARTS = [
    # --- charger BQ24074 (USB500 mode, 500 mA, NTC on TS) ---
    ("U60", "Package_DFN_QFN", "QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm", "BQ24074RGTR", 77.0, 10.0, 0, "B",
     {"1": "TS", "2": "BAT", "3": "BAT", "4": "GND", "5": "GND", "6": "EN1", "8": "GND", "9": "CHG",
      "10": "VSYS", "11": "VSYS", "12": "ILIM", "13": "VBUS", "16": "ISET", "17": "GND"}, "C54313"),
    ("C60", *C0805, "10uF", 71.8, 8.0, 90, "B", two("VBUS", "GND"), "C15850"),
    ("C61", *C0805, "10uF", 82.6, 6.8, 90, "B", two("VSYS", "GND"), "C15850"),
    ("C62", *C0805, "10uF", 71.8, 15.2, 90, "B", two("BAT", "GND"), "C15850"),
    ("R10", *R0805, "1.8k", 71.8, 11.6, 90, "B", two("ISET", "GND"), "C1358"),
    ("R11", *R0805, "1.5k", 82.6, 13.4, 90, "B", two("ILIM", "GND"), "C4310"),
    ("R12", *R0805, "10k", 77.0, 15.8, 0, "B", two("VBUS", "EN1"), "C17414"),
    # --- buck-boost TPS63001 (fixed 3.3 V) ---
    ("U61", "Package_SON", "Texas_DRC0010J", "TPS63001DRCR", 87.5, 10.0, 0, "B",
     {"1": "VCC", "2": "L2", "3": "GND", "4": "L1", "5": "VSYS", "6": "EN_BB", "7": "GND", "8": "VINA",
      "9": "GND", "10": "VCC", "11": "GND"}, "C28060"),
    ("L10", "Inductor_SMD", "L_Changjiang_FNR4020S", "2.2uH 4x4", 93.6, 10.0, 90, "B", two("L1", "L2"), "C167825"),
    ("C63", *C0805, "10uF", 85.8, 16.4, 0, "B", two("VSYS", "GND"), "C15850"),
    ("C64", *C0805, "10uF", 92.6, 16.4, 0, "B", two("VCC", "GND"), "C15850"),
    ("C65", *C0805, "10uF", 96.0, 16.4, 0, "B", two("VCC", "GND"), "C15850"),
    ("R13", *R0805, "100", 89.2, 16.4, 0, "B", two("VSYS", "VINA"), "C17408"),
    ("C66", *C0805, "100nF", 85.6, 5.2, 0, "B", two("VINA", "GND"), "C49678"),
    # --- power switch: volume-pot switch + RC start pulse + KEEP latch ---
    ("R20", *R0805, "100", 73.5, 25.0, 90, "B", two("VSYS", "PWR_A"), "C17408"),
    ("R21", *R0805, "1M", 76.5, 25.0, 90, "B", two("PWR_B", "GND"), "C17514"),
    ("C81", *C0805, "1uF", 79.5, 25.0, 90, "B", two("PWR_B", "PULSE"), "C28323"),
    ("R22", *R0805, "1M", 82.5, 25.0, 90, "B", two("PULSE", "GND"), "C17514"),
    ("D20", *SOT23, "BAT54C", 86.0, 25.0, 0, "B", {"1": "PULSE", "2": "HOLD", "3": "EN_BB"}, "C134405"),
    ("R23", *R0805, "1M", 89.5, 25.0, 90, "B", two("EN_BB", "GND"), "C17514"),
    ("Q20", *SOT23, "AO3401A", 74.5, 31.0, 0, "B", {"1": "QSG", "2": "PWR_B", "3": "HOLD"}, "C15127"),
    ("R24", *R0805, "100k", 78.6, 31.0, 0, "B", two("QSG", "PWR_B"), "C17407"),
    ("Q21", *SOT23, "AO3400A", 82.8, 31.0, 0, "B", {"1": "KEEP", "2": "GND", "3": "QSG"}, "C20917"),
    ("R25", *R0805, "100k", 86.6, 31.0, 0, "B", two("KEEP", "GND"), "C17407"),
    # SPEC v4 (F2): with USB present the switch alone holds the converter on
    # (Q22 in parallel with the KEEP transistor). Without it, the Teensy could
    # never be flashed: the bootloader lets go of pin 10 during an upload and
    # KEEP's 100 k would switch the Pocket off mid-flash; and the first tests
    # (no Pocket firmware) could not keep the 3.3 V up.
    ("Q22", *SOT23, "AO3400A", 90.6, 31.0, 0, "B", {"1": "VBUS", "2": "GND", "3": "QSG"}, "C20917"),
    ("R26", *R0805, "100k", 94.4, 31.0, 0, "B", two("VBUS", "GND"), "C17407"),
    # --- charge light (CHG -> red of the LED, works switched off) + LED resistors ---
    ("Q30", *SOT23, "AO3401A", 40.0, 17.0, 0, "B", {"1": "CHG", "2": "VBUS", "3": "CHGLED"}, "C15127"),
    ("R30", *R0805, "100k", 43.5, 17.0, 90, "B", two("VBUS", "CHG"), "C17407"),
    ("R31", *R0805, "1k", 46.5, 17.0, 90, "B", two("CHGLED", "CHGA"), "C17513"),
    ("D30", *SOT23, "BAT54C", 50.0, 17.0, 0, "B", {"1": "CHGA", "2": "LEDR_A", "3": "LED_R"}, "C134405"),
    # SPEC v4: the charge light only with the Pocket OFF. Q31's gate sits on
    # the 3.3 V rail: switched on, it shunts CHGA to ground (5 mA from USB,
    # never from the battery); switched off the rail is 0 V (TPS63001 load
    # disconnect, Teensy VUSB-VIN cut) and the red lights while charging.
    ("Q31", *SOT23, "AO3400A", 46.5, 20.6, 0, "B", {"1": "VCC", "2": "GND", "3": "CHGA"}, "C20917"),
    ("R32", *R0805, "270", 40.0, 23.5, 0, "B", two("LED_R_DRV", "LEDR_A"), "C17590"),
    ("R33", *R0805, "330", 45.0, 23.5, 0, "B", two("LED_G_DRV", "LED_G"), "C17630"),
    # --- battery divider, headphone detect ---
    ("R40", *R0805, "1M", 51.0, 7.4, 0, "B", two("BAT", "VBAT_S"), "C17514"),
    ("R41", *R0805, "1M", 55.0, 7.4, 0, "B", two("VBAT_S", "GND"), "C17514"),
    ("C40", *C0805, "100nF", 59.0, 7.4, 0, "B", two("VBAT_S", "GND"), "C49678"),
    ("R42", *R0805, "100k", 38.0, 7.4, 0, "B", two("HP_TIPSW", "HP_DET"), "C17407"),
    ("R43", *R0805, "1M", 42.0, 7.4, 0, "B", two("HP_DET", "GND"), "C17514"),
    ("C41", *C0805, "100nF", 46.0, 7.4, 0, "B", two("HP_DET", "GND"), "C49678"),
    # --- speaker amplifier PAM8302A on VSYS ---
    ("U62", "Package_SO", "MSOP-8_3x3mm_P0.65mm", "PAM8302AASCR", 36.0, 34.0, 0, "B",
     {"1": "AMP_SD", "3": "INP", "4": "INN", "5": "SPK_P", "6": "VSYS", "7": "GND", "8": "SPK_N"}, "C113367"),
    ("C67", *C0805, "10uF", 33.5, 37.8, 0, "B", two("VSYS", "GND"), "C15850"),
    ("C68", *C0805, "1uF", 37.7, 37.8, 0, "B", two("VSYS", "GND"), "C28323"),
    ("R44", *R0805, "100k", 43.2, 34.0, 90, "B", two("AMP_SD", "GND"), "C17407"),
    ("R45", *R0805, "68k", 31.0, 43.2, 0, "B", two("HP_L", "AMP_P"), "C17801"),
    ("R46", *R0805, "68k", 34.4, 43.2, 0, "B", two("HP_R", "AMP_P"), "C17801"),
    ("R47", *R0805, "33k", 37.8, 43.2, 0, "B", two("HP_VGND", "AMP_N"), ""),
    ("C42", *C0805, "100nF", 31.0, 40.6, 0, "B", two("AMP_P", "INP"), "C49678"),
    ("C43", *C0805, "100nF", 37.6, 40.6, 0, "B", two("AMP_N", "INN"), "C49678"),
    # --- sensor groups: EN_A = SENS_EN & !S3, EN_B = SENS_EN & S3 ---
    ("U53", *SOT235, "74LVC1G04", 47.4, 32.2, 0, "B", {"2": "SEL3", "3": "GND", "4": "NS3", "5": "VCC"}, "C7827"),
    ("U54", *SOT235, "74LVC1G08", 53.4, 32.2, 0, "B", {"1": "NS3", "2": "SENS_EN", "3": "GND", "4": "EN_A", "5": "VCC"}, "C7666"),
    ("U55", *SOT235, "74LVC1G08", 59.4, 32.2, 0, "B", {"1": "SEL3", "2": "SENS_EN", "3": "GND", "4": "EN_B", "5": "VCC"}, "C7666"),
    ("C55", *C0805, "100nF", 56.4, 36.4, 0, "B", two("VCC", "GND"), "C49678"),
    # --- connectors (top) ---
    ("J_BAT", "Connector_JST", "JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", "battery 3-wire (+, NTC, -)", 12.6, 32.0, 270, "T",
     {"1": "BAT", "2": "TS", "3": "GND"}, "C131339"),
    ("J_SPK", "Connector_JST", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "speaker", 15.6, 23.5, 0, "T",
     {"1": "SPK_P", "2": "SPK_N"}, "C131337"),
    ("J_PNL", "Connector_JST", "JST_SH_BM08B-SRSS-TB_1x08-1MP_P1.00mm_Vertical", "panel board", 17.7, 33.0, 90, "T",
     {"1": "VBUS", "2": "VBUS", "3": "GND", "4": "GND", "5": "HP_L", "6": "HP_R", "7": "HP_VGND", "8": "HP_TIPSW"}, "C160394"),
    ("J_CTL", "Connector_JST", "JST_SH_BM10B-SRSS-TB_1x10-1MP_P1.00mm_Vertical", "controls board", 57.0, 42.8, 180, "T",
     {"1": "VCC", "2": "POT", "3": "GND", "4": "PWR_A", "5": "PWR_B", "6": "ENC_A", "7": "ENC_B", "8": "ENC_SW",
      "9": "LED_R", "10": "LED_G"}, "C160396"),
    ("J_HP", "Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical", "wires from the Audio Board's jack", 41.5, 43.3, 90, "T",
     {"1": "HP_L", "2": "HP_R", "3": "HP_VGND"}, ""),
]
# heights above the board's top for the case check (mated plug included)
TOP_HEIGHT = {"J_BAT": 10.5, "J_SPK": 10.5, "J_PNL": 6.0, "J_CTL": 6.0, "J_HP": 3.0}


def place_part(ref, libname, fp, value, x, y, rot, side, nets):
    f = B.place(B.lib(libname), fp, ref, x, y, value, back=(side == "B"), rot=rot)
    for p in f.Pads():
        n = nets.get(p.GetNumber())
        if n:
            p.SetNet(B.net(n))
    if side == "B":
        f.Reference().SetVisible(False)
    return f


ITEM_NET = {}                   # router item -> net, for the job list


STUB_END = {}
STUB_SEGS = []
FANOUT = {"U60": 2.0, "U61": 2.0}   # fine-pitch ICs -> lateral spread factor
EP_PADS = {"U60": "17", "U61": "11"}
GND_TO_EP = {"U60": ("4", "5", "8"), "U61": ("3", "7", "9")}   # ground pins tied straight to the exposed pad


def fanout(fp, spread):
    """Escape tracks from a fine-pitch package: the grid router can't end
    on 0.5 / 0.65 mm pitch pads (its clearance halo covers them), so every
    used pin gets a short straight stub that fans out to >= 1 mm spacing,
    and the stub's end is the router's target for that pin."""
    cx, cy = B.xy(fp.GetPosition())
    layer = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
    ep = EP_PADS.get(fp.GetReference())
    if ep:          # thermal / ground vias in the exposed pad: the router reaches it from the other side
        e = B.pad(fp, ep)
        ex, ey = B.xy(e.GetPosition())
        h = pcbnew.ToMM(e.GetBoundingBox().GetHeight())
        spots = [(ex, ey)] if h < 2.0 else [(ex, ey - 0.8), (ex, ey + 0.8)]
        for vx, vy in spots:
            B.add_via(vx, vy, e.GetNetname(), item=(fp.GetReference(), ep))
    for p in fp.Pads():
        n = p.GetNetname()
        if not n or p.GetNumber() == EP_PADS.get(fp.GetReference()):
            continue
        px, py = B.xy(p.GetPosition())
        if p.GetNumber() in GND_TO_EP.get(fp.GetReference(), ()):
            e = B.pad(fp, EP_PADS[fp.GetReference()])
            ebb = e.GetBoundingBox()
            ehx, ehy = pcbnew.ToMM(ebb.GetWidth()) / 2, pcbnew.ToMM(ebb.GetHeight()) / 2
            # 0.2 mm wide, nudged 0.05 towards the package's middle: the
            # corner pins sit 0.25 from the next side's pin
            if abs(px - cx) >= abs(py - cy):
                ly = py - math.copysign(0.05, py - cy)
                a, end = (px, ly), (cx + math.copysign(ehx - 0.15, px - cx), ly)
            else:
                lx = px - math.copysign(0.05, px - cx)
                a, end = (lx, py), (lx, cy + math.copysign(ehy - 0.15, py - cy))
            B.add_track([a, end], layer, n, 0.2)
            continue
        dx, dy = px - cx, py - cy
        bb = p.GetBoundingBox()
        w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        if abs(dx) >= abs(dy):
            o, l, t, tip = (math.copysign(1, dx), 0), (0, 1), dy, abs(dx) + w / 2
        else:
            o, l, t, tip = (0, math.copysign(1, dy)), (1, 0), dx, abs(dy) + h / 2
        at = lambda d, lat: (round(cx + o[0] * d + l[0] * lat, 4), round(cy + o[1] * d + l[1] * lat, 4))
        p1, p2 = at(tip + 0.15, t), at(tip + 1.25, t * spread)
        p3 = at(tip + 1.65, t * spread)
        B.add_track([(px, py), p1, p2], layer, n, 0.25)
        B.add_track([p2, p3], layer, n, 0.4, item=(fp.GetReference(), p.GetNumber()))
        STUB_SEGS.append((p2, p3, n))
        STUB_END[(fp.GetReference(), p.GetNumber())] = p3
        ITEM_NET[(fp.GetReference(), p.GetNumber())] = n


def lanes(fp, direction, depth=2.0, layer_index=0):
    """In front of a fine row of connector pins (top layer), block the
    router except one straight lane per pin, so tracks leave square instead
    of hugging the row and walling the next pin in."""
    R = B.router
    pads_ = [p for p in fp.Pads() if p.GetNumber() != "MP"]
    boxes = []
    for p in pads_:
        bb = p.GetBoundingBox()
        boxes.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
    if direction in ("+x", "-x"):
        x0 = max(b[2] for b in boxes) if direction == "+x" else min(b[0] for b in boxes) - depth
        x1, y0, y1 = x0 + depth, min(b[1] for b in boxes) - 0.6, max(b[3] for b in boxes) + 0.6
        mids, coord = [(b[1] + b[3]) / 2 for b in boxes], 1
    else:
        y0 = max(b[3] for b in boxes) if direction == "+y" else min(b[1] for b in boxes) - depth
        y1, x0, x1 = y0 + depth, min(b[0] for b in boxes) - 0.6, max(b[2] for b in boxes) + 0.6
        mids, coord = [(b[0] + b[2]) / 2 for b in boxes], 0
    for ix, iy, cx, cy in R._area(x0, y0, x1, y1, 0):
        if x0 <= cx < x1 and y0 <= cy < y1:
            if not any(abs((cx, cy)[coord] - m) < 0.14 for m in mids):
                R.owner[layer_index][iy * R.W + ix] = B.HARD
                R.novia[iy * R.W + ix] = 1


def register(fps):
    """Pads on the router grid; repeated pad numbers (MP, shell) get their
    own item keys so the router connects each one."""
    seen = {}
    for fp in fps:
        for p in fp.Pads():
            key = None
            if p.GetNetname() and not (fp.GetReference() in FANOUT and p.GetNumber() != EP_PADS.get(fp.GetReference())):
                k = (fp.GetReference(), p.GetNumber())
                seen[k] = seen.get(k, 0) + 1
                key = k if seen[k] == 1 else (fp.GetReference(), "%s#%d" % (p.GetNumber(), seen[k]))
                ITEM_NET[key] = p.GetNetname()
            B.register_pad(p, key)


def fp_box(fp, courtyard=True):
    xs, ys = [], []
    layers = ("F.CrtYd", "B.CrtYd") if courtyard else ("F.Fab", "B.Fab")
    for g in fp.GraphicalItems():
        if g.GetLayerName() in layers:
            bb = g.GetBoundingBox()
            xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
            ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    if not xs:
        bb = fp.GetBoundingBox(False)
        return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
    return (min(xs), min(ys), max(xs), max(ys))


def build():
    B.board = pcbnew.BOARD()
    B.nets.clear()
    B.via_spots.clear()
    B.pending_tracks.clear()
    B.POWER_NETS = POWER
    # 0.3 mm power / 0.25 mm signal tracks (the Pocket's currents are < 1 A):
    # a smaller clearance halo lets tracks pass between the Teensy's header
    # pins (the grid is aligned on them) and reach 0.65 mm pitch pads
    B.POWER_W, B.HW_MAX, B.SLACK = 0.3, 0.15, 0.04
    board = B.board
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(G.PCB_THICKNESS))
    # 4 layers: In1 = GND plane, In2 = 3.3 V plane; the router uses the outer two
    board.SetCopperLayerCount(4)
    ks = G.keys()
    pins = G.stack_pins()
    anchor = [(p[3], p[4]) for p in pins if p[0] == "J1" and p[1] == 1][0]
    B.router = B.Router(G.PCB_W, G.PCB_H, anchor)
    R = B.router
    R.mark_edges(G.OUTLINE)
    # no vias where the case's pillars touch the board's back
    for sx, sy, sr in G.SUPPORTS:
        rr = sr + B.VIA_D / 2 + 0.1
        for ix, iy, cx, cy in R._area(sx, sy, sx, sy, rr):
            if math.hypot(cx - sx, cy - sy) < rr:
                R.novia[iy * R.W + ix] = 1
    fps = []

    # ---- keys: switch (front), TMAG5253 + 100 nF (back) ----
    for k in ks:
        cx, cy = k["cx"], k["cy"]
        fps.append(B.place(B.LOCAL_LIB, "Gateron_Magnetic_MX_1u", k["ref"], cx, cy))
        u = B.place(B.lib("Package_SON"), "Texas_X2SON-4-1EP_1.1x1.4mm_P0.5mm_EP0.8x0.6mm", k["sensor"], cx, cy,
                    "TMAG5253BA3IQDMRR", back=True)
        u.Reference().SetVisible(False)
        out = "OUT_%s" % k["sensor"]
        for num, n in (("1", "VCC"), ("2", "GND"), ("3", k["en"]), ("4", out)):
            B.pad(u, num).SetNet(B.net(n))
        P = {n: B.xy(B.pad(u, n).GetPosition()) for n in "1234"}
        assert abs(P["1"][0] - cx - 0.25) < 0.01 and abs(P["1"][1] - cy + 0.775) < 0.01, P
        assert abs(P["3"][0] - cx + 0.25) < 0.01 and abs(P["3"][1] - cy - 0.775) < 0.01, P
        c = B.place(B.lib("Capacitor_SMD"), "C_0805_2012Metric", k["cap"], cx, cy + G.CAP_DY, "100nF", back=True)
        c.Reference().SetVisible(False)
        pa, pb = B.xy(B.pad(c, "1").GetPosition()), B.xy(B.pad(c, "2").GetPosition())
        left, right = ("1", "2") if pa[0] < pb[0] else ("2", "1")
        shift = (cx + 0.25) - min(pa[0], pb[0])
        c.SetPosition(B.mm(cx + shift, cy + G.CAP_DY))
        B.pad(c, left).SetNet(B.net("VCC"))
        B.pad(c, right).SetNet(B.net("GND"))
        gx = B.xy(B.pad(c, right).GetPosition())[0]
        k["gx"] = gx
        fps += [u, c]

    # ---- multiplexers (back, long side along y) ----
    for m, spec in enumerate(G.MUXES):
        u = B.place(B.lib("Package_SO"), "SOIC-24W_7.5x15.4mm_P1.27mm", spec["ref"], spec["x"], spec["y"],
                    "CD74HC4067M96", back=True, rot=spec["rot"])
        for number, func in G.MUX_PINS.items():
            name = None
            if func == "COM":
                name = "COM%d" % m
            elif func in ("S0", "S1", "S2", "S3"):
                name = "SEL%s" % func[1]
            elif func in ("GND", "E"):
                name = "GND"
            elif func == "VCC":
                name = "VCC"
            else:
                name = "FREE%d_%s" % (m, func[1:])
            B.pad(u, str(number)).SetNet(B.net(name))
        u.Reference().SetPosition(B.mm(spec["x"], spec["y"]))
        vx, vy = B.xy(B.pad(u, "24").GetPosition())
        sgn = 1 if vx > spec["x"] else -1
        c = B.place(B.lib("Capacitor_SMD"), "C_0805_2012Metric", "C7%d" % (m + 1), vx + sgn * 2.4,
                    vy + (1.3 if vy < spec["y"] else -1.3), "100nF", back=True, rot=90)
        c.Reference().SetVisible(False)
        d = lambda n: math.hypot(B.xy(B.pad(c, n).GetPosition())[0] - vx, B.xy(B.pad(c, n).GetPosition())[1] - vy)
        hi, lo = ("1", "2") if d("1") < d("2") else ("2", "1")
        B.pad(c, hi).SetNet(B.net("VCC"))
        B.pad(c, lo).SetNet(B.net("GND"))
        spec["fp"] = u
        fps += [u, c]

    # ---- the rest of the parts ----
    part_fp = {}
    for ref, libname, fp, value, x, y, rot, side, nets, _lcsc in PARTS:
        f = place_part(ref, libname, fp, value, x, y, rot, side, nets)
        part_fp[ref] = f
        fps.append(f)

    # ---- Teensy / Audio Board header holes (front) ----
    sockets = {}
    for ref in ("J1", "J2"):
        first = [p for p in pins if p[0] == ref and p[1] == 1][0]
        s = B.place(B.lib("Connector_PinSocket_2.54mm"), "PinSocket_1x14_P2.54mm_Vertical", ref, first[3], first[4], rot=90)
        s.Value().SetVisible(False)
        sockets[ref] = s
    for ref, number, pin, x, y in pins:
        p = B.pad(sockets[ref], str(number))
        got = B.xy(p.GetPosition())
        assert abs(got[0] - x) < 0.01 and abs(got[1] - y) < 0.01, (ref, number, got)
        n = G.PIN_NETS.get(pin)
        if n:
            p.SetNet(B.net(n))
    fps += list(sockets.values())

    for i, (x, y, keep) in enumerate(G.MOUNT, start=1):
        h = B.place(B.lib("MountingHole"), "MountingHole_2.2mm_M2", "H%d" % i, x, y)
        h.Reference().SetVisible(False)
        fps.append(h)
        R.mark_hole(x, y, 2 * keep)

    register(fps)
    for ref, spread in FANOUT.items():
        fanout(part_fp[ref], spread)
    lanes(part_fp["J_PNL"], "+x")
    lanes(part_fp["J_CTL"], "-y")

    # ---- checks: parts on the board, back parts off the pillars, top parts in the case's room ----
    problems = []
    for f in fps:
        x0, y0, x1, y1 = fp_box(f)
        if f.GetReference().startswith("SW"):
            continue
        for px in (x0, (x0 + x1) / 2, x1):
            for py in (y0, (y0 + y1) / 2, y1):
                if not G.point_in_poly((px, py), G.OUTLINE):
                    problems.append(("outside the board", f.GetReference(), round(px, 2), round(py, 2)))
        if f.IsFlipped():
            for sx, sy, sr in G.SUPPORTS:
                if math.hypot(max(x0 - sx, 0, sx - x1), max(y0 - sy, 0, sy - y1)) < sr:
                    problems.append(("on a pillar", f.GetReference(), (sx, sy)))
        ref = f.GetReference()
        if ref in TOP_HEIGHT:
            fx0, fy0, fx1, fy1 = fp_box(f, courtyard=False)
            zone = G.ENV["connector_zones"].get(ref)
            if zone:        # the design's own reservation for this connector
                zx0, zy0, zx1, zy1 = zone["rect"]
                if not (zx0 <= fx0 and fx1 <= zx1 and zy0 <= fy0 and fy1 <= zy1) or                         G.ENV["z_pcb_top"] + TOP_HEIGHT[ref] > zone["z_top_max"]:
                    problems.append(("outside its connector zone", ref, (fx0, fy0, fx1, fy1)))
                continue
            for px in (fx0, fx1):
                for py in (fy0, fy1):
                    if not G.room_at(TOP_HEIGHT[ref], (px, py)):
                        problems.append(("no room in the case", ref, round(px, 2), round(py, 2), TOP_HEIGHT[ref]))
            # the Teensy's micro-B plug (z 14.35-21.85) and the panel board (z 22.3)
            pr = G.ENV["stack"]["usb_plug"]["rect"]
            top_z = G.ENV["z_pcb_top"] + TOP_HEIGHT[ref]
            if top_z > G.ENV["stack"]["usb_plug"]["z"][0] and fx1 > pr[0][0] and fx0 < pr[1][0] and fy1 > pr[0][1] and fy0 < pr[2][1]:
                problems.append(("under the micro-B plug", ref))
    if problems:
        for p in problems:
            print("PLACEMENT:", p)
        raise SystemExit("placement problems: %d" % len(problems))

    # ---- fixed copper per key ----
    row_vcc, row_gnd, row_en = {}, {}, {}
    for k in ks:
        cx, cy, gx = k["cx"], k["cy"], k["gx"]
        out, en = "OUT_%s" % k["sensor"], k["en"]
        # 3.3 V and GND straight into the inner planes beside each sensor
        B.add_track([(cx + 0.25, cy - 0.775), (cx + 0.25, cy + G.VCC_VIA_DY)], pcbnew.B_Cu, "VCC", SENSOR_W)
        B.add_via(cx + 0.25, cy + G.VCC_VIA_DY, "VCC")
        B.add_track([(gx, cy + G.CAP_DY), (gx, cy + G.GND_VIA_DY)], pcbnew.B_Cu, "GND", LOCAL_W)
        B.add_via(gx, cy + G.GND_VIA_DY, "GND")
        B.add_track([(cx + 0.25, cy + 0.775), (cx + 0.25, cy + 1.5), (gx, cy + 1.5)], pcbnew.B_Cu, "GND", SENSOR_W)
        ov = (cx + G.OUT_VIA[0], cy + G.OUT_VIA[1])
        B.add_track([(cx - 0.25, cy - 0.775), (cx - 0.25, cy - 1.25), (cx - 0.25 - 0.45, cy - 1.7), ov], pcbnew.B_Cu, out, SENSOR_W)
        B.add_via(ov[0], ov[1], out, item=("via", k["sensor"]))
        ev = (cx + G.EN_VIA[0], cy + G.EN_VIA[1])
        B.add_track([(cx - 0.25, cy + 0.775), (cx - 0.25, cy + 1.25), (cx - 0.25 - 0.45, cy + 1.7), (ev[0], cy + 1.7), ev],
                    pcbnew.B_Cu, en, SENSOR_W)
        B.add_via(ev[0], ev[1], en)
        eb = (ev[0], cy + G.EN_BUS_DY)
        B.add_track([ev, eb], pcbnew.F_Cu, en, LOCAL_W)
        B.add_via(eb[0], eb[1], en)
        row_vcc.setdefault(k["row"], []).append(cx + 0.25)
        row_gnd.setdefault(k["row"], []).append(gx)
        row_en.setdefault(k["row"], []).append(ev[0])
        k["out_via"] = ov
    def via_room(x, y, net_name="GND"):
        nid = R.nid(net_name)
        for ix, iy, cx, cy in R._area(x, y, x, y, 0.75):
            if math.hypot(cx - x, cy - y) > 0.75:
                continue
            for li in (0, 1):
                o = R.owner[li][iy * R.W + ix]
                if o not in (B.FREE, nid):
                    return False
        ix, iy = R.cell(x, y)
        return not R.novia[iy * R.W + ix]

    row_y = {k["row"]: k["cy"] for k in ks}
    for r, cy in row_y.items():
        en = G.GROUP_EN[G.ROW_GROUP[r]]
        B.add_track(sorted((x, cy + G.EN_BUS_DY) for x in row_en[r]), pcbnew.B_Cu, en, 0.4, item=("enbus", r))

    # ---- jobs ----
    B.ROOTS.clear()          # 3.3 V and GND are planes: nothing routed for them

    fixed = {k["sensor"] for k in ks} | {k["cap"] for k in ks}

    def items_of(net_name):
        return sorted(i for i, n in ITEM_NET.items() if n == net_name and i[0] not in fixed)

    def dist(a, b):
        ca = next(iter(R.items[a]))[1]
        cb = next(iter(R.items[b]))[1]
        return math.hypot((ca % R.W - cb % R.W) * B.PITCH, (ca // R.W - cb // R.W) * B.PITCH)

    jobs = []
    first_item = {}
    net_names = sorted({p.GetNetname() for f in fps for p in f.Pads() if p.GetNetname()})
    for n in net_names:
        if n.startswith("OUT_") or n.startswith("FREE") or n in ("VCC", "GND"):
            continue
        its = items_of(n)
        buses = [("enbus", r) for r in row_y if G.GROUP_EN[G.ROW_GROUP[r]] == n] if n in ("EN_A", "EN_B") else []
        its += buses
        if n in B.ROOTS:
            root = B.ROOTS[n]
            its = [i for i in its if i != root]
            its.sort(key=lambda i: dist(i, root))
            for i in its:
                jobs.append((n, i, "tree", "%s %s" % (n, i)))
            continue
        if len(its) < 2:
            print("single-item net", n, its)
            continue
        # every item joins the tree grown from the first one (any order works)
        R.tree[n] = set(R.items[its[0]])
        first_item[n] = its[0]
        done = [its[0]]
        rest = its[1:]
        while rest:
            nxt = min(rest, key=lambda i: min(dist(i, d) for d in done))
            rest.remove(nxt)
            jobs.append((n, nxt, "tree", "%s %s" % (n, nxt)))
            done.append(nxt)
    # sensor outputs: to any free channel of the right half of their multiplexer
    free = {(m, g): set(range(8 * g, 8 * g + 8)) for m in range(2) for g in range(2)}
    outs = sorted(ks, key=lambda k: -(abs(k["out_via"][0] - G.MUXES[k["mux"]]["x"]) + abs(k["out_via"][1] - G.MUXES[k["mux"]]["y"])))
    for k in outs:
        jobs.append(("OUT_%s" % k["sensor"], ("via", k["sensor"]), ("mux", k), "%s -> %s" % (k["sensor"], G.MUXES[k["mux"]]["ref"])))

    first = [n for n in os.environ.get("POCKET_ROUTE_FIRST", DEFAULT_ROUTE_FIRST).split(",") if n]
    order = {"GND": 0, "VCC": 1}
    # jobs touching a fine-pitch IC's fan-out go first, shortest first: once
    # other routes pass in front of the stub ends there is no way in
    near_ic = lambda j: j[1][0] in FANOUT or first_item.get(j[0], ("",))[0] in FANOUT or         (isinstance(j[2], list) and any(t[0] in FANOUT for t in j[2]))
    def jlen(j):
        if isinstance(j[2], list):
            return dist(j[1], j[2][0])
        if j[0] in first_item:
            return dist(j[1], first_item[j[0]])
        return 0.0
    # order: the fine-pitch fan-outs, then every other connection shortest
    # first (local links before the long ones that would fence them in),
    # the 28 sensor outputs, and ground last (the pours take what is left)
    def est(j):
        if j[0].startswith("OUT_"):
            return 0.0
        if j[0] in B.ROOTS:
            return dist(j[1], B.ROOTS[j[0]])
        return min(dist(j[1], o) for o in [first_item[j[0]]] + [i for i in items_of(j[0]) if i != j[1] and i in R.items][:6])             if j[0] in first_item else jlen(j)
    tier = lambda j: -1 if near_ic(j) else 3 if j[0].startswith("OUT_") else 1
    out_first = [n for n in os.environ.get("POCKET_OUT_FIRST", DEFAULT_OUT_FIRST).split(",") if n]
    jobs.sort(key=lambda j: (tier(j) == 3, j[0] not in first, first.index(j[0]) if j[0] in first else 0, tier(j),
                             j[0] not in out_first, out_first.index(j[0]) if j[0] in out_first else 0, est(j)))
    # every 3.3 V / GND pad drops into its plane through a via beside it
    stitched, unstitched = 0, []
    for fp in fps:
        ref = fp.GetReference()
        if ref in fixed or ref.startswith("SW"):
            continue
        for pad_ in fp.Pads():
            n = pad_.GetNetname()
            if n not in ("VCC", "GND") or pad_.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                continue
            num = pad_.GetNumber()
            if num == EP_PADS.get(ref) or (ref in FANOUT and num in GND_TO_EP.get(ref, ())):
                continue
            layer = pcbnew.F_Cu if pad_.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            px, py = B.xy(pad_.GetPosition())
            if (ref, num) in STUB_END:
                sx, sy = STUB_END[(ref, num)]
                cands, start = [(sx, sy)], (sx, sy)
                cands += [(sx + dx, sy + dy) for dx, dy in ((0.8, 0), (-0.8, 0), (0, 0.8), (0, -0.8))]
            else:
                fx, fy = B.xy(fp.GetPosition())
                bb = pad_.GetBoundingBox()
                hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
                out = (px - fx, py - fy)
                if len(list(fp.Pads())) > 2:            # along the pad's long side, away from the part
                    out = (math.copysign(1, out[0]), 0) if hw > hh else (0, math.copysign(1, out[1]))
                elif abs(out[0]) >= abs(out[1]):
                    out = (math.copysign(1, out[0]), 0)
                else:
                    out = (0, math.copysign(1, out[1]))
                L = math.hypot(*out) or 1.0
                ux, uy = out[0] / L, out[1] / L
                cands = []
                for dx, dy in ((ux, uy), (uy, -ux), (-uy, ux), (-ux, -uy)):
                    for extra in (0.55, 0.9, 1.3):
                        ext = abs(dx) * hw + abs(dy) * hh + extra
                        cands.append((px + dx * ext, py + dy * ext))
                start = (px, py)
            for vx, vy in cands:
                if via_room(vx, vy, n):
                    if (vx, vy) != start:
                        B.add_track([start, (vx, vy)], layer, n, 0.3)
                    B.add_via(vx, vy, n)
                    stitched += 1
                    break
            else:
                unstitched.append((ref, num, n))
    print("pads into the planes:", stitched, "routed to the nearest same-net copper instead:", unstitched)
    for ref, num, n in unstitched:
        jobs.insert(0, (n, (ref, num), "copper", "%s %s.%s -> nearest %s copper" % (n, ref, num, n)))

    for net_name, src, dst, label in jobs:
        if dst == "copper":
            B.connect(net_name, src, set(R.copper[net_name]) - R.items[src], label)
            print("routed", label)
            continue
        if dst == "tree":
            targets = R.tree.get(net_name, set()) - R.items[src]
        elif dst[0] == "mux":
            k = dst[1]
            m, g = k["mux"], k["group"]
            mref = G.MUXES[m]["ref"]
            targets = set()
            for ch in free[(m, g)]:
                targets |= R.items[(mref, str(G_channel_pin(ch)))]
            path = B.connect(net_name, src, targets, label, extra=["FREE%d_%d" % (m, c) for c in free[(m, g)]])
            last = (path[-1][0], path[-1][1])
            ch = [c for c in free[(m, g)] if last in R.items[(mref, str(G_channel_pin(c)))]][0]
            free[(m, g)].discard(ch)
            k["ch"] = ch
            p = B.pad(B.board.FindFootprintByReference(mref), str(G_channel_pin(ch)))
            p.SetNet(B.net(net_name))
            B.register_pad(p, (mref, str(G_channel_pin(ch))))
            print("routed", label, "I%d" % ch)
            continue
        else:
            targets = set()
            for it in dst:
                targets |= R.items[it]
        if not targets:
            raise SystemExit("no target for %s" % label)
        B.connect(net_name, src, targets, label)
        if net_name not in B.ROOTS:
            R.tree[net_name] |= R.items[src]
        if dst != "tree" and net_name not in B.ROOTS:
            for it in dst:
                R.tree[net_name] |= R.items[it]
        print("routed", label)

    # a route may join a fan-out stub before its end: cut the tip back to
    # where the route meets it (or drop it)
    def same(u, v, tol=0.01):
        return math.hypot(u[0] - v[0], u[1] - v[1]) < tol
    for p2, p3, n in STUB_SEGS:
        tips = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == n
                and ((same(B.xy(t.GetStart()), p2) and same(B.xy(t.GetEnd()), p3)) or
                     (same(B.xy(t.GetStart()), p3) and same(B.xy(t.GetEnd()), p2)))]
        if not tips:
            continue
        tip = tips[0]
        tid = tip.m_Uuid.AsString()
        others = [t for t in board.GetTracks() if t.m_Uuid.AsString() != tid and t.GetNetname() == n]
        if any(t.GetClass() == "PCB_VIA" and same(B.xy(t.GetPosition()), p3, 0.05) for t in others) or \
                any(t.GetClass() == "PCB_TRACK" and (same(B.xy(t.GetStart()), p3, 0.05) or same(B.xy(t.GetEnd()), p3, 0.05)) for t in others):
            continue
        dx, dy = p3[0] - p2[0], p3[1] - p2[1]
        L2 = dx * dx + dy * dy
        far = None                  # furthest point along the tip where another track / via of the net lands
        for t in others:
            pts = [B.xy(t.GetPosition())] if t.GetClass() == "PCB_VIA" else [B.xy(t.GetStart()), B.xy(t.GetEnd())]
            for q in pts:
                u = ((q[0] - p2[0]) * dx + (q[1] - p2[1]) * dy) / L2
                if u <= 0.02:
                    continue
                uc = min(u, 1.0)
                if math.hypot(q[0] - p2[0] - uc * dx, q[1] - p2[1] - uc * dy) < 0.3:
                    far = max(far or 0.0, uc)
        if far is None:
            board.Remove(tip)
        elif far < 0.999:
            cut = B.mm(p2[0] + far * dx, p2[1] + far * dy)
            tip.SetEnd(cut) if same(B.xy(tip.GetEnd()), p3) else tip.SetStart(cut)

    for m, spec in enumerate(G.MUXES):
        for g in (0, 1):
            for ch in free[(m, g)]:
                B.pad(spec["fp"], str(G_channel_pin(ch))).SetNetCode(0)

    # ---- planes: In1 GND, In2 3.3 V, whole board ----
    for layer, pn in ((pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "VCC")):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(B.net(pn))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((0, 0), (G.PCB_W, 0), (G.PCB_W, G.PCB_H), (0, G.PCB_H)):
            ol.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)

    # ---- outline, labels ----
    pts = G.OUTLINE + G.OUTLINE[:1]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(B.mm(x1, y1))
        seg.SetEnd(B.mm(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)
    B.text("eTuttino Pocket v0.2", 150.0, 88.0, 1.2)
    B.text("eTuttino Pocket v0.2 - TMAG5253 on this side", 128.5, 88.0, 1.0, pcbnew.B_SilkS)
    for f in fps:
        f.Reference().SetVisible(False)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcbnew.SaveBoard(BOARD_PATH, board)
    print("saved", BOARD_PATH)
    os.makedirs(G.BUILD, exist_ok=True)
    G.write_csv(ks, os.path.join(G.BUILD, "pocket_keys.csv"))
    with open(HEADER_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(G.key_header(ks))
    print("wrote", HEADER_PATH)
    return ks


def G_channel_pin(ch):
    return [p for p, f in G.MUX_PINS.items() if f == "I%d" % ch][0]


BOM_EXTRA = [
    ("TMAG5253BA3IQDMRR (CONSIGNED / global sourcing: not stocked at LCSC)", lambda ks: [k["sensor"] for k in ks], "X2SON-4 1.1x1.4", ""),
    ("100nF 0805 X7R", lambda ks: [k["cap"] for k in ks] + ["C71", "C72"], "C_0805", "C49678"),
    ("CD74HC4067M96", lambda ks: ["U51", "U52"], "SOIC-24W", "C98457"),
]


def fab():
    gdir = os.path.join(FAB_DIR, "gerbers")
    os.makedirs(gdir, exist_ok=True)
    for name in os.listdir(gdir):
        os.remove(os.path.join(gdir, name))
    drc = os.path.join(FAB_DIR, "pocket_drc.json")
    B.cli("pcb", "drc", "--format", "json", "--severity-all", "--output", drc, BOARD_PATH)
    rep = json.load(open(drc, encoding="utf-8"))
    vio = rep.get("violations", [])
    errors = [v for v in vio if v.get("severity") == "error"]
    unc = rep.get("unconnected_items", [])
    print("DRC: %d errors, %d warnings, %d unconnected" % (len(errors), len(vio) - len(errors), len(unc)))
    for v in vio[:40]:
        print("  [%s] %s" % (v.get("severity"), v.get("description")), [(i.get("description"), i.get("pos")) for i in v.get("items", [])[:2]])
    for u in unc[:20]:
        print("  [unconnected]", [i.get("description") for i in u.get("items", [])])
    B.cli("pcb", "export", "gerbers", "--output", gdir + os.sep,
          "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", BOARD_PATH)
    B.cli("pcb", "export", "drill", "--output", gdir + os.sep, "--format", "excellon", "--excellon-separate-th", BOARD_PATH)
    for side in ("back", "front"):
        cpl = os.path.join(FAB_DIR, "pocket_cpl_%s.csv" % ("bottom" if side == "back" else "top"))
        B.cli("pcb", "export", "pos", "--side", side, "--format", "csv", "--units", "mm", "--smd-only", "--output", cpl, BOARD_PATH)
        jlc.cpl(cpl)
    ks = G.keys()
    lines = list(BOM_EXTRA)
    groups = {}
    for ref, libname, fp, value, x, y, rot, side, nets, lcsc in PARTS:
        if libname.startswith("Connector_PinHeader"):
            continue
        key = (value, fp, lcsc)
        groups.setdefault(key, []).append(ref)
    with open(os.path.join(FAB_DIR, "pocket_bom.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("Comment,Designator,Footprint,LCSC Part #\n")
        for comment, refs, footprint, lcsc in lines:
            f.write('"%s","%s","%s","%s"\n' % (comment, ",".join(refs(ks)), footprint, lcsc))
        for (value, fp, lcsc), refs in groups.items():
            f.write('"%s","%s","%s","%s"\n' % (value, ",".join(refs), fp, lcsc))
    z = os.path.join(FAB_DIR, "pocket_gerbers.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(os.listdir(gdir)):
            zf.write(os.path.join(gdir, name), name)
    print("wrote", z)
    for side in ("top", "bottom"):
        try:
            B.cli("pcb", "render", "--side", side, "--width", "1800", "--height", "900",
                  "--output", os.path.join(FAB_DIR, "pocket_%s.png" % side), BOARD_PATH)
        except subprocess.CalledProcessError:
            print("render failed for", side)
    return len(errors), len(vio) - len(errors), len(unc)


def verify():
    """Board x firmware contract: every sensor's output reaches the channel
    pocket_keys.h says, in the channel half its EN group is switched on with;
    COM / address / LED / control lines reach the pins PINOS.md names."""
    b = pcbnew.LoadBoard(BOARD_PATH)
    hdr = open(HEADER_PATH, encoding="utf-8").read()

    def ints(pat):
        return [int(v) for v in re.findall(r"-?\d+", re.search(pat, hdr, re.S).group(1))]
    table = ints(r"POCKET_KEY_INPUT\[POCKET_LAYOUT_ROWS\]\[POCKET_LAYOUT_COLS\] = \{(.*?)\};")
    sel = ints(r"POCKET_MUX_SEL_PINS\[4\] = \{([^}]*)\}")
    com = ints(r"POCKET_MUX_COM_PINS\[2\] = \{([^}]*)\}")
    led = ints(r"POCKET_LED_PINS\[2\] = \{([^}]*)\}")
    first = ints(r"POCKET_FIRST_NOTE\[POCKET_LAYOUT_ROWS\] = \{([^}]*)\}")
    fcol = ints(r"POCKET_FIRST_COL\[POCKET_LAYOUT_ROWS\] = \{([^}]*)\}")
    pin_of = {}
    for ref, side in (("J1", G.TEENSY_LEFT), ("J2", G.TEENSY_RIGHT)):
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNetname():
                pin_of.setdefault(p.GetNetname(), []).append(side[int(p.GetNumber()) - 1])
    bad = 0

    def want(net_name, pin):
        nonlocal bad
        if str(pin) not in pin_of.get(net_name, []):
            bad += 1
            print("  MISMATCH %s: board pins %s, contract %s" % (net_name, pin_of.get(net_name), pin))
    for s in range(4):
        want("SEL%d" % s, sel[s])
    for m in range(2):
        want("COM%d" % m, com[m])
    want("LED_R_DRV", led[0])
    want("LED_G_DRV", led[1])
    for n, pin in (("SENS_EN", 4), ("KEEP", 10), ("AMP_SD", 12), ("VBAT_S", 16), ("HP_DET", 17), ("POT", 22),
                   ("ENC_A", 11), ("ENC_B", 9), ("ENC_SW", 6)):
        want(n, pin)
    chan = {p: int(f[1:]) for p, f in G.MUX_PINS.items() if f.startswith("I")}
    muxfp = [b.FindFootprintByReference(s["ref"]) for s in G.MUXES]
    for m, fp in enumerate(muxfp):
        if [p.GetNetname() for p in fp.Pads() if p.GetNumber() == "13"][0] != "SEL3":
            bad += 1
            print("  MISMATCH S3 of", G.MUXES[m]["ref"])
    n_ok = 0
    for k in G.keys():
        s = b.FindFootprintByReference(k["sensor"])
        out = [p.GetNetname() for p in s.Pads() if p.GetNumber() == "4"][0]
        en = [p.GetNetname() for p in s.Pads() if p.GetNumber() == "3"][0]
        found = [(m, chan[int(p.GetNumber())]) for m, fp in enumerate(muxfp) for p in fp.Pads()
                 if p.GetNetname() == out and p.GetNumber().isdigit() and int(p.GetNumber()) in chan]
        fw = table[(k["row"] - 1) * G.GRID_COLS + k["col"]]
        note = first[k["row"] - 1] + 3 * (k["col"] - fcol[k["row"] - 1])
        ok = len(found) == 1 and fw == found[0][0] * 16 + found[0][1] and note == k["note"]
        ok = ok and en == G.GROUP_EN[found[0][1] // 8]
        if ok:
            n_ok += 1
        else:
            bad += 1
            print("  MISMATCH", k["ref"], "board", found, en, "header", fw, "note", note, k["note"])
    print("board x firmware: %d/28 keys reach the channel pocket_keys.h reads (EN group matching), %d mismatches" % (n_ok, bad))
    return bad


def sync_pinos():
    """Copy POCKET_KEY_INPUT from pocket_keys.h into PINOS.md's ```c block
    (the contract shows the table the board was checked against)."""
    pinos = os.path.join(HERE, "PINOS.md")
    hdr = open(HEADER_PATH, encoding="utf-8").read()
    table = hdr[hdr.index("const int8_t POCKET_KEY_INPUT"):].strip()
    s = open(pinos, encoding="utf-8").read()
    a = s.index("```c", s.index("## Tabela de teclas"))
    b = s.index("```", a + 4)
    s = s[:a] + "```c\n" + table + "\n" + s[b:]
    with open(pinos, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("PINOS.md: KEY_INPUT block updated")


def route_with_retries(max_attempts=16):
    """Greedy router: a net routed early can wall off a later one. On a
    failure start again in a fresh process with that net first -- among
    the other connections, or among the sensor outputs (which always come
    after everything else)."""
    first = [n for n in os.environ.get("POCKET_ROUTE_FIRST", DEFAULT_ROUTE_FIRST).split(",") if n]
    outs = [n for n in os.environ.get("POCKET_OUT_FIRST", DEFAULT_OUT_FIRST).split(",") if n]
    for attempt in range(max_attempts):
        env = dict(os.environ, POCKET_ROUTE_FIRST=",".join(first), POCKET_OUT_FIRST=",".join(outs), POCKET_CHILD="1")
        r = subprocess.run([sys.executable, os.path.abspath(__file__)], env=env, capture_output=True, text=True)
        sys.stdout.write(r.stdout[-5000:])
        sys.stdout.write(r.stderr[-3000:])
        failed = [l.split("(")[-1].rstrip(")") for l in r.stdout.splitlines() if l.startswith("ROUTING FAILED")]
        if r.returncode == 0 or not failed:
            print("attempt %d: exit %d, route-first: %s / outputs: %s" % (attempt + 1, r.returncode, ",".join(first) or "-", ",".join(outs) or "-"))
            return r.returncode
        f = failed[0]
        print("attempt %d: %s failed, retrying with it first" % (attempt + 1, f))
        if f.startswith("OUT_"):
            outs = [f] + [n for n in outs if n != f]
        else:
            first = [f] + [n for n in first if n != f]
    return 1


if __name__ == "__main__" and not os.environ.get("POCKET_CHILD"):
    sys.exit(route_with_retries())

if __name__ == "__main__":
    try:
        build()
    except B.RoutingFailed:
        pcbnew.SaveBoard(os.path.join(KICAD_DIR, "pocket_failed.kicad_pcb"), B.board)
        sys.exit(3)
    e, w, u = fab()
    bad = verify()
    if not bad:
        sync_pinos()
    sys.exit(1 if e or w or u or bad else 0)
