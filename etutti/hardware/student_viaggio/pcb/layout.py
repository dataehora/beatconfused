"""eTutti StudentViaggio v0.2 -- the compact layout: outline, key centres, mounting holes.

    python etutti/hardware/student_viaggio/pcb/layout.py

Plain CPython (stdlib). Writes pcb/layout.json (read by build_board.py) and img/layout.svg.

Where it comes from:
  * the left block (x <= 78 mm: MicroMod, power, codec, encoders, connectors) and the top strip
    with the two multiplexers are the Viaggio J1's, at the J1's coordinates, routing included;
  * the keyboard is the studentBK draft's: 19.05 x 18.0 mm pitch, rows of 6 / 7 / 8 / 7 keys,
    the 8-key row the widest, and a board that ends in a point on the right;
  * the keys start as far left as the J1 block allows: the first key circle clears the VSYS
    track that runs down x = 60..61 to the speaker amplifier, and the top row clears the mux
    lines and their vias, which reach y = 21.6.

Coordinates are the J1 board's (KiCad frame, mm, y down): the board's top-left corner is
(2.5, 2.5), as on the J1.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PITCH_X, PITCH_Y = 19.05, 18.0
KEY_X0 = 68.5                   # centre of the first key of the 8-key row
ROW_Y = {4: 29.5, 3: 47.5, 2: 65.5, 1: 83.5}       # row 4 at the back (top), row 1 nearest the player
ROW_OFF = {4: 1.0, 3: 0.5, 2: 0.0, 1: 0.5}          # in pitches, from KEY_X0
ROW_KEYS = {1: range(1, 8), 2: range(8, 16), 3: range(16, 23), 4: range(23, 29)}   # K01..K28 (Pocket order)
KEY_R = 7.3                     # electrode courtyard radius

LEFT, TOP, BOTTOM = 2.5, 2.5, 97.5
CORNER_R = 5.0
RIGHT = 212.5                   # the tip
TIP_Y = (59.5, 71.5)            # flat part of the tip, centred on the 8-key row
TOP_END, BOTTOM_END = 195.0, 203.0      # where the top / bottom edges turn towards the tip

# M2 holes (2.2 mm, as on the J1). H1-H4 stay where the J1 has them; H5-H8 move into the new
# key grid (each sits 11.2-12 mm from its three nearest key centres); H9-H11 are new.
HOLES = {
    "H1": (88.0, 6.5), "H2": (72.5, 94.0), "H3": (6.0, 60.0), "H4": (55.0, 63.0),
    "H5": (KEY_X0 + 2.0 * PITCH_X, 41.5), "H6": (KEY_X0 + 5.0 * PITCH_X, 41.5),
    "H7": (KEY_X0 + 2.5 * PITCH_X, 71.5), "H8": (KEY_X0 + 5.5 * PITCH_X, 71.5),
    "H9": (206.5, 51.5), "H10": (197.0, 94.0), "H11": (KEY_X0 + 3.0 * PITCH_X, 94.0),
}


def keys():
    out = {}
    for row, ks in ROW_KEYS.items():
        for i, n in enumerate(ks):
            out[n] = (round(KEY_X0 + (ROW_OFF[row] + i) * PITCH_X, 3), ROW_Y[row], row)
    return out


def outline():
    """Edge.Cuts: [("line", x0, y0, x1, y1) | ("arc", x0, y0, xm, ym, x1, y1)], clockwise from the top-left."""
    r = CORNER_R
    k = r * (1 - math.sqrt(0.5))
    return [
        ("arc", LEFT, TOP + r, LEFT + k, TOP + k, LEFT + r, TOP),
        ("line", LEFT + r, TOP, TOP_END, TOP),
        ("line", TOP_END, TOP, RIGHT, TIP_Y[0]),
        ("line", RIGHT, TIP_Y[0], RIGHT, TIP_Y[1]),
        ("line", RIGHT, TIP_Y[1], BOTTOM_END, BOTTOM),
        ("line", BOTTOM_END, BOTTOM, LEFT + r, BOTTOM),
        ("arc", LEFT + r, BOTTOM, LEFT + k, BOTTOM - k, LEFT, BOTTOM - r),
        ("line", LEFT, BOTTOM - r, LEFT, TOP + r),
    ]


def polygon():
    return [(LEFT, TOP), (TOP_END, TOP), (RIGHT, TIP_Y[0]), (RIGHT, TIP_Y[1]), (BOTTOM_END, BOTTOM), (LEFT, BOTTOM)]


def dist_seg(p, a, b):
    l2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    u = max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / l2))
    return math.hypot(a[0] + u * (b[0] - a[0]) - p[0], a[1] + u * (b[1] - a[1]) - p[1])


def check(ks):
    poly = polygon()
    edges = list(zip(poly, poly[1:] + poly[:1]))
    worst_edge = min(min(dist_seg((x, y), a, b) for a, b in edges) - KEY_R for x, y, _ in ks.values())
    worst_key = min(math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in ks.items() for j, b in ks.items() if i < j)
    worst_hole = min(math.hypot(h[0] - k[0], h[1] - k[1]) for h in HOLES.values() for k in ks.values())
    hole_edge = min(min(dist_seg(h, a, b) for a, b in edges) for h in HOLES.values())
    if worst_edge < 2.0 or worst_key < 2 * KEY_R + 2.0 or worst_hole < KEY_R + 3.5 or hole_edge < 3.0:
        raise SystemExit("layout: key to edge %.2f, key to key %.2f, hole to key %.2f, hole to edge %.2f"
                         % (worst_edge, worst_key, worst_hole, hole_edge))
    return {"tecla_borda_min": round(worst_edge, 2), "tecla_tecla_centros_min": round(worst_key, 2),
            "furo_tecla_centros_min": round(worst_hole, 2), "furo_borda_min": round(hole_edge, 2)}


def svg(ks):
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 216 100" width="1080" height="500">',
         '<rect width="216" height="100" fill="#fff"/>',
         '<polygon points="%s" fill="#e8efe8" stroke="#234" stroke-width="0.4"/>'
         % " ".join("%.2f,%.2f" % p for p in polygon()),
         '<rect x="2.5" y="2.5" width="75.5" height="95" fill="#c9d6e8" opacity="0.5"/>',
         '<text x="6" y="94" font-size="3.2" fill="#234">bloco da Viaggio J1 (x &lt;= 78)</text>']
    for n, (x, y, row) in sorted(ks.items()):
        s.append('<circle cx="%.2f" cy="%.2f" r="%.1f" fill="#f2d24a" stroke="#654" stroke-width="0.3"/>' % (x, y, KEY_R))
        s.append('<text x="%.2f" y="%.2f" font-size="3" text-anchor="middle">K%02d</text>' % (x, y + 1, n))
    for h, (x, y) in HOLES.items():
        s.append('<circle cx="%.2f" cy="%.2f" r="1.1" fill="#fff" stroke="#c00" stroke-width="0.4"/>' % (x, y))
        s.append('<text x="%.2f" y="%.2f" font-size="2.4" fill="#c00">%s</text>' % (x + 1.6, y + 0.9, h))
    return "\n".join(s + ["</svg>"]) + "\n"


def main():
    ks = keys()
    data = {"versao": "0.2", "passo": [PITCH_X, PITCH_Y], "raio_tecla": KEY_R,
            "teclas": {"K%02d" % n: {"x": x, "y": y, "fileira": row} for n, (x, y, row) in sorted(ks.items())},
            "contorno": outline(), "poligono": polygon(), "furos": HOLES,
            "tamanho_mm": [round(RIGHT - LEFT, 2), round(BOTTOM - TOP, 2)], "folgas": check(ks)}
    json.dump(data, open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.makedirs(os.path.join(HERE, "..", "img"), exist_ok=True)
    open(os.path.join(HERE, "..", "img", "layout.svg"), "w", encoding="utf-8", newline="\n").write(svg(ks))
    print("placa %.1f x %.1f mm; %s" % (RIGHT - LEFT, BOTTOM - TOP, data["folgas"]))


if __name__ == "__main__":
    main()
