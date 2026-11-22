"""eTutti Student V4 (R7V4): estudo da ligacao "H" (cabo SH de estoque, nada soldado, nada a mais na base). So ESTUDO: nao muda esquema,
posicionamento, regua nem placa. Numeros e figuras (CadQuery venv: matplotlib):

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/regua/ligacao_h_r7.py

Escreve pcb/regua/ligacao_h_r7.json e pcb/regua/img/h_pinagem_r7.png, h_teclado32_r7.png, h_juncao_r7.png (planta e corte do elo),
(R10V4: a figura do microfone saiu; o ME 3 deixou de ser referencia). Reutiliza as funcoes de desenho de conectores_r6.py (nome da nota em cada tecla; C azul, F laranja).

Dados de fabricante usados (JST, eSR_SZ.pdf, lido em 22 nov 2026):
  cabecalho SM06B-SRSS-TB (lateral, SMT): altura 2,95 mm, profundidade 4,85, B = 8,0 (6 vias), footprint 5,55 +- 0,1 de fundo;
  BM06B-SRSS-TB (topo): altura 4,9, profundidade 2,9; soquete/plugue 06SR-3S: 7,0 x 3,6 x ~2,45; fio AWG 30, 7 fios, isolante
  OD 0,54-0,58 mm; corrente 0,7 A; contato 20 mOhm inicial, 40 mOhm depois de ensaio.
O desenho nao traz raio de dobra: regra adotada R >= 6 mm (~10 x OD), minimo absoluto estatico 3 mm  (conferir).
"""
import importlib.util
import json
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
spec = importlib.util.spec_from_file_location("c6", os.path.join(HERE, "conectores_r6.py"))
c6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c6)
RL, T, ROWS, note, key_circle = c6.RL, c6.T, c6.ROWS, c6.note, c6.key_circle

# ---------------------------------------------------------------- constantes do estudo
HDR_H, HDR_D, HDR_B, FOOT_D = 2.95, 4.85, 8.0, 5.55      # SM06B-SRSS-TB (JST)
PLUG_W, PLUG_H = 7.0, 3.6                                 # 06SR-3S (JST)
R_MIN, R_ABS = 6.0, 3.0                                   # raio de dobra (regra adotada / minimo estatico)
STUB = 5.0                                                # reta depois do plugue antes da dobra
PLUG_BACK = 2.5                                           # o comprimento do cabo e medido ate a face do plugue: tiro 2 x 2,5 (conferir)
U_IN, U_OUT = 5.9, 68.1
VH = -4.3                                                 # eixo do cabecalho na faixa de tras (v)
BOARD_EDGE, J_X = 77.5, 77.4
POCKET = {1: 6.9, 2: 8.9, 3: 10.9, 4: 13.9}


def free_len(L):
    return L - 2 * PLUG_BACK


def loop_u(d, Lfree):
    """Elo em U (as duas bocas para o mesmo lado, distancia d entre eixos): cabo = 2 s + pi r + (d - 2 r), r = d/2 se d < 2 R_MIN.
    Devolve (profundidade do U alem da boca, s, r)."""
    r = max(d / 2.0, R_MIN) if d < 2 * R_MIN else R_MIN
    r = d / 2.0 if d < 2 * R_MIN else r
    s = (Lfree - math.pi * r - (d - 2 * r)) / 2.0
    return s + r, s, r


def study():
    out = {}
    d = (c6.RL + U_IN) - U_OUT                             # 74,0 + 5,9 - 68,1 = 11,8
    out["d_entre_reguas_mm"] = round(d, 2)
    for L, nm in ((50.8, "50,8 (2 pol)"), (101.6, "101,6 (4 pol)")):
        Lf = free_len(L)
        dep, s, r = loop_u(d, Lf)
        out["elo_" + nm] = {"comprimento_livre_mm": round(Lf, 1), "caminho_minimo_mm": round(2 * STUB + math.pi * d / 2, 1),
                            "sobra_mm": round(Lf - (2 * STUB + math.pi * d / 2), 1), "profundidade_do_U_alem_da_boca_mm": round(dep, 1),
                            "reta_s_mm": round(s, 1), "raio_mm": round(r, 2)}
    # placa -> 1a regua: J60k (x 77,4, boca +x) ate o IN (x0 + 5,9, boca -y, 4,3 atras do eixo da fileira)
    rows = {}
    for r_, x0, y, m0 in ROWS:
        dx = abs((x0 + U_IN) - J_X)
        dy = abs(VH)
        path = dx + dy + 2 * STUB                            # caminho minimo manhattan com uma reta de 5 mm em cada plugue
        rows[r_] = {"x0": x0, "dx": round(dx, 1), "dy": dy, "caminho_minimo_mm": round(path, 1),
                    "sobra_50,8": round(free_len(50.8) - path, 1), "sobra_101,6": round(free_len(101.6) - path, 1)}
    out["placa_1a_regua"] = rows
    # onde pôr o OUT para o cabo de 50,8 quase esticado (U de profundidade minima): d = Lfree - 2 s - ... resolve d
    # 2 STUB + pi r + (d - 2 r) = Lfree com r = R_MIN -> d = Lfree - 2 STUB - (pi - 2) R_MIN
    d_best = free_len(50.8) - 2 * STUB - (math.pi - 2) * R_MIN
    out["d_para_cabo_50,8_sem_folga_mm"] = round(d_best, 1)
    out["u_OUT_para_esse_d"] = round(c6.RL + U_IN - d_best, 1)
    # queda de tensao (corrente de 1 sensor ligado ~2,6 mA por fileira, 2 contatos por elo, fio 30 AWG 0,34 ohm/m, contato 20-40 mohm)
    for nm, n_link in (("32 teclas (1 elo placa->1 + 1 elo entre reguas)", 2),):
        Rlink = 2 * 0.040 + 0.34 * 0.0458                     # 2 contatos a 40 mOhm + 45,8 mm de fio
        out["queda_GND_mV_por_pino"] = round(2.6e-3 * n_link * Rlink * 1e3, 2)
        out["queda_GND_mV_P9_dois_pinos"] = round(2.6e-3 * n_link * Rlink / 2 * 1e3, 2)
    out["capacitancia_cabo_pF"] = round(1.0 * 0.1 * (45.8 + 45.8), 1)   # 1 pF/cm
    return out


# ------------------------------------------------------------------ figura 1: pinagem e cabos
P6_ATUAL = ["+3V3", "GND", "OUT", "CLK", "DATA", "NC"]
P6S = ["+3V3", "GND", "OUT", "GND", "CLK", "DATA"]
P9 = ["GND", "+3V3", "OUT", "CLK", "DATA", "CLK", "OUT", "+3V3", "GND"]
COL = {"+3V3": "#d9534f", "GND": "#333333", "OUT": "#2f7fbf", "CLK": "#e0a020", "DATA": "#2f9f5f", "NC": "#bbbbbb"}


def severidade(a, b):
    if a == b or "NC" in (a, b):
        return 0
    if {a, b} == {"+3V3", "GND"}:
        return 9
    if "+3V3" in (a, b):
        return 3
    return 2


def pin_column(ax, x, pins, title, ymax):
    ax.text(x, ymax + 0.9, title, ha="center", fontsize=8, fontweight="bold")
    n = len(pins)
    for k, nm in enumerate(pins):
        y = ymax - k
        ax.add_patch(Rectangle((x - 0.9, y - 0.4), 1.8, 0.8, fc=COL[nm], ec="k", lw=0.5, alpha=0.9))
        ax.text(x, y, "%d %s" % (k + 1, nm), color="w" if nm != "NC" else "k", ha="center", va="center", fontsize=6.5)
    return n


def fig_pinagem():
    cases = [("6 vias, pinagem de hoje (1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 DADO, 6 NC)", P6_ATUAL),
             ("6 vias PROTEGIDA P6s (1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO)", P6S),
             ("9 vias SIMETRICA P9 (1 e 9 GND, 2 e 8 +3V3, 3 e 7 OUT, 4 e 6 CLK, 5 DADO)", P9)]
    fig, axs = plt.subplots(3, 2, figsize=(15, 13))
    for i, (ttl, pins) in enumerate(cases):
        n = len(pins)
        for j, rev in enumerate((False, True)):
            ax = axs[i][j]
            ax.set_xlim(-6, 6)
            ax.set_ylim(-1.2, n + 1.2)
            ax.axis("off")
            ymax = n - 1
            pin_column(ax, -3.2, pins, "saída (OUT) da régua A", ymax)
            pin_column(ax, 3.2, pins, "entrada (IN) da régua B", ymax)
            worst = 0
            bad = []
            for k in range(n):
                k2 = (n - 1 - k) if rev else k
                a, b = pins[k], pins[k2]
                sv = severidade(a, b)
                worst = max(worst, sv)
                col = "#2e7d32" if sv == 0 else ("#c62828" if sv == 9 else "#ef6c00")
                ax.plot([-2.3, 2.3], [ymax - k, ymax - k2], color=col, lw=1.8 if sv else 1.2, alpha=0.9)
                if sv:
                    bad.append("%s-%s" % (a, b))
            tipo = "cabo INVERTIDO (JST A..A, Pimoroni): pino k liga ao pino %d-k" % (n + 1) if rev else "cabo RETO 1:1 (JST A..B): pino k liga ao pino k"
            if worst == 0:
                res = "FUNCIONA (todas as ligações coincidem; alimentação nunca trocada)"
                rc = "#2e7d32"
            elif worst == 9:
                res = "INVERTE a alimentação (+3V3 em GND): PROIBIDO"
                rc = "#c62828"
            else:
                res = "NÃO funciona, mas sem dano: alimentação não é invertida; liga %s (via resistores em série)" % (", ".join(sorted(set(bad))))
                rc = "#ef6c00"
            ax.set_title(("%s\n%s" % (ttl, tipo)) if True else tipo, fontsize=7.5, loc="left")
            ax.text(0, -0.9, res, ha="center", fontsize=8, color=rc, fontweight="bold")
    fig.suptitle("R7V4 · ordem dos pinos: cabo reto (1:1) x invertido (1 <-> 6) com cada pinagem. Verde = mesma rede; laranja = rede diferente; vermelho = alimentação invertida", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(IMG, "h_pinagem_r7.png"), dpi=100)
    plt.close(fig)


# ------------------------------------------------------------------ figura 2: planta das 32 teclas com os cabos
def u_path(x0, y0, x1, y1, depth):
    """polilinha suave: sai para tras (menor y) 'depth' mm das duas bocas e passa por baixo (U em planta)."""
    r = abs(x1 - x0) / 2.0
    s = depth - r
    pts = [(x0, y0), (x0, y0 - s)]
    n = 24
    xc = (x0 + x1) / 2.0
    for i in range(n + 1):
        a = math.pi * i / n
        pts.append((xc - r * math.cos(a), y0 - s - r * math.sin(a)))
    pts.append((x1, y1 - s))
    pts.append((x1, y1))
    return pts


def fig_teclado32(st):
    fig, ax = plt.subplots(figsize=(18, 7.4))
    ax.add_patch(Rectangle((2.45, 2.45), BOARD_EDGE - 2.45, 95.1, fc="#e9f2e0", ec="#2f5d1c", lw=1.2, zorder=1))
    ax.text(40, 50, "placa principal\n(interface)\nJ601..J604 na borda", ha="center", va="center", fontsize=10, color="#2f5d1c")
    dep = st["elo_50,8 (2 pol)"]["profundidade_do_U_alem_da_boca_mm"]
    for r, x0, y, m0 in ROWS:
        yh = y + VH
        for k in range(2):
            xr = x0 + RL * k
            ax.add_patch(Rectangle((xr + 0.2, y - 7), RL - 0.4, 14, fc="#9fe0c8", ec="#0e7a5f", lw=1.0, zorder=2))
            for c in range(4):
                key_circle(ax, xr + 9.25 + 18.5 * c, y, note(m0 + 3 * (4 * k + c)), r=6.9, alpha=1.0)
            for uc, nm in ((U_IN, "IN"), (U_OUT, "OUT")):
                ax.add_patch(Rectangle((xr + uc - 4.7, yh - 2.9), 9.4, 5.8, fc="#6fa0d8", ec="#2a5a9a", alpha=0.85, zorder=2.5))
                ax.text(xr + uc, yh, nm, fontsize=6, ha="center", va="center", zorder=7)
        # elo entre as duas reguas: U para tras (menor y), 50,8 mm
        xo = x0 + U_OUT
        xi = x0 + RL + U_IN
        pts = u_path(xo, yh - 2.9 - 2.45, xi, yh - 2.9 - 2.45, dep)
        xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
        ax.plot(xs_, ys_, color="#d35400", lw=2.4, zorder=2.6, ls="--")
        if min(ys_) < 2.0:
            ax.plot([x for x, y_ in pts if y_ < 2.0], [y_ for x, y_ in pts if y_ < 2.0], color="red", lw=3.2, zorder=2.7)
            ax.text(xo + 14, 6.0, "U de %.1f mm sai do case: só há %.1f mm até a parede" % (dep, yh - 2.9 - 2.45 - 2.0), fontsize=7, color="red", va="bottom")
        # placa -> 1a regua
        xin = x0 + U_IN
        ax.plot([J_X + 2, xin + 1.5, xin + 1.5, xin], [y, y, yh - 2.9 - 4, yh - 2.9], color="#c0392b", lw=2.4, zorder=2.6, ls="-")
        ax.add_patch(Rectangle((BOARD_EDGE - 3, y - 4.7), 3, 9.4, fc="#d9548a", ec="k", lw=0.4, zorder=3))
        ax.text(BOARD_EDGE - 1.5, y + 5.2, "J60%d" % r, fontsize=6.5, ha="center", va="top")
    ax.axhline(2.0, color="k", lw=1.5)
    ax.text(10, 1.2, "parede do case (y = 2)", fontsize=7, va="bottom")
    ax.set_xlim(0, 268)
    ax.set_ylim(100, -4)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), jogador embaixo")
    ax.set_title("Student V4 R7V4, ligação H, 32 teclas (nome da nota em cada tecla; C azul, F laranja).\n"
                 "Azul = cabeçalhos SH IN/OUT embaixo das réguas (boca para trás); vermelho = cabo placa -> 1ª régua (50,8 mm); tracejado laranja = elo entre réguas "
                 "(50,8 mm, U de %.1f mm para trás, por baixo da régua da fileira de trás)" % dep, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "h_teclado32_r7.png"), dpi=100)
    plt.close(fig)


# ------------------------------------------------------------------ figura 3: junção (planta + corte) da fileira 1 (a mais rasa)
def fig_juncao(st):
    fig, axs = plt.subplots(1, 3, figsize=(19, 6.4), gridspec_kw={"width_ratios": [1.5, 1.0, 1.0]})
    dep = st["elo_50,8 (2 pol)"]["profundidade_do_U_alem_da_boca_mm"]
    # (a) planta, fileira 2 (E4 | G4 como na R6V4)
    ax = axs[0]
    c6.junction_plan(ax, "planta da junção E4 | G4 (fileira 2): cabeçalho SM06B embaixo (azul), plugue 7,0 x 3,6 (verde), elo de 50,8 mm", 40, 108)
    ax.set_ylim(22, -34)
    for xc, nm in ((U_OUT, "OUT (A)"), (RL + U_IN, "IN (B)")):
        ax.add_patch(Rectangle((xc - 4.7, -6.9), 9.4, FOOT_D, fc="#6fa0d8", ec="#2a5a9a", alpha=0.9, zorder=4))
        ax.add_patch(Rectangle((xc - PLUG_W / 2, -6.9 - 2.45), PLUG_W, 2.45, fc="#8fd18f", ec="#2e7d32", alpha=0.95, zorder=4))
        ax.text(xc, -4.1, nm, fontsize=6.5, ha="center", va="center", zorder=7)
    pts = u_path(U_OUT, -9.35, RL + U_IN, -9.35, dep)
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#d35400", lw=2.6, zorder=6)
    uo2 = st["u_OUT_para_esse_d"]
    ax.add_patch(Rectangle((uo2 - 4.7, -6.9), 9.4, FOOT_D, fc="none", ec="#1b5e20", ls="--", lw=1.4, zorder=6))
    ax.add_patch(Rectangle((uo2 - PLUG_W / 2, -6.9 - 2.45), PLUG_W, 2.45, fc="none", ec="#1b5e20", ls="--", lw=1.4, zorder=6))
    ax.text(uo2, -4.1, "OUT'", fontsize=6.5, ha="center", va="center", color="#1b5e20", zorder=7)
    y0 = -9.35
    alt = [(uo2, y0), (uo2, y0 - 5.0)]
    n = 16
    for i in range(n + 1):
        a = math.pi / 2 * i / n
        alt.append((uo2 + R_MIN - R_MIN * math.cos(a), y0 - 5.0 - R_MIN * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 * i / n
        alt.append((RL + U_IN - R_MIN + R_MIN * math.sin(a), y0 - 5.0 - R_MIN * math.cos(a)))
    alt.append((RL + U_IN, y0 - 5.0))
    alt.append((RL + U_IN, y0))
    ax.plot([p[0] for p in alt], [p[1] for p in alt], color="#1b5e20", lw=2.4, ls="--", zorder=6)
    ax.text(uo2 - 4, -19.5, "alternativa: OUT' em u = %.1f (d = %.1f mm):\ncabo de 50,8 mm quase esticado, U de 11 mm" % (uo2, st["d_para_cabo_50,8_sem_folga_mm"]), fontsize=6.5, color="#1b5e20")
    ax.add_patch(Rectangle((60, -31), 40, 20, fc="none", ec="#8e44ad", ls="--", lw=1.2, zorder=6))
    ax.text(80, -32.5, "rebaixo (planta): ~ 40 x 20 mm sob a régua de trás", fontsize=7, color="#8e44ad", ha="center")
    ax.text(41, 20.5, "U de %.1f mm além da boca: passa sob a régua da fileira de trás (eixo 16,02 mm atrás, 14 mm de largura)" % dep, fontsize=6.5, color="#8a6d00")
    # (b) corte ao longo de y pelo eixo do OUT: z x y
    ax = axs[1]
    ax.set_title("corte ao longo de y pelo OUT da fileira 1 (bolso mais raso: 6,9 mm)", fontsize=8, loc="left")
    ax.set_xlim(-24, 9)
    ax.set_ylim(-11.5, 3)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.15)
    ax.tick_params(labelsize=6)
    ax.set_xlabel("v (mm, eixo da fileira = 0; trás à esquerda)", fontsize=7)
    ax.add_patch(Rectangle((-7, -T), 14, T, fc=c6.GOLD, ec="k", lw=0.5))
    ax.text(-6.5, 0.4, "régua 1,2 mm", fontsize=6.5)
    ax.axhline(-T - 6.9, color="k", lw=1)
    ax.text(-23.5, -T - 7.6, "piso da bandeja (fileira 1: 6,9 mm sob a régua)", fontsize=6.5)
    # cabecalho: de v -4.3-2.9... profundidade FOOT_D ao longo de v
    vh0 = VH - FOOT_D / 2
    ax.add_patch(Rectangle((vh0, -T - HDR_H), HDR_D, HDR_H, fc="#6fa0d8", ec="#2a5a9a"))
    ax.text(vh0 + HDR_D / 2, -T - HDR_H / 2, "SM06B\n2,95", fontsize=5.5, ha="center", va="center")
    ax.add_patch(Rectangle((vh0 - 2.45, -T - PLUG_H), 2.45, PLUG_H, fc="#8fd18f", ec="#2e7d32"))
    ax.text(vh0 - 1.2, -T - PLUG_H - 0.7, "plugue 3,6", fontsize=5.5, ha="center")
    ax.plot([vh0 - 2.45, vh0 - 2.45 - STUB], [-T - PLUG_H / 2] * 2, color="#d35400", lw=2.4)
    th = [math.pi * i / 20 for i in range(21)]
    ax.add_patch(Rectangle((-14, -T - 6.9), 7, 6.9 - T - 0.0, fc="none", ec="none"))
    ax.text(-23.5, 2.3, "o cabo sai reto 5 mm e dobra\ncom raio >= 6 mm (3 mm é o mínimo\nestático): numa bandeja de 6,9 mm\no U fica deitado no piso (planta),\nnão em pé (diâmetro 12 mm)", fontsize=6.3, color="#a04000", va="top")
    ax.annotate("", (3.5, -T), (3.5, -T - 6.9), arrowprops=dict(arrowstyle="<->"))
    ax.text(4.0, -5.0, "6,9", fontsize=7)
    ax.annotate("", (vh0 + HDR_D + 0.6, -T), (vh0 + HDR_D + 0.6, -T - PLUG_H), arrowprops=dict(arrowstyle="<->"))
    ax.text(vh0 + HDR_D + 0.9, -3.6, "3,6 (plugue)\nsobra 3,3 mm", fontsize=6)
    # (c) quadro de alturas
    ax = axs[2]
    ax.axis("off")
    rows = [("peça (JST, eSR_SZ.pdf)", "medida"),
            ("SM06B-SRSS-TB lateral: altura / fundo", "2,95 / 4,85 mm (footprint 5,55 +-0,1)"),
            ("largura do cabeçalho 6 vias (9 vias)", "8,0 mm (11,0 mm)"),
            ("plugue 06SR-3S: largura x altura", "7,0 x 3,6 mm (9 vias: 10,0)"),
            ("fio AWG 30, 7 fios, isolante OD", "0,54 a 0,58 mm; 0,7 A"),
            ("contato: inicial / depois de ensaio", "20 / 40 mOhm max."),
            ("raio de dobra (o desenho NÃO dá)", ">= 6 mm adotado; 3 mm estático (conferir)"),
            ("reta depois do plugue", "5 mm (adotado)"),
            ("elo entre réguas (d = %.1f mm): sobra" % st["d_entre_reguas_mm"], "%.1f mm do cabo de 50,8" % st["elo_50,8 (2 pol)"]["sobra_mm"]),
            ("U além da boca com 50,8 / 101,6", "%.1f / %.1f mm" % (dep, st["elo_101,6 (4 pol)"]["profundidade_do_U_alem_da_boca_mm"])),
            ("OUT em u = %.1f daria o cabo de 50,8 sem folga" % st["u_OUT_para_esse_d"], "d = %.1f mm" % st["d_para_cabo_50,8_sem_folga_mm"])]
    for i, (a, b) in enumerate(rows):
        y = 1 - i * 0.085
        ax.text(0.0, y, a, fontsize=7.5, fontweight="bold" if i == 0 else "normal", transform=ax.transAxes)
        ax.text(0.58, y, b, fontsize=7.5, fontweight="bold" if i == 0 else "normal", transform=ax.transAxes)
    fig.suptitle("R7V4 · junção da ligação H (planta e corte). Planta = vista de cima, trás no topo; corte = ao longo de y", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(IMG, "h_juncao_r7.png"), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    st = study()
    json.dump(st, open(os.path.join(HERE, "ligacao_h_r7.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(st, indent=1, ensure_ascii=False))
    fig_pinagem()
    fig_teclado32(st)
    fig_juncao(st)
    print("ok")
