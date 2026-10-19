"""The eTuttino Pocket's two small boards (KiCad's Python):

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/pocket/pcb/build_small_boards.py

  controls  under the interface lid (case envelope "controls"): EC11E
            encoder, 3 mm R/G LED, JST SH 10-way header on top at its right
            edge (cable to the main board's J_CTL), 5 joint pads on its back
            at the left edge for the pot board.
  pot       the volume pot's board, standing VERTICAL right of the shaft
            (x 21.62-23.22, y 43-55, z 13.8-29.8): Alps RK097 horizontal-type
            pot with switch on its left face, its shaft up through the lid,
            5 joint pads on its right face, 1.0-1.3 mm above the controls
            board's back face, soldered across the 90 degree corner.
            Frame: X = y - 43, Y = 29.8 - z (seen from the pot's side, F face
            towards -x: the SPEC frame is left-handed, so the player (+y) is on
            the RIGHT. v0.1 had X = 55 - y, a mirrored board: the joint's GND
            pad landed on a pad without a net -- fixed in v0.2, SPEC v4 F2).
  (panel    the v4 USB-C + jack board: REMOVED in SPEC v5 -- micro-B panel
            extension cable + wired panel jack instead; in git history.)

Each board: DRC (errors, warnings, unconnected) and Gerbers in fab/.
Exits non-zero unless both are 0/0/0.
"""
import json
import math
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.normpath(os.path.join(HERE, "..", "..")))

import pcbnew  # noqa: E402

import build_pcb as B  # noqa: E402
import pocket_geom as G  # noqa: E402

KICAD_DIR = os.path.join(HERE, "kicad")
FAB_DIR = os.path.join(HERE, "fab")
CT = G.ENV["controls"]
# The SH-10 cable to the main board's J_CTL (crimped there, its far end cut
# and soldered): wires 1-5 to the pot board (the pot and its switch), wires
# 6-10 to the controls board's right edge (encoder and LED). The controls
# board takes its GND through the 90 degree joint from the pot board; the
# other joint pads are only solder for strength.
CTL_NETS = {1: "VCC", 2: "POT", 3: "GND", 4: "PWR_A", 5: "PWR_B", 6: "ENC_A", 7: "ENC_B", 8: "ENC_SW",
            9: "LED_R", 10: "LED_G"}
# joint pads, by the controls board's y (the pot board's X = y - 43); clear
# of the encoder's left lug (y 47.4-50.6)
JOINT = {44.0: None, 45.2: None, 46.4: "GND", 51.6: None, 52.8: None, 54.0: None}
TAB_BACK, TAB_FRONT = 40.0, 57.5
JOINT_Y = 14.8          # pot board: z 15.0, just under the controls board's back face (z 15.58)


def reset(thickness=1.6):
    B.board = pcbnew.BOARD()
    B.nets.clear()
    B.via_spots.clear()
    B.ROOTS.clear()
    B.POWER_NETS = {"VCC", "GND", "VBUS"}
    # small boards, few nets, little current: 0.3 mm power / 0.25 mm signal
    # tracks, so the router's clearance halo can be smaller too
    B.POWER_W, B.HW_MAX, B.SLACK = 0.3, 0.15, 0.04
    B.board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(thickness))
    return B.board


def clean(fp):
    """Footprints that draw their own board cut-outs (the jack, the pot)
    would break the outline: drop those; hide reference texts."""
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == pcbnew.Edge_Cuts:
            fp.Remove(g)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    return fp


def place_at(libname, name, ref, value, target, rot, back=False, ref_pad=None):
    """Footprint placed so its Fab circle centre (shaft / LED body) -- or
    the given pad, or the middle of its pads -- lands on target."""
    fp = B.place(B.lib(libname), name, ref, 0, 0, value, back=back, rot=rot)
    pt = None
    if ref_pad:
        pt = B.xy(B.pad(fp, ref_pad).GetPosition())
    else:
        for g in fp.GraphicalItems():
            if hasattr(g, "GetShape") and g.GetShape() == pcbnew.SHAPE_T_CIRCLE and "Fab" in g.GetLayerName():
                pt = B.xy(g.GetCenter())
                break
    if pt is None:
        ps = [B.xy(p.GetPosition()) for p in fp.Pads()]
        pt = (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))
    fp.SetPosition(B.mm(target[0] - pt[0], target[1] - pt[1]))
    return clean(fp)


def smd_pad(ref, x, y, w, h, net_name, back=False):
    """A lone SMD pad (wire / joint pad) as a one-pad footprint."""
    fp = pcbnew.FOOTPRINT(B.board)
    fp.SetReference(ref)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    p = pcbnew.PAD(fp)
    p.SetNumber("1")
    p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetSize(B.mm(w, h))
    p.SetLayerSet(pcbnew.PAD.SMDMask())
    fp.Add(p)
    fp.SetPosition(B.mm(x, y))
    B.board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    if net_name:
        p.SetNet(B.net(net_name))
    return fp


def outline(pts):
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(B.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(B.mm(ax, ay))
        s.SetEnd(B.mm(bx, by))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        B.board.Add(s)


def strip_silk(fps, x0, y0, x1, y1):
    for fp in fps:
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and hasattr(g, "GetShape"):
                bb = g.GetBoundingBox()
                gx0, gy0, gx1, gy1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
                if gx0 < x0 + 0.2 or gy0 < y0 + 0.2 or gx1 > x1 - 0.2 or gy1 > y1 - 0.2:
                    fp.Remove(g)


ORDER = {"controls": ["LED_R"]}


def drop_one_sided_vias():
    """A via the router dropped as an item but that only one layer's
    copper ever reached: remove it (DRC warns about it)."""
    def ends(t):
        return [B.xy(t.GetStart()), B.xy(t.GetEnd())]
    tracks = [t for t in B.board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    for v in [t for t in B.board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        vx, vy = B.xy(v.GetPosition())
        layers = {t.GetLayer() for t in tracks if t.GetNetname() == v.GetNetname()
                  and any(math.hypot(px - vx, py - vy) < 0.05 for px, py in ends(t))}
        if len(layers) < 2:
            B.board.Remove(v)


def tight_courtyard(fp, margin):
    """Replace a footprint's courtyard by the box round its pads and Fab body."""
    xs, ys = [], []
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            fp.Remove(g)
        elif g.GetLayer() == pcbnew.F_Fab:
            bb = g.GetBoundingBox()
            xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
            ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
        ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
    x0, y0, x1, y1 = min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(B.mm(*a))
        s.SetEnd(B.mm(*b))
        s.SetLayer(pcbnew.F_CrtYd)
        s.SetWidth(pcbnew.FromMM(0.05))
        fp.Add(s)


def lanes(R, pads_, side, depth=1.6):
    """In front of a tight row of wire pads, block the top layer except one
    lane per pad, so routes come in square instead of hugging the row."""
    boxes = []
    for p in [q for fp in pads_ for q in fp.Pads()]:
        bb = p.GetBoundingBox()
        boxes.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
    if side == "left":
        x0 = min(b[0] for b in boxes) - depth
        x1 = min(b[0] for b in boxes)
        y0, y1 = min(b[1] for b in boxes) - 0.6, max(b[3] for b in boxes) + 0.6
        mids = [(b[1] + b[3]) / 2 for b in boxes]
        for ix, iy, cx, cy in R._area(x0, y0, x1, y1, 0):
            if x0 <= cx < x1 and y0 <= cy <= y1:
                R.novia[iy * R.W + ix] = 1
                if not any(abs(cy - m) < 0.14 for m in mids):
                    R.owner[0][iy * R.W + ix] = B.HARD
                    R.owner[1][iy * R.W + ix] = B.HARD


def route_all(fps, w, h, anchor, poly, jobs_first=(), pre=None):
    B.router = B.Router(w, h, anchor)
    B.router.mark_edges(poly)
    item_net = {}
    for fp in fps:
        seen = {}
        for p in fp.Pads():
            key = None
            if p.GetNetname():
                k = (fp.GetReference(), p.GetNumber())
                seen[k] = seen.get(k, 0) + 1
                key = k if seen[k] == 1 else (fp.GetReference(), "%s#%d" % (p.GetNumber(), seen[k]))
                item_net[key] = p.GetNetname()
            B.register_pad(p, key)
    jobs_first = list(jobs_first)
    if pre:
        pre(B.router)
    nets = sorted(set(item_net.values()), key=lambda n: (n not in jobs_first, jobs_first.index(n) if n in jobs_first else 0, n))
    R = B.router
    for n in nets:
        its = sorted(i for i, nn in item_net.items() if nn == n)
        if len(its) < 2:
            continue
        R.tree[n] = set(R.items[its[0]])
        for i in its[1:]:
            targets = R.tree[n] - R.items[i]
            B.connect(n, i, targets, "%s %s" % (n, i))
            R.tree[n] |= R.items[i]
            print("routed", n, i)


def drc_and_gerbers(path, name):
    out = os.path.join(FAB_DIR, "%s_gerbers" % name)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    drc = os.path.join(FAB_DIR, "%s_drc.json" % name)
    B.cli("pcb", "drc", "--format", "json", "--severity-all", "--output", drc, path)
    rep = json.load(open(drc, encoding="utf-8"))
    vio = rep.get("violations", [])
    err = [v for v in vio if v.get("severity") == "error"]
    unc = rep.get("unconnected_items", [])
    print("%s DRC: %d errors, %d warnings, %d unconnected" % (name, len(err), len(vio) - len(err), len(unc)))
    for v in vio[:20]:
        print("  [%s] %s" % (v.get("severity"), v.get("description")), [(i.get("description"), i.get("pos")) for i in v.get("items", [])[:2]])
    for u in unc[:10]:
        print("  [unconnected]", [i.get("description") for i in u.get("items", [])])
    B.cli("pcb", "export", "gerbers", "--output", out + os.sep,
          "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", path)
    B.cli("pcb", "export", "drill", "--output", out + os.sep, "--format", "excellon", "--excellon-separate-th", path)
    z = os.path.join(FAB_DIR, "%s_gerbers.zip" % name)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in sorted(os.listdir(out)):
            f.write(os.path.join(out, n), n)
    for side in ("top", "bottom"):
        try:
            B.cli("pcb", "render", "--side", side, "--width", "1000", "--height", "700",
                  "--output", os.path.join(FAB_DIR, "%s_%s.png" % (name, side)), path)
        except subprocess.CalledProcessError:
            print("render failed", name, side)
    return len(err), len(vio) - len(err), len(unc)


# ---------------------------------------------------------------- controls
def controls():
    reset()
    x0, y0, x1, y1 = CT["rect"]
    fps = []
    sw = place_at("Rotary_Encoder", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm", "SW1", "EC11E 15/15", CT["encoder"], 270)
    for p in sw.Pads():
        if p.GetNumber() != "MP":
            p.SetNet(B.net({"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "GND", "S2": "ENC_SW"}[p.GetNumber()]))
    abc = [B.xy(p.GetPosition())[1] for p in sw.Pads() if p.GetNumber() in "ABC"]
    assert max(abc) < CT["encoder"][1], "encoder A/B/C must face the back"
    d1 = place_at("LED_THT", "LED_D3.0mm-3", "D1", "LED 3mm R/G CC", CT["led"], 0)   # legs along x: lanes past the posts
    for p in d1.Pads():
        p.SetNet(B.net({"1": "LED_R", "2": "GND", "3": "LED_G"}[p.GetNumber()]))
    # 10 wire pads for the SH-10 cable (its far end on the main board's J_CTL):
    # a BM10B header with its two lugs needs 12.8 + 1.0 mm along y, the board has 13.5
    fps += [sw, d1]
    for y, n in JOINT.items():
        fps.append(smd_pad("JP%d" % len(fps), x0 + 1.15, y, 1.3, 1.0, n, back=True))
    for i, k in enumerate(range(6, 11)):         # cable wires 6-10, right edge, top
        fps.append(smd_pad("JW%d" % k, x1 - 1.3, 45.1 + 1.9 * i, 1.4, 1.0, CTL_NETS[k]))
    for i, (hx, hy) in enumerate(CT["holes"], start=1):
        h = clean(B.place(B.lib("MountingHole"), "MountingHole_2.2mm_M2", "H%d" % i, hx, hy))
        for g in list(h.GraphicalItems()):     # the lid post (5) clears the encoder and LED; its courtyard is wider
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                h.Remove(g)
        fps.append(h)
    # the EC11E's legs need 17 mm along y (A/B/C 7.5 behind the shaft, the
    # switch 7 in front): two tabs past the envelope's rectangle (CHECK with
    # the design: over the Audio Board at the back, towards the speaker box in front)
    ex0, ex1 = CT["encoder"][0] - 4.1, CT["encoder"][0] + 4.1
    poly = [(x0, y0), (ex0, y0), (ex0, TAB_BACK), (ex1, TAB_BACK), (ex1, y0), (x1, y0),
            (x1, y1), (ex1, y1), (ex1, TAB_FRONT), (ex0, TAB_FRONT), (ex0, y1), (x0, y1)]
    route_all(fps, x1 + 1, TAB_FRONT + 1, (x0, TAB_BACK), poly, ORDER.get("controls", ()))
    outline(poly)
    B.text("CTL v0.2", 45.0, 43.6, 0.8, pcbnew.B_SilkS)
    strip_silk(fps, x0, y0, x1, y1)
    path = os.path.join(KICAD_DIR, "pocket_controls.kicad_pcb")
    pcbnew.SaveBoard(path, B.board)
    return path


# ---------------------------------------------------------------- pot board
def pot():
    reset()
    pb = CT["pot"]
    W = pb["board"][3] - pb["board"][1]               # 12 (y extent)
    H = pb["board_z"][1] - pb["board_z"][0]           # 16 (z extent)
    ymin, ztop = pb["board"][1], pb["board_z"][1]
    # seen from the pot's side (looking +x) the player (+y) is on the right:
    # KiCad X grows with y (the SPEC frame is left-handed)
    X = lambda y: y - ymin
    Y = lambda z: ztop - z
    shaft_X, shoulder_Y = X(pb["shaft"][1]), Y(pb["body_z"][1])
    # RK097 horizontal-with-switch footprint: shaft along -x, body front 5 mm
    # in front of pins 1-3, shaft axis on pin 2. Rot 270: -x -> up (-Y).
    rv = B.place(B.lib("Potentiometer_THT"), "Potentiometer_Alps_RK097_Single_Horizontal_Switch", "RV1", 0, 0,
                 "RK097 A10k + SPST", rot=270)
    p2 = B.xy(B.pad(rv, "2").GetPosition())
    rv.SetPosition(B.mm(shaft_X - p2[0], shoulder_Y + 5.0 - p2[1]))
    clean(rv)
    for p in rv.Pads():
        p.SetNet(B.net({"1": "GND", "2": "POT", "3": "VCC", "4": "PWR_A", "5": "PWR_B"}[p.GetNumber()]))
    got = {p.GetNumber(): B.xy(p.GetPosition()) for p in rv.Pads()}
    assert abs(got["2"][0] - shaft_X) < 0.01 and got["4"][1] > got["1"][1], got
    fps = [rv]
    for yj, n in JOINT.items():
        fps.append(smd_pad("JP%d" % len(fps), X(yj), JOINT_Y, 1.0, 1.0, n, back=True))
    # cable wires 1-5 (back face, top, above the encoder's top), each over the pin it feeds
    for k, Xw in ((5, 1.2), (1, 3.4), (2, 5.6), (3, 7.8), (4, 10.0)):
        fps.append(smd_pad("JW%d" % k, Xw, 1.2, 1.0, 1.2, CTL_NETS[k], back=True))
    poly = [(0, 0), (W, 0), (W, H), (0, H)]
    route_all(fps, W + 1, H + 1, (0, 0), poly, ("GND", "VCC"))
    outline(poly)
    B.text("VOL v0.2", W / 2, 1.2, 0.8)
    strip_silk(fps, 0, 0, W, H)
    path = os.path.join(KICAD_DIR, "pocket_pot.kicad_pcb")
    pcbnew.SaveBoard(path, B.board)
    return path, {k: (round(v[0], 2), round(v[1], 2)) for k, v in got.items()}


if __name__ == "__main__":
    os.makedirs(KICAD_DIR, exist_ok=True)
    os.makedirs(FAB_DIR, exist_ok=True)
    which = sys.argv[1:] or ["controls", "pot"]
    res = {}
    for name in which:
        for attempt in range(40):
            try:
                if name == "controls":
                    path = controls()
                elif name == "pot":
                    path, pads = pot()
                    print("pot board pads (X, Y):", pads)
                else:
                    raise SystemExit("unknown board %s (the panel board was removed in SPEC v5)" % name)
                break
            except B.RoutingFailed as e:
                failed = e.args[0]
                pcbnew.SaveBoard(os.path.join(KICAD_DIR, "pocket_%s_failed.kicad_pcb" % name), B.board)
                order = ORDER.setdefault(name, [])
                if failed in order:
                    order.remove(failed)
                order.insert(0, failed)
                print("attempt %d: %s failed, now first: %s" % (attempt + 1, failed, order))
        else:
            res[name] = ("routing failed",)
            continue
        print(name, "route order", ORDER.get(name))
        res[name] = drc_and_gerbers(path, "pocket_" + name)
    print(res)
    sys.exit(0 if all(v == (0, 0, 0) for v in res.values()) else 1)
