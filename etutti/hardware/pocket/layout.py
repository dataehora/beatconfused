"""eTuttino Pocket -- key layout, plan outline and interface (SPEC v2, D1).

Stdlib only:  python etutti/hardware/pocket/layout.py      (~2 min: it packs the interface)
Writes into etutti/hardware/pocket/build/:
  pocket_keys.csv     one line per key (note, row, xp, x, y, colour)
  pocket_top.svg      plan view to scale, the eTuttino's outline behind it
  pocket.json         the contract: keys, outlines, interface, and where the
                      battery, the Teensy + Audio Board stack, the speaker and
                      the switched pot go (design owns it; electronics and the
                      pages read it)

The plan geometry is shape.py (shared with the D1 study variants.py and, in
D2, the CadQuery model). The left side is the variant recommended in
variants.RECOMMENDED, marked "provisional" until J picks one.

The power budget and POWER.md belong to the electronics agent since SPEC v2
(task E1); this script no longer writes them.

landing_svgs.py (programacao-som) imports this module for keys_for(),
outlines(), O_ETUTTINO, WIDTH and D_BTN: keep those names.
"""
import csv
import json
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


def contract(r):
    """pocket.json from a variants.study() result."""
    import variants as V
    g, kn, spk, st, bat, pan = r["geo"], r["knobs"], r["speaker"], r["stack"], r["battery"], r["panel"]
    keys = g.keys
    rows = {row: sorted((k for k in keys if k["row"] == row), key=lambda k: k["xp"]) for row in (1, 2, 3, 4)}
    # firmware/page grid, generate.py's ROWS convention: (first MIDI note, count, x offset, first column)
    grid = [[rows[row][0]["midi"], len(rows[row]), {1: 0.0, 2: -0.5, 3: 0.0, 4: 0.5}[row], 0 if row == 2 else 1]
            for row in (1, 2, 3, 4)]
    gx = [p[0] for p in r["grille"]]
    gy = [p[1] for p in r["grille"]]
    p = st["parts"]
    return {
        "version": 2, "spec": "v2", "task": "D1",
        "provisional": True, "variant": r["key"], "variant_name": g.v["name"],
        "variant_params": {k: g.v[k] for k in ("band", "nose", "corner", "bulge")},
        "note": "Provisional (SPEC v2 D1): the left side J has not picked yet. Plan only; heights from the eTuttino stack-up. "
                "Coordinates: x right from the case's leftmost point, y from the back (0) to the player (100), z up from the table, mm.",
        "keys": keys, "rows": grid, "length": round(g.length, 1), "width": WIDTH,
        "etuttino_length": round(max(x for x, _ in r["etuttino"]) - min(x for x, _ in r["etuttino"]), 1),
        "origin": g.origin,
        "range": f"{note_name(min(k['midi'] for k in keys))}–{note_name(max(k['midi'] for k in keys))}",
        "heights": {"floor": S.FLOOR_T, "pcb_bottom": S.Z_PCB_BOT, "pcb_top": S.Z_PCB_TOP, "plate_top": S.Z_PLATE_TOP,
                    "deck": S.Z_DECK, "key_top": S.Z_KEY_TOP, "interface": S.Z_IF, "crease_y": S.IF_CREASE_Y,
                    "slope_deg": S.IF_SLOPE, "wall": S.WALL, "top": S.TOP_T},
        "opening": rnd(g.open), "chamfer": rnd(g.chamfer), "ramp": rnd(g.ramp), "box": rnd(g.outline),
        "inner": rnd(g.inner), "etuttino_box": rnd(r["etuttino"]),
        # the interface top: knobs, LED, grille, logo (what the pages draw)
        "controls": {
            "volume": [round(v, 2) for v in kn["volume"]], "select": [round(v, 2) for v in kn["select"]],
            "led": [round(v, 2) for v in kn["led"]], "knob_d": V.KNOB_D, "led_d": V.LED_D,
            "grille": [round(min(gx), 1), round(min(gy), 1), round(max(gx), 1), round(max(gy), 1)],   # bounding box (old readers)
            "grille_outline": rnd(r["grille"]), "holes": r["holes"], "hole_d": V.HOLE_D,
            "logo": rnd(r["logo"]), "logo_text": [round(v, 2) for v in r["logo_c"]],
        },
        # under the lid
        "controls_board": {"rect": rnd(kn["board"]), "z": [round(v, 2) for v in kn["z_board"]],
                           "pot": {"rect": rnd(kn["pot"]), "z": [round(v, 2) for v in kn["z_pot"]],
                                   "reserved": {"body_xy": V.POT_SW[:2], "height": V.POT_SW[2]},
                                   "kind": "9 mm pot with on/off switch at the start of travel (CHECK the part)"},
                           "encoder": {"rect": rnd(kn["encoder"]), "z": [round(v, 2) for v in kn["z_enc"]]},
                           "note": "hangs under the lid like the eTuttino's; part tops 0.2 under the lid"},
        "speaker": {"centre": [round(v, 2) for v in spk["centre"]], "d": spk["d"], "d_max": round(spk["d_max"], 1),
                    "depth": spk["depth"], "z_face": round(spk["z_face"], 2), "tilt_deg": S.IF_SLOPE,
                    "box": rnd(spk["box"]), "box_floor_z": round(r["box_floor"], 2),
                    "back_volume_cm3": round(r["v_back"], 1),
                    "note": "face 0.3 under the 13 deg lid, sealed to it; closed back box printed round it"},
        "battery": None if not bat else {
            "rect": rnd(bat["rect"]), "centre": [round(v, 2) for v in bat["centre"]], "angle": bat["angle"],
            "cell": [V.BATT["l"], V.BATT["w"], V.BATT["t"]], "reserved": [V.BATT_L, V.BATT_W],
            "z": list(V.BATT_Z), "kind": "LiPo 1S 1000 mAh 603450-type (CHECK)",
            "note": "on the bottom plate, off the main board (keyboard keeps the eTuttino height); reached by taking the bottom off"},
        "stack": {"audio_board": rnd(p["audio"][0]), "teensy": rnd(p["teensy"][0]), "ab_jack": rnd(p["ab_jack"][0]),
                  "usb_plug": rnd(p["plug"][0]), "angle": st["angle"], "origin": [st["x"], st["y"]],
                  "z": {"audio_bottom": round(V.Z_AB, 2), "audio_top": round(V.Z_AB_TOP, 2), "teensy_bottom": round(V.Z_TEENSY, 2),
                        "usb_top": round(V.Z_USB_TOP, 2), "height": V.STACK_H},
                  "note": "Teensy 4.0 on Audio Board Rev D, 3 mm above the main board (eTuttino); local u along the 38 mm side from the USB end"},
        "panel": {"usb": {"rect": rnd(pan["usb"]), "at": [round(v, 2) for v in pan["usb_at"]],
                          "normal": [round(v, 3) for v in pan["usb_n"]]},
                  "jack": {"rect": rnd(pan["jack"]), "at": [round(v, 2) for v in pan["jack_at"]],
                           "normal": [round(v, 3) for v in pan["jack_n"]]},
                  "z": list(pan["z"]), "cable_mm": round(pan["cable"], 1),
                  "note": "panel micro-USB receptacle and 3.5 mm jack in the left face; a 90 deg plug + short cable to the Teensy"},
        "main_board": {"keys": rnd(r["boards"][0]), "tongue": rnd(r["boards"][1]),
                       "note": "where the main board may be: keys (opening - 3) + a tongue under the stack. Not under the battery."},
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
         f'<polygon points="{pts(ref_box)}" fill="none" stroke="#b9b2a6" stroke-width="0.5" stroke-dasharray="2 1.5"/>',
         f'<polygon points="{pts(info["box"])}" fill="#e7e1d6" stroke="#4a443c" stroke-width="0.6"/>',
         f'<polygon points="{pts(info["ramp"])}" fill="#ddd5c6"/>',
         f'<polygon points="{pts(info["opening"])}" fill="#26231f"/>',
         f'<polygon points="{pts(c["grille_outline"])}" fill="#d6ccbb" stroke="#9c9486" stroke-width="0.4"/>']
    for x, y in c["holes"]:
        s.append(f'<circle cx="{x - x0:.2f}" cy="{y + pad:.2f}" r="0.95" fill="#6f665a"/>')
    lx, ly = c["logo_text"]
    s.append(f'<text x="{lx - x0:.1f}" y="{ly + pad:.1f}" font-size="5.5" text-anchor="middle" fill="#9a8f7e" font-weight="700">eTuttino</text>')
    s.append(f'<text x="{lx - x0:.1f}" y="{ly + pad + 4.2:.1f}" font-size="2.8" text-anchor="middle" fill="#9a8f7e" letter-spacing="0.8">POCKET</text>')
    for (x, y), lab in ((c["volume"], "VOL"), (c["select"], "SOM")):
        s.append(f'<circle cx="{x - x0}" cy="{y + pad}" r="{c["knob_d"] / 2}" fill="#3b3631"/>')
        s.append(f'<text x="{x - x0}" y="{y + pad - 6.2}" font-size="3" text-anchor="middle" fill="#6b645a">{lab}</text>')
    s.append(f'<circle cx="{c["led"][0] - x0}" cy="{c["led"][1] + pad}" r="{c["led_d"] / 2}" fill="#5fb85f"/>')
    for k in keys:
        fill = "#1d1b19" if k["sharp"] else "#fbfaf6"
        s.append(f'<circle cx="{k["x"] - x0}" cy="{k["y"] + pad}" r="{D_BTN / 2}" fill="{fill}" stroke="#55504a" stroke-width="0.3"/>')
        s.append(f'<text x="{k["x"] - x0}" y="{k["y"] + pad + 1.2}" font-size="3.4" text-anchor="middle" fill="{"#ddd" if k["sharp"] else "#333"}">{k["note"]}</text>')
    s.append(f'<text x="{pad}" y="{H - 3}" font-size="4" fill="#4a443c">eTuttino Pocket · variante {info["variant"]} ({info["variant_name"]}, provisória) · '
             f'{len(keys)} teclas · {info["length"]:.0f} × {WIDTH:.0f} mm</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    import variants as V
    os.makedirs(BUILD, exist_ok=True)
    r = V.study(V.RECOMMENDED)
    assert not r["checks"], r["checks"]
    info = contract(r)
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
        fh.write(top_svg(info, keys, r["etuttino"]))
    print(f"{len(keys)} keys, {info['range']}; O = {info['origin']}; variant {info['variant']} ({info['variant_name']}, provisional)")
    print(f"case {info['length']:.1f} x {WIDTH:.0f} mm (eTuttino {info['etuttino_length']:.1f}); "
          f"speaker {info['speaker']['d']:.0f} mm, back box {info['speaker']['back_volume_cm3']} cm3")
    print(f"firmware ROWS = {info['rows']}")


if __name__ == "__main__":
    main()
