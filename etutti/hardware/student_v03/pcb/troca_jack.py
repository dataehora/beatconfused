"""Student V3: the two jacks (J301 OUT, J302 IN) become the XUNPU PJ-327A (LCSC C49284723).

    python etutti/hardware/student_v03/pcb/schematic.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/troca_jack.py

JLCPCB flags the SHOU HAN PJ-327A 5JJ (C668605) as "difficult to process"; the XUNPU PJ-327A does not get the
warning. Its pads are numbered 2-6 (datasheet: 2 and 5 sleeve, 6 ring, 4 tip, 3 tip switch, NC to 4) where the
5JJ's are 1-5 (1 and 2 sleeve, 3 ring, 4 tip, 5 switch). The pads' places are the same within 0.4 mm along
the jack's edge and the XUNPU's leads (3.0 x 1.6 mm) fall inside the board's 3 x 2 mm pads, so the routed
copper stays as it is: this script only renumbers the pads by function, renames the two "unconnected" nets that
carry a pad number, widens the two locating holes to 1.2 mm (the XUNPU's pegs) and writes the new part's fields.
DRC with schematic parity must come out as before.
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(V3, ".."))
V2 = os.path.join(HW, "student_v02")
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V2, "pcb"))
sys.path.insert(0, V2)
sys.path.insert(0, os.path.join(HW, "viaggio_j1"))
import build_board as BB        # noqa: E402

NAME = "student_v03"
KDIR = os.path.join(V3, "kicad")
BUILD = os.path.join(HERE, "build")
BOARD = os.path.join(KDIR, NAME + ".kicad_pcb")
BB.NAME, BB.KDIR, BB.BUILD, BB.BOARD = NAME, KDIR, BUILD, BOARD

OLD_TO_NEW = {"1": "2", "2": "5", "3": "6", "4": "4", "5": "3"}     # by function (sleeve, sleeve, ring, tip, switch)
DATASHEET = "https://atta.szlcsc.com/upload/public/pdf/source/20250630/AB61CB55FE842E2CCBB937FDB8FB366C.pdf"
FIELDS = {
    "J301": {"LCSC": "C49284723", "Datasheet": DATASHEET, "Description":
             "SMD, angulo reto, XUNPU (V3; o SHOU HAN 5JJ foi trocado porque a JLCPCB o marca como dificil de montar); "
             "2/5 manga (HP_VGND, nunca no GND), 6 anel, 4 ponta, 3 contato da ponta (fechado sem plugue)"},
    "J302": {"LCSC": "C49284723", "Datasheet": DATASHEET, "Description":
             "IN (microfone): manga no GND, ponta = sinal com bias; anel e contato da ponta soltos (XUNPU, V3)"},
}
NET_RENAME = {"unconnected-(J302-R-Pad3)": "unconnected-(J302-R-Pad6)",
              "unconnected-(J302-TN-Pad5)": "unconnected-(J302-TN-Pad3)"}


def main():
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    for ref, want in FIELDS.items():
        fp = b.FindFootprintByReference(ref)
        numbered = [p for p in fp.Pads() if p.GetNumber()]
        assert sorted(p.GetNumber() for p in numbered) == sorted(OLD_TO_NEW), (ref, [p.GetNumber() for p in numbered])
        for p in numbered:
            p.SetNumber(OLD_TO_NEW[p.GetNumber()])
        for p in fp.Pads():
            if not p.GetNumber():                      # the two locating holes
                p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
                p.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
        fp.SetValue("PJ-327A")
        BB.set_fields(fp, want)
    for old, new in NET_RENAME.items():
        n = b.FindNet(old)
        assert n is not None, old
        n.SetNetname(new)
    for ref in ("SW401", "SW402"):                # as in the V3 schematic (the encoders are soldered at home)
        BB.set_fields(b.FindFootprintByReference(ref), {"Montagem": "sem peca (encoder soldado em casa, topo)"})
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())          # the copper pours keep clear of the wider holes
    d = BB.save_and_drc(b, original)
    viol = {}
    for x in d.get("violations", []):
        if x["severity"] == "error":
            viol[x["type"]] = viol.get(x["type"], 0) + 1
    print("DRC erros:", viol, "| ligacoes faltando:", len(d.get("unconnected_items", [])),
          "| paridade:", len(d.get("schematic_parity", [])))
    for x in d.get("schematic_parity", [])[:20]:
        print("  paridade:", x["description"], [i["description"] for i in x["items"]])
    ok = viol == BB.ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity")
    json.dump({"drc_erros": viol, "faltando": len(d.get("unconnected_items", [])),
               "paridade": len(d.get("schematic_parity", []))},
              open(os.path.join(HERE, "troca_jack.json"), "w", encoding="utf-8"), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
