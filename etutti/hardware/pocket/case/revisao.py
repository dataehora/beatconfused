"""The Pocket's review page for J: etutti/pocket/revisao/index.html (SPEC v5, F3).

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
    kr, tb = pa["knob_recesses"], pa["teensy_button"]
    rows = [
        ("Comprimento × largura", f"{n(pj['length'])} × {n(pj['width'], 0)} mm (o eTuttino tem {n(pj['etuttino_length'])})"),
        ("Altura", "teclado igual ao eTuttino: tampa a 17,4 mm, topo das teclas a 26,6; interface a 33"),
        ("Peso das peças impressas", f"{n(w['v4_materials']['printed_total_g'], 0)} g: casca de cima em resina "
                                     f"{n(w['v4_materials']['top_shell_resin_g'], 0)} g, fundo + tampinha + fundo da caixa em MJF "
                                     f"{n(w['v4_materials']['mjf_parts_g'], 0)} g, 28 capas em resina {n(w['v4_materials']['caps_resin_g'], 0)} g; "
                                     f"mais {n(w['plate_fr4_g'], 0)} g da placa de FR-4 dos switches"),
        ("Flexão da placa a 3 N", f"{n(sag['max_mm'], 3)} mm no pior botão ({sag['worst_key']}), média {n(sag['mean_mm'], 3)}; "
                                  f"limite 0,05 ({sag['pillars']} pilares)"),
        ("Alto-falante CLS0361-L152", f"caixa fechada de {n(sp['back_volume_nominal_cm3'])} cm³ "
                                      f"({n(sp['back_volume_conservative_cm3'])} contando o alto-falante inteiro como sólido); pedido 8–12"),
        ("Grade", f"{sp['grille']['holes']} furos de Ø {n(2.1)}, {n(sp['grille']['open_ratio'] * 100, 0)} % do cone abertos (pedido ≥ 30 %); "
                  f"{n(sp['membrane_to_grille_mm'], 1)} mm da membrana"),
        ("Bateria", f"berço {n(bt['cradle_inside'][0])} × {n(bt['cradle_inside'][1])} × {n(bt['cradle_inside'][2])} (o pedido), "
                    f"fora da placa principal, sai por uma tampinha no fundo; bolso do plugue {n(bt['pocket_inside'][0])} × "
                    f"{n(bt['pocket_inside'][1])} × {n(bt['pocket_inside'][2])} (pedido ≥ 14,5 × 9 × 6)"),
        ("Micro-USB e fone", f"na parede curva de trás-esquerda, sem plaquinha: extensão micro-B em fita FPC, a fêmea num túnel com "
                             f"um ressalto de {n(0.5)} na parede e uma trava impressa (2 × M2); janela 12 × 8 com parede de {n(3.0)} "
                             f"(rebaixo por fora de {n(pa['female']['outer_recess_depth'])}). Fone Cliff FC681375V em furo de Ø {n(8.2)}, "
                             f"parede de {n(2.0)}, porca por fora (rebaixo de {n(pa['jack']['spot_face_depth'])})"),
        ("Knobs", f"rebaixo de Ø {n(kr['recess_d'], 0)} × {n(kr['recess_depth'])} sob os dois; a porca M7 fica rente "
                  f"({n(kr['nut']['flush_with_lid'])}); sobram {n(kr['thread']['left_above_nut'])} mm de rosca acima dela, dentro do knob; "
                  f"knob proposto Ø {n(kr['knob']['d'], 0)}, saia {n(kr['knob']['skirt_to_nut_axial'])} acima da porca"),
        ("Botão do Teensy", f"furo de Ø {n(tb['hole_d'])} na tampa, sobre o botão, com tubo-guia: um clipe desce {n(tb['depth_lid_to_teensy'])} mm "
                            f"até o botão com o case fechado (posição do botão: conferir na peça)"),
        ("Arestas abertas nos STL", ", ".join(f"{k} {v['open_edges']}" for k, v in fc["stl"].items())),
        ("Raios pela abertura", f"{fc['rays']['keys'][0]} livres de {sum(fc['rays']['keys'])} (teclas), "
                                f"{fc['rays']['grille'][0]} de {sum(fc['rays']['grille'])} (grade), "
                                f"{fc['rays']['panel'][0]} de {sum(fc['rays']['panel'])} (janela do micro-USB e furo do fone), "
                                f"{fc['rays']['button'][0]} de {sum(fc['rays']['button'])} (furo do botão do Teensy)"),
        ("Colisões", f"{len(fc['collisions_with_case'])} entre peças e case; "
                     f"{sum(1 for p in fc['pairs'] if p[2] > 0)} entre peças; "
                     f"{sum(1 for v in fc['case_parts_overlap'].values() if v > 0)} entre as peças do case"),
    ]
    table = "".join(f'<tr><th scope="row">{a}</th><td>{b}</td></tr>' for a, b in rows)
    figs = [
        ("seixo_iso.png", "O Seixo, variante B, com as teclas, os knobs propostos (Ø 15), o LED e a grade."),
        ("seixo_recessos.png", "Sem os knobs: os dois rebaixos de Ø 14 na tampa, a porca M7 rente no do volume e o furinho do botão do Teensy à direita do logo."),
        ("seixo_left.png", "A parede curva de trás-esquerda: janela do micro-USB (com rebaixo) e o fone com a porca por fora."),
        ("fit_conectores.png", "Por cima, sem a tampa: o bloco da fêmea micro-B com a trava (azul), o fone, e em amarelo o espaço da fita FPC "
                               "(sobe do plugue do Teensy, dobra sob o bloco, sobra dobrada sobre o Teensy)."),
        ("fit_corte_y21.png", "Corte em y = 21: a fêmea no túnel, presa pelo ressalto da parede e pela trava; o plugue do Teensy embaixo, com 2 mm para a fita dobrar; à direita, o tubo-guia do botão."),
        ("fit_corte_y38.png", "Corte em y = 38: o fone por cima do J_BAT, com a porca por fora."),
        ("fit_corte_y49.png", "Corte na linha dos knobs (y = 49): os rebaixos, a porca rente, o potenciômetro e o encoder."),
        ("fit_corte_x31.png", "Corte pelo encoder (x = 31): as duas abas da plaquinha dos knobs; a da frente entra num rebaixo da parede da caixa do alto-falante."),
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
  <title>BeatConfused | eTuttino Pocket · revisão F3</title>
  <meta name="description" content="eTuttino Pocket: o case Seixo, variante B, com micro-USB de painel, rebaixos dos knobs e acesso ao botão do Teensy (SPEC v5, F3)." />
  <!-- Review page for J (SPEC v5, task F3). Portuguese only, unlisted:
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
      <p class="family-lead">O case do Pocket na SPEC v5 (tarefa F3): sem a plaquinha do painel, o micro-USB vem do Teensy por uma
      fita FPC até a parede, o fone é de painel com fios, as porcas dos knobs ficam escondidas num rebaixo e dá para apertar o botão do
      Teensy com um clipe sem abrir o case. Tudo conferido peça por peça contra as medidas da eletrônica. {n(pj['length'])} × 100 mm.</p>
      <p><span class="family-tag">Parte física fechada · para revisar</span></p>
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
      <h2>O que mudou na v5 (F3)</h2>
      <ul>
        <li><strong>Micro-USB de painel em fita FPC</strong>: o cabo redondo de 4,5 mm com raio ≥ 18 não cabia (o máximo possível era
        R 13 no laço e R 7 no plugue). A eletrônica trocou pela extensão em fita: macho de 90° "UP" no Teensy, a fita sobe, dobra chata
        sob o bloco e entra na fêmea. A fêmea desliza num túnel até um ressalto de 0,5 na parede, e uma trava impressa com 2 parafusos M2
        segura por trás.</li>
        <li><strong>Fone de painel Cliff FC681375V</strong>, ligado por fios, numa face plana própria; porca de Ø 10 por fora, nervura
        contra o giro por dentro.</li>
        <li><strong>Rebaixo de Ø 14 × 2 sob os dois knobs</strong>: a porca M7 do volume fica rente com a tampa, coberta pelo knob;
        o seletor tem o mesmo rebaixo. Uma chave de porca impressa entra no rebaixo.</li>
        <li><strong>Botão de gravação do Teensy</strong>: furo de Ø 1,6 na tampa, à direita do logo, com tubo-guia até o Teensy.</li>
        <li>Saíram a plaquinha do painel, o ressalto dela, o pino, a costela e a aba.</li>
      </ul>
      <h2>Na v4 (F1)</h2>
      <ul>
        <li><strong>Logo reto</strong> (horizontal), centrado na zona de trás da interface, 0,4 de fundo; a casca de cima é de resina.</li>
        <li><strong>Bolso do plugue da bateria</strong> de {n(bt['pocket_inside'][0])} × {n(bt['pocket_inside'][1])} × {n(bt['pocket_inside'][2])}
        para o par JST PH encaixado.</li>
        <li><strong>Abas da plaquinha dos knobs</strong>: a de trás passa por cima da Audio Board; a da frente entra num rebaixo
        da parede da caixa do alto-falante, que continua fechada.</li>
        <li><strong>Materiais</strong>: casca de cima em resina; fundo, tampinha da bateria, fundo da caixa, trava e chave em MJF; capas em resina.</li>
      </ul>
      <h2>Desde o D1</h2>
      <ul>
        <li><strong>Potenciômetro com chave</strong> (o pedido da SPEC sem subir a tampa): um de 9 mm deitado, numa plaquinha em pé
        à direita do eixo, preso na tampa pela porca da rosca M7. O corpo pendura até 14,5 mm, por cima da bateria.</li>
        <li><strong>Bateria</strong> no berço pedido (58,5 × 36,5 × 7,6, já com os 8 % de inchaço), no fundo da parte da frente da
        interface, fora da placa principal. Sai por uma tampinha de 2 parafusos no fundo, sem abrir a tampa; o plugue dela se
        encaixa num bolso dentro do próprio berço.</li>
        <li><strong>Pilha baixa</strong> (Teensy soldado direto na Audio Board, como a eletrônica prefere): 8,7 mm em vez de 13.</li>
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
