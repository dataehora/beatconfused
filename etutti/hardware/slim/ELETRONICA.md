# eTutti Slim · Eletrônica (SPEC R1SL, etapa 1 — portão A)

Atende a **SPEC R1SL §8, item 1**. Nada é colocado nem roteado: só componentes, esquema e lógica. Independente da V4 (a máquina de escrever o esquema foi **copiada** para `pcb/`, nada é importado da V4).

## 1. O que foi feito

| Entrega | Onde | Estado |
|---|---|---|
| Esquema KiCad da **placa principal** (5 folhas: P processador, E energia, F fone, I interface, R conectores das réguas) | `pcb/schematic.py` → `pcb/kicad/` | **ERC 0 erros / 0 avisos**, netlist = declarada. 119 peças, 93 redes |
| Esquema KiCad da **régua R8** | `pcb/regua/schematic_regua.py` → `pcb/kicad_regua/` | **ERC 0 / 0**, netlist = declarada. 20 peças, 14 redes |
| BOM com PN, LCSC, Basic/Extended, estoque | `pcb/bom_esquema.csv`, `pcb/bom_regua.csv`, conferência em `fornecimento/bom_conferido.{csv,json}` (50 códigos, LCSC + JLCPCB) | feita em 24 nov 2026 |
| Mapa de pinos do RT1062 (pinos Teensy 4.1 ↔ bolas) | `pcb/PINOS.md` (gerado por `pcb/pinos.py`) | contrato com a programação; conferido contra o sketch (`etutti/firmware/slim/check_pins.py`, 16/16) |
| Lógica de energia (BQ24075 + SYSOFF + USB) | seção 3 | projetada; **não testada em bancada** |
| Escada da chave de 7 posições | seção 4 | calculada |
| STEP dos componentes escolhidos | `modelos/` (`fetch_models.py`; 14 de 16 baixados, fora do Git) | medidas na seção 7 |

Rodar (da raiz do repositório): `python etutti/hardware/slim/pcb/schematic.py`, depois `.../pcb/regua/schematic_regua.py`, `.../pcb/pinos.py`, `.../fornecimento/conferir_bom_slim.py` (~3 min, 2 s entre pedidos).

## 2. Escolhas de componentes

| Função | Escolha | LCSC / classe / estoque (24 nov) | Observação |
|---|---|---|---|
| Processador | **RT1062 chip-down** | **MIMXRT1062DVJ6B** (12×12 mm, 0,8 mm) C3216699 · Ext · **1** em estoque. A SPEC cita **DVL6B** (C2847497 · Ext · 64) | **Desvio da SPEC, ver §6.1.** O mapa de bolas do esquema é o do 12×12 (o do Viaggio) |
| Bootloader | MKL02 com bootloader PJRC | **consignada** (só a PJRC vende) | como a SPEC |
| Flash | W25Q64JVSSIM | C5362615 · Ext · 3944 | 64 Mbit, como a Teensy 4.1 |
| Cristal 24 MHz | 7U24000E08UCG (8 pF) | C524739 · Ext · 3410 | o C431156 do Viaggio está **sem estoque** |
| Codec | SGTL5000XNLA3R2 (QFN-20) | C2651833 · Ext · 952 | só saída de fone; **C307 = 100 nF** (datasheet: VAG 0,1 µF) |
| Carregador | **BQ24075RGTR** | C15464 · Ext · 15786 | SYSOFF no pino 15 |
| 3,3 V | TPS63001DRCR + FNR4020S2R2MT | C28060 / C167825 · Ext | buck-boost (a bateria desce a 3,0 V) |
| USB‑C | **TYPE-C-31-M-14** (HRO, 16 pinos, “laminated board” = mid-mount) | C223907 · Ext · 2218 | modelo 11,45 × 8,56 × 3,16 mm; a JLCPCB pode não montar peça mid-mount por baixo (ver §6.4) |
| P2 OUT (3,5 mm) | **mid-mount: não achei peça em estoque** | nenhuma (só entradas com estoque 0) | montar em casa ou consignar; o esquema usa o footprint do PJ-327A de topo só como marcador |
| **Pot 9 mm com chave** | **nenhum na LCSC/JLCPCB** | — | **ver §6.2**: o RK097 de 5 pinos da LCSC (RK0971114Z1N, C2938587) tem chave de **empurrar**, não rotativa; candidato a conferir: Same Sky PTN09S1 (9,5 mm, “SWITCH”, DigiKey), sem datasheet lido |
| **Chave de 7 posições** | **Alps SRBV170501** | C470375 · Ext · 325 | 1 polo, 7 posições, **sem curto** entre posições, 30° por passo, corpo de 7,5 mm; eixo L = 15 ou 20 mm (170501 × 170701: conferir qual é qual); STEP do 170501 não existe (EasyEDA dá o 141404) |
| Réguas: sensor | TMAG5253BA3IQDMRR | C22401868 · Ext · 2912 (LCSC: 229) | 32 por instrumento |
| Réguas: registrador | 74HC595BQ,115 (DHVQFN-16) | C730243 · Ext · 137 mil | |
| Conector das réguas | FFC 8 vias 0,5 mm, contato por baixo | C66953 · Ext · 5028 | **altura 2,0 mm**: ver §6.5 |
| Bateria (conector) | JST PH S3B-PH-SM4-TB | C265101 · Ext | **5,5 mm de altura**: ver §6.5 |
| Bateria | **LP402764-1000** (68 × 28 × 4,5 máx., 1000 mAh) | não é peça JLCPCB | ver §5 |
| LED | TJ-S1615SW6TGLCRG-A5 | C273605 · Ext | vermelho/verde |
| PROG | TS-1187A | C318884 · **Basic** | |
| Demais passivos | 0402 de valores Basic | 21 tipos Extended no total (a JLCPCB cobra por tipo Extended) | **sem cotação**, como pede a SPEC |

Tipos **Extended** (principal + régua): 21. Os resistores da escada foram escolhidos só entre valores **Basic** (1 k, 2,2 k, 4,7 k, 10 k, 22 k, 47 k, 100 k) para não criar tipos novos; o PTC (F201) e o 2,2 MΩ do cristal são Extended e podem sair (o PTC está na SPEC §5.2).

## 3. Energia: BQ24075 + SYSOFF + USB

Fato do datasheet (TI SLUS810, seção SYSOFF): **SYSOFF tem pull-up interno de ~5 MΩ no VBAT**; SYSOFF alto desconecta a bateria do OUT e, com adaptador, **desliga também a carga**; deixe-o sempre acionado, nunca flutuando. Logo: sem acionamento externo a bateria fica **desconectada** (consumo ~0), e qualquer lógica só precisa **puxar o SYSOFF a GND** quando o instrumento deve ligar.

```
 VBAT ──SW401 (chave do pot: SW1-SW2)── SWV ──┬─ C205 4,7 µF ──┐                         BQ24075
                                              │                ├─ ONG ─ Q201 (N) ──┐
                                              ├─ R215+R216 (2 M) → SW_S (pino 25)    ├──────── SYSOFF (pino 15)
                                              └─ Q202 (P, fonte=SWV, dreno=ONG) ─┘   │
                                        KEEP (pino 10) → Q203 (N) → gate de Q202      │
 VBUS_F → R213/R214 (divisor 100k/100k) → VBUS_G → Q204 (N) ──────────────────────────┘
```

| Situação | SYSOFF | Resultado |
|---|---|---|
| Knob OFF, sem USB | alto (pull-up interno) | bateria desligada do OUT: **nada consome**; o sistema está desligado |
| Knob sai de OFF (chave fecha) | baixo por ~3 s | o fechamento empurra ~VBAT no ONG por C205 (R210 1 MΩ o descarrega, τ ≈ 3 s com a perda de capacitância): Q201 liga, OUT sobe, o 3,3 V sobe, o RT1062 parte; **o firmware põe KEEP = 1 logo na partida** (`setup()`), Q203 → Q202 passa a manter o ONG em SWV: o sistema fica ligado enquanto a chave estiver fechada |
| Knob ON | baixo (KEEP) | funciona só na bateria; o firmware lê a chave (SW_S = SWV/2 ≥ 1,0 V) |
| Knob vai a OFF | alto | **em hardware**: SWV cai, Q202 deixa de conduzir (só conduz com a chave fechada), o ONG descarrega: o sistema desliga sem depender do firmware |
| Desligamento automático (15 min sem uso, ou bateria < 3,3 V por 5 s) | alto | o firmware solta KEEP: SYSOFF é solto, a bateria se desconecta, a placa morre; para ligar de novo: **abrir e fechar o knob** (nova borda) |
| **USB presente** | **baixo** (Q204, gate = ½ VBUS ≈ 2,5 V) | o BQ24075 carrega e alimenta o OUT; o instrumento acorda **com o knob em OFF** (“soft off”: mudo, LED de carga, MIDI vivo). Com USB o KEEP não é preciso |
| USB sai com o knob OFF | alto | desliga |
| USB sai com o knob ON | segue baixo (KEEP) | continua na bateria |

Pontos conferidos: Q201/Q203/Q204 = AO3400A (Vth máx. 1,45 V), Q202 = AO3401A, ambos **Basic**; com a bateria em 3,0 V os gates ainda ficam com ≥ 1,5 V de folga. A SPEC pedia “lógica mantém SYSOFF baixo sempre que há USB”: é o Q204. Correntes em espera: knob fechado, R215+R216 = 2 MΩ (~2 µA) e R211 100 kΩ só com o KEEP ligado (SWV/100 k = 40 µA, em operação).
**Risco que só a bancada fecha:** a duração do pulso de partida (C205 × R210 depende da capacitância real do X5R sob 4 V). Se o RT1062 levar mais de ~2 s para ligar o KEEP (a partida normal da Teensy é < 0,5 s, com a rotina de calibração das teclas vindo depois do KEEP), o sistema desliga antes. Se for preciso, R210 sobe para 2,2 MΩ.

## 4. Escada da chave de 7 posições

Comum (pinos 1 e 10) → `REG_ADC` (pino 24 / A10); R401 10 kΩ de +3V3 até o comum; cada posição k (pinos 2…8) liga o comum a um resistor para GND; o pino 9 é terminal virtual (não usado). Como a chave é “sem curto”, **entre duas posições o comum fica aberto = 3,3 V**, e o firmware mantém a última posição.

| Pos. | Registro | Resistor | Tensão (3,3 V) | Contagem 12 bits |
|---|---|---|---|---|
| 1 | L | 1 k (R402) | 0,300 V | 373 |
| 2 | LM | 2,2 k (R403) | 0,595 V | 739 |
| 3 | M | 4,7 k (R404) | 1,055 V | 1310 |
| 4 | MM | 10 k (R405) | 1,650 V | 2048 |
| 5 | MH | 22 k (R406) | 2,269 V | 2817 |
| 6 | LH | 47 k (R407) | 2,720 V | 3376 |
| 7 | H | 100 k (R408) | 3,000 V | 3724 |
| — | entre posições | aberto | 3,300 V | 4095 |

A menor distância entre dois níveis é 0,28 V (47 k → 100 k) = 350 contagens, contra ±1 % dos resistores (≈ 40 contagens no pior caso): folga de 8×. Limiar de “aberto”: 3,15 V. Os valores são todos **Basic**.

## 5. Bateria (a SPEC pede opções de distribuidor com NTC)

Envelope da SPEC: 4,5 × 28 × 68 mm, baia em x −88…−60 (28 mm) e y −14,5…54 (68,5 mm).
- **LP402764-1000** (folha de dados de um fabricante de Shenzhen, vista em um fórum da TI): 3,7 V, 1000 mAh, **máximos** 68 × 28 × 4,5 mm, PCM de 1,5 A, cabos 26 AWG com conector ZHL1.25. É exatamente o envelope: **folga de 0 mm na largura e 0,5 mm no comprimento** nos máximos.
- **Não achei** distribuidor com um LP402764 (ou equivalente de ≤ 4,5 mm) **com NTC de 3 fios e JST PH 2,0**. O 3 fios com NTC que existe em loja (Core Electronics, 1000 mAh) mede 7 × 30 × 50 mm: não cabe.
- Caminho prático: pedir ao fabricante o **LP402764 com NTC de 10 kΩ em 3 fios e conector JST PH** (ou o conector que o J preferir), ou usar uma bateria de 2 fios e **ligar o TS do BQ24075 a um resistor de 10 kΩ para GND** (o carregador passa a ignorar temperatura): isso muda o esquema (R + NTC sai).
- O que o J precisa escolher e mandar o STEP: ver as perguntas no `FIT_CHECK.md`.

## 6. Problemas encontrados (desvios e riscos)

1. **RT1062: a SPEC mistura dois encapsulamentos.** “MIMXRT1062DVL6B (BGA196 12 × 12, passo 0,8)”: o **DVL6B é o 10 × 10 mm** (a Teensy usa esse; EasyEDA chama o modelo de P0.65), enquanto o 12 × 12 mm de 0,8 mm é o **DVJ6B**. LCSC/JLCPCB: DVL6B **64** em estoque (US$ ~14), DVJ6B **1**. O esquema usa o mapa de bolas do 12 × 12 (o do Viaggio, 196 bolas, mesmos nomes de bolas que a Teensy, que usa o 10 × 10: conferir na NXP). **Pergunta 1.** O RT1062 é peça Extended e sai da JLCPCB só se houver estoque: com 1 peça não dá para montar 5 placas; em ambos os casos a opção segura é **consignar** (PJRC/DigiKey/Mouser).
2. **Pot 9 mm com chave rotativa: não existe no catálogo da JLCPCB.** O que a LCSC tem na série RK097 com chave tem chave de empurrar (0,5 mm de curso) ou nenhuma. Fica como peça **montada em casa**, de distribuidor: candidatos a ler o datasheet antes (Alps RK097 com “chave rotativa” = dígito de chave 1 no PN; Same Sky PTN09S1). **Pergunta 2.** Alternativa sem chave física: pot comum + comparador de baixa corrente que puxa o SYSOFF quando o cursor sai de ~0 V (sem o “clique” tátil, e o pot consome ~66 µA o tempo todo ligado a VBAT, ou um comparador micropower a mais); não implementei.
3. **Chave de 7 posições é longa.** O STEP mais próximo (SRBV141404) mede 26,5 mm no total, **21,9 mm acima da face da placa** e 4,6 mm de pinos abaixo: com a placa a z = 5,0 o eixo chega a z ≈ 27, bem acima do tampo (14 mm no nível da fileira 1; “knobs baixos em poços de 1,2 mm” fica impossível com esse eixo). Ver o `FIT_CHECK.md`.
4. **Peças mid-mount (USB-C e jack):** têm pernas dos dois lados da placa; a JLCPCB pode não montá-las pelo processo “só face de baixo”. Previsto: soldar à mão ou consignar. **Pergunta 3** no FIT_CHECK.
5. **Alturas abaixo da placa:** a SPEC dá 2,2 mm entre a face de baixo da régua (z 3,8) e o piso (z 1,6). FFC de 2,0 mm deixa 0,1–0,2 mm; o indutor FNR4020 (STEP: 2,6 mm) e o JST PH de lado (5,5 mm) **não cabem** nessa folga: ver o FIT_CHECK.
6. **Par USB (SPEC §5.2: 30–35 mm):** em Full Speed (12 Mbit/s, subida ≥ 4 ns) 35 mm de FR-4 (~0,23 ns de atraso) é eletricamente curto: **aceitável**, com 90 Ω diferenciais só como boa prática. O **risco** é a Teensy 4 negociar **High Speed (480 Mbit/s)** num host que o aceite: com um par longo e sem impedância controlada isso pode falhar. Mitigação: forçar Full Speed (`USB_PORTSC1.PFSC`) no firmware; **não verificado** (precisa da placa). **Pergunta 4.**
7. **Nada do esquema foi comprado, cotado, posicionado ou roteado.** Estoques e códigos de 24 nov 2026; mudam.

## 7. Medidas dos STEP baixados (EasyEDA, por código LCSC; `modelos/index.json`)

| Peça | Caixa (mm) | Observação |
|---|---|---|
| USB-C TYPE-C-31-M-14 | 11,45 × 8,56 × 3,16 | |
| SRBV (modelo do 141404) | 18,22 × 19,85 × 26,5 (z −4,6…21,9) | modelo aproximado do 170501 |
| RT1062 DVL6B | 10,0 × 10,0 × 1,51 | (o DVJ6B não tem modelo) |
| BQ24075 / TPS63001 / SGTL5000 | 3,0 × 3,0 × 0,6–0,76 | |
| FFC 8P | 8,3 × 6,6 × 2,1 | |
| TMAG5253 / 74HC595 | 1,42 × 1,1 × 0,41 / 3,52 × 2,52 × 1,03 | |
| JST PH lateral S3B | 10,0 × 8,5 × 5,5 | |
| Indutor FNR4020 | 4,0 × 4,0 × 2,61 | |
| LED 1615 / TS-1187A / cristal | 0,6 / 1,55 / 0,72 de altura | |

## Perguntas para o design

(As perguntas completas, com as de posicionamento, estão em `FIT_CHECK.md`, fim.)
