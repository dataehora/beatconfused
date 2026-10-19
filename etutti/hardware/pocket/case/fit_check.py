"""eTuttino Pocket, SPEC v5 F3: does everything fit the Seixo case?

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/fit_check.py [--no-renders]

Builds every part the case holds as a solid, sized from the electronics'
contract pcb/PECAS.json (read at run time; the few numbers it doesn't give
are marked CHECK here) and placed where case.py reserves room for it, then:

  1. each part against the shell, the bottom plate, the switch plate and
     the other parts: overlap volume (must be 0) and the smallest gap;
  2. heights: each part's top against the lid above it;
  3. the speaker: sealed back volume, grille open area, grille -> membrane;
  4. the panel connectors (micro-B female, jack): wall left at the holes,
     the FPC ribbon's room (plug top -> under the block -> the trava), the VBUS wire;
     the knob recesses and the Teensy's program-button pinhole;
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


def conn_solids(pc):
    """The FPC micro-B female head + its trava bar, the user's plug overmould
    in the window, the jack (body, thread, nut) and the ribbon's zones (PECAS v5)."""
    j = pc["headphone_jack"]["datasheet_dims"]
    assert sorted(j["body"][:2]) == sorted(C.JACK_BODY[:2]) and j["body"][2] == C.JACK_BODY[2]
    cut = pc["micro_b_panel_cable"]["panel_cutout"]
    assert list(cut["hole"]) == list(C.FEM_HOLE[:2]) and cut["hole_corner_r"] == C.FEM_HOLE[2]
    head, bar = C.female_solids()
    jb, jt, jn = C.jack_solids()
    g = C.conn_geometry()
    # a user's plug overmould (~10.5 x 7, PECAS) pushed in up to the lip
    mo = C.local_solid(C.stadium(10.5, 7.0, 1.0, -g["fem_wall"] - 8.0, -C.FEM_LIP[0] - 0.05), g["fem_origin"], g["n"], C.FEM_Z)
    out = {"fem_head": head, "fem_trava": bar, "jack": jb, "jack_thread": jt, "jack_nut": jn, "plug_outside": mo}
    return out, C.ribbon_zones()


def controls_solids(pc):
    x0, y0, x1, y1, z0, z1 = C.POT_BODY
    pot = box(x0, y0, z0, x1, y1, z1)
    vx, vy = C.VOLUME_XY
    lid = C.z_interface(vy, C.TOP_T)
    bushing = cyl(vx, vy, z1, z1 + C.POT_BUSHING_L, 6.98)
    # the shaft cut to end 1.0 under the knob's top (L 20 from the body face, cut; see knob_geometry)
    shaft = cyl(vx, vy, z1 + C.POT_BUSHING_L, C.Z_IF + C.KNOB_LIFT + C.KNOB_H - 1.0, 5.98)
    bx0, by0, bx1, by1, bz0, bz1 = C.POT_BOARD
    potboard = box(bx0, by0, bz0, bx1, by1, bz1)
    potlegs = box(bx1, by0, C.CTRL_TOP + 0.2, C.POT_LEGS_X, by1, bz1)   # clipped legs: only above the controls board
    cx0, cy0, cx1, cy1 = C.CTRL_BOARD
    ctrl = box(cx0, cy0, C.CTRL_TOP - C.CTRL_T, cx1, cy1, C.CTRL_TOP)
    legs = box(cx0, cy0, C.CTRL_TOP - C.CTRL_T - C.CTRL_LEGS, cx1, cy1, C.CTRL_TOP - C.CTRL_T)
    for tx0, ty0, tx1, ty1 in C.CTRL_TABS:          # the EC11E's two tabs (E2b), with legs under them
        ctrl = ctrl.fuse(box(tx0, ty0, C.CTRL_TOP - C.CTRL_T, tx1, ty1, C.CTRL_TOP))
        legs = legs.fuse(box(tx0, ty0, C.CTRL_TOP - C.CTRL_T - C.CTRL_LEGS, tx1, ty1, C.CTRL_TOP - C.CTRL_T))
    e = pc["encoder"]["body"]
    sx, sy = C.SELECT_XY
    enc = box(sx - e["plan"][0] / 2, sy - e["plan"][1] / 2, C.CTRL_TOP, sx + e["plan"][0] / 2, sy + e["plan"][1] / 2,
              C.CTRL_TOP + e["height_above_pcb"])
    enc_shaft = cyl(sx, sy, C.CTRL_TOP + e["height_above_pcb"], C.CTRL_TOP + e["height_above_pcb"] + 5.0, 7.0).fuse(
        cyl(sx, sy, C.CTRL_TOP + e["height_above_pcb"] + 5.0, C.CTRL_TOP + e["height_above_pcb"] + e["shaft_l"], 5.98))
    led = pc["led"]["body"]
    lx, ly = C.LED_XY
    led_top = C.Z_IF - 0.5
    led_s = cyl(lx, ly, led_top - led["height"], led_top, led["d"]).fuse(
        cyl(lx, ly, led_top - led["height"], led_top - led["height"] + 1.0, led["flange_d"]))
    spacer = cyl(lx, ly, C.CTRL_TOP, led_top - led["height"], 4.0)
    a0, b0, a1, b1 = C.CTRL_CONN
    conn = box(a0, b0, C.CTRL_TOP, a1, b1, C.CTRL_TOP + 4.25 + 2.0)
    out = {"pot": pot.fuse(bushing).fuse(shaft), "pot_board": potboard.fuse(potlegs), "controls_board": ctrl, "controls_legs": legs,
           "encoder": enc.fuse(enc_shaft), "led": led_s.fuse(spacer), "controls_conn": conn}
    out.update(knob_solids(pc))
    return out


def knob_geometry(pc):
    """Numbers of the knob recesses (SPEC v5 4): pot nut flush in the lid,
    the thread left, the knob's engagement on each shaft."""
    z_lid = C.Z_IF
    z_floor = z_lid - C.KNOB_RECESS_DEPTH
    z_under = C.z_interface(C.KNOB_Y, C.TOP_T)
    face = C.POT_BODY[5] + (z_under - C.POT_BODY[5])      # clamped: the body face rises to the lid's underside
    bush_top = face + C.POT_BUSHING_L
    skirt = z_lid + C.KNOB_LIFT
    cav_top = skirt + C.KNOB_CAVITY[1]
    top = skirt + C.KNOB_H
    e = pc["encoder"]["body"]
    enc_tip = C.CTRL_TOP + e["height_above_pcb"] + e["shaft_l"]
    pot_tip = face + 20.0                                  # PECAS volume_pot: L 20 from the body face (L 15 also sold)
    ac = C.POT_NUT_AF / math.cos(math.radians(30))
    return {
        "recess_d": C.KNOB_RECESS_D, "recess_depth": C.KNOB_RECESS_DEPTH, "floor_t": round(z_floor - z_under, 2),
        "nut": {"af": C.POT_NUT_AF, "ac": round(ac, 2), "t": C.POT_NUT_T, "top_z": round(z_floor + C.POT_NUT_T, 2),
                "flush_with_lid": round(z_floor + C.POT_NUT_T - z_lid, 2),
                "corner_to_recess_wall": round((C.KNOB_RECESS_D - ac) / 2, 2)},
        "thread": {"bushing_l": C.POT_BUSHING_L, "clamped_floor": round(z_floor - z_under, 2),
                   "under_nut_top": round(z_floor + C.POT_NUT_T - face, 2),
                   "left_above_nut": round(bush_top - (z_floor + C.POT_NUT_T), 2),
                   "nut_engaged": C.POT_NUT_T},
        "knob": {"d": C.KNOB_D, "h": C.KNOB_H, "skirt_bottom_z": round(skirt, 2), "top_z": round(top, 2),
                 "covers_recess_by": round((C.KNOB_D - C.KNOB_RECESS_D) / 2, 2),
                 "skirt_to_nut_axial": round(skirt - (z_floor + C.POT_NUT_T), 2),
                 "cavity": list(C.KNOB_CAVITY), "cavity_to_bushing_top": round(cav_top - bush_top, 2),
                 "cavity_to_thread_radial": round((C.KNOB_CAVITY[0] - 7.0) / 2, 2),
                 "gap_between_knobs": round(C.SELECT_XY[0] - C.VOLUME_XY[0] - C.KNOB_D, 2),
                 "knob_to_led_hole": round(C.LED_XY[0] - C.SELECT_XY[0] - C.KNOB_D / 2 - C.LED_HOLE_D / 2, 2)},
        "engagement": {"pot_L20_tip_z": round(pot_tip, 2), "pot_L15_tip_z": round(face + 15.0, 2),
                       "pot_bore_from_z": round(cav_top, 2),
                       "pot_L20_cut_to_knob_top": round(top - 1.0 - cav_top, 2), "pot_L15": round(face + 15.0 - cav_top, 2),
                       "encoder_tip_z": round(enc_tip, 2), "encoder_L20": round(min(enc_tip, top - 1.0) - cav_top, 2),
                       "encoder_L25": round(min(enc_tip + 5.0, top - 1.0) - cav_top, 2)},
    }


def knob_solids(pc):
    """The pot nut in its recess and the two (proposed) knobs."""
    g = knob_geometry(pc)
    vx, vy = C.VOLUME_XY
    zf = C.Z_IF - C.KNOB_RECESS_DEPTH
    ac = C.POT_NUT_AF / math.cos(math.radians(30))
    nut = cq.Workplane("XY", origin=(vx, vy, zf)).polygon(6, ac).extrude(C.POT_NUT_T).val()
    nut = nut.cut(cyl(vx, vy, zf - 1, zf + 5, 7.0))
    out = {"pot_nut": nut}
    for nm, (x, y) in (("knob_vol", C.VOLUME_XY), ("knob_sel", C.SELECT_XY)):
        z0 = g["knob"]["skirt_bottom_z"]
        k = cyl(x, y, z0, z0 + C.KNOB_H, C.KNOB_D)
        k = k.cut(cyl(x, y, z0 - 1, z0 + C.KNOB_CAVITY[1], C.KNOB_CAVITY[0]))
        k = k.cut(cyl(x, y, z0, z0 + C.KNOB_H - 1.0, 6.0))
        out[nm] = k
    return out


def battery(pc):
    b = pc["battery"]["body"]
    t, w, l = b["with_pcm_and_wire_fold"]
    swell = t * (1 + b["swelling_allowance_pct"] / 100.0)
    c = C.BATT_C
    cell = box(c[0] - l / 2, c[1] - w / 2, C.BATT_Z[0], c[0] + l / 2, c[1] + w / 2, C.BATT_Z[0] + t)
    swollen = box(c[0] - l / 2, c[1] - w / 2, C.BATT_Z[0], c[0] + l / 2, c[1] + w / 2, C.BATT_Z[0] + swell)
    # the mated JST PH 3-way pair lying flat in the pocket, its axis along x (PECAS v3
    # battery.connector_pocket_v4.mated: 8.0 wide x 4.8 high x 12.5 long), centred
    m = pc["battery"]["connector_pocket_v4"]["parts"]["mated"]["dims_wxhxl"]
    x0, x1, y0 = C.BATT_POCKET
    y1 = C.BATT_C[1] - C.BATT_IN[1] / 2
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    plug = box(xm - m[2] / 2, ym - m[0] / 2, C.BATT_Z[0], xm + m[2] / 2, ym + m[0] / 2, C.BATT_Z[0] + m[1])
    return cell, swollen, plug


def board_connectors(pc):
    """J_BAT and J_SPK on the main board's top with their PH plugs in (PECAS
    main_board_connectors: B3B / B2B-PH-K-S vertical, 10.5 tall with the plug)."""
    out = {}
    for it in pc["main_board_connectors"]["items"]:
        if it["ref"] not in ("J_BAT", "J_SPK"):
            continue
        n = 3 if it["ref"] == "J_BAT" else 2
        L = 2.0 * (n - 1) + 3.9 + 0.05                      # PH body along the pin row
        x, y = it["at"]
        h = it.get("plug_height_total", 10.5)
        if it["rot"] in (90, 270):                          # pins along y from pin 1 (rot 270: +y)
            sol = box(x - 2.82, y - 1.95, C.Z_PCB_TOP, x + 1.72, y - 1.95 + L, C.Z_PCB_TOP + h)   # as the KiCad footprint
        else:
            sol = box(x - 1.95, y - 2.25, C.Z_PCB_TOP, x - 1.95 + L, y + 2.25, C.Z_PCB_TOP + h)
        out["j_" + it["ref"][2:].lower()] = sol
    return out


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


def min_radius(pts, k=2):
    """Smallest radius through every 3 points k apart along the centre line."""
    out = 1e9
    for i in range(k, len(pts) - k):
        a, b, c = pts[i - k], pts[i], pts[i + k]
        ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
        s2 = (ab + bc + ca) / 2
        A = max(s2 * (s2 - ab) * (s2 - bc) * (s2 - ca), 0.0) ** 0.5
        if A > 1e-9:
            out = min(out, ab * bc * ca / (4 * A))
    return out


def ray_probe():
    """Rays down the exported shell (file frame: y_file = 100 - y_spec)
    through each key's opening, each grille hole and each knob/LED hole:
    nothing may stop them (a film over the keys once hid in a render)."""
    import pyvista as pv
    m = pv.read(os.path.join(C.OUT, "seixo_tampa.stl"))
    res = {"keys": [0, 0], "grille": [0, 0], "holes": [0, 0], "panel": [0, 0], "button": [0, 0], "blocked": []}

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
    # the Teensy's program button: straight down the pinhole to the Teensy's parts
    bx, by = C.teensy_button_xy()
    for dx, dy in ((0, 0), (0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4)):
        free(bx + dx, by + dy, z1=C.Z_TEENSY_PARTS + 0.2, key="button")
    # sideways through the micro-B window and the jack hole: from outside the wall to the inner face
    g = C.conn_geometry()
    fo, n, t = g["fem_origin"], g["n"], (-g["n"][1], g["n"][0])
    rays = []
    # into the window up to the lip (the plug's overmould), then through the lip's opening into the tunnel
    for ds, dz, end in ((0, 0, 3.0), (5.0, 0, -0.6), (-5.0, 0, -0.6), (0, 3.0, -0.6), (0, -3.0, -0.6),
                        (3.6, 0, 3.0), (-3.6, 0, 3.0), (0, 1.4, 3.0), (0, -1.4, 3.0)):
        a, b = (fo[0] - n[0] * 12 + t[0] * ds, fo[1] - n[1] * 12 + t[1] * ds), (fo[0] + n[0] * end + t[0] * ds, fo[1] + n[1] * end + t[1] * ds)
        rays.append((a, b, C.FEM_Z + dz, "fem"))
    jo = g["jack_origin"]
    for dy, dz in ((0, 0), (3.2, 0), (-3.2, 0), (0, 3.2), (0, -3.2)):
        rays.append(((jo[0] - 12, jo[1] + dy), (jo[0] + 0.3, jo[1] + dy), C.JACK_Z + dz, "jack"))
    for a, b, z, k in rays:
        pts, _ = m.ray_trace((a[0], C.WIDTH - a[1], z), (b[0], C.WIDTH - b[1], z), first_point=False)
        ok = len(pts) == 0
        res["panel"][0 if ok else 1] += 1
        if not ok:
            res["blocked"].append([k, round(a[0], 2), round(a[1], 2), round(z, 2)])
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
    pan, ribbon = conn_solids(pc)
    ctl = controls_solids(pc)
    cell, swollen, bplug = battery(pc)
    bconn = board_connectors(pc)
    board, below = main_board()
    sw, caps, cap_list = keyboard()
    parts = {"main_board": board, "board_underside": below, **st, **pan, **ctl,
             "battery": swollen, "battery_plug": bplug, "speaker": spk_full, **bconn}
    case_parts = {"shell": shell, "fundo": fundo, "plate": plate, "box_floor": bfloor, "hatch": hatch}
    R = {"spec": "v5", "task": "F3", "length": round(C.length(), 2), "plan_vs_shape_py": round(C.check_plan(), 3)}

    # 1. every part against the case parts
    allowed = {("board_underside", "fundo"), ("main_board", "fundo"),   # pillars touch the board
               ("main_board", "shell"), ("board_underside", "shell"),   # screw notches are in the outline; checked by gap below
               ("pot", "shell"),                                       # the bushing goes through the lid
               ("plug_outside", "shell"), ("jack_thread", "shell")}    # through the window / hole (checked by gap below)
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
    pairs = [("usb_plug", "fem_head"), ("usb_plug", "fem_trava"), ("teensy_usb", "fem_trava"), ("teensy", "fem_head"),
             ("fem_head", "jack"), ("fem_trava", "jack"), ("jack", "j_bat"), ("jack", "pot"), ("jack", "pot_board"),
             ("jack", "encoder"), ("jack", "controls_board"), ("fem_trava", "j_bat"), ("fem_trava", "j_spk"),
             ("audio_board", "controls_board"), ("ab_jack", "controls_legs"), ("teensy", "controls_legs"),
             ("audio_board", "controls_legs"), ("audio_board", "pot_board"), ("ab_jack", "pot_board"),
             ("battery", "main_board"), ("battery", "board_underside"), ("speaker", "controls_board"),
             ("speaker", "encoder"), ("speaker", "pot"), ("controls_conn", "led"), ("encoder", "led"),
             ("pot", "encoder"), ("main_board", "speaker"), ("pot_board", "encoder"),
             ("pot", "controls_board"), ("pot_board", "controls_board"),
             ("j_bat", "battery_plug"), ("battery_plug", "main_board"),
             ("battery_plug", "battery"), ("battery_plug", "pot"), ("battery_plug", "pot_board"),
             ("pot_nut", "knob_vol"), ("pot", "knob_vol"), ("encoder", "knob_sel"), ("knob_vol", "knob_sel")]
    pair_res = []
    for a, b in pairs:
        pair_res.append([a, b, round(overlap(parts[a], parts[b]), 3), round(gap(parts[a], parts[b]), 2)])
    # the controls board's two tabs (E2b): back one over the stack, front one in the speaker box's dent
    tabs = []
    for tx0, ty0, tx1, ty1 in C.CTRL_TABS:
        t = box(tx0, ty0, C.CTRL_TOP - C.CTRL_T - C.CTRL_LEGS, tx1, ty1, C.CTRL_TOP)
        tabs.append({"rect": [tx0, ty0, tx1, ty1], "to_shell": round(gap(t, shell), 2),
                     "to_ab_jack": round(gap(t, parts["ab_jack"]), 2), "to_teensy": round(gap(t, parts["teensy"]), 2),
                     "to_audio_board": round(gap(t, parts["audio_board"]), 2), "to_speaker": round(gap(t, parts["speaker"]), 2),
                     "to_box_floor": round(gap(t, bfloor), 2), "to_pot_board": round(gap(t, parts["pot_board"]), 2)})
    R["controls_tabs"] = tabs
    R["logo"] = {"lines": [[l[0], round(l[4], 2), round(l[5], 2), l[2], round(l[6], 2), round(l[7], 2)] for l in C.logo_layout()["lines"]],
                 "bbox": [round(v, 2) for v in C.logo_layout()["bbox"]], "margins_lr_back_front": C.logo_layout()["margins"],
                 "depth": C.LOGO_DEPTH}
    R["collisions_with_case"] = coll
    R["gap_to_shell"] = gaps
    R["pairs"] = pair_res
    R["box_floor_vs_bay"] = round(gap(bfloor, fundo), 2)
    cp = list(case_parts.items())
    R["case_parts_overlap"] = {"%s/%s" % (a, b): round(overlap(sa, sb), 4) for i, (a, sa) in enumerate(cp) for b, sb in cp[i + 1:]}
    conn = pan["fem_head"].fuse(pan["fem_trava"]).fuse(pan["jack"])
    R["connectors_vs_columns"] = {"%g,%g" % xy: round(gap(conn, cyl(xy[0], xy[1], C.FLOOR_T, C.BOSS_TOP.get(xy, 40.0), C.BOSS_D)), 2)
                                  for xy in C.screw_points() if xy[0] < 70}
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
    box_in = C.poly_prism(inner, C.SPK_BOX_BOTTOM, 45.0).intersect(cav).cut(shell)   # less the ring and the tab's dent
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
    # 4. the panel connectors, the ribbon, the VBUS wire, the knobs, the Teensy button
    g = C.conn_geometry()
    obstacles = {**{k: v for k, v in parts.items() if k not in ("board_underside", "plug_outside")}, "shell": shell}
    rib = {}
    for k, z in ribbon.items():
        hits = {o: round(overlap(z, v), 3) for o, v in obstacles.items() if overlap(z, v) > 1e-3}
        bb = z.BoundingBox()
        rib[k] = {"hits": hits, "bbox": [round(v, 2) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)]}
    vw = C.cable_wire(C.vusb_wire_path()[1:-1])
    vcl = {k: round(vw.distance(v) - 0.6, 2) for k, v in obstacles.items() if k not in ("teensy", "audio_board")}
    pc_c = pc["micro_b_panel_cable"]
    zb0, ztop = C.fem_block_rect()[1]
    R["panel"] = {
        "female": {"kind": "FPC ribbon, 'UP' male, female head in a tunnel + trava", "origin": [round(v, 2) for v in g["fem_origin"]],
                   "axis": [round(v, 3) for v in g["n"]], "z": C.FEM_Z,
                   "wall_at_window_raw": round(g["fem_wall"], 2), "wall_at_window": C.FEM_WALL, "lip": list(C.FEM_LIP),
                   "outer_recess": list(C.FEM_RECESS), "outer_recess_depth": round(g["fem_wall"] - C.FEM_WALL, 2),
                   "window": list(C.FEM_HOLE), "tunnel": list(C.FEM_POCKET), "pecas_pocket": [12.4, 9.4, 4.4],
                   "head_in_tunnel": [round((C.FEM_POCKET[i] - C.FEM_HEAD[j]) / 2, 2) for i, j in ((0, 0), (2, 2))],
                   "block": {"width": C.FEM_BLOCK[0], "floor": C.FEM_BLOCK[1], "z": [round(zb0, 2), round(ztop, 2)]},
                   "screws": list(C.FEM_SCREWS), "trava": list(C.TRAVA),
                   "floor_over_plug_top": round(zb0 - C.stack_parts()["usb_plug"][1][1], 2),
                   "head_vs_shell": round(gap(pan["fem_head"], shell), 2), "trava_vs_jack": round(gap(pan["fem_trava"], pan["jack"]), 2),
                   "plug_overmould_in_window": round(gap(pan["plug_outside"], shell), 2)},
        "jack": {"origin": [round(v, 2) for v in g["jack_origin"]], "axis": [1.0, 0.0], "z": C.JACK_Z,
                 "wall_at_hole_raw": round(g["jack_wall"], 2), "wall_at_hole": C.JACK_WALL,
                 "spot_face_depth": round(g["jack_wall"] - C.JACK_WALL, 2), "hole_d": C.JACK_HOLE_D, "spot_d": C.JACK_SPOT_D,
                 "facet": list(C.JACK_FACET), "thread_in_hole_radial": round((C.JACK_HOLE_D - 8.0) / 2, 2),
                 "body_vs_shell": round(gap(pan["jack"], shell), 2), "nut_vs_shell": round(gap(pan["jack_nut"], shell), 2),
                 "room_behind": round(C.JACK_BODY[2] + C.JACK_TABS, 1),
                 "to_j_bat": round(gap(pan["jack"], parts["j_bat"]), 2), "to_pot_board": round(gap(pan["jack"], parts["pot_board"]), 2),
                 "to_pot": round(gap(pan["jack"], parts["pot"]), 2), "to_encoder": round(gap(pan["jack"], parts["encoder"]), 2),
                 "lid_over": round(C.z_interface(C.JACK_Y, C.TOP_T) - (C.JACK_Z + C.JACK_BODY[1] / 2), 2)},
        "ribbon": rib,
        "vusb_wire": {"clearance": dict(sorted(vcl.items(), key=lambda kv: kv[1])[:5])},
        "knob_recesses": knob_geometry(pc),
        "teensy_button": {"xy": [round(v, 2) for v in C.teensy_button_xy()], "hole_d": C.BTN_HOLE_D,
                          "depth_lid_to_teensy": round(C.Z_IF - C.Z_TEENSY_PARTS, 2),
                          "tube": [C.BTN_TUBE_D, round(C.Z_TEENSY_PARTS + C.BTN_TUBE_GAP, 2)],
                          "tube_vs_teensy": round(gap(C.button_tube(), st["teensy"]), 2),
                          "to_ramp_top_edge": round(C.interface_band(C.teensy_button_xy()[1])[1] - C.teensy_button_xy()[0], 2),
                          "to_logo": round(C.teensy_button_xy()[0] - C.logo_layout()["bbox"][2], 2)},
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
        "plug_in_pocket_to_fundo": round(gap(bplug, fundo), 2),
        "plug_in_pocket_overlap": round(overlap(bplug, fundo), 4),
        "pocket_inside": [round(C.BATT_POCKET[1] - C.BATT_POCKET[0], 2), round(C.BATT_C[1] - C.BATT_IN[1] / 2 - C.BATT_POCKET[2], 2),
                          round(C.BATT_Z[1] - C.BATT_Z[0], 2)],
        "pocket_min_pecas": [pc["battery"]["connector_pocket_v4"]["pocket_min"][k] for k in ("x_along_axis", "y", "z")],
        "pocket_to_shell": round(gap(fundo.intersect(C.poly_prism(C.pocket_rects()[1], 0, 20)), shell), 2),
        "bay_to_shell": round(gap(fundo.intersect(C.poly_prism(C.battery_rects()[1], 0, 20)), shell), 2),
    }
    # 6. heights under the lid
    R["heights"] = {
        "pot_body_top": C.POT_BODY[5], "lid_under_at_knobs": round(C.z_interface(C.KNOB_Y, C.TOP_T), 2),
        "encoder_top": round(C.CTRL_TOP + pc["encoder"]["body"]["height_above_pcb"], 2),
        "teensy_usb_top": round(C.Z_USB_TOP, 2), "plug_top": round(C.stack_parts()["usb_plug"][1][1], 2),
        "female_head": [round(C.FEM_Z - C.FEM_HEAD[2] / 2, 2), round(C.FEM_Z + C.FEM_HEAD[2] / 2, 2)],
        "female_block": [round(v, 2) for v in C.fem_block_rect()[1]],
        "jack_body": [round(C.JACK_Z - C.JACK_BODY[1] / 2, 2), round(C.JACK_Z + C.JACK_BODY[1] / 2, 2)],
        "controls_board": [round(C.CTRL_TOP - C.CTRL_T, 2), C.CTRL_TOP],
    }
    # 7. exports
    names = ["seixo_tampa", "seixo_fundo", "seixo_tampa_bateria", "seixo_caixa_fundo", "plate", "seixo_trava_usb", "seixo_chave_porca"]
    capn = ["keycap_natural", "keycap_sharp", "keycap_cf", "keycap_test_4"]
    R["stl"] = stl_checks(names + capn)
    R["rays"] = ray_probe()
    # 8. weight
    vol = sum(R["stl"][n]["volume_cm3"] for n in names if n != "plate")
    R["weight"] = {"printed_cm3": round(vol, 1),
                   **{k: round(vol * d, 0) for k, d in DENSITY.items()},
                   "plate_fr4_g": round(R["stl"]["plate"]["volume_cm3"] * 1.85, 0)}
    # SPEC v4 change 5: top shell in resin, the rest in MJF; the 28 caps in resin
    cc = C.cap_counts()
    caps_cm3 = sum(R["stl"]["keycap_" + k]["volume_cm3"] * n for k, n in cc.items())
    shell_g = R["stl"]["seixo_tampa"]["volume_cm3"] * DENSITY["resin_g"]
    mjf_g = sum(R["stl"][n]["volume_cm3"] for n in ("seixo_fundo", "seixo_tampa_bateria", "seixo_caixa_fundo", "seixo_trava_usb", "seixo_chave_porca")) * DENSITY["mjf_pa12_g"]
    R["weight"]["v4_materials"] = {"top_shell_resin_g": round(shell_g, 1), "mjf_parts_g": round(mjf_g, 1),
                                   "caps_resin_g": round(caps_cm3 * DENSITY["resin_g"], 1), "cap_counts": cc,
                                   "printed_total_g": round(shell_g + mjf_g + caps_cm3 * DENSITY["resin_g"], 0)}
    with open(os.path.join(C.OUT, "fit_check.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    if renders:
        render_all(shell, fundo, plate, bfloor, hatch, parts, sw, caps, pc, ribbon)
    return R


# ------------------------------------------------------------- pictures
COLOURS = {"pcb": "#2f7d4a", "ab": "#1d5d3b", "teensy": "#3aa86b", "batt": "#d08a3c", "spk": "#8a6a48",
           "ctrl": "#6b4a92", "metal": "#9a9a9a", "dark": "#26282c", "plug": "#444444", "panel": "#3c7a9a", "knob": "#efece6"}
PART_COL = {"main_board": "pcb", "audio_board": "ab", "teensy": "teensy", "teensy_usb": "metal", "usb_plug": "plug",
            "ab_jack": "dark", "fem_head": "panel", "fem_trava": "panel", "jack": "dark", "jack_nut": "metal",
            "plug_outside": "plug", "pot_nut": "metal", "knob_vol": "knob", "knob_sel": "knob", "pot": "ctrl", "pot_board": "ctrl",
            "controls_board": "ctrl", "encoder": "metal", "led": "metal", "controls_conn": "dark", "battery": "batt",
            "speaker": "spk", "battery_plug": "dark", "j_bat": "plug", "j_spk": "plug"}


def render_all(shell, fundo, plate, bfloor, hatch, parts, sw, caps, pc, ribbon):
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
        elif mode == "inside_hi":
            pl.add_mesh(sh.clip(normal=(0, 0, 1), origin=(0, 0, 30.3), invert=True), color="#d9d4cb", opacity=0.6)
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
        if mode in ("iso", "inside", "inside_hi"):
            pl.add_mesh(mesh(sw, "sw"), color="#26282c")
        if mode in ("inside_hi", "ysec", "xsec"):
            for k, z in ribbon.items():
                m = mesh(z, "rib_" + k)
                if mode == "xsec":
                    m = m.clip(normal=(1, 0, 0), origin=(cut, 0, 0), invert=False)
                elif mode == "ysec":
                    m = m.clip(normal=(0, 1, 0), origin=(0, C.WIDTH - cut, 0), invert=False)
                if m.n_points:
                    pl.add_mesh(m, color="#e0b33a", opacity=0.55)
    shots = [
        ("fit_iso", "iso", None, [(-60, -150, 170), (70, 50, 12), (0, 0, 1)], 30, None),
        ("fit_dentro", "inside", None, [(55, 50, 300), (55, 50, 0), (0, 1, 0)], None, 58),
        ("fit_corte_x30", "xsec", 30.0, [(-300, 50, 16), (30, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_x15", "xsec", 15.12, [(-300, 50, 16), (15, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y49", "ysec", 49.0, [(50, -300, 16), (50, 51, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y78", "ysec", C.SPK_C[1], [(50, -300, 16), (50, 22, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y21", "ysec", 21.0, [(50, -300, 16), (50, 79, 16), (0, 0, 1)], None, 30),
        ("fit_corte_x31", "xsec", 31.12, [(-300, 50, 16), (31, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_x18", "xsec", 18.0, [(-300, 50, 16), (18, 50, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y44", "ysec", 44.5, [(50, -300, 16), (50, 55.5, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y38", "ysec", C.JACK_Y, [(50, -300, 16), (50, 62, 16), (0, 0, 1)], None, 30),
        ("fit_corte_y27", "ysec", 27.0, [(50, -300, 16), (50, 73, 16), (0, 0, 1)], None, 30),
        ("fit_conectores", "inside_hi", None, [(35, 74, 220), (35, 74, 0), (0, 1, 0)], None, 24),
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
