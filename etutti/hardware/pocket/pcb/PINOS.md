# eTuttino Pocket · mapa de pinos do Teensy 4.0

**Versão final para a P1** (SPEC v3, tarefa E2, 17 out 2026). Dono: eletrônica. É o contrato com a
programação: a firmware do Pocket (`ETUTTI_MODEL_POCKET`) segue esta tabela. Quando a placa existir
(E2b), o `build_pcb.py` do Pocket vai escrever o `KEY_INPUT` no sketch e conferir a placa contra ele,
como no eTuttino. Os outros pinos ficam fixos aqui.

Os pinos são os mesmos da versão provisória (E1). O que muda na v3 está em "Mudanças desde o E1",
no fim do arquivo.

Só os 24 pinos da borda (0–23) são usáveis: o Teensy fica soldado na Audio Board e os pads de
baixo (24–33) ficam inacessíveis. Os 24 estão todos ocupados.

## Tabela

| Pino | Função | Sentido | Elétrica | Igual ao eTuttino? |
|---:|---|---|---|---|
| 0 | MUX S0 | saída | endereço dos 2 CD74HC4067 | sim |
| 1 | MUX S1 | saída | | sim |
| 2 | MUX S2 | saída | | sim |
| 3 | MUX S3 | saída | também escolhe o **grupo de sensores ligado**: S3 = 0 liga os canais 0–7, S3 = 1 liga os canais 8–15 | sim, com função nova |
| 4 | SENS_EN | saída | liga os sensores (alto = ligados). Na placa: EN_A = SENS_EN · /S3, EN_B = SENS_EN · S3 | **novo** (era LED vermelho) |
| 5 | LED_G | saída | LED verde, 330 Ω | sim |
| 6 | ENC_SW | entrada, pull-up | clique do encoder, para o GND | sim |
| 7 | (Audio Board) I2S OUT1A | — | reservado | — |
| 8 | (Audio Board) I2S IN1 | — | reservado | — |
| 9 | ENC_B | entrada, pull-up, interrupção | encoder B | sim |
| 10 | KEEP | saída | segura o conversor de 3,3 V ligado (alto = fica ligado) | **novo** |
| 11 | ENC_A | entrada, pull-up, interrupção | encoder A | **mudou** (era 17) |
| 12 | AMP_SD | saída | amplificador do alto-falante (alto = ligado). 100 kΩ para o GND na placa | **novo** |
| 13 | LED_R | saída | LED vermelho, por 270 Ω e um diodo Schottky. Acende junto o LED laranja do próprio Teensy | **mudou** (era 4) |
| 14 (A0) | MUX1 COM | ADC, INPUT_PULLDOWN | 14 sensores | sim |
| 15 (A1) | MUX2 COM | ADC, INPUT_PULLDOWN | 14 sensores | sim |
| 16 (A2) | VBAT | ADC | divisor 1 MΩ / 1 MΩ + 100 nF: V(pino) = V(bateria) / 2 | **novo** (era MUX3 COM) |
| 17 (A3) | HP_DET | ADC | fone plugado ≈ 0 V; sem fone ≈ 1,4 V | **novo** (era ENC_A) |
| 18 | (Audio Board) I2C SDA | — | reservado | — |
| 19 | (Audio Board) I2C SCL | — | reservado | — |
| 20 | (Audio Board) I2S LRCLK1 | — | reservado | — |
| 21 | (Audio Board) I2S BCLK1 | — | reservado | — |
| 22 (A8) | POT | ADC | potenciômetro de volume, 10 kΩ log (A), entre 3,3 V e GND | sim |
| 23 | (Audio Board) I2S MCLK1 | — | reservado | — |

### Conferência com a Audio Board Rev D

A Rev D usa os pinos 7, 8, 20, 21 e 23 (I2S) e 18, 19 (I2C). Esses ficam reservados. Os outros
pinos que a Audio Board toca:

- **10–13:** soquete de cartão SD (CS, MOSI, MISO, SCK). O Pocket não usa cartão: o soquete fica
  **vazio**. Sem cartão, nada pesa nessas linhas (conferir no esquema da Rev D se há pull-up no CS;
  se houver, o KEEP só fica puxado para cima, que é o lado de "ligado", e some com o trilho).
- **6:** CS do chip de memória opcional (não montado).
- **15:** pad do potenciômetro opcional da Audio Board (não montado). É assim no eTuttino também.

### Conferência com o sketch do eTuttino

Mantidos: endereço do multiplexador em 0–3, COMs em 14/15 com `INPUT_PULLDOWN`, verde no 5, clique
no 6, encoder B no 9, potenciômetro no 22 (com a detecção por pull-up/pull-down na partida), tabela de
Gray e `ENC_STEPS_PER_DETENT` (o encoder do Pocket é 15 pulsos / 15 detentes, como o do eTuttino: 4).
Mudam só os pinos que a v2 já tinha listado (abaixo).

## Como cada sinal se comporta

- **Sensores (TMAG5253BA3, EN).** Com EN baixo a saída do sensor fica em alta impedância e o
  INPUT_PULLDOWN do COM lê 0. Depois de ligar um grupo (trocar S3 ou subir SENS_EN), esperar
  **45 µs** (tON máximo do BA3; 130 µs se um dia for o UA5) antes de ler. Ordem: canais 0–7 dos
  dois multiplexadores, troca S3, espera, canais 8–15. A leitura completa deve ficar em ~340 µs
  (~3 kHz) a 600 MHz; a P1 mede a 396.
- **Tensão de repouso do sensor.** TMAG5253BA3: VCC/2 = 1,65 V sem campo, sobe com o sul do ímã
  (15 mV/mT). O DRV5056 dava 0,6 V. `SENSOR_ZERO` ≈ 1,65 V; "presente" acima de ~1,2 V (sensor
  ausente lê 0 pelo pull-down).
- **HP_DET.** O contato de comutação da ponta do jack vai ao pino por 100 kΩ, com 1 MΩ e 100 nF
  para o GND. Sem fone o pino vê a tensão de repouso da saída de fone do SGTL5000 filtrada (~1,4 V,
  conferir); com fone o contato abre e o pino cai a 0 V. Limiar sugerido 0,8 V com ~50 ms de
  confirmação. Codec desligado: 0 V = "fone", o amplificador fica desligado (lado seguro).
  **A manga do jack vai no terra virtual (HP_VGND) da Audio Board, nunca no GND.**
- **AMP_SD.** Ligar só sem fone, com volume acima de zero e alguma voz soando; desligar ~2 s depois
  do silêncio e no desligamento automático. O PAM8302A pede 10 ms entre alimentação e SD alto; ao
  ligar, subir o volume digital depois de ~20 ms para evitar estalo.
- **VBAT.** `analogRead` × 2 × 3,3 / 4095 (calibrar no protótipo). ~4,2 V cheia, 3,7 V no meio,
  **desligar abaixo de 3,3 V** (o PCM corta em ~2,5–3,0 V). Com USB o carregador segura ~4,2 V.
- **Carregando.** Não há pino do carregador (não sobrou). A luz de carga é feita só no hardware: o
  CHG do BQ24074 acende o vermelho, inclusive com o Pocket desligado. Para a página, a firmware
  deduz: USB presente (VBUS visto pelo i.MX RT, p.ex. o bit B-session-valid do `USB1_OTGSC`,
  conferir) e VBAT < 4,15 V = "carregando"; USB e VBAT ≥ 4,15 V = "carregada".
- **LED durante a carga.** Enquanto carrega, o vermelho fica aceso pelo carregador e a firmware
  **não consegue apagá-lo**: com o verde aceso ele aparece laranja. As piscadas de confirmação do
  encoder (§7 da SPEC) devem usar o **verde** (apagar e acender), que continua sob controle da
  firmware. O "vermelho piscando" de erro só é visível sem USB.
- **KEEP.** Primeira coisa na partida (em `startup_early_hook`): `pinMode(10, OUTPUT);
  digitalWrite(10, HIGH)`. O pulso da chave segura o conversor por ~0,5 s (conferir); depois só o KEEP.
  Desligamento automático de verdade (SPEC §9, segundo estágio): silenciar, gravar o que precisar
  na EEPROM e baixar o KEEP: tudo desliga (~10 µA). Para religar, o usuário gira o volume até o
  clique (abre a chave) e volta. Com a chave aberta tudo desliga mesmo com o KEEP alto.
- **LED.** Vermelho no 13, verde no 5. O vermelho passa por um diodo Schottky (queda de ~0,35 V):
  com 270 Ω dá ~4 mA, o mesmo brilho do eTuttino. PWM nos dois funciona.
- **Encoder.** A no 11 e B no 9, com `attachInterrupt` nos dois, mesma tabela de Gray. Clique no 6.

## O que a programação muda em relação ao sketch do eTuttino

1. `MUX_COUNT = 2`, `MUX_COM_PINS = {14, 15}`.
2. `LED_PINS = {13, 5}` (vermelho, verde).
3. `ENC_A_PIN = 11` (era 17).
4. Novos: `SENS_EN_PIN = 4`, `KEEP_PIN = 10`, `AMP_SD_PIN = 12`, `VBAT_PIN = 16` (A2), `HP_DET_PIN = 17` (A3).
5. Leitura por grupo (S3) com 45 µs de espera; `SENSOR_ZERO` / `PRESENT_MIN` do TMAG5253BA3.
6. `set_arm_clock(396000000)` com as condições da SPEC §6 (medir e voltar a 600 MHz se falhar).
7. Confirmações do LED pelo verde (o vermelho pode estar preso pela carga).

## Mudanças desde o E1 (provisório)

- Nenhum pino mudou de lugar. O mapa deixa de ser provisório.
- **LED_R:** passa por um diodo (o "OU" com a luz de carga) e o resistor vai de 330 Ω para 270 Ω.
  Consequência para a firmware: item 7 acima.
- **USB:** o 5 V do carregador sai da plaquinha USB-C (antes de chegar ao Teensy), não de um fio
  no pad VUSB do Teensy. A firmware não muda.
- Encoder confirmado com 15 pulsos / 15 detentes: `ENC_STEPS_PER_DETENT = 4`, igual ao eTuttino.
