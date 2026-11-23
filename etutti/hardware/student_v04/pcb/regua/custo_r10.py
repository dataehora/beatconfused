"""Student V4 (R10V4, item 3): 4 x R8 against 8 x R4 for the 32-key instrument. Stdlib; writes pcb/regua/custo_r10.json.

    python etutti/hardware/student_v04/pcb/regua/custo_r10.py

Parts: LCSC price tiers of fornecimento/precos_jlc.json (21-22 nov, JLCPCB parts library), low = tier at the order's quantity, high = 1-piece price.
ESTIMATES (nothing is quoted, nothing is bought): the ruler PCB price per area (derived from the R5V4 estimate US$ 5-12 for 5 panels of 74 cm2) and
a 1.0-1.5 factor for panels above 100 x 100 mm (JLCPCB's cheap tier is 100 x 100; the price above it is by area and was not quoted); the home assembly times.
Rules of the order (as in ELETRONICA E3): 5 bare panels minimum, 2 assembled minimum, preparation 8.24 + stencil 1.55, US$ 3.09 per Extended type,
SMT + nitrogen 3.2; the ruler order has 3 Extended types in both cases, so those fixed items are equal and are shown once.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", ".."))
P = json.load(open(os.path.join(HW, "fornecimento", "precos_jlc.json"), encoding="utf-8"))


def tier(code, qty):
    best = P[code]["tiers"][0][1]
    for q, p in P[code]["tiers"]:
        if qty >= q:
            best = p
    return best


def parts_usd(n_sens, n_595, n_conn, n_100nf, n_10uf, n_330, assembled_rulers, ruler_qty_each=1):
    """Parts cost of `assembled_rulers` rulers; qty drives the tier (low) or 1 piece (high)."""
    q = assembled_rulers
    lines = {"C22401868": n_sens * q, "C730243": n_595 * q, "C160405": n_conn * q, "C1525": n_100nf * q, "C15850": n_10uf * q, "C25104": n_330 * q}
    low = sum(tier(c, n) * n for c, n in lines.items())
    high = sum(P[c]["tiers"][0][1] * n for c, n in lines.items())
    return round(low, 2), round(high, 2)


R4 = dict(n_sens=4, n_595=1, n_conn=2, n_100nf=5, n_10uf=1, n_330=1)
R8 = dict(n_sens=8, n_595=1, n_conn=2, n_100nf=9, n_10uf=1, n_330=1)
RATE = (0.0135, 0.032)        # US$ per cm2 and per panel, 5 panels (derived from US$ 5-12 for 5 x 74 cm2)
ABOVE = (1.0, 1.5)            # factor for panels above 100 x 100 mm (assumption)


def panel(n, L, ruler_w=14.0, rail=5.0, gap=2.0):
    w = rail + gap + (L - 0.4) + gap + rail
    h = rail + gap + n * ruler_w + (n - 1) * gap + gap + rail
    return round(w, 1), round(h, 1), round(w * h / 100.0, 1)


out = {}
# ---- panels
opts = {}
for n in (1, 2, 3, 4):
    w, h, a = panel(n, 148.0)
    pcb = (round(5 * a * RATE[0] * ABOVE[0], 1), round(5 * a * RATE[1] * ABOVE[1], 1))
    opts["R8, %d tira(s) por painel" % n] = {"painel_mm": [w, h], "area_cm2": a, "passa_de_100x100": w > 100 or h > 100,
                                              "R8_por_painel": n, "R8_nos_2_paineis_montados": 2 * n, "lado_menor_que_70": min(w, h) < 70,
                                              "PCB_5_paineis_USD": pcb}
w, h, a = panel(5, 74.0)
opts["R4, 5 tiras por painel (a de hoje)"] = {"painel_mm": [w, h], "area_cm2": a, "passa_de_100x100": False, "R4_por_painel": 5,
                                              "PCB_5_paineis_USD": (round(5 * a * RATE[0], 1), round(5 * a * RATE[1], 1))}
out["paineis"] = opts
# ---- cost: 4 x R8 (2 panels of 2, 4 assembled) | 4 x R8 + 2 spare (3 panels) | 8 x R4 (2 panels of 5, 10 assembled)
rows = {}
w, h, a2 = panel(2, 148.0)
w4, h4, a4 = panel(5, 74.0)
rows["4 x R8 (2 paineis de 2, 4 montadas, sem reserva)"] = dict(
    reguas_montadas=4, pecas=parts_usd(**R8, assembled_rulers=4),
    pcb=(round(5 * a2 * RATE[0] * ABOVE[0], 1), round(5 * a2 * RATE[1] * ABOVE[1], 1)), cabos=(round(4 * 1.206, 2), round(4 * 1.42, 2)), m2=8, plugues=8)
rows["4 x R8 + 2 de reserva (3 paineis de 2, 6 montadas)"] = dict(
    reguas_montadas=6, pecas=parts_usd(**R8, assembled_rulers=6),
    pcb=(round(5 * a2 * RATE[0] * ABOVE[0], 1), round(5 * a2 * RATE[1] * ABOVE[1], 1)), cabos=(round(4 * 1.206, 2), round(4 * 1.42, 2)), m2=8, plugues=8)
rows["8 x R4 (2 paineis de 5, 10 montadas; a R8V4)"] = dict(
    reguas_montadas=10, pecas=parts_usd(**R4, assembled_rulers=10),
    pcb=(round(5 * a4 * RATE[0], 1), round(5 * a4 * RATE[1], 1)), cabos=(round(8 * 1.206, 2), round(8 * 1.42, 2)), m2=11, plugues=16)
for k, r in rows.items():
    r["total_variavel_USD"] = (round(r["pecas"][0] + r["pcb"][0] + r["cabos"][0], 1), round(r["pecas"][1] + r["pcb"][1] + r["cabos"][1], 1))
out["custo_32_teclas"] = rows
base = rows["8 x R4 (2 paineis de 5, 10 montadas; a R8V4)"]["total_variavel_USD"]
for k in list(rows)[:2]:
    r = rows[k]["total_variavel_USD"]
    out["diferenca_contra_8xR4_" + k.split("(")[0].strip().replace(" ", "_")] = (round(r[0] - base[0], 1), round(r[1] - base[1], 1))
# fixed items, equal in both
out["itens_iguais_USD"] = {"preparacao + estencil": 9.79, "3 tipos Extended x 3,09": 9.27, "SMT e nitrogenio": 3.2, "soma": round(9.79 + 9.27 + 3.2, 2)}
# ---- home assembly, estimate (no prototype): minutes
m = {}
for name, nr, nplug, nm2 in (("4 x R8", 4, 8, 8), ("8 x R4", 8, 16, 11)):
    t = nr * 1.0 * (1.5 if name == "4 x R8" else 1.0) + nplug * 0.5 + nm2 * 0.7
    m[name] = round(t, 1)
out["montagem_em_casa_min_(palpite)"] = m
json.dump(out, open(os.path.join(HERE, "custo_r10.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
