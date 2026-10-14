"""The manual's pictures, rendered in Blender (Cycles on the GPU):

    blender -b --python render_blender.py -- [shot ...] [--fast]

Builds the assembled eTuttino from the case STLs (../case/out), the two
KiCad boards (build/main.glb, build/controls.glb, exported by build.py)
and the parts library (build/lib, parts.py), then renders each shot of
SHOTS as either

  "real"  photo-like: PBR materials, studio light, perspective camera;
  "line"  a technical line drawing: flat white parts, black outlines
          (Freestyle), the parts added in that step filled in amber and
          drawn heavier, the rest grey; orthographic (axonometric) camera.

Exploded views move whole groups along an axis. For every shot it also
writes build/shots/<name>.json with the 2D pixel position of each
balloon anchor and arrow, so annotate.py can draw them; the pictures
themselves carry no text and serve all three languages.

Units: metres in Blender, millimetres everywhere in this file (M()).
Frame: the case files' (x right, y away from the player, z up).
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


def M(*v):
    return tuple(x / 1000.0 for x in v)


F = lambda y: W - y        # SPEC y -> file y

# ------------------------------------------------------------- materials
COLOURS = {
    "case_seixo": ("#d3cdc2", 0.55, 0.0), "pcb_teensy": ("#1d5e34", 0.35, 0.0), "pcb_audio": ("#1d5e34", 0.35, 0.0),
    "chip": ("#141414", 0.55, 0.0), "steel": ("#c9cacc", 0.28, 1.0), "alu": ("#d4d6d8", 0.33, 1.0),
    "brass": ("#bdb6a6", 0.3, 1.0), "tin": ("#dcdcdc", 0.22, 1.0), "plastic_black": ("#121212", 0.5, 0.0),
    "plastic_dark": ("#1c1d20", 0.5, 0.0), "stem": ("#ecebe6", 0.45, 0.0), "plastic_white": ("#f1eee5", 0.5, 0.0),
    "button": ("#f4f4f4", 0.4, 0.0), "cap0402": ("#8c7b5d", 0.5, 0.0), "cap0805": ("#8c7b5d", 0.5, 0.0),
    "knob": ("#d9d4cb", 0.5, 0.0), "natural": ("#f4f2ee", 0.32, 0.0), "sharp": ("#1d1d1f", 0.32, 0.0),
    "cf": ("#f4f2ee", 0.32, 0.0), "plate": ("#121314", 0.42, 0.0), "insert": ("#0e0e0f", 0.5, 0.0),
    "cable_black": ("#151515", 0.45, 0.0),
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


def build_materials():
    for name, (c, r, mt) in COLOURS.items():
        MATS[name] = principled(name, c, r, mt)
    MATS["pcb_teensy"].node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.4
    MATS["smoke"] = principled("smoke", "#2d3036", 0.15, 0.0, **{"Transmission Weight": 0.55, "IOR": 1.5})
    MATS["led_lens"] = principled("led_lens", "#dfffe6", 0.08, 0.0, **{"Transmission Weight": 0.9, "IOR": 1.5})
    led = MATS["led_lens"].node_tree.nodes["Principled BSDF"]
    led.inputs["Emission Color"].default_value = hex_rgb("#3cff6a")
    led.inputs["Emission Strength"].default_value = 3.0
    MATS["led_orange"] = principled("led_orange", "#ff9a2e", 0.3, 0.0, **{"Emission Strength": 0.0})
    for i, c in enumerate(WIRE_COLOURS):
        MATS["wire%d" % i] = principled("wire%d" % i, c, 0.45)
    # white oak: rings and rays from wave + noise
    m = bpy.data.materials.new("oak")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.08, 1.0, 1.0)   # object space is mm: grain along x
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 0.35
    wave.inputs["Distortion"].default_value = 5.0
    wave.inputs["Detail"].default_value = 4.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.25
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_rgb("#8a5c33")
    ramp.color_ramp.elements[1].color = hex_rgb("#c39362")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], mix.inputs["A"])
    nt.links.new(noise.outputs["Fac"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.35
    MATS["oak"] = m
    MATS["mother_of_pearl"] = principled("mother_of_pearl", "#efe9df", 0.25, 0.0, **{"Coat Weight": 0.5})
    MATS["ebony"] = principled("ebony", "#211b17", 0.3, 0.0, **{"Coat Weight": 0.5})
    MATS["knob_wood"] = principled("knob_wood", "#3a2a1e", 0.4)
    # line-drawing fills: flat (emission) so Freestyle's lines carry the shape
    for name, c in (("line_white", "#ffffff"), ("line_new", "#f6d58f"), ("line_grey", "#f2f2f2")):
        mm = bpy.data.materials.new(name)
        mm.use_nodes = True
        nt = mm.node_tree
        nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = hex_rgb(c)
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(e.outputs[0], o.inputs[0])
        MATS[name] = mm


# ------------------------------------------------------------- scene
GROUPS = {}            # group name -> parent empty
OBJ_GROUP = {}         # object -> group name


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


def import_glb(path, gname, z_bottom, keep_refs=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    holder = bpy.data.objects.new("H_" + gname, None)
    bpy.context.scene.collection.objects.link(holder)
    for r in roots:
        r.parent = holder
    # kicad-cli: x, -y_spec, z above the board's underside (metres) -> files' frame
    holder.location = (0, W / 1000.0, z_bottom / 1000.0)
    holder.parent = group(gname)
    for o in new:
        OBJ_GROUP[o.name] = gname
        if o.type == "MESH":
            for p in o.data.polygons:
                p.use_smooth = False
            for m in o.data.materials:
                # KiCad's soldermask and silkscreen come semi-transparent: make them solid
                if m and m.node_tree and "Principled BSDF" in m.node_tree.nodes:
                    b = m.node_tree.nodes["Principled BSDF"]
                    b.inputs["Alpha"].default_value = 1.0
                    r, g, bl, _ = b.inputs["Base Color"].default_value
                    if g > r * 1.5 and g > bl and g < 0.4:          # the soldermask
                        b.inputs["Base Color"].default_value = hex_rgb("#1b5a33")
                        b.inputs["Coat Weight"].default_value = 0.4
                    b.inputs["Roughness"].default_value = min(b.inputs["Roughness"].default_value, 0.45)
    return new


def children(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return []
    out = [o]
    for c in o.children_recursive:
        out.append(c)
    return out


CABLE_OBJS = {}


def cable(name, pts_mm, d, mat, gname):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = d / 2000.0
    cu.bevel_resolution = 4
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


def build_scene(version="seixo"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    GROUPS.clear()
    OBJ_GROUP.clear()
    MATS.clear()
    build_materials()
    sc = bpy.context.scene
    if version == "seixo":
        import_stl(os.path.join(CASE_OUT, "seixo_tampa.stl"), "case_seixo", "lid", name="lid")
        import_stl(os.path.join(CASE_OUT, "seixo_fundo.stl"), "case_seixo", "bottom", name="bottom")
    else:
        import_stl(os.path.join(CASE_OUT, "madeira_corpo.stl"), "oak", "lid", name="lid")
        import_stl(os.path.join(CASE_OUT, "madeira_fundo.stl"), "oak", "bottom", name="bottom")
    import_stl(os.path.join(CASE_OUT, "insert.stl"), "insert", "insert", name="insert")
    import_stl(os.path.join(CASE_OUT, "plate.stl"), "plate", "plate", name="plate")
    import_glb(os.path.join(BUILD, "main.glb"), "board", Z["pcb_bot"])
    import_glb(os.path.join(BUILD, "controls.glb"), "controls_board", Z["controls_top"] - Z["controls_t"])
    # J3 belongs to its own step
    for o in children("J3"):
        OBJ_GROUP[o.name] = "j3"
    # parts library, instanced
    cache = {}
    for i, inst in enumerate(A["instances"]):
        part = inst["part"]
        if version == "madeira" and part == "led_seixo":
            part = "led_madeira"
        for f in sorted(os.listdir(LIB)):
            p, mat, _ = f.split(".")
            if p != part:
                continue
            key = (part, mat)
            if version == "madeira" and mat == "knob":
                mat = "knob_wood"
            o = import_stl(os.path.join(LIB, f), mat, inst["group"], inst["loc"], inst["rot"],
                           name="%s_%d_%s" % (inst["tag"], i, mat)) if key not in cache else None
            if key in cache:
                o = cache[key].copy()
                o.data = cache[key].data
                sc.collection.objects.link(o)
                o.location = M(*inst["loc"])
                o.rotation_euler = [math.radians(a) for a in inst["rot"]]
                o.name = "%s_%d_%s" % (inst["tag"], i, mat)
                attach(o, inst["group"])
            else:
                cache[key] = o
    # caps
    look = {"seixo": ("natural", "sharp", "cf"), "madeira": ("mother_of_pearl", "ebony", "mother_of_pearl")}[version]
    caps = {}
    for kind, mat in zip(("natural", "sharp", "cf"), look):
        o = import_stl(os.path.join(CASE_OUT, "keycap_%s.stl" % kind), mat, "caps", name="cap_" + kind)
        caps[kind] = o
    keys = json.load(open(os.path.join(BUILD, "keys.json")))
    for kind, o in caps.items():
        top = max(v.co.z for v in o.data.vertices)   # mesh data is in mm (object scale 0.001)
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
    # cables
    c = A["cables"]
    ph = c["ph8"]
    for w in range(ph["wires"]):
        off = (w - 3.5) * ph["pitch"]
        pts = [ph["from"], *ph["mid"], ph["to"]]
        pts = [(x + off, y, z) for x, y, z in pts]
        cable("ph_w%d" % w, pts, ph["d"], "wire%d" % w, "cable")
    cable("usb_cable", c["usb"]["path"], c["usb"]["d"], "cable_black", "usb_cable")
    jw = c["jack_wires"]
    for w, mat in enumerate(("wire1", "wire7", "wire0")):
        off = (w - 1) * jw["pitch"]
        cable("jack_w%d" % w, [(x, y + off, z) for x, y, z in jw["path"]], jw["d"], mat, "panel")
    return sc


def solo_scene(stl, mat):
    """One STL on its own, centred on the origin (the keycap test print)."""
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


# ------------------------------------------------------------- render setup
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


def studio(sc, target, radius):
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
        d = t - lo.location
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    # a soft floor to catch the shadow
    bpy.ops.mesh.primitive_plane_add(size=50 * r, location=(t.x, t.y, -0.0002))
    fl = bpy.context.active_object
    fl.data.materials.append(principled("floor", "#f3f1ec", 0.9))
    fl.is_shadow_catcher = True


def camera(sc, loc, target, lens=None, ortho=None):
    cd = bpy.data.cameras.new("cam")
    co = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(co)
    co.location = M(*loc)
    d = mathutils.Vector(M(*target)) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.clip_start, cd.clip_end = 0.001, 10.0
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho / 1000.0
    else:
        cd.lens = lens or 70
    sc.camera = co
    return co


def lineart(sc, new_groups, hidden=()):
    """Flat fills + Freestyle outlines; new_groups heavy and amber."""
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
        if o.type not in ("MESH", "CURVE"):
            continue
        g = OBJ_GROUP.get(o.name)
        new = g in new_groups
        mat = MATS["line_new" if new else "line_white"]
        if o.type == "MESH":
            o.data = o.data.copy() if o.data.users > 1 and new else o.data
            o.data.materials.clear()
            o.data.materials.append(mat)
        else:
            o.data = o.data.copy()
            o.data.materials.clear()
            o.data.materials.append(mat)
        if new:
            hl.objects.link(o)
    vl = sc.view_layers[0]
    fs = vl.freestyle_settings
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


def hide(groups):
    for o in bpy.data.objects:
        if OBJ_GROUP.get(o.name) in groups:
            o.hide_render = True


def explode(offsets):
    for g, (dx, dy, dz) in offsets.items():
        if g in GROUPS:
            GROUPS[g].location = M(dx, dy, dz)
    # J3 sits inside the board's tree: move its root on its own
    if "j3" in offsets:
        r = bpy.data.objects.get("J3")
        if r:
            r.location = r.location + mathutils.Vector(M(*offsets["j3"]))


def section(sc, x):
    """Cuts every mesh at x (keeps x > cut), with a boolean box."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x / 1000.0 - 0.5, 0.05, 0.05))
    cutter = bpy.context.active_object
    cutter.scale = (1.0, 1.0, 1.0)
    cutter.hide_render = True
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o is cutter or o.name == "Plane":
            continue
        wb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        if min(v.x for v in wb) > x / 1000.0 or not o.visible_get():
            continue
        if max(v.x for v in wb) < x / 1000.0:
            o.hide_render = True
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        mod = o.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        mod.solver = "EXACT"


def project(sc, pts):
    cam = sc.camera
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    out = []
    for p in pts:
        v = world_to_camera_view(sc, cam, mathutils.Vector(M(*p)))
        out.append([round(v.x * rx, 1), round((1 - v.y) * ry, 1)])
    return out


# ------------------------------------------------------------- the shots
# Balloon numbers = the parts list in the manual (PARTS in annotate.py).
ST = {"x0": 20.0, "x1": 58.0, "y0": F(41.8), "y1": F(5.0)}
TEENSY_C = (40.11, F(21.38))
CTRL = A["instances"]


def inst_loc(tag):
    for i in A["instances"]:
        if i["tag"] == tag:
            return i["loc"]


def shots():
    zt = Z["pcb_top"]
    zc = Z["controls_top"]
    pot = inst_loc("pot")
    enc = inst_loc("encoder")
    led = inst_loc("led")
    plug1 = inst_loc("ph_plug_j1")
    pusb = inst_loc("panel_usb")
    pjack = inst_loc("panel_jack")
    m2 = inst_loc("m2x10")
    m25 = inst_loc("m25x8")
    m2x5 = inst_loc("m2x5")
    S = {}
    # ---------------- photo-like
    S["r_finished"] = dict(mode="real", version="seixo", res=(2400, 1500), samples=192,
                           cam=((-150, -300, 270), (168, 50, 8), 62), exposure=-0.4, hidden=[], explode={},
                           balloons=[])
    S["r_finished_madeira"] = dict(S["r_finished"], version="madeira")
    S["r_exploded"] = dict(mode="real", version="seixo", res=(2400, 2000), samples=160,
                           cam=((-200, -400, 380), (160, 50, 85), 50), exposure=-0.3, hidden=[],
                           explode={"case_screws": (0, 0, -45), "board_screws": (0, 0, -30), "bottom": (0, 0, -15),
                                    "board_nuts": (0, 0, 25), "stack": (0, 0, 22), "usb_cable": (0, 0, 22),
                                    "panel": (-25, 0, 10), "insert": (-25, 0, 10), "cable": (0, 0, 40),
                                    "plate": (0, 0, 40), "switches": (0, 0, 58), "caps": (0, 0, 92),
                                    "controls_board": (0, 0, 70), "controls": (0, 0, 70), "controls_screws": (0, 0, 55),
                                    "lid": (0, 0, 150), "knobs": (0, 0, 185)},
                           balloons=[(1, (200, 2, -14)), (2, (300, 6, 167.4)), (3, (300, 30, 7.7)),
                                     (4, (318, 50, 52.8)), (5, (290, 25, 77)), (6, (270, 30, 117)),
                                     (7, (40, 78, 38)), (10, (25, 50, 94)), (14, (20, 55, 219)),
                                     (17, (-21, 55, 22))])
    S["r_stack"] = dict(mode="real", version="seixo", res=(2000, 1400), samples=192,
                        cam=((-35, -10, 70), (40, 78, 12), 70), hidden=["lid", "plate", "switches", "caps", "controls", "insert", "panel", "usb_cable",
                                                                       "controls_board", "knobs", "cable", "controls_screws",
                                                                       "case_screws"],
                        explode={}, balloons=[])
    S["r_controls"] = dict(mode="real", version="seixo", res=(2000, 1400), samples=192,
                           cam=((-25, -55, 60), (36, 52, 20), 60),
                           hidden=["lid", "knobs", "plate", "switches", "caps", "case_screws"], explode={}, balloons=[])
    S["r_keycap_test"] = dict(mode="real", solo=("keycap_test_4.stl", "natural"), res=(1600, 1100), samples=160,
                              cam=((-30, -95, 85), (0, 0, 2), 60), exposure=-1.0, balloons=[])
    S["r_section"] = dict(mode="real", version="seixo", res=(2400, 1100), samples=192,
                          cam=((-300, 50, 18), (30, 50, 18), None, 120), hidden=["case_screws"], explode={},
                          section=30.0, balloons=[])
    # ---------------- line drawings, one per assembly step
    base = ["lid", "caps", "knobs", "case_screws", "controls_screws", "board_screws", "board_nuts", "bottom"]
    iso = lambda tgt, scale, d=(-1.0, -1.25, 1.05): ((tgt[0] + d[0] * 400, tgt[1] + d[1] * 400, tgt[2] + d[2] * 400),
                                                      tgt, None, scale)
    S["l_keycaps"] = dict(mode="line", new=["caps"], keep_box=(132, 186, F(66), F(34)),
                          hidden=["lid", "knobs", "case_screws", "controls_screws", "board_screws", "board_nuts", "bottom",
                                  "board", "j3", "stack", "controls", "controls_board", "cable", "panel", "insert",
                                  "usb_cable"],
                          explode={"caps": (0, 0, 16)}, cam=iso((159, 50, 24), 100), res=(1800, 1400),
                          balloons=[(6, (150, F(58), 47)), (5, (176, F(50), 18))],
                          arrows=[((140, F(42), 44), (140, F(42), 32))])
    S["l_j3"] = dict(mode="line", new=["j3"], hidden=base + ["stack", "plate", "switches", "controls", "controls_board",
                                                             "cable", "panel", "insert", "usb_cable"],
                     explode={"j3": (0, 0, 14)}, cam=iso((40, 52, 10), 85), res=(2000, 1400),
                     balloons=[(16, (33, F(49), zt + 20)), (3, (62, 42, zt))],
                     arrows=[((33, F(49), zt + 12), (33, F(49), zt + 7))])
    S["l_stack"] = dict(mode="line", new=["stack"], hidden=base + ["plate", "switches", "controls", "controls_board",
                                                                   "cable", "panel", "insert", "usb_cable"],
                        explode={"stack": (0, 0, 0)}, cam=iso((40, 75, 14), 95), res=(2000, 1500),
                        parts_explode={"teensy": (0, 0, 26), "header": (0, 0, 14), "audio_board": (0, 0, 7)},
                        balloons=[(7, (40, F(21.4), 45)), (9, (24, F(29), 33)), (8, (55, 63, 23)), (3, (60, 45, zt))],
                        arrows=[((62, F(21.4), 38), (62, F(21.4), 22)), ((62, F(37), 24), (62, F(37), 12))])
    S["l_switches"] = dict(mode="line", new=["plate", "switches"],
                           hidden=base + ["controls", "controls_board", "cable", "panel", "insert", "usb_cable"],
                           explode={"plate": (0, 0, 22), "switches": (0, 0, 44)}, cam=iso((170, 50, 25), 300),
                           res=(2400, 1500),
                           balloons=[(5, (300, 58, 75)), (4, (318, 50, 35)), (3, (300, 20, zt))],
                           arrows=[((270, 20, 70), (270, 20, 52)), ((285, 15, 42), (285, 15, 30))])
    S["l_controls"] = dict(mode="line", new=["controls", "cable"],
                           hidden=base + ["plate", "switches", "panel", "insert", "usb_cable"],
                           explode={"controls": (0, 0, 22), "cable": (0, 0, -6)},
                           cam=iso((36, 55, 22), 110), res=(2000, 1500),
                           balloons=[(11, (pot[0], pot[1], zc + 40)), (12, (enc[0], enc[1], zc + 40)),
                                     (13, (led[0], led[1], zc + 32)), (10, (55, 40, zc)), (15, (plug1[0], plug1[1], zc - 22))],
                           arrows=[((pot[0] - 8, pot[1], zc + 30), (pot[0] - 8, pot[1], zc + 12)),
                                   ((led[0] + 6, led[1], zc + 24), (led[0] + 6, led[1], zc + 8))])
    S["l_panel"] = dict(mode="line", new=["panel", "insert", "usb_cable"],
                        hidden=base + ["plate", "switches", "controls", "controls_board", "cable"],
                        explode={"insert": (-22, 0, 0), "panel": (-12, 0, 0)},
                        cam=iso((25, 50, 16), 95, d=(-1.2, -1.0, 0.8)), res=(2000, 1500),
                        balloons=[(17, (-22, 55, 30)), (18, (pusb[0] - 12, pusb[1], pusb[2] + 8)),
                                  (19, (pjack[0] - 12, pjack[1], pjack[2] + 8)), (20, (14, F(23), 28))],
                        arrows=[((-34, 30, 16), (-24, 30, 16))])
    S["l_bottom"] = dict(mode="line", new=["board_screws", "board_nuts", "board", "j3", "stack"],
                         hidden=["lid", "caps", "knobs", "case_screws", "controls", "controls_board", "cable",
                                 "controls_screws"],
                         explode={"board_screws": (0, 0, -24), "board_nuts": (0, 0, 30), "board": (0, 0, 14),
                                  "j3": (0, 0, 0), "stack": (0, 0, 14), "panel": (0, 0, 14), "insert": (0, 0, 14),
                                  "usb_cable": (0, 0, 14), "plate": (0, 0, 14), "switches": (0, 0, 14)},
                         cam=iso((40, 50, 5), 120, d=(-1.0, -1.3, 0.9)), res=(2000, 1500),
                         balloons=[(21, (m2[0], m2[1], -24)), (22, (m2[0] + 2, m2[1], zt + 30)), (1, (60, 4, 2)),
                                   (3, (75, 20, zt + 14))],
                         arrows=[((m2[0] - 6, m2[1], -22), (m2[0] - 6, m2[1], -6)),
                                 ((m2[0] - 6, m2[1], zt + 40), (m2[0] - 6, m2[1], zt + 33))])
    S["l_lid_controls"] = dict(mode="line", new=["controls", "controls_board", "controls_screws"],
                               hidden=["caps", "knobs", "case_screws", "board", "j3", "stack", "plate", "switches",
                                       "bottom", "board_screws", "board_nuts", "panel", "insert", "usb_cable", "cable"],
                               explode={"controls": (0, 0, -18), "controls_board": (0, 0, -18),
                                        "controls_screws": (0, 0, -32)},
                               cam=((-200, -260, -230), (40, 50, 18), None, 120), res=(2000, 1500),
                               balloons=[(10, (20, 40, zc - 30)), (23, (m2x5[0], m2x5[1], zc - 42)), (2, (60, 10, 30))],
                               arrows=[((m2x5[0] + 5, m2x5[1], zc - 40), (m2x5[0] + 5, m2x5[1], zc - 24))])
    S["l_close"] = dict(mode="line", new=["lid", "case_screws"], hidden=["caps", "knobs"],
                        explode={"lid": (0, 0, 40), "controls": (0, 0, 40), "controls_board": (0, 0, 40),
                                 "controls_screws": (0, 0, 40), "case_screws": (0, 0, -28), "cable": (0, 0, 20)},
                        cam=iso((165, 50, 20), 360), res=(2400, 1600),
                        balloons=[(2, (250, 6, 60)), (24, (m25[0], m25[1], -36)), (1, (165, 4, 2))],
                        arrows=[((200, 50, 75), (200, 50, 58)), ((m25[0] - 8, m25[1], -32), (m25[0] - 8, m25[1], -14))])
    S["l_caps"] = dict(mode="line", new=["caps", "knobs"], hidden=[],
                       explode={"caps": (0, 0, 24), "knobs": (0, 0, 22)}, cam=iso((170, 50, 30), 340),
                       res=(2400, 1500),
                       balloons=[(6, (290, 40, 58)), (14, (20, 55, 64))],
                       arrows=[((250, 20, 56), (250, 20, 40)), ((10, 55, 62), (10, 55, 46))])
    return S


def run(names, fast=False):
    os.makedirs(SHOTS_DIR, exist_ok=True)
    keys = []
    S = shots()
    for name in names:
        s = S[name]
        if s.get("solo"):
            sc = solo_scene(*s["solo"])
        else:
            sc = build_scene(s.get("version", "seixo"))
        hide(s.get("hidden", []))
        if s.get("keep_box"):
            x0, x1, y0, y1 = [v / 1000.0 for v in s["keep_box"]]
            for o in bpy.data.objects:
                if o.type == "MESH" and OBJ_GROUP.get(o.name) in ("switches", "caps", "plate"):
                    if OBJ_GROUP[o.name] == "plate":
                        o.hide_render = True
                        continue
                    if not (x0 <= o.location.x <= x1 and y0 <= o.location.y <= y1):
                        o.hide_render = True
        explode(s.get("explode", {}))
        for tag, d in s.get("parts_explode", {}).items():
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
            studio(sc, tgt, 260)
            if s.get("section") is not None:
                section(sc, s["section"])
        else:
            setup_render(sc, res, 1)
            sc.cycles.use_denoising = False
            sc.render.line_thickness = 1.0 if not fast else 0.5
            lineart(sc, s.get("new", []))
        if s["mode"] == "real":
            sc.view_settings.exposure = s.get("exposure", 0.0)
        sc.render.filepath = os.path.join(SHOTS_DIR, name + ".png")
        bpy.ops.render.render(write_still=True)
        meta = {"res": list(res), "balloons": [[n, *xy] for (n, _), xy in
                                               zip(s.get("balloons", []), project(sc, [p for _, p in s.get("balloons", [])]))],
                "arrows": [project(sc, list(a)) for a in s.get("arrows", [])], "mode": s["mode"]}
        json.dump(meta, open(os.path.join(SHOTS_DIR, name + ".json"), "w"))
        print("SHOT", name)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fast = "--fast" in argv
    names = [a for a in argv if not a.startswith("--")] or list(shots().keys())
    run(names, fast)
