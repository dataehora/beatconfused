"""KiCad's placement file -> the CPL format JLCPCB's assembly upload reads.

    python jlc.py fab/etuttino_cpl_bottom.csv

kicad-cli writes `Ref,Val,Package,PosX,PosY,Rot,Side`; JLCPCB rejects that
("Failed processing the CPL file") and wants `Designator,Mid X,Mid Y,
Layer,Rotation`, layer as Top/Bottom. build_pcb.py calls cpl() right
after the export; run it by hand to convert an existing file in place.
"""
import csv
import sys


def cpl(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if rows and "Designator" in rows[0]:
        return len(rows)                  # already converted
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        for r in rows:
            w.writerow([r["Ref"], r["Val"], r["Package"], "%.4fmm" % float(r["PosX"]), "%.4fmm" % float(r["PosY"]),
                        "%g" % (float(r["Rot"]) % 360), "Bottom" if r["Side"].lower() == "bottom" else "Top"])
    return len(rows)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, cpl(p), "parts")
