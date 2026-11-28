"""Metrics of a routed ruler board: DRC (kicad-cli, with parity when a schematic sits beside it), tracks, vias, length.
    KiCad python: python metricas.py board.kicad_pcb [--sch ../../kicad_regua/slim_regua.kicad_sch]  -> prints one JSON line
"""
import collections, json, os, subprocess, sys, tempfile, shutil
import pcbnew
CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, "..", "..", "kicad_regua", "slim_regua.kicad_sch")

def drc(pcb, tag="x"):
    out = os.path.join(HERE, "build", "drc_%s.json" % tag)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    d = os.path.dirname(os.path.abspath(pcb))
    base = os.path.splitext(os.path.basename(pcb))[0]
    # project, rules, schematic (for parity) and libraries of the base board beside the board under test
    BASE = os.path.join(HERE, "kicad", "base")
    if os.path.abspath(d) != os.path.abspath(BASE):
        for ext in (".kicad_pro", ".kicad_dru", ".kicad_sch"):
            shutil.copy(os.path.join(BASE, "slim_regua" + ext), os.path.join(d, base + ext))
        for f in ("slim_regua_R.kicad_sch", "fp-lib-table", "sym-lib-table", "slim.kicad_sym"):
            shutil.copy(os.path.join(BASE, f), os.path.join(d, f))
        shutil.copytree(os.path.join(BASE, "slim.pretty"), os.path.join(d, "slim.pretty"), dirs_exist_ok=True)
    subprocess.run([CLI, "pcb", "drc", "--severity-all", "--schematic-parity", "--format", "json", "-o", out, pcb], capture_output=True)
    j = json.load(open(out, encoding="utf-8"))
    c = collections.Counter(v["severity"] for v in j["violations"])
    sig = [u for u in j.get("unconnected_items", []) if not any("[GND]" in i["description"] for i in u["items"])]
    return {"nao_ligados_sinais": len(sig), "erros": c.get("error", 0), "avisos": c.get("warning", 0), "nao_ligados": len(j.get("unconnected_items", [])),
            "paridade": len(j.get("schematic_parity", [])),
            "tipos": dict(collections.Counter(v["type"] for v in j["violations"]))}

def geom(pcb):
    b = pcbnew.LoadBoard(pcb)
    tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    bynet = collections.defaultdict(float)
    for t in tr:
        bynet[t.GetNetname()] += t.GetLength() / 1e6
    return {"trilhas": len(tr), "vias": len(vias), "comprimento_mm": round(sum(bynet.values()), 2),
            "larg_min_mm": round(min([t.GetWidth() for t in tr] or [0]) / 1e6, 3),
            "por_rede": {k: round(v, 2) for k, v in sorted(bynet.items())}}

if __name__ == "__main__":
    p = os.path.abspath(sys.argv[1])
    r = geom(p)
    r["drc"] = drc(p, os.path.splitext(os.path.basename(p))[0])
    print(json.dumps(r))
