"""Pictures of the eTutti concept models for /etutti/models/ (run with
KiCad's Python):

    "C:/Program Files/KiCad/10.0/bin/python.exe" concepts_render.py

Runs concepts.py (the top-view diagrams) and concepts_cad.py in FreeCAD
(the 3D models), turns each model's STLs into one VRML scene and renders it
with kicad-cli, the same raytracer and page colour as the manuals'
pictures: etutti/models/img/<model>_{iso,left,top}.jpg (+ "-sm" copies),
and a close-up of the eTuttiChorus grip.

KiCad always draws a board and frames its camera on it, so each scene sits
on a 1 mm dummy board hidden inside the solid case body.
"""
import os
import subprocess
import sys

import pcbnew

import assembly3d as A
import concepts as C

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "concepts_build")
FREECAD_PY = os.environ.get("FREECAD_PYTHON", "C:/Program Files/FreeCAD 1.0/bin/python.exe")
KICAD_CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe" if os.name == "nt" else "kicad-cli")

A.COLORS.update({
    "case": (0.42, 0.07, 0.10),
    "port": (0.03, 0.03, 0.03),
    "led": (0.30, 0.85, 0.40),
    "screen": (0.02, 0.02, 0.03),
    "screen_on": (0.10, 0.22, 0.38),
    "grille": (0.04, 0.04, 0.05),
})
A.IMG_DIR = C.IMG_DIR


def scene(m):
    v = A.Vrml()
    for f in sorted(os.listdir(BUILD)):
        prefix = m.name + "_"
        if not f.startswith(prefix) or not f.endswith(".stl"):
            continue
        color = f[len(prefix):-4]
        if "_" in color and color.split("_")[0] == "chorus":     # etutti_ vs etutti_chorus_
            continue
        v.stl(os.path.join(BUILD, f), color)
    path = os.path.join(BUILD, m.name + ".wrl")
    v.save(path)
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.0))
    i = 10.0
    pts = [(i, i), (m.length - i, i), (m.length - i, m.depth - i), (i, m.depth - i), (i, i)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by)))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        b.Add(s)
    A.add_model(b, path, "SCENE")
    board = os.path.join(BUILD, m.name + ".kicad_pcb")
    pcbnew.SaveBoard(board, b)
    return board


def pivot(m, x, y, z=0.0):
    return "%.2f,%.2f,%.2f" % ((x - m.length / 2) / 10, (m.depth / 2 - y) / 10, z / 10)


SCALE = float(os.environ.get("CONCEPT_SCALE", "1"))    # < 1 for quick previews


def render_png(board, w, h, extra):
    return A.render_png(KICAD_CLI, board, "top", int(w * SCALE), int(h * SCALE), extra)


def render(m):
    board = scene(m)
    made = []
    img = render_png(board, 4800, 3000, ("--perspective", "--rotate", "-52,0,-22", "--zoom", "1.0"))
    made.append(A.save(img, "%s_iso.jpg" % m.name))
    img = render_png(board, 4800, 3000, ("--perspective", "--rotate", "-68,0,58", "--zoom", "1.9",
                                                             "--pivot", pivot(m, 0, m.depth / 2, 10)))
    made.append(A.save(img, "%s_left.jpg" % m.name, pad=60))
    img = render_png(board, 6000, 3000, ("--zoom", "1.7"))
    made.append(A.save(img, "%s_top.jpg" % m.name))
    if m.chorus:
        img = render_png(board, 4800, 3000, ("--perspective", "--rotate", "-40,0,-18", "--zoom", "2.6",
                                                                 "--pivot", pivot(m, C.GRIP_W / 2, m.depth / 2, 18)))
        made.append(A.save(img, "%s_grip.jpg" % m.name, (0, 0, img.width, img.height)))
    return made


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "concepts.py")], check=True)
    r = subprocess.run([FREECAD_PY, os.path.join(HERE, "concepts_cad.py")], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr[-3000:])
        raise SystemExit("concepts_cad.py failed")
    only = sys.argv[1:]
    for m in C.MODELS:
        if only and m.name not in only:
            continue
        for path in render(m):
            print(path)


if __name__ == "__main__":
    main()
