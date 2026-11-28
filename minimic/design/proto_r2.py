#!/usr/bin/env python3
"""Liebling (Batschauer) - protótipo visual R2MIC: planta, isométricos e opções.
Só biblioteca padrão. Escreve liebling_r2.html ao lado deste arquivo.
Tudo em mm; a planta tem a origem no canto superior esquerdo da placa (plugue à esquerda)."""
import math
import os

C30 = math.sqrt(3) / 2
BOARD_L, BOARD_W, BOARD_T = 60.0, 16.0, 1.0
GREEN, YELLOW, RED = "#3ddc6a", "#ffd23f", "#ff4a3d"


def led_levels(n):
    """(dBFS, cor) de cada LED, do mais fraco ao mais forte."""
    tabela = {
        8: [(-36, GREEN), (-27, GREEN), (-18, GREEN), (-12, GREEN), (-8, YELLOW), (-4, YELLOW), (-2, RED), (0, RED)],
        10: [(-42, GREEN), (-36, GREEN), (-30, GREEN), (-24, GREEN), (-18, GREEN), (-12, GREEN),
             (-9, YELLOW), (-6, YELLOW), (-3, RED), (0, RED)],
        11: [(-42, GREEN), (-36, GREEN), (-30, GREEN), (-24, GREEN), (-20, GREEN), (-16, GREEN),
             (-12, YELLOW), (-9, YELLOW), (-6, YELLOW), (-3, RED), (0, RED)],
    }
    return tabela[n]


def plan(n_led=10, slider="S1", foam=True, overload_dot=False, callouts=False, dims=False, lit_to=-12, plug=True):
    """Planta da placa em mm (origem = canto superior esquerdo da placa)."""
    o = []
    # plugue USB-C macho (visto de cima) e placa
    if plug:
        o.append('<rect x="-6.65" y="3.53" width="8.15" height="8.94" rx="1.2" fill="#c3c7ce" stroke="#6b7078" stroke-width=".18"/>')
        o.append('<rect x="-5.6" y="4.5" width="6" height="7" rx=".8" fill="none" stroke="#8c919a" stroke-width=".15"/>')
    o.append('<rect x="0" y="0" width="60" height="16" rx="2" fill="#202026" stroke="#3a3a44" stroke-width=".2"/>')
    o.append('<rect x="0" y="3.5" width="2.2" height="9" fill="#9aa0a8" opacity=".55"/>')
    # medidor
    levels = led_levels(n_led)[::-1]  # o mais forte fica perto do plugue
    pitch = 32.0 / (n_led - 1)
    o.append('<text x="12.2" y="2.55" font-size="1.15" fill="#9a9aa6" text-anchor="end">dBFS</text>')
    for i, (db, col) in enumerate(levels):
        x = 14.0 + i * pitch
        on = db <= lit_to
        o.append('<circle cx="%.2f" cy="4.9" r="%s" fill="%s" opacity="%s"/>' % (x, "1.5" if on else "0", col, ".28"))
        o.append('<rect x="%.2f" y="4.5" width="1.6" height="0.8" rx=".15" fill="%s" opacity="%s"/>' % (x - .8, col, "1" if on else ".32"))
        o.append('<text x="%.2f" y="2.9" font-size="1.05" fill="#b5b5c0" text-anchor="middle">%s</text>' % (x, db if db else "0"))
    if overload_dot:
        o.append('<circle cx="10.4" cy="4.9" r=".55" fill="#59a8ff"/>')
        o.append('<text x="10.4" y="7.2" font-size=".9" fill="#59a8ff" text-anchor="middle">MIC</text>')
    # serigrafia
    o.append('<text x="14" y="9.55" font-size="2.7" fill="#f2f2f2" font-family="Georgia,serif" font-style="italic">Liebling</text>')
    o.append('<text x="31.6" y="9.55" font-size="1.15" fill="#9a9aa6" letter-spacing=".25">BATSCHAUER</text>')
    # ganho
    o.append('<text x="12.2" y="12.45" font-size="1.15" fill="#9a9aa6" text-anchor="end">GAIN</text>')
    if slider == "S1":  # slider mecânico, curso 15 mm
        o.append('<rect x="21" y="10.5" width="17" height="2.4" rx="1.2" fill="#08080a" stroke="#9aa0a8" stroke-width=".18"/>')
        o.append('<rect x="27.5" y="9.3" width="4" height="4.8" rx=".5" fill="#8d929c" stroke="#d0d4da" stroke-width=".15"/>')
        for k in range(4):
            o.append('<line x1="%.2f" y1="9.9" x2="%.2f" y2="13.5" stroke="#5a5e66" stroke-width=".15"/>' % (28.2 + k * .85, 28.2 + k * .85))
        o.append('<text x="23" y="15.1" font-size="1.05" fill="#b5b5c0" text-anchor="middle">0</text>')
        o.append('<text x="36" y="15.1" font-size="1.05" fill="#b5b5c0" text-anchor="middle">+42 dB</text>')
    elif slider == "S2":  # slider capacitivo desenhado no cobre, 30 mm
        for k in range(10):
            x0 = 14 + k * 3.0
            o.append('<polygon points="%.2f,13.2 %.2f,10.2 %.2f,13.2" fill="#c9a24a" opacity=".92"/>' % (x0, x0 + 1.5, x0 + 3.0))
            o.append('<polygon points="%.2f,10.2 %.2f,13.2 %.2f,10.2" fill="#a8842f" opacity=".92"/>' % (x0 + 1.5, x0 + 3.0, x0 + 4.5)) if k < 9 else None
        o.append('<circle cx="30.5" cy="11.7" r="1.7" fill="none" stroke="#fff" stroke-width=".18" stroke-dasharray=".5 .4"/>')
        o.append('<text x="14" y="15.1" font-size="1.05" fill="#b5b5c0">0</text>')
        o.append('<text x="44" y="15.1" font-size="1.05" fill="#b5b5c0" text-anchor="end">+42 dB</text>')
    else:  # S3 roda de polegar na borda
        o.append('<rect x="24" y="10.2" width="11" height="7.2" rx="2.4" fill="#8d929c" stroke="#d0d4da" stroke-width=".15"/>')
        for k in range(8):
            o.append('<line x1="%.2f" y1="11" x2="%.2f" y2="16.8" stroke="#5a5e66" stroke-width=".15"/>' % (25.6 + k * 1.15, 25.6 + k * 1.15))
        o.append('<text x="29.5" y="9.3" font-size=".95" fill="#b5b5c0" text-anchor="middle">0  ◀▶  +42</text>')
    # microfone
    o.append('<rect x="52.5" y="6.5" width="4" height="3" rx=".3" fill="#cfd2d8" stroke="#6b7078" stroke-width=".12"/>')
    o.append('<circle cx="54.5" cy="8" r=".9" fill="#050506" stroke="#fff" stroke-width=".1"/>')
    if foam:
        o.append('<circle cx="54.5" cy="8" r="5" fill="#46464c" opacity=".78" stroke="#cfcfd6" stroke-width=".15" stroke-dasharray=".7 .5"/>')
        for k in range(14):
            a = k * 0.9
            o.append('<circle cx="%.2f" cy="%.2f" r=".28" fill="#2a2a2e"/>' % (54.5 + 3.3 * math.cos(a * 2.3) * (0.4 + (k % 3) * .3), 8 + 3.3 * math.sin(a * 2.3) * (0.5 + (k % 4) * .22)))
    if callouts:
        pts = [(1, -3.2, -3.4, -3.2, 3.5), (2, 28, -3.4, 28, 2.0), (4, 54.5, -3.4, 54.5, 3.3),
               (3, 30, 19.6, 30, 13.9), (6, 18, 19.6, 18, 10.0), (5, 58.8, 19.6, 57.8, 11.9)]
        for n, cx, cy, tx, ty in pts:
            o.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#59a8ff" stroke-width=".15"/>' % (cx, cy, tx, ty))
            o.append('<circle cx="%s" cy="%s" r="1.35" fill="#59a8ff"/>' % (cx, cy))
            o.append('<text x="%s" y="%s" font-size="1.6" fill="#0b1118" text-anchor="middle" font-weight="700">%d</text>' % (cx, cy + .58, n))
    if dims:
        d = '#8a8a96'
        o.append('<line x1="0" y1="24.3" x2="60" y2="24.3" stroke="%s" stroke-width=".15"/>' % d)
        o.append('<line x1="0" y1="23.6" x2="0" y2="25" stroke="%s" stroke-width=".15"/><line x1="60" y1="23.6" x2="60" y2="25" stroke="%s" stroke-width=".15"/>' % (d, d))
        o.append('<text x="30" y="23.7" font-size="1.3" fill="#c8c8d2" text-anchor="middle">60 mm</text>')
        o.append('<line x1="65.5" y1="0" x2="65.5" y2="16" stroke="%s" stroke-width=".15"/>' % d)
        o.append('<line x1="64.8" y1="0" x2="66.2" y2="0" stroke="%s" stroke-width=".15"/><line x1="64.8" y1="16" x2="66.2" y2="16" stroke="%s" stroke-width=".15"/>' % (d, d))
        o.append('<text x="68.8" y="8.5" font-size="1.3" fill="#c8c8d2" text-anchor="middle">16 mm</text>')
        o.append('<text x="-3.3" y="14.9" font-size="1.0" fill="#c8c8d2" text-anchor="middle">USB-C</text>')
    return "".join(o)


def svg_plan(vb, **kw):
    return '<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg" role="img">%s</svg>' % (vb, plan(**kw))


# ---------------------------------------------------------------- isométrico
class Iso:
    def __init__(self, scale, ox=0.0, oy=0.0):
        self.S, self.ox, self.oy = scale, ox, oy
        self.out, self.pts = [], []

    def P(self, x, y, z):
        px = (x - y) * C30 * self.S + self.ox
        py = ((x + y) * 0.5 - z) * self.S + self.oy
        self.pts.append((px, py))
        return px, py

    def poly(self, pts, fill, stroke="#000", sw=.5, op=1):
        s = " ".join("%.1f,%.1f" % p for p in pts)
        self.out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" opacity="%s"/>' % (s, fill, stroke, sw, op))

    def box(self, x0, x1, y0, y1, z0, z1, top, right, front, stroke="#000", sw=.4):
        P = self.P
        self.poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], front, stroke, sw)
        self.poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], right, stroke, sw)
        self.poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], top, stroke, sw)

    def cyl(self, cx, cy, z0, z1, r, top, side, stroke="#000"):
        rx, ry = r * self.S * 1.2247, r * self.S * 0.7071
        tx, ty = self.P(cx, cy, z1)
        bx, by = self.P(cx, cy, z0)
        self.pts += [(tx - rx, ty - ry), (tx + rx, ty + ry), (bx - rx, by + ry)]
        self.out.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" stroke="%s" stroke-width=".4"/>' % (bx, by, rx, ry, side, stroke))
        self.out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (tx - rx, ty, 2 * rx, by - ty, side))
        self.out.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" stroke="%s" stroke-width=".4"/>' % (tx, ty, rx, ry, top, stroke))

    def plan_on(self, world, z, **kw):
        """Coloca a planta (mm) sobre uma face: world(u,v)->(x,y,z)."""
        o = world(0, 0)
        a = world(1, 0)
        b = world(0, 1)
        p0, pa, pb = self.P(*o), self.P(*a), self.P(*b)
        m = (pa[0] - p0[0], pa[1] - p0[1], pb[0] - p0[0], pb[1] - p0[1], p0[0], p0[1])
        self.out.append('<g transform="matrix(%.4f %.4f %.4f %.4f %.2f %.2f)">%s</g>' % (m + (plan(**kw),)))

    def svg(self, pad=18):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        x0, y0 = min(xs) - pad, min(ys) - pad
        w, h = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
        return '<svg viewBox="%.0f %.0f %.0f %.0f" xmlns="http://www.w3.org/2000/svg" role="img"><defs>%s</defs>%s</svg>' % (
            x0, y0, w, h, GRAD, "".join(self.out))


GRAD = ('<linearGradient id="fade" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#1b1d22"/>'
        '<stop offset=".55" stop-color="#1b1d22" stop-opacity=".9"/><stop offset="1" stop-color="#1b1d22" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="fade2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#34373e"/>'
        '<stop offset=".55" stop-color="#34373e" stop-opacity=".9"/><stop offset="1" stop-color="#34373e" stop-opacity="0"/></linearGradient>')


def led_boxes(iso, world, n=10, lit_to=-12):
    levels = led_levels(n)[::-1]
    pitch = 32.0 / (n - 1)
    for i, (db, col) in enumerate(levels):
        u = 14.0 + i * pitch
        x0, y0, z0 = world(u - .8, 4.5)
        x1, y1, z1 = world(u + .8, 5.3)
        iso.box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0 - 0.0, z0 + .6,
                col if db <= lit_to else "#3b3b44", "#202026", "#2a2a30", stroke="#111", sw=.2)


def iso_flat():
    iso = Iso(8.2)
    T = BOARD_T
    wd = lambda u, v: (u, v, T)
    # plugue
    iso.box(-6.65, 1.5, 3.53, 12.47, -1.13, 2.13, "#c8ccd3", "#9ea3ab", "#b2b6be")
    # placa
    iso.box(0, 60, 0, 16, 0, T, "#202026", "#0f0f12", "#17171b")
    iso.plan_on(wd, T, n_led=10, slider="S1", foam=False, plug=False)
    led_boxes(iso, wd)
    # knob do slider
    iso.box(27.5, 31.5, 9.3, 14.1, T, T + 3.2, "#9aa0a8", "#6f747c", "#80858d", stroke="#222", sw=.3)
    # microfone e espuma
    iso.box(52.5, 56.5, 6.5, 9.5, T, T + 1.0, "#cfd2d8", "#9ea3ab", "#b2b6be", stroke="#222", sw=.3)
    iso.cyl(54.5, 8, T, T + 3.5, 5, "#55555c", "#3a3a40")
    return iso.svg()


def iso_use():
    iso = Iso(6.4)
    PH_W, PH_T, PH_H = 72.0, 8.5, 26.0
    xc, y_mid = 36.0, PH_T / 2
    # celular: só a parte de baixo, com a ponta de cima esmaecida
    iso.box(0, PH_W, 0, PH_T, 0, PH_H, "#34373e", "url(#fade2)", "url(#fade)", stroke="#0b0b0d", sw=.5)
    # tela (face +y), a moldura e a área de vidro
    P = iso.P
    iso.poly([P(3, PH_T, 4), P(PH_W - 3, PH_T, 4), P(PH_W - 3, PH_T, PH_H), P(3, PH_T, PH_H)], "url(#fade)", "#2a2d33", .4, .9)
    # plugue visível entre o celular e a placa
    gap = 1.8
    iso.box(xc - 4.47, xc + 4.47, y_mid - 1.63, y_mid + 1.63, -gap, 0, "#c8ccd3", "#9ea3ab", "#b2b6be", stroke="#222", sw=.3)

    def wd(u, v, w=0.0):
        return (xc + 8 - v, y_mid - .5 + w, -gap - u)  # v para -x: o texto lê-se girando a cabeça

    # placa pendurada (u = comprimento para baixo, v = largura, w = espessura em +y)
    iso.box(xc - 8, xc + 8, y_mid - .5, y_mid + .5, -gap - 60, -gap, "#202026", "#0f0f12", "#17171b")
    iso.plan_on(lambda u, v: wd(u, v, 1.0), 0, n_led=10, slider="S1", foam=False, plug=False)
    y_top = y_mid + .5
    # LEDs, knob, microfone, espuma (por profundidade: maiores x+y por último)
    levels = led_levels(10)[::-1]
    for i, (db, col) in enumerate(levels):
        u = 14.0 + i * 3.2
        x0, y0, z0 = wd(u + .8, 4.5, 1.0)
        x1, y1, z1 = wd(u - .8, 5.3, 1.0)
        iso.box(min(x0, x1), max(x0, x1), y_top, y_top + .6, min(z0, z1), max(z0, z1),
                col if db <= -12 else "#3b3b44", "#202026", col if db <= -12 else "#2a2a30", stroke="#111", sw=.2)
    x0, _, z0 = wd(27.5, 9.3)
    x1, _, z1 = wd(31.5, 14.1)
    iso.box(min(x0, x1), max(x0, x1), y_top, y_top + 3.2, min(z0, z1), max(z0, z1), "#9aa0a8", "#6f747c", "#a2a7af", stroke="#222", sw=.3)
    x0, _, z0 = wd(52.5, 6.5)
    x1, _, z1 = wd(56.5, 9.5)
    iso.box(min(x0, x1), max(x0, x1), y_top, y_top + 1.0, min(z0, z1), max(z0, z1), "#cfd2d8", "#9ea3ab", "#cfd2d8", stroke="#222", sw=.3)
    # espuma: disco de Ø10 voltado para o usuário (+y)
    cx, _, cz = wd(54.5, 8)
    r = 5.0
    ptsf = [iso.P(cx + r * math.cos(t * math.pi / 12), y_top + 3.5, cz + r * math.sin(t * math.pi / 12)) for t in range(24)]
    ptsb = [iso.P(cx + r * math.cos(t * math.pi / 12), y_top, cz + r * math.sin(t * math.pi / 12)) for t in range(24)]
    iso.poly(ptsb, "#3a3a40", "#111", .4)
    iso.poly(ptsf, "#55555c", "#111", .4)
    return iso.svg()


# ------------------------------------------------------------------ página
CSS = """
:root{--bg:#121216;--card:#1b1b22;--ink:#e8e8ee;--mut:#9a9aa8;--acc:#59a8ff;--ok:#3ddc6a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 16px 60px}
h1{font:italic 600 2.4rem Georgia,serif;margin:0}h1 small{font:500 .9rem system-ui;color:var(--mut);letter-spacing:.2em;margin-left:10px}
h2{font-size:1.15rem;margin:38px 0 4px;border-top:1px solid #2a2a34;padding-top:22px}
p.sub{color:var(--mut);margin:.2rem 0 1rem}
.card{background:var(--card);border-radius:12px;padding:14px;margin:12px 0}
.card svg{width:100%;height:auto;display:block}
.grid{display:grid;gap:12px;align-items:start}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:760px){.g2,.g3{grid-template-columns:1fr}}
.opt h3{margin:.2rem 0;font-size:1rem}.opt p{margin:.15rem 0;font-size:.9rem;color:#c8c8d2}
.rec{display:inline-block;background:var(--ok);color:#06210f;border-radius:6px;padding:0 7px;font-size:.75rem;font-weight:700;margin-left:6px}
ol.leg{columns:2;font-size:.92rem;color:#c8c8d2;margin:6px 0 0;padding-left:20px}
.note{font-size:.88rem;color:var(--mut)}
"""


def opt(title, body, svg, rec=False):
    return '<div class="card opt">%s<h3>%s%s</h3>%s</div>' % (
        svg, title, '<span class="rec">no desenho</span>' if rec else "", body)


def page():
    vb_main = "-10 -7 82 34"
    vb_mini = "-8.5 -.8 71 18"
    main = svg_plan(vb_main, n_led=10, slider="S1", foam=True, callouts=True, dims=True)
    legend = [
        "Plugue USB-C macho SMD soldado na ponta da placa (6,65 mm visíveis, 8,94 mm de largura).",
        "Medidor de 10 LEDs, sobe em direção ao plugue (vermelho perto do celular).",
        "Slider de ganho, 0 a +42 dB, curso de 15 mm (opções de slider abaixo).",
        "Microfone MEMS de topo (candidato Infineon IM72D128) com furo acústico na placa.",
        "Espuma acústica Ø10 colada sobre a porta: plosivas e rajadas de ar do fole.",
        "Serigrafia: nome, marca, escala. Nada sobre pad.",
    ]
    sl = [
        ("S1 · Slider mecânico, curso 15 mm",
         "Peça SMD/THT de 15 mm de curso. Tem o toque que o músico reconhece, uma peça só. Resolução ≈ 2,8 dB/mm: pede mão firme, e o desgaste é o único ponto fraco. "
         "A eletrônica confere um modelo que a JLCPCB monte.", "S1", True),
        ("S2 · Slider capacitivo no cobre, 30 mm",
         "Sem peça: o desenho do cobre é o slider (10 losangos). Dobra o curso (≈ 1,4 dB/mm), custo zero e sem desgaste. "
         "Contras: sem tato nem batente, dedo molhado/luva muda a leitura, firmware de toque no RP2040 (PIO) e ajuste fino em teste real.", "S2", False),
        ("S3 · Roda de polegar na borda",
         "Não é slider, mostrada para comparar: gira com o dedão na lateral, ocupa pouco comprimento e dá curso longo (mais de 1 volta, ≈ 0,5 dB/grau). "
         "Peça sem estoque certo na JLCPCB; fica fora se você mantiver o slider.", "S3", False),
    ]
    sl_html = "".join(opt(t, '<p>%s</p>' % b, svg_plan(vb_mini, n_led=10, slider=s, foam=True), r) for t, b, s, r in sl)
    ld = [
        ("L1 · 8 LEDs",
         "Verde −36, −27, −18, −12 · amarelo −8, −4 · vermelho −2, 0. Passo de 4 a 9 dB: dá para ajustar o ganho, mas é grosseiro perto do topo, que é onde o acordeon decide. Economiza ~US$ 0,03.",
         dict(n_led=8, lit_to=-12), False),
        ("L2 · 10 LEDs",
         "Verde −42 a −12 (6) · amarelo −9, −6 · vermelho −3, 0 (clip, fica preso 1 s). Bom compromisso: passo de 3 a 6 dB onde importa.",
         dict(n_led=10, lit_to=-12), True),
        ("L3 · 12 LEDs (11 + aviso de microfone)",
         "Escala de 4 dB no verde e 3 dB de −12 a 0, mais um LED azul que só acende quando o próprio sensor satura (o ganho não resolve). "
         "Mais ~US$ 0,05, mais um pino, e o que o bayan de perto mais precisa saber.", dict(n_led=11, overload_dot=True, lit_to=-12), False),
    ]
    ld_html = "".join(opt(t, '<p>%s</p>' % b, svg_plan(vb_mini, slider="S1", foam=True, **kw), r) for t, b, kw, r in ld)
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Liebling · protótipo visual R2MIC</title><style>%s</style></head><body><main>
<h1>Liebling<small>BATSCHAUER · MIC USB-C</small></h1>
<p class="sub">Protótipo visual do conceito R2MIC. Medidas em mm, placa 60 × 16 × 1,0. Tudo é desenho de conceito: nada foi encomendado nem conferido em peça real.</p>

<h2>Planta</h2>
<div class="card">%s<ol class="leg">%s</ol></div>

<h2>Isométrico</h2>
<p class="sub">À esquerda, o produto; à direita, em uso no celular em pé, com os LEDs voltados para o músico.</p>
<div class="grid g2"><div class="card">%s</div><div class="card">%s</div></div>
<p class="note">O plugue USB-C é reversível: se a placa entrar de cabeça para baixo, os LEDs ficam virados para trás e o músico vira o plugue. O sentido do medidor com o celular deitado (live em paisagem) é uma pergunta aberta na SPEC.</p>

<h2>Opções de slider de ganho</h2>
<p class="sub">Curso e resolução são o que decide: 0 a +42 dB em 15 mm dá ~2,8 dB/mm.</p>
<div class="grid g3">%s</div>

<h2>Opções do medidor de LEDs</h2>
<p class="sub">Simulação: voz em bom nível, acesos até −12 dBFS. Em todas, o vermelho do fim da escala (0) é o clip.</p>
<div class="grid g3">%s</div>
</main></body></html>""" % (CSS, main, "".join("<li>%s</li>" % t for t in legend), iso_flat(), iso_use(), sl_html, ld_html)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "liebling_r2.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page())
    print(path)
