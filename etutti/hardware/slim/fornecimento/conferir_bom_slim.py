"""Checks every LCSC code of the Slim BOMs (main board + R8 ruler) on LCSC and JLCPCB: real part number, package, stock, class.

    python etutti/hardware/slim/fornecimento/conferir_bom_slim.py

Reads pcb/bom_esquema.csv and pcb/bom_regua.csv; writes fornecimento/bom_conferido.json and .csv. One request every 2 s (plain curl).
Nothing is bought or ordered.
"""
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import busca_jlc as B  # noqa: E402

PCB = os.path.join(HERE, "..", "pcb")


def main():
    codes = {}
    for fn, who in (("bom_esquema.csv", "principal"), ("bom_regua.csv", "regua")):
        for r in csv.DictReader(open(os.path.join(PCB, fn), encoding="utf-8")):
            lc = (r.get("lcsc") or "").strip()
            if lc and lc != "-":
                e = codes.setdefault(lc, {"placas": set(), "refs": [], "valor": r.get("valor") or r.get("valor_peca")})
                e["placas"].add(who)
                e["refs"].append("%s:%s" % (who[0], r.get("referencias")))
    out = []
    for lc in sorted(codes):
        e = codes[lc]
        d = B.lcsc(lc)
        time.sleep(1.5)
        j = [x for x in B.jlc(lc, 3) if x.get("componentCode") == lc]
        time.sleep(1.5)
        rec = {"lcsc": lc, "valor": e["valor"], "placas": "+".join(sorted(e["placas"])), "refs": " ".join(e["refs"])[:80],
               "peca": d.get("productModel"), "encapsulamento": d.get("encapStandard"), "estoque_lcsc": d.get("stockNumber"),
               "estoque_jlc": j[0].get("stockCount") if j else None,
               "classe": {"base": "Basic", "expand": "Extended"}.get(j[0].get("componentLibraryType")) if j else None,
               "preco_usd": (d.get("productPriceList") or [{}])[0].get("usdPrice")}
        out.append(rec)
        print("%-9s %-26s %-18s LCSC %-8s JLC %-8s %-8s %s" % (lc, (rec["peca"] or "?")[:26], (rec["encapsulamento"] or "")[:18],
              rec["estoque_lcsc"], rec["estoque_jlc"], rec["classe"], rec["placas"]), flush=True)
    json.dump(out, open(os.path.join(HERE, "bom_conferido.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "bom_conferido.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
