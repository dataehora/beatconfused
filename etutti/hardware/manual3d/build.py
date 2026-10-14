"""Rebuilds every picture of the assembly manual, end to end:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe build.py [shot ...] [--fast]

1. kicad-cli: the main board and the controls board (J1 only) -> build/*.glb
2. parts.py: the parts library and where each instance goes -> build/lib, build/assembly.json
3. Blender: render_blender.py -> build/shots/*.png + *.json
4. annotate.py: balloons, arrows, crop -> etutti/manuais/img/*.jpg
5. KiCad's own top/bottom renders of the main board (fab/) -> img/board_{top,bottom}.jpg

Needs: KiCad 10, Blender 5 (Cycles; set BLENDER if it isn't the Steam
install below), and this CadQuery venv. With shot names only those are
re-rendered; --fast renders at a third of the size with few samples.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BUILD = os.path.join(HERE, "build")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
BLENDER = os.environ.get("BLENDER", "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe")
IMG = os.path.normpath(os.path.join(HW, "..", "manuais", "img"))


def run(cmd):
    print(">", " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)))
    subprocess.run(cmd, check=True)


def glb(board, out, *extra):
    run([KICAD_CLI, "pcb", "export", "glb", "-f", "--user-origin", "0x0mm", "--include-pads", "--include-silkscreen",
         "--include-soldermask", *extra, "-o", os.path.join(BUILD, out),
         os.path.join(HW, "kicad", board + ".kicad_pcb")])


def boards():
    from PIL import Image
    sys.path.insert(0, HERE)
    from annotate import content_box
    for side in ("top", "bottom"):
        im = Image.open(os.path.join(HW, "fab", "etuttino_%s.png" % side)).convert("RGB")
        bg = im.getpixel((2, 2))
        im = im.crop(content_box(im, bg, 20))
        im.save(os.path.join(IMG, "board_%s.jpg" % side), quality=88, optimize=True)
        im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS).save(
            os.path.join(IMG, "board_%s-sm.jpg" % side), quality=84, optimize=True)


def main():
    args = sys.argv[1:]
    os.makedirs(BUILD, exist_ok=True)
    glb("etuttino", "main.glb")
    glb("etuttino_controls", "controls.glb", "--component-filter", "J1")
    run([sys.executable, os.path.join(HERE, "parts.py")])
    run([BLENDER, "-b", "--python", os.path.join(HERE, "render_blender.py"), "--", *args])
    run([sys.executable, os.path.join(HERE, "annotate.py"), *[a for a in args if not a.startswith("--")]])
    boards()


if __name__ == "__main__":
    main()
