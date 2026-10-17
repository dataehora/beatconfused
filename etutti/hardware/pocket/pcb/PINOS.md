# eTuttino Pocket · mapa de pinos do Teensy 4.0

**PROVISÓRIO** (SPEC v2, tarefa E1, 17 out 2026). Dono: eletrônica. É o contrato com a
programação: a firmware do Pocket (`ETUTTI_MODEL_POCKET`) segue esta tabela. Quando a placa
existir (depois de D2), o `build_pcb.py` do Pocket vai escrever o `KEY_INPUT` no sketch e
conferir a placa contra ele, como no eTuttino; os outros pinos ficam fixos aqui.

Só os 24 pinos da borda (0–23) são usáveis: o Teensy fica soldado na Audio Board e os pads de
baixo (24–33) ficam inacessíveis. Os 24 estão todos ocupados.

## Tabela

| Pino | Função | Sentido | Elétrica | Igual ao eTuttino? |
|---:|---|---|---|---|
| 0 | MUX S0 | saída | endereço dos 2 CD74HC4067 | sim |
| 1 | MUX S1 | saída | | sim |
| 2 | MUX S2 | saída | | sim |
| 3 | MUX S3 | saída | também escolhe o **grupo de sensores ligado** (S3 = 0: canais 0–7; S3 = 1: canais 8–15) | sim, com função nova |
| 4 | SENS_EN | saída | liga todos os sensores (alto = ligados). Com S3, decide qual grupo recebe EN (porta lógica na placa) | **novo** (era LED vermelho) |
| 5 | LED_G | saída PWM | LED verde, 330 Ω | sim |
| 6 | ENC_SW | entrada, pull-up | clique do encoder, para o GND | sim |
| 7 | (Audio Board) I2S OUT1A | — | reservado | — |
| 8 | (Audio Board) I2S IN1 | — | reservado | — |
| 9 | ENC_B | entrada, pull-up, interrupção | encoder B | sim |
| 10 | KEEP | saída | segura o conversor de 3,3 V ligado (alto = fica ligado). Ver "Liga/desliga" | **novo** |
| 11 | ENC_A | entrada, pull-up, interrupção | encoder A | **mudou** (era 17) |
| 12 | AMP_SD | saída | amplificador do alto-falante (alto = ligado). 100 kΩ para o GND na placa: Teensy desligado = amplificador desligado | **novo** |
| 13 | LED_R | saída PWM | LED vermelho, 330 Ω. Acende junto o LED laranja do próprio Teensy (≈ 3 mA a mais só enquanto o vermelho está aceso) | **mudou** (era 4) |
| 14 (A0) | MUX1 COM | ADC, INPUT_PULLDOWN | 14 sensores | sim |
| 15 (A1) | MUX2 COM | ADC, INPUT_PULLDOWN | 14 sensores | sim |
| 16 (A2) | VBAT | ADC | divisor 1 MΩ / 1 MΩ + 100 nF: V(pino) = V(bateria) / 2 (1,5–2,1 V) | **novo** (era MUX3 COM) |
| 17 (A3) | HP_DET | ADC | fone plugado = ~0 V; sem fone ≈ 1,4 V (ver abaixo) | **novo** (era ENC_A) |
| 18 | (Audio Board) I2C SDA | — | reservado | — |
| 19 | (Audio Board) I2C SCL | — | reservado | — |
| 20 | (Audio Board) I2S LRCLK1 | — | reservado | — |
| 21 | (Audio Board) I2S BCLK1 | — | reservado | — |
| 22 (A8) | POT | ADC | potenciômetro de volume (10 kΩ, log) | sim |
| 23 | (Audio Board) I2S MCLK1 | — | reservado | — |

Pinos 10–13 também vão ao soquete de cartão SD da Audio Board (CS, MOSI, MISO, SCK): **o Pocket
não usa cartão SD** e o soquete fica vazio. O 6 é o CS do chip de memória opcional da Audio Board
(não montado), e o 15 vai ao pad do potenciômetro opcional da Audio Board (não montado), como no eTuttino.

## Como cada sinal se comporta

- **Sensores (TMAG5253, EN).** Com EN baixo a saída do sensor fica em alta impedância e o
  INPUT_PULLDOWN do COM lê 0. Depois de ligar um grupo (trocar S3, ou subir SENS_EN), esperar
  **45 µs** (tON máximo do TMAG5253BA3; 130 µs se for o UA5) antes de ler. Ordem de leitura:
  canais 0–7 dos dois multiplexadores, troca S3, espera, canais 8–15. A leitura completa medida
  no Teensy do J dá ~340 µs (~3 kHz).
- **Tensão de repouso do sensor.** TMAG5253BA3 (bipolar): VCC/2 = 1,65 V sem campo, sobe com o
  sul do ímã (15 mV/mT). TMAG5253UA5 (unipolar): 0,2 V sem campo (48 mV/mT). O DRV5056 dava 0,6 V.
  A firmware precisa trocar `SENSOR_ZERO` e `PRESENT_MIN` (com o BA3: zero 1,65 V e "presente" acima
  de ~1,2 V; com o UA5: zero 0,2 V e "presente" acima de ~0,08 V).
- **HP_DET.** O jack tem um contato que encosta na ponta (canal esquerdo) quando não há plugue. Esse
  contato vai ao pino por 100 kΩ, com 1 MΩ e 100 nF para o GND. Sem fone, o pino vê a tensão de
  repouso da saída de fone do SGTL5000 (~1,6 V, conferir) filtrada: ~1,4 V. Com fone, o contato
  abre e o pino cai para 0 V. Limiar sugerido: 0,8 V, com ~50 ms de confirmação. Com o codec
  desligado o pino lê 0 V = "fone": o amplificador fica desligado, que é o lado seguro.
  **A manga do jack vai no terra virtual (HP_VGND) da Audio Board, nunca no GND.**
- **AMP_SD.** Ligar só com: sem fone, volume acima de zero e alguma voz soando; desligar depois
  de ~2 s de silêncio e no desligamento automático. O PAM8302A pede 10 ms entre alimentação e
  SD alto; ao ligar, subir o volume digital depois de ~20 ms para evitar estalo.
- **VBAT.** `analogRead` × 2 × 3,3 / 4095 (calibrar no protótipo). Na bateria: ~4,2 V cheia,
  3,7 V meio, **desligar abaixo de 3,3 V** (o PCM da bateria corta em ~2,5–3,0 V). Com USB
  ligado o carregador mantém 4,2 V.
- **Carregando.** O carregador não vai a um pino (não sobrou pino). A firmware deduz: USB
  presente (VBUS lido no registrador da USB do i.MX RT) e VBAT < 4,15 V = "carregando"; USB e
  VBAT ≥ 4,15 V = "carregada". Ver a pergunta sobre um LED de carga no `ELETRONICA.md`.
- **KEEP.** Primeira coisa na partida (antes do `setup()`, p.ex. em `startup_early_hook`):
  `pinMode(10, OUTPUT); digitalWrite(10, HIGH)`. O pulso da chave segura o conversor por
  ~0,5 s (conferir); depois disso só o KEEP o mantém. Para o desligamento automático "de verdade":
  silenciar, salvar o que precisar na EEPROM e baixar o KEEP: tudo desliga. Para religar, o
  usuário gira o volume até o clique (desliga) e volta.
- **LED.** Vermelho no 13, verde no 5, ambos PWM. Laranja = os dois.
- **Encoder.** A no 11 e B no 9, as duas com interrupção (`attachInterrupt`), mesma tabela de Gray
  e `ENC_STEPS_PER_DETENT` do eTuttino. Clique no 6.

## O que a programação muda em relação ao sketch do eTuttino

1. `MUX_COUNT = 2`, `MUX_COM_PINS = {14, 15}`.
2. `LED_PINS = {13, 5}` (vermelho, verde).
3. `ENC_A_PIN = 11` (era 17).
4. Novos: `SENS_EN_PIN = 4`, `KEEP_PIN = 10`, `AMP_SD_PIN = 12`, `VBAT_PIN = 16` (A2), `HP_DET_PIN = 17` (A3).
5. Leitura dos sensores por grupo (S3) com espera de tON; `SENSOR_ZERO` / `PRESENT_MIN` do TMAG5253.
6. Clock do ARM: começar em 396 MHz (`set_arm_clock(396000000)` no `setup()`); medir a CPU com o
   motor do Pocket e, se ficar abaixo de ~40 % a 240 MHz, usar 240 MHz.
