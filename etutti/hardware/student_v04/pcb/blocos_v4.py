"""Colour block pictures of the placed V4 main board, top and bottom, with the main dimensions (CadQuery venv: matplotlib).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/blocos_v4.py

Reads pcb/posicao_v4.json and pcb/build/partes_v4.json; writes pcb/img/principal_blocos_topo.png and principal_blocos_fundo.png
(the bottom is drawn as seen FROM BELOW: x mirrored, as the JLCPCB preview shows it).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
d = json.load(open(os.path.join(HERE, "posicao_v4.json"), encoding="utf-8"))
parts = {p["ref"]: p for p in json.load(open(os.path.join(HERE, "build", "partes_v4.json"), encoding="utf-8"))}
P = d["pecas"]
x0, y0, x1, y1 = d["contorno"]
USB = {"J201", "U201", "D201", "R201", "R202"}
GROUP = {"P": ("MicroMod (M.2)", "#7F77DD"), "E": ("Energia e carga", "#D85A30"), "F": ("Audio (codec, OUT, IN)", "#1D9E75"),
         "I": ("Interface (tela, botao)", "#BA7517"), "A": ("Amplificador e alto-falante", "#2aa57d"), "R": ("Fileiras (J601..J604)", "#D4537E")}
USB_G = ("USB", "#378ADD")
NAMES = {"J201": "USB-C", "J301": "OUT", "J302": "IN", "J202": "bateria", "J401": "tela", "J501": "alto-falante",
         "SW401": "knob volume", "SW402": "knob registro", "SW403": "Program", "U301": "codec", "U501": "amp", "U202": "carregador",
         "U204": "conversor", "J101": "M.2", "J601": "fil. 1", "J602": "fil. 2", "J603": "fil. 3", "J604": "fil. 4", "U201": "ESD"}


def grp(ref):
    if ref in USB:
        return USB_G
    p = parts.get(ref)
    return GROUP.get(p["sheet"]) if p else None


def draw(side, out):
    fig, ax = plt.subplots(figsize=(8.2, 10.8))
    sgn = 1 if side == "F" else -1
    X = (lambda x: x) if side == "F" else (lambda x: x0 + x1 - x)
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc="#EAF3DE", ec="#3B6D11", lw=1.3))
    c = d["zonas"]["cartao"]
    if side == "B":
        ax.add_patch(Rectangle((X(c[2]), c[1]), c[2] - c[0], c[3] - c[1], fc="#CECBF6", ec="#534AB7", lw=0.8, alpha=0.5))
        ax.text(X((c[0] + c[2]) / 2), (c[1] + c[3]) / 2 + 4, "cartao MicroMod 22 x 22\n(pecas <= 1,9 mm)", ha="center", fontsize=7, color="#3C3489")
    seen = set()
    for ref, p in P.items():
        if p["lado"] != side or ref.startswith("H") and ref[1:].isdigit() or ref == "H101":
            continue
        g = grp(ref)
        if not g:
            continue
        a, b, cc, dd = p["patio"]
        xa, xb = sorted((X(a), X(cc)))
        ax.add_patch(Rectangle((xa, b), xb - xa, dd - b, fc=g[1], ec=g[1], alpha=0.55, lw=0.5))
        seen.add(g)
        if ref in NAMES:
            ax.text((xa + xb) / 2, (b + dd) / 2, NAMES[ref], ha="center", va="center", fontsize=6.5)
    for ref in ("H1", "H2", "H3", "H4", "H101"):
        p = P[ref]
        ax.add_patch(Circle((X(p["x"]), p["y"]), 1.1 if ref != "H101" else 1.35, fc="white", ec="k", lw=0.8))
        ax.text(X(p["x"]) + 1.8, p["y"], "%s (%.1f; %.1f)" % (ref, p["x"], p["y"]), fontsize=6, va="center")
    if side == "F":
        for ref in ("SW401", "SW402"):
            p = P[ref]
            ax.add_patch(Circle((p["x"], p["y"]), 7.5, fc="none", ec="#633806", ls="--", lw=1))
            ax.text(p["x"], p["y"] + 9.2, "knob Ø15", ha="center", fontsize=6, color="#633806")
    fz = d["metricas"]["fenda_do_cabo"]
    xa, xb = sorted((X(fz[0]), X(fz[2])))
    ax.add_patch(Rectangle((xa, fz[1]), xb - xa, fz[3] - fz[1], fc="white", ec="k", lw=0.6, hatch="////"))
    ax.text((xa + xb) / 2, fz[1] - 0.8, "fenda do cabo da tela", ha="center", fontsize=6)
    # dimensions
    ax.annotate("", xy=(x0, y1 + 3.5), xytext=(x1, y1 + 3.5), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((x0 + x1) / 2, y1 + 5.2, "%.2f mm" % (x1 - x0), ha="center", fontsize=8)
    ax.annotate("", xy=(x1 + 4, y0), xytext=(x1 + 4, y1), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(x1 + 5, (y0 + y1) / 2, "%.2f mm" % (y1 - y0), rotation=90, va="center", fontsize=8)
    ux, uy = d["metricas"]["usbc_pads_xy"]
    ax.annotate("USB-C: pads em y %.1f\n(furo na parede esquerda, y 10)" % uy, xy=(X(x0), uy), xytext=(X(x0) + sgn * 8, 2.0 if False else -3.5),
                fontsize=7, arrowprops=dict(arrowstyle="->"), annotation_clip=False)
    mx = d["metricas"]["mouth_x_fileiras"]
    for k, ry in ((1, 74.03), (2, 58.01), (3, 41.99), (4, 25.97)):
        if side == "B":
            ax.text(X(x1) + 1.0, ry + 5.2, "J60%d  y %.2f" % (k, ry), fontsize=6, ha="right", color="#8a2250")
    ax.set_xlim((x0 - 6, x1 + 12) if side == "F" else (x0 - 12, x1 + 6))
    ax.set_ylim(y1 + 8, y0 - 6)
    ax.set_aspect("equal")
    ax.set_title("Placa principal V4 (R8V4, portao P): %s\n(cor clara = peca neste lado; circulos tracejados = knobs)" %
                 ("topo (so os 2 encoders, o furo do modulo e os pads do alto-falante)" if side == "F" else "fundo, visto DE BAIXO (x espelhado): "
                  "tudo o que a JLCPCB monta"), fontsize=9)
    handles = [Rectangle((0, 0), 1, 1, fc=g[1], alpha=0.55) for g in sorted(seen)]
    ax.legend(handles, [g[0] for g in sorted(seen)], loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7, frameon=False)
    ax.grid(True, lw=0.15)
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    draw("F", os.path.join(IMG, "principal_blocos_topo.png"))
    draw("B", os.path.join(IMG, "principal_blocos_fundo.png"))
    print("ok")
