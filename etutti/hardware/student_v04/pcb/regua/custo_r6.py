"""Student V4 (R6V4, item 3): linking cost of the ruler chain, 32/48/64/80 keys, option G (E2 bridge + pigtail) vs D (R5V4). Stdlib.

    python etutti/hardware/student_v04/pcb/regua/custo_r6.py     (writes custo_r6.json)
Prices: JLCPCB parts library 21 nov (1 pc), Pololu #5543 3.32, Extended fee 3.09 per type per order. Estimates are marked.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SOCK, SH, MALE, EXT = 0.1152, 0.069, 0.0192, 3.09
POLOLU = 3.32
CRIMP_TOOL, CRIMP_PARTS, WIRE = 30.0, 0.6, 4.0          # D (R5V4)
out = {}
for keys in (32, 48, 64, 80):
    n = keys // 16                                       # rulers per row
    rulers, assembled = 4 * n, max(10, 5 * ((4 * n + 4) // 5))   # minimum order: 10 rulers = 2 panels
    bridges = 4 * (n - 1)
    entry = 4
    # G: sockets replace the SH on the ruler (no change in the number of Extended types: SH out, socket in); the male type is +1
    d_sock = 2 * assembled * (SOCK - SH)
    male_parts = (2 * (bridges + 4) + entry + 4) * MALE   # bridges + spare, entry plugs + spare
    ext = EXT                                             # +1 type (C55213903) on the ruler order
    pigtails = 2 * POLOLU                                 # 2 cables -> 4 pigtails (+2 more cables per extra 4 rows: none)
    # panel: bridges ride on spare strips of the ruler panel; 80 keys has no spare strip -> one more 5-strip panel (estimate 6-12)
    spare_strips = assembled - rulers
    strips_needed = -(-bridges // 8)                      # 8 bridges per 73.6 x 14 strip (est.)
    extra_panel = 0.0 if strips_needed <= spare_strips else 9.0
    G = d_sock + male_parts + ext + pigtails + extra_panel
    D = 4 * CRIMP_PARTS + CRIMP_TOOL + WIRE
    D_sem_ferr = 4 * CRIMP_PARTS + WIRE
    out[keys] = {"reguas": rulers, "pontes": bridges, "pigtails": entry, "montadas_no_pedido": assembled, "tiras_sobrando": spare_strips,
                 "G_USD": round(G, 2), "G_detalhe": {"fêmeas a mais": round(d_sock, 2), "machos": round(male_parts, 2), "tipo Extended novo": ext,
                 "2 cabos SH 100 mm": pigtails, "painel extra (est.)": extra_panel},
                 "D_USD": round(D, 2), "D_sem_ferramenta_USD": round(D_sem_ferr, 2), "G_menos_D": round(G - D, 2),
                 "juntas_de_solda_G": 5 * entry, "juntas_de_solda_D": 10 * (4 * (n - 1)),
                 "tipos_extended_reguas": "TMAG + fêmea 1x5 + 595 + macho = 4 (era 3; D: 3)"}
json.dump(out, open(os.path.join(HERE, "custo_r6.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in out.items():
    print(k, v["G_USD"], "D", v["D_USD"], "diff", v["G_menos_D"], "juntas G/D", v["juntas_de_solda_G"], v["juntas_de_solda_D"], "tiras sobrando", v["tiras_sobrando"])
