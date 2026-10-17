"""eTuttino Pocket -- key layout, plan outline and power budget (SPEC v1).

Stdlib only:  python etutti/hardware/pocket/layout.py
Writes into etutti/hardware/pocket/build/:
  pocket_keys.csv     one line per key (note, row, xp, x, y, colour)
  pocket_top.svg      plan view to scale, the eTuttino's outline behind it
  pocket.json         the numbers the prototype page and later scripts read
and rewrites etutti/hardware/pocket/POWER.md from the budget below.

Same C-griff geometry as the eTuttino (case/case.py, case/SPEC.md):
pitch 18.5, rows 16.02 apart, 100 mm deep box. Only the key count, the
keyboard origin O and the interface change. The plan outline here is a
preview (convex hull of the clearance circles); case.py stays the source
of the exact case once it learns the Pocket model.
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
CLR_SIDE = 15.0                                       # button edge -> opening, sides
BOX_OFF = 10.3                                        # opening -> outer wall
R_OPEN = D_BTN / 2 + CLR_SIDE                         # 22.5, concentric with the row-2 end keys
R_BOX = R_OPEN + BOX_OFF                              # 32.8
CLR_FB = WIDTH / 2 - BOX_OFF - 1.5 * ROW_PITCH - D_BTN / 2   # ~8.17
RAMP_TOP_R = R_OPEN + 12.7                            # 35.2: interface ramp, top edge
TAN30 = math.tan(math.radians(30))

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
G3 = 55

# ---- the Pocket ----
# Highest note per row (the user's spec): row 4 C5, row 3 D5, row 2 E5, row 1 D#5.
TOP = {1: "D#5", 2: "E5", 3: "D5", 4: "C5"}
O_ETUTTINO = 104.0
O_POCKET = 84.0             # x of xp = 0: compact interface (controls 16 mm apart, no screen zone)

# Interface (SPEC v1 section 5), plan positions in mm
VOLUME_XY = (12.0, 45.0)
SELECT_XY = (28.0, 45.0)
LED_XY = (40.0, 45.0)
KNOB_D = 9.0
LED_D = 3.5
GRILLE = (8.0, 61.0, 32.0, 88.0)      # x0, y0, x1, y1 on the 13 deg slope


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


def circles(keys, r, y0, y1, steps=72):
    pts = []
    for k in keys:
        for i in range(steps):
            a = 2 * math.pi * i / steps
            pts.append((round(k["x"] + r * math.cos(a), 3), round(min(y1, max(y0, k["y"] + r * math.sin(a))), 3)))
    return pts


def outlines(keys):
    y_top = ROW_Y[4] - D_BTN / 2 - CLR_FB
    y_bot = ROW_Y[1] + D_BTN / 2 + CLR_FB
    opening = hull(circles(keys, R_OPEN, y_top, y_bot))
    box = hull(circles(keys, R_BOX, 0.0, WIDTH) + [(0.0, 0.0), (0.0, WIDTH)])
    return opening, box


def row2_end(keys, last=False):
    xs = [k["x"] for k in keys if k["row"] == 2]
    return max(xs) if last else min(xs)


# ---- power budget, 3.3 V rail (mA): typical, maximum ----
# Every line marked CHECK is an estimate to measure on the first board.
BUDGET = [
    ("Teensy 4.0 a 600 MHz (CHECK: medir)", 100.0, 120.0),
    ("Audio Board (SGTL5000) com fone 32 ohm, volume normal (CHECK)", 20.0, 40.0),
    ("Sensores Hall DRV5056, {n} x 6 mA (máx. 10 mA, datasheet TI)", None, None),
    ("2 x CD74HC4067", 0.1, 0.2),
    ("LED bicolor (um lado aceso, 330 ohm)", 4.0, 8.0),
    ("Carregador + conversor, quiescente", 0.1, 0.5),
]
V_RAIL = 3.3
EFF = 0.90           # buck-boost at ~300-450 mA (CHECK the chosen part's curve)
V_BATT = 3.7
DERATE = 0.85        # cut-off at 3.0-3.3 V, ageing, cold
TARGET_H = 4.0
CAPACITIES = [1500, 2000, 2500]


def power(n_keys):
    rows = []
    for name, typ, mx in BUDGET:
        if typ is None:
            name, typ, mx = name.format(n=n_keys), 6.0 * n_keys, 10.0 * n_keys
        rows.append((name, typ, mx))
    i_typ = sum(r[1] for r in rows)
    i_max = sum(r[2] for r in rows)
    def need(i):
        wh = i / 1000 * V_RAIL / EFF * TARGET_H
        return wh, wh / V_BATT * 1000 / DERATE
    def hours(i, mah):
        return mah * DERATE / 1000 * V_BATT * EFF / (i / 1000 * V_RAIL)
    return {
        "rows": rows, "i_typ": i_typ, "i_max": i_max,
        "need_typ": need(i_typ), "need_max": need(i_max),
        "runtime": [(c, hours(i_typ, c), hours(i_max, c)) for c in CAPACITIES],
    }


def write_power_md(pw, n_keys):
    f = lambda v: f"{v:.1f}".replace(".", ",")
    lines = [
        "# eTuttino Pocket · orçamento de energia",
        "",
        "Gerado por `layout.py` (não editar à mão; mude o `BUDGET` no script).",
        f"Trilho único de {f(V_RAIL)} V a partir de uma LiPo 1S por um conversor buck-boost (eficiência {int(EFF * 100)} %).",
        f"Meta: {f(TARGET_H)} h tocando com fone. Capacidade útil = {int(DERATE * 100)} % da nominal (corte, envelhecimento, frio).",
        "",
        "| Consumidor | típ. (mA) | máx. (mA) |",
        "|---|---:|---:|",
    ]
    for name, t, m in pw["rows"]:
        lines.append(f"| {name.replace('CHECK', 'conferir')} | {f(t)} | {f(m)} |")
    lines += [
        f"| **Total no trilho de {f(V_RAIL)} V** | **{f(pw['i_typ'])}** | **{f(pw['i_max'])}** |",
        "",
        f"Para {f(TARGET_H)} h: típico {f(pw['need_typ'][0])} Wh → **{pw['need_typ'][1]:.0f} mAh**; "
        f"pior caso {f(pw['need_max'][0])} Wh → **{pw['need_max'][1]:.0f} mAh**.",
        "",
        "| Bateria | autonomia típica | pior caso |",
        "|---|---:|---:|",
    ]
    for c, ht, hm in pw["runtime"]:
        lines.append(f"| {c} mAh | {f(ht)} h | {f(hm)} h |")
    lines += [
        "",
        f"Os {n_keys} sensores Hall são mais da metade do consumo. O datasheet dá 6 mA típicos por sensor; "
        "medir a corrente real da placa é o primeiro teste do protótipo.",
        "",
    ]
    with open(os.path.join(HERE, "POWER.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def svg(keys, opening, box, ref_box, length, ref_length):
    pad = 12
    W = ref_length + 2 * pad
    H = WIDTH + 2 * pad
    pts = lambda poly: " ".join(f"{x + pad:.2f},{y + pad:.2f}" for x, y in poly)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" width="{W * 4:.0f}" height="{H * 4:.0f}" font-family="sans-serif">',
         f'<rect width="{W:.1f}" height="{H:.1f}" fill="#f6f4ef"/>',
         f'<polygon points="{pts(ref_box)}" fill="none" stroke="#b9b2a6" stroke-width="0.5" stroke-dasharray="2 1.5"/>',
         f'<text x="{ref_length + pad - 2:.1f}" y="{pad - 3}" font-size="4" text-anchor="end" fill="#8a8377">eTuttino {ref_length:.0f} mm</text>',
         f'<polygon points="{pts(box)}" fill="#e7e1d6" stroke="#4a443c" stroke-width="0.6"/>',
         f'<polygon points="{pts(opening)}" fill="#26231f"/>',
         f'<rect x="{GRILLE[0] + pad}" y="{GRILLE[1] + pad}" width="{GRILLE[2] - GRILLE[0]}" height="{GRILLE[3] - GRILLE[1]}" rx="3" fill="none" stroke="#9c9486" stroke-width="0.4"/>']
    gx = GRILLE[0] + 3
    while gx < GRILLE[2] - 1:
        gy = GRILLE[1] + 3
        while gy < GRILLE[3] - 1:
            s.append(f'<circle cx="{gx + pad:.1f}" cy="{gy + pad:.1f}" r="0.95" fill="#9c9486"/>')
            gy += 4
        gx += 4
    for (x, y), lab in ((VOLUME_XY, "VOL"), (SELECT_XY, "SOM")):
        s.append(f'<circle cx="{x + pad}" cy="{y + pad}" r="{KNOB_D / 2}" fill="#3b3631"/>')
        s.append(f'<text x="{x + pad}" y="{y + pad - 6.5}" font-size="3" text-anchor="middle" fill="#6b645a">{lab}</text>')
    s.append(f'<circle cx="{LED_XY[0] + pad}" cy="{LED_XY[1] + pad}" r="{LED_D / 2}" fill="#5fb85f"/>')
    for k in keys:
        fill = "#1d1b19" if k["sharp"] else "#fbfaf6"
        s.append(f'<circle cx="{k["x"] + pad}" cy="{k["y"] + pad}" r="{D_BTN / 2}" fill="{fill}" stroke="#55504a" stroke-width="0.3"/>')
        if k["cf"]:
            s.append(f'<circle cx="{k["x"] + pad}" cy="{k["y"] + pad}" r="4" fill="none" stroke="#b9b2a6" stroke-width="0.5" stroke-dasharray="0.8 0.8"/>')
        s.append(f'<text x="{k["x"] + pad}" y="{k["y"] + pad + 1.2}" font-size="3.4" text-anchor="middle" fill="{"#ddd" if k["sharp"] else "#333"}">{k["note"]}</text>')
    s.append(f'<text x="{pad}" y="{H - 3}" font-size="4" fill="#4a443c">eTuttino Pocket · {len(keys)} teclas · {length:.0f} × {WIDTH:.0f} mm (contorno aproximado)</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(BUILD, exist_ok=True)
    keys = keys_for(TOP, O_POCKET)
    opening, box = outlines(keys)
    length = max(x for x, _ in box)

    ref = keys_for({1: "D#6", 2: "E6", 3: "D6", 4: "C6"}, O_ETUTTINO)
    assert len(ref) == 44, len(ref)
    _, ref_box = outlines(ref)
    ref_length = max(x for x, _ in ref_box)

    # interface checks: controls clear of the ramp's top edge by >= 5 mm
    x2 = row2_end(keys)
    ramp_x_at = lambda y: x2 - RAMP_TOP_R + max(0.0, ROW_Y[2] - y) * TAN30
    led_margin = ramp_x_at(LED_XY[1]) - (LED_XY[0] + LED_D / 2)
    assert led_margin >= 5.0, f"LED only {led_margin:.1f} mm from the ramp"
    assert SELECT_XY[0] - VOLUME_XY[0] - KNOB_D >= 6.0, "knobs too close"

    rows = {r: [k for k in keys if k["row"] == r] for r in (1, 2, 3, 4)}
    with open(os.path.join(BUILD, "pocket_keys.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["row", "note", "midi", "xp", "x", "y", "colour", "c_or_f"])
        for k in sorted(keys, key=lambda k: (k["row"], k["xp"])):
            w.writerow([k["row"], k["note"], k["midi"], k["xp"], k["x"], k["y"],
                        "black" if k["sharp"] else "white", int(k["cf"])])
    with open(os.path.join(BUILD, "pocket_top.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg(keys, opening, box, ref_box, length, ref_length))

    pw = power(len(keys))
    write_power_md(pw, len(keys))

    # Firmware/page grid, same convention as generate.py's ROWS:
    # (first MIDI note, count, x offset in key units, first column)
    grid = []
    for r in (1, 2, 3, 4):
        ks = sorted(rows[r], key=lambda k: k["xp"])
        grid.append([ks[0]["midi"], len(ks), {1: 0.0, 2: -0.5, 3: 0.0, 4: 0.5}[r], 0 if r == 2 else 1])
    info = {
        "keys": keys, "rows": grid, "length": round(length, 1), "width": WIDTH,
        "etuttino_length": round(ref_length, 1), "origin": O_POCKET,
        "range": f"{note_name(min(k['midi'] for k in keys))}–{note_name(max(k['midi'] for k in keys))}",
        "opening": opening, "box": box, "etuttino_box": ref_box,
        "controls": {"volume": VOLUME_XY, "select": SELECT_XY, "led": LED_XY, "grille": GRILLE},
        "power": {"i_typ": pw["i_typ"], "i_max": pw["i_max"],
                  "mah_typ": round(pw["need_typ"][1]), "mah_max": round(pw["need_max"][1]),
                  "runtime": pw["runtime"]},
    }
    with open(os.path.join(BUILD, "pocket.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)

    print(f"{len(keys)} keys, {info['range']}; rows " +
          ", ".join(f"{r}: {len(rows[r])} ({rows[r][0]['note']}..{max(rows[r], key=lambda k: k['xp'])['note']})" for r in (1, 2, 3, 4)))
    print(f"case ~{length:.1f} x {WIDTH:.0f} mm (eTuttino ~{ref_length:.1f}); LED {led_margin:.1f} mm from the ramp")
    print(f"firmware ROWS = {grid}")
    print(f"power {pw['i_typ']:.0f} mA typ / {pw['i_max']:.0f} mA max at 3.3 V; "
          f"4 h needs {pw['need_typ'][1]:.0f} mAh typ / {pw['need_max'][1]:.0f} mAh worst")
    for c, ht, hm in pw["runtime"]:
        print(f"  {c} mAh: {ht:.1f} h typ, {hm:.1f} h worst")


if __name__ == "__main__":
    main()
