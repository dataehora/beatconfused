"""eTutti Student V3: audit of every chip's pin-out against the symbol of the real LCSC part.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/auditoria_pinos.py

For every part of the V2 board that has an LCSC code, reads the pin number -> pin name table of the
EasyEDA symbol of THAT code (the cached JSON in student_v01/fornecimento/easyeda and
student_v02/fornecimento/easyeda: the symbol of the part JLCPCB will actually place) and puts it next
to the net our board has on the same pad number. A person (or a heuristic below) reads the table:
a supply pin on a signal net, or a signal pin on a supply, is a mistake. Writes pcb/auditoria_pinos.json
and prints one table per part.
"""
import collections
import csv
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
V2 = os.path.join(HW, "student_v02")
BOARD = os.path.join(V2, "kicad", "student_v02.kicad_pcb")
CACHES = [os.path.join(HW, "student_v01", "fornecimento", "easyeda"), os.path.join(V2, "fornecimento", "easyeda")]


def symbol_pins(code):
    for c in CACHES:
        p = os.path.join(c, code + ".json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))["result"]
            pins = collections.defaultdict(list)
            for s in d["dataStr"]["shape"]:
                if s.startswith("P~"):
                    seg = s.split("^^")
                    num = seg[0].split("~")[3]
                    name = seg[3].split("~")[4]
                    pins[num].append(name)
            return d.get("title"), {k: "/".join(v) for k, v in pins.items()}
    return None, None


def main():
    codes = {}
    for r in csv.DictReader(open(os.path.join(V2, "fab", "student_v02_bom.csv"), encoding="utf-8")):
        for ref in r["Designator"].split(","):
            codes[ref] = (r["Comment"], r["LCSC Part #"])
    b = pcbnew.LoadBoard(BOARD)
    out = {}
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if ref not in codes or not ref[0] in "UQDJSL" or ref.startswith(("U7", "H", "HG")):
            continue
        val, code = codes[ref]
        title, pins = symbol_pins(code)
        nets = collections.defaultdict(set)
        for pad in fp.Pads():
            nets[pad.GetNumber()].add(pad.GetNetname() or "-")
        rows = []
        for n in sorted(set(nets) | set(pins or {}), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x)):
            rows.append((n, (pins or {}).get(n, "?"), "/".join(sorted(nets.get(n, {"(sem pad)"})))))
        out[ref] = {"valor": val, "lcsc": code, "titulo": title, "pinos": rows}
    # one TMAG as the representative of the 28
    json.dump(out, open(os.path.join(HERE, "auditoria_pinos.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for ref, d in out.items():
        print("\n== %s  %s  %s  | %s" % (ref, d["valor"], d["lcsc"], d["titulo"]))
        for n, name, net in d["pinos"]:
            print("   %-4s %-26s %s" % (n, name[:26], net))


if __name__ == "__main__":
    main()
