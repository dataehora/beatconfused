"""eTutti Slim (R4SL item 1): longitudinal sections proving CONTINUOUS support under the four rulers. PyVista (slice) + matplotlib.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/case.py          (first: writes out/base.stl)
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/corte_apoio.py   -> case/renders/corte_apoio_4fileiras.png, case/out/apoio.json

For every row: the section plane through the support rail (|v| = 6.75, both rails) and through the centre line (v = 0). The check is NUMERIC: along the whole ruler
(tail included) the base must be solid between the floor and the ruler's bottom face under each rail (probe line 0.1 mm under the ruler); the report lists the gaps (none expected).
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_slim as L  # noqa: E402

OUT = os.path.join(HERE, "out")
REN = os.path.join(HERE, "renders")
os.makedirs(REN, exist_ok=True)
base = pv.read(os.path.join(OUT, "base.stl"))


def intervals(slc, z):
    """x intervals of material along the horizontal line z in a slice (closed loops in the x-z plane)."""
    xs = []
    pts = slc.points
    lines = slc.lines.reshape(-1, 3)[:, 1:] if slc.n_lines else []
    for a, b in lines:
        za, zb = pts[a][2], pts[b][2]
        if (za - z) * (zb - z) < 0:
            t = (z - za) / (zb - za)
            xs.append(float(pts[a][0] + t * (pts[b][0] - pts[a][0])))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def covered(iv, x0, x1):
    gaps, cur = [], x0
    for a, b in sorted(iv):
        if b <= cur:
            continue
        if a >= x1 - 1e-3:
            break
        if a > cur + 1e-3:
            gaps.append((round(cur, 2), round(a, 2)))
        cur = max(cur, b)
    if cur < x1 - 1e-3:
        gaps.append((round(cur, 2), round(x1, 2)))
    return gaps


def main():
    rep = {"revisao": "R4SL", "regra": "apoio continuo em todo o comprimento, o mesmo tipo nas 4 fileiras, sem furos no piso", "fileiras": []}
    fig, axes = plt.subplots(4, 2, figsize=(22, 14))
    for r in range(4):
        x0, x1 = L.ROW_X0[r] - L.U_KEY1, L.ROW_X0[r] - L.U_KEY1 + L.RULER_L
        zb = L.RULER_BOT[r]
        y0 = L.ROW_Y[r]
        row = {"fileira": r + 1, "x": [round(x0, 2), round(x1, 2)], "regua_baixo_z": round(zb, 2), "trilhos": []}
        for c, (vname, v) in enumerate((("trilho v = +6,75", 6.75), ("centro v = 0", 0.0))):
            ax = axes[r][c]
            slc = base.slice(normal="y", origin=(0, y0 + v, 0))
            # base outline (lines)
            pts = slc.points
            for a, b in (slc.lines.reshape(-1, 3)[:, 1:] if slc.n_lines else []):
                ax.plot([pts[a][0], pts[b][0]], [pts[a][2], pts[b][2]], color="#1d1d1f", lw=0.6)
            ax.add_patch(plt.Rectangle((x0, zb), x1 - x0, 1.2, color="#2f6b3a", alpha=0.85))
            ax.plot([x0, x1], [zb - 0.1, zb - 0.1], color="#b3261e", lw=0.6, ls="--")
            for k in range(L.NKEYS):
                xk = L.ROW_X0[r] + L.P * k
                ax.add_patch(plt.Rectangle((xk - 7.0, zb + 1.2), 14.0, 5.85 - 1.2 + 1.2, fill=False, ec="#8b8b8b", lw=0.4))
            if c == 0:
                iv = intervals(slc, zb - 0.1)
                gaps = covered(iv, x0, x1)
                row["trilhos"].append({"plano": vname, "intervalos_de_material": [(round(a, 2), round(b, 2)) for a, b in iv], "vaos": gaps})
                ax.set_title("fileira %d - %s: material de %.2f a %.2f; vaos: %s" % (r + 1, vname, min(a for a, b in iv) if iv else 0, max(b for a, b in iv) if iv else 0, gaps or "nenhum"), fontsize=9)
            else:
                ax.set_title("fileira %d - %s (zona livre sob a regua; bolsos sob os postes so na fileira 1)" % (r + 1, vname), fontsize=9)
            ax.set_xlim(-102, 150)
            ax.set_ylim(0, 14)
            ax.set_aspect("equal")
            ax.axvline(L.ROW_X0[r] - L.U_KEY1 + 14.0, color="#999", lw=0.4, ls=":")
        # the other rail (-6.75) too
        slc2 = base.slice(normal="y", origin=(0, y0 - 6.75, 0))
        iv2 = intervals(slc2, zb - 0.1)
        row["trilhos"].append({"plano": "trilho v = -6,75", "intervalos_de_material": [(round(a, 2), round(b, 2)) for a, b in iv2], "vaos": covered(iv2, x0, x1)})
        row["continuo"] = all(not t["vaos"] for t in row["trilhos"])
        rep["fileiras"].append(row)
    fig.suptitle("eTutti Slim R4SL - apoio das 4 reguas: cortes longitudinais da base (verde = regua, tracejado vermelho = linha de prova 0,1 mm sob a regua; cauda a esquerda)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(REN, "corte_apoio_4fileiras.png"), dpi=110)
    rep["todas_continuas"] = all(f["continuo"] for f in rep["fileiras"])
    json.dump(rep, open(os.path.join(OUT, "apoio.json"), "w", encoding="utf-8"), indent=1)
    for f in rep["fileiras"]:
        print("fileira", f["fileira"], "continuo", f["continuo"], [t["vaos"] for t in f["trilhos"]])
    print("todas continuas:", rep["todas_continuas"])


if __name__ == "__main__":
    main()
