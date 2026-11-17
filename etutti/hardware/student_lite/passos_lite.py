"""eTutti Student Lite: pictures for the Lite page (no case, no screen, bottom-side assembly by JLCPCB).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_lite/passos_lite.py

Reuses the Student V2 scene (case/render.py, case/passos.py) and keeps only the board, its parts, the
keys, the grid and the spacers. The parts of the board are split by where they sit:
  fundo   = bottom-side parts (JLCPCB fits them)           modulo = the MicroMod module (fitted at home)
  topo    = top-side small parts + connectors (soldered at home)
  encoders = the two encoders with their shafts (soldered at home)
Writes etutti/studentLite/img/*.jpg and tamanhos.json, ancoras.json.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.normpath(os.path.join(HERE, "..", "student_v02"))
sys.path.insert(0, os.path.join(V2, "case"))
import passos as P          # noqa: E402
import render as R          # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
IMG = os.path.join(REPO, "etutti", "studentLite", "img")
P.IMG = IMG


def lite_scene():
    S = []
    for m, col, op, grp in R.scene():
        if grp in ("tampa", "base", "caixa", "falante", "janela", "tela", "botoes"):
            continue
        if grp == "pecas":
            b = m.bounds
            dx, dy = b[1] - b[0], b[3] - b[2]
            if b[4] < -0.5:
                grp = "modulo" if (dx > 18 and dy > 18) else "fundo"
            elif b[5] > 6.0:
                grp = "encoders"
            else:
                grp = "topo"
        if grp == "knobs":
            grp = "knobs"
        S.append((m, col, op, grp))
    return S


def main():
    os.makedirs(P.PASSOS, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    S = lite_scene()
    cx, cy = 126.0, -50.0
    sizes = {}
    iso = [(cx - 230, cy - 330, 250), (cx, cy + 5, 5), (0, 0, 1)]
    below = [(cx, cy + 40, -420), (cx, cy, -4), (0, -1, 0)]
    left = [(-30, -50 - 190, 150), (36, -48, 4), (0, 0, 1)]
    ALL = {g for _m, _c, _o, g in S}
    A = {"placa", "fundo"}

    def shot(name, cam, shown, new=(), off=None, zoom=1.3, size=(2000, 1200), w=1400):
        P.view(S, name + ".png", cam, size, shown, new=new, offsets=off, zoom=zoom)
        sizes[name] = P.jpg(name, w)

    # exploded view, bottom to top
    off = {"modulo": (0, 0, -34), "fundo": (0, 0, 0), "topo": (0, 0, 14), "encoders": (0, 0, 22), "teclas": (0, 0, 30),
           "espacadores": (0, 0, 52), "grade": (0, 0, 66), "parafusos": (0, 0, 82), "knobs": (0, 0, 78)}
    anchors = {"1": (190, 50, 0), "2": (11, 48, 18), "3": (36, 44.5, 40), "4": (48, 25, -22), "5": (200, 40, 36),
               "6": (170, 34, 52 + 11), "7": (136, 42, 66 + 8), "8": (200.2, 92.5, 82 + 5), "9": (28, 44.5, 78 + 14)}
    a = P.view(S, "lite_explodido.png", [(cx - 300, cy - 520, 150), (cx - 10, cy + 5, 20), (0, 0, 1)], (2400, 1800), ALL, offsets=off,
               zoom=1.5, anchors=anchors)
    sizes["lite_explodido"] = P.jpg("lite_explodido", 1800)
    json.dump(a, open(os.path.join(IMG, "ancoras.json"), "w"), indent=1)

    shot("lite_jlc_fundo", below, {"placa", "fundo"}, new={"placa", "fundo"}, zoom=1.1)
    shot("lite_passo_1", iso, A, new=A, zoom=1.35)                                  # what arrives
    shot("lite_passo_2", left, A | {"topo"}, new={"topo"}, zoom=1.9)                 # small parts + connectors
    shot("lite_passo_3", left, A | {"topo", "encoders", "knobs"}, new={"encoders", "knobs"}, zoom=1.9,
         off={"knobs": (0, 0, 24)})
    shot("lite_passo_4", below, A | {"topo", "encoders", "knobs", "modulo"}, new={"modulo"}, zoom=1.1, off={"modulo": (0, 0, -22)})
    shot("lite_passo_5", iso, A | {"topo", "encoders", "knobs", "modulo", "teclas"}, new={"teclas"}, zoom=1.35,
         off={"teclas": (0, 0, 16)})
    shot("lite_passo_6", iso, ALL, new={"espacadores", "grade", "parafusos"}, zoom=1.35,
         off={"espacadores": (0, 0, 20), "grade": (0, 0, 36), "parafusos": (0, 0, 52)})
    shot("lite_final", iso, ALL, zoom=1.35, w=1800)
    json.dump(sizes, open(os.path.join(IMG, "tamanhos.json"), "w"), indent=1)
    print(json.dumps(sizes))


if __name__ == "__main__":
    main()
