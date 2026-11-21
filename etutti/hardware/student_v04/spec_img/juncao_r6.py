"""R6V4 (Chat): sketch of the joint between two rulers of row 2 (E4 | G4) with the two board-to-board connector ideas.

    python etutti/hardware/student_v04/spec_img/juncao_r6.py   -> spec_img/juncao_r6.png

Ruler numbers come from FIT_CHECK.md (74.0 x 14.0, 0.4 gap, pocket |y| < 4.2, rails 4.2..7.0, key pegs D1.7 at +-5.08 on y = 0,
sensor pocket +-1.1, pocket 6.9 mm under row 1). Connector sizes are ESTIMATES from catalogue descriptions (1.27 mm pitch,
female 3.4 mm tall), to be replaced by the Code with real drawings.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
L, GAP = 74.0, 0.4
B0 = L + GAP
KEYS_A = [(46.25, "C#4"), (64.75, "E4")]
KEYS_B = [(B0 + 9.25, "G4"), (B0 + 27.75, "A#4")]
X0, X1 = 52, 96


def base_plan(ax, title):
    for x0 in (0, B0):
        ax.add_patch(Rectangle((x0, -7), L, 14, fc="#e8f0e0", ec="#4a6a3a", lw=1.2))
    for ys in (4.2, -7.0):
        ax.add_patch(Rectangle((X0, ys), X1 - X0, 2.8, fc="#d9d2c5", ec="none", alpha=0.6, zorder=0))
    ax.text(X0 + 0.5, 5.6, "trilho (sob a régua)", fontsize=7, color="#7a6a50")
    ax.text(X0 + 0.5, -6.3, "trilho (sob a régua)", fontsize=7, color="#7a6a50")
    for cx, name in KEYS_A + KEYS_B:
        ax.add_patch(Rectangle((cx - 7, -7), 14, 14, fc="none", ec="#999", ls="--", lw=0.8))
        for px in (cx - 5.08, cx + 5.08):
            ax.add_patch(Circle((px, 0), 0.85, fc="#555", ec="none", zorder=5))
        ax.add_patch(Rectangle((cx - 1.1, -1.1), 2.2, 2.2, fc="#b03030", ec="none", zorder=5))
        white = "#" not in name
        ax.text(cx, 9.0, name, ha="center", va="center", fontsize=9, fontweight="bold",
                color="black" if white else "white",
                bbox=dict(boxstyle="round,pad=0.25", fc="white" if white else "black", ec="black"), clip_on=True)
    ax.axvspan(L - 3.3, B0 + 3.3, color="#ffe9a8", alpha=0.35, zorder=0)
    ax.text((L + B0) / 2, -9.6, "faixa livre no eixo:\n6,6 mm entre pinos", ha="center", fontsize=7, color="#8a6a00")
    ax.text(30 + X0 / 2, 0, "", fontsize=7)
    ax.set_xlim(X0, X1); ax.set_ylim(-11.5, 11); ax.set_aspect("equal")
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(X0 + 0.6, -0.6, "régua A", fontsize=8, color="#4a6a3a")
    ax.text(X1 - 6.5, -0.6, "régua B", fontsize=8, color="#4a6a3a")


fig, axs = plt.subplots(3, 1, figsize=(10, 11.5), gridspec_kw={"height_ratios": [1, 1, 0.75]})

# E1: J's idea taken literally: right-angle male (A, right end) into right-angle female (B, left end), pins along x
ax = axs[0]
base_plan(ax, "E1 — macho em ângulo (fim de A) entrando na fêmea em ângulo (início de B), vista de baixo, passo 1,27")
ax.add_patch(Rectangle((70.9, -3.4), 1.4, 6.8, fc="#c9a0dc", ec="#6a3a8a", lw=0.8))      # male pads
ax.add_patch(Rectangle((72.3, -3.4), 1.7, 6.8, fc="#8a5aaa", ec="#6a3a8a", lw=0.8))      # male body
for i in range(5):
    y = -2.54 + i * 1.27
    ax.plot([74.0, 76.9], [y, y], color="#b8860b", lw=1.6)
ax.add_patch(Rectangle((B0, -3.4), 4.2, 6.8, fc="#5a8acb", ec="#2a4a7a", lw=0.8, alpha=0.9))  # female body (est.)
ax.add_patch(Rectangle((B0 + 4.2, -3.4), 1.4, 6.8, fc="#a8c4ea", ec="#2a4a7a", lw=0.8))     # female pads
ax.add_patch(Circle((B0 + 4.17, 0), 1.6, fc="none", ec="red", lw=2, zorder=6))
ax.annotate("bate no pino da 1ª tecla de B\n(fêmea + pads ~5,6 mm; livre 3,3)", xy=(B0 + 4.6, 1.3), xytext=(84, 5.5),
            fontsize=8, color="red", arrowprops=dict(arrowstyle="->", color="red"))
ax.text(70.6, -5.1, "macho", fontsize=7, color="#6a3a8a"); ax.text(B0 + 0.3, -5.1, "fêmea", fontsize=7, color="#2a4a7a")

# E2: identical female sockets at both ends, rows along x in the front lane, a bridge plugs from below
ax = axs[1]
base_plan(ax, "E2 — fêmea igual nas duas pontas + ponte macho-macho por baixo, fileira ao longo de x (faixa da frente)")
ax.add_patch(Rectangle((66.0, 0.95), 16.4, 3.15, fc="#f0c070", ec="#a07020", lw=1.0, alpha=0.55, zorder=3))
for x0 in (66.6, B0 + 0.5):
    ax.add_patch(Rectangle((x0, 1.25), 6.9, 2.55, fc="#5a8acb", ec="#2a4a7a", lw=0.8, zorder=4))
    for i in range(5):
        ax.add_patch(Circle((x0 + 0.9 + i * 1.27, 2.52), 0.3, fc="#b8860b", ec="none", zorder=5))
ax.text(66.2, 4.55, "ponte (PCB 16 x 3,2, dois machos 1x5)", fontsize=7, color="#a07020")
ax.text(60, -3.2, "nada muda no eixo:\npinos e sensores livres", fontsize=7, color="#333")

# E2 cross-section along x at y = +2.5
ax = axs[2]
ax.set_title("E2 em corte (x–z na faixa da frente, fileira 1: bolsa de 6,9 mm)", fontsize=10, loc="left")
for x0 in (0, B0):
    ax.add_patch(Rectangle((x0, -1.2), L, 1.2, fc="#e8f0e0", ec="#4a6a3a"))
ax.add_patch(Rectangle((X0, -8.1 - 2.0), X1 - X0, 2.0, fc="#d9d2c5", ec="#7a6a50"))
ax.text(X0 + 0.5, -9.5, "piso da bandeja", fontsize=7, color="#7a6a50")
for x0 in (66.6, B0 + 0.5):
    ax.add_patch(Rectangle((x0, -4.6), 6.9, 3.4, fc="#5a8acb", ec="#2a4a7a"))
ax.add_patch(Rectangle((66.0, -6.4), 16.4, 0.8, fc="#f0c070", ec="#a07020"))
for x0 in (66.6, B0 + 0.5):
    ax.add_patch(Rectangle((x0, -5.6), 6.9, 1.0, fc="#333", ec="none"))
ax.annotate("", xy=(84.5, -1.2), xytext=(84.5, -6.4), arrowprops=dict(arrowstyle="<->", color="#333"))
ax.text(85, -3.9, "~5,2 mm (estimativa)\nfolga ~1,7 até o piso", fontsize=7)
for cx, name in KEYS_A + KEYS_B:
    ax.add_patch(Rectangle((cx - 7, 0), 14, 3.4, fc="none", ec="#999", ls="--", lw=0.8))
    white = "#" not in name
    ax.text(cx, 1.7, name, ha="center", va="center", fontsize=8, fontweight="bold", color="black" if white else "white",
            bbox=dict(boxstyle="round,pad=0.2", fc="white" if white else "black", ec="black"), clip_on=True)
ax.text(X0 + 0.5, 2.6, "teclas (corpo de baixo)", fontsize=7, color="#777")
ax.set_xlim(X0, X1); ax.set_ylim(-10.5, 4.5); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

fig.suptitle("Junção de duas réguas da fileira 2 (E4 | G4) — conectores fixos: esboço do Chat, medidas a confirmar", fontsize=11)
fig.tight_layout()
out = os.path.join(HERE, "juncao_r6.png")
fig.savefig(out, dpi=130)
print(out)
