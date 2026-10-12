"""The eTuttino case: a 3D-printable two-piece enclosure, built from the
same geometry as the board (generate.py) and the support points
mechanics.py picked (build/etuttino_supports.json).

Run with FreeCAD's Python (build_pcb.py does it after routing):

    "C:/Program Files/FreeCAD 1.0/bin/python.exe" case.py

Writes fab/etuttino_case_top.step/.stl and fab/etuttino_case_bottom.step/.stl
(mm; the STLs are what a 3D-printing service wants, the STEP files open in
any CAD program for changes).

  bottom tray   floor + low walls. A boss under every mounting hole (with
                a pocket for the plate-standoff screw head, or a through
                hole for the screws that hold the top), a pillar wherever
                mechanics.py found a clear spot on the back of the board,
                recesses for four stick-on rubber feet.
  top shell     walls + a 3 mm deck at plate level. The deck has one
                stepped opening following the four staggered key rows (it
                rests on the plate's edge and clamps the plate + board
                sandwich down onto the tray), a hole for the power LED in
                the front-left corner, and in the back-left corner a pod
                over the Teensy + Audio Board with the USB and headphone
                openings in its left side. Nothing in the case touches the
                stack: the board and the Teensy + Audio Board are joined
                only by the Audio Board's 28 header legs.

The two halves are held together by eight M2 self-tapping screws from
below, through the tray's walls into the top shell's walls; two more go up
through the board's two left holes into posts under the deck.

Coordinates: board millimetres (x right, y towards the player), z up from
the board's top surface. FreeCAD's y points the other way, so every point
goes in as (x, -y, z).
"""
import json
import os
import sys

import FreeCAD as App
import MeshPart
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate as G  # noqa: E402

FAB = os.path.join(HERE, "fab")

CL = 0.5                 # board edge to the inside of the wall
WALL = 5.0
R_OUT = 3.0              # outer corner radius
UNDER = 4.5              # under the board: parts (SOIC 2.65 mm) and trimmed legs
FLOOR = 2.0
Z_SPLIT = -G.PCB_THICKNESS            # tray top = board underside
Z_FLOOR_TOP = Z_SPLIT - UNDER
Z_FLOOR = Z_FLOOR_TOP - FLOOR
DECK = (5.0, 8.0)        # deck: rests on the plate (top at 5 mm above the board)
CAP_GAP = 0.6            # deck opening beyond each key's 19.05 mm cell
LID_Z = 6.0              # deck underside over the Audio Board (its parts are ~1 mm tall)
POD_TOP = 25.5           # Teensy top 17.2 mm, USB 19.8, header pins + solder ~19
POD_ROOF = 2.0
POD_X1 = G.key_left_edge(2) + 0.5 * G.U - 8.6 - 1.0   # pod's right face: 1 mm short of row 3's first keycap
SCREW_PILOT = 0.85       # M2 self-tapping pilot hole radius
SCREW_CLEAR = 1.2        # M2 clearance radius
HEAD_R, HEAD_DEPTH = 2.3, 2.0   # M2 pan-head counterbore
FOOT_R, FOOT_DEPTH, FOOT_INSET = 5.4, 0.6, 14.0   # 10 mm rubber feet

# where the stack's openings are (see assembly3d.py for the same numbers)
AUDIO_TOP = 3.0 + 1.6
JACK_Y = G.STACK_CY + 7.62 + 7.2
JACK_Z = AUDIO_TOP + 2.5
USB_Z = 18.5
POD_Y1 = G.STACK_CY + 8.89 + 0.6 + 1.5      # pod's front face over the Teensy (+ 0.6 clear, 1.5 wall)
JACK_X1, JACK_Y1 = G.STACK_ZONE[0] + 13.0 + 1.5 + 1.5, JACK_Y + 3.0 + 1.2 + 1.4   # extension over the jack


def P(x, y, z):
    return App.Vector(x, -y, z)


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, P(x0, y1, z0))


def cyl(x, y, z0, z1, r):
    return Part.makeCylinder(r, z1 - z0, P(x, y, z0))


def rbox(x0, y0, z0, x1, y1, z1, r):
    b = box(x0, y0, z0, x1, y1, z1)
    vertical = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return b.makeFillet(r, vertical)


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out


OX0, OY0 = -CL - WALL, -CL - WALL
OX1, OY1 = G.PCB_W + CL + WALL, G.PCB_H + CL + WALL
IX0, IY0, IX1, IY1 = -CL, -CL, G.PCB_W + CL, G.PCB_H + CL


def wall_screws():
    m = CL + WALL / 2
    W, H = G.PCB_W, G.PCB_H
    return [(-m, 10.0), (-m, H - 10.0), (W + m, 10.0), (W + m, H - 10.0),
            (W * 0.3, -m), (W * 0.7, -m), (W * 0.3, H + m), (W * 0.7, H + m)]


def bottom_tray(sup):
    tray = rbox(OX0, OY0, Z_FLOOR, OX1, OY1, Z_SPLIT, R_OUT)
    tray = tray.cut(box(IX0, IY0, Z_FLOOR_TOP, IX1, IY1, Z_SPLIT + 1))
    adds, cuts = [], []
    for x, y, kind in sup["bosses"]:
        adds.append(cyl(x, y, Z_FLOOR_TOP - 0.01, Z_SPLIT, 3.0))
        if kind == "plate":
            # the screw under the board into the plate standoff: head pocket
            cuts.append(cyl(x, y, Z_SPLIT - HEAD_DEPTH, Z_SPLIT + 1, HEAD_R))
        else:
            # a screw from below, through the board, into the top shell
            cuts.append(cyl(x, y, Z_FLOOR - 1, Z_SPLIT + 1, SCREW_CLEAR))
            cuts.append(cyl(x, y, Z_FLOOR - 1, Z_FLOOR + HEAD_DEPTH, HEAD_R))
    r = sup["pillar_d"] / 2
    for x, y in sup["pillars"]:
        adds.append(cyl(x, y, Z_FLOOR_TOP - 0.01, Z_SPLIT, r))
    for x, y in wall_screws():
        cuts.append(cyl(x, y, Z_FLOOR - 1, Z_SPLIT + 1, SCREW_CLEAR))
        cuts.append(cyl(x, y, Z_FLOOR - 1, Z_FLOOR + HEAD_DEPTH, HEAD_R))
    for fx in (OX0 + FOOT_INSET, OX1 - FOOT_INSET):
        for fy in (OY0 + FOOT_INSET, OY1 - FOOT_INSET):
            cuts.append(cyl(fx, fy, Z_FLOOR - 1, Z_FLOOR + FOOT_DEPTH, FOOT_R))
    tray = tray.fuse(union(adds)).cut(union(cuts))
    return tray.removeSplitter()


def key_opening():
    rects = []
    for r in range(len(G.ROWS)):
        y0 = G.GRID_Y0 + G.row_slot(r) * G.U
        rects.append(box(G.key_left_edge(r) - CAP_GAP, y0 - CAP_GAP, DECK[0] - 1,
                         G.key_right_edge(r) + CAP_GAP, y0 + G.U + CAP_GAP, DECK[1] + 1))
    return union(rects)


def top_shell(sup):
    shell = rbox(OX0, OY0, Z_SPLIT, OX1, OY1, DECK[1], R_OUT)
    shell = shell.cut(box(IX0, IY0, Z_SPLIT - 1, IX1, IY1, DECK[0]))
    # the pod over the Teensy + Audio Board (kept inside the rounded outline)
    pod = union([box(OX0, OY0, DECK[1] - 0.01, POD_X1, POD_Y1, POD_TOP),
                 box(OX0, OY0, DECK[1] - 0.01, JACK_X1, JACK_Y1, POD_TOP)])
    pod = pod.common(rbox(OX0, OY0, DECK[1] - 1, OX1, OY1, POD_TOP + 1, R_OUT))
    shell = shell.fuse(pod)
    # posts under the deck at the board's two left holes
    posts = [cyl(x, y, 0.0, DECK[0] + 0.01, 2.6) for x, y, kind in sup["bosses"] if kind == "pcb"]
    shell = shell.fuse(union(posts))

    zx0, zy0, zx1, zy1 = G.STACK_ZONE
    cuts = [key_opening(),
            # room over the Audio Board under the deck
            box(zx0 - 0.5, zy0 - 0.5, DECK[0] - 1, zx1 + 0.5, zy1 + 0.5, LID_Z),
            # pod cavity: Teensy + headers, and the jack
            box(IX0, IY0, DECK[0] - 1, POD_X1 - 1.4, POD_Y1 - 1.5, POD_TOP - POD_ROOF),
            box(IX0, IY0, DECK[0] - 1, JACK_X1 - 1.5, JACK_Y1 - 1.4, POD_TOP - POD_ROOF),
            # USB plug (overmould ~11 x 7.5 mm) and headphone plug openings, left side
            box(OX0 - 1, G.STACK_CY - 6.5, USB_Z - 4.5, IX0 + 0.01, G.STACK_CY + 6.5, USB_Z + 4.5),
            Part.makeCylinder(3.6, WALL + 2, P(OX0 - 1, JACK_Y, JACK_Z), App.Vector(1, 0, 0)),
            # power LED window
            cyl(G.LED["x"], G.LED["y"], DECK[0] - 1, DECK[1] + 1, 1.75)]
    for x, y, kind in sup["bosses"]:
        if kind == "plate":
            # head of the plate-standoff screw on top of the plate
            cuts.append(cyl(x, y, DECK[0] - 0.01, DECK[0] + HEAD_DEPTH, HEAD_R))
        else:
            cuts.append(cyl(x, y, -0.01, DECK[0] - 0.5, SCREW_PILOT))
    for x, y in wall_screws():
        cuts.append(cyl(x, y, Z_SPLIT - 0.01, Z_SPLIT + 7.0, SCREW_PILOT))
    shell = shell.cut(union(cuts))
    return shell.removeSplitter()


def export(shape, name):
    assert shape.isValid(), name
    step = os.path.join(FAB, name + ".step")
    stl = os.path.join(FAB, name + ".stl")
    shape.exportStep(step)
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.35)
    mesh.write(stl)
    bb = shape.BoundBox
    print("%s: %.1f x %.1f x %.1f mm, %.0f cm3, %d triangles" % (
        name, bb.XLength, bb.YLength, bb.ZLength, shape.Volume / 1000, mesh.CountFacets))


def main():
    with open(os.path.join(G.BUILD, "etuttino_supports.json"), encoding="utf-8") as f:
        sup = json.load(f)
    os.makedirs(FAB, exist_ok=True)
    export(bottom_tray(sup), "etuttino_case_bottom")
    export(top_shell(sup), "etuttino_case_top")


if __name__ == "__main__":
    main()
