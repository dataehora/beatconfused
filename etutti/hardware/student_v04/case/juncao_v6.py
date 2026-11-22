"""eTutti Student V4 (R6V4 item 1, design part): ruler-to-ruler joints E1, E1c, E2, E2b, F on the real model, and the board -> first ruler study.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/juncao_v6.py

Writes case/renders/juncao_opcoes_r6.png (plan of row 2's joint E4|G4 and section of row 1's joint F#4|A4 for every option),
juncao_E2_r6.png (the recommended: plan, two sections, assembly), juncao_placa_r6.png (board -> first ruler: why a rigid plug is impossible, the cable)
and case/out/juncao_r6.json (interference volumes at EVERY junction of 32/48/64/80 keys; parts of the ruler that the joint's footprint hits).
Dimensions are ESTIMATES (juncao_r6.py) until ELETRONICA.md R6V4 brings the real parts.
"""
import json
import math
import os
import sys

import matplotlib
import matplotlib.transforms
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import Circle, Rectangle       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_r4 as R        # noqa: E402
import juncao_r6 as J      # noqa: E402

L = R.L
box = R.box
REN = os.path.join(HERE, "renders")
T = L.RULER_T
COL = {"femea": "#60A5FA", "macho": "#A78BFA", "pino": "#F59E0B", "ponte": "#F0C070", "mola": "#34D399", "bloco": "#9CA3AF", "aba": "#9CA3AF"}


def ov(a, b):
    d = [min(a[i + 1], b[i + 1]) - max(a[i], b[i]) for i in (0, 2, 4)]
    return d[0] * d[1] * d[2] if all(x > 0 for x in d) else 0.0


def union(bs):
    u = None
    for b in bs:
        s = box(*b)
        u = s if u is None else u.union(s)
    return u


def check(mod):
    R.CRADLE_OPT = None
    tray = R.tray(mod)
    R.CRADLE_OPT = "E2"
    cn = R.connectors(mod)
    sc = R.screws(mod)
    ru = R.rulers_solid(mod)
    res = {}
    for opt, o in J.OPTIONS.items():
        parts, cr = [], []
        rp = {}
        for r, xj, y, z0 in J.bridges(mod):
            parts += [J.to_box(p, xj, y, z0) for p in o["parts"] if not (opt == "E2" and p[1] == "femea")]   # E2: the sockets are the J1/J2 headers
            cr += [J.to_box_cradle(c, xj, y, z0) for c in J.cradle(opt, r)]
            for nm, bx in J.ruler_part_boxes(xj, y, z0, skip=(() if opt.startswith("E1") else ("J1", "J2", "LK1", "LK2"))):
                for p in [q for q in o["parts"] if not (opt == "E2" and q[1] == "femea")]:
                    v = ov(J.to_box(p, xj, y, z0), bx)
                    if v > 0:
                        rp[nm.split(".")[0]] = round(rp.get(nm.split(".")[0], 0) + v, 2)
        pu = union(parts)
        out = {"bandeja (sem berço)": round(R.inter(pu, tray), 2), "pinos das teclas": round(R.inter(pu, cn["pinos"]), 2),
               "sensores": round(R.inter(pu, cn["sensores"]), 2), "parafusos": round(R.inter(pu, sc), 2),
               "cabeçalhos J1": round(R.inter(pu, cn["cabecalhos"]), 2), "plugues J1": round(R.inter(pu, cn["plugues"]), 2),
               "réguas (só toca)": round(R.inter(pu, ru), 2), "peças da régua (mm3 por ref)": rp}
        if cr:
            cu = union(cr)
            out["berço x pinos/sensores/parafusos"] = round(R.inter(cu, cn["pinos"]) + R.inter(cu, cn["sensores"]) + R.inter(cu, sc), 2)
            out["berço x ponte e conectores"] = round(R.inter(cu, pu), 2)
            out["berço x plugues J1"] = round(R.inter(cu, cn["plugues"]), 2)
            out["berço: volume cm3"] = round(sum((b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4]) for b in cr) / 1000, 3)
        res[opt] = out
    return res


# ---------------------------------------------------------------- figures
def key_cap(ax, x, y, name, fs=7):
    sharp = "#" in name
    cf = name[0] in "CF" and not sharp
    cap = Circle((x, y), 7.5, fc="#1b1b1b" if sharp else "white", ec="#2C2C2A", lw=0.7, alpha=0.30, zorder=3)
    ax.add_patch(cap)
    if cf:
        for i in range(-3, 3):
            for j in range(-3, 3):
                if (i + j) % 2 == 0:
                    sq = Rectangle((x + i * 3, y + j * 3), 3, 3, fc="#2C2C2A", ec="none", alpha=0.35, zorder=3,
                                   transform=matplotlib.transforms.Affine2D().rotate_deg_around(x, y, 45) + ax.transData)
                    ax.add_patch(sq)
                    sq.set_clip_path(cap)
    ax.text(x, y - 5.6, name, ha="center", va="center", fontsize=fs, fontweight="bold" if cf else "normal", zorder=12,
            bbox=dict(boxstyle="round,pad=0.12", fc="#1b1b1b" if sharp else "white", ec="#666", lw=0.4, alpha=0.9), color="white" if sharp else "black", clip_on=True)


def plan(ax, mod, row, opt, xr=15.0):
    r, xj, y, z0 = [j for j in J.bridges(mod) if j[0] == row][0]
    ax.set_xlim(xj - xr, xj + xr)
    ax.set_ylim(y + 9, y - 10)
    ax.set_aspect("equal")
    for ru in L.rulers(mod):
        if ru["row"] == row:
            ax.add_patch(Rectangle((ru["x0"] + 0.2, y - 7), L.RULER_L - 0.4, 14, fc="#BFEBDD", ec="#0F6E56", lw=0.7, zorder=2))
            for sgn in (-1, 1):
                ya, yb = sorted((y + sgn * L.RAIL_IN, y + sgn * L.RAIL_OUT))
                ax.add_patch(Rectangle((ru["x0"] + 0.2, ya), L.RULER_L - 0.4, yb - ya, fc="none", ec="#6B7280", lw=0.5, hatch="////", alpha=0.5, zorder=3))
    for r2, x, yk in L.key_list(mod):
        if r2 == row and abs(x - xj) < xr + 8:
            idx = int(round((x - [q[2] for q in L.ROWS if q[0] == row][0]) / L.PITCH))
            key_cap(ax, x, yk, L.note_name(row, idx))
            for dx in (-L.PEG_DX, L.PEG_DX):
                ax.add_patch(Circle((x + dx, yk), 0.85, fc="#111827", zorder=8))
            ax.add_patch(Rectangle((x - 1.1, yk - 1.1), 2.2, 2.2, fc="#B03030", zorder=8))
    for nm, bx in J.ruler_part_boxes(xj, y, z0, skip=(() if opt.startswith("E1") else ("J1", "J2", "LK1", "LK2"))):
        ax.add_patch(Rectangle((bx[0], bx[2]), bx[1] - bx[0], bx[3] - bx[2], fc="#D1D5DB", ec="#6B7280", lw=0.4, zorder=5, alpha=0.9))
        ax.text((bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2, nm.split(".")[0], fontsize=5, ha="center", va="center", zorder=6, clip_on=True)
    for p in sorted(J.OPTIONS[opt]["parts"], key=lambda q: -q[6]):
        b = J.to_box(p, xj, y, z0)
        ax.add_patch(Rectangle((b[0], b[2]), b[1] - b[0], b[3] - b[2], fc=COL[p[1]], ec="#1F2937", lw=0.5, alpha=0.75, zorder=7 + p[7] / 10.0))
    for c in J.cradle(opt, row):
        b = J.to_box_cradle(c, xj, y, z0)
        ax.add_patch(Rectangle((b[0], b[2]), b[1] - b[0], b[3] - b[2], fc="none", ec="#4B5563", lw=0.8, ls="--", zorder=6))
    ax.axvline(xj, color="#B91C1C", lw=0.5, ls=":", zorder=9)
    ax.set_xticks([])
    ax.set_yticks([])


def section(ax, mod, row, opt, vcut=2.5, xr=15.0):
    r, xj, y, z0 = [j for j in J.bridges(mod) if j[0] == row][0]
    zu = z0 - T
    ax.set_xlim(xj - xr, xj + xr)
    ax.set_ylim(L.Z_FLOOR - 1.2, z0 + 9)
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((xj - xr, L.Z_FLOOR - 1.2), 2 * xr, 1.2, fc="#9CA3AF", ec="#374151", lw=0.5))
    for x0 in (xj - L.RULER_L + 0.2, xj + 0.2):
        ax.add_patch(Rectangle((x0, zu), L.RULER_L - 0.4, T, fc="#86EFAC", ec="#14532D", lw=0.6))
    for ru in L.rulers(mod):
        if ru["row"] == row:
            for i in range(4):
                xc = ru["x0"] + L.PITCH / 2 + i * L.PITCH
                if abs(xc - xj) > xr + 8:
                    continue
                ax.add_patch(Rectangle((xc - 7.7, z0 + 2.0), 15.4, 6.5, fc="none", ec="#888", ls="--", lw=0.7))
                idx = int(round((xc - [q[2] for q in L.ROWS if q[0] == row][0]) / L.PITCH))
                nm = L.note_name(row, idx)
                sharp = "#" in nm
                cf = nm[0] in "CF" and not sharp
                ax.text(xc, z0 + 5.2, nm, ha="center", va="center", fontsize=7, fontweight="bold" if cf else "normal", color="white" if sharp else "black",
                        bbox=dict(boxstyle="round,pad=0.15", fc="#1b1b1b" if sharp else ("#FDE68A" if cf else "white"), ec="#444", lw=0.5), clip_on=True)
                for dx in (-L.PEG_DX, L.PEG_DX):
                    ax.add_patch(Rectangle((xc + dx - 0.85, zu - L.PEG_BELOW), 1.7, L.PEG_BELOW, fc="#111827"))
    for p in J.OPTIONS[opt]["parts"]:
        b = J.to_box(p, xj, y, z0)
        if b[2] <= y + vcut <= b[3] or p[1] in ("pino",):
            ax.add_patch(Rectangle((b[0], b[4]), b[1] - b[0], b[5] - b[4], fc=COL[p[1]], ec="#1F2937", lw=0.5, alpha=0.9))
    for c in J.cradle(opt, row):
        b = J.to_box_cradle(c, xj, y, z0)
        if b[2] <= y + vcut <= b[3]:
            ax.add_patch(Rectangle((b[0], b[4]), b[1] - b[0], b[5] - b[4], fc="#D1D5DB", ec="#374151", lw=0.5, hatch="//"))
    ht = J.height_total(opt)
    dfl = J.D_FLOOR[row]
    ax.annotate("", xy=(xj + 11.5, zu), xytext=(xj + 11.5, zu - ht), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text(xj + 9.0, zu - ht / 2 - 1.5, "%.1f mm\n(bolsa %.1f; folga %.1f)" % (ht, dfl, dfl - ht), fontsize=6.5, va="center")
    ax.axvline(xj, color="#B91C1C", lw=0.5, ls=":")
    ax.set_xticks([])


def fig_opcoes(mod=0):
    opts = list(J.OPTIONS)
    fig, axs = plt.subplots(2, len(opts), figsize=(5.2 * len(opts), 7.0), gridspec_kw={"height_ratios": [1.15, 1.0]})
    for i, o in enumerate(opts):
        plan(axs[0][i], mod, 2, o)
        axs[0][i].set_title(__import__("textwrap").fill(J.OPTIONS[o]["titulo"], 46), fontsize=8)
        section(axs[1][i], mod, 1, o, vcut={"E1": 0.0, "E1c": 0.0, "E2": -4.3}.get(o, 2.5))
        axs[1][i].set_title("corte x-z, fileira 1 (bolsa 6,9 mm), v = %s" % ({"E1": "0 (eixo)", "E1c": "0 (eixo)", "E2": "-4,3 (faixa de trás)"}.get(o, "+2,5 (faixa da frente)")), fontsize=7)
    fig.suptitle("R6V4 · junção régua-régua (medidas ESTIMADAS, a confirmar). Planta: junção E4|G4 da fileira 2 (jogador embaixo); corte: junção F#4|A4 da fileira 1. Pinos pretos, sensores vermelhos, trilhos hachurados, peças da régua em cinza.", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "juncao_opcoes_r6.png"), dpi=115)
    plt.close(fig)


def fig_E2(mod=0):
    fig = plt.figure(figsize=(17, 10.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.95])
    a = fig.add_subplot(gs[0, 0:2])
    plan(a, mod, 1, "E2", xr=22)
    a.set_title("E2, planta: junção F#4 | A4 da fileira 1 (bolsa mais rasa). fêmeas azuis (J1/J2 passam a ser a fêmea 1x5) na faixa de trás, ponte (amarela) por baixo, berço tracejado", fontsize=8)
    b = fig.add_subplot(gs[0, 2])
    section(b, mod, 1, "E2", vcut=-4.3, xr=15)
    b.set_title("corte x-z em v = -4,3 (faixa de trás)", fontsize=8)
    # y-section through the right socket (u = +3.45)
    c = fig.add_subplot(gs[1, 0])
    r, xj, y, z0 = [j for j in J.bridges(mod) if j[0] == 1][0]
    zu = z0 - T
    c.set_xlim(y - 8, y + 8)
    c.set_ylim(L.Z_FLOOR - 1.2, z0 + 3)
    c.set_aspect("equal")
    c.add_patch(Rectangle((y - 8, L.Z_FLOOR - 1.2), 16, 1.2, fc="#9CA3AF", ec="#374151"))
    c.add_patch(Rectangle((y - 7, zu), 14, T, fc="#86EFAC", ec="#14532D"))
    for sgn in (1,):                                  # the back rail (v < 0) is notched here (header notch of layout_r4.notches)
        ya, yb = sorted((y + sgn * L.RAIL_IN, y + sgn * L.RAIL_OUT))
        c.add_patch(Rectangle((ya, L.Z_FLOOR), yb - ya, zu - L.Z_FLOOR, fc="#D1D5DB", ec="#374151", hatch="//"))
    for p in J.OPTIONS["E2"]["parts"]:
        if p[2] <= 5.9 <= p[3]:
            bb = J.to_box(p, xj, y, z0)
            c.add_patch(Rectangle((bb[2], bb[4]), bb[3] - bb[2], bb[5] - bb[4], fc=COL[p[1]], ec="k", lw=0.5))
    for cc in J.cradle("E2", 1):
        if cc[1] <= 5.9 <= cc[2]:
            bb = J.to_box_cradle(cc, xj, y, z0)
            c.add_patch(Rectangle((bb[2], bb[4]), bb[3] - bb[2], bb[5] - bb[4], fc="#D1D5DB", ec="k", lw=0.5, hatch="//"))
    c.set_title("corte y-z em u = +5,9 (centro da fêmea de B): faixa de trás v -6,9..-1,7, o trilho de trás está entalhado aqui", fontsize=7.5)
    # assembly
    d = fig.add_subplot(gs[1, 1:3])
    d.axis("off")
    d.text(0, 1.0, "Montagem e retenção (E2)", fontsize=10, fontweight="bold", va="top")
    d.text(0, 0.9, ("1. Bandeja de frente para cima: a ponte (2 machos 1x5, pinos para cima) cai no berço do piso (bloco sob ela: só 0,5 mm na fileira 1, 2,7 / 4,7 / 7,7 nas 2 / 3 / 4; 2 abas nas pontas).\n"
                    "2. As duas réguas (fêmeas viradas para baixo) descem na VERTICAL sobre os machos: 5 contatos por lado, curso de 3,4 mm.\n"
                    "3. M2 de cada régua nas bossas da bandeja: o parafuso fixa a altura da régua, o berço fixa a da ponte: o encaixe não pode soltar,\n"
                    "    só se os parafusos soltarem. Sem esforço lateral: as abas do berço seguram a ponte em x; em y ela é guiada pelos machos.\n"
                    "4. Tampa com as teclas desce: pinos D1,7 entram nos furos das réguas (como antes).\n"
                    "Desmontar: tirar a tampa, os 2 M2 da régua, subir a régua; a ponte fica no berço.\n\n"
                    "Por que não o E1: a régua só se posiciona pelos 8 pinos D1,7 (furo D1,7) e pelo M2 (folga 0,1 mm): deslizar 3 mm em x e\n"
                    "montar da direita para a esquerda é impossível; e a fêmea de 5,6 mm bate no pino da 1ª tecla de B (e o J1/J2 de 9,4 mm, no fundo da régua)."), fontsize=8.2, va="top", linespacing=1.5)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "juncao_E2_r6.png"), dpi=115)
    plt.close(fig)


def board_rows(mod=0):
    rows = []
    rs = L.rulers(mod)
    x_edge = L.BOARD_OUT[2]
    for r, y, x0, n in L.ROWS:
        first = [q for q in rs if q["row"] == r][0]
        dz = L.ZR[r - 1]
        rows.append({"fileira": r, "x_borda_placa": x_edge, "x_inicio_regua": round(first["x0"], 2), "dx_mm": round(first["x0"] - x_edge, 2),
                     "dz_mm": dz, "regua_acima_do_fundo_da_placa_mm": round(dz - 0.0, 1)})
    return rows


def fig_placa(mod=0):
    rows = board_rows(mod)
    rs = L.rulers(mod)
    fig, axs = plt.subplots(1, 2, figsize=(17, 8), gridspec_kw={"width_ratios": [1.1, 1.0]})
    cols = {1: "#2563EB", 2: "#16A34A", 3: "#D97706", 4: "#B91C1C"}
    ax = axs[0]
    ax.set_xlim(60, 130)
    ax.set_ylim(86, 8)
    ax.set_aspect("equal")
    x0, y0, x1, y1 = L.BOARD_OUT
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#EAF3DE", ec="#3B6D11"))
    for ru in rs:
        if ru["k"] == 0:
            ax.add_patch(Rectangle((ru["x0"] + 0.2, ru["y"] - 7), L.RULER_L - 0.4, 14, fc="#BFEBDD", ec="#0F6E56", lw=0.7, alpha=0.9))
            r = ru["row"]
            ax.add_patch(Rectangle((ru["x0"] + 0.5, ru["y"] + 1.25), 6.9, 2.55, fc="#60A5FA", ec="k", lw=0.5, zorder=5))
            ax.text(ru["x0"] + 4, ru["y"] + 2.5, "fêmea E2", fontsize=5.5, ha="center", va="center", zorder=6)
            ax.text(ru["x0"] + 20, ru["y"] - 5.0, "fileira %d: desnível %.0f mm, vão %.2f mm" % (r, L.ZR[r - 1], ru["x0"] - x1), fontsize=7, color=cols[r])
    for r, y, xx, n in L.ROWS:
        a, b = (74.075 - 3.3, 77.4)
        ax.add_patch(Rectangle((a, y - 3.8), b - a, 7.6, fc="#FBCFE8", ec="#9D174D", lw=0.6, zorder=4))
    for c in L.cables(mod):
        if c["de"].startswith("J60"):
            ax.plot([p[0] for p in c["pts"]], [p[1] for p in c["pts"]], color=cols[c["row"]], lw=2, zorder=7)
    for r, y, x0_, n in L.ROWS:
        first = [q for q in rs if q["row"] == r][0]
        # note names of the first two keys of each row
        for i in range(2):
            kx = x0_ + i * L.PITCH
            key_cap(ax, kx, y, L.note_name(r, i), fs=6)
    ax.set_title("Planta: placa (verde), J601..J604 (rosa, boca em x 77,4), 1ª régua de cada fileira com a fêmea E2 do início; cabo SH 25 mm (J601..J604 -> J1)", fontsize=8.5)
    ax = axs[1]
    ax.set_xlim(60, 130)
    ax.set_ylim(-11, 12)
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((60, -1.2), x1 - 60, 1.2, fc="#86EFAC", ec="k"))
    ax.add_patch(Rectangle((60, L.Z_FLOOR - 1.2), 70, 1.2, fc="#9CA3AF", ec="k"))
    for r in (1, 2, 3, 4):
        first = [q for q in rs if q["row"] == r and q["k"] == 0][0]
        z0 = L.ZR[r - 1]
        ax.add_patch(Rectangle((first["x0"] + 0.2, z0 - T), 40, T, fc="#34D399", ec="k", lw=0.5, alpha=0.85))
        ax.text(first["x0"] + 42, z0 - T / 2, "fileira %d (z %.0f)" % (r, z0), fontsize=7, va="center", color=cols[r])
    ax.set_title("Vista lateral: a placa (z 0 = topo) e as réguas das 4 fileiras em 0, 2, 4 e 7 mm", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "juncao_placa_r6.png"), dpi=115)
    plt.close(fig)
    return rows


def main():
    out = {"parametros": "ESTIMADOS, a confirmar (juncao_r6.py)", "opcoes": {k: {"altura_total_mm": J.height_total(k), "folga_bolsa_fil1_mm": round(J.D_FLOOR[1] - J.height_total(k), 2),
                                                                                  "montagem": v["montagem"], "est": v["est"]} for k, v in J.OPTIONS.items()}}
    out["placa_regua"] = fig_placa(0)
    fig_opcoes(0)
    fig_E2(0)
    for m in ((0, 1, 2, 3) if "--tudo" in sys.argv else ()):
        out["fit_%d_teclas" % (32 + 16 * m)] = check(m)
        print("mod", m, "done", flush=True)
    if "--tudo" in sys.argv:
        json.dump(out, open(os.path.join(HERE, "out", "juncao_r6.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
