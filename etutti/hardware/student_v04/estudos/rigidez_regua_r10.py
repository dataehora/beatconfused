"""eTutti Student V4 (R10V4 item 2, R8 ruler of 148 mm): how much a ruler bends under a key press (3 N) with the tray's rails after the cable recesses and the new M2 pairs.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/rigidez_regua_r10.py

Model (1D finite elements, Euler-Bernoulli beam along the ruler, 0.5 mm elements; numpy only):
  * the ruler is a FR-4 strip 148 x 14 x 1.2 mm, E = 18 GPa: EI = E * 14 * 1.2^3 / 12 = 36 288 N mm^2; its ends are free (the neighbour ruler is ignored);
  * it rests on the tray's two rails (front v +4.2..7.0, back v -7.0..-4.2) wherever they are not cut by a notch or recess: both rails present = rigid support;
    only one present = the load at the axis reaches that rail through the ruler's own width (a 5.6 mm cantilever strip, k = 3 E t^3 / (12 l^3) per mm
    of length = 44 N/mm per mm); none = unsupported;
  * the M2 screws (the two of the row) hold the ruler at their bosses: rigid in both directions;
  * 3 N pressed at each of the four key centres in turn (u 9.25 + 18.5 k, k = 0..7); the number is the worst deflection at the loaded node over the 8 rulers.
Lower bound ("pessimista"): a one-rail stretch counts as unsupported too (k = 0).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "case"))
import layout_r4 as L    # noqa: E402
import ligacao_h as H    # noqa: E402

E, T, W = 18000.0, 1.2, 14.0
EI = E * W * T ** 3 / 12.0
K_ONE = 3.0 * E * T ** 3 / 12.0 / 5.6 ** 3          # N/mm per mm of length
STEP = 0.5
LOAD = 3.0
KEY_U = tuple(9.25 + 18.5 * k for k in range(8))
RIGID = 1e7


def rails_of(ru, rr):
    """Intervals (u0, u1) where the front / back rail exist for this ruler."""
    out = {"frente": [], "fundo": []}
    for (xa, xb, ya, yb, row) in rr:
        if row != ru["row"] or xb <= ru["x0"] or xa >= ru["x0"] + L.RULER_L:
            continue
        key = "frente" if (ya + yb) / 2 > ru["y"] else "fundo"
        out[key].append((xa - ru["x0"], xb - ru["x0"]))
    return out


def present(iv, u):
    return any(a - 1e-9 <= u <= b + 1e-9 for a, b in iv)


def solve(ru, rr, load_u, one_rail_k):
    n_el = int(round((L.RULER_L - 0.4) / STEP))
    u0 = 0.2
    nn = n_el + 1
    ndof = 2 * nn
    Kg = np.zeros((ndof, ndof))
    le = STEP
    ke = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                 [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
    for e in range(n_el):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        Kg[np.ix_(idx, idx)] += ke
    iv = rails_of(ru, rr)
    m2 = [x - ru["x0"] for x, _y in L.m2_points(ru)]
    for i in range(nn):
        u = u0 + i * STEP
        w = STEP if 0 < i < nn - 1 else STEP / 2
        f, b = present(iv["frente"], u), present(iv["fundo"], u)
        if f and b:
            Kg[2 * i, 2 * i] += RIGID * w
        elif f or b:
            Kg[2 * i, 2 * i] += one_rail_k * w
    for u in m2:
        i = int(round((u - u0) / STEP))
        Kg[2 * i, 2 * i] += RIGID
    # the load goes on the node nearest the key
    res = []
    for ku in load_u:
        F = np.zeros(ndof)
        i = int(round((ku - u0) / STEP))
        F[2 * i] = -LOAD                               # pressed down
        wv = np.linalg.solve(Kg + 1e-9 * np.eye(ndof), F)
        res.append(abs(wv[2 * i]))
    return res


def solve_grid(ru, rr, load_u):
    """Grillage of three lines along the ruler (back v -5.6, axis 0, front +5.6), each a beam of a third of the width (4.67 mm), joined by transverse beams
    (E t^3 / 12 per mm of length over the 5.6 mm between lines); dofs per node: w, theta_x, theta_y (torsion of each third included). The rails
    hold the front and back nodes where they exist (rigid, up only in reality: the load pushes down so that is exact); the M2 boss holds the front node
    (v +5.2 ~ +5.6) in both directions; the load is on the axis node."""
    n_el = int(round((L.RULER_L - 0.4) / STEP))
    nn = n_el + 1
    u0 = 0.2
    nid = lambda i, j: 3 * (i * 3 + j)            # first dof of node (i, j): w; +1 theta_x; +2 theta_y
    nd = 3 * nn * 3
    Kg = np.zeros((nd, nd))
    le = STEP
    EIl = E * (W / 3.0) * T ** 3 / 12.0
    kl = EIl / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                  [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
    lt = 5.6
    EIt = E * le * T ** 3 / 12.0                   # a transverse strip as wide as the element spacing
    kt = EIt / lt ** 3 * np.array([[12, 6 * lt, -12, 6 * lt], [6 * lt, 4 * lt ** 2, -6 * lt, 2 * lt ** 2],
                                  [-12, -6 * lt, 12, -6 * lt], [6 * lt, 2 * lt ** 2, -6 * lt, 4 * lt ** 2]])
    for j in range(3):
        for i in range(n_el):
            idx = [nid(i, j), nid(i, j) + 2, nid(i + 1, j), nid(i + 1, j) + 2]
            Kg[np.ix_(idx, idx)] += kl
    for i in range(nn):
        for j in range(2):
            idx = [nid(i, j), nid(i, j) + 1, nid(i, j + 1), nid(i, j + 1) + 1]
            Kg[np.ix_(idx, idx)] += kt
    GJ = E / 2.6 * (W / 3.0) * T ** 3 / 3.0        # torsion of each third of the strip (G = E / 2(1 + 0.3)): the twist couples theta_x along x
    for j in range(3):
        for i in range(n_el):
            a, b = nid(i, j) + 1, nid(i + 1, j) + 1
            Kg[a, a] += GJ / le
            Kg[b, b] += GJ / le
            Kg[a, b] -= GJ / le
            Kg[b, a] -= GJ / le
    iv = rails_of(ru, rr)
    for i in range(nn):
        u = u0 + i * STEP
        if present(iv["fundo"], u):
            Kg[nid(i, 0), nid(i, 0)] += RIGID
        if present(iv["frente"], u):
            Kg[nid(i, 2), nid(i, 2)] += RIGID
    for u in [x - ru["x0"] for x, _y in L.m2_points(ru)]:
        i = int(round((u - u0) / STEP))
        Kg[nid(i, 2), nid(i, 2)] += RIGID
    res = []
    for ku in load_u:
        F = np.zeros(nd)
        i = int(round((ku - u0) / STEP))
        F[nid(i, 1)] = -LOAD
        wv = np.linalg.solve(Kg + 1e-9 * np.eye(nd), F)
        res.append(abs(wv[nid(i, 1)]))
    return res


def main():
    H.configure(L.OUT_X)
    L.RECESS[:] = H.recess_notches()
    rr = L.rail_rects(0)
    out = {"EI_Nmm2": EI, "k_um_trilho": K_ONE, "regua": {}}
    worst = {"real": 0.0, "faixa": 0.0, "pessimista": 0.0}
    for ru in L.rulers(0):
        d_real = solve_grid(ru, rr, KEY_U)
        d_strip = solve(ru, rr, KEY_U, K_ONE)
        d_pess = solve(ru, rr, KEY_U, 0.0)
        iv = rails_of(ru, rr)
        kept = {k: round(100 * sum(b - a for a, b in v) / (L.RULER_L - 0.4)) for k, v in iv.items()}
        gap = {}
        for k, v in iv.items():
            v = sorted(v)
            g = [(v[i + 1][0] - v[i][1]) for i in range(len(v) - 1)]
            gap[k] = round(max(g), 1) if g else 0.0
        out["regua"]["R%d.%d" % (ru["row"], ru["k"])] = {"m2_u": [round(x - ru["x0"], 1) for x, _y in L.m2_points(ru)], "trilho_que_resta_%": kept, "maior_vao_mm": gap,
                                                          "flexao_grelha_mm": [round(float(d), 4) for d in d_real], "flexao_faixa_mm": [round(float(d), 4) for d in d_strip], "flexao_pessimista_mm": [round(float(d), 4) for d in d_pess]}
        worst["real"] = max(worst["real"], max(d_real))
        worst["faixa"] = max(worst.get("faixa", 0.0), max(d_strip))
        worst["pessimista"] = max(worst["pessimista"], max(d_pess))
    out["pior_mm"] = {k: round(float(v), 4) for k, v in worst.items()}
    out["montante"] = montante()
    json.dump(out, open(os.path.join(HERE, "rigidez_regua_r10.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k, v in out["regua"].items():
        print(k, v["m2_u"], v["trilho_que_resta_%"], v["maior_vao_mm"], v["flexao_grelha_mm"], v["flexao_faixa_mm"], v["flexao_pessimista_mm"])
    print("pior", out["pior_mm"])


def montante():
    """The rail itself (PA12 MJF, E = 1700 MPa, no safety factor on E): (a) vertical shortening under 3 N spread over a 5 mm length of the 2.8 mm wide rail,
    for the highest rail (row 4, 13.9 mm above the floor); (b) a sideways 1 N at the top of an isolated 10 mm piece of that rail, cantilevered from the floor
    (what a rail would do with NO riser and NO end wall: the worst piece left by a notch); (c) the same piece tied by the 2 mm riser (a 4.8 mm thick wall)."""
    Ep = 1700.0
    h = 13.9
    t = 2.8
    a = 3.0 * h / (Ep * t * 5.0)
    I1 = 10.0 * t ** 3 / 12.0
    b = 1.0 * h ** 3 / (3 * Ep * I1)
    I2 = 10.0 * (t + 2.0) ** 3 / 12.0
    c = 1.0 * h ** 3 / (3 * Ep * I2)
    return {"montante_mais_alto_h_mm": h, "encurtamento_3N_mm": round(a, 5), "lateral_1N_peca_de_10mm_isolada_mm": round(b, 4), "lateral_1N_com_riser_4_8mm_mm": round(c, 4)}


if __name__ == "__main__":
    main()
    print(montante())
