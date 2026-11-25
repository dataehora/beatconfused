"""Checks the schematic's RT1062 footprint and ball map against the SamacSys library the J supplied (modelos/rt1062/kicad/).

    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 etutti/hardware/slim/pcb/confere_rt1062.py

1. footprint: same 196 pad names, same positions (max deviation printed), pad diameters of both;
2. ball map: every SamacSys symbol pin name (numeric suffix stripped: VSS_1 -> VSS, DCDC__IN_Q -> DCDC_IN_Q) equals rt1062_balls.json.
Exit 1 on a difference.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr as S  # noqa: E402

LIB = os.path.join(HERE, "..", "modelos", "rt1062", "kicad")


def pads(path):
    t = open(path, encoding="utf-8").read()
    return {m.group(1): (float(m.group(4)), float(m.group(5)), float(m.group(6)))
            for m in re.finditer(r'\(pad "?([A-Z0-9]+)"?\s+(\w+)\s+(\w+)\s+\(at ([-\d.]+) ([-\d.]+)[^)]*\)\s+\(size ([-\d.]+) ([-\d.]+)\)', t)}


a = pads(os.path.join(LIB, "BGA196C80P14X14_1200X1200X152.kicad_mod"))
b = pads(os.path.join(HERE, "kicad", "slim.pretty", "BGA-196_12x12mm_P0.8mm_RT1062.kicad_mod"))
bad = 0
if set(a) != set(b):
    print("pad names differ:", sorted(set(a) ^ set(b))[:10]); bad += 1
dev = max(max(abs(a[k][0] - b[k][0]), abs(a[k][1] - b[k][1])) for k in a if k in b)
print("footprint: %d vs %d pads, max position deviation %.4f mm, pad diameter SamacSys %.3f / esquema %.3f" % (
    len(a), len(b), dev, next(iter(a.values()))[2], next(iter(b.values()))[2]))
bad += dev > 0.001
balls = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
root = S.parse(open(os.path.join(LIB, "MIMXRT1062DVJ6B.kicad_sym"), encoding="utf-8").read())
pins = {}


def walk(n):
    for x in n:
        if isinstance(x, list) and x and x[0] == "pin":
            pins[S.first(x, "number")[1]] = S.first(x, "name")[1]
        elif isinstance(x, list):
            walk(x)


walk(root)
diff = []
for k, nm in pins.items():
    base = re.sub(r"_\d+$", "", nm).replace("__", "_")
    if nm.replace("__", "_") != balls.get(k) and base != balls.get(k):
        diff.append((k, nm, balls.get(k)))
print("ball map: %d SamacSys pins, %d differ after stripping suffixes %s" % (len(pins), len(diff), diff[:10]))
bad += len(diff) + (set(pins) != set(balls))
sys.exit(1 if bad else 0)
