"""eTutti Student V4 (R7V4 item 1, aplicado na R8V4): estudo e analise da ligacao "H" (cabo SH de estoque + rebaixo na base), so 32 teclas.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/ligacao_h.py [analise|figuras|tudo]

Nao altera o case oficial (case_r4.py / layout_r4.py): importa so as posicoes de layout_r4 (Python puro) e desenha o estudo
em matplotlib + numpy (raster de 0,1 mm). Escreve case/out/ligacao_h.json e as figuras case/renders/ligacao_h_*.png.

Modelo do cabo (todos os numeros marcados "conferir" nao vem de desenho do fabricante; o PDF da JST e protegido e sem texto extraivel):
  * jumper JST A06SR06SR30K51B: 6 fios AWG30, 50,8 mm (2 in), plugue SHR-06V-S nas duas pontas; os fios saem do plugue no eixo de encaixe;
  * comprimento livre de fio F: 50,8 (limite alto) ou 44,0 (se os 50,8 incluirem os corpos dos plugues, 3,4 mm cada);
  * feixe de 6 fios deitado: 5,0 mm de largura x 1,0 de espessura; raio de dobra minimo adotado 4,0 mm (5 x o diametro do fio, ~0,8 mm; a JST
    nao publica raio de dobra do SH: conferir) no plano da fita (curvas "de lado" com os fios soltos) e 4,0 mm no plano vertical;
  * a medida do cabo e a do laco em U de largura 11,8 (entre as saidas dos dois plugues) e raio 5,9.
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                          # noqa: E402
import numpy as np                                                       # noqa: E402
from matplotlib.patches import Circle, Rectangle, Polygon                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402
import planta_v4 as PL   # noqa: E402

REN = os.path.join(HERE, "renders")
OUT = os.path.join(HERE, "out")
os.makedirs(REN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------- parametros do estudo
F_LIST = {"45,8": 45.8, "50,8": 50.8}      # comprimento livre de fio: 45,8 = 50,8 - 2 x 2,5 (eletronica); 50,8 = limite alto
BW, BT = 5.6, 0.6                          # feixe deitado: largura (plano) e espessura
RC_MIN = 6.0                               # raio de dobra adotado pela eletronica (minimo estatico 3 mm; conferir)
RC = RC_MIN
PLUG_W, PLUG_D, PLUG_H = 7.0, 2.45, 3.6         # plugue 06SR-3S (JST eSR_SZ.pdf, pela eletronica)
HDR_W, HDR_D, HDR_FOOT, HDR_H = 9.4, 4.85, 5.55, 2.95   # SM06B-SRSS-TB lateral: largura da pegada, fundo do corpo, fundo da pegada, altura
STRAIGHT = 5.0                             # reta minima depois do plugue (eletronica; conferir)
IN_U = 5.9
OUT_U = L.OUT_X                            # R8V4: cabecalho OUT em u 47,5 (aprovado pelo J); a R7V4 estudou 49,5 e a R4V4 tinha 68,1
RLOOP = 5.9
CLR = 0.5                                  # folga lateral do feixe a trilho, boss, parede
Z_FLOOR = L.Z_FLOOR                        # -8,1
GRID = 0.1
XMAX, YMAX = 252.0, 100.0                  # raster de y 0 a 100 (os lacos ficam em y > 0; a parede de tras, em y -2, so entra nas contas)
NX, NY = int(XMAX / GRID), int(YMAX / GRID)
WALL_IN = L.Y_BACK + L.WALL + 0.15         # R8V4: face interna da parede de tras da bandeja (a parede vai a y -2: 102 mm de largura)
LANE_Y0 = L.LANE_Y0                        # -7,5 (boca do cabecalho em relacao ao eixo da fileira)
Y_EXIT = LANE_Y0 - PLUG_D                  # -9,95: face de tras do plugue
Z_AXIS = -(L.RULER_T + HDR_H / 2.0)         # eixo de encaixe abaixo do topo da regua (-2,675)


def zr(row):
    return L.ZR[row - 1]


def axis_z(row):
    return zr(row) + Z_AXIS


# ----------------------------------------------------------------------------- raster
def blank():
    return np.zeros((NY, NX), dtype=bool)


def stamp_disk(m, x, y, r):
    i0, i1 = max(0, int((x - r) / GRID)), min(NX, int((x + r) / GRID) + 2)
    j0, j1 = max(0, int((y - r) / GRID)), min(NY, int((y + r) / GRID) + 2)
    if i0 >= i1 or j0 >= j1:
        return
    xs = (np.arange(i0, i1) + 0.5) * GRID
    ys = (np.arange(j0, j1) + 0.5) * GRID
    d = (xs[None, :] - x) ** 2 + (ys[:, None] - y) ** 2 <= r * r
    m[j0:j1, i0:i1] |= d


def stamp_rect(m, x0, x1, y0, y1):
    i0, i1 = max(0, int(x0 / GRID)), min(NX, int(math.ceil(x1 / GRID)))
    j0, j1 = max(0, int(y0 / GRID)), min(NY, int(math.ceil(y1 / GRID)))
    if i0 < i1 and j0 < j1:
        m[j0:j1, i0:i1] = True


def sweep(pts, hw, step=0.1):
    m = blank()
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(n + 1):
            t = k / n
            stamp_disk(m, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, hw)
    return m


def area(m):
    return float(m.sum()) * GRID * GRID


# ----------------------------------------------------------------------------- obstaculos rigidos (planta)
def rails():
    """Trilhos depois dos entalhes dos cabecalhos (os do R6V4): lista (x0, x1, y0, y1, fileira)."""
    return L.rail_rects(0)


def rail_height(row):
    """Altura do trilho da fileira: do piso (-8,1) ate a face de baixo da regua."""
    return zr(row) - L.RULER_T - Z_FLOOR


PROPOSED = {"m2": None, "posts": None, "wall": None}


def m2_pts(ru):
    if PROPOSED["m2"]:
        return [(ru["x0"] + dx, ru["y"] + 5.2) for dx in PROPOSED["m2"][ru["row"]]]
    return L.m2_points(ru)


def solid_masks():
    """Mascaras (raster) dos obstaculos rigidos: bossas M2, postes internos (circulo + lamina), postes de parede (os propostos, se PROPOSED estiver preenchido)."""
    boss, post, wall = blank(), blank(), blank()
    for ru in L.rulers(0):
        for mx, my in m2_pts(ru):
            stamp_disk(boss, mx, my, L.M2_BOSS_D / 2)
    for px, py in (PROPOSED["posts"] or L.pick_posts(0)):
        stamp_disk(post, px, py, 2.7)
        stamp_rect(post, px - 0.7, px + 0.7, py - 1.66, py + 2.34)
    for px, py in (PROPOSED["wall"] or L.wall_posts(0)):
        stamp_disk(wall, px, py, 3.0)
    return boss, post, wall


# ----------------------------------------------------------------------------- o laco do cabo entre reguas
def configure(out_u):
    """Muda a posicao do cabecalho OUT (u) e refaz as pecas dependentes (raio efetivo do laco e pecas de baixo da regua)."""
    global OUT_U, RLOOP
    OUT_U = out_u
    RLOOP = min(RC, d_link() / 2.0)
    build_under_parts()


def d_link():
    """Distancia em x entre o plugue OUT da regua A e o IN da regua B."""
    return (74.0 - OUT_U) + IN_U


def loop_a(F):
    """Perna reta de cada lado: F = 2a + pi R + (d - 2R) (duas curvas de 90 graus de raio R e uma reta de d - 2R entre elas)."""
    d = d_link()
    return (F - math.pi * RLOOP - max(0.0, d - 2 * RLOOP)) / 2.0


def loop_path(xj, y_row, a, side=0.0):
    """Polilinha (x, y) do cabo de uma juncao: sai do plugue OUT da regua A para tras (-y) por a, curva de 90 graus de raio R, reta ao longo de x, curva
    de 90 graus e perna de volta ate o plugue IN da regua B."""
    xa, xb = xj - (74.0 - OUT_U), xj + IN_U
    ye = y_row + Y_EXIT
    R = RLOOP
    pts = [(xa, ye), (xa, ye - a)]
    cy = ye - a
    for k in range(1, 46):
        t = math.pi + (math.pi / 2) * k / 45.0
        pts.append((xa + R + R * math.cos(t), cy + R * math.sin(t)))
    pts.append((xb - R, cy - R))
    for k in range(1, 46):
        t = 1.5 * math.pi + (math.pi / 2) * k / 45.0
        pts.append((xb - R + R * math.cos(t), cy + R * math.sin(t)))
    pts.append((xb, ye))
    return pts


def loop_body(xj, y_row, a):
    """Area ocupada pelo cabo e pelos dois plugues (para o entalhe nos trilhos): feixe + folga e a pegada de cada plugue (7,6 + 0,4 de folga)."""
    m = sweep(loop_path(xj, y_row, a), BW / 2 + CLR)
    xa, xb = xj - (74.0 - OUT_U), xj + IN_U
    for xc in (xa, xb):
        stamp_rect(m, xc - PLUG_W / 2 - 0.2, xc + PLUG_W / 2 + 0.2, y_row + Y_EXIT, y_row + LANE_Y0)
    return m


def path_len(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def junctions():
    out = []
    for r, y, x0, n in L.ROWS:
        row = [q for q in L.rulers(0) if q["row"] == r]
        for a, b in zip(row[:-1], row[1:]):
            out.append({"row": r, "xj": b["x0"], "y": y})
    return out


def a_max_for_row(row, y_row):
    """Maior perna reta que cabe dentro da parede (a borda do feixe a CLR da face interna): so conta a fileira 4 e as que chegam ao fundo."""
    ye = y_row + Y_EXIT
    return ye - RLOOP - BW / 2 - CLR - WALL_IN


# ----------------------------------------------------------------------------- analise
def analyse():
    rl = rails()
    boss, post, wall = solid_masks()
    res = {"parametros": {"F": F_LIST, "feixe": [BW, BT], "raio_min": RC_MIN, "raio_U": RLOOP, "out_u": OUT_U, "d": d_link(), "saida_plugue_y": Y_EXIT, "eixo_z": Z_AXIS}, "juncoes": []}
    rail_union = {}
    for Fk, F in F_LIST.items():
        a = loop_a(F)
        for j in junctions():
            r, xj, y = j["row"], j["xj"], j["y"]
            pts = loop_path(xj, y, a)
            body = loop_body(xj, y, a)
            ye = y + Y_EXIT
            apex_edge = ye - a - RLOOP - BW / 2          # borda do feixe no fundo do U
            fits_wall = apex_edge - CLR >= WALL_IN
            hit_wall_post = area(body & wall)
            hit_post = area(body & post)
            hit_boss = area(body & boss)
            # trilhos tocados (cada trilho e uma lista de segmentos)
            rails_hit = []
            lost_vol = 0.0
            lost_len = {}
            for (ra, rb, ya, yb, rr) in rl:
                sub = body[int(ya / GRID):int(math.ceil(yb / GRID)), int(ra / GRID):int(math.ceil(rb / GRID))]
                if sub.any():
                    cols = np.where(sub.any(axis=0))[0]
                    x_lo, x_hi = ra + cols[0] * GRID, ra + (cols[-1] + 1) * GRID
                    rails_hit.append({"fileira": rr, "x0": round(x_lo, 1), "x1": round(x_hi, 1), "y0": round(ya, 2), "y1": round(yb, 2)})
                    lost_vol += (x_hi - x_lo) * (yb - ya) * rail_height(rr)
                    lost_len[rr] = lost_len.get(rr, 0) + (x_hi - x_lo)
            # canais (entre os trilhos de dentro) atravessados
            res["juncoes"].append({
                "F": Fk, "fileira": r, "xj": xj, "perna_a": round(a, 2), "ponta_y": round(apex_edge, 2),
                "cabe_na_parede": bool(fits_wall), "falta_mm": round(max(0.0, WALL_IN + CLR - apex_edge), 2),
                "area_mm2_conflito": {"poste_parede": round(hit_wall_post, 1), "poste_interno": round(hit_post, 1), "bossa_M2": round(hit_boss, 1)},
                "trilhos_cruzados": rails_hit, "trilho_removido_mm3": round(lost_vol), "trilho_removido_mm": {str(k): round(v, 1) for k, v in lost_len.items()},
                "caixa_xy": [round(xj - (74.0 - OUT_U) - PLUG_W / 2 - 0.2, 1), round(xj + IN_U + PLUG_W / 2 + 0.2, 1), round(apex_edge - CLR, 1), round(y + LANE_Y0, 1)],
            })
    return res


def main_analise():
    res = analyse()
    json.dump(res, open(os.path.join(OUT, "ligacao_h.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for j in res["juncoes"]:
        print(j["F"], "fileira", j["fileira"], "perna %.1f" % j["perna_a"], "ponta y %.1f" % j["ponta_y"], "parede", j["cabe_na_parede"], "falta", j["falta_mm"],
              j["area_mm2_conflito"], "trilho -%d mm3" % j["trilho_removido_mm3"], j["trilho_removido_mm"])
    return res




# ============================================================================= parte 2: perfil vertical, folgas, cruzamentos, cabo da placa, cabecalhos
RULER = json.load(open(os.path.join(HERE, "..", "pcb", "regua", "posicao_regua8.json"), encoding="utf-8"))
UNDER_PARTS = []


def build_under_parts():
    """Pecas do lado de baixo da regua (ref, patio_uv, altura) com os J1/J2 novos (SM06B lateral: 2,95 mm, pegada 9,4 x 5,55 a partir da boca em v -7,5)."""
    UNDER_PARTS.clear()
    for ref, p in RULER["pecas"].items():
        if p["lado"] != "B" or ref in ("J1", "J2", "LK1", "LK2"):
            continue
        h = float(p["altura_mm"]) if p["altura_mm"] not in ("", None) else 0.0
        if ref.startswith("U") and ref != "U9":      # R8 file (R11V4): U1..U8 sensors, U9 the 595 (mid-ruler, u 74, rot 90)
            h = 0.8
        UNDER_PARTS.append((ref, p["patio_uv"], h))
    for ref, u in (("J1", IN_U), ("J2", OUT_U)):
        UNDER_PARTS.append((ref, [u - HDR_W / 2, LANE_Y0, u + HDR_W / 2, LANE_Y0 + HDR_FOOT], HDR_H))


build_under_parts()
PEG_U = [4.17, 14.33, 22.67, 32.83, 41.17, 51.33, 59.67, 69.83]


def ls_needed(drop):
    """Comprimento horizontal minimo para descer `drop` mm com curva suave de curvatura maxima 1/RC_MIN (z = drop (1 - cos(pi s / Ls)) / 2)."""
    return math.pi * math.sqrt(max(drop, 0.0) * RC_MIN / 2.0)


BT_REST = None


def z_rest():
    return Z_FLOOR + (BT if BT_REST is None else BT_REST) / 2.0


def cable_z(s_from_exit, drop, Ls):
    if s_from_exit >= Ls:
        return z_rest()
    return z_rest() + drop * (1 + math.cos(math.pi * s_from_exit / Ls)) / 2.0


def profile_clearance(row, F):
    """Folga vertical minima (mm) do feixe aos corpos e pecas de baixo das reguas ACIMA dele, ao longo do laco da juncao da fileira `row`."""
    j = [q for q in junctions() if q["row"] == row][0]
    a = loop_a(F)
    pts = loop_path(j["xj"], j["y"], a)
    z0 = axis_z(row)
    drop = z0 - z_rest()
    Ls = min(ls_needed(drop), path_len(pts) / 2.0)
    worst = {"valor": 1e9, "onde": ""}
    # amostra: s medido da saida de A (e simetrico na chegada em B)
    L_tot = path_len(pts)
    acc = 0.0
    for k in range(len(pts) - 1):
        seg = math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
        for t in (0.0, 0.5):
            s = acc + seg * t
            sd = min(s, L_tot - s)
            z = cable_z(sd, drop, Ls)
            x = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t
            y = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t
            top = z + (BT if BT_REST is None else BT_REST) / 2.0
            for ru in L.rulers(0):
                if ru["row"] == row:
                    continue
                zu = zr(ru["row"]) - L.RULER_T
                if ru["x0"] - 0.0 <= x <= ru["x0"] + L.RULER_L and ru["y"] - 7.0 - BW / 2 <= y <= ru["y"] + 7.0 + BW / 2:
                    c = zu - top
                    if c < worst["valor"]:
                        worst = {"valor": round(c, 2), "onde": "corpo da regua da fileira %d" % ru["row"]}
                    for ref, (u0, v0, u1, v1), h in UNDER_PARTS:
                        if ru["x0"] + u0 - BW / 2 <= x <= ru["x0"] + u1 + BW / 2 and ru["y"] + v0 - BW / 2 <= y <= ru["y"] + v1 + BW / 2:
                            c = zu - h - top
                            if c < worst["valor"]:
                                worst = {"valor": round(c, 2), "onde": "%s da regua da fileira %d" % (ref, ru["row"])}
                    for ui in PEG_U:
                        if abs(x - (ru["x0"] + ui)) < 0.85 + BW / 2 and abs(y - ru["y"]) < 0.85 + BW / 2:
                            c = zu - L.PEG_BELOW - top
                            if c < worst["valor"]:
                                worst = {"valor": round(c, 2), "onde": "pino de tecla da regua da fileira %d" % ru["row"]}
        acc += seg
    return {"fileira": row, "queda_mm": round(drop, 2), "Ls_precisa_mm": round(ls_needed(drop), 1), "perna_mm": round(a, 1), "perna_mais_curva_mm": round(path_len(pts) / 2.0, 1),
            "curva_ok": bool(ls_needed(drop) <= path_len(pts) / 2.0 + 1e-6), "folga_vertical_min_mm": worst["valor"], "onde": worst["onde"]}


def crossings(F):
    """Area (mm2) em que os feixes de juncoes de fileiras diferentes se sobrepoem em planta (cabo por cima de cabo)."""
    a = loop_a(F)
    ms = {}
    for j in junctions():
        ms[j["row"]] = sweep(loop_path(j["xj"], j["y"], a), BW / 2)
    out = {}
    for r in (1, 2, 3):
        out["%d x %d" % (r, r + 1)] = round(area(ms[r] & ms[r + 1]), 1)
    out["1 x 3"] = round(area(ms[1] & ms[3]), 1)
    out["2 x 4"] = round(area(ms[2] & ms[4]), 1)
    return out


def board_cable(row, F):
    """Cabo da placa (plugue em J60x, fios +x) ate o plugue IN da 1a regua (fios -y): curva de Bezier de comprimento F (como em layout_r4.cable_between)."""
    first = [q for q in L.rulers(0) if q["row"] == row][0]
    y = [r_[1] for r_ in L.ROWS if r_[0] == row][0]
    j_back = float(L.POS["metricas"]["mouth_x_fileiras"][str(row)]) + PLUG_D
    pin = (first["x0"] + IN_U, y + Y_EXIT)
    pts = L.cable_between((j_back, y), (1, 0), pin, (0, -1), F)
    return pts, (j_back, y), pin


def board_cable_report(row, F):
    pts, a, b = board_cable(row, F)
    boss, post, wall = solid_masks()
    body = sweep(pts, BW / 2 + CLR)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    rl = rails()
    crossed = []
    for (ra, rb, ya, yb, rr) in rl:
        sub = body[int(ya / GRID):int(math.ceil(yb / GRID)), int(ra / GRID):int(math.ceil(rb / GRID))]
        if sub.any():
            cols = np.where(sub.any(axis=0))[0]
            crossed.append({"fileira": rr, "x0": round(ra + cols[0] * GRID, 1), "x1": round(ra + (cols[-1] + 1) * GRID, 1), "y0": round(ya, 2), "y1": round(yb, 2)})
    return {"fileira": row, "F": F, "chord_xy": round(math.hypot(b[0] - a[0], b[1] - a[1]), 1),
            "caixa": [round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1)],
            "conflito_mm2": {"poste_parede": round(area(body & wall), 1), "poste_interno": round(area(body & post), 1), "bossa_M2": round(area(body & boss), 1)},
            "trilhos_cruzados": crossed, "comprimento_mm": round(path_len(pts), 1), "pts": pts}


def wall_posts_h(mod=0):
    """Proposta (nao aplicada): postes de parede a >= 12 mm das juncoes das fileiras 3 e 4 (o de x = 161,5 cai em cima do laco)."""
    Lx = L.length(mod)
    juncs = sorted(set(j["xj"] for j in junctions()))
    forb = [(80.0, 102.0)] + [(xj - (74.0 - OUT_U) - 7.0, xj + IN_U + 7.0) for xj in juncs]
    xs = [L.X_IF + 10.0]
    n = int(math.ceil((Lx - 10.0 - xs[0]) / 80.0))
    cand = [xs[0] + (Lx - 10.0 - xs[0]) * k / n for k in range(n + 1)]
    out = []
    for c in cand:
        for lo, hi in forb:
            if lo < c < hi:
                c = hi + 0.5 if (lo == 80.0 or abs(c - hi) <= abs(c - lo)) else lo - 0.5
        out.append(round(c, 2))
    # entre dois postes seguidos nao mais de 80 mm: acrescenta se preciso
    out = sorted(out)
    fixed = [out[0]]
    for c in out[1:]:
        while c - fixed[-1] > 80.0:
            m = fixed[-1] + 60.0
            for lo, hi in forb:
                if lo < m < hi:
                    m = lo - 0.5
            fixed.append(round(m, 2))
        fixed.append(c)
    return fixed


# ============================================================================= parte 3: figuras
ROWCOL = {1: "#DC2626", 2: "#2563EB", 3: "#059669", 4: "#9333EA"}


def hdr_box(ru, name):
    u = IN_U if name == "IN" else OUT_U
    return (ru["x0"] + u - HDR_W / 2, ru["x0"] + u + HDR_W / 2, ru["y"] + LANE_Y0, ru["y"] + LANE_Y0 + HDR_FOOT)


def plug_box(ru, name):
    u = IN_U if name == "IN" else OUT_U
    return (ru["x0"] + u - PLUG_W / 2, ru["x0"] + u + PLUG_W / 2, ru["y"] + Y_EXIT, ru["y"] + LANE_Y0)


def overlay(ax, mask, color, alpha=0.45, z=9):
    rgba = np.zeros(mask.shape + (4,))
    rgba[mask] = matplotlib.colors.to_rgba(color, alpha)
    ax.imshow(rgba, extent=(0, XMAX, YMAX, 0), origin="upper", interpolation="nearest", zorder=z, aspect="equal")


def removed_spans(F=45.8):
    """Vaos (continuos) cortados nos trilhos para o laco de cada juncao: (x0, x1, y0, y1, fileira_do_trilho, fileira_do_cabo)."""
    out = []
    a = loop_a(F)
    rl = rails()
    for j in junctions():
        body = loop_body(j["xj"], j["y"], a)
        for (ra, rb, ya, yb, rr) in rl:
            sub = body[int(ya / GRID):int(math.ceil(yb / GRID)), int(ra / GRID):int(math.ceil(rb / GRID))]
            if sub.any():
                cols = np.where(sub.any(axis=0))[0]
                out.append((ra + cols[0] * GRID, ra + (cols[-1] + 1) * GRID, ya, yb, rr, j["row"]))
    return out


def plan_figure(F=45.8):
    fig, ax = plt.subplots(figsize=(18.5, 8.6))
    rrect = PL.rrect
    Lx = L.length(0)
    rrect(ax, 0, 0, Lx, 100, L.CASE_R, fc="#F1EFE8", ec=PL.C["case"], lw=1.6, zorder=1)
    rrect(ax, 2, 2, Lx - 2, 98, L.CASE_R - 2, fc="none", ec=PL.C["case"], lw=0.8, zorder=2)
    x0b, y0b, x1b, y1b = L.BOARD_OUT
    rrect(ax, x0b, y0b, x1b, y1b, L.BOARD_R, fc=PL.C["board"], ec=PL.C["board_ec"], lw=1.0, zorder=3)
    ax.text(40, 50, "placa principal\n(interface)", ha="center", va="center", fontsize=8, color="#3B6D11")
    for k in ("J601", "J602", "J603", "J604"):
        a, b, c, d = L.P[k]["patio"]
        ax.add_patch(Rectangle((a, b), c - a, d - b, fc="#D4537E", ec="#9D174D", alpha=0.6, zorder=4))
        ax.text(a - 0.6, (b + d) / 2, k, ha="right", va="center", fontsize=5.8, zorder=12)
    rs = L.rulers(0)
    # trilhos (cinza) e vaos cortados (vermelho hachurado)
    for (ra, rb, ya, yb, rr) in rails():
        ax.add_patch(Rectangle((ra, ya), rb - ra, yb - ya, fc="#9CA3AF", ec="none", alpha=0.55, zorder=3))
    for (xa, xb, ya, yb, rr, cr) in removed_spans(F):
        ax.add_patch(Rectangle((xa, ya), xb - xa, yb - ya, fc="#FECACA", ec="#B91C1C", lw=0.6, hatch="xxx", zorder=5))
    for ru in rs:
        ax.add_patch(Rectangle((ru["x0"] + 0.2, ru["y"] - 7), L.RULER_L - 0.4, 14, fc=PL.C["ruler"], ec=PL.C["ruler_ec"], lw=0.7, alpha=0.55, zorder=3))
        for mx, my in m2_pts(ru):
            ax.add_patch(Circle((mx, my), L.M2_BOSS_D / 2, fc="#D1D5DB", ec="black", lw=0.5, alpha=0.8, zorder=6))
            ax.add_patch(Circle((mx, my), 1.9, fc="white", ec="black", lw=0.5, zorder=7))
        for mx, my in L.m2_points(ru):
            if PROPOSED["m2"] and all(abs(mx - q[0]) > 0.01 for q in m2_pts(ru)):
                ax.add_patch(Circle((mx, my), L.M2_BOSS_D / 2, fc="none", ec="#B91C1C", lw=1.0, ls=":", zorder=7))
    first = {r: x0 for r, _y, x0, _n in L.ROWS}
    for r, x, y in L.key_list(0):
        idx = int(round((x - first[r]) / L.PITCH))
        PL.key_cap(ax, x, y, L.note_name(r, idx), fs=6.4, z=5)
    for ru in rs:
        for nm in ("IN", "OUT"):
            hb, pb = hdr_box(ru, nm), plug_box(ru, nm)
            ax.add_patch(Rectangle((hb[0], hb[2]), hb[1] - hb[0], hb[3] - hb[2], fc="#FDE047", ec="black", lw=0.5, alpha=0.75, zorder=9))
            ax.add_patch(Rectangle((pb[0], pb[2]), pb[1] - pb[0], pb[3] - pb[2], fc="#FB7185", ec="black", lw=0.5, alpha=0.85, zorder=10))
    # lacos entre reguas
    a = loop_a(F)
    for j in junctions():
        pts = loop_path(j["xj"], j["y"], a)
        body = sweep(pts, BW / 2)
        overlay(ax, body, ROWCOL[j["row"]], 0.22, 8)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=ROWCOL[j["row"]], lw=1.6, zorder=11)
        ax.text(j["xj"], pts[len(pts) // 2][1] + 1.0, "fileira %d" % j["row"], ha="center", va="top", fontsize=6.4, color=ROWCOL[j["row"]], fontweight="bold", zorder=12)
    # cabos da placa (50,8)
    for r in (1, 2, 3, 4):
        pts, _a, _b = board_cable(r, 45.8)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#BE185D", lw=1.4, ls="--", zorder=11)
    # postes
    for px, py in L.pick_posts(0):
        ax.add_patch(Circle((px, py), 2.5, fc="#FED7AA", ec=PL.C["post"], lw=0.8, zorder=8))
    for px, py in (PROPOSED["posts"] or []):
        ax.add_patch(Circle((px, py), 2.7, fc="none", ec="#15803D", lw=1.4, ls="--", zorder=8))
    old = L.wall_posts(0)
    new = wall_posts_h(0)
    for px, py in old:
        ax.add_patch(Circle((px, py), 3.0, fc="#FED7AA", ec=PL.C["post"], lw=0.8, zorder=8))
    for px in new:
        for py in (7.0, 93.0):
            ax.add_patch(Circle((px, py), 3.0, fc="none", ec="#15803D", lw=1.4, ls="--", zorder=8))
    ax.plot([2.15, Lx - 2.15], [2.15, 2.15], color="#B91C1C", lw=1.0, zorder=12)
    ax.set_xlim(60, Lx + 6)
    ax.set_ylim(103, -3)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), o jogador esta embaixo (y = 100)")
    ax.set_title("R7V4 - ligacao H, 32 teclas: planta de TODAS as reguas com cabecalhos (amarelo), plugues (rosa), lacos do cabo de 45,8 mm uteis (cor por fileira), OUT em u 49,5, "
                 "vaos cortados nos trilhos (vermelho hachurado), cabos da placa (tracejado). Nome da nota em cada tecla.", fontsize=8.6)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h = [Patch(fc="#FDE047", ec="black", label="cabecalho SH (embaixo da regua)"), Patch(fc="#FB7185", ec="black", label="plugue SH"),
         Line2D([0], [0], color=ROWCOL[1], lw=2, label="laco, fileira 1 (45,8 mm)"), Line2D([0], [0], color=ROWCOL[2], lw=2, label="fileira 2"),
         Line2D([0], [0], color=ROWCOL[3], lw=2, label="fileira 3"), Line2D([0], [0], color=ROWCOL[4], lw=2, label="fileira 4 (cabe no limite: 0,3 mm da parede)"),
         Line2D([0], [0], color="#BE185D", lw=1.4, ls="--", label="cabo placa -> 1a regua (45,8 mm)"),
         Patch(fc="#FECACA", ec="#B91C1C", hatch="xxx", label="vao cortado no trilho (rebaixo)"), Patch(fc="#9CA3AF", alpha=0.55, label="trilho que fica"),
         Patch(fc="#FED7AA", ec=PL.C["post"], label="postes atuais"), Patch(fc="none", ec="#15803D", ls="--", label="postes de parede e internos propostos"), Patch(fc="none", ec="#B91C1C", ls=":", label="M2 atuais que mudam (os propostos estao em cinza)"),
         Line2D([0], [0], color="#B91C1C", lw=1.0, label="face interna da parede de tras (y 2,15)")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=6, fontsize=6.8, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "ligacao_h_planta_r7.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)


def present_rails_at(x, spans):
    """Trilhos (y0, y1, fileira) presentes na secao x (depois dos entalhes dos cabecalhos e dos vaos dos lacos)."""
    out = []
    for (ra, rb, ya, yb, rr) in rails():
        if not (ra <= x <= rb):
            continue
        cut = any(sa <= x <= sb and abs(sy0 - ya) < 0.01 and abs(sy1 - yb) < 0.01 for (sa, sb, sy0, sy1, _rr, _cr) in spans)
        out.append((ya, yb, rr, cut))
    return out


def section_figure(F=45.8, fname="ligacao_h_cortes_r8.png"):
    spans = removed_spans(F)
    a = loop_a(F)
    fig, axs = plt.subplots(4, 1, figsize=(17.0, 15.5))
    for ax, row in zip(axs, (1, 2, 3, 4)):
        j = [q for q in junctions() if q["row"] == row][0]
        xs = j["xj"] - (74.0 - OUT_U)               # secao pela perna da regua A (saida)
        y0 = j["y"]
        ax.add_patch(Rectangle((0, L.Z_BOT), 100, L.Z_FLOOR - L.Z_BOT, fc="#6B7280", ec="black", lw=0.6, zorder=2))     # piso
        ax.add_patch(Rectangle((L.Y_BACK, L.Z_BOT), L.WALL, 40, fc="#6B7280", ec="black", lw=0.6, zorder=2))                   # parede de tras (y -2..0)
        ax.add_patch(Rectangle((0, L.CEILING if False else 12.6), 100, 2.0, fc="#D3D1C7", ec="black", lw=0.5, zorder=2))   # telhado da interface (referencia)
        for ru in L.rulers(0):
            if not (ru["x0"] <= xs <= ru["x0"] + L.RULER_L):
                continue
            z1 = zr(ru["row"]) - L.RULER_T
            ax.add_patch(Rectangle((ru["y"] - 7, z1), 14, L.RULER_T, fc=ROWCOL[ru["row"]], ec="black", lw=0.6, alpha=0.8, zorder=6))
            ax.text(ru["y"], z1 + L.RULER_T + 0.4, "regua f.%d" % ru["row"], ha="center", fontsize=7, color=ROWCOL[ru["row"]], zorder=12, clip_on=True)
            for ya, yb, rr, cut in present_rails_at(xs, spans):
                if rr == ru["row"] and abs(((ya + yb) / 2) - ru["y"]) < 8:
                    ax.add_patch(Rectangle((ya, Z_FLOOR), yb - ya, z1 - Z_FLOOR, fc="none" if cut else "#9CA3AF", ec="#B91C1C" if cut else "black",
                                           lw=0.8, ls="--" if cut else "-", hatch="xx" if cut else None, alpha=0.85, zorder=5))
        # cabecalho e plugue da regua da fileira `row`
        z1 = zr(row) - L.RULER_T
        ax.add_patch(Rectangle((y0 + LANE_Y0, z1 - HDR_H), HDR_D, HDR_H, fc="#FDE047", ec="black", lw=0.7, zorder=7))
        ax.add_patch(Rectangle((y0 + Y_EXIT, axis_z(row) - PLUG_H / 2), PLUG_D, PLUG_H, fc="#FB7185", ec="black", lw=0.7, zorder=8))
        # perfil do cabo (centro) ao longo da perna A e raio de dobra
        z0 = axis_z(row)
        drop = z0 - z_rest()
        Ls = ls_needed(drop)
        ye = y0 + Y_EXIT
        half = (2 * a + math.pi * RLOOP + max(0.0, d_link() - 2 * RLOOP)) / 2.0
        Ls = min(ls_needed(drop), half)
        s = np.linspace(0, a + math.pi * RLOOP / 2.0, 200)
        yy = np.where(s <= a, ye - s, ye - a - RLOOP * np.sin(np.clip((s - a) / RLOOP, 0, math.pi / 2)))
        zz = np.array([cable_z(v, drop, Ls) for v in s])
        ax.plot(yy, zz, color="#111827", lw=3.6, solid_capstyle="round", zorder=11)
        ax.plot(yy, zz, color="#F59E0B", lw=2.0, solid_capstyle="round", zorder=12)
        apex = ye - a - RLOOP - BW / 2
        ax.axvline(WALL_IN, color="#B91C1C", lw=1.0, zorder=3)
        ok = apex - CLR >= WALL_IN
        ax.text(0.01, 0.97, "laco atras do plugue: perna %.1f + raio %.1f = %.1f mm (F = %.1f, OUT em u %.1f, d = %.1f)\nqueda do cabo %.1f mm em %.1f mm (curva suave, R >= %.0f mm)\nlargura do rebaixo em x: %.1f mm"
                % (a, RLOOP, a + RLOOP, F, OUT_U, d_link(), drop, Ls, RC_MIN, d_link() + PLUG_W + 0.4), transform=ax.transAxes, va="top", fontsize=7.5)
        ax.set_title("Corte y-z em x = %.2f (perna de saida da regua A, fileira %d): bolso sob a regua %.1f mm; plug eixo z %.1f; %s" %
                     (xs, row, zr(row) - L.RULER_T - Z_FLOOR, z0, "o laco CABE (borda a %.1f mm da parede)" % (apex - WALL_IN) if ok else
                      "o laco NAO CABE: passa %.1f mm da parede de tras" % (WALL_IN + CLR - apex)), fontsize=9, color="black" if ok else "#B91C1C")
        ax.set_xlim(L.Y_BACK - 1, y0 + 9)
        for t_ in ax.texts:
            t_.set_clip_on(True)
        ax.set_ylim(L.Z_BOT - 0.6, 21)
        ax.set_xlabel("y (mm) -> frente (o jogador)")
        ax.set_ylabel("z (mm)")
        ax.invert_xaxis() if False else None
        ax.set_aspect("equal")
    fig.suptitle("R8V4 - ligacao H (OUT u 47,5): cortes do rebaixo em cada fileira (trilho hachurado = vao cortado; piso NAO muda: 2,0 mm)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, fname), dpi=130, bbox_inches="tight")
    plt.close(fig)


def option_data():
    """Cabecalho da regua: 4 posicoes/orientacoes testadas em 2D na juncao A|B da fileira 2 (u rel. a regua A; v para o jogador)."""
    # pecas de baixo da regua que podem ser tocadas: pinos de tecla (D1,7, 1,5 abaixo), sensores, 595, capacitores; regua vizinha
    res = []
    plug_w, plug_d, hdr_w, hdr_d = PLUG_W, PLUG_D, HDR_W, HDR_FOOT
    u0_ = OUT_U
    def rect_overlap(a, b):
        w = min(a[1], b[1]) - max(a[0], b[0])
        h = min(a[3], b[3]) - max(a[2], b[2])
        return w * h if w > 0 and h > 0 else 0.0
    pegs = [(u - 0.85, u + 0.85, -0.85, 0.85) for u in PEG_U]            # em A; B repete com +74
    pegs = pegs + [(u + 74.0 - 0.85, u + 74.0 + 0.85, -0.85, 0.85) for u in PEG_U]
    under = []
    for ref, (u0, v0, u1, v1), h in UNDER_PARTS:
        if ref.startswith(("J", "LK")):
            continue
        under.append((u0, u1, v0, v1, ref))
        under.append((u0 + 74.0, u1 + 74.0, v0, v1, ref))
    options = {
        "A  boca para tras (-y), faixa de tras (R4V4), OUT em u %.1f" % OUT_U: {"hdr": (u0_ - hdr_w / 2, u0_ + hdr_w / 2, -7.5, -7.5 + hdr_d), "plug": (u0_ - plug_w / 2, u0_ + plug_w / 2, -7.5 - plug_d, -7.5)},
        "B  boca para frente (+y), faixa da frente": {"hdr": (u0_ - hdr_w / 2, u0_ + hdr_w / 2, 7.5 - hdr_d, 7.5), "plug": (u0_ - plug_w / 2, u0_ + plug_w / 2, 7.5, 7.5 + plug_d)},
        "C  boca para a ponta (+x), cabecalho na ponta, v = -4,5": {"hdr": (74.0 - hdr_d, 74.0, -4.5 - hdr_w / 2, -4.5 + hdr_w / 2), "plug": (74.0, 74.0 + plug_d, -4.5 - plug_w / 2, -4.5 + plug_w / 2)},
        "D  boca para dentro (-x), plugue sob a propria regua, v = -4,5": {"hdr": (74.0 - hdr_d, 74.0, -4.5 - hdr_w / 2, -4.5 + hdr_w / 2), "plug": (74.0 - hdr_d - plug_d, 74.0 - hdr_d, -4.5 - plug_w / 2, -4.5 + plug_w / 2)},
    }
    for name, o in options.items():
        hdr, plug = o["hdr"], o["plug"]
        tol = 0.15
        def hit(a, b):
            return min(a[1], b[1]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[2], b[2]) > tol
        peg_hits = sum(1 for p_ in pegs if hit(plug, p_) or hit(hdr, p_))
        part_hits = [u[4] for u in under if hit(plug, (u[0], u[1], u[2], u[3])) or hit(hdr, (u[0], u[1], u[2], u[3]))]
        plug_front = plug[3] > 7.0 and plug[2] > 0 and plug[0] < 74.0                  # plugue na frente da regua: pisa na regua da fileira da frente (mais baixa)
        res.append({"opcao": name, "hdr": hdr, "plug": plug, "pinos_tocados": peg_hits, "pecas_tocadas": sorted(set(part_hits)),
                    "cabecalho_fora_da_regua_mm": round(max(0.0, -7.0 - hdr[2], hdr[3] - 7.0), 2),
                    "plugue_na_frente_colide_regua_da_frente": bool(plug_front)})
    return res


def header_figure():
    opts = option_data()
    fig, axs = plt.subplots(1, 4, figsize=(18.0, 6.2))
    for ax, o in zip(axs, opts):
        ax.add_patch(Rectangle((52, -7), 22, 14, fc=PL.C["ruler"], ec=PL.C["ruler_ec"], alpha=0.7, zorder=1))
        ax.add_patch(Rectangle((74.4, -7), 22, 14, fc=PL.C["ruler"], ec=PL.C["ruler_ec"], alpha=0.35, zorder=1, ls="--"))
        ax.text(63, 5.7, "regua A", ha="center", fontsize=8)
        ax.text(85, 5.7, "regua B", ha="center", fontsize=8)
        for u in PEG_U:
            for off in (0, 74.0):
                ax.add_patch(Circle((u + off, 0), 0.85, fc="#F59E0B", ec="black", lw=0.5, zorder=4))
        for ref, (u0, v0, u1, v1), h in UNDER_PARTS:
            if ref.startswith(("J", "LK")):
                continue
            for off in (0, 74.0):
                ax.add_patch(Rectangle((u0 + off, v0), u1 - u0, v1 - v0, fc="#6366F1", ec="none", alpha=0.45, zorder=3))
        h, p = o["hdr"], o["plug"]
        ax.add_patch(Rectangle((h[0], h[2]), h[1] - h[0], h[3] - h[2], fc="#FDE047", ec="black", lw=1.0, alpha=0.8, zorder=6))
        ax.add_patch(Rectangle((p[0], p[2]), p[1] - p[0], p[3] - p[2], fc="#FB7185", ec="black", lw=1.0, alpha=0.8, zorder=7))
        bad = o["pinos_tocados"] > 0 or o["cabecalho_fora_da_regua_mm"] > 0 or o["pecas_tocadas"] or o["plugue_na_frente_colide_regua_da_frente"]
        if bad:
            msg = "FALHA: pinos de tecla tocados %d; pecas %s;\ncabecalho %.1f mm fora da regua; plugue sobre a regua da frente: %s" % (
                o["pinos_tocados"], ",".join(o["pecas_tocadas"]) or "-", o["cabecalho_fora_da_regua_mm"], "sim" if o["plugue_na_frente_colide_regua_da_frente"] else "nao")
        else:
            msg = "SEM conflito: cabecalho dentro da regua;\no plugue sai para tras e passa sob a regua da fileira de tras (folga vertical 2,3 a 4,3 mm)"
        ax.set_title(o["opcao"] + "\n" + msg, fontsize=7.4, color="#B91C1C" if bad else "#15803D")
        ax.set_xlim(52, 96)
        ax.set_ylim(15, -15)
        ax.set_aspect("equal")
        ax.set_xlabel("u (mm), junção A | B em u = 74")
        ax.set_ylabel("v (mm), + para o jogador")
    fig.suptitle("R7V4 - posicao e orientacao do cabecalho SH na regua (planta da juncao; pinos de tecla D1,7 em laranja, sensores/595/capacitores em azul)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "ligacao_h_cabecalhos_r7.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)
    return opts


def assembly_figure(F=45.8):
    """Passos em casa (corte y-z pela perna da regua B de uma juncao da fileira 2; a regua B e a que se acrescenta)."""
    row = 2
    j = [q for q in junctions() if q["row"] == row][0]
    y0 = j["y"]
    z1 = zr(row) - L.RULER_T
    ye = y0 + Y_EXIT
    a = loop_a(F)
    z0 = axis_z(row)
    drop = z0 - z_rest()
    Ls = ls_needed(drop)
    steps = [
        ("1  Base com os rebaixos; regua A ja parafusada e ligada", 0),
        ("2  O cabo de estoque (plugue na ponta A ja ligada) deitado no rebaixo", 0),
        ("3  A regua B erguida 12 mm acima do degrau; o plugue livre sobe ate o cabecalho", 12),
        ("4  O plugue entra (movimento -y da regua, 4 mm): cabecalho e plugue travados", 12),
        ("5  A regua desce; o cabo cai no rebaixo, nada fica sob a regua", 0),
        ("6  O M2 (1 ou 2 por regua) desce na bossa; regua B presa; pinca fina para trocar uma regua depois", 0),
    ]
    fig, axs = plt.subplots(3, 2, figsize=(16.0, 11.0))
    for ax, (title, lift) in zip(axs.flat, steps):
        n = int(title.split()[0])
        ax.add_patch(Rectangle((0, L.Z_BOT), 100, L.Z_FLOOR - L.Z_BOT, fc="#6B7280", ec="black", lw=0.6, zorder=2))
        for ya, yb, cut in ((y0 + 4.2, y0 + 7.0, False), (y0 - 7.0, y0 - 4.2, n >= 3)):
            ax.add_patch(Rectangle((ya, Z_FLOOR), yb - ya, z1 - Z_FLOOR, fc="none" if cut else "#9CA3AF", ec="#B91C1C" if cut else "black", lw=0.7,
                                   ls="--" if cut else "-", hatch="xx" if cut else None, zorder=5))
        # a regua B (a que sobe e desce); a regua de tras (fileira 3) em cinza
        if n >= 3:
            ax.add_patch(Rectangle((y0 - 7, z1 + lift), 14, L.RULER_T, fc=ROWCOL[row], ec="black", lw=0.6, alpha=0.85, zorder=6))
            ax.add_patch(Rectangle((y0 - 6.89, z1 + lift - 4.3), 5.84, 4.3, fc="#FDE047", ec="black", lw=0.7, zorder=7))
        z3 = zr(3) - L.RULER_T
        ax.add_patch(Rectangle((y0 - 16.02 - 7, z3), 14, L.RULER_T, fc=ROWCOL[3], ec="black", lw=0.6, alpha=0.5, zorder=6))
        for ya, yb, cut in ((y0 - 16.02 + 4.2, y0 - 16.02 + 7.0, True), (y0 - 16.02 - 7.0, y0 - 16.02 - 4.2, True)):
            ax.add_patch(Rectangle((ya, Z_FLOOR), yb - ya, z3 - Z_FLOOR, fc="none", ec="#B91C1C", hatch="xx", lw=0.7, ls="--", zorder=5))
        # cabo
        s = np.linspace(0, a, 160)
        yy = ye - s
        if n == 1:
            pass
        elif n == 2:
            ax.plot(ye - np.linspace(0, a, 100), np.full(100, z_rest()), color="#F59E0B", lw=3.0, zorder=11)
            ax.add_patch(Rectangle((ye, z_rest()), L.PLUG_D, 3.9, fc="#FB7185", ec="black", lw=0.7, zorder=8))
        elif n == 3:
            ax.add_patch(Rectangle((ye - 3.0, z0 + lift - 1.95), L.PLUG_D, 3.9, fc="#FB7185", ec="black", lw=0.7, zorder=8, alpha=0.9))
            sx = np.linspace(0, 20, 120)
            zz = z_rest() + (z0 + lift - z_rest()) * np.clip(1 - sx / 14.0, 0, 1) ** 1.6
            ax.plot(ye - 3.0 - sx, zz, color="#F59E0B", lw=3.0, zorder=11)
            ax.annotate("12 mm", xy=(y0 + 8.5, z1), xytext=(y0 + 8.5, z1 + 12), arrowprops=dict(arrowstyle="<->"), fontsize=8)
        elif n == 4:
            ax.add_patch(Rectangle((ye, z0 + lift - 1.95), L.PLUG_D, 3.9, fc="#FB7185", ec="black", lw=0.7, zorder=8))
            sx = np.linspace(0, 20, 120)
            zz = z_rest() + (z0 + lift - z_rest()) * np.clip(1 - sx / 14.0, 0, 1) ** 1.6
            ax.plot(ye - sx, zz, color="#F59E0B", lw=3.0, zorder=11)
            ax.annotate("", xy=(ye + 0.2, z0 + lift + 3.4), xytext=(ye - 4.2, z0 + lift + 3.4), arrowprops=dict(arrowstyle="->", lw=1.4, color="#B91C1C"))
            ax.text(ye - 2, z0 + lift + 4.0, "plugue +y (4 mm)", fontsize=7, ha="center", color="#B91C1C")
        else:
            ax.add_patch(Rectangle((ye, z0 - 1.95), L.PLUG_D, 3.9, fc="#FB7185", ec="black", lw=0.7, zorder=8))
            half = (2 * a + math.pi * RLOOP + max(0.0, d_link() - 2 * RLOOP)) / 2.0
            Ls5 = min(ls_needed(drop), half)
            s5 = np.linspace(0, a + math.pi * RLOOP / 2.0, 200)
            yy5 = np.where(s5 <= a, ye - s5, ye - a - RLOOP * np.sin(np.clip((s5 - a) / RLOOP, 0, math.pi / 2)))
            zz5 = np.array([cable_z(v, drop, Ls5) for v in s5])
            ax.plot(yy5, zz5, color="#F59E0B", lw=3.0, zorder=11)
            if n == 6:
                for mx in (y0 + 5.2,):
                    ax.add_patch(Rectangle((mx - 1.0, z1 - 6.0), 2.0, 6.0 + L.RULER_T + 1.6, fc="#374151", ec="black", lw=0.6, zorder=9))
                    ax.add_patch(Rectangle((mx - 1.9, z1 + L.RULER_T), 3.8, 1.6, fc="#374151", ec="black", lw=0.6, zorder=9))
                ax.text(y0 + 5.2, z1 - 7.3, "M2", ha="center", fontsize=7)
        ax.set_title(title, fontsize=9)
        ax.set_xlim(y0 - 40, y0 + 10)
        ax.set_ylim(L.Z_BOT - 0.6, 22)
        ax.set_aspect("equal")
        ax.set_xlabel("y (mm) -> frente")
    fig.suptitle("R8V4 - montagem oficial em casa da ligacao H (corte y-z pela perna de uma juncao da fileira 2; ordem das fileiras: da frente para tras)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "ligacao_h_montagem_r8.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def rails_left_h(F=45.8):
    """Trilhos que sobram sob cada regua depois de TODOS os vaos (cabecalhos + lacos + plugues): fracao e maior vao seguido; flecha conservadora
    (regua de 14 x 1,2 mm de FR-4, E = 22 GPa, apoiada so nas pontas do vao, 3 N no meio, sem contar o outro trilho nem as bossas)."""
    cut = blank()
    a = loop_a(F)
    for j in junctions():
        cut |= loop_body(j["xj"], j["y"], a)
    out = {}
    I = 14.0 * L.RULER_T ** 3 / 12.0
    for ru in L.rulers(0):
        for side, sgn in (("fundo", -1), ("frente", 1)):
            ya, yb = sorted((ru["y"] + sgn * L.RAIL_IN, ru["y"] + sgn * L.RAIL_OUT))
            ym = (ya + yb) / 2
            xa, xb = ru["x0"] + 0.2, ru["x0"] + L.RULER_L - 0.2
            base = blank()
            for (ra, rb, y0_, y1_, rr) in rails():
                if rr == ru["row"] and abs((y0_ + y1_) / 2 - ym) < 0.1 and ra >= xa - 0.01 and rb <= xb + 0.01:
                    stamp_rect(base, ra, rb, y0_, y1_)
            row = (base & ~cut)[int(ym / GRID), int(xa / GRID):int(xb / GRID)]
            frac = float(row.mean()) if len(row) else 0.0
            # maior vao sem trilho
            best, cur = 0, 0
            for v in row:
                cur = 0 if v else cur + 1
                best = max(best, cur)
            gap = best * GRID
            delta = 3.0 * gap ** 3 / (48.0 * 22000.0 * I)
            out["f%d.%d %s" % (ru["row"], ru["k"], side)] = {"resta_%": round(100 * frac), "maior_vao_mm": round(gap, 1), "flecha_conservadora_mm": round(delta, 3)}
    return out


def main_figuras():
    configure(L.OUT_X)
    section_figure()
    assembly_figure()
    section_figure(50.8, "ligacao_h_cortes_r8_50.png")
    return None


def pick_posts_h():
    """Postes internos fora de u 50..62 de cada regua (o cabecalho OUT em u 49,5 ocupa u 44,8..54,2 e o poste de u 55,5 cai nele)."""
    rows = {r: x0 for r, _y, x0, _n in L.ROWS}
    ok = []
    for px, py in L.post_candidates(0):
        r = [q for q in L.ROWS if abs(q[1] - L.ROWP / 3.0 - 0 - py) < 0.01 or abs(q[1] - L.ROWP / 3.0 - py) < 0.01]
        row = r[0][0] if r else None
        x0 = rows[row] - L.PITCH / 2
        u = (px - x0) % 74.0
        if not (46.0 < u < 64.0):
            ok.append((px, py))
    n = 5
    idx = sorted(set(int(round(i * (len(ok) - 1) / (n - 1))) for i in range(n)))
    return [ok[i] for i in idx]


def search_m2(cable_zone):
    """Pares de M2 por fileira (u1, u2) que nao encostam em plugue, perna ou cabo da placa (bossa D6 + 0,4): o par mais afastado, o mais centrado."""
    res = {}
    rs = L.rulers(0)
    for row in (1, 2, 3, 4):
        feas = []
        for u in np.arange(12.0, 64.0, 0.5):
            good = True
            for ru in [q for q in rs if q["row"] == row]:
                t = blank()
                stamp_disk(t, ru["x0"] + u, ru["y"] + 5.2, L.M2_BOSS_D / 2 + 0.4)
                if (t & cable_zone).any():
                    good = False
            if good:
                feas.append(float(u))
        best = None
        for i, u1 in enumerate(feas):
            for u2 in feas[i + 1:]:
                if u2 - u1 < 18.0:
                    continue
                score = (u2 - u1) - 2.0 * abs((u1 + u2) / 2.0 - 37.0)
                if best is None or score > best[0]:
                    best = (score, u1, u2)
        res[row] = (best[1], best[2]) if best else None
    return res


def sensibilidade():
    """Fileira 4 (a mais apertada) contra a posicao do OUT (u) e o comprimento F: perna, profundidade pedida e livre atras da boca do cabecalho."""
    out = []
    keep = OUT_U
    for u in (68.1, 55.0, 49.5, 47.5, 44.5):
        configure(u)
        for F in (45.8, 50.8):
            a = loop_a(F)
            need = -Y_EXIT + LANE_Y0 * 0 + a + RLOOP + BW / 2 + CLR
            avail = 25.97 + Y_EXIT - WALL_IN                      # do plugue (face de tras) ate a parede interna
            falta = a + RLOOP + BW / 2 + CLR - avail
            out.append({"out_u": u, "d": round(d_link(), 1), "F": F, "perna_a": round(a, 2), "raio": round(RLOOP, 2), "reta_5_ok": bool(a >= STRAIGHT),
                        "profundidade_pedida_atras_do_plugue": round(a + RLOOP + BW / 2 + CLR, 1), "livre": round(avail, 2), "folga_mm": round(-falta, 2),
                        "fecha": bool(falta <= 0)})
    configure(keep)
    return out


def full_report():
    configure(49.5)
    res = {"juncoes_postes_atuais": analyse()["juncoes"]}
    # zona de cabos (lacos de F = 45,8 e 50,8 e cabos da placa) para procurar os M2
    zone = blank()
    for F in (45.8, 50.8):
        for j in junctions():
            zone |= loop_body(j["xj"], j["y"], loop_a(F))
        for r in (1, 2, 3, 4):
            pts, _a, _b = board_cable(r, F)
            zone |= sweep(pts, BW / 2 + CLR)
    res["m2_propostos"] = {str(k): v for k, v in search_m2(zone).items()}
    PROPOSED["m2"] = {k: v for k, v in search_m2(zone).items()}
    PROPOSED["posts"] = pick_posts_h()
    PROPOSED["wall"] = [(x, 7.0) for x in wall_posts_h(0)] + [(x, 93.0) for x in wall_posts_h(0)]
    res["postes_internos_propostos"] = PROPOSED["posts"]
    res["juncoes"] = analyse()["juncoes"]
    res["sensibilidade_fileira4"] = sensibilidade()
    res["perfil_vertical"] = {Fk: [profile_clearance(r, F) for r in (1, 2, 3, 4)] for Fk, F in F_LIST.items()}
    global BT_REST
    BT_REST = 5.6
    res["perfil_vertical_em_pe"] = {Fk: [profile_clearance(r, F) for r in (1, 2, 3, 4)] for Fk, F in F_LIST.items()}
    BT_REST = None
    res["cruzamentos_mm2"] = {Fk: crossings(F) for Fk, F in F_LIST.items()}
    res["cabo_da_placa"] = {}
    for r in (1, 2, 3, 4):
        for F in (45.8, 50.8, 100.0):
            b = board_cable_report(r, F)
            b.pop("pts")
            res["cabo_da_placa"]["f%d_%g" % (r, F)] = json.loads(json.dumps(b, default=float))
    res["postes_parede_propostos"] = wall_posts_h(0)
    res["trilhos_que_sobram"] = {Fk: rails_left_h(F) for Fk, F in F_LIST.items()}
    res["cabecalhos"] = option_data()
    json.dump(res, open(os.path.join(OUT, "ligacao_h.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
    return res


# ============================================================================= R8V4: recessos, M2 e postes aplicados no modelo oficial
HOLE_FORBID_U = (24.5, 33.0)    # a regua leva o 595 (u 26,56..28,94, v 2,5..5,9) e C5 (u 30,2..31,2, v 6,2) ao lado do furo M2 (v +5,2): sem furo nesta faixa
HOLE_U_RANGE = (4.0, 70.0)


def plugs_and_headers_mask():
    m = blank()
    for ru in L.rulers(0):
        for nm in ("IN", "OUT"):
            if nm == "OUT" and ru["last"] and not L.OUT_ON_LAST:
                continue                       # R11V4: no OUT header on the R8
            hb, pb = hdr_box(ru, nm), plug_box(ru, nm)
            stamp_rect(m, hb[0], hb[1], hb[2], hb[3])
            if nm == "OUT" and ru["last"]:
                continue                       # no plug on the last ruler of a row
            stamp_rect(m, pb[0] - 0.2, pb[1] + 0.2, pb[2], pb[3])
    return m


def cable_zone():
    """Zona de cabos: lacos e cabos da placa nos dois comprimentos (45,8 e 50,8), mais plugues e cabecalhos de todas as reguas."""
    zone = plugs_and_headers_mask()
    for F in F_LIST.values():
        for j in junctions():
            zone |= loop_body(j["xj"], j["y"], loop_a(F))
        for r in (1, 2, 3, 4):
            pts, _a, _b = board_cable(r, F)
            zone |= sweep(pts, BW / 2 + CLR)
    return zone


def hole_feasible_per_ruler(zone, us=(18.5, 37.0, 55.5), bossd=None):
    """Para cada regua (fileira, k): quais dos tres vaos entre as teclas (u 18,5 / 37 / 55,5: o unico lugar onde a cabeca do M2 cabe entre as carcacas)
    deixam o boss D6 (+0,4) livre da zona de cabos, plugues e cabecalhos."""
    out = {}
    d = (bossd or (L.M2_BOSS_D + 0.8)) / 2
    for ru in L.rulers(0):
        ok = []
        for u in us:
            t = blank()
            stamp_disk(t, ru["x0"] + u, ru["y"] + 5.2, d)
            if not (t & zone).any():
                ok.append(u)
        out[(ru["row"], ru["k"])] = ok
    return out


def hole_feasible(zone):
    """Por fileira: u (passo 0,5) em que o boss D6 (+0,4) de TODAS as reguas da fileira nao toca zona de cabos, plugue ou cabecalho."""
    feas = {}
    rs = L.rulers(0)
    for row in (1, 2, 3, 4):
        ok = []
        for u in np.arange(HOLE_U_RANGE[0], HOLE_U_RANGE[1] + 0.01, 0.5):
            if HOLE_FORBID_U[0] < u < HOLE_FORBID_U[1]:
                continue
            good = True
            for ru in [q for q in rs if q["row"] == row]:
                t = blank()
                stamp_disk(t, ru["x0"] + u, ru["y"] + 5.2, L.M2_BOSS_D / 2 + 0.4)
                if (t & zone).any():
                    good = False
            if good:
                ok.append(float(u))
        feas[row] = ok
    return feas


def post_feasible(zone):
    """Postes internos candidatos (L.post_candidates) que nao tocam a zona de cabos (circulo D5,4 + lamina 1,4 x 4,0, folga 0,4)."""
    ok = []
    for px, py in L.post_candidates(0):
        t = blank()
        stamp_disk(t, px, py, 2.7 + 0.4)
        stamp_rect(t, px - 0.7 - 0.4, px + 0.7 + 0.4, py - 1.66 - 0.4, py + 2.34 + 0.4)
        ok.append(((px, py), not (t & zone).any()))
    return ok


def recess_notches(Fs=(45.8, 50.8), min_stub=3.0):
    """Rebaixos nos trilhos para os lacos e os cabos da placa (os dois comprimentos): um retangulo por trilho cruzado (so do que sobra dos entalhes
    de cabecalho e plugue), e tambem os tocos de trilho com menos de `min_stub` mm que sobrariam entre dois cortes (nao se imprimem nem seguram nada).
    Devolve a lista de notches no formato de layout_r4.notches()."""
    body = blank()
    for F in Fs:
        for j in junctions():
            body |= loop_body(j["xj"], j["y"], loop_a(F))
        for r in (1, 2, 3, 4):
            pts, _a, _b = board_cable(r, F)
            body |= sweep(pts, BW / 2 + CLR)
    out = []
    for (ra, rb, ya, yb, rr) in L.rail_rects(0, recess=False):
        cuts = []
        sub = body[int(ya / GRID):int(math.ceil(yb / GRID)), int(ra / GRID):int(math.ceil(rb / GRID))]
        if sub.any():
            cols = np.where(sub.any(axis=0))[0]
            runs, start = [], cols[0]
            for a, b in zip(cols[:-1], cols[1:]):
                if b - a > 5:                      # a gap of more than 0,5 mm starts a new run (one recess per crossing, not one for the whole rail)
                    runs.append((start, a))
                    start = b
            runs.append((start, cols[-1]))
            cuts = [(max(ra, ra + c0 * GRID - 0.1), min(rb, ra + (c1 + 1) * GRID + 0.1)) for c0, c1 in runs]
        # stubs: the pieces left between the cuts (and the piece's own ends) shorter than min_stub go too
        edges = [ra] + [v for c in sorted(cuts) for v in c] + [rb]
        for k in range(0, len(edges), 2):
            a_, b_ = edges[k], edges[k + 1]
            if 0 < b_ - a_ < min_stub:
                cuts.append((a_ - 0.05, b_ + 0.05))
        # merge touching cuts
        cuts.sort()
        merged = []
        for c in cuts:
            if merged and c[0] <= merged[-1][1] + 0.05:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
            else:
                merged.append(c)
        for c0, c1 in merged:
            out.append({"x0": round(c0, 3), "x1": round(c1, 3), "y0": ya - 0.01, "y1": yb + 0.01, "row": rr,
                        "tipo": "rebaixo do cabo (laço ou cabo da placa)"})
    return out


def main_r8():
    """Numeros da R8V4 (OUT u 47,5, case de 102 mm): folga na fileira 4, perfil vertical, cruzamentos, cabos da placa, recessos, M2, fita colada."""
    global BT_REST
    configure(L.OUT_X)
    res = {"parametros": {"out_u": OUT_U, "d": d_link(), "raio": RLOOP, "parede_interna_y": WALL_IN, "profundidade_case": L.CASE[1]}}
    # fileira 4 por profundidade do case
    rows4 = []
    for back in (0.0, -1.0, -1.5, -2.0, -2.5):
        wall_in = back + L.WALL + 0.15
        for F in (45.8, 50.8):
            a = loop_a(F)
            avail = 25.97 + Y_EXIT - wall_in
            need = a + RLOOP + BW / 2 + CLR
            rows4.append({"y_costas": back, "profundidade": round(100 - back, 1), "F": F, "perna_a": round(a, 2), "pede": round(need, 2), "livre": round(avail, 2),
                          "folga_mm": round(avail - need, 2), "borda_do_feixe_a_parede_mm": round(avail - need + CLR, 2)})
    res["fileira4_por_profundidade"] = rows4
    res["sensibilidade_OUT_costas_0"] = sensibilidade()
    res["perfil_vertical"] = {str(F): [profile_clearance(r, F) for r in (1, 2, 3, 4)] for F in F_LIST.values()}
    BT_REST = BW                                      # fita colada em pe: 5,6 de altura
    res["perfil_vertical_fita_em_pe"] = {str(F): [profile_clearance(r, F) for r in (1, 2, 3, 4)] for F in F_LIST.values()}
    BT_REST = None
    res["cruzamentos_mm2"] = {str(F): crossings(F) for F in F_LIST.values()}
    res["cabo_da_placa"] = {}
    for r in (1, 2, 3, 4):
        for F in (45.8, 50.8):
            b = board_cable_report(r, F)
            b.pop("pts")
            res["cabo_da_placa"]["f%d_%g" % (r, F)] = json.loads(json.dumps(b, default=float))
    zone = cable_zone()
    res["m2_viaveis_por_regua"] = {"%d.%d" % k: v for k, v in hole_feasible_per_ruler(zone).items()}
    res["m2_viaveis_boss_D5"] = {"%d.%d" % k: v for k, v in hole_feasible_per_ruler(zone, bossd=5.0).items()}
    res["postes_viaveis"] = [[list(c), bool(ok)] for c, ok in post_feasible(zone)]
    rec = L.RECESS if L.RECESS else recess_notches()
    res["rebaixos"] = [{k: (round(float(v), 2) if not isinstance(v, str) else v) for k, v in n.items()} for n in rec]
    res["rebaixo_por_juncao_mm"] = {"x": round(d_link() + PLUG_W + 0.4, 1), "y_45_8": round(-Y_EXIT + loop_a(45.8) + RLOOP + BW / 2 + CLR, 1),
                                    "y_50_8": round(-Y_EXIT + loop_a(50.8) + RLOOP + BW / 2 + CLR, 1)}
    res["trilhos_que_sobram"] = {"%d.%d" % k: v for k, v in L.rails_left(0).items()}
    json.dump(res, open(os.path.join(OUT, "ligacao_h_r8.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
    return res


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if arg == "r8":
        r = main_r8()
    if arg in ("figuras", "tudo"):
        main_figuras()
    print("ok")


