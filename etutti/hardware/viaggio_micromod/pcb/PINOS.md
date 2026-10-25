# eTutti Viaggio MicroMod · mapa de pinos (numeração Teensy MicroMod)

**SPEC v2.2, passo M1, 25 out 2026.** Dono: eletrônica. É o contrato com a programação.

O processador é o módulo **SparkFun MicroMod Teensy** (DEV-16402) no conector M.2 J101. A firmware
compila como **`teensy:avr:teensyMM`** ("Teensy MicroMod" no Teensyduino; conferido com
`arduino-cli board listall teensy`, Teensyduino 1.62 instalado no PC do J) e usa os números de pino do
Teensy MicroMod.

A coluna "pad" é o pad do conector M.2. A ligação pad → bola do RT1062 → pino foi lida rede por rede
no esquema da SparkFun (`Hardware/MicroMod-Teensy.sch` do repositório
`sparkfun/MicroMod_Teensy_Processor`). As 67 linhas foram conferidas por script contra a tabela
`MM_PADS` do `pcb/schematic.py`, sem diferença. Fonte única: o esquema gerado por `pcb/schematic.py`
(rótulos globais com os nomes da coluna "rede").

**Os números de pino não mudaram em relação ao Viaggio v2.1.** Os pinos 0–26 do Teensy MicroMod estão
nas mesmas bolas do RT1062 que no Teensy 4.1, e todos saem no conector. O único pino novo é o **28**
(pad 4, 3.3V_EN = PWR_EN).

Os canais dos multiplexadores (`KEY_INPUT`) ainda são os do Pocket v0.3. A placa roteada (M3) os
reescreve e confere 28/28.

## Tabela

| Pino | Pad M.2 (nome MicroMod) | Bola RT1062 | Rede | Função | Sentido |
|---:|---|---|---|---|---|
| 0 | 19 (RX1) | AD_B0_03 | MUX_S0 | endereço dos 2 multiplexadores | saída |
| 1 | 17 (TX1) | AD_B0_02 | MUX_S1 | | saída |
| 2 | 47 (PWM1) | EMC_04 | MUX_S2 | | saída |
| 3 | 32 (PWM0) | EMC_05 | MUX_S3 | também escolhe o grupo: S3 = 0 liga os canais 0–7 (EN_A), S3 = 1 os canais 8–15 (EN_B) | saída |
| 4 | 10 (D0) | EMC_06 | SENS_EN | liga os sensores (alto = ligados) | saída |
| 5 | 18 (D1) | EMC_08 | LED_G | verde do I3, por 330 Ω | saída |
| 6 | 71 (G6) | B0_10 | SEL_SW | clique do **seletor** (I2), direto; INPUT_PULLUP. Só funções de som | entrada |
| 7 | 56 (AUD_OUT) | B1_01 | I2S_TX | I2S OUT1A → SGTL5000 e MAX98357A | — |
| 8 | 54 (AUD_IN) | B1_00 | — | livre | — |
| 9 | 69 (G7) | B0_11 | SEL_B | seletor B, INPUT_PULLUP, interrupção | entrada |
| 10 | 55 (SPI_CS#) | B0_00 | KEEP | segura o 3,3 V ligado (alto); 100 kΩ para o GND | saída |
| 11 | 59 (SPI_SDO) | B0_02 | SEL_A | seletor A, INPUT_PULLUP, interrupção | entrada |
| 12 | 61 (SPI_SDI) | B0_01 | AMP_SD | liga o MAX98357A (alto); 680 kΩ até o SD_MODE | saída |
| 13 | 57 (SPI_SCK) | B0_03 | LED_R | vermelho do I3, por 270 Ω e um diodo. **Acende também o LED azul do módulo** (1 kΩ, ~1,3 mA) | saída |
| 14 (A0) | 34 (A0) | AD_B1_02 | MUX_R_COM | COM do T2 (metade direita, notas altas) | ADC, INPUT_PULLDOWN |
| 15 (A1) | 38 (A1) | AD_B1_03 | MUX_L_COM | COM do T1 (metade esquerda, notas baixas) | ADC, INPUT_PULLDOWN |
| 16 (A2) | 20 (RX2) | AD_B1_07 | VBAT_S | bateria: 1 MΩ / 1 MΩ + 100 nF, V(pino) = VBAT / 2 | ADC |
| 17 (A3) | 22 (TX2) | AD_B1_06 | HP_DET | fone plugado ≈ 0 V; sem fone ≈ 1,4 V | ADC |
| 18 | 12 (I2C_SDA) | AD_B1_01 | I2C_SDA | SGTL5000 (2,2 kΩ) | — |
| 19 | 14 (I2C_SCL) | AD_B1_00 | I2C_SCL | SGTL5000 (2,2 kΩ) | — |
| 20 | 52 (AUD_LRCLK) | AD_B1_10 | I2S_LRCLK | I2S LRCLK1 | — |
| 21 | 50 (AUD_BCLK) | AD_B1_11 | I2S_BCLK | I2S BCLK1 | — |
| 22 (A8) | 49 (BATT_VIN/3) | AD_B1_08 | VOL_A | **volume** A, INPUT_PULLUP, interrupção. No Teensy o pad 49 é só o pino 22: não há divisor no módulo | entrada |
| 23 | 58 (AUD_MCLK) | AD_B1_09 | AUD_MCLK_P | I2S MCLK1, por 100 Ω junto do J101 | — |
| 24 (A10) | 53 (I2C_SCL1) | AD_B0_12 | VOL_B | volume B, INPUT_PULLUP, interrupção | entrada |
| 25 (A11) | 51 (I2C_SDA1) | AD_B0_13 | VOL_SW | clique do **volume** (I1), por um diodo (D205, ~0,2 V apertado); INPUT_PULLUP. **Liga/desliga** (2 s) | entrada |
| 26 (A12) | 67 (G8) | AD_B1_14 | CHG_STAT | ~CHG do BQ24074 por um diodo, INPUT_PULLUP: baixo = carregando. **Só vale com USB** | entrada |
| 27 (A13) | 8 (G11) | AD_B1_15 | — | livre | — |
| **28** | **4 (3.3V_EN)** | EMC_32 | **PWR_EN** | **novo.** Pull-up de 100 kΩ na placa (R218): solto = ligado. **Baixo = desligar com USB** (ver abaixo) | saída |
| 29–45 | 16, 41, 43, 65, 63, 66, 64, 60, 62, 70, 68, 40, 42, 44, 46, 48, 73 | — | — | livres (não ligados) | — |
| — | 6 (RESET#) | ONOFF | ONOFF | **no Teensy MicroMod é o ONOFF do RT1062**, não um reset. Ligado ao clique do volume (D205) e ao pad de teste TP101 | — |
| — | 11 (BOOT#) | MKL02 PTB2 (PROGRAM) | PROG | botão Program (I4) | — |
| — | 3, 5 (USB_D±) | USB1 | USB_DP/DN | USB-C (E1) pelo U201 | — |
| — | 9 (USB_VIN) | USB1_VBUS | VBUS | o módulo vê a USB | — |
| — | 2, 74 (3.3V) | — | +3V3 | do TPS63001 (E4) | — |
| — | 72 (RTC_3V) | VDD_SNVS_IN (diodo) | — | sem ligação (sem pilha do relógio) | — |
| — | 35, 37 (USBHOST_D±) | USB2 | — | sem ligação | — |
| — | 13, 15, 21, 23 | — | — | não ligados no módulo Teensy | — |

## Conferência: todos os sinais cabem nos pinos do módulo

O Teensy MicroMod expõe os pinos 0–45 no conector (46 pinos). O Viaggio usa 27 (0–7, 9–26 e 28),
mais ONOFF, PROGRAM, USB e alimentação. Sobram livres o 8, o 27 e o 29–45.

| Pedido da SPEC §7 (M1) | Pinos | Cabe? |
|---|---|---|
| I2S 7/20/21/23 e I2C 18/19 | os mesmos | sim (pads AUD_* e I2C_* do MicroMod) |
| Saídas dos mux em entradas analógicas | 14 (A0), 15 (A1) | sim (pads A0/A1, os analógicos do MicroMod) |
| 2 encoders com clique | 22/24/25 (volume), 11/9/6 (seletor) | sim; todo pino do Teensy 4 aceita interrupção |
| LED R/G | 13, 5 | sim |
| KEEP, AMP_SD | 10, 12 | sim |
| CHG_STAT | 26 | sim |
| VBAT_S (analógica) | 16 (A2) | sim |
| HP_DET | 17 (A3) | sim (analógica, como no v2.1) |
| SENS_EN, S0–S3 | 4, 0–3 | sim |

## Diferença em relação ao `viaggio/pcb/PINOS.md` (v2.1)

| Item | Viaggio v2.1 (Teensy 4.1 na placa) | Viaggio MicroMod |
|---|---|---|
| Placa no Teensyduino | `teensy:avr:teensy41` | **`teensy:avr:teensyMM`** |
| Pinos 0–26 | rede e função da tabela | **iguais** (mesmo número, mesma bola) |
| Pino 13 | só o LED vermelho do I3 | também o **LED azul do módulo** (não há como cortar sem mexer no módulo) |
| Pino 28 | livre | **PWR_EN** (pad 3.3V_EN) |
| Desligar com USB | desligamento do SNVS (`SNVS_LPCR` TOP + DP_EN), que baixava o PMIC_ON_REQ e cortava o E4 pela porta U206 | **baixar o pino 28** (e o KEEP). O PMIC_ON_REQ não sai no conector |
| `BTN_PRESS_TIME` = 10 s | sim | **sim, mantido**: o ONOFF sai no pad 6 |
| LDO do SNVS (E5) | sempre ligado | **não existe**: desligado, o SNVS fica sem energia (perde o relógio, que não usamos) |
| Pinos 48–54 (PSRAM) | reservados | não existem no MicroMod (o módulo não tem PSRAM; 16 MB de flash) |
| LED vermelho do MKL02 | no verso da placa | é o LED amarelo do módulo |

## Como cada sinal de energia se comporta

- **Ligar (clique do volume, 2 s), sem USB.** O clique de I1 fecha o VOL_SW_N no GND, liga o Q203, e
  o VSYS chega ao EN_REQ (D203), que é o EN do TPS63001. O 3,3 V sobe, o SNVS do módulo parte do zero
  (PMIC_ON_REQ alto por padrão) e o módulo parte. Na `startup_early_hook`:
  `pinMode(10, OUTPUT); digitalWrite(10, LOW)`. Se o pino 25 continuar baixo até 2 s desde a
  partida, subir o KEEP (10), mostrar no LED e ficar ligado. Se o clique for solto antes, deixar o
  KEEP baixo: tudo desliga ao soltar.
- **Não mexer no pino 28 na partida** (deixar como entrada, sem pull-down interno). O pull-up da
  placa o mantém alto.
- **Ligar com USB.** Com o 3,3 V ligado e o PWR_EN alto, o U203 segura o EN (USB_HOLD) depois de
  ~0,1–0,2 s (R218 × C213). Por isso, com USB, um clique curto já deixa a placa ligada: se o clique
  for solto antes de 2 s, a firmware deve **desligar como abaixo** (pino 28 baixo).
- **Desligar sem USB:** silenciar, gravar o que precisar, mostrar no LED, baixar o KEEP. Desliga
  quando o clique é solto.
- **Desligar com USB:** o mesmo, e também `pinMode(28, OUTPUT); digitalWrite(28, LOW)` e ficar
  assim. O USB_HOLD cai, o E4 desliga quando o clique é solto, e o módulo, o codec e os sensores
  ficam sem energia. Só o BQ24074 continua a carregar, e a luz de carga aparece. O C213 segura o
  PWR_EN_S baixo enquanto o 3,3 V cai, então a placa não religa sozinha.
- **Gravar a firmware:** com o aparelho ligado e USB. O bootloader reinicia o RT1062: o KEEP cai,
  mas o pino 28 fica solto (alto pelo R218) e o USB_HOLD mantém tudo ligado.
- **Recuperação de firmware ruim:** com USB, segurar o clique do volume (liga o 3,3 V) e apertar o
  Program (I4). O módulo entra no bootloader e a USB mantém a placa ligada depois de soltar o clique.
- **Proteção do botão preso / firmware travada:** o clique também chega ao **ONOFF** (pad 6) pelo
  D205. Na partida a firmware grava 10 s no `BTN_PRESS_TIME` do `SNVS_LPCR`, como no v2.1. Com o
  clique preso 10 s, o SNVS desliga o RT1062 (o próprio módulo corta o seu 3,3 V interno pelo
  PMIC_ON_REQ). Sem USB, a placa toda apaga ao soltar o clique. Com USB, a placa fica alimentada com
  o módulo parado. O próximo clique o religa pelo ONOFF. Além disso, a firmware deve usar o
  **watchdog** (WDOG1/RTWDOG) para travamentos sem clique.
- **SEL_SW (6) e VOL_SW (25):** INPUT_PULLUP. O do volume lê ~0,2 V apertado (queda do BAT54C).
- **CHG_STAT (26):** baixo = carregando, alto = carga completa ou sem bateria. Sem USB o pino fica
  indefinido; a firmware só o lê com o VBUS presente (USB1).
- **AMP_SD (12):** alto = ligado, mono (L+R)/2 pelo resistor de 680 kΩ; baixo = desligado. Como no
  v2.1.
- **Sensores:** iguais ao Pocket (TMAG5253BA3, 1,65 V em repouso, 45 µs depois de trocar o S3).
