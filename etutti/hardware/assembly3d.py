"""3D pictures of the eTuttino for the manuals (run with KiCad's Python;
build_pcb.py calls render_all() after building the board).

KiCad has 3D models for the SMD parts and the pin sockets, but not for the
Gateron switches, the keycaps, the plate or the Teensy + Audio Board. This
module writes simple VRML stand-ins for those (boxes and cylinders, sized
from the real parts), drops them onto a copy of the routed board, and
renders:

  etutti/manuais/img/pcb_top.jpg, pcb_bottom.jpg      the bare board (parts on the back)
  etutti/manuais/img/detail_*.jpg                     close-ups for soldering
  etutti/manuais/img/assembled_*.jpg                  everything installed

Each picture also gets a small "-sm" copy for the page; the manual opens
the full one when clicked.
"""
import os
import subprocess

import pcbnew

import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.normpath(os.path.join(HERE, "..", "manuais", "img"))
MODEL_PATH = os.path.join(HERE, "kicad", "etuttino_assembly.wrl")
ASSEMBLED_PATH = os.path.join(HERE, "kicad", "etuttino_assembled.kicad_pcb")

# Heights above the board's top surface (mm). MX geometry: the plate top
# sits 5 mm above the PCB; the switch's top housing rises ~6.6 mm above it.
PLATE_Z = (3.5, 5.0)
SWITCH_Z = (5.0, 11.4)
KEYCAP_Z = (11.8, 18.8)
AUDIO_Z = 3.0            # Audio Board soldered low on its header legs
AUDIO_T = 1.6
HEADER_H = 8.5           # stacking header body on the Audio Board
TEENSY_T = 1.6

COLORS = {
    "plate": (0.08, 0.08, 0.09),
    "switch": (0.25, 0.27, 0.30),
    "cap_light": (0.95, 0.92, 0.86),
    "cap_dark": (0.22, 0.23, 0.25),
    "cap_c": (0.55, 0.23, 0.18),
    "audio": (0.10, 0.42, 0.22),
    "teensy": (0.09, 0.48, 0.28),
    "header": (0.06, 0.06, 0.06),
    "pin": (0.85, 0.70, 0.30),
    "chip": (0.05, 0.05, 0.05),
    "metal": (0.75, 0.76, 0.78),
}


class Vrml:
    """Shapes in board millimetres (x right, y down, z up from the board's
    top surface), written in KiCad's VRML units (0.1 inch, y up)."""

    def __init__(self):
        self.shapes = []

    @staticmethod
    def _p(x, y, z):
        return "%.4f %.4f %.4f" % (x / 2.54, -y / 2.54, z / 2.54)

    def _shape(self, pts, faces, color):
        r, g, b = COLORS[color]
        self.shapes.append(
            "Shape {\n appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f specularColor 0.15 0.15 0.15 shininess 0.25 } }\n"
            " geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] }\n}\n"
            % (r, g, b, ", ".join(self._p(*p) for p in pts), " ".join(" ".join(str(i) for i in f) + " -1" for f in faces)))

    def box(self, x0, y0, z0, x1, y1, z1, color):
        pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
               (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        self._shape(pts, faces, color)

    def cylinder(self, cx, cy, z0, z1, r, color, n=28, axis="z"):
        import math
        pts = []
        for z in (z0, z1):
            for i in range(n):
                a = 2 * math.pi * i / n
                u, v = r * math.cos(a), r * math.sin(a)
                if axis == "z":
                    pts.append((cx + u, cy + v, z))
                else:   # along x: z0..z1 are x positions, cx/cy are y/z of the axis
                    pts.append((z, cx + u, cy + v))
        faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self._shape(pts, faces, color)

    def save(self, path):
        with open(path, "w", encoding="ascii") as f:
            f.write("#VRML V2.0 utf8\n" + "".join(self.shapes))


def build_model():
    v = Vrml()
    ks = G.keys()
    # plate (the notch for the stack is left open)
    x0, y0 = G.GRID_X0 - G.PLATE_MARGIN, G.GRID_Y0 - G.PLATE_MARGIN
    x1 = G.GRID_X0 + G.GRID_UNITS * G.U + G.PLATE_MARGIN
    y1 = G.GRID_Y0 + 4 * G.U + G.PLATE_MARGIN
    v.box(x0, y0, PLATE_Z[0], G.NOTCH_X, G.NOTCH_Y, PLATE_Z[1], "plate")
    v.box(x0, G.NOTCH_Y, PLATE_Z[0], x1, y1, PLATE_Z[1], "plate")
    # switches and round keycaps
    for k in ks:
        cx, cy = k["cx"], k["cy"]
        v.box(cx - 7.4, cy - 7.4, SWITCH_Z[0], cx + 7.4, cy + 7.4, SWITCH_Z[1], "switch")
        name = G.note_name(k["note"])
        color = "cap_dark" if "#" in name else "cap_light"
        v.cylinder(cx, cy, KEYCAP_Z[0], KEYCAP_Z[1], 8.6, color)
        if name.startswith("C") and "#" not in name:
            v.cylinder(cx, cy - 5.0, KEYCAP_Z[1], KEYCAP_Z[1] + 0.25, 0.9, "cap_c", n=12)
    # Audio Board, low on its header legs, with the headphone jack beside
    # the 0-12 row at the USB end
    zx0, zy0, zx1, zy1 = G.STACK_ZONE
    za, zt = AUDIO_Z, AUDIO_Z + AUDIO_T
    v.box(zx0, zy0, za, zx1, zy1, zt, "audio")
    jy = G.STACK_CY - 7.62 - 7.2
    v.box(zx1 - 13.0, jy - 3.0, zt, zx1 - 0.5, jy + 3.0, zt + 5.0, "header")
    v.cylinder(jy, zt + 2.5, zx1 - 0.5, zx1 + 1.5, 2.6, "header", axis="x")
    for ref, pad, pin, x, y in G.stack_pins():
        v.box(x - 0.32, y - 0.32, 0.0, x + 0.32, y + 0.32, za, "pin")
    # stacking-header bodies on top of the Audio Board, then the Teensy
    for row_y in (G.STACK_CY - 7.62, G.STACK_CY + 7.62):
        v.box(G.STACK_CX - 17.78, row_y - 1.27, zt, G.STACK_CX + 17.78, row_y + 1.27, zt + HEADER_H, "header")
    tz = zt + HEADER_H
    v.box(G.STACK_CX - 17.78, G.STACK_CY - 8.89, tz, G.STACK_CX + 17.78, G.STACK_CY + 8.89, tz + TEENSY_T, "teensy")
    v.box(G.STACK_CX - 6.0, G.STACK_CY - 5.0, tz + TEENSY_T, G.STACK_CX + 4.0, G.STACK_CY + 5.0, tz + TEENSY_T + 0.9, "chip")
    v.box(G.STACK_CX + 13.5, G.STACK_CY - 3.8, tz + TEENSY_T, G.STACK_CX + 18.8, G.STACK_CY + 3.8, tz + TEENSY_T + 2.6, "metal")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    v.save(MODEL_PATH)
    return KEYCAP_Z[1], tz + TEENSY_T + 2.6


def assembled_board(board_path):
    b = pcbnew.LoadBoard(board_path)
    # the stack is soldered straight to the board: no sockets in the picture
    for ref in ("J1", "J2"):
        fp = b.FindFootprintByReference(ref)
        fp.Models().clear()
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference("ASSEMBLY")
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = MODEL_PATH.replace("\\", "/")
    fp.Add3DModel(m)
    b.Add(fp)
    pcbnew.SaveBoard(ASSEMBLED_PATH, b)
    return ASSEMBLED_PATH


def render(cli, board, out, side="top", width=3000, height=1200, extra=()):
    path = os.path.join(IMG_DIR, out)
    args = [cli, "pcb", "render", "--side", side, "--width", str(width), "--height", str(height),
            "--quality", "high", "--background", "opaque", *extra, "--output", path, board]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path


def small_copy(cli, board, out, side, extra, width, height):
    base, ext = os.path.splitext(out)
    return render(cli, board, base + "-sm" + ext, side, width // 3, height // 3, extra)


def render_all(cli, board_path):
    os.makedirs(IMG_DIR, exist_ok=True)
    keycap_top, stack_top = build_model()
    assembled = assembled_board(board_path)
    # Pan is in board-centre-relative units of the render; these views were
    # framed by trial on the 267 x 88 mm board.
    shots = [
        (board_path, "pcb_top.jpg", "top", (), 3000, 1100),
        (board_path, "pcb_bottom.jpg", "bottom", (), 3000, 1100),
        (board_path, "detail_sensors.jpg", "bottom", ("--zoom", "4", "--pan", "6,1.2,0"), 2400, 1500),
        (board_path, "detail_muxes.jpg", "bottom", ("--zoom", "3.2", "--pan", "-3.2,-2.4,0"), 2400, 1500),
        (board_path, "detail_stack.jpg", "top", ("--zoom", "3.2", "--pan", "-9.8,-2.2,0"), 2400, 1500),
        (assembled, "assembled_top.jpg", "top", (), 3000, 1100),
        (assembled, "assembled_iso.jpg", "top", ("--perspective", "--rotate", "-48,0,18", "--zoom", "1.05"), 3000, 1600),
        (assembled, "assembled_front.jpg", "front", ("--zoom", "1.3"), 3000, 700),
    ]
    made = []
    for board, out, side, extra, w, h in shots:
        made.append(render(cli, board, out, side, w, h, extra))
        small_copy(cli, board, out, side, extra, w, h)
    return made, keycap_top, stack_top
