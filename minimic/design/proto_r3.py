#!/usr/bin/env python3
"""Liebling (Batschauer) - protótipo visual R3MIC.
Placa 72 x 22 mm, plugue USB-C no centro do lado maior (a placa é a continuação do corpo do celular),
barra de nível (feedback, 12 LEDs coloridos) em cima, barra de ganho (15 LEDs brancos, 2 botões) embaixo,
par estéreo de microfones nas pontas. Só biblioteca padrão. Escreve liebling_r3.html.
Planta: origem no canto superior esquerdo da placa; o lado do plugue é y = 0."""
import math
import os

from proto_r2 import Iso, CSS as CSS2  # noqa: E402  (mesma pasta)

W, D, T = 72.0, 22.0, 1.2
G, Y, R, B = "#3ddc6a", "#ffd23f", "#ff4a3d", "#4aa8ff"
GOLD = "#c9a24a"
LEVELS = [(-42, G), (-36, G), (-30, G), (-24, G), (-20, G), (-16, G), (-12, Y), (-9, Y), (-6, Y), (-3, R), (0, R)]
MEANING = ["baixo", "baixo", "baixo", "baixo", "bom", "bom", "forte (picos do bayan aqui)", "forte", "forte", "limite", "no teto"]
FB_Y, GAIN_Y = 6.3, 15.5
FB_X = [15.9 + i * 3.65 for i in range(12)]        # 11 níveis + SAT
GAIN_X = [21.5 + i * (29.0 / 14) for i in range(15)]  # 0 .. +42 dB em passos de 3 dB
MIC_X = (6.5, 65.5)
MIC_Y = 11.0
OUTLINE = [(1.5, 0), (70.5, 0), (72, 1.5), (72, 19), (69, 22), (3, 22), (0, 19), (0, 1.5)]
GOLD_LINE = "M 30.6 .8 L 1.9 .8 L .8 1.9 L .8 18.6 L 3.4 21.2 L 68.6 21.2 L 71.2 18.6 L 71.2 1.9 L 70.1 .8 L 41.4 .8"


def outline_pts():
    return " ".join("%s,%s" % p for p in OUTLINE)


def plan(state="ok", gain=6, foam=True, plug=True, callouts=False, dims=False, only_outline=None, mic="mems"):
    """state: 'ok' | 'hot' | 'sat'. gain: posição 0..14 (0,5 = meio passo: acende dois LEDs)."""
    if only_outline:
        return '<polygon points="%s" fill="%s"/>' % (outline_pts(), only_outline)
    o = []
    if plug:
        o.append('<rect x="31.53" y="-6.65" width="8.94" height="9.15" rx="1.3" fill="#c3c7ce" stroke="#6b7078" stroke-width=".18"/>')
        o.append('<rect x="32.6" y="-5.6" width="6.8" height="7" rx=".9" fill="none" stroke="#8c919a" stroke-width=".15"/>')
    o.append('<polygon points="%s" fill="#17171c" stroke="#3a3a44" stroke-width=".15"/>' % outline_pts())
    o.append('<path d="%s" fill="none" stroke="%s" stroke-width=".22"/>' % (GOLD_LINE, GOLD))
    o.append('<rect x="31.5" y="0" width="9" height="2.5" fill="%s" opacity=".7"/>' % GOLD)
    # --- medidor (feedback): colorido e brilhante
    lit_to = {"ok": -16, "hot": -3, "sat": 0}[state]
    o.append('<text x="14.3" y="2.3" font-size=".95" fill="#9a9aa6" letter-spacing=".15">LEVEL  dBFS</text>')
    for i in range(12):
        x = FB_X[i]
        if i < 11:
            db, col = LEVELS[i]
            on = db <= lit_to
            blink = state == "sat" and col == R
            lab = str(db)
            w, h = 2.0, 1.2
        else:
            db, col = 99, B
            on = state == "sat"
            blink = on
            lab = "SAT"
            w, h = 3.0, 1.6
        if on:
            o.append('<circle cx="%.2f" cy="%s" r="%s" fill="%s" opacity=".30"/>' % (x, FB_Y, 2.6 if i == 11 else 1.9, col))
        o.append('<rect x="%.2f" y="%.2f" width="%s" height="%s" rx=".2" fill="%s" opacity="%s" %s/>' % (
            x - w / 2, FB_Y - h / 2, w, h, col, "1" if on else ".26",
            'stroke="#fff" stroke-width=".14"' if (on and blink) else ""))
        o.append('<text x="%.2f" y="3.9" font-size="%s" fill="%s" text-anchor="middle" %s>%s</text>' % (
            x, 1.2 if i == 11 else .95, B if i == 11 else "#b5b5c0", 'font-weight="700"' if i == 11 else "", lab))
    # --- identidade
    o.append('<text x="14.5" y="12.7" font-size="3" fill="%s" font-family="Georgia,serif" font-style="italic">Liebling</text>' % GOLD)
    o.append('<text x="14.7" y="13.9" font-size=".9" fill="#9a9aa6" letter-spacing=".3">BATSCHAUER</text>')
    # --- barra de ganho: branca e discreta
    for i in range(15):
        x = GAIN_X[i]
        lit = (abs(i - gain) < 0.51)
        o.append('<rect x="%.2f" y="%.2f" width=".8" height="1.6" rx=".15" fill="#f1f1ea" opacity="%s"/>' % (x - .4, GAIN_Y - .8, ".95" if lit else ".22"))
        if lit:
            o.append('<circle cx="%.2f" cy="%s" r="1.1" fill="#f1f1ea" opacity=".14"/>' % (x, GAIN_Y))
    for i, t in ((0, "0"), (4, "+12"), (8, "+24"), (12, "+36"), (14, "+42")):
        o.append('<text x="%.2f" y="18.7" font-size=".95" fill="#9a9aa6" text-anchor="middle">%s</text>' % (GAIN_X[i], t))
    o.append('<text x="36" y="13.5" font-size=".95" fill="#9a9aa6" text-anchor="middle" letter-spacing=".25">GAIN dB</text>')
    for bx, sym in ((16, "−"), (56, "+")):
        o.append('<rect x="%s" y="14.2" width="3.4" height="2.6" rx=".4" fill="#8d929c" stroke="#d0d4da" stroke-width=".12"/>' % (bx - 1.7))
        o.append('<circle cx="%s" cy="15.5" r=".85" fill="#5a5e66"/>' % bx)
        o.append('<text x="%s" y="19.3" font-size="1.7" fill="#e8e8ee" text-anchor="middle" font-weight="700">%s</text>' % (bx, sym))
    # --- par estéreo
    for mx, lab in zip(MIC_X, "LR"):
        if mic == "cap":  # cápsula de eletreto Ø9,7 (versão B)
            o.append('<circle cx="%s" cy="%s" r="5.3" fill="none" stroke="%s" stroke-width=".3"/>' % (mx, MIC_Y, GOLD))
            o.append('<circle cx="%s" cy="%s" r="4.85" fill="#aeb3bb" stroke="#e6e9ee" stroke-width=".15"/>' % (mx, MIC_Y))
            o.append('<circle cx="%s" cy="%s" r="3.7" fill="#2a2c31"/>' % (mx, MIC_Y))
            for k in range(7):
                for j in range(7):
                    px, py = (k - 3) * .8, (j - 3) * .8
                    if px * px + py * py < 3.3 ** 2:
                        o.append('<circle cx="%.2f" cy="%.2f" r=".18" fill="#5b5f68"/>' % (mx + px, MIC_Y + py))
            if foam:
                o.append('<circle cx="%s" cy="%s" r="6.5" fill="#46464c" opacity=".5" stroke="#cfcfd6" stroke-width=".15" stroke-dasharray=".7 .5"/>' % (mx, MIC_Y))
            o.append('<text x="%s" y="19.9" font-size="1.4" fill="#e8e8ee" text-anchor="middle" font-weight="700">%s</text>' % (mx, lab))
            continue
        o.append('<circle cx="%s" cy="%s" r="2.4" fill="none" stroke="%s" stroke-width=".3"/>' % (mx, MIC_Y, GOLD))
        o.append('<rect x="%s" y="%s" width="4" height="3" rx=".3" fill="#cfd2d8" stroke="#6b7078" stroke-width=".12"/>' % (mx - 2, MIC_Y - 1.5))
        o.append('<circle cx="%s" cy="%s" r=".9" fill="#050506" stroke="#fff" stroke-width=".1"/>' % (mx, MIC_Y))
        if foam:
            o.append('<circle cx="%s" cy="%s" r="5" fill="#46464c" opacity=".8" stroke="#cfcfd6" stroke-width=".15" stroke-dasharray=".7 .5"/>' % (mx, MIC_Y))
            for k in range(12):
                a = k * 2.1
                o.append('<circle cx="%.2f" cy="%.2f" r=".26" fill="#2a2a2e"/>' % (mx + 3.3 * math.cos(a) * (0.4 + (k % 3) * .3), MIC_Y + 3.3 * math.sin(a) * (0.45 + (k % 4) * .2)))
        o.append('<text x="%s" y="19.9" font-size="1.4" fill="#e8e8ee" text-anchor="middle" font-weight="700">%s</text>' % (mx, lab))
    if callouts:
        pts = [(1, 50, -9.5, 40.0, -4.2), (2, 22, -9.5, 22, 2.9), (3, 63, -9.5, 56.05, 5.1),
               (7, 10, 27.8, 22, 12.4), (5, 24, 27.8, 16, 17.2), (4, 38, 27.8, 38, 19.0), (6, 60, 27.8, 65.5, 16.3)]
        for n, cx, cy, tx, ty in pts:
            o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#59a8ff" stroke-width=".15"/>' % (cx, cy, tx, ty))
            o.append('<circle cx="%s" cy="%s" r="1.35" fill="#59a8ff"/>' % (cx, cy))
            o.append('<text x="%s" y="%s" font-size="1.6" fill="#0b1118" text-anchor="middle" font-weight="700">%d</text>' % (cx, cy + .58, n))
    if dims:
        d = "#8a8a96"
        o.append('<line x1="0" y1="31.4" x2="72" y2="31.4" stroke="%s" stroke-width=".15"/><line x1="0" y1="30.7" x2="0" y2="32.1" stroke="%s" stroke-width=".15"/><line x1="72" y1="30.7" x2="72" y2="32.1" stroke="%s" stroke-width=".15"/>' % (d, d, d))
        o.append('<text x="36" y="30.8" font-size="1.3" fill="#c8c8d2" text-anchor="middle">72 mm</text>')
        o.append('<line x1="77" y1="0" x2="77" y2="22" stroke="%s" stroke-width=".15"/><line x1="76.3" y1="0" x2="77.7" y2="0" stroke="%s" stroke-width=".15"/><line x1="76.3" y1="22" x2="77.7" y2="22" stroke="%s" stroke-width=".15"/>' % (d, d, d))
        o.append('<text x="80.4" y="11.5" font-size="1.3" fill="#c8c8d2" text-anchor="middle">22 mm</text>')
        o.append('<text x="36" y="25.4" font-size="1.0" fill="#8a8a96" text-anchor="middle">microfones a 59 mm um do outro</text>')
    return "".join(o)


def svg(vb, **kw):
    return '<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg" role="img">%s</svg>' % (vb, plan(**kw))


# --------------------------------------------------------------- isométricos
class Iso3(Iso):
    def plan_on(self, world, **kw):
        for cu, cv in ((W, 0), (0, D), (W, D)):
            self.P(*world(cu, cv))  # só para o enquadramento
        p0, pa, pb = self.P(*world(0, 0)), self.P(*world(1, 0)), self.P(*world(0, 1))
        m = (pa[0] - p0[0], pa[1] - p0[1], pb[0] - p0[0], pb[1] - p0[1], p0[0], p0[1])
        self.out.append('<g transform="matrix(%.4f %.4f %.4f %.4f %.2f %.2f)">%s</g>' % (m + (plan(**kw),)))


def components(state="ok", gain=6, mic="mems"):
    """(u0,u1,v0,v1,h,topo,lado,frente) de cada peça sobre a placa, em mm da planta."""
    items = []
    lit_to = {"ok": -16, "hot": -3, "sat": 0}[state]
    for i in range(12):
        x = FB_X[i]
        if i < 11:
            db, col = LEVELS[i]
            on, w, h, hh = db <= lit_to, 2.0, 1.2, .6
        else:
            col, on, w, h, hh = B, state == "sat", 3.0, 1.6, .7
        items.append((x - w / 2, x + w / 2, FB_Y - h / 2, FB_Y + h / 2, hh, col if on else "#3b3b44", "#202026", col if on else "#2a2a30"))
    for i in range(15):
        x = GAIN_X[i]
        on = abs(i - gain) < .51
        items.append((x - .4, x + .4, GAIN_Y - .8, GAIN_Y + .8, .5, "#f1f1ea" if on else "#55555c", "#303036", "#44444a"))
    for bx in (16, 56):
        items.append((bx - 1.7, bx + 1.7, 14.2, 16.8, 1.6, "#9aa0a8", "#6f747c", "#80858d"))
    if mic == "mems":
        for mx in MIC_X:
            items.append((mx - 2, mx + 2, MIC_Y - 1.5, MIC_Y + 1.5, 1.0, "#cfd2d8", "#9ea3ab", "#b2b6be"))
    return items


def mic_stack(mic):
    """Cilindros (raio, altura inicial, final, topo, lado) sobre cada furo/cápsula."""
    if mic == "cap":
        return [(4.85, 0, 6.5, "#2a2c31", "#aeb3bb"), (5.7, 6.5, 9.0, "#55555c", "#3a3a40")]
    return [(5.0, 0, 3.0, "#55555c", "#3a3a40")]


def iso_flat(state="ok", mic="mems"):
    iso = Iso3(7.6)
    wd = lambda u, v, w=0: (u, v, w)
    # plugue (atrás da placa, saindo do lado y = 0)
    iso.box(31.53, 40.47, -6.65, 2.5, T / 2 - 1.63, T / 2 + 1.63, "#c8ccd3", "#9ea3ab", "#b2b6be")
    for k in range(6):
        iso.plan_on(lambda u, v, z=T * k / 6: (u, v, z), only_outline="#0d0d10")
    iso.plan_on(lambda u, v: (u, v, T), foam=False, plug=False, state=state, mic=mic)
    items = sorted(components(state, mic=mic), key=lambda c: (c[0] + c[1] + c[2] + c[3]))
    for u0, u1, v0, v1, h, top, side, front in items:
        iso.box(u0, u1, v0, v1, T, T + h, top, side, front, stroke="#111", sw=.2)
    for mx in MIC_X:
        for r, h0, h1, top, side in mic_stack(mic):
            iso.cyl(mx, MIC_Y, T + h0, T + h1, r, top, side)
    return iso.svg()


def iso_use(state="ok", mic="mems"):
    iso = Iso3(5.6)
    PH_W, PH_T, PH_H = 72.0, 8.5, 22.0
    xc, y_mid, gap = 36.0, 4.25, 0.8
    iso.box(0, PH_W, 0, PH_T, 0, PH_H, "#34373e", "url(#fade2)", "url(#fade)", stroke="#0b0b0d", sw=.5)
    P = iso.P
    iso.poly([P(3, PH_T, 3), P(PH_W - 3, PH_T, 3), P(PH_W - 3, PH_T, PH_H), P(3, PH_T, PH_H)], "url(#fade)", "#2a2d33", .4, .9)
    iso.box(xc - 4.47, xc + 4.47, y_mid - 1.63, y_mid + 1.63, -gap, 0, "#c8ccd3", "#9ea3ab", "#b2b6be", stroke="#222", sw=.3)
    y0 = y_mid - T / 2
    ytop = y_mid + T / 2
    X0 = xc - W / 2

    def wd(u, v, w=0.0):
        return (X0 + u, y0 + w, -gap - v)

    # corpo da placa: 6 cópias do contorno em y crescente, a última com a planta
    for k in range(6):
        iso.plan_on(lambda u, v, w=T * k / 6: wd(u, v, w), only_outline="#0d0d10")
    iso.plan_on(lambda u, v: wd(u, v, T), foam=False, plug=False, state=state, mic=mic)

    def pbox(u0, u1, v0, v1, h, top, side, front):
        x0, x1 = X0 + u0, X0 + u1
        z0, z1 = -gap - v1, -gap - v0
        iso.box(x0, x1, ytop, ytop + h, z0, z1, top, side, front, stroke="#111", sw=.2)

    # em pé, a face +y é a "tampa" (a que o músico vê): o rótulo da cor vai na frente
    for u0, u1, v0, v1, h, top, side, front in sorted(components(state, mic=mic), key=lambda c: c[0] + c[1]):
        pbox(u0, u1, v0, v1, h, front, side, front)
    for mx in MIC_X:
        cx, cz = X0 + mx, -gap - MIC_Y
        n = 24
        for r, h0, h1, top, side in mic_stack(mic):
            pf = [iso.P(cx + r * math.cos(t * 2 * math.pi / n), ytop + h1, cz + r * math.sin(t * 2 * math.pi / n)) for t in range(n + 1)]
            pb = [iso.P(cx + r * math.cos(t * 2 * math.pi / n), ytop + h0, cz + r * math.sin(t * 2 * math.pi / n)) for t in range(n + 1)]
            iso.poly(pb, side, "#111", .3)
            for t in range(n):
                iso.poly([pb[t], pb[t + 1], pf[t + 1], pf[t]], side, side, .3)
            iso.poly(pf, top, "#111", .4)
    return iso.svg()


# ------------------------------------------------------------------- página
CSS = CSS2 + """
table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{padding:5px 8px;border-bottom:1px solid #2a2a34;text-align:left}
th{color:var(--mut);font-weight:600}.dot{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px}
.warn{border-left:3px solid #4aa8ff;padding-left:12px}
"""


def page():
    legend = [
        "Plugue USB-C macho no <b>centro do lado maior</b>: a placa é a continuação do corpo do celular.",
        "Barra de <b>nível</b>: 11 LEDs verde/amarelo/vermelho, brilhantes, legíveis de longe.",
        "<b>SAT</b>: o degrau logo depois do vermelho. Azul, piscando; o texto \"SAT\" na serigrafia basta.",
        "Barra de <b>ganho</b>: 15 LEDs brancos e discretos; o aceso mostra a posição (0 a +42 dB).",
        "Botões <b>−</b> e <b>+</b> nas pontas da barra de ganho.",
        "<b>Par estéreo</b> (L e R), a 59 mm um do outro, cada um com espuma Ø10.",
        "Marca em cobre dourado (ENIG), contorno dourado e chanfros: o desenho da PCB é o acabamento. Sem caixa.",
    ]
    main = svg("-9 -12 96 46", state="ok", callouts=True, dims=True)
    strips = ""
    for st, tit, txt in (("ok", "Voz/instrumento em bom nível", "Verde aceso até −16 dBFS: há margem. Amarelo é o alvo dos picos do bayan."),
                         ("hot", "Perto do limite", "Chegou ao primeiro vermelho (−3): baixe um passo de ganho."),
                         ("sat", "Saturou", "Vermelhos e SAT piscam juntos e o SAT acende azul: houve distorção. Baixe o ganho agora.")):
        strips += '<div class="card opt">%s<h3>%s</h3><p>%s</p></div>' % (svg("13 0 47 10.4", state=st, foam=False, plug=False), tit, txt)
    gains = ""
    for g, tit, txt in ((0, "0 dB", "Mínimo. Um LED aceso."),
                        (6, "+18 dB", "Um toque em + sobe 1,5 dB (meio LED); o LED aceso mostra a posição."),
                        (9.5, "+28,5 dB", "Meio passo: dois LEDs vizinhos acesos.")):
        gains += '<div class="card opt">%s<h3>%s</h3><p>%s</p></div>' % (svg("13 12.2 47 8.6", gain=g, foam=False, plug=False), tit, txt)
    rows = "".join('<tr><td><span class="dot" style="background:%s"></span>%s dBFS</td><td>%s</td></tr>' % (LEVELS[i][1], LEVELS[i][0], MEANING[i]) for i in range(11))
    rows += '<tr><td><span class="dot" style="background:%s"></span>SAT</td><td><b>saturou</b>: a saída chegou a 0 dBFS (cortou) ou o próprio sensor passou de ~128 dB SPL</td></tr>' % B
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Liebling · protótipo visual R3MIC</title><style>%s</style></head><body><main>
<h1>Liebling<small>BATSCHAUER · MIC USB-C ESTÉREO</small></h1>
<p class="sub">Protótipo visual da R3MIC. Placa 72 × 22 × 1,2 mm, sem caixa. Conceito: nada foi encomendado nem conferido em peça real.</p>
<h2>Planta</h2><div class="card">%s<ol class="leg">%s</ol></div>
<h2>Isométrico</h2>
<p class="sub">À esquerda, a placa; à direita, no celular em pé (selfie stick ou estante): a placa vira o queixo do celular, com os LEDs para o músico.</p>
<div class="grid g2"><div class="card">%s</div><div class="card">%s</div></div>
<h2>Medidor: escala, cor e saturação</h2>
<p class="sub">As posições de cima, da esquerda para a direita, são as da tabela; o SAT é sempre o degrau seguinte ao último vermelho.</p>
<div class="grid g3">%s</div>
<div class="card"><table><tr><th>LED</th><th>significa</th></tr>%s</table></div>
<h2>Barra de ganho (botões − e +)</h2>
<div class="grid g3">%s</div>
<p class="note">Brancos e fracos de propósito: o músico lê o ganho de perto e o medidor colorido de longe. O ganho fica guardado ao desligar.</p>
</main></body></html>""" % (CSS, main, "".join("<li>%s</li>" % t for t in legend),
                           iso_flat("ok"), iso_use("sat"), strips, rows, gains)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "liebling_r3.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page())
    print(path)
