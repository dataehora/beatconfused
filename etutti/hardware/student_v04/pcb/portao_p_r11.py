"""Gate P (R11V4): the final placement plan of the whole instrument (32 keys) and of the ruler, with coloured blocks, headers, holes
and the main dimensions. CadQuery venv python (matplotlib); reads the DESIGN's layout (case/layout_r4.py, plain Python) so the M2 / post
positions are the design's current ones, and the electronics' pcb/posicao_v4.json + pcb/regua/posicao_regua.json.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v04/pcb/portao_p_r11.py

Writes pcb/img/portao_p_r11_instrumento.png (plan, 32 keys with the note name on every key, C blue / F orange) and
pcb/img/portao_p_r11_cotas.png (main board and ruler with dimensions) plus pcb/img/portao_p.json (numbers quoted in POSICIONAMENTO.md).
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HW, "case"))
import layout_r4 as L  # noqa: E402

IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
pos = json.load(open(os.path.join(HERE, "posicao_v4.json"), encoding="utf-8"))
parts = {p["ref"]: p for p in json.load(open(os.path.join(HERE, "build", "partes_v4.json"), encoding="utf-8"))}
GROUP = {"P": "#7F77DD", "E": "#D85A30", "F": "#1D9E75", "I": "#BA7517", "A": "#2aa57d", "R": "#D4537E"}
USB = {"J201", "U201", "D201", "R201", "R202"}
BLUE, ORANGE = "#1f5fbf", "#e07b00"
ROWC = {1: "#c0392b", 2: "#2c7a3f", 3: "#7a3fb0", 4: "#b07a00"}


def main():
    out = {}
    fig, ax = plt.subplots(figsize=(17, 8.2))
    ax.add_patch(FancyBboxPatch((0, L.Y_BACK), L.length(0), L.CASE[1], boxstyle="round,pad=0,rounding_size=%g" % L.CASE_R,
                                fc="#f6f6f2", ec="#444", lw=1.6, zorder=0))
    x0, y0, x1, y1 = pos["contorno"]
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3", fc="#EAF3DE", ec="#3B6D11", lw=1.3, zorder=1))
    for ref, p in pos["pecas"].items():
        if ref.startswith("H") and ref[1:].isdigit() or ref == "H101":
            continue
        if ref in USB:
            col = "#378ADD"
        else:
            q = parts.get(ref)
            col = GROUP.get(q["sheet"]) if q else None
        if not col:
            continue
        a, b, c, d = p["patio"]
        ax.add_patch(Rectangle((a, b), c - a, d - b, fc=col, ec="none", alpha=0.5, zorder=2))
    ax.text(40, 17.5, "MicroMod", fontsize=7, ha="center", color="#3C3489", zorder=3)
    for ref, (nm, dx, dy) in {"J201": ("USB-C", 0, 0), "J301": ("OUT", 0, 0), "J302": ("IN", 0, 0)}.items():
        p = pos["pecas"][ref]
        ax.text(p["x"], p["y"], nm, fontsize=6, ha="center", va="center", zorder=3)
    ax.text(14, 25, "bateria\n(sob a placa)", fontsize=6, ha="center", zorder=3)
    ax.add_patch(Circle(L.SPEAKER, 14, fc="#2aa57d", alpha=0.25, ec="#2aa57d", zorder=2))
    ax.text(L.SPEAKER[0], L.SPEAKER[1], "alto-falante\nØ28", fontsize=6.5, ha="center", va="center", zorder=3)
    for kx, ky in L.KNOBS:
        ax.add_patch(Circle((kx, ky), 7.5, fc="#fbe9c8", ec="#633806", ls="--", lw=1, zorder=3))
    ax.text(L.KNOBS[0][0], L.KNOBS[0][1] + 9, "volume", fontsize=6.5, ha="center")
    ax.text(L.KNOBS[1][0], L.KNOBS[1][1] + 9, "registro", fontsize=6.5, ha="center")
    for k, (hx, hy) in L.HOLES.items():
        ax.add_patch(Circle((hx, hy), 1.1, fc="white", ec="k", lw=0.8, zorder=5))
        ax.text(hx + 1.5, hy, k, fontsize=5.5, zorder=5)
    # rulers, keys
    rs = L.rulers(0)
    for ru in rs:
        ax.add_patch(Rectangle((ru["x0"] + 0.2, ru["y"] - 7), L.RULER_L - 0.4, 14, fc="#fff3c4", ec=ROWC[ru["row"]], lw=1.0, alpha=0.55, zorder=2))
        for nm, c in (("IN", L.IN_X), ("OUT", L.OUT_X)):
            if nm == "OUT" and ru["last"] and not getattr(L, "OUT_ON_LAST", True):
                continue                      # R11V4: the R8 of the 32-key instrument has no OUT header
            ax.add_patch(Rectangle((ru["x0"] + c - 4.7, ru["y"] + L.LANE_Y0), 9.4, L.HDR_D, fc="#d9548a", ec="k", lw=0.4, alpha=0.8, zorder=4))
            ax.text(ru["x0"] + c, ru["y"] + L.LANE_Y0 + 3, nm, fontsize=5, ha="center", va="center", zorder=5)
        _by = getattr(L, "M2_BY_RULER", {}).get((ru["row"], ru["k"]), L.M2_BY_ROW[ru["row"]])
        for (mx, my) in [(ru["x0"] + du, ru["y"] + 5.2) for du in _by]:
            ax.add_patch(Circle((mx, my), 1.1, fc="white", ec="#c0392b", lw=1.0, zorder=5))
    idx = {}
    for r, x, y in L.key_list(0):
        i = idx.get(r, 0)
        idx[r] = i + 1
        nm = L.note_name(r, i)
        cf = L.is_cf(nm)
        col = BLUE if nm[0] == "C" and cf else ORANGE if cf else "#555"
        ax.add_patch(Circle((x, y), 7.2, fc=(col if cf else "white"), ec=col, lw=1.0, alpha=(0.28 if cf else 1.0), zorder=3))
        ax.text(x, y, nm, fontsize=7.5, ha="center", va="center", color=col, fontweight="bold", zorder=6)
    for (px, py) in L.pick_posts(0):
        ax.add_patch(Circle((px, py), 2.7, fc="#d8f0d0", ec="#2f7a2f", lw=0.8, zorder=4))
    for (px, py) in L.wall_posts(0):
        ax.add_patch(Circle((px, py), 3.0, fc="#d8f0d0", ec="#2f7a2f", lw=0.8, zorder=4))
    for F, ls, lw in ((45.8, "-", 1.4), (50.8, "--", 1.0)):
        try:
            for cb in L.cables(0, F):
                xs = [p[0] for p in cb["pts"]]
                ys = [p[1] for p in cb["pts"]]
                ax.plot(xs, ys, ls, color=ROWC[cb["row"]], lw=lw, zorder=6)
        except Exception as e:                               # the design's helper may not close for every F
            out["cabos_%s_erro" % F] = str(e)
    ax.set_xlim(-4, L.length(0) + 4)
    ax.set_ylim(L.Y_FRONT + 6, L.Y_BACK - 6)
    ax.set_aspect("equal")
    ax.set_title("Student V4, portao P (R11V4): instrumento de 32 teclas, 4 reguas R8, uma por fileira (frente = fileira 1, embaixo). Nome da nota em cada tecla (C azul, F laranja)." + chr(10) + ""
                 "Reguas amarelas, cabecalhos IN/OUT rosa (boca para tras), M2 vermelho (dois por regua), postes verdes, cabos de 45,8 (cheio) e 50,8 mm (tracejado) por fileira.\n"
                 "Placa principal verde; blocos: azul USB, roxo MicroMod, laranja energia, verde audio, ocre interface, rosa conectores das fileiras. Cotas: caixa %.0f x %.0f mm, placa %.2f x %.2f mm."
                 % (L.length(0), L.CASE[1], x1 - x0, y1 - y0), fontsize=6.5)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), + = jogador")
    ax.grid(True, lw=0.12)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "portao_p_r11_instrumento.png"), dpi=130)
    plt.close(fig)
    out["m2_por_fileira_u"] = {str(k): v for k, v in L.M2_BY_ROW.items()}
    out["postes_internos"] = L.pick_posts(0)
    out["postes_parede_x"] = list(L.WALL_POST_X)
    out["caixa_mm"] = [L.length(0), L.CASE[1]]
    json.dump(out, open(os.path.join(IMG, "portao_p_r11.json"), "w"), indent=1)
    print(json.dumps(out)[:600])


if __name__ == "__main__":
    main()
