"""eTutti Student V3: photo-real pictures in Blender (Cycles, GPU).

    "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe" -b --python etutti/hardware/student_v03/case/render_blender.py -- [shot ...] [--fast]

Reads case/blender/build/manifest.json and the PLY meshes written by blender_export.py. Every shot lists the groups shown,
how far each group is pulled apart (exploded views), the camera and the picture size. Writes case/blender/out/<shot>.png with the
background transparent (a soft floor shadow on the beauty shots); blender_finish.py (CadQuery venv, Pillow) lays them on the page's
paper colour and writes the JPEGs the page serves.

Units: metres in Blender, millimetres in the manifest. The scene's frame is used as it is (x right, y = -SPEC y, z up).
Materials: printed nylon / resin for the case, matt black FR-4 for the grid, gloss for the buttons, metal for the screws and
connectors, smoked acrylic for the window. The board is KiCad's own GLB (mask, copper pads, silkscreen) with the boxes of the scene
standing for the parts.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "blender", "build")
OUT = os.path.join(HERE, "blender", "out")
MAN = json.load(open(os.path.join(BUILD, "manifest.json")))
BOX_GROUPS = {"teclas", "pecas", "encoders", "tela", "modulo", "bateria", "caixa"}


def M(*v):
    return tuple(x / 1000.0 for x in v)


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def principled(name, colour, rough=0.5, metal=0.0, **extra):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(colour)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in extra.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


# (group, colour) -> (colour, roughness, metallic, extras); anything not listed uses its own colour, roughness 0.5
LOOK = {
    ("tampa", "E8DEC6"): ("#E8DEC6", 0.46, 0.0, {"Specular IOR Level": 0.35}),
    ("tampa", "C8402A"): ("#C8402A", 0.28, 0.0, {"Coat Weight": 0.5, "Coat Roughness": 0.1}),
    ("tampa", "E07A2C"): ("#E07A2C", 0.28, 0.0, {"Coat Weight": 0.5, "Coat Roughness": 0.1}),
    ("tampa", "E3B23C"): ("#E3B23C", 0.28, 0.0, {"Coat Weight": 0.5, "Coat Roughness": 0.1}),
    ("tampa", "8A3A22"): ("#8A3A22", 0.3, 0.0, {}),
    ("tampa", "2B2925"): ("#2B2925", 0.3, 0.0, {"Coat Weight": 0.3}),
    ("base", "9C9B96"): ("#A3A29D", 0.62, 0.0, {}),
    ("base", "rgb"): ("#1E1E1E", 0.8, 0.0, {}),                # the silicone / PU feet
    ("grade", "1C1B1A"): ("#1C1B1A", 0.5, 0.0, {"Specular IOR Level": 0.4}),
    ("espacadores", "B8AE9A"): ("#CFC6B2", 0.5, 0.0, {}),
    ("parafusos", "8C8C8C"): ("#B9BBBD", 0.3, 1.0, {}),
    ("parafusos_base", "8C8C8C"): ("#B9BBBD", 0.3, 1.0, {}),
    ("parafusos_base", "6E6C68"): ("#9A9C9E", 0.32, 1.0, {}),
    ("porcas", "6E6C68"): ("#9A9C9E", 0.32, 1.0, {}),
    ("botoes", "F1ECE1"): ("#F1ECE1", 0.27, 0.0, {"Coat Weight": 0.25, "Coat Roughness": 0.15}),
    ("botoes", "1E1C1B"): ("#1E1C1B", 0.27, 0.0, {"Coat Weight": 0.25, "Coat Roughness": 0.15}),
    ("knobs", "1E1C1B"): ("#1E1C1B", 0.3, 0.0, {"Coat Weight": 0.2}),
    ("teclas", "6F6A62"): ("#7B7569", 0.3, 0.0, {}),
    ("encoders", "8C8C8C"): ("#A8A9AB", 0.35, 0.8, {}),
    ("encoders", "B3B2AE"): ("#C9CACC", 0.25, 1.0, {}),
    ("pecas", "B3B2AE"): ("#C4C5C7", 0.28, 1.0, {}),
    ("pecas", "2B2925"): ("#262626", 0.45, 0.0, {}),
    ("pecas", "0E0D0C"): ("#0E0D0C", 0.5, 0.0, {}),
    ("caixa", "7A746A"): ("#8A8478", 0.55, 0.0, {}),
    ("falante", "22201E"): ("#1B1A19", 0.5, 0.0, {}),
    ("falante", "2A2826"): ("#2A2826", 0.7, 0.0, {}),
    ("janela", "141312"): ("#0E0D0C", 0.04, 0.0, {"Specular IOR Level": 0.8, "Coat Weight": 0.6, "Coat Roughness": 0.02}),
    ("tela", "0B0B0A"): ("#0A0A0A", 0.05, 0.0, {"Specular IOR Level": 0.8}),
    ("tela", "1B4F8A"): ("#1B4F8A", 0.4, 0.0, {}),
    ("bateria", "5E7FA3"): ("#6B8DB3", 0.4, 0.0, {"Coat Weight": 0.2}),
    ("modulo", "1F3B63"): ("#1F3B63", 0.38, 0.0, {"Coat Weight": 0.2}),
    ("modulo", "2B2925"): ("#222222", 0.5, 0.0, {}),
    ("m25_espacador", "E8E2D0"): ("#EAE4D2", 0.55, 0.0, {}),
    ("m25_parafuso", "E8E2D0"): ("#EAE4D2", 0.55, 0.0, {}),
    ("m25_porca", "E8E2D0"): ("#EAE4D2", 0.55, 0.0, {}),
    ("cabo", "D9D5CC"): ("#D9D5CC", 0.5, 0.0, {}),
}
MATS = {}


def material(group, col):
    key = (group, col)
    if key not in MATS:
        c, r, mt, ex = LOOK.get(key, ("#" + col if col != "rgb" else "#333333", 0.5, 0.0, {}))
        MATS[key] = principled("%s_%s" % key, c, r, mt, **ex)
    return MATS[key]


# ------------------------------------------------------------------ scene
GROUPS = {}
GROUP_OBJS = {}


def group_empty(name):
    if name not in GROUPS:
        e = bpy.data.objects.new("G_" + name, None)
        bpy.context.scene.collection.objects.link(e)
        GROUPS[name] = e
        GROUP_OBJS[name] = []
    return GROUPS[name]


def weld_and_smooth(o, angle=35.0, bevel=False, flat=False):
    old = o.data
    me = bpy.data.meshes.new(old.name + "_clean")      # rebuilt without the PLY's custom normals (they smear the shading of flat plates)
    me.from_pydata([v.co[:] for v in old.vertices], [], [tuple(p.vertices) for p in old.polygons])
    me.update()
    mats = list(old.materials)
    o.data = me
    bpy.data.meshes.remove(old)
    for m in mats:
        me.materials.append(m)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    o.select_set(True)
    if bevel:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = 0.00025
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
    if flat:
        for p in me.polygons:
            p.use_smooth = False
    else:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for f in MAN["files"]:
        g, col = f["group"], f["colour"]
        if g == "placa":
            continue                      # the board comes from KiCad's GLB
        bpy.ops.wm.ply_import(filepath=os.path.join(BUILD, f["file"]), global_scale=0.001)
        o = bpy.context.selected_objects[0]
        o.name = "%s__%s" % (g, col.lstrip("#"))
        o.data.materials.clear()
        o.data.materials.append(material(g, col))
        weld_and_smooth(o, angle=35.0, bevel=g in BOX_GROUPS and col != "rgb", flat=g in ("grade", "base"))
        o.parent = group_empty(g)
        GROUP_OBJS[g].append(o)
    # the board: KiCad's GLB (frame: glTF y-up -> Blender z-up), aligned by its bounding box to the scene's board
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(BUILD, "placa.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    lo = mathutils.Vector((1e9, 1e9, 1e9))
    hi = mathutils.Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
    holder = bpy.data.objects.new("H_placa", None)
    bpy.context.scene.collection.objects.link(holder)
    for o in new:
        if o.parent is None:
            o.parent = holder
    zb = MAN["board_underside"] / 1000.0
    holder.location = (0.0025 - lo.x, -0.0975 - lo.y, zb - lo.z)
    bpy.context.view_layer.update()
    holder.parent = group_empty("placa")
    for o in meshes:
        print('GLBMESH', o.name, [(m.name, [round(v, 2) for v in m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value]) for m in o.data.materials if m and m.node_tree])
        GROUP_OBJS["placa"].append(o)
        for p in o.data.polygons:
            p.use_smooth = False
        for m in o.data.materials:
            if m and m.node_tree and "Principled BSDF" in m.node_tree.nodes:
                b = m.node_tree.nodes["Principled BSDF"]
                b.inputs["Alpha"].default_value = 1.0
                r, g, bl, _ = b.inputs["Base Color"].default_value
                if abs(r - 0.5) < 0.01 and abs(g - 0.5) < 0.01:           # HASL-tinned pads
                    b.inputs["Base Color"].default_value = lin("#B9B9B6")
                    b.inputs["Metallic"].default_value = 1.0
                    b.inputs["Roughness"].default_value = 0.3
                elif r > 0.9 and g > 0.9:                                  # silkscreen
                    b.inputs["Base Color"].default_value = lin("#E6E4DA")
                    b.inputs["Roughness"].default_value = 0.6
                elif g > r * 1.3 and g > bl:                               # the soldermask
                    b.inputs["Base Color"].default_value = lin("#1B5A33")
                    b.inputs["Coat Weight"].default_value = 0.0
                    b.inputs["Roughness"].default_value = 0.6
    return lo, hi


def setup_render(sc, res, samples):
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.2
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"


def look_at(cam, pos, target, up):
    p = mathutils.Vector(pos)
    f = (mathutils.Vector(target) - p).normalized()
    r = f.cross(mathutils.Vector(up)).normalized()
    u = r.cross(f)
    m = mathutils.Matrix(((r.x, u.x, -f.x, p.x), (r.y, u.y, -f.y, p.y), (r.z, u.z, -f.z, p.z), (0, 0, 0, 1)))
    cam.matrix_world = m


def lights_and_world(sc, target, dist, under, floor, zmin):
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = lin("#F3F1EC")
    bg.inputs["Strength"].default_value = 0.22
    sc.world = world
    t = mathutils.Vector(target)
    r = dist
    rig = [("key", (-1.0, -1.6, 1.8), 1500, 1.0), ("fill", (1.6, -0.8, 0.9), 450, 1.8),
           ("rim", (0.4, 1.6, 1.2), 900, 0.8), ("top", (0, 0, 2.5), 250, 2.4)]
    if under:
        rig += [("under1", (-1.0, -1.4, -1.6), 1300, 1.4), ("under2", (1.4, -0.6, -1.2), 700, 1.8)]
    for name, (dx, dy, dz), power, size in rig:
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = power * r * r * 0.04
        ld.size = size * r
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = t + mathutils.Vector((dx, dy, dz)) * r
        d = t - lo.location
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=3.0, location=(t.x, t.y, zmin - 0.00003))
        fl = bpy.context.active_object
        fl.name = "floor"
        fl.data.materials.append(principled("floor", "#F3F1EC", 0.9))
        fl.is_shadow_catcher = True


def render_shot(name, s, fast):
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name == "floor":
            bpy.data.objects.remove(o, do_unlink=True)
    shown = set(s["shown"])
    for g, e in GROUPS.items():
        vis = g in shown
        e.location = M(*s["offsets"].get(g, (0, 0, 0)))
        for o in GROUP_OBJS[g]:
            o.hide_render = not vis
            o.hide_viewport = not vis
    # the board's holder has the group empty as parent: its meshes follow
    pos, target, up = s["cam"]
    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.sensor_fit = "VERTICAL"
    cd.angle = 2 * math.atan(math.tan(math.radians(15)) / s["zoom"])
    cd.clip_start, cd.clip_end = 0.01, 5.0
    look_at(cam, M(*pos), M(*target), up)
    dist = (mathutils.Vector(M(*pos)) - mathutils.Vector(M(*target))).length
    zmin = -0.0101 + 0.0
    lights_and_world(sc, M(*target), max(dist * 0.55, 0.25), s["under"], s["floor"], -0.0102)
    scale = 0.5 if fast else 1.0
    setup_render(sc, (int(s["size"][0] * scale), int(s["size"][1] * scale)), 24 if fast else 160)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("rendered", name)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fast = "--fast" in argv
    names = [a for a in argv if not a.startswith("--")]
    os.makedirs(OUT, exist_ok=True)
    build_scene()
    for n, s in MAN["shots"].items():
        if names and n not in names:
            continue
        render_shot(n, s, fast)


main()
