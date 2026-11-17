"""eTutti Student V2: writes the presentation page, beatconfused.com/etutti/studentV2/.

    python etutti/hardware/student_v02/pagina.py

Plain Python. Writes etutti/studentV2/index.html and styles.css (the pictures in etutti/studentV2/img/
come from case/passos.py). The texts and the price table live here: edit them here, not in the HTML.

Money: every price is a range (low, high). "visto" = a shop page seen on 15 Nov 2026 (the Student V01
sourcing, student_v01/fornecimento/FORNECIMENTO.md and LISTA_DE_COMPRAS.md); "estimativa" = not quoted,
an order of magnitude to be replaced by a quote. Pounds are turned into dollars at RATE (an assumption,
not a quote). Shipping, VAT and customs are left out.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "studentV2"))
IMG = os.path.join(OUT, "img")
RATE = 1.30          # US$ per GBP
SIZES = json.load(open(os.path.join(IMG, "tamanhos.json")))
PINS = json.load(open(os.path.join(IMG, "ancoras.json")))


def esc(s):
    return html.escape(s, quote=True)


def usd(v):
    return "US$ %s" % format(int(v + 0.5), ",").replace(",", ".")


def usd2(v):
    return "US$ %s" % ("%.2f" % v).replace(".", ",")


def money(v):
    """Whole dollars from 100 up, cents below; whole numbers without the cents."""
    if v >= 100 or abs(v - round(v)) < 0.005:
        return usd(v)
    return usd2(v)


def rng(lo, hi, f=money):
    a, b = f(lo), f(hi)
    return a if a == b else "%s a %s" % (a, b.replace("US$ ", ""))


# ------------------------------------------------------------------ the shopping list, by order (supplier)
# (order, supplier, [(area, item, qty, what/code, low, high, currency, tag)])
BUY = [
    ("JLCPCB · placa montada", "JLCPCB (peças da LCSC)", [
        ("Eletrônica", "Placa principal, 4 camadas, 246,5 × 95 × 1,2 mm, ENIG: 5 unidades", "5", "Gerbers em fab/student_v02_gerbers.zip", 34, 34, "USD", "estimativa"),
        ("Eletrônica", "Preparação da montagem nos dois lados e estênceis", "1", "BOM e CPL em fab/", 68, 68, "USD", "estimativa"),
        ("Eletrônica", "Taxa por tipo de peça estendida (cerca de 22 tipos)", "22", "a JLCPCB cobra por tipo", 40, 70, "USD", "estimativa"),
        ("Eletrônica", "Peças das 2 placas montadas (140 peças cada, 35 linhas de BOM)", "2", "sensores, codec, carregador, amplificador, encoders, conectores", 68, 75, "USD", "visto"),
        ("Eletrônica", "Solda à mão dos 2 encoders e das juntas de furo passante", "2", "feita pela JLCPCB", 8, 10, "USD", "estimativa"),
    ]),
    ("JLCPCB · grade do teclado", "JLCPCB", [
        ("Teclado", "Grade FR-4 de 1,6 mm, 2 camadas, máscara preta fosca: 5 unidades (1 usada)", "5", "fab/student_v02_grade_gerbers.zip", 10, 20, "USD", "estimativa"),
    ]),
    ("Gateron", "Loja da Gateron (ou Chosfox, Ukeebs)", [
        ("Teclado", "Teclas Gateron KS-20 Magnetic Orange (38 gf), pacote de 35", "28 (de 35)", "sensor Hall sob cada tecla", 24.5, 26.6, "USD", "visto"),
    ]),
    ("SparkFun · módulo", "DigiKey UK ou SparkFun", [
        ("Eletrônica", "Módulo MicroMod Teensy (DEV-16402)", "1", "£ 18,69 sem IVA na DigiKey UK; US$ 24,95 na SparkFun. Inclui o parafuso M2,5 × 3.", 18.69 * RATE, 22.43 * RATE, "USD", "visto"),
    ]),
    ("eBay / Amazon · energia", "eBay, Amazon", [
        ("Energia", "Bateria LiPo 503450, 3,7 V, ~1000 mAh, 3 fios (NTC), plugue JST PH 2,0", "1", "medir o NTC (~10 kΩ) e a ordem dos fios antes de ligar", 5 * RATE, 8 * RATE, "USD", "visto"),
    ]),
    ("Eletrônica de bancada", "Pimoroni, Adafruit, SparkFun, Mouser, Amazon, eBay ou AliExpress", [
        ("Interface", "Módulo OLED 0,96″ 128 × 64, SSD1306, I²C, 4 pinos, 3,3 V", "1", "conferir placa de ~27,3 × 27,8 mm, furos e ordem dos pinos", 3 * RATE, 6 * RATE, "USD", "estimativa"),
        ("Interface", "Cabo JST SH 1,0 mm de 4 vias, 50 a 100 mm (Qwiic / STEMMA QT)", "1", "uma ponta no J401, a outra soldada na tela", 2 * RATE, 4 * RATE, "USD", "estimativa"),
        ("Som", "Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W", "1", "pedir a frequência de ressonância; quanto mais baixa, melhor", 2 * RATE, 5 * RATE, "USD", "estimativa"),
        ("Som", "Tela acústica 0,3 mm (36 × 28 mm), junta de espuma de 1 mm Ø 28/24, silicone", "1 kit", "veda a frente e o furo dos fios da caixa", 4 * RATE, 8 * RATE, "USD", "estimativa"),
        ("Energia", "Cabo USB-C", "1", "carga, MIDI e configuração", 0, 5 * RATE, "USD", "estimativa"),
    ]),
    ("Ferragem e acabamento", "ferragem, loja de modelismo ou de tintas", [
        ("Fixação", "Parafusos M2: 10 × 16 mm com porca, 6 × 14 mm (autoatarraxante), 2 × 5 mm, 4 × 4 mm", "22 + 10 porcas", "cabeça panela", 5 * RATE, 8 * RATE, "USD", "estimativa"),
        ("Acabamento", "Tinta para os rebaixos e para as faixas (vermelho, laranja, amarelo, preto, marrom-avermelhado) ou vinil adesivo", "1 kit", "cores: ver a seção do conceito", 5 * RATE, 10 * RATE, "USD", "estimativa"),
        ("Interface", "Acrílico fumê escuro de 1 mm, 25,7 × 14,7 mm, cantos R 1", "1", "corte a laser sob encomenda, ou lixado de uma chapa", 3 * RATE, 8 * RATE, "USD", "estimativa"),
    ]),
    ("Impressão 3D", "JLC3DP, PCBWay ou Craftcloud (resina ou nylon MJF)", [
        ("Case", "Tampa (creme) e base (cinza)", "1 + 1", "119 cm³ de material", 0, 0, "USD", "estimativa"),
        ("Teclado", "Botões: 12 branco, 11 preto, 5 branco com pontos (4 alturas de haste)", "28", "resina ou MJF: o encaixe em cruz não sai em filamento", 0, 0, "USD", "estimativa"),
        ("Teclado", "Espaçadores da grade Ø 5 × 11,35 mm", "10", "", 0, 0, "USD", "estimativa"),
        ("Interface", "Knobs chapéu com luva e furo em D", "2", "preto, traço pintado", 0, 0, "USD", "estimativa"),
        ("Som", "Caixa acústica em L (10,4 cm³), na mesma peça do anel", "1", "paredes cheias: tem de ser estanque", 0, 0, "USD", "estimativa"),
    ]),
]
PRINT_COST = (45 * RATE, 110 * RATE)       # the whole print order, GBP 45-110 in dollars (estimate by volume)
OPTIONAL = [("Molas longas de 65 g e de 80 g, 1 pacote de cada (para o peso de uma tecla de acordeão)", 6 * RATE, 12 * RATE, "estimativa")]


def supplier_totals():
    rows = []
    for name, who, items in BUY:
        lo = sum(i[4] for i in items)
        hi = sum(i[5] for i in items)
        if name == "Impressão 3D":
            lo, hi = PRINT_COST
        rows.append((name, who, lo, hi, items))
    return rows


# ------------------------------------------------------------------ parts by area (the bill of materials of the instrument)
AREAS = [
    ("Eletrônica", "A placa vem pronta da JLCPCB; o módulo do processador é encaixado em casa.", [
        ("Placa principal, montada", "1", "JLCPCB", "4 camadas, 1,2 mm, ENIG; 140 peças soldadas por máquina; 28 sensores Hall no verso, sob as teclas"),
        ("Módulo MicroMod Teensy (DEV-16402)", "1", "SparkFun / DigiKey", "i.MX RT1062, 16 MB; encaixa no conector M.2 do verso, com 1 parafuso M2,5 × 3"),
        ("Sensor Hall TMAG5253 (C22401868)", "28", "JLCPCB (LCSC)", "um sob cada tecla, no verso"),
        ("Codec de áudio SGTL5000 (C2651833)", "1", "JLCPCB (LCSC)", "fone, entrada de microfone com bias, saída para o amplificador"),
        ("Amplificador MAX98357A (C910544), carregador BQ24074 (C54313), conversor TPS63001 (C28060)", "3", "JLCPCB (LCSC)", "som do alto-falante, carga da bateria, 3,3 V"),
        ("Multiplexadores 74HC4067 (C179326)", "2", "JLCPCB (LCSC)", "leem as 28 teclas por 2 canais"),
        ("Encoders com clique EC11E18244AU (C202365)", "2", "JLCPCB (LCSC)", "eixo de 20 mm: volume e registro; soldados à mão pela JLCPCB"),
        ("Conectores: USB-C, 2 jacks 3,5 mm (OUT e IN), JST SH da tela, JST PH da bateria", "5", "JLCPCB (LCSC)", "USB-C TYPE-C-31-M-12, jacks PJ-327A, SM04B-SRSS-TB, S3B-PH-SM4-TB"),
    ]),
    ("Teclado", "28 teclas G3 a E5 em fileiras de 7, 8, 7 e 6, a 18,5 mm; fileiras 2 mm, 2 mm e 3 mm mais altas.", [
        ("Teclas Gateron KS-20 Magnetic Orange", "28", "Gateron", "curso de 4,1 mm; apoiadas na placa, seguras pela grade"),
        ("Grade FR-4 de 1,6 mm, máscara preta fosca", "1", "JLCPCB", "28 furos de Ø 6,2 mm; fica a 0,15 mm acima das teclas; só acabamento"),
        ("Espaçadores Ø 5 × 11,35 mm", "10", "impressão", "entre a placa e a grade, na borda"),
        ("Parafusos M2 × 16 e porcas M2", "10 + 10", "ferragem", "por cima, atravessam grade, espaçador e placa; a porca fica sob a placa"),
        ("Botões Ø 15 mm: branco, preto, branco com pontos (C e F)", "28", "impressão", "4 alturas de haste; a altura acima do tampo é de 3,7 / 5,7 / 7,7 / 10,7 mm"),
        ("Molas longas de 65 g ou 80 g (opcional)", "28", "loja de teclados", "mudam o peso da tecla; não alteram placa nem firmware"),
    ]),
    ("Interface", "Tela, dois knobs, grade do alto-falante e legendas, à esquerda do teclado.", [
        ("Módulo OLED 0,96″ 128 × 64 (I²C)", "1", "loja de eletrônica", "preso por baixo da tampa em 4 postes (M2 × 4)"),
        ("Cabo JST SH de 4 vias", "1", "loja de eletrônica", "liga a tela ao J401"),
        ("Janela de acrílico fumê de 1 mm", "1", "corte a laser", "24 × 13 mm de vidro à vista"),
        ("Knobs chapéu", "2", "impressão", "Ø 12 mm, 7 mm de altura; luva escondida sobre o eixo"),
    ]),
    ("Som", "Alto-falante de 28 mm sob 7 fendas, com caixa acústica fechada em L de 10,4 cm³.", [
        ("Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W", "1", "loja de eletrônica", "fios soldados ao J501"),
        ("Caixa acústica em L, com o anel de fixação", "1", "impressão", "estanque; 2 parafusos M2 × 5 nas buchas da tampa"),
        ("Tela acústica 0,3 mm e junta de espuma de 1 mm", "1 + 1", "loja de eletrônica", "entre as fendas e o alto-falante"),
    ]),
    ("Energia", "Bateria no piso da base; troca tirando os 6 parafusos de baixo.", [
        ("Bateria LiPo 503450, ~1000 mAh, 3 fios", "1", "eBay / Amazon", "o terceiro fio é o NTC de 10 kΩ"),
        ("Cabo USB-C", "1", "—", "carga, MIDI e configuração pela página"),
    ]),
    ("Case e acabamento", "252 × 100 × 28,3 mm, tampa creme e base cinza (acabamento Retrô).", [
        ("Tampa, com o logo e as legendas em rebaixo de 0,4 mm", "1", "impressão", "chanfro de 30°, três sulcos, aba que forma o poço do teclado"),
        ("Base", "1", "impressão", "berço da bateria, pinos e pilares de apoio sob a placa"),
        ("Parafusos M2 × 14 da tampa", "6", "ferragem", "por baixo, atravessam base e placa e entram nos postes da tampa"),
        ("Tinta e faixas", "1 kit", "tintas / vinil", "faixas #C8402A, #E07A2C, #E3B23C; tinta #2B2925 e #8A3A22"),
    ]),
]

EXPLODED = [
    ("Base", "cinza, impressa"), ("Bateria LiPo 503450", "no berço da base"), ("Placa principal", "montada pela JLCPCB"),
    ("Módulo MicroMod Teensy", "sob a placa, no conector M.2"), ("Teclas Gateron × 28", "apoiadas na placa"),
    ("Espaçadores × 10 e parafusos M2 × 16", "fixam a grade pela borda"), ("Grade FR-4 de 1,6 mm", "máscara preta fosca"),
    ("Tampa", "creme, impressa"), ("Janela de acrílico fumê", "24 × 13 mm"), ("Tela OLED 0,96″", "presa por baixo da tampa"),
    ("Alto-falante e caixa acústica", "em L, 10,4 cm³"), ("Botões × 28", "entram por cima, pela grade"), ("Knobs × 2", "sobre os eixos dos encoders"),
]

STEPS = [
    ("passo_1", "Placa e módulo", [
        "Confira a placa recebida da JLCPCB: os conectores sobre os pads, o pino 1 dos chips e dos 28 sensores.",
        "Encaixe o módulo MicroMod Teensy no conector M.2 do verso e prenda-o com o parafuso M2,5 × 3 no espaçador.",
    ], "Placa, módulo, encoders, jacks e USB-C"),
    ("passo_2", "Teclas", [
        "Pressione as 28 teclas Gateron nos seus lugares: dois pinos de plástico por tecla a posicionam, e não há solda (o sensor Hall está no verso da placa).",
        "Se for trocar as molas, faça-o agora, uma tecla de teste primeiro.",
    ], "28 teclas Gateron KS-20"),
    ("passo_3", "Grade", [
        "Ponha os 10 espaçadores sobre os furos da borda, a grade FR-4 por cima e os parafusos M2 × 16 por cima de tudo; as porcas M2 ficam por baixo da placa.",
        "A grade fica 0,15 mm acima das teclas e é o que as segura. Os parafusos ficam escondidos sob a tampa.",
    ], "10 espaçadores, grade FR-4, 10 parafusos e porcas"),
    ("passo_4", "A tampa, por dentro", [
        "Com a tampa de cabeça para baixo: ponha o acrílico fumê na janela, prenda a tela nos 4 postes (M2 × 4) e ligue o cabo JST SH.",
        "Ponha a tela acústica, a junta de espuma e o alto-falante sob as fendas; prenda a caixa acústica com 2 parafusos M2 × 5. Passe os fios do alto-falante pelo furo da caixa e vede-o com uma gota de silicone.",
    ], "Janela, tela, alto-falante e caixa acústica"),
    ("passo_5", "Fechar a tampa sobre a placa", [
        "Antes de fechar, ligue o cabo da tela ao J401 e solde os fios do alto-falante ao J501, deixando uns 40 mm de folga.",
        "Desça a tampa na vertical sobre a placa: os conectores ficam 0,3 mm atrás da parede, e os eixos dos encoders sobem pelos furos dos knobs.",
    ], "Tampa com tudo o que leva dentro"),
    ("passo_6", "Bateria e base", [
        "Antes: meça o terceiro fio da bateria (cerca de 10 kΩ até o negativo) e confira a ordem dos fios contra o J202 (1 positivo, 2 NTC, 3 negativo). Positivo e negativo invertidos danificam a placa.",
        "Ponha a bateria no berço da base, encaixe o plugue no J202 e feche a base por baixo com 6 parafusos M2 × 14, que atravessam base e placa e entram nos postes da tampa.",
    ], "Base, bateria e 6 parafusos"),
    ("passo_7", "Botões e knobs", [
        "Por cima, pressione cada botão pelo furo da grade até a cruz da tecla, na altura da sua fileira (haste de 7,2 / 9,2 / 11,2 / 14,2 mm, da fileira 1, a da frente, à 4).",
        "Encaixe os dois knobs nos eixos dos encoders, com o furo em D virado para o chato do eixo.",
    ], "28 botões e 2 knobs"),
]

CSS = """\
:root {
  --paper: #F3F1EC;
  --card: #FBFAF6;
  --ink: #2B2925;
  --muted: #5C574F;
  --line: #D8D2C4;
  --red: #C8402A;
  --orange: #E07A2C;
  --yellow: #E3B23C;
  --brown: #8A3A22;
  color-scheme: light;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 4.2rem; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 400 1rem/1.6 "Inter", system-ui, sans-serif;
}
.page { max-width: 68rem; margin: 0 auto; padding: 0 1rem 4rem; }
a { color: var(--brown); }
a:hover { color: #5E2716; }
.stripes { height: 14px; background: linear-gradient(90deg, var(--red) 0 33%, var(--orange) 33% 66%, var(--yellow) 66%); }
.hero { padding: 1.6rem 0 1rem; text-align: center; }
.hero .eyebrow { margin: 0; font: 500 0.8rem/1.2 "Inter", sans-serif; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted); }
.hero h1 {
  margin: 0.4rem 0 0.2rem;
  font: 400 clamp(2rem, 6vw, 3.4rem)/1.1 "Michroma", "Space Grotesk", sans-serif;
  letter-spacing: 0.04em;
}
.hero h1 small { display: block; margin-top: 0.4rem; font-size: 0.38em; letter-spacing: 0.3em; color: var(--brown); }
.hero p.lead { max-width: 44rem; margin: 1rem auto 0; font-size: 1.15rem; color: #45413A; }
.hero img { width: 100%; height: auto; margin-top: 1rem; }
nav.toc {
  position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; gap: 0.2rem 0.4rem; justify-content: center;
  margin: 0 -1rem; padding: 0.5rem 1rem; background: rgba(243, 241, 236, 0.94); backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--line);
}
nav.toc a { padding: 0.25rem 0.7rem; border-radius: 999px; font: 500 0.85rem/1.4 "Inter", sans-serif; text-decoration: none; color: var(--ink); }
nav.toc a:hover { background: #E8DEC6; }
section { margin-top: 3rem; }
section h2 { margin: 0 0 0.3rem; font: 700 clamp(1.5rem, 4vw, 2rem)/1.2 "Space Grotesk", "Inter", sans-serif; }
section h2 + p.sub { margin: 0 0 1.2rem; color: var(--muted); }
section h3 { margin: 1.8rem 0 0.4rem; font: 700 1.15rem/1.3 "Space Grotesk", "Inter", sans-serif; }
.kicker { margin: 0; font: 600 0.75rem/1.2 "Inter", sans-serif; letter-spacing: 0.16em; text-transform: uppercase; color: var(--brown); }
figure { margin: 1rem 0; }
figure img { display: block; width: 100%; height: auto; background: var(--paper); border-radius: 6px; }
figcaption { margin-top: 0.4rem; font-size: 0.88rem; color: var(--muted); }
.grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr)); }
.card { padding: 1rem 1.1rem; background: var(--card); border: 1px solid var(--line); border-radius: 10px; }
.card h3 { margin-top: 0; }
.card p { margin: 0.3rem 0 0; }
.facts { display: grid; gap: 0.8rem; grid-template-columns: repeat(auto-fit, minmax(min(10.5rem, 100%), 1fr)); margin: 1.2rem 0; padding: 0; list-style: none; }
.facts li { padding: 0.8rem 1rem; background: var(--card); border: 1px solid var(--line); border-top: 4px solid var(--orange); border-radius: 8px; }
.facts b { display: block; font: 700 1.45rem/1.2 "Space Grotesk", sans-serif; }
.facts span { font-size: 0.88rem; color: var(--muted); }
.status { padding: 1rem 1.2rem; background: #FFF6DF; border: 1px solid #E3C98A; border-radius: 10px; }
.status h3 { margin-top: 0; }
.status ul { margin: 0.3rem 0 0; padding-left: 1.2rem; }
.swatches { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0.8rem 0; padding: 0; list-style: none; }
.swatches li { display: flex; align-items: center; gap: 0.45rem; font-size: 0.88rem; }
.swatches i { display: inline-block; width: 1.4rem; height: 1.4rem; border-radius: 4px; border: 1px solid rgba(0,0,0,.2); }
/* exploded view */
.exploded { position: relative; }
.exploded .pin {
  position: absolute; transform: translate(-50%, -50%); width: 1.7rem; height: 1.7rem; border-radius: 50%;
  display: grid; place-items: center; background: var(--ink); color: #fff; font: 700 0.82rem/1 "Inter", sans-serif;
  border: 2px solid var(--paper); box-shadow: 0 1px 4px rgba(0,0,0,.35);
}
@media (max-width: 600px) { .exploded .pin { width: 1.2rem; height: 1.2rem; font-size: 0.66rem; border-width: 1px; } }
ol.legend { display: grid; gap: 0.35rem 1.4rem; grid-template-columns: repeat(auto-fit, minmax(min(20rem, 100%), 1fr)); margin: 1rem 0 0; padding: 0; list-style: none; counter-reset: n; }
ol.legend li { display: flex; gap: 0.6rem; align-items: baseline; }
ol.legend li::before {
  counter-increment: n; content: counter(n); flex: none; width: 1.5rem; height: 1.5rem; border-radius: 50%;
  display: grid; place-items: center; background: var(--ink); color: #fff; font: 700 0.78rem/1 "Inter", sans-serif;
}
ol.legend span { color: var(--muted); }
/* steps */
.step { display: grid; gap: 1rem 1.6rem; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); align-items: center; margin: 1.6rem 0; padding: 1rem; background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
.step figure { margin: 0; }
.step h3 { margin: 0 0 0.4rem; }
.step .num { display: inline-grid; place-items: center; width: 2rem; height: 2rem; margin-right: 0.5rem; border-radius: 50%; background: var(--red); color: #fff; font: 700 1rem/1 "Space Grotesk", sans-serif; }
.step p { margin: 0.4rem 0; }
.step .new { margin-top: 0.6rem; font-size: 0.88rem; color: var(--muted); }
@media (max-width: 760px) { .step { grid-template-columns: 1fr; } }
/* tables */
.tablewrap { overflow-x: auto; margin: 0.8rem 0; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }
table { width: 100%; border-collapse: collapse; font-size: 0.93rem; }
th, td { padding: 0.5rem 0.7rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }
th { background: #EDE6D4; font: 600 0.8rem/1.3 "Inter", sans-serif; letter-spacing: 0.04em; text-transform: uppercase; color: #45413A; white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
td.qty { white-space: nowrap; }
tr.sub td { background: #F7F2E4; font-weight: 600; }
tr.total td { background: #2B2925; color: #fff; font-weight: 700; border-bottom: 0; }
tr.total td.num { font-size: 1.1rem; }
.tag { display: inline-block; padding: 0 0.45rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; background: #E5EEDB; color: #3B5B26; }
.tag.est { background: #F6E7C8; color: #7A5410; }
.note { font-size: 0.88rem; color: var(--muted); }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: 0.88rem; color: var(--muted); }
@media print {
  nav.toc { display: none; }
  body { background: #fff; }
  section, .step, figure, tr { break-inside: avoid; }
}
"""


def imgtag(name, alt):
    w, h = SIZES[name]
    return '<a href="img/%s.jpg"><img src="img/%s.jpg" width="%d" height="%d" alt="%s" loading="lazy" /></a>' % (name, name, w, h, esc(alt))


def img(name, alt, caption=None, cls=""):
    cap = "<figcaption>%s</figcaption>" % caption if caption else ""
    return '<figure class="%s">%s%s</figure>' % (cls, imgtag(name, alt), cap)


def build():
    rows = supplier_totals()
    tot_lo = sum(r[2] for r in rows)
    tot_hi = sum(r[3] for r in rows)
    opt_lo = sum(o[1] for o in OPTIONAL)
    opt_hi = sum(o[2] for o in OPTIONAL)

    h = []
    A = h.append
    A('<!doctype html>\n<html lang="pt-BR">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />')
    A('''  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KCCMBL7GMJ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag("js", new Date());
    gtag("config", "G-KCCMBL7GMJ");
  </script>''')
    A('  <title>BeatConfused | eTutti Student V2</title>')
    A('  <meta name="description" content="eTutti Student V2: o conceito, as peças por área e fornecedor, a vista explodida, a sequência de montagem e o orçamento." />')
    A('  <!-- Written by etutti/hardware/student_v02/pagina.py: edit the texts and the prices there.\n       Part of the unlisted eTutti work in progress: kept out of the sitemap and of search results. -->')
    A('  <meta name="robots" content="noindex,nofollow" />\n  <meta name="theme-color" content="#F3F1EC" />')
    A('  <link rel="preconnect" href="https://fonts.googleapis.com" />\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />')
    A('  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Michroma&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />')
    A('  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />\n  <link rel="stylesheet" href="styles.css?v=20261117" />\n</head>\n<body>')
    A('  <div class="stripes" aria-hidden="true"></div>\n  <main class="page">')
    A('    <a class="site-title" href="/">beatconfused.com</a>')
    A('''    <header class="hero">
      <p class="eyebrow">BeatConfused Studio · protótipo</p>
      <h1>eTutti<small>STUDENT · V2</small></h1>
      <p class="lead">Um acordeão de teclado para estudar: 28 teclas magnéticas com velocity, tela, dois knobs, alto-falante, entrada de microfone, bateria e USB-C, numa caixa Retrô de 252 × 100 mm.</p>''')
    A("      " + img("isometrico", "O eTutti Student V2 em perspectiva: tampa creme com faixas vermelha, laranja e amarela, teclado de botões brancos e pretos, tela e dois knobs à esquerda."))
    A('    </header>')
    A('''    <nav class="toc" aria-label="Seções">
      <a href="#conceito">Conceito</a><a href="#pecas">Peças</a><a href="#explodida">Vista explodida</a>
      <a href="#montagem">Montagem</a><a href="#orcamento">Orçamento</a>
    </nav>''')

    # ---------------- concept
    A('    <section id="conceito">\n      <p class="kicker">1 · Conceito</p>\n      <h2>Um acordeão de estudo, do tamanho de uma prancheta</h2>')
    A('      <p class="sub">O Student V2 é a versão compacta do eTutti: o teclado de acordeão de botões (C-griff) com a sensibilidade de um instrumento de verdade, sem fole, em uma caixa que cabe numa mochila.</p>')
    A('''      <ul class="facts">
        <li><b>28 teclas</b><span>C-griff, de G3 a E5, em 4 fileiras a 18,5 mm</span></li>
        <li><b>Velocity</b><span>sensor Hall sob cada tecla Gateron, curso de 4,1 mm</span></li>
        <li><b>252 × 100 × 28,3 mm</b><span>tampa creme, base cinza, 3 sulcos e um chanfro de 30°</span></li>
        <li><b>Tela OLED 0,96″</b><span>registro, volume e carga, atrás de acrílico fumê</span></li>
        <li><b>2 knobs com clique</b><span>volume e registro</span></li>
        <li><b>Som próprio</b><span>alto-falante de 28 mm numa caixa fechada de 10,4 cm³</span></li>
        <li><b>Entradas e saídas</b><span>USB-C (carga e MIDI), OUT 3,5 mm e IN 3,5 mm (microfone)</span></li>
        <li><b>Bateria LiPo</b><span>1 célula, cerca de 1000 mAh, trocada tirando 6 parafusos</span></li>
      </ul>''')
    A('      <div class="grid">')
    A('<div class="card"><h3>O teclado</h3><p>As fileiras sobem 2, 2 e 3 mm uma sobre a outra (topos a 3,7, 5,7, 7,7 e 10,7 mm do tampo), de modo que o dedo sente cada fileira. Os botões têm Ø 15 mm e cúpula convexa, em três tipos: branco, preto e branco com pontos (o C e o F, para achar a posição no escuro).</p></div>')
    A('<div class="card"><h3>A grade</h3><p>Uma placa de FR-4 de 1,6 mm, preta fosca, cobre as teclas a 0,15 mm e as segura sem plate nem parafusos à vista: ela é fixada só pela borda, sob a tampa. O poço do teclado tem 5,25 mm de profundidade.</p></div>')
    A('<div class="card"><h3>A placa</h3><p>A mesma eletrônica da Student V1, com a interface refeita: sem LED, com tela por I²C, entrada de microfone e dois encoders de eixo curto. Sem parafusos na área do teclado: 4 pinos e 3 pilares da base sustentam a placa, e a pior tecla cede 0,049 mm sob 3 N.</p></div>')
    A('<div class="card"><h3>O acabamento Retrô</h3><p>Faixas vermelha, laranja e amarela que dão a volta pelo tampo, pelo chanfro e pela parede, e o logo em Michroma em rebaixo de 0,4 mm com tinta.</p>')
    A('<ul class="swatches"><li><i style="background:#E8DEC6"></i>tampa #E8DEC6</li><li><i style="background:#9C9B96"></i>base #9C9B96</li><li><i style="background:#C8402A"></i>#C8402A</li><li><i style="background:#E07A2C"></i>#E07A2C</li><li><i style="background:#E3B23C"></i>#E3B23C</li><li><i style="background:#2B2925"></i>tinta #2B2925</li><li><i style="background:#8A3A22"></i>tinta #8A3A22</li></ul></div>')
    A('      </div>')
    A("      " + img("planta", "O instrumento visto de cima: a coluna da esquerda com tela, dois knobs e a grade do alto-falante, e o teclado de 28 botões."
                      , "Planta. Da esquerda para a direita: logo, tela, knobs, grade do alto-falante, e o teclado."))
    A('      <div class="grid">')
    A("      " + img("parede", "A parede esquerda com o furo do USB-C e os dois furos dos jacks.", "Parede esquerda: USB-C, OUT e IN em furos fechados, sem emendas."))
    A("      " + img("logo", "Detalhe do logo eTUTTI e STUDENT V2 e da tela.", "O logo: “eTUTTI” em rebaixo, “STUDENT · V2” pintado."))
    A("      " + img("corte", "Corte pelas fileiras do teclado.", "Corte pelas fileiras: a grade, as teclas, a placa e a base."))
    A("      " + img("corte_falante", "Corte pelo alto-falante e pela caixa acústica.", "Corte pelo alto-falante: fendas, alto-falante, caixa acústica e bateria."))
    A('      </div>')
    A('''      <div class="status">
        <h3>Estado do projeto</h3>
        <ul>
          <li><b>Pronto:</b> esquema, placa (verificação de regras limpa, igual ao esquema), BOM e posições de montagem, grade FR-4, case em 20 peças sem nenhuma interferência em 202 pares, estudos de flexão e de acústica, renders.</li>
          <li><b>Pendente:</b> o firmware da V2 (tela, microfone, sem LED), conferir de novo a prévia de montagem da JLCPCB, escolher o alto-falante e refazer o estudo com os números dele, e cotar a impressão.</li>
          <li><b>Nada foi encomendado, impresso ou montado.</b> Os preços abaixo são de pesquisa: confira todos na hora do pedido.</li>
        </ul>
      </div>
    </section>''')

    # ---------------- parts by area
    A('    <section id="pecas">\n      <p class="kicker">2 · Peças</p>\n      <h2>O que leva, por área e por fornecedor</h2>')
    A('      <p class="sub">Seis áreas. A coluna “Fornecedor” diz onde cada peça se compra; o orçamento, na seção 5, está agrupado por pedido.</p>')
    for area, blurb, items in AREAS:
        A('      <h3>%s</h3><p class="note">%s</p>' % (esc(area), esc(blurb)))
        A('      <div class="tablewrap"><table><thead><tr><th>Peça</th><th>Qtd</th><th>Fornecedor</th><th>Observação</th></tr></thead><tbody>')
        for name, qty, who, obs in items:
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td>%s</td></tr>' % (esc(name), esc(qty), esc(who), esc(obs)))
        A('</tbody></table></div>')
    A('      <h3>Os mesmos itens, por fornecedor</h3>')
    A('      <div class="tablewrap"><table><thead><tr><th>Fornecedor</th><th>Fornece</th></tr></thead><tbody>')
    byw = [
        ("JLCPCB / LCSC", "placa principal montada (140 peças), grade FR-4"),
        ("Gateron", "28 teclas KS-20 Magnetic Orange (pacote de 35)"),
        ("SparkFun ou DigiKey", "módulo MicroMod Teensy"),
        ("eBay ou Amazon", "bateria LiPo 503450 de 3 fios"),
        ("Loja de eletrônica", "tela OLED, cabo JST SH, alto-falante, tela acústica, espuma, silicone, cabo USB-C"),
        ("Ferragem e tintas", "parafusos e porcas M2, tinta, vinil"),
        ("Impressão 3D (JLC3DP, PCBWay, Craftcloud)", "tampa, base, 28 botões, 10 espaçadores, 2 knobs, caixa acústica"),
        ("Corte a laser", "janela de acrílico fumê"),
    ]
    for a, b in byw:
        A("<tr><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b)))
    A('</tbody></table></div>\n    </section>')

    # ---------------- exploded
    A('    <section id="explodida">\n      <p class="kicker">3 · Vista explodida</p>\n      <h2>Da base aos botões</h2>')
    A('      <p class="sub">As peças em ordem de baixo para cima, como se montam.</p>')
    w, hh = SIZES["explodido"]
    A('      <div class="exploded"><a href="img/explodido.jpg"><img src="img/explodido.jpg" width="%d" height="%d" alt="Vista explodida do instrumento, com as 13 peças numeradas." loading="lazy" style="width:100%%;height:auto;display:block;border-radius:6px" /></a>' % (w, hh))
    for k, (x, y) in PINS.items():
        A('<span class="pin" style="left:%.2f%%;top:%.2f%%" aria-hidden="true">%s</span>' % (x, y, k))
    A('</div>')
    A('      <ol class="legend">')
    for n, s in EXPLODED:
        A('<li><div>%s<br /><span>%s</span></div></li>' % (esc(n), esc(s)))
    A('      </ol>\n    </section>')

    # ---------------- assembly
    A('    <section id="montagem">\n      <p class="kicker">4 · Montagem</p>\n      <h2>Sete passos, sem solda além de dois fios</h2>')
    A('      <p class="sub">Em cada figura, o que é novo no passo está em cor e o que já estava montado, esmaecido. Ferramentas: chave Phillips pequena, alicate de bico fino, ferro de solda (só para os dois fios do alto-falante), multímetro.</p>')
    A('      <h3>Antes de começar</h3>')
    A('      <ul><li>Placa principal e grade FR-4 vêm da JLCPCB; módulo MicroMod, teclas e bateria chegam à parte.</li><li>Case, botões, knobs, espaçadores e caixa acústica são impressos; os botões e os knobs pedem resina ou MJF.</li><li>Pinte o logo e as legendas, e as faixas, antes de montar.</li></ul>')
    for i, (fig, title, texts, new) in enumerate(STEPS, 1):
        A('      <article class="step"><figure>%s</figure><div><h3><span class="num">%d</span>%s</h3>%s<p class="new">Novo neste passo: %s.</p></div></article>'
          % (imgtag(fig, "Passo %d: %s" % (i, title)), i, esc(title),
             "".join("<p>%s</p>" % esc(t) for t in texts), esc(new)))
    A('      <h3>Primeira ligação</h3>')
    A('      <p>Com o USB ligado a tela deve acender com a carga. O firmware da Student V2 ainda não existe: as teclas, o som e o microfone só poderão ser testados depois dele. O projeto completo, com os relatórios de eletrônica, de ajustes e de compras, está em <code>etutti/hardware/student_v02/</code>.</p>')
    A('    </section>')

    # ---------------- budget
    A('    <section id="orcamento">\n      <p class="kicker">5 · Orçamento</p>\n      <h2>Quanto custa um instrumento</h2>')
    A('      <p class="sub">Um instrumento completo, pedindo o mínimo à JLCPCB (5 placas, 2 montadas). Os valores são faixas, em dólares; libras convertidas a £ 1 = US$ %s (uma suposição, não uma cotação). Fora: frete, IVA e impostos de importação.</p>' % ("%.2f" % RATE).replace(".", ","))
    A('      <div class="tablewrap"><table><thead><tr><th>Pedido</th><th>Fornecedor</th><th class="num">Valor</th></tr></thead><tbody>')
    for name, who, lo, hi, _items in rows:
        A('<tr><td>%s</td><td>%s</td><td class="num">%s</td></tr>' % (esc(name), esc(who), esc(rng(lo, hi))))
    A('<tr class="total"><td colspan="2">Total do primeiro instrumento</td><td class="num">%s</td></tr>' % esc(rng(tot_lo, tot_hi)))
    A('</tbody></table></div>')
    A('      <p class="note">Opcional, fora do total: molas de 65 g e de 80 g para o peso da tecla, %s.</p>' % esc(rng(opt_lo, opt_hi)))
    A('      <h3>Detalhe por pedido</h3>')
    for name, who, lo, hi, items in rows:
        A('      <div class="tablewrap"><table><thead><tr><th colspan="5">%s · %s</th></tr><tr><th>Item</th><th>Qtd</th><th>Observação</th><th>Fonte do preço</th><th class="num">Valor</th></tr></thead><tbody>' % (esc(name), esc(who)))
        for area, item, qty, obs, ilo, ihi, _cur, tag in items:
            if name == "Impressão 3D":
                val = "—"
            else:
                val = rng(ilo, ihi)
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td><span class="tag%s">%s</span></td><td class="num">%s</td></tr>'
              % (esc(item), esc(qty), esc(obs), "" if tag == "visto" else " est", "preço visto" if tag == "visto" else "estimativa", esc(val)))
        if name == "Impressão 3D":
            A('<tr class="sub"><td colspan="4">Pedido de impressão inteiro (tampa, base, 28 botões, espaçadores, 2 knobs e a caixa acústica: cerca de 146 cm³ de material). Estimativa pelo volume; cotar em duas lojas com os STEP de <code>case/out/</code>.</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
        else:
            A('<tr class="sub"><td colspan="4">Subtotal</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
        A('</tbody></table></div>')
    A('      <h3>Como ler estes números</h3>')
    A('''      <ul>
        <li><b>Preço visto</b> é o de uma página de loja de 15 de novembro de 2026; <b>estimativa</b> é uma ordem de grandeza ainda sem cotação.</li>
        <li>Os preços da JLCPCB vêm da estimativa da Student V1 (a cotação real só sai com os arquivos enviados) e das peças da LCSC; <b>a JLCPCB cobra a maior parte do pedido em taxas fixas</b>: montar as 5 placas custaria só um pouco mais que montar 2. Com as 5 montadas, o pedido à JLCPCB (placas e grades) passaria a cerca de US$ 335 a 370 (estimativa da Student V1).</li>
        <li>Sobram do primeiro pedido 1 placa montada (reserva), 3 placas nuas, 4 grades, 7 teclas e o que sobrar dos pacotes de ferragem: o segundo instrumento custa muito menos.</li>
        <li>O alto-falante ainda não foi escolhido: o estudo acústico usa um alto-falante nominal, e a caixa foi desenhada para um de Ø 28 × 5 mm.</li>
      </ul>''')
    A('    </section>')
    A('''    <footer>
      <p>Projeto em desenvolvimento, fora do mapa do site e dos buscadores. Arquivos de projeto em <code>etutti/hardware/student_v02/</code> do repositório <a href="https://github.com/dataehora/beatconfused">dataehora/beatconfused</a>.</p>
      <p><a href="/">beatconfused.com</a> · <a href="mailto:beatconfused@beatconfused.com">beatconfused@beatconfused.com</a></p>
    </footer>
  </main>
</body>
</html>''')
    return "\n".join(h), (tot_lo, tot_hi), [(r[0], r[2], r[3]) for r in rows]


def main():
    os.makedirs(OUT, exist_ok=True)
    page, tot, rows = build()
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
    open(os.path.join(OUT, "styles.css"), "w", encoding="utf-8", newline="\n").write(CSS)
    print("total", [round(v) for v in tot])
    for r in rows:
        print("  %-30s %6.0f %6.0f" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
