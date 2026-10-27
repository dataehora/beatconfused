"""eTutti Viaggio J1 -- route the connections still open on J's board, lot by lot.

Run with KiCad 10's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/rota_restante.py <lot>
    (<lot> = 1..5, or "fotos" for the pictures only)

Lots (task of 27 Oct 2026, authorised by J):
  1  BB_L1, BB_L2, VSYS, VBAT and the GND islands of the charger / converter (x 50-76, y 3-21)
  2  VBUS
  3  GND of the codec (U301.21, C304.2), I2C_SDA, I2C_SCL and the +3V3 left of the keyboard
  4  the +3V3 pockets in the keyboard (x >= 95)
  5  OUT_K03 (its loose stub at (118.97; 8.45) is deleted first)

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
THIN_REFS = ("J201", "U202", "U204", "J202", "U501", "J101")
PROTECT = []
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


def build_masks(ctx, w, net, widths, margin):
    """Blocked masks for the net being routed: per routing layer and width; plus via mask."""
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


def astar(w, usable, vok, src, tgt, tvia, layer_cost, via_cost, max_expand=4_000_000, cellcost=None):
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
            if i in tvs:
                ng = gc + via_cost
                if ng < g.get(VIA_END, 1e18):
                    g[VIA_END] = ng
                    parent[VIA_END] = s
                    heapq.heappush(heap, (ng, ng, VIA_END))
            for l2 in range(3):
                if l2 == li or not usable[l2][i]:
                    continue
                ns = (l2, i, 8)
                ng = gc + via_cost
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
    def __init__(self, ctx):
        self.ctx = ctx
        self.cell = MM(2)
        self.d = defaultdict(list)
        for it in ctx.items:
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


if __name__ == "__main__":
    main()
