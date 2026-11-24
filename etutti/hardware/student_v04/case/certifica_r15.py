"""R15V4 item 4.1 (exact certificate): re-run the 0.05 mm plan-section opening (disc r = 0.75 = the 1.5 mm rule) on the FINAL base mesh, band by band; prints every piece narrower than 1.5 mm with area >= 0.2 mm2
(corner residues of <= 0.13 mm2 do not count) and its height (sum of the bands it appears in). Usage: certifica_r15.py [stl]"""
import json, os, sys
import numpy as np, pyvista as pv
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fragil_r15 as P
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "r4_32_base.stl")
    m = pv.read(path); b = m.bounds
    org = (b[0] - 0.5, b[2] - 0.5); dims = (int((b[1] - b[0] + 1) / P.PIX) + 1, int((b[3] - b[2] + 1) / P.PIX) + 1)
    # bands from the mesh's horizontal facets: use the section z's of the STL via unique z of vertices with normals up/down
    zs = np.unique(np.round(m.points[:, 2], 3))
    bands = [(a, c) for a, c in zip(zs[:-1], zs[1:]) if c - a >= 0.1]
    out = []
    for za, zb in bands:
        F = P.slice_mask(m, (za + zb) / 2, org, dims)
        E = ndi.distance_transform_edt(F) >= 0.75 / P.PIX
        O = ndi.distance_transform_edt(~E) <= 0.75 / P.PIX if E.any() else np.zeros_like(F)
        T = F & ~O
        T[:, :int((79 - org[0]) / P.PIX)] = False
        lab, n = ndi.label(T)
        for k, sl in enumerate(ndi.find_objects(lab), start=1):
            a = (lab[sl] == k).sum() * P.PIX ** 2
            if a >= 0.2:
                out.append({"z": [float(za), float(zb)], "x": [round(org[0] + sl[1].start * P.PIX, 1), round(org[0] + sl[1].stop * P.PIX, 1)],
                            "y": [round(-(org[1] + sl[0].stop * P.PIX), 1), round(-(org[1] + sl[0].start * P.PIX), 1)], "area": round(float(a), 2)})
    print(len(bands), "bandas;", len(out), "pecas finas (>= 0.2 mm2)")
    for o in out: print(o)
    json.dump(out, open(os.path.join(HERE, "out", "certificado_r15.json"), "w"), indent=1)
main()
