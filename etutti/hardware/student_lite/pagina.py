"""eTutti Student Lite: writes the page beatconfused.com/etutti/studentLite/.

    python etutti/hardware/student_lite/pagina.py

A cost-reduction DRAFT of the Student V2: same board, three changes (JLCPCB assembles the bottom side
only; no screen; no case). Reuses the V2 page's CSS, helpers and price conventions (student_v02/pagina.py);
the pictures come from passos_lite.py and the fab files from lite.py. Money: see student_v02/pagina.py
("visto" = a shop page seen on 15 Nov 2026, "estimativa" = not quoted).
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "student_v02"))
import pagina as V2         # noqa: E402

RATE = V2.RATE
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "studentLite"))
IMG = os.path.join(OUT, "img")
SIZES = json.load(open(os.path.join(IMG, "tamanhos.json")))
PINS = json.load(open(os.path.join(IMG, "ancoras.json")))
FAB = json.load(open(os.path.join(HERE, "fab.json"), encoding="utf-8"))
esc, rng = V2.esc, V2.rng

# (order, supplier, [(area, item, qty, note, low, high, currency, tag)])
BUY = [
    ("JLCPCB · placa, montagem só no fundo", "JLCPCB (peças da LCSC)", [
        ("Eletrônica", "Placa principal, 4 camadas, 246,5 × 95 × 1,2 mm, ENIG: 5 unidades", "5", "Gerbers em fab/student_lite_gerbers.zip (os mesmos da V2)", 34, 34, "USD", "estimativa"),
        ("Eletrônica", "Preparação da montagem de um só lado e estêncil", "1", "BOM e CPL só do fundo, em fab/", 30, 40, "USD", "estimativa"),
        ("Eletrônica", "Taxa por tipo de peça estendida (cerca de 16 tipos, contra 22 na V2)", "16", "saíram o encoder, o USB-C, o jack, o TVS, o ESD e o JST SH", 29, 51, "USD", "estimativa"),
        ("Eletrônica", "Peças das 2 placas montadas (125 peças cada, 32 linhas de BOM)", "2", "28 sensores, codec, carregador, amplificador, 2 multiplexadores, conector do módulo e da bateria", 55, 62, "USD", "estimativa"),
    ]),
    ("JLCPCB · grade do teclado", "JLCPCB", [
        ("Teclado", "Grade FR-4 de 1,6 mm, 2 camadas, máscara preta fosca: 5 unidades (1 usada)", "5", "fab/student_v02_grade_gerbers.zip", 10, 20, "USD", "estimativa"),
    ]),
    ("LCSC · peças do topo, soldadas em casa", "LCSC", [
        ("Eletrônica", "Encoder com clique EC11E18244AU (C202365)", "2", "eixo de 20 mm: volume e registro", 4, 8, "USD", "estimativa"),
        ("Eletrônica", "USB-C TYPE-C-31-M-12 (C165948) e 2 jacks PJ-327A (C668605)", "1 + 2", "USB-C com 4 pinos de fixação; jacks OUT e IN", 1.5, 3.5, "USD", "estimativa"),
        ("Eletrônica", "USBLC6-2SC6 (C7519), SMF5.0A (C151296), 10 µF 0603 (C19702), 100 nF 0402 (C1525), 100 kΩ 0402 (C25741), 1 MΩ 0402 (C26083)", "6 tipos", "peças pequenas: peça a mais, para o caso de se perder uma", 1, 3, "USD", "estimativa"),
        ("Eletrônica", "Frete da LCSC até Londres (pedido pequeno)", "1", "ou junte ao pedido de outro fornecedor", 8, 20, "USD", "estimativa"),
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
    ("Eletrônica de bancada e ferragem", "Pimoroni, Adafruit, Mouser, Amazon, eBay ou AliExpress", [
        ("Interface", "Knobs para o eixo do encoder (conferir o diâmetro e o formato do eixo)", "2", "no lugar dos knobs impressos da V2", 2, 6, "USD", "estimativa"),
        ("Som", "Alto-falante Ø 28 × 5 mm, 8 Ω, 2 W", "1", "sem caixa acústica: soa fraco, serve para testar", 2 * RATE, 5 * RATE, "USD", "estimativa"),
        ("Energia", "Cabo USB-C", "1", "carga, MIDI e configuração", 0, 5 * RATE, "USD", "estimativa"),
        ("Fixação", "10 parafusos M2 × 16 com porca; 10 espaçadores de nylon M2, 11 mm, mais arruelas finas para acertar a altura; 4 pés de borracha", "1 kit", "os espaçadores impressos da V2 viram peças de mercado; os pés mantêm a placa fora da mesa", 5.5, 12, "USD", "estimativa"),
    ]),
]
OPTIONAL = [("Capas de tecla MX genéricas, 28 (o Lite não leva os botões impressos)", 6, 15, "estimativa"),
            ("Molas longas de 65 g e de 80 g, 1 pacote de cada", 6 * RATE, 12 * RATE, "estimativa")]

# what the V2 page lists that the Lite leaves out
CUT = [
    ("Tampa, base, 28 botões, 10 espaçadores, 2 knobs e caixa acústica (impressão 3D)", "case"),
    ("Tela OLED, cabo JST SH, janela de acrílico", "tela"),
    ("Tela acústica, espuma e silicone", "case"),
    ("Parafusos do case (M2 × 14, × 5, × 4), tinta e vinil", "case"),
    ("Soldagem dos encoders pela JLCPCB, montagem do topo, JST SH (J401)", "montagem"),
]

AREAS = [
    ("Montada pela JLCPCB (só o fundo)", "125 peças por placa, 32 linhas de BOM; é a lista de <code>fab/student_lite_bom.csv</code>.", [
        ("Placa principal, 4 camadas", "1", "JLCPCB", "a mesma da V2: nenhum arquivo de fabricação muda"),
        ("Sensor Hall TMAG5253 (C22401868)", "28", "JLCPCB (LCSC)", "um sob cada tecla"),
        ("Codec SGTL5000 (C2651833), amplificador MAX98357A (C910544), carregador BQ24074 (C54313), conversor TPS63001 (C28060)", "4", "JLCPCB (LCSC)", "som, carga e 3,3 V"),
        ("Multiplexadores 74HC4067 (C179326)", "2", "JLCPCB (LCSC)", "leem as 28 teclas por 2 canais"),
        ("Conector M.2 do módulo (J101), espaçador do módulo (H101), JST PH da bateria (J202), botão Program (SW403)", "4", "JLCPCB (LCSC)", "tudo no fundo"),
        ("Resistores, capacitores, ferrites, indutor e demais passivos", "cerca de 80", "JLCPCB (LCSC)", "0402, 0603 e 0805"),
    ]),
    ("Soldadas em casa (topo)", "11 peças: o que a JLCPCB não solda quando só monta o fundo. Lista em <code>fab/student_lite_montar_em_casa.csv</code>.", [
        ("Encoders EC11E18244AU (SW401, SW402)", "2", "LCSC", "furo passante, 5 pinos e 2 de fixação cada; levam os knobs"),
        ("USB-C TYPE-C-31-M-12 (J201)", "1", "LCSC", "SMD de 16 pinos e 4 pinos de fixação: a peça mais difícil"),
        ("Jacks PJ-327A (J301 OUT, J302 IN)", "2", "LCSC", "SMD com 2 pinos de fixação"),
        ("USBLC6-2SC6 (U201), SMF5.0A (D201)", "2", "LCSC", "SOT-23-6 e SOD-123F"),
        ("10 µF 0603 (C210), 100 nF 0402 (C308), 100 kΩ 0402 (R303), 1 MΩ 0402 (R304)", "4", "LCSC", "as menores peças da placa"),
    ]),
    ("Comprado à parte, encaixado ou soldado em casa", "O que não vai na placa.", [
        ("Módulo MicroMod Teensy (DEV-16402)", "1", "SparkFun / DigiKey", "no conector M.2 do verso, com 1 parafuso M2,5 × 3"),
        ("Teclas Gateron KS-20 Magnetic Orange", "28", "Gateron", "apenas encaixadas na placa: sem solda"),
        ("Grade FR-4 de 1,6 mm, máscara preta fosca", "1", "JLCPCB", "28 furos de Ø 6,2 mm; fica a 0,15 mm acima das teclas"),
        ("Espaçadores de nylon M2 de 11 mm, parafusos M2 × 16 e porcas", "10 + 10 + 10", "ferragem", "fixam a grade pela borda"),
        ("Alto-falante Ø 28 × 5 mm, 8 Ω", "1", "loja de eletrônica", "fios soldados nos 2 pads do J501"),
        ("Bateria LiPo 503450 de 3 fios", "1", "eBay / Amazon", "no J202"),
        ("Knobs", "2", "loja de eletrônica", "no eixo dos encoders"),
        ("Cabo USB-C", "1", "—", "carga, MIDI e configuração"),
    ]),
    ("Não faz parte do Lite", "Tudo isto está na V2 e foi cortado.", [
        ("Case (tampa e base), botões, espaçadores impressos, knobs impressos e caixa acústica", "—", "impressão 3D", "o Lite é uma placa aberta, para avaliar o custo"),
        ("Tela OLED, cabo JST SH, conector J401, janela de acrílico", "—", "—", "o firmware da V2 também precisaria ignorar a tela"),
        ("Tinta, vinil, tela acústica, espuma, silicone e parafusos do case", "—", "—", ""),
    ]),
]

EXPLODED = [
    ("Placa principal", "montada pela JLCPCB no fundo"), ("Peças pequenas, USB-C e jacks", "soldados em casa, no topo"),
    ("Encoders × 2", "soldados em casa"), ("Módulo MicroMod Teensy", "sob a placa, no conector M.2"),
    ("Teclas Gateron × 28", "apoiadas na placa"), ("Espaçadores de nylon × 10", "11 mm, na borda"),
    ("Grade FR-4 de 1,6 mm", "máscara preta fosca"), ("Parafusos M2 × 16 e porcas × 10", "porca sob a placa"),
    ("Knobs × 2", "sobre os eixos dos encoders"),
]

STEPS = [
    ("lite_jlc_fundo", "Receber e conferir a placa", [
        "A JLCPCB entrega a placa com o fundo pronto: sensores, codec, amplificador, carregador, conversor, multiplexadores e o conector do módulo. O topo está nu, só com os pads.",
        "Confira a olho: os conectores sobre os pads, o pino 1 dos chips e dos 28 sensores. Meça com o multímetro que não há curto entre o GND e o 3,3 V antes de soldar qualquer coisa.",
    ], "Nada: é o que chega pelo correio (o verso da placa)"),
    ("lite_passo_2", "Soldar as peças pequenas e os conectores do topo", [
        "Com fluxo, pinça e ferro de ponta fina (ou ar quente): primeiro os quatro passivos (C210, C308, R303, R304), depois U201 (SOT-23-6) e D201 (a faixa do catodo para o lado certo).",
        "Em seguida, os jacks J301 e J302 e, por último, o USB-C J201: ponha primeiro os pinos de fixação, depois alinhe os 16 pinos e solde com fluxo em abundância. Passe a lupa para ver pontes entre pinos.",
    ], "USB-C, 2 jacks, ESD, TVS e 4 passivos"),
    ("lite_passo_3", "Encoders e knobs", [
        "Encaixe os dois encoders EC11E nos furos (volume à esquerda, registro à direita), segure-os contra a placa e solde os 5 pinos e os 2 de fixação de cada um, de baixo.",
        "Encaixe os knobs nos eixos de 20 mm.",
    ], "2 encoders e 2 knobs"),
    ("lite_passo_4", "Módulo", [
        "Pelo verso, encaixe o módulo MicroMod Teensy no conector M.2 a 30° e prenda-o ao espaçador com o parafuso M2,5 × 3.",
        "Com a placa ainda sem teclas e sem bateria, ligue o USB-C a um computador: nada deve esquentar. Sem firmware da V2, o teste de sinais fica para depois.",
    ], "Módulo MicroMod Teensy"),
    ("lite_passo_5", "Teclas", [
        "Pressione as 28 teclas Gateron nos seus lugares: dois pinos de plástico por tecla a posicionam, e não há solda (o sensor Hall está no verso).",
        "Para trocar as molas, faça-o agora, com uma tecla de teste primeiro.",
    ], "28 teclas Gateron KS-20"),
    ("lite_passo_6", "Grade", [
        "Ponha os 10 espaçadores de nylon sobre os furos da borda, a grade FR-4 por cima e os parafusos M2 × 16; as porcas ficam por baixo da placa. Se a grade encostar nas teclas, calce os espaçadores com arruelas finas até sobrar cerca de 0,15 mm.",
        "Cole os 4 pés de borracha sob a placa.",
    ], "10 espaçadores, grade FR-4, 10 parafusos, porcas e pés"),
    ("lite_final", "Alto-falante e bateria", [
        "Solde os dois fios do alto-falante nos pads do J501 (no topo, perto da borda inferior).",
        "Antes de ligar a bateria: meça o terceiro fio (cerca de 10 kΩ até o negativo) e confira a ordem dos fios contra o J202 (1 positivo, 2 NTC, 3 negativo). Positivo e negativo invertidos danificam a placa.",
    ], "Alto-falante e bateria"),
]


def usd_range(lo, hi):
    return rng(lo, hi)


def supplier_totals():
    rows = []
    for name, who, items in BUY:
        rows.append((name, who, sum(i[4] for i in items), sum(i[5] for i in items), items))
    return rows


def imgtag(name, alt):
    w, h = SIZES[name]
    return '<a href="img/%s.jpg"><img src="img/%s.jpg" width="%d" height="%d" alt="%s" loading="lazy" /></a>' % (name, name, w, h, esc(alt))


def build():
    rows = supplier_totals()
    lo = sum(r[2] for r in rows)
    hi = sum(r[3] for r in rows)
    v2 = V2.supplier_totals()
    v2lo = sum(r[2] for r in v2)
    v2hi = sum(r[3] for r in v2)
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
    A('  <title>BeatConfused | eTutti Student Lite</title>')
    A('  <meta name="description" content="eTutti Student Lite: rascunho de baixo custo do Student V2, sem tela e sem case, com a placa montada só no fundo; peças, montagem em casa e orçamento." />')
    A('  <!-- Written by etutti/hardware/student_lite/pagina.py: edit the texts and the prices there.\n       Part of the unlisted eTutti work in progress: kept out of the sitemap and of search results. -->')
    A('  <meta name="robots" content="noindex,nofollow" />\n  <meta name="theme-color" content="#F3F1EC" />')
    A('  <link rel="preconnect" href="https://fonts.googleapis.com" />\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />')
    A('  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Michroma&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />')
    A('  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />\n  <link rel="stylesheet" href="styles.css?v=20261117" />\n</head>\n<body>')
    A('  <div class="stripes" aria-hidden="true"></div>\n  <main class="page">')
    A('    <a class="site-title" href="/">beatconfused.com</a>')
    A('''    <header class="hero">
      <p class="eyebrow">BeatConfused Studio · rascunho de custo</p>
      <h1>eTutti<small>STUDENT · LITE</small></h1>
      <p class="lead">A mesma placa do Student V2, com três cortes para medir quanto custa a versão mais barata: a JLCPCB monta só o fundo, sem tela e sem case. O resto da montagem é em casa.</p>''')
    A("      " + imgtag("lite_final", "A placa do Student Lite montada, com teclas, grade preta e dois knobs, sem case."))
    A('    </header>')
    A('''    <nav class="toc" aria-label="Seções">
      <a href="#mudancas">O que muda</a><a href="#pecas">Peças</a><a href="#explodida">Vista explodida</a>
      <a href="#montagem">Montagem em casa</a><a href="#orcamento">Orçamento</a>
    </nav>''')

    A('    <section id="mudancas">\n      <p class="kicker">1 · O que muda</p>\n      <h2>Três cortes sobre o Student V2</h2>')
    A('      <p class="sub">Nada na placa nem na grade foi redesenhado: os arquivos de fabricação são os da V2. O que muda é o que se encomenda e o que se monta em casa.</p>')
    A('      <div class="grid">')
    A('<div class="card"><h3>1 · JLCPCB monta só o fundo</h3><p>Das 137 peças da V2, 125 estão no fundo e a JLCPCB as solda. As 12 do topo ficam sem montar; delas, 11 são soldadas em casa (USB-C, 2 jacks, ESD, TVS, 4 passivos e os 2 encoders com os knobs) e a 12ª, o conector da tela, não existe no Lite. A montagem de um lado só cobra menos de preparação e de peças estendidas.</p></div>')
    A('<div class="card"><h3>2 · Sem tela</h3><p>Saem a tela OLED, o cabo JST SH e a janela de acrílico. O conector J401 fica sem peça. O firmware da V2 ainda não existe, e o do Lite não usaria a tela.</p></div>')
    A('<div class="card"><h3>3 · Sem case</h3><p>Saem a tampa, a base, os 28 botões, os knobs e os espaçadores impressos, a caixa acústica, a tinta e os parafusos do case. A placa fica aberta, com 4 pés de borracha, e a grade FR-4 continua fixando as teclas.</p></div>')
    A('      </div>')
    A('      <h3>O que continua igual</h3>')
    A('      <p>28 teclas Gateron KS-20 Magnetic com velocity, a placa de 4 camadas com sensores Hall, o módulo MicroMod Teensy, o codec com saída de fone e entrada de microfone, o alto-falante de 28 mm (agora sem caixa), a bateria LiPo e o USB-C.</p>')
    A('''      <div class="status">
        <h3>Estado</h3>
        <ul>
          <li><b>Pronto:</b> a lista de peças do fundo e do topo, os arquivos de montagem só do fundo (<code>fab/student_lite_cpl.csv</code> e <code>_bom.csv</code>), as imagens, o orçamento.</li>
          <li><b>Não verificado:</b> a prévia da JLCPCB com o CPL só do fundo, o encaixe das peças do topo à mão, e se o firmware pode rodar sem a tela. Os preços da JLCPCB são estimativas, derivadas da V2.</li>
          <li><b>Nada foi encomendado nem montado.</b></li>
        </ul>
      </div>
    </section>''')

    A('    <section id="pecas">\n      <p class="kicker">2 · Peças</p>\n      <h2>O que leva, e quem solda cada parte</h2>')
    A('      <p class="sub">Quatro grupos: o que a JLCPCB monta, o que se solda em casa, o que se compra à parte e o que saiu.</p>')
    for area, blurb, items in AREAS:
        A('      <h3>%s</h3><p class="note">%s</p>' % (esc(area), blurb))
        A('      <div class="tablewrap"><table><thead><tr><th>Peça</th><th>Qtd</th><th>Fornecedor</th><th>Observação</th></tr></thead><tbody>')
        for name, qty, who, obs in items:
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td>%s</td></tr>' % (esc(name), esc(qty), esc(who), esc(obs)))
        A('</tbody></table></div>')
    A('    </section>')

    A('    <section id="explodida">\n      <p class="kicker">3 · Vista explodida</p>\n      <h2>Da placa aos knobs</h2>')
    A('      <p class="sub">As peças em ordem de baixo para cima. O módulo fica sob a placa.</p>')
    w, hh = SIZES["lite_explodido"]
    A('      <div class="exploded"><a href="img/lite_explodido.jpg"><img src="img/lite_explodido.jpg" width="%d" height="%d" alt="Vista explodida da placa do Lite com as 9 peças numeradas." loading="lazy" style="width:100%%;height:auto;display:block;border-radius:6px" /></a>' % (w, hh))
    for k, (x, y) in PINS.items():
        A('<span class="pin" style="left:%.2f%%;top:%.2f%%" aria-hidden="true">%s</span>' % (x, y, k))
    A('</div>\n      <ol class="legend">')
    for n, s in EXPLODED:
        A('<li><div>%s<br /><span>%s</span></div></li>' % (esc(n), esc(s)))
    A('      </ol>\n    </section>')

    A('    <section id="montagem">\n      <p class="kicker">4 · Montagem em casa</p>\n      <h2>Sete passos, com solda fina</h2>')
    A('      <p class="sub">Em cada figura, o que é novo no passo está em cor e o que já estava montado, esmaecido. A V2 pedia só dois fios de solda; o Lite pede as 11 peças do topo, e é aí que está a dificuldade.</p>')
    A('      <h3>Ferramentas</h3>')
    A('      <ul><li>Ferro de solda de ponta fina e solda de 0,5 mm; fluxo em gel ou caneta; malha dessoldadora; pinça fina; lupa ou microscópio.</li><li>Opcional, mas ajuda no USB-C: estação de ar quente.</li><li>Multímetro; chave Phillips pequena; alicate de bico fino.</li></ul>')
    for i, (fig, title, texts, new) in enumerate(STEPS, 1):
        A('      <article class="step"><figure>%s</figure><div><h3><span class="num">%d</span>%s</h3>%s<p class="new">Novo neste passo: %s.</p></div></article>'
          % (imgtag(fig, "Passo %d: %s" % (i, title)), i, esc(title), "".join("<p>%s</p>" % esc(t) for t in texts), esc(new)))
    A('      <h3>Primeira ligação</h3>')
    A('      <p>O firmware da Student V2 ainda não existe: teclas, som e microfone só poderão ser testados depois dele. Até lá, o que se confere é a eletrônica: sem curto na entrada, módulo reconhecido pelo computador e tensões no lugar.</p>')
    A('    </section>')

    A('    <section id="orcamento">\n      <p class="kicker">5 · Orçamento</p>\n      <h2>Quanto custa o Lite</h2>')
    A('      <p class="sub">Um instrumento, pedindo o mínimo à JLCPCB (5 placas, 2 montadas). Faixas em dólares; libras a £ 1 = US$ %s (suposição). Fora: frete, IVA e impostos.</p>' % ("%.2f" % RATE).replace(".", ","))
    A('      <div class="tablewrap"><table><thead><tr><th>Pedido</th><th>Fornecedor</th><th class="num">Valor</th></tr></thead><tbody>')
    for name, who, l, hgh, _it in rows:
        A('<tr><td>%s</td><td>%s</td><td class="num">%s</td></tr>' % (esc(name), esc(who), esc(rng(l, hgh))))
    A('<tr class="total"><td colspan="2">Total do Student Lite</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
    A('</tbody></table></div>')
    A('      <p class="note">Opcionais, fora do total: %s.</p>' % esc("; ".join("%s, %s" % (o[0], rng(o[1], o[2])) for o in OPTIONAL)))
    A('      <h3>Lite contra V2</h3>')
    A('      <div class="tablewrap"><table><thead><tr><th>Versão</th><th>O que inclui</th><th class="num">Total</th></tr></thead><tbody>')
    A('<tr><td>Student V2</td><td>placa montada dos dois lados, tela, case impresso, botões, acabamento</td><td class="num">%s</td></tr>' % esc(rng(v2lo, v2hi)))
    A('<tr><td>Student Lite</td><td>placa montada só no fundo, sem tela, sem case, topo soldado em casa</td><td class="num">%s</td></tr>' % esc(rng(lo, hi)))
    A('<tr class="sub"><td colspan="2">Diferença (faixas inteiras, de baixo e de cima)</td><td class="num">− %s a − %s</td></tr>' % (V2.usd(v2lo - lo), V2.usd(v2hi - hi).replace("US$ ", "")))
    A('</tbody></table></div>')
    A('      <p class="note">O que o Lite corta: %s.</p>' % esc("; ".join(c[0] for c in CUT)))
    A('      <h3>Detalhe por pedido</h3>')
    for name, who, l, hgh, items in rows:
        A('      <div class="tablewrap"><table><thead><tr><th colspan="5">%s · %s</th></tr><tr><th>Item</th><th>Qtd</th><th>Observação</th><th>Fonte do preço</th><th class="num">Valor</th></tr></thead><tbody>' % (esc(name), esc(who)))
        for _a, item, qty, obs, il, ih, _c, tag in items:
            A('<tr><td>%s</td><td class="qty">%s</td><td>%s</td><td><span class="tag%s">%s</span></td><td class="num">%s</td></tr>'
              % (esc(item), esc(qty), esc(obs), "" if tag == "visto" else " est", "preço visto" if tag == "visto" else "estimativa", esc(rng(il, ih))))
        A('<tr class="sub"><td colspan="4">Subtotal</td><td class="num">%s</td></tr></tbody></table></div>' % esc(rng(l, hgh)))
    A('      <h3>Como ler estes números</h3>')
    A('''      <ul>
        <li><b>Preço visto</b> é o de uma página de loja de 15 de novembro de 2026; <b>estimativa</b> é uma ordem de grandeza sem cotação.</li>
        <li>Os preços da JLCPCB derivam da estimativa da V2: a preparação cai porque a montagem é de um lado só, as taxas por peça estendida caem porque saíram 6 tipos (encoder, USB-C, jack, TVS, ESD, JST SH), e as peças caem com elas. <b>Só a cotação real, com os arquivos enviados, confirma.</b> Se a placa se enquadrar na montagem econômica de um lado só da JLCPCB, o valor pode ser ainda menor: não foi verificado.</li>
        <li>A LCSC é um pedido à parte, com frete próprio; é o que mais pesa no lado “montar em casa” (US$ %s).</li>
        <li>Sem caixa acústica, o alto-falante soa pouco: serve para conferir que há som, não para avaliar o timbre.</li>
      </ul>''' % esc(rng(sum(i[4] for i in rows[2][4]), sum(i[5] for i in rows[2][4])).replace("US$ ", "")))
    A('    </section>')
    A('''    <footer>
      <p>Rascunho de avaliação de custo, fora do mapa do site e dos buscadores. Arquivos em <code>etutti/hardware/student_lite/</code> do repositório <a href="https://github.com/dataehora/beatconfused">dataehora/beatconfused</a>; a versão completa está em <a href="/etutti/studentV2/">/etutti/studentV2/</a>.</p>
      <p><a href="/">beatconfused.com</a></p>
    </footer>
  </main>
</body>
</html>''')
    return "\n".join(h), (lo, hi), (v2lo, v2hi), [(r[0], r[2], r[3]) for r in rows]


def main():
    os.makedirs(OUT, exist_ok=True)
    page, tot, v2, rows = build()
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
    open(os.path.join(OUT, "styles.css"), "w", encoding="utf-8", newline="\n").write(V2.CSS)
    print("Lite", [round(v) for v in tot], "V2", [round(v) for v in v2])
    for r in rows:
        print("  %-45s %6.0f %6.0f" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
