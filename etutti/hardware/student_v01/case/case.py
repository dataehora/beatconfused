"""eTutti Student V01: the prototype's case, two printed pieces plus four spacers.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v01/case/case.py

Frame of the 3D model (model3d/build.py): x right, y = -y of KiCad, z up, millimetres,
**z = 0 at the top of the board**. The functions take KiCad x, y.

  fundo   tray under the board: floor, walls up to the board's top, a boss under each of the 8 M2
          holes, the 6 pillars that hold the keyboard up, a cradle for the battery, a hole to
          reach the Program button.
  tampa   lid: walls from the board's top up and a flat top that also covers the keyboard, like
          an accordion's: a thin deck just above the switches with one round hole per key, so
          only each key's stem comes out and the button sits above the deck. Under the deck a
          rim round the keyboard sits on the plate. Holes for the two knobs and the LED, a
          grille and a seat for the speaker, openings for USB-C and headphones in the left wall,
          four posts that take the screws.
  espacador  ring between board and plate at the four holes inside the keyboard (print 4).
  capa    the button: a stem that passes through the deck onto the switch's cross, and a domed
          head above the deck (print 28). It goes on from above, after the lid.

Screws: 8 x M2 from underneath. H1-H4 go through fundo and board into the lid's posts (self-tapping,
M2 x 16). H5-H8, between the keys, go through fundo, board, spacer and plate into an M2 nut on
the plate (M2 x 16).

Writes out/*.step, out/*.stl and out/case.json (the numbers the fit check and the render read).
"""
import json
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FOOTPRINTS = os.path.join(HERE, "..", "model3d", "build", "footprints.json")

# ---- the board and what stands on it (from the 3D model and its heights.json)
BOARD = (2.5, 2.5, 249.0, 97.5)      # KiCad x0, y0, x1, y1
BOARD_R = 5.0
T_PCB = 1.2
PLATE_TOP = 5.1                      # the plate's top face above the board (1.6 mm plate)
PLATE_T = 1.6
HOLES = [(88.0, 6.5), (74.0, 93.0), (6.0, 60.0), (55.0, 63.0),                    # H1-H4: lid posts
         (98.45, 52.67), (153.95, 31.31), (153.95, 63.35), (209.45, 52.67)]       # H5-H8: through the plate
PILLARS = [(197.5, 32.5), (207.5, 67.5), (112.5, 67.5), (167.5, 67.5), (127.5, 32.5), (132.5, 67.5)]
KNOBS = [(20.0, 49.0), (36.0, 49.0)]
LED = (50.0, 49.0)
SPEAKER = (31.0, 78.0)
SPEAKER_D, SPEAKER_H = 36.0, 4.6
PROGRAM = (52.0, 36.0)
USB_Y, USB_W, USB_H = 13.0, 9.6, 3.7          # opening in the left wall: centre, width, height above the board
JACK_Y, JACK_W, JACK_H = 25.08, 7.0, 5.6
BATTERY = (12.0, 45.0, 46.0, 95.0)            # KiCad x0, y0, x1, y1 of the 503450 under the front-left
BATTERY_BOTTOM = 7.6                          # below the board's top

# ---- the case
GAP = 0.4                # board to wall
WALL = 2.0
FLOOR = 2.0
DEPTH = 8.1              # inside floor, below the board's top (0.5 under the battery)
HOUSING_TOP = PLATE_TOP + 6.1     # top of a switch's housing above the board (11.2)
KEY_TRAVEL = 4.1
DECK_T = 1.6             # the perforated deck over the keys
LID_TOP = HOUSING_TOP + 0.4 + DECK_T      # 13.2: the deck clears the switch housings by 0.4
LID_T = 2.0
KEY_OPEN_R = 10.8        # the room under the deck is the union of a circle of this radius round every key
RIM_W = 2.5              # rim round that room, down to the plate
KEY_HOLE = 7.0           # hole in the deck for a key's stem (the button's stem is 5.6)
CAP_STEM_D = 5.6
CAP_HEAD_D = 16.5
CAP_HEAD_UNDER = LID_TOP + KEY_TRAVEL + 0.7    # 18.0: a pressed button stops 0.7 above the deck
CAP_HEAD_H = 3.9
CAP_CROSS = (4.15, 1.30, 3.8)                  # MX cross socket: arm length, arm width, depth
BOSS_D, BOSS_HOLE, HEAD_D, HEAD_DEPTH = 6.0, 2.4, 4.4, 2.2
PILLAR_D = 4.0
POST_D, POST_PILOT = 4.6, 1.6        # H1 is 2.7 mm from the plate's edge
KNOB_HOLE = 8.4                      # the encoder's bushing is 7.0
LED_HOLE = 3.1                       # a 3 mm light pipe
GRILLE_D, GRILLE_PITCH, GRILLE_HOLE = 30.0, 3.2, 1.6
SPACER_D, SPACER_HOLE = 4.6, 2.4


def keys():
    fps = json.load(open(FOOTPRINTS))["footprints"]
    return [(f["x"], f["y"]) for f in fps if f["lib"].startswith("Gateron")]


def prism(x0, y0, x1, y1, z0, z1, r):
    """Rounded box over a KiCad rectangle."""
    w = (cq.Workplane("XY").workplane(offset=z0).center((x0 + x1) / 2, -(y0 + y1) / 2)
         .rect(x1 - x0, y1 - y0).extrude(z1 - z0))
    return w.edges("|Z").fillet(r) if r > 0 else w


def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, -y).circle(d / 2).extrude(z1 - z0)


def union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


def shell(z0, z1):
    x0, y0, x1, y1 = BOARD
    g = GAP + WALL
    return prism(x0 - g, y0 - g, x1 + g, y1 + g, z0, z1, BOARD_R + g)


def cavity(z0, z1):
    x0, y0, x1, y1 = BOARD
    return prism(x0 - GAP, y0 - GAP, x1 + GAP, y1 + GAP, z0, z1, BOARD_R + GAP)


def fundo():
    zf = -DEPTH                              # inside floor
    body = shell(zf - FLOOR, 0).cut(cavity(zf, 0.01))
    for x, y in HOLES:
        body = body.union(cyl(x, y, zf, -T_PCB, BOSS_D))
    for x, y in PILLARS:
        body = body.union(cyl(x, y, zf, -T_PCB, PILLAR_D))
    # battery cradle: low ribs on three sides (the fourth is the front wall)
    bx0, by0, bx1, by1 = BATTERY
    rib, h = 1.2, 1.5
    for r in ((bx0 - rib - 0.3, by0 - rib - 0.3, bx1 + rib + 0.3, by0 - 0.3),
              (bx0 - rib - 0.3, by0 - 0.3, bx0 - 0.3, by1 - 8), (bx1 + 0.3, by0 - 0.3, bx1 + rib + 0.3, by1 - 8)):
        body = body.union(prism(r[0], r[1], r[2], r[3], zf, zf + h, 0))
    for x, y in HOLES:
        body = body.cut(cyl(x, y, zf - FLOOR - 1, 1, BOSS_HOLE))
        body = body.cut(cyl(x, y, zf - FLOOR - 0.01, zf - FLOOR + HEAD_DEPTH, HEAD_D))
    body = body.cut(cyl(PROGRAM[0], PROGRAM[1], zf - FLOOR - 1, zf + 1, 3.0))
    # the headphone socket's barrel hangs 0.25 mm below the board's top where it crosses the wall
    body = body.cut(prism(BOARD[0] - GAP - WALL - 1, JACK_Y - JACK_W / 2, BOARD[0] - GAP + 0.01, JACK_Y + JACK_W / 2, -0.7, 0.1, 0))
    return body


def tampa():
    under = LID_TOP - LID_T
    body = shell(0, LID_TOP).cut(cavity(-0.01, under))
    ks = keys()
    # rim round the key opening, from the lid down to the plate
    rim = union([cyl(x, y, PLATE_TOP, under + 0.01, 2 * (KEY_OPEN_R + RIM_W)) for x, y in ks])
    body = body.union(rim)
    for x, y in HOLES[:4]:
        body = body.union(cyl(x, y, 0, under + 0.01, POST_D))
    # speaker seat: a ring the speaker's rim sits in, under the grille
    sx, sy = SPEAKER
    body = body.union(cyl(sx, sy, under - 2.0, under + 0.01, SPEAKER_D + 3.2).cut(cyl(sx, sy, under - 3, under + 1, SPEAKER_D + 0.6)))
    # cuts: the room for the switches under the deck, then one hole per key through the deck
    body = body.cut(union([cyl(x, y, PLATE_TOP - 1, LID_TOP - DECK_T, 2 * KEY_OPEN_R) for x, y in ks]))
    body = body.cut(cq.Workplane("XY").workplane(offset=LID_TOP - DECK_T - 1).pushPoints([(x, -y) for x, y in ks])
                    .circle(KEY_HOLE / 2).extrude(DECK_T + 2))
    for x, y in KNOBS:
        body = body.cut(cyl(x, y, under - 1, LID_TOP + 1, KNOB_HOLE))
    body = body.cut(cyl(LED[0], LED[1], under - 1, LID_TOP + 1, LED_HOLE))
    n = int(GRILLE_D / GRILLE_PITCH / 2) + 1
    holes = [(sx + i * GRILLE_PITCH + (GRILLE_PITCH / 2 if j % 2 else 0), sy + j * GRILLE_PITCH * 0.866)
             for i in range(-n, n + 1) for j in range(-n, n + 1)]
    holes = [(x, y) for x, y in holes if (x - sx) ** 2 + (y - sy) ** 2 <= (GRILLE_D / 2) ** 2]
    body = body.cut(cq.Workplane("XY").workplane(offset=under - 1).pushPoints([(x, -y) for x, y in holes])
                    .circle(GRILLE_HOLE / 2).extrude(LID_T + 2))
    for x, y in HOLES[:4]:
        body = body.cut(cyl(x, y, -0.01, under - 1.0, POST_PILOT))
    # USB-C and headphone openings in the left wall, open at the bottom (the lid drops over them)
    x0 = BOARD[0] - GAP - WALL - 1
    for yc, w, h in ((USB_Y, USB_W, USB_H), (JACK_Y, JACK_W, JACK_H)):
        body = body.cut(prism(x0, yc - w / 2, BOARD[0] + 1.5, yc + w / 2, -0.01, h, 0))
    return body, len(holes)


def capa():
    """One button, key up, in the model's frame at x = y = 0 (its stem's foot at the switch housing's top)."""
    z0 = HOUSING_TOP
    stem = cq.Workplane("XY").workplane(offset=z0).circle(CAP_STEM_D / 2).extrude(CAP_HEAD_UNDER - z0 + 0.5)
    # head: a flat-bottomed dome, a slice of a sphere
    r = (CAP_HEAD_D ** 2 / 4 + CAP_HEAD_H ** 2) / (2 * CAP_HEAD_H)
    ball = cq.Workplane("XY").sphere(r).translate((0, 0, CAP_HEAD_UNDER + CAP_HEAD_H - r))
    head = ball.intersect(cq.Workplane("XY").workplane(offset=CAP_HEAD_UNDER).circle(CAP_HEAD_D).extrude(CAP_HEAD_H + 1))
    body = stem.union(head)
    L, w, d = CAP_CROSS
    cross = (cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(L, w).extrude(d)
             .union(cq.Workplane("XY").workplane(offset=z0 - 0.01).rect(w, L).extrude(d)))
    return body.cut(cross)


def espacador():
    return cyl(0, 0, 0, PLATE_TOP - PLATE_T - 0.05, SPACER_D).cut(cyl(0, 0, -1, 10, SPACER_HOLE))


def main():
    os.makedirs(OUT, exist_ok=True)
    f = fundo()
    t, grille = tampa()
    e = espacador()
    info = {}
    for name, w in (("fundo", f), ("tampa", t), ("espacador", e), ("capa", capa())):
        solids = w.solids().vals()
        bb = w.val().BoundingBox()
        vol = sum(s.Volume() for s in solids)
        info[name] = {"solidos": len(solids), "volume_cm3": round(vol / 1000, 1),
                      "caixa_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
                      "z": [round(bb.zmin, 2), round(bb.zmax, 2)]}
        cq.exporters.export(w, os.path.join(OUT, name + ".step"))
        cq.exporters.export(w, os.path.join(OUT, name + ".stl"), tolerance=0.03, angularTolerance=0.2)
    info["grade_furos"] = grille
    info["medidas"] = {"fora_mm": info["fundo"]["caixa_mm"][:2] + [round(DEPTH + FLOOR + LID_TOP, 1)],
                       "fundo_interno_abaixo_da_placa": DEPTH, "tampa_acima_da_placa": LID_TOP,
                       "deck_por_baixo": LID_TOP - DECK_T, "topo_do_alojamento_da_tecla": HOUSING_TOP,
                       "capa_cabeca_por_baixo": CAP_HEAD_UNDER, "capa_topo": CAP_HEAD_UNDER + CAP_HEAD_H,
                       "curso_da_tecla": KEY_TRAVEL,
                       "parede": WALL, "folga_da_placa": GAP}
    json.dump(info, open(os.path.join(OUT, "case.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(info, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
