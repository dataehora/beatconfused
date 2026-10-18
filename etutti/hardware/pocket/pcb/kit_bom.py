#!/usr/bin/env python3
"""eTuttino Pocket -- full kit BOM: everything one buys to build one Pocket
(stdlib only; eletronica owns it):

    python etutti/hardware/pocket/pcb/kit_bom.py

Writes fab/pocket_kit_bom.csv and prints the same list as a Markdown table
(pasted into ELETRONICA.md). The JLCPCB-assembled parts are listed per
board by their own BOMs (fab/pocket_bom.csv, fab/pocket_panel_bom.csv): here
they count as one line per board. "buy" = per Pocket + spares of small or
fragile parts. status "conferir" = code / stock / exact variant not checked.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fab", "pocket_kit_bom.csv")

# (group, item, part / code, per Pocket, buy, source, code at source, link, note, status)
ITEMS = [
    # ---- boards
    ("Placas", "Placa principal montada (verso: CIs, passivos, 28 TMAG5253; topo: J_PNL, J_CTL)",
     "4 camadas, 1,2 mm, Gerbers fab/pocket_gerbers.zip + BOM fab/pocket_bom.csv + CPL fab/pocket_cpl_bottom.csv / _top.csv",
     1, "5 placas / 2 montadas", "JLCPCB (PCBA)", "-", "https://jlcpcb.com/", "TMAG5253BA3IQDMRR fora do estoque da JLCPCB: consignar (linha abaixo) ou 'global sourcing'", "final"),
    ("Placas", "Sensor Hall para a placa principal (consignado na JLCPCB)", "TI TMAG5253BA3IQDMRR, X2SON-4",
     28, 40, "TI store / DigiKey / Mouser", "296-TMAG5253BA3IQDMRRCT-ND (DigiKey, conferir)", "https://www.ti.com/product/TMAG5253",
     "28 + perdas de montagem (a JLCPCB pede ~5-10 % a mais); 2 placas montadas = 56 + 6", "conferir"),
    ("Placas", "Plaquinha do painel montada (topo: USB-C, 2 x 5,1 k, ESD)",
     "2 camadas, 1,6 mm, fab/pocket_panel_gerbers.zip + fab/pocket_panel_bom.csv + fab/pocket_panel_cpl_top.csv",
     1, "5 placas / 2 montadas", "JLCPCB (PCBA)", "C165948, C25905, C2827688", "https://jlcpcb.com/", "o jack de fone é soldado em casa", "final"),
    ("Placas", "Plaquinha dos knobs (sem montagem)", "2 camadas, 1,6 mm, fab/pocket_controls_gerbers.zip",
     1, 5, "JLCPCB", "-", "https://jlcpcb.com/", "pedido mínimo de 5", "final"),
    ("Placas", "Plaquinha do volume, em pé (sem montagem)", "2 camadas, 1,6 mm, fab/pocket_pot_gerbers.zip",
     1, 5, "JLCPCB", "-", "https://jlcpcb.com/", "pedido mínimo de 5", "final"),
    ("Placas", "Plate dos switches", "FR-4 1,6 mm, desenho do design (case/out/plate.dxf)",
     1, 5, "JLCPCB (como placa sem cobre)", "-", "https://jlcpcb.com/", "arquivo do design", "conferir"),
    # ---- the stack
    ("Teensy", "Teensy 4.0", "PJRC TEENSY40 (sem pinos)", 1, 1, "PJRC / distribuidor", "TEENSY40", "https://www.pjrc.com/store/teensy40.html", "cortar a ponte VUSB-VIN antes de soldar", "final"),
    ("Teensy", "Audio Board Rev D", "PJRC TEENSY4_AUDIO", 1, 1, "PJRC / distribuidor", "TEENSY4_AUDIO", "https://www.pjrc.com/store/teensy3_audio.html", "", "final"),
    ("Teensy", "Barra de pinos extralonga 1 x 14, passo 2,54 (pilha baixa)", "header macho 1x14, pino ~20 mm (plástico ~2,5)", 2, 4, "PJRC / AliExpress / Mouser",
     "conferir", "https://www.pjrc.com/store/header_14x1_d.html", "as pernas atravessam a Audio Board e a placa principal: medir antes", "conferir"),
    # ---- keys
    ("Teclado", "Switch magnético Gateron (Hall) KS-20", "Gateron Magnetic Jade (ou equivalente KS-20 com ímã)", 28, 32, "Gateron / lojas de teclado",
     "conferir", "https://www.gateron.com/", "ímã com o norte para baixo (sensor no verso)", "conferir"),
    ("Teclado", "Capas dos botões", "impressas (arquivos do design, case/out)", 28, 32, "impressão 3D", "-", "-", "imprimir 4 de teste primeiro", "conferir"),
    # ---- controls
    ("Controles", "Potenciômetro de volume com chave", "Alps RK0971221Z05 (RK097, 10 k, chave SPST, horizontal)", 1, 2, "LCSC", "C336003",
     "https://www.lcsc.com/product-detail/C336003.html", "curva e comprimento do eixo a conferir; vem com porca M7", "conferir"),
    ("Controles", "Encoder com clique", "Alps EC11E 15 pulsos / 15 detentes, com chave, eixo D 20 mm (família EC11E1520xxx)", 1, 2,
     "Mouser / TME / Farnell", "conferir sufixo", "https://tech.alpsalpine.com/e/products/category/encorders/sub/01/series/ec11e/", "", "conferir"),
    ("Controles", "LED 3 mm bicolor vermelho/verde, catodo comum", "Kingbright WP937EGW", 1, 3, "DigiKey / Mouser", "754-1234-ND (conferir)",
     "https://www.kingbrightusa.com/images/catalog/SPEC/WP937EGW.pdf", "", "conferir"),
    ("Controles", "Espaçador do LED 3 mm, ~10 mm", "espaçador de nylon para LED 3 mm", 1, 3, "AliExpress / Mouser", "conferir", "-", "ou tubo de luz", "conferir"),
    ("Controles", "Knobs para eixo serrilhado D6", "knob ~D10-12, furo D6 serrilhado (18 dentes)", 2, 3, "AliExpress / Mouser", "conferir", "-", "ou impresso pelo design", "conferir"),
    # ---- panel
    ("Painel", "Jack de fone 3,5 com comutação na ponta", "Same Sky SJ1-3525N", 1, 2, "DigiKey / Mouser", "CP1-3525N-ND",
     "https://www.sameskydevices.com/product/resource/pdf/sj1-352xn.pdf", "manga no terra virtual (HP_VGND), nunca no GND", "final"),
    ("Painel", "Cabo micro-B 90 graus curto", "cabo USB micro-B macho 90 graus (para cortar), ~10-20 cm", 1, 2, "AliExpress / Amazon",
     "conferir", "-", "sentido do ângulo conforme a pilha (design: stack.usb_plug)", "conferir"),
    # ---- cables / connectors
    ("Cabos", "Conector da bateria na placa", "JST B3B-PH-K-S", 1, 2, "LCSC", "C131339", "https://www.lcsc.com/product-detail/C131339.html", "soldar em casa (passante)", "final"),
    ("Cabos", "Conector do alto-falante na placa", "JST B2B-PH-K-S", 1, 2, "LCSC", "C131337", "https://www.lcsc.com/product-detail/C131337.html", "soldar em casa (passante)", "conferir"),
    ("Cabos", "Rabicho da bateria", "cabo de extensão JST PH 2,0 3 vias macho-fêmea, 100 mm (cortar para ~70)", 1, 2, "AliExpress / Adafruit",
     "conferir", "-", "ligação 1:1; conferir a polaridade com o multímetro", "conferir"),
    ("Cabos", "Plugue do alto-falante", "cabo JST PH 2,0 2 vias com fios, 100 mm (fêmea PHR-2)", 1, 2, "AliExpress / LCSC", "conferir", "-", "ou PHR-2 + 2 terminais SPH crimpados", "conferir"),
    ("Cabos", "Cabo do painel", "cabo JST SH 1,0 8 vias, 100 mm, com conector numa ponta (fios soltos na outra)", 1, 2, "AliExpress / LCSC", "conferir",
     "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf", "ou com conector nas duas pontas, cortar uma", "conferir"),
    ("Cabos", "Cabo dos knobs", "cabo JST SH 1,0 10 vias, 100 mm, com conector numa ponta", 1, 2, "AliExpress / LCSC", "conferir",
     "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf", "", "conferir"),
    ("Cabos", "Fio fino de silicone", "28-30 AWG, 2 cores, 1 m", 1, 1, "qualquer", "-", "-", "fios do fone (Audio Board -> J_HP)", "final"),
    ("Cabos", "Termorretrátil fino", "D1,5 e D3", 1, 1, "qualquer", "-", "-", "", "final"),
    # ---- power / sound
    ("Energia e som", "Bateria LiPo 1S 1000-1200 mAh, PCM, NTC 10 k (3 fios), JST PH 3", "tipo 603450 (EEMB LP603450 com NTC, ou 603450 3 fios pronta)", 1, 1,
     "EEMB / eBay / Core Electronics", "CE06795 (reserva)", "https://www.eemb.com/product-252", "célula <= 7 x 36 x 58 com PCM; nunca furar, dobrar ou carregar sem o NTC", "conferir"),
    ("Energia e som", "Alto-falante 36 mm 8 ohm 2 W", "Same Sky CLS0361-L152", 1, 1, "Mouser / DigiKey / TME", "CLS0361-L152",
     "https://www.sameskydevices.com/product/resource/cls0361-l152.pdf", "", "final"),
    ("Energia e som", "Junta de espuma do alto-falante", "espuma adesiva 0,8 mm, anel D36/D30", 1, 2, "qualquer", "-", "-", "medida do design", "conferir"),
    ("Energia e som", "Espuma da bateria", "espuma EVA/PU 1-2 mm, 36 x 58", 1, 2, "qualquer", "-", "-", "sem cola na célula", "conferir"),
    # ---- screws (counts from the design's FIT_CHECK.md)
    ("Fixação", "Parafuso do fundo", "M2,5 x 8 autoatarraxante para plástico, cabeça escareada (ou inserto a quente M2,5)", 10, 12, "qualquer", "-", "-", "conferir comprimento com o design", "conferir"),
    ("Fixação", "Parafuso + porca da placa principal", "M2 x 10 cabeça panela + porca M2", 2, 4, "qualquer", "-", "-", "de baixo para cima, porca em cima da placa", "conferir"),
    ("Fixação", "Parafuso da plaquinha dos knobs", "M2 x 5 autoatarraxante para plástico", 2, 4, "qualquer", "-", "-", "", "conferir"),
    ("Fixação", "Parafuso da plaquinha do painel (furo H2)", "M2 x 6 autoatarraxante para plástico", 1, 3, "qualquer", "-", "-", "o H1 é só um pino do poste", "conferir"),
    ("Fixação", "Parafuso da tampinha da bateria", "M2 x 5 cabeça escareada, autoatarraxante", 2, 4, "qualquer", "-", "-", "", "conferir"),
    # ---- printed
    ("Impressos", "Casca de cima (tampa)", "resina (case/out/seixo_tampa.stl)", 1, 1, "JLC3DP / PCBWay / Craftcloud", "-", "-", "arquivos e materiais do design", "conferir"),
    ("Impressos", "Fundo, tampinha da bateria, fundo da caixa do alto-falante", "MJF (case/out)", 1, 1, "JLC3DP / PCBWay / Craftcloud", "-", "-", "arquivos e materiais do design", "conferir"),
    # ---- consumables
    ("Consumíveis", "Fita Kapton", "10 mm", 1, 1, "qualquer", "-", "-", "isolar o fundo do Teensy e o PCM da bateria", "final"),
    ("Consumíveis", "Cola para vedar a caixa do alto-falante", "silicone neutro ou cola E6000", 1, 1, "qualquer", "-", "-", "", "final"),
]


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["grupo", "item", "peça", "por Pocket", "comprar", "fornecedor", "código", "link", "observação", "status"])
        for row in ITEMS:
            w.writerow(row)
    print("| Grupo | Item | Peça | Por Pocket | Comprar | Fornecedor / código | Status |")
    print("|---|---|---|---:|---:|---|---|")
    for g, item, part, n, buy, src, code, link, note, st in ITEMS:
        code_s = code if code == "-" else ("[%s](%s)" % (code, link) if link.startswith("http") else code)
        if code == "-" and link.startswith("http"):
            code_s = "[link](%s)" % link
        print("| %s | %s | %s | %s | %s | %s · %s | %s |" % (g, item, part, n, buy, src, code_s, st))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
