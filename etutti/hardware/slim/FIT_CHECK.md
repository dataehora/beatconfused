# eTutti Slim · FIT_CHECK (SPEC R3SL, Etapa 2a — portão B da régua)

Resposta à **SPEC R3SL §8**. Relatórios: [POSICIONAMENTO.md](POSICIONAMENTO.md) (régua e grade), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (41 itens), [ELETRONICA.md](ELETRONICA.md), [FIRMWARE.md](FIRMWARE.md). **Parado no portão B da régua: sem rotas, a placa principal não foi posicionada, nada cotado ou comprado.**

## 1. Resumo da R3SL

| Parte | Resultado |
|---|---|
| **Design** | decisões da R3SL aplicadas no modelo do case (`case/case.py`: planta **249,5 × 89,1**, +10,5 mm à esquerda, bolso de 0,6 sob o P2, furos do USB‑C z 5,2 e do P2 z 4,0, plataforma dos registros +1,0, anel de LED, trilhos de apoio, bolsos dos postes da fileira 1); **envelope da régua** entregue (`case/envelope_regua.json`); `RESTRICOES_CASE.md` com 41 itens (17 novos) |
| **Eletrônica** | régua R8 + grade posicionadas, **DRC sem trilhas 0 erros / 0 avisos, paridade 0**; planta cotada com a nota em cada tecla; cena 3D com o case e cortes |
| **Programação e som** | índice × posição × nota: **32/32 ok** (`check_teclas.py`); `PINOS.md` × sketch: 15/15 |
| STEP que faltam | bateria LPP 503759 8HH (o fabricante não publica; usei a caixa 5,4 × 37,5 × 60,5) · MKL02 · JST SH 3 vias (altura 2,9 da LCSC). Todos os da régua têm STEP real |
| Desvios da R3SL | (1) **folga axial dos registros 0,8 mm, não 1,3** (pele de PA12 de 0,5 sobre o ímã Ø6 × 2,5); (2) **cabeça do parafuso M2 a 0,05 mm do flange da KS‑33D**; (3) o furo da grade ficou 14,03 (meio da faixa da SPEC), cantos R0,5 |

## 2. Decisões da R3SL aplicadas (medidas no modelo, `case/out/numeros.json`)

| Decisão | Aplicado | Medida |
|---|---|---|
| Bateria B3 | **+10,5 mm à esquerda** | planta x −100,5 … 149,0 (249,5), y −18,5 … 70,6 (89,1); baia 38,5 × 68,5 |
| Placa principal em z 6,8 + bolso de 0,6 sob o P2 | bolso 15,0 × 9,0 × 0,6 (piso 1,0 sob ele) | divisão base/tampo em z 8,0 (= topo da placa) |
| Furos do USB‑C e do P2 | USB‑C 9,0 × 3,6, centro z 5,2, x = −66; P2 Ø6,2, centro z 4,0, y = 59,5 | a 34,5 mm da quina esquerda (USB‑C) |
| Plataforma dos registros +1,0 | topo z **15,01** (as teclas não mudam: tampo máx. 22,0, borda da frente 11,1) | poço 13,81; face de baixo 12,31 |
| Plataforma do volume | topo z 21,01 | poço 19,81; face de baixo 18,31 |
| Anel de LED translúcido | fenda passante Ø23,2/Ø20,8 no tampo + peça `anel_led` (1,5 mm) | SLA ou acrílico |
| Knob retido pela haste, montado por último | desenho `case/img/knobs_corte.svg` | cabeça Ø10 / Ø19 sob o tampo |
| OFF às 7h30 (225°), 270° no sentido horário | ímã de OFF a 7,2 mm do eixo, no batente anti‑horário | registrado em R13 |
| Plugue SH por rabicho crimpado | R21 | JST SH 2,9 mm |

## 3. Envelope da régua entregue à eletrônica (`case/envelope_regua.json`)

- **Apoio contínuo:** dois **trilhos de 1,5 mm** (|v| = 6,0…7,5) sob as bordas longas de cada régua, até a face de baixo dela; **o mesmo tipo nas 4 fileiras, sem furos no piso**; a zona livre sob a régua é |v| < 6 (altura livre 2,2 / 4,2 / 6,2 / 9,2).
- **Bolsos sob os postes:** Ø5,8 até z 1,0, **só na fileira 1** (o poste chega a z 1,3); nas fileiras 2–4 o poste não alcança o piso.
- **2 espaçadores M2 por régua:** u = 49,0 e 123,0 (nos vãos 2‑3 e 6‑7), v = 0; parafuso M2 × 6, porca sextavada 4,6 × 1,6 sob a régua, cabeça sobre a grade; **furos Ø2,2** na régua e na grade.
- **Cauda e FFC:** cauda de 14,0 além da carcaça da tecla 1; FFC de 1,0 mm de altura, boca para −x na ponta esquerda; cabo reto.
- **Grade:** 148,0 × 16,0 × 1,2, a 1,3 mm acima da régua; furos 14,03 (R0,5); **alcance lateral 0,72 mm** entre a carcaça de uma fileira e a grade da vizinha.
- **Tamanho:** régua 160,0 (cauda 14,0 + teclas até u = 160); posição das réguas: fileiras 1 e 3 de x = −21,25 a 138,75; fileiras 2 e 4 de x = −30,5 a 129,5.

## 4. Itens novos do RESTRICOES_CASE.md (R25…R41, 17) e os que mudam o lado de fora

**Mudam o lado de fora e já estavam aprovados:** R02/R03 (furos), R07/R08 (+10,5 mm), R09 (plataforma dos registros +1,0), R17 (anel de LED). **Novos itens que mudam o lado de fora: nenhum.** Os novos tratam do apoio das réguas (R25), zona livre (R26), parafusos M2 (R27, **R35 crítico**), grade (R28, R41), FFC (R29), orientação das chaves (R30), tampo e plataformas (R31), corte base/tampo e paredes (R32, R36, R37), teto (R33), rampa (R34), MJF (R38), chave Hall (R39) e knobs (R40).

## 5. Pontos que só o protótipo fecha

Campo magnético real no sensor e na chave Hall; folga axial de 0,8 mm com a tolerância do MJF (±0,3); furo da grade 14,03 com a fresa da JLCPCB; painel régua + grade; comprimento do FFC (a principal ainda não está posicionada).

## Perguntas para o design

1. **Folga axial dos registros: 0,8 mm.** Com o ímã Ø6 × 2,5 (z 8,5…11,0) e 0,5 mm de pele de PA12 sobre ele, a cabeça chega a z 11,5 e a face de baixo do tampo fica em 12,31: **0,8 mm**, não os 1,3 da SPEC (que valem sem a pele). Aceita 0,8, ou o ímã fica **exposto no topo** da cabeça (1,3), ou a plataforma sobe mais 0,5?
2. **Plataforma plana de Ø26:** o tampo é inclinado 7,1°; um disco plano a z 15,01 fica **2,6 mm acima do tampo na frente** e **0,6 mm abaixo dele atrás**. Aceita assim, ou a plataforma deve **seguir a inclinação** (tampo + 1,0, com o poço inclinado)?
3. **Furo da grade:** 14,03 com cantos R0,5. A fresa da JLCPCB tem tolerância de ±0,1 e raio interno mínimo a confirmar; pedir 14,03 assim, ou 14,10 com alívio nos cantos?
4. **Painel régua + grade:** o painel proposto é ≈ 164 × 42 mm com trilho de 2,0 mm. Posso perguntar à JLCPCB (sem cotação) se aceita as duas peças no mesmo painel, ou o J prefere pedidos separados?
5. **Cabeça do parafuso M2 a 0,05 mm do flange da KS‑33D** (R35): escolhe (a) cabeça escareada nivelada à grade (grade escareada, como na V3), (b) parafuso de cabeça menor Ø3,2 (folga 0,25) ou (c) espaçador colado, sem parafuso?
6. **Orientação das chaves:** guia de luz **para trás**, ímã/sensor **para o jogador**, TMAG5253 a 4,3 mm do centro **do lado do jogador**. Confirma? (a outra orientação inverte as faixas de roteamento.)
7. **Cabos FFC iguais de ~50 mm** nas 4 fileiras (a principal ainda não está posicionada): aceita já, ou espera a 2b para escolher o comprimento?
