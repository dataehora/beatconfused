# eTutti Student V4 · firmware e som (R1V4 + R2V4)

21 nov 2026. Atende as tarefas **P1** (capacidade do Teensy MicroMod para 76 teclas, Full Speed USB) e **P2** (começo do firmware V4, §9 itens 1–3) da **R1V4**, com a varredura da **R2V4** (F2: réguas de 4 teclas, 4 linhas OUT, cadeia de registradores de deslocamento).

**O firmware compila para a V4 (28, 44, 60 e 76 teclas), para o Student V01 e para o eTuttino. Nada foi gravado e nada rodou numa placa: a V4 não existe.** Tudo o que é tempo medido abaixo é **conta** (marcada "estimado"), a partir das medições do eTuttino (CLAUDE.md) e dos números do datasheet que o repositório já traz. Os pinos e o contrato de varredura seguem o `student_v04/pcb/PINOS.md` (rascunho da eletrônica, 74HC595 C5947, SCAN_DATA = 2, SCAN_CLK = 3); o que o PINOS.md ainda marca "(conferir)" continua a conferir.

## Um sketch, três instrumentos

O sketch continua sendo `etutti/firmware/etutti_synth/etutti_synth.ino`.

| Placa no Teensyduino | Chave | Instrumento |
|---|---|---|
| Teensy 4.0 | — | eTuttino (44 teclas), como antes |
| Teensy MicroMod | `ETUTTI_STUDENT_V4 0` (padrão) | Student V01, como antes |
| Teensy MicroMod | **`ETUTTI_STUDENT_V4 1`** | **Student V4** |

A chave é a linha `#define ETUTTI_STUDENT_V4 0` perto do topo do sketch (o Teensyduino não deixa passar `-D` pela linha de comando sem trocar as definições da placa). O número de teclas é `#define V4_KEYS 28` (28, 44, 60 ou 76; outro valor dá `#error`).

```
arduino-cli compile --fqbn teensy:avr:teensyMM:usb=midi,speed=396 etutti/firmware/etutti_synth      # V01
arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi etutti/firmware/etutti_synth                # eTuttino
# V4: mudar a chave para 1 (em uma cópia, ou no sketch) e compilar como o V01
```

## P1 · capacidade do Teensy MicroMod para 76 teclas

### Pinos e ADC

O Teensy 4 tem 14 pinos analógicos (A0–A13 = pinos 14–27). O MicroMod usa, em qualquer versão: I²C 18/19 (A4/A5) e I2S 20/21/23 (A6/A7/A9), que não saem do lugar. Sobram **7 pinos analógicos livres: 14, 15, 22, 24, 25, 26, 27**, além de VBAT (16) e HP_DET (17), que já são analógicos.

| Uso na V4 (suposto) | Pino |
|---|---|
| OUT das fileiras 1–4 (OUT_R1..R4) | 14, 15, 26, 27 (A0, A1, A12, A13) |
| SCAN_DATA, SCAN_CLK da cadeia de 74HC595 (SRCLK e RCLK juntos) | 2, 3 |
| Volume A, B, clique (liga/desliga) | 22, 24, 25 (como na V01; também são analógicos, mas sem uso) |
| Seletor A, B, clique | 11, 9, 6 |
| VBAT (÷2), HP_DET | 16, 17 |
| CHG_STAT | **0** (saiu do 26, que virou OUT_R3) |
| KEEP, AMP_SD | 10, 12 |
| LED vermelho, verde | 13, 5 |
| I2S TX / RX (fone, alto-falante / **microfone pelo codec**) | 7 / 8 |
| I2S LRCLK, BCLK, MCLK; I²C SDA, SCL (codec, **OLED**) | 20, 21, 23; 18, 19 |
| PWR_EN (3.3V_EN) | 28 (na V3/V4 não está ligado a nada) |
| **Livres** | 1, 4, 13 (também acende o LED azul do módulo) e 29–45 |

**Cabe**, com folga nos pinos digitais. O limite é o analógico: **dividir cada fileira em 2 linhas OUT (8 ADC, SPEC §5.2) não cabe** sem abrir mão de outro pino analógico, porque só 7 estão livres (14, 15, 22, 24, 25, 26, 27) e os 3 de 22/24/25 são dos knobs (qualquer pino do Teensy 4 aceita interrupção, então os knobs podem ir para pinos digitais, mas ainda faltaria 1: HP_DET ou VBAT teriam de virar leitura digital ou dividir um pino). Três a oito linhas OUT em 7 pinos é uma decisão da eletrônica; este firmware usa 4 e não precisa de mais (ver velocity).

### Tempo de varredura (estimado)

Por coluna: ligar os 4 sensores (`tON`) + 4 leituras + um pulso de clock. Dados de entrada:
- **tON máximo do TMAG5253BA3 = 45 µs** (valor que o repositório já usa, `pocket/pcb/PINOS.md`; o UA5 seria 130 µs). O texto da R1V4 cita "< 25 µs bipolar, < 60 µs unipolar, típicos": são números diferentes dos do repositório. **Não reli o datasheet nesta sessão** (baixar o PDF pede autorização); o firmware usa **60 µs** (`SENSOR_WAKE_US`), 45 µs + folga, o mesmo valor da V01. Confirmar com a variante escolhida (pergunta 1).
- `analogRead` do Teensy 4 a 12 bits, sem média: **5,6 µs** por leitura (derivado do eTuttino: 240 µs para 34 teclas com 16 trocas de canal de 3 µs, CLAUDE.md). Independe da velocidade da CPU.
- Pulso de clock + troca de coluna: ~1,5 µs.

Como a leitura de uma coluna só começa depois que os sensores acordam, e o processamento da coluna anterior (4 teclas, ~3 µs) cabe dentro dessa espera, **a aritmética não custa tempo extra** (o firmware faz exatamente isso).

| Teclas | Colunas | Passada, tON 45 µs | Passada, tON 60 µs (firmware) | Passada, tON 130 µs (UA5) |
|---:|---:|---:|---:|---:|
| 28 | 8 | 551 µs (1,8 kHz) | **671 µs (1,5 kHz)** | 1231 µs |
| 44 | 12 | 827 µs | 1007 µs | 1847 µs |
| 60 | 16 | 1102 µs | 1342 µs | 2462 µs |
| 76 | 20 | 1378 µs (726 Hz) | **1678 µs (596 Hz)** | 3078 µs |

Para comparação, a V01 (2 multiplexadores, 14 sensores ligados por vez) varre 28 teclas em ~340 µs. A V4 é mais lenta por passada, porque cada coluna espera o `tON` sozinha, mas liga **só 4 sensores por vez** (V01: 14): estimado **10,4 mA** contra 36,4 mA (36,4 mA/14 = 2,6 mA por sensor ligado, de `pocket/POWER.md`). **Com 76 teclas o consumo dos sensores é o mesmo**: continua 4 ligados por vez.

### Resolução do velocity (1 ms = 127, 80 ms = 1)

O erro de velocity vem do tempo entre as duas leituras que cercam cada cruzamento (VEL_START e NOTE_ON_AT). Convenção de `POWER.md`: erro de tempo de ¼ do período por cruzamento, dois cruzamentos independentes. Erro em unidades de velocity (estimado):

| Período da passada | batida de 1 ms | 2 ms | 5 ms | 10 ms | 20 ms |
|---:|---:|---:|---:|---:|---:|
| 671 µs (28 teclas) | ±6,8 | ±3,4 | ±1,4 | ±0,7 | ±0,3 |
| 1007 µs (44) | ±10 | ±5,1 | ±2,0 | ±1,0 | ±0,5 |
| 1678 µs (76) | ±17 | ±8,5 | ±3,4 | ±1,7 | ±0,9 |
| **leitura só da coluna (hot scan, 85 µs)** | ±0,9 | ±0,4 | ±0,2 | ±0,1 | ±0 |

Uma batida de 1 ms (1,4 mm em 1 ms, 1,4 m/s) não é de dedo: o mais rápido que se toca fica em 3–5 ms, onde o erro com 76 teclas é de ±3 a ±6 unidades, com 28 teclas ±1 a ±2. **Para ficar bem em todas as versões, o firmware ganhou a "leitura quente"** (hot scan): quando uma tecla já saiu do repouso (≥ 3 % do curso), está subindo e ainda não passou do ponto de nota ligada, o firmware lê **só a coluna dela**, de novo e de novo (~85 µs cada, até 3 ms), em vez de esperar uma passada inteira. Isso dá ~12 amostras numa batida de 1 ms, qualquer que seja o número de teclas, sem precisar de mais linhas OUT. Custo: as outras teclas ficam até 3 ms sem leitura durante uma batida (aceitável, mas é uma troca; ver pergunta 3). **Estimado; precisa de teclas de verdade para afinar `HOT_FROM` e `HOT_BUDGET_US`.**

### Capacitância da linha OUT (estimada)

20 sensores desligados (alta impedância, ~5 pF cada, valor suposto) + trilha e cabo entre réguas (~100–150 pF, suposto) + o pino do ADC (~5 pF): **~0,2–0,3 nF**, abaixo do limite de 1 nF que a TI cita (R1V4 §5.2). Com 76 teclas a conta é a mesma, porque são 20 sensores por linha (5 réguas por fileira). Depende do comprimento real dos cabos da F2.

### CPU com síntese + varredura (estimado)

- **Síntese:** o CLAUDE.md mede, no Teensy 4.0 a 600 MHz, **12 % de CPU** (8 notas, acordeão amostrado, MM) e **20 %** (as quatro fileiras de palhetas). Escalando linearmente para 396 MHz (a velocidade do orçamento de bateria): **~18 % e ~30 %**. O microfone (I2S RX + medidor de pico) acrescenta pouco (estimado < 1 %).
- **Varredura:** o laço principal espera o `tON` (sem ocupar interrupção). A aritmética de 76 teclas é ~76 × 0,8 µs ≈ 60 µs por passada e cabe dentro das esperas. O truque `restAtModel` evita recalcular 2 raízes cúbicas por tecla parada a cada passada (na V4 só quando o repouso deriva > 0,5 contagem).
- **Efeito mútuo:** o áudio roda em interrupção e rouba tempo do laço. Com 30 % de áudio, uma passada de 76 teclas (1678 µs) se alonga para ~2,4 ms em média (÷ 0,7). Uma atualização do áudio dura até ~0,9 ms contínuos (30 % de 2,9 ms). Se isso cair entre as duas leituras de uma batida, o intervalo se alarga (a interpolação continua exata, só menos fina). **Medir na placa** (`AudioProcessorUsageMax()` com um `usb=serialmidi` temporário, como no CLAUDE.md).

**Conclusão P1:** o MicroMod **dá conta de 76 teclas** em pinos, ADC e CPU. O ponto fraco é o tempo de varredura (0,6 kHz com 76 teclas, 1,5 kHz com 28), contornado pela leitura quente. O que mais importa mudar na eletrônica, se quiser mais folga: um sensor com `tON` menor, ou 6–7 linhas OUT.

### Full Speed USB (R1V4 §5.4, item 3): é possível

Lido nos fontes do Teensyduino **1.62.0** instalado (`cores/teensy4/usb.c`, `startup.c`, `usb_midi.c`):
- `usb_init()` termina com a linha `//USB1_PORTSC1 |= USB_PORTSC1_PFSC; // force 12 Mbit/sec`, **comentada** (usb.c:237). O bit existe em `imxrt.h` (`USB_PORTSC1_PFSC`, bit 24).
- `startup.c` chama `startup_late_hook()` (fraca) **logo depois** de `usb_init()` (linha 209), antes de `setup()`. Um sketch pode defini-la. O host só reseta o barramento ~100 ms depois de ver o dispositivo, então o bit entra a tempo.
- O resto do core já aceita o enlace a 12 Mbit/s: o tratador de interrupção (`usb.c:367`) lê `HSP` na mudança de porta e põe `usb_high_speed = 0`; `usb_midi.c:103` escolhe pacotes de 64 bytes (`MIDI_TX_SIZE_12`) nesse caso.

O sketch tem, na V4, `extern "C" void startup_late_hook() { USB1_PORTSC1 |= USB_PORTSC1_PFSC; }`, ligado por `V4_FORCE_FULL_SPEED` (1). **Não foi testado numa placa.** Se um dia a enumeração falhar, é só pôr 0; o bootloader do módulo é outro chip (MKL02), então regravar continua possível pelo botão Program. Compila.

## P2 · firmware V4 (itens 1–3 do §9)

Tudo atrás de `ETUTTI_STUDENT_V4`; o código da V01 e do eTuttino não mudou de comportamento (os helpers `processKey` e `finishScan` são a mesma lógica de antes, tirada de dentro de `scanKeys`).

### 1. Mapa de pinos como contrato
Os pinos estão no bloco `ETUTTI_V4` do início do sketch e seguem o `PINOS.md`: OUT_R1..R4 = 14/15/26/27, SCAN_DATA = 2, SCAN_CLK = 3, CHG_STAT = 0, o resto igual à V01. O `firmware_check.py` da V01 não cobre a V4 (e a V4 ainda não tem esquema para conferir).

### 2. Varredura por fileira com cadeia de 74HC595
- **Arranjo:** 4 linhas OUT (uma por fileira, sem pull interno: o pull-down de 100 kΩ é da placa) e uma cadeia DATA/CLK comum às quatro fileiras. Um "1" na cadeia liga **uma coluna** (4 sensores, um por fileira) de cada vez. `V4_KEYS` 28 = 2 réguas por fileira (8 colunas), 44 = 3 (12), 60 = 4 (16), 76 = 5 (20).
- **Contrato do 595 (PINOS.md), tratado no firmware (`srPulse`, `srClear`, `srSelect`):**
  1. SRCLK e RCLK são a mesma linha, então a saída **atrasa um pulso** em relação ao deslocamento. O acesso aleatório empurra o padrão inteiro e dá **1 pulso a mais** (que trava o padrão); o passo em ordem é só 1 pulso, porque o atraso é constante.
  2. Cada régua tem **8 estágios** e só QA..QD levam sensores: coluna global c = régua c/4, sensor c%4, estágio 8·(c/4) + c%4. Entre réguas o "1" passa por 4 estágios mortos: **da coluna 3 para a 4 são 5 pulsos**, nas outras 1.
  3. As saídas **não são Hi-Z na partida**: `srClear()` dá 8N + 1 pulsos com DATA = 0 antes de qualquer leitura (também ao desligar).
  4. CLK a no máximo 5 MHz: meio período de 100 ns (`SR_HALF_PERIOD_NS`). Acesso aleatório = 8N + 1 pulsos: 41 pulsos (~10 µs) com 76 teclas. O PINOS.md fala em "160 pulsos" para 20 colunas; pela regra "8 estágios por régua × N réguas por fileira" são 8 × 5 = 40 (+ 1), então usei 41 (pergunta 2).
- **Passada:** `srSelect(0)` e, para cada coluna: esperar `SENSOR_WAKE_US` (60 µs), ler as teclas da coluna, avançar o "1" e processar a coluna anterior durante o `tON` da próxima. O PINOS.md prevê 60 µs (normal) ou 90 µs (12 bits limpos, resíduo de assentamento 1,8 % → 0,25 %): `SENSOR_WAKE_US` é uma constante só; a 90 µs a passada de 76 teclas vai a ~2,2 ms (a conferir na placa).
- **Leitura quente:** ver P1. As leituras das quatro linhas usam `analogRead` em sequência (5,6 µs cada, 22 µs por coluna). O PINOS.md conta ~6 µs com ADC1 e ADC2 em paralelo (biblioteca ADC): economiza ~16 µs por coluna (cerca de 20 % do passo) e **não foi aplicado**.
- **Calibração por tecla e velocity:** o mesmo modelo da V01 (raiz cúbica do campo, repouso medido na partida, fundo aprendido e gravado na EEPROM, direção do sensor TMAG5253 lida do repouso, 1 ms = 127 e 80 ms = 1). EEPROM: magic `0xE7770106`, 4 + 2 × 76 = 156 bytes (o registro do seletor fica em 200).
- **Ordem das teclas** (índice 0–75, usado no teste de teclas CC 15): fileira por fileira a partir da fileira 1, da esquerda para a direita.

### Mapa de notas por módulo
`noteShift` desloca todas as teclas em oitavas inteiras: **−12 por módulo de grave**. Padrão (R1V4 §4.4): o 1º módulo extra vai para o agudo, o 2º para o grave, e assim por diante. Conferido por script contra a R1V4:

| Teclas | Colunas | Teclas por fileira (1–4) | Faixa |
|---:|---:|---|---|
| 28 | 8 | 7, 8, 7, 6 | G3–E5 |
| 44 | 12 | 11, 12, 11, 10 | G3–E6 |
| 60 | 16 | 15, 16, 15, 14 | G2–E6 |
| 76 | 20 | 19, 20, 19, 18 | G2–E7 |

C-griff e B-griff (CC 24) continuam valendo. **Pendente:** o usuário reconfigurar o mapa (e cada registro de acordeão trazer o seu, decisão 20) pede um CC novo e um lugar na EEPROM; não inventei CC porque o mapa de CCs vive também em `script.js` (pergunta 4).

### 3. Tela, bateria, fone, microfone, USB, KEEP
- **OLED (`V4_HAVE_OLED`):** SSD1306 128 × 64 em I²C (0x3C). O Teensyduino não traz biblioteca de OLED, então o sketch tem um **driver mínimo próprio** (buffer de 1 KB, fonte 5×7 de maiúsculas e dígitos, envio em pedaços de 16 bytes, um por passada do laço, **só com nenhuma tecla em movimento**, porque o I²C bloqueia ~0,4 ms por pedaço). Girada 180° (`OLED_ROTATION 2`): faz o que o `setRotation(2)` da Adafruit_SSD1306 faria, pelo remapeamento de segmento + sentido de varredura do próprio controlador. Mostra: **% de bateria** (curva típica de LiPo, primeiros valores) com "BAT/USB/CHG", o registro (ou instrumento), volume, **HP/SPK** (HP_DET), "REST" e uma barra de bateria e outra de **microfone**. Se a tela não responder ao endereço na partida, o firmware segue sem ela.
- **Microfone (`V4_HAVE_MIC`):** entrada MIC do codec (`inputSelect(AUDIO_INPUT_MIC)`, `micGain(36)`), I2S RX no pino 8 ("microfone IN" no PINOS.md), só um medidor de pico para a tela. Falta confirmar que o microfone da placa entra pelo MIC (e não pelo LINE IN) do SGTL5000.
- **HP_DET:** como na V01 (fone ≈ 0 V, sem fone ≈ 1,4 V; alto-falante só sem fone).
- **Acordar por USB:** a V3/V4 liga o 3,3 V quando o USB entra (D206). A partida sem clique já fazia o firmware ficar ligado (`powerBegin`).
- **Desligar com USB (muda na V4):** na V3/V4 nada corta o 3,3 V com o cabo plugado (o PWR_EN não está ligado). Então "desligar" com USB vira **desligamento suave**: sensores, amplificador, tela e LED apagam; um clique do volume (ou tirar o cabo) reinicia. Sem USB, é o desligamento de sempre (KEEP baixo).
- **KEEP pela atividade do usuário:** o KEEP já era solto depois de 15 minutos sem tecla, knob ou MIDI (5 minutos: o amplificador descansa). Na V4 esse tempo **conta também com o cabo USB plugado** (na V01 o USB zerava o contador); depois dele, desligamento suave.

## O que não foi feito
- **Full Speed**, **OLED**, **microfone** e a varredura **nunca rodaram em hardware**.
- O firmware nunca falou com um 595 de verdade: a ordem da cadeia (estágio 0 = QA da régua mais perto do DATA) e o atraso de um pulso vêm do PINOS.md e são a primeira coisa a conferir na placa.
- A página (`script.js`, `websynth.js`) não ganhou modelo Student V4 (a tarefa é só do firmware).
- Notas acima de E6 (88) com a V4 de 76 teclas (até E7 = 100): o acordeão amostrado toca a amostra mais próxima e a reafina (a palheta de 4' soa até 112); as amostras ficam a 24 kHz e as tabelas sintetizadas só foram feitas até E6. A verificar de ouvido (pergunta 5).
- `firmware_check.py` da V01 continua válido (o bloco de pinos da V01 manteve o seu texto); não há verificador análogo para a V4.

## Conferências feitas

| Conferência | Resultado |
|---|---|
| Compila, Teensy MicroMod, `speed=396`, V4 com 28 / 44 / 60 / 76 teclas | sim (28: flash 118 KB de código, 70 KB de RAM1; ver abaixo) |
| Compila, Teensy MicroMod, V01 (`ETUTTI_STUDENT_V4 0`) | sim, código 90 KB como antes |
| Compila, Teensy 4.0, eTuttino | sim, código 89 KB como antes |
| Mapa de notas das quatro versões × R1V4 §4.4 (por script) | igual |
| Tempos, velocity, CPU | **estimados**, tabelas acima |

## Como testar (quando houver placa)
1. Gravar com `ETUTTI_STUDENT_V4 1` e `V4_KEYS` = o número de teclas fitadas. O LED laranja na partida e a leitura do repouso levam ~0,1–0,2 s.
2. CC 15 (teste de teclas) na página: o anel de cada tecla deve responder, na ordem fileira por fileira.
3. Se alguma tecla ficar fora (LED vermelho piscando), o índice dela é o da ordem acima; confira a ligação da coluna e a ordem do registrador.
4. Medir `AudioProcessorUsageMax()` (build `usb=serialmidi` temporário) e o tempo de uma passada com `micros()` antes de afinar `SENSOR_WAKE_US`, `HOT_FROM` e `HOT_BUDGET_US`.
5. Conferir no host (USBView ou equivalente) a velocidade 12 Mbit/s com `V4_FORCE_FULL_SPEED 1`.

## Perguntas para o design

1. **tON do sensor:** o PINOS.md/E2 confirma 20 µs típico e 45 µs máximo para o BA3; os "25 / 60 µs típicos" da R1V4 ficam então superados. Com 130 µs (UA5) a passada de 76 teclas passa de 3 ms e a leitura quente deixa de bastar.
2. **Contagem de pulsos:** o PINOS.md diz "20 colunas = 160 pulsos" no acesso aleatório; eu uso 8 estágios × N réguas por fileira + 1 = 41 para 76 teclas. Confirme a conta, e que a coluna 0 é a régua mais perto do Teensy.
3. **Leitura quente:** aceita que, durante uma batida (até 3 ms), as outras teclas fiquem sem leitura? A alternativa é mais linhas OUT (limite de 7 pinos analógicos livres) ou um sensor mais rápido.
4. **Mapa de notas do usuário:** quer um CC novo (e o lugar na EEPROM) para escolher quantos módulos vão para o grave, e um mapa por registro de acordeão? Tem de ser decidido junto com a página.
5. **Notas até E7:** o 76 teclas passa o que o acordeão amostrado cobre bem (a captura foi até a tecla 79). Quer gravar mais amostras agudas ou limitar o mapa?
6. **Microfone:** entra mesmo pela entrada MIC do codec? E para que serve (só o medidor de nível, ou também afinador/entrada de efeito)?
7. **Desligar com USB:** o desligamento suave (tela e sensores apagados, a placa continua ligada) basta, ou a V4 deve levar de volta o PWR_EN (3.3V_EN) para cortar o 3,3 V com o cabo plugado?
8. **ADC duplo:** quer que eu use ADC1 e ADC2 em paralelo (biblioteca ADC, ~6 µs por coluna em vez de 22)? Ganha cerca de 20 % do passo, ao custo de depender dessa biblioteca.
