"""PNG renders of the case (SPEC 10.4), offscreen with PyVista:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe render.py

reads the STLs case.py / keycap.py wrote into out/ and writes
renders/<version>_{iso,top,left}.png for "seixo" and "madeira": the case
with the plate, dark switches and the button caps (white/black for Seixo,
mother-of-pearl/ebony for Madeira), knobs, LED and the connector insert.
"""
import os
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402

OUT, RENDERS = C.OUT, os.path.join(HERE, "renders")

LOOK = {
    "seixo": {"body": "seixo_tampa", "bottom": "seixo_fundo", "case": "#d9d4cb", "rough": 0.55,
              "natural": "#f4f2ee", "sharp": "#1d1d1f", "cf": "#f4f2ee", "knob": "#d9d4cb"},
    "madeira": {"body": "madeira_corpo", "bottom": "madeira_fundo", "case": "#c49a63", "rough": 0.7,
                "natural": "#efe9df", "sharp": "#211b17", "cf": "#efe9df", "knob": "#3a2a1e"},
}
SWITCH, PLATE, INSERT, LED = "#26282c", "#111214", "#0d0d0e", "#7fe08f"
BG = "#f3f1ec"


def mesh(name):
    return pv.read(os.path.join(OUT, name + ".stl"))


def wood(m):
    """Oak-ish: a grain of stripes along x on the vertex colours."""
    x, y, z = m.points.T
    g = 0.5 + 0.5 * np.sin(x * 0.9 + 2.5 * np.sin(y * 0.21 + x * 0.013) + z * 0.4)
    g = g ** 3
    base = np.array([196, 154, 99]) / 255
    dark = np.array([150, 108, 64]) / 255
    m["rgb"] = (base * (1 - 0.35 * g[:, None]) + dark * 0.35 * g[:, None]).clip(0, 1)
    return m


def scene(version, pl):
    look = LOOK[version]
    body = mesh(look["body"])
    if version == "madeira":
        pl.add_mesh(wood(body), scalars="rgb", rgb=True, smooth_shading=False, specular=0.15)
    else:
        pl.add_mesh(body, color=look["case"], specular=0.25, specular_power=12)
    pl.add_mesh(mesh("plate"), color=PLATE)
    pl.add_mesh(mesh("insert"), color=INSERT)
    sw = pv.read(os.path.join(OUT, "switches.stl"))
    pl.add_mesh(sw, color=SWITCH)
    caps = {kind: pv.read(os.path.join(OUT, "keycap_%s.stl" % kind)) for kind in ("natural", "sharp", "cf")}
    F = lambda y: C.WIDTH - y      # SPEC y -> file y (case.py mirrors on export)
    for n, row, x, y, kind in C.keys():
        cap = caps[kind].copy().translate((x, F(y), C.Z_KEY_TOP - caps[kind].bounds[5]))
        pl.add_mesh(cap, color=look[kind], specular=0.5 if version == "madeira" else 0.3,
                    specular_power=30)
    for x, y in (C.VOLUME_XY, C.SELECT_XY):
        z = C.z_interface(y)
        pl.add_mesh(pv.Cylinder(center=(x, F(y), z + 3.6), direction=(0, 0, 1), radius=4.5, height=6.4,
                                resolution=48), color=look["knob"], specular=0.3)
    lx, ly = C.LED_XY
    if True:      # Seixo: the LED in its hole; Madeira: lit through the acrylic window
        pl.add_mesh(pv.Disc(center=(lx, F(ly), C.z_interface(ly) + 0.02), inner=0, outer=1.7, normal=(0, -0.05, 1)),
                    color=LED)


def shoot(version, view, path):
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1000) if view != "left" else (1400, 900))
    pl.set_background(BG)
    scene(version, pl)
    pl.enable_anti_aliasing("ssaa")
    c = (168.0, 50.0, 15.0)
    if view == "iso":
        pl.camera_position = [(-95.0, -230.0, 230.0), c, (0, 0, 1)]
        pl.camera.view_angle = 30
    elif view == "top":
        pl.camera_position = [(c[0], c[1], 700.0), (c[0], c[1], 0), (0, 1, 0)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 105
    else:   # the left face, looking along +x
        pl.camera_position = [(-400.0, 50.0, 18.0), (0, 50.0, 18.0), (0, 0, 1)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 40
    pl.add_light(pv.Light(position=(-200, -300, 400), focal_point=c, intensity=0.35))
    pl.screenshot(path)
    pl.close()
    print(path)


def main():
    os.makedirs(RENDERS, exist_ok=True)
    for version in LOOK:
        for view in ("iso", "top", "left"):
            shoot(version, view, os.path.join(RENDERS, "%s_%s.png" % (version, view)))


if __name__ == "__main__":
    main()
