"""The Pocket's review page for J: etutti/pocket/revisao/index.html (SPEC v3, D2).

    python etutti/hardware/pocket/case/revisao.py        (stdlib; run after
    case.py, fit_check.py, mechanics.py, render.py and ../layout.py)

Portuguese only, noindex, not linked from the home page or the sitemap.
The pictures are the PNGs in renders/ (linked, not copied); the numbers
come from out/fit_check.json, out/board_sag.json and ../build/pocket.json.
Edit this script, not the page.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
PAGE = os.path.normpath(os.path.join(POCKET, "..", "..", "pocket", "revisao", "index.html"))
IMG = "../../hardware/pocket/case/renders/"


def n(v, d=1):
    """Portuguese number: comma decimals."""
    return f"{v:.{d}f}".replace(".", ",")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


QUESTIONS = []      # filled by main() from FIT_CHECK.md's last section, so the page and the report agree


def questions_from_report():
    path = os.path.join(POCKET, "FIT_CHECK.md")
    if not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8").read()
    if "## Perguntas para a gestão" not in txt:
        return []
    part = txt.split("## Perguntas para a gestão", 1)[1]
    items, cur = [], None
    for line in part.splitlines():
        s = line.strip()
        if line[:1].isdigit() and ". " in line[:4]:          # a top-level item
            if cur:
                items.append(cur)
            cur = s.split(". ", 1)[1]
        elif s and cur is not None and not s.startswith("#"):
            if s[:1].isdigit() and ". " in s[:4]:              # a nested numbered item
                s = "(" + s.split(". ", 1)[0] + ") " + s.split(". ", 1)[1]
            cur += " " + s.lstrip("- ")
    if cur:
        items.append(cur)
    return items


def md_inline(s):
    """**bold** and `code` to HTML (enough for the questions)."""
    import html
    import re
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def page():
    fc = load(os.path.join(HERE, "out", "fit_check.json"))
    sag = load(os.path.join(HERE, "out", "board_sag.json"))
    pj = load(os.path.join(POCKET, "build", "pocket.json"))
    with open(os.path.join(POCKET, "build", "pocket_top.svg"), encoding="utf-8") as f:
        top = f.read()
    top = top.replace('<svg xmlns', '<svg class="pv-svg" role="img" aria-label="O Pocket visto de cima" xmlns', 1)
    top = top.split(">", 1)
    top = top[0].split(' width="')[0] + ">" + top[1]          # drop the fixed size: it scales to the column
    sp, pa, bt, w = fc["speaker"], fc["panel"], fc["battery"], fc["weight"]
    rows = [
        ("Comprimento × largura", f"{n(pj['length'])} × {n(pj['width'], 0)} mm (o eTuttino tem {n(pj['etuttino_length'])})"),
        ("Altura", "teclado igual ao eTuttino: tampa a 17,4 mm, topo das teclas a 26,6; interface a 33"),
        ("Peso do case impresso", f"{n(w['resin_g'], 0)} g em resina, {n(w['mjf_pa12_g'], 0)} g em MJF "
                                  f"({n(w['printed_cm3'])} cm³), mais {n(w['plate_fr4_g'], 0)} g da placa de FR-4 dos switches"),
        ("Flexão da placa a 3 N", f"{n(sag['max_mm'], 3)} mm no pior botão ({sag['worst_key']}), média {n(sag['mean_mm'], 3)}; "
                                  f"limite 0,05 ({sag['pillars']} pilares)"),
        ("Alto-falante CLS0361-L152", f"caixa fechada de {n(sp['back_volume_nominal_cm3'])} cm³ "
                                      f"({n(sp['back_volume_conservative_cm3'])} contando o alto-falante inteiro como sólido); pedido 8–12"),
        ("Grade", f"{sp['grille']['holes']} furos de Ø {n(2.1)}, {n(sp['grille']['open_ratio'] * 100, 0)} % do cone abertos (pedido ≥ 30 %); "
                  f"{n(sp['membrane_to_grille_mm'], 1)} mm da membrana"),
        ("Bateria", f"berço {n(bt['cradle_inside'][0])} × {n(bt['cradle_inside'][1])} × {n(bt['cradle_inside'][2])} (o pedido), "
                    f"fora da placa principal, sai por uma tampinha no fundo"),
        ("USB-C e fone", f"na parede curva de trás-esquerda, numa plaquinha só; parede de {n(1.0)} mm no furo do USB-C "
                         f"e {n(1.5)} no do fone, com rebaixo por fora ({n(pa['usb_recess_depth'])} e {n(pa['jack_spot_depth'])} mm)"),
        ("Arestas abertas nos STL", ", ".join(f"{k} {v['open_edges']}" for k, v in fc["stl"].items())),
        ("Raios pela abertura", f"{fc['rays']['keys'][0]} livres de {sum(fc['rays']['keys'])} (teclas), "
                                f"{fc['rays']['grille'][0]} de {sum(fc['rays']['grille'])} (grade)"),
    ]
    table = "".join(f'<tr><th scope="row">{a}</th><td>{b}</td></tr>' for a, b in rows)
    figs = [
        ("seixo_iso.png", "O Seixo, variante B, com as teclas, os knobs, o LED e a grade."),
        ("seixo_iface.png", "A área de interface: logo gravado acompanhando a curva, knobs e LED na linha y = 49, grade só sobre o cone."),
        ("seixo_left.png", "A parede curva de trás-esquerda: USB-C e fone, com rebaixos por fora."),
        ("fit_dentro.png", "Por dentro, sem a tampa: placa principal (verde), pilha Teensy + Audio Board (atrás), plaquinha do painel "
                           "(azul), potenciômetro deitado e plaquinha dos knobs (roxo), caixa do alto-falante; a bateria fica embaixo, no fundo."),
        ("fit_corte_y21.png", "Corte em y = 21: a plaquinha do painel passa por cima do plugue do Teensy."),
        ("fit_corte_y49.png", "Corte na linha dos knobs (y = 49): potenciômetro preso na tampa, encoder e LED na plaquinha, bateria embaixo."),
        ("fit_corte_y78.png", "Corte pelo alto-falante: grade, junta, caixa fechada e o berço da bateria embaixo."),
        ("seixo_below.png", "Por baixo: a tampinha da bateria com 2 parafusos, os parafusos do fundo e os pés."),
    ]
    fig_html = "".join(f"""
      <figure class="rv-fig">
        <img src="{IMG}{f}" alt="{c}" loading="lazy" />
        <figcaption>{c}</figcaption>
      </figure>""" for f, c in figs)
    qs = questions_from_report()
    q_html = "".join(f"<li>{md_inline(q)}</li>" for q in qs)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BeatConfused | eTuttino Pocket · revisão D2</title>
  <meta name="description" content="eTuttino Pocket: o case Seixo, variante B, modelado (SPEC v3, D2)." />
  <!-- Review page for J (SPEC v3, task D2). Portuguese only, unlisted:
       not on the home page, not in the sitemap. Written by
       etutti/hardware/pocket/case/revisao.py -- edit that script, not this file. -->
  <meta name="robots" content="noindex,nofollow" />
  <meta name="theme-color" content="#10131d" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  />
  <link rel="stylesheet" href="/shared/tuner-common.css?v=20260913" />
  <link rel="stylesheet" href="../../family.css?v=20261017" />
  <link rel="stylesheet" href="/shared/site-title.css?v=20261008" />
  <style>
    .rv-wrap {{ max-width: 52rem; width: 100%; margin: 0 auto; display: grid; gap: 1.2rem; min-width: 0; }}
    .rv-box {{ padding: 1rem; border: 1px solid var(--border); border-radius: 0.9rem;
      background: var(--surface-solid); box-shadow: var(--shadow-soft); min-width: 0; }}
    .rv-box h2 {{ margin: 0 0 0.5rem; font-family: "Cormorant Garamond", Georgia, serif; font-size: 1.55rem; line-height: 1.15; }}
    .rv-fig {{ margin: 0.8rem 0 0; }}
    .rv-fig img, .pv-svg {{ display: block; width: 100%; height: auto; border-radius: 0.5rem; }}
    .rv-fig figcaption {{ margin-top: 0.3rem; color: var(--ink-soft); font-size: 0.85rem; }}
    .rv-table-wrap {{ overflow-x: auto; }}
    .rv-table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
    .rv-table th, .rv-table td {{ padding: 0.4rem 0.45rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
    .rv-table tbody th {{ font-weight: 600; color: var(--ink-soft); width: 34%; }}
    .rv-box p, .rv-box li {{ font-size: 0.94rem; }}
    .rv-box ul, .rv-box ol {{ padding-left: 1.2rem; display: grid; gap: 0.35rem; }}
    @media (max-width: 560px) {{ .rv-box {{ padding: 0.7rem; }} .rv-table {{ font-size: 0.8rem; }} .rv-table tbody th {{ width: 40%; }} }}
  </style>
</head>
<body>
  <main class="page">
    <a class="site-title" href="/">beatconfused.com</a>
    <header class="hero">
      <p class="eyebrow">eTuttino Pocket · revisão</p>
      <h1>O Seixo, variante B</h1>
      <p class="family-lead">O case do Pocket modelado (SPEC v3, tarefa D2): o lado esquerdo em curva única que o J escolheu, com
      tudo o que vai dentro conferido peça por peça contra as medidas da eletrônica. {n(pj['length'])} × 100 mm.</p>
      <p><span class="family-tag">Versão final da B · para revisar</span></p>
    </header>

    <div class="rv-wrap">
    <section class="rv-box">
      <h2>Vista de cima</h2>
      {top}
      <p class="rv-fig"><small>Em escala; tracejado: o eTuttino, com os teclados sobrepostos.</small></p>
    </section>

    <section class="rv-box">
      <h2>Como ficou</h2>
      {fig_html}
    </section>

    <section class="rv-box">
      <h2>Números</h2>
      <div class="rv-table-wrap"><table class="rv-table"><tbody>{table}</tbody></table></div>
    </section>

    <section class="rv-box">
      <h2>O que mudou desde o D1</h2>
      <ul>
        <li><strong>Potenciômetro com chave</strong> (o pedido da SPEC sem subir a tampa): um de 9 mm deitado, numa plaquinha em pé
        à direita do eixo, preso na tampa pela porca da rosca M7. O corpo pendura até 14,5 mm, por cima da bateria.</li>
        <li><strong>Bateria</strong> no berço pedido (58,5 × 36,5 × 7,6, já com os 8 % de inchaço), no fundo da parte da frente da
        interface, fora da placa principal. Sai por uma tampinha de 2 parafusos no fundo, sem abrir a tampa; o plugue dela se
        encaixa num bolso dentro do próprio berço.</li>
        <li><strong>Pilha baixa</strong> (Teensy soldado direto na Audio Board, como a eletrônica prefere): 8,7 mm em vez de 13.</li>
        <li><strong>USB-C e fone numa plaquinha só</strong>, na parede curva de trás-esquerda, por cima do plugue do Teensy.</li>
        <li><strong>Alto-falante CLS0361-L152</strong> sob a grade, com caixa traseira fechada e vedada que cresce para o lado.</li>
      </ul>
    </section>

    <section class="rv-box">
      <h2>Perguntas para a gestão</h2>
      <ol>{q_html}</ol>
    </section>
    </div>

    <p class="family-back"><a href="../">← eTuttino Pocket</a></p>

    <footer class="footer">
      <p class="footer-links"><a href="https://beatconfused.com">beatconfused.com</a></p>
    </footer>
  </main>
</body>
</html>
"""


def main():
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    with open(PAGE, "w", encoding="utf-8", newline="\n") as f:
        f.write(page())
    print("wrote", PAGE)


if __name__ == "__main__":
    main()
