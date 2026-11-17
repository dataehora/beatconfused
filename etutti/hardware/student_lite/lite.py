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
WHY = {
    "SW401": "encoder do volume (EC11E18244AU), furo passante",
    "SW402": "encoder do registro (EC11E18244AU), furo passante",
    "J201": "USB-C (16 pinos, 4 de fixação)",
    "J301": "jack OUT 3,5 mm (PJ-327A)", "J302": "jack IN 3,5 mm (PJ-327A)",
    "U201": "proteção ESD do USB (SOT-23-6)", "D201": "diodo TVS de 5 V (SOD-123F)",
    "C210": "10 µF 0603", "C308": "100 nF 0402", "R303": "100 kΩ 0402", "R304": "1 MΩ 0402",
}


def main():
    os.makedirs(FAB, exist_ok=True)
    cpl = list(csv.reader(open(os.path.join(V2F, "student_v02_cpl.csv"), encoding="utf-8")))
    head, rows = cpl[0], cpl[1:]
    bottom = [r for r in rows if r[6] == "Bottom"]
    top = [r for r in rows if r[6] == "Top" and r[0] not in NO_FIT]
    keep = {r[0] for r in bottom}
    csv.writer(open(os.path.join(FAB, "student_lite_cpl.csv"), "w", encoding="utf-8", newline="")).writerows([head] + bottom)

    bom = list(csv.reader(open(os.path.join(V2F, "student_v02_bom.csv"), encoding="utf-8")))
    out, top_codes = [bom[0]], {}
    for r in bom[1:]:
        refs = r[1].split(",")
        k = [x for x in refs if x in keep]
        t = [x for x in refs if x not in keep]
        if k:
            out.append([r[0], ",".join(k), r[2], r[3]])
        if t:
            top_codes[r[3]] = (r[0], t, r[2])
    csv.writer(open(os.path.join(FAB, "student_lite_bom.csv"), "w", encoding="utf-8", newline="")).writerows(out)

    home = [["referencia", "valor", "pacote", "codigo LCSC", "o que e"]]
    code_of = {x: (c, v, p) for c, (v, rs, p) in top_codes.items() for x in rs}
    for r in sorted(top, key=lambda r: r[0]):
        c, v, p = code_of[r[0]]
        home.append([r[0], v, p, c, WHY.get(r[0], "")])
    csv.writer(open(os.path.join(FAB, "student_lite_montar_em_casa.csv"), "w", encoding="utf-8", newline="")).writerows(home)
    shutil.copyfile(os.path.join(V2F, "student_v02_gerbers.zip"), os.path.join(FAB, "student_lite_gerbers.zip"))

    rec = {"pecas_jlc": len(bottom), "linhas_bom_jlc": len(out) - 1, "pecas_em_casa": len(top),
           "linhas_bom_v2": len(bom) - 1, "em_casa": [r[0] for r in home[1:]],
           "codigos_em_casa": sorted({r[3] for r in home[1:]}), "fora": NO_FIT}
    json.dump(rec, open(os.path.join(HERE, "fab.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
