"""eTuttino Pocket case, Seixo only (SPEC v5, task F3; v4 F1 and D2 before it), CadQuery.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/case.py

writes into out/ (STEP + STL, mirrored to a right-handed frame, see below):
  seixo_tampa        top shell: walls, keyboard lid, interface lid with the
                     engraved logo, the two knob recesses, knob/LED holes, the
                     Teensy button pinhole + guide tube, speaker grille and
                     seat, sealed speaker box walls, the micro-B female's
                     chord boss (window, recess, M3 pilots) and the jack's
                     facet (hole, spot face, rib), lid pockets over both,
                     posts for the controls board, screw columns
  seixo_fundo        bottom plate: board pillars, battery bay (walls + roof),
                     the hatch opening, countersunk screw holes, feet
  seixo_tampa_bateria  the battery hatch (2 M2 screws)
  seixo_caixa_fundo  the speaker box's floor (glued/sealed under its walls)
  plate              1.6 mm FR-4 switch plate (also plate.dxf)
  seixo_trava_usb    the bar that holds the FPC micro-B female in its tunnel
  seixo_chave_porca  printed nut driver for the pot's M7 nut in its recess

fit_check.py checks the electronics (pcb/PECAS.json) against these solids,
pcb_envelope.py writes out/pcb_envelope.json (the contract with the
electronics), render.py makes the pictures, mechanics.py the board's sag.

Plan geometry: ../shape.py, variant B ("Seixo"): the same rules, but here
the outline, the opening and the ramp edges are built EXACTLY (lines and
arcs) instead of shape.py's sampled polygons; check_plan() compares them.

Coordinates as in the eTuttino SPEC: x right from the case's leftmost point,
y from the back (0) to the player (100), z up from the table, mm. That
frame is left-handed, so everything is modelled in it and mirrored on
export: y_file = 100 - y_spec (x right, y away from the player, z up).
"""
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, POCKET)
import shape as S  # noqa: E402

# ================================================================ parameters
VARIANT = "B"
V = S.VARIANTS[VARIANT]
ORIGIN, KEYS, PLAN = S.place(V)                 # PLAN: shape.py's sampled outline (checked against ours)
P, D_BTN, WIDTH = S.P, S.D_BTN, S.WIDTH
ROW_PITCH = S.ROW_PITCH
ROW_Y = S.ROW_Y
D_SKIRT = 16.5

# keyboard opening (eTuttino rules)
CLR_SIDE, CLR_FB = S.CLR_SIDE, S.CLR_FB         # 15 / 8.17
R_OPEN_CORNER = 6.0                             # the four 120 deg corners
CHAMFER_W, CHAMFER_DROP = 4.0, 2.0
BOX_OFF = S.BOX_OFF                             # 10.3 right/front/back
R_CORNER = V["corner"]                          # 24: every other corner of the outline
BAND = V["band"]                                # 54: interface width (ramp top edge -> wall)

# heights (the eTuttino stack-up)
FLOOR_T = S.FLOOR_T                             # 2.0
Z_PCB_BOT, Z_PCB_TOP = S.Z_PCB_BOT, S.Z_PCB_TOP  # 6.5 / 7.7 (1.2 mm board)
PCB_T = Z_PCB_TOP - Z_PCB_BOT
PLATE_T = S.PLATE_T
Z_PLATE_TOP = S.Z_PLATE_TOP                     # 12.8
Z_DECK = S.Z_DECK                               # 17.4
Z_KEY_TOP = S.Z_KEY_TOP                         # 26.6
Z_IF, IF_CREASE_Y, IF_CREASE_R, IF_SLOPE = S.Z_IF, S.IF_CREASE_Y, S.IF_CREASE_R, S.IF_SLOPE
TAN_IF, COS_IF = S.TAN_IF, S.COS_IF
WALL = S.WALL                                   # 2.5 (Seixo)
TOP_T = S.TOP_T                                 # 2.5 lid over the interface
PLATE_OVERLAP = 3.0

# ramp (eTuttino): foot = the chamfer's outer edge, top edge = opening + 12.7, both R 5
RAMP_FOOT_OFF, RAMP_TOP_OFF = S.RAMP_FOOT_OFF, S.RAMP_TOP_OFF
RAMP_EDGE_R = 5.0
OUTER_EDGE_R = 1.0     # the outside top edges (walls -> deck / interface): no sharp edge under the hand

# ---------------------------------------------------------------- interface (SPEC v3 4, 7)
KNOB_Y = 49.0
VOLUME_XY = (15.12, KNOB_Y)
SELECT_XY = (31.12, KNOB_Y)
LED_XY = (43.12, KNOB_Y)
POT_HOLE_D = 7.3                                # M7 x 0.75 bushing (PECAS volume_pot)
# SPEC v5 change 5 (J's option A): the pot's M7 nut sits FLUSH in a round
# recess in the lid, covered by the knob; the selector gets the same recess
# (no nut) so the two look alike. No anti-rotation hole any more: the pot is
# soldered to its vertical board, which is soldered to the controls board on
# two lid posts, so it cannot turn; its pin (if the part has one) is clipped.
POT_PIN = None
POT_NUT_AF, POT_NUT_T = 10.0, 2.0               # M7 x 0.75 pot nut: across flats, thickness (PECAS nut_v5: size for 10 AF x 2.0; 9-10 AF typical, CHECK)
POT_BUSHING_L = 7.0                             # M7 thread from the body face (PECAS: footprint drawing)
KNOB_RECESS_D = 14.0                            # nut across corners 11.55 + room for the printed nut driver (OD 13.4)
KNOB_RECESS_DEPTH = POT_NUT_T                   # the nut's top flush with the lid (z 33)
SHAFT_HOLE_D = 6.8                              # encoder shaft (not nutted: the encoder sits on the controls board)
LED_HOLE_D = 3.5
# the knob (proposal, both the same: SPEC v5 4): skirt D15 covers the D14
# recess by 0.5 all round; skirt bottom 0.5 above the lid; D6 bore with a set
# screw (fits the pot's knurled shaft and the encoder's flatted one alike)
KNOB_D = 15.0
KNOB_H = 14.0                                   # skirt bottom -> top
KNOB_LIFT = 0.5                                 # skirt bottom above the lid surface
KNOB_BORE_MIN = 8.0                             # shaft engagement asked by PECAS (>= 8)
KNOB_CAVITY = (8.5, 5.0)                        # underside cavity for the bushing/thread left above the nut (d, depth)
NUT_TOOL = (10.15, 13.4, 25.0)                  # printed nut driver: hex AF inside, round OD (0.3 radial in the recess), length

# Teensy program button (SPEC v5 3): on the Teensy's TOP face at the end away
# from its USB, centred across its width (PJRC's drawing: the button and the
# orange LED sit at that end) -- 2.5 in from the end is CHECK on the part.
# Pressed from the top through a pinhole in the flat interface lid, with a
# guide tube down to just above the Teensy (from below it is impossible: the
# Audio Board and the main board are under it).
TEENSY_BTN_IN = 2.5                             # button centre, in from the Teensy's far end
BTN_HOLE_D = 1.6                                # paper clip (D 0.8-1.0)
BTN_TUBE_D = 4.0
BTN_TUBE_GAP = 1.3                              # tube bottom above the Teensy's parts (17.7)

# logo, engraved in the flat lid: STRAIGHT (horizontal), centred in the
# interface's back zone (SPEC v4 change 1): "eTuttino" over "POCKET"
LOGO_DEPTH = 0.4                                # SPEC v4 4: ~0.4, resin top shell
LOGO_FONT = r"C:/Windows/Fonts/georgiab.ttf"
LOGO_FONT2 = r"C:/Windows/Fonts/arialbd.ttf"
LOGO_SIZE = (9.0, 4.0)                          # font sizes (em): "eTuttino" 6.9 tall, "POCKET" cap 2.9
LOGO_TRACK = (0.3, 1.6)                         # extra letter spacing
LOGO_GAP = 2.6                                  # "eTuttino" baseline -> top of "POCKET"
LOGO_ZONE_Y = (4.0, 39.5)                       # back zone: behind the knob skirts (49 - 4.5) less the SPEC's 5
LOGO_MIN_MARGIN = 5.0                           # text -> outer edge / ramp top edge, at least

# speaker (PECAS speaker: Same Sky CLS0361-L152, final)
SPK_C = (26.88, 77.54)
SPK_D, SPK_DEPTH, SPK_FRAME_H, SPK_MAGNET_D = 36.0, 6.0, 2.7, 15.9
SPK_CONE_D = 31.0                               # radiating area (inside the rim) -- CHECK on the part
GASKET_T = 0.8                                  # foam ring, ~0.5 compressed: grille -> rim
SPK_SEAT_CLR = 0.3                              # radial, round the frame (36 +- 0.2)
SPK_RING_W, SPK_RING_H = 1.2, 3.0               # locating ring round the frame, hanging from the lid
GRILLE_HOLE_D, GRILLE_PITCH = 2.1, 3.0          # hex on the sloping lid; only over the cone (bridges 0.9)
GRILLE_EDGE = 0.8                               # hole edge -> cone edge
BOX_WALL = 1.5
BOX_FLOOR_T = 1.2
BOX_GROW = (13.0, 1.0)                          # the box's inside grows past the frame: +x (sideways), and all round
# the box floor sits on the battery bay's roof (below)

# the panel connectors on the back-left curved wall (SPEC v5 change 3; PECAS v5
# micro_b_panel_cable + headphone_jack). The panel board (USB-C + jack) is gone.
#
# micro-B extension on an FPC flat ribbon (PECAS v5, the design's F3 proposal:
# a round cable with R >= 18 does not fit): 'UP' 90 deg male in the Teensy (the
# ribbon rises from the plug's top), a small female head with no ears at the
# other end. The head slides into a tunnel in a block on a flat chord boss of
# the wall until it meets a 0.5 lip at the wall (the lip takes the plug's pull);
# a printed bar ("trava", 2 x M2 x 5 at 16) behind it takes the push. The
# block sits over the Teensy's plug with 2.0 under it for the ribbon's fold.
CONN_CHORD = (10.0, 40.0, 1.0)                  # boss face: chord of the inner wall between y0 and y1, d inwards
FEM_S, FEM_Z = -6.5, 27.25                      # head axis: along the chord from its middle (- = back), height
FEM_HEAD = (12.0, 9.0, 4.0)                     # female head w x length x h (PECAS, conferir)
FEM_POCKET = (12.4, 9.4, 4.4)                   # the tunnel (PECAS ~12.4 x 9.4 x 4.4)
FEM_LIP = (0.5, 8.6, 3.6, 0.8)                  # lip at the wall's inner face: thickness, opening w, h, R (receptacle 7.5 x 2.6)
FEM_HOLE = (12.0, 8.0, 1.0)                     # window w, h, R from outside to the lip (the plug's overmould enters it)
FEM_WALL = 3.0                                  # window + lip (PECAS: 1.0-3.0, design 3.0)
FEM_RECESS = (13.5, 9.0, 2.0)                   # outside: flat recess round the window (w, h, R) on the curved wall
FEM_BLOCK = (19.2, 1.2, 0.8)                    # block width (across), floor and pilot outer wall
FEM_SCREWS = (16.0, 1.6, 5.0)                   # M2 x 5 self-tapping into the block's end face: pitch, pilot d, depth
TRAVA = (19.2, 1.5, 6.4, 12.4, 1.6)             # the bar: w, thickness, h, ribbon slot w, h (MJF)
RIBBON_UNDER = 2.0                              # plug top -> block floor (the ribbon rises from the plug and folds flat)
CONN_LID_CLR = 0.3                              # parts -> lid
# headphone jack, Cliff FC681375V (M8 x 0.75 ring nut outside): its own flat
# facet, axis along +x at y JACK_Y (radial would run it into the pot board),
# turned so its 9.0 side is horizontal and 10.5 vertical: over J_BAT (top 18.2)
# and 0.5 from the pot board
JACK_Y, JACK_Z = 38.0, 23.95
JACK_BODY = (9.0, 10.5, 13.0)                   # across (y), height (z), length behind the shoulder
JACK_TABS = 4.0                                 # solder tabs out of the back face (+ ~4 of wires, bendable)
JACK_HOLE_D = 8.2
JACK_WALL = 2.0                                 # PECAS 1.0-2.5 (1.5-2.0 recommended)
JACK_SPOT_D = 11.5                              # outside: nut D10 (or hex 10 A/F, 11.5 across corners)
JACK_FACET = (12.0, 11.0)                       # inside flat (y, z) for the body's front face (PECAS >= 11 x 10)
JACK_RIB = (1.2, 8.0)                           # anti-rotation rib beside the body's 10.5 face: thickness, length

# Teensy 4.0 + Audio Board Rev D, the LOW stack (PECAS stack.low: Teensy soldered
# straight on the Audio Board, 8.7 from under the Audio Board to the top of the USB)
STACK_XY, STACK_ANGLE = (30.0, 4.0), 0.0        # Audio Board corner at its USB end / VIN side
AUDIO_L, AUDIO_W, AUDIO_LIFT = 38.0, 36.8, 3.0
PAST_USB, PAST_VIN = 3.6, 8.76
STACK_H = 8.7
Z_AB = Z_PCB_TOP + AUDIO_LIFT                   # 10.7
Z_AB_TOP = Z_AB + 1.6
Z_TEENSY_TOP = Z_AB + STACK_H - 2.6             # 16.8 (board top; the USB socket is 2.6 on it)
Z_USB_TOP = Z_AB + STACK_H                      # 19.4
Z_TEENSY_PARTS = Z_TEENSY_TOP + 0.9             # solder of the long headers, chips
USB_PLUG = (11.0, 11.0, 7.5)                    # 90 deg micro-B overmould (PECAS micro_b_link)

# controls (PECAS volume_pot / encoder / led / controls_connector)
# the switched pot lies on its side on a small vertical board RIGHT of it (between
# it and the encoder): its body runs 11.25 to the left of that board, the shaft
# 6.5 from it. (PECAS put that board behind the shaft, at y 40.9-42.5, where the
# panel board needs the room.)
POT_BODY = (10.37, 44.25, 21.62, 53.75, 14.5, 30.3)       # x0, y0, x1, y1, z0, z1
POT_BOARD = (21.62, 43.0, 23.22, 55.0, 13.8, 29.8)
POT_LEGS_X = 24.3                               # its legs clipped to 1.0 past the board (the encoder is at 24.92)
CTRL_BOARD = (23.22, 42.5, 50.6, 56.0)          # its left edge meets the pot board at 90 deg
# two tabs for the EC11E's legs (PECAS controls_board, E2b): the back one over
# the Audio Board, the front one into a dent in the speaker box's back wall
CTRL_TABS = [(27.0, 40.0, 35.2, 42.5), (27.0, 56.0, 35.2, 57.5)]
TAB_CLR = 0.5                                   # tab -> the dent's walls
TAB_DENT_TOP = 18.5                             # the dent's ceiling (tab top 17.18; encoder legs are under the tab)
CTRL_CONN = (46.4, 43.0, 50.6, 55.0)            # 10-way SH header on top at the right edge (12 along y)
CTRL_T = 1.6
CTRL_TOP = 17.18
CTRL_LEGS = 1.5
ENC = (12.4, 13.2, 6.5)
CTRL_POSTS = [(40.4, 44.8), (40.4, 53.2)]       # M2 into lid posts
POST_D, POST_PILOT_D, POST_PILOT_DEPTH = 5.0, 1.7, 6.0
CTRL_CABLE = (50.6, 40.9, 56.0, 45.8)           # where its cable drops to the main board (J_CTL below it)

# battery bay (PECAS battery: cradle 7.6 x 36.5 x 58.5), on the bottom plate, off the main board
BATT_C, BATT_ANGLE = (40.0, 68.3), 0.0           # v4: +2 x, +2.5 y (D2: 38, 65.8) so the plug pocket gets its 9.0 in y
BATT_IN = (58.5, 36.5, 7.6)                     # length (x), width (y), height
BATT_WALL, BATT_ROOF = 1.2, 1.0
BATT_ROOF_GAP = 0.2
BATT_PCM_END = -1                               # -1: the PCM end (wire exit) at the left
# the battery's plug mates INSIDE the bay, in a pocket behind its left end
# (x range, back y): out through the hatch, unplug, no lid to open. A short
# pigtail from the main board comes down into the pocket through BATT_SLOT.
BATT_POCKET = (10.0, 26.0, 40.8)                # v4: 16.0 x 9.25 x 7.6 (PECAS connector_pocket_v4: >= 14.5 x 9.0 x 6.0); x0 clear of the column at (5.3, 38.5)
BATT_SLOT = (10.0, 16.0)                        # x range of the pigtail's way in (6 x 4, PECAS), in the pocket's roof
HATCH_CLR = 0.3
HATCH_SCREWS_DX = 24.0

# board, case screws, pillars
PCB_CLR = 0.5                                   # board edge -> inside of the walls / bay walls
BOSS_D, PILOT_D = 6.0, 2.2                      # M2.5 self-tapping into the shell (or heat-set insert)
SCREW_CLR_D, HEAD_D, HEAD_DEPTH = 2.9, 5.2, 1.6
FUNDO_CLR = 0.3
PILLAR_D = 4.0
SCREW_PILLAR_D = 6.0
M2_CLR_D, M2_HEAD_D, M2_HEAD_DEPTH = 2.4, 4.2, 1.4
FOOT_D, FOOT_DEPTH = 10.5, 0.6

# ================================================================ keys
G3 = min((k for k in KEYS if k["row"] == 2), key=lambda k: k["x"])
E5 = max((k for k in KEYS if k["row"] == 2), key=lambda k: k["x"])
ROW2_X = (G3["x"], E5["x"])
GC = (G3["x"], G3["y"])                         # centre of the left side's arcs
R_LEFT = S.R_RAMP + BAND                        # 89.2


def keys():
    """(n, row, x, y, kind) like the eTuttino's case.keys()."""
    out = []
    for k in KEYS:
        kind = "sharp" if k["sharp"] else ("cf" if k["cf"] else "natural")
        out.append((k["n"], k["row"], k["x"], k["y"], kind))
    return out


def note_name(n):
    return S.note_name(S.G3 + n)

# ================================================================ 2D: exact contours
TAN = math.tan(math.radians(30))
COS = math.cos(math.radians(30))


def _fillet(prev, v, nxt, r):
    """Tangent points, arc midpoint and centre of a fillet of radius r at v."""
    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        return dx / L, dy / L
    u1, u2 = unit(v, prev), unit(v, nxt)
    theta = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
    t = r / math.tan(theta / 2)
    bx, by = u1[0] + u2[0], u1[1] + u2[1]
    bl = math.hypot(bx, by)
    bx, by = bx / bl, by / bl
    c = r / math.sin(theta / 2)
    centre = (v[0] + bx * c, v[1] + by * c)
    return ((v[0] + u1[0] * t, v[1] + u1[1] * t), (centre[0] - bx * r, centre[1] - by * r),
            (v[0] + u2[0] * t, v[1] + u2[1] * t), centre)


def fillets(contour):
    n = len(contour)
    return [_fillet(contour[i - 1][0], contour[i][0], contour[(i + 1) % n][0], contour[i][1]) for i in range(n)]


def hex_contour(d):
    """The keyboard opening grown by d: [(vertex, radius)], the eTuttino's
    rule (lateral vertices concentric with the row-2 end keys, R 6 at the
    four 120 deg corners)."""
    ytop = ROW_Y[4] - D_BTN / 2 - CLR_FB - d
    ybot = ROW_Y[1] + D_BTN / 2 + CLR_FB + d
    side = D_BTN / 2 + CLR_SIDE + d
    yl = ROW_Y[2]
    xl = ROW2_X[0] - side / COS
    xr = ROW2_X[1] + side / COS
    return [((xl + (yl - ytop) * TAN, ytop), R_OPEN_CORNER + d),
            ((xr - (yl - ytop) * TAN, ytop), R_OPEN_CORNER + d),
            ((xr, yl), side),
            ((xr - (ybot - yl) * TAN, ybot), R_OPEN_CORNER + d),
            ((xl + (ybot - yl) * TAN, ybot), R_OPEN_CORNER + d),
            ((xl, yl), side)]


def contour_pieces(contour):
    """[(kind, points)] of a vertex/radius contour: 'line' (2 pts) / 'arc' (3 pts)."""
    f = fillets(contour)
    out = []
    for i in range(len(f)):
        a_in, mid, a_out, _ = f[i]
        out.append(("arc", [a_in, mid, a_out]))
        nxt = f[(i + 1) % len(f)][0]
        out.append(("line", [a_out, nxt]))
    return out


def _line_meet(p, d, y):
    """Point where the line through p with direction d reaches the given y."""
    t = (y - p[1]) / d[1]
    return (p[0] + d[0] * t, y)


def outline_pieces():
    """The case in plan, exactly: variant B of shape.py. Clockwise in the
    SPEC frame (x right, y towards the player): back wall, the right ">" (a
    line tangent to the circles R 32.8 round C5 and E5, the arc round E5,
    the line to D#5), front wall, then the left side: ONE arc of R 89.2
    round G3 (concentric with the ramp's tip). R 24 at the four corners
    where it meets y = 0 / 100 (shape.round_corners does the same with a
    rolling disk; the short R 32.8 arc pieces near y = 0 / 100 vanish in it)."""
    rb = S.R_BOX
    row4_last = max((k for k in KEYS if k["row"] == 4), key=lambda k: k["x"])
    row1_last = max((k for k in KEYS if k["row"] == 1), key=lambda k: k["x"])
    E = (E5["x"], E5["y"])
    nb, nf = (COS, -0.5), (COS, 0.5)                     # outward normals of the right edges
    tb_e = (E[0] + rb * nb[0], E[1] + rb * nb[1])
    tf_e = (E[0] + rb * nf[0], E[1] + rb * nf[1])
    dir_b = (row4_last["x"] - E[0], row4_last["y"] - E[1])   # E5 -> C5 (back, up the page)
    dir_f = (row1_last["x"] - E[0], row1_last["y"] - E[1])   # E5 -> D#5
    vbr = _line_meet(tb_e, dir_b, 0.0)
    vfr = _line_meet(tf_e, dir_f, WIDTH)
    # left: the big arc round G3, its back tangent at 210 deg reaching y = 0 at B0
    R = R_LEFT
    t210 = (GC[0] + R * math.cos(math.radians(210)), GC[1] + R * math.sin(math.radians(210)))
    vbl = _line_meet(t210, (math.sin(math.radians(30)), -math.cos(math.radians(30))), 0.0)
    bl = _fillet(t210, vbl, (vbl[0] + 50, 0.0), R_CORNER)
    br = _fillet((vbr[0] - 50, 0.0), vbr, tb_e, R_CORNER)
    fr = _fillet(tf_e, vfr, (vfr[0] - 50, WIDTH), R_CORNER)
    # front-left: R 24 tangent to y = 100 and inside the big circle
    cy = WIDTH - R_CORNER
    cx = GC[0] - math.sqrt((R - R_CORNER) ** 2 - (cy - GC[1]) ** 2)
    fl_line = (cx, WIDTH)
    k = R / (R - R_CORNER)
    fl_arc = (GC[0] + (cx - GC[0]) * k, GC[1] + (cy - GC[1]) * k)
    a_mid = math.atan2((fl_line[1] + fl_arc[1]) / 2 - cy, (fl_line[0] + fl_arc[0]) / 2 - cx)
    fl_mid = (cx + R_CORNER * math.cos(a_mid), cy + R_CORNER * math.sin(a_mid))
    # the big arc from fl_arc through the far left point to t210
    a0 = math.atan2(fl_arc[1] - GC[1], fl_arc[0] - GC[0])
    a1 = math.radians(210)
    am = (a0 % (2 * math.pi) + a1) / 2
    big_mid = (GC[0] + R * math.cos(am), GC[1] + R * math.sin(am))
    return [
        ("line", [bl[2], br[0]]),
        ("arc", [br[0], br[1], br[2]]),
        ("line", [br[2], tb_e]),
        ("arc", [tb_e, (E[0] + rb, E[1]), tf_e]),
        ("line", [tf_e, fr[0]]),
        ("arc", [fr[0], fr[1], fr[2]]),
        ("line", [fr[2], fl_line]),
        ("arc", [fl_line, fl_mid, fl_arc]),
        ("arc", [fl_arc, big_mid, t210]),
        ("line", [t210, bl[0]]),
        ("arc", [bl[0], bl[1], bl[2]]),
    ]


def pieces_wire(pieces, z=0.0):
    wp = cq.Workplane("XY", origin=(0, 0, z)).moveTo(*pieces[0][1][0])
    for kind, pts in pieces:
        if kind == "line":
            if math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) > 1e-6:
                wp = wp.lineTo(*pts[1])
        else:
            wp = wp.threePointArc(pts[1], pts[2])
    return wp.close()


def pieces_points(pieces, seg=0.5):
    """The contour as a polygon (arcs split into ~seg chords)."""
    pts = []
    for kind, p in pieces:
        if kind == "line":
            a, b = p
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / seg))
            pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
        else:
            a, m, b = p
            c, r = _circle3(a, m, b)
            t0 = math.atan2(a[1] - c[1], a[0] - c[0])
            tm = math.atan2(m[1] - c[1], m[0] - c[0])
            t1 = math.atan2(b[1] - c[1], b[0] - c[0])
            d1 = (tm - t0) % (2 * math.pi)
            d2 = (t1 - t0) % (2 * math.pi)
            sweep = d2 if d1 <= d2 else d2 - 2 * math.pi
            n = max(2, int(abs(sweep) * r / seg))
            pts += [(c[0] + r * math.cos(t0 + sweep * i / n), c[1] + r * math.sin(t0 + sweep * i / n)) for i in range(n)]
    return pts


def _circle3(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


def outline_points(seg=0.5):
    return pieces_points(outline_pieces(), seg)


def opening_points(d=0.0, seg=0.5):
    return pieces_points(contour_pieces(hex_contour(d)), seg)


def contour_wp(contour, z=0.0):
    return pieces_wire(contour_pieces(contour), z)


def outline_wp(z=0.0, inset=0.0):
    wp = pieces_wire(outline_pieces(), z)
    if inset:
        w = wp.wires().val().offset2D(-inset)[0]
        return cq.Workplane("XY").add(w)
    return wp


def prism_wire(wire, z0, z1):
    w = wire.translate(cq.Vector(0, 0, z0 - wire.Center().z))
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(w), cq.Vector(0, 0, z1 - z0))


def outline_solid(z0, z1, inset=0.0):
    w = pieces_wire(outline_pieces()).wires().val()
    if inset:
        w = w.offset2D(-inset)[0]
    return prism_wire(w, z0, z1)


def length():
    xs = [x for x, _ in outline_points(0.2)]
    return max(xs) - min(xs)


def check_plan():
    """Our exact outline against shape.py's sampled one: largest gap."""
    ours = outline_points(0.25)
    worst = max(S.edge_dist(ours, p) for p in PLAN)
    return worst


# ================================================================ 3D helpers
def box3(x0, y0, z0, x1, y1, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cyl(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0))


def fuse(shapes):
    shapes = [s for s in shapes if s is not None]
    out = shapes[0]
    if len(shapes) > 1:
        out = out.fuse(*shapes[1:])
    return out.clean()


def poly_prism(pts, z0, z1):
    w = cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in pts], close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(w), cq.Vector(0, 0, z1 - z0))


def z_interface(y, dz=0.0):
    return S.z_interface(y, dz)


def below_plane(dz=0.0, x0=-60, x1=300):
    """Everything under the interface's top (flat to the crease, R 10, then
    13 deg down to the front), lowered by dz along its normal."""
    y0, y1 = -50.0, WIDTH + 50.0
    yc = IF_CREASE_Y - dz * (1 / COS_IF - 1) / TAN_IF
    corner = (yc, Z_IF - dz)
    a = (y0, Z_IF - dz)
    b = (y1, z_interface(y1, dz))
    t1, mid, t2, _ = _fillet(a, corner, b, max(IF_CREASE_R - dz, 0.5))
    wp = (cq.Workplane("YZ", origin=(x0, 0, 0)).moveTo(y0, -10).lineTo(*a).lineTo(*t1)
          .threePointArc(mid, t2).lineTo(*b).lineTo(y1, -10).close().extrude(x1 - x0))
    return wp.val()


# ================================================================ ramp
def ramp_edge(d, y_from=-30.0, y_to=WIDTH + 30.0, n_line=48, k_arc=60):
    """One ramp edge in plan, back to front: the opening's "<" grown by d,
    as the back 30 deg line (from beyond the back wall), the arc round G3
    (210 -> 150 deg) and the front 30 deg line (on through the front wall).
    Fixed point counts, so the foot and top edges pair up point for point."""
    r = D_BTN / 2 + CLR_SIDE + d
    a_b, a_f = math.radians(210), math.radians(150)
    tb = (GC[0] + r * math.cos(a_b), GC[1] + r * math.sin(a_b))
    tf = (GC[0] + r * math.cos(a_f), GC[1] + r * math.sin(a_f))
    sb = _line_meet(tb, (math.sin(math.radians(30)), -COS), y_from)
    sf = _line_meet(tf, (math.sin(math.radians(30)), COS), y_to)
    pts = [(sb[0] + (tb[0] - sb[0]) * i / n_line, sb[1] + (tb[1] - sb[1]) * i / n_line) for i in range(n_line)]
    pts += [(GC[0] + r * math.cos(a_b + (a_f - a_b) * i / k_arc), GC[1] + r * math.sin(a_b + (a_f - a_b) * i / k_arc))
            for i in range(k_arc)]
    pts += [(tf[0] + (sf[0] - tf[0]) * i / n_line, tf[1] + (sf[1] - tf[1]) * i / n_line) for i in range(n_line + 1)]
    return pts


def raised_region(foot_d, z_foot, top_d, dz_top, z_hi=45.0):
    """The interface block and its ramp: the ruled surface from the foot
    edge (z_foot) through the top edge (on the interface top lowered by
    dz_top), extended to z_hi; everything left of it, under the top. ONE
    ruled loft through two splines of paired points (the OCC lessons)."""
    foot = ramp_edge(foot_d)
    top = ramp_edge(top_d)
    lo, hi = [], []
    for (x, y), (qx, qy) in zip(foot, top):
        zq = z_interface(min(max(qy, 0.0), WIDTH), dz_top)
        s_ = (z_hi - z_foot) / (zq - z_foot)
        lo.append(cq.Vector(x, y, z_foot))
        hi.append(cq.Vector(x + (qx - x) * s_, y + (qy - y) * s_, z_hi))
    lo_edges, hi_edges = [cq.Edge.makeSpline(lo)], [cq.Edge.makeSpline(hi)]
    far = -60.0

    def close(edges, z):
        a = edges[-1].endPoint()
        b = edges[0].startPoint()
        tail = [a, cq.Vector(far, a.y, z), cq.Vector(far, b.y, z), b]
        return cq.Wire.assembleEdges(edges + [cq.Edge.makeLine(p, q) for p, q in zip(tail, tail[1:])])
    loft = cq.Solid.makeLoft([close(lo_edges, z_foot), close(hi_edges, z_hi)], ruled=True)
    return loft.intersect(below_plane(dz_top))


def round_ramp(body):
    """R 5 on the ramp's foot and top edges, one after the other."""
    def is_ramp(f):
        c = f.Center()
        if c.x > ROW2_X[0] + 10 or c.z < Z_DECK + 0.5 or abs(c.z - z_interface(c.y)) < 0.5:
            return False
        n = f.normalAt(c)
        return 0.05 < abs(n.z) < 0.98

    def edges(b, where):
        out = []
        for f in b.Faces():
            if not is_ramp(f):
                continue
            for e in f.Edges():
                c = e.Center()
                if c.y < 0.5 or c.y > WIDTH - 0.5:
                    continue
                if where(c) and not any(e.isSame(o) for o in out):
                    out.append(e)
        return out
    for where in (lambda c: abs(c.z - Z_DECK) < 0.05,
                  lambda c: abs(c.z - z_interface(c.y)) < 0.3):
        es = edges(body, where)
        try:
            nb = body.fillet(RAMP_EDGE_R, es)
            assert nb.isValid(), "invalid result"
            body = nb
        except Exception as exc:
            print("ramp fillet failed (%s): edges left sharp" % exc)
    return body


def round_outer_top(body, r=OUTER_EDGE_R):
    """R 1 on the top edges of the outer walls (deck and interface)."""
    if r <= 0:
        return body
    pts = outline_points(1.0)
    es = []
    for e in body.Edges():
        c = e.Center()
        if c.z < Z_DECK - 0.05:
            continue
        if S.edge_dist(pts, (c.x, c.y)) > 0.05:
            continue
        # a horizontal-ish edge on the outside wall at its top
        b = e.BoundingBox()
        if b.zlen > 12:
            continue
        es.append(e)
    try:
        nb = body.fillet(r, es)
        assert nb.isValid()
        return nb
    except Exception as exc:
        print("outer edge rounding failed (%s): left sharp" % exc)
        return body


def outer_body():
    base = outline_solid(0.0, Z_DECK)
    tall = outline_solid(0.0, Z_IF + 5.0)
    raised = raised_region(RAMP_FOOT_OFF, Z_DECK, RAMP_TOP_OFF, 0.0).intersect(tall)
    body = base.fuse(raised).clean()
    body = round_ramp(body)
    return round_outer_top(body)


def cavity():
    """The inside: walls WALL, lid TOP_T under the interface, the keyboard
    lid down to the plate's top; open at the bottom."""
    low = outline_solid(-1.0, Z_PLATE_TOP, WALL)
    tall = outline_solid(-1.0, Z_IF, WALL)
    raised = raised_region(RAMP_FOOT_OFF + WALL, Z_PLATE_TOP, RAMP_TOP_OFF + WALL, TOP_T).intersect(tall)
    return low.fuse(raised).clean()


def rounded_opening_cutter():
    """The keyboard opening with its 4 mm rounded edge: ONE ruled loft
    through stacked opening contours (eTuttino)."""
    z_land = Z_DECK - CHAMFER_DROP
    levels = [(0.0, Z_PLATE_TOP - 3.0), (0.0, z_land)]
    n = 16
    for i in range(1, n + 1):
        phi = math.pi / 2 * i / n
        levels.append((CHAMFER_W * (1 - math.cos(phi)), z_land + CHAMFER_DROP * math.sin(phi)))
    levels.append((CHAMFER_W, Z_DECK + 5.0))
    secs = [contour_wp(hex_contour(d), z).wire().val() for d, z in levels]
    return cq.Solid.makeLoft(secs, ruled=True)




# ================================================================ interior layout (plan)
def local_rect(origin, ang, u0, v0, u1, v1):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    ox, oy = origin
    return [(ox + u * c - v * s, oy + u * s + v * c) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]


def stack_parts():
    """The Teensy + Audio Board stack: {name: (plan polygon, (z0, z1))}.
    Local frame: u along the Audio Board's 38 mm side from its USB end, v
    across from its VIN side (as variants.stack_parts)."""
    R = lambda u0, v0, u1, v1: local_rect(STACK_XY, STACK_ANGLE, u0, v0, u1, v1)
    tcx, tcy = PAST_USB + 6.5 * 2.54, PAST_VIN + 7.62
    jy = tcy + 7.62 + 7.2
    u_usb = tcx - 18.8
    zc = Z_TEENSY_TOP + 1.3
    return {
        "audio_board": (R(0, 0, AUDIO_L, AUDIO_W), (Z_AB, Z_AB_TOP)),
        "ab_jack": (R(0, jy - 3, 13, jy + 3), (Z_AB_TOP, Z_AB + 6.7)),
        "teensy": (R(tcx - 17.78, tcy - 8.89, tcx + 17.78, tcy + 8.89), (Z_AB_TOP, Z_TEENSY_PARTS)),
        "teensy_usb": (R(u_usb, tcy - 3.75, u_usb + 5.0, tcy + 3.75), (Z_TEENSY_TOP, Z_USB_TOP)),
        "usb_plug": (R(u_usb - USB_PLUG[0], tcy - USB_PLUG[1] / 2, u_usb, tcy + USB_PLUG[1] / 2),
                     (zc - USB_PLUG[2] / 2, zc + USB_PLUG[2] / 2)),
    }


def stack_pin_centres():
    """The 28 header legs (they pin the main board under the stack)."""
    tcy = PAST_VIN + 7.62
    out = []
    for i in range(14):
        for s in (-1, 1):
            out.append(local_rect(STACK_XY, STACK_ANGLE, PAST_USB + 2.54 * i, tcy + s * 7.62,
                                  PAST_USB + 2.54 * i, tcy + s * 7.62)[0])
    return out


def inner_points(seg=0.5):
    w = pieces_wire(outline_pieces()).wires().val().offset2D(-WALL)[0]
    n = max(64, int(w.Length() / seg))
    return [(p.x, p.y) for p in w.positions([i / n for i in range(n)])]


def _wall_point_at_y(y):
    """Where the inside of the left wall crosses the given y."""
    pts = inner_points(0.25)
    best = None
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < 60 and (best is None or x < best[0]):
                best = (x, y)
    return best


_CONN = {}


def wall_x_at(y, side="inner"):
    """x of the left wall's inner (or outer) surface at plan y."""
    if side == "inner":
        return _wall_point_at_y(y)[0]
    pts = outline_points(0.2)
    best = None
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < 60 and (best is None or x < best):
                best = x
    return best


def conn_geometry():
    """The female's chord boss: its face (a vertical plane), the female's
    origin on it (flange front, axis), the jack's facet. Frames: n = inwards,
    t = along the face (back -> front)."""
    if _CONN:
        return _CONN
    y0, y1, d = CONN_CHORD
    a, b = _wall_point_at_y(y0), _wall_point_at_y(y1)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (t[1], -t[0])
    if n[0] < 0:
        n = (-n[0], -n[1])
    m = ((a[0] + b[0]) / 2 + n[0] * d, (a[1] + b[1]) / 2 + n[1] * d)
    at = lambda s, dd=0.0: (m[0] + t[0] * s + n[0] * dd, m[1] + t[1] * s + n[1] * dd)
    outer = outline_points(0.2)

    def wall_behind(p, nn):
        lo, hi = 0.0, 15.0
        for _ in range(40):
            mid = (lo + hi) / 2
            q = (p[0] - nn[0] * mid, p[1] - nn[1] * mid)
            if S.inside(outer, q):
                lo = mid
            else:
                hi = mid
        return lo
    fo = at(FEM_S)
    # the jack's facet: perpendicular to +x, just inside the wall over its height
    yj0, yj1 = JACK_Y - JACK_FACET[0] / 2, JACK_Y + JACK_FACET[0] / 2
    xf = max(wall_x_at(yj0 + k * (yj1 - yj0) / 10) for k in range(11)) + 0.2
    jo = (xf, JACK_Y)
    _CONN.update({"m": m, "t": t, "n": n, "at": at, "chord": L, "fem_origin": fo,
                  "fem_wall": wall_behind(fo, n), "jack_origin": jo, "jack_wall": wall_behind(jo, (1.0, 0.0))})
    return _CONN


def local_solid(sh, origin, n, z):
    """sh built with +x = inwards along n, +y = along t (n turned +90 deg), z about the axis."""
    ang = math.degrees(math.atan2(n[1], n[0]))
    return sh.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang).translate(cq.Vector(origin[0], origin[1], z))


def stadium(w, h, r, x0, x1):
    """A rounded rectangle w (y) x h (z), corners r, from x0 to x1 along x."""
    sk = cq.Workplane("YZ", origin=(x0, 0, 0)).rect(w, h).extrude(x1 - x0)
    if r > 0:
        sk = sk.edges("|X").fillet(min(r, h / 2 - 0.01, w / 2 - 0.01))
    return sk.val()


def female_solids():
    """The FPC female head in its tunnel (PECAS micro_b_panel_cable.female,
    ~12 x 9 x 4, conferir) and the trava bar behind it."""
    g = conn_geometry()
    w, L, h = FEM_HEAD
    head = cq.Solid.makeBox(L, w, h, cq.Vector(0.0, -w / 2, -h / 2))
    tw, tt, th, sw, sh = TRAVA
    bar = cq.Solid.makeBox(tt, tw, th, cq.Vector(FEM_POCKET[1], -tw / 2, -th / 2)).cut(
        cq.Solid.makeBox(tt + 2, sw, sh, cq.Vector(FEM_POCKET[1] - 1, -sw / 2, -sh / 2)))
    for y in (-FEM_SCREWS[0] / 2, FEM_SCREWS[0] / 2):
        bar = bar.cut(cq.Solid.makeCylinder(1.15, tt + 2, cq.Vector(FEM_POCKET[1] - 1, y, 0), cq.Vector(1, 0, 0)))
    return local_solid(head, g["fem_origin"], g["n"], FEM_Z), local_solid(bar, g["fem_origin"], g["n"], FEM_Z)


def trava():
    """The bar as a printable part (lying flat)."""
    tw, tt, th, sw, sh = TRAVA
    bar = cq.Solid.makeBox(tw, th, tt, cq.Vector(-tw / 2, -th / 2, 0)).cut(cq.Solid.makeBox(sw, sh, tt + 2, cq.Vector(-sw / 2, -sh / 2, -1)))
    for x in (-FEM_SCREWS[0] / 2, FEM_SCREWS[0] / 2):
        bar = bar.cut(cq.Solid.makeCylinder(1.15, tt + 2, cq.Vector(x, 0, -1)))
    return bar


def fem_block_rect():
    """The block's plan footprint (4 points) and its z range."""
    g = conn_geometry()
    o, n = g["fem_origin"], g["n"]
    t = (-n[1], n[0])
    hw = FEM_BLOCK[0] / 2
    L = FEM_POCKET[1]
    pts = [(o[0] + n[0] * a + t[0] * b, o[1] + n[1] * a + t[1] * b) for a, b in ((0, -hw), (L, -hw), (L, hw), (0, hw))]
    z0 = FEM_Z - FEM_POCKET[2] / 2 - FEM_BLOCK[1]
    return pts, (z0, z_interface(o[1], TOP_T))


def ribbon_zones():
    """Where the FPC ribbon goes (PECAS: flat, any fold R >= 1.5): it rises
    from the plug's top, folds flat under the block, comes out past the
    block's inner end, rises and enters the trava's slot; the extra length
    (10 cm cable, ~9 cm spare) lies folded flat over the Teensy. Solids for
    the fit check (nothing of the case or the parts may be in them)."""
    rect, (pz0, pz1) = stack_parts()["usb_plug"]
    x0, x1 = min(p[0] for p in rect), max(p[0] for p in rect)
    y0, y1 = min(p[1] for p in rect), max(p[1] for p in rect)
    zf = fem_block_rect()[1][0]
    g = conn_geometry()
    e = FEM_POCKET[1] + TRAVA[1]
    riser = local_solid(cq.Solid.makeBox(2.6, 13.0, FEM_Z + 2.0 - pz1, cq.Vector(e + 0.3, -6.5, pz1 + 0.05 - FEM_Z)),
                        g["fem_origin"], g["n"], FEM_Z)
    return {"fold_under_block": box3(x0 + 0.5, y0 + 1.0, pz1 + 0.05, x1 - 0.5, y1 - 1.0, zf - 0.05),
            "riser_at_block_end": riser,
            "spare_over_teensy": box3(x1 + 2.0, 13.5, Z_USB_TOP + 0.6, x1 + 16.0, 27.5, Z_USB_TOP + 4.0)}


def jack_solids():
    """The Cliff FC681375V: body + tabs inside, thread through the wall, nut outside."""
    g = conn_geometry()
    w, h, L = JACK_BODY
    body = cq.Solid.makeBox(L, w, h, cq.Vector(0, -w / 2, -h / 2))
    tabs = cq.Solid.makeBox(JACK_TABS, w - 2.0, h - 2.0, cq.Vector(L, -(w - 2.0) / 2, -(h - 2.0) / 2))
    wall = g["jack_wall"]
    wj = JACK_WALL
    thread = cq.Solid.makeCylinder(4.0, 4.5, cq.Vector(-4.5, 0, 0), cq.Vector(1, 0, 0))
    nut = cq.Solid.makeCylinder(5.0, 2.0, cq.Vector(-wj - 2.0, 0, 0), cq.Vector(1, 0, 0))
    o = g["jack_origin"]
    return (local_solid(body.fuse(tabs), o, (1.0, 0.0), JACK_Z), local_solid(thread, o, (1.0, 0.0), JACK_Z),
            local_solid(nut, o, (1.0, 0.0), JACK_Z))


def battery_rects():
    """Battery bay: inside (the cradle) and outside (with its walls)."""
    l, w, _ = BATT_IN
    inside = local_rect(BATT_C, BATT_ANGLE, -l / 2, -w / 2, l / 2, w / 2)
    o = BATT_WALL
    outside = local_rect(BATT_C, BATT_ANGLE, -l / 2 - o, -w / 2 - o, l / 2 + o, w / 2 + o)
    return inside, outside


def pocket_rects():
    """The connector pocket behind the bay's left end: inside and outside."""
    l, w, _ = BATT_IN
    x0, x1, y0 = BATT_POCKET
    y1 = BATT_C[1] - w / 2 + 0.01
    o = BATT_WALL
    return ([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
            [(x0 - o, y0 - o), (x1 + o, y0 - o), (x1 + o, y1), (x0 - o, y1)])


BATT_Z = (FLOOR_T, FLOOR_T + BATT_IN[2])                  # 2.0 .. 9.6
BATT_ROOF_Z = (BATT_Z[1] + BATT_ROOF_GAP, BATT_Z[1] + BATT_ROOF_GAP + BATT_ROOF)   # 9.8 .. 10.8
HATCH_SCREWS = [(BATT_C[0] - 17.0, BATT_C[1] + BATT_IN[1] / 2 + BATT_WALL + 2.2),     # +-17 (D2: 19): clear of the column at (63, 93.5)
                (BATT_C[0] + 17.0, BATT_C[1] + BATT_IN[1] / 2 + BATT_WALL + 2.2)]
HATCH_BOSS_D = 5.0
HATCH_T = 1.2


def hatch_rect(grow=0.0):
    """The hatch door: the bay's inside + 2.0 round it, the front side
    reaching over the two screw bosses."""
    l, w, _ = BATT_IN
    x0, x1 = BATT_C[0] - l / 2 - 2.0 - grow, BATT_C[0] + l / 2 + 2.0 + grow
    y0 = BATT_C[1] - w / 2 - 2.0 - grow
    y1 = HATCH_SCREWS[0][1] + HATCH_BOSS_D / 2 + 0.8 + grow
    return x0, y0, x1, y1


# speaker box
def spk_inner_contour():
    """The box's inside in plan: the frame's circle grown by BOX_GROW[1],
    stretched BOX_GROW[0] towards +x (round, convex)."""
    r = SPK_D / 2 + SPK_SEAT_CLR + BOX_GROW[1]
    c0 = SPK_C
    c1 = (SPK_C[0] + BOX_GROW[0], SPK_C[1])
    return S.ccw(S.hull(S.circles([c0, c1], r, steps=96)))


SPK_BOX_BOTTOM = BATT_ROOF_Z[1] + 0.1 + BOX_FLOOR_T      # the walls end here; the floor plate is glued under them


def speaker_face_z(y):
    """The speaker's front face (rim) at plan y: the lid's underside less the compressed gasket."""
    return z_interface(y, TOP_T) - GASKET_T * 0.6 / COS_IF


# ================================================================ fixings
def screw_points():
    """Case screws from below into columns of the top shell."""
    return [(100.0, 6.0), (157.0, 6.0), (214.0, 6.0),
            (100.0, 94.0), (157.0, 94.0), (214.0, 94.0),
            (246.5, ROW_Y[2]),
            (25.0, 6.5), (63.0, 93.5), (5.3, 38.5)]


# columns that stop short (they hang on the wall): the one at the left wall
# would run up through the vertical pot board
BOSS_TOP = {(5.3, 38.5): 13.2}

BOARD_SCREWS = [(26.0, 35.0), (232.0, ROW_Y[2])]          # M2 from below, nut on the board
EXTRA_PILLARS = [(75.0, 51.0), (77.0, 68.0), (72.0, 41.0), (80.0, 85.0), (238.0, 46.0), (238.0, 70.0)]


def pillar_points():
    """Board supports on the bottom plate: the centre of every triangle of
    three neighbouring keys (eTuttino), plus a few round the ends."""
    ks = [(row, x, y) for _, row, x, y, _ in keys()]
    have = {(row, round(x, 3)) for row, x, _ in ks}
    pts = set()
    for row, x, y in ks:
        for other in (row - 1, row + 1):
            if other not in ROW_Y:
                continue
            if (row, round(x + P, 3)) in have and (other, round(x + P / 2, 3)) in have:
                pts.add((round(x + P / 2, 3), round(y + (ROW_Y[other] - y) / 3, 3)))
    pts = sorted(pts, key=lambda p: (p[1], p[0]))
    return pts + list(EXTRA_PILLARS)


# ================================================================ shell parts
def grille_holes():
    """Holes over the cone only: a hex grid measured on the 13 deg lid."""
    rc = SPK_CONE_D / 2 - GRILLE_EDGE - GRILLE_HOLE_D / 2
    px, py = GRILLE_PITCH, GRILLE_PITCH * COS * COS_IF
    out = []
    for j in range(-12, 13):
        y = SPK_C[1] + j * py
        off = GRILLE_PITCH / 2 if j % 2 else 0.0
        for i in range(-12, 13):
            x = SPK_C[0] + i * px + off
            if math.hypot(x - SPK_C[0], (y - SPK_C[1]) / COS_IF) <= rc + 1e-6:
                out.append((round(x, 3), round(y, 3)))
    return out


def grille_open_ratio():
    n = len(grille_holes())
    cone = math.pi * (SPK_CONE_D / 2) ** 2
    return n, n * math.pi * (GRILLE_HOLE_D / 2) ** 2 / cone


_GLYPH = {}


def _glyph(ch, font, size, depth):
    key = (ch, font, size, depth)
    if key not in _GLYPH:
        _GLYPH[key] = cq.Workplane("XY").text(ch, size, depth, fontPath=font, halign="center", valign="bottom").val()
    return _GLYPH[key]


def _line_glyphs(text, font, size, track):
    widths, heights = [], []
    for ch in text:
        bb = _glyph(ch, font, size, 1.0).BoundingBox()
        widths.append(max(bb.xlen, size * 0.25))
        heights.append(bb.ymax)
    return widths, sum(widths) + track * (len(text) - 1), max(heights)


def interface_band(y):
    """x range of the interface's flat top at plan y: the outside of the
    left wall -> the ramp's top edge (before its R 5)."""
    pts = outline_points(0.25)
    xl = None
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < 80 and (xl is None or x < xl):
                xl = x
    top = ramp_edge(RAMP_TOP_OFF)
    for (x0, y0), (x1, y1) in zip(top, top[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            return xl, x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    return xl, None


_LOGO = {}


def logo_layout():
    """The straight logo: two centred lines, the block centred in the back
    zone (vertically on LOGO_ZONE_Y's middle, horizontally on the band's
    middle there). Returns {"lines": [(text, font, size, track, cx, baseline, width, height)],
    "bbox": (x0, y0, x1, y1), "margins": (left, right, back, front)}."""
    if _LOGO:
        return _LOGO
    w1, W1, H1 = _line_glyphs("eTuttino", LOGO_FONT, LOGO_SIZE[0], LOGO_TRACK[0])
    w2, W2, H2 = _line_glyphs("POCKET", LOGO_FONT2, LOGO_SIZE[1], LOGO_TRACK[1])
    block_h = H1 + LOGO_GAP + H2
    ym = (LOGO_ZONE_Y[0] + LOGO_ZONE_Y[1]) / 2
    y0 = ym - block_h / 2                       # top of "eTuttino" (SPEC: smaller y = away from the player)
    b1 = y0 + H1                                # its baseline
    b2 = b1 + LOGO_GAP + H2
    xl, xr = interface_band(ym)
    cx = (xl + xr) / 2
    # margins: the narrowest band over each line's height
    def margin(width, ya, yb):
        lm, rm = 1e9, 1e9
        for k in range(11):
            y = ya + (yb - ya) * k / 10
            a, b = interface_band(y)
            lm = min(lm, cx - width / 2 - a)
            rm = min(rm, b - (cx + width / 2))
        return lm, rm
    m1, m2 = margin(W1, y0, b1), margin(W2, b2 - H2, b2)
    _LOGO.update({"lines": [("eTuttino", LOGO_FONT, LOGO_SIZE[0], LOGO_TRACK[0], cx, b1, W1, H1),
                            ("POCKET", LOGO_FONT2, LOGO_SIZE[1], LOGO_TRACK[1], cx, b2, W2, H2)],
                  "bbox": (cx - max(W1, W2) / 2, y0, cx + max(W1, W2) / 2, b2),
                  "margins": (round(min(m1[0], m2[0]), 2), round(min(m1[1], m2[1]), 2),
                              round(y0, 2), round(KNOB_Y - KNOB_D / 2 - b2, 2))})
    assert min(_LOGO["margins"][:2]) >= LOGO_MIN_MARGIN, _LOGO["margins"]
    return _LOGO


def logo_letters():
    """(char, font, size, x, y, up_deg) for the engraved logo: straight
    lines, each centred on the zone; (x, y) = the letter's centre on its
    baseline, up_deg = -90 (the letters' tops point away from the player)."""
    out = []
    for text, font, size, track, cx, base, W, _ in logo_layout()["lines"]:
        widths, _, _ = _line_glyphs(text, font, size, track)
        s = cx - W / 2
        for ch, w in zip(text, widths):
            out.append((ch, font, size, s + w / 2, base, -90.0))
            s += w + track
    return out


def logo_solid(z_top, depth):
    """The engraving cutter: the letters from z_top - depth up."""
    parts = []
    for ch, font, size, x, y, a in logo_letters():
        g = _glyph(ch, font, size, depth + 2.0)
        # drawn y-up; the SPEC frame is mirrored (y towards the player): mirror
        # the glyph so it reads right on the exported (mirrored) part, then
        # turn its top (now -y) to point along the radius
        g = g.mirror("XZ")
        g = g.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a + 90.0)
        parts.append(g.translate(cq.Vector(x, y, z_top - depth)))
    return fuse(parts)


def cable_wire(pts):
    return cq.Wire.makePolygon([cq.Vector(*p) for p in pts])


def vusb_wire_path():
    """The 26 AWG VBUS wire (PECAS vusb_wire): from the Teensy's VUSB pad
    (bottom, 6.2 in from the USB end, beside the VUSB-VIN cut: as the manual's
    Teensy model, CHECK on the real board) along the gap under the Teensy, out
    of the USB end, over the Audio Board's left edge (between its top, 12.3,
    and the plug, 14.35), down to J_VBUS (build_pocket_pcb: 18.5, 18.0)."""
    t = stack_parts()["teensy"][0]
    x0 = min(p[0] for p in t)
    yc = (min(p[1] for p in t) + max(p[1] for p in t)) / 2
    zt = Z_TEENSY_TOP - 1.6 - 0.6
    return [(x0 + 6.2, yc - 1.4, zt), (x0 + 0.8, yc - 1.4, Z_AB_TOP + 1.2), (STACK_XY[0] + 1.0, yc - 1.6, Z_AB_TOP + 1.0),
            (STACK_XY[0] - 1.5, yc - 1.9, 11.0), (24.0, 18.2, 9.0), (19.5, 18.0, Z_PCB_TOP + 1.2), (18.5, 18.0, Z_PCB_TOP + 0.6)]


def connector_boss_and_cuts():
    """The flat chord boss with the FPC female's block (tunnel, lip, window,
    outer recess, 2 M2 pilots) and the jack's facet (D8.2 hole, outer spot
    face, anti-rotation rib). Returns (adds, cuts, keepout): adds are
    intersected with the cavity; cuts and keepout go through the shell."""
    g = conn_geometry()
    n, fo = g["n"], g["fem_origin"]
    pw, pl, ph = FEM_POCKET
    bw, bfl, _ = FEM_BLOCK
    zb0, ztop = fem_block_rect()[1]
    # boss behind the face (the wall's bulge) + the block in front of it, up to the lid
    boss = local_solid(cq.Solid.makeBox(12.0, bw + 3.0, ztop + 1.0 - zb0, cq.Vector(-12.0, -(bw + 3.0) / 2, zb0 - FEM_Z)),
                       fo, n, FEM_Z)
    block = local_solid(cq.Solid.makeBox(pl, bw, ztop + 1.0 - zb0, cq.Vector(0.0, -bw / 2, zb0 - FEM_Z)), fo, n, FEM_Z)
    o = g["jack_origin"]
    jf = JACK_FACET
    facet = local_solid(cq.Solid.makeBox(12.0, jf[0], jf[1], cq.Vector(-12.0, -jf[0] / 2, -jf[1] / 2)), o, (1.0, 0.0), JACK_Z)
    rw, rl = JACK_RIB
    w, h, L = JACK_BODY
    rib = local_solid(cq.Solid.makeBox(rl, rw, 20.0, cq.Vector(0.0, -w / 2 - CONN_LID_CLR - rw, -h / 2 + 2.0)),
                      o, (1.0, 0.0), JACK_Z)
    adds = [boss, block, facet, rib]
    cuts = []
    # tunnel, open at the inner end
    cuts.append(local_solid(cq.Solid.makeBox(pl + 1.0, pw, ph, cq.Vector(0.0, -pw / 2, -ph / 2)), fo, n, FEM_Z))
    lt, lw, lh, lr = FEM_LIP
    cuts.append(local_solid(stadium(lw, lh, lr, -lt - 0.5, 0.5), fo, n, FEM_Z))
    hw_, hh, hr = FEM_HOLE
    cuts.append(local_solid(stadium(hw_, hh, hr, -15.0, -lt), fo, n, FEM_Z))
    rw2, rh2, rr2 = FEM_RECESS
    cuts.append(local_solid(stadium(rw2, rh2, rr2, -20.0, -FEM_WALL), fo, n, FEM_Z))
    sp, sd, sdep = FEM_SCREWS
    for y in (-sp / 2, sp / 2):
        cuts.append(local_solid(cq.Solid.makeCylinder(sd / 2, sdep + 0.01, cq.Vector(pl + 0.01, y, 0), cq.Vector(-1, 0, 0)),
                                fo, n, FEM_Z))
    cuts.append(local_solid(cq.Solid.makeCylinder(JACK_HOLE_D / 2, 15.0, cq.Vector(-14.0, 0, 0), cq.Vector(1, 0, 0)),
                            o, (1.0, 0.0), JACK_Z))
    cuts.append(local_solid(cq.Solid.makeCylinder(JACK_SPOT_D / 2, 15.0, cq.Vector(-JACK_WALL - 15.0, 0, 0), cq.Vector(1, 0, 0)),
                            o, (1.0, 0.0), JACK_Z))
    c = CONN_LID_CLR
    jk = local_solid(cq.Solid.makeBox(L + JACK_TABS + c, w + 2 * c, h + 2 * c, cq.Vector(0.0, -w / 2 - c, -h / 2 - c)),
                     o, (1.0, 0.0), JACK_Z)
    return adds, cuts, jk


def tab_dent():
    """(x0, y0, x1, y1, z_top) of the room the front tab needs in the box's
    back wall: the tab grown by TAB_CLR; y0 = the tab's back edge."""
    x0, y0, x1, y1 = CTRL_TABS[1]
    return x0 - TAB_CLR, y0, x1 + TAB_CLR, y1 + TAB_CLR, TAB_DENT_TOP


def speaker_box_walls():
    """Walls of the sealed back box, hanging from the lid down to
    SPK_BOX_BOTTOM, and the locating ring round the frame."""
    inner = spk_inner_contour()
    outer = S.offset(inner, BOX_WALL, 24)
    walls = poly_prism(outer, SPK_BOX_BOTTOM, 45.0).cut(poly_prism(inner, SPK_BOX_BOTTOM - 1, 46.0))
    # the dent for the controls board's front tab: a walled pocket pushed into
    # the box's back wall, open towards the back (the box stays sealed: the
    # dent's walls stand on the same glued floor)
    dx0, dy0, dx1, dy1, dz = tab_dent()
    shell_dent = box3(dx0 - BOX_WALL, dy0 - 5.0, SPK_BOX_BOTTOM, dx1 + BOX_WALL, dy1 + BOX_WALL, dz + BOX_WALL)
    walls = walls.fuse(shell_dent.intersect(poly_prism(outer, SPK_BOX_BOTTOM - 1, 46.0)))
    walls = walls.cut(box3(dx0, dy0 - 10.0, SPK_BOX_BOTTOM - 1, dx1, dy1, dz)).clean()
    # the ring is square to the lid (the speaker's axis), from the lid down SPK_RING_H
    r_ring = SPK_D / 2 + SPK_SEAT_CLR
    zf = speaker_face_z(SPK_C[1])
    ring = cq.Solid.makeCylinder(r_ring + SPK_RING_W, SPK_RING_H + 6.0, cq.Vector(0, 0, -SPK_RING_H))
    ring = ring.cut(cq.Solid.makeCylinder(r_ring, SPK_RING_H + 8.0, cq.Vector(0, 0, -SPK_RING_H - 1)))
    ring = ring.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -IF_SLOPE).translate(cq.Vector(SPK_C[0], SPK_C[1], zf))
    return walls, ring


def controls_posts():
    lid = z_interface(KNOB_Y, TOP_T)
    return [cyl(x, y, CTRL_TOP, lid + 0.5, POST_D) for x, y in CTRL_POSTS]


def bosses(body):
    return [cyl(x, y, FLOOR_T, BOSS_TOP.get((x, y), 60.0), BOSS_D).intersect(body) for x, y in screw_points()]


def teensy_button_xy():
    """The Teensy's program button in plan (see TEENSY_BTN_IN)."""
    t = stack_parts()["teensy"][0]
    u_far = max(p[0] for p in t)                 # the end away from the USB (STACK_ANGLE 0)
    yc = (min(p[1] for p in t) + max(p[1] for p in t)) / 2
    return (u_far - TEENSY_BTN_IN, yc)


def button_tube():
    """The guide tube under the pinhole: from the lid down to just above the Teensy."""
    x, y = teensy_button_xy()
    return cyl(x, y, Z_TEENSY_PARTS + BTN_TUBE_GAP, z_interface(y, TOP_T) + 0.5, BTN_TUBE_D)


def knob_recesses():
    """The round recesses in the lid under both knobs (SPEC v5 4)."""
    out = []
    for x, y in (VOLUME_XY, SELECT_XY):
        z = z_interface(y)
        out.append(cyl(x, y, z - KNOB_RECESS_DEPTH, z + 5.0, KNOB_RECESS_D))
    return out


def top_cuts():
    cuts = []
    vx, vy = VOLUME_XY
    cuts.append(cyl(vx, vy, 0, 50, POT_HOLE_D))
    if POT_PIN:
        px, py = vx + POT_PIN[0], vy + POT_PIN[1]
        zl = z_interface(py, TOP_T)
        cuts.append(cyl(px, py, zl - 0.01, zl + POT_PIN[3], POT_PIN[2]))
    cuts += knob_recesses()
    bx, by = teensy_button_xy()
    cuts.append(cyl(bx, by, Z_TEENSY_PARTS, 50, BTN_HOLE_D))
    cuts.append(cq.Solid.makeCone(BTN_HOLE_D / 2, BTN_HOLE_D / 2 + 0.6, 0.6, cq.Vector(bx, by, Z_IF - 0.6)))   # small lead-in
    cuts.append(cyl(SELECT_XY[0], SELECT_XY[1], 0, 50, SHAFT_HOLE_D))
    cuts.append(cyl(LED_XY[0], LED_XY[1], 0, 50, LED_HOLE_D))
    cuts += [cyl(x, y, 18.0, 50, GRILLE_HOLE_D) for x, y in grille_holes()]
    return cuts


def spk_wire_hole():
    r_in = SPK_D / 2 + SPK_SEAT_CLR + BOX_GROW[1]
    wx = SPK_C[0] + BOX_GROW[0] + r_in
    return cq.Solid.makeCylinder(1.0, 6.0, cq.Vector(wx - 2.0, SPK_C[1] - 4.0, SPK_BOX_BOTTOM + 2.0), cq.Vector(1, 0, 0))


_SHELL = {}


def shell():
    """The Seixo top shell."""
    if "s" in _SHELL:
        return _SHELL["s"]
    body = outer_body()
    cav = cavity()
    s = body.cut(cav)
    walls, ring = speaker_box_walls()
    padds, pcuts, keep = connector_boss_and_cuts()
    adds = [walls.intersect(cav), ring.intersect(cav)] + [a.intersect(cav) for a in padds]
    adds += [p.intersect(cav) for p in controls_posts()]
    adds.append(button_tube().intersect(cav))
    adds += bosses(body)
    s = s.fuse(*adds).clean()
    s = s.cut(rounded_opening_cutter())
    s = sorted(s.Solids(), key=lambda x: x.Volume(), reverse=True)[0]
    cuts = top_cuts() + pcuts + [keep]
    cuts.append(logo_solid(Z_IF, LOGO_DEPTH))
    cuts += [cyl(x, y, FLOOR_T - 0.01, FLOOR_T + 8.0, PILOT_D) for x, y in screw_points()]
    cuts += [cyl(x, y, CTRL_TOP - 0.01, CTRL_TOP + POST_PILOT_DEPTH, POST_PILOT_D) for x, y in CTRL_POSTS]
    cuts.append(spk_wire_hole())
    s = s.cut(fuse(cuts)).clean()
    _SHELL["s"] = s
    return s


# ================================================================ bottom plate, hatch, box floor, plate
FEET = [(30.0, 14.0), (80.0, 90.0), (225.0, 14.0), (225.0, 86.0)]


def fundo():
    """Bottom plate inside the walls: board pillars, the battery bay (walls
    + roof) round the hatch opening, countersunk case screws, feet."""
    t = FLOOR_T
    plate = outline_solid(0.0, t, WALL + FUNDO_CLR)
    inside, outside = battery_rects()
    p_in, p_out = pocket_rects()
    bay = poly_prism(outside, t - 0.01, BATT_ROOF_Z[1]).fuse(poly_prism(p_out, t - 0.01, BATT_ROOF_Z[1]))
    bay = bay.cut(poly_prism(inside, t - 0.02, BATT_ROOF_Z[0])).cut(poly_prism(p_in, t - 0.02, BATT_ROOF_Z[0]))
    adds = [bay]
    for x, y in HATCH_SCREWS:
        adds.append(cyl(x, y, t - 0.01, BATT_Z[1], HATCH_BOSS_D))
    for x, y in pillar_points():
        adds.append(cyl(x, y, t - 0.01, Z_PCB_BOT, PILLAR_D))
    for x, y in BOARD_SCREWS:
        adds.append(cyl(x, y, t - 0.01, Z_PCB_BOT, SCREW_PILLAR_D))
    plate = plate.fuse(*adds).clean()
    cuts = [poly_prism(inside, -1.0, t + 0.5)]               # the hatch opening
    x0, y0, x1, y1 = hatch_rect(HATCH_CLR)
    cuts.append(box3(x0, y0, -1.0, x1, y1, HATCH_T).intersect(outline_solid(-2.0, 5.0, WALL + FUNDO_CLR - 0.5)))   # recess for the door
    for x, y in HATCH_SCREWS:
        cuts.append(cyl(x, y, 1.0, BATT_Z[1] - 0.5, 1.7))
    py0 = BATT_POCKET[2]
    cuts.append(box3(BATT_SLOT[0], py0 - BATT_WALL - 0.5, BATT_ROOF_Z[1] - 4.0,
                     BATT_SLOT[1], py0 + 2.5, BATT_ROOF_Z[1] + 1.0))   # the pigtail's way in: back wall + roof
    for x, y in BOARD_SCREWS:
        cuts.append(cyl(x, y, -1, Z_PCB_BOT + 1, M2_CLR_D))
        cuts.append(cyl(x, y, -1, M2_HEAD_DEPTH, M2_HEAD_D))
    for x, y in screw_points():
        cuts.append(cyl(x, y, -1, t + 1, SCREW_CLR_D))
        cuts.append(cyl(x, y, -1, HEAD_DEPTH, HEAD_D))
    for fx, fy in FEET:
        cuts.append(cyl(fx, fy, -1, FOOT_DEPTH, FOOT_D))
    return plate.cut(fuse(cuts)).clean()


def hatch():
    x0, y0, x1, y1 = hatch_rect(0.0)
    door = cq.Workplane().add(box3(x0, y0, 0.0, x1, y1, HATCH_T)).edges("|Z").fillet(1.5).val()
    door = door.intersect(outline_solid(-1.0, 5.0, WALL + FUNDO_CLR))      # the front-left corner follows the outline
    cuts = []
    for x, y in HATCH_SCREWS:
        cuts.append(cyl(x, y, -1, 2, 2.3))
        cuts.append(cq.Solid.makeCone(2.2, 1.15, 1.05, cq.Vector(x, y, -0.001)))
    cuts.append(cyl((x0 + x1) / 2, y0 - 3.5, -1, 2, 10.0))   # finger notch at the back edge
    return door.cut(fuse(cuts)).clean()


def box_floor():
    """The box's floor, glued under its walls; where the box meets the
    case's front wall the floor stops 0.2 short of it (glue fills that)."""
    outer = S.offset(spk_inner_contour(), BOX_WALL, 24)
    fl = poly_prism(outer, SPK_BOX_BOTTOM - BOX_FLOOR_T, SPK_BOX_BOTTOM)
    return fl.intersect(outline_solid(0.0, 20.0, WALL + 0.2))


def switch_plate():
    p = contour_wp(hex_contour(PLATE_OVERLAP), Z_PLATE_TOP - PLATE_T).extrude(PLATE_T).val()
    cuts = [box3(x - 7, y - 7, 0, x + 7, y + 7, 30) for _, _, x, y, _ in keys()]
    cuts += [cyl(x, y, 0, 30, BOSS_D + 1.0) for x, y in screw_points()]
    return p.cut(fuse(cuts)).clean()


# ================================================================ the main board's room
def board_face():
    """The main board's outline as a face: the inside of the walls less
    PCB_CLR, without the front-left corner where the battery bay (and its
    hatch bosses) stand, notched round the screw columns."""
    inside, outside = battery_rects()
    bx1 = max(p[0] for p in outside) + PCB_CLR
    by0 = min(p[1] for p in outside) - PCB_CLR
    _, p_out = pocket_rects()
    px1 = max(p[0] for p in p_out) + PCB_CLR
    py0 = min(p[1] for p in p_out) - PCB_CLR
    w = pieces_wire(outline_pieces()).wires().val().offset2D(-(WALL + PCB_CLR))[0]
    face = cq.Face.makeFromWires(w)
    for x1, y0 in ((bx1, by0), (px1, py0)):
        notch = cq.Face.makeFromWires(cq.Wire.makePolygon(
            [cq.Vector(-10, y0, 0), cq.Vector(x1, y0, 0), cq.Vector(x1, 120, 0), cq.Vector(-10, 120, 0)], close=True))
        face = face.cut(notch)
    for x, y in screw_points():
        face = face.cut(cq.Face.makeFromWires(cq.Wire.makeCircle(BOSS_D / 2 + 0.5, cq.Vector(x, y, 0), cq.Vector(0, 0, 1))))
    face = max(face.Faces(), key=lambda f: f.Area())
    return face


def wire_points(w, step=0.5):
    n = max(16, int(w.Length() / step))
    return [(round(p.x, 3), round(p.y, 3)) for p in w.positions([i / n for i in range(n)])]


def board_outline(step=0.5):
    return wire_points(board_face().outerWire(), step)


def main_board_solid():
    f = board_face()
    return cq.Solid.extrudeLinear(f.translate(cq.Vector(0, 0, Z_PCB_BOT)), cq.Vector(0, 0, PCB_T))


# ================================================================ export
def to_file(shape):
    """SPEC coordinates -> the files' right-handed ones."""
    return shape.mirror("XZ", (0, WIDTH / 2, 0))


def export(shape, name, tol=0.05, mirror=True):
    os.makedirs(OUT, exist_ok=True)
    assert shape.isValid(), name
    if mirror:
        shape = to_file(shape)
    cq.exporters.export(cq.Workplane().add(shape), os.path.join(OUT, name + ".step"))
    cq.exporters.export(cq.Workplane().add(shape), os.path.join(OUT, name + ".stl"), tolerance=tol, angularTolerance=0.2)
    bb = shape.BoundingBox()
    print("%-20s %6.1f x %5.1f x %4.1f mm  %7.2f cm3" % (name, bb.xlen, bb.ylen, bb.zlen, shape.Volume() / 1000))


# what each printed / bought part is made of (SPEC v4 change 5): the top shell
# in resin for the engraved logo; the rest in MJF PA12 (stronger, cheaper)
MATERIALS = {
    "seixo_tampa": ("resina (SLA/DLP, engenharia: Tough/Grey)", 1, "casca de cima: logo de 0,4, grade, rebaixos dos knobs, janelas do micro-USB e do fone"),
    "seixo_fundo": ("MJF PA12", 1, "fundo com os pilares da placa e o berço da bateria"),
    "seixo_tampa_bateria": ("MJF PA12", 1, "tampinha da bateria, 2 parafusos M2"),
    "seixo_caixa_fundo": ("MJF PA12", 1, "fundo da caixa do alto-falante, colado e vedado"),
    "plate": ("FR-4 1,6 mm (Gerber da eletrônica / plate.dxf)", 1, "placa dos switches"),
    "seixo_trava_usb": ("MJF PA12", 1, "trava da fêmea micro-B (FPC) no túnel, 2 parafusos M2 x 5"),
    "seixo_chave_porca": ("MJF PA12", 1, "chave da porca M7 do potenciômetro (entra no rebaixo de Ø 14)"),
    "keycap_natural": ("resina branca", None, "capas das naturais (sem Dó/Fá)"),
    "keycap_sharp": ("resina preta", None, "capas dos sustenidos"),
    "keycap_cf": ("resina branca", None, "capas de Dó e Fá, xadrez diagonal em relevo"),
    "keycap_test_4": ("resina (branca)", 1, "teste: 4 capas num canal, antes das 28"),
}


def cap_counts():
    """How many caps of each kind the Pocket takes."""
    out = {"natural": 0, "sharp": 0, "cf": 0}
    for _, _, _, _, kind in keys():
        out[kind] += 1
    return out


def export_caps():
    """The eTuttino's caps (same heights: keycap.py run against this
    module's parameters), into out/ for the Pocket's file set."""
    sys.modules.setdefault("case", sys.modules[__name__])     # keycap's "import case" = this module, not the eTuttino's
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "case")))
    import keycap as K
    assert K.C.Z_KEY_TOP == Z_KEY_TOP and K.C.WIDTH == WIDTH
    for kind in ("natural", "sharp", "cf"):
        export(K.cap(kind), "keycap_" + kind, tol=0.01, mirror=False)
    export(K.test_print(), "keycap_test_4", tol=0.01, mirror=False)


def nut_tool():
    """A printed nut driver for the pot nut in its D14 recess: hex socket at
    one end, a bore through for the shaft, round outside (OD < the recess)."""
    af, od, L = NUT_TOOL
    t = cq.Solid.makeCylinder(od / 2, L, cq.Vector(0, 0, 0))
    hexs = cq.Workplane("XY").polygon(6, af / math.cos(math.radians(30))).extrude(POT_NUT_T + 1.5).val()
    t = t.cut(hexs).cut(cq.Solid.makeCylinder(7.8 / 2, L + 2, cq.Vector(0, 0, -1)))
    grip = [cq.Solid.makeCylinder(0.8, L - 8.0, cq.Vector(od / 2 * math.cos(a), od / 2 * math.sin(a), 6.0))
            for a in [k * math.pi / 6 for k in range(12)]]
    return t.cut(fuse(grip)).clean()


def build_all():
    return {
        "seixo_tampa": shell(),
        "seixo_fundo": fundo(),
        "seixo_tampa_bateria": hatch(),
        "seixo_caixa_fundo": box_floor(),
        "plate": switch_plate(),
        "seixo_chave_porca": nut_tool(),
        "seixo_trava_usb": trava(),
    }


def main():
    print("length %.2f mm, plan vs shape.py %.3f mm" % (length(), check_plan()))
    parts = build_all()
    for name, shp in parts.items():
        export(shp, name)
    export_caps()
    flat = cq.Workplane().add(to_file(parts["plate"])).faces("<Z")
    cq.exporters.export(flat, os.path.join(OUT, "plate.dxf"))
    n, ratio = grille_open_ratio()
    print("grille: %d holes, %.0f %% of the cone" % (n, ratio * 100))


if __name__ == "__main__":
    main()
