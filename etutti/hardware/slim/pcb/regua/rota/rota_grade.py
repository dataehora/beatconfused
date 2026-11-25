"""Stage 2 (own router): the signals of the ruler on a 0.1 mm grid, two layers. KiCad python (pcbnew + numpy), deterministic.

    "C:/Program Files/KiCad/10.0/bin/python.exe" rota_grade.py [in.kicad_pcb] [out.kicad_pcb] [--order=NET,NET,...]

Same idea as the grid router of etutti/hardware/build_pcb.py (A* over cells that no other net claims, turn and via costs, a net only ever joins its own copper tree),
rewritten over numpy masks because the ruler has 0.5 mm pitch parts: grid 0.1 mm aligned to the pad centres, track 0.2, clearance 0.15 (claim radius 0.25 from other
copper), via 0.6/0.3 (claim 0.45), NPTH holes 0.25 + 0.38, outline 0.45. OUT is kept 1.2 mm (centre to centre = 1.0 mm edge to edge) from DATA/CLK/LATCH copper
outside the FFC zone. No part is moved; nothing is written but the output board. A net that fails goes first and the run starts again (up to RETRIES times).
"""
import heapq, json, math, os, sys, time
import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
G = 0.1                      # grid pitch (mm)
TW, CLR, VD, VDR = (float(os.environ.get("R_TW", 0.2)), float(os.environ.get("R_CLR", 0.15)), float(os.environ.get("R_VD", 0.6)), 0.3)
R_T = CLR + TW / 2           # centre-line claim of copper for other nets' tracks
R_V = CLR + VD / 2           # ... for other nets' vias
R_OUTWARD = 1.2              # OUT centre to DATA/CLK/LATCH copper centre (edge to edge 1.0 + 0.2)
EDGE = 0.45
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
LAYER_COST = [1.5, 1.0]
LAYER_COST_EN = [float(os.environ.get("R_ENF", 1.0)), float(os.environ.get("R_ENB", 2.0))]     # the EN lanes prefer the top face (the placement plan)
VIA_COST = 3.0
TURN = {0: 0.0, 1: 0.1, 2: 0.4}
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
FREE, HARD = -1, -2
FFC_X = 25.6                 # right edge of the "Zona FFC" rule area
mm = pcbnew.ToMM
M = pcbnew.FromMM
DIGITAL = ("DATA", "CLK", "LATCH")
HW = float(os.environ.get("R_HW", 1.5))     # weighted A*: the search of a 150 mm lane would flood the 15 mm wide board otherwise
RETRIES = int(os.environ.get("R_RETRIES", 6))
MAXEXP = int(os.environ.get("R_MAXEXP", 1_500_000))


class Grid:
    def __init__(self, x0, y0, x1, y1):
        self.ox, self.oy = x0, y0
        self.W, self.H = int(round((x1 - x0) / G)) + 1, int(round((y1 - y0) / G)) + 1
        self.T = [np.full((self.H, self.W), FREE, np.int16) for _ in LAYERS]     # claims for tracks
        self.V = [np.full((self.H, self.W), FREE, np.int16) for _ in LAYERS]     # claims for vias
        self.NOVIA = np.zeros((self.H, self.W), bool)
        self.KA = [np.full((self.H, self.W), FREE, np.int16) for _ in LAYERS]    # digital copper claim (for OUT only)
        xs = self.ox + np.arange(self.W) * G
        ys = self.oy + np.arange(self.H) * G
        self.X, self.Y = np.meshgrid(xs, ys)

    def cell(self, x, y):
        return int(round((x - self.ox) / G)), int(round((y - self.oy) / G))

    def window(self, x0, y0, x1, y1, r):
        ix0 = max(0, int((x0 - r - self.ox) / G))
        ix1 = min(self.W - 1, int((x1 + r - self.ox) / G) + 1)
        iy0 = max(0, int((y0 - r - self.oy) / G))
        iy1 = min(self.H - 1, int((y1 + r - self.oy) / G) + 1)
        return slice(iy0, iy1 + 1), slice(ix0, ix1 + 1)

    @staticmethod
    def claim(arr, win, mask, nid):
        cur = arr[win]
        new = np.where(mask & (cur == FREE), nid, cur)
        new = np.where(mask & (cur != FREE) & (cur != nid), HARD, new)
        arr[win] = new.astype(np.int16)

    def rect(self, layers, x0, y0, x1, y1, nid, rt=R_T, rv=R_V, novia=0.0):
        win = self.window(x0, y0, x1, y1, max(rt, rv, novia))
        X, Y = self.X[win], self.Y[win]
        d = np.hypot(np.maximum(np.maximum(x0 - X, 0), X - x1), np.maximum(np.maximum(y0 - Y, 0), Y - y1))
        for li in layers:
            self.claim(self.T[li], win, d < rt, nid)
            self.claim(self.V[li], win, d < rv, nid)
        if novia:
            self.NOVIA[win] |= d < novia

    def circle(self, layers, cx, cy, r0, nid, rt=R_T, rv=R_V):
        win = self.window(cx, cy, cx, cy, max(rt, rv) + r0)
        d = np.hypot(self.X[win] - cx, self.Y[win] - cy) - r0
        for li in layers:
            self.claim(self.T[li], win, d < rt, nid)
            self.claim(self.V[li], win, d < rv, nid)

    def segment(self, li, ax, ay, bx, by, nid, hw=TW / 2):
        win = self.window(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), R_V + hw)
        X, Y = self.X[win], self.Y[win]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-12
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) - hw
        self.claim(self.T[li], win, d < R_T, nid)
        self.claim(self.V[li], win, d < R_V, nid)

    def keepaway_seg(self, li, ax, ay, bx, by, nid):
        """cells whose centre is within R_OUTWARD of a digital centre-line (outside the FFC zone) are forbidden for OUT."""
        win = self.window(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), R_OUTWARD)
        X, Y = self.X[win], self.Y[win]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-12
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        self.claim(self.KA[li], win, (d < R_OUTWARD) & (X > FFC_X), nid)


def load(path):
    b = pcbnew.LoadBoard(path)
    nets = {}

    def nid(name):
        if name not in nets:
            nets[name] = len(nets)
        return nets[name]
    pads, holes, ko = [], [], []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            r = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                holes.append((mm(p.GetX()), mm(p.GetY()), mm(p.GetDrillSize().x) / 2))
                continue
            name = p.GetNetname()
            pads.append({"ref": fp.GetReference(), "num": p.GetNumber(), "net": name, "rect": r, "x": mm(p.GetX()), "y": mm(p.GetY()),
                         "layers": [i for i, L in enumerate(LAYERS) if p.IsOnLayer(L)]})
            nid(name)
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetZoneName().startswith("M2"):
            bb = z.GetBoundingBox()
            ko.append((mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())))
    fixed, fvias = [], []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            fvias.append((t.GetNetname(), mm(t.GetX()), mm(t.GetY()), mm(t.GetWidth(pcbnew.F_Cu))))
        else:
            fixed.append((t.GetNetname(), 0 if t.GetLayer() == pcbnew.F_Cu else 1, (mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth())))
    for name in [f[0] for f in fixed] + [v[0] for v in fvias]:
        nid(name)
    # virtual pads: the free (dangling) end of a fixed bus is where the head joins it
    ends = {}
    for net, li, a, e, w in fixed:
        for q in (a, e):
            ends.setdefault((net, li, round(q[0], 3), round(q[1], 3)), 0)
            ends[(net, li, round(q[0], 3), round(q[1], 3))] += 1
    for (net, li, x, y), cnt in ends.items():
        if net in ("OUT", "+3V3") and cnt == 1 and abs(x - 36.0) < 1e-3:
            pads.append({"ref": "BUS", "num": "ini", "net": net, "rect": (x - 0.1, y - 0.1, x + 0.1, y + 0.1), "x": x, "y": y, "layers": [li]})
    return b, nets, pads, holes, ko, fixed, fvias


def build_grid(pads, holes, ko, nets, fixed=(), fvias=()):
    g = Grid(20.05, 22.55, 179.95, 37.45)
    for li in range(2):
        for arr in (g.T[li], g.V[li]):
            arr[g.X < 20 + EDGE] = HARD
            arr[g.X > 180 - EDGE] = HARD
            arr[g.Y < 22.5 + EDGE] = HARD
            arr[g.Y > 37.5 - EDGE] = HARD
    for (hx, hy, hr) in holes:
        g.circle([0, 1], hx, hy, hr, HARD, rt=0.25 + TW / 2 + 0.03, rv=0.25 + VD / 2 + 0.02)
    for (x0, y0, x1, y1) in ko:
        g.rect([0, 1], x0, y0, x1, y1, HARD, rt=TW / 2, rv=VD / 2)
    for net, li, a, e, w in fixed:
        g.segment(li, a[0], a[1], e[0], e[1], nets[net], hw=w / 2)
        if net in DIGITAL:
            g.keepaway_seg(li, a[0], a[1], e[0], e[1], nets[net])
    for net, x, y, dia in fvias:
        g.circle([0, 1], x, y, dia / 2, nets[net])
        g.NOVIA[g.window(x, y, x, y, dia / 2 + 0.05)] |= True
    for p in pads:
        x0, y0, x1, y1 = p["rect"]
        g.rect(p["layers"], x0, y0, x1, y1, nets[p["net"]], novia=VD / 2 + 0.05)
        if p["net"] in DIGITAL:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            for li in p["layers"]:
                g.keepaway_seg(li, x0, cy, x1, cy, nets[p["net"]]) if (x1 - x0) >= (y1 - y0) else g.keepaway_seg(li, cx, y0, cx, y1, nets[p["net"]])
    return g


class Router:
    def __init__(self, g, nets, pads):
        self.g, self.nets, self.pads = g, nets, pads
        self.copper = {n: set() for n in nets}       # net -> {(li, ix, iy)}
        self.tracks, self.vias = [], []              # (net, li, a, b) / (net, x, y)

    def pad_cells(self, p):
        ix, iy = self.g.cell(p["x"], p["y"])
        return [(li, ix, iy) for li in p["layers"]]

    def search(self, net, sources, targets):
        g = self.g
        nid = self.nets[net]
        W, H = g.W, g.H
        allow = []
        for li in range(2):
            a = (g.T[li] == FREE) | (g.T[li] == nid)
            if net == "OUT":
                a &= (g.KA[li] == FREE)
            allow.append(bytearray(a.ravel().astype(np.uint8).tobytes()))
        vm = []
        for li in range(2):
            vm.append((g.V[li] == FREE) | (g.V[li] == nid))
        v = vm[0] & vm[1] & ~g.NOVIA & (g.T[0] != HARD) & (g.T[1] != HARD)
        if net == "OUT":
            v &= (g.KA[0] == FREE) & (g.KA[1] == FREE)
        via_ok = bytearray(v.ravel().astype(np.uint8).tobytes())
        lc = LAYER_COST_EN if net.startswith("EN") else LAYER_COST
        tset = {(li, iy * W + ix) for li, ix, iy in targets}
        tx = [t[1] % W for t in tset]
        ty = [t[1] // W for t in tset]
        bx0, bx1, by0, by1 = min(tx), max(tx), min(ty), max(ty)

        def h(ix, iy):
            dx = max(bx0 - ix, 0, ix - bx1)
            dy = max(by0 - iy, 0, iy - by1)
            return (max(dx, dy) + 0.4142 * min(dx, dy)) * G
        heap, gs, par = [], {}, {}
        for li, ix, iy in sources:
            if not allow[li][iy * W + ix]:
                continue
            s = (li, iy * W + ix, 8)
            gs[s] = 0.0
            par[s] = None
            heapq.heappush(heap, (HW * h(ix, iy), 0.0, s))
        n = 0
        while heap:
            f, gc, s = heapq.heappop(heap)
            if gc > gs.get(s, 1e18):
                continue
            li, idx, d = s
            if (li, idx) in tset:
                path = []
                while s is not None:
                    path.append(s)
                    s = par[s]
                return path[::-1]
            n += 1
            if n > MAXEXP:
                return None
            ix, iy = idx % W, idx // W
            for nd, (dx, dy) in enumerate(DIRS):
                if d != 8:
                    t = min((nd - d) % 8, (d - nd) % 8)
                    if t > 2:
                        continue
                    tc = TURN[t]
                else:
                    tc = 0.0
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < W and 0 <= jy < H):
                    continue
                j = jy * W + jx
                if not allow[li][j]:
                    continue
                if dx and dy and not (allow[li][iy * W + jx] and allow[li][jy * W + ix]):
                    continue
                ng = gc + (1.41421 if dx and dy else 1.0) * G * lc[li] + tc
                ns = (li, j, nd)
                if ng < gs.get(ns, 1e18):
                    gs[ns] = ng
                    par[ns] = s
                    heapq.heappush(heap, (ng + HW * h(jx, jy), ng, ns))
            if via_ok[idx] and allow[1 - li][idx]:
                ns = (1 - li, idx, 8)
                ng = gc + VIA_COST
                if ng < gs.get(ns, 1e18):
                    gs[ns] = ng
                    par[ns] = s
                    heapq.heappush(heap, (ng + HW * h(ix, iy), ng, ns))
        return None

    def commit(self, net, path, p_src=None, p_tgt=None):
        g = self.g
        nid = self.nets[net]
        W = g.W
        pts = [(li, g.ox + (idx % W) * G, g.oy + (idx // W) * G, idx % W, idx // W) for li, idx, _ in path]
        runs = []
        for li, x, y, ix, iy in pts:
            if runs and runs[-1][0] == li:
                runs[-1][1].append((x, y))
            else:
                if runs:
                    self.vias.append((net, x, y))
                    g.circle([0, 1], x, y, VD / 2, nid)
                    g.NOVIA[g.window(x, y, x, y, VD / 2 + 0.05)] |= True
                runs.append((li, [(x, y)]))
            self.copper[net].add((li, ix, iy))
        for li, run in runs:
            simple = [run[0]]
            for i in range(1, len(run) - 1):
                ax, ay = simple[-1]
                bx, by = run[i]
                cx, cy = run[i + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                    simple.append(run[i])
            simple.append(run[-1])
            if p_src is not None and li == path[0][0] and run is runs[0][1]:
                simple.insert(0, (p_src["x"], p_src["y"]))
            if p_tgt is not None and run is runs[-1][1] and li == path[-1][0]:
                simple.append((p_tgt["x"], p_tgt["y"]))
            for a, b in zip(simple, simple[1:]):
                if a == b:
                    continue
                self.tracks.append((net, li, a, b))
                g.segment(li, a[0], a[1], b[0], b[1], nid)
                if net in DIGITAL:
                    g.keepaway_seg(li, a[0], a[1], b[0], b[1], nid)
                n = int(round(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / G))
                for k in range(n + 1):
                    cx, cy = a[0] + (b[0] - a[0]) * k / max(n, 1), a[1] + (b[1] - a[1]) * k / max(n, 1)
                    self.copper[net].add((li, *g.cell(cx, cy)))


def mst_order(pts):
    """nearest-neighbour growth order over pad centres (first = leftmost)."""
    todo = sorted(range(len(pts)), key=lambda i: pts[i][0])
    order = [todo.pop(0)]
    while todo:
        j = min(todo, key=lambda k: min(math.hypot(pts[k][0] - pts[o][0], pts[k][1] - pts[o][1]) for o in order))
        todo.remove(j)
        order.append(j)
    return order


def run(src, order, log):
    b, nets, pads, holes, ko, fixed, fvias = load(src)
    g = build_grid(pads, holes, ko, nets, fixed, fvias)
    R = Router(g, nets, pads)
    for net, li, a, e, w in fixed:
        n = int(round(max(abs(e[0] - a[0]), abs(e[1] - a[1])) / G))
        for k in range(n + 1):
            R.copper[net].add((li, *g.cell(a[0] + (e[0] - a[0]) * k / max(n, 1), a[1] + (e[1] - a[1]) * k / max(n, 1))))
    covered = set()
    for p in pads:
        if p["ref"] != "BUS" and any((li, *g.cell(p["x"], p["y"])) in R.copper[p["net"]] for li in p["layers"]):
            covered.add((p["ref"], p["num"]))
    log["pads_ja_ligados"] = len(covered)
    bad = []
    for p in pads:
        ix, iy = g.cell(p["x"], p["y"])
        off = max(abs(g.ox + ix * G - p["x"]), abs(g.oy + iy * G - p["y"]))
        log["pad_fora_da_grade_max_mm"] = round(max(log.get("pad_fora_da_grade_max_mm", 0), off), 3)
        for li in p["layers"]:
            v = g.T[li][iy, ix]
            if v not in (FREE, nets[p["net"]]):
                bad.append((p["ref"], p["num"], p["net"], int(v)))
    log["pads_inacessiveis"] = bad
    failed = []
    for net in order:
        npads = [p for p in pads if p["net"] == net and (p["ref"], p["num"]) not in covered]
        if len(npads) < 2:
            continue
        pts = [(p["x"], p["y"]) for p in npads]
        seq = mst_order(pts)
        done = [seq[0]]
        for i in seq[1:]:
            p = npads[i]
            j = min(done, key=lambda k: math.hypot(pts[k][0] - pts[i][0], pts[k][1] - pts[i][1]))
            src_c = R.pad_cells(p)
            path = R.search(net, src_c, set(R.pad_cells(npads[j])) - set(src_c))
            if path is None:
                failed.append((net, p["ref"], p["num"]))
                break
            R.commit(net, path, p, npads[j])
            done.append(i)
    return R, failed


def write(src, dst, R):
    b = pcbnew.LoadBoard(src)
    keep = []
    for net, li, a, e in R.tracks:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(M(e[0]), M(e[1])))
        t.SetWidth(M(TW))
        t.SetLayer(LAYERS[li])
        t.SetNet(b.FindNet(net))
        b.Add(t)
        keep.append(t)
    for net, x, y in R.vias:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
        v.SetNet(b.FindNet(net))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(M(VD))
        v.SetDrill(M(VDR))
        b.Add(v)
        keep.append(v)
    pcbnew.SaveBoard(dst, b)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = os.path.abspath(args[0]) if args else os.path.join(HERE, "kicad", "base", "slim_regua.kicad_pcb")
    dst = os.path.abspath(args[1]) if len(args) > 1 else os.path.join(HERE, "kicad", "sinais_proprio.kicad_pcb")
    order = ["CLK", "LATCH", "DATA", "OUT", "+3V3"]     # the head nets; the EN lanes and the buses are drawn by fixa.py
    for a in sys.argv[1:]:
        if a.startswith("--order="):
            order = a.split("=", 1)[1].split(",")
    t0 = time.time()
    log = {}
    for attempt in range(RETRIES):
        R, failed = run(src, order, log)
        log.setdefault("tentativas", []).append({"ordem": list(order), "falhas": failed, "segundos": round(time.time() - t0, 1)})
        print("tentativa", attempt + 1, "falhas", failed, "%.1fs" % (time.time() - t0), "pads inacessiveis:", log["pads_inacessiveis"], flush=True)
        if not failed:
            break
        f = failed[0][0]
        order = [f] + [n for n in order if n != f]
    log["ordem_final"] = order
    log["falhas"] = failed
    write(src, dst, R)
    log["vias"] = len(R.vias)
    log["trilhas"] = len(R.tracks)
    log["segundos"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    json.dump(log, open(os.path.join(HERE, "build", "rota_grade_log.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in log.items() if k != "tentativas"}))
    if failed:
        sys.exit(1)


main()
