# eTutti Viaggio · relatório da eletrônica

**SPEC v2 (Rev2), passo 3.1: esquema. 24 out 2026.** Dono: eletrônica. Sem placa neste passo:
nada foi posicionado nem roteado, nada foi encomendado.

## O que foi feito

- **Esquema KiCad 10** em `pcb/kicad/`: `viaggio.kicad_sch` (raiz) e uma folha por setor
  (`viaggio_P/E/F/I/A/T.kicad_sch`), mais a biblioteca própria `viaggio.kicad_sym` e o `sym-lib-table`.
  - Quem escreve tudo é `pcb/schematic.py` (Python puro). O circuito fica como dados, uma lista
    por setor. **Não editar os `.kicad_sch` à mão:** mudar o script e rodar de novo:

    ```
    python etutti/hardware/viaggio/pcb/schematic.py
    ```

  - Cada peça tem o campo **`Codigo`** com o código da SPEC §3 (P1…T4), visível ao lado da
    referência. É o mesmo código de `concept/rev2/out/viaggio_rev2.json`. As referências seguem uma
    faixa por folha: P = 1xx, E = 2xx, F = 3xx, I = 4xx, A = 5xx, T = 6xx/7xx (sensores U701–U728).
  - Ligações por rótulos globais em cada pino; os nomes são os do `PINOS.md`.
  - A raiz tem os PWR_FLAG das redes que o ERC não vê alimentadas: VBUS (conector), DCDC_IN e
    SGTL_VDDA (ferrites), VDD_SOC (indutor do DCDC), VDD_SNVS_IN (diodos), BB_VINA (RC) e GND.
- **ERC: 0 erros, 0 avisos** (`kicad-cli sch erc --severity-all`, relatório em
  `pcb/build/viaggio_erc.json`).
- **Conferência da netlist:** o script exporta a netlist pelo KiCad (`pcb/build/viaggio_netlist.net`) e
  a compara, rede a rede, com as ligações declaradas. Resultado: **136 redes, 179 peças, tudo igual.**
  O script sai com erro se o ERC ou essa conferência falharem.
- **`pcb/PINOS.md`** em numeração Teensy 4.1, com as diferenças em relação ao Pocket.
- **`pcb/bom_preliminar.csv`**: 84 linhas, 179 peças, com código LCSC, classe básica/estendida,
  preço unitário estimado, montagem e status (final/conferir).
- **`pcb/rt1062_balls.json`**: as 196 bolas do RT1062 12 × 12, extraídas da tabela 87 do datasheet da
  NXP. Elas conferem com as 133 bolas que o esquema do Teensy 4.1 nomeia (nenhuma diferença).
- **Integração:** `.claude/agents/eletronica.md` passa a cobrir o Viaggio, e o `CLAUDE.md` aponta a
  SPEC v2 e o plano da §7.

## O circuito, setor por setor

### P · Processador (a partir do esquema público do Teensy 4.1)

- **P1 RT1062 DVJ6B** em 6 unidades no símbolo: alimentação, sistema, GPIO_AD, GPIO_B, GPIO_EMC e
  GPIO_SD.
  - Alimentação como no Teensy 4.1: DCDC_IN pela ferrite de 120 Ω (L101), DCDC_LP → 4,7 µH → VDD_SOC
    (com o DCDC_SENSE) e todos os NVCC no 3,3 V.
  - Os capacitores são os da PJRC, com a referência Teensy no campo Description (C32, C24, C19…).
  - USB1 no USB-C. Os dois VBUS do RT1062 vão no VBUS.
  - Sem Ethernet, USB host ou cartão SD: as bolas deles ficam marcadas "sem ligação".
- **SNVS:** D101/D102 = os D2/D1 do Teensy. O anodo que no Teensy é a pilha (VBAT) aqui recebe o
  SNVS_3V3 do LDO sempre ligado E5. Assim o SNVS liga antes de qualquer outro regulador.
- **PMIC_ON_REQ** (100 kΩ para o GND, R7 do Teensy) entra na porta U206. O 3,3 V só sobe com ele
  alto (ver E5).
- **P2 MKL02** exatamente como no Teensy 4.1:
  - PTA3 → DCDC_PSWITCH + AD_B0_11 + 100 kΩ para o GND (sem RC);
  - PTB5 → AD_B0_08; PTA4 → AD_B0_04; PTA5/PTB0/PTA7/PTA6 → AD_B0_06/07/09/10 (JTAG);
  - PTA1 → EMC_01, PTB4 → B0_13, PTB1 → POR_B;
  - PTB2 = Program (I4), PTB3 = LED vermelho de erro (470 Ω);
  - PTA0/PTA2 sem ligação;
  - AD_B0_05 no GND.
- **P3 flash** W25Q64JV em SD_B1_06–11. **P4 PSRAM** APS6404L em EMC_24–29, marcada "não montar".
- **P5 cristais**: 24 MHz com 2 × 12 pF e 2,2 MΩ do XTALI ao GND, como a PJRC desenhou; 32,768 kHz
  com 2 × 20 pF.
- **MCLK:** 100 Ω em série (R105, código P1), para ficar junto do P1 (SPEC §4, 8º).
- **Modo seguro:** nada no hardware o ativa. Só a firmware poderia fazer isso, com o sketch de
  travamento da PJRC.

### E · Energia (a partir do Pocket)

- **E1/E2:** USB-C TYPE-C-31-M-12, 2 × 5,1 kΩ nos CC, USBLC6-2SC6 no D+/D− e no VBUS, TVS SMF5.0A no
  VBUS.
- **E3:** BQ24074 em USB500 (EN2 = 0, EN1 = 1), 500 mA (1,8 kΩ), ILIM 1,5 kΩ, NTC no TS. TMR e ITERM
  ficam abertos (valores padrão, conferido no datasheet).
  - Luz de carga como no Pocket (Q201/Q202): o vermelho acende com o ~CHG só com o aparelho
    desligado.
  - **STAT:** o ~CHG chega ao pino 26 por um diodo (D202).
  - Divisor de 1 MΩ / 1 MΩ da bateria no pino 16.
- **Trava liga/desliga (E3):** o clique de I2 liga o Q203, que leva o VSYS ao EN pelo D203. O KEEP
  (pino 10) entra pelo mesmo diodo duplo. O "USB mantém ligado" é a porta U203, alimentada pelo
  3,3 V: USB **e** aparelho já ligado. Plugar a USB com o aparelho desligado não liga nada, só
  carrega.
- **E4:** TPS63001 (3,3 V fixo), indutor de 2,2 µH, VINA por RC.
- **E5 (partida do P1):** LDO XC6206P332MR sempre ligado no VSYS (1 µA) → SNVS_3V3. Ele alimenta
  o SNVS (por D101) e a porta U206. **EN do TPS63001 = PMIC_ON_REQ E EN_REQ.**
  - A PJRC pede que o 3,3 V ligue com o PMIC_ON_REQ, e que o regulador entenda 1,1 V. O TPS63001
    pede ≥ 1,2 V no EN, então a porta é necessária.
  - A porta é um 74LVC1G08 a 3,3 V (VIH 2,3 V). Ela só deixa passar quando o PMIC_ON_REQ chega ao
    nível do SNVS (~3,1 V), depois da fase de 1,1 V: o 3,3 V espera o SNVS terminar de ligar.
- **E6:** JST PH 3 vias SMD em ângulo reto (1 = +, 2 = NTC, 3 = −, ordem do Pocket).

### F · Fone (a partir da Audio Board Rev D2 que o Pocket usava)

- **F1:** SGTL5000 de 20 pinos como a Rev D2:
  - VDDA pela ferrite de 600 Ω, VDDIO no 3,3 V, VDDD a 1,8 V por LDO (a Rev D2 usa AP7313; aqui
    XC6206P182MR, mesmo encapsulamento);
  - VAG 0,15 µF, I2C com 2,2 kΩ;
  - entrada de linha, microfone, saída de linha e DOUT sem ligação.
- **F2:** jack com contato na ponta. A ponta vai no HP_L, o anel no HP_R e a manga no **HP_VGND**,
  nunca no GND. O contato da ponta vai ao HP_DET (100 kΩ, 1 MΩ, 100 nF; igual ao Pocket).

### I · Interface

- **I1/I2:** dois EC11E com clique. A, B, comum e um lado da chave no GND.
- **I3:** LED vermelho/verde de 4 pads. O vermelho passa pelo OU (D402) da luz de carga com o pino
  13 (270 Ω); o verde vai ao pino 5 (330 Ω).
- **I4:** botão Program para o GND.

### A · Alto-falante

- **A1:** MAX98357A no VSYS, no mesmo I2S do F1. GAIN_SLOT aberto (9 dB). SD_MODE pelo pino 12 com
  680 kΩ, o que dá mono (L+R)/2.
- **A2:** dois pads para os fios do alto-falante.

### T · Teclas

- **T1/T2:** 74HC4067PW, a versão em TSSOP-24 pedida na SPEC; o CD74HC4067 da TI não existe em
  TSSOP, e a pinagem da Nexperia é igual. T1 = metade esquerda, COM no pino 15; T2 = metade direita,
  COM no 14.
- **T3:** 74LVC1G04 + 2 × 1G08, que fazem o EN_A e o EN_B a partir do SENS_EN e do S3.
- **T4:** 28 × TMAG5253BA3 com 100 nF cada. A almofada térmica vai no GND (o datasheet permite).
  Os canais e os grupos EN seguem o Pocket v0.3 (`pocket/pcb/build/pocket_keys.csv`, mesmas posições
  de tecla). O passo 3.4 os refaz pelo roteamento.

## Peças escolhidas e datasheets

| Código | Peça | LCSC | Classe | Datasheet |
|---|---|---|---|---|
| P1 | NXP MIMXRT1062DVJ6B | consignada | — | [IMXRT1060CEC rev 4 (cópia da PJRC)](https://www.pjrc.com/teensy/IMXRT1060CEC_rev4.pdf), [esquema Teensy 4.1](https://www.pjrc.com/teensy/schematic.html) |
| P2 | PJRC MKL02 (bootloader Teensy 4.1) | consignada | — | [PJRC](https://www.pjrc.com/store/ic_mkl02_t4.html) |
| P3 | Winbond W25Q64JVSSIQ, SOIC-8 208 mil | C179171 | estendida | [Winbond W25Q64JV](https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en&partNo=W25Q64JV) |
| P4 | AP Memory APS6404L-3SQR-ZR (não montar) | C3040877 | estendida | [LCSC](https://www.lcsc.com/product-detail/C3040877.html) |
| P5 | 24 MHz 3225 8 pF / 32,768 kHz FC-135 | C431156 / C32346 | estendida / básica | [JLCPCB C431156](https://jlcpcb.com/partdetail/C431156) |
| E1 | HRO TYPE-C-31-M-12 | C165948 | estendida | [LCSC](https://www.lcsc.com/product-detail/C165948.html) |
| E2 | USBLC6-2SC6, SMF5.0A | C7519, C151296 | básica?, estendida | [ST](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) |
| E3 | TI BQ24074RGTR | C54313 | estendida (conferido) | [TI](https://www.ti.com/lit/ds/symlink/bq24074.pdf) |
| E4 | TI TPS63001DRCR + FNR4020S2R2MT | C28060, C167825 | estendida | [TI](https://www.ti.com/lit/ds/symlink/tps63001.pdf) |
| E5 | XC6206P332MR + 74LVC1G08 | C5446, C7666 | básica, estendida | [TI 1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf) |
| E6 | JST S3B-PH-SM4-TB | C265101 | estendida | [LCSC](https://www.lcsc.com/product-detail/Wire-To-Board-Connector_JST-S3B-PH-SM4-TB-LF-SN_C265101.html) |
| F1 | NXP SGTL5000XNLA3 + XC6206P182MR | C511764, C347373 | estendida | [SGTL5000 (PJRC)](https://www.pjrc.com/teensy/SGTL5000.pdf), [Audio Board](https://www.pjrc.com/store/teensy3_audio.html) |
| F2 | Hroparts PJ-313D-6A | C95463 | estendida | [LCSC](https://www.lcsc.com/product-detail/C95463.html) |
| I1, I2 | Alps EC11E 15/15 com chave | (achar) | estendida | [Alps EC11E](https://tech.alpsalpine.com/e/products/detail/EC11E15244G1/) |
| I3 | TOGIALED TJ-S1615SW6TGLCRG-A5 | C273605 | estendida | [LCSC](https://www.lcsc.com/product-detail/C273605.html) |
| I4 | XKB TS-1187A (5,1 × 5,1) | C318884 | básica | — |
| A1 | Analog MAX98357AETE+T | C910544 | estendida | [Analog](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf) |
| T1, T2 | Nexperia 74HC4067PW | C547038 | estendida | [Nexperia](https://assets.nexperia.com/documents/data-sheet/74HC_HCT4067.pdf) |
| T3 | 74LVC1G04 + 2 × 74LVC1G08 | C7827, C7666 | estendida | [TI](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf) |
| T4 | TI TMAG5253BA3IQDMRR | Global Sourcing | — | [TI](https://www.ti.com/lit/ds/symlink/tmag5253.pdf) |

**Custo estimado da placa montada, por unidade** (preços estimados: as páginas da LCSC/JLCPCB não
mostram preço a um script):

| Grupo | USD |
|---|---|
| Peças que a JLC monta | ~11 |
| Consignadas (P1 + P2) | ~17 |
| Global Sourcing (28 × TMAG5253) | ~12,6 |
| Não montadas | — |

Ainda faltam as taxas das peças estendidas: são 18 códigos distintos.

## Itens (conferir)

O status de cada linha está no `bom_preliminar.csv`: 38 linhas "conferir" e 46 "final". Os
principais:

1. **Códigos LCSC de passivos** marcados "conferir" (220 nF, 2,2 µF, 12/20 pF, 270/330/470 Ω,
   1,5/1,8/2,2 kΩ). Sem código: 150 nF, 680 kΩ e 2,2 MΩ (0402). Conferir no orçamento da JLCPCB.
2. **Ferrites** de 120 Ω (DCDC_IN, ≥ 1 A) e 600 Ω (VDDA) e o **indutor de 4,7 µH do DCDC do núcleo**
   (≥ 0,5 A, 0805 ou 2016): sem código.
3. **EC11E 15/15 com chave:** falta o código LCSC exato. O C255515 é o 18/36, que mudaria o
   `ENC_STEPS_PER_DETENT`.
4. **Jack PJ-313D-6A:** pinagem dos 6 terminais (ponta, anel, manga, contato da ponta). Não há
   footprint no KiCad: criar no passo 3.3.
5. **LED 1615 de 4 pads:** pinagem (qual pad é qual cor) e footprint a criar.
6. **Cristal de 32,768 kHz:** 3215 (FC-135, C32346) no lugar do 2012 da SPEC; o 2012 na LCSC sai
   mais caro e raro. **Botão Program:** 5,1 × 5,1 (TS-1187A, básico) no lugar do 4 × 4 da SPEC.
7. **Footprint do BGA-196 12 × 12 P0,8:** o KiCad não tem; criar no passo 3.2 a partir do desenho
   da NXP (figura 54).
8. **W25Q64JVSSIQ ("-Q"):** precisa do bootloader ≥ 1.09 (página da PJRC). A versão "-M"
   (W25Q64JVSSIM) serve em qualquer versão. Perguntar à PJRC a versão dos MKL02 vendidos hoje.
9. **TEST_MODE (K6), WAKEUP, PMIC_STBY_REQ, GPANAIO:** sem ligação, como no Teensy 4.1 (o esquema da
   PJRC não os liga).
10. **Consumo desligado:** LDO E5 1 µA + SNVS com RTC (~15–25 µA, datasheet) + portas (< 1 µA) +
    MAX98357A em shutdown (< 1 µA) + BQ24074 sem USB (~6 µA). Total ~25–35 µA, ou mais de 3 anos
    para descarregar 1000 mAh. O `POWER.md` fica para o passo 3.4, com os números da placa.
11. **PMIC_ON_REQ:** a fase de 1,1 V e o nível final (~VDD_SNVS_IN) vêm da página da PJRC, não de
    medida. A porta U206 resolve os dois casos, mas é a parte nova do bloco P: conferir no primeiro
    protótipo com o osciloscópio (PMIC_ON_REQ, EN_E4, 3,3 V, PSWITCH).

## Perguntas para a gestão

1. **Liga/desliga com USB.** Com a USB ligada o aparelho fica ligado mesmo com o KEEP baixo (para
   gravar a firmware). Para desligar de verdade com USB, a firmware pode pedir o desligamento do
   SNVS (baixa o PMIC_ON_REQ). O próximo clique religa pelo ONOFF, que pus no clique do seletor por
   um diodo. Isso fica como o comportamento padrão, ou basta o "desligamento leve" do Pocket?
2. **ONOFF com o clique preso ~5 s desliga tudo** (padrão do RT1062, como no Teensy 4.1). Isso fica
   como proteção contra firmware travada?
3. **Duas trocas pequenas de encapsulamento:** cristal de 32 kHz em 3215 (a SPEC diz 2012) e botão
   Program de 5,1 × 5,1 básico (a SPEC diz 4 × 4). Aceitas?
4. **Encoder:** os dois EC11E seguem 15 pulsos / 15 detentes como no Pocket, ou um 18/36 (C255515,
   em estoque na LCSC) para o volume?
5. **Flash "-Q" ou "-M":** a "-M" funciona com qualquer bootloader, mas a LCSC tem menos estoque.
   Perguntamos à PJRC a versão dos MKL02 que eles vendem hoje?
