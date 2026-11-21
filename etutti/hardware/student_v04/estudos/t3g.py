"""eTutti Student V4 (R3V4): numbers behind the T3-G study. numpy only (the STEP part of the work is in the FIT_CHECK, measured with CadQuery).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/t3g.py

Writes estudos/t3g.json:
  1. latch window of the KS-20 (Orange drawing, page 5, left view at 900 dpi: 90.0 px/mm from the 5.00 dimension; +-0.03 mm read error)
  2. vertical play of a grade of thickness t held by the barbs (t = 1.2, 1.5, 1.6)
  3. dipole fit of the Hall flux (102 Gs at 0.3 mm, 905 Gs at 4.1 mm) and the effect of a thicker regua / the Low Profile Jade (680 Gs, estimated)
  4. deck without preload: 3 N on one key, thickness x interior posts (the R2V4 grillage, preload 0)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t3_deck as T    # noqa: E402

# ---- 1. latch (measured on the drawing; heights above the seat)
CATCH_ROOT, CATCH_TIP = 3.69, 3.16     # up-facing flank of the barb: root at the arm's wall (x = 6.94), tip at x = 7.52 (15.00 over the tips)
X_ROOT, X_TIP, X_HOLE = 6.94, 7.52, 7.00
SHOULDER = 5.00                        # +-0.05, underside of the upper housing (the grade's top rests here)


def flank_z(x):
    return CATCH_ROOT - (x - X_ROOT) * (CATCH_ROOT - CATCH_TIP) / (X_TIP - X_ROOT)


def latch():
    z_hole = flank_z(X_HOLE)           # where the hole edge (x = 7.00) meets the flank
    out = {"flanco_raiz_z": CATCH_ROOT, "flanco_ponta_z": CATCH_TIP, "z_no_furo_14_00": round(z_hole, 3),
           "janela_nominal_mm": round(SHOULDER - z_hole, 2), "janela_ate_a_ponta_mm": round(SHOULDER - CATCH_TIP, 2), "placas": {}}
    for t, tol in ((1.2, 0.12), (1.5, 0.05), (1.6, 0.16)):
        bottom = SHOULDER - t
        play = bottom - z_hole
        engage = (flank_z(X_HOLE) - bottom) / (CATCH_ROOT - CATCH_TIP) * (X_TIP - X_ROOT) if play < 0 else 0.0
        out["placas"][str(t)] = {"fundo_da_placa_z": round(bottom, 2), "folga_vertical_nominal_mm": round(play, 2),
                                 "folga_faixa_mm": [round(play - tol - 0.05, 2), round(play + tol + 0.05, 2)],
                                 "penetracao_do_flanco_mm": round(engage, 2)}
    return out


# ---- 3. dipole
def dipole():
    r = (905.0 / 102.0) ** (1 / 3)
    d0 = (4.1 * r - 0.3) / (r - 1)                  # distance at rest (x = 0), from (d0 - 0.3) / (d0 - 4.1) = r
    db = d0 - 4.1                                   # distance at the bottom of the travel
    res = {"d_repouso_mm": round(d0, 2), "d_fundo_mm": round(db, 2), "dBdx_fundo_Gs_por_mm": round(3 * 905 / db)}
    for name, extra in (("regua 1,2 (como Gateron/V3)", 0.0), ("regua 1,6 (+0,4)", 0.4), ("regua 1,2 +-0,12 (pior)", 0.12)):
        d = db + extra
        res[name] = {"fluxo_fundo_Gs": round(905 * (db / d) ** 3), "fluxo_repouso_Gs": round(905 * (db / (d + 4.1)) ** 3)}
    jade = {}
    for L in (3.5, 3.3):
        b_bot = 680.0
        d_rest = db + L
        jade[str(L)] = {"fluxo_fundo_Gs": 680, "fluxo_repouso_Gs_estimado": round(680 * (db / d_rest) ** 3, 1),
                        "swing_Gs": round(680 - 680 * (db / d_rest) ** 3), "dBdx_fundo_Gs_por_mm": round(3 * 680 / db)}
    res["jade_lp_estimado(mesmo d_fundo, mesma geometria de ima: NAO medido)"] = jade
    sens = 15.0                                      # mV/mT, BA3 at 3.3 V (ELETRONICA.md)
    res["BA3_excursao_V_KS20"] = round((905 - 90) / 10 * sens / 1000, 2)
    res["BA3_excursao_V_Jade"] = round((680 - 87) / 10 * sens / 1000, 2)
    res["BA3_tensao_no_fundo_V_KS20"] = round(1.65 + 905 / 10 * sens / 1000, 2)
    return res


# ---- 4. deck
def deck():
    out = {}
    for m, mesh, ns in ((0, 4.0, (0, 5, 10)), (3, 6.0, (0, 14, 28))):
        for t in (2.0, 2.5, 3.0):
            r, _ = T.deck_study(m, mesh, 0.0, t, ns)
            out["%d teclas, deck %.1f mm" % (28 + 16 * m, t)] = {k: v["3N_numa_tecla_mm"] for k, v in r["interiores"].items()}
    return out


if __name__ == "__main__":
    res = {"presilhas": latch(), "dipolo": dipole(), "deck_3N_sem_precarga_mm_por_n_de_postes": deck()}
    json.dump(res, open(os.path.join(HERE, "t3g.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
