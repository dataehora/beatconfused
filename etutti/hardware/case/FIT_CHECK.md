# eTuttino — conferência do case (SPEC v5 + passo 18,5)

Gerado por `fit_check.py` a partir de `case.py` (CadQuery). As peças são sólidos com medidas de datasheet, da placa atual ou medidas por você; as incertas estão marcadas CHECK no código. Coordenadas da SPEC (y para quem toca). Folga = menor distância entre a peça e o case (tampa + fundo).

Modelo da SPEC v5 com três decisões do usuário tomadas depois dela, para entrar na v6: **passo 18,5 mm** (grade hexagonal mantida), **fim da rampa com a curva até 75° e reta até a face** (ver §5), e pilha Teensy + Audio Board de **~13 mm no eTuttino** e **reduzida em 3–4 mm (≤ 10 mm) no Chorus**.

## Resumo

- **eTuttino (sem tela), pilha montada (13 mm): cabe.**
- **eTuttiChorus (tela + alto-falante), pilha montada (13 mm): não cabe** — colide: plugue micro-USB 90° × tela 1,9" (módulo).
- **eTuttino (sem tela), pilha reduzida (10 mm): cabe.**
- **eTuttiChorus (tela + alto-falante), pilha reduzida (10 mm): cabe.**

Pilha mais alta que cabe (de baixo da Audio Board ao topo do USB do Teensy): **16.9 mm** no eTuttino Seixo, 16.4 mm no eTuttino Madeira, **12.1 mm** no Chorus Seixo e 11.6 mm no Chorus Madeira. A sua pilha tem ~13 mm.

## 1. Teclado: passo 18.50 mm, grade hexagonal

Cada botão fica a **18.50 mm** dos seis vizinhos (lados e diagonais iguais, triângulos equiláteros). As fileiras ficam a 18.50 × cos 30° = **16.02 mm** uma da outra, em y = 74.03, 58.01, 41.99, 25.97 (fileira 1 → 4). Folga da abertura: 8.2 mm na frente e atrás, 15 nas laterais. Comprimento total **331.1 mm**.

Medidas do Gateron KS-20 (desenho oficial KS-20TF10B045NW-X72): carcaça de cima 15,40 × 15,10 mm, 11,10 mm da PCB ao topo da carcaça, placa a 5,00 mm, furo 14,00, curso 4,1 ± 0,2.

| Conferência | Folga |
|---|---|
| Carcaça × carcaça, mesma fileira | 3.10 mm |
| Carcaça × carcaça, diagonal (fileira vizinha) | 0.92 mm (é o limite: passo mínimo ≈ 17,8 mm) |
| Teia da placa entre furos 14 × 14 | 2.02 mm entre fileiras, 4.50 mm na fileira |
| Botão Ø15 × vizinho | 3.50 mm |
| Saia Ø17 × vizinha | 1.50 mm |
| Saia × borda da abertura | 7.2 mm frente/trás, 14.0 mm laterais |
| Switches × case | 0.0 mm (Seixo), 0.0 mm (Madeira) |

**Capas.** A saia redonda (Ø17, parede de 0.8 mm) não pode descer até os cantos da carcaça retangular do Gateron. Com o curso de 4.1 mm, a base da saia fica a **9.78 mm acima da placa** com a tecla solta (z = 22.48; apertada, 5.68 mm). A capa tem **4.02 mm** da base da saia ao topo (z = 26.5), com o tubo da haste por baixo. Entre a tampa (z 15.7) e a saia aparecem ~6.8 mm da carcaça escura. O topo da carcaça e a altura da haste não estão cotados no desenho do Gateron: o `keycap_test_4.stl` (4 capas) confirma isso nos switches reais.

## 2. Teensy + Audio Board, tela, knobs, LED, alto-falante e conectores

Audio Board **38,0 × 36,8 × 6,7 mm** (anúncio da SB Components, conferido na sua placa), pilha montada de **~13 mm**. Largura útil da interface com altura total, na metade da frente (onde a rampa desce reta, o ponto mais estreito): 54.5 mm no Seixo, 51.5 mm na Madeira. Teto interno: z 30.5 sob a parte plana (Seixo), caindo a 13° até z 20.0 na frente.

**Por baixo da rampa e da tampa à esquerda da fileira 1** (Seixo). Ali o teto é a tampa do teclado: sobram **5.0 mm** acima da PCB (3.5 mm onde a placa de switches passa por cima). Faixa livre de placa de switches, por y: y 62: x 65.8–67.6; y 70: x 65.8–72.2; y 78: x 65.8–76.8; y 86: x 65.8–81.5; y 92: a partir de x 64.1. Cabem peças baixas da placa principal (SMD, multiplexador, LDO, conectores baixos), não a pilha nem o alto-falante. Por baixo da rampa o teto sobe do nível da tampa até o da interface em ~8.7 mm na horizontal.

**Arranjo testado** (`renders/fit_top.png`): placa principal estendida por baixo da interface; pilha no canto de trás, fileira VIN atrás, USB para a face esquerda: Audio Board em x 20–58, y 5–41.8, Teensy em y 12.5–30.3. Potenciômetro, encoder e LED numa plaquinha sob a tampa (y 38–52), por cima da borda da Audio Board.

Ordem dos controles (v5): volume (20; 45), seletor (37; 45), LED (52; 45); tela em x 8–62.

### Pilha montada (13 mm)

Topo do Teensy z = 21.1, topo do micro-USB z = 23.7, plugue USB de 90° até z = 26.2. Teto sobre o Teensy: z = 30.5 (Seixo) / 30.0 (Madeira).

| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |
|---|---|---|---|---|
| Audio Board | ok (2.5 mm) | ok (1.0 mm) | ok (2.5 mm) | ok (1.0 mm) |
| jack da Audio Board | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| codec | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| barra de pinos | ok (10.0 mm) | ok (8.5 mm) | ok (10.0 mm) | ok (8.5 mm) |
| pinos + solda no Teensy | ok (8.0 mm) | ok (7.5 mm) | ok (8.0 mm) | ok (7.5 mm) |
| Teensy 4.0 | ok (9.4 mm) | ok (8.5 mm) | ok (9.4 mm) | ok (8.5 mm) |
| chips do Teensy | ok (8.5 mm) | ok (8.0 mm) | ok (8.5 mm) | ok (8.0 mm) |
| micro-USB do Teensy | ok (6.8 mm) | ok (6.3 mm) | ok (6.8 mm) | ok (6.3 mm) |
| plugue micro-USB 90° | ok (4.3 mm) | ok (3.8 mm) | ok (4.3 mm) | ok (3.8 mm) |
| placa de interface | ok (4.4 mm) | ok (3.1 mm) | ok (4.4 mm) | ok (3.1 mm) |
| potenciômetro | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| potenciômetro (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| LED 3 mm | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.29 mm) | justo (0.29 mm) |

Entre peças (menos de 1 mm, sem contar as que se encostam de propósito):

- placa de interface × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- placa de interface × jack de painel — Chorus Madeira: ok (0.8 mm); Chorus Seixo: ok (1.0 mm); eTuttino Madeira: ok (0.8 mm); eTuttino Seixo: ok (1.0 mm)
- plugue micro-USB 90° × tela 1,9" (módulo) — Chorus Madeira: **colide** (42.4 mm³); Chorus Seixo: justo (0.15 mm)
- chips do Teensy × conector da tela — Chorus Madeira: ok (0.8 mm)

### Pilha reduzida (10 mm)

Topo do Teensy z = 18.1, topo do micro-USB z = 20.7, plugue USB de 90° até z = 23.2. Teto sobre o Teensy: z = 30.5 (Seixo) / 30.0 (Madeira).

| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |
|---|---|---|---|---|
| Audio Board | ok (2.5 mm) | ok (1.0 mm) | ok (2.5 mm) | ok (1.0 mm) |
| jack da Audio Board | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| codec | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| barra de pinos | ok (10.0 mm) | ok (8.5 mm) | ok (10.0 mm) | ok (8.5 mm) |
| pinos + solda no Teensy | ok (10.6 mm) | ok (9.1 mm) | ok (10.6 mm) | ok (9.1 mm) |
| Teensy 4.0 | ok (10.0 mm) | ok (8.5 mm) | ok (10.0 mm) | ok (8.5 mm) |
| chips do Teensy | ok (11.5 mm) | ok (11.0 mm) | ok (11.5 mm) | ok (11.0 mm) |
| micro-USB do Teensy | ok (9.8 mm) | ok (9.3 mm) | ok (9.8 mm) | ok (9.3 mm) |
| plugue micro-USB 90° | ok (5.5 mm) | ok (5.5 mm) | ok (5.5 mm) | ok (5.5 mm) |
| placa de interface | ok (4.4 mm) | ok (3.1 mm) | ok (4.4 mm) | ok (3.1 mm) |
| potenciômetro | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| potenciômetro (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) | ok (8.3 mm) |
| LED 3 mm | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.29 mm) | justo (0.29 mm) |

Entre peças (menos de 1 mm, sem contar as que se encostam de propósito):

- placa de interface × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- placa de interface × jack de painel — Chorus Madeira: ok (0.8 mm); Chorus Seixo: ok (1.0 mm); eTuttino Madeira: ok (0.8 mm); eTuttino Seixo: ok (1.0 mm)

Potenciômetro, encoder, tela e alto-falante aparecem como "justo" (0,2–0,3 mm) de propósito: ficam encostados por baixo da tampa. Figuras: `renders/fit_iso.png`, `fit_top.png` (eTuttino, pilha montada, Seixo, tampa transparente), `fit_section_M.png` (Chorus com a pilha de 13 mm, corte na linha do Teensy) `fit_section_R.png` (pilha reduzida), `fit_top_chorus.png` (Chorus em planta) e `fit_section_x.png` (corte de trás para a frente pelo alto-falante).

**Condições que continuam valendo:** plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura); peças de painel com no máximo ~10 mm de corpo atrás do inserto (na Madeira a parede é afinada para 2.5 mm ali); potenciômetro, encoder e LED numa plaquinha sob a tampa, com pernas cortadas rente; fone de painel ligado por fio à Audio Board (um plugue reto de 3,5 mm não cabe).

## 3. Altura dos eixos

| Montagem | Eixo L (da face de montagem) | Padrão EC11 / RK09 |
|---|---|---|
| plaquinha sob a tampa, Seixo | 16.0 mm | L = 15 (-1.0 mm no knob) |
| plaquinha sob a tampa, Madeira | 16.5 mm | L = 15 (-1.5 mm no knob) |
| na placa principal | 32.1 mm | L = 30 (-2.1 mm no knob) |

Knob Ø9 a 0.8 mm da superfície, eixo 6 mm dentro dele. O LED de 3 mm fica num espaçador de 3.9 mm (Seixo) / 3.6 mm (Madeira) sobre a plaquinha.

## 4. Espessura de parede

| | Seixo (resina/MJF) | Madeira (carvalho, CNC) |
|---|---|---|
| Paredes | 2.5 mm | 4.0 mm (2.5 em volta do inserto) |
| Tampa da interface | 2.5 mm | 3.0 mm |
| Tampa em volta das teclas | 3.0 mm, apoiada na placa | igual |
| Borda da abertura | arredondado 4 × 2.0 + 1.0 mm reto | igual |
| Teia da grade | 2.1 mm | igual |
| LED | furo Ø3.5 | pele de 0.8 mm |

A Madeira precisa de duas fixações no CNC (de cima, e virada para o bolsão interno).

## 5. Perguntas para o design

Já decidido nesta rodada (para escrever na v6): passo 18,5 com fileiras a 16.02 mm; caixa mantida com 100 mm (a folga frente/trás do teclado sobe de 7,5 para 8.17 mm, a faixa de tampa continua 10.3 mm, o comprimento cai para 331.1 mm); curva da frente da rampa até 75° e depois reta, chegando à face em x ≈ 47.4 (cima) e 56.1 (baixo); pilha de 13 mm no eTuttino e ≤ 10 mm no Chorus.

1. **Raio do vinco.** A SPEC pede o vinco em y = 55 arredondado, sem dar o raio. Usei R 10 (`IF_CREASE_R`).
2. **Saia das capas.** Com passo 18,5 e saia Ø17 sobram 1.50 mm entre saias vizinhas. Manter, ou saia Ø16,5 (2.00 mm)?
3. **Switch à mostra.** Entre a tampa e a saia aparecem ~6.8 mm da carcaça. A tampa em volta das teclas (`Z_DECK`, hoje 15.7) pode subir até ~17.4 sem tocar as saias apertadas, escondendo boa parte do switch. Sobe?
4. **Madeira.** A borda da abertura (1.0 mm reto) é frágil em carvalho, e a pele de 0.8 mm sobre o LED provavelmente fica escura. Borda mais grossa só na Madeira? LED com furo e janela de acrílico em vez da pele?
5. **Texto da SPEC para a v6.** Seção 2: passo 18,5 e fileiras em y = 74.03, 58.01, 41.99, 25.97. Seção 4: comprimento ~331.1 e o fim da rampa como acima. Seção 8 (Madeira): ainda diz "fresagem de 3 eixos de cima: ... bolsão interno", contra as duas fixações da intro e da mudança 7. Seção 9: pilha de 13 / ≤ 10 mm e PCB refeita com fileiras a 16.02 mm (não 16,5).
