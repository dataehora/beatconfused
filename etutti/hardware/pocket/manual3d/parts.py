"""Component library and assembly for the Pocket's assembly-manual pictures.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe parts.py

Adapted from etutti/hardware/manual3d/parts.py (the eTuttino's, unchanged):
models the parts that have no KiCad 3D model, from their datasheet sizes
(PECAS.json; CHECK where a size is a guess), one STL per material, and
writes where every instance goes, the cables as polylines and the
placement of the three KiCad boards (SPEC v5: no panel board). Everything is in the case files'
frame (x right, y away from the player, z up, mm; y_file = 100 - y_spec),
so it lines up with ../case/out/*.stl.

Writes build/lib/<part>.<material>.stl and build/assembly.json.
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(POCKET, "case"))
import case as C  # noqa: E402  (the Pocket's case)
sys.modules.setdefault("case", C)
sys.path.insert(0, os.path.normpath(os.path.join(POCKET, "..", "case")))
import keycap as K  # noqa: E402  (the eTuttino's caps and switches, run on the Pocket's case module)

BUILD = os.path.join(HERE, "build")
LIB = os.path.join(BUILD, "lib")
W = C.WIDTH
F = lambda y: W - y      # SPEC y -> file y
ENV = json.load(open(os.path.join(C.OUT, "pcb_envelope.json")))
PECAS = json.load(open(os.path.join(POCKET, "pcb", "PECAS.json"), encoding="utf-8"))["parts"]


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


# ------------------------------------------------------------- stack (LOW: Teensy straight on the Audio Board)
BOARD_T = 1.6
TEENSY = (35.56, 17.78)
ST = ENV["stack"]
AX0, AY0, AX1, AY1 = ST["audio_board"]              # SPEC
ROW_Y = ST["pin_rows_y"]                            # SPEC: VIN row (back) first
PIN_X = [ST["pin1_x"] + i * ST["pin_pitch"] for i in range(ST["pins_per_row"])]
CX = (PIN_X[0] + PIN_X[-1]) / 2
CY = sum(ROW_Y) / 2
Z_AB = ST["z"]["audio_bottom"]                      # 10.7
Z_TEENSY = ST["z"]["teensy_top"] - BOARD_T          # 15.2
HEADER_PLASTIC = Z_TEENSY - (Z_AB + BOARD_T)        # 2.9: the header's plastic is the only spacer


def teensy():
    """Local: centre of the board, underside at z = 0, USB towards -x. The
    VUSB-VIN cut pads on the underside near the USB end (PJRC's drawing;
    position CHECK on the real board)."""
    w, d = TEENSY
    pcb = box(-w / 2, -d / 2, 0, w / 2, d / 2, BOARD_T)
    for x in PIN_X:
        for y in (-7.62, 7.62):
            pcb = pcb.cut(cyl(x - CX, y, -1, 4, 1.0))
    t = BOARD_T
    chips = union(cbox(2.5, 0, t, 10.0, 10.0, 1.1), cbox(-6.5, 3.6, t, 4.0, 3.0, 0.8),
                  cbox(-7.0, -4.0, t, 3.0, 3.0, 0.9), cbox(10.6, -3.4, t, 3.2, 2.5, 0.8))
    button = cbox(14.8, 0, t, 3.0, 4.0, 1.6)
    usb = cbox(-w / 2 + 2.4, 0, t, 5.6, 7.6, 2.6)
    usb = usb.cut(cbox(-w / 2 - 0.6, 0, t + 0.6, 2.0, 6.4, 1.4))
    led = cbox(-11.5, 6.6, t, 1.6, 0.8, 0.5)
    caps = union(*[cbox(x, y, t, 1.0, 0.5, 0.5) for x, y in ((8.6, 4.0), (8.6, -4.6), (-2.8, -6.6), (-3.8, 6.4),
                                                             (11.4, 2.2), (-10.4, -1.0))])
    return {"pcb_teensy": pcb, "chip": chips, "button": button, "steel": usb, "led_orange": led, "cap0402": caps}


def vusb_pads():
    """The two VUSB / VIN pads and the thin trace between them, under the
    Teensy (local as teensy(), z below 0)."""
    x0 = -TEENSY[0] / 2 + 6.2
    return {"tin": union(cbox(x0, -1.4, -0.05, 1.4, 1.2, 0.05), cbox(x0, 1.4, -0.05, 1.4, 1.2, 0.05),
                         cbox(x0, 0, -0.04, 0.35, 1.8, 0.04))}


def audio_board():
    """Local: the board's corner (SPEC x0, file y of its front edge),
    underside at z = 0; USB/jack end towards -x (as the eTuttino's)."""
    w, d = AX1 - AX0, AY1 - AY0
    pcb = box(0, 0, 0, w, d, BOARD_T)
    yrow = [F(r) - F(AY1) for r in ROW_Y]
    for x in PIN_X:
        for y in yrow:
            pcb = pcb.cut(cyl(x - AX0, y, -1, 4, 1.0))
    t = BOARD_T
    jy = F(CY + 7.62 + 7.2) - F(AY1)
    jack = cbox(6.5, jy, t, 13.0, 6.0, 5.1).union(cyl(-0.8, jy, t + 2.55, 1.0, 5.0, (1, 0, 0)))
    jack = jack.cut(cyl(-1.0, jy, t + 2.55, 6, 3.6, (1, 0, 0)))
    cy_l = F(CY) - F(AY1)
    codec = cbox(CX - AX0 - 1.0, F(CY + 14.0) - F(AY1), t, 3.0, 3.0, 0.9)
    reg = cbox(CX - AX0 + 9.0, F(CY + 13.0) - F(AY1), t, 2.9, 1.6, 1.1)
    caps = union(*[cbox(CX - AX0 + dx, F(CY + dy) - F(AY1), t, 1.6, 0.8, 0.8)
                   for dx, dy in ((-6, 12), (-6, 15.5), (4, 11.5), (4, 16.5), (13, 15.5), (15, 11.0))])
    sd = cbox(w - 8.0, cy_l, -1.8, 12.0, 11.5, 1.8)
    # the jack's three terminals under the board (L tip, R ring, VGND sleeve) -- CHECK on the Rev D
    legs = union(*[cbox(lx, jy + dy, -1.2, 1.0, 0.6, 1.2) for lx, dy in ((3.0, -2.2), (8.0, -2.2), (11.0, 2.2))])
    return {"pcb_audio": pcb, "chip": codec.union(reg), "plastic_black": jack, "cap0805": caps, "steel": sd, "tin": legs}


def jack_legs_xy():
    """Where the Audio Board jack's 3 terminals are (file frame, x, y)."""
    jy = F(CY + 7.62 + 7.2)
    return [(AX0 + lx, jy + dy) for lx, dy in ((3.0, -2.2), (8.0, -2.2), (11.0, 2.2))]


def header():
    """One 1x14 extra-long header, local: pin 1 at x = 0, plastic underside
    at z = 0 (on the Audio Board's top)."""
    n = ST["pins_per_row"]
    plastic = box(-1.27, -1.27, 0, (n - 1) * 2.54 + 1.27, 1.27, HEADER_PLASTIC)
    z_bot = C.Z_PCB_BOT - 0.8 - (Z_AB + BOARD_T)     # trimmed 0.8 under the main board
    z_top = HEADER_PLASTIC + BOARD_T + 1.4
    pins = union(*[box(i * 2.54 - 0.32, -0.32, z_bot, i * 2.54 + 0.32, 0.32, z_top) for i in range(n)])
    return {"plastic_black": plastic, "tin": pins}


def solder_joints():
    shapes = []
    for row in ROW_Y:
        for x in PIN_X:
            y = F(row)
            for z0, up in ((C.Z_PCB_BOT, False), (Z_AB, False), (Z_TEENSY + BOARD_T, True)):
                shapes.append(cq.Workplane().add(cq.Solid.makeCone(1.0, 0.35, 0.8, cq.Vector(x, y, z0),
                                                                   cq.Vector(0, 0, 1 if up else -1))))
    return {"tin": union(*shapes)}


def shim():
    """The temporary 3 mm shim between the main board and the Audio Board."""
    return {"shim": box(AX0 + 4, F(AY1 - 2), C.Z_PCB_TOP, AX1 - 4, F(AY1 - 8), C.Z_PCB_TOP + 3.0).union(
        box(AX0 + 4, F(AY0 + 8), C.Z_PCB_TOP, AX1 - 4, F(AY0 + 2), C.Z_PCB_TOP + 3.0))}


# ------------------------------------------------------------- keyboard
def gateron():
    zp = 0.0
    zb = -(C.Z_PLATE_TOP - C.Z_PCB_TOP)
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
    stem = cyl(0, 0, K.HOUSING_H, K.STEM_ABOVE * 0.4, 5.4).union(
        union(cbox(0, 0, K.HOUSING_H, 4.0, 1.17, K.STEM_ABOVE), cbox(0, 0, K.HOUSING_H, 1.17, 4.0, K.STEM_ABOVE)))
    return {"plastic_dark": bot.union(pegs).union(clips), "smoke": top, "stem": stem}


# ------------------------------------------------------------- controls
def pot_rk097():
    """Alps RK097 horizontal with switch, lying on its vertical board.
    Local: shaft axis = z, the body's top face (under the bushing) at z = 0,
    its board on the +x side at x = BODY_X (PECAS volume_pot; the case's
    POT_BODY: 15.8 along the shaft with the switch)."""
    bx0, by0, bx1, by1, bz0, bz1 = C.POT_BODY
    sx, sy = C.VOLUME_XY
    h = bz1 - bz0
    body = box(bx0 - sx, by0 - sy, -h, bx1 - sx, by1 - sy, 0)
    sw = box(bx0 - sx + 1.0, by0 - sy + 1.0, -h, bx1 - sx - 1.0, by1 - sy - 1.0, -h + 3.0)   # switch can at the back
    bush = cyl(0, 0, 0, 7.0, 7.0)
    shaft = cyl(0, 0, 7.0, 8.0, 6.0)                 # tip at z 45.3 (PECAS: L 15)
    legs = union(*[box(bx1 - sx, dy - 0.3, -h + zz, C.POT_LEGS_X - sx, dy + 0.3, -h + zz + 0.8)
                   for dy, zz in ((-2.5, 9.0), (0.0, 9.0), (2.5, 9.0), (-2.5, 2.0), (2.5, 2.0))])
    return {"steel": body.cut(sw), "plastic_black": sw, "brass": bush, "alu": shaft, "tin": legs}


def encoder():
    """Alps EC11E with switch, D6 shaft (L 25, cut to the knob), M7 bushing (PECAS encoder);
    local: board top at z = 0."""
    e = PECAS["encoder"]["body"]
    body = cbox(0, 0, 0, e["plan"][0], e["plan"][1], e["height_above_pcb"])
    base = cbox(0, 0, 0, e["plan"][0], e["plan"][1], 1.5)
    bush = cyl(0, 0, e["height_above_pcb"], 5.0, 7.0)
    L = min(e["shaft_l"], C.Z_IF + C.KNOB_LIFT + C.KNOB_H - 1.0 - C.CTRL_TOP)     # cut to the knob's bore (L 25 - 2.2)
    shaft = cyl(0, 0, e["height_above_pcb"] + 5.0, L - e["height_above_pcb"] - 5.0, 6.0).cut(
        box(1.5, -4, e["height_above_pcb"] + 10.0, 4, 4, L + 1))
    legs = union(*[cbox(dx, 7.5, -1.5, 0.8, 0.3, 1.5) for dx in (-2.5, 0, 2.5)],
                 *[cbox(dx, -7.0, -1.5, 0.8, 0.3, 1.5) for dx in (-2.5, 2.5)])
    return {"steel": body.cut(base), "plastic_black": base, "brass": bush, "alu": shaft, "tin": legs}


def knob():
    """The proposed knob (case.KNOB_*: D15 x 14, set screw, a cavity underneath
    for the thread left above the nut); local: underside at z = 0."""
    k = cyl(0, 0, 0, C.KNOB_H, C.KNOB_D)
    k = k.faces(">Z").edges().fillet(1.2)
    k = k.cut(cyl(0, 0, -1, C.KNOB_CAVITY[1] + 1, C.KNOB_CAVITY[0]))
    k = k.cut(cbox(0, 2.6, C.KNOB_H - 0.5, 0.8, 3.0, 1.0))                       # pointer line
    for i in range(30):
        a = 2 * math.pi * i / 30
        k = k.cut(cyl((C.KNOB_D / 2 + 0.15) * math.cos(a), (C.KNOB_D / 2 + 0.15) * math.sin(a), 1.0, C.KNOB_H - 2.5, 0.7))
    k = k.cut(cyl(0, 0, C.KNOB_H / 2, 10, 2.0, (1, 0, 0)))                          # set screw hole
    return {"knob": k}


def led(spacer):
    """3 mm red/green LED on its spacer; local: board top at z = 0."""
    return {"led_lens": cyl(0, 0, spacer + 1.0, 5.3 - 1.0 - 1.5, 3.0).union(
        cq.Workplane().add(cq.Solid.makeSphere(1.5, cq.Vector(0, 0, spacer + 3.8)))).union(cyl(0, 0, spacer, 1.0, 3.8)),
        "tin": union(*[cbox(dx, 0, -1.5, 0.45, 0.45, spacer + 1.5) for dx in (-2.54, 0, 2.54)]),
        "plastic_black": cyl(0, 0, 0, spacer, 4.5).cut(cyl(0, 0, -1, spacer + 2, 3.0))}


def nut_m7():
    n = cq.Workplane("XY").polygon(6, C.POT_NUT_AF / math.cos(math.pi / 6)).extrude(C.POT_NUT_T)
    return {"steel": n.cut(cyl(0, 0, -1, 4, 7.0))}


def nut_tool():
    """The printed nut driver (case/out/seixo_chave_porca), hex end down; local: z = 0 at its hex end."""
    return {"case_mjf": cq.Workplane().add(C.nut_tool())}


# ------------------------------------------------------------- the panel parts (SPEC v5: FPC micro-B + wired jack)
def placed(shape):
    """A case.py solid in SPEC coordinates -> the files' frame, as a Workplane."""
    return cq.Workplane().add(C.to_file(shape))


def fpc_female():
    """The FPC female head in its tunnel (case.female_solids) with the
    receptacle opening on its front, and the trava bar; file frame."""
    head, bar = C.female_solids()
    g = C.conn_geometry()
    hole = C.local_solid(cq.Solid.makeBox(1.5, 7.5, 2.6, cq.Vector(-0.5, -3.75, -1.3)), g["fem_origin"], g["n"], C.FEM_Z)
    tongue = C.local_solid(cq.Solid.makeBox(1.0, 5.0, 0.6, cq.Vector(0.2, -2.5, -0.3)), g["fem_origin"], g["n"], C.FEM_Z)
    return {"plastic_black": placed(head.cut(hole)), "steel": placed(tongue)}, {"case_mjf": placed(bar)}


def jack_cliff():
    """Cliff FC681375V (case.jack_solids): body + tabs, thread, ring nut outside; file frame."""
    body, thread, nut_ = C.jack_solids()
    g = C.conn_geometry()
    o = g["jack_origin"]
    bore = cq.Solid.makeCylinder(1.8, 8.0, cq.Vector(o[0] - 7.0, o[1], C.JACK_Z), cq.Vector(1, 0, 0))
    ring = nut_.cut(cq.Solid.makeCylinder(4.0, 4.0, cq.Vector(o[0] - 6.0, o[1], C.JACK_Z), cq.Vector(1, 0, 0)))
    ring = ring.cut(cq.Solid.makeBox(2.2, 1.0, 12.0, cq.Vector(o[0] - C.JACK_WALL - 2.1, o[1] - 0.5, C.JACK_Z - 6.0)))   # spanner slot
    return {"plastic_black": placed(body), "steel": placed(thread.cut(bore)).union(placed(ring))}


def ribbon_segments():
    """The FPC ribbon's centre line as (p0, p1, width direction) in SPEC
    coordinates: up from the plug's top, three flat layers over the Teensy
    (the spare of the 10 cm), back under the block, up at the block's end and
    into the trava's slot. Width ~10 (PECAS ~10-12), thickness 0.3."""
    rect, (pz0, pz1) = C.stack_parts()["usb_plug"]
    xc = (min(p[0] for p in rect) + max(p[0] for p in rect)) / 2
    yc = (min(p[1] for p in rect) + max(p[1] for p in rect)) / 2
    g = C.conn_geometry()
    o, n = g["fem_origin"], g["n"]
    t = (-n[1], n[0])
    e = C.FEM_POCKET[1] + C.TRAVA[1] + 1.2
    riser = (o[0] + n[0] * e, o[1] + n[1] * e)
    z0 = pz1 + 0.25
    segs = [((xc, yc, pz1), (xc, yc, z0), (0, 1, 0)),
            ((xc, yc, z0), (46.0, yc, z0), (0, 1, 0)),
            ((46.0, yc, z0 + 0.5), (33.0, yc, z0 + 0.5), (0, 1, 0)),
            ((33.0, yc, z0 + 1.0), (45.0, yc, z0 + 1.0), (0, 1, 0)),
            ((45.0, yc, z0 + 1.5), (riser[0] + 2.0, yc, z0 + 1.5), (0, 1, 0)),
            ((riser[0] + 2.0, yc, z0 + 1.5), (riser[0], riser[1], z0 + 1.5), (1, 0, 0)),
            ((riser[0], riser[1], z0 + 1.5), (riser[0], riser[1], C.FEM_Z), (t[0], t[1], 0)),
            ((riser[0], riser[1], C.FEM_Z), (o[0] + n[0] * (C.FEM_HEAD[1] - 0.5), o[1] + n[1] * (C.FEM_HEAD[1] - 0.5), C.FEM_Z), (t[0], t[1], 0))]
    return segs


def ribbon(width=10.0, thick=0.3):
    out = None
    for p0, p1, wd in ribbon_segments():
        a, b = cq.Vector(*p0), cq.Vector(*p1)
        d = b - a
        L = d.Length
        if L < 1e-6:
            continue
        u = d.normalized()
        w = cq.Vector(*wd).normalized()
        th = u.cross(w).normalized()
        # a box along u, width w, thickness th, centred on the segment (plus overlap at the joints)
        corner = a - u * 0.6 - w * (width / 2) - th * (thick / 2)
        pl = cq.Plane(origin=corner, xDir=u, normal=th)
        bx = cq.Workplane(pl).rect(L + 1.2, width, centered=False).extrude(thick).val()
        bx = C.to_file(bx)
        out = cq.Workplane().add(bx) if out is None else out.union(cq.Workplane().add(bx))
    return {"fpc": out}


def plug_up():
    """The 'UP' 90 deg micro-B male in the Teensy (PECAS male_90: ~11 x 8.5 x 5.5,
    conferir), tip into the Teensy's socket, ribbon out of its top."""
    rect, (pz0, pz1) = C.stack_parts()["usb_plug"]
    x0, x1 = min(p[0] for p in rect), max(p[0] for p in rect)
    yc = (min(p[1] for p in rect) + max(p[1] for p in rect)) / 2
    zc = (pz0 + pz1) / 2
    over = C.box3(x1 - 11.0, yc - 4.25, zc - 2.75, x1, yc + 4.25, pz1)
    tongue = C.box3(x1, yc - 3.4, zc - 0.9, x1 + 6.0, yc + 3.4, zc + 0.9)
    return {"plastic_black": placed(over), "steel": placed(tongue)}


# ------------------------------------------------------------- connectors, battery, speaker
def ph_mated():
    """The battery's PHR-3 (right) mated with the pigtail's in-line male
    (left), lying flat; local: centre, bottom at z = 0, axis x."""
    m = PECAS["battery"]["connector_pocket_v4"]["parts"]["mated"]["dims_wxhxl"]
    w, h, L = m
    phr = box(0, -w / 2, 0, 6.0, w / 2, h)
    male = box(-L + 6.0, -w / 2 + 0.2, 0.1, 0, w / 2 - 0.2, h - 0.1)
    return {"plastic_white": phr.translate((L / 2 - 6.0, 0, 0)), "plastic_dark": male.translate((L / 2 - 6.0, 0, 0))}


def ph_plug(n):
    """PHR-n housing on a board header (plugged in, wires up); local: centre, board top at z = 0."""
    L = 2.0 * (n - 1) + 3.9
    return {"plastic_white": cbox(0, 0.3, 4.0, L - 0.4, 3.6, 6.5)}      # the header itself comes with the KiCad board


def battery():
    """LiPo 603450 with PCM and NTC (PECAS battery): cell + PCM end at -x.
    Local: centre of the 58 x 36 footprint, bottom at z = 0."""
    t, wd, L = PECAS["battery"]["body"]["with_pcm_and_wire_fold"]
    cell = box(-L / 2 + 6.0, -wd / 2, 0, L / 2, wd / 2, t - 0.6).edges("|X").fillet(1.2)
    pcm = box(-L / 2, -wd / 2 + 2, 0.3, -L / 2 + 6.0, wd / 2 - 2, t - 1.2)
    return {"lipo": cell, "kapton": pcm}


def foam(L, Wd, t):
    return {"foam": box(-L / 2, -Wd / 2, 0, L / 2, Wd / 2, t)}


def speaker():
    """CLS0361-L152: face (rim) at z = 0, body towards -z."""
    b = PECAS["speaker"]["body"]
    d, depth, fh, md = b["frame_d"], b["total_depth"], b["frame_height"], b["magnet_d"]
    frame = cyl(0, 0, -fh, fh, d).cut(cyl(0, 0, -fh - 1, fh + 2, d - 3.0))
    cone = cq.Workplane().add(cq.Solid.makeCone((d - 3.0) / 2, 7.0, fh - 0.6, cq.Vector(0, 0, -fh + 0.0)))
    cone = cone.cut(cq.Workplane().add(cq.Solid.makeCone((d - 3.4) / 2, 6.6, fh - 0.6, cq.Vector(0, 0, -fh + 0.4))))
    magnet = cyl(0, 0, -depth, depth - fh + 0.4, md)
    dome = cq.Workplane().add(cq.Solid.makeSphere(4.5, cq.Vector(0, 0, -4.2))).intersect(cyl(0, 0, -0.9, 0.85, 12))
    return {"steel": frame.union(magnet), "paper": cone, "plastic_black": dome}


def gasket():
    d = PECAS["speaker"]["body"]["frame_d"]
    return {"foam": cyl(0, 0, 0, C.GASKET_T, d).cut(cyl(0, 0, -1, 3, d - 4.0))}


# ------------------------------------------------------------- fasteners
def screw(d, length, head_d, head_h, csk=False):
    """Under the head at z = 0, shank up +z, head below."""
    if csk:
        head = cq.Workplane().add(cq.Solid.makeCone(head_d / 2, d / 2, head_h, cq.Vector(0, 0, -head_h)))
    else:
        head = cyl(0, 0, -head_h, head_h, head_d).faces("<Z").edges().fillet(head_h * 0.45)
    head = head.cut(cbox(0, 0, -head_h - 0.1, head_d * 0.55, head_d * 0.14, head_h * 0.7)).cut(
        cbox(0, 0, -head_h - 0.1, head_d * 0.14, head_d * 0.55, head_h * 0.7))
    shank = cyl(0, 0, 0, length - (head_h if csk else 0) - 0.4, d).union(cq.Workplane().add(
        cq.Solid.makeCone(d / 2, d / 4, 0.4, cq.Vector(0, 0, length - (head_h if csk else 0) - 0.4))))
    return {"steel": head.union(shank)}


def nut(d, af, h):
    n = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h)
    return {"steel": n.cut(cyl(0, 0, -1, h + 2, d))}


# ------------------------------------------------------------- export
def export(name, parts):
    os.makedirs(LIB, exist_ok=True)
    for mat, w in parts.items():
        cq.exporters.export(w, os.path.join(LIB, "%s.%s.stl" % (name, mat)), tolerance=0.02, angularTolerance=0.1)


def mat4(cols, t):
    """4x4 row-major from three column vectors and a translation (mm)."""
    return [[cols[0][i], cols[1][i], cols[2][i], t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def main():
    ct = ENV["controls"]
    lib = {
        "teensy": teensy(), "vusb_pads": vusb_pads(), "audio_board": audio_board(), "header": header(),
        "solder": solder_joints(), "shim": shim(), "gateron": gateron(), "pot": pot_rk097(), "encoder": encoder(),
        "knob": knob(), "led": led(C.Z_IF - 0.5 - 5.3 - C.CTRL_TOP), "nut_m7": nut_m7(), "nut_tool": nut_tool(),
        "fpc_female": fpc_female()[0], "trava": fpc_female()[1], "jack_cliff": jack_cliff(), "fpc_ribbon": ribbon(),
        "plug_up": plug_up(), "ph_mated": ph_mated(), "ph3": ph_plug(3), "ph2": ph_plug(2),
        "battery": battery(), "batt_foam": foam(54.0, 32.0, 1.0), "speaker": speaker(), "gasket": gasket(),
        "screw_m25x8": screw(2.5, 8.0, 5.0, 1.4, csk=True), "screw_m2x10": screw(2.0, 10.0, 3.8, 1.3),
        "screw_m2x5": screw(2.0, 5.0, 3.8, 1.3),
        "screw_m2x6_csk": screw(2.0, 6.0, 4.0, 1.1, csk=True), "nut_m2": nut(2.0, 4.0, 1.6),
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
    add("vusb_pads", CX, CY, Z_TEENSY, "vusb", tag="vusb")
    for row in ROW_Y:
        add("header", PIN_X[0], row, Z_AB + BOARD_T, "stack", tag="header")
    add("solder", 0, W, 0, "stack", tag="solder")
    add("shim", 0, W, 0, "shim", tag="shim")
    # keyboard
    for n, row, x, y, kind in C.keys():
        add("gateron", x, y, C.Z_PLATE_TOP, "switches", tag="switch")
    # controls
    sx, sy = C.VOLUME_XY
    add("pot", sx, sy, C.POT_BODY[5], "pot", tag="pot")
    add("nut_m7", sx, sy, C.Z_IF - C.POT_NUT_T, "pot_nut", tag="pot_nut")          # flush in its recess (SPEC v5)
    add("nut_tool", sx, sy, C.Z_IF - C.POT_NUT_T + 0.2, "nut_tool", tag="nut_tool")
    add("encoder", C.SELECT_XY[0], C.SELECT_XY[1], C.CTRL_TOP, "encoder", tag="encoder")
    add("led", C.LED_XY[0], C.LED_XY[1], C.CTRL_TOP, "led", tag="led")
    for (x, y), z0 in ((C.VOLUME_XY, C.Z_IF + C.KNOB_LIFT), (C.SELECT_XY, C.Z_IF + C.KNOB_LIFT)):
        add("knob", x, y, z0, "knobs", tag="knob")
    # the panel parts (file frame already): FPC female + trava, the jack, the UP plug and the ribbon
    add("fpc_female", 0, W, 0, "fpc_female", tag="fpc_female")
    add("trava", 0, W, 0, "trava", tag="trava")
    add("jack_cliff", 0, W, 0, "jack", tag="jack")
    add("plug_up", 0, W, 0, "fpc_plug", tag="plug_up")
    add("fpc_ribbon", 0, W, 0, "fpc_ribbon", tag="fpc_ribbon")
    g = C.conn_geometry()
    fo, fn = g["fem_origin"], g["n"]
    ft = (-fn[1], fn[0])
    for sgn in (-1, 1):
        q = (fo[0] + fn[0] * (C.FEM_POCKET[1] + C.TRAVA[1]) + ft[0] * sgn * C.FEM_SCREWS[0] / 2,
             fo[1] + fn[1] * (C.FEM_POCKET[1] + C.TRAVA[1]) + ft[1] * sgn * C.FEM_SCREWS[0] / 2)
        rz_s = math.degrees(math.atan2(-fn[1], fn[0]))
        # screw along -n (into the block's end face): head on the trava, shank towards the wall
        inst.append({"part": "screw_m2x5", "loc": [q[0], F(q[1]), C.FEM_Z], "rot": [0, -90, rz_s], "group": "trava_screws",
                     "tag": "m2x5t"})
    # main-board headers with their plugs: J_BAT (rot 270: pins along y), J_SPK
    for it in PECAS["main_board_connectors"]["items"]:
        if it["ref"] == "J_BAT":
            add("ph3", it["at"][0] - 0.55, it["at"][1] + 2.0, C.Z_PCB_TOP, "plugs", rz=90, tag="plug_bat")
        if it["ref"] == "J_SPK":
            add("ph2", it["at"][0] + 1.0, it["at"][1], C.Z_PCB_TOP, "plugs", tag="plug_spk")
    # battery, its plug pair in the pocket, the foam
    add("battery", C.BATT_C[0], C.BATT_C[1], C.BATT_Z[0] + 1.0, "battery", tag="battery")
    add("batt_foam", C.BATT_C[0], C.BATT_C[1], C.BATT_Z[0], "battery", tag="batt_foam")
    x0, x1, y0 = C.BATT_POCKET
    py1 = C.BATT_C[1] - C.BATT_IN[1] / 2
    add("ph_mated", (x0 + x1) / 2, (y0 + py1) / 2, C.BATT_Z[0], "pigtail", tag="ph_mated")
    # speaker, tilted with the lid (its axis leans towards the player: -y in the files)
    zf = C.speaker_face_z(C.SPK_C[1])
    add("speaker", C.SPK_C[0], C.SPK_C[1], zf, "speaker", rx=C.IF_SLOPE, tag="speaker")
    add("gasket", C.SPK_C[0], C.SPK_C[1], zf, "gasket", rx=C.IF_SLOPE, tag="gasket")
    # fasteners
    for x, y in C.screw_points():
        add("screw_m25x8", x, y, C.HEAD_DEPTH, "case_screws", tag="m25x8")
    for x, y in C.BOARD_SCREWS:
        add("screw_m2x10", x, y, C.M2_HEAD_DEPTH, "board_screws", tag="m2x10")
        add("nut_m2", x, y, C.Z_PCB_TOP, "board_nuts", tag="nut_m2")
    for x, y in C.CTRL_POSTS:
        add("screw_m2x5", x, y, C.CTRL_TOP - C.CTRL_T, "ctrl_screws", tag="m2x5")
    for x, y in C.HATCH_SCREWS:
        add("screw_m2x6_csk", x, y, 1.1, "hatch_screws", tag="m2x6csk")

    # ---------------------------------------------------------------- KiCad boards: placement (file frame, mm)
    boards = {
        "main": {"glb": "pocket.glb", "group": "board", "matrix": mat4([(1, 0, 0), (0, 1, 0), (0, 0, 1)], (0, W, C.Z_PCB_BOT)),
                 "own_groups": {"J_BAT": "jbat", "J_SPK": "jspk", "J_CTL": "board", "J_HP": "board", "J_VBUS": "jvbus",
                                "J_JACK": "jjack"},
                 "hide": ["J1", "J2"]},
        "controls": {"glb": "pocket_controls.glb", "group": "ctrl_board",
                     "matrix": mat4([(1, 0, 0), (0, 1, 0), (0, 0, 1)], (0, W, C.CTRL_TOP - C.CTRL_T)), "hide": ["D1"]},
    }
    # the pot board stands in the y-z plane at x 21.62-23.22, its parts side (F) towards -x.
    # glb local (gx = X, gy = -Y, gz = up through the board); a proper rotation:
    # file x = 23.22 - gz, file y = F(43) - ... (X runs towards the player), file z = 29.8 + gy
    pb = ct["pot"]
    bx1, by0, by1 = pb["board"][2], pb["board"][1], pb["board"][3]
    ztop = pb["board_z"][1]
    boards["pot"] = {"glb": "pocket_pot.glb", "group": "pot_board",
                     "matrix": mat4([(0, -1, 0), (0, 0, 1), (-1, 0, 0)], (bx1, F(by0), ztop))}
    # ---------------------------------------------------------------- cables (file frame polylines)
    P = lambda x, y, z: (x, F(y), z)
    zt = C.Z_PCB_TOP
    jbat = [it for it in PECAS["main_board_connectors"]["items"] if it["ref"] == "J_BAT"][0]["at"]
    jspk = [it for it in PECAS["main_board_connectors"]["items"] if it["ref"] == "J_SPK"][0]["at"]
    jvbus, jjack = (18.5, 18.0), (18.5, 28.6)          # build_pocket_pcb.py (J_JACK: 1x4 along +y)
    jctl = [it for it in PECAS["main_board_connectors"]["items"] if it["ref"] == "J_CTL"][0]["at"]
    jhp = [it for it in PECAS["main_board_connectors"]["items"] if it["ref"] == "J_HP"][0]["at"]
    cables = []

    def cab(name, pts, d, mat, group):
        cables.append({"name": name, "pts": [list(p) for p in pts], "d": d, "mat": mat, "group": group})
    # VBUS wire (26 AWG): the Teensy's VUSB pad -> J_VBUS (case.vusb_wire_path)
    cab("vusb_w", [P(x, y, z) for x, y, z in C.vusb_wire_path()], 1.1, "wire1", "vusb_wire")
    # the jack's 4 wires: tabs (back face) -> J_JACK 1-4 (T, R, S, tip switch)
    jo = g["jack_origin"]
    xb = jo[0] + C.JACK_BODY[2] + C.JACK_TABS
    for i, (dy, dz, mat) in enumerate(((-2.0, 2.0, "wire5"), (2.0, 2.0, "wire4"), (-2.0, -2.0, "wire6"), (2.0, -2.0, "wire3"))):
        pad = (jjack[0], jjack[1] + 2.54 * i)
        cab("jack_w%d" % i, [P(xb - 0.5, jo[1] + dy, C.JACK_Z + dz), P(xb + 2.5, jo[1] + dy, C.JACK_Z + dz - 1.0),
                            P(xb + 2.0, jo[1] - 3.0 + 0.6 * i, 16.0), P(pad[0] + 1.5, pad[1], zt + 4.0), P(pad[0], pad[1], zt + 0.3)],
            0.7, mat, "jack_wires")
    # a paper clip into the Teensy's program-button pinhole (step 9)
    bx, by = C.teensy_button_xy()
    cab("clip", [P(bx + 18.0, by - 6.0, C.Z_IF + 16.0), P(bx + 6.0, by - 2.0, C.Z_IF + 14.0), P(bx, by, C.Z_IF + 9.0),
                 P(bx, by, C.Z_TEENSY_PARTS + 0.6)], 0.9, "clip", "clip")
    # SH-10 controls cable: J_CTL up the cable zone; 6-10 to the controls board's right edge, 1-5 over the encoder to the pot board
    for i in range(10):
        k = i + 1
        mat = "wire%d" % (i % 8)
        base = [P(jctl[0] + (i - 4.5) * 0.5, jctl[1], zt + 6.0), P(54.0, 44.5, 20.0)]
        if k >= 6:
            yk = 45.1 + 1.9 * (k - 6)
            pts = base + [P(52.0, yk, C.CTRL_TOP + 1.5), P(C.CTRL_BOARD[2] - 1.3, yk, C.CTRL_TOP + 0.2)]
        else:
            Xw = {5: 1.2, 1: 3.4, 2: 5.6, 3: 7.8, 4: 10.0}[k]
            yw = by0 + Xw            # pot board v0.2: y = 43 + X
            pts = base + [P(50.0, 46.0, 28.6), P(30.0, yw, 28.8), P(bx1 + 0.3, yw, ztop - 1.2)]
        cab("ctl_w%d" % k, pts, 0.6, mat, "ctl_cable")
    # speaker wires: out of the box's hole, over the bay's roof, to J_SPK
    sw = ENV["speaker"]["wire_hole"]
    for i, mat in enumerate(("wire1", "wire0")):
        o_ = (i - 0.5) * 0.9
        cab("spk_w%d" % i, [P(sw["xy"][0] - 3, sw["xy"][1] + o_, sw["z"]), P(sw["xy"][0] + 2, sw["xy"][1] + o_, sw["z"]),
                            P(66.0, 55.0 + o_, 13.5), P(50.0, 44.0 + o_, 13.0), P(26.0, 39.0 + o_, 13.0),
                            P(18.0, 30.0 + o_, 14.0), P(jspk[0] + 1.0 + o_, jspk[1], zt + 7.0)], 0.7, mat, "spk_wires")
    # battery pigtail: J_BAT's plug, forward and down through the way-in slot into the pocket (male end at the left)
    sl = ENV["battery"]["pigtail_way_in"]["rect"]
    pm = ((x0 + x1) / 2 - 6.25, (y0 + py1) / 2)
    for i, mat in enumerate(("wire1", "wire3", "wire0")):
        o_ = (i - 1) * 0.9
        cab("pig_w%d" % i, [P(jbat[0] + o_, jbat[1] + 2.0, zt + 9.0), P(jbat[0] + o_, jbat[1] + 2.0, zt + 13.0),
                            P(12.5 + o_, 38.0, 16.0), P(12.5 + o_, (sl[1] + sl[3]) / 2, 9.5),
                            P(pm[0] - 2.5, pm[1] + o_, 5.0), P(pm[0], pm[1] + o_, 4.4)], 0.7, mat, "pigtail")
    # the battery's own wires: from its PCM end (left) back into the pocket, into the PHR-3's right end
    for i, mat in enumerate(("wire1", "wire3", "wire0")):
        o_ = (i - 1) * 0.9
        bl = C.BATT_C[0] - C.BATT_IN[0] / 2
        cab("bat_w%d" % i, [P(bl + 1.0, C.BATT_C[1] - 8 + o_ * 2, 5.0), P(bl + 4.0, py1 + 3.0 + o_, 5.5),
                            P(x1 - 1.0, py1 - 1.0 + o_, 5.0), P(pm[0] + 12.5, pm[1] + o_, 4.4)], 0.7, mat, "battery")
    # headphone wires: from the Audio Board jack's terminals (underside) down to the J_HP pads
    for i, ((lx, ly), mat) in enumerate(zip(jack_legs_xy(), ("wire1", "wire5", "wire0"))):
        cab("hp_w%d" % i, [(lx, ly, Z_AB - 1.0), (lx + 1.0, ly - 1.0, Z_AB - 1.8), (jhp[0] - 2.54 + 2.54 * i, F(jhp[1]) + 2.0, zt + 1.6),
                           (jhp[0] - 2.54 + 2.54 * i, F(jhp[1]), zt + 0.2)], 0.6, mat, "hp_wires")

    data = {"instances": inst, "cables": cables, "boards": boards,
            "z": {"pcb_bot": C.Z_PCB_BOT, "pcb_top": C.Z_PCB_TOP, "plate_top": C.Z_PLATE_TOP, "key_top": C.Z_KEY_TOP,
                  "controls_top": C.CTRL_TOP, "interface": C.Z_IF, "fem_z": C.FEM_Z, "jack_z": C.JACK_Z, "ab": Z_AB,
                  "teensy_top": Z_TEENSY + BOARD_T},
            "stack_height": round(Z_TEENSY + BOARD_T + 2.6 - Z_AB, 2), "width": W,
            "points": {
                "teensy_c": [CX, F(CY)], "teensy_3v": [PIN_X[2], F(ROW_Y[0])], "jbat": [jbat[0], F(jbat[1])],
                "jspk": [jspk[0], F(jspk[1])], "jvbus": [jvbus[0], F(jvbus[1])], "jctl": [jctl[0], F(jctl[1])],
                "jjack": [jjack[0], F(jjack[1])], "jjack3": [jjack[0], F(jjack[1] + 2 * 2.54)],
                "jhp": [jhp[0], F(jhp[1])], "teensy_vin": [PIN_X[0], F(ROW_Y[0])],
                "fem": [fo[0], F(fo[1])], "fem_in": [fo[0] + fn[0] * 5.0, F(fo[1] + fn[1] * 5.0)],
                "trava": [fo[0] + fn[0] * (C.FEM_POCKET[1] + C.TRAVA[1]), F(fo[1] + fn[1] * (C.FEM_POCKET[1] + C.TRAVA[1]))],
                "fem_n": [fn[0], -fn[1]], "jack": [g["jack_origin"][0], F(g["jack_origin"][1])],
                "plug": [(min(p[0] for p in C.stack_parts()["usb_plug"][0]) + max(p[0] for p in C.stack_parts()["usb_plug"][0])) / 2,
                         F(sum(p[1] for p in C.stack_parts()["usb_plug"][0]) / 4)],
                "button": [C.teensy_button_xy()[0], F(C.teensy_button_xy()[1])],
                "pot": list(C.VOLUME_XY[:1]) + [F(C.VOLUME_XY[1])],
                "encoder": [C.SELECT_XY[0], F(C.SELECT_XY[1])], "led": [C.LED_XY[0], F(C.LED_XY[1])],
                "spk": [C.SPK_C[0], F(C.SPK_C[1])], "batt": [C.BATT_C[0], F(C.BATT_C[1])],
                "pocket": [(x0 + x1) / 2, F((y0 + py1) / 2)], "spk_hole": [sw["xy"][0], F(sw["xy"][1])],
                "jw4": [bx1 + 0.3, F(by0 + 10.0)], "ctrl_posts": [[x, F(y)] for x, y in C.CTRL_POSTS],
                "board_screws": [[x, F(y)] for x, y in C.BOARD_SCREWS], "hatch_screws": [[x, F(y)] for x, y in C.HATCH_SCREWS],
                "joint": [C.CTRL_BOARD[0] + 0.5, F(46.4)],
            }}
    os.makedirs(BUILD, exist_ok=True)
    json.dump(data, open(os.path.join(BUILD, "assembly.json"), "w"), indent=1)
    json.dump([{"n": n, "row": r, "x": x, "y": y, "kind": k} for n, r, x, y, k in C.keys()],
              open(os.path.join(BUILD, "keys.json"), "w"))
    print("stack height %.1f mm, %d instances, %d cables" % (data["stack_height"], len(inst), len(cables)))


if __name__ == "__main__":
    main()
