"""eTutti Slim (R4SL, stage 2b): the MAIN board PLACED, with NO tracks. KiCad python.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/slim/pcb/posiciona_principal.py

Reads: pcb/build/slim_netlist.net (schematic.py), case/envelope_principal.json (the Design's contract: outline, posts, knobs, connectors, FFC).
Writes: pcb/kicad_principal/slim_principal.kicad_pcb (+ .kicad_pro, .kicad_dru), pcb/principal/posicao_principal.json (positions, pads, heights, escape zone: the input of the plan,
the 3D scene and the routing stage). Never routes. Never run over a board that has been routed: it rebuilds the files.

Frame: the file uses KiCad's page frame X = 200 + x, Y = 100 - y (x, y = the instrument's frame, y towards the BACK), i.e. the board seen from ABOVE (the player's side down).
Every part sits on the BOTTOM face (JLCPCB bottom assembly).  Method:
  1. fixed parts (their place is decided by the case): FFC x4 on the outline's edge facing +x, the two angle sensors on the knob axes, the Hall switch under the OFF magnet,
     the LED on the ring, the USB-C and the P2 jack at their wall holes, the battery plug J202, the RT1062 first (orientation = the one that minimises the wire length
     to the connectors, USB, I2S and flash), then the program button;
  2. every other part, by sector, big to small: a search on a 0.5 mm grid around the anchor, four orientations, cost = weighted distance of its pads to the placed pads on the same
     nets (power nets: only the pads of its anchor IC), no courtyard overlap (0.2 mm gap), 0.3 mm from the outline, nothing inside the BGA's escape zone (2.5 mm all round) or a post's disc.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import sexpr as S  # noqa: E402

KD = os.path.join(HERE, "kicad_principal")
OUTD = os.path.join(HERE, "principal")
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
SLIM_FP = os.path.join(HERE, "kicad", "slim.pretty")
ENV = json.load(open(os.path.join(HW, "case", "envelope_principal.json"), encoding="utf-8"))
M, T = pcbnew.FromMM, pcbnew.ToMM
OXK, OYK = 200.0, 100.0
GRAVE = []
ESCAPE = 2.5
EDGE_MARGIN = 0.3
GAP = 0.1                                     # half of the 0.2 mm courtyard gap


def K(x, y):                                 # instrument -> KiCad page
    return OXK + x, OYK - y


def I(X, Y):                                 # KiCad page -> instrument
    return X - OXK, OYK - Y


def VEC(X, Y):
    return pcbnew.VECTOR2I(M(X), M(Y))


def parse_netlist(path):
    tree = S.parse(open(path, encoding="utf-8").read())
    comps = {}
    for c in S.find(S.first(tree, "components"), "comp"):
        ref = S.first(c, "ref")[1]
        fields = {}
        for f in S.find(S.first(c, "fields"), "field"):
            fields[S.first(f, "name")[1]] = f[-1] if isinstance(f[-1], str) and f[-1] != S.first(f, "name")[1] else ""
        sp = S.first(c, "sheetpath")
        comps[ref] = {"value": S.first(c, "value")[1], "fp": S.first(c, "footprint")[1], "fields": fields,
                      "path": S.first(sp, "tstamps")[1].rstrip("/") + "/" + S.first(c, "tstamps")[1]}
    nets = {}
    pins = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        for x in S.find(n, "node"):
            r, p = S.first(x, "ref")[1], S.first(x, "pin")[1]
            nets.setdefault(name, []).append((r, p))
            pins.setdefault(r, {})[p] = name
    return comps, nets, pins


def load_fp(spec):
    lib, name = spec.split(":")
    libdir = SLIM_FP if lib == "slim" else KICAD_FP + "/" + lib + ".pretty"
    fp = pcbnew.FootprintLoad(libdir, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def court(fp):
    layer = pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
    bb = fp.GetCourtyard(layer).BBox()
    if bb.GetWidth() == 0:
        bb = fp.GetBoundingBox(False)
    return (T(bb.GetX()), T(bb.GetY()), T(bb.GetX() + bb.GetWidth()), T(bb.GetY() + bb.GetHeight()))


def set_pose(fp, x, y, rot):                 # x, y in the instrument frame
    X, Y = K(x, y)
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    fp.SetPosition(VEC(X, Y))


def pad_xy(fp, num):                         # instrument frame
    p = fp.FindPadByNumber(num).GetPosition()
    return I(T(p.x), T(p.y))


def pads_xy(fp):
    return [(pd.GetNumber(), I(T(pd.GetPosition().x), T(pd.GetPosition().y))) for pd in fp.Pads()]


def rect_i(fp):                              # courtyard rectangle in the instrument frame (x0, y0, x1, y1), y up
    X0, Y0, X1, Y1 = court(fp)
    xa, ya = I(X0, Y1)
    xb, yb = I(X1, Y0)
    return (xa, ya, xb, yb)


def seg(b, x0, y0, x1, y1, layer, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VEC(*K(x0, y0)))
    s.SetEnd(VEC(*K(x1, y1)))
    s.SetLayer(layer)
    s.SetWidth(M(w))
    b.Add(s)


def text(b, s, x, y, layer, size=1.0, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetPosition(VEC(*K(x, y)))
    t.SetTextSize(pcbnew.VECTOR2I(M(size), M(size)))
    t.SetTextThickness(M(0.15))
    t.SetMirrored(mirror)
    t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    b.Add(t)


def inside_poly(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def dist_to_edge(pt, poly):
    best = 1e9
    x, y = pt
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)))
    return best


def rect_inside(r, poly, margin=EDGE_MARGIN):
    x0, y0, x1, y1 = r
    nx = max(2, int((x1 - x0) / 0.5) + 1)
    ny = max(2, int((y1 - y0) / 0.5) + 1)
    for i in range(nx + 1):
        for j in range(ny + 1):
            p = (x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny)
            if not inside_poly(p, poly) or dist_to_edge(p, poly) < margin:
                return False
    return True


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def grow(r, g):
    return (r[0] - g, r[1] - g, r[2] + g, r[3] + g)


def main():
    comps, nets, pins = parse_netlist(os.path.join(HERE, "build", "slim_netlist.net"))
    poly = [tuple(p) for p in ENV["placa"]["contorno"]]
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        seg(b, x0, y0, x1, y1, pcbnew.Edge_Cuts)
    netinfo = {}

    def net_of(name):
        if name not in netinfo:
            ni = pcbnew.NETINFO_ITEM(b, name)
            b.Add(ni)
            netinfo[name] = ni
        return netinfo[name]

    TOP_FACE = {"D401"}                     # R5SL item 6: the ring LED is soldered at home on the TOP face (a reverse-mounted 1615 has no window)
    fps = {}
    for ref, c in sorted(comps.items()):
        fp = load_fp(c["fp"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        for k in ("Codigo", "LCSC", "Montagem", "Datasheet", "Description"):
            fp.SetField(k, c["fields"].get(k, "") or "")
        for f_ in fp.GetFields():
            f_.SetVisible(False)
        for pad in fp.Pads():
            n = pins.get(ref, {}).get(pad.GetNumber())
            if n:
                pad.SetNet(net_of(n))
        b.Add(fp)
        if ref not in TOP_FACE:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fps[ref] = fp

    # ---- big nets: power / ground (excluded from the wire-length cost except through the anchor IC)
    BIG = {n for n, v in nets.items() if len(v) > 14}

    placed = {}                              # ref -> rect (instrument frame, grown by GAP)
    keepouts = []                            # (rect, name)
    for (px, py) in ENV["pilares"]["pontos"]:
        keepouts.append(((px - 3.4, py - 3.4, px + 3.4, py + 3.4), "pilar"))
    # chamfer corner (back-left): a keep-out triangle approximated by a rectangle
    # ---- helpers
    def free(rect, ignore=(), edge=True):
        if edge and not rect_inside(rect, poly):
            return False
        for r_, _ in keepouts:
            if overlap(rect, r_):
                return False
        for ref, r_ in placed.items():
            if ref in ignore:
                continue
            if overlap(rect, r_):
                return False
        return True

    def net_targets(ref, anchor_ref):
        """For each net of `ref`: the centroid of the placed pads on it (big nets: only the anchor IC's pads)."""
        out = []
        for pnum, n in pins.get(ref, {}).items():
            if n.startswith("unconnected"):
                continue
            pts = []
            for r2, p2 in nets[n]:
                if r2 == ref or r2 not in placed:
                    continue
                if n in BIG and r2 != anchor_ref:
                    continue
                if n == "GND" and r2 != anchor_ref:
                    continue
                q = fps[r2].FindPadByNumber(p2)
                if q is not None:
                    pts.append(I(T(q.GetPosition().x), T(q.GetPosition().y)))
            if pts:
                out.append((pnum, (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), 0.5 if n in BIG else 1.0))
        return out

    def cost_here(fp, ref, anchor_ref):
        tg = net_targets(ref, anchor_ref)
        c = 0.0
        for pnum, (tx, ty), w in tg:
            q = fp.FindPadByNumber(pnum)
            if q is None:
                continue
            px, py = I(T(q.GetPosition().x), T(q.GetPosition().y))
            c += w * math.hypot(px - tx, py - ty)
        return c

    def commit(ref, x, y, rot):
        fp = fps[ref]
        set_pose(fp, x, y, rot)
        placed[ref] = grow(rect_i(fp), GAP)

    # ---------------------------------------------------------------- 1. fixed parts
    rows = ENV["ffc"]
    for r in rows:
        fp = fps[r["ref"]]
        best = None
        for rot in (0, 90, 180, 270):
            set_pose(fp, r["x_borda_placa"] - 2.0, r["y"], rot)
            sig = [pad_xy(fp, str(n)) for n in range(1, 9)]
            mp = [I(T(pd.GetPosition().x), T(pd.GetPosition().y)) for pd in fp.Pads() if pd.GetNumber() == "MP"]
            if sum(p[0] for p in mp) / 2 > sum(p[0] for p in sig) / 8 + 1.0:       # the mouth (hold-down side) towards +x
                best = rot
                # pin 8 at the FRONT? the pinout is reversed on this board: pad 1 sits at the front (-y)  -> checked below
        if best is None:
            raise SystemExit("%s: no orientation with the mouth towards +x" % r["ref"])
        set_pose(fp, r["x_borda_placa"] - 2.0, r["y"], best)
        # shift so that the courtyard's +x edge sits 0.2 mm inside the outline edge
        c = rect_i(fp)
        dx = (r["x_borda_placa"] - 0.2) - c[2]
        set_pose(fp, r["x_borda_placa"] - 2.0 + dx, r["y"], best)
        # centre on the row's y by the signal pads
        sig = [pad_xy(fp, str(n)) for n in range(1, 9)]
        dy = r["y"] - sum(p[1] for p in sig) / 8
        set_pose(fp, r["x_borda_placa"] - 2.0 + dx, r["y"] + dy, best)
        r["rot"] = best
        r["pino1_y_relativo"] = round(pad_xy(fp, "1")[1] - pad_xy(fp, "8")[1], 2)
        placed[r["ref"]] = grow(rect_i(fp), GAP)

    kn = ENV["knobs"]
    for ref, pos in (("U401", kn["registros"]["eixo"]), ("U402", kn["volume"]["eixo"]), ("U403", kn["volume"]["chave_off"]["pos"])):
        commit(ref, pos[0], pos[1], 0)
    vx, vy = kn["volume"]["eixo"]
    commit("D401", vx, vy + 11.0, 0)
    # USB-C: mouth towards +y (the back wall), centred on the hole
    ux = ENV["conectores"]["usb_c"]["x"]
    fp = fps["J201"]
    ok = None
    for rot in (0, 90, 180, 270):
        set_pose(fp, ux, ENV["placa"]["faixa"]["y"][1] - 4.0, rot)
        sh = [I(T(pd.GetPosition().x), T(pd.GetPosition().y)) for pd in fp.Pads() if pd.GetNumber() == "SH"]
        sg = [pad_xy(fp, "A5")]
        if sum(p[1] for p in sh) / len(sh) > sg[0][1] + 1.0 or True:
            pass
    # the footprint's mouth is +y (courtyard larger on +y, signal pads on -y): in the board frame (y up) after the flip the mouth points to -y at rot 0
    for rot in (0, 180):
        set_pose(fp, ux, 60.0, rot)
        sg = pad_xy(fp, "A5")
        c = rect_i(fp)
        centre_y = (c[1] + c[3]) / 2
        if sg[1] < centre_y:                 # signal pads towards the FRONT, so the body (mouth) points to the BACK
            ok = rot
            break
    c = rect_i(fp)
    dy = (ENV["paredes_internas"]["tras_y"] - 0.2) - c[3]
    set_pose(fp, ux, 60.0 + dy, ok)
    placed["J201"] = grow(rect_i(fp), GAP)
    # P2 jack: mouth towards -x (the left wall); courtyard's -x edge against the left wall - 0.2
    fp = fps["J301"]
    jy = ENV["conectores"]["p2"]["y"]
    okj = None
    for rot in (0, 90, 180, 270):
        set_pose(fp, -90.0, jy, rot)
        c = rect_i(fp)
        if (c[2] - c[0]) > (c[3] - c[1]):    # long axis along x
            p1, p5 = pad_xy(fp, "1"), pad_xy(fp, "5")
            if p1[0] < p5[0]:                # pad 1 sits at the mouth end (STEP: bore entrance at the footprint's y-min end): mouth towards -x
                okj = rot
                break
    if okj is None:
        okj = 90
    set_pose(fp, -90.0, jy, okj)
    c = rect_i(fp)
    set_pose(fp, -90.0 + ((ENV["paredes_internas"]["esquerda_x"] + 0.2) - c[0]), jy + (jy - (c[1] + c[3]) / 2), okj)
    placed["J301"] = grow(rect_i(fp), GAP)
    fixed = ["J601", "J602", "J603", "J604", "U401", "U402", "U403", "D401", "J201", "J301"]

    # ---------------------------------------------------------------- 2. the RT1062: the orientation that minimises the wire length to the fixed parts
    U = fps["U101"]
    bx, by = -47.25, 33.0
    tgt = {}
    for pnum, n in pins["U101"].items():
        pts = []
        for r2, p2 in nets.get(n, []):
            if r2 in fixed and n not in BIG:
                q = fps[r2].FindPadByNumber(p2)
                pts.append(I(T(q.GetPosition().x), T(q.GetPosition().y)))
        if pts:
            tgt[pnum] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    best = None
    for rot in (0, 90, 180, 270):
        set_pose(U, bx, by, rot)
        c = sum(math.hypot(I(T(U.FindPadByNumber(p).GetPosition().x), T(U.FindPadByNumber(p).GetPosition().y))[0] - t[0],
                           I(T(U.FindPadByNumber(p).GetPosition().x), T(U.FindPadByNumber(p).GetPosition().y))[1] - t[1]) for p, t in tgt.items())
        if best is None or c < best[0]:
            best = (c, rot)
    set_pose(U, bx, by, best[1])
    rot_bga = best[1]
    placed["U101"] = grow(rect_i(U), GAP)
    esc = (bx - 6.0 - ESCAPE, by - 6.0 - ESCAPE, bx + 6.0 + ESCAPE, by + 6.0 + ESCAPE)       # the balls span +-5.8, the body +-6.0
    keepouts.append((esc, "zona de escape do BGA"))
    del placed["U101"]
    placed["U101"] = grow(rect_i(U), GAP)

    # ---------------------------------------------------------------- 3. the rest, by sector, big to small
    ANCHOR = {"P1": "U101", "P2": "U101", "P3": "U101", "P5": "U101", "E1": "J201", "E2": "J201", "E3": "U202", "E4": "U403", "E5": "U204", "E6": "J202",
              "F1": "U301", "F2": "J301", "I1": "U401", "I2": "U402", "I3": "D401", "I4": "J202", "R1": "J601", "R2": "J602", "R3": "J603", "R4": "J604", "R5": "U101"}
    HOME = {"U202": (-50.0, 57.0), "U204": (-50.0, 62.0), "J202": (-72.0, 51.5), "U301": (-86.0, 59.0), "SW403": (-84.0, 56.0), "U201": (-62.0, 62.0), "U102": (-44.0, 14.0),
            "U103": (-50.0, 14.0), "Y101": (-44.0, 20.0), "Y102": (-52.0, 20.0)}
    todo = [r for r in comps if r not in placed]
    area = {}
    for r in todo:
        c0 = fps[r]
        set_pose(c0, 0, 0, 0)
        rr = rect_i(c0)
        area[r] = (rr[2] - rr[0]) * (rr[3] - rr[1])
    # first the ICs and connectors (large), then passives
    todo.sort(key=lambda r: -area[r])
    # place anchors needed before their dependants
    order = [r for r in todo if r in ("J202", "U202", "U204", "U301", "SW403", "U201", "U102", "U103", "Y101", "Y102", "L201", "L102", "Q201")]
    rest = [r for r in todo if r not in order]
    order += rest
    report = {}
    for ref in order:
        code = comps[ref]["fields"].get("Codigo", "")
        anchor_ref = ANCHOR.get(code, "U101")
        if anchor_ref not in placed:
            anchor_ref = "U101"
        if ref in HOME:
            ax, ay = HOME[ref]
        else:
            a = fps[anchor_ref]
            q = I(T(a.GetPosition().x), T(a.GetPosition().y))
            ax, ay = q
        fp = fps[ref]
        best = None
        tried = 0
        # candidate positions: rings around the anchor, step 0.5
        cands = []
        R = 0.0
        while R < 70 and len(cands) < 4000:
            n = max(1, int(2 * math.pi * R / 0.5))
            for i in range(n):
                a_ = 2 * math.pi * i / n
                cands.append((ax + R * math.cos(a_), ay + R * math.sin(a_), R))
            R += 0.5
        found = 0
        for (cx, cy, Rr) in cands:
            if found >= 10:
                break
            ok_any = False
            for rot in (0, 90, 180, 270):
                set_pose(fp, cx, cy, rot)
                if ref == 'J202':                                      # JST SH: the mouth (hold-down tabs' side) towards -y, to the battery bay
                    sg = [I(T(pd.GetPosition().x), T(pd.GetPosition().y))[1] for pd in fp.Pads() if pd.GetNumber() in ('1', '2', '3')]
                    mp = [I(T(pd.GetPosition().x), T(pd.GetPosition().y))[1] for pd in fp.Pads() if pd.GetNumber() == 'MP']
                    if sum(mp) / len(mp) >= sum(sg) / len(sg) - 0.5:
                        continue
                rc = grow(rect_i(fp), GAP)
                if not free(rc):
                    continue
                ok_any = True
                cc = cost_here(fp, ref, anchor_ref) + 0.3 * Rr
                if best is None or cc < best[0]:
                    best = (cc, cx, cy, rot)
            if ok_any:
                found += 1
        if best is None:
            raise SystemExit("%s: no free spot" % ref)
        commit(ref, best[1], best[2], best[3])
        report[ref] = {"custo": round(best[0], 1)}

    # ---------------------------------------------------------------- 4. holes, keep-outs, silk
    for k, (px, py) in enumerate(ENV["pilares"]["pontos"]):
        fp = pcbnew.FootprintLoad(KICAD_FP + "/MountingHole.pretty", "MountingHole_2.2mm_M2")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
        fp.SetReference("H%d" % (k + 1))
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPosition(VEC(*K(px, py)))
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        for d_ in list(fp.GraphicalItems()):
            if d_.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                fp.Remove(d_)
                GRAVE.append(d_)
        b.Add(fp)
        fps["H%d" % (k + 1)] = fp

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    os.makedirs(KD, exist_ok=True)
    os.makedirs(OUTD, exist_ok=True)
    import shutil
    shutil.copy(os.path.join(HERE, 'kicad', 'fp-lib-table'), os.path.join(KD, 'fp-lib-table'))
    shutil.copytree(SLIM_FP, os.path.join(KD, 'slim.pretty'), dirs_exist_ok=True)
    out_pcb = os.path.join(KD, "slim_principal.kicad_pcb")
    pcbnew.SaveBoard(out_pcb, b)

    pro_path = os.path.join(KD, "slim_principal.kicad_pro")
    pro = json.load(open(pro_path)) if os.path.exists(pro_path) else {"meta": {"filename": "slim_principal.kicad_pro", "version": 3}}
    pro["board"] = {"design_settings": {"rules": {"min_clearance": 0.1, "min_copper_edge_clearance": 0.25, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                                                  "min_through_hole_diameter": 0.3, "min_track_width": 0.1, "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
                                                  "min_text_height": 0.8, "min_text_thickness": 0.12, "min_silk_clearance": 0.0, "min_connection": 0.1},
                                    "rule_severities": {"lib_footprint_mismatch": "ignore", "silk_edge_clearance": "ignore"}}}
    pro["net_settings"] = {"classes": [{"name": "Default", "clearance": 0.1, "track_width": 0.2, "via_diameter": 0.5, "via_drill": 0.3, "diff_pair_width": 0.2,
                                        "diff_pair_gap": 0.2, "diff_pair_via_gap": 0.25, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                                        "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)"}],
                           "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []}
    json.dump(pro, open(pro_path, "w"), indent=2)

    HEIGHT = {"BGA": 1.6, "TYPE-C": 3.25, "Jack": 5.0, "SH_SM03B": 2.9, "FFC": 1.0, "SOIC": 1.75, "FNR3015": 1.5, "L_0805": 1.3, "L_0603": 0.9, "C_0805": 1.45, "C_0603": 0.9,
              "C_0402": 0.55, "R_0402": 0.45, "R_0603": 0.55, "SOT-23": 1.1, "QFN": 1.0, "Crystal_SMD_3225": 0.8, "Crystal_SMD_3215": 0.9, "VQFN": 1.0, "Texas": 1.0, "SW_Push": 1.5, "SOD": 1.0, "LED": 0.7}
    rec = {"revisao": "R4SL", "quadro": "instrumento (x direita, y TRAS); no KiCad: X = 200 + x, Y = 100 - y", "pecas": {}, "pads": [], "orientacao": {"bga_rot": rot_bga, "ffc": {r["ref"]: r["rot"] for r in rows}},
           "escape_bga": {"retangulo": [round(v, 2) for v in esc], "largura_mm": ESCAPE}, "placa": {"contorno": poly, "z_baixo": ENV["placa"]["z_baixo"]}}
    for ref, fp in fps.items():
        c = rect_i(fp)
        h = ""
        for key, val in HEIGHT.items():
            if key in str(fp.GetFPID().GetLibItemName()):
                h = val
                break
        x, y = I(T(fp.GetX()), T(fp.GetY()))
        rec["pecas"][ref] = {"x": round(x, 3), "y": round(y, 3), "rot": round(fp.GetOrientationDegrees(), 1), "lado": "baixo" if fp.GetLayer() == pcbnew.B_Cu else "cima",
                             "patio": [round(c[0], 2), round(c[1], 2), round(c[2], 2), round(c[3], 2)], "altura_mm": h, "fp": str(fp.GetFPID().GetLibItemName()),
                             "codigo": comps.get(ref, {}).get("fields", {}).get("Codigo", "")}
        for pd in fp.Pads():
            sz = pd.GetSize()
            px, py = I(T(pd.GetPosition().x), T(pd.GetPosition().y))
            rec["pads"].append({"ref": ref, "n": pd.GetNumber(), "net": pd.GetNetname(), "x": round(px, 3), "y": round(py, 3), "w": round(T(sz.x), 3), "h": round(T(sz.y), 3), "furo": round(T(pd.GetDrillSize().x), 2)})
    json.dump(rec, open(os.path.join(OUTD, "posicao_principal.json"), "w", encoding="utf-8"), indent=1)
    print("pecas", len(comps), "BGA rot", rot_bga)
    for r in rows:
        print(r["ref"], "rot", r["rot"], "pino1-pino8 em y", r["pino1_y_relativo"])


if __name__ == "__main__":
    main()
