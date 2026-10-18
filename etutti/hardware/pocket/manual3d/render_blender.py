"""The Pocket assembly manual's pictures, rendered in Blender (Cycles):

    blender -b --python render_blender.py -- [shot ...] [--fast]

Adapted from etutti/hardware/manual3d/render_blender.py (the eTuttino's,
unchanged). Builds the assembled Pocket from the case STLs (../case/out),
the four KiCad boards (build/*.glb, placed by build/assembly.json) and the
parts library (build/lib, parts.py), then renders each shot of SHOTS as

  "real"  photo-like: PBR materials, studio light, perspective camera;
  "line"  a line drawing: flat white parts, black outlines (Freestyle), the
          parts of that step amber and heavier; orthographic camera.

Each shot shows only the groups it lists ("show"); "new" are amber,
"explode" moves whole groups. For every shot it writes build/shots/<name>.json
with the balloons, arrows and dimension lines projected to pixels, for
annotate.py. Units: metres in Blender, mm here (M()). Frame: the case
files' (x right, y away from the player, z up).
"""
import json
import math
import os
import sys

import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
LIB = os.path.join(BUILD, "lib")
CASE_OUT = os.path.normpath(os.path.join(HERE, "..", "case", "out"))
SHOTS_DIR = os.path.join(BUILD, "shots")
A = json.load(open(os.path.join(BUILD, "assembly.json")))
Z = A["z"]
W = A["width"]
PTS = A["points"]


def M(*v):
    return tuple(x / 1000.0 for x in v)


F = lambda y: W - y        # SPEC y -> file y

COLOURS = {
    "case_seixo": ("#d3cdc2", 0.55, 0.0), "pcb_teensy": ("#1d5e34", 0.35, 0.0), "pcb_audio": ("#1d5e34", 0.35, 0.0),
    "chip": ("#141414", 0.55, 0.0), "steel": ("#c9cacc", 0.28, 1.0), "alu": ("#d4d6d8", 0.33, 1.0),
    "brass": ("#bdb6a6", 0.3, 1.0), "tin": ("#dcdcdc", 0.22, 1.0), "plastic_black": ("#121212", 0.5, 0.0),
    "plastic_dark": ("#1c1d20", 0.5, 0.0), "stem": ("#ecebe6", 0.45, 0.0), "plastic_white": ("#f1eee5", 0.5, 0.0),
    "button": ("#f4f4f4", 0.4, 0.0), "cap0402": ("#8c7b5d", 0.5, 0.0), "cap0805": ("#8c7b5d", 0.5, 0.0),
    "knob": ("#2a2a2c", 0.5, 0.0), "natural": ("#f4f2ee", 0.32, 0.0), "sharp": ("#1d1d1f", 0.32, 0.0),
    "cf": ("#f4f2ee", 0.32, 0.0), "plate": ("#121314", 0.42, 0.0), "cable_black": ("#151515", 0.45, 0.0),
    "case_mjf": ("#bfb8ab", 0.75, 0.0), "lipo": ("#b9bcc2", 0.3, 0.8), "kapton": ("#d9902a", 0.35, 0.0),
    "foam": ("#3a3a3c", 0.95, 0.0), "paper": ("#2b2622", 0.8, 0.0), "shim": ("#b58f5e", 0.9, 0.0),
}
WIRE_COLOURS = ["#1a1a1a", "#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#2e86c1", "#8e44ad", "#bdc3c7"]
MATS = {}


def hex_rgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def principled(name, colour, rough=0.5, metal=0.0, **extra):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_rgb(colour)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in extra.items():
        b.inputs[k].default_value = v
    return m


def build_materials(led_colour=None):
    for name, (c, r, mt) in COLOURS.items():
        MATS[name] = principled(name, c, r, mt)
    MATS["smoke"] = principled("smoke", "#2d3036", 0.15, 0.0, **{"Transmission Weight": 0.55, "IOR": 1.5})
    MATS["led_lens"] = principled("led_lens", "#f2efe9", 0.08, 0.0, **{"Transmission Weight": 0.7, "IOR": 1.5})
    if led_colour:
        b = MATS["led_lens"].node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = hex_rgb(led_colour)
        b.inputs["Emission Strength"].default_value = 6.0
    MATS["led_orange"] = principled("led_orange", "#ff9a2e", 0.3, 0.0)
    for i, c in enumerate(WIRE_COLOURS):
        MATS["wire%d" % i] = principled("wire%d" % i, c, 0.45)
    for name, c in (("line_white", "#ffffff"), ("line_new", "#f6d58f")):
        mm = bpy.data.materials.new(name)
        mm.use_nodes = True
        nt = mm.node_tree
        nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = hex_rgb(c)
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(e.outputs[0], o.inputs[0])
        MATS[name] = mm


GROUPS = {}
OBJ_GROUP = {}
OWN_ROOTS = {}          # group -> board sub-trees (e.g. J_BAT inside the main board) that move with it


def group(name):
    if name not in GROUPS:
        e = bpy.data.objects.new("G_" + name, None)
        bpy.context.scene.collection.objects.link(e)
        GROUPS[name] = e
    return GROUPS[name]


def attach(obj, gname):
    obj.parent = group(gname)
    OBJ_GROUP[obj.name] = gname


def import_stl(path, mat, gname, loc=(0, 0, 0), rot=(0, 0, 0), name=None):
    bpy.ops.wm.stl_import(filepath=path, global_scale=0.001)
    o = bpy.context.selected_objects[0]
    if name:
        o.name = name
    o.data.materials.clear()
    o.data.materials.append(MATS[mat])
    o.location = M(*loc)
    o.rotation_euler = [math.radians(a) for a in rot]
    for p in o.data.polygons:
        p.use_smooth = False
    attach(o, gname)
    return o


def import_board(spec):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(BUILD, spec["glb"]))
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new("H_" + spec["group"], None)
    bpy.context.scene.collection.objects.link(holder)
    for r in [o for o in new if o.parent is None]:
        r.parent = holder
    m = spec["matrix"]
    holder.matrix_world = mathutils.Matrix([[m[i][0], m[i][1], m[i][2], m[i][3] / 1000.0] for i in range(3)] + [[0, 0, 0, 1]])
    holder.parent = group(spec["group"])
    for o in new:
        OBJ_GROUP[o.name] = spec["group"]
        if o.type == "MESH":
            for p in o.data.polygons:
                p.use_smooth = False
            for mt in o.data.materials:
                if mt and mt.node_tree and "Principled BSDF" in mt.node_tree.nodes:
                    b = mt.node_tree.nodes["Principled BSDF"]
                    b.inputs["Alpha"].default_value = 1.0
                    r, g, bl, _ = b.inputs["Base Color"].default_value
                    if g > r * 1.5 and g > bl and g < 0.4:
                        b.inputs["Base Color"].default_value = hex_rgb("#1b5a33")
                    b.inputs["Roughness"].default_value = min(b.inputs["Roughness"].default_value, 0.45)
    names = {o.name.split(".")[0]: o for o in new}
    for ref, g in spec.get("own_groups", {}).items():
        o = names.get(ref)
        if o:
            OWN_ROOTS.setdefault(g, []).append(o)
            for c in [o] + list(o.children_recursive):
                OBJ_GROUP[c.name] = g
    for ref in spec.get("hide", []):
        o = names.get(ref)
        if o:
            for c in [o] + list(o.children_recursive):
                OBJ_GROUP[c.name] = "_hidden"


def cable(name, pts_mm, d, mat, gname):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = d / 2000.0
    cu.bevel_resolution = 3
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts_mm) - 1)
    for p, xyz in zip(sp.points, pts_mm):
        p.co = (*M(*xyz), 1.0)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(pts_mm))
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(MATS[mat])
    attach(o, gname)
    return o


def build_scene(led_colour=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    GROUPS.clear()
    OBJ_GROUP.clear()
    OWN_ROOTS.clear()
    MATS.clear()
    build_materials(led_colour)
    sc = bpy.context.scene
    for f, mat, g in (("seixo_tampa", "case_seixo", "lid"), ("seixo_fundo", "case_mjf", "bottom"),
                      ("seixo_tampa_bateria", "case_mjf", "hatch"), ("seixo_caixa_fundo", "case_mjf", "box_floor"),
                      ("plate", "plate", "plate")):
        import_stl(os.path.join(CASE_OUT, f + ".stl"), mat, g, name=g)
    for spec in A["boards"].values():
        import_board(spec)
    cache = {}
    for i, inst in enumerate(A["instances"]):
        part = inst["part"]
        for f in sorted(os.listdir(LIB)):
            p, mat, _ = f.split(".")
            if p != part:
                continue
            key = (part, mat)
            nm = "%s_%d_%s" % (inst["tag"], i, mat)
            if key not in cache:
                cache[key] = import_stl(os.path.join(LIB, f), mat, inst["group"], inst["loc"], inst["rot"], name=nm)
            else:
                o = cache[key].copy()
                o.data = cache[key].data
                sc.collection.objects.link(o)
                o.location = M(*inst["loc"])
                o.rotation_euler = [math.radians(a) for a in inst["rot"]]
                o.name = nm
                attach(o, inst["group"])
    caps = {}
    for kind in ("natural", "sharp", "cf"):
        caps[kind] = import_stl(os.path.join(CASE_OUT, "keycap_%s.stl" % kind), kind, "caps", name="cap_" + kind)
    keys = json.load(open(os.path.join(BUILD, "keys.json")))
    for kind, o in caps.items():
        top = max(v.co.z for v in o.data.vertices)
        first = True
        for k in keys:
            if k["kind"] != kind:
                continue
            ob = o if first else o.copy()
            if not first:
                sc.collection.objects.link(ob)
                attach(ob, "caps")
            ob.location = M(k["x"], F(k["y"]), Z["key_top"] - top)
            first = False
    for c in A["cables"]:
        cable(c["name"], c["pts"], c["d"], c["mat"], c["group"])
    return sc


def solo_scene(stl, mat):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    GROUPS.clear()
    OBJ_GROUP.clear()
    MATS.clear()
    build_materials()
    o = import_stl(os.path.join(CASE_OUT, stl), mat, "solo", name="solo")
    bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    c = sum(bb, mathutils.Vector()) / 8
    o.location = o.location - mathutils.Vector((c.x, c.y, min(v.z for v in bb)))
    return bpy.context.scene


def setup_render(sc, res, samples, transparent=False):
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"


def studio(sc, target, radius, floor=True):
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_rgb("#f3f1ec")
    bg.inputs["Strength"].default_value = 0.35
    sc.world = world
    t = mathutils.Vector(M(*target))
    r = radius / 1000.0
    for name, (dx, dy, dz), power, size in (("key", (-1.0, -1.6, 1.8), 900, 1.2), ("fill", (1.6, -0.8, 0.9), 300, 1.5),
                                            ("rim", (0.4, 1.6, 1.2), 500, 0.8), ("top", (0, 0, 2.5), 250, 2.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = power * r * r * 0.2
        ld.size = size * r
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = t + mathutils.Vector((dx, dy, dz)) * r
        lo.rotation_euler = (t - lo.location).to_track_quat("-Z", "Y").to_euler()
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=50 * r, location=(t.x, t.y, -0.0002))
        fl = bpy.context.active_object
        fl.data.materials.append(principled("floor", "#f3f1ec", 0.9))
        fl.is_shadow_catcher = True


def camera(sc, loc, target, lens=None, ortho=None, up="Y"):
    cd = bpy.data.cameras.new("cam")
    co = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(co)
    co.location = M(*loc)
    co.rotation_euler = (mathutils.Vector(M(*target)) - co.location).to_track_quat("-Z", up).to_euler()
    cd.clip_start, cd.clip_end = 0.001, 10.0
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho / 1000.0
    else:
        cd.lens = lens or 70
    sc.camera = co
    return co


def lineart(sc, new_groups):
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    world = bpy.data.worlds.new("wl")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    sc.world = world
    hl = bpy.data.collections.new("HIGHLIGHT")
    sc.collection.children.link(hl)
    for o in list(bpy.data.objects):
        if o.type not in ("MESH", "CURVE") or o.hide_render:
            continue
        new = OBJ_GROUP.get(o.name) in new_groups
        mat = MATS["line_new" if new else "line_white"]
        if o.type == "MESH" and o.data.users > 1:
            o.data = o.data.copy()
        elif o.type == "CURVE":
            o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(mat)
        if new:
            hl.objects.link(o)
    fs = sc.view_layers[0].freestyle_settings
    fs.crease_angle = math.radians(134)
    for ls in list(fs.linesets):
        fs.linesets.remove(ls)
    for name, neg, colour, thick in (("new", "INCLUSIVE", (0, 0, 0), 2.4), ("ctx", "EXCLUSIVE", (0.42, 0.42, 0.42), 1.3)):
        ls = fs.linesets.new(name)
        ls.select_by_collection = True
        ls.collection = hl
        ls.collection_negation = neg
        ls.select_by_visibility = True
        ls.visibility = "VISIBLE"
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        ls.select_external_contour = True
        ls.linestyle.color = colour
        ls.linestyle.thickness = thick
        ls.linestyle.caps = "ROUND"
        ls.linestyle.chaining = "PLAIN"


def show_only(groups):
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE"):
            o.hide_render = OBJ_GROUP.get(o.name) not in groups


def explode(offsets):
    bpy.context.view_layer.update()
    for g, d in offsets.items():
        if g in GROUPS:
            GROUPS[g].location = M(*d)
        for o in OWN_ROOTS.get(g, []):
            o.matrix_world = mathutils.Matrix.Translation(mathutils.Vector(M(*d))) @ o.matrix_world


def section(sc, axis, value, keep_greater=True):
    """Cut every visible mesh at axis = value (mm), keeping the greater (or
    smaller) side, with an exact boolean."""
    i = "xyz".index(axis)
    loc = [0.12, 0.05, 0.02]
    loc[i] = value / 1000.0 + (-0.5 if keep_greater else 0.5)
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    cutter = bpy.context.active_object
    cutter.hide_render = True
    v = value / 1000.0
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o is cutter or o.hide_render or o.name.startswith("Plane"):
            continue
        wb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        lo, hi = min(p[i] for p in wb), max(p[i] for p in wb)
        if (keep_greater and lo > v) or (not keep_greater and hi < v):
            continue
        if (keep_greater and hi < v) or (not keep_greater and lo > v):
            o.hide_render = True
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        mod = o.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        mod.solver = "EXACT"
    for o in list(bpy.data.objects):          # cables (curves) on the removed side
        if o.type == "CURVE" and not o.hide_render:
            wb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            mid = sum(p[i] for p in wb) / 8
            if (keep_greater and mid < v) or (not keep_greater and mid > v):
                o.hide_render = True


def project(sc, pts):
    cam = sc.camera
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    out = []
    for p in pts:
        v = world_to_camera_view(sc, cam, mathutils.Vector(M(*p)))
        out.append([round(v.x * rx, 1), round((1 - v.y) * ry, 1)])
    return out


# ------------------------------------------------------------- the shots
# Balloon numbers = the parts list in the manual (STYLE.md); letters = test points.
CASE = ["lid", "bottom", "hatch", "box_floor"]
INSIDE = ["board", "jbat", "jspk", "plugs", "stack", "hp_wires", "plate", "switches", "pot", "pot_board", "encoder", "led",
          "ctrl_board", "ctl_cable", "panel_board", "usb_c", "jack", "usb_cable", "pnl_cable", "speaker", "gasket",
          "spk_wires", "battery", "pigtail", "board_screws", "board_nuts", "ctrl_screws", "panel_screw"]
ALL = CASE + INSIDE + ["caps", "knobs", "pot_nut", "case_screws", "hatch_screws"]
STACK = ["stack", "vusb"]


def iso(tgt, scale, d=(-1.0, -1.25, 1.05), r=400):
    return ((tgt[0] + d[0] * r, tgt[1] + d[1] * r, tgt[2] + d[2] * r), tgt, None, scale)


def shots():
    zt = Z["pcb_top"]
    zc = Z["controls_top"]
    zp = Z["panel_top"]
    P = PTS
    tc = P["teensy_c"]
    S = {}
    C_PL = Z["plate_top"]
    # ---------------- photo-like
    S["r_hero"] = dict(mode="real", res=(2400, 1400), samples=192, show=ALL,
                       cam=((-120, -230, 210), (125, 50, 10), 55), exposure=-0.4)
    S["r_exploded"] = dict(mode="real", res=(2400, 2000), samples=160, show=ALL + ["shim"][:0],
                           cam=((-170, -330, 330), (120, 50, 70), 50), exposure=-0.3,
                           explode={"case_screws": (0, 0, -40), "hatch_screws": (0, 0, -40), "hatch": (0, 0, -28),
                                    "board_screws": (0, 0, -30), "bottom": (0, 0, -14), "battery": (0, 0, -6),
                                    "board_nuts": (0, 0, 22), "board": (0, 0, 8), "jbat": (0, 0, 8), "jspk": (0, 0, 8),
                                    "plugs": (0, 0, 8), "hp_wires": (0, 0, 8), "stack": (0, 0, 24), "usb_cable": (0, 0, 24),
                                    "plate": (0, 0, 40), "switches": (0, 0, 58), "caps": (0, 0, 92),
                                    "box_floor": (0, 0, 70), "speaker": (0, 0, 84), "gasket": (0, 0, 86),
                                    "spk_wires": (0, 0, 84), "pot": (0, 0, 78), "pot_board": (0, 0, 78),
                                    "ctrl_board": (0, 0, 78), "encoder": (0, 0, 78), "led": (0, 0, 78),
                                    "ctl_cable": (0, 0, 60), "ctrl_screws": (0, 0, 66), "panel_board": (0, 0, 70),
                                    "usb_c": (0, 0, 70), "jack": (0, 0, 70), "pnl_cable": (0, 0, 60),
                                    "panel_screw": (0, 0, 60), "pigtail": (0, 0, 0), "lid": (0, 0, 165),
                                    "pot_nut": (0, 0, 185), "knobs": (0, 0, 200)},
                           balloons=[(1, (150, F(98), -12)), (2, (200, F(99), 182)), (3, (200, F(88), zt + 8)),
                                     (4, (230, F(58), C_PL + 40)), (5, (240, F(58), C_PL + 64)), (6, (225, F(58), 26.6 + 92)),
                                     (24, (P["spk"][0], P["spk"][1] - 12, 106)), (27, (P["batt"][0], P["batt"][1] - 18, 0)),
                                     (15, (P["pot"][0], P["pot"][1], 212))])
    S["r_keycap_test"] = dict(mode="real", solo=("keycap_test_4.stl", "natural"), res=(1600, 1100), samples=160,
                              cam=((-30, -95, 85), (0, 0, 2), 60), exposure=-1.0)
    S["r_stack"] = dict(mode="real", res=(2000, 1300), samples=192, show=STACK,
                        cam=((tc[0], tc[1] - 160, 13.5), (tc[0], tc[1], 13.5), 85), floor=False,
                        dims=[((tc[0] - 21, tc[1] - 22, Z["ab"]), (tc[0] - 21, tc[1] - 22, Z["ab"] + 8.7), "8,7")],
                        balloons=[(7, (tc[0] + 10, tc[1] - 9, Z["teensy_top"])), (8, (tc[0] + 14, tc[1] - 21, Z["ab"] + 0.8)),
                                  (9, (tc[0] + 8, tc[1] - 7.6, Z["ab"] + 3.0))])
    for name, y_spec in (("r_section_y21", 21.0), ("r_section_y49", 49.0)):
        S[name] = dict(mode="real", res=(2400, 1250), samples=192, show=ALL, floor=False,
                       cam=((52, -260, 20), (52, F(y_spec), 18), None, 104), section=("y", F(y_spec), True))
    S["r_section_y21"]["balloons"] = [(16, (P["usb_c"][0] + 6, F(21), zp - 0.8)), (7, (45, F(21), Z["teensy_top"])),
                                      (8, (60, F(21), Z["ab"] + 0.8)), (19, (24, F(21), 18)), (3, (80, F(21), zt)),
                                      (2, (95, F(21), 34)), (1, (95, F(21), 1))]
    S["r_section_y49"]["balloons"] = [(12, (P["pot"][0] - 3, F(49), 24)), (13, (P["encoder"][0], F(49), 21)),
                                      (14, (P["led"][0], F(49), 29)), (27, (40, F(49), 5)), (28, (18, F(49), 4)),
                                      (10, (46, F(49), zc)), (11, (22.4, F(49), 22))]
    S["r_section_x30"] = dict(mode="real", res=(2400, 1100), samples=192, show=ALL, floor=False,
                              cam=((-250, 50, 20), (30, 50, 18), None, 116), section=("x", 30.0, True),
                              balloons=[(24, (30, F(77), 22)), (26, (30, F(80), 11.5)), (27, (30, F(68), 6)),
                                        (13, (30, F(49), 21)), (8, (30, F(30), Z["ab"] + 0.8)), (7, (30, F(20), 16))])
    for name, col in (("r_led_red", "#ff2a14"), ("r_led_off", None)):
        S[name] = dict(mode="real", res=(1400, 1000), samples=128, show=ALL, led=col, exposure=-0.6,
                       cam=((P["led"][0] - 40, P["led"][1] - 70, 95), (P["led"][0] - 8, P["led"][1], 33), 70))
    # ---------------- line drawings, one per step
    S["l_teensy_cut"] = dict(mode="line", show=["stack", "vusb"], new=["vusb"], hide_tags=["audio_board", "header", "solder"],
                             cam=((tc[0] - 60, tc[1] - 70, Z["ab"] - 90), (tc[0] - 8, tc[1], 15.2), None, 40), res=(1800, 1300),
                             balloons=[(7, (tc[0] + 10, tc[1] + 6, 15.2))],
                             arrows=[((tc[0] - 11.6, tc[1] - 9, 15.2 - 6), (tc[0] - 11.6, tc[1] - 1.5, 15.2 - 0.2))])
    S["l_audio_wires"] = dict(mode="line", show=["stack", "hp_wires"], new=["hp_wires"], hide_tags=["teensy", "header", "solder"],
                              cam=((40, F(35) - 70, Z["ab"] - 85), (38, F(35), Z["ab"]), None, 48), res=(1800, 1300),
                              balloons=[(8, (55, F(25), Z["ab"])), (31, (37, F(37), Z["ab"] - 3))])
    S["l_stack"] = dict(mode="line", show=["stack"], new=["stack"], hide_tags=["solder"],
                        tag_explode={"teensy": (0, 0, 24), "header": (0, 0, 12)},
                        cam=iso((tc[0], tc[1], 22), 88), res=(2000, 1600),
                        balloons=[(7, (tc[0] + 8, tc[1], 15.2 + 24 + 1.6)), (9, (tc[0] - 12, F(12.76), Z["ab"] + 1.6 + 12 + 2.9)),
                                  (8, (60, F(36), Z["ab"] + 1.6))],
                        arrows=[((72, tc[1], 15.2 + 30), (72, tc[1], 15.2 + 12))])
    S["l_connectors"] = dict(mode="line", show=["board", "jbat", "jspk"], new=["jbat", "jspk"],
                             explode={"jbat": (0, 0, 10), "jspk": (0, 0, 10)},
                             cam=iso((25, F(32), zt), 70), res=(2000, 1500),
                             balloons=[(22, (P["jbat"][0], P["jbat"][1], zt + 16)), (23, (P["jspk"][0], P["jspk"][1], zt + 16)),
                                       (20, (P["jpnl"][0], P["jpnl"][1], zt + 1)), (21, (P["jctl"][0], P["jctl"][1], zt + 1)),
                                       (31, (P["jhp"][0], P["jhp"][1], zt)), (3, (60, F(10), zt))],
                             arrows=[((P["jbat"][0] - 6, P["jbat"][1], zt + 14), (P["jbat"][0] - 6, P["jbat"][1], zt + 4))])
    S["l_stack_main"] = dict(mode="line", show=["board", "jbat", "jspk", "stack", "shim", "hp_wires"],
                             new=["stack", "shim", "hp_wires"], explode={"stack": (0, 0, 16), "hp_wires": (0, 0, 0)},
                             cam=iso((48, F(24), 14), 95), res=(2000, 1500),
                             balloons=[(7, (tc[0] + 8, tc[1], 15.2 + 16 + 1.6)), (38, (60, F(37), zt + 3)),
                                       (31, (P["jhp"][0], P["jhp"][1], zt + 2)), (3, (80, F(10), zt))],
                             arrows=[((tc[0] + 22, tc[1], 15.2 + 16), (tc[0] + 22, tc[1], 15.2 + 4))])
    S["l_switches"] = dict(mode="line", show=["board", "jbat", "jspk", "stack", "plate", "switches"], new=["plate", "switches"],
                           explode={"plate": (0, 0, 20), "switches": (0, 0, 40)}, cam=iso((140, 50, 20), 230),
                           res=(2400, 1500),
                           balloons=[(5, (220, F(40), 52)), (4, (230, F(60), 33)), (3, (150, F(93), zt))],
                           arrows=[((200, F(15), 64), (200, F(15), 48)), ((210, F(12), 34), (210, F(12), 24))])
    S["l_pot_board"] = dict(mode="line", show=["pot", "pot_board"], new=["pot"], explode={"pot": (-14, 0, 0)},
                            cam=iso((18, F(49), 24), 60, d=(-1.2, -0.9, 0.7)), res=(1800, 1400),
                            balloons=[(12, (P["pot"][0] - 14, P["pot"][1], 26)), (11, (22.4, F(44), 15))],
                            arrows=[((4, F(49), 22), (12, F(49), 22))])
    S["l_controls"] = dict(mode="line", show=["pot", "pot_board", "ctrl_board", "encoder", "led"], new=["encoder", "led", "ctrl_board"],
                           explode={"encoder": (0, 0, 14), "led": (0, 0, 14)},
                           cam=iso((34, F(49), 20), 70), res=(2000, 1500),
                           balloons=[(13, (P["encoder"][0], P["encoder"][1], 52)), (14, (P["led"][0], P["led"][1], 47)),
                                     (10, (48, F(54), zc)), (11, (22.4, F(44), 15))],
                           arrows=[((P["encoder"][0] - 9, P["encoder"][1], 40), (P["encoder"][0] - 9, P["encoder"][1], 26))])
    S["l_joint"] = dict(mode="line", show=["pot", "pot_board", "ctrl_board", "encoder", "led"], new=["pot_board"],
                        cam=((50, F(49) - 70, -40), (24, F(49), 15), None, 48), res=(1800, 1300),
                        balloons=[(11, (22.4, F(52), 16)), (10, (40, F(44), zc - 1.6))])
    S["l_cable_ctl"] = dict(mode="line", show=["pot", "pot_board", "ctrl_board", "encoder", "led", "ctl_cable", "board"],
                            new=["ctl_cable"], cam=iso((40, F(46), 18), 85), res=(2000, 1500),
                            balloons=[(21, (54, F(44.5), 20)), (10, (46, F(54), zc)), (11, (22.4, F(44), 15))])
    S["l_panel"] = dict(mode="line", show=["panel_board", "usb_c", "jack", "usb_cable", "pnl_cable"],
                        new=["jack", "usb_cable", "pnl_cable"], explode={"jack": (0, 0, 10)},
                        cam=iso((16, F(26), zp), 70, d=(1.0, -1.2, 1.1)), res=(2000, 1500),
                        balloons=[(18, (P["jack"][0], P["jack"][1], zp + 15)), (17, (P["usb_c"][0], P["usb_c"][1], zp + 3)),
                                  (19, (25, F(15), 18)), (20, (P["jpnl"][0], P["jpnl"][1], zt + 6)), (16, (20, F(32), zp))],
                        arrows=[((P["jack"][0] + 5, P["jack"][1], zp + 14), (P["jack"][0] + 5, P["jack"][1], zp + 6))])
    S["l_panel_under"] = dict(mode="line", show=["panel_board", "usb_c", "jack"], new=["usb_c"],
                              cam=((40, F(22) - 50, zp - 80), (16, F(24), zp), None, 50), res=(1800, 1300),
                              balloons=[("H1", (*P["h1"], zp - 1.6)), ("H2", (*P["h2"], zp - 1.6)),
                                        (17, (*P["usb_leg_rl"], zp - 1.6))])
    lid_up = ((-160, -200, -220), None, None, 150)
    S["l_lid_boards"] = dict(mode="line", show=["lid", "pot", "pot_board", "ctrl_board", "encoder", "led", "ctrl_screws",
                                                "panel_board", "usb_c", "jack", "panel_screw", "ctl_cable", "pnl_cable", "usb_cable"],
                             new=["pot", "pot_board", "ctrl_board", "encoder", "led", "ctrl_screws", "panel_board", "usb_c",
                                  "jack", "panel_screw"],
                             explode={g: (0, 0, -16) for g in ("pot", "pot_board", "ctrl_board", "encoder", "led", "panel_board",
                                                                "usb_c", "jack", "ctl_cable", "pnl_cable", "usb_cable")}
                             | {"ctrl_screws": (0, 0, -30), "panel_screw": (0, 0, -30)},
                             cam=((-120, -160, -200), (40, 55, 20), None, 125), res=(2000, 1600),
                             balloons=[(10, (45, F(54), zc - 16)), (34, (*P["ctrl_posts"][0], zc - 34)),
                                       (35, (*P["h2"], zp - 34)), (16, (12, F(30), zp - 17)), ("H1", (*P["h1"], zp - 17)),
                                       (2, (90, F(10), 30))],
                             arrows=[((P["ctrl_posts"][0][0] + 4, P["ctrl_posts"][0][1], zc - 30), (P["ctrl_posts"][0][0] + 4, P["ctrl_posts"][0][1], zc - 20)),
                                     ((P["h2"][0] + 4, P["h2"][1], zp - 30), (P["h2"][0] + 4, P["h2"][1], zp - 20))])
    S["l_speaker"] = dict(mode="line", show=["lid", "speaker", "gasket", "box_floor", "spk_wires"],
                          new=["speaker", "gasket", "box_floor", "spk_wires"],
                          explode={"gasket": (0, 0, -14), "speaker": (0, 0, -30), "spk_wires": (0, 0, -30), "box_floor": (0, 0, -55)},
                          cam=((-110, -190, -170), (40, 25, 0), None, 130), res=(2000, 1700),
                          balloons=[(25, (P["spk"][0] + 17.5, P["spk"][1], 10.5)), (24, (P["spk"][0] - 10, P["spk"][1], -8)),
                                    (26, (P["spk"][0] + 20, P["spk"][1], -44)), (2, (3, F(60), 20))],
                          arrows=[((P["spk"][0] - 22, P["spk"][1], -20), (P["spk"][0] - 22, P["spk"][1], -4))])
    S["l_board_mount"] = dict(mode="line", show=["bottom", "board", "jbat", "jspk", "plugs", "stack", "hp_wires", "plate",
                                                 "switches", "board_screws", "board_nuts"],
                              new=["board_screws", "board_nuts"],
                              explode={g: (0, 0, 14) for g in ("board", "jbat", "jspk", "plugs", "stack", "hp_wires", "plate",
                                                                "switches")} | {"board_screws": (0, 0, -22), "board_nuts": (0, 0, 32)},
                              cam=iso((100, 50, 5), 250, d=(-1.0, -1.6, 0.42)), res=(2400, 1500),
                              balloons=[(33, (*P["board_screws"][0], -24)), (33, (*P["board_screws"][1], -24)),
                                        (1, (150, 4, 2)), (3, (150, F(10), zt + 14))],
                              arrows=[((P["board_screws"][0][0] - 6, P["board_screws"][0][1], -20), (P["board_screws"][0][0] - 6, P["board_screws"][0][1], -4))])
    S["l_battery"] = dict(mode="line", show=["bottom", "battery", "pigtail", "hatch", "hatch_screws", "board", "plugs"],
                          new=["battery", "pigtail", "hatch", "hatch_screws"],
                          explode={"battery": (0, 0, -24), "hatch": (0, 0, -50), "hatch_screws": (0, 0, -66)},
                          cam=((-100, -170, -190), (45, 32, 0), None, 120), res=(2000, 1600),
                          balloons=[(27, (P["batt"][0] - 20, P["batt"][1], -22)), (28, (*P["pocket"], 3)),
                                    (29, (P["batt"][0] + 15, P["batt"][1], -50)), (36, (*P["hatch_screws"][0], -66)),
                                    (1, (120, F(20), 0))],
                          arrows=[((P["batt"][0] + 26, P["batt"][1], -30), (P["batt"][0] + 26, P["batt"][1], -8))])
    S["l_close"] = dict(mode="line", show=ALL[:-3] + ["case_screws", "hatch_screws"], new=["lid", "case_screws"],
                        explode={g: (0, 0, 40) for g in ("lid", "pot", "pot_board", "ctrl_board", "encoder", "led", "ctrl_screws",
                                                          "panel_board", "usb_c", "jack", "panel_screw", "speaker", "gasket",
                                                          "box_floor")} | {"case_screws": (0, 0, -26)},
                        cam=iso((125, 50, 20), 300), res=(2400, 1600),
                        balloons=[(2, (200, F(5), 75)), (32, (100, F(94), -26)), (1, (150, F(97), 2))],
                        arrows=[((160, F(50), 82), (160, F(50), 62)), ((95, F(94), -24), (95, F(94), -8))])
    S["l_caps"] = dict(mode="line", show=ALL, new=["caps", "knobs", "pot_nut"],
                       explode={"caps": (0, 0, 22), "knobs": (0, 0, 22), "pot_nut": (0, 0, 10)},
                       cam=iso((125, 50, 30), 290), res=(2400, 1500),
                       balloons=[(6, (220, F(40), 56)), (15, (P["encoder"][0], P["encoder"][1], 62)), (37, (P["pot"][0], P["pot"][1], 45))],
                       arrows=[((200, F(20), 58), (200, F(20), 42))])
    no_panel = [g for g in INSIDE if g not in ("panel_board", "usb_c", "jack", "pnl_cable", "usb_cable", "speaker", "gasket",
                                              "pot", "pot_board", "ctrl_board", "encoder", "led", "ctl_cable")]
    S["l_testpoints"] = dict(mode="line", show=no_panel + ["bottom"], new=["plugs"],
                             cam=((40, F(40), 300), (40, F(40), 0), None, 78), res=(2000, 1600),
                             balloons=[("A", (P["jbat"][0] - 0.5, P["jbat"][1] - 4.0, zt + 10.5)),
                                       ("B", (P["jbat"][0] - 0.5, P["jbat"][1], zt + 10.5)),
                                       ("C", (P["jbat"][0] - 0.5, P["jbat"][1] - 2.0, zt + 10.5)),
                                       ("E", (*P["teensy_3v"], Z["teensy_top"])), (23, (P["jspk"][0] + 1, P["jspk"][1], zt + 4))])
    S["l_tp_panel"] = dict(mode="line", show=["panel_board", "usb_c", "jack", "pnl_cable", "usb_cable", "pot", "pot_board",
                                              "ctrl_board", "encoder", "led", "ctl_cable"], new=[],
                           cam=((28, F(36), 300), (28, F(36), 0), None, 52), res=(1800, 1600),
                           balloons=[("D", (*P["tp1"], zp)), ("F", (*P["tp7"], zp)), ("G", (*P["jw4"], 26)),
                                     (16, (12, F(30), zp)), (11, (22.4, F(52), 29))])
    return S


def run(names, fast=False):
    os.makedirs(SHOTS_DIR, exist_ok=True)
    S = shots()
    for name in names:
        s = S[name]
        if s.get("solo"):
            sc = solo_scene(*s["solo"])
        else:
            sc = build_scene(s.get("led"))
            show_only(set(s.get("show", ALL)) - {"_hidden"})
            for o in bpy.data.objects:
                if any(o.name.startswith(t + "_") for t in s.get("hide_tags", [])):
                    o.hide_render = True
        explode(s.get("explode", {}))
        for tag, d in s.get("tag_explode", {}).items():
            for o in bpy.data.objects:
                if o.name.startswith(tag + "_"):
                    o.location = o.location + mathutils.Vector(M(*d))
        loc, tgt, lens, *ortho = s["cam"]
        camera(sc, loc, tgt, lens=lens, ortho=ortho[0] if ortho else None)
        res = s["res"]
        if fast:
            res = (res[0] // 3, res[1] // 3)
        if s["mode"] == "real":
            setup_render(sc, res, 32 if fast else s["samples"], transparent=True)
            studio(sc, tgt, 260, floor=s.get("floor", True))
            if s.get("section"):
                section(sc, *s["section"])
            sc.view_settings.exposure = s.get("exposure", 0.0)
        else:
            setup_render(sc, res, 1)
            sc.cycles.use_denoising = False
            sc.render.line_thickness = 1.0 if not fast else 0.5
            lineart(sc, s.get("new", []))
        sc.render.filepath = os.path.join(SHOTS_DIR, name + ".png")
        bpy.ops.render.render(write_still=True)
        bl = s.get("balloons", [])
        meta = {"res": list(res), "mode": s["mode"],
                "balloons": [[n, *xy] for (n, _), xy in zip(bl, project(sc, [p for _, p in bl]))],
                "arrows": [project(sc, list(a)) for a in s.get("arrows", [])],
                "dims": [[*project(sc, [a, b]), t] for a, b, t in s.get("dims", [])]}
        json.dump(meta, open(os.path.join(SHOTS_DIR, name + ".json"), "w"))
        print("SHOT", name)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fast = "--fast" in argv
    names = [a for a in argv if not a.startswith("--")] or list(shots().keys())
    run(names, fast)
