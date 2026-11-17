"""eTutti Student V2: pictures of the modelled case, to compare with the canvas.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v02/case/render.py

Reads out/*.stl and out/case.json (case.py), pcb/footprints.json. Writes renders/:
  planta.png        from above, no perspective (the canvas' "planta")
  corte.png         cut along the rows at x = 107.7 (a key of row 2 and one of row 4 are cut through
                    their middle; rows 1 and 3 are half a pitch behind and show whole), seen from the left
  corte_falante.png cut through the speaker at x = 40
  isometrico.png    the closed instrument
  explodido.png     the pieces apart
  parede.png        the left wall with the connectors
Colours: the SPEC's Retro finish (the stripes are paint; here they are drawn on the lid's mesh).
"""
import json
import os
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

OUT = os.path.join(HERE, "out")
REN = os.path.join(HERE, "renders")
INFO = json.load(open(os.path.join(OUT, "case.json"), encoding="utf-8"))
FP = json.load(open(os.path.join(HERE, "..", "pcb", "footprints.json"), encoding="utf-8"))["footprints"]
CREAM, GREY, DARK = "#E8DEC6", "#9C9B96", "#4E4A45"
WHITE, BLACK = "#F1ECE1", "#1E1C1B"
STRIPES = [(58.0, 4.5, "#C8402A"), (63.5, 4.0, "#E07A2C"), (68.5, 2.0, "#E3B23C"),
           (237.5, 4.5, "#C8402A"), (243.0, 4.0, "#E07A2C"), (248.5, 2.0, "#E3B23C")]
TRAVEL = INFO["niveis"]["curso"]


def stl(name):
    return pv.read(os.path.join(OUT, name + ".stl"))


def moved(m, x, y, dz=0.0):
    return m.translate((x, -y, dz), inplace=False)


def box(x0, y0, x1, y1, z0, z1):
    return pv.Box(bounds=(x0, x1, -y1, -y0, z0, z1))


def stripes():
    """The paint: thin skins just outside the lid's top, its back and front chamfers and its front wall."""
    out = []
    e = 0.06
    for x0, w, col in STRIPES:
        x1 = x0 + w
        quads = [[(x0, 6, 18.2 + e), (x1, 6, 18.2 + e), (x1, 94, 18.2 + e), (x0, 94, 18.2 + e)],
                 [(x0, 94, 18.2 + e), (x1, 94, 18.2 + e), (x1, 100 + e, 14.7 + e), (x0, 100 + e, 14.7 + e)],
                 [(x0, 6, 18.2 + e), (x1, 6, 18.2 + e), (x1, -e, 14.7 + e), (x0, -e, 14.7 + e)],
                 [(x0, 100 + e, 14.7), (x1, 100 + e, 14.7), (x1, 100 + e, -4.0), (x0, 100 + e, -4.0)]]
        for q in quads:
            pts = np.array([(x, -y, z) for x, y, z in q], dtype=float)
            out.append((pv.PolyData(pts, faces=[4, 0, 1, 2, 3]), col, 1.0, "tampa"))
    return out


def scene():
    """[(mesh, colour or None, opacity, group)]"""
    S = []
    S.append((stl("tampa"), CREAM, 1.0, "tampa"))
    S += stripes()
    ink = stl("tinta")                      # the paint in the recesses, lifted a hair so that it shows
    S.append((ink.translate((-0.03, 0, 0.03), inplace=False), "#2B2925", 1.0, "tampa"))
    S.append((stl("tinta_marrom").translate((-0.03, 0, 0.02), inplace=False), "#8A3A22", 1.0, "tampa"))   # pad-printed, SPEC v3
    S.append((stl("base"), GREY, 1.0, "base"))
    S.append((stl("grade"), "#1C1B1A", 1.0, "grade"))        # FR-4, matte black mask
    sp = stl("espacador")
    for x, y in INFO["posicoes"]["parafusos_da_grade"]:
        S.append((moved(sp, x, y), "#B8AE9A", 1.0, "espacadores"))
        S.append((pv.Cylinder(center=(x, -y, INFO["niveis"]["grade"][1] + 0.8), direction=(0, 0, 1), radius=1.9, height=1.6), "#8C8C8C", 1.0, "parafusos"))
    cache = {}
    for k in INFO["teclas"]:
        name = "botao_%s_f%d" % (k["tipo"], k["fileira"])
        cache.setdefault(name, stl(name))
        S.append((moved(cache[name], k["x"], k["y"]), BLACK if k["tipo"] == "preto" else WHITE, 1.0, "botoes"))
        S.append((box(k["x"] - 7, k["y"] - 7, k["x"] + 7, k["y"] + 7, 0, 11.2), "#6F6A62", 1.0, "teclas"))
    kn = stl("knob")
    for x, y in G.KNOBS:
        S.append((moved(kn, x, y), BLACK, 1.0, "knobs"))
        S.append((box(x - 6.6, y - 6, x + 6.6, y + 6, 0, 6.5), "#8C8C8C", 1.0, "pecas"))
        S.append((pv.Cylinder(center=(x, -y, 13.25), direction=(0, 0, 1), radius=3.0, height=13.5), "#B3B2AE", 1.0, "pecas"))
    S.append((stl("caixa_acustica"), "#7A746A", 1.0, "caixa"))
    lv = INFO["pecas"]["caixa_acustica"]
    S.append((pv.Cylinder(center=(G.SPEAKER[0], -G.SPEAKER[1], lv["frente_do_falante_z"] - 2.5), direction=(0, 0, 1),
                          radius=14.0, height=5.0), "#22201E", 1.0, "falante"))
    S.append((stl("janela"), "#141312", 1.0, "janela"))
    g = G.GRILLE          # the acoustic mesh under the slots
    S.append((box(g["x0"] - 1.5, g["y0"] - 1.5, g["x1"] + 1.5, g["y0"] + (g["n"] - 1) * g["pitch"] + g["slot"] + 1.5, 15.9, 16.2),
              "#2A2826", 1.0, "falante"))
    ol = INFO["niveis"]["oled"]
    cx, cy = INFO["posicoes"]["oled_centro"]
    S.append((box(cx - 13.65, cy - 13.9, cx + 13.65, cy + 13.9, ol["pcb_bottom"], ol["pcb_top"]), "#1B4F8A", 1.0, "tela"))
    S.append((box(cx - 13.35, cy - 9.2, cx + 13.35, cy + 10.1, ol["pcb_top"], ol["glass_top"]), "#0B0B0A", 1.0, "tela"))
    # board and its parts
    x0, y0, x1, y1 = G.BOARD
    S.append((box(x0, y0, x1, y1, -1.2, 0), "#3F6B4A", 1.0, "placa"))
    for f in FP:
        if f["lib"].startswith(("MountingHole", "Gateron", "TestPoint")) or f["ref"] in ("SW401", "SW402"):
            continue
        if f["ref"] in ("J301", "J302"):        # jack: body and its collar
            S.append((box(f["x"], f["y"] - 3, f["x"] + 12.2, f["y"] + 3, 0, 5.1), "#2B2925", 1.0, "pecas"))
            S.append((pv.Cylinder(center=(f["x"] - 1.0, -f["y"], G.JACK_Z), direction=(1, 0, 0), radius=2.5, height=2.0),
                      "#B3B2AE", 1.0, "pecas"))
            S.append((pv.Cylinder(center=(f["x"] - 1.9, -f["y"], G.JACK_Z), direction=(1, 0, 0), radius=1.8, height=0.3),
                      "#0E0D0C", 1.0, "pecas"))
            continue
        if f["ref"] == "J201":                  # USB-C shell
            S.append((box(f["x"] - 3.65, f["y"] - 4.47, f["x"] + 3.65, f["y"] + 4.47, 0.1, 3.26), "#B3B2AE", 1.0, "pecas"))
            S.append((box(f["x"] - 3.75, f["y"] - 3.4, f["x"] - 3.6, f["y"] + 3.4, 1.1, 2.3), "#0E0D0C", 1.0, "pecas"))
            continue
        h = f["height"] or {"J401": 2.95, "J201": 3.26, "J301": 5.0, "J302": 5.0, "J202": 5.5, "J101": 4.7}.get(f["ref"], 0.8)
        bx0, by0, bx1, by1 = f["box"]
        col = "#B3B2AE" if f["ref"][0] == "J" else "#2B2925"
        if f["bottom"]:
            S.append((box(bx0, by0, bx1, by1, -1.2 - h, -1.2), col, 1.0, "pecas"))
        else:
            S.append((box(bx0, by0, bx1, by1, 0, h), col, 1.0, "pecas"))
    bx0, by0, bx1, by1, bt = INFO["posicoes"]["bateria"]
    zf = INFO["niveis"]["piso_interno"]
    S.append((box(bx0, by0, bx1, by1, zf, zf + bt), "#5E7FA3", 1.0, "bateria"))
    return S


def add(pl, m, col, op=1.0):
    if col is None:
        pl.add_mesh(m, scalars="rgb", rgb=True, smooth_shading=True, split_sharp_edges=True, opacity=op)
    else:
        pl.add_mesh(m, color=col, smooth_shading=True, split_sharp_edges=True, opacity=op)


def shot(S, name, camera, size=(2400, 1100), parallel=True, scale=None, clip=None, hide=(), offsets=None, zoom=None):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("#F3F1EC")
    for m, col, op, grp in S:
        if grp in hide:
            continue
        if offsets and grp in offsets:
            m = m.translate(offsets[grp], inplace=False)
        if clip:
            if m.n_cells == 1:
                continue                      # a paint skin
            m = m.triangulate().clean()
            cut = None
            for nrm in (clip[0], tuple(-v for v in clip[0])):
                try:
                    c = m.clip_closed_surface(normal=nrm, origin=clip[1])
                except Exception:
                    c = m.clip(normal=nrm, origin=clip[1])
                if c.n_points and c.bounds[0] >= clip[1][0] - 0.01:
                    cut = c
                    break
            if cut is None:
                if m.bounds[0] >= clip[1][0] - 0.01:
                    cut = m
                else:
                    continue
            m = cut
        add(pl, m, col, op)
    pl.camera_position = camera
    if parallel:
        pl.enable_parallel_projection()
        if scale:
            pl.camera.parallel_scale = scale
    if zoom:
        pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(60, 80, 300), focal_point=(126, -50, 0), intensity=0.35))
    pl.screenshot(os.path.join(REN, name))
    pl.close()


def main():
    os.makedirs(REN, exist_ok=True)
    S = scene()
    cx, cy = 126.0, -50.0
    shot(S, "planta.png", [(cx, cy, 500), (cx, cy, 0), (0, 1, 0)], size=(2600, 1100), scale=54)
    # cut along the rows: keep x > 107.7, look from the left (-x) towards +x; the player is on the right
    shot(S, "corte.png", [(-400, cy, 9), (107.7, cy, 9), (0, 0, 1)], size=(2400, 1000), scale=24,
         clip=((-1, 0, 0), (107.7, 0, 0)))
    shot(S, "corte_falante.png", [(-400, cy, 5), (40, cy, 5), (0, 0, 1)], size=(2400, 900), scale=22,
         clip=((-1, 0, 0), (40.0, 0, 0)))       # 3 mm beside the speaker's axis: a rib of the box is on the axis
    shot(S, "isometrico.png", [(cx - 190, cy - 300, 250), (cx, cy + 5, 5), (0, 0, 1)], size=(2400, 1400), parallel=False, zoom=1.35)
    shot(S, "parede.png", [(-400, cy, 4), (0, cy, 4), (0, 0, 1)], size=(2400, 800), scale=22)
    shot(S, "parede_zoom.png", [(-400, -38, 3), (0, -38, 3), (0, 0, 1)], size=(2400, 800), scale=8.5)
    shot(S, "logo.png", [(34, -50, 500), (34, -50, 0), (0, 1, 0)], size=(1500, 1500), scale=52)
    shot(S, "logo_iso.png", [(60, -50 + 90, 90), (22, -50, 14), (0, 0, 1)], size=(2000, 1300), parallel=False, zoom=1.0)
    off = {"tampa": (0, 0, 70), "janela": (0, 0, 70), "knobs": (0, 0, 95), "botoes": (0, 0, 50), "grade": (0, 0, 28),
           "parafusos": (0, 0, 40), "caixa": (0, 0, 44), "falante": (0, 0, 56), "tela": (0, 0, 60), "base": (0, 0, -45),
           "bateria": (0, 0, -22)}
    shot(S, "explodido.png", [(cx - 260, cy - 420, 330), (cx, cy, 15), (0, 0, 1)], size=(2400, 1800), parallel=False,
         offsets=off, zoom=1.15)
    print(sorted(os.listdir(REN)))


if __name__ == "__main__":
    main()
