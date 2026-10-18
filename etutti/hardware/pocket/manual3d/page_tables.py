"""Writes the generated parts of the Pocket's assembly manual
(etutti/pocket/manual/index.html), between its BEGIN/END markers:

    python page_tables.py        (stdlib)

  table:bom   the kit BOM, from pcb/fab/pocket_kit_bom.csv (eletrônica's)
  svg:ctl     wiring of the SH-10 controls cable (MANUAL_ELETRICO.md 6.1)
  svg:pnl     wiring of the SH-8 panel cable and the micro-B cable (6.2)
  svg:bat     the battery plug x pigtail x J_BAT polarity check (7.2)
"""
import csv
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
POCKET = os.path.dirname(HERE)
PAGE = os.path.normpath(os.path.join(POCKET, "..", "..", "pocket", "manual", "index.html"))
BOM = os.path.join(POCKET, "pcb", "fab", "pocket_kit_bom.csv")
WIRE = {"preto": "#1a1a1a", "vermelho": "#c0392b", "laranja": "#e67e22", "amarelo": "#f1c40f", "verde": "#27ae60",
        "azul": "#2e86c1", "roxo": "#8e44ad", "cinza": "#9aa1a6", "branco": "#d8d8d8", "marrom": "#7b4a2a"}
E = html.escape


def bom_table():
    rows = list(csv.DictReader(open(BOM, encoding="utf-8")))
    out = ['<div class="table-wrap"><table><thead><tr><th>Grupo</th><th>Item</th><th>Por Pocket</th><th>Comprar</th>'
           '<th>Onde / código</th><th>Obs.</th></tr></thead><tbody>']
    for r in rows:
        link = r["link"].strip()
        where = E(r["fornecedor"])
        code = r["código"].strip()
        if code and code != "-":
            where += " · " + E(code)
        if link.startswith("http"):
            where = '<a href="%s" rel="noopener">%s</a>' % (E(link, quote=True), where)
        tag = ' <span class="tag tag-none">conferir</span>' if r["status"].strip() == "conferir" else ""
        out.append("<tr><td>%s</td><td><strong>%s</strong><br /><small>%s</small>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            E(r["grupo"]), E(r["item"]), E(r["peça"]), tag, E(r["por Pocket"]), E(r["comprar"]), where, E(r["observação"])))
    out.append("</tbody></table></div>")
    return "\n        ".join(out)


def wiring(title, left, rows, right_groups, caption, height=None):
    """A wiring figure: a connector (left) with numbered pins, one line per
    wire to its pad on a board (right). rows: (pin, signal, colour, group, pad)."""
    row_h = 22
    top = 34
    h = height or top + row_h * len(rows) + 20
    w = 640
    s = ['<figure><svg class="wiring" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (w, h, E(title, quote=True)),
         '<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>' % (w, h),
         '<text x="12" y="20" font-weight="700">%s</text>' % E(left),
         '<rect x="12" y="%d" width="60" height="%d" rx="4" fill="#f1eee5" stroke="#221e1b"/>' % (top - 10, row_h * len(rows))]
    groups = {}
    for i, (pin, sig, col, grp, pad) in enumerate(rows):
        y = top + i * row_h + 1
        s.append('<text x="22" y="%d">%s</text>' % (y + 4, E(str(pin))))
        s.append('<text x="84" y="%d">%s</text>' % (y + 4, E(sig)))
        s.append('<line x1="72" y1="%d" x2="380" y2="%d" stroke="%s" stroke-width="5" stroke-linecap="round"/>' % (y, y, WIRE[col]))
        s.append('<line x1="72" y1="%d" x2="380" y2="%d" stroke="#221e1b" stroke-width="0.6" stroke-opacity="0.5"/>' % (y - 2.5, y - 2.5))
        s.append('<text x="300" y="%d" text-anchor="end" fill="#6b6b6b">%s</text>' % (y - 5, E(col)))
        s.append('<text x="392" y="%d" font-weight="600">%s</text>' % (y + 4, E(pad)))
        groups.setdefault(grp, []).append(y)
    for grp, ys in groups.items():
        y0, y1 = min(ys) - 10, max(ys) + 10
        s.append('<rect x="450" y="%d" width="180" height="%d" rx="5" fill="#f6d58f" stroke="#221e1b"/>' % (y0, y1 - y0))
        s.append('<text x="540" y="%d" text-anchor="middle" font-weight="600">%s</text>' % ((y0 + y1) / 2 + 4, E(grp)))
    s.append("</svg><figcaption>%s</figcaption></figure>" % caption)
    return "\n        ".join(s)


def ctl():
    rows = [(1, "VCC", "vermelho", "plaquinha do volume (11), face de trás", "JW1"),
            (2, "POT", "laranja", "plaquinha do volume (11), face de trás", "JW2"),
            (3, "GND", "preto", "plaquinha do volume (11), face de trás", "JW3"),
            (4, "PWR_A (chave)", "amarelo", "plaquinha do volume (11), face de trás", "JW4"),
            (5, "PWR_B (chave)", "verde", "plaquinha do volume (11), face de trás", "JW5"),
            (6, "ENC_A", "azul", "plaquinha dos knobs (10), borda direita", "JW6"),
            (7, "ENC_B", "roxo", "plaquinha dos knobs (10), borda direita", "JW7"),
            (8, "ENC_SW", "cinza", "plaquinha dos knobs (10), borda direita", "JW8"),
            (9, "LED_R", "branco", "plaquinha dos knobs (10), borda direita", "JW9"),
            (10, "LED_G", "marrom", "plaquinha dos knobs (10), borda direita", "JW10")]
    rows = [(p, s_, c, g.split(",")[0], pad) for p, s_, c, g, pad in rows]
    return wiring("Esquema do cabo dos knobs", "J_CTL (SH 10)", rows, None,
                  "Cabo dos knobs (21): o conector fica no J_CTL da placa principal; a outra ponta é cortada e soldada. "
                  "As cores são só exemplo: o que vale é o número do fio, contado do pino 1 (lado marcado do conector).")


def pnl():
    rows = [(1, "VBUS", "vermelho", "plaquinha do painel (16)", "TP1"), (2, "VBUS", "vermelho", "plaquinha do painel (16)", "TP1"),
            (3, "GND", "preto", "plaquinha do painel (16)", "TP4"), (4, "GND", "preto", "plaquinha do painel (16)", "TP4"),
            (5, "HP_L", "azul", "plaquinha do painel (16)", "TP5"), (6, "HP_R", "verde", "plaquinha do painel (16)", "TP6"),
            (7, "HP_VGND", "roxo", "plaquinha do painel (16)", "TP7"), (8, "HP_TIPSW", "amarelo", "plaquinha do painel (16)", "TP8"),
            ("µB 1", "VBUS", "vermelho", "plaquinha do painel (16)", "TP1"), ("µB 3", "D+", "verde", "plaquinha do painel (16)", "TP2"),
            ("µB 2", "D−", "branco", "plaquinha do painel (16)", "TP3"), ("µB 5", "GND", "preto", "plaquinha do painel (16)", "TP4")]
    return wiring("Esquema do cabo do painel e do cabo micro-B", "J_PNL (SH 8) · cabo micro-B (19)", rows, None,
                  "Em cima, o cabo do painel (20), do J_PNL: VBUS e GND usam dois fios cada (TP1 e TP4, junto com os do cabo micro-B); "
                  "TP5 a TP8 ficam na ponta direita, depois do jack. Embaixo, o cabo micro-B (19), cortado a ~40 mm do plugue: "
                  "vermelho VBUS, verde D+, branco D−, preto GND (cores USB comuns; confira com o multímetro).")


def bat():
    rows = [(1, "BAT+", "vermelho", "plugue da bateria (27)", "verm. +"),
            (2, "NTC", "amarelo", "plugue da bateria (27)", "NTC"),
            (3, "GND", "preto", "plugue da bateria (27)", "preto −")]
    return wiring("Polaridade da bateria", "J_BAT · rabicho", rows, None,
                  "Antes de encaixar a bateria: o fio vermelho dela tem de cair no pino que vai ao J_BAT 1, o NTC no 2 e o preto "
                  "no 3. A ordem dos fios muda entre vendedores; se não bater, troque os terminais na carcaça do rabicho (28).")


def main():
    page = open(PAGE, encoding="utf-8").read()
    for key, fn in (("table:bom", bom_table), ("svg:ctl", ctl), ("svg:pnl", pnl), ("svg:bat", bat)):
        pat = re.compile(r"(<!-- BEGIN %s -->)(.*?)(\s*<!-- END %s -->)" % (re.escape(key), re.escape(key)), re.S)
        assert pat.search(page), key
        page = pat.sub(lambda m: m.group(1) + "\n        " + fn() + m.group(3), page)
    open(PAGE, "w", encoding="utf-8", newline="\n").write(page)
    print("wrote", PAGE)


if __name__ == "__main__":
    main()
