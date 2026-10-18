"""The room the Pocket's Seixo case leaves for the main board (SPEC v4, F1):

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/pcb_envelope.py

writes out/pcb_envelope.json (the contract with the electronics: the Pocket
board scripts read it, as the eTuttino's generate.py / build_pcb.py read
etutti/hardware/case/out/pcb_envelope.json) and renders/pcb_envelope.png.

Same schema as the eTuttino's envelope, plus the Pocket's own blocks
(battery, panel, speaker, cables, connector zones). Frame: SPEC
coordinates, x right from the case's leftmost point, y towards the player,
mm = KiCad's top view (y down the screen, the player at the bottom).
Heights are absolute z (table = 0) unless a key says "above_pcb".

  outline          the board's edge: the inside of the walls less 0.5,
                   without the front-left corner where the battery bay
                   stands (the bay is never under the board), notched
                   round the case's screw columns
  boss_keepouts    the case's screw columns (bottom plate -> top shell)
  supports         pillars on the bottom plate the board rests on: no
                   parts, pads or vias on the BACK inside these circles
  mounting_holes   2 x M2 from below through the bigger pillars, nut on top
  max_below        parts on the back: up to this (to the bottom plate)
  plate_outline    the FR-4 switch plate's edge; under it, parts on top up to plate_clear
  levels           {h: [{outer, holes}]}: where parts on TOP of the board up to h
                   mm tall fit, with every fixed part of the case and the
                   interface taken out (the stack is NOT taken out: it is
                   the board's own; see stack)
  keys             every key: note, row, centre (switch + Hall sensor under it)
  stack            Teensy 4.0 + Audio Board Rev D, the LOW stack, its pins
  controls         the controls board under the lid (pot on its own vertical board)
  panel            the USB-C + jack board on the back-left wall
  battery          the bay, its hatch, where its 3 wires come out
  speaker          where it sits and where its 2 wires leave the sealed box
  cables           the zones the cables take to the main board
  connector_zones  suggested spots for J_BAT, J_SPK, J_PNL, J_CTL (PECAS main_board_connectors)
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import fit_check as FC  # noqa: E402

S = C.S
LEVELS = (2.0, 3.0, 4.5, 6.5, 9.0, 10.5, 12.0, 15.0, 18.0, 21.0)


def section(solid, z):
    """The solid's section at z: [{"outer": polygon, "holes": [polygons]}]."""
    slab = solid.intersect(C.box3(-50, -50, z - 0.01, 320, 150, z + 0.01))
    polys = []
    for f in slab.Faces():
        bb = f.BoundingBox()
        if bb.zlen < 1e-4 and abs(bb.zmin - (z - 0.01)) < 1e-4 and f.Area() > 1.0:       # the slab's bottom faces
            polys.append({"outer": C.wire_points(f.outerWire(), 1.0),
                          "holes": [C.wire_points(w, 1.0) for w in f.innerWires()]})
    return polys


def obstacles():
    """Everything fixed in the case that is not the main board's own."""
    pc = FC.pecas()
    pan, _ = FC.panel_solids(pc)
    ctl = FC.controls_solids(pc)
    _, swollen, bplug = FC.battery(pc)
    _, full, _ = FC.speaker(pc)
    a0, b0, a1, b1 = C.CTRL_CABLE
    cable = C.box3(a0, b0, C.Z_PCB_TOP + 7.0, a1, b1, 40.0)       # the controls cable drops here (its plug sits lower)
    plate_zone = C.contour_wp(C.hex_contour(C.PLATE_OVERLAP), C.Z_PLATE_TOP - C.PLATE_T).extrude(10.0).val()   # the plate and the keys above it
    parts = [C.shell(), C.fundo(), plate_zone, C.box_floor(), swollen, bplug, full,
             pan["panel_board"], pan["usb_c"], pan["jack"], pan["panel_screw_head"], cable] + list(ctl.values())
    return parts


def envelope():
    zt = C.Z_PCB_TOP
    cav = C.outline_solid(C.FLOOR_T, C.Z_IF, C.WALL).intersect(C.cavity())
    free = cav
    for o in obstacles():
        free = free.cut(o)
    levels = {"%.1f" % h: section(free, zt + h - 0.02) for h in LEVELS}
    plate = C.switch_plate()
    zb = C.Z_PLATE_TOP - C.PLATE_T
    plate_face = [f for f in plate.Faces() if f.BoundingBox().zlen < 1e-4 and abs(f.BoundingBox().zmin - zb) < 1e-4][0]
    st = C.stack_parts()
    ab = st["audio_board"][0]
    tcy = C.STACK_XY[1] + C.PAST_VIN + 7.62
    pg = C.panel_geometry()
    at = pg["at"]
    inside, outside = C.battery_rects()
    l, w, _ = C.BATT_IN
    xe = C.BATT_C[0] - l / 2
    pc = FC.pecas()
    r = lambda v, d=3: round(v, d)
    rp = lambda pts: [[r(x), r(y)] for x, y in pts]
    return {
        "spec": "pocket SPEC v4, task F1 (Seixo, variant B)",
        "frame": "SPEC: x right from the case's leftmost point, y towards the player, mm (= KiCad top view)",
        "case_length": r(C.length(), 2),
        "z_pcb_top": zt, "z_pcb_bottom": C.Z_PCB_BOT, "pcb_thickness": r(C.PCB_T, 2),
        "outline": C.board_outline(0.5),
        "boss_keepouts": [{"x": x, "y": r(y), "r": C.BOSS_D / 2 + 0.5,
                           "top_z": C.BOSS_TOP.get((x, y), "lid")} for x, y in C.screw_points()],
        "supports": [{"x": r(x), "y": r(y), "r": C.PILLAR_D / 2 + 0.5} for x, y in C.pillar_points()]
        + [{"x": x, "y": r(y), "r": C.SCREW_PILLAR_D / 2 + 0.5, "screw": True} for x, y in C.BOARD_SCREWS],
        "mounting_holes": [{"x": x, "y": r(y), "d": 2.2, "keepout": C.SCREW_PILLAR_D / 2 + 0.5,
                            "note": "M2 from below through the bottom plate's pillar, nut on top of the board"}
                           for x, y in C.BOARD_SCREWS],
        "max_below": r(C.Z_PCB_BOT - C.FLOOR_T, 2),
        "plate_outline": C.wire_points(plate_face.outerWire(), 1.0),
        "plate_cutout": 14.0,
        "plate_clear": r(C.Z_PLATE_TOP - C.PLATE_T - zt, 2),
        "plate_thickness": C.PLATE_T,
        "levels": levels,
        "levels_note": "h = height above the board's top face; each polygon is free room at that height "
                       "(the case, its fixed parts, the speaker box, the battery bay, the panel and controls boards taken out)",
        "pitch": C.P, "row_pitch": r(S.ROW_PITCH, 4),
        "keys": [{"n": n, "note": C.note_name(n), "row": row, "x": r(x, 4), "y": r(y, 4), "kind": kind}
                 for n, row, x, y, kind in C.keys()],
        "stack": {
            "kind": "LOW (PECAS stack.low): Teensy soldered straight on the Audio Board with long headers",
            "audio_board": [r(min(p[0] for p in ab)), r(min(p[1] for p in ab)), r(max(p[0] for p in ab)), r(max(p[1] for p in ab))],
            "angle": C.STACK_ANGLE,
            "pin_rows_y": [r(tcy - 7.62), r(tcy + 7.62)],
            "pin1_x": r(C.STACK_XY[0] + C.PAST_USB),
            "pins_per_row": 14, "pin_pitch": 2.54,
            "usb_end": "left (x small): the Teensy's micro-B faces the left wall", "vin_row": "back (smaller y)",
            "audio_lift": C.AUDIO_LIFT,
            "z": {"audio_bottom": r(C.Z_AB, 2), "audio_top": r(C.Z_AB_TOP, 2), "teensy_top": r(C.Z_TEENSY_TOP, 2),
                  "usb_top": r(C.Z_USB_TOP, 2), "height_audio_bottom_to_usb_top": C.STACK_H},
            "teensy": rp(st["teensy"][0]), "ab_jack": rp(st["ab_jack"][0]),
            "usb_plug": {"rect": rp(st["usb_plug"][0]), "z": [r(v, 2) for v in st["usb_plug"][1]],
                         "note": "90 deg micro-B overmould 11 x 11 x 7.5 (PECAS micro_b_link); its cable goes up/back to the panel board"},
        },
        "controls": {
            "rect": list(C.CTRL_BOARD), "tabs": [list(t) for t in C.CTRL_TABS],
            "tabs_note": "the EC11E's two tabs (E2b): the back one over the Audio Board, the front one in a dent of the speaker box's "
                         "back wall (x %.1f-%.1f, y <= %.1f, z <= %.1f, open below to the box floor at z %.2f)" % (
                             C.tab_dent()[0], C.tab_dent()[2], C.tab_dent()[3], C.tab_dent()[4], C.SPK_BOX_BOTTOM),
            "top_z": C.CTRL_TOP, "thickness": C.CTRL_T, "legs_below": C.CTRL_LEGS,
            "encoder": list(C.SELECT_XY), "encoder_rot": "as the eTuttino (A/B/C to the back)",
            "led": list(C.LED_XY), "led_top_z": r(C.Z_IF - 0.5, 2),
            "holes": [list(p) for p in C.CTRL_POSTS], "hole_d": 2.2, "post_d": C.POST_D,
            "connector": {"rect": list(C.CTRL_CONN), "note": "10-way SH header on top, 12 along y, cable leaves +x then drops in cables.controls"},
            "pot": {"shaft": list(C.VOLUME_XY), "body": list(C.POT_BODY[:4]), "body_z": list(C.POT_BODY[4:]),
                    "board": list(C.POT_BOARD[:4]), "board_z": list(C.POT_BOARD[4:]), "legs_to_x": C.POT_LEGS_X,
                    "lid_hole_d": C.POT_HOLE_D,
                    "anti_rotation_hole": {"xy": [r(C.VOLUME_XY[0] + C.POT_PIN[0]), r(C.VOLUME_XY[1] + C.POT_PIN[1])],
                                           "d": C.POT_PIN[2], "depth": C.POT_PIN[3]},
                    "note": "horizontal-type 9 mm switched pot on a VERTICAL board right of the shaft (x 21.62-23.22), its body to the left, "
                            "M7 bushing nutted on the lid; the pot board meets the controls board's left edge at 90 deg"},
        },
        "panel": {
            "board": rp(pg["board"]), "z": [r(C.PANEL_Z_TOP - C.PANEL_T, 2), C.PANEL_Z_TOP],
            "nothing_below": True, "above_max": pc["panel_board"]["body"]["above_board_max"],
            "front_edge": [rp([pg["at"](-15, 0)])[0], rp([pg["at"](15, 0)])[0]],
            "inward_normal": [r(v, 4) for v in pg["n"]], "along": [r(v, 4) for v in pg["t"]],
            "usb_c": {"xy": rp([at(C.PANEL_USB_S, 0)])[0], "z": r(C.USB_C_ZC, 2), "hole": list(C.USB_C_HOLE),
                      "wall_at_hole": C.USB_C_WALL, "outer_recess": list(C.USB_C_RECESS),
                      "front_past_board_edge": r(C.USB_C_WALL - 0.15, 2)},
            "jack": {"part": "Same Sky SJ1-3525N", "xy": rp([at(C.PANEL_JACK_S, 0)])[0], "z": r(C.JACK_ZC, 2), "hole_d": C.JACK_HOLE_D,
                     "wall_at_hole": C.JACK_WALL, "outer_spot_face_d": C.JACK_SPOT_D,
                     "outer_spot_face_depth": r(pg["wall_jack"] - C.JACK_WALL, 2),
                     "barrel_front_past_board_edge": 1.35},
            "holes": [{"kind": kind, "xy": rp([at(s, d)])[0], "uv": [r(s + 15.0, 2), r(d, 2)], "d": C.PANEL_SCREW_D,
                       **({"post_d": C.PANEL_POST_D, "post_foot_d": C.PANEL_POST_FOOT[0], "post_foot_h": C.PANEL_POST_FOOT[1],
                           "pin_d": C.PANEL_PIN_D, "pin_len": C.PANEL_PIN_L,
                           "note": "LOCATING PIN from the lid post, from above; stops 0.2 short of the board's underside; nothing under the board"}
                          if kind == "pin" else
                          {"rib_w_across_u": C.PANEL_RIB_W, "rib_v": [-8.0, r(d + C.PANEL_RIB_W / 2, 2)], "pilot_d": C.PANEL_PILOT_D,
                           "head_under_board": list(C.PANEL_HEAD),
                           "note": "M2 x 6 self-tapping FROM BELOW into a rib of the lid that joins the wall boss; the rib lands on the "
                                   "board TOP over u %.2f-%.2f, v 0-%.2f: keep parts out of that strip" % (
                                       s + 15 - C.PANEL_RIB_W / 2, s + 15 + C.PANEL_RIB_W / 2, d + C.PANEL_RIB_W / 2)})}
                      for kind, s, d in C.PANEL_HOLES],
            "front_ledge": {"depth_v": C.PANEL_LEDGE[0], "thickness": C.PANEL_LEDGE[1],
                            "note": "the board's front edge rests on a ledge 0.8 deep along its full 30 mm (clear of the USB-C front legs at v 1.15-2.35)"},
            "note": "board top at z %.1f: it passes 0.45 over the Teensy's micro-B plug, so NO parts on its underside; "
                    "front edge on the flat boss of the wall, M2 screws from below into posts from the lid" % C.PANEL_Z_TOP,
        },
        "battery": {
            "bay_inside": rp(inside), "bay_outside": rp(outside), "z_inside": [C.BATT_Z[0], C.BATT_Z[1]],
            "roof_z": [r(v, 2) for v in C.BATT_ROOF_Z], "board_notch": "the outline leaves out x < %.2f, y > %.2f and, for the connector pocket, x < %.2f, y > %.2f" % (
                max(p[0] for p in outside) + C.PCB_CLR, min(p[1] for p in outside) - C.PCB_CLR,
                max(p[0] for p in C.pocket_rects()[1]) + C.PCB_CLR, min(p[1] for p in C.pocket_rects()[1]) - C.PCB_CLR),
            "connector_pocket": {"inside": rp(C.pocket_rects()[0]), "outside": rp(C.pocket_rects()[1]), "z_inside": [C.BATT_Z[0], C.BATT_Z[1]],
                                 "size": [r(C.BATT_POCKET[1] - C.BATT_POCKET[0], 2), r(C.BATT_C[1] - C.BATT_IN[1] / 2 - C.BATT_POCKET[2], 2),
                                          r(C.BATT_Z[1] - C.BATT_Z[0], 2)],
                                 "note": "the battery's PHR-3 mates here with the pigtail's in-line male, lying flat, axis along x "
                                         "(PECAS connector_pocket_v4 >= 14.5 x 9.0 x 6.0); open to the cradle along its front for the battery's "
                                         "wires; pull the battery out of the hatch and unplug, without opening the lid"},
            "pigtail_way_in": {"rect": [C.BATT_SLOT[0], r(C.BATT_POCKET[2] - C.BATT_WALL - 0.5), C.BATT_SLOT[1], r(C.BATT_POCKET[2] + 2.5)],
                               "z": [r(C.BATT_ROOF_Z[1] - 4.0, 2), r(C.BATT_ROOF_Z[1], 2)],
                               "note": "through the pocket's back wall and roof, from J_BAT (or pads) in connector_zones.back_left"},
            "hatch_screws": [[x, r(y)] for x, y in C.HATCH_SCREWS],
        },
        "speaker": {"centre": list(C.SPK_C), "frame_d": C.SPK_D, "face_z_at_centre": r(C.speaker_face_z(C.SPK_C[1]), 2),
                    "tilt_deg": C.IF_SLOPE, "box_inside": rp(C.spk_inner_contour()), "box_bottom_z": r(C.SPK_BOX_BOTTOM - C.BOX_FLOOR_T, 2),
                    "wire_hole": {"xy": [r(C.SPK_C[0] + C.BOX_GROW[0] + C.SPK_D / 2 + C.SPK_SEAT_CLR + C.BOX_GROW[1] + C.BOX_WALL), r(C.SPK_C[1] - 4.0)],
                                  "z": r(C.SPK_BOX_BOTTOM + 2.0, 2), "d": 2.0, "note": "sealed with glue after threading the 2 wires"}},
        "cables": {
            "controls": {"rect": list(C.CTRL_CABLE), "note": "the 10-way SH cable drops here from the controls board to J_CTL"},
            "panel": "micro-B cable (~40) from the panel board's back edge to the Teensy's plug; SH-8 (~100) to J_PNL",
            "battery": "3 wires (~60) from the bay's wire exit to J_BAT",
            "speaker": "2 wires (152) from the box's wire hole to J_SPK",
        },
        "connector_zones": {
            "back_left": {"rect": [11.0, 16.0, 19.8, 34.5], "z_top_max": 21.9,
                          "for": ["J_BAT", "J_SPK", "J_PNL"],
                          "note": "under the panel board (nothing on its underside), left of the Teensy's plug: "
                                  "PH plugs (10.5 tall) and the SH-8 fit; check the exact edge against levels['10.5']"},
            "J_CTL": {"rect": [C.CTRL_CABLE[0], 40.95, 64.0, r(min(p[1] for p in outside) - C.PCB_CLR, 2)], "z_top_max": 14.0,
                      "note": "SH-10 vertical (4.25 + plug) between the Audio Board's front edge and the battery notch"},
        },
    }


def plot(env, path):
    import pyvista as pv
    import numpy as np
    pl = pv.Plotter(off_screen=True, window_size=(2000, 900))
    pl.set_background("#f3f1ec")

    def poly(pts, color, width=2):
        a = np.array([(x, C.WIDTH - y, 0.0) for x, y in list(pts) + list(pts[:1])])
        pl.add_mesh(pv.lines_from_points(a), color=color, line_width=width)

    def circle(x, y, rr, color, width=2):
        poly([(x + rr * math.cos(t / 24 * 2 * math.pi), y + rr * math.sin(t / 24 * 2 * math.pi)) for t in range(24)], color, width)
    poly([(x, y) for x, y in C.outline_points(1.0)], "#4a443c", 2)
    poly(env["outline"], "#1d6b3a", 4)
    poly(env["plate_outline"], "#111111", 2)
    shades = ["#d9d3c6", "#c9c2b4", "#b5ad9c", "#a19884", "#8d836c", "#796e55", "#655a40", "#51472c", "#3d351f", "#2a2412"]
    for (h, polys), col in zip(sorted(env["levels"].items(), key=lambda kv: float(kv[0])), shades):
        for p in polys:
            poly(p["outer"], col, 1)
            for hh in p["holes"]:
                poly(hh, col, 1)
    for b in env["boss_keepouts"]:
        circle(b["x"], b["y"], b["r"], "#c0392b", 3)
    for s in env["supports"]:
        circle(s["x"], s["y"], s["r"], "#2471a3", 3)
    for k in env["keys"]:
        x, y = k["x"], k["y"]
        poly([(x - 7, y - 7), (x + 7, y - 7), (x + 7, y + 7), (x - 7, y + 7)], "#777777", 1)
    x0, y0, x1, y1 = env["stack"]["audio_board"]
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#16a085", 3)
    poly(env["stack"]["teensy"], "#16a085", 2)
    poly(env["stack"]["usb_plug"]["rect"], "#16a085", 2)
    x0, y0, x1, y1 = env["controls"]["rect"]
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#8e44ad", 3)
    for x0, y0, x1, y1 in env["controls"]["tabs"]:
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#8e44ad", 3)
    poly(env["panel"]["board"], "#2e86c1", 3)
    poly(env["battery"]["bay_outside"], "#d35400", 3)
    poly(env["battery"]["connector_pocket"]["outside"], "#d35400", 3)
    for nm, z in env["connector_zones"].items():
        x0, y0, x1, y1 = z["rect"]
        poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#f1c40f", 2)
    pl.camera_position = [(C.length() / 2, 50, 500), (C.length() / 2, 50, 0), (0, 1, 0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = 56
    pl.add_text("Pocket PCB envelope (SPEC v4 F1): board outline green, plate black, free room brown (darker = taller), "
                "columns red, pillars blue, stack teal, controls purple, panel blue, battery bay orange, connector zones yellow",
                font_size=9, color="#333333")
    pl.screenshot(path)
    pl.close()


def main():
    env = envelope()
    os.makedirs(C.OUT, exist_ok=True)
    with open(os.path.join(C.OUT, "pcb_envelope.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=1)
    plot(env, os.path.join(HERE, "renders", "pcb_envelope.png"))
    xs = [p[0] for p in env["outline"]]
    print("outline x %.1f..%.1f, %d points; levels %s" % (min(xs), max(xs), len(env["outline"]),
          {h: len(p) for h, p in env["levels"].items()}))


if __name__ == "__main__":
    main()
