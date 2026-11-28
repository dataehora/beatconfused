"""Liebling (R3MIC, E2): custo de pecas por placa a 10 e 100 un., montagem Economic JLCPCB.

    python minimic/pcb/custo_e2.py

Le a biblioteca de pecas da JLCPCB (curl, 2 s entre pedidos; resultados em build/custo_e2_cache.json, so lê codigos
que ainda nao estao no cache), calcula pelo preco por faixa do pedido total (qtd por placa x N) e escreve
build/custo_e2.json e build/custo_e2.md. Nada e comprado: so consulta de preco.

Convencao de numeros: "loja" = biblioteca JLCPCB/LCSC no dia da consulta; "conta" = calculo deste script;
"estimativa" = sem cotacao (placa, SMT, taxas).
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import consulta_jlc as jlc

BUILD = os.path.join(HERE, "build")
CACHE = os.path.join(BUILD, "custo_e2_cache.json")

EXT_FEE = 3.09          # US$ por tipo Extended por pedido (cotacao de 18 nov, V3)
SETUP = 8.24            # montagem Economic, preparacao (cotacao de 18 nov)
STENCIL = 1.55          # estencil (cotacao de 18 nov)
SMT_MIN = 3.20          # "SMT e nitrogenio" da cotacao da V3
JOINT = 0.0017          # US$ por junta (estimativa: valor lembrado da tabela JLCPCB, nao conferido)

# (ref, descricao, codigo LCSC, qtd por placa)
BOM = [
    ("MK1-2", "IM72D128VV01 (microfone PDM, 11 Hz)", "C36405960", 2),
    ("U1", "RP2040 (QFN-56 7x7)", "C2040", 1),
    ("U2", "W25Q16JVSNIQ (flash QSPI 16 Mbit, SOIC-8)", "C2456211", 1),
    ("Y1", "12 MHz 3225 (YXC X322512MSB4SI)", "C9002", 1),
    ("U3", "XC6206P332MR (LDO 3,3 V, SOT-23)", "C5446", 1),
    ("J1", "plugue USB-C macho JXTCONN TYPE-C-MBB008 (24P, placa 0,8 mm)", "C53432944", 1),
    ("SW1-2", "tatil SMD TS-1187A-B-A-B (5,1x5,1x1,5)", "C318884", 2),
    ("D1-15", "LED 0603 branco KT-0603W", "C2290", 15),
    ("D16-21", "LED 0805 verde KT-0805G", "C2297", 6),
    ("D22-24", "LED 0805 amarelo KT-0805Y", "C2296", 3),
    ("D25-26", "LED 0805 vermelho NCD0805R1", "C84256", 2),
    ("D27", "LED 1206 azul KT-1206B (SAT)", "C72691", 1),
    ("R-led", "0402 330 ohm (medidor 12x)", "C25104", 12),
    ("R-cp", "0402 1 kohm (charlieplex 5x, cristal 1x)", "C11702", 6),
    ("R-pu", "0402 10 kohm (CS flash, RUN)", "C25744", 2),
    ("R-cc", "0402 5,1 kohm (CC do plugue)", "C25905", 1),
    ("R-mic", "0402 22 ohm (filtro RC dos microfones)", "C25092", 1),
    ("R-usb", "0402 27 ohm (serie D+ D-)", "C25100", 2),
    ("C-100n", "0402 100 nF", "C1525", 12),
    ("C-1u", "0402 1 uF", "C52923", 4),
    ("C-10u", "0603 10 uF", "C19702", 3),
    ("C-xt", "0402 22 pF (cristal)", "C1555", 2),
]
OPCOES = {
    "V01 no lugar do VV01 (estoque na JLCPCB)": [("MK1-2", "IM72D128V01 (20 Hz)", "C5119248", 2)],
    "plugue MAB169 (16P) no lugar do MBB008": [("J1", "JXTCONN TYPE-C-MAB169 (16P, placa 0,8 mm)", "C53432943", 1)],
    "ESD USBLC6-2SC6 (a mais)": [("U4", "USBLC6-2SC6", "C2687116", 1)],
    "flash Basic W25Q128JVSIQ no lugar da W25Q16": [("U2", "W25Q128JVSIQ (Basic, 128 Mbit)", "C97521", 1)],
    "LDO TLV75533 (Extended)": [("U3", "TLV75533PDBVR", "C404027", 1)],
}


def load():
    return json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(codes):
    cache = load()
    for c in codes:
        if c in cache and cache[c]:
            continue
        r = jlc.ask(c, 10)
        hit = [p for p in r if isinstance(r, list) and p["codigo"] == c]
        cache[c] = hit[0] if hit else None
        print(c, cache[c] and (cache[c]["modelo"], cache[c]["classe"], cache[c]["estoque"]), flush=True)
        time.sleep(2)
        os.makedirs(BUILD, exist_ok=True)
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return cache


def unit(tiers, qty):
    p = tiers[0][1]
    for start, price in tiers:
        if qty >= start:
            p = price
    return p


def custo(lines, cache, n):
    rows, parts, ext = [], 0.0, set()
    for ref, desc, code, q in lines:
        d = cache[code]
        u = unit(d["tiers"], q * n)
        rows.append((ref, desc, code, q, d["classe"], d["estoque"], u, u * q))
        parts += u * q
        if d["classe"] != "Basic":
            ext.add(code)
    return rows, parts, ext


def aplica(opcao):
    lines = {l[0]: l for l in BOM}
    for l in OPCOES[opcao]:
        lines[l[0]] = l
    return list(lines.values())


def resumo(lines, cache, n, juntas=290):
    rows, parts, ext = custo(lines, cache, n)
    fixo = SETUP + STENCIL + EXT_FEE * len(ext) + max(SMT_MIN, JOINT * juntas * n)
    return rows, parts, len(ext), fixo, parts + fixo / n


def main():
    codes = [l[2] for l in BOM] + [l[2] for o in OPCOES.values() for l in o]
    cache = fetch(dict.fromkeys(codes))
    out, md = {}, []
    for n in (10, 100):
        rows, parts, next, fixo, tot = resumo(BOM, cache, n)
        out[n] = {"pecas_por_placa": parts, "tipos_extended": next, "fixo_pedido": fixo, "por_placa_sem_pcb": tot}
        md.append(f"### N = {n}\n\n| ref | peca | LCSC | qtd | classe | estoque | US$/un | US$/placa |\n|---|---|---|---|---|---|---|---|")
        for r in rows:
            md.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]:.4f} | {r[7]:.4f} |")
        md.append(f"\npecas por placa **{parts:.2f}**; tipos Extended **{next}** (x {EXT_FEE} = {EXT_FEE*next:.2f}); "
                  f"fixo do pedido {fixo:.2f} (preparacao {SETUP} + estencil {STENCIL} + Extended + SMT); "
                  f"**por placa sem PCB: {tot:.2f}**\n")
    md.append("### Opcoes (delta por placa em relacao ao basico, N = 10 e 100)\n\n| opcao | N=10 | N=100 |\n|---|---|---|")
    for o in OPCOES:
        cel = []
        for n in (10, 100):
            base = resumo(BOM, cache, n)[4]
            alt = resumo(aplica(o), cache, n)[4] if o not in ("ESD USBLC6-2SC6 (a mais)",) else resumo(BOM + OPCOES[o], cache, n)[4]
            cel.append(f"{alt - base:+.2f}")
        md.append(f"| {o} | {cel[0]} | {cel[1]} |")
    open(os.path.join(BUILD, "custo_e2.md"), "w", encoding="utf-8").write("\n".join(md))
    json.dump(out, open(os.path.join(BUILD, "custo_e2.json"), "w"), indent=1)
    print("\n".join(md))


if __name__ == "__main__":
    main()
