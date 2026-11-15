"""Does anything of the instrument sit inside the case's plastic?

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v01/case/fit_check.py

Takes the assembled instrument of model3d/build.py and, for every group of parts, counts the
mesh points that lie more than 0.15 mm inside the fundo or the tampa, and how deep the worst one
is. Parts that are meant to touch the case (the board on its bosses, the plate under the rim)
touch at a face and stay under that margin. Writes out/fit_check.json; exits non-zero when a
group goes deeper than 0.15 mm.

It also lists the clearances that matter: under the battery, above the tallest parts under the
lid, between the lid and a pressed key cap.
"""
import json
import os
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model3d"))
sys.path.insert(0, HERE)
import build as model      # noqa: E402
import case as C           # noqa: E402

MARGIN = 0.15
KEY_TRAVEL = 4.1


def main():
    parts, _ = model.assemble()
    shells = {g: m.triangulate().compute_normals(auto_orient_normals=True) for g, m, _ in parts if g in ("case_fundo", "case_tampa")}
    groups = {}
    for g, m, _ in parts:
        if g.startswith("case_") or g == "pilares":
            continue
        groups.setdefault(g, []).append(np.asarray(m.points))
    out, bad = {}, []
    for g, chunks in sorted(groups.items()):
        pts = pv.PolyData(np.vstack(chunks))
        rec = {}
        for name, shell in shells.items():
            d = pts.compute_implicit_distance(shell)["implicit_distance"]     # negative inside
            inside = d < -MARGIN
            rec[name] = {"pontos_dentro": int(inside.sum()), "mais_fundo_mm": round(float(-d.min()), 2) if inside.any() else 0.0}
            if inside.any():
                where = pts.points[np.argmin(d)]
                rec[name]["onde_x_ykicad_z"] = [round(float(where[0]), 1), round(float(-where[1]), 1), round(float(where[2]), 1)]
                bad.append((g, name, rec[name]))
        out[g] = rec
    z = {g: (float(min(c[:, 2].min() for c in ch)), float(max(c[:, 2].max() for c in ch))) for g, ch in groups.items()}
    under = C.LID_TOP - C.LID_T
    clear = {
        "sob a bateria (fundo interno)": round(z["bateria"][0] + C.DEPTH, 2),
        "sob o conector da bateria e as pecas de baixo": round(z["pecas_baixo"][0] + C.DEPTH, 2),
        "sob o modulo": round(z["modulo"][0] + C.DEPTH, 2),
        "entre o alto-falante e a placa": round(under - C.SPEAKER_H, 2),
        "tampa acima do USB-C (3,25) e do jack (4,75)": [round(under - 3.25, 2), round(under - 4.75, 2)],
        "entre a tampa e a capa de uma tecla apertada": round(z["capas"][0] + 3.7 - KEY_TRAVEL - C.LID_TOP, 2),
        "tampa abaixo do topo do alojamento das teclas": round(C.PLATE_TOP + 6.1 - C.LID_TOP, 2),
    }
    json.dump({"margem_mm": MARGIN, "grupos": out, "folgas_mm": clear}, open(os.path.join(HERE, "out", "fit_check.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    for g, rec in out.items():
        print("%-14s %s" % (g, {k: (v["pontos_dentro"], v["mais_fundo_mm"]) for k, v in rec.items()}))
    print(json.dumps(clear, indent=1, ensure_ascii=False))
    for b in bad:
        print("INTERFERENCIA:", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
