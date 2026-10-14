"""Pictures and numbers for the /etutti/models/ page, from the case model:

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe models_render.py

reads out/*.stl (case.py, keycap.py) and renders/*.png (render.py) and
writes into etutti/models/img/:
  seixo_{iso,top,left}.jpg, madeira_{iso,top,left}.jpg  (+ -sm copies)
  anatomy.jpg     the Seixo in perspective with numbered call-outs (the
                  page lists what each number is, per language)
  keycaps.jpg     the three button caps, Seixo and Madeira colours
and prints the measurements the page quotes (size, heights, case weight).
"""
import json
import os
import sys

import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import render as R  # noqa: E402

IMG = os.path.normpath(os.path.join(HERE, "..", "..", "models", "img"))
F = lambda y: C.WIDTH - y      # SPEC y -> file y

# densities (g/cm3) for the weight estimate
DENSITY = {"seixo": 1.15, "madeira": 0.75}   # SLA/MJF resin ~1.1-1.2; white oak, dry ~0.75


def jpg(src, name, sm_width=900):
    im = crop_bg(Image.open(src)).convert("RGB")
    im.save(os.path.join(IMG, name + ".jpg"), quality=86, optimize=True)
    h = round(im.height * sm_width / im.width)
    im.resize((sm_width, h), Image.LANCZOS).save(os.path.join(IMG, name + "-sm.jpg"), quality=82, optimize=True)


def crop_bg(im, pad=30):
    """Crops a render to its content (anything that isn't the background)."""
    a = np.asarray(im.convert("RGB")).astype(int)
    bg = np.array([int(R.BG[i:i + 2], 16) for i in (1, 3, 5)])
    mask = np.abs(a - bg).sum(axis=2) > 12
    ys, xs = np.where(mask)
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.width), min(ys.max() + pad, im.height))
    return im.crop(box)


# Call-outs on the perspective view: (number, SPEC x, y, z). The page's
# legend says what each one is.
CALLOUTS = [
    (1, 200.0, 8.0, C.Z_DECK),                              # keyboard area (deck behind row 4)
    (2, 298.25 + 24.5, C.ROW_Y[2], C.Z_DECK - 1.0),         # chamfer at the right vertex
    (3, 35.0, 18.0, C.Z_IF),                                # screen / engraving zone
    (4, C.VOLUME_XY[0], C.VOLUME_XY[1], C.Z_IF + 7.0),      # volume knob
    (5, C.SELECT_XY[0], C.SELECT_XY[1], C.Z_IF + 7.0),      # instrument selector
    (6, C.LED_XY[0], C.LED_XY[1], C.Z_IF),                  # LED
    (7, 30.0, 80.0, C.z_interface(80.0)),                   # grille at 13 deg
    (8, 0.0, C.USB_YZ[0], C.USB_YZ[1]),                     # micro-USB, left face
    (9, 0.0, C.JACK_YZ[0], C.JACK_YZ[1]),                   # headphones, left face
    (10, 72.0, 30.0, 25.0),                                 # the ramp
]


def anatomy():
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1000))
    pl.set_background(R.BG)
    R.scene("seixo", pl)
    pl.enable_anti_aliasing("ssaa")
    c = (168.0, 50.0, 15.0)
    pl.camera_position = [(-95.0, -230.0, 230.0), c, (0, 0, 1)]
    pl.camera.view_angle = 30
    pl.add_light(pv.Light(position=(-200, -300, 400), focal_point=c, intensity=0.35))
    path = os.path.join(HERE, "renders", "models_anatomy_raw.png")
    pl.screenshot(path)
    ren = pl.renderer
    pts = []
    for n, x, y, z in CALLOUTS:
        ren.SetWorldPoint(x, F(y), z, 1.0)
        ren.WorldToDisplay()
        dx, dy, _ = ren.GetDisplayPoint()
        pts.append((n, dx, 1000 - dy))
    pl.close()
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arialbd.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    # leader: from the point up/out to a badge
    offsets = {1: (0, -90), 2: (60, -70), 3: (-40, -110), 4: (-70, -90), 5: (-10, -110), 6: (50, -100),
               7: (-90, 70), 8: (-110, 30), 9: (-110, 70), 10: (50, -150)}
    for n, x, y in pts:
        ox, oy = offsets[n]
        bx, by = x + ox, y + oy
        d.line([(x, y), (bx, by)], fill="#8a2d1c", width=3)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill="#8a2d1c")
        r = 22
        d.ellipse([bx - r, by - r, bx + r, by + r], fill="#8a2d1c", outline="white", width=3)
        d.text((bx, by), str(n), fill="white", font=font, anchor="mm")
    im = crop_bg(im)
    im.save(os.path.join(HERE, "renders", "models_anatomy.png"))
    os.remove(path)
    return os.path.join(HERE, "renders", "models_anatomy.png")


def keycaps():
    pl = pv.Plotter(off_screen=True, window_size=(1800, 900))
    pl.set_background(R.BG)
    caps = {k: pv.read(os.path.join(C.OUT, "keycap_%s.stl" % k)) for k in ("natural", "sharp", "cf")}
    for row, version in enumerate(("seixo", "madeira")):
        look = R.LOOK[version]
        for i, kind in enumerate(("natural", "sharp", "cf")):
            m = caps[kind].copy()
            b = m.bounds
            m.translate((i * 24.0 - (b[0] + b[1]) / 2, row * -24.0 - (b[2] + b[3]) / 2, -b[4]), inplace=True)
            pl.add_mesh(m, color=look[kind], specular=0.5 if version == "madeira" else 0.3, specular_power=30)
    pl.enable_anti_aliasing("ssaa")
    c = (24.0, -12.0, 3.0)
    pl.camera_position = [(24.0, -300.0, 170.0), c, (0, 0, 1)]
    pl.camera.view_angle = 11
    pl.add_light(pv.Light(position=(-60, -100, 120), focal_point=c, intensity=0.4))
    path = os.path.join(HERE, "renders", "models_keycaps.png")
    pl.screenshot(path)
    pl.close()
    crop_bg(Image.open(path)).save(path)
    return path


def measurements():
    out = {}
    for v, parts in (("seixo", ("seixo_tampa", "seixo_fundo")), ("madeira", ("madeira_corpo", "madeira_fundo"))):
        vol = sum(abs(pv.read(os.path.join(C.OUT, p + ".stl")).volume) for p in parts) / 1000.0   # cm3
        out[v] = {"volume_cm3": round(vol, 1), "grams": round(vol * DENSITY[v])}
    b = pv.read(os.path.join(C.OUT, "seixo_tampa.stl")).bounds
    out["size_mm"] = [round(b[1] - b[0], 1), round(b[3] - b[2], 1), round(b[5] - b[4], 1)]
    out["z_key_top"] = C.Z_KEY_TOP
    out["z_deck"] = C.Z_DECK
    out["z_interface"] = C.Z_IF
    return out


def main():
    os.makedirs(IMG, exist_ok=True)
    for v in ("seixo", "madeira"):
        for view in ("iso", "top", "left"):
            jpg(os.path.join(HERE, "renders", "%s_%s.png" % (v, view)), "%s_%s" % (v, view))
    jpg(anatomy(), "anatomy", 1100)
    jpg(keycaps(), "keycaps", 900)
    print(json.dumps(measurements(), indent=1))


if __name__ == "__main__":
    main()
