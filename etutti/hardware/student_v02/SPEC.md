# eTutti Student V2 — SPEC v2

Data: 16 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code
Responde ao FIT_CHECK do PR #150 (SPEC v1 atendida). Conceito visual atualizado no canvas: https://claude.ai/artifact/2xeBWDz7PnhAhXUK7pcHGy (prancha "Especificação do conceito · v2").

Base: o que o PR #150 entregou em `etutti/hardware/student_v02/` (placa, case em peças, estudos). Tudo o que não é mencionado aqui continua como na v1 e no modelo do PR.

## Mudanças desde a v1 (respostas às 12 perguntas do FIT_CHECK)

1. **Emendas na parede esquerda: não aceitas.** Furos fechados, sem rasgos nem dentes na base. Os conectores ficam recuados cerca de 0,3 mm atrás da face interna da parede, e a placa entra por baixo na tampa (montagem com a tampa de cabeça para baixo). Os furos são dimensionados para o corpo do plugue: USB-C 12,5 × 7,0 com cantos R 3,5; jacks Ø 6,5. A divisa tampa/base e a faixa cinza ficam como estão (z = −4,0). Confirmar a profundidade de encaixe dos plugues; se o recuo não funcionar, voltar com alternativas antes de mudar a divisa.
2. **Grade do teclado: FR-4 de 1,6 mm com máscara preta fosca**, pedida junto com a placa (arquivo de fabricação próprio, como o plate da V1).
3. **Folga grade ↔ teclas: 0,15 mm**, sem espuma. A grade desce para z 11,35–12,95 e o poço passa de 5,0 para **5,25 mm**. A altura dos botões em relação ao tampo não muda (as hastes crescem 0,25 mm).
4. **Pinos sob o teclado: aprovado o caso D** — 4 pinos Ø 5 com ponta Ø 2 nos furos da V1, em (98,45; 52,67), (153,95; 31,31), (153,95; 63,35) e (209,45; 52,67), mais 3 pilares Ø 4 sem furo em (127,5; 32,5), (182,5; 62,5) e (182,5; 32,5).
5. **Décimo parafuso da grade em x = 160,02: ok.**
6. **Borda do poço a 15,0 mm dos centros** (12,5 + raio de 2,5), como na v1. O canvas foi corrigido.
7. **Janela da tela: 24 × 13 mm**, centrada em x = 37 (x 25–49, y 15,5–28,5), com **acrílico fumê escuro** de 1 mm. Filete de 0,5 mm a 1,5 mm abaixo da janela, com a mesma largura.
8. **Faixa amarela da direita sobre o chanfro lateral: mantida** de propósito (envolve a quina, no espírito da referência).
9. **Caixa acústica: crescer para 10–12 cm³ em L**, por dentro, sem mudar nada por fora. Continua estanque (fios vedados com silicone), na mesma peça do anel. O firmware corta os graves abaixo de ~300 Hz no alto-falante.
10. **Carga com o instrumento desligado:** com o USB ligado, a tela acende só com a carga, em brilho baixo. Registrar para o firmware.
11. **Troca da bateria:** basta tirar os 6 parafusos da base. Sem tampa de acesso.
12. **Logo, OUT e IN: baixo-relevo de 0,4 mm com preenchimento de tinta.** Logo "eTUTTI" + "STUDENT · V2" em Michroma, de pé ao longo da borda esquerda (y 8–92, a partir de x 8,6). "OUT" e "IN" com 2 mm de altura, à direita de cada furo, abaixo dos sulcos. Modelar os rebaixos.

Decisões do PR #150 aceitas como estão: aberturas medidas, fixação da grade (M2 × 16 por cima + espaçador + porca, copo na base), 6 parafusos M2 × 14 da tampa nas posições listadas no FIT_CHECK, luva do knob, tela em 4 postes com cabo de 4 vias, OLED por I²C, encoders de eixo de 20 mm girados, bateria no piso da base.

## Valores que mudam em relação à v1

| Item | v1 | v2 |
|---|---|---|
| Grade do teclado (z) | 11,6–13,2 | **11,35–12,95** |
| Folga grade ↔ teclas | 0,4 | **0,15** |
| Profundidade do poço | 5,0 | **5,25** |
| Base do botão até a grade, em repouso (fileiras 1–4) | 5,2 / 7,2 / 9,2 / 12,2 | **5,45 / 7,45 / 9,45 / 12,45** |
| Folga com a tecla no fim do curso (fileiras 1–4) | 1,1 / 3,1 / 5,1 / 8,1 | **1,35 / 3,35 / 5,35 / 8,35** |
| Espaçador da grade | 11,6 | **11,35** |
| Janela da tela | 30 × 15 | **24 × 13, acrílico fumê** |
| Caixa acústica | ~4 cm³ redonda | **10–12 cm³ em L** |
| Aberturas dos conectores | rasgo até a base | **furos fechados: USB-C 12,5 × 7; jacks Ø 6,5** |
| Grade: material | não definido | **FR-4 1,6, máscara preta fosca** |

## Entregáveis deste ciclo

1. Atualizar a placa: o recuo dos conectores (posição em x), o arquivo de fabricação da grade em FR-4 e o que mais a mudança exigir; DRC e BOM atualizados.
2. Atualizar o modelo 3D e os STEP/STL: furos fechados, grade em z 11,35, poço de 5,25, hastes +0,25, janela 24 × 13 com o acrílico, caixa acústica em L, rebaixos do logo e das legendas.
3. Refazer o estudo acústico com a caixa em L (volume final, ganho em 262 e 523 Hz).
4. Renders: planta, corte pelas fileiras, corte pelo alto-falante, parede esquerda (mostrando os furos fechados) e isométrico.
5. FIT_CHECK.md atualizado, terminando com "Perguntas para o design".

---

# Anexo — SPEC v1 (referência, com os valores substituídos pela tabela acima)


Data: 16 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code (eletrônica + modelo 3D)
Conceito visual: canvas "eTutti Student V2 · conceito de layout" — https://claude.ai/artifact/2xeBWDz7PnhAhXUK7pcHGy
Base: `etutti/hardware/student_v01/` (placa, firmware e case da V1).

Acabamento deste ciclo: **Retrô**. O acabamento **Nave** fica no inventário (não desenvolver agora).

## Mudanças em relação à Student V1

- Case novo: altura fixa de 28,3 mm, chanfro largo na borda, três sulcos, poço do teclado de 5 mm.
- Fileiras de botões em alturas diferentes (+2, +2, +3 mm); botão Ø 15 com saia.
- Grade do teclado separada, só de acabamento, sem parafusos visíveis.
- PCB sem parafusos na área do teclado (pinos na base).
- Interface nova: tela OLED 0,96″, dois knobs chapéu, alto-falante com caixa acústica; **LED removido**.
- Conectores: USB-C, OUT 3,5 mm (fone/caixa de som), **IN 3,5 mm (microfone, novo)**.

## Sistema de coordenadas

- Planta: origem no canto de trás à esquerda do case; **x** para a direita (0–252), **y** para a frente, em direção a quem toca (0–100).
- Altura: **z = 0 no topo da PCB**. Base do case em z = −10,1; tampo em z = 18,2.

## 1. Corpo

| Item | Valor |
|---|---|
| Dimensões externas | 252 × 100 × 28,3 mm (z −10,1 a 18,2), cantos em planta R 9 |
| Altura | fixa e uniforme; a única mudança de nível é o poço do teclado |
| Paredes | verticais |
| Chanfro da borda superior | 30°, 6,0 mm na horizontal × 3,5 mm na vertical, as duas arestas em R 1,5; igual nos quatro lados |
| Sulcos | 3 sulcos de 0,8 mm (largura) a cada 2,2 mm, em z = 8,0 / 10,2 / 12,4, a volta toda |
| Base (cor cinza) | z −10,1 a −4,0; quina inferior chanfrada 1,5 |
| Espessura da tampa | 2,0 mm |
| Fixação tampa ↔ base | parafusos por baixo, só na borda (fora da área do teclado) |

Acabamento Retrô: tampa creme (#E8DEC6 / #EDE4CF), chanfro em degradê do mesmo tom, base cinza (#9C9B96); faixas vermelha (#C8402A, 4,5 mm), laranja (#E07A2C, 4 mm) e amarela (#E3B23C, 2 mm), com 1 mm entre elas, de trás para a frente sobre o tampo, o chanfro e a parede da frente, em x = 58 e x = 237,5.

## 2. Teclado

- Mesmo teclado da V1: 28 teclas C-griff, G3–E5, grade de 18,5 mm (na fileira) × 16,02 mm (entre fileiras). As coordenadas dos centros são as da placa da V1.
- Fileira 1 é a da frente (y = 74,03); fileira 4 é a do fundo (y = 25,97).
- Teclas magnéticas Gateron **apoiadas na PCB** (corpo de z 0 a 11,2), haste em z 14,8, curso de 4,1 mm.

### Alturas das fileiras (degraus 2 + 2 + 3 mm)

| Fileira | Topo do botão (z) | Acima do tampo | Base do botão até a grade, em repouso | Folga com a tecla no fim do curso |
|---|---|---|---|---|
| 1 (frente) | 21,9 | +3,7 | 5,2 | 1,1 |
| 2 | 23,9 | +5,7 | 7,2 | 3,1 |
| 3 | 25,9 | +7,7 | 9,2 | 5,1 |
| 4 (fundo) | 28,9 | +10,7 | 12,2 | 8,1 |

A altura vem só do comprimento da haste de cada botão. Não há degrau na grade: ela é plana.

### Botões

- Ø 15 mm, cúpula convexa de 2,3 mm, saia de 1,2 mm, cabeça com 3,5 mm de altura total; haste de Ø 5,6 mm.
- **Três tipos**: branco (naturais), preto (sustenidos) e branco com pontos (C e F).
- Textura de pontos: covinhas de Ø 0,66 mm a cada 1,4 mm, numa grade a 45°, cobrindo toda a cúpula.
- O preto e branco do C-griff tem de ficar sempre visível.

### Grade do teclado (peça separada)

- Placa de acabamento de 1,6 mm, de z 11,6 a 13,2, 0,4 mm acima das teclas. Funciona como a placa de um teclado mecânico custom.
- Um furo de Ø 6,2 por botão (folga de 0,3 por lado), com chanfro de 0,3 na entrada.
- Contorno: acompanha o poço e passa 6 mm além da abertura, ficando por baixo da tampa.
- Fixação: **10 parafusos M2 na borda**, em espaçadores sobre a PCB, escondidos sob a tampa. **Nenhum parafuso visível.**
- A tampa tem uma aba que forma a parede do poço (raio de 2,5 em cima e de 1,0 embaixo) e termina 0,2 mm acima da grade.
- Poço: 5 mm de profundidade (z 18,2 → 13,2); o contorno acompanha as diagonais do teclado, com 5 mm do botão até a parede.

## 3. PCB e fixação

- **Nenhum parafuso atravessa a área do teclado.**
- A PCB é apoiada e posicionada por pinos que sobem da base, inclusive sob a área do teclado, nos vãos entre as teclas. Uma proposta de posição está na fileira 2: x = 116,95 / 153,95 / 190,95, y = 57,99.
- **Code deve estudar:** se só os pinos bastam contra a flexão da PCB e da grade ao tocar com força; quantos pinos, de que diâmetro e onde; se é preciso algum apoio extra.

## 4. Interface (área à esquerda do teclado)

| Item | Posição / medida |
|---|---|
| Logo "eTUTTI" + "STUDENT · V2" | fonte Michroma, de pé ao longo da borda esquerda, de y 8 a 92, começando em x 8,6 (fora do chanfro) |
| Tela OLED 0,96″ 128×64 | janela de 30 × 15 mm em x 22–52, y 14,5–29,5; filete de 0,5 mm em y 31,0 |
| Knobs (encoder com clique) | centros em (28; 44,5) e (46; 44,5); knob "chapéu" preto com saia de Ø 12, corpo de Ø 9, altura de 7 mm, traço creme; legendas VOL e REGISTRO |
| Grade do alto-falante | 7 fendas de 32 × 1,6 mm a cada 3,6 mm (barras de 2,0), pontas arredondadas, x 21–53, y 61,5–84,7, atravessando a tampa de 2,0 |
| LED | **removido** — o estado do instrumento (ligado, carga, registro) aparece na tela |

Todos os elementos da interface ficam centrados em x = 37, com cerca de 7 mm entre eles.

Encoder: o knob tem só 7 mm, então o eixo precisa sair no máximo cerca de 6 mm acima do tampo. Usar eixo curto ou encoder montado mais baixo.

## 5. Alto-falante

- Ø 28 × 5 mm, centrado em (37; 73,1), sob a grade.
- Pilha, de cima para baixo: tampa com fendas (2,0) → tela acústica (0,3) → junta de espuma (1,0) → alto-falante.
- **Caixa acústica fechada** atrás do cone, com cerca de 4 cm³ (interior de ~10 mm de altura, de z ~2,6 a ~13). A caixa e o anel de fixação são uma única peça impressa, presa por 2 parafusos M2 × 5 em buchas da tampa (y = 73,1 ± 18,6), sem cola.
- **Code deve estudar:** volume da caixa e resposta de graves para o alto-falante escolhido; o que fica abaixo da caixa na PCB.

## 6. Conectores (parede esquerda, x = 0)

| Conector | Centro (y) | Altura do centro | Legenda gravada |
|---|---|---|---|
| USB-C | 16 | z 1,7 | nenhuma |
| OUT 3,5 mm (fone ou caixa de som, saída de fone do codec) | 36 | z 2,8 | "OUT" |
| IN 3,5 mm (microfone, entrada de mic do codec com bias) | 60 | z 2,8 | "IN" |

As legendas vão ao lado direito de cada furo, na faixa lisa abaixo dos sulcos, e nunca sobre o chanfro ou os sulcos.

## 7. Entregáveis pedidos ao Code

1. **Revisão da eletrônica**:
   - placa nova dentro do contorno V2, mantendo a grade do teclado da V1;
   - OLED 0,96″ (I²C ou SPI);
   - dois encoders de eixo curto;
   - USB-C, OUT e IN nas posições acima;
   - remoção do LED;
   - espaçadores da grade e furos dos pinos de apoio;
   - zona livre sob o alto-falante e a caixa;
   - lista de materiais.
2. **Modelo 3D detalhado** do case em peças: base, tampa, grade do teclado, botões (3 tipos × 4 alturas de haste), knob, anel + caixa acústica. Com fit check contra a placa e as teclas.
3. **Estudos pedidos**: flexão/estabilidade com os pinos (seção 3) e volume da caixa acústica (seção 5).
4. **FIT_CHECK.md**, terminando com "Perguntas para o design".
