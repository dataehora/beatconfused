"""DRC of the placed main board (no tracks), with schematic parity. Plain python (calls kicad-cli).

    python etutti/hardware/slim/pcb/principal/drc_principal.py     -> pcb/principal/build/drc_principal.json

Stage 2b accepts: 0 errors, 0 warnings, parity 0; the unconnected items are the ratsnest (no tracks yet) and are only counted.
"""
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KD = os.path.join(HERE, "..", "kicad_principal")
CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
out = os.path.join(HERE, "build", "drc_principal_raw.json")
subprocess.run([CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json", "-o", out, os.path.join(KD, "slim_principal.kicad_pcb")], capture_output=True)
d = json.load(open(out, encoding="utf-8"))
c = collections.Counter(v["severity"] for v in d["violations"])
res = {"erros": c.get("error", 0), "avisos": c.get("warning", 0), "nao_ligados": len(d.get("unconnected_items", [])), "paridade": len(d.get("schematic_parity", [])),
       "tipos": dict(collections.Counter(v["type"] for v in d["violations"]))}
print(res)
for v in d["violations"][:12]:
    print(v["severity"], v["type"], v["description"][:90], [i.get("description", "")[:50] for i in v["items"]][:2])
json.dump(res, open(os.path.join(HERE, "build", "drc_principal.json"), "w"), indent=1)
sys.exit(1 if res["erros"] + res["avisos"] + res["paridade"] else 0)
