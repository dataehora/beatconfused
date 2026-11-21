"""Pictures of the placed V4 ruler (CadQuery venv: matplotlib, numpy).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/regua/vistas_regua.py

Reads pcb/regua/posicao_regua.json (posiciona_regua.py); writes pcb/regua/img/{regua_planta,regua_corte}.png.
All views are in the ruler frame: u along the row (right), v across (+v = front, towards the player, drawn DOWN) -- the top view,
seen through the board (the parts are on the bottom). Section heights follow case_f2.py / case_t3g.py (z = 0 at row 1's ruler top).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
d = json.load(open(os.path.join(HERE, "posicao_regua.json"), encoding="utf-8"))
OX, OY = d["origem"]
COL = {"U": "#3b78c4", "J": "#d9548a", "C": "#3fa66b", "R": "#3fa66b", "L": "#e08a1e"}
NOTAS = ["G3", "A#3", "C#4", "E4"]      # exemplo: 1a regua da fileira 2 (R5V4); as outras fileiras trocam os nomes, a posicao e a mesma
U5C = "#8a6fd1"
ZR = [0.0, 2.0, 4.0, 7.0]
T, FLOOR = 1.2, -8.1
RAIL_IN, RAIL_OUT = 4.2, 7.0
ROWP = 16.02


def part_color(ref):
    return U5C if ref == "U5" else COL.get(ref[0], "#999")


def plan():
    fig, ax = plt.subplots(figsize=(13, 5.6))
    poly = d["contorno_uv"]
    ax.add_patch(Polygon(poly, closed=True, fc="#e9f2e0", ec="#2f5d1c", lw=1.4, zorder=1))
    for k, uc in enumerate(d["teclas_u"]):
        ax.add_patch(Rectangle((uc - 7, -7), 14, 14, fill=False, ec="#999", ls=":", lw=0.8, zorder=1))
        ax.text(uc, 6.0, "tecla %d  (ex. fil. 2: %s)" % (k + 1, NOTAS[k]), ha="center", va="center", fontsize=7, color="#777")
    for f in d["furos"]:
        ax.add_patch(Circle((f["u"], f["v"]), f["d"] / 2, fc="white", ec="k", lw=0.8, zorder=3))
    for h in d["furos"]:
        if h["tipo"] == "M2":
            ax.add_patch(Circle((h["u"], h["v"]), 3.2, fill=False, ec="#c0392b", ls="--", lw=0.8, zorder=2))
            ax.text(h["u"], h["v"] + 4.4, "M2 (patamar Ø6,4 embaixo)", ha="center", fontsize=6, color="#c0392b")
    for ref, p in d["pecas"].items():
        if ref.startswith(("PEG", "H")):
            continue
        c = p["patio_uv"]
        ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fc=part_color(ref), ec="none", alpha=0.25, zorder=2))
    for pd_ in d["pads"]:
        if pd_["ref"].startswith(("PEG", "H")):
            continue
        w, h = (pd_["h"], pd_["w"]) if round(pd_["rot"]) % 180 == 90 else (pd_["w"], pd_["h"])
        ax.add_patch(Rectangle((pd_["u"] - w / 2, pd_["v"] - h / 2), w, h, fc=part_color(pd_["ref"]), ec="none", alpha=0.9, zorder=4))
    for ref, p in d["pecas"].items():
        if ref.startswith(("PEG", "H")):
            continue
        c = p["patio_uv"]
        ax.text((c[0] + c[2]) / 2, (c[1] + c[3]) / 2, ref, ha="center", va="center", fontsize=6.5, zorder=5, color="k")
    for r, w in d["janelas_plugue"].items():
        ax.add_patch(Rectangle((w[0], w[1]), w[2] - w[0], w[3] - w[1], fill=True, fc="#d9f0ff", ec="#2a7fb8", ls="--", lw=0.8, zorder=0))
        ax.text((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, "plugue\n" + r, ha="center", va="center", fontsize=6.5, color="#1d5d86")
    for nu in (0, 18.5, 37, 55.5, 74):
        ax.text(nu, -8.3 - 4.6 + 3.2 if False else -7.6, "entalhe", ha="center", fontsize=5, color="#555")
    # dimensions
    y0 = 9.6
    ax.annotate("", xy=(0.2, y0), xytext=(73.8, y0), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(37, y0 + 0.7, "73,6 mm (74 nominais menos 0,2 de folga em cada ponta)", ha="center", fontsize=7)
    ax.annotate("", xy=(-3, -7), xytext=(-3, 7), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(-3.3, 0, "14", ha="right", va="center", fontsize=7)
    for ref in ("J1", "J2", "U5"):
        p = d["pecas"][ref]
        ax.text(p["u"], p["patio_uv"][3] + 0.9 if ref == "U5" else p["patio_uv"][1] - 0.5, "u %.1f / v %.2f" % (p["u"], p["v"]), ha="center", fontsize=6, color="#444")
    ax.set_xlim(-8, 82)
    ax.set_ylim(12, -15)
    ax.set_aspect("equal")
    ax.set_xlabel("u (mm) ao longo da fileira")
    ax.set_ylabel("v (mm)  +v = frente (jogador)")
    ax.set_title("Regua universal de 4 teclas, R5V4: vista de cima, em transparencia (todas as pecas estao no FUNDO). "
                 "Azul = TMAG5253, roxo = 74HC595, rosa = SH-6 (J1 entrada, J2 saida: opcao A), laranja = pads do elo soldado (LK1 entrada, LK2 saida), verde = passivos", fontsize=6.5)
    ax.grid(True, lw=0.15)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "regua_planta.png"), dpi=170)
    plt.close(fig)


def section():
    """Three sections: (a) across the row at J1 (v, z) for the four rows; (b) along the row (u, z) at v = -3.95 (the connectors) ; (c) at v = 0 (sensors, pegs)."""
    fig = plt.figure(figsize=(14, 9.5))
    # (a) v-z at u = J1, rows 1..4: the ruler k at v offset -(k-1)*ROWP
    ax = fig.add_subplot(2, 1, 1)
    j1 = d["pecas"]["J1"]
    for r in range(4):
        zt = ZR[r]
        vc = -r * ROWP                                  # row r+1 is behind row r by 16.02 (back = -v)
        ax.add_patch(Rectangle((vc - 7, zt - T), 14, T, fc="#c9a86a", ec="k", lw=0.6))
        for sgn in (-1, 1):
            va, vb = sorted((vc + sgn * RAIL_IN, vc + sgn * RAIL_OUT))
            ax.add_patch(Rectangle((va, FLOOR), vb - va, zt - T - FLOOR, fc="#d8d8d8", ec="#888", lw=0.5))
        # J1 body (4.3 high), pad row, plug window
        v0, v1 = j1["patio_uv"][1] + vc, j1["patio_uv"][3] + vc
        ax.add_patch(Rectangle((v0, zt - T - 4.3), v1 - v0, 4.3, fc="#d9548a", ec="k", lw=0.5, alpha=0.85))
        wv0 = -7 + vc - 4.6
        ax.add_patch(Rectangle((wv0, zt - T - 4.3), 4.6, 4.3, fc="#d9f0ff", ec="#2a7fb8", ls="--", lw=0.8, alpha=0.9))
        # pegs and key body
        ax.add_patch(Rectangle((vc - 0.85, zt - T - 1.5), 1.7, 1.5, fc="#555", ec="none"))
        ax.add_patch(Rectangle((vc - 7, zt), 14, 5.0, fc="#7fb3e8", ec="k", lw=0.4, alpha=0.4))
        ax.text(vc, zt + 6.0, "fileira %d" % (r + 1), ha="center", fontsize=7)
        ax.text(vc, zt - T - 5.1, "pocket %.1f" % (zt - T - FLOOR), ha="center", fontsize=6, color="#444")
    ax.axhline(FLOOR, color="k", lw=1)
    ax.text(-60, FLOOR - 0.6, "piso da bandeja z = -8,1", fontsize=7)
    ax.set_xlim(-62, 10)
    ax.set_ylim(-10.5, 12)
    ax.set_aspect("equal")
    ax.set_title("(a) Corte por J1 (u = %.1f), atravessando as quatro fileiras (atras = -v, a esquerda). Rosa = SH-6 (4,3 mm), azul claro tracejado = onde o plugue entra: "
                 "a trilha (cinza) da fileira de tras, mais alta, precisa de uma janela de ~7 x 2,8 mm" % j1["u"], fontsize=8)
    ax.set_xlabel("v (mm)")
    ax.set_ylabel("z (mm), 0 = topo da regua da fileira 1")
    # (b) u-z along the row at the connector line (v = -3.95): parts hanging below the ruler row 1
    ax = fig.add_subplot(2, 1, 2)
    ax.add_patch(Rectangle((0.2, -T), 73.6, T, fc="#c9a86a", ec="k", lw=0.6))
    for ref, p in d["pecas"].items():
        if ref.startswith(("PEG", "H")):
            continue
        c = p["patio_uv"]
        h = float(p["altura_mm"] or 0.5)
        ax.add_patch(Rectangle((c[0], -T - h), c[2] - c[0], h, fc=part_color(ref), ec="k", lw=0.4, alpha=0.75))
        ax.text((c[0] + c[2]) / 2, -T - h - 0.45, ref, ha="center", fontsize=6)
    for f in d["furos"]:
        if f["tipo"] == "pino da tecla":
            ax.add_patch(Rectangle((f["u"] - 0.85, -T - 1.5), 1.7, 1.5, fc="#555", ec="none"))
    for uc in d["teclas_u"]:
        ax.add_patch(Rectangle((uc - 7, 0), 14, 5.0, fc="#7fb3e8", ec="k", lw=0.4, alpha=0.35))
    ax.axhline(FLOOR, color="k", lw=1)
    ax.add_patch(Rectangle((0.2, FLOOR), 73.6, 1.0, fc="#ddd", ec="none"))
    ax.set_xlim(-2, 76)
    ax.set_ylim(-9, 7)
    ax.set_title("(b) Corte ao longo da regua (projecao de todas as pecas do fundo; alturas: TMAG 0,4, 74HC595 0,9, capacitor 0805 1,4, SH-6 4,3; pinos da tecla 1,5 abaixo). "
                 "Pocket da fileira 1: 6,9 mm entre a regua (z -1,2) e o piso (z -8,1)", fontsize=8)
    ax.set_xlabel("u (mm)")
    ax.set_ylabel("z (mm)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "regua_corte.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    plan()
    section()
    print("wrote regua_planta.png, regua_corte.png")
