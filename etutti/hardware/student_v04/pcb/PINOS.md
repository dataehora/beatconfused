# eTutti Student V4 · mapa de pinos (FINAL da placa principal, R3V4; teclado de 32 teclas, R5V4; microfone R6V4; conector P6s e R305 = 0 ohm, R8V4; régua R8 e microfones eletreto/dinâmico, R10V4)

## R10V4: o que mudou para a programação (os pinos do Teensy NÃO mudam)

**Nenhum pino, nenhuma rede muda.** Mudam: (1) a régua padrão de 32 teclas passa a ser a **R8** (uma por fileira, 8 TMAG5253 e um 74HC595 com os **8 estágios usados**); (2) o contrato do microfone; (3) o C310 deixa de ser montado. Este bloco **substitui** o que as seções R8V4, R6V4, R5V4 e "A varredura" abaixo dizem sobre estágios mortos, pulsos e limiar de curto (cada trecho superado está marcado).

### Régua e varredura (32 teclas = 4 x R8)
- **R8:** 8 posições, passo 18,5 mm, 148 mm nominais (147,6 mm de placa). QA..QH = EN dos sensores 1..8: **nenhum estágio morto**. Terminações **idênticas** às da R4: IN (SH à esquerda, u 5,9), OUT (SH à direita, a 26,5 mm da ponta direita nominal), mesma pinagem P6s, mesma altura (2,95 mm), mesma boca (−y), 330 ohm no QH'. Qualquer régua liga a qualquer outra com o mesmo cabo.
- **Regra de coluna: coluna = estágio** da cadeia da fileira (estágio 0 = QA da régua mais perto da placa). Com a R4 sempre na ponta do agudo (SPEC R10V4), os estágios mortos (QE..QH da R4) ficam **só no fim** da cadeia, nunca entre colunas vivas.
- **Pulsos:** S = 8 x (número de registradores 595 da fileira, sejam de R8 ou de R4: cada um tem 8 estágios).

  | Teclas | Réguas por fileira | Estágios S | Colunas vivas | Acesso aleatório (S + 1 pulsos) | Passada em ordem (70 us/coluna) |
  |---:|---|---:|---:|---:|---:|
  | **32** | R8 | 8 | 8 | **9** | 0,56 ms |
  | 48 | R8 + R4 | 16 | 12 | 17 | 0,84 ms |
  | 64 | R8 + R8 | 16 | 16 | 17 | 1,12 ms |
  | 80 | R8 + R8 + R4 | 24 | 20 | 25 | 1,40 ms |

  (R8V4 e antes, só R4: 17 / 25 / 33 / 41. A fórmula 8 N + 1 continua valendo com **N = número de registradores de 8 estágios na fileira**, não "réguas de 4 teclas".) A 5 MHz, 9 pulsos = 1,8 us; a 2,5 MHz, 3,6 us.
- **Em ordem (32 teclas):** DATA = 1 só no primeiro pulso, 0 nos outros; a saída travada atrasa 1 pulso e **a coluna seguinte está sempre a 1 pulso**: uma passada de 8 colunas gasta 8 pulsos (antes: passo 8 por régua, com 4 estágios mortos no meio). Como a R4 só existe no fim, o "1" pode ser reinjetado a cada `colunas vivas` pulsos (12 / 16 / 20) sem esperar os estágios mortos.
- **Partida:** S pulsos com DATA = 0 zeram a cadeia (8 com 32 teclas); os 8N + 1 = 9 do sketch servem (sobra 1). **Acesso aleatório:** padrão de S bits + 1 pulso; bit k (0 = primeiro enviado) = estágio S − 1 − k: o primeiro bit vai para o último estágio.
- Sem mudança: SRCLK + RCLK juntos, ~OE em GND, SRCLR em 3,3 V, saídas desligadas em alta impedância, CLK até 5 MHz (330 ohm em CLK e DADO), t_espera de 60 us.
- **Para 48/64/80 teclas só muda o número de estágios S** (a tabela); a principal e os pinos não mudam.

### Microfone: eletreto com alimentação de plug-in e dinâmico, só pelo J302 (IN)
Adaptadores, phantom de 48 V e microfone de PC com bias no anel estão fora do escopo. **O ME 3 e o boost de 9-10 V saíram do projeto.** Detalhes e contas em `ELETRONICA.md` (R10V4) e `pcb/mic_ganho.py`.

- **Bias (CHIP_MIC_CTRL, 0x002A):** `BIAS_RESISTOR` (bits 9:8): 0 = bloco desligado **e saída em alta impedância (datasheet, Tabela 29)**, 1 = 2 k, 2 = 4 k, 3 = 8 k; `BIAS_VOLT` (bits 6:4): 1,25 V + 0,25 V x n, 7 = 3,0 V (no máximo VDDA − 0,2 V); `GAIN` (bits 1:0): 0 / +20 / +30 / +40 dB. Eletreto: `0x0170 | ganho` (2 k, 3,0 V; com R305 = 0 ohm são 2 kohm no total). Dinâmico: `0x0070 | ganho` (bias desligado; a ponta fica sem carga do lado do codec). O sketch já faz isto (`MicCodec`).
- **Bias ligado por engano numa bobina de 150-600 ohm não faz mal:** 1,15-1,4 mA, 0,3-0,8 mW na bobina (sem aquecimento); o diafragma só é empurrado por uma força estática equivalente a ~20 Pa (estimativa, da ordem de uma variação barométrica de 0,2 hPa); o codec não vê o CC (C309). Custa **0,6-1,9 dB de sinal** (a bobina enxerga 2 k em paralelo com os 2,9 k de entrada do codec). **Ligar ou desligar o bias gera um degrau de ~20 Pa no diafragma: silenciar a entrada ~150 ms em volta da troca.**
- **Carga da entrada (datasheet, Tabela 4): impedância do MIC = 2,9 kohm típica;** fundo de escala 2,83 Vpp = 1,0 Vrms (0 dB total).
- **MIC_DET (pino 25, leitura com o bias LIGADO, 8 leituras, histerese)** — substitui a regra de 0,30 V da R6V4:

  | v (V) | O que é |
  |---|---|
  | **>= 2,85** | nada ligado, ou plugue de linha com acoplamento por capacitor: sem microfone |
  | **<= 0,10** | curto, ou fonte de baixa resistência CC (< ~70 ohm): sem microfone |
  | 0,10 a ~0,85 | bobina dinâmica de 70 a ~600 ohm (150 / 300 / 600 ohm = 0,21 / 0,39 / 0,69 V; com +-20 % no resistor interno de 2 k, 600 ohm vai de 0,60 a 0,82 V) |
  | ~0,95 a 2,85 | eletreto (0,1 / 0,3 / 0,5 mA = 2,8 / 2,4 / 2,0 V; o FET da cápsula não deixa a ponta abaixo de ~0,9 V, estimativa) |

  **Limiar sugerido dinâmico/eletreto: 0,85 V descendo, 0,95 V subindo** (o sketch usa 0,60 / 0,80: uma bobina de 600 ohm, 0,60-0,82 V, cairia do lado "eletreto"; como o Auto mantém o bias ligado nos dois casos, isso só muda o ganho de fábrica, não faz mal). **As faixas se tocam** (bobina de ~800 ohm = 0,75-1,0 V; eletreto de >= 1 mA = 0,6-1,4 V), por isso fica o item de menu **"Tipo mic" Auto / Eletreto / Dinâmico (CC 111)**: Dinâmico declarado desliga o bias e **cega** o MIC_DET (lê 0 V; não há como saber se o plugue saiu: o contato de chave do jack não chega ao Teensy).
- **Efeitos de voz** só com microfone detectado (Auto/Eletreto) ou declarado (Dinâmico).
- **Ganho de fábrica (cálculo, `pcb/mic_ganho.py`; alvo -18 dBFS rms em 105 dB SPL a 1-3 cm):** dinâmico 0,45 mV/Pa ~39 dB; 1,7 mV/Pa ~30 dB; eletreto -44 dBV/Pa ~20 dB (passos: pré 0/20/30/40 + ADC 0 a 22,5 dB de 1,5 em 1,5). **Os padrões do sketch (24 dB dinâmico, 6 dB eletreto) ficam 9-14 dB abaixo desse alvo**: conservadores contra picos e canto a 1 cm (+9 dB); a SNR cai o mesmo tanto (tabela no relatório).
- **C310 (100 nF no MIC_BIAS) NÃO é montado** (R10V4): com R305 = 0 ohm ele ficava na ponta do jack e cortava o agudo (eletreto -1,9 / -9,9 / -17,5 dB a 1 / 4 / 10 kHz; bobina de 600 ohm -3 dB a 4 kHz). O pad fica para um 220-470 pF opcional.


## R8V4: o que mudou para a programação (os pinos do Teensy NÃO mudam)

- **Nenhum pino, nenhuma rede e nenhuma temporização do Teensy muda.** Muda só a **ordem dos pinos do conector** de 6 vias (J601..J604 na principal, J1 = entrada e J2 = saída de cada régua), a nova pinagem **P6s**:

  | Pino do conector | 1 | 2 | 3 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|
  | R7V4 e antes | +3V3 | GND | OUT | CLK | DADO | NC |
  | **P6s (R8V4)** | **+3V3** | **GND** | **OUT** | **GND** | **CLK** | **DADO** |

  O CLK continua sendo `SCAN_CLK` (pino 3) e o DADO `SCAN_DATA` (pino 2); só o pino físico do cabo mudou (CLK 4 → 5, DADO 5 → 6, o 4 virou GND). **Nada na firmware depende da ordem do conector** (ela só conhece pinos do Teensy); basta não haver comentário ou tabela que cite "conector pino 4 = CLK".
- **Resistores em série de CLK e DADO: 330 ohm** (R605 = CLK, R606 = DADO; eram 100). RC de ~7 ns com ~20 pF contra 100 ns de meio período a 5 MHz: **o CLK de 5 MHz continua valendo**, mas a borda é um pouco mais lenta; use `digitalWriteFast` como antes e, se a leitura de bancada mostrar atraso, 2,5-3 MHz sobra com folga (a varredura de 32 teclas, 17 pulsos, passa de ~3,4 us a 5 MHz para ~6,8 us a 2,5 MHz: irrelevante frente aos 8 x 70 us por varredura).
- **Cabo de estoque:** o JST `A06SR06SR30K51B` (reto, pino k → pino k). Com um cabo "invertido" (sufixo A) não há dano (todas as redes cruzadas passam por resistor ou por GND), mas **a varredura não funciona**; a firmware não consegue detectar isso, só o teste de continuidade do usuário.
- **R305 = 0 ohm** (aprovado): o bias do microfone é só o interno do SGTL5000. A firmware já escolhe `BIAS_RESISTOR` (2 kohm): **use 2 kohm**. **(Superado na R10V4: a regra de MIC_DET e o C310 estão na seção R10V4; o boost de 9-10 V saiu do projeto.)**
- Contagem de pinos usados: **28** (igual).


## R6V4: o que mudou para a programação (dois pinos trocam de função)

- **VOL_SW passa do pino 25 para o pino 4** (clique do volume, a mesma lógica: o clique de 2 s liga/desliga pelo hardware; a firmware só lê). O pino 25 (A11) virou **MIC_DET**, entrada analógica.
- **(Regra superada na R10V4: limiar de curto 0,10 V e dinâmico/eletreto em 0,85/0,95 V.)** **Detecção do microfone em J302 (IN)** (detalhe na seção "Microfone"): `analogRead(25)` com o **MIC_BIAS ligado** (3,0 V, `BIAS_RESISTOR` 2 k); leitura em volts `v = analogRead(25) * 3.3 / 1023` (10 bits) ou 4095 (12 bits):
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
- **(Superado na R10V4: 9 / 17 / 17 / 25 pulsos; N = registradores de 8 estágios.)** Pulsos do acesso aleatório = 8 x N + 1 (N = réguas por fileira): **17 / 25 / 33 / 41** (32 / 48 / 64 / 80 teclas; o número de réguas por fileira, 2 / 3 / 4 / 5, é o que conta).
  A varredura completa em ordem (colunas 8/12/16/20, 70 us/passo) também é a mesma: 0,56 / 0,84 / 1,12 / 1,40 ms.
- **(Superado na R10V4: a R8 usa os 8 estágios; a R4 só no agudo, com os mortos no fim.)** **Cadeia de registradores:** nada a ajustar. Cada régua continua com 8 estágios (QA..QD = sensores 1..4, QE..QH mortos), e agora os 4 sensores de
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

**(R10V4: a R8 não tem estágios mortos e os pulsos são 9 / 17 / 17 / 25; ver o início deste arquivo. O que segue vale para tempos e para o atraso de 1 pulso.)**

**Barramento da régua** (R8V4: conector de 6 vias nas duas pontas, pinagem **P6s**; o sinal é o mesmo): 1 +3V3 · 2 GND · 3 OUT · 4 GND · 5 CLK · 6 DATA
(a coluna "4 CLK, 5 DATA, 6 reservado" das revisões antigas está superada). Na ponta de entrada o pino 6 é o SER do 595; na ponta de saída é o QH' (por 330 ohm) (cascata). VCC, GND, OUT e CLK passam direto.
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

- Jack IN (J302, XUNPU PJ-327A): manga no GND, **ponta = MIC_J**; R305 (R8V4: 0 ohm; era 2,2 k) de MIC_BIAS à ponta; C309 1 uF da ponta ao MIC (pino 10); C310 100 nF no MIC_BIAS (Fig. 20 do datasheet).
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
