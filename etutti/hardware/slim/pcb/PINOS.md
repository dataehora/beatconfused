# eTutti Slim · mapa de pinos (R1SL, etapa 1)

Contrato entre a eletronica e a programacao. Numeracao da Teensy 4.1 (`teensy:avr:teensy41`); o processador e o RT1062 chip-down da propria placa. Gerado por `pcb/pinos.py` a partir de `pcb/schematic.py`; conferido contra o sketch por `etutti/firmware/slim/check_pins.py`.

## Pinos usados

| Pino | Rede | Pad RT1062 | Bola | Tipo | Funcao |
|---:|---|---|---|---|---|
| 0 | CHG_STAT | GPIO_AD_B0_03 | G11 | in | ~CHG do BQ24075 (0 = carregando), pull-up 100k |
| 1 | PGOOD_N | GPIO_AD_B0_02 | M11 | in | ~PGOOD do BQ24075 (0 = USB presente) |
| 2 | SCAN_DATA_P | GPIO_EMC_04 | F2 | out | DADO do 74HC595 das 4 reguas (100 ohm em serie) |
| 3 | SCAN_CLK_P | GPIO_EMC_05 | G5 | out | CLOCK (SRCLK) das reguas |
| 4 | SCAN_LATCH_P | GPIO_EMC_06 | H5 | out | LATCH (RCLK) das reguas |
| 5 | LED_G | GPIO_EMC_08 | H3 | out PWM (ânodo comum: LIGA em nível baixo) | LED verde |
| 6 | SET | GPIO_B0_10 | D9 | out | arma o latch de energia (Q206): partida por USB com o knob ligado |
| 7 | I2S_TX | GPIO_B1_01 | B11 | I2S | SAI1 TX_DATA0 -> SGTL5000 DIN |
| 10 | KILL | GPIO_B0_00 | D7 | out | desarma o latch de energia (Q207): desligamento automatico |
| 13 | LED_R | GPIO_B0_03 | D8 | out PWM (ânodo comum: LIGA em nível baixo) | LED vermelho |
| 14 | OUT_R1 | GPIO_AD_B1_02 | L11 | ADC | saida analogica da fileira 1 (a mais baixa) |
| 15 | OUT_R2 | GPIO_AD_B1_03 | M12 | ADC | fileira 2 |
| 16 | VBAT_S | GPIO_AD_B1_07 | K10 | ADC | VBAT/2 (1M/1M) |
| 18 | I2C_SDA | GPIO_AD_B1_01 | K11 | I2C | Wire SDA (SGTL5000 0x0A) |
| 19 | I2C_SCL | GPIO_AD_B1_00 | J11 | I2C | Wire SCL |
| 20 | I2S_LRCLK | GPIO_AD_B1_10 | L13 | I2S | LRCLK |
| 21 | I2S_BCLK | GPIO_AD_B1_11 | J13 | I2S | BCLK |
| 23 | AUD_MCLK_P | GPIO_AD_B1_09 | M13 | I2S | MCLK 11,3 MHz (100 ohm em serie) |
| 25 | KNOB_N | GPIO_AD_B0_13 | L14 | in | 0 = knob de volume fora de OFF (inversor Q209, pull-up 100k no 3V3) |
| 26 | OUT_R3 | GPIO_AD_B1_14 | G12 | ADC | fileira 3 |
| 27 | OUT_R4 | GPIO_AD_B1_15 | J14 | ADC | fileira 4 (a mais alta) |

Pinos de ADC das 4 linhas OUT: 14, 15, 26, 27 (cada um pertence aos dois conversores, ADC1 e ADC2: leitura em paralelo de duas fileiras de cada vez).
Livres: 8, 9, 11, 12, 17, 22 (A8), 24 (A10) e os demais pads do RT1062 (os dois sensores de angulo estao no I2C: 18/19, enderecos 0x35 e 0x22; SGTL5000 0x0A).

## Bolas que mandam no posicionamento do BGA (12 x 12, 14 x 14, passo 0,8; colunas 1-14, linhas A-P sem I e O)

| Grupo | Bolas |
|---|---|
| USB (D+, D-) | L8 (USB_OTG1_DP), M8 (USB_OTG1_DN) |
| Flash QSPI | L3 (SD_B1_06), L4 (SD_B1_07), N4 (SD_B1_09), P3 (SD_B1_08), P4 (SD_B1_10), P5 (SD_B1_11) |
| Cristal 24 MHz e 32 kHz | P11 (XTALI), N11 (XTALO), N9 (RTC_XTALI), P9 (RTC_XTALO) |
| I2S e I2C | B11 (B1_01), K11 (AD_B1_01), J11 (AD_B1_00), L13 (AD_B1_10), J13 (AD_B1_11), M13 (AD_B1_09) |
| ADC (4 fileiras) | L11 (AD_B1_02), M12 (AD_B1_03), G12 (AD_B1_14), J14 (AD_B1_15) |
| ADC (knobs, bateria) | K10 (AD_B1_07) |
| Varredura | F2 (EMC_04), G5 (EMC_05), H5 (EMC_06) |
| Bootloader (MKL02) | F11 (AD_B0_04), E14 (AD_B0_06), F12 (AD_B0_07), F13 (AD_B0_08), F14 (AD_B0_09), G13 (AD_B0_10), G10 (AD_B0_11), F3 (EMC_01), D10 (B0_13), K3 (DCDC_PSWITCH), M7 (POR_B) |
| Energia do DCDC | M2 (DCDC_LP), L2 (DCDC_IN), K4 (DCDC_IN_Q), J5 (DCDC_SENSE), K3 (DCDC_PSWITCH) |

Lado da matriz (N = linhas A-C, S = L-P, O = colunas 1-3, L = 12-14; as letras cardeais valem para o desenho do esquema do NXP, nao para a placa; a orientacao final sai do posicionamento): USB (D+, D-): S; Flash QSPI: S/SO; Cristal 24 MHz e 32 kHz: S; I2S e I2C: L/N/SL/centro; ADC (4 fileiras): L/S/SL; ADC (knobs, bateria): centro; Varredura: O/centro; Bootloader (MKL02): L/O/S/centro; Energia do DCDC: O/SO/centro

## Notas

- ONOFF e deixado sem ligacao (a Teensy 4.1 sem botao); PMIC_ON_REQ tem 100 k para GND; o 3,3 V nao depende dele (sobe com o OUT do BQ24075).
- R2SL: DVJ6B 12 x 12 mm (decisao do J); footprint e mapa de bolas conferidos contra a SamacSys (`pcb/confere_rt1062.py`: 196/196 pads, desvio 0 mm, 0 diferencas de nome).
- Bolas SD_B1_05 (N3) e EMC_23 (G2) sem ligacao, como no Viaggio; sem PSRAM (pinos 48-54 livres).
