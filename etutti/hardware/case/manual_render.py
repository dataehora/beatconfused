"""Pictures for the assembly manual (etutti/manuais/), board v0.7 in the
SPEC v9 case:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe manual_render.py

Sources: the two KiCad boards (exported to STL here with kicad-cli, the
bare board and its parts separately), the case and caps in out/
(case.py, keycap.py), and the stack, controls-board and panel-part
solids fit_check.py checks. Writes etutti/manuais/img/<name>.jpg plus
a -sm copy of each:

  parts        everything, exploded
  keycap_test  the 4-cap test print
  board_top / board_bottom   the main board (KiCad's own renders in fab/)
  stack        the Teensy + Audio Board on the main board, from the front
  switches     plate and switches on the board
  controls     the controls board over the main board, cable to J3
  panel        the left end: insert, panel USB and jack, short cables
  closing      the board in the bottom shell, the two M2 screws from below
  section      the finished Seixo cut front to back at x = 30: stack,
               controls board, knobs and an M2 screw
"""
import os
import subprocess
import sys
import tempfile

import cadquery as cq
import numpy as np
import pyvista as pv
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import fit_check as FC  # noqa: E402
import render as R  # noqa: E402
from models_render import crop_bg  # noqa: E402

HW = os.path.normpath(os.path.join(HERE, ".."))
IMG = os.path.normpath(os.path.join(HERE, "..", "..", "manuais", "img"))
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
TMP = tempfile.mkdtemp()
V = C.VERSIONS["seixo"]
F = lambda y: C.WIDTH - y      # SPEC y -> file y

COL = {"pcb": "#1d6b3a", "parts": "#2a2a2a", "audio": "#14532d", "teensy": "#3cb371", "pins": "#c9a227",
       "usb": "#c0c0c0", "plug": "#3a3a3a", "cable": "#1b1b1b", "knob": "#d9d4cb", "metal": "#b8b8b8",
       "led": "#7fe08f", "jst": "#f2efe6", "panel": "#909090"}


def kicad_stl(board, flag, name):
    path = os.path.join(TMP, name + ".stl")
    subprocess.run([KICAD_CLI, "pcb", "export", "stl", "-f", "--user-origin", "0x0mm", flag, "-o", path,
                    os.path.join(HW, "kicad", board + ".kicad_pcb")], check=True, capture_output=True)
    return pv.read(path)


def place_kicad(m, z_bottom):
    """kicad-cli's frame (x, -y_spec, z from the board's underside) -> the files'."""
    m = m.copy()
    m.points[:, 1] = C.WIDTH + m.points[:, 1]
    m.points[:, 2] = m.points[:, 2] + z_bottom
    return m


def cq_mesh(shape, name):
    p = os.path.join(TMP, name + ".stl")
    cq.exporters.export(cq.Workplane().add(C.to_file(shape)), p, tolerance=0.05)
    return pv.read(p)


def tube(points_spec, r=1.6):
    pts = np.array([(x, F(y), z) for x, y, z in points_spec], dtype=float)
    spline = pv.Spline(pts, 60)
    return spline.tube(radius=r, n_sides=16)


# ------------------------------------------------------------- the parts
def build():
    """Every part as (key, mesh, colour) in the files' frame, assembled."""
    P = {}
    main_board = kicad_stl("etuttino", "--board-only", "main_board")
    main_parts = kicad_stl("etuttino", "--no-board-body", "main_parts")
    P["board"] = [(place_kicad(main_board, C.Z_PCB_BOT), COL["pcb"]),
                  (place_kicad(main_parts, C.Z_PCB_BOT), COL["parts"])]
    # Teensy + Audio Board: fit_check's mounted (13 mm) stack, plus the
    # header legs down through the main board
    st, info = FC.stack("M")
    stack = []
    for name, col, s in st:
        if "plugue" in name:
            continue
        c = {"audio": COL["audio"], "stack": "#222222", "teensy": COL["teensy"], "usb": COL["usb"]}[col]
        stack.append((cq_mesh(s, "st_" + str(len(stack))), c))
    cx, cy = info["cx"], info["cy"]
    for ry in (cy - 7.62, cy + 7.62):
        for i in range(14):
            x = cx - 6.5 * 2.54 + i * 2.54
            stack.append((pv.Cylinder(center=(x, F(ry), C.Z_PCB_BOT + 1.4), direction=(0, 0, 1), radius=0.33,
                                      height=info["teensy_top"] - C.Z_PCB_BOT + 1.0, resolution=10), COL["pins"]))
    P["stack"] = stack
    P["stack_info"] = info
    # plate + switches + caps (the STLs are in the files' frame already)
    P["plate"] = [(R.mesh("plate"), R.PLATE)]
    P["switches"] = [(pv.read(os.path.join(C.OUT, "switches.stl")), R.SWITCH)]
    caps = {k: pv.read(os.path.join(C.OUT, "keycap_%s.stl" % k)) for k in ("natural", "sharp", "cf")}
    look = R.LOOK["seixo"]
    P["caps"] = [(caps[kind].copy().translate((x, F(y), C.Z_KEY_TOP - caps[kind].bounds[5])), look[kind])
                 for n, row, x, y, kind in C.keys()]
    # controls board: the real outline from KiCad, the bodies from fit_check
    ctop = C.controls_top(V)
    t = C.CONTROLS["thickness"]
    cb = kicad_stl("etuttino_controls", "--board-only", "controls_board")
    ctrl = [(place_kicad(cb, ctop - t), COL["pcb"])]
    for name, col, s in FC.interface_board(V)[0]:
        if name.startswith("plaquinha") or "M2" in name:
            continue
        c = {"knobpart": COL["metal"], "panel": COL["jst"], "plug": COL["jst"], "led": COL["led"]}[col]
        ctrl.append((cq_mesh(s, "ct_" + str(len(ctrl))), c))
    knobs = []
    for x, y in (C.VOLUME_XY, C.SELECT_XY):
        z = C.z_interface(y)
        ctrl.append((pv.Cylinder(center=(x, F(y), (ctop + 6.5 + z + 3) / 2), direction=(0, 0, 1), radius=3.0,
                                 height=z + 3 - ctop - 6.5, resolution=24), COL["metal"]))
        knobs.append((pv.Cylinder(center=(x, F(y), z + 3.6), direction=(0, 0, 1), radius=4.5, height=6.4,
                                  resolution=48), look["knob"]))
    P["controls"] = ctrl
    P["knobs"] = knobs
    # the 8-way cable from the controls board's JST (facing down) to J3
    jx, jy = C.CONTROLS["jst"]
    j3 = FC_J3()
    P["cable"] = [(tube([(jx, jy, ctop - t - 10.0), (jx, jy + 2, ctop - t - 13.0),
                         (j3[0], j3[1] + 2, C.Z_PCB_TOP + 12.0), (j3[0], j3[1], C.Z_PCB_TOP + 8.0)], r=1.4),
                   "#c0392b")]
    # panel parts and the two short cables to the Teensy and the Audio Board
    panel = [(cq_mesh(s, "pn_" + str(i)), COL["panel"]) for i, (name, col, s) in enumerate(FC.panel_parts(V))]
    panel.append((R.mesh("insert"), R.INSERT))
    usb_y, usb_z = C.USB_YZ
    jack_y, jack_z = C.JACK_YZ
    tx = info["x"][0] - 1.0
    panel.append((tube([(14.0, usb_y, usb_z), (17.0, usb_y, usb_z - 1), (tx - 4, cy, info["usb_z"] + 2),
                        (tx, cy, info["usb_z"])], r=1.7), COL["cable"]))
    panel.append((tube([(14.0, jack_y, jack_z), (18.0, jack_y, jack_z - 2), (24.0, info["y"][1] - 4, info["usb_top"] - 6),
                        (28.0, info["y"][1] - 6, C.Z_PCB_TOP + 4.5)], r=1.2), COL["cable"]))
    P["panel"] = panel
    # case
    P["lid"] = [(R.mesh("seixo_tampa"), look["case"])]
    P["bottom"] = [(R.mesh("seixo_fundo"), look["case"])]
    # the board's two M2 screws: head under the bottom plate, nut on top
    scr = []
    for x, y in C.SCREW_PILLARS:
        scr.append((pv.Cylinder(center=(x, F(y), (C.Z_PCB_TOP + 3.0) / 2 + 0.3), direction=(0, 0, 1), radius=1.0,
                                height=C.Z_PCB_TOP + 2.4, resolution=16), COL["metal"]))
        scr.append((pv.Cylinder(center=(x, F(y), 0.9), direction=(0, 0, 1), radius=2.0, height=1.4, resolution=24),
                    COL["metal"]))
        scr.append((pv.Cylinder(center=(x, F(y), C.Z_PCB_TOP + 0.8), direction=(0, 0, 1), radius=2.3, height=1.6,
                                resolution=6), COL["metal"]))
    P["screws"] = scr
    return P


def FC_J3():
    """J3's place on the main board, from the KiCad file (SPEC x, y)."""
    import re
    s = open(os.path.join(HW, "kicad", "etuttino.kicad_pcb"), encoding="utf-8").read()
    i = s.index('"Reference" "J3"')
    head = s.rfind("(footprint", 0, i)
    m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", s[head:i])
    return float(m.group(1)), float(m.group(2))


# ------------------------------------------------------------- shooting
def shoot(name, items, cam, size=(1800, 1100), parallel=None, clip=None, sm=900):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background(R.BG)
    for m, col in items:
        if clip is not None:
            m = cut(m, clip)
            if m is None:
                continue
        pl.add_mesh(m, color=col, specular=0.25, specular_power=15)
    pl.enable_anti_aliasing("ssaa")
    pl.camera_position = cam
    if parallel:
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = parallel
    else:
        pl.camera.view_angle = 30
    pl.add_light(pv.Light(position=(-200, -300, 400), focal_point=cam[1], intensity=0.35))
    raw = os.path.join(TMP, name + ".png")
    pl.screenshot(raw)
    pl.close()
    save(Image.open(raw), name, sm)


def cut(m, clip):
    """Keeps the part of m beyond the plane, capped where the mesh is closed
    (so the cut faces show solid), else just clipped open."""
    normal, origin = clip
    x0 = origin[0]
    m = m.extract_surface().triangulate().clean()
    if m.bounds[1] <= x0:
        return None
    if m.bounds[0] >= x0:
        return m
    for n in (normal, tuple(-v for v in normal)):
        try:
            c = m.clip_closed_surface(normal=n, origin=origin)
        except Exception:
            break
        if c.n_points and c.bounds[0] >= x0 - 0.01:
            return c
    c = m.clip(normal=normal, origin=origin, invert=False)
    return c if c.n_points else None


def save(im, name, sm=900):
    im = crop_bg(im).convert("RGB")
    im.save(os.path.join(IMG, name + ".jpg"), quality=86, optimize=True)
    h = round(im.height * sm / im.width)
    im.resize((sm, h), Image.LANCZOS).save(os.path.join(IMG, name + "-sm.jpg"), quality=82, optimize=True)
    print(name)


def lift(items, dz):
    return [(m.copy().translate((0, 0, dz)), c) for m, c in items]


def main():
    os.makedirs(IMG, exist_ok=True)
    P = build()
    iso = [(-120.0, -260.0, 260.0), (165.0, 50.0, 10.0), (0, 0, 1)]
    left_iso = [(-90.0, -110.0, 120.0), (45.0, 50.0, 14.0), (0, 0, 1)]

    # everything, exploded
    shoot("parts", P["bottom"] + lift(P["screws"], -12) + lift(P["board"] + P["stack"], 14)
          + lift(P["switches"] + P["plate"], 32) + lift(P["caps"], 56) + lift(P["controls"] + P["knobs"], 40)
          + lift(P["lid"], 105) + lift(P["panel"], 14),
          [(-160.0, -330.0, 330.0), (165.0, 50.0, 45.0), (0, 0, 1)], size=(1800, 1300))

    # the keycap test print
    test = pv.read(os.path.join(C.OUT, "keycap_test_4.stl"))
    b = test.bounds
    c = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    shoot("keycap_test", [(test, "#f4f2ee")], [(c[0] - 40, c[1] - 120, c[2] + 90), c, (0, 0, 1)], size=(1400, 900))

    # the main board, KiCad's own renders
    for side in ("top", "bottom"):
        save(Image.open(os.path.join(HW, "fab", "etuttino_%s.png" % side)), "board_" + side, 1100)

    # the stack, from the front-left, low
    shoot("stack", P["board"] + P["stack"],
          [(-20.0, 30.0, 40.0), (40.0, 75.0, 12.0), (0, 0, 1)], size=(1600, 1100))

    # plate and switches
    shoot("switches", P["board"] + P["stack"] + P["plate"] + P["switches"], iso)

    # the controls board over the main board, the cable to J3
    shoot("controls", P["board"] + P["stack"] + P["controls"] + P["cable"] + P["plate"] + P["switches"],
          left_iso, size=(1600, 1100))

    # the left end: panel parts and cables
    shoot("panel", P["board"] + P["stack"] + P["panel"] + P["controls"] + P["cable"] + P["bottom"],
          [(-70.0, -60.0, 90.0), (25.0, 50.0, 14.0), (0, 0, 1)], size=(1600, 1100))

    # the board in the bottom shell, screws from below
    shoot("closing", P["bottom"] + P["board"] + P["stack"] + P["screws"] + P["plate"] + P["switches"] + P["panel"]
          + P["controls"] + P["cable"], iso)

    # the finished case, cut front to back at x = 30 (through the stack, the
    # controls board, the volume knob's neighbour and the screw at (30; 60))
    allp = (P["bottom"] + P["lid"] + P["board"] + P["stack"] + P["screws"] + P["controls"] + P["knobs"]
            + P["panel"] + P["cable"] + P["plate"] + P["switches"])
    shoot("section", allp, [(-300.0, 50.0, 18.0), (30.0, 50.0, 18.0), (0, 0, 1)], size=(1800, 800),
          parallel=26, clip=((1, 0, 0), (30.0, 0, 0)))

    # the finished instrument
    save(Image.open(os.path.join(HERE, "renders", "seixo_iso.png")), "finished", 1100)


if __name__ == "__main__":
    main()
