# eTutti Viaggio · mapa de pinos (numeração Teensy 4.1)

**SPEC v2.1, passo 3.2, 24 out 2026** (3.1: SPEC v2). Dono: eletrônica. É o contrato com a programação. A placa tem o
"Teensy 4.1 na placa", então a firmware compila como `teensy:avr:teensy41` e usa os números de pino
do Teensy 4.1. A coluna "pad" diz a bola do RT1062 (LFBGA-196 12 × 12) e o nome do pad, tirados do
esquema público da PJRC e conferidos com a tabela 87 do datasheet da NXP
(`pcb/rt1062_balls.json`). Fonte única: o esquema gerado por `pcb/schematic.py`
(rótulos globais com os nomes da coluna "rede").

Os canais dos multiplexadores (`KEY_INPUT`) por enquanto são os do Pocket v0.3. A placa roteada do
passo 3.4 vai reescrevê-los e conferi-los 28/28, como no Pocket.

## Tabela

| Pino T4.1 | Pad (bola) | Rede | Função | Sentido | Pocket (T4.0) |
|---:|---|---|---|---|---|
| 0 | AD_B0_03 (G11) | MUX_S0 | endereço dos 2 multiplexadores | saída | igual |
| 1 | AD_B0_02 (M11) | MUX_S1 | | saída | igual |
| 2 | EMC_04 (F2) | MUX_S2 | | saída | igual |
| 3 | EMC_05 (G5) | MUX_S3 | também escolhe o grupo: S3 = 0 liga os canais 0–7 (EN_A), S3 = 1 os canais 8–15 (EN_B) | saída | igual |
| 4 | EMC_06 (H5) | SENS_EN | liga os sensores (alto = ligados) | saída | igual |
| 5 | EMC_08 (H3) | LED_G | verde do I3, por 330 Ω | saída | igual |
| 6 | B0_10 (D9) | SEL_SW | clique do **seletor** (I2), ligado direto; INPUT_PULLUP, chave para o GND. Só funções de som | entrada | igual (era ENC_SW) |
| 7 | B1_01 (B11) | I2S_TX | I2S OUT1A → SGTL5000 e MAX98357A | — | igual |
| 8 | B1_00 (A11) | — | livre (I2S IN1; o Viaggio não tem entrada de áudio) | — | era reservado |
| 9 | B0_11 (A10) | SEL_B | seletor B, INPUT_PULLUP, interrupção | entrada | igual (era ENC_B) |
| 10 | B0_00 (D7) | KEEP | segura o 3,3 V ligado (alto); 100 kΩ para o GND | saída | igual |
| 11 | B0_02 (E8) | SEL_A | seletor A, INPUT_PULLUP, interrupção | entrada | igual (era ENC_A) |
| 12 | B0_01 (E7) | AMP_SD | liga o MAX98357A (alto); 680 kΩ até o SD_MODE | saída | igual, outro amplificador |
| 13 | B0_03 (D8) | LED_R | vermelho do I3, por 270 Ω e um diodo | saída | igual |
| 14 (A0) | AD_B1_02 (L11) | MUX_R_COM | COM do T2 (metade direita, notas altas) | ADC, INPUT_PULLDOWN | igual |
| 15 (A1) | AD_B1_03 (M12) | MUX_L_COM | COM do T1 (metade esquerda, notas baixas) | ADC, INPUT_PULLDOWN | igual |
| 16 (A2) | AD_B1_07 (K10) | VBAT_S | bateria: 1 MΩ / 1 MΩ + 100 nF, V(pino) = VBAT / 2 | ADC | igual |
| 17 (A3) | AD_B1_06 (J12) | HP_DET | fone plugado ≈ 0 V; sem fone ≈ 1,4 V | ADC | igual |
| 18 | AD_B1_01 (K11) | I2C_SDA | SGTL5000 (2,2 kΩ) | — | igual |
| 19 | AD_B1_00 (J11) | I2C_SCL | SGTL5000 (2,2 kΩ) | — | igual |
| 20 | AD_B1_10 (L13) | I2S_LRCLK | I2S LRCLK1 | — | igual |
| 21 | AD_B1_11 (J13) | I2S_BCLK | I2S BCLK1 | — | igual |
| 22 (A8) | AD_B1_08 (H13) | VOL_A | **volume** A, INPUT_PULLUP, interrupção | entrada | **mudou** (era POT) |
| 23 | AD_B1_09 (M13) | AUD_MCLK_P | I2S MCLK1, por 100 Ω junto do P1 | — | igual |
| 24 (A10) | AD_B0_12 (K14) | VOL_B | volume B, INPUT_PULLUP, interrupção | entrada | **novo** |
| 25 (A11) | AD_B0_13 (L14) | VOL_SW | clique do **volume** (I1), por um diodo (D205, ~0,2 V apertado); INPUT_PULLUP. **Liga/desliga** (2 s) | entrada | **novo** |
| 26 (A12) | AD_B1_14 (G12) | CHG_STAT | ~CHG do BQ24074 por um diodo, INPUT_PULLUP: baixo = carregando. **Só vale com USB** | entrada | **novo** |
| 27–41 | — | — | livres (não ligados) | — | — |
| 42–47 | SD_B0_xx | — | sem cartão SD: não ligados | — | — |
| 48–54 | EMC_22..29 | PSRAM_* | reservados para a PSRAM P4 (não montada). EMC_22 (pino 51, 2ª flash do Teensy 4.1) e EMC_23 (G2) sem ligação | — | — |

Ligações que não são pinos do Teensy (como no Teensy 4.1): JTAG/boot do MKL02 (AD_B0_04, 06–11,
EMC_01, B0_13, POR_B, DCDC_PSWITCH), flash em SD_B1_06–11, AD_B0_05 no GND, USB1 D+/D− no USB-C
(E1/E2), PMIC_ON_REQ para a porta U206 e ONOFF para o clique do volume (por diodo).

## Como cada sinal novo se comporta

- **Liga/desliga (clique do volume, 2 s; SPEC v2.1).** O clique de I1 fecha o VOL_SW_N no GND. Isso
  liga o Q203, que leva o VSYS ao EN_REQ (diodo D203). O EN do TPS63001 é `PMIC_ON_REQ E EN_REQ` (U206,
  alimentada pelo LDO sempre ligado E5). O mesmo clique chega ao pino 25 e ao ONOFF do SNVS pelos dois
  anodos do D205.
  - **Ligar:** com o clique apertado o 3,3 V sobe, o MKL02 solta o PSWITCH e a firmware parte. Na
    `startup_early_hook`: `pinMode(10, OUTPUT); digitalWrite(10, LOW)`. Se o pino 25 continuar baixo
    até 2 s desde a partida, subir o KEEP (10), mostrar no LED e ficar ligado. Se o clique for solto
    antes, deixar o KEEP baixo: tudo desliga ao soltar.
  - **Desligar:** clique de 2 s com o aparelho ligado. Silenciar, gravar o que precisar, mostrar no
    LED e baixar o KEEP. Desliga quando o clique é solto. (O aviso sonoro dos dois casos vem depois,
    na programação.)
  - **Desligar com USB ligada = desligamento do SNVS.** Com USB, o U203 mantém o EN alto enquanto o
    3,3 V estiver ligado (é o que deixa gravar a firmware: o bootloader solta o pino 10), então baixar
    o KEEP não basta. A firmware pede o desligamento do SNVS (`SNVS_LPCR`, bit TOP, com o DP_EN),
    que baixa o PMIC_ON_REQ e corta o EN de E4. O próximo clique de 2 s religa pelo ONOFF. Assim a
    luz de carga (só com o aparelho desligado) também aparece com USB.
  - **`BTN_PRESS_TIME` = 10 s:** na partida a firmware grava 10 s no campo `BTN_PRESS_TIME` do
    `SNVS_LPCR`. ONOFF preso 10 s desliga tudo (proteção contra firmware travada; o padrão do RT1062
    é 5 s).
  - **Recuperação de firmware ruim:** com USB ligada, segurar o clique do volume (liga o 3,3 V) e
    apertar o Program (I4). Ao soltar o clique, a USB mantém a placa ligada no bootloader.
  - Desligado, só ficam o LDO E5, o SNVS e a porta U206 (~10–25 µA, conferir).
- **SEL_SW (6) e VOL_SW (25):** os dois usam INPUT_PULLUP. O do volume lê ~0,2 V apertado (queda
  do BAT54C), que ainda é nível baixo; o do seletor vai direto à chave.
- **CHG_STAT (26):** baixo = carregando, alto = carga completa ou sem bateria. Sem USB o pino fica
  indefinido (~2,3 V); a firmware só o lê quando vê o VBUS (USB1, `USB1_OTGSC`).
- **AMP_SD (12):** alto = ligado. O resistor de 680 kΩ e os 100 kΩ internos do MAX98357A dão
  0,42 V no SD_MODE, o que escolhe o modo mono (L+R)/2. Baixo (ou o pino solto) = desligado. Usar
  como no Pocket: só sem fone, com som, e desligar ~2 s depois do silêncio.
- **Sensores:** iguais ao Pocket (TMAG5253BA3, 1,65 V em repouso, 45 µs depois de trocar o S3).
- **MCLK:** o mesmo pino 23. O resistor de 100 Ω fica na placa, junto do P1.

## Diferenças em relação ao Pocket (o que a programação muda)

1. Placa: `teensy:avr:teensy41` (era `teensy40`). Os pinos 0–21 e 23 têm a mesma função do Pocket.
2. **Volume = encoder:** `VOL_A_PIN = 22`, `VOL_B_PIN = 24`, `VOL_SW_PIN = 25`. Sai o POT (22) e a
   detecção de potenciômetro na partida. Mesma tabela de Gray. **Encoder: EC11E18244A5 (18 pulsos /
   36 detentes, LCSC C255515), o mesmo nos dois**: `ENC_STEPS_PER_DETENT = 2` (o 15/15 do Pocket
   não tem estoque na LCSC).
3. **Seletor:** mesmos pinos (A = 11, B = 9, clique = 6); o clique é só para as funções de som.
   **O liga/desliga é o clique do volume (pino 25, 2 s, ver acima)**; no Pocket era a chave do
   potenciômetro.
4. **Novo:** `CHG_STAT_PIN = 26` (o Pocket não tinha pino para o carregador).
5. **Amplificador:** MAX98357A digital (I2S, mesmo pino 7 do codec) em vez do PAM8302A analógico.
   AMP_SD continua no 12 com a mesma lógica. A firmware precisa mandar o áudio ao I2S com as duas
   saídas: o amplificador mistura L+R.
6. **KEEP (10):** mesmo pino e mesma polaridade. Muda a partida: com o clique do volume solto antes
   de 2 s, a firmware não sobe o KEEP. Novo: desligamento do SNVS com USB e `BTN_PRESS_TIME` = 10 s.
7. **LED:** mesmos pinos (13 vermelho, 5 verde) e mesma luz de carga só com o aparelho desligado.
   Some o LED laranja do Teensy no 13; fica um LED vermelho do MKL02 no verso, que é só do
   bootloader.
8. Pino 8 livre (era I2S IN1, reservado pela Audio Board).
