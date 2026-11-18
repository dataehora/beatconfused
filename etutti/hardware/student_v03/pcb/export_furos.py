"""KiCad python: writes pcb/furos.json (the case's fixing holes, read from the V3 board) and pcb/footprints.json
(every footprint: place, courtyard, height field; for the case's fit check and renders)."""
import json
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "kicad", "student_v03.kicad_pcb")
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(BOARD)
pos = {fp.GetReference(): [round(MM(fp.GetPosition().x), 3), round(MM(fp.GetPosition().y), 3)] for fp in b.GetFootprints()}
furos = {"tampa": {r: pos[r] for r in ("H1", "H2", "H3", "H4", "H9", "H10")},
         "grade": {"HG%d" % i: pos["HG%d" % i] for i in range(1, 11)},
         "pinos da base": {r: pos[r] for r in ("H5", "H6", "H7", "H8")},
         "modulo (H101)": pos["H101"]}
json.dump({"furos": furos}, open(os.path.join(HERE, "furos.json"), "w"), indent=1)
print(furos)
