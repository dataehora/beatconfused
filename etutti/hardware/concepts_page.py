"""Writes etutti/models/index.html, the concept-layouts page, from the
texts below (en/pt/es) -- the page stays a plain static file like the rest
of the site; edit here and re-run:

    python concepts_page.py

Pictures and diagrams come from concepts_render.py / concepts.py.
"""
import os

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "index.html"))

L = {
 "en": {
  "intro": "Three concepts built from one design: the <strong>eTuttino</strong>, the <strong>eTutti</strong> and the <strong>eTuttiChorus</strong>. Each one keeps everything the one before it has and adds to it. These are layouts to look at and compare, not build instructions: to build the current eTuttino, see the <a href=\"../manuais/\">manuals</a>.",
  "fig_all": "Drawn to the same scale, the three models differ only at the right end (one more key per row) and in the grip (screen and speaker). Click any picture to see it in high resolution.",
  "shared_kicker": "The common design", "shared_h": "A keyboard with a grip",
  "shared_p": [
   "Every model starts with the same left end: a <strong>grip</strong> for the left hand. It is the tallest part of the case, but kept as low as the electronics inside allow: <strong>30.5 mm</strong> from the table, a comfortable thickness to hold, with the thumb on top and the fingers underneath. It is <strong>76 mm</strong> long, room for the four fingers, and the edges the hand meets are rounded.",
   "Inside it, in the front half against the left face, sit the <strong>Teensy 4.0 and the Audio Board</strong>, stacked as on the eTuttino board (19.8 mm tall). The USB socket and the headphone output come out of the grip's left face, away from the playing hand. The back half of the grip is left free: the eTuttiChorus fills it with the screen and the battery.",
   "Just before the keys, a <strong>ramp</strong> takes the case down to the keyboard's height (15.7 mm, 26.5 mm to the top of the keys) and leaves about 20 mm between the grip and the nearest key top, so the playing hand has room. The keyboard is the eTuttino's: 19.05 mm button pitch, four staggered rows, C-griff, row 1 nearest the player.",
  ],
  "fig_plan": "Top view, to scale: grip, ramp and keyboard. Dashed: inside the case.",
  "specs": ["Keys", "Range", "Size", "Grip", "Keyboard", "In the grip"],
  "spec_h": "Height: {grip} mm grip, {deck} mm keyboard ({keys} mm to the key tops)",
  "m": {
   "etuttino": {"kicker": "Model 1 · compact", "desc": "The keyboard, a power LED, USB and audio out.",
     "p": ["The eTuttino's 44 keys (C-griff, G3–E6) and nothing more on the outside: one LED by the ramp, the USB socket and the headphone output in the grip's left face. The grip already has the room the bigger models use."],
     "inside": "Teensy 4.0 + Audio Board, LED; back half free"},
   "etutti": {"kicker": "Model 2 · three octaves", "desc": "The same layout, every row one key longer: G3–G6.",
     "p": ["The same grip and the same button layout, with one more key at the right end of every row: row 1 up to F♯6, row 2 up to G6, row 3 up to F6 and row 4 up to D♯6. That makes <strong>48 keys and exactly three octaves</strong>, G3 to G6, for 19 mm more length."],
     "inside": "the same as the eTuttino"},
   "etutti_chorus": {"kicker": "Model 3 · stand-alone", "desc": "The eTutti with a battery, a speaker and a screen.",
     "p": ["The eTutti made portable: it plays without a computer or a cable. Everything new goes in the grip, so the keyboard doesn't change.",
           "On top, towards the back, a <strong>1.9-inch colour screen</strong> (320 × 170, the size and place of the Corsair Vanguard 96's LCD) for the instrument, register and volume. In front of it, beside the electronics, a discreet <strong>round speaker grille</strong> over a small 28 mm driver, the way some keyboards hide notebook speakers in their case. Under the screen, a <strong>rechargeable battery</strong> (3.7 V, about 2000 mAh). A power switch joins the USB socket and the headphone output on the left face; the USB socket also charges the battery."],
     "inside": "Teensy 4.0 + Audio Board, screen, speaker, battery, LED"},
  },
  "fig_iso": "{name} in perspective.", "fig_left": "The left end: the grip, with the sockets in its left face.",
  "fig_top": "From above.", "fig_grip": "The grip: the screen at the back, the speaker grille in front of it, the LED by the ramp.",
  "cmp_h": "Side by side", "cmp_cols": ["", "eTuttino", "eTutti", "eTuttiChorus"],
  "cmp_rows": [("Keys", "44", "48", "48"), ("Range", "G3–E6", "G3–G6", "G3–G6"), ("Size", "339 × 100 mm", "358 × 100 mm", "358 × 100 mm"),
               ("Sound", "headphone / line out", "headphone / line out", "built-in speaker + headphone out"), ("Screen", "—", "—", '1.9" colour'),
               ("Power", "USB", "USB", "battery or USB")],
  "note": "Sizes are design targets of the concept, worked out from the eTuttino's parts; they will move when a model is detailed into a real board and case.",
  "back": "← Back to eTutti", "toc_kicker": "Models",
 },
 "pt": {
  "intro": "Três conceitos feitos a partir de um mesmo projeto: o <strong>eTuttino</strong>, o <strong>eTutti</strong> e o <strong>eTuttiChorus</strong>. Cada um mantém tudo o que o anterior tem e acrescenta algo. São layouts para ver e comparar, não instruções de montagem: para montar o eTuttino atual, veja os <a href=\"../manuais/\">manuais</a>.",
  "fig_all": "Na mesma escala, os três modelos só diferem na ponta direita (uma tecla a mais por fileira) e na pega (tela e alto-falante). Clique em qualquer imagem para ver em alta resolução.",
  "shared_kicker": "O projeto em comum", "shared_h": "Um teclado com pega",
  "shared_p": [
   "Todos os modelos começam com a mesma ponta esquerda: uma <strong>pega</strong> para a mão esquerda. É a parte mais alta da caixa, mas tão baixa quanto a eletrônica dentro dela permite: <strong>30,5 mm</strong> da mesa, uma espessura confortável para segurar, com o polegar em cima e os dedos por baixo. Ela tem <strong>76 mm</strong> de comprimento, espaço para os quatro dedos, e as bordas que a mão toca são arredondadas.",
   "Dentro dela, na metade da frente e encostados na face esquerda, ficam o <strong>Teensy 4.0 e a Audio Board</strong>, empilhados como na placa do eTuttino (19,8 mm de altura). O USB e a saída de fone saem pela face esquerda da pega, longe da mão que toca. A metade de trás da pega fica livre: o eTuttiChorus a ocupa com a tela e a bateria.",
   "Logo antes das teclas, uma <strong>rampa</strong> desce a caixa até a altura do teclado (15,7 mm, 26,5 mm até o topo das teclas) e deixa uns 20 mm entre a pega e o topo da tecla mais próxima, para a mão que toca ter espaço. O teclado é o do eTuttino: botões a 19,05 mm, quatro fileiras desencontradas, C-griff, fileira 1 mais perto de quem toca.",
  ],
  "fig_plan": "Vista de cima, em escala: pega, rampa e teclado. Tracejado: dentro da caixa.",
  "specs": ["Teclas", "Extensão", "Tamanho", "Pega", "Teclado", "Na pega"],
  "spec_h": "Altura: pega {grip} mm, teclado {deck} mm ({keys} mm até o topo das teclas)",
  "m": {
   "etuttino": {"kicker": "Modelo 1 · compacto", "desc": "O teclado, um LED, USB e saída de áudio.",
     "p": ["As 44 teclas do eTuttino (C-griff, Sol3–Mi6) e nada mais por fora: um LED junto à rampa, o USB e a saída de fone na face esquerda da pega. A pega já tem o espaço que os modelos maiores usam."],
     "inside": "Teensy 4.0 + Audio Board, LED; metade de trás livre"},
   "etutti": {"kicker": "Modelo 2 · três oitavas", "desc": "A mesma disposição, cada fileira com uma tecla a mais: Sol3–Sol6.",
     "p": ["A mesma pega e a mesma disposição dos botões, com uma tecla a mais na ponta direita de cada fileira: fileira 1 até Fá♯6, fileira 2 até Sol6, fileira 3 até Fá6 e fileira 4 até Ré♯6. São <strong>48 teclas e exatamente três oitavas</strong>, de Sol3 a Sol6, com 19 mm a mais de comprimento."],
     "inside": "o mesmo do eTuttino"},
   "etutti_chorus": {"kicker": "Modelo 3 · independente", "desc": "O eTutti com bateria, alto-falante e tela.",
     "p": ["O eTutti portátil: toca sem computador e sem cabo. Tudo o que é novo fica na pega, então o teclado não muda.",
           "Em cima, na parte de trás, uma <strong>tela colorida de 1,9 polegada</strong> (320 × 170, o tamanho e o lugar da tela do Corsair Vanguard 96) para instrumento, registro e volume. À frente dela, ao lado da eletrônica, uma <strong>grade redonda de alto-falante</strong>, discreta, sobre um alto-falante pequeno de 28 mm, como alguns teclados escondem alto-falantes de notebook na caixa. Sob a tela, uma <strong>bateria recarregável</strong> (3,7 V, cerca de 2000 mAh). Uma chave liga/desliga se junta ao USB e à saída de fone na face esquerda; o próprio USB carrega a bateria."],
     "inside": "Teensy 4.0 + Audio Board, tela, alto-falante, bateria, LED"},
  },
  "fig_iso": "{name} em perspectiva.", "fig_left": "A ponta esquerda: a pega, com as conexões na face esquerda.",
  "fig_top": "Visto de cima.", "fig_grip": "A pega: a tela atrás, a grade do alto-falante à frente dela, o LED junto à rampa.",
  "cmp_h": "Lado a lado", "cmp_cols": ["", "eTuttino", "eTutti", "eTuttiChorus"],
  "cmp_rows": [("Teclas", "44", "48", "48"), ("Extensão", "Sol3–Mi6", "Sol3–Sol6", "Sol3–Sol6"), ("Tamanho", "339 × 100 mm", "358 × 100 mm", "358 × 100 mm"),
               ("Som", "fone / saída de linha", "fone / saída de linha", "alto-falante + saída de fone"), ("Tela", "—", "—", "1,9\" colorida"),
               ("Energia", "USB", "USB", "bateria ou USB")],
  "note": "As medidas são metas do conceito, calculadas a partir das peças do eTuttino; elas vão mudar quando um modelo for detalhado em placa e caixa de verdade.",
  "back": "← Voltar ao eTutti", "toc_kicker": "Modelos",
 },
 "es": {
  "intro": "Tres conceptos hechos a partir de un mismo diseño: el <strong>eTuttino</strong>, el <strong>eTutti</strong> y el <strong>eTuttiChorus</strong>. Cada uno conserva todo lo que tiene el anterior y le añade algo. Son layouts para ver y comparar, no instrucciones de montaje: para montar el eTuttino actual, mira los <a href=\"../manuais/\">manuales</a>.",
  "fig_all": "A la misma escala, los tres modelos solo cambian en el extremo derecho (una tecla más por fila) y en el agarre (pantalla y altavoz). Haz clic en cualquier imagen para verla en alta resolución.",
  "shared_kicker": "El diseño común", "shared_h": "Un teclado con agarre",
  "shared_p": [
   "Todos los modelos empiezan con el mismo extremo izquierdo: un <strong>agarre</strong> para la mano izquierda. Es la parte más alta de la caja, pero tan baja como lo permite la electrónica que lleva dentro: <strong>30,5 mm</strong> desde la mesa, un grosor cómodo para sujetar, con el pulgar arriba y los dedos por debajo. Mide <strong>76 mm</strong> de largo, sitio para los cuatro dedos, y los bordes que toca la mano están redondeados.",
   "Dentro, en la mitad delantera y contra la cara izquierda, van el <strong>Teensy 4.0 y la Audio Board</strong>, apilados como en la placa del eTuttino (19,8 mm de alto). El USB y la salida de auriculares salen por la cara izquierda del agarre, lejos de la mano que toca. La mitad trasera del agarre queda libre: el eTuttiChorus la ocupa con la pantalla y la batería.",
   "Justo antes de las teclas, una <strong>rampa</strong> baja la caja hasta la altura del teclado (15,7 mm, 26,5 mm hasta la parte de arriba de las teclas) y deja unos 20 mm entre el agarre y la tecla más cercana, para que la mano que toca tenga sitio. El teclado es el del eTuttino: botones a 19,05 mm, cuatro filas desfasadas, C-griff, la fila 1 la más cercana a quien toca.",
  ],
  "fig_plan": "Vista desde arriba, a escala: agarre, rampa y teclado. Discontinuo: dentro de la caja.",
  "specs": ["Teclas", "Extensión", "Tamaño", "Agarre", "Teclado", "En el agarre"],
  "spec_h": "Altura: agarre {grip} mm, teclado {deck} mm ({keys} mm hasta las teclas)",
  "m": {
   "etuttino": {"kicker": "Modelo 1 · compacto", "desc": "El teclado, un LED, USB y salida de audio.",
     "p": ["Las 44 teclas del eTuttino (C-griff, Sol3–Mi6) y nada más por fuera: un LED junto a la rampa, el USB y la salida de auriculares en la cara izquierda del agarre. El agarre ya tiene el sitio que usan los modelos más grandes."],
     "inside": "Teensy 4.0 + Audio Board, LED; mitad trasera libre"},
   "etutti": {"kicker": "Modelo 2 · tres octavas", "desc": "La misma disposición, cada fila con una tecla más: Sol3–Sol6.",
     "p": ["El mismo agarre y la misma disposición de botones, con una tecla más al final de cada fila: la fila 1 hasta Fa♯6, la fila 2 hasta Sol6, la fila 3 hasta Fa6 y la fila 4 hasta Re♯6. Son <strong>48 teclas y exactamente tres octavas</strong>, de Sol3 a Sol6, con 19 mm más de largo."],
     "inside": "lo mismo que el eTuttino"},
   "etutti_chorus": {"kicker": "Modelo 3 · autónomo", "desc": "El eTutti con batería, altavoz y pantalla.",
     "p": ["El eTutti portátil: suena sin ordenador y sin cable. Todo lo nuevo va en el agarre, así que el teclado no cambia.",
           "Arriba, hacia atrás, una <strong>pantalla a color de 1,9 pulgadas</strong> (320 × 170, el tamaño y el sitio de la pantalla del Corsair Vanguard 96) para instrumento, registro y volumen. Delante, junto a la electrónica, una <strong>rejilla redonda de altavoz</strong>, discreta, sobre un altavoz pequeño de 28 mm, como algunos teclados esconden altavoces de portátil en la caja. Bajo la pantalla, una <strong>batería recargable</strong> (3,7 V, unos 2000 mAh). Un interruptor de encendido se une al USB y a la salida de auriculares en la cara izquierda; el mismo USB carga la batería."],
     "inside": "Teensy 4.0 + Audio Board, pantalla, altavoz, batería, LED"},
  },
  "fig_iso": "{name} en perspectiva.", "fig_left": "El extremo izquierdo: el agarre, con las conexiones en la cara izquierda.",
  "fig_top": "Visto desde arriba.", "fig_grip": "El agarre: la pantalla detrás, la rejilla del altavoz delante, el LED junto a la rampa.",
  "cmp_h": "Lado a lado", "cmp_cols": ["", "eTuttino", "eTutti", "eTuttiChorus"],
  "cmp_rows": [("Teclas", "44", "48", "48"), ("Extensión", "Sol3–Mi6", "Sol3–Sol6", "Sol3–Sol6"), ("Tamaño", "339 × 100 mm", "358 × 100 mm", "358 × 100 mm"),
               ("Sonido", "auriculares / línea", "auriculares / línea", "altavoz + salida de auriculares"), ("Pantalla", "—", "—", "1,9\" a color"),
               ("Alimentación", "USB", "USB", "batería o USB")],
  "note": "Las medidas son objetivos del concepto, calculados a partir de las piezas del eTuttino; cambiarán cuando un modelo se detalle en placa y caja de verdad.",
  "back": "← Volver al eTutti", "toc_kicker": "Modelos",
 },
}

NAMES = {"etuttino": "eTuttino", "etutti": "eTutti", "etutti_chorus": "eTuttiChorus"}
SPEC = {"etuttino": ("44", {"en": "G3–E6", "pt": "Sol3–Mi6", "es": "Sol3–Mi6"}, "339 × 100 mm"),
        "etutti": ("48", {"en": "G3–G6", "pt": "Sol3–Sol6", "es": "Sol3–Sol6"}, "358 × 100 mm"),
        "etutti_chorus": ("48", {"en": "G3–G6", "pt": "Sol3–Sol6", "es": "Sol3–Sol6"}, "358 × 100 mm")}


def fig(src, alt, cap, wide=True, plan=False):
    big = src.replace("-sm.jpg", ".jpg")
    cls = ' class="plan"' if plan else ""
    return ('          <figure%s>\n            <a class="zoomable" href="img/%s"><img%s src="img/%s" alt="%s" loading="lazy" /></a>\n'
            '            <figcaption>%s</figcaption>\n          </figure>\n') % (' class="wide"' if wide else "", big, cls, src, alt, cap)


def block(lang):
    t = L[lang]
    o = ['      <div class="lang-block" data-lang="%s">\n' % lang]
    o.append('        <p class="manual-intro">%s</p>\n' % t["intro"])
    o.append('        <nav class="model-nav" aria-label="%s">\n' % t["toc_kicker"])
    for k in NAMES:
        o.append('          <a href="#%s-%s"><img src="img/%s_iso-sm.jpg" alt="" loading="lazy" /><span class="nav-name">%s</span><span class="nav-desc">%s</span></a>\n'
                 % (lang, k, k, NAMES[k], t["m"][k]["desc"]))
    o.append('        </nav>\n')
    o.append('        <p class="manual-intro">%s</p>\n' % t["fig_all"])
    # shared design
    o.append('        <section class="manual" id="%s-shared">\n          <p class="manual-kicker">%s</p>\n          <h2>%s</h2>\n' % (lang, t["shared_kicker"], t["shared_h"]))
    for p in t["shared_p"]:
        o.append('          <p>%s</p>\n' % p)
    o.append(fig("etuttino_plan.svg", t["fig_plan"], t["fig_plan"], plan=True).replace('href="img/etuttino_plan.svg"', 'href="img/etuttino_plan.svg"'))
    o.append(fig("etuttino_left-sm.jpg", t["fig_left"], t["fig_left"]))
    o.append('        </section>\n')
    for k in NAMES:
        m = t["m"][k]
        keys, rng, size = SPEC[k]
        o.append('        <section class="manual" id="%s-%s">\n          <p class="manual-kicker">%s</p>\n          <h2>%s</h2>\n' % (lang, k, m["kicker"], NAMES[k]))
        o.append(fig("%s_iso-sm.jpg" % k, t["fig_iso"].format(name=NAMES[k]), t["fig_iso"].format(name=NAMES[k])))
        for p in m["p"]:
            o.append('          <p>%s</p>\n' % p)
        s = t["specs"]
        o.append('          <ul class="spec-list">\n')
        for label, value in ((s[0], keys), (s[1], rng[lang]), (s[2], size), (s[5], m["inside"])):
            o.append('            <li><span>%s</span><strong>%s</strong></li>\n' % (label, value))
        o.append('          </ul>\n')
        o.append('          <p>%s</p>\n' % t["spec_h"].format(grip="30,5" if lang != "en" else "30.5", deck="15,7" if lang != "en" else "15.7", keys="26,5" if lang != "en" else "26.5"))
        if k == "etutti_chorus":
            o.append(fig("%s_grip-sm.jpg" % k, t["fig_grip"], t["fig_grip"]))
            o.append(fig("%s_left-sm.jpg" % k, t["fig_left"], t["fig_left"]))
        o.append(fig("%s_plan.svg" % k, t["fig_plan"], t["fig_plan"], plan=True))
        o.append(fig("%s_top-sm.jpg" % k, t["fig_top"], t["fig_top"]))
        o.append('        </section>\n')
    # comparison
    o.append('        <section class="manual" id="%s-compare">\n          <h2>%s</h2>\n          <div class="table-wrap">\n            <table>\n' % (lang, t["cmp_h"]))
    o.append('              <thead><tr>%s</tr></thead>\n              <tbody>\n' % "".join("<th>%s</th>" % c for c in t["cmp_cols"]))
    for row in t["cmp_rows"]:
        o.append('                <tr><td>%s</td>%s</tr>\n' % (row[0], "".join("<td>%s</td>" % c for c in row[1:])))
    o.append('              </tbody>\n            </table>\n          </div>\n')
    o.append('          <div class="callout"><p>%s</p></div>\n        </section>\n' % t["note"])
    o.append('      </div>\n')
    return "".join(o)


HEAD = '''<!doctype html>
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
  <title data-i18n="meta.title">BeatConfused | eTutti models</title>
  <meta
    name="description"
    content="Concept layouts of the eTutti family: the compact eTuttino, the three-octave eTutti and the stand-alone eTuttiChorus with battery, speaker and screen."
    data-i18n-attr="content:meta.description"
  />
  <!-- Part of the unlisted eTutti work in progress: kept out of the sitemap
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
  <link rel="stylesheet" href="styles.css?v=20261012" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <link rel="stylesheet" href="/i18n/i18n.css?v=20261003" />
</head>
<body>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
    <header class="hero">
      <p class="eyebrow" data-i18n="hero.eyebrow">BeatConfused Studio</p>
      <h1 data-i18n="hero.title">eTutti models</h1>
    </header>
    <p class="manual-back"><a href="../" data-i18n="nav.back">← Back to eTutti</a></p>

'''

TAIL = '''  </main>

  <script>
    // The page text is written out once per language (.lang-block); these
    // strings only cover the page chrome.
    window.BC_STRINGS = {
      en: {
        "meta.title": "BeatConfused | eTutti models",
        "meta.description": "Concept layouts of the eTutti family: the compact eTuttino, the three-octave eTutti and the stand-alone eTuttiChorus with battery, speaker and screen.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "eTutti models",
        "nav.back": "← Back to eTutti",
      },
      pt: {
        "meta.title": "BeatConfused | Modelos do eTutti",
        "meta.description": "Layouts conceituais da família eTutti: o eTuttino compacto, o eTutti de três oitavas e o eTuttiChorus independente, com bateria, alto-falante e tela.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "Modelos do eTutti",
        "nav.back": "← Voltar ao eTutti",
      },
      es: {
        "meta.title": "BeatConfused | Modelos del eTutti",
        "meta.description": "Layouts conceptuales de la familia eTutti: el eTuttino compacto, el eTutti de tres octavas y el eTuttiChorus autónomo, con batería, altavoz y pantalla.",
        "hero.eyebrow": "BeatConfused Studio",
        "hero.title": "Modelos del eTutti",
        "nav.back": "← Volver al eTutti",
      },
    };
  </script>
  <script src="../manuais/lightbox.js?v=20261021"></script>
  <script src="/i18n/i18n.js?v=20261003"></script>
</body>
</html>
'''

html = HEAD + "".join(block(l) for l in ("en", "pt", "es")) + TAIL
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)
print("ok", len(html))
