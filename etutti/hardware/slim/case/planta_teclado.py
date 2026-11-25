"""eTutti Slim (R6SL): keyboard plan with the note name on every button (naturals white, sharps black, C and F with the tactile dimple). Stdlib only.

    python etutti/hardware/slim/case/planta_teclado.py   -> case/img/planta_teclado.{svg,png}

View from above, player at the bottom (row 1 nearest).  Button head D15; hole D11 (dashed); case outline from case.py's plan.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_slim as L  # noqa: E402

IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
SC = 5.0
X0, Y1 = -105.0, 70.0
LEFT, RIGHT, FRONT, BACK = -98.0, 149.0, -18.5, 70.6


def px(x):
    return 20 + (x - X0) * SC


def py(y):
    return 70 + (Y1 - y) * SC


def main():
    W, H = int(20 + (RIGHT - X0 + 8) * SC), int(70 + (Y1 - FRONT + 8) * SC + 60)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif"><rect width="100%%" height="100%%" fill="#fbfaf6"/>' % (W, H, W, H)]
    o.append('<text x="20" y="28" font-size="17" font-weight="bold">eTutti Slim R6SL - planta do teclado com o nome da nota em cada botao (vista de cima, jogador embaixo)</text>')
    o.append('<text x="20" y="50" font-size="12" fill="#555">naturais brancas, sustenidos pretos, C e F brancos com a pontilhado diagonal tatil (quadrados de 0,5, fundo 0,18, passo 1,1, em D11); botao D15, furo do tampo D11; passo 18,5, fileiras 16,02; mm</text>')
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="#f1ece0" stroke="#776" stroke-width="2"/>' % (px(LEFT), py(BACK), (RIGHT - LEFT) * SC, (BACK - FRONT) * SC, 6 * SC))
    for r in range(4):
        for k in range(L.NKEYS):
            x, y, n = L.ROW_X0[r] + L.P * k, L.ROW_Y[r], L.NOTES[r][k]
            sharp = "#" in n
            cf = n[0] in "CF" and not sharp
            fill, ink = ("#1d1d1f", "#fff") if sharp else ("#ffffff", "#1d1d1f")
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#aaa" stroke-width="0.8" stroke-dasharray="3,2"/>' % (px(x), py(y), 5.5 * SC))
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#222" stroke-width="1.5"/>' % (px(x), py(y), 7.5 * SC, fill))
            if cf:
                o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#f1efe8" stroke="#999" stroke-width="0.6"/>' % (px(x), py(y), 5.5 * SC))
                for i_ in range(-9, 10):
                    for j_ in range(-9, 10):
                        dx, dy = (i_ - j_) * 1.1 / 2 ** 0.5, (i_ + j_) * 1.1 / 2 ** 0.5
                        if (dx * dx + dy * dy) ** 0.5 + 0.36 <= 5.5:
                            o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#8a8575" transform="rotate(45 %.2f %.2f)"/>' % (px(x + dx) - 0.25 * SC, py(y + dy) - 0.25 * SC, 0.5 * SC, 0.5 * SC, px(x + dx), py(y + dy)))
                o.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle" fill="%s">%s</text>' % (px(x), py(y) + 5, '#000', n))
            else:
                o.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle" fill="%s">%s</text>' % (px(x), py(y) + 5, ink, n))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#555">fileira %d</text>' % (px(LEFT) + 6, py(L.ROW_Y[r]) + 4, r + 1))
    o.append('<text x="20" y="%d" font-size="12" fill="#555">C e F: o nome fica sobre o pontilhado. Fileira 1 = a mais perto do jogador e a mais baixa; degraus 2 / 2 / 3 mm.</text>' % (H - 20))
    o.append("</svg>")
    path = os.path.join(IMG, "planta_teclado.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(IMG, "planta_teclado.png"), "--window-size=%d,%d" % (W, H), "file:///" + path.replace("\\", "/")], capture_output=True)
    print(path)


if __name__ == "__main__":
    main()
