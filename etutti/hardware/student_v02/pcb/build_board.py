"""eTutti Student V2 -- make the board from the routed Student V1 board (SPEC v1, then v2).

    python etutti/hardware/student_v02/geometria.py
    python etutti/hardware/student_v02/pcb/schematic.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/pcb/build_board.py

The V1 board (student_v01/kicad/viaggio_micromod.kicad_pcb) is read, never written. The keyboard
(28 switches, sensors, multiplexers and their routing) stays exactly as it is. What changes, all
left of the keyboard or on the board's edge:

  1. the LED goes (D401, D402, R401, R402 and their tracks);
  2. USB-C: J201 with its protection (U201, D201, R201, R202) and their tracks move 3 mm
     towards the player (y 13 -> 16); the USB pair is only stretched where it runs along y;
  3. OUT: the headphone socket J301 and its detector parts move to y 36;
  4. IN: a second socket J302 at y 60, with R305 (bias) and C309 next to the codec;
  5. the two encoders go to the knob centres of the SPEC, (28; 44.5) and (46; 44.5), turned
     so that their pins and lugs miss the codec; C307 moves out of a lug's way;
  6. J401, the socket of the OLED's cable, on the top side between the screen and the knobs;
  7. the speaker's wire pads J501 move out from under the acoustic box;
  8. holes: H3 and H4 move (they were where the IN socket and the acoustic box are), H9 and
     H10 are new (lid screws on the right); HG1-HG10 are the spacers of the keyboard grid;
     H5-H8, between the keys, stay as the holes the base's locating pins enter;
  9. outline: corners R 6.5 (the case's inner corner is R 7).
 10. SPEC v2: J201, J301 and J302 alone step back so that their fronts are 0.3 mm behind the
     wall's inner face (x = 2.3); J501 goes in front of the rectangular acoustic box.

Then: every track or via that KiCad's DRC finds on other copper, on a hole or in a keep-out is
taken out, the stubs are pruned, and what is open is routed again with the router of the J1
(viaggio_j1/rota_restante.py). KiCad's DRC with schematic parity must come out as the V1's
(0 errors but the 3 accepted EN_B widths, 0 unconnected, parity 0); the script exits non-zero
otherwise.

Writes kicad/student_v02.kicad_pcb (+ .kicad_pro, .kicad_dru), pcb/build/student_v02_drc.json and
pcb/board.json (what was done).
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
V2 = os.path.normpath(os.path.join(HERE, ".."))
J1 = os.path.normpath(os.path.join(HERE, "..", "..", "viaggio_j1"))
V1_KICAD = os.path.normpath(os.path.join(HERE, "..", "..", "student_v01", "kicad"))
sys.path.insert(0, HERE)
sys.path.insert(0, V2)
sys.path.insert(0, J1)
import sexpr as S             # noqa: E402
import geometria as G         # noqa: E402
import rota_restante as rr    # noqa: E402

KDIR = os.path.join(V2, "kicad")
BUILD = os.path.join(HERE, "build")
NAME = "student_v02"
BOARD = os.path.join(KDIR, NAME + ".kicad_pcb")
V1_BOARD = os.path.join(V1_KICAD, "viaggio_micromod.kicad_pcb")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
NS = uuid.UUID("3b8e6f0c-2d4a-4f61-8c7e-5a9d1e2f4b22")      # schematic.py's namespace
ACCEPTED = {"track_width": 3}       # EN_B at U711, as on the V1

MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
DEAD = ("LED_R", "LED_G", "LED_R_A", "LED_G_A", "LEDR_A")
PLANES = ("GND", "+3V3")

USB_SHIFT = G.USB_Y - 13.0
OUT_SHIFT = G.OUT_Y - 25.0
USB_GROUP = ("J201", "U201", "D201", "R201", "R202")
OUT_GROUP = ("J301", "R303", "R304", "C308")
# lid screws (through the base and the board into posts of the lid) and where they were on the V1
LID_HOLES = {"H1": (88.0, 6.5), "H2": (74.0, 93.0), "H3": (6.5, 48.5), "H4": (8.0, 91.5),
             "H9": (238.0, 9.0), "H10": (238.0, 91.0)}
PIN_HOLES = ("H5", "H6", "H7", "H8")     # the base's locating pins
# SPEC v2: the sockets end 0.3 mm behind the wall's inner face. Front of the USB-C shell = 3.65 mm
# from its footprint's origin, front of the jack's collar = 2.0 mm (both from the footprints' F.Fab).
USB_DX = round(G.CONN_FRONT_X - (4.7 - 3.65), 3)
JACK_DX = round(G.CONN_FRONT_X - (2.15 - 2.0), 3)
J501_NEAR = (50.0, 93.2)        # in front of the acoustic box (SPEC v2: the box is a rectangle now)
J401_NEAR = (39.0, 33.5)
SPEAKER_FREE_R = 17.5       # nothing taller than the board's copper inside this radius of the speaker

GRAVE = []


def rm(b, item):
    """Remove from the board and keep the Python object alive (see student_viaggio/pcb/build_board.py)."""
    b.Remove(item)
    GRAVE.append(item)


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def xy(p):
    return TOMM(p.x), TOMM(p.y)


def is_via(t):
    return t.GetClass() == "PCB_VIA"


def dist_seg(p, a, e):
    (px, py), (ax, ay), (ex, ey) = p, a, e
    l2 = (ex - ax) ** 2 + (ey - ay) ** 2
    u = 0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * (ex - ax) + (py - ay) * (ey - ay)) / l2))
    return math.hypot(ax + u * (ex - ax) - px, ay + u * (ey - ay) - py)


def bbox(it):
    bb = it.GetBoundingBox()
    return TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())


# ---------------------------------------------------------------------------- schematic
def schematic():
    """({ref: {field: text, 'Value': ..}}, {(ref, pin): net}) from the netlist schematic.py exported."""
    path = os.path.join(BUILD, NAME + "_netlist.net")
    if not os.path.exists(path):
        raise SystemExit("run schematic.py first (%s missing)" % path)
    tree = S.parse(open(path, encoding="utf-8").read())
    fields, nets = {}, {}
    for c in S.find(S.first(tree, "components"), "comp"):
        f = {}
        d = S.first(c, "description")
        f["Description"] = d[1] if d and len(d) > 1 else ""
        f["Value"] = S.first(c, "value")[1]
        ds = S.first(c, "datasheet")
        f["Datasheet"] = ds[1] if ds and len(ds) > 1 and ds[1] != "~" else ""
        fl = S.first(c, "fields")
        for x in (S.find(fl, "field") if fl else []):
            f[S.first(x, "name")[1]] = x[2] if len(x) > 2 else ""
        f["dnp"] = any(S.first(p, "name") and S.first(p, "name")[1] == "dnp" for p in S.find(c, "property"))
        f["sheet"] = S.first(S.first(c, "sheetpath"), "names")[1]
        fields[S.first(c, "ref")[1]] = f
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1]
        for x in S.find(n, "node"):
            nets[(S.first(x, "ref")[1], S.first(x, "pin")[1])] = name
    return fields, nets


def set_fields(fp, want):
    for k in ("Description", "Datasheet", "Codigo", "LCSC", "Montagem"):
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


def link(fp, ref, sheet_uuid, sheet_letter, sheet_name):
    fp.SetReference(ref)
    fp.SetPath(pcbnew.KIID_PATH("/%s/%s" % (sheet_uuid, uid("sym", ref, 1))))
    fp.SetSheetname(sheet_name)
    fp.SetSheetfile("%s_%s.kicad_sch" % (NAME, sheet_letter))


def net_of(b, name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n


# ---------------------------------------------------------------------------- moving
def move_group(b, refs, inside, dx, dy, report, what, nets=None):
    """Move footprints and the copper of a region. A track with one end inside is stretched if it
    stays on the same line (it runs along the move), else it is taken out and routed again."""
    for r in refs:
        fp = b.FindFootprintByReference(r)
        p = xy(fp.GetPosition())
        fp.SetPosition(V(p[0] + dx, p[1] + dy))
    cnt = collections.Counter()
    for t in list(b.GetTracks()):
        if nets is not None and t.GetNetname() not in nets:
            continue
        if is_via(t):
            p = xy(t.GetPosition())
            if inside(p):
                t.SetPosition(V(p[0] + dx, p[1] + dy))
                cnt["vias movidas"] += 1
            continue
        a, e = xy(t.GetStart()), xy(t.GetEnd())
        ia, ie = inside(a), inside(e)
        if ia and ie:
            t.SetStart(V(a[0] + dx, a[1] + dy))
            t.SetEnd(V(e[0] + dx, e[1] + dy))
            cnt["trilhas movidas"] += 1
        elif ia or ie:
            along = (abs(a[0] - e[0]) < 1e-4 and dx == 0) or (abs(a[1] - e[1]) < 1e-4 and dy == 0)
            if along:
                if ia:
                    t.SetStart(V(a[0] + dx, a[1] + dy))
                else:
                    t.SetEnd(V(e[0] + dx, e[1] + dy))
                cnt["trilhas esticadas (%s)" % t.GetNetname()] += 1
            else:
                if rr.klass(t.GetNetname()) == "USB":
                    raise SystemExit("%s: a USB track would be cut at %s" % (what, (a, e)))
                cnt["trilhas tiradas (%s)" % t.GetNetname()] += 1
                rm(b, t)
    report[what] = dict(cnt)


def place_by_lugs(fp, centre, rot):
    """Turn an encoder and put the middle of its two lugs (= its shaft) on `centre`."""
    fp.SetOrientationDegrees(rot)
    mp = [xy(p.GetPosition()) for p in fp.Pads() if p.GetNumber() == "MP"]
    cx, cy = sum(p[0] for p in mp) / len(mp), sum(p[1] for p in mp) / len(mp)
    o = xy(fp.GetPosition())
    fp.SetPosition(V(o[0] + centre[0] - cx, o[1] + centre[1] - cy))


def obstacles(b, layer, skip_refs=(), skip_nets=()):
    """Boxes of what is on a copper layer: tracks, vias, pads, and the courtyards of that side."""
    out = []
    for t in b.GetTracks():
        if (is_via(t) or t.GetLayer() == layer) and t.GetNetname() not in skip_nets:
            out.append(bbox(t))
    side = pcbnew.B_CrtYd if layer == pcbnew.B_Cu else pcbnew.F_CrtYd
    for fp in b.GetFootprints():
        if fp.GetReference() in skip_refs:
            continue
        if fp.IsFlipped() == (layer == pcbnew.B_Cu):
            c = fp.GetCourtyard(side)
            if c.OutlineCount():
                bb = c.BBox()
                out.append((TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())))
        for p in fp.Pads():
            if p.IsOnLayer(layer) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                out.append(bbox(p))
    return out


def free_spot(boxes, near, sizes, reach, margin=0.25, ok=None):
    """Nearest free place for a box: sizes = {rot: (w, h)}. Returns (x, y, rot)."""
    best = None
    n = int(reach / 0.25)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = round(near[0] + i * 0.25, 2), round(near[1] + j * 0.25, 2)
            d = math.hypot(cx - near[0], cy - near[1])
            if d > reach or (best and d >= best[0]) or (ok and not ok(cx, cy)):
                continue
            for rot, (w, h) in sizes.items():
                x0, y0, x1, y1 = cx - w / 2 - margin, cy - h / 2 - margin, cx + w / 2 + margin, cy + h / 2 + margin
                if all(x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1 for bx0, by0, bx1, by1 in boxes):
                    best = (d, cx, cy, rot)
                    break
    if best is None:
        raise SystemExit("no free place near %s" % (near,))
    return best[1:]


def courtyard_size(fp, layer):
    bb = fp.GetCourtyard(layer).BBox()
    return TOMM(bb.GetWidth()), TOMM(bb.GetHeight())


# ---------------------------------------------------------------------------- save + DRC
def save_and_drc(b, original):
    """pcbnew's file with the V1's (setup ...) block (stack-up, plot settings) put back; then KiCad's DRC."""
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
    pro = json.load(open(os.path.join(V1_KICAD, "viaggio_micromod.kicad_pro"), encoding="utf-8"))
    pro["meta"]["filename"] = NAME + ".kicad_pro"
    json.dump(pro, open(os.path.join(KDIR, NAME + ".kicad_pro"), "w", encoding="utf-8"), indent=2)
    for fn in os.listdir(KDIR):
        if fn.endswith((".kicad_prl", ".lck")) or fn == "fp-info-cache":
            os.remove(os.path.join(KDIR, fn))
    out = os.path.join(BUILD, NAME + "_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
                    "-o", out, BOARD], check=False, capture_output=True)
    return json.load(open(out, encoding="utf-8"))


RIP_TYPES = ("clearance", "shorting_items", "hole_clearance", "copper_edge_clearance", "tracks_crossing",
             "hole_to_hole", "items_not_allowed", "via_dangling", "track_dangling", "solder_mask_bridge",
             "annular_width", "drill_out_of_range", "hole_near_hole", "courtyards_overlap")


def rip_by_drc(b, original, report, keep, when, touched, dangling=True):
    """Take out the tracks and vias KiCad's DRC objects to, until it objects to none."""
    total = collections.Counter()
    for _pass in range(25):
        d = save_and_drc(b, original)
        by_uuid = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
        gone = set()
        for x in d.get("violations", []):
            if x["type"] == "hole_to_hole" and dangling:
                # a GND stitching via too near another hole: it goes
                v = [by_uuid[i["uuid"]] for i in x["items"] if i.get("uuid") in by_uuid and is_via(by_uuid[i["uuid"]])
                     and by_uuid[i["uuid"]].GetNetname() == "GND"]
                if v and v[0].m_Uuid.AsString() not in gone:
                    gone.add(v[0].m_Uuid.AsString())
                    total["via de GND perto de outro furo"] += 1
                continue
            if x["type"] not in RIP_TYPES or x["severity"] != "error" and x["type"] not in ("via_dangling", "track_dangling"):
                continue
            if not dangling and x["type"] in ("via_dangling", "track_dangling"):
                continue        # a cut route is mended where it was cut; its two halves stay
            cand = [by_uuid[i["uuid"]] for i in x["items"] if i.get("uuid") in by_uuid and i["uuid"] not in keep]
            if not cand:
                continue
            # the one to go: never a USB track if the other can go; a signal before a supply
            cand.sort(key=lambda t: (rr.klass(t.GetNetname()) == "USB", rr.klass(t.GetNetname()) == "Corrente",
                                     t.GetNetname() in PLANES and not is_via(t)))
            t = cand[0]
            if rr.klass(t.GetNetname()) == "USB":
                raise SystemExit("DRC (%s) on a USB track: %s" % (x["type"], x["description"]))
            if x["type"] in ("via_dangling", "track_dangling"):
                # a loose end goes only if nothing hangs on it: KiCad also calls "dangling" a track that
                # ends off-centre on a pad or a via, and that one is a connection
                net = t.GetNetname()
                def joined():       # groups of the net that hold a pad
                    return sum(1 for g in rr.clusters(b, net) if any(i.GetClass() == "PAD" for i in g["items"]))
                before = joined()
                b.Remove(t)
                if joined() > before:
                    b.Add(t)
                    keep.add(t.m_Uuid.AsString())
                    total["ponta que e ligacao, mantida"] += 1
                    continue
                GRAVE.append(t)
                del by_uuid[t.m_Uuid.AsString()]
                gone.add(None)
                total["%s" % x["type"]] += 1
                continue
            gone.add(t.m_Uuid.AsString())
            total["%s (%s)" % (x["type"], t.GetNetname() if t.GetNetname() in PLANES else "sinal/alimentacao")] += 1
            touched.add(t.GetNetname())
        if not gone:
            break
        for u in gone:
            if u is not None and u in by_uuid:
                rm(b, by_uuid[u])
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    report["tirado pelo DRC (%s)" % when] = dict(total)
    return d


# ---------------------------------------------------------------------------- main
def main():
    os.makedirs(BUILD, exist_ok=True)
    shutil.copyfile(V1_BOARD, BOARD)
    shutil.copyfile(os.path.join(V1_KICAD, "viaggio_micromod.kicad_dru"), os.path.join(KDIR, NAME + ".kicad_dru"))
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    sch_fields, sch_nets = schematic()
    report = {}
    touched = set()

    def F(ref):
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit("no %s on the board" % ref)
        return fp

    # the keys must be where geometria.py says
    for i, (_row, kx, ky) in enumerate(G.KEYS):
        if not any(abs(xy(fp.GetPosition())[0] - kx) < 0.01 and abs(xy(fp.GetPosition())[1] - ky) < 0.01
                   for fp in b.GetFootprints() if re.match(r"SW\d\d?$", fp.GetReference())):
            raise SystemExit("no switch at %s" % ((kx, ky),))
    sheet_of = {}
    for fp in b.GetFootprints():
        path = fp.GetPath().AsString().strip("/").split("/")
        if len(path) == 2:
            sheet_of[fp.GetSheetfile()[-11:-10]] = (path[0], fp.GetSheetname())
    report["folhas"] = {k: v[1] for k, v in sheet_of.items()}

    # ---- 1. the LED goes
    for ref in ("D401", "D402", "R401", "R402"):
        rm(b, F(ref))
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in DEAD:
            rm(b, t)
            n += 1
    touched.add("CHGA")
    report["LED"] = {"pecas": 4, "trilhas e vias": n}

    # ---- 2. USB-C group, 3. OUT group
    move_group(b, OUT_GROUP, lambda p: p[0] < 15.6 and 19.6 < p[1] < 33.6, 0, OUT_SHIFT, report, "OUT (J301 e detector)")
    move_group(b, USB_GROUP, lambda p: p[0] < 22.0 and 10.25 < p[1] < 19.5, 0, USB_SHIFT, report, "USB-C (J201 e protecao)")
    # SPEC v2: the two sockets alone step back from the wall (their parts stay)
    move_group(b, ("J301",), lambda p: p[0] < 15.6 and 30.6 < p[1] < 41.4, JACK_DX, 0, report, "OUT recuado",
               nets=("HP_L", "HP_R", "HP_VGND", "HP_TIPSW"))
    move_group(b, ("J201",), lambda p: p[0] < 10.75 and 10.25 + USB_SHIFT < p[1] < 19.5 + USB_SHIFT, USB_DX, 0, report,
               "USB-C recuado")
    report["recuo dos conectores"] = {"frente em x": G.CONN_FRONT_X, "USB-C andou": USB_DX, "jacks andaram": JACK_DX}
    for net in ("HP_L", "HP_R", "HP_VGND", "HP_TIPSW", "HP_DET", "VBUS", "CC1", "CC2", "GND"):
        touched.add(net)

    # ---- 5. encoders
    for ref, c in zip(("SW401", "SW402"), G.KNOBS):
        fp = F(ref)
        for p in fp.Pads():
            touched.add(p.GetNetname())
        place_by_lugs(fp, c, 0)
    for ref in ("SW401", "SW402"):
        pads = {p.GetNumber(): [round(v, 2) for v in xy(p.GetPosition())] for p in F(ref).Pads() if p.GetNumber() != "MP"}
        report[ref] = {"centro": list(G.KNOBS[int(ref[-1]) - 1]), "pinos": pads}
    # C307 out of the way of SW401's lug
    c307 = F("C307")
    for t in list(b.GetTracks()):
        if t.GetNetname() == "SGTL_VAG":
            rm(b, t)
    touched.add("SGTL_VAG")
    pin5 = xy(F("U301").FindPadByNumber("5").GetPosition())
    w, h = 1.9, 1.0
    c307.SetPosition(V(-50, -50))
    x, y, rot = free_spot(obstacles(b, pcbnew.B_Cu, skip_nets=()), (pin5[0] + 0.6, pin5[1] + 1.0),
                          {0: (w, h), 90: (h, w)}, 5.0, margin=0.15)
    c307.SetPosition(V(x, y))
    c307.SetOrientationDegrees(rot)
    report["C307"] = {"x": x, "y": y, "rot": rot}

    # ---- 4. IN socket and the microphone parts
    fsheet = sheet_of["F"]
    j302 = pcbnew.Cast_to_FOOTPRINT(F("J301").Duplicate(False))
    b.Add(j302)
    link(j302, "J302", fsheet[0], "F", fsheet[1])
    p = xy(F("J301").GetPosition())
    j302.SetPosition(V(p[0], p[1] + G.IN_Y - G.OUT_Y))
    u301 = F("U301")
    mic = xy(u301.FindPadByNumber("10").GetPosition())
    for ref, model in (("C309", "C213"), ("R305", "R301")):
        fp = pcbnew.Cast_to_FOOTPRINT(F(model).Duplicate(False))
        b.Add(fp)
        link(fp, ref, fsheet[0], "F", fsheet[1])
        fp.SetPosition(V(-60, -60))
        x, y, rot = free_spot(obstacles(b, pcbnew.B_Cu), (mic[0] - 0.5, mic[1] + 2.5), {0: (1.9, 1.0), 90: (1.0, 1.9)}, 6.0,
                              margin=0.3)
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        report[ref] = {"x": x, "y": y, "rot": rot}

    # ---- 6. the OLED's socket
    isheet = sheet_of["I"]
    j401 = pcbnew.FootprintLoad(os.path.join(KICAD_FP, "Connector_JST.pretty"), "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal")
    j401.SetFPID(pcbnew.LIB_ID("Connector_JST", "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"))
    b.Add(j401)
    link(j401, "J401", isheet[0], "I", isheet[1])
    j401.SetPosition(V(-80, -80))
    cw, chh = courtyard_size(j401, pcbnew.F_CrtYd)
    x, y, rot = free_spot(obstacles(b, pcbnew.F_Cu, skip_nets=("GND",)), J401_NEAR, {0: (cw, chh)}, 8.0, margin=0.4,
                          ok=lambda cx, cy: 30.5 < cy < 36.5)
    j401.SetPosition(V(x, y))
    report["J401"] = {"x": x, "y": y, "rot": 0, "patio": [round(cw, 2), round(chh, 2)]}

    # ---- 7. speaker pads out from under the acoustic box
    j501 = F("J501")
    for p_ in j501.Pads():
        touched.add(p_.GetNetname())
    old = xy(j501.GetPosition())
    for t in list(b.GetTracks()):
        if t.GetNetname() in ("SPK_P", "SPK_N"):
            pts = [xy(t.GetPosition())] if is_via(t) else [xy(t.GetStart()), xy(t.GetEnd())]
            if any(math.hypot(q[0] - G.SPEAKER[0], q[1] - G.SPEAKER[1]) < SPEAKER_FREE_R + 1.5 for q in pts) or \
                    any(abs(q[0] - old[0]) < 6 and abs(q[1] - old[1]) < 2 for q in pts):
                rm(b, t)
    j501.SetPosition(V(-90, -90))
    bx0, by0, bx1, by1 = G.BOX_RECT
    boxes = obstacles(b, pcbnew.F_Cu, skip_nets=("GND", "+3V3")) + obstacles(b, pcbnew.B_Cu, skip_nets=("GND", "+3V3"))
    cw, chh = courtyard_size(j501, pcbnew.F_CrtYd)
    jx, jy, _rot = free_spot(boxes, J501_NEAR, {0: (cw, chh)}, 14.0, margin=0.4,
                             ok=lambda cx, cy: by1 + 2.5 < cy < 94.5 and 40.0 < cx < 62.0)
    off = xy(j501.GetCourtyard(pcbnew.F_CrtYd).BBox().GetCenter())
    j501.SetPosition(V(jx - (off[0] + 90), jy - (off[1] + 90)))
    report["J501"] = {"x": round(xy(j501.GetPosition())[0], 2), "y": round(xy(j501.GetPosition())[1], 2)}

    # ---- 8. holes
    rule = {z.GetZoneName(): z for z in b.Zones() if z.GetIsRuleArea()}
    h1 = F("H1")
    h1c = xy(h1.GetPosition())
    holes = dict(LID_HOLES)
    for k, pt in enumerate(G.grid_screws(), 1):
        holes["HG%d" % k] = tuple(pt)
    report["furos"] = {"tampa": {}, "grade": {}, "pinos da base": {}}
    for ref, (hx, hy) in holes.items():
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            fp = pcbnew.Cast_to_FOOTPRINT(h1.Duplicate(False))
            fp.SetReference(ref)
            b.Add(fp)
            fp.SetPosition(V(*h1c))
            if not ref.startswith("HG"):      # a grid spacer is plastic on plastic: no copper-free square
                z = pcbnew.Cast_to_ZONE(rule["M2 H1"].Duplicate(False))
                z.SetZoneName("M2 " + ref)
                b.Add(z)
                rule["M2 " + ref] = z
        old = xy(fp.GetPosition())
        if abs(old[0] - hx) > 0.001 or abs(old[1] - hy) > 0.001:
            fp.SetPosition(V(hx, hy))
            if "M2 " + ref in rule:
                rule["M2 " + ref].Move(V(hx - old[0], hy - old[1]))
        report["furos"]["grade" if ref.startswith("HG") else "tampa"][ref] = [hx, hy]
    for ref in PIN_HOLES:
        report["furos"]["pinos da base"][ref] = [round(v, 2) for v in xy(F(ref).GetPosition())]
    # a hole may not land on a part
    for ref, (hx, hy) in holes.items():
        for fp in b.GetFootprints():
            if fp.GetReference() in holes or fp.GetReference() in PIN_HOLES or re.match(r"SW\d\d?$", fp.GetReference()):
                continue
            for p_ in fp.Pads():
                x0, y0, x1, y1 = bbox(p_)
                if x0 - 2.0 < hx < x1 + 2.0 and y0 - 2.0 < hy < y1 + 2.0:
                    raise SystemExit("hole %s at %s is on %s" % (ref, (hx, hy), fp.GetReference()))

    # ---- 9. outline
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.Edge_Cuts:
            rm(b, d)
    x0, y0, x1, y1 = G.BOARD
    r = G.BOARD_R
    k = r * (1 - math.sqrt(0.5))

    def edge(kind, *pts):
        sh = pcbnew.PCB_SHAPE(b)
        if kind == "line":
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(V(*pts[0]))
            sh.SetEnd(V(*pts[1]))
        else:
            sh.SetShape(pcbnew.SHAPE_T_ARC)
            sh.SetArcGeometry(V(*pts[0]), V(*pts[1]), V(*pts[2]))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(MM(0.1))
        b.Add(sh)
    edge("line", (x0 + r, y0), (x1 - r, y0))
    edge("arc", (x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r))
    edge("line", (x1, y0 + r), (x1, y1 - r))
    edge("arc", (x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
    edge("line", (x1 - r, y1), (x0 + r, y1))
    edge("arc", (x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r))
    edge("line", (x0, y1 - r), (x0, y0 + r))
    edge("arc", (x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))

    # ---- the board's parts as the schematic has them: nets, values, fields, not-fitted marks
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and d.GetText() == "eTutti Student V01":
            d.SetText("eTutti Student V2")
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref not in sch_fields:
            continue
        f = sch_fields[ref]
        if fp.GetValue() != f["Value"]:
            report.setdefault("valores trocados", {})[ref] = [fp.GetValue(), f["Value"]]
            fp.SetValue(f["Value"])
        set_fields(fp, f)
        if f["dnp"] != fp.IsDNP():
            fp.SetDNP(f["dnp"])
            report.setdefault("nao montar", []).append(ref)
        for p_ in fp.Pads():
            want = sch_nets.get((ref, p_.GetNumber()))
            if want is None:
                continue
            if p_.GetNetname() != want:
                report.setdefault("redes trocadas", {})["%s.%s" % (ref, p_.GetNumber())] = [p_.GetNetname(), want]
                p_.SetNet(net_of(b, want))
                if not want.startswith("unconnected-"):
                    touched.add(want)
    missing = sorted(set(sch_fields) - {fp.GetReference() for fp in b.GetFootprints()})
    extra = sorted(fp.GetReference() for fp in b.GetFootprints()
                   if fp.GetReference() not in sch_fields and not re.match(r"(H|HG|SW)\d+$", fp.GetReference()))
    if missing or extra:
        raise SystemExit("board vs schematic: missing %s, extra %s" % (missing, extra))
    tb = b.GetTitleBlock()
    tb.SetTitle("eTutti Student V2 · placa principal")
    tb.SetRevision("SPEC v2")
    tb.SetDate("2026-11-16")

    # ---- what the DRC objects to goes, then the stubs
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    rip_by_drc(b, original, report, set(), "antes de rotear", touched, dangling=False)

    # ---- the codec's top pins. I2S_DOUT (pin 16, new) had no way out: the stubs of pins 17, 18 and 19
    # (I2S_TX, SDA, SCL) wrap over it on their way to vias on the left. The fan-out of the four pins
    # is drawn again by hand, 0.15 mm tracks on B.Cu, nested from the inside out:
    #   16 I2S_RX  -> a via where the I2S_TX one was;
    #   17 I2S_TX  -> a new via 0.6 mm further up, joined to its In2 track by a short diagonal;
    #   18 SDA, 19 SCL -> their own vias on the left, one lane further up than before.
    u301 = F("U301")
    pin = {n: xy(u301.FindPadByNumber(str(n)).GetPosition()) for n in (16, 17, 18, 19)}
    names = {16: "I2S_RX", 17: "I2S_TX", 18: "I2C_SDA", 19: "I2C_SCL"}
    for n, nm in names.items():
        if u301.FindPadByNumber(str(n)).GetNetname() != nm or abs(pin[n][1] - 34.05) > 0.01 \
                or abs(pin[n][0] - (23.2 + 0.4 * (n - 16))) > 0.01:
            raise SystemExit("U301 pin %d is not where the hand fan-out expects it" % n)
    tx_via_old, sda_via, scl_via = (22.792, 33.443), (20.442, 33.617), (20.154, 32.666)
    gone = 0
    tx_in2 = None
    for t_ in list(b.GetTracks()):
        if t_.GetNetname() not in names.values():
            continue
        if is_via(t_):
            q = xy(t_.GetPosition())
            if t_.GetNetname() == "I2S_TX" and math.hypot(q[0] - tx_via_old[0], q[1] - tx_via_old[1]) < 0.05:
                rm(b, t_)
                gone += 1
            continue
        s_, e_ = xy(t_.GetStart()), xy(t_.GetEnd())
        inbox = all(19.9 < q[0] < 25.0 and 32.3 < q[1] < 34.2 for q in (s_, e_))
        if t_.GetLayer() == pcbnew.B_Cu and inbox:
            rm(b, t_)
            gone += 1
        elif t_.GetLayer() == pcbnew.In2_Cu and t_.GetNetname() == "I2S_TX":
            if math.hypot(e_[0] - tx_via_old[0], e_[1] - tx_via_old[1]) < 0.05 or math.hypot(s_[0] - tx_via_old[0], s_[1] - tx_via_old[1]) < 0.05:
                rm(b, t_)               # the diagonal into the old via
                gone += 1
            elif abs(s_[0] - 22.511) < 0.01 and abs(e_[0] - 22.511) < 0.01 and max(s_[1], e_[1]) > 33.0:
                tx_in2 = t_
    if tx_in2 is None:
        raise SystemExit("I2S_TX: the In2 track that came down to the codec was not found")
    for nm, at_ in (("I2C_SDA", sda_via), ("I2C_SCL", scl_via)):
        if not any(is_via(t_) and t_.GetNetname() == nm and math.hypot(xy(t_.GetPosition())[0] - at_[0], xy(t_.GetPosition())[1] - at_[1]) < 0.05
                   for t_ in b.GetTracks()):
            raise SystemExit("%s: no via at %s" % (nm, at_))
    keep = set()

    def seg(net, layer, pts, w=0.15):
        for q0, q1 in zip(pts, pts[1:]):
            tr = pcbnew.PCB_TRACK(b)
            tr.SetStart(V(*q0))
            tr.SetEnd(V(*q1))
            tr.SetWidth(MM(w))
            tr.SetLayer(layer)
            tr.SetNet(net_of(b, net))
            b.Add(tr)
            keep.add(tr.m_Uuid.AsString())

    def via(net, at_):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(V(*at_))
        v.SetWidth(pcbnew.F_Cu, MM(rr.VIA_D))
        v.SetDrill(MM(rr.VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net_of(b, net))
        b.Add(v)
        keep.add(v.m_Uuid.AsString())

    tx_via = (22.82, 32.84)
    seg("I2S_RX", pcbnew.B_Cu, [pin[16], (23.2, 33.52), tx_via_old])
    via("I2S_RX", tx_via_old)
    seg("I2S_TX", pcbnew.B_Cu, [pin[17], (23.6, 33.45), (22.99, 32.84), tx_via])
    via("I2S_TX", tx_via)
    # its In2 track now ends higher and turns into the new via
    low = tx_in2.GetStart() if xy(tx_in2.GetStart())[1] > xy(tx_in2.GetEnd())[1] else tx_in2.GetEnd()
    turn = (22.511, tx_via[1] - (tx_via[0] - 22.511))
    if low == tx_in2.GetStart():
        tx_in2.SetStart(V(*turn))
    else:
        tx_in2.SetEnd(V(*turn))
    seg("I2S_TX", pcbnew.In2_Cu, [turn, tx_via], 0.2)
    y_sda, y_scl = 32.39, 32.07
    seg("I2C_SDA", pcbnew.B_Cu, [pin[18], (24.0, 33.3), (24.0 - (33.3 - y_sda), y_sda),
                                 (sda_via[0] + (sda_via[1] - y_sda), y_sda), sda_via])
    seg("I2C_SCL", pcbnew.B_Cu, [pin[19], (24.4, 33.3), (24.4 - (33.3 - y_scl), y_scl),
                                 (scl_via[0] + (scl_via[1] - y_scl), y_scl), scl_via])
    report["leque do codec"] = {"tirado": gone, "novo": len(keep), "via do I2S_RX": list(tx_via_old), "via do I2S_TX": list(tx_via)}
    fan_nets = []
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d0 = save_and_drc(b, original)
    bad0 = [(x["type"], x["description"], [(i["description"], i["pos"]) for i in x["items"]]) for x in d0.get("violations", [])
            if x["severity"] == "error" and any(i.get("uuid") in keep for i in x["items"])]
    if bad0:
        for x in bad0:
            print("leque do codec:", x)
        raise SystemExit("the hand fan-out of the codec breaks a rule")

    # ---- route what is open
    _astar = rr.astar
    expand = int(os.environ.get("V2_EXPAND", "10000000"))
    attempts = int(os.environ.get("V2_ATTEMPTS", "6"))
    rr.astar = lambda *a, **kw: _astar(*a, **dict(kw, max_expand=expand))
    prog = open(os.path.join(BUILD, "progress.log"), "w", encoding="utf-8")

    def say(*a):
        prog.write(" ".join(str(x) for x in a) + "\n")
        prog.flush()
    for ref in ("C307", "C309", "R305", "J401"):
        for pad in F(ref).Pads():
            if pad.GetNumber() == "MP":
                continue
            x, y = xy(pad.GetPosition())
            rr.PROTECT.append({"rede": pad.GetNetname(), "pino": "%s.%s" % (ref, pad.GetNumber()),
                               "caixa": [x - 0.7, y - 0.7, x + 0.7, y + 0.7], "camadas": list(rr.RL)})
    all_nets = sorted({p_.GetNetname() for p_ in b.GetPads() if p_.GetNetname() and not p_.GetNetname().startswith("unconnected-")})
    made, log, fails, routed = [], [], [], []
    first = None
    import time
    for attempt in range(1, attempts + 1):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        ctx = rr.Ctx(b)
        chk = rr.Checker(ctx)
        made, log, fails, routed = [], [], [], []
        opened = [n_ for n_ in all_nets if n_ not in PLANES and len(rr.clusters(b, n_)) > 1]
        if first is None:
            # supplies first, then the short signals round the codec, then the long ones
            first = sorted(opened, key=lambda n_: (rr.klass(n_) != "Corrente",
                                                   fan_nets.index(n_) if n_ in fan_nets else 9, n_))
        order = [n_ for n_ in first if n_ in opened] + [n_ for n_ in opened if n_ not in first]
        say("tentativa", attempt, "abertas:", order)
        for net in order:
            before, nf, t0 = len(made), len(fails), time.time()
            rr.join_net(ctx, chk, net, None, made, log, fails)
            routed.append({"rede": net, "objetos": len(made) - before})
            say("  %-12s %3d objetos %5.0f s  %s" % (net, len(made) - before, time.time() - t0, fails[nf:]))
        for _round in range(3):
            before = len(made)
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
            ctx.refresh()
            chk = rr.Checker(ctx)
            rr.join_net(ctx, chk, "+3V3", None, made, log, fails)
            rr.join_net(ctx, chk, "GND", None, made, log, fails, gnd_mode=True)
            routed.append({"rede": "GND / +3V3 (rodada %d)" % (_round + 1), "objetos": len(made) - before})
            say("  GND/+3V3 rodada", _round + 1, len(made) - before, "objetos")
            if len(made) == before:
                break
        report.setdefault("tentativas", []).append(
            {"tentativa": attempt, "falhas": sorted({f["net"] + " " + str(f["pinos"]) for f in fails})})
        print("tentativa %d: %d objetos, falhas %s" % (attempt, len(made), sorted({f["net"] for f in fails})), flush=True)
        say("falhas:", fails)
        if not fails or attempt == attempts:
            break
        ids = set(made)
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in ids:
                rm(b, t)
        bad = [f["net"] for f in fails]
        first = [n_ for n_ in order if n_ in bad] + [n_ for n_ in order if n_ not in bad]
    report["roteado"] = routed
    report["falhas"] = [dict(f, **{k: [float(v) for v in f[k]] for k in ("de", "ate", "em") if k in f}) for f in fails]
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    d = rip_by_drc(b, original, report, keep, "depois de rotear", set())
    viol = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] == "error")
    warn = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] != "error")
    report["drc"] = {"erros": dict(viol), "avisos": dict(warn), "ligacoes_faltando": len(d.get("unconnected_items", [])),
                     "paridade": len(d.get("schematic_parity", []))}
    report["drc_detalhe"] = [(x["type"], x["description"], [(i["description"], i["pos"]) for i in x["items"]])
                             for x in d.get("violations", []) if x["severity"] == "error"][:40]
    report["paridade_detalhe"] = [(x["type"], x["description"], [i["description"] for i in x["items"]])
                                  for x in d.get("schematic_parity", [])][:40]
    report["faltando_detalhe"] = [[(i["description"], i["pos"]) for i in x["items"]] for x in d.get("unconnected_items", [])][:40]
    json.dump(report, open(os.path.join(HERE, "board.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k in ("LED", "OUT (J301 e detector)", "USB-C (J201 e protecao)", "OUT recuado", "USB-C recuado", "J501", "SW401", "SW402", "C307", "C309", "R305", "J401",
              "tirado pelo DRC (antes de rotear)", "tirado pelo DRC (depois de rotear)", "roteado", "falhas", "drc"):
        print(k, ":", json.dumps(report.get(k), ensure_ascii=False))
    for x in report["drc_detalhe"][:20] + report["paridade_detalhe"][:20] + report["faltando_detalhe"][:20]:
        print("  ", x)
    ok = dict(viol) == ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity") and not fails
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
