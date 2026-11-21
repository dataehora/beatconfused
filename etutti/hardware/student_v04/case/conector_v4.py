"""eTutti Student V4 (R4V4 task 3): the ruler's connector zone, plan (zoom) and section through row 1's IN header (x = 95.1).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/conector_v4.py
Writes case/renders/ruler_conector_v4.png.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R                  # noqa: E402
import corte_v4 as K                 # noqa: E402
import planta_v4 as PL               # noqa: E402

L = R.L


def main():
    tray, ru, cn = R.tray(0), R.rulers_solid(0), R.connectors(0)
    x0 = L.rulers(0)[[q["row"] for q in L.rulers(0)].index(1)]["x0"]
    xs = x0 + L.IN_X
    fig, axs = plt.subplots(1, 2, figsize=(17, 8), gridspec_kw={"width_ratios": [1.0, 1.15]})
    PL.draw(axs[0], (78, 140), detail=False, sockets=False)
    axs[0].set_ylim(86, 40)
    axs[0].set_title("Planta: filas 1 e 2, começo das réguas (cabeçalho amarelo, plugue rosa, cabo, entalhes hachurados)", fontsize=9)
    for name, solid, col in (("bandeja", tray, "#9CA3AF"), ("régua", ru, "#86EFAC"), ("cabeçalho", cn["cabecalhos"], "#FDE047"),
                             ("plugue", cn["plugues"], "#FB7185"), ("pinos", cn["pinos"], "#111827"), ("sensor", cn["sensores"], "#6366F1")):
        K.fill(axs[1], K.polys(solid, xs), fc=col, ec="#222222", lw=0.5, alpha=0.9)
    axs[1].set_xlim(38, 92)
    axs[1].set_ylim(-11, 6)
    axs[1].set_aspect("equal")
    axs[1].set_title("Corte em x = %.1f (cabeçalho IN da fileira 1 e a fileira 2 atrás); o plugue passa sob a régua mais alta" % xs, fontsize=9)
    axs[1].set_xlabel("y (mm) -> frente")
    axs[1].set_ylabel("z (mm)")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "renders", "ruler_conector_v4.png"), dpi=130)
    print("ok")


if __name__ == "__main__":
    main()
