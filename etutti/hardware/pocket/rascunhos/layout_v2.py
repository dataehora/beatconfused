"""eTuttino Pocket -- key layout, plan outline, interface and power budget (SPEC v2).

Stdlib only:  python etutti/hardware/pocket/layout.py
Writes into etutti/hardware/pocket/build/:
  pocket_keys.csv     one line per key (note, row, xp, x, y, colour)
  pocket_top.svg      plan view to scale, the eTuttino's outline behind it
  pocket.json         every number and polygon the prototype page and later scripts read
and rewrites etutti/hardware/pocket/POWER.md from the budget below.

Same C-griff geometry as the eTuttino (case/case.py, case/SPEC.md): pitch
18.5, rows 16.02 apart, 100 mm deep box. v2 gives the left end a "<" of its
own, parallel to the keyboard's left edge: the interface becomes a chevron
band of constant width between the case's left edge and the ramp. The plan
outline here is a preview; case.py stays the source of the exact case once
it learns the Pocket model.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

# ---- geometry shared with the eTuttino (case/case.py) ----
P = 18.5
D_BTN = 15.0
ROW_PITCH = P * math.cos(math.radians(30))           # 16.02
ROW_Y = {r: 50.0 + (2.5 - r) * ROW_PITCH for r in (1, 2, 3, 4)}
WIDTH = 100.0
CLR_SIDE = 15.0
BOX_OFF = 10.3
R_OPEN = D_BTN / 2 + CLR_SIDE                         # 22.5, concentric with the row-2 end keys
R_CHAMFER = R_OPEN + 4.0                              # 26.5, the chamfer's outer edge
R_BOX = R_OPEN + BOX_OFF                              # 32.8
R_RAMP = R_OPEN + 12.7                                # 35.2, the ramp's top edge
CLR_FB = WIDTH / 2 - BOX_OFF - 1.5 * ROW_PITCH - D_BTN / 2
SIN30, COS30, TAN30 = 0.5, math.cos(math.radians(30)), math.tan(math.radians(30))

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
G3 = 55

# ---- the Pocket ----
TOP = {1: "D#5", 2: "E5", 3: "D5", 4: "C5"}   # highest note per row (J's spec)
O_ETUTTINO = 104.0

# v2: left end. Two 30 deg faces meeting at row 2's height, parallel to the keyboard's "<".
BAND_W = 48.0               # interface band, measured along x between the case's left faces and the ramp's top edge
R_VERTEX = 25.0             # the left nose
R_LEFT_CORNER = 14.0        # where the left faces meet the back and the front
WALL = 2.5                  # Seixo wall
INSET = 7.0                 # interface items keep this from the left face and from the ramp

# Heights (v2): the battery goes under the key board, so the keyboard area rises 6 mm.
Z_DECK = 17.4 + 6.0         # 23.4
Z_KEY_TOP = 26.6 + 6.0      # 32.6
Z_IF = 33.0                 # interface flat part, unchanged
IF_CREASE_Y = 55.0
IF_SLOPE = 13.0

# Interface items, back to front
LOGO_Y = (10.0, 32.0)       # engraving band, a parallelogram following the left faces
KNOB_Y = 45.0
VOLUME_X, SELECT_X, LED_X = 14.0, 30.0, 42.0
KNOB_D, LED_D = 9.0, 3.5
GRILLE_Y = (63.0, 93.0)     # parallelogram on the 13 deg slope
SPEAKER_D = 36.0            # full-range driver under the grille
SPEAKER_Y = 77.0
HOLE_D, HOLE_PITCH = 1.9, 3.6

# Connectors on the back-left face (flat, facing back-left: cables away from the player)
USB_Y, JACK_Y = 33.0, 20.0

# Battery under the key board
BATTERY = (90.0, 60.0, 5.5)     # x, y, z  -- e.g. a 1S pouch "556090" class, ~3000 mAh (CHECK)
STACK = (36.0, 28.0)            # Teensy 4.0 on Audio Board Rev D footprint (CHECK), turned to the back-left face


def midi(name):
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTE_NAMES.index(pitch)


def note_name(m):
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


def keys_for(top, origin):
    """C-griff, n = semitones from G3. Row 4 repeats row 1 half a key right."""
    lim = {r: midi(t) - G3 for r, t in top.items()}
    out = []
    for n in range(0, max(lim.values()) + 1):
        if n % 3 == 2 and n <= lim[1]:
            out.append((n, 1, (n - 2) / 3))
        if n % 3 == 0 and n <= lim[2]:
            out.append((n, 2, n / 3 - 0.5))
        if n % 3 == 1 and n <= lim[3]:
            out.append((n, 3, (n - 1) / 3))
        if n % 3 == 2 and 2 <= n <= lim[4]:
            out.append((n, 4, (n - 2) / 3 + 0.5))
    keys = []
    for n, row, xp in out:
        m = G3 + n
        keys.append({
            "n": n, "midi": m, "note": note_name(m), "row": row, "xp": xp,
            "x": round(origin + xp * P, 2), "y": round(ROW_Y[row], 2),
            "sharp": (m % 12) in (1, 3, 6, 8, 10),
            "cf": (m % 12) in (0, 5),
        })
    return keys


# ---- 2D helpers ----
def hull(points):
    pts = sorted(set(points))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def circles(centres, r, y0, y1, steps=96):
    pts = []
    for cx, cy in centres:
        for i in range(steps):
            a = 2 * math.pi * i / steps
            pts.append((round(cx + r * math.cos(a), 3), round(min(y1, max(y0, cy + r * math.sin(a))), 3)))
    return pts


def fillet(poly, corner, r, steps=24):
    """Replace the vertex `corner` (must be in poly) by an arc of radius r."""
    i = poly.index(corner)
    a, p, c = poly[i - 1], poly[i], poly[(i + 1) % len(poly)]
    u1 = ((a[0] - p[0]), (a[1] - p[1])); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
    u2 = ((c[0] - p[0]), (c[1] - p[1])); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
    half = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))) / 2
    t = r / math.tan(half)
    bis = (u1[0] + u2[0], u1[1] + u2[1]); lb = math.hypot(*bis); bis = (bis[0] / lb, bis[1] / lb)
    cen = (p[0] + bis[0] * r / math.sin(half), p[1] + bis[1] * r / math.sin(half))
    s, e = (p[0] + u1[0] * t, p[1] + u1[1] * t), (p[0] + u2[0] * t, p[1] + u2[1] * t)
    a0, a1 = math.atan2(s[1] - cen[1], s[0] - cen[0]), math.atan2(e[1] - cen[1], e[0] - cen[0])
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    arc = [(round(cen[0] + r * math.cos(a0 + d * k / steps), 3), round(cen[1] + r * math.sin(a0 + d * k / steps), 3)) for k in range(steps + 1)]
    return poly[:i] + arc + poly[i + 1:]


def left_x(poly, y):
    """Smallest x where the horizontal line at y crosses the polygon."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return min(xs)


def point_in(poly, p):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def offset_inward(poly, d):
    """Points of poly moved d inwards (crude: towards the centroid along the normal) -- for checks only."""
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        vx, vy = cx - x, cy - y; l = math.hypot(vx, vy)
        out.append((x + vx / l * d, y + vy / l * d))
    return out


def opening_and_box(keys, left_end):
    """eTuttino rules for the opening/chamfer/ramp; the box's left end comes from left_end()."""
    y_top = ROW_Y[4] - D_BTN / 2 - CLR_FB
    y_bot = ROW_Y[1] + D_BTN / 2 + CLR_FB
    centres = [(k["x"], k["y"]) for k in keys]
    opening = hull(circles(centres, R_OPEN, y_top, y_bot))
    chamfer = hull(circles(centres, R_CHAMFER, y_top - 4, y_bot + 4))
    ramp = hull(circles(centres, R_RAMP, 0.0, WIDTH))
    right = hull(circles(centres, R_BOX, 0.0, WIDTH))
    box = left_end(right)
    return opening, chamfer, ramp, box


def pocket_left_end(x2):
    """The case's left end, v2: '<' parallel to the keyboard's, BAND_W left of the ramp's sharp '<'."""
    y2 = ROW_Y[2]
    ramp_vertex_x = x2 - R_RAMP / COS30      # sharp vertex of the ramp's offset '<'
    vx = ramp_vertex_x - BAND_W
    V = (round(vx, 3), round(y2, 3))
    B = (round(vx + y2 * TAN30, 3), 0.0)
    F = (round(vx + (WIDTH - y2) * TAN30, 3), WIDTH)

    def build(right):
        poly = hull(right + [V, B, F])
        poly = fillet(poly, V, R_VERTEX)
        poly = fillet(poly, B, R_LEFT_CORNER)
        poly = fillet(poly, F, R_LEFT_CORNER)
        return poly
    return build, V


def etuttino_left_end(right):
    return hull(right + [(0.0, 0.0), (0.0, WIDTH)])


def parallelogram(box, ramp, y0, y1, inset, steps=12):
    """Band between the left face (+inset) and the ramp edge (-inset), from y0 to y1."""
    left = [(left_x(box, y0 + (y1 - y0) * k / steps) + inset, y0 + (y1 - y0) * k / steps) for k in range(steps + 1)]
    right = [(left_x(ramp, y1 - (y1 - y0) * k / steps) - inset, y1 - (y1 - y0) * k / steps) for k in range(steps + 1)]
    return [(round(x, 2), round(y, 2)) for x, y in left + right]


# ---- power ----
BUDGET = [   # 3.3 V rail, mA: typical, maximum
    ("Teensy 4.0 a 600 MHz (CHECK: medir)", 100.0, 120.0),
    ("Audio Board (SGTL5000), fone 32 ohm ou saída de linha (CHECK)", 20.0, 40.0),
    ("Sensores Hall DRV5056, {n} x 6 mA (máx. 10 mA, datasheet TI)", None, None),
    ("2 x CD74HC4067", 0.1, 0.2),
    ("LED bicolor (um lado aceso, 330 ohm)", 4.0, 8.0),
    ("Carregador + conversor, quiescente", 0.1, 0.5),
]
V_RAIL, EFF, V_BATT, DERATE = 3.3, 0.90, 3.7, 0.85
SPEAKER_W = (0.30, 0.60)     # average electrical power into the speaker, tocando em volume normal / alto (CHECK)
AMP_EFF = 0.85               # class-D straight from the battery
AMP_Q_MA = 4.0
TARGET_H = 4.0
CAPACITIES = [2000, 2500, 3000]


def power(n_keys):
    rows = []
    for name, typ, mx in BUDGET:
        if typ is None:
            name, typ, mx = name.format(n=n_keys), 6.0 * n_keys, 10.0 * n_keys
        rows.append((name, typ, mx))
    i_typ, i_max = sum(r[1] for r in rows), sum(r[2] for r in rows)
    w = {
        "fone": (i_typ / 1000 * V_RAIL / EFF, i_max / 1000 * V_RAIL / EFF),
    }
    amp_q = AMP_Q_MA / 1000 * V_BATT
    w["alto-falante"] = (w["fone"][0] + SPEAKER_W[0] / AMP_EFF + amp_q, w["fone"][1] + SPEAKER_W[1] / AMP_EFF + amp_q)
    usable_wh = lambda mah: mah / 1000 * V_BATT * DERATE
    runtime = {mode: [(c, usable_wh(c) / wt, usable_wh(c) / wm) for c in CAPACITIES] for mode, (wt, wm) in w.items()}
    need = {mode: (TARGET_H * wt / V_BATT / DERATE * 1000, TARGET_H * wm / V_BATT / DERATE * 1000) for mode, (wt, wm) in w.items()}
    return {"rows": rows, "i_typ": i_typ, "i_max": i_max, "watts": w, "runtime": runtime, "need": need}


def write_power_md(pw, n_keys):
    f = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
    L = [
        "# eTuttino Pocket · orçamento de energia (v2)",
        "",
        "Gerado por `layout.py` (não editar à mão; mude o `BUDGET` no script).",
        f"Trilho de {f(V_RAIL)} V a partir de uma LiPo 1S por um buck-boost (eficiência {int(EFF * 100)} %). "
        f"O amplificador classe D do alto-falante vai direto na bateria (eficiência {int(AMP_EFF * 100)} %) e fica desligado com o fone plugado.",
        f"Capacidade útil = {int(DERATE * 100)} % da nominal (corte, envelhecimento, frio).",
        "",
        "| Consumidor (trilho de 3,3 V) | típ. (mA) | máx. (mA) |",
        "|---|---:|---:|",
    ]
    for name, t, m in pw["rows"]:
        L.append(f"| {name.replace('CHECK', 'conferir')} | {f(t)} | {f(m)} |")
    L += [
        f"| **Total** | **{f(pw['i_typ'])}** | **{f(pw['i_max'])}** |",
        "",
        f"Alto-falante: {f(SPEAKER_W[0], 2)} W médios tocando em volume normal, {f(SPEAKER_W[1], 2)} W alto (conferir medindo); amplificador {f(AMP_Q_MA, 0)} mA em repouso.",
        "",
        "| Modo | consumo da bateria, típ. / pior | para 4 h, típ. / pior |",
        "|---|---:|---:|",
    ]
    for mode, (wt, wm) in pw["watts"].items():
        nt, nm = pw["need"][mode]
        L.append(f"| {mode} | {f(wt, 2)} W / {f(wm, 2)} W | {nt:.0f} / {nm:.0f} mAh |")
    L += ["", "| Bateria | fone, típ. / pior | alto-falante, típ. / pior |", "|---|---:|---:|"]
    for (c, ft, fm), (_, st, sm) in zip(pw["runtime"]["fone"], pw["runtime"]["alto-falante"]):
        L.append(f"| {c} mAh | {f(ft)} h / {f(fm)} h | {f(st)} h / {f(sm)} h |")
    L += ["", f"Os {n_keys} sensores Hall são a maior parte do consumo. Medir a corrente real da placa é o primeiro teste do protótipo.", ""]
    with open(os.path.join(HERE, "POWER.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


# ---- drawing ----
def svg(info, keys, ref_box):
    pad = 12
    W, H = info["etuttino_length"] + 2 * pad, WIDTH + 2 * pad
    pts = lambda poly: " ".join(f"{x + pad:.2f},{y + pad:.2f}" for x, y in poly)
    c = info["controls"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" width="{W * 4:.0f}" height="{H * 4:.0f}" font-family="sans-serif">',
         f'<rect width="{W:.1f}" height="{H:.1f}" fill="#f2f3ef"/>',
         f'<defs><clipPath id="body"><polygon points="{pts(info["box"])}"/></clipPath></defs>',
         f'<polygon points="{pts(ref_box)}" fill="none" stroke="#b5b8b0" stroke-width="0.5" stroke-dasharray="2 1.5"/>',
         f'<polygon points="{pts(info["box"])}" fill="#dcdcd5"/>',
         f'<polygon points="{pts(info["ramp"])}" fill="#cfcfc7" clip-path="url(#body)"/>',
         f'<polygon points="{pts(info["chamfer"])}" fill="#bdbdb4"/>',
         f'<polygon points="{pts(info["opening"])}" fill="#262a27"/>',
         f'<polygon points="{pts(info["box"])}" fill="none" stroke="#3d423e" stroke-width="0.6"/>',
         f'<polygon points="{pts(c["logo"])}" fill="none" stroke="#9a9d95" stroke-width="0.35" stroke-dasharray="1 1"/>',
         f'<text x="{c["logo_text"][0] + pad:.1f}" y="{c["logo_text"][1] + pad:.1f}" font-size="5.2" text-anchor="middle" fill="#6d716a" font-weight="700">eTuttino</text>',
         f'<text x="{c["logo_text"][0] + pad:.1f}" y="{c["logo_text"][1] + pad + 4.4:.1f}" font-size="3" text-anchor="middle" fill="#6d716a" letter-spacing="0.6">POCKET</text>',
         f'<circle cx="{c["speaker"][0] + pad}" cy="{c["speaker"][1] + pad}" r="{SPEAKER_D / 2}" fill="none" stroke="#9a9d95" stroke-width="0.35" stroke-dasharray="1.2 1"/>']
    for x, y in c["holes"]:
        s.append(f'<circle cx="{x + pad:.2f}" cy="{y + pad:.2f}" r="{HOLE_D / 2}" fill="#7d8179"/>')
    for (x, y), lab in ((c["volume"], "VOL"), (c["select"], "SOM")):
        s.append(f'<circle cx="{x + pad}" cy="{y + pad}" r="{KNOB_D / 2}" fill="#2f3330"/>')
        s.append(f'<text x="{x + pad}" y="{y + pad - 6.5}" font-size="3" text-anchor="middle" fill="#6d716a">{lab}</text>')
    s.append(f'<circle cx="{c["led"][0] + pad}" cy="{c["led"][1] + pad}" r="{LED_D / 2}" fill="#46c06e"/>')
    for k in keys:
        fill = "#1b1d1c" if k["sharp"] else "#fbfbf8"
        s.append(f'<circle cx="{k["x"] + pad}" cy="{k["y"] + pad}" r="{D_BTN / 2}" fill="{fill}" stroke="#55594f" stroke-width="0.3"/>')
        s.append(f'<text x="{k["x"] + pad}" y="{k["y"] + pad + 1.2}" font-size="3.4" text-anchor="middle" fill="{"#ddd" if k["sharp"] else "#333"}">{k["note"]}</text>')
    for (x, y), lab in ((info["usb"], "USB"), (info["jack"], "fone")):
        s.append(f'<circle cx="{x + pad:.2f}" cy="{y + pad:.2f}" r="1.6" fill="#3d423e"/>')
        s.append(f'<text x="{x + pad - 3:.2f}" y="{y + pad + 1:.2f}" font-size="3" text-anchor="end" fill="#6d716a">{lab}</text>')
    s.append(f'<text x="{pad}" y="{H - 3}" font-size="4" fill="#3d423e">eTuttino Pocket v2 · {len(keys)} teclas · {info["length"]:.0f} × {WIDTH:.0f} mm (contorno aproximado)</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(BUILD, exist_ok=True)

    # The nose's leftmost point sits at x = 0: solve for O.
    retreat = R_VERTEX / math.sin(math.radians(60)) - R_VERTEX     # arc vs sharp vertex
    vx = -retreat
    x2 = vx + BAND_W + R_RAMP / COS30
    origin = round(x2 + P / 2, 2)
    keys = keys_for(TOP, origin)
    build_left, V = pocket_left_end(min(k["x"] for k in keys if k["row"] == 2))
    opening, chamfer, ramp, box = opening_and_box(keys, build_left)
    length = max(x for x, _ in box)
    assert abs(min(x for x, _ in box)) < 0.2, min(x for x, _ in box)

    ref = keys_for({1: "D#6", 2: "E6", 3: "D6", 4: "C6"}, O_ETUTTINO)
    assert len(ref) == 44
    _, _, _, ref_box = opening_and_box(ref, etuttino_left_end)
    ref_length = max(x for x, _ in ref_box)

    # ---- interface, back to front ----
    band_x = lambda y: (left_x(box, y), left_x(ramp, y))
    logo = parallelogram(box, ramp, *LOGO_Y, INSET)
    ly = sum(LOGO_Y) / 2
    logo_text = ((band_x(ly)[0] + band_x(ly)[1]) / 2, ly)
    lo, hi = band_x(KNOB_Y)
    knobs = {"volume": (VOLUME_X, KNOB_Y), "select": (SELECT_X, KNOB_Y), "led": (LED_X, KNOB_Y)}
    assert VOLUME_X - KNOB_D / 2 - lo >= 5.0, f"volume knob {VOLUME_X - KNOB_D / 2 - lo:.1f} mm from the left face"
    assert hi - (LED_X + LED_D / 2) >= 5.0, f"LED {hi - LED_X - LED_D / 2:.1f} mm from the ramp"
    grille = parallelogram(box, ramp, *GRILLE_Y, INSET)
    holes = []
    y = GRILLE_Y[0] + 2.0
    row = 0
    while y <= GRILLE_Y[1] - 2.0:
        a, b = left_x(box, y) + INSET + 2.0, left_x(ramp, y) - INSET - 2.0
        x = a + (HOLE_PITCH / 2 if row % 2 else 0)
        while x <= b:
            holes.append((round(x, 2), round(y, 2)))
            x += HOLE_PITCH
        y += HOLE_PITCH * COS30
        row += 1
    sl, sr = band_x(SPEAKER_Y)
    speaker = ((sl + sr) / 2, SPEAKER_Y)
    inner = offset_inward(box, WALL + 0.5)
    for i in range(36):
        a = 2 * math.pi * i / 36
        p = (speaker[0] + SPEAKER_D / 2 * math.cos(a), speaker[1] + SPEAKER_D / 2 * math.sin(a))
        assert point_in(inner, p), f"speaker leaves the case at {p}"
    assert speaker[1] + SPEAKER_D / 2 <= WIDTH - WALL - 0.5

    # connectors on the back-left face: on the line from the nose to the back corner
    on_face = lambda yy: (round(left_x(box, yy), 2), yy)
    usb, jack = on_face(USB_Y), on_face(JACK_Y)

    rows = {r: [k for k in keys if k["row"] == r] for r in (1, 2, 3, 4)}
    with open(os.path.join(BUILD, "pocket_keys.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["row", "note", "midi", "xp", "x", "y", "colour", "c_or_f"])
        for k in sorted(keys, key=lambda k: (k["row"], k["xp"])):
            w.writerow([k["row"], k["note"], k["midi"], k["xp"], k["x"], k["y"],
                        "black" if k["sharp"] else "white", int(k["cf"])])

    pw = power(len(keys))
    write_power_md(pw, len(keys))

    grid = []
    for r in (1, 2, 3, 4):
        ks = sorted(rows[r], key=lambda k: k["xp"])
        grid.append([ks[0]["midi"], len(ks), {1: 0.0, 2: -0.5, 3: 0.0, 4: 0.5}[r], 0 if r == 2 else 1])
    kx = [k["x"] for k in keys]
    battery = ((min(kx) + max(kx)) / 2, 50.0)
    rnd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
    info = {
        "version": 2, "keys": keys, "rows": grid, "length": round(length, 1), "width": WIDTH,
        "etuttino_length": round(ref_length, 1), "origin": origin,
        "range": f"{note_name(min(k['midi'] for k in keys))}–{note_name(max(k['midi'] for k in keys))}",
        "heights": {"deck": Z_DECK, "key_top": Z_KEY_TOP, "interface": Z_IF},
        "opening": rnd(opening), "chamfer": rnd(chamfer), "ramp": rnd(ramp), "box": rnd(box), "etuttino_box": rnd(ref_box),
        "controls": {**knobs, "logo": logo, "logo_text": [round(v, 2) for v in logo_text], "grille": grille,
                     "holes": holes, "speaker": [round(v, 2) for v in speaker], "speaker_d": SPEAKER_D},
        "usb": usb, "jack": jack,
        "battery": {"centre": [round(v, 2) for v in battery], "size": BATTERY},
        "power": {"i_typ": pw["i_typ"], "i_max": pw["i_max"], "watts": pw["watts"], "runtime": pw["runtime"], "need": pw["need"],
                  "rail_w": [V_RAIL, EFF, V_BATT, DERATE], "speaker_w": SPEAKER_W, "amp": [AMP_EFF, AMP_Q_MA]},
    }
    with open(os.path.join(BUILD, "pocket.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)
    with open(os.path.join(BUILD, "pocket_top.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg(info, keys, ref_box))

    print(f"{len(keys)} keys, {info['range']}; O = {origin}")
    print(f"case ~{length:.1f} x {WIDTH:.0f} mm (eTuttino ~{ref_length:.1f}); knob row {lo:.1f}..{hi:.1f}; speaker at ({speaker[0]:.1f}, {speaker[1]:.1f})")
    print(f"usb {usb}, jack {jack}; {len(holes)} grille holes")
    print(f"firmware ROWS = {grid}")
    for mode, runs in pw["runtime"].items():
        print(f"  {mode}: " + ", ".join(f"{c} mAh {t:.1f}/{m:.1f} h" for c, t, m in runs))


if __name__ == "__main__":
    main()
