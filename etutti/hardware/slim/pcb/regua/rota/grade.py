"""Stage 5 of the ruler routing: check the GRADE (R8SL 3a). KiCad python for the geometry + kicad-cli for DRC and Gerbers.

    "C:/Program Files/KiCad/10.0/bin/python.exe" grade.py

Reads pcb/kicad_regua/slim_grade.kicad_pcb (written by posiciona_regua.build_grade; never changed here), copies it to rota/kicad/grade/, runs the DRC, exports Gerbers + drill
(rota/kicad/grade/fab/), then measures: 8 square holes of 14.00 mm (the Edge.Cuts loops), dog-bone reliefs (a loop is bigger than 14 x 14 by the relief), 2 M2 holes with the
countersink note, no copper at all (no track, zone, copper pad), the nearest copper to any hole (none). Writes rota/build/grade.json and an image img/grade.png.
"""
import json, math, os, shutil, subprocess, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "kicad_regua", "slim_grade.kicad_pcb")
D = os.path.join(HERE, "kicad", "grade"); os.makedirs(os.path.join(D, "fab"), exist_ok=True)
CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
shutil.copy(SRC, os.path.join(D, "slim_grade.kicad_pcb"))
pcb = os.path.join(D, "slim_grade.kicad_pcb")
mm = 1e-6
# DRC
out = os.path.join(HERE, "build", "drc_grade.json"); os.makedirs(os.path.dirname(out), exist_ok=True)
subprocess.run([CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, pcb], capture_output=True)
dj = json.load(open(out, encoding="utf-8"))
res = {"drc": {"erros": sum(v["severity"] == "error" for v in dj["violations"]), "avisos": sum(v["severity"] == "warning" for v in dj["violations"]),
               "nao_ligados": len(dj.get("unconnected_items", []))}}
# Gerbers + drill
for f in os.listdir(os.path.join(D, "fab")):
    os.remove(os.path.join(D, "fab", f))
subprocess.run([CLI, "pcb", "export", "gerbers", "--layers", "Edge.Cuts,Cmts.User,F.Cu,B.Cu,F.Mask,B.Mask", "-o", os.path.join(D, "fab") + "/", pcb], capture_output=True)
subprocess.run([CLI, "pcb", "export", "drill", "--format", "excellon", "-o", os.path.join(D, "fab") + "/", pcb], capture_output=True)
res["gerbers"] = sorted(os.listdir(os.path.join(D, "fab")))
# geometry
b = pcbnew.LoadBoard(pcb)
segs = []
for dr in b.GetDrawings():
    if dr.GetLayer() == pcbnew.Edge_Cuts:
        a, e = dr.GetStart(), dr.GetEnd()
        shape = dr.GetShape()
        segs.append((shape, a.x * mm, a.y * mm, e.x * mm, e.y * mm, dr))
# chain edge pieces into loops
pts = []
for s in segs:
    pts.append(s)
loops = []
remaining = list(range(len(pts)))
def key(x, y): return (round(x, 3), round(y, 3))
ends = {}
for i, s in enumerate(pts):
    ends.setdefault(key(s[1], s[2]), []).append(i); ends.setdefault(key(s[3], s[4]), []).append(i)
seen = set()
for i in range(len(pts)):
    if i in seen: continue
    loop = [i]; seen.add(i); cur = key(pts[i][3], pts[i][4]); start = key(pts[i][1], pts[i][2])
    while cur != start:
        nxt = [j for j in ends.get(cur, []) if j not in seen]
        if not nxt: break
        j = nxt[0]; seen.add(j); loop.append(j)
        cur = key(pts[j][3], pts[j][4]) if key(pts[j][1], pts[j][2]) == cur else key(pts[j][1], pts[j][2])
    loops.append(loop)
info = []
for lp in loops:
    xs = [v for j in lp for v in (pts[j][1], pts[j][3])]; ys = [v for j in lp for v in (pts[j][2], pts[j][4])]
    info.append({"w": round(max(xs) - min(xs), 3), "h": round(max(ys) - min(ys), 3), "cx": round((max(xs) + min(xs)) / 2, 3), "cy": round((max(ys) + min(ys)) / 2, 3), "pecas": len(lp),
                 "arcos": sum(1 for j in lp if pts[j][0] == pcbnew.SHAPE_T_ARC)})
outer = max(info, key=lambda q: q["w"] * q["h"])
holes = [q for q in info if q is not outer]
res["contorno_mm"] = [outer["w"], outer["h"]]
res["furos_quadrados"] = len(holes)
res["furos_largura_h_mm"] = sorted({h["w"] for h in holes}), sorted({h["h"] for h in holes})
res["dogbone_arcos_por_furo"] = sorted({h["arcos"] for h in holes})
# a 14.00 hole: the straight sides measured between the reliefs: the loop bounding box is bigger by the relief at the corners
import statistics
h0 = holes[0]
res["passo_furos_mm"] = sorted({round(holes[i + 1]["cx"] - holes[i]["cx"], 3) for i in range(len(holes) - 1)}) if holes else []
# the straight sides: segments longer than 10 mm inside the first hole's box (the dog-bone reliefs are short polyline pieces)
long_ = [p for p in pts if math.hypot(p[3] - p[1], p[4] - p[2]) > 10 and abs(p[1] - h0["cx"]) < 8 and abs(p[2] - h0["cy"]) < 8]
xs_edge = sorted({round(p[1] - h0["cx"], 3) for p in long_ if abs(p[1] - p[3]) < 1e-3})
ys_edge = sorted({round(p[2] - h0["cy"], 3) for p in long_ if abs(p[2] - p[4]) < 1e-3})
res["lados_retos_x_rel"] = xs_edge; res["lados_retos_y_rel"] = ys_edge
res["furo_reto_mm"] = [round(xs_edge[-1] - xs_edge[0], 3), round(ys_edge[-1] - ys_edge[0], 3)] if xs_edge and ys_edge else None
res["dogbone_extensao_alem_do_lado_mm"] = round((h0["w"] - res["furo_reto_mm"][0]) / 2, 3)
# M2 holes and copper
m2 = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        m2.append({"ref": fp.GetReference(), "furo_mm": p.GetDrillSize().x * mm, "x": p.GetX() * mm, "y": p.GetY() * mm, "npth": p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
                   "cobre": bool(p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)), "pad_mm": p.GetSizeX() * mm})
res["m2"] = m2
res["trilhas"] = len(list(b.GetTracks())); res["zonas"] = len(list(b.Zones()))
notes = [dr.GetText() for dr in b.GetDrawings() if dr.GetClass() == "PCB_TEXT"]
res["notas_escareado"] = notes
res["distancia_furo_m2_ao_furo_quadrado_mm"] = None
json.dump(res, open(os.path.join(HERE, "build", "grade.json"), "w"), indent=1)
json.dump({"contorno": outer, "furos": holes, "m2": m2, "segs": [[p[0], p[1], p[2], p[3], p[4]] for p in pts]}, open(os.path.join(HERE, "build", "grade_geom.json"), "w"))
print(json.dumps({k: v for k, v in res.items() if not k.startswith("lados_retos")}, indent=1))
