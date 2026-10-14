"""The eTuttino's controls board (case SPEC v8): volume pot, instrument
encoder and power LED, hung under the interface lid on two posts, wired
to the main board's J3 by an 8-way JST PH cable.

    "C:/Program Files/KiCad/10.0/bin/python.exe" controls_pcb.py

Writes kicad/etuttino_controls.kicad_pcb, fab/etuttino_controls_gerbers.zip,
fab/etuttino_controls_drc.json and fab/etuttino_controls_top.png /
_bottom.png. Exits non-zero on a DRC error or anything unconnected.

Geometry from case/out/pcb_envelope.json ("controls"): board rectangle,
the two M2 holes over the lid's posts, the pot / encoder shafts and the LED
in SPEC coordinates (x from the case's left face, y towards the player),
which is this board's top view: its top faces the lid, the parts stand on
it and their shafts go up through the lid.

  RV1  Alps RK09K vertical pot, 6 mm shaft L = 15      volume
  SW1  Alps EC11E encoder with push switch, L = 15     instrument
  D1   3 mm red/green LED, common cathode, on a spacer
  J1   JST PH B8B-PH-K (vertical) on the back, facing down: the cable
       drops straight to the main board's J3 below.
       1 VCC  2 GND  3 POT  4 ENC_A  5 ENC_B  6 ENC_SW  7 LED_R  8 LED_G
       (pin for pin as the main board's J3)
The encoder's common (C) and one switch leg (S1) go to GND; the Teensy's
pull-ups do the rest. The LED's resistors are on the main board.
"""
import json
import math
import os
import subprocess
import sys
import zipfile

import pcbnew

import build_pcb as B
import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(B.KICAD_DIR, "etuttino_controls.kicad_pcb")
CT = G.ENV["controls"]

NETS_JST = {1: "VCC", 2: "GND", 3: "POT", 4: "ENC_A", 5: "ENC_B", 6: "ENC_SW", 7: "LED_R", 8: "LED_G"}


def place_at(lib, name, ref, value, target, rot, back=False):
    """Places a footprint (rotated by rot, on the back if asked) so that its
    reference point lands on `target`: the centre of its Fab-layer circle
    (the shaft of the pot / encoder, the LED's body), else the middle of its
    pads (the connector)."""
    fp = B.place(B.lib(lib), name, ref, 0, 0, value, back=back, rot=rot)

    def ref_point():
        for g in fp.GraphicalItems():
            if hasattr(g, "GetShape") and g.GetShape() == pcbnew.SHAPE_T_CIRCLE and "Fab" in g.GetLayerName():
                return B.xy(g.GetCenter())
        ps = [B.xy(p.GetPosition()) for p in fp.Pads()]
        return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))
    cx, cy = ref_point()
    fp.SetPosition(B.mm(target[0] - cx, target[1] - cy))
    return fp


def build():
    B.board = pcbnew.BOARD()
    B.nets.clear()
    B.via_spots.clear()
    B.ROOTS.clear()
    board = B.board
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
    x0, y0, x1, y1 = CT["rect"]
    outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    B.router = B.Router(x1 + 1, y1 + 1, (x0, y0))
    B.router.mark_edges(outline)

    fps = []
    rv = place_at("Potentiometer_THT", "Potentiometer_Alps_RK09K_Single_Vertical", "RV1", "RK09K 10k lin",
                  CT["pot"], CT["pot_rot"])
    for p in rv.Pads():
        if p.GetNumber() in ("1", "2", "3"):    # the mounting lugs (MP) stay unconnected
            p.SetNet(B.net({"1": "GND", "2": "POT", "3": "VCC"}[p.GetNumber()]))
    sw = place_at("Rotary_Encoder", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm", "SW1", "EC11E",
                  CT["encoder"], CT["encoder_rot"])
    for p in sw.Pads():
        if p.GetNumber() != "MP":
            p.SetNet(B.net({"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "GND", "S2": "ENC_SW"}[p.GetNumber()]))
    d1 = place_at("LED_THT", "LED_D3.0mm-3", "D1", "LED 3mm R/G CC", CT["led"], 0)
    for p in d1.Pads():
        p.SetNet(B.net({"1": "LED_R", "2": "GND", "3": "LED_G"}[p.GetNumber()]))
    j1 = place_at("Connector_JST", "JST_PH_B8B-PH-K_1x08_P2.00mm_Vertical", "J1", "to main board J3",
                  CT["jst"], CT["jst_rot"], back=True)
    for p in j1.Pads():
        p.SetNet(B.net(NETS_JST[int(p.GetNumber())]))
    fps += [rv, sw, d1, j1]
    for i, (hx, hy) in enumerate(CT["holes"], start=1):
        h = B.place(B.lib("MountingHole"), "MountingHole_2.2mm_M2", "H%d" % i, hx, hy)
        h.Reference().SetVisible(False)
        fps.append(h)
    for fp in fps:
        fp.Value().SetVisible(False)
        for p in fp.Pads():
            B.register_pad(p, (fp.GetReference(), p.GetNumber()) if p.GetNetname() else None)

    jobs = []
    for n in ("POT", "ENC_A", "ENC_B", "ENC_SW", "LED_R", "LED_G", "VCC"):
        jp = [k for k, v in NETS_JST.items() if v == n][0]
        dst = [(fp.GetReference(), p.GetNumber()) for fp in (rv, sw, d1) for p in fp.Pads() if p.GetNetname() == n]
        jobs.append((n, ("J1", str(jp)), dst[:1], "J1.%d -> %s" % (jp, n)))
    gnd = [(fp.GetReference(), p.GetNumber()) for fp in (rv, sw, d1) for p in fp.Pads() if p.GetNetname() == "GND"]
    jobs.append(("GND", ("J1", "2"), gnd[:1], "J1.2 -> GND"))
    for it in gnd[1:]:
        jobs.append(("GND", it, "tree", "GND %s.%s" % it))
    for n, src, dst, label in jobs:
        if dst == "tree":
            targets = B.router.tree.get(n, set()) - B.router.items[src]
        else:
            targets = set()
            for it in dst:
                targets |= B.router.items[it]
        B.connect(n, src, targets, label)
        if dst != "tree":
            for it in dst:
                B.router.tree[n] |= B.router.items[it]
        print("routed", label)

    for (ax, ay), (bx, by) in zip(outline, outline[1:] + outline[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(B.mm(ax, ay))
        seg.SetEnd(B.mm(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)
    B.text("eTuttino controls v0.7", (x0 + x1) / 2, y1 - 1.4, 0.9)
    B.text("VOL", CT["pot"][0], CT["pot"][1] + 11.0, 0.8)
    B.text("SOUND", CT["encoder"][0] + 10.0, CT["encoder"][1] + 11.0, 0.8)
    # silkscreen that would hang over the board's edge (the pot's outline)
    for fp in fps:
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and hasattr(g, "GetShape"):
                bb = g.GetBoundingBox()
                gx0, gy0, gx1, gy1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
                if gx0 < x0 + 0.2 or gy0 < y0 + 0.2 or gx1 > x1 - 0.2 or gy1 > y1 - 0.2:
                    fp.Remove(g)
    pcbnew.SaveBoard(PATH, board)
    print("saved", PATH)


def fab():
    out = os.path.join(B.FAB_DIR, "controls_gerbers")
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):
        os.remove(os.path.join(out, name))
    drc = os.path.join(B.FAB_DIR, "etuttino_controls_drc.json")
    B.cli("pcb", "drc", "--format", "json", "--severity-all", "--output", drc, PATH)
    rep = json.load(open(drc, encoding="utf-8"))
    vio = rep.get("violations", [])
    errors = [v for v in vio if v.get("severity") == "error"]
    unc = rep.get("unconnected_items", [])
    print("DRC: %d errors, %d warnings, %d unconnected" % (len(errors), len(vio) - len(errors), len(unc)))
    for v in vio[:20]:
        print("  [%s] %s" % (v.get("severity"), v.get("description")), [i.get("description") for i in v.get("items", [])[:2]])
    B.cli("pcb", "export", "gerbers", "--output", out + os.sep,
          "--layers", "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", PATH)
    B.cli("pcb", "export", "drill", "--output", out + os.sep, "--format", "excellon", "--excellon-separate-th", PATH)
    z = os.path.join(B.FAB_DIR, "etuttino_controls_gerbers.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for name in sorted(os.listdir(out)):
            f.write(os.path.join(out, name), name)
    print("wrote", z)
    for side in ("top", "bottom"):
        try:
            B.cli("pcb", "render", "--side", side, "--width", "1200", "--height", "700",
                  "--output", os.path.join(B.FAB_DIR, "etuttino_controls_%s.png" % side), PATH)
        except subprocess.CalledProcessError:
            print("render failed for", side)
    return len(errors), len(unc)


if __name__ == "__main__":
    try:
        build()
    except B.RoutingFailed:
        pcbnew.SaveBoard(os.path.join(B.KICAD_DIR, "etuttino_controls_failed.kicad_pcb"), B.board)
        sys.exit(3)
    e, u = fab()
    sys.exit(1 if e or u else 0)
