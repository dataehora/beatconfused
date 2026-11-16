"""Run with KiCad's Python: writes pcb/footprints.json (every footprint of the V2 board: where it
is, its courtyard box, its height field) for the case's fit check and the renders."""
import json
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "kicad", "student_v02.kicad_pcb")
MM = pcbnew.ToMM

b = pcbnew.LoadBoard(BOARD)
out = []
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    flipped = fp.IsFlipped()
    box = fp.GetCourtyard(pcbnew.B_CrtYd if flipped else pcbnew.F_CrtYd).BBox()
    if box.GetWidth() <= 0:
        box = fp.GetBoundingBox(False)
    h = fp.GetFieldText("Altura_mm") if fp.HasField("Altura_mm") else ""
    p = fp.GetPosition()
    out.append({"ref": fp.GetReference(), "value": fp.GetValue(), "lib": str(fp.GetFPID().GetLibItemName()),
                "x": round(MM(p.x), 3), "y": round(MM(p.y), 3), "rot": fp.GetOrientationDegrees(), "bottom": flipped,
                "box": [round(MM(v), 3) for v in (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())],
                "pads": [[round(MM(q.GetPosition().x), 3), round(MM(q.GetPosition().y), 3), q.GetNumber(),
                          q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH] for q in fp.Pads()]
                if fp.GetReference()[:2] in ("J2", "J3", "J4", "J5", "J1", "SW") and len(fp.GetReference()) > 3 else [],
                "height": float(h.replace(",", ".")) if h else None, "dnp": fp.IsDNP()})
json.dump({"thickness": MM(b.GetDesignSettings().GetBoardThickness()), "footprints": out},
          open(os.path.join(HERE, "footprints.json"), "w"), indent=0)
print(len(out), "footprints")
