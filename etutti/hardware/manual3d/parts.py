"""Component library and assembly for the manual's 3D pictures.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe parts.py

Models the parts KiCad has no 3D model for, from their datasheet sizes
(marked CHECK where a size is a guess), one STL per material, and writes
where every instance goes. Everything is in the case files' frame
(x right, y away from the player, z up, mm; y_file = 100 - y_spec) so it
lines up with case/out/*.stl and the KiCad boards.

Writes build/lib/<part>.<material>.stl and build/assembly.json.
render_blender.py reads both.
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "case"))
import case as C  # noqa: E402
import keycap as K  # noqa: E402

BUILD = os.path.join(HERE, "build")
LIB = os.path.join(BUILD, "lib")
F = lambda y: C.WIDTH - y      # SPEC y -> file y


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane().add(cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0)))


def cbox(cx, cy, z0, sx, sy, h):
    return box(cx - sx / 2, cy - sy / 2, z0, cx + sx / 2, cy + sy / 2, z0 + h)


def cyl(x, y, z0, h, d, axis=(0, 0, 1)):
    return cq.Workplane().add(cq.Solid.makeCylinder(d / 2, h, cq.Vector(x, y, z0), cq.Vector(*axis)))


def union(*ws):
    out = ws[0]
    for w in ws[1:]:
        out = out.union(w)
    return out


# ------------------------------------------------------------- stack
# Teensy 4.0 (PJRC drawing): 35.56 x 17.78, pins 2.54 on rows 15.24 apart.
# Audio Adaptor Rev D: 38.0 x 36.8 (measured, fit_check), SGTL5000 QFN-20
# 3 x 3, 3.5 mm headphone jack, micro SD socket underneath -- CHECK.
BOARD_T = 1.6
TEENSY = (35.56, 17.78)
HEADER_PLASTIC = 2.5      # the extra-long header's plastic: the only spacer
AUDIO_LIFT = 3.0
ENV = json.load(open(os.path.join(C.OUT, "pcb_envelope.json")))
ST = ENV["stack"]
AX0, AY0, AX1, AY1 = ST["audio_board"]              # SPEC
ROW_Y = ST["pin_rows_y"]                            # SPEC
PIN_X = [ST["pin1_x"] + i * ST["pin_pitch"] for i in range(ST["pins_per_row"])]
CX = (PIN_X[0] + PIN_X[-1]) / 2
CY = sum(ROW_Y) / 2
Z_AB = C.Z_PCB_TOP + AUDIO_LIFT                     # Audio Board underside
Z_TEENSY = Z_AB + BOARD_T + HEADER_PLASTIC          # Teensy underside


def teensy():
    """Local: centre of the board, underside at z = 0, USB towards -x."""
    w, d = TEENSY
    pcb = box(-w / 2, -d / 2, 0, w / 2, d / 2, BOARD_T)
    for x in PIN_X:
        for y in (-7.62, 7.62):
            pcb = pcb.cut(cyl(x - CX, y, -1, 4, 1.0))
    t = BOARD_T
    chips = union(cbox(2.5, 0, t, 10.0, 10.0, 1.1),     # i.MX RT1062
                  cbox(-6.5, 3.6, t, 4.0, 3.0, 0.8),    # flash
                  cbox(-7.0, -4.0, t, 3.0, 3.0, 0.9),   # MKL02
                  cbox(10.6, -3.4, t, 3.2, 2.5, 0.8))   # crystal can
    button = cbox(14.8, 0, t, 3.0, 4.0, 1.6)
    usb = cbox(-w / 2 + 2.4, 0, t, 5.6, 7.6, 2.6)       # micro-B, 1 mm past the edge
    usb = usb.cut(cbox(-w / 2 - 0.6, 0, t + 0.6, 2.0, 6.4, 1.4))
    led = cbox(-11.5, 6.6, t, 1.6, 0.8, 0.5)
    caps = union(*[cbox(x, y, t, 1.0, 0.5, 0.5) for x, y in ((8.6, 4.0), (8.6, -4.6), (-2.8, -6.6), (-3.8, 6.4),
                                                             (11.4, 2.2), (-10.4, -1.0))])
    return {"pcb_teensy": pcb, "chip": chips, "button": button, "steel": usb, "led_orange": led, "cap0402": caps}


def audio_board():
    """Local: board's own corner (SPEC x0, file y of its far edge) -> placed
    so its underside is at z = 0. USB/jack end towards -x."""
    w, d = AX1 - AX0, AY1 - AY0
    pcb = box(0, 0, 0, w, d, BOARD_T)
    yrow = [F(r) - F(AY1) for r in ROW_Y]
    for x in PIN_X:
        for y in yrow:
            pcb = pcb.cut(cyl(x - AX0, y, -1, 4, 1.0))
    t = BOARD_T
    # SPEC y of the jack (fit_check): cy + 7.62 + 7.2
    jy = F(CY + 7.62 + 7.2) - F(AY1)
    jack = cbox(6.5, jy, t, 13.0, 6.0, 5.1).union(cyl(-0.8, jy, t + 2.55, 1.0, 5.0, (1, 0, 0)).translate((0, 0, 0)))
    jack = jack.cut(cyl(-1.0, jy, t + 2.55, 6, 3.6, (1, 0, 0)))
    cy_l = F(CY) - F(AY1)
    codec = cbox(CX - AX0 - 1.0, F(CY + 14.0) - F(AY1), t, 3.0, 3.0, 0.9)
    reg = cbox(CX - AX0 + 9.0, F(CY + 13.0) - F(AY1), t, 2.9, 1.6, 1.1)
    caps = union(*[cbox(CX - AX0 + dx, F(CY + dy) - F(AY1), t, 1.6, 0.8, 0.8)
                   for dx, dy in ((-6, 12), (-6, 15.5), (4, 11.5), (4, 16.5), (13, 15.5), (15, 11.0))])
    sd = cbox(w - 8.0, cy_l, -1.8, 12.0, 11.5, 1.8)      # micro SD socket underneath
    return {"pcb_audio": pcb, "chip": codec.union(reg), "plastic_black": jack, "cap0805": caps, "steel": sd}


def header():
    """One 1x14 extra-long male header, local: pin 1 at x = 0, plastic
    underside at z = 0. Pins run from below the main board to above the Teensy."""
    n = ST["pins_per_row"]
    plastic = box(-1.27, -1.27, 0, (n - 1) * 2.54 + 1.27, 1.27, HEADER_PLASTIC)
    z_bot = C.Z_PCB_BOT - 1.6 - Z_AB - BOARD_T       # relative to the plastic's underside
    z_top = BOARD_T + HEADER_PLASTIC + 1.6
    pins = union(*[box(i * 2.54 - 0.32, -0.32, z_bot, i * 2.54 + 0.32, 0.32, z_top) for i in range(n)])
    return {"plastic_black": plastic, "tin": pins}


def solder_joints():
    """Solder fillets where the header pins meet each board (and under the main board)."""
    shapes = []
    for row in ROW_Y:
        for x in PIN_X:
            y = F(row)
            for z0, up in ((C.Z_PCB_BOT, False), (Z_AB, False), (Z_TEENSY + BOARD_T, True)):
                if up:
                    shapes.append(cq.Workplane().add(cq.Solid.makeCone(1.0, 0.35, 0.8, cq.Vector(x, y, z0))))
                else:
                    shapes.append(cq.Workplane().add(cq.Solid.makeCone(1.0, 0.35, 0.8, cq.Vector(x, y, z0),
                                                                       cq.Vector(0, 0, -1))))
    return {"tin": union(*shapes)}


# ------------------------------------------------------------- switches and caps
def gateron():
    """Gateron KS-20 magnetic switch, local: centre, plate top at z = 0."""
    zp = 0.0
    zb = -(C.Z_PLATE_TOP - C.Z_PCB_TOP)             # board top
    bot = cbox(0, 0, zb, K.BOTTOM_W, K.BOTTOM_W, -C.PLATE_T - zb)
    clips = union(cbox(0, 7.25, -C.PLATE_T - 1.2, 4.0, 0.6, 1.2), cbox(0, -7.25, -C.PLATE_T - 1.2, 4.0, 0.6, 1.2))
    pegs = union(cyl(-5.08, 0, zb - 2.2, 2.2, 1.7), cyl(5.08, 0, zb - 2.2, 2.2, 1.7))
    def octagon(wx, wy, c, z):
        hx, hy = wx / 2, wy / 2
        pts = [(-hx + c, -hy), (hx - c, -hy), (hx, -hy + c), (hx, hy - c), (hx - c, hy), (-hx + c, hy),
               (-hx, hy - c), (-hx, -hy + c)]
        return cq.Wire.makePolygon([cq.Vector(x, y, z) for x, y in pts], close=True)
    top = cq.Workplane().add(cq.Solid.makeLoft([
        octagon(K.HOUSING_W_BOT[0], K.HOUSING_W_BOT[1], K.HOUSING_CHAMFER, zp - C.PLATE_T),
        octagon(K.HOUSING_W_BOT[0], K.HOUSING_W_BOT[1], K.HOUSING_CHAMFER, zp + 1.0),
        octagon(K.HOUSING_W_TOP, K.HOUSING_W_TOP, K.HOUSING_CHAMFER * 0.8, K.HOUSING_H)], True))
    light = cbox(0, 5.0, K.HOUSING_H - 0.01, 3.0, 2.0, 0.02)
    stem = cyl(0, 0, K.HOUSING_H, K.STEM_ABOVE * 0.4, 5.4).union(
        union(cbox(0, 0, K.HOUSING_H, 4.0, 1.17, K.STEM_ABOVE), cbox(0, 0, K.HOUSING_H, 1.17, 4.0, K.STEM_ABOVE)))
    return {"plastic_dark": bot.union(pegs).union(clips), "smoke": top, "stem": stem, "plastic_black": light}


# ------------------------------------------------------------- controls board parts
def pot():
    """Alps RK09K vertical, 15 mm knurled shaft from the mounting face (z = 0 = board top)."""
    body = cbox(0, 0, 0, 9.8, 11.0, 6.5)
    bush = cyl(0, 0, 6.5, 5.0, 7.0)
    shaft = cyl(0, 0, 11.5, 15.0 - 5.0, 6.0)
    legs = union(*[cbox(dx, -6.0, -3.0, 0.8, 0.3, 3.5) for dx in (-2.5, 0, 2.5)])
    lugs = union(cbox(-5.0, 2.0, -2.5, 0.4, 2.0, 2.5), cbox(5.0, 2.0, -2.5, 0.4, 2.0, 2.5))
    return {"steel": body.union(lugs), "brass": bush, "alu": shaft, "tin": legs}


def encoder():
    """Alps EC11E with switch, 15 mm shaft, M7 bushing."""
    body = cbox(0, 0, 0, 12.4, 13.2, 6.5)
    base = cbox(0, 0, 0, 12.4, 13.2, 1.5)
    bush = cyl(0, 0, 6.5, 5.0, 7.0)
    shaft = cyl(0, 0, 11.5, 15.0 - 5.0, 6.0).cut(box(1.5, -4, 16.5, 4, 4, 27))
    legs = union(*[cbox(dx, -7.5, -3.0, 0.8, 0.3, 3.5) for dx in (-2.5, 0, 2.5)],
                 *[cbox(dx, 7.0, -3.0, 0.8, 0.3, 3.5) for dx in (-2.5, 2.5)])
    return {"steel": body.cut(base), "plastic_black": base, "brass": bush, "alu": shaft, "tin": legs}


def knob():
    """Ø9 knob for a 6 mm shaft, local: underside at z = 0, with a pointer groove."""
    k = cyl(0, 0, 0, 6.4, 9.0)
    k = k.faces(">Z").edges().fillet(0.8)
    k = k.cut(cbox(0, 2.6, 5.9, 0.7, 2.4, 1.0))
    for i in range(24):
        a = 2 * math.pi * i / 24
        k = k.cut(cyl(4.6 * math.cos(a), 4.6 * math.sin(a), 0.8, 4.6, 0.6))
    return {"knob": k}


def led(spacer):
    """3 mm red/green LED on a spacer; local: board top at z = 0."""
    out = {"led_lens": cyl(0, 0, spacer + 1.0, 4.3 - 1.5, 3.0).union(
        cq.Workplane().add(cq.Solid.makeSphere(1.5, cq.Vector(0, 0, spacer + 3.8)))).union(
        cyl(0, 0, spacer, 1.0, 3.8)),
        "tin": union(*[cbox(dx, 0, -2.5, 0.45, 0.45, spacer + 2.5) for dx in (-1.27, 0, 1.27)])}
    if spacer > 0:
        out["plastic_black"] = cyl(0, 0, 0, spacer, 4.5).cut(cyl(0, 0, -1, spacer + 2, 3.0))
    return out


# ------------------------------------------------------------- connectors and cables
def ph_plug():
    """JST PHR-8 housing, local: mating face at z = 0, body going -z."""
    h = cbox(0, 0, -6.0, 15.8, 4.5, 6.0)
    for i in range(8):
        h = h.cut(cbox((i - 3.5) * 2.0, 0, -6.5, 1.2, 1.2, 1.0))
    return {"plastic_white": h}


def panel_usb():
    """Panel micro-B socket behind the insert, local: front face at x = 0, body +x."""
    body = box(0, -5.0, -4.0, 10.0, 5.0, 4.0)
    flange = box(-1.0, -6.5, -2.0, 0, 6.5, 2.0)
    mouth = box(-1.1, -3.9, -1.2, 2.0, 3.9, 1.2)
    return {"plastic_black": body.cut(mouth), "steel": flange.cut(mouth).union(box(-0.9, -3.6, -1.0, 0.5, 3.6, 1.0))}


def panel_jack():
    """Panel 3.5 mm jack, M6 bushing through the insert, nut outside."""
    body = cyl(0.0, 0, 0, 10.0, 8.0, (1, 0, 0))
    bush = cyl(-4.5, 0, 0, 4.5, 6.0, (1, 0, 0)).cut(cyl(-5, 0, 0, 6, 3.6, (1, 0, 0)))
    nut = cq.Workplane("YZ").polygon(6, 9.2).extrude(-1.8).translate((-2.6, 0, 0)).cut(cyl(-5, 0, 0, 6, 6.0, (1, 0, 0)))
    lugs = union(*[box(10.0, dy - 0.4, -1.5, 13.0, dy + 0.4, 1.5) for dy in (-2.5, 0, 2.5)])
    return {"plastic_black": body, "steel": bush.union(nut), "tin": lugs}


def usb_plug_90():
    """Right-angle micro-B plug, local: plug tip at the origin pointing +x,
    overmould going -x then turning down (-z)."""
    tongue = box(0, -3.5, -0.9, 6.0, 3.5, 0.9)
    over = box(-11.0, -5.5, -3.75, 0, 5.5, 3.75)
    over = over.edges("|Y").fillet(1.5)
    return {"steel": tongue, "plastic_black": over}


# ------------------------------------------------------------- fasteners
def screw(d, length, head_d, head_h):
    """Pan-head Phillips screw, local: under the head at z = 0, shank up +z,
    head below."""
    head = cyl(0, 0, -head_h, head_h, head_d).faces("<Z").edges().fillet(head_h * 0.45)
    head = head.cut(cbox(0, 0, -head_h - 0.1, head_d * 0.55, head_d * 0.14, head_h * 0.7)).cut(
        cbox(0, 0, -head_h - 0.1, head_d * 0.14, head_d * 0.55, head_h * 0.7))
    shank = cyl(0, 0, 0, length - 0.4, d).union(cq.Workplane().add(
        cq.Solid.makeCone(d / 2, d / 4, 0.4, cq.Vector(0, 0, length - 0.4))))
    # a hint of thread: shallow rings
    for i in range(int(length / (d * 0.45))):
        z = 0.6 + i * d * 0.45
        if z > length - 0.8:
            break
        shank = shank.cut(cyl(0, 0, z, d * 0.12, d + 1).cut(cyl(0, 0, z - 1, 3, d * 0.86)))
    return {"steel": head.union(shank)}


def nut(d, af, h):
    n = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h)
    return {"steel": n.cut(cyl(0, 0, -1, h + 2, d))}


def spacer_led():
    return {}


# ------------------------------------------------------------- export
def export(name, parts):
    os.makedirs(LIB, exist_ok=True)
    for mat, w in parts.items():
        cq.exporters.export(w, os.path.join(LIB, "%s.%s.stl" % (name, mat)), tolerance=0.02, angularTolerance=0.1)


def main():
    v = C.VERSIONS["seixo"]
    ctop = ENV["controls"]["top_z"]["seixo"]
    ct = ENV["controls"]
    led_stand = 3.9          # fit_check: Seixo LED spacer so the dome is flush in the lid hole
    lib = {
        "teensy": teensy(), "audio_board": audio_board(), "header": header(), "solder": solder_joints(),
        "gateron": gateron(), "pot": pot(), "encoder": encoder(), "knob": knob(), "led_seixo": led(led_stand),
        "led_madeira": led(0.0), "ph_plug": ph_plug(), "panel_usb": panel_usb(), "panel_jack": panel_jack(),
        "usb_plug_90": usb_plug_90(),
        "screw_m2x10": screw(2.0, 10.0, 3.8, 1.3), "screw_m2x5": screw(2.0, 5.0, 3.8, 1.3),
        "screw_m25x8": screw(2.5, 8.0, 4.8, 1.4), "nut_m2": nut(2.0, 4.0, 1.6),
    }
    for name, parts in lib.items():
        export(name, parts)
        print(name)

    inst = []

    def add(part, x, y_spec, z, group, rz=0.0, rx=0.0, ry=0.0, tag=None):
        inst.append({"part": part, "loc": [x, F(y_spec), z], "rot": [rx, ry, rz], "group": group, "tag": tag or part})

    # stack
    add("audio_board", AX0, AY1, Z_AB, "stack", tag="audio_board")
    add("teensy", CX, CY, Z_TEENSY, "stack", tag="teensy")
    for row in ROW_Y:
        add("header", PIN_X[0], row, Z_AB + BOARD_T, "stack", tag="header")
    add("solder", 0, C.WIDTH, 0, "stack", tag="solder")
    # switches
    for n, row, x, y, kind in C.keys():
        add("gateron", x, y, C.Z_PLATE_TOP, "switches", tag="switch")
    # controls board parts (board-top at ctop)
    add("pot", ct["pot"][0], ct["pot"][1], ctop, "controls", rz=ct["pot_rot"], tag="pot")
    add("encoder", ct["encoder"][0], ct["encoder"][1], ctop, "controls", rz=ct["encoder_rot"], tag="encoder")
    add("led_seixo", ct["led"][0], ct["led"][1], ctop, "controls", tag="led")
    for (x, y) in (C.VOLUME_XY, C.SELECT_XY):
        add("knob", x, y, C.z_interface(y) + 0.8, "knobs", tag="knob")
    # the 8-way cable's two plugs: into J1 (controls board's back, facing down) and J3 (main board top)
    jx, jy = ct["jst"]
    add("ph_plug", jx, jy - 1.35 + 2.4, ctop - ct["thickness"] - 6.0, "cable", tag="ph_plug_j1")
    j3 = j3_xy()
    add("ph_plug", j3[0] + 7.0, j3[1] + 1.0, C.Z_PCB_TOP + 6.0, "cable", rx=180, tag="ph_plug_j3")
    # panel parts behind the insert (fit_check: t = INSERT_WALL + 1.5)
    t = C.INSERT_WALL + 1.5
    add("panel_usb", t - 1.5, C.USB_YZ[0], C.USB_YZ[1], "panel", tag="panel_usb")
    add("panel_jack", t, C.JACK_YZ[0], C.JACK_YZ[1], "panel", tag="panel_jack")
    teensy_usb_x = CX - TEENSY[0] / 2 - 1.0
    add("usb_plug_90", teensy_usb_x - 6.0 + 0.5, CY, Z_TEENSY + BOARD_T + 1.3, "usb_cable", tag="usb_plug")
    # fasteners
    for x, y in C.SCREW_PILLARS:
        add("screw_m2x10", x, y, C.M2_HEAD_DEPTH, "board_screws", tag="m2x10")
        add("nut_m2", x, y, C.Z_PCB_TOP, "board_nuts", tag="nut_m2")
    for x, y in ct["holes"]:
        add("screw_m2x5", x, y, ctop - ct["thickness"], "controls_screws", tag="m2x5")
    for x, y in C.screw_points():
        add("screw_m25x8", x, y, C.HEAD_DEPTH, "case_screws", tag="m25x8")

    # cables as polylines (file frame); Blender sweeps them
    plug_j1 = (jx, F(jy + 1.05), ctop - ct["thickness"] - 12.0)
    plug_j3 = (j3[0] + 7.0, F(j3[1] + 1.0), C.Z_PCB_TOP + 12.0)
    cables = {
        "ph8": {"from": plug_j1, "to": plug_j3, "wires": 8, "pitch": 2.0, "d": 1.0, "group": "cable",
                "mid": [(jx - 3, F(jy - 2), plug_j1[2] - 3), (j3[0] + 9, F(j3[1] + 3), plug_j3[2] + 3)]},
        "usb": {"path": [(t + 10.0, F(C.USB_YZ[0]), C.USB_YZ[1]), (t + 15.0, F(C.USB_YZ[0] - 2), C.USB_YZ[1] - 1.0),
                         (teensy_usb_x - 14.0, F(CY + 3), Z_TEENSY + 2.0), (teensy_usb_x - 11.0, F(CY), Z_TEENSY + 2.9)],
                "d": 3.4, "group": "usb_cable"},
        "jack_wires": {"path": [(t + 13.0, F(C.JACK_YZ[0]), C.JACK_YZ[1]), (t + 17.0, F(C.JACK_YZ[0] - 4), C.JACK_YZ[1] - 3),
                                (AX0 + 4.0, F(AY1 - 1.0), Z_AB + 3.0), (AX0 + 6.0, F(AY1 - 2.0), Z_AB - 0.2)],
                       "d": 0.9, "wires": 3, "pitch": 1.1, "group": "panel"},
    }
    data = {"instances": inst, "cables": cables,
            "z": {"pcb_bot": C.Z_PCB_BOT, "pcb_top": C.Z_PCB_TOP, "plate_top": C.Z_PLATE_TOP,
                  "key_top": C.Z_KEY_TOP, "controls_top": ctop, "controls_t": ct["thickness"]},
            "stack_height": round(Z_TEENSY + BOARD_T + 2.6 - Z_AB, 2),
            "width": C.WIDTH}
    json.dump(data, open(os.path.join(BUILD, "assembly.json"), "w"), indent=1)
    json.dump([{"n": n, "row": r, "x": x, "y": y, "kind": k} for n, r, x, y, k in C.keys()],
              open(os.path.join(BUILD, "keys.json"), "w"))
    print("stack height %.1f mm, %d instances" % (data["stack_height"], len(inst)))


def j3_xy():
    import re
    s = open(os.path.join(HERE, "..", "kicad", "etuttino.kicad_pcb"), encoding="utf-8").read()
    i = s.index('"Reference" "J3"')
    head = s.rfind("(footprint", 0, i)
    m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", s[head:i])
    return float(m.group(1)), float(m.group(2))


if __name__ == "__main__":
    main()
