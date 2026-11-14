"""eTutti Student V01: the board that is ordered.

It is the Viaggio J1 board (etutti/hardware/viaggio_j1/kicad/, routed and checked there) with one
change: the board name on both silkscreens. This script

  1. copies the J1's KiCad project (the files Git tracks) into student_v01/kicad/;
  2. replaces the two silkscreen texts, and checks the board file differs from the J1's in exactly
     those two lines;
  3. runs KiCad's DRC with schematic parity (must match the J1's result: 0 errors, 0 unconnected,
     parity 0, only the 3 accepted 0.12 mm EN_B segments);
  4. writes fab/: Gerbers + drill zip, JLCPCB BOM and CPL, the parts fitted at home, the plate's
     Gerbers, renders.

Run with KiCad's Python, from anywhere:
  "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/build.py

Nothing in viaggio_j1/ is written.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J1 = os.path.normpath(os.path.join(HERE, "..", "viaggio_j1"))
KICAD = os.path.join(HERE, "kicad")
BUILD = os.path.join(HERE, "build")
FAB = os.path.join(HERE, "fab")
NAME = "student_v01"
BOARD = os.path.join(KICAD, "viaggio_micromod.kicad_pcb")      # the project keeps the J1's name:
PLATE = os.path.join(KICAD, NAME + "_plate.kicad_pcb")         # the schematic stores it in every part
OLD_TEXT = '(gr_text "eTutti Viaggio MicroMod \u00b7 J1 \u00b7 SPEC v2.5"'
NEW_TEXT = '(gr_text "eTutti Student V01"'
ACCEPTED = {"track_width": 3}        # EN_B at U711, accepted in the Viaggio MicroMod SPEC v2.5

sys.path.insert(0, J1)
import pcbnew    # noqa: E402
import m3        # noqa: E402  (the J1's checks and fab export; its paths are redirected below)


def copy_project():
    files = subprocess.run(["git", "ls-files", "kicad"], cwd=J1, check=True,
                           capture_output=True, text=True).stdout.split()
    for d in (KICAD, BUILD, FAB):
        os.makedirs(d, exist_ok=True)
    for rel in files:
        name = os.path.relpath(rel, "kicad").replace("viaggio_j1_plate", NAME + "_plate")
        dst = os.path.join(KICAD, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(J1, rel), dst)
    return len(files)


def rename_board():
    raw = open(BOARD, "rb").read()
    old, new = OLD_TEXT.encode("utf-8"), NEW_TEXT.encode("utf-8")
    if raw.count(old) != 2:
        raise SystemExit("expected the J1 board name twice on the silkscreen, found %d" % raw.count(old))
    out = raw.replace(old, new)
    open(BOARD, "wb").write(out)
    a = open(os.path.join(J1, "kicad", "viaggio_micromod.kicad_pcb"), "rb").read().split(b"\n")
    b = out.split(b"\n")
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(a) != len(b) or len(changed) != 2:
        raise SystemExit("board differs from the J1's in %d lines, expected 2" % len(changed))
    return [i + 1 for i in changed]


def check():
    d, violations, unconnected, parity = m3.drc(NAME)
    if unconnected or parity or violations != ACCEPTED:
        raise SystemExit("DRC: %s, %d unconnected, parity %d" % (violations, unconnected, parity))
    return {"violacoes": violations, "ligacoes_faltando": unconnected, "paridade": parity}


def fab():
    b = pcbnew.LoadBoard(BOARD)
    rec = {"pedido": dict(m3.ORDER)}
    z, files = m3.gerbers(BOARD, NAME, m3.GERBER_LAYERS)
    rec["gerbers"] = {"zip": os.path.basename(z), "arquivos": files}
    rec.update(m3.bom_cpl(b))
    for kind in ("bom", "cpl", "fora_da_montagem"):
        os.replace(os.path.join(FAB, "viaggio_j1_%s.csv" % kind), os.path.join(FAB, "%s_%s.csv" % (NAME, kind)))
    fora = os.path.join(FAB, NAME + "_fora_da_montagem.csv")
    text = open(fora, encoding="utf-8").read().replace("viaggio_j1_plate", NAME + "_plate")
    open(fora, "w", encoding="utf-8", newline="").write(text)
    zp, _ = m3.gerbers(PLATE, NAME + "_plate", "F.Cu,B.Cu,F.Silkscreen,F.Mask,B.Mask,Edge.Cuts")
    rec["plate"] = os.path.basename(zp)
    rec["imagens"] = m3.renders(BOARD, NAME) + m3.renders(PLATE, NAME + "_plate", ("top",))
    return rec


def main():
    m3.BOARD, m3.BUILD, m3.FAB = BOARD, BUILD, FAB
    rec = {"arquivos_copiados": copy_project(), "linhas_mudadas": rename_board()}
    rec["drc"] = check()
    rec.update(fab())
    json.dump(rec, open(os.path.join(HERE, "build.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
