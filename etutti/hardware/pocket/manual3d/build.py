"""Rebuilds every picture of the Pocket's assembly manual, end to end:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe build.py [shot ...] [--fast]

Adapted from etutti/hardware/manual3d/build.py (the eTuttino's, unchanged):

1. kicad-cli: the four Pocket boards (pcb/kicad) -> build/*.glb
2. parts.py: parts library + where each instance, cable and board goes
3. Blender: render_blender.py -> build/shots/*.png + *.json
4. annotate.py: balloons, arrows, dimensions, crop -> etutti/pocket/manual/img/*.jpg
5. the boards' own KiCad renders (pcb/fab/*.png) -> img/board_*.jpg

Needs KiCad 10, Blender 5 (BLENDER, default the Steam install) and this
CadQuery venv. With shot names only those are re-rendered; --fast renders
at a third of the size with few samples.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
BLENDER = os.environ.get("BLENDER", "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe")
IMG = os.path.normpath(os.path.join(POCKET, "..", "..", "pocket", "manual", "img"))


def run(cmd):
    print(">", " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)))
    subprocess.run(cmd, check=True)


def glb(board):
    run([KICAD_CLI, "pcb", "export", "glb", "-f", "--user-origin", "0x0mm", "--include-pads", "--include-silkscreen",
         "--include-soldermask", "-o", os.path.join(BUILD, board + ".glb"),
         os.path.join(POCKET, "pcb", "kicad", board + ".kicad_pcb")])


def boards():
    from PIL import Image
    sys.path.insert(0, HERE)
    from annotate import content_box
    os.makedirs(IMG, exist_ok=True)
    for src, dst in (("pocket_top", "board_top"), ("pocket_bottom", "board_bottom"),
                     ("pocket_panel_top", "panel_top"), ("pocket_panel_bottom", "panel_bottom")):
        im = Image.open(os.path.join(POCKET, "pcb", "fab", src + ".png")).convert("RGB")
        im = im.crop(content_box(im, im.getpixel((2, 2)), 20))
        im.save(os.path.join(IMG, dst + ".jpg"), quality=88, optimize=True)
        sm = min(1000, im.width)
        im.resize((sm, round(im.height * sm / im.width)), Image.LANCZOS).save(
            os.path.join(IMG, dst + "-sm.jpg"), quality=84, optimize=True)


def main():
    args = sys.argv[1:]
    os.makedirs(BUILD, exist_ok=True)
    for b in ("pocket", "pocket_controls", "pocket_pot", "pocket_panel"):
        glb(b)
    run([sys.executable, os.path.join(HERE, "parts.py")])
    run([BLENDER, "-b", "--python", os.path.join(HERE, "render_blender.py"), "--", *args])
    run([sys.executable, os.path.join(HERE, "annotate.py"), *[a for a in args if not a.startswith("--")]])
    boards()


if __name__ == "__main__":
    main()
