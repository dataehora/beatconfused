"""eTutti Student V4 (R1V4 task D1 + D4, R2V4 F2): numbers behind the T3 detail and the case fixing.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/t3_deck.py

numpy only. Writes estudos/t3_deck.json. Sections:
  1. the Gateron KS-20 drawing's numbers (KS-20TF10B045NW-X72, 2023-09-13; the Orange has the same body, CHECK)
  2. the vertical tolerance stack between the lid's deck and the ruler (published tolerances, worst case and RSS)
  3. play of the two pegs in the ruler's holes, tie-down force against a 3 N press
  4. the deck as a plate (grillage, 4 mm mesh): preload of the 28 keys, 3 N on one key, for three fixing schemes
  5. the stepped deck as a 1D frame (what the ramps add)
  6. the lid's wall between fixing points
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometria as G    # noqa: E402

PITCH, ROWP = G.PITCH, G.ROW_PITCH
X_IF = 79.0                      # the interface's right edge (lid wall between interface and keyboard)
CASE_W = 100.0

# ---------------------------------------------------------------- 1. KS-20 (drawing numbers)
KS20 = {
    "desenho": "KS-20TF10B045NW-X72 (Gateron, 2023-09-13); o KS-20 Orange tem o mesmo corpo (conferir o desenho dele)",
    "carcaca_de_cima_mm": (15.40, 15.10),
    "altura_do_assento_ao_topo_mm": 11.10, "altura_tol_sem_indicacao_mm": 0.4,   # >10~30: +-0.4 (tabela geral do desenho)
    "ombro_inferior_a_5_00": "5,00 +-0,05 do assento ate a face de baixo da carcaca de cima (a face aponta PARA BAIXO: nao serve de apoio para a tampa)",
    "cobertura_afunilada_mm": 2.70, "cobertura_afunilada_tol": 0.1,
    "corpo_de_baixo_mm": (14.00, 14.00), "corpo_de_baixo_tol": 0.05, "largura_14_70_tol": 0.3,
    "furo_dos_pinos_mm": 1.70, "furo_tol": 0.05, "pinos_entre_centros_mm": 10.16,
    "pino_diametro": "nao cotado no desenho (estimado 1,55-1,60; conferir)",
    "pads_do_sensor": "0,8 x 0,8, entre os furos (1,27 de passo)",
    "curso_total_mm": 4.10, "curso_tol": 0.2, "curso_com_prensa_mm": "4,10 +-0,05 (desenho de corte)",
    "haste_cruz_mm": (4.00, 1.30), "haste_tol": "4,00 +0,05/-0,10 ; 1,30 +-0,04",
    "forca_inicial_gf": "30 +-10 (o desenho da variante X72; a Orange 38 gf ajusta a mola, nao o corpo)",
    "fluxo_posicao_inicial_Gs": "102 +-15", "fluxo_fundo_Gs": "905 +-80",
    "chanfro_do_topo": "2,70 +-0,1 de cobertura afunilada; largura do topo plano NAO cotada (estimada 11,4; conferir)",
}

# ---------------------------------------------------------------- 2. vertical stack
H_HOUSING, T_HOUSING = 11.10, 0.4         # seat to top face; tolerance of the drawing's general table (>10~30)
T_HOUSING_REAL = 0.10                     # what a molded part probably holds (not published: ASSUMED)
T_RULER, T_RULER_TOL = 1.2, 0.12          # JLCPCB 1.2 mm, +-10 %
PRINT_TOL = 0.3                           # JLC3DP, up to 100 mm (MJF, SLA +-0.2, SLS/FDM +-0.3)
FOAM_T, FOAM_COMPRESSION = 2.0, 0.50      # die-cut closed-cell PE foam, 2 mm, 50 % at nominal


def stack(h_tol, print_tol, ruler_tol=T_RULER_TOL):
    terms = {"carcaca (assento ate o topo)": h_tol, "espessura da regua": ruler_tol,
             "degrau da base (impressao)": print_tol, "deck da tampa ate o plano de encaixe (impressao)": print_tol}
    worst = sum(terms.values())
    rss = math.sqrt(sum(v * v for v in terms.values()))
    return {"termos": terms, "pior_caso_mm": round(worst, 3), "rss_mm": round(rss, 3)}


def stack_cases():
    out = {"publicada (carcaca +-0,4; impressao +-0,3 MJF/SLS/FDM)": stack(T_HOUSING, 0.3),
           "SLA (impressao +-0,2, resina cura +-0,15 apos 1-3 dias)": stack(T_HOUSING, 0.2),
           "carcaca real suposta +-0,1, impressao +-0,15 (tipico, NAO publicado)": stack(T_HOUSING_REAL, 0.15)}
    return out


# ---------------------------------------------------------------- 3. peg play
def pegs():
    hole_nom, hole_tol = 1.70, 0.05
    jlc_npth = 0.05           # NPTH drill tolerance, JLCPCB published +-0.05 (CHECK: PTH is +0.13/-0.08)
    hole_max = hole_nom + hole_tol + jlc_npth
    peg_min = 1.55            # ASSUMED
    play_r = (hole_max - peg_min) / 2
    span = 10.16
    rot = math.degrees(2 * play_r / span)
    # tie-down: 3 N at the cap's edge (8 mm from the axis), body footprint 14 mm: the load lies 1 mm outside the footprint
    tie = 3.0 * (8.0 - 7.0) / 14.0
    return {"furo_max_mm": round(hole_max, 3), "pino_min_estimado_mm": peg_min, "folga_radial_mm": round(play_r, 3),
            "giro_no_plano_graus": round(rot, 2), "translacao_x_mm": round(2 * play_r, 3), "translacao_y_mm": round(play_r, 3),
            "forca_de_amarracao_N_a_3N_na_borda": round(tie, 2)}


# ---------------------------------------------------------------- 4. plate grillage
class Plate:
    def __init__(self, x0, x1, y0, y1, t, E, h=4.0):
        self.x0, self.y0 = x0, y0
        self.nx = int(math.ceil((x1 - x0) / h)) + 1
        self.ny = int(math.ceil((y1 - y0) / h)) + 1
        self.hx, self.hy = (x1 - x0) / (self.nx - 1), (y1 - y0) / (self.ny - 1)
        N = self.nx * self.ny
        K = np.zeros((3 * N, 3 * N))

        def beam(a, b, L, EI, rot):
            k = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                        [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
            d = [3 * a, 3 * a + rot, 3 * b, 3 * b + rot]
            K[np.ix_(d, d)] += k
        for j in range(self.ny):
            for i in range(self.nx):
                wy = self.hy * (0.5 if j in (0, self.ny - 1) else 1.0)
                wx = self.hx * (0.5 if i in (0, self.nx - 1) else 1.0)
                if i + 1 < self.nx:
                    beam(self.node(i, j), self.node(i + 1, j), self.hx, E * wy * t ** 3 / 12, 1)
                if j + 1 < self.ny:
                    beam(self.node(i, j), self.node(i, j + 1), self.hy, E * wx * t ** 3 / 12, 2)
        self.K, self.N = K, N

    def node(self, i, j):
        return j * self.nx + i

    def near(self, x, y):
        return self.node(int(round((x - self.x0) / self.hx)), int(round((y - self.y0) / self.hy)))

    def solve(self, supports, loads):
        """loads: list of (x, y, N) applied together. Returns the node displacement vector (w)."""
        fixed = sorted({3 * self.near(x, y) for x, y in supports})
        free = np.setdiff1d(np.arange(3 * self.N), fixed)
        F = np.zeros(3 * self.N)
        for x, y, f in loads:
            F[3 * self.near(x, y)] += f
        u = np.zeros(3 * self.N)
        u[free] = np.linalg.solve(self.K[np.ix_(free, free)], F[free])
        return u[0::3]

    def single(self, supports, points, f):
        """f newtons on each point, one at a time (a factorisation per support set)."""
        fixed = sorted({3 * self.near(x, y) for x, y in supports})
        free = np.setdiff1d(np.arange(3 * self.N), fixed)
        pos = {d: n for n, d in enumerate(free)}
        Kf = self.K[np.ix_(free, free)]
        B = np.zeros((len(free), len(points)))
        rows = []
        for c, (x, y) in enumerate(points):
            r = pos.get(3 * self.near(x, y))
            rows.append(r)
            if r is not None:
                B[r, c] = f
        U = np.linalg.solve(Kf, B)
        return [0.0 if r is None else float(U[r, c]) for c, r in enumerate(rows)]


def key_sites(modules=0):
    rows = [(r, y, x0, n + 4 * modules) for r, y, x0, n in G.ROWS]
    return [(x0 + i * PITCH, y) for r, y, x0, n in rows for i in range(n)], rows


def triangles(modules=0):
    """Centroids of the three-key triangles (free spots for a boss: a 3.1 mm corridor opening to a diamond, radius ~2.7 mm)."""
    keys, rows = key_sites(modules)
    cs = []
    pts = {}
    for r, y, x0, n in rows:
        for i in range(n):
            pts[(r, i)] = (x0 + i * PITCH, y)
    for r in range(1, 4):                    # row r (front) and r+1 (behind)
        _, y1, xa, na = rows[r - 1]
        _, y2, xb, nb = rows[r]
        for i in range(na):
            a = pts[(r, i)]
            for j in range(nb):
                b = pts[(r + 1, j)]
                if abs(abs(a[0] - b[0]) - PITCH / 2) < 0.05 and abs(a[1] - b[1]) < ROWP + 0.1:
                    # third key: the next one in row r on the same side of b
                    for k in range(na):
                        c = pts[(r, k)]
                        if abs(abs(c[0] - a[0]) - PITCH) < 0.05 and abs(c[0] - b[0]) < PITCH / 2 + 0.05 and c[0] != a[0]:
                            cs.append(((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3))
    out = sorted({(round(x, 2), round(y, 2)) for x, y in cs})
    return out


def perimeter(x0, x1, y0, y1, step):
    pts = []
    n = int((x1 - x0) / step) + 1
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts += [(x, y0), (x, y1)]
    m = int((y1 - y0) / step) + 1
    for j in range(m + 1):
        y = y0 + (y1 - y0) * j / m
        pts += [(x0, y), (x1, y)]
    return pts


def deck_study(modules=0, mesh=4.0, preload=1.0, t=2.0, n_int=(0, 5, 10, 19)):
    """Deck as a plate on its walls (supported all along the perimeter = the lid shell held down at its fixings, ideal)
    plus n interior fixing points at triangle centroids; and the same with only the points (no walls: pessimistic)."""
    keys, rows = key_sites(modules)
    L = 252.0 + 74.0 * modules
    E = 1800.0 * (1 - 8.0 / PITCH)             # PA12 E = 1.8 GPa (JLC3DP), net of the 8 mm holes
    plate = Plate(X_IF, L, 0.0, CASE_W, t, E, mesh)
    tri = [(x, y) for x, y in triangles(modules) if x > X_IF + 8]
    perim_all = perimeter(X_IF, L, 0.0, CASE_W, mesh)
    loads = [(x, y, preload) for x, y in keys]
    res = {"modulos": modules, "teclas": len(keys), "comprimento_mm": L, "espessura_deck_mm": t,
           "pre_carga_por_tecla_N": preload, "triangulos_livres": len(tri), "interiores": {}}
    for n in n_int:
        interior = []
        if n:
            n = min(n, len(tri))
            idx = np.linspace(0, len(tri) - 1, n).astype(int)
            interior = [tri[i] for i in idx]
        w = plate.solve(perim_all + interior, loads)
        sing = plate.single(perim_all + interior, keys, 3.0)
        res["interiores"][str(n)] = {"preload_max_mm": round(float(np.max(w)), 3), "preload_media_mm": round(float(np.mean(w)), 3),
                                     "3N_numa_tecla_mm": round(max(sing), 3)}
    return res, tri


# ---------------------------------------------------------------- 5. stepped deck as a 1D frame in y
def frame_y(t=2.0, E=1800.0, q=0.22, supports_pinned=True):
    """Stepped deck profile in the y-z plane (per mm of x): bands at heights 0/2/4/7 joined by 45 deg ramps, 2 mm sheet,
    pinned at y = 0 and y = 100 (the walls). q = upward preload in N per mm of x (4 rows x 1 N per 18.5 mm)."""
    c = [G.ROWS[i][1] for i in range(4)]       # row y centres (row 1 = 74.03 ... row 4 = 25.97)
    zr = [0.0, 2.0, 4.0, 7.0]
    s = [2.0, 2.0, 3.0]
    pts = [(100.0, zr[0]), ]
    for i in range(3):
        ys = c[i] - 8.3
        pts.append((ys, zr[i]))
        pts.append((ys - s[i], zr[i + 1]))
    pts.append((0.0, zr[3]))
    pts = sorted(pts)                          # y ascending: 0 .. 100
    # refine to ~1 mm
    ys, zs = [], []
    for (ya, za), (yb, zb) in zip(pts[:-1], pts[1:]):
        n = max(1, int(round(math.hypot(yb - ya, zb - za))))
        for k in range(n):
            ys.append(ya + (yb - ya) * k / n)
            zs.append(za + (zb - za) * k / n)
    ys.append(pts[-1][0])
    zs.append(pts[-1][1])
    N = len(ys)
    K = np.zeros((3 * N, 3 * N))
    A, I = t, t ** 3 / 12.0
    for e in range(N - 1):
        dx, dz = ys[e + 1] - ys[e], zs[e + 1] - zs[e]
        L = math.hypot(dx, dz)
        cth, sth = dx / L, dz / L
        kl = np.zeros((6, 6))
        a, b = E * A / L, E * I / L ** 3
        kl[0, 0] = kl[3, 3] = a
        kl[0, 3] = kl[3, 0] = -a
        kl[1, 1] = kl[4, 4] = 12 * b
        kl[1, 4] = kl[4, 1] = -12 * b
        kl[1, 2] = kl[2, 1] = kl[1, 5] = kl[5, 1] = 6 * b * L
        kl[4, 2] = kl[2, 4] = kl[4, 5] = kl[5, 4] = -6 * b * L
        kl[2, 2] = kl[5, 5] = 4 * b * L * L
        kl[2, 5] = kl[5, 2] = 2 * b * L * L
        T = np.zeros((6, 6))
        R = np.array([[cth, sth, 0], [-sth, cth, 0], [0, 0, 1]])
        T[:3, :3] = R
        T[3:, 3:] = R
        kg = T.T @ kl @ T
        d = list(range(3 * e, 3 * e + 3)) + list(range(3 * (e + 1), 3 * (e + 1) + 3))
        K[np.ix_(d, d)] += kg
    F = np.zeros(3 * N)
    for i in range(N):
        wgt = 0.5 if i in (0, N - 1) else 1.0
        F[3 * i + 1] += q * wgt * (ys[min(i + 1, N - 1)] - ys[max(i - 1, 0)]) / 2.0
    fixed = [0, 1, 3 * (N - 1), 3 * (N - 1) + 1]
    free = np.setdiff1d(np.arange(3 * N), fixed)
    u = np.zeros(3 * N)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    wz = u[1::3]
    # flat 2 mm plate (same span, same load): w = 5 q L^4 / (384 E I), pinned-pinned
    flat = 5 * q * 100.0 ** 4 / (384 * E * I)
    return {"flecha_do_perfil_escalonado_mm": round(float(np.max(np.abs(wz))), 4), "flecha_da_placa_plana_mm": round(flat, 3),
            "carga_N_por_mm_de_x": q}


# ---------------------------------------------------------------- 6. lid wall between fixings
def wall_between_fixings(spacing, line_load, h=20.0, t=2.0, E=1800.0):
    I = t * h ** 3 / 12.0
    return 5 * line_load * spacing ** 4 / (384 * E * I)       # simply supported, uniform


def main():
    res = {"ks20": KS20, "pilha_vertical": stack_cases(), "pinos": pegs()}
    res["espuma"] = {"espessura_mm": FOAM_T, "compressao_nominal": FOAM_COMPRESSION,
                     "janela_de_compressao_para_pior_caso_publicado_mm": round(2 * stack(T_HOUSING, 0.3)["pior_caso_mm"], 2),
                     "forca_por_tecla_estimada_N": "2-4 (PE de 33 kg/m3, 50 % de compressao, 60 mm2: ESTIMADO, sem medida)"}
    res["deck"] = {}
    for m, mesh in ((0, 4.0), (3, 6.0)):
        for t in (2.0, 3.0):
            r, tri = deck_study(m, mesh, 1.0, t, (0, 5, 10, 19) if m == 0 else (0, 14, 28, 55))
            res["deck"]["%d teclas, deck %.0f mm" % (28 + 16 * m, t)] = r
    res["perfil_escalonado"] = frame_y()
    res["parede"] = {"flecha_entre_parafusos_mm": {str(s): round(wall_between_fixings(s, 0.22), 4) for s in (40, 60, 80, 120)},
                     "nota": "parede de 2 x 20 mm, PA12 E = 1,8 GPa, carga de pre-carga 0,22 N/mm de x (1 N por tecla)"}
    json.dump(res, open(os.path.join(HERE, "t3_deck.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
