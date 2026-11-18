"""eTutti Student V3: the V2 and the V3 side by side (same camera), to see the exposed keyboard (SPEC v4 item 12).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/case/render_comparacao.py

Loads the V2's render.py as a module (its own out/ and the V2's case.json), draws both closed instruments with the
same camera, writes renders/comparacao_v2_v3.png (V2 left, V3 right) and a side view of both.
"""
import importlib.util
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(HERE, "renders")
V2 = os.path.normpath(os.path.join(HERE, "..", "..", "student_v02", "case", "render.py"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.join(os.path.dirname(path), ".."))
    spec.loader.exec_module(m)
    return m


def main():
    os.makedirs(REN, exist_ok=True)
    v2 = load(V2, "render_v2")
    v3 = load(os.path.join(HERE, "render.py"), "render_v3")
    v2.REN = REN
    cx, cy = 126.0, -50.0
    for tag, m in (("v2", v2), ("v3", v3)):
        S = m.scene()
        m.REN = REN
        m.shot(S, "iso_%s.png" % tag, [(cx - 190, cy - 300, 250), (cx, cy + 5, 5), (0, 0, 1)], size=(1600, 1000), parallel=False, zoom=1.35)
        # side view from the front (the player): the case's height and the buttons' height
        m.shot(S, "frente_%s.png" % tag, [(cx, -400, 8), (cx, 0, 8), (0, 0, 1)], size=(2000, 700), scale=24)
    for kind, out in (("iso", "comparacao_v2_v3.png"), ("frente", "comparacao_frente_v2_v3.png")):
        a = Image.open(os.path.join(REN, "%s_v2.png" % kind))
        b = Image.open(os.path.join(REN, "%s_v3.png" % kind))
        if kind == "iso":
            W = a.width + b.width
            img = Image.new("RGB", (W, a.height + 50), (243, 241, 236))
            img.paste(a, (0, 50))
            img.paste(b, (a.width, 50))
        else:
            img = Image.new("RGB", (a.width, a.height * 2 + 100), (243, 241, 236))
            img.paste(a, (0, 50))
            img.paste(b, (0, a.height + 100))
        d = ImageDraw.Draw(img)
        d.text((20, 15), "V2: tampo em z 18.2, poco de 5.25 mm, case de 28.3 mm", fill=(0, 0, 0))
        if kind == "iso":
            d.text((a.width + 20, 15), "V3 (SPEC v4): tampo em z 14.5, poco de 1.55 mm, case de 24.6 mm", fill=(0, 0, 0))
        else:
            d.text((20, a.height + 65), "V3 (SPEC v4): tampo em z 14.5, poco de 1.55 mm, case de 24.6 mm", fill=(0, 0, 0))
        img.save(os.path.join(REN, out))
        print(out)


if __name__ == "__main__":
    main()
