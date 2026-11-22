# eTutti Student V4 · mapa de pinos (FINAL da placa principal, R3V4; teclado de 32 teclas, R5V4; microfone R6V4)

## R6V4: o que mudou para a programação (dois pinos trocam de função)

- **VOL_SW passa do pino 25 para o pino 4** (clique do volume, a mesma lógica: o clique de 2 s liga/desliga pelo hardware; a firmware só lê). O pino 25 (A11) virou **MIC_DET**, entrada analógica.
- **Detecção do microfone em J302 (IN)** (detalhe na seção "Microfone"): `analogRead(25)` com o **MIC_BIAS ligado** (3,0 V, `BIAS_RESISTOR` 2 k); leitura em volts `v = analogRead(25) * 3.3 / 1023` (10 bits) ou 4095 (12 bits):
  - **v >= 2,85 V:** nada ligado, ou plugue de linha com acoplamento por capacitor (sem corrente CC) → **efeitos de voz desligados / escondidos**;
  - **0,30 V < v < 2,85 V:** carga CC de microfone de eletreto → **efeitos de voz disponíveis**;
  - **v <= 0,30 V:** curto ou fonte com resistência CC baixa (microfone dinâmico, saída de linha ligada em CC) → tratar como "sem microfone de eletreto" (não liga os efeitos);
  - filtre com 8 leituras e histerese de 0,1 V; o RC é de 10 ms. Com o bias desligado a leitura é 0 V e não vale.
- Pino 25 deixa de servir de entrada digital; nada mais mudou. **Contagem de pinos usados: 28.**
- Mapa de notas e tamanhos: **32 / 48 / 64 / 80 teclas** (R5V4); conectores da principal J601..J604 sem mudança na recomendada da R6V4 (o plugue SH-6 da principal continua; o que muda é a régua, ver `POSICIONAMENTO.md`, parte 4).

## R5V4: o que mudou para a programação (os pinos NÃO mudam)

O teclado passa a **32 / 48 / 64 / 80 teclas, réguas sempre cheias** (4 sensores ocupados em toda régua, nenhuma posição sem tecla). Nenhum pino,
nenhuma rede e nenhuma temporização muda; muda só o **mapa de notas**:

| Fileira | Teclas (32) | `FIRST_NOTE` | Notas (3 semitons por coluna, colunas 0..7) |
|---|---:|---:|---|
| 1 (frente) | 8 | **57** (A3) | A3 C4 D#4 F#4 A4 C5 D#5 **F#5** |
| 2 | 8 | **55** (G3) | G3 A#3 C#4 E4 G4 A#4 C#5 E5 |
| 3 | 8 | **56** (G#3) | G#3 B3 D4 **F4** G#4 B4 D5 **F5** |
| 4 (trás) | 8 | **54** (F#3; era 57) | **F#3** A3 C4 D#4 F#4 A4 C5 **D#5** |

- `FIRST_NOTE = {57, 55, 56, 54}` (o da fileira 4 era 57), `FIRST_COL = {0, 0, 0, 0}` como antes; **8 teclas em todas as fileiras** (antes 7, 8, 7, 6).
- Colunas globais: 32 teclas = 8 colunas (2 réguas por fileira); 48 = 12; 64 = 16; 80 = 20, **todas ocupadas nas 4 fileiras**: `V4_KEYS` = 32 / 48 / 64 / 80
  (4 x 8, 4 x 12, 4 x 16, 4 x 20). Para a fileira 4, a régua começa em x 79,95 (alinhada com a fileira 2, antes 89,2).
- Pulsos do acesso aleatório = 8 x N + 1 (N = réguas por fileira): **17 / 25 / 33 / 41** (32 / 48 / 64 / 80 teclas; o número de réguas por fileira, 2 / 3 / 4 / 5, é o que conta).
  A varredura completa em ordem (colunas 8/12/16/20, 70 us/passo) também é a mesma: 0,56 / 0,84 / 1,12 / 1,40 ms.
- **Cadeia de registradores:** nada a ajustar. Cada régua continua com 8 estágios (QA..QD = sensores 1..4, QE..QH mortos), e agora os 4 sensores de
  toda régua são notas de verdade: o "1" que anda passa pelos mesmos 4 estágios mortos entre uma régua e a seguinte. A ligação física das réguas (R5V4, item 3)
  não altera o protocolo: continuam 5 condutores (+3V3, GND, OUT, CLK, DATA/QH').

**Atende R3V4 (21 nov 2026) e R5V4 (teclado de 32).** Dono: eletrônica. Contrato com a programação (`programacao-som` lê, não edita).
Conferido contra o esquema da V4 (`pcb/schematic.py`, ERC 0/0, netlist = `TEENSY_NETS`/`MM_PADS`) e o posicionamento
(`pcb/posiciona_v4.py`, paridade placa × esquema 0). Compila como `teensy:avr:teensyMM:usb=midi,speed=396`.
**Um só contrato com o `FIRMWARE.md`:** onde os dois diziam coisas diferentes, vale este arquivo (lista em "Correções da R3V4").

## Correções da R3V4 (o que a programação ajusta)

1. **Pulsos do acesso aleatório = 8 x N + 1 por fileira** (N = réguas por fileira; as 4 fileiras andam em paralelo, DATA/CLK comuns).
   32 teclas: 17; 48: 25; 64: 33; 80: 41 (~10 us a 5 MHz). A linha "20 colunas = 160 pulsos" da R2V4 estava **errada** (contava 8 estágios por
   coluna). A conta do `FIRMWARE.md` (41 com 80 teclas) está certa.
2. **Coluna 0 = a régua mais perto da placa principal**, estágio 0 = QA da primeira régua (a que recebe o DATA do conector J60k); o primeiro bit
   empurrado vai para a última régua.
3. **FIRST_COL = {0, 0, 0, 0}** (era {1, 0, 1, 1} na V3): a régua começa **na primeira tecla da fileira** (início = x da primeira tecla - 9,25 mm).
   **R5V4:** 8 teclas em todas as fileiras, sem posição vazia; `FIRST_NOTE = {57, 55, 56, 54}` (o da fileira 4 era 57); 3 semitons por coluna; +4 teclas por módulo.
4. O **microfone** entra no **MIC do SGTL5000** (pino 10 do codec, via C309 1 uF), nunca no LINE IN: ver "Microfone".
5. **J401 (tela) é o mesmo SH de 6 vias das fileiras**: 1 +3V3, 2 GND, 3 SDA, 4 SCL (5 e 6 sem uso); no cabo só 4 fios.

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
| **4** | 10 (D0) | **VOL_SW** (R6V4, **movido do 25**) | clique do volume (liga/desliga); só digital, INPUT_PULLUP como antes | entrada |
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
| **25 (A11)** | 51 | **MIC_DET** (R6V4) | tomada de CC da ponta do jack IN (via R306 100 k + C311 100 nF): detecta microfone de eletreto | **ADC** |
| **26 (A12)** | 67 (G8) | **OUT_R3** | fileira 3 | ADC |
| **27 (A13)** | 8 (G11) | **OUT_R4** | fileira 4 (a de trás) | ADC |
| 28 | 4 (3.3V_EN) | NC | sem uso (a cadeia PWR_EN da V1 não existe na V3/V4) | - |
| 29-45 | 16, 41, 43, 65, 63, 66, 64, 60, 62, 70, 68, 40, 42, 44, 46, 48, 73 | - | livres. **(conferir)** 38, 39, 40, 41 (pads 70, 68, 40, 42) têm ADC no Teensy 4.1; se valerem no MicroMod, servem de **OUT_B** (2ª linha por fileira) | - |

Resumo de uso: 28 sinais (0, 2, 3, 6-12, 14-28 menos 13) e, nos pads que não são pinos, ONOFF (6), PROGRAM (11), USB, 3,3 V.
Livres: 1, 4, 5, 13 e 29-45. **Para 80 teclas não faltam pinos.**

## A varredura (R2V4, E2): o contrato de tempo e de ordem

**Barramento da régua** (R5V4: conector de 6 vias nas duas pontas OU elo soldado de 5 fios; o sinal é o mesmo): 1 +3V3 · 2 GND · 3 OUT · 4 CLK · 5 DATA · 6 reservado
(OUT_B). Na ponta de entrada o pino 5 é o SER do 595; na ponta de saída é o QH' (cascata). VCC, GND, OUT e CLK passam direto.
Na placa principal há **4 conectores, um por fileira**: OUT_Rk próprio, SCAN_CLK e SCAN_DATA **comuns às 4**.

**Registrador:** 74HC595, SRCLK e RCLK juntos (uma linha CLK), SRCLR em 3,3 V, OE em GND. Efeitos que a firmware tem de saber:
1. a saída travada **atrasa um pulso** em relação ao deslocamento (a saída mostra o estado anterior ao pulso);
2. cada régua tem **8 estágios** (cascata pelo QH'), mas só QA..QD ligam sensores: o "1" que anda passa por **4 estágios mortos**
   (todas as colunas desligadas) entre uma régua e a seguinte;
3. as saídas **não são Hi-Z na partida**: ao ligar, dar 8 x N pulsos de CLK com DATA = 0 antes de ler (zera a cadeia).

**Coluna global c (0..C-1)** = régua c/4, sensor c%4 (QA..QD), igual nas 4 fileiras. 32 teclas: C = 8 (2 réguas por fileira);
48: 12; 64: 16; 80: 20. Com N réguas por fileira, a cadeia tem 8 N estágios.
- **Varredura em ordem:** com DATA = 1 no primeiro pulso e 0 nos outros, o "1" anda 1 estágio por pulso. Colunas 0..3 aparecem
  nos pulsos 1..4 (mais o atraso de 1), as colunas 4..7 do pulso 9 ao 12, e assim por diante (**passo 8 por régua**).
- **Acesso aleatório** (varredura rápida da tecla "quente"): empurrar o padrão de 8 N bits (o primeiro bit enviado vai para a
  última régua) e dar **1 pulso a mais**: **8 N + 1 pulsos por fileira** (80 teclas, N = 5: 41 pulsos = ~10 us a 5 MHz). Bit k (0 = primeiro) = estágio 8N-1-k.
- Velocidade do CLK: **até 5 MHz** (meio período >= 100 ns; HC595 a 3,3 V). Usar `digitalWriteFast`.

**Tempo por coluna** (E2, datasheet do TMAG5253, variante BA3 bipolar): ligar leva **20 us típico, 45 us MÁXIMO** (até 95 % do
valor final); a firmware espera **t_espera = 60 us** (valor da V3) no modo normal e **90 us** se a leitura precisar de 12 bits
limpos. Depois lê as 4 linhas (A0, A1, A12, A13) com ADC1 e ADC2 em paralelo, ~6 us. Passo = 70 us (ou 100 us).

| Teclas | Colunas | Varredura completa (70 us/passo) | (100 us/passo) |
|---:|---:|---:|---:|
| 32 | 8 | 0,56 ms | 0,80 ms |
| 48 | 12 | 0,84 ms | 1,20 ms |
| 64 | 16 | 1,12 ms | 1,60 ms |
| 80 | 20 | 1,40 ms | 2,00 ms |

(a V3 com multiplexadores varre 28 teclas em ~0,25 ms, **estimativa** (2 esperas de 60 us + 14 canais por metade): a F2 é ~2 vezes mais lenta na varredura em ordem.)
**Velocity:** com 1 ms = 127, a quantização de 0,56 ms (28) ou 1,4 ms (76) é grossa. A firmware deve (a) **interpolar** o instante
em que cada limiar é cruzado entre duas varreduras, e (b) fazer **varredura rápida da coluna quente**: ao sair do repouso, ler só
a coluna da tecla (padrão por acesso aleatório + 60 us + leitura = ~70 us, ~14 kHz). Sem isso, 80 teclas não resolvem 1 ms.

**Calibração:** repouso por tecla medido na partida (1,65 V típico em BA3 com 3,3 V; 1,61-1,69 V pelo datasheet).
Erro por assentamento: coluna lida 60 us depois do EN tem resíduo de ~1,8 % da diferença para a coluna anterior (tau efetivo ~15 us,
estimado a partir do "95 % em 45 us"); com 90 us o resíduo cai para ~0,25 %. **(conferir na primeira placa; é cálculo.)**

## Cadeia de energia e demais sinais

Iguais à V3 / `viaggio_micromod/pcb/PINOS.md` ("Como cada sinal de energia se comporta"): liga pelo clique do volume (2 s) ou
pelo USB (D206); KEEP no 10; AMP_SD no 12; HP_DET no 17; CHG_STAT agora no **0**.

## Microfone (R3V4, item 6; datasheet do SGTL5000, Freescale rev. 2, texto lido)

- Jack IN (J302, XUNPU PJ-327A): manga no GND, **ponta = MIC_J**; R305 2,2 k de MIC_BIAS à ponta; C309 1 uF da ponta ao MIC (pino 10); C310 100 nF no MIC_BIAS (Fig. 20 do datasheet).
- MIC_BIAS: 1,25 a 3,00 V em passos de 0,25 V (`CHIP_MIC_CTRL.BIAS_VOLT`), **no máximo VDDA - 200 mV** (VDDA = 3,3 V pelo ferrite: até 3,0 V vale). `BIAS_RESISTOR` (2/4/8 k) **não pode ser 0**
  (0 desliga o bloco). A biblioteca de áudio do Teensy (`micGain`) liga 2 k + 3,0 V: com o R305 em série são 4,2 k, ~0,45 mA num eletreto de 1 V. O datasheet diz que o R1 externo só é preciso se os resistores
  internos não servem: **o R305 pode virar 0 ohm** se a cápsula pedir mais corrente (a firmware escolhe; a placa aceita as duas).
- Ganho do pré-amplificador (`GAIN`): 0 / +20 / +30 / +40 dB. **Fonte de linha no IN não está prevista** (R6V4: um plugue de linha, sem CC, lê >= 2,85 V em MIC_DET e **não** liga os efeitos de voz) (o LINEIN do codec fica sem ligação nesta placa): só microfone de eletreto; a alternativa de nível de linha pediria outro jack (fora da R3V4).
- A impedância de entrada do MIC está na tabela 5 do datasheet (extração do PDF sem o número): **(conferir)**; C309 de 1 uF dá corte de voz seguro para Zin >= 2 kohm.

### Detecção de microfone (R6V4, item 5)
- O contato de chave da ponta do PJ-327A (pino 3) **não chega ao Teensy** (fica solto) e **não adianta**: dá só "tem plugue", não "tem microfone". Em vez disso, **R306 (100 k) liga a ponta (MIC_J) ao pino 25**, com C311 (100 nF) no pino: lê a tensão CC da ponta.
- Contas (bias 3,0 V, 2 k interno + R305 2,2 k = 4,2 k): sem carga, MIC_J = 3,0 V; eletreto de 0,1 / 0,3 / 0,5 mA: **2,6 / 1,7 / 0,9 V**; dinâmico (~200 ohm): ~0,14 V. O R306 de 100 k tira só 3 % do sinal de áudio (Z do C311 a 1 kHz é 1,6 k; o caminho de 100 k é de ordem maior que o R305). **(conferir na primeira placa)** com um eletreto e um plugue de linha: o limiar de 2,85 V é conta, não medida.
- Custo: 2 peças Basic 0402 (100 k C25741 como R305-série; 100 nF C1525), ~US$ 0,002, sem tipo Extended novo. Placa: **posicionadas sem trilhas, DRC 0 erros, paridade 0, ERC 0/0**.
- Limitação: um microfone de PC com bias no **anel** (a ponta é só sinal) e anel não ligado aqui (J302 pino 6 NC) não funciona nem é detectado; só vale microfone com a cápsula ligada à ponta (headset mono). Pergunta ao design/gestão.

## Pendências desta tabela (da R2V4, ainda valem)

- **KEY_INPUT** deixa de existir: a tecla é (fileira, coluna). Mapa de notas: `FIRST_NOTE = {57, 55, 56, 54}` (R5V4), **`FIRST_COL = {0, 0, 0, 0}`** (R3V4), 3 semitons por coluna;
  **R5V4:** 8 teclas por fileira, colunas 0..7, nenhuma vazia (antes 7, 8, 7, 6). 48: colunas 0..11 (12 por fileira); 64: 16; 80: 20. Ordem dos módulos e transposição: do firmware (R1V4, §4.4).
- Os pinos 14, 15, 26, 27 como entradas analógicas de OUT: **sem pull** interno; o pull-down de 100 kohm por linha está na placa principal.
- Pinos 38-41 como segundo conjunto de OUT: **(conferir)** no esquema da SparkFun antes de depender deles.
