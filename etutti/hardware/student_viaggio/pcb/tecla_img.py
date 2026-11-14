"""Draw one electrode (img/tecla.png) from footprints.comb_shapes(): yellow = GND, orange = signal.

    python etutti/hardware/student_viaggio/pcb/tecla_img.py        (needs Pillow)
"""
import math
import os

from PIL import Image, ImageDraw

import footprints as F

HERE = os.path.dirname(os.path.abspath(__file__))
S, R = 60.0, 8.0                    # pixels per mm, half the picture in mm
COL = {"1": (230, 200, 40), "2": (240, 120, 60)}


def P(x, y):
    return ((x + R) * S, (y + R) * S)


def main():
    img = Image.new("RGB", (int(2 * R * S), int(2 * R * S)), (92, 110, 58))
    d = ImageDraw.Draw(img)
    k = F.COMB_KEEPOUT_R
    d.ellipse([P(-k, -k), P(k, k)], fill=(32, 58, 42))
    for pad, kind, cx, cy, w, h, ang, _exposed in F.comb_shapes():
        if kind == "circle":
            d.ellipse([P(cx - w / 2, cy - w / 2), P(cx + w / 2, cy + w / 2)], fill=COL[pad])
            continue
        a = math.radians(-ang)
        ux, uy = math.cos(a), math.sin(a)
        if kind == "oval":          # a round-ended stroke along its long axis
            l = (w - h) / 2
            d.line([P(cx - ux * l, cy - uy * l), P(cx + ux * l, cy + uy * l)], fill=COL[pad], width=int(h * S))
            for s in (-1, 1):
                q = (cx + s * ux * l, cy + s * uy * l)
                d.ellipse([P(q[0] - h / 2, q[1] - h / 2), P(q[0] + h / 2, q[1] + h / 2)], fill=COL[pad])
        else:
            d.rectangle([P(cx - w / 2, cy - h / 2), P(cx + w / 2, cy + h / 2)], fill=COL[pad])
    vx, vy = F.COMB_VIA
    d.ellipse([P(vx - 0.15, vy - 0.15), P(vx + 0.15, vy + 0.15)], fill=(0, 0, 0))     # the via's drill
    img.save(os.path.join(HERE, "..", "img", "tecla.png"))


if __name__ == "__main__":
    main()
