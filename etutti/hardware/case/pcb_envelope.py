"""The room the case leaves for the main board (SPEC v7, item 9.2):

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe pcb_envelope.py

writes out/pcb_envelope.json (read by etutti/hardware/generate.py and
build_pcb.py, which run on plain / KiCad Python: no CadQuery needed there)
and renders/pcb_envelope.png (a plan of it).

Frame: SPEC coordinates, x right, y towards the player, in mm. That is
also KiCad's top view (y down the screen, the player at the bottom), so
the numbers go into the board as they are.

One board fits both versions: the outline is the Madeira's cavity (4 mm
walls; the Seixo's is larger) less PCB_CLR, with notches round the screw
bosses. Heights are above the board's top face (z = case.Z_PCB_TOP):

  outline               the board's edge (notched round the bosses)
  boss_keepouts         screw columns from the bottom plate to the top:
                        the board is notched round them
  supports              pillars on the bottom plate the board rests on:
                        no parts on the BACK inside these circles
  max_below             parts on the back: up to this (to the bottom plate)
  plate_outline         the switch plate's edge (as case.py cuts it): under
                        it, parts on top up to plate_clear (the plate's underside)
  levels                {h: [polygons]}: where parts on top up to h mm tall
                        fit (cavity sections at z_pcb_top + h). Outside the
                        plate, up to the lid (h 5.0) fits everywhere; higher
                        only under the interface and the ramp.
  keys                  every key: note, row, centre (switch + Hall sensor
                        under it)
  stack, sub_board,     the parts placed in fit_check.py, whose footprints
  panel                 the board has to respect
  mounting_holes        (v8) the two M2 holes over the screw pillars
  controls              (v8) the controls board: rectangle, parts, its two
                        M2 holes (the lid's posts), its top's z per version
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import fit_check as F  # noqa: E402

PCB_CLR = 0.5            # board edge to the inside of the walls
LEVELS = (5.0, 6.5, 9.0, 12.0, 15.0, 18.0, 21.0)


def wire_points(w, step=1.0):
    """A closed wire as an ordered polygon (sampled along the whole wire, so
    the edges' own orientations don't matter)."""
    n = max(8, int(w.Length() / step))
    return [(round(p.x, 3), round(p.y, 3)) for p in w.positions([i / n for i in range(n)])]


def section(solid, z):
    """Outer outlines of a solid's section at height z."""
    slab = solid.intersect(C.box3(-50, -50, z - 0.01, 450, 150, z + 0.01))
    polys = []
    for f in slab.Faces():
        if f.normalAt(f.Center()).z < -0.99:            # the slab's bottom faces
            polys.append(wire_points(f.outerWire()))
    return polys


def envelope():
    mad = C.VERSIONS["madeira"]
    # the board: the Madeira's cavity less PCB_CLR, notched round the screw bosses
    inner = C.contour_wp(C.box_contour()).offset2D(-mad["wall"] - PCB_CLR).wires().val()
    face = cq.Face.makeFromWires(inner)
    for k in [{"x": x, "y": y} for x, y in C.screw_points()]:
        face = face.cut(cq.Face.makeFromWires(cq.Wire.makeCircle(C.BOSS_D / 2 + 0.5, cq.Vector(k["x"], k["y"], 0), cq.Vector(0, 0, 1))))
    face = max(face.Faces(), key=lambda f: f.Area())
    outline = face.outerWire()
    # the switch plate's edge as case.py cuts it (notched round the bosses too)
    plate = C.switch_plate()
    plate_face = [f for f in plate.Faces() if f.normalAt(f.Center()).z < -0.99][0]
    cav = C.cavity(mad)
    cav = cav.intersect(C.cavity(C.VERSIONS["seixo"]))      # the tighter of the two everywhere
    zt = C.Z_PCB_TOP
    levels = {}
    for h in LEVELS:
        levels["%.1f" % h] = section(cav, zt + h - 0.02)
    _, st = F.stack("M")
    sub_y = C.VOLUME_XY[1]
    half = max(F.POT[1], F.ENC[1]) / 2
    ib, ii = F.interface_board(mad)
    sub_bottom = ii["sub_top"] - F.BOARD_T - F.SUB_PINS
    t_panel = C.INSERT_WALL + 1.5
    return {
        "spec": "case SPEC v7 (shape frozen)",
        "frame": "SPEC: x right, y towards the player, mm (= KiCad top view)",
        "z_pcb_top": zt, "pcb_thickness": C.PCB_T,
        "outline": wire_points(outline),
        "boss_keepouts": [{"x": x, "y": y, "r": C.BOSS_D / 2 + 0.5} for x, y in C.screw_points()],
        "supports": [{"x": round(x, 3), "y": round(y, 3),
                      "r": (C.SCREW_PILLAR_D if (x, y) in C.SCREW_PILLARS else C.PILLAR_D) / 2 + 0.5}
                     for x, y in C.pillar_points()],
        "max_below": C.UNDER_PCB,
        "plate_outline": wire_points(plate_face.outerWire()),
        "plate_cutout": 14.0,
        "plate_clear": C.Z_PLATE_TOP - C.PLATE_T - zt,
        "plate_thickness": C.PLATE_T,
        "mounting_holes": [{"x": x, "y": y, "d": 2.2, "keepout": C.SCREW_PILLAR_D / 2 + 0.5,
                            "note": "M2 from below through the bottom plate's pillar, nut on top of the board"}
                           for x, y in C.SCREW_PILLARS],
        "controls": dict({k: (list(v) if isinstance(v, tuple) else v) for k, v in C.CONTROLS.items()},
                         top_z={name: round(C.controls_top(v), 3) for name, v in C.VERSIONS.items()}),
        "levels": levels,
        "pitch": C.P, "row_pitch": round(C.ROW_PITCH, 4),
        "keys": [{"n": n, "note": C.note_name(n), "row": row, "x": round(x, 4), "y": round(y, 4), "kind": kind}
                 for n, row, x, y, kind in C.keys()],
        "stack": {
            "audio_board": [st["x"][0], st["y"][0], st["x"][1], st["y"][1]],
            "pin_rows_y": [round(st["cy"] - 7.62, 3), round(st["cy"] + 7.62, 3)],
            "pin1_x": round(st["x"][0] + F.PAST_USB, 3),
            "pins_per_row": 14, "pin_pitch": 2.54,
            "usb_end": "left (x = 0 face)", "vin_row": "back (smaller y)",
            "audio_lift": F.AUDIO_LIFT, "height_eTuttino": F.STACKS["M"]["height"], "height_chorus": F.STACKS["R"]["height"],
        },
        "sub_board": {"rect": [14.5, round(sub_y - half - 0.4, 3), 56.0, round(sub_y + half + 0.4, 3)],
                      "bottom_above_pcb": round(sub_bottom - zt, 2),
                      "holds": "volume pot, encoder, 3 mm power LED (cabled to the main board)"},
        "panel": {"rect": [t_panel, C.USB_YZ[0] - F.USB_PANEL[1] / 2 - 2, t_panel + max(F.USB_PANEL[0], F.JACK_PANEL[0]),
                           C.JACK_YZ[0] + F.JACK_PANEL[1] / 2 + 2],
                  "bottom_above_pcb": round(min(C.USB_YZ[1] - F.USB_PANEL[2] / 2, C.JACK_YZ[1] - F.JACK_PANEL[1] / 2) - zt, 2)},
    }


def plot(env, path):
    import pyvista as pv
    import numpy as np
    pl = pv.Plotter(off_screen=True, window_size=(2000, 700))
    pl.set_background("#f3f1ec")

    def poly(pts, color, width=2):
        a = np.array([(x, C.WIDTH - y, 0.0) for x, y in list(pts) + list(pts[:1])])   # drawn the right way up
        pl.add_mesh(pv.lines_from_points(a), color=color, line_width=width)

    def circle(x, y, r, color, width=2):
        poly([(x + r * math.cos(t / 24 * 2 * math.pi), y + r * math.sin(t / 24 * 2 * math.pi)) for t in range(24)],
             color, width)
    poly(env["outline"], "#1d6b3a", 4)
    poly(env["plate_outline"], "#111111", 2)
    shades = ["#c9c2b4", "#b5ad9c", "#a19884", "#8d836c", "#796e55", "#655a40", "#51472c"]
    for (h, polys), col in zip(sorted(env["levels"].items(), key=lambda kv: float(kv[0])), shades):
        for p in polys:
            poly(p, col, 2)
    for b in env["boss_keepouts"]:
        circle(b["x"], b["y"], b["r"], "#c0392b", 3)
    for s in env["supports"]:
        circle(s["x"], s["y"], s["r"], "#2471a3", 3)
    for k in env["keys"]:
        x, y = k["x"], k["y"]
        poly([(x - 7, y - 7), (x + 7, y - 7), (x + 7, y + 7), (x - 7, y + 7)], "#777777", 1)
    x0, y0, x1, y1 = env["stack"]["audio_board"]
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#16a085", 3)
    x0, y0, x1, y1 = env["sub_board"]["rect"]
    poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#8e44ad", 3)
    pl.camera_position = [(168, 50, 500), (168, 50, 0), (0, 1, 0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = 58
    pl.add_text("PCB envelope (v7): outline green, plate black, height levels brown (lighter = lower), "
                "bosses red, supports blue, stack teal, controls board purple", font_size=10, color="#333333")
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
