#!/usr/bin/env python3
"""Liebling: comparação das versões A (MEMS), B (eletreto Ø9,7) e C (diafragma grande Ø16).
Escreve liebling_r3_comparacao.html."""
import os

import proto_r3 as P
from proto_b import chains, box, arrow  # noqa: F401

CSS = P.CSS + """
.ab td:first-child{color:var(--mut);width:18%}.ab td.a{color:#9ad9ff}.ab td.b{color:#ffd9a0}.ab td.c{color:#b9f0b0}
.verdict{background:#1c2430;border-left:3px solid #59a8ff;padding:12px 14px;border-radius:8px;margin:10px 0}
.q{color:#ffb4a0}
"""


def chain_c():
    d = '<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#888"/></marker></defs>'
    s = d + '<text x="6" y="16" font-size="13" fill="#b9f0b0" font-weight="700">C · cápsulas de diafragma grande (variante)</text>'
    s += '<rect x="2" y="22" width="334" height="56" rx="8" fill="#1d3a1d" opacity=".35" stroke="#5fa35f" stroke-dasharray="4 3"/>'
    s += '<text x="330" y="90" font-size="10.5" fill="#8fd18f" text-anchor="end">zona analógica (ruído = problema)</text>'
    s += box(6, 28, 100, 44, "2 × Ø16 mm", "#1d3a1d", "#5fa35f", "back-electret + JFET")
    s += arrow(106, 50, 128)
    s += box(128, 28, 100, 44, "polarização", "#262630", "#555", "+ filtro RC")
    s += arrow(228, 50, 248)
    s += box(248, 28, 82, 44, "ADC", "#262630", "#555", "PCM1863")
    s += arrow(336, 50, 366)
    s += box(366, 28, 90, 44, "RP2040", "#262630", "#555", "ganho · medidor")
    s += arrow(456, 50, 484)
    s += box(484, 28, 70, 44, "USB-C", "#262630", "#555")
    return '<svg viewBox="0 0 560 100" xmlns="http://www.w3.org/2000/svg">%s</svg>' % s


def page():
    vb = "-9 -9 108 46"
    P.set_size(72, 22, 6.5)
    plan_a = P.svg("-9 -12 96 46", state="ok", dims=True)
    plan_b = P.svg("-9 -12 96 46", state="ok", dims=True, mic="cap")
    iso_a, use_a = P.iso_flat("ok"), P.iso_use("ok")
    iso_b, use_b = P.iso_flat("ok", mic="cap"), P.iso_use("ok", mic="cap")
    P.set_size(84, 24, 10.5)
    plan_c = P.svg(vb, state="ok", dims=True, mic="ldc")
    iso_c, use_c = P.iso_flat("ok", mic="ldc"), P.iso_use("ok", mic="ldc")
    ca, cb = chains()
    cc = chain_c()
    rows = [
        ("Placa", "72 × 22 mm", "72 × 22 mm", "<b>84 × 24 mm</b> (capsulas Ø16 pedem mais largura; 6 mm de cada lado além do celular)"),
        ("Altura com espuma", "~ 4 mm", "~ 9 mm", "~ 12 mm"),
        ("Ruído próprio (dB SPL A)", "≈ 22 <i>(ficha)</i>", "≈ 15 a 19,5 <i>(ficha + conta)</i>", "<span class=q>hipótese: 8 a 16</span> (nenhuma ficha achada)"),
        ("Sobrecarga (AOP)", "128 dB SPL <i>(ficha)</i>", "119 a 122 <i>(ficha)</i>", "<span class=q>120 a 128, limitada pelo JFET com 3,3-5 V</span>; o catálogo diz \"130\" sem dizer o que é"),
        ("Graves", "queda em 11 Hz <i>(ficha)</i>", "<b>não confirmado</b> (60 Hz na ficha de loja)", "<span class=q>20 Hz no catálogo, genérico</span>; omni plausível, cardioide tem efeito de proximidade"),
        ("Padrão polar", "omni", "omni", "<b>omni ou cardioide</b> (sob encomenda): o cardioide reduz vazamento da banda e da sala, mas levanta os graves de perto"),
        ("Casamento L × R", "± 1 dB <i>(típico, a conferir)</i>", "± 3 dB", "sensibilidade \"customizada\": pareamento e calibração obrigatórios"),
        ("Montagem", "SMD, a JLCPCB monta", "cápsulas soldadas à mão", "cápsulas soldadas à mão; 2 furos de ventilação atrás (cardioide)"),
        ("Documentação do componente", "ficha Infineon, aberta", "ficha Primo, aberta", "<b>só catálogo de fabricante, sem ficha por tamanho, sem SNR, sem preço</b>"),
        ("Custo extra por placa", "referência", "≈ + US$ 15 a 25 <i>(est.)</i>", "<span class=q>a cotar</span>; estimativa de trabalho + US$ 25 a 45"),
        ("Pronto para a Fase 1?", "sim", "sim, com ressalvas", "<b>não</b>: depende de ficha e amostra do fabricante (pedir ficha não é comprar)"),
    ]
    tr = "".join('<tr><td>%s</td><td class="a">%s</td><td class="b">%s</td><td class="c">%s</td></tr>' % r for r in rows)
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Liebling · comparação A B C</title><style>%s</style></head><body><main>
<h1>Liebling<small>COMPARAÇÃO · A · B · C</small></h1>
<p class="sub">A = MEMS (versão da SPEC). B = cápsulas de eletreto Ø9,7 mm. C = cápsulas de diafragma maior (Ø16 mm). Mesma interface em todas. Em itálico, o que vem de ficha aberta; o que está marcado como hipótese é conta minha, sem ficha. Visto em 28 nov 2026.</p>
<h2>Plantas</h2>
<div class="card"><h3>A · MEMS</h3>%s</div>
<div class="card"><h3>B · eletreto Ø9,7</h3>%s</div>
<div class="card"><h3>C · diafragma Ø16, placa 84 × 24</h3>%s</div>
<h2>Isométricos</h2>
<div class="grid g3"><div class="card">%s</div><div class="card">%s</div><div class="card">%s</div></div>
<div class="grid g3"><div class="card">%s</div><div class="card">%s</div><div class="card">%s</div></div>
<h2>Cadeia do sinal</h2>
<div class="card">%s</div><div class="card">%s</div><div class="card">%s</div>
<h2>A × B × C</h2>
<div class="card"><table class="ab"><tr><th></th><th>A · MEMS</th><th>B · eletreto Ø9,7</th><th>C · diafragma Ø16</th></tr>%s</table></div>
<h2>O que achei para a C</h2>
<div class="card"><table><tr><th>Candidato</th><th>O que diz a fonte</th><th>Serve para graves de estúdio?</th></tr>
<tr><td>Cápsulas back-electret de 14 a 25,4 mm (catálogo de fabricante, 797 Audio)</td><td>omni, cardioide ou hipercardioide, com ou sem JFET, Mylar de 3 ou 6 µm; resposta "20-20000 Hz" e máx. 130 dB SPL, <b>genéricos</b>; sensibilidade e capacitância "sob medida"; <b>sem SNR, sem ficha por tamanho, sem preço</b></td><td>talvez; <b>não dá para afirmar</b> sem a curva medida de 20 a 200 Hz</td></tr>
<tr><td>Elementos de 14 e 16 mm de outro fabricante</td><td>50 Hz a 20 kHz e SNR acima de 58 dB (anúncio)</td><td><b>não</b>: pior que o MEMS</td></tr>
<tr><td>Primo EM297M1Z1 (cardioide, ~10 mm)</td><td>SNR 78 a 79 dB, 60 Hz a 20 kHz (ficha Primo e loja)</td><td>não é diafragma grande, e a faixa começa em 60 Hz</td></tr>
<tr><td>Condensador verdadeiro de 1" (estúdio)</td><td>precisa de polarização de 60 a 80 V; no estúdio vem do phantom de 48 V</td><td>é o que mais se aproxima do estúdio, mas <b>não cabe num microfone alimentado só pelo USB</b> sem um conversor elevador, e o conversor mete ruído</td></tr></table></div>
<h2>Leitura honesta</h2>
<div class="verdict"><p><b>Para graves, hoje só a A tem prova na ficha</b> (queda em 11 Hz, 128 dB SPL, número de fabricante aberto). Não achei <b>nenhum componente de diafragma grande, comprável, com ficha de verdade</b> que mostre graves e ruído de estúdio. Os fabricantes de cápsula vendem por consulta e "sob medida".</p>
<p>A C pode ser a que mais se aproxima de estúdio, porque diafragma maior dá mais sinal e deixa o ruído da eletrônica pesar menos, e o cardioide resolve o vazamento da banda. Mas é <b>hipótese</b>: precisa de ficha, de amostra medida e de um caminho analógico mais exigente, numa placa maior (84 × 24 mm) e mais alta (12 mm), mais pesada na alavanca do plugue. O custo-benefício depende de uma medição que ainda não existe.</p>
<p><b>Proposta:</b> seguir a A como base. Para a C, a Fase 1 faz só <b>pedir ficha e curva de graves</b> a 2 ou 3 fabricantes (lista na SPEC §9); se vierem números bons (≤ 12 dB(A), −3 dB em 20 Hz, 120 dB SPL ou mais), a C vira uma segunda versão na Fase 2, com amostras.</p></div>
</main></body></html>""" % (CSS, plan_a, plan_b, plan_c, iso_a, iso_b, iso_c, use_a, use_b, use_c, ca, cb, cc, tr)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "liebling_r3_comparacao.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page())
    print(path)
