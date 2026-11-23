"""eTutti Student V4 (R11V4): BOM and CPL (JLCPCB format) of the four ruler variants, per panel layout.

    REGUA_N=8 "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/regua/pacotes_regua.py
    REGUA_N=4 "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/regua/pacotes_regua.py

One drawing per length (R8 = 8 positions, R4 = 4): the OUT connector J2 and its 330 ohm R1 are on the board; the variants without OUT
(R8, R4) just leave J2 and R1 out of the BOM and the CPL (JLCPCB does not fit what is not listed), the variants with OUT (R8E, R4E) list them.
Positions and rotations of the parts come from cpl_jlc.py's method (EasyEDA footprint pads laid on the board's pads, bottom side mirrored), fitted
on the single placed ruler, then copied to every strip of the panel at the panel's strip offsets (fab_regua.strip_xy). The panel itself
(geometry only, no tracks yet) is written by fab_regua.py with MODO=regua, PAINEL_N = strips per panel.

Writes fab/regua/<variant>_painel<N>/{bom.csv, cpl.csv} and pcb/regua/pacotes_regua_R<N>.json (counts, Extended types).
Nothing is routed here and nothing is ordered: these are the files the roteamento agent's routed boards drop into (positions do not depend on tracks).
"""
import csv
import json
import os
import shutil
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(PCB, ".."))
sys.path.insert(0, PCB)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HW, "..", "student_v01", "fornecimento")))
import posiciona_regua as PR  # noqa: E402
if os.environ.get("REGUA_BOARD"):                     # R11V4: the routed board (posiciona_regua.py rebuilds the unrouted one from scratch: never over a routed board)
    PR.OUT = os.path.abspath(os.environ["REGUA_BOARD"])
import cpl_jlc  # noqa: E402

NPOS = PR.NPOS
SUF = PR.SUF
FORN = os.path.join(HW, "fornecimento")
PADS = os.path.join(FORN, "easyeda_pads.json")
BUILD = PR.BUILD
RAIL, GAP, STRIP_H = 5.0, 2.0, 14.0
OUT_REFS = ("J2", "R1")
LAYOUTS = {8: (2, 4), 4: (5,)}[NPOS]          # strips per panel: R8 target 2, alternative 4; R4 5
NAMES = {8: ("R8", "R8E"), 4: ("R4", "R4E")}[NPOS]


def main():
    if not os.path.exists(PADS):
        shutil.copyfile(os.path.join(HW, "..", "student_v03", "fornecimento", "easyeda_pads.json"), PADS)
    cpl_unit = os.path.join(BUILD, "cpl_unitaria.csv")
    cpl_jlc.HERE, cpl_jlc.BOARD, cpl_jlc.PADS = FORN, PR.OUT, PADS
    cpl_jlc.CACHE, cpl_jlc.CPL = os.path.join(FORN, "easyeda"), cpl_unit
    try:
        cpl_jlc.main()
    except SystemExit as e:
        if e.code:
            raise
    unit = list(csv.DictReader(open(cpl_unit, encoding="utf-8")))
    parts = {p["ref"]: p for p in json.load(open(os.path.join(BUILD, "partes_regua.json"), encoding="utf-8"))}
    summary = {"comprimento": NPOS, "variantes": {}}
    for per in LAYOUTS:
        for var in NAMES:
            with_out = var.endswith("E")
            d = os.path.join(HW, "fab", "regua", "%s_painel%d" % (var, per))
            os.makedirs(d, exist_ok=True)
            rows, bom = [], {}
            for i in range(per):
                sx = RAIL + GAP
                sy = RAIL + GAP + i * (STRIP_H + GAP)
                dx = sx - (PR.OX + PR.U0)
                dy = sy - (PR.OY + PR.VB)
                for r in unit:
                    ref = r["Designator"]
                    if ref in OUT_REFS and not with_out:
                        continue
                    x = float(r["Mid X"][:-2]) + dx
                    y = float(r["Mid Y"][:-2]) - dy           # JLCPCB Y is up, KiCad's is down
                    rows.append(["%s-%d" % (ref, i + 1), r["Val"], r["Package"], "%.4fmm" % x, "%.4fmm" % y, r["Rotation"], "Bottom"])
                    b = bom.setdefault(parts[ref]["lcsc"], {"c": parts[ref]["value"], "fp": r["Package"], "refs": []})
                    b["refs"].append("%s-%d" % (ref, i + 1))
            with open(os.path.join(d, "cpl.csv"), "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
                w.writerows(rows)
            with open(os.path.join(d, "bom.csv"), "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
                for lc, b in sorted(bom.items(), key=lambda kv: kv[1]["refs"][0]):
                    w.writerow([b["c"], ",".join(b["refs"]), b["fp"], lc])
            ext = sorted({lc for lc in bom if parts[[x.rsplit("-", 1)[0] for x in bom[lc]["refs"]][0]]["cls"] == "estendida"})
            summary["variantes"]["%s_painel%d" % (var, per)] = {
                "pecas_por_painel": len(rows), "pecas_por_regua": len(rows) // per, "linhas_bom": len(bom),
                "tipos_extended": ext, "n_extended": len(ext)}
    json.dump(summary, open(os.path.join(HERE, "pacotes_regua_R%d.json" % NPOS), "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
