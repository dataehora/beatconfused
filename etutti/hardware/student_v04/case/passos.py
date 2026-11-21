"""eTutti Student V3: the exploded view and the assembly steps, for the presentation page and the assembly manual.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/passos.py [picture names...]   (~3 min)

Reads the same scene as render.py (the meshes in out/*.stl, after case.py) and adds what render.py leaves out: the MicroMod
module and its fixing (screw, spacer, nut), the nuts of the grid screws, the 6 lid screws, the screen's cable. Writes
  renders/passos/*.png                      (full size)
  ../../../studentV3/img/*.jpg              (what the page serves)
  ../../../studentV3/img/ancoras.json       (where each numbered part is in the exploded picture, % of its width / height)
  ../../../studentV3/img/tamanhos.json
In a step picture the parts added by that step keep their colours and the ones already there are faded; the parts being
added are pulled apart along the way they go in.
Steps 8 and 9 are drawn with the view upside down (view-up = -z): the lid lies face down on the bench, as it does in the
real assembly, the board is lowered into it and the tray goes on from the open side.
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
IMG = os.path.join(REPO, "etutti", "studentV3", "img")
PASSOS = os.path.join(R.REN, "passos")
BG = (0xF3, 0xF1, 0xEC)
INFO = R.INFO
Z0 = INFO["niveis"]["base"]
GRID_TOP = INFO["niveis"]["grade"][1]
BOARD_BOTTOM = -1.2


def fade(col, k=0.62):
    if not isinstance(col, str):
        return col
    c = col.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(int(v + (b - v) * k) for v, b in zip(rgb, BG))


def tube(p0, p1, r, col, grp, sag=0.0):
    """A wire: a tube along a short arc from p0 to p1 (SPEC coordinates, y as in the SPEC); sag lowers the middle."""
    pts = []
    for t in np.linspace(0, 1, 14):
        p = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
        p[2] -= sag * 4 * t * (1 - t)
        pts.append((p[0], -p[1], p[2]))
    return (pv.Spline(np.array(pts), 40).tube(radius=r), col, 1.0, grp)


def scene():
    S = R.scene()
    # regroup: the encoders (above the board) are their own group; the rest of 'pecas' is what the factory solders underneath
    out = []
    for m, col, op, grp in S:
        if grp == "pecas" and m.bounds[4] > -0.5:
            grp = "encoders"
        if grp == "parafusos":
            continue            # redrawn below, flush with the grid
        out.append((m, col, op, grp))
    S = out
    # grid screws: flat heads flush with the grid, shank to 0.25 past the nut under the board; the nuts under the board
    for x, y in INFO["posicoes"]["parafusos_da_grade"]:
        S.append((pv.Cylinder(center=(x, -y, GRID_TOP - 0.4), direction=(0, 0, 1), radius=1.9, height=0.8), "#8C8C8C", 1.0, "parafusos"))
        S.append((pv.Cylinder(center=(x, -y, GRID_TOP - 8.0), direction=(0, 0, 1), radius=1.0, height=15.2), "#8C8C8C", 1.0, "parafusos"))
        S.append((pv.Cylinder(center=(x, -y, BOARD_BOTTOM - 0.8), direction=(0, 0, 1), radius=2.3, height=1.6, resolution=6),
                  "#6E6C68", 1.0, "porcas"))
    # the six lid screws M2 x 14, from below through the tray and the board into the lid's posts
    for x, y in INFO["posicoes"]["parafusos_da_tampa"]:
        S.append((pv.Cylinder(center=(x, -y, Z0 + 0.9), direction=(0, 0, 1), radius=2.1, height=1.8), "#6E6C68", 1.0, "parafusos_base"))
        S.append((pv.Cylinder(center=(x, -y, Z0 + 7.0), direction=(0, 0, 1), radius=0.9, height=12.2), "#8C8C8C", 1.0, "parafusos_base"))
    # the MicroMod module (22 x 22 x 1 mm) under the board, 2.5 mm below it on a nylon spacer; M2.5 screw from above, nut below
    hx, hy = INFO["posicoes"]["h101"]
    mz1 = BOARD_BOTTOM - 2.5
    S.append((R.box(27.5, 7.0, 49.5, 29.0, mz1 - 1.0, mz1), "#1F3B63", 1.0, "modulo"))
    S.append((R.box(37.0, 12.0, 43.0, 18.0, mz1 - 1.8, mz1 - 1.0), "#2B2925", 1.0, "modulo"))          # the processor
    S.append((pv.Cylinder(center=(hx, -hy, BOARD_BOTTOM - 1.25), direction=(0, 0, 1), radius=2.0, height=2.5), "#E8E2D0", 1.0, "m25_espacador"))
    S.append((pv.Cylinder(center=(hx, -hy, 0.4), direction=(0, 0, 1), radius=2.4, height=0.8), "#E8E2D0", 1.0, "m25_parafuso"))
    S.append((pv.Cylinder(center=(hx, -hy, -4.0), direction=(0, 0, 1), radius=1.25, height=8.0), "#E8E2D0", 1.0, "m25_parafuso"))
    S.append((pv.Cylinder(center=(hx, -hy, mz1 - 2.0), direction=(0, 0, 1), radius=2.5, height=2.0, resolution=6), "#E8E2D0", 1.0, "m25_porca"))
    # the screen's cable: the plug in J401 (wires added by cable())
    S.append((R.box(32.8, 34.6, 38.2, 38.4, BOARD_BOTTOM - 2.2, BOARD_BOTTOM - 0.2), "#D9D5CC", 1.0, "cabo"))
    return S


WIRES = [("#C8402A", -1.5), ("#2B2925", -0.5), ("#E3B23C", 0.5), ("#3F7FD1", 1.5)]


def cable(top_z):
    """The 4 wires from the J401 plug, up through the slot, to the screen's pin row (SPEC coordinates)."""
    L = []
    cx_, cy_ = INFO["posicoes"]["oled_centro"]
    for col, dx in WIRES:
        L.append(tube((35.5 + dx * 0.8, 36.0, BOARD_BOTTOM - 1.0), (35.5 + dx * 0.8, 31.2, 4.0), 0.5, col, "cabo"))
        L.append(tube((35.5 + dx * 0.8, 31.2, 4.0), (cx_ + dx * 2.54, cy_ + 12.0, top_z), 0.22, col, "cabo", sag=6.0))
    return L


def view(S, name, camera, size, shown, new=(), offsets=None, zoom=None, anchors=None, under=0.0):
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
    if zoom:
        pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(60, 80, 300), focal_point=(126, -50, 0), intensity=0.35))
    if under:
        pl.add_light(pv.Light(position=(100, -200, -300), focal_point=(126, -50, 0), intensity=0.8 * under))
        pl.add_light(pv.Light(position=(250, 80, -300), focal_point=(126, -50, 0), intensity=0.4 * under))
    pl.screenshot(os.path.join(PASSOS, name))
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
    S += cable(top_z=16.0)
    cx, cy = 126.0, -50.0
    sizes = {}
    only = set(sys.argv[1:])

    def want(n):
        return not only or n in only

    # ---------------------------------------------------------------- exploded, bottom to top
    ALL = {g for _m, _c, _o, g in S}
    off = {"base": (0, 0, -64), "parafusos_base": (0, 0, -64), "bateria": (0, 0, -40),
           "porcas": (0, 0, -26), "modulo": (0, 0, -10), "m25_espacador": (0, 0, -6), "m25_porca": (0, 0, -16), "m25_parafuso": (0, 0, 8),
           "teclas": (0, 0, 16), "espacadores": (0, 0, 36), "parafusos": (0, 0, 58), "grade": (0, 0, 46),
           "tela": (-70, 0, 70), "falante": (-70, 0, 70), "caixa": (-70, 0, 70), "janela": (-70, 0, 92),
           "tampa": (0, 0, 112), "botoes": (0, 0, 156), "knobs": (0, 0, 156), "encoders": (0, 0, 20)}
    keys = INFO["teclas"]
    k8 = min(keys, key=lambda k: (k["x"] - 170) ** 2 + (k["y"] - 40) ** 2)
    k16 = min(keys, key=lambda k: (k["x"] - 190) ** 2 + (k["y"] - 66) ** 2)
    anchors = {
        "1": (215, 88, Z0 - 64 - 2), "2": (30, 70, -8.1 + 2.6 - 40), "3": (200, 80, -1.2),
        "4": (36, 18, -4.7 - 10), "5": (47.5, 14, 11), "6": (224.9, 31.74, BOARD_BOTTOM - 0.8 - 26), "7": (46, 44.5, 6 + 20),
        "8": (k8["x"], k8["y"], 11.2 + 16), "9": (157.13, 92.53, GRID_TOP + 58), "10": (232.7, 70.77, 6.2 + 36),
        "11": (200, 55, GRID_TOP + 46), "12": (130, 6, 14.5 + 112), "13": (37 - 70, 20, 13 + 92), "14": (37 - 70, 20, 10 + 70),
        "15": (37 - 70, 73, 8 + 70), "16": (k16["x"], k16["y"], 24 + 156), "17": (46, 44.5, 25.8 + 156),
    }
    if want("explodido"):
        a = view(S, "explodido.png", [(cx - 330, cy - 480, 380), (cx - 30, cy + 5, 60), (0, 0, 1)], (2400, 2000), ALL, offsets=off,
                 zoom=1.0, anchors=anchors)
        sizes["explodido"] = jpg("explodido", 1800)
        json.dump(a, open(os.path.join(IMG, "ancoras.json"), "w"), indent=1)

    base_g = {"placa", "pecas"}
    iso = [(cx - 230, cy - 330, 250), (cx, cy + 5, 5), (0, 0, 1)]
    below = [(cx - 160, cy - 300, -260), (cx, cy + 5, -2), (0, 0, 1)]

    def step(name, shown, new, cam, offs=None, zoom=1.3, size=(2000, 1200), under=0.0):
        if not want(name):
            return
        view(S, name + ".png", cam, size, shown, new=new, offsets=offs, zoom=zoom, under=under)
        sizes[name] = jpg(name, 1400)

    # 1: the board as it arrives (from below), and the encoders soldered on top
    step("passo_1a", base_g, {"placa", "pecas"}, below, zoom=1.3, under=1.0)
    step("passo_1", base_g | {"encoders"}, {"encoders"}, iso, offs={"encoders": (0, 0, 26)}, zoom=1.35)
    # 2: the module under the board, on its spacer, screw from above, nut below
    modg = base_g | {"encoders", "modulo", "m25_espacador", "m25_parafuso", "m25_porca"}
    step("passo_2", modg, {"modulo", "m25_espacador", "m25_parafuso", "m25_porca"},
         [(-100, -300, -90), (40, -18, -4), (0, 0, 1)],
         offs={"modulo": (0, 0, -18), "m25_espacador": (0, 0, -9), "m25_porca": (0, 0, -34), "m25_parafuso": (0, 0, 12)},
         zoom=1.55, size=(2000, 1300), under=0.9)
    # 3: the 28 keys
    step("passo_3", modg | {"teclas"}, {"teclas"}, iso, offs={"teclas": (0, 0, 34)}, zoom=1.35)
    # 4: nuts, spacers, grid, 10 countersunk screws
    g4 = modg | {"teclas", "porcas", "espacadores", "grade", "parafusos"}
    step("passo_4", g4, {"porcas", "espacadores", "grade", "parafusos"}, iso,
         offs={"porcas": (0, 0, -18), "espacadores": (0, 0, 30), "grade": (0, 0, 50), "parafusos": (0, 0, 66)}, zoom=1.1)
    # 5: the 28 buttons
    g5 = g4 | {"botoes"}
    step("passo_5", g5, {"botoes"}, iso, offs={"botoes": (0, 0, 44)}, zoom=1.35)
    # 6: the screen's cable up through the slot (zoomed on the left end)
    step("passo_6", g5 | {"cabo"}, {"cabo"}, [(-30, -190, 120), (40, -40, 4), (0, 0, 1)], zoom=1.25, size=(2000, 1300))
    # 7: the lid face down: window, screen, acoustic box with the speaker (seen from the open side)
    lid = {"tampa", "janela", "tela", "falante", "caixa"}
    if want("passo_7"):
        view(S, "passo_7.png", [(-70, -320, -230), (40, -45, -20), (0, 0, 1)], (2000, 1200), lid,
             new={"janela", "tela", "falante", "caixa"}, zoom=1.5, under=0.6,
             offsets={"janela": (0, 0, -20), "tela": (0, 0, -42), "falante": (0, 0, -66), "caixa": (0, 0, -80)})
        sizes["passo_7"] = jpg("passo_7", 1400)
    # 8: board into the lid (view upside down: the lid lies on its face)
    boardg = ["placa", "pecas", "encoders", "modulo", "m25_espacador", "m25_parafuso", "m25_porca", "teclas", "porcas",
              "espacadores", "grade", "parafusos", "botoes", "cabo"]
    inner = g5 | {"cabo", "tampa", "janela", "tela", "falante", "caixa"}
    if want("passo_8"):
        view(S, "passo_8.png", [(cx - 240, cy - 330, -210), (cx, cy + 5, 6), (0, 0, -1)], (2000, 1200), inner,
             new=set(boardg), offsets={g: (0, 0, -60) for g in boardg}, zoom=1.2, under=0.6)
        sizes["passo_8"] = jpg("passo_8", 1400)
    # 9: feet on the tray, battery in its cradle, tray and 6 screws from the open side
    g9 = inner | {"base", "bateria", "parafusos_base"}
    if want("passo_9"):
        view(S, "passo_9.png", [(cx - 240, cy - 330, -210), (cx, cy + 5, -8), (0, 0, -1)], (2000, 1200), g9,
             new={"base", "bateria", "parafusos_base"},
             offsets={"base": (0, 0, -62), "bateria": (0, 0, -40), "parafusos_base": (0, 0, -92)}, zoom=1.2, under=0.6)
        sizes["passo_9"] = jpg("passo_9", 1400)
    # 10: knobs
    step("passo_10", g9 | {"knobs"}, {"knobs"}, iso, offs={"knobs": (0, 0, 30)}, zoom=1.4)

    for n, w in (("isometrico", 1800), ("planta", 1800), ("parede", 1500), ("parede_zoom", 1500), ("logo", 1100), ("corte", 1500),
                 ("corte_falante", 1500), ("bandeja_de_baixo", 1500), ("bandeja_de_cima", 1500), ("grade_escareada", 1400)):
        if not os.path.exists(os.path.join(R.REN, n + ".png")):
            continue
        im = Image.open(os.path.join(R.REN, n + ".png")).convert("RGB")
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(os.path.join(IMG, n + ".jpg"), quality=86, optimize=True, progressive=True)
        sizes[n] = [w, h]
    p = os.path.join(IMG, "tamanhos.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(sizes)
    json.dump(old, open(p, "w"), indent=1)
    print(json.dumps(old))


if __name__ == "__main__":
    main()
