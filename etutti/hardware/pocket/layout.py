"""eTuttino Pocket -- key layout, plan outline and interface: the pocket.json
contract (SPEC v5, task F3: the Seixo case, variant B).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/layout.py

(the CadQuery venv: main() reads the exact contours and the part positions
from case/case.py; importing this module stays stdlib-only, so
landing_svgs.py can keep using keys_for(), outlines(), O_ETUTTINO, WIDTH and
D_BTN with plain Python.)

Writes into etutti/hardware/pocket/build/:
  pocket_keys.csv     one line per key (note, row, xp, x, y, colour)
  pocket_top.svg      plan view to scale, the eTuttino's outline behind it
  pocket.json         the contract: keys, outlines, interface (knobs, LED,
                      grille, logo), and where the battery bay, the Teensy +
                      Audio Board stack, the speaker, the controls and the
                      panel board sit. Design owns it; the electronics and
                      the pages read it. The board's own contract is
                      case/out/pcb_envelope.json.

Run case/case.py and case/fit_check.py first (pocket.json quotes the back
volume and the weight from case/out/fit_check.json).
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
sys.path.insert(0, HERE)
import shape as S  # noqa: E402

# ---- re-exported for landing_svgs.py and older readers ----
P, D_BTN, ROW_PITCH, ROW_Y, WIDTH = S.P, S.D_BTN, S.ROW_PITCH, S.ROW_Y, S.WIDTH
R_OPEN, R_BOX, CLR_FB = S.R_OPEN, S.R_BOX, S.CLR_FB
NOTE_NAMES, G3 = S.NOTE_NAMES, S.G3
TOP = S.POCKET_TOP
O_ETUTTINO = 104.0
midi, note_name, keys_for, hull, circles = S.midi, S.note_name, S.keys_for, S.hull, S.circles


def outlines(keys):
    """v1 preview rule, used by landing_svgs.py for the eTuttino family:
    opening and box as convex hulls, the left face flat at x = 0."""
    y_top = ROW_Y[4] - D_BTN / 2 - CLR_FB
    y_bot = ROW_Y[1] + D_BTN / 2 + CLR_FB
    c = [(k["x"], k["y"]) for k in keys]
    opening = hull(circles(c, R_OPEN, y_top, y_bot, 72))
    box = hull(circles(c, R_BOX, 0.0, WIDTH, 72) + [(0.0, 0.0), (0.0, WIDTH)])
    return opening, box


def rnd(poly, d=2):
    return [[round(x, d), round(y, d)] for x, y in poly]


def _rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def contract():
    """pocket.json from case/case.py (D2)."""
    sys.path.insert(0, os.path.join(HERE, "case"))
    import case as C
    fc_path = os.path.join(HERE, "case", "out", "fit_check.json")
    fc = json.load(open(fc_path, encoding="utf-8")) if os.path.exists(fc_path) else {}
    keys = C.KEYS
    rows = {row: sorted((k for k in keys if k["row"] == row), key=lambda k: k["xp"]) for row in (1, 2, 3, 4)}
    grid = [[rows[row][0]["midi"], len(rows[row]), {1: 0.0, 2: -0.5, 3: 0.0, 4: 0.5}[row], 0 if row == 2 else 1]
            for row in (1, 2, 3, 4)]
    holes = C.grille_holes()
    # the grille's outline in plan: the holes' field, round on the 13 deg slope (an ellipse in plan)
    rc = C.SPK_CONE_D / 2 - C.GRILLE_EDGE + 0.4
    gpoly = [(C.SPK_C[0] + rc * math.cos(t * math.pi / 36), C.SPK_C[1] + rc * C.COS_IF * math.sin(t * math.pi / 36))
             for t in range(72)]
    gx, gy = [p[0] for p in gpoly], [p[1] for p in gpoly]
    letters = C.logo_letters()
    lpts = []
    for ch, font, size, x, y, a in letters:
        ar = math.radians(a)
        for rr in (0.0, size * 0.75):
            lpts.append((x + rr * math.cos(ar), y + rr * math.sin(ar)))
    logo_zone = S.offset(S.hull(lpts), 2.0, 24)
    lc = (sum(p[0] for p in lpts) / len(lpts), sum(p[1] for p in lpts) / len(lpts))
    ett_keys, ett = S.etuttino_outline()
    shift = C.G3["x"] - min(k["x"] for k in ett_keys if k["row"] == 2)
    ett = [(x + shift, y) for x, y in ett]
    st = C.stack_parts()
    g = C.conn_geometry()
    inside, outside = C.battery_rects()
    pk = lambda poly: rnd(poly)
    sp = fc.get("speaker", {})
    return {
        "version": 5, "spec": "v5", "task": "F3", "variant": C.VARIANT, "variant_name": C.V["name"],
        "variant_params": {k: C.V[k] for k in ("band", "nose", "corner", "bulge")},
        "note": "SPEC v5 F3: the Seixo case, variant B, as modelled in case/case.py. "
                "Coordinates: x right from the case's leftmost point, y from the back (0) to the player (100), z up from the table, mm.",
        "keys": keys, "rows": grid, "length": round(C.length(), 1), "width": WIDTH,
        "etuttino_length": round(max(x for x, _ in ett) - min(x for x, _ in ett), 1),
        "origin": C.ORIGIN,
        "range": f"{note_name(min(k['midi'] for k in keys))}–{note_name(max(k['midi'] for k in keys))}",
        "heights": {"floor": C.FLOOR_T, "pcb_bottom": C.Z_PCB_BOT, "pcb_top": C.Z_PCB_TOP, "plate_top": C.Z_PLATE_TOP,
                    "deck": C.Z_DECK, "key_top": C.Z_KEY_TOP, "interface": C.Z_IF, "crease_y": C.IF_CREASE_Y,
                    "slope_deg": C.IF_SLOPE, "wall": C.WALL, "top": C.TOP_T},
        "opening": rnd(C.opening_points(0.0, 1.0)), "chamfer": rnd(C.opening_points(C.CHAMFER_W, 1.0)),
        "ramp": rnd(C.opening_points(C.RAMP_TOP_OFF, 1.0)), "box": rnd(C.outline_points(1.0)),
        "inner": rnd(C.inner_points(1.0)), "etuttino_box": rnd(ett),
        "controls": {
            "volume": list(C.VOLUME_XY), "select": list(C.SELECT_XY), "led": list(C.LED_XY),
            "knob_d": C.KNOB_D, "led_d": C.LED_HOLE_D,
            "knob_recess": {"d": C.KNOB_RECESS_D, "depth": C.KNOB_RECESS_DEPTH, "pot_nut": [C.POT_NUT_AF, C.POT_NUT_T],
                            "knob_proposal": {"d": C.KNOB_D, "h": C.KNOB_H, "lift": C.KNOB_LIFT, "cavity": list(C.KNOB_CAVITY)}},
            "grille": [round(min(gx), 1), round(min(gy), 1), round(max(gx), 1), round(max(gy), 1)],   # bounding box (old readers)
            "grille_outline": rnd(gpoly), "holes": [[round(x, 2), round(y, 2)] for x, y in holes], "hole_d": C.GRILLE_HOLE_D,
            "logo": rnd(logo_zone), "logo_text": [round(lc[0], 2), round(lc[1], 2)],
            "logo_letters": [{"char": ch, "x": round(x, 2), "y": round(y, 2), "up_deg": round(a, 2),
                              "size": size, "font": os.path.basename(font)} for ch, font, size, x, y, a in letters],
            "logo_depth": C.LOGO_DEPTH,
            "logo_lines": [{"text": t, "font": os.path.basename(f), "size": sz, "x": round(cx, 2), "baseline_y": round(b, 2),
                            "width": round(w, 2), "height": round(h, 2)} for t, f, sz, _, cx, b, w, h in C.logo_layout()["lines"]],
            "logo_kind": "straight (horizontal), centred in the interface's back zone, engraved",
        },
        "controls_board": {
            "rect": _rect(*C.CTRL_BOARD), "z": [round(C.CTRL_TOP - C.CTRL_T, 2), C.CTRL_TOP],
            "posts": [list(p) for p in C.CTRL_POSTS], "tabs": [_rect(*t) for t in C.CTRL_TABS], "connector": _rect(*C.CTRL_CONN),
            "pot": {"rect": _rect(*C.POT_BODY[:4]), "z": list(C.POT_BODY[4:]),
                    "board": _rect(*C.POT_BOARD[:4]), "board_z": list(C.POT_BOARD[4:]),
                    "kind": "9 mm switched pot, horizontal type (PECAS volume_pot), on a vertical board right of its shaft; M7 nut flush in a D13 lid recess"},
            "encoder": {"rect": _rect(C.SELECT_XY[0] - 6.2, C.SELECT_XY[1] - 6.6, C.SELECT_XY[0] + 6.2, C.SELECT_XY[1] + 6.6),
                        "z": [C.CTRL_TOP, round(C.CTRL_TOP + 6.5, 2)]},
            "note": "hangs under the lid on 2 M2 posts; the pot board meets its left edge at 90 deg",
        },
        "speaker": {"centre": list(C.SPK_C), "d": C.SPK_D, "depth": C.SPK_DEPTH, "part": "Same Sky CLS0361-L152",
                    "z_face": round(C.speaker_face_z(C.SPK_C[1]), 2), "tilt_deg": C.IF_SLOPE,
                    "box": pk(C.spk_inner_contour()), "box_floor_z": round(C.SPK_BOX_BOTTOM - C.BOX_FLOOR_T, 2),
                    "back_volume_cm3": sp.get("back_volume_nominal_cm3"),
                    "back_volume_conservative_cm3": sp.get("back_volume_conservative_cm3"),
                    "note": "rim on a foam gasket under the 13 deg lid, inside a locating ring; sealed back box: walls from the lid, glued floor"},
        "battery": {
            "rect": pk(inside), "outside": pk(outside), "centre": list(C.BATT_C), "angle": C.BATT_ANGLE,
            "cell": [7.0, 36.0, 58.0], "reserved": list(C.BATT_IN), "z": [C.BATT_Z[0], C.BATT_Z[1]],
            "roof_z": [round(v, 2) for v in C.BATT_ROOF_Z], "hatch_screws": [list(p) for p in C.HATCH_SCREWS],
            "connector_pocket": pk(C.pocket_rects()[0]),
            "kind": "LiPo 1S 1000 mAh 603450 with PCM and NTC (3 wires), PECAS battery",
            "note": "bay on the bottom plate (walls + roof), off the main board; out through a hatch in the bottom, the lid stays shut"},
        "stack": {"audio_board": pk(st["audio_board"][0]), "teensy": pk(st["teensy"][0]), "ab_jack": pk(st["ab_jack"][0]),
                  "usb_plug": pk(st["usb_plug"][0]), "angle": C.STACK_ANGLE, "origin": list(C.STACK_XY),
                  "z": {"audio_bottom": round(C.Z_AB, 2), "audio_top": round(C.Z_AB_TOP, 2), "teensy_top": round(C.Z_TEENSY_TOP, 2),
                        "usb_top": round(C.Z_USB_TOP, 2), "height": C.STACK_H},
                  "note": "LOW stack (Teensy soldered straight on the Audio Board), 3 mm above the main board; u along the 38 mm side from the USB end"},
        "panel": {"micro_b": {"at": rnd([g["fem_origin"]])[0], "normal": [round(-v, 3) for v in g["n"]], "z": C.FEM_Z,
                              "window": list(C.FEM_HOLE), "outer_recess": list(C.FEM_RECESS),
                              "kind": "FPC micro-B extension: female head in a tunnel on a flat boss, 0.5 lip, printed trava (2 x M2)"},
                  "jack": {"at": rnd([g["jack_origin"]])[0], "normal": [-1.0, 0.0], "z": C.JACK_Z,
                           "part": "Cliff FC681375V", "hole_d": C.JACK_HOLE_D, "spot_face_d": C.JACK_SPOT_D},
                  "note": "micro-USB (FPC extension) + 3.5 jack (wired) on the back-left curved wall; no panel board since v5; see pcb_envelope.json panel"},
        "teensy_button": {"pinhole": [round(v, 2) for v in C.teensy_button_xy()], "d": C.BTN_HOLE_D,
                          "note": "paper clip from the top, through the lid, down a guide tube to the Teensy's program button (CHECK its position)"},
        "main_board": {"outline": rnd(C.board_outline(1.0)), "note": "= case/out/pcb_envelope.json outline (the bay's corner left out)"},
        "case": {"version": "Seixo", "files": "case/out/seixo_tampa, seixo_fundo, seixo_tampa_bateria, seixo_caixa_fundo, seixo_trava_usb, seixo_chave_porca, plate, keycap_natural/sharp/cf, keycap_test_4 (.step/.stl)",
                 "weight_g": fc.get("weight"),
                 "materials": {k: {"material": m, "qty": q, "what": w} for k, (m, q, w) in C.MATERIALS.items()},
                 "cap_counts": C.cap_counts()},
    }


def top_svg(info, keys, ref_box):
    pad = 12
    xs = [x for x, _ in ref_box] + [x for x, _ in info["box"]]
    x0, x1 = min(xs) - pad, max(xs) + pad
    W, H = x1 - x0, WIDTH + 2 * pad
    pts = lambda poly: " ".join(f"{x - x0:.2f},{y + pad:.2f}" for x, y in poly)
    c = info["controls"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" width="{W * 4:.0f}" height="{H * 4:.0f}" font-family="sans-serif">',
         f'<rect width="{W:.1f}" height="{H:.1f}" fill="#f6f4ef"/>',
         f'<clipPath id="pb"><polygon points="{pts(info["box"])}"/></clipPath>',
         f'<polygon points="{pts(ref_box)}" fill="none" stroke="#b9b2a6" stroke-width="0.5" stroke-dasharray="2 1.5"/>',
         f'<polygon points="{pts(info["box"])}" fill="#e7e1d6" stroke="#4a443c" stroke-width="0.6"/>',
         f'<polygon points="{pts(info["ramp"])}" fill="#ddd5c6" clip-path="url(#pb)"/>',
         f'<polygon points="{pts(info["chamfer"])}" fill="#c9bfae"/>',
         f'<polygon points="{pts(info["opening"])}" fill="#26231f"/>',
         f'<polygon points="{pts(c["grille_outline"])}" fill="#d6ccbb" stroke="#9c9486" stroke-width="0.4"/>']
    for x, y in c["holes"]:
        s.append(f'<circle cx="{x - x0:.2f}" cy="{y + pad:.2f}" r="{c["hole_d"] / 2:.2f}" fill="#6f665a"/>')
    for L in c["logo_letters"]:
        fam = "Georgia, serif" if L["font"].startswith("georgia") else "Arial, sans-serif"
        s.append(f'<text x="{L["x"] - x0:.2f}" y="{L["y"] + pad:.2f}" font-size="{L["size"]:.2f}" font-family="{fam}" '
                 f'font-weight="700" text-anchor="middle" fill="#9a8f7e" transform="rotate({L["up_deg"] + 90:.2f} {L["x"] - x0:.2f} {L["y"] + pad:.2f})">{L["char"]}</text>')
    for (x, y), lab in ((c["volume"], "VOL"), (c["select"], "SOM")):
        s.append(f'<circle cx="{x - x0}" cy="{y + pad}" r="{c["knob_d"] / 2}" fill="#3b3631"/>')
        s.append(f'<text x="{x - x0}" y="{y + pad + 8.6}" font-size="3" text-anchor="middle" fill="#6b645a">{lab}</text>')
    s.append(f'<circle cx="{c["led"][0] - x0}" cy="{c["led"][1] + pad}" r="{c["led_d"] / 2}" fill="#5fb85f"/>')
    for k in keys:
        fill = "#1d1b19" if k["sharp"] else "#fbfaf6"
        s.append(f'<circle cx="{k["x"] - x0}" cy="{k["y"] + pad}" r="{D_BTN / 2}" fill="{fill}" stroke="#55504a" stroke-width="0.3"/>')
        s.append(f'<text x="{k["x"] - x0}" y="{k["y"] + pad + 1.2}" font-size="3.4" text-anchor="middle" fill="{"#ddd" if k["sharp"] else "#333"}">{k["note"]}</text>')
    s.append(f'<text x="{pad}" y="{H - 3}" font-size="4" fill="#4a443c">eTuttino Pocket · Seixo, variante {info["variant"]} · '
             f'{len(keys)} teclas · {info["length"]:.1f} × {WIDTH:.0f} mm</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(BUILD, exist_ok=True)
    info = contract()
    keys = info["keys"]
    with open(os.path.join(BUILD, "pocket_keys.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["row", "note", "midi", "xp", "x", "y", "colour", "c_or_f"])
        for k in sorted(keys, key=lambda k: (k["row"], k["xp"])):
            w.writerow([k["row"], k["note"], k["midi"], k["xp"], k["x"], k["y"],
                        "black" if k["sharp"] else "white", int(k["cf"])])
    with open(os.path.join(BUILD, "pocket.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(BUILD, "pocket_top.svg"), "w", encoding="utf-8") as fh:
        fh.write(top_svg(info, keys, info["etuttino_box"]))
    print(f"{len(keys)} keys, {info['range']}; O = {info['origin']}; variant {info['variant']} ({info['variant_name']})")
    print(f"case {info['length']:.1f} x {WIDTH:.0f} mm (eTuttino {info['etuttino_length']:.1f}); "
          f"speaker {info['speaker']['d']:.0f} mm, back box {info['speaker']['back_volume_cm3']} cm3")
    print(f"firmware ROWS = {info['rows']}")


if __name__ == "__main__":
    main()
