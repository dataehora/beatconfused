"""Liebling (R3MIC, E1): consulta a biblioteca de pecas da JLCPCB (curl, 2 s entre pedidos, sem rajada).

    python minimic/pcb/consulta_jlc.py "IM72D128" "RP2040" ...

Imprime codigo LCSC, modelo, encapsulamento, classe (Basic/Extended), estoque e faixas de preco.
Grava o resultado bruto em minimic/pcb/build/consulta_jlc.json (so leitura de preco; nada e comprado).
"""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "consulta_jlc.json")
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def ask(kw, n=10):
    body = json.dumps({"keyword": kw, "currentPage": 1, "pageSize": n})
    raw = subprocess.run(["curl", "-s", "--max-time", "60", "-H", "Content-Type: application/json", "-d", body, API],
                         capture_output=True).stdout
    try:
        lst = json.loads(raw.decode("utf-8"))["data"]["componentPageInfo"]["list"] or []
    except Exception as e:
        return {"erro": str(e), "bruto": raw[:200].decode("utf-8", "replace")}
    return [{"codigo": p.get("componentCode"), "modelo": p.get("componentModelEn"), "marca": p.get("componentBrandEn"),
             "pacote": p.get("componentSpecificationEn"), "classe": {"base": "Basic", "expand": "Extended"}.get(p.get("componentLibraryType"), p.get("componentLibraryType")),
             "estoque": p.get("stockCount"), "montagem": p.get("assemblyProcess"),
             "tiers": [[x["startNumber"], x["productPrice"]] for x in p.get("componentPrices") or []]} for p in lst]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    for kw in sys.argv[1:]:
        r = ask(kw)
        res[kw] = r
        print("==", kw)
        if isinstance(r, dict):
            print("  ", r)
        for p in r if isinstance(r, list) else []:
            print("  ", p["codigo"], p["modelo"], "|", p["pacote"], "|", p["classe"], "| estoque", p["estoque"], "|", p["tiers"][:4])
        time.sleep(2)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
