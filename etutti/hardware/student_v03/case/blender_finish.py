"""eTutti Student V3: lays the Blender renders on the page's paper colour and writes the JPEGs the page serves.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/blender_finish.py

Reads case/blender/out/r_*.png (RGBA, transparent background, from render_blender.py). Writes
  etutti/studentV3/img/foto_<name>.jpg      r_isometrico -> foto_isometrico.jpg, r_passo_4 -> foto_passo_4.jpg, ...
and adds their sizes to etutti/studentV3/img/tamanhos.json.
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "blender", "out")
IMG = os.path.normpath(os.path.join(HERE, "..", "..", "..", "studentV3", "img"))
PAPER = (0xF3, 0xF1, 0xEC, 255)
WIDTH = {"r_explodido": 1800, "r_isometrico": 1800}


def main():
    p = os.path.join(IMG, "tamanhos.json")
    sizes = json.load(open(p))
    for f in sorted(os.listdir(OUT)):
        if not (f.startswith("r_") and f.endswith(".png")):
            continue
        name = f[2:-4]
        im = Image.open(os.path.join(OUT, f)).convert("RGBA")
        bg = Image.new("RGBA", im.size, PAPER)
        bg.alpha_composite(im)
        w = WIDTH.get("r_" + name, 1500)
        h = round(im.height * w / im.width)
        bg.convert("RGB").resize((w, h), Image.LANCZOS).save(os.path.join(IMG, "foto_%s.jpg" % name), quality=88, optimize=True, progressive=True)
        sizes["foto_" + name] = [w, h]
        print(name, w, h)
    json.dump(sizes, open(p, "w"), indent=1)


if __name__ == "__main__":
    main()
