"""Student V4 (R11V4, item 3/4): cost of each ruler variant's JLCPCB order (R8, R8E, R4, R4E). Stdlib; writes custo_r11.json.

    python etutti/hardware/student_v04/pcb/regua/custo_r11.py

Same assumptions as custo_r10.py: LCSC price tiers of fornecimento/precos_jlc.json (low = tier at the order's quantity, high = 1 piece); the PCB price
is an ESTIMATE per area (US$ 0.0135-0.032 per cm2 and panel, 5 panels; x1.0-1.5 above 100 x 100 mm, not quoted); fixed items of the assembly order
(preparation 8.24 + stencil 1.55 + 3.09 per Extended type + SMT 3.2) as in ELETRONICA E3. 5 bare panels minimum, 2 assembled panels minimum.
One order = one variant (the JLCPCB assembles every board of an order alike): that is why R8 and R8E are two orders from the same Gerbers.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", ".."))
P = json.load(open(os.path.join(HW, "fornecimento", "precos_jlc.json"), encoding="utf-8"))
RATE, ABOVE = (0.0135, 0.032), (1.0, 1.5)


def tier(code, qty):
    best = P[code]["tiers"][0][1]
    for q, p in P[code]["tiers"]:
        if qty >= q:
            best = p
    return best


def panel(n, L, rail=5.0, gap=2.0):
    w = rail + gap + (L - 0.4) + gap + rail
    h = rail + gap + n * 14 + (n - 1) * gap + gap + rail
    return round(w, 1), round(h, 1), round(w * h / 100, 1)


def parts(sens, conn, r330, rulers):
    n = {"C22401868": sens, "C730243": 1, "C160405": conn, "C1525": sens + 1, "C15850": 1, "C25104": r330}
    low = sum(tier(c, k * rulers) * k * rulers for c, k in n.items() if k)
    high = sum(P[c]["tiers"][0][1] * k * rulers for c, k in n.items() if k)
    return round(low, 2), round(high, 2)


FIXED = round(8.24 + 1.55 + 3 * 3.09 + 3.2, 2)
out = {"fixo_montagem_USD": FIXED, "variantes": {}}
for name, sens, L, out_on, per in (("R8", 8, 148.0, False, 2), ("R8E", 8, 148.0, True, 2), ("R8 (painel de 4)", 8, 148.0, False, 4),
                                   ("R8E (painel de 4)", 8, 148.0, True, 4), ("R4", 4, 74.0, False, 5), ("R4E", 4, 74.0, True, 5)):
    w, h, a = panel(per, L)
    over = w > 100 or h > 100
    rulers = 2 * per                                   # 2 assembled panels
    pc = parts(sens, 2 if out_on else 1, 1 if out_on else 0, rulers)
    f = ABOVE if over else (1.0, 1.0)
    pcb = (round(5 * a * RATE[0] * f[0], 1), round(5 * a * RATE[1] * f[1], 1))
    tot = (round(pc[0] + pcb[0] + FIXED, 1), round(pc[1] + pcb[1] + FIXED, 1))
    one = tuple(round(x / rulers, 2) for x in tot)
    out["variantes"][name] = {"painel_mm": [w, h], "cm2": a, "reguas_montadas": rulers, "pecas_USD": pc, "pcb_USD": pcb,
                              "fixo_USD": FIXED, "pedido_USD": tot, "por_regua_montada_USD": one}
    print("%-20s %5.1f x %4.1f  %3d reguas  pecas %s  pcb %s  pedido %s  por regua %s" % (name, w, h, rulers, pc, pcb, tot, one))
# the part that OUT costs on one ruler
d = tier("C160405", 8) + tier("C25104", 8)
out["custo_do_OUT_por_regua_USD"] = round(d, 3)
json.dump(out, open(os.path.join(HERE, "custo_r11.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("OUT (J2 + R1) por regua: US$ %.3f" % d)
