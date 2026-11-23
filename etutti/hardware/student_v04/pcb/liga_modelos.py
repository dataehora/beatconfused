"""Student V4 (R13V4, item 2.3): copies a routed board and links the EasyEDA STEP models (pcb/modelos_kicad.py) to its footprints; renders bottom and top. KiCad python.

    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/liga_modelos.py principal|r8
The routed boards themselves are not touched: the copies are kicad/student_v04_roteada_3d.kicad_pcb and kicad/regua/student_v04_regua8_roteada_3d.kicad_pcb.
Model paths are relative to the project folder (${KIPRJMOD}/../fornecimento/modelos3d/kicad/...); the models folder is outside Git (fornecimento/baixar_modelos.py + modelos_kicad.py).
"""
import json, os, subprocess, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
CFG = {"principal": ("kicad/student_v04_roteada.kicad_pcb", "kicad/student_v04_roteada_3d.kicad_pcb", "${KIPRJMOD}/../fornecimento/modelos3d/kicad/", ""),
       "r8": ("kicad/regua/student_v04_regua8_roteada.kicad_pcb", "kicad/regua/student_v04_regua8_roteada_3d.kicad_pcb", "${KIPRJMOD}/../../fornecimento/modelos3d/kicad/", "-1")}
KCLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"


def main(name):
    src, dst, pref, suf = CFG[name]
    m = json.load(open(os.path.join(HERE, "build", "modelos_kicad_%s.json" % name), encoding="utf-8"))
    b = pcbnew.LoadBoard(os.path.join(HW, src))
    n = 0
    for fp in b.GetFootprints():
        key = fp.GetReference() + suf
        for old in list(fp.Models()):
            pass
        fp.Models().clear()
        for fld in fp.GetFields():                      # the copy is for looking at: no field text over the bodies
            fld.SetVisible(False)
        if key in m:
            mod = pcbnew.FP_3DMODEL()
            mod.m_Filename = pref + m[key]
            mod.m_Show = True
            fp.Add3DModel(mod)
            n += 1
    pcbnew.SaveBoard(os.path.join(HW, dst), b)
    print(name, n, "footprints with a model ->", dst)
    for side in ("bottom", "top"):
        out = os.path.join(HERE, "img", "modelos3d_%s_%s.png" % (name, side))
        subprocess.run([KCLI, "pcb", "render", "--side", side, "--width", "2400", "--height", "2400" if name == "principal" else "800", "--quality", "basic", "--background", "opaque", "--output", out, os.path.join(HW, dst)], capture_output=True)
        print(out, os.path.exists(out))


if __name__ == "__main__":
    main(sys.argv[1])
