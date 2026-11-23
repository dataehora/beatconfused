"""R11V4 item 1: the REAL OLED, in plain Python (no CadQuery): Adafruit product 326, "Monochrome 0.96 in 128x64 OLED Graphic Display - STEMMA QT" (SSD1306, 3.3 V, I2C).

Every number below was read from Adafruit's published board file (github.com/adafruit/Adafruit-128x64-Monochrome-OLED-PCB, "Adafruit 0.96in 128x64 OLED STEMMA QT.brd",
Eagle XML: outline, 2.5 mm plated holes, JST_SH4 positions and the package of the Univision UG-2864HSWEG01 panel) and cross-checked with the fabrication print on the
Adafruit Learn page and the shop page (thickness 6.2 mm, holes 24 mm apart). Board frame (xb, yb): the Eagle TOP view = the module's BACK (components) side,
origin at the lower-left corner of the outline; yb grows towards the unpopulated 8-pin header.

NOT in any drawing (assumed, to be measured on the real module, FIT_CHECK R11V4 risk list): PCB thickness 1.6 and glass + tape 1.5 (they add to the shop's 6.2 mm
total with the 3.1 mm of the SH4 connectors: 1.5 + 1.6 + 3.1 = 6.2), the position tolerance of the panel on the board.

Orientation chosen for the instrument ("B"): glass up, the header edge towards +y (the player), the display rotated 180 degrees in firmware (SSD1306 remap: free).
World = (WX0 + xb, WY0 + yb) with the VIEWING AREA centred on the lid's window (centre 37; 22).
"""
import math

# ---- published numbers (mm)
W_B, H_B = 29.21, 31.75                          # board: 1.15 x 1.25 in, with the two lugs at the bottom edge (yb 0..5.08)
HOLES_B = [(2.54, 2.54), (26.67, 2.54), (2.54, 29.21), (26.67, 29.21)]     # four plated holes: drill 2.5, pad 3.2 (24.13 x 26.67 apart)
HOLE_D, PAD_D = 2.5, 3.2
GLASS_X, GLASS_Y = (14.605 - 13.35, 14.605 + 13.35), (12.573 - 4.9 + 0.0, 12.573 + 14.36)   # glass 26.7 x 19.26: xb 1.255..27.955, yb 7.673..26.933 (panel placed MR0 at 14.605; 12.573)
ACT_X, ACT_Y = (14.605 - 10.872, 14.605 + 10.872), (12.573 + 1.396, 12.573 + 12.26)         # viewing area 21.744 x 10.864: yb 13.969..24.833
ACT_C = ((ACT_X[0] + ACT_X[1]) / 2, (ACT_Y[0] + ACT_Y[1]) / 2)                              # (14.605, 19.401): 2.098 above the glass centre (the FPC is at the glass's low-yb end)
CONN_YB = 16.51                                  # the two JST_SH4 (STEMMA QT) on the BACK side, one at each side edge, mouths facing outwards
CONN_L = ((2.54, "left"), (26.67, "right"))      # origin xb of each connector (mouth towards -xb for the left one, +xb for the right one)
CONN_BODY_DEPTH, CONN_BODY_W = 4.25, 6.1         # body from the footprint's tDocu box (-2.086..2.164 along the mating axis, 6.1 wide)
CONN_H = 3.1                                     # height under the PCB (derived from the 6.2 mm total, see above)
PLUG_W, PLUG_D, PLUG_H = 5.0, 2.45, 3.6          # SHR-04V-S plug: 4 positions = 3 x 1.0 + 2.0 wide (the 6-way plug is 7.0)

# ---- stack (z, from the lid): glass 0.1 under the ceiling, as in R10V4
PCB_T, GLASS_T_TOTAL = 1.6, 1.5                  # PCB, panel + foam tape over the PCB's front face
POST_D, PT_PILOT = 4.2, 1.75                     # lid posts on the 4 holes (D4.2: 0.18 mm from the glass edge at the upper holes); PT 2.0 pilot

# ---- placement in the instrument
WINDOW_C = (37.0, 22.0)                          # the lid's window 24 x 13 (x 25..49, y 15.5..28.5)
WX0, WY0 = WINDOW_C[0] - ACT_C[0], WINDOW_C[1] - ACT_C[1]      # world = (WX0 + xb, WY0 + yb) for orientation B: 22.395, 2.599


def world(xb, yb):
    return (WX0 + xb, WY0 + yb)


def levels(ceiling):
    glass_top = ceiling - 0.1
    pcb_top = glass_top - GLASS_T_TOTAL
    return {"glass_top": glass_top, "pcb_top": pcb_top, "pcb_bottom": pcb_top - PCB_T, "back_bottom": pcb_top - PCB_T - CONN_H}


def outline_b(n=14):
    """The board's outline in (xb, yb): rectangle 29.21 x 31.75 with R2.54 upper corners, the notch between the lugs (x 5.08..24.13 above yb 5.08)."""
    r = 2.54
    pts = []

    def arc(cx, cy, a0, a1):
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += arc(2.54, 2.54, 180, 360)                                  # left lug (semicircle, bottom)
    pts += [(5.08, 5.08), (24.13, 5.08)]
    pts += arc(26.67, 2.54, 180, 360)                                 # right lug
    pts += arc(26.67, 29.21, 0, 90)                                   # upper right corner
    pts += arc(2.54, 29.21, 90, 180)                                  # upper left corner
    return pts


def conn_boxes_b():
    """Each SH4 body and its plug, as boxes in (xb0, xb1, yb0, yb1, dz0, dz1) with dz measured from the PCB's BOTTOM face (negative = below it)."""
    out = []
    axis = -CONN_H / 2.0
    for x0, side in CONN_L:
        s = -1.0 if side == "left" else 1.0                  # direction of the mouth along xb
        # footprint: along the mating axis the body goes from -2.086 (mouth side) to +2.164 (pads side)
        mouth = x0 + s * 2.086
        back = x0 - s * 2.164
        out.append(("corpo " + side, min(mouth, back), max(mouth, back), CONN_YB - CONN_BODY_W / 2, CONN_YB + CONN_BODY_W / 2, -CONN_H, 0.0))
        p0, p1 = mouth, mouth + s * PLUG_D
        out.append(("plugue " + side, min(p0, p1), max(p0, p1), CONN_YB - PLUG_W / 2, CONN_YB + PLUG_W / 2, axis - PLUG_H / 2, min(axis + PLUG_H / 2, 0.0)))   # the plug's top is clipped at the PCB's lower face (the 0.45 mm overhang of the board edge)
    return out


def plug_exit_world():
    """Where the cable's wires leave the RIGHT-hand plug (orientation B: the right-hand connector is the module's xb 26.67 one): (x, y, z below the PCB bottom)."""
    mouth = 26.67 + 2.086
    return world(mouth + PLUG_D, CONN_YB) + (-CONN_H / 2.0,)


def cable_path_xz(r=3.0, x_drop=50.0, n=24):
    """Centre line (x, z) of the Qwiic cable's wires from the right-hand plug's exit to the main board's slit (R10V4 slit x 44.45..51.45, kept): an S -- a 180 degree turn of
    radius r (out +x, down, back -x), a short run, a 90 degree bend of radius r down through the slit at x_drop. z is absolute (0 = the main board's top)."""
    ex, ey, ez = plug_exit_world()
    z0 = levels(12.6)["pcb_bottom"] + ez                     # the plug's axis
    pts = [(ex, z0)]
    cx, cz = ex, z0 - r
    for i in range(1, n + 1):                                # clockwise from the top of the circle to the bottom
        t = math.pi / 2 - math.pi * i / n
        pts.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    xc = x_drop + r                                          # centre of the second bend (heading -x at its top)
    pts.append((xc, cz - r))
    cz2 = cz - r - r
    for i in range(1, n + 1):
        t = math.pi / 2 + (math.pi / 2) * i / n
        pts.append((xc + r * math.cos(t), cz2 + r * math.sin(t)))
    pts.append((x_drop, -3.2))
    return pts


def cable_length(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def holes_world():
    return [world(x, y) for x, y in HOLES_B]


def summary(ceiling=12.6):
    lv = levels(ceiling)
    gx0, gy0 = world(GLASS_X[0], GLASS_Y[0])
    gx1, gy1 = world(GLASS_X[1], GLASS_Y[1])
    ax0, ay0 = world(ACT_X[0], ACT_Y[0])
    ax1, ay1 = world(ACT_X[1], ACT_Y[1])
    return {"orientacao": "B: vidro para cima, borda do cabeçalho para +y (jogador); imagem girada 180 graus no firmware",
            "origem_mundo_xb0_yb0": [round(WX0, 3), round(WY0, 3)], "placa_x": [round(WX0, 3), round(WX0 + W_B, 3)], "placa_y": [round(WY0, 3), round(WY0 + H_B, 3)],
            "vidro_x": [round(gx0, 3), round(gx1, 3)], "vidro_y": [round(gy0, 3), round(gy1, 3)],
            "area_ativa_x": [round(ax0, 3), round(ax1, 3)], "area_ativa_y": [round(ay0, 3), round(ay1, 3)],
            "furos_mundo": [[round(x, 3), round(y, 3)] for x, y in holes_world()], "niveis_z": {k: round(v, 2) for k, v in lv.items()},
            "plugue_direito_saida": [round(v, 3) for v in plug_exit_world()]}


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=1, ensure_ascii=False))
