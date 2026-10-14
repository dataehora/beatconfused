"""Finishes the Blender shots for the manual (any Python with Pillow):

    python annotate.py [shot ...]

For each build/shots/<name>.png + .json: puts the photo-like renders on
the page colour (they come with a transparent background and a caught
shadow), draws the motion arrows and the numbered balloons (numbers
only: the manual's parts list names them in each language), crops to
the drawing and writes etutti/manuais/img/<name>.jpg plus a -sm copy.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "build", "shots")
IMG = os.environ.get("MANUAL_IMG") or os.path.normpath(os.path.join(HERE, "..", "..", "manuais", "img"))
BG = (247, 245, 240)
INK = (34, 30, 27)
ARROW = (196, 74, 36)
SS = 2                 # draw at 2x, then downsample: smooth lines


def font(px):
    for f in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default()


def content_box(im, bg, pad):
    px = im.convert("RGB").load()
    w, h = im.size
    xs, ys = [], []
    step = max(1, w // 600)
    for y in range(0, h, step):
        for x in range(0, w, step):
            p = px[x, y]
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 18:
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0, 0, w, h)
    return (max(min(xs) - pad, 0), max(min(ys) - pad, 0), min(max(xs) + pad, w), min(max(ys) + pad, h))


def arrow(d, a, b, width, colour):
    (x0, y0), (x1, y1) = a, b
    ang = math.atan2(y1 - y0, x1 - x0)
    head = width * 4.2
    bx, by = x1 - head * 0.8 * math.cos(ang), y1 - head * 0.8 * math.sin(ang)
    d.line([(x0, y0), (bx, by)], fill=colour, width=int(width))
    left = (x1 - head * math.cos(ang - 0.42), y1 - head * math.sin(ang - 0.42))
    right = (x1 - head * math.cos(ang + 0.42), y1 - head * math.sin(ang + 0.42))
    d.polygon([(x1, y1), left, right], fill=colour)


def finish(name):
    meta = json.load(open(os.path.join(SHOTS, name + ".json")))
    src = Image.open(os.path.join(SHOTS, name + ".png"))
    w, h = src.size
    if meta["mode"] == "real":
        base = Image.new("RGBA", src.size, BG + (255,))
        base.alpha_composite(src.convert("RGBA"))
        im = base.convert("RGB")
        bg = BG
    else:
        im = src.convert("RGB")
        bg = (255, 255, 255)
    # room round the picture for balloons pushed outwards
    m = int(max(w, h) * 0.12)
    canvas = Image.new("RGB", (w + 2 * m, h + 2 * m), bg)
    canvas.paste(im, (m, m))
    im = canvas
    shift = lambda p: [p[0] + m, p[1] + m]
    meta["arrows"] = [[shift(a), shift(b)] for a, b in meta.get("arrows", [])]
    meta["balloons"] = [[n, x + m, y + m] for n, x, y in meta.get("balloons", [])]
    w, h = im.size
    im = im.resize((w * SS, h * SS), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    unit = max(w, h) * SS / 1000.0          # 1/1000 of the picture's long side
    for a, b in meta.get("arrows", []):
        arrow(d, [v * SS for v in a], [v * SS for v in b], 4.0 * unit, ARROW)
    # balloons: pushed out from the drawing's centre along the anchor's direction
    box = content_box(im, bg, 0)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    r = 17 * unit
    f = font(int(r * 1.15))
    placed = []
    for n, x, y in meta.get("balloons", []):
        x, y = x * SS, y * SS
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        bx, by = x + dx / L * 70 * unit, y + dy / L * 70 * unit
        for px, py in placed:                 # nudge away from balloons already placed
            if math.hypot(bx - px, by - py) < 2.4 * r:
                by += 2.6 * r * (1 if by >= py else -1)
        placed.append((bx, by))
        d.line([(x, y), (bx, by)], fill=INK, width=int(2.2 * unit))
        d.ellipse([x - 3.5 * unit, y - 3.5 * unit, x + 3.5 * unit, y + 3.5 * unit], fill=INK)
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, 255, 255), outline=INK, width=int(2.6 * unit))
        d.text((bx, by + 0.5 * unit), str(n), fill=INK, font=f, anchor="mm")
    im = im.resize((w, h), Image.LANCZOS)
    im = im.crop(content_box(im, bg, int(max(w, h) * 0.02)))
    os.makedirs(IMG, exist_ok=True)
    im.save(os.path.join(IMG, name + ".jpg"), quality=88, optimize=True)
    sm = 1000
    if im.width > sm:
        im.resize((sm, round(im.height * sm / im.width)), Image.LANCZOS).save(
            os.path.join(IMG, name + "-sm.jpg"), quality=84, optimize=True)
    else:
        im.save(os.path.join(IMG, name + "-sm.jpg"), quality=84, optimize=True)
    print(name, im.size)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(SHOTS) if f.endswith(".json"))
    for n in names:
        finish(n)
