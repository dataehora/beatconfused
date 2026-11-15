"""eTutti Student V01: the whole instrument in 3D, without the case (the case is the next step).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v01/model3d/build.py

1. kicad-cli exports the board and the plate as GLB; KiCad's Python lists every footprint.
2. The parts are put together in one frame: x right, y = -y of KiCad (towards the back), z up,
   **top of the board at z = 0**, millimetres.
   - board, silkscreen, pads and the parts KiCad's library has a model for: from the GLB;
   - parts without a KiCad model: a box of the courtyard size and the footprint's `Altura_mm`;
   - MicroMod Teensy module: SparkFun's STEP (student/eTutti_3D.3dshapes, J's folder);
   - encoders, USB-C, jack, M.2 connector, battery connector, Program button, LED: the parts' own
     STEP models, downloaded from EasyEDA by LCSC code (fetch_models.py -> modelos/, not in Git);
   - knobs and support pillar: J's VRML models from the same folder;
   - keys (Gateron KS-20 + the Pocket's cap), plate, battery, speaker: built here from their sizes.
3. Writes img/*.png (views), heights.json (how far each group reaches above and below the board)
   and build/student_v01.gltf (the model, to open in a 3D viewer).

J's folder is not in Git; without it the script stops and says so.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glb  # noqa: E402

ROOT = os.path.dirname(HERE)
HW = os.path.dirname(ROOT)
BUILD = os.path.join(HERE, "build")
IMG = os.path.join(HERE, "img")
SHAPES = os.path.join(HW, "student", "eTutti_3D.3dshapes")
MODULE_STEP = os.path.join(SHAPES, "SparkFun MicroMod Teensy Processor.step")
KEYCAP = os.path.join(HW, "pocket", "case", "out", "keycap_natural.stl")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
KICAD_PY = "C:/Program Files/KiCad/10.0/bin/python.exe"

T_PCB = 1.2
# keys (Gateron KS-20 on a 1.6 mm plate; numbers of etutti/hardware/case/keycap.py)
Z_PLATE_TOP = 5.1            # above the board's top
PLATE_T = 1.6
HOUSING_H = 6.1              # top housing above the plate
STEM = 3.6
CAP_Z = (11.2, 18.9)         # the Pocket's cap, key up
# MicroMod: card on a 2.5 mm standoff, 4.2 mm connector
STANDOFF_H = 2.5
CARD = 22.0
CARD_NOTCH_OFFSET = 4.0      # the screw notch is 4 mm off the card's centre line
# parts off the board (first guesses for the case step, see README)
ENC_PIN_BELOW = 2.3          # EC11 legs under the board, untrimmed
BATTERY = (34.0, 50.0, 5.0)  # LiPo 503450, ~1000 mAh: x, y, thickness
BATTERY_AT = (29.0, 70.0)    # KiCad x, y of its centre: under the board, front-left
BATTERY_TOP = -(T_PCB + 1.0 + 0.4)       # under the encoder legs trimmed to 1 mm, 0.4 of foam
SPEAKER_D, SPEAKER_H, SPEAKER_FACE_Z = 36.0, 4.6, 7.8      # face against the underside of the lid
PILLARS = [(197.5, 32.5), (207.5, 67.5), (112.5, 67.5), (167.5, 67.5), (127.5, 32.5), (132.5, 67.5)]
KNOB = {"SW401": "Volume_Knob.wrl", "SW402": "Encoder_Knob.wrl"}
MODELS = os.path.join(HERE, "modelos")       # EasyEDA's STEP models (fetch_models.py), not in Git
USB_MOUTH_X = 0.9            # KiCad x of the USB-C's mouth: 1.6 mm past the board's edge
JACK_MOUTH = (0, 1)          # which way the jack's mouth points in its own model
M2_SLOT = (0, 1)             # which way the card slot points in the M.2 connector's model
KNOB_FROM_Z = 8.0            # of J's knob models only the knob is used; the encoder body is a box

COL = {"pcb_part": (0.12, 0.12, 0.13), "metal": (0.75, 0.76, 0.78), "housing": (0.20, 0.21, 0.23),
       "stem": (0.85, 0.25, 0.20), "cap": (0.93, 0.91, 0.86), "plate": (0.10, 0.10, 0.11),
       "battery": (0.55, 0.60, 0.70), "speaker": (0.25, 0.25, 0.27), "module": (0.75, 0.10, 0.12),
       "socket": (0.10, 0.10, 0.11), "pillar": (0.85, 0.70, 0.30), "pin": (0.80, 0.80, 0.82),
       "case": (0.86, 0.84, 0.80)}


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def exports():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    for name, pcb, extra in (("board", "viaggio_micromod", ["--include-pads", "--include-silkscreen", "--subst-models"]),
                             ("plate", "student_v01_plate", [])):
        run([KICAD_CLI, "pcb", "export", "glb", "-f", "--user-origin", "0x0mm", "--include-soldermask"] + extra +
            ["-o", os.path.join(BUILD, name + ".glb"), os.path.join(ROOT, "kicad", pcb + ".kicad_pcb")])
    run([KICAD_PY, os.path.join(HERE, "footprints.py")])


# ---------------------------------------------------------------- mesh helpers (model frame)
def poly(points, faces):
    f = np.column_stack([np.full(len(faces), 3), faces]).ravel()
    return pv.PolyData(np.asarray(points, dtype=float), f)


def box(x0, y0, z0, x1, y1, z1):
    return pv.Box(bounds=(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1)))


def kbox(b, z0, z1):
    """Box over a KiCad rectangle [x0, y0, x1, y1]."""
    return box(b[0], -b[1], z0, b[2], -b[3], z1)


def cyl(xk, yk, z0, z1, d, n=48):
    return pv.Cylinder(center=(xk, -yk, (z0 + z1) / 2), direction=(0, 0, 1), radius=d / 2, height=abs(z1 - z0),
                       resolution=n).triangulate()


def hull(points):
    return pv.PolyData(np.asarray(points, dtype=float)).delaunay_3d().extract_surface(algorithm="dataset_surface").triangulate()


def vrml(path):
    """(points_mm, faces, rgb, zmin, zmax) of each Shape of a KiCad-style VRML file (1 unit = 2.54 mm)."""
    text = open(path, encoding="utf-8", errors="replace").read()
    out = []
    for chunk in text.split("Shape {")[1:]:
        col = re.search(r"diffuseColor\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", chunk)
        pts = re.search(r"point\s*\[([^\]]*)\]", chunk)
        idx = re.search(r"coordIndex\s*\[([^\]]*)\]", chunk)
        if not (pts and idx):
            continue
        p = np.array(re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", pts.group(1)), dtype=float).reshape(-1, 3) * 2.54
        faces, cur = [], []
        for v in (int(s) for s in re.findall(r"-?\d+", idx.group(1))):
            if v < 0:
                faces += [(cur[0], cur[i], cur[i + 1]) for i in range(1, len(cur) - 1)]
                cur = []
            else:
                cur.append(v)
        rgb = tuple(float(c) for c in col.groups()) if col else (0.5, 0.5, 0.5)
        out.append((p, np.array(faces), rgb))
    return out


def placed(p, xk, yk, z=0.0, rot=np.eye(3)):
    q = p @ np.asarray(rot, dtype=float).T
    return q + np.array([xk, -yk, z])


def step_mesh(key):
    """A model of modelos/ (file name starts with `key`) as one mesh in its own frame (cached as STL)."""
    step = next(os.path.join(MODELS, n) for n in sorted(os.listdir(MODELS)) if n.startswith(key) and n.endswith(".step"))
    stl = os.path.join(BUILD, key + ".stl")
    if not os.path.exists(stl) or os.path.getmtime(stl) < os.path.getmtime(step):
        import cadquery as cq
        cq.exporters.export(cq.importers.importStep(step), stl, tolerance=0.03, angularTolerance=0.3)
    return pv.read(stl)


def module_mesh():
    """SparkFun's STEP as one mesh, in its own frame (card 0..22 x 0..22, z 0..0.7; cached)."""
    stl = os.path.join(BUILD, "micromod_teensy.stl")
    if not os.path.exists(stl):
        import cadquery as cq
        cq.exporters.export(cq.importers.importStep(MODULE_STEP), stl, tolerance=0.05, angularTolerance=0.3)
    return pv.read(stl)


# ---------------------------------------------------------------- the assembly
def assemble():
    fps = json.load(open(os.path.join(BUILD, "footprints.json")))["footprints"]
    by = {f["ref"]: f for f in fps}
    parts = []          # (group, mesh, rgb)

    def add(group, mesh, rgb):
        parts.append((group, mesh, rgb))

    # board + the models KiCad has; GLB z = 0 is the board's bottom
    for p, f, rgb, _ in glb.read(os.path.join(BUILD, "board.glb")):
        p[:, 2] -= T_PCB
        add("placa", poly(p, f), rgb)
    for p, f, rgb, _ in glb.read(os.path.join(BUILD, "plate.glb")):
        p[:, 2] += Z_PLATE_TOP - PLATE_T
        add("plate", poly(p, f), COL["plate"])

    cap = pv.read(KEYCAP)
    cap.points[:, 2] += CAP_Z[1] - cap.bounds[5]
    special = set(KNOB) | {"J101", "H101", "J201", "J301", "J202", "SW403", "D401"}
    for f in fps:
        ref, b, h = f["ref"], f["box"], f["height"] or 0.0
        if f["lib"].startswith("Gateron"):
            x, y = f["x"], -f["y"]
            add("teclas", box(x - 7, y - 7, 0, x + 7, y + 7, Z_PLATE_TOP - PLATE_T), COL["housing"])
            lo, hi, zt = (7.7, 7.55), (5.7, 5.7), Z_PLATE_TOP + HOUSING_H
            add("teclas", hull([(x + sx * w[0], y + sy * w[1], z) for w, z in ((lo, Z_PLATE_TOP - PLATE_T), (lo, Z_PLATE_TOP + 1), (hi, zt))
                                for sx in (-1, 1) for sy in (-1, 1)]), COL["housing"])
            add("teclas", box(x - 2, y - 0.6, zt, x + 2, y + 0.6, zt + STEM), COL["stem"])
            add("teclas", box(x - 0.6, y - 2, zt, x + 0.6, y + 2, zt + STEM), COL["stem"])
            add("capas", cap.translate((x, y, 0), inplace=False), COL["cap"])
        elif ref in special or f["has_model"] or h <= 0:
            continue
        else:                                   # no KiCad model: courtyard box, shrunk a little
            s = 0.25
            bb = [b[0] + s, b[1] + s, b[2] - s, b[3] - s]
            z = (-T_PCB, -T_PCB - h) if f["bottom"] else (0, h)
            add("pecas_baixo" if f["bottom"] else "pecas_cima", kbox(bb, *z), COL["pcb_part"])

    # the real models of the parts KiCad's library lacks (modelos/, by fetch_models.py)
    def centre(f):
        return (f["box"][0] + f["box"][2]) / 2, (f["box"][1] + f["box"][3]) / 2

    def real(group, key, ref, facing, to, rgb, seat=0.0, at=None, edge=None):
        """Places a downloaded model: its direction `facing` (model x, y) turned to `to` (model frame,
        after the flip of a bottom part), its box centred on the courtyard, or with its far end in
        the `to` direction at KiCad x = `edge`. `seat` is the model's z of the board surface."""
        f = by[ref]
        m = step_mesh(key)
        p = m.points - np.array([0, 0, seat])
        v = np.array(facing, dtype=float)
        if f["bottom"]:
            p = p * np.array([1, -1, -1])
            v = v * np.array([1, -1])
        t = np.arctan2(to[1], to[0]) - np.arctan2(v[1], v[0])
        c, sn = np.cos(t), np.sin(t)
        p = np.column_stack([p[:, 0] * c - p[:, 1] * sn, p[:, 0] * sn + p[:, 1] * c, p[:, 2]])
        cx, cy = at or centre(f)
        lo, hi = p.min(0), p.max(0)
        shift = np.array([cx - (lo[0] + hi[0]) / 2, -cy - (lo[1] + hi[1]) / 2, -T_PCB if f["bottom"] else 0.0])
        if edge is not None:
            shift[0] = edge - (lo[0] if to[0] < 0 else hi[0])
        add(group, pv.PolyData(p + shift, m.faces), rgb)

    def pads_back(ref):
        """Unit direction (model frame) from the mounting pads to the signal pads of a connector."""
        ps = by[ref]["pads"]
        sig = np.mean([(x, -y) for x, y, n in ps if n.isdigit()], axis=0)
        mp = np.mean([(x, -y) for x, y, n in ps if not n.isdigit()], axis=0)
        d = sig - mp
        return (float(np.sign(d[0])), 0.0) if abs(d[0]) > abs(d[1]) else (0.0, float(np.sign(d[1])))

    for ref, wrl in KNOB.items():                 # encoder + J's knob, raised to the model's shaft top
        real("pecas_cima", "encoder_EC11E", ref, (1, 0), (1, 0), COL["metal"])
        cx, cy = centre(by[ref])
        top = step_mesh("encoder_EC11E").bounds[5]
        for p, fc, rgb in vrml(os.path.join(SHAPES, wrl)):
            if p[:, 2].min() >= KNOB_FROM_Z:
                add("knobs", poly(placed(p, cx, cy, top - 20.0), fc), rgb)
    real("pecas_cima", "usbc_TYPE-C-31-M-12", "J201", (0, 1), (-1, 0), COL["metal"], edge=USB_MOUTH_X)
    real("pecas_cima", "jack_PJ-327A", "J301", JACK_MOUTH, (-1, 0), COL["housing"])
    real("pecas_cima", "led_1615", "D401", (1, 0), (1, 0), (0.95, 0.95, 0.92))
    real("pecas_baixo", "botao_TS-1187A", "SW403", (1, 0), (1, 0), COL["metal"])
    back = pads_back("J202")
    real("pecas_baixo", "jst_S3B-PH-SM4-TB", "J202", (0, -1), back, (0.92, 0.90, 0.84))
    real("modulo", "m2_91302-42-067", "J101", M2_SLOT, (1, 0), COL["socket"], seat=-1.7)   # 4.2 mm body + 0.8 mm pegs

    # MicroMod: connector, standoff + screw, and SparkFun's module (card centre line 4 mm from the standoff)
    j, h = by["J101"], by["H101"]
    zb = -T_PCB
    add("modulo", cyl(h["x"], h["y"], zb - STANDOFF_H, zb, 4.2), COL["pillar"])
    add("modulo", cyl(h["x"], h["y"], zb - STANDOFF_H - 0.8 - 1.3, zb - STANDOFF_H - 0.8, 4.5), COL["metal"])
    m = module_mesh()
    cyk = h["y"] + CARD_NOTCH_OFFSET if abs(j["y"] - (h["y"] + CARD_NOTCH_OFFSET)) < 1 else h["y"] - CARD_NOTCH_OFFSET
    s = m.points.copy()                       # STEP: x across the card, y from the connector edge, z up
    side = 1.0 if cyk > h["y"] else -1.0
    q = np.column_stack([h["x"] - CARD + s[:, 1],                         # along the card: to the standoff
                         -(cyk - side * (s[:, 0] - CARD / 2)),            # across
                         zb - STANDOFF_H - s[:, 2]])                      # away from the board
    mod = pv.PolyData(q, m.faces)
    add("modulo", mod, COL["module"])

    # battery, speaker, pillars: first guesses, decided with the case
    bx, by_ = BATTERY_AT
    add("bateria", box(bx - BATTERY[0] / 2, -by_ - BATTERY[1] / 2, BATTERY_TOP - BATTERY[2],
                       bx + BATTERY[0] / 2, -by_ + BATTERY[1] / 2, BATTERY_TOP), COL["battery"])
    a2 = (31.0, 78.0)
    add("alto_falante", cyl(a2[0], a2[1], SPEAKER_FACE_Z - 1.2, SPEAKER_FACE_Z, SPEAKER_D), COL["speaker"])
    add("alto_falante", cyl(a2[0], a2[1], SPEAKER_FACE_Z - SPEAKER_H, SPEAKER_FACE_Z - 1.2, 22.0), COL["metal"])
    floor = min(BATTERY_TOP - BATTERY[2], -T_PCB - 5.5) - 0.5
    pil = vrml(os.path.join(SHAPES, "Support_Pillar.wrl"))
    for x, y in PILLARS:
        for p, fc, rgb in pil:
            p = p.copy()
            p[:, 2] = floor + p[:, 2] / p[:, 2].max() * (-T_PCB - floor)
            add("pilares", poly(placed(p, x, y), fc), rgb)
    # the case (case/case.py), when it has been built
    case = os.path.join(ROOT, "case", "out")
    if os.path.exists(os.path.join(case, "tampa.stl")):
        add("case_fundo", pv.read(os.path.join(case, "fundo.stl")), COL["case"])
        add("case_tampa", pv.read(os.path.join(case, "tampa.stl")), COL["case"])
        sp = pv.read(os.path.join(case, "espacador.stl"))
        for f in fps:
            if f["lib"].startswith("MountingHole") and f["ref"] in ("H5", "H6", "H7", "H8"):
                add("espacadores", sp.translate((f["x"], -f["y"], 0), inplace=False), COL["pillar"])
                add("espacadores", cyl(f["x"], f["y"], Z_PLATE_TOP, Z_PLATE_TOP + 1.6, 4.4, 6), COL["metal"])   # M2 nut
    return parts, floor


def heights(parts, floor):
    out = {}
    for g in sorted({p[0] for p in parts}):
        zs = [(m.bounds[4], m.bounds[5]) for gg, m, _ in parts if gg == g]
        out[g] = {"z_min": round(min(z[0] for z in zs), 2), "z_max": round(max(z[1] for z in zs), 2)}
    out["_fundo_interno_do_case"] = round(floor, 2)
    out["_abaixo_da_placa_mm"] = {g: round(-T_PCB - v["z_min"], 2) for g, v in out.items()
                                  if isinstance(v, dict) and v["z_min"] < -T_PCB - 0.3}
    return out


CASE = ("case_fundo", "case_tampa", "espacadores")
SHOTS = {      # name: (camera position, focal point, view up, hidden groups)
    "cima": ((60, -330, 300), (125, -52, 0), (0, 0, 1), CASE),
    "cima_sem_capas": ((60, -330, 300), (125, -52, 0), (0, 0, 1), CASE + ("capas",)),
    "baixo": ((60, 230, -330), (125, -50, 0), (0, 0, -1), CASE),
    "baixo_esquerda": ((-40, 110, -150), (40, -50, -3), (0, 0, -1), CASE),
    "cima_esquerda": ((-60, -150, 110), (30, -35, 3), (0, 0, 1), CASE),
    "modulo": ((60, 40, -75), (40, -18, -3), (0, 0, -1), CASE + ("bateria",)),
    "frente": ((125, -520, 6), (125, -50, 6), (0, 0, 1), CASE),
    "esquerda": ((-300, -50, 6), (40, -50, 6), (0, 0, 1), CASE),
    # with the case (the loose pillars of the bare model are the case's own here)
    "case_cima": ((60, -330, 300), (125, -52, 0), (0, 0, 1), ("pilares",)),
    "case_esquerda": ((-90, -170, 120), (30, -40, 3), (0, 0, 1), ("pilares",)),
    "case_baixo": ((60, 230, -330), (125, -50, 0), (0, 0, -1), ("pilares",)),
    "case_aberto_baixo": ((60, 230, -330), (125, -50, 0), (0, 0, -1), ("pilares", "case_fundo")),
    "case_fundo": ((60, -330, 300), (125, -52, 0), (0, 0, 1),
                   ("pilares", "case_tampa", "capas", "teclas", "plate", "knobs", "alto_falante", "espacadores",
                    "placa", "pecas_cima", "pecas_baixo", "modulo")),
    "case_frente": ((125, -520, 6), (125, -50, 6), (0, 0, 1), ("pilares",)),
}


def render(parts):
    for name, (pos, focal, up, hide) in SHOTS.items():
        pl = pv.Plotter(off_screen=True, window_size=(2000, 1200))
        pl.set_background("#f3f1ec")
        for g, m, rgb in parts:
            if g not in hide:
                pl.add_mesh(m, color=rgb, smooth_shading=False, specular=0.15)
        pl.camera_position = [pos, focal, up]
        if name in ("frente", "esquerda", "case_frente"):
            pl.enable_parallel_projection()
            pl.camera.parallel_scale = 40 if name == "esquerda" else 84
        else:
            pl.camera.view_angle = 22
        pl.screenshot(os.path.join(IMG, "student_v01_%s.png" % name))
        if name == "cima":
            pl.export_gltf(os.path.join(BUILD, "student_v01.gltf"))
        pl.close()


def main():
    if not os.path.exists(MODULE_STEP):
        raise SystemExit("falta a pasta de modelos do J: " + SHAPES)
    if "--no-export" not in sys.argv:
        exports()
    parts, floor = assemble()
    h = heights(parts, floor)
    json.dump(h, open(os.path.join(HERE, "heights.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(h, indent=1, ensure_ascii=False))
    render(parts)


if __name__ == "__main__":
    main()
