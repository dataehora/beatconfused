"""Run with KiCad's Python: writes build/footprints.json (every footprint of the board: where it is,
its courtyard box, its height field, and whether KiCad's library has its 3D model)."""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "kicad", "viaggio_micromod.kicad_pcb")
MODELS = "C:/Program Files/KiCad/10.0/share/kicad/3dmodels"
MM = pcbnew.ToMM

b = pcbnew.LoadBoard(BOARD)
out = []
for fp in b.GetFootprints():
    flipped = fp.IsFlipped()
    box = fp.GetCourtyard(pcbnew.B_CrtYd if flipped else pcbnew.F_CrtYd).BBox()
    if box.GetWidth() <= 0:
        box = fp.GetBoundingBox(False)
    models = [m.m_Filename for m in fp.Models()]
    have = [os.path.exists(m.replace("${KICAD10_3DMODEL_DIR}", MODELS)) for m in models]
    h = fp.GetFieldText("Altura_mm") if fp.HasField("Altura_mm") else ""
    p = fp.GetPosition()
    out.append({"ref": fp.GetReference(), "value": fp.GetValue(), "lib": str(fp.GetFPID().GetLibItemName()),
                "x": MM(p.x), "y": MM(p.y), "rot": fp.GetOrientationDegrees(), "bottom": flipped,
                "box": [MM(box.GetLeft()), MM(box.GetTop()), MM(box.GetRight()), MM(box.GetBottom())],
                "height": float(h.replace(",", ".")) if h else None, "has_model": bool(models) and all(have)})
ds = b.GetDesignSettings()
json.dump({"thickness": MM(ds.GetBoardThickness()), "footprints": out},
          open(os.path.join(HERE, "build", "footprints.json"), "w"), indent=0)
print(len(out), "footprints")
