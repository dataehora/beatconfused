"""eTutti Student V4 (R5V4 item 3, design part): the ruler-to-ruler link and the board-to-ruler cable, options A..D, drawn on the real model.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/ligacao_v5.py [modules]

Writes case/renders/ligacao_elo_v5.png (plan + section at the junction of row 2's two rulers, for A, B, C, D), ligacao_placa_v5.png (the four
board -> first-ruler cables, with the 0..7 mm step) and case/out/ligacao_v5.json (interference volumes of every option's envelope with the tray,
the pegs, the sensors and the rulers, at EVERY junction of the instrument).

Dimensions of the electronics' parts are ENVELOPES taken from the SPEC, the model's SH header and typical catalogue values; each one is marked
"a confirmar" until ELETRONICA.md gives pads, connector and heights. Change them in PARTS below.
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import Circle, Rectangle       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R        # noqa: E402
import corte_teclado_v5 as K   # noqa: E402

L = R.L
box = R.box
REN = os.path.join(HERE, "renders")
GAP = 0.4                                   # between two rulers of a row (0.2 + 0.2)
T = L.RULER_T

# ---- envelopes (a confirmar)
PARTS = {
    "A_cabo_comercial_mm": 100.0,            # shortest SH-6 plug-to-plug jumper in stock (Pololu 5543 / Pimoroni, 100 mm; ELETRONICA R5V4); 25 mm only made to order
    "A_cabo_largura": 4.0, "A_cabo_altura": 1.2,
    "B_pad_pitch": 1.0, "B_pads": 5, "B_pad_a_borda": 1.0,           # ELETRONICA R5V4: 5 pads 1.4 x 0.7, u = 2.1 / 71.9, v -0.4..3.6; 28-30 AWG, ~7 mm, ~1 mm under the ruler (envelope 1.4)
    "C_conn": (3.9, 6.7, 1.0),              # FPC/FFC connector 6 x 0.5 mm, bottom side: depth along the mating axis, width, height (estimativa)
    "C_ffc_larg": 4.0, "C_ffc_esp": 0.3,
}


def junctions(mod):
    """Every junction of a row: (row, x_j, y, ZR of the row)."""
    out = []
    rs = L.rulers(mod)
    for r, y, x0, n in L.ROWS:
        row = [q for q in rs if q["row"] == r]
        for a, b in zip(row[:-1], row[1:]):
            out.append((r, b["x0"], y, R.F.ZR[r - 1]))
    return out


class mode:
    """Temporarily switch layout_r4.LINK ("A": SH cable everywhere, with the OUT plug windows; "D": the recommended)."""
    def __init__(self, m):
        self.m = m

    def __enter__(self):
        self.old = L.LINK
        L.LINK = self.m

    def __exit__(self, *a):
        L.LINK = self.old


def env_A(xj, y, z0):
    """Headers (OUT of the left ruler, IN of the right one), plugs, and the cable's slack lying on the floor of the NEXT row's pocket."""
    with mode("A"):
        return _env_A(xj, y, z0)


def _env_A(xj, y, z0):
    zt = z0 - T
    rk = {"x0": xj - L.RULER_L, "y": y}
    rk1 = {"x0": xj, "y": y}
    parts = []
    for ru, nm in ((rk, "OUT"), (rk1, "IN")):
        for name, xa, xb, ya, yb, za, zb in L.conn_boxes(ru):
            if name.startswith(nm):
                parts.append(box(xa, xb, ya, yb, z0 + za, z0 + zb))
    # slack: the cable leaves both plugs towards the back (-y) into the next row's pocket (axis y - 16.02) and lies there
    exc = PARTS["A_cabo_comercial_mm"] - 14.0
    run = exc / 2.0
    pocket_y = y - L.ROWP
    w, h = PARTS["A_cabo_largura"], 2 * PARTS["A_cabo_altura"] + 0.4          # two layers (out and back)
    xa, xb = xj - L.RULER_L + L.OUT_X - run, xj + L.IN_X
    parts.append(box(xa, xb, pocket_y - w / 2, pocket_y + w / 2, L.Z_FLOOR, L.Z_FLOOR + h) if y > L.ROWS[3][1] + 1 else
                 box(xa, xb, y - 9.5 - w, y - 9.5, L.Z_FLOOR, L.Z_FLOOR + h))
    return parts


def env_B(xj, y, z0):
    """R5V4 contract of the electronics (ELETRONICA.md): 5 pads 1.4 x 0.7 at u = 2.1 / 71.9, v -0.4..3.6, wires ~7 mm, ~1 mm under the ruler."""
    return [box(*L.link_box(xj, y, z0))]


def env_C(xj, y, z0):
    zt = z0 - T
    d, w, h = PARTS["C_conn"]
    left = box(xj - GAP / 2 - d, xj - GAP / 2, y - w / 2, y + w / 2, zt - h, zt)
    right = box(xj + GAP / 2, xj + GAP / 2 + d, y - w / 2, y + w / 2, zt - h, zt)
    ffc = box(xj - GAP / 2 - d + 0.6, xj + GAP / 2 + d - 0.6, y - PARTS["C_ffc_larg"] / 2, y + PARTS["C_ffc_larg"] / 2,
              zt - h - PARTS["C_ffc_esp"], zt - h)
    return [left, right, ffc]


ENVS = {"A": env_A, "B": env_B, "C": env_C, "D": env_B}


def union(sols):
    u = sols[0]
    for s in sols[1:]:
        u = u.union(s)
    return u


def check(mod):
    tray, ru, cn = R.tray(mod), R.rulers_solid(mod), R.connectors(mod)
    res = {}
    sc = R.screws(mod)
    with mode("A"):
        tray_A = R.tray(mod)
    for opt, fn in ENVS.items():
        tot = {"bandeja": 0.0, "pinos": 0.0, "sensores": 0.0, "reguas": 0.0, "cabecalhos_J2": 0.0, "parafusos": 0.0}
        for r, xj, y, z0 in junctions(mod):
            e = union(fn(xj, y, z0))
            tot["bandeja"] += R.inter(e, tray_A if opt == "A" else tray)
            tot["pinos"] += R.inter(e, cn["pinos"])
            tot["sensores"] += R.inter(e, cn["sensores"])
            tot["reguas"] += R.inter(e, ru)
            tot["cabecalhos_J2"] += R.inter(e, cn["cabecalhos"])
            tot["parafusos"] += R.inter(e, sc)
        res[opt] = {k: round(v, 2) for k, v in tot.items()}
    return res


# ---------------------------------------------------------------- the figure
def plan_ax(ax, xj, y, mod, opt, xr=22.0):
    tray = None
    ax.set_xlim(xj - xr, xj + xr)
    ax.set_ylim(y + 9, y - 24)
    ax.set_aspect("equal")
    # rulers of the row and of the next row (back)
    for rr in (y, y - L.ROWP):
        for ru in L.rulers(mod):
            if abs(ru["y"] - rr) < 0.05:
                ax.add_patch(Rectangle((ru["x0"] + 0.2, rr - 7), L.RULER_L - 0.4, 14, fc="#BFEBDD", ec="#0F6E56", lw=0.7, zorder=2))
                for sgn in (-1, 1):
                    ya, yb = sorted((rr + sgn * L.RAIL_IN, rr + sgn * L.RAIL_OUT))
                    ax.add_patch(Rectangle((ru["x0"] + 0.2, ya), L.RULER_L - 0.4, yb - ya, fc="none", ec="#6B7280", lw=0.5, ls="--", hatch="////", zorder=3, alpha=0.5))
    for r2, x, yk in L.key_list(mod):
        if abs(yk - y) < 0.05 or abs(yk - (y - L.ROWP)) < 0.05:
            idx = int(round((x - [q[2] for q in L.ROWS if abs(q[1] - yk) < 0.05][0]) / L.PITCH))
            row = [q[0] for q in L.ROWS if abs(q[1] - yk) < 0.05][0]
            nm = L.note_name(row, idx)
            sharp = "#" in nm
            ax.add_patch(Circle((x, yk), 7.5, fc="#1b1b1b" if sharp else "white", ec="#2C2C2A", lw=0.6, alpha=0.35, zorder=4))
            ax.text(x, yk - 5.2, nm, fontsize=6, ha="center", zorder=5, color="#444444", clip_on=True)
            for dx in (-L.PEG_DX, L.PEG_DX):
                ax.add_patch(Circle((x + dx, yk), 0.85, fc="#111827", zorder=5))
    ax.axvline(xj, color="#B91C1C", lw=0.5, ls=":", zorder=6)
    fn = ENVS[opt]
    sol_boxes = []
    if opt == "A":
      with mode("A"):
        for nm_, xa, xb, ya, yb, za, zb in L.conn_boxes({"x0": xj - L.RULER_L, "y": y}):
            if nm_.startswith("OUT"):
                ax.add_patch(Rectangle((xa, ya), xb - xa, yb - ya, fc="#FDE047" if nm_.endswith("header") else "#FB7185", ec="k", lw=0.5, alpha=0.8, zorder=7))
        for nm_, xa, xb, ya, yb, za, zb in L.conn_boxes({"x0": xj, "y": y}):
            if nm_.startswith("IN"):
                ax.add_patch(Rectangle((xa, ya), xb - xa, yb - ya, fc="#FDE047" if nm_.endswith("header") else "#FB7185", ec="k", lw=0.5, alpha=0.8, zorder=7))
        po, pi = (xj - L.RULER_L + L.OUT_X, y + L.LANE_Y0 - L.PLUG_D), (xj + L.IN_X, y + L.LANE_Y0 - L.PLUG_D)
        exc = PARTS["A_cabo_comercial_mm"] - 14.0
        run = exc / 2.0
        py = y - L.ROWP if y > L.ROWS[3][1] + 1 else y - 11.0
        pts = [po, (po[0], py - 1.0), (po[0] - run, py - 1.0), (po[0] - run, py + 1.0), (pi[0], py + 1.0), (pi[0], pi[1])]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#BE185D", lw=1.6, zorder=8)
        ax.set_xlabel("cabo de estoque de %g mm: sobra de %.0f mm (a eletrônica descarta; só sob medida em 15/25 mm)" % (PARTS["A_cabo_comercial_mm"], exc), fontsize=7)
    elif opt in ("B", "D"):
        for k in range(5):
            yy = y + L.LK_V[0] + k * (L.LK_V[1] - L.LK_V[0]) / 4.0
            for sx in (-1, 1):
                ax.add_patch(Rectangle((xj + sx * L.LK_U[0] - L.LK_PAD[0] / 2, yy - L.LK_PAD[1] / 2), L.LK_PAD[0], L.LK_PAD[1], fc="#F59E0B", ec="k", lw=0.4, zorder=7))
            ax.plot([xj - L.LK_U[0], xj + L.LK_U[0]], [yy, yy], color="#BE185D", lw=1.0, zorder=8)
        ax.set_xlabel("5 pads 1,4 x 0,7 a 1,0 mm de cada ponta (u 2,1 e 71,9; v -0,4..3,6) e 5 fios de ~7 mm, na bolsa entre os trilhos", fontsize=7)
    elif opt == "C":
        d, w, h = PARTS["C_conn"]
        for sx in (-1, 1):
            xa = xj + sx * GAP / 2 if sx > 0 else xj - GAP / 2 - d
            ax.add_patch(Rectangle((xa, y - w / 2), d, w, fc="#FDE047", ec="k", lw=0.5, alpha=0.85, zorder=7))
        ax.add_patch(Rectangle((xj - d - GAP / 2 + 0.6, y - PARTS["C_ffc_larg"] / 2), 2 * d + GAP - 1.2, PARTS["C_ffc_larg"], fc="#BE185D", ec="k", lw=0.4, alpha=0.8, zorder=8))
        ax.set_xlabel("2 conectores FPC 6 x 0,5 mm frente a frente + jumper FFC em linha (a confirmar)", fontsize=7)
    ax.set_yticks([])


def section_ax(ax, xj, y, z0, mod, opt, tray, ru, cn):
    yy = y - 4.4 if opt == "A" else y
    parts = [("bandeja", tray, "#9CA3AF"), ("régua", ru, "#86EFAC")]
    for name, solid, col in parts:
        K.fill(ax, K.sect(solid, "y", yy), fc=col, ec="#222222", lw=0.4, alpha=0.9)
    for s in ENVS[opt](xj, y, z0):
        col = "#FDE047" if opt in ("A", "C") else "#F59E0B"
        K.fill(ax, K.sect(s, "y", yy), fc=col, ec="#7C2D12", lw=0.6, alpha=0.95)
    K.fill(ax, K.sect(cn["pinos"], "y", yy), fc="#111827", ec="k", lw=0.3)
    K.fill(ax, K.sect(cn["sensores"], "y", yy), fc="#6366F1", ec="k", lw=0.3)
    ax.set_xlim(xj - 26, xj + 26)
    ax.set_ylim(L.Z_BOT - 0.5, z0 + 4)
    ax.set_aspect("equal")
    ax.axvline(xj, color="#B91C1C", lw=0.5, ls=":")
    ax.set_xlabel("x (mm)")
    ax.set_title("corte em y = %.2f%s" % (yy, " (faixa dos cabeçalhos)" if opt == "A" else " (eixo da fileira)"), fontsize=7.5)


def figure_elo(mod=0):
    tray, ru, cn = R.tray(mod), R.rulers_solid(mod), R.connectors(mod)
    with mode("A"):
        tray_A = R.tray(mod)
    jr = [j for j in junctions(mod) if j[0] == 2][0]
    r, xj, y, z0 = jr
    fig, axs = plt.subplots(2, 4, figsize=(21, 9.5), gridspec_kw={"height_ratios": [1.5, 0.9]})
    titles = {"A": "A. cabo SH pronto nas duas pontas", "B": "B. elo soldado: 5 fios nos pads do fundo", "C": "C. FFC/FPC com 2 conectores",
              "D": "D. misto: cabo pronto só placa -> 1ª régua; elo soldado (B) nas fileiras"}
    for i, opt in enumerate("ABCD"):
        plan_ax(axs[0][i], xj, y, mod, "B" if opt == "D" else opt)
        axs[0][i].set_title(titles[opt], fontsize=8.5)
        section_ax(axs[1][i], xj, y, z0, mod, opt, tray_A if opt == "A" else tray, ru, cn)
        if opt == "D":
            axs[1][i].set_title("corte do elo (= B); os 4 cabos placa -> régua: ver ligacao_placa_v5.png", fontsize=7.5)
    axs[0][0].set_ylabel("y (mm), jogador embaixo")
    axs[1][0].set_ylabel("z (mm)")
    fig.suptitle("Ligação entre réguas (R5V4), junção das réguas 1|2 da fileira 2 (fileira 3 atrás), geometria a confirmar: réguas em linha, na mesma altura, a %.1f mm (cinza hachurado = trilhos da bandeja)" % GAP, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "ligacao_elo_v5.png"), dpi=125, bbox_inches="tight")
    plt.close(fig)


def figure_placa(mod=0):
    """The four board -> first ruler cables (25 mm plug to plug): plan chords and the 0..7 mm step, 3D chord against the 25 mm."""
    rs = L.rulers(mod)
    rows = []
    fig, axs = plt.subplots(1, 2, figsize=(17, 7.5), gridspec_kw={"width_ratios": [1.15, 1.0]})
    cols = {1: "#2563EB", 2: "#16A34A", 3: "#D97706", 4: "#B91C1C"}
    jx = float(L.POS["metricas"]["mouth_x_fileiras"]["1"])
    for c in L.cables(mod):
        if not c["de"].startswith("J60"):
            continue
        r = c["row"]
        first = [q for q in rs if q["row"] == r][0]
        z_ruler = R.F.ZR[r - 1] - T - 2.1                      # the plug axis below the ruler's top
        z_board = -L.T_PCB - 2.1                                # J60x axis under the board
        a, b = c["pts"][0], c["pts"][-1]
        plan_len = L.plen(c["pts"])
        dz = z_ruler - z_board
        chord = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + dz ** 2)
        rows.append({"fileira": r, "desnivel_mm": round(dz, 1), "corda_3d_mm": round(chord, 1), "cabo_25": 25.0, "folga_cabo_25_mm": round(25.0 - chord, 1),
                     "sobra_cabo_50_mm": round(PARTS["A_cabo_comercial_mm"] - chord, 1)})
        axs[0].plot([p[0] for p in c["pts"]], [p[1] for p in c["pts"]], color=cols[r], lw=2, label="fileira %d: desnível %.1f mm" % (r, dz))
        # side view: x against z, a straight-ish line with the step spread over the plan length
        s, zs, xs_ = 0.0, [], []
        for i, p in enumerate(c["pts"]):
            if i:
                s += math.hypot(p[0] - c["pts"][i - 1][0], p[1] - c["pts"][i - 1][1])
            xs_.append(p[0])
            zs.append(z_board + dz * (0.5 - 0.5 * math.cos(math.pi * s / plan_len)))
        axs[1].plot(xs_, zs, color=cols[r], lw=2, label="fileira %d (z de %.1f a %.1f)" % (r, z_board, z_ruler))
    for ru in rs:
        if ru["k"] == 0:
            axs[0].add_patch(Rectangle((ru["x0"] + 0.2, ru["y"] - 7), L.RULER_L - 0.4, 14, fc="#BFEBDD", ec="#0F6E56", lw=0.7))
            axs[1].add_patch(Rectangle((ru["x0"] + 0.2, R.F.ZR[ru["row"] - 1] - T), 30, T, fc="#34D399", ec="k", lw=0.4))
    for name, x0, x1, y0, y1 in (("J601..J604", jx - 4.25, 78.0, 0, 100),):
        axs[0].add_patch(Rectangle((75.0, 12), 3, 78, fc="#FBCFE8", ec="#9D174D", lw=0.6))
    axs[1].add_patch(Rectangle((60, -L.T_PCB), 18.5, L.T_PCB, fc="#86EFAC", ec="k", lw=0.4))
    axs[0].set_xlim(70, 125)
    axs[0].set_ylim(86, 5)
    axs[0].set_aspect("equal")
    axs[0].set_title("Planta: os 4 cabos placa -> 1ª régua (25 mm entre plugues; as réguas das fileiras 1 e 3 começam em x 89,2, as 2 e 4 em 79,95)", fontsize=8.5)
    axs[0].legend(fontsize=7, loc="lower right")
    axs[1].set_xlim(70, 125)
    axs[1].set_ylim(-9, 9)
    axs[1].set_title("Vista lateral (x, z): a placa (verde claro) e as réguas em quatro alturas (0, 2, 4, 7): desnível de 0 a 7 mm", fontsize=8.5)
    axs[1].set_xlabel("x (mm)")
    axs[1].set_ylabel("z (mm)")
    axs[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "ligacao_placa_v5.png"), dpi=125)
    plt.close(fig)
    return rows


def main():
    mods = [int(a) for a in sys.argv[1:]] or [0, 3]
    out = {"parametros_a_confirmar": {k: v for k, v in PARTS.items()}}
    figure_elo(0)
    out["cabos_placa"] = figure_placa(0)
    for m in mods:
        out["interferencias_mm3_modulos_%d" % m] = check(m)
    json.dump(out, open(os.path.join(HERE, "out", "ligacao_v5.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
