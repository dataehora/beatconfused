"""eTutti Viaggio MicroMod -- the USB pair, routed by hand-computed coordinates (SPEC v2.3).

The one exception to "Code does not route" (J, 25 Oct 2026): only USB_DP and USB_DN. No router and
no path search: every segment below is written out from the pads of J201 (USB-C, top), U201
(USBLC6-2SC6, top) and J101 (M.2 socket, bottom).

Run with KiCad's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/route_usb.py

It opens kicad/viaggio_micromod.kicad_pcb, removes the USB tracks/vias it wrote before (their UUIDs
are in build/route_usb.json), adds the pair again (all locked), refills the zones, saves, runs
kicad-cli DRC with schematic parity and writes close-up pictures to build/. It exits non-zero if a
USB track or via it did not write is on the board, or if a check fails. Nothing else is touched.

Why the pair loops round U201 (read before "simplifying" it):
  * J201's pads run DN, DP, DN, DP from the top (B7 12.25, A6 12.75, A7 13.25, B6 13.75). On one
    layer the two DN pads and the two DP pads can only be joined one pair under the plug body (left
    of the pads) and the other pair to the right, and either way DN leaves J201 ABOVE DP.
  * U201 (rot 0) has DP on its top row (pads 1/6, y 11.3) and DN on the bottom row (pads 3/4).
  * The .kicad_dru allows USB tracks off F.Cu only inside J101's courtyard, so the pair cannot swap
    layers on the way to U201.
  So the pair runs under U201 to its right side, turns up and enters pads 6/4 from the right (the
  U-turn puts DP on top), crosses the chip on its own pads (6->1, 4->3: flow-through), leaves to the
  left, turns up and runs back above U201 to J101, where the vias and B.Cu stubs put DP on pad 3 and
  DN on pad 5. With U201 turned 180 deg the pair would run straight (see ELETRONICA.md).
"""
import json
import math
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "viaggio_micromod"
BOARD_PATH = os.path.join(HERE, "kicad", NAME + ".kicad_pcb")
BUILD = os.path.join(HERE, "build")
MANIFEST = os.path.join(BUILD, "route_usb.json")
DRC_OUT = os.path.join(BUILD, "route_usb_drc.json")
KICAD_BIN = os.path.dirname(sys.executable)
KICAD_CLI = os.path.join(KICAD_BIN, "kicad-cli.exe" if os.name == "nt" else "kicad-cli")

NETS = ("USB_DP", "USB_DN")
W = 0.24            # pair width on F.Cu over In1 GND (build/impedance.json: Zdiff 91 ohm)
GAP = 0.15          # pair gap
PITCH = W + GAP     # 0.39 centre to centre
W_IN = 0.20         # B.Cu stubs inside J101's courtyard (pads 0.3 at 0.5 pitch)
VIA_D, VIA_DRILL = 0.5, 0.3
MAX_LEN, MAX_SKEW, MAX_VIAS = 40.0, 2.0, 2

# ---- the expected pads (the script stops if the placement moved) ----------------------------------
EXPECT = {
    ("J201", "B7"): ("USB_DN", 8.745, 12.25), ("J201", "A6"): ("USB_DP", 8.745, 12.75),
    ("J201", "A7"): ("USB_DN", 8.745, 13.25), ("J201", "B6"): ("USB_DP", 8.745, 13.75),
    ("U201", "1"): ("USB_DP", 17.762, 11.30), ("U201", "6"): ("USB_DP", 20.038, 11.30),
    ("U201", "3"): ("USB_DN", 17.762, 13.20), ("U201", "4"): ("USB_DN", 20.038, 13.20),
    ("J101", "3"): ("USB_DP", 22.225, 9.25), ("J101", "5"): ("USB_DN", 22.225, 9.75),
}


def offset_polyline(pts, d):
    """Offset a polyline (0/45/90 deg segments) by d to its LEFT (y down: left of east is north),
    with mitred corners, so a pair keeps one gap through every 45 deg bend."""
    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        return dx / n, dy / n

    def left(u):
        return (u[1], -u[0])

    out = []
    for i, p in enumerate(pts):
        if i == 0:
            n = left(unit(pts[0], pts[1]))
            out.append((p[0] + d * n[0], p[1] + d * n[1]))
        elif i == len(pts) - 1:
            n = left(unit(pts[-2], pts[-1]))
            out.append((p[0] + d * n[0], p[1] + d * n[1]))
        else:
            n1, n2 = left(unit(pts[i - 1], p)), left(unit(p, pts[i + 1]))
            k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
            out.append((p[0] + d * (n1[0] + n2[0]) / k, p[1] + d * (n1[1] + n2[1]) / k))
    return [(round(x, 4), round(y, 4)) for x, y in out]


def geometry():
    """Every USB segment and via, in mm. Returns {net: [(layer, width, [points])]}, {net: [via]}."""
    h = PITCH / 2
    # 1. J201: DN pads joined under the plug body (left of the pad row), DP pads to the right.
    dn_join = [(8.745, 12.25), (7.95, 12.25), (7.75, 12.45), (7.75, 13.05), (7.95, 13.25), (8.745, 13.25)]
    dp_join = [(8.745, 13.75), (9.55, 13.75), (9.75, 13.55), (9.75, 12.95), (9.95, 12.75)]
    # 2. the pair from J201 under U201 (DN north): centreline, DN = left offset when heading east.
    c_in = [(10.10, 12.555), (10.60, 12.555), (12.09, 14.045), (19.388, 14.045)]
    dn_in, dp_in = offset_polyline(c_in, +h), offset_polyline(c_in, -h)
    dn_tail = [(8.745, 12.25), (9.99, 12.25), dn_in[0]]                 # B7 drops into the pair
    dp_head = [(8.745, 12.75), (9.95, 12.75), dp_in[0]]                 # A6 straight into the pair
    # the U-turn on U201's right (DP outer, x 21.6, leaves room for a VBUS via right of pad 5); DN
    # inner, one pitch inside, with the mitred inner chamfer of DP's 0.5 chamfer.
    dn_to4 = [dn_in[-1], (20.9385, 13.85), (21.21, 13.5785), (21.21, 13.41), (21.00, 13.20), (20.038, 13.20)]
    dp_to6 = [dp_in[-1], (21.10, 14.24), (21.60, 13.74), (21.60, 11.50), (21.40, 11.30), (20.038, 11.30)]
    # 3. across U201 on its own pads (flow-through): 6 -> 1 and 4 -> 3.
    dp_chip = [(20.038, 11.30), (17.762, 11.30)]
    dn_chip = [(20.038, 13.20), (17.762, 13.20)]
    # 4. out to the left, up, and back east above U201 (heading north DN is west = left offset).
    c_back = [(16.195, 11.10), (16.195, 10.245), (16.495, 9.945), (22.90, 9.945)]
    dn_back, dp_back = offset_polyline(c_back, +h), offset_polyline(c_back, -h)
    # DN's leg carries the length match (DP's U-turn on the right is the longer one): a loop west
    # to x 14.8 and back; the space it encloses left of pad 2 (GND) holds that pad's via.
    xw = 14.80
    dn_leg = [(17.762, 13.20), (xw + 0.2, 13.20), (xw, 13.00), (xw, 11.90), (xw + 0.2, 11.70),
              (15.60, 11.70), (16.00, 11.30), dn_back[0]]
    dp_leg = [(17.762, 11.30), (16.59, 11.30), dp_back[0]]
    # 5. into J101's courtyard, vias between its pin rows, B.Cu stubs into the pads' inner ends.
    v_dn, v_dp = (23.75, 9.75), (24.60, 9.70)
    dn_end = [dn_back[-1], v_dn]
    dp_end = [dp_back[-1], (23.11, 10.35), (23.95, 10.35), v_dp]
    dn_bot = [v_dn, (22.60, 9.75)]
    dp_bot = [v_dp, (24.15, 9.25), (22.60, 9.25)]
    F, B = "F.Cu", "B.Cu"
    tracks = {
        "USB_DN": [(F, W, dn_join), (F, W, dn_tail), (F, W, dn_in), (F, W, dn_to4), (F, W, dn_chip),
                   (F, W, dn_leg), (F, W, dn_back), (F, W, dn_end), (B, W_IN, dn_bot)],
        "USB_DP": [(F, W, dp_join), (F, W, dp_head), (F, W, dp_in), (F, W, dp_to6), (F, W, dp_chip),
                   (F, W, dp_leg), (F, W, dp_back), (F, W, dp_end), (B, W_IN, dp_bot)],
    }
    # the signal path J201 -> J101 (for the length match; the J201 join loops are stubs)
    path = {
        "USB_DN": [dn_tail, dn_in, dn_to4, dn_chip, dn_leg, dn_back, dn_end, dn_bot],
        "USB_DP": [dp_head, dp_in, dp_to6, dp_chip, dp_leg, dp_back, dp_end, dp_bot],
    }
    vias = {"USB_DN": [v_dn], "USB_DP": [v_dp]}
    return tracks, vias, path


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def check_angles(tracks):
    for net, items in tracks.items():
        for _layer, _w, pts in items:
            for a, b in zip(pts, pts[1:]):
                dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
                if dx > 1e-3 and dy > 1e-3 and abs(dx - dy) > 2e-3:
                    raise SystemExit("not a 0/45/90 segment on %s: %s -> %s" % (net, a, b))


def mm(v):
    return pcbnew.FromMM(v)


def pt(p):
    return pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))


def check_pads(b):
    for (ref, num), (net, x, y) in EXPECT.items():
        fp = b.FindFootprintByReference(ref)
        pads = [p for p in fp.Pads() if p.GetNumber() == num] if fp else []
        if not pads:
            raise SystemExit("%s pad %s missing" % (ref, num))
        p = pads[0]
        q = p.GetPosition()
        if p.GetNetname() != net or abs(pcbnew.ToMM(q.x) - x) > 0.01 or abs(pcbnew.ToMM(q.y) - y) > 0.01:
            raise SystemExit("%s pad %s is %s at (%.3f, %.3f), expected %s at (%.3f, %.3f): placement "
                             "changed, recompute the route" % (ref, num, p.GetNetname(), pcbnew.ToMM(q.x),
                                                                pcbnew.ToMM(q.y), net, x, y))


def remove_old(b):
    old = set()
    if os.path.exists(MANIFEST):
        old = set(json.load(open(MANIFEST, encoding="utf-8")).get("uuids", []))
    removed, foreign = 0, []
    for t in list(b.GetTracks()):
        if t.GetNetname() not in NETS:
            continue
        if t.m_Uuid.AsString() in old:
            b.Delete(t)
            removed += 1
        else:
            foreign.append(t)
    if foreign:
        raise SystemExit("%d USB track(s)/via(s) on the board that this script did not write: "
                         "left untouched, nothing saved" % len(foreign))
    return removed, old


def add(b, tracks, vias):
    nets = {n: b.FindNet(n) for n in NETS}
    uuids = []
    for net, items in tracks.items():
        for layer, w, pts in items:
            for a, c in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pt(a))
                t.SetEnd(pt(c))
                t.SetWidth(mm(w))
                t.SetLayer(b.GetLayerID(layer))
                t.SetNet(nets[net])
                t.SetLocked(True)
                b.Add(t)
                uuids.append(t.m_Uuid.AsString())
    for net, vs in vias.items():
        for p in vs:
            v = pcbnew.PCB_VIA(b)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetPosition(pt(p))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            try:
                v.SetWidth(mm(VIA_D))
            except TypeError:
                v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(nets[net])
            v.SetLocked(True)
            b.Add(v)
            uuids.append(v.m_Uuid.AsString())
    return uuids


def drc():
    cmd = [KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity",
           "--output", DRC_OUT, BOARD_PATH]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.load(open(DRC_OUT, encoding="utf-8")), r.stdout


def usb_unconnected(d):
    n = 0
    for u in d.get("unconnected_items", []):
        if any(any(net in it.get("description", "") for net in NETS) for it in u.get("items", [])):
            n += 1
    return n


# ---- pictures --------------------------------------------------------------------------------------
REGION = (5.0, 7.0, 26.0, 16.0)          # mm: J201's pad row to J101's pads 3/5
SCALE = 60                               # px per mm


def picture(b, side, out):
    """2D plot of one copper side of REGION (top: F.Cu seen from above; bottom: B.Cu seen from above,
    i.e. NOT mirrored, so it lines up with the top picture). USB nets in colour, others grey."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = REGION
    img = Image.new("RGB", (int((x1 - x0) * SCALE), int((y1 - y0) * SCALE)), (250, 250, 247))
    dr = ImageDraw.Draw(img)
    lay = pcbnew.F_Cu if side == "top" else pcbnew.B_Cu
    col = {"USB_DP": (200, 40, 40), "USB_DN": (30, 90, 200)}

    def P(x, y):
        return ((x - x0) * SCALE, (y - y0) * SCALE)

    # 1 mm grid
    for gx in range(int(x0), int(x1) + 1):
        dr.line([P(gx, y0), P(gx, y1)], fill=(232, 232, 228))
    for gy in range(int(y0), int(y1) + 1):
        dr.line([P(x0, gy), P(x1, gy)], fill=(232, 232, 228))
    # courtyards of the side
    for fp in b.GetFootprints():
        if fp.GetLayer() != lay:
            continue
        cb = fp.GetCourtyard(lay).BBox()
        r = [P(pcbnew.ToMM(cb.GetLeft()), pcbnew.ToMM(cb.GetTop())),
             P(pcbnew.ToMM(cb.GetRight()), pcbnew.ToMM(cb.GetBottom()))]
        dr.rectangle(r, outline=(170, 120, 200))
        dr.text((r[0][0] + 4, r[0][1] + 2), fp.GetReference(), fill=(140, 90, 170))
    # pads on this copper side
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnLayer(lay):
                continue
            bb = pad.GetBoundingBox()
            r = [P(pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())),
                 P(pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))]
            c = col.get(pad.GetNetname(), (150, 150, 150))
            dr.rectangle(r, fill=tuple(int(v * 0.5 + 125) for v in c), outline=c)
    # tracks and vias
    for t in b.GetTracks():
        c = col.get(t.GetNetname(), (110, 110, 110))
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            cx, cy = P(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y))
            ro, ri = VIA_D / 2 * SCALE, VIA_DRILL / 2 * SCALE
            dr.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=c)
            dr.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=(250, 250, 247))
            continue
        if t.GetLayer() != lay:
            continue
        s, e = t.GetStart(), t.GetEnd()
        a, z = P(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)), P(pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
        wpx = pcbnew.ToMM(t.GetWidth()) * SCALE
        dr.line([a, z], fill=c, width=max(1, int(round(wpx))))
        for p in (a, z):
            dr.ellipse([p[0] - wpx / 2, p[1] - wpx / 2, p[0] + wpx / 2, p[1] + wpx / 2], fill=c)
    title = ("lado de cima, F.Cu" if side == "top" else "lado de baixo, B.Cu (visto de cima, sem espelhar)")
    dr.text((8, 6), "eTutti Viaggio MicroMod - par USB - %s - grade 1 mm - vermelho USB_DP, azul USB_DN"
            % title, fill=(20, 20, 20))
    img.save(out)


def top_blocks(text):
    """Split a .kicad_pcb into (head, [top-level child blocks], tail); quoted strings may hold
    parentheses (net names like "unconnected-(J201-SBU1-PadA8)")."""
    depth, i, start, blocks, in_str = 0, 0, None, [], False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
            if depth == 2:
                start = i
        elif ch == ")":
            depth -= 1
            if depth == 1:
                # the block owns the whitespace before it (newline + tab)
                ws = start
                while ws > 0 and text[ws - 1] in " \t\r\n":
                    ws -= 1
                blocks.append([ws, i + 1])
            elif depth == 0:
                break
        i += 1
    # blocks as text, each with its leading whitespace; the head ends where the first block's
    # whitespace begins
    head = text[:blocks[0][0]]
    tail = text[blocks[-1][1]:]
    return head, [text[a:z] for a, z in blocks], tail


def kind(block):
    return block.lstrip().split(None, 1)[0].lstrip("(")


def save(b, old_uuids):
    """Write only what this script changes into the file as it was: SaveBoard alone also rewrites
    the project files (it dropped the .kicad_pro's sheet list), the stack-up (the masks' epsilon_r)
    and every text's font block. So: save to a temporary copy, take from it the USB segments/vias
    and the zones (their fill changes round the new vias), and splice them into the original."""
    old = open(BOARD_PATH, encoding="utf-8", newline="").read()
    tmp = os.path.join(BUILD, "route_usb_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for ext in (".kicad_pro", ".kicad_prl"):          # SaveBoard writes a project next to the copy
        p = os.path.join(BUILD, "route_usb_tmp" + ext)
        if os.path.exists(p):
            os.remove(p)
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    h_old, b_old, t_old = top_blocks(old)
    _h, b_new, _t = top_blocks(new)

    def is_usb(blk):
        return kind(blk) in ("segment", "via") and any('(net "%s")' % n in blk for n in NETS)

    usb_new = [x for x in b_new if is_usb(x)]
    zones_new = [x for x in b_new if kind(x) == "zone"]
    out, zi, placed = [], 0, False
    for blk in b_old:
        k = kind(blk)
        if is_usb(blk):
            if not any(u in blk for u in old_uuids):
                raise SystemExit("unexpected USB item in the file")
            continue
        if k == "zone":
            if not placed:
                out.extend(usb_new)
                placed = True
            out.append(zones_new[zi])
            zi += 1
            continue
        out.append(blk)
    if not placed:
        out.extend(usb_new)
    if zi != len(zones_new):
        raise SystemExit("zone count changed while saving")
    open(BOARD_PATH, "w", encoding="utf-8", newline="").write(h_old + "".join(out) + t_old)


def main():
    os.makedirs(BUILD, exist_ok=True)
    tracks, vias, path = geometry()
    check_angles(tracks)
    b = pcbnew.LoadBoard(BOARD_PATH)
    check_pads(b)
    removed, old_uuids = remove_old(b)
    uuids = add(b, tracks, vias)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    save(b, old_uuids)
    json.dump({"uuids": uuids}, open(MANIFEST, "w", encoding="utf-8"), indent=1)

    # measurements, from the board as saved
    b = pcbnew.LoadBoard(BOARD_PATH)
    total = {n: 0.0 for n in NETS}
    nvias = {n: 0 for n in NETS}
    locked = True
    for t in b.GetTracks():
        n = t.GetNetname()
        if n not in NETS:
            continue
        locked = locked and t.IsLocked()
        if t.GetClass() == "PCB_VIA":
            nvias[n] += 1
        else:
            total[n] += pcbnew.ToMM(t.GetLength())
    signal = {n: sum(plen(p) for p in path[n]) for n in NETS}
    skew = abs(signal["USB_DP"] - signal["USB_DN"])
    d, out = drc()
    vio = d.get("violations", [])
    par = d.get("schematic_parity", [])
    unc = d.get("unconnected_items", [])
    usb_unc = usb_unconnected(d)
    for side in ("top", "bottom"):
        picture(b, side, os.path.join(BUILD, "route_usb_%s.png" % side))
    report = {
        "removed_old_items": removed, "tracks_and_vias_written": len(uuids), "all_locked": locked,
        "length_total_mm": {n: round(v, 2) for n, v in total.items()},
        "length_J201_to_J101_mm": {n: round(v, 2) for n, v in signal.items()},
        "skew_mm": round(skew, 2), "vias": nvias,
        "drc_violations": len(vio), "schematic_parity": len(par), "unconnected": len(unc),
        "unconnected_usb": usb_unc,
        "violation_types": sorted({v.get("type", "") for v in vio}),
    }
    print(json.dumps(report, indent=1))
    json.dump(dict(report, uuids=uuids), open(MANIFEST, "w", encoding="utf-8"), indent=1)
    bad = []
    if vio or par:
        bad.append("DRC: %d violations, %d parity" % (len(vio), len(par)))
    if usb_unc:
        bad.append("%d USB connections missing" % usb_unc)
    if max(total.values()) > MAX_LEN:
        bad.append("a USB net is longer than %.0f mm" % MAX_LEN)
    if skew > MAX_SKEW:
        bad.append("skew %.2f mm > %.1f" % (skew, MAX_SKEW))
    if max(nvias.values()) > MAX_VIAS:
        bad.append("more than %d vias on a USB net" % MAX_VIAS)
    if not locked:
        bad.append("a USB item is not locked")
    if bad:
        for v in vio[:20]:
            print(v.get("type"), v.get("description"), [i.get("description") for i in v.get("items", [])])
        raise SystemExit("FAILED: " + "; ".join(bad))
    print("OK")


if __name__ == "__main__":
    main()
