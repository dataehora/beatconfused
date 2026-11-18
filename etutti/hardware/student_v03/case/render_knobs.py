"""Student V3 (SPEC v6 task 2): the two knobs side by side on the lid, isometric. CadQuery venv:
    python etutti/hardware/student_v03/case/render_knobs.py   -> renders/knobs_7_e_10.png"""
import os, sys
import numpy as np
import pyvista as pv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import case as K
pv.OFF_SCREEN = True
pl = pv.Plotter(off_screen=True, window_size=(1800, 900))
pl.set_background("white")
def stl(n): return pv.read(os.path.join(K.OUT, n + ".stl"))
lid = stl("tampa").clip_box([-1, 70, -60, -1, -1, 30], invert=False)     # the left end of the lid, with the two knobs' holes
kx = [k for k in K.G.KNOBS]
pl.add_mesh(lid, color="#e8dcc0", smooth_shading=False)
# a shaft stub + knob at the first knob spot, and the 7 mm knob beside it, so both are seen at once
for (x, y), v, shaft in ((kx[0], "7", 19.5), (kx[1], "10", 24.5)):
    m = stl("knob_%smm" % v)
    pl.add_mesh(m.translate((x, -y, 0)) if False else m.translate((x - 0, -y - 0, 0)), color="#2b2925")
    sh = pv.Cylinder(center=(x, -y, (K.ZT - 3 + shaft) / 2 - 0.0 + 3), direction=(0, 0, 1), radius=3, height=shaft - K.ZT + 3 - 3 + 3)
    pl.add_mesh(sh, color="#aaaaaa")
pl.add_text("knob de 7 mm (eixo de 15 mm, ponta a 19,5) e de 10 mm (EC11E18244AU inteiro, ponta a 24,5)", font_size=10, color="black")
pl.camera_position = [(kx[0][0] + 80, -kx[0][1] - 140, 80), (kx[0][0] + 10, -kx[0][1] + 5, 15), (0, 0, 1)]
pl.screenshot(os.path.join(HERE, "renders", "knobs_7_e_10.png"))
print("ok", kx)
