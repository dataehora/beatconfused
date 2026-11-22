"""eTutti Student V4 (R6V4): figures of the ruler-chain connector study (CadQuery venv: matplotlib).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/regua/conectores_r6.py

Writes pcb/regua/img/conectores_{E1,E2,entrada,descartadas,teclado32}.png. Plan = seen from above, back (-v) at the top;
section = along x. Frame of the junction: x = u along ruler A (ruler B starts at u = 74). Notes: row 2's E4 | G4.
Part sizes from LCSC (conferir); footprint 6.76 x 5.20 mm from EasyEDA's H4.3 (the H3.4 has none).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
RL, GAP, T, FLOOR = 74.0, 0.4, 1.2, -8.1
SOCK_W, SOCK_D, SOCK_H = 6.76, 5.20, 3.4
BRIDGE = (18.2, 6.8)
U_OUT, U_IN = 68.1, 74.0 + 5.6
NN = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ROWS = [(1, 89.2, 74.03, 57), (2, 79.95, 58.01, 55), (3, 89.2, 41.99, 56), (4, 79.95, 25.97, 54)]
BOARD_EDGE = 77.5
ZR = {1: 0.0, 2: 2.0, 3: 4.0, 4: 7.0}
GOLD, GRN, ORG, PINK = "#c9a86a", "#2f8f4f", "#e08a1e", "#d9548a"


def note(m):
    return "%s%d" % (NN[m % 12], m // 12 - 1)


def key_circle(ax, x, y, nm, r=7.4, alpha=0.35):
    hi = nm[0] == "C" and "#" not in nm
    hf = nm[0] == "F" and "#" not in nm
    fc = "#9ec5f4" if hi else "#f7c978" if hf else "white"
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#555", lw=1.0, alpha=0.85 if (hi or hf) else alpha, zorder=2))
    ax.text(x, y, nm, ha="center", va="center", fontsize=9, fontweight="bold" if (hi or hf) else "normal", zorder=6)


def ruler(ax, x0):
    ax.add_patch(Rectangle((x0 + 0.2, -7), RL - GAP, 14, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))


def holes_and_sensors(ax, x0):
    for c in range(4):
        uc = 9.25 + 18.5 * c
        for d in (-5.08, 5.08):
            ax.add_patch(Circle((x0 + uc + d, 0), 0.85, fc="#555", ec="none", zorder=3))
        ax.add_patch(Rectangle((x0 + uc - 0.6, -0.9), 1.2, 1.8, fc="#b03030", ec="none", zorder=3))


def junction_plan(ax, title, xlo=40, xhi=108):
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(12, -13)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=8, loc="left")
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)
    ruler(ax, 0)
    ruler(ax, RL)
    holes_and_sensors(ax, 0)
    holes_and_sensors(ax, RL)
    m0 = ROWS[1][3]
    key_circle(ax, 64.75, 0, note(m0 + 9))
    key_circle(ax, RL + 9.25, 0, note(m0 + 12))
    key_circle(ax, 46.25, 0, note(m0 + 6))
    key_circle(ax, RL + 27.75, 0, note(m0 + 15))
    ax.text(xlo + 0.5, -11.9, "régua A (fileira 2)", fontsize=7, color="#2f5d1c")
    ax.text(xhi - 0.5, -11.9, "régua B", fontsize=7, color="#2f5d1c", ha="right")


def sec_axes(ax, x0, x1, title):
    ax.set_xlim(x0, x1)
    ax.set_ylim(-9.5, 5)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=8, loc="left")
    ax.axhline(FLOOR, color="k", lw=1)
    ax.add_patch(Rectangle((x0, FLOOR - 1.2), x1 - x0, 1.2, fc="#ddd", ec="none"))
    ax.text(x0 + 0.5, FLOOR + 0.3, "piso da bandeja z = -8,1 (fileira 1: bolso 6,9 mm)", fontsize=6)
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)
    ax.add_patch(Rectangle((x0, -T), RL - x0 - GAP / 2, T, fc=GOLD, ec="k", lw=0.5))
    ax.add_patch(Rectangle((RL + GAP / 2, -T), x1 - RL, T, fc=GOLD, ec="k", lw=0.5))
    ax.text(RL, 2.5, "E4 | G4 (teclas acima)", fontsize=8, ha="center")


def fig_E1():
    fig, axs = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axs[0]
    junction_plan(ax, "E1 · macho em ângulo (fim de A) -> fêmea em ângulo (início de B), contatos ao longo de y (planta)")
    ax.add_patch(Rectangle((RL - 5.2, -3.4), 4.3, 6.8, fc="#c9a0dc", ec="#6b3a8a", alpha=0.9, zorder=4))
    ax.text(RL - 3.0, 0, "macho", fontsize=6, ha="center", va="center", rotation=90, zorder=7)
    ax.add_patch(Rectangle((RL + 0.9, -3.4), 5.2, 6.8, fc="#6fa0d8", ec="#2a5a9a", alpha=0.9, zorder=4))
    ax.text(RL + 3.5, 0, "fêmea\n(>= 5,2 mm)", fontsize=6, ha="center", va="center", zorder=7)
    ax.add_patch(Circle((RL + 4.17, 0), 1.9, fc="none", ec="red", lw=1.5, zorder=8))
    ax.annotate("bate no furo do pino\nda 1ª tecla de B (G4)", (RL + 4.17, 1.8), (RL + 10, 8.5), fontsize=7, color="red",
                arrowprops=dict(arrowstyle="->", color="red"))
    ax.text(41, 10.8, "faixa livre no eixo: 6,6 mm entre os pinos de E4 e G4; peça hipotética (não existe em estoque)", fontsize=6.5, color="#8a6d00")
    ax = axs[1]
    sec_axes(ax, 60, 92, "corte ao longo de x (v = 0)")
    ax.add_patch(Rectangle((RL - 5.2, -T - 2.0), 4.3, 2.0, fc="#c9a0dc", ec="#6b3a8a"))
    ax.add_patch(Rectangle((RL + 0.9, -T - 2.0), 5.2, 2.0, fc="#6fa0d8", ec="#2a5a9a"))
    for u in (RL - 4.17, RL + 4.17):
        ax.add_patch(Rectangle((u - 0.85, -T - 1.5), 1.7, 1.5, fc="#555", ec="none"))
    ax.text(62, -6.8, "cabe em altura, não em planta: inviável", fontsize=7, color="red")
    fig.suptitle("E1 (ideia literal): não existe a peça de estoque, e a fileira de contatos cai no pino da 1ª tecla de B", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(IMG, "conectores_E1.png"), dpi=110)
    plt.close(fig)


def fig_E2():
    fig, axs = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={"height_ratios": [1.15, 1]})
    ax = axs[0]
    junction_plan(ax, "E2 · fêmea 1x5 (boca para baixo) nas duas pontas, na faixa de trás, + ponte com 2 machos (planta, peças do fundo em transparência)")
    for uc, nm in ((U_OUT, "fêmea OUT (A)"), (U_IN, "fêmea IN (B)")):
        ax.add_patch(Rectangle((uc - SOCK_W / 2, -6.9), SOCK_W, SOCK_D, fc="#6fa0d8", ec="#2a5a9a", alpha=0.9, zorder=4))
        ax.text(uc, -4.3, nm, fontsize=6, ha="center", va="center", zorder=7)
        for i in range(5):
            ax.add_patch(Circle((uc - 2.54 + 1.27 * i, -4.3), 0.3, fc="#a07a20", zorder=5))
    ax.add_patch(Rectangle((RL - BRIDGE[0] / 2, -7.6), BRIDGE[0], BRIDGE[1], fc="#f0d090", ec="#a07a20", alpha=0.55, zorder=3, ls="--"))
    ax.text(RL, -8.6, "ponte (PCB 1,2 mm, 18,2 x 6,8 mm, no painel das réguas)", fontsize=6.5, ha="center", color="#7a5a10")
    ax.text(41, 10.8, "faixa de trás v -6,9..-1,05 livre de pinos (v 0) e sensores (pads até v -1,06); 1,5 mm até C1 e C4. A faixa da frente (3,1 mm; trilho em v +4,2..+7) não comporta 5,2 mm",
            fontsize=6.5, color="#8a6d00")
    ax = axs[1]
    sec_axes(ax, 50, 100, "corte ao longo de x na faixa de trás (v = -4,3), fileira 1 (a mais apertada)")
    zb = -T - SOCK_H - 0.6
    for uc in (U_OUT, U_IN):
        ax.add_patch(Rectangle((uc - SOCK_W / 2, -T - SOCK_H), SOCK_W, SOCK_H, fc="#6fa0d8", ec="#2a5a9a"))
        ax.add_patch(Rectangle((uc - SOCK_W / 2, zb - 1.0), SOCK_W, 1.0, fc="#222", ec="none"))
        for i in range(5):
            ax.add_patch(Rectangle((uc - 2.54 + 1.27 * i - 0.2, zb), 0.4, SOCK_H, fc="#c9a86a", ec="none"))
    ax.add_patch(Rectangle((RL - BRIDGE[0] / 2, zb - 1.0 - T), BRIDGE[0], T, fc=GRN, ec="k", lw=0.5))
    ax.annotate("", (RL + 19, -T), (RL + 19, zb - 1.0 - T), arrowprops=dict(arrowstyle="<->"))
    ax.text(RL + 19.6, -4.6, "6,2 mm\nsob a régua", fontsize=7)
    ax.text(RL + 19.6, -8.6, "folga 0,7", fontsize=7, color="#a03030")
    ax.text(51, -2.0, "fêmea H3,4 (3,4) + 0,6 de pino que sobra + macho (1,0) + ponte (1,2) = 6,2 (conferir)", fontsize=6.5)
    fig.suptitle("E2 (RECOMENDADA): fêmea SHOU HAN C55566451 nas réguas, ponte com machos C55213903", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(IMG, "conectores_E2.png"), dpi=110)
    plt.close(fig)


def fig_entrada():
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axs[0]
    ax.set_xlim(62, 118)
    ax.set_ylim(18, -22)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)
    ax.set_title("planta: placa principal -> 1ª régua das fileiras 2 (régua a 2,45 mm da borda) e 1 (a 11,7 mm)", fontsize=8, loc="left")
    ax.add_patch(Rectangle((62, -22), BOARD_EDGE - 62, 40, fc="#dfeccf", ec="#2f5d1c", lw=1.2, zorder=1))
    ax.text(64, -20.5, "placa principal", fontsize=7, color="#2f5d1c")
    for r, x0, dy in ((2, 79.95, 0.0), (1, 89.2, 16.02)):
        ax.add_patch(Rectangle((x0, dy - 7), 36, 14, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))
        m0 = ROWS[r - 1][3]
        key_circle(ax, x0 + 9.25, dy, note(m0))
        key_circle(ax, x0 + 27.75, dy, note(m0 + 3))
        ax.add_patch(Rectangle((x0 + 5.6 - SOCK_W / 2, dy - 6.9), SOCK_W, SOCK_D, fc="#6fa0d8", ec="#2a5a9a", alpha=0.9, zorder=4))
        ax.text(x0 + 5.6, dy - 4.3, "fêmea IN", fontsize=6, ha="center", va="center", zorder=7)
        ax.add_patch(Rectangle((BOARD_EDGE - 6.15, dy - 4.7), 6.15, 9.4, fc=PINK, ec="k", lw=0.5, alpha=0.8, zorder=4))
        ax.text(BOARD_EDGE - 3.1, dy, "J60%d" % r, fontsize=6, ha="center", va="center", zorder=7)
        ax.plot([BOARD_EDGE + 1, BOARD_EDGE + 6, x0 + 4.0, x0 + 5.6], [dy, dy, dy - 4.3, dy - 4.3], color="#c0392b", lw=2.4, zorder=5)
        ax.text(BOARD_EDGE + 1, dy + 6.8, "pigtail SH -> macho, 25 mm", fontsize=6.5, color="#c0392b")
    ax = axs[1]
    ax.set_xlim(66, 112)
    ax.set_ylim(-20.5, 10)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)
    ax.set_title("corte ao longo de x: os planos das réguas sobem 0 / 2 / 4 / 7 mm", fontsize=8, loc="left")
    ax.add_patch(Rectangle((66, -T), BOARD_EDGE - 66, T, fc=GRN, ec="k", lw=0.5))
    ax.text(68, 0.8, "placa z 0", fontsize=6)
    for r, x0 in ((1, 89.2), (2, 79.95), (3, 89.2), (4, 79.95)):
        z = ZR[r]
        ax.add_patch(Rectangle((x0, z - T), 112 - x0, T, fc=GOLD, ec="k", lw=0.4, alpha=0.7))
        ax.text(111.5, z + 0.3, "fileira %d  z +%.0f" % (r, z), fontsize=6.5, ha="right")
    ax.axhline(FLOOR, color="k", lw=1)
    ax.add_patch(Rectangle((BOARD_EDGE - 6.15, -T - 4.3), 6.15, 4.3, fc=PINK, ec="k", alpha=0.85))
    ax.text(BOARD_EDGE - 3, -T - 2.4, "J60k", fontsize=6, ha="center")
    ax.text(70, -14, "o cabo flexível acompanha o degrau;\numa ponte rígida só serviria à fileira 1", fontsize=7, color="#c0392b")
    fig.suptitle("Entrada placa -> 1ª régua: pigtail de SH-6 cortado (25 mm), plugue SH na principal, macho C55213903 soldado na ponta que entra na fêmea", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(IMG, "conectores_entrada.png"), dpi=110)
    plt.close(fig)


def fig_descartadas():
    fig, axs = plt.subplots(2, 2, figsize=(15, 9))
    for k, (ttl, kind) in enumerate((("E3 · FFC/FPC 1,0 mm com conector ZIF nas duas pontas", "ffc"),
                                     ("E4 · ponte com contatos de mola SMD (BWCD, 2 mm, passo 2,54)", "mola"))):
        ax = axs[0][k]
        junction_plan(ax, ttl + " (planta)", 50, 98)
        if kind == "ffc":
            for xc in (RL - 5, RL + 5.4):
                ax.add_patch(Rectangle((xc - 2, -3.2), 4.0, 6.4, fc="#8a6fd1", ec="k", alpha=0.8, zorder=4))
            ax.plot([RL - 5, RL, RL + 5.4], [4, 6, 4], color="#5b3fb0", lw=3, zorder=5)
            ax.text(52, 10.5, "conector FPC de 6 vias com estoque: não achei (C48735, estoque 0)", fontsize=6.5, color="#a03030")
        else:
            for xc in (U_OUT, U_IN):
                for i in range(5):
                    ax.add_patch(Rectangle((xc - 5.08 + 2.54 * i - 1.0, -7.0), 2.0, 3.0, fc=ORG, ec="k", lw=0.4, alpha=0.9, zorder=4))
            ax.text(52, 10.5, "5 contatos a 2,54 mm = 10 mm por ponta; só pressão, sem retenção própria", fontsize=6.5, color="#a03030")
        ax = axs[1][k]
        sec_axes(ax, 48, 100, ttl.split(" · ")[0] + " (corte ao longo de x)")
        if kind == "ffc":
            for xc in (RL - 5, RL + 5.4):
                ax.add_patch(Rectangle((xc - 2, -T - 2.0), 4.0, 2.0, fc="#8a6fd1", ec="k"))
            ax.plot([RL - 5, RL, RL + 5.4], [-T - 1.0, -T - 6.0, -T - 1.0], color="#5b3fb0", lw=3)
        else:
            for xc in (U_OUT, U_IN):
                ax.add_patch(Rectangle((xc - 6.35, -T - 1.0), 12.7, 1.0, fc=ORG, ec="k", alpha=0.8))
            ax.add_patch(Rectangle((RL - 13, -T - 3.2), 26, 1.2, fc=GRN, ec="k"))
            ax.text(RL, -T - 5.0, "molas apertadas contra almofadas da régua", fontsize=7, ha="center")
    fig.suptitle("Opções descartadas na R6V4 (planta e corte)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(IMG, "conectores_descartadas.png"), dpi=110)
    plt.close(fig)


def fig_teclado32():
    fig, ax = plt.subplots(figsize=(17, 6.6))
    ax.add_patch(Rectangle((2.45, 2.45), BOARD_EDGE - 2.45, 95.1, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))
    ax.text(40, 50, "placa principal\n(interface)", ha="center", va="center", fontsize=10, color="#2f5d1c")
    for r, x0, y, m0 in ROWS:
        for k in range(2):
            xr = x0 + RL * k
            ax.add_patch(Rectangle((xr + 0.2, y - 7), RL - GAP, 14, fc="#9fe0c8", ec="#0e7a5f", lw=1.0, zorder=2))
            for c in range(4):
                key_circle(ax, xr + 9.25 + 18.5 * c, y, note(m0 + 3 * (4 * k + c)), r=6.9, alpha=1.0)
            for uc in (5.6, 68.1):
                ax.add_patch(Rectangle((xr + uc - SOCK_W / 2, y - 6.9), SOCK_W, SOCK_D, fc="#6fa0d8", ec="#2a5a9a", alpha=0.8, zorder=2.5))
        ax.add_patch(Rectangle((x0 + RL - 9.1, y - 7.6), 18.2, 6.8, fc="#f0b040", ec="#a07a20", alpha=0.9, zorder=2.7))
        ax.plot([BOARD_EDGE, BOARD_EDGE + 4, x0 + 5.6], [y, y, y - 4.3], color="#c0392b", lw=2.6, zorder=2.6)
        ax.add_patch(Rectangle((BOARD_EDGE - 4, y - 3), 4, 6, fc=PINK, ec="k", lw=0.4, zorder=3))
        ax.text(BOARD_EDGE - 2, y + 5, "J60%d" % r, fontsize=6.5, ha="center", va="top")
    ax.set_xlim(0, 268)
    ax.set_ylim(100, 0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), jogador embaixo")
    ax.set_title("Student V4 R6V4: 32 teclas, nome da nota em cada tecla (C azul, F laranja). Azul claro = fêmeas das réguas; laranja = ponte (4); "
                 "vermelho = pigtail SH -> macho (4). +16 teclas = +4 pontes", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "conectores_teclado32.png"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    for f in (fig_E1, fig_E2, fig_entrada, fig_descartadas, fig_teclado32):
        f()
    print("ok")
