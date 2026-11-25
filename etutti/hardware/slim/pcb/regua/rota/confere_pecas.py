"""Check that no part moved: positions, rotation and side of every footprint of the routed ruler equal the placed board's. KiCad python.
    python confere_pecas.py     -> prints 'ok: N pecas iguais' or the differences; exit 1 on a difference"""
import os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
a = pcbnew.LoadBoard(os.path.join(HERE, "..", "..", "kicad_regua", "slim_regua.kicad_pcb"))
b = pcbnew.LoadBoard(os.path.join(HERE, "kicad", "slim_regua_rota.kicad_pcb"))
pa = {f.GetReference(): (f.GetX(), f.GetY(), round(f.GetOrientationDegrees(), 3), f.GetLayer()) for f in a.GetFootprints()}
pb = {f.GetReference(): (f.GetX(), f.GetY(), round(f.GetOrientationDegrees(), 3), f.GetLayer()) for f in b.GetFootprints()}
diff = [k for k in set(pa) | set(pb) if pa.get(k) != pb.get(k)]
print("ok: %d pecas iguais" % len(pa) if not diff else "DIFERENTES: %s" % diff)
sys.exit(1 if diff else 0)
