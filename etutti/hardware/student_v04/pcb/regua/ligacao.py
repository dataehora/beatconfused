"""eTutti Student V4 (R5V4): the ruler-link study, pictures + numbers (CadQuery venv: matplotlib, numpy).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/regua/ligacao.py

Writes pcb/regua/img/{ligacao_A,ligacao_B,ligacao_C,ligacao_D}.png (plan + section of each option: the board -> first ruler link
and the ruler -> ruler link of one row), ligacao_teclado32.png (the 32-key keyboard with every note name, C and F highlighted, the
recommended links drawn) and pcb/regua/ligacao.json (counts, cost, minutes per option and per size 32/48/64/80).
Frame of the panels: x along the instrument (the board's right edge at x = 77.5, row 2's first ruler starts at x = 79.95), v across
(+v = player, drawn DOWN, back = up). Sections use the ruler top of row 1 as z = 0 (pocket 6.9 mm, floor z = -8.1), as vistas_regua.py.
Numbers marked (est.) are estimates, not quotes.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

# ----------------------------------------------------------------------------- geometry (contract, see POSICIONAMENTO.md)
BOARD_EDGE = 77.5
R2X = 79.95                      # row 2 (and 4): first ruler starts here; rows 1, 3: 89.2
RL = 74.0                        # ruler pitch along the row (73.6 board + 0.4 gap)
GAP = 0.4
T, FLOOR = 1.2, -8.1
KEYS_PITCH = 18.5
J_IN, J_OUT = 5.9, 68.1          # u of J1 / J2 (A, C) on the ruler; v = -3.95, mouth -v
LK_IN, LK_OUT = 2.1, 71.9        # u of the solder pads (B, D); pads v -0.4 .. 3.6, 1.0 pitch
LK_V0 = -0.4
PADW, PADH = 1.4, 0.7
GOLD, BLUE, PINK, ORG, GRN, GRY = "#c9a86a", "#3b78c4", "#d9548a", "#e08a1e", "#3fa66b", "#999999"
ROWS = [  # row (1 = front), first ruler x, axis y, first note (MIDI), name
    (1, 89.2, 74.03, 57), (2, 79.95, 58.01, 55), (3, 89.2, 41.99, 56), (4, 79.95, 25.97, 54)]
NN = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note(m):
    return "%s%d" % (NN[m % 12], m // 12 - 1)


# ----------------------------------------------------------------------------- numbers
def numbers():
    out = {"tamanhos": {}}
    for keys in (32, 48, 64, 80):
        n = keys // 16                                  # rulers per row (2, 3, 4, 5)
        out["tamanhos"][keys] = {"reguas_por_fileira": n, "reguas": 4 * n, "elos_placa_regua": 4, "elos_regua_regua": 4 * (n - 1),
                                 "elos_total": 4 + 4 * (n - 1), "pulsos_acesso_aleatorio": 8 * n + 1, "colunas": 4 * n, "sensores_ocupados": keys}
    # option costs (US$) -- (est.) where marked; prices seen: Pololu #5543 (10 cm, 6 pin, double ended) US$ 3.32, #5545 25 cm US$ 4.06,
    # JLCPCB library SH-6 clone C160405 US$ 0.069 (Extended, 3.09 per type per order), LCSC FFC 6P 1.0 mm cables C90533 (7 cm) 0.055
    P = {"cabo_100mm": 3.32, "sh6_clone": 0.069, "ext_tipo": 3.09, "fio_30awg_kit": 4.0, "ffc_cabo": 0.06, "fpc_conector": 0.12,
         "custom_25mm_moq50": 150.0 / 50, "crimp_ferramenta": 30.0, "contatos_caixas_por_cabo": 0.6}
    out["precos"] = P
    opts = {}
    for keys, d in out["tamanhos"].items():
        el, pl = d["elos_regua_regua"], d["elos_placa_regua"]
        r = d["reguas"]
        e = {}
        # A: plug cable on all links, J1 + J2 on every ruler
        e["A_estoque_100mm"] = {"cabos": el + pl, "USD": round((el + pl) * P["cabo_100mm"], 2), "cabe": "nao (sobra de 75 a 88 mm)",
                                "ext_a_mais_regua": 0, "min_montagem": 2 * (el + pl)}
        e["A_sob_medida"] = {"cabos": el + pl, "USD": round(50 * P["custom_25mm_moq50"], 2), "obs": "lote minimo de 50 (referencia Newegg/Alibaba: 50 un. = US$ 152,5 para 300 mm; 15/25 mm nao cotado)",
                             "ext_a_mais_regua": 0, "min_montagem": 1.5 * (el + pl)}
        # B: all soldered: 12 joints per link (5 + 5 wire ends)... 10 joints (5 wires x 2 ends) per link
        e["B_tudo_soldado"] = {"elos": el + pl, "juntas": 10 * (el + pl), "USD": P["fio_30awg_kit"], "ext_a_menos_regua": -1,
                               "min_montagem": round(5.0 * (el + pl), 0), "obs": "J1/J2 saem das reguas e J601..J604 saem da principal"}
        # C: FFC with connectors on both ends of every link
        e["C_FFC_conector"] = {"elos": el + pl, "conectores": 2 * (el + pl), "USD": round(2 * (el + pl) * P["fpc_conector"] + (el + pl) * P["ffc_cabo"], 2),
                               "ext_a_mais_regua": 1, "min_montagem": round(3.0 * (el + pl), 0)}
        # D: cable (custom 25 mm) board->ruler 1 (4 per instrument) + soldered elo in the row
        e["D_misto"] = {"cabos_placa": pl, "elos_soldados": el, "juntas": 10 * el, "USD_cabos_sob_medida_lote50": round(50 * P["custom_25mm_moq50"], 2),
                        "USD_cabos_crimpados_em_casa": round(pl * P["contatos_caixas_por_cabo"] + P["crimp_ferramenta"], 2),
                        "USD_fios": P["fio_30awg_kit"], "min_montagem": round(1.5 * pl + 5.0 * el, 0)}
        opts[keys] = e
    out["opcoes"] = opts
    return out


# ----------------------------------------------------------------------------- drawing helpers
def ruler_rect(ax, x0, v0=-7, v1=7, dashed=False, label=None):
    ax.add_patch(Rectangle((x0 + 0.2, v0), RL - GAP, v1 - v0, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))
    if label:
        ax.text(x0 + 37 if x0 + 37 > ax.get_xlim()[0] else ax.get_xlim()[0] + 1, v1 - 0.8, label, ha="center", va="bottom", fontsize=7, color="#2f5d1c", clip_on=True)


def pads(ax, x, v0, n=5, color=ORG, side=1):
    for i in range(n):
        ax.add_patch(Rectangle((x - PADW / 2, v0 + i - PADH / 2), PADW, PADH, fc=color, ec="none", zorder=5))


def sh_connector(ax, xc, vc, mouth="-v", label="J", plug=True):
    """Pin row centre (xc, vc), body 9.4 x 6.15 behind the pins, plug 7.6 x 5.0 beyond the mouth. mouth '-v' or '+x'."""
    if mouth == "-v":
        ax.add_patch(Rectangle((xc - 4.7, vc - 3.0), 9.4, 6.15, fc=PINK, ec="k", lw=0.5, alpha=0.8, zorder=4))
        if plug:
            ax.add_patch(Rectangle((xc - 3.8, vc - 3.0 - 5.0 - 0.0), 7.6, 5.0, fc="#d9f0ff", ec="#2a7fb8", ls="--", lw=0.8, zorder=3))
    else:
        ax.add_patch(Rectangle((xc - 6.15, vc - 4.7), 6.15, 9.4, fc=PINK, ec="k", lw=0.5, alpha=0.8, zorder=4))
        if plug:
            ax.add_patch(Rectangle((xc, vc - 3.8), 5.0, 7.6, fc="#d9f0ff", ec="#2a7fb8", ls="--", lw=0.8, zorder=3))
    ax.text(xc, vc, label, ha="center", va="center", fontsize=6.5, zorder=6)


def wire(ax, pts, color="#222", lw=1.0, ls="-", z=7):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round")


def smooth(ax, pts, **kw):
    pts = list(pts)
    if (len(pts) - 1) % 3 == 0:
        codes = [Path.MOVETO] + [Path.CURVE4] * (len(pts) - 1)
    else:
        while (len(pts) - 1) % 2:
            pts.append(pts[-1])
        codes = [Path.MOVETO] + [Path.CURVE3] * (len(pts) - 1)
    ax.add_patch(PathPatch(Path(pts, codes), fc="none", **kw))


def setup(ax, x0, x1, title, v0=-14, v1=9):
    ax.set_xlim(x0, x1)
    ax.set_ylim(v1, v0)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=8, loc="left")
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)


def board_side(ax):
    ax.add_patch(Rectangle((60, -14), BOARD_EDGE - 60, 23, fc="#dfeccf", ec="#2f5d1c", lw=1.2, zorder=1))
    ax.text(62, -12.6, "placa principal (fundo, peças)", fontsize=6.5, color="#2f5d1c")


# ----------------------------------------------------------------------------- panels: plan
def plan_board(ax, opt):
    """Board right edge -> first ruler of row 2 (the tight one: ruler 2.55 mm from the edge)."""
    setup(ax, 62, 100, "planta: placa principal → 1ª régua (fileira 2, a mais apertada)")
    board_side(ax)
    ruler_rect(ax, R2X)
    ax.text(R2X + 1, 7.7, "régua 1 (fileira 2)", fontsize=7, color="#2f5d1c")
    if opt in ("A", "D", "Astock"):
        sh_connector(ax, BOARD_EDGE - 3.0, 0, mouth="+x", label="J602")
        sh_connector(ax, R2X + J_IN, -3.95, mouth="-v", label="J1")
        if opt == "Astock":
            smooth(ax, [(82.4, 0), (100, 0), (100, -13), (95, -13), (88, -13), (85.85, -11.5)], ec="#c0392b", lw=2.2, ls="--")
            ax.text(90, 4, "cabo de estoque: 100 mm, sobra 75 mm\n(laço de ~28 mm: não cabe)", fontsize=6.5, color="#c0392b")
        else:
            smooth(ax, [(82.4, 0), (85.0, 0), (85.0, -4.0), (85.0, -7.5), (85.85, -11.5)], ec="#c0392b", lw=2.2)
            ax.text(87, 4.4, "cabo SH-6 sob medida 25 mm", fontsize=6.5, color="#c0392b")
    if opt in ("B",):
        pads(ax, 75.3, -2.0, color=ORG)
        ax.text(70, 5.3, "5 pads na borda da placa (fundo)", fontsize=6.5, color=ORG)
        pads(ax, R2X + LK_IN, LK_V0)
        for i in range(5):
            wire(ax, [(75.3 + 0.7, -2.0 + i), (78, -2.0 + i), (R2X + LK_IN - 0.7, LK_V0 + i)], color="#222")
        ax.text(80, 5.6, "5 fios 28–30 AWG, 7 a 10 mm", fontsize=6.5)
    if opt == "C":
        sh_connector(ax, BOARD_EDGE - 1.5, 0, mouth="+x", label="FPC\nplaca", plug=False)
        ax.add_patch(Rectangle((R2X + 0.2, -3.2), 3.2, 6.4, fc="#8a6fd1", ec="k", lw=0.5, alpha=0.8, zorder=4))
        ax.text(R2X + 1.8, 0, "FPC", fontsize=5.5, ha="center", va="center", zorder=6)
        smooth(ax, [(BOARD_EDGE, 0), (79.2, 6.0), (R2X + 0.2, 0)], ec="#5b3fb0", lw=3.0)
        ax.text(70, 7.8, "jumper FFC 1,0 mm 31 mm (arco entre os conectores, 2,5 mm de vão)", fontsize=6, color="#5b3fb0")


def plan_junction(ax, opt):
    """Ruler 1 end -> ruler 2 start of the same row (in line, 0.4 mm apart)."""
    x1 = R2X + RL
    sp = SPAN[opt]
    setup(ax, x1 - sp, x1 + sp, "planta: régua → régua (mesma fileira, em linha, a 0,4 mm)")
    ruler_rect(ax, R2X)
    ruler_rect(ax, x1)
    ax.text(x1 - sp + 1, 7.5, "régua 1 ←", fontsize=7, color="#2f5d1c")
    ax.text(x1 + sp - 1, 7.5, "→ régua 2", fontsize=7, color="#2f5d1c", ha="right")
    if opt in ("A", "Astock"):
        sh_connector(ax, R2X + J_OUT, -3.95, label="J2")
        sh_connector(ax, x1 + J_IN, -3.95, label="J1")
        if opt == "Astock":
            smooth(ax, [(R2X + J_OUT, -11.5), (R2X + J_OUT + 2, -30), (x1 + J_IN - 2, -30), (x1 + J_IN, -11.5)], ec="#c0392b", lw=2.2, ls="--")
            ax.text(x1 - 29, 8.6, "cabo de 100 mm: sobra 88 mm, laço de ~25 mm\npara trás, sob a régua da fileira de trás", fontsize=6.5, color="#c0392b")
        else:
            smooth(ax, [(R2X + J_OUT, -11.8), (R2X + J_OUT + 1.5, -14.8), (x1 + J_IN - 1.5, -14.8), (x1 + J_IN, -11.8)], ec="#c0392b", lw=2.2)
            ax.text(x1 - 12, -12.2, "cabo 15 mm", fontsize=6.5, color="#c0392b")
    if opt in ("B", "D"):
        pads(ax, R2X + LK_OUT, LK_V0)
        pads(ax, x1 + LK_IN, LK_V0)
        for i in range(5):
            wire(ax, [(R2X + LK_OUT + 0.7 - 0.7, LK_V0 + i), (x1 + LK_IN + 0.7 - 0.7, LK_V0 + i)], color="#222", lw=1.6)
        ax.text(x1 - 6, 8.2, "elo: 5 fios 7 mm", fontsize=6.5)
        ax.add_patch(Rectangle((x1 - 1.0, -7), 2.0, 4.3, fc="white", ec="#555", ls=":", lw=0.8, zorder=2))
        ax.text(x1, -8.0, "entalhe/poste", fontsize=5.5, ha="center")
    if opt == "C":
        for xc, side in ((R2X + 68.0, 1), (x1 + 6.0, -1)):
            ax.add_patch(Rectangle((xc - 2.0, -3.2), 4.0, 6.4, fc="#8a6fd1", ec="k", lw=0.5, alpha=0.8, zorder=4))
        smooth(ax, [(R2X + 70.0, 0), (x1, 5.5), (x1 + 4.0, 0)], ec="#5b3fb0", lw=3.0)
        ax.text(x1 - 29, 7.5, "conectores FPC com a boca um para o outro: jumper FFC 31 mm em arco", fontsize=6, color="#5b3fb0")


# ----------------------------------------------------------------------------- panels: section
def sec_base(ax, x0, x1, ztop=0.0):
    ax.set_xlim(x0, x1)
    ax.set_ylim(-9.5, 6)
    ax.set_aspect("equal")
    ax.axhline(FLOOR, color="k", lw=1)
    ax.add_patch(Rectangle((x0, FLOOR - 1.2), x1 - x0, 1.2, fc="#ddd", ec="none"))
    ax.text(x0 + 0.5, FLOOR + 0.3, "piso da bandeja z = −8,1 (fileira 1: bolso 6,9 mm)", fontsize=6)
    ax.tick_params(labelsize=6)
    ax.grid(True, lw=0.15)


def sec_board(ax, opt):
    """Along x at v = 0 (row 1's z levels; row 2 is +2 mm: the margins grow)."""
    sec_base(ax, 66, 100)
    ax.set_title("corte pelo eixo x: placa → 1ª régua", fontsize=8, loc="left")
    ax.add_patch(Rectangle((66, -T), BOARD_EDGE - 66, T, fc="#2f8f4f", ec="k", lw=0.5))
    ax.text(70, 0.6, "placa 1,2", fontsize=6)
    ax.add_patch(Rectangle((R2X + 0.2, -T), RL, T, fc=GOLD, ec="k", lw=0.5))
    ax.text(R2X + 8, 0.6, "régua 1,2", fontsize=6)
    ax.add_patch(Rectangle((R2X + 0.2, 0), 14, 5, fc="#7fb3e8", ec="k", lw=0.3, alpha=0.3))
    if opt in ("A", "D", "Astock"):
        ax.add_patch(Rectangle((BOARD_EDGE - 6.15, -T - 4.3), 6.15, 4.3, fc=PINK, ec="k", lw=0.5, alpha=0.85))
        ax.add_patch(Rectangle((BOARD_EDGE, -T - 4.3), 5.0, 3.9, fc="#d9f0ff", ec="#2a7fb8", ls="--", lw=0.8))
        ax.text(BOARD_EDGE - 3, -T - 2.4, "J602", fontsize=6, ha="center")
        ax.text(BOARD_EDGE + 2.5, -T - 6.3, "plugue 7,6 x 5,0 x 3,9\nsob a ponta da régua", fontsize=6, ha="center")
        smooth(ax, [(82.4, -T - 2.2), (86, -T - 2.2), (88, -T - 3.0)], ec="#c0392b", lw=2.0)
    if opt == "B":
        for i in range(2):
            ax.add_patch(Rectangle((74.6, -T - 0.25), 1.4, 0.25, fc=ORG, ec="none"))
        ax.add_patch(Rectangle((R2X + LK_IN - 0.7, -T - 0.25), 1.4, 0.25, fc=ORG, ec="none"))
        wire(ax, [(75.3, -T - 0.4), (79, -T - 1.2), (R2X + LK_IN, -T - 0.4)], lw=2.0)
        ax.text(76, -T - 3.0, "fio 0,6 + solda: ≈ 1 mm abaixo\nda régua (bolso 6,9: sobram 5,9)", fontsize=6)
    if opt == "C":
        ax.add_patch(Rectangle((BOARD_EDGE - 3.5, -T - 2.0), 3.5, 2.0, fc="#8a6fd1", ec="k", lw=0.5, alpha=0.8))
        ax.add_patch(Rectangle((R2X + 0.2, -T - 2.0), 3.5, 2.0, fc="#8a6fd1", ec="k", lw=0.5, alpha=0.8))
        smooth(ax, [(BOARD_EDGE, -T - 1.0), (79.2, -T - 6.5), (R2X + 0.2, -T - 1.0)], ec="#5b3fb0", lw=3.0)
        ax.text(70, -T - 7.2, "FFC 31 mm: arco de ~5 mm para baixo", fontsize=6)
    ax.set_xlabel("x (mm)", fontsize=6)
    ax.set_ylabel("z (mm)", fontsize=6)


def sec_junction(ax, opt):
    x1 = R2X + RL
    sec_base(ax, x1 - SPAN[opt], x1 + SPAN[opt])
    ax.set_title("corte ao longo da fileira, na junção (v ≈ 1,6; no A e no C, na faixa dos conectores)", fontsize=8, loc="left")
    ax.add_patch(Rectangle((R2X + 0.2, -T), RL - GAP, T, fc=GOLD, ec="k", lw=0.5))
    ax.add_patch(Rectangle((x1 + 0.2, -T), RL - GAP, T, fc=GOLD, ec="k", lw=0.5))
    ax.add_patch(Rectangle((x1 - 0.2, FLOOR), 0.4, 0.0, fc="k"))
    ax.add_patch(Rectangle((x1 - 1.0, FLOOR), 2.0, 5.0, fc="#bbb", ec="#555", lw=0.5, alpha=0.6))
    ax.text(x1, FLOOR + 5.6, "poste/\nnervura", fontsize=5.5, ha="center")
    for xp in (R2X + 69.83, R2X + 70.7, x1 + 4.17):
        pass
    for u in (R2X + 74 - 4.17, x1 + 4.17):
        ax.add_patch(Rectangle((u - 0.85, -T - 1.5), 1.7, 1.5, fc="#555", ec="none"))
    ax.text(x1 + 4.2, -T - 2.0, "pino", fontsize=5.5, ha="center")
    if opt in ("A", "Astock"):
        for xc in (R2X + J_OUT, x1 + J_IN):
            ax.add_patch(Rectangle((xc - 4.7, -T - 4.3), 9.4, 4.3, fc=PINK, ec="k", lw=0.5, alpha=0.8))
        if opt == "A":
            smooth(ax, [(R2X + J_OUT, -T - 2.2), (R2X + J_OUT + 1.5, -T - 7.5), (x1 + J_IN - 1.5, -T - 7.5), (x1 + J_IN, -T - 2.2)], ec="#c0392b", lw=2.0)
            ax.text(x1 - 10, -T - 8.6, "cabo 15 mm: alça de ~3,6 mm", fontsize=6)
        else:
            smooth(ax, [(R2X + J_OUT, -T - 2.2), (R2X + J_OUT + 4, -T - 18), (x1 + J_IN - 4, -T - 18), (x1 + J_IN, -T - 2.2)], ec="#c0392b", lw=2.0, ls="--")
            ax.text(x1 - 28, -9.2, "alça de ~20 mm de fundo > bolso (6,9): não cabe", fontsize=6, color="#c0392b")
    if opt in ("B", "D"):
        for xc in (R2X + LK_OUT, x1 + LK_IN):
            ax.add_patch(Rectangle((xc - 0.7, -T - 0.25), 1.4, 0.25, fc=ORG, ec="none"))
        wire(ax, [(R2X + LK_OUT, -T - 0.4), (x1 + LK_IN, -T - 0.4)], lw=2.4)
        ax.text(x1 - 12, -T - 3.2, "elo: fio sobre os pads, ≈ 1 mm abaixo da régua", fontsize=6)
    if opt == "C":
        for xc in (R2X + 68.0, x1 + 6.0):
            ax.add_patch(Rectangle((xc - 2.0, -T - 2.0), 4.0, 2.0, fc="#8a6fd1", ec="k", lw=0.5, alpha=0.8))
        smooth(ax, [(R2X + 70.0, -T - 1.0), (x1, -T - 8.5), (x1 + 4.0, -T - 1.0)], ec="#5b3fb0", lw=3.0)
        ax.text(x1 - 25, -T - 9.0, "FFC em arco por baixo (cola nas nervuras?)", fontsize=6)
    ax.set_xlabel("x (mm)", fontsize=6)


SPAN = {"A": 22, "Astock": 30, "B": 16, "C": 22, "D": 16}
NAMES = {"A": "A · cabos SH-6 prontos, plugue nas duas pontas (15 mm entre réguas, 25 mm da placa)",
         "Astock": "A (estoque) · o mais curto vendido pronto: 100 mm (Pololu #5543, Pimoroni 100 mm)",
         "B": "B · tudo soldado: pads na borda da placa e nas pontas das réguas, fio de 28–30 AWG (sem conector)",
         "C": "C · FFC/FPC 1,0 mm com conector ZIF nas duas pontas (jumper de 31 mm, o mais curto Molex 150390201)",
         "D": "D · misto (RECOMENDADA): cabo SH-6 de 25 mm da placa à 1ª régua + elo soldado dentro da fileira"}


def option_figure(opt):
    fig, axs = plt.subplots(2, 2, figsize=(16, 9.5))
    plan_board(axs[0][0], opt)
    plan_junction(axs[0][1], opt)
    sec_board(axs[1][0], opt)
    sec_junction(axs[1][1], opt)
    fig.suptitle(NAMES[opt], fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(IMG, "ligacao_%s.png" % opt), dpi=110)
    plt.close(fig)


# ----------------------------------------------------------------------------- the keyboard with names and the links
def keyboard():
    fig, ax = plt.subplots(figsize=(17, 6.6))
    ax.add_patch(Rectangle((2.45, 2.45), BOARD_EDGE - 2.45, 95.1, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))
    ax.text(40, 50, "placa principal\n(interface)", ha="center", va="center", fontsize=10, color="#2f5d1c")
    for r, x0, y, m0 in ROWS:
        for k in range(2):
            xr = x0 + RL * k
            ax.add_patch(Rectangle((xr + 0.2, y - 7), RL - GAP, 14, fc="#9fe0c8", ec="#0e7a5f", lw=1.0, zorder=2))
            for c in range(4):
                col = 4 * k + c
                m = m0 + 3 * col
                nm = note(m)
                xc = xr + 9.25 + 18.5 * c
                hi = nm.startswith("C") and "#" not in nm
                hf = nm.startswith("F") and "#" not in nm
                fc = "#9ec5f4" if hi else "#f7c978" if hf else "white"
                ax.add_patch(Circle((xc, y), 6.9, fc=fc, ec="#222", lw=1.2 if (hi or hf) else 0.7, zorder=3))
                ax.text(xc, y, nm, ha="center", va="center", fontsize=9 if (hi or hf) else 8, fontweight="bold" if (hi or hf) else "normal", zorder=4)
            # elo
        yb = y - 3.95
        # board -> ruler 1: cable plug (red) ; ruler1 -> ruler2: soldered elo (orange) at the pads
        ax.plot([BOARD_EDGE, x0 + 5.9], [y, y - 3.95], color="#c0392b", lw=2.4, zorder=2.6)
        ax.add_patch(Rectangle((x0 + 5.9 - 4.7, y - 7.0), 9.4, 6.15, fc=PINK, ec="k", lw=0.4, alpha=0.5, zorder=2.5))
        ax.text(x0 + 5.9, y - 5.5, "J1", fontsize=6, ha="center", zorder=2.7)
        ax.add_patch(Rectangle((BOARD_EDGE - 4, y - 3.0), 4.0, 6.0, fc=PINK, ec="k", lw=0.4, zorder=3))
        ax.text(BOARD_EDGE - 2, y + 5, "J60%d" % r, fontsize=6.5, ha="center", va="top")
        xj = x0 + RL
        ax.plot([x0 + LK_OUT, xj + LK_IN], [y + 1.6 + 1.5, y + 1.6 + 1.5], color=ORG, lw=3.5, zorder=6)
        ax.text(x0 + 148 + 2, y, "fileira %d  %s–%s" % (r, note(m0), note(m0 + 3 * 7 + 0) if False else note(m0 + 21)), fontsize=8, va="center")
    ax.set_xlim(0, 268)
    ax.set_ylim(100, 0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), jogador embaixo")
    ax.set_title("Student V4 R5V4: 32 teclas (8 réguas cheias, vista de cima). Azul = C, laranja = F. "
                 "Vermelho = cabo SH-6 de 25 mm (placa → 1ª régua, 4); laranja = elo soldado (régua → régua, 4). Cada módulo de +16 teclas acrescenta 4 elos soldados", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "ligacao_teclado32.png"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    n = numbers()
    json.dump(n, open(os.path.join(HERE, "ligacao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for o in ("A", "Astock", "B", "C", "D"):
        option_figure(o)
    keyboard()
    print(json.dumps(n["tamanhos"], ensure_ascii=False))
    print("ok")
