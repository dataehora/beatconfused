# eTutti Slim · Eletrônica (SPEC R2SL, etapa 1 — portão A)

Atende a **SPEC R2SL §8, item 1** (refaz só o que mudou desde a R1SL / PR #210). Nada é colocado, roteado, cotado ou comprado. Independente da V4.

## 1. O que mudou e o que ficou

| Entrega | Onde | Estado (25 nov 2026) |
|---|---|---|
| Esquema da **principal** (P processador, E energia, F fone, I interface, R conectores das réguas) | `pcb/schematic.py` → `pcb/kicad/` | **ERC 0 erros / 0 avisos**, netlist = declarada; 120 peças, 87 redes |
| Esquema da **régua R8** | `pcb/regua/schematic_regua.py` | **ERC 0 / 0**; 20 peças (FFC trocado para o de 1,0 mm) |
| RT1062 **DVJ6B**: footprint e mapa de bolas × SamacSys | `pcb/confere_rt1062.py` | **196/196 pads, desvio de posição 0,0000 mm, 0 diferenças de nome**; diâmetro do pad 0,394 (SamacSys) × 0,35 mm (esquema): a eletrônica mantém 0,35 no posicionamento/roteamento (máscara 0,45), decisão do passo 2 |
| BOM conferida (LCSC + JLCPCB, classe, estoque), sem cotação | `pcb/bom_esquema.csv`, `pcb/bom_regua.csv`, `fornecimento/bom_conferido.{csv,json}` | 48 códigos, 140 peças, **24 tipos Extended** (eram 21) |
| Mapa de pinos | `pcb/PINOS.md` (gerado por `pcb/pinos.py`) | 21 pinos; conferido contra o sketch (15/15) |
| Saíram | pot com chave (SW401), SRBV (SW402), escada R401–R408, chave de empurrar/clique do pot, latch por borda do pot | — |
| Entraram | 2 × TMAG5273, chave Hall DRV5032, latch de energia, KILL/SET, USB-C e P2 da V4 por baixo, FFC 1,0 mm, indutor 1,5 mm, JST SH 3 vias da bateria | — |
| STEP | `modelos/` (`fetch_models.py`; 18 baixados + RT1062 da SamacSys) | medidas em `FIT_CHECK.md` |

Rodar (raiz do repositório): `python etutti/hardware/slim/pcb/schematic.py`, `.../pcb/regua/schematic_regua.py`, `.../pcb/pinos.py`, `"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" -X utf8 .../pcb/confere_rt1062.py`, `.../fornecimento/conferir_bom_slim.py` (~3 min).

## 2. Knobs magnéticos: escolha dos sensores

**Sensor de ângulo: TMAG5273 (TI), versões A2 e B2** (SOT-23-6, 2,9 × 2,8 × 1,65 mm).

| Critério | TMAG5273A2/B2 | AS5600 | MT6701 |
|---|---|---|---|
| Endereço I²C com o SGTL5000 (0x0A) no mesmo barramento | **4 endereços de fábrica**: A = **0x35**, B = **0x22**, C = 0x78, D = 0x44 → **dois sensores sem conflito** | **fixo 0x36**: dois no mesmo barramento colidem (só o AS5600L tem endereço configurável) | fixo 0x06 (I²C) |
| Campo no sensor | faixa ±133/±266 mT (A2/B2) ou ±40/±80 mT (A1): cobre o ímã de Ø6 × 2 a ~3,5 mm (~80–150 mT, estimativa de dipolo; ver §3) | 30–70 mT recomendado: o ímã “satura” de perto | 10–100 mT |
| Resolução | ângulo CORDIC de 13 bits (1/16°), 4 × em XY | 12 bits | 14 bits |
| Consumo | 2,3 mA contínuo (1,2 µA em wake-and-sleep de 5 s; ~160 µA com intervalo de 1 ms) | 6,4 mA | 10 mA |
| Alimentação | 1,7–3,6 V (a 3,3 V da placa) | 3,3/5 V | 3,3–5 V |
| LCSC | A2 C3020565 (**60** em estoque), B2 C41935525 (**416**); A1 C3716049 (3241) existe como reserva do 0x35 | SOIC-8 | SOP-8 |

Escolha: **U401 = TMAG5273A2 (0x35) → registros; U402 = TMAG5273B2 (0x22) → volume**, ambos na face de baixo, sob o eixo do knob, no mesmo barramento I²C (pinos 18/19, 2,2 kΩ já existentes). Faixa ±266 mT (registro `SENSOR_CONFIG_2` = 0x07) e ângulo XY (`ANGLE_EN` = 01, registros 0x19/0x1A). Risco: estoque do A2 (60 peças); reserva = A1 (0x35, ±40/±80 mT) com ímã menor (Ø4 × 2). O consumo de 2 × 2,3 mA entra na conta da bateria.

**Chave Hall do OFF do volume: DRV5032ZE (TI, C266118, SOT-23, 5509 em estoque).** Omnipolar (qualquer polo), saída em **dreno aberto**, **BOP 33–63 mT** e BRP 30–58 mT (a versão menos sensível), **2,3 µA** a 20 Hz, 1,65–5,5 V: alimentada **direto pela bateria**. Por que a ZE e não a FA (BOP 1,5–4,8 mT, 1,6 µA, push-pull, 58 mil em estoque): o ímã **central** do knob (Ø6) dá ~5–13 mT a 8–9 mm do eixo, o que **dispararia a FA** em qualquer ângulo; com a ZE o ímã de OFF (Ø4 × 2, ~100–120 mT a 2,2 mm) tem margem ≥ 1,5 × sobre o BOP máximo, e o ímã central, margem ≥ 2,5 × sob o BOP mínimo (33 mT). A conta usa fórmulas analíticas, **não** foi medida (item de bancada).

## 3. Lógica de energia (BQ24075 + SYSOFF + chave Hall + USB)

Fato do datasheet: **SYSOFF tem pull-up interno de ~5 MΩ no VBAT**; alto = bateria desconectada do OUT (e, com adaptador, carga desligada). Logo, sem acionamento a placa está desligada, e basta **puxar o SYSOFF a GND** para ligar.

```
 VBAT ─ R250 1M ─┬─ HALL_X ── Q202 (g)        U403 DRV5032ZE: OUT baixo = ímã de OFF presente
 (U403 OUT) ─────┘      │
                        ├─ Q209 (g) → KNOB_N (pino 25, 0 = ligado) , R258 100k no 3V3
                        └─ C251 100n → SETG (R253 1M) → Q205 : BORDA de subida arma o latch

 latch ARM/ARMB: Q203/Q204 cruzados, R251/R252 1M (uma conduz sempre: ~3,7 µA)
   SET  (pino 6)  → Q206 → puxa ARMB   | KILL (pino 10) → Q207 → puxa ARM
 SYSOFF ── Q201 (g = ARM) ── ONX ── Q202 (g = HALL_X) ── GND     (série: latch armado E knob fora de OFF)
 SYSOFF ── Q208 (g = ½ VBUS)  ── GND                                (USB presente)
```

| Situação | SYSOFF | Resultado |
|---|---|---|
| Knob em OFF (ímã sobre a chave), sem USB | alto | **bateria desconectada em hardware** (Q202 aberto), qualquer que seja o latch |
| Knob sai de OFF (sentido horário) | baixo | HALL_X sobe → C251 arma o latch (pulso ~0,1 s) → Q201+Q202 conduzem → OUT, 3,3 V e RT1062 sobem; o latch segura sem o firmware. O “clique” é o detente mecânico no OFF (Design), não um interruptor |
| Knob ligado | baixo | liga/desliga só pela chave Hall |
| Desligamento automático (15 min sem uso, ou bateria < 3,3 V por 5 s) | alto | o firmware dá um pulso em **KILL** (50 ms): o latch desarma, SYSOFF é solto, a placa morre **e não reinicia** (HALL_X continua alto, sem nova borda); para religar é preciso levar o knob a OFF e voltar |
| USB presente | baixo (Q208) | carrega e alimenta com o knob em OFF (“soft off”: mudo, LED de carga, MIDI vivo); com o knob ligado, o firmware dá **SET** (pino 6) na partida: ao tirar o cabo a bateria assume |
| USB sai, knob em OFF | alto | desliga |

**Consumo em OFF (pior caso, 4,2 V, 85 °C):** DRV5032ZE ~3 µA + pull-up R250 (chave conduzindo) 4,2 µA + latch 4,2 µA + BQ24075 sleep (IBAT(PDWN) ≤ 6,5 µA) + fugas ≈ **≤ 18 µA**; típico ~10 µA. **Vida em prateleira só pela eletrônica:** 1000 mAh × 0,9 / 18 µA ≈ 50 000 h ≈ **70 meses** (B1); 1260 mAh úteis (B3) ≈ 97 meses. A **autodescarga da célula** (LiPo ≈ 2–3 %/mês) é muito maior e manda: a eletrônica não é o fator limitante. Todos os transistores são AO3400A/AO3401A **Basic**.

Pontos que só a bancada fecha: a temporização do pulso de SET (C251 × R253 = 0,1 s × a perda de capacitância do X5R sob tensão), o disparo real da chave Hall com o ímã do knob (campos de §2 são analíticos) e o corte limpo do SYSOFF (BQ24075) com Q201/Q202 em série.

## 4. Peças pedidas pela R2SL

| Função | Escolha | LCSC / classe / estoque | Observação |
|---|---|---|---|
| Processador | **MIMXRT1062DVJ6B** (12 × 12, 0,8) | C3216699 · Ext · **1** (consignado) | footprint/símbolo conferidos (§1); STEP 12,0 × 12,0 × 1,52 |
| USB‑C | HRO TYPE-C-31-M-12 | C165948 · Ext · 426 mil | face de baixo, JLCPCB; STEP 8,94 × 7,9 × 4,1 (z −0,85…3,25) |
| P2 | XUNPU PJ-327A | C49284723 · Ext · 3250 | face de baixo, JLCPCB; STEP 14,2 × 8,6 × 5,4 (z −2,9…2,5); corpo 4,4 mm (LCSC); pads: 2/5 manga, 6 anel, 4 ponta, 3 chave da ponta |
| FFC | KH-FPC0.5-H1.0SMT-8P-QCHF | C3250113 · Ext · 2374 | **contatos dos dois lados, entrada por cima ou por baixo** (resposta à dúvida da SPEC); 1,0 mm de altura; STEP 6,01 × 3,5 × 1,02; os 4 cabos FFC têm de ser de 0,3 mm de espessura (0,5 mm de passo) |
| Indutor do TPS63001 | **FNR3015S2R2MT** (2,2 µH, 2 A) | C167747 · Ext · 81 mil | **1,5 mm** (era o FNR4020 de 2,6 mm): regra de alturas (a); STEP 3,0 × 3,0 × 1,52. A corrente média é ~0,15 A, o pico do TPS63001 em carga leve é pequeno |
| Conector da bateria | **JST SH 3 vias** SM03B-SRSS-TB | C160403 · Ext · 20 715 | **2,9 mm**, face de baixo (regra a: o PH de 5,5 mm não cabe). Nenhuma das 3 baterias traz SH: o J solda/crimpa o plugue |
| TS do BQ24075 | R259 10 kΩ (**não montar** com B2/B3) | C25744 Basic | só para a B1 (2 fios, sem NTC) |

## 5. Baterias B1 / B2 / B3 (nada comprado)

Corrente da placa ≈ 105 mA na bateria (FIRMWARE.md); 85 % da capacidade útil.

| | **B1** LP402764-1000 | **B2** VARTA LPP 503562 S | **B3** VARTA LPP 503759 8HH |
|---|---|---|---|
| Fabricante / folha | genérico (Shenzhen); folha de dados num fórum da TI, capacidade ambígua | **VARTA** (folha de dados na Farnell, 2026390/2026391) | **VARTA** (folha na Farnell, 2026384; e no fórum da TI) |
| Capacidade | 1000 mAh (conferir) | 1150 mín. / **1200 típ.** | 1320 mín. / **1400 típ.** |
| Medidas | **máx. 4,5 × 28 × 68** | célula máx. 5,0 × 35 × 62 (Adafruit: pack 34 × 62 × 5); **pack com PCM a conferir** | distribuidores: 5,2–5,4 × 37–37,5 × 60–60,5 (a folha não dá o contorno): **conferir** |
| PCM / NTC | PCM 1,5 A; **sem NTC** → R259 10 k no TS | PCM; **NTC 10 kΩ B 3435** + resistor de ID | PCM; **NTC 10 kΩ B 3380**, sem ID; fios AWG24: vermelho (+), branco (NTC), preto (−) |
| Conector | ZHL1.25 (ou fios) | **a variante 56456 701 099 da Farnell tem contatos de pressão (snap)**, não fios: a versão com fios não foi confirmada | **fios soltos** (3 fios) |
| Distribuidor / pequena quantidade | nenhum achado: **não** | **Farnell 56456 701 099** (1 un.), mas é a variante snap: **sim, com ressalva** | **Farnell 56427 201 018, ~€ 16, estoque “10+”**; Texim: MOQ 600: **sim (Farnell)** |
| Baia / case | 29 × 69,5: **+1 mm** à esquerda (ou à frente) | pack ≥ 35 + folga 0,75 × 2 = **36,5**: **+8,5 mm** à esquerda | pack ≥ 37,5 + 1 = **38,5**: **+10,5 mm** à esquerda |
| Espessura (> 4,5) | n/a | 5,0: folga ao tampo ≥ 2,5 mm (piso 1,6 + 5,0 = 6,6; tampo ≥ 9,5 por cima da baia) | 5,2–5,4: idem, folga ≥ 2,3 mm; **não toca na placa** (a baia fica fora da faixa x −57…−33) |
| Autonomia (≈ 105 mA) | **~8,1 h** | **~9,7 h** | **~11,3 h** |

Resumo: **B3 dá mais autonomia, NTC de verdade e é a única com pacote vendável em pequena quantidade com fios de 3 vias, ao custo de +10,5 mm no lado esquerdo**; B1 é a que não muda o lado de fora, mas depende do R259 e de fornecedor ainda não identificado; B2 só vale se o fabricante confirmar a versão com fios. O J escolhe e manda o STEP.

## 6. Alturas sob a placa e altura mínima da placa principal

Folga sob a placa = face de baixo da placa − piso (z 1,6). Peças da **face de baixo** (STEP / LCSC):

| Peça | Altura sob a face de baixo | Observação |
|---|---|---|
| **P2 XUNPU PJ-327A** | **≈ 5,0** (eixo a 2,8 da face na geometria da V3, meia altura 2,2 do corpo de 4,4; o STEP dá 5,4 de ponta a ponta) | **a mais alta: define a placa**; ver `RESTRICOES_CASE.md` R01 |
| USB‑C M-12 | 3,25 (pernas −0,85 atravessam a placa) | |
| JST SH 3 vias | 2,9 | |
| TMAG5273 (2 ×) | 1,65 | |
| DVJ6B BGA | 1,52 (STEP) | |
| FNR3015 | 1,52 | |
| DRV5032ZE | 1,05 | |
| 74HC595, FFC H1.0, BQ24075, SGTL5000, TPS63001, TMAG5253, LED, cristal | 0,4–1,05 | |

**Altura mínima da placa principal: face de baixo em z = 1,6 + 5,0 + 0,2 (folga) = 6,8 mm** (topo da placa 8,0 com 1,2 mm de espessura), **definida pelo P2**; com um bolso de 0,6 mm sob o jack (o piso mínimo sob o bolso é 1,0 mm) cairia para 6,2 mm. Isso é **3,0 mm acima** da face de baixo da régua da fileira 1 (3,8) e **entre** as das fileiras 2 e 3 (5,8 e 7,8). Tudo o mais cabe nessa folga (4,6 mm) com ≥ 1,7 mm de sobra.

## 7. Par USB e Full Speed

Aceito pela SPEC. Foi **comprovado no sketch** que `USB1_PORTSC1 |= USB_PORTSC1_PFSC` compila; que forçar Full Speed funciona com a Teensy 4.1 num host real **não foi verificado** (precisa de placa): fica como item de bancada.

## Perguntas para o design

As perguntas completas (inclusive as de posicionamento) estão em `FIT_CHECK.md`, no fim.
