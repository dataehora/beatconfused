"""R15V4: the base's underside seen from below: the 8 adhesive feet, the Ø3 hole for the PROG button (SW403), the 15 screw heads / 8 nut pockets, the H101 recess; plus a section through the
PROG hole (floor, hole, SW403 under the board, toothpick).  -> renders/base_fundo_prog_r15.png (and renders/prog_r15.png: only the PROG detail, for the page)"""
import json, math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Polygon
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("ETUTTI_CRADLE", "1")
import layout_r4 as L
pes = json.load(open(os.path.join(HERE, "out", "pes_r15.json")))["pos_xy"]

def underside(ax, zoom=None):
    Lx = L.length(0)
    ax.add_patch(FancyBboxPatch((2.15, 0.15), Lx - 4.3, 97.7, boxstyle="round,pad=0,rounding_size=4", fc="#f5f0e6", ec="k", lw=1.2))
    for x, y in L.LID_POSTS: ax.add_patch(Circle((x, y), 2.2, fc="white", ec="#374151")); ax.add_patch(Circle((x, y), 1.2, fc="white", ec="#374151"))
    for x, y in L.pick_posts(0) + L.wall_posts(0): ax.add_patch(Circle((x, y), 2.1, fc="white", ec="#7c2d12"))
    for ru in L.rulers(0):
        for mx, my in L.m2_points(ru):
            r = 2.43
            ax.add_patch(Polygon([(mx + r * math.cos(math.radians(60 * i)), my + r * math.sin(math.radians(60 * i))) for i in range(6)], fc="white", ec="#15803d", lw=1.0))
    ax.add_patch(Circle(L.H101, 4.0, fc="white", ec="#374151", ls="--"))
    ax.add_patch(Circle(L.PROG, 1.5, fc="#fecaca", ec="#b91c1c", lw=2))
    for i, (x, y) in enumerate(pes, start=1):
        ax.add_patch(Circle((x, y), 7.94 / 2, fc="#9ca3af", ec="k"))
        ax.text(x, y, str(i), ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax.set_xlim(0, Lx); ax.set_ylim(-1, 99); ax.set_aspect("equal")
    ax.invert_yaxis()                                  # seen from below with the left edge at the left: the player's side (y = 100) is at the bottom of the picture

def main():
    fig = plt.figure(figsize=(22, 13))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], hspace=0.25)
    a = fig.add_subplot(gs[0, :]); underside(a)
    a.annotate("furo Ø3 do botão PROG\n(x 52,0; y 36,0)", xy=L.PROG, xytext=(L.PROG[0] + 12, L.PROG[1] - 22), arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.5), color="#b91c1c", fontsize=12, fontweight="bold")
    a.set_title("Planta da base (transparente: mostra o que há na face de baixo; esquerda do instrumento à esquerda, a frente, onde o jogador senta, embaixo): 8 pés 3M SJ5302 Ø7,94 (cinza, numerados), furo PROG Ø3 (vermelho), "
                "bolsos sextavados das 8 porcas (verde), rebaixos dos parafusos da tampa (marrom) e das bossas H1..H4, rebaixo do H101 (tracejado)", fontsize=10)
    b = fig.add_subplot(gs[1, 0]); b.set_aspect("equal")
    zb, zf, zbd = -10.1, -8.1, -1.2
    b.add_patch(Rectangle((40, zb), 24, 2.0, fc="#f5f0e6", ec="k"))                       # floor
    b.add_patch(Rectangle((50.5, zb), 3.0, 2.0, fc="white", ec="#b91c1c", lw=2))           # hole D3
    b.add_patch(Rectangle((40, zbd), 24, 1.2, fc="#065f46", ec="k"))                # main board 1.2 (z -1.2 .. 0)
    b.add_patch(Rectangle((48.2, -4.7), 7.6, 3.5, fc="#6b7280", ec="k"))                   # SW403 body (courtyard 7.6 wide, 3.5 high)
    b.add_patch(Rectangle((51.2, -5.4), 1.6, 0.7, fc="#374151", ec="k"))                   # the button's actuator
    b.add_patch(Rectangle((51.0, -13.0), 2.0, 7.6, fc="#d97706", ec="k", alpha=0.8, zorder=5))   # toothpick, tip against the actuator
    b.annotate("", xy=(52.0, -5.5), xytext=(52.0, -11.8), arrowprops=dict(arrowstyle="->", color="#b91c1c"))
    b.text(54.5, -12.0, "palito (Ø2): passa o furo Ø3 e\nchega ao atuador, 3,4 mm acima do piso", fontsize=10, color="#b91c1c")
    b.text(40.5, -9.4, "piso 2,0", fontsize=10); b.text(40.5, -3.0, "", fontsize=10); b.text(40.5, 0.9, "placa principal 1,2 (SW403 no lado de baixo, 3,5 de altura)", fontsize=10)
    b.set_xlim(40, 64); b.set_ylim(-14, 2)
    b.set_title("Corte pelo furo PROG (y 36,0): a ponta do palito chega ao SW403 por baixo", fontsize=11)
    c = fig.add_subplot(gs[1, 1]); underside(c)
    c.set_xlim(30, 75); c.set_ylim(55, 15)
    c.set_title("Detalhe: o furo PROG, longe dos pés (distância mínima a um pé: %.0f mm)" % min(math.hypot(L.PROG[0] - x, L.PROG[1] - y) for x, y in pes), fontsize=11)
    fp = os.path.join(HERE, "renders", "base_fundo_prog_r15.png")
    fig.savefig(fp, dpi=100, bbox_inches="tight"); print(fp)
    fig2, (ax2, ax3) = plt.subplots(1, 2, figsize=(16, 7)); 
    plt.close(fig2)
main()
