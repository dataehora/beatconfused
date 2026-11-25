"""Stage 1 of the ruler routing (R8SL 3a): the base board to route. KiCad python, idempotent (rewrites rota/kicad/base/ every time).

    "C:/Program Files/KiCad/10.0/bin/python.exe" prepara.py

Reads the placed board pcb/kicad_regua/slim_regua.kicad_pcb (never writes there; no part is moved) and writes rota/kicad/base/slim_regua.kicad_pcb with
  - the routing rules (.kicad_pro as the placement's, .kicad_dru rewritten: OUT keep-away 1,0 mm except at the FFC pads, tracks >= 0,15, preferred 0,2, via 0,6/0,3),
  - the rule area "Zona FFC" (no keep-out; only scopes the OUT rule),
  - the GND pour on F.Cu (key side) over the whole outline, net GND, clearance 0,2, islands removed, M2 keep-outs kept.
No track yet.
"""
import json, os, shutil, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "kicad_regua")
DST = os.path.join(HERE, "kicad", "base")
M = pcbnew.FromMM
os.makedirs(DST, exist_ok=True)
for f in ("slim_regua.kicad_pcb", "slim_regua.kicad_pro", "slim_regua.kicad_sch", "slim_regua_R.kicad_sch", "fp-lib-table", "sym-lib-table", "slim.kicad_sym"):
    shutil.copy(os.path.join(SRC, f), os.path.join(DST, f))
shutil.copytree(os.path.join(SRC, "slim.pretty"), os.path.join(DST, "slim.pretty"), dirs_exist_ok=True)

DRU = """(version 1)
# eTutti Slim ruler R8 -- routing rules (R8SL, stage 3a).
(rule "Vias 0,6 / furo 0,3"
    (condition "A.Type == 'via'")
    (constraint via_diameter (min 0.5mm))
    (constraint hole_size (min 0.3mm)))
(rule "Trilhas: minimo 0,15; preferida 0,2"
    (condition "A.Type == 'track'")
    (constraint track_width (min 0.15mm) (opt 0.2mm)))
# OUT is the analogue line (the 8 sensors share it, mV swings). DATA/CLK/LATCH are the fast edges (3.3 V, ns). Crosstalk falls with distance:
# 1.0 mm = 5 track widths, well beyond the 0.15 mm default gap. At the FFC pads (0.5 mm pitch, OUT is pin 3 beside DATA pin 4) the pitch itself
# leaves 0.2 mm between pads, so the rule is relaxed only inside the rule area "Zona FFC" (2 mm in front of the connector).
(rule "OUT longe de DADO/CLOCK/LATCH (>= 1,0 mm)"
    (condition "A.NetName == 'OUT' && (B.NetName == 'DATA' || B.NetName == 'CLK' || B.NetName == 'LATCH')")
    (constraint clearance (min 1.0mm)))
(rule "OUT junto aos pads do FFC (passo 0,5: folga entre pads 0,2 mm)"
    (condition "A.NetName == 'OUT' && (B.NetName == 'DATA' || B.NetName == 'CLK' || B.NetName == 'LATCH') && (A.insideArea('Zona FFC') || B.insideArea('Zona FFC'))")
    (constraint clearance (min 0.2mm)))
"""
open(os.path.join(DST, "slim_regua.kicad_dru"), "w", newline="\n").write(DRU)

pro = os.path.join(DST, "slim_regua.kicad_pro")
d = json.load(open(pro, encoding="utf-8"))
d["board"]["design_settings"]["rules"].update({"min_clearance": 0.1, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3, "min_via_annular_width": 0.1})
d["net_settings"]["classes"][0].update({"clearance": 0.1, "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3})
json.dump(d, open(pro, "w", encoding="utf-8"), indent=2)

b = pcbnew.LoadBoard(os.path.join(DST, "slim_regua.kicad_pcb"))
# rule area Zona FFC: x 20..25.6, y 26.5..33.5 (J1 pads at x 23.45, y 28.25..31.75)
z = pcbnew.ZONE(b); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.F_Cu); z.SetLayerSet(ls)
z.SetZoneName("Zona FFC"); z.SetIsRuleArea(True)
z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowFootprints(False); z.SetDoNotAllowPads(False)
o = z.Outline(); o.NewOutline()
for x, y in ((20.0, 26.5), (25.6, 26.5), (25.6, 33.5), (20.0, 33.5)):
    o.Append(M(x), M(y))
b.Add(z)

# keep-outs round every NPTH hole (hole radius + 0.25 copper-to-hole + 0.1 half track + 0.03): the grid router of KiCadRoutingTools delivered only
# 0.20-0.23 mm to the key holes, KiCad's rule (min_hole_clearance 0.25, JLCPCB's own limit) wants 0.25. Tracks and vias are kept out; the pour may fill.
import math
n_ko = 0
for fp in b.GetFootprints():
    for pd in fp.Pads():
        if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and pd.GetDrillSize().x > 0:
            r = pcbnew.ToMM(pd.GetDrillSize().x) / 2 + 0.25 + 0.1 + 0.03
            R = r / math.cos(math.pi / 24)
            cx, cy = pcbnew.ToMM(pd.GetX()), pcbnew.ToMM(pd.GetY())
            zk = pcbnew.ZONE(b); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.F_Cu); zk.SetLayerSet(ls)
            zk.SetZoneName("Furo + 0,38 (%s)" % fp.GetReference()); zk.SetIsRuleArea(True)
            zk.SetDoNotAllowTracks(True); zk.SetDoNotAllowVias(True); zk.SetDoNotAllowZoneFills(False); zk.SetDoNotAllowFootprints(False); zk.SetDoNotAllowPads(False)
            o = zk.Outline(); o.NewOutline()
            for k in range(24):
                a = 2 * math.pi * (k + .5) / 24
                o.Append(M(cx + R * math.cos(a)), M(cy + R * math.sin(a)))
            b.Add(zk); n_ko += 1
print("keep-outs de furo:", n_ko)
# GND pour on F.Cu
g = pcbnew.ZONE(b); g.SetLayer(pcbnew.F_Cu); g.SetNet(b.FindNet("GND")); g.SetZoneName("GND topo")
g.SetLocalClearance(M(0.2)); g.SetMinThickness(M(0.2)); g.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
g.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
g.SetThermalReliefGap(M(0.3)); g.SetThermalReliefSpokeWidth(M(0.3))
o = g.Outline(); o.NewOutline()
for x, y in ((20.0, 22.5), (180.0, 22.5), (180.0, 37.5), (20.0, 37.5)):
    o.Append(M(x), M(y))
b.Add(g)
pcbnew.SaveBoard(os.path.join(DST, "slim_regua.kicad_pcb"), b)
print("base escrita em", DST)
