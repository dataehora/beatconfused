"""eTutti Student V3 -- the USB pair redone: both lines on B.Cu, no via, matched length, over a GND island on In2.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/refaz_usb.py

Why (J, 19 Nov 2026: "eliminate any chance of an unstable USB connection, it is critical for MIDI"). The first V3 routing
left D- 17 mm long with two vias and 6.5 mm on F.Cu, D+ 12 mm: 5 mm of skew, 0.2 / 0.24 mm widths, no coupling, and
In2 under the pair was the +3V3 pour with signal tracks in it. The SPEC of the V1 asked for <= 2 mm of skew, <= 2 vias,
continuous GND underneath. Now that the USB-C, the ESD chip and the module are all on the bottom, the pair can stay on
B.Cu from end to end:

  * D+ and D- are written out from the pads (hand-computed 45-degree polylines, like viaggio_micromod/pcb/route_usb.py),
    0.2 mm wide; the pair is coupled at 0.327 mm pitch (gap 0.127: ~92 ohm differential on the 7628 prepreg of
    JLC04121H-7628, see viaggio_micromod/pcb/build/impedance.json) wherever the pads allow it; the fan-out to the
    ESD chip's pads (1.9 mm apart) and to the module's 0.5 mm pitch pads is the only place they part;
  * the two turns of the long run (left, then right) make the outer line change from D- to D+, so the lengths
    balance by themselves; a small trombone takes up what is left (skew <= 0.15 mm);
  * under the pair In2 gets a GND island (priority over the +3V3 pour) and a keep-out for tracks and vias, so the
    return current finds a continuous reference 0.21 mm below; GND vias stitch it to the In1 plane;
  * the .kicad_dru gets: USB only on B.Cu, gap >= 0.127 between the two lines, >= 0.3 mm to any other net away from the
    three parts' courtyards.
What the new pair displaces is taken out by DRC and routed again with the V2/V3 router (viaggio_j1/rota_restante.py).

Reads kicad/student_v03.kicad_pcb (the board of build_board_v3.py / troca_jack.py) and writes it back.
Set V3_ATTEMPTS / V3_EXPAND to shorten a run; progress is in build/progress.log.
"""
import collections
import json
import math
import os
import sys
import time

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(V3, ".."))
V2 = os.path.join(HW, "student_v02")
sys.path.insert(0, HERE)
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V2, "pcb"))
sys.path.insert(0, V2)
sys.path.insert(0, os.path.join(HW, "viaggio_j1"))
import build_board_v3 as B3     # noqa: E402  (also sets BB.NAME / KDIR / BUILD / BOARD)
import build_board as BB        # noqa: E402
import rota_restante as rr      # noqa: E402

MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
BOARD, KDIR, BUILD, NAME = B3.BOARD, B3.KDIR, B3.BUILD, B3.NAME
W = 0.2                                     # track width, both lines
PITCH = 0.327                               # centre-to-centre where coupled (gap 0.127)
MARGIN_IN2 = 0.5                            # In2 keep-out: edge of the track + this

# ---------------------------------------------------------------- the pair (KiCad mm, y down)
# J201 (USB-C, bottom): B6 (9.99, 15.25) and A6 (9.99, 16.25) are D+, A7 (9.99, 15.75) and B7 (9.99, 16.75) are D-.
# D+ pads joined on the west of the pads (loop round A7's west end), D- pads joined on the east (a short bridge across
# A6's east end). U201 (USBLC6, bottom): D+ pins 6 (16.01, 12.55) and 1 (18.29, 12.55), D- pins 4 (16.01, 14.45) and
# 3 (18.29, 14.45); the board's track runs pad to pad over the chip (the chip's own tie is a tap on it).
# J101 (M.2): D+ on pad 3 (22.23, 9.25), D- on pad 5 (22.23, 9.75).
DP_LOOP = [(9.29, 16.15), (9.14, 16.15), (8.95, 15.95), (8.95, 15.50), (9.14, 15.30), (9.29, 15.30)]
DN_BRIDGE = [(10.64, 15.80), (10.79, 15.80), (10.99, 16.00), (10.99, 16.45), (10.79, 16.65), (10.64, 16.65)]
C = 26.85                                   # D+ diagonal: x + y = C ; D- diagonal: x + y = C + PITCH * sqrt(2)
CN = C + PITCH * math.sqrt(2)
XV = 19.673                                 # D+ vertical run (x), D- is PITCH to the east of it
XVN = XV + PITCH


def dp_path(extra=0.0):
    y0 = 15.15
    return [(10.64, y0), (C - y0, y0), (C - 12.55, 12.55), (XV - 0.4, 12.55), (XV, 12.15), (XV, 9.65), (XV + 0.4, 9.25), (21.9, 9.25)]


def dn_path(extra=0.0):
    yN = 15.15 + PITCH
    y_top = (XV + 9.65 + PITCH * math.sqrt(2)) - XVN          # D- diagonal: x + y = XV + 9.65 + PITCH * sqrt(2)
    return [(10.99, 16.00), (10.99 + (16.00 - yN), yN), (CN - yN, yN), (CN - 14.45, 14.45), (XVN - 0.427, 14.45), (XVN, 14.02),
            (XVN, y_top), (XVN + (y_top - 9.577), 9.577), (21.3, 9.577), (21.47, 9.75), (21.9, 9.75)]


def plen(p):
    return sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1))


def trombone(path, seg, amount, side):
    """Lengthen `path` by `amount` mm with a rectangular bump (two 45-degree-free steps of height h) on straight
    segment `seg` (index of its first point); side = +1/-1 is the perpendicular direction to bump towards."""
    (x0, y0), (x1, y1) = path[seg], path[seg + 1]
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy * side, ux * side
    h = amount / 2.0                        # up h and back down h: +2h, minus nothing (the base is shortened by 0)
    a = L / 2 - 0.4
    b2 = L / 2 + 0.4
    pts = [(x0 + ux * a, y0 + uy * a), (x0 + ux * a + nx * h, y0 + uy * a + ny * h),
           (x0 + ux * b2 + nx * h, y0 + uy * b2 + ny * h), (x0 + ux * b2, y0 + uy * b2)]
    return path[:seg + 1] + pts + path[seg + 1:]


def seg_dist(p, a, b2):
    (px, py), (ax, ay), (bx, by) = p, a, b2
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg_dist(a0, a1, b0, b1):
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    if cross(a0, a1, b0) * cross(a0, a1, b1) < 0 and cross(b0, b1, a0) * cross(b0, b1, a1) < 0:
        return 0.0
    return min(seg_dist(a0, b0, b1), seg_dist(a1, b0, b1), seg_dist(b0, a0, a1), seg_dist(b1, a0, a1))


def clear_near(b, polylines, margin):
    """Take out the copper of other nets that touches or comes within `margin` (mm, edge to edge) of the new pair
    (a via that overlaps a track is turned into that track's net when KiCad saves: a short, so it must go first)."""
    segs = [(pl[i], pl[i + 1]) for pl in polylines for i in range(len(pl) - 1)]
    gone = collections.Counter()
    for t in list(b.GetTracks()):
        if t.GetNetname() in ("USB_DP", "USB_DN"):
            continue
        if t.GetClass() == "PCB_VIA":
            c = (TOMM(t.GetPosition().x), TOMM(t.GetPosition().y))
            r = TOMM(t.GetWidth(pcbnew.F_Cu)) / 2
            if any(seg_dist(c, a, z) < r + W / 2 + margin for a, z in segs):
                gone["via " + t.GetNetname()] += 1
                BB.rm(b, t)
        elif t.GetLayer() == pcbnew.B_Cu:
            a0 = (TOMM(t.GetStart().x), TOMM(t.GetStart().y))
            a1 = (TOMM(t.GetEnd().x), TOMM(t.GetEnd().y))
            r = TOMM(t.GetWidth()) / 2
            if any(seg_seg_dist(a0, a1, a, z) < r + W / 2 + margin for a, z in segs):
                gone["trilha " + t.GetNetname()] += 1
                BB.rm(b, t)
    return dict(gone)


def build_paths():
    """D+ and D- polylines (after the length trombone) and their through-path lengths from B6 / A7."""
    dp, dn = dp_path(), dn_path()
    dp_len = plen([(9.99, 15.25)] + dp)
    dn_len = plen([(9.99, 15.75), (10.64, 15.80), (10.79, 15.80)] + dn)
    first = {"D+": round(dp_len, 3), "D-": round(dn_len, 3)}
    diff = dp_len - dn_len
    if abs(diff) > 0.1:
        if diff > 0:       # D- shorter: bump (east, away from D+) on its vertical
            idx = [i for i in range(len(dn) - 1) if dn[i] == (XVN, 14.02)][0]
            dn = trombone(dn, idx, abs(diff), +1)
        else:              # D+ shorter: bump (west, away from D-) on its vertical
            idx = [i for i in range(len(dp) - 1) if dp[i] == (XV, 12.15)][0]
            dp = trombone(dp, idx, abs(diff), -1)
    dp_len = plen([(9.99, 15.25)] + dp)
    dn_len = plen([(9.99, 15.75), (10.64, 15.80), (10.79, 15.80)] + dn)
    return dp, dn, {"antes_do_ajuste": first, "D+": round(dp_len, 3), "D-": round(dn_len, 3), "diferenca": round(dp_len - dn_len, 3)}


def add_in2_zones(b, dp, dn):
    """Keep-out for tracks and vias on In2 under the pair, and a GND island (priority over the +3V3 pour) there."""
    segs = corridor_segments(dp, dn)
    ls_in2 = pcbnew.LSET()
    ls_in2.AddLayer(pcbnew.In2_Cu)
    ko = pcbnew.ZONE(b)
    ko.SetIsRuleArea(True)
    ko.SetDoNotAllowTracks(True)
    ko.SetDoNotAllowVias(True)
    ko.SetDoNotAllowZoneFills(False)
    ko.SetLayerSet(ls_in2)
    ko.SetZoneName("USB: In2 limpa sob o par")
    o = ko.Outline()
    for p0, p1 in segs:
        o.NewOutline()
        for (qx, qy) in seg_rect(p0, p1, W / 2 + MARGIN_IN2, 0.3):
            o.Append(MM(qx), MM(qy))
    b.Add(ko)
    gz = pcbnew.ZONE(b)
    gz.SetLayer(pcbnew.In2_Cu)
    gz.SetNet(b.FindNet("GND"))
    gz.SetAssignedPriority(10)
    gz.SetZoneName("USB: ilha de GND na In2")
    gz.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    gz.SetMinThickness(MM(0.2))
    go = gz.Outline()
    for p0, p1 in segs:
        go.NewOutline()
        for (qx, qy) in seg_rect(p0, p1, 1.3, 0.8):
            go.Append(MM(qx), MM(qy))
    b.Add(gz)


def add_via(b, x, y, net, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(pcbnew.F_Cu, MM(d))
    v.SetDrill(MM(drill))
    v.SetNet(b.FindNet(net))
    b.Add(v)
    return v


def add_track(b, p0, p1, net, layer=pcbnew.B_Cu, w=W, lock=True):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(p0[0]), MM(p0[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(p1[0]), MM(p1[1])))
    t.SetLayer(layer)
    t.SetWidth(MM(w))
    t.SetNet(b.FindNet(net))
    t.SetLocked(lock)
    b.Add(t)
    return t


def add_poly(b, pts, net, **kw):
    made = []
    for i in range(len(pts) - 1):
        if pts[i] != pts[i + 1]:
            made.append(add_track(b, pts[i], pts[i + 1], net, **kw))
    return made


def seg_rect(p0, p1, half, ext=None):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    ext = half if ext is None else ext
    ex, ey = ux * ext, uy * ext
    return [(x0 - ex + nx * half, y0 - ey + ny * half), (x1 + ex + nx * half, y1 + ey + ny * half),
            (x1 + ex - nx * half, y1 + ey - ny * half), (x0 - ex - nx * half, y0 - ey - ny * half)]


def corridor_segments(dp, dn, xmin=11.8, xmax=21.35):
    """Segments (and the half-width round them) that need a clean reference on In2: the whole pair between the
    J201 joins and the module's pad row."""
    out = []
    for path in (dp, dn):
        for i in range(len(path) - 1):
            p0, p1 = path[i], path[i + 1]
            if max(p0[0], p1[0]) < xmin or min(p0[0], p1[0]) > xmax:
                continue
            out.append((p0, p1))
    return out


def main():
    os.makedirs(BUILD, exist_ok=True)
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    report = {}
    # ---- rules
    dru_path = os.path.join(KDIR, NAME + ".kicad_dru")
    dru = open(dru_path, encoding="utf-8").read()
    i0 = dru.index('(rule "USB: 0,2')
    i1 = dru.index('(rule "Corrente: minimo 0,8')
    dru = dru[:i0] + """(rule "USB: so em B.Cu (par de ponta a ponta no fundo, sem vias, sobre a ilha de GND da In2)"
    (condition "A.NetClass == 'USB' && A.Type == 'track' && A.Layer != 'B.Cu'")
    (constraint disallow track))
(rule "USB: 0,2 mm, vao do par >= 0,127"
    (condition "A.NetClass == 'USB' && A.Type == 'track'")
    (constraint track_width (min 0.19mm) (opt 0.2mm))
    (constraint diff_pair_gap (min 0.127mm)))
(rule "USB: 0,25 mm de qualquer outra rede (a ilha de cobre de GND fica de fora), fora dos patios do J201, U201 e J101"
    (condition "A.NetClass == 'USB' && B.NetClass != 'USB' && A.Type == 'track' && B.Type != 'Zone' && !A.intersectsCourtyard('J201') && !A.intersectsCourtyard('U201') && !A.intersectsCourtyard('J101')")
    (constraint clearance (min 0.25mm)))
""" + dru[i1:]
    open(dru_path, "w", encoding="utf-8").write(dru)

    # ---- take the old pair out
    for t in list(b.GetTracks()):
        if t.GetNetname() in ("USB_DP", "USB_DN"):
            BB.rm(b, t)
    dp, dn, lens = build_paths()
    report["comprimento"] = lens
    # ---- the ESD chip's two middle pins sit between the two lines (1.9 mm apart). VBUS (pin 5) keeps its via in the gap
    # between the chip's columns; GND (pin 2, east column) gets a via in the pocket east of the pad, between D+ and
    # D-. R202 (CC2's 5.1k) goes to the north side of the pair, next to the GND pad, so CC2 never crosses it.
    for t in list(b.GetTracks()):
        n_ = t.GetNetname()
        if n_ == "CC2":
            BB.rm(b, t)

    r202 = b.FindFootprintByReference("R202")
    r202.SetPosition(pcbnew.VECTOR2I(MM(12.4), MM(12.75)))
    r202.SetOrientationDegrees(180)
    report["R202"] = {str(p_.GetNumber()): (round(TOMM(p_.GetPosition().x), 3), round(TOMM(p_.GetPosition().y), 3))
                      for p_ in r202.Pads()}
    report["tirado_perto_do_par"] = clear_near(b, [DP_LOOP, dp, DN_BRIDGE, dn], 0.32)
    print("tirado perto do par:", report["tirado_perto_do_par"], flush=True)
    keep = set()
    made = []
    made += add_poly(b, DP_LOOP, "USB_DP")
    made += add_poly(b, dp, "USB_DP")
    made += add_poly(b, DN_BRIDGE, "USB_DN")
    made += add_poly(b, dn, "USB_DN")
    made += add_poly(b, [(18.29, 13.5), (19.33, 13.5)], "GND", w=0.3, lock=False)
    made.append(add_via(b, 19.33, 13.5, "GND"))
    for t in made:
        keep.add(t.m_Uuid.AsString())
    report["pontas"] = {"dp": dp, "dn": dn}
    # ---- In2: keep-out + GND island under the corridor
    add_in2_zones(b, dp, dn)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    json.dump(report, open(os.path.join(HERE, "refaz_usb.json"), "w", encoding="utf-8"), indent=1)
    print("comprimentos:", report["comprimento"], flush=True)

    # ---- what the pair displaced goes, then everything open is routed again (as build_board_v3.py does)
    B3.rip_by_drc(b, original, report, keep, "depois do par", set(), dangling=False)
    _astar = rr.astar
    expand = int(os.environ.get("V3_EXPAND", "10000000"))
    attempts = int(os.environ.get("V3_ATTEMPTS", "6"))
    rr.astar = lambda *a, **kw: _astar(*a, **dict(kw, max_expand=expand))
    prog = open(os.path.join(BUILD, "progress.log"), "w", encoding="utf-8")

    def say(*a):
        prog.write(" ".join(str(x) for x in a) + "\n")
        prog.flush()
    all_nets = sorted({p_.GetNetname() for p_ in b.GetPads() if p_.GetNetname() and not p_.GetNetname().startswith("unconnected-")})
    first = None
    fails = []
    for attempt in range(1, attempts + 1):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        ctx = rr.Ctx(b)
        chk = rr.Checker(ctx)
        made2, log, fails = [], [], []
        opened = [n_ for n_ in all_nets if n_ not in BB.PLANES and len(rr.clusters(b, n_)) > 1]
        if first is None:
            first = sorted(opened, key=lambda n_: (rr.klass(n_) != "Corrente", n_))
        order = [n_ for n_ in first if n_ in opened] + [n_ for n_ in opened if n_ not in first]
        say("tentativa", attempt, "abertas:", order)
        for net in order:
            before, nf, t0 = len(made2), len(fails), time.time()
            rr.join_net(ctx, chk, net, None, made2, log, fails)
            say("  %-12s %3d objetos %5.0f s  %s" % (net, len(made2) - before, time.time() - t0, fails[nf:]))
        for _round in range(3):
            before = len(made2)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
            ctx.refresh()
            chk = rr.Checker(ctx)
            rr.join_net(ctx, chk, "+3V3", None, made2, log, fails)
            rr.join_net(ctx, chk, "GND", None, made2, log, fails, gnd_mode=True)
            say("  GND/+3V3 rodada", _round + 1, len(made2) - before, "objetos")
            if len(made2) == before:
                break
        print("tentativa %d: %d objetos, falhas %s" % (attempt, len(made2), sorted({f["net"] for f in fails})), flush=True)
        say("falhas:", fails)
        if not fails or attempt == attempts:
            break
        ids = set(made2)
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in ids:
                BB.rm(b, t)
        bad = [f["net"] for f in fails]
        first = [n_ for n_ in order if n_ in bad] + [n_ for n_ in order if n_ not in bad]
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d = B3.rip_by_drc(b, original, report, keep, "depois de rotear", set())
    viol = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] == "error")
    warn = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] != "error")
    report["drc"] = {"erros": dict(viol), "avisos": dict(warn), "ligacoes_faltando": len(d.get("unconnected_items", [])),
                     "paridade": len(d.get("schematic_parity", []))}
    report["drc_detalhe"] = [(x["type"], x["description"], [(i["description"], i["pos"]) for i in x["items"]])
                             for x in d.get("violations", []) if x["severity"] == "error"][:40]
    report["faltando_detalhe"] = [[(i["description"], i["pos"]) for i in x["items"]] for x in d.get("unconnected_items", [])][:40]
    report["falhas"] = [dict(f, **{k: [float(v) for v in f[k]] for k in ("de", "ate", "em") if k in f}) for f in fails]
    json.dump(report, open(os.path.join(HERE, "refaz_usb.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("drc:", json.dumps(report["drc"]), flush=True)
    for x in report["drc_detalhe"][:20] + report["faltando_detalhe"][:20]:
        print("  ", x)
    ok = dict(viol) == BB.ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity") and not fails
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
