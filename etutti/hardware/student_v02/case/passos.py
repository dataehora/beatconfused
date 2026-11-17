"""eTutti Student V2: the exploded view and the assembly steps, for the presentation page.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v02/case/passos.py

Reads the same scene as render.py (the meshes in out/*.stl). Writes
  renders/passos/explodido.png, passo_1.png ... passo_7.png     (full size)
  ../../../studentV2/img/*.jpg                                    (what the page serves)
  ../../../studentV2/img/ancoras.json                             (where each numbered part is in the
                                                                   exploded picture, in % of its width/height)
In a step picture the parts added by that step keep their colours and the ones already there are
faded, so the eye goes to what is new.
"""
import json
import os
import sys

import numpy as np
import pyvista as pv
import vtk
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R          # noqa: E402

G = R.G
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
IMG = os.path.join(REPO, "etutti", "studentV2", "img")
PASSOS = os.path.join(R.REN, "passos")
BG = (0xF3, 0xF1, 0xEC)


def fade(col, k=0.62):
    c = col.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(int(v + (b - v) * k) for v, b in zip(rgb, BG))


def scene():
    S = R.scene()
    # the six screws of the lid, from below: heads in the base's recesses
    for x, y in R.INFO["posicoes"]["parafusos_da_tampa"]:
        S.append((pv.Cylinder(center=(x, -y, -10.1 + 0.9), direction=(0, 0, 1), radius=2.1, height=1.8), "#6E6C68", 1.0, "parafusos_base"))
        S.append((pv.Cylinder(center=(x, -y, -4.0), direction=(0, 0, 1), radius=0.9, height=12.0), "#8C8C8C", 1.0, "parafusos_base"))
    return S


def view(S, name, camera, size, shown, new=(), offsets=None, parallel=False, zoom=None, scale=None, anchors=None, up_ok=True):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("#F3F1EC")
    for m, col, op, grp in S:
        if grp not in shown:
            continue
        if offsets and grp in offsets:
            m = m.translate(offsets[grp], inplace=False)
        c = col if (not new or grp in new) else fade(col)
        R.add(pl, m, c, op)
    pl.camera_position = camera
    if parallel:
        pl.enable_parallel_projection()
        if scale:
            pl.camera.parallel_scale = scale
    if zoom:
        pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(60, 80, 300), focal_point=(126, -50, 0), intensity=0.35))
    path = os.path.join(PASSOS, name)
    pl.screenshot(path)
    out = None
    if anchors:
        out = {}
        W, H = size
        co = vtk.vtkCoordinate()
        co.SetCoordinateSystemToWorld()
        for k, (x, y, z) in anchors.items():
            co.SetValue(x, -y, z)
            px, py = co.GetComputedDoubleDisplayValue(pl.renderer)
            out[k] = [round(100 * px / W, 2), round(100 * (1 - py / H), 2)]
    pl.close()
    return out


def jpg(name, width, q=86):
    im = Image.open(os.path.join(PASSOS, name + ".png")).convert("RGB")
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(os.path.join(IMG, name + ".jpg"), quality=q, optimize=True, progressive=True)
    return [width, h]


def main():
    os.makedirs(PASSOS, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    S = scene()
    cx, cy = 126.0, -50.0
    ALL = {g for _m, _c, _o, g in S}
    sizes = {}

    # ---- exploded, in the order the parts go together (bottom to top)
    off = {"base": (0, 0, -50), "parafusos_base": (0, 0, -50), "bateria": (0, 0, -26),
           "espacadores": (0, 0, 22), "grade": (0, 0, 36), "parafusos": (0, 0, 50),
           "tela": (-78, 0, 64), "falante": (-78, 0, 64), "caixa": (-78, 0, 64), "janela": (-78, 0, 86),
           "tampa": (0, 0, 104), "botoes": (0, 0, 150), "knobs": (0, 0, 150)}
    anchors = {
        "1": (215, 88, -57.5), "2": (38, 73, -20.8), "3": (200, 80, -1.2), "4": (27.5, 18, -3.5),
        "5": (136, 41.99, 11.2 + 2), "6": (200.2, 92.53, 50 + 5), "7": (170, 34, 36 + 12.9),
        "8": (130, 6, 104 + 8), "9": (37 - 78, 22, 86 + 17), "10": (37 - 78, 22, 64 + 14), "11": (37 - 78, 73, 64 + 10),
        "12": (170, 58, 150 + 20), "13": (28, 44.5, 150 + 25),
    }
    a = view(S, "explodido.png", [(cx - 330, cy - 480, 360), (cx - 36, cy + 5, 62), (0, 0, 1)], (2400, 2000), ALL, offsets=off,
             zoom=1.05, anchors=anchors)
    sizes["explodido"] = jpg("explodido", 1800)
    json.dump(a, open(os.path.join(IMG, "ancoras.json"), "w"), indent=1)

    cam_iso = [(cx - 230, cy - 330, 250), (cx, cy + 5, 5), (0, 0, 1)]
    # ---- steps
    base_g = {"placa", "pecas"}
    steps = [
        ("passo_1", base_g, base_g, None, cam_iso, {}),
        ("passo_2", base_g | {"teclas"}, {"teclas"}, None, cam_iso, {}),
        ("passo_3", base_g | {"teclas", "espacadores", "grade", "parafusos"}, {"espacadores", "grade", "parafusos"}, None, cam_iso, {}),
    ]
    for name, shown, new, _x, cam, o in steps:
        view(S, name + ".png", cam, (2000, 1200), shown, new=new, offsets=o, zoom=1.35)
        sizes[name] = jpg(name, 1400)
    # 4: the lid, seen from below, with what goes inside it
    lid = {"tampa", "janela", "tela", "falante", "caixa"}
    view(S, "passo_4.png", [(cx - 60, cy + 40, -330), (cx - 60, cy, 4), (0, -1, 0)], (2000, 1200), lid, new={"janela", "tela", "falante", "caixa"},
         zoom=1.35)
    sizes["passo_4"] = jpg("passo_4", 1400)
    # 5: the lid comes down over the board and its grid
    inner = base_g | {"teclas", "espacadores", "grade", "parafusos", "tampa", "janela", "tela", "falante", "caixa"}
    view(S, "passo_5.png", cam_iso, (2000, 1200), inner, new={"tampa", "janela", "tela", "falante", "caixa"},
         offsets={"tampa": (0, 0, 46), "janela": (0, 0, 46), "tela": (0, 0, 46), "falante": (0, 0, 46), "caixa": (0, 0, 46)}, zoom=1.2)
    sizes["passo_5"] = jpg("passo_5", 1400)
    # 6: the base with the battery, from below
    shown6 = inner | {"base", "bateria", "parafusos_base"}
    view(S, "passo_6.png", [(cx - 300, cy - 400, 170), (cx, cy + 5, -22), (0, 0, 1)], (2000, 1200), shown6, new={"base", "bateria", "parafusos_base"},
         offsets={"base": (0, 0, -62), "bateria": (0, 0, -62), "parafusos_base": (0, 0, -62)}, zoom=1.3)
    sizes["passo_6"] = jpg("passo_6", 1400)
    # 7: buttons and knobs, from above
    shown7 = inner | {"base", "bateria", "parafusos_base", "botoes", "knobs"}
    view(S, "passo_7.png", cam_iso, (2000, 1200), shown7, new={"botoes", "knobs"},
         offsets={"botoes": (0, 0, 30), "knobs": (0, 0, 30)}, zoom=1.35)
    sizes["passo_7"] = jpg("passo_7", 1400)
    # the finished instrument and the left wall (already made by render.py): copied for the page
    for n, w in (("isometrico", 1800), ("planta", 1800), ("parede", 1500), ("parede_zoom", 1500), ("logo", 1100), ("corte", 1500),
                 ("corte_falante", 1500)):
        im = Image.open(os.path.join(R.REN, n + ".png")).convert("RGB")
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(os.path.join(IMG, n + ".jpg"), quality=86, optimize=True, progressive=True)
        sizes[n] = [w, h]
    json.dump(sizes, open(os.path.join(IMG, "tamanhos.json"), "w"), indent=1)
    print(json.dumps(sizes))
    print(json.dumps(a))


if __name__ == "__main__":
    main()
