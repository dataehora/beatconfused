"""eTutti Student V4 (R13V4): the OLED screens, simulated from the firmware.

    python etutti/hardware/student_v04/telas_oled.py

Plain Python + Pillow. Reads etutti/firmware/student_v4/ (oled_font.h = the real glyphs; ui_text.h = the texts; student_v4.ino = the
menu tables ITEMS_*, the draw routines drawMenu / drawStatus / drawWarning, whose layout numbers are copied here) and writes
etutti/studentV4/img/tela_<name>_<pt|en>.png (128 x 64 enlarged 4x) plus img/telas.json (the catalogue, with the tree of the menu).
Nothing here runs on a real SSD1306: it is the firmware's own drawing code redone on a pixel grid.
When the menu or the texts change in the sketch, run this again; pagina.py reads telas.json.
"""
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.normpath(os.path.join(HERE, "..", "..", "firmware", "student_v4"))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "studentV4", "img"))
K = 4                               # zoom
LANGS = ["pt", "en"]                # LANG_PT, LANG_EN (ui_text.h)

FONT_H = open(os.path.join(FW, "oled_font.h"), encoding="utf-8").read()
INO = open(os.path.join(FW, "student_v4.ino"), encoding="utf-8").read()
UI = open(os.path.join(FW, "ui_text.h"), encoding="utf-8").read()

# ---------------------------------------------------------------- the font (oled_font.h)
ASCII, EXT = [], {}
_asc_part = FONT_H.split("OLED_FONT_EXT")[0]
for m in re.finditer(r"\{(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4})\},", _asc_part):
    ASCII.append([int(x, 16) for x in m.groups()])
assert len(ASCII) == 95, len(ASCII)
for m in re.finditer(r"\{(0x[0-9A-F]{4}),\{(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4}),(0x[0-9A-F]{4})\}\},", FONT_H):
    v = [int(x, 16) for x in m.groups()]
    EXT[v[0]] = v[1:]


def glyph(cp):
    if 32 <= cp <= 126:
        return ASCII[cp - 32]
    return EXT.get(cp, ASCII[ord("?") - 32])


# ---------------------------------------------------------------- texts and menu tables read from the sketch
def txt(body):
    """('"Voz", "Voice"') -> ['Voz', 'Voice'] (a missing language falls back to English, as tr() does)."""
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
    return parts


def txt_of(m):
    p = txt(m)
    return {"pt": p[0], "en": p[1] if len(p) > 1 else p[0]}


STR_NAMES = re.search(r"enum StrId \{(.*?)\};", UI, re.S).group(1)
STR_NAMES = [s.strip() for s in STR_NAMES.replace("\n", " ").split(",") if s.strip() and s.strip() != "S_COUNT"]
STR_BODY = re.search(r"const Txt STR\[S_COUNT\] = \{(.*?)\};", UI, re.S).group(1)
STR = {}
for name, m in zip(STR_NAMES, re.findall(r"\{(\"[^}]*)\}", STR_BODY)):
    STR[name] = txt_of(m)
assert len(STR) == len(STR_NAMES) and "S_SPEAKER_ON" in STR, (len(STR), len(STR_NAMES))


def table(name):
    body = re.search(r"const Txt %s\[\d+\] = \{(.*?)\};" % name, UI, re.S).group(1)
    return [txt_of(m) for m in re.findall(r"\{(\"[^}]*)\}", body)]


HARM_MODES, FOLD_NAMES, RATIO_NAMES = table("HARM_MODES"), table("FOLD_NAMES"), table("RATIO_NAMES")
MIC_TYPES, CURVES = table("MIC_TYPE_NAMES"), table("CURVE_NAMES")
LANG_NAMES = re.findall(r'"([^"]*)"', re.search(r"LANG_NAME\[LANG_COUNT\] = \{(.*?)\};", UI).group(1))
PAGES_ENUM = [s.strip() for s in re.search(r"enum \{ (PG_MAIN.*?) \};", UI).group(1).split(",") if s.strip() != "PG_COUNT"]
ITEM_RE = re.compile(r'\{\{(\"[^}]*)\}, (MK_\w+), (\w+), (true|false)\}')
ITEMS = {}
for pg in ("MAIN", "VOICE", "INPUT", "OUTPUT", "SOUND", "SYSTEM"):
    body = re.search(r"const MenuItem ITEMS_%s\[\] = \{(.*?)\};\n" % pg, INO, re.S).group(1)
    ITEMS["PG_" + pg] = [{"name": txt_of(a), "kind": b, "id": c, "needsMic": d == "true"} for a, b, c, d in ITEM_RE.findall(body)]
PAGE_TITLE = {}
for m in re.finditer(r"PAGE_OF\(\(Txt\{\{(\"[^}]*)\}\}\), ITEMS_(\w+)\)", INO):
    PAGE_TITLE["PG_" + m.group(2)] = txt_of(m.group(1))
REGISTER_NAMES = re.findall(r'"([A-Z]+)"', re.search(r"REGISTER_NAMES\[7\] = \{(.*?)\};", INO).group(1))
assert len(REGISTER_NAMES) == 7 and sum(len(v) for v in ITEMS.values()) == 5 + 12 + 10 + 6 + 3 + 6, [len(v) for v in ITEMS.values()]


# ---------------------------------------------------------------- the state the screens depend on (defaults of the sketch)
class St:
    def __init__(self, **kw):
        self.mic = True              # a microphone in IN (micPlugged)
        self.headphones = True
        self.usb = False
        self.charging = False
        self.battery = 85
        self.register = 2            # DEFAULT_REGISTER = MM = VIOLIN
        self.volume = 90
        self.resting = False
        # VoiceFx defaults
        self.voice, self.vocoder, self.harm, self.interval, self.echo, self.echoTime, self.echoFb, self.reverb = 0, 0, 0, 64, 0, 40, 40, 40
        self.gate, self.micGain = 32, 19
        self.gateAtk, self.gateHold, self.gateRel, self.gateRatio, self.hpf = 20, 50, 40, 2, 40
        self.antiFb, self.harmFollow, self.harmFold, self.speaker = False, False, True, False
        self.followMode, self.helpAmt, self.harm4 = 0, 80, False
        self.eq, self.eqCut, self.eqDip = True, 63, 63
        self.keysCC, self.ambience, self.curve, self.keyTest, self.micType = 127, 25, 2, False, 0
        self.lang = "pt"
        self.__dict__.update(kw)


def lround(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


LEVELS = {"M_VOICE_DRY": "voice", "M_VOCODER": "vocoder", "M_HARM": "harm", "M_HARM_INT": "interval", "M_HARM_HELP": "helpAmt",
          "M_ECHO": "echo", "M_ECHO_TIME": "echoTime", "M_ECHO_FB": "echoFb", "M_VOICE_REV": "reverb", "M_MIC_GAIN": "micGain",
          "M_GATE_THR": "gate", "M_GATE_ATK": "gateAtk", "M_GATE_HOLD": "gateHold", "M_GATE_REL": "gateRel", "M_HPF": "hpf",
          "M_KEYS_LEVEL": "keysCC", "M_EQ_CUT": "eqCut", "M_EQ_DIP": "eqDip", "M_AMBIENCE": "ambience", "M_VOLUME": "volume"}


def shown(it, s):                                     # menuShown()
    if it["needsMic"] and not s.mic:
        return False
    if it["kind"] == "MK_SUB":
        return True
    i = it["id"]
    if i == "M_HARM_INT":
        return not s.harmFollow
    if i == "M_HARM_HELP":
        return s.harmFollow and s.followMode == 1
    if i == "M_HARM_VOICES":
        return s.harmFollow
    if i == "M_HARM_FOLD":
        return s.harmFollow and s.followMode != 1
    return True


def lines_of(page, s):
    return [it for it in ITEMS[page] if shown(it, s)]


def value_text(it, s):                                # menuValueText()
    i, L = it["id"], s.lang
    g = lambda t: t[L]
    if i == "M_HARM_INT":
        return "%+d st" % lround((s.interval - 64) * 12.0 / 64.0)
    if i == "M_ECHO_TIME":
        return "%d ms" % lround(60.0 + s.echoTime * (680.0 / 127.0))
    if i == "M_MIC_GAIN":
        return "%d dB" % ((s.micGain * 60 + 63) // 127)
    if i == "M_MIC_TYPE":
        return g(MIC_TYPES[s.micType])
    if i == "M_GATE_ATK":
        return "%.1f ms" % (0.5 + s.gateAtk * s.gateAtk * (29.5 / 16129.0))
    if i == "M_GATE_HOLD":
        return "%d ms" % int(s.gateHold * s.gateHold * (500.0 / 16129.0))
    if i == "M_GATE_REL":
        return "%d ms" % int(20.0 + s.gateRel * s.gateRel * (980.0 / 16129.0))
    if i == "M_HPF":
        return "%d Hz" % int(60.0 + s.hpf * (340.0 / 127.0))
    if i == "M_EQ_CUT":
        return "%d Hz" % lround(150.0 + s.eqCut * (300.0 / 127.0))
    if i == "M_EQ_DIP":
        return "-%d dB" % lround(s.eqDip * (12.0 / 127.0))
    if i == "M_SPK_EQ":
        return STR["S_ON" if s.eq else "S_OFF"][L]
    if i == "M_HARM_MODE":
        return g(HARM_MODES[1 + s.followMode if s.harmFollow else 0])
    if i == "M_HARM_VOICES":
        return "4" if s.harm4 else "3"
    if i == "M_HARM_FOLD":
        return g(FOLD_NAMES[1 if s.harmFold else 0])
    if i == "M_GATE_RATIO":
        return g(RATIO_NAMES[s.gateRatio])
    if i == "M_ANTI_FB":
        return STR["S_ON" if s.antiFb else "S_OFF"][L]
    if i == "M_VOICE_OUT":
        return STR["S_SPEAKER_ON" if s.speaker else "S_PHONES"][L]
    if i == "M_REGISTER":
        return REGISTER_NAMES[s.register]
    if i == "M_VEL_CURVE":
        return g(CURVES[s.curve])
    if i == "M_KEY_TEST":
        return STR["S_ON" if s.keyTest else "S_OFF"][L]
    if i == "M_LANGUAGE":
        return LANG_NAMES[0 if L == "pt" else 1]
    if i in LEVELS:
        return "%d%%" % ((getattr(s, LEVELS[i]) * 100 + 63) // 127)
    return ""


# ---------------------------------------------------------------- the pixel grid and the drawing routines (the sketch's, line by line)
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
            g = glyph(ord(ch))
            for c in range(5):
                for r in range(10):
                    if g[c] >> r & 1:
                        self.rect(x + c * scale, y + r * scale, scale, scale, on)
            x += 6 * scale

    def right(self, xr, y, s, on=True):
        self.text(xr - 6 * len(s), y, s, 1, on)

    def image(self):
        im = Image.new("RGB", (128 * K + 16, 64 * K + 16), (28, 28, 30))
        px = im.load()
        for y in range(64):
            for x in range(128):
                on = self.p[y][x]
                col = (226, 240, 255) if on else (0, 6, 14)
                for dy in range(K - 1 if on else K):
                    for dx in range(K - 1 if on else K):          # a dark gap between lit pixels, as a real panel shows
                        px[8 + x * K + dx, 8 + y * K + dy] = col
        return im


def draw_menu(s, page, cursor, scroll, toast=None):
    o = Oled()
    L = s.lang
    o.rect(0, 0, 128, 10, True)
    if toast:
        o.text(2, 0, toast, 1, False)
    elif page == "PG_MAIN":
        o.text(2, 0, STR["S_MENU"][L], 1, False)
    else:
        o.text(2, 0, "%s > %s" % (STR["S_MENU"][L], PAGE_TITLE[page][L]), 1, False)
    lines = lines_of(page, s)
    o.right(126, 0, "%d/%d" % (cursor + 1, len(lines)), False)
    for r in range(5):
        idx = scroll + r
        if idx >= len(lines):
            break
        it = lines[idx]
        y = 11 + r * 10
        sel = idx == cursor
        if sel:
            o.rect(0, y, 128, 10, True)
        o.text(2, y, it["name"][L], 1, not sel)
        if it["kind"] == "MK_SUB":
            o.right(126, y, ">", not sel)
        elif it["kind"] == "MK_LEVEL":
            on = not sel
            fill = getattr(s, LEVELS[it["id"]]) * 15 // 127
            o.rect(70, y + 3, 19, 1, on)
            o.rect(70, y + 8, 19, 1, on)
            o.rect(70, y + 3, 1, 6, on)
            o.rect(88, y + 3, 1, 6, on)
            o.rect(72, y + 5, fill, 2, on)
            o.right(126, y, value_text(it, s), not sel)
        elif it["kind"] == "MK_ENUM":
            o.right(126, y, value_text(it, s), not sel)
    return o


def draw_warning(s, blink):
    o = Oled()
    L = s.lang
    if blink:
        o.rect(0, 0, 128, 64, True)
        o.rect(2, 2, 124, 60, False)
    else:
        o.rect(0, 0, 128, 1, True)
        o.rect(0, 63, 128, 1, True)
    w = 12 * len(STR["S_WARN_TITLE"][L])
    o.text((128 - w) // 2, 2, STR["S_WARN_TITLE"][L], 2, True)
    for y, k in ((24, "S_WARN_1"), (34, "S_WARN_2"), (44, "S_WARN_3"), (52, "S_WARN_4")):
        o.text(4, y, STR[k][L], 1, True)
    return o


def draw_status(s, voice_text="", mic_level=0):
    """drawStatus(): voice_text is what the sketch puts right of the volume line (the sketch computes it from the voice state)."""
    o = Oled()
    L = s.lang
    o.text(0, 0, "%s %d%%" % ("CHG" if s.charging else ("USB" if s.usb else "BAT"), s.battery), 2)
    o.text(0, 20, REGISTER_NAMES[s.register], 2)
    show_rest = s.resting and not voice_text
    line = "%s %d %s%s%s" % (STR["S_VOL"][L], s.volume, STR["S_HP" if s.headphones else "S_SPK"][L], " " if show_rest else "",
                            STR["S_REST"][L] if show_rest else "")
    o.text(0, 41, line)
    if voice_text:
        o.right(127, 41, voice_text)
    o.rect(0, 54, 82, 1, True)
    o.rect(0, 63, 82, 1, True)
    o.rect(0, 54, 1, 10, True)
    o.rect(81, 54, 1, 10, True)
    o.rect(2, 56, s.battery * 78 // 100, 6, True)
    if not s.mic:
        o.text(86, 54, STR["S_NO_MIC"][L])
    else:
        o.text(88, 54, STR["S_MIC"][L])
        o.rect(112, 56, mic_level * 2, 6, True)
    return o


# ---------------------------------------------------------------- the catalogue of screens
# each entry: (name, group, {pt, en caption}, builder(lang) -> Oled)
def build_catalogue():
    C = []

    def add(name, group, cap_pt, cap_en, fn):
        C.append({"name": name, "group": group, "caption": {"pt": cap_pt, "en": cap_en}, "fn": fn})

    def menu_fn(page, cursor, scroll=0, toast=None, **kw):
        def f(L):
            s = St(lang=L, **kw)
            t = STR[toast][L] if toast else None
            return draw_menu(s, page, cursor, scroll, t)
        return f

    # ---- status screens
    add("status", "status", "Tela comum: bateria, registro (MM = VIOLIN), volume, saída (alto-falante), sem microfone.",
        "The ordinary screen: battery, register (MM = VIOLIN), volume, output (speaker), no microphone.",
        lambda L: draw_status(St(lang=L, mic=False, headphones=False)))
    add("status_fone", "status", "Com fone no jack OUT: o texto da saída passa a \"fone\" e o alto-falante se cala.",
        "With headphones in the OUT jack: the output reads \"hp\" and the speaker goes quiet.",
        lambda L: draw_status(St(lang=L, mic=False, headphones=True)))
    add("status_carga", "status", "USB ligado e carregando: \"CHG\" no lugar de \"BAT\" (sem carga: \"USB\").",
        "USB plugged in and charging: \"CHG\" instead of \"BAT\" (charged: \"USB\").",
        lambda L: draw_status(St(lang=L, mic=False, headphones=False, usb=True, charging=True, battery=60)))
    add("status_bateria_baixa", "status", "Bateria baixa: a barra quase vazia (o LED pisca vermelho devagar abaixo de 3,5 V).",
        "Low battery: the bar is almost empty (the LED blinks red slowly under 3.5 V).",
        lambda L: draw_status(St(lang=L, mic=False, headphones=False, battery=8)))
    add("status_repouso", "status", "Cinco minutos sem tocar: \"repouso\" (o amplificador descansa; aos 15 minutos o instrumento desliga).",
        "Five minutes without playing: \"rest\" (the amplifier rests; after 15 minutes the instrument switches off).",
        lambda L: draw_status(St(lang=L, mic=False, headphones=False, resting=True)))
    add("status_registro", "status", "Girar o seletor muda o registro (aqui BANDONEON); o LED verde pisca até você clicar para guardar.",
        "Turning the selector changes the register (here BANDONEON); the green LED blinks until you click to keep it.",
        lambda L: draw_status(St(lang=L, mic=False, headphones=False, register=1)))
    for i, n in enumerate(REGISTER_NAMES):
        pass
    add("status_mic", "status", "Com um microfone no IN e fone: \"voz\" quando algum efeito de voz está ligado, mais o medidor do nível do microfone.",
        "With a microphone in IN and headphones: \"voice\" when a voice effect is on, plus the microphone level meter.",
        lambda L: draw_status(St(lang=L, mic=True, headphones=True, voice=100), STR["S_VOICE"][L] + " *", 5))
    add("status_mic_nota", "status", "Harmonizador que segue as teclas: a nota que a tela ouve na sua voz (aqui A4).",
        "Harmonizer following the keys: the note the screen hears in your voice (here A4).",
        lambda L: draw_status(St(lang=L, mic=True, headphones=True, harm=100, harmFollow=True), "%s A4" % STR["S_VOICE"][L], 3))
    add("status_sem_mic_voz", "status", "Efeito de voz ligado, mas sem microfone: a tela avisa \"sem mic\".",
        "A voice effect is on but no microphone: the screen says \"no mic\".",
        lambda L: draw_status(St(lang=L, mic=False, headphones=True, voice=100), STR["S_NO_MIC"][L]))
    add("status_voz_muda", "status", "Microfone e alto-falante, sem a voz no alto-falante: \"voz muda\" (para evitar microfonia).",
        "Microphone and speaker, voice not on the speaker: \"voice off\" (to avoid feedback).",
        lambda L: draw_status(St(lang=L, mic=True, headphones=False, voice=100), STR["S_VOICE_OFF"][L]))
    add("status_microfonia", "status", "Voz no alto-falante ligada: \"!microfonia\" pisca ao lado do volume.",
        "Voice on the speaker switched on: \"!feedback\" blinks beside the volume.",
        lambda L: draw_status(St(lang=L, mic=True, headphones=False, voice=100, speaker=True), STR["S_FEEDBACK"][L], 2))
    add("aviso_a", "aviso", "Ao ligar a voz no alto-falante, este aviso ocupa a tela por 4 s (quadro 1 de 2, a moldura pisca).",
        "Switching the voice onto the speaker shows this warning for 4 s (frame 1 of 2, the border blinks).",
        lambda L: draw_warning(St(lang=L), True))
    add("aviso_b", "aviso", "O mesmo aviso, quadro 2 de 2.", "The same warning, frame 2 of 2.", lambda L: draw_warning(St(lang=L), False))

    # ---- menu
    add("menu_principal", "menu", "Clique longo (0,7 s) no seletor abre o menu. Com microfone: Voz, Captação, Saída, Som, Sistema.",
        "A long click (0.7 s) on the selector opens the menu. With a microphone: Voice, Input, Output, Sound, System.",
        menu_fn("PG_MAIN", 0))
    add("menu_principal_sem_mic", "menu", "Sem microfone no IN, as páginas Voz e Captação não aparecem.",
        "With no microphone in IN, the Voice and Input pages are not listed.", menu_fn("PG_MAIN", 0, mic=False))
    add("menu_voz", "menu", "Voz (só com microfone): voz seca, vocoder, harmonizador, modo, intervalo, eco e reverb da voz.",
        "Voice (only with a microphone): dry voice, vocoder, harmonizer, mode, interval, echo and voice reverb.", menu_fn("PG_VOICE", 0))
    add("menu_voz_rolada", "menu", "A lista rola: cinco linhas por vez, com \"posição/total\" no canto.",
        "The list scrolls: five lines at a time, with \"position/total\" in the corner.", menu_fn("PG_VOICE", 8, 4))
    add("menu_voz_exato", "menu", "Modo do harmonizador \"Exato\": somem o intervalo e a força; entram \"Vozes\" e \"Oitava\".",
        "Harmonizer mode \"Exact\": interval and strength disappear; \"Voices\" and \"Octave\" appear.",
        menu_fn("PG_VOICE", 3, harmFollow=True, followMode=0, harm=90))
    add("menu_voz_ajuda", "menu", "Modo \"Ajuda\": aparece a \"Intensidade\" (quanto a voz é puxada para a nota).",
        "Mode \"Assist\": the \"Strength\" line appears (how far the voice is pulled to the note).",
        menu_fn("PG_VOICE", 3, harmFollow=True, followMode=1, harm=90))
    add("menu_entrada", "menu", "Captação (só com microfone): ganho, porta de ruído (limiar, razão, ataque, retenção, soltura), passa-altas, antimicrofonia.",
        "Input (only with a microphone): gain, noise gate (threshold, ratio, attack, hold, release), high-pass, anti-feedback.",
        menu_fn("PG_INPUT", 0))
    add("menu_entrada_rolada", "menu", "Final da lista da Captação: \"Mic padrão\" (ajustes de fábrica de um headset) e \"Limpar notch\".",
        "End of the Input list: \"Mic default\" (factory settings for a headset) and \"Clear notch\".", menu_fn("PG_INPUT", 9, 5))
    add("menu_saida", "menu", "Saída: volume, para onde vai a voz, nível das teclas, equalizador do alto-falante (corte e pico de 1 kHz).",
        "Output: volume, where the voice goes, key level, speaker equaliser (cutoff and 1 kHz dip).", menu_fn("PG_OUTPUT", 0))
    add("menu_saida_sem_mic", "menu", "Sem microfone, a Saída perde \"Saída voz\" e \"Teclas\".",
        "With no microphone, Output loses \"Voice out\" and \"Keys\".", menu_fn("PG_OUTPUT", 0, mic=False))
    add("menu_som", "menu", "Som: registro (um clique troca ao próximo), reverb e curva de velocity.",
        "Sound: register (a click goes to the next), reverb and velocity curve.", menu_fn("PG_SOUND", 0))
    add("menu_sistema", "menu", "Sistema: salvar, zerar a voz, calibrar as teclas, teste de teclas, tipo de microfone, idioma.",
        "System: save, reset voice, calibrate keys, key test, microphone type, language.", menu_fn("PG_SYSTEM", 0))
    add("menu_sistema_rolado", "menu", "Final do Sistema: \"Tipo mic\" (Auto, Eletreto, Dinâmico) e \"Idioma\".",
        "End of System: \"Mic type\" (Auto, Electret, Dynamic) and \"Language\".", menu_fn("PG_SYSTEM", 5, 1))
    add("menu_tipo_mic", "menu", "\"Tipo mic\" em \"Dinâmico\": o bias do microfone fica desligado (gravado na hora).",
        "\"Mic type\" set to \"Dynamic\": the microphone bias is off (kept at once).", menu_fn("PG_SYSTEM", 4, 0, micType=2))
    add("menu_idioma", "menu", "O idioma do menu troca na hora (Português / English) e fica guardado.",
        "The menu language changes at once (Português / English) and is kept.", menu_fn("PG_SYSTEM", 5, 1))
    add("menu_salvo", "menu", "Clicar em \"Salvar\" mostra \"Salvo\" por 1,5 s na barra de título.",
        "Clicking \"Save\" shows \"Saved\" for 1.5 s in the title bar.", menu_fn("PG_SYSTEM", 0, 0, toast="S_T_SAVED"))
    add("menu_calibrado", "menu", "\"Calibrar\" esquece e reaprende a amplitude de cada tecla: \"Calibrado\".",
        "\"Calibrate\" forgets and relearns each key's travel: \"Calibrated\".", menu_fn("PG_SYSTEM", 2, 0, toast="S_T_CAL"))
    add("menu_registro", "menu", "Em Som > Registro, o volume gira muda o registro sem sair do menu.",
        "In Sound > Register, turning the volume knob changes the register without leaving the menu.",
        menu_fn("PG_SOUND", 0, register=4))
    add("menu_volume", "menu", "Em Saída > Volume, o botão de volume muda o valor da linha sob o cursor.",
        "In Output > Volume, the volume knob changes the value of the line under the cursor.", menu_fn("PG_OUTPUT", 0, volume=60))
    return C


def tree(lang):
    """The whole menu as a nested list for the page: [(name, kind, [children or None])]"""
    out = []
    for it in ITEMS["PG_MAIN"]:
        node = {"name": it["name"][lang], "needsMic": it["needsMic"], "children": []}
        for sub in ITEMS[it["id"]]:
            node["children"].append({"name": sub["name"][lang], "kind": sub["kind"], "needsMic": sub["needsMic"], "id": sub["id"]})
        out.append(node)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cat = build_catalogue()
    meta = {"screens": [], "tree": {}, "registers": REGISTER_NAMES, "w": 128 * K + 16, "h": 64 * K + 16}
    for c in cat:
        for L in LANGS:
            c["fn"](L).image().save(os.path.join(OUT, "tela_%s_%s.png" % (c["name"], L)), optimize=True)
        meta["screens"].append({"name": c["name"], "group": c["group"], "caption": c["caption"]})
    for L in LANGS:
        meta["tree"][L] = tree(L)
    # every register on the status screen, one strip (the selector turns through them)
    for L in LANGS:
        strip = Image.new("RGB", ((128 * K + 16) * 2, (64 * K + 16) * 4), (28, 28, 30))
        for i in range(7):
            im = draw_status(St(lang=L, mic=False, headphones=False, register=i)).image()
            strip.paste(im, ((i % 2) * (128 * K + 16), (i // 2) * (64 * K + 16)))
        strip.save(os.path.join(OUT, "tela_registros_%s.png" % L), optimize=True)
    json.dump(meta, open(os.path.join(OUT, "telas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("screens:", len(cat), "x", len(LANGS), "+ registers strip; items:", {k: len(v) for k, v in ITEMS.items()})


if __name__ == "__main__":
    main()
