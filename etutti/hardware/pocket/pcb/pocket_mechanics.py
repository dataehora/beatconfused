"""How far the Pocket's main board bends under a key press (KiCad's Python,
which has numpy):

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/pocket/pcb/pocket_mechanics.py

Uses the eTuttino's grillage model (etutti/hardware/mechanics.py:
deflections()) unchanged, pointed at the Pocket's geometry through its
module global G -- the eTuttino script itself is not modified. Supports:
the case's pillars and its two M2 screws (pcb_envelope.json "supports"),
plus the 28 Audio Board header legs soldered into the board under the stack.

Writes build/pocket_supports.json and exits non-zero above 0.05 mm at 3 N.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.normpath(os.path.join(HERE, "..", "..")))

import mechanics as M  # noqa: E402  (the eTuttino's)
import pocket_geom as P  # noqa: E402


def main():
    M.G = P                                  # PCB_W, PCB_H, PCB_THICKNESS from the Pocket
    ks = P.keys()
    loads = [(k["cx"], k["cy"]) for k in ks]
    legs = [(p[3], p[4]) for p in P.stack_pins()]
    pillars = [(x, y) for x, y, _ in P.SUPPORTS]
    sag = M.deflections(pillars + legs, loads)
    worst = max(range(len(ks)), key=lambda i: sag[i])
    res = {
        "model": "eTuttino mechanics.deflections(): grillage of the bare %.1f mm FR-4 board's bounding box, "
                 "%.0f mm mesh, E = %.0f MPa, no twisting stiffness, plate ignored" % (P.PCB_THICKNESS, M.GRID_H, M.E_FR4),
        "press_n": M.PRESS_N,
        "supports": len(pillars),
        "max_mm": round(max(sag), 4),
        "mean_mm": round(sum(sag) / len(sag), 4),
        "worst_key": "%s (row %d)" % (P.note_name(ks[worst]["note"]), ks[worst]["row"]),
        "target_mm": M.TARGET_MM,
        "per_key_mm": {"%s %s" % (k["ref"], P.note_name(k["note"])): round(d, 4) for k, d in zip(ks, sag)},
    }
    os.makedirs(P.BUILD, exist_ok=True)
    with open(os.path.join(P.BUILD, "pocket_supports.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("%d supports: worst sag %.3f mm (%s), mean %.3f mm at %.0f N; target %.2f" % (
        len(pillars), res["max_mm"], res["worst_key"], res["mean_mm"], M.PRESS_N, M.TARGET_MM))
    return 0 if res["max_mm"] <= M.TARGET_MM else 1


if __name__ == "__main__":
    sys.exit(main())
