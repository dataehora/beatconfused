# eTutti Student V4 · relatório da eletrônica

**SPEC atendida: R1V4 e R2V4 (21 nov 2026), tarefas de eletrônica: E1, E2, E3 (verificação de custo da R2V4), E4, E5.**
Data: 21 nov 2026. Nada foi posicionado, roteado, encomendado nem gerado em `fab/`: é estudo (Fase A). A V3, a V2 e a V1 não foram tocadas.
Scripts novos (reproduzem os números): `calculos_eletronica.py` (E2, E3), `fornecimento/precos_jlc.py` (preços e classe na
biblioteca da JLCPCB, 21 nov, curl de 2 em 2 s). Contrato com a programação: `pcb/PINOS.md` (rascunho já entregue).
Convenção: **(conferir)** = sem medida ou datasheet conferido; **estimativa** = conta minha, sem cotação.

## 0. Resumo

| Pergunta | Resposta |
|---|---|
| A varredura sem multiplexador funciona? | **Sim.** TMAG5253 BA3: liga em 20 us típico, **45 us máximo** (a 95 %). Com 60 us de espera + 6 us de leitura: **28 teclas em 0,56 ms, 76 em 1,4 ms** (a V3 ~0,25 ms, estimativa). Velocity pede interpolação e varredura rápida da coluna "quente" (§2). |
| OUT compartilhado aguenta? | **Sim:** 20 sensores + trilha + cabos = **~490 pF** estimados, limite do datasheet 1000 pF. |
| Corrente | 4 sensores ligados: **10,4 mA típico, 20 mA máximo** (V3: 36 mA típico, 14 sensores). |
| Pinos | Sobram: usa 27 dos 46; **livres 1, 4, 5, 13, 29-45**. Cabe 76 teclas, e 8 linhas OUT se for preciso. |
| Registrador | **74HC595D, LCSC C5947, SO-16, é Basic** (US$ 0,10). Os 74HC164 e 4094 são todos Extended. |
| Custo F2 x F1 (28 teclas, pedido mínimo, sem frete) | **F2 US$ 292-371 (com a impressão MJF real do design, US$ 51,2), F1 US$ 332-477: F2 sai 12 a 22 % mais barata, não mais cara.** Passa no critério de 25 % com folga (§3). (O design cita 296-375: diferença de ~US$ 4 em ferragem.) |
| Custo de +16 teclas na F2 | eletrônica **~US$ 13** (4 réguas no mesmo pedido) + teclas US$ 14,6; ver §3.4. |
| Par USB | ≤ 10 mm, B.Cu sobre In2 (GND inteiro), **w 0,24 / s 0,15 mm = 91 ohm** no empilhamento JLC04121H-7628 (§4). |
| Régua | 4 sensores + 1 595 + 2 conectores JST SH 6 vias (clone XYECONN, US$ 0,07), 2 camadas, **74 x 14 x 1,2 mm, painel de 5 (88 x 84 mm)** (§5). |
| Alto-falante real | **Dayton Audio CE28MB-8**: Ø 28 x 4,5 mm, Fs 623 Hz, Qts 1,63, Vas 21,5 cm3 (§1.3). |

## 1. E1 · a BOM da V3, linha a linha

Fonte: `student_v03/bom_v3.csv` (34 linhas, 130 peças, 17 tipos Extended) e preços de 21 nov (`precos_jlc.json`).
"Basic" = sem taxa de US$ 3,09 por tipo. Pacote x footprint: as linhas da V3 já foram conferidas pelo `cpl_jlc.py` e pela
`AUDITORIA.md` da V3 e **não mudam**; os dois códigos novos estão marcados.

### 1.1 Linhas que ficam, e se há Basic

| Linha (código LCSC) | Classe | Existe Basic equivalente? | Decisão na F2 |
|---|---|---|---|
| 100 nF C1525, 1 uF C52923, 2,2 uF C12530, 10 uF C19702 / C15850 | Basic | já são | ficam; 41 de 100 nF caem para 10 na principal (31 vão para as réguas ou somem) |
| Resistores C25076, C25905, C25879, C25867, C25744, C25741, C26083, ferrite C1002, BAV70 C68978, AO3401A C15127, TS-1187A C318884 | Basic | já são | ficam |
| SMF5.0A C151296 (D201, TVS) | Extended | **não**: SMAJ5.0A (C113952, SMA) também é Extended e maior | fica (decisão do J: TVS e USBLC6 ficam) |
| USBLC6-2SC6 C7519 | Extended | **não** (UMW C2687116 e TECH PUBLIC C558442 também Extended, US$ 0,05 contra 0,16: só preço) | fica; trocar por UMW economiza US$ 0,2, sem relevância |
| J202 JST PH 3 vias C265101 (bateria) | Extended | não (clones PH2.0 C668618/C668620 também Extended; só 2 vias nas buscas) | fica o JST original (plugue da bateria) |
| J401 SM04B-SRSS-TB C160404 (tela) | Extended | não | fica; **ou** usar o mesmo SH de 6 vias da régua e um cabo de 6 fios (corta 1 tipo, US$ 3,09) |
| J301/J302 PJ-327A XUNPU C49284723 | Extended | não há jack 3,5 mm Basic | fica |
| L201 2,2 uH C167825 (FNR4020S) | Extended | não (os 2,2 uH baratos são 0603/0805 de sinal, sem a corrente do TPS63001) | fica |
| J101 M.2 C48985906 | Extended | não | fica; **pacote x footprint conferido na V3** |
| U301 SGTL5000 C2651833, U501 MAX98357A C910544, U204 TPS63001 C28060, U202 BQ24074 C54313 | Extended | não há equivalente Basic | ficam |
| U302 XC6206P182MR C347373 (1,8 V do codec) | Extended | não: ME6211C18M5G-N (C236671) e AP2112K-1.8 (C176944) também Extended | fica |
| J201 USB-C HRO C165948 | Extended | não | fica |
| TMAG5253BA3 C22401868 | Extended | não | fica, agora só nas réguas (1 tipo no pedido das réguas) |
| EC11E18244AU C202365 (casa) | Extended | n/a | solda em casa, fora do pedido |

### 1.2 Linhas que somem da placa principal na F2

| Linha | Qtd | Por quê |
|---|---:|---|
| 74HC4067PW C179326 (U601, U602) | 2 | sem multiplexador (E2) |
| 74LVC1G04 C7827, 74LVC1G08 C7666 (U603-U605) | 3 | só geravam EN_A/EN_B a partir de S3 e SENS_EN |
| TMAG5253 (U701-U728) e os 28 x 100 nF C7xx | 28 + 28 | vão para as réguas (32 sensores: 8 réguas x 4) |
| C601-C603 | 3 | decoupling dos multiplexadores |

**Resultado: 17 tipos Extended na F1 caem para 14 na principal (13 + o conector SH-6) mais 2 nas réguas (TMAG e SH-6), 16 no total.** A meta da R1V4
("menos que 17") é cumprida por 1 tipo, e por 2 se o SH-6 servir também à tela (J401), **sem perder função**.

### 1.3 O que entra de novo (códigos conferidos na biblioteca da JLCPCB, 21 nov)

| Peça | Código | Classe | Estoque | Preço | Observação |
|---|---|---|---:|---|---|
| 74HC595D,118 (Nexperia), SO-16 | **C5947** | **Basic** | 305 318 | US$ 0,10 (0,08 a 50) | footprint SOIC-16 de 3,9 mm de corpo **(conferir pads no EasyEDA, como o `cpl_jlc.py` faz)** |
| Conector SH 6 vias, lateral, 1,0 mm (XYECONN XY-SM06B-SRSS-TB) | **C56123098** | Extended | 5 971 | US$ 0,069 (0,055 a 100) | clone do JST SM06B-SRSS-TB; o original C160405 custa US$ 0,90. **Clone: conferir o footprint e o ajuste do plugue** |
| Alternativas de conector | C225115 (CJT 1,25 mm, 6 vias, US$ 0,12), C38036 (1,25 mm, US$ 0,07), C48735 (FPC 1,0 mm, **estoque 0**) | Extended | | | só Extended: nenhuma é Basic |

**Alto-falante real (decisão 7): Dayton Audio CE28MB-8** ([folha de dados](https://www.daytonaudio.com/images/resources/285-147--dayton-audio-ce28mb-8-spec-sheet.pdf)):
Ø 28 mm x 4,5 mm (cabe nos 5 mm da V3), 8 ohm, Re 7,54 ohm, Le 0,45 mH, **Fs 623 Hz, Qms 2,22, Qes 6,16, Qts 1,63**, **Vas 0,0215 L**, Sd 4,52 cm2, Xmax 0,1 mm,
Mms 0,087 g, SPL 81 dB a 2,83 V/1 m, 1 W RMS / 2 W máx., resposta 620 Hz-20 kHz. Fios soldados em J501 (como na V3). Não está na JLCPCB: compra em loja (preço ~US$ 5-8, estimativa).
**Alternativas com folha de dados** (resultados de busca; **não conferidas aqui**): Visaton K 28 WP-8 (Fs 700 Hz, 76 dB), Same Sky CLS0281 (Fs 500 Hz), Taoglas SPKM.28.8.A (Fs 580 Hz).
Para a caixa: Vas 21,5 cm3 com Qts 1,63 é um alto-falante **sem graves** por natureza; a caixa de 9,75 cm3 da V3 coloca a ressonância perto de 1 kHz
(estudo `estudos/acustica.py` do design); isso vale para qualquer 28 mm. **(conferir: refazer `acustica.py` com estes parâmetros é tarefa do design.)**

## 2. E2 · varredura sem multiplexador (R1V4 §5.2)

Datasheet: [TMAG5253](https://www.ti.com/lit/ds/symlink/tmag5253.pdf) (SBASAI5E, rev. abr 2026; lido em PDF).

### 2.1 Valores do datasheet que entram nas contas

| Parâmetro | BAx (bipolar, o BA3 da V3) | UAx (unipolar) |
|---|---|---|
| tON, do EN subir até OUT a 95 % (CLoad 100 pF) | **20 us típico, 45 us máximo** | 55 / **130 us** |
| Corrente ativa a 3,3 V | 2,6 mA típico, 5 mA máximo | 1,9-2,6 típico, 3,3-4 máx. |
| Corrente desligado (EN baixo) | 8 nA típico | idem |
| Largura de banda | 15 kHz (-3 dB) | idem |
| Resistência de saída | ativo 1,27 (ohm); desligado 9 (Mohm); **a coluna de unidades saiu embaralhada na extração do PDF: (conferir)** | |
| Carga capacitiva | até **1 nF** na saída | |
| Sensibilidade BA3, 3,3 V | 15 mV/mT, repouso 1,65 V (1,61-1,69) | |

A SPEC cita < 25 us (bipolar) e < 60 us (unipolar) como típicos; o datasheet lido (rev. abr 2026) dá 20 / 55 us típicos e **45 / 130 us máximos**; a conta usa o máximo.
Com o BA3 da V3, a conta usa **45 us**. (Se alguém trocar para a variante unipolar, a varredura de 28 teclas passa de 0,56 para ~1,5 ms.)

### 2.2 Princípio

```
                       OUT_R1 ----------- (14)  fileira 1 (frente): 1 fio analógico, 7 ou 8 ... 19 sensores em paralelo
 MicroMod Teensy ----- OUT_R2 ----------- (15)  fileira 2
                       OUT_R3 ----------- (26)  fileira 3
                       OUT_R4 ----------- (27)  fileira 4
                       SCAN_CLK ---------- (3)  \  comuns às 4 fileiras
                       SCAN_DATA --------- (2)  /

 fileira k:  [principal]--cabo--[régua 1: 595 + 4 TMAG]--cabo--[régua 2: ...]--cabo--[...]
                                 SER->QA QB QC QD (EN dos 4 sensores)   QH'-> SER da próxima
                                 OUT dos 4 sensores ligados na mesma linha OUT_Rk (barramento)
```
Ao ligar a coluna c, **um sensor por fileira** responde, cada um na sua linha OUT. As 4 linhas são lidas juntas (2 no ADC1, 2 no ADC2).

### 2.3 Tempo de varredura (45 us é o MÁXIMO do datasheet; a espera usada tem margem)

Modelo: passo = espera + leitura das 4 linhas (~6 us, 2 + 2 conversões em 2 ADCs, **estimativa**, ~3 us cada) + deslocamento do 595 (<1 us, 5 MHz).
O resíduo de assentamento usa um polo único calibrado em "95 % em 45 us" (tau = 15 us, **modelo, não medida**).

| Espera após o EN | Resíduo da coluna anterior | Passo | 28 teclas (8 colunas) | 44 (12) | 60 (16) | 76 (20) |
|---:|---:|---:|---:|---:|---:|---:|
| 45 us (o máximo, "95 %") | 5,0 % | 55 us | 0,44 ms | 0,66 | 0,88 | 1,10 |
| **60 us (valor da V3)** | **1,8 %** | **70 us** | **0,56 ms (1,8 kHz)** | 0,84 | 1,12 | **1,40 ms (0,71 kHz)** |
| 90 us (12 bits limpos) | 0,25 % | 100 us | 0,80 ms | 1,20 | 1,60 | 2,00 ms |
| 60 us com **2 linhas OUT por fileira** (pinos 38-41, **conferir**) | 1,8 % | 70 us | 0,28 ms | 0,42 | 0,56 | 0,70 ms |

Resíduo é o erro de leitura (fração da diferença entre a coluna anterior e esta). Com diferença de até ~1 V (BA3 em +-60 mT), 60 us deixa até ~18 mV
(~1,2 mT); **a firmware deve ler a coluna k depois de uma coluna k-1 em repouso, ou usar 90 us**. Calibração de repouso por tecla absorve o resto.

### 2.4 Resolução de velocity

O firmware da V1 usa 1 ms = 127 e 80 ms = 1 (log): **19,9 passos de velocity por oitava de tempo**. Para o intervalo de 1 ms (o mais rápido):

| Varredura | Erro sem interpolar (+-T/2) | Interpolando entre duas leituras (+-T/8, **estimativa**) |
|---|---:|---:|
| V3, 0,25 ms | +-3,4 passos | +-0,9 |
| **F2 28 teclas, 0,56 ms** | **+-7,1** | **+-1,9** |
| F2 76 teclas, 1,4 ms | +-15,3 | +-4,6 |
| **varredura rápida da coluna quente, 0,07 ms** | +-1,0 | +-0,3 |

**Conclusão:** em 28 teclas a F2 basta **com interpolação** (+-2 passos no extremo mais rápido, igual à V3 sem interpolar). Em 76 teclas, só com **varredura rápida da
coluna quente** (ou 2 linhas OUT por fileira + interpolação). A varredura rápida é possível porque o 595 aceita **acesso aleatório**: empurrar o padrão de 8N bits
leva 160 pulsos de 200 ns = 32 us **durante** a leitura anterior ou como parte do passo (`PINOS.md`). Isso é trabalho do `programacao-som` (P1/P2).

### 2.5 Capacitância da linha OUT (limite 1 nF)

Suposições: sensor 20 pF (o próprio datasheet usa "cerca de 20 pF" para chegar a 50 sensores), trilha 0,7 pF/cm, cabo 1 pF/cm (60 mm por elo), 3 pF por conector, 5 pF no ADC
(**todos estimativa, menos os 20 pF**):

| Réguas na fileira | Sensores | C total | Margem até 1 nF |
|---:|---:|---:|---:|
| 2 (28 teclas) | 8 | ~200 pF | 5x |
| 3 (44) | 12 | ~300 pF | 3,3x |
| 4 (60) | 16 | ~390 pF | 2,5x |
| **5 (76)** | **20** | **~490 pF** | **2x** |

Com a saída ativa de 1,27 ohm e o pull-down de 100 kohm (sugerido no datasheet) a linha carrega e descarrega em ns: o limite de tempo é o tON interno, não a linha.

### 2.6 Corrente

Só 4 sensores ligados por vez: **10,4 mA típico, 20 mA máximo** (V3: 14 ligados = 36 mA típico, 70 mA máximo). Os 595 gastam < 0,1 mA cada. Com a varredura contínua
a corrente média é ~10,4 mA; em repouso (nenhuma tecla há 2 s) a firmware pode reduzir a taxa de varredura e baixar para ~1 mA. A economia sobre a V3 é ~26 mA em ~100 mA do
instrumento (ver `POWER.md` da Viaggio; um `POWER.md` da V4 vem com a Fase B).

### 2.7 Pinos do MicroMod Teensy (detalhe em `pcb/PINOS.md`)

Precisa: 4 ADC (OUT) + 2 (VBAT, HP_DET) + DADO + CLOCK + I2S (4) + I2C (2) + 2 encoders (6) + KEEP, AMP_SD, CHG_STAT. **Total 27 de 46 pinos.** Os 4 OUT ficam em
**14, 15, 26, 27** (CHG_STAT passa do 26 para o 0); todo o resto mantém o número da V3, então o firmware existente não muda de pino. 76 teclas **não pedem pino extra**.

### 2.8 CPU

Busca ocupada de 60 us por passo ocuparia 100 % do laço principal a 28 teclas; o áudio roda em interrupção e não é afetado, mas o resto do laço (MIDI, OLED) ficaria sem tempo.
**Estimativa:** com a varredura por máquina de estados (IntervalTimer a 70-100 us, 2 ISRs por passo de ~2-4 us), a carga fica em **~5 % (28 teclas) e ~8 % (76)**; a síntese do
acordeão amostrado mediu 12-20 % no Teensy 4.0 (CLAUDE.md). **Não medido:** o MicroMod não está disponível; é conta. Cabe a P1 confirmar.

## 3. E3 · verificação de custo (R2V4, item 2)

### 3.1 Base e o que é estimativa

- **Visto na biblioteca da JLCPCB em 21 nov:** preço de cada peça (por faixa de quantidade), classe Basic/Extended.
- **Da cotação do J de 18 nov (V3):** placa de 4 camadas 246,5 x 95 mm, 5 un., engenharia 25,00 + placa 14,50 = 39,50; montagem econômica pelo fundo: preparação 8,24 e estêncil 1,55; US$ 3,09 por tipo Extended.
- **Estimativa (sem cotação):** placa principal da F2 (4 camadas, ~85 x 95 mm: **US$ 14,50 a 39,50**; se a taxa de engenharia de 25 não valer para a placa menor, vai para o piso), régua 2 camadas
  (US$ 5-12), SMT e nitrogênio (3,2 por montagem, valor da página da V3), cabos SH prontos (US$ 3-8), ferragem, impressão do case da F1 (US$ 58-143 = faixa da V3, por volume). **Impressão da F2: US$ 51,2 (MJF, número do design, FIT_CHECK 12.x).** Frete, IVA e alfândega ficam de fora.
- Mínimos da JLCPCB: **2 placas montadas** e 5 placas nuas por desenho. Na F1: 1 desenho. Na F2: **2 desenhos** (principal e régua), cada um com a sua preparação e o seu estêncil.
  Uma montagem de régua = **1 painel de 5 réguas** (design fechou 88 x 84 mm); 2 painéis montados = **10 réguas** (28 teclas usam 8, sobram 2; **44 teclas usam 12: já não cabem no pedido mínimo, pedem +1 painel montado**).

### 3.2 A tabela (US$, pedido mínimo, 28 teclas; baixo-alto)

| Item | F1 plana (V3, só referência) | F2 réguas |
|---|---:|---:|
| Placa principal (PCB) | 39,50 (4L, 246,5 x 95) | 14,50-39,50 (4L, ~85 x 95) **estimativa** |
| Réguas (PCB, 5 painéis de 5) | - | 5-12 **estimativa** |
| Montagem principal: preparação + estêncil | 9,79 | 9,79 |
| Montagem réguas: preparação + estêncil | - | 9,79 |
| Tipos Extended x 3,09 | 17 tipos = 52,53 | principal 14 = 43,26 + réguas 2 = 6,18 -> **49,44** |
| Peças, 2 placas principais montadas | 65,18 | 36,04 |
| Peças, 10 réguas montadas (40 TMAG etc.) | - | 22,54 |
| SMT e nitrogênio | 3,20 | 6,40 |
| Grade FR-4 escareada | 15-30 **estimativa** | 0 (a T3 é a tampa) |
| Parafusos, porcas, pés | 10-20 **estimativa** | 6-12 **estimativa** |
| Cabos SH 6 vias (8) e conectores | 0 | 3-8 **estimativa** (conectores já nas peças) |
| Impressão do case | 58,5-143 **estimativa, V3** | **51,2 (MJF, design)** |
| **Subtotal que difere** | **253,7-363,2** | **213,7-256,7** |
| Comum às duas: teclas 25,6, módulo 27, bateria 8, OLED+cabo 10, alto-falante CE28MB-8 6,5, tela acústica 8, USB 3, kit M2,5 4, 2 encoders 4,4 | 78,6-114,0 | 78,6-114,0 |
| **Total do instrumento de 28 teclas** | **332-477** | **292-371** |
| **Diferença F2 contra F1** | | **-12 % (baixo) / -22 % (alto)**; no subtotal que difere: -16 % / -29 % |

A parte da F1 que corresponde só à eletrônica (39,50 + 9,79 + 52,53 + 65,18 + 3,2 = 170) bate com a faixa de US$ 172-183 da V3.
**Pior canto** (F2 alto 371 contra F1 baixo 332) = **+12 %**, ainda abaixo de 25 %. Para a F2 passar de F1 + 25 % no cenário central, faltaria a F2 custar **~US$ 120 a mais** em itens hoje estimados (PCB principal, painel de réguas recusado e refeito pela JLCPCB, ferragem): improvável. **Sigo sem parar (R2V4, item 2).**

### 3.3 Onde a F2 ganha e onde perde

| | Ganha | Perde |
|---|---|---|
| Placa grande de 4 camadas, grade e impressão | 0 a -25 (PCB principal menor), -15 a -30 (sem grade), impressão MJF 51,2 contra 58,5-143 | |
| Multiplexadores e lógica | -3 tipos Extended (-9,27), -29 de peças | |
| Segunda montagem (réguas) | | +9,79 de preparação, +6,18 de Extended, +3,2 de SMT, +5-12 de PCB |
| Cabos | | +3-8 |
| Flexão da placa | a régua apoiada inteira no degrau tende a 0 mm de flexão | |

**Se for preciso reduzir a F2** (não é, mas ficam as alavancas, em ordem de ganho): (a) tela no mesmo SH-6 da régua: -3,09; (b) régua e principal no **mesmo pedido**
(JLCPCB cobra a preparação por desenho: não ajuda); (c) **solda direta entre réguas** no lugar de conectores: -6,18 (tipo SH-6 das réguas) -8 de cabos, +25 min de solda em casa e perde a troca fácil (§5.2);
(d) 28 teclas usam 8 das 10 réguas montadas: 2 sobram; (e) trocar USBLC6 por clone: -0,2.

### 3.4 Custo incremental de cada módulo de +16 teclas na F2

| | US$ |
|---|---:|
| 4 réguas no mesmo pedido das primeiras (peças + PCB + 4 cabos) | **~13** |
| 4 réguas em pedido separado (10 réguas montadas) | ~52 |
| 16 teclas Gateron | 14,6 |
| 16 botões + 74 mm de case | a pedir ao design (28 teclas = 51,2) |
| Eletrônica da principal | 0 (a principal não cresce) |

As 10 réguas do pedido mínimo cobrem 28 teclas (8); **44 teclas pedem 12 réguas: +1 painel montado** (a preparação e os tipos Extended das réguas já estão pagos só se for no mesmo pedido; senão ~US$ 52). 60 teclas (16 réguas) pedem 2 painéis montados a mais.
Na F1 cada módulo alarga a placa de 4 camadas em 74 mm: o preço da PCB principal sobe com a área (estimativa não feita: fora do escopo da R2V4, que pede a F1 só no caso de 28).

## 4. E4 · par USB (R1V4 §5.4)

**Empilhamento padrão JLCPCB para 1,2 mm, 4 camadas: JLC04121H-7628** (F.Cu 35 um, prepreg 7628 de 0,2104 mm Dk 4,4, In1 15 um, núcleo 0,6, In2, prepreg 0,2104, B.Cu).
Publicado pela JLCPCB, vale **sem pedir controle de impedância**. Solver 2D da Viaggio (`viaggio/pcb/impedance.py`, comparado com IPC-2141A e com um ponto do calculador da JLCPCB):

| w (mm) | s (mm) | Zdiff (solver) | IPC-2141A |
|---:|---:|---:|---:|
| 0,20 | 0,127 | 91,7 | 98,4 |
| 0,22 | 0,127 | 88,7 | 94,2 |
| **0,24** | **0,15** | **91,2** | 93,7 |
| 0,26 | 0,15 | 88,4 | 90,0 |

**Proposta: w = 0,24 mm, s = 0,15 mm -> 91 ohm** (+-10 % na largura de fabrica = ~86-96 ohm). As camadas externas são simétricas: o par vai em **B.Cu sobre In2 = GND inteiro** (a In1 fica
para +3V3 e sinais lentos). As peças do USB (USB-C, USBLC6, J101) ficam no fundo, então **sem via**.
1. **Comprimento <= 10 mm** (V3: 17,2). Critério físico: tempo de subida do USB de alta velocidade 500 ps / (6 x 5,6 ps/mm, e_eff 2,85) = **14,8 mm** é o comprimento "elétricamente curto";
   **10 mm cabe com folga de 1,5x mesmo se a conexão negociar 480 Mbit/s.** A 12 Mbit/s (tempo de subida >= 4 ns, 118 mm) é irrelevante. Diferença entre D+ e D-: <= 0,15 mm.
2. **Referência contínua:** a In2 inteira sob o par e 1 mm de cada lado, sem fenda, sem trilha de sinal na In2 sob ele; ilhas de cobre da In2 só de GND. O pour de +3V3 da V3 na In2 **não** pode repetir.
3. **Full Speed:** é do `programacao-som` (P1): o bit PFSC do PORTSC1; se não for possível, 1 + 2 bastam.
4. **Posicionamento (Fase B):** USB-C e M.2 lado a lado. Orçamento do trecho: pad do USB-C -> USBLC6 ~2,5 mm, através do ESD ~1,5, até o pad 3/5 do J101 ~5-6 mm = **~9-10 mm. Só fecha se o USB-C ficar a <= 7 mm da linha dos pads 3/5 do M.2 (estimativa de geometria, a confirmar ao posicionar).**
   O resistor R202 do CC2 fica fora do corredor, como na V3.

É cálculo, não medida: o teste da primeira placa (velocidade negociada, MIDI contínuo) continua valendo.

## 5. E5 · a régua universal de 4 teclas (R2V4, itens 3 e 5)

### 5.1 Esquema de princípio (uma régua, tudo no fundo)

```
 Conector IN (SH 6 vias)          74HC595D (U1, SO-16)                          4 x TMAG5253BA3 (U2..U5)
 1 +3V3 ------+------------------ VCC(16)    C1 100 nF + C2 10 uF 0805 junto ao pino     VCC(1) <- +3V3, 100 nF cada
 2 GND -------+------------------ GND(8), OE(13)                                          GND(2)
 3 OUT --------+----------------- (barramento) -----------------------------------------> OUT(4) dos 4 sensores unidos
 4 CLK  --------------------------- SRCLK(11) + RCLK(12) juntos                            EN(3) <- QA(15) QB(1) QC(2) QD(3)
 5 SER  --------------------------- SER(14)         SRCLR(10) -> +3V3
 6 reservado (OUT_B)                QH'(9) -> pino 5 do conector OUT (cascata)    QE-QH (4-7): sem uso
 Conector OUT (SH 6 vias): 1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 = QH' (por 100 ohm), 6 reservado -- iguais aos do IN por trilha direta
```
- 14 peças por régua: 4 TMAG, 1 595, 2 SH-6, 6 capacitores (5 x 100 nF + 1 x 10 uF), 1 x 100 ohm no QH'.
- Pull-down de 100 kohm por linha OUT e os 100 ohm de CLK/DATA ficam na **placa principal**.
- **Nada no topo da régua.** Os 4 sensores, o 595 e os conectores ficam no fundo, no bolso do degrau; no topo só as 2 furações das teclas.
- Pino 5 do conector de entrada é SER e, no de saída, QH': o cabo de elo é 1:1 e liga QH' (régua k) ao SER (régua k+1).
- **Partida:** as saídas do 595 não são Hi-Z na partida; a firmware dá 8N pulsos com DATA = 0 antes de ler. Janela de dezenas de us com colunas ligadas ao acaso: **risco aceito**
  (cada sensor leva >= 20 us para sair do desligado; a janela de pulso tem 0,1 us por estágio).

### 5.2 Forma de ligação em cadeia (elos: principal -> régua 1 -> régua 2...)

28 teclas = 8 réguas = 4 elos principal-régua 1 e 4 elos régua 1-régua 2 = **8 elos**, 20 conectores (16 nas réguas, 4 na principal).

| | **A. JST SH 6 vias + cabo pronto** (recomendada) | B. FFC/FPC 1,0 mm | C. Solda direta (barra de pinos ou fios) |
|---|---|---|---|
| Peça no pedido da JLCPCB | SH-6 lateral, clone C56123098 (US$ 0,07), **Extended** | FPC 1,0 mm C48735, **estoque 0**; outros tipos não pesquisados | nenhuma |
| Custo de 8 elos | 20 x 0,07 = 1,4 + 8 cabos SH ~US$ 3-8 (estimativa) = **~5-9** | cabos FFC 6P, 7 cm = US$ 0,06 cada (C90533, estoque 998) + conectores: ~2 | ~1 de fio/pinos |
| Tipo Extended a mais | +1 na principal e +1 nas réguas = **+6,18** | idem | **0** |
| Montagem em casa | encaixar 8 cabos: ~5 min | encaixar e travar 20 fechos ZIF: ~15 min, frágil | soldar 48 pontos: ~25 min |
| Confiabilidade | boa: trava por atrito, cabo fino; **vibração de teclado é baixa** | média: o fecho ZIF abre se mexido | **a melhor**, mas troca de régua exige dessoldar |
| Altura sob o degrau | SH lateral ~**4,3 mm (conferir no datasheet da JST)** | ~2,5 mm (FPC1.0 C48735, "PH2.5") | ~2 mm (fio) |
| Troca de régua/sensor | fácil | média | difícil |

Recomendo **A**, com C como alternativa se a diferença de 6,18 + 8 incomodar. A ordem de montagem permite A e C no mesmo projeto: os pads de C ficam ao lado do SH.
O SH exige bolso de ~4,5 mm sob as pontas da régua; a fileira 1 tem o degrau mais baixo: se o piso+degrau for menor que isso, o conector da ponta fica **fora** do apoio, pendurado na emenda. **É pergunta para o design.**

### 5.3 OUT compartilhado, cabo incluso

20 sensores + 5 réguas de trilha + 5 cabos de 60 mm + 10 conectores = **~490 pF (estimativa)** contra 1 nF do datasheet (2x de margem; ver §2.5). Cabos de 60 mm: o ideal é <= 100 mm.
Cada elo leva CLK em série pelos 5 CIs da cadeia: com 100 ohm de série e ~150 pF de carga, tau = 15 ns, bem dentro dos 200 ns por pulso.

### 5.4 Painel de réguas e montagem pelo fundo

- **Geometria (design fechou: 74 x 14,0 mm; a proposta inicial era 12):** régua de **74 x 14 mm** (4 x 18,5 de passo para o sensor ficar centrado em cada célula e o passo atravessar a emenda entre réguas), 1,2 mm, 2 camadas, cobre 1 oz.
  Largura 14 mm: o SO-16 tem 6 mm de corpo; as teclas (14 mm de corpo) apoiam nos furos e a borda pode sobrar 1 mm de cada lado (**design confere**).
- **Painel (design):** 5 réguas, **88 x 84 mm**, dentro de 100 x 100, separadas por **mouse bites** (V-cut não serve: o conector fica na borda). Dois painéis montados = 10 réguas.
- **A JLCPCB monta pelo fundo um painel assim?** A V3 já usou montagem econômica **só pelo fundo** numa placa única. **Painel feito pelo cliente com mouse bites e trilhos de 5 mm é uma opção
  documentada da JLCPCB, mas eu não consegui confirmar o aceite da montagem econômica com painel de cliente sem subir os arquivos: RISCO ACEITO, a testar na cotação.** Se recusar: pedir o painel
  pela própria JLCPCB ("Panel by JLCPCB", 1 x 6), custo da cotação.
- **Pontos de atenção:** conectores na ponta pedem trilho; fiduciais de painel (2 no trilho); o SO-16 e os X2SON de 0,5 mm de passo são do tamanho que a JLCPCB faz sem custo extra (como na V3).

### 5.5 Encaixe no degrau e distância ímã-sensor

- **Localização (design):** **2 furos de Ø 2,4 mm** em (18,5; +5,2) e (55,5; +5,2) da régua (37 mm entre eles), entalhes de 2,0 x 4,3 mm na borda de trás. Tolerância NPTH da JLCPCB (+-0,1 mm, **a confirmar**): erro de posição ~0,15 mm, do mesmo tamanho do da V3 pelos furos H1-H10. (Substitui a proposta anterior de furo redondo + oblongo a 66 mm.)
- **Bolso no degrau:** 4 bolsos de sensor (**1,8 x 2,2 x 0,8 mm**, o X2SON tem 0,4 mm de altura), 1 de 595 (**7 x 11 x 2,2 mm**, SO-16 de 1,75 mm de altura), 2 de conector (**bolso livre de 8,4 mm no design; conferir a altura do SH**).
- **Distância ímã-sensor igual à da V3:** a régua é de **1,2 mm** como a placa da V3, o sensor está no fundo dela, e a tecla se apoia na face de cima da régua pelos 2 pinos: a distância entre o ímã da KS-20 e o sensor
  é **a mesma pela construção** (espessura da placa + altura do sensor). **A tolerância de espessura da JLCPCB (+-10 % = +-0,12 mm) é a mesma da V3; a calibração do firmware (repouso por tecla medido na partida) continua valendo.**
  **(conferir)** que o degrau não encosta nos sensores (fundo do bolso).
- O degrau escalonado (passos de 2, 2 e 3 mm) só muda a **altura** da régua; a distância ímã-sensor não depende dela.

## 6. O que a programação precisa ajustar

`pcb/PINOS.md` (rascunho novo; a V3 não tinha `PINOS.md` próprio, vale o da `viaggio_micromod/pcb/PINOS.md` com estas mudanças):
1. **Somem** MUX_S0-S3 (0-3), SENS_EN (4), MUX_R_COM/L_COM (14/15) e a tabela `KEY_INPUT`: a tecla vira (fileira, coluna).
2. **OUT_R1..R4 = 14, 15, 26, 27** (ADC). **CHG_STAT: 26 -> 0.** **SCAN_DATA = 2, SCAN_CLK = 3.** O resto não muda de pino.
3. Varredura: coluna a coluna, **60 us** de espera (ou 90), leitura das 4 linhas, 8N pulsos com DATA = 0 na partida, **atraso de 1 pulso** na saída travada, **4 estágios mortos** entre réguas, acesso aleatório por padrão
   de 8N bits + 1 pulso. Detalhe e tabela de tempo em `PINOS.md`.
4. Velocity: **interpolar** o instante dos limiares e **varrer só a coluna quente** quando uma tecla sair do repouso; sem isso 76 teclas não resolvem 1 ms.
5. CPU: varredura por IntervalTimer (máquina de estados), não por espera ocupada.

## 7. Pendências e riscos aceitos

| Item | Impacto se estiver errado |
|---|---|
| Unidade da ROUT do TMAG5253 (extração do PDF embaralhada) | baixo: só afeta a carga das 19 saídas desligadas em paralelo com a ativa |
| Modelo de assentamento de 1 polo (tau 15 us) | a espera de 60 us pode precisar de 90 us; custa 0,24 ms a mais na varredura de 28 |
| Painel de réguas na montagem econômica da JLCPCB | recusa = pedido de painel pela JLCPCB (custo da cotação) |
| Altura real do SH lateral e do clone XYECONN | muda o bolso e o degrau da fileira 1 |
| Taxa de engenharia da placa principal pequena | +25 de custo (já no cenário alto) |
| Pinos 38-41 com ADC no MicroMod | só importa para 2 linhas OUT por fileira |
| Saídas do 595 na partida | microssegundos com colunas ligadas; risco baixo |
| Preço e número de impressão da F2 | design ainda não entregou |

## Perguntas para o design

1. **Conectores nas pontas da régua:** o SH 6 vias lateral tem ~4,3 mm de altura **(conferir)**. A fileira 1 tem o degrau mais baixo: cabe um bolso de ~4,5 mm sob as pontas, ou o conector fica fora do apoio, na emenda entre réguas?
2. **Emenda entre réguas:** o elo de 60 mm precisa de um canal entre réguas (ou um vão de ~10 mm). A régua de 74 mm com passo contínuo atravessa a emenda; confirme que o vão de cabo cabe sem sacrificar o degrau.
3. Régua 74 x 14 mm, 2 furos Ø 2,4 e entalhes 2,0 x 4,3: **recebido, adotado** (FIT_CHECK 12.x). Confirmar só a altura real do SH no bolso de 8,4 mm.
4. Impressão MJF da F2 = US$ 51,2: **adotada na tabela**; falta o número por módulo de +16.
5. **Posição do USB-C e do M.2 na principal:** o USB-C precisa ficar a <= 7 mm da linha dos pads 3/5 do M.2 (par <= 10 mm); isso é compatível com o lado esquerdo e a parede da F2?
6. **Alto-falante:** refazer `estudos/acustica.py` com o Dayton CE28MB-8 (Fs 623 Hz, Qts 1,63, Vas 21,5 cm3, Sd 4,52 cm2); ou prefere outro 28 mm com Fs menor?
