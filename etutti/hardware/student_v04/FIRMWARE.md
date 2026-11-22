# eTutti Student V4 · firmware e som (SPEC R7V4)

22 nov 2026. **Atende a R7V4, regra geral 2 (tarefa 3 da tabela): a Student V4 tem sketch próprio, `etutti/firmware/student_v4/`**, só com o caminho da V4 modular de **32 teclas**. O sketch compartilhado `etutti/firmware/etutti_synth/` fica congelado (não foi editado, não é compilado nem conferido aqui). O texto das revisões R1V4 a R6V4 deste arquivo (estudos de capacidade, contas, discussões, tabelas por tamanho) foi consolidado abaixo; o histórico completo está no git (commits das R1V4 a R6V4).

**Nada foi gravado e nada rodou numa placa: a V4 não existe.** Todo tempo, CPU e nível de microfone é **conta** (marcado "estimado"); só a memória é **compilada**. Pinos e contrato de varredura: `pcb/PINOS.md` (da eletrônica, lido, não editado).

## 1 · A pasta e a compilação

```
etutti/firmware/student_v4/
  student_v4.ino    o sketch (teclado, áudio, voz, menu, energia)
  voice_fx.h        efeitos de voz (entrada do microfone, vocoder, rastreador YIN, eco, supressor de microfonia)
  ui_text.h         textos da tela e tipos do menu (português / inglês)
  oled_font.h       fonte 5 x 10 com acentos (gerada por tools/oled_font/make_font.py)
  reed_sampler.h    acordeão amostrado (4 fileiras de palhetas, por voz)
  name.c            nome USB "eTutti"
  .gitignore        reed_samples.cpp e reed_samples.h (dados licenciados: nunca versionar)
```

`reed_samples.cpp/.h` (1,3 MB, gerados por `etutti/firmware/tools/accordion_samples/build_samples.py` a partir da biblioteca licenciada do J) ficam **só na máquina dele** e agora são gravados em `student_v4/` (os três scripts de `tools/` passaram a escrever aqui). Sem os dois arquivos o sketch compila e usa as tabelas sintetizadas de palhetas.

**Compilação** (`arduino-cli compile --fqbn teensy:avr:teensyMM:usb=midi,speed=396 etutti/firmware/student_v4`, Teensyduino 1.62, nada gravado):

| | Flash (código + dados) | RAM1 (variáveis) | RAM2 (variáveis) |
|---|---:|---:|---:|
| **com** as amostras do acordeão | 140 784 + 1 239 352 B (~1,39 MB; livre 15,1 MB) | 105 024 B (livre 255 KB) | 202 272 B (livre 322 KB) |
| **sem** as amostras (tabelas sintetizadas) | 140 464 + 41 496 B | 104 000 B | 202 272 B |

`#error` se o USB não for MIDI ou se a placa não for o Teensy MicroMod.

### O que o sketch próprio não tem (regra geral 2)

Nenhum ramo de outra placa ou modelo (nem tabelas de pinos, multiplexadores ou potenciômetro), nenhuma chave de compilação por tamanho ou por recurso (tudo o que a V4 usa é fixo), só a regra analógica de detecção de microfone (as modalidades 0 e 1 saíram), nenhum build de medição, e **só o acordeão**: sem instrumentos de amostras nem síntese (saíram o CC 25, os CCs de oscilador 20-22, 28-30, 75, 79, 85-87, 102-104 e a linha "Instrumento" do menu), o que também tirou ~50 KB de flash e um mixer do grafo de áudio.

## 2 · Teclado: varredura, velocity, mapa de notas

**Hardware** (`PINOS.md`): réguas de 4 teclas (4 TMAG5253BA3 + um 74HC595), encadeadas em cada fileira. Quatro linhas analógicas **OUT_R1..R4 = pinos 14, 15, 26, 27**, `SCAN_DATA` = 2, `SCAN_CLK` = 3 (comuns às 4 fileiras, SRCLK e RCLK juntos). Um "1" andando na cadeia liga **uma coluna** (4 sensores, um por fileira); as saídas desligadas ficam em alta impedância. O sketch segue o contrato: a saída travada **atrasa 1 pulso**; cada régua tem 8 estágios e só QA..QD têm sensores (**4 estágios mortos** entre réguas: de uma coluna 3 para a 4 são 5 pulsos); na partida, `8N + 1` pulsos com DATA = 0 zeram a cadeia (N = réguas por fileira); acesso aleatório = padrão de `8N` bits + 1 pulso; CLK a 5 MHz (`SR_HALF_PERIOD_NS` 100).

**32 teclas = 2 réguas por fileira, 8 colunas, 4 fileiras de 8 teclas, 17 pulsos.** Mapa de notas (3 semitons por coluna, `FIRST_COL` = 0 em todas):

| Fileira | `FIRST_NOTE` C-griff (B-griff) | Notas |
|---|---|---|
| 1 (frente) | 57 A3 (56 G#3) | A3 C4 D#4 F#4 A4 C5 D#5 F#5 |
| 2 | 55 G3 (55) | G3 A#3 C#4 E4 G4 A#4 C#5 E5 |
| 3 | 56 G#3 (57 A3) | G#3 B3 D4 F4 G#4 B4 D5 F5 |
| 4 (trás) | 54 F#3 (53 F3) | F#3 A3 C4 D#4 F#4 A4 C5 D#5 |

Conferido contra o `PINOS.md` (R5V4): `FIRST_NOTE = {57, 55, 56, 54}`. CC 24 troca C-griff / B-griff (a fileira 4 acompanha a 1).

**Leitura.** `IntervalTimer` chama `scanTick()` a cada 12 us na prioridade NVIC 96 (acima do USB 112, do DMA do I2S 128 e do áudio 208); `scanTick()` nunca espera: se os sensores da coluna ligada ainda não passaram `SENSOR_WAKE_US` (60 us; o TMAG5253BA tem 20 us típico e **45 us máximo**) volta na hora; senão lê a coluna (ADC1 e ADC2 em paralelo: pinos 14/15 alcançam os dois, 26/27 só o ADC2, logo dois pares de conversões, ~6 us), liga a próxima e processa as 4 teclas. Os eventos de tecla (nota com velocity, posição do teste de teclas) vão para uma fila de 128 posições (sem trava) que o `loop()` entrega às vozes e ao `usbMIDI` (`drainKeyEvents()`). A leitura da bateria/HP_DET (`analogReadSlow`) e o CC 14 pausam a varredura por alguns us (`scanPaused`).

**Curso e velocity.** O campo do ímã cai com ~1/d³, então o curso (0..1) vem da raiz cúbica do campo acima de 1,65 V, entre o repouso (medido na partida e que segue a deriva lenta) e o fundo (aprendido, guardado na EEPROM). O sinal do sensor (sobe ou desce) sai da leitura de repouso; leituras que descem são espelhadas em torno da meia escala. Nota ligada em 45 % do curso, desligada em 30 %; velocity = tempo de 12 % a 45 %, em escala log (1 ms = 127, 80 ms = 1), com o instante **interpolado** entre duas leituras. Curvas (CC 9): fixa 100, suave, normal, dura.

**Leitura quente.** Uma tecla que começou a subir (> 3 % do curso, há menos de 15 ms) faz a coluna dela ser relida várias vezes (~85 us trocando de coluna, ~56 us na mesma), em rodízio entre as colunas quentes, com orçamento por passada de `2,2 ms - passada nominal` (mínimo 300 us), de modo que nenhuma tecla fique muito mais que ~2,2 ms sem leitura.

| 32 teclas | |
|---|---|
| Passada nominal (8 colunas x ~72 us), sem tecla quente | **~0,58 ms (1,7 kHz)**, estimado |
| Leitura quente | ~81 us (outra coluna), ~56 us (a mesma), estimado |
| Erro de velocity (± unidades, ¼ do período por cruzamento): batida de 1 / 2 / 5 / 10 ms | passada sozinha 5,9 / 2,9 / 1,2 / 0,6; leitura quente de 1 coluna 0,6 / 0,3 / 0,1 / 0,1; de 2 colunas (acorde) 1,7 / 0,9 / 0,3 / 0,2 |
| CPU da varredura | **~19 %** (13-14 us de trabalho a cada 72 us), estimado |

O mais rápido que um dedo toca fica em 3-5 ms, onde a leitura quente dá ±0,1 a ±0,7. **Calibração:** a EEPROM guarda a amplitude de cada tecla (CC 14 ou menu CALIBRAR esquece e reaprende). **Erro de assentamento:** a coluna lida 60 us após o EN tem resíduo de ~1,8 % da diferença para a anterior (estimado; com 90 us, ~0,25 %): **(conferir na primeira placa)**.

## 3 · Som

Acordeão de 8 vozes, quatro palhetas por nota: 16' (cassotto), 8' M1 (aberta), 8' M2 (cassotto, desafinada pelo "molhado", CC 27) e 4' (piccolo), escolhidas por **sete registros** (CC 26): L Bassoon, ML Bandoneon, MM Violin (padrão), MH Oboe, H Piccolo, LH Organ, M Clarinet. Palhetas **amostradas** (`reed_sampler.h`: quatro fileiras de amostras com laço, interpolação Catmull-Rom, passa-baixas de brilho) quando `reed_samples.*` existem, senão tabelas aditivas **limitadas em banda** (nunca dente-de-serra ou quadrada crua). **Velocity = pressão do fole**: 24 dB de volume e, nas amostras, brilho (passa-baixas de 700 Hz a 16 kHz, pelo menos 3x a nota); medido 27 dB entre as velocities 4 e 127 numa G3. Depois: filtro de tom (**biquad**, nunca o SVF; CC 74), reverb leve (CC 91), volume (ganho antes do I2S: o MAX98357A não tem volume próprio; CC 7). Equilíbrio das fileiras (`SAMPLED_REED_GAIN`) e comprimento do laço são **primeiros palpites**, a ouvir na placa.

**Alto-falante de estudo (EQ).** O MAX98357A e o SGTL5000 recebem o mesmo fluxo I2S; por isso "só no alto-falante" = **sem plugue no OUT (HP_DET)**. Sem plugue, o fluxo passa por 4 biquads (passa-altas de 4ª ordem Butterworth a 300 Hz = 24 dB/oitava, corte de -6 dB em 1 kHz, Q 1,2); com plugue o equalizador é desconectado (custo 0). CC 105 liga/desliga (padrão ligado), 106 corte (150 a 450 Hz), 107 pico de 1 kHz (0 a -12 dB). No padrão a G3 (196 Hz) sai ~15 dB mais baixa (conta em numpy: -38,2 dB a 100 Hz, -15,1 a 196, -3,5 a 300, -6,0 a 1 kHz). **Ponto de partida de conta, não ouvido.** +~0,45 % de CPU só quando o alto-falante é a saída.

## 4 · Voz (microfone no IN)

**Regra:** os efeitos de voz só funcionam com **um microfone de eletreto no IN (J302)**; sem ele as páginas Voz e Captação e as linhas Saída voz e Teclas somem do menu e `voiceBlocked()` cala tudo da voz (CPU 0), a tela mostra `sem mic`; os ajustes voltam ao plugar. **Detecção** (`PINOS.md` R6V4): o pino **25 (MIC_DET, ADC)** lê a tensão CC da ponta (R306 100 k + C311 100 nF) com o MIC_BIAS em 3,0 V; leitura a cada 50 ms, 3 iguais para mudar:

| Tensão | Jack | Efeitos de voz |
|---|---|---|
| >= 2,85 V | nada, ou plugue de linha (sem carga CC) | desligados |
| 0,30 V < v < 2,85 V | eletreto (0,1 / 0,3 / 0,5 mA = 2,6 / 1,7 / 0,9 V) | liberados |
| <= 0,30 V | curto, ou dinâmico de baixa impedância | desligados |

Limiares são **conta** (`MIC_DET_MIN_V`, `MIC_DET_MAX_V`); medir na primeira placa. Microfone de PC com bias no anel não é detectado nem funciona (J302 pino 6 NC). **VOL_SW = pino 4** (R6V4; o 25 é MIC_DET).

**Saída:** a voz sai **só no fone/AUX** por padrão; o alto-falante é opção do menu (CC 96) com aviso de microfonia na tela, e **nunca é salvo ligado**.

**Cadeia** (`voice_fx.h`): `VoiceInput` (passa-altas, ganho, notches, **expansor** com limiar/razão/ataque/retenção/soltura) → vocoder de 10 bandas (teclado de portadora) / 4 deslocadores `AudioEffectGranular` / rastreador de afinação **YIN** / eco (60..740 ms, realimentação até 0,85) / FFT de 1024 pontos do **supressor de microfonia** (notches de -18 dB, Q 30, até 4, desligado até o menu ligar) → mistura → reverb comum. **Padrão de fábrica = headset a 2-3 cm da boca** (conta, não ouvido): ganho 26 dB, limiar ~550, razão forte, ataque 1,2 ms, retenção ~78 ms, soltura ~117 ms, passa-altas 167 Hz; a ação "Mic headset" do menu volta a estes valores. Conta: cápsula de -42 dBV/Pa, voz a 2,5 cm = ~6,3 mV rms, x20 = ~126 mV, ~0,14 da escala (sem corte); o alto-falante a ~30 cm chega 22 dB abaixo e fica sob o limiar. YIN: simulado em numpy, erro máx. 13 cents com vibrato, nenhum erro de oitava (voz real **não** testada).

**Harmonizador que segue a tecla** (CC 95 liga, **108 modo** (valor/32: 0 Exato, 1 Ajuda, 2 Intervalo), **109** força da ajuda, **110** vozes (>= 64 = 4, padrão 3), 97 oitava perto/exata; CC 19 = intervalo fixo quando não segue): **Exato** (cada nota segurada ganha um deslocador que põe a voz exatamente nela), **Ajuda** (um deslocador puxa a voz parte do caminho para a nota mais próxima, até 3 semitons; a seca faz fade para fora ~40 ms), **Intervalo** (a voz fica natural; cada outra nota ganha o intervalo até a nota de referência; uma tecla sozinha = silêncio). Sem voz com afinação por 300 ms ou sem nota, a harmonia silencia. Latência (estimada): harmonia ~25-30 ms atrás da seca; tecla nova ouvida em ~40 ms; seguir uma mudança de nota do cantor ~60 ms.

**CCs de voz** (só no sketch; a página V4 muda `script.js` junto quando existir): 16 seca, 17 vocoder, 18 harmonizador, 19 intervalo, 76 eco, 77 tempo, 78 realimentação, 80 reverb da voz, 81 limiar, 82 ganho do microfone (20..52 dB no codec), 83 nível do teclado, 84 ataque, 89 retenção, 90 soltura, 92 passa-altas, 93 razão, 94 supressor, 95, 96, 97, 105-107 (EQ), 108-110. Tudo começa desligado.

## 5 · Tela, menu, energia

**OLED SSD1306 128 x 64** (J401, I2C 0x3C compartilhado com o codec), driver próprio com buffer de 1 KB enviado em pedaços de 16 bytes, uma por passada do `loop()` (a varredura em interrupção não é atrasada pelo I2C). Fonte 5 x 10 com minúsculas e acentos (~1,6 KB), texto em UTF-8, **português e inglês** (Sistema > Idioma, gravado na hora na EEPROM, endereço 250; padrão português). Para um idioma novo: código no enum de `ui_text.h`, nome em `LANG_NAME` e um texto a mais em cada `{...}` (o que faltar cai para o inglês); espanhol fica para depois do protótipo (R7V4 item 4). Telas desenhadas com a fonte real em `img/tela_pt.png` e `img/tela_en.png` (`tools/oled_font/render_screens.py`), **não vistas num SSD1306**.

**Knobs** (pinos `PINOS.md`: volume A/B 22/24, clique 4; seletor A/B 11/9, clique 6; `ENC_STEPS_PER_DETENT` 2, EC11E18244A5): volume gira = volume (CC 7 de volta); **clique do volume segurado 2 s liga/desliga** (KEEP = pino 10; o hardware faz o liga/desliga, a firmware só lê e segura o KEEP); seletor gira = os sete registros (CC 26 de volta, LED verde piscando até guardar), clique depois de girar = guarda o registro para a próxima partida (EEPROM 200), clique sem girar = volta ao MM seco; **clique longo do seletor (0,7 s) abre o menu**, o curto age ao soltar. No menu: seletor move o cursor, clique entra / troca / executa, volume gira o valor, clique do volume volta; fecha sozinho em 30 s.

```
Menu  ├ Voz (só com microfone): seca, vocoder, harmonizador, modo, intervalo/força, oitava, vozes, eco (nível, tempo, realimentação), reverb da voz
      ├ Captação (só com microfone): ganho, limiar, razão, ataque, retenção, soltura, passa-altas, Mic headset, antimicrofonia, limpar notches
      ├ Saída: volume, saída da voz (fone/AUX ou + alto-falante, com aviso), nível das teclas, EQ do alto-falante, corte, pico de 1 kHz
      ├ Som: registro, reverb, curva de velocity
      └ Sistema: salvar, zerar voz, calibrar, teste de teclas, idioma
```

**Salvar** guarda (EEPROM 210) a voz, a EQ, o modo do harmonizador e as vozes; o alto-falante da voz nunca. **LED:** laranja ao ler as teclas (>= 0,6 s), verde tocando, verde piscando = registro por guardar, verde breve a cada 2 s = repouso, vermelho lento = bateria baixa, vermelho rápido = codec ou sensor de tecla não respondeu (inclui placa sem réguas), laranja carregando. **Energia:** carregador BQ24074 (CHG_STAT = pino 0), bateria no pino 16 (divisor 1:2), desliga sozinho com bateria vazia ou após 15 min sem tecla/knob/MIDI (5 min: amplificador em repouso); **desligamento suave** com USB (nada corta o 3,3 V com o cabo; um clique reinicia); alto-falante ligado quando não há fone (AMP_SD = pino 12); USB a 12 Mbit/s (`startup_late_hook`, R1V4 5.4 item 3, **não testado**).

## 6 · CPU e memória

**Memória (compilada):** tabela da seção 1. `AudioMemory(104)` é estimativa (+34 blocos de voz sobre o acordeão): **medir** `AudioMemoryUsageMax()`. Os 4 deslocadores usam 25,6 KB de RAM2 cada, o eco 64 KB.

**CPU a 396 MHz (estimada, ciclos por amostra x 44 117 amostras/s; erro dos efeitos ±50 %):**

| Bloco | CPU |
|---|---:|
| acordeão, 8 notas, MM (medido num Teensy 4.0 a 600 MHz: 12 %; a 396 MHz ~18 %) / quatro fileiras de palhetas (medido 20 %, ~30 % a 396) | 18 % / 30 % |
| voz, vocoder (4,4 %), eco, reverb da voz, mixers, entrada | ~5,5 % |
| harmonizador Exato com 4 notas (YIN 1,2 % + 4 x 0,3 % + filtro) | ~2,5 % |
| supressor de microfonia (FFT 1,1 % + notches 0,5 % + análise 0,1 %) / expansor | 1,7 % / 0,2 % |
| EQ do alto-falante (só sem fone) | 0,45 % |
| **varredura** | **~19 %** |
| **Pior caso, tudo ligado** | **~60 %** |

O áudio fica com ~81 % da CPU (a varredura leva ~19 %) e o pior caso precisa de ~41 %: **396 MHz basta (estimado)**; 600 MHz só se `AudioProcessorUsageMax()` na placa passar de ~80 % ou faltarem blocos (custa +31 mA, ~1 h de bateria). Bateria (conta, 1000 mAh): ~5,5 h a 396 MHz.

**Medir na primeira placa:** um build de medição (`usb=serialmidi` que toque 8 notas, ligue cada efeito por 6 s e imprima `AudioProcessorUsageMax()`, os blocos e o tempo de uma passada) **não existe no sketch próprio**. Para medir, copiar `student_v4/` para uma pasta temporária, acrescentar as impressões e compilar com `usb=serialmidi`; regravar o `usb=midi` depois.

## 7 · Validação do conceito modular (só do conceito: regra geral 1)

A firmware é parametrizada por **uma constante, `STRIPS_PER_ROW` (N, réguas por fileira)**; o detalhado é N = 2 (32 teclas). Nada na **placa principal** muda com N (os mesmos 4 OUT, 2 pinos de varredura e conectores), e as fórmulas são:

- colunas = 4 N, teclas = 16 N, estágios da cadeia = 8 N, **pulsos do acesso aleatório = 8 N + 1** (a partida limpa a cadeia com 8 N + 1 pulsos); cada 16 teclas a mais = +1 régua por fileira = +4 colunas;
- **passada nominal** = colunas x ~72 us = **~288 us x N** (estimado; a taxa de colunas, e não o número delas, manda na CPU, ~19 % para qualquer N); o orçamento da leitura quente encolhe com a passada (`2,2 ms - passada`, mínimo 300 us), e a resolução de velocity sem leitura quente cai com a passada (¼ do período por cruzamento), por isso a leitura quente da coluna que se move é o que mantém a velocity;
- mapa de notas: cada módulo de 16 teclas soma 4 colunas (uma oitava); o 1º módulo extra vai para o agudo, o 2º para o grave (`EXTRA_MODULES`, `BASS_MODULES`, `noteShift` = -12 por módulo de grave; transposição fixa, o mapa do usuário fica para depois do protótipo);
- **limites do sketch** (não da placa): o conjunto de colunas quentes é uma máscara de 32 bits (4 N <= 32, N <= 8) e o mapa da EEPROM guarda a calibração de 2 bytes por tecla antes do registro (endereço 200): 4 + 32 N <= 200, **N <= 6**; acima disso mudar `EEPROM_REGISTER`.

Nada disso foi compilado com N diferente de 2 (regra geral 1: só a V4 de 32 teclas é detalhada e conferida).

## 8 · Ligação das réguas por cabo SH e mudanças que a firmware pede (R7V4 item 1)

Reli `pcb/PINOS.md` e `ELETRONICA.md` ao fim: **nenhuma mudança de pino nem de pinagem de régua foi publicada pela eletrônica na R7V4** (o estudo da ligação H ainda é dela e do design). O que a firmware pede se a pinagem mudar:
- Os pinos do MicroMod (OUT 14/15/26/27, SCAN 2/3) são nets da placa principal; **a ordem dos 6 fios dentro de um cabo SH não aparece na firmware**. Trocar a posição de OUT/CLK/DATA/+3V3/GND nos conectores das réguas, ou usar um cabo "invertido" (pino 1 ↔ 6), **não muda nenhuma linha do sketch**, desde que a eletrônica mantenha o contrato do sinal (DATA entra no SER da 1ª régua, CLK comum, OUT por fileira).
- Cuidado de eletrônica, não de firmware: um cabo ao contrário não pode levar +3V3 a um pino de sinal. A firmware põe SCAN_DATA e SCAN_CLK em saída em `setupKeys()` e as dirige em baixo logo depois; os 100 ohms em série do `PINOS.md` limitam a corrente de um engano, e os OUT são só entradas analógicas (`INPUT_DISABLE`).
- Se a pinagem passar a ter um pino de **detecção de régua** (livres hoje: 1, 5, 13 e 29-45), seria uma leitura a mais no laço: pedir à eletrônica o pino.

## Conferências feitas

| Conferência | Resultado |
|---|---|
| Compilação `teensyMM:usb=midi,speed=396`, com e sem `reed_samples` | OK, sem avisos de erro; números na seção 1 |
| `grep` de V01, eTuttino, Pocket, Viaggio, Lite, V2, V3, `ETUTTI_*`, multiplexador, piano, violão, `etutti_synth` na pasta `student_v4` (fora dos dados `reed_samples.*`) | nenhuma ocorrência |
| Pinos do sketch × `PINOS.md` (OUT 14/15/26/27, SCAN 2/3, VOL_SW 4, MIC_DET 25, CHG_STAT 0, KEEP 10, AMP_SD 12, HP_DET 17, VBAT 16, knobs 22/24 e 11/9/6, I2S, I2C 18/19) | iguais (lidos no `PINOS.md`; a firmware não tem como testar a placa) |
| `FIRST_NOTE` × `PINOS.md` R5V4 | `{57, 55, 56, 54}` (B-griff `{56, 55, 57, 53}`) |
| Tela, som, microfone, CPU, latências | **não** ouvidos nem medidos (nada rodou em placa) |

## Como testar (quando houver placa)

1. Gravar `student_v4` (`teensy:avr:teensyMM:usb=midi,speed=396`). O LED laranja e a leitura do repouso levam ~0,1-0,2 s.
2. CC 15 (teste de teclas): cada tecla responde, na ordem fileira por fileira (índice = fileira x 8 + coluna). Tecla fora = LED vermelho rápido; conferir a coluna e a ordem do registrador.
3. Medir a passada com `micros()` e `AudioProcessorUsageMax()` (build temporário, seção 6) antes de afinar `SENSOR_WAKE_US` (60 us), `HOT_FROM` e `MAX_KEY_GAP_US`.
4. Microfone: medir a tensão do pino 25 com o eletreto escolhido e com um plugue de linha, e ajustar `MIC_DET_MIN_V` / `MIC_DET_MAX_V`.
5. Menu: clique longo do seletor; girar o seletor, girar o volume, clique do volume = voltar; segurar o volume 2 s desliga.
6. Conferir no host a velocidade USB de 12 Mbit/s.

## R8V4: conferência contra a pinagem P6s (22 nov 2026)

Atende **R8V4**, ordem 3. `PINOS.md` relido no fim (versão do commit 5f6c68e; a eletrônica atualiza em paralelo, sem pino novo até aqui).

- **Pinos do Teensy: nenhum muda.** J601-J604 em P6s (1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO) só reordena o conector; OUT 14/15/26/27, SCAN_DATA 2, SCAN_CLK 3 e todos os outros ficam. O sketch não tem nada da ordem do conector: só conhece pinos, a cadeia (8 estágios por régua, 5 pulsos entre réguas, 8N+1 pulsos) e os pinos de OUT. O segundo GND (pino 4) e o DADO no pino 6 não têm função no código. **Nenhuma mudança de lógica.**
- **CLK com 330 Ω em série** (R605/R606; o do QH' na régua): constante de tempo tau = R x C. Pior caso, CLK comum às 4 fileiras com 2 réguas cada: 8 entradas de 595 (~3,5 pF) + 4 cabos (~9 pF) + trilhas = ~65 pF, tau = 330 x 65 pF = ~21 ns, subida 10-90 % de ~47 ns. O meio período do sketch é 100 ns (5 MHz): o nível chega a 99 % antes da próxima borda, e o limiar de 50 % é cruzado com ~15 ns de atraso, igual em CLK e DADO (mesmo 330 Ω), então o preparo do dado se mantém. **`SR_HALF_PERIOD_NS = 100` fica.** Cálculo, não medido; se o osciloscópio mostrar subida lenta, subir para 150 ns custa ~1 us na varredura rápida.
- **Microfone, R305 = 0 ohm:** só os 2 k internos do codec (`BIAS_RESISTOR`) em série com a cápsula, bias 3,0 V. Tensão na ponta = 3,0 - 2 k x I: 0,1 / 0,3 / 0,5 / 1 mA dão **2,8 / 2,4 / 2,0 / 1,0 V** (com 4,2 k eram 2,6 / 1,7 / 0,9 / sem 1 mA). Aberto ou linha com capacitor: 3,0 V; curto: 0 V. Limiares mantidos (`MIC_DET_MIN_V` 0,30 V, `MIC_DET_MAX_V` 2,85 V): o limite alto está 0,15 V abaixo do aberto e só 50 mV acima da cápsula de 0,1 mA, então uma cápsula que puxe menos de ~0,075 mA seria lida como ausente; o limite baixo corresponde a 1,35 mA. Só os comentários do sketch mudaram. **A medir na placa** (cápsula real, plugue de linha, tolerância do bias).
- **Compilação** só da V4 (`teensy:avr:teensyMM:usb=midi,speed=396`, com `reed_samples`): flash code 140784 + data 1239352 + headers 8404 (livre 15126532); RAM1 variáveis 105024, code 138184, padding 25656 (livre 255424); RAM2 variáveis 202272 (livre 322016). `grep` por outras versões/modelos em `student_v4` (fora de `reed_samples.*`): nenhuma ocorrência.
- Regra nova do J (nada é comprado até o protótipo fechar): o limiar do microfone fica como risco, o sketch é robusto a ele (só desliga os efeitos de voz).

## Perguntas para o design

1. **Instrumentos fora:** o sketch próprio só toca acordeão (os sete registros; sem piano, baixo, violão nem synth). Está certo para a V4? A página V4 só precisa dos CCs listados nas seções 2 a 4.
2. **Build de medição:** não há build de medição no sketch próprio. Quer que o sketch próprio tenha uma chave de medição da CPU , ou basta o procedimento da seção 6 quando houver placa?
3. **Limite de N:** o sketch aceita N <= 6 réguas por fileira (EEPROM). É folga suficiente para a validação do conceito modular, ou o design quer o mapa da EEPROM já reorganizado?
4. **Ligação H:** se o estudo escolher um cabo com pinagem invertida ou um pino de detecção de régua, a firmware só precisa do pino novo (seção 8). Há previsão de pino de detecção?
5. **Pendentes das revisões anteriores, que dependem de placa ou decisão:** limiares do microfone (R6V4), padrão do headset (que cápsula?), EQ do alto-falante de ouvido (300 Hz / -6 dB é de conta), supressor de microfonia (primeiro modelo, não ouvido), modos do harmonizador (R7V4 item 4: ficam como estão até haver instrumento), espanhol na tela (depois do protótipo), página V4 (os CCs de voz existem só no sketch), mapa de notas do usuário (CC e EEPROM) e notas até E7 (as amostras cobrem bem até a tecla 79).
6. **R8V4, microfone:** com R305 = 0 ohm uma cápsula de menos de ~0,075 mA não é detectada. Para a cápsula escolhida, qual a corrente típica (datasheet)? Se for menor, subir `MIC_DET_MAX_V` (ex.: 2,92 V) estreita a margem contra o jack aberto (3,0 V).
