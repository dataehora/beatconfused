"""R3V4: pictures of the T3-G case. Reads out/t3g_28_*.stl, writes renders/t3g_28_iso.png, t3g_28_corte.png (section across row 2, x = key centre)."""
import os
import numpy as np
import pyvista as pv
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); REN = os.path.join(HERE, "renders")
C = {"tampa": "#C9C5BB", "base": "#8F8C85", "reguas": "#2F7D4F", "grades": "#C8A24A", "teclas": "#EDE8DA", "parafusos": "#333333"}
def load(n):
    return pv.read(os.path.join(OUT, "t3g_28_%s.stl" % n))
def shot(parts, path, cam, size=(1800, 900), clip=None, par=None):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("white")
    for n in parts:
        m = load(n)
        if clip is not None:
            m = m.clip(normal=clip[0], origin=clip[1], invert=False)
        pl.add_mesh(m, color=C[n], smooth_shading=False)
    if par:
        pl.enable_parallel_projection(); pl.camera_position = cam; pl.camera.parallel_scale = par
    else:
        pl.camera_position = cam; pl.camera.zoom(1.3)
    pl.screenshot(path); pl.close()
L = 252.0
shot(["tampa", "base", "teclas"], os.path.join(REN, "t3g_28_iso.png"), [(L * .15, -330, 210), (L / 2, -50, 8), (0, 0, 1)])
# exploded: grades lifted
pl = pv.Plotter(off_screen=True, window_size=(1800, 1100)); pl.set_background("white")
for n, dz in (("base", 0), ("reguas", 20), ("grades", 42), ("teclas", 30), ("tampa", 80)):
    pl.add_mesh(load(n).translate((0, 0, dz)), color=C[n])
pl.camera_position = [(L * .1, -380, 330), (L / 2, -50, 50), (0, 0, 1)]; pl.camera.zoom(1.2)
pl.screenshot(os.path.join(REN, "t3g_28_explodido.png")); pl.close()
# section: row 2 (y_spec 58.01 -> file y = -58.01), key at x = 98.45+...: x = 89.2+18.5*3 = 144.7 ; keep x >= 144.7
shot(["tampa", "base", "reguas", "grades", "teclas", "parafusos"], os.path.join(REN, "t3g_28_corte.png"),
     [(60, -58.0, 20), (144.7, -58.0, 6), (0, 0, 1)], size=(1800, 1000), clip=((1, 0, 0), (144.7, 0, 0)), par=75)
