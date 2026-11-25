"""eTutti Slim (R11SL item 2): assembly sequence, one image per step, from realistic models. CadQuery + PyVista.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/montagem.py   [--so-imagens]
    -> case/renders/montagem_p<n>_{iso,esq,dir}.png, case/montagem/{base.step, conjunto.glb, montagem.json}

Run first: case.py, cena_principal.py's inputs (pcb/principal/posicao_principal.json), pcb/regua/posiciona_regua.py (positions).
Steps (the order is justified in FIT_CHECK.md):
  1  the base with the 8 nuts in their pockets (one per guide)
  2  the battery in its bay, then the main board on its 5 posts (the FFC connectors J601..J604 face +x, open towards the rulers)
  3..6  ruler of row 1, 2, 3, 4: its 20 mm FFC cable already plugged into the ruler's J1 and into the main board's connector, the ruler laid on its guides/rails and
        screwed (M2 x 6 through the grade, spacer, ruler into the nut), one row per step (row 1 first: the lowest)
  7  the 32 KS-33D switches, pressed into the grade and the ruler (they close the assembly); note names on the keys
Models: KS-33D (Gateron STEP), FFC connector C3250113 (EasyEDA STEP), TMAG5253, 74HC595, caps (EasyEDA / KiCad 3D), the main board and its 98 parts (KiCad GLB-free: the
EasyEDA STEP by LCSC code fitted to the placed pads), VARTA 523450 (maker's STEP), M2 screws / spacers / nuts (drawn from the standards' dimensions: M2 x 6 pan head
D3.8 x 1.6, nut 4.0 AF x 1.6, spacer D3.8/D2.2 x 1.3).  The FFC CABLE has no maker's model (custom 20 mm): drawn as a 0.3 x 4.5 mm ribbon of the right length.
"""
import json
import math
import os
import shutil
import sys

import cadquery as cq
import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cena_principal as CP  # noqa: E402
import cena_regua as CR  # noqa: E402
import layout_slim as L  # noqa: E402

REN, OUT = CR.REN, CR.OUT
MONT = os.path.join(HERE, "montagem")
os.makedirs(MONT, exist_ok=True)
ENV = CR.ENV
CABLE_L, CABLE_W, CABLE_T, INSERT = 20.0, 4.5, 0.3, 3.4
COL = {"base": "#b9b4a8", "porca": "#c9ccd0", "placa": "#1f6b4a", "bateria": "#c7b9a5", "regua": "#2f6b3a", "grade": "#6b5a3a", "ferr": "#9aa0a6", "cabo": "#d9c27a", "ks": "#cfd8cf"}


def hexnut(x, y, z0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).polygon(6, 4.6).extrude(1.6)


def cable_mesh(x_edge, zb, x_left, zr, y):
    """The 20 mm FFC between the main board's connector (mouth at x_edge, z zb) and the ruler's J1 (mouth at x_left, z zr): 3.4 mm inside each connector, the free
    part an S plus a shallow bulge up, with the length that makes 20 mm in all."""
    free = CABLE_L - 2 * INSERT
    n = 60
    ts = np.linspace(0, 1, n)
    s = ts * ts * (3 - 2 * ts)

    def curve(a):
        xs = x_edge + (x_left - x_edge) * ts
        zs = zb + (zr - zb) * s + a * np.sin(np.pi * ts) ** 2
        return xs, zs

    def length(a):
        xs, zs = curve(a)
        return float(np.sum(np.hypot(np.diff(xs), np.diff(zs))))
    lo, hi = 0.0, 12.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if length(mid) < free:
            lo = mid
        else:
            hi = mid
    a = (lo + hi) / 2
    xs, zs = curve(a)
    xs = np.concatenate([[x_edge - INSERT], xs, [x_left + INSERT]])
    zs = np.concatenate([[zb], zs, [zr]])
    pts = np.column_stack([xs, np.full_like(xs, y), zs])
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    nrm = np.column_stack([-tang[:, 2], np.zeros(len(tang)), tang[:, 0]])
    verts = []
    for p, nn in zip(pts, nrm):
        for dy in (-CABLE_W / 2, CABLE_W / 2):
            for dn in (-CABLE_T / 2, CABLE_T / 2):
                verts.append(p + nn * dn + np.array([0, dy, 0]))
    verts = np.array(verts)
    faces = []
    m = len(pts)
    for i in range(m - 1):
        b0, b1 = 4 * i, 4 * (i + 1)
        for e0, e1 in ((0, 1), (1, 3), (3, 2), (2, 0)):
            faces += [4, b0 + e0, b0 + e1, b1 + e1, b1 + e0]
    faces += [4, 0, 1, 3, 2]
    e = 4 * (m - 1)
    faces += [4, e, e + 1, e + 3, e + 2]
    return pv.PolyData(verts, np.array(faces)), round(a, 2), round(length(a) + 2 * INSERT, 2)


def build_groups():
    tr = CR.part_transforms()
    sw = CR.step_mesh(CR.SW_STEP, "ks33d")
    cache = {}
    G = {}
    # step 1: base + nuts
    base = pv.read(os.path.join(OUT, "base.stl"))
    nuts = []
    for r in range(4):
        ri = ENV["fileiras"][r]
        for u, v in zip(ri["m2_u"], ri["m2_v"]):
            nuts.append((CR.stl_mesh(hexnut(ri["x_left"] + u, ri["y"] + v, ri["z_bottom"] - 1.6), "nut_%d_%d" % (r, int(u))), COL["porca"], 1.0, "porca%d" % r))
    G[1] = [(base, COL["base"], 1.0, "base")] + nuts
    # step 2: battery + main board (everything from the main-board scene that belongs to it)
    allm = CP.build()
    ruler_refs = set(CR.POS["pecas"].keys())
    drop = ruler_refs | {"base", "tampo", "ferragem", "ks33d", "knob_registros", "knob_volume"} | {"regua%d" % r for r in range(4)} | {"grade%d" % r for r in range(4)}
    G[2] = [m for m in allm if m[3] not in drop]
    # steps 3..6: one ruler with its grade, hardware (screws + spacers), parts and FFC cable
    cables = {}
    for r in range(4):
        ri = ENV["fileiras"][r]
        fr = ENV["ffc_principal"][r] if "ffc_principal" in ENV else None
        grp = [(CR.stl_mesh(CR.ruler_board(r), "pcb%d" % r), COL["regua"], 1.0, "regua%d" % r), (CR.stl_mesh(CR.grade_board(r), "grade%d" % r), COL["grade"], 1.0, "grade%d" % r)]
        for i, h in enumerate(CR.hardware(r)):
            if i % 3 == 2:                        # the nut is already in its pocket (step 1)
                continue
            grp.append((CR.stl_mesh(h, "hw%d_%d" % (r, i)), COL["ferr"], 1.0, "ferragem"))
        for ref, (A, bottom, fpname) in tr.items():
            if fpname.startswith("TMAG"):
                key, cen, col = "tmag5253", (0, 0), "#222222"
            elif fpname.startswith("HC595"):
                key, cen, col = "hc595", (0, 0), "#222222"
            elif fpname.startswith("FFC"):
                key, cen, col = "ffc", CR.FFC_CENTER_FP, "#e8d9a8"
            elif fpname.startswith("C_0402"):
                key, cen, col = "C_0402", (0, 0), "#9b7b4a"
            elif fpname.startswith("C_0805"):
                key, cen, col = "C_0805", (0, 0), "#9b7b4a"
            else:
                continue
            if key not in cache:
                cache[key] = CR.step_mesh(CR.STEPS.get(key) or CR.KICAD3D[key], key)
            grp.append((CR.place(cache[key], A, bottom, ri, cen), col, 1.0, "%s_r%d" % (ref, r)))
        f = [q for q in ENV_P["ffc"] if q["fileira"] == r + 1][0]
        zb = 6.8 - 0.5
        zr = ri["z_bottom"] - 0.5
        cm, bulge, total = cable_mesh(f["x_borda_placa"], zb, ri["x_left"], zr, ri["y"])
        grp.append((cm, COL["cabo"], 1.0, "cabo%d" % r))
        cables[r + 1] = {"bulge_mm": bulge, "comprimento_total_mm": total, "vao_mm": f["folga_horizontal_mm"], "dz_mm": round(zr - zb, 2)}
        G[3 + r] = grp
    # step 7: switches
    sws = []
    for r in range(4):
        ri = ENV["fileiras"][r]
        for k in ri["keys"]:
            m = sw.copy()
            m.translate((k["x"] - CR.SW_AXIS[0], k["y"] - CR.SW_AXIS[1], ri["z_top"] - CR.SW_SEAT), inplace=True)
            sws.append((m, COL["ks"], 1.0, "ks_%s_%d" % (k["note"], r)))
    G[7] = sws
    return G, cables


def scene_upto(G, n):
    out = []
    for i in range(1, n + 1):
        out += G[i]
    return out


def shot(meshes, name, cam, size=(1800, 1000), scale=None, labels=None):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for m, col, op, nm in meshes:
        pl.add_mesh(m, color=col, opacity=op, smooth_shading=False, show_edges=False)
    if labels:
        pts = np.array([p for p, _ in labels])
        pl.add_point_labels(pts, [t for _, t in labels], font_size=11, shape=None, text_color="black", always_visible=True, show_points=False)
    pl.camera_position = cam
    if scale:
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = scale
    pl.show(screenshot=os.path.join(REN, name + ".png"))
    pl.close()
    print(name)


def details(n):
    """focal points of the two detail views of step n"""
    if n == 1:
        r = ENV["fileiras"][0]
        return (r["x_left"] + L.M2_ENDS[0], r["y"], 3.0), (r["x_left"] + L.M2_ENDS[1], r["y"], 3.0), 14
    if n == 2:
        return (-33.0, 24.0, 7.0), (-78.0, 14.0, 5.0), 34
    r = ENV["fileiras"][n - 3] if n <= 6 else ENV["fileiras"][0]
    zt = r["z_top"] + 1.5
    return (r["x_left"] + 12.0, r["y"], zt), (r["x_left"] + L.M2_ENDS[1] - 4.0, r["y"], zt), 17


def export_glb(meshes, path):
    pl = pv.Plotter(off_screen=True)
    for m, col, op, nm in meshes:
        if m.n_cells > 6000:                    # the glb is for turning the model: decimate the heavy parts (the 32 switches, the battery's text)
            m = m.triangulate().decimate(0.75)
        pl.add_mesh(m, color=col, opacity=op)
    try:
        pl.export_gltf(path)
        ok = True
    except Exception as e:  # noqa: BLE001
        print("glb:", e)
        ok = False
    pl.close()
    return ok


ENV_P = json.load(open(os.path.join(HERE, "envelope_principal.json"), encoding="utf-8"))


def main():
    G, cables = build_groups()
    notes = []
    for r in range(4):
        ri = ENV["fileiras"][r]
        for k in ri["keys"]:
            notes.append(((k["x"], k["y"], ri["z_top"] + 6.5), k["note"]))
    iso = [(-175, -150, 165), (30, 28, 8), (0, 0, 1)]
    for n in range(1, 8):
        ms = scene_upto(G, n)
        lab = notes if n == 7 else None
        shot(ms, "montagem_p%d_iso" % n, iso, labels=lab)
        a, b, sc = details(n)
        for tag, p in (("esq", a), ("dir", b)):
            cam = [(p[0] - 38, p[1] - 52, p[2] + 40), p, (0, 0, 1)]
            shot(ms, "montagem_p%d_%s" % (n, tag), cam, size=(1400, 900), scale=sc, labels=([q for q in notes if abs(q[0][0] - p[0]) < 30 and abs(q[0][1] - p[1]) < 14] if n == 7 else None))
    allm = scene_upto(G, 7)
    ok = export_glb(allm, os.path.join(MONT, "conjunto.glb"))
    shutil.copy(os.path.join(OUT, "base.step"), os.path.join(MONT, "base.step"))
    json.dump({"passos": 7, "glb": ok, "cabos": cables}, open(os.path.join(MONT, "montagem.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(cables))


if __name__ == "__main__":
    main()
