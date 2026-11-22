"""eTutti Student V4 (R4V4): the real layout of the instrument seen from above, in plain Python (no CadQuery).

One source for the model (case_r4.py), the official plan (planta_v4.py) and the section (corte_v4.py).
Frame: x right, y_spec towards the player (row 1 in front), z = 0 at the main board's top = the top of row 1's ruler.

Contents
  * the main board, its parts and holes (pcb/posicao_v4.json, from the electronics);
  * the interface: battery 503450, speaker Dayton CE28MB-8, acoustic box, OLED and its window/slit, knobs, PROG button,
    the sockets in the left wall, the lid's posts on H1..H4;
  * the rulers' connectors (R4V4 task 3): header + plug + cable of every ruler, the M2 positions per row, the tray notches.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

POS = json.load(open(os.path.join(HERE, "..", "pcb", "posicao_v4.json"), encoding="utf-8"))
P = POS["pecas"]

# ---------------------------------------------------------------- levels (z = 0 at the board's top)
Z_BOT, Z_FLOOR = -10.1, -8.1
T_PCB = 1.2
Z_BOARD_BOTTOM = -T_PCB
ROOF_TOP, ROOF_T = 14.6, 2.0                # SPEC R4V4: deck 2.5 + gap 1.0 + housing 11.10 -> the interface roof is level with row 1's deck
CEILING = ROOF_TOP - ROOF_T                 # 12.6
CASE = (252.0, 100.0)
WALL = 2.0
CASE_R = 6.0                                # plan corner radius of the case (outside); V3 had 9.0, which cuts the board and the USB-C (FIT_CHECK R4V4 section 2)
X_IF = 79.0

# ---------------------------------------------------------------- the main board
BOARD_OUT = POS["contorno"]                 # x0, y0, x1, y1 = 2.45, 2.45, 77.5, 97.55
BOARD_R = 3.0
HOLES = {k: (P[k]["x"], P[k]["y"]) for k in ("H1", "H2", "H3", "H4", "H101")}
SLIT = POS["metricas"]["fenda_do_cabo"]     # the OLED cable's slot through the board
CARD = (22.0, 7.0, 44.0, 29.0)              # MicroMod card in plan (22 x 22: the electronics' "cartao" zone starts at the M.2 connector)
CARD_BELOW = 4.7                            # module depth under the board's bottom (measured on the V01 model, student_v01/model3d)

# ---------------------------------------------------------------- the interface
BATTERY_CELL = (34.0, 50.0, 5.0)            # 503450 seen from above: x 34 (the wires' end), y 50, thickness 5 (nominal; cradle adds 0.5 mm all round)
BATTERY_XY = (17.4, 40.0)                   # x0, y0 of the cell (long side along y; the wires leave the end at y 40, towards J202)
SPEAKER = G.SPEAKER                         # (37.0, 73.1)
SPK_D, SPK_H = 28.0, 4.5                    # Dayton CE28MB-8
KNOBS = G.KNOBS                             # shaft centres (28; 44.5), (46; 44.5): the C pad of the encoder + 7.5
PROG = (52.0, 36.0)                         # SW403, pressed from below through a 3 mm hole in the tray
USB_Y, OUT_Y, IN_Y = P["J201"]["y"], P["J301"]["y"], P["J302"]["y"]     # 10, 36, 60 (geometria.py still has the V3's USB_Y = 16)
# the lid's posts on the board's mounting holes (H1..H4): D 6 with an M2 insert, screw from below through the tray's boss
LID_POSTS = [HOLES["H1"], HOLES["H2"], HOLES["H3"], HOLES["H4"]]
H101 = HOLES["H101"]

# ---------------------------------------------------------------- the keyboard (SPEC R4V4 item 2)
PITCH, ROWP = G.PITCH, G.ROW_PITCH
# R5V4: 32 keys, rulers always full. (row, y, first key x, keys): rows 1 and 3 start at ruler x 89.2, rows 2 and 4 at 79.95
# (row 4 is one button to the left, aligned with row 2; its notes are one semitone below row 2's in each column)
ROWS = [(1, 74.03, 98.45, 8), (2, 58.01, 89.2, 8), (3, 41.99, 98.45, 8), (4, 25.97, 89.2, 8)]
FIRST_MIDI = {1: 57, 2: 55, 3: 56, 4: 54}      # A3, G3, G#3, F#3; each column +3 semitones along a row (a minor third), as the SPEC's figure
CASE_LEN = 244.0                               # R6V4: +4 mm of flat deck after the last button (R5V4 had 240: ruler end 237.0 + 1.0 clearance + 2.0 wall; now inner face 242.0)
ZR = [0.0, 2.0, 4.0, 7.0]
RULER_L, RULER_W, RULER_T = 4 * PITCH, 14.0, 1.2
RAIL_IN, RAIL_OUT = 4.2, 7.0
M2_BOSS_D, M2_PILOT, M2_HEAD = 6.0, 3.2, 3.8
PEG_DX, PEG_D, PEG_BELOW = 5.08, 1.7, 1.5      # 2 pegs at +-5.08 from the key centre, 1.5 mm below the ruler's underside

# ---------------------------------------------------------------- the ruler's connectors (task 3)
# SH side-entry header SM06B-SRSS-TB (clone XYECONN C56123098), taken from the board's footprint J601: 9.9 wide, 6.65 deep (courtyards).
HDR_W, HDR_D, HDR_H = 9.4, 6.15, 4.25         # footprint along the pin row, depth along the mating axis, height from the ruler's underside
HDR_OVER = 0.5                                # the mouth is 0.5 mm past the ruler's back edge
PLUG_W, PLUG_D, PLUG_H = 7.6, 5.0, 3.9        # SHR-06V-S plug (estimate: check JST's drawing)
AXIS_Z = -(RULER_T + 2.1)                     # the mating axis below the ruler's top (header mid-height)
SOCK_W, SOCK_H, SOCK_V = 6.76, 3.4, (-6.9, -1.7)   # R6V4 female 1x5 1.27 (EasyEDA footprint of the H4.3 twin; H3.4 to confirm)
IN_X, OUT_X = 5.9, 68.1                       # centres along the ruler (0 = its start, 74 = its end)
LANE_Y0, LANE_Y1 = -(RULER_W / 2 + HDR_OVER), -1.35   # back lane: y from the row axis (the sensor pocket ends at +-1.1)
CABLE_ROW_MM, CABLE_MAIN_MM = 15.0, 25.0     # plug-to-plug lengths asked for (custom)
CABLE_D = 3.5                                 # the six wires as a flat bundle seen from the side: about 3.5 x 1.2 mm; 3.5 used as a width
NOTCH_PLUG_W = PLUG_W + 0.4                   # the plug's notch in the next row's front rail
NOTCH_HDR_W = HDR_W + 1.0                     # the header's notch in the ruler's own back rail

M2_BY_ROW = {1: (18.5, 55.5), 2: (37.0, 55.5), 3: (18.5, 37.0), 4: (37.0, 55.5)}   # R5V4: row 4 now starts like row 2 (x 79.95), so it takes row 2 positions   # chosen so no M2 boss meets a plug's notch (see conflicts())


def length(mod):
    return CASE_LEN + 74.0 * mod


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(row, idx):
    """Name of key `idx` (0 = nearest the main board) of row `row`: midi 57/55/56/54 + 3 per column (C-griff, SPEC R5V4 figure)."""
    m = FIRST_MIDI[row] + 3 * idx
    return "%s%d" % (NOTE_NAMES[m % 12], m // 12 - 1)


def is_cf(name):
    return name.startswith(("C", "F")) and not name.startswith(("C#", "F#"))


def key_list(mod):
    return [(r, x0 + i * PITCH, y) for r, y, x0, n in ROWS for i in range(n + 4 * mod)]


def rulers(mod):
    out = []
    for r, y, x0, n in ROWS:
        n += 4 * mod
        for k in range(int(math.ceil(n / 4.0))):
            out.append({"row": r, "x0": x0 - PITCH / 2 + k * RULER_L, "y": y, "k": k})
    return out


def m2_points(ru):
    return [(ru["x0"] + dx, ru["y"] + 5.2) for dx in M2_BY_ROW[ru["row"]]]


def post_candidates(mod):
    """The lid's interior posts: centroids of the 'type a' triangles, not on a ruler's junction (x = 0 / 74 of a ruler),
    where the connectors and the M2 notches are."""
    out = []
    for r in range(1, 4):
        _, y1, xa, na = ROWS[r - 1]
        _, y2, xb, nb = ROWS[r]
        na += 4 * mod
        nb += 4 * mod
        for i in range(na - 1):
            xm = xa + (i + 0.5) * PITCH
            j = (xm - xb) / PITCH
            if abs(j - round(j)) < 1e-6 and 0 <= round(j) < nb:
                rel = (xm - (xa - PITCH / 2)) % RULER_L
                if min(rel, RULER_L - rel) > 1.0 and xm > X_IF + 8:
                    out.append((round(xm, 3), round(y1 - ROWP / 3.0, 3)))
    return out


def pick_posts(mod):
    n = {0: 5, 1: 8, 2: 11, 3: 14}[mod]
    c = post_candidates(mod)
    idx = sorted(set(int(round(i * (len(c) - 1) / (n - 1))) for i in range(n)))
    return [c[i] for i in idx]


def post_checks(mod):
    """R5V4: for every interior post, the distance from its round boss (D 5.4) and its 1.4 x 4.0 blade to the nearest key housing
    (15.4 x 15.1 rectangle, 0.4 mm margin of the 1.0 gap not counted) and to the nearest ruler junction (x = 0 / 74 of a ruler)."""
    keys = key_list(mod)
    out = []
    for px, py in pick_posts(mod):
        d_boss = min(_rect_dist(px, py, (x - 7.7, x + 7.7, y - 7.55, y + 7.55)) for _r, x, y in keys) - 2.7
        blade = (px - 0.7, px + 0.7, py - 1.66, py + 2.34)
        d_blade = min(max(0.0, max(blade[0] - (x + 7.7), (x - 7.7) - blade[1], blade[2] - (y + 7.55), (y - 7.55) - blade[3])) for _r, x, y in keys)
        junc = min(min((px - ru["x0"]) % RULER_L, RULER_L - (px - ru["x0"]) % RULER_L) for ru in rulers(mod) if abs(ru["y"] - (py + ROWP / 3.0)) < 0.05)
        out.append({"x": px, "y": py, "boss_ao_corpo_mm": round(d_boss, 2), "lamina_ao_corpo_mm": round(d_blade, 2), "ate_a_juncao_mm": round(junc, 2)})
    return out


def wall_posts(mod):
    """Perimeter bosses of the keyboard area (every <= 80 mm along the long walls, plus the corners). The two interface-side
    bosses of the R3V4 model (7; 12) and (7; 88) are gone: the interface's four posts are the board's H1..H4."""
    L = length(mod)
    xs = [X_IF + 10.0, L - 10.0]
    n = int(math.ceil((xs[1] - xs[0]) / 80.0))
    xs = [xs[0] + (xs[1] - xs[0]) * k / n for k in range(n + 1)]
    return [(x, 7.0) for x in xs] + [(x, CASE[1] - 7.0) for x in xs]


# ---------------------------------------------------------------- R5V4: the recommended link (option D, ELETRONICA.md R5V4)
LINK = "E2"           # R6V4: "E2" = 4 SH cables board -> 1st ruler (J1/IN only) + a bridge with two male 1x5 headers under every junction (juncao_r6.py); "D" = soldered links (R5V4); "A": SH cable everywhere
J2_FITTED = True      # E2: J1/J2 are the two identical female sockets (real part, ELETRONICA R6V4). # R6V4: with fixed connectors between rulers J2 is not needed (SPEC R6V4 item 2); in "D" True meant J2 left on the ruler without a cable
LK_U = (2.1, 71.9)    # centres of the link pads along the ruler (u), ELETRONICA R5V4: 5 pads 1.4 x 0.7 mm, 1.0 mm from each end
LK_PAD = (1.4, 0.7)   # along u, along v
LK_V = (-0.4, 3.6)    # span of the 5 pads across the ruler (v = y - y_row; + towards the player), pitch 1.0
LK_WIRE_DEPTH = 1.4   # wire + solder below the ruler's underside: ~1 mm (ELETRONICA) + 0.4 margin
LK_LEN = 7.0


def solder_links(mod):
    """Junctions of every row: (row, x_j, y) with x_j = the second ruler's start."""
    out = []
    rs = rulers(mod)
    for r, y, x0, n in ROWS:
        row = [q for q in rs if q["row"] == r]
        for a, b in zip(row[:-1], row[1:]):
            out.append((r, b["x0"], y))
    return out


def link_box(xj, y, z0):
    """Envelope of one soldered link: pads + 7 mm wires + solder, under the ruler (absolute z), along the junction x_j."""
    ut = LK_U[1]                                    # pad centre of the left ruler, u = 71.9 of 74 -> 2.1 before the junction
    a = xj - (RULER_L - ut) - LK_PAD[0] / 2
    b = xj + LK_U[0] + LK_PAD[0] / 2
    return (a, b, y + LK_V[0] - LK_PAD[1] / 2, y + LK_V[1] + LK_PAD[1] / 2, z0 - RULER_T - LK_WIRE_DEPTH, z0 - RULER_T)


# ---------------------------------------------------------------- connectors: positions, notches, cables
def conn_boxes(ru):
    """(name, x0, x1, y0, y1, z0, z1) of one ruler's header and plug for IN and OUT, in absolute x and y."""
    x0, y = ru["x0"], ru["y"]
    out = []
    zt = -RULER_T                                   # the ruler's underside (z relative to the ruler's top, absolute z = ZR + this)
    for name, c in (("IN", IN_X), ("OUT", OUT_X)):
        if name == "OUT" and LINK in ("D", "E2") and not J2_FITTED:
            continue
        xa, xb = x0 + c - HDR_W / 2, x0 + c + HDR_W / 2
        if LINK == "E2":     # R6V4: SHOU HAN PM1.27-1x5PLT-H3.4 (C55566451): footprint 6.76 x 5.2 (alternate pads), insulator 3.4, in the back lane v -6.9..-1.7
            out.append((name + "_header", x0 + c - SOCK_W / 2, x0 + c + SOCK_W / 2, y + SOCK_V[0], y + SOCK_V[1], zt - SOCK_H, zt))
            if name == "IN" and ru["k"] == 0:       # the pigtail's male 1x5 (C55213903: 1.0 plastic, 0.6 mm short of the socket's face) soldered to the cable
                out.append(("IN_plug", x0 + c - 3.2, x0 + c + 3.2, y - 5.5, y - 2.1, zt - 5.0, zt - 4.0))
            continue
        out.append((name + "_header", xa, xb, y + LANE_Y0, y + LANE_Y0 + HDR_D, zt - HDR_H, zt))
        if name == "OUT" and LINK in ("D", "E2"):
            continue                                # options D and E2: J2 has no plug
        if LINK == "E2":
            if name == "IN" and ru["k"] == 0:       # the pigtail's male 1x5 (C55213903: 1.0 plastic, 0.6 mm short of the socket's face) soldered to the cable
                out.append(("IN_plug", x0 + c - 3.2, x0 + c + 3.2, y - 5.5, y - 2.1, zt - 5.0, zt - 4.0))
            continue                                # E2: only the row's first ruler has a cable; the others' J1 stays empty
        pa, pb = x0 + c - PLUG_W / 2, x0 + c + PLUG_W / 2
        out.append((name + "_plug", pa, pb, y + LANE_Y0 - PLUG_D, y + LANE_Y0, zt - 0.3 - PLUG_H, zt - 0.3))
    return out


def plug_back_points(ru):
    """(x, y) where the wires leave the IN and OUT plugs (the plugs' back faces)."""
    return {"IN": (ru["x0"] + IN_X, ru["y"] + LANE_Y0 - PLUG_D), "OUT": (ru["x0"] + OUT_X, ru["y"] + LANE_Y0 - PLUG_D)}


def bezier(p0, p1, p2, p3, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def plen(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def cable_between(a, da, b, db, target):
    """A cubic Bezier from a (leaving along da) to b (arriving against db) whose length is `target` mm (handles of equal length)."""
    lo, hi = 0.1, 60.0
    pts = None
    for _ in range(60):
        h = (lo + hi) / 2
        pts = bezier(a, (a[0] + da[0] * h, a[1] + da[1] * h), (b[0] + db[0] * h, b[1] + db[1] * h), b)
        if plen(pts) < target:
            lo = h
        else:
            hi = h
    return pts


def cables(mod):
    """Every cable of the instrument: the main board's J60x -> the row's first ruler (IN), and ruler k (OUT) -> ruler k+1 (IN)."""
    out = []
    rs = rulers(mod)
    mouth = POS["metricas"]["mouth_x_fileiras"]
    for r, y, x0, n in ROWS:
        row = [q for q in rs if q["row"] == r]
        j_back = float(mouth[str(r)]) + PLUG_D                    # J60x plug: mouth + the plug's depth; the wires leave towards +x
        if LINK == "E2":                                          # pigtail: the wires leave the male towards -x, no more bend under the next row
            pin = (row[0]["x0"] + IN_X - 3.2, y - 3.8)
            chord = math.hypot(pin[0] - j_back, pin[1] - y)
            tgt = chord * 1.25 + 4.0
            out.append({"row": r, "de": "J60%d" % r, "para": "R%d.0 IN" % r, "pts": cable_between((j_back, y), (1, 0), pin, (-1, 0), tgt), "alvo_mm": round(tgt, 1)})
            continue
        pin = plug_back_points(row[0])["IN"]
        out.append({"row": r, "de": "J60%d" % r, "para": "R%d.0 IN" % r,
                    "pts": cable_between((j_back, y), (1, 0), pin, (0, -1), CABLE_MAIN_MM), "alvo_mm": CABLE_MAIN_MM})
        for a, b in zip(row[:-1], row[1:]):
            if LINK in ("D", "E2"):
                continue                                # the links are soldered wires (D) or a bridge (E2), not SH cables
            po, pi = plug_back_points(a)["OUT"], plug_back_points(b)["IN"]
            out.append({"row": r, "de": "R%d.%d OUT" % (r, a["k"]), "para": "R%d.%d IN" % (r, b["k"]),
                        "pts": cable_between(po, (0, -1), pi, (0, -1), CABLE_ROW_MM), "alvo_mm": CABLE_ROW_MM})
    return out


def notches(mod):
    """Rectangles (x0, x1, y0, y1, row) cut from the tray's rails: the header's notch in the ruler's own back rail and the plug's
    notch in the next row's front rail (the plug passes under that higher ruler)."""
    out = []
    for ru in rulers(mod):
        x0, y, r = ru["x0"], ru["y"], ru["row"]
        for c in (IN_X, OUT_X):
            if c == OUT_X and LINK in ("D", "E2") and not J2_FITTED:
                continue
            hx0, hx1 = x0 + c - NOTCH_HDR_W / 2, x0 + c + NOTCH_HDR_W / 2
            hx0, hx1 = (x0 if hx0 - x0 < 1.5 else hx0), (x0 + RULER_L if x0 + RULER_L - hx1 < 1.5 else hx1)      # no stub of rail left at a ruler's end
            out.append({"x0": hx0, "x1": hx1, "y0": y - RAIL_OUT - 0.5, "y1": y - RAIL_IN + 0.3,
                        "row": r, "tipo": "cabeçalho (trilho de trás da própria fileira)"})
            if r < 4 and LINK != "E2" and (c == IN_X or LINK == "A"):
                yn = ROWS[r][1]                                  # the next row's (r+1) centre
                out.append({"x0": x0 + c - NOTCH_PLUG_W / 2, "x1": x0 + c + NOTCH_PLUG_W / 2, "y0": yn + RAIL_IN - 0.3, "y1": yn + RAIL_OUT + 0.3,
                            "row": r + 1, "tipo": "plugue (trilho da frente da fileira %d)" % (r + 1)})
    # the main board's cable of row r reaches the first ruler's IN plug: where the next row's ruler starts EARLIER (row 1 -> row 2, 9.25 mm)
    # it has to cross that row's front rail before the plug's notch: one longer notch there
    for c in cables(mod):
        r = c["row"]
        if not c["de"].startswith("J60") or r >= 4 or LINK == "E2":
            continue
        yn = ROWS[r][1]
        band = (yn + RAIL_IN - 0.3, yn + RAIL_OUT + 0.3)
        xs = [p[0] for p in c["pts"] if band[0] - CABLE_D / 2 < p[1] < band[1] + CABLE_D / 2]
        first = [q for q in rulers(mod) if q["row"] == r][0]
        if not xs:
            continue
        for n in out:
            if n["row"] == r + 1 and n["tipo"].startswith("plugue") and abs(n["x0"] + NOTCH_PLUG_W / 2 - (first["x0"] + IN_X)) < 0.01:
                lo, hi = min(xs) - CABLE_D / 2 - 0.3, max(xs) + CABLE_D / 2 + 0.3
                if lo < n["x0"] or hi > n["x1"]:
                    n["x0"], n["x1"] = min(n["x0"], lo), max(n["x1"], hi)
                    n["tipo"] = "plugue + passagem do cabo da placa principal (trilho da frente da fileira %d)" % (r + 1)
    return out


def conflicts(mod):
    """Every plug notch against every M2 boss (circle D6 + 0.4) and every lid post (D5 + 0.8) of the rows concerned."""
    bad = []
    posts = pick_posts(mod)
    for nt in notches(mod):
        for ru in rulers(mod):
            for (mx, my) in m2_points(ru):
                if nt["x0"] - 3.4 < mx < nt["x1"] + 3.4 and nt["y0"] - 3.4 < my < nt["y1"] + 3.4:
                    bad.append(("M2", ru["row"], round(mx, 2), round(my, 2), nt["tipo"]))
        for px, py in posts:
            if nt["x0"] - 3.3 < px < nt["x1"] + 3.3 and nt["y0"] - 3.3 < py < nt["y1"] + 3.3:
                bad.append(("poste", round(px, 2), round(py, 2), nt["tipo"]))
    return bad


def rails_left(mod):
    """Fraction of each rail's length kept after the notches."""
    out = {}
    for ru in rulers(mod):
        key = (ru["row"], ru["k"])
        L = RULER_L - 0.4
        lost_back = 0.0
        lost_front = 0.0
        for nt in notches(mod):
            lo, hi = max(nt["x0"], ru["x0"] + 0.2), min(nt["x1"], ru["x0"] + RULER_L - 0.2)
            if hi <= lo:
                continue
            yc = nt["y0"] + (nt["y1"] - nt["y0"]) / 2
            if abs(yc - (ru["y"] - 5.6)) < 3.0:
                lost_back += hi - lo
            elif abs(yc - (ru["y"] + 5.6)) < 3.0:
                lost_front += hi - lo
        out[key] = {"fundo_%": round(100 * (1 - lost_back / L)), "frente_%": round(100 * (1 - lost_front / L))}
    return out


def _rect_dist(px, py, r):
    dx = max(r[0] - px, 0.0, px - r[1])
    dy = max(r[2] - py, 0.0, py - r[3])
    return math.hypot(dx, dy)


def rail_rects(mod):
    """The tray's rails after the notches, as (x0, x1, y0, y1, row) rectangles (plan)."""
    nts = notches(mod)
    out = []
    for ru in rulers(mod):
        for sgn in (-1, 1):
            ya, yb = sorted((ru["y"] + sgn * RAIL_IN, ru["y"] + sgn * RAIL_OUT))
            xa, xb = ru["x0"] + 0.2, ru["x0"] + RULER_L - 0.2
            cuts = sorted((max(n["x0"], xa), min(n["x1"], xb)) for n in nts
                          if n["y0"] < yb and n["y1"] > ya and n["x0"] < xb and n["x1"] > xa and abs((n["y0"] + n["y1"]) / 2 - (ya + yb) / 2) < 1.0)
            x = xa
            for c0, c1 in cuts:
                if c0 > x:
                    out.append((x, c0, ya, yb, ru["row"]))
                x = max(x, c1)
            if xb > x:
                out.append((x, xb, ya, yb, ru["row"]))
    return out


def cable_clearance(mod):
    """Minimum clearance (mm) from every cable's centre line, less half the bundle, to the tray's rails, the M2 bosses and the
    interior posts (plan view; the cable runs at the plugs' axis, between the floor and the rulers' undersides)."""
    rr = rail_rects(mod)
    bosses = [(mx, my, M2_BOSS_D / 2) for ru in rulers(mod) for mx, my in m2_points(ru)]
    posts = [(px, py, 2.5) for px, py in pick_posts(mod)]
    res = []
    for c in cables(mod):
        worst = {"trilho": 1e9, "M2": 1e9, "poste": 1e9}
        for x, y in c["pts"]:
            for r in rr:
                worst["trilho"] = min(worst["trilho"], _rect_dist(x, y, r[:4]) - CABLE_D / 2)
            for bx, by, br in bosses:
                worst["M2"] = min(worst["M2"], math.hypot(x - bx, y - by) - br - CABLE_D / 2)
            for bx, by, br in posts:
                worst["poste"] = min(worst["poste"], math.hypot(x - bx, y - by) - br - CABLE_D / 2)
        res.append({"cabo": "%s -> %s" % (c["de"], c["para"]), "comprimento_mm": round(plen(c["pts"]), 1),
                    "folga_min_mm": {k: round(v, 2) for k, v in worst.items()},
                    "recuo_maximo_mm": None})
    return res


# ---------------------------------------------------------------- the lid corner and the board (plan, analytic)
def inner_corner_clearance():
    """Distance from the board's / the sockets' corners to the lid's inner wall at the two left corners (positive = clear)."""
    ri = CASE_R - WALL
    out = {}
    cy = {"trás": CASE_R, "frente": CASE[1] - CASE_R}
    x0, y0, x1, y1 = BOARD_OUT
    for name, ycen, yb in (("trás (y=0)", CASE_R, y0), ("frente (y=100)", CASE[1] - CASE_R, y1)):
        # the board's corner arc: centre and radius
        bc = (x0 + BOARD_R, yb + BOARD_R if yb == y0 else yb - BOARD_R)
        d_centres = math.hypot(bc[0] - CASE_R, bc[1] - ycen)
        out["placa x parede interna, canto " + name] = round(ri - (d_centres + BOARD_R), 2)
    # the USB-C receptacle: its corner at (front x, y +- half width): CONN_FRONT_X = 2.3, the body is 9 wide (y 5.5..14.5 at y=10)
    for yy in (USB_Y - 4.5, USB_Y + 4.5):
        if yy < CASE_R:
            xwall = CASE_R - math.sqrt(max(ri ** 2 - (CASE_R - yy) ** 2, 0.0))
        else:
            xwall = WALL
        out["USB-C: face da frente do conector (x 2,3) menos a parede interna, em y=%.1f" % yy] = round(2.3 - xwall, 2)
    return out


def main():
    mod = 0
    print("conflitos:", conflicts(mod))
    print("trilhos que sobram:", rails_left(mod))
    for c in cables(mod):
        print(c["de"], "->", c["para"], "comprimento %.1f" % plen(c["pts"]))
    print(inner_corner_clearance())
    for c in cable_clearance(mod):
        print(c)


if __name__ == "__main__":
    main()
