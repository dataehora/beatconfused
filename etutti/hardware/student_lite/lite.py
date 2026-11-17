"""eTutti Student Lite: fabrication files for JLCPCB assembly of the BOTTOM side only.

    python etutti/hardware/student_lite/lite.py

Same board as the Student V2 (nothing in the Gerbers changes). Only the pick-and-place and the BOM
differ: every top-side part is left out and soldered at home (the encoders with their knobs, USB-C,
the two jacks, the ESD chip and TVS diode, 5 small passives). J401 (the screen's connector) is left
out altogether: the Lite has no screen.
Writes fab/student_lite_bom.csv, _cpl.csv, _montar_em_casa.csv, student_lite_gerbers.zip (a copy of
the V2's) and fab.json.
"""
import csv
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
V2F = os.path.normpath(os.path.join(HERE, "..", "student_v02", "fab"))
FAB = os.path.join(HERE, "fab")
NO_FIT = {"J401": "conector da tela: o Lite não tem tela"}
# Extended -> Basic swaps (same 0402 footprint, so the CPL and the board do not change). JLCPCB charges
# US$ 3.09 per Extended part type (quote of 18 Nov 2026); every type removed saves that.
#   R203 1.8k -> 2.2k : BQ24074 ICHG = 890/R = 0.49 A -> 0.405 A (0.4 C for the 1000 mAh cell)
#   R501 680k -> 1M   : MAX98357A SD_MODE = 3.3 V x 100k/(100k+R): 0.42 V -> 0.30 V (mono window 0.16-0.77 V)
#   C307 150nF -> 100nF: SGTL5000 datasheet (Freescale, Figures 19 and 20): VAG pin = 0.1 uF
SUBS = {
    "R203": ("2.2k", "C25879", "BQ24074: corrente de carga 0,49 A -> 0,405 A"),
    "R501": ("1M", "C26083", "MAX98357A SD_MODE 0,42 V -> 0,30 V (janela mono 0,16-0,77 V)"),
    "C307": ("100nF", "C1525", "SGTL5000: o datasheet pede 0,1 uF no VAG"),
}
# H101 (Wurth SMT standoff): refused by the Economic PCBA, so it is soldered at home (or, from the V3,
# replaced by a plain hole + screw + spacer).
HOME_ONLY = {"H101": "espaçador SMD M2.5 do módulo (Würth 9774025151R): a econômica não o aceita"}
# Extended types in the JLCPCB quote of 18 Nov 2026 (BOM of the bottom side): 16 types x US$ 3.09 = US$ 49.44
EXTENDED = {"C162182", "C134405", "C48985906", "C265101", "C167825", "C25871", "C4131", "C54313", "C7666", "C28060",
            "C2651833", "C347373", "C910544", "C179326", "C7827", "C22401868"}
WHY = {
    "SW401": "encoder do volume (EC11E18244AU), furo passante",
    "SW402": "encoder do registro (EC11E18244AU), furo passante",
    "J201": "USB-C (16 pinos, 4 de fixação)",
    "J301": "jack OUT 3,5 mm (PJ-327A)", "J302": "jack IN 3,5 mm (PJ-327A)",
    "H101": "espaçador SMD M2.5 do módulo MicroMod (antes do módulo)",
    "U201": "proteção ESD do USB (SOT-23-6)", "D201": "diodo TVS de 5 V (SOD-123F)",
    "C210": "10 µF 0603", "C308": "100 nF 0402", "R303": "100 kΩ 0402", "R304": "1 MΩ 0402",
}


def main():
    os.makedirs(FAB, exist_ok=True)
    cpl = list(csv.reader(open(os.path.join(V2F, "student_v02_cpl.csv"), encoding="utf-8")))
    head, rows = cpl[0], cpl[1:]
    bottom = [r for r in rows if r[6] == "Bottom"]
    top = [r for r in rows if (r[6] == "Top" and r[0] not in NO_FIT) or r[0] in HOME_ONLY]
    keep = {r[0] for r in bottom}
    csv.writer(open(os.path.join(FAB, "student_lite_cpl.csv"), "w", encoding="utf-8", newline="")).writerows([head] + bottom)

    bom = list(csv.reader(open(os.path.join(V2F, "student_v02_bom.csv"), encoding="utf-8")))
    per, top_codes = [], {}
    for r in bom[1:]:
        for x in r[1].split(","):
            if x in HOME_ONLY or x not in keep:
                top_codes[x] = (r[3], r[0], r[2])
            else:
                c, v = (SUBS[x][1], SUBS[x][0]) if x in SUBS else (r[3], r[0])
                per.append((x, v, r[2], c))
    groups = {}
    for x, v, fp, c in per:
        groups.setdefault((c, v, fp), []).append(x)
    out = [bom[0]] + [[v, ",".join(refs), fp, c] for (c, v, fp), refs in groups.items()]
    csv.writer(open(os.path.join(FAB, "student_lite_bom.csv"), "w", encoding="utf-8", newline="")).writerows(out)
    # CPL: bottom parts that the Lite assembles (H101 is soldered at home)
    bottom = [r for r in bottom if r[0] not in HOME_ONLY]
    csv.writer(open(os.path.join(FAB, "student_lite_cpl.csv"), "w", encoding="utf-8", newline="")).writerows([head] + bottom)

    home = [["referencia", "valor", "pacote", "codigo LCSC", "o que e"]]
    for r in sorted(top, key=lambda r: r[0]):
        c, v, p = top_codes[r[0]]
        home.append([r[0], v, p, c, WHY.get(r[0], "")])
    csv.writer(open(os.path.join(FAB, "student_lite_montar_em_casa.csv"), "w", encoding="utf-8", newline="")).writerows(home)
    shutil.copyfile(os.path.join(V2F, "student_v02_gerbers.zip"), os.path.join(FAB, "student_lite_gerbers.zip"))

    rec = {"pecas_jlc": len(bottom), "linhas_bom_jlc": len(out) - 1, "pecas_em_casa": len(top),
           "linhas_bom_v2": len(bom) - 1, "em_casa": [r[0] for r in home[1:]],
           "codigos_em_casa": sorted({r[3] for r in home[1:]}), "fora": NO_FIT, "trocas_basic": {k: list(v) for k, v in SUBS.items()},
           "tipos_extendidos_jlc": sorted(c for c in {g[0] for g in groups} if c in EXTENDED)}
    rec["n_extendidos_jlc"] = len(rec["tipos_extendidos_jlc"])
    json.dump(rec, open(os.path.join(HERE, "fab.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
