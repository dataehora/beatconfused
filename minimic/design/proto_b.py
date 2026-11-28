#!/usr/bin/env python3
"""Liebling versão B: cápsulas de eletreto (membrana) em vez de MEMS. Escreve liebling_r3_b.html."""
import math
import os

import proto_r3 as A

CSS = A.CSS + """
.ab td:first-child{color:var(--mut);width:24%}.ab td.a{color:#9ad9ff}.ab td.b{color:#ffd9a0}
.verdict{background:#1c2430;border-left:3px solid #59a8ff;padding:12px 14px;border-radius:8px}
"""


def box(x, y, w, h, txt, fill="#262630", stroke="#555", sub=""):
    s = '<rect x="%s" y="%s" width="%s" height="%s" rx="6" fill="%s" stroke="%s"/>' % (x, y, w, h, fill, stroke)
    s += '<text x="%s" y="%s" font-size="13" fill="#e8e8ee" text-anchor="middle">%s</text>' % (x + w / 2, y + h / 2 + (-2 if sub else 5), txt)
    if sub:
        s += '<text x="%s" y="%s" font-size="10.5" fill="#9a9aa8" text-anchor="middle">%s</text>' % (x + w / 2, y + h / 2 + 13, sub)
    return s


def arrow(x0, y, x1):
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#888" stroke-width="1.5" marker-end="url(#ar)"/>' % (x0, y, x1, y)


def chains():
    d = '<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#888"/></marker></defs>'
    a = d
    a += '<text x="6" y="16" font-size="13" fill="#9ad9ff" font-weight="700">A · MEMS digital (versão atual)</text>'
    a += box(6, 28, 150, 44, "2 × IM72D128", "#1c2f3d", "#3d78a0", "PDM, 128 dB SPL")
    a += arrow(156, 50, 190)
    a += box(190, 28, 190, 44, "RP2040", "#262630", "#555", "decimação · ganho · medidor")
    a += arrow(380, 50, 414)
    a += box(414, 28, 120, 44, "USB-C", "#262630", "#555", "2 canais · 24 bits")
    b = d
    b += '<text x="6" y="16" font-size="13" fill="#ffd9a0" font-weight="700">B · cápsulas de eletreto (variante)</text>'
    b += '<rect x="2" y="22" width="334" height="56" rx="8" fill="#3a2a14" opacity=".35" stroke="#a87a3c" stroke-dasharray="4 3"/>'
    b += '<text x="330" y="90" font-size="10.5" fill="#c9a24a" text-anchor="end">zona analógica (ruído = problema)</text>'
    b += box(6, 28, 100, 44, "2 × EM272", "#3a2a14", "#a87a3c", "Ø9,7 · 80 dB")
    b += arrow(106, 50, 128)
    b += box(128, 28, 100, 44, "polarização", "#262630", "#555", "+ filtro RC")
    b += arrow(228, 50, 248)
    b += box(248, 28, 82, 44, "ADC", "#262630", "#555", "PCM1863")
    b += arrow(336, 50, 366)
    b += box(366, 28, 90, 44, "RP2040", "#262630", "#555", "ganho · medidor")
    b += arrow(456, 50, 484)
    b += box(484, 28, 70, 44, "USB-C", "#262630", "#555")
    return ('<svg viewBox="0 0 540 100" xmlns="http://www.w3.org/2000/svg">%s</svg>' % a,
            '<svg viewBox="0 0 560 100" xmlns="http://www.w3.org/2000/svg">%s</svg>' % b)


def page():
    main = A.svg("-9 -12 96 46", state="ok", callouts=False, dims=True, mic="cap")
    ca, cb = chains()
    rows = [
        ("Ruído próprio (dB SPL A)", "≈ 22", "≈ 15 a 19,5 (cápsula 14; o ADC soma ~18 com ganho 0 dB e some com ganho alto)"),
        ("Ponto de sobrecarga (AOP)", "128 dB SPL", "119 a 122 dB SPL (cápsula); com a escala do ADC em 128, o limite é a cápsula"),
        ("Graves", "queda em 11 Hz (Infineon)", "<b>não confirmado</b>: 60 Hz a 20 kHz na ficha de loja; a curva do fabricante precisa ser lida"),
        ("Casamento L × R", "± 1 dB (típico MEMS, a conferir)", "± 3 dB de sensibilidade por cápsula: pareamento ou calibração no firmware"),
        ("Montagem", "SMD, a JLCPCB monta", "cápsulas <b>soldadas à mão</b> (fios ou pinos); ADC e amplificadores SMD"),
        ("Altura sobre a placa", "~ 4 mm com a espuma", "~ 9 mm com a espuma"),
        ("Ruído de montagem", "PDM é digital, imune ao ruído do USB e dos LEDs", "caminho analógico ao lado do RP2040, do USB e do multiplexador dos LEDs: layout em estrela, filtros, LDO próprio"),
        ("Custo extra por placa", "referência", "≈ + US$ 15 a 25 (cápsulas, ADC, amplificadores, filtros; <b>estimativa</b>)"),
    ]
    tr = "".join('<tr><td>%s</td><td class="a">%s</td><td class="b">%s</td></tr>' % r for r in rows)
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Liebling · versão B</title><style>%s</style></head><body><main>
<h1>Liebling<small>VERSÃO B · CÁPSULAS DE ELETRETO</small></h1>
<p class="sub">Variante para comparar com a versão A (MEMS). Mesma placa 72 × 22 mm, mesma interface; muda o sensor e o caminho do sinal. Os números do sensor e do conversor vêm das fichas de fabricante e de loja vistas em 28 nov 2026; as contas são minhas e precisam ser conferidas.</p>
<h2>Planta (versão B)</h2><div class="card">%s<p class="note">Cápsulas Ø9,7 mm (classe EM272) nas pontas, com espuma de Ø13 mm por cima. A face de trás leva o ADC estéreo, os amplificadores e o regulador analógico.</p></div>
<h2>Isométrico</h2>
<div class="grid g2"><div class="card">%s</div><div class="card">%s</div></div>
<h2>Cadeia do sinal</h2>
<div class="card">%s</div><div class="card">%s</div>
<h2>A × B</h2>
<div class="card"><table class="ab"><tr><th></th><th>A · MEMS</th><th>B · eletreto</th></tr>%s</table></div>
<h2>Leitura honesta</h2>
<div class="verdict"><p><b>A B baixa o ruído em 2,5 a 7 dB, mas perde 6 a 9 dB de margem antes de saturar e põe os graves em dúvida.</b> Para um bayan de perto (picos de 105 a 115 dB SPL), a margem importa mais que o ruído: o ruído da sala (30 a 40 dB(A)) já cobre os dois. A B só faz sentido em estúdio muito silencioso, com a fonte a mais de ~50 cm e ganho alto, onde o ruído do sensor é o limite.</p>
<p>A B custa mais, é montada à mão, tem caminho analógico num produto com USB e LEDs ao lado, e as duas cápsulas precisam casar. Se o resultado medido da A mostrar ruído audível, a B vira o próximo passo, com cápsula de sobrecarga maior, se existir uma.</p></div>
</main></body></html>""" % (CSS, main, A.iso_flat("ok", mic="cap"), A.iso_use("ok", mic="cap"), ca, cb, tr)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "liebling_r3_b.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page())
    print(path)
