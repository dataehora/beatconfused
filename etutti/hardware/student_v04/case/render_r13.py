"""eTutti Student V4 (R13V4): photo-real renders (Blender 5.2, Cycles/OptiX) of the 32-key instrument and its 11 assembly steps.

  1. kicad-cli pcb export glb -f --user-origin 0x0mm --include-pads --include-silkscreen --subst-models -o case/blender/build/principal_full.glb kicad/student_v04_roteada_3d.kicad_pcb
     (same for kicad/regua/student_v04_regua8_roteada_3d.kicad_pcb -> r8_full.glb)
  2. CadQuery venv:  python etutti/hardware/student_v04/case/cena_r13.py
  3. "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe" -b --python etutti/hardware/student_v04/case/render_r13.py -- [shot ...] [--fast]
  4. CadQuery venv:  python etutti/hardware/student_v04/case/finish_r13.py        (paper background, numbered balloons, writes etutti/studentV4/img/)

Frame: the KiCad GLBs come out in the file frame already (x right, y = -SPEC y, z up); the main board is shifted -1.12 in z (top = 0), a ruler goes to
(x0 - 10, -y + 17, ZR - 1.12). Groups are the names written by cena_r13.py. Each shot lists the groups shown, how far each is pulled (mm, file frame),
the camera, the size, and numbered anchors (group, SPEC point) that the renderer projects into out/<shot>.json for the balloons.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import bpy_extras
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "blender", "build")
OUT = os.path.join(HERE, "blender", "out")
MAN = json.load(open(os.path.join(BUILD, "manifest_parts.json")))
ZR = [0.0, 2.0, 4.0, 7.0]
ROWS = {r["row"]: r for r in MAN["rulers"]}
CX, CY = 122.0, -49.0


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


GLOSS = {"Coat Weight": 0.3, "Coat Roughness": 0.12}


def look(group, col):
    """(hex, roughness, metallic, extras) for a mesh file of this group and colour."""
    c = "#" + col
    g = group
    if g == "tampa":
        return (c, 0.46, 0.0, {"Specular IOR Level": 0.35})
    if g == "base":
        return ("#A3A29D", 0.62, 0.0, {})
    if g.startswith("gra_"):
        return (c, 0.5, 0.0, {"Specular IOR Level": 0.4})
    if g.startswith("capa_"):
        return (c, 0.27, 0.0, {"Coat Weight": 0.25, "Coat Roughness": 0.15})
    if g.startswith("tec_"):
        return (c, 0.32, 0.0, {})
    if g.startswith(("par_", "por_")) or g == "parafusos_base":
        return ("#B9BBBD", 0.3, 1.0, {})
    if g.startswith(("cab_", "pta_", "qwiic", "fios")):
        return (c, 0.5, 0.0, {})
    if g == "pes":
        return ("#1E1E1E", 0.85, 0.0, {})
    if g == "janela":
        return ("#0E0D0C", 0.04, 0.0, {"Specular IOR Level": 0.25, "Coat Weight": 0.12, "Coat Roughness": 0.05, "Alpha": 0.25})
    if g == "knobs":
        return (c, 0.3, 0.0, {"Coat Weight": 0.2})
    if g == "oled":
        return (c, 0.1 if col in ("0B0B0A", "101010") else 0.45, 0.0, {})
    if g == "bateria":
        return (c, 0.4, 0.0, {"Coat Weight": 0.2})
    if g == "caixa":
        return ("#8A8478", 0.55, 0.0, {})
    if g.startswith("m25"):
        return ("#EAE4D2", 0.55, 0.0, {})
    if g in ("encoders", "modulo"):
        r, gg, b = [int(col[i:i + 2], 16) for i in (0, 2, 4)]
        metal = 1.0 if abs(r - gg) < 12 and abs(gg - b) < 12 and r > 110 else 0.0
        return (c, 0.3 if metal else 0.5, metal, {})
    return (c, 0.5, 0.0, {})


MATS = {}


def material(group, col):
    k = (group, col)
    if k not in MATS:
        c, r, m, ex = look(group, col)
        MATS[k] = principled("%s_%s" % k, c, r, m, **ex)
    return MATS[k]


GROUPS, GROUP_OBJS = {}, {}


def group_empty(name):
    if name not in GROUPS:
        e = bpy.data.objects.new("G_" + name, None)
        bpy.context.scene.collection.objects.link(e)
        GROUPS[name] = e
        GROUP_OBJS[name] = []
    return GROUPS[name]


def clean(o, flat=False, angle=35.0):
    old = o.data
    me = bpy.data.meshes.new(old.name + "_c")
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
    if flat:
        for p in me.polygons:
            p.use_smooth = False
    else:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def import_glb(path, group, loc, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new("H_" + tag, None)
    bpy.context.scene.collection.objects.link(holder)
    for o in new:
        if o.parent is None:
            o.parent = holder
    holder.location = M(*loc)
    holder.parent = group_empty(group)
    for o in new:
        if o.type == "MESH":
            GROUP_OBJS[group].append(o)
            for m in o.data.materials:
                if m and m.node_tree and "Principled BSDF" in m.node_tree.nodes:
                    b = m.node_tree.nodes["Principled BSDF"]
                    b.inputs["Alpha"].default_value = 1.0
        elif o.type == "EMPTY":
            GROUP_OBJS[group].append(o)
    return new


def tune_board_materials(objs):
    """KiCad's board materials: mask green, HASL pads, silkscreen; the component models keep the colours of their STEP files."""
    seen = set()
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if not m or m.name in seen or not m.node_tree or "Principled BSDF" not in m.node_tree.nodes:
                continue
            seen.add(m.name)
            b = m.node_tree.nodes["Principled BSDF"]
            r, g, bl, _ = b.inputs["Base Color"].default_value
            n = m.name.lower()
            if "mask" in n or "soldermask" in n or "board" in n:
                b.inputs["Base Color"].default_value = lin("#1B5A33")
                b.inputs["Roughness"].default_value = 0.55
            elif "silk" in n:
                b.inputs["Base Color"].default_value = lin("#E6E4DA")
                b.inputs["Roughness"].default_value = 0.6
            elif "copper" in n or "pad" in n or "tin" in n:
                b.inputs["Base Color"].default_value = lin("#C9B98A")
                b.inputs["Metallic"].default_value = 1.0
                b.inputs["Roughness"].default_value = 0.3
    print("GLB MATERIALS", sorted(seen))


def ruler_loc(x0, y_spec, z):
    return (x0 - 10.0, -y_spec + 17.0, z - 1.12)


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for f in MAN["files"]:
        g, col = f["group"], f["colour"]
        bpy.ops.wm.ply_import(filepath=os.path.join(BUILD, f["file"]), global_scale=0.001)
        o = bpy.context.selected_objects[0]
        o.name = "%s__%s" % (g, col)
        o.data.materials.clear()
        o.data.materials.append(material(g, col))
        clean(o, flat=g in ("base", "tampa") and False)
        o.parent = group_empty(g)
        GROUP_OBJS[g].append(o)
    # R15V4: the OLED shows the firmware's status screen (telas_oled.py -> studentV4/img/tela_status_pt.png), emissive, behind the acrylic
    t = MAN["tela"]
    img = bpy.data.images.load(os.path.normpath(os.path.join(HERE, "..", "..", "..", "studentV4", "img", "tela_status_pt.png")))
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    pl = bpy.context.active_object
    pl.name = "oled_tela"
    pl.scale = M(t["w"], t["h"], 1.0)
    pl.location = M(t["cx"], t["cy_file"], t["z"])
    mt = bpy.data.materials.new("tela_oled")
    mt.use_nodes = True
    nt = mt.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.interpolation = "Closest"
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 9.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    pl.data.materials.append(mt)
    pl.parent = group_empty("oled")
    GROUP_OBJS["oled"].append(pl)
    new = import_glb(os.path.join(BUILD, "principal_full.glb"), "placa", (0, 0, -1.12), "placa")
    tune_board_materials(new)
    for r in (1, 2, 3, 4):
        ru = ROWS[r]
        new = import_glb(os.path.join(BUILD, "r8_full.glb"), "reg_r%d" % r, ruler_loc(ru["x0"], ru["y"], ZR[r - 1]), "reg%d" % r)
        tune_board_materials(new)
    # panel (step 1): two panels of two rulers + the mouse-bite tabs
    for tag, ys in (("pA", (70.0, 86.0)), ("pB", (22.0, 38.0))):
        for i, y in enumerate(ys):
            new = import_glb(os.path.join(BUILD, "r8_full.glb"), "%s%d" % (tag, i + 1), ruler_loc(60.0, y, 0.0), "%s%d" % (tag, i + 1))
            tune_board_materials(new)
        e = group_empty("%s_abas" % tag)
        for xu in (30.0, 74.0, 118.0):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            o = bpy.context.active_object
            o.scale = M(5.0, 2.6, 1.12)
            o.location = M(60.0 + xu, -(ys[0] + ys[1]) / 2.0, -0.56)
            o.data.materials.append(principled("aba", "#1B5A33", 0.55))
            o.parent = e
            GROUP_OBJS["%s_abas" % tag].append(o)


# ------------------------------------------------------------------ note labels on the caps
def add_labels():
    e = group_empty("rotulos")
    for k in MAN["keys"]:
        z = ZR[k["row"] - 1] + 22.8 + 0.03
        bpy.ops.object.text_add(location=M(k["x"], -k["y"], z))
        o = bpy.context.active_object
        o.data.body = k["nome"]
        o.data.size = 0.0036
        o.data.extrude = 0.00012
        o.data.align_x = "CENTER"
        o.data.align_y = "CENTER"
        bpy.ops.object.convert(target="MESH")
        o = bpy.context.active_object
        col = "#F4F1E8" if k["tipo"] == "black" else "#1B1B1B"
        o.data.materials.append(principled("txt_" + k["tipo"], col, 0.4))
        o.parent = e
        o.name = "rot_" + k["nome"]
        GROUP_OBJS["rotulos"].append(o)
        k["_row"] = k["row"]
    # a small paper plate under the letters of the C/F caps (the checker would swallow them)
    for k in MAN["keys"]:
        if k["tipo"] != "cf":
            continue
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        o = bpy.context.active_object
        o.scale = M(6.6, 3.8, 0.12)
        o.location = M(k["x"], -k["y"], ZR[k["row"] - 1] + 22.8 + 0.0)
        o.data.materials.append(principled("plate", "#F1ECE1", 0.3))
        o.parent = e
        GROUP_OBJS["rotulos"].append(o)


# ------------------------------------------------------------------ shots
def explode(**kw):
    return {k: v for k, v in kw.items()}


ALLROWS = lambda f: {("%s_r%d" % (p, r)): f(r) for p in ("reg", "gra", "tec", "cab", "par", "por", "capa") for r in (1, 2, 3, 4)}


def shots():
    iso = [(CX - 230, CY - 330, 250), (CX, CY + 5, 5), (0, 0, 1)]
    below = [(CX - 160, CY - 300, -260), (CX, CY + 5, -2), (0, 0, 1)]
    inner_lid = ["tampa", "janela", "oled", "qwiic", "alto_falante", "caixa", "fios"]
    boardg = ["placa", "encoders", "modulo", "m25_parafuso", "m25_espacador", "m25_porca", "bateria"]
    rows = lambda p: ["%s_r%d" % (p, r) for r in (1, 2, 3, 4)]
    S = {}

    def add(name, shown, cam, zoom, size, offs=None, fade=(), floor=False, under=False, anchors=None, labels=False):
        S[name] = dict(shown=list(shown), cam=cam, zoom=zoom, size=list(size), offsets=offs or {}, fade=list(fade), floor=floor, under=under,
                       anchors=anchors or {}, labels=labels)

    closed = ["tampa", "base", "janela", "oled", "encoders", "knobs"] + rows("capa")
    add("foto_instrumento", closed + ["rotulos"], [(CX - 170, CY - 290, 190), (CX - 5, CY + 5, 8), (0, 0, 1)], 1.18, (2400, 1500), floor=True, labels=True)
    add("foto_tela", closed + ["rotulos"], [(30, -75, 150), (37, -24, 12), (0, 0, 1)], 2.2, (2000, 1200), floor=True, labels=False)
    off_ex = {"base": (0, 0, -70), "parafusos_base": (0, 0, -70), "pes": (0, 0, -78)}
    for r in (1, 2, 3, 4):
        for p in ("reg", "cab", "por"):
            off_ex["%s_r%d" % (p, r)] = (0, 0, -34)
        off_ex["par_r%d" % r] = (0, 0, 14)
        off_ex["gra_r%d" % r] = (0, 0, 0)
        off_ex["tec_r%d" % r] = (0, 0, 20)
        off_ex["capa_r%d" % r] = (0, 0, 150)
    for g in inner_lid:
        off_ex[g] = (0, 0, 70)
    for g in boardg:
        off_ex[g] = (0, 0, 70)
    off_ex["knobs"] = (0, 0, 150)
    off_ex["rotulos"] = (0, 0, 150)
    alls = sorted(set(GROUPS) - {"pA1", "pA2", "pB1", "pB2", "pA_abas", "pB_abas", "pta_r1", "pta_r2", "pta_r3", "pta_r4", "fios2"})
    add("foto_explodido", alls, [(CX - 330, CY - 480, 330), (CX - 30, CY + 5, 55), (0, 0, 1)], 1.0, (2400, 2000), off_ex)

    # 1: break the rulers out of the panel
    pan = ["pA1", "pA2", "pB1", "pB2", "pA_abas", "pB_abas"]
    add("passo_1", pan, [(60 + 74 - 90, -20 - 300, 210), (60 + 74, -54, 0), (0, 0, 1)], 1.5, (2000, 1300),
        {"pA2": (0, -12, 6), "pB2": (0, -12, 6)}, floor=True,
        anchors={"1": ("pA1", (134, 70, 1.2)), "2": ("pA_abas", (104, 78, 0)), "3": ("pA2", (134, 86, 1.2)), "4": ("pB1", (134, 22, 1.2))})
    # 2: the home soldering: encoders, speaker wires
    add("passo_2", ["placa", "encoders", "alto_falante", "fios2"], [(-60, -300, 180), (40, -56, 8), (0, 0, 1)], 1.45, (2000, 1300),
        {"encoders": (0, 0, 26), "alto_falante": (0, 0, 50)}, floor=True,
        anchors={"1": ("placa", (40, 50, 0)), "2": ("encoders", (28, 44.5, 6)), "3": ("encoders", (46, 44.5, 6)), "4": ("alto_falante", (37, 73.1, 8)), "5": ("placa", (48.1, 94.4, 0))})
    # 3: the MicroMod under the board
    add("passo_3", ["placa", "encoders", "modulo", "m25_parafuso", "m25_espacador", "m25_porca"], [(-90, -230, -150), (36, -18, -10), (0, 0, 1)], 1.45, (2000, 1300),
        {"modulo": (0, 0, -20), "m25_espacador": (0, 0, -8), "m25_porca": (0, 0, -36), "m25_parafuso": (0, 0, 14)}, fade=["placa", "encoders"], under=True,
        anchors={"1": ("modulo", (34, 18, -5.0)), "2": ("m25_parafuso", (42, 14, 1.0)), "3": ("m25_espacador", (42, 14, -2.5)), "4": ("m25_porca", (42, 14, -6.0)), "5": ("placa", (22, 18, -3.0))})
    # 4: OLED, window, speaker and box into the lid (lid face down)
    add("passo_4", inner_lid, [(-80, -330, -240), (42, -50, -30), (0, 0, 1)], 1.0, (2000, 1300),
        {"janela": (0, 0, -22), "oled": (0, 0, -44), "qwiic": (0, 0, -44), "alto_falante": (0, -42, -66), "caixa": (0, -42, -84), "fios": (0, -42, -66)}, fade=["tampa"], under=True,
        anchors={"1": ("tampa", (30, 20, 12)), "2": ("janela", (37, 22, 12)), "3": ("oled", (30, 25, 11)), "4": ("qwiic", (47, 19, 5)), "5": ("alto_falante", (37, 73, 8)), "6": ("caixa", (37, 73, 4))})
    # 5: the battery to the board
    add("passo_5", ["placa", "encoders", "modulo", "m25_parafuso", "m25_espacador", "m25_porca", "bateria"], [(-60, -230, -190), (40, -50, -14), (0, 0, 1)], 1.25, (2000, 1250),
        {"bateria": (0, 0, 0)}, fade=["placa", "encoders", "modulo", "m25_parafuso", "m25_espacador", "m25_porca"], under=True,
        anchors={"1": ("bateria", (34, 65, -3)), "2": ("bateria", (30, 37, -5)), "3": ("placa", (64.5, 26.5, -4.5)), "4": ("placa", (40, 70, -1.2))})
    # R15V4 (bolts BEFORE the keys: with the grade and the keys on, the grade's web covers the bolt heads and the gap between the covers is 3.1 mm)
    # 6: the tray with the nuts (seen from below)
    add("passo_6", ["base"] + rows("por"), [(CX - 110, CY - 250, -250), (CX, CY + 5, -12), (0, 0, 1)], 1.0, (2000, 1250), {("por_r%d" % r): (0, 0, -30) for r in (1, 2, 3, 4)}, under=True,
        anchors={"1": ("base", (120, 10, -10)), "2": ("por_r1", (107.7, 79.2, -9)), "3": ("por_r4", (116.95, 31.2, -5)), "4": ("base", (200, 90, -10))})
    # 7: rulers (with their cables) into the tray, front to back (row 1 first), then the bolts
    o8 = {}
    for r in (1, 2, 3, 4):
        z = 22.0 * r
        for p in ("reg", "cab"):
            o8["%s_r%d" % (p, r)] = (0, 0, z)
        o8["par_r%d" % r] = (0, 0, z + 20)
    add("passo_7", ["base"] + rows("por") + rows("reg") + rows("cab") + rows("par"),
        [(CX - 260, CY - 330, 200), (CX, CY + 5, 40), (0, 0, 1)], 1.08, (2000, 1350), o8,
        anchors={"1": ("base", (120, 95, -6)), "2": ("reg_r1", (130, 74, 0)), "3": ("cab_r1", (100, 62, -7)), "4": ("par_r1", (107.7, 79.2, 1)), "5": ("par_r4", (116.95, 31.2, 8)), "6": ("cab_r4", (100, 20, 0))})
    # 8: grade + 4 keys of each row down onto the bolted rulers (pegs into the ruler)
    o6 = {}
    for r in (1, 2, 3, 4):
        o6["gra_r%d" % r] = (0, 0, 16)
        o6["tec_r%d" % r] = (0, 0, 34)
    add("passo_8", ["base"] + rows("por") + rows("reg") + rows("cab") + rows("par") + rows("gra") + rows("tec"), [(CX - 150, CY - 260, 190), (CX + 20, CY, 12), (0, 0, 1)], 1.3, (2000, 1250), o6,
        anchors={"1": ("reg_r1", (130, 74, 0)), "2": ("gra_r1", (136, 74, 4.5)), "3": ("tec_r1", (116.95, 74, 8)), "4": ("reg_r4", (130, 26, 7))})
    # 9: the board into the lid, cables (lid face down)
    o9 = {g: (0, 0, -60) for g in boardg}
    o9["pta_r1"] = o9["pta_r2"] = o9["pta_r3"] = o9["pta_r4"] = (0, 0, -60)
    add("passo_9", inner_lid + boardg + rows("pta"), [(40, -330, -250), (62, -50, -8), (0, 0, -1)], 1.1, (2000, 1250), o9, fade=inner_lid, under=True,
        anchors={"1": ("placa", (40, 50, -1.2)), "2": ("pta_r1", (90, 74, -2.6)), "3": ("pta_r4", (90, 26, -2.6)), "4": ("qwiic", (35, 30, -3)), "5": ("bateria", (30, 60, -5)), "6": ("modulo", (34, 18, -5))})
    # 10: lid on the tray (normal view), caps and knobs, screws from below
    o10 = {g: (0, 0, 80) for g in inner_lid + boardg}
    o10["tampa"] = (0, 0, 80)
    o10["bateria"] = (0, 0, 0)
    for r in (1, 2, 3, 4):
        o10["capa_r%d" % r] = (0, 0, 130)
    o10["knobs"] = (0, 0, 130)
    o10["parafusos_base"] = (0, 0, -40)
    keep = ["base", "parafusos_base"] + rows("por") + rows("reg") + rows("gra") + rows("tec") + rows("cab") + rows("par")
    add("passo_10", keep + inner_lid + boardg + rows("capa") + ["knobs", "rotulos"], [(CX - 300, CY - 400, 260), (CX, CY + 5, 50), (0, 0, 1)], 1.0, (2000, 1500),
        dict(o10, rotulos=(0, 0, 130)), fade=keep, labels=True,
        anchors={"1": ("tampa", (130, 6, 14)), "2": ("capa_r2", (98.45 - 9.25 + 9.25 + 18.5, 58, 22.8)), "3": ("knobs", (28, 44.5, 14.6)), "4": ("parafusos_base", (176.6, 93, -9)), "5": ("base", (120, 95, -6))})
    # 11: feet (seen from below)
    add("passo_11", ["tampa", "base", "parafusos_base", "pes"], [(CX - 110, CY - 250, -250), (CX, CY + 5, -8), (0, 0, 1)], 1.2, (2000, 1250), {"pes": (0, 0, -22)}, under=True,
        anchors={"1": ("pes", (14, 10, -11)), "2": ("pes", (230, 90, -11)), "3": ("base", (120, 50, -10))})
    return S


# ------------------------------------------------------------------ render
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
    cam.matrix_world = mathutils.Matrix(((r.x, u.x, -f.x, p.x), (r.y, u.y, -f.y, p.y), (r.z, u.z, -f.z, p.z), (0, 0, 0, 1)))


def lights_and_world(sc, target, dist, under, floor, zmin):
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = lin("#F3F1EC")
    bg.inputs["Strength"].default_value = 0.22
    sc.world = world
    t = mathutils.Vector(target)
    r = dist
    rig = [("key", (-1.0, -1.6, 1.8), 1500, 1.0), ("fill", (1.6, -0.8, 0.9), 450, 1.8), ("rim", (0.4, 1.6, 1.2), 900, 0.8), ("top", (0, 0, 2.5), 250, 2.4)]
    if under:
        rig += [("under1", (-1.0, -1.4, -1.6), 1300, 1.4), ("under2", (1.4, -0.6, -1.2), 700, 1.8)]
    for name, (dx, dy, dz), power, size in rig:
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = power * r * r * 0.04
        ld.size = size * r
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = t + mathutils.Vector((dx, dy, dz)) * r
        lo.rotation_euler = (t - lo.location).to_track_quat("-Z", "Y").to_euler()
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=3.0, location=(t.x, t.y, zmin))
        fl = bpy.context.active_object
        fl.name = "floor"
        fl.data.materials.append(principled("floor", "#F3F1EC", 0.9))
        fl.is_shadow_catcher = True


FADE_MATS = {}


def set_fade(objs, on):
    for o in objs:
        if o.type != "MESH":
            continue
        for i, m in enumerate(o.data.materials):
            if not m or not m.node_tree or "Principled BSDF" not in m.node_tree.nodes:
                continue
            b = m.node_tree.nodes["Principled BSDF"]
            key = m.name
            if on:
                FADE_MATS.setdefault(key, (list(b.inputs["Base Color"].default_value), b.inputs["Alpha"].default_value))
                c = FADE_MATS[key][0]
                paper = lin("#F3F1EC")
                b.inputs["Base Color"].default_value = [x + (p - x) * 0.38 for x, p in zip(c, paper)]
            elif key in FADE_MATS:
                b.inputs["Base Color"].default_value = FADE_MATS[key][0]


def render_shot(name, s, fast):
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name == "floor":
            bpy.data.objects.remove(o, do_unlink=True)
    shown = set(s["shown"])
    fade = set(s["fade"])
    for g, e in GROUPS.items():
        vis = g in shown
        e.location = M(*s["offsets"].get(g, (0, 0, 0)))
        for o in GROUP_OBJS[g]:
            o.hide_render = not vis
            o.hide_viewport = not vis
        set_fade(GROUP_OBJS[g], g in fade)
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
    lights_and_world(sc, M(*target), max(dist * 0.55, 0.25), s["under"], s["floor"], (-0.0102 if name != "passo_1" else -0.0012))
    scale = 0.5 if fast else 1.0
    W, H = int(s["size"][0] * scale), int(s["size"][1] * scale)
    setup_render(sc, (W, H), 24 if fast else 160)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.context.view_layer.update()
    # anchors -> pixel fractions
    anc = {}
    for n, (g, p) in s["anchors"].items():
        off = s["offsets"].get(g, (0, 0, 0))
        w = mathutils.Vector(M(p[0] + off[0], -p[1] + off[1], p[2] + off[2]))
        co = bpy_extras.object_utils.world_to_camera_view(sc, cam, w)
        anc[n] = [round(co.x, 4), round(1 - co.y, 4)]
    json.dump(anc, open(os.path.join(OUT, name + ".json"), "w"))
    bpy.ops.render.render(write_still=True)
    print("rendered", name, anc)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    fast = "--fast" in argv
    names = [a for a in argv if not a.startswith("--")]
    os.makedirs(OUT, exist_ok=True)
    build_scene()
    add_labels()
    S = shots()
    for n, s in S.items():
        if names and n not in names:
            continue
        # labels only where asked: they are objects of the 'rotulos' group (hidden otherwise)
        render_shot(n, s, fast)


main()
