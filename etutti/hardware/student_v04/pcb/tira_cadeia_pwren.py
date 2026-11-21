"""Student V3: the redundant USB-hold chain goes (J, 19 Nov 2026: option A, "USB wakes, no cut-off with a cable").

    python etutti/hardware/student_v03/pcb/schematic.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/pcb/tira_cadeia_pwren.py

D206 (VBUS_S -> EN_REQ) switches the 3.3 V on whenever a cable is plugged, so the V1/V2 "USB AND PWR_EN" hold (U203 +
D204 + R217 + R218 + C213, module pad 4 = 3.3V_EN = Teensy pin 28) could no longer switch anything off: it only added
parts and a 100 ms timing that had to beat the 3.3 V's fall. This script takes the five footprints and the copper of
USB_HOLD / PWR_EN_S / PWR_EN off the board, leaves J101 pad 4 unconnected (the net name KiCad's netlist gives it), lets
DRC remove the stubs that were left on +3V3 / GND, refills the zones and checks DRC with schematic parity.
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, ".."))
HW = os.path.normpath(os.path.join(V3, ".."))
V2 = os.path.join(HW, "student_v02")
sys.path.insert(0, HERE)
sys.path.insert(0, V3)
sys.path.insert(0, os.path.join(V2, "pcb"))
sys.path.insert(0, V2)
sys.path.insert(0, os.path.join(HW, "viaggio_j1"))
import build_board_v3 as B3     # noqa: E402
import build_board as BB        # noqa: E402

GONE = ["U203", "D204", "R217", "R218", "C213"]
DEAD_NETS = ("USB_HOLD", "PWR_EN_S", "PWR_EN")
PAD4 = "unconnected-(J101A-3.3V_EN_(28)-Pad4)"


def main():
    original = open(B3.BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(B3.BOARD)
    report = {"tiradas": GONE}
    for t in list(b.GetTracks()):
        if t.GetNetname() in DEAD_NETS:
            BB.rm(b, t)
    for ref in GONE:
        BB.rm(b, b.FindFootprintByReference(ref))
    j101 = b.FindFootprintByReference("J101")
    for p in j101.Pads():
        if p.GetNumber() == "4":
            p.SetNet(BB.net_of(b, PAD4))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d = B3.rip_by_drc(b, original, report, set(), "depois de tirar a cadeia", set())
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    # a net that went through one of the removed pads (VBUS_S: R214/R215 - U203 - D206) is open now: route it again
    rr = B3.rr
    all_nets = sorted({p_.GetNetname() for p_ in b.GetPads() if p_.GetNetname() and not p_.GetNetname().startswith("unconnected-")})
    ctx = rr.Ctx(b)
    chk = rr.Checker(ctx)
    made, log, fails = [], [], []
    opened = [n_ for n_ in all_nets if n_ not in BB.PLANES and len(rr.clusters(b, n_)) > 1]
    report["abertas"] = opened
    for net in opened:
        rr.join_net(ctx, chk, net, None, made, log, fails)
    report["falhas"] = [f["net"] + " " + str(f.get("pinos")) for f in fails]
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d = B3.rip_by_drc(b, original, report, set(), "depois de rotear", set())
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    d = BB.save_and_drc(b, original)
    import collections
    viol = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] == "error")
    warn = collections.Counter(x["type"] for x in d.get("violations", []) if x["severity"] != "error")
    report["drc"] = {"erros": dict(viol), "avisos": dict(warn), "ligacoes_faltando": len(d.get("unconnected_items", [])),
                     "paridade": len(d.get("schematic_parity", []))}
    report["paridade_detalhe"] = [(x["type"], x["description"], [i["description"] for i in x["items"]])
                                  for x in d.get("schematic_parity", [])][:20]
    json.dump(report, open(os.path.join(HERE, "tira_cadeia_pwren.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report["drc"]))
    for x in report["paridade_detalhe"]:
        print("  paridade:", x)
    ok = dict(viol) == BB.ACCEPTED and not d.get("unconnected_items") and not d.get("schematic_parity")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
