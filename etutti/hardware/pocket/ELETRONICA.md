# eTuttino Pocket · eletrônica (relatório)

Relatório do agente `eletronica`. Cada tarefa tem uma seção; o fim do arquivo traz as perguntas
para a gestão. Medidas em mm. **(conferir)** = número de datasheet de distribuidor, estimativa,
ou peça ainda sem medida conferida.

## E2b · Placas (SPEC v3, 18 out 2026)

**SPEC atendida:** v3, tarefa E2b ("Passo 1 · Eletrônica"), sobre o `pcb_envelope.json` do D2
(commit 0ec8e14). Nada foi encomendado nem montado.

### Resultado

| Placa | Arquivo | DRC (erros / avisos / não ligados) | Fab |
|---|---|---|---|
| Principal, 4 camadas, 1,2 mm | `pcb/kicad/pocket.kicad_pcb` | **0 / 0 / 0** | `pcb/fab/pocket_gerbers.zip`, `pocket_bom.csv`, `pocket_cpl_bottom.csv`, `pocket_cpl_top.csv` |
| Plaquinha dos knobs, 1,6 mm | `pcb/kicad/pocket_controls.kicad_pcb` | **0 / 0 / 0** | `pcb/fab/pocket_controls_gerbers.zip` |
| Plaquinha do volume (vertical), 1,6 mm | `pcb/kicad/pocket_pot.kicad_pcb` | **0 / 0 / 0** | `pcb/fab/pocket_pot_gerbers.zip` |
| Plaquinha do painel (USB-C + fone), 1,6 mm | `pcb/kicad/pocket_panel.kicad_pcb` | **0 / 0 / 0** | `pcb/fab/pocket_panel_gerbers.zip` |

- **Placa × firmware: 28/28** teclas chegam ao canal que o `pcb/pocket_keys.h` diz, no grupo de EN
  certo, e os pinos de endereço, COM, LED, KEEP, AMP_SD, VBAT, HP_DET, POT e encoder batem com o
  `PINOS.md`. A tabela está no `PINOS.md` e no `pcb/pocket_keys.h` (o sketch do Pocket ainda não
  existe; a P1 o inclui).
- **Rigidez** (`pcb/pocket_mechanics.py`, o modelo do eTuttino sobre os 45 apoios do case + as 28 pernas
  da Audio Board): pior tecla **0,021 mm** a 3 N (D♯5, fileira 1), média 0,008 mm. Meta 0,05.
- Scripts: `pcb/pocket_geom.py` (geometria e rede, só stdlib), `pcb/build_pocket_pcb.py` (placa
  principal), `pcb/build_small_boards.py` (as três plaquinhas), `pcb/pocket_mechanics.py`. Usam o
  roteador e o modelo de flexão do eTuttino (`build_pcb.py`, `mechanics.py`) pelas variáveis de módulo,
  sem mudar nada neles.

### O que mudou em relação ao E2 (decisões de placa)

1. **4 camadas.** Em 2 camadas o roteador não fechou a zona da esquerda (carregador, conversor,
   amplificador e as duas fileiras de pinos do Teensy no mesmo lugar). Com um plano de GND (In1) e um
   de 3,3 V (In2), cada pino de GND/3,3 V desce por uma via ao lado e só os sinais são roteados. A
   JLCPCB faz 4 camadas em 1,2 mm; custa mais que 2 camadas (pergunta 1).
2. **Conversor TPS63001** (3,3 V fixo, VSON-10 3 × 3, [datasheet](https://www.ti.com/lit/ds/symlink/tps63001.pdf),
   LCSC [C28060](https://www.lcsc.com/product-detail/C28060.html)) no lugar do TPS63802: o encapsulamento
   VSON-HR do TPS63802 não tem desenho conferido no KiCad. Mesma função; repouso maior (50 µA, só com o
   aparelho ligado). Indutor 2,2 µH 4 × 4 (Changjiang FNR4020S ou equivalente, código LCSC a escolher).
   Autonomia recalculada no `POWER.md`: **6,7 h com fone, 4,5 h com alto-falante** (típicos).
3. **Sensores ligados por grupo** como pedido: as fileiras 1 e 3 ficam nos canais 0–7 (EN_A =
   SENS_EN · /S3), as 2 e 4 nos canais 8–15 (EN_B = SENS_EN · S3). Cada fileira tem um barramento de EN no
   verso; um 74LVC1G04 e dois 74LVC1G08 ficam perto do Teensy.
4. **Multiplexadores por lado**: U51 lê a metade direita (COM no pino 14), U52 a esquerda (pino 15),
   ambos em pé na faixa atrás da fileira 4.
5. **Pino VIN do Teensy sem ligação** (o E1 o ligava ao 3,3 V): o 3,3 V entra pelo pino 3V3, com a ponte
   VUSB–VIN cortada, o modo que a PJRC descreve.
6. **Lugar das peças no verso**: carregador e conversor entre o Teensy e a fileira 4 (x 71–97, y 4–17);
   chave/partida/KEEP em x 73–90, y 25–31; luz de carga e resistores do LED sob a pilha; amplificador e a
   entrada dele na frente do Teensy (x 30–44, y 32–44); divisores da bateria e do HP_DET sob a pilha.
7. **Cabo dos knobs**: o J_CTL (SH 10 vias) fica na zona do design; na outra ponta o cabo é cortado e
   soldado — vias 1–5 na plaquinha do volume, 6–10 na borda direita da plaquinha dos knobs (pinos no
   `PINOS.md`). O LED e os dois postes da tampa formam uma parede na plaquinha dos knobs que as linhas
   do encoder não conseguiam atravessar até um conector na borda; um BM10B com as abas também não cabia
   nos 13,5 mm.
8. **Plaquinha dos knobs com duas abas** (x 27,0–35,2): y 40,0–42,5 atrás e 56,0–57,5 na frente. O EC11E
   ocupa 17 mm em y (A/B/C 7,5 atrás do eixo, a chave 7 à frente); nenhuma rotação cabe no retângulo de
   13,5 mm (de lado, as pernas entram na plaquinha do volume). LED com as pernas ao longo de x.
9. **Plaquinha do volume**: Alps RK097 horizontal com chave (desenho do KiCad), corpo de 13,3 ao longo do
   eixo (não 15,8): o corpo vai de z 30,3 a 17,0; os pinos da chave ficam em z 19,05, acima da plaquinha
   dos knobs. A junta de 90° tem 6 pads (só um é GND; os outros são solda de reforço), embaixo da
   plaquinha dos knobs (z ~15).
10. **Plaquinha do painel**: SJ1-3525N (Same Sky, [datasheet](https://www.cuidevices.com/product/resource/pdf/sj1-352xn.pdf),
    tem desenho no KiCad) no lugar do PJ-327A; USB-C TYPE-C-31-M-12 com o leque feito à mão; VBUS só no
    par A9/B4 (o plugue liga os quatro VBUS entre si); sem diodo de ESD (não coube). Fios soldados em pads:
    micro-B (VBUS, D+, D−, GND) e o SH-8 do J_PNL (cortado nesta ponta).
11. **Conectores de cima na placa principal**: J_BAT (PH 3, x 12,6, y 32–36), J_SPK (PH 2, 15,6 / 17,6,
    y 23,5), J_PNL (SH 8, x 17,7, y 33) na zona de trás-esquerda (conferidos contra os níveis e o plugue
    micro-B), J_CTL (SH 10) na zona dele, J_HP (3 fios do jack da Audio Board) em x 41,5–46,6, y 43,3.

### BOM / LCSC (placa principal)

Montagem na JLCPCB pelo verso (`pocket_cpl_bottom.csv`) e, para os dois SH, por cima
(`pocket_cpl_top.csv`; ou soldar à mão). Sem código LCSC ainda (a JLCPCB acha pelo valor/pacote, ou
**conferir**): resistores 1,8 k, 100 Ω, 270 Ω, 68 k, 33 k; indutor 2,2 µH 4 × 4; 74LVC1G04.
**TMAG5253BA3IQDMRR: consignado / "global sourcing"** (marcado no BOM). Fora da JLCPCB: SJ1-3525N,
RK097 com chave, EC11E, LED, cabos SH/micro-B, bateria, alto-falante.

### Pedidos ao design (detalhe em `pcb/PECAS.json`)

1. **Plaquinha dos knobs:** confirmar as duas abas (x 27,0–35,2; y 40,0–42,5 e 56,0–57,5). A da frente
   precisa passar pela parede da caixa do alto-falante.
2. **Bolso do conector da bateria:** o par PH 3 vias encaixado (PHR-3 de 7,95 × 4,5 + macho em linha,
   ~13–14 de comprimento) não cabe em 12,3 × 6,75 × 7,6. Pedido: ≥ 14,5 × 9,0 × 6,0.
3. **Plaquinha do painel:** a perna de trás-esquerda da carcaça do USB-C (passante) e a cabeça do
   parafuso M2 do furo 1 (u 4,0; v 10,3) ficam sobre o plugue micro-B (folga de 0,45). Cortar a perna
   rente resolve a primeira; o parafuso de baixo não cabe ali (trocar por pino/encaixe, ou subir a
   plaquinha ~1,5).
4. **Cabo dos knobs:** caminho para 5 fios saindo da face de trás da plaquinha do volume (z ~28,6,
   acima do encoder) e 5 da borda direita da plaquinha dos knobs (y 45–53), juntando-se no SH-10 que
   desce ao J_CTL.

### O que a programação precisa ajustar

- Usar `pcb/pocket_keys.h` (`POCKET_KEY_INPUT`, pinos). Mux 0 = U51 (pino 14), mux 1 = U52 (pino 15);
  ler canais 0–7 com S3 = 0 (EN_A) e 8–15 com S3 = 1 (EN_B), 45 µs depois de trocar S3.
- Nenhum pino mudou. O VIN fica solto (não afeta a firmware).

## E2 · Fechar as peças (SPEC v3, 17 out 2026)

**SPEC atendida:** v3, tarefa E2 ("Passo 1 · Eletrônica"). A placa (E2b) vem depois do
`pcb_envelope.json` do D2.

**Contrato com o design:** `pcb/PECAS.json` traz cada peça que o case abriga: código, LCSC, datasheet,
corpo (do desenho do datasheet), orientação, altura, keep-outs, saída dos cabos, `status`
(final / conferir) e `needs_from_design` (o que o case precisa dar).

### O que foi feito

1. **Potenciômetro com chave que cabe sem subir a tampa** (SPEC §3, opção 1).
2. **USB-C** numa plaquinha do painel, junto com o fone, com o 5 V do carregador tirado antes do Teensy.
3. **Bateria com NTC (3 fios)**: modelo, fornecedores, berço e ligação ao TS.
4. **Luz de carga** pelo CHG do BQ24074 no vermelho do LED que já existe, também desligado.
5. **Pilha mais baixa** avaliada: recomendada, não crítica.
6. **`pcb/PINOS.md`** deixa de ser provisório (nenhum pino mudou de lugar).
7. **`POWER.md`** regenerado por `pcb/power_budget.py`, com a carga pela USB-C e a opção de 1200 mAh.

### 1. Potenciômetro de volume com chave

**Solução: 9 mm com chave, tipo horizontal, numa plaquinha vertical** (opção 1 da SPEC §3).

- O corpo do 9 mm com chave mede **15,8 ao longo do eixo** (chave incluída), 9,5 de largura e
  11,25 a partir da placa dele, com o eixo a 6,5 da placa ([desenho RK0972S](https://kyohritsu.com/eclib/OTHER/DATASHEET/rk0972s.pdf)).
- Essa medida ao longo do eixo não muda com a montagem. O que muda é o que fica embaixo:
  - **vertical, na plaquinha dos knobs** (como o RK09K do eTuttino): 16,6 acima da placa. Não cabe
    nos 13 reservados, e baixar a plaquinha 3,6 a põe em cima da Audio Board;
  - **horizontal, numa plaquinha vertical** atrás do eixo: não há placa embaixo do corpo. O corpo
    desce de logo abaixo da tampa (z 30,3) até z 14,5, dentro da faixa de z que a plaquinha dos
    knobs já usa (14,08–30,18). Em planta ocupa x 10,4–19,9 e y 42,5–53,8, quase exatamente o
    retângulo reservado no `pocket.json` (10,1–20,1 × 42,8–55,3). **A tampa não sobe.**
- A plaquinha do volume (≈ 13,6 × 16 × 1,6) fica em pé em y 40,9–42,5 e se liga à plaquinha dos
  knobs em ângulo reto: uma aba dela entra numa fenda da plaquinha dos knobs e é soldada em 5 pads
  (ou 5 fios curtos). A plaquinha dos knobs perde a ponta esquerda (recorte em volta do corpo).
- O eixo passa pela tampa e a **porca M7 prende o potenciômetro na tampa**: o knob fica firme e a
  plaquinha não carrega esforço. Furo Ø7,3 e um furo cego Ø1,2 para o pino antigiro (ou corta-se o pino).
- Knob Ø9 em eixo Ø6 serrilhado, igual ao RK09K: serve. Com L = 15 a ponta do eixo fica 12,3 acima
  da tampa.
- A chave só leva o sinal de liga/desliga (alguns mA, ver a arquitetura do E1). Não passa a corrente do aparelho.
- **Peça:** RK0972S-A10K (L 15, KC), ou Alps RK097 com chave. Na LCSC achei o Alps **RK0971221Z05**
  ([C336003](https://www.lcsc.com/product-detail/C336003.html), 60 em estoque), com curva e eixo a
  conferir **(conferir)**. A curva log (A) é a preferida; com linear (B) a firmware corrige a curva.
- **Por que não o de 16 mm com chave:** corpo Ø16–17 e 13–17 ao longo do eixo com a caixa da chave.
  Não é mais baixo que o de 9 mm, é mais largo, e com o encoder a 16 mm sobra ~1 mm entre os corpos.

### 2. USB-C e a ligação ao Teensy

**Solução: uma plaquinha do painel com o USB-C e o fone, deitada (paralela ao fundo), com a borda da
frente num ressalto plano por dentro da parede curva de trás-esquerda.**

```
 USB-C (plaquinha do painel) ── CC1, CC2: 5,1 kΩ ao GND · ESD USBLC6-2SC6
   ├── VBUS, D+, D−, GND ── cabo curto com plugue micro-B de 90° ── micro-B do Teensy
   │                        (o VUSB do Teensy só vai ao sensor de VBUS do i.MX: ponte VUSB–VIN cortada)
   └── VBUS, GND (2+2 vias) ── cabo JST SH 8 vias ── placa principal: BQ24074 IN
       HP_L, HP_R, HP_VGND, HP_TIPSW (fone) ─┘
```

- A parede é um arco (R ~89): numa corda de 30 a flecha é ~1,3. Um ressalto plano por dentro deixa a
  borda reta; os dois conectores ficam lado a lado, com ~14 entre centros.
- **Receptáculo:** Korean Hroparts **TYPE-C-31-M-12** (16 vias, SMD com pernas da carcaça
  passantes), [C165948](https://www.lcsc.com/product-detail/C165948.html). Corpo 8,94 × 7,35 × 3,26
  **(conferir no desenho)**. Furo oblongo 9,4 × 3,7 na parede; a frente do receptáculo fica 0–0,3
  atrás da face de fora, e por fora um rebaixo de 13 × 7 × 0,5 para a capa do plugue assentar na curva.
- **CC1 e CC2 com 5,1 kΩ** ao GND (0402, [C25905](https://www.lcsc.com/product-detail/C25905.html)):
  carregadores e cabos C-C entregam 5 V. **ESD:** USBLC6-2SC6 ([C7519](https://www.lcsc.com/product-detail/C7519.html)).
- **O 5 V do carregador sai do USB-C, antes do Teensy.** O fio no pad VUSB do Teensy (E1) não existe
  mais. Continua o corte da ponte VUSB–VIN: o Teensy é alimentado pelo 3,3 V do conversor.
- **Até o Teensy:** um cabo curto (~40 mm) com plugue micro-B de 90°, comprado e cortado, com os 4 fios
  soldados em pads da plaquinha (D+/D− trançados). A USB do Teensy 4.0 é de 480 Mbit/s; com ~40 mm
  trançados deve funcionar, e se não negociar alta velocidade ela cai para 12 Mbit/s, que basta para
  MIDI **(conferir no protótipo)**. A direção do ângulo do plugue depende da posição final da pilha.
- **Força de encaixe** (~20 N) vai para o ressalto pela plaquinha: 2 parafusos M2 autoatarraxantes
  ou um trilho impresso preso pelo fundo (o design escolhe).
- **Alternativa recusada:** USB-C na língua da placa principal. A placa fica em z 6,5–7,7; o
  conector sairia baixo na parede e a língua não chega à parede perto do USB.

### 3. Fone de painel

- **PJ-327A** (5 terminais: manga, ponta, comutação da ponta, anel, comutação do anel), passante,
  horizontal, na plaquinha do painel. Corpo 14,3 × 9 × 6 **(conferir)**. Na LCSC: SHOU HAN
  PJ-327A-CJ [C17701691](https://www.lcsc.com/product-detail/C17701691.html) **(conferir no desenho
  que a comutação da ponta é fechada sem plugue)**.
- Furo Ø6 com rebaixo externo Ø10 × 0,5 para plugues gordos; parede ≤ 1,5 no furo.
- Manga → **HP_VGND** (terra virtual da Audio Board), **nunca no GND**. Ponta/anel → HP_L/HP_R.
  Comutação da ponta → rede do HP_DET na placa principal (pino 17).
- Os sinais do fone saem dos terminais do jack da própria Audio Board (3 fios curtos até a placa
  principal, que alimenta o amplificador) e seguem pelo cabo SH até a plaquinha do painel.

### 4. Bateria com NTC

- **Pedido:** LiPo 1S 603450 com PCM e **NTC de 10 kΩ (B 3435), 3 fios**, plugue JST PH 2,0 de 3 vias.
- **Onde comprar** (todos a conferir):
  - EEMB LP603450 sob encomenda com o fio do NTC ([página](https://www.eemb.com/product-252)), célula
    6,3 × 34,5 × 52 máx., ~22 g;
  - pacote 603450 de 3 fios com NTC à venda pronto, mas de **1200 mAh** (mesmo tamanho; vendedor
    zengtrader, [eBay 112702247608](https://www.ebay.com/itm/112702247608));
  - reserva que também cabe no berço: Core Electronics **CE06795** (1000 mAh, NTC, PCM, 7 × 30 × 50,
    JST-PH 3, [página](https://core-electronics.com.au/catalog/product/view/sku/CE06795)).
- **Berço:** 7 × 36 × 58 (célula + PCM + dobra dos fios), +8 % de inchaço na espessura (as células
  incham na espessura): **7,6 × 36,5 × 58,5**, mais um canal de ~6 × 4 para os 3 fios. Fora de baixo
  da placa principal, acesso pelo fundo, presa pelo fundo com uma espuma (sem cola na célula).
- **NTC no TS do BQ24074:** o carregador injeta 75 µA no TS ([datasheet](https://www.ti.com/lit/ds/symlink/bq24074.pdf)).
  Para a carga a 2,1 V (28 kΩ ≈ 0 °C) e a 0,3 V (4 kΩ ≈ 50 °C), a janela padrão do NTC de 10 kΩ B 3435.
  Ligação: NTC entre TS e GND (o fio do NTC e o negativo da bateria). Sem resistor extra.
- **Plugue:** JST PH B3B-PH-K-S na placa ([C131339](https://www.lcsc.com/product-detail/C131339.html)).
  A ordem dos fios varia entre vendedores: **conferir antes de ligar**. A montagem alternativa
  (sem NTC) troca o NTC por 10 kΩ fixo do TS ao GND.

### 5. Luz de carga pelo CHG

O CHG do BQ24074 é um dreno aberto que vai ao GND enquanto carrega (e pisca a 2 Hz se o tempo de
segurança estoura). O LED do Pocket é de catodo comum (os pinos do Teensy fornecem corrente), então
o CHG não pode acendê-lo direto: precisa de uma chave do lado de cima.

```
 VBUS (5 V, só com USB) ── 100 kΩ ──┬── porta do AO3401A (P-MOSFET)
                                    └── CHG do BQ24074 (baixo = carregando)
 VBUS ── fonte do AO3401A ── dreno ── 1 kΩ ──► BAT54C (diodo 1) ──┐
 pino 13 do Teensy ── 270 Ω ─────────────────► BAT54C (diodo 2) ──┴── LED_R (anodo vermelho, plaquinha dos knobs)
```

- Carregando: o CHG puxa a porta, o MOSFET conduz, ~2,8 mA da USB acendem o vermelho, **com o Pocket
  ligado ou desligado**. Sem USB não há nada no circuito.
- Os dois diodos fazem um "OU": o Teensy desligado não recebe corrente pelo pino 13, e o pino 13 não
  alimenta o circuito da carga.
- Peças: AO3401A ([C15127](https://www.lcsc.com/product-detail/C15127.html)), BAT54C
  ([C134405](https://www.lcsc.com/product-detail/C134405.html)), resistores 0402.
- **Efeito na firmware:** enquanto carrega, o vermelho fica aceso e a firmware não o apaga. As
  piscadas de confirmação passam para o verde (ver `PINOS.md`). Pergunta 4 abaixo.
- O CHG não vai a um pino do Teensy (não há pino livre). A página mostra "carregando" pela dedução
  VBUS + VBAT descrita no `PINOS.md`.

### 6. Pilha mais baixa

| Pilha | Audio Board até o topo do USB | topo do USB do Teensy | observação |
|---|---:|---:|---|
| como no D1 (espaçador de 2,5 + 3 de altura da Audio Board) | 13,0 | z 23,7 | medida na pilha do J |
| **baixa:** Teensy soldado direto na Audio Board com headers extralongos (só o plástico de espaçador) | **~8,7 (conferir)** | **~z 19,4** | como no manual do eTuttino |

- Ganho de ~4,3 em altura. O topo do USB passa folgado sob a rampa; o design pode usar isso para
  encolher a faixa da interface alguns milímetros.
- Cuidado de montagem: **cortar a ponte VUSB–VIN antes** de soldar o Teensy (depois a face de baixo
  fica contra a Audio Board). Com a v3 nada mais precisa ser soldado embaixo do Teensy (o fio do VUSB saiu).
- Recomendo a pilha baixa; não é crítico.

### Peças escolhidas (E2)

| Função | Peça | LCSC | Medidas | Datasheet | Status |
|---|---|---|---|---|---|
| Volume com chave | RK0972S-A10K L15 / Alps RK0971221Z05 | [C336003](https://www.lcsc.com/product-detail/C336003.html) | 15,8 × 9,5 × 11,25, M7 | [RK0972S](https://kyohritsu.com/eclib/OTHER/DATASHEET/rk0972s.pdf) | conferir (curva, eixo) |
| Encoder | Alps EC11E com chave, 15 pulsos / 15 detentes, eixo 20 | não achado | 12,4 × 13,2 × 6,5 | [EC11E](https://tech.alpsalpine.com/e/products/category/encorders/sub/01/series/ec11e/) | conferir (sufixo) |
| LED | 3 mm vermelho/verde, catodo comum (Kingbright WP937EGW ou equiv.) | conferir | Ø3 × 5,3 | [WP937EGW](https://www.kingbrightusa.com/images/catalog/SPEC/WP937EGW.pdf) | conferir |
| USB-C | Hroparts TYPE-C-31-M-12 | [C165948](https://www.lcsc.com/product-detail/C165948.html) | 8,94 × 7,35 × 3,26 | LCSC | conferir |
| ESD da USB | USBLC6-2SC6 | [C7519](https://www.lcsc.com/product-detail/C7519.html) | SOT-23-6 | [ST](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) | final |
| CC 5,1 kΩ (2×) | 0402 1 % | [C25905](https://www.lcsc.com/product-detail/C25905.html) | 0402 | — | final |
| Fone | PJ-327A, 5 terminais | [C17701691](https://www.lcsc.com/product-detail/C17701691.html) | 14,3 × 9 × 6 | [LCSC](https://datasheet.lcsc.com/lcsc/2309121405_SHOU-HAN-PJ-327A-CJ_C17701691.pdf) | conferir |
| Bateria | 603450 1S, PCM, NTC 10 kΩ B 3435, 3 fios | — (pronta) | 7 × 36 × 58 com PCM | [EEMB](https://www.eemb.com/product-252) | conferir |
| Alto-falante | Same Sky CLS0361-L152 | — (Mouser/DigiKey) | Ø36 × 6,0 (aro 2,7; ímã Ø15,9), 8,6 g, fios 152 | [CLS0361-L152](https://www.sameskydevices.com/product/resource/cls0361-l152.pdf) | final |
| Luz de carga | AO3401A + BAT54C | [C15127](https://www.lcsc.com/product-detail/C15127.html), [C134405](https://www.lcsc.com/product-detail/C134405.html) | SOT-23 | [AO3401A](https://www.aosmd.com/res/datasheets/AO3401A.pdf), [BAT54C](https://www.diodes.com/assets/Datasheets/ds11005.pdf) | final |
| Conector da bateria | JST PH B3B-PH-K-S | [C131339](https://www.lcsc.com/product-detail/C131339.html) | 7,9 × 4,5 × 6 | [JST PH](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf) | final |
| Conector do alto-falante | JST PH B2B-PH-K-S | C131337 (conferir) | 5,9 × 4,5 × 6 | [JST PH](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf) | conferir |
| Cabo do painel | JST SH BM08B-SRSS-TB (2×) + cabo SH 8 vias | [C160394](https://www.lcsc.com/product-detail/C160394.html) | 10 × 4,25 × 4,25 | [JST SH](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) | final |
| Cabo dos knobs | JST SH BM10B-SRSS-TB (2×) + cabo SH 10 vias | [C160396](https://www.lcsc.com/product-detail/C160396.html) | 12 × 4,25 × 4,25 | [JST SH](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) | final |
| Cabo micro-B de 90° | comprado, cortado e soldado | — | plugue 11 × 11 × 7,5 | — | conferir |

Seguem do E1, sem mudança: BQ24074RGTR (C54313), TPS63802DLAR (C2845237), PAM8302AASCR (C113367),
TMAG5253BA3 (consignado), 2 × CD74HC4067M96. As portas do EN por grupo saem no E2b.

**Plaquinha dos knobs, 10 vias** (antes 8 no eTuttino): VCC, GND, POT, ENC_A, ENC_B, ENC_SW, LED_R,
LED_G e os 2 fios da chave (PWR_A = saída do carregador por 100 Ω, PWR_B = SW_ON). O conector
fica no **lado de cima** da plaquinha: um conector para baixo, como o do eTuttino, esbarraria na Audio
Board, que passa por baixo dela.

### Consumo e autonomia

Sem mudança de arquitetura desde o E1: os números são os mesmos (detalhes no `POWER.md`).

| Cenário recomendado (TMAG5253BA3 por grupo, 396 MHz) | fone | alto-falante |
|---|---:|---:|
| 1000 mAh, típico | **6,9 h** | **4,5 h** |
| 1000 mAh, pior caso | 4,2 h | 2,4 h |
| 1200 mAh (se a bateria de 3 fios vier assim), típico | 8,2 h | 5,4 h |

- Carga: ~2,5 h desligado (1000 mAh, 500 mA), ~3 h tocando com fone. Pela USB-C com qualquer cabo.
- A luz de carga usa ~2,8 mA da USB, não da bateria.
- Desligado (chave ou KEEP): ~10 µA. Todas as correntes ainda são de datasheet e modelo: medir no protótipo.

### O que o design precisa dar (detalhe em `PECAS.json`, `needs_from_design`)

1. Ressalto plano ≥ 32 × 10 por dentro da parede de trás-esquerda; parede ≤ 1,0 no furo do USB-C
   (oblongo 9,4 × 3,7, rebaixo externo 13 × 7 × 0,5) e ≤ 1,5 no do fone (Ø6, rebaixo Ø10 × 0,5);
   2 pilares M2 ou um trilho para a plaquinha do painel.
2. Na tampa, no knob de volume: furo Ø7,3 para a bucha M7 (com porca) e furo cego Ø1,2 para o pino antigiro.
3. Espaço para a plaquinha vertical do volume em y 40,9–42,5, de z 13,8 para cima, e nada em
   z 14,5–17,2 sob o corpo do potenciômetro.
4. Berço da bateria 7,6 × 36,5 × 58,5 com canal para 3 fios.
5. Caixa do alto-falante para 6,0 ± 0,3 de profundidade (o D1 reservou 5,5) e ≥ 8 cm³ (10 de preferência), vedada.
6. Caminho para o cabo SH de 10 vias da borda direita da plaquinha dos knobs até a placa principal,
   e para o cabo SH de 8 vias da plaquinha do painel até a placa principal.
7. Escolher a pilha (normal 13,0 ou baixa ~8,7).

### O que a programação precisa ajustar (`pcb/PINOS.md`)

Os pinos são os da versão provisória, agora finais. Novo na v3:

1. Enquanto carrega, o vermelho do LED fica aceso pelo carregador e a firmware não o apaga: as
   piscadas de confirmação do encoder devem usar o verde.
2. O vermelho passa por um diodo; o brilho fica igual ao do eTuttino (resistor de 270 Ω).
3. "Carregando" para a página: VBUS (registrador da USB do i.MX RT) + VBAT < 4,15 V.
4. Encoder de 15 pulsos / 15 detentes: `ENC_STEPS_PER_DETENT = 4`, como no eTuttino.

## E1 · Energia e som (SPEC v2, 17 out 2026) · histórico

Decisões da v3 sobre o E1: TMAG5253BA3 por grupo, KEEP com desligamento em dois estágios,
bateria com NTC, USB-C no case, luz de carga pelo STAT, alto-falante CLS0361-L152, 396 MHz com
condições. O texto abaixo é o do E1; o que mudou está no E2 acima.

**SPEC atendida:** v2, tarefa E1 ("Passo 1 · Eletrônica"). Sem placa nem Gerbers (esperam D2).

### Resumo

- **Autonomia com 1000 mAh, tocando sem parar** (recomendado: sensor TMAG5253, sensores ligados
  por grupo, Teensy a 396 MHz):

  | | típico | pior caso |
  |---|---:|---:|
  | com fone | **6,9 h** (hoje 3,0 h) | **4,2 h** (hoje 1,9 h) |
  | com alto-falante (0,2 W médios; pior 0,5 W) | **4,5 h** (hoje 2,5 h) | **2,4 h** (hoje 1,4 h) |

  Com o Teensy a 240 MHz (se a programação confirmar a CPU): 7,9 h com fone, 5,0 h com
  alto-falante (típicos).
- **A maior economia é o sensor:** o TMAG5253 (TI, 2023) gasta 2,4–2,6 mA contra 6 mA do DRV5056,
  tem pino EN (desliga em 8 nA, saída em alta impedância) e liga em ≤ 45 µs (BA3) contra até
  300 µs. Os 28 sensores passam de 168 mA para 36 mA médios.
- **Medido no Teensy do J:** a CPU do áudio e o tempo de leitura das teclas em 8 frequências de
  clock (tabela no `POWER.md`). O motor de palhetas de hoje usa só 8,5 % da CPU a 600 MHz e 34 %
  a 150 MHz. A corrente não foi medida (não há medidor no PC do J): a do Teensy por clock é um modelo.
- **Orçamento movido** para `pcb/power_budget.py` (stdlib), que escreve o `POWER.md`.
- **`pcb/PINOS.md` provisório:** os 24 pinos da borda do Teensy ficam todos ocupados; muda
  o LED vermelho (4 → 13), o encoder A (17 → 11) e o COM 3 sai.

### Arquitetura de energia

```
 USB micro-B do Teensy ── VUSB (pad de baixo do Teensy; corte VUSB–VIN feito) ── fio ──┐
                                                                                         │
                                         ┌──────────── BQ24074 (carregador, power-path) ◄┘
              LiPo 1S 1000 mAh + PCM ◄── BAT          OUT = 4,4 V com USB / = bateria sem USB
              (JST PH 2,0)                              │
                     divisor 1M/1M ─ pino 16            ├── PAM8302A VDD (SD = pino 12, 100k p/ GND) ── alto-falante
                                                        │
                                                        └── chave do volume (SPST) ── SW_ON ──┐
                                                                                               │
                                     KEEP (pino 10) ── circuito de partida/retenção ── EN ─────┘
                                                                                               │
                                                     TPS63802 (buck-boost) ◄── OUT do BQ24074 ─┘
                                                        │ 3,3 V
                                                        ├── pino 3.3V do Teensy (e VIN ligado ao 3,3 V)
                                                        │      └── Audio Board (pelos headers)
                                                        └── 28 sensores, 2 multiplexadores, LED
```

- **Teensy alimentado pelo 3,3 V.** Corta-se a ponte VUSB–VIN no verso do Teensy (o corte que a
  PJRC documenta) e o 3,3 V do conversor entra pelo pino 3.3V; o pino VIN vai ao mesmo 3,3 V
  (o regulador do Teensy fica com entrada = saída e não puxa corrente reversa, conferir). O 5 V
  da USB chega ao carregador por **um fio curto** do pad VUSB (verso do Teensy) até a placa
  principal, soldado antes de montar o Teensy na Audio Board. É a única modificação no Teensy.
- **Carregador BQ24074:** modo USB500 (EN2 = 0, EN1 = 1, fixo por resistor): no máximo 500 mA
  da porta USB, seguro em qualquer computador. Corrente de carga 500 mA (R_ISET = 1,78 kΩ;
  K_ISET = 890 AΩ). Tocando enquanto carrega, o power-path dá prioridade ao aparelho e carrega
  com o resto. Carga completa ~2,5 h desligado (conferir). TS com 10 kΩ fixo se a bateria não
  tiver NTC.
- **Conversor TPS63802** em vez do TPS63020 da v1: mesmo papel, menor (2 × 3 mm contra 3 × 4),
  11 µA de repouso, 2 A, aceita 1,3–5,5 V na entrada (cobre 4,4 V da USB e a bateria até o fim).
  O TPS63020 continua como segunda opção (mesmo esquema, outro layout).
- **Liga/desliga (SPEC §6):** a chave do potenciômetro liga a saída do carregador ao nó SW_ON.
  - Ao fechar a chave, um pulso RC (1 µF / 1 MΩ, ~0,5 s, conferir) liga o EN do conversor; o
    Teensy acorda e sobe o **KEEP** (pino 10) em poucos ms, que mantém o EN ligado por um
    transistor alimentado pelo próprio SW_ON. Um diodo impede que o Teensy desligado anule o pulso.
  - Chave aberta: SW_ON = 0, o EN cai, tudo desliga, mesmo com o KEEP alto.
  - O amplificador desliga junto: o SD dele tem 100 kΩ para o GND e o Teensy sem energia não o liga.
  - O carregador continua carregando com a chave aberta (ele fica antes da chave).
  - **Desligamento automático de verdade:** a firmware baixa o KEEP e o aparelho desliga
    (~10 µA). Para religar, o usuário gira o volume até o clique e volta. Sem o KEEP, o
    "desligamento automático" só pode baixar o consumo para ~23 mA, e um Pocket esquecido ligado
    esvazia a bateria em ~1,5 dia. Pergunta 2 para a gestão.
- **Medida da bateria:** divisor 1 MΩ / 1 MΩ com 100 nF, direto na bateria (2 µA sempre), pino 16.
- **Desligado:** ~10 µA (carregador sem entrada, conversor desligado, divisor, amplificador em
  shutdown): a bateria dura anos; fica a autodescarga dela.

### Peças escolhidas

| Função | Peça | LCSC | Medidas | Datasheet | Notas |
|---|---|---|---|---|---|
| Bateria | LiPo 1S 1000 mAh tipo 603450, com PCM, 2 fios + JST PH 2,0 | — (comprar pronta) | célula 6,3 × 34,5 × 52 máx. (EEMB LP603450); **com PCM e dobra dos fios, reservar 7 × 36 × 58** + ~60 mm de fio (conferir) | [EEMB LP603450](https://www.eemb.com/product-252) | "603450" é só tamanho: cada fabricante tem 1000–1200 mAh e PCM de 2–4 mm. A polaridade do JST varia entre vendedores: conferir antes de ligar. Prever ~8 % de inchaço no berço. |
| Carregador com power-path | TI **BQ24074RGTR**, QFN-16 3 × 3 | [C54313](https://www.lcsc.com/product-detail/C54313.html) | 3 × 3 × 1 | [bq24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf) | OUT 4,4 V com USB; OVP 10,5 V. |
| Buck-boost 3,3 V | TI **TPS63802DLAR**, VSON-10 2 × 3 | [C2845237](https://lcsc.com/product-detail/C2845237.html) | 2 × 3 × 1 + indutor 0,47 µH (~4 × 4) | [tps63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf) | 2ª opção TPS63020DSJR [C15483](https://www.lcsc.com/product-detail/C15483.html), [datasheet](https://www.ti.com/lit/ds/symlink/tps63020.pdf). |
| Amplificador classe D mono | Diodes **PAM8302AASCR**, MSOP-8 | [C113367](https://lcsc.com/product-detail/C113367.html) | 3 × 3 × 1 | [PAM8302A](https://www.diodes.com/assets/Datasheets/PAM8302A.pdf) | 2,0–5,5 V, na bateria; 0,65 W em 8 Ω a 3,6 V (1 % THD); repouso 4 mA, shutdown < 1 µA; ganho máx. 23,5 dB, reduzido com R de entrada (~33 kΩ → ~11 dB, conferir de ouvido). |
| Sensor Hall (28×) | TI **TMAG5253BA3** (padrão) ou **TMAG5253UA5**, X2SON-4 | não achado na LCSC/JLCPCB (conferir); TI/DigiKey/Mouser, consignado à JLCPCB | 1,4 × 1,1 × 0,4 | [tmag5253](https://www.ti.com/lit/ds/symlink/tmag5253.pdf) | Mesmo lado (verso) e mesma orientação do DRV5056: lê o sul na face marcada, que é o que o ímã norte-para-baixo do Gateron dá através da placa. Ver "Reduções". |
| Sensor, alternativa SOT-23 | TI DRV5053OAQDBZR(Q1) | [C165150](https://www.lcsc.com/product-image/C165150.html) (sem estoque) / Q1 C2654961 | SOT-23 | [drv5053](https://www.ti.com/lit/ds/symlink/drv5053.pdf) | 2,7 mA, liga em 35 µs, sem EN, saída 0,2–1,8 V invertida (o sul baixa a tensão), satura em 73 mT. Só se o TMAG5253 não puder ser comprado. |
| Multiplexador (2×) | CD74HC4067M96, SOIC-24 | (como no eTuttino) | — | [CD74HC4067](https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf) | Igual ao eTuttino. |
| Porta para o EN dos grupos | SN74LVC2G08 + SN74LVC1G04 (ou equivalente) | escolher na placa (D2) | SOT-23/SC-70 | — | EN_A = SENS_EN · /S3, EN_B = SENS_EN · S3. |
| Potenciômetro de volume com chave | 9 mm, 10 kΩ log (A), chave SPST que fecha no início do curso, tipo **RK0972S / RV097NS** | não achado na LCSC (conferir) | ver abaixo | [desenho RK0972S](https://kyohritsu.com/eclib/OTHER/DATASHEET/rk0972s.pdf) | A chave abre nos primeiros ~30° (sentido anti-horário, até o clique). |
| Jack de fone | jack estéreo 3,5 de painel **com contato de comutação na ponta** (5 terminais), ≤ 10 de profundidade | — (conferir modelo) | como o do eTuttino + 1 terminal | — | 4 fios: L, R, terra virtual (manga) e o contato da ponta. |

#### Alto-falante (o maior que couber; 8 Ω)

| Candidato | Contorno | Profundidade | Potência | Sensibilidade | Ressonância | Volume traseiro recomendado | Datasheet |
|---|---|---:|---|---|---:|---:|---|
| **Same Sky CLS0361-L152** (recomendado) | Ø36 redondo | 6,0 | 2 W (3 W máx.) | 88 dB a 1 W / 0,5 m | 450 Hz | **8–12 cm³** fechado (conferir) | [CLS0361-L152](https://www.sameskydevices.com/product/resource/cls0361-l152.pdf) |
| PUI Audio AS03608MR-LW100-R | Ø36 redondo | 4,6 | 1 W (1,5 W máx.) | 91 dB (condição não informada, conferir) | 500 Hz | 6–10 cm³ (conferir) | [AS03608MR-LW100-R](https://api.puiaudio.com/filename/AS03608MR-LW100-R.pdf) |
| Same Sky CMS-30204-18L250 | 30 × 20 retangular | 4,0 | 1 W (1,2 W máx.) | 94 dB a 1 W / 0,1 m (≈ 80 dB a 1 m) | 700 Hz | 3–5 cm³ (conferir) | [CMS-30204-18L250](https://www.sameskydevices.com/product/audio/speakers/miniature-(10-mm~40-mm)/cms-30204-18l250) |
| Same Sky CLS0281-L152 (se só couber 28) | Ø28 redondo | 5,8 | 1 W | 82 dB | 440–660 Hz | 3–5 cm³ (conferir) | [TME CLS0281-L152](https://www.tme.com/ca/en/details/cls0281-l152/speakers/same-sky-r/) |

- Volume traseiro **fechado e vedado** (junta de espuma ou cola em volta do aro), atrás do cone,
  sem comunicar com o resto do case. Um volume menor que o recomendado sobe a ressonância e corta
  mais grave; maior não faz mal. Com Ø36 e 10 cm³, o grave útil começa em ~550–650 Hz
  (estimativa): o Pocket vai de G3 (196 Hz) a E5 (659 Hz), então o alto-falante reproduz os
  harmônicos e o ouvido completa a fundamental. Por isso a equalização da programação corta
  abaixo de ~400 Hz e limita o pico (SPEC §5).
- Frente: a grade precisa de área aberta ≥ ~30 % da área do cone, a ≤ 1–2 mm da membrana, com
  uma junta entre o aro e a parede.
- Não há códigos LCSC úteis para alto-falantes desses fabricantes: compra direta
  (Mouser/DigiKey/TME); vai ligado por fio, fora da montagem da JLCPCB.
- Alternativa sem volume traseiro: alto-falante "com caixa" 20 × 30 × 6,8 (tipo 2030 cavity,
  2 W): encaixa mais fácil, soa como um celular. Só se não couber o Ø36 com volume.

#### Potenciômetro com chave: medidas para o design

Do desenho RK0972S (9 mm, com chave; o RV097NS é o mesmo formato, conferir no modelo comprado):

- corpo 9,5 de largura × 15,8 de comprimento (ao longo do eixo, **incluindo a chave**) × ~10 de altura;
- rosca M7 × 0,75, eixo Ø6 serrilhado, comprimento L = 15 ou 20 a partir do corpo;
- 8 terminais Ø1 (3 do potenciômetro, 2 da chave, apoios), passo 5 / 2,5.
- **Montado com o eixo para cima** (versão vertical, terminais na face de trás): **15,8 + 0,8 de
  corpo acima da placa, mais o eixo: 31–36 do topo da placa à ponta do eixo** (L = 15 ou 20,
  conferir). É ~10 mais alto que o RK09K do eTuttino.
- O desenho mostrado é da versão horizontal (eixo paralelo à placa, eixo a 6,5 da placa). Se a
  vertical não existir no fornecedor, a horizontal serve montada numa plaquinha perpendicular à
  tampa. Quem decide é o design (altura disponível sob a tampa).

#### Detecção do fone

O jack tem um contato que encosta na ponta (canal esquerdo) quando não há plugue e se afasta
quando o plugue entra. Esse contato vai ao pino 17 (ADC) por 100 kΩ, com 1 MΩ e 100 nF para o GND.

- Sem fone: o pino vê a tensão de repouso da saída de fone do SGTL5000 (~1,6 V, que é também a
  do terra virtual), filtrada do áudio: ~1,4 V.
- Com fone: o contato abre e o pino vai a 0 V.
- O contato nunca toca o GND nem o terra virtual: a manga do jack continua só no **HP_VGND** da
  Audio Board. A carga extra na saída esquerda é de 1,1 MΩ (desprezível).
- Codec desligado ou na partida: 0 V = "fone", o amplificador fica desligado (lado seguro).
- O amplificador pega o som das mesmas saídas de fone (L + R somados por resistores, contra o
  HP_VGND, entradas diferenciais com 1 µF): o potenciômetro de volume vale para fone e
  alto-falante, e a programação aplica a equalização do alto-falante quando HP_DET diz "sem fone".

### Reduções de consumo (SPEC §6)

1. **Sensor de menor consumo: TMAG5253.** Analógico ratiométrico, 15 kHz de banda (DRV5056: 20 kHz;
   a batida mais rápida dura ~1 ms, então sobra), EN com saída em alta impedância, sente o sul na
   face marcada como o DRV5056 (vai no verso, mesma orientação).
   - **BA3** (bipolar, ±80 mT, 15 mV/mT, repouso 1,65 V, 2,6 mA típ./5 mA máx., liga em 20/45 µs):
     a mesma faixa do DRV5056A3, padrão seguro.
   - **UA5** (unipolar, 0–52 mT, 48 mV/mT, repouso 0,2 V, 2,4/4 mA, liga em 55/130 µs): o triplo
     de resolução, se o campo no fim do curso ficar abaixo de ~50 mT.
   - Mesma pegada X2SON: a escolha entre os dois fica para a medição do campo no protótipo.
   - Ponto fraco: não achei na LCSC/JLCPCB; compra na TI/DigiKey e consigna, ou "global sourcing"
     da JLCPCB (conferir prazo e custo). X2SON 1,4 × 1,1 é só montagem de fábrica (rota A do manual).
2. **Sensores ligados por grupo.** O bit S3 do endereço (que já existe) escolhe o grupo de canais
   0–7 ou 8–15 dos dois multiplexadores; uma porta lógica liga o EN só do grupo que está sendo lido.
   Metade dos sensores desligada o tempo todo: 73 → 36 mA. Com o BA3 a leitura cai de 4,6 kHz
   para ~3 kHz (medido + calculado); o erro de velocidade fica em ±2 de 127 na batida mais rápida.
   **Com o DRV5056 não vale:** o tON de até 300 µs derruba a leitura para ~1,2 kHz (tabela no
   `POWER.md`). O SENS_EN geral (pino 4) também desliga todos no repouso e no desligamento leve.
3. **Teensy em clock menor (medido a CPU, estimada a corrente).** O motor atual usa 8,5 % a
   600 MHz, 12,9 % a 396 MHz, 21 % a 240 MHz. Proposta: começar em 396 MHz (~31 mA a menos,
   estimativa) e a programação mede com o motor do Pocket (Musette com 3 palhetas de 8', presets)
   se 240 MHz fica abaixo de ~40 %. A leitura das teclas a 240 MHz leva 266 µs (medido), sem efeito
   na velocidade. Coordenar com a programação (P1).
4. **Amplificador desligado em silêncio:** o SD (pino 12) desliga o PAM8302A com fone plugado,
   ~2 s depois da última voz, e no desligamento automático: −4 mA (até −8) de repouso. Pouco
   tocando; importa parado.

### Consumo e autonomia

Detalhes e todos os cenários no `POWER.md`. Bateria 1000 mAh, 85 % úteis (3,15 Wh).

| Cenário | fone típ. | fone pior | alto-falante típ. | alto-falante pior |
|---|---:|---:|---:|---:|
| antes (v1): DRV5056, 600 MHz | 3,0 h | 1,9 h | 2,5 h | 1,4 h |
| TMAG5253BA3 sempre ligado, 600 MHz | 4,5 h | 2,7 h | 3,4 h | 1,9 h |
| TMAG5253BA3 por grupo, 600 MHz | 5,5 h | 3,5 h | 3,9 h | 2,2 h |
| **TMAG5253BA3 por grupo, 396 MHz (recomendado)** | **6,9 h** | **4,2 h** | **4,5 h** | **2,4 h** |
| TMAG5253BA3 por grupo, 240 MHz | 7,9 h | 4,6 h | 5,0 h | 2,6 h |

- Trilho de 3,3 V no recomendado: ~128 mA típicos com fone (Teensy ~69, sensores 36, Audio
  Board 20). Antes: ~290 mA.
- Alto-falante: 0,2 W médios típicos, 0,5 W no pior caso (estimativa, conferir de ouvido).
- Ligado sem tocar: ~93 mA (~9 h). Desligamento leve: ~23 mA (~1,5 dia). Com KEEP ou chave: ~10 µA.
- Medido em hardware: só CPU e tempo de leitura. Correntes: datasheets e modelo (conferir no protótipo).

### Para o design conferir o encaixe

- Bateria: reservar **7 × 36 × 58** + saída de ~60 mm de fio com JST PH 2,0; acesso pelo fundo.
- Alto-falante Ø36 × 6,0 (CLS0361-L152) com **8–12 cm³** de volume traseiro fechado; ou Ø36 × 4,6
  (AS03608MR) com 6–10 cm³; ou 30 × 20 × 4,0 com 3–5 cm³.
- Potenciômetro com chave: corpo ~9,5 × 10 em planta (versão vertical), **31–36 de altura do
  topo da placa à ponta do eixo**; rosca M7.
- Novo na placa principal (D2): BQ24074, TPS63802 + indutor ~4 × 4, PAM8302A, portas do EN,
  JST PH 2 vias da bateria, 2 vias do alto-falante, 4 fios do jack, 1 fio do VUSB.

### O que a programação precisa ajustar (`pcb/PINOS.md`, provisório)

1. `MUX_COUNT = 2`, COMs em 14 e 15. O pino 16 vira **VBAT** (A2, bateria/2).
2. LED vermelho **4 → 13** (verde continua no 5). O pino 4 vira **SENS_EN**.
3. Encoder A **17 → 11** (B no 9, clique no 6, iguais). O pino 17 vira **HP_DET** (A3).
4. Novos: **KEEP** = 10 (subir na partida, em `startup_early_hook`), **AMP_SD** = 12.
5. Leitura por grupos (S3) com espera de 45 µs (BA3) depois de trocar de grupo.
6. `SENSOR_ZERO` / `PRESENT_MIN` do TMAG5253 (BA3: repouso 1,65 V).
7. `set_arm_clock(396000000)`; medir a CPU do Pocket e, se der, 240 MHz.
8. "Carregando" deduzido de VBUS + VBAT (sem pino do carregador); cortar em VBAT < 3,3 V.

## Perguntas para a gestão

Do E2b (as do E2 continuam abertas, logo abaixo):

1. **Placa principal de 4 camadas?** Em 2 camadas o roteamento não fechou na zona do Teensy; com
   planos de GND e 3,3 V fecha com DRC 0/0/0. A JLCPCB faz 4 camadas em 1,2 mm, mais cara que 2.
   Aceita, ou prefere que eu tente 2 camadas espalhando mais as peças (mais tempo, sem garantia)?
2. **TPS63001 no lugar do TPS63802:** mesma função, 3,3 V fixo, com desenho no KiCad e na LCSC
   (C28060). Custa ~0,2 h de autonomia no modelo (6,7 h com fone). Aceita?
3. **Cabos soldados nas plaquinhas** (knobs, volume e painel: o SH sai crimpado só do lado da placa
   principal): aceitável para o protótipo, ou quer conectores (pede ~1 mm a mais na plaquinha dos knobs
   e outro lugar para o J1 dela)?
4. **Plaquinha dos knobs com abas** para as pernas do encoder (design confirma o espaço)?

Do E2 (sem resposta ainda):

5. **Potenciômetro com chave:** aprova o 9 mm com chave montado deitado numa plaquinha vertical, preso
   na tampa pela porca M7?
6. **USB-C e fone numa plaquinha do painel** com cabo micro-B de 90° cortado e soldado: aceitável?
7. **Bateria de 3 fios:** aceita 1000 a 1200 mAh (603450)? E o fornecedor?
8. **LED durante a carga:** vermelho aceso pelo carregador mesmo ligado (laranja tocando), ou só com
   o Pocket desligado (um transistor a mais)?
