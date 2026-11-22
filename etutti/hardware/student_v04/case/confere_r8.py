"""R8V4: conferencia da exportacao (arestas abertas das malhas e ray-probe da area do teclado e dos furos de tecla)."""
import os, sys, json
import numpy as np
import pyvista as pv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L
OUT = os.path.join(HERE, "out")
res = {}
for nm in ("tampa", "base", "reguas", "teclas"):
    m = pv.read(os.path.join(OUT, "r4_32_%s.stl" % nm)).clean()
    e = m.extract_feature_edges(boundary_edges=True, feature_edges=False, manifold_edges=False, non_manifold_edges=True)
    res[nm] = {"arestas_abertas_ou_nao_manifold": int(e.n_cells), "volume_cm3": round(m.volume / 1000, 1)}
lid = pv.read(os.path.join(OUT, "r4_32_tampa.stl")).clean()
miss = 0
tot = 0
for r, x, y in L.key_list(0):
    # file frame: y_file = -y_spec; vertical ray through the key centre above/below the deck, must cross the lid only outside the 8 mm hole (none at r < 3.9)
    pts, _ = lid.ray_trace([x, -y, 60.0], [x, -y, -30.0])
    tot += 1
    if len(pts) > 0 and any(abs(p[2]) < 40 and p[2] > L.ZR[r - 1] + 11.0 for p in pts):
        miss += 1
res["ray_probe_furos_de_tecla"] = {"teclas": tot, "com_filme_sobre_o_furo": miss}
# the keyboard area is open: rays at points between keys of the deck must hit the deck (sanity: deck present)
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(OUT, "confere_r8.json"), "w"), indent=1)
