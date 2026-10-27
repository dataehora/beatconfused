"""eTutti Viaggio J1 -- GND and +3V3 copper on the board J routed by hand.

Run with KiCad 10's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/cobre.py

What it does (and only this; J's tracks and vias are never moved):
  1. deletes the 6 dangling vias the DRC reported (net + position checked first);
  2. adds GND pours on F.Cu and B.Cu and a +3V3 pour on In2.Cu (clearance 0.25, thermal
     relief), each over the whole board; the M2 rule areas keep their copper-free rings;
     In1.Cu stays the existing whole-board GND zone ("L2 GND");
  3. adds GND stitching vias 0.5/0.3 on a ~5 mm grid wherever one clears everything on every
     layer, and one more in every F.Cu/B.Cu GND island that has no via or through-hole pad;
  4. for every GND / +3V3 pad the DRC still reports unconnected: a via 0.5/0.3 as near as
     possible with a straight stub to the pad (GND via lands on In1, +3V3 only where the In2
     pour reaches);
  5. writes the board back by splicing ONLY the new zones/vias/tracks, the refilled In1 zone and
     the removal of the 6 vias into the file as it was (pcbnew.SaveBoard alone rewrites the
     .kicad_pro, the stack-up and text fonts -- lesson of PR #120);
  6. runs the KiCad DRC, pictures each copper layer into build/ and prints a summary.

Re-runnable: everything it creates is recorded in cobre_uuids.json (and its zones are named
"COBRE ..."); a new run removes those first, so nothing is duplicated.
"""
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "kicad", "viaggio_micromod.kicad_pcb")
BUILD = os.path.join(HERE, "build")
MANIFEST = os.path.join(HERE, "cobre_uuids.json")
KICAD_CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

ZONE_PREFIX = "COBRE "
IN1_ZONE = "L2 GND"
# dangling vias from the DRC of 27 Oct 2026 (net, x, y in mm)
DANGLING = [("OUT_K03", 118.65, 8.77), ("MUX_S2", 184.33, 12.25), ("PROG", 23.36, 11.25),
            ("EN_A", 98.20, 43.40), ("HP_L", 11.94, 30.27), ("HP_R", 8.85, 23.30)]

MM = pcbnew.FromMM
VIA_D, VIA_DRILL = MM(0.5), MM(0.3)
R_VIA = VIA_D // 2
ZONE_CLR = MM(0.25)
CLR_STITCH = MM(0.25)        # stitching via against anything
CLR_PIN = MM(0.2)            # per-pin via / stub against other nets (Corrente class is 0.2)
EDGE_STITCH, EDGE_PIN = MM(1.0), MM(0.65)
GRID = 5.0
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
CU_NAME = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "In1.Cu", pcbnew.In2_Cu: "In2.Cu", pcbnew.B_Cu: "B.Cu"}


def V(x, y):
    return pcbnew.VECTOR2I(int(x), int(y))


def mm(v):
    return round(pcbnew.ToMM(v), 2)


# ---------------------------------------------------------------- spatial index of copper
class Index:
    def __init__(self, cell=MM(2)):
        self.cell = cell
        self.d = defaultdict(list)

    def add(self, key, shape, net, kind, item):
        bb = shape.BBox()
        e = (shape, net, kind, item)
        c = self.cell
        for cx in range(bb.GetLeft() // c, bb.GetRight() // c + 1):
            for cy in range(bb.GetTop() // c, bb.GetBottom() // c + 1):
                self.d[(key, cx, cy)].append(e)

    def query(self, key, p, rad):
        c, seen = self.cell, set()
        for cx in range((p.x - rad) // c, (p.x + rad) // c + 1):
            for cy in range((p.y - rad) // c, (p.y + rad) // c + 1):
                for e in self.d.get((key, cx, cy), ()):
                    if id(e) not in seen:
                        seen.add(id(e))
                        yield e


def index_item(idx, it):
    net = it.GetNetCode()
    if it.GetClass() == "PCB_VIA":
        for L in CU:
            if it.IsOnLayer(L):
                idx.add(L, it.GetEffectiveShape(L), net, "via", it)
        idx.add("HOLE", it.GetEffectiveHoleShape(), net, "via", it)
    elif it.GetClass() == "PAD":
        for L in CU:
            if it.IsOnLayer(L):
                idx.add(L, it.GetEffectiveShape(L), net, "pad", it)
        if it.HasHole():
            idx.add("HOLE", it.GetEffectiveHoleShape(), net, "pad", it)
    else:
        L = it.GetLayer()
        idx.add(L, it.GetEffectiveShape(L), net, "track", it)


def build_index(b):
    idx = Index()
    for t in b.GetTracks():
        index_item(idx, t)
    for p in b.GetPads():
        index_item(idx, p)
    return idx


# ---------------------------------------------------------------- geometry helpers
def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


class Board:
    def __init__(self, b):
        self.b = b
        outl = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(outl, False)
        self.outline = outl
        ch = outl.Outline(0)
        pts = [ch.CPoint(i) for i in range(ch.PointCount())]
        self.edges = [(pts[i].x, pts[i].y, pts[(i + 1) % len(pts)].x, pts[(i + 1) % len(pts)].y)
                      for i in range(len(pts))]
        self.rules = [z for z in b.Zones() if z.GetIsRuleArea()]
        j101 = b.FindFootprintByReference("J101")
        self.j101 = j101.GetCourtyard(pcbnew.B_CrtYd) if j101 else None

    def inside(self, p, margin):
        if not self.outline.Contains(p):
            return False
        return min(seg_dist(p.x, p.y, *e) for e in self.edges) >= margin

    def rule_hit(self, shape, what):
        for z in self.rules:
            if what == "via" and not z.GetDoNotAllowVias():
                continue
            if what == "track" and not z.GetDoNotAllowTracks():
                continue
            if z.Outline().Collide(shape, MM(0.05)):
                return True
        return False


def via_ok(B, idx, p, net, clr, edge, own_pad=None, own_clr=MM(0.1), same_net_tracks_ok=True):
    if not B.inside(p, edge):
        return False
    circ = pcbnew.SHAPE_CIRCLE(p, R_VIA)
    if B.rule_hit(circ, "via"):
        return False
    rad = R_VIA + clr + MM(0.1)
    for L in CU:
        for shape, n, kind, it in idx.query(L, p, rad):
            if n == net and kind == "track" and same_net_tracks_ok:
                continue
            c = own_clr if (own_pad is not None and it is own_pad) else clr
            if shape.Collide(circ, c):
                return False
    for shape, n, kind, it in idx.query("HOLE", p, rad):
        c = own_clr if (own_pad is not None and it is own_pad) else clr
        if shape.Collide(circ, max(c, MM(0.25))):
            return False
    return True


def stub_ok(B, idx, a, p, width, layer, net):
    seg = pcbnew.SHAPE_SEGMENT(a, p, width)
    if B.rule_hit(seg, "track"):
        return False
    rad = int(math.hypot(p.x - a.x, p.y - a.y)) + width + CLR_PIN + MM(0.1)
    mid = V((a.x + p.x) // 2, (a.y + p.y) // 2)
    for shape, n, kind, it in idx.query(layer, mid, rad):
        if n == net:
            continue
        if shape.Collide(seg, CLR_PIN):
            return False
    for shape, n, kind, it in idx.query("HOLE", mid, rad):
        if n == net:
            continue
        if shape.Collide(seg, MM(0.25)):
            return False
    return True


# ---------------------------------------------------------------- board edits
def new_via(b, idx, p, net, made):
    v = pcbnew.PCB_VIA(b)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetPosition(p)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    try:
        v.SetWidth(VIA_D)
    except TypeError:
        v.SetWidth(pcbnew.F_Cu, VIA_D)
    v.SetDrill(VIA_DRILL)
    v.SetNetCode(net)
    b.Add(v)
    index_item(idx, v)
    made.append(v)
    return v


def new_track(b, idx, a, p, width, layer, net, made):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(a)
    t.SetEnd(p)
    t.SetWidth(width)
    t.SetLayer(layer)
    t.SetNetCode(net)
    b.Add(t)
    index_item(idx, t)
    made.append(t)
    return t


def new_zone(b, B, layer, net, name):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    ch = B.outline.Outline(0)
    for i in range(ch.PointCount()):
        q = ch.CPoint(i)
        ol.Append(q.x, q.y)
    z.SetLocalClearance(ZONE_CLR)
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD solid: thermals on fine pins came out starved
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    z.SetAssignedPriority(0)
    b.Add(z)
    return z


def fill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def filled(z, layer):
    return z.GetFilledPolysList(layer)


# ---------------------------------------------------------------- splice save
def top_blocks(text):
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
                ws = start
                while ws > 0 and text[ws - 1] in " \t\r\n":
                    ws -= 1
                blocks.append([ws, i + 1])
            elif depth == 0:
                break
        i += 1
    head = text[:blocks[0][0]]
    tail = text[blocks[-1][1]:]
    return head, [text[a:z] for a, z in blocks], tail


def kind(block):
    return block.lstrip().split(None, 1)[0].lstrip("(")


UUID_RE = re.compile(r'\(uuid "([^"]+)"\)')
NAME_RE = re.compile(r'\(name "([^"]*)"\)')


def block_uuid(blk):
    m = UUID_RE.search(blk)
    return m.group(1) if m else None


def zone_name(blk):
    m = NAME_RE.search(blk)
    return m.group(1) if m else None


def save(b, original, drop_uuids, new_uuids):
    """original: the file text when the script started. drop_uuids: blocks to take out (the
    dangling vias, the previous run's items). new_uuids: this run's vias/tracks."""
    tmp = os.path.join(BUILD, "cobre_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for f in os.listdir(BUILD):
        if f.startswith("cobre_tmp") and not f.endswith(".kicad_pcb"):
            os.remove(os.path.join(BUILD, f))
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    _h, b_new, _t = top_blocks(new)
    h_old, b_old, t_old = top_blocks(original)
    new_items = [x for x in b_new if kind(x) in ("segment", "via") and block_uuid(x) in new_uuids]
    if len(new_items) != len(new_uuids):
        raise SystemExit("splice: %d new items in the saved copy, expected %d"
                         % (len(new_items), len(new_uuids)))
    zones_new = {zone_name(x): x for x in b_new if kind(x) == "zone"}
    out, placed, dropped = [], False, 0
    for blk in b_old:
        k = kind(blk)
        if k in ("segment", "via", "arc") and block_uuid(blk) in drop_uuids:
            dropped += 1
            continue
        if k == "zone":
            nm = zone_name(blk)
            if nm.startswith(ZONE_PREFIX):
                continue
            if not placed:
                out.extend(new_items)
                placed = True
            if nm == IN1_ZONE:
                out.append(zones_new[IN1_ZONE])
                for nm2 in sorted(zones_new):
                    if nm2.startswith(ZONE_PREFIX):
                        out.append(zones_new[nm2])
                continue
        out.append(blk)
    if not placed:
        raise SystemExit("splice: no zone block in the original file")
    open(BOARD, "w", encoding="utf-8", newline="").write(h_old + "".join(out) + t_old)
    return dropped


# ---------------------------------------------------------------- DRC
def drc(tag):
    out = os.path.join(BUILD, "drc_%s.json" % tag)
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all",
                    "--format", "json", "-o", out, BOARD], check=True, capture_output=True)
    return json.load(open(out, encoding="utf-8"))


def net_of(desc):
    m = re.search(r"\[([^\]]+)\]", desc)
    return m.group(1) if m else "?"


def unconnected_pads(d, b, nets):
    pads = {p.m_Uuid.AsString(): p for p in b.GetPads()}
    found = []
    for u in d.get("unconnected_items", []):
        for it in u["items"]:
            p = pads.get(it.get("uuid"))
            if p is not None and p.GetNetname() in nets and p not in found:
                found.append(p)
    return found


def loose_islands(b, gnd, zones):
    """F.Cu/B.Cu GND islands with no GND via or through-hole pad inside: the fill kept them
    because they touch an SMD pad, but nothing takes them to In1. Returns
    [(layer, island centre, [GND SMD pads in it])]."""
    anchors = [t.GetPosition() for t in b.GetTracks()
               if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd]
    anchors += [p.GetPosition() for p in b.GetPads() if p.GetNetCode() == gnd and p.HasHole()]
    out = []
    for z, L in zones:
        fp = filled(z, L)
        for i in range(fp.OutlineCount()):
            if any(fp.Contains(a, i) for a in anchors):
                continue
            pads = [p for p in b.GetPads() if p.GetNetCode() == gnd and p.IsOnLayer(L)
                    and fp.Contains(p.GetPosition(), i)]
            out.append((L, fp.Outline(i).BBox().Centre(), pads))
    return out


# ---------------------------------------------------------------- stitching
def stitch_grid(b, B, idx, gnd, zF, zB, z1, made):
    bb = B.outline.BBox()
    x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    nx = int(pcbnew.ToMM(bb.GetWidth()) // GRID) + 1
    ny = int(pcbnew.ToMM(bb.GetHeight()) // GRID) + 1
    fF, fB, f1 = filled(zF, pcbnew.F_Cu), filled(zB, pcbnew.B_Cu), filled(z1, pcbnew.In1_Cu)
    offsets = [(0, 0)] + [(dx * 0.5, dy * 0.5) for r in (1, 2, 3, 4)
                          for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                          if max(abs(dx), abs(dy)) == r]
    n = 0
    for i in range(nx):
        for j in range(ny):
            cx, cy = x0 + GRID / 2 + i * GRID, y0 + GRID / 2 + j * GRID
            for dx, dy in offsets:
                p = V(MM(cx + dx), MM(cy + dy))
                if B.j101 is not None and B.j101.Contains(p):
                    continue
                if not f1.Contains(p) or not (fF.Contains(p) or fB.Contains(p)):
                    continue
                if via_ok(B, idx, p, gnd, CLR_STITCH, EDGE_STITCH):
                    new_via(b, idx, p, gnd, made)
                    n += 1
                    break
    return n


def stitch_islands(b, B, idx, gnd, zones, z1, made):
    f1 = filled(z1, pcbnew.In1_Cu)
    anchors = [t.GetPosition() for t in b.GetTracks()
               if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd]
    anchors += [p.GetPosition() for p in b.GetPads() if p.GetNetCode() == gnd and p.HasHole()]
    added, lost = 0, []
    ring = [(math.cos(a * math.pi / 4), math.sin(a * math.pi / 4)) for a in range(8)]
    for z, L in zones:
        fp = filled(z, L)
        for i in range(fp.OutlineCount()):
            if any(fp.Contains(a, i) for a in anchors):
                continue
            ob = fp.Outline(i).BBox()
            cx, cy = ob.Centre().x, ob.Centre().y
            pts = []
            step = MM(0.25)
            for x in range(ob.GetLeft(), ob.GetRight() + 1, step):
                for y in range(ob.GetTop(), ob.GetBottom() + 1, step):
                    pts.append(((x - cx) ** 2 + (y - cy) ** 2, x, y))
            pts.sort()
            ok = False
            for _d, x, y in pts:
                p = V(x, y)
                if not fp.Contains(p, i) or not f1.Contains(p):
                    continue
                if not all(fp.Contains(V(x + MM(0.3) * c, y + MM(0.3) * s), i) for c, s in ring):
                    continue
                if B.j101 is not None and B.j101.Contains(p):
                    continue
                if via_ok(B, idx, p, gnd, CLR_STITCH, EDGE_STITCH):
                    new_via(b, idx, p, gnd, made)
                    anchors.append(p)
                    added += 1
                    ok = True
                    break
            if not ok:
                area = pcbnew.ToMM(pcbnew.ToMM(fp.Outline(i).Area()))
                lost.append((CU_NAME[L], mm(cx), mm(cy), round(area, 2)))
    return added, lost


def prune_unanchored(b, made, gnd, zF, zB, z1):
    """A stitching via must land in the In1 pour and in F.Cu or B.Cu pour after the refill,
    or it would only touch one layer (via_dangling)."""
    fF, fB, f1 = filled(zF, pcbnew.F_Cu), filled(zB, pcbnew.B_Cu), filled(z1, pcbnew.In1_Cu)
    gone = 0
    for v in list(made):
        if v.GetClass() != "PCB_VIA" or v.GetNetCode() != gnd:
            continue
        p = v.GetPosition()
        if f1.Contains(p) and (fF.Contains(p) or fB.Contains(p)):
            continue
        made.remove(v)
        b.Remove(v)
        gone += 1
    return gone


# ---------------------------------------------------------------- per-pin vias
def pin_via(b, B, idx, pad, zone_fill, made):
    """Via near pad + straight stub. zone_fill: the filled poly the via must land in
    (In1 GND or In2 +3V3)."""
    net = pad.GetNetCode()
    c = pad.GetPosition()
    layers = [L for L in (pcbnew.F_Cu, pcbnew.B_Cu) if pad.IsOnLayer(L)]
    sz = pad.GetSize(layers[0]) if layers else pad.GetSize(pcbnew.F_Cu)
    half = max(sz.x, sz.y) / 2
    narrow = min(sz.x, sz.y) < MM(0.45)
    widths = [MM(0.15)] if narrow else [MM(0.2), MM(0.15)]
    best = None
    fills = zone_fill if isinstance(zone_fill, list) else [zone_fill]
    for zf in fills:                           # preferred pour first (the connected one)
        for k in range(0, 40):                 # distance from the pad centre, nearest first
            d = MM(0.35) + k * MM(0.1)
            if d > half + MM(3.0):
                break
            for a in range(32):
                ang = a * math.pi / 16
                p = V(c.x + d * math.cos(ang), c.y + d * math.sin(ang))
                if not zf.Contains(p):
                    continue
                if not via_ok(B, idx, p, net, CLR_PIN, EDGE_PIN, own_pad=pad):
                    continue
                for L in layers:
                    for w in widths:
                        if stub_ok(B, idx, c, p, w, L, net):
                            best = (p, L, w)
                            break
                    if best:
                        break
                if best:
                    break
            if best:
                break
        if best:
            break
    if not best:
        return None
    p, L, w = best
    v = new_via(b, idx, p, net, made)
    new_track(b, idx, c, p, w, L, net, made)
    return (pad.GetParentFootprint().GetReference(), pad.GetNumber(), pad.GetNetname(),
            CU_NAME[L], mm(p.x), mm(p.y), mm(w), mm(math.hypot(p.x - c.x, p.y - c.y)),
            v.m_Uuid.AsString())


# ---------------------------------------------------------------- picture
def picture(b, layer, made_ids, out, title):
    from PIL import Image, ImageDraw
    S = 8.0
    bb = b.GetBoardEdgesBoundingBox()
    ox, oy = bb.GetLeft() - MM(2), bb.GetTop() - MM(6)
    W = int(pcbnew.ToMM(bb.GetWidth() + MM(4)) * S)
    H = int(pcbnew.ToMM(bb.GetHeight() + MM(8)) * S)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)

    def P(v):
        return (pcbnew.ToMM(v.x - ox) * S, pcbnew.ToMM(v.y - oy) * S)

    def chain(ch):
        return [P(ch.CPoint(i)) for i in range(ch.PointCount())]

    outl = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outl, False)
    dr.polygon(chain(outl.Outline(0)), fill=(236, 236, 228), outline=(80, 80, 80))
    colours = {"GND": (150, 200, 235), "+3V3": (245, 190, 120)}
    for z in b.Zones():
        if z.GetIsRuleArea():
            if z.GetDoNotAllowVias():
                dr.polygon(chain(z.Outline().Outline(0)), outline=(200, 0, 200))
            continue
        if not z.IsOnLayer(layer):
            continue
        fp = z.GetFilledPolysList(layer)
        col = colours.get(z.GetNetname(), (200, 200, 200))
        for i in range(fp.OutlineCount()):
            dr.polygon(chain(fp.Outline(i)), fill=col)
            for h in range(fp.HoleCount(i)):
                dr.polygon(chain(fp.Hole(i, h)), fill=(236, 236, 228))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        if t.GetLayer() != layer:
            continue
        new = t.m_Uuid.AsString() in made_ids
        col = (220, 0, 0) if new else ((30, 60, 160) if t.GetNetname() == "GND" else
                                        (190, 90, 0) if t.GetNetname() == "+3V3" else (60, 60, 60))
        w = max(1, int(pcbnew.ToMM(t.GetWidth()) * S))
        dr.line([P(t.GetStart()), P(t.GetEnd())], fill=col, width=w)
    for p in b.GetPads():
        if not p.IsOnLayer(layer):
            continue
        bbp = p.GetBoundingBox()
        col = (30, 60, 160) if p.GetNetname() == "GND" else (190, 90, 0) if p.GetNetname() == "+3V3" \
            else (110, 110, 110)
        a, z2 = P(V(bbp.GetLeft(), bbp.GetTop())), P(V(bbp.GetRight(), bbp.GetBottom()))
        dr.rectangle([a, z2], outline=col)
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = P(t.GetPosition())
        r = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2 * S
        uid = t.m_Uuid.AsString()
        if uid in made_ids:
            col = (0, 150, 0) if made_ids[uid] == "stitch" else (220, 0, 0)
        else:
            col = (90, 90, 90)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col)
    dr.text((8, 6), title + "  |  azul = GND, laranja = +3V3, verde = via de costura nova, "
            "vermelho = via/toco por pino novo, magenta = anel livre M2", fill=(0, 0, 0))
    img.save(out)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(BUILD, exist_ok=True)
    original = open(BOARD, encoding="utf-8", newline="").read()
    prev = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    prev_ids = set(prev.get("stitch", []) + prev.get("pin", []))

    b = pcbnew.LoadBoard(BOARD)
    # 0. take out a previous run (collect first, remove after: proxies of removed items go stale)
    tracks = list(b.GetTracks())
    ids = [t.m_Uuid.AsString() for t in tracks]
    gone = [t for t, u in zip(tracks, ids) if u in prev_ids]
    gone_z = [z for z in b.Zones() if z.GetZoneName().startswith(ZONE_PREFIX)]

    # 1. the six dangling vias
    removed = list(prev.get("removed_dangling", []))
    for net, x, y in DANGLING:
        hit = [(t, u) for t, u in zip(tracks, ids) if t.GetClass() == "PCB_VIA"
               and t.GetNetname() == net
               and abs(pcbnew.ToMM(t.GetPosition().x) - x) < 0.02
               and abs(pcbnew.ToMM(t.GetPosition().y) - y) < 0.02]
        if len(hit) > 1:
            raise SystemExit("more than one via of %s at (%.2f; %.2f)" % (net, x, y))
        if hit:
            removed.append({"net": net, "x": x, "y": y, "uuid": hit[0][1]})
            gone.append(hit[0][0])
        elif not any(r["net"] == net for r in removed):
            raise SystemExit("dangling via of %s at (%.2f; %.2f) not found" % (net, x, y))
    for t in gone:
        b.Remove(t)
    for z in gone_z:
        b.Remove(z)
    del tracks
    drop = prev_ids | {r["uuid"] for r in removed}

    B = Board(b)
    gnd = b.FindNet("GND").GetNetCode()
    v33 = b.FindNet("+3V3").GetNetCode()
    z1 = [z for z in b.Zones() if z.GetZoneName() == IN1_ZONE][0]

    # 2-3. pours
    zF = new_zone(b, B, pcbnew.F_Cu, b.FindNet("GND"), ZONE_PREFIX + "GND F.Cu")
    zB = new_zone(b, B, pcbnew.B_Cu, b.FindNet("GND"), ZONE_PREFIX + "GND B.Cu")
    z2 = new_zone(b, B, pcbnew.In2_Cu, b.FindNet("+3V3"), ZONE_PREFIX + "+3V3 In2.Cu")
    fill(b)

    # 4. stitching
    idx = build_index(b)
    stitch = []
    n_grid = stitch_grid(b, B, idx, gnd, zF, zB, z1, stitch)
    fill(b)
    n_isl, lost = stitch_islands(b, B, idx, gnd, [(zF, pcbnew.F_Cu), (zB, pcbnew.B_Cu)], z1, stitch)
    fill(b)
    pruned = prune_unanchored(b, stitch, gnd, zF, zB, z1)
    for z in (zF, zB, z2):
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    fill(b)
    pruned += prune_unanchored(b, stitch, gnd, zF, zB, z1)
    fill(b)

    def manifest(pin_items):
        return {"stitch": [v.m_Uuid.AsString() for v in stitch],
                "pin": [x.m_Uuid.AsString() for x in pin_items],
                "removed_dangling": removed}

    pin_items, pin_log, pin_fail = [], [], []
    m = manifest(pin_items)
    save(b, original, drop, set(m["stitch"]) | set(m["pin"]))
    d = drc("cobre_r0")

    # 5. per-pin vias, two rounds
    for rnd in (1, 2):
        pads = unconnected_pads(d, b, ("GND", "+3V3"))
        for _L, _c, ps in loose_islands(b, gnd, [(zF, pcbnew.F_Cu), (zB, pcbnew.B_Cu)]):
            pads += [p for p in ps if p not in pads]
        if not pads:
            break
        idx = build_index(b)
        f2_main = pcbnew.SHAPE_POLY_SET(filled(z2, pcbnew.In2_Cu))     # islands removed
        # J's In2 tracks wall in pockets of the +3V3 pour that hold no +3V3 item yet, so the
        # "always remove islands" fill dropped them; look at the pour with its islands kept, so
        # a pad inside such a pocket can take a via into it (the pocket then survives the final
        # fill, tying that pocket's pads together; it still needs one link to the rest).
        z2.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        fill(b)
        f1 = filled(z1, pcbnew.In1_Cu)
        f2 = filled(z2, pcbnew.In2_Cu)
        tried = {(r[0], r[1]) for r in pin_log} | {(r[0], r[1]) for r in pin_fail}
        for pad in pads:
            key = (pad.GetParentFootprint().GetReference(), pad.GetNumber())
            if key in tried:
                continue
            r = pin_via(b, B, idx, pad, f1 if pad.GetNetCode() == gnd else [f2_main, f2],
                        pin_items)
            if r:
                pin_log.append(r)
            else:
                pin_fail.append(key + (pad.GetNetname(), mm(pad.GetPosition().x),
                                       mm(pad.GetPosition().y)))
        z2.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        fill(b)
        # a +3V3 via whose In2 pour did not reach it after the refill is taken back
        f2 = filled(z2, pcbnew.In2_Cu)
        f1 = filled(z1, pcbnew.In1_Cu)
        for v in [x for x in pin_items if x.GetClass() == "PCB_VIA"]:
            ok = (f1 if v.GetNetCode() == gnd else f2).Contains(v.GetPosition())
            if not ok:
                stub = [t for t in pin_items if t.GetClass() == "PCB_TRACK"
                        and t.GetEnd() == v.GetPosition()]
                uid = v.m_Uuid.AsString()
                for r in [r for r in pin_log if r[-1] == uid]:
                    pin_log.remove(r)
                    pin_fail.append(r[:3] + ("In2 nao alcanca a via", r[4], r[5]))
                for t in stub + [v]:
                    pin_items.remove(t)
                    b.Remove(t)
        fill(b)
        m = manifest(pin_items)
        save(b, original, drop, set(m["stitch"]) | set(m["pin"]))
        d = drc("cobre_r%d" % rnd)

    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1)

    # 6. pictures and summary
    b = pcbnew.LoadBoard(BOARD)
    made_ids = {u: "stitch" for u in m["stitch"]}
    made_ids.update({u: "pin" for u in m["pin"]})
    for L, nm, tt in ((pcbnew.F_Cu, "top", "F.Cu (lado de cima)"),
                      (pcbnew.B_Cu, "bottom", "B.Cu (lado de baixo, visto de cima, sem espelhar)"),
                      (pcbnew.In2_Cu, "in2", "In2.Cu (+3V3 entre as trilhas)"),
                      (pcbnew.In1_Cu, "in1", "In1.Cu (GND)")):
        picture(b, L, made_ids, os.path.join(BUILD, "cobre_%s.png" % nm), "eTutti Viaggio J1 - " + tt)
    pin_vias = defaultdict(int)
    for r in pin_log:
        pin_vias[r[2]] += 1
    summary = {
        "removed_dangling": removed,
        "stitch_vias": len(m["stitch"]), "stitch_grid": n_grid, "stitch_islands": n_isl,
        "stitch_pruned": pruned, "islands_without_via": lost,
        "pin_vias": dict(pin_vias), "pin_log": pin_log, "pin_fail": pin_fail,
        "violations": {}, "unconnected": {},
    }
    for v in d.get("violations", []):
        summary["violations"][v["type"]] = summary["violations"].get(v["type"], 0) + 1
    for u in d.get("unconnected_items", []):
        n = net_of(u["items"][0]["description"])
        summary["unconnected"].setdefault(n, []).append(
            [(it["description"][:70], it["pos"]["x"], it["pos"]["y"]) for it in u["items"]])
    summary["parity"] = len(d.get("schematic_parity", []))
    zs = {z.GetZoneName(): z for z in b.Zones()}
    summary["loose_islands_final"] = [
        (CU_NAME[L], mm(c.x), mm(c.y), ["%s.%s" % (p.GetParentFootprint().GetReference(),
                                                  p.GetNumber()) for p in ps])
        for L, c, ps in loose_islands(b, b.FindNet("GND").GetNetCode(),
                                      [(zs[ZONE_PREFIX + "GND F.Cu"], pcbnew.F_Cu),
                                       (zs[ZONE_PREFIX + "GND B.Cu"], pcbnew.B_Cu)])]
    json.dump(summary, open(os.path.join(BUILD, "cobre_resumo.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps({k: summary[k] for k in ("stitch_vias", "stitch_grid", "stitch_islands",
                                               "stitch_pruned", "pin_vias", "violations",
                                               "parity")}, indent=1))
    print("unconnected:", {k: len(v) for k, v in summary["unconnected"].items()})
    print("pin vias failed:", len(pin_fail))
    bad = {k: n for k, n in summary["violations"].items() if k != "track_width"}
    if bad or summary["violations"].get("track_width", 0) > 13:
        print("NEW DRC VIOLATIONS:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
