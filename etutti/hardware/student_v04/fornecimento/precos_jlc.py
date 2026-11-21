"""Student V4 (R2V4, E1/E3): prices and library class of every LCSC code the V3 BOM and the V4 ruler use.

    python etutti/hardware/student_v04/fornecimento/precos_jlc.py

Reads student_v03/bom_v3.csv (read only), asks JLCPCB's parts library (curl, 2 s apart, no bursts) for class, stock and
price tiers, and writes precos_jlc.json (cached: codes already in the file are not asked again).
"""
import csv, json, os, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, "..", "..", "student_v03", "bom_v3.csv"))
OUT = os.path.join(HERE, "precos_jlc.json")
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
EXTRA = ["C5947", "C56123098", "C160405", "C38036", "C225115", "C2687116", "C558442"]


def ask(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10})
    raw = subprocess.run(["curl", "-s", "-f", "--max-time", "60", "-H", "Content-Type: application/json", "-d", body, API],
                         capture_output=True).stdout
    try:
        for p in json.loads(raw.decode("utf-8"))["data"]["componentPageInfo"]["list"] or []:
            if p.get("componentCode") == code:
                return {"classe": {"base": "Basic", "expand": "Extended"}.get(p.get("componentLibraryType"), "?"),
                        "estoque": p.get("stockCount"), "modelo": p.get("componentModelEn"),
                        "tiers": [[x["startNumber"], x["productPrice"]] for x in p.get("componentPrices") or []]}
    except Exception:
        pass
    return None


def main():
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    codes = [r["lcsc"] for r in csv.DictReader(open(V3, encoding="utf-8"))] + EXTRA
    for c in dict.fromkeys(codes):
        if c in cache and cache[c]:
            continue
        cache[c] = ask(c)
        time.sleep(2)
        print(c, cache[c] and (cache[c]["classe"], cache[c]["tiers"][:2]))
    json.dump(cache, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
