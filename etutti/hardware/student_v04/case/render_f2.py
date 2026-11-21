"""eTutti Student V4 (R2V4 F2): pictures of the conceptual case. Reads out/f2_<n>_*.stl (case_f2.py), writes renders/f2_*.png.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/render_f2.py
Grey = case pieces, green = rulers, orange = foam, light = KS-20 stand-ins and caps. No finish, no logo.
"""
import os

import sys

import numpy as np
import pyvista as pv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
REN = os.path.join(HERE, "renders")
os.makedirs(REN, exist_ok=True)
C = {"tampa": "#C9C5BB", "base": "#8F8C85", "reguas": "#2F7D4F", "teclas": "#EDE8DA", "espuma": "#D9822B"}


def load(n, name, dz=0.0, dy=0.0):
    m = pv.read(os.path.join(OUT, "f2_%d_%s.stl" % (n, name)))
    if dz or dy:
        m = m.translate((0, dy, dz))
    return m


def scene(parts, path, cam, size=(1800, 900), parallel=False, clip=None, zoom=1.0, scale=None):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for m, col in parts:
        if clip is not None:
            m = m.clip_closed_surface(normal=clip[0], origin=clip[1])
        pl.add_mesh(m, color=col, smooth_shading=False, show_edges=False, specular=0.1)
    if parallel:
        pl.enable_parallel_projection()
    pl.camera_position = cam
    if parallel and scale:
        pl.camera.parallel_scale = scale
    else:
        pl.camera.zoom(zoom)
    pl.screenshot(path)
    pl.close()


def main():
    n = 28
    L = 252.0
    ctr = (L / 2, -50.0, 8.0)
    # 1. closed, isometric from the front-left
    parts = [(load(n, "tampa"), C["tampa"]), (load(n, "base"), C["base"]), (load(n, "teclas"), C["teclas"])]
    scene(parts, os.path.join(REN, "f2_28_iso.png"), [(L * 0.15, -330.0, 210.0), ctr, (0, 0, 1)], zoom=1.35)
    # 2. exploded
    parts = [(load(n, "base"), C["base"]), (load(n, "reguas", 22), C["reguas"]), (load(n, "teclas", 44), C["teclas"]),
             (load(n, "espuma", 66), C["espuma"]), (load(n, "tampa", 92), C["tampa"])]
    scene(parts, os.path.join(REN, "f2_28_explodido.png"), [(L * 0.1, -380.0, 330.0), (L / 2, -50.0, 55.0), (0, 0, 1)], size=(1800, 1100), zoom=1.25)
    # 3/4. sections: cut in CadQuery (the STL meshes are not clean enough for a capped clip)
    import cadquery as cq
    import case_f2 as F
    pieces = {"tampa": F.lid(0), "base": F.base(0), "reguas": F.rulers_solid(0), "espuma": F.foam_rings(0), "teclas": F.key_bodies(0, 0.0, True)}
    x0 = 107.7
    ycut = 41.99                       # row 3 (y_spec) through the middle of its keys
    halfx = F.box(x0 - 600, x0, -50, 150, -50, 80)           # keep x <= x0, seen from +x
    halfy = F.box(-50, 600, -50, ycut, -50, 80)            # keep y_spec <= ycut (the back half), seen from the front
    for tag, half, mirror_it in (("x", halfx, True), ("y", halfy, True)):
        for name, w in pieces.items():
            cut = F.mirror(w.intersect(half))
            cq.exporters.export(cut, os.path.join(OUT, "f2_28_cut%s_%s.stl" % (tag, name)), tolerance=0.05, angularTolerance=0.2)
    cols = {"tampa": C["tampa"], "base": C["base"], "reguas": C["reguas"], "espuma": C["espuma"], "teclas": C["teclas"]}
    parts = [(pv.read(os.path.join(OUT, "f2_28_cutx_%s.stl" % k)), cols[k]) for k in pieces]
    scene(parts, os.path.join(REN, "f2_28_corte_x.png"), [(x0 + 420.0, -50.0, 8.0), (x0, -50.0, 8.0), (0, 0, 1)], size=(1800, 700),
          parallel=True, scale=30.0)
    parts = [(pv.read(os.path.join(OUT, "f2_28_cuty_%s.stl" % k)), cols[k]) for k in pieces]
    scene(parts, os.path.join(REN, "f2_28_corte_y.png"), [(L / 2 + 20, -ycut - 420.0, 8.0), (L / 2 + 20, -ycut, 8.0), (0, 0, 1)], size=(2000, 600),
          parallel=True, scale=42.0)
    # 5. plan of the tray with the rulers
    parts = [(load(n, "base"), C["base"]), (load(n, "reguas"), C["reguas"])]
    scene(parts, os.path.join(REN, "f2_28_planta_base.png"), [(L / 2, -50.0, 600.0), (L / 2, -50.0, 0.0), (0, 1, 0)], size=(2000, 840),
          parallel=True, scale=58.0)
    # 6. the four sizes, plan view of the lids stacked
    pl = pv.Plotter(off_screen=True, window_size=(2000, 1500))
    pl.set_background("white")
    for k, nn in enumerate((28, 44, 60, 76)):
        m = load(nn, "tampa", dy=-130.0 * k)
        pl.add_mesh(m, color=C["tampa"], show_edges=False)
    pl.enable_parallel_projection()
    pl.camera_position = [(237.0, -250.0, 900.0), (237.0, -250.0, 0.0), (0, 1, 0)]
    pl.camera.parallel_scale = 290.0
    pl.screenshot(os.path.join(REN, "f2_tamanhos.png"))
    pl.close()
    # 7. 76 keys, closed
    parts = [(load(76, "tampa"), C["tampa"]), (load(76, "base"), C["base"]), (load(76, "teclas"), C["teclas"])]
    scene(parts, os.path.join(REN, "f2_76_iso.png"), [(120.0, -520.0, 250.0), (237.0, -50.0, 8.0), (0, 0, 1)], zoom=1.45)


if __name__ == "__main__":
    main()
