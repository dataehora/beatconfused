"""eTutti Slim (R3SL, stage 2a): 3D scene of the four rulers + grades + switches + case, with sections. CadQuery + PyVista.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/case.py            (first: the case)
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/cena_regua.py

Realistic models: the KS-33D (Gateron STEP), TMAG5253 / 74HC595 / FFC (EasyEDA STEP by LCSC code, modelos/baixados/), the 0402 and 0805 capacitors (KiCad 3D library),
placed from pcb/regua/posicao_regua.json by fitting each part's footprint pads to its placed pads (so the rotation / bottom-side mirror is exactly KiCad's).
The ruler board and the grade are built from the Design's contract (envelope_regua.json). Writes case/renders/{cena_iso,corte_tecla,corte_cauda,corte_longitudinal}.png.
"""
import glob
import json
import os
import re
import sys

import cadquery as cq
import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import layout_slim as L  # noqa: E402
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import verificacao as V  # noqa: E402

OUT = os.path.join(HERE, "out")
REN = os.path.join(HERE, "renders")
TMP = os.path.join(OUT, "tmp")
os.makedirs(REN, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
POS = json.load(open(os.path.join(HW, "pcb", "regua", "posicao_regua.json"), encoding="utf-8"))
ENV = json.load(open(os.path.join(HERE, "envelope_regua.json"), encoding="utf-8"))
KISH = "C:/Program Files/KiCad/10.0/share/kicad"
SW_STEP = os.path.join(HW, "fornecimento", "gateron", "KS-33D_FB_POM_Mini.stp")
BX = os.path.join(HW, "modelos", "baixados")
SW_AXIS = (16.7, 4.5)
SW_SEAT = -1.4                                   # PCB top face in the STEP's z (verified: stem top 9.4 above it, post bottom 3.7 below it)
STEPS = {"tmag5253": glob.glob(BX + "/tmag5253_C22401868.step")[0], "hc595": glob.glob(BX + "/hc595_dhvqfn_C730243.step")[0],
         "ffc": glob.glob(BX + "/ffc_8p_05_h1_C3250113.step")[0]}
FFC_CENTER_FP = (0.0, 0.45)                      # the STEP is centred on its body; the footprint origin is the pad row's centre line
KICAD3D = {"C_0402": KISH + "/3dmodels/Capacitor_SMD.3dshapes/C_0402_1005Metric.step", "C_0805": KISH + "/3dmodels/Capacitor_SMD.3dshapes/C_0805_2012Metric.step"}


def step_mesh(path, name):
    f = os.path.join(TMP, name + ".stl")
    if not os.path.exists(f):
        cq.exporters.export(cq.importers.importStep(path), f, tolerance=0.03, angularTolerance=0.2)
    return pv.read(f)


def stl_mesh(wp, name):
    f = os.path.join(TMP, name + ".stl")
    cq.exporters.export(wp, f, tolerance=0.05, angularTolerance=0.1)
    return pv.read(f)


def fp_pads(libfile):
    t = open(libfile, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'\(pad "?(\w*)"? (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+)', t):
        out.setdefault(m.group(1), (float(m.group(4)), float(m.group(5))))
    return out


def fp_file(fpname):
    if fpname in ("TMAG5253_X2SON4_EE", "HC595_DHVQFN16_EE", "FFC_8P_0.5_KH-H1.0", "KS33D_holes"):
        return os.path.join(HW, "pcb", "kicad_regua", "slim.pretty", fpname + ".kicad_mod")
    for d in ("Capacitor_SMD",):
        f = "%s/footprints/%s.pretty/%s.kicad_mod" % (KISH, d, fpname)
        if os.path.exists(f):
            return f


def fit_affine(src, dst):
    """2x3 affine (rotation / reflection + translation) from footprint-local to placed pad positions (least squares)."""
    A = np.hstack([np.array(src), np.ones((len(src), 1))])
    X, *_ = np.linalg.lstsq(A, np.array(dst), rcond=None)
    return X.T       # 2x3


def part_transforms():
    """{ref: (A 2x3 in (u, v), bottom?)} from posicao_regua.json."""
    pads = {}
    for p in POS["pads"]:
        pads.setdefault(p["ref"], {}).setdefault(p["n"], []).append((p["u"], p["v"]))
    res = {}
    for ref, q in POS["pecas"].items():
        if ref.startswith(("SW", "H")):
            continue
        lib = fp_pads(fp_file(q["fp"]))
        src, dst = [], []
        for n, lst in pads[ref].items():
            if n in lib and n != "MP":
                src.append(lib[n]); dst.append(lst[0])
        if len(src) >= 3 and np.linalg.matrix_rank(np.array(src) - np.mean(src, axis=0)) >= 2:
            A = fit_affine(src, dst)
        else:                                   # two pads: rotation only, from the axis through them
            s0, s1, d0, d1 = np.array(src[0]), np.array(src[1]), np.array(dst[0]), np.array(dst[1])
            a = np.arctan2(*(d1 - d0)[::-1]) - np.arctan2(*(s1 - s0)[::-1])
            R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
            t = (d0 + d1) / 2 - R @ ((s0 + s1) / 2)
            A = np.hstack([R, t.reshape(2, 1)])
        res[ref] = (A, q["lado"] == "baixo", q["fp"])
    return res


def place(mesh, A, bottom, rowinfo, center_fp=(0.0, 0.0), z_pcb=None):
    """Place a part mesh (model xy = footprint frame, z up from the pad plane) on ruler `rowinfo`."""
    m = mesh.copy()
    pts = np.array(m.points)
    xy = pts[:, :2] - np.array(center_fp)
    uv = (A[:, :2] @ xy.T).T + A[:, 2]
    x = rowinfo["x_left"] + uv[:, 0]
    y = rowinfo["y"] - uv[:, 1]                  # +v is the player (front) = -y in the instrument frame
    z = (rowinfo["z_bottom"] - pts[:, 2]) if bottom else (rowinfo["z_top"] + pts[:, 2])
    m.points = np.column_stack([x, y, z])
    if bottom:                                   # mirrored z (and the fit's reflection): keep the normals outward
        m.flip_faces(inplace=True)
    return m


def ruler_board(r):
    ri = ENV["fileiras"][r]
    x0, y0 = ri["x_left"], ri["y"]
    pcb = cq.Workplane("XY").box(L.RULER_L, L.RULER_W, L.RULER_T, centered=False).translate((x0, y0 - L.RULER_W / 2, ri["z_bottom"]))
    for k in ri["keys"]:
        pcb = pcb.cut(cq.Workplane("XY").workplane(offset=ri["z_bottom"] - 1).center(k["x"], k["y"]).circle(L.POST_D / 2).extrude(3))
        for sgn in (-1, 1):
            pcb = pcb.cut(cq.Workplane("XY").workplane(offset=ri["z_bottom"] - 1).center(k["x"] + sgn * L.PEG_DX, k["y"]).circle(L.PEG_D / 2).extrude(3))
    for u, v, sl in zip(ri["m2_u"], ri["m2_v"], ENV["regua"]["m2_slot"]):
        hole = cq.Workplane("XY").workplane(offset=ri["z_bottom"] - 1).center(x0 + u, y0 + v)
        pcb = pcb.cut(hole.slot2D(sl, L.M2_D).extrude(3) if sl else hole.circle(L.M2_D / 2).extrude(3))
    return pcb


def grade_board(r):
    ri = ENV["fileiras"][r]
    x0 = ri["x_left"] + L.GRADE_U0
    gl = L.GRADE_U1 - L.GRADE_U0
    g = cq.Workplane("XY").box(gl, L.GRADE_W, L.GRADE_T, centered=False).translate((x0, ri["y"] - L.GRADE_W / 2, ri["grade_z_bottom"]))
    for k in ri["keys"]:
        g = g.cut(cq.Workplane("XY").workplane(offset=ri["grade_z_bottom"] - 1).center(k["x"], k["y"]).rect(L.GRADE_HOLE, L.GRADE_HOLE).extrude(4))
        for sx in (-1, 1):
            for sy in (-1, 1):
                g = g.cut(cq.Workplane("XY").workplane(offset=ri["grade_z_bottom"] - 1).center(k["x"] + sx * (L.GRADE_HOLE / 2 - L.GRADE_DOGBONE[0]), k["y"] + sy * (L.GRADE_HOLE / 2 - L.GRADE_DOGBONE[0])).circle(L.GRADE_DOGBONE[1]).extrude(4))
    for u, v, sl in zip(ri["m2_u"], ri["m2_v"], ENV["regua"]["m2_slot"]):
        hole = cq.Workplane("XY").workplane(offset=ri["grade_z_bottom"] - 1).center(ri["x_left"] + u, ri["y"] + v)
        g = g.cut(hole.slot2D(sl, L.M2_D).extrude(4) if sl else hole.circle(L.M2_D / 2).extrude(4))
    return g


def hardware(r):
    """Spacers, M2 bolts and nuts of one ruler."""
    ri = ENV["fileiras"][r]
    out = []
    for u, v in zip(ri["m2_u"], ri["m2_v"]):
        x, y = ri["x_left"] + u, ri["y"] + v
        sp = cq.Workplane("XY").workplane(offset=ri["z_top"]).center(x, y).circle(1.9).circle(1.1).extrude(L.SPACER_H)
        head = cq.Workplane("XY").workplane(offset=ri["grade_z_bottom"] + L.GRADE_T).center(x, y).circle(1.9).extrude(1.6)
        shank = cq.Workplane("XY").workplane(offset=ri["z_bottom"] - 2.0).center(x, y).circle(1.0).extrude(ri["grade_z_bottom"] + L.GRADE_T - ri["z_bottom"] + 2.0)
        nut = cq.Workplane("XY").workplane(offset=ri["z_bottom"] - 1.6).center(x, y).polygon(6, 4.6).extrude(1.6)
        out += [sp, head.union(shank), nut]
    return out


def build_scene():
    meshes = []                                  # (mesh, color, opacity, name)
    base = pv.read(os.path.join(OUT, "base.stl")); lid = pv.read(os.path.join(OUT, "tampo.stl"))
    meshes.append((base, "#b9b4a8", 1.0, "base"))
    meshes.append((lid, "#efe6d2", 1.0, "tampo"))
    tr = part_transforms()
    sw = step_mesh(SW_STEP, "ks33d")
    cache = {}
    for r in range(4):
        ri = ENV["fileiras"][r]
        meshes.append((stl_mesh(ruler_board(r), "pcb%d" % r), "#2f6b3a", 1.0, "regua%d" % r))
        meshes.append((stl_mesh(grade_board(r), "grade%d" % r), "#6b5a3a", 1.0, "grade%d" % r))
        for i, h in enumerate(hardware(r)):
            meshes.append((stl_mesh(h, "hw%d_%d" % (r, i)), "#9aa0a6", 1.0, "ferragem"))
        for k in ri["keys"]:
            m = sw.copy()
            m.translate((k["x"] - SW_AXIS[0], k["y"] - SW_AXIS[1], ri["z_top"] - SW_SEAT), inplace=True)
            meshes.append((m, "#cfd8cf", 1.0, "ks33d"))
        for ref, (A, bottom, fpname) in tr.items():
            if fpname.startswith("TMAG"):
                key, cen, col = "tmag5253", (0, 0), "#222222"
            elif fpname.startswith("HC595"):
                key, cen, col = "hc595", (0, 0), "#222222"
            elif fpname.startswith("FFC"):
                key, cen, col = "ffc", FFC_CENTER_FP, "#e8d9a8"
            elif fpname.startswith("C_0402"):
                key, cen, col = "C_0402", (0, 0), "#9b7b4a"
            elif fpname.startswith("C_0805"):
                key, cen, col = "C_0805", (0, 0), "#9b7b4a"
            else:
                continue
            if key not in cache:
                cache[key] = step_mesh(STEPS.get(key) or KICAD3D[key], key)
            meshes.append((place(cache[key], A, bottom, ri, cen), col, 1.0, ref))
    return meshes


def clip(mesh, normal, origin):
    """Keep the side the normal points to; closed solids get a cap (clip_closed_surface), open meshes are just clipped."""
    try:
        c = mesh.clip_closed_surface(normal=normal, origin=origin)
        if c.n_points:
            return c
    except Exception:
        pass
    return mesh.clip(normal=normal, origin=origin, invert=False)


def shot(meshes, name, normal=None, origin=None, cam=None, size=(1800, 900), hide=(), scale=None):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for m, col, op, nm in meshes:
        if nm in hide:
            continue
        if normal is not None:
            m = clip(m, normal, origin)
            if m.n_points == 0:
                continue
        pl.add_mesh(m, color=col, opacity=op, smooth_shading=False, show_edges=False)
    if cam:
        pl.camera_position = cam
    if scale:
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = scale
    pl.show(screenshot=os.path.join(REN, name + ".png"))
    pl.close()
    print(name)


def main():
    T0 = V.inicio()
    meshes = build_scene()
    V.forcar("cena_regua")
    r1 = ENV["fileiras"][0]
    # 1. iso without the lid: the four rulers on their steps
    shot(meshes, "cena_iso", cam=[(-170, -150, 150), (20, 25, 6), (0, 0, 1)], hide=("tampo",), size=(1800, 1000))
    # 2. transverse section through key 3 of row 1 (x = 37), the part x >= 37 kept, seen from -x; zoom on row 1 and a wide one with the four rows
    x3 = r1["keys"][2]["x"]
    shot(meshes, "corte_tecla", normal=(1, 0, 0), origin=(x3, 0, 0), cam=[(x3 - 150, 0, 10), (x3, 0, 10), (0, 0, 1)], size=(1800, 1000), scale=13)
    shot(meshes, "corte_tecla_4fileiras", normal=(1, 0, 0), origin=(x3, 0, 0), cam=[(x3 - 150, 24, 12), (x3, 24, 12), (0, 0, 1)], size=(1800, 1000), scale=36)
    # 3. section through the tail of row 1 (the FFC pads): x = x_left + 3.45
    xt = r1["x_left"] + 3.45
    shot(meshes, "corte_cauda", normal=(1, 0, 0), origin=(xt, 0, 0), cam=[(xt - 150, 0, 8), (xt, 0, 8), (0, 0, 1)], size=(1800, 1000), scale=13)
    # 4. longitudinal section on the centre line of row 1 (y = 0): the back half kept, seen from the front
    shot(meshes, "corte_longitudinal", normal=(0, 1, 0), origin=(0, 0.01, 0), cam=[(r1["x_left"] + 80, -150, 9), (r1["x_left"] + 80, 0, 9), (0, 0, 1)], size=(2000, 520), scale=18)


if __name__ == "__main__":
    _t0 = V.inicio()
    main()
    V.exige([os.path.join(REN, n + ".png") for n in ("cena_iso", "corte_tecla", "corte_tecla_4fileiras", "corte_cauda", "corte_longitudinal")], _t0, "cena_regua")
