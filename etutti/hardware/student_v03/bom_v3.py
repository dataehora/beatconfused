"""eTutti Student V3: the bill of materials, with JLCPCB's library class (Basic / Extended) of every code.

    python etutti/hardware/student_v03/bom_v3.py

Starts from the V2 BOM (student_v02/fab/student_v02_bom.csv), applies the V3 value changes (the same as
build_sem_rota.py: R203, R501, C307 and the four BAT54C -> BAV70), drops H101 (now a plain hole) and
asks JLCPCB's parts library for each code's class and stock (curl, 2 s apart). Everything is assembled
by JLCPCB on the bottom side except the two encoders (soldered at home, top side).
Writes bom_v3.csv and bom_v3.json. JLCPCB charges US$ 3.09 for each Extended part type (quote of
18 Nov 2026).
"""
import csv
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2F = os.path.normpath(os.path.join(HERE, "..", "student_v02", "fab"))
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
FEE = 3.09
SUBS = {"R203": ("2.2k", "C25879"), "R501": ("1M", "C26083"), "C307": ("100nF", "C1525"),
        "D202": ("BAV70", "C68978"), "D203": ("BAV70", "C68978"), "D204": ("BAV70", "C68978"), "D205": ("BAV70", "C68978"),
        "J301": ("PJ-327A", "C49284723"), "J302": ("PJ-327A", "C49284723")}
DROP = {"H101": "agora um furo liso de 2,7 mm (parafuso M2,5, espaçador de nylon de 2,5 mm e porca)"}
HOME = {"SW401": "encoder do volume", "SW402": "encoder do registro"}


def lib_class(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10})
    raw = subprocess.run(["curl", "-s", "-f", "--max-time", "60", "-H", "Content-Type: application/json", "-d", body, API],
                         capture_output=True).stdout
    try:
        for p in json.loads(raw)["data"]["componentPageInfo"]["list"] or []:
            if p.get("componentCode") == code:
                return {"base": "Basic", "expand": "Extended"}.get(p.get("componentLibraryType"), "?"), p.get("stockCount")
    except Exception:
        pass
    return "?", None


def main():
    per = []
    for r in csv.DictReader(open(os.path.join(V2F, "student_v02_bom.csv"), encoding="utf-8")):
        for ref in r["Designator"].split(","):
            if ref in DROP:
                continue
            val, code = SUBS.get(ref, (r["Comment"], r["LCSC Part #"]))
            per.append((ref, val, r["Footprint"], code))
    per.append(("D206", "BAV70", "SOT-23", "C68978"))      # new in the V3: a USB plug switches the 3.3 V on
    groups = {}
    for ref, val, fp, code in per:
        groups.setdefault((code, val, fp), []).append(ref)
    rows, classes = [], {}
    for (code, val, fp), refs in groups.items():
        if code not in classes:
            classes[code] = lib_class(code)
            time.sleep(1.5)
        cls, stock = classes[code]
        home = [x for x in refs if x in HOME]
        rows.append({"valor": val, "designadores": ",".join(refs), "qtd": len(refs), "footprint": fp, "lcsc": code, "classe": cls,
                     "estoque_jlc": stock, "montagem": "casa (topo)" if len(home) == len(refs) else "JLCPCB (fundo)"})
        print("%-9s %-9s x%-2d %-22s %s" % (code, cls, len(refs), val[:22], rows[-1]["montagem"]), flush=True)
    jlc = [r for r in rows if r["montagem"].startswith("JLC")]
    ext = sorted({r["lcsc"] for r in jlc if r["classe"] == "Extended"})
    unk = sorted({r["lcsc"] for r in jlc if r["classe"] == "?"})
    summary = {"linhas_jlc": len(jlc), "pecas_jlc": sum(r["qtd"] for r in jlc), "tipos_extended": len(ext), "extended": ext,
               "taxa_extended_usd": round(len(ext) * FEE, 2), "sem_classe": unk}
    csv.DictWriter(open(os.path.join(HERE, "bom_v3.csv"), "w", encoding="utf-8", newline=""), fieldnames=list(rows[0])).writeheader()
    with open(os.path.join(HERE, "bom_v3.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    json.dump({"resumo": summary, "linhas": rows, "descartadas": DROP}, open(os.path.join(HERE, "bom_v3.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
