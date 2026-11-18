"""eTutti Student V3: hands the scene to Blender for the photo-real pictures.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/blender_export.py
    "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe" -b --python etutti/hardware/student_v03/case/render_blender.py -- [shot ...] [--fast]

This script (CadQuery venv, after case.py) writes case/blender/build/:
  <group>__<colour>.ply   every mesh of passos.scene() (+ the screen's cable), merged per group and colour, millimetres,
                          in the scene's frame (x right, y = -SPEC y, z up, z = 0 at the board's top)
  manifest.json           the files with their group and colour, and the shots: which groups are shown, how far each group
                          is pulled apart, the camera (position, target, up, zoom), picture size, and the look (floor, light from below)
The board's own copper, mask and silkscreen come from the KiCad GLB (kicad-cli, written here too): build/placa.glb.
Shots mirror case/passos.py (same cameras and offsets) plus a few beauty shots; render_blender.py reads the manifest.
"""
import json
import os
import subprocess
import sys

import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import passos as P          # noqa: E402

R = P.R
BUILD = os.path.join(HERE, "blender", "build")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
BOARD = os.path.normpath(os.path.join(HERE, "..", "kicad", "student_v03.kicad_pcb"))
cx, cy = 126.0, -50.0


def shots():
    iso = [(cx - 230, cy - 330, 250), (cx, cy + 5, 5), (0, 0, 1)]
    below = [(cx - 160, cy - 300, -260), (cx, cy + 5, -2), (0, 0, 1)]
    S = {}
    base_g = ["placa", "pecas"]
    modg = base_g + ["encoders", "modulo", "m25_espacador", "m25_parafuso", "m25_porca"]
    g4 = modg + ["teclas", "porcas", "espacadores", "grade", "parafusos"]
    g5 = g4 + ["botoes"]
    boardg = ["placa", "pecas", "encoders", "modulo", "m25_espacador", "m25_parafuso", "m25_porca", "teclas", "porcas",
              "espacadores", "grade", "parafusos", "botoes", "cabo"]
    inner = g5 + ["cabo", "tampa", "janela", "tela", "falante", "caixa"]
    g9 = inner + ["base", "bateria", "parafusos_base"]
    allg = sorted({g for _m, _c, _o, g in P.scene()} | {"cabo"})

    def add(name, shown, cam, zoom, size, offs=None, under=False, floor=False, pers=True):
        S[name] = dict(shown=list(shown), cam=[list(c) for c in cam], zoom=zoom, size=list(size), offsets=offs or {}, under=under, floor=floor)

    # ---- beauty shots (closed instrument)
    closed = ["tampa", "janela", "tela", "falante", "caixa", "base", "bateria", "parafusos_base", "placa", "pecas", "encoders",
              "modulo", "m25_espacador", "m25_parafuso", "m25_porca", "teclas", "porcas", "espacadores", "grade", "parafusos", "botoes", "knobs"]
    add("r_isometrico", closed, [(cx - 190, cy - 300, 250), (cx, cy + 5, 5), (0, 0, 1)], 1.15, (2400, 1400), floor=True)
    add("r_esquerda", closed, [(-30, -190, 95), (38, -52, 10), (0, 0, 1)], 1.7, (2400, 1500), floor=True)
    add("r_teclado", closed, [(cx + 40, cy - 250, 110), (cx + 30, cy + 10, 14), (0, 0, 1)], 1.9, (2400, 1500), floor=True)
    add("r_parede", closed, [(-150, -75, 6), (0, -56, -2), (0, 0, 1)], 3.4, (2400, 1500), floor=True)
    add("r_fundo", ["tampa", "base", "bateria", "parafusos_base"], [(cx - 120, cy - 300, -330), (cx, cy + 5, -8), (0, 0, 1)], 1.4, (2400, 1500), under=True)
    # ---- exploded
    off = {"base": (0, 0, -64), "parafusos_base": (0, 0, -64), "bateria": (0, 0, -40),
           "porcas": (0, 0, -26), "modulo": (0, 0, -10), "m25_espacador": (0, 0, -6), "m25_porca": (0, 0, -16), "m25_parafuso": (0, 0, 8),
           "teclas": (0, 0, 16), "espacadores": (0, 0, 36), "parafusos": (0, 0, 58), "grade": (0, 0, 46),
           "tela": (-70, 0, 70), "falante": (-70, 0, 70), "caixa": (-70, 0, 70), "janela": (-70, 0, 92),
           "tampa": (0, 0, 112), "botoes": (0, 0, 156), "knobs": (0, 0, 156), "encoders": (0, 0, 20)}
    add("r_explodido", allg, [(cx - 330, cy - 480, 380), (cx - 30, cy + 5, 60), (0, 0, 1)], 1.0, (2400, 2000), off)
    # ---- steps
    add("r_passo_1a", base_g, below, 1.3, (2000, 1250), under=True)
    add("r_passo_1", base_g + ["encoders"], iso, 1.35, (2000, 1250), {"encoders": (0, 0, 26)})
    add("r_passo_2", modg, [(-100, -300, -90), (40, -18, -4), (0, 0, 1)], 1.55, (2000, 1300),
        {"modulo": (0, 0, -18), "m25_espacador": (0, 0, -9), "m25_porca": (0, 0, -34), "m25_parafuso": (0, 0, 12)}, under=True)
    add("r_passo_3", modg + ["teclas"], iso, 1.35, (2000, 1250), {"teclas": (0, 0, 34)})
    add("r_passo_4", g4, iso, 1.1, (2000, 1250), {"porcas": (0, 0, -18), "espacadores": (0, 0, 30), "grade": (0, 0, 50), "parafusos": (0, 0, 66)})
    add("r_passo_5", g5, iso, 1.35, (2000, 1250), {"botoes": (0, 0, 44)})
    add("r_passo_6", g5 + ["cabo"], [(-30, -190, 120), (40, -40, 4), (0, 0, 1)], 1.25, (2000, 1300))
    lid = ["tampa", "janela", "tela", "falante", "caixa"]
    add("r_passo_7", lid, [(-70, -320, -230), (40, -45, -20), (0, 0, 1)], 1.5, (2000, 1250),
        {"janela": (0, 0, -20), "tela": (0, 0, -42), "falante": (0, 0, -66), "caixa": (0, 0, -80)}, under=True)
    add("r_passo_8", inner, [(cx - 240, cy - 330, -210), (cx, cy + 5, 6), (0, 0, -1)], 1.2, (2000, 1250),
        {g: (0, 0, -60) for g in boardg}, under=True)
    add("r_passo_9", g9, [(cx - 240, cy - 330, -210), (cx, cy + 5, -8), (0, 0, -1)], 1.2, (2000, 1250),
        {"base": (0, 0, -62), "bateria": (0, 0, -40), "parafusos_base": (0, 0, -92)}, under=True)
    add("r_passo_10", g9 + ["knobs"], iso, 1.4, (2000, 1250), {"knobs": (0, 0, 30)})
    return S


def main():
    os.makedirs(BUILD, exist_ok=True)
    S = P.scene()
    S += P.cable(top_z=16.0)
    groups = {}
    for m, col, op, grp in S:
        key = (grp, col if isinstance(col, str) else "rgb")
        groups.setdefault(key, []).append(m)
    files = []
    for (grp, col), meshes in sorted(groups.items()):
        merged = meshes[0].copy()
        if len(meshes) > 1:
            merged = pv.merge([m.triangulate() if hasattr(m, "triangulate") else m for m in meshes], merge_points=False)
        else:
            merged = merged.triangulate()
        merged.clear_data()
        name = "%s__%s.ply" % (grp, col.lstrip("#"))
        merged.save(os.path.join(BUILD, name), binary=True)
        files.append({"file": name, "group": grp, "colour": col})
    # the board (copper, mask, silkscreen) from KiCad: no component models, they are the boxes of the scene
    glb = os.path.join(BUILD, "placa.glb")
    subprocess.run([KICAD_CLI, "pcb", "export", "glb", "-f", "--user-origin", "0x0mm", "--include-pads", "--include-silkscreen",
                    "--component-filter", "NONE_X", "-o", glb, BOARD], check=True, capture_output=True)
    man = {"files": files, "shots": shots(), "board_underside": P.BOARD_BOTTOM}
    json.dump(man, open(os.path.join(BUILD, "manifest.json"), "w"), indent=1)
    print(len(files), "mesh files,", len(man["shots"]), "shots")


if __name__ == "__main__":
    main()
