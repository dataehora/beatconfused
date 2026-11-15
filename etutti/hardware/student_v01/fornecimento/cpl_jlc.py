"""Writes fab/student_v01_cpl.csv with the position and rotation JLCPCB needs for every part,
worked out from the pads instead of from a rotation table.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/fornecimento/cpl_jlc.py

JLCPCB places a part by the footprint EasyEDA has for its LCSC code: the CPL's X/Y is where that
footprint's origin goes, and Rotation 0 is that footprint as EasyEDA draws it. KiCad's footprint
for the same part may have another origin (the encoder's is its pin A, the jack's is at the board
edge) and another zero orientation. So, for every part on the board:

  1. the EasyEDA footprint of its LCSC code is fetched (its pads are kept in
     fornecimento/easyeda_pads.json; a new code is fetched with plain curl, slowly) and its pads read;
  2. the turn (0/90/180/270) and shift that lay those pads on the board's pads are found: by pad
     number when both footprints number their pads alike, else by the pads' places;
  3. X/Y = where the EasyEDA origin lands; Rotation = that turn. For a part on the bottom the
     EasyEDA footprint is mirrored left-right first and the turn is counted the other way, which is
     JLCPCB's bottom-side convention (it reproduces the usual 180 - angle rule for a part whose
     two footprints agree).

It prints, per footprint, the old CPL's rotation next to the new one and the shift of the
position, and writes fornecimento/cpl_jlc.json. A pad pattern that fits in more than one turn
equally well (a two-pad part is the same turned 180) is settled by the pad numbers; if those
cannot settle it either the part is listed under "ambiguas" for a look at JLCPCB's preview.
"""
import csv
import json
import math
import os
import subprocess
import sys
import time

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOARD = os.path.join(ROOT, "kicad", "viaggio_micromod.kicad_pcb")
CACHE = os.path.join(HERE, "easyeda")
CPL = os.path.join(ROOT, "fab", "student_v01_cpl.csv")
API = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"
NOT_ASSEMBLED = ("Gateron", "MountingHole", "TestPoint", "SolderWire")
MM = pcbnew.ToMM
UNIT = 0.254                      # EasyEDA's unit (10 mil) in mm


PADS = os.path.join(HERE, "easyeda_pads.json")      # the pads read so far, by LCSC code (in Git)


def easyeda(code):
    """Pads of the EasyEDA footprint: [(number, x, y)] in mm, y up, relative to its origin."""
    known = json.load(open(PADS, encoding="utf-8")) if os.path.exists(PADS) else {}
    if code in known:
        return [tuple(p) for p in known[code]]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, code + ".json")
    if not os.path.exists(path):
        raw = subprocess.run(["curl", "-s", "-f", "--max-time", "90", API % code], capture_output=True).stdout
        time.sleep(25)                # the server refuses after about a dozen requests in a few minutes
        try:
            json.loads(raw)["result"]["packageDetail"]["dataStr"]["shape"]
        except Exception:
            return None
        open(path, "wb").write(raw)
    d = json.load(open(path, encoding="utf-8"))["result"]["packageDetail"]["dataStr"]
    ox, oy = float(d["head"]["x"]), float(d["head"]["y"])
    pads = []
    for s in d["shape"]:
        f = s.split("~")
        if f[0] == "PAD":
            pads.append((f[8], round((float(f[2]) - ox) * UNIT, 4), round(-(float(f[3]) - oy) * UNIT, 4)))
    known[code] = pads
    json.dump(known, open(PADS, "w", encoding="utf-8"), indent=0, sort_keys=True)
    return pads


def turn(p, deg):
    c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg)))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def fit(board_pads, ee_pads, bottom):
    """Best (cost, turn, tx, ty, how) laying the EasyEDA pads on the board's pads."""
    ee = [(n, -x, y) if bottom else (n, x, y) for n, x, y in ee_pads]
    # pad numbers that appear exactly once in both footprints; enough of them settle the fit
    bn, en = [n for n, _, _ in board_pads], [n for n, _, _ in ee]
    common = {n for n in bn if n and bn.count(n) == 1 and en.count(n) == 1}
    by_number = len(common) >= max(2, 0.6 * min(len(bn), len(en)))
    out = []
    for deg in (0, 90, 180, 270):
        e = [(n,) + turn((x, y), deg) for n, x, y in ee]
        if by_number:
            eb = {n: (x, y) for n, x, y in e}
            pairs = [((x, y), eb[n]) for n, x, y in board_pads if n in common]
        else:                       # centroids together, then each board pad with its nearest EasyEDA pad
            cb = [sum(v) / len(board_pads) for v in zip(*[(x, y) for _, x, y in board_pads])]
            ce = [sum(v) / len(e) for v in zip(*[(x, y) for _, x, y in e])]
            pairs = []
            for _, x, y in board_pads:
                q = min(e, key=lambda t: (t[1] - ce[0] - x + cb[0]) ** 2 + (t[2] - ce[1] - y + cb[1]) ** 2)
                pairs.append(((x, y), (q[1], q[2])))
        tx = sum(b[0] - q[0] for b, q in pairs) / len(pairs)
        ty = sum(b[1] - q[1] for b, q in pairs) / len(pairs)
        cost = max(math.hypot(b[0] - q[0] - tx, b[1] - q[1] - ty) for b, q in pairs)
        out.append((cost, deg, tx, ty, "numeros" if by_number else "posicoes"))
    return sorted(out)


def main():
    board = pcbnew.LoadBoard(BOARD)
    before = os.path.join(HERE, "cpl_antigo.csv")       # the table-based CPL this one replaces, kept to compare
    old = {r["Designator"]: r for r in csv.DictReader(open(before, encoding="utf-8"))} if os.path.exists(before) else {}
    rows, report, ambiguous, failed = [], {}, [], []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        name = str(fp.GetFPID().GetLibItemName())
        ref = fp.GetReference()
        mont = fp.GetFieldText("Montagem") if fp.HasField("Montagem") else ""
        if any(k in name for k in NOT_ASSEMBLED) or mont.startswith("sem peca"):
            continue
        code = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
        bottom = fp.IsFlipped()
        pads = [(p.GetNumber(), MM(p.GetPosition().x), -MM(p.GetPosition().y)) for p in fp.Pads()
                if p.GetNumber() != "" or p.IsOnCopperLayer()]
        ee = easyeda(code) if code else None
        if not ee:
            failed.append((ref, code))
            continue
        fits = fit(pads, ee, bottom)
        cost, deg, tx, ty, how = fits[0]
        # another turn fitting as well: only harmless when the part is the same turned (2 pads, no polarity)
        twin = [f for f in fits[1:] if f[0] - cost < 0.05]
        rotation = (-deg) % 360 if bottom else deg
        o = old.get(ref)
        ox, oy = (float(o["Mid X"][:-2]), float(o["Mid Y"][:-2])) if o else (tx, ty)
        rows.append([ref, fp.GetValue(), name, "%.4fmm" % tx, "%.4fmm" % ty, "%d" % rotation, "Bottom" if bottom else "Top"])
        rec = report.setdefault(name, {"lcsc": code, "refs": [], "como": how, "erro_max_mm": 0.0, "antes_depois": set(),
                                       "deslocamento_mm": 0.0, "lado": "baixo" if bottom else "cima"})
        rec["refs"].append(ref)
        rec["erro_max_mm"] = max(rec["erro_max_mm"], round(cost, 3))
        rec["deslocamento_mm"] = max(rec["deslocamento_mm"], round(math.hypot(tx - ox, ty - oy), 2))
        rec["antes_depois"].add(((int(float(o["Rotation"])) if o else None), rotation, fp.GetOrientationDegrees()))
        if twin and how == "posicoes":
            ambiguous.append((ref, name, [f[1] for f in twin]))
        if cost > 0.6:
            ambiguous.append((ref, name, "pads a %.2f mm" % cost))
    if failed:
        print("sem footprint da EasyEDA (o CPL nao foi escrito):", failed)
        sys.exit(1)
    with open(CPL, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        w.writerows(rows)
    for name, r in sorted(report.items(), key=lambda kv: -kv[1]["deslocamento_mm"]):
        ad = sorted(r["antes_depois"], key=str)
        changed = sorted({(a - b) % 360 for a, b, _ in ad if a is not None})
        r["antes_depois"] = [list(x) for x in ad]
        r["rotacao_mudou_em"] = changed
        print("%-44s %-5s x%-2d %-8s erro %.2f  rot antes->depois difere em %-10s desloc %.2f mm" % (
            name[:44], r["lado"], len(r["refs"]), r["como"], r["erro_max_mm"], changed, r["deslocamento_mm"]))
    print("pecas no CPL:", len(rows), "| sem footprint da EasyEDA:", failed, "| a olhar na previa:", ambiguous)
    json.dump({"pecas": len(rows), "sem_footprint": failed, "ambiguas": ambiguous, "footprints": report},
              open(os.path.join(HERE, "cpl_jlc.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
