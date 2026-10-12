"""3D concept models of the eTutti family (run with FreeCAD's Python;
concepts_render.py calls it). Every number comes from concepts.py.

For each model it writes one STL per colour into concepts_build/
(<model>_<colour>.stl): the case body, the plate seen through the key
opening, switch tops, keycaps, the port insides, the LED and, on the
eTuttiChorus, the screen and the speaker behind its grille. These are
appearance models for the pictures, not parts to print: the body is one
solid block.

Coordinates as everywhere: board mm, x right, y towards the player, z up
from the keyboard PCB; FreeCAD's y points the other way, so points go in
as (x, -y, z).
"""
import math
import os
import sys

import FreeCAD as App
import MeshPart
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import concepts as C  # noqa: E402

OUT = os.path.join(HERE, "concepts_build")


def P(x, y, z):
    return App.Vector(x, -y, z)


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, P(x0, y1, z0))


def cyl(x, y, z0, z1, r):
    return Part.makeCylinder(r, z1 - z0, P(x, y, z0))


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out


def body(m):
    """The case as one block: side profile (grip, ramp, keyboard deck)
    with rounded grip edges, cut to a rounded plan outline."""
    L, D = m.length, m.depth
    gx, rx = C.GRIP_W, C.GRIP_W + C.RAMP_W
    prof = [(0, C.FLOOR_Z), (L, C.FLOOR_Z), (L, C.DECK_Z), (rx, C.DECK_Z), (gx, C.GRIP_TOP), (0, C.GRIP_TOP)]
    wire = Part.makePolygon([App.Vector(x, 0, z) for x, z in prof + prof[:1]])
    solid = Part.Face(wire).extrude(App.Vector(0, -D, 0))
    # soften the edges the hand meets (all of them run along y)
    radii = {(0.0, C.FLOOR_Z): 7.0, (0.0, C.GRIP_TOP): 7.0, (gx, C.GRIP_TOP): 5.0,
             (rx, C.DECK_Z): 4.0, (L, C.DECK_Z): 2.0, (L, C.FLOOR_Z): 2.0}
    for (ex, ez), r in radii.items():
        edges = [e for e in solid.Edges
                 if abs(e.Vertexes[0].Point.x - ex) < 1e-6 and abs(e.Vertexes[1].Point.x - ex) < 1e-6
                 and abs(e.Vertexes[0].Point.z - ez) < 1e-6 and abs(e.Vertexes[1].Point.z - ez) < 1e-6]
        if edges:
            solid = solid.makeFillet(r, edges)
    plan = box(0, 0, C.FLOOR_Z - 1, L, D, C.GRIP_TOP + 1)
    vertical = [e for e in plan.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    plan = plan.makeFillet(C.CORNER_R, vertical)
    return solid.common(plan)


def key_parts(m):
    cells = m.row_cells()
    opening = union([box(x0 - C.CAP_GAP, y0 - C.CAP_GAP, C.PLATE_Z - 1.0, x1 + C.CAP_GAP, y1 + C.CAP_GAP, C.GRIP_TOP + 1)
                     for x0, y0, x1, y1 in cells])
    plate = union([box(x0 - C.CAP_GAP, y0 - C.CAP_GAP, C.PLATE_Z - 1.0, x1 + C.CAP_GAP, y1 + C.CAP_GAP, C.PLATE_Z)
                   for x0, y0, x1, y1 in cells])
    switches, light, dark, dots = [], [], [], []
    for k in m.keys():
        x, y = k["cx"], k["cy"]
        switches.append(box(x - 7.4, y - 7.4, C.PLATE_Z, x + 7.4, y + 7.4, C.SWITCH_TOP))
        cap = cyl(x, y, C.KEYCAP_Z[0], C.KEYCAP_Z[1], C.CAP_R)
        cap = cap.makeFillet(1.2, [e for e in cap.Edges if abs(e.Vertexes[0].Point.z - C.KEYCAP_Z[1]) < 1e-6])
        (dark if "♯" in k["name"] else light).append(cap)
        if k["name"][0] == "C" and "♯" not in k["name"]:
            dots.append(cyl(x, y - 5.0, C.KEYCAP_Z[1] - 0.2, C.KEYCAP_Z[1] + 0.15, 0.9))
    return opening, {"plate": [plate], "switch": switches, "cap_light": light, "cap_dark": dark, "cap_c": dots}


def grip_parts(m):
    cuts, parts = [], {"port": [], "metal": [], "led": [], "screen": [], "screen_on": [], "grille": []}
    for name, y, z, w, h in m.ports():
        if name == "jack":
            cuts.append(Part.makeCylinder(w / 2, 7.0, P(-1.0, y, z), App.Vector(1, 0, 0)))
            parts["port"].append(Part.makeCylinder(w / 2, 0.6, P(5.4, y, z), App.Vector(1, 0, 0)))
        else:
            cuts.append(box(-1.0, y - w / 2, z - h / 2, 6.0, y + w / 2, z + h / 2))
            parts["port"].append(box(5.4, y - w / 2, z - h / 2, 6.0, y + w / 2, z + h / 2))
            if name == "usb":     # the Teensy's micro-USB socket at the back of the opening
                parts["metal"].append(box(3.4, y - 3.9, z - 1.4, 5.5, y + 3.9, z + 1.4))
            else:                 # slide switch knob
                parts["metal"].append(box(2.0, y - 1.2, z - 1.5, 5.5, y + 1.2, z + 1.5))
    for x0, y0, x1, y1, z0, z1, key in m.grip_parts():
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if key == "led":
            cuts.append(cyl(cx, cy, C.GRIP_TOP - 3, C.GRIP_TOP + 1, 1.8))
            parts["led"].append(cyl(cx, cy, C.GRIP_TOP - 3, C.GRIP_TOP + 0.5, 1.55))
        elif key == "screen":
            cuts.append(box(x0, y0, C.GRIP_TOP - 1.0, x1, y1, C.GRIP_TOP + 1))
            parts["screen"].append(box(x0, y0, C.GRIP_TOP - 1.0, x1, y1, C.GRIP_TOP - 0.3))
            aw, ah = C.SCREEN["active"]
            parts["screen_on"].append(box(cx - aw / 2, cy - ah / 2, C.GRIP_TOP - 0.3, cx + aw / 2, cy + ah / 2, C.GRIP_TOP - 0.2))
        elif key == "speaker":
            r = (x1 - x0) / 2
            cuts.append(cyl(cx, cy, z0, C.GRIP_TOP - 1.5, r))          # room for the driver under a 1.5 mm skin
            cuts.append(union([cyl(hx, hy, C.GRIP_TOP - 1.6, C.GRIP_TOP + 1, C.SPEAKER["hole_r"])
                               for hx, hy in C.grille_holes(x0, y0, x1, y1)]))
            parts["grille"].append(cyl(cx, cy, z0, C.GRIP_TOP - 1.5, r))
    return cuts, parts


def export(name, color, shapes):
    if not shapes:
        return
    comp = Part.makeCompound(shapes)
    mesh = MeshPart.meshFromShape(Shape=comp, LinearDeflection=0.08, AngularDeflection=0.4)
    mesh.write(os.path.join(OUT, "%s_%s.stl" % (name, color)))


def build(m):
    opening, keys = key_parts(m)
    cuts, extras = grip_parts(m)
    b = body(m).cut(opening).cut(union(cuts))
    export(m.name, "case", [b])
    for color, shapes in list(keys.items()) + list(extras.items()):
        export(m.name, color, shapes)
    bb = b.BoundBox
    print("%s: %.1f x %.1f x %.1f mm, %d keys" % (m.name, bb.XLength, bb.YLength, bb.ZLength, len(m.keys())))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    for m in C.MODELS:
        build(m)
