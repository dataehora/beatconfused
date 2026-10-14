"""Writes etutti/models/index.html, the eTuttino's case and family page,
in English, Portuguese and Spanish (one .lang-block each). Edit the texts
here, then:

    python models_page.py

The pictures come from models_render.py (run that first if the case
changed); the numbers below are the ones it prints.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.normpath(os.path.join(HERE, "..", "..", "models", "index.html"))

# from models_render.py / case.py
SIZE = "331 × 100"
Z_IF, Z_KEYS, Z_DECK = "33", "26.6", "17.4"
GRAMS = {"seixo": 170, "madeira": 125}     # case shell + bottom, rounded to 5 g


def num(lang, s):
    """Decimal comma for pt/es."""
    return s if lang == "en" else s.replace(".", ",")


T = {
    "en": {
        "intro": "The eTuttino in its own case: a C-griff keyboard of <strong>44 buttons on an 18.5 mm hexagonal grid</strong>, with the interface on the left. One shape, two finishes. This is the design ready to be made; to build one, see the <a href=\"../manuais/\">manuals</a>.",
        "hero_alt": "The eTuttino in the Seixo case, in perspective.",
        "finishes_kicker": "Two finishes, one shape",
        "finishes_h": "Seixo and Madeira",
        "finishes_p": "Both versions have exactly the same outside; only the material and the way it is made change. Click any picture to see it larger.",
        "seixo_h": "Seixo",
        "seixo_p": "Plastic in one colour, printed in resin (SLA) or nylon (MJF). Light-grey case, white and black buttons. 2.5 mm walls; the bottom is screwed on from below.",
        "madeira_h": "Madeira",
        "madeira_p": "White oak, cut on a 3-axis CNC in two setups (the top, then turned over for the pocket inside), oil finish. Mother-of-pearl and ebony buttons. 4 mm walls, a thin bottom cover, and a 3 mm light pipe for the LED, sanded flush with the wood.",
        "top": "From above",
        "left": "The left face: micro-USB and headphones",
        "iso": "In perspective",
        "anatomy_kicker": "Anatomy",
        "anatomy_h": "What is where",
        "anatomy_alt": "The Seixo in perspective with numbered call-outs.",
        "anatomy": [
            "<strong>Keyboard area</strong>: 44 buttons, C-griff, rows 16.02 mm apart. The opening keeps one button (15 mm) of clearance along the diagonal ends, the \"&lt;\" on the left and \"&gt;\" on the right.",
            "<strong>Rounded chamfer</strong> round the opening, 4 mm wide and 2 mm deep, in the case's own material.",
            "<strong>Screen zone</strong>: an engraving or a sticker on the eTuttino; the 1.9\" screen goes here on the eTuttiChorus.",
            "<strong>Volume</strong>: a pot.",
            "<strong>Instrument selector</strong>: an endless encoder with a click.",
            "<strong>LED</strong>: orange at power-up, green while playing, red blinking on a problem.",
            "<strong>Grille</strong> on the front part of the interface, which slopes down at 13° towards the player: ventilation on the eTuttino, the speaker's opening on the eTuttiChorus.",
            "<strong>Micro-USB</strong> on the left face, in a black insert, away from the playing hand.",
            "<strong>Headphones</strong> (3.5 mm jack), beside it.",
            "<strong>Rounded ramp</strong> from the interface (33 mm) down to the keyboard deck. It runs straight towards the front, so a flat stretch of deck is left beside row 1 for the left hand.",
        ],
        "buttons_kicker": "Buttons",
        "buttons_h": "Low domes with a skirt",
        "buttons_p": "One cap shape for every key: a low convex dome, 15 mm across, flaring to a 16.5 mm skirt (2 mm between neighbours), on a standard MX cross. White for the natural notes, black for the sharps. The Cs and Fs are white with a raised diagonal check on top, to find your place by touch.",
        "buttons_alt": "The three caps: natural, sharp and C/F. Back row Seixo colours, front row Madeira.",
        "buttons_cap": "Natural, sharp and C/F with its raised check. Back: Seixo (white and black); front: Madeira (mother-of-pearl and ebony).",
        "family_kicker": "The family",
        "family_h": "eTuttino, eTutti, eTuttiChorus",
        "family_p": "The bigger models are variations of this case. Only the eTuttino is designed in full; the other two are still in development.",
        "fam_rows": [
            ("", "eTuttino", "eTutti", "eTuttiChorus"),
            ("Status", "designed, ready to make", "in development", "in development"),
            ("Buttons", "44", "48 (one more per row)", "48"),
            ("Range", "G3–E6", "G3–G6", "G3–G6"),
            ("Length", "≈ 331 mm", "≈ 350 mm", "≈ 350 mm"),
            ("Sound", "headphones / line", "headphones / line", "speaker + headphones"),
            ("Screen", "— (engraving)", "— (engraving)", "1.9\" colour, 320 × 170"),
            ("Power", "USB", "USB", "battery or USB"),
            ("Teensy + Audio Board stack", "≈ 13 mm", "≈ 13 mm", "≤ 10 mm (under the screen)"),
        ],
        "family_note": "The eTutti adds F♯6, G6, F6 and D♯6 at the right end of rows 1 to 4: three full octaves.",
        "measures_kicker": "Measurements",
        "measures_h": "The eTuttino in numbers",
        "meas_rows": [
            ("Size", SIZE + " mm"),
            ("Height, interface", Z_IF + " mm"),
            ("Height, top of the buttons", Z_KEYS + " mm"),
            ("Height, deck round the keys", Z_DECK + " mm"),
            ("Button pitch", "18.5 mm, hexagonal"),
            ("Seixo", "resin (SLA) or nylon (MJF), one colour"),
            ("Madeira", "white oak, oil finish"),
            ("Case weight, estimated", "Seixo ≈ %d g · Madeira ≈ %d g" % (GRAMS["seixo"], GRAMS["madeira"])),
        ],
        "measures_note": "Weights are for the case alone (shell and bottom), from the model's volume: resin at 1.15 g/cm³, oak at 0.75 g/cm³.",
        "dev": "in development",
    },
    "pt": {
        "intro": "O eTuttino no seu case: um teclado C-griff de <strong>44 botões numa grade hexagonal de 18,5 mm</strong>, com a área de interface à esquerda. Uma forma, dois acabamentos. Este é o projeto pronto para fabricar; para montar o seu, veja os <a href=\"../manuais/\">manuais</a>.",
        "hero_alt": "O eTuttino no case Seixo, em perspectiva.",
        "finishes_kicker": "Dois acabamentos, mesma forma",
        "finishes_h": "Seixo e Madeira",
        "finishes_p": "As duas versões têm exatamente o mesmo exterior; só mudam o material e a fabricação. Clique numa figura para vê-la maior.",
        "seixo_h": "Seixo",
        "seixo_p": "Plástico de uma cor só, impresso em resina (SLA) ou nylon (MJF). Case cinza-claro, botões brancos e pretos. Paredes de 2,5 mm; o fundo é parafusado por baixo.",
        "madeira_h": "Madeira",
        "madeira_p": "Carvalho branco, fresado num CNC de 3 eixos em duas fixações (o topo e, virado, o bolsão interno), acabamento a óleo. Botões madrepérola e ébano. Paredes de 4 mm, tampa de fundo fina e um condutor de luz (light pipe) de 3 mm para o LED, lixado rente à madeira.",
        "top": "Vista de cima",
        "left": "A face esquerda: micro-USB e fone",
        "iso": "Em perspectiva",
        "anatomy_kicker": "Anatomia",
        "anatomy_h": "O que fica onde",
        "anatomy_alt": "O Seixo em perspectiva, com legendas numeradas.",
        "anatomy": [
            "<strong>Área do teclado</strong>: 44 botões, C-griff, fileiras a 16,02 mm. A abertura deixa a folga de um botão (15 mm) nas pontas diagonais, o \"&lt;\" à esquerda e o \"&gt;\" à direita.",
            "<strong>Chanfro arredondado</strong> em volta da abertura, de 4 mm de largura e 2 mm de queda, no mesmo material do case.",
            "<strong>Zona da tela</strong>: gravação ou adesivo no eTuttino; no eTuttiChorus, a tela de 1,9\" fica aqui.",
            "<strong>Volume</strong>: um potenciômetro.",
            "<strong>Seletor de instrumento</strong>: um encoder de giro infinito, com clique.",
            "<strong>LED</strong>: laranja ao ligar, verde tocando, vermelho piscando com problema.",
            "<strong>Grade</strong> na parte da frente da interface, que desce a 13° para quem toca: ventilação no eTuttino, saída do alto-falante no eTuttiChorus.",
            "<strong>Micro-USB</strong> na face esquerda, num inserto preto, longe da mão que toca.",
            "<strong>Fone</strong> (jack de 3,5 mm), ao lado.",
            "<strong>Rampa arredondada</strong> da interface (33 mm) até o tampo do teclado. Ela desce reta para a frente, e assim sobra um trecho de tampo plano ao lado da fileira 1 para a mão esquerda.",
        ],
        "buttons_kicker": "Botões",
        "buttons_h": "Domos baixos com saia",
        "buttons_p": "Um só formato de capa para todas as teclas: um domo convexo baixo de 15 mm, que abre numa saia de 16,5 mm (2 mm entre vizinhas), com encaixe em cruz MX. Branco nas notas naturais, preto nos sustenidos. Os Dós e Fás são brancos com um xadrez diagonal em relevo no topo, para achar a posição no tato.",
        "buttons_alt": "As três capas: natural, sustenido e Dó/Fá. Atrás, cores do Seixo; na frente, da Madeira.",
        "buttons_cap": "Natural, sustenido e Dó/Fá com o xadrez em relevo. Atrás: Seixo (branco e preto); na frente: Madeira (madrepérola e ébano).",
        "family_kicker": "A família",
        "family_h": "eTuttino, eTutti, eTuttiChorus",
        "family_p": "Os modelos maiores são variações deste case. Só o eTuttino está projetado por inteiro; os outros dois ainda estão em desenvolvimento.",
        "fam_rows": [
            ("", "eTuttino", "eTutti", "eTuttiChorus"),
            ("Situação", "projetado, pronto para fabricar", "em desenvolvimento", "em desenvolvimento"),
            ("Botões", "44", "48 (um a mais por fileira)", "48"),
            ("Extensão", "Sol3–Mi6", "Sol3–Sol6", "Sol3–Sol6"),
            ("Comprimento", "≈ 331 mm", "≈ 350 mm", "≈ 350 mm"),
            ("Som", "fone / linha", "fone / linha", "alto-falante + fone"),
            ("Tela", "— (gravação)", "— (gravação)", "1,9\" colorida, 320 × 170"),
            ("Alimentação", "USB", "USB", "bateria ou USB"),
            ("Pilha Teensy + Audio Board", "≈ 13 mm", "≈ 13 mm", "≤ 10 mm (sob a tela)"),
        ],
        "family_note": "O eTutti acrescenta Fá♯6, Sol6, Fá6 e Ré♯6 na ponta direita das fileiras 1 a 4: três oitavas completas.",
        "measures_kicker": "Medidas",
        "measures_h": "O eTuttino em números",
        "meas_rows": [
            ("Tamanho", SIZE + " mm"),
            ("Altura da interface", Z_IF + " mm"),
            ("Altura do topo dos botões", Z_KEYS + " mm"),
            ("Altura do tampo do teclado", Z_DECK + " mm"),
            ("Passo dos botões", "18,5 mm, hexagonal"),
            ("Seixo", "resina (SLA) ou nylon (MJF), uma cor"),
            ("Madeira", "carvalho branco, acabamento a óleo"),
            ("Peso do case, estimado", "Seixo ≈ %d g · Madeira ≈ %d g" % (GRAMS["seixo"], GRAMS["madeira"])),
        ],
        "measures_note": "Os pesos são só do case (corpo e fundo), a partir do volume do modelo: resina a 1,15 g/cm³, carvalho a 0,75 g/cm³.",
        "dev": "em desenvolvimento",
    },
    "es": {
        "intro": "El eTuttino en su propia caja: un teclado C-griff de <strong>44 botones en una rejilla hexagonal de 18,5 mm</strong>, con la zona de interfaz a la izquierda. Una forma, dos acabados. Es el diseño listo para fabricar; para armar el tuyo, mira los <a href=\"../manuais/\">manuales</a>.",
        "hero_alt": "El eTuttino en la caja Seixo, en perspectiva.",
        "finishes_kicker": "Dos acabados, la misma forma",
        "finishes_h": "Seixo y Madeira",
        "finishes_p": "Las dos versiones tienen exactamente el mismo exterior; solo cambian el material y la fabricación. Haz clic en una figura para verla más grande.",
        "seixo_h": "Seixo",
        "seixo_p": "Plástico de un solo color, impreso en resina (SLA) o nailon (MJF). Caja gris claro, botones blancos y negros. Paredes de 2,5 mm; el fondo se atornilla desde abajo.",
        "madeira_h": "Madeira",
        "madeira_p": "Roble blanco, fresado en un CNC de 3 ejes en dos sujeciones (la cara superior y, dada la vuelta, el vaciado interior), acabado al aceite. Botones nácar y ébano. Paredes de 4 mm, una tapa de fondo fina y un conductor de luz (light pipe) de 3 mm para el LED, lijado a ras de la madera.",
        "top": "Vista desde arriba",
        "left": "La cara izquierda: micro-USB y auriculares",
        "iso": "En perspectiva",
        "anatomy_kicker": "Anatomía",
        "anatomy_h": "Qué va dónde",
        "anatomy_alt": "El Seixo en perspectiva, con llamadas numeradas.",
        "anatomy": [
            "<strong>Zona del teclado</strong>: 44 botones, C-griff, filas a 16,02 mm. La abertura deja la holgura de un botón (15 mm) en los extremos diagonales, el \"&lt;\" a la izquierda y el \"&gt;\" a la derecha.",
            "<strong>Chaflán redondeado</strong> alrededor de la abertura, de 4 mm de ancho y 2 mm de caída, en el mismo material de la caja.",
            "<strong>Zona de la pantalla</strong>: grabado o adhesivo en el eTuttino; en el eTuttiChorus va aquí la pantalla de 1,9\".",
            "<strong>Volumen</strong>: un potenciómetro.",
            "<strong>Selector de instrumento</strong>: un encoder sin fin, con clic.",
            "<strong>LED</strong>: naranja al encender, verde al tocar, rojo parpadeando si hay un problema.",
            "<strong>Rejilla</strong> en la parte delantera de la interfaz, que baja a 13° hacia quien toca: ventilación en el eTuttino, salida del altavoz en el eTuttiChorus.",
            "<strong>Micro-USB</strong> en la cara izquierda, en un inserto negro, lejos de la mano que toca.",
            "<strong>Auriculares</strong> (jack de 3,5 mm), al lado.",
            "<strong>Rampa redondeada</strong> desde la interfaz (33 mm) hasta la cubierta del teclado. Baja recta hacia delante, y así queda un tramo de cubierta plana junto a la fila 1 para la mano izquierda.",
        ],
        "buttons_kicker": "Botones",
        "buttons_h": "Domos bajos con faldón",
        "buttons_p": "Una sola forma de tapa para todas las teclas: un domo convexo bajo de 15 mm que se abre en un faldón de 16,5 mm (2 mm entre vecinas), con encaje en cruz MX. Blanco en las notas naturales, negro en los sostenidos. Los Do y Fa son blancos con un damero diagonal en relieve arriba, para encontrar la posición al tacto.",
        "buttons_alt": "Las tres tapas: natural, sostenido y Do/Fa. Detrás, colores del Seixo; delante, de la Madeira.",
        "buttons_cap": "Natural, sostenido y Do/Fa con su damero en relieve. Detrás: Seixo (blanco y negro); delante: Madeira (nácar y ébano).",
        "family_kicker": "La familia",
        "family_h": "eTuttino, eTutti, eTuttiChorus",
        "family_p": "Los modelos mayores son variaciones de esta caja. Solo el eTuttino está diseñado por completo; los otros dos siguen en desarrollo.",
        "fam_rows": [
            ("", "eTuttino", "eTutti", "eTuttiChorus"),
            ("Estado", "diseñado, listo para fabricar", "en desarrollo", "en desarrollo"),
            ("Botones", "44", "48 (uno más por fila)", "48"),
            ("Extensión", "Sol3–Mi6", "Sol3–Sol6", "Sol3–Sol6"),
            ("Largo", "≈ 331 mm", "≈ 350 mm", "≈ 350 mm"),
            ("Sonido", "auriculares / línea", "auriculares / línea", "altavoz + auriculares"),
            ("Pantalla", "— (grabado)", "— (grabado)", "1,9\" a color, 320 × 170"),
            ("Alimentación", "USB", "USB", "batería o USB"),
            ("Pila Teensy + Audio Board", "≈ 13 mm", "≈ 13 mm", "≤ 10 mm (bajo la pantalla)"),
        ],
        "family_note": "El eTutti añade Fa♯6, Sol6, Fa6 y Re♯6 en el extremo derecho de las filas 1 a 4: tres octavas completas.",
        "measures_kicker": "Medidas",
        "measures_h": "El eTuttino en números",
        "meas_rows": [
            ("Tamaño", SIZE + " mm"),
            ("Altura de la interfaz", Z_IF + " mm"),
            ("Altura de la parte superior de los botones", Z_KEYS + " mm"),
            ("Altura de la cubierta del teclado", Z_DECK + " mm"),
            ("Paso de los botones", "18,5 mm, hexagonal"),
            ("Seixo", "resina (SLA) o nailon (MJF), un color"),
            ("Madeira", "roble blanco, acabado al aceite"),
            ("Peso de la caja, estimado", "Seixo ≈ %d g · Madeira ≈ %d g" % (GRAMS["seixo"], GRAMS["madeira"])),
        ],
        "measures_note": "Los pesos son solo de la caja (cuerpo y fondo), a partir del volumen del modelo: resina a 1,15 g/cm³, roble a 0,75 g/cm³.",
        "dev": "en desarrollo",
    },
}


def fig(src, alt, cap=None, cls="wide", sm=True):
    small = src.replace(".jpg", "-sm.jpg") if sm else src
    cap = alt if cap is None else cap
    return (f'<figure class="{cls}">\n'
            f'  <a class="zoomable" href="img/{src}"><img src="img/{small}" alt="{alt}" loading="lazy" /></a>\n'
            + (f'  <figcaption>{cap}</figcaption>\n' if cap else '')
            + '</figure>')


def block(lang):
    t = T[lang]
    n = lambda s: num(lang, s)
    o = [f'<div class="lang-block" data-lang="{lang}">']
    o.append(f'<p class="manual-intro">{t["intro"]}</p>')
    o.append(fig("seixo_iso.jpg", t["hero_alt"], cls="wide hero-figure"))
    # finishes
    o.append(f'<section class="manual" id="{lang}-finishes">')
    o.append(f'<p class="manual-kicker">{t["finishes_kicker"]}</p><h2>{t["finishes_h"]}</h2><p>{t["finishes_p"]}</p>')
    o.append('<div class="finish-grid">')
    for v in ("seixo", "madeira"):
        o.append(f'<div class="finish"><h3>{t[v + "_h"]}</h3><p>{t[v + "_p"]}</p>')
        o.append(fig(f"{v}_top.jpg", f'{t[v + "_h"]} · {t["top"]}', cls=""))
        o.append(fig(f"{v}_left.jpg", f'{t[v + "_h"]} · {t["left"]}', cls=""))
        if v == "madeira":
            o.append(fig("madeira_iso.jpg", f'{t[v + "_h"]} · {t["iso"]}', cls=""))
        o.append('</div>')
    o.append('</div></section>')
    # anatomy
    o.append(f'<section class="manual" id="{lang}-anatomy">')
    o.append(f'<p class="manual-kicker">{t["anatomy_kicker"]}</p><h2>{t["anatomy_h"]}</h2>')
    o.append(fig("anatomy.jpg", t["anatomy_alt"], cap=""))
    o.append('<ol class="anatomy-list">' + "".join(f"<li>{x}</li>" for x in t["anatomy"]) + "</ol>")
    o.append('</section>')
    # buttons
    o.append(f'<section class="manual" id="{lang}-buttons">')
    o.append(f'<p class="manual-kicker">{t["buttons_kicker"]}</p><h2>{t["buttons_h"]}</h2><p>{t["buttons_p"]}</p>')
    o.append(fig("keycaps.jpg", t["buttons_alt"], cap=t["buttons_cap"]))
    o.append('</section>')
    # family
    o.append(f'<section class="manual" id="{lang}-family">')
    o.append(f'<p class="manual-kicker">{t["family_kicker"]}</p><h2>{t["family_h"]}</h2><p>{t["family_p"]}</p>')
    head, *rows = t["fam_rows"]
    o.append('<div class="table-wrap"><table>')
    o.append('<thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + '</tr></thead><tbody>')
    for r in rows:
        cells = []
        for c in r[1:]:
            c = n(c) if any(ch.isdigit() for ch in c) else c
            cells.append(f'<td><span class="tag-dev">{c}</span></td>' if c == t["dev"] else f"<td>{c}</td>")
        o.append(f"<tr><td>{r[0]}</td>" + "".join(cells) + "</tr>")
    o.append('</tbody></table></div>')
    o.append(f'<p>{t["family_note"]}</p>')
    o.append('</section>')
    # measurements
    o.append(f'<section class="manual" id="{lang}-measures">')
    o.append(f'<p class="manual-kicker">{t["measures_kicker"]}</p><h2>{t["measures_h"]}</h2>')
    o.append('<div class="table-wrap"><table><tbody>')
    for k, v in t["meas_rows"]:
        o.append(f"<tr><th scope=\"row\">{k}</th><td>{n(v)}</td></tr>")
    o.append('</tbody></table></div>')
    o.append(f'<div class="callout"><p>{t["measures_note"]}</p></div>')
    o.append('</section>')
    o.append('</div>')
    return "\n".join(o)


HEAD = """<!doctype html>
<html lang="en">
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
  <title data-i18n="meta.title">BeatConfused | eTuttino case</title>
  <meta
    name="description"
    content="The eTuttino's case in two finishes, Seixo (resin) and Madeira (white oak), its anatomy, buttons and measurements, and the eTutti family."
    data-i18n-attr="content:meta.description"
  />
  <!-- Generated by etutti/hardware/case/models_page.py: edit the texts there.
       Part of the unlisted eTutti work in progress: kept out of the sitemap
       and out of search results until it's ready. -->
  <meta name="robots" content="noindex,nofollow" />
  <meta name="theme-color" content="#10131d" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Marck+Script&display=swap"
    rel="stylesheet"
  />
  <link rel="stylesheet" href="/shared/tuner-common.css?v=20260913" />
  <link rel="stylesheet" href="../manuais/styles.css?v=20261023" />
  <link rel="stylesheet" href="styles.css?v=20261014" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <link rel="stylesheet" href="/i18n/i18n.css?v=20261003" />
</head>
<body>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
    <header class="hero">
      <p class="eyebrow" data-i18n="hero.eyebrow">BeatConfused Studio</p>
      <h1 data-i18n="hero.title">The eTuttino's case</h1>
    </header>
    <p class="manual-back"><a href="../" data-i18n="nav.back">← Back to eTutti</a></p>
"""

TAIL = """  </main>

  <script>
    // The page text is written out once per language (.lang-block); these
    // strings only cover the page chrome.
    window.BC_STRINGS = {
      en: {
        "meta.title": "BeatConfused | eTuttino case",
        "meta.description": "The eTuttino's case in two finishes, Seixo (resin) and Madeira (white oak), its anatomy, buttons and measurements, and the eTutti family.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "The eTuttino's case",
        "nav.back": "← Back to eTutti",
      },
      pt: {
        "meta.title": "BeatConfused | Case do eTuttino",
        "meta.description": "O case do eTuttino em dois acabamentos, Seixo (resina) e Madeira (carvalho branco), a anatomia, os botões e as medidas, e a família eTutti.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "O case do eTuttino",
        "nav.back": "← Voltar ao eTutti",
      },
      es: {
        "meta.title": "BeatConfused | Caja del eTuttino",
        "meta.description": "La caja del eTuttino en dos acabados, Seixo (resina) y Madeira (roble blanco), su anatomía, botones y medidas, y la familia eTutti.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "La caja del eTuttino",
        "nav.back": "← Volver al eTutti",
      },
    };
  </script>
  <script src="../manuais/lightbox.js?v=20261021"></script>
  <script src="/i18n/i18n.js?v=20261003"></script>
</body>
</html>
"""


def main():
    body = "\n".join(block(l) for l in ("en", "pt", "es"))
    body = "\n".join("    " + line if line else line for line in body.split("\n"))
    with open(PAGE, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEAD + body + "\n" + TAIL)
    print(PAGE)


if __name__ == "__main__":
    main()
