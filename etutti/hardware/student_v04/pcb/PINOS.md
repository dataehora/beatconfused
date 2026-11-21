# eTutti Student V4 · mapa de pinos (RASCUNHO, F2 + régua de 4 sensores)

**Atende R1V4 e R2V4 (21 nov 2026).** Dono: eletrônica. Contrato com a programação (`programacao-som` lê, não edita).
**Rascunho:** a placa da V4 ainda não existe (esquema na Fase B, depois do portão). Os números abaixo vêm do
`student_v03/pcb/schematic.py` (`TEENSY_NETS`, `MM_PADS`) com as mudanças da F2. O que ainda **não** foi conferido
no esquema da V4 está marcado **(conferir)**. Compila como `teensy:avr:teensyMM:usb=midi,speed=396`.

## O que mudou em relação à V3 (e à `viaggio_micromod/pcb/PINOS.md`)

| Mudança | Motivo |
|---|---|
| Somem MUX_S0..S3 (0-3), SENS_EN (4), MUX_R_COM/MUX_L_COM (14/15) | não há multiplexador: cada fileira tem a sua linha OUT (R2V4, E2) |
| **OUT_R1..OUT_R4 = pinos 14, 15, 26, 27** (A0, A1, A12, A13) | 1 linha analógica por fileira; todos os pinos 14-27 têm ADC1 e ADC2 |
| **SCAN_DATA = 2, SCAN_CLK = 3** | cadeia de registradores 74HC595 das réguas (DATA e CLK comuns às 4 fileiras) |
| **CHG_STAT passa do 26 para o 0** | o 26 vira OUT_R3; o 0 é digital livre (pad 19, RX1) |
| Todo o resto (6-12, 16-25, 28) | **igual à V3**: firmware existente vale sem mudar o número do pino |

## Tabela

| Pino | Pad M.2 (nome MicroMod) | Rede | Função | Sentido |
|---:|---|---|---|---|
| 0 | 19 (RX1) | CHG_STAT | ~CHG do BQ24074 (baixo = carregando), INPUT_PULLUP, só vale com USB. **Movido do 26** | entrada |
| 1 | 17 (TX1) | - | livre | - |
| **2** | 47 (PWM1) | **SCAN_DATA** | entrada serial (SER) da primeira régua de cada fileira, por 100 ohm | saída |
| **3** | 32 (PWM0) | **SCAN_CLK** | SRCLK e RCLK dos 595 (ligados juntos), por 100 ohm | saída |
| 4 | 10 (D0) | - | livre (era SENS_EN) | - |
| 5 | 18 (D1) | - | livre | - |
| 6 | 71 (G6) | SEL_SW | clique do seletor de registro, INPUT_PULLUP | entrada |
| 7 | 56 (AUD_OUT) | I2S_TX | I2S para SGTL5000 e MAX98357A | - |
| 8 | 54 (AUD_IN) | I2S_RX | I2S do codec (microfone IN) | - |
| 9 | 69 (G7) | SEL_B | seletor B | entrada |
| 10 | 55 (SPI_CS#) | KEEP | segura o 3,3 V | saída |
| 11 | 59 (SPI_SDO) | SEL_A | seletor A | entrada |
| 12 | 61 (SPI_SDI) | AMP_SD | liga o MAX98357A | saída |
| 13 | 57 (SPI_SCK) | - | livre (também acende o LED azul do módulo) | - |
| **14 (A0)** | 34 (A0) | **OUT_R1** | linha analógica da **fileira 1** (a da frente) | ADC |
| **15 (A1)** | 38 (A1) | **OUT_R2** | fileira 2 | ADC |
| 16 (A2) | 20 (RX2) | VBAT_S | bateria, divisor 1:2 | ADC |
| 17 (A3) | 22 (TX2) | HP_DET | fone plugado | ADC |
| 18 | 12 (I2C_SDA) | I2C_SDA | SGTL5000 e tela OLED (J401), 2,2 kohm | - |
| 19 | 14 (I2C_SCL) | I2C_SCL | idem | - |
| 20 | 52 (AUD_LRCLK) | I2S_LRCLK | | - |
| 21 | 50 (AUD_BCLK) | I2S_BCLK | | - |
| 22 (A8) | 49 | VOL_A | volume A | entrada |
| 23 | 58 (AUD_MCLK) | AUD_MCLK_P | MCLK, 100 ohm junto do J101 | - |
| 24 (A10) | 53 | VOL_B | volume B | entrada |
| 25 (A11) | 51 | VOL_SW | clique do volume (liga/desliga) | entrada |
| **26 (A12)** | 67 (G8) | **OUT_R3** | fileira 3 | ADC |
| **27 (A13)** | 8 (G11) | **OUT_R4** | fileira 4 (a de trás) | ADC |
| 28 | 4 (3.3V_EN) | NC | sem uso (a cadeia PWR_EN da V1 não existe na V3/V4) | - |
| 29-45 | 16, 41, 43, 65, 63, 66, 64, 60, 62, 70, 68, 40, 42, 44, 46, 48, 73 | - | livres. **(conferir)** 38, 39, 40, 41 (pads 70, 68, 40, 42) têm ADC no Teensy 4.1; se valerem no MicroMod, servem de **OUT_B** (2ª linha por fileira) | - |

Resumo de uso: 27 sinais (0, 2, 3, 6-12, 14-28 menos 13) e, nos pads que não são pinos, ONOFF (6), PROGRAM (11), USB, 3,3 V.
Livres: 1, 4, 5, 13 e 29-45. **Para 76 teclas não faltam pinos.**

## A varredura (R2V4, E2): o contrato de tempo e de ordem

**Barramento da régua** (conector de 6 vias, igual nas duas pontas): 1 +3V3 · 2 GND · 3 OUT · 4 CLK · 5 DATA · 6 reservado
(OUT_B). Na ponta de entrada o pino 5 é o SER do 595; na ponta de saída é o QH' (cascata). VCC, GND, OUT e CLK passam direto.
Na placa principal há **4 conectores, um por fileira**: OUT_Rk próprio, SCAN_CLK e SCAN_DATA **comuns às 4**.

**Registrador:** 74HC595, SRCLK e RCLK juntos (uma linha CLK), SRCLR em 3,3 V, OE em GND. Efeitos que a firmware tem de saber:
1. a saída travada **atrasa um pulso** em relação ao deslocamento (a saída mostra o estado anterior ao pulso);
2. cada régua tem **8 estágios** (cascata pelo QH'), mas só QA..QD ligam sensores: o "1" que anda passa por **4 estágios mortos**
   (todas as colunas desligadas) entre uma régua e a seguinte;
3. as saídas **não são Hi-Z na partida**: ao ligar, dar 8 x N pulsos de CLK com DATA = 0 antes de ler (zera a cadeia).

**Coluna global c (0..C-1)** = régua c/4, sensor c%4 (QA..QD), igual nas 4 fileiras. 28 teclas: C = 8 (2 réguas por fileira);
44: 12; 60: 16; 76: 20. Com N réguas por fileira, a cadeia tem 8 N estágios.
- **Varredura em ordem:** com DATA = 1 no primeiro pulso e 0 nos outros, o "1" anda 1 estágio por pulso. Colunas 0..3 aparecem
  nos pulsos 1..4 (mais o atraso de 1), as colunas 4..7 do pulso 9 ao 12, e assim por diante (**passo 8 por régua**).
- **Acesso aleatório** (varredura rápida da tecla "quente"): empurrar o padrão de 8 N bits (o primeiro bit enviado vai para a
  última régua) e dar **1 pulso a mais**. 20 colunas = 160 pulsos = ~30 us a 5 MHz. Bit k (0 = primeiro) = estágio 8N-1-k.
- Velocidade do CLK: **até 5 MHz** (meio período >= 100 ns; HC595 a 3,3 V). Usar `digitalWriteFast`.

**Tempo por coluna** (E2, datasheet do TMAG5253, variante BA3 bipolar): ligar leva **20 us típico, 45 us MÁXIMO** (até 95 % do
valor final); a firmware espera **t_espera = 60 us** (valor da V3) no modo normal e **90 us** se a leitura precisar de 12 bits
limpos. Depois lê as 4 linhas (A0, A1, A12, A13) com ADC1 e ADC2 em paralelo, ~6 us. Passo = 70 us (ou 100 us).

| Teclas | Colunas | Varredura completa (70 us/passo) | (100 us/passo) |
|---:|---:|---:|---:|
| 28 | 8 | 0,56 ms | 0,80 ms |
| 44 | 12 | 0,84 ms | 1,20 ms |
| 60 | 16 | 1,12 ms | 1,60 ms |
| 76 | 20 | 1,40 ms | 2,00 ms |

(a V3 com multiplexadores varre 28 teclas em ~0,25 ms, **estimativa** (2 esperas de 60 us + 14 canais por metade): a F2 é ~2 vezes mais lenta na varredura em ordem.)
**Velocity:** com 1 ms = 127, a quantização de 0,56 ms (28) ou 1,4 ms (76) é grossa. A firmware deve (a) **interpolar** o instante
em que cada limiar é cruzado entre duas varreduras, e (b) fazer **varredura rápida da coluna quente**: ao sair do repouso, ler só
a coluna da tecla (padrão por acesso aleatório + 60 us + leitura = ~70 us, ~14 kHz). Sem isso, 76 teclas não resolvem 1 ms.

**Calibração:** repouso por tecla medido na partida (1,65 V típico em BA3 com 3,3 V; 1,61-1,69 V pelo datasheet).
Erro por assentamento: coluna lida 60 us depois do EN tem resíduo de ~1,8 % da diferença para a coluna anterior (tau efetivo ~15 us,
estimado a partir do "95 % em 45 us"); com 90 us o resíduo cai para ~0,25 %. **(conferir na primeira placa; é cálculo.)**

## Cadeia de energia e demais sinais

Iguais à V3 / `viaggio_micromod/pcb/PINOS.md` ("Como cada sinal de energia se comporta"): liga pelo clique do volume (2 s) ou
pelo USB (D206); KEEP no 10; AMP_SD no 12; HP_DET no 17; CHG_STAT agora no **0**.

## Pendências desta tabela

- **KEY_INPUT** deixa de existir: a tecla é (fileira, coluna). Mapa de notas na tabela abaixo (igual à V3):
  `FIRST_NOTE = {57, 55, 56, 57}`, `FIRST_COL = {1, 0, 1, 1}`, 3 semitons por coluna; teclas por fileira 7, 8, 7, 6.
  28 teclas: colunas 0..7 (as 4 posições sem tecla: fileira 1 col 0, fileira 3 col 0, fileira 4 col 0 e col 7).
  44: colunas 0..11 (11/12/11/10 teclas); 60: 16; 76: 20 (19/20/19/18). Ordem dos módulos e transposição: do firmware (R1V4, §4.4).
- Os pinos 14, 15, 26, 27 como entradas analógicas de OUT: **sem pull** interno; o pull-down de 100 kohm por linha está na placa principal.
- Pinos 38-41 como segundo conjunto de OUT: **(conferir)** no esquema da SparkFun antes de depender deles.
