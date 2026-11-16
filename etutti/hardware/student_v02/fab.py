"""eTutti Student V2: fabrication files of the board (after pcb/build_board.py ended clean).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v02/fab.py

Uses the J1's export functions (viaggio_j1/m3.py: Gerbers + drill zip, BOM, pictures) and the
Student V1's CPL method (student_v01/fornecimento/cpl_jlc.py: position and rotation worked out
from the pads of the EasyEDA footprint of each LCSC code). Neither folder is written: the pads
read so far are copied to fornecimento/easyeda_pads.json here, and new codes are added to it.

Writes fab/student_v02_gerbers.zip, _bom.csv, _cpl.csv, _fora_da_montagem.csv, _top.png,
_bottom.png and fab.json. Parts marked "nao montar" (the V1's charge-light driver) are left
out of the BOM and the CPL.
"""
import csv
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J1 = os.path.normpath(os.path.join(HERE, "..", "viaggio_j1"))
V1F = os.path.normpath(os.path.join(HERE, "..", "student_v01", "fornecimento"))
KICAD = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "pcb", "build")
FAB = os.path.join(HERE, "fab")
FORN = os.path.join(HERE, "fornecimento")
NAME = "student_v02"
BOARD = os.path.join(KICAD, NAME + ".kicad_pcb")

sys.path.insert(0, J1)
sys.path.insert(0, V1F)
import pcbnew      # noqa: E402
import m3          # noqa: E402
import cpl_jlc     # noqa: E402

HOME = [
    ["MOD1", "SparkFun MicroMod Teensy (DEV-16402)", "em casa: encaixar no J101"],
    ["SCR1", "parafuso M2.5 x 3 (kit SparkFun)", "em casa: prende o modulo no H101"],
    ["DS1", "modulo OLED 0,96 pol. 128 x 64 SSD1306 I2C, 4 pinos", "em casa: preso na tampa, cabo JST SH de 4 vias ao J401"],
    ["A2", "alto-falante 28 x 5 mm, 8 ohm, 2 W", "em casa: na caixa acustica, fios soldados no J501"],
    ["BAT", "LiPo 1S 503450 ~1000 mAh com NTC (3 fios)", "em casa: no J202"],
    ["SW1-SW28", "28 teclas Gateron KS-20 magneticas", "em casa: encaixadas na placa (sem plate), presas pela grade"],
]


def main():
    for d in (FAB, FORN, BUILD):
        os.makedirs(d, exist_ok=True)
    m3.BOARD, m3.BUILD, m3.FAB = BOARD, BUILD, FAB
    b = pcbnew.LoadBoard(BOARD)
    dnp = sorted(fp.GetReference() for fp in b.GetFootprints()
                 if fp.IsDNP() or (fp.HasField("Montagem") and fp.GetFieldText("Montagem") == "nao montar"))
    rec = {"nao_montar": dnp}
    z, files = m3.gerbers(BOARD, NAME, m3.GERBER_LAYERS)
    rec["gerbers"] = {"zip": os.path.basename(z), "arquivos": files}
    rec.update(m3.bom_cpl(b))
    for kind in ("bom", "cpl", "fora_da_montagem"):
        os.replace(os.path.join(FAB, "viaggio_j1_%s.csv" % kind), os.path.join(FAB, "%s_%s.csv" % (NAME, kind)))
    # BOM without the parts that are not fitted
    bom = os.path.join(FAB, NAME + "_bom.csv")
    rows = list(csv.reader(open(bom, encoding="utf-8")))
    out = [rows[0]]
    for r in rows[1:]:
        refs = [x for x in r[1].split(",") if x not in dnp]
        if refs:
            out.append([r[0], ",".join(refs), r[2], r[3]])
    csv.writer(open(bom, "w", encoding="utf-8", newline="")).writerows(out)
    rec["bom_linhas"] = len(out) - 1
    fora = os.path.join(FAB, NAME + "_fora_da_montagem.csv")
    rows = [r for r in csv.reader(open(fora, encoding="utf-8"))][1:]
    rows = [r for r in rows if r[0] not in ("MOD1", "SCR1", "PLATE", "A2", "BAT")]
    w = csv.writer(open(fora, "w", encoding="utf-8", newline=""))
    w.writerow(["referencia", "peca", "por que"])
    w.writerows(rows + [[r, "(footprint na placa)", "nao montar: acionador da luz de carga da V1, sem LED na V2"] for r in dnp] + HOME)
    rec["fora"] = [r[0] for r in rows] + dnp

    # CPL from the pads
    pads = os.path.join(FORN, "easyeda_pads.json")
    if not os.path.exists(pads):
        shutil.copyfile(os.path.join(V1F, "easyeda_pads.json"), pads)
    shutil.copyfile(os.path.join(FAB, NAME + "_cpl.csv"), os.path.join(FORN, "cpl_por_tabela.csv"))
    cpl_jlc.HERE, cpl_jlc.BOARD, cpl_jlc.PADS = FORN, BOARD, pads
    cpl_jlc.CACHE, cpl_jlc.CPL = os.path.join(FORN, "easyeda"), os.path.join(FAB, NAME + "_cpl.csv")
    os.replace(os.path.join(FORN, "cpl_por_tabela.csv"), os.path.join(FORN, "cpl_antigo.csv"))
    try:
        cpl_jlc.main()
    except SystemExit as e:
        if e.code:
            raise
    cpl = os.path.join(FAB, NAME + "_cpl.csv")
    rows = list(csv.reader(open(cpl, encoding="utf-8")))
    rows = [rows[0]] + [r for r in rows[1:] if r[0] not in dnp]
    csv.writer(open(cpl, "w", encoding="utf-8", newline="")).writerows(rows)
    rec["cpl"] = {"pecas": len(rows) - 1, "cima": sum(1 for r in rows[1:] if r[6] == "Top"),
                  "baixo": sum(1 for r in rows[1:] if r[6] == "Bottom")}
    rec["imagens"] = m3.renders(BOARD, NAME)
    json.dump(rec, open(os.path.join(HERE, "fab.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
