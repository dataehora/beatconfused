# eTutti Student V4 · firmware e som (SPEC R10V4)

22 nov 2026. **Atualizado para a R10V4 (ordens 3 e 4, seção "R10V4" abaixo; as demais seções já refletem 4 × R8 e os dois tipos de microfone).** Atende a R7V4, regra geral 2 (tarefa 3 da tabela): a Student V4 tem sketch próprio, `etutti/firmware/student_v4/`**, só com o caminho da V4 modular de **32 teclas**. O sketch compartilhado `etutti/firmware/etutti_synth/` fica congelado (não foi editado, não é compilado nem conferido aqui). O texto das revisões R1V4 a R6V4 deste arquivo (estudos de capacidade, contas, discussões, tabelas por tamanho) foi consolidado abaixo; o histórico completo está no git (commits das R1V4 a R6V4).

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

**Hardware** (`PINOS.md`): réguas de 4 teclas (R10V4: **uma R8 por fileira**, 8 TMAG5253BA3 + um 74HC595 usando os 8 estágios; a R4, de 4 sensores, só existe nos tamanhos de 48 e 80 teclas e fica sempre na ponta do agudo). Quatro linhas analógicas **OUT_R1..R4 = pinos 14, 15, 26, 27**, `SCAN_DATA` = 2, `SCAN_CLK` = 3 (comuns às 4 fileiras, SRCLK e RCLK juntos). Um "1" andando na cadeia liga **uma coluna** (4 sensores, um por fileira); as saídas desligadas ficam em alta impedância. O sketch segue o contrato: a saída travada **atrasa 1 pulso**; **coluna = estágio** (a R8 usa QA..QH; sem estágio morto entre colunas: a próxima coluna está sempre a 1 pulso); na partida, `8N + 1` pulsos com DATA = 0 zeram a cadeia (N = réguas por fileira; 1 com 32 teclas = 9 pulsos); acesso aleatório = padrão de `8N` bits + 1 pulso = 9; CLK a 5 MHz (`SR_HALF_PERIOD_NS` 100).

**32 teclas = 4 × R8 (uma por fileira), 8 colunas, 4 fileiras de 8 teclas, 9 pulsos de acesso aleatório.** Mapa de notas (3 semitons por coluna, `FIRST_COL` = 0 em todas):

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
| Passada nominal (8 colunas x ~72 us), sem tecla quente | **~0,58 ms (1,7 kHz)**, estimado (igual à de 2 × R4: o número de colunas não mudou) |
| Leitura quente | ~83 us (outra coluna; 9 pulsos = ~1,8 us contra ~3,4 us dos 17 de antes), ~56 us (a mesma), estimado |
| Erro de velocity (± unidades, ¼ do período por cruzamento): batida de 1 / 2 / 5 / 10 ms | passada sozinha 5,9 / 2,9 / 1,2 / 0,6; leitura quente de 1 coluna 0,6 / 0,3 / 0,1 / 0,1; de 2 colunas (acorde) 1,7 / 0,9 / 0,3 / 0,2 |
| CPU da varredura | **~19 %** (13-14 us de trabalho a cada 72 us), estimado |

O mais rápido que um dedo toca fica em 3-5 ms, onde a leitura quente dá ±0,1 a ±0,7. **Calibração:** a EEPROM guarda a amplitude de cada tecla (CC 14 ou menu CALIBRAR esquece e reaprende). **Erro de assentamento:** a coluna lida 60 us após o EN tem resíduo de ~1,8 % da diferença para a anterior (estimado; com 90 us, ~0,25 %): **(conferir na primeira placa)**.

## 3 · Som

Acordeão de 8 vozes, quatro palhetas por nota: 16' (cassotto), 8' M1 (aberta), 8' M2 (cassotto, desafinada pelo "molhado", CC 27) e 4' (piccolo), escolhidas por **sete registros** (CC 26): L Bassoon, ML Bandoneon, MM Violin (padrão), MH Oboe, H Piccolo, LH Organ, M Clarinet. Palhetas **amostradas** (`reed_sampler.h`: quatro fileiras de amostras com laço, interpolação Catmull-Rom, passa-baixas de brilho) quando `reed_samples.*` existem, senão tabelas aditivas **limitadas em banda** (nunca dente-de-serra ou quadrada crua). **Velocity = pressão do fole**: 24 dB de volume e, nas amostras, brilho (passa-baixas de 700 Hz a 16 kHz, pelo menos 3x a nota); medido 27 dB entre as velocities 4 e 127 numa G3. Depois: filtro de tom (**biquad**, nunca o SVF; CC 74), reverb leve (CC 91), volume (ganho antes do I2S: o MAX98357A não tem volume próprio; CC 7). Equilíbrio das fileiras (`SAMPLED_REED_GAIN`) e comprimento do laço são **primeiros palpites**, a ouvir na placa.

**Alto-falante de estudo (EQ).** O MAX98357A e o SGTL5000 recebem o mesmo fluxo I2S; por isso "só no alto-falante" = **sem plugue no OUT (HP_DET)**. Sem plugue, o fluxo passa por 4 biquads (passa-altas de 4ª ordem Butterworth a 300 Hz = 24 dB/oitava, corte de -6 dB em 1 kHz, Q 1,2); com plugue o equalizador é desconectado (custo 0). CC 105 liga/desliga (padrão ligado), 106 corte (150 a 450 Hz), 107 pico de 1 kHz (0 a -12 dB). No padrão a G3 (196 Hz) sai ~15 dB mais baixa (conta em numpy: -38,2 dB a 100 Hz, -15,1 a 196, -3,5 a 300, -6,0 a 1 kHz). **Ponto de partida de conta, não ouvido.** +~0,45 % de CPU só quando o alto-falante é a saída.

## 4 · Voz (microfone no IN)

**Regra (R10V4):** os efeitos de voz só funcionam com **um microfone no IN (J302), eletreto com alimentação de plug-in ou dinâmico, detectado ou declarado no menu**; sem ele as páginas Voz e Captação e as linhas Saída voz e Teclas somem do menu e `voiceBlocked()` cala tudo da voz (CPU 0), a tela mostra `sem mic`; os ajustes voltam ao plugar. Só pelo jack de 3,5 mm (adaptadores, phantom de 48 V e microfone de PC com bias no anel ficam fora). Detecção, bias, ganho e contas: seção "R10V4" abaixo. **VOL_SW = pino 4** (R6V4; o 25 é MIC_DET).

**Saída:** a voz sai **só no fone/AUX** por padrão; o alto-falante é opção do menu (CC 96) com aviso de microfonia na tela, e **nunca é salvo ligado**.

**Cadeia** (`voice_fx.h`): `VoiceInput` (passa-altas, ganho, notches, **expansor** com limiar/razão/ataque/retenção/soltura) → vocoder de 10 bandas (teclado de portadora) / 4 deslocadores `AudioEffectGranular` / rastreador de afinação **YIN** / eco (60..740 ms, realimentação até 0,85) / FFT de 1024 pontos do **supressor de microfonia** (notches de -18 dB, Q 30, até 4, desligado até o menu ligar) → mistura → reverb comum. **Padrão de fábrica por tipo de microfone** (conta, não ouvido; R10V4: eletreto 9 dB, dinâmico 28 dB): limiar ~550, razão forte, ataque 1,2 ms, retenção ~78 ms, soltura ~117 ms, passa-altas 167 Hz; a ação "Mic padrão" do menu volta a estes valores (e ao ganho do tipo em uso). Conta de nível: tabela da seção R10V4 (voz cantada a 2 cm, ~105 dB SPL); o alto-falante a ~30 cm chega 22 dB abaixo e fica sob o limiar. YIN: simulado em numpy, erro máx. 13 cents com vibrato, nenhum erro de oitava (voz real **não** testada).

**Harmonizador que segue a tecla** (CC 95 liga, **108 modo** (valor/32: 0 Exato, 1 Ajuda, 2 Intervalo), **109** força da ajuda, **110** vozes (>= 64 = 4, padrão 3), 97 oitava perto/exata; CC 19 = intervalo fixo quando não segue): **Exato** (cada nota segurada ganha um deslocador que põe a voz exatamente nela), **Ajuda** (um deslocador puxa a voz parte do caminho para a nota mais próxima, até 3 semitons; a seca faz fade para fora ~40 ms), **Intervalo** (a voz fica natural; cada outra nota ganha o intervalo até a nota de referência; uma tecla sozinha = silêncio). Sem voz com afinação por 300 ms ou sem nota, a harmonia silencia. Latência (estimada): harmonia ~25-30 ms atrás da seca; tecla nova ouvida em ~40 ms; seguir uma mudança de nota do cantor ~60 ms.

**CCs de voz** (só no sketch; a página V4 muda `script.js` junto quando existir): 16 seca, 17 vocoder, 18 harmonizador, 19 intervalo, 76 eco, 77 tempo, 78 realimentação, 80 reverb da voz, 81 limiar, 82 ganho do microfone (0 a 60 dB no codec: pré-amplificador 0/20/30/40 dB + ADC 0 a 22,5 dB; era 20 a 52), 111 tipo de microfone (valor/43: 0 auto, 1 eletreto, 2 dinâmico), 83 nível do teclado, 84 ataque, 89 retenção, 90 soltura, 92 passa-altas, 93 razão, 94 supressor, 95, 96, 97, 105-107 (EQ), 108-110. Tudo começa desligado.

## 5 · Tela, menu, energia

**OLED SSD1306 128 x 64** (J401, I2C 0x3C compartilhado com o codec), driver próprio com buffer de 1 KB enviado em pedaços de 16 bytes, uma por passada do `loop()` (a varredura em interrupção não é atrasada pelo I2C). Fonte 5 x 10 com minúsculas e acentos (~1,6 KB), texto em UTF-8, **português e inglês** (Sistema > Idioma, gravado na hora na EEPROM, endereço 250; padrão português). Para um idioma novo: código no enum de `ui_text.h`, nome em `LANG_NAME` e um texto a mais em cada `{...}` (o que faltar cai para o inglês); espanhol fica para depois do protótipo (R7V4 item 4). Telas desenhadas com a fonte real em `img/tela_pt.png` e `img/tela_en.png` (`tools/oled_font/render_screens.py`), **não vistas num SSD1306**.

**Knobs** (pinos `PINOS.md`: volume A/B 22/24, clique 4; seletor A/B 11/9, clique 6; `ENC_STEPS_PER_DETENT` 2, EC11E18244A5): volume gira = volume (CC 7 de volta); **clique do volume segurado 2 s liga/desliga** (KEEP = pino 10; o hardware faz o liga/desliga, a firmware só lê e segura o KEEP); seletor gira = os sete registros (CC 26 de volta, LED verde piscando até guardar), clique depois de girar = guarda o registro para a próxima partida (EEPROM 200), clique sem girar = volta ao MM seco; **clique longo do seletor (0,7 s) abre o menu**, o curto age ao soltar. No menu: seletor move o cursor, clique entra / troca / executa, volume gira o valor, clique do volume volta; fecha sozinho em 30 s.

```
Menu  ├ Voz (só com microfone): seca, vocoder, harmonizador, modo, intervalo/força, oitava, vozes, eco (nível, tempo, realimentação), reverb da voz
      ├ Captação (só com microfone): ganho, limiar, razão, ataque, retenção, soltura, passa-altas, Mic padrão, antimicrofonia, limpar notches
      ├ Saída: volume, saída da voz (fone/AUX ou + alto-falante, com aviso), nível das teclas, EQ do alto-falante, corte, pico de 1 kHz
      ├ Som: registro, reverb, curva de velocity
      └ Sistema: salvar, zerar voz, calibrar, teste de teclas, tipo de microfone (Auto / Eletreto / Dinâmico), idioma
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

## 7 · Validação do conceito modular (só do conceito: regra geral 1; R10V4)

A firmware é parametrizada por **duas constantes por fileira, `RULERS_R8` e `RULERS_R4`**; o detalhado é 1 R8 e nenhuma R4 (32 teclas). Colunas = 8 R8 + 4 R4, estágios da cadeia = 8 (R8 + R4), **coluna = estágio** (a R4 é sempre a última régua da fileira, no agudo: seus estágios QE..QH sobram depois da última coluna e o "1" nunca cruza um estágio morto). Nada na placa principal muda.

| Combinação | Colunas | Estágios | Pulsos do acesso aleatório | Passada nominal (~72 us/coluna) |
|---|---:|---:|---:|---:|
| R8 (32) | 8 | 8 | 9 | ~0,58 ms |
| R8 + R4 (48) | 12 | 16 | 17 | ~0,86 ms |
| R8 + R8 (64) | 16 | 16 | 17 | ~1,15 ms |
| R8 + R8 + R4 (80) | 20 | 24 | 25 | ~1,44 ms |

Só os números mudam. **Limites do sketch:** a máscara de colunas quentes é de 32 bits (até 32 colunas; 20 cabem) e o mapa da EEPROM guarda 2 bytes por tecla a partir do endereço 4, antes do registro (endereço 200): 4 + 2 x teclas <= 196, ou seja **até 96 teclas** (80 cabem; `EEPROM_REGISTER` só muda acima disso). O mapa de notas soma uma oitava (4 colunas) por módulo: o 1º extra vai para o agudo, o 2º para o grave (`noteShift` -12 por módulo de grave): 48 = F#3-F#6, 64 = F#2-F#6, 80 = F#2-F#7. **Conferido por compilação** (cópia temporária com 2 R8 + 1 R4 e 80 teclas): compila, +2,6 KB de RAM1; o sketch entregue só tem as duas constantes.

## 8 · Ligação das réguas por cabo SH e mudanças que a firmware pede (R7V4 item 1)

Reli `pcb/PINOS.md` e `ELETRONICA.md` ao fim: **nenhuma mudança de pino nem de pinagem de régua foi publicada pela eletrônica na R7V4** (o estudo da ligação H ainda é dela e do design). O que a firmware pede se a pinagem mudar:
- Os pinos do MicroMod (OUT 14/15/26/27, SCAN 2/3) são nets da placa principal; **a ordem dos 6 fios dentro de um cabo SH não aparece na firmware**. Trocar a posição de OUT/CLK/DATA/+3V3/GND nos conectores das réguas, ou usar um cabo "invertido" (pino 1 ↔ 6), **não muda nenhuma linha do sketch**, desde que a eletrônica mantenha o contrato do sinal (DATA entra no SER da 1ª régua, CLK comum, OUT por fileira).
- Cuidado de eletrônica, não de firmware: um cabo ao contrário não pode levar +3V3 a um pino de sinal. A firmware põe SCAN_DATA e SCAN_CLK em saída em `setupKeys()` e as dirige em baixo logo depois; os 100 ohms em série do `PINOS.md` limitam a corrente de um engano, e os OUT são só entradas analógicas (`INPUT_DISABLE`).
- Se a pinagem passar a ter um pino de **detecção de régua** (livres hoje: 1, 5, 13 e 29-45), seria uma leitura a mais no laço: pedir à eletrônica o pino.

## R10V4 · 4 × R8 e microfones (22 nov 2026)

Atende **R10V4**, ordens 3 e 4. `PINOS.md` relido: a R8V4 não mudou nenhum pino; ele ainda descreve a régua de 4 posições com 4 estágios mortos, o que esta seção supera com o contrato abaixo (pedido à eletrônica, pergunta 9). Compilação só da V4, `teensy:avr:teensyMM:usb=midi,speed=396`, com `reed_samples`: **flash** code 141 360 + data 1 239 352 + headers 8 852 (livre 15 125 508 B); **RAM1** variáveis 105 024, code 138 760, padding 25 080 (livre 255 424); **RAM2** variáveis 202 272 (livre 322 016). `grep` por microfone de marca, fonte elevadora de bias e por V01/eTuttino/Pocket/Viaggio/Lite/V2/V3/`ETUTTI_*` em `student_v4` (fora de `reed_samples.*`): nenhuma ocorrência.

### Teclado: 4 × R8, 32 teclas

- **Contrato de varredura que o sketch segue:** uma R8 por fileira, os 8 estágios do 595 = 8 colunas (QA = coluna 0, a mais perto da placa e do grave, ... QH = coluna 7); DATA entra no SER da R8, CLK comum; **9 pulsos** para o acesso aleatório e para a partida (8 + 1), **1 pulso** para a coluna seguinte. Sem estágio morto entre colunas, sem junção régua-régua.
- **Mudanças no código:** `STRIPS_PER_ROW` virou `RULERS_R8` (1) e `RULERS_R4` (0); `LAYOUT_COLS` = 8 R8 + 4 R4; `SR_STAGES` = 8 por régua; `srSelect()` perdeu o salto de 5 pulsos e a conta de estágio `8(c/4) + c%4` (estágio = coluna); `V4_KEYS` = 32 (`static_assert`); `EEPROM_MAGIC` + 1 (a ordem física das colunas mudou).
- **Mapa das 32 teclas (não mudou):** `FIRST_NOTE = {57, 55, 56, 54}`; fileira 1 A3 C4 D#4 F#4 A4 C5 D#5 F#5, fileira 2 G3-E5, fileira 3 G#3-F5, fileira 4 F#3-D#5; conjunto **F#3-F#5** (25 notas); índice da tecla = fileira x 8 + coluna (CC 15).
- **Tempos (estimados, nada rodou em placa):** passada nominal 8 x ~72 us = **~0,58 ms** (a mesma de 2 x R4: o número de colunas não mudou); acesso aleatório 9 pulsos a 5 MHz = ~1,8 us (eram 17 = ~3,4 us), leitura quente ~83 us em outra coluna; CPU da varredura **~19 %** (a mesma; o trabalho por coluna caiu ~1 us, dentro do erro da estimativa); velocity com a mesma resolução (erro de +-5,9 / 2,9 / 1,2 / 0,6 unidades para batida de 1 / 2 / 5 / 10 ms sem leitura quente; +-0,6 / 0,3 / 0,1 / 0,1 com ela). Espera do sensor (60 us) e CLK de 5 MHz (330 ohm em série, R8V4) continuam.
- **48 / 64 / 80:** seção 7. Só mudam `RULERS_R8` e `RULERS_R4`, com a R4 sempre no fim da cadeia.

### Microfones: eletreto e dinâmico pelo J302

**O que cada tipo pede da placa e do firmware**

| | Eletreto (plug-in, 2-5 V) | Dinâmico (150-600 ohm) |
|---|---|---|
| Bias do SGTL5000 | **ligado**: MIC_BIAS 3,0 V atrás de 2 k internos (`BIAS_RESISTOR` 2 k, `BIAS_VOLT` 3,0 V; R305 = 0 ohm) | **desligado** (`BIAS_RESISTOR` = 0, que desliga o bloco), só se o tipo for declarado no menu |
| MIC_DET com o bias ligado | 2,8 / 2,4 / 2,0 / 1,0 V para 0,1 / 0,3 / 0,5 / 1 mA | 3,0 x Rc / (2 k + Rc): 150 / 300 / 600 ohm = **0,21 / 0,39 / 0,69 V** |
| Ganho de fábrica (CC 82) | 9 dB | 28 dB (0,45 mV/Pa pede 34; 1,7 mV/Pa pede 22) |

**Bias ligado por engano numa bobina de 150-600 ohm: não faz mal.** Corrente de 1,40 / 1,30 / 1,15 mA e potência na bobina de 0,29 / 0,51 / 0,80 mW (150 / 300 / 600 ohm), muito abaixo do que o fio de uma bobina aguenta; o CC não chega ao codec (C309, 1 uF). Custo: o sinal cai 0,6 / 1,2 / 2,3 dB (a carga de 2 k contra a bobina) e entram ~0,1 uV de ruído do resistor de bias. Desligar o bias melhora 1-2 dB, mas não é crítico; por isso o modo Auto **nunca desliga o bias** (o detector precisa dele ligado) e só o tipo **Dinâmico declarado no menu** o desliga.

**Detecção (MIC_DET, pino 25, R306 100 k + C311 100 nF): distingue com segurança só os extremos.**
- `v >= 2,85 V`: nada, ou plugue de linha com capacitor. `v <= 0,10 V`: curto ou fonte de baixa impedância (< ~70 ohm). Os dois = **sem microfone**. O limite de curto desceu de 0,30 para 0,10 V para a bobina de 150 ohm (0,21 V) não ser lida como curto.
- De 0,10 a ~0,85 V é a faixa da bobina dinâmica; acima de ~0,95 V, eletreto (limiares e histerese da eletrônica, R10V4). As faixas **se tocam**: uma bobina de 600-700 ohm, a tolerância do resistor interno (se ele variar de 1,6 a 2,4 k, 600 ohm lê 0,82 a 0,60 V) e um eletreto que puxe mais de 1 mA caem na mesma região. **O tipo não é confiável só pela tensão**, então existe o item **"Tipo mic" (Auto / Eletreto / Dinâmico)** em Sistema, em PT/EN, gravado na EEPROM no mesmo instante (endereço 256, com o ganho de cada tipo); o CC 111 faz o mesmo.
- **Auto** (padrão): bias ligado; < 0,85 V = dinâmico, > 0,95 V = eletreto (histerese 0,85/0,95, igual ao `PINOS.md` R10V4; antes 0,60/0,80), só para escolher o ganho de fábrica; os efeitos de voz valem nos dois. **Eletreto:** qualquer carga entre 0,10 e 2,85 V conta como microfone. **Dinâmico:** o bias desliga e a leitura cai a 0 V, então **o detector fica cego e o tipo declarado vale como "microfone presente"** (tirar o plugue não é percebido; a voz só é cortada ao trocar o tipo). Religar o bias por alguns ms para espiar daria um estalo no sinal: não foi feito.
- Limiares são **conta, a medir na primeira placa** com uma cápsula, uma bobina e um plugue de linha (`MIC_SHORT_V`, `MIC_DYN_UP_V`, `MIC_DYN_DOWN_V`, `MIC_OPEN_V`).

**Ganho e ruído (conta).** Premissas ainda "conferir" no datasheet: fundo de escala do ADC 1,0 Vrms e ruído de entrada do ADC 31 uV a 0 dB. Voz cantada a 1-3 cm; referência de 2 cm: suave 95 dB SPL (1,8 Pa), normal 105 (3,5 Pa), forte 115 (11 Pa); alvo: normal em **~-22 dBFS rms** (picos ~12 dB acima; forte +10 dB ainda fecha em ~0 dBFS de pico). **Reconciliação com a eletrônica (alvo -18 dBFS, 39 / 30,5 / 20 dB):** a diferença de ganho vem quase toda do alvo (4 a 8 dB); a conta dela implica fundo de escala ~1,1 Vrms, que bate com o 1,0 Vrms usado aqui (a "0,75 mV" da mensagem parece ser 0,75 Vrms; mudaria < 3 dB). Com -18 dBFS um canto forte (+10 dB) estoura (picos +4 dBFS); com -26 fica baixo para o expansor/YIN. Adotado -22; o usuário ajusta de 0 a 60 dB. A diferença restante do eletreto (9 contra 20 dB) é de sensibilidade: aqui -42 dBV/Pa (7,9 mV/Pa); com uma cápsula de ~-50 dBV/Pa o padrão ficaria ~8 dB baixo (menu). Níveis em dBFS rms:

| Microfone, ganho | suave | normal | forte | ruído equiv. na entrada | SNR normal / suave |
|---|---:|---:|---:|---:|---:|
| dinâmico 0,45 mV/Pa, **34 dB** | -27,9 | -21,9 | -12,0 | 0,6 uV | 68 / 62 dB (a eletrônica dá 71 ideal e 53 com 3 uV de ruído do pré, suposição dela; sem esse ruído aqui) |
| dinâmico 1,7 mV/Pa, **22 dB** | -28,4 | -22,4 | -12,4 | 2,5 uV | 66 / 60 dB |
| dinâmico, padrão **28 dB**, com 0,45 mV/Pa | -33,9 | -27,9 | -18,0 | 1,3 uV | 62 / 56 dB |
| dinâmico, padrão **28 dB**, com 1,7 mV/Pa | -22,4 | -16,4 | -6,4 | 1,3 uV | 74 / 68 dB |
| eletreto -42 dBV/Pa, **9 dB** | -28,0 | -22,0 | -12,0 | 11 uV | 68 / 62 dB |

(Ruído = ADC com o ganho dado + térmico de uma bobina de 300 ohm em 20 kHz. O ruído da cápsula do eletreto, tipicamente 58-62 dB(A) de SNR a 94 dB SPL, domina e não está na conta.) Com o **ganho máximo do SGTL5000 (62,5 dB: 40 dB + 22,5 dB)** o dinâmico de 0,45 mV/Pa daria -3 dBFS a 105 dB SPL: **sobra ganho**; o limite real é o ruído da própria bobina (0,31 uV, ~63 dB de SNR a 94 dB SPL), não o codec. **Não falta ganho: nenhuma mudança de placa por isso.** A faixa do menu passou a 0-60 dB (antes 20-52, que não chegava aos 6 dB do eletreto).

**Resolvido pela eletrônica (R10V4): C310 não montado** (pad mantido para 220-470 pF opcional) e, pela Tabela 29, `BIAS_RESISTOR` = 0 deixa o MIC_BIAS em alta impedância; o sketch silencia a voz por 150 ms ao trocar o bias. O texto a seguir é o cálculo que motivou a pergunta (vale só com o C310 montado). Com **R305 = 0 ohm**, o **C310 (100 nF no MIC_BIAS) fica direto na ponta do jack**. Para o eletreto ele fica em paralelo com os 2 k da carga: passa-baixas de 1/(2 pi x 2 k x 100 nF) = **~800 Hz** (-4 dB a 1 kHz, -14 dB a 4 kHz, -22 dB a 10 kHz). Para o dinâmico é um shunt de 100 nF sobre a bobina: corte de 10,6 / 5,3 / 2,7 kHz para 150 / 300 / 600 ohm (-2 dB a 4 kHz com 300 ohm, -5 dB com 600). **Cálculo, a medir.** Se for assim, o C310 não deve ser montado com R305 = 0 ohm (ou o R305 volta a >= 1 k), decisão da eletrônica; o datasheet mostra o capacitor no MIC_BIAS **com** o resistor externo em série. Também não se sabe se o pino fica em alta impedância com o bloco desligado (**a medir**): se ele puxasse para 0 V, o tipo Dinâmico em bias desligado poria a ponta em curto no CC e no sinal; o remédio é uma linha do sketch (`micBiasWanted()` sempre verdadeiro).

**Telas do menu (PT / EN).** Sistema ganha a linha **"Tipo mic" / "Mic type"** com **Auto / Eletreto / Dinâmico** (Auto / Electret / Dynamic); a ação "Mic headset" virou **"Mic padrão" / "Mic default"** e volta ao ganho do tipo em uso; "Ganho mic" mostra 0 a 60 dB. Os PNG `img/tela_pt.png` e `img/tela_en.png` **não foram regerados**.

### Pendências

- Tudo é conta; nada foi ouvido nem medido numa placa. A medir: limiares MIC_DET, o MIC_BIAS desligado, o efeito do C310, ruído e nível reais dos dois tipos, tempo de passada e CPU.
- `PINOS.md` ainda trata a régua como R4 com estágios mortos e cita o limiar de curto de 0,30 V; o sketch já segue 8 estágios e 0,10 V.

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

## R11V4 · OLED real e OUT (22 nov 2026)

Atende **R11V4**, item 1 (parte da firmware). Quando esta seção foi escrita, `ELETRONICA.md` e `FIT_CHECK.md` ainda **não traziam o modelo de OLED escolhido** (só o módulo assumido: vidro 26,7 x 19,26, área ativa 21,74 x 10,86 mm, janela 24 x 13, 4 furos; isso é o 0,96" 128 x 64, **SSD1306**). Reler quando a escolha entrar.

- **Controlador, resolução, endereço, tensão (premissa até a escolha):** SSD1306, 128 x 64, I²C 0x3C, 3,3 V no J401 (pinos 1 +3V3, 2 GND, 3 SDA, 4 SCL), varredura horizontal em páginas de 8 linhas, girado 180° (`OLED_ROTATION = 2`). A área ativa de 21,74 mm / 128 px = 0,17 mm por pixel: a fonte 5 x 10 (com acentos) fica com **0,85 x 1,70 mm por caractere** e o menu de 21 colunas ocupa 17,8 mm dos 21,74. Como a resolução e a área ativa **não mudaram**, `img/tela_pt.png` e `img/tela_en.png` continuam valendo (não regerados).
- **O que mudou no sketch:** nova chave `OLED_SH1106` (padrão 0 = SSD1306; `-DOLED_SH1106=1` ou editar a linha). Com 1: coluna inicial 2 (vidro de 128 colunas num controlador de 132), sem o comando de modo de endereçamento, DC-DC interno ligado (0xAD 0x8B) e o quadro enviado página por página (0xB0+página, coluna baixa/alta) em vez da janela de colunas. O menu e as telas são os mesmos. Se o modelo escolhido for de outra resolução (ex.: 128 x 32), é preciso redesenhar as telas (pedir antes à firmware).
- **OUT / R4 / cascata:** o sketch **não depende** de OUT nem de R4 para a V4 de 32 teclas: `RULERS_R8 = 1`, `RULERS_R4 = 0` por fileira, a cadeia termina na R8 (a firmware só lê as 4 linhas OUT das fileiras e o DATA/CLK da placa; nenhum pino ou conector de saída da cadeia é usado). `RULERS_R8`/`RULERS_R4` ficam como parâmetros do conceito modular, sem efeito no uso normal.
- **Compilação** (só a V4, `teensy:avr:teensyMM:usb=midi,speed=396`): flash code 141488 + data 1239352 + headers 8724 (livre 15125508); RAM1 variáveis 105024, code 138888, padding 24952 (livre 255424); RAM2 variáveis 202272 (livre 322016). Compilou com `OLED_SH1106` 0 e 1 (o tamanho reportado é igual; a variante 1 só não foi gravada nem testada em tela). Nada foi gravado.

**R11V4, OLED escolhido (Adafruit 326, SSD1306 128 x 64, 3,3 V):** a rotação de 180° do driver (`OLED_ROTATION = 2` = segmento A0 + COM C0, como `setRotation(2)`) já atende a orientação "B"; `OLED_SH1106 = 0`. Endereço conforme `PINOS.md`: o sketch tenta **0x3D** (fábrica, sem jumper) e, se não responder, **0x3C** (jumper fechado). Layout e telas inalterados. Recompilado: ver números na seção acima (código do driver só ganhou o teste de endereço).

## R12V4 · conferência do sketch contra a placa (23 nov 2026)

Atende **R12V4**, item 3. Novo `firmware_check.py` (KiCad python; lê `kicad/student_v04_roteada.kicad_pcb` quando existe, senão `kicad/student_v04.kicad_pcb`; redes e pinos não mudam com o roteamento) e escreve `firmware_check.json`.

- **Pinos: 25/25 conferidos, 0 divergências.** Cada pino do sketch (OUT_R1..R4 = 14/15/26/27, SCAN_DATA 2, SCAN_CLK 3, VOL_A/B 22/24, VOL_SW 4, SEL_A/B/SW 11/9/6, KEEP 10, AMP_SD 12, VBAT_S 16, HP_DET 17, CHG_STAT 0, MIC_DET 25) e os fixos da biblioteca de áudio (I2S 7/8/20/21/23, I²C 18/19) é comparado em três lugares: `PINOS.md`, a rede do pad correspondente do J101 na placa e a do netlist do esquema (`pcb/build/student_v04_netlist.net`). Conferido nas duas placas (posicionada e a roteada em andamento). Nenhum pino repetido. Os dois LED do sketch (13 e 5) caem em pads sem rede (o 13 é o LED azul do módulo; a placa não tem LED): sem divergência, nenhum sinal usa esses pinos.
- **Varredura:** 4 × R8 por fileira (`RULERS_R8 = 1`, `RULERS_R4 = 0`, `static_assert` de 32 teclas), nenhum OUT/R4 usado; `SR_STAGES = 8`; o script simula o `srSelect()` numa cadeia de 8 estágios com SRCLK e RCLK juntos: a coluna c acende o estágio c, **9 pulsos** (8N+1, N = 1), e o `srClear()` também 9. `FIRST_NOTE` = {57, 55, 56, 54} (C) e {56, 55, 57, 53} (B), `FIRST_COL` = 0, como no `PINOS.md`.
- **OLED:** SSD1306 128 x 64 (`0xA8 0x3F`), endereço 0x3D e, se não responder, 0x3C; imagem girada 180° (`OLED_ROTATION = 2` = segmento 0xA0 + COM 0xC0); `OLED_SH1106 = 0`. J401 na placa: 1 GND, 2 +3V3, 3 SDA, 4 SCL (ordem Qwiic), SDA/SCL nos pads do Teensy 18/19.
- **Microfone:** menu "Tipo mic" (Auto / Eletreto / Dinâmico); `micSetup()` escreve CHIP_MIC_CTRL (0x002A) com 0x0170 (bias 2 kohm, 3,0 V) ou 0x0070 (bias desligado) mais o ganho do pré-amplificador. Limiares: curto <= 0,10 V, dinâmico < 0,85 V (volta a eletreto acima de 0,95 V), eletreto até 2,85 V, nada >= 2,85 V. Esquema/placa: R305 = 0 ohm (MIC_BIAS-MIC_J), **C310 "nao montar"**, R306 100 kohm (MIC_J-MIC_DET), C311 100 nF no MIC_DET (filtro de 10 ms). Com o bias de 2 kohm sozinho: eletreto de 0,1/0,3/0,5/1 mA = 2,8/2,4/2,0/1,0 V; bobina de 150/300/600 ohm = 0,21/0,39/0,69 V, coerente com as faixas do sketch. **Nenhuma correção no sketch.**
- **Compilação** (só a V4, `teensy:avr:teensyMM:usb=midi,speed=396`): flash code 141552 + data 1239352 + headers 8660 (livre 15125508); RAM1 variáveis 105024, code 138952, padding 24888 (livre 255424); RAM2 variáveis 202272 (livre 322016).
- **Observação para a eletrônica (não é do sketch):** o `PINOS.md` (linhas dos pinos 2 e 3) ainda diz "por 100 ohm" para SCAN_DATA/SCAN_CLK; a placa tem R605/R606 de **330 ohm** (R8V4). O sketch independe do valor (meio período de 100 ns, tau ~21 ns).
- **Pendente:** reler o script quando a placa roteada for aceita (basta rodar `firmware_check.py`); nada de bancada (nada foi comprado).

## Perguntas para o design

1. **Instrumentos fora:** o sketch próprio só toca acordeão (os sete registros; sem piano, baixo, violão nem synth). Está certo para a V4? A página V4 só precisa dos CCs listados nas seções 2 a 4.
2. **Build de medição:** não há build de medição no sketch próprio. Quer que o sketch próprio tenha uma chave de medição da CPU , ou basta o procedimento da seção 6 quando houver placa?
3. **Limite de N:** o sketch aceita N <= 6 réguas por fileira (EEPROM). É folga suficiente para a validação do conceito modular, ou o design quer o mapa da EEPROM já reorganizado?
4. **Ligação H:** se o estudo escolher um cabo com pinagem invertida ou um pino de detecção de régua, a firmware só precisa do pino novo (seção 8). Há previsão de pino de detecção?
5. **Pendentes das revisões anteriores, que dependem de placa ou decisão:** limiares do microfone (R6V4), padrão do headset (que cápsula?), EQ do alto-falante de ouvido (300 Hz / -6 dB é de conta), supressor de microfonia (primeiro modelo, não ouvido), modos do harmonizador (R7V4 item 4: ficam como estão até haver instrumento), espanhol na tela (depois do protótipo), página V4 (os CCs de voz existem só no sketch), mapa de notas do usuário (CC e EEPROM) e notas até E7 (as amostras cobrem bem até a tecla 79).
6. **R8V4, microfone:** com R305 = 0 ohm uma cápsula de menos de ~0,075 mA não é detectada. Para a cápsula escolhida, qual a corrente típica (datasheet)? Se for menor, subir `MIC_DET_MAX_V` (ex.: 2,92 V) estreita a margem contra o jack aberto (3,0 V).
7. **R10V4, C310 (respondida pela eletrônica: não montado; bias desligado = alta impedância):** com R305 = 0 ohm o C310 (100 nF no MIC_BIAS) fica na ponta do jack e corta o agudo do eletreto (~800 Hz) e o da bobina dinâmica (2,7-10 kHz). A eletrônica pode tirar o C310 (ou pôr o R305 de volta em >= 1 k)? E, pelo datasheet, o MIC_BIAS fica em alta impedância com `BIAS_RESISTOR` = 0?
8. **R10V4, tipo de microfone:** o modo Auto deixa o bias sempre ligado (o detector precisa dele) e só o tipo Dinâmico declarado o desliga e fica cego ao plugue. Serve, ou o design prefere bias sempre ligado também no Dinâmico (perda de 1-2 dB, nenhum risco de ponta em curto)?
9. **R10V4, PINOS.md:** a eletrônica atualiza para 8 estágios por R8 (coluna = estágio, 9 pulsos) e para o limiar de curto de 0,10 V?
10. **R10V4, sensibilidade:** os dois dinâmicos de referência (0,45 e 1,7 mV/Pa) pedem 34 e 22 dB; o padrão do tipo Dinâmico é 28 dB. Quer um item de menu com a sensibilidade, ou o ganho manual basta?
11. **R11V4, OLED:** qual o modelo escolhido (controlador, resolução, endereço)? Se não for SSD1306 128 x 64 em 0x3C, a firmware ajusta `OLED_SH1106`/endereço (ou o layout, se a resolução mudar) e regera as telas. O módulo precisa de pull-ups de I²C? Os do codec (2,2 kohm) já servem para os dois.
