"""eTuttino Pocket, SPEC v3 D2: does everything fit the Seixo case?

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/fit_check.py [--no-renders]

Builds every part the case holds as a solid, sized from the electronics'
contract pcb/PECAS.json (read at run time; the few numbers it doesn't give
are marked CHECK here) and placed where case.py reserves room for it, then:

  1. each part against the shell, the bottom plate, the switch plate and
     the other parts: overlap volume (must be 0) and the smallest gap;
  2. heights: each part's top against the lid above it;
  3. the speaker: sealed back volume, grille open area, grille -> membrane;
  4. the panel connectors: wall left at the holes, face to the outside;
  5. the exported STLs: open / non-manifold mesh edges, and rays down
     through the keyboard opening, the grille and the knob holes (a film
     left by OCC would stop them);
  6. weight from the STL volumes.

Writes out/fit_check.json (FIT_CHECK.md quotes it) and renders/fit_*.png.
SPEC coordinates (y towards the player) throughout; the renders are drawn
in the files' mirrored frame so they look like the instrument.
"""
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "case")))
import keycap as K  # noqa: E402  (the eTuttino's caps and switch stand-ins; same heights)

S = C.S
PECAS_PATH = os.path.join(C.POCKET, "pcb", "PECAS.json")
RENDERS = os.path.join(HERE, "renders")
box, cyl = C.box3, C.cyl

DENSITY = {"resin_g": 1.18, "mjf_pa12_g": 1.01}      # g/cm3: an engineering resin (Tough/Grey class), MJF PA12


def pecas():
    with open(PECAS_PATH, encoding="utf-8") as f:
        return json.load(f)["parts"]


# ------------------------------------------------------------- parts
def tilted(solid, pivot):
    """Turn a solid built with its axis along -z (face at z = 0) to the 13 deg
    lid: its top tips towards the player, as the lid does."""
    s = solid.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -C.IF_SLOPE)
    return s.translate(cq.Vector(*pivot))


def speaker(pc):
    b = pc["speaker"]["body"]
    d, depth, fh, md = b["frame_d"], b["total_depth"], b["frame_height"], b["magnet_d"]
    c = C.SPK_C
    zf = C.speaker_face_z(c[1])
    frame = cq.Solid.makeCylinder(d / 2, fh, cq.Vector(0, 0, -fh))
    magnet = cq.Solid.makeCylinder(md / 2, depth, cq.Vector(0, 0, -depth))
    full = cq.Solid.makeCylinder(d / 2, depth, cq.Vector(0, 0, -depth))
    cone = cq.Solid.makeCylinder(C.SPK_CONE_D / 2, 0.01, cq.Vector(0, 0, -0.6))     # membrane ~0.6 behind the rim (CHECK)
    return (tilted(frame.fuse(magnet), (c[0], c[1], zf)), tilted(full, (c[0], c[1], zf)),
            tilted(cone, (c[0], c[1], zf)))


def stack_solids():
    out = {}
    for name, (poly, (z0, z1)) in C.stack_parts().items():
        out[name] = C.poly_prism(poly, z0, z1)
    return out


def panel_solids(pc):
    pg = C.panel_geometry()
    at, n = pg["at"], pg["n"]
    ang = math.degrees(math.atan2(-n[1], -n[0]))
    out = {"panel_board": C.poly_prism(pg["board"], C.PANEL_Z_TOP - C.PANEL_T, C.PANEL_Z_TOP)}

    def place(sh, p, zc):
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang)
        return sh.translate(cq.Vector(p[0], p[1], zc))
    u = pc["usb_c"]["body"]
    face = C.USB_C_WALL - 0.15                          # the shell's face, outwards from the chord
    usb = box(face - u["depth"], -u["width"] / 2, -u["height"] / 2, face, u["width"] / 2, u["height"] / 2)
    usb = cq.Workplane().add(usb).edges("|X").fillet(u["height"] / 2 - 0.01).val()
    out["usb_c"] = place(usb, at(C.PANEL_USB_S, 0), C.USB_C_ZC)
    j = pc["headphone_jack"]["body"]
    bf = C.JACK_WALL - 0.15
    barrel = cq.Solid.makeCylinder(j["barrel_d"] / 2, j["barrel_len"], cq.Vector(bf - j["barrel_len"], 0, 0), cq.Vector(1, 0, 0))
    body = box(bf - j["barrel_len"] - j["length"], -j["width"] / 2, C.PANEL_Z_TOP - C.JACK_ZC,
               bf - j["barrel_len"], j["width"] / 2, C.PANEL_Z_TOP - C.JACK_ZC + pc["panel_board"]["body"]["above_board_max"])
    out["jack"] = place(barrel.fuse(body), at(C.PANEL_JACK_S, 0), C.JACK_ZC)
    return out, pg


def controls_solids(pc):
    x0, y0, x1, y1, z0, z1 = C.POT_BODY
    pot = box(x0, y0, z0, x1, y1, z1)
    vx, vy = C.VOLUME_XY
    lid = C.z_interface(vy, C.TOP_T)
    bushing = cyl(vx, vy, z1, C.Z_IF + 2.0, 7.0)
    shaft = cyl(vx, vy, C.Z_IF + 2.0, C.Z_IF + 12.3, 6.0)
    bx0, by0, bx1, by1, bz0, bz1 = C.POT_BOARD
    potboard = box(bx0, by0, bz0, bx1, by1, bz1)
    potlegs = box(bx1, by0, C.CTRL_TOP + 0.2, C.POT_LEGS_X, by1, bz1)   # clipped legs: only above the controls board
    cx0, cy0, cx1, cy1 = C.CTRL_BOARD
    ctrl = box(cx0, cy0, C.CTRL_TOP - C.CTRL_T, cx1, cy1, C.CTRL_TOP)
    legs = box(cx0, cy0, C.CTRL_TOP - C.CTRL_T - C.CTRL_LEGS, cx1, cy1, C.CTRL_TOP - C.CTRL_T)
    e = pc["encoder"]["body"]
    sx, sy = C.SELECT_XY
    enc = box(sx - e["plan"][0] / 2, sy - e["plan"][1] / 2, C.CTRL_TOP, sx + e["plan"][0] / 2, sy + e["plan"][1] / 2,
              C.CTRL_TOP + e["height_above_pcb"])
    enc_shaft = cyl(sx, sy, C.CTRL_TOP + e["height_above_pcb"], C.CTRL_TOP + e["height_above_pcb"] + 5.0, 7.0).fuse(
        cyl(sx, sy, C.CTRL_TOP + e["height_above_pcb"] + 5.0, C.CTRL_TOP + e["height_above_pcb"] + e["shaft_l"], 6.0))
    led = pc["led"]["body"]
    lx, ly = C.LED_XY
    led_top = C.Z_IF - 0.5
    led_s = cyl(lx, ly, led_top - led["height"], led_top, led["d"]).fuse(
        cyl(lx, ly, led_top - led["height"], led_top - led["height"] + 1.0, led["flange_d"]))
    spacer = cyl(lx, ly, C.CTRL_TOP, led_top - led["height"], 4.0)
    a0, b0, a1, b1 = C.CTRL_CONN
    conn = box(a0, b0, C.CTRL_TOP, a1, b1, C.CTRL_TOP + 4.25 + 2.0)
    return {"pot": pot.fuse(bushing).fuse(shaft), "pot_board": potboard.fuse(potlegs), "controls_board": ctrl, "controls_legs": legs,
            "encoder": enc.fuse(enc_shaft), "led": led_s.fuse(spacer), "controls_conn": conn}


def battery(pc):
    b = pc["battery"]["body"]
    t, w, l = b["with_pcm_and_wire_fold"]
    swell = t * (1 + b["swelling_allowance_pct"] / 100.0)
    c = C.BATT_C
    cell = box(c[0] - l / 2, c[1] - w / 2, C.BATT_Z[0], c[0] + l / 2, c[1] + w / 2, C.BATT_Z[0] + t)
    swollen = box(c[0] - l / 2, c[1] - w / 2, C.BATT_Z[0], c[0] + l / 2, c[1] + w / 2, C.BATT_Z[0] + swell)
    # the mated JST PH 3-pin pair in the pocket (plug + receptacle, ~11.5 x 4.5 x 6, CHECK)
    x0, x1, y0 = C.BATT_POCKET
    plug = box(x0 + 0.4, y0 + 0.6, C.BATT_Z[0] + 0.5, x0 + 0.4 + 11.5, y0 + 0.6 + 4.5, C.BATT_Z[0] + 0.5 + 6.0)
    return cell, swollen.fuse(plug)


def main_board():
    b = C.main_board_solid()
    below = cq.Solid.extrudeLinear(C.board_face().translate(cq.Vector(0, 0, C.FLOOR_T + 0.0)),
                                   cq.Vector(0, 0, C.Z_PCB_BOT - C.FLOOR_T))
    return b, below


def keyboard():
    sw = [K.switch(x, y) for _, _, x, y, _ in C.keys()]
    caps = {kind: K.cap(kind) for kind in ("natural", "sharp", "cf")}
    cp = [caps[kind].translate(cq.Vector(x, y, 0)) for _, _, x, y, kind in C.keys()]
    return cq.Compound.makeCompound(sw), cq.Compound.makeCompound(cp), cp


# ------------------------------------------------------------- measures
def overlap(a, b):
    try:
        v = a.intersect(b).Volume()
    except Exception:
        v = -1.0
    return v


def gap(a, b):
    try:
        return a.distance(b)
    except Exception:
        return float("nan")


def stl_checks(names):
    """Open / non-manifold edges of each exported STL."""
    import pyvista as pv
    out = {}
    for n in names:
        m = pv.read(os.path.join(C.OUT, n + ".stl"))
        fe = m.extract_feature_edges(boundary_edges=True, non_manifold_edges=True, feature_edges=False, manifold_edges=False)
        out[n] = {"open_edges": int(fe.n_cells), "volume_cm3": round(abs(m.volume) / 1000, 3),
                  "triangles": int(m.n_cells)}
    return out


def ray_probe():
    """Rays down the exported shell (file frame: y_file = 100 - y_spec)
    through each key's opening, each grille hole and each knob/LED hole:
    nothing may stop them (a film over the keys once hid in a render)."""
    import pyvista as pv
    m = pv.read(os.path.join(C.OUT, "seixo_tampa.stl"))
    res = {"keys": [0, 0], "grille": [0, 0], "holes": [0, 0], "blocked": []}

    def free(x, y, z0=45.0, z1=C.Z_PLATE_TOP + 0.3, key=None):
        pts, _ = m.ray_trace((x, C.WIDTH - y, z0), (x, C.WIDTH - y, z1), first_point=False)
        ok = len(pts) == 0
        res[key][0 if ok else 1] += 1
        if not ok:
            res["blocked"].append([key, round(x, 2), round(y, 2)])
        return ok
    for _, _, x, y, _ in C.keys():
        for dx, dy in ((0, 0), (6.5, 0), (-6.5, 0), (0, 6.5), (0, -6.5)):
            free(x + dx, y + dy, key="keys")
    for x, y in C.grille_holes():
        free(x, y, z1=C.z_interface(y, C.TOP_T) - 0.6, key="grille")
    for (x, y) in (C.VOLUME_XY, C.SELECT_XY, C.LED_XY):
        free(x, y, z1=C.z_interface(y, C.TOP_T) - 0.6, key="holes")
    return res


# ------------------------------------------------------------- run
def run(renders=True):
    pc = pecas()
    shell = C.shell()
    fundo = C.fundo()
    plate = C.switch_plate()
    bfloor = C.box_floor()
    hatch = C.hatch()
    spk_nom, spk_full, membrane = speaker(pc)
    st = stack_solids()
    pan, pg = panel_solids(pc)
    ctl = controls_solids(pc)
    cell, swollen = battery(pc)
    board, below = main_board()
    sw, caps, cap_list = keyboard()
    parts = {"main_board": board, "board_underside": below, **st, **pan, **ctl,
             "battery": swollen, "speaker": spk_full}
    case_parts = {"shell": shell, "fundo": fundo, "plate": plate, "box_floor": bfloor, "hatch": hatch}
    R = {"spec": "v3", "task": "D2", "length": round(C.length(), 2), "plan_vs_shape_py": round(C.check_plan(), 3)}

    # 1. every part against the case parts
    allowed = {("board_underside", "fundo"), ("main_board", "fundo"),   # pillars touch the board
               ("main_board", "shell"), ("board_underside", "shell"),   # screw notches are in the outline; checked by gap below
               ("pot", "shell")}                                       # the bushing goes through the lid
    coll = []
    gaps = {}
    for pn, ps in parts.items():
        for cn, cs in case_parts.items():
            v = overlap(ps, cs)
            if v > 1e-3 and (pn, cn) not in allowed:
                coll.append([pn, cn, round(v, 3)])
        gaps[pn] = round(gap(ps, shell), 2)
    # the pot's bushing in its hole, the board and the shell (only the walls/columns could touch)
    R["pot_in_lid"] = round(overlap(ctl["pot"], shell), 4)
    R["board_vs_shell"] = round(overlap(board, shell), 4)
    R["board_vs_fundo"] = round(overlap(board, fundo), 4)
    R["board_vs_plate"] = round(overlap(board, plate), 4)
    # 2. parts against each other (the ones that share room)
    pairs = [("audio_board", "panel_board"), ("teensy", "panel_board"), ("teensy_usb", "panel_board"),
             ("usb_plug", "panel_board"), ("ab_jack", "panel_board"), ("usb_plug", "jack"), ("usb_plug", "usb_c"),
             ("pot_board", "panel_board"), ("pot", "panel_board"), ("jack", "pot_board"),
             ("audio_board", "controls_board"), ("ab_jack", "controls_legs"), ("teensy", "controls_legs"),
             ("audio_board", "controls_legs"), ("audio_board", "pot_board"), ("ab_jack", "pot_board"),
             ("battery", "main_board"), ("battery", "board_underside"), ("speaker", "controls_board"),
             ("speaker", "encoder"), ("speaker", "pot"), ("controls_conn", "led"), ("encoder", "led"),
             ("pot", "encoder"), ("main_board", "speaker"), ("usb_c", "jack"), ("pot_board", "encoder"),
             ("pot", "controls_board"), ("pot_board", "controls_board")]
    pair_res = []
    for a, b in pairs:
        pair_res.append([a, b, round(overlap(parts[a], parts[b]), 3), round(gap(parts[a], parts[b]), 2)])
    R["collisions_with_case"] = coll
    R["gap_to_shell"] = gaps
    R["pairs"] = pair_res
    R["box_floor_vs_bay"] = round(gap(bfloor, fundo), 2)
    cols = {"%g,%g" % xy: round(gap(pan["panel_board"].fuse(pan["jack"]).fuse(pan["usb_c"]), cyl(xy[0], xy[1], C.FLOOR_T, C.BOSS_TOP.get(xy, 40.0), C.BOSS_D)), 2)
            for xy in C.screw_points() if xy[0] < 70}
    R["panel_vs_columns"] = cols
    R["stack_vs_columns"] = {"%g,%g" % xy: round(min(gap(s, cyl(xy[0], xy[1], C.FLOOR_T, C.BOSS_TOP.get(xy, 40.0), C.BOSS_D))
                                                      for s in st.values()), 2) for xy in C.screw_points() if xy[0] < 70}
    R["box_floor_vs_speaker"] = round(gap(bfloor, spk_full), 2)
    R["hatch_vs_fundo"] = round(overlap(hatch, fundo), 4)
    # keyboard: switches and caps against the shell and the plate's web
    R["switches_vs_shell"] = round(gap(sw, shell), 2)
    R["caps_vs_shell"] = round(gap(caps, shell), 2)
    R["caps_vs_opening_min"] = round(min(gap(c, shell) for c in cap_list), 2)

    # 3. speaker
    cav = C.cavity()
    inner = C.spk_inner_contour()
    box_in = C.poly_prism(inner, C.SPK_BOX_BOTTOM, 45.0).intersect(cav)
    R["speaker"] = {
        "back_volume_nominal_cm3": round(box_in.cut(spk_nom).Volume() / 1000, 1),
        "back_volume_conservative_cm3": round(box_in.cut(spk_full).Volume() / 1000, 1),
        "grille": dict(zip(("holes", "open_ratio"), C.grille_open_ratio())),
        "membrane_to_grille_mm": round(gap(membrane, shell), 2),
        "rim_to_lid_mm": round(gap(spk_nom, shell), 2),
        "frame_seat_radial_clr": C.SPK_SEAT_CLR,
        "lowest_back_z": round(spk_full.BoundingBox().zmin, 2),
        "box_bottom_z": round(C.SPK_BOX_BOTTOM, 2),
    }
    R["speaker"]["grille"]["open_ratio"] = round(R["speaker"]["grille"]["open_ratio"], 3)
    # 4. panel
    R["panel"] = {
        "chord_mm": round(pg["chord"], 2), "wall_at_usb": round(pg["wall_usb"], 2), "wall_at_jack": round(pg["wall_jack"], 2),
        "wall_mid": round(pg["wall_mid"], 2), "wall_board_ends": [round(v, 2) for v in pg["wall_ends"]],
        "usb_recess_depth": round(pg["wall_usb"] - C.USB_C_WALL, 2), "jack_spot_depth": round(pg["wall_jack"] - C.JACK_WALL, 2),
        "usb_c_vs_shell": round(gap(pan["usb_c"], shell), 2), "jack_vs_shell": round(gap(pan["jack"], shell), 2),
        "board_vs_shell": round(gap(pan["panel_board"], shell), 2),
        "board_over_plug": round(gap(pan["panel_board"], st["usb_plug"]), 2),
        "front_edge_wall_pts": [[round(v, 2) for v in pg["a"]], [round(v, 2) for v in pg["b"]]],
    }
    # 5. battery
    b = pc["battery"]["body"]
    R["battery"] = {
        "cradle_inside": list(C.BATT_IN), "pecas_cradle": b["cradle"],
        "z": [C.BATT_Z[0], C.BATT_Z[1]], "roof_z": [round(v, 2) for v in C.BATT_ROOF_Z],
        "cell_vs_fundo_overlap": round(overlap(cell, fundo), 4), "swollen_vs_fundo_overlap": round(overlap(swollen, fundo), 4),
        "swollen_to_roof": round(C.BATT_ROOF_Z[0] - (C.BATT_Z[0] + b["with_pcm_and_wire_fold"][0] * (1 + b["swelling_allowance_pct"] / 100)), 2),
        "bay_to_board": round(gap(C.poly_prism(C.battery_rects()[1], C.FLOOR_T, C.BATT_ROOF_Z[1]).fuse(
            C.poly_prism(C.pocket_rects()[1], C.FLOOR_T, C.BATT_ROOF_Z[1])), board), 2),
        "plug_in_pocket_to_fundo": round(gap(swollen, fundo), 2),
        "bay_to_shell": round(gap(fundo.intersect(C.poly_prism(C.battery_rects()[1], 0, 20)), shell), 2),
    }
    # 6. heights under the lid
    R["heights"] = {
        "pot_body_top": C.POT_BODY[5], "lid_under_at_knobs": round(C.z_interface(C.KNOB_Y, C.TOP_T), 2),
        "encoder_top": round(C.CTRL_TOP + pc["encoder"]["body"]["height_above_pcb"], 2),
        "teensy_usb_top": round(C.Z_USB_TOP, 2), "plug_top": round(C.stack_parts()["usb_plug"][1][1], 2),
        "panel_board": [round(C.PANEL_Z_TOP - C.PANEL_T, 2), C.PANEL_Z_TOP],
        "panel_parts_top": round(C.PANEL_Z_TOP + pc["panel_board"]["body"]["above_board_max"], 2),
        "controls_board": [round(C.CTRL_TOP - C.CTRL_T, 2), C.CTRL_TOP],
    }
    # 7. exports
    names = ["seixo_tampa", "seixo_fundo", "seixo_tampa_bateria", "seixo_caixa_fundo", "plate"]
    R["stl"] = stl_checks(names)
    R["rays"] = ray_probe()
    # 8. weight
    vol = sum(R["stl"][n]["volume_cm3"] for n in names if n != "plate")
    R["weight"] = {"printed_cm3": round(vol, 1),
                   **{k: round(vol * d, 0) for k, d in DENSITY.items()},
                   "plate_fr4_g": round(R["stl"]["plate"]["volume_cm3"] * 1.85, 0)}
    with open(os.path.join(C.OUT, "fit_check.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    if renders:
        render_all(shell, fundo, plate, bfloor, hatch, parts, sw, caps, pc)
    return R


# ------------------------------------------------------------- pictures
COLOURS = {"pcb": "#2f7d4a", "ab": "#1d5d3b", "teensy": "#3aa86b", "batt": "#d08a3c", "spk": "#8a6a48",
           "ctrl": "#6b4a92", "metal": "#9a9a9a", "dark": "#26282c", "plug": "#444444", "panel": "#3c7a9a"}
PART_COL = {"main_board": "pcb", "audio_board": "ab", "teensy": "teensy", "teensy_usb": "metal", "usb_plug": "plug",
            "ab_jack": "dark", "panel_board": "panel", "usb_c": "metal", "jack": "dark", "pot": "ctrl", "pot_board": "ctrl",
            "controls_board": "ctrl", "encoder": "metal", "led": "metal", "controls_conn": "dark", "battery": "batt",
            "speaker": "spk"}


def render_all(shell, fundo, plate, bfloor, hatch, parts, sw, caps, pc):
    import pyvista as pv
    import tempfile
    os.makedirs(RENDERS, exist_ok=True)
    tmp = tempfile.mkdtemp()
    cache = {}

    def mesh(shape, name):
        if name not in cache:
            p = os.path.join(tmp, name + ".stl")
            cq.exporters.export(cq.Workplane().add(C.to_file(shape)), p, tolerance=0.05, angularTolerance=0.2)
            cache[name] = pv.read(p)
        return cache[name]

    def scene(pl, mode, cut=None):
        sh = mesh(shell, "shell")
        if mode == "inside":
            pl.add_mesh(sh.clip(normal=(0, 0, 1), origin=(0, 0, 20.5), invert=True), color="#d9d4cb", opacity=0.35)
        elif mode == "xsec":
            pl.add_mesh(sh.clip(normal=(1, 0, 0), origin=(cut, 0, 0), invert=False), color="#d9d4cb")
        elif mode == "ysec":
            pl.add_mesh(sh.clip(normal=(0, 1, 0), origin=(0, C.WIDTH - cut, 0), invert=False), color="#d9d4cb")
        else:
            pl.add_mesh(sh, color="#d9d4cb", opacity=0.25)
        for nm, s, col in (("fundo", fundo, "#c9c2b4"), ("plate", plate, "#111214"), ("bfloor", bfloor, "#b8ad9b"),
                           ("hatch", hatch, "#a39886")):
            m = mesh(s, nm)
            if mode == "xsec":
                m = m.clip(normal=(1, 0, 0), origin=(cut, 0, 0), invert=False)
            elif mode == "ysec":
                m = m.clip(normal=(0, 1, 0), origin=(0, C.WIDTH - cut, 0), invert=False)
            if m.n_points:
                pl.add_mesh(m, color=col)
        for nm, s in parts.items():
            if nm not in PART_COL:
                continue
            m = mesh(s, "p_" + nm)
            if mode == "xsec":
                m = m.clip(normal=(1, 0, 0), origin=(cut, 0, 0), invert=False)
            elif mode == "ysec":
                m = m.clip(normal=(0, 1, 0), origin=(0, C.WIDTH - cut, 0), invert=False)
            if m.n_points == 0:
                continue
            op = 0.45 if nm == "main_board" and mode in ("inside", "iso") else 1.0
            pl.add_mesh(m, color=COLOURS[PART_COL[nm]], opacity=op)
        if mode in ("iso", "inside"):
            pl.add_mesh(mesh(sw, "sw"), color="#26282c")
    shots = [
        ("fit_iso", "iso", None, [(-60, -150, 170), (70, 50, 12), (0, 0, 1)], 30, None),
        ("fit_dentro", "inside", None, [(55, 50, 300), (55, 50, 0), (0, 1, 0)], None, 58),
        ("fit_corte_x30", "xsec", 30.0, [(-300, 50, 16), (30, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_x15", "xsec", 15.12, [(-300, 50, 16), (15, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y49", "ysec", 49.0, [(50, -300, 16), (50, 51, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y78", "ysec", C.SPK_C[1], [(50, -300, 16), (50, 22, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y21", "ysec", 21.0, [(50, -300, 16), (50, 79, 16), (0, 0, 1)], None, 30),
    ]
    for name, mode, cut, cam, va, ps in shots:
        pl = pv.Plotter(off_screen=True, window_size=(1600, 1000))
        pl.set_background("#f3f1ec")
        scene(pl, mode, cut)
        pl.camera_position = cam
        if ps:
            pl.enable_parallel_projection()
            pl.camera.parallel_scale = ps
        elif va:
            pl.camera.view_angle = va
        pl.enable_anti_aliasing("ssaa")
        pl.add_light(pv.Light(position=(-200, -300, 400), focal_point=(60, 50, 10), intensity=0.35))
        pl.screenshot(os.path.join(RENDERS, name + ".png"))
        pl.close()
        print("  renders/%s.png" % name)


def main():
    R = run(renders="--no-renders" not in sys.argv)
    print(json.dumps({k: R[k] for k in ("length", "collisions_with_case", "speaker", "panel", "battery", "rays", "weight")},
                     ensure_ascii=False, indent=1))
    print("pairs:", [p for p in R["pairs"]])
    print("gaps:", R["gap_to_shell"])
    print("stl:", R["stl"])


if __name__ == "__main__":
    main()
