"""eTutti Student V3: writes the presentation page and the assembly manual.

    python etutti/hardware/student_v03/pagina.py

Plain Python (+ Pillow for the two board pictures). Writes
  etutti/studentV3/index.html     the concept, the electronics (block diagram, schematic sheets), the parts, the sourcing, the budget
  etutti/studentV3/montagem.html  the assembly manual: before you start, tools, ten steps with exploded views, first power-up, measurements
  etutti/studentV3/styles.css
The pictures (etutti/studentV3/img/) come from case/passos.py (CadQuery venv) and the KiCad exports; the schematic sheets
(etutti/studentV3/esquema/*.svg) from `kicad-cli sch export svg`. The texts and the price tables live here: edit them here, not in the HTML.

Money: every price is a range (low, high). "visto" = a shop page seen on 15 Nov 2026 (the Student V01 sourcing); "estimativa" = not
quoted, an order of magnitude to be replaced by a quote. Pounds become dollars at RATE (an assumption, not a quote). JLCPCB lines come
from the quote of 18 Nov 2026 (student_v03/README.md) and are derived: the quote itself needs the uploaded files. Shipping, VAT
and customs are left out.
"""
import csv
import html
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ETUTTI = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ETUTTI, "studentV3")
IMG = os.path.join(OUT, "img")
RATE = 1.30          # US$ per GBP
SIZES = json.load(open(os.path.join(IMG, "tamanhos.json")))
PINS = json.load(open(os.path.join(IMG, "ancoras.json")))

# the V2 page's helpers and style sheet (same family look); loaded by path, it only reads its own folder's pictures
_spec = importlib.util.spec_from_file_location("pagina_v2", os.path.join(HERE, "..", "student_v02", "pagina.py"))
V2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V2)
esc, money, rng = V2.esc, V2.money, V2.rng


def bom_numbers():
    rows = list(csv.DictReader(open(os.path.join(HERE, "fab", "student_v03_bom.csv"), encoding="utf-8")))
    parts = sum(len(r["Designator"].split(",")) for r in rows)
    cpl = list(csv.DictReader(open(os.path.join(HERE, "fab", "student_v03_cpl.csv"), encoding="utf-8")))
    ext = [r for r in csv.DictReader(open(os.path.join(HERE, "bom_v3.csv"), encoding="utf-8")) if r["classe"] == "Extended"]
    return len(rows), parts, len(cpl), len(ext)


BOM_LINES, BOM_PARTS, CPL_ROWS, EXT_TYPES = bom_numbers()

# ------------------------------------------------------------------ the shopping list, by order (supplier)
# (area, item, qty, what/code, low, high, currency, tag)
BUY = [
    ("JLCPCB · placa montada", "JLCPCB (peças da LCSC)", [
        ("Eletrônica", "Placa principal, 4 camadas, 246,5 × 95 × 1,2 mm: 5 unidades (engenharia 25,00 + placa 14,50)", "5", "fab/student_v03_gerbers.zip", 39.5, 39.5, "USD", "visto"),
        ("Eletrônica", "Montagem econômica só pelo fundo: preparação e estêncil", "1", "BOM e CPL em fab/", 9.79, 9.79, "USD", "visto"),
        ("Eletrônica", "%d tipos de peça estendida × US$ 3,09" % EXT_TYPES, str(EXT_TYPES), "a JLCPCB cobra por tipo; as demais são básicas", EXT_TYPES * 3.09, EXT_TYPES * 3.09, "USD", "visto"),
        ("Eletrônica", "Peças de 2 placas montadas (%d peças cada, %d linhas de BOM)" % (CPL_ROWS, BOM_LINES), "2", "sensores, codec, carregador, amplificador, conectores", 64, 75, "USD", "estimativa"),
        ("Eletrônica", "SMT e nitrogênio", "1", "", 3.2, 3.2, "USD", "estimativa"),
    ]),
    ("JLCPCB · grade do teclado", "JLCPCB (ou PCBWay)", [
        ("Teclado", "Grade FR-4 de 1,6 mm, máscara preta fosca, 10 furos escareados a 90°: 5 unidades (1 usada)", "5", "fab/student_v03_grade_gerbers.zip + figura", 15, 30, "USD", "estimativa"),
    ]),
    ("Gateron", "Loja da Gateron (ou Chosfox, Ukeebs)", [
        ("Teclado", "Teclas Gateron KS-20 Magnetic Orange (38 gf), pacote de 35", "28 (de 35)", "sensor Hall sob cada tecla", 24.5, 26.6, "USD", "visto"),
    ]),
    ("SparkFun · módulo", "DigiKey UK ou SparkFun", [
        ("Eletrônica", "Módulo MicroMod Teensy (DEV-16402)", "1", "£ 18,69 sem IVA na DigiKey UK; US$ 24,95 na SparkFun", 18.69 * RATE, 22.43 * RATE, "USD", "visto"),
    ]),
    ("eBay / Amazon · energia", "eBay, Amazon", [
        ("Energia", "Bateria LiPo 503450, 3,7 V, ~1000 mAh, 3 fios (NTC), plugue JST PH 2,0", "1", "medir o NTC (~10 kΩ) e a ordem dos fios antes de ligar", 5 * RATE, 8 * RATE, "USD", "visto"),
    ]),
    ("Eletrônica de bancada", "Pimoroni, Adafruit, SparkFun, Mouser, Amazon, eBay ou AliExpress", [
        ("Interface", "Módulo OLED 0,96″ 128 × 64, SSD1306, I²C, 4 pinos, 3,3 V", "1", "placa de ~27,3 × 27,8 mm, 4 furos de 2 mm; conferir a ordem dos pinos", 3 * RATE, 6 * RATE, "USD", "estimativa"),
        ("Interface", "Cabo JST SH 1,0 mm de 4 vias, 50 mm (Qwiic / STEMMA QT), uma ponta solta", "1", "plugue no J401; os fios sobem pela fenda e são soldados na tela", 2 * RATE, 4 * RATE, "USD", "estimativa"),
        ("Som", "Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W", "1", "pedir a frequência de ressonância; quanto mais baixa, melhor", 2 * RATE, 5 * RATE, "USD", "estimativa"),
        ("Som", "Tela acústica 0,3 mm (36 × 28 mm), junta de espuma de 1 mm Ø 28/24, silicone", "1 kit", "veda a frente e o furo dos fios da caixa", 4 * RATE, 8 * RATE, "USD", "estimativa"),
        ("Energia", "Cabo USB-C", "1", "carga, MIDI e configuração", 0, 5 * RATE, "USD", "estimativa"),
    ]),
    ("Ferragem e acabamento", "ferragem, loja de modelismo ou de tintas", [
        ("Fixação", "Parafusos M2 não magnéticos (latão ou inox A4): 10 × 16 mm de cabeça escareada (ISO 7046) com 10 porcas, 6 × 14 mm de cabeça panela, 2 × 5 mm, 4 × 4 mm", "22 + 10 porcas", "ferro e aço-carbono perto dos ímãs das teclas distorcem a leitura", 6 * RATE, 10 * RATE, "USD", "estimativa"),
        ("Fixação", "Módulo MicroMod: parafuso M2,5 × 8 de náilon, espaçador de náilon de 2,5 mm e porca M2,5 de náilon", "1 + 1 + 1", "o parafuso M2,5 × 3 que vem com o módulo não serve nesta pilha", 2 * RATE, 4 * RATE, "USD", "estimativa"),
        ("Apoio", "Pés autoadesivos de poliuretano ou silicone de 80 Shore A ou mais, Ø 8 × 1,5 mm", "10", "o silicone macio (40–60A) não serve: a tecla pior ultrapassa 0,05 mm de flexão", 2 * RATE, 5 * RATE, "USD", "estimativa"),
        ("Acabamento", "Tinta para os rebaixos e para as faixas (vermelho, laranja, amarelo, preto, marrom-avermelhado) ou vinil adesivo", "1 kit", "cores: ver a seção do conceito", 5 * RATE, 10 * RATE, "USD", "estimativa"),
        ("Interface", "Acrílico fumê escuro de 1 mm, 25,7 × 14,7 mm, cantos R 1", "1", "corte a laser sob encomenda, ou lixado de uma chapa", 3 * RATE, 8 * RATE, "USD", "estimativa"),
    ]),
    ("Impressão 3D", "JLC3DP, PCBWay ou Craftcloud (resina ou nylon MJF)", [
        ("Case", "Tampa (creme, sem emenda na parede, 24,6 mm de altura) e bandeja do fundo (cinza)", "1 + 1", "~118 cm³ de material", 0, 0, "USD", "estimativa"),
        ("Teclado", "Botões: 12 branco, 11 preto, 5 branco com pontos (4 alturas de haste)", "28", "resina ou MJF: o encaixe em cruz não sai em filamento", 0, 0, "USD", "estimativa"),
        ("Teclado", "Espaçadores da grade Ø 5 × 11,35 mm", "10", "", 0, 0, "USD", "estimativa"),
        ("Interface", "Knobs chapéu de 10 mm (furo em D de 9,2 mm de fundo), sem luva", "2", "preto, traço pintado", 0, 0, "USD", "estimativa"),
        ("Som", "Caixa acústica em L (9,75 cm³), na mesma peça do anel", "1", "paredes cheias: tem de ser estanque", 0, 0, "USD", "estimativa"),
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


# ------------------------------------------------------------------ parts by area
AREAS = [
    ("Eletrônica", "A placa vem pronta da JLCPCB, com todas as peças soldadas pelo fundo. Em casa: dois encoders, o módulo do processador e os fios do alto-falante.", [
        ("Placa principal, montada", "1", "JLCPCB", "4 camadas, 1,2 mm; %d peças soldadas por máquina, todas no fundo; 28 sensores Hall sob as teclas" % CPL_ROWS),
        ("Módulo MicroMod Teensy (DEV-16402)", "1", "SparkFun / DigiKey", "i.MX RT1062, 16 MB; encaixa no conector M.2 do fundo, preso no H101"),
        ("Sensor Hall TMAG5253 (C22401868)", "28", "JLCPCB (LCSC)", "um sob cada tecla; lê os dois polos"),
        ("Codec de áudio SGTL5000 (C2651833)", "1", "JLCPCB (LCSC)", "fone, entrada de microfone com bias, saída para o amplificador"),
        ("Amplificador MAX98357A (C910544), carregador BQ24074 (C54313), conversor TPS63001 (C28060)", "3", "JLCPCB (LCSC)", "som do alto-falante, carga da bateria, 3,3 V"),
        ("Multiplexadores 74HC4067 (C179326)", "2", "JLCPCB (LCSC)", "leem as 28 teclas por 2 canais"),
        ("Encoders com clique EC11E18244AU (C202365)", "2", "LCSC / Digi-Key (solda em casa)", "eixo de 20 mm (ponta a ~24,5 mm da placa): volume e registro; a JLCPCB não os solda nesta versão"),
        ("Conectores: USB-C, 2 jacks 3,5 mm (OUT e IN), JST SH da tela, JST PH da bateria", "5", "JLCPCB (LCSC)", "USB-C TYPE-C-31-M-12, jacks XUNPU PJ-327A, SM04B-SRSS-TB, S3B-PH-SM4-TB"),
    ]),
    ("Teclado", "28 teclas G3 a E5 em fileiras de 7, 8, 7 e 6, a 18,5 mm; fileiras 2 mm, 2 mm e 3 mm mais altas.", [
        ("Teclas Gateron KS-20 Magnetic Orange", "28", "Gateron", "curso de 4,1 mm; apoiadas na placa, seguras pela grade"),
        ("Grade FR-4 de 1,6 mm, máscara preta fosca, furos escareados", "1", "JLCPCB", "28 furos de Ø 6,2 mm e 10 furos escareados a 90° (boca de Ø 3,8 mm); fica a 0,15 mm acima das teclas"),
        ("Espaçadores Ø 5 × 11,35 mm", "10", "impressão", "entre a placa e a grade, na borda"),
        ("Parafusos M2 × 16 de cabeça escareada e porcas M2", "10 + 10", "ferragem", "a cabeça fica rente à grade; a porca fica sob a placa, dentro de um copo da bandeja"),
        ("Botões Ø 15 mm: branco, preto, branco com pontos (C e F)", "28", "impressão", "4 alturas de haste; topos a 7,4 / 9,4 / 11,4 / 14,4 mm acima do tampo"),
        ("Molas longas de 65 g ou 80 g (opcional)", "28", "loja de teclados", "mudam o peso da tecla; não alteram placa nem firmware"),
    ]),
    ("Interface", "Tela, dois knobs, grade do alto-falante e legendas, à esquerda do teclado.", [
        ("Módulo OLED 0,96″ 128 × 64 (I²C)", "1", "loja de eletrônica", "girado 180°, preso por baixo da tampa em 4 postes (M2 × 4)"),
        ("Cabo JST SH de 4 vias, 50 mm", "1", "loja de eletrônica", "o plugue vai no J401, no fundo da placa; os fios sobem pela fenda e são soldados na tela"),
        ("Janela de acrílico fumê de 1 mm", "1", "corte a laser", "24 × 13 mm de vidro à vista"),
        ("Knobs chapéu de 10 mm", "2", "impressão", "Ø 12 mm, 11,3 mm sobre o tampo, furo em D de 9,2 mm sobre o eixo inteiro"),
    ]),
    ("Som", "Alto-falante de 28 mm sob 7 fendas, com caixa acústica fechada em L de 9,75 cm³.", [
        ("Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W", "1", "loja de eletrônica", "fios soldados ao J501 (pads no topo da placa)"),
        ("Caixa acústica em L, com o anel de fixação", "1", "impressão", "estanque; 2 parafusos M2 × 5 nas buchas da tampa"),
        ("Tela acústica 0,3 mm e junta de espuma de 1 mm", "1 + 1", "loja de eletrônica", "entre as fendas e o alto-falante"),
    ]),
    ("Energia", "Bateria no piso da bandeja; para trocá-la, tira-se a bandeja (6 parafusos).", [
        ("Bateria LiPo 503450, ~1000 mAh, 3 fios", "1", "eBay / Amazon", "o terceiro fio é o NTC de 10 kΩ"),
        ("Cabo USB-C", "1", "—", "carga, MIDI e configuração pela página"),
    ]),
    ("Case, apoios e acabamento", "252 × 100 × 24,6 mm, tampa creme sem emenda e bandeja cinza (acabamento Retrô).", [
        ("Tampa, com o logo e as legendas em rebaixo de 0,4 mm", "1", "impressão", "chanfro de 4,0 × 3,5 mm, três sulcos, 6 postes de parafuso; furos inteiros para USB-C, OUT e IN"),
        ("Bandeja do fundo", "1", "impressão", "2 mm de piso, borda, nervuras, berço da bateria, 4 pinos e 4 pilares de apoio sob a placa"),
        ("Parafusos M2 × 14 da bandeja", "6", "ferragem", "pelo fundo: atravessam a bandeja e a placa e entram nos postes da tampa"),
        ("Pés de poliuretano ou silicone de 80A, Ø 8 × 1,5", "10", "loja de eletrônica", "colados nos rebaixos da bandeja: 4 sob os pinos, 4 sob os pilares, 2 à esquerda"),
        ("Fixação do módulo: parafuso M2,5 × 8, espaçador 2,5, porca M2,5 (náilon)", "1 + 1 + 1", "ferragem", "pilha de cima para baixo: parafuso, placa, espaçador, módulo, porca"),
        ("Tinta e faixas", "1 kit", "tintas / vinil", "faixas #C8402A, #E07A2C, #E3B23C; tinta #2B2925 e #8A3A22"),
    ]),
]

BY_SUPPLIER = [
    ("JLCPCB / LCSC", "placa principal montada (%d peças), grade FR-4 escareada" % CPL_ROWS),
    ("Gateron", "28 teclas KS-20 Magnetic Orange (pacote de 35)"),
    ("SparkFun ou DigiKey", "módulo MicroMod Teensy"),
    ("LCSC ou Digi-Key", "2 encoders EC11E18244AU (C202365), para soldar em casa"),
    ("eBay ou Amazon", "bateria LiPo 503450 de 3 fios"),
    ("Loja de eletrônica", "tela OLED, cabo JST SH, alto-falante, tela acústica, espuma, silicone, cabo USB-C, pés de 80A"),
    ("Ferragem e tintas", "parafusos e porcas M2 e M2,5 (inox A4, latão ou náilon), tinta, vinil"),
    ("Impressão 3D (JLC3DP, PCBWay, Craftcloud)", "tampa, bandeja, 28 botões, 10 espaçadores, 2 knobs, caixa acústica"),
    ("Corte a laser", "janela de acrílico fumê"),
]

EXPLODED = [
    ("Bandeja do fundo e 6 parafusos M2 × 14", "cinza, impressa; 10 pés de 80A colados por baixo"),
    ("Bateria LiPo 503450", "no berço da bandeja"),
    ("Placa principal", "montada pela JLCPCB, peças no fundo"),
    ("Módulo MicroMod Teensy", "sob a placa, no conector M.2"),
    ("Parafuso, espaçador e porca M2,5 de náilon", "prendem o módulo no H101"),
    ("Porcas M2 × 10", "sob a placa, uma em cada copo da bandeja"),
    ("Encoders × 2", "soldados em casa, no topo da placa"),
    ("Teclas Gateron × 28", "apoiadas na placa, sem solda"),
    ("Parafusos M2 × 16 escareados × 10", "rentes à face da grade"),
    ("Espaçadores × 10", "Ø 5 × 11,35 mm, na borda"),
    ("Grade FR-4 de 1,6 mm", "preta fosca, 28 furos e 10 escareados"),
    ("Tampa", "creme, impressa"),
    ("Janela de acrílico fumê", "24 × 13 mm de vidro à vista"),
    ("Tela OLED 0,96″", "presa por baixo da tampa, girada 180°"),
    ("Alto-falante e caixa acústica", "em L, 9,75 cm³"),
    ("Botões × 28", "entram por cima, pela grade"),
    ("Knobs × 2", "10 mm, sobre os eixos dos encoders"),
]

# ------------------------------------------------------------------ the assembly: ten steps
# (figure, title, time, tools, parts, [paragraphs], [warnings], check)
STEPS = [
    ("passo_1", "A placa e os encoders", "20 min",
     "ferro de solda (ponta fina, 330 °C), solda 0,6 mm com fluxo, alicate de corte, lupa",
     "placa principal, 2 encoders EC11E18244AU",
     ["Receba a placa da JLCPCB e confira a olho nu, com a lupa: os dois jacks e o USB-C devem estar na borda esquerda, ao fundo; o conector M.2 (J101), o JST SH da tela (J401) e o JST PH da bateria (J202) estão no fundo. Todas as peças estão do lado de baixo; do lado de cima só há as ilhas dos encoders, os pads dos fios do alto-falante (J501) e os furos.",
      "Os 5 pinos de cada encoder (3 do giro, 2 do clique) e as duas abas de fixação passam pela placa de cima para baixo. Encaixe-os até o corpo encostar na placa e solde por baixo: as pernas ficam 3,5 mm abaixo da placa. Alinhe pelo corpo, não pelo eixo: o eixo termina a ~24,5 mm da placa e o chato do eixo deve ficar do lado de dentro do furo em D do knob (passo 10).",
      "Não precisa cortar as pernas: a bandeja tem 4,4 mm de folga sob os encoders."],
     ["Solde só as pernas dos encoders; nada mais do topo precisa de solda neste passo.",
      "Gire o eixo à mão depois de soldar: deve girar em detentes e clicar ao apertar."],
     "Encoders retos, corpo rente à placa, eixo girando em detentes e com clique."),
    ("passo_2", "O módulo MicroMod", "10 min",
     "chave de fenda pequena ou os dedos, pinça",
     "módulo MicroMod Teensy, parafuso M2,5 × 8 de náilon, espaçador de náilon de 2,5 mm, porca M2,5 de náilon",
     ["Vire a placa de cabeça para baixo, sobre um pano. O conector M.2 (J101) fica no fundo da placa, à esquerda, e o furo H101, de 2,7 mm, a 20 mm dele, à direita.",
      "Encoste a borda de contatos do módulo no conector, a uns 30°, e empurre até assentar; depois baixe o módulo sobre o espaçador de náilon de 2,5 mm, posto entre a placa e o módulo, sobre o furo H101.",
      "Pelo topo da placa, passe o parafuso M2,5 × 8 de náilon pelo furo, pelo espaçador e pelo furo do módulo, e aperte a porca de náilon por baixo. A pilha, de cima para baixo: parafuso, placa (1,2), espaçador (2,5), módulo (1,0), porca (2,0). A porca vai a ~6,7 mm abaixo da face de cima da placa, e a ponta do parafuso a ~8 mm: o rebaixo de 1,0 mm do piso da bandeja deixa 1,1 mm de folga."],
     ["Aperte pouco: o náilon rosqueia fácil e a placa do módulo é fina.",
      "Não use o parafuso M2,5 × 3 que vem com o módulo: é curto demais para esta pilha.",
      "Trocar o módulo depois é uma operação rara: obriga a tirar a bandeja, a bateria e a levantar a placa (ver o final do manual)."],
     "Módulo reto e firme, sem folga; parafuso e porca sem passar da face de baixo do módulo mais do que ~1,3 mm."),
    ("passo_3", "As 28 teclas Gateron", "10 min",
     "nenhuma",
     "28 teclas Gateron KS-20 Magnetic Orange",
     ["Vire a placa de volta, com o topo para cima. Cada tecla tem dois pinos de plástico que a posicionam em dois furos da placa: pressione-a no lugar até assentar. Não há solda: o sensor Hall TMAG5253 está do outro lado da placa, bem sob a tecla, e lê o ímã que desce com a haste.",
      "As teclas entram em 4 fileiras, de frente para trás, de 7, 8, 7 e 6 teclas (a fileira da frente, a mais próxima de quem toca, é a 1; a de trás, a 4). Os furos já marcam as posições, a 18,5 mm; as fileiras se deslocam entre si em meia tecla, num arranjo hexagonal.",
      "Se for trocar as molas por molas mais pesadas (65 g ou 80 g), faça-o agora, e teste uma tecla primeiro: a mola mais pesada muda o peso, não as leituras."],
     ["Os ímãs das teclas atraem ferro: mantenha chaves de aço e parafusos longe das teclas durante a montagem, ou use ferramentas não magnéticas."],
     "As 28 teclas no mesmo nível, assentadas; cada uma desce e sobe sem prender."),
    ("passo_4", "A grade de FR-4", "25 min",
     "chave Phillips pequena, pinça, chave de boca ou alicate de bico para as porcas",
     "10 espaçadores Ø 5 × 11,35, grade FR-4 escareada, 10 parafusos M2 × 16 escareados, 10 porcas M2 (todos não magnéticos)",
     ["A grade é uma placa de FR-4 preta de 1,6 mm que cobre as teclas a 0,15 mm sem tocá-las e as impede de sair. Ela se prende pela borda, em 10 pontos (os mesmos 10 furos de 2,3 mm da placa).",
      "Ponha um espaçador sobre cada um dos 10 furos da placa, ponha a grade por cima, com a face de baixo para a placa e as bocas dos escareados para cima, e passe um parafuso M2 × 16 de cabeça escareada por cada furo, pelo topo, até atravessar o espaçador e a placa.",
      "Por baixo, enrosque a porca M2 em cada parafuso (apoie a placa na borda, de modo que o fundo fique livre, ou levante-a de lado). A porca vai ficar dentro de um copo da bandeja no passo 9, 3,2 mm de fundo, por isso fica logo abaixo da placa: a ponta do parafuso passa só ~0,25 mm da porca.",
      "Aperte em cruz, pouco a pouco. A cabeça deve ficar rente à face da grade: se sobrar uma cabeça acima, a tampa não fecha; se afundar demais, o escareado de 0,75 mm foi mal feito."],
     ["Use parafusos e porcas não magnéticos (latão ou inox A4): o aço comum perto dos ímãs distorce a leitura das teclas.",
      "Não force a grade: é FR-4, e uma rachadura na borda do furo não se conserta.",
      "Confira que a grade ficou a ~0,15 mm das teclas: ao apertar uma tecla, ela não deve raspar na grade."],
     "10 parafusos rentes, a grade plana, as teclas livres nos furos de Ø 6,2 mm."),
    ("passo_5", "Os botões", "10 min",
     "nenhuma",
     "28 botões impressos: 12 brancos, 11 pretos, 5 brancos com pontos",
     ["Cada botão tem uma haste com um encaixe em cruz que entra na cruz da tecla. Empurre-o por cima, pelo furo da grade, até assentar. A altura da haste muda por fileira, para que o dedo sinta cada fileira: 7,2 / 9,2 / 11,2 / 14,2 mm, da fileira 1 (a da frente) à 4 (a de trás); os topos ficam a 7,4 / 9,4 / 11,4 / 14,4 mm acima do tampo.",
      "Os pontos marcam o C e o F, para achar a posição no escuro. Os 5 botões pontilhados são os Cs e os Fs; a planta, na apresentação, mostra onde cada um fica.",
      "Pressione cada botão: a tecla deve descer e subir livre. Se um botão raspar na parede do furo da grade, ele não está reto."],
     ["Os botões são de resina ou nylon MJF: o encaixe em cruz de impressão em filamento quebra."],
     "28 botões retos, cada um descendo 4,1 mm e voltando."),
    ("passo_6", "O cabo da tela", "15 min",
     "ferro de solda, solda fina, cola quente, pinça, alicate de corte",
     "cabo JST SH de 4 vias de 50 mm (uma ponta solta), módulo OLED 0,96″",
     ["O conector da tela (J401) está no fundo da placa, e o módulo OLED vai preso à tampa, ao lado. O cabo liga os dois: encaixe o plugue JST SH no J401, pelo fundo, e faça os 4 fios subirem pela fenda de 7 × 2,5 mm que atravessa a placa, de baixo para cima. O plugue não passa pela fenda: só os fios.",
      "A ordem dos fios é a Qwiic: preto = GND, vermelho = 3,3 V, azul = SDA, amarelo = SCL. Confira a ordem dos pinos do seu módulo OLED (GND, VCC, SCL, SDA na maioria) e solde os 4 fios nas ilhas dele, deixando uns 30 mm de folga dobrada entre a placa e a tela. Uma gota de cola quente sobre as soldas alivia a tensão.",
      "O módulo OLED vai girado 180° na tampa, com a borda dos pinos virada para a frente, para os fios descerem quase em linha reta até a fenda: ~9 mm do módulo à placa, 1,2 mm da fenda e ~3 mm até o J401."],
     ["Confira a ordem dos pinos do módulo contra o plugue antes de soldar: a ordem varia entre fabricantes.",
      "A boca do J401 (para que lado o plugue entra) só se confirma na primeira placa montada: se o plugue pedir a direção contrária, vire-o."],
     "Os 4 fios soldados, firmes, sem ponte de solda; o plugue no J401."),
    ("passo_7", "A tampa por dentro", "30 min",
     "chave Phillips pequena, ferro de solda, cola, silicone",
     "tampa, janela de acrílico fumê, módulo OLED, caixa acústica, alto-falante, tela acústica, junta de espuma, 4 parafusos M2 × 4, 2 parafusos M2 × 5",
     ["Ponha a tampa de cabeça para baixo, sobre um pano: o poço do teclado fica embaixo, a abertura do fundo para cima. Cole o acrílico fumê na janela, por dentro, no rebaixo de 1,0 mm.",
      "Prenda o módulo OLED nos 4 postes (M2 × 4), com a tela virada para a janela. O vidro deve ficar atrás do acrílico, sem folga nem tensão.",
      "Cole a tela acústica nas fendas, ponha a junta de espuma e o alto-falante (Ø 28 × 5 mm) sob as 7 fendas, e prenda a caixa acústica em L, com 2 parafusos M2 × 5, nas buchas da tampa. Passe os fios do alto-falante pelo furo da caixa e vede-o com uma gota de silicone: a caixa é fechada e tem de ser estanque (9,75 cm³).",
      "Solde os fios do alto-falante nos pads do J501, no topo da placa (na frente da caixa), deixando uns 40 mm de folga. A placa fica ainda solta, ao lado da tampa, presa pelos fios do alto-falante e da tela: eles têm folga para o passo seguinte."],
     ["O silicone cura em horas: faça este passo antes e deixe curar.",
      "Não ponha o alto-falante sem a junta de espuma: ela é a vedação entre as fendas e a caixa."],
     "Janela firme, tela sem folga, caixa estanque (sopre no furo dos fios: o cone do alto-falante deve mexer)."),
    ("passo_8", "A placa na tampa", "10 min",
     "nenhuma",
     "tampa com tudo o que leva dentro; a placa com teclas, grade e botões",
     ["Com a tampa ainda de cabeça para baixo, desça a placa, também de cabeça para baixo (o topo para baixo), dentro dela. Os botões passam pelo poço do teclado, os eixos dos encoders pelos furos dos knobs, e os três soquetes (USB-C, OUT, IN) pendem para o lado aberto, sem cruzar a parede: terminam alinhados aos furos fechados da parede esquerda, 0,3 mm atrás dela.",
      "A placa chega a 0,5 mm da parede por todos os lados: entra reta, sem esforço. Os 6 postes da tampa entram pelos furos H1–H4, H9 e H10 da placa.",
      "Acomode os fios do alto-falante e da tela sem dobrar na fenda nem prender sob a placa."],
     ["Os conectores passam muito perto da parede: não force, ajuste a posição da placa se prender."],
     "A placa assentada nos postes, os botões saindo pelo poço, os 3 soquetes alinhados aos furos."),
    ("passo_9", "Bateria, bandeja e parafusos", "20 min",
     "chave Phillips pequena, multímetro",
     "bandeja do fundo, 10 pés de 80A, bateria LiPo 503450, 6 parafusos M2 × 14",
     ["Antes de tudo, cole os 10 pés nos rebaixos de Ø 8,4 mm da face de baixo da bandeja: 4 sob os pinos, 4 sob os pilares, 2 à esquerda. Eles ficam 1,0 mm para fora do rebaixo.",
      "Meça a bateria: o fio do meio (NTC) deve dar ~10 kΩ até o negativo. Confira a ordem dos fios contra o J202: 1 = positivo, 2 = NTC, 3 = negativo. Positivo e negativo invertidos danificam a placa.",
      "Ponha a bateria no berço da bandeja (à esquerda, na frente), ligue o plugue no J202 e dobre o fio sem apertar. Encaixe a bandeja na tampa, por baixo: os 4 pinos Ø 5 entram nos furos H5–H8 entre as teclas, os 4 pilares ficam sob a placa e as 10 porcas dos parafusos da grade caem nos copos.",
      "Por baixo, passe os 6 parafusos M2 × 14 pelos furos da bandeja e da placa até os postes da tampa. Aperte pouco a pouco, em cruz, sem passar da resistência: o plástico impresso rosqueia direto."],
     ["Use parafusos não magnéticos também aqui (latão ou inox A4).",
      "Positivo e negativo da bateria trocados danificam o carregador e o conversor: confira duas vezes.",
      "Os pés têm de ser de 80 Shore A ou mais: um pé de silicone macio faz a tecla pior flexionar mais que 0,05 mm."],
     "A bandeja rente à borda da tampa, sem vão; os 6 parafusos firmes; a bateria sem apertar."),
    ("passo_10", "Os knobs", "5 min",
     "nenhuma",
     "2 knobs de 10 mm",
     ["Vire o instrumento. Em cada encoder, encaixe um knob no eixo, com o furo em D virado para o chato do eixo, até a saia assentar sem raspar no tampo (folga de 0,8 mm). O furo tem 9,2 mm de fundo e termina 0,5 mm acima da ponta do eixo.",
      "O topo do knob fica a 11,3 mm sobre o tampo (z 25,8). Se o chato do eixo for mais curto do que o previsto, o knob pode girar em falso: nesse caso uma gota de cola no eixo resolve."],
     ["Esta é a medida mais incerta do modelo: o comprimento real do eixo só se confirma com a peça na mão (ver as medidas a conferir, no fim)."],
     "Os dois knobs retos, girando em detentes; o clique funciona."),
]

CHECKS = [
    ("Medidas da primeira amostra", "A lista do que o modelo estima e só a peça real confirma. Anote os números e eles viram a próxima versão do desenho.", [
        ("USB-C: altura do centro no fundo", "cupom da parede (`out/cupom_parede_*`), plugue real, ver se entra centrado e sem folga", "`USB_Z` (−2,9)"),
        ("Jacks: altura do eixo", "mesmo cupom, plugue P2 real (limite de Ø 6,4)", "`JACK_Z` (−4,0)"),
        ("Recuo da frente das tomadas até a parede", "paquímetro: face da tomada até a borda da placa (±0,1–0,2 mm de solda)", "`CONN_FRONT_X` (= parede + 0,3)"),
        ("Pilha do módulo (H101)", "paquímetro de profundidade: do fundo da placa até a ponta do parafuso e a porca", "`H101_RECESS` (Ø 8 × 1,0)"),
        ("Boca do J401 (cabo da tela)", "olhar o conector soldado: para que lado abre", "percurso do cabo (informativo)"),
        ("Eixo dos encoders: comprimento e chato", "paquímetro de profundidade da ponta do eixo à placa e do chato à ponta", "`KNOB['shaft_top']` (24,5), `shaft_flat` (4,5), `bore_over` (0,5)"),
        ("Compressão do pé de 80A sob 3 N", "case montado na mesa, peso de ~300 g na tecla SW23, paquímetro de profundidade ou relógio comparador", "`FOOT_H` (1,5); acima de 0,02 mm, trocar por PU de 90A"),
        ("OLED, bateria e plugues reais", "OLED: ilhas e área ativa; bateria 503450 com proteção e NTC; plugues contra 12,35 × 6,5 e Ø 6,4", "`OLED_PCB`, `BATTERY`, `USB_OPENING`, `JACK_OPENING_D`"),
    ]),
]

# ------------------------------------------------------------------ the extra CSS
CSS = V2.CSS + """
/* V3 additions */
.stepwide { display: block; }
.stepwide figure { margin: 0 0 0.8rem; }
.step .meta { display: grid; gap: 0.2rem 0.8rem; grid-template-columns: auto 1fr; margin: 0.4rem 0 0.2rem; font-size: 0.88rem; }
.step .meta dt { font-weight: 600; color: var(--muted); }
.step .meta dd { margin: 0; }
.warn { margin: 0.6rem 0; padding: 0.6rem 0.9rem; background: #FFF1EA; border: 1px solid #E6B49E; border-left: 5px solid var(--red); border-radius: 8px; font-size: 0.92rem; }
.warn ul { margin: 0; padding-left: 1.1rem; }
.check { margin: 0.6rem 0 0; padding: 0.5rem 0.8rem; background: #EEF5E6; border: 1px solid #B9D3A0; border-radius: 8px; font-size: 0.92rem; }
.diagram { margin: 1rem 0; overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--card); }
.diagram svg { display: block; width: 100%; min-width: 46rem; height: auto; }
.diagram text { font-family: "Inter", system-ui, sans-serif; fill: var(--ink); }
ul.sheets { display: grid; gap: 0.5rem 1rem; grid-template-columns: repeat(auto-fit, minmax(min(17rem, 100%), 1fr)); padding: 0; list-style: none; }
ul.sheets li { padding: 0.6rem 0.8rem; background: var(--card); border: 1px solid var(--line); border-radius: 8px; }
ul.sheets small { display: block; color: var(--muted); }
.tipbox { margin: 1rem 0; padding: 0.7rem 1rem; background: #F4F0E4; border: 1px solid var(--line); border-radius: 8px; }
code { font-size: 0.88em; background: #EFE9D8; padding: 0 0.25em; border-radius: 3px; }
.mini { display: grid; gap: 0.8rem; grid-template-columns: repeat(auto-fit, minmax(min(18rem, 100%), 1fr)); }
"""


def imgtag(name, alt):
    w, h = SIZES[name]
    return '<a href="img/%s.jpg"><img src="img/%s.jpg" width="%d" height="%d" alt="%s" loading="lazy" /></a>' % (name, name, w, h, esc(alt))


def img(name, alt, caption=None, cls=""):
    cap = "<figcaption>%s</figcaption>" % caption if caption else ""
    return '<figure class="%s">%s%s</figure>' % (cls, imgtag(name, alt), cap)


def head(title, desc, other=None):
    return '''<!doctype html>
<html lang="pt-BR">
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
  <title>%s</title>
  <meta name="description" content="%s" />
  <!-- Written by etutti/hardware/student_v03/pagina.py: edit the texts and the prices there.
       Part of the unlisted eTutti work in progress: kept out of the sitemap and of search results. -->
  <meta name="robots" content="noindex,nofollow" />
  <meta name="theme-color" content="#F3F1EC" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Michroma&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <link rel="stylesheet" href="styles.css?v=20261118" />
</head>
<body>
  <div class="stripes" aria-hidden="true"></div>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
''' % (esc(title), esc(desc))


FOOT = '''    <footer>
      <p>Projeto em desenvolvimento, fora do mapa do site e dos buscadores. Arquivos de projeto em <code>etutti/hardware/student_v03/</code> do repositório <a href="https://github.com/dataehora/beatconfused">dataehora/beatconfused</a>.</p>
      <p><a href="/">beatconfused.com</a> · <a href="mailto:beatconfused@beatconfused.com">beatconfused@beatconfused.com</a></p>
    </footer>
  </main>
</body>
</html>'''


# ------------------------------------------------------------------ the block diagram (SVG)
def diagram():
    def box(x, y, w, h, title, sub="", fill="#FBFAF6", stroke="#8A3A22"):
        r = '<rect x="%d" y="%d" width="%d" height="%d" rx="7" fill="%s" stroke="%s" stroke-width="1.5" />' % (x, y, w, h, fill, stroke)
        lines = sub.split("|") if sub else []
        ty = y + (h - 13 * len(lines) - 14) / 2 + 12
        r += '<text x="%d" y="%d" font-size="13" font-weight="700" text-anchor="middle">%s</text>' % (x + w / 2, ty, esc(title))
        for i, line in enumerate(lines):
            r += '<text x="%d" y="%d" font-size="10.5" text-anchor="middle" fill="#5C574F">%s</text>' % (x + w / 2, ty + 15 + 13 * i, esc(line))
        return r

    def line(x1, y1, x2, y2, label="", color="#2B2925", dash=False, both=False, lx=None, ly=None):
        d = ' stroke-dasharray="5 4"' if dash else ""
        m = ' marker-start="url(#ar)"' if both else ""
        r = '<path d="M%d %d L%d %d" stroke="%s" stroke-width="1.6" fill="none"%s%s marker-end="url(#ar)" />' % (x1, y1, x2, y2, color, d, m)
        if label:
            r += '<text x="%d" y="%d" font-size="10.5" text-anchor="middle" fill="%s">%s</text>' % (lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else min(y1, y2) - 6, color, esc(label))
        return r

    def group(x, y, w, h, label):
        return ('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="#F2EDDF" stroke="#D8D2C4" />'
                '<text x="%d" y="%d" font-size="10.5" font-weight="700" letter-spacing="2" fill="#8A3A22">%s</text>') % (x, y, w, h, x + 10, y + 16, label)

    P = ['<svg viewBox="0 0 1000 540" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagrama de blocos da eletrônica da Student V3">']
    P.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#2B2925" /></marker></defs>')
    # ---- energia (left)
    P.append(group(10, 14, 220, 460, "ENERGIA"))
    P.append(box(25, 40, 190, 50, "USB-C", "TYPE-C-31-M-12 · 5 V, MIDI"))
    P.append(box(25, 106, 190, 50, "Proteção ESD e TVS", "USBLC6-2SC6 · SMF5.0A"))
    P.append(box(25, 172, 190, 50, "Carregador BQ24074", "carga da LiPo · lê o NTC"))
    P.append(box(25, 238, 190, 50, "Bateria LiPo 503450", "3,7 V · ~1000 mAh · J202"))
    P.append(box(25, 304, 190, 50, "TPS63001 + L 2,2 µH", "buck-boost · 3,3 V fixo"))
    P.append(box(25, 400, 190, 54, "D206 (BAV70)", "o USB acorda o instrumento|(VBUS → EN)"))
    for y in (90, 156, 222, 288):
        P.append(line(120, y, 120, y + 16))
    # ---- processor (centre)
    P.append(box(330, 40, 190, 414, "Módulo MicroMod Teensy", "i.MX RT1062 · 600 MHz|16 MB de flash|conector M.2 (J101)|+ parafuso H101||áudio I²S · I²C|entradas analógicas|GPIO · USB", "#F7F2E4", "#C8402A"))
    P.append(line(215, 329, 330, 329, "3,3 V", "#C8402A", lx=272, ly=321))
    P.append(line(215, 427, 330, 427, "EN", "#8A3A22", True, lx=272, ly=419))
    # ---- right groups
    P.append(group(610, 14, 380, 232, "SOM"))
    P.append(box(625, 36, 350, 44, "Codec SGTL5000", "I²S · I²C (0x0A) · fone · microfone com bias"))
    P.append(line(520, 58, 625, 58, "I²S · I²C", both=True, lx=572, ly=50))
    P.append(box(625, 94, 350, 44, "Amplificador MAX98357A", "classe D · mesmo I²S do codec"))
    P.append(line(520, 116, 625, 116, "I²S", lx=572, ly=108))
    P.append(box(625, 152, 350, 36, "Alto-falante Ø 28 mm · 8 Ω", "caixa fechada de 9,75 cm³"))
    P.append(line(800, 138, 800, 152))
    P.append(box(625, 198, 170, 36, "OUT · fone 3,5 mm", "XUNPU PJ-327A"))
    P.append(box(805, 198, 170, 36, "IN · microfone 3,5 mm", "XUNPU PJ-327A"))
    P.append(group(610, 258, 380, 94, "TECLAS"))
    P.append(box(625, 280, 350, 60, "28 sensores Hall TMAG5253 + 2 × 74HC4067", "um sensor sob cada tecla · 16 canais por multiplexador"))
    P.append(line(520, 310, 625, 310, "analógico · S0–S3", both=True, lx=572, ly=302))
    P.append(group(610, 366, 380, 150, "INTERFACE"))
    P.append(box(625, 388, 350, 36, "2 encoders EC11E com clique", "volume · registro · o clique liga"))
    P.append(line(520, 406, 625, 406, "GPIO", lx=572, ly=398))
    P.append(box(625, 432, 350, 36, "Tela OLED SSD1306 · J401 JST SH", "I²C (0x3C) · o mesmo barramento do codec"))
    P.append(line(520, 450, 625, 450, "I²C", both=True, lx=572, ly=442))
    P.append(box(625, 474, 350, 32, "Botão Program · TS-1187A", "gravar o firmware"))
    P.append(line(520, 490, 625, 490, "GPIO", lx=572, ly=482))
    P.append('<text x="10" y="500" font-size="10.5" fill="#5C574F">Seta cheia: sinal ou energia. Tracejada: acordar.</text>')
    P.append('<text x="10" y="516" font-size="10.5" fill="#5C574F">Na própria placa: tudo, exceto os encoders, a tela, o alto-falante, a bateria e o módulo.</text>')
    P.append('</svg>')
    return "".join(P)


def build_index():
    rows = supplier_totals()
    tot_lo = sum(r[2] for r in rows)
    tot_hi = sum(r[3] for r in rows)
    opt_lo = sum(o[1] for o in OPTIONAL)
    opt_hi = sum(o[2] for o in OPTIONAL)
    h = []
    A = h.append
    A(head("BeatConfused | eTutti Student V3", "eTutti Student V3: o conceito, a eletrônica, as peças e onde comprar, a vista explodida, o orçamento e a ligação ao manual de montagem."))
    A('''    <header class="hero">
      <p class="eyebrow">BeatConfused Studio · protótipo</p>
      <h1>eTutti<small>STUDENT · V3</small></h1>
      <p class="lead">Um acordeão de teclado para estudar: 28 teclas magnéticas com velocity, tela, dois knobs, alto-falante, entrada de microfone, bateria e USB-C, numa caixa Retrô de 252 × 100 × 24,6 mm. A placa vem pronta da JLCPCB, montada toda pelo fundo.</p>''')
    A("      " + img("isometrico", "O eTutti Student V3 em perspectiva: tampa creme com faixas vermelha, laranja e amarela, teclado de botões brancos e pretos, tela e dois knobs à esquerda."))
    A('    </header>')
    A('''    <nav class="toc" aria-label="Seções">
      <a href="#conceito">Conceito</a><a href="#eletronica">Eletrônica</a><a href="#pecas">Peças e fornecedores</a>
      <a href="#explodida">Vista explodida</a><a href="#montagem">Montagem</a><a href="#orcamento">Orçamento</a><a href="#estado">Estado</a>
    </nav>''')

    # ---------------- concept
    A('    <section id="conceito">\n      <p class="kicker">1 · Conceito</p>\n      <h2>Um acordeão de estudo, do tamanho de uma prancheta</h2>')
    A('      <p class="sub">Para quem nunca viu o projeto: o eTutti é uma família de instrumentos eletrônicos com o teclado de um acordeão de botões (C-griff), a sensibilidade de um instrumento de verdade e nenhum fole. O Student é o modelo compacto, para estudar em qualquer lugar. A V3 é a mesma ideia da V2, com a placa refeita para que a fábrica monte tudo pelo fundo, e o case ajustado a isso.</p>')
    A('''      <ul class="facts">
        <li><b>28 teclas</b><span>C-griff, de G3 a E5, em 4 fileiras a 18,5 mm</span></li>
        <li><b>Velocity</b><span>sensor Hall sob cada tecla Gateron, curso de 4,1 mm</span></li>
        <li><b>252 × 100 × 24,6 mm</b><span>tampa creme sem emenda, bandeja cinza, 3 sulcos e chanfro de 4,0 × 3,5 mm</span></li>
        <li><b>Tela OLED 0,96″</b><span>registro, volume e carga, atrás de acrílico fumê</span></li>
        <li><b>2 knobs com clique</b><span>volume e registro; o clique liga</span></li>
        <li><b>Som próprio</b><span>alto-falante de 28 mm numa caixa fechada de 9,75 cm³</span></li>
        <li><b>Entradas e saídas</b><span>USB-C (carga e MIDI), OUT 3,5 mm e IN 3,5 mm (microfone)</span></li>
        <li><b>Bateria LiPo</b><span>1 célula, cerca de 1000 mAh, trocada tirando 6 parafusos</span></li>
      </ul>''')
    A('      <div class="grid">')
    A('<div class="card"><h3>O que é o C-griff</h3><p>Um acordeão de botões tem os botões em fileiras que sobem de semitom em semitom. Na disposição C-griff, cada fileira vizinha avança um semitom e o padrão se repete a cada terça menor: uma frase se toca em qualquer tom com o mesmo desenho dos dedos. Aqui são 28 botões, de G3 a E5, em 4 fileiras de 7, 8, 7 e 6; as fileiras se deslocam em meia tecla, num arranjo hexagonal a 18,5 mm.</p></div>')
    A('<div class="card"><h3>O teclado</h3><p>As fileiras sobem 2, 2 e 3 mm uma sobre a outra (topos a 7,4, 9,4, 11,4 e 14,4 mm acima do tampo), de modo que o dedo sente cada fileira. Os botões têm Ø 15 mm e cúpula convexa, em três tipos: branco, preto e branco com pontos (o C e o F, para achar a posição no escuro). Cada botão tem uma haste com encaixe em cruz sobre uma tecla Gateron magnética, cujo sensor Hall mede a velocidade da descida.</p></div>')
    A('<div class="card"><h3>A grade</h3><p>Uma placa de FR-4 de 1,6 mm, preta fosca, cobre as teclas a 0,15 mm e as segura sem plate nem parafusos à vista: ela é fixada só pela borda, com 10 parafusos de cabeça escareada rentes à face, sob a tampa. A tampa cobre a grade com 1,4 mm de material.</p></div>')
    A('<div class="card"><h3>A placa, pelo fundo</h3><p>Na V3 a JLCPCB monta todas as peças só pelo lado de baixo da placa: o USB-C, os dois jacks e os conectores ficam abaixo dela, e a tampa os recebe com furos inteiros na parede. O topo da placa só tem os dois encoders (soldados em casa) e as ilhas dos fios do alto-falante. Isso baixa o custo da montagem e tira da bancada 11 peças.</p></div>')
    A('<div class="card"><h3>O acabamento Retrô</h3><p>Faixas vermelha, laranja e amarela que dão a volta pelo tampo, pelo chanfro e pela parede, e o logo em Michroma em rebaixo de 0,4 mm com tinta.</p>')
    A('<ul class="swatches"><li><i style="background:#E8DEC6"></i>tampa #E8DEC6</li><li><i style="background:#9C9B96"></i>bandeja #9C9B96</li><li><i style="background:#C8402A"></i>#C8402A</li><li><i style="background:#E07A2C"></i>#E07A2C</li><li><i style="background:#E3B23C"></i>#E3B23C</li><li><i style="background:#2B2925"></i>tinta #2B2925</li><li><i style="background:#8A3A22"></i>tinta #8A3A22</li></ul></div>')
    A('<div class="card"><h3>Rigidez e apoio</h3><p>A placa não leva parafusos na área do teclado. Em vez disso, 4 pinos e 4 pilares impressos na bandeja a sustentam por baixo, sobre 10 pés de 80 Shore A: a pior tecla cede 0,036 mm sob 3 N (0,047 mm no pior caso, com o pé comprimido), abaixo da meta de 0,05 mm.</p></div>')
    A('      </div>')
    A("      " + img("planta", "O instrumento visto de cima: a coluna da esquerda com tela, dois knobs e a grade do alto-falante, e o teclado de 28 botões.",
                      "Planta. Da esquerda para a direita: logo, tela, knobs, grade do alto-falante, e o teclado."))
    A('      <div class="grid">')
    A("      " + img("parede", "A parede esquerda com o furo do USB-C e os dois furos dos jacks.", "Parede esquerda: USB-C, OUT e IN em furos fechados, sem emendas."))
    A("      " + img("logo", "Detalhe do logo eTUTTI e da tela.", "O logo, em rebaixo, e a janela da tela."))
    A("      " + img("corte", "Corte pelas fileiras do teclado.", "Corte pelas fileiras: a tampa, a grade, as teclas, a placa e a bandeja."))
    A("      " + img("corte_falante", "Corte pelo alto-falante e pela caixa acústica.", "Corte pelo alto-falante: fendas, alto-falante, caixa acústica e bateria."))
    A('      </div>')
    A('    </section>')

    # ---------------- electronics
    A('    <section id="eletronica">\n      <p class="kicker">2 · Eletrônica</p>\n      <h2>Como o instrumento pensa e soa</h2>')
    A('      <p class="sub">Uma placa só, de 4 camadas, com 28 sensores sob as teclas, um módulo de processador encaixado, o som, a bateria e a tela. Esta seção explica o desenho em blocos, depois o caminho de cada sinal; os esquemas completos, folha a folha, estão no final.</p>')
    A('      <div class="diagram">%s</div>' % diagram())
    A('      <h3>Como funciona, em quatro frases</h3>')
    A('''      <ol>
        <li><b>Lê as teclas.</b> Sob cada tecla há um sensor Hall TMAG5253. O ímã da haste se aproxima ao apertar, e o sensor devolve uma tensão que muda com a distância. Dois multiplexadores de 16 canais levam as 28 tensões a dois pinos analógicos do módulo; o módulo escolhe o canal pelos seletores S0–S3 e lê a descida da tecla milhares de vezes por segundo. A velocity vem do tempo que o sinal leva para percorrer uma parte do curso.</li>
        <li><b>Pensa.</b> O módulo MicroMod Teensy (i.MX RT1062 a 600 MHz, 16 MB) roda o firmware do acordeão: um sintetizador de lingüetas amostradas, com sete registros, em que a velocity vira a pressão do fole. Ele também lê os dois encoders (volume e registro), a tela e o botão Program.</li>
        <li><b>Soa.</b> O módulo manda o áudio digital (I²S) ao codec SGTL5000, que alimenta a saída de fone (OUT) e recebe o microfone (IN, com bias para eletreto); o mesmo I²S vai ao amplificador MAX98357A, que toca o alto-falante de 28 mm quando não há fone plugado.</li>
        <li><b>Alimenta-se.</b> O USB-C carrega a bateria LiPo pelo BQ24074 (que lê o NTC da bateria) e o TPS63001 faz 3,3 V estáveis para tudo, seja a bateria cheia, seja quase vazia. Ligar um cabo USB acorda o instrumento (D206); sem cabo, o clique do volume liga e desliga.</li>
      </ol>''')
    A('      <h3>Os sinais, por área</h3>')
    A('''      <div class="grid">
        <div class="card"><h3>Energia</h3><p>USB-C com proteção (USBLC6 e TVS SMF5.0A) → carregador BQ24074 → bateria (J202, 3 fios com NTC) → TPS63001 e indutor de 2,2 µH → 3,3 V. O módulo recebe o 3,3 V já regulado e traz o seu próprio sequenciamento de partida (o de fábrica da PJRC e da SparkFun).</p></div>
        <div class="card"><h3>Teclas</h3><p>28 sensores em 2 grupos, um multiplexador por grupo. Os 28 sensores são mais da metade do consumo da placa, por isso o firmware do Student V01 os liga em dois grupos, só enquanto lê (60 µs de despertar).</p></div>
        <div class="card"><h3>Som</h3><p>SGTL5000 no barramento I²C do módulo e na linha I²S (pinos 7/20/21/23); MAX98357A na mesma I²S; fone e microfone nos dois jacks de 3,5 mm (a manga é a terra; com um fone plugado, o alto-falante é desligado).</p></div>
        <div class="card"><h3>Interface</h3><p>Dois encoders com clique, o botão Program e a tela OLED por I²C: o mesmo barramento do codec, sem pino novo. A tela só mostra estado (registro, volume, carga), e o firmware a manda em pedaços pequenos, para não atrasar a leitura das teclas.</p></div>
      </div>''')
    A('      <h3>A placa: o que mudou da V2 para a V3</h3>')
    A('      <div class="tablewrap"><table><thead><tr><th></th><th>V2</th><th>V3</th></tr></thead><tbody>')
    for a, b, c in (
        ("Lado de cima", "encoders, USB-C, 2 jacks, ESD, TVS, passivos, J401, H101", "só os 2 encoders (solda em casa) e os pads dos fios do alto-falante"),
        ("Montagem na JLCPCB", "dois lados", "só o fundo (montagem econômica)"),
        ("Conector da tela (J401)", "topo", "fundo, com fenda de 7 × 2,5 mm para o cabo subir à tela"),
        ("Fixação do módulo (H101)", "espaçador SMD", "furo liso de 2,7 mm, parafuso e porca de náilon M2,5 e espaçador de 2,5 mm"),
        ("Jacks", "SHOU HAN PJ-327A", "XUNPU PJ-327A (a JLCPCB sinalizava o outro como difícil de processar)"),
        ("Energia com USB", "cadeia PWR_EN (5 peças)", "D206: o USB liga o 3,3 V; sem cadeia"),
        ("Par USB D+/D−", "em F.Cu, 90 Ω alvo", "inteiro em B.Cu, sem vias, 17,209 mm cada linha, sobre uma ilha de terra"),
        ("Tipos estendidos na JLCPCB", "~22", "%d" % EXT_TYPES),
    ):
        A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c)))
    A('</tbody></table></div>')
    A('      <div class="grid">')
    A('<figure><a href="img/placa_topo.jpg"><img src="img/placa_topo.jpg" width="%d" height="%d" alt="A placa vista de cima" loading="lazy" /></a><figcaption>Placa, topo: só os 2 encoders e os pads do alto-falante.</figcaption></figure>' % tuple(SIZES["placa_topo"]))
    A('<figure><a href="img/placa_fundo.jpg"><img src="img/placa_fundo.jpg" width="%d" height="%d" alt="A placa vista de baixo" loading="lazy" /></a><figcaption>Placa, fundo (espelhado): as 130 peças soldadas pela JLCPCB.</figcaption></figure>' % tuple(SIZES["placa_fundo"]))
    A('      </div>')
    A('      <h3>Os esquemas, folha a folha</h3>')
    A('      <p class="note">Exportados do KiCad (SVG, abrem no navegador; use o zoom): uma folha por área, com os códigos das peças (LCSC) no campo <i>Codigo</i> de cada uma.</p>')
    A('      <ul class="sheets">')
    for f, t, s in (("raiz", "Raiz", "as seis folhas ligadas"), ("P-processador", "P · Processador", "módulo MicroMod, conectores, botão Program"), ("E-energia", "E · Energia", "USB-C, carregador, bateria, conversor"),
                    ("F-fone", "F · Fone", "codec, jacks OUT e IN, microfone"), ("I-interface", "I · Interface", "encoders, tela"), ("A-alto-falante", "A · Alto-falante", "amplificador, alto-falante"),
                    ("T-teclas", "T · Teclas", "28 sensores e 2 multiplexadores")):
        A('<li><a href="esquema/%s.svg">%s</a><small>%s</small></li>' % (f, esc(t), esc(s)))
    A('      </ul>')
    A('      <div class="tipbox"><b>Verificação de regras da placa:</b> o DRC do KiCad, com paridade do esquema, dá 0 ligações faltando e paridade 0; as únicas violações são 3 larguras de trilha de 0,12 mm (a rede EN_B, na entrada de um pino fino, aceita) e 5 avisos de ponta solta (pontas de trilha fora do centro de uma via e um toco curto; o DRC confirma 0 ligações faltando). A impedância do par USB (90 Ω) não está garantida: o trecho tem ~25 mm.</div>')
    A('    </section>')

    # ---------------- parts by area
    A('    <section id="pecas">\n      <p class="kicker">3 · Peças e fornecedores</p>\n      <h2>O que leva, por área e por fornecedor</h2>')
    A('      <p class="sub">Seis áreas. A coluna “Fornecedor” diz onde cada peça se compra; o orçamento, na seção 6, está agrupado por pedido.</p>')
    for area, blurb, items in AREAS:
        A('      <h3>%s</h3><p class="note">%s</p>' % (esc(area), esc(blurb)))
        A('      <div class="tablewrap"><table><thead><tr><th>Peça</th><th>Qtd</th><th>Fornecedor</th><th>Observação</th></tr></thead><tbody>')
        for name, qty, who, obs in items:
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td>%s</td></tr>' % (esc(name), esc(qty), esc(who), esc(obs)))
        A('</tbody></table></div>')
    A('      <h3>Os mesmos itens, por fornecedor</h3>')
    A('      <div class="tablewrap"><table><thead><tr><th>Fornecedor</th><th>Fornece</th></tr></thead><tbody>')
    for a, b in BY_SUPPLIER:
        A("<tr><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b)))
    A('</tbody></table></div>')
    A('      <p class="note">Os arquivos para a JLCPCB estão em <code>etutti/hardware/student_v03/fab/</code>: Gerbers da placa e da grade, BOM (%d linhas, %d peças) e CPL (%d peças, todas no fundo). Cada peça tem o código LCSC; %d tipos são estendidos (cobrança por tipo) e os demais são básicos.</p>' % (BOM_LINES, BOM_PARTS, CPL_ROWS, EXT_TYPES))
    A('    </section>')

    # ---------------- exploded
    A('    <section id="explodida">\n      <p class="kicker">4 · Vista explodida</p>\n      <h2>Da bandeja aos botões</h2>')
    A('      <p class="sub">As peças em ordem de baixo para cima, como se montam. Na placa, as peças do fundo são as que a JLCPCB solda.</p>')
    w, hh = SIZES["explodido"]
    A('      <div class="exploded"><a href="img/explodido.jpg"><img src="img/explodido.jpg" width="%d" height="%d" alt="Vista explodida do instrumento, com as 17 peças numeradas." loading="lazy" style="width:100%%;height:auto;display:block;border-radius:6px" /></a>' % (w, hh))
    for k, (x, y) in PINS.items():
        A('<span class="pin" style="left:%.2f%%;top:%.2f%%" aria-hidden="true">%s</span>' % (x, y, k))
    A('</div>')
    A('      <ol class="legend">')
    for n, s in EXPLODED:
        A('<li><div>%s<br /><span>%s</span></div></li>' % (esc(n), esc(s)))
    A('      </ol>\n    </section>')

    # ---------------- assembly summary
    A('    <section id="montagem">\n      <p class="kicker">5 · Montagem</p>\n      <h2>Dez passos, uma solda e dois fios</h2>')
    A('      <p class="sub">O manual completo, com um desenho explodido por passo, ferramentas, tempos, cuidados e verificações, está em <a href="montagem.html"><b>montagem.html</b></a>. Aqui, o resumo.</p>')
    A('      <div class="tablewrap"><table><thead><tr><th>#</th><th>Passo</th><th>Tempo</th><th>O que se monta</th></tr></thead><tbody>')
    for i, (fig, title, tempo, tools, parts, texts, warns, check) in enumerate(STEPS, 1):
        A('<tr><td class="num">%d</td><td><a href="montagem.html#passo%d">%s</a></td><td class="qty">%s</td><td>%s</td></tr>' % (i, i, esc(title), esc(tempo), esc(parts)))
    A('</tbody></table></div>')
    A('      <p>A solda: os 2 encoders (passo 1) e os 4 fios da tela e os 2 do alto-falante (passos 6 e 7). A ordem importa: a placa é montada com tudo, e só então desce na tampa, de cabeça para baixo, e a bandeja fecha por baixo.</p>')
    A('      <div class="grid">%s%s</div>' % (img("bandeja_de_baixo", "A bandeja do fundo vista de baixo, com os rebaixos dos 10 pés.", "A bandeja, de baixo: os 10 rebaixos dos pés, as nervuras e o berço da bateria."),
                                              img("bandeja_de_cima", "A bandeja do fundo vista de cima, com pinos, pilares, copos das porcas e nervuras.", "A bandeja, de cima: 4 pinos, 4 pilares, os copos das porcas da grade e o berço da bateria.")))
    A('    </section>')

    # ---------------- budget
    A('    <section id="orcamento">\n      <p class="kicker">6 · Orçamento</p>\n      <h2>Quanto custa um instrumento</h2>')
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
            val = "—" if name == "Impressão 3D" else rng(ilo, ihi)
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td><span class="tag%s">%s</span></td><td class="num">%s</td></tr>'
              % (esc(item), esc(qty), esc(obs), "" if tag == "visto" else " est", "preço visto" if tag == "visto" else "estimativa", esc(val)))
        if name == "Impressão 3D":
            A('<tr class="sub"><td colspan="4">Pedido de impressão inteiro (tampa, bandeja, 28 botões, espaçadores, 2 knobs e a caixa acústica: cerca de 150 cm³ de material). Estimativa pelo volume; cotar em duas lojas com os STEP de <code>case/out/</code>.</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
        else:
            A('<tr class="sub"><td colspan="4">Subtotal</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
        A('</tbody></table></div>')
    A('      <h3>Como ler estes números</h3>')
    A('''      <ul>
        <li><b>Preço visto</b> é o de uma página de loja de 15 de novembro de 2026 ou da cotação da JLCPCB de 18 de novembro; <b>estimativa</b> é uma ordem de grandeza ainda sem cotação.</li>
        <li><b>A JLCPCB cobra a maior parte do pedido em taxas fixas</b> (engenharia, estêncil e uma taxa por tipo de peça estendida): montar as 5 placas custaria só um pouco mais que montar 2. A cotação real só sai com os arquivos enviados.</li>
        <li>A grade escareada pede aprovação da JLCPCB no pedido (o texto pronto está em <code>case/GRADE_ESCAREADA.md</code>); se ela recusar, a grade vai para a PCBWay, que lista furo escareado entre as capacidades.</li>
        <li>Sobram do primeiro pedido 1 placa montada (reserva), 3 placas nuas, 4 grades, 7 teclas e o que sobrar dos pacotes de ferragem: o segundo instrumento custa muito menos.</li>
        <li>O alto-falante ainda não foi escolhido: o estudo acústico usa um alto-falante nominal, e a caixa foi desenhada para um de Ø 28 × 5 mm.</li>
      </ul>''')
    A('    </section>')

    # ---------------- state
    A('    <section id="estado">\n      <p class="kicker">7 · Estado</p>\n      <h2>O que está pronto e o que falta</h2>')
    A('''      <div class="status">
        <h3>Estado do projeto (18 de novembro de 2026)</h3>
        <ul>
          <li><b>Pronto:</b> esquema, placa roteada (DRC com paridade do esquema: 0 ligações faltando), BOM, CPL de montagem só pelo fundo e Gerbers, grade FR-4 escareada, case em 20 peças sem nenhuma interferência em 245 pares (placa e bandeja entram por baixo livres em todo o curso), estudos de flexão e de acústica, renders e o manual de montagem.</li>
          <li><b>Pendente:</b> o <b>firmware</b> da V3 (o do Student V01 compila para o módulo e tem o acordeão e os knobs, mas não tem tela nem microfone, nem o acordar por USB); conferir a prévia de montagem da JLCPCB; escolher o alto-falante e refazer o estudo com os números dele; cotar a impressão; confirmar a grade escareada na JLCPCB.</li>
          <li><b>Medir na primeira amostra:</b> a lista de 8 itens (altura do USB-C e dos jacks, pilha do módulo, boca do J401, eixo dos encoders, compressão dos pés, OLED, bateria, plugues), no fim do <a href="montagem.html#medir">manual de montagem</a>.</li>
          <li><b>Nada foi encomendado, impresso ou montado.</b> Os preços acima são de pesquisa: confira todos na hora do pedido.</li>
        </ul>
      </div>''')
    A('    </section>')
    A(FOOT)
    return "\n".join(h), (tot_lo, tot_hi), [(r[0], r[2], r[3]) for r in rows]


def build_manual():
    h = []
    A = h.append
    A(head("BeatConfused | eTutti Student V3: manual de montagem", "Manual de montagem do eTutti Student V3: ferramentas, peças, dez passos com vista explodida, primeira ligação e medidas a conferir."))
    A('''    <header class="hero">
      <p class="eyebrow">BeatConfused Studio · manual de montagem</p>
      <h1>eTutti<small>STUDENT · V3</small></h1>
      <p class="lead">Do zero ao instrumento fechado, em dez passos, com uma vista explodida em cada um. Para quem nunca viu o projeto: leia primeiro <a href="index.html">a apresentação</a>.</p>
    </header>
    <nav class="toc" aria-label="Seções">
      <a href="#antes">Antes de começar</a><a href="#passos">Os dez passos</a><a href="#ligar">Primeira ligação</a><a href="#medir">Medir na amostra</a><a href="#trocar">Trocar o módulo</a>
    </nav>''')
    A('    <section id="antes">\n      <p class="kicker">0 · Antes de começar</p>\n      <h2>O que chega, o que se faz em casa</h2>')
    A('''      <div class="grid">
        <div class="card"><h3>Chega pronto</h3><ul>
          <li><b>Placa principal</b>, com todas as peças soldadas pelo fundo (JLCPCB), menos os 2 encoders.</li>
          <li><b>Grade FR-4</b>, preta, com 10 furos escareados (JLCPCB).</li></ul></div>
        <div class="card"><h3>Chega à parte</h3><ul>
          <li>Módulo MicroMod Teensy; teclas Gateron KS-20 Magnetic; bateria LiPo; tela OLED; cabo JST SH; alto-falante e vedação.</li>
          <li>Os 2 encoders EC11E18244AU.</li>
          <li>Parafusos, porcas e pés; acrílico; tinta.</li></ul></div>
        <div class="card"><h3>Impresso</h3><ul>
          <li>Tampa e bandeja; 28 botões; 10 espaçadores; 2 knobs; caixa acústica. Resina ou nylon MJF: o encaixe em cruz dos botões não sai em filamento.</li>
          <li>Pinte o logo e as legendas, e as faixas, antes de montar.</li></ul></div>
      </div>''')
    A('      <h3>Ferramentas</h3>')
    A('      <ul><li>Chave Phillips pequena (PH0) e uma chave de boca ou alicate de bico fino para as porcas M2.</li><li>Ferro de solda com ponta fina (330 °C), solda de 0,6 mm com fluxo, malha dessoldadora, lupa.</li><li>Pinça, alicate de corte, cola quente, silicone, cola cianoacrilato fraca.</li><li>Multímetro, paquímetro (de profundidade, se possível).</li><li>Um pano macio para apoiar a placa e a tampa.</li></ul>')
    A('      <div class="warn"><b>Antes de montar, três regras:</b><ul><li><b>Nada de ferro perto das teclas.</b> Os ímãs atraem aço comum e distorcem a leitura. Parafusos e porcas em latão, inox A4 ou náilon.</li><li><b>Bateria:</b> confira a ordem dos fios (1 = +, 2 = NTC, 3 = −) e meça o NTC (~10 kΩ) antes de ligar. Invertida, ela danifica a placa.</li><li><b>Sem força:</b> a grade é de FR-4, o módulo e os conectores são pequenos, e os plásticos impressos rosqueiam sem esforço.</li></ul></div>')
    A('      <p>Tempo total, com a cura do silicone: uma tarde. A tabela abaixo é a ordem dos passos; cada um tem a sua figura.</p>')
    A('      <div class="tablewrap"><table><thead><tr><th>#</th><th>Passo</th><th>Tempo</th><th>Ferramentas</th></tr></thead><tbody>')
    for i, (fig, title, tempo, tools, parts, texts, warns, check) in enumerate(STEPS, 1):
        A('<tr><td class="num">%d</td><td><a href="#passo%d">%s</a></td><td class="qty">%s</td><td>%s</td></tr>' % (i, i, esc(title), esc(tempo), esc(tools)))
    A('</tbody></table></div>')
    A('      <p class="note">Em cada figura, o que é novo no passo está em cor e o que já estava montado está esmaecido; as peças novas aparecem separadas, na direção em que entram. Nos passos 8 e 9 a imagem está de cabeça para baixo, como o instrumento fica na bancada: a tampa deitada sobre a face, a abertura para cima.</p>')
    A('    </section>')

    A('    <section id="passos">\n      <p class="kicker">1 · Os dez passos</p>\n      <h2>Montagem passo a passo</h2>')
    for i, (fig, title, tempo, tools, parts, texts, warns, check) in enumerate(STEPS, 1):
        extra = ""
        if fig == "passo_1":
            extra = '<figure>%s<figcaption>Passo 1, antes: o fundo da placa como chega da JLCPCB, com as 130 peças soldadas. Só os 2 encoders (acima) são soldados em casa.</figcaption></figure>' % imgtag("passo_1a", "A placa vista de baixo, com as peças soldadas pela fábrica")
        A('      <article class="step stepwide" id="passo%d"><figure>%s</figure><div><h3><span class="num">%d</span>%s</h3>' % (i, imgtag(fig, "Passo %d: %s" % (i, title)), i, esc(title)))
        A('<dl class="meta"><dt>Tempo</dt><dd>%s</dd><dt>Ferramentas</dt><dd>%s</dd><dt>Peças</dt><dd>%s</dd></dl>' % (esc(tempo), esc(tools), esc(parts)))
        A("".join("<p>%s</p>" % esc(t) for t in texts))
        if warns:
            A('<div class="warn"><b>Cuidado</b><ul>%s</ul></div>' % "".join("<li>%s</li>" % esc(w) for w in warns))
        A('<p class="check"><b>Verifique:</b> %s</p>' % esc(check))
        A(extra)
        A('</div></article>')
    A('    </section>')

    A('    <section id="ligar">\n      <p class="kicker">2 · Primeira ligação</p>\n      <h2>Antes de ligar, e o que esperar</h2>')
    A('''      <h3>Antes de ligar a bateria (com a bandeja ainda aberta, passo 9)</h3>
      <ol>
        <li>Multímetro em continuidade: <b>GND</b> (a manga de um dos jacks) contra o <b>3,3 V</b> (a saída do conversor TPS63001, U204): não deve haver continuidade, ou seria um curto.</li>
        <li>Bateria: o fio do meio dá ~10 kΩ até o negativo, e a ordem dos fios no plugue é a do J202 (1 +, 2 NTC, 3 −).</li>
        <li>Olhe por baixo, com a lupa, se o módulo está reto no conector M.2 e se as pernas dos encoders não tocam nada.</li>
      </ol>
      <h3>O que esperar</h3>
      <ul>
        <li><b>Cabo USB-C no computador:</b> o 3,3 V deve subir (o D206 acorda o instrumento) e o computador deve ver o módulo (com o firmware de fábrica da PJRC, como “Teensy”; depois de gravado, como “eTutti”).</li>
        <li><b>Carga:</b> com a bateria ligada e o cabo, o carregador (BQ24074) sobe a tensão da bateria; meça: ela deve chegar a 4,2 V.</li>
        <li><b>Firmware:</b> o sketch de <code>etutti/firmware/etutti_synth/</code> compila para o Teensy MicroMod (<code>teensy:avr:teensyMM:usb=midi,speed=396</code>) e tem o acordeão amostrado, os sete registros e os knobs. <b>Falta, para a V3:</b> a tela, o microfone, o acordar por USB e o mapeamento definitivo dos pinos (a placa da V3 não tem LED). Até lá, as teclas, o som e a leitura só se testam com o firmware do Student V01.</li>
        <li><b>Primeiro teste das teclas:</b> grave o firmware (botão Program, ao fundo, atrás do furo em (52; 36)) e, na página <a href="/etutti/etuttino/">/etutti/etuttino/</a>, ligue o MIDI e aperte as teclas. Cada tecla deve dar nota e velocity coerentes.</li>
        <li><b>Par USB:</b> a impedância de 90 Ω não está garantida; confira na primeira placa a conexão (velocidade e MIDI).</li>
      </ul>''')
    A('    </section>')

    A('    <section id="medir">\n      <p class="kicker">3 · Medir na primeira amostra</p>\n      <h2>O que o modelo estima e só a peça real confirma</h2>')
    for title, blurb, rows in CHECKS:
        A('      <p class="sub">%s Nenhuma forma muda até lá.</p>' % esc(blurb))
        A('      <div class="tablewrap"><table><thead><tr><th>O que medir</th><th>Como</th><th>Parâmetro que muda</th></tr></thead><tbody>')
        for a, b, c in rows:
            A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c).replace("`", "")))
        A('</tbody></table></div>')
    A('    </section>')

    A('    <section id="trocar">\n      <p class="kicker">4 · Manutenção</p>\n      <h2>Trocar a bateria ou o módulo</h2>')
    A('      <p><b>Bateria:</b> tire os 6 parafusos M2 × 14 do fundo e a bandeja; desligue o J202 e troque; feche como no passo 9.</p>')
    A('      <p><b>Módulo MicroMod</b> (rara): tire a bandeja, desligue o J401 e a bateria, tire os knobs, levante a placa uns 3 cm (os fios do alto-falante e da tela seguram) e solte os 4 parafusos do módulo OLED; a placa sai inteira e o parafuso do H101 fica acessível pelo topo. É uma limitação aceita; uma porca SMD no topo, soldada em casa, permitiria soltar o módulo só tirando a bandeja.</p>')
    A('      <p class="note">As figuras destes passos vêm do modelo 3D do case (<code>etutti/hardware/student_v03/case/passos.py</code>); a peça real pode diferir nos detalhes que a lista acima marca como a medir.</p>')
    A('    </section>')
    A(FOOT)
    return "\n".join(h)


def make_board_pictures():
    from PIL import Image
    for src, dst in (("student_v03_top.png", "placa_topo"), ("student_v03_bottom.png", "placa_fundo")):
        im = Image.open(os.path.join(HERE, "fab", src)).convert("RGB")
        w = 1500
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(os.path.join(IMG, dst + ".jpg"), quality=85, optimize=True, progressive=True)
        SIZES[dst] = [w, h]
    json.dump(SIZES, open(os.path.join(IMG, "tamanhos.json"), "w"), indent=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    make_board_pictures()
    page, tot, rows = build_index()
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
    open(os.path.join(OUT, "montagem.html"), "w", encoding="utf-8", newline="\n").write(build_manual())
    open(os.path.join(OUT, "styles.css"), "w", encoding="utf-8", newline="\n").write(CSS)
    print("total", [round(v) for v in tot])
    for r in rows:
        print("  %-30s %6.0f %6.0f" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
