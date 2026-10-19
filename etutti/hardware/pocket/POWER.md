# eTuttino Pocket · orçamento de energia

Gerado por `pcb/power_budget.py` (eletrônica; não editar à mão). SPEC v5, tarefa F4 (sensor TMAG5253BA3 por grupo e 396 MHz decididos na v3; o clock final sai da medição na etapa de programação). Conversor TPS63001 (3,3 V fixo, LCSC C28060), aceito na v4. Na v5 a entrada volta a ser o micro-USB do Teensy (cabo de extensão de painel), com o 5 V tirado do pad VUSB por um fio.

Bateria LiPo 1S de **1000 mAh** (3,7 V médios), capacidade útil 85 % (corte em ~3,3 V, envelhecimento, frio) = 3,15 Wh.
Trilho único de 3,3 V pelo buck-boost TPS63001 (3,3 V fixo; eficiência 90 % típica, 86 % no pior caso, conferir). O amplificador do alto-falante (PAM8302A) vai direto na bateria (saída do carregador), fora do trilho de 3,3 V.

Origem de cada número: **medido** no Teensy 4.0 + Audio Board Rev D do J (17 out 2026), **datasheet**, ou **estimativa (conferir)**.

## Medido no Teensy do J (17 out 2026)

Sketch descartável feito do `etutti_synth` atual (usb=serialmidi): `set_arm_clock()` em cada frequência, acorde de 8 notas com as 4 palhetas e reverb por 2,5 s, `AudioProcessorUsageMax()`, e o tempo de uma leitura de 28 teclas em 2 multiplexadores (14 canais × 2 `analogRead`, 3 µs de acomodação por canal, como no sketch). Sem placa de teclas: o tempo de leitura não depende do sensor.

| Clock ARM | CPU do áudio (máx.) | leitura de 28 teclas | Teensy (estimativa) |
|---:|---:|---:|---:|
| 600 MHz | 8,5 % | 217 µs | 100 mA |
| 528 MHz | 9,6 % | 226 µs | 84 mA |
| 450 MHz | 11,3 % | 231 µs | 74 mA |
| 396 MHz | 12,9 % | 235 µs | 69 mA |
| 300 MHz | 17,0 % | 249 µs | 60 mA |
| 240 MHz | 21,2 % | 266 µs | 53 mA |
| 198 MHz | 25,8 % | 286 µs | 48 mA |
| 150 MHz | 33,7 % | 344 µs | 42 mA |

- A CPU do áudio escala com 1/clock: o motor de palhetas de hoje (8 vozes × 4 palhetas + reverb) usa só 8,5 % a 600 MHz e 34 % a 150 MHz. A 3ª palheta de 8' do Musette (P1) acrescenta ~25 % ao custo dos osciladores (estimativa).
- O ADC fica mais lento com o clock (o barramento IPG cai junto), mas a leitura de 28 teclas continua abaixo de 0,35 ms em todas as frequências.
- A corrente do Teensy **não foi medida** (não há medidor de corrente no PC do J). A coluna da direita é um modelo: 30 mA fixos + parcela dinâmica ∝ f·V², com a tensão do núcleo que o `set_arm_clock()` usa, ajustado aos ~100 mA a 600 MHz que a PJRC publica. Medir no protótipo.

## Consumidores por cenário (mA no trilho de 3,3 V)

### v1 (hoje): DRV5056, 600 MHz

| Consumidor | típ. fone | máx. fone | típ. alto-falante | máx. alto-falante |
|---|---:|---:|---:|---:|
| Teensy 4.0 a 600 MHz (estimativa, conferir) | 100,0 | 120,0 | 100,0 | 120,0 |
| Audio Board (SGTL5000) (conferir) | 20,0 | 40,0 | 12,0 | 20,0 |
| 28 sensores DRV5056A3 | 168,0 | 280,0 | 168,0 | 280,0 |
| 2 x CD74HC4067 | 0,1 | 0,2 | 0,1 | 0,2 |
| LED (uma cor, PWM) | 2,0 | 8,0 | 2,0 | 8,0 |
| **Total no trilho** | **290,1** | **448,2** | **282,1** | **428,2** |

### TMAG5253BA3 por grupo, 396 MHz (recomendado)

| Consumidor | típ. fone | máx. fone | típ. alto-falante | máx. alto-falante |
|---|---:|---:|---:|---:|
| Teensy 4.0 a 396 MHz (estimativa, conferir) | 69,1 | 82,9 | 69,1 | 82,9 |
| Audio Board (SGTL5000) (conferir) | 20,0 | 40,0 | 12,0 | 20,0 |
| 28 sensores TMAG5253BA3 ligados 50 % do tempo | 36,4 | 70,0 | 36,4 | 70,0 |
| 2 x CD74HC4067 | 0,1 | 0,2 | 0,1 | 0,2 |
| LED (uma cor, PWM) | 2,0 | 8,0 | 2,0 | 8,0 |
| **Total no trilho** | **127,6** | **201,1** | **119,6** | **181,1** |

Alto-falante (na bateria): 0,20 W médios típicos / 0,50 W no pior caso (volume alto), classe D com 80–85 % de eficiência, mais 4–8 mA de repouso do PAM8302A (datasheet). Os watts médios são estimativa (conferir com o alto-falante escolhido, de ouvido).

## Autonomia tocando sem parar, bateria de 1000 mAh

| Cenário | fone típ. | fone pior | alto-falante típ. | alto-falante pior |
|---|---:|---:|---:|---:|
| v1 (hoje): DRV5056, 600 MHz | 3,0 h | 1,8 h | 2,4 h | 1,4 h |
| TMAG5253BA3 sempre ligado, 600 MHz | 4,4 h | 2,7 h | 3,3 h | 1,8 h |
| TMAG5253BA3 por grupo (S3), 600 MHz | 5,4 h | 3,4 h | 3,9 h | 2,2 h |
| **TMAG5253BA3 por grupo, 396 MHz** | **6,7 h** | **4,1 h** | **4,5 h** | **2,4 h** |
| TMAG5253BA3 por grupo, 240 MHz | 7,7 h | 4,5 h | 4,9 h | 2,5 h |

"Pior" = todos os consumidores no máximo do datasheet ao mesmo tempo e o conversor na pior eficiência; na prática fica entre as duas colunas.

## Efeito do liga/desliga dos sensores na velocidade

Os sensores de cada grupo (canais 0–7 e 8–15 dos dois multiplexadores, escolhidos pelo bit S3 do endereço) só ficam ligados enquanto o seu grupo é lido; depois de trocar de grupo a firmware espera o tempo de ligar (tON máximo do datasheet). Leitura de um grupo: 8 canais × (3 µs + 2 leituras de 6,25 µs) = 124 µs a 600 MHz (medido).

| Sensor e modo | tON máx. | período de leitura | leituras por tecla/s | amostras numa batida de 1 ms | erro de velocidade, batida de 1 ms | erro, batida de 10 ms |
|---|---:|---:|---:|---:|---:|---:|
| DRV5056A3 sempre ligado | 300 µs | 217 µs | 4608 | 4,6 | ±2 | ±0 |
| DRV5056A3 por grupo | 300 µs | 848 µs | 1179 | 1,2 | ±6 | ±1 |
| TMAG5253BA3 sempre ligado | 45 µs | 217 µs | 4608 | 4,6 | ±2 | ±0 |
| TMAG5253BA3 por grupo | 45 µs | 338 µs | 2959 | 3,0 | ±2 | ±0 |
| TMAG5253UA5 por grupo | 130 µs | 508 µs | 1969 | 2,0 | ±3 | ±0 |

Erro de velocidade em unidades MIDI (1–127), com o mapa logarítmico da firmware (1 ms = 127, 80 ms = 1) e um erro de tempo de ~¼ do período por cruzamento (interpolação linear entre leituras; estimativa). Com o DRV5056 (tON até 300 µs) o liga/desliga por grupo derruba a leitura para ~1,2 kHz: a batida mais rápida cabe em ~1 amostra. **Não recomendado com o DRV5056.** Com o TMAG5253BA3 (tON ≤ 45 µs) a leitura fica em ~3 kHz e o erro é pequeno.

## Parado, desligamento automático e desligado

| Estado | consumo | a bateria cheia dura |
|---|---:|---:|
| Ligado, sem tocar (amplificador desligado, sensores lidos a ~500 Hz com liga/desliga geral) | ~93 mA no trilho | ~9 h |
| Desligamento automático "leve" (Teensy a 24 MHz, codec desligado, sensores a 20 Hz; acorda numa tecla) | ~23 mA (conferir) | ~35 h |
| Desligamento automático "de verdade" (a firmware solta o KEEP e o conversor desliga) | ~10 µA (carregador + divisor) | anos (fica a autodescarga da bateria) |
| Chave do volume desligada | ~10 µA | anos |

O "leve" não é desligado: sozinho, um Pocket esquecido ligado gastaria a bateria em pouco mais de um dia. Por isso a SPEC v3 usa os dois estágios: leve depois de 15 min, KEEP baixo (desligado de verdade) depois de mais 30.

## Carga pelo micro-USB

BQ24074 em modo USB500 (EN1 = 1, EN2 = 0): no máximo 500 mA da USB; corrente de carga programada 500 mA (R_ISET = 1,78 kΩ, K_ISET = 890 AΩ; datasheet). O 5 V chega pelo cabo de extensão micro-B de painel, entra no micro-B do Teensy e sai do pad VUSB (ponte VUSB–VIN cortada) por um fio de 26 AWG até o J_VBUS da placa principal. Qualquer carregador ou porta USB-A serve; carregador USB-C, com um cabo C → micro-B (o resistor de 5,1 kΩ que o carregador precisa está no próprio cabo).

### Corrente no pad VUSB e no micro-B do Teensy 4.0

- **Esquema da PJRC** (https://www.pjrc.com/teensy/schematic40.png): o VBUS do micro-B (J1 pino 1) vai **direto** ao nó VUSB (só o C25 de 2,2 µF), sem fusível. O fusível de 500 mA (F1) fica do lado do VIN, depois da ponte VUSB–VIN, no caminho do 5 V da USB host. Com a ponte cortada, a corrente do carregador passa só pelo contato do micro-B e pela trilha até o pad.
- **PJRC, loja do Teensy 4.0** (https://www.pjrc.com/store/teensy40.html): o VUSB recebe a energia da USB e pode ser separado do VIN cortando os dois pads do verso; nenhuma corrente máxima é publicada para o pad.
- **Paul Stoffregen, fórum PJRC** (https://forum.pjrc.com/index.php?threads/max-current-through-vusb-to-pcb.27859/, sobre o Teensy 3.1): resposta curta "500 mA", limitada pelo PTC e pela resistência do cabo, conector e trilhas. No 4.0 o PTC não está nesse caminho, então o limite prático é o do próprio USB 2.0 (500 mA de uma porta de computador) e o do contato do micro-B (1,8 A pela especificação Micro-USB, conferir no conector da PJRC).
- **No Pocket:** o BQ24074 limita a entrada a 500 mA (USB500, típico 475), mais ~5 mA da luz de carga e 50 µA do R26: **≤ ~0,5 A, dentro do que a PJRC indica** e bem abaixo do contato do micro-B. O Teensy não tira nada do VUSB (é alimentado pelo 3,3 V do conversor). Fio de 26 AWG (~0,13 Ω/m): 50 mm = 7 mΩ, 3,5 mV de queda a 500 mA.

| Situação | corrente na bateria | carga completa (estimativa, conferir) |
|---|---:|---:|
| 1000 mAh, desligado | 500 mA | ~2,5 h |
| 1000 mAh, tocando com fone (o aparelho tira ~106 mA da OUT a 4,4 V) | ~394 mA | ~3,0 h |
| 1200 mAh, desligado | 500 mA | ~2,9 h |
| 1200 mAh, tocando com fone (o aparelho tira ~106 mA da OUT a 4,4 V) | ~394 mA | ~3,5 h |

Fase de tensão constante no fim da carga: +0,5 h (estimativa). A carga para fora de 0–50 °C (NTC de 10 kΩ, B 3435, no TS: corrente de 75 µA, desliga a 2,1 V = 28 kΩ ≈ 0 °C e a 0,3 V = 4 kΩ ≈ 50 °C; datasheet).

**Luz de carga** (CHG do BQ24074 → P-MOSFET → 1000 Ω → diodo → vermelho do LED): ~2,8 mA, tirados da USB, não da bateria, **só com o Pocket desligado** (SPEC v4). Ligado, o trilho de 3,3 V liga o Q31, que desvia a luz para o GND: ~5,0 mA da USB enquanto carrega e toca, nada da bateria. O TVS do VBUS (SMF5.0A) só vê tensão com USB: a fuga dele sai da USB, nunca da bateria.

## Autonomia com outra capacidade

A bateria de 3 fios que se acha em 603450 às vezes é de 1200 mAh (mesmo tamanho). Cenário recomendado, típico:

| Bateria | com fone | com alto-falante |
|---|---:|---:|
| 1000 mAh | 6,7 h | 4,5 h |
| 1200 mAh | 8,1 h | 5,4 h |

## Para conferir no protótipo

1. Corrente real do trilho de 3,3 V com o Teensy a 600, 396 e 240 MHz (multímetro em série com a bateria).
2. Corrente dos 28 sensores e o campo do ímã do Gateron no fundo do curso (escolhe TMAG5253UA5 ou BA3).
3. Volume confortável no alto-falante: potência média real (tensão RMS na bobina).
4. Eficiência do TPS63001 com a carga real.
5. Tempo de carga real e a temperatura da bateria tocando enquanto carrega.
