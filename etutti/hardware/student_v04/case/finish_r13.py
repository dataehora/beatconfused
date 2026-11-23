"""eTutti Student V4 (R13V4): lays the Blender renders on the page's paper colour, draws the numbered balloons, writes the JPEGs the page serves.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v04/case/finish_r13.py [name ...]

Reads case/blender/out/<shot>.png (RGBA, transparent) and <shot>.json (anchors: fraction of width / height). Writes
  etutti/studentV4/img/foto_instrumento.jpg, foto_explodido.jpg, passo_1.jpg ... passo_11.jpg
and updates img/tamanhos.json. Balloon numbers are the parts' numbers in FIT_CHECK.md (R13V4 section, "Peças numeradas").
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "blender", "out")
IMG = os.path.normpath(os.path.join(HERE, "..", "..", "..", "studentV4", "img"))
PAPER = (0xF3, 0xF1, 0xEC, 255)
WIDTH = 1700


def font(sz):
    for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def main():
    names = sys.argv[1:]
    p = os.path.join(IMG, "tamanhos.json")
    sizes = json.load(open(p)) if os.path.exists(p) else {}
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".png"):
            continue
        name = f[:-4]
        if names and name not in names:
            continue
        im = Image.open(os.path.join(OUT, f)).convert("RGBA")
        bg = Image.new("RGBA", im.size, PAPER)
        bg.alpha_composite(im)
        w = WIDTH
        h = round(im.height * w / im.width)
        bg = bg.convert("RGB").resize((w, h), Image.LANCZOS)
        jp = os.path.join(OUT, name + ".json")
        if os.path.exists(jp):
            anc = json.load(open(jp))
            d = ImageDraw.Draw(bg, "RGBA")
            fn = font(int(w * 0.017))
            rad = int(w * 0.0175)
            placed = []
            for n, (fx, fy) in sorted(anc.items(), key=lambda t: int(t[0])):
                x, y = fx * w, fy * h
                best = None
                for ang in (-50, -130, 50, 130, -90, 90, 0, 180, -20, 200, -160, 20):
                    for dist in (rad * 2.4, rad * 3.4):
                        bx, by = x + dist * math.cos(math.radians(ang)), y + dist * math.sin(math.radians(ang))
                        if not (rad < bx < w - rad and rad < by < h - rad):
                            continue
                        if all(math.hypot(bx - qx, by - qy) > rad * 2.3 for qx, qy in placed):
                            best = (bx, by)
                            break
                    if best:
                        break
                bx, by = best or (x + rad * 2.4, y - rad * 2.4)
                placed.append((bx, by))
                d.line([(x, y), (bx, by)], fill=(40, 40, 38, 255), width=max(2, w // 700))
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(40, 40, 38, 255))
                d.ellipse([bx - rad, by - rad, bx + rad, by + rad], fill=(255, 255, 255, 235), outline=(40, 40, 38, 255), width=max(2, w // 650))
                tw = d.textbbox((0, 0), n, font=fn)
                d.text((bx - (tw[2] - tw[0]) / 2 - tw[0], by - (tw[3] - tw[1]) / 2 - tw[1]), n, font=fn, fill=(20, 20, 20, 255))
        out = os.path.join(IMG, name + ".jpg")
        bg.save(out, quality=88, optimize=True, progressive=True)
        sizes[name] = [w, h]
        print(name, w, h)
    json.dump(sizes, open(p, "w"), indent=1)


if __name__ == "__main__":
    main()
