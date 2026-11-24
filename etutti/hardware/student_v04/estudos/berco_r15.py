"""R15V4 item 4.3: how the ruler rests on the tray: (A) the two 2.8 mm rails of R14V4 against (B) a continuous cradle under the whole ruler with pockets only where the ruler has
parts under it (0.3 mm clear, pockets closer than 1.5 mm merged).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/berco_r15.py

Measures, per ruler and for the instrument (32 keys, 4 x R8):
  * support: % of the ruler's underside (147.6 x 14 mm, raster 0.1 mm) that rests on the tray (rails or cradle, after every notch, recess, pocket and the bolt holes, plus the D6 bosses
    for A); the longest stretch of the ruler's length with no support at all on the centre line, front line or back line;
  * deflection at 3 N under each key (grillage of three lines with torsion, the model of estudos/rigidez_regua_r10.py; B adds the cradle as a rigid support of the centre line
    outside the pockets);
  * volume of the base (CadQuery builds, case/out/r4_32_base_antes.stl / _depois.stl) and MJF cost at US$ 0.28 per cm3 (the R10V4 rate).
"""
import inspect
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "case"))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402
import ligacao_h as H    # noqa: E402
import rigidez_regua_r10 as RG    # noqa: E402

os.environ.setdefault("ETUTTI_CRADLE", "1")
import case_r4 as R      # noqa: E402

PIX = 0.1
USD_CM3 = 0.28


def pockets_v0():
    """(u0, u1) of the pockets that contain the centre line v = 0."""
    return [(p[0], p[2]) for p in R.cradle_pockets() if p[1] <= 0.0 <= p[3]]


def solve_grid_cradle():
    src = inspect.getsource(RG.solve_grid)
    marker = "    res = []\n    for ku in load_u:"
    add = ("    for i in range(nn):\n        u = u0 + i * STEP\n"
           "        if not any(p0 <= u <= p1 for p0, p1 in POCKETS_V0):\n            Kg[nid(i, 1), nid(i, 1)] += RIGID\n")
    assert marker in src
    src = src.replace(marker, add + marker).replace("def solve_grid(", "def solve_grid_cradle(")
    ns = dict(RG.__dict__)
    ns["POCKETS_V0"] = pockets_v0()
    exec(src, ns)
    return ns["solve_grid_cradle"]


def support_masks(ru, rr, nts, pockets):
    """Boolean masks (v, u) of the ruler's underside: A (rails + D6 bosses), B (cradle)."""
    nu, nv = int(round((L.RULER_L - 0.4) / PIX)), int(round(14.0 / PIX))
    us = 0.2 + (np.arange(nu) + 0.5) * PIX
    vs = -7.0 + (np.arange(nv) + 0.5) * PIX
    U, V = np.meshgrid(us, vs)
    A = np.zeros_like(U, dtype=bool)
    for (xa, xb, ya, yb, row) in rr:
        if row != ru["row"]:
            continue
        A |= (U + ru["x0"] >= xa) & (U + ru["x0"] <= xb) & (V + ru["y"] >= ya) & (V + ru["y"] <= yb)
    cut = np.zeros_like(A)
    for nt in nts:                                              # notches and recesses cut from rails and from the cradle alike
        cut |= (U + ru["x0"] >= nt["x0"]) & (U + ru["x0"] <= nt["x1"]) & (V + ru["y"] >= nt["y0"]) & (V + ru["y"] <= nt["y1"])
    holes = np.zeros_like(A)
    bosses = np.zeros_like(A)
    for (mx, my) in L.m2_points(ru):
        holes |= (U + ru["x0"] - mx) ** 2 + (V + ru["y"] - my) ** 2 <= 1.2 ** 2
        bosses |= (U + ru["x0"] - mx) ** 2 + (V + ru["y"] - my) ** 2 <= L.M2_BOSS_D ** 2 / 4
    A = (A | (bosses & ~cut)) & ~holes
    B = ~cut                                                     # the cradle fills the whole width ...
    for (u0, v0, u1, v1, dep) in pockets:                       # ... except the pockets
        B &= ~((U >= u0) & (U <= u1) & (V >= v0) & (V <= v1))
    B &= ~holes
    return A, B, us


def main():
    H.configure(L.OUT_X)
    L.RECESS[:] = H.recess_notches()
    rr = L.rail_rects(0)
    nts = L.notches(0)
    pockets = R.cradle_pockets()
    gridB = solve_grid_cradle()
    out = {"pockets_u_v_prof": [[round(x, 2) for x in p] for p in pockets], "regua": {}}
    worstA = worstB = 0.0
    areaA = areaB = tot = 0.0
    for ru in L.rulers(0):
        A, B, us = support_masks(ru, rr, nts, pockets)
        dA = RG.solve_grid(ru, rr, RG.KEY_U)
        dB = gridB(ru, rr, RG.KEY_U)
        worstA, worstB = max(worstA, max(dA)), max(worstB, max(dB))
        aA, aB = 100.0 * A.mean(), 100.0 * B.mean()
        areaA += A.sum()
        areaB += B.sum()
        tot += A.size
        # longest run along u where no mask column keeps support on the front line / back line / centre line (rows v ~ +5.6, -5.6, 0)
        def gap(mask, v):
            row = mask[int(round((v + 7.0) / PIX))]
            best = cur = 0
            for x in row:
                cur = 0 if x else cur + 1
                best = max(best, cur)
            return round(best * PIX, 1)
        out["regua"]["R%d" % ru["row"]] = {"apoio_A_%": round(aA, 1), "apoio_B_%": round(aB, 1),
                                          "maior_vao_sem_apoio_mm_A": {"tras": gap(A, -5.6), "centro": gap(A, 0.0), "frente": gap(A, 5.6)},
                                          "maior_vao_sem_apoio_mm_B": {"tras": gap(B, -5.6), "centro": gap(B, 0.0), "frente": gap(B, 5.6)},
                                          "flecha_A_mm": round(float(max(dA)), 4), "flecha_B_mm": round(float(max(dB)), 5)}
    vol = {}
    for k in ("antes", "depois"):
        p = os.path.join(HERE, "..", "case", "out", "r4_32_%s.json" % k)
        if os.path.exists(p):
            vol[k] = json.load(open(p, encoding="utf-8"))["volume_cm3"]
    out["resumo"] = {"apoio_A_%": round(100 * areaA / tot, 1), "apoio_B_%": round(100 * areaB / tot, 1), "flecha_pior_A_mm": round(float(worstA), 4), "flecha_pior_B_mm": round(float(worstB), 5),
                     "volume_cm3": vol, "custo_extra_MJF_US$": round((vol.get("depois", {}).get("base", 0) - vol.get("antes", {}).get("base", 0)) * USD_CM3, 1)}
    json.dump(out, open(os.path.join(HERE, "berco_r15.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k, v in out["regua"].items():
        print(k, v)
    print(out["resumo"])


if __name__ == "__main__":
    main()
