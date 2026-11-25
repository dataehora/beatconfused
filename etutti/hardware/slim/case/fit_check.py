"""eTutti Slim (R12SL): interference check of the whole assembly (the 7-step model of montagem.py + the lid). CadQuery + PyVista.

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/case/fit_check.py   -> case/out/fit_check.json (+ prints the pairs)

Method: the vertices of every moving or fixed component (densified) are tested against the CLOSED solids of the base, the lid, the four ruler boards, the four grades and
the main board with `compute_implicit_distance`; a vertex deeper than 0.08 mm inside a solid it does not belong to is an interference.  Contacts (a nut in its pocket,
a ruler on its guide, a peg in its hole) sit at distance ~0 and do not count.  Pairs that are SUPPOSED to overlap (a screw through its own grade/ruler holes: 0.1 mm
clearance) are tested too: they pass because the holes are cut in the models.
"""
import json
import os
import sys

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montagem as M  # noqa: E402

DEPTH = 0.08


def dens(m, n=40000):
    """vertices of the mesh, plus the midpoints of its edges when the mesh is coarse"""
    pts = np.array(m.points)
    if len(pts) < n // 4:
        try:
            e = m.extract_all_edges()
            pairs = e.lines.reshape(-1, 3)[:, 1:]
            mid = (np.array(e.points)[pairs[:, 0]] + np.array(e.points)[pairs[:, 1]]) / 2
            pts = np.vstack([pts, mid])
        except Exception:  # noqa: BLE001
            pass
    return pts


def inside_count(points, solid):
    cloud = pv.PolyData(points)
    d = cloud.compute_implicit_distance(solid, inplace=False)["implicit_distance"]
    return int(np.sum(d < -DEPTH)), float(d.min())


def main():
    G, cables = M.build_groups()
    lid = pv.read(os.path.join(M.OUT, "tampo.stl"))
    solids = {"base": [m for m in G[1] if m[3] == "base"][0][0], "tampo": lid}
    for r in range(4):
        grp = G[3 + r]
        solids["regua%d" % r] = [m for m in grp if m[3] == "regua%d" % r][0][0]
        solids["grade%d" % r] = [m for m in grp if m[3] == "grade%d" % r][0][0]
    solids["placa"] = [m for m in G[2] if m[3] == "placa"][0][0]
    comps = []                                    # (name, mesh, own solids that do not count)
    for m, col, op, nm in G[2]:
        if nm not in ("placa",):
            comps.append((nm, m, {"placa"}))
    for r in range(4):
        for m, col, op, nm in G[3 + r]:
            own = {"regua%d" % r, "grade%d" % r}
            if nm in ("regua%d" % r, "grade%d" % r):
                comps.append((nm, m, own))
            elif nm == "ferragem":
                comps.append(("ferragem%d" % r, m, own))      # holes are cut in the models: kept in the test
            else:
                comps.append((nm, m, own))
    for m, col, op, nm in G[7]:
        r = int(nm.rsplit("_", 1)[-1])
        comps.append((nm, m, {"regua%d" % r, "grade%d" % r}))
    for m, col, op, nm in G[1]:
        if nm.startswith("porca"):
            comps.append((nm, m, {"base"}))
    bad = []
    n_tests = 0
    for nm, m, own in comps:
        pts = dens(m)
        bb = np.array(m.bounds)
        for sn, sol in solids.items():
            if sn in own or sn == nm:
                continue
            sb = np.array(sol.bounds)
            if np.any(bb[0::2] > sb[1::2]) or np.any(bb[1::2] < sb[0::2]):
                continue
            n_tests += 1
            c, dmin = inside_count(pts, sol)
            if c:
                bad.append({"peca": nm, "dentro_de": sn, "pontos": c, "penetracao_max_mm": round(-dmin, 3)})
    json.dump({"revisao": "R12SL", "pares_testados": n_tests, "profundidade_limite_mm": DEPTH, "interferencias": bad}, open(os.path.join(M.OUT, "fit_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("pares testados:", n_tests, "interferencias:", len(bad))
    for b in bad[:40]:
        print(b)


if __name__ == "__main__":
    main()
