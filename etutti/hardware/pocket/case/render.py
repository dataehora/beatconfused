"""PNG renders of the Pocket's Seixo case (PyVista, offscreen):

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/pocket/case/render.py

reads the STLs case.py wrote into out/ (and writes out/switches.stl, the
stand-in switches) and writes renders/seixo_{iso,top,left,back,below}.png:
the case with the plate, switches and button caps (the eTuttino's caps,
keycap.py: white naturals, black sharps, C and F with the diagonal chequer),
the knobs, the LED, the speaker behind the grille.
"""
import os
import sys

import cadquery as cq
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "case")))
import keycap as K  # noqa: E402

OUT, RENDERS = C.OUT, os.path.join(HERE, "renders")
ETT_OUT = os.path.normpath(os.path.join(HERE, "..", "..", "case", "out"))
CASE, NATURAL, SHARP = "#d9d4cb", "#f4f2ee", "#1d1d1f"
SWITCH, PLATE, LED, KNOB, METAL = "#26282c", "#111214", "#7fe08f", "#d9d4cb", "#8c8c8c"
BG = "#f3f1ec"
F = lambda y: C.WIDTH - y     # SPEC y -> file y


def mesh(name, folder=OUT):
    return pv.read(os.path.join(folder, name + ".stl"))


def switches():
    path = os.path.join(OUT, "switches.stl")
    sw = C.to_file(cq.Compound.makeCompound([K.switch(x, y) for _, _, x, y, _ in C.keys()]))
    cq.exporters.export(cq.Workplane().add(sw), path, tolerance=0.05)
    return pv.read(path)


def scene(pl, sw, with_bottom=True, knobs=True):
    pl.add_mesh(mesh("seixo_tampa"), color=CASE, specular=0.25, specular_power=12)
    if with_bottom:
        pl.add_mesh(mesh("seixo_fundo"), color="#cfc9be")
        pl.add_mesh(mesh("seixo_tampa_bateria"), color="#cfc9be")
    pl.add_mesh(mesh("plate"), color=PLATE)
    pl.add_mesh(sw, color=SWITCH)
    caps = {kind: mesh("keycap_" + kind, ETT_OUT) for kind in ("natural", "sharp", "cf")}
    for _, _, x, y, kind in C.keys():
        cap = caps[kind].copy().translate((x, F(y), 0.0))
        pl.add_mesh(cap, color=SHARP if kind == "sharp" else NATURAL, specular=0.3, specular_power=30)
    for x, y in ((C.VOLUME_XY, C.SELECT_XY) if knobs else ()):
        z = C.z_interface(y)
        pl.add_mesh(pv.Cylinder(center=(x, F(y), z + C.KNOB_LIFT + C.KNOB_H / 2), direction=(0, 0, 1), radius=C.KNOB_D / 2,
                                height=C.KNOB_H, resolution=64), color="#2b2a28", specular=0.4)
    lx, ly = C.LED_XY
    pl.add_mesh(pv.Disc(center=(lx, F(ly), C.z_interface(ly) - 0.3), inner=0, outer=1.6, normal=(0, 0, 1)), color=LED)
    # the speaker's cone seen through the grille
    sx, sy = C.SPK_C
    zf = C.speaker_face_z(sy) - 0.6
    pl.add_mesh(pv.Disc(center=(sx, F(sy), zf), inner=0, outer=C.SPK_CONE_D / 2,
                        normal=(0, -0.225, 0.974)), color="#3a3633")


def shoot(view, path, sw):
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1000))
    pl.set_background(BG)
    scene(pl, sw, knobs=(view != "recessos"))
    if view == "recessos":
        vx, vy = C.VOLUME_XY
        pl.add_mesh(pv.Cylinder(center=(vx, F(vy), C.Z_IF - C.POT_NUT_T / 2), direction=(0, 0, 1), radius=C.POT_NUT_AF / 2 / 0.866,
                                height=C.POT_NUT_T, resolution=6), color=METAL)
        pl.add_mesh(pv.Cylinder(center=(vx, F(vy), C.Z_IF + 2.2), direction=(0, 0, 1), radius=3.5, height=4.5, resolution=32), color=METAL)
    pl.enable_anti_aliasing("ssaa")
    c = (C.length() / 2, 50.0, 15.0)
    if view == "iso":
        pl.camera_position = [(-40.0, -170.0, 170.0), (c[0] - 10, 45, 8), (0, 0, 1)]
        pl.camera.view_angle = 27
    elif view == "iface":
        pl.camera_position = [(-70.0, -95.0, 120.0), (40.0, 45.0, 22.0), (0, 0, 1)]
        pl.camera.view_angle = 30
    elif view == "top":
        pl.camera_position = [(c[0], 50.0, 700.0), (c[0], 50.0, 0), (0, 1, 0)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 70
    elif view == "left":      # the back-left face with the micro-USB and the jack
        pl.camera_position = [(-170.0, 210.0, 60.0), (20.0, 75.0, 18.0), (0, 0, 1)]
        pl.camera.view_angle = 30
    elif view == "recessos":  # the lid without knobs: the two recesses, the pot nut, the Teensy pinhole
        pl.camera_position = [(10.0, -40.0, 120.0), (40.0, 72.0, 30.0), (0, 0, 1)]
        pl.camera.view_angle = 26
    elif view == "below":
        pl.camera_position = [(c[0], 50.0, -700.0), (c[0], 50.0, 0), (0, 1, 0)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 70
    pl.add_light(pv.Light(position=(-200, -300, 400), focal_point=c, intensity=0.35))
    pl.screenshot(path)
    pl.close()
    print(path)


def main():
    os.makedirs(RENDERS, exist_ok=True)
    sw = switches()
    for view in ("iso", "iface", "top", "left", "below", "recessos"):
        shoot(view, os.path.join(RENDERS, "seixo_%s.png" % view), sw)


if __name__ == "__main__":
    main()
