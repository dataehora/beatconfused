# eTuttino — conferência da eletrônica no case (SPEC item 9)

Gerado por `fit_check.py` a partir de `case.py` (CadQuery). As peças são sólidos com as medidas de datasheet ou da placa atual; as incertas estão marcadas *conferir* no código. Coordenadas da SPEC (y para quem toca). Folga = menor distância entre a peça e o case (tampa + fundo).

## Resumo

- **eTuttino (sem tela), pilha atual (soquetes 8,5 mm, 19,8 mm): não cabe** — colide: plugue micro-USB 90°.
- **eTuttiChorus (tela + alto-falante), pilha atual (soquetes 8,5 mm, 19,8 mm): não cabe** — colide: Teensy 4.0 × conector da tela, Teensy 4.0 × tela 1,9" (módulo), chips do Teensy × conector da tela, chips do Teensy × tela 1,9" (módulo), micro-USB do Teensy × tela 1,9" (módulo), pinos + solda no Teensy × tela 1,9" (módulo), plugue micro-USB 90°, plugue micro-USB 90° × tela 1,9" (módulo).
- **eTuttino (sem tela), pilha baixa (Teensy soldado na Audio Board, 11,3 mm): cabe.**
- **eTuttiChorus (tela + alto-falante), pilha baixa (Teensy soldado na Audio Board, 11,3 mm): cabe.**

**Condições para caber (pilha B):**

1. Teensy mais baixo que hoje. O espaço entre a Audio Board e o Teensy pode ser no máximo 9.7 mm no eTuttino (Seixo) / 9.2 mm (Madeira) e 4.7 / 4.2 mm no Chorus. Hoje são 11 mm (soquete 8,5 + espaçador 2,5). Teensy soldado direto nos pinos da Audio Board (2,5 mm, como a PJRC monta) cabe em todos. No eTuttino, um soquete baixo (~4–5 mm) ainda deixa o Teensy removível.
2. Plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura) no cabo até o USB de painel.
3. Peças de painel com no máximo ~10 mm de corpo atrás do inserto: senão batem no potenciômetro (x = 20). Na Madeira a parede é afinada para 2.5 mm em volta do inserto (bolsão por dentro).
4. Potenciômetro, encoder e LED numa plaquinha sob a tampa, com pernas cortadas rente (~1,5 mm). Por baixo dela passa a borda da Audio Board, com o jack dela.
5. O jack de painel ligado por fio aos pinos de fone da Audio Board, ou por um plugue de 90°. Um plugue reto de 3,5 mm não cabe entre a Audio Board e a parede.

## 0. Antes de tudo: a grade das teclas mudou

A SPEC põe as fileiras a **16,5 mm** uma da outra (74,8 / 58,3 / 41,8 / 25,3), com meio passo de deslocamento: uma grade hexagonal (19,05 × cos 30° = 16,50), onde cada botão fica a 19,05 mm dos seis vizinhos. A PCB atual (`generate.py`, PR #77/#78) tem as fileiras a **19,05 mm** (grade MX retangular, 267 × 97,2 mm). Ou seja, **a placa atual não serve neste case**: a PCB e a placa de switches têm que ser refeitas na grade nova. Notas, fileiras e firmware não mudam (a ordem C-griff é a mesma), só a geometria. Cabe com folga: switches a 2,5 mm entre fileiras (16,5 − 14), carcaça de cima a 1,5 mm, e sobram ~15 mm atrás da fileira 4 e na frente da fileira 1 para os multiplexadores, como hoje.

## 1. Teensy + Audio Board, tela, knobs, LED, alto-falante e conectores (9.1)

**Largura útil.** O ponto mais estreito da área de interface, na fileira 2, tem 61.7 mm em cima (x = 0 até o começo do declive, x = 61.7: o arco R 32,8 em volta do botão G3 corta o vértice vivo 56,6 da SPEC). A cavidade com altura total vai de x = 2.5 a 59.2 no Seixo (56.7 mm) e de 4.0 a 57.7 na Madeira (53.7 mm). Os ~68 mm da SPEC são o vértice da abertura das teclas (68,49), não o espaço interno. Abaixo do declive a cavidade continua (o teto desce até a tampa das teclas, z = 12.7), então peças baixas podem ir mais para a direita.

**Arranjo testado** (vista de cima em `renders/fit_top.png`): placa principal estendida para a esquerda por baixo da interface (uma placa só; a pilha continua presa só pelas pernas dos headers). A pilha fica no canto de trás, fileira VIN atrás, USB virado para a face esquerda: Audio Board em x 20–60, y 5–43.7; Teensy em y 13.2–31.0. A borda esquerda fica a 20 mm da parede para caber o plugue USB de 90° e as peças de painel. Potenciômetro, encoder e LED vão numa plaquinha de interface pendurada sob a tampa (y 37–53), por cima da borda da Audio Board.

### Pilha A — pilha atual (soquetes 8,5 mm, 19,8 mm)

Topo do Teensy z = 24.9, topo do micro-USB z = 27.5, plugue USB de 90° até z = 29.9. Teto interno sobre o Teensy: z = 29.4 (Seixo) / 28.9 (Madeira).

| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |
|---|---|---|---|---|
| Audio Board | ok (2.5 mm) | ok (1.0 mm) | ok (2.5 mm) | ok (1.0 mm) |
| jack da Audio Board | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| codec | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| barra de pinos | ok (5.6 mm) | ok (5.1 mm) | ok (5.6 mm) | ok (5.1 mm) |
| pinos + solda no Teensy | ok (2.7 mm) | ok (2.2 mm) | ok (2.7 mm) | ok (2.2 mm) |
| Teensy 4.0 | ok (4.0 mm) | ok (3.5 mm) | ok (4.0 mm) | ok (3.5 mm) |
| chips do Teensy | ok (3.3 mm) | ok (2.8 mm) | ok (3.3 mm) | ok (2.8 mm) |
| micro-USB do Teensy | ok (1.7 mm) | ok (1.2 mm) | ok (1.7 mm) | ok (1.2 mm) |
| plugue micro-USB 90° | **colide** (67.3 mm³) | **colide** (127.8 mm³) | **colide** (67.3 mm³) | **colide** (127.8 mm³) |
| placa de interface | ok (6.0 mm) | ok (4.6 mm) | ok (6.0 mm) | ok (4.6 mm) |
| potenciômetro | justo (0.25 mm) | justo (0.25 mm) | justo (0.25 mm) | justo (0.25 mm) |
| potenciômetro (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| LED 3 mm | ok (1.5 mm) | ok (1.5 mm) | ok (1.5 mm) | ok (1.5 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.30 mm) | justo (0.30 mm) |

Entre peças (menos de 1 mm):

- Audio Board × barra de pinos — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- jack da Audio Board × potenciômetro (pernas) — Chorus Madeira: justo (0.32 mm); Chorus Seixo: ok (0.8 mm); eTuttino Madeira: justo (0.32 mm); eTuttino Seixo: ok (0.8 mm)
- jack da Audio Board × encoder (pernas) — Chorus Madeira: justo (0.32 mm); Chorus Seixo: ok (0.8 mm); eTuttino Madeira: justo (0.32 mm); eTuttino Seixo: ok (0.8 mm)
- barra de pinos × Teensy 4.0 — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- pinos + solda no Teensy × Teensy 4.0 — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- Teensy 4.0 × micro-USB do Teensy — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- micro-USB do Teensy × plugue micro-USB 90° — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × potenciômetro — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × potenciômetro (pernas) — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × encoder — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × encoder (pernas) — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × LED 3 mm — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- placa de interface × jack de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- pinos + solda no Teensy × tela 1,9" (módulo) — Chorus Madeira: **colide** (61.2 mm³); Chorus Madeira: **colide** (69.7 mm³); Chorus Seixo: **colide** (36.3 mm³); Chorus Seixo: **colide** (69.7 mm³)
- Teensy 4.0 × tela 1,9" (módulo) — Chorus Madeira: **colide** (152.8 mm³); Chorus Seixo: **colide** (8.6 mm³)
- Teensy 4.0 × conector da tela — Chorus Madeira: **colide** (60.2 mm³); Chorus Seixo: **colide** (64.1 mm³)
- chips do Teensy × tela 1,9" (módulo) — Chorus Madeira: **colide** (89.8 mm³); Chorus Seixo: **colide** (61.1 mm³)
- chips do Teensy × conector da tela — Chorus Madeira: **colide** (0.0 mm³); Chorus Seixo: **colide** (7.1 mm³)
- micro-USB do Teensy × tela 1,9" (módulo) — Chorus Madeira: **colide** (104.7 mm³); Chorus Seixo: **colide** (93.1 mm³)
- plugue micro-USB 90° × tela 1,9" (módulo) — Chorus Madeira: **colide** (484.6 mm³); Chorus Seixo: **colide** (484.6 mm³)
- barra de pinos × tela 1,9" (módulo) — Chorus Madeira: ok (0.9 mm)
- USB de painel × tela 1,9" (módulo) — Chorus Madeira: ok (0.6 mm)

### Pilha B — pilha baixa (Teensy soldado na Audio Board, 11,3 mm)

Topo do Teensy z = 16.4, topo do micro-USB z = 19.0, plugue USB de 90° até z = 21.4. Teto interno sobre o Teensy: z = 29.4 (Seixo) / 28.9 (Madeira).

| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |
|---|---|---|---|---|
| Audio Board | ok (2.5 mm) | ok (1.0 mm) | ok (2.5 mm) | ok (1.0 mm) |
| jack da Audio Board | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| codec | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| barra de pinos | ok (10.3 mm) | ok (9.2 mm) | ok (10.3 mm) | ok (9.2 mm) |
| pinos + solda no Teensy | ok (11.2 mm) | ok (9.8 mm) | ok (11.2 mm) | ok (9.8 mm) |
| Teensy 4.0 | ok (10.7 mm) | ok (9.2 mm) | ok (10.7 mm) | ok (9.2 mm) |
| chips do Teensy | ok (11.8 mm) | ok (11.3 mm) | ok (11.8 mm) | ok (11.3 mm) |
| micro-USB do Teensy | ok (10.2 mm) | ok (9.7 mm) | ok (10.2 mm) | ok (9.7 mm) |
| plugue micro-USB 90° | ok (6.8 mm) | ok (6.8 mm) | ok (6.8 mm) | ok (6.8 mm) |
| placa de interface | ok (6.0 mm) | ok (4.6 mm) | ok (6.0 mm) | ok (4.6 mm) |
| potenciômetro | justo (0.25 mm) | justo (0.25 mm) | justo (0.25 mm) | justo (0.25 mm) |
| potenciômetro (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| LED 3 mm | ok (1.5 mm) | ok (1.5 mm) | ok (1.5 mm) | ok (1.5 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.30 mm) | justo (0.30 mm) |

Entre peças (menos de 1 mm):

- Audio Board × barra de pinos — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- jack da Audio Board × potenciômetro (pernas) — Chorus Madeira: justo (0.32 mm); Chorus Seixo: ok (0.8 mm); eTuttino Madeira: justo (0.32 mm); eTuttino Seixo: ok (0.8 mm)
- jack da Audio Board × encoder (pernas) — Chorus Madeira: justo (0.32 mm); Chorus Seixo: ok (0.8 mm); eTuttino Madeira: justo (0.32 mm); eTuttino Seixo: ok (0.8 mm)
- barra de pinos × Teensy 4.0 — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- pinos + solda no Teensy × Teensy 4.0 — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- Teensy 4.0 × micro-USB do Teensy — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- micro-USB do Teensy × plugue micro-USB 90° — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × potenciômetro — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × potenciômetro (pernas) — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × encoder — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × encoder (pernas) — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × LED 3 mm — Chorus Madeira: justo (0.00 mm); Chorus Seixo: justo (0.00 mm); eTuttino Madeira: justo (0.00 mm); eTuttino Seixo: justo (0.00 mm)
- placa de interface × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- placa de interface × jack de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- USB de painel × tela 1,9" (módulo) — Chorus Madeira: ok (0.6 mm)

## 2. Altura dos eixos (9.2)

Knob Ø9 a 0.8 mm da superfície, eixo entrando 6 mm no knob. Superfície em y = 45: z = 30.75.

| Montagem | Comprimento L do eixo (da face de montagem) | Padrão EC11 / RK09 |
|---|---|---|
| plaquinha sob a tampa, Seixo | 16.3 mm | L = 15 (-1.3 mm no knob) |
| plaquinha sob a tampa, Madeira | 16.8 mm | L = 15 (-1.8 mm no knob) |
| na placa principal (z 7.7) | 29.8 mm | L = 30 (+0.2 mm no knob) |

Na placa principal os corpos (z 7.7–14.2) bateriam na Audio Board/jack na pilha do canto de trás, e o eixo de 30 mm fica comprido e com folga lateral; a plaquinha sob a tampa usa eixos L = 15 (os mais comuns) e deixa os knobs baixos. O LED de 3 mm na mesma plaquinha precisa ficar 4.2 mm acima dela no Seixo (ponta rente ao furo) e 3.9 mm na Madeira (por baixo da pele de 0.8 mm): um espaçador de LED resolve.

## 3. Saias de 17 mm (9.3)

- Vizinhos: passo 19,05 nas seis direções (a grade é hexagonal), saias Ø17 → **2,05 mm** entre saias. Ok para dedos e para imprimir; não dá para aumentar a saia além de ~18 mm.
- Saia × borda da abertura: 6.5 mm na frente/atrás e 14.0 mm nas laterais (a folga da SPEC é medida do Ø15).
- Saia × carcaça do switch: uma saia redonda Ø17 (Ø15,4 por dentro) sobre a carcaça quadrada do MX bate nos cantos se descer muito. Com curso de 4.0 mm a base da saia tem que ficar a **10.1 mm acima da placa** com a tecla solta (z = 22.82), e a capa fica com 3.68 mm de altura até o topo (z = 26,5) — um domo baixo de fato, com o tubo da haste por baixo. Consequência visual: entre a tampa (z 15,7) e a saia aparecem ~7 mm da carcaça do switch — por isso carcaça escura. Números de carcaça e haste são MX nominais: conferir com o Gateron KS-20 e com o teste de 4 capas.

## 4. Espessura de parede (9.4)

| | Seixo (resina/MJF) | Madeira (carvalho, CNC) |
|---|---|---|
| Paredes laterais | 2.5 mm | 4.0 mm |
| Tampa da interface | 2.5 mm | 3.0 mm |
| Tampa em volta das teclas | 3.0 mm (z 12.7–15.7, apoiada na placa) | igual |
| Borda da abertura | arredondado 4 × 2.0 + 1.0 mm reto | igual — é o ponto mais frágil na madeira |
| Teia da grade | 2.1 mm entre furos | igual |
| Fundo | 2.0 mm, encaixado dentro das paredes | 2.0 mm |
| LED | furo Ø3.5 | pele de 0.8 mm por cima |

- Resina e MJF: 2,5 mm é confortável (mínimo prático ~1,5–2). A borda de 1 mm da abertura passa, mas é melhor 1,2+ em resina frágil.
- Madeira: 4 mm nas paredes e 3 mm na tampa são o mínimo sensato para carvalho. A borda da abertura (1 mm de altura reta, fibra cruzada nas pontas do hexágono) pode lascar: aumentar `CHAMFER_DROP`/`LID_T` só na Madeira ou deixar a borda mais grossa. Pele de 0,8 mm de carvalho branco quase não deixa a luz passar: testar numa sobra (0,5 mm e um LED forte costumam ser necessários).
- A SPEC diz "fresagem de 3 eixos de cima, numa fixação só" incluindo o bolsão interno — não dá: o bolsão é por baixo. São **duas fixações**: de cima (contorno, abertura, arredondado, rebaixo da tela, furos) e virada (bolsão, rebaixo do fundo, bosses, teto inclinado da interface com fresa de topo esférico). Os cantos internos do bolsão já têm raio ≥ 12 mm.

## 5. Outras observações da SPEC

- O texto do item 4 diz que a borda de cima do declive é "abertura + 20,3", mas o vértice que ele dá, (56,6; 58,3), é abertura + 10,3 — o espelho do lado direito. Usei o vértice (`TRANS_TOP_OFF = 10.3`).
- O contorno da grade passa ~1,2 mm da borda do declive no canto (75,5; 89). Os furos que cairiam no declive são descartados (`GRILLE_KEEP`); sobram 107 furos.
- Os vértices da caixa da SPEC usam a frente em y = 100,1 (74,8 + 15 + 10,3); o modelo prende a frente em y = 100 (diferença de 0,05 mm no x do vértice da frente).
- O sistema de coordenadas da SPEC é canhoto (x direita, y para quem toca, z para cima). Modelado ao pé da letra, o instrumento sai espelhado num CAD. Os arquivos exportados são espelhados para y = 100 − y_SPEC (y para trás), e o instrumento fica certo: interface à esquerda de quem toca.
