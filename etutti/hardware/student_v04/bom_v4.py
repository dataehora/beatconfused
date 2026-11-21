"""BOM of the V4 main board (JLCPCB bottom assembly): classes and prices from fornecimento/precos_jlc.json (21 nov).

    python etutti/hardware/student_v04/bom_v4.py     (after pcb/schematic.py)  -> bom_v4.csv, bom_v4.json
"""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
pj = json.load(open(os.path.join(HERE, "fornecimento", "precos_jlc.json"), encoding="utf-8"))
parts = json.load(open(os.path.join(HERE, "pcb", "build", "partes_v4.json"), encoding="utf-8"))
rows, ext, total, unknown = {}, set(), 0.0, []
for p in parts:
    if not p["lcsc"] or p["mount"].startswith(("sem peca", "em casa")):
        continue
    info = pj.get(p["lcsc"])
    if not info:
        unknown.append((p["ref"], p["lcsc"])); cls, price = "?", p["price"] or 0
    else:
        cls = info["classe"]; tiers = info["tiers"]; price = tiers[0][1]
    r = rows.setdefault(p["lcsc"], dict(lcsc=p["lcsc"], valor=p["value"], classe=cls, refs=[], preco=price))
    r["refs"].append(p["ref"]); total += price
    if cls != "Basic": ext.add(p["lcsc"])
out = sorted(rows.values(), key=lambda r: r["refs"][0])
with open(os.path.join(HERE, "bom_v4.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["lcsc", "valor", "classe_jlc", "qtd", "referencias", "preco_unit_usd"])
    for r in out: w.writerow([r["lcsc"], r["valor"], r["classe"], len(r["refs"]), " ".join(r["refs"]), r["preco"]])
res = {"linhas": len(out), "pecas": sum(len(r["refs"]) for r in out), "tipos_extended": len(ext), "extended": sorted(ext),
       "pecas_usd_por_placa": round(total, 2), "sem_preco": unknown}
json.dump(res, open(os.path.join(HERE, "bom_v4.json"), "w"), indent=1)
print(res)
