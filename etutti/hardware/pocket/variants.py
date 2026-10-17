"""eTuttino Pocket -- SPEC v2, task D1: the new left side and the interface.

Kept as the record of the D1 study. J picked variant B (SPEC v3); the case
is case/case.py now and the review page is written by case/revisao.py
(this script rewrites the old D1 page only with --d1-page).

Stdlib only:  python etutti/hardware/pocket/variants.py

For each left-side variant in shape.VARIANTS it lays out the interface
(SPEC v2 section 4, back to front: engraved logo, knobs + LED, speaker
grille on the 13 deg slope) and packs what goes under it, checking
plan clearances and heights against the case:

  - the largest round speaker under the grille, with a closed back box;
  - the 1000 mAh LiPo on the bottom plate, NOT under the main board (so
    the keyboard keeps the eTuttino's height);
  - the Teensy 4.0 + Audio Board stack on a tongue of the main board,
    its USB plug towards the left face;
  - the controls board (switched volume pot, encoder, LED) under the lid;
  - the panel USB and headphone jack on the left face.

Writes etutti/hardware/pocket/build/variants.json, the drawings in
etutti/hardware/pocket/case/renders/ and the review page
etutti/pocket/revisao/index.html. layout.py calls study() for the
recommended variant and writes its numbers into pocket.json.

Every size marked CHECK is an estimate: the electronics agent picks the
real parts (ELETRONICA.md); change the numbers here when it does.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shape as S  # noqa: E402

BUILD = os.path.join(HERE, "build")
RENDERS = os.path.join(HERE, "case", "renders")
REVIEW = os.path.normpath(os.path.join(HERE, "..", "..", "pocket", "revisao", "index.html"))

RECOMMENDED = "B"

# ---------------------------------------------------------------- parts (CHECK)
# Speakers: diameter, depth (frame to the back of the magnet), magnet diameter.
# Generic micro speakers, mylar or paper cone, 4-8 ohm, 1-3 W (CHECK the chosen part).
SPEAKERS = [(50.0, 9.0, 20.0), (45.0, 8.0, 18.0), (40.0, 6.0, 16.0), (36.0, 5.5, 15.0),
            (30.0, 5.0, 12.0), (28.0, 5.0, 12.0), (23.0, 4.5, 10.0), (20.0, 4.0, 9.0)]
SPK_CLR_WALL = 3.0         # speaker rim -> outer face (Seixo wall 2.5 + 0.5)
SPK_CLR_RAMP = 3.0         # speaker rim -> ramp top edge (the lid's inside turns down 2.5 before it)
SPK_Y_MIN = 57.0           # speaker rim stays on the 13 deg slope (crease at 55, R 10)
SPK_Y_MAX = S.WIDTH - S.WALL - 0.5
BOX_WALL, BOX_FLOOR = 1.5, 1.2     # printed back box round the speaker

# LiPo 1S 1000 mAh "603450": 6.0 x 34 x 50 (max, PCM included) -- CHECK the chosen cell.
BATT = {"t": 6.0, "w": 34.0, "l": 50.0}
BATT_SWELL = 0.5           # room to swell
BATT_CLR = 0.5             # all round in the cradle
BATT_LEADS = 3.0           # wires out of the PCM end
BATT_W = BATT["w"] + 2 * BATT_CLR                   # 35
BATT_L = BATT["l"] + 2 * BATT_CLR + BATT_LEADS      # 54
BATT_Z = (S.FLOOR_T, S.FLOOR_T + BATT["t"] + BATT_SWELL + BATT_CLR)   # 2.0 .. 9.0
BATT_CLR_WALL = 3.5        # cradle ribs on the bottom plate: wall 2.5 + rib 1.0
BOARD_GROW = -3.0          # main board's left edge = opening - 3, 19.5 from the key centres (CHECK with the electronics)
BOARD_CLR = 1.0            # battery cradle -> main board edge

# Teensy 4.0 + Audio Board Rev D, the eTuttino's stack (case/fit_check.py).
AUDIO_L, AUDIO_W = 38.0, 36.8
PAST_USB, PAST_VIN = 3.6, 8.76
AUDIO_LIFT, BOARD_T, USB_ON_TEENSY = 3.0, 1.6, 2.6
STACK_H = 13.0             # under the Audio Board to the top of the Teensy's USB
USB_PLUG = (11.0, 11.0, 7.5)       # 90 deg micro-B plug: along, across, height -- CHECK
Z_AB = S.Z_PCB_TOP + AUDIO_LIFT    # 10.7, Audio Board bottom
Z_AB_TOP = Z_AB + BOARD_T          # 12.3
Z_TEENSY = Z_AB_TOP + STACK_H - 2 * BOARD_T - USB_ON_TEENSY     # 19.5, Teensy bottom
Z_USB_TOP = Z_TEENSY + BOARD_T + USB_ON_TEENSY                   # 23.7
Z_PLUG_C = Z_TEENSY + BOARD_T + 1.3
Z_AB_JACK = Z_AB + 6.7             # the Audio Board's own jack socket top: 17.4

# Interface (SPEC v2 section 4): knobs and LED in a row, volume left.
KNOB_D, LED_D = 9.0, 3.5           # knob caps and LED hole (eTuttino SPEC)
KNOB_PITCH, LED_PITCH = 16.0, 12.0  # volume -> selector, selector -> LED (Pocket v1)
EDGE_MIN = 5.0                     # knobs / LED -> edges of the interface area (SPEC v2)
GRILLE_RAMP_MIN = 6.0              # grille -> ramp (SPEC v2)
KNOB_Y_PREF = 49.0                 # as far forward as the flat part allows (eTuttino: 45): the stack behind needs the room
# switched 9 mm pot: body (plan) and height above its board. The eTuttino's
# RK09K is 6.5 tall; a 9 mm pot with a rotary on/off switch at the start of
# its travel (e.g. Alps RK09D with switch / generic WH9011A-type) has the switch
# deck behind the resistive deck -- reserved 13.0 (CHECK the chosen part).
POT_SW = (10.0, 12.5, 13.0)
ENC = (12.4, 13.2, 6.5)            # Alps EC11E (eTuttino)
CTRL_T, CTRL_LEGS = 1.6, 1.5
CTRL_DEPTH = 14.0                  # controls board, front to back (pot body 12.5 + 1.25 each side)
LID_GAP = 0.2                      # pot body top under the lid
# panel USB receptacle and jack behind the left face (eTuttino fit_check)
USB_PANEL = (10.0, 10.0, 8.0)      # depth, width, height -- CHECK
JACK_PANEL = (10.0, 8.0)           # depth, diameter -- CHECK
PANEL_Z = 22.5                     # centre height: above the controls board (17.3) and the AB jack (17.4)
HOLE_D, HOLE_PITCH = 1.9, 3.6      # grille holes, hex pitch on the slope


# ---------------------------------------------------------------- helpers
def ceiling_need(z, y):
    """How far outside the opening a part reaching up to z must stay, at y.
    Deck/chamfer: lid underside 12.8 out to opening + 6.5; the ramp's inside
    rises from there to the interface's underside at opening + 15.2."""
    zc = S.z_interface(y, S.TOP_T)
    if z <= S.Z_PLATE_BOT - 0.3:
        return 0.0
    if z <= S.Z_PLATE_TOP - 0.3:
        return S.PLATE_OVERLAP + 0.5
    if z > zc - 0.2:
        return float("inf")
    foot, top = S.RAMP_FOOT_OFF + S.WALL, S.RAMP_TOP_OFF + S.WALL
    return foot + (z + 0.2 - S.Z_PLATE_TOP) / (zc - S.Z_PLATE_TOP) * (top - foot)


class Geo:
    """Everything one variant's checks need, precomputed."""

    def __init__(self, key):
        self.key = key
        self.v = S.VARIANTS[key]
        self.origin, self.keys, self.outline = S.place(self.v)
        self.length = max(x for x, _ in self.outline)
        self.open = S.ccw(S.opening(self.keys))
        self.ramp = S.ccw(S.ramp_top(self.keys))
        self.chamfer = S.ccw(S.opening(self.keys, 4.0))
        self.inner = S.ccw(S.erode(self.outline, S.WALL))
        self.board_keys = S.ccw(S.opening(self.keys, BOARD_GROW))
        self.x2 = min(k["x"] for k in self.keys if k["row"] == 2)

    def d_open(self, poly):
        return S.poly_gap(poly, self.open)

    def d_open_pt(self, p):
        return -S.depth(self.open, p)

    def fits_height(self, poly, z):
        """poly reaching up to z sits under the lid everywhere."""
        need = ceiling_need(z, max(y for _, y in poly))
        if need == float("inf"):
            return False
        if need <= 0:
            return True
        return self.d_open(poly) >= need

    def in_case(self, poly, clr):
        return all(S.depth(self.outline, p) >= clr for p in poly)


def area_gap(poly, region):
    return S.poly_gap(poly, region)


# ---------------------------------------------------------------- 1. knobs
def place_knobs(g):
    """Volume, selector, LED in a row: the row's y as near the eTuttino's 45
    as the flat part allows, x centred between the two edge margins."""
    best = None
    for yi in range(0, 21):
        for sgn in ((1,) if yi == 0 else (1, -1)):
            y = KNOB_Y_PREF + sgn * yi * 0.5
            if y + KNOB_D / 2 > S.IF_CREASE_Y - 1.5 or y < 25:
                continue
            # left margin: the volume knob to the outline; right: the LED to the ramp edge
            lo, hi = None, None
            x = 0.0
            while x < g.x2:
                items = [(x, KNOB_D / 2), (x + KNOB_PITCH, KNOB_D / 2), (x + KNOB_PITCH + LED_PITCH, LED_D / 2)]
                ml = min(S.depth(g.outline, (cx, y)) - r for cx, r in items)
                mr = min(-S.depth(g.ramp, (cx, y)) - r for cx, r in items)
                if min(ml, mr) >= EDGE_MIN:
                    lo = x if lo is None else lo
                    hi = x
                x += 0.25
            if lo is None:
                continue
            x = (lo + hi) / 2
            items = [(x, KNOB_D / 2), (x + KNOB_PITCH, KNOB_D / 2), (x + KNOB_PITCH + LED_PITCH, LED_D / 2)]
            ml = min(S.depth(g.outline, (cx, y)) - r for cx, r in items)
            mr = min(-S.depth(g.ramp, (cx, y)) - r for cx, r in items)
            best = {"y": y, "volume": (x, y), "select": (x + KNOB_PITCH, y), "led": (x + KNOB_PITCH + LED_PITCH, y),
                    "margin_left": ml, "margin_ramp": mr, "slack": hi - lo}
            break
        if best:
            break
    if not best:
        return None
    vx, y = best["volume"]
    lx = best["led"][0]
    lid = S.z_interface(y + POT_SW[1] / 2, S.TOP_T)          # the lid's underside at the pot body's front
    top = lid - LID_GAP - POT_SW[2]                           # controls board top
    bx0, bx1 = vx - POT_SW[0] / 2 - 1.5, lx + 3.5
    best["board"] = S.rect((bx0 + bx1) / 2, y, bx1 - bx0, CTRL_DEPTH)
    best["pot"] = S.rect(vx, y, POT_SW[0], POT_SW[1])
    best["encoder"] = S.rect(vx + KNOB_PITCH, y, ENC[0], ENC[1])
    best["z_board"] = (top - CTRL_T - CTRL_LEGS, top)         # legs + board
    best["z_pot"] = (top, top + POT_SW[2])
    best["z_enc"] = (top, top + ENC[2])
    best["ok_height"] = g.fits_height(best["pot"], top + POT_SW[2]) and g.in_case(best["board"], S.WALL + 0.5)
    return best


# ---------------------------------------------------------------- 2. speaker
def place_speaker(g, knobs):
    """Largest circle under the 13 deg slope: rim >= 3 from the outer face
    and the ramp's top edge, back rim past the crease and its back box
    clear of the controls board."""
    y_min = max(SPK_Y_MIN, max(y for _, y in knobs["board"]) + 0.6 + BOX_WALL)
    best = (-1, None)
    y = y_min
    while y <= SPK_Y_MAX:
        x = 0.0
        while x < g.x2:
            p = (x, y)
            r = min(S.depth(g.outline, p) - SPK_CLR_WALL,
                    -S.depth(g.ramp, p) - SPK_CLR_RAMP,
                    y - y_min, SPK_Y_MAX - y)
            if r > best[0]:
                best = (r, p)
            x += 0.5
        y += 0.5
    r_max, c = best
    # refine round the best point
    step = 0.25
    for _ in range(3):
        cx, cy = c
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                p = (cx + dx * step, cy + dy * step)
                r = min(S.depth(g.outline, p) - SPK_CLR_WALL, -S.depth(g.ramp, p) - SPK_CLR_RAMP,
                        p[1] - y_min, SPK_Y_MAX - p[1])
                if r > r_max:
                    r_max, c = r, p
        step /= 2
    d_fit = 2 * r_max
    d, h, mag = next(s for s in SPEAKERS if s[0] <= d_fit + 1e-6)
    face_c = S.z_interface(c[1], S.TOP_T) - 0.3                # face against the lid, tilted 13 deg
    return {"centre": c, "d_max": d_fit, "d": d, "depth": h, "magnet": mag,
            "z_face": face_c, "z_back": face_c - h * S.COS_IF,
            "circle": S.circle_poly(c[0], c[1], d / 2 + 0.3),
            "box": S.circle_poly(c[0], c[1], d / 2 + BOX_WALL)}


# ---------------------------------------------------------------- 3. stack
def stack_parts(cx, cy, ang):
    """The stack's plan pieces in the case frame. Local frame: u along the
    Audio Board's 38 mm side from its USB end, v across from the VIN side."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    to = lambda u, v: (cx + u * c - v * s, cy + u * s + v * c)
    R = lambda u0, v0, u1, v1: [to(u0, v0), to(u1, v0), to(u1, v1), to(u0, v1)]
    tcx = PAST_USB + 6.5 * 2.54                 # Teensy centre along u
    tcy = PAST_VIN + 7.62                       # ...and across
    jy = tcy + 7.62 + 7.2
    px, py, _ = USB_PLUG
    u_usb = tcx - 18.8
    return {
        "audio": (R(0, 0, AUDIO_L, AUDIO_W), (Z_AB, Z_AB_TOP)),
        "ab_jack": (R(0, jy - 3, 13, jy + 3), (Z_AB_TOP, Z_AB_JACK)),
        "teensy": (R(u_usb, tcy - 8.89, tcx + 17.78, tcy + 8.89), (Z_AB_TOP, Z_USB_TOP)),
        "plug": (R(u_usb - px, tcy - py / 2, u_usb, tcy + py / 2), (Z_PLUG_C - USB_PLUG[2] / 2, Z_PLUG_C + USB_PLUG[2] / 2)),
        "plug_end": to(u_usb - px, tcy),
    }


def _stack_ok(g, parts, names, blockers):
    if not g.in_case(parts["audio"][0], S.WALL + 0.5):
        return False
    for name in names:
        poly, (z0, z1) = parts[name]
        if not g.fits_height(poly, z1):
            return False
        for bpoly, bz in blockers:
            if z1 > bz and S.poly_gap(poly, bpoly) < 0.5:
                return False
    return True


def stack_candidates(g, knobs, spk):
    """Every stack placement that fits (1 mm, 15 deg grid), best first: the
    90 deg plug's end nearest the left wall (short cable), then furthest back."""
    blockers = [(knobs["board"], knobs["z_board"][0]), (spk["box"], 0.0)]
    out = []
    for ang in range(0, 360, 15):
        for yi in range(0, 81, 1):
            for xi in range(0, int(g.x2) - 30, 1):
                parts = stack_parts(float(xi), float(yi), ang)
                if not g.in_case(parts["plug"][0], S.WALL + 0.5):
                    continue
                if _stack_ok(g, parts, ("audio", "ab_jack", "teensy", "plug"), blockers):
                    wall = S.depth(g.outline, parts["plug_end"]) - S.WALL
                    out.append(((round(wall), yi, xi), {"x": xi, "y": yi, "angle": ang, "parts": parts, "plug_to_wall": wall}))
    out.sort(key=lambda t: t[0])
    return [c for _, c in out]


def main_board(g, st):
    """Main board: the keys' area (opening + 1) and a tongue under the stack."""
    ab = st["parts"]["audio"][0]
    ys = [y for _, y in ab]
    lo, hi = min(ys) - 2, max(ys) + 2
    near = [p for p in g.board_keys if lo <= p[1] <= hi]
    tongue = S.ccw(S.hull(S.offset(ab, 1.0, 24) + near))
    return [g.board_keys, tongue]


# ---------------------------------------------------------------- 4. battery
def place_battery(g, boards, step=1, around=None):
    """The battery cradle on the bottom plate, clear of the main board: the
    placement with the most room to the walls and the board."""
    inner = S.ccw(S.erode(g.outline, BATT_CLR_WALL))
    grown = [S.ccw(S.offset(b, BOARD_CLR, 24)) for b in boards]
    best = None
    if around:
        (cx, cy), a0 = around
        angs = [a0 - 15, a0 - 7.5, a0, a0 + 7.5, a0 + 15]
        ys = [cy + d * 0.5 for d in range(-8, 9)]
        xs = [cx + d * 0.5 for d in range(-8, 9)]
    else:
        angs = list(range(0, 180, 15))
        ys = list(range(0, 101, step))
        xs = list(range(0, int(g.x2) + 10, step))
    for ang in angs:
        for yi in ys:
            for xi in xs:
                r = S.rect(float(xi), float(yi), BATT_L, BATT_W, ang)
                if not all(S.inside(inner, p) for p in r):
                    continue
                if any(S.poly_gap(r, b) <= 0 for b in grown):
                    continue
                m = min(min(S.depth(g.outline, p) for p in r) - BATT_CLR_WALL,
                        min(S.poly_gap(r, b) for b in boards) - BOARD_CLR)
                if best is None or m > best[0]:
                    best = (m, xi, yi, ang, r)
    if not best:
        return None
    m, xi, yi, ang, r = best
    return {"centre": (xi, yi), "angle": ang, "rect": r, "margin": m}


# ---------------------------------------------------------------- 5. panel parts
def place_panel(g, st, knobs, spk):
    """The panel USB receptacle and the headphone jack behind the left face,
    each along the wall's normal: USB at the free spot nearest the plug's
    end (short cable), the jack at the next free spot >= 13 mm away."""
    pe = st["parts"]["plug_end"]
    wall = S.resample(g.outline, 1.0)
    n = len(wall)
    z = (PANEL_Z - USB_PANEL[2] / 2, PANEL_Z + USB_PANEL[2] / 2)
    # what reaches above z[0]: the knob bodies, the speaker's box, the Teensy, the plug
    others = [(nm, poly) for nm, poly, z1 in (
        ("plaquinha", knobs["board"], knobs["z_board"][1]), ("potenciômetro", knobs["pot"], knobs["z_pot"][1]),
        ("encoder", knobs["encoder"], knobs["z_enc"][1]), ("caixa do alto-falante", spk["box"], 99.0),
        ("Teensy", st["parts"]["teensy"][0], Z_USB_TOP), ("jack da Audio Board", st["parts"]["ab_jack"][0], Z_AB_JACK),
        ("plugue USB", st["parts"]["plug"][0], 99.0)) if z1 > z[0]]

    def at(i):
        a, b = wall[(i - 2) % n], wall[(i + 2) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty)
        nx, ny = ty / L, -tx / L
        if S.inside(g.outline, (wall[i][0] + nx, wall[i][1] + ny)):
            nx, ny = -nx, -ny
        return wall[i], (nx, ny)

    def part(i, depth, width):
        p, (nx, ny) = at(i)
        t = S.WALL + 1.5                       # behind the wall and the part's flange / nut
        cx, cy = p[0] - nx * (t + depth / 2), p[1] - ny * (t + depth / 2)
        return S.rect(cx, cy, depth, width, math.degrees(math.atan2(ny, nx))), p, (nx, ny)

    def free(poly, extra=()):
        if not g.fits_height(poly, z[1]) or not g.in_case(poly, S.WALL + 0.3):
            return False
        return all(S.poly_gap(poly, o) >= 0.5 for _, o in others) and all(S.poly_gap(poly, o) >= 1.0 for o in extra)

    # only the left faces: the outward normal points left (nx < -0.25)
    order = sorted((i for i in range(n) if at(i)[1][0] < -0.25),
                   key=lambda i: math.hypot(wall[i][0] - pe[0], wall[i][1] - pe[1]))
    usb = None
    for i in order:
        cand = part(i, USB_PANEL[0], USB_PANEL[1])
        if free(cand[0]):
            usb = cand
            break
    jack = None
    if usb:
        extra = (usb[0],)
        for i in order:
            if math.hypot(wall[i][0] - usb[1][0], wall[i][1] - usb[1][1]) < 13.0:
                continue
            cand = part(i, JACK_PANEL[0], JACK_PANEL[1])
            if free(cand[0], extra):
                jack = cand
                break
    clash = [] if usb and jack else ["conectores do painel sem lugar na face esquerda"]
    cable = math.hypot(usb[1][0] - pe[0], usb[1][1] - pe[1]) if usb else None
    return {"usb": usb[0] if usb else [], "usb_at": usb[1] if usb else None, "usb_n": usb[2] if usb else None,
            "jack": jack[0] if jack else [], "jack_at": jack[1] if jack else None, "jack_n": jack[2] if jack else None,
            "z": z, "clash": clash, "cable": cable}


# ---------------------------------------------------------------- 6. grille, logo
def region_poly(g, centre, ok, r_max=80.0, n=120):
    """Star-shaped region round centre where ok(p) holds, as a polygon."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        lo, hi = 0.0, r_max
        for _ in range(30):
            mid = (lo + hi) / 2
            if ok((centre[0] + mid * math.cos(a), centre[1] + mid * math.sin(a))):
                lo = mid
            else:
                hi = mid
        pts.append((centre[0] + lo * math.cos(a), centre[1] + lo * math.sin(a)))
    return pts


def grille(g, spk):
    c = spk["centre"]
    r_in = spk["d"] / 2 - 1.5                  # holes only over the cone, inside the gasket
    ok = lambda p: (math.hypot(p[0] - c[0], p[1] - c[1]) <= r_in and S.depth(g.outline, p) >= EDGE_MIN
                    and -S.depth(g.ramp, p) >= GRILLE_RAMP_MIN and p[1] >= SPK_Y_MIN + 1.0)
    poly = region_poly(g, c, ok, r_in + 1)
    holes = []
    py = HOLE_PITCH * S.COS30 * S.COS_IF
    j = 0
    y = c[1] - r_in
    while y <= c[1] + r_in:
        x = c[0] - r_in + (HOLE_PITCH / 2 if j % 2 else 0.0)
        while x <= c[0] + r_in:
            if S.inside(poly, (x, y)) and S.edge_dist(poly, (x, y)) >= HOLE_D / 2 + 0.6:
                holes.append((round(x, 2), round(y, 2)))
            x += HOLE_PITCH
        y += py
        j += 1
    return poly, holes


def logo_zone(g, knobs):
    y_lim = knobs["y"] - KNOB_D / 2 - 4.0
    ok = lambda p: (p[1] <= y_lim and p[1] >= S.WALL + 4.0 and S.depth(g.outline, p) >= EDGE_MIN
                    and -S.depth(g.ramp, p) >= EDGE_MIN)
    # centre: middle of the band at mid-height of the zone
    yc = (y_lim + 6.5) / 2
    xs = [x / 4 for x in range(0, int(g.x2 * 4)) if ok((x / 4, yc))]
    c = ((min(xs) + max(xs)) / 2, yc)
    return region_poly(g, c, ok, 80.0, 160), c


# ---------------------------------------------------------------- study
def study(key):
    g = Geo(key)
    kn = place_knobs(g)
    assert kn, f"{key}: knobs don't fit"
    spk = place_speaker(g, kn)
    cands = stack_candidates(g, kn, spk)
    assert cands, f"{key}: stack doesn't fit"
    # the first stack placement that leaves the panel parts room on the left
    # face and the battery a place off the main board
    st = bat = pan = None
    seen = set()
    tried = 0
    for c in cands:
        sig = (round(c["angle"]), round(c["x"]) // 3, round(c["y"]) // 3)
        if sig in seen:
            continue
        seen.add(sig)
        p = place_panel(g, c, kn, spk)
        if p["clash"]:
            continue
        tried += 1
        if tried > 60:
            break
        boards = main_board(g, c)
        b = place_battery(g, boards, step=1)
        if not b:
            continue
        st, bat, pan = c, place_battery(g, boards, around=(b["centre"], b["angle"])), p
        break
    if st is None:                      # report the best stack with what fails
        st = cands[0]
        boards = main_board(g, st)
        bat = place_battery(g, boards, step=1)
        pan = place_panel(g, st, kn, spk)
    boards = main_board(g, st)
    gr, holes = grille(g, spk)
    logo, logo_c = logo_zone(g, kn)
    # back box: floor on the battery if it is under the speaker, else on its own floor
    over_batt = bat is not None and S.poly_gap(spk["box"], bat["rect"]) <= 0
    z_floor = (BATT_Z[1] if over_batt else S.FLOOR_T + 0.3) + BOX_FLOOR
    r = spk["d"] / 2
    h_air = spk["z_back"] - z_floor
    v_back = math.pi * r * r * h_air / 1000.0                 # cm3, behind the magnet only (conservative)
    # checks
    checks = []
    for a, b, za, zb, what in ((spk["box"], kn["board"], (z_floor, 40), kn["z_board"], "caixa do alto-falante x controles"),):
        if S.poly_gap(a, b) < 0.5 and za[1] > zb[0]:
            checks.append(what)
    if bat:
        for b in boards:
            if S.poly_gap(bat["rect"], b) < BOARD_CLR:
                checks.append("bateria sob a placa")
    else:
        checks.append("bateria: sem lugar fora da placa principal")
    checks += pan["clash"]
    if not kn["ok_height"]:
        checks.append("potenciômetro ou plaquinha não cabem sob a tampa")
    if min(kn["margin_left"], kn["margin_ramp"]) < EDGE_MIN - 1e-6:
        checks.append("knobs/LED a menos de 5 mm das bordas")
    # clearances, for the report
    g_ramp = min(-S.depth(g.ramp, q) for q in gr)
    g_wall = min(S.depth(g.outline, q) for q in gr)
    if g_ramp < GRILLE_RAMP_MIN - 0.05:
        checks.append("grade a menos de 6 mm da rampa")
    c = spk["centre"]
    spk_wall = S.depth(g.outline, c) - spk["d"] / 2
    spk_ramp = -S.depth(g.ramp, c) - spk["d"] / 2
    under = S.poly_gap(st["parts"]["audio"][0], kn["board"]) <= 0
    clear = {"grille_ramp": g_ramp, "grille_wall": g_wall, "speaker_wall": spk_wall, "speaker_ramp": spk_ramp,
             "speaker_ctrl": S.poly_gap(spk["box"], kn["board"]),
             "ab_under_ctrl": (kn["z_board"][0] - Z_AB_TOP) if under else None,
             "teensy_ramp": g.d_open(st["parts"]["teensy"][0]) - ceiling_need(Z_USB_TOP, max(y for _, y in st["parts"]["teensy"][0])),
             "pot_lid": LID_GAP}
    ett_keys, ett = S.etuttino_outline()
    shift = g.x2 - min(k["x"] for k in ett_keys if k["row"] == 2)
    ett = [(x + shift, y) for x, y in ett]
    return {"key": key, "geo": g, "knobs": kn, "speaker": spk, "stack": st, "boards": boards, "battery": bat,
            "panel": pan, "grille": gr, "holes": holes, "logo": logo, "logo_c": logo_c,
            "box_floor": z_floor, "box_over_battery": over_batt, "air_h": h_air, "v_back": v_back,
            "checks": checks, "etuttino": ett, "etuttino_shift": shift, "clear": clear}


def summary(r):
    g = r["geo"]
    kn, spk, st, bat, pan = r["knobs"], r["speaker"], r["stack"], r["battery"], r["panel"]
    R = lambda v, d=1: None if v is None else round(v, d)
    return {
        "variant": r["key"], "name": g.v["name"], "params": {k: g.v[k] for k in ("band", "nose", "corner", "bulge")},
        "length": R(g.length), "origin": g.origin, "shorter_than_etuttino": R(331.0 - g.length),
        "knob_y": kn["y"], "volume": [R(v) for v in kn["volume"]], "select": [R(v) for v in kn["select"]],
        "led": [R(v) for v in kn["led"]],
        "knob_margin_left": R(kn["margin_left"]), "knob_margin_ramp": R(kn["margin_ramp"]),
        "speaker_d_max": R(spk["d_max"]), "speaker_d": spk["d"], "speaker_depth": spk["depth"],
        "speaker_centre": [R(v) for v in spk["centre"]], "back_volume_cm3": R(r["v_back"]),
        "back_box_floor": R(r["box_floor"]), "back_box_over_battery": r["box_over_battery"], "air_h": R(r["air_h"]),
        "battery": None if not bat else {"centre": [R(v) for v in bat["centre"]], "angle": bat["angle"], "margin": R(bat["margin"])},
        "stack": {"origin": [st["x"], st["y"]], "angle": st["angle"], "plug_to_wall": R(st["plug_to_wall"])},
        "pot": {"z": [R(v) for v in kn["z_pot"]], "reserved_h": POT_SW[2], "board_z": [R(v) for v in kn["z_board"]]},
        "panel_cable": R(pan["cable"]),
        "holes": len(r["holes"]),
        "clear": {k: R(v) for k, v in r["clear"].items()},
        "checks": r["checks"],
    }


# ---------------------------------------------------------------- drawings
SVG_STYLE = """
.pv-ett{fill:none;stroke:#9c9384;stroke-width:.6;stroke-dasharray:2.4 1.6}
.pv-body{fill:#e9e1d3;stroke:#4a443c;stroke-width:.7;stroke-linejoin:round}
.pv-ramp{fill:#ddd3c2}
.pv-chamfer{fill:#c9bfae}
.pv-well{fill:#2a2520}
.pv-key{fill:#fbfaf6;stroke:#55504a;stroke-width:.3}
.pv-key.pv-sharp{fill:#1d1b19;stroke:#8a8377}
.pv-note{font:600 3.6px Inter,'Segoe UI',sans-serif;text-anchor:middle;fill:#3b3631}
.pv-note.pv-sharp{fill:#e6e0d6}
.pv-knob{fill:#3b3631}
.pv-led{fill:#5fb85f}
.pv-grille{fill:#d6ccbb;stroke:#a39886;stroke-width:.4}
.pv-hole{fill:#6f665a}
.pv-logo{font:700 6px 'Cormorant Garamond',Georgia,serif;text-anchor:middle;fill:#9a8f7e}
.pv-logo2{font:600 2.8px Inter,'Segoe UI',sans-serif;letter-spacing:.8px;text-anchor:middle;fill:#9a8f7e}
.pv-logozone{fill:none;stroke:#b8ad9b;stroke-width:.35;stroke-dasharray:1 1}
.pv-dim{stroke:#4a443c;stroke-width:.35;fill:none}
.pv-dimt{font:600 4.2px Inter,'Segoe UI',sans-serif;text-anchor:middle;fill:#4a443c}
.pv-lab{font:500 3.4px Inter,'Segoe UI',sans-serif;fill:#3b3631}
.pv-labw{font:600 3.4px Inter,'Segoe UI',sans-serif;fill:#fff}
.pv-inner{fill:none;stroke:#8a8377;stroke-width:.35;stroke-dasharray:1.2 .8}
.pv-rampline{fill:none;stroke:#8a8377;stroke-width:.35}
.pv-board{fill:#cfe3c8;stroke:#4f7d45;stroke-width:.4}
.pv-batt{fill:rgba(214,140,60,.55);stroke:#a3561e;stroke-width:.5}
.pv-ab{fill:rgba(30,90,55,.75);stroke:#14532d;stroke-width:.4}
.pv-teensy{fill:rgba(60,170,110,.85);stroke:#1d6b3a;stroke-width:.4}
.pv-plug{fill:rgba(70,70,70,.8)}
.pv-spk{fill:rgba(128,96,64,.35);stroke:#806040;stroke-width:.5}
.pv-box{fill:none;stroke:#806040;stroke-width:.4;stroke-dasharray:1.2 .8}
.pv-ctrl{fill:rgba(120,80,160,.35);stroke:#6b4a92;stroke-width:.4}
.pv-pot{fill:rgba(120,80,160,.7);stroke:#4b2f6e;stroke-width:.3}
.pv-panel{fill:#8d8d8d;stroke:#555;stroke-width:.3}
"""


def _f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _pts(poly, dx, dy):
    return " ".join(f"{_f(x + dx)},{_f(y + dy)}" for x, y in poly)


def svg_top(r, frame, title=None):
    """The variant from above, to scale, the eTuttino's outline behind it
    (keyboards superimposed). frame = (x0, x1) shared by all variants."""
    g = r["geo"]
    x0, x1 = frame
    dx, dy = -x0, 4.0
    W, H = x1 - x0, S.WIDTH + 16.0
    s = [f'<svg class="pv-svg" viewBox="0 0 {_f(W)} {_f(H)}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="{title or "Planta"}"><style>{SVG_STYLE}</style>']
    s.append(f'<polygon class="pv-ett" points="{_pts(r["etuttino"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-body" points="{_pts(g.outline, dx, dy)}"/>')
    s.append(f'<clipPath id="clip-{r["key"]}"><polygon points="{_pts(g.outline, dx, dy)}"/></clipPath>')
    s.append(f'<polygon class="pv-ramp" clip-path="url(#clip-{r["key"]})" points="{_pts(g.ramp, dx, dy)}"/>')
    s.append(f'<polygon class="pv-chamfer" points="{_pts(g.chamfer, dx, dy)}"/>')
    s.append(f'<polygon class="pv-well" points="{_pts(g.open, dx, dy)}"/>')
    s += _interface(r, dx, dy)
    for k in g.keys:
        sh = " pv-sharp" if k["sharp"] else ""
        s.append(f'<circle class="pv-key{sh}" cx="{_f(k["x"] + dx)}" cy="{_f(k["y"] + dy)}" r="{_f(S.D_BTN / 2)}"/>')
        s.append(f'<text class="pv-note{sh}" x="{_f(k["x"] + dx)}" y="{_f(k["y"] + dy + 1.25)}">{k["note"].replace("#", "♯")}</text>')
    # overall length
    yd = S.WIDTH + dy + 6.0
    s.append(f'<path class="pv-dim" d="M{_f(dx)} {_f(yd - 2.5)}V{_f(yd + 1.5)}M{_f(g.length + dx)} {_f(yd - 2.5)}V{_f(yd + 1.5)}'
             f'M{_f(dx)} {_f(yd)}H{_f(g.length + dx)}"/>')
    s.append(f'<text class="pv-dimt" x="{_f(g.length / 2 + dx)}" y="{_f(yd + 5.2)}">{g.length:.0f} mm</text>')
    ex = max(x for x, _ in r["etuttino"])
    s.append(f'<text class="pv-lab" x="{_f(ex + dx - 2)}" y="{_f(dy - 1.2)}" text-anchor="end" fill="#8a8377">eTuttino ({ex - min(x for x, _ in r["etuttino"]):.0f} mm)</text>')
    s.append("</svg>")
    return "\n".join(s)


def _interface(r, dx, dy):
    g, kn = r["geo"], r["knobs"]
    s = []
    s.append(f'<polygon class="pv-logozone" points="{_pts(r["logo"], dx, dy)}"/>')
    lx, ly = r["logo_c"]
    s.append(f'<text class="pv-logo" x="{_f(lx + dx)}" y="{_f(ly + dy)}">eTuttino</text>')
    s.append(f'<text class="pv-logo2" x="{_f(lx + dx)}" y="{_f(ly + dy + 4.2)}">POCKET</text>')
    s.append(f'<polygon class="pv-grille" points="{_pts(r["grille"], dx, dy)}"/>')
    for x, y in r["holes"]:
        s.append(f'<circle class="pv-hole" cx="{_f(x + dx)}" cy="{_f(y + dy)}" r="{_f(HOLE_D / 2)}"/>')
    for name in ("volume", "select"):
        x, y = kn[name]
        s.append(f'<circle class="pv-knob" cx="{_f(x + dx)}" cy="{_f(y + dy)}" r="{_f(KNOB_D / 2)}"/>')
    x, y = kn["led"]
    s.append(f'<circle class="pv-led" cx="{_f(x + dx)}" cy="{_f(y + dy)}" r="{_f(LED_D / 2)}"/>')
    return s


def svg_inside(r, frame, title=None):
    """The left end with the lid off: what sits under the interface."""
    g, kn, spk, st, bat, pan = r["geo"], r["knobs"], r["speaker"], r["stack"], r["battery"], r["panel"]
    x0, x1 = frame
    dx, dy = -x0, 4.0
    W, H = x1 - x0, S.WIDTH + 8.0
    s = [f'<svg class="pv-svg" viewBox="0 0 {_f(W)} {_f(H)}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="{title or "Por dentro"}"><style>{SVG_STYLE}</style>']
    s.append(f'<clipPath id="cut-{r["key"]}"><rect x="0" y="0" width="{_f(W)}" height="{_f(H)}"/></clipPath>')
    s.append(f'<g clip-path="url(#cut-{r["key"]})">')
    s.append(f'<polygon class="pv-body" points="{_pts(g.outline, dx, dy)}"/>')
    for b in r["boards"]:
        s.append(f'<polygon class="pv-board" points="{_pts(b, dx, dy)}"/>')
    s.append(f'<polygon class="pv-inner" points="{_pts(g.inner, dx, dy)}"/>')
    s.append(f'<polygon class="pv-rampline" points="{_pts(g.ramp, dx, dy)}"/>')
    s.append(f'<polygon class="pv-well" style="opacity:.25" points="{_pts(g.open, dx, dy)}"/>')
    for k in g.keys:
        s.append(f'<circle class="pv-key" style="opacity:.5" cx="{_f(k["x"] + dx)}" cy="{_f(k["y"] + dy)}" r="{_f(S.D_BTN / 2)}"/>')
    if bat:
        s.append(f'<polygon class="pv-batt" points="{_pts(bat["rect"], dx, dy)}"/>')
    p = st["parts"]
    s.append(f'<polygon class="pv-ab" points="{_pts(p["audio"][0], dx, dy)}"/>')
    s.append(f'<polygon class="pv-teensy" points="{_pts(p["teensy"][0], dx, dy)}"/>')
    s.append(f'<polygon class="pv-plug" points="{_pts(p["ab_jack"][0], dx, dy)}"/>')
    s.append(f'<polygon class="pv-plug" points="{_pts(p["plug"][0], dx, dy)}"/>')
    s.append(f'<polygon class="pv-box" points="{_pts(spk["box"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-spk" points="{_pts(spk["circle"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-ctrl" points="{_pts(kn["board"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-pot" points="{_pts(kn["pot"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-pot" points="{_pts(kn["encoder"], dx, dy)}"/>')
    x, y = kn["led"]
    s.append(f'<circle class="pv-led" cx="{_f(x + dx)}" cy="{_f(y + dy)}" r="1.5"/>')
    s.append(f'<polygon class="pv-panel" points="{_pts(pan["usb"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-panel" points="{_pts(pan["jack"], dx, dy)}"/>')
    # labels
    def lab(x, y, text, cls="pv-lab", anchor="middle"):
        s.append(f'<text class="{cls}" x="{_f(x + dx)}" y="{_f(y + dy)}" text-anchor="{anchor}">{text}</text>')
    cx, cy = spk["centre"]
    lab(cx, cy + 1.2, f"alto-falante Ø{spk['d']:.0f}")
    if bat:
        bx, by = bat["centre"]
        bxr = max(q[0] for q in bat["rect"]) - 2.0
        lab(bxr, max(q[1] for q in bat["rect"]) - 3.0, "bateria", anchor="end")
    tc = [sum(q[0] for q in p["teensy"][0]) / 4, sum(q[1] for q in p["teensy"][0]) / 4]
    lab(tc[0], tc[1] + 1.2, "Teensy", "pv-labw")
    ac = [sum(q[0] for q in p["audio"][0]) / 4, sum(q[1] for q in p["audio"][0]) / 4]
    s.append("</g></svg>")
    return "\n".join(s)


def svg_compare(results, frame):
    """The three outlines on top of each other, keyboards superimposed."""
    x0, x1 = frame
    dx, dy = -x0, 4.0
    W, H = x1 - x0, S.WIDTH + 8.0
    g0 = results[0]["geo"]
    s = [f'<svg class="pv-svg" viewBox="0 0 {_f(W)} {_f(H)}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-label="As três variantes sobrepostas"><style>{SVG_STYLE}'
         '.pv-o{fill:none;stroke-width:.8}.pv-oA{stroke:#8c3b2f}.pv-oB{stroke:#2f6b4f}.pv-oC{stroke:#3d5a99;stroke-dasharray:3 1.5}'
         '.pv-ot{font:700 4.4px Inter,"Segoe UI",sans-serif}</style>']
    s.append(f'<polygon class="pv-ett" points="{_pts(results[0]["etuttino"], dx, dy)}"/>')
    s.append(f'<polygon class="pv-ramp" style="opacity:.6" points="{_pts(g0.ramp, dx, dy)}"/>')
    s.append(f'<polygon class="pv-well" points="{_pts(g0.open, dx, dy)}"/>')
    for k in g0.keys:
        sh = " pv-sharp" if k["sharp"] else ""
        s.append(f'<circle class="pv-key{sh}" cx="{_f(k["x"] + dx)}" cy="{_f(k["y"] + dy)}" r="{_f(S.D_BTN / 2)}"/>')
    cols = {"A": "#8c3b2f", "B": "#2f6b4f", "C": "#3d5a99"}
    for i, r in enumerate(results):
        sh = g0.x2 - r["geo"].x2                       # align the keyboards on the first variant's
        poly = [(x + sh, y) for x, y in r["geo"].outline]
        s.append(f'<polygon class="pv-o pv-o{r["key"]}" points="{_pts(poly, dx, dy)}"/>')
        xl = min(x for x, _ in poly)
        s.append(f'<text class="pv-ot" fill="{cols[r["key"]]}" x="{_f(xl + dx + 2)}" y="{_f(dy + 12 + 6 * i)}">{r["key"]}</text>')
    s.append("</svg>")
    return "\n".join(s)


def _n(v, d=0):
    """Portuguese number: comma decimals."""
    return f"{v:.{d}f}".replace(".", ",")


def review_page(results, rec):
    """etutti/pocket/revisao/index.html: Portuguese only, noindex."""
    by = {r["key"]: r for r in results}
    sm = {r["key"]: summary(r) for r in results}
    top_frame = (min(min(x for x, _ in r["etuttino"]) for r in results) - 3,
                 max(max(x for x, _ in r["etuttino"]) for r in results) + 3)
    in_frame = (-3.0, max(r["geo"].x2 for r in results) + 14.0)
    cmp_frame = (-3.0 + min(0.0, min(results[0]["geo"].x2 - r["geo"].x2 for r in results)),
                 results[0]["geo"].length + 3)

    def batt_txt(r):
        b = r["battery"]
        if not b:
            return "não coube fora da placa"
        return f"no fundo, sob {'o alto-falante e os knobs' if b['centre'][1] > 60 else 'os knobs'}, fora da placa principal"

    cards = []
    for r in results:
        k, g, s_ = r["key"], r["geo"], sm[r["key"]]
        spk = r["speaker"]
        rec_tag = ' <span class="family-tag">recomendada</span>' if k == rec else ""
        nose = "concêntrica com a rampa" if g.v["nose"] is None else f"R {_n(g.v['nose'])}"
        cards.append(f"""
    <section class="rv-card" id="variante-{k.lower()}">
      <h2>Variante {k} · {g.v['name']}{rec_tag}</h2>
      <p class="rv-tagline">{g.v['tagline']}.</p>
      <figure class="rv-fig">
        {svg_top(r, top_frame, f"Variante {k} vista de cima")}
        <figcaption>Vista de cima, em escala. Tracejado: o eTuttino, com os teclados sobrepostos.</figcaption>
      </figure>
      <figure class="rv-fig">
        {svg_inside(r, in_frame, f"Variante {k} por dentro")}
        <figcaption>Por dentro, sem a tampa (lado esquerdo, escala maior): placa principal em verde claro,
        bateria em laranja, Audio Board e Teensy em verde, plaquinha dos knobs em roxo, alto-falante e a
        caixa dele em marrom, USB e fone de painel em cinza.</figcaption>
      </figure>
      <ul class="rv-facts">
        <li><strong>{_n(g.length, 1)} mm</strong> de comprimento ({_n(331.0 - g.length, 1)} mm menor que o eTuttino) × 100 mm</li>
        <li>Faixa da interface: {_n(g.v['band'])} mm da borda da rampa até a parede; ponta {nose}; quinas R {_n(g.v['corner'])}{'; faces curvas, flecha de ' + _n(g.v['bulge']) + ' mm' if g.v['bulge'] else ''}</li>
        <li>Alto-falante: cabe Ø {_n(spk['d_max'], 1)}; reservado <strong>Ø {_n(spk['d'])}</strong> × {_n(spk['depth'], 1)} mm com caixa fechada de <strong>{_n(r['v_back'], 1)} cm³</strong></li>
        <li>Knobs a {_n(s_['knob_margin_left'], 1)} mm da parede e o LED a {_n(s_['knob_margin_ramp'], 1)} mm da rampa (mínimo 5)</li>
        <li>Bateria 1000 mAh: {batt_txt(r)}</li>
      </ul>
    </section>""")

    rows = [
        ("Comprimento", lambda r, s_: f"{_n(r['geo'].length, 1)} mm"),
        ("Menor que o eTuttino em", lambda r, s_: f"{_n(331.0 - r['geo'].length, 1)} mm"),
        ("Faixa da interface", lambda r, s_: f"{_n(r['geo'].v['band'])} mm"),
        ("Ponta do \"<\"", lambda r, s_: "concêntrica (R " + _n(S.R_RAMP + r['geo'].v['band']) + ")" if r['geo'].v['nose'] is None else "R " + _n(r['geo'].v['nose'])),
        ("Quinas", lambda r, s_: "R " + _n(r['geo'].v['corner'])),
        ("Maior alto-falante redondo", lambda r, s_: "Ø " + _n(r['speaker']['d_max'], 1)),
        ("Alto-falante reservado", lambda r, s_: f"Ø {_n(r['speaker']['d'])} × {_n(r['speaker']['depth'], 1)}"),
        ("Volume traseiro fechado", lambda r, s_: f"{_n(r['v_back'], 1)} cm³"),
        ("Furos da grade (Ø 1,9)", lambda r, s_: str(len(r['holes']))),
        ("Knob → parede / LED → rampa", lambda r, s_: f"{_n(s_['knob_margin_left'], 1)} / {_n(s_['knob_margin_ramp'], 1)} mm"),
        ("Grade → rampa", lambda r, s_: f"{_n(r['clear']['grille_ramp'], 1)} mm"),
        ("Bateria fora da placa", lambda r, s_: "sim" if r['battery'] else "não"),
        ("Altura do teclado", lambda r, s_: "igual ao eTuttino"),
    ]
    head = "".join(f'<th scope="col">{k}{" ★" if k == rec else ""}</th>' for k in by)
    body = "".join("<tr><th scope=\"row\">" + lab + "</th>" + "".join(f"<td>{fn(by[k], sm[k])}</td>" for k in by) + "</tr>"
                   for lab, fn in rows)
    r0 = by[rec]
    kn0 = r0["knobs"]
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BeatConfused | eTuttino Pocket · revisão D1</title>
  <meta name="description" content="eTuttino Pocket: três variantes do lado esquerdo e da área de interface para escolher (SPEC v2, D1)." />
  <!-- Review page for J (SPEC v2, task D1). Portuguese only, unlisted:
       not on the home page, not in the sitemap. Written by
       etutti/hardware/pocket/variants.py -- edit that script, not this file. -->
  <meta name="robots" content="noindex,nofollow" />
  <meta name="theme-color" content="#10131d" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  />
  <link rel="stylesheet" href="/shared/tuner-common.css?v=20260913" />
  <link rel="stylesheet" href="../../family.css?v=20261017" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <style>
    .rv-wrap {{ max-width: 52rem; width: 100%; margin: 0 auto; display: grid; gap: 1.2rem; min-width: 0; }}
    .rv-card, .rv-box {{ padding: 1rem; border: 1px solid var(--border); border-radius: 0.9rem;
      background: var(--surface-solid); box-shadow: var(--shadow-soft); min-width: 0; }}
    .rv-card h2, .rv-box h2 {{ margin: 0 0 0.3rem; font-family: "Cormorant Garamond", Georgia, serif; font-size: 1.55rem; line-height: 1.15; }}
    .rv-tagline {{ margin: 0 0 0.6rem; color: var(--ink-soft); }}
    .rv-fig {{ margin: 0.6rem 0 0; }}
    .rv-fig figcaption {{ margin-top: 0.3rem; color: var(--ink-soft); font-size: 0.82rem; }}
    .pv-svg {{ display: block; width: 100%; height: auto; }}
    .rv-facts {{ margin: 0.7rem 0 0; padding-left: 1.1rem; display: grid; gap: 0.25rem; font-size: 0.92rem; }}
    .rv-table-wrap {{ overflow-x: auto; }}
    .rv-table {{ width: 100%; border-collapse: collapse; font-size: 0.86rem; }}
    .rv-table th, .rv-table td {{ padding: 0.35rem 0.4rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
    .rv-table thead th {{ font-weight: 700; }}
    .rv-table tbody th {{ font-weight: 600; color: var(--ink-soft); }}
    .rv-box p, .rv-box li {{ font-size: 0.94rem; }}
    .rv-box ul {{ padding-left: 1.1rem; }}
    .rv-legend {{ display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.85rem; margin: 0.4rem 0 0; padding: 0; list-style: none; }}
    .rv-legend span {{ display: inline-block; width: 1.4rem; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.3rem; }}
    @media (max-width: 560px) {{ .rv-card, .rv-box {{ padding: 0.7rem; }} .rv-table {{ font-size: 0.78rem; }} }}
  </style>
</head>
<body>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
    <header class="hero">
      <p class="eyebrow">eTuttino Pocket · revisão</p>
      <h1>O novo lado esquerdo</h1>
      <p class="family-lead">Três formas para o lado esquerdo e a área de interface (SPEC v2, tarefa D1). Todas seguem o "&lt;" do
      teclado a distância constante, com raios generosos, e levam, de trás para a frente, o logo gravado, os knobs com o LED e a grade
      do alto-falante. Escolha uma; a recomendação está no fim.</p>
      <p><span class="family-tag">Provisório · para escolher</span></p>
    </header>

    <div class="rv-wrap">
    <section class="rv-box">
      <h2>As três sobrepostas</h2>
      {svg_compare(results, cmp_frame)}
      <ul class="rv-legend">
        <li><span style="border-color:#8c3b2f"></span>A · {by['A']['geo'].v['name']}</li>
        <li><span style="border-color:#2f6b4f"></span>B · {by['B']['geo'].v['name']}</li>
        <li><span style="border-color:#3d5a99;border-top-style:dashed"></span>C · {by['C']['geo'].v['name']}</li>
        <li><span style="border-color:#9c9384;border-top-style:dashed"></span>eTuttino</li>
      </ul>
    </section>
{''.join(cards)}

    <section class="rv-box">
      <h2>Comparação</h2>
      <div class="rv-table-wrap">
        <table class="rv-table">
          <thead><tr><th></th>{head}</tr></thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </section>

    <section class="rv-box">
      <h2>O que é igual nas três</h2>
      <ul>
        <li>O teclado é o do eTuttino: as mesmas teclas, a mesma abertura e <strong>a mesma altura</strong> (tampa a 17,4 mm, topo das teclas a 26,6 mm).
        A bateria fica no fundo, ao lado da placa principal e não embaixo dela; sai tirando o fundo, sem abrir a tampa.</li>
        <li>A interface tem a altura e a inclinação do eTuttino: plana a 33 mm até y = 55, depois desce a 13° para quem toca. Os knobs ficam
        na parte plana (Ø 9, a {_n(KNOB_PITCH)} mm um do outro, LED {_n(LED_PITCH)} mm à direita), a grade fica na parte inclinada.</li>
        <li>O potenciômetro de volume tem chave (liga/desliga no começo do curso). Reservei {_n(POT_SW[2])} mm de corpo acima da plaquinha
        (o RK09K do eTuttino tem 6,5): a plaquinha desce para {_n(kn0['z_board'][1], 1)} mm e passa por cima da Audio Board.</li>
        <li>A pilha Teensy + Audio Board fica atrás, sob o logo, numa língua da placa principal; o USB sai num plugue de 90° e um cabo curto
        até o USB de painel na face esquerda, com o fone ao lado, como no eTuttino.</li>
        <li>Medidas a conferir quando a eletrônica escolher as peças: bateria 603450 (6 × 34 × 50), alto-falante, potenciômetro com chave.</li>
      </ul>
    </section>

    <section class="rv-box">
      <h2>Recomendação: {rec} · {by[rec]['geo'].v['name']}</h2>
      <p>{RECOMMENDATION_TEXT}</p>
    </section>
    </div>

    <p class="family-back"><a href="../">← eTuttino Pocket</a></p>

    <footer class="footer">
      <p class="footer-links"><a href="https://beatconfused.com">beatconfused.com</a></p>
    </footer>
  </main>
</body>
</html>
"""
    return html


RECOMMENDATION_TEXT = (
    "É a mais curta das três e a que mais tem a cara do nome do case: o lado esquerdo vira uma curva só, "
    "concêntrica com a ponta da rampa, então a faixa da interface tem a mesma largura em todo o contorno e "
    "logo, knobs e grade ficam alinhados a ela sem sobras. Não há quina: a curva da ponta encontra as faces "
    "de trás e da frente com raios grandes. O preço é que o USB e o fone saem numa parede curva, e o case "
    "precisa de um ressalto plano por dentro para o conector de painel (fica para o D2)."
)


def render_png(svg, path, width=1400):
    """PNG of an SVG with headless Edge (Windows); skipped quietly elsewhere."""
    import subprocess
    import tempfile
    edge = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if not os.path.exists(edge):
        return False
    vb = [float(v) for v in svg.split('viewBox="')[1].split('"')[0].split()]
    h = int(width * vb[3] / vb[2]) + 2
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "p.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(f"<html><body style='margin:0;background:#fff'><div style='width:{width}px'>{svg}</div></body></html>")
        for _ in range(3):
            subprocess.run([edge, "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={path}",
                            f"--window-size={width},{h}", "file:///" + page.replace(os.sep, "/")],
                           capture_output=True, timeout=90)
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                return True
    return False


def main():
    keys = [a for a in sys.argv[1:] if not a.startswith("--")] or list(S.VARIANTS)
    results = []
    for k in keys:
        r = study(k)
        print(json.dumps(summary(r), ensure_ascii=False))
        results.append(r)
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, "variants.json"), "w", encoding="utf-8") as fh:
        json.dump({"spec": "v2", "task": "D1", "recommended": RECOMMENDED,
                   "variants": [summary(r) for r in results]}, fh, indent=1, ensure_ascii=False)
    if len(results) < len(S.VARIANTS):
        return
    os.makedirs(RENDERS, exist_ok=True)
    top_frame = (min(min(x for x, _ in r["etuttino"]) for r in results) - 3,
                 max(max(x for x, _ in r["etuttino"]) for r in results) + 3)
    in_frame = (-3.0, max(r["geo"].x2 for r in results) + 14.0)
    cmp_frame = (-3.0 + min(0.0, min(results[0]["geo"].x2 - r["geo"].x2 for r in results)), results[0]["geo"].length + 3)
    svgs = {"d1_comparacao": svg_compare(results, cmp_frame)}
    for r in results:
        svgs[f"d1_{r['key']}_cima"] = svg_top(r, top_frame)
        svgs[f"d1_{r['key']}_dentro"] = svg_inside(r, in_frame)
    for name, svg in svgs.items():
        with open(os.path.join(RENDERS, name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        ok = render_png(svg, os.path.join(RENDERS, name + ".png"))
        print(f"  {name}: svg{' + png' if ok else ''}")
    if "--d1-page" in sys.argv:      # the review page is the D2 one now (case/revisao.py)
        os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
        with open(REVIEW, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(review_page(results, RECOMMENDED))
        print(f"wrote {os.path.relpath(REVIEW, HERE)}")


if __name__ == "__main__":
    main()
