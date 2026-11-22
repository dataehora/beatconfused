"""Draws a few OLED screens of the Student V4 (R6V4 item 7) with the real font data of oled_font.h, in pt and en.
Layout numbers are the ones of drawMenu()/drawStatus() in the sketch. Needs Pillow. Writes student_v04/img/tela_pt.png and tela_en.png."""
import os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
H = open(os.path.join(HERE, "..", "..", "etutti_synth", "oled_font.h"), encoding="utf-8").read()
ASCII = {}
EXT = {}
for m in re.finditer(r"\{(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4})\},\s+// (.*)", H):
    ASCII[len(ASCII)] = [int(x, 16) for x in m.groups()[:5]]
for m in re.finditer(r"\{(0x[0-9A-F]{4}),\{(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4})\}\},", H):
    v = [int(x, 16) for x in m.groups()]
    EXT[v[0]] = v[1:]


class Oled:
    def __init__(self):
        self.p = [[0] * 128 for _ in range(64)]

    def rect(self, x, y, w, h, on):
        for j in range(h):
            for i in range(w):
                if 0 <= x + i < 128 and 0 <= y + j < 64:
                    self.p[y + j][x + i] = 1 if on else 0

    def text(self, x, y, s, scale=1, on=True):
        for ch in s:
            cp = ord(ch)
            g = ASCII[cp - 32] if 32 <= cp <= 126 else EXT.get(cp, ASCII[ord("?") - 32])
            for c in range(5):
                for r in range(10):
                    if g[c] >> r & 1:
                        self.rect(x + c * scale, y + r * scale, scale, scale, on)
            x += 6 * scale

    def right(self, xr, y, s, on=True):
        self.text(xr - 6 * len(s), y, s, 1, on)

    def img(self, k=4):
        im = Image.new("RGB", (128 * k + 8, 64 * k + 8), (40, 40, 40))
        px = im.load()
        for y in range(64):
            for x in range(128):
                col = (120, 200, 255) if self.p[y][x] else (0, 0, 0)
                for dy in range(k):
                    for dx in range(k):
                        px[4 + x * k + dx, 4 + y * k + dy] = col
        return im


def menu(title, count, cur, lines):
    o = Oled()
    o.rect(0, 0, 128, 10, True)
    o.text(2, 0, title, 1, False)
    o.right(126, 0, "%d/%d" % (cur + 1, count), False)
    for r, (name, kind, val, fill) in enumerate(lines):
        y = 11 + r * 10
        sel = r == cur
        if sel:
            o.rect(0, y, 128, 10, True)
        o.text(2, y, name, 1, not sel)
        if kind == "sub":
            o.right(126, y, ">", not sel)
        else:
            if kind == "lvl":
                on = not sel
                o.rect(70, y + 3, 19, 1, on); o.rect(70, y + 8, 19, 1, on)
                o.rect(70, y + 3, 1, 6, on); o.rect(88, y + 3, 1, 6, on)
                o.rect(72, y + 5, fill, 2, on)
            o.right(126, y, val, not sel)
    return o


def status(t):
    o = Oled()
    o.text(0, 0, "BAT 85%", 2)
    o.text(0, 20, "VIOLIN", 2)
    o.text(0, 41, t["vol"])
    o.right(127, 41, t["voice"])
    o.rect(0, 54, 82, 1, True); o.rect(0, 63, 82, 1, True); o.rect(0, 54, 1, 10, True); o.rect(81, 54, 1, 10, True)
    o.rect(2, 56, 66, 6, True)
    o.text(86 if t["nomic"] else 88, 54, t["mic"])
    if not t["nomic"]:
        o.rect(112, 56, 8, 6, True)
    return o


def warning(t):
    o = Oled()
    o.rect(0, 0, 128, 64, True); o.rect(2, 2, 124, 60, False)
    o.text((128 - 12 * len(t[0])) // 2, 2, t[0], 2)
    for i, s in enumerate(t[1:]):
        o.text(4, [24, 34, 44, 52][i], s)
    return o


SETS = {
    "pt": dict(
        screens=[
            menu("Menu", 5, 0, [("Voz", "sub", "", 0), ("Captação", "sub", "", 0), ("Saída", "sub", "", 0), ("Som", "sub", "", 0), ("Sistema", "sub", "", 0)]),
            menu("Menu > Voz", 9, 3, [("Voz seca", "lvl", "20%", 3), ("Harmoniz.", "lvl", "55%", 8), ("Modo harm.", "enum", "Ajuda", 0), ("Intensidade", "lvl", "63%", 9), ("Oitava", "enum", "Perto", 0)]),
            menu("Menu > Captação", 10, 0, [("Ganho mic", "lvl", "26 dB", 3), ("Limiar", "lvl", "25%", 4), ("Razão", "enum", "Forte", 0), ("Retenção", "lvl", "78 ms", 6), ("Mic headset", "enum", "", 0)]),
            menu("Menu > Sistema", 5, 4, [("Salvar", "x", "", 0), ("Zerar voz", "x", "", 0), ("Calibrar", "x", "", 0), ("Teste tec.", "enum", "Desligado", 0), ("Idioma", "enum", "Português", 0)]),
            status(dict(vol="vol 90 fone", voice="voz C#4", mic="mic", nomic=False)),
            status(dict(vol="vol 90 alto", voice="sem mic", mic="sem mic", nomic=True)),
            warning(["Aviso", "Voz no alto-falante", "Pode dar microfonia", "Mic perto da boca e", "volume baixo"]),
        ]),
    "en": dict(
        screens=[
            menu("Menu", 3, 0, [("Output", "sub", "", 0), ("Sound", "sub", "", 0), ("System", "sub", "", 0)]),
            menu("Menu > Voice", 9, 3, [("Dry voice", "lvl", "20%", 3), ("Harmonizer", "lvl", "55%", 8), ("Harm mode", "enum", "Assist", 0), ("Strength", "lvl", "63%", 9), ("Octave", "enum", "Near", 0)]),
            menu("Menu > Input", 10, 0, [("Mic gain", "lvl", "26 dB", 3), ("Threshold", "lvl", "25%", 4), ("Ratio", "enum", "Hard", 0), ("Hold", "lvl", "78 ms", 6), ("Headset mic", "enum", "", 0)]),
            menu("Menu > System", 5, 4, [("Save", "x", "", 0), ("Reset voice", "x", "", 0), ("Calibrate", "x", "", 0), ("Key test", "enum", "Off", 0), ("Language", "enum", "English", 0)]),
            status(dict(vol="vol 90 hp", voice="voice C#4", mic="mic", nomic=False)),
            status(dict(vol="vol 90 spk", voice="no mic", mic="no mic", nomic=True)),
            warning(["Warning", "Voice on speaker", "May cause feedback", "Mic at the mouth and", "volume low"]),
        ]),
}

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", "hardware", "student_v04", "img")
os.makedirs(out, exist_ok=True)
for lang, d in SETS.items():
    ims = [o.img(3) for o in d["screens"]]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 2, h * 4), (40, 40, 40))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 2) * w, (i // 2) * h))
    sheet.save(os.path.join(out, "tela_%s.png" % lang))
    print("wrote", os.path.join(out, "tela_%s.png" % lang))
