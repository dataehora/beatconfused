"""eTutti Viaggio J1 -- route the connections still open on J's board, lot by lot.

Run with KiCad 10's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/rota_restante.py <lot>
    (<lot> = 1..5, 6a, 6b, 6c, or "fotos" for the pictures only)

Lots (task of 27 Oct 2026, authorised by J):
  1  BB_L1, BB_L2, VSYS, VBAT and the GND islands of the charger / converter (x 50-76, y 3-21)
  2  VBUS
  3  GND of the codec (U301.21, C304.2), I2C_SDA, I2C_SCL and the +3V3 left of the keyboard
  4  the +3V3 pockets in the keyboard (x >= 95)
  5  OUT_K03 (its loose stub at (118.97; 8.45) is deleted first)
  6a/6b/6c  closing (27 Oct 2026): authorised rip-up and reroute, see "lot 6" below

What it does, and only this:
  * nothing existing is moved or deleted (except lot 5's stub); footprints are not touched;
  * a 3-layer grid A* (F.Cu, In2.Cu, B.Cu; In1 is the whole GND plane and is never routed;
    through vias 0.5/0.3) joins the clusters of each net, as pcbnew's connectivity sees them;
    widths follow the .kicad_dru classes: Corrente 0.8 (down to 0.2 only inside the courtyards
    of J201, U202, U204, J202, U501, J101), GND/+3V3 0.3 or 0.2, signals 0.2, and 0.15 only on
    the cells next to the pins being joined;
  * every new segment and via is checked again with pcbnew's exact shapes (clearance per class,
    hole clearance, hole-to-hole, board edge) before it is kept;
  * the zones are refilled; GND/+3V3 pieces a new track cut loose are joined in the same lot;
  * the board is written by splicing only the new segments/vias and the refilled zones into the
    file as it was (lesson of PR #120): every other block is checked identical, by uuid;
  * the KiCad DRC runs and the script exits non-zero on any new violation that is not the
    13 track_width of J's tracks (or the OUT_K03 stub before lot 5).

Re-runnable: what each lot creates is recorded in rota_restante.json; running lot N again
first removes what lot N made before.
"""
import heapq
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

import numpy as np
import pcbnew
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "kicad", "viaggio_micromod.kicad_pcb")
PRO = os.path.join(HERE, "kicad", "viaggio_micromod.kicad_pro")
BUILD = os.path.join(HERE, "build")
MANIFEST = os.path.join(HERE, "rota_restante.json")
KICAD_CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

def MM(v):
    return pcbnew.FromMM(float(v))


TOMM = pcbnew.ToMM
RL = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]             # routing layers, index 0..2
ALLCU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LNAME = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "In1.Cu", pcbnew.In2_Cu: "In2.Cu", pcbnew.B_Cu: "B.Cu"}
VIA_D, VIA_DRILL = 0.5, 0.3
EDGE_CLR, HOLE_CLR, HOLE2HOLE = 0.3, 0.2, 0.25
SLACK = 0.01
THIN_REFS = ("J201", "U202", "U204", "J202", "U501", "J101",
             # added to the .kicad_dru rule on 27 Oct 2026 (lot 6)
             "R205", "R206", "R214", "Q201", "U201", "C201")
PROTECT = []
NECK = True      # lots 1-5: Corrente may neck to 0.3 next to a pin; lot 6: only inside THIN_REFS
RIP = None       # lot 6: called when a connection failed twice (rip up and reroute)
STUB_OUT_K03 = ("OUT_K03", 118.975, 8.4451, 118.6494, 8.7707)

LOTS = {
    1: {"nets": ["BB_L1", "BB_L2", "VSYS", "VBAT"], "gnd": (50, 3, 76, 21), "v33": None,
        "txt": "BB_L1, BB_L2, VSYS, VBAT e GND do carregador/conversor"},
    2: {"nets": ["VBUS"], "gnd": None, "v33": None, "txt": "VBUS"},
    3: {"nets": ["I2C_SDA", "I2C_SCL"], "gnd": (15, 30, 35, 40), "v33": (0, 0, 95, 95),
        "txt": "GND do codec, I2C_SDA, I2C_SCL e +3V3 junto do J101 e do codec"},
    4: {"nets": [], "gnd": None, "v33": (95, 0, 247, 95), "txt": "bolsoes de +3V3 no teclado"},
    5: {"nets": ["OUT_K03"], "gnd": None, "v33": None, "txt": "OUT_K03"},
}


def V(x, y):
    return pcbnew.VECTOR2I(int(round(x)), int(round(y)))


def r2(v):
    return round(v, 2)


# ------------------------------------------------------------------ net classes
def net_classes():
    d = json.load(open(PRO, encoding="utf-8"))
    ns = d["net_settings"]
    clr = {c["name"]: c["clearance"] for c in ns["classes"]}
    pats = [(re.compile("^" + p["pattern"] + "$"), p["netclass"]) for p in ns.get("netclass_patterns", [])]
    return clr, pats


CLASS_CLR, CLASS_PATS = net_classes()


def klass(name):
    for rx, k in CLASS_PATS:
        if rx.match(name):
            return k
    return "Default"


def clr_of(name):
    return max(CLASS_CLR.get(klass(name), 0.1), 0.1)


def widths_for(net):
    """(widths, widest first; min width outside the thin region; min inside it)."""
    k = klass(net)
    if k == "Corrente":
        return [0.8, 0.5, 0.3, 0.2, 0.15], 0.8, 0.15
    if net in ("GND", "+3V3"):
        return [0.3, 0.2, 0.15], 0.2, 0.15
    return [0.2, 0.15], 0.2, 0.15


# ------------------------------------------------------------------ board helpers
class Ctx:
    def __init__(self, b):
        self.b = b
        o = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(o, False)
        self.outline = o
        ch = o.Outline(0)
        self.opts = [(TOMM(ch.CPoint(i).x), TOMM(ch.CPoint(i).y)) for i in range(ch.PointCount())]
        self.rules = [z for z in b.Zones() if z.GetIsRuleArea()
                      and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias())]
        self.thin_polys = []
        for ref in THIN_REFS:
            fp = b.FindFootprintByReference(ref)
            if fp is None:
                continue
            for L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                c = fp.GetCourtyard(L)
                for i in range(c.OutlineCount()):
                    chn = c.Outline(i)
                    self.thin_polys.append([(TOMM(chn.CPoint(k).x), TOMM(chn.CPoint(k).y))
                                            for k in range(chn.PointCount())])
        self.refresh()

    def refresh(self):
        b = self.b
        self.items = list(b.GetTracks()) + list(b.GetPads())
        self.netname = {}
        for it in self.items:
            self.netname[it.GetNetCode()] = it.GetNetname()


def bbox_mm(it):
    bb = it.GetBoundingBox()
    return TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())


def item_layers(it):
    if it.GetClass() == "PCB_VIA":
        return [L for L in ALLCU if it.IsOnLayer(L)]
    if it.GetClass() == "PAD":
        return [L for L in ALLCU if it.IsOnLayer(L)]
    return [it.GetLayer()]


def has_hole(it):
    if it.GetClass() == "PCB_VIA":
        return True
    if it.GetClass() == "PAD":
        return it.HasHole()
    return False


# ------------------------------------------------------------------ raster window
class Win:
    def __init__(self, x0, y0, x1, y1, p):
        self.p = p
        self.x0, self.y0 = x0, y0
        self.W = int(math.ceil((x1 - x0) / p)) + 1
        self.H = int(math.ceil((y1 - y0) / p)) + 1

    def img(self):
        return Image.new("1", (self.W, self.H), 0)

    def px(self, x, y):
        return ((x - self.x0) / self.p, (y - self.y0) / self.p)

    def poly(self, dr, pts):
        if len(pts) >= 3:
            dr.polygon([self.px(x, y) for x, y in pts], fill=1)

    def polyset(self, dr, ps):
        for i in range(ps.OutlineCount()):
            ch = ps.Outline(i)
            self.poly(dr, [(TOMM(ch.CPoint(k).x), TOMM(ch.CPoint(k).y)) for k in range(ch.PointCount())])

    def disc(self, dr, x, y, r):
        cx, cy = self.px(x, y)
        rr = r / self.p
        dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=1, outline=1)

    def stadium(self, dr, a, b_, r):
        self.disc(dr, a[0], a[1], r)
        self.disc(dr, b_[0], b_[1], r)
        w = max(1, int(round(2 * r / self.p)))
        dr.line([self.px(*a), self.px(*b_)], fill=1, width=w)

    def xy(self, ix, iy):
        return self.x0 + ix * self.p, self.y0 + iy * self.p

    def inside(self, x0, y0, x1, y1):
        return not (x1 < self.x0 or y1 < self.y0 or x0 > self.x0 + self.W * self.p
                    or y0 > self.y0 + self.H * self.p)


def inflated(it, L, c):
    ps = pcbnew.SHAPE_POLY_SET()
    it.TransformShapeToPolygon(ps, L, MM(c), MM(0.005), pcbnew.ERROR_OUTSIDE)
    return ps


def hole_geom(it):
    h = it.GetEffectiveHoleShape()
    a, b_ = h.GetSeg().A, h.GetSeg().B
    return (TOMM(a.x), TOMM(a.y)), (TOMM(b_.x), TOMM(b_.y)), TOMM(h.GetWidth()) / 2


def big_gnd_pad(it):
    """A GND exposed pad (both sides >= 1.2 mm): vias inside it are the normal way down."""
    if it.GetNetname() != "GND":
        return False
    L = pcbnew.B_Cu if it.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
    sz = it.GetSize(L)
    return min(TOMM(sz.x), TOMM(sz.y)) >= 1.2


def build_masks(ctx, w, net, widths, margin, skip=None):
    """Blocked masks for the net being routed: per routing layer and width; plus via mask.
    skip: uuids of tracks left out (lot 6: the tracks that may be ripped up)."""
    my_clr = clr_of(net)
    imgs = {(li, wd): w.img() for li in range(3) for wd in widths}
    drs = {k: ImageDraw.Draw(v) for k, v in imgs.items()}
    vimg = w.img()
    vdr = ImageDraw.Draw(vimg)
    reach = max(widths) / 2 + 0.3 + margin + 0.5
    for it in ctx.items:
        x0, y0, x1, y1 = bbox_mm(it)
        if not w.inside(x0 - reach, y0 - reach, x1 + reach, y1 + reach):
            continue
        if skip and it.GetClass() == "PCB_TRACK" and it.m_Uuid.AsString() in skip:
            continue
        own = it.GetNetname() == net and it.GetNetCode() != 0
        cls = it.GetClass()
        if not own:
            c = max(my_clr, clr_of(it.GetNetname())) + margin
            for L in item_layers(it):
                if L in RL:
                    li = RL.index(L)
                    for wd in widths:
                        w.polyset(drs[(li, wd)], inflated(it, L, c + wd / 2 + SLACK))
                w.polyset(vdr, inflated(it, L, c + VIA_D / 2 + SLACK))
        elif cls == "PAD" and not it.HasHole() and not big_gnd_pad(it):
            # no via in an SMD pad of our own net (except a GND exposed pad)
            for L in item_layers(it):
                w.polyset(vdr, inflated(it, L, 0.05 + VIA_D / 2))
        if has_hole(it):
            a, b_, r = hole_geom(it)
            w.stadium(vdr, a, b_, r + HOLE2HOLE + VIA_DRILL / 2 + SLACK)
            if not own:
                for li in range(3):
                    for wd in widths:
                        w.stadium(drs[(li, wd)], a, b_, r + HOLE_CLR + margin + wd / 2 + SLACK)
    # copper kept round pads a new track had cut loose (lot retry)
    for pr in PROTECT:
        if pr["rede"] == net:
            continue
        x0, y0, x1, y1 = pr["caixa"]
        box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for li in range(3):
            if RL[li] in pr["camadas"]:
                for wd in widths:
                    w.poly(drs[(li, wd)], box)
        w.poly(vdr, box)
    # rule areas (M2 rings): no tracks, no vias
    def rule_area(d, o, r):
        w.polyset(d, o)
        for i in range(o.OutlineCount()):
            ch = o.Outline(i)
            pts = [(TOMM(ch.CPoint(k).x), TOMM(ch.CPoint(k).y)) for k in range(ch.PointCount())]
            for k in range(len(pts)):
                w.stadium(d, pts[k], pts[(k + 1) % len(pts)], r)
    for z in ctx.rules:
        o = z.Outline()
        for li in range(3):
            if z.GetDoNotAllowTracks() and z.IsOnLayer(RL[li]):
                for wd in widths:
                    rule_area(drs[(li, wd)], o, wd / 2 + 0.02 + SLACK)
        if z.GetDoNotAllowVias():
            rule_area(vdr, o, VIA_D / 2 + 0.02 + SLACK)
    # board edge
    ins = w.img()
    w.poly(ImageDraw.Draw(ins), ctx.opts)
    inside = np.array(ins, dtype=bool)
    blocked = {}
    for (li, wd), im in imgs.items():
        d = drs[(li, wd)]
        r = EDGE_CLR + margin + wd / 2 + SLACK
        n = len(ctx.opts)
        for k in range(n):
            w.stadium(d, ctx.opts[k], ctx.opts[(k + 1) % n], r)
        blocked[(li, wd)] = np.array(im, dtype=bool) | ~inside
    r = EDGE_CLR + margin + VIA_D / 2 + SLACK
    n = len(ctx.opts)
    for k in range(n):
        w.stadium(vdr, ctx.opts[k], ctx.opts[(k + 1) % n], r)
    vblock = np.array(vimg, dtype=bool) | ~inside
    return blocked, vblock


def thin_mask(ctx, w):
    im = w.img()
    d = ImageDraw.Draw(im)
    for pts in ctx.thin_polys:
        w.poly(d, pts)
    return np.array(im, dtype=bool)


def dilate(m, r):
    out = m.copy()
    H, W = m.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if (dx or dy) and dx * dx + dy * dy <= r * r:
                ys0, ys1 = max(0, -dy), min(H, H - dy)
                xs0, xs1 = max(0, -dx), min(W, W - dx)
                out[ys0:ys1, xs0:xs1] |= m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


# ------------------------------------------------------------------ clusters
def clusters(b, net):
    """Connected groups of a net's items (pcbnew connectivity, zones included)."""
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    items = [t for t in b.GetTracks() if t.GetNetname() == net] + \
            [p for p in b.GetPads() if p.GetNetname() == net]
    seen, out = {}, []
    for it in items:
        u = it.m_Uuid.AsString()
        if u in seen:
            continue
        grp = conn.GetConnectedItems(it)
        g = {"items": [it], "zones": set()}
        seen[u] = len(out)
        for o in grp:
            if o.GetClass() == "ZONE":
                g["zones"].add(o.m_Uuid.AsString())
                continue
            uo = o.m_Uuid.AsString()
            if uo not in seen:
                seen[uo] = len(out)
                g["items"].append(o)
        out.append(g)
    return out


def zone_islands(b, g):
    """Zone island polygons (layer, SHAPE_POLY_SET index) holding one of the cluster's items."""
    res = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.m_Uuid.AsString() not in g["zones"]:
            continue
        for L in z.GetLayerSet().Seq():
            fp = z.GetFilledPolysList(L)
            for i in range(fp.OutlineCount()):
                for it in g["items"]:
                    if not it.IsOnLayer(L):
                        continue
                    pts = [it.GetPosition()] if it.GetClass() != "PCB_TRACK" else [it.GetStart(), it.GetEnd()]
                    if any(fp.Contains(p, i) for p in pts):
                        res.append((z, L, fp, i))
                        break
    return res


def cluster_points(b, g, step=0.5):
    pts = []
    for it in g["items"]:
        if it.GetClass() == "PCB_TRACK":
            a, e = it.GetStart(), it.GetEnd()
            n = max(1, int(TOMM(it.GetLength()) / step))
            for k in range(n + 1):
                pts.append((TOMM(a.x + (e.x - a.x) * k / n), TOMM(a.y + (e.y - a.y) * k / n)))
        else:
            p = it.GetPosition()
            pts.append((TOMM(p.x), TOMM(p.y)))
    for z, L, fp, i in g.get("isl", []):
        ch = fp.Outline(i)
        n = ch.PointCount()
        s = max(1, n // 400)
        for k in range(0, n, s):
            q = ch.CPoint(k)
            pts.append((TOMM(q.x), TOMM(q.y)))
    return np.array(pts) if pts else np.zeros((0, 2))


def has_in1(b, g):
    for z in b.Zones():
        if z.m_Uuid.AsString() in g["zones"] and z.IsOnLayer(pcbnew.In1_Cu):
            return True
    return False


def cluster_mask(ctx, w, g, net, pads_only=False):
    """Cells (per routing layer) on the cluster's own copper."""
    imgs = [w.img() for _ in range(3)]
    drs = [ImageDraw.Draw(i) for i in imgs]
    for it in g["items"]:
        if pads_only and it.GetClass() != "PAD":
            continue
        x0, y0, x1, y1 = bbox_mm(it)
        if not w.inside(x0, y0, x1, y1):
            continue
        for L in item_layers(it):
            if L in RL:
                li = RL.index(L)
                if it.GetClass() == "PCB_TRACK":
                    a, e = it.GetStart(), it.GetEnd()
                    w.stadium(drs[li], (TOMM(a.x), TOMM(a.y)), (TOMM(e.x), TOMM(e.y)),
                              max(TOMM(it.GetWidth()) / 2 - 0.04, 0.03))
                else:
                    w.polyset(drs[li], inflated(it, L, -0.0) if it.GetClass() == "PAD"
                              else inflated(it, L, 0))
    for z, L, fp, i in ([] if pads_only else g.get("isl", [])):
        if L in RL:
            ch = fp.Outline(i)
            w.poly(drs[RL.index(L)], [(TOMM(ch.CPoint(k).x), TOMM(ch.CPoint(k).y))
                                      for k in range(ch.PointCount())])
            for h in range(fp.HoleCount(i)):
                hc = fp.Hole(i, h)
                hp = [(TOMM(hc.CPoint(k).x), TOMM(hc.CPoint(k).y)) for k in range(hc.PointCount())]
                if len(hp) >= 3:
                    ImageDraw.Draw(imgs[RL.index(L)]).polygon([w.px(x, y) for x, y in hp], fill=0)
    # a route may only end where its end point is surely inside the copper (KiCad tests the
    # point): one cell in from the rasterised edge
    return [~dilate(~np.array(i, dtype=bool), 1) for i in imgs]


def in1_mask(b, w):
    im = w.img()
    d = ImageDraw.Draw(im)
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In1_Cu) and z.GetNetname() == "GND":
            fp = z.GetFilledPolysList(pcbnew.In1_Cu)
            for i in range(fp.OutlineCount()):
                ch = fp.Outline(i)
                w.poly(d, [(TOMM(ch.CPoint(k).x), TOMM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
                for h in range(fp.HoleCount(i)):
                    hc = fp.Hole(i, h)
                    hp = [w.px(TOMM(hc.CPoint(k).x), TOMM(hc.CPoint(k).y)) for k in range(hc.PointCount())]
                    if len(hp) >= 3:
                        d.polygon(hp, fill=0)
    m = np.array(im, dtype=bool)
    # the via must sit well inside the fill
    return ~dilate(~m, int(math.ceil(0.3 / w.p)))


# ------------------------------------------------------------------ A*
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
TURN = {0: 0.0, 1: 0.05, 2: 0.3}


def astar(w, usable, vok, src, tgt, tvia, layer_cost, via_cost, max_expand=4_000_000, cellcost=None,
          vcost=None):
    """usable[li]: flat list of bools; vok: flat via-ok list; src/tgt: per layer flat bool
    lists; tvia: flat list (a via there finishes). Returns [(li, i)] path and end-with-via flag."""
    W, H = w.W, w.H
    P = w.p
    tcells = [(li, i) for li in range(3) for i in np.flatnonzero(tgt[li]).tolist()]
    tv = np.flatnonzero(tvia).tolist() if tvia is not None else []
    if not tcells and not tv:
        return None, False
    allt = [i for _, i in tcells] + tv
    txs = [i % W for i in allt]
    tys = [i // W for i in allt]
    bx0, bx1, by0, by1 = min(txs), max(txs), min(tys), max(tys)
    tset = [set(np.flatnonzero(tgt[li]).tolist()) for li in range(3)]
    tvs = set(tv)

    def h(ix, iy):
        dx = max(bx0 - ix, 0, ix - bx1)
        dy = max(by0 - iy, 0, iy - by1)
        return (max(dx, dy) + 0.4142 * min(dx, dy)) * P

    g, parent, heap = {}, {}, []
    for li in range(3):
        for i in np.flatnonzero(src[li]).tolist():
            if not usable[li][i]:
                continue
            s = (li, i, 8)
            g[s] = 0.0
            parent[s] = None
            heapq.heappush(heap, (h(i % W, i // W), 0.0, s))
    n = 0
    VIA_END = (-1, -1, -1)
    while heap:
        f, gc, s = heapq.heappop(heap)
        if s == VIA_END:
            break
        if gc > g.get(s, 1e18):
            continue
        li, i, d = s
        if i in tset[li] and parent[s] is not None:
            break
        n += 1
        if n > max_expand:
            return None, False
        ix, iy = i % W, i // W
        U = usable[li]
        lc = layer_cost[li]
        CC = cellcost[li] if cellcost is not None else None
        for nd, (dx, dy) in enumerate(DIRS):
            if d != 8:
                turn = min((nd - d) % 8, (d - nd) % 8)
                if turn > 2:
                    continue
                tc = TURN[turn]
            else:
                tc = 0.0
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx < W and 0 <= jy < H):
                continue
            j = jy * W + jx
            if not U[j]:
                continue
            if dx and dy and not (U[iy * W + jx] and U[jy * W + ix]):
                continue
            ng = gc + (1.41421 if dx and dy else 1.0) * P * lc * (CC[j] if CC is not None else 1.0) + tc
            ns = (li, j, nd)
            if ng < g.get(ns, 1e18):
                g[ns] = ng
                parent[ns] = s
                heapq.heappush(heap, (ng + h(jx, jy), ng, ns))
        if vok[i]:
            vc_i = via_cost * (vcost[i] if vcost is not None else 1.0)
            if i in tvs:
                ng = gc + vc_i
                if ng < g.get(VIA_END, 1e18):
                    g[VIA_END] = ng
                    parent[VIA_END] = s
                    heapq.heappush(heap, (ng, ng, VIA_END))
            for l2 in range(3):
                if l2 == li or not usable[l2][i]:
                    continue
                ns = (l2, i, 8)
                ng = gc + vc_i
                if ng < g.get(ns, 1e18):
                    g[ns] = ng
                    parent[ns] = s
                    heapq.heappush(heap, (ng + h(ix, iy), ng, ns))
    else:
        return None, False
    end_via = s == VIA_END
    if end_via:
        s = parent[s]
    path = []
    while s is not None:
        path.append((s[0], s[1]))
        s = parent[s]
    return path[::-1], end_via


# ------------------------------------------------------------------ exact check
class Checker:
    def __init__(self, ctx, skip=None):
        self.ctx = ctx
        self.cell = MM(2)
        self.skip = skip
        self.rebuild()

    def rebuild(self):
        self.d = defaultdict(list)
        for it in self.ctx.items:
            if self.skip and it.GetClass() == "PCB_TRACK" and it.m_Uuid.AsString() in self.skip:
                continue
            self.add(it)

    def add(self, it):
        for L in item_layers(it):
            self._put(L, it.GetEffectiveShape(L), it)
        if has_hole(it):
            self._put("HOLE", it.GetEffectiveHoleShape(), it)

    def _put(self, key, shape, it):
        bb = shape.BBox()
        c = self.cell
        e = (shape, it)
        for cx in range(bb.GetLeft() // c, bb.GetRight() // c + 1):
            for cy in range(bb.GetTop() // c, bb.GetBottom() // c + 1):
                self.d[(key, cx, cy)].append(e)

    def query(self, key, bb):
        c, seen = self.cell, set()
        for cx in range(bb.GetLeft() // c - 1, bb.GetRight() // c + 2):
            for cy in range(bb.GetTop() // c - 1, bb.GetBottom() // c + 2):
                for e in self.d.get((key, cx, cy), ()):
                    if id(e[1]) not in seen:
                        seen.add(id(e[1]))
                        yield e

    def edge_ok(self, shape, need):
        o = self.ctx.outline
        ch = o.Outline(0)
        n = ch.PointCount()
        for k in range(n):
            seg = pcbnew.SHAPE_SEGMENT(ch.CPoint(k), ch.CPoint((k + 1) % n), 0)
            if seg.Collide(shape, MM(need)):
                return False
        return o.Contains(shape.BBox().Centre())

    def rules_ok(self, shape, what):
        for z in self.ctx.rules:
            if what == "via" and not z.GetDoNotAllowVias():
                continue
            if what == "track" and not z.GetDoNotAllowTracks():
                continue
            if z.Outline().Collide(shape, MM(0.01)):
                return False
        return True

    def track_ok(self, a, e, wd, L, net):
        seg = pcbnew.SHAPE_SEGMENT(a, e, MM(wd))
        self.why = "borda ou area M2"
        if not self.rules_ok(seg, "track") or not self.edge_ok(seg, EDGE_CLR + 0.005):
            return False
        bb = seg.BBox()
        bb.Inflate(MM(0.5))
        for shape, it in self.query(L, bb):
            if it.GetNetname() == net and it.GetNetCode() != 0:
                continue
            c = max(clr_of(net), clr_of(it.GetNetname())) + 0.005
            if shape.Collide(seg, MM(c)):
                self.why = describe(it)
                return False
        for shape, it in self.query("HOLE", bb):
            if it.GetNetname() == net and it.GetNetCode() != 0:
                continue
            if shape.Collide(seg, MM(HOLE_CLR + 0.005)):
                self.why = "furo de " + describe(it)
                return False
        return True

    def via_ok(self, p, net):
        circ = pcbnew.SHAPE_CIRCLE(p, MM(VIA_D / 2))
        hole = pcbnew.SHAPE_CIRCLE(p, MM(VIA_DRILL / 2))
        if not self.rules_ok(circ, "via") or not self.edge_ok(circ, EDGE_CLR + 0.005):
            return False
        bb = circ.BBox()
        bb.Inflate(MM(0.5))
        for L in ALLCU:
            for shape, it in self.query(L, bb):
                if it.GetNetname() == net and it.GetNetCode() != 0:
                    if it.GetClass() == "PAD" and not it.HasHole() and not big_gnd_pad(it)                             and shape.Collide(circ, 0):
                        return False
                    continue
                c = max(clr_of(net), clr_of(it.GetNetname())) + 0.005
                if shape.Collide(circ, MM(c)):
                    return False
        for shape, it in self.query("HOLE", bb):
            if shape.Collide(hole, MM(HOLE2HOLE + 0.005)):
                return False
            if not (it.GetNetname() == net and it.GetNetCode() != 0) and shape.Collide(circ, MM(HOLE_CLR + 0.005)):
                return False
        return True


# ------------------------------------------------------------------ one connection
def route(ctx, chk, net, srcg, tgtg, tgt_in1, attempt, made, log):
    b = ctx.b
    widths, wmin, wthin = widths_for(net)
    margin = 0.03 if attempt == 1 else 0.0
    winm = 6.0 if attempt == 1 else 16.0
    sp = cluster_points(b, srcg)
    tp = cluster_points(b, tgtg) if tgtg is not None else np.zeros((0, 2))
    # nearest pair of points -> window
    if len(tp):
        best = None
        for k in range(0, len(sp)):
            d2 = ((tp - sp[k]) ** 2).sum(1)
            j = int(d2.argmin())
            if best is None or d2[j] < best[0]:
                best = (d2[j], sp[k], tp[j])
        _, pa, pb = best
        x0, x1 = min(pa[0], pb[0]) - winm, max(pa[0], pb[0]) + winm
        y0, y1 = min(pa[1], pb[1]) - winm, max(pa[1], pb[1]) + winm
    else:
        pa = sp.mean(0)
        x0, x1, y0, y1 = sp[:, 0].min() - winm, sp[:, 0].max() + winm, sp[:, 1].min() - winm, sp[:, 1].max() + winm
    bb = ctx.outline.BBox()
    x0, y0 = max(x0, TOMM(bb.GetLeft()) - 0.5), max(y0, TOMM(bb.GetTop()) - 0.5)
    x1, y1 = min(x1, TOMM(bb.GetRight()) + 0.5), min(y1, TOMM(bb.GetBottom()) + 0.5)
    area = (x1 - x0) * (y1 - y0)
    p = 0.05 if area < 900 else 0.1
    w = Win(x0, y0, x1, y1, p)
    blocked, vblock = build_masks(ctx, w, net, widths, margin)
    thin = thin_mask(ctx, w) if klass(net) == "Corrente" else None
    sm = cluster_mask(ctx, w, srcg, net)
    tm = cluster_mask(ctx, w, tgtg, net) if tgtg is not None else [np.zeros((w.H, w.W), bool)] * 3
    # thin only at the entry of the pins being joined (1 mm round their pads); Corrente goes
    # down to 0.3 there and to 0.15 in (and 0.6 mm round) the courtyards the .kicad_dru names
    pm = cluster_mask(ctx, w, srcg, net, True)
    if tgtg is not None:
        pm = [a | c for a, c in zip(pm, cluster_mask(ctx, w, tgtg, net, True))]
    near = dilate(pm[0] | pm[1] | pm[2], int(math.ceil((0.6 if klass(net) == "Corrente" else 1.0) / p)))
    if thin is not None:
        thin = dilate(thin, int(math.ceil(0.1 / p)))
    # per cell: widest free width; usable where >= the minimum allowed there
    usable, wcell, amins = [], [], []
    for li in range(3):
        best = np.zeros((w.H, w.W))
        for wd in sorted(widths):
            best = np.where(~blocked[(li, wd)], wd, best)
        allowed_min = np.full((w.H, w.W), wmin)
        if thin is not None:
            if NECK:
                allowed_min = np.where(near, 0.3, allowed_min)
            allowed_min = np.where(thin, wthin, allowed_min)
        else:
            allowed_min = np.where(near, wthin, allowed_min)
        u = best >= allowed_min - 1e-9
        usable.append(u)
        wcell.append(best)
        amins.append(allowed_min)
    vok = ~vblock
    tvia = None
    if tgt_in1:
        tvia = (vok & in1_mask(b, w)).ravel().tolist()
    if not any((sm[li] & usable[li]).any() for li in range(3)):
        return "sem saida no ponto de partida %s (folga)" % label(srcg)
    if not any((tm[li] & usable[li]).any() for li in range(3)) and not (tvia is not None and any(tvia)):
        return "sem entrada no ponto de chegada %s (folga)" % label(tgtg)
    lc = [1.0, 1.0 if net == "+3V3" else 1.4, 1.0]
    U = [u.ravel().tolist() for u in usable]
    # a narrowed cell costs four times a full-width one: thin only where it must be
    cc = [np.where(wcell[li] < wmin - 1e-9, 4.0, 1.0).ravel().tolist() for li in range(3)]
    path, end_via = astar(w, U, vok.ravel().tolist(), [m.ravel().tolist() for m in sm],
                          [m.ravel().tolist() for m in tm], tvia, lc, via_cost=1.5, cellcost=cc)
    if path is None:
        return "sem caminho (janela %.0fx%.0f mm, passo %.2f)" % (x1 - x0, y1 - y0, p)
    # path -> segments and vias
    pts = [(li, i % w.W, i // w.W) for li, i in path]
    vias = []
    runs, cur = [], [pts[0]]
    for q in pts[1:]:
        if q[0] != cur[-1][0]:
            vias.append((q[1], q[2]))
            runs.append(cur)
            cur = [q]
        else:
            cur.append(q)
    runs.append(cur)
    if end_via:
        vias.append((pts[-1][1], pts[-1][2]))
    segs = []
    for run in runs:
        li = run[0][0]
        k = 0
        while k < len(run) - 1:
            dx, dy = run[k + 1][1] - run[k][1], run[k + 1][2] - run[k][2]
            m = k + 1
            wd = min(wcell[li][run[k][2], run[k][1]], wcell[li][run[m][2], run[m][1]])
            while m + 1 < len(run) and (run[m + 1][1] - run[m][1], run[m + 1][2] - run[m][2]) == (dx, dy):
                wn = min(wd, wcell[li][run[m + 1][2], run[m + 1][1]])
                if wn != wd:
                    break
                m += 1
            wd = min(wd, max(widths))
            amin = min(amins[li][run[k][2], run[k][1]], amins[li][run[m][2], run[m][1]])
            segs.append((li, run[k][1:], run[m][1:], wd, amin))
            k = m
    # merge collinear pieces of equal width
    out = []
    for s in segs:
        if out:
            o = out[-1]
            if o[0] == s[0] and o[3] == s[3] and o[2] == s[1]:
                d1 = (o[2][0] - o[1][0], o[2][1] - o[1][1])
                d2 = (s[2][0] - s[1][0], s[2][1] - s[1][1])
                if d1[0] * d2[1] - d1[1] * d2[0] == 0 and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                    out[-1] = (o[0], o[1], s[2], o[3], min(o[4], s[4]))
                    continue
        out.append(s)
    # exact check, narrowing a piece if it must (never below what is allowed there)
    new = []
    for li, a, e, wd, amin in out:
        A = V(MM(w.xy(*a)[0]), MM(w.xy(*a)[1]))
        E = V(MM(w.xy(*e)[0]), MM(w.xy(*e)[1]))
        if A == E:
            continue
        ok = False
        for wt in [x for x in sorted(widths, reverse=True) if amin - 1e-9 <= x <= wd + 1e-9]:
            if chk.track_ok(A, E, wt, RL[li], net):
                ok = True
                break
        if not ok:
                return "conferencia exata falhou (trilha %s (%.2f;%.2f)-(%.2f;%.2f) toca %s)" % (
                LNAME[RL[li]], TOMM(A.x), TOMM(A.y), TOMM(E.x), TOMM(E.y), chk.why)
        new.append(("t", A, E, wt, RL[li]))
    for k1 in range(len(vias)):
        for k2 in range(k1 + 1, len(vias)):
            if math.hypot(vias[k1][0] - vias[k2][0], vias[k1][1] - vias[k2][1]) * w.p < VIA_DRILL + HOLE2HOLE + 0.01:
                return "duas vias da mesma rota coladas em (%.2f; %.2f)" % w.xy(*vias[k1])
    for vx, vy in vias:
        P_ = V(MM(w.xy(vx, vy)[0]), MM(w.xy(vx, vy)[1]))
        if not chk.via_ok(P_, net):
            return "conferencia exata falhou (via (%.2f;%.2f))" % (TOMM(P_.x), TOMM(P_.y))
        new.append(("v", P_))
    netinfo = b.FindNet(net)
    length, nv, wset = 0.0, 0, set()
    for n_ in new:
        if n_[0] == "t":
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(n_[1])
            t.SetEnd(n_[2])
            t.SetWidth(MM(n_[3]))
            t.SetLayer(n_[4])
            t.SetNet(netinfo)
            length += TOMM(t.GetLength())
            wset.add(n_[3])
        else:
            t = pcbnew.PCB_VIA(b)
            t.SetViaType(pcbnew.VIATYPE_THROUGH)
            t.SetPosition(n_[1])
            t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            try:
                t.SetWidth(MM(VIA_D))
            except TypeError:
                t.SetWidth(pcbnew.F_Cu, MM(VIA_D))
            t.SetDrill(MM(VIA_DRILL))
            t.SetNet(netinfo)
            nv += 1
        b.Add(t)
        chk.add(t)
        ctx.items.append(t)
        made.append(t.m_Uuid.AsString())
    log.append({"net": net, "de": [r2(pa[0]), r2(pa[1])],
                "ate": [r2(pb[0]), r2(pb[1])] if len(tp) else "In1 (via)",
                "comprimento_mm": round(length, 2), "larguras_mm": sorted(wset), "vias": nv,
                "camadas": sorted({LNAME[n_[4]] for n_ in new if n_[0] == "t"}),
                "tentativa": attempt})
    return None


# ------------------------------------------------------------------ per-net drivers
def describe(it):
    if it.GetClass() == "PAD":
        return "%s.%s [%s]" % (it.GetParentFootprint().GetReference(), it.GetNumber(), it.GetNetname())
    p = it.GetPosition() if it.GetClass() != "PCB_TRACK" else it.GetStart()
    return "%s [%s] (%.2f; %.2f)" % (it.GetClass().replace("PCB_", "").lower(), it.GetNetname(),
                                     TOMM(p.x), TOMM(p.y))


def label(g):
    pads = sorted("%s.%s" % (it.GetParentFootprint().GetReference(), it.GetNumber())
                  for it in g["items"] if it.GetClass() == "PAD")
    if pads:
        return pads[0]
    it = sorted(g["items"], key=lambda t: t.m_Uuid.AsString())[0]
    p = it.GetPosition() if it.GetClass() != "PCB_TRACK" else it.GetStart()
    return "%s (%.2f; %.2f)" % (it.GetClass().replace("PCB_", "").lower(), TOMM(p.x), TOMM(p.y))


def in_region(pt, reg):
    return reg is None or (reg[0] <= pt[0] <= reg[2] and reg[1] <= pt[1] <= reg[3])


def ident(g):
    return frozenset(it.m_Uuid.AsString() for it in g["items"])


def is_split(g, start):
    """True when this cluster holds part, but not all, of a cluster that existed at the start."""
    s = ident(g)
    return any(s & S and not S <= s for S in start)


def join_net(ctx, chk, net, region, made, log, fails, gnd_mode=False, start=None):
    """Join the clusters of a net. gnd_mode: every GND cluster without the In1 plane goes to it.
    region: only clusters/pairs there. start: only pieces split off clusters of this list."""
    b = ctx.b
    tried = defaultdict(int)
    for _round in range(80):
        gs = clusters(b, net)
        for g in gs:
            g["isl"] = zone_islands(b, g)
        if gnd_mode:
            main = [g for g in gs if has_in1(b, g)]
            todo = []
            for g in gs:
                if has_in1(b, g):
                    continue
                if start is not None and not is_split(g, start):
                    continue
                c = cluster_points(b, g)
                if len(c) and in_region(c.mean(0), region) and tried[label(g)] < 2:
                    todo.append(g)
            if not todo:
                return
            g = todo[0]
            key = label(g)
            tried[key] += 1
            err = route(ctx, chk, net, g, main[0] if main else None, True, tried[key], made, log)
            if err and tried[key] >= 2 and RIP is not None:
                err = RIP(ctx, chk, net, g, main[0] if main else None, True, made, log) or None
            if err and tried[key] >= 2:
                c = cluster_points(b, g).mean(0)
                fails.append({"net": net, "pinos": key, "em": [r2(c[0]), r2(c[1])], "motivo": err})
            continue
        if len(gs) < 2:
            return
        pts = [cluster_points(b, g) for g in gs]
        ids = [ident(g) for g in gs]
        pairs = []
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                # with `start`: only two pieces of what was one cluster when the lot began
                if start is not None and not any(S & ids[i] and S & ids[j] for S in start):
                    continue
                A, B_ = pts[i], pts[j]
                if not len(A) or not len(B_):
                    continue
                if len(A) * len(B_) > 4e6:
                    A = A[::max(1, len(A) // 2000)]
                    B_ = B_[::max(1, len(B_) // 2000)]
                d2 = ((A[:, None, :] - B_[None, :, :]) ** 2).sum(2)
                k = np.unravel_index(int(d2.argmin()), d2.shape)
                pa, pb = A[k[0]], B_[k[1]]
                if in_region(pa, region) and in_region(pb, region):
                    pairs.append((float(d2[k]), i, j, pa, pb))
        pairs.sort(key=lambda t: t[0])
        key = None
        for d, i, j, pa, pb in pairs:
            kk = tuple(sorted((label(gs[i]), label(gs[j]))))
            if tried[kk] < 2:
                key = (kk, i, j, pa, pb)
                break
        if key is None:
            return
        kk, i, j, pa, pb = key
        tried[kk] += 1
        # route from the smaller cluster to the bigger one
        a, c = (gs[i], gs[j]) if len(gs[i]["items"]) <= len(gs[j]["items"]) else (gs[j], gs[i])
        err = route(ctx, chk, net, a, c, False, tried[kk], made, log)
        if err and tried[kk] >= 2 and RIP is not None:
            err = RIP(ctx, chk, net, a, c, False, made, log) or None
        if err and tried[kk] >= 2:
            fails.append({"net": net, "pinos": "%s - %s" % kk, "de": [r2(pa[0]), r2(pa[1])],
                          "ate": [r2(pb[0]), r2(pb[1])], "motivo": err})


# ------------------------------------------------------------------ splice save
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


def block_uuid(blk):
    m = UUID_RE.search(blk)
    return m.group(1) if m else None


def is_rule_zone(blk):
    return "(keepout" in blk or "(rule_area" in blk


def save(b, original, drop_uuids, new_uuids):
    tmp = os.path.join(BUILD, "rota_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for f in os.listdir(BUILD):
        if f.startswith("rota_tmp") and not f.endswith(".kicad_pcb"):
            os.remove(os.path.join(BUILD, f))
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    _h, b_new, _t = top_blocks(new)
    h_old, b_old, t_old = top_blocks(original)
    new_items = [x for x in b_new if kind(x) in ("segment", "via") and block_uuid(x) in new_uuids]
    if len(new_items) != len(new_uuids):
        raise SystemExit("splice: %d new items in the saved copy, expected %d" % (len(new_items), len(new_uuids)))
    zones_new = {block_uuid(x): x for x in b_new if kind(x) == "zone"}
    out, placed, dropped, zrep = [], False, 0, 0
    for blk in b_old:
        k = kind(blk)
        if k in ("segment", "via", "arc") and block_uuid(blk) in drop_uuids:
            dropped += 1
            continue
        if k == "zone":
            if not placed:
                out.extend(new_items)
                placed = True
            if not is_rule_zone(blk):
                out.append(zones_new[block_uuid(blk)])
                zrep += 1
                continue
        out.append(blk)
    if not placed:
        raise SystemExit("splice: no zone block in the original file")
    text = h_old + "".join(out) + t_old
    # block-by-block check: everything but the new items and the refilled zones is identical
    _h2, b_chk, _t2 = top_blocks(text)
    keep_old = [x for x in b_old if not (kind(x) in ("segment", "via", "arc") and block_uuid(x) in drop_uuids)
                and not (kind(x) == "zone" and not is_rule_zone(x))]
    keep_new = [x for x in b_chk if not (kind(x) in ("segment", "via") and block_uuid(x) in new_uuids)
                and not (kind(x) == "zone" and not is_rule_zone(x))]
    if keep_old != keep_new:
        raise SystemExit("splice: unchanged blocks differ")
    open(BOARD, "w", encoding="utf-8", newline="").write(text)
    return {"dropped": dropped, "zones_refilled": zrep, "new": len(new_items), "blocks_identical": len(keep_old)}


# ------------------------------------------------------------------ DRC
def drc(tag):
    out = os.path.join(BUILD, "drc_rota_%s.json" % tag)
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all",
                    "--format", "json", "-o", out, BOARD], check=True, capture_output=True)
    return json.load(open(out, encoding="utf-8"))


def net_of(desc):
    m = re.search(r"\[([^\]]+)\]", desc)
    return m.group(1) if m else "?"


def drc_summary(d):
    v = defaultdict(int)
    for x in d.get("violations", []):
        v[x["type"]] += 1
    u = defaultdict(int)
    for x in d.get("unconnected_items", []):
        u[net_of(x["items"][0]["description"])] += 1
    return dict(v), dict(u), len(d.get("schematic_parity", []))


# ------------------------------------------------------------------ pictures
def picture(b, layer, made_ids, out, title):
    S = 8.0
    bb = b.GetBoardEdgesBoundingBox()
    ox, oy = bb.GetLeft() - MM(2), bb.GetTop() - MM(6)
    W = int(TOMM(bb.GetWidth() + MM(4)) * S)
    H = int(TOMM(bb.GetHeight() + MM(8)) * S)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)

    def P(v):
        return (TOMM(v.x - ox) * S, TOMM(v.y - oy) * S)

    def chain(ch):
        return [P(ch.CPoint(i)) for i in range(ch.PointCount())]

    outl = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outl, False)
    dr.polygon(chain(outl.Outline(0)), fill=(236, 236, 228), outline=(80, 80, 80))
    colours = {"GND": (170, 210, 240), "+3V3": (248, 205, 150)}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(layer):
            continue
        fp = z.GetFilledPolysList(layer)
        col = colours.get(z.GetNetname(), (200, 200, 200))
        for i in range(fp.OutlineCount()):
            dr.polygon(chain(fp.Outline(i)), fill=col)
            for h in range(fp.HoleCount(i)):
                dr.polygon(chain(fp.Hole(i, h)), fill=(236, 236, 228))
    for p in b.GetPads():
        if not p.IsOnLayer(layer):
            continue
        bbp = p.GetBoundingBox()
        a, z2 = P(V(bbp.GetLeft(), bbp.GetTop())), P(V(bbp.GetRight(), bbp.GetBottom()))
        dr.rectangle([a, z2], outline=(110, 110, 110))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetLayer() != layer:
            continue
        new = t.m_Uuid.AsString() in made_ids
        col = (220, 0, 0) if new else (90, 90, 90)
        w = max(1, int(TOMM(t.GetWidth()) * S))
        dr.line([P(t.GetStart()), P(t.GetEnd())], fill=col, width=w)
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        if t.m_Uuid.AsString() not in made_ids:
            continue
        x, y = P(t.GetPosition())
        r = VIA_D / 2 * S + 1
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(220, 0, 0), outline=(0, 0, 0))
    dr.text((8, 6), title + "  |  vermelho = trilhas e vias novas (rota restante), cinza = J, "
            "azul claro = GND, laranja claro = +3V3", fill=(0, 0, 0))
    img.save(out)


def pictures(m):
    b = pcbnew.LoadBoard(BOARD)
    made = {u for lot in m.get("lotes", {}).values() for u in lot.get("uuids", [])}
    for L, nm, tt in ((pcbnew.F_Cu, "cima", "F.Cu (cima)"),
                      (pcbnew.B_Cu, "baixo", "B.Cu (baixo, visto de cima, sem espelhar)"),
                      (pcbnew.In2_Cu, "in2", "In2.Cu")):
        picture(b, L, made, os.path.join(BUILD, "rota_%s.png" % nm), "eTutti Viaggio J1 - " + tt)


# ------------------------------------------------------------------ main
def main():
    os.makedirs(BUILD, exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    m = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"lotes": {}}
    if arg == "fotos":
        pictures(m)
        return
    if arg in LOT6:
        main6(arg, m)
        return
    lot = int(arg)
    spec = LOTS[lot]
    original = open(BOARD, encoding="utf-8", newline="").read()
    base = drc("lote%d_antes" % lot)
    v0, u0, _p0 = drc_summary(base)
    prev = m["lotes"].get(str(lot), {})
    drop = set(prev.get("uuids", []))

    b = pcbnew.LoadBoard(BOARD)
    tracks = list(b.GetTracks())
    gone = [t for t in tracks if t.m_Uuid.AsString() in drop]
    stub_removed = prev.get("toco_apagado")
    if lot == 5:
        net, xa, ya, xb, yb = STUB_OUT_K03
        hit = [t for t in tracks if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net
               and abs(TOMM(t.GetStart().x) - xa) < 0.01 and abs(TOMM(t.GetStart().y) - ya) < 0.01
               and abs(TOMM(t.GetEnd().x) - xb) < 0.01 and abs(TOMM(t.GetEnd().y) - yb) < 0.01]
        if len(hit) > 1:
            raise SystemExit("more than one OUT_K03 stub")
        if hit:
            stub_removed = hit[0].m_Uuid.AsString()
            gone.append(hit[0])
        elif not stub_removed:
            raise SystemExit("OUT_K03 stub not found")
        drop.add(stub_removed)
    for t in gone:
        b.Remove(t)
    del tracks

    if gone:
        # a re-run: the zones in the file were filled round what is now taken out
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    ctx = Ctx(b)
    chk = Checker(ctx)
    start = {n: [ident(g) for g in clusters(b, n)] for n in ("GND", "+3V3")}
    for tentativa_lote in range(4):
        made, log, fails = [], [], []
        for net in spec["nets"]:
            join_net(ctx, chk, net, None, made, log, fails)
        if spec["v33"]:
            join_net(ctx, chk, "+3V3", spec["v33"], made, log, fails)
        if spec["gnd"]:
            join_net(ctx, chk, "GND", spec["gnd"], made, log, fails, gnd_mode=True)

        # refill; GND / +3V3 pieces cut loose by the new tracks are part of the lot
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        extra = 0
        for _k in range(3):
            before = len(made)
            ctx.refresh()
            chk = Checker(ctx)
            join_net(ctx, chk, "GND", None, made, log, fails, gnd_mode=True, start=start["GND"])
            join_net(ctx, chk, "+3V3", None, made, log, fails, start=start["+3V3"])
            if len(made) == before:
                break
            extra += len(made) - before
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        # pieces still cut loose: protect the copper round their pads and do the lot again
        cut = []
        for n in ("GND", "+3V3"):
            gs = clusters(b, n)
            ids = [ident(g) for g in gs]
            for k, g in enumerate(gs):
                if n == "GND" and has_in1(b, g):
                    continue
                if not is_split(g, start[n]):
                    continue
                if n == "+3V3" and not any(S & ids[k] and S & ids[j] for S in start[n]
                                           for j in range(len(gs)) if j != k):
                    continue
                cut.append((n, g))
        if not cut:
            break
        r = 1.5 + 0.75 * tentativa_lote
        for n, g in cut:
            for it in g["items"]:
                if it.GetClass() != "PAD":
                    continue
                x0, y0, x1, y1 = bbox_mm(it)
                PROTECT.append({"rede": n, "pino": describe(it), "caixa": [x0 - r, y0 - r, x1 + r, y1 + r],
                                "camadas": [L for L in item_layers(it) if L in RL]})
        print("lote %d: %d pedaco(s) soltos, de novo com protecao %.2f mm: %s"
              % (lot, len(cut), r, [label(g) for _n, g in cut]))
        if tentativa_lote == 3:
            for n, g in cut:
                c = cluster_points(b, g).mean(0)
                fails.append({"net": n, "pinos": label(g), "em": [r2(c[0]), r2(c[1])],
                              "motivo": "pedaco de %s cortado pelas trilhas novas e nao religado" % n})
            break
        gone2 = [t for t in b.GetTracks() if t.m_Uuid.AsString() in set(made)]
        for t in gone2:
            b.Remove(t)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        ctx = Ctx(b)
        chk = Checker(ctx)

    info = save(b, original, drop, set(made))
    d = drc("lote%d" % lot)
    v1, u1, p1 = drc_summary(d)
    rec = {"txt": spec["txt"], "uuids": made, "ligacoes": log, "fora": fails,
           "toco_apagado": stub_removed, "gravacao": info,
           "drc_antes": {"violacoes": v0, "nao_roteadas": u0},
           "drc_depois": {"violacoes": v1, "nao_roteadas": u1, "paridade": p1},
           "vias_extra_ilhas": extra, "protecoes": PROTECT}
    m["lotes"][str(lot)] = rec
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: rec[k] for k in ("gravacao", "drc_antes", "drc_depois")}, indent=1))
    for x in log:
        print("ok  ", x)
    for x in fails:
        print("FORA", x)
    # track_width on our own new pieces: only Corrente necks (>= 0.3) at a pin entry, which
    # the .kicad_dru only allows inside six courtyards; they are listed, not hidden
    mine = {u for L_ in m["lotes"].values() for u in L_.get("uuids", [])}
    necks, tw_j = [], 0
    for x in d.get("violations", []):
        if x["type"] != "track_width":
            continue
        it = x["items"][0]
        if it.get("uuid") in mine:
            mw = re.search(r"actual ([0-9.]+) mm", x["description"])
            necks.append({"rede": net_of(it["description"]), "x": r2(it["pos"]["x"]), "y": r2(it["pos"]["y"]),
                          "largura": float(mw.group(1)) if mw else None,
                          "camada": it["description"].split(" on ")[1].split(",")[0]})
        else:
            tw_j += 1
    rec["afinamentos_entrada_pino"] = necks
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for x in necks:
        print("neck", x)
    v1 = dict(v1)
    v1["track_width"] = tw_j
    bad_neck = [x for x in necks if not x["largura"] or x["largura"] < 0.3 or klass(x["rede"]) != "Corrente"]
    allowed = {"track_width": 13, "track_dangling": 1 if lot < 5 else 0}
    bad = {k: n for k, n in v1.items() if n > allowed.get(k, 0)}
    if bad_neck:
        bad["track_width_novo"] = len(bad_neck)
    if bad:
        print("NEW DRC VIOLATIONS:", bad)
        sys.exit(1)


# ------------------------------------------------------------------ lot 6: closing (27 Oct 2026)
# Answers of the management to the 5 questions of "Rota restante" (COBRE.md), authorised by J:
#  * rip up and reroute ONLY the tracks that block the 11 open connections: J's +3V3 track in
#    B.Cu at x ~71.7 next to U204; the In2 tracks under the codec's exposed pad (U301.21) and
#    under C304; the tracks closing the pockets of R209.2, R211.2, C203.1, R206.1, R210.1 and
#    U202.10/11. Every ripped track is remade: same net and width, joining the same points;
#  * at least 2 GND vias (0.5/0.3) in U301.21;
#  * no part moves, nothing else is deleted.
# A ripped segment is cut only where it is in the way: its two ends stay as new segments (same
# net, width, layer, on its own line) and a detour of the same width joins the two cut points.
# Sub-lots: 6a U204 / charger, 6b codec, 6c what is left. A sub-lot is done once: to redo it,
# check the board out at the commit before it and drop its entry from rota_restante.json.
RIPC, RIPV = 25.0, 40.0          # A* cost factor of a cell / of a via that needs a rip
V33_U204 = ["aec31083-1f7b-4dc5-8cb3-358c01c0e2db", "c40a17e3-3c5d-466d-ab19-d537afde617b",
            "2a252c93-d6cb-4677-aef6-5241a5231d1a", "a4c0fa06-0fe6-4cf7-b05e-f5c8077415d7",
            "8c10bf73-8c0d-467d-8760-620d9198f542", "ac807682-fab9-4950-a4e4-5ece2d947b93"]
POCKETS = {
    # U202.10/11 (charger OUT): in 6c the power tracks round it may be ripped too
    "R210.1": {"box": 3.0}, "U202.10": {"box": 3.0, "box_6c": 5.0, "corrente_6c": True},
    "U202.11": {"box": 3.0, "box_6c": 5.0, "corrente_6c": True},
    "C203.1": {"box": 3.0}, "R206.1": {"box": 3.0}, "R209.2": {"box": 3.0},
    "R211.2": {"box": 3.0}, "C304.2": {"box": 2.0, "layers": [pcbnew.In2_Cu]},
}
LOT6 = {
    "6a": {"txt": "regiao do U204 e do carregador",
           "group": {"uuids": V33_U204, "nets": ["BB_L1", "BB_L2", "VSYS"], "region": (66, 5, 78, 14),
                     "txt": "+3V3 do J em B.Cu junto do U204 (x ~71,7)"},
           "nets": ["VSYS", "VBAT", "VBUS"], "gnd": (50, 3, 77, 22)},
    "6b": {"txt": "codec: vias no pad central do U301 e GND do C304", "codec": True, "nets": [],
           "gnd": (15, 30, 35, 40)},
    "6c": {"txt": "o que restou", "nets": ["BB_L1", "BB_L2", "VSYS", "VBAT", "VBUS"], "gnd": "all"},
}
ST = None


def seg_geom(t):
    a, e = t.GetStart(), t.GetEnd()
    return (TOMM(a.x), TOMM(a.y)), (TOMM(e.x), TOMM(e.y))


def proj(a, e, p):
    """(distance from p to the segment a-e, position of the nearest point along it in mm)."""
    dx, dy = e[0] - a[0], e[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return math.hypot(p[0] - a[0], p[1] - a[1]), 0.0
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L
    tc = min(max(t, 0.0), L)
    q = (a[0] + dx * tc / L, a[1] + dy * tc / L)
    return math.hypot(p[0] - q[0], p[1] - q[1]), tc


def seg_rec(t):
    a, e = seg_geom(t)
    return {"rede": t.GetNetname(), "camada": LNAME[t.GetLayer()], "largura": round(TOMM(t.GetWidth()), 3),
            "de": [round(a[0], 3), round(a[1], 3)], "ate": [round(e[0], 3), round(e[1], 3)],
            "comprimento_mm": round(TOMM(t.GetLength()), 3), "uuid": t.m_Uuid.AsString()}


def pads_of(g):
    return ["%s.%s" % (it.GetParentFootprint().GetReference(), it.GetNumber())
            for it in g["items"] if it.GetClass() == "PAD"]


def find_pad(b, lab):
    ref, num = lab.split(".")
    return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]


def new_track(b, net, L, A, E, wd):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(A)
    t.SetEnd(E)
    t.SetWidth(MM(wd))
    t.SetLayer(L)
    t.SetNet(b.FindNet(net))
    return t


def new_via(b, net, P):
    t = pcbnew.PCB_VIA(b)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetPosition(P)
    t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    try:
        t.SetWidth(MM(VIA_D))
    except TypeError:
        t.SetWidth(pcbnew.F_Cu, MM(VIA_D))
    t.SetDrill(MM(VIA_DRILL))
    t.SetNet(b.FindNet(net))
    return t


class St:
    """Lot 6 state: what was added and taken out, with undo back to a mark."""
    def __init__(self, ctx, chk, made, log):
        self.ctx, self.chk, self.made, self.log = ctx, chk, made, log
        self.removed, self.apagadas, self.desvios, self.rips = [], [], [], []
        self.codec = None

    def mark(self):
        return (len(self.made), len(self.log), len(self.removed), len(self.apagadas), len(self.desvios))

    def sync(self):
        self.ctx.refresh()
        self.chk.rebuild()

    def add(self, t):
        self.ctx.b.Add(t)
        self.made.append(t.m_Uuid.AsString())
        self.ctx.items.append(t)
        self.chk.add(t)

    def remove(self, t):
        self.apagadas.append(seg_rec(t))
        self.removed.append(t)
        self.ctx.b.Remove(t)

    def undo(self, mk):
        b = self.ctx.b
        newu = set(self.made[mk[0]:])
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in newu:
                b.Remove(t)
        del self.made[mk[0]:]
        del self.log[mk[1]:]
        for o in self.removed[mk[2]:]:
            b.Add(o)
        del self.removed[mk[2]:]
        del self.apagadas[mk[3]:]
        del self.desvios[mk[4]:]
        self.sync()


def cut(st, t, t0, t1):
    """Take segment t out and put back its two ends outside [t0, t1] (mm along it). Returns the
    detour job that must join the two cut points again."""
    b = st.ctx.b
    a, e = seg_geom(t)
    L = math.hypot(e[0] - a[0], e[1] - a[1])
    t0 = 0.0 if t0 < 0.25 else t0
    t1 = L if t1 > L - 0.25 else t1
    A0, E0 = t.GetStart(), t.GetEnd()
    A, E = V(A0.x, A0.y), V(E0.x, E0.y)

    def at(s):
        return V(A.x + (E.x - A.x) * s / L, A.y + (E.y - A.y) * s / L)
    P0 = A if t0 <= 0 else at(t0)
    P1 = E if t1 >= L else at(t1)
    net, lay, wd = t.GetNetname(), t.GetLayer(), round(TOMM(t.GetWidth()), 4)
    uu = t.m_Uuid.AsString()
    st.remove(t)
    rest = []
    if t0 > 0:
        r = new_track(b, net, lay, A, P0, wd)
        st.add(r)
        rest.append(r.m_Uuid.AsString())
    if t1 < L:
        r = new_track(b, net, lay, P1, E, wd)
        st.add(r)
        rest.append(r.m_Uuid.AsString())
    return {"net": net, "L": lay, "w": [wd], "P": [P0, P1], "orig": [uu], "restos": rest}


def touches(ctx, net, L, P):
    for it in ctx.items:
        if it.GetNetname() != net or not it.IsOnLayer(L):
            continue
        if it.GetEffectiveShape(L).Collide(P, 2000):
            return True
    return False


def merge_jobs(st, jobs):
    """Two cuts of one chain that meet at a point with no copper left become one detour."""
    def same(P, Q):
        return abs(P.x - Q.x) <= 2000 and abs(P.y - Q.y) <= 2000
    jobs = [dict(j) for j in jobs]
    again = True
    while again:
        again = False
        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                a, c = jobs[i], jobs[j]
                if (a["net"], a["L"]) != (c["net"], c["L"]):
                    continue
                for ea in (0, 1):
                    for ec in (0, 1):
                        if same(a["P"][ea], c["P"][ec]) and not touches(st.ctx, a["net"], a["L"], a["P"][ea]):
                            a["P"] = [a["P"][1 - ea], c["P"][1 - ec]]
                            a["orig"] = a["orig"] + c["orig"]
                            a["restos"] = a["restos"] + c["restos"]
                            a["w"] = a["w"] + c["w"]
                            del jobs[j]
                            again = True
                            break
                    if again:
                        break
                if again:
                    break
            if again:
                break
    return [j for j in jobs if not same(j["P"][0], j["P"][1])]


def run_segments(w, run, wcell, li):
    """Grid cells of one layer -> [(start xy, end xy, width)], straight pieces of one width."""
    out = []
    k = 0
    while k < len(run) - 1:
        dx, dy = run[k + 1][1] - run[k][1], run[k + 1][2] - run[k][2]
        wd = min(wcell[li][run[k][2], run[k][1]], wcell[li][run[k + 1][2], run[k + 1][1]])
        m = k + 1
        while m + 1 < len(run) and (run[m + 1][1] - run[m][1], run[m + 1][2] - run[m][2]) == (dx, dy) \
                and wcell[li][run[m + 1][2], run[m + 1][1]] >= wd:
            m += 1
        out.append((w.xy(run[k][1], run[k][2]), w.xy(run[m][1], run[m][2]), wd))
        k = m
    return out


def route_pts(st, jb, attempt):
    """Detour: join jb's two points with the ripped track's width (its narrower pin-entry width
    only within 1 mm of the two points)."""
    ctx, chk, b = st.ctx, st.chk, st.ctx.b
    net, L = jb["net"], jb["L"]
    wbig, wsmall = max(jb["w"]), min(jb["w"])
    widths = sorted({wbig, wsmall})
    margin = 0.03 if attempt == 1 else 0.0
    winm = 4.0 if attempt == 1 else 12.0
    p0 = (TOMM(jb["P"][0].x), TOMM(jb["P"][0].y))
    p1 = (TOMM(jb["P"][1].x), TOMM(jb["P"][1].y))
    bb = ctx.outline.BBox()
    x0 = max(min(p0[0], p1[0]) - winm, TOMM(bb.GetLeft()) - 0.5)
    y0 = max(min(p0[1], p1[1]) - winm, TOMM(bb.GetTop()) - 0.5)
    x1 = min(max(p0[0], p1[0]) + winm, TOMM(bb.GetRight()) + 0.5)
    y1 = min(max(p0[1], p1[1]) + winm, TOMM(bb.GetBottom()) + 0.5)
    p = 0.05 if (x1 - x0) * (y1 - y0) < 900 else 0.1
    w = Win(x0, y0, x1, y1, p)
    blocked, vblock = build_masks(ctx, w, net, widths, margin)
    li0 = RL.index(L)
    nearimg = w.img()
    for P_ in (p0, p1):
        w.disc(ImageDraw.Draw(nearimg), P_[0], P_[1], 1.0)
    near = np.array(nearimg, dtype=bool)
    sm = [np.zeros((w.H, w.W), bool) for _ in range(3)]
    tm = [np.zeros((w.H, w.W), bool) for _ in range(3)]
    s_img, t_img = w.img(), w.img()
    w.disc(ImageDraw.Draw(s_img), p0[0], p0[1], max(1.5 * p, wsmall / 2))
    w.disc(ImageDraw.Draw(t_img), p1[0], p1[1], max(1.5 * p, wsmall / 2))
    # an end point on a via (or a through pad) of the net may be left on any layer
    def on_via(P_):
        return any(it.GetNetname() == net and has_hole(it) and it.GetEffectiveShape(pcbnew.F_Cu).Collide(P_, 2000)
                   for it in ctx.items if it.GetClass() in ("PCB_VIA", "PAD"))
    for li in range(3):
        if li == li0 or on_via(jb["P"][0]):
            sm[li] = np.array(s_img, dtype=bool)
        if li == li0 or on_via(jb["P"][1]):
            tm[li] = np.array(t_img, dtype=bool)
    usable, wcell = [], []
    for li in range(3):
        big = ~blocked[(li, wbig)]
        small = ~blocked[(li, wsmall)] & near
        wc = np.where(big, wbig, np.where(small, wsmall, 0.0))
        # the two end points lie on the ripped track's own line: free for its width
        wc = np.where((sm[li] | tm[li]) & (wc == 0), wsmall, wc)
        usable.append(wc > 0)
        wcell.append(wc)
    lc = [1.0, 1.0 if net == "+3V3" else 1.4, 1.0]
    cc = [np.where(wcell[li] < wbig - 1e-9, 4.0, 1.0).ravel().tolist() for li in range(3)]
    path, _ = astar(w, [u.ravel().tolist() for u in usable], (~vblock).ravel().tolist(),
                    [m.ravel().tolist() for m in sm], [m.ravel().tolist() for m in tm], None, lc,
                    via_cost=1.5, cellcost=cc)
    if path is None:
        return "sem caminho (janela %.0fx%.0f mm)" % (x1 - x0, y1 - y0)
    pts = [(li, i % w.W, i // w.W) for li, i in path]
    runs, cur, vias = [], [pts[0]], []
    for q in pts[1:]:
        if q[0] != cur[-1][0]:
            runs.append(cur)
            vias.append(w.xy(q[1], q[2]))
            cur = [q]
        else:
            cur.append(q)
    runs.append(cur)
    pieces = []
    for k, run in enumerate(runs):
        li = run[0][0]
        segs = run_segments(w, run, wcell, li)
        first = w.xy(run[0][1], run[0][2])
        last = w.xy(run[-1][1], run[-1][2])
        if k == 0:
            segs = [(p0, first, wcell[li][run[0][2], run[0][1]])] + segs
        if k == len(runs) - 1:
            segs = segs + [(last, p1, wcell[li][run[-1][2], run[-1][1]])]
        pieces += [(RL[li], a, e, wd) for a, e, wd in segs]
    for k1 in range(len(vias)):
        for k2 in range(k1 + 1, len(vias)):
            if math.hypot(vias[k1][0] - vias[k2][0], vias[k1][1] - vias[k2][1]) < VIA_DRILL + HOLE2HOLE + 0.01:
                return "duas vias do desvio coladas"
    new = []
    for lay, a, e, wd in pieces:
        A, E = V(MM(a[0]), MM(a[1])), V(MM(e[0]), MM(e[1]))
        if A == E:
            continue
        if not chk.track_ok(A, E, wd, lay, net):
            return "conferencia exata falhou (%s (%.2f;%.2f)-(%.2f;%.2f) toca %s)" % (
                LNAME[lay], a[0], a[1], e[0], e[1], chk.why)
        new.append(("t", lay, A, E, wd))
    for vx, vy in vias:
        P_ = V(MM(vx), MM(vy))
        if not chk.via_ok(P_, net):
            return "conferencia exata falhou (via (%.2f;%.2f))" % (vx, vy)
        new.append(("v", P_))
    length, nv, lays, uu = 0.0, 0, set(), []
    for n_ in new:
        if n_[0] == "t":
            t = new_track(b, net, n_[1], n_[2], n_[3], n_[4])
            length += TOMM(t.GetLength())
            lays.add(LNAME[n_[1]])
        else:
            t = new_via(b, net, n_[1])
            nv += 1
        st.add(t)
        uu.append(t.m_Uuid.AsString())
    st.desvios.append({"rede": net, "larguras": sorted(set(jb["w"])), "camada_original": LNAME[L],
                       "de": [r2(p0[0]), r2(p0[1])], "ate": [r2(p1[0]), r2(p1[1])],
                       "comprimento_mm": round(length, 2), "camadas": sorted(lays), "vias": nv,
                       "substitui": jb["orig"], "restos": jb["restos"], "uuids": uu, "tentativa": attempt})
    return None


def detours(st, jobs):
    for jb in jobs:
        err = None
        for attempt in (1, 2):
            err = route_pts(st, jb, attempt)
            if not err:
                break
        if err:
            return "desvio de %s (%s, %s) nao fechou: %s" % (jb["net"], LNAME[jb["L"]], jb["orig"][0][:8], err)
    return None


def pocket_sel(ctx, net, gs, st):
    made = set(st.made)
    labs = set()
    for g in gs:
        if g is not None:
            labs.update(pads_of(g))
    labs = sorted(labs & set(POCKETS))
    sel = set()
    for lab in labs:
        P = POCKETS[lab]
        q = find_pad(ctx.b, lab).GetPosition()
        late = st.sub == "6c"
        qx, qy = TOMM(q.x), TOMM(q.y)
        r = P.get("box_6c", P["box"]) if late else P["box"]
        power = late and P.get("corrente_6c", False)
        for t in ctx.items:
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() == net:
                continue
            if not power and (klass(t.GetNetname()) == "Corrente" or TOMM(t.GetWidth()) > 0.3):
                continue
            if "layers" in P and t.GetLayer() not in P["layers"]:
                continue
            u = t.m_Uuid.AsString()
            if u in made:
                continue
            x0, y0, x1, y1 = bbox_mm(t)
            if x1 < qx - r or x0 > qx + r or y1 < qy - r or y0 > qy + r:
                continue
            sel.add(u)
    return sel, labs


def rip_search(ctx, net, srcg, tgtg, tgt_in1, attempt, ripids):
    """A* where the authorised tracks may be crossed at a high cost. Returns {uuid: [(t, r)]}:
    where (mm along the track) the path needs it gone, and the radius it needs round there."""
    b = ctx.b
    widths, wmin, wthin = widths_for(net)
    margin = 0.03 if attempt == 1 else 0.0
    winm = 6.0 if attempt == 1 else 16.0
    sp = cluster_points(b, srcg)
    tp = cluster_points(b, tgtg) if (tgtg is not None and not tgt_in1) else np.zeros((0, 2))
    if len(tp):
        A_, B_ = sp, tp
        if len(A_) * len(B_) > 4e6:
            A_, B_ = A_[::max(1, len(A_) // 2000)], B_[::max(1, len(B_) // 2000)]
        d2 = ((A_[:, None, :] - B_[None, :, :]) ** 2).sum(2)
        k = np.unravel_index(int(d2.argmin()), d2.shape)
        pa, pb = A_[k[0]], B_[k[1]]
        x0, x1 = min(pa[0], pb[0]) - winm, max(pa[0], pb[0]) + winm
        y0, y1 = min(pa[1], pb[1]) - winm, max(pa[1], pb[1]) + winm
    else:
        x0, x1, y0, y1 = sp[:, 0].min() - winm, sp[:, 0].max() + winm, sp[:, 1].min() - winm, sp[:, 1].max() + winm
    bb = ctx.outline.BBox()
    x0, y0 = max(x0, TOMM(bb.GetLeft()) - 0.5), max(y0, TOMM(bb.GetTop()) - 0.5)
    x1, y1 = min(x1, TOMM(bb.GetRight()) + 0.5), min(y1, TOMM(bb.GetBottom()) + 0.5)
    p = 0.05 if (x1 - x0) * (y1 - y0) < 900 else 0.1
    w = Win(x0, y0, x1, y1, p)
    hard, hv = build_masks(ctx, w, net, widths, margin, skip=ripids)
    full, fv = build_masks(ctx, w, net, widths, margin)
    thin = thin_mask(ctx, w) if klass(net) == "Corrente" else None
    if thin is not None:
        thin = dilate(thin, int(math.ceil(0.1 / p)))
    sm = cluster_mask(ctx, w, srcg, net)
    tm = cluster_mask(ctx, w, tgtg, net) if (tgtg is not None and not tgt_in1) else [np.zeros((w.H, w.W), bool)] * 3
    pm = cluster_mask(ctx, w, srcg, net, True)
    if tgtg is not None and not tgt_in1:
        pm = [a | c for a, c in zip(pm, cluster_mask(ctx, w, tgtg, net, True))]
    near = dilate(pm[0] | pm[1] | pm[2], int(math.ceil((0.6 if klass(net) == "Corrente" else 1.0) / p)))

    def cells(blk):
        us, wc = [], []
        for li in range(3):
            best = np.zeros((w.H, w.W))
            for wd in sorted(widths):
                best = np.where(~blk[(li, wd)], wd, best)
            amin = np.full((w.H, w.W), wmin)
            if thin is not None:
                if NECK:
                    amin = np.where(near, 0.3, amin)
                amin = np.where(thin, wthin, amin)
            else:
                amin = np.where(near, wthin, amin)
            us.append(best >= amin - 1e-9)
            wc.append(best)
        return us, wc
    uh, wh = cells(hard)
    uf, _wf = cells(full)
    rip = [uh[li] & ~uf[li] for li in range(3)]
    vok = ~hv
    tvia = (vok & in1_mask(b, w)).ravel().tolist() if tgt_in1 else None
    if not any((sm[li] & uh[li]).any() for li in range(3)):
        return None, "sem saida no ponto de partida mesmo arrancando trilhas"
    cc = [(np.where(wh[li] < wmin - 1e-9, 4.0, 1.0) * np.where(rip[li], RIPC, 1.0)).ravel().tolist()
          for li in range(3)]
    vc = np.where(fv, RIPV, 1.0).ravel().tolist()
    lc = [1.0, 1.0 if net == "+3V3" else 1.4, 1.0]
    path, end_via = astar(w, [u.ravel().tolist() for u in uh], vok.ravel().tolist(),
                          [m.ravel().tolist() for m in sm], [m.ravel().tolist() for m in tm], tvia, lc,
                          via_cost=1.5, cellcost=cc, vcost=vc)
    if path is None:
        return None, "sem caminho mesmo arrancando as trilhas autorizadas (janela %.0fx%.0f mm)" % (x1 - x0, y1 - y0)
    geo = []
    for t in ctx.items:
        if t.GetClass() == "PCB_TRACK" and t.m_Uuid.AsString() in ripids:
            a, e = seg_geom(t)
            geo.append((t.m_Uuid.AsString(), a, e, t.GetLayer(), TOMM(t.GetWidth()) / 2,
                        max(clr_of(net), clr_of(t.GetNetname()))))
    hits = defaultdict(list)
    W = w.W
    for li, i in path:
        if not rip[li].flat[i]:
            continue
        ix, iy = i % W, i // W
        x, y = w.xy(ix, iy)
        wd = min(wh[li][iy, ix], max(widths))
        for u, a, e, L, hw, c in geo:
            if L != RL[li]:
                continue
            d, tt = proj(a, e, (x, y))
            if d < hw + c + wd / 2 + margin + SLACK + 1.5 * p:
                hits[u].append((tt, wd / 2 + c))
    vcells = [path[k] for k in range(1, len(path)) if path[k][0] != path[k - 1][0]]
    if end_via:
        vcells.append(path[-1])
    for li, i in vcells:
        if not fv.flat[i]:
            continue
        x, y = w.xy(i % W, i // W)
        for u, a, e, L, hw, c in geo:
            d, tt = proj(a, e, (x, y))
            if d < hw + c + VIA_D / 2 + margin + SLACK + 1.5 * p:
                hits[u].append((tt, VIA_D / 2 + c))
    return dict(hits), None


def rip_route(ctx, chk, net, srcg, tgtg, tgt_in1, made, log):
    """A connection that failed twice: rip up only the authorised tracks in its way, route it,
    then remake every ripped track by a detour. Two attempts; all or nothing."""
    st = ST
    sel, labs = pocket_sel(ctx, net, [srcg] + ([] if tgt_in1 else [tgtg]), st)
    if not sel:
        return "sem trilhas autorizadas para arrancar"
    last = None
    for attempt in (1, 2):
        hits, err = rip_search(ctx, net, srcg, tgtg, tgt_in1, attempt, sel)
        if err:
            last = err
            continue
        mk = st.mark()
        byu = {t.m_Uuid.AsString(): t for t in ctx.items if t.GetClass() == "PCB_TRACK"}
        jobs = []
        for u, lst in hits.items():
            t = byu[u]
            ext = TOMM(t.GetWidth()) / 2 + max(r for _, r in lst) + 0.4
            jobs.append(cut(st, t, min(tt for tt, _ in lst) - ext, max(tt for tt, _ in lst) + ext))
        st.sync()
        jobs = merge_jobs(st, jobs)
        err = route(ctx, st.chk, net, srcg, tgtg, tgt_in1, attempt, made, log)
        if err:
            st.undo(mk)
            last = "com %d trilha(s) arrancada(s): %s" % (len(hits), err)
            continue
        err = detours(st, jobs)
        if err:
            st.undo(mk)
            last = err
            continue
        st.rips.append({"rede": net, "pinos": labs, "tentativa": attempt,
                        "apagadas": st.apagadas[mk[3]:], "desvios": st.desvios[mk[4]:]})
        print("  rip ok: %s %s, %d trilha(s) arrancada(s) e refeita(s)" % (net, labs, len(hits)))
        return None
    print("  rip falhou: %s %s: %s" % (net, labs, last))
    return last


def group_rip(st, grp, fails):
    """J's +3V3 track next to U204: out first, the three connections it closed, then its detour
    (or the detour first, on the 2nd attempt)."""
    global RIP
    ctx = st.ctx
    RIP = None
    last = None
    for attempt in (1, 2):
        mk = st.mark()
        f0 = len(fails)
        byu = {t.m_Uuid.AsString(): t for t in ctx.items if t.GetClass() == "PCB_TRACK"}
        if any(u not in byu for u in grp["uuids"]):
            raise SystemExit("group: a track of the +3V3 chain is missing")
        jobs = [cut(st, byu[u], 0.0, 1e9) for u in grp["uuids"]]
        st.sync()
        jobs = merge_jobs(st, jobs)
        if attempt == 2:
            err = detours(st, jobs)
            if err:
                st.undo(mk)
                last = err
                break
        nlog = len(st.log)
        for net in grp["nets"]:
            join_net(ctx, st.chk, net, grp["region"], st.made, st.log, fails)
        closed = st.log[nlog:]
        err = detours(st, jobs) if attempt == 1 else None
        if err or not closed:
            st.undo(mk)
            del fails[f0:]
            last = err or "nenhuma ligacao fechou"
            continue
        st.rips.append({"rede": ",".join(grp["nets"]), "pinos": grp["txt"], "tentativa": attempt,
                        "apagadas": st.apagadas[mk[3]:], "desvios": st.desvios[mk[4]:],
                        "fechadas": [x["net"] for x in closed]})
        print("  grupo ok (tentativa %d): %s" % (attempt, [x["net"] for x in closed]))
        return
    for net in grp["nets"]:
        fails.append({"net": net, "pinos": grp["txt"], "motivo": "trilha de +3V3 sem desvio: %s" % last})


def codec_vias(st):
    """At least 2 GND vias in the codec's exposed pad U301.21; the In2 tracks under it that are in
    the way are cut there and remade around."""
    ctx, b = st.ctx, st.ctx.b
    pad = find_pad(b, "U301.21")
    c = pad.GetPosition()
    cx, cy = TOMM(c.x), TOMM(c.y)
    sz = pad.GetSize(pcbnew.B_Cu)
    hx, hy = TOMM(sz.x) / 2 - VIA_D / 2 - 0.02, TOMM(sz.y) / 2 - VIA_D / 2 - 0.02
    x0, y0, x1, y1 = bbox_mm(pad)
    made = set(st.made)
    rip = {}
    for t in ctx.items:
        if t.GetClass() != "PCB_TRACK" or t.GetLayer() != pcbnew.In2_Cu or t.GetNetname() == "GND":
            continue
        u = t.m_Uuid.AsString()
        bx0, by0, bx1, by1 = bbox_mm(t)
        if u in made or bx1 < x0 - 1 or bx0 > x1 + 1 or by1 < y0 - 1 or by0 > y1 + 1:
            continue
        rip[u] = t
    soft = Checker(ctx, skip=set(rip))

    def conflicts(px, py):
        out = set()
        for u, t in rip.items():
            a, e = seg_geom(t)
            R = TOMM(t.GetWidth()) / 2 + max(clr_of("GND"), clr_of(t.GetNetname())) + VIA_D / 2 + 0.03
            if proj(a, e, (px, py))[0] < R:
                out.add(u)
        return frozenset(out)
    cands = []
    nx, ny = int(hx / 0.025), int(hy / 0.025)
    for ix in range(-nx, nx + 1):
        for iy in range(-ny, ny + 1):
            px, py = cx + ix * 0.025, cy + iy * 0.025
            if soft.via_ok(V(MM(px), MM(py)), "GND"):
                cands.append(((px, py), conflicts(px, py)))
    if not cands:
        return "nenhum ponto de via no pad, mesmo sem as trilhas do In2"
    sets = sorted({cf for _, cf in cands}, key=lambda s: (len(s), -sum(1 for _, cf in cands if cf <= s)))
    # two via sets (fewest In2 tracks in the way first); each with the tracks cut only round the
    # vias, then cut whole (a detour from a short cut can be shut in by its neighbours)
    plan = [(S, mode) for S in sets for mode in ("local", "inteira")]
    tries, last, nset = 0, None, 0
    for S, mode in plan:
        pool = [q for q, cf in cands if cf <= S]
        chosen = [min(pool, key=lambda q: math.hypot(q[0] - cx, q[1] - cy))]
        while len(chosen) < 4:
            best = max(pool, key=lambda q: min(math.hypot(q[0] - o[0], q[1] - o[1]) for o in chosen))
            if min(math.hypot(best[0] - o[0], best[1] - o[1]) for o in chosen) < VIA_DRILL + HOLE2HOLE + 0.05:
                break
            chosen.append(best)
        if len(chosen) < 2:
            continue
        if mode == "local":
            nset += 1
            if nset > 2:
                break
        tries += 1
        mk = st.mark()
        jobs = []
        for u in S:
            t = rip[u]
            a, e = seg_geom(t)
            R = TOMM(t.GetWidth()) / 2 + max(clr_of("GND"), clr_of(t.GetNetname())) + VIA_D / 2
            ts = [proj(a, e, q)[1] for q in chosen if proj(a, e, q)[0] < R + 0.03]
            if mode == "local":
                jobs.append(cut(st, t, min(ts) - R - 0.4, max(ts) + R + 0.4))
            else:
                jobs.append(cut(st, t, 0.0, 1e9))
        st.sync()
        jobs = merge_jobs(st, jobs)
        ok = True
        for q in chosen:
            P_ = V(MM(q[0]), MM(q[1]))
            if not st.chk.via_ok(P_, "GND"):
                ok = False
                break
            st.add(new_via(b, "GND", P_))
        err = None if ok else "via no pad recusada na conferencia exata"
        if ok:
            err = detours(st, jobs)
        print("  codec tentativa %d (%s, vias %s, trilhas %s): %s" % (
            tries, mode, [[round(q[0], 2), round(q[1], 2)] for q in chosen],
            sorted(rip[u].GetNetname() for u in S), err or "ok"))
        if err:
            st.undo(mk)
            last = err
            continue
        st.codec = {"vias": [[round(q[0], 3), round(q[1], 3)] for q in chosen], "corte": mode,
                    "apagadas": st.apagadas[mk[3]:], "desvios": st.desvios[mk[4]:], "tentativa": tries}
        st.rips.append({"rede": "GND", "pinos": ["U301.21"], "tentativa": tries,
                        "apagadas": st.apagadas[mk[3]:], "desvios": st.desvios[mk[4]:]})
        print("  codec: %d vias em U301.21 %s, %d trilha(s) do In2 refeita(s)" % (len(chosen), st.codec["vias"], len(S)))
        return None
    return last or "nenhum conjunto de 2 vias"


def main6(sub, m):
    global RIP, NECK, ST
    NECK = False
    spec = LOT6[sub]
    if sub in m["lotes"]:
        raise SystemExit("sublote %s ja feito: para refazer, volte o .kicad_pcb ao commit anterior "
                         "e tire a entrada dele do rota_restante.json" % sub)
    original = open(BOARD, encoding="utf-8", newline="").read()
    base = drc("lote%s_antes" % sub)
    v0, u0, p0 = drc_summary(base)
    b = pcbnew.LoadBoard(BOARD)
    ctx = Ctx(b)
    chk = Checker(ctx)
    made, log, fails = [], [], []
    st = St(ctx, chk, made, log)
    st.sub = sub
    ST = st
    start = {n: [ident(g) for g in clusters(b, n)] for n in ("GND", "+3V3")}
    if spec.get("group"):
        group_rip(st, spec["group"], fails)
    RIP = rip_route
    if spec.get("codec"):
        err = codec_vias(st)
        if err:
            fails.append({"net": "GND", "pinos": "U301.21", "em": [24.0, 35.5], "motivo": err})
    for net in spec["nets"]:
        join_net(ctx, st.chk, net, None, made, log, fails)
    if spec.get("gnd"):
        join_net(ctx, st.chk, "GND", None if spec["gnd"] == "all" else spec["gnd"], made, log, fails,
                 gnd_mode=True)
    RIP = None
    # refill; GND / +3V3 pieces cut loose are joined here
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    extra = 0
    for _k in range(3):
        before = len(made)
        st.sync()
        join_net(ctx, st.chk, "GND", None, made, log, fails, gnd_mode=True, start=start["GND"])
        join_net(ctx, st.chk, "+3V3", None, made, log, fails, start=start["+3V3"])
        if len(made) == before:
            break
        extra += len(made) - before
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for n in ("GND", "+3V3"):
        gs = clusters(b, n)
        ids = [ident(g) for g in gs]
        for k, g in enumerate(gs):
            if n == "GND" and has_in1(b, g):
                continue
            if not is_split(g, start[n]):
                continue
            if n == "+3V3" and not any(S & ids[k] and S & ids[j] for S in start[n]
                                       for j in range(len(gs)) if j != k):
                continue
            cc_ = cluster_points(b, g).mean(0)
            fails.append({"net": n, "pinos": label(g), "em": [r2(cc_[0]), r2(cc_[1])],
                          "motivo": "pedaco de %s cortado e nao religado" % n})
    drop = {r["uuid"] for r in st.apagadas}
    info = save(b, original, drop, set(made))
    d = drc("lote%s" % sub)
    v1, u1, p1 = drc_summary(d)
    rec = {"txt": spec["txt"], "uuids": made, "ligacoes": log, "fora": fails, "gravacao": info,
           "apagadas": st.apagadas, "desvios": st.desvios, "arrancadas_por_ligacao": st.rips,
           "codec": st.codec, "vias_extra_ilhas": extra,
           "drc_antes": {"violacoes": v0, "nao_roteadas": u0, "paridade": p0},
           "drc_depois": {"violacoes": v1, "nao_roteadas": u1, "paridade": p1}}
    m["lotes"][sub] = rec
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: rec[k] for k in ("gravacao", "drc_antes", "drc_depois")}, indent=1))
    for x in log:
        print("ok  ", x)
    for x in st.apagadas:
        print("apagada", x)
    for x in st.desvios:
        print("desvio", {k: x[k] for k in ("rede", "larguras", "de", "ate", "comprimento_mm", "camadas", "vias")})
    for x in fails:
        print("FORA", x)
    bad = {}
    for k, n in v1.items():
        lim = 13 if k == "track_width" else v0.get(k, 0)
        if n > lim:
            bad[k] = n
    worse = {n: u1.get(n, 0) for n in set(u0) | set(u1) if u1.get(n, 0) > u0.get(n, 0)}
    if worse:
        bad["nao_roteadas_a_mais"] = worse
    if p1:
        bad["paridade"] = p1
    if bad:
        print("NEW DRC PROBLEMS:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
