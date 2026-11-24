"""Looks parts up in JLCPCB's assembly parts library and on LCSC (plain curl, 2 s apart).

    python etutti/hardware/slim/fornecimento/busca_jlc.py "keyword" ["keyword" ...]   # search by words / part number
    python etutti/hardware/slim/fornecimento/busca_jlc.py -c C15464 [C...]            # LCSC detail of codes

Prints: LCSC code, maker part, package, class (Basic/Extended), JLC stock. With -c also LCSC stock, price, category.
Nothing is bought or ordered.
"""
import json
import subprocess
import sys
import time

JLC = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
LCSC = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=%s"


def curl(args, **kw):
    return subprocess.run(["curl", "-s", "-f", "--max-time", "60"] + args, capture_output=True, **kw).stdout


def jlc(keyword, n=12):
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": n})
    raw = curl(["-H", "Content-Type: application/json", "-d", body, JLC])
    try:
        return json.loads(raw)["data"]["componentPageInfo"]["list"] or []
    except Exception:
        return []


def lcsc(code):
    raw = curl([LCSC % code])
    try:
        return json.loads(raw).get("result") or {}
    except Exception:
        return {}


def main():
    a = sys.argv[1:]
    if a and a[0] == "-c":
        for c in a[1:]:
            r = lcsc(c)
            j = [x for x in jlc(c, 3) if x.get("componentCode") == c]
            print("%-9s %-26s %-22s %-18s LCSC %-7s JLC %-7s %s | US$ %s | %s" % (
                c, (r.get("productModel") or "?")[:26], (r.get("encapStandard") or "")[:22], (r.get("catalogName") or "")[:18],
                r.get("stockNumber", ""), j[0].get("stockCount") if j else "",
                {"base": "Basic", "expand": "Extended"}.get(j[0].get("componentLibraryType")) if j else "-",
                (r.get("productPriceList") or [{}])[0].get("usdPrice"), (r.get("productIntroEn") or "")[:90]), flush=True)
            time.sleep(2)
        return
    for k in a:
        print("== %s" % k)
        for p in jlc(k):
            print("  %-9s %-28s %-24s %-8s stock %-7s %s" % (
                p.get("componentCode"), (p.get("componentModelEn") or "")[:28], (p.get("componentSpecificationEn") or "")[:24],
                {"base": "Basic", "expand": "Extended"}.get(p.get("componentLibraryType"), p.get("componentLibraryType")),
                p.get("stockCount"), (p.get("describe") or p.get("componentName") or "")[:70]), flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
