"""R13V4 item 1: the 32-key fit check again with the ORIGINAL JST SM06B / SM04B bodies (8.0 x 4.95 x 2.91 and 6.0 x 4.95 x 2.91, electronics' MODELOS_3D / datasheet).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/verifica_jst_r13.py   (~90 s)

The case models a header as 9.4 wide (footprint with the hold-downs) x 4.85 deep x 2.95 high, mouth 0.5 mm past the ruler's back edge, and keeps 5.55 mm of
footprint in the tray's notches. The original body is narrower (8.0), shorter (2.91) and 0.10 mm DEEPER (4.95): only the depth can grow. This run sets HDR_D = 4.95
(and keeps 9.4 / 2.95 as the envelope) and the board's SH headers at the TALL table's 4.25 mm, writes into a scratch folder (the official out/ is untouched) and prints
every non-zero interference of the connector, cable and interface tables.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_r4 as L    # noqa: E402
L.HDR_D = 4.95
import case_r4 as C4     # noqa: E402
tmp = os.path.join(tempfile.gettempdir(), "jst_r13")
os.makedirs(tmp, exist_ok=True)
C4.OUT = tmp
info = C4.build(0)
I = info["interferencias_mm3"]
nz = {t: {k: v for k, v in d.items() if v} for t, d in I.items()}
print("NON-ZERO:", json.dumps(nz, ensure_ascii=False))
old = json.load(open(os.path.join(HERE, "out", "r4_32.json"), encoding="utf-8"))["interferencias_mm3"]
same = all(I[t] == old[t] for t in I)
print("IDENTICAL TO THE OFFICIAL r4_32.json:", same)
