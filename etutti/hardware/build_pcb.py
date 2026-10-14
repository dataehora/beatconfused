"""Build the routed eTuttino PCB (Hall-effect version) and its fab files.

Run with KiCad's own Python (it ships the pcbnew module):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

It places every part from the geometry in generate.py, routes the whole
board, runs KiCad's DRC and exports everything a PCB service needs:

  kicad/etuttino.kicad_pcb        the board, open it in KiCad to inspect/edit
  fab/etuttino_gerbers.zip        Gerbers + drill files (PCB only)
  fab/etuttino_bom.csv            parts list for the fab's assembly service
  fab/etuttino_cpl_bottom.csv     where each part goes (all SMD parts are
                                  on the back, so one-sided assembly)
  fab/etuttino_plate_gerbers.zip  the switch plate as an FR4 "PCB" (cutouts only)
  fab/etuttino_drc.json           KiCad's design-rule-check report
  fab/etuttino_top.png / _bottom.png   renders for a visual check

What is on the board:
  - front: 44 Gateron magnetic switches (no pins, two plastic pegs) on the
    case's 18.5 mm hexagonal grid, the two rows of 14 holes for the Teensy
    4.0 + Audio Board stack (back left, USB facing the case's left face) and
    J3, the cable to the controls board under the interface lid (volume
    pot, encoder, power LED),
  - back: under every switch a DRV5056A3 linear Hall sensor and its
    100 nF capacitor; three CD74HC4067 analog multiplexers; an AMS1117-3.3
    regulator for the sensors; the LED's two 330 ohm resistors.

The board's outline is the case's (case/out/pcb_envelope.json, see
generate.py): the router keeps EDGE_CLEAR from that polygon, notches
included.

Why the sensors are on the back: the DRV5056 only responds to a magnetic
SOUTH pole facing its marked (top) side, and Gateron's magnetic switches
have the magnet's NORTH pole facing down. Mounted on the back, the sensor
faces away from the switch, so the field reaches it through the board from
behind, which the sensor reads as positive. (With a switch whose magnet
has south facing down, the sensors would have to move to the front.)

Routing (two layers):
  - per key, fixed: sensor -> capacitor -> a 3.3 V bus above the key row
    and a GND bus below it (back), the output to a via,
  - everything else -- the 44 sensor outputs to their multiplexer
    channels, the multiplexer outputs and address lines to the Teensy, and
    the regulator / multiplexer supplies -- by a small grid router (A*,
    both layers, vias allowed) that keeps KiCad's clearances. DRC then
    checks the result independently.
"""
import heapq
import json
import math
import os
import subprocess
import sys
import zipfile
from array import array

import pcbnew

import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_LIB = os.path.join(HERE, "etuttino.pretty")
KICAD_DIR = os.path.join(HERE, "kicad")
FAB_DIR = os.path.join(HERE, "fab")
BOARD_PATH = os.path.join(KICAD_DIR, "etuttino.kicad_pcb")

KICAD_BIN = os.path.dirname(sys.executable)
KICAD_CLI = os.path.join(KICAD_BIN, "kicad-cli.exe" if os.name == "nt" else "kicad-cli")
FP_ROOT = os.environ.get("KICAD10_FOOTPRINT_DIR") or os.path.normpath(
    os.path.join(KICAD_BIN, "..", "share", "kicad", "footprints"))

TRACK_W = 0.25                  # signals
POWER_W = 0.4                   # 3.3 V, GND, VIN
LOCAL_W = 0.3                   # sensor <-> capacitor <-> bus stubs
VIA_D = 0.6
VIA_DRILL = 0.3
POWER_NETS = {"VCC", "GND", "VIN"}

# Per-key layout on the back (mm from the switch centre, +y towards the player).
CAP_DY = -3.0                   # 100 nF right above the sensor
VCC_BUS_DY = -5.0               # 3.3 V bus above each key row
GND_BUS_DY = 5.0                # GND bus below it
OUT_VIA_DY = 2.7                # sensor output drops to a via here
MUX_CAP_REFS = ["C71", "C72", "C73"]   # 100 nF next to each multiplexer
LDO_CIN, LDO_COUT = "C80", "C81"         # regulator input / output capacitors
# Every net with a fixed starting point grows from it: a route may only
# join copper already connected to this item (see Router.component).
ROOTS = {"VCC": (G.LDO["ref"], "2"), "GND": ("J1", "1"), "VIN": ("J2", "1")}

board = pcbnew.BOARD()
nets = {}


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def xy(vec):
    return (pcbnew.ToMM(vec.x), pcbnew.ToMM(vec.y))


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def load(lib_path, name):
    fp = pcbnew.FootprintLoad(lib_path, name)
    if fp is None:
        raise SystemExit("footprint not found: %s / %s" % (lib_path, name))
    return fp


def lib(name):
    return os.path.join(FP_ROOT, name + ".pretty")


def pad(fp, number):
    for p in fp.Pads():
        if p.GetNumber() == number:
            return p
    raise KeyError(number)


def pads(fp, number):
    return [p for p in fp.Pads() if p.GetNumber() == number]


def width_of(net_name):
    return POWER_W if net_name in POWER_NETS else TRACK_W


def place(lib_path, name, ref, x, y, value=None, back=False, rot=0):
    fp = load(lib_path, name)
    fp.SetReference(ref)
    if value:
        fp.SetValue(value)
    fp.SetPosition(mm(x, y))
    board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    if rot:
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + rot)
    fp.Value().SetVisible(False)
    return fp


def text(s, x, y, size=1.5, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(mm(x, y))
    t.SetLayer(layer)
    t.SetTextSize(mm(size, size))
    t.SetTextThickness(pcbnew.FromMM(size * 0.15))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


# ======================================================================
# Grid router
# ======================================================================
CLEAR = 0.2                     # KiCad's default copper clearance
HOLE_CLEAR = 0.25               # copper to hole
EDGE_CLEAR = 0.5                # copper to board edge
HW_MAX = POWER_W / 2            # widest track any route can be
SLACK = 0.06                    # grid quantisation margin
PITCH = 0.254                   # 1/10 of the Teensy pin pitch
VIA_COST = 2.5                  # mm-equivalent cost of a layer change
TURN_COST = {0: 0.0, 1: 0.12, 2: 0.45}   # 0 / 45 / 90 degree turns (mm)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
FREE, HARD = -1, -2
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


class Router:
    def __init__(self, w_mm, h_mm, anchor):
        # Align the grid on the Teensy pins: the gap between two socket
        # pads (2.54 mm apart) is then exactly one grid line.
        self.ox = anchor[0] - math.floor(anchor[0] / PITCH) * PITCH
        self.oy = anchor[1] - math.floor(anchor[1] / PITCH) * PITCH
        self.W = int((w_mm - self.ox) / PITCH) + 1
        self.H = int((h_mm - self.oy) / PITCH) + 1
        n = self.W * self.H
        self.owner = [array("h", [FREE]) * n for _ in LAYERS]
        self.novia = bytearray(n)
        self.net_ids = {}
        self.net_names = []
        # per net: {(layer, idx): attach point (x, y) or None}
        self.copper = {}
        self.items = {}           # item key -> set of (layer, idx)
        self.tree = {}            # net -> cells already joined to that net's copper
        self.recording = None

    def nid(self, name):
        if name not in self.net_ids:
            self.net_ids[name] = len(self.net_names)
            self.net_names.append(name)
            self.copper[name] = {}
        return self.net_ids[name]

    def cx(self, ix):
        return self.ox + ix * PITCH

    def cy(self, iy):
        return self.oy + iy * PITCH

    def cell(self, x, y):
        return (int(round((x - self.ox) / PITCH)), int(round((y - self.oy) / PITCH)))

    def _claim(self, li, idx, nid):
        cur = self.owner[li][idx]
        if cur == FREE:
            self.owner[li][idx] = nid
        elif cur != nid:
            self.owner[li][idx] = HARD

    def _area(self, x0, y0, x1, y1, reach):
        ix0 = max(0, int((x0 - reach - self.ox) / PITCH))
        iy0 = max(0, int((y0 - reach - self.oy) / PITCH))
        ix1 = min(self.W - 1, int((x1 + reach - self.ox) / PITCH) + 1)
        iy1 = min(self.H - 1, int((y1 + reach - self.oy) / PITCH) + 1)
        for iy in range(iy0, iy1 + 1):
            y = self.cy(iy)
            for ix in range(ix0, ix1 + 1):
                yield ix, iy, self.cx(ix), y

    def mark_segment(self, layers, a, b, half, net_name, item=None, attach=False):
        """Copper of half-width `half` along a-b. net_name None = no net
        (blocks everyone). Cells near the centreline become attach points
        for later routes of the same net."""
        nid = HARD if net_name is None else self.nid(net_name)
        reach = half + CLEAR + HW_MAX + SLACK
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        for ix, iy, x, y in self._area(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), reach):
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
            px, py = ax + t * dx, ay + t * dy
            d = math.hypot(x - px, y - py)
            if d >= reach:
                continue
            idx = iy * self.W + ix
            for layer in layers:
                li = LAYERS.index(layer)
                if nid == HARD:
                    self.owner[li][idx] = HARD
                    continue
                self._claim(li, idx, nid)
                if d <= half - 0.02:
                    self.copper[net_name][(li, idx)] = (round(px, 4), round(py, 4))
                    if item is not None:
                        self.items.setdefault(item, set()).add((li, idx))
                    if self.recording is not None:
                        self.recording.add((li, idx))

    def mark_rect(self, layers, x0, y0, x1, y1, net_name, item=None, smd=False, inside_fn=None):
        nid = HARD if net_name is None else self.nid(net_name)
        reach = CLEAR + HW_MAX + SLACK
        for ix, iy, x, y in self._area(x0, y0, x1, y1, max(reach, 0.35)):
            ddx = max(x0 - x, 0.0, x - x1)
            ddy = max(y0 - y, 0.0, y - y1)
            d = math.hypot(ddx, ddy)
            idx = iy * self.W + ix
            if smd and d < VIA_D / 2 + 0.05:
                self.novia[idx] = 1
            if d >= reach:
                continue
            for layer in layers:
                li = LAYERS.index(layer)
                if nid == HARD:
                    self.owner[li][idx] = HARD
                    continue
                self._claim(li, idx, nid)
                inside = x0 + 0.05 <= x <= x1 - 0.05 and y0 + 0.05 <= y <= y1 - 0.05
                if inside and inside_fn is not None:
                    inside = inside_fn(x, y)
                if inside:
                    self.copper[net_name].setdefault((li, idx), None)
                    if item is not None:
                        self.items.setdefault(item, set()).add((li, idx))

    def mark_hole(self, x, y, drill):
        r = drill / 2 + HOLE_CLEAR + HW_MAX + SLACK
        for ix, iy, cx, cy in self._area(x, y, x, y, r):
            if math.hypot(cx - x, cy - y) < r:
                idx = iy * self.W + ix
                self.owner[0][idx] = HARD
                self.owner[1][idx] = HARD
                self.novia[idx] = 1

    def mark_edges(self, poly):
        """Everything outside the board's outline (a polygon), and within
        EDGE_CLEAR of it, is off limits."""
        r = EDGE_CLEAR + HW_MAX + SLACK
        segs = list(zip(poly, poly[1:] + poly[:1]))
        for iy in range(self.H):
            y = self.cy(iy)
            xs = sorted(x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                        for (x0, y0), (x1, y1) in segs if (y0 > y) != (y1 > y))
            inside = list(zip(xs[0::2], xs[1::2]))
            for ix in range(self.W):
                x = self.cx(ix)
                if not any(a <= x <= b for a, b in inside):
                    idx = iy * self.W + ix
                    self.owner[0][idx] = HARD
                    self.owner[1][idx] = HARD
        for (ax, ay), (bx, by) in segs:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy or 1e-12
            for ix, iy, x, y in self._area(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), r):
                t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                if math.hypot(x - ax - t * dx, y - ay - t * dy) < r:
                    idx = iy * self.W + ix
                    self.owner[0][idx] = HARD
                    self.owner[1][idx] = HARD

    def component(self, net_name, seeds):
        """Cells of `net_name` copper connected to `seeds`: 8-neighbours on
        a layer, and both layers where copper sits at the same spot on both
        (vias, through-hole pads)."""
        cells = self.copper.get(net_name, {})
        todo = [c for c in seeds if c in cells]
        seen = set(todo)
        W = self.W
        while todo:
            li, idx = todo.pop()
            ix, iy = idx % W, idx // W
            nbrs = [(1 - li, idx)]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx or dy:
                        jx, jy = ix + dx, iy + dy
                        if 0 <= jx < W and 0 <= jy < self.H:
                            nbrs.append((li, jy * W + jx))
            for c in nbrs:
                if c in cells and c not in seen:
                    seen.add(c)
                    todo.append(c)
        return seen

    # ------------------------------------------------------------ search
    extra = frozenset()           # more owner ids the current search may use

    def usable(self, li, idx, nid):
        o = self.owner[li][idx]
        return o == FREE or o == nid or o in self.extra

    def via_ok(self, ix, iy, nid):
        if self.novia[iy * self.W + ix]:
            return False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < self.W and 0 <= jy < self.H):
                    return False
                j = jy * self.W + jx
                if not (self.usable(0, j, nid) and self.usable(1, j, nid)):
                    return False
        return True

    def search(self, net_name, sources, targets, max_expand=8_000_000):
        nid = self.nid(net_name)
        W = self.W
        tset = set(targets)
        tx = [i % W for _, i in tset]
        ty = [i // W for _, i in tset]
        bx0, bx1, by0, by1 = min(tx), max(tx), min(ty), max(ty)

        def h(ix, iy):
            dx = max(bx0 - ix, 0, ix - bx1)
            dy = max(by0 - iy, 0, iy - by1)
            return (max(dx, dy) + 0.4142 * min(dx, dy)) * PITCH

        g = {}
        parent = {}
        heap = []
        for li, idx in sources:
            if not self.usable(li, idx, nid):
                continue
            s = (li, idx, 8)
            g[s] = 0.0
            parent[s] = None
            heapq.heappush(heap, (h(idx % W, idx // W), 0.0, s))
        expanded = 0
        while heap:
            f, gc, s = heapq.heappop(heap)
            if gc > g.get(s, 1e18):
                continue
            li, idx, d = s
            if (li, idx) in tset:
                path = []
                while s is not None:
                    path.append(s)
                    s = parent[s]
                return path[::-1]
            expanded += 1
            if expanded > max_expand:
                print("  search limit hit for", net_name)
                break
            ix, iy = idx % W, idx // W
            for nd, (dx, dy) in enumerate(DIRS):
                if d != 8:
                    turn = min((nd - d) % 8, (d - nd) % 8)
                    if turn > 2:
                        continue
                    tc = TURN_COST[turn]
                else:
                    tc = 0.0
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < W and 0 <= jy < self.H):
                    continue
                j = jy * W + jx
                if not self.usable(li, j, nid):
                    continue
                if dx and dy and not (self.usable(li, iy * W + jx, nid) and self.usable(li, jy * W + ix, nid)):
                    continue
                ng = gc + (1.41421 if dx and dy else 1.0) * PITCH + tc
                ns = (li, j, nd)
                if ng < g.get(ns, 1e18):
                    g[ns] = ng
                    parent[ns] = s
                    heapq.heappush(heap, (ng + h(jx, jy), ng, ns))
            # layer change
            if self.via_ok(ix, iy, nid):
                ns = (1 - li, idx, 8)
                ng = gc + VIA_COST
                if ng < g.get(ns, 1e18):
                    g[ns] = ng
                    parent[ns] = s
                    heapq.heappush(heap, (ng + h(ix, iy), ng, ns))
        return None


# The order the retries found for the current layout; a layout change may
# need a new one (the retry loop finds it and prints it).
DEFAULT_ROUTE_FIRST = "OUT_U41,OUT_U42,GND,LED_R,LED_G_DRV,OUT_U34"


class RoutingFailed(Exception):
    pass


router = None
pending_tracks = []             # (layer, a, b, width, net) added to the board at the end


def add_track(points, layer, net_name, width=None, register=True, item=None):
    w = width or width_of(net_name)
    for a, b in zip(points, points[1:]):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(mm(*a))
        t.SetEnd(mm(*b))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(layer)
        t.SetNet(net(net_name))
        board.Add(t)
        if register:
            router.mark_segment([layer], a, b, w / 2, net_name, item=item, attach=True)


via_spots = {}                  # net -> [(x, y)] of its vias


def add_via(x, y, net_name, item=None):
    via_spots.setdefault(net_name, []).append((x, y))
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(mm(x, y))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetNet(net(net_name))
    board.Add(v)
    router.mark_segment(LAYERS, (x, y), (x, y), VIA_D / 2, net_name, item=item, attach=True)


def register_pad(p, item):
    """Marks a pad's copper on the router grid."""
    bb = p.GetBoundingBox()
    x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    layers = [l for l in LAYERS if p.IsOnLayer(l)]
    name = p.GetNetname() or None
    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
        cx, cy = xy(p.GetPosition())
        router.mark_hole(cx, cy, pcbnew.ToMM(p.GetDrillSize().x))
        return
    smd = p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD

    def inside(x, y):
        # a route may only end where the pad really has copper (round
        # pads and rounded corners leave the bounding box's corners bare)
        return all(p.HitTest(mm(x + dx, y + dy)) for dx, dy in ((0.06, 0), (-0.06, 0), (0, 0.06), (0, -0.06)))
    router.mark_rect(layers, x0, y0, x1, y1, name, item=item, smd=smd, inside_fn=inside)
    if not smd:
        cx, cy = xy(p.GetPosition())
        i = router.cell(cx, cy)
        router.novia[i[1] * router.W + i[0]] = 1


def path_to_copper(net_name, path, start_xy=None, end_xy=None):
    """Turns a search path (states) into tracks and vias on the board."""
    pts = [(router.cx(idx % router.W), router.cy(idx // router.W), li) for li, idx, _ in path]
    runs = []                   # [(layer_index, [points])]
    for x, y, li in pts:
        if runs and runs[-1][0] == li:
            runs[-1][1].append((x, y))
        else:
            if runs:
                # Changing layer right beside one of this net's vias (the
                # sensor's own, usually): go through that via instead of
                # drilling a second one on top of it.
                near = [v for v in via_spots.get(net_name, []) if abs(x - v[0]) < VIA_D and abs(y - v[1]) < VIA_D]
                if near:
                    runs[-1][1].append(near[0])
                    runs.append((li, [near[0], (x, y)]))
                    continue
                add_via(x, y, net_name)
            runs.append((li, [(x, y)]))
    if start_xy:
        runs[0][1].insert(0, start_xy)
    if end_xy:
        runs[-1][1].append(end_xy)
    for li, run in runs:
        # drop collinear points
        simple = [run[0]]
        for i in range(1, len(run) - 1):
            ax, ay = simple[-1]
            bx, by = run[i]
            cx, cy = run[i + 1]
            if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                simple.append(run[i])
        simple.append(run[-1])
        add_track(simple, LAYERS[li], net_name)


def connect(net_name, source_item, targets, label, extra=None):
    """Routes one item to a set of target cells, then records everything
    now joined (source item, new copper, explicit target items) as part of
    the net's connected tree."""
    src = router.items[source_item]
    if source_item[0] == "via":
        src = {c for c in src if c[0] == 0}     # leave the sensor's via on the front
    router.extra = frozenset(router.nid(n) for n in extra) if extra else frozenset()
    path = router.search(net_name, src, targets)
    router.extra = frozenset()
    if path is None:
        print("ROUTING FAILED: %s (%s)" % (label, net_name))
        raise RoutingFailed(net_name)
    last = (path[-1][0], path[-1][1])
    end = router.copper[net_name].get(last)
    router.recording = set()
    path_to_copper(net_name, path, end_xy=end)
    if net_name in ROOTS:
        router.tree[net_name] = router.component(net_name, router.items[ROOTS[net_name]])
    else:
        router.tree.setdefault(net_name, set()).update(router.recording | src)
    router.recording = None
    return path


# ======================================================================
# Board
# ======================================================================
def build():
    global router
    keys = G.keys()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(pcbnew.FromMM(G.PCB_THICKNESS))
    pins = G.stack_pins()
    anchor = [(p[3], p[4]) for p in pins if p[0] == "J1" and p[1] == 1][0]
    router = Router(G.PCB_W, G.PCB_H, anchor)
    router.mark_edges(G.OUTLINE)

    footprints = []             # every placed footprint; pads registered once nets are set

    # ---- switches (front) and, under each, sensor + capacitor (back) ----
    row_vcc = {}                # row -> [x of each key's 3.3 V drop]
    row_gnd = {}
    for k in keys:
        cx, cy = k["cx"], k["cy"]
        footprints.append(place(LOCAL_LIB, "Gateron_Magnetic_MX_1u", k["ref"], cx, cy))

        u = place(lib("Package_TO_SOT_SMD"), "SOT-23-3", k["sensor"], cx, cy, "DRV5056A3QDBZR", back=True)
        u.Reference().SetVisible(False)
        out_net = "OUT_%s" % k["sensor"]
        pad(u, "1").SetNet(net("VCC"))
        pad(u, "2").SetNet(net(out_net))
        pad(u, "3").SetNet(net("GND"))
        p_vcc, p_out, p_gnd = (xy(pad(u, n).GetPosition()) for n in "123")
        assert p_vcc[0] > cx and p_out[0] > cx and p_gnd[0] < cx and p_vcc[1] < p_out[1], (p_vcc, p_out, p_gnd)

        c = place(lib("Capacitor_SMD"), "C_0805_2012Metric", k["cap"], cx, cy + CAP_DY, "100nF", back=True)
        c.Reference().SetVisible(False)
        c1, c2 = xy(pad(c, "1").GetPosition()), xy(pad(c, "2").GetPosition())
        cap_vcc, cap_gnd = ("1", "2") if c1[0] > c2[0] else ("2", "1")
        pad(c, cap_vcc).SetNet(net("VCC"))
        pad(c, cap_gnd).SetNet(net("GND"))
        cap_y = cy + CAP_DY
        footprints += [u, c]

        vcc_y, gnd_y = cy + VCC_BUS_DY, cy + GND_BUS_DY
        pending_tracks.append(([p_vcc, (p_vcc[0], cap_y), (p_vcc[0], vcc_y)], pcbnew.B_Cu, "VCC", LOCAL_W))
        pending_tracks.append(([(p_gnd[0], cap_y), p_gnd, (p_gnd[0], gnd_y)], pcbnew.B_Cu, "GND", LOCAL_W))
        k["out_via"] = (p_out[0], cy + OUT_VIA_DY)
        pending_tracks.append(([p_out, k["out_via"]], pcbnew.B_Cu, out_net, TRACK_W))
        row_vcc.setdefault(k["row"], []).append(p_vcc[0])
        row_gnd.setdefault(k["row"], []).append(p_gnd[0])
        k["row_y"] = cy

    # ---- multiplexers, regulator, their capacitors (back) ----
    muxes = []
    for m, spec in enumerate(G.MUXES):
        rot = spec.get("rot", 180)
        u = place(lib("Package_SO"), "SOIC-24W_7.5x15.4mm_P1.27mm", spec["ref"], spec["x"], spec["y"],
                  "CD74HC4067M96", back=True, rot=rot)
        spec["pads"] = {}
        for number, func in G.MUX_PINS.items():
            got = xy(pad(u, str(number)).GetPosition())
            spec["pads"][number] = got
            if rot == 180:
                want = G.mux_pin_offset(number)
                assert abs(got[0] - spec["x"] - want[0]) < 0.01 and abs(got[1] - spec["y"] - want[1]) < 0.01, (number, got)
            name = None
            if func == "COM":
                name = "COM%d" % m
            elif func in ("S0", "S1", "S2", "S3"):
                name = "SEL%s" % func[1]
            elif func in ("GND", "E"):
                name = "GND"
            elif func == "VCC":
                name = "VCC"
            if name:
                pad(u, str(number)).SetNet(net(name))
        # Every channel pad starts on a placeholder net of its own: a sensor
        # output may end on any free one (see the job loop), and the
        # firmware table is written from what the router chose. Separate
        # placeholders keep the clearance between neighbouring pads.
        for ch in range(G.MUX_CHANNELS):
            pad(u, str(G.channel_pin(ch))).SetNet(net("FREE%d_%d" % (m, ch)))
        u.Reference().SetPosition(mm(spec["x"], spec["y"]))
        cdx, cdy, crot = spec.get("cap", (2.4, 9.8, 0))
        c = place(lib("Capacitor_SMD"), "C_0805_2012Metric", MUX_CAP_REFS[m], spec["x"] + cdx, spec["y"] + cdy,
                  "100nF", back=True, rot=crot)
        c.Reference().SetVisible(False)
        # the capacitor pad nearer the multiplexer's VCC pin takes VCC
        vx, vy = spec["pads"][[p for p, f in G.MUX_PINS.items() if f == "VCC"][0]]
        d = lambda n: math.hypot(xy(pad(c, n).GetPosition())[0] - vx, xy(pad(c, n).GetPosition())[1] - vy)
        hi, lo = ("1", "2") if d("1") < d("2") else ("2", "1")
        pad(c, hi).SetNet(net("VCC"))
        pad(c, lo).SetNet(net("GND"))
        muxes.append((u, c))
        footprints += [u, c]

    # Rotated 180 deg: input pins on the left, VIN (pin 3) towards the
    # Teensy's VIN row at the back, the output tab on the right.
    ldo = place(lib("Package_TO_SOT_SMD"), "SOT-223-3_TabPin2", G.LDO["ref"], G.LDO["x"], G.LDO["y"],
                "AMS1117-3.3", back=True, rot=G.LDO.get("rot", 0))
    for p in ldo.Pads():
        p.SetNet(net({"1": "GND", "2": "VCC", "3": "VIN"}[p.GetNumber()]))
    vin_xy = xy(pad(ldo, "3").GetPosition())
    assert vin_xy[0] < G.LDO["x"] and vin_xy[1] < G.LDO["y"], vin_xy
    ldo.Reference().SetPosition(mm(G.LDO["x"], G.LDO["y"] + 4.6))
    c_in = place(lib("Capacitor_SMD"), "C_0805_2012Metric", LDO_CIN, G.LDO["x"] - 7.0, G.LDO["y"] - 3.2, "10uF",
                 back=True, rot=90)
    c_out = place(lib("Capacitor_SMD"), "C_0805_2012Metric", LDO_COUT, G.LDO["x"] + 7.2, G.LDO["y"] - 3.2, "22uF",
                  back=True, rot=90)
    for cap, live in ((c_in, "VIN"), (c_out, "VCC")):
        cap.Reference().SetVisible(False)
        p1, p2 = pad(cap, "1"), pad(cap, "2")
        # the pad nearer the regulator's centre line takes the live net
        near, far = (p1, p2) if abs(xy(p1.GetPosition())[1] - G.LDO["y"]) < abs(xy(p2.GetPosition())[1] - G.LDO["y"]) else (p2, p1)
        near.SetNet(net(live))
        far.SetNet(net("GND"))
    footprints += [ldo, c_in, c_out]

    # ---- the power LED's 330 ohm resistors (back); the LED itself is on the
    # controls board, through J3 ----
    led_res = {}
    for ref, dx, drv, out in (("R1", 0.0, "LED_R_DRV", "LED_R"), ("R2", 3.0, "LED_G_DRV", "LED_G")):
        r = place(lib("Resistor_SMD"), "R_0805_2012Metric", ref, G.LED_RES["x"] + dx, G.LED_RES["y"], "330", back=True, rot=90)
        r.Reference().SetVisible(False)
        p1, p2 = pad(r, "1"), pad(r, "2")
        low, high = (p1, p2) if xy(p1.GetPosition())[1] > xy(p2.GetPosition())[1] else (p2, p1)
        low.SetNet(net(out))      # the pad nearer J3 (in front)
        high.SetNet(net(drv))
        led_res[ref] = (high.GetNumber(), low.GetNumber())
    footprints += [board.FindFootprintByReference(r) for r in led_res]

    # ---- J3: cable to the controls board (JST PH, 2 mm, vertical, top) ----
    j3 = place(lib("Connector_JST"), "JST_PH_B8B-PH-K_1x08_P2.00mm_Vertical", G.J3["ref"], G.J3["x"], G.J3["y"],
               "controls board")
    for p in j3.Pads():
        p.SetNet(net(G.J3_PINS[int(p.GetNumber())]))
    footprints.append(j3)

    # ---- Teensy sockets (front, through-hole) ----
    sockets = {}
    for ref in ("J1", "J2"):
        first = [p for p in pins if p[0] == ref and p[1] == 1][0]
        s = place(lib("Connector_PinSocket_2.54mm"), "PinSocket_1x14_P2.54mm_Vertical", ref, first[3], first[4], rot=90)
        s.Value().SetVisible(False)
        sockets[ref] = s
    for ref, number, pin, x, y in pins:
        p = pad(sockets[ref], str(number))
        got = xy(p.GetPosition())
        assert abs(got[0] - x) < 0.01 and abs(got[1] - y) < 0.01, (ref, number, got, (x, y))
        n = G.pin_net(pin)
        if n:
            p.SetNet(net(n))
    footprints += list(sockets.values())

    # ---- mounting holes ----
    for i, (x, y) in enumerate(G.mounting_holes(), start=1):
        h = place(lib("MountingHole"), "MountingHole_2.2mm_M2", "H%d" % i, x, y)
        h.Reference().SetVisible(False)
        footprints.append(h)
        # no copper under the nut (top) or on the pillar (back)
        router.mark_hole(x, y, 2 * G.MOUNT_KEEPOUT[(x, y)])

    for fp in footprints:
        for p in fp.Pads():
            register_pad(p, (fp.GetReference(), p.GetNumber()) if p.GetNetname() else None)

    # nothing on the back where the bottom plate's pillars hold the board up
    clash = []
    for fp in footprints:
        if not fp.IsFlipped():
            continue
        bb = fp.GetBoundingBox(False)
        x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        for sx, sy, sr in G.SUPPORTS:
            if math.hypot(max(x0 - sx, 0, sx - x1), max(y0 - sy, 0, sy - y1)) < sr:
                clash.append((fp.GetReference(), (sx, sy)))
    if clash:
        raise SystemExit("parts on the back over a bottom-plate pillar: %s" % clash)

    # ---- fixed copper: per-key stubs, row buses, trunks, output vias ----
    for points, layer, name, w in pending_tracks:
        add_track(points, layer, name, w)
    for k in keys:
        add_via(k["out_via"][0], k["out_via"][1], "OUT_%s" % k["sensor"], item=("via", k["sensor"]))
    rows_y = sorted({k["row_y"] for k in keys})
    by_row = {k["row_y"]: k["row"] for k in keys}
    # one 3.3 V bus above and one GND bus below each key row, as long as
    # the row; the router joins them to the regulator and the Teensy
    for cy in rows_y:
        r = by_row[cy]
        add_track(sorted({(x, cy + VCC_BUS_DY) for x in row_vcc[r]}), pcbnew.B_Cu, "VCC", item=("vccbus", r))
        add_track(sorted({(x, cy + GND_BUS_DY) for x in row_gnd[r]}), pcbnew.B_Cu, "GND", item=("gndbus", r))
    # the regulator's output pin and its tab are separate pads: join them
    out_pads = [xy(p.GetPosition()) for p in pads(ldo, "2")]
    add_track(out_pads, pcbnew.B_Cu, "VCC", 0.6, item=(G.LDO["ref"], "2"))

    # ---- routed connections ----
    jobs = []
    # row buses first, nearest the regulator / Teensy GND first
    ldo_y = G.LDO["y"]
    gnd_y0 = [p[4] for p in pins if p[0] == "J1" and p[1] == 1][0]
    for r in sorted(by_row.values(), key=lambda r: abs([y for y, rr in by_row.items() if rr == r][0] + VCC_BUS_DY - ldo_y)):
        jobs.append(("VCC", ("vccbus", r), "tree", "row %d 3.3 V bus" % (r + 1)))
    for r in sorted(by_row.values(), key=lambda r: abs([y for y, rr in by_row.items() if rr == r][0] + GND_BUS_DY - gnd_y0)):
        jobs.append(("GND", ("gndbus", r), "tree", "row %d GND bus" % (r + 1)))
    # sensor outputs, furthest from their multiplexer first, each to any
    # free channel of its multiplexer
    outs = []
    for k in keys:
        spec = G.MUXES[k["mux"]]
        dist = abs(k["out_via"][0] - spec["x"]) + abs(k["out_via"][1] - spec["y"])
        outs.append((dist, k))
    # Front multiplexer U51 the other way round, nearest first: its 16 keys
    # all sit in rows 1-2 to its right, and the far ones' traces along the
    # row boxed the near ones' vias in; the far ones can still go round
    # through the empty strip in front of row 1.
    outs.sort(key=lambda t: t[0] if t[1]["mux"] == 0 else -t[0])
    free_channels = {m: set(range(G.MUX_CHANNELS)) for m in range(len(G.MUXES))}
    for _, k in outs:
        spec = G.MUXES[k["mux"]]
        jobs.append(("OUT_%s" % k["sensor"], ("via", k["sensor"]), ("mux", k["mux"], k),
                     "%s -> %s" % (k["sensor"], spec["ref"])))
    # Multiplexer outputs to the Teensy ADC pins, and the address lines, all
    # with the power: before the sensor outputs. The far multiplexer's lines
    # run along the back strip behind row 4 (routed after the sensors, its
    # COM and address lines found the way blocked; when they crossed the
    # rows, earlier layouts routed them last so they wouldn't box the
    # sensors in -- set ETUTTINO_LATE_FAR=1 to get that back).
    far = set()
    if os.environ.get("ETUTTINO_LATE_FAR"):
        far = {spec["ref"] for spec in G.MUXES if abs(spec["x"] - G.STACK_CX) > G.PCB_W / 2}
    late = set()
    for m, spec in enumerate(G.MUXES):
        com_pad = [p for p, f in G.MUX_PINS.items() if f == "COM"][0]
        j2 = [p for p in pins if p[0] == "J2" and p[2] == G.COM_PINS[m]][0]
        jobs.append(("COM%d" % m, (spec["ref"], str(com_pad)), [("J2", str(j2[1]))], "%s COM -> pin %s" % (spec["ref"], G.COM_PINS[m])))
    # address lines: Teensy -> the nearest multiplexer, then on to the others
    for s, pin in enumerate(G.SEL_PINS):
        j1 = [p for p in pins if p[0] == "J1" and p[2] == pin][0]
        sel_pad = str([p for p, f in G.MUX_PINS.items() if f == "S%d" % s][0])
        order = sorted(G.MUXES, key=lambda m: abs(m["x"] - j1[3]) + abs(m["y"] - j1[4]))
        jobs.append(("SEL%d" % s, ("J1", str(j1[1])), [(order[0]["ref"], sel_pad)], "pin %s -> %s S%d" % (pin, order[0]["ref"], s)))
        for spec in order[1:]:
            jobs.append(("SEL%d" % s, (spec["ref"], sel_pad), "tree", "%s S%d" % (spec["ref"], s)))
            if spec["ref"] in far:
                late.add(jobs[-1][3])
    # power
    ldo_ref = G.LDO["ref"]
    pad_of = lambda fp, name: "1" if pad(fp, "1").GetNetname() == name else "2"
    jobs.append(("VIN", ("J2", "1"), [(ldo_ref, "3")], "VIN -> regulator"))
    jobs.append(("VIN", (LDO_CIN, pad_of(c_in, "VIN")), "tree", "%s VIN" % LDO_CIN))
    for item in [("J2", "2"), (ldo_ref, "1"), (LDO_CIN, pad_of(c_in, "GND")), (LDO_COUT, pad_of(c_out, "GND"))]:
        jobs.append(("GND", item, "tree", "GND %s.%s" % item))
    jobs.append(("VCC", (LDO_COUT, pad_of(c_out, "VCC")), "tree", "VCC %s" % LDO_COUT))
    # power LED: Teensy pin -> resistor -> J3 (the LED is on the controls board)
    j3_pin = {n: str(p) for p, n in G.J3_PINS.items()}
    for ref, drv, out in (("R1", "LED_R_DRV", "LED_R"), ("R2", "LED_G_DRV", "LED_G")):
        teensy_pin = [p for p, n in G.LED_PINS.items() if n == drv][0]
        j1 = [p for p in pins if p[0] == "J1" and p[2] == teensy_pin][0]
        jobs.append((drv, ("J1", str(j1[1])), [(ref, led_res[ref][0])], "pin %s -> %s" % (teensy_pin, ref)))
        jobs.append((out, (ref, led_res[ref][1]), [(G.J3["ref"], j3_pin[out])], "%s -> J3" % ref))
    # pot and encoder lines: Teensy pin -> J3; J3's supply joins the trees
    for teensy_pin, n in G.CONTROL_PINS.items():
        row = [p for p in pins if p[2] == teensy_pin][0]
        jobs.append((n, (row[0], str(row[1])), [(G.J3["ref"], j3_pin[n])], "pin %s -> J3 %s" % (teensy_pin, n)))
    jobs.append(("VCC", (G.J3["ref"], j3_pin["VCC"]), "tree", "J3 3.3 V"))
    jobs.append(("GND", (G.J3["ref"], j3_pin["GND"]), "tree", "J3 GND"))
    gnd_pins = [str(p) for p, f in G.MUX_PINS.items() if f in ("GND", "E")]
    for m, spec in enumerate(G.MUXES):
        cref = MUX_CAP_REFS[m]
        cap = muxes[m][1]
        c_gnd = "1" if pad(cap, "1").GetNetname() == "GND" else "2"
        c_vcc = "2" if c_gnd == "1" else "1"
        # (only ever join the net's connected tree: a pin-to-capacitor hop
        # first would make an island the next job could join instead)
        jobs.append(("VCC", (spec["ref"], "24"), "tree", "%s VCC" % spec["ref"]))
        jobs.append(("VCC", (cref, c_vcc), "tree", "%s VCC" % cref))
        for gp in gnd_pins:
            jobs.append(("GND", (spec["ref"], gp), "tree", "%s pin %s GND" % (spec["ref"], gp)))
        jobs.append(("GND", (cref, c_gnd), "tree", "%s GND" % cref))

    # Each rooted net's tree starts as the copper connected to its root.
    for net_name, root in ROOTS.items():
        router.tree[net_name] = router.component(net_name, router.items[root])

    # Few, long, must-not-fail connections first (power, multiplexer
    # outputs and address lines); the 44 sensor outputs then fit around them,
    # and the far multiplexer's long lines last.
    # Sensor outputs that failed in an earlier attempt go first (see
    # route_with_retries below).
    first = [n for n in os.environ.get("ETUTTINO_ROUTE_FIRST", DEFAULT_ROUTE_FIRST).split(",") if n]
    tier = lambda j: 2 if j[3] in late else 1 if j[0].startswith("OUT_") else 0
    jobs.sort(key=lambda j: (tier(j), j[0] not in first, first.index(j[0]) if j[0] in first else 0))
    for net_name, src_item, dst, label in jobs:
        if dst == "tree":
            targets = router.tree.get(net_name, set()) - router.items[src_item]
        elif dst[0] == "mux":
            _, m, k = dst
            ref = G.MUXES[m]["ref"]
            targets = set()
            for ch in free_channels[m]:
                targets |= router.items[(ref, str(G.channel_pin(ch)))]
            path = connect(net_name, src_item, targets, label, extra=["FREE%d_%d" % (m, c) for c in free_channels[m]])
            last = (path[-1][0], path[-1][1])
            ch = [c for c in free_channels[m] if last in router.items[(ref, str(G.channel_pin(c)))]][0]
            free_channels[m].discard(ch)
            k["ch"] = ch
            # the pad now belongs to this output: claim it (and its
            # clearance) for this net, so later routes keep away from it
            p = pad(board.FindFootprintByReference(ref), str(G.channel_pin(ch)))
            p.SetNet(net(net_name))
            register_pad(p, (ref, str(G.channel_pin(ch))))
            print("routed", label, "I%d" % ch)
            continue
        else:
            targets = set()
            for it in dst:
                targets |= router.items[it]
        if not targets:
            raise SystemExit("no target for %s" % label)
        connect(net_name, src_item, targets, label)
        if dst != "tree" and net_name not in ROOTS:
            for it in dst:
                router.tree[net_name] |= router.items[it]
        print("routed", label)

    # unused channel pads: no net
    for m, spec in enumerate(G.MUXES):
        fp = board.FindFootprintByReference(spec["ref"])
        for ch in free_channels[m]:
            pad(fp, str(G.channel_pin(ch))).SetNetCode(0)
    write_channel_table(keys)

    # ---- outline, labels ----
    corners = G.OUTLINE + G.OUTLINE[:1]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(mm(x1, y1))
        seg.SetEnd(mm(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)

    text("eTuttino v0.7 HE", G.KEY_O + 3 * G.U, G.ROW_Y[4] - 10.5, 1.2)
    text("controls board", G.J3["x"] + 7.0, G.J3["y"] + 4.6, 0.9)
    text("< USB - Teensy 4.0 on Audio Board Rev D", G.STACK_CX, G.STACK_ZONE[1] + 2.6, 0.9)
    j1_gnd = [p for p in pins if p[0] == "J1" and p[1] == 1][0]
    j2_vin = [p for p in pins if p[0] == "J2" and p[1] == 1][0]
    text("GND", j1_gnd[3], j1_gnd[4] + 2.4, 0.8)
    text("VIN", j2_vin[3], j2_vin[4] - 2.4, 0.8)
    text("0", j1_gnd[3] + 2.54, j1_gnd[4] + 2.4, 0.8)
    text("23", j2_vin[3] + 7.62, j2_vin[4] - 2.4, 0.8)
    text("eTuttino v0.7 HE - C-griff G3-E6 - beatconfused.com/etutti", G.KEY_O + 5 * G.U, G.ROW_Y[1] + 14.0, 1.0, pcbnew.B_SilkS)
    text("Sensors DRV5056A3 on this side, under each switch", G.KEY_O + 5 * G.U, G.ROW_Y[4] - 14.0, 1.0, pcbnew.B_SilkS)

    os.makedirs(KICAD_DIR, exist_ok=True)
    pcbnew.SaveBoard(BOARD_PATH, board)
    print("saved", BOARD_PATH)


def write_channel_table(keys):
    """The channels the router picked, written into the firmware's
    KEY_INPUT table and build/etuttino_keys.csv (verify_against_firmware
    then checks the saved board against that file)."""
    import re
    table = G.firmware_key_table(keys)
    ino = open(FIRMWARE, encoding="utf-8").read()
    new = re.sub(r"const int8_t KEY_INPUT\[LAYOUT_ROWS\]\[LAYOUT_COLS\] = \{.*?\n\};", lambda _: table, ino, flags=re.S)
    if new != ino:
        with open(FIRMWARE, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print("firmware KEY_INPUT updated from the routed channels")
    os.makedirs(G.BUILD, exist_ok=True)
    G.write_csv(keys)


def cli(*args):
    print("kicad-cli", " ".join(args[:3]), "...")
    subprocess.run([KICAD_CLI, *args], check=True, stdout=subprocess.DEVNULL)


# LCSC numbers of JLCPCB "basic" parts (no extended-part fee). The TI parts
# are matched by manufacturer part number in JLCPCB's BOM tool.
BOM_LINES = [
    # (comment / MPN, designators, footprint, LCSC)
    ("DRV5056A3QDBZR", lambda ks: [k["sensor"] for k in ks], "SOT-23-3", ""),
    ("100nF 0805 X7R", lambda ks: [k["cap"] for k in ks] + MUX_CAP_REFS, "C_0805", "C49678"),
    ("CD74HC4067M96", lambda ks: [m["ref"] for m in G.MUXES], "SOIC-24W", ""),
    ("AMS1117-3.3", lambda ks: [G.LDO["ref"]], "SOT-223", "C6186"),
    ("10uF 0805", lambda ks: [LDO_CIN], "C_0805", "C15850"),
    ("22uF 0805", lambda ks: [LDO_COUT], "C_0805", "C45783"),
    ("330R 0805", lambda ks: ["R1", "R2"], "R_0805", "C17630"),
]


def fab():
    gerber_dir = os.path.join(FAB_DIR, "gerbers")
    os.makedirs(gerber_dir, exist_ok=True)
    # Clear old outputs file by file (removing the folder itself trips over
    # OneDrive/Explorer holding a handle on it).
    for name in os.listdir(gerber_dir):
        os.remove(os.path.join(gerber_dir, name))

    drc_path = os.path.join(FAB_DIR, "etuttino_drc.json")
    cli("pcb", "drc", "--format", "json", "--severity-all", "--output", drc_path, BOARD_PATH)
    with open(drc_path, encoding="utf-8") as f:
        report = json.load(f)
    violations = report.get("violations", [])
    unconnected = report.get("unconnected_items", [])
    errors = [v for v in violations if v.get("severity") == "error"]
    print("DRC: %d errors, %d warnings, %d unconnected" % (
        len(errors), len(violations) - len(errors), len(unconnected)))
    for v in violations[:40]:
        print("  [%s] %s" % (v.get("severity"), v.get("description")))
        for item in v.get("items", [])[:2]:
            print("        ", item.get("description"), item.get("pos"))
    for u in unconnected[:20]:
        print("  [unconnected]", [i.get("description") for i in u.get("items", [])])

    cli("pcb", "export", "gerbers", "--output", gerber_dir + os.sep,
        "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
        BOARD_PATH)
    cli("pcb", "export", "drill", "--output", gerber_dir + os.sep, "--format", "excellon",
        "--excellon-separate-th", BOARD_PATH)

    # Assembly files: every SMD part is on the back.
    cpl_path = os.path.join(FAB_DIR, "etuttino_cpl_bottom.csv")
    cli("pcb", "export", "pos", "--side", "back", "--format", "csv", "--units", "mm",
        "--smd-only", "--output", cpl_path, BOARD_PATH)
    ks = G.keys()
    with open(os.path.join(FAB_DIR, "etuttino_bom.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("Comment,Designator,Footprint,LCSC Part #\n")
        for comment, refs, footprint, lcsc in BOM_LINES:
            f.write('"%s","%s","%s","%s"\n' % (comment, ",".join(refs(ks)), footprint, lcsc))

    zip_path = os.path.join(FAB_DIR, "etuttino_gerbers.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(gerber_dir)):
            z.write(os.path.join(gerber_dir, name), name)
    print("wrote", zip_path, sorted(os.listdir(gerber_dir)))

    for side in ("top", "bottom"):
        try:
            cli("pcb", "render", "--side", side, "--width", "1600", "--height", "1200",
                "--output", os.path.join(FAB_DIR, "etuttino_%s.png" % side), BOARD_PATH)
        except subprocess.CalledProcessError:
            print("render failed for", side)
    return len(errors), len(unconnected)


FIRMWARE = os.path.join(HERE, "..", "firmware", "etutti_synth", "etutti_synth.ino")


def verify_against_firmware():
    """Reads the saved board back and checks, for every key, that its
    sensor's output reaches the multiplexer channel -- and that
    multiplexer's output the Teensy pin -- the firmware reads for that
    key's position, and that the address lines go to the pins the firmware
    drives. DRC only proves the copper matches the nets; this proves the
    nets match the firmware."""
    import re
    b = pcbnew.LoadBoard(BOARD_PATH)
    pin_of_net = {}
    for ref, side in (("J1", G.TEENSY_LEFT), ("J2", G.TEENSY_RIGHT)):
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNetname():
                pin_of_net[p.GetNetname()] = side[int(p.GetNumber()) - 1]
    ino = open(FIRMWARE, encoding="utf-8").read()

    def ints(pattern):
        return [int(v) for v in re.findall(r"-?\d+", re.search(pattern, ino, re.S).group(1))]

    sel_pins = ints(r"MUX_SEL_PINS\[4\] = \{([^}]*)\}")
    led_pins = ints(r"LED_PINS\[2\] = \{([^}]*)\}")
    com_pins = ints(r"MUX_COM_PINS\[MUX_COUNT\] = \{([^}]*)\}")
    table = ints(r"KEY_INPUT\[LAYOUT_ROWS\]\[LAYOUT_COLS\] = \{(.*?)\};")
    first_col = ints(r"FIRST_COL\[LAYOUT_ROWS\] = \{([^}]*)\}")
    first = ints(r"FIRST_NOTE\[2\]\[LAYOUT_ROWS\] = \{(.*?)\};")
    bad = 0
    for s in range(4):
        if int(pin_of_net["SEL%d" % s]) != sel_pins[s]:
            bad += 1
            print("  MISMATCH address S%d: board pin %s, firmware %d" % (s, pin_of_net["SEL%d" % s], sel_pins[s]))
    for i, n in enumerate(("LED_R_DRV", "LED_G_DRV")):
        if int(pin_of_net[n]) != led_pins[i]:
            bad += 1
            print("  MISMATCH LED: %s on pin %s, firmware %d" % (n, pin_of_net[n], led_pins[i]))
    mux_by_ref = {}
    for m, spec in enumerate(G.MUXES):
        fp = b.FindFootprintByReference(spec["ref"])
        mux_by_ref[spec["ref"]] = fp
        com = [p.GetNetname() for p in fp.Pads() if p.GetNumber() == "1"][0]
        if int(pin_of_net[com]) != com_pins[m]:
            bad += 1
            print("  MISMATCH %s output: board pin %s, firmware %d" % (spec["ref"], pin_of_net[com], com_pins[m]))
    channel_of_pin = {p: int(f[1:]) for p, f in G.MUX_PINS.items() if f.startswith("I")}
    for k in G.keys():
        out = [p.GetNetname() for p in b.FindFootprintByReference(k["sensor"]).Pads() if p.GetNumber() == "2"][0]
        found = None
        for m, spec in enumerate(G.MUXES):
            for p in mux_by_ref[spec["ref"]].Pads():
                if p.GetNetname() == out:
                    found = (m, channel_of_pin[int(p.GetNumber())])
        fw = table[k["row"] * G.GRID_COLS + k["col"]]
        note = first[k["row"]] + 3 * (k["col"] - first_col[k["row"]])
        if found is None or fw != found[0] * 16 + found[1] or note != k["note"]:
            bad += 1
            print("  MISMATCH", k["ref"], "board", found, "firmware", fw, "note", note, k["note"])
    print("firmware check: %d/%d keys reach the inputs the firmware reads, %d mismatches" % (len(G.keys()), len(G.keys()), bad))
    return bad


PLATE_PATH = os.path.join(KICAD_DIR, "etuttino_plate.kicad_pcb")


def build_plate():
    """The switch plate as a copper-less FR4 'PCB': outline + 14 mm cutouts +
    M2 holes, in the same coordinates as the main board so everything lines
    up. Order it from the same fab (1.6 mm FR4 is the usual MX plate)."""
    global board
    main_board = board
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(G.PLATE_THICKNESS))
    ox = min(x for x, _ in G.PLATE_OUTLINE)
    oy = min(y for _, y in G.PLATE_OUTLINE)
    pw = max(x for x, _ in G.PLATE_OUTLINE) - ox
    ph = max(y for _, y in G.PLATE_OUTLINE) - oy

    def outline(pts):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            seg = pcbnew.PCB_SHAPE(board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetStart(mm(ax, ay))
            seg.SetEnd(mm(bx, by))
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetWidth(pcbnew.FromMM(0.1))
            board.Add(seg)

    def rect(x0, y0, x1, y1):
        outline([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])

    outline(G.plate_outline())
    half = G.CUTOUT / 2
    for k in G.keys():
        rect(k["cx"] - half, k["cy"] - half, k["cx"] + half, k["cy"] + half)
    for i, (x, y) in enumerate(G.mounting_holes(), start=1):
        if G.in_plate(x, y):
            h = load(lib("MountingHole"), "MountingHole_2.2mm_M2")
            h.SetReference("H%d" % i)
            h.Reference().SetVisible(False)
            h.SetPosition(mm(x, y))
            board.Add(h)
    text("eTuttino plate v0.7 (1.6 mm)", ox + pw / 2, oy + ph - 2.0, 1.2)
    pcbnew.SaveBoard(PLATE_PATH, board)
    print("saved", PLATE_PATH)
    board = main_board

    out = os.path.join(FAB_DIR, "plate_gerbers")
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):
        os.remove(os.path.join(out, name))
    cli("pcb", "export", "gerbers", "--output", out + os.sep,
        "--layers", "F.Cu,B.Cu,F.Silkscreen,F.Mask,B.Mask,Edge.Cuts", PLATE_PATH)
    cli("pcb", "export", "drill", "--output", out + os.sep, "--format", "excellon",
        "--excellon-separate-th", PLATE_PATH)
    zip_path = os.path.join(FAB_DIR, "etuttino_plate_gerbers.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(out)):
            z.write(os.path.join(out, name), name)
    print("wrote", zip_path)
    try:
        cli("pcb", "render", "--side", "top", "--width", "1600", "--height", "900",
            "--output", os.path.join(FAB_DIR, "etuttino_plate_top.png"), PLATE_PATH)
    except subprocess.CalledProcessError:
        print("plate render failed")


def route_with_retries(max_attempts=20):
    """The router is greedy: a net routed early can wall off a later one.
    When a sensor output fails, start again (a fresh process, so no state
    leaks) with that net routed first, up to max_attempts times. The order
    that worked is printed so it can be reused."""
    first = [n for n in os.environ.get("ETUTTINO_ROUTE_FIRST", DEFAULT_ROUTE_FIRST).split(",") if n]
    for attempt in range(max_attempts):
        env = dict(os.environ, ETUTTINO_ROUTE_FIRST=",".join(first), ETUTTINO_CHILD="1")
        r = subprocess.run([sys.executable, os.path.abspath(__file__)], env=env, capture_output=True, text=True)
        sys.stdout.write(r.stdout[-6000:])
        failed = [l.split("(")[-1].rstrip(")") for l in r.stdout.splitlines() if l.startswith("ROUTING FAILED")]
        if r.returncode == 0 or not failed:
            print("attempt %d: exit %d, route-first order: %s" % (attempt + 1, r.returncode, ",".join(first) or "-"))
            return r.returncode
        print("attempt %d: %s failed, retrying with it first" % (attempt + 1, failed[0]))
        first = [failed[0]] + [n for n in first if n != failed[0]]
    return 1


def renders():
    """The manuals' pictures (assembly3d.py) were made for the #78 board and
    its FreeCAD case, both gone: the case is case/ now (CadQuery, with its
    own renders). They need redoing for the v7 board before --renders works
    again."""
    raise SystemExit("--renders: assembly3d.py still describes the #78 board; see renders.__doc__")


if __name__ == "__main__" and "--renders" in sys.argv:
    renders()
    sys.exit(0)

if __name__ == "__main__" and not os.environ.get("ETUTTINO_CHILD"):
    sys.exit(route_with_retries())

if __name__ == "__main__":
    try:
        build()
    except RoutingFailed:
        # keep the half-routed board for a look at what blocked the route
        pcbnew.SaveBoard(os.path.join(KICAD_DIR, "etuttino_failed.kicad_pcb"), board)
        sys.exit(3)
    errs, unc = fab()
    mismatches = verify_against_firmware()
    build_plate()
    sys.exit(1 if errs or unc or mismatches else 0)
