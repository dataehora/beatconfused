#!/usr/bin/env python3
"""Liebling (Batschauer), R3MIC, versao A - D1: estudo da alavanca do plugue no centro da placa de 72 x 22 mm.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe minimic/design/estudo_alavanca.py

Escreve minimic/design/estudo_alavanca.json e as figuras em minimic/design/img/ (alavanca.png, capinha.png, largura.png).
Tudo e conta de projeto: as premissas estao marcadas ASSUMIDO e a Fase 2 (peca real, celular real) as substitui.
Quadro: x = ao longo dos 72 mm, y = espessura (1,2 mm), v = ao longo dos 22 mm (v = 0 na borda do plugue). O plugue entra no celular
ao longo de -v. "Fraco" = carga na direcao da espessura (y) da placa; "forte" = carga no plano da placa (x)."""
import json
import math
import os

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
G = 9.81
OUT = {}

# ------------------------------------------------------------------ 1. massa
W, D = 72.0, 22.0
AREA = 1548.73                       # mm2, contorno com entalhe (gerar_envelope.py)
RHO_FR4 = 1.85e-3                    # g/mm3
CU_FRAC, CU_T, RHO_CU = 0.5, 0.035, 8.96e-3


def massa(t):
    fr4 = AREA * t * RHO_FR4
    cu = AREA * CU_FRAC * 2 * CU_T * RHO_CU
    pecas = {
        "FR-4 (%.1f mm)" % t: fr4,
        "cobre (2 camadas, 35 um, 50 %)": cu,
        "27 LEDs (12 x 0805/1206 + 15 x 0603) a 0,015 g": 27 * 0.015,
        "2 botoes tateis a 0,10 g": 0.20,
        "RP2040 0,10 + flash 0,03 + LDO 0,03 + 2 microfones 0,02": 0.20,
        "~60 passivos a 0,003 g": 0.18,
        "cristal": 0.05,
        "mascara, ENIG, solda": 0.15,
        "2 espumas Ø10 x 3 (0,03 g cada)": 0.06,
    }
    placa = sum(pecas.values())
    plug = 1.2                       # ASSUMIDO: plugue USB-C metalico com 4 pernas, 0,9 a 1,5 g
    return pecas, placa, plug


pecas12, placa12, plug = massa(1.2)
pecas16, placa16, _ = massa(1.6)
M12, M16 = placa12 + plug, placa16 + plug
OUT["massa"] = {"itens_1.2": {k: round(v, 3) for k, v in pecas12.items()}, "placa_sem_plugue_1.2_g": round(placa12, 2), "plugue_g_assumido": plug,
                "total_1.2_g": round(M12, 2), "total_1.6_g": round(M16, 2), "faixa_g": [5.5, 7.5], "pior_caso_g": 8.0}

# ------------------------------------------------------------------ 2. cargas e momentos
V_CG = 11.0                          # mm da borda do plugue ao centro de massa (plugue na borda, resto simetrico; ligeiramente > D/2 pelos botoes: 11)
MASS_W = 8.0                         # g (pior caso)
GAP_NOM = 0.5                        # folga entre a borda da placa e o celular (mm)
ARM_ROOT_CG = V_CG
Fg = MASS_W * 1e-3 * G               # 1 g, N
loads = [
    # nome, forca N, braco ate a raiz do plugue (mm), onde, justificativa
    ("peso (1 g), celular deitado, placa horizontal", Fg, V_CG, "no centro de massa", "o celular de barriga para cima: peso na direcao fraca"),
    ("manuseio / pau de selfie balancando (10 g)", 10 * Fg, V_CG, "no centro de massa", "10 g e a aceleracao de um balanco forte do pau de selfie"),
    ("empurrao leve na borda livre (2 N)", 2.0, D - 2.5, "no meio da borda livre (v = 22)", "roçar na roupa, no estojo, na estante: ~0,2 kgf; CARGA DE PROJETO"),
    ("empurrao forte na borda livre (5 N)", 5.0, D - 2.5, "no meio da borda livre (v = 22)", "apoiar a mao ou encostar na parede: ~0,5 kgf; CARGA DE SOBREVIVENCIA"),
    ("empurrao forte na PONTA (5 N, x = 70)", 5.0, 1.0, "no microfone da ponta", "ver torque abaixo"),
]
# torque em torno do eixo do plugue para a carga na ponta
ARM_TIP_X = 34.0                     # mm do centro (x = 36) ate a ponta (x = 70)
OUT["cargas"] = []
SHELL = dict(w=8.25, h=2.40, t=0.25)  # casca USB-C nominal, parede 0,25 (ASSUMIDO)
SIGY_SHELL = 200.0                   # MPa, aco inox / latao encruado (ASSUMIDO)


def shell_Z(s):
    w, h, t = s["w"], s["h"], s["t"]
    I = (w * h ** 3 - (w - 2 * t) * (h - 2 * t) ** 3) / 12.0
    return I, I / (h / 2)


Ish, Zsh = shell_Z(SHELL)
LEG_CAP_THT, LEG_CAP_SMD = 25.0, 8.0     # N por perna ASSUMIDO (THT: 25-60, tabs SMD: 8-15)
N_LEG_FACE = 2                           # pernas por face da placa (4 pernas: 2 em cima, 2 embaixo) ASSUMIDO


def leg_force(M, t):
    """Binario nas pernas: bracos = espessura da placa + 0,2 (metal da perna) ; n pernas por face."""
    arm = t + 0.2
    return M / (arm * N_LEG_FACE)


rows = []
for nome, F, arm, onde, why in loads:
    for t, mtot in ((1.2, M12), (1.6, M16)):
        M = F * (arm + GAP_NOM) if "PONTA" not in nome else None
        if M is None:
            T_ax = F * ARM_TIP_X                       # N.mm de torque em torno do eixo do plugue
            M = F * (V_CG + GAP_NOM)                   # flexao simultanea (carga no meio da asa)
            # torque resistido pelo par das pernas da esquerda e da direita (bracos = 7 mm entre pares de pernas ASSUMIDO)
            f_leg = T_ax / (7.0 * 2)
            rows.append({"caso": nome, "t": t, "F_N": F, "M_Nmm": round(T_ax, 1), "tipo": "torque no eixo do plugue", "sigma_casca_MPa": None,
                         "F_perna_N": round(f_leg, 1), "margem_THT": round(LEG_CAP_THT / f_leg, 2), "margem_SMD": round(LEG_CAP_SMD / f_leg, 2)})
            continue
        sig = M / Zsh
        f_leg = leg_force(M, t)
        rows.append({"caso": nome, "t": t, "F_N": round(F, 3), "M_Nmm": round(M, 1), "tipo": "flexao fraca", "sigma_casca_MPa": round(sig, 1),
                     "F_perna_N": round(f_leg, 1), "margem_THT": round(LEG_CAP_THT / f_leg, 2), "margem_SMD": round(LEG_CAP_SMD / f_leg, 2)})
OUT["cargas"] = rows
OUT["casca"] = {"w": SHELL["w"], "h": SHELL["h"], "t": SHELL["t"], "I_mm4": round(Ish, 2), "Z_mm3": round(Zsh, 2), "sigma_escoamento_MPa": SIGY_SHELL,
                "momento_de_escoamento_Nmm": round(Zsh * SIGY_SHELL, 0)}
OUT["capacidade_perna_N"] = {"THT": LEG_CAP_THT, "SMD": LEG_CAP_SMD}
for t in (1.2, 1.6):
    arm = t + 0.2
    Mcap = LEG_CAP_THT * arm * N_LEG_FACE
    OUT["empurrao_max_borda_livre_N_%.1f" % t] = round(Mcap / (D - 2.5 + GAP_NOM), 2)
    OUT["momento_max_juncao_THT_Nmm_%.1f" % t] = round(Mcap, 1)

# ------------------------------------------------------------------ 3. folga no receptaculo (balanço livre)
CLEAR_Y = 2.56 - 2.40                # folga do receptaculo (2,56) - casca (2,40) = 0,16 mm
MATE = 5.5                           # mm de plugue dentro (ASSUMIDO)
tilt = CLEAR_Y / MATE
OUT["folga_receptaculo"] = {"folga_mm": CLEAR_Y, "inclinacao_rad": round(tilt, 4), "inclinacao_graus": round(math.degrees(tilt), 2),
                            "deslocamento_na_borda_livre_mm": round(tilt * (D + GAP_NOM), 2), "deslocamento_no_microfone_mm": round(tilt * (P_MIC := 11.0 + GAP_NOM), 2)}

# ------------------------------------------------------------------ 4. grillage da placa (flexao da PCB)
E_FR4, NU = 17000.0, 0.15           # MPa (fibra, com cobre: 17-20 GPa)
H_GRID = 0.5


def outline_poly():
    cx, n0, n1, nd = 36.0, 36.0 - 4.62, 36.0 + 4.62, 2.6
    return [(1.5, 0), (n0, 0), (n0, nd), (n1, nd), (n1, 0), (70.5, 0), (72, 1.5), (72, 19), (69, 22), (3, 22), (0, 19), (0, 1.5)]


def inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def grillage(t, loads_nodes, mass_g, clamp="notch"):
    """Grelha de vigas (x e y) com h = 0,5 mm, 3 gdl por no (w, theta_x, theta_y); engastada no contorno do entalhe.
    loads_nodes: lista (x, y, F_N para baixo). Se mass_g, soma peso distribuido (g de 1 g em N)."""
    poly = outline_poly()
    nx, ny = int(W / H_GRID) + 1, int(D / H_GRID) + 1
    idx = -np.ones((nx, ny), dtype=int)
    pts = []
    for i in range(nx):
        for j in range(ny):
            x, y = i * H_GRID, j * H_GRID
            xs, ys = x + (36.0 - x) * 1e-6, y + (11.0 - y) * 1e-6      # um tico para dentro: nos de borda contam
            if inside(poly, xs, ys):
                idx[i, j] = len(pts)
                pts.append((x, y))
    nn = len(pts)
    ndof = 3 * nn
    Dp = E_FR4 * t ** 3 / (12 * (1 - NU ** 2))
    EI = Dp * H_GRID
    GJ = Dp * (1 - NU) * H_GRID
    le = H_GRID
    kb = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                  [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
    kt = GJ / le * np.array([[1, -1], [-1, 1]])
    I, J, V = [], [], []

    def add(dofs, k):
        for a, da in enumerate(dofs):
            for b, db in enumerate(dofs):
                I.append(da)
                J.append(db)
                V.append(k[a, b])
    elems = []
    for i in range(nx):
        for j in range(ny):
            a = idx[i, j]
            if a < 0:
                continue
            if i + 1 < nx and idx[i + 1, j] >= 0:      # viga ao longo de x: flexao w, theta_y(=dof 2) ; torcao theta_x(dof 1)
                b = idx[i + 1, j]
                add([3 * a, 3 * a + 2, 3 * b, 3 * b + 2], kb)
                add([3 * a + 1, 3 * b + 1], kt)
                elems.append(("x", a, b))
            if j + 1 < ny and idx[i, j + 1] >= 0:      # viga ao longo de y: flexao w, theta_x(dof 1) ; torcao theta_y(dof 2)
                b = idx[i, j + 1]
                add([3 * a, 3 * a + 1, 3 * b, 3 * b + 1], kb)
                add([3 * a + 2, 3 * b + 2], kt)
                elems.append(("y", a, b))
    K = sp.csr_matrix((V, (I, J)), shape=(ndof, ndof))
    F = np.zeros(ndof)
    if mass_g:
        # peso por no proporcional a area do no (placa + pecas: massa total distribuida uniformemente, sem o plugue)
        w_node = mass_g * 1e-3 * G / nn
        for a in range(nn):
            F[3 * a] -= w_node
    for (x, y, f) in loads_nodes:
        a = idx[int(round(x / H_GRID)), int(round(y / H_GRID))]
        assert a >= 0, (x, y)
        F[3 * a] -= f
    # engaste: nos do contorno do entalhe (y = 2,6, x entre n0 e n1; e as paredes laterais)
    fixed = []
    n0, n1, nd = 36.0 - 4.62, 36.0 + 4.62, 2.6
    for k, (x, y) in enumerate(pts):
        on_bottom = nd - 1e-9 <= y <= nd + 0.6 and n0 - 0.6 <= x <= n1 + 0.6
        on_side = (n0 - 0.6 <= x <= n0 or n1 <= x <= n1 + 0.6) and y <= nd + 0.6
        if on_bottom or on_side:
            fixed += [3 * k, 3 * k + 1, 3 * k + 2]
    free = np.setdiff1d(np.arange(ndof), fixed)
    u = np.zeros(ndof)
    u[free] = spl.spsolve(K[free][:, free].tocsc(), F[free])
    # momento maximo por largura nas vigas (flexao): M = EI * curvatura ~ | (6 (w_a - w_b)/l^2 ...)| ; usa extremos de cada viga
    mmax = 0.0
    for (d, a, b) in elems:
        if d == "x":
            wa, ta, wb, tb = u[3 * a], u[3 * a + 2], u[3 * b], u[3 * b + 2]
        else:
            wa, ta, wb, tb = u[3 * a], u[3 * a + 1], u[3 * b], u[3 * b + 1]
        # momentos nas pontas da viga de Hermite
        ma = EI / le ** 2 * (-6 * (wb - wa) / le + 4 * ta + 2 * tb)
        mb = EI / le ** 2 * (6 * (wb - wa) / le - 2 * ta - 4 * tb)
        mmax = max(mmax, abs(ma), abs(mb))
    m_per_w = mmax / H_GRID
    sigma = 6 * m_per_w / t ** 2
    wmin = u[0::3].min()
    return {"deflexao_max_mm": round(float(-wmin), 4), "sigma_nominal_MPa": round(float(sigma), 1), "nos": nn, "u": u, "pts": pts}


# validacao: reuso de grillage com contorno temporario
def validar():
    global outline_poly, W, D
    bk = (outline_poly, W, D)
    # faixa 20 x 5, engastada em x = 0 (usa a rotina com 'notch' desligado: contorno retangular e engaste na borda esquerda)
    def strip_outline():
        return [(0, 0), (20, 0), (20, 5), (0, 5)]
    # copia local simplificada: resolve com a mesma montagem
    outline_poly = strip_outline
    W, D = 20.0, 5.0
    import types
    src = grillage
    # engaste na borda esquerda: sobrescreve a condicao pelos nos com x=0 via notch trick
    res = None
    try:
        # monta manualmente com a rotina (os nos do "notch" nao existem): usa um clamp alternativo
        nx, ny = int(W / H_GRID) + 1, int(D / H_GRID) + 1
        t = 1.2
        Dp = E_FR4 * t ** 3 / (12 * (1 - NU ** 2))
        EI = Dp * H_GRID
        le = H_GRID
        kb = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                      [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
        GJ = Dp * (1 - NU) * H_GRID
        kt = GJ / le * np.array([[1, -1], [-1, 1]])
        n = nx * ny
        Km = np.zeros((3 * n, 3 * n))
        id_ = lambda i, j: i * ny + j

        def add(dofs, k):
            for a, da in enumerate(dofs):
                for b, db in enumerate(dofs):
                    Km[da, db] += k[a, b]
        for i in range(nx):
            for j in range(ny):
                a = id_(i, j)
                if i + 1 < nx:
                    b = id_(i + 1, j)
                    add([3 * a, 3 * a + 2, 3 * b, 3 * b + 2], kb)
                    add([3 * a + 1, 3 * b + 1], kt)
                if j + 1 < ny:
                    b = id_(i, j + 1)
                    add([3 * a, 3 * a + 1, 3 * b, 3 * b + 1], kb)
                    add([3 * a + 2, 3 * b + 2], kt)
        F = np.zeros(3 * n)
        for j in range(ny):
            F[3 * id_(nx - 1, j)] = -1.0 / ny
        fixed = []
        for j in range(ny):
            fixed += [3 * id_(0, j), 3 * id_(0, j) + 1, 3 * id_(0, j) + 2]
        free = np.setdiff1d(np.arange(3 * n), fixed)
        u = np.zeros(3 * n)
        u[free] = np.linalg.solve(Km[free][:, free], F[free])
        tip = -np.mean([u[3 * id_(nx - 1, j)] for j in range(ny)])
        exact = 1.0 * 20.0 ** 3 / (3 * Dp * 5.0)
        res = {"grelha_mm": round(float(tip), 4), "viga_FL3/3EI_mm": round(float(exact), 4), "razao": round(float(tip / exact), 3)}
    finally:
        outline_poly, W, D = bk
    return res


OUT["validacao_grelha_faixa_20x5"] = validar()
fe = {}
masses = {1.2: placa12, 1.6: placa16}
for t in (1.2, 1.6):
    r = {}
    g0 = grillage(t, [], masses[t])
    r["peso_1g"] = {"deflexao_max_mm": g0["deflexao_max_mm"], "sigma_nominal_MPa": g0["sigma_nominal_MPa"]}
    g10 = grillage(t, [], masses[t] * 10)
    r["peso_10g"] = {"deflexao_max_mm": g10["deflexao_max_mm"], "sigma_nominal_MPa": g10["sigma_nominal_MPa"]}
    g2 = grillage(t, [(36.0, 22.0, 2.0)], 0)
    r["empurrao_2N_borda_livre_x36"] = {"deflexao_max_mm": g2["deflexao_max_mm"], "sigma_nominal_MPa": g2["sigma_nominal_MPa"]}
    g5 = grillage(t, [(36.0, 22.0, 5.0)], 0)
    r["empurrao_5N_borda_livre_x36"] = {"deflexao_max_mm": g5["deflexao_max_mm"], "sigma_nominal_MPa": g5["sigma_nominal_MPa"]}
    g2t = grillage(t, [(70.0, 11.0, 2.0)], 0)
    r["empurrao_2N_ponta_x70"] = {"deflexao_max_mm": g2t["deflexao_max_mm"], "sigma_nominal_MPa": g2t["sigma_nominal_MPa"]}
    gt = grillage(t, [(70.0, 11.0, 5.0)], 0)
    r["empurrao_5N_ponta_x70"] = {"deflexao_max_mm": gt["deflexao_max_mm"], "sigma_nominal_MPa": gt["sigma_nominal_MPa"]}
    fe["t_%.1f" % t] = r
OUT["flexao_placa"] = fe
OUT["flexao_premissas"] = {"E_MPa": E_FR4, "nu": NU, "malha_mm": H_GRID, "engaste": "contorno do entalhe (juncao rigida: melhor caso para a placa)", "Kt_canto": 2.5,
                           "resistencia_flexao_FR4_MPa": "350-450 (adotado 100 como admissivel com cobre, fadiga e Kt)"}

# frequencia da asa (balanço): primeira flexao
E_si = E_FR4 * 1e6
for t in (1.2, 1.6):
    rho_eff = (placa12 if t == 1.2 else placa16) * 1e-3 / (AREA * t * 1e-9)   # kg/m3 equivalente (inclui as pecas)
    L = 0.0315
    f1 = 0.5596 / L ** 2 * (t * 1e-3) * math.sqrt(E_si / (12 * rho_eff))
    OUT["f1_asa_Hz_%.1f" % t] = round(f1, 0)

# ------------------------------------------------------------------ 5. capinha
LP = 6.65                              # comprimento do plugue para fora da borda (protótipo)
R_MOUTH = 0.3                          # ASSUMIDO: boca do receptaculo recuada 0,3 mm da superficie do celular nu
D_PORT = 6.5                           # ASSUMIDO: profundidade da boca ao fundo do receptaculo, celular nu (6,1 a 6,9)
LMIN = 5.0                             # ASSUMIDO: inserção minima para conservar contatos + retenção
cap_rows = []
for tc in (0.0, 0.5, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0):
    for lp in (6.65, 7.5, 8.5):
        mate = min(D_PORT, lp - tc - R_MOUTH * 0 - 0.0)
        # a placa fica na face externa da capinha: a distancia da borda da placa ao fundo = tc + (profundidade ate o fundo)
        mate = min(D_PORT - 0.0, lp - tc)
        cap_rows.append({"capinha_mm": tc, "plugue_mm": lp, "insercao_mm": round(mate, 2), "ok_>=5.0": mate >= LMIN})
OUT["capinha"] = {"premissas": {"Lp": LP, "D_port": D_PORT, "Lmin": LMIN, "tc_max_para_Lp_6.65": round(LP - LMIN, 2)},
                  "tabela": cap_rows}
# folga celular nu
OUT["folga_celular_nu"] = {"min": round(max(0, LP - 6.9), 2), "max": round(max(0, LP - 6.1), 2), "nominal": round(max(0, LP - D_PORT), 2)}
OUT["rebaixo_minimo"] = {"conta": "profundidade do receptaculo (6.1-6.9) + capinha tc <= 6.65 + (6.9-D_port)?", "tc_max_nominal": round(LP - LMIN, 2),
                         "comprimento_para_capinha_2mm": round(LMIN + 2.0, 2), "comprimento_para_capinha_3mm": round(LMIN + 3.0, 2)}

# ------------------------------------------------------------------ 6. largura
phones = [("compacto (64-68)", 66.0), ("Pixel 8 / Galaxy S24 (~70.6)", 70.6), ("iPhone 15/16 (~71.6)", 71.6), ("Pixel 9 (~72)", 72.0),
          ("Galaxy S24+ (~75.9)", 75.9), ("Pixel 9 Pro XL (~76.6)", 76.6), ("iPhone Pro Max (~77.6)", 77.6), ("Galaxy S Ultra (~79)", 79.0)]
wrows = []
for nome, wp in phones:
    for tc in (0.0, 1.0):
        wt = wp + 2 * tc
        wrows.append({"celular": nome, "largura_celular_mm": wp, "capinha_mm": tc, "largura_total": round(wt, 1),
                      "sobra_por_lado_mm": round((wt - W) / 2, 2), "porta_deslocada_1mm_pior_lado": round((wt - W) / 2 - 1.0, 2)})
OUT["largura"] = wrows

# ------------------------------------------------------------------ saida
with open(os.path.join(HERE, "estudo_alavanca.json"), "w", encoding="utf-8") as f:
    json.dump(OUT, f, indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ figuras
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .25})
# figura 1: alavanca (esboço lateral + barras de forca por perna)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})
a = ax[0]
a.set_aspect("equal")
a.set_xlim(-14, 30)
a.set_ylim(-9, 9)
a.grid(False)
a.add_patch(plt.Rectangle((-14, -4.2), 12.5, 8.4, fc="#d9d9de", ec="#555"))          # celular (espessura 8.4)
a.text(-8, 0, "celular\n(corpo ~8 mm)", ha="center", va="center", fontsize=8)
a.add_patch(plt.Rectangle((-1.5, -1.63 + 0.0), 6.65 - 5.15, 3.26, fc="#c8ccd3", ec="#555"))  # plugue visivel
a.add_patch(plt.Rectangle((-2.0, -1.63), 2.0 + 0.0, 3.26, fc="#c8ccd3", ec="#555"))
a.add_patch(plt.Rectangle((0.5, -0.6), 22, 1.2, fc="#222", ec="k"))                     # placa
a.add_patch(plt.Rectangle((-1.5, -1.63), 2.0 + 0.5, 3.26, fc="#c8ccd3", ec="#555"))
a.annotate("", xy=(11.5, -0.6), xytext=(11.5, 3.5), arrowprops=dict(arrowstyle="->", color="#2a7"))
a.text(11.8, 3.6, "peso 8 g x 1 g = 0,08 N\n(celular deitado)", fontsize=8, color="#2a7")
a.annotate("", xy=(22.5, -6.2), xytext=(22.5, -0.6), arrowprops=dict(arrowstyle="->", color="#d33", lw=2))
a.text(22.5, -7.8, "empurrao 2 N (projeto)\n5 N (sobrevivencia)", ha="center", fontsize=8, color="#d33")
a.annotate("", xy=(0.5, 5.2), xytext=(11.5, 5.2), arrowprops=dict(arrowstyle="<->"))
a.text(6, 5.6, "braco 11 mm", ha="center", fontsize=8)
a.annotate("", xy=(0.5, 7.0), xytext=(22.5, 7.0), arrowprops=dict(arrowstyle="<->"))
a.text(11.5, 7.4, "braco 22 mm (borda livre)", ha="center", fontsize=8)
a.text(-1.5, -2.9, "plugue 3,26 x 6,65", fontsize=8)
a.set_title("Vista lateral (corte pela espessura): a placa e uma aba de 22 mm em balanço")
a.axis("off")
b = ax[1]
cases = [r for r in OUT["cargas"] if r["tipo"] == "flexao fraca"]
labels = []
v12, v16 = [], []
for nome in dict.fromkeys(r["caso"] for r in cases):
    labels.append(nome.split(" (")[0].replace("empurrao", "empurrão").replace("manuseio / pau de selfie balancando", "balanço 10 g") + "\n(" + nome.split("(")[-1].rstrip(")") + ")")
    v12.append([r["F_perna_N"] for r in cases if r["caso"] == nome and r["t"] == 1.2][0])
    v16.append([r["F_perna_N"] for r in cases if r["caso"] == nome and r["t"] == 1.6][0])
x = np.arange(len(labels))
b.bar(x - .2, v12, .4, label="placa 1,2 mm", color="#4aa8ff")
b.bar(x + .2, v16, .4, label="placa 1,6 mm", color="#ffd23f")
b.axhline(LEG_CAP_THT, color="#2a7", ls="--")
b.text(len(labels) - .5, LEG_CAP_THT + 1, "perna THT ~25 N (assumido)", color="#2a7", ha="right", fontsize=8)
b.axhline(LEG_CAP_SMD, color="#d33", ls="--")
b.text(len(labels) - .5, LEG_CAP_SMD + 1, "perna SMD ~8 N (assumido)", color="#d33", ha="right", fontsize=8)
b.set_xticks(x)
b.set_xticklabels(labels, fontsize=7)
b.set_ylabel("força em cada perna do plugue (N)")
b.set_title("Binário nas pernas (4 pernas, 2 por face)")
b.legend(loc="upper left")
plt.tight_layout()
plt.savefig(os.path.join(IMG, "alavanca.png"), dpi=140)
plt.close()

# figura 2: capinha
fig, a = plt.subplots(figsize=(7.5, 4.2))
tcs = np.linspace(0, 3.5, 100)
for lp, col in ((6.65, "#4aa8ff"), (7.5, "#ffd23f"), (8.5, "#2a7")):
    a.plot(tcs, np.minimum(D_PORT, lp - tcs), color=col, label="plugue %.2f mm fora da borda" % lp)
a.axhline(LMIN, color="#d33", ls="--")
a.text(3.45, LMIN + .08, "inserção mínima 5,0 (assumido)", color="#d33", ha="right", fontsize=8)
for tc, lab in ((1.0, "fina 1,0"), (2.0, "comum 2,0"), (3.0, "reforçada 3,0")):
    a.axvline(tc, color="#999", lw=.8)
    a.text(tc, 3.4, lab, rotation=90, va="bottom", fontsize=8, color="#555")
a.set_xlabel("espessura da capinha na borda da porta (mm)")
a.set_ylabel("inserção efetiva no celular (mm)")
a.set_ylim(3.3, 7)
a.set_title("Capinha: o plugue de 6,65 mm só atravessa capinha de até ~1,6 mm")
a.legend(loc="lower left", fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(IMG, "capinha.png"), dpi=140)
plt.close()

# figura 3: largura
fig, a = plt.subplots(figsize=(9, 4.2))
names = [p[0] for p in phones]
x = np.arange(len(phones))
wp = np.array([p[1] for p in phones])
a.bar(x - .2, (wp - W) / 2, .4, label="sem capinha", color="#4aa8ff")
a.bar(x + .2, (wp + 2 - W) / 2, .4, label="capinha fina 1,0 mm", color="#ffd23f")
a.axhline(0, color="k", lw=.8)
a.set_xticks(x)
a.set_xticklabels([n.replace(" (", "\n(") for n in names], fontsize=7)
a.set_ylabel("celular − placa, por lado (mm)\n(positivo: a placa é mais estreita)")
a.set_title("Largura 72 mm contra o celular (centrada; larguras de memória, ±1 mm)")
a.legend()
plt.tight_layout()
plt.savefig(os.path.join(IMG, "largura.png"), dpi=140)
plt.close()

print(json.dumps({k: OUT[k] for k in ("massa", "casca", "folga_receptaculo", "validacao_grelha_faixa_20x5", "flexao_placa", "capinha", "f1_asa_Hz_1.2", "f1_asa_Hz_1.6",
                                         "empurrao_max_borda_livre_N_1.2", "empurrao_max_borda_livre_N_1.6", "folga_celular_nu")}, indent=1, ensure_ascii=False)[:9000])
for r in OUT["cargas"]:
    print(r)
