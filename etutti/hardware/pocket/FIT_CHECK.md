# eTuttino Pocket · fit check (design)

**SPEC atendida: v5, tarefa F3** (case para o micro-USB, knobs e botão do Teensy, Seixo variante B). 19 out 2026.
O F1 e o M1 (SPEC v4), o D2 (v3) e o D1 (v2) estão no histórico do git.

Página de revisão para o J: `/etutti/pocket/revisao/` (só português, noindex).

**Resultado: nenhuma divergência aberta contra o `pcb/PECAS.json` v5 (F4).**
- Zero colisões entre as peças e o case, entre as peças e entre as peças do case.
- 0 arestas abertas nos 11 STL.
- Raios livres:
  - 140/140 nas teclas, 73/73 na grade e 3/3 nos knobs e no LED;
  - **14/14 na janela do micro-USB e no furo do fone**;
  - **5/5 no furo do botão do Teensy**.
- Flexão da placa: **0,029 mm a 3 N** (limite 0,05). O contorno da placa não mudou.

## 1. O que foi feito

Tudo em `etutti/hardware/pocket/case/` (CadQuery, venv `C:/Users/julia/.venvs/cadquery`). A ordem de rodar é a do F1:
1. `case.py`;
2. `fit_check.py`;
3. `pcb_envelope.py`;
4. `mechanics.py`;
5. `render.py`;
6. `../layout.py`;
7. `revisao.py`;
8. `etutti/landing_svgs.py`, só regenerado.

### 1.1 Saiu a plaquinha do painel

Saíram o ressalto da plaquinha, a aba de apoio, o poste com pino (furo 1), a costela do M2 (furo 2), as janelas do USB-C
e do SJ1-3525N.

### 1.2 Micro-USB de painel: extensão em fita FPC (a eletrônica trocou o cabo no F4, por proposta do design)

**O cabo redondo do primeiro `PECAS` v5 não cabia.** Era um cabo de 3,5 a 4,5 mm, com raio ≥ 18 e de 25 a 30 cm (com
~20 cm sobrando).
- A única altura livre sob a tampa é z 19,5–30,5, por cima do Teensy.
- As laterais do plugue de 90° estão fechadas:
  - para trás, a coluna do parafuso (25; 6,5) e a parede;
  - para a frente, a aba da plaquinha dos knobs, o encoder, o fone e a fêmea.
- O melhor possível foi R ~13 no laço sobre o Teensy e R ~6–7 na entrada do plugue, com um cabo de OD ≤ 3,0 e de
  ~11 cm.

A eletrônica escolheu a **extensão em fita FPC** (`micro_b_panel_cable` v5):
- macho de 90° "UP" no Teensy: a fita sai do topo do plugue;
- fêmea numa cabecinha sem orelhas, de ~12 × 9 × 4 (conferir);
- fita de 10 cm.

Como ficou no case:
- **Ressalto plano** no lado de dentro da parede curva de trás-esquerda. A face é a corda da parede interna entre y 10 e
  y 40, 1 mm para dentro.
- **Bloco com túnel** de 12,4 × 9,4 × 4,4 (o pedido), aberto para dentro. O eixo vai na direção (0,919; 0,393), a z 27,25.
  A origem fica em (14,29; 19,42).
  - A fêmea entra por trás e encosta num **ressalto de 0,5** na parede. O ressalto tem abertura de 8,6 × 3,6 (o
    receptáculo é 7,5 × 2,6) e segura o puxão do plugue.
  - Folga da cabeça no túnel: 0,2 de cada lado.
- **Janela de 12 × 8 R1** por fora até o ressalto. A parede total na janela é **3,0** (janela 2,5 + ressalto 0,5).
- **Rebaixo plano por fora** de 13,5 × 9,0 R2, com **1,94** de fundo: a parede crua ali tem 4,94.
- **Trava impressa** `seixo_trava_usb` (MJF): barra de 19,2 × 6,4 × 1,5 com rasgo de 12,4 × 1,6 para a fita.
  - Vai presa por **2 × M2 × 5 autoatarraxantes a 16 mm**, em pilotos de Ø 1,6 × 5 na face de dentro do bloco.
  - Segura o empurrão do plugue (~20 N).
- O bloco tem 19,2 de largura e vai do chão (z 23,85, piso de 1,2) até a tampa. Fica **2,0 acima do topo do plugue do
  Teensy** (z 21,85).
- **Caminho da fita** (zonas reservadas no `pcb_envelope.json → panel.ribbon`, vazias de qualquer peça ou do case):
  1. sobe do topo do plugue;
  2. dobra chata sob o bloco (2,0 de altura, a dobra pede R ≥ 1,5 + 0,3);
  3. sai pela ponta do bloco, sobe até a trava e entra na fêmea pelo rasgo;
  4. a sobra (~9 cm) fica dobrada chata sobre o Teensy, em x 33–47, y 13,5–27,5, z 20–23,4.

  Fica longe do L10 (x 93,6) e do amplificador.
- O plugue "UP" foi conferido com o envelope antigo (11 × 11 × 7,5, que contém o 11 × 8,5 × 5,5 do PECAS).

### 1.3 Fone de painel Cliff FC681375V

- Fica numa **face plana própria**, com eixo em **+x** e furo em (6,69; 38,0), z 23,95. Pelo eixo radial ele bateria
  na plaquinha do potenciômetro.
- O corpo vai virado: **9,0 na horizontal e 10,5 na vertical**. Assim passa 0,5 acima do J_BAT e a 1,5 da plaquinha do
  potenciômetro.
- **Furo de Ø 8,2** (rosca M8, 0,1 de folga radial). **Parede de 2,0** no furo: o pedido é ≤ 2,5 e o recomendado 1,5–2,0.
- **Rebaixo por fora de Ø 11,5**, com 2,42 de fundo, para a porca anelar de Ø 10 (ou sextavada de 10).
  - A rosca tem 4,5; parede + porca = 4,0.
- Face plana por dentro de 12 × 11 (pedido ≥ 11 × 10).
- **Nervura contra o giro** de 1,2 × 8 ao lado da face de 10,5 do corpo, porque a peça não tem trava própria.
- Atrás da parede: corpo 13 + terminais 4 em linha reta. Os fios descem para o J_JACK.
  - Em linha reta sobram 18,2 até o canto do encoder (0,1 de sobreposição em y só ali). Os fios dobram antes.
- **Folgas:** J_BAT 0,5; plaquinha do pot 1,5; pot 1,75; encoder 1,52; trava da fêmea 1,22; tampa 1,3 por cima.

### 1.4 Rebaixo sob os knobs (SPEC v5, Mudança 5)

- **Rebaixo redondo de Ø 13 × 2,0** na tampa, sob os dois knobs.
- No do volume, a **porca M7 assenta rente**: topo a z 33,0, igual à tampa.
  - Medidas usadas da porca: 9 sextavado × 2,0, 10,4 entre cantos (conferir com a porca que vem no RK097).
  - Sobram 1,3 entre os cantos da porca e a parede do rebaixo. É o lugar da parede de uma chave de porca fina.
- O do seletor tem o mesmo rebaixo, sem porca.
- **Fundo do rebaixo: 0,5** (a tampa tem 2,5). É o que fica preso entre a face do potenciômetro e a porca. Trabalha em
  compressão, apoiado por baixo pelo corpo do pot.
- **Saiu o furo do pino anti-giro.** O pot está soldado na plaquinha em pé, que está soldada na plaquinha dos knobs,
  parafusada em 2 postes: ele não gira. Se o RK097 tiver o pino, ele é cortado.
- **Rosca útil do potenciômetro:**
  - bucha M7 de 7,0 a partir da face do corpo;
  - 0,5 presos no fundo e 2,0 na porca (rosca toda engatada);
  - **sobram 4,5 de rosca acima da porca**, dentro do knob.
- **Knob (proposta; o kit BOM fala em "~D10-12", que não cobre o rebaixo):**
  - Medidas: **Ø 14 × 14**, saia a 0,5 da tampa, furo D6 com parafuso de fixação, que serve no eixo serrilhado do pot e
    no eixo chato do encoder.
  - Por baixo, um alojamento de Ø 8,5 × 5 para a rosca que sobra: 0,75 de folga radial e 1,0 acima da bucha.
  - O knob cobre o rebaixo com 0,5 de sobra radial.
  - **Saia → porca: 0,5.** Entre os dois knobs ficam 2,0; do knob ao furo do LED, 3,25.
- **Encaixe no eixo:**
  - pot L 20 cortado a 4 mm da ponta: 8,0 (o PECAS pede ≥ 8);
  - pot L 15: 7,0;
  - encoder L 20: só **5,2**; com L 25, 8,0.
- **Chave de porca impressa** `seixo_chave_porca` (MJF): tubo de Ø 12,4 × 25 com sextavado de 9,15 numa ponta e furo
  passante de Ø 7,8 para o eixo. Ela cabe no rebaixo de Ø 13.

### 1.5 Botão de gravação do Teensy: **dá para alcançar com o case fechado**

- Por baixo não dá: o botão fica na face de **cima** do Teensy, e embaixo dele estão a Audio Board, a placa principal e o
  fundo.
- Por cima, sim. O botão fica na ponta oposta ao USB, centrado na largura. A PJRC diz "na ponta oposta ao micro-USB", mas
  não publica a cota. Usei 2,5 da borda, que é **conferir na peça**.
- Na pilha baixa, isso dá **(65,39; 20,38)**, sob a parte plana da interface:
  - 4,9 antes da aresta de cima da rampa;
  - 7,0 à direita do logo.
- **Furo de Ø 1,6** na tampa, com entrada chanfrada de 0,6, e **tubo-guia** de Ø 4 que desce até z 19,0, 1,3 acima do
  Teensy.
- Um clipe (Ø 0,8–1,0) desce 15,3 mm até o botão. Os raios pelo furo chegam livres ao Teensy (5/5).
- No manual (M2): "endireite um clipe, enfie no furinho à direita do logo e aperte de leve".

### 1.6 Fio do VBUS

Caminho de ~1,2 mm reservado e conferido: sai do pad VUSB pela ponta USB da pilha, entre o Teensy e a Audio Board, passa
pela borda esquerda da Audio Board (x 30) e desce até o J_VBUS (18,5; 18,0). Fica 1,47 abaixo do plugue e 0,6 da placa
na ponta.

### Arquivos finais (`case/out/`)

| Arquivo | O que é | Material | Qtd | Volume |
|---|---|---|---:|---:|
| `seixo_tampa` | casca de cima: paredes, tampas, logo, grade, rebaixos dos knobs, furo e tubo do botão do Teensy, bloco da fêmea micro-USB (túnel, ressalto, janela, rebaixo, pilotos M2), face e nervura do fone, postes dos knobs, caixa do alto-falante, colunas | **resina** (SLA/DLP, de engenharia) | 1 | 74,8 cm³ |
| `seixo_fundo` | fundo: pilares, berço e bolso da bateria, parafusos, pés | **MJF PA12** | 1 | 45,1 cm³ |
| `seixo_tampa_bateria` | tampinha da bateria | MJF PA12 | 1 | 3,3 cm³ |
| `seixo_caixa_fundo` | fundo da caixa do alto-falante | MJF PA12 | 1 | 2,2 cm³ |
| **`seixo_trava_usb`** | trava da fêmea micro-USB | MJF PA12 | 1 | 0,14 cm³ |
| **`seixo_chave_porca`** | chave da porca M7 | MJF PA12 | 1 | 1,5 cm³ |
| `plate` (+ `plate.dxf`) | placa dos switches | FR-4 1,6 | 1 | 13,2 cm³ |
| `keycap_natural` / `_sharp` / `_cf` / `_test_4` | capas | resina | 12 / 11 / 5 / 1 | 0,52 / 0,52 / 0,49 / 2,1 cm³ |

## 2. A forma

Igual ao F1: 251,5 × 100, contorno exato × `shape.py` 0,03 mm. As lições do OCC foram seguidas e as exportações conferidas
(§9).

## 3. Peça por peça (`PECAS.json` v5 × espaço reservado)

`fit_check.py` lê o `PECAS.json` na hora e confere:
- as medidas do furo do micro-USB e do corpo do fone (com `assert`);
- interseção zero de cada peça com a casca, o fundo, a placa dos switches, o fundo da caixa e a tampinha.

| Peça (PECAS v5) | Onde | Medida usada | Folga mínima |
|---|---|---|---|
| Fêmea micro-B FPC (cabeça) | túnel, eixo (0,919; 0,393), z 27,25 | 12 × 9 × 4 (conferir) | 0,2 em volta no túnel; encostada no ressalto de 0,5 |
| Trava + 2 × M2 × 5 | ponta do bloco | 19,2 × 6,4 × 1,5 | → fone 1,22; → plugue do Teensy 2,2 |
| Plugue do usuário (sobremoldagem) | na janela de 12 × 8 | ~10,5 × 7 (PECAS) | 0,5–0,75 radial; entra 2,5 até o ressalto |
| Macho 90° "UP" + fita FPC | plugue 11 × 11 × 7,5 (envelope); zonas da fita | fita 0,3 × 10–12 | 2,0 sob o bloco para a dobra; zonas sem nada dentro |
| Fone Cliff FC681375V | furo (6,69; 38), eixo +x, z 23,95 | corpo 9 × 10,5 × 13 + terminais 4; rosca M8 × 4,5; porca Ø 10 × 2 | J_BAT 0,5; plaq. do pot 1,5; pot 1,75; encoder 1,52; tampa 1,3 |
| Fio do VBUS (26 AWG) | pad VUSB → J_VBUS | Ø 1,2 | → plugue 1,47; → placa 0,6 |
| Potenciômetro RK097 | igual ao F1, bucha presa no fundo do rebaixo | 15,8 × 9,5 × 11,25; rosca M7 × 7 | rosca no furo 0,15; → encoder 3,3 |
| Porca M7 | no rebaixo de Ø 13 | 9 sextavado × 2,0 (conferir) | rente; 1,3 dos cantos à parede do rebaixo |
| Knobs (proposta) | Ø 14 × 14, saia a z 33,5 | furo D6 + parafuso | → porca 0,5; → rosca 0,75 / 1,0; entre eles 2,0 |
| Encoder EC11E | igual ao F1 | 12,4 × 13,2 × 6,5; eixo de 20 | eixo no furo 0,4; → alto-falante 3,05 |
| LED, plaquinhas dos knobs, SH-10 | iguais ao F1 | — | iguais (§3 do F1: 0,25 / 0,5 / 1,28) |
| Teensy + Audio Board (baixa) | igual ao F1 | 8,7 | → tampa 0,5; → tubo do botão 1,3 |
| Bateria, bolso do plugue, J_BAT/J_SPK | iguais ao F1 | — | iguais (inchada → teto 0,24; par JST → bateria 0,88) |
| Alto-falante CLS0361-L152 | igual | Ø 36 × 6,0 | anel 0,3; membrana → grade 1,07 |
| Placa principal | `pcb_envelope.json` (contorno sem mudança) | 1,2 | → paredes e colunas 0,5 |
| Teclas | iguais | — | switch → casca 8,3; capa → abertura 10,3 |

## 4. Alturas sob a tampa (tampa por dentro a z 30,5)

| O quê | Faixa z | Até a tampa |
|---|---:|---:|
| Corpo do potenciômetro | 14,5–30,3 | 0,2 (encosta ao apertar a porca) |
| Bloco da fêmea | 23,85–30,5 | é da tampa |
| Cabeça da fêmea | 25,25–29,25 | teto do túnel a 29,45 |
| Fone (corpo) | 18,7–29,2 | 1,3 |
| Plugue do Teensy | 14,35–21,85 | 2,0 até o bloco (dobra da fita) |
| Encoder (corpo) | 17,18–23,68 | o eixo atravessa |

## 5. Caixa do alto-falante e grade

Sem mudança: 17,9 cm³ (15,2 no pior caso), 73 furos, 33,5 % do cone, membrana a 1,07 da grade.

## 6. O contrato com a placa: `case/out/pcb_envelope.json` (o que mudou, para a eletrônica)

- **`outline`: sem mudança** (conferido ponto a ponto contra o F1). `boss_keepouts`, `supports`, `mounting_holes`, `keys`,
  `stack`, `plate_*`, `battery` e `speaker` também não mudaram.
- **`panel` reescrito** (saiu a plaquinha):
  - `micro_b_female`:
    - origem, eixo e z;
    - cabeça, túnel, janela, ressalto, parede e rebaixo de fora;
    - planta e z do bloco (`block_plan`, `block_z` 23,85–30,5);
    - parafusos (2 × M2 × 5 a 16, pilotos Ø 1,6 × 5) e a trava.
  - `ribbon`: as três zonas da fita (dobra sob o bloco, subida na ponta do bloco, sobra sobre o Teensy).
  - `jack`: Cliff FC681375V em (6,69; 38), eixo +x, z 23,95, corpo virado (9 × 10,5), furo 8,2, parede 2,0, rebaixo de
    Ø 11,5.
  - `vusb_wire`: o caminho do fio.
- **`connector_zones.back_left`**:
  - `for` agora é J_BAT, J_SPK, J_VBUS e J_JACK;
  - novo `z_top_max_under_jack`: **para y > 33,2, nada acima de z 18,4**, porque o fone passa por cima ali. O J_BAT, com
    topo a 18,2, cabe.
- **`controls.pot`**:
  - `anti_rotation_hole` = null;
  - novo `lid_recess` (Ø 13 × 2, fundo de 0,5).
- **`levels`**: só de h 10,5 para cima perderam um pouco de área: o fone, a face dele e as zonas da fita entraram; a
  plaquinha saiu. De 2,0 a 9,0, iguais.
- **`cables.panel`**: fita FPC de 10 cm, 4 fios do fone ao J_JACK e o fio do VBUS ao J_VBUS.
- `spec` = "pocket SPEC v5, task F3".

**Para a eletrônica:** nada a refazer na placa principal, porque o contorno é o mesmo. Conferir que nada no topo, em
y > 33,2 e x 11–19,8, passa de z 18,4.

## 7. Rigidez da placa

`mechanics.py`: **0,029 mm no pior botão (C5, fileira 4) a 3 N**, média 0,011. Limite 0,05. Igual ao F1, porque o contorno
e os apoios não mudaram.

## 8. Fabricação

- **Materiais:**
  - casca de cima em resina;
  - fundo, tampinha, fundo da caixa, **trava e chave da porca** em MJF PA12;
  - capas em resina;
  - placa dos switches em FR-4.
- **Na resina:**
  - o fundo do rebaixo dos knobs tem 0,5: imprime bem em resina de engenharia. Ver a pergunta 2;
  - o túnel tem teto de 1,05 até a tampa;
  - o ressalto da fêmea tem 0,5.
- **No MJF:** a trava tem 1,5 de espessura e 0,65 entre o rasgo e os furos dos parafusos. Abrir os furos M2 para Ø 2,4 se
  vierem apertados.
- **Parafusos novos:**
  - 2 × M2 × 5 autoatarraxantes (trava da fêmea);
  - saem o M2 × 6 e o pino da plaquinha do painel.
- **Peso:**
  - **peças impressas ~158 g**: casca em resina 88 g, MJF 53 g, capas 17 g;
  - placa dos switches em FR-4: ~24 g;
  - instrumento inteiro: ~420 g (estimativa, como no F1).

## 9. Conferência das exportações

- **Arestas abertas ou não-manifold: 0** em todos os 11 STL (casca, fundo, tampinha, fundo da caixa, plate, trava, chave e
  as 4 capas).
- **Raios** na casca exportada:
  - teclas: 140/140;
  - grade: 73/73;
  - knobs e LED: 3/3;
  - **janela do micro-USB:** 5 raios de fora até o ressalto e 5 pela abertura do ressalto até o túnel;
  - **furo do fone:** 5 raios de fora até a face de dentro.

  Ao todo 14/14 livres. Mais **botão do Teensy**: 5/5 do topo da tampa até o Teensy.
- **Peças do case entre si:** interseção 0 em todos os pares.

## 10. Renders (`etutti/hardware/pocket/case/renders/`)

- `seixo_iso`, `seixo_iface`, `seixo_top`, `seixo_below`.
- `seixo_left`: janela do micro-USB com o rebaixo, e o fone.
- **`seixo_recessos`** (novo): sem os knobs, os dois rebaixos, a porca rente e o furinho do botão.
- **`fit_conectores`** (novo): por cima, sem a tampa: o bloco, a trava, o fone e as zonas da fita em amarelo.
- Cortes:
  - `fit_corte_y21`: a fêmea no túnel sobre o plugue, a dobra da fita e o tubo do botão;
  - **`fit_corte_y27`** e **`fit_corte_y38`** (fone sobre o J_BAT), novos;
  - `fit_corte_y44`, `fit_corte_y49` (rebaixos e porca), `fit_corte_y78`;
  - `fit_corte_x15`, `fit_corte_x18`, `fit_corte_x30`, `fit_corte_x31`.
- `fit_iso`, `fit_dentro`, `pcb_envelope`.

Conferi as imagens olhando.

## 11. Mudanças de contrato

### `build/pocket.json` (version 5, spec v5, task F3)

- `panel`:
  - agora `micro_b` (origem, normal, z, janela, rebaixo, tipo) e `jack` (Cliff FC681375V, origem, normal, z, furo,
    rebaixo);
  - saíram `board` e `holes`.
- Novo `teensy_button` (furo em (65,39; 20,38), Ø 1,6).
- `controls.knob_d` = 14 (proposta) e novo `controls.knob_recess`.
- `case.files` com a trava e a chave; `case.materials` com as duas.
- Sem mudança: teclas, contornos, knobs e LED (posições), grade, logo, bateria, pilha e `main_board.outline`.

### `case/out/pcb_envelope.json`

Ver §6.

### Pedidos a outras disciplinas

- **Kit BOM (eletrônica):**
  - knob **Ø 14** com furo D6 e parafuso de fixação, no lugar de "~D10-12", que não cobre o rebaixo de Ø 13;
  - 2 × M2 × 5 da trava.
- **Manual (M2, design):** o `manual3d/` ainda usa as constantes da plaquinha do painel. Ele é refeito no M2.

## Perguntas para a gestão

1. **Knob de Ø 14 × 14** (com alojamento por baixo para a rosca e parafuso de fixação), no lugar do "~D10-12" do kit: é o menor que cobre o rebaixo de Ø 13 da porca. Entre os dois knobs ficam 2,0 mm. Aprova o tamanho? Ou prefere um knob impresso por nós, com o mesmo desenho dos dois?
2. **Fundo do rebaixo de 0,5 mm** sob a porca: para a porca M7 de 2,0 ficar rente, sobra 0,5 da tampa de 2,5. Ela trabalha em compressão entre a porca e o corpo do pot e imprime bem em resina. Se preferir mais folga, a alternativa é 0,8 de fundo e a porca 0,3 acima da tampa, ainda coberta pelo knob. Fica 0,5?
3. **Eixo do encoder:** com o knob proposto, o eixo L 20 do EC11E entra só 5,2 mm no knob (o parafuso de fixação prende, mas o PECAS pede ≥ 8). Com L 25 entra 8,0. Trocamos o encoder para L 25 (pedido à eletrônica) ou fica o L 20?
4. **Botão do Teensy:** o furo de Ø 1,6 com tubo-guia fica à direita do logo, na posição em que o botão deve estar (2,5 da ponta, centrado: a PJRC não publica a cota). Antes de imprimir, o J confere com uma régua no Teensy dele. Pode ser assim?
5. **Protótipo:** com a extensão FPC e o fone de painel, a parte física da v5 está fechada no case, sem divergência aberta. As medidas da cabeça da fêmea FPC e do plugue "UP" são de vendedor: conferir na peça antes de imprimir a casca. Pode encomendar? Casca de cima em resina; fundo, tampinha, fundo da caixa, trava e chave em MJF; capas em resina, primeiro o `keycap_test_4`.
