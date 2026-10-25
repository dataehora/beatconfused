"""Review pictures of a board region: kicad-cli SVG export -> cropped -> PNG (PyMuPDF, CadQuery venv).

    python etutti/hardware/viaggio_micromod/pcb/snap.py BOARD.kicad_pcb OUT.png LAYERS x0 y0 x1 y1 [px_per_mm]

Plain CPython. LAYERS like "F.Cu,B.Cu,Edge.Cuts". The crop is in board mm.
Kept from the Viaggio v2.1 for board review pictures (step M2/M3).
"""
import os
import re
import subprocess
import sys
import tempfile

KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PYMUPDF_PY = "C:/Users/julia/.venvs/cadquery/Scripts/python.exe"


def snap(board, out, layers, x0, y0, x1, y1, ppm=40, theme=None):
    tmp = tempfile.mkdtemp(prefix="viaggio_micromod_snap_")
    svg = os.path.join(tmp, "b.svg")
    cmd = [KICAD_CLI, "pcb", "export", "svg", "--layers", layers, "--mode-single", "--page-size-mode", "0",
           "--exclude-drawing-sheet", "--output", svg, board]
    subprocess.run(cmd, check=True, capture_output=True)
    s = open(svg, encoding="utf-8").read()
    # page mode 0: the SVG user units are mm of the page, the board drawn at its own coordinates
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', s)
    w, h = (x1 - x0), (y1 - y0)
    s = s.replace(m.group(0), 'viewBox="%g %g %g %g"' % (x0, y0, w, h), 1)
    s = re.sub(r'width="[\d.]+(mm|cm|in)?"', 'width="%gmm"' % w, s, count=1)
    s = re.sub(r'height="[\d.]+(mm|cm|in)?"', 'height="%gmm"' % h, s, count=1)
    open(svg, "w", encoding="utf-8").write(s)
    # rasterise with PyMuPDF (the CadQuery venv has it); white background
    code = ("import pymupdf,sys; d=pymupdf.open(sys.argv[1]); p=d[0]; "
            "pix=p.get_pixmap(alpha=False, dpi=int(float(sys.argv[3]))); pix.save(sys.argv[2])")
    subprocess.run([PYMUPDF_PY, "-c", code, svg, os.path.abspath(out), str(ppm * 25.4)],
                   check=True, capture_output=True)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    snap(a[0], a[1], a[2], *[float(v) for v in a[3:7]], ppm=float(a[7]) if len(a) > 7 else 40)
