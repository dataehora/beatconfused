"""eTutti Student V4 (R1V4 D1): dimensional drawing of the KS-20 in the T3 stack (one key of row 1, section along the row's width).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/ks20_desenho.py
Numbers: Gateron drawing KS-20TF10B045NW-X72 (2023-09-13) + case_f2.py. '~' = estimated (not dimensioned in the drawing).
Writes case/renders/ks20_pilha_T3.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "case", "renders", "ks20_pilha_T3.png")

fig, ax = plt.subplots(figsize=(11, 10))
ax.set_aspect("equal")
# z levels from the tray's top (Pm = 0): rail 6.9 (row 1 step), ruler 1.2, housing 11.1, foam 1.0, deck 3.0
Z_RAIL = 6.9
Z_R0, Z_R1 = Z_RAIL, Z_RAIL + 1.2
Z_H = Z_R1 + 11.1
Z_F = Z_H + 1.0
Z_D = Z_F + 3.0
col = {"rail": "#8F8C85", "rul": "#2F7D4F", "key": "#EDE8DA", "foam": "#D9822B", "deck": "#C9C5BB", "cap": "#F1ECE1"}


def R(x0, x1, z0, z1, c, ec="k", lw=0.6):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=col[c], ec=ec, lw=lw))


R(-9, 9, 0, 0.0001, "rail")
R(-8.0, 8.0, -2.0, 0, "rail")                                   # tray floor (cut off)
R(-7.8, -5.0, 0, Z_R0, "rail")
R(5.0, 7.8, 0, Z_R0, "rail")                                    # rails
R(-7.8, 7.8, Z_R0, Z_R1, "rul")                                  # ruler 15.6 x 1.2
R(-7.0, 7.0, Z_R1, Z_R1 + 5.0, "key")                            # bottom body 14 x 14 (0..5)
R(-7.55, 7.55, Z_R1 + 5.0, Z_R1 + 8.4, "key")                    # housing 15.1 (section across the rows)
ax.add_patch(Polygon([(-7.55, Z_R1 + 8.4), (7.55, Z_R1 + 8.4), (5.7, Z_H), (-5.7, Z_H)], fc=col["key"], ec="k", lw=0.6))
R(-2.1, 2.1, Z_H, Z_H + 3.6, "key")                              # stem
R(-5.5, -3.7, Z_H, Z_F, "foam")
R(3.7, 5.5, Z_H, Z_F, "foam")
R(-12, -3.5, Z_F, Z_D, "deck")
R(3.5, 12, Z_F, Z_D, "deck")                                    # deck 3 mm with the 7 mm hole


def dim(z0, z1, x, txt, side=1):
    ax.annotate("", xy=(x, z0), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(x + side * 0.6, (z0 + z1) / 2, txt, fontsize=9, va="center", ha="left" if side > 0 else "right")


dim(0, Z_R0, 14.5, "degrau da base: 6,9 (fileira 1; 8,9 / 10,9 / 13,9 nas 2-4)")
dim(Z_R0, Z_R1, 14.5, "regua 1,2 +-0,12")
dim(Z_R1, Z_H, 14.5, "KS-20: 11,10 (+-0,4 pela tabela do desenho)")
dim(Z_H, Z_F, 14.5, "espuma 2,0 livre, 1,0 comprimida")
dim(Z_F, Z_D, 14.5, "deck 3,0")
dim(Z_R1 + 5.0, Z_R1 + 8.4, -14.5, "5,00 +-0,05: face onde a placa de aco assentaria\n(aponta para baixo, nao serve)", side=-1)
dim(Z_R1 + 8.4, Z_H, -14.5, "cobertura afunilada 2,70 +-0,1", side=-1)
dim(Z_R1, Z_R1 + 5.0, -14.5, "corpo de baixo 14,00 +-0,05", side=-1)
ax.text(0, Z_D + 1.3, "furo do deck Ø8,0 (tubo Ø5,6 do botao)", ha="center", fontsize=9)
ax.text(0, Z_R0 - 3.2, "bolso da regua: sensores (1,1), registrador (1,2), conector;\npontas dos pinos da tecla (~2) pendem no bolso", ha="center", fontsize=8)
ax.text(0, -3.4, "bandeja (piso 2,0)", ha="center", fontsize=8)
ax.text(0, Z_H + 7.0, "botao (cabeça no ZR+22,9; curso 4,10)", ha="center", fontsize=9)
ax.set_xlim(-34, 34)
ax.set_ylim(-5, Z_D + 4)
ax.set_title("KS-20 na pilha T3 (R2V4/F2), corte pela largura da fileira 1; z = 0 no topo da bandeja (plano de encaixe tampa x base)", fontsize=10)
ax.axis("off")
fig.tight_layout()
fig.savefig(OUT, dpi=140)
print(OUT)
