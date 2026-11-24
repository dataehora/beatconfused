"""eTutti Student V4 (R13V4 item 5): writes the model page and the complete manual, in Portuguese and English.

    python etutti/hardware/student_v04/telas_oled.py      # first: the OLED screens, simulated from the firmware
    python etutti/hardware/student_v04/pagina.py

Plain Python (+ Pillow for the fallback pictures). Writes etutti/studentV4/{index.html, styles.css, script.js, img/, arquivos/}.
The page is unlisted: noindex, no home card, not in sitemap.xml. One .lang-block per language, shown by html[lang] (same pattern
as etutti/manuais/). Texts and prices live HERE: edit them here, not in the HTML.

Sources (R13V4): pictures in etutti/studentV4/img/ (design: foto_instrumento, foto_explodido, passo_1..11; electronics: the JLCPCB previews
are converted from student_v04/pcb/img/previa_jlc_*.png); section 5 = fab/COMPRA.md (Portuguese, read here) + compra_en.md (English
translation, kept here, update both together); steps = pagina_passos.py; MODELOS_3D.md and the quote sheets are copied to arquivos/.
Money: every price is a range in US$ and an ESTIMATE (ELETRONICA.md / fab/principal/LEIAME_COTACAO.md, R13V4), nothing was quoted as a purchase.
"""
import html
import json
import math
import os
import re
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ETUTTI = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ETUTTI, "studentV4")
IMG = os.path.join(OUT, "img")
ARQ = os.path.join(OUT, "arquivos")
REN = os.path.join(HERE, "case", "renders")
VER = "20261124a"
sys.path.insert(0, os.path.join(HERE, "case"))
import layout_r4 as LAY    # noqa: E402  (stdlib only)

for d in (OUT, IMG, ARQ):
    os.makedirs(d, exist_ok=True)
PENDING = []


def esc(s):
    return html.escape(s, quote=True)


def B(pt, en, tag="div"):
    """The two language blocks of a piece of content."""
    return ('<%s class="lang-block" data-lang="pt">%s</%s>\n<%s class="lang-block" data-lang="en">%s</%s>' % (tag, pt, tag, tag, en, tag))


# ---------------------------------------------------------------- pictures
FALLBACK = {   # name -> (render in case/renders, max width)
    "planta": ("planta_geral_v4_r15.png", 1700),
    "planta_interface": ("planta_interface_v4_r15.png", 1500),
    "corte_interface": ("corte_interface_v4_r15.png", 1500),
    "iso_base_r15": ("iso_base_r15_frente_esq.png", 2200),
    "iso_base_r15_tras": ("iso_base_r15_tras_dir.png", 2200),
    "corte_base_r15": ("corte_base_r15.png", 1700),
    "base_antes_depois_r15": ("base_antes_depois_r15.png", 1700),
    "prog_r15": ("base_fundo_prog_r15.png", 1900),
}


def find_img(name):
    for ext in ("jpg", "jpeg", "png"):
        p = os.path.join(IMG, "%s.%s" % (name, ext))
        if os.path.exists(p):
            return "%s.%s" % (name, ext)
    return None


def trim(im, pad=12):
    """Crop the white margins of a drawing sheet (matplotlib figures come with a lot of blank paper)."""
    from PIL import ImageChops
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    if not box:
        return im
    return im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height)))


def prepare_fallbacks():
    for name, (src, mw) in FALLBACK.items():
        sp = os.path.join(REN, src)
        if not os.path.exists(sp):
            continue
        im = trim(Image.open(sp).convert("RGB"))
        if im.width > mw:
            im = im.resize((mw, int(im.height * mw / im.width)), Image.LANCZOS)
        im.save(os.path.join(IMG, name + ".jpg"), quality=86, optimize=True)


def prepare_extra():
    sp = os.path.join(REN, "regua_parafusos_r14.png")
    if os.path.exists(sp):
        im = trim(Image.open(sp).convert("RGB"))
        if im.width > 2000:
            im = im.resize((2000, int(im.height * 2000 / im.width)), Image.LANCZOS)
        im.save(os.path.join(IMG, "regua_parafusos_r14.jpg"), quality=86, optimize=True)


PREVIAS = {"previa_principal_bottom": "previa_jlc_principal_bottom.png", "previa_principal_top": "previa_jlc_principal_top.png", "previa_r8_bottom": "previa_jlc_r8_bottom.png"}


def prepare_previews():
    for name, src in PREVIAS.items():
        sp = os.path.join(HERE, "pcb", "img", src)
        if os.path.exists(sp):
            im = Image.open(sp).convert("RGB")
            if im.width > 1700:
                im = im.resize((1700, int(im.height * 1700 / im.width)), Image.LANCZOS)
            im.save(os.path.join(IMG, name + ".jpg"), quality=88, optimize=True)


def fig(name, alt_pt, alt_en, cap_pt, cap_en, pending_pt="Figura a chegar do design (render do modelo 3D).", pending_en="Figure to come from the design (3D model render)."):
    f = find_img(name)
    if f:
        w, h = Image.open(os.path.join(IMG, f)).size
        im = lambda alt: '<a href="img/%s"><img src="img/%s" width="%d" height="%d" alt="%s" loading="lazy" /></a>' % (f, f, w, h, esc(alt))
        return ('<figure>%s<figcaption>%s</figcaption></figure>' % (B(im(alt_pt), im(alt_en)), B(cap_pt, cap_en)))
    PENDING.append(name)
    return '<figure class="pending">%s</figure>' % B("<p>%s <small>(%s)</small></p>" % (pending_pt, name), "<p>%s <small>(%s)</small></p>" % (pending_en, name))


# ---------------------------------------------------------------- the keyboard, from layout_r4.py
def keyboard_svg(griff):
    """Plan of the 32 keys, row 1 nearest the player (bottom). griff 'C' or 'B' (B: rows 1 and 3 swapped, row 4 follows row 1 minus 3)."""
    first = dict(LAY.FIRST_MIDI)
    if griff == "B":
        first = {1: 56, 2: 55, 3: 57, 4: 53}
    names = LAY.NOTE_NAMES
    o = ['<svg viewBox="52 12 190 82" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="keyboard">',
         '<defs><pattern id="chk%s" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="3" height="3" fill="#2B2925"/><rect x="3" y="3" width="3" height="3" fill="#2B2925"/></pattern></defs>' % griff]
    o.append('<rect x="76" y="14" width="164" height="78" rx="5" fill="#EAE4D3" stroke="#B9B09A"/>')
    for r, y, x0, n in LAY.ROWS:
        o.append('<text x="74" y="%.1f" font-size="4.6" text-anchor="end" fill="#5C574F">%d</text>' % (y + 1.6, r))
        for i in range(n):
            m = first[r] + 3 * i
            nm = "%s%d" % (names[m % 12], m // 12 - 1)
            x = x0 + i * LAY.PITCH
            sharp = "#" in nm
            cf = nm[0] in "CF" and not sharp
            if sharp:
                o.append('<circle cx="%.2f" cy="%.2f" r="7.6" fill="#1b1b1b" stroke="#000" stroke-width="0.5"/>' % (x, y))
                o.append('<text x="%.2f" y="%.2f" font-size="5" text-anchor="middle" fill="#fff">%s</text>' % (x, y + 1.8, nm))
            else:
                o.append('<circle cx="%.2f" cy="%.2f" r="7.6" fill="#fff" stroke="#2B2925" stroke-width="0.5"/>' % (x, y))
                if cf:
                    o.append('<circle cx="%.2f" cy="%.2f" r="7.6" fill="url(#chk%s)"/>' % (x, y, griff))
                    o.append('<text x="%.2f" y="%.2f" font-size="5" font-weight="700" text-anchor="middle" fill="#000" stroke="#fff" stroke-width="1.3" paint-order="stroke">%s</text>' % (x, y + 1.8, nm))
                else:
                    o.append('<text x="%.2f" y="%.2f" font-size="5" text-anchor="middle" fill="#000">%s</text>' % (x, y + 1.8, nm))
    o.append('<text x="76" y="92.5" font-size="4" fill="#5C574F">← </text>')
    o.append('</svg>')
    return "".join(o)


# ---------------------------------------------------------------- block diagram (vertical, readable at 375 px)
def diagram(L):
    t = {
        "pt": dict(rul="4 réguas R8", rul2="32 sensores Hall + 74HC595", scan="varredura: 2 fios + 4 linhas analógicas", mm="MicroMod Teensy",
                   mm2="teclas, velocity, acordeão, menu", knob="2 knobs", oled="Tela OLED", i2c="I²C", codec="Codec SGTL5000", amp="Amplificador",
                   spk="Alto-falante", out="Fone / AUX (OUT)", inn="Microfone (IN)", usb="USB-C", usb2="MIDI, carga", chg="Carregador", bat="Bateria LiPo",
                   reg="3,3 V", i2s="I²S (áudio)", pw="energia"),
        "en": dict(rul="4 R8 rulers", rul2="32 Hall sensors + 74HC595", scan="scan: 2 wires + 4 analog lines", mm="MicroMod Teensy",
                   mm2="keys, velocity, accordion, menu", knob="2 knobs", oled="OLED screen", i2c="I²C", codec="SGTL5000 codec", amp="Amplifier",
                   spk="Speaker", out="Headphones / AUX (OUT)", inn="Microphone (IN)", usb="USB-C", usb2="MIDI, charge", chg="Charger", bat="LiPo battery",
                   reg="3.3 V", i2s="I²S (audio)", pw="power"),
    }[L]
    s = ['<svg viewBox="0 0 360 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="block diagram" class="bd">',
         '<defs><marker id="ar%s" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" fill="#5C574F"/></marker></defs>' % L]

    def box(x, y, w, h, a, b=None, cls="b1"):
        s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="8" class="%s"/>' % (x, y, w, h, cls))
        if b:
            s.append('<text x="%d" y="%d" text-anchor="middle" class="t1">%s</text><text x="%d" y="%d" text-anchor="middle" class="t2">%s</text>' % (x + w / 2, y + h / 2 - 2, esc(a), x + w / 2, y + h / 2 + 13, esc(b)))
        else:
            s.append('<text x="%d" y="%d" text-anchor="middle" class="t1">%s</text>' % (x + w / 2, y + h / 2 + 5, esc(a)))

    def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, both=False):
        m = ' marker-start="url(#ar%s)"' % L if both else ""
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="ln" marker-end="url(#ar%s)"%s/>' % (x1, y1, x2, y2, L, m))
        if label:
            s.append('<text x="%d" y="%d" class="t3">%s</text>' % (lx if lx is not None else x1 + 6, ly if ly is not None else (y1 + y2) / 2 + 3, esc(label)))

    box(60, 8, 240, 52, t["rul"], t["rul2"], "b2")
    arrow(180, 60, 180, 100, t["scan"], 186, 84)
    box(40, 100, 280, 64, t["mm"], t["mm2"], "b3")
    box(8, 190, 90, 40, t["knob"], None, "b4")
    box(262, 190, 90, 40, t["oled"], None, "b4")
    arrow(60, 164, 53, 190, None, both=True)
    arrow(300, 164, 307, 190, t["i2c"], 312, 180, both=True)
    arrow(180, 164, 180, 250, t["i2s"], 186, 212, both=True)
    box(100, 250, 160, 44, t["codec"], None, "b5")
    arrow(140, 294, 70, 340)
    box(8, 340, 124, 40, t["out"], None, "b6")
    arrow(290, 340, 220, 294)
    box(228, 340, 124, 40, t["inn"], None, "b6")
    # amplifier fed from the same I2S
    arrow(180, 294, 180, 330, None)
    s.append('<rect x="146" y="330" width="68" height="34" rx="8" class="b5"/><text x="180" y="351" text-anchor="middle" class="t1">%s</text>' % esc(t["amp"]))
    arrow(180, 364, 180, 392)
    s.append('<rect x="136" y="392" width="88" height="30" rx="8" class="b6"/><text x="180" y="412" text-anchor="middle" class="t1">%s</text>' % esc(t["spk"]))
    # power chain
    box(8, 450, 90, 44, t["usb"], t["usb2"], "b7")
    arrow(98, 472, 128, 472, None)
    box(128, 450, 90, 44, t["chg"], None, "b7")
    arrow(218, 472, 248, 472, None, both=True)
    box(248, 450, 104, 44, t["bat"], None, "b7")
    arrow(300, 494, 300, 522, t["pw"], 306, 512)
    box(240, 522, 112, 30, t["reg"], None, "b7")
    arrow(53, 450, 53, 420, None)
    s.append('<text x="60" y="436" class="t3">USB</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- small markdown (COMPRA.md hook)
def md_to_html(md):
    out, lst, tab = [], False, []

    def inline(x):
        x = esc(x)
        x = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", x)
        x = re.sub(r"`(.+?)`", r"<code>\1</code>", x)
        return x

    def flush():
        nonlocal lst, tab
        if lst:
            out.append("</ul>")
            lst = False
        if tab:
            rows = [r for r in tab if not re.match(r"^\|[\s:|-]+\|?$", r)]
            h = "<div class=\"tablewrap\"><table>"
            for i, r in enumerate(rows):
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                tg = "th" if i == 0 else "td"
                h += "<tr>%s</tr>" % "".join("<%s>%s</%s>" % (tg, inline(c), tg) for c in cells)
            out.append(h + "</table></div>")
            tab = []

    for ln in md.splitlines():
        if ln.startswith("|"):
            if lst:
                flush()
            tab.append(ln)
            continue
        flush()
        if ln.startswith("#"):
            n = min(len(ln) - len(ln.lstrip("#")) + 2, 5)
            out.append("<h%d>%s</h%d>" % (n, inline(ln.lstrip("# ")), n))
        elif re.match(r"^\s*[-*] ", ln):
            if not lst:
                out.append("<ul>")
                lst = True
            out.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*] ", "", ln)))
        elif re.match(r"^\s*\d+\. ", ln):
            out.append("<p>%s</p>" % inline(ln.strip()))
        elif ln.strip():
            out.append("<p>%s</p>" % inline(ln))
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- prices (ESTIMATES: fab/principal/LEIAME_COTACAO.md, R12V4)
PRICES = [   # area_pt, area_en, low, high, note_pt, note_en  (same lines as fab/COMPRA.md section 4, R15V4; the sum is the official total)
    ("Placa principal montada (JLCPCB)", "Main board, assembled (JLCPCB)", 158.0, 158.0,
     "cotação real do J (24 nov, ENIG, o site passou a montagem para Standard): placa 25,50 + montagem 132,62; 5 placas, 2 montadas. Com HASL e montagem Economic: cerca de 134 (estimativa)",
     "J's real quote (24 Nov, ENIG, the site switched assembly to Standard): board 25.50 + assembly 132.62; 5 boards, 2 assembled. With HASL and Economic assembly: about 134 (estimate)"),
    ("4 réguas R8 montadas (JLCPCB, pedido à parte)", "4 R8 rulers, assembled (JLCPCB, separate order)", 72.0, 72.0,
     "cotação real do J (23 nov): painel de 2 réguas, 5 painéis, 2 montados", "J's real quote (23 Nov): panel of 2 rulers, 5 panels, 2 assembled"),
    ("Grade-régua FR-4 1,6 mm (JLCPCB, placa nua)", "1.6 mm FR-4 ruler grid (JLCPCB, bare board)", 8.0, 15.0, "estimativa, não cotada", "estimate, not quoted"),
    ("6 cabos JST SH (placa → réguas, 2 de reserva) e cabo Qwiic 50 mm", "6 JST SH cables (board → rulers, 2 spare) and 50 mm Qwiic cable", 8.0, 10.0, "A06SR06SR30K51B", "A06SR06SR30K51B"),
    ("Tela OLED Adafruit 326", "Adafruit 326 OLED", 17.5, 17.5, "SSD1306 128 x 64, I²C", "SSD1306 128 x 64, I²C"),
    ("Ferragem (M2 passantes e porcas, formadores de rosca, M2,5 de náilon, 8 pés 3M Bumpon)", "Hardware (M2 through bolts and nuts, thread-forming screws, nylon M2.5, 8 3M Bumpon feet)", 6.0, 12.0, "estimativa", "estimate"),
    ("Case impresso em MJF PA12 (base, tampa, capas, caixa acústica, knobs)", "Case printed in MJF PA12 (base, lid, caps, acoustic box, knobs)", 46.0, 51.0,
     "valor de COMPRA.md, por volume; não cotado (o berço contínuo da base nova não está incluído, ver a nota abaixo)", "COMPRA.md's figure, by volume; not quoted (the new base's continuous cradle is not included, see the note below)"),
    ("Teclas, módulo, bateria, alto-falante, encoders, molas e cabo USB-C", "Keys, module, battery, speaker, encoders, springs and USB-C cable", 71.5, 92.6,
     "KS-20 Orange; MicroMod DEV-16402; LiPo 503450; CE28MB-8; EC11E18244AU", "KS-20 Orange; MicroMod DEV-16402; LiPo 503450; CE28MB-8; EC11E18244AU"),
]
_p = os.path.join(HERE, "precos_pagina.json")
if os.path.exists(_p):
    PRICES = [tuple(r) for r in json.load(open(_p, encoding="utf-8"))["linhas"]]


def price_table():
    lo = sum(r[2] for r in PRICES)
    hi = sum(r[3] for r in PRICES)
    rng = lambda a, b, sep: ("%.1f" % a).replace(".", sep) if abs(a - b) < 0.05 else ("%.1f–%.1f" % (a, b)).replace(".", sep)
    rows_pt = "".join("<tr><td>%s<small>%s</small></td><td class=\"num\">%s</td></tr>" % (esc(r[0]), esc(r[4]), rng(r[2], r[3], ",")) for r in PRICES)
    rows_en = "".join("<tr><td>%s<small>%s</small></td><td class=\"num\">%s</td></tr>" % (esc(r[1]), esc(r[5]), rng(r[2], r[3], ".")) for r in PRICES)
    pt = ('<div class="tablewrap"><table><tr><th>Item</th><th>US$</th></tr>%s<tr class="tot"><td>Total, 32 teclas, pedido mínimo, sem frete nem IVA</td><td class="num">%.0f–%.0f</td></tr></table></div>'
          % (rows_pt, lo, hi))
    en = ('<div class="tablewrap"><table><tr><th>Item</th><th>US$</th></tr>%s<tr class="tot"><td>Total, 32 keys, minimum order, no shipping or VAT</td><td class="num">%.0f–%.0f</td></tr></table></div>'
          % (rows_en, lo, hi))
    return B(pt, en), lo, hi


# ---------------------------------------------------------------- the catalogue of screens
TELAS = json.load(open(os.path.join(IMG, "telas.json"), encoding="utf-8")) if os.path.exists(os.path.join(IMG, "telas.json")) else None


def screens_gallery(group, intro_pt="", intro_en=""):
    if not TELAS:
        PENDING.append("telas (run telas_oled.py)")
        return ""
    items = [s for s in TELAS["screens"] if s["group"] == group]
    w, h = TELAS["w"], TELAS["h"]

    def cards(L):
        return "".join('<figure class="tela"><img src="img/tela_%s_%s.png" width="%d" height="%d" alt="%s" loading="lazy" /><figcaption>%s</figcaption></figure>'
                       % (s["name"], L, w, h, esc(s["caption"][L]), esc(s["caption"][L])) for s in items)
    return B('<div class="telas">%s</div>' % cards("pt"), '<div class="telas">%s</div>' % cards("en"))


def menu_tree_html(L):
    if not TELAS:
        return ""
    tr = TELAS["tree"][L]
    mic = {"pt": "só com microfone", "en": "only with a microphone"}[L]
    kind = {"MK_SUB": "", "MK_LEVEL": {"pt": "nível", "en": "level"}[L], "MK_ENUM": {"pt": "escolha", "en": "choice"}[L], "MK_ACTION": {"pt": "ação", "en": "action"}[L]}
    o = ['<ul class="tree">']
    for top in tr:
        o.append('<li><b>%s</b>%s<ul>' % (esc(top["name"]), (' <em>(%s)</em>' % mic) if top["needsMic"] else ""))
        for c in top["children"]:
            o.append('<li>%s <small>%s%s</small></li>' % (esc(c["name"]), kind[c["kind"]], (", " + mic) if c["needsMic"] and not top["needsMic"] else ""))
        o.append("</ul></li>")
    o.append("</ul>")
    return "".join(o)


# ---------------------------------------------------------------- the assembly steps (section 6): texts in pagina_passos.py
from pagina_passos import STEPS, EXTRA   # noqa: E402

CARES = ("pt", "en")


def steps_html():
    pt, en = [], []
    for i, (f, tp, te, tm, ptp, pte, xp, xe, wp, we, bal) in enumerate(STEPS, 1):
        figh = fig(f, "Passo %d" % i, "Step %d" % i, "Passo %d: %s" % (i, tp), "Step %d: %s" % (i, te))
        xf = EXTRA.get(i)
        xfig = fig(xf[0], xf[3], xf[4], xf[1], xf[2]) if xf else None
        for lst, L, ti, parts, tx, wr, lab, k in ((pt, "pt", tp, ptp, xp, wp, ("Tempo", "Peças", "Números na figura"), 0), (en, "en", te, pte, xe, we, ("Time", "Parts", "Numbers in the figure"), 1)):
            w = '<div class="warn">%s</div>' % esc(wr) if wr else ""
            leg = '<ol class="legend" aria-label="%s">%s</ol>' % (lab[2], "".join("<li>%s</li>" % esc(b[k]) for b in bal)) if bal else ""
            extra = figh_block(xfig, L) if xfig else ""
            lst.append('<article class="step" id="passo-%d%s"><h3><span class="n">%d</span> %s</h3>%s%s<dl class="meta"><dt>%s</dt><dd>%s</dd><dt>%s</dt><dd>%s</dd></dl><p>%s</p>%s%s</article>'
                       % (i, "" if L == "pt" else "-en", i, esc(ti), figh_block(figh, L), leg, lab[0], esc(tm), lab[1], esc(parts), tx, extra, w))
    return B("".join(pt), "".join(en))


def figh_block(figh, L):
    """A fig() holds both languages: keep only the requested language's block (or the pending box)."""
    if 'class="pending"' in figh:
        m = re.search(r'<div class="lang-block" data-lang="%s">(.*?)</div>' % L, figh, re.S)
        return '<figure class="pending">%s</figure>' % m.group(1)
    imgm = re.search(r'<div class="lang-block" data-lang="%s">(.*?)</div>' % L, figh, re.S)
    capm = re.findall(r'<div class="lang-block" data-lang="%s">(.*?)</div>' % L, figh, re.S)
    return "<figure>%s<figcaption>%s</figcaption></figure>" % (capm[0], capm[1])


# ---------------------------------------------------------------- the files (section 10)
def copy_files():
    rows = []      # (src, dest name, pt label, en label, group)
    src = lambda *p: os.path.join(HERE, *p)
    fw = os.path.join(ETUTTI, "firmware", "student_v4")
    rows += [
        (src("fab", "principal", "student_v04_gerbers.zip"), "placa_principal_gerbers.zip", "Placa principal: Gerbers e furação (4 camadas)", "Main board: Gerbers and drills (4 layers)", "fab"),
        (src("fab", "principal", "bom.csv"), "placa_principal_bom.csv", "Placa principal: BOM (formato JLCPCB)", "Main board: BOM (JLCPCB format)", "fab"),
        (src("fab", "principal", "cpl.csv"), "placa_principal_cpl.csv", "Placa principal: CPL (posições, todas no fundo)", "Main board: CPL (positions, all on the bottom)", "fab"),
        (src("fab", "regua", "R8_painel2", "gerbers.zip"), "regua_R8_painel2_gerbers.zip", "Régua R8, painel de 2: Gerbers (2 camadas)", "R8 ruler, panel of 2: Gerbers (2 layers)", "fab"),
        (src("fab", "regua", "R8_painel2", "bom.csv"), "regua_R8_painel2_bom.csv", "Régua R8, painel de 2: BOM", "R8 ruler, panel of 2: BOM", "fab"),
        (src("fab", "regua", "R8_painel2", "cpl.csv"), "regua_R8_painel2_cpl.csv", "Régua R8, painel de 2: CPL", "R8 ruler, panel of 2: CPL", "fab"),
        (src("fab", "student_v04_grade_regua_painel_gerbers.zip"), "grade_regua_painel_gerbers.zip", "Grade-régua FR-4 de 1,6 mm (painel): Gerbers, placa nua sem montagem", "FR-4 ruler grid 1.6 mm (panel): Gerbers, bare board, no assembly", "fab"),
        (src("fab", "student_v04_grade_contorno32_gerbers.zip"), "grade_contorno32_gerbers.zip", "Grade FR-4 (contorno de 32 teclas): Gerbers", "FR-4 grid (32-key outline): Gerbers", "fab"),
        (src("fab", "COMPRA.md"), "COMPRA.md", "COMPRA.md: o que marcar e preencher em cada loja (eletrônica, pt)", "COMPRA.md: what to tick and fill in at each shop (electronics, pt)", "doc"),
        (src("compra_en.md"), "COMPRA_en.md", "COMPRA_en.md: o mesmo texto em inglês (tradução)", "COMPRA_en.md: the same text in English (translation)", "doc"),
        (src("fornecimento", "MODELOS_3D.md"), "MODELOS_3D.md", "MODELOS_3D.md: modelo 3D, posição, giro e pino 1 das peças montadas pela JLCPCB (pt)", "MODELOS_3D.md: 3D model, position, rotation and pin 1 of the parts JLCPCB assembles (pt)", "doc"),
        (src("fab", "principal", "LEIAME_COTACAO.md"), "LEIAME_COTACAO_principal.md", "Placa principal: como cotar, conferências e lista de pré-visualização (pt)", "Main board: how to quote, checks and preview checklist (pt)", "doc"),
        (src("fab", "regua", "LEIAME_COTACAO.md"), "LEIAME_COTACAO_regua.md", "Réguas: como cotar, variantes e painéis (pt)", "Rulers: how to quote, variants and panels (pt)", "doc"),
    ]
    for n, pt, en in (("base", "Base (bandeja)", "Base (tray)"), ("tampa", "Tampa", "Lid"), ("teclas", "Botões (32)", "Buttons (32)"), ("caixa_acustica", "Caixa acústica", "Acoustic box"),
                      ("knob_1", "Knob (impressão 1 de 2)", "Knob (print 1 of 2)")):
        rows.append((src("case", "out", "r4_32_%s.stl" % n), "case_%s.stl" % n, "Case, " + pt + " (STL)", "Case, " + en + " (STL)", "case"))
    for n, pt, en in (("base", "Base", "Base"), ("tampa", "Tampa", "Lid")):
        rows.append((src("case", "out", "r4_32_%s.step" % n), "case_%s.step" % n, "Case, " + pt + " (STEP)", "Case, " + en + " (STEP)", "case"))
    hexf = os.path.join(HERE, "firmware_hex", "student_v4_teensyMM_midi_396.hex")
    rows.append((hexf, "student_v4_teensyMM_midi_396.hex", "Firmware compilado (sem as amostras licenciadas do acordeão), Teensy MicroMod, USB MIDI, 396 MHz",
                 "Compiled firmware (without the licensed accordion samples), Teensy MicroMod, USB MIDI, 396 MHz", "fw"))
    out = []
    for s, d, pt, en, g in rows:
        if os.path.exists(s):
            shutil.copyfile(s, os.path.join(ARQ, d))
            out.append((d, pt, en, g, os.path.getsize(s)))
        else:
            PENDING.append("arquivo " + d)
            out.append((None, pt, en, g, 0))
    # the sketch itself, zipped without the gitignored sample data
    import zipfile
    zp = os.path.join(ARQ, "student_v4_sketch.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("student_v4.ino", "voice_fx.h", "ui_text.h", "oled_font.h", "reed_sampler.h", "name.c"):
            z.write(os.path.join(fw, f), "student_v4/" + f)
    out.append(("student_v4_sketch.zip", "Sketch do Arduino (pasta student_v4, sem os dados de amostras)", "Arduino sketch (folder student_v4, without the sample data)", "fw", os.path.getsize(zp)))
    return out


def size_txt(n):
    return "%.0f kB" % (n / 1024.0) if n < 1048576 else "%.1f MB" % (n / 1048576.0)


def files_html(files):
    def block(L):
        groups = {"fab": ("Fabricação (JLCPCB)", "Manufacturing (JLCPCB)"), "case": ("Case (impressão 3D)", "Case (3D printing)"), "doc": ("Folhas de apoio (eletrônica)", "Support sheets (electronics)"), "fw": ("Firmware", "Firmware")}
        o = []
        for g, (gp, ge) in groups.items():
            o.append("<h3>%s</h3><ul class=\"files\">" % (gp if L == "pt" else ge))
            for d, pt, en, gg, sz in files:
                if gg != g:
                    continue
                lab = pt if L == "pt" else en
                if d:
                    o.append('<li><a href="arquivos/%s" download>%s</a> <small>%s · %s</small></li>' % (d, esc(lab), d, size_txt(sz)))
                else:
                    o.append("<li>%s <small>(%s)</small></li>" % (esc(lab), "ainda não gerado" if L == "pt" else "not generated yet"))
            o.append("</ul>")
        o.append("<p>%s</p>" % ("A tabela de modelos 3D das peças está também em <code>etutti/hardware/student_v04/fornecimento/MODELOS_3D.md</code> no repositório (acima, cópia)." if L == "pt"
                                else "The table of the parts' 3D models is also in <code>etutti/hardware/student_v04/fornecimento/MODELOS_3D.md</code> in the repository (copy above)."))
        return "".join(o)
    return B(block("pt"), block("en"))


# ---------------------------------------------------------------- section 5: COMPRA.md (pt, from the electronics) and compra_en.md (en)
PAGE_NAMES = [   # (path as written in COMPRA.md, name of the same file in section 10)
    ("`principal/student_v04_gerbers.zip`", "`placa_principal_gerbers.zip`"), ("`principal/bom.csv`", "`placa_principal_bom.csv`"), ("`principal/cpl.csv`", "`placa_principal_cpl.csv`"),
    ("`regua/R8_painel2/gerbers.zip`", "`regua_R8_painel2_gerbers.zip`"), ("`regua/R8_painel2/bom.csv`", "`regua_R8_painel2_bom.csv`"), ("`regua/R8_painel2/cpl.csv`", "`regua_R8_painel2_cpl.csv`"),
]
def compra_md(L):
    if L == "en":
        f = os.path.join(HERE, "compra_en.md")
        txt = open(f, encoding="utf-8").read() if os.path.exists(f) else None
        if txt is None:
            return None
        lines = [l for l in txt.splitlines() if not l.startswith("# Student V4")]
        return "\n".join(l[1:] if l.startswith("##") else l for l in lines)
    f = os.path.join(HERE, "fab", "COMPRA.md")
    if not os.path.exists(f):
        return None
    out = []
    for ln in open(f, encoding="utf-8").read().splitlines():
        if ln.startswith("# Student V4"):
            continue
        if ln.startswith("- principal:"):
            ln = "- principal: `placa_principal_gerbers.zip`, `placa_principal_bom.csv`, `placa_principal_cpl.csv`"
        elif ln.startswith("- réguas R8"):
            ln = "- réguas R8 (painel de 2): `regua_R8_painel2_gerbers.zip`, `regua_R8_painel2_bom.csv`, `regua_R8_painel2_cpl.csv`"
        elif ln.startswith("- folhas de apoio"):
            ln = "- folhas de apoio: `LEIAME_COTACAO_principal.md`, `LEIAME_COTACAO_regua.md`, `MODELOS_3D.md`"
        elif ln.startswith("Arquivos que vão para a JLCPCB"):
            ln = "Arquivos que vão para a JLCPCB (a seção 10 desta página tem todos, com estes nomes):"
        for a, b in PAGE_NAMES:
            ln = ln.replace(a, b)
        ln = ln.replace("use a lista de conferência de `principal/LEIAME_COTACAO.md` contra `pcb/img/previa_jlc_principal_bottom.png`", "use a lista de conferência logo abaixo contra as figuras de pré-visualização")
        ln = ln.replace("comparar com `pcb/img/previa_jlc_principal_bottom.png` e a lista de `principal/LEIAME_COTACAO.md`", "comparar com as figuras de pré-visualização e a lista de conferência abaixo")
        ln = ln.replace("comparar com `previa_jlc_r8_bottom.png`", "comparar com a pré-visualização da R8")
        out.append(ln)
    return "\n".join(l[1:] if l.startswith("##") else l for l in out)


# ---------------------------------------------------------------- sections
def build():
    prepare_fallbacks()
    prepare_extra()
    prepare_previews()
    price_html, lo, hi = price_table()
    files = copy_files()
    compra_pt = compra_md("pt")
    compra_en = compra_md("en")
    compra_pt_html = md_to_html(compra_pt) if compra_pt else None
    compra_en_html = md_to_html(compra_en) if compra_en else None
    if compra_pt_html is None:
        PENDING.append("fab/COMPRA.md")
    S = []

    def section(sid, title_pt, title_en, body):
        S.append('<section id="%s"><h2>%s</h2>%s</section>' % (sid, B(esc(title_pt), esc(title_en), "span"), body))

    # 1
    hero_fig = fig("foto_instrumento", "O instrumento pronto", "The finished instrument", "O instrumento pronto (render).", "The finished instrument (render).",
                   "Foto do instrumento pronto a chegar do design.", "Photo of the finished instrument to come from the design.")
    if find_img("foto_instrumento") is None:
        hero_fig = fig("planta", "Planta do instrumento visto de cima", "Plan view of the instrument", "Planta oficial, de cima: a tela, os dois knobs e o alto-falante à esquerda; as quatro fileiras de teclas à direita. A foto virá do design.",
                       "Official plan from above: screen, two knobs and speaker on the left; the four rows of keys on the right. The photo will come from the design.")
    section("o-que-e", "1 · O que é", "1 · What it is", B(
        "<p>O <strong>eTutti Student V4</strong> é um acordeão cromático de botões, eletrônico, com <strong>32 teclas</strong> no arranjo <strong>C-griff</strong> (de G3 a F5, quatro fileiras de 8). Cada tecla é uma Gateron magnética: um sensor Hall mede a que profundidade ela está e <strong>com que velocidade</strong> foi apertada, então o toque forte soa mais forte e mais brilhante, como o fole de um acordeão.</p>"
        "<p>Ele tem <strong>som próprio</strong> (um acordeão com sete registros, que sai pelo alto-falante embutido ou pelos fones), uma <strong>tela</strong> e <strong>dois knobs</strong> para volume, registro e menu, entrada de <strong>microfone</strong> (para a sua voz entrar no som) e <strong>USB-C</strong>: carrega a bateria, grava o firmware e fala <strong>MIDI</strong> com o computador.</p>"
        "<p>É um protótipo para <strong>montar em casa</strong>: a JLCPCB solda a eletrônica, você solda dois encoders, encaixa um módulo e monta o resto com parafusos. Esta página reúne tudo o que precisa para entender, pedir, montar e tocar, sem outra ajuda.</p>"
        '<div class="status"><strong>Estado:</strong> o projeto está fechado no papel e conferido no computador. <strong>Nada foi comprado, impresso nem montado</strong>, e o firmware ainda não rodou numa placa real. Todo preço, tempo e medida aqui é estimativa, até o protótipo existir.</div>',
        "<p>The <strong>eTutti Student V4</strong> is an electronic chromatic button accordion with <strong>32 keys</strong> in the <strong>C-griff</strong> layout (G3 to F5, four rows of 8). Each key is a magnetic Gateron: a Hall sensor measures how deep it is and <strong>how fast</strong> it was pressed, so a hard touch sounds louder and brighter, like an accordion's bellows.</p>"
        "<p>It has its <strong>own sound</strong> (an accordion with seven registers, through the built-in speaker or headphones), a <strong>screen</strong> and <strong>two knobs</strong> for volume, register and menu, a <strong>microphone</strong> input (so your voice joins the sound) and <strong>USB-C</strong>: it charges the battery, loads the firmware and speaks <strong>MIDI</strong> to a computer.</p>"
        "<p>It is a prototype <strong>to build at home</strong>: JLCPCB solders the electronics, you solder two encoders, snap in a module and assemble the rest with screws. This page has everything you need to understand, order, build and play it, with no other help.</p>"
        '<div class="status"><strong>Status:</strong> the design is closed on paper and checked on the computer. <strong>Nothing has been bought, printed or built</strong>, and the firmware has not yet run on a real board. Every price, time and measure here is an estimate until the prototype exists.</div>') + hero_fig)

    # 2
    section("como-funciona", "2 · Como funciona", "2 · How it works", B(
        "<p>Em cada tecla há um ímã e, do outro lado da régua, um sensor Hall <strong>TMAG5253</strong>. As teclas ficam em quatro <strong>réguas R8</strong> (uma por fileira, 8 teclas cada), ligadas à placa principal por um cabo de seis fios. A placa principal tem o módulo <strong>MicroMod Teensy</strong> (o processador), o codec de áudio, o amplificador do alto-falante, o carregador da bateria, a tela e os knobs.</p>"
        + '<div class="diagram">' + diagram("pt") + "</div>"
        "<h3>Da tecla à nota</h3><ol>"
        "<li>Um registrador de deslocamento (74HC595) em cada régua liga <strong>uma coluna</strong> de sensores por vez; as quatro fileiras são lidas ao mesmo tempo, em quatro linhas analógicas. Uma passada pelas 8 colunas leva cerca de 0,6 ms (estimado).</li>"
        "<li>O campo do ímã cai com o cubo da distância, então o curso da tecla (0 a 100 %) é calculado por uma raiz cúbica da leitura, entre o repouso (medido ao ligar) e o fundo (aprendido e guardado).</li>"
        "<li>A nota liga em 45 % do curso e desliga em 30 %. A <strong>velocity</strong> vem do tempo que a tecla leva de 12 % a 45 %: 1 ms é o máximo, 80 ms é o mínimo.</li>"
        "<li>No acordeão, a velocity é a <strong>pressão do fole</strong>: muda o volume (cerca de 24 dB) e o brilho do som.</li></ol>"
        "<h3>Modular</h3><p>As mesmas réguas se repetem: com 48, 64 ou 80 teclas basta juntar mais réguas em cada fileira; a cadeia de ligação e a varredura crescem sem mudar a placa principal, e o case cresce pela mesma regra de comprimento. Esta página detalha só a versão de 32 teclas.</p>",
        "<p>Each key has a magnet and, on the other side of the ruler, a <strong>TMAG5253</strong> Hall sensor. The keys sit on four <strong>R8 rulers</strong> (one per row, 8 keys each), joined to the main board by a six-wire cable. The main board carries the <strong>MicroMod Teensy</strong> module (the processor), the audio codec, the speaker amplifier, the battery charger, the screen and the knobs.</p>"
        + '<div class="diagram">' + diagram("en") + "</div>"
        "<h3>From key to note</h3><ol>"
        "<li>A shift register (74HC595) on each ruler switches on <strong>one column</strong> of sensors at a time; the four rows are read together on four analog lines. One pass over the 8 columns takes about 0.6 ms (estimated).</li>"
        "<li>The magnet's field falls with the cube of distance, so the key travel (0 to 100 %) comes from a cube root of the reading, between the rest position (measured at power-up) and the bottom (learnt and stored).</li>"
        "<li>The note switches on at 45 % of travel and off at 30 %. <strong>Velocity</strong> comes from the time the key takes from 12 % to 45 %: 1 ms is the maximum, 80 ms the minimum.</li>"
        "<li>On the accordion, velocity is <strong>bellows pressure</strong>: it changes the loudness (about 24 dB) and the brightness of the sound.</li></ol>"
        "<h3>Modular</h3><p>The same rulers repeat: with 48, 64 or 80 keys you just chain more rulers on each row; the chain and the scan grow without changing the main board, and the case grows by the same length rule. This page details only the 32-key version.</p>"))

    # 3
    section("teclado", "3 · O teclado", "3 · The keyboard", B(
        "<p>32 teclas em quatro fileiras de 8, a 18,5 mm uma da outra, em malha hexagonal. A <strong>fileira 1 é a mais perto de quem toca</strong> (embaixo na figura). Cada coluna sobe uma terça menor (3 semitons), e as fileiras ficam em degraus de altura (0, 2, 4 e 7 mm) para o dedo achar a fileira. Brancas = naturais, pretas = sustenidos; <strong>C e F</strong> levam xadrez, para achar a posição no escuro.</p>"
        "<h3>C-griff (padrão)</h3>" + '<div class="kb">' + keyboard_svg("C") + "</div>"
        "<h3>B-griff</h3><p>O B-griff espelha o arranjo: as fileiras 1 e 3 trocam de lugar (e a 4 acompanha a 1). Troca-se pelo CC 24 do MIDI; o desenho das teclas não muda, só as notas.</p>" + '<div class="kb">' + keyboard_svg("B") + "</div>",
        "<p>32 keys in four rows of 8, 18.5 mm apart, on a hexagonal grid. <strong>Row 1 is nearest the player</strong> (at the bottom of the figure). Each column goes up a minor third (3 semitones), and the rows step up in height (0, 2, 4 and 7 mm) so the finger finds its row. White = naturals, black = sharps; <strong>C and F</strong> are checkered, to find your place in the dark.</p>"
        "<h3>C-griff (default)</h3>" + '<div class="kb">' + keyboard_svg("C") + "</div>"
        "<h3>B-griff</h3><p>B-griff mirrors the layout: rows 1 and 3 swap places (row 4 follows row 1). It is switched by MIDI CC 24; the keys do not change, only the notes.</p>" + '<div class="kb">' + keyboard_svg("B") + "</div>"))

    # 4
    parts_pt = ("<h3>O que vem montado e o que é de casa</h3><ul>"
                "<li><strong>JLCPCB monta:</strong> a placa principal (78 peças, todas no fundo: sensor de energia, codec, amplificador, carregador, conversor, conectores USB-C, OUT, IN, SH e M.2) e as 4 réguas R8 (32 sensores TMAG5253, 4 registradores 74HC595 e os conectores SH).</li>"
                "<li><strong>Soldado em casa:</strong> os 2 encoders EC11E18244AU e os 2 fios do alto-falante.</li>"
                "<li><strong>Encaixado ou parafusado, sem solda:</strong> módulo MicroMod Teensy (DEV-16402) com parafuso e espaçador M2,5 de náilon, tela OLED Adafruit 326 e cabo Qwiic, bateria LiPo 503450, 32 teclas Gateron KS-20 Orange, 4 cabos SH, parafusos e porcas M2, 8 pés adesivos 3M Bumpon.</li>"
                "<li><strong>Impresso (MJF PA12):</strong> base, tampa, 32 botões, 2 knobs, caixa acústica em L.</li></ul>"
                "<h3>Ferramentas</h3><p>Ferro de solda com ponta fina, solda 0,6 mm, alicate de corte, pinça fina, chave Phillips #0 não magnética, multímetro, lupa ou microscópio, lixa fina, silicone, cola quente. Parafusos e ferramentas <strong>não magnéticos</strong> perto das teclas.</p>"
                "<h3>Preço (estimativa)</h3>")
    parts_en = ("<h3>What arrives assembled and what is done at home</h3><ul>"
                "<li><strong>JLCPCB assembles:</strong> the main board (78 parts, all on the bottom: power ICs, codec, amplifier, charger, converter, the USB-C, OUT, IN, SH and M.2 connectors) and the 4 R8 rulers (32 TMAG5253 sensors, 4 74HC595 registers and the SH connectors).</li>"
                "<li><strong>Soldered at home:</strong> the 2 EC11E18244AU encoders and the 2 speaker wires.</li>"
                "<li><strong>Snapped or screwed in, no soldering:</strong> the MicroMod Teensy module (DEV-16402) with an M2.5 nylon screw and spacer, the Adafruit 326 OLED and Qwiic cable, the LiPo 503450 battery, 32 Gateron KS-20 Orange keys, 4 SH cables, M2 screws and nuts, 8 adhesive 3M Bumpon feet.</li>"
                "<li><strong>Printed (MJF PA12):</strong> base, lid, 32 buttons, 2 knobs, L-shaped acoustic box.</li></ul>"
                "<h3>Tools</h3><p>Soldering iron with a fine tip, 0.6 mm solder, side cutters, fine tweezers, non-magnetic Phillips #0 screwdriver, multimeter, magnifier or microscope, fine sandpaper, silicone, hot glue. <strong>Non-magnetic</strong> screws and tools near the keys.</p>"
                "<h3>Price (estimate)</h3>")
    expl = fig("foto_explodido", "Vista explodida do instrumento", "Exploded view of the instrument", "Vista explodida: tampa, tela, alto-falante e caixa, placa, módulo, bateria, bandeja com as quatro réguas, teclas, capas e knobs.",
               "Exploded view: lid, screen, speaker and box, board, module, battery, tray with the four rulers, keys, caps and knobs.")
    case_figs = (fig("iso_base_r15", "Isométrico da base, com os apoios numerados", "Isometric of the base, with numbered supports",
                     "A base sozinha, vista de frente e da esquerda: o berço contínuo sob cada régua (azul), os risers, as paredes de ponta, as bossas dos parafusos e os apoios numerados, com o nome da nota em cada tecla. A legenda de cada número está na própria figura (clique para ampliar).",
                     "The base alone, seen from the front-left: the continuous cradle under each ruler (blue), the risers, end walls, bolt bosses and the numbered supports, with the note name on each key. Each number's legend is in the figure itself (click to enlarge).")
                 + fig("iso_base_r15_tras", "Isométrico da base, visto de trás e da direita", "Isometric of the base, seen from the back-right",
                       "A mesma base, de trás e da direita.", "The same base, from the back-right.")
                 + fig("base_antes_depois_r15", "As pontas das réguas na base, antes e depois", "The ruler ends in the base, before and after",
                       "Antes e depois: em vermelho, as paredes e hastes de menos de 1,5 mm que a base antiga tinha nas pontas das réguas; a base nova não as tem (resta um degrau de 0,7 mm preso ao longo do comprimento na fileira 4). Figura de trabalho do design, em português.",
                       "Before and after: in red, the walls and stubs under 1.5 mm that the old base had at the ruler ends; the new base has none (one 0.7 mm step remains, attached along its length, on row 4). Design working figure, in Portuguese.")
                 + fig("planta", "Planta do instrumento", "Plan of the instrument", "Planta, de cima, com o nome da nota em cada tecla.", "Plan from above, with the note name on each key.")
                 + fig("planta_interface", "Planta da interface", "Plan of the interface", "A área da interface (esquerda): tela, knobs, alto-falante, bateria, módulo e placa.", "The interface area (left): screen, knobs, speaker, battery, module and board.")
                 + fig("corte_interface", "Cortes da interface", "Sections of the interface", "Cortes pela interface: tampa, caixa acústica, alto-falante, OLED, placa, módulo, bateria e base.", "Sections through the interface: lid, acoustic box, speaker, OLED, board, module, battery and base."))
    case_txt = B("<h3>O case: base e tampa</h3><p>A base de MJF PA12 (130 cm³) leva as quatro réguas num <strong>berço contínuo</strong>: cada régua repousa numa laje sólida da largura dela (14 mm), com bolsos só onde há peça sob a régua, em vez de dois trilhos finos. Apoia 86 % da face de baixo da régua (contra 37 %), e a régua flete 0,0013 mm a 3 N na tecla (contra 0,0151 mm). A base não tem partes frágeis: uma varredura de paredes e hastes de menos de 1,5 mm achou 11 grupos na base antiga e deixou 1 (um degrau de 0,7 mm preso ao longo do comprimento). Cada bolso de porca tem três costelas de pressão que a seguram. Embaixo há 8 pés adesivos e o furo de Ø3 para o botão PROG (passo 11).</p>",
                 "<h3>The case: base and lid</h3><p>The MJF PA12 base (130 cm³) carries the four rulers on a <strong>continuous cradle</strong>: each ruler rests on a solid slab as wide as itself (14 mm), with pockets only where a part sits under the ruler, instead of two thin rails. It supports 86 % of the ruler's underside (against 37 %), and the ruler deflects 0.0013 mm at 3 N on the key (against 0.0151 mm). The base has no fragile parts: a scan for walls and stubs under 1.5 mm found 11 groups in the old base and left 1 (a 0.7 mm step attached along its length). Each nut pocket has three pressure ribs that hold it. Underneath are 8 adhesive feet and the dia 3 hole for the PROG button (step 11).</p>")
    section("pecas", "4 · Peças e preço", "4 · Parts and price", expl + B(parts_pt, parts_en) + price_html + B(
        "<p><small>Valores de <code>fab/COMPRA.md</code> (R15V4), pedido mínimo, sem frete nem IVA. As duas placas são cotações reais do J (158 e 72); nas demais linhas o piso usa preços por quantidade e o teto, o preço de uma peça. A soma das linhas dá US$ 387–428, o mesmo número de <code>fab/COMPRA.md</code> (com HASL e montagem Economic na principal: 363–404). Nada foi comprado. <strong>Nota:</strong> a base nova tem um berço contínuo sob as réguas (apoio de 86 % contra 37 %, flecha de 0,0013 mm contra 0,0151 mm a 3 N); o design estima que ele acrescente cerca de US$ 12 à impressão (+43 cm³ de MJF), valor ainda não somado à linha do case. As peças da JLCPCB têm modelo 3D, posição, giro e pino 1 conferidos: <a href=\"arquivos/MODELOS_3D.md\">MODELOS_3D.md</a>.</small></p>",
        "<p><small>Figures from <code>fab/COMPRA.md</code> (R15V4), minimum order, no shipping or VAT. Both boards are J's real quotes (158 and 72); in the other lines the low end uses quantity prices and the high end single-piece prices. The lines add up to US$ 387–428, the same number as <code>fab/COMPRA.md</code> (with HASL and Economic assembly on the main board: 363–404). Nothing has been bought. <strong>Note:</strong> the new base has a continuous cradle under the rulers (86 % support against 37 %, deflection 0.0013 mm against 0.0151 mm at 3 N); the design estimates it adds about US$ 12 to the print (+43 cm³ of MJF), not yet added to the case line. The JLCPCB parts have their 3D model, position, rotation and pin 1 checked: <a href=\"arquivos/MODELOS_3D.md\">MODELOS_3D.md</a> (Portuguese).</small></p>") + case_txt + case_figs)

    # 5
    chk_pt = ("<h3>O que conferir na pré-visualização da JLCPCB</h3><p>Antes de pagar, compare a tela de posições da JLCPCB com as figuras abaixo (a pré-visualização própria do projeto, com os mesmos modelos 3D nas posições do CPL; <strong>o anel vermelho marca o pino 1 da placa</strong>; a vista de baixo é espelhada, porque a placa foi virada em torno do eixo vertical). "
              "Em cada ponto, <strong>se algo diferir, mande o print</strong>: nada foi subido.</p><ol>"
              "<li><strong>J601 a J604</strong> (SH de 6 vias): a boca para a <strong>borda direita</strong>, pino 1 no anel (o pad do alto, junto de J604 e J202).</li>"
              "<li><strong>J401</strong> (SH de 4 vias): a boca para <strong>cima</strong>, rumo à fenda do cabo do OLED; pino 1 do lado direito do desenho.</li>"
              "<li><strong>USB-C J201</strong> e <strong>jacks J301, J302</strong>: a boca para a <strong>borda esquerda</strong>, rente à borda.</li>"
              "<li><strong>J202</strong> (JST PH da bateria): a boca para <strong>baixo</strong> (o lado das 3 pernas), pino 1 no anel.</li>"
              "<li><strong>J101</strong> (M.2): o encaixe aberto para o lado do espaçador H101 (para a direita no desenho do topo).</li>"
              "<li><strong>Pino 1</strong> de U202 (BQ24074), U204 (TPS63001), U301 (SGTL5000), U501 (MAX98357A) e U201 (USBLC6): o ponto do corpo no canto do anel. <strong>U302</strong> e os SOT-23 (D202, D203, D205, D206, Q203): a perna isolada (1 de um lado, 2 e 3 do outro, conforme o anel).</li>"
              "<li><strong>D201</strong> (SMF5.0A): a faixa do cátodo do lado do pino 1 do footprint (pad 1 = cátodo na EasyEDA; confira).</li>"
              "<li><strong>Serigrafia:</strong> a placa traz só rótulos curtos (FILEIRA 1 a 4, OLED, BAT, USB, FONE, ENTRADA, PROG, SPK). <strong>O rótulo da FILEIRA 4 fica ao lado do J202</strong> (o conector da bateria), junto do J604: não confunda os dois.</li>"
              "<li>Os corpos de <strong>C101 a C501 (0805), FB301, U201 e C210</strong> podem aparecer deslocados dos pads: é erro do modelo da biblioteca da EasyEDA, não da posição. Se aparecerem <strong>girados</strong> ou fora por mais de 2 mm, avise.</li></ol>"
              "<p>Todas as peças da principal e das réguas têm modelo 3D na EasyEDA; pino 1 e boca já foram conferidos no projeto. A tabela completa, peça a peça, é a <a href=\"arquivos/MODELOS_3D.md\">MODELOS_3D.md</a>.</p>")
    chk_en = ("<h3>What to check in JLCPCB's preview</h3><p>Before paying, compare JLCPCB's placement screen with the figures below (the project's own preview, with the same 3D models at the CPL positions; <strong>the red ring marks the board's pin 1</strong>; the bottom view is mirrored because the board was turned about its vertical axis). "
              "At each point, <strong>if anything differs, send the screenshot</strong>: nothing has been uploaded.</p><ol>"
              "<li><strong>J601 to J604</strong> (6-way SH): mouth towards the <strong>right edge</strong>, pin 1 in the ring (the top pad, next to J604 and J202).</li>"
              "<li><strong>J401</strong> (4-way SH): mouth <strong>up</strong>, towards the OLED cable slit; pin 1 on the right of the drawing.</li>"
              "<li><strong>USB-C J201</strong> and <strong>jacks J301, J302</strong>: mouth towards the <strong>left edge</strong>, flush with it.</li>"
              "<li><strong>J202</strong> (battery JST PH): mouth <strong>down</strong> (the side of the 3 legs), pin 1 in the ring.</li>"
              "<li><strong>J101</strong> (M.2): the open slot towards the H101 spacer (to the right in the top view).</li>"
              "<li><strong>Pin 1</strong> of U202 (BQ24074), U204 (TPS63001), U301 (SGTL5000), U501 (MAX98357A) and U201 (USBLC6): the body's dot at the ring's corner. <strong>U302</strong> and the SOT-23s (D202, D203, D205, D206, Q203): the lone leg (1 on one side, 2 and 3 on the other, per the ring).</li>"
              "<li><strong>D201</strong> (SMF5.0A): the cathode stripe on the side of the footprint's pin 1 (pad 1 = cathode in EasyEDA; check).</li>"
              "<li><strong>Silkscreen:</strong> the board carries only short labels (ROW 1 to 4, OLED, BAT, USB, PHONES, IN, PROG, SPK). <strong>The ROW 4 label sits next to J202</strong> (the battery connector), by J604: do not confuse the two.</li>"
              "<li>The bodies of <strong>C101 to C501 (0805), FB301, U201 and C210</strong> may look displaced from their pads: that is an error in the EasyEDA library model, not in the position. If they look <strong>rotated</strong> or off by more than 2 mm, say so.</li></ol>"
              "<p>All parts of the main board and of the rulers have a 3D model on EasyEDA; pin 1 and mouth were already checked in the project. The full part-by-part table is <a href=\"arquivos/MODELOS_3D.md\">MODELOS_3D.md</a> (Portuguese).</p>")
    intro5 = B("<p>São <strong>duas encomendas à JLCPCB</strong> (placa principal e réguas, cada uma com os seus arquivos da seção 10), mais lojas e a impressão 3D. O texto abaixo é o <code>fab/COMPRA.md</code> da eletrônica: o que marcar em cada tela, o que comprar, onde e por quanto. <strong>Nada disso deve ser comprado antes de o protótipo inteiro ser fechado.</strong></p>"
               "<div class=\"status\"><strong>Valores reais da JLCPCB (cotações do J):</strong> placa principal <strong>US$ 158</strong> (placa 25,50 + montagem 132,62, 24 nov); régua R8 em painel de 2 <strong>US$ 72</strong> (23 nov). Na principal: <strong>Specify Stackup = No</strong> (um empilhamento especificado obriga a montagem Standard), montagem <strong>Economic</strong>, acabamento <strong>ENIG ou HASL sem chumbo</strong>. Com ENIG o site da JLCPCB passa a montagem para Standard ao subir BOM e CPL: o suporte dela confirmou que é um erro do site, e nenhuma peça da BOM é “Standard only”. A alternativa é HASL, cerca de US$ 24 mais barato no total (estimativa); o J escolhe na hora. Total do protótipo: <strong>US$ 387–428</strong> (363–404 com HASL e Economic).</div>",
               "<p>There are <strong>two JLCPCB orders</strong> (main board and rulers, each with its own files from section 10), plus shops and 3D printing. The text below is the electronics' <code>fab/COMPRA.md</code>: what to tick on each screen, what to buy, where and for how much (English translation; the Portuguese file is the source). <strong>None of this should be bought before the whole prototype design is closed.</strong></p>"
               "<div class=\"status\"><strong>Real JLCPCB figures (J's quotes):</strong> main board <strong>US$ 158</strong> (board 25.50 + assembly 132.62, 24 Nov); R8 ruler in a panel of 2 <strong>US$ 72</strong> (23 Nov). On the main board: <strong>Specify Stackup = No</strong> (a specified stackup forces Standard assembly), <strong>Economic</strong> assembly, <strong>ENIG or lead-free HASL</strong> finish. With ENIG JLCPCB's site switches assembly to Standard when BOM and CPL are uploaded: its support confirmed this is a site error, and no part on the BOM is Standard-only. The alternative is HASL, about US$ 24 cheaper in total (estimate); J chooses when ordering. Prototype total: <strong>US$ 387–428</strong> (363–404 with HASL and Economic).</div>")
    if compra_pt_html and compra_en_html:
        extra = B('<div class="compra">%s</div>' % compra_pt_html, '<div class="compra">%s</div>' % compra_en_html)
    else:
        extra = B('<p class="pend">O passo a passo com as telas da JLCPCB não foi encontrado (fab/COMPRA.md).</p>', '<p class="pend">The JLCPCB step by step was not found (fab/COMPRA.md).</p>')
    prev = (fig("previa_principal_bottom", "Pré-visualização da placa principal, fundo (onde estão as 78 peças)", "Main board preview, bottom (where the 78 parts are)",
                "Placa principal, vista de baixo (espelhada), com os modelos 3D nas posições do CPL; anel vermelho = pino 1.", "Main board, bottom view (mirrored), 3D models at the CPL positions; red ring = pin 1.")
            + fig("previa_principal_top", "Pré-visualização da placa principal, topo", "Main board preview, top",
                  "Placa principal, topo: só os pads das peças de casa (2 encoders, alto-falante).", "Main board, top: only the pads of the parts done at home (2 encoders, speaker).")
            + fig("previa_r8_bottom", "Pré-visualização da régua R8 em painel de 2, fundo", "R8 ruler preview in a panel of 2, bottom",
                  "Régua R8 em painel de 2, vista de baixo: sensores TMAG5253, registrador 74HC595 e conectores SH.", "R8 ruler in a panel of 2, bottom view: TMAG5253 sensors, 74HC595 register and SH connectors."))
    section("como-pedir", "5 · Como pedir", "5 · How to order", intro5 + extra + B(chk_pt, chk_en) + prev)

    # 6
    section("montagem", "6 · Montagem", "6 · Assembly", B("<p>Onze passos, um por figura, na ordem do projeto: as réguas são parafusadas na base antes das teclas (passos 6 a 8). Leva uma tarde. Os números das figuras estão listados em cada passo.</p>"
                                                          "<div class=\"warn\"><strong>A confirmar antes de montar:</strong> o giro do módulo MicroMod (dedos no J101, meia-lua no H101, componentes para fora) foi deduzido do modelo 3D da SparkFun e deve ser confirmado pelo desenho de montagem dela (passo 3).</div>"
                                                          "<div class=\"warn\"><strong>Cuidados:</strong> a bateria LiPo não pode ser perfurada, dobrada, aquecida nem ter os polos encostados; os formadores de rosca cortam a própria rosca no plástico (sem apertar demais); o pó de fibra de FR-4 é irritante (lixe com cuidado); toque num metal aterrado antes de pegar o módulo e as placas (descarga eletrostática); parafusos de ferro perto das teclas distorcem a leitura.</div>",
                                                          "<p>Eleven steps, one per figure, in the design's order: the rulers are bolted to the base before the keys go on (steps 6 to 8). It takes an afternoon. The numbers in each figure are listed in its step.</p>"
                                                          "<div class=\"warn\"><strong>To confirm before building:</strong> the MicroMod module's orientation (fingers into J101, half-moon on H101, components facing out) was deduced from SparkFun's 3D model and must be confirmed against their assembly drawing (step 3).</div>"
                                                          "<div class=\"warn\"><strong>Care:</strong> a LiPo cell must not be punctured, bent, heated or have its terminals shorted; thread-forming screws cut their own thread in the plastic (do not over-tighten); FR-4 dust is an irritant (sand carefully); touch earthed metal before handling the module and boards (ESD); iron screws near the keys distort the reading.</div>")
            + steps_html())

    # 7
    section("primeiro-uso", "7 · Primeiro uso", "7 · First use", B(
        "<h3>Gravar o firmware</h3><p>O firmware é um sketch do Arduino para o <strong>Teensy MicroMod</strong>. Há dois caminhos.</p>"
        "<h4>Caminho 1: Teensyduino (compila e grava)</h4><ol>"
        "<li>Instale o Arduino IDE e o <a href=\"https://www.pjrc.com/teensy/td_download.html\">Teensyduino</a>.</li>"
        "<li>Baixe o <a href=\"arquivos/student_v4_sketch.zip\">sketch</a> e abra <code>student_v4.ino</code>.</li>"
        "<li>Em <em>Ferramentas</em>: placa <strong>Teensy MicroMod</strong>, <em>USB Type</em> <strong>MIDI</strong>, <em>CPU Speed</em> <strong>396 MHz</strong>.</li>"
        "<li>Conecte o USB-C, aperte o botão <strong>PROG</strong> da placa se o Teensy não entrar no modo de gravação sozinho (com o instrumento fechado, use um palito de dente pelo furo de Ø3 na base, em x 52; y 36: <a href=\"#passo-11\">figura no passo 11</a>), e clique em <em>Carregar</em>.</li></ol>"
        "<h4>Caminho 2: o arquivo .hex (sem compilar)</h4><ol>"
        "<li>Baixe o <a href=\"arquivos/student_v4_teensyMM_midi_396.hex\" download>arquivo .hex</a> e abra o <a href=\"https://www.pjrc.com/teensy/loader.html\">Teensy Loader</a>.</li>"
        "<li><em>File → Open HEX File</em> e escolha o arquivo; ligue o USB-C; aperte <strong>PROG</strong> se pedido; <em>Program</em>.</li></ol>"
        "<div class=\"status\"><strong>Importante:</strong> o .hex da página foi compilado <strong>sem as amostras gravadas do acordeão</strong>, que vêm de uma biblioteca licenciada e não podem ser distribuídas. Sem elas o firmware usa palhetas sintetizadas (tabelas aditivas de banda limitada): o instrumento funciona igual, mas o timbre do acordeão é diferente (mais simples). Com as amostras, o firmware ocupa cerca de 1,4 MB de flash; sem elas, cerca de 180 kB.</div>"
        "<h3>Ligar</h3><ol>"
        "<li>Segure o <strong>clique do knob de volume por 2 s</strong>: o LED pisca laranja/verde durante a espera e a placa liga. Solte antes e ela desliga de novo.</li>"
        "<li>O LED fica <strong>laranja</strong> enquanto o firmware lê o repouso das teclas (cerca de 0,2 s), depois <strong>verde</strong>. Não toque nas teclas nessa hora.</li>"
        "<li>A tela mostra a bateria, o registro (VIOLIN) e o volume. Toque uma tecla: o acordeão soa no alto-falante, ou nos fones se houver um no jack OUT.</li></ol>"
        "<h3>Calibrar as teclas</h3><p>Ao ligar, o firmware mede o repouso de cada tecla. O <strong>fundo</strong> é aprendido tocando: aperte cada tecla até o fim uma vez; o valor fica guardado. Para refazer tudo: menu <em>Sistema → Calibrar</em> (ou MIDI CC 14). O <em>Teste tec.</em> do mesmo menu mostra a posição de cada tecla pelo MIDI.</p>"
        "<h3>O que o LED diz</h3><div class=\"tablewrap\"><table><tr><th>LED</th><th>Significa</th></tr>"
        "<tr><td>laranja</td><td>lendo o repouso das teclas (ao ligar) ou carregando a bateria (com USB)</td></tr>"
        "<tr><td>verde</td><td>tocando</td></tr>"
        "<tr><td>verde piscando</td><td>você girou o seletor: o registro novo ainda não foi guardado (clique para guardar)</td></tr>"
        "<tr><td>verde, um brilho a cada 2 s</td><td>repouso (5 min sem tocar)</td></tr>"
        "<tr><td>vermelho lento</td><td>bateria baixa (abaixo de 3,5 V)</td></tr>"
        "<tr><td>vermelho rápido</td><td>o codec ou algum sensor de tecla não respondeu (régua mal ligada?)</td></tr></table></div>",
        "<h3>Loading the firmware</h3><p>The firmware is an Arduino sketch for the <strong>Teensy MicroMod</strong>. There are two ways.</p>"
        "<h4>Way 1: Teensyduino (compiles and loads)</h4><ol>"
        "<li>Install the Arduino IDE and <a href=\"https://www.pjrc.com/teensy/td_download.html\">Teensyduino</a>.</li>"
        "<li>Download the <a href=\"arquivos/student_v4_sketch.zip\">sketch</a> and open <code>student_v4.ino</code>.</li>"
        "<li>Under <em>Tools</em>: board <strong>Teensy MicroMod</strong>, <em>USB Type</em> <strong>MIDI</strong>, <em>CPU Speed</em> <strong>396 MHz</strong>.</li>"
        "<li>Plug in the USB-C, press the board's <strong>PROG</strong> button if the Teensy does not enter programming mode by itself (with the instrument closed, use a toothpick through the dia 3 hole in the base, at x 52; y 36: <a href=\"#passo-11-en\">figure in step 11</a>), and click <em>Upload</em>.</li></ol>"
        "<h4>Way 2: the .hex file (no compiling)</h4><ol>"
        "<li>Download the <a href=\"arquivos/student_v4_teensyMM_midi_396.hex\" download>.hex file</a> and open the <a href=\"https://www.pjrc.com/teensy/loader.html\">Teensy Loader</a>.</li>"
        "<li><em>File → Open HEX File</em> and choose it; plug in the USB-C; press <strong>PROG</strong> if asked; <em>Program</em>.</li></ol>"
        "<div class=\"status\"><strong>Important:</strong> the page's .hex was built <strong>without the recorded accordion samples</strong>, which come from a licensed library and cannot be distributed. Without them the firmware uses synthesised reeds (band-limited additive tables): the instrument works the same, but the accordion timbre is different (simpler). With the samples the firmware takes about 1.4 MB of flash; without them, about 180 kB.</div>"
        "<h3>Switching on</h3><ol>"
        "<li>Hold the <strong>volume knob's click for 2 s</strong>: the LED blinks orange/green while you wait and the board powers up. Let go sooner and it switches off again.</li>"
        "<li>The LED is <strong>orange</strong> while the firmware reads the keys' rest position (about 0.2 s), then <strong>green</strong>. Keep your hands off the keys meanwhile.</li>"
        "<li>The screen shows the battery, the register (VIOLIN) and the volume. Play a key: the accordion sounds on the speaker, or on headphones if one is in the OUT jack.</li></ol>"
        "<h3>Calibrating the keys</h3><p>At power-up the firmware measures each key's rest. The <strong>bottom</strong> is learnt by playing: press each key all the way once; the value is stored. To redo everything: menu <em>System → Calibrate</em> (or MIDI CC 14). The <em>Key test</em> in the same menu reports each key's position over MIDI.</p>"
        "<h3>What the LED says</h3><div class=\"tablewrap\"><table><tr><th>LED</th><th>Meaning</th></tr>"
        "<tr><td>orange</td><td>reading the keys' rest (at power-up) or charging the battery (with USB)</td></tr>"
        "<tr><td>green</td><td>playing</td></tr>"
        "<tr><td>blinking green</td><td>you turned the selector: the new register is not stored yet (click to keep it)</td></tr>"
        "<tr><td>green, a flash every 2 s</td><td>resting (5 min without playing)</td></tr>"
        "<tr><td>slow red</td><td>low battery (below 3.5 V)</td></tr>"
        "<tr><td>fast red</td><td>the codec or some key sensor did not answer (ruler badly connected?)</td></tr></table></div>"))

    # 8
    regs = TELAS["registers"] if TELAS else []
    regn = {"pt": ["Bassoon (L)", "Bandoneon (ML)", "Violin (MM, padrão)", "Oboe (MH)", "Piccolo (H)", "Organ (LH)", "Clarinet (M)"],
            "en": ["Bassoon (L)", "Bandoneon (ML)", "Violin (MM, default)", "Oboe (MH)", "Piccolo (H)", "Organ (LH)", "Clarinet (M)"]}
    ui_pt = ("<h3>Os dois knobs</h3><div class=\"tablewrap\"><table><tr><th></th><th>Girar</th><th>Clicar</th><th>Segurar</th></tr>"
             "<tr><td><strong>Volume</strong></td><td>volume (3 por clique do knob); dentro do menu, muda o valor da linha</td><td>dentro do menu: volta (na primeira página, fecha o menu)</td><td><strong>2 s: liga e desliga</strong>, com ou sem menu</td></tr>"
             "<tr><td><strong>Seletor</strong> (registro)</td><td>troca o registro; dentro do menu, move o cursor</td><td>depois de girar: guarda o registro para a próxima vez; sem girar: volta ao Violin. No menu: entra, troca ou executa</td><td><strong>0,7 s: abre o menu</strong> (fecha sozinho em 30 s)</td></tr></table></div>"
             "<h3>Telas comuns</h3><p>Fora do menu a tela mostra a bateria (BAT, USB ou CHG ao carregar), o registro, o volume e a saída (fone ou alto-falante), e embaixo a barra da bateria e o medidor do microfone. Cada figura abaixo é <strong>simulada a partir do código do firmware</strong> (mesma fonte, mesmas posições, 128 × 64 pixels ampliados 4×); a tela real ainda não foi vista.</p>")
    ui_en = ("<h3>The two knobs</h3><div class=\"tablewrap\"><table><tr><th></th><th>Turn</th><th>Click</th><th>Hold</th></tr>"
             "<tr><td><strong>Volume</strong></td><td>volume (3 per knob click); inside the menu, changes the value of the line</td><td>inside the menu: back (on the first page, closes the menu)</td><td><strong>2 s: power on/off</strong>, menu or not</td></tr>"
             "<tr><td><strong>Selector</strong> (register)</td><td>changes the register; inside the menu, moves the cursor</td><td>after turning: keeps the register for next time; without turning: back to Violin. In the menu: enters, flips or runs</td><td><strong>0.7 s: opens the menu</strong> (closes itself after 30 s)</td></tr></table></div>"
             "<h3>The ordinary screens</h3><p>Outside the menu the screen shows the battery (BAT, USB or CHG when charging), the register, the volume and the output (headphones or speaker), and at the bottom the battery bar and the microphone meter. Every figure below is <strong>simulated from the firmware's own code</strong> (same font, same positions, 128 × 64 pixels enlarged 4×); the real screen has not been seen yet.</p>")
    tela_fig = fig("foto_tela", "A tela do instrumento acesa na janela da tampa", "The instrument's screen lit in the lid's window",
                   "A janela da tampa com a tela de estado acesa (render com a tela simulada a partir do código do firmware; a tela real ainda não foi vista).",
                   "The lid's window with the status screen lit (render with the screen simulated from the firmware's own code; the real screen has not been seen yet).")
    body8 = B(ui_pt, ui_en) + tela_fig + screens_gallery("status") + B(
        "<h3>Registros</h3><p>O V4 tem <strong>um instrumento: o acordeão</strong>, com sete registros (que palhetas soam), na ordem em que o seletor gira: " + ", ".join(regn["pt"]) + ".</p>",
        "<h3>Registers</h3><p>The V4 has <strong>one instrument: the accordion</strong>, with seven registers (which reeds sound), in the order the selector turns: " + ", ".join(regn["en"]) + ".</p>")
    if TELAS:
        body8 += B('<figure><img src="img/tela_registros_pt.png" width="%d" height="%d" alt="registros" loading="lazy" /><figcaption>Os sete nomes na tela, na ordem do seletor.</figcaption></figure>' % ((TELAS["w"]) * 2, (TELAS["h"]) * 4),
                   '<figure><img src="img/tela_registros_en.png" width="%d" height="%d" alt="registers" loading="lazy" /><figcaption>The seven names on screen, in selector order.</figcaption></figure>' % ((TELAS["w"]) * 2, (TELAS["h"]) * 4))
    body8 += B("<h3>A árvore completa do menu</h3><p>Clique longo no seletor. Linhas marcadas “só com microfone” só aparecem com um microfone no IN; algumas linhas da página Voz aparecem conforme o modo do harmonizador.</p>" + menu_tree_html("pt"),
               "<h3>The whole menu tree</h3><p>Long click on the selector. Lines marked “only with a microphone” appear only with a microphone in IN; some Voice lines appear depending on the harmonizer's mode.</p>" + menu_tree_html("en"))
    body8 += screens_gallery("menu")
    body8 += B("<h3>Volume, saída e microfone</h3><ul>"
               "<li><strong>Volume:</strong> o knob de volume ou Saída → Volume. O volume é digital (antes do amplificador); o alto-falante só é ligado quando não há fones no OUT.</li>"
               "<li><strong>Equalizador do alto-falante:</strong> o alto-falante de 28 mm não tem graves; Saída → EQ alto-f. corta abaixo de ~300 Hz e rebaixa 1 kHz. Com fones o equalizador não age.</li>"
               "<li><strong>Tipo mic:</strong> Sistema → Tipo mic. <em>Auto</em> reconhece o microfone sozinho (eletreto liga o bias); <em>Eletreto</em> força o bias ligado; <em>Dinâmico</em> desliga o bias (um microfone dinâmico não o quer). Cada tipo guarda seu próprio ganho.</li>"
               "<li><strong>Voz:</strong> com um microfone no IN, a página Voz põe a sua voz no som (seca, vocoder, harmonizador que segue as teclas, eco, reverb). Modos do harmonizador: <em>Fixo</em> (intervalo constante), <em>Exato</em> (cada tecla segurada vira uma voz exatamente naquela nota), <em>Ajuda</em> (puxa a voz em direção à nota) e <em>Intervalo</em> (mantém as distâncias entre as teclas). A voz vai aos fones; no alto-falante ela fica muda, a menos que você ligue Saída → Saída voz → + Alto-fal., que mostra o aviso de microfonia.</li>"
               "<li><strong>Salvar:</strong> Sistema → Salvar guarda a voz, o equalizador e o registro; o idioma e o tipo de microfone se guardam na hora.</li></ul>"
               "<h3>Bateria e desligamento</h3><p>Com bateria, o instrumento desliga sozinho abaixo de 3,3 V ou depois de <strong>15 minutos</strong> sem tecla, knob ou MIDI (aos 5 minutos o amplificador descansa e a tela diz “repouso”). Com USB ligado nada corta a energia: “desligar” apaga tudo, e um clique do volume religa. A carga é automática: LED e tela mostram CHG.</p>"
               "<h3>MIDI no computador</h3><p>Com o USB-C ligado o instrumento aparece como uma porta <strong>USB MIDI</strong> chamada “eTutti” e envia as notas com velocity. Recebe também controles (canal 1):</p>"
               "<div class=\"tablewrap\"><table><tr><th>CC</th><th>Função</th></tr><tr><td>7</td><td>volume</td></tr><tr><td>9</td><td>curva de velocity (0 fixa, 32 suave, 64 normal, 96 dura)</td></tr><tr><td>14</td><td>recalibrar as teclas (≥ 64)</td></tr><tr><td>15</td><td>teste de teclas (≥ 64 liga)</td></tr><tr><td>24</td><td>C-griff (&lt; 64) / B-griff (≥ 64)</td></tr><tr><td>26</td><td>registro (máscara de palhetas)</td></tr><tr><td>27</td><td>afinação das palhetas “molhadas” (0 a 30 cents)</td></tr><tr><td>72 / 73</td><td>soltura / ataque</td></tr><tr><td>74</td><td>filtro de tom</td></tr><tr><td>91</td><td>reverb</td></tr><tr><td>120 / 123</td><td>silenciar tudo / soltar todas as notas</td></tr></table></div>"
               "<p>Qualquer programa de música com MIDI USB serve. A página do eTuttino do site ainda não conhece o V4.</p>",
               "<h3>Volume, output and microphone</h3><ul>"
               "<li><strong>Volume:</strong> the volume knob or Output → Volume. Volume is digital (before the amplifier); the speaker is only on when nothing is in OUT.</li>"
               "<li><strong>Speaker equaliser:</strong> the 28 mm speaker has no bass; Output → Speaker EQ cuts below ~300 Hz and dips 1 kHz. With headphones it does nothing.</li>"
               "<li><strong>Mic type:</strong> System → Mic type. <em>Auto</em> recognises the microphone (electret turns the bias on); <em>Electret</em> forces the bias on; <em>Dynamic</em> turns the bias off (a dynamic mic does not want it). Each type keeps its own gain.</li>"
               "<li><strong>Voice:</strong> with a microphone in IN, the Voice page puts your voice in the sound (dry, vocoder, a harmonizer that follows the keys, echo, reverb). Harmonizer modes: <em>Fixed</em> (constant interval), <em>Exact</em> (each held key becomes a voice exactly on that note), <em>Assist</em> (pulls the voice towards the note) and <em>Interval</em> (keeps the distances between the keys). The voice goes to headphones; on the speaker it is muted unless you switch on Output → Voice out → + Speaker, which shows the feedback warning.</li>"
               "<li><strong>Save:</strong> System → Save stores the voice, the equaliser and the register; language and mic type are kept at once.</li></ul>"
               "<h3>Battery and switching off</h3><p>On battery the instrument switches itself off below 3.3 V or after <strong>15 minutes</strong> without a key, knob or MIDI (after 5 minutes the amplifier rests and the screen says “rest”). With USB plugged in nothing cuts the power: “off” darkens everything, and a volume click wakes it. Charging is automatic: the LED and screen show CHG.</p>"
               "<h3>MIDI on a computer</h3><p>With the USB-C plugged in the instrument appears as a <strong>USB MIDI</strong> port named “eTutti” and sends notes with velocity. It also receives controllers (channel 1):</p>"
               "<div class=\"tablewrap\"><table><tr><th>CC</th><th>Function</th></tr><tr><td>7</td><td>volume</td></tr><tr><td>9</td><td>velocity curve (0 fixed, 32 soft, 64 normal, 96 hard)</td></tr><tr><td>14</td><td>recalibrate the keys (≥ 64)</td></tr><tr><td>15</td><td>key test (≥ 64 on)</td></tr><tr><td>24</td><td>C-griff (&lt; 64) / B-griff (≥ 64)</td></tr><tr><td>26</td><td>register (reed mask)</td></tr><tr><td>27</td><td>tuning of the “wet” reeds (0 to 30 cents)</td></tr><tr><td>72 / 73</td><td>release / attack</td></tr><tr><td>74</td><td>tone filter</td></tr><tr><td>91</td><td>reverb</td></tr><tr><td>120 / 123</td><td>silence all / release all notes</td></tr></table></div>"
               "<p>Any music program with USB MIDI will do. The site's eTuttino page does not know the V4 yet.</p>")
    body8 += screens_gallery("aviso")
    section("interface", "8 · A interface", "8 · The interface", body8)

    # 9
    section("problemas", "9 · Problemas comuns", "9 · Common problems", B(
        "<div class=\"tablewrap\"><table><tr><th>Sintoma</th><th>O que fazer</th></tr>"
        "<tr><td>Não liga</td><td>Segure o clique do volume por 2 s inteiros. Carregue a bateria por USB. Confira o plugue da bateria no J202 e a polaridade.</td></tr>"
        "<tr><td>LED vermelho rápido</td><td>Alguma régua ou sensor não respondeu: confira o cabo SH de cada fileira (plugue até o fim, conector IN) e o módulo no M.2. Use Sistema → Teste tec. para ver qual tecla falta.</td></tr>"
        "<tr><td>Uma tecla não soa ou soa sozinha</td><td>Recalibre (Sistema → Calibrar). Veja se o botão raspa na tampa e se há aço perto do ímã.</td></tr>"
        "<tr><td>Velocity sempre igual</td><td>Troque a curva (Som → Curva vel.); recalibre.</td></tr>"
        "<tr><td>Sem som no alto-falante</td><td>Tire o plugue do OUT (com fones o alto-falante se cala). Confira os fios no J501 e o volume.</td></tr>"
        "<tr><td>Apitos (microfonia)</td><td>Mic longe do alto-falante, volume baixo, ou use fones. Ligue Captação → Antimicrof.</td></tr>"
        "<tr><td>Tela apagada ou borrada</td><td>Confira o cabo Qwiic no J401 e a ordem dos fios; endereço 0x3D ou 0x3C é testado sozinho. Se a imagem vier deslocada 2 pixels, o módulo é SH1106 e o firmware precisa de <code>OLED_SH1106 = 1</code>.</td></tr>"
        "<tr><td>O computador não vê o MIDI</td><td>Cabo USB só de carga? Use um cabo de dados. O nome é “eTutti” (o Windows pode mostrar “Teensy MIDI”).</td></tr>"
        "<tr><td>Travou, não grava mais</td><td>Segure o botão PROG por ~15 s para a fábrica do Teensy e grave de novo.</td></tr></table></div>",
        "<div class=\"tablewrap\"><table><tr><th>Symptom</th><th>What to do</th></tr>"
        "<tr><td>Does not switch on</td><td>Hold the volume click for a full 2 s. Charge the battery over USB. Check the battery plug at J202 and the polarity.</td></tr>"
        "<tr><td>Fast red LED</td><td>A ruler or sensor did not answer: check each row's SH cable (plug fully in, IN connector) and the module in the M.2. Use System → Key test to see which key is missing.</td></tr>"
        "<tr><td>A key is silent or sounds by itself</td><td>Recalibrate (System → Calibrate). See whether the button rubs the lid and whether steel is near the magnet.</td></tr>"
        "<tr><td>Velocity always the same</td><td>Change the curve (Sound → Vel curve); recalibrate.</td></tr>"
        "<tr><td>No sound on the speaker</td><td>Unplug the OUT jack (with headphones the speaker goes quiet). Check the J501 wires and the volume.</td></tr>"
        "<tr><td>Howling (feedback)</td><td>Mic away from the speaker, volume down, or use headphones. Switch on Input → Anti-feedbk.</td></tr>"
        "<tr><td>Screen blank or garbled</td><td>Check the Qwiic cable at J401 and the wire order; address 0x3D or 0x3C is tried automatically. If the picture is shifted by 2 pixels the module is an SH1106 and the firmware needs <code>OLED_SH1106 = 1</code>.</td></tr>"
        "<tr><td>The computer does not see MIDI</td><td>Charge-only USB cable? Use a data cable. The name is “eTutti” (Windows may show “Teensy MIDI”).</td></tr>"
        "<tr><td>Hung, will not load any more</td><td>Hold the PROG button for ~15 s to restore the Teensy's factory sketch and load again.</td></tr></table></div>"))

    # 10
    section("arquivos", "10 · Arquivos", "10 · Files", files_html(files) + B(
        "<p>Tudo mora em <code>etutti/hardware/student_v04/</code> (projeto) e <code>etutti/firmware/student_v4/</code> (firmware) no <a href=\"https://github.com/dataehora/beatconfused\">repositório</a>. Os dados das amostras do acordeão não são públicos.</p>",
        "<p>Everything lives in <code>etutti/hardware/student_v04/</code> (project) and <code>etutti/firmware/student_v4/</code> (firmware) in the <a href=\"https://github.com/dataehora/beatconfused\">repository</a>. The accordion sample data is not public.</p>"))

    nav = [("o-que-e", "1 O que é", "1 What it is"), ("como-funciona", "2 Como funciona", "2 How it works"), ("teclado", "3 Teclado", "3 Keyboard"),
           ("pecas", "4 Peças", "4 Parts"), ("como-pedir", "5 Pedir", "5 Order"), ("montagem", "6 Montagem", "6 Assembly"),
           ("primeiro-uso", "7 Primeiro uso", "7 First use"), ("interface", "8 Interface", "8 Interface"), ("problemas", "9 Problemas", "9 Problems"), ("arquivos", "10 Arquivos", "10 Files")]
    nav_html = "".join('<a href="#%s">%s</a>' % (i, B(esc(p), esc(e), "span")) for i, p, e in nav)

    page = """<!doctype html>
<html lang="pt">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KCCMBL7GMJ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag("js", new Date());
    gtag("config", "G-KCCMBL7GMJ");
  </script>
  <title>BeatConfused | eTutti Student V4</title>
  <meta name="description" content="eTutti Student V4: 32-key electronic chromatic button accordion with Hall-effect keys, in Portuguese and English: what it is, parts, how to order, assembly, first use and the menu." />
  <!-- Written by etutti/hardware/student_v04/pagina.py: edit the texts and the prices there.
       Part of the unlisted eTutti work in progress: kept out of the sitemap and of search results. -->
  <meta name="robots" content="noindex,nofollow" />
  <meta name="theme-color" content="#F3F1EC" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Michroma&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <link rel="stylesheet" href="styles.css?v=%(v)s" />
</head>
<body>
  <div class="stripes" aria-hidden="true"></div>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
    <div class="langbar" role="group" aria-label="Language"><button type="button" data-set="pt">Português</button><button type="button" data-set="en">English</button></div>
    <header class="hero">
      <p class="eyebrow">BeatConfused Studio</p>
      <h1>eTutti<small>STUDENT &middot; V4</small></h1>
      <p class="lead">%(lead)s</p>
    </header>
    <nav class="toc">%(nav)s</nav>
    %(sections)s
    <footer><p><small>%(foot)s</small></p></footer>
  </main>
  <script src="script.js?v=%(v)s"></script>
</body>
</html>
""" % {"v": VER, "nav": nav_html, "sections": "\n".join(S),
       "lead": B("Acordeão cromático eletrônico de 32 teclas: manual completo para entender, pedir, montar e tocar.", "32-key electronic chromatic accordion: the complete manual to understand, order, build and play it.", "span"),
       "foot": B("SPEC R15V4. Projeto não construído: preços, tempos e medidas são estimativas. Gerado por student_v04/pagina.py.", "SPEC R15V4. Not built yet: prices, times and measures are estimates. Generated by student_v04/pagina.py.", "span")}
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    open(os.path.join(OUT, "styles.css"), "w", encoding="utf-8").write(CSS)
    open(os.path.join(OUT, "script.js"), "w", encoding="utf-8").write(JS)
    print("page written; price total US$ %.0f-%.0f; pending: %s" % (lo, hi, ", ".join(sorted(set(PENDING))) or "-"))


CSS = """\
/* eTutti Student V4 page. Written by etutti/hardware/student_v04/pagina.py */
:root { --paper:#F3F1EC; --card:#FBFAF6; --ink:#2B2925; --muted:#5C574F; --line:#D8D2C4; --red:#C8402A; --orange:#E07A2C; --yellow:#E3B23C; --brown:#8A3A22; color-scheme: light; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 4.2rem; }
body { margin:0; background:var(--paper); color:var(--ink); font:400 1rem/1.6 "Inter", system-ui, sans-serif; overflow-wrap:anywhere; }
.lang-block { display:none; }
html[lang="pt"] .lang-block[data-lang="pt"], html[lang="en"] .lang-block[data-lang="en"] { display:block; }
html[lang="pt"] span.lang-block[data-lang="pt"], html[lang="en"] span.lang-block[data-lang="en"] { display:inline; }
.page { max-width:56rem; margin:0 auto; padding:0 1rem 4rem; }
a { color:var(--brown); } a:hover { color:#5E2716; }
.stripes { height:14px; background:linear-gradient(90deg,var(--red) 0 33%,var(--orange) 33% 66%,var(--yellow) 66%); }
.page .site-title { font-size:1.05rem; white-space:nowrap; display:inline-block; }
.langbar { display:flex; gap:.4rem; justify-content:flex-end; margin:.4rem 0 0; }
.langbar button { font:600 .8rem "Inter",sans-serif; padding:.3rem .8rem; border:1px solid var(--line); border-radius:999px; background:var(--card); color:var(--ink); cursor:pointer; }
.langbar button[aria-pressed="true"] { background:var(--ink); color:#fff; border-color:var(--ink); }
.hero { padding:1rem 0 .6rem; text-align:center; }
.eyebrow { margin:0; font:500 .8rem/1.2 "Inter",sans-serif; letter-spacing:.18em; text-transform:uppercase; color:var(--muted); }
.hero h1 { margin:.4rem 0 .2rem; font:400 clamp(2rem,9vw,3.2rem)/1.1 "Michroma","Space Grotesk",sans-serif; letter-spacing:.04em; }
.hero h1 small { display:block; margin-top:.4rem; font-size:.38em; letter-spacing:.3em; color:var(--brown); }
.lead { max-width:40rem; margin:.8rem auto 0; font-size:1.1rem; color:#45413A; }
nav.toc { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:.2rem .3rem; justify-content:center; margin:0 -1rem; padding:.5rem 1rem; background:rgba(243,241,236,.95); border-bottom:1px solid var(--line); }
nav.toc a { padding:.2rem .6rem; border-radius:999px; font:500 .8rem/1.4 "Inter",sans-serif; text-decoration:none; color:var(--ink); }
nav.toc a:hover { background:#E8DEC6; }
section { margin-top:2.6rem; }
section h2 { margin:0 0 .6rem; font:700 clamp(1.4rem,5vw,1.9rem)/1.2 "Space Grotesk","Inter",sans-serif; }
section h3 { margin:1.6rem 0 .4rem; font:700 1.1rem/1.3 "Space Grotesk",sans-serif; }
section h4 { margin:1.1rem 0 .3rem; font:600 1rem/1.3 "Inter",sans-serif; }
figure { margin:1rem 0; }
figure img { display:block; width:100%; height:auto; background:#fff; border-radius:6px; }
figcaption { margin-top:.4rem; font-size:.88rem; color:var(--muted); }
figure.pending { padding:1rem; border:2px dashed var(--line); border-radius:8px; color:var(--muted); text-align:center; }
.status { padding:.9rem 1.1rem; background:#FFF6DF; border:1px solid #E3C98A; border-radius:10px; margin:1rem 0; }
.warn { margin:.7rem 0; padding:.6rem .9rem; background:#FFF1EA; border:1px solid #E6B49E; border-left:5px solid var(--red); border-radius:8px; font-size:.92rem; }
.pend { color:var(--muted); font-style:italic; }
.tablewrap { overflow-x:auto; margin:.6rem 0; }
table { border-collapse:collapse; width:100%; font-size:.92rem; background:var(--card); }
th, td { padding:.45rem .6rem; border:1px solid var(--line); text-align:left; vertical-align:top; }
th { background:#EFE9D8; }
td small { display:block; color:var(--muted); }
td.num { text-align:right; white-space:nowrap; }
tr.tot td { font-weight:700; background:#EFE9D8; }
code { font-size:.88em; background:#EFE9D8; padding:0 .25em; border-radius:3px; }
.diagram { margin:1rem auto; max-width:30rem; border:1px solid var(--line); border-radius:10px; background:var(--card); }
.diagram svg, .kb svg { display:block; width:100%; height:auto; }
.bd .b1,.bd .b2,.bd .b3,.bd .b4,.bd .b5,.bd .b6,.bd .b7 { stroke:#2B2925; stroke-width:1; }
.bd .b2 { fill:#A8E1CC; } .bd .b3 { fill:#CFCBF0; } .bd .b4 { fill:#FFE29A; } .bd .b5 { fill:#BFE6D8; } .bd .b6 { fill:#F5D7C6; } .bd .b7 { fill:#F2C9B6; }
.bd .ln { stroke:#5C574F; stroke-width:1.6; }
.bd text { fill:#2B2925; font-family:"Inter",sans-serif; } .bd .t1 { font-size:13px; font-weight:600; } .bd .t2 { font-size:11px; } .bd .t3 { font-size:10px; fill:#5C574F; }
.kb { margin:.6rem 0; border:1px solid var(--line); border-radius:10px; background:var(--card); padding:.3rem; }
.kb text { font-family:"Inter",sans-serif; }
article.step { margin:1.4rem 0 2rem; padding-top:.4rem; border-top:1px solid var(--line); }
article.step h3 { margin-top:.4rem; } .n { display:inline-grid; place-items:center; width:1.8rem; height:1.8rem; border-radius:50%; background:var(--ink); color:#fff; font:700 .9rem "Inter",sans-serif; margin-right:.3rem; }
dl.meta { display:grid; gap:.2rem .8rem; grid-template-columns:auto 1fr; margin:.3rem 0; font-size:.88rem; } dl.meta dt { font-weight:600; color:var(--muted); } dl.meta dd { margin:0; }
.telas { display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(min(17rem,100%),1fr)); }
.tela { margin:0; padding:.5rem; background:var(--card); border:1px solid var(--line); border-radius:8px; }
.tela img { image-rendering:pixelated; border-radius:4px; }
ul.tree, ul.tree ul { list-style:none; margin:.2rem 0; padding-left:1rem; border-left:2px solid var(--line); } ul.tree > li { margin:.5rem 0; } ul.tree small { color:var(--muted); }
ul.files { padding-left:1.1rem; } ul.files small { color:var(--muted); display:block; }
details.compra { margin:1rem 0; padding:.6rem .9rem; background:var(--card); border:1px solid var(--line); border-radius:8px; } details.compra summary { cursor:pointer; font-weight:600; }
ol.legend { margin:.2rem 0 .8rem; padding-left:1.6rem; columns:2 14rem; font-size:.88rem; color:var(--muted); }
div.compra h3 { margin-top:1.8rem; }
footer { margin-top:3rem; color:var(--muted); text-align:center; }
"""

JS = """\
// Language switch for the Student V4 page: html[lang] selects the .lang-block shown (pattern of etutti/manuais/).
(function () {
  var KEY = "bc-studentv4-lang";
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function put(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function set(l) {
    document.documentElement.lang = l;
    document.title = l === "pt" ? "BeatConfused | eTutti Student V4 (Português)" : "BeatConfused | eTutti Student V4 (English)";
    var b = document.querySelectorAll(".langbar button");
    for (var i = 0; i < b.length; i++) b[i].setAttribute("aria-pressed", b[i].getAttribute("data-set") === l ? "true" : "false");
  }
  var q = /[?&]lang=(pt|en)/.exec(location.search);
  var start = q ? q[1] : (get() || ((navigator.language || "pt").toLowerCase().indexOf("pt") === 0 ? "pt" : "en"));
  set(start);
  var btns = document.querySelectorAll(".langbar button");
  for (var i = 0; i < btns.length; i++) btns[i].addEventListener("click", function () { var l = this.getAttribute("data-set"); put(l); set(l); });
})();
"""

if __name__ == "__main__":
    build()
