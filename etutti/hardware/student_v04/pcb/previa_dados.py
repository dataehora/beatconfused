"""Student V4 (R13V4, item 2): dumps what the JLCPCB preview needs from a routed board (KiCad python).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/previa_dados.py principal|r8

Writes pcb/build/previa_<board>.json: outline segments, thickness, and per footprint ref, value, LCSC, library name, side, position/rotation, pads
(global and local), all in mm with y UP (x, -y_kicad, the CPL's convention). Nothing is changed in the board.
"""
import json, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BOARDS = {"principal": os.path.join(HW, "kicad", "student_v04_roteada.kicad_pcb"),
          "r8": os.path.join(HW, "kicad", "regua", "student_v04_regua_R8_painel_de_2.kicad_pcb"),
          "r4": os.path.join(HW, "kicad", "regua", "student_v04_regua_painel.kicad_pcb")}
MM = pcbnew.ToMM


def main(name):
    b = pcbnew.LoadBoard(BOARDS[name])
    out = {"board": os.path.relpath(BOARDS[name], HW), "thickness": round(MM(b.GetDesignSettings().GetBoardThickness()), 3), "outline": [], "fps": {}}
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            s, e = d.GetStart(), d.GetEnd()
            out["outline"].append([d.GetShapeStr(), MM(s.x), -MM(s.y), MM(e.x), -MM(e.y)])
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        pads, loc = [], []
        for p in fp.Pads():
            if p.GetNumber() == "" and not p.IsOnCopperLayer():
                continue
            g = p.GetPosition(); l = p.GetFPRelativePosition()
            sz = p.GetSize()
            pads.append([p.GetNumber(), MM(g.x), -MM(g.y), MM(sz.x), MM(sz.y), p.GetShape(), p.GetOrientationDegrees(), 1 if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else 0,
                         p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH, MM(p.GetDrillSizeX())])
            loc.append([p.GetNumber(), MM(l.x), -MM(l.y)])
        p0 = fp.GetPosition()
        out["fps"][ref] = {"value": fp.GetValue(), "lcsc": fp.GetFieldText("LCSC") if fp.HasField("LCSC") else "", "name": str(fp.GetFPID().GetLibItemName()),
                           "bottom": fp.IsFlipped(), "angle": fp.GetOrientationDegrees(), "x": MM(p0.x), "y": -MM(p0.y), "pads": pads, "local_pads": loc,
                           "montagem": fp.GetFieldText("Montagem") if fp.HasField("Montagem") else ""}
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "build", "previa_%s.json" % name), "w"), indent=0)
    print(name, len(out["fps"]), "footprints", len(out["outline"]), "outline items")


if __name__ == "__main__":
    main(sys.argv[1])
