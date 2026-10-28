"""eTutti Viaggio J1 -- the power block (E3 charger BQ24074 U202, E4 buck-boost TPS63001 U204 + L201)
laid out again, clean (decision of 28 Oct 2026).

Run with KiCad 10's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/energia.py <step>
    <step> = a | b | c | d | fotos <tag>

Steps (each one is a commit; each starts from the board the previous one left):
  a  clear the region (every track and via of any net inside REG, except the locked USB pair;
     tracks crossing the border are cut on it), move the authorised passives, then the input /
     output capacitors glued to the pins, the GND vias to In1 and the thermal-pad vias;
  b  the inductor loop U204.L1 -> L201 -> U204.L2 (same layer as the chip, no vias, >= 0.8);
  c  VBUS, VSYS, VBAT at 0.8 (necking only inside the .kicad_dru courtyards);
  d  the signals of the region and every other net that was cut, then the C304.2 GND.

Same writing method as rota_restante.py (PR #120/#123): the board is saved by pcbnew to a
temporary file and only the new segments / vias, the removed ones, the moved footprints and the
refilled zones are spliced into the original text; every other block is checked identical.
Re-runnable: what a step makes is recorded in energia.json; step a always starts again from the
board of BASE_COMMIT (main after PR #125), steps b-d remove what they made before.
"""
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np            # noqa: E402
import pcbnew                 # noqa: E402
from PIL import Image, ImageDraw, ImageFont   # noqa: E402
import rota_restante as rr    # noqa: E402

BOARD = rr.BOARD
BUILD = rr.BUILD
MANIFEST = os.path.join(HERE, "energia.json")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BOARD_REL = "etutti/hardware/viaggio_j1/kicad/viaggio_micromod.kicad_pcb"
BASE_COMMIT = "845bcd6"
MM, TOMM, V = rr.MM, rr.TOMM, rr.V

# the region (mm, KiCad frame: x right, y down)
REG = (50.0, 2.0, 80.0, 22.0)
KEEP_NETS = ("USB_DP", "USB_DN")


# ------------------------------------------------------------------ pictures
def _font(sz):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


NETCOL = {"GND": (60, 120, 200), "+3V3": (230, 140, 30), "VBUS": (200, 0, 0), "VSYS": (200, 0, 140),
          "VBAT": (120, 70, 0), "BB_L1": (0, 150, 0), "BB_L2": (0, 150, 0)}


def picture(b, layer, out, title, made=(), box=None, S=40.0):
    x0, y0, x1, y1 = box or (REG[0] - 3, REG[1] - 1, REG[2] + 3, REG[3] + 3)
    W, H = int((x1 - x0) * S), int((y1 - y0) * S) + 30
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    f1, f2 = _font(13), _font(10)

    def P(v):
        return ((TOMM(v.x) - x0) * S, (TOMM(v.y) - y0) * S + 30)

    def Pm(x, y):
        return ((x - x0) * S, (y - y0) * S + 30)

    def chain(ch):
        return [P(ch.CPoint(i)) for i in range(ch.PointCount())]

    outl = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outl, False)
    dr.rectangle([0, 30, W, H], fill=(205, 205, 200))
    dr.polygon(chain(outl.Outline(0)), fill=(246, 246, 240), outline=(80, 80, 80))
    zc = {"GND": (205, 225, 245), "+3V3": (252, 225, 190)}
    for z in b.Zones():
        if not z.IsOnLayer(layer):
            continue
        if z.GetIsRuleArea():
            o = z.Outline()
            for i in range(o.OutlineCount()):
                dr.polygon(chain(o.Outline(i)), outline=(150, 0, 150))
            continue
        fp = z.GetFilledPolysList(layer)
        col = zc.get(z.GetNetname(), (220, 220, 220))
        for i in range(fp.OutlineCount()):
            dr.polygon(chain(fp.Outline(i)), fill=col)
            for h in range(fp.HoleCount(i)):
                dr.polygon(chain(fp.Hole(i, h)), fill=(246, 246, 240))
    for p in b.GetPads():
        if not p.IsOnLayer(layer):
            continue
        ps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, layer, 0, MM(0.005), pcbnew.ERROR_OUTSIDE)
        col = NETCOL.get(p.GetNetname(), (110, 110, 110))
        for i in range(ps.OutlineCount()):
            dr.polygon(chain(ps.Outline(i)), fill=tuple(int(c * 0.5 + 127) for c in col), outline=(0, 0, 0))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetLayer() != layer:
            continue
        col = NETCOL.get(t.GetNetname(), (100, 100, 100))
        w = max(1, int(round(TOMM(t.GetWidth()) * S)))
        a, e = P(t.GetStart()), P(t.GetEnd())
        dr.line([a, e], fill=col, width=w)
        r = w / 2
        for q in (a, e):
            dr.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
        if t.m_Uuid.AsString() in made:
            dr.line([a, e], fill=(255, 255, 255), width=1)
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = P(t.GetPosition())
        r = rr.VIA_D / 2 * S
        col = NETCOL.get(t.GetNetname(), (100, 100, 100))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(0, 0, 0))
        rh = rr.VIA_DRILL / 2 * S
        dr.ellipse([x - rh, y - rh, x + rh, y + rh], fill=(255, 255, 255))
    # footprint references (parts on this side) and the region
    side_b = layer == pcbnew.B_Cu
    for fp in b.GetFootprints():
        if fp.IsFlipped() != side_b and layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            continue
        p = fp.GetPosition()
        x, y = P(p)
        if 0 <= x < W and 30 <= y < H:
            dr.text((x - 12, y - 7), fp.GetReference(), fill=(0, 0, 0), font=f2)
    dr.rectangle([Pm(REG[0], REG[1]), Pm(REG[2], REG[3])], outline=(0, 160, 0), width=2)
    for gx in range(int(math.ceil(x0)), int(x1) + 1):
        if gx % 5 == 0:
            dr.text((Pm(gx, y0)[0] + 1, 32), str(gx), fill=(0, 100, 0), font=f2)
            dr.line([Pm(gx, y0), Pm(gx, y0 + 0.4)], fill=(0, 100, 0))
    for gy in range(int(math.ceil(y0)), int(y1) + 1):
        if gy % 5 == 0:
            dr.text((2, Pm(x0, gy)[1] - 6), str(gy), fill=(0, 100, 0), font=f2)
    dr.text((6, 6), title, fill=(0, 0, 0), font=f1)
    img.save(out)


def fotos(tag, b=None, made=()):
    b = b or pcbnew.LoadBoard(BOARD)
    leg = ("vermelho VBUS, magenta VSYS, marrom VBAT, verde BB_L1/L2, azul GND, laranja +3V3, "
           "cinza sinais; retangulo verde = regiao")
    for L, nm, tt in ((pcbnew.F_Cu, "fcu", "F.Cu"), (pcbnew.B_Cu, "bcu", "B.Cu, visto de cima"),
                      (pcbnew.In2_Cu, "in2", "In2.Cu")):
        picture(b, L, os.path.join(BUILD, "energia_%s_%s.png" % (tag, nm)),
                "Viaggio J1 bloco de energia - %s - %s | %s" % (tag, tt, leg), made)




# ------------------------------------------------------------------ moves (authorised: E3/E4 passives,
# L201, C304 up to ~2 mm; same side, inside the outline, off the M2 rings and rule areas)
# ref: (x, y, rotation) in mm / degrees, KiCad frame
MOVES = {
    # inductor turned so its pads face U204.L2 (pin 2, top) and U204.L1 (pin 4, bottom)
    "L201": (73.75, 9.0, 90),
    # output cap of U204: VOUT pad right above pin 1, GND pad towards the PowerPAD
    "C208": (69.70, 6.0, 180),
    # input cap of U204 (VSYS, 10 uF, same part as C206): VIN pad right under pin 5
    "C202": (69.60, 12.25, 180),
    # battery cap of U202: VBAT pad facing pins 2/3, GND pad facing pin 4
    "C203": (65.45, 9.30, 270),
    # VINA filter of U204 next to pins 8 (VINA) / 7 (GND), R216 right above it
    "C209": (67.00, 8.75, 270),
    "R216": (67.00, 6.85, 270),
    # +3V3 bulk cap (was on the input side of U204)
    "C207": (65.40, 13.90, 0),
    # VSYS cap north of the block, its VSYS pad next to R216
    "C206": (64.67, 5.18, 180),
    # out of the corridor west of the charger's OUT pins (10/11), where the VSYS vias go
    "C213": (54.58, 7.17, 180),
    "C205": (59.58, 11.23, 180),
}
MAX_MOVE = 5.5


def apply_moves(b, moves):
    rec = []
    for ref, (x, y, r) in moves.items():
        fp = b.FindFootprintByReference(ref)
        p = fp.GetPosition()
        x0, y0, r0 = TOMM(p.x), TOMM(p.y), fp.GetOrientationDegrees()
        d = math.hypot(x - x0, y - y0)
        if d > MAX_MOVE:
            raise SystemExit("move of %s is %.2f mm" % (ref, d))
        fp.SetPosition(V(MM(x), MM(y)))
        fp.SetOrientationDegrees(r)
        fp.BuildCourtyardCaches()
        rec.append({"ref": ref, "de": [round(x0, 3), round(y0, 3), round(r0, 1)],
                    "para": [x, y, r], "distancia_mm": round(d, 2), "uuid": fp.m_Uuid.AsString()})
    return rec


# ------------------------------------------------------------------ clearing the region
def clip(a, e, box):
    """Parametric interval [t0, t1] of segment a-e inside box (Liang-Barsky), or None."""
    x0, y0, x1, y1 = box
    dx, dy = e[0] - a[0], e[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    return t0, t1


def clear_region(b):
    """Every track / via of any net inside REG goes, except the USB pair; a track crossing the
    border is cut on it (its outside part stays as a new segment)."""
    gone, stubs, per_net = [], [], defaultdict(lambda: [0, 0, 0.0])
    for t in list(b.GetTracks()):
        if t.GetNetname() in KEEP_NETS:
            continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if REG[0] <= TOMM(p.x) <= REG[2] and REG[1] <= TOMM(p.y) <= REG[3]:
                per_net[t.GetNetname()][1] += 1
                gone.append(t)
            continue
        if t.GetClass() != "PCB_TRACK":
            raise SystemExit("arc in the board: not handled")
        A, E = t.GetStart(), t.GetEnd()
        a, e = (TOMM(A.x), TOMM(A.y)), (TOMM(E.x), TOMM(E.y))
        c = clip(a, e, REG)
        if c is None or c[1] - c[0] < 1e-9:
            continue
        t0, t1 = c
        L = TOMM(t.GetLength())
        per_net[t.GetNetname()][0] += 1
        per_net[t.GetNetname()][2] += L * (t1 - t0)
        gone.append(t)

        def at(s):
            return V(A.x + (E.x - A.x) * s, A.y + (E.y - A.y) * s)
        for s0, s1 in ((0.0, t0), (t1, 1.0)):
            if (s1 - s0) * L > 1e-4:
                n = rr.new_track(b, t.GetNetname(), t.GetLayer(), at(s0), at(s1), round(TOMM(t.GetWidth()), 4))
                stubs.append(n)
    for t in gone:
        b.Remove(t)
    for n in stubs:
        b.Add(n)
    return gone, stubs, {k: {"trilhas": v[0], "vias": v[1], "comprimento_mm": round(v[2], 2)}
                         for k, v in sorted(per_net.items())}


# ------------------------------------------------------------------ routing restricted to the region
BAND = 0.6          # the router may go this far outside REG, to reach the cut ends
ROUTE_BOX = None    # set per step


def _outside(w, box):
    im = w.img()
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    w.poly(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return ~np.array(im, dtype=bool)


_build_masks = rr.build_masks


def build_masks_reg(ctx, w, net, widths, margin, skip=None):
    blocked, vblock = _build_masks(ctx, w, net, widths, margin, skip)
    if ROUTE_BOX is not None:
        x0, y0, x1, y1 = ROUTE_BOX
        out_t = _outside(w, (x0 - BAND, y0 - BAND, x1 + BAND, y1 + BAND))
        out_v = _outside(w, ROUTE_BOX)
        for k in blocked:
            blocked[k] = blocked[k] | out_t
        vblock = vblock | out_v
    return blocked, vblock


rr.build_masks = build_masks_reg


# ------------------------------------------------------------------ hand-placed geometry
class Geo:
    def __init__(self, b):
        self.b = b
        self.ctx = rr.Ctx(b)
        self.chk = rr.Checker(self.ctx)
        self.made = []
        self.log = []

    def sync(self):
        self.ctx.refresh()
        self.chk.rebuild()

    def _add(self, t):
        self.b.Add(t)
        self.made.append(t.m_Uuid.AsString())
        self.ctx.items.append(t)
        self.chk.add(t)

    def track(self, net, layer, pts, w, what=""):
        """A polyline; every piece checked with pcbnew's exact shapes before it is kept."""
        P = [V(MM(x), MM(y)) for x, y in pts]
        for A, E in zip(P, P[1:]):
            if not self.chk.track_ok(A, E, w, layer, net):
                raise SystemExit("geometria %s [%s]: trilha (%.3f;%.3f)-(%.3f;%.3f) %.2f toca %s"
                                 % (what, net, TOMM(A.x), TOMM(A.y), TOMM(E.x), TOMM(E.y), w, self.chk.why))
        for A, E in zip(P, P[1:]):
            self._add(rr.new_track(self.b, net, layer, A, E, w))
        self.log.append({"o_que": what, "rede": net, "camada": rr.LNAME[layer], "largura": w,
                         "pontos": [[round(x, 3), round(y, 3)] for x, y in pts],
                         "comprimento_mm": round(sum(math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                                                     for a_, b_ in zip(pts, pts[1:])), 2)})

    def via(self, net, x, y, what="", must=True):
        P = V(MM(x), MM(y))
        if not self.chk.via_ok(P, net):
            if must:
                raise SystemExit("geometria %s [%s]: via (%.3f;%.3f) nao cabe" % (what, net, x, y))
            return False
        self._add(rr.new_via(self.b, net, P))
        self.log.append({"o_que": what, "rede": net, "via": [round(x, 3), round(y, 3)]})
        return True

    def fan(self, ref, num, net, n, what, rmin=0.65, rmax=1.6, w=0.3, prefer=None):
        """Up to n vias round a pad, each with a straight stub from the pad centre (via to In1 for
        GND, to the In2 pour for +3V3). Candidates nearest first, optionally towards `prefer`."""
        fp = self.b.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        c = (TOMM(pad.GetPosition().x), TOMM(pad.GetPosition().y))
        L = pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        cands = []
        for k in range(int(round((rmax - rmin) / 0.05)) + 1):
            r = rmin + 0.05 * k
            for j in range(32):
                ang = 2 * math.pi * j / 32
                x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
                cost = r
                if prefer is not None:
                    cost += 0.3 * math.hypot(x - prefer[0], y - prefer[1])
                cands.append((cost, x, y))
        cands.sort()
        got = []
        for _c, x, y in cands:
            if len(got) >= n:
                break
            if any(math.hypot(x - gx, y - gy) < rr.VIA_D + 0.35 for gx, gy in got):
                continue
            P = V(MM(x), MM(y))
            if not self.chk.via_ok(P, net):
                continue
            # stub from the pad edge towards the via
            A = V(MM(c[0]), MM(c[1]))
            if not self.chk.track_ok(A, P, w, L, net):
                continue
            self._add(rr.new_via(self.b, net, P))
            self._add(rr.new_track(self.b, net, L, A, P, w))
            got.append((x, y))
        if len(got) < n:
            raise SystemExit("geometria %s: so %d de %d vias junto de %s.%s" % (what, len(got), n, ref, num))
        self.log.append({"o_que": what, "rede": net, "pino": "%s.%s" % (ref, num),
                         "vias": [[round(x, 3), round(y, 3)] for x, y in got]})
        return got


# ------------------------------------------------------------------ saving (splice, as rota_restante)
def save(b, original, drop_uuids, new_uuids, moved_uuids):
    tmp = os.path.join(BUILD, "energia_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for f in os.listdir(BUILD):
        if f.startswith("energia_tmp") and not f.endswith(".kicad_pcb"):
            os.remove(os.path.join(BUILD, f))
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    _h, b_new, _t = rr.top_blocks(new)
    h_old, b_old, t_old = rr.top_blocks(original)
    kind, buid = rr.kind, rr.block_uuid
    new_items = [x for x in b_new if kind(x) in ("segment", "via") and buid(x) in new_uuids]
    if len(new_items) != len(new_uuids):
        raise SystemExit("splice: %d new items in the saved copy, expected %d" % (len(new_items), len(new_uuids)))
    zones_new = {buid(x): x for x in b_new if kind(x) == "zone"}
    fps_new = {buid(x): x for x in b_new if kind(x) == "footprint"}
    out, placed, dropped, zrep, frep = [], False, 0, 0, 0
    for blk in b_old:
        k = kind(blk)
        if k in ("segment", "via", "arc") and buid(blk) in drop_uuids:
            dropped += 1
            continue
        if k == "footprint" and buid(blk) in moved_uuids:
            out.append(fps_new[buid(blk)])
            frep += 1
            continue
        if k == "zone":
            if not placed:
                out.extend(new_items)
                placed = True
            if not rr.is_rule_zone(blk):
                out.append(zones_new[buid(blk)])
                zrep += 1
                continue
        out.append(blk)
    if not placed:
        raise SystemExit("splice: no zone block in the original file")
    if frep != len(moved_uuids) or dropped != len(drop_uuids):
        raise SystemExit("splice: %d/%d footprints, %d/%d removals" % (frep, len(moved_uuids), dropped, len(drop_uuids)))
    text = h_old + "".join(out) + t_old
    _h2, b_chk, _t2 = rr.top_blocks(text)

    def keep(x, olds):
        k = kind(x)
        if k in ("segment", "via", "arc") and buid(x) in (drop_uuids if olds else new_uuids):
            return False
        if k == "zone" and not rr.is_rule_zone(x):
            return False
        if k == "footprint" and buid(x) in moved_uuids:
            return False
        return True
    keep_old = [x for x in b_old if keep(x, True)]
    keep_new = [x for x in b_chk if keep(x, False)]
    if keep_old != keep_new:
        raise SystemExit("splice: unchanged blocks differ")
    open(BOARD, "w", encoding="utf-8", newline="").write(text)
    return {"removidas": dropped, "zonas_repreenchidas": zrep, "novas": len(new_items),
            "footprints_movidos": frep, "blocos_identicos": len(keep_old)}


# ------------------------------------------------------------------ DRC
def drc(tag):
    out = os.path.join(BUILD, "drc_energia_%s.json" % tag)
    subprocess.run([rr.KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all",
                    "--format", "json", "-o", out, BOARD], check=True, capture_output=True)
    d = json.load(open(out, encoding="utf-8"))
    v, u, p = rr.drc_summary(d)
    return d, v, u, p


HARD = ("clearance", "shorting_items", "short", "hole_clearance", "hole_to_hole", "copper_edge_clearance",
        "courtyards_overlap", "items_not_allowed", "via_diameter", "hole_size", "drill_out_of_range",
        "malformed_courtyard", "pth_inside_courtyard", "npth_inside_courtyard", "solder_mask_bridge",
        "text_height", "annular_width", "track_width", "invalid_outline", "lib_footprint_mismatch")


def check(base_v, v, p):
    bad = {}
    for k, n in v.items():
        if k in ("track_dangling", "unconnected_items"):
            continue
        if n > base_v.get(k, 0):
            bad[k] = (base_v.get(k, 0), n)
    if p:
        bad["paridade"] = p
    return bad


def base_text():
    """The board of BASE_COMMIT, with the working copy's line ends (CRLF on J's PC)."""
    raw = subprocess.run(["git", "show", "%s:%s" % (BASE_COMMIT, BOARD_REL)], cwd=REPO, check=True,
                         capture_output=True).stdout.decode("utf-8").replace("\r\n", "\n")
    cur = open(BOARD, "rb").read(200)
    return raw.replace("\n", "\r\n") if b"\r\n" in cur else raw


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


# ------------------------------------------------------------------ step a: caps glued to the pins
BC = pcbnew.B_Cu


def step_a(g):
    """Input / output caps glued to the pins, GND vias to In1, PowerPAD vias (all in B.Cu, the side of
    the chips). Pin entries are 0.24-0.3 wide inside the chips' courtyards (.kicad_dru)."""
    T, Vv, F = g.track, g.via, g.fan
    # ---- U204 (TPS63001): PowerPAD vias, GND pins 3/7/9 to the PowerPAD
    for y in (8.2, 9.0, 9.8):
        Vv("GND", 69.475, y, "U204 PowerPAD")
    T("GND", BC, [(70.875, 9.0), (70.0, 9.0)], 0.24, "U204.3 PGND -> PowerPAD")
    T("GND", BC, [(68.075, 9.5), (68.9, 9.5)], 0.24, "U204.7 PS/SYNC -> PowerPAD")
    T("GND", BC, [(68.075, 8.5), (68.9, 8.5)], 0.24, "U204.9 GND -> PowerPAD")
    # output: VOUT (pin 1) straight up to C208.1; C208.2 to the PowerPAD's top finger
    T("+3V3", BC, [(70.875, 8.0), (70.875, 7.35)], 0.3, "U204.1 VOUT -> C208.1 (saida do pino)")
    T("+3V3", BC, [(70.875, 7.35), (70.7, 6.3)], 0.6, "U204.1 VOUT -> C208.1")
    T("GND", BC, [(68.85, 6.5), (69.225, 7.45)], 0.4, "C208.2 -> PowerPAD (dedo de cima)")
    # FB (pin 10, +3V3): its own via to the In2 +3V3 plane, next to the pin
    T("+3V3", BC, [(68.075, 8.0), (68.0, 7.25)], 0.2, "U204.10 FB -> via")
    Vv("+3V3", 68.0, 7.25, "U204.10 FB -> In2")
    # input: VIN (pin 5) straight down to C202.1; C202.2 to the PowerPAD's bottom finger
    T("VSYS", BC, [(70.875, 10.0), (70.875, 10.55)], 0.3, "U204.5 VIN -> C202.1 (saida do pino)")
    T("VSYS", BC, [(70.875, 10.55), (70.6, 11.75)], 0.8, "U204.5 VIN -> C202.1")
    T("GND", BC, [(68.75, 11.6), (69.225, 10.6)], 0.4, "C202.2 -> PowerPAD (dedo de baixo)")
    # VINA filter: pin 8 -> C209.1 <- R216.2; C209.2 -> pin 7
    T("BB_VINA", BC, [(68.075, 9.0), (67.85, 9.0), (67.2, 8.4)], 0.2, "U204.8 VINA -> C209.1")
    T("BB_VINA", BC, [(67.0, 7.36), (67.0, 8.27)], 0.2, "R216.2 -> C209.1")
    T("GND", BC, [(67.0, 9.3), (67.5, 9.5), (68.075, 9.5)], 0.2, "C209.2 -> U204.7")
    # ---- U202 (BQ24074): thermal pad vias, GND pins 4/5/8 to it
    for x in (61.6, 62.4):
        for y in (8.6, 9.4):
            Vv("GND", x, y, "U202 pad termico")
    T("GND", BC, [(63.438, 9.75), (62.6, 9.75)], 0.24, "U202.4 -> pad termico")
    T("GND", BC, [(62.75, 10.438), (62.75, 9.6)], 0.24, "U202.5 -> pad termico")
    T("GND", BC, [(61.25, 10.438), (61.25, 9.6)], 0.24, "U202.8 -> pad termico")
    # IN (pin 13) -> C201.1
    T("VBUS", BC, [(61.25, 7.562), (61.1, 6.55)], 0.3, "U202.13 IN -> C201.1 (saida do pino)")
    T("VBUS", BC, [(61.1, 6.55), (60.4, 5.8)], 0.8, "U202.13 IN -> C201.1")
    # BAT (pins 2/3) -> C203.1; GND pin 4 -> C203.2
    T("VBAT", BC, [(63.438, 8.75), (63.438, 9.25)], 0.24, "U202.2-3 BAT")
    T("VBAT", BC, [(63.438, 9.0), (64.35, 8.85)], 0.3, "U202.2/3 BAT -> C203.1 (saida do pino)")
    T("VBAT", BC, [(64.35, 8.85), (65.3, 8.5)], 0.8, "U202.2/3 BAT -> C203.1")
    T("GND", BC, [(63.438, 9.75), (64.2, 10.15), (64.9, 10.25)], 0.3, "U202.4 -> C203.2")
    # ---- GND vias at every cap's GND pad, +3V3 vias at the +3V3 pads (In2 plane)
    F("C208", "2", "GND", 2, "C208.2 -> In1", prefer=(67.9, 5.0))
    F("C208", "1", "+3V3", 2, "C208.1 -> In2 (+3V3 do U204 direto ao plano)", prefer=(71.3, 4.6))
    F("C202", "2", "GND", 2, "C202.2 -> In1", prefer=(68.3, 13.4))
    F("C209", "2", "GND", 1, "C209.2 -> In1", prefer=(66.3, 9.6))
    F("C201", "2", "GND", 2, "C201.2 -> In1", prefer=(63.0, 4.6))
    F("C203", "2", "GND", 2, "C203.2 -> In1", prefer=(65.5, 11.4))
    F("C206", "2", "GND", 2, "C206.2 -> In1", prefer=(63.2, 4.4))
    F("C207", "2", "GND", 2, "C207.2 -> In1", prefer=(67.0, 14.6))
    F("C207", "1", "+3V3", 2, "C207.1 -> In2", prefer=(63.6, 14.6))
    F("C205", "2", "GND", 1, "C205.2 -> In1", prefer=(58.6, 11.9))
    F("C205", "1", "+3V3", 1, "C205.1 -> In2", prefer=(60.6, 11.9))
    F("C213", "2", "GND", 1, "C213.2 -> In1", prefer=(54.0, 6.4))


# ------------------------------------------------------------------ step b: the inductor loop
def step_b(g):
    """U204.L1 -> L201.1 and U204.L2 -> L201.2 in B.Cu (the chip's layer), no vias. 0.24 only from the
    pin to the edge of U204's courtyard; 0.8 from there into the inductor pad."""
    T = g.track
    T("BB_L2", BC, [(70.875, 8.5), (71.75, 8.5)], 0.24, "U204.2 L2 (saida do pino)")
    T("BB_L2", BC, [(71.75, 8.4), (72.6, 8.4)], 0.8, "U204.2 L2 -> L201.2")
    T("BB_L1", BC, [(70.875, 9.5), (71.75, 9.5)], 0.24, "U204.4 L1 (saida do pino)")
    T("BB_L1", BC, [(71.75, 9.65), (72.6, 9.65)], 0.8, "U204.4 L1 -> L201.1")


# ------------------------------------------------------------------ routing helpers (steps c, d)
def ratio_of(x):
    """Length of a routed connection over the straight distance between its ends (>= 1 mm)."""
    if not isinstance(x.get("ate"), list):
        return None
    d = math.hypot(x["ate"][0] - x["de"][0], x["ate"][1] - x["de"][1])
    return round(x["comprimento_mm"] / max(d, 1.0), 2)


def region_nets(b):
    """Nets with copper or pads inside the region (or touching it), USB pair excepted."""
    nets = set()
    x0, y0, x1, y1 = REG
    for p in b.GetPads():
        q = p.GetPosition()
        if x0 <= TOMM(q.x) <= x1 and y0 <= TOMM(q.y) <= y1 and p.GetNetCode() > 0:
            nets.add(p.GetNetname())
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pts = [t.GetPosition()]
        else:
            pts = [t.GetStart(), t.GetEnd()]
        for q in pts:
            if x0 - BAND <= TOMM(q.x) <= x1 + BAND and y0 - BAND <= TOMM(q.y) <= y1 + BAND:
                nets.add(t.GetNetname())
    return {n for n in nets if n not in KEEP_NETS and not n.startswith("unconnected")}


def regb():
    """Pairs to join: both nearest points within 2 mm of the region (a pad that reaches into it,
    such as J202's, has its centre outside); the routing itself stays within BAND."""
    return (REG[0] - 2.0, REG[1] - 2.0, REG[2] + 2.0, REG[3] + 2.0)


def route_nets(g, nets, fails):
    global ROUTE_BOX
    ROUTE_BOX = REG
    for net in nets:
        rr.join_net(g.ctx, g.chk, net, regb(), g.made, g.log, fails)
    ROUTE_BOX = None


def step_c(g, fails):
    """VBUS, VSYS, VBAT. VSYS leaves the charger's OUT pins (10/11, west side) by two vias in the
    corridor freed there; the rest is the grid router, Corrente at 0.8 outside the courtyards."""
    T, Vv = g.track, g.via
    T("VSYS", BC, [(60.562, 8.75), (60.562, 9.25)], 0.24, "U202.10-11 OUT")
    T("VSYS", BC, [(60.562, 9.0), (59.5, 9.0)], 0.3, "U202.10/11 OUT (saida do pino)")
    T("VSYS", BC, [(59.5, 9.0), (58.6, 9.0)], 0.8, "U202.10/11 OUT -> vias")
    Vv("VSYS", 59.3, 9.0, "U202 OUT -> F.Cu")
    Vv("VSYS", 58.6, 9.0, "U202 OUT -> F.Cu")
    rr.NECK = False
    g.sync()
    route_nets(g, ["VSYS", "VBAT", "VBUS"], fails)


def step_d(g, fails, skip=()):
    nets = sorted(region_nets(g.b) - {"VBUS", "VSYS", "VBAT", "BB_L1", "BB_L2", "GND", "+3V3"} - set(skip))
    local, through = [], []
    for n in nets:
        has_pad = any(p.GetNetname() == n and REG[0] <= TOMM(p.GetPosition().x) <= REG[2]
                      and REG[1] <= TOMM(p.GetPosition().y) <= REG[3] for p in g.b.GetPads())
        (local if has_pad else through).append(n)
    route_nets(g, local + through, fails)
    return local, through


# ------------------------------------------------------------------ driver
ORDER = ["a", "b", "c", "d"]
TXT = {"a": "regiao limpa, pecas movidas, capacitores colados aos pinos e vias de GND",
       "b": "laco do indutor", "c": "VBUS, VSYS e VBAT", "d": "sinais da regiao, redes cortadas e GND do C304"}


def refill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def main():
    os.makedirs(BUILD, exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "fotos":
        fotos(sys.argv[2])
        return
    if arg not in ORDER:
        raise SystemExit(__doc__)
    m = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"etapas": {}}
    later = [s for s in ORDER[ORDER.index(arg) + 1:] if s in m["etapas"]]
    if later:
        raise SystemExit("etapas %s ja feitas depois de %s: refaca a partir da 'a'" % (later, arg))
    drop, moved_uuids, rec = set(), set(), {"txt": TXT[arg]}
    if arg == "a":
        m = {"etapas": {}, "regiao": list(REG), "base": BASE_COMMIT}
        original = base_text()
        open(BOARD, "w", encoding="utf-8", newline="").write(original)
        dbase, vb, ub, pb = drc("base")
        m["drc_base"] = {"violacoes": vb, "nao_roteadas": ub, "paridade": pb}
        b = pcbnew.LoadBoard(BOARD)
        fotos("antes", b)
        gone, stubs, per_net = clear_region(b)
        drop = {t.m_Uuid.AsString() for t in gone}
        rec["apagadas_por_rede"] = per_net
        rec["cortes_na_borda"] = len(stubs)
        rec["movidas"] = apply_moves(b, MOVES)
        moved_uuids = {x["uuid"] for x in rec["movidas"]}
        refill(b)
        g = Geo(b)
        for t in stubs:
            g.made.append(t.m_Uuid.AsString())
        step_a(g)
    else:
        # a re-run starts again from the board as the previous step left it (kept in build/)
        pre = os.path.join(BUILD, "energia_antes_de_%s.kicad_pcb" % arg)
        if arg in m["etapas"]:
            original = open(pre, encoding="utf-8", newline="").read()
            open(BOARD, "w", encoding="utf-8", newline="").write(original)
        else:
            original = open(BOARD, encoding="utf-8", newline="").read()
            open(pre, "w", encoding="utf-8", newline="").write(original)
        b = pcbnew.LoadBoard(BOARD)
        g = Geo(b)
        fails = []
        if arg == "b":
            step_b(g)
        elif arg == "c":
            step_c(g, fails)
        else:
            rec["redes"] = step_d(g, fails)
        rec["fora"] = fails
    refill(b)
    info = save(b, original, drop, set(g.made), moved_uuids)
    d, v, u, p = drc(arg)
    rec.update({"uuids": g.made, "geometria_e_rotas": g.log, "gravacao": info,
                "drc": {"violacoes": v, "nao_roteadas": u, "paridade": p}})
    rec["razoes"] = [{"rede": x["net"], "de": x["de"], "ate": x["ate"], "comprimento_mm": x["comprimento_mm"],
                      "razao": ratio_of(x)} for x in g.log if "net" in x and ratio_of(x) is not None]
    m["etapas"][arg] = rec
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    made = set()
    for s in ORDER[:ORDER.index(arg) + 1]:
        made |= set(m["etapas"][s]["uuids"])
    fotos(arg, pcbnew.LoadBoard(BOARD), made)
    print(json.dumps({"gravacao": info, "drc_base": m["drc_base"], "drc": rec["drc"]}, indent=1))
    for x in rec.get("fora", []):
        print("FORA", x)
    for x in rec["razoes"]:
        if x["razao"] and x["razao"] > 2:
            print("RAZAO > 2", x)
    bad = check(m["drc_base"]["violacoes"], v, p)
    if bad:
        print("NEW DRC PROBLEMS:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
