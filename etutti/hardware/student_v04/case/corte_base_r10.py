"""R11V4 item 2: cross sections of the robust base across the four rows (y-z planes), from the real solids of case_r4.py.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/corte_base_r10.py  ->  renders/corte_base_r15.png
A: x = 150 (between M2 holes: rails, risers, rulers, key housings, lid); B: x = 116.95 (M2 boss of rows 2 and 4 and the interior post (116.95; 52.67));
C: x = 107.7 (M2 boss of rows 1 and 3, post (107.7; 68.69)); D: x = 92 (through the IN plugs and board cables of rows 1 and 3).
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R      # noqa: E402
import corte_v4 as C     # noqa: E402

L = R.L


def main():
    tray, lid, ru, sc = R.tray(0), R.lid(0), R.rulers_solid(0), R.screws(0)
    keys = R.T.key_bodies(0, 0.0)
    cn = R.connectors(0)
    up = R.under_parts(0)
    parts = [("tampa", lid, "#E5E1D6"), ("bandeja", tray, "#9CA3AF"), ("teclas", keys, "#FBCFE8"), ("réguas", ru, "#4ADE80"), ("parafusos", sc, "#6B7280"),
             ("cabeçalhos", cn["cabecalhos"], "#222222"), ("plugues", cn["plugues"], "#FFFFFF"), ("peças sob a régua", up, "#F59E0B")]
    planes = [(150.0, "A: x = 150 mm, entre os furos M2: trilhos, risers entre fileiras (a frente fechada), réguas, carcaças, tampa"),
              (116.95, "B: x = 116,95 mm: bossa M2 das fileiras 2 e 4 e poste interno (116,95; 52,67)"),
              (107.7, "C: x = 107,7 mm: bossa M2 das fileiras 1 e 3 e poste interno (107,7; 68,69)"),
              (92.0, "D: x = 92 mm: plugues IN e túneis dos cabos da placa (fileiras 1 e 3)")]
    fig, axs = plt.subplots(4, 1, figsize=(15, 20))
    for ax, (x0, tt) in zip(axs, planes):
        for name, solid, col in parts:
            C.fill(ax, C.polys(solid, x0), fc=col, ec="#222222", lw=0.4, alpha=0.9)
        ax.set_xlim(-3, 102)
        ax.set_ylim(-11.5, 23)
        ax.set_aspect("equal")
        ax.set_title(tt, fontsize=10)
        ax.set_xlabel("y (mm)  ->  frente (jogador); fileira 4 atrás (y ~ 26), fileira 1 na frente (y ~ 74)")
        ax.set_ylabel("z (mm)")
        for r, y, _x, _n in L.ROWS:
            ax.text(y, 21.0, "fileira %d" % r, ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(R.HERE, "renders", "corte_base_r15.png"), dpi=130)
    print("ok")


if __name__ == "__main__":
    main()
