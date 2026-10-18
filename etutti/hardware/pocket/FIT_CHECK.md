# eTuttino Pocket · fit check (design)

**SPEC atendida: v3, tarefa D2** (modelo do Seixo, variante B). 18 out 2026.
O D1 (estudo das variantes A, B e C, SPEC v2) está no histórico do git e em `variants.py`.

Página de revisão para o J: `/etutti/pocket/revisao/` (só português, noindex), agora com a versão final da B.

## 1. O que foi feito

Tudo em `etutti/hardware/pocket/case/` (CadQuery, venv `C:/Users/julia/.venvs/cadquery`). Ordem de rodar:

1. `case.py`: o modelo e as exportações (`out/*.step`, `out/*.stl`, `out/plate.dxf`).
2. `fit_check.py`: cada peça do `pcb/PECAS.json` contra o case e contra as outras; volume da caixa do alto-falante; conferência das exportações; peso. Escreve `out/fit_check.json` e `renders/fit_*.png`.
3. `pcb_envelope.py`: o contrato com a eletrônica, `out/pcb_envelope.json`, e `renders/pcb_envelope.png`.
4. `mechanics.py`: flexão da placa sobre os pilares, `out/board_sag.json`.
5. `render.py`: `renders/seixo_*.png`.
6. `../layout.py`: o `build/pocket.json` (agora lê o modelo; roda no venv do CadQuery).
7. `revisao.py`: a página de revisão. Depois, `python etutti/landing_svgs.py` (rodei; o código dele não mudou).

Peças exportadas (espelhadas para um sistema destro: `y_arquivo = 100 − y_SPEC`):

| Arquivo | O que é | Volume |
|---|---|---:|
| `seixo_tampa` | casca de cima: paredes, tampa do teclado, tampa da interface com o logo gravado, furos dos knobs e do LED, grade, anel e paredes da caixa do alto-falante, ressalto do painel com os furos do USB-C e do fone, postes das duas plaquinhas, colunas dos parafusos | 74,6 cm³ |
| `seixo_fundo` | fundo: pilares da placa, berço da bateria (paredes e teto), abertura da tampinha, parafusos escareados, pés | 44,7 cm³ |
| `seixo_tampa_bateria` | tampinha da bateria, 2 parafusos M2 | 3,3 cm³ |
| `seixo_caixa_fundo` | fundo da caixa do alto-falante, colado sob as paredes | 2,3 cm³ |
| `plate` | placa dos switches, FR-4 de 1,6 (também `plate.dxf`) | 13,2 cm³ |

Lições do OCC seguidas (`CLAUDE.md`): a abertura é **um loft só** por contornos empilhados; cada borda da rampa é **uma spline** por pontos densos e pareados (mesma contagem nas duas bordas); os dois R 5 da rampa são feitos um depois do outro; a casca fica só com o maior sólido depois do corte; **cada exportação é conferida** (§9).

## 2. A forma (Seixo, variante B)

- **251,5 × 100 mm**, como no D1. O contorno é construído **exato** (retas e arcos): a curva única de R 89,2 em volta do G3, concêntrica com a ponta da rampa, quinas de R 24, e o ">" da direita com R 32,8 em volta do E5. Diferença máxima para o polígono do `shape.py`: **0,03 mm**.
- **Abertura** com a regra do eTuttino (folga lateral de 1 botão, R 6 nas quatro quinas de 120°, chanfro arredondado de 4 × 2). O polígono do `shape.py` tinha bicos nessas quinas; o `pocket.json` agora leva os contornos exatos.
- **Rampa**: pé no chanfro (abertura + 4), topo em abertura + 12,7, os dois R 5. Atrás e na frente ela segue o "<" em linha reta até atravessar as paredes; em volta do G3, um arco.
- **Novidade: R 1 nas arestas de cima das paredes** (deck e interface), para não haver quina viva onde a mão encosta. O eTuttino tinha essas arestas vivas. Pergunta 3.
- **Interface**: plana a 33 até y = 55 (R 10 na dobra), depois 13° para a frente; tampa de 2,5.
- **Logo gravado** a 0,4 de profundidade, acompanhando a curva: cada letra num arco em volta do G3, "eTuttino" em Georgia Bold 7,6 (altura das maiúsculas 5,3) no raio 63,5 e "POCKET" em Arial Bold 3,6 no raio 56, centrados a 215,5°. Na parte de trás a curva é íngreme, então o texto sobe ~55° para a direita (ver `renders/seixo_iface.png`). Pergunta 1.
- **Knobs na linha y = 49**, como pedido: volume (15,12), seletor (31,12), LED (43,12).
- **Grade** só sobre o cone: **73 furos de Ø 2,1** em grade hexagonal de 3,0 (medida na tampa inclinada), pontes de 0,9. **33,5 % do cone aberto** (pedido ≥ ~30 %; cone de Ø 31, conferir no alto-falante).

## 3. Os conflitos da §3, resolvidos com a eletrônica

### Potenciômetro com chave (sem subir a tampa)

A eletrônica escolheu a opção 1 da SPEC (`PECAS.json` → `volume_pot`): **RK0972S de 9 mm com chave, tipo horizontal**, numa plaquinha **em pé**, com o eixo para cima e a rosca M7 presa na tampa pela porca.

- O corpo (15,8 ao longo do eixo, com a chave) **pendura de z 30,3 a 14,5**. A tampa não muda.
- **Mudei a posição da plaquinha do potenciômetro.** A eletrônica a pôs atrás do eixo (y 40,9–42,5), exatamente onde a plaquinha do painel precisa passar (§4). Aqui ela fica **à direita do eixo**, entre o potenciômetro e o encoder:
  - plaquinha em x 21,62–23,22, y 43–55, z 13,8–29,8;
  - corpo para a esquerda, x 10,37–21,62, y 44,25–53,75;
  - eixo a 6,5 da plaquinha, no (15,12; 49).
- As pernas que atravessam a plaquinha precisam ser **cortadas a ≤ 1,0** (x ≤ 24,3): o encoder começa em x 24,92. Folga medida: **0,62**.
- A plaquinha dos knobs vai de x 23,22 a 50,6 e encosta a 90° na do potenciômetro (aba ou 5 fios, como a eletrônica propôs).
- Debaixo do potenciômetro (z < 14,5) só há o teto do berço da bateria (z 10,8): **3,7 de folga**.
- Na tampa: furo de Ø 7,3 para a rosca M7 (0,15 de folga radial) e um furo cego de Ø 1,3 × 1,5 para o pino anti-giro em (15,12; 43,0). A posição do pino depende da peça: conferir, ou cortar o pino.

### Bateria

- **Berço exatamente como o pedido**: 58,5 × 36,5 × 7,6 (7 × 36 × 58 + 8 % de inchaço na espessura), centrado em (38; 65,8). Fica sob o potenciômetro, a plaquinha dos knobs e o alto-falante.
- O berço é **parte do fundo**: paredes de 1,2 e teto de 1,0 (z 9,8–10,8), com 0,24 entre a célula inchada e o teto.
- **Acesso pelo fundo sem abrir a tampa**: tampinha de 1,2 com 2 parafusos M2 escareados, encaixada num rebaixo do fundo. A quina da frente-esquerda dela segue o contorno do case. A célula fica sobre a tampinha, com espuma; nada colado nela.
- **Fora da placa principal**: a placa deixa de fora o canto x < 68,95, y > 45,85, e também x < 24, y > 39,1 por causa do bolso. Folgas: berço → placa **0,5**; berço → casca **0,39**; bolso → casca 0,67.
- **O plugue da bateria se encaixa dentro do berço.** O PCM fica na ponta **esquerda**.
  - Atrás dessa ponta, o berço tem um **bolso para o par JST PH encaixado**: 12,3 × 6,75 × 7,6, em x 10–22,3, y 40,8–47,55.
  - Um rabicho curto da placa principal desce até o bolso por um canal de 6 × 4, como pedido, na parede e no teto do bolso (x 12–18).
  - Para trocar a bateria: abre-se a tampinha, puxa-se a célula com o plugue e desencaixa-se do lado de fora. Não se abre a tampa nem se tira o fundo.
  - O J_BAT (ou os pads do rabicho) fica na zona de trás-esquerda (§6).
  - O par encaixado (estimado em 11,5 × 4,5 × 6) cabe com 0,4 nas pontas e 1,1 até o teto (conferir as medidas do par JST).
- O comprimento do case **não precisou crescer**.

### USB-C e fone (ressalto plano na parede curva)

A eletrônica pôs os dois numa plaquinha só, de 30 × 13 (`panel_board`).

- **Lugar**: a parede curva de trás-esquerda. A borda da frente da plaquinha fica na corda entre os pontos da parede em y 9 e y 37 (30,9 de corda). Por dentro, um **ressalto plano de 34 × 10,7** enche a curva atrás dela; a eletrônica pediu ≥ 32 × 10.
- **Altura: a plaquinha fica a z 22,3–23,9, não a 20,0.** Ela passa **por cima do plugue de 90° do micro-B do Teensy**, com 0,45 de folga, e por isso **não pode ter nada embaixo**. As peças de cima vão até z 30,1, a 0,4 da tampa. Centro do USB-C em z 25,53 e do fone em z 26,5, 14 mm um do outro ao longo da borda; o USB-C fica do lado de trás.
- **Paredes nos furos, como pedido**: 1,0 no USB-C (furo oblongo de 9,4 × 3,7) e 1,5 no fone (Ø 6,0).
  - Com o ressalto, a parede ali tem ~3,8. Por isso os rebaixos de fora são mais fundos que os 0,5 sugeridos:
    - USB-C: 13 × 7 com R 3, **2,9 de fundo**;
    - fone: Ø 10, **2,2 de fundo**.
  - Pergunta 2.
  - Com isso, a frente do receptáculo USB-C passa **0,85** da borda da plaquinha, e a do cano do fone **1,35**.
- **Fixação**: 2 parafusos M2 de baixo para cima, em postes de Ø 4,4 que descem da tampa até a plaquinha.
  - Os dois ficam do lado do USB-C, em (25,6; 17,39) e (21,2; 26,81).
  - Atrás do fone não há lugar: o corpo dele (14,3 + 2) passa da plaquinha.
  - Não ficam a 22 mm um do outro, como na sugestão. A eletrônica confere.
  - A borda da frente encosta no ressalto, que segura o puxão do plugue.
- **Folgas**:
  - USB-C → casca: 0,22;
  - fone → casca: 0,4;
  - fone → poste: 0,9;
  - USB-C → poste: 1,6;
  - plaquinha → coluna (25; 6,5): 2,6;
  - plaquinha → potenciômetro: 2,2.

### Alto-falante CLS0361-L152 (Ø 36 × 6,0)

- Centro em (26,88; 77,54), como no D1. O aro fica sob a tampa inclinada de 13°, sobre uma **junta de espuma de 0,8** (~0,5 apertada), dentro de um **anel de centragem** perpendicular à tampa (folga radial de 0,3).
- Distância **membrana → grade: ~1,1 mm**, supondo a membrana 0,6 atrás do aro (conferir). O pedido é ≤ 1–2.
- **Caixa traseira fechada e vedada**: paredes de 1,5 que descem da tampa até z 12,1, com um fundo colado (`seixo_caixa_fundo`) que apoia no teto do berço.
  - A caixa cresce 13 mm **para o lado** (+x), como a SPEC permite.
  - Volume: **18,5 cm³**, ou **15,8 cm³** contando o alto-falante inteiro como sólido.
  - O pedido é 8–12 (10 de preferência). A eletrônica diz que maior não faz mal. Pergunta 4.
- Os 2 fios saem por um furo de Ø 2, vedado com cola, no lado +x da caixa, em (60,7; 73,5), z 14,1.

## 4. Peça por peça (`PECAS.json` × espaço reservado)

`fit_check.py` monta cada peça como sólido, com as medidas do `PECAS.json` lidas na hora. **Nenhuma colide com o case**: interseção zero com a casca, o fundo, a placa dos switches, o fundo da caixa e a tampinha.

| Peça (PECAS) | Onde | Medida usada | Folga mínima |
|---|---|---|---|
| Potenciômetro RK0972S | corpo x 10,37–21,62, y 44,25–53,75, z 14,5–30,3 | 15,8 × 9,5 × 11,25; rosca Ø 7 | rosca no furo 0,15; corpo → encoder 3,3; → caixa do alto-falante 3,6 |
| Plaquinha do potenciômetro | x 21,62–23,22 (pernas até 24,3), y 43–55, z 13,8–29,8 | | → encoder 0,62; → painel 4,5 |
| Encoder EC11E | (31,12; 49), placa a z 17,18 | 12,4 × 13,2 × 6,5; eixo de 20 | eixo no furo Ø 6,8: 0,4; → caixa do alto-falante 1,1 |
| LED 3 mm bicolor | (43,12; 49), topo a z 32,5 | Ø 3, aba Ø 3,8, 5,3 de altura, sobre espaçador de ~10 | no furo Ø 3,5: 0,25 |
| Plaquinha dos knobs | x 23,22–50,6, y 42,5–56, z 15,58–17,18 | 1,6 + pernas de 1,5 | → caixa do alto-falante 0,74; → Audio Board 3,7 (por cima) |
| Conector SH-10 | x 46,4–50,6, y 43–55, na borda direita | 12 × 4,25 × 4,25 + 2 | → LED 1,3; → casca 2,7 |
| Plaquinha do painel | corda y 9–37, z 22,3–23,9 | 30 × 13 × 1,6, nada embaixo | → plugue do micro-B 0,45; peças → tampa 0,4 |
| USB-C TYPE-C-31-M-12 | (14,58; 16,66), z 25,53 | 8,94 × 7,35 × 3,26 | 0,22 no furo |
| Fone PJ-327A | (8,66; 29,34), z 26,5 | 14,3 × 9 × 6, cano Ø 5 × 2 | 0,4 no furo; → poste 0,9 |
| Plugue micro-B 90° | x 20,3–31,3, y 14,9–25,9, z 14,35–21,85 | 11 × 11 × 7,5 | → casca 2,0; → USB-C 2,0 |
| Teensy + Audio Board (baixa) | Audio Board x 30–68, y 4–40,8, z 10,7–12,3; Teensy até 17,7 (USB 19,4) | 38 × 36,8; 8,7 de altura | Audio Board → tampa do deck 0,5; Teensy → rampa 1,27 |
| Bateria 603450 com NTC | berço 58,5 × 36,5 × 7,6 em (38; 65,8), bolso do plugue atrás da ponta esquerda | 7 × 36 × 58 + 8 %; par PH 11,5 × 4,5 × 6 (conferir) | célula inchada → teto 0,24; par PH no bolso: 0,4 nas pontas; berço → placa 0,5 |
| Alto-falante CLS0361-L152 | (26,88; 77,54), inclinado 13° | Ø 36 × 6,0 | anel 0,3; membrana → grade ~1,1; fundo da caixa → magneto 2,7 |
| Placa principal | `pcb_envelope.json` | 1,2 mm, z 6,5–7,7 | → paredes, colunas, berço: 0,5 |
| Teclas | 28 switches + capas | Gateron KS-20, capas do eTuttino | switch → casca 8,3; capa → abertura 10,3 |

## 5. Alturas sob a tampa (interface plana: tampa por dentro a z 30,5)

| O quê | Topo | Até a tampa |
|---|---:|---:|
| Corpo do potenciômetro | 30,3 | 0,2 (a rosca prende na tampa) |
| Peças da plaquinha do painel | 30,1 | 0,4 |
| Encoder (corpo) | 23,68 | eixo atravessa |
| Plaquinha dos knobs | 17,18 | postes de Ø 5 até a tampa |
| Plugue do micro-B | 21,85 | 0,45 até a plaquinha do painel |
| USB do Teensy | 19,4 | sob a rampa: 1,27 do Teensy à rampa |
| Teto do berço | 10,8 | fundo da caixa do alto-falante a 10,9 |

## 6. O contrato com a placa: `case/out/pcb_envelope.json` (novo)

O mesmo esquema do eTuttino (`etutti/hardware/case/out/pcb_envelope.json`), mais blocos do Pocket. Coordenadas da SPEC (= vista de cima do KiCad), z absoluto.

- **`outline`**: a borda da placa. É o lado de dentro das paredes menos 0,5, com recortes em volta das 10 colunas dos parafusos. A eletrônica pode recortar mais. Ficam de fora:
  - o canto da frente-esquerda, onde está o berço da bateria (x < 68,95, y > 45,85);
  - o bolso do plugue (x < 24, y > 39,1).
- **`boss_keepouts`**: as 10 colunas, r 3,5.
  - A de (5,3; 38,5) só sobe até z 13,2.
  - A de (246,5; 58) entra na parede da ponta direita.
- **`supports`**: **43 pilares de Ø 4** no fundo, um no centro de cada triângulo de três teclas, mais 6 em volta das pontas. Somam-se 2 pilares de Ø 6 com parafuso. No **verso**, nada de peça, pad ou via dentro dos círculos.
- **`mounting_holes`**: 2 × M2 de baixo, em (26; 35) e (232; 58,01), com porca em cima da placa.
- **`max_below`**: 4,5 (até o fundo). **`plate_outline`**, `plate_clear` 3,5, `plate_thickness` 1,6.
- **`levels`**: onde cabem peças em cima da placa até h = 2 / 3 / 4,5 / 6,5 / 9 / 10,5 / 12 / 15 / 18 / 21 mm. Já tirei o case e todas as peças fixas que não são da placa: berço, caixa do alto-falante, plaquinhas do painel e dos knobs, potenciômetro, encoder, LED e a descida do cabo dos knobs.
  - **Mudança de formato:** cada nível é uma lista de `{"outer": [...], "holes": [[...]]}` (no eTuttino eram só polígonos).
  - A pilha não sai dos níveis: ela é da própria placa.
- **`keys`**: as 28 teclas, com nota, fileira e centro.
- **`stack`**: pilha **baixa**, Audio Board em [30; 4; 68; 40,8], ângulo 0.
  - USB do Teensy para a esquerda, fileira do VIN atrás.
  - Fileiras de pinos em y 12,76 e 28,0, pino 1 em x 33,6, 3 mm acima da placa.
  - Também: o plugue de 90° e as alturas.
- **`controls`**: plaquinha dos knobs com o retângulo, os 2 furos M2 dos postes, o encoder, o LED e o conector. Inclui `pot`: corpo, plaquinha em pé, pernas, furo da tampa e furo do pino.
- **`panel`**: a plaquinha do painel.
  - Polígono, z, a borda da frente e a normal.
  - USB-C e fone: posição, z, furo, parede, rebaixo, quanto passam da borda.
  - Os 2 furos M2.
  - "Nada embaixo".
- **`battery`**: o berço por dentro e por fora, z, teto, o recorte da placa, `connector_pocket` (o bolso do plugue), `pigtail_way_in` (por onde o rabicho da placa entra) e os parafusos da tampinha.
- **`speaker`**: centro, z da face, contorno da caixa e o furo dos fios.
- **`cables`**: descida do cabo dos knobs (x 50,6–56, y 40,9–45,8) e o caminho dos outros cabos.
- **`connector_zones`**: lugares sugeridos para os conectores.
  - J_BAT, J_SPK e J_PNL na zona de trás-esquerda, x 11–19,8, y 16–34,5, sob a plaquinha do painel, até z 21,9.
  - J_CTL entre a frente da Audio Board e o recorte da bateria (x 50,6–64, y 40,95–45,85, até z 14).

Figura: `renders/pcb_envelope.png`.

## 7. Rigidez da placa

`mechanics.py` usa o método do eTuttino: grelha de vigas da FR-4 nua de 1,2 mm, sem a ajuda da placa dos switches. Aqui a malha é de 2 mm, sobre o **contorno real** da placa (no eTuttino era o retângulo envolvente, malha de 4).

A placa se apoia nos 45 pilares e nas 28 pernas da pilha. Resultado: **0,029 mm no pior botão (C5, fileira 4) a 3 N**, média 0,011. O limite é 0,05.

A eletrônica deve rodar o `mechanics.py` dela com a placa real (E2b); os pilares não mudam.

## 8. Fabricação

- **Espessuras**:
  - paredes e tampa da interface: 2,5;
  - tampa do teclado: 4,6 (do deck à placa dos switches);
  - fundo: 2,0;
  - berço: paredes 1,2, teto 1,0;
  - caixa do alto-falante: paredes 1,5, fundo 1,2;
  - anel: 1,2;
  - tampinha da bateria: 1,2;
  - parede no USB-C 1,0 e no fone 1,5;
  - pontes da grade: 0,9;
  - gravação do logo: 0,4.
- **Parafusos**:
  - fundo: 10 × M2,5 autoatarraxantes (ou insertos a quente) em colunas de Ø 6, furo-piloto de Ø 2,2, cabeça escareada Ø 5,2;
  - plaquinha dos knobs: 2 × M2 em postes de Ø 5;
  - plaquinha do painel: 2 × M2 em postes de Ø 4,4;
  - pilotos de Ø 1,7;
  - placa principal: 2 × M2 com porca;
  - tampinha: 2 × M2 escareados, em bosses de Ø 5.
- **Folgas de impressão**:
  - fundo → paredes: 0,3;
  - tampinha → rebaixo: 0,3;
  - rosca M7 → furo: 0,15 radial;
  - eixo: 0,4;
  - LED: 0,25;
  - alto-falante no anel: 0,3;
  - USB-C no furo: 0,23 por lado.
- **Resina × MJF**:
  - **Resina** (±0,1–0,15): tudo serve como está.
  - **MJF PA12** (±0,3):
    - abrir o furo da rosca para Ø 7,5 e os pilotos M2 para Ø 1,8;
    - o traço mais fino do logo (~0,45 em Georgia 7,6) fica no limite do MJF (~0,5): resina recomendada para a casca de cima, ou o logo maior;
    - pó preso: o berço é aberto por baixo e a caixa do alto-falante só fecha depois. Não há cavidade fechada na impressão.
- **Peso**:
  - **Peças impressas: 125,1 cm³ = ~148 g em resina (1,18) ou ~126 g em MJF (1,01).** Placa dos switches em FR-4: ~24 g.
  - Estimativa do instrumento inteiro (conferir):
    - 28 switches × ~5 g = 140 g;
    - capas: 17 g;
    - placa principal: ~45 g;
    - Teensy + Audio Board: ~10 g;
    - bateria: 22 g;
    - alto-falante: 8,6 g;
    - parafusos, knobs e plaquinhas: ~13 g.
  - **Total: ~430 g em resina, ~410 g em MJF.**

## 9. Conferência das exportações

- **Arestas abertas ou não-manifold nos STL: 0** em todos (`seixo_tampa`, `seixo_fundo`, `seixo_tampa_bateria`, `seixo_caixa_fundo`, `plate`).
  - A primeira versão tinha 1 aresta aberta: a coluna da ponta direita tangenciava a parede. Ela passou para x 246,5 e entra na parede.
- **Raios** de cima para baixo no STL da casca:
  - abertura: **140 de 140 livres** (5 por tecla: centro e ±6,5 em x e y, até a placa);
  - grade: **73 de 73** furos atravessam;
  - furos dos knobs e do LED: 3 de 3.
  - Não sobrou película.
- `check_plan`: contorno exato × `shape.py`: 0,03 mm.

## 10. Renders (`etutti/hardware/pocket/case/renders/`)

- `seixo_iso`, `seixo_iface`, `seixo_top`, `seixo_left` (USB-C e fone na parede curva) e `seixo_below` (tampinha da bateria).
- `fit_iso` e `fit_dentro` (o interior com as peças).
- Cortes `fit_corte_y21` (painel sobre o plugue), `fit_corte_y49` (linha dos knobs), `fit_corte_y78` (alto-falante), `fit_corte_x15` e `fit_corte_x30`.
- `pcb_envelope`.
- Os `d1_*` são do D1.

Conferi cada imagem olhando.

## 11. Mudanças de contrato (para a eletrônica)

### `build/pocket.json` (version 3, spec v3, task D2)

- **Saiu `provisional`.** O resto do cabeçalho continua: `variant` B, `origin` 98,45, `length` 251,5, `rows` (a grade da firmware), sem mudança.
- `opening`, `chamfer`, `ramp`, `box` e `inner` agora vêm dos contornos exatos do modelo. Na abertura, R 6 nas quatro quinas (antes, bicos). Diferença ≤ ~1 mm só nessas quinas.
- `controls`:
  - `grille_outline` é o campo real dos furos (elipse em planta) e `grille` o retângulo envolvente (11,8; 62,8; 42,0; 92,3);
  - `holes` são 73 furos, com `hole_d` 2,1;
  - novos: `logo_letters` (letra, posição, ângulo, corpo, fonte) e `logo_depth`;
  - knobs e LED sem mudança.
- `controls_board`:
  - `rect` agora x 23,22–50,6;
  - novos: `posts`, `connector`, `pot.board` e `pot.board_z`;
  - `pot.rect` é o corpo deitado;
  - saiu `pot.reserved`.
- `speaker`: `part`, `box` (contorno de dentro), `box_floor_z` 10,9, `back_volume_cm3` 18,5 e `back_volume_conservative_cm3` 15,8. Saiu `d_max`.
- `battery`: `rect` é o berço de 58,5 × 36,5 em (38; 65,8). Novos: `outside`, `roof_z` e `hatch_screws`.
- `stack`: **pilha baixa**, `origin` (30; 4), **`angle` 0** (antes 30). Em `z`, saiu `teensy_bottom` e entrou `teensy_top`.
- `panel`:
  - novo: `board`, o polígono da plaquinha do painel;
  - `usb` e `jack` têm `at`, `normal` e `z`;
  - saíram `usb.rect`, `jack.rect` e `cable_mm`.
- `main_board`: saíram `keys` e `tongue`; agora há `outline`, igual ao do `pcb_envelope.json`.
- Novo `case`: arquivos e peso.

### `case/out/pcb_envelope.json` (novo, §6)

O que muda em relação às sugestões do `PECAS.json`:

- plaquinha do potenciômetro à direita do eixo, com as pernas cortadas a ≤ 1,0;
- plaquinha do painel a z 22,3–23,9, com **nada embaixo**;
- USB-C a z 25,53 e fone a z 26,5;
- postes do painel em (25,6; 17,39) e (21,2; 26,81);
- USB-C passa 0,85 da borda da plaquinha, e o cano do fone 1,35;
- plaquinha dos knobs em x 23,22–50,6, com o conector na borda direita;
- PCM da bateria à esquerda, com o plugue encaixado num bolso do berço e um rabicho da placa até ele (em vez dos 60 mm de fio direto até o J_BAT).

## Perguntas para a gestão

1. **Logo na curva:** a parte de trás da interface é íngreme, então "eTuttino POCKET" acompanhando a curva fica inclinado uns 55° (`renders/seixo_iface.png`). Fica assim, ou o J prefere o logo reto (horizontal), como nos desenhos do D1?
2. **Rebaixos do USB-C e do fone:** para a parede ficar com 1,0 e 1,5 nos furos (o pedido da eletrônica) atrás do ressalto plano, os rebaixos de fora ficam fundos.
   - USB-C: 13 × 7, com 2,9 de fundo.
   - Fone: Ø 10, com 2,2 de fundo.
   
   Visualmente são duas "janelas" afundadas na curva. Aceita, ou prefere um inserto preto (como o do eTuttino) com os dois conectores?
3. **R 1 nas arestas de cima das paredes:** arredondei as arestas externas do deck e da interface (o eTuttino as tinha vivas). Confirma?
4. **Caixa do alto-falante com 18,5 cm³** (15,8 contando o alto-falante inteiro), acima dos 8–12 pedidos. A eletrônica diz que maior não faz mal. Mantém, ou quer que eu feche em ~10–12 para sobrar espaço?
5. **Bateria pela tampinha de 2 parafusos no fundo**, com o plugue encaixado num bolso do berço (o J_BAT fica escondido sob a tampa, atrás da pilha). Para isso a eletrônica precisa de um rabicho curto da placa até o bolso, com um JST PH fêmea na ponta, e de conferir se o par encaixado cabe em 12,3 × 6,75 × 7,6. Aprova?
6. **Material da casca de cima:** em MJF, o traço mais fino do logo (~0,45) fica no limite. Recomendo resina para a casca de cima (o fundo, as tampinhas e a caixa podem ser MJF). Ou aumento o logo?
7. **Para a eletrônica (E2b), pelo integrador:**
   1. confirmar a plaquinha do potenciômetro à direita do eixo, com as pernas cortadas a ≤ 1,0;
   2. a plaquinha do painel sem nada embaixo, a z 22,3–23,9, com os dois furos M2 do lado do USB-C;
   3. o plugue micro-B de 90° com o cabo saindo **para o lado ou para trás**, não para cima (a plaquinha do painel passa 0,45 acima);
   4. J_BAT, J_SPK e J_PNL na zona de trás-esquerda, e J_CTL entre a Audio Board e o recorte da bateria (`pcb_envelope.json` → `connector_zones`);
   5. o rabicho da bateria até o bolso do berço (`battery.connector_pocket`, `battery.pigtail_way_in`).
