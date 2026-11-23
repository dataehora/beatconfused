"""eTutti Student V4 (R4V4): the official plan of the whole instrument seen from above, with the model's real positions.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/planta_v4.py

Writes case/renders/planta_geral_v4.png (whole instrument), planta_interface_v4.png (the interface, zoomed) and
ruler_conector_v4.png (the ruler's connector zone). All positions come from layout_r4.py (the same module case_r4.py builds from).
"""
import math
import os
import sys

import matplotlib
import matplotlib.transforms
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                          # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402

REN = os.path.join(HERE, "renders")
os.makedirs(REN, exist_ok=True)
G = L.G

C = {"case": "#444441", "lid": "#D3D1C7", "board": "#EAF3DE", "board_ec": "#3B6D11", "usb": "#378ADD", "mm": "#7F77DD", "energy": "#D85A30",
     "audio": "#1D9E75", "ui": "#BA7517", "row": "#D4537E", "ruler": "#9FE1CB", "ruler_ec": "#0F6E56", "batt": "#C2410C", "spk": "#0E7490",
     "oled": "#1D4ED8", "post": "#7C2D12", "cable": "#BE185D", "notch": "#B91C1C"}
BLOCKS = {"J201": "usb", "U201": "usb", "D201": "usb", "J101": "mm", "TP101": "mm", "U202": "energy", "U204": "energy", "L201": "energy",
          "Q203": "energy", "D202": "energy", "D203": "energy", "D205": "energy", "J202": "energy", "D206": "energy", "U301": "audio",
          "U302": "audio", "J301": "audio", "J302": "audio", "U501": "audio", "J501": "audio", "FB301": "audio", "SW401": "ui",
          "SW402": "ui", "SW403": "ui", "J401": "ui", "J601": "row", "J602": "row", "J603": "row", "J604": "row"}
LABELS = {"J201": "USB-C", "J301": "OUT", "J302": "IN", "J202": "bat. JST", "J401": "tela", "J101": "M.2", "U501": "amp.", "J601": "J601", "J602": "J602",
          "J603": "J603", "J604": "J604", "SW403": "PROG", "U301": "codec", "U202": "carreg.", "U204": "conv."}


def rrect(ax, x0, y0, x1, y1, r, **kw):
    ax.add_patch(FancyBboxPatch((x0 + r, y0 + r), x1 - x0 - 2 * r, y1 - y0 - 2 * r, boxstyle="round,pad=%g,rounding_size=%g" % (r, r), **kw))


def key_cap(ax, x, y, name, fs=7.0, z=5):
    """A key cap seen from above, C-griff colours (project rule): naturals white, sharps black, C and F with a diagonal checkerboard.
    The note's name is written on every cap (R5V4 rule)."""
    sharp = "#" in name
    cf = name[0] in "CF" and not sharp
    cap = Circle((x, y), 7.5, fc="#1b1b1b" if sharp else "white", ec="#2C2C2A", lw=0.8, zorder=z)
    ax.add_patch(cap)
    if cf:
        step = 3.0
        for i in range(-3, 3):
            for j in range(-3, 3):
                if (i + j) % 2 == 0:
                    sq = Rectangle((x + i * step, y + j * step), step, step, fc="#2C2C2A", ec="none", zorder=z + 0.1,
                                   transform=matplotlib.transforms.Affine2D().rotate_deg_around(x, y, 45) + ax.transData)
                    ax.add_patch(sq)
                    sq.set_clip_path(cap)
    ax.text(x, y, name, ha="center", va="center", fontsize=fs, color="white" if sharp else "black",
            fontweight="bold" if cf else "normal", zorder=20,
            bbox=dict(boxstyle="round,pad=0.12", fc="#1b1b1b" if sharp else "white", ec="none", alpha=0.85))


def draw(ax, xlim, mod=0, detail=True, sockets=True):
    Lx = L.length(mod)
    # case: outer, lid wall (2 mm), roof
    rrect(ax, 0, L.Y_BACK, Lx, L.Y_FRONT, L.CASE_R, fc="#F1EFE8", ec=C["case"], lw=1.6, zorder=1)
    rrect(ax, 2, L.Y_BACK + 2, Lx - 2, L.Y_FRONT - 2, L.CASE_R - 2, fc="none", ec=C["case"], lw=0.8, ls="-", zorder=2)
    # board
    x0, y0, x1, y1 = L.BOARD_OUT
    rrect(ax, x0, y0, x1, y1, L.BOARD_R, fc=C["board"], ec=C["board_ec"], lw=1.2, zorder=3)
    for ref, p in L.P.items():
        if ref.startswith(("H", "TP")) or ref in ("J501",):
            continue
        a, b, c, d = p["patio"]
        col = C[BLOCKS.get(ref, "audio")] if ref in BLOCKS else "#8a8a85"
        ax.add_patch(Rectangle((a, b), c - a, d - b, fc=col, ec=col, alpha=0.55 if p["lado"] == "B" else 0.85, lw=0.5, zorder=4))
        if detail and ref in LABELS:
            ax.text((a + c) / 2, (b + d) / 2, LABELS[ref], ha="center", va="center", fontsize=5.6, zorder=12)
    # module card (under the board) and its screw
    cx0, cy0, cx1, cy1 = L.CARD
    ax.add_patch(Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fc="#CECBF6", ec="#534AB7", lw=0.9, alpha=0.5, ls="--", zorder=5))
    ax.text((cx0 + cx1) / 2 + 3, cy0 + 2.0, "MicroMod (sob a placa)", ha="center", fontsize=5.6, color="#3C3489", zorder=12)
    # battery under the board
    bx, by = L.BATTERY_XY
    bw, bl, _t = L.BATTERY_CELL
    ax.add_patch(Rectangle((bx, by), bw, bl, fc="none", ec=C["batt"], lw=1.2, ls="--", zorder=6))
    ax.text(bx + bw / 2 + 6, by + bl + 2.8, "bateria 503450, 34 x 50 x 5 (sob a placa)", ha="center", va="center", fontsize=5.6, color=C["batt"], zorder=12)
    ax.annotate("", xy=(58.0, 31.0), xytext=(bx + bw / 2, by), arrowprops=dict(arrowstyle="-", color=C["batt"], lw=1.0, ls=":",
                connectionstyle="angle,angleA=0,angleB=90,rad=4"), zorder=6)
    # speaker, box, ears
    sx, sy = L.SPEAKER
    ax.add_patch(Circle((sx, sy), L.SPK_D / 2, fc="#CFFAFE", ec=C["spk"], lw=1.0, alpha=0.7, zorder=7))
    ax.text(sx, sy, "Dayton\nCE28MB-8\nØ28 x 4,5", ha="center", va="center", fontsize=6, color=C["spk"], zorder=12)
    a, b, c, d = G.BOX_RECT
    ax.add_patch(Rectangle((a, b), c - a, d - b, fc="none", ec=C["spk"], lw=1.0, ls="-", zorder=7))
    ax.add_patch(Rectangle((G.BOX_LEG_X0, b), c - G.BOX_LEG_X0, d - b, fc="none", ec=C["spk"], lw=0, hatch="////", alpha=0.35, zorder=7))
    for ex, ey in G.SPEAKER_SCREWS:
        ax.add_patch(Circle((ex, ey), 2.5, fc="white", ec=C["spk"], lw=0.7, zorder=8))
    ax.text((a + 5), d - 1.2, "caixa acústica (L)", fontsize=5.6, color=C["spk"], zorder=12)
    # OLED (R11V4: the real module, Adafruit 326), window, slit
    import oled_r11 as OL
    wx0, wy0, wx1, wy1 = G.OLED_WINDOW
    ax.add_patch(Polygon([OL.world(x, y) for x, y in OL.outline_b()], closed=True, fc="#DBEAFE", ec=C["oled"], lw=0.9, ls="--", alpha=0.55, zorder=7))
    gx0, gy0 = OL.world(OL.GLASS_X[0], OL.GLASS_Y[0])
    gx1, gy1 = OL.world(OL.GLASS_X[1], OL.GLASS_Y[1])
    ax.add_patch(Rectangle((gx0, gy0), gx1 - gx0, gy1 - gy0, fc="#BFDBFE", ec=C["oled"], lw=0.8, alpha=0.7, zorder=7))
    ax0, ay0 = OL.world(OL.ACT_X[0], OL.ACT_Y[0])
    ax1, ay1 = OL.world(OL.ACT_X[1], OL.ACT_Y[1])
    ax.add_patch(Rectangle((ax0, ay0), ax1 - ax0, ay1 - ay0, fc="#1E3A8A", ec="none", alpha=0.85, zorder=8))
    ax.add_patch(Rectangle((wx0, wy0), wx1 - wx0, wy1 - wy0, fc="none", ec="#B91C1C", lw=1.2, zorder=9))
    ax.text((wx0 + wx1) / 2, (wy0 + wy1) / 2, "área ativa 21,74 x 10,86", ha="center", va="center", fontsize=5.4, color="white", zorder=12)
    ax.text((wx0 + wx1) / 2, wy0 - 0.8, "janela 24 x 13", ha="center", va="bottom", fontsize=5.4, color="#B91C1C", zorder=12)
    for hx, hy in OL.holes_world():
        ax.add_patch(Circle((hx, hy), OL.POST_D / 2, fc="#FED7AA", ec=C["post"], lw=0.8, zorder=10))
        ax.add_patch(Circle((hx, hy), OL.HOLE_D / 2, fc="white", ec=C["post"], lw=0.5, zorder=11))
    for nm, xb0, xb1, yb0, yb1, _d0, _d1 in OL.conn_boxes_b():
        if nm == "plugue left":
            continue                                    # only the right-hand connector is cabled
        (x0_, y0_), (x1_, y1_) = OL.world(xb0, yb0), OL.world(xb1, yb1)
        ax.add_patch(Rectangle((min(x0_, x1_), min(y0_, y1_)), abs(x1_ - x0_), abs(y1_ - y0_), fc="#FDE047" if nm.startswith("corpo") else "#FB7185", ec="black", lw=0.5, alpha=0.8, zorder=11))
    pxe, pye, _pz = OL.plug_exit_world()
    ax.annotate("cabo de 4 fios\nao J401 (fenda)", xy=(pxe, pye), xytext=(pxe + 3.0, pye - 7.5), fontsize=5.2, zorder=12, arrowprops=dict(arrowstyle="->", lw=0.5))
    ax.text(37.0, OL.WY0 - 0.6, "OLED Adafruit 326 (29,2 x 31,75; furos Ø2,5 a 24,13 x 26,67)", ha="center", va="bottom", fontsize=5.2, color=C["oled"], zorder=12)
    sx0, sy0, sx1, sy1 = L.SLIT
    ax.add_patch(Rectangle((sx0, sy0), sx1 - sx0, sy1 - sy0, fc="white", ec="black", lw=0.8, hatch="////", zorder=9))
    ax.text(sx0, sy1 + 1.0, "fenda do cabo (mantida)", fontsize=4.6, zorder=12, ha="left", va="bottom")
    # knobs, encoders, PROG
    for kx, ky in L.KNOBS:
        ax.add_patch(Rectangle((kx - 6.0, ky - 6.7), 12.0, 13.4, fc="#FDE68A", ec=C["ui"], lw=0.8, alpha=0.6, zorder=7))
        ax.add_patch(Circle((kx, ky), 6.0, fc="#FEF3C7", ec="#92400E", lw=1.2, zorder=8))
        ax.add_patch(Circle((kx, ky), 4.6, fc="none", ec="#92400E", lw=0.5, zorder=8))
    ax.text(L.KNOBS[0][0], L.KNOBS[0][1] + 8.6, "volume", ha="center", fontsize=5.8, zorder=12)
    ax.text(L.KNOBS[1][0], L.KNOBS[1][1] + 8.6, "registro", ha="center", fontsize=5.8, zorder=12)
    ax.add_patch(Circle(L.PROG, 1.5, fc="white", ec="black", lw=0.8, zorder=9))
    ax.text(L.PROG[0] + 2.3, L.PROG[1] + 0.2, "PROG (por baixo)", fontsize=5.2, zorder=12, va="center")
    # sockets in the left wall
    for yc, w, nm in ((L.USB_Y, 12.8, "USB-C y %g" % L.USB_Y), (L.OUT_Y, 6.5, "OUT y %g" % L.OUT_Y), (L.IN_Y, 6.5, "IN y %g" % L.IN_Y)):
        ax.add_patch(Rectangle((-0.1, yc - w / 2), 2.2, w, fc="white", ec="black", lw=1.0, zorder=13))
        if sockets:
            ax.annotate(nm, xy=(0, yc), xytext=(-10 if xlim[0] > -12 else -22, yc), fontsize=6, va="center", ha="left",
                        arrowprops=dict(arrowstyle="->", lw=0.7), annotation_clip=False, zorder=14)
    # lid posts on H1..H4 + H101
    for k in ("H1", "H2", "H3", "H4"):
        hx, hy = L.HOLES[k]
        ax.add_patch(Circle((hx, hy), 2.7, fc="#FED7AA", ec=C["post"], lw=1.0, zorder=10))
        ax.add_patch(Circle((hx, hy), 1.2, fc="white", ec=C["post"], lw=0.6, zorder=11))
        ax.text(hx + 3.2, hy, k, fontsize=5.6, va="center", color=C["post"], zorder=12)
    hx, hy = L.H101
    ax.add_patch(Circle((hx, hy), 1.35, fc="white", ec="black", lw=0.8, zorder=11))
    ax.text(hx + 1.9, hy, "H101", fontsize=5.2, va="center", zorder=12)
    # keyboard
    rs = L.rulers(mod)
    for ru in rs:                                    # R10V4: the closed front (riser) and the end walls of the robust base
        xa, xb, y = ru["x0"] + 0.2, ru["x0"] + L.RULER_L - 0.2, ru["y"]
        ynext = L.ROWS[ru["row"] - 2][1] - L.RAIL_OUT if ru["row"] > 1 else y + L.RAIL_OUT + 2.0
        ax.add_patch(Rectangle((xa, y + L.RAIL_OUT), xb - xa, ynext - y - L.RAIL_OUT, fc="#E7E5E4", ec="#A8A29E", lw=0.4, zorder=2))
        for ex in (xa, xb - 2.0):
            ax.add_patch(Rectangle((ex, y - L.RAIL_OUT), 2.0, 2 * L.RAIL_OUT, fc="#E7E5E4", ec="#A8A29E", lw=0.4, zorder=2))
    posts = L.pick_posts(mod)
    for ru in rs:
        xa, y = ru["x0"], ru["y"]
        ax.add_patch(Rectangle((xa + 0.2, y - 7), L.RULER_L - 0.4, 14, fc=C["ruler"], ec=C["ruler_ec"], lw=0.7, alpha=0.9, zorder=3))
        for dx in [x - xa for x, _y in L.m2_points(ru)]:
            ax.add_patch(Circle((xa + dx, y + 5.2), 1.9, fc="#D1D5DB", ec="black", lw=0.6, zorder=6))
            ax.plot([xa + dx - 1.0, xa + dx + 1.0], [y + 5.2, y + 5.2], color="black", lw=0.5, zorder=7)
    first = {r: x0 for r, _y, x0, _n in L.ROWS}
    for r, x, y in L.key_list(mod):
        ax.add_patch(Rectangle((x - 7, y - 7), 14, 14, fc="none", ec="#6B7280", lw=0.5, ls=":", zorder=4))
        idx = int(round((x - first[r]) / L.PITCH))
        key_cap(ax, x, y, L.note_name(r, idx), fs=7.0 if detail else 7.0)
    for ru in rs:
        ax.text(ru["x0"] - 1.0, ru["y"], "", fontsize=6)
    for r, y, x0, n in L.ROWS:
        xe = max(q["x0"] for q in rs if q["row"] == r) + L.RULER_L
        n = n + 4 * mod
        ax.text(xe + 1.6, y, "fileira %d\n%s-%s" % (r, L.note_name(r, 0), L.note_name(r, n - 1)), fontsize=6.3, va="center", ha="left", zorder=12)
    for px, py in posts:
        ax.add_patch(Circle((px, py), 2.5, fc="#FED7AA", ec=C["post"], lw=0.8, zorder=8))
    for px, py in L.wall_posts(mod):
        ax.add_patch(Circle((px, py), 3.0, fc="#FED7AA", ec=C["post"], lw=0.8, zorder=8))
    # connectors, notches, cables
    for nt in L.notches(mod):
        ax.add_patch(Rectangle((nt["x0"], nt["y0"]), nt["x1"] - nt["x0"], nt["y1"] - nt["y0"], fc="none", ec=C["notch"], lw=0.5, hatch="xxxx", alpha=0.7, zorder=6))
    for ru in rs:
        for name, xa, xb, ya, yb, za, zb in L.conn_boxes(ru):
            hdr = name.endswith("header")
            ax.add_patch(Rectangle((xa, ya), xb - xa, yb - ya, fc="#FDE047" if hdr else "#FB7185", ec="black", lw=0.5, alpha=0.5, zorder=9 if hdr else 8))
    for F_, ls_, lw_, col in ((L.CABLE_FREE_MM[1], (0, (4, 2)), 1.0, "#7C3AED"), (L.CABLE_FREE_MM[0], "-", 1.5, C["cable"])):
        for c in L.cables(mod, F_):
            ax.plot([p[0] for p in c["pts"]], [p[1] for p in c["pts"]], color=col, lw=lw_, ls=ls_, zorder=10)
    for t in ax.texts:
        t.set_clip_on(True)
    ax.set_xlim(*xlim)
    ax.set_ylim(L.Y_FRONT + 3, L.Y_BACK - 3)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), o jogador está embaixo (y = 100)")


def legend(ax):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h = [Patch(fc=C["board"], ec=C["board_ec"], label="placa principal 75,05 x 95,1"), Patch(fc="#CECBF6", ec="#534AB7", label="módulo (sob a placa)"),
         Patch(fc="none", ec=C["batt"], ls="--", label="bateria (sob a placa)"), Patch(fc="#CFFAFE", ec=C["spk"], label="alto-falante / caixa (sobre a placa)"),
         Patch(fc="#BFDBFE", ec=C["oled"], label="OLED Adafruit 326: placa, vidro, área ativa; janela vermelha"), Patch(fc="#FDE68A", ec=C["ui"], label="encoders e knobs"),
         Patch(fc="#FED7AA", ec=C["post"], label="postes da tampa (H1..H4, internos, de parede)"), Patch(fc=C["ruler"], ec=C["ruler_ec"], label="réguas R8 (8 teclas, 148 mm), uma por fileira"),
         Patch(fc="#D1D5DB", ec="black", label="parafusos M2 passantes com porca embaixo (2 por régua, 8 ao todo)"), Patch(fc="#FDE047", ec="black", label="cabeçalho SH IN da régua (u 5,9); a R8 não tem OUT"),
         Patch(fc="#FB7185", ec="black", label="plugue SH (3,6 x 7,0 x 2,45)"), Line2D([0], [0], color=C["cable"], lw=1.5, label="cabo SH da placa, 45,8 mm de fio útil (placa -> régua da fileira)"), Line2D([0], [0], color="#7C3AED", lw=1.0, ls="--", label="o mesmo com 50,8 mm de fio útil"),
         Patch(fc="none", ec=C["notch"], hatch="xxxx", label="rebaixo / entalhe nos trilhos da bandeja (piso intacto)"),
         Line2D([0], [0], color=C["case"], lw=0.8, label="parede 2 mm (case de 244 x 102 mm; parede de trás em y = -2)")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=6.4, frameon=False)


def main(mod=0):
    Lx = L.length(mod)
    fig, ax = plt.subplots(figsize=(17.5, 8.2))
    draw(ax, (-26, Lx + 12), mod)
    ax.set_title("eTutti Student V4 (R11V4, 4 x R8 sem OUT) - planta geral oficial, %d teclas, vista de cima: nome da nota em cada tecla; naturais brancas, sustenidos pretos, "
                 "C e F em xadrez diagonal" % (32 + 16 * mod), fontsize=9.5)
    ax.annotate("", xy=(0, L.Y_BACK - 1.0), xytext=(Lx, L.Y_BACK - 1.0), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text(Lx / 2, L.Y_BACK - 1.6, "%g mm" % Lx, ha="center", fontsize=7)
    ax.annotate("", xy=(Lx + 3.0, L.Y_BACK), xytext=(Lx + 3.0, L.Y_FRONT), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text(Lx + 4.2, (L.Y_BACK + L.Y_FRONT) / 2, "%g mm" % L.CASE[1], rotation=90, va="center", fontsize=7)
    xr = max(q["x0"] for q in L.rulers(mod)) + L.RULER_L
    ax.annotate("", xy=(xr - 0.2, 100.8), xytext=(Lx, 100.8), arrowprops=dict(arrowstyle="<->", lw=0.6, color="#B91C1C"))
    ax.text(xr - 1, 102.6, "folga %.1f" % (Lx - L.WALL - xr + 0.2), fontsize=5.8, color="#B91C1C", ha="right")
    legend(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "planta_geral_v4_r11.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13.5, 9.5))
    draw(ax, (-22, 135))
    ax.set_title("Interface e começo do teclado (R11V4), zoom da planta geral, com os nomes das notas", fontsize=10)
    legend(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "planta_interface_v4_r11.png"), dpi=140)
    plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
