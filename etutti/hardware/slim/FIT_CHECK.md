# eTutti Slim · FIT_CHECK (SPEC R2SL, etapa 1 — portão A)

Resposta à **SPEC R2SL §8**. Relatórios das outras partes: [ELETRONICA.md](ELETRONICA.md), [FIRMWARE.md](FIRMWARE.md); registro de restrições novo: [RESTRICOES_CASE.md](RESTRICOES_CASE.md); corte dos knobs: `case/img/knobs_corte.svg` (e `.png`). **Parado no portão A: nada foi posicionado, roteado, cotado ou comprado.**

## 1. Resumo da R2SL

| Parte | Resultado |
|---|---|
| Eletrônica | Principal **ERC 0/0** (120 peças), régua **ERC 0/0** (20 peças); RT1062 DVJ6B conferido contra a SamacSys (196/196 pads, 0 mm, 0 diferenças de nome); BOM conferida (48 códigos, 24 tipos Extended) |
| Knobs | sensor de ângulo **TMAG5273** (A2 0x35 + B2 0x22), chave Hall **DRV5032ZE**; ímã Ø6 × 2,0 a 2,5 mm do sensor; OFF por latch + chave Hall (SYSOFF), consumo em OFF ≤ 18 µA |
| Firmware | compila para Teensy 4.1; 2 sensores I²C, OFF por Hall, latch SET/KILL, **Full Speed forçado** (compila, não verificado) |
| Alturas | **a placa principal sobe para z 6,8** (face de baixo), definida pelo **P2 XUNPU** (≈ 5,0 sob a face) |
| Bateria | B1 +1 mm / B2 +8,5 mm / B3 +10,5 mm à esquerda; autonomia 8,1 / 9,7 / 11,3 h |
| RESTRICOES_CASE.md | **24 itens**, **6 mudam o lado de fora** (R02, R03, R07, R08, R09, R17; abaixo) |
| STEP que faltam | bateria (B1/B2/B3) · MKL02 · ímãs (cilindros pelas medidas) · SRBV/pot (saíram) |

## 2. Itens do RESTRICOES_CASE.md que mudam o lado de fora (precisam da aprovação do J)

| ID | O que muda por fora |
|---|---|
| **R02** | **Furo do USB‑C na parede de trás: 9,0 × 3,6 mm, centro em z ≈ 5,2** (a placa está em z 6,8, não mais 3,8) |
| **R03** | **Furo do P2 na parede esquerda: Ø6,2, centro em z ≈ 4,0**, y = 59,5; a 1,2 mm da baia da bateria |
| **R07 / R08** | **Planta cresce à esquerda: B1 +1 mm, B2 +8,5 mm, B3 +10,5 mm** (239 → 240 / 247,5 / 249,5); o USB‑C fica a 24 / 32,5 / 34,5 mm da quina |
| **R09** | **Plataforma dos registros +1,0 mm** (opcional) para dar folga ao conjunto de ímã e cabeça sob o tampo |
| **R17** | **Anel leitoso de LED no tampo** em volta do knob de volume (peça nova, Ø23,2/Ø20,8 × 1,5) |

## 3. Envelopes conferidos contra os STEP das peças novas (`modelos/index.json`)

| Peça | STEP (mm) | Conferência |
|---|---|---|
| **KS‑33D** | 14,6 × 14,6 × 13,1 | ✔ (R1SL) |
| **RT1062 DVJ6B** (SamacSys) | 12,0 × 12,0 × 1,52 | ✔ cabe sob a placa (folga 3,7) |
| **USB‑C HRO M-12** | 8,94 × 7,9 × 4,1 (z −0,85…3,25) | ✔ 3,25 sob a face |
| **P2 XUNPU PJ-327A** | 14,2 × 8,6 × 5,4 (z −2,9…2,5); corpo 4,4 `[L]` | ⚠ **define a placa**: leitura ambígua do STEP (a origem do modelo não é o plano dos pads); usei 5,0 sob a face, da geometria validada da V3; **confirmar com o STEP no passo 2** |
| FFC KH-FPC0.5 H1.0 | 6,01 × 3,5 × 1,02 | ✔ 1,0 sob a face; contato dos dois lados |
| TMAG5273 A2/B2 | 2,81 × 2,9 × 1,65 | ✔ sob a placa (folga 3,5) |
| DRV5032ZE | 2,51 × 2,9 × 1,05 | ✔ |
| FNR3015 | 3,0 × 3,0 × 1,52 | ✔ (era 2,61) |
| JST SH 3 vias | 2,9 de altura `[L]` (STEP não baixado) | ✔ 2,3 de folga |
| TMAG5253, 74HC595, BQ24075, SGTL5000, TPS63001, LED, cristal, PROG | 0,4–1,55 | ✔ |

Alturas da principal: **face de baixo z 6,8 = 1,6 (piso) + 5,0 (P2) + 0,2 (margem)**. Com isso o topo da placa é z 8,0 e o conjunto dos knobs (`case/img/knobs_corte.svg`) fecha assim: **registros** (tampo z 14,0, face de baixo do tampo sob o poço z 11,3, cabeça da haste z 9,0–11,0 → **0,3 de folga axial**), **volume** (tampo z 21,0 → 7,3 de folga).

## 4. Knob magnético (opção C): proposta do Design

(Desenho cotado: `case/img/knobs_corte.svg`, gerado por `case/knobs_corte.py`.)

- **Poço** Ø17,6 × 1,2; **piso sob o poço 1,5 mm** (do tampo) mais um **colar de 3,0 mm acima do piso do poço** (OD 9,0, furo Ø5,4): **mancal de 4,5 mm** para a haste Ø5,0 (0,2 mm de folga por lado, MJF).
- **Haste e retenção:** a haste PA12 tem uma **cabeça** sob o tampo (Ø10 nos registros; Ø19 no volume): a haste **sobe de baixo** pelo mancal e o **knob encaixa por cima** (garras de pressão). A cabeça é a própria retenção (não cabem 0,8 mm de canal para anel/arruela).
- **Ímã de ângulo:** Ø6 × 2,0 diametral (**a SPEC dizia Ø6 × 2,5 “a confirmar”: com a placa a z 6,8 e o tampo dos registros a z 11,3, só cabem 2,0 + 0,5 de pele de PA12**) no fundo da cabeça, a **0,5 mm acima da placa** (z 8,5); **ímã → sensor = 2,5 mm** (face do ímã ao centro do chip na face de baixo), 3,5 mm do centro do ímã; campo estimado 80–150 mT (faixa do sensor ±266 mT).
- **Cliques:** sem esfera/mola (não há 2 mm). **Registros:** 7 reentrâncias a 45° no colar + 2 braços flexores de PA12 (0,8 mm de espessura) no knob, batentes nos extremos (os 270° de curso). **Volume:** **uma** reentrância forte na posição de OFF (o “clique” ao ligar) + atrito + batentes nos dois extremos. Torque-alvo 15–30 mN·m (a SRBV era 30 ± 15) a **medir no protótipo**. **Risco R13 aceito:** vida de um flexor de PA12 MJF desconhecida.
- **Anel de LED do volume:** LED 1615 de montagem reversa a **11 mm do eixo**, atravessando um furo na placa; a luz passa **ao lado** da cabeça Ø19 (raio 9,5) e sobe até um **anel leitoso Ø23,2/Ø20,8 × 1,5** encaixado no tampo; o PA12 MJF cinza não difunde: precisa da peça separada (R17).
- **OFF por Hall:** o segundo ímã (Ø4 × 2,0) fica na cabeça do volume a **7,2 mm do eixo**, sobre o DRV5032ZE na face de baixo; o ímã central de Ø6 dá no máximo ~13 mT lá (BOP mínimo 33 mT).

## 5. Pontos que só o protótipo fecha

Campo real no sensor e na chave Hall (as contas são analíticas), pulso de SET do latch, vida do flexor, folga axial de 0,3 mm com a tolerância do MJF (±0,3), Full Speed forçado no host.

## Perguntas para o design

1. **P2 define a placa em z 6,8** (≈ 5,0 mm sob a face). Aprova isso (a placa 3,0 mm acima da régua da fileira 1), ou prefere o **bolso de 0,6 mm** no piso sob o jack (placa em 6,2) ou procurar um P2 mais baixo? Os furos do USB‑C (z 5,2) e do P2 (z 4,0) saem dessa escolha.
2. **Bateria:** B1 (+1 mm; sem NTC → R259 e fornecedor ainda por achar), B2 (+8,5 mm; versão com fios não confirmada) ou **B3** (+10,5 mm; NTC e 3 fios, Farnell 56427 201 018)? A escolha define o crescimento do case à esquerda e a distância do USB‑C à quina.
3. **Folga dos registros:** aceita **0,3 mm de folga axial** (e ímã de 2,0 mm) com o tampo na altura atual, ou **sobe 1,0 mm a plataforma dos registros** (exterior; folga 1,3 e ímã de 2,5 como na SPEC)?
4. **Anel de LED no volume:** aprova uma peça leitosa separada no tampo (Ø23,2/Ø20,8 × 1,5) ou prefere um furo/pipe de acrílico de 3 mm só num ponto?
5. **Plugue da bateria:** nenhuma das três vem com **JST SH**; aceita que o J solde/crimpe o plugue (J202 SH de 3 vias, 2,9 mm, na face de baixo) em vez do JST PH de topo?
6. **Retenção só pela cabeça da haste** (knob entra por cima, haste por baixo) em vez de anel/arruela: aceita a montagem com a tampa virada e o knob por último?
7. **Posição do OFF** do volume: o ímã de OFF a **7,2 mm do eixo**, no ângulo do clique (batente CCW); em que ângulo (em relação ao “para a frente” do teclado) fica o OFF no desenho do Chat (`knobs7.svg` / marcação em arco)?
