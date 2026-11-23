"""eTutti Student V4 (R12V4, item 2): fabrication files of the MAIN board, from the ROUTED board (kicad/student_v04_roteada.kicad_pcb).

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/fab_principal.py

Never runs posiciona_v4.py (that rebuilds the unrouted board). Reads the routed board, writes fab/principal/:
  student_v04_gerbers.zip (4 copper layers, paste, silk, mask, outline + Excellon drill, PTH and NPTH), bom.csv, cpl.csv (bottom only, JLCPCB format),
  fora_da_montagem.csv (parts not placed by JLCPCB: bought apart or fitted at home), conferencias.json (DRC, layer count, drill count, LCSC checks), top/bottom PNG.
CPL: position and rotation by the method of student_v01/fornecimento/cpl_jlc.py (EasyEDA footprint pads laid on the board's pads, bottom side mirrored).
Parts left out of BOM and CPL: field Montagem = "nao montar" (C310), "sem peca" (encoders, speaker pads, test point), holes.
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
J1 = os.path.normpath(os.path.join(HERE, "..", "viaggio_j1"))
V1F = os.path.normpath(os.path.join(HERE, "..", "student_v01", "fornecimento"))
BOARD = os.path.join(HERE, "kicad", "student_v04_roteada.kicad_pcb")
FAB = os.path.join(HERE, "fab", "principal")
FORN = os.path.join(HERE, "fornecimento")
BUILD = os.path.join(HERE, "pcb", "build")
KCLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
sys.path.insert(0, J1)
sys.path.insert(0, V1F)
import pcbnew      # noqa: E402
import m3          # noqa: E402
import cpl_jlc     # noqa: E402

NOT_PLACED = ("nao montar", "sem peca", "em casa")


def main():
    os.makedirs(FAB, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    rec = {}
    b = pcbnew.LoadBoard(BOARD)
    rec["camadas_de_cobre"] = b.GetCopperLayerCount()
    rec["espessura_mm"] = round(pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()), 3)
    # DRC with parity of the routed board
    drc = os.path.join(BUILD, "drc_principal_roteada.json")
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--schematic-parity", "--format", "json", "-o", drc, BOARD], capture_output=True)
    d = json.load(open(drc, encoding="utf-8"))
    rec["drc"] = {"violacoes": Counter((v["severity"], v["type"]) for v in d["violations"]).most_common(),
                  "nao_conectadas": len(d.get("unconnected_items", [])), "paridade": len(d.get("schematic_parity", []))}
    rec["drc"]["violacoes"] = [[list(k), n] for k, n in rec["drc"]["violacoes"]]
    # Gerbers + drill
    m3.BOARD, m3.BUILD, m3.FAB = BOARD, BUILD, FAB
    z, files = m3.gerbers(BOARD, "student_v04", m3.GERBER_LAYERS)
    os.replace(z, os.path.join(FAB, "student_v04_gerbers.zip")) if os.path.basename(z) != "student_v04_gerbers.zip" else None
    rec["gerbers"] = {"zip": "fab/principal/student_v04_gerbers.zip", "arquivos": files}
    rec["gerbers"]["camadas_cobre_nos_arquivos"] = sorted(n.split("-")[-1] for n in files if n.endswith((".gtl", ".gbl", ".g1", ".g2")))
    # drill count against the board: PTH = vias + plated pad holes; NPTH = non-plated holes
    pth = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    npth = 0
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSizeX() > 0:
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    pth += 1
                else:
                    npth += 1
    gd = os.path.join(BUILD, "gerbers_student_v04")

    def holes(path):
        n = 0
        for line in open(path, encoding="utf-8", errors="replace"):
            if re.match(r"^X-?\d", line) or re.match(r"^X-?\d+\.\d+Y", line):
                n += 1
        return n
    drl = {f: holes(os.path.join(gd, f)) for f in files if f.endswith(".drl")}
    rec["furos"] = {"placa_PTH_vias_e_pads": pth, "placa_NPTH": npth, "arquivos_drl": drl}
    # BOM / CPL
    pads = os.path.join(FORN, "easyeda_pads.json")
    cpl_tmp = os.path.join(BUILD, "cpl_principal_tudo.csv")
    cpl_jlc.HERE, cpl_jlc.BOARD, cpl_jlc.PADS = FORN, BOARD, pads
    cpl_jlc.CACHE, cpl_jlc.CPL = os.path.join(FORN, "easyeda"), cpl_tmp
    try:
        cpl_jlc.main()
    except SystemExit as e:
        if e.code:
            raise
    cpl = list(csv.DictReader(open(cpl_tmp, encoding="utf-8")))
    skip, fora, groups = set(), [], {}
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        mont = fp.GetFieldText("Montagem") if fp.HasField("Montagem") else ""
        name = str(fp.GetFPID().GetLibItemName())
        lcsc = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
        if fp.IsDNP() or mont.startswith(NOT_PLACED) or any(k in name for k in m3.NOT_ASSEMBLED) or not lcsc:
            skip.add(ref)
            fora.append([ref, fp.GetValue(), mont or name])
            continue
        g = groups.setdefault((fp.GetValue(), name, lcsc), [])
        g.append(ref)
    rows = [r for r in cpl if r["Designator"] not in skip]
    with open(os.path.join(FAB, "cpl.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        for r in rows:
            w.writerow([r["Designator"], r["Val"], r["Package"], r["Mid X"], r["Mid Y"], r["Rotation"], r["Layer"]])

    def key(r):
        return (r.rstrip("0123456789"), int(re.sub(r"\D", "", r) or 0))
    with open(os.path.join(FAB, "bom.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (v, n, l), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([v, ",".join(sorted(refs, key=key)), n, l])
    with open(os.path.join(FAB, "fora_da_montagem.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["referencia", "peca", "por que"])
        w.writerows(fora)
    rec["bom"] = {"linhas": len(groups), "pecas": sum(len(v) for v in groups.values())}
    rec["cpl"] = {"pecas": len(rows), "baixo": sum(1 for r in rows if r["Layer"] == "Bottom"), "cima": sum(1 for r in rows if r["Layer"] == "Top")}
    rec["fora"] = [r[0] for r in fora]
    bom_refs = {x for refs in groups.values() for x in refs}
    rec["bom_igual_cpl"] = bom_refs == {r["Designator"] for r in rows}
    # LCSC checks against the JLCPCB library cache (fornecimento/precos_jlc.json)
    pj = json.load(open(os.path.join(FORN, "precos_jlc.json"), encoding="utf-8"))
    lc = []
    ext = set()
    for (v, n, l), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        info = pj.get(l) or {}
        lc.append({"lcsc": l, "valor": v, "footprint": n, "qtd": len(refs), "classe": info.get("classe", "?"), "estoque": info.get("estoque"),
                   "modelo": info.get("modelo"), "preco_1": (info.get("tiers") or [[0, None]])[0][1]})
        if info.get("classe") != "Basic":
            ext.add(l)
    rec["lcsc"] = lc
    rec["tipos_extended"] = len(ext)
    rec["custo_pecas_USD_1_placa"] = round(sum(x["qtd"] * (x["preco_1"] or 0) for x in lc), 2)
    # pictures
    for side in ("top", "bottom"):
        subprocess.run([KCLI, "pcb", "render", "--side", side, "--width", "1800", "--height", "1800", "--quality", "basic",
                        "--output", os.path.join(FAB, "student_v04_%s.png" % side), BOARD], capture_output=True)
    json.dump(rec, open(os.path.join(FAB, "conferencias.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rec.items() if k != "lcsc"}, indent=1, ensure_ascii=False))
    for x in lc:
        print(x)


if __name__ == "__main__":
    main()
