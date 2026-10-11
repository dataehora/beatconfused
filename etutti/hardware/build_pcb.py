"""Build the routed eTuttino PCB and its fabrication files.

Run with KiCad's own Python (it ships the pcbnew module):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

It places every part from the geometry in generate.py, routes the whole
board, runs KiCad's DRC and exports everything a PCB service needs:

  kicad/etuttino.kicad_pcb        the board, open it in KiCad to inspect/edit
  fab/etuttino_gerbers.zip        Gerbers + drill files, upload this to the
                                  fab (JLCPCB, PCBWay, OSH Park, ...)
  fab/etuttino_plate_gerbers.zip  the switch plate as an FR4 "PCB" (cutouts only)
  fab/etuttino_bom.csv, fab/etuttino_cpl_bottom.csv
                                  optional: let the fab solder diodes + sockets
  fab/etuttino_drc.json           KiCad's design-rule-check report
  fab/etuttino_top.png / _bottom.png   renders for a visual check

Routing scheme (two layers):
  - each key: hot-swap socket and diode on the back (B.Cu); the socket's
    column pad drops through a via to the front,
  - columns run on the front (F.Cu), zig-zagging down the staggered rows,
    then up into the strip behind the keys,
  - rows run on the back along each key row, out to a channel on the
    right edge and up to the Teensy,
  - the last stretch to the Teensy sockets is on the back, nested so no
    two traces on the same layer cross.
"""
import json
import os
import subprocess
import sys
import zipfile

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

TRACK_W = 0.25
VIA_D = 0.6
VIA_DRILL = 0.3

# Key-local routing offsets (mm, from the switch centre, +y down).
VIA_OFFSET = (-7.6, 0.6)        # column via, just below the socket's column pad
DIODE_OFFSET = (2.0, 5.5)       # diode centre, under the switch, clear of the socket
ANODE_X = 7.6                   # anode trace runs up the right side of the key
ROW_Y = 8.5                     # row trace, between this key row and the next

# Teensy-side routing (see the module docstring).
COL_CORRIDOR_Y = {0: 26.0, 1: 25.0, 2: 24.0, 3: 23.0,          # to J1, between the sockets
                  4: 37.5, 5: 38.5, 6: 39.5, 7: 40.5, 8: 41.5}  # to J2, below the sockets
ROW_CHANNEL_X0 = 176.6          # first row channel on the right edge, then +0.6 each
ROW_TOP_Y0 = 16.0               # top row's run above J1, then 1 mm higher per row below

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


def pad(fp, number):
    for p in fp.Pads():
        if p.GetNumber() == number:
            return p
    raise KeyError(number)


def track(points, layer, net_name):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(mm(x1, y1))
        t.SetEnd(mm(x2, y2))
        t.SetWidth(pcbnew.FromMM(TRACK_W))
        t.SetLayer(layer)
        t.SetNet(net(net_name))
        board.Add(t)


def via(x, y, net_name):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(mm(x, y))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetNet(net(net_name))
    board.Add(v)


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


def build():
    keys = G.keys()

    # ---- switches + diodes, and the per-key routing on the back ----
    cathodes = {}   # row -> [(x, y)]
    col_vias = {}   # col -> [(row, x, y)]
    for k in keys:
        cx, cy = k["cx"], k["cy"]
        sw = load(LOCAL_LIB, "Kailh_MX_Hotswap_1u")
        sw.SetReference(k["ref"])
        sw.SetPosition(mm(cx, cy))
        board.Add(sw)
        col_net = "COL%d" % k["col"]
        row_net = "ROW%d" % k["row"]
        key_net = "K_%s" % k["ref"]
        pad(sw, "1").SetNet(net(col_net))
        pad(sw, "2").SetNet(net(key_net))

        d = load(os.path.join(FP_ROOT, "Diode_SMD.pretty"), "D_SOD-123")
        d.SetReference(k["diode"])
        d.SetPosition(mm(cx + DIODE_OFFSET[0], cy + DIODE_OFFSET[1]))
        board.Add(d)
        d.Flip(d.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        # Anode must end up on the right (towards the anode trace).
        if xy(pad(d, "2").GetPosition())[0] < xy(pad(d, "1").GetPosition())[0]:
            d.SetOrientationDegrees(d.GetOrientationDegrees() + 180)
        d.Reference().SetVisible(False)
        pad(d, "2").SetNet(net(key_net))   # anode -> switch
        pad(d, "1").SetNet(net(row_net))   # cathode -> row

        p1 = xy(pad(sw, "1").GetPosition())
        p2 = xy(pad(sw, "2").GetPosition())
        an = xy(pad(d, "2").GetPosition())
        ca = xy(pad(d, "1").GetPosition())
        vx, vy = cx + VIA_OFFSET[0], cy + VIA_OFFSET[1]

        track([p1, (vx, vy)], pcbnew.B_Cu, col_net)
        via(vx, vy, col_net)
        track([an, (cx + ANODE_X, an[1]), (cx + ANODE_X, cy - 3.0), p2], pcbnew.B_Cu, key_net)
        track([ca, (ca[0], cy + ROW_Y)], pcbnew.B_Cu, row_net)

        cathodes.setdefault(k["row"], []).append((ca[0], cy + ROW_Y))
        col_vias.setdefault(k["col"], []).append((k["row"], vx, vy))

    # ---- Teensy sockets ----
    pins = G.stack_pins()
    sockets = {}
    for ref in ("J1", "J2"):
        first = [p for p in pins if p[0] == ref and p[1] == 1][0]
        s = load(os.path.join(FP_ROOT, "Connector_PinSocket_2.54mm.pretty"), "PinSocket_1x14_P2.54mm_Vertical")
        s.SetReference(ref)
        s.SetPosition(mm(first[3], first[4]))
        s.SetOrientationDegrees(-90)
        board.Add(s)
        sockets[ref] = s
    pad_pos = {}
    gnd_pads = []
    for ref, number, pin, x, y in pins:
        p = pad(sockets[ref], str(number))
        got = xy(p.GetPosition())
        assert abs(got[0] - x) < 0.01 and abs(got[1] - y) < 0.01, (ref, number, got, (x, y))
        n = G.pin_net(pin)
        if n:
            p.SetNet(net(n))
            if n == "GND":
                gnd_pads.append((x, y))
            else:
                pad_pos[n] = (x, y)

    # ---- rows: along each key row on the back, out to the right channel ----
    # Rows nest without crossing when, going down the board, each row gets a
    # channel further out, a run above J1 that is higher, and a J1 pad
    # further left — so rank the rows by height, top first.
    by_height = sorted(range(len(G.ROWS)), key=lambda r: cathodes[r][0][1])
    pad_xs = [pad_pos["ROW%d" % r][0] for r in by_height]
    assert pad_xs == sorted(pad_xs, reverse=True), "ROW_PINS order would make row traces cross"
    for rank, r in enumerate(by_height):
        row_net = "ROW%d" % r
        pts = sorted(cathodes[r])
        y = pts[0][1]
        chan_x = ROW_CHANNEL_X0 + 0.6 * rank
        top_y = ROW_TOP_Y0 - rank
        # Split at every cathode so each stub ends on a segment end.
        track(pts + [(chan_x, y)], pcbnew.B_Cu, row_net)
        px, py = pad_pos[row_net]
        track([(chan_x, y), (chan_x, top_y), (px, top_y), (px, py)], pcbnew.B_Cu, row_net)

    # ---- columns: zig-zag down the rows on the front, then up to the Teensy ----
    for c, vias in col_vias.items():
        col_net = "COL%d" % c
        vias.sort(key=lambda v: v[2])   # top of the board first
        chain = [(x, y) for _, x, y in vias]
        track(chain, pcbnew.F_Cu, col_net)
        top_x, top_y = chain[0]
        cy = COL_CORRIDOR_Y[c]
        track([(top_x, top_y), (top_x, cy)], pcbnew.F_Cu, col_net)
        via(top_x, cy, col_net)
        px, py = pad_pos[col_net]
        track([(top_x, cy), (px, cy), (px, py)], pcbnew.B_Cu, col_net)

    # ---- tie the two Teensy GND pins together (front, right of the sockets) ----
    (gx1, gy1), (gx2, gy2) = sorted(gnd_pads, key=lambda p: p[1])
    track([(gx1, gy1), (gx1, gy1 + 7.0), (gx2, gy1 + 9.5), (gx2, gy2)], pcbnew.F_Cu, "GND")

    # ---- mounting holes, outline, labels ----
    for i, (x, y) in enumerate(G.mounting_holes(), start=1):
        h = load(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_2.2mm_M2")
        h.SetReference("H%d" % i)
        h.Reference().SetVisible(False)
        h.SetPosition(mm(x, y))
        board.Add(h)

    w, hgt = G.PCB_W, G.PCB_H
    corners = [(0, 0), (w, 0), (w, hgt), (0, hgt), (0, 0)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(mm(x1, y1))
        seg.SetEnd(mm(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)

    text("eTuttino v0.1", 30, 12, 2.0)
    text("beatconfused.com/etutti", 30, 16.5, 1.2)
    text("Teensy 4.0 + Audio Board Rev D", G.STACK_CX - 2, G.STACK_CY + 11.5, 1.0)
    text("USB >", G.PCB_W - 9, G.STACK_CY, 1.2)
    # Orientation marks for plugging the Teensy stack in the right way round.
    j1_gnd = [p for p in pins if p[0] == "J1" and p[1] == 1][0]
    j2_vin = [p for p in pins if p[0] == "J2" and p[1] == 1][0]
    text("GND", j1_gnd[3], j1_gnd[4] - 2.4, 0.8)
    text("VIN", j2_vin[3], j2_vin[4] + 2.4, 0.8)
    text("0", j1_gnd[3] - 2.54, j1_gnd[4] - 2.4, 0.8)
    text("23", j2_vin[3] - 7.62, j2_vin[4] + 2.4, 0.8)
    text("eTuttino v0.1 - C-griff G3-G5", 40, 8, 1.5, pcbnew.B_SilkS)

    os.makedirs(KICAD_DIR, exist_ok=True)
    pcbnew.SaveBoard(BOARD_PATH, board)
    print("saved", BOARD_PATH)


def cli(*args):
    print("kicad-cli", " ".join(args[:3]), "...")
    subprocess.run([KICAD_CLI, *args], check=True, stdout=subprocess.DEVNULL)


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

    # Optional: files for having the fab solder the diodes and sockets
    # (bottom-side SMT assembly). Not needed for a bare-PCB order.
    cpl_path = os.path.join(FAB_DIR, "etuttino_cpl_bottom.csv")
    cli("pcb", "export", "pos", "--side", "back", "--format", "csv", "--units", "mm",
        "--smd-only", "--output", cpl_path, BOARD_PATH)
    # The socket footprint belongs to the front (it is the switch), so KiCad
    # leaves it out of the back-side list: append the sockets ourselves,
    # centred between their two pads, in KiCad's CSV convention (Y up).
    with open(cpl_path, "a", encoding="utf-8", newline="") as f:
        for k in G.keys():
            f.write('"%s","CPG151101S11","Kailh_MX_Hotswap",%.6f,%.6f,0.000000,bottom' % (
                k["ref"], k["cx"] - 0.6215, -(k["cy"] - 3.81)) + chr(10))
    with open(os.path.join(FAB_DIR, "etuttino_bom.csv"), "w", encoding="utf-8", newline="") as f:
        refs_sw = ",".join(k["ref"] for k in G.keys())
        refs_d = ",".join(k["diode"] for k in G.keys())
        f.write("Comment,Designator,Footprint,Quantity\n")
        f.write('"Kailh MX hot-swap socket CPG151101S11","%s",Kailh_MX_Hotswap_1u,%d\n' % (refs_sw, len(G.keys())))
        f.write('"1N4148W","%s",SOD-123,%d\n' % (refs_d, len(G.keys())))

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
    """Reads the saved board back and checks, for every key, that the
    Teensy pins its row and column nets reach are the ones the firmware
    scans for that key's position, in both C-griff and B-griff. DRC only
    proves the copper matches the nets; this proves the nets match the
    firmware."""
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

    row_pins = ints(r"ROW_PINS\[MATRIX_ROWS\] = \{([^}]*)\}")
    col_pins = ints(r"COL_PINS\[MATRIX_COLS\] = \{([^}]*)\}")
    first_col = ints(r"FIRST_COL\[MATRIX_ROWS\] = \{([^}]*)\}")
    first = ints(r"FIRST_NOTE\[2\]\[MATRIX_ROWS\] = \{(.*?)\};")
    first_note = [first[0:4], first[4:8]]
    # This board is laid out in C-griff (generate.ROWS); B-griff is the
    # same switches with the firmware's second note table.
    b_first = [first_note[1][r] for r in range(4)]
    bad = 0
    for k in G.keys():
        sw = b.FindFootprintByReference(k["ref"])
        d = b.FindFootprintByReference(k["diode"])
        col_net = [p.GetNetname() for p in sw.Pads() if p.GetNumber() == "1"][0]
        row_net = [p.GetNetname() for p in d.Pads() if p.GetNumber() == "1"][0]
        r = row_pins.index(int(pin_of_net[row_net]))
        c = col_pins.index(int(pin_of_net[col_net]))
        fw_c = first_note[0][r] + 3 * (c - first_col[r])
        if c < first_col[r] or fw_c != k["note"] or (r, c) != (k["row"], k["col"]):
            bad += 1
            print("  MISMATCH", k["ref"], "board", k["note"], "firmware", fw_c)
        fw_b = b_first[r] + 3 * (c - first_col[r])
        assert 0 <= fw_b < 128
    print("firmware check: %d/%d keys reach the pins the firmware expects" % (len(G.keys()) - bad, len(G.keys())))
    return bad


PLATE_PATH = os.path.join(KICAD_DIR, "etuttino_plate.kicad_pcb")


def build_plate():
    """The switch plate as a copper-less FR4 'PCB': outline + 14 mm cutouts +
    M2 holes, in the same coordinates as the main board so everything lines
    up. Order it from the same fab (1.6 mm FR4 is the usual MX plate)."""
    global board
    main_board = board
    board = pcbnew.BOARD()
    ox = G.GRID_X0 - G.PLATE_MARGIN
    oy = G.GRID_Y0 - G.PLATE_MARGIN
    pw = 9 * G.U + 2 * G.PLATE_MARGIN
    ph = 4 * G.U + 2 * G.PLATE_MARGIN

    def rect(x0, y0, x1, y1):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            seg = pcbnew.PCB_SHAPE(board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetStart(mm(ax, ay))
            seg.SetEnd(mm(bx, by))
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetWidth(pcbnew.FromMM(0.1))
            board.Add(seg)

    rect(ox, oy, ox + pw, oy + ph)
    half = G.CUTOUT / 2
    for k in G.keys():
        rect(k["cx"] - half, k["cy"] - half, k["cx"] + half, k["cy"] + half)
    for i, (x, y) in enumerate(G.mounting_holes(), start=1):
        if oy <= y <= oy + ph:
            h = load(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_2.2mm_M2")
            h.SetReference("H%d" % i)
            h.Reference().SetVisible(False)
            h.SetPosition(mm(x, y))
            board.Add(h)
    text("eTuttino plate v0.1", ox + pw / 2, oy + ph - 2.6, 1.2)
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


if __name__ == "__main__":
    build()
    errs, unc = fab()
    mismatches = verify_against_firmware()
    build_plate()
    sys.exit(1 if errs or unc or mismatches else 0)
