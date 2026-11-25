"""Stage 2a of the ruler routing: the REGULAR part of the copper, drawn by script (KiCad python, idempotent).

    "C:/Program Files/KiCad/10.0/bin/python.exe" fixa.py   -> rota/kicad/fixo.kicad_pcb

Reads rota/kicad/base/slim_regua.kicad_pcb (no part moved). Draws what repeats on every sensor and the long lanes, so the grid router (rota_grade.py) only has the head
(J1, U9, C9, C10) left to solve. Why: a greedy router that routes the 8 EN lanes and the two buses together fills the 2.4 mm of free height under the sensors in the
wrong order (measured, see ROTEAMENTO.md); with the lane order fixed by hand every net fits.

Per sensor k (x_k = 41.25 + 18.5 (k-1); pads: 1 +3V3 (x-0.7, 34.05), 2 GND (x+0.7, 34.05), 3 EN (x+0.7, 34.55), 4 OUT (x-0.7, 34.55), 5 GND (x, 34.3)):
  B.Cu  +3V3 : bus at y 33.11 (0.2 wide), tee down to the cap's pad 1 (x-1.52), cap pad 1 -> sensor pad 1
  B.Cu  OUT  : bus at y 35.30, stub up to pad 4
  B.Cu  EN   : pad 3 -> 0.7 mm to the right -> via (x+1.4, 34.55) -> F.Cu stub down to the lane
  B.Cu  GND  : pad 2 -> via (x+1.4, 33.75), pad 5 (thermal pad) -> via (x, 33.65): both into the F.Cu pour
F.Cu EN lanes, 0.15 wide at 0.30 pitch (gap 0.15), band y 35.05 .. 37.15; the lane of EN_j is at y = 35.05 + 0.30 (j - k) when it passes sensor k, one step up after
each sensor (45 degree jog between sensors); lane start x = 36.5 for the head.
Head fan-out of EN2..EN8 (the pads on U9's bottom and right side): vias in a staircase (0.5 / 0.65 mm) so the B.Cu stubs of the pads to the left pass the vias of the pads
to the right at 0.5 mm; F.Cu straight down to the lane row and east. EN1 (U9 pin 15, top row): B.Cu east to a via at (32.5, 28.84), F.Cu down x = 32.5.
The router then gets: DATA, CLK, LATCH, OUT (J1.3 -> the OUT bus start), +3V3 (J1.2, C9, C10, U9.10, U9.16 -> the +3V3 bus start).
"""
import os
import json as _j, os as _o
TAILG = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "..", "..", "case", "envelope_regua.json"), encoding="utf-8"))["regua"]["cauda_g"]   # R10SL: tail growth (the head parts keep their place relative to the keys)

import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
M = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
W, WL = 0.2, 0.15
VDIA, VDR = 0.5, 0.3
Y3, YO = 33.11, 35.30
LANE0, LANEP = 35.05, 0.30
XL = 36.5 + TAILG                      # lane start
SRC = os.path.join(HERE, "kicad", "base", "slim_regua.kicad_pcb")
DST = os.path.join(HERE, "kicad", "fixo.kicad_pcb")
b = pcbnew.LoadBoard(SRC)
keep = []


def tr(net, pts, layer=pcbnew.B_Cu, w=W):
    for a, e in zip(pts, pts[1:]):
        if a == e:
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(*a)); t.SetEnd(V(*e)); t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net))
        b.Add(t); keep.append(t)


def via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetNet(b.FindNet(net)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(M(VDIA)); v.SetDrill(M(VDR))
    b.Add(v); keep.append(v)


def lane_y(k, j):
    return round(LANE0 + LANEP * (j - k), 3)


F, B = pcbnew.F_Cu, pcbnew.B_Cu
xs = [41.25 + TAILG + 18.5 * (k - 1) for k in range(1, 9)]
for k in range(1, 9):
    x = xs[k - 1]
    # 3V3
    tr("+3V3", [(x - 1.52, Y3), (x - 1.52, 34.05), (x - 0.7, 34.05)])
    # OUT
    tr("OUT", [(x - 0.7, 34.55), (x - 0.7, YO)])
    # EN drop
    en = "EN%d" % k
    tr(en, [(x + 0.7, 34.55), (x + 1.4, 34.55)])
    via(en, x + 1.4, 34.55)
    tr(en, [(x + 1.4, 34.55), (x + 1.4, lane_y(k, k))], F, WL)
    # GND
    tr("GND", [(x + 0.7, 34.05), (x + 1.4, 33.75)])
    via("GND", x + 1.4, 33.75)
    tr("GND", [(x, 34.3), (x, 33.65)])
    via("GND", x, 33.65)
# buses
tr("+3V3", [(36.0 + TAILG, Y3), (xs[7] - 1.52, Y3)])
tr("OUT", [(36.0 + TAILG, YO), (xs[7] - 0.7, YO)])
# lanes: EN_j passes sensors 1 .. j-1; its end is the stub of sensor j
def jog(pts, x, k, j):
    """lane j climbs one step (0.30) before sensor k; the jogs of lane j are at x - 4.6 + 0.5 j, so adjacent lanes never run their 45-degree pieces side by side."""
    jx = x - 4.6 + 0.5 * j
    pts.append((jx, lane_y(k - 1, j)))
    pts.append((jx + LANEP, lane_y(k, j)))


for j in range(2, 9):
    pts = [(XL, lane_y(1, j))]
    for k in range(2, j + 1):
        jog(pts, xs[k - 1], k, j)
    pts.append((xs[j - 1] + 1.4, lane_y(j, j)))
    tr("EN%d" % j, pts, F, WL)
# head: EN3..EN8 staircase on U9's bottom row, EN2 on the right pin, EN1 on the top row
pad = {}
for fp in b.GetFootprints():
    if fp.GetReference() == "U9":
        for p in fp.Pads():
            pad[p.GetNumber()] = (pcbnew.ToMM(p.GetX()), pcbnew.ToMM(p.GetY()))
stair = {3: 32.20, 4: 32.85, 5: 33.50, 6: 34.15, 7: 34.80, 8: 35.45}
for j, vy in stair.items():
    px, py = pad[str(j - 1)]            # EN3 = pin 2 ... EN8 = pin 7
    en = "EN%d" % j
    tr(en, [(px, py), (px, vy)])
    via(en, px, vy)
    ly = lane_y(1, j)
    tr(en, [(px, vy), (px, ly), (XL, ly)], F, WL)
# EN2
px, py = pad["1"]
tr("EN2", [(px, py), (31.7 + TAILG, py)])
via("EN2", 31.7 + TAILG, py)
tr("EN2", [(31.7 + TAILG, py), (31.7 + TAILG, lane_y(1, 2)), (XL, lane_y(1, 2))], F, WL)
# EN1
px, py = pad["15"]
tr("EN1", [(px, py), (32.5 + TAILG, py)])
via("EN1", 32.5 + TAILG, py)
tr("EN1", [(32.5 + TAILG, py), (32.5 + TAILG, lane_y(1, 1)), (xs[0] + 1.4, lane_y(1, 1))], F, WL)
# J1 GND pads 7 and 8 (the two on the top of the connector, 0.5 mm pitch): one via east of them, reserved before the router runs (otherwise the other head nets wall them in)
jp = {}
for fp in b.GetFootprints():
    if fp.GetReference() == "J1":
        for p in fp.Pads():
            jp[p.GetNumber()] = (pcbnew.ToMM(p.GetX()), pcbnew.ToMM(p.GetY()))
tr("GND", [jp["8"], (24.7, 28.65)])
tr("GND", [jp["7"], (24.7, 28.65)])
via("GND", 24.7, 28.65)
pcbnew.SaveBoard(DST, b)
print("fixo.kicad_pcb escrito")
