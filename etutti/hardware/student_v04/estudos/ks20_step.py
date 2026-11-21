"""eTutti Student V4 (R3V4): measurements on the Gateron STEP (fornecimento/gateron/KS-20T_20210922.stp, a 2021 KS-20T).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/estudos/ks20_step.py

Seat plane found at z = 0.85 (main underside; the top collar is then 11.10 above it, as on the Orange drawing). Writes estudos/ks20_step.json:
horizontal faces by height above the seat, and the section extents every 0.5 mm. The STEP differs from the 2023 Orange PDF (centre post instead of
the two pegs, two stem posts instead of the central cross): use the PDF for pins and stem, the STEP only for the cover/flange envelope.
"""
import json, os
import cadquery as cq, numpy as np
H = os.path.dirname(os.path.abspath(__file__))
s = cq.importers.importStep(os.path.join(H, "..", "fornecimento", "gateron", "KS-20T_20210922.stp")).val()
cy, seat = 26.5, 0.85
faces = []
for f in s.Faces():
    if f.geomType() == "PLANE":
        n = f.normalAt()
        if abs(abs(n.z) - 1) < 1e-6 and f.Area() > 0.8:
            b = f.BoundingBox()
            faces.append({"z_rel": round(b.zmin - seat, 2), "dir": "cima" if n.z > 0 else "baixo", "area": round(f.Area(), 1),
                          "x": [round(b.xmin, 2), round(b.xmax, 2)], "y": [round(b.ymin - cy, 2), round(b.ymax - cy, 2)]})
faces.sort(key=lambda d: d["z_rel"])
bb = s.BoundingBox()
json.dump({"seat_z": seat, "bbox": [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin - cy, bb.ymax - cy, bb.zmin - seat, bb.zmax - seat)],
           "faces_horizontais": faces}, open(os.path.join(H, "ks20_step.json"), "w"), indent=1)
print(len(faces), "faces; bbox rel seat", [round(v, 2) for v in (bb.zmin - seat, bb.zmax - seat)])
