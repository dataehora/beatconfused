"""One-off (R13V4 final adjustments): rewrites rows 14-16, adds the FR-4 ruler grid, and the totals table in fab/COMPRA.md and compra_en.md. Idempotent."""
import os
import re

HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PT = {
    "14": "| 14 | **Parafusos formadores de rosca M2 (PT 2,0)**: **tampa, 15 x M2 x 14** (H1..H4, 5 postes internos, 6 postes de parede); **OLED, 4 x M2 x 4** | 19 (+10 reserva) | idem | cabeça panela, inox ou aço; **reaplicar o parafuso formador de rosca tem limite (5-10 vezes, estimativa)** | US$ 0,04 |",
    "15": "| 15 | **Pés de silicone** (Ø8 x 1,0, colados direto, sem rebaixo) | **6** | Amazon/eBay UK | **dureza 70A ou mais** (mole demais deixa a placa fletir) | ~£3 (estim.) |",
    "16": "| 16 | **MicroMod no H101**: parafuso de **náilon M2,5 x 8** + **porca de náilon M2,5** + **espaçador de náilon de 2,5 mm** | **2 parafusos, 2 porcas, 2 espaçadores** (1 + 1 reserva) | ferragem (Accu, Bolt Base, eBay UK) | o parafuso atravessa **placa 1,2 + espaçador 2,5 + módulo ~1,0 = 4,7 mm** e fecha na porca (~2 mm): 4,7 + 2 = 6,7, então **M2,5 x 8** (x 6 não fecha); **conferir a espessura real do módulo** e que a ponta (1,3 mm além da porca) não toca a base: pedido ao design | centavos (estim.) |",
    "19": "| 19 | **Grade-régua FR-4 1,6 mm** (a grade do teclado: placa nua, sem montagem, sem peças) | **1 painel** (5 é o mínimo da JLCPCB, as demais ficam de reserva) | **JLCPCB**, mesmo carrinho da principal (um frete só) | upload `student_v04_grade_regua_painel_gerbers.zip` (esta pasta, `fab/`; vem de `pcb/grade_fab.py`); **2 camadas, 1,6 mm, FR-4 TG135, HASL sem chumbo, máscara preta fosca, 5 painéis, sem montagem**; **conferir quantas grades cabem num painel** (ver `student_v04_grade_contorno32_gerbers.zip` para a grade de 32 teclas inteira) | US$ 8-15 (**estim.**: placa pequena de 2 camadas + engenharia; não cotado) |",
}
EN = {
    "14": "| 14 | **M2 thread-forming screws (PT 2.0)**: **lid, 15 x M2 x 14** (H1..H4, 5 inner posts, 6 wall posts); **OLED, 4 x M2 x 4** | 19 (+10 spare) | same | pan head, stainless or steel; **re-using a thread-forming screw has a limit (5-10 times, estimate)** | US$ 0.04 |",
    "15": "| 15 | **Silicone feet** (Ø8 x 1.0, stuck on directly, no recess) | **6** | Amazon/eBay UK | **hardness 70A or more** (too soft lets the board flex) | ~£3 (est.) |",
    "16": "| 16 | **MicroMod at H101**: **nylon M2.5 x 8** screw + **nylon M2.5 nut** + **2.5 mm nylon spacer** | **2 screws, 2 nuts, 2 spacers** (1 + 1 spare) | hardware (Accu, Bolt Base, eBay UK) | the screw goes through **board 1.2 + spacer 2.5 + module ~1.0 = 4.7 mm** and closes on the nut (~2 mm): 4.7 + 2 = 6.7, so **M2.5 x 8** (x 6 does not close); **check the module's real thickness** and that the tip (1.3 mm past the nut) does not touch the base: request to the design | pennies (est.) |",
    "19": "| 19 | **1.6 mm FR-4 ruler grid** (the keyboard grid: bare board, no assembly, no parts) | **1 panel** (5 is JLCPCB's minimum, the rest are spares) | **JLCPCB**, same cart as the main board (one shipping) | upload `student_v04_grade_regua_painel_gerbers.zip` (this folder, `fab/`; from `pcb/grade_fab.py`); **2 layers, 1.6 mm, FR-4 TG135, lead-free HASL, matte black mask, 5 panels, no assembly**; **check how many grids fit in a panel** (see `student_v04_grade_contorno32_gerbers.zip` for the whole 32-key grid) | US$ 8-15 (**est.**: small 2-layer board + engineering; not quoted) |",
}
TOT_PT = """| Grupo | Faixa (US$) | Tipo |
|---|---:|---|
| Principal (PCB + montagem, 2 montadas) | 113,4-138,4 | **estim.** (PCB 4 camadas ENIG é suposição; a cotação do J era ~105 antes dos SH originais, +7,0) |
| Réguas 4 x R8 (painel de 2) | 47,3-64,2 | **estim.** (a cotação do J era ~70, +3,3) |
| Grade-régua FR-4 1,6 mm (JLCPCB, item 19) | 8-15 | **estim.** |
| Cabos SH (6) + cabo Qwiic | 8-10 | visto 22 nov |
| OLED Adafruit 326 | 17,5 | visto 22 nov |
| Ferragem (M2 passantes e porcas, PT, M2,5 náilon, pés; itens 12-16) | 6-12 | **estim.** |
| Case MJF (inclui capas, knobs e caixa acústica) | 46-51 | **estim.** (não cotado) |
| Teclas, módulo, bateria, alto-falante, encoders, molas, cabo USB-C (MicroMod ~24 + KS-20 24,5-26,6 + molas 3-8 + bateria 6-10 + alto-falante 7-10 + encoders 4-6 + USB-C 3-8) | 71,5-92,6 | misto: visto 15 nov (módulo, teclas, bateria) e **estim.** |
| **Total (soma das linhas)** | **318-401** | R13V4; a soma das linhas é o número oficial |
"""
TOT_EN = """| Group | Range (US$) | Type |
|---|---:|---|
| Main board (PCB + assembly, 2 assembled) | 113.4-138.4 | **est.** (4-layer ENIG PCB is an assumption; J's quote was ~105 before the original SH, +7.0) |
| 4 x R8 rulers (panel of 2) | 47.3-64.2 | **est.** (J's quote was ~70, +3.3) |
| 1.6 mm FR-4 ruler grid (JLCPCB, item 19) | 8-15 | **est.** |
| SH cables (6) + Qwiic cable | 8-10 | seen 22 Nov |
| Adafruit 326 OLED | 17.5 | seen 22 Nov |
| Hardware (M2 through bolts and nuts, PT, nylon M2.5, feet; items 12-16) | 6-12 | **est.** |
| MJF case (includes caps, knobs and acoustic box) | 46-51 | **est.** (not quoted) |
| Keys, module, battery, speaker, encoders, springs, USB-C cable (MicroMod ~24 + KS-20 24.5-26.6 + springs 3-8 + battery 6-10 + speaker 7-10 + encoders 4-6 + USB-C 3-8) | 71.5-92.6 | mixed: seen 15 Nov (module, keys, battery) and **est.** |
| **Total (sum of the lines)** | **318-401** | R13V4; the sum of the lines is the official number |
"""


def fix(path, rows, tot, anchor_total):
    s = open(path, encoding="utf-8").read()
    lines = s.split("\n")
    out = []
    for ln in lines:
        m = re.match(r"^\| (\d+) \|", ln)
        if m and m.group(1) in ("14", "15", "16"):
            ln = rows[m.group(1)]
        out.append(ln)
    s = "\n".join(out)
    if "| 19 |" not in s:
        s = re.sub(r"(\| 18 \|[^\n]*\n)", lambda m: m.group(1) + rows["19"] + "\n", s, count=1)
    a = s.index(anchor_total)
    a = s.index("| Group" if "Group" in s[a:a + 200] else "| Grupo", a)
    b = s.index("\n\n", a)
    s = s[:a] + tot.rstrip("\n") + s[b:]
    open(path, "w", encoding="utf-8").write(s)


fix(os.path.join(HW, "fab", "COMPRA.md"), PT, TOT_PT, "## 4. Totais")
fix(os.path.join(HW, "compra_en.md"), EN, TOT_EN, "## 4. Totals")
print("ok")
