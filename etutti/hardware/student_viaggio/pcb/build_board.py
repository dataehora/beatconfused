"""eTutti StudentViaggio v0.2 -- make the compact board from the routed Viaggio J1 board.

    python etutti/hardware/student_viaggio/pcb/layout.py             (outline, key centres, holes)
    python etutti/hardware/student_viaggio/pcb/schematic.py          (schematic + footprints)
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_viaggio/pcb/build_board.py

The J1 board (viaggio_j1/kicad/viaggio_micromod.kicad_pcb) is read, never written. Its left block
(MicroMod, power, codec, encoders, connectors: x <= 78 mm) and the two multiplexers stay where
they are, with their routing. What this script changes:

  1. removes the 28 Gateron switches, the 28 TMAG5253 and their capacitors, the three sensor
     power gates and every track of EN_A, EN_B, NS3, SENS_EN and of the 28 OUT_Kxx nets;
  2. draws the outline of layout.json (210 x 95 mm, pointed on the right), removes what is
     left outside it, moves the M2 holes H5-H8 and adds H9-H11 (with their keep-out squares);
  3. clears the top copper where the 28 electrodes go (F.Cu tracks and vias inside the key
     circles), then every stub left hanging;
  4. puts a signal via and a FSR_Comb_D12 electrode (K01-K28) on each key centre of
     layout.json; the electrode is turned 180 deg when the via does not fit on its right;
  5. adds R601 / R602 (10 k, +3V3 to each mux common) on the back, next to the muxes;
  6. routes the 28 key nets and what steps 2-5 left open with the J1 router
     (viaggio_j1/rota_restante.py), refills the zones;
  7. runs KiCad's DRC with schematic parity. Exits non-zero on any violation.

Writes pcb/kicad/student_viaggio.kicad_pcb (+ .kicad_pro and .kicad_dru copied from the J1) and
build/student_viaggio_drc.json, build/student_viaggio_board.json (what was done, key by key).
"""
import collections
import json
import math
import os
import re
import shutil
import subprocess
import sys
import uuid

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
J1 = os.path.normpath(os.path.join(HERE, "..", "..", "viaggio_j1"))
sys.path.insert(0, HERE)
sys.path.insert(0, J1)
import footprints as FPS      # noqa: E402
import sexpr as S             # noqa: E402
import rota_restante as rr    # noqa: E402  (the J1 router; it only reads the J1 project's net classes here)

KDIR = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
NAME = "student_viaggio"
BOARD = os.path.join(KDIR, NAME + ".kicad_pcb")
J1_BOARD = os.path.join(J1, "kicad", "viaggio_micromod.kicad_pcb")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PRETTY = os.path.join(KDIR, FPS.LIB + ".pretty")
NS = uuid.UUID("3b8e6f0c-2d4a-4f61-8c7e-5a9d1e2f4b22")      # schematic.py's namespace
TITLE = "eTutti StudentViaggio v0.2 - teclas resistivas"
LAYOUT = json.load(open(os.path.join(HERE, "layout.json"), encoding="utf-8"))

MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
CLEAR_R = 6.8           # F.Cu tracks nearer than this to a key centre are taken out
VIA_R = 6.85            # vias too (the keepout is 6.5; via 0.25 + clearance 0.1)
KEY_AREA = 9.0          # GND / +3V3 stubs are pruned only this near a key centre
DEAD = ("EN_A", "EN_B", "NS3", "SENS_EN")
PLANES = ("GND", "+3V3")


GRAVE = []


def rm(b, item):
    """Remove from the board and keep the Python object alive: letting pcbnew's SWIG wrapper of a
    removed footprint be collected breaks the type table (later calls return bare SwigPyObjects)."""
    b.Remove(item)
    GRAVE.append(item)


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def xy(p):
    return TOMM(p.x), TOMM(p.y)


def dist_seg(p, a, e):
    (px, py), (ax, ay), (ex, ey) = p, a, e
    l2 = (ex - ax) ** 2 + (ey - ay) ** 2
    u = 0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * (ex - ax) + (py - ay) * (ey - ay)) / l2))
    return math.hypot(ax + u * (ex - ax) - px, ay + u * (ey - ay) - py)


def is_via(t):
    return t.GetClass() == "PCB_VIA"


def inside_board(p, margin):
    """Inside the outline polygon of layout.json, at least `margin` from its edges."""
    poly = LAYOUT["poligono"]
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c and all(dist_seg(p, poly[i], poly[(i + 1) % n]) >= margin for i in range(n))


def new_via(b, p, net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(*p))
    v.SetWidth(pcbnew.F_Cu, MM(rr.VIA_D))
    v.SetDrill(MM(rr.VIA_DRILL))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(net))
    b.Add(v)
    return v


# ---------------------------------------------------------------------------- schematic
def schematic():
    """({ref: {field: text}}, {(ref, pin): net}) from the netlist schematic.py exported."""
    path = os.path.join(BUILD, NAME + "_netlist.net")
    if not os.path.exists(path):
        raise SystemExit("run schematic.py first (%s missing)" % path)
    tree = S.parse(open(path, encoding="utf-8").read())
    fields, nets = {}, {}
    for c in S.find(S.first(tree, "components"), "comp"):
        f = {}
        d = S.first(c, "description")
        f["Description"] = d[1] if d and len(d) > 1 else ""
        fl = S.first(c, "fields")
        for x in (S.find(fl, "field") if fl else []):
            f[S.first(x, "name")[1]] = x[2] if len(x) > 2 else ""
        fields[S.first(c, "ref")[1]] = f
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1]
        for x in S.find(n, "node"):
            nets[(S.first(x, "ref")[1], S.first(x, "pin")[1])] = name
    return fields, nets


def set_fields(fp, want):
    for k in ("Description", "Codigo", "LCSC", "Montagem"):
        if k not in want:
            continue
        if fp.HasField(k):
            fp.GetField(k).SetText(want[k])
        else:
            fld = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, k)
            fld.SetText(want[k])
            fld.SetVisible(False)
            fld.SetLayer(pcbnew.F_Fab)
            fp.Add(fld)


# ---------------------------------------------------------------------------- pruning
def prune(b, nets, keys, keep_vias, extra_pts):
    """Remove track ends that touch nothing, and signal vias left on fewer than two layers."""
    removed = collections.Counter()
    while True:
        by_net = collections.defaultdict(list)
        for t in b.GetTracks():
            by_net[t.GetNetname()].append(t)
        pads = collections.defaultdict(list)
        for p in b.GetPads():
            pads[p.GetNetname()].append(p)

        def touches(net, pt, layer, me):
            for o in by_net[net]:
                if o is me:
                    continue
                if is_via(o):
                    if math.hypot(pt[0] - TOMM(o.GetPosition().x), pt[1] - TOMM(o.GetPosition().y)) \
                            <= TOMM(o.GetWidth(pcbnew.F_Cu)) / 2 + 0.002:
                        return True
                elif o.GetLayer() == layer and dist_seg(pt, xy(o.GetStart()), xy(o.GetEnd())) \
                        <= TOMM(o.GetWidth()) / 2 + 0.002:
                    return True
            for p in pads[net]:
                if p.IsOnLayer(layer) and p.HitTest(V(*pt)):
                    return True
            return False

        def near_key(t):
            a, e = xy(t.GetStart()), xy(t.GetEnd())
            return any(dist_seg(k, a, e) < KEY_AREA for k in keys) or \
                any(dist_seg(k, a, e) < 3.0 for k in extra_pts)

        gone = []
        for net in nets:
            for t in by_net[net]:
                if is_via(t):
                    if net == "GND" or t.m_Uuid.AsString() in keep_vias:
                        continue
                    pt = xy(t.GetPosition())
                    layers = sum(1 for L in rr.ALLCU if touches(net, pt, L, t))
                    if net == "+3V3":       # a via that fed a removed part: only the In2 pour is left on it
                        if layers == 0 and (any(math.hypot(pt[0] - k[0], pt[1] - k[1]) < KEY_AREA for k in keys)
                                            or any(math.hypot(pt[0] - k[0], pt[1] - k[1]) < 5.0 for k in extra_pts)):
                            gone.append(t)
                    elif layers < 2:
                        gone.append(t)
                    continue
                if net in PLANES and not near_key(t):
                    continue
                if not touches(net, xy(t.GetStart()), t.GetLayer(), t) or \
                        not touches(net, xy(t.GetEnd()), t.GetLayer(), t):
                    gone.append(t)
        if not gone:
            return removed
        for t in gone:
            removed[t.GetNetname()] += 1
            rm(b, t)


# ---------------------------------------------------------------------------- new parts
def link(fp, ref, sheet_path, fields):
    fp.SetReference(ref)
    fp.SetPath(pcbnew.KIID_PATH("%s/%s" % (sheet_path, uid("sym", ref, 1))))
    fp.SetSheetname("T · Teclas")
    fp.SetSheetfile(NAME + "_T.kicad_sch")
    set_fields(fp, fields[ref])


def free_spot(b, near, avoid_boxes, size=(2.6, 1.6), reach=9.0):
    """Nearest free place on the back for a 0402 (courtyard + room for its vias), on a 0.25 grid."""
    boxes = []
    for t in b.GetTracks():
        if is_via(t) or t.GetLayer() == pcbnew.B_Cu:
            bb = t.GetBoundingBox()
            boxes.append((TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())))
    for fp in b.GetFootprints():
        if fp.IsFlipped():
            bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
            boxes.append((TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())))
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu):
                bb = p.GetBoundingBox()
                boxes.append((TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())))
    boxes += avoid_boxes
    best = None
    n = int(reach / 0.25)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = near[0] + i * 0.25, near[1] + j * 0.25
            d = math.hypot(cx - near[0], cy - near[1])
            if d > reach or (best and d >= best[0]):
                continue
            for rot, (w, h) in ((0, size), (90, (size[1], size[0]))):
                x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
                if all(x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1 for bx0, by0, bx1, by1 in boxes):
                    best = (d, cx, cy, rot)
                    break
    if best is None:
        raise SystemExit("no free place for a resistor near %s" % (near,))
    return best[1:]


# ---------------------------------------------------------------------------- save + DRC
def save_and_drc(b, original):
    """pcbnew's file with the J1's (setup ...) block (stack-up, plot settings) put back; then KiCad's DRC."""
    pcbnew.SaveBoard(BOARD, b)
    new = open(BOARD, encoding="utf-8", newline="").read()

    def setup_block(text):
        i = text.index("\n\t(setup")
        depth, j = 0, i + 1
        while True:
            ch = text[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i + 1, j + 1
            j += 1
    a0, a1 = setup_block(original)
    b0, b1 = setup_block(new)
    new = new[:b0] + original[a0:a1] + new[b1:]
    new = re.sub(r"viaggio_micromod_([PEFIAT])\.kicad_sch", NAME + r"_\1.kicad_sch", new)
    open(BOARD, "w", encoding="utf-8", newline="").write(new)
    pro = json.load(open(os.path.join(J1, "kicad", "viaggio_micromod.kicad_pro"), encoding="utf-8"))
    pro["meta"]["filename"] = NAME + ".kicad_pro"
    json.dump(pro, open(os.path.join(KDIR, NAME + ".kicad_pro"), "w", encoding="utf-8"), indent=2)
    for fn in os.listdir(KDIR):
        if fn.endswith((".kicad_prl", ".lck")) or fn == "fp-info-cache":
            os.remove(os.path.join(KDIR, fn))
    out = os.path.join(BUILD, NAME + "_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
                    "-o", out, BOARD], check=False, capture_output=True)
    return json.load(open(out, encoding="utf-8"))


# ---------------------------------------------------------------------------- main
def main():
    os.makedirs(BUILD, exist_ok=True)
    if not os.path.exists(os.path.join(PRETTY, FPS.COMB_NAME + ".kicad_mod")):
        raise SystemExit("run schematic.py first (footprint library missing)")
    # a private copy of the J1 board and project: pcbnew.SaveBoard rewrites the project file next to it
    shutil.copyfile(J1_BOARD, BOARD)
    for ext in (".kicad_pro", ".kicad_dru"):
        shutil.copyfile(os.path.join(J1, "kicad", "viaggio_micromod" + ext), os.path.join(KDIR, NAME + ext))
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    sch_fields, sch_nets = schematic()
    report = {"teclas": {}, "removido": {}, "roteado": [], "falhas": []}

    # ---- 1. the J1 keys go
    keys = {}
    for n in range(1, 29):
        u = b.FindFootprintByReference("U7%02d" % n)
        out = u.FindPadByNumber("4")
        if out.GetNetname() != "OUT_K%02d" % n:
            raise SystemExit("key %d on the J1 board is not as expected" % n)
        k = LAYOUT["teclas"]["K%02d" % n]
        keys[n] = {"c": (k["x"], k["y"]), "net": out.GetNetname()}
    sheet_path = "/" + b.FindFootprintByReference("U601").GetPath().AsString().strip("/").split("/")[0]
    if b.FindFootprintByReference("U601").GetPath().AsString() != "%s/%s" % (sheet_path, uid("sym", "U601", 1)):
        raise SystemExit("the J1 board's symbol uuids are not schematic.py's")
    gates = [b.FindFootprintByReference(r) for r in ("U603", "U604", "U605", "C603")]
    drop = gates + [b.FindFootprintByReference(p % n) for n in range(1, 29) for p in ("SW%d", "U7%02d", "C7%02d")]
    old_pts = [xy(fp.GetPosition()) for fp in drop]
    touched = {p.GetNetname() for fp in drop for p in fp.Pads() if p.GetNetname() and p.GetNetname() not in DEAD}
    for fp in drop:
        rm(b, fp)
    report["removido"]["pecas"] = len(drop)
    for p in b.GetPads():
        if p.GetNetname() in DEAD:      # J101 pad 10 (Teensy pin 4): not connected now
            name = sch_nets[(p.GetParentFootprint().GetReference(), p.GetNumber())]
            if not name.startswith("unconnected-"):
                raise SystemExit("pad %s of %s: the schematic says %s" % (p.GetNumber(), p.GetParentAsString(), name))
            net = pcbnew.NETINFO_ITEM(b, name)
            b.Add(net)
            p.SetNet(net)
    centres = [k["c"] for k in keys.values()]
    key_nets = {k["net"] for k in keys.values()}
    cnt = collections.Counter()
    for t in list(b.GetTracks()):
        if t.GetNetname() in DEAD or t.GetNetname() in key_nets:
            rm(b, t)
            cnt["trilhas e vias das teclas e dos sensores da J1"] += 1

    # ---- 2. outline, holes, silkscreen guides
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_SHAPE" and d.GetLayer() in (pcbnew.Edge_Cuts, pcbnew.F_SilkS, pcbnew.B_SilkS):
            rm(b, d)        # the J1 outline and its dashed case / sector guides
    for seg in LAYOUT["contorno"]:
        sh = pcbnew.PCB_SHAPE(b)
        if seg[0] == "line":
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(V(seg[1], seg[2]))
            sh.SetEnd(V(seg[3], seg[4]))
        else:
            sh.SetShape(pcbnew.SHAPE_T_ARC)
            sh.SetArcGeometry(V(seg[1], seg[2]), V(seg[3], seg[4]), V(seg[5], seg[6]))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(MM(0.1))
        b.Add(sh)
    for t in list(b.GetTracks()):
        pts = [xy(t.GetPosition())] if is_via(t) else [xy(t.GetStart()), xy(t.GetEnd())]
        if not all(inside_board(q, 0.6) for q in pts):
            rm(b, t)
            touched.add(t.GetNetname())
            cnt["trilhas e vias fora do contorno novo"] += 1
    rule = {z.GetZoneName(): z for z in b.Zones() if z.GetIsRuleArea()}
    h1 = b.FindFootprintByReference("H1")
    h1c = xy(h1.GetPosition())
    hole_boxes = []
    for ref, (hx, hy) in LAYOUT["furos"].items():
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            fp = pcbnew.Cast_to_FOOTPRINT(h1.Duplicate(False))
            fp.SetReference(ref)
            b.Add(fp)
            fp.SetPosition(V(*h1c))
            z = pcbnew.Cast_to_ZONE(rule["M2 H1"].Duplicate(False))
            z.SetZoneName("M2 " + ref)
            b.Add(z)
            rule["M2 " + ref] = z
            report.setdefault("furos_novos", []).append(ref)
        old = xy(fp.GetPosition())
        if abs(old[0] - hx) > 0.001 or abs(old[1] - hy) > 0.001:
            fp.SetPosition(V(hx, hy))
            rule["M2 " + ref].Move(V(hx - old[0], hy - old[1]))
            hole_boxes.append((hx - 3.5, hy - 3.5, hx + 3.5, hy + 3.5))
            report.setdefault("furos_movidos", []).append(ref)
    for t in list(b.GetTracks()):       # nothing under a hole's keep-out square
        pts = [xy(t.GetPosition())] if is_via(t) else [xy(t.GetStart()), xy(t.GetEnd())]
        r = TOMM(t.GetWidth(pcbnew.F_Cu) if is_via(t) else t.GetWidth()) / 2 + 0.05
        for x0, y0, x1, y1 in hole_boxes:
            box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            hit = any(x0 - r < q[0] < x1 + r and y0 - r < q[1] < y1 + r for q in pts) or (
                not is_via(t) and any(dist_seg(c, pts[0], pts[1]) < r for c in box))
            if hit:
                rm(b, t)
                touched.add(t.GetNetname())
                cnt["trilhas e vias sob os furos novos"] += 1
                break

    # ---- 3. clear the copper under the electrodes
    for t in list(b.GetTracks()):
        net = t.GetNetname()
        if is_via(t):
            q = xy(t.GetPosition())
            if any(math.hypot(q[0] - c[0], q[1] - c[1]) < VIA_R for c in centres):
                rm(b, t)
                touched.add(net)
                cnt["vias de %s nas teclas" % (net if net in PLANES else "sinal")] += 1
        elif t.GetLayer() == pcbnew.F_Cu:
            a, e = xy(t.GetStart()), xy(t.GetEnd())
            if any(dist_seg(c, a, e) < CLEAR_R + TOMM(t.GetWidth()) / 2 for c in centres):
                rm(b, t)
                touched.add(net)
                cnt["trilhas F.Cu nas teclas"] += 1

    # ---- 4. signal vias and electrodes (turned 180 deg when the via does not fit on the right)
    chk = rr.Checker(rr.Ctx(b))
    keep_vias = set()
    tx0, tx1, ty = FPS.COMB_TAB
    def tab_hits(c, sgn):
        """Copper of another net where the GND tab would go (it pokes out of the key circle)."""
        ta, te = (c[0] + sgn * tx0, c[1] + sgn * ty), (c[0] + sgn * tx1, c[1] + sgn * ty)
        hits = []
        for t in b.GetTracks():
            if t.GetNetname() == "GND":
                continue
            if is_via(t):
                if dist_seg(xy(t.GetPosition()), ta, te) < 0.25 + 0.25 + 0.15:
                    hits.append(t)
            elif t.GetLayer() == pcbnew.F_Cu and min(
                    dist_seg(xy(t.GetStart()), ta, te), dist_seg(xy(t.GetEnd()), ta, te),
                    dist_seg(ta, xy(t.GetStart()), xy(t.GetEnd())), dist_seg(te, xy(t.GetStart()), xy(t.GetEnd()))
            ) < 0.25 + TOMM(t.GetWidth()) / 2 + 0.15:
                hits.append(t)
        return hits

    for n, k in keys.items():
        for rot, sgn in ((0, 1), (180, -1)):
            q = (k["c"][0] + sgn * FPS.COMB_VIA[0], k["c"][1] + sgn * FPS.COMB_VIA[1])
            if chk.via_ok(V(*q), k["net"]) and not tab_hits(k["c"], sgn):
                break
        else:
            raise SystemExit("key %d: the electrode fits neither way (signal via or GND tab on other copper)" % n)
        v = new_via(b, q, k["net"])
        keep_vias.add(v.m_Uuid.AsString())
        k["via"], k["rot"] = q, rot
    power = sorted(t for t in touched if rr.klass(t) == "Corrente")
    if power:
        raise SystemExit("a power net lost copper (%s): move the keys or holes instead" % power)
    pr = prune(b, sorted((touched | set(PLANES)) - key_nets), centres, keep_vias, old_pts)
    report["removido"].update(cnt)
    report["removido"]["tocos podados"] = dict(pr)

    notes = {}
    import csv
    for row in csv.DictReader(open(os.path.join(HERE, "..", "..", "pocket", "pcb", "build", "pocket_keys.csv"))):
        notes[int(row["switch"][2:])] = (row["note"], row["row"])
    gnd = b.FindNet("GND")
    for n, k in keys.items():
        fp = pcbnew.FootprintLoad(PRETTY, FPS.COMB_NAME)
        fp.SetFPID(pcbnew.LIB_ID(FPS.LIB, FPS.COMB_NAME))
        b.Add(fp)
        fp.SetPosition(V(*k["c"]))
        fp.SetOrientationDegrees(k["rot"])
        note, row = notes[n]
        fp.SetValue("tecla %s" % note)
        link(fp, "K%02d" % n, sheet_path, sch_fields)
        fp.Reference().SetVisible(False)
        for p in fp.Pads():
            p.SetNet(gnd if p.GetNumber() == "1" else b.FindNet(k["net"]))
        report["teclas"]["K%02d" % n] = {"nota": note, "centro": [round(v, 3) for v in k["c"]], "rede": k["net"],
                                         "giro": k["rot"]}

    # ---- 4. the two reference resistors
    card = [z for z in b.Zones() if z.GetZoneName() == "cartao_MicroMod"]
    avoid = []
    for z in card:
        bb = z.GetBoundingBox()
        avoid.append((TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())))
    model = b.FindFootprintByReference("R214")      # a 10 k 0402 on the back, same part (C25744)
    for ref, mux, code in (("R601", "U601", "T1"), ("R602", "U602", "T2")):
        com = b.FindFootprintByReference(mux).FindPadByNumber("1")
        x, y, rot = free_spot(b, xy(com.GetPosition()), avoid)
        fp = pcbnew.Cast_to_FOOTPRINT(model.Duplicate(False))
        b.Add(fp)
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        link(fp, ref, sheet_path, sch_fields)
        set_fields(b.FindFootprintByReference(mux), sch_fields[mux])
        fp.FindPadByNumber("1").SetNet(b.FindNet("+3V3"))
        fp.FindPadByNumber("2").SetNet(com.GetNet())
        report[ref] = {"x": round(x, 3), "y": round(y, 3), "rot": rot, "comum": com.GetNetname()}

    # ---- texts
    for d in list(b.GetDrawings()):
        if d.GetClass() != "PCB_TEXT":
            continue
        t = d.GetText()
        if t in ("T4", "T3", "area do logo"):
            rm(b, d)
        elif t.startswith("eTutti Viaggio MicroMod - placa principal"):
            d.SetText(TITLE)
            d.SetPosition(V(161.0, 95.2))
        elif t.startswith("eTutti Viaggio MicroMod - verso"):
            d.SetText("eTutti StudentViaggio v0.2 - verso: modulo, chips")
            d.SetPosition(V(161.0, 95.2))
    tb = b.GetTitleBlock()
    tb.SetTitle("eTutti StudentViaggio · placa principal")
    tb.SetRevision("v0.2")
    tb.SetDate("2026-11-14")

    def drop_dangling(when):
        """Stubs KiCad calls dangling (shorter than the via or track they end in): take them out.
        Before routing too: left in, they sat in the way of the mux inputs' escape lanes."""
        for _pass in range(10):
            d = save_and_drc(b, original)
            loose = [x for x in d.get("violations", []) if x["type"] in ("track_dangling", "via_dangling")]
            if not loose:
                break
            n = 0
            for x in loose:
                it = x["items"][0]
                m = re.search(r"\[([^\]]+)\]", it["description"])
                pos = (it["pos"]["x"], it["pos"]["y"])
                for t in list(b.GetTracks()):
                    if t.GetNetname() != m.group(1) or t.m_Uuid.AsString() in keep_vias:
                        continue
                    if is_via(t) != (x["type"] == "via_dangling"):
                        continue
                    dd = math.hypot(pos[0] - TOMM(t.GetPosition().x), pos[1] - TOMM(t.GetPosition().y)) if is_via(t) \
                        else dist_seg(pos, xy(t.GetStart()), xy(t.GetEnd()))
                    if dd < 0.02:
                        rm(b, t)
                        n += 1
                        break
            report["removido"]["pontas soltas (%s, passada %d)" % (when, _pass + 1)] = n
            if not n:
                break
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    drop_dangling("antes de rotear")
    # ---- 5. route what is open
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for n, k in keys.items():      # no new via under an electrode
        rr.PROTECT.append({"rede": "-", "pino": "K%02d" % n,
                           "caixa": [k["c"][0] - 6.6, k["c"][1] - 6.6, k["c"][0] + 6.6, k["c"][1] + 6.6],
                           "camadas": [pcbnew.F_Cu]})
    # an escape lane on B.Cu for every mux input, and room for a via beside the muxes' capacitors:
    # without them the first routes box the last pins in
    for mux in ("U601", "U602"):
        fp = b.FindFootprintByReference(mux)
        cy = TOMM(fp.GetPosition().y)
        for pad in fp.Pads():
            if pad.GetNetname() in key_nets:
                x, y = xy(pad.GetPosition())
                y2 = y - 2.6 if y < cy else y + 2.6
                rr.PROTECT.append({"rede": pad.GetNetname(), "pino": "%s.%s" % (mux, pad.GetNumber()),
                                   "caixa": [x - 0.2, min(y, y2), x + 0.2, max(y, y2)], "camadas": [pcbnew.B_Cu]})
    for ref in ("C601", "C602", "R601", "R602"):
        for pad in b.FindFootprintByReference(ref).Pads():
            x, y = xy(pad.GetPosition())
            rr.PROTECT.append({"rede": pad.GetNetname(), "pino": "%s.%s" % (ref, pad.GetNumber()),
                               "caixa": [x - 0.9, y - 0.9, x + 0.9, y + 0.9], "camadas": list(rr.RL)})

    # the long runs to the far keys need more search than the J1's leftovers did
    _astar = rr.astar
    rr.astar = lambda *a, **kw: _astar(*a, **dict(kw, max_expand=10_000_000))

    def run(k):
        pads = [q for q in b.GetPads() if q.GetNetname() == k["net"] and q.GetParentFootprint().GetReference()[0] == "U"]
        q = xy(pads[0].GetPosition())
        return math.hypot(q[0] - k["via"][0], q[1] - k["via"][1])
    first = sorted((touched - set(PLANES) - key_nets) | {"MUX_L_COM", "MUX_R_COM"})
    order = [k["net"] for k in sorted(keys.values(), key=run, reverse=True)]       # the longest runs first
    for attempt in range(1, 7):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        ctx = rr.Ctx(b)
        chk = rr.Checker(ctx)
        made, log, fails = [], [], []
        routed = []
        for net in first + order:
            if len(rr.clusters(b, net)) > 1:
                before = len(made)
                rr.join_net(ctx, chk, net, None, made, log, fails)
                routed.append({"rede": net, "objetos": len(made) - before})
        for _round in range(3):
            before = len(made)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
            ctx.refresh()
            chk = rr.Checker(ctx)
            rr.join_net(ctx, chk, "+3V3", None, made, log, fails)
            rr.join_net(ctx, chk, "GND", None, made, log, fails, gnd_mode=True)
            routed.append({"rede": "GND / +3V3 (rodada %d)" % (_round + 1), "objetos": len(made) - before})
            if len(made) == before:
                break
        report.setdefault("tentativas", []).append(
            {"tentativa": attempt, "falhas": sorted({f["net"] + " " + str(f["pinos"]) for f in fails})})
        print("tentativa %d: %d objetos, falhas %s" % (attempt, len(made), sorted({f["net"] for f in fails})), flush=True)
        if not fails or attempt == 6:
            break
        # again, with the nets that failed first; a plane pad that stayed loose gets its surroundings kept free
        ids = set(made)
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in ids:
                rm(b, t)
        bad = [f["net"] for f in fails if f["net"] in key_nets or f["net"] in first]
        first = [n for n in first if n in bad] + [n for n in first if n not in bad]
        order = [n for n in order if n in bad] + [n for n in order if n not in bad]
        for f in fails:
            if f["net"] in PLANES and "em" in f:
                x, y = float(f["em"][0]), float(f["em"][1])
                rr.PROTECT.append({"rede": f["net"], "pino": str(f["pinos"]),
                                   "caixa": [x - 1.5, y - 1.5, x + 1.5, y + 1.5], "camadas": list(rr.RL)})
    report["roteado"] = routed
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fails = [dict(f, **{k: [float(v) for v in f[k]] for k in ("de", "ate", "em") if k in f}) for f in fails]
    report["falhas"] = fails

    drop_dangling("depois de rotear")
    d = save_and_drc(b, original)
    summ = {k: dict(collections.Counter("%s (%s)" % (x["type"], x["severity"]) for x in d.get(k, [])))
            for k in ("violations", "unconnected_items", "schematic_parity")}
    report["drc"] = summ
    json.dump(report, open(os.path.join(BUILD, NAME + "_board.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("removido:", report["removido"])
    print("pentes girados 180:", [k for k, v in report["teclas"].items() if v["giro"]])
    print("R601:", report["R601"], " R602:", report["R602"])
    print("roteado:", report["roteado"])
    print("falhas:", fails)
    print("DRC:", summ)
    bad = d.get("violations") or d.get("unconnected_items") or d.get("schematic_parity") or fails
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
