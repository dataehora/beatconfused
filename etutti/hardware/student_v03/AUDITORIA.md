# Student V3 — auditoria de chips (pinagem, esquema, valores)

Feita em 18 nov 2026 sobre a placa V2 (a base do V3). Método:

1. **Pinagem contra o símbolo da peça real.** `auditoria_pinos.py` lê, de cada código LCSC, o símbolo da EasyEDA (o
   da peça que a JLCPCB vai colocar) e o põe ao lado da rede que a nossa placa tem no mesmo pad. Saída em
   `pcb/auditoria_pinos.json`. Isso pega o erro "pinagem de um clone diferente do original".
2. **Datasheets lidos** (quando foi possível obter o PDF): BQ24074, TPS63001, TMAG5253 (TI), SGTL5000 (Freescale/NXP,
   figuras 19 e 20), esquema do MicroMod Teensy (SparkFun, v13).
3. **Valores** dos componentes de cada circuito de referência contra o datasheet.

## Resultado por chip

| Chip | Pinagem | Valores e ligação | Fonte |
|---|---|---|---|
| **SGTL5000** (U301) | ✔ 20QFN: 1 HP_R … 20 VDDD, igual à figura 20 | **C307 (VAG) era 150 nF, da Audio Board antiga; o datasheet pede 0,1 µF → corrigido para 100 nF.** VDDD externo de 1,8 V (U302) como o datasheet exige "para projetos novos", com C de 2,2 µF (o mínimo é 0,1 µF). VDDA por ferrite + 100 nF, VDDIO 3,3 V. 20QFN não tem CPFILT | datasheet |
| **BQ24074** (U202) | ✔ TS, BAT, CE#, EN2, EN1, PGOOD#, VSS, CHG#, OUT, ILIM, IN, TMR, ITERM, ISET | EN2=0 e EN1=1 → USB500 (tabela 7-2) ✔. TMR e ITERM abertos = padrão (o datasheet diz "deixe sem ligação") ✔. ICHG = 890/R_ISET (K_ISET 797–975 AΩ): **R203 1,8 kΩ → 2,2 kΩ**, 0,405 A (Basic). TS precisa do NTC de 10 kΩ da bateria de 3 fios ✔ | datasheet |
| **TPS63001** (U204) | ✔ 1 VOUT, 2 L2, 3 PGND, 4 L1, 5 VIN, 6 EN, 7 PS/SYNC, 8 VINA, 9 GND, 10 FB, 11 PAD | FB ligado ao VOUT (versão de 3,3 V fixa) ✔; PS/SYNC baixo = economia ✔; L de 2,2 µH, 10 µF na entrada e 2 × 10 µF na saída, R de 100 Ω no VINA ✔ (o circuito típico) | datasheet |
| **TMAG5253** (U701–U728) | ✔ 1 VCC, 2 GND, 3 EN, 4 OUT, pad térmico ligado ao GND | 100 nF por sensor (o datasheet pede ≥ 0,1 µF) ✔. EN = EN_A/EN_B (as portas U604/U605) | datasheet |
| **MAX98357A** (U501) | ✔ TQFN-16, DIN 1, GAIN 2, SD_MODE 4, VDD 7/8, OUTP 9, OUTN 10, LRCLK 14, BCLK 16 | GAIN_SLOT aberto = 9 dB ✔. SD_MODE = 3,3 V × 100 k/(100 k + R501): **680 k → 1 MΩ** dá 0,30 V, dentro da janela mono (0,16 a 0,77 V). VDD ligado ao VSYS (≤ 5,5 V) ✔ | símbolo + datasheet conhecido |
| **74HC4067** (U601/U602) | ✔ Z 1, Y0–Y15, S0–S3, E# 15, VCC 24 | E# no GND (sempre ligado; a habilitação dos sensores é pelo EN dos TMAG) ✔ | símbolo |
| **74LVC1G04/08** (U203, U603–U605) | ✔ SOT-23-5 | alimentadas a 3,3 V ✔ | símbolo |
| **XC6206P182MR** (U302, UMW C347373) | ✔ pelo símbolo: 1 VSS, 2 VOUT, 3 VIN, igual às nossas redes | **Atenção: clones de XC6206 diferem de pinagem. O PDF do fabricante da LCSC não pôde ser baixado; a pinagem está conferida só contra o símbolo da EasyEDA.** Conferir na primeira placa (3,3 V na entrada, 1,8 V na saída, antes de ligar o codec) | símbolo |
| **USBLC6-2SC6** (U201) | ✔ 1 e 6 = D+, 3 e 4 = D−, 2 GND, 5 VBUS | | símbolo |
| **AO3401A** (Q203) | ✔ 1 G, 2 S, 3 D | P-FET do clique do volume ✔ | símbolo |
| **BAV70** (D202–D205; era BAT54C) | ✔ SOT-23: 1 A1, 2 A2, 3 catodo comum (igual ao BAT54C) | Queda de ~0,5 V em vez de ~0,2 V: a leitura do CHG (pino com pull-up, VIL de ~1,0 V) e o ONOFF do módulo (VIL ~0,9 V) ainda têm 0,4 V de folga; o EN do TPS63001 (VIH baixo) recebe 2,3 a 2,7 V. **Troca aplicada; confirmar na bancada** | análise |
| **MicroMod J101** (M.2, 67 pads) | ✔ conferido contra o esquema do MicroMod Teensy da SparkFun (v13): 2 e 74 = 3,3 V, 3 D+, 5 D−, 4 3,3V_EN, 6 RESET/ON-OFF, 9 USB_VIN, 11 BOOT, 12 SDA, 14 SCL, 50/52/54/56/58 = BCLK/LRCLK/AUD_IN/AUD_OUT/MCLK, 34 e 38 = A0 e A1 (os COM dos sensores, analógicos), os demais são GPIO | | esquema |
| **USB-C** (J201) | ✔ A5/B5 CC com 5,1 kΩ, D+/D− nos dois lados | | símbolo |
| **Jacks PJ-327A** (J301 OUT, J302 IN) | ⚠ **só os números dos pinos**: a função de cada pino (ponta, anéis, luva, chave) vem do datasheet da Shouhan, que não pude baixar. A ligação de V2 (OUT: luva e HP_VGND no 1 e 2, R no 3, L no 4, chave no 5; IN: GND no 1 e 2, microfone no 4) é a do projeto e não foi reconferida | **conferir contra o datasheet antes de encomendar** |
| **Botão Program** (SW403, TS-1187A) | ⚠ idem: a ligação interna dos 4 pinos vem do datasheet da XKB (não baixado) | conferir |
| **Encoders** (SW401/402) | ✔ A, B, C (comum), S1/S2 (clique) | | símbolo |
| **JST PH** (J202) | ✔ 1 VBAT, 2 NTC, 3 GND | a ordem dos fios da bateria varia por fabricante: medir | |
| **JST SH** (J401) | ✔ ordem Qwiic: 1 GND, 2 3,3 V, 3 SDA, 4 SCL | | |

## O que esta auditoria encontrou

Erros de valor, não de pinagem:

1. **C307 (VAG do SGTL5000): 150 nF, o valor de uma versão antiga da Audio Board; o datasheet manda 0,1 µF.** Corrigido.
2. R203 e R501 eram valores Extended com um Basic equivalente: trocados (0,405 A de carga; 0,30 V no SD_MODE).
3. BAT54C → BAV70 (Basic): a queda do diodo sobe, mas as margens calculadas ficam folgadas.

Nenhuma pinagem de chip estava trocada.

## O que não foi possível conferir

- Datasheets que a LCSC serve como página HTML e não como PDF: **PJ-327A, TS-1187A e XC6206 da UMW**. A ligação dessas três está conferida só pelo símbolo da EasyEDA ou pelo projeto antigo. Se você tiver os PDFs, me passe.
- **Sequência de ligação**: li as redes (clique → Q203 → PWR_KEY → D203 → EN_REQ → TPS63001; USB presente → BQ24074 → VSYS; KEEP do firmware segura o EN), mas não simulei o comportamento, e nada disso rodou em placa real.
- A sequência de alimentação do SGTL5000 (VDDD externo depois de VDDA e VDDIO) segue o datasheet ("VDDD de 1,1 a 2,0 V, 11 mA mínimo"); o LDO de 1,8 V sobe com o 3,3 V.
