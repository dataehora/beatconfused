"""eTutti Slim (R5SL): keyboard plan with the note name on every button (naturals white, sharps black, C and F with the tactile dimple). Stdlib only.

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
    o.append('<text x="20" y="28" font-size="17" font-weight="bold">eTutti Slim R5SL - planta do teclado com o nome da nota em cada botao (vista de cima, jogador embaixo)</text>')
    o.append('<text x="20" y="50" font-size="12" fill="#555">naturais brancas, sustenidos pretos, C e F brancos com a covinha tatil (D5,0 x 0,4 no domo); botao D15, furo do tampo D11; passo 18,5, fileiras 16,02; mm</text>')
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
                o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#e3ded0" stroke="#999" stroke-width="1"/>' % (px(x), py(y), 2.5 * SC))
                o.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle" fill="%s">%s</text>' % (px(x), py(y) + 22, ink, n))
            else:
                o.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle" fill="%s">%s</text>' % (px(x), py(y) + 5, ink, n))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#555">fileira %d</text>' % (px(LEFT) + 6, py(L.ROW_Y[r]) + 4, r + 1))
    o.append('<text x="20" y="%d" font-size="12" fill="#555">C e F: o nome fica abaixo da covinha. Fileira 1 = a mais perto do jogador e a mais baixa; degraus 2 / 2 / 3 mm.</text>' % (H - 20))
    o.append("</svg>")
    path = os.path.join(IMG, "planta_teclado.svg")
    open(path, "w", encoding="utf-8").write("\n".join(o))
    edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    if os.path.exists(edge):
        subprocess.run([edge, "--headless", "--screenshot=" + os.path.join(IMG, "planta_teclado.png"), "--window-size=%d,%d" % (W, H), "file:///" + path.replace("\\", "/")], capture_output=True)
    print(path)


if __name__ == "__main__":
    main()
