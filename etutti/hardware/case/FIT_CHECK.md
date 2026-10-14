# eTuttino — conferência do case (SPEC v9)

Gerado por `fit_check.py` a partir de `case.py` (CadQuery). As peças são sólidos com medidas de datasheet, da placa atual ou medidas por você; as incertas estão marcadas CHECK no código. Coordenadas da SPEC (y para quem toca). Folga = menor distância entre a peça e o case (tampa + fundo).

**v9.** Nada muda no case nem nas placas: a forma é a da v7 (congelada) com as mudanças da v8 (plate de FR-4 de 1.6 mm, botões em z = 26.6, reto de 2.6 mm na borda da abertura, dois parafusos M2 por baixo nos pilares (30; 60) e (12; 70) de Ø6, plaquinha de controles `etutti/hardware/controls_pcb.py` em dois postes sob a tampa). Mudanças da v9, só no firmware e na página: `ENC_STEPS_PER_DETENT = 4` (EC11E de 15 pulsos / 15 cliques), gravado no Teensy; a página `/etutti/` acompanha CC 7 (volume) e CC 25 (instrumento) sem mandar o CC de volta. O contorno interno para a PCB continua em `out/pcb_envelope.json`.

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
| Saia Ø16.5 × vizinha (as seis, mesma fileira e diagonais) | 2.00 mm |
| Saia × borda da abertura | 7.4 mm frente/trás, 14.2 mm laterais |
| Switches × case | 8.3 mm (Seixo), 8.3 mm (Madeira) |

**Capas.** A saia redonda (Ø16.5, parede de 0.8 mm) não pode descer até os cantos da carcaça retangular do Gateron. Com o curso de 4.1 mm, a base da saia fica a **10.21 mm acima da placa** com a tecla solta (z = 23.01; apertada, 6.11 mm). A capa tem **3.59 mm** da base da saia ao topo (z = 26.6), com o tubo da haste por baixo. Entre a tampa (z 17.4) e a saia aparecem ~5.6 mm da carcaça escura. O topo da carcaça e a altura da haste não estão cotados no desenho do Gateron: o `keycap_test_4.stl` (4 capas) confirma isso nos switches reais.

### Conferências da v6 (continuam valendo na v7)

1. **Tampa em z = 17.4 × saia apertada.** A base da saia, com a tecla no fim do curso, fica em z = 18.91: **1.51 mm acima da tampa**. Ela não chega ao nível da tampa, então também não encosta na borda da abertura (que de qualquer forma está a 7.4 mm na horizontal). A tampa mais grossa só cresce para cima: a face de baixo continua em z = 12.8, apoiada na placa, e nada da placa principal sob a faixa de 10.3 mm muda. Switches × case: 8.3 mm.

2. **Saias Ø16.5.** Na grade hexagonal os seis vizinhos ficam a 18.5 mm, então a folga é **2.00 mm** em todas as direções, diagonais incluídas.

3. **Fim da rampa.** A reta depois dos 75° só existe entre y ≈ 99.5 e a face da frente; as bordas chegam à face em x ≈ 47.4 (cima) e 56.1 (baixo). A largura útil da interface (seção 2) e a faixa livre à esquerda da fileira 1 não mudam; a grade continua a 6 mm da rampa.

4. **Madeira.** O reto da borda da abertura tem **2.6 mm**, como no Seixo (v7). O LED fica sob um condutor de luz redondo de Ø3.0 × 6.0 mm (CHECK com a peça comprada) num furo de Ø3.1, com a ponta lixada rente.

## 2. Teensy + Audio Board, tela, knobs, LED, alto-falante e conectores

Audio Board **38,0 × 36,8 × 6,7 mm** (anúncio da SB Components, conferido na sua placa), pilha montada de **~13 mm**. Largura útil da interface com altura total, na metade da frente (onde a rampa desce reta, o ponto mais estreito): 54.5 mm no Seixo, 51.5 mm na Madeira. Teto interno: z 30.5 sob a parte plana (Seixo), caindo a 13° até z 20.0 na frente.

**Por baixo da rampa e da tampa à esquerda da fileira 1** (Seixo). Ali o teto é a tampa do teclado: sobram **5.1 mm** acima da PCB (3.5 mm onde a placa de switches passa por cima). Faixa livre de placa de switches, por y: y 62: x 65.8–67.6; y 70: x 65.8–72.2; y 78: x 65.8–76.8; y 86: x 65.8–81.5; y 92: a partir de x 64.1. Cabem peças baixas da placa principal (SMD, multiplexador, LDO, conectores baixos), não a pilha nem o alto-falante. Por baixo da rampa o teto sobe do nível da tampa até o da interface em ~8.7 mm na horizontal.

**Arranjo testado** (`renders/fit_top.png`): placa principal estendida por baixo da interface; pilha no canto de trás, fileira VIN atrás, USB para a face esquerda: Audio Board em x 20–58, y 5–41.8, Teensy em y 12.5–30.3. A plaquinha de controles (y 35.5–61.0) fica presa por baixo da tampa, por cima da borda da Audio Board.

Ordem dos controles (v5): volume (20; 45), seletor (37; 45), LED (52; 45); tela em x 8–62.

### Pilha montada (13 mm)

Topo do Teensy z = 21.1, topo do micro-USB z = 23.7, plugue USB de 90° até z = 26.2. Teto sobre o Teensy: z = 30.5 (Seixo) / 30.0 (Madeira).

| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |
|---|---|---|---|---|
| Audio Board | ok (2.5 mm) | ok (1.0 mm) | ok (2.5 mm) | ok (1.0 mm) |
| jack da Audio Board | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| codec | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) | ok (10.3 mm) |
| barra de pinos | ok (8.4 mm) | ok (8.2 mm) | ok (8.4 mm) | ok (8.2 mm) |
| pinos + solda no Teensy | ok (7.9 mm) | ok (7.5 mm) | ok (7.9 mm) | ok (7.5 mm) |
| Teensy 4.0 | ok (7.7 mm) | ok (7.6 mm) | ok (7.7 mm) | ok (7.6 mm) |
| chips do Teensy | ok (8.5 mm) | ok (8.0 mm) | ok (8.5 mm) | ok (8.0 mm) |
| micro-USB do Teensy | ok (6.8 mm) | ok (6.3 mm) | ok (6.8 mm) | ok (6.3 mm) |
| plugue micro-USB 90° | ok (4.3 mm) | ok (3.8 mm) | ok (4.3 mm) | ok (3.8 mm) |
| plaquinha de controles | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| potenciômetro | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| potenciômetro (pernas) | ok (5.7 mm) | ok (5.7 mm) | ok (5.7 mm) | ok (5.7 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (7.5 mm) | ok (7.5 mm) | ok (7.5 mm) | ok (7.5 mm) |
| JST da plaquinha | ok (7.1 mm) | ok (7.1 mm) | ok (7.1 mm) | ok (7.1 mm) |
| plugue do cabo | ok (5.7 mm) | ok (5.2 mm) | ok (5.7 mm) | ok (5.2 mm) |
| LED 3 mm + espaçador | justo (0.25 mm) | ok (1.1 mm) | justo (0.25 mm) | ok (1.1 mm) |
| porca M2 (placa principal) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) |
| ponta do parafuso M2 | ok (2.8 mm) | ok (2.8 mm) | ok (2.8 mm) | ok (2.8 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (0.9 mm) | ok (0.6 mm) | ok (0.9 mm) | ok (0.6 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.29 mm) | justo (0.29 mm) |

Entre peças (menos de 1 mm, sem contar as que se encostam de propósito):

- plaquinha de controles × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- plaquinha de controles × jack de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
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
| pinos + solda no Teensy | ok (8.9 mm) | ok (8.7 mm) | ok (8.9 mm) | ok (8.7 mm) |
| Teensy 4.0 | ok (9.2 mm) | ok (8.5 mm) | ok (9.2 mm) | ok (8.5 mm) |
| chips do Teensy | ok (11.5 mm) | ok (11.0 mm) | ok (11.5 mm) | ok (11.0 mm) |
| micro-USB do Teensy | ok (9.8 mm) | ok (9.3 mm) | ok (9.8 mm) | ok (9.3 mm) |
| plugue micro-USB 90° | ok (5.5 mm) | ok (5.5 mm) | ok (5.5 mm) | ok (5.5 mm) |
| plaquinha de controles | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| potenciômetro | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| potenciômetro (pernas) | ok (5.7 mm) | ok (5.7 mm) | ok (5.7 mm) | ok (5.7 mm) |
| encoder | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) | justo (0.20 mm) |
| encoder (pernas) | ok (7.5 mm) | ok (7.5 mm) | ok (7.5 mm) | ok (7.5 mm) |
| JST da plaquinha | ok (7.1 mm) | ok (7.1 mm) | ok (7.1 mm) | ok (7.1 mm) |
| plugue do cabo | ok (5.7 mm) | ok (5.2 mm) | ok (5.7 mm) | ok (5.2 mm) |
| LED 3 mm + espaçador | justo (0.25 mm) | ok (1.1 mm) | justo (0.25 mm) | ok (1.1 mm) |
| porca M2 (placa principal) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) | ok (1.2 mm) |
| ponta do parafuso M2 | ok (2.8 mm) | ok (2.8 mm) | ok (2.8 mm) | ok (2.8 mm) |
| USB de painel | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) | ok (2.2 mm) |
| jack de painel | ok (0.9 mm) | ok (0.6 mm) | ok (0.9 mm) | ok (0.6 mm) |
| placa principal | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) | justo (0.00 mm) |
| tela 1,9" (módulo) | — | — | justo (0.20 mm) | justo (0.20 mm) |
| conector da tela | — | — | ok (4.2 mm) | ok (4.2 mm) |
| alto-falante 28 mm | — | — | justo (0.29 mm) | justo (0.29 mm) |

Entre peças (menos de 1 mm, sem contar as que se encostam de propósito):

- plaquinha de controles × USB de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)
- plaquinha de controles × jack de painel — Chorus Madeira: ok (0.5 mm); Chorus Seixo: ok (0.5 mm); eTuttino Madeira: ok (0.5 mm); eTuttino Seixo: ok (0.5 mm)

Potenciômetro, encoder, tela e alto-falante aparecem como "justo" (0,2–0,3 mm) de propósito: ficam encostados por baixo da tampa. Figuras: `renders/fit_iso.png`, `fit_top.png` (eTuttino, pilha montada, Seixo, tampa transparente), `fit_section_M.png` (Chorus com a pilha de 13 mm, corte na linha do Teensy) `fit_section_R.png` (pilha reduzida), `fit_top_chorus.png` (Chorus em planta) e `fit_section_x.png` (corte de trás para a frente pelo alto-falante).

**Condições que continuam valendo:** plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura); peças de painel com no máximo ~10 mm de corpo atrás do inserto (na Madeira a parede é afinada para 2.5 mm ali); potenciômetro, encoder e LED numa plaquinha sob a tampa, com pernas cortadas rente; fone de painel ligado por fio à Audio Board (um plugue reto de 3,5 mm não cabe).

## 3. Altura dos eixos

| Montagem | Eixo L (da face de montagem) | Padrão EC11 / RK09 |
|---|---|---|
| plaquinha sob a tampa, Seixo | 16.0 mm | L = 15 (-1.0 mm no knob) |
| plaquinha sob a tampa, Madeira | 16.5 mm | L = 15 (-1.5 mm no knob) |
| na placa principal | 32.1 mm | L = 30 (-2.1 mm no knob) |

Knob Ø9 a 0.8 mm da superfície, eixo 6 mm dentro dele. O LED de 3 mm fica num espaçador de 3.9 mm (Seixo) / -1.9 mm (Madeira) sobre a plaquinha.

## 4. Espessura de parede

| | Seixo (resina/MJF) | Madeira (carvalho, CNC) |
|---|---|---|
| Paredes | 2.5 mm | 4.0 mm (2.5 em volta do inserto) |
| Tampa da interface | 2.5 mm | 3.0 mm |
| Tampa em volta das teclas | 4.6 mm, apoiada na placa | igual |
| Borda da abertura | arredondado 4 × 2.0 + 2.6 mm reto | igual |
| Teia da grade | 2.1 mm | igual |
| LED | furo Ø3.5 | furo Ø3.1 + light pipe de Ø3.0 |

A Madeira precisa de duas fixações no CNC (de cima, e virada para o bolsão interno).

## 5. Perguntas para o design

Feito nesta rodada (v9): encoder com 4 transições por clique, gravado no Teensy (enumera como "eTutti"; o clique exato só se confere com a plaquinha montada); a página segue os knobs (verificado no navegador com um MIDI simulado: volume, instrumento, volta ao acordeom clássico, nenhum CC devolvido). Site e manuais refeitos seguindo o `etutti/BRIEF-site-manuais.md` (PRs #93–#97).

1. **Light pipe da Madeira.** Com a plaquinha na Madeira (topo em z = 23.3), um LED de 3 mm direto na placa chega a z = 28.6, 1.4 mm abaixo da face de baixo da tampa (z = 30.0). Então o condutor de luz cabe com **~4 mm** de comprimento (os 3.0 mm da tampa mais a folga), não os 6 mm de `LIGHT_PIPE_L` (CHECK): com 6 mm ele bateria no LED. O manual diz ~4 mm. Comprar o de 4 mm (ou cortar), ou mudar algo na v10?
2. **Pilha.** O manual pede o Teensy soldado direto na Audio Board com barras de pinos extralongas (o plástico da barra como único espaçador): dá ~8–9 mm, abaixo dos 13 mm conferidos e dos 10 mm do Chorus. Confirmar com a peça antes do protótipo.
3. **Protótipo.** Os arquivos de fabricação continuam prontos (placa principal, plate de 1,6 mm, plaquinha de controles, case e capas), e agora o site e os manuais também. Encomendar?
