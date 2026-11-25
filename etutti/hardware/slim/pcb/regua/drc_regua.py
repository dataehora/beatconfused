"""DRC of the placed ruler (no tracks) and of the grade, with schematic parity. Plain python (calls kicad-cli).

    python etutti/hardware/slim/pcb/regua/drc_regua.py     -> pcb/regua/build/drc_regua.json (counts), prints them

Stage 2a accepts: 0 errors, 0 warnings, parity 0; the unconnected items are the ratsnest (no tracks yet) and are only counted.
"""
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KD = os.path.join(HERE, "..", "kicad_regua")
CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
res, bad = {}, 0
for name, parity in (("slim_regua", True), ("slim_grade", False)):
    out = os.path.join(HERE, "build", "drc_%s_raw.json" % name)
    cmd = [CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out]
    if parity:
        cmd.insert(3, "--schematic-parity")
    subprocess.run(cmd + [os.path.join(KD, name + ".kicad_pcb")], capture_output=True)
    d = json.load(open(out, encoding="utf-8"))
    c = collections.Counter(v["severity"] for v in d["violations"])
    res[name] = {"erros": c.get("error", 0), "avisos": c.get("warning", 0), "nao_ligados": len(d.get("unconnected_items", [])),
                 "paridade": len(d.get("schematic_parity", [])) if parity else None,
                 "tipos": dict(collections.Counter(v["type"] for v in d["violations"]))}
    bad += res[name]["erros"] + res[name]["avisos"] + (res[name]["paridade"] or 0)
    print(name, res[name])
json.dump(res, open(os.path.join(HERE, "build", "drc_regua.json"), "w"), indent=1)
sys.exit(1 if bad else 0)
