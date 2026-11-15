"""Looks up every LCSC code of the assembly BOM on LCSC and writes fornecimento/bom_lcsc.json:
what the code really is (maker's part number, package), its stock and its price for the order.

    python etutti/hardware/student_v01/fornecimento/conferir_bom.py [boards]

One request every 3 s, with plain curl (see model3d/fetch_models.py). The comparison of each
package with the board's footprint is read by a person from the table this prints: the names
differ too much between LCSC and KiCad to compare by program.
"""
import csv
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, "..", "fab", "student_v01_bom.csv")
API = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=%s"


def lookup(code):
    raw = subprocess.run(["curl", "-s", "-f", "--max-time", "60", API % code], capture_output=True).stdout
    r = (json.loads(raw).get("result") or {}) if raw else {}
    return r


JLC = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def jlc(keyword):
    """JLCPCB's own parts library (what its assembly line has): rows for a code or a part number."""
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": 10})
    raw = subprocess.run(["curl", "-s", "-f", "--max-time", "60", "-H", "Content-Type: application/json", "-d", body, JLC],
                         capture_output=True).stdout
    try:
        rows = json.loads(raw)["data"]["componentPageInfo"]["list"] or []
    except Exception:
        rows = []
    return [{"lcsc": p.get("componentCode"), "peca": p.get("componentModelEn"), "encapsulamento": p.get("componentSpecificationEn"),
             "classe": {"base": "basica", "expand": "estendida"}.get(p.get("componentLibraryType"), p.get("componentLibraryType")),
             "estoque_jlc": p.get("stockCount")} for p in rows]


def price_for(r, qty):
    best = None
    for p in r.get("productPriceList") or []:
        if p["ladder"] <= max(qty, r.get("minBuyNumber") or 1):
            best = p["usdPrice"]
    return best if best is not None else ((r.get("productPriceList") or [{}])[0].get("usdPrice"))


def main():
    boards = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5
    rows = list(csv.DictReader(open(BOM, encoding="utf-8")))
    out = []
    for row in rows:
        code = row["LCSC Part #"].strip()
        n = len(row["Designator"].split(","))
        rec = {"valor": row["Comment"], "refs": row["Designator"], "n": n, "footprint": row["Footprint"], "lcsc": code}
        if code:
            r = lookup(code)
            time.sleep(2)
            j = next((x for x in jlc(code) if x["lcsc"] == code), None)
            time.sleep(2)
            rec.update({"classe": j["classe"], "estoque_jlc": j["estoque_jlc"]} if j else {"classe": None, "estoque_jlc": None})
            if r:
                qty = n * boards
                rec.update({"peca": r.get("productModel"), "marca": r.get("brandNameEn"),
                            "encapsulamento": r.get("encapStandard"), "categoria": r.get("catalogName"),
                            "estoque": r.get("stockNumber"), "minimo": r.get("minBuyNumber"),
                            "multiplo": r.get("split"), "preco_usd": price_for(r, qty),
                            "descricao": (r.get("productIntroEn") or "")[:160]})
            else:
                rec["erro"] = "sem resposta da LCSC"
        out.append(rec)
        print("%-9s %-22s | %-22s %-16s | LCSC %-8s JLC %-8s %-9s | US$ %-7s | %s x%d" % (
            code or "-", (rec.get("peca") or rec.get("erro") or "GLOBAL SOURCING")[:22], row["Footprint"][:22],
            (rec.get("encapsulamento") or "")[:16], rec.get("estoque", ""), rec.get("estoque_jlc", ""),
            rec.get("classe") or "", rec.get("preco_usd", ""), row["Comment"][:18], n), flush=True)
    if "--buscar" in sys.argv:              # extra searches by part number, printed only
        for k in sys.argv[sys.argv.index("--buscar") + 1:]:
            for x in jlc(k):
                print("busca %-22s -> %s" % (k, x), flush=True)
            time.sleep(2)
    json.dump({"placas": boards, "linhas": out}, open(os.path.join(HERE, "bom_lcsc.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
