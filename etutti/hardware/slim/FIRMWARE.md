# eTutti Slim · Firmware (SPEC R2SL, etapa 1 — portão A)

Atende a **SPEC R2SL §8, item 2**. Sketch próprio e independente da V4: `etutti/firmware/slim/` (`slim.ino`, `name.c` = nome USB “eTutti”, `check_pins.py`). **Compila** para Teensy 4.1:

```powershell
& "C:/Program Files/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe" compile --fqbn teensy:avr:teensy41:usb=midi,speed=396 etutti/firmware/slim
```

Resultado (25 nov 2026, Teensyduino 1.60): flash 66 KB de código + 9,8 KB de dados, RAM1 17,5 KB, RAM2 13 KB, sem avisos. **Nunca rodou numa placa Slim** (ela não existe). `check_pins.py` confere os 15 pinos do sketch contra `pcb/PINOS.md`: 0 erros.

## O que mudou na R2SL

| Função | Como ficou | Estado |
|---|---|---|
| **Registros (7 posições)** | TMAG5273A2 (0x35) por I²C: ângulo XY (registros 0x19/0x1A, 13 bits, 1/16°); posição = `round((ângulo − REG_A0)/45°)`, 7 posições a 45°; **histerese** (uma nova posição só vale a ≤ 14,5° do seu centro) e **memória da última** (a zona morta entre a posição 7 e a 1 não muda nada); envia **CC 26** com a máscara (L, LM, M, MM, MH, LH, H) | compila; `REG_A0` é provisório (depende de como o chip fica na placa): ajustar com o primeiro knob |
| **Volume contínuo** | TMAG5273B2 (0x22): ângulo entre o clique de OFF (`VOL_A_MIN`) e o fim de curso (`VOL_A_MAX`) → 0…1, filtro de 1 polo, `codec.volume()` e **CC 7** quando muda | compila; limites provisórios |
| **OFF pela chave Hall** | não há mais KEEP nem leitura de chave de pot. O pino 25 (`KNOB_N`) lê a chave Hall invertida (0 = fora de OFF); **a bateria é desconectada em hardware** com o knob em OFF; o firmware só trata o desligamento automático | compila |
| **Latch de energia** | **SET** (pino 6): pulso de 10 ms na partida se o knob já está ligado (partida por USB); **KILL** (pino 10): pulso de 50 ms no desligamento automático (15 min sem uso sem USB, ou bateria < 3,3 V por 5 s) → a placa morre e não reinicia até o knob passar por OFF | compila; lógica na seção 3 do `ELETRONICA.md` |
| **Full Speed forçado** | `USB1_PORTSC1 \|= USB_PORTSC1_PFSC` no início do `setup()` | **compila; não verificado** em host real (se a enumeração já tiver começado em High Speed, pode ser preciso um desconectar/reconectar suave) |
| Tudo o mais | varredura das 32 teclas (4 linhas analógicas em paralelo, 595 por LATCH/CLOCK/DADO), modelo de tecla (cubo-raiz, 45 %/30 %, velocity logarítmica), LED, USB MIDI “eTutti”: **como na R1SL** | — |

Os dois sensores são lidos a 50 Hz (loop lento); a I²C a 400 kHz leva ~0,3 ms por leitura de 2 bytes. Configuração: modo contínuo (`DEVICE_CONFIG_2` = 0x02), canais X e Y, faixa ±266 mT (`SENSOR_CONFIG_2` = 0x07, o ímã dá 80–150 mT no sensor, estimativa).

## O que NÃO está aqui

- O **motor de acordeão** (palhetas amostradas, dados licenciados): 8 vozes simples placeholder; os 7 registros só mudam a forma de onda.
- A página `/etutti/` não conhece o Slim; sem EEPROM (registro e fundo de tecla não são guardados); sem watchdog.
- Modo **wake-and-sleep** dos TMAG5273 (economizaria ~4 mA): o modo contínuo é mais simples e robusto.

## Consumo, bateria e prateleira (**estimativas**, não medidas)

- **Corrente a 3,3 V:** núcleo a 396 MHz ~70 mA, 4 TMAG5253 ligados por vez ~8 mA, **2 × TMAG5273 contínuos 4,6 mA** (novo), SGTL5000 com fone ~15–20 mA, resto ~5 mA → **~105 mA**; na bateria (TPS63001 a ~90 %) **~105 mA**.
- **Autonomia (85 % da capacidade útil):** B1 1000 mAh **~8,1 h**; B2 1200 mAh **~9,7 h**; B3 1400 mAh **~11,3 h**. A 600 MHz, ~1,5 h a menos.
- **OFF (knob em OFF, sem USB):** **≤ 18 µA** no pior caso (típico ~10 µA): chave Hall ~3 µA + pull-up da chave 4,2 µA + latch 4,2 µA + BQ24075 ≤ 6,5 µA. **Prateleira só pela eletrônica ≈ 70 meses (B1)**; a autodescarga da LiPo (2–3 %/mês) é o fator real, não a eletrônica.
- **CPU de áudio:** como na R1SL (motor definitivo ~12–20 % medido na V4 no mesmo RT1062; o placeholder não foi medido). A varredura roda no `loop()` abaixo do áudio.

## Contrato com a eletrônica

Todos os pinos vêm de `etutti/hardware/slim/pcb/PINOS.md`; se o mapa mudar, `check_pins.py` quebra. Endereços I²C: SGTL5000 0x0A, TMAG5273A2 0x35, TMAG5273B2 0x22.

## Perguntas

Sem perguntas para o design. Para a bancada: ângulos de referência dos knobs, o pulso de SET e o Full Speed (`ELETRONICA.md` §3 e §7).

## R3SL: índice × posição × nota (conferido contra a régua posicionada)

`etutti/firmware/slim/check_teclas.py` compara a tabela `NOTE[][]` do sketch com o contrato do Design (`case/envelope_regua.json`) e com a régua posicionada (`pcb/regua/posicao_regua.json`): **32/32 teclas batem** (índice = 8 × (fileira − 1) + posição; posição 1 = esquerda; nota → MIDI com C4 = 60). A coluna c da varredura é o estágio c do 595 (QA…QH = EN1…EN8 = TMAG5253 U1…U8, nos pinos 15, 1, 2, 3, 4, 5, 6, 7 do 595): conferido nas redes da régua posicionada. O sketch não mudou.

## R4SL — bateria escolhida, NTC, carga e autonomia

Bateria: **VARTA 1/LPP 523450 S PCM W (56457 201 016)**, 1000 mAh (cabeçalho da folha; a tabela diz 1320 mín./1400 típ.: usei o conservador), PCM, **NTC 10 kΩ ±1 %, B 3380**, fios vermelho (+), branco (NTC), preto (−), AWG24.
- **NTC:** 28,2 kΩ a 0 °C, 10 kΩ a 25 °C, 4,9 kΩ a 45 °C, 3,6 kΩ a 50 °C (B 3380). Vai direto no TS do BQ24075 (R259 **não monta**); o BQ24075 corta a carga fora da janela dele. O firmware não lê o NTC (só o VBAT/2 no pino 16).
- **Corrente de carga:** R203 = 2,2 kΩ → ICHG = 890/2200 = **0,405 A = 0,41 C** de 1000 mAh (**≤ 0,5 C**; a folha admite 1,98 A); carga completa ≈ 2,8 h.
- **Autonomia (≈ 105 mA, 85 % útil):** **~8,1 h** a 396 MHz (1320 mAh mín. da tabela: ~10,7 h); OFF ≤ 18 µA. O desligamento por bateria vazia (< 3,3 V por 5 s) fica **acima** do corte do PCM (2,3 V).
- **Pinos × placa posicionada:** `etutti/firmware/slim/check_placa.py` lê `pcb/PINOS.md` e `pcb/principal/posicao_principal.json`: **21/21 pinos** na bola e na rede certas; os mais longos (estimativa Manhattan): I²S_TX 59, BCLK 55, LRCLK 53 mm (o SGTL5000 está no pé da placa), OUT_R1 46 mm; **par USB 36 mm** em linha reta. `check_pins.py` 15/15 e `check_teclas.py` 32/32 seguem ok.

## R5SL — pinos × placa

Refeito `check_placa.py` depois do LED na face de cima: **21/21 pinos** na bola e na rede certas; os mais longos: I²S_TX 59, BCLK 55, LRCLK 53, OUT_R1 46 mm; par USB 47,7 / 46,4 mm (Manhattan; 36 mm em linha reta, aceito). Nada muda no firmware: os pinos do LED (R/G) são os mesmos. Com a BAK de 950 mAh (se for a substituta) a autonomia cai a ~7,7 h.

## R6SL — LED e pico de consumo

LED do anel: 0805 bicolor vermelho/verde-amarelo, **mesmos pinos: 13 (LED_R, D8) e 5 (LED_G, H3)**, mesma polaridade (ânodos nos pinos, cátodos em GND); `check_placa.py` 21/21 depois do reposicionamento. Pico de consumo para a BAK: ~250 mA a 3,3 V, ~325 mA na bateria (< 475 mA, 68 %); autonomia com a BAK ~7,7 h.

## R8SL — portão F-1: o instrumento completo (26 nov 2026)

Sketch `etutti/firmware/slim/slim.ino`, uma só fonte, **duas versões**. O motor de som foi **copiado** do `etutti_synth` (que continua congelado).

| Versão | Para quê | Compilar |
|---|---|---|
| **Produção** | Slim: RT1062 chip-down = Teensy 4.1 | `arduino-cli compile --fqbn teensy:avr:teensy41:usb=midi,speed=396 etutti/firmware/slim` |
| **Bancada** (`SLIM_BANCADA`, liga sozinho no `teensy40`) | Teensy 4.0 do J + Audio Board Rev D, sem placa Slim | `arduino-cli compile --fqbn teensy:avr:teensy40:usb=midi,speed=396 etutti/firmware/slim` (força: `-DSLIM_BANCADA=0/1`) |
| Medição (temporária) | CPU/memória/pico na serial | cópia da pasta com `#define SLIM_BENCH_PRINT 1` na primeira linha, `usb=serialmidi`, lida em `COM3` por `System.IO.Ports.SerialPort` |

Gravar: `arduino-cli upload -p <porta de board list> --fqbn ...` (depois do upload a Teensy fica 10-20 s no bootloader, `PID_0478`, e volta como `VID_16C0&PID_0485` "eTutti").

### O que foi feito
1. **Som:** acordeão com **palhetas amostradas** (`ReedSampler`, 4 ranks, 8 vozes; `reed_sampler.h` copiado), velocidade = pressão do fole (`accordionLevel` 24 dB + `accordionBrightness` com passa-baixas 700 Hz-16 kHz), envoltória de fole (ataque 24 ms, soltura 82 ms), reverb leve. **Registros** na ordem do knob (SPEC 4) com os nomes do J: 1 L Bassoon, 2 LM **Bandoneon**, 3 M **Clarinet**, 4 MM **Violin**, 5 MH **Oboe**, 6 LH **Organ**, 7 H **Piccolo** (máscara CC 26: 1 = 16', 2 = 8' M1, 4 = 8' M2, 8 = 4'). **As amostras (`reed_samples.cpp/.h`, licenciadas) estão em `etutti/firmware/slim/.gitignore`** (confirmado com `git check-ignore`); sem elas o mesmo sketch compila com as tabelas sintetizadas (compilado e conferido: 7,8 KB de dados em vez de 1,2 MB).
2. **Teclado:** varredura das 4 réguas (595 + TMAG5253, OUT_R1..R4) como na R3SL; nota ligada em 45 %, desligada em 30 %, velocity logarítmica; repouso medido na partida (16 quadros) e **fundo aprendido por tecla, guardado na EEPROM** (gravação só 5 s depois de parar de tocar; CC 14 recalibra). Linha 4 repete notas da 1: `noteHolders` (a nota só começa na primeira tecla e só para na última). Sem placa não foi exercitado.
3. **Knobs (TMAG5273 0x35 / 0x22):** 7 posições a 45° com **histerese** (8°), zona morta entre 7 e 1 mantém a última, **posição guardada na EEPROM** (vale na partida); volume contínuo (filtro de 1 polo, `codec.volume`, CC 7); chave Hall (pino 25) + latch SET/KILL; desligamento automático (15 min sem uso, ou bateria < 3,3 V por 5 s, só sem USB). Sensor que não responde: nada trava, é tentado de novo a cada 1 s e o LED fica vermelho rápido. Ângulos de referência (`REG_A0`, `VOL_A_*`) seguem **provisórios** (dependem de como o chip fica na placa).
4. **LED em ânodo comum (R7SL):** pinos 13 (R) e 5 (G) **ligam em nível BAIXO**, apagam em ALTO; pino solto (reset, alta impedância) = apagado, porque o ânodo está no +3V3 e não há caminho ao GND. Estados: verde breve a cada 2 s (ligado, parado), verde (tocando), laranja (lendo as teclas ≥ 0,6 s e **carregando**), vermelho lento (**bateria baixa**), vermelho rápido (**erro de sensor**: codec, régua ou knob mudos).
5. **USB:** MIDI "eTutti" (`name.c`) e **Full Speed forçado**. **Achado:** o gancho da V4 (`USB1_PORTSC1 |= PFSC` em `startup_late_hook`) **não funciona** no core 1.62: o gancho roda 300 ms depois do `usb_init()`, o host já enumerou em High Speed (medido na bancada: PSPD = 2). O Slim faz um **desconectar suave** (RS = 0, PFSC, 60 ms, RS = 1): o host enumera de novo, agora a 12 Mbit/s (medido: PSPD = 0, "eTutti" estável). A V4 deveria ganhar a mesma correção (fora do escopo).
6. **Bancada:** troca varredura, knobs e energia por simulados: um padrão automático percorre os **7 registros e um 8º segmento com os 4 ranks juntos** (7 s cada: arpejo de 4 notas, velocity 30-127, depois 8 notas ao mesmo tempo), manda os mesmos Note On/Off e CC 26 pela USB, e também toca o Note On que chegar por MIDI (CC 7 = volume; volume fixo de 0,35 por segurança). Sensores ausentes, bateria e latch não são lidos nem pulsados.

### Medido no Teensy 4.0 do J (396 MHz, amostras reais, `usb=serialmidi` com `SLIM_BENCH_PRINT`)
- **Som:** cada um dos 7 registros e o segmento "4 ranks" saíram no mixer final (`AudioAnalyzePeak`, pico por segundo): L 0,13, LM 0,18, M 0,16, MM 0,16, MH 0,17, LH 0,19, H 0,12, 4 ranks 0,21 (escala 1,0; margem ampla, sem clip). Pelo fone **não ouvi** (sem ouvido aqui): o que está confirmado é o sinal no mixer, o codec respondendo (`codecOk`) e a enumeração; **J: ouvir os 7 registros no fone**.
- **CPU de áudio (`AudioProcessorUsageMax`, 396 MHz):** 8 notas, registros de 1-2 ranks: **13-19 %**; **pior caso (8 notas, 4 ranks): 29,8 %** (a 600 MHz ficaria ~20 %). Antes do reverb e do bellows serem iguais aos da eTuttino (12 %/20 % a 600 MHz): confere.
- **Blocos de áudio:** pico **8** de 60 reservados (`AudioMemory(60)`; podem baixar para ~24).
- **Memória (relatório do compilador):** produção Teensy 4.1: flash código 78,7 KB + dados 1,21 MB (as amostras), RAM1 61,9 KB de variáveis (+75 KB de código), RAM2 22,4 KB; livre para arquivos 6,8 MB. Bancada Teensy 4.0: código 72,6 KB + dados 1,21 MB, RAM1 60,0 KB, RAM2 22,4 KB.
- **USB:** Full Speed (PSPD 0), enumera como "eTutti" (MIDI), estável.

### Checks (portão F-1)
`check_pins.py` 15/15, `check_teclas.py` 32/32, `check_placa.py` 21/21: **passaram** (os dois últimos leram `posicao_principal.json` atual). Ambas as versões compilam sem avisos (produção 4.1 e bancada 4.0; mais a de produção sem as amostras).

### Desvios e limites
- Velocidade de produção compilada a **396 MHz** (a conta de consumo da R2SL usa isso); 600 MHz só se a CPU pedir.
- O código real de varredura, knobs, latch, LED de carga/bateria e EEPROM das teclas **compila mas não rodou** (a placa não existe); na bancada só rodam som, USB, LED (pino 13 da 4.0 é o LED da placa, com lógica invertida) e registros simulados.
- Não há tom/instrumentos extras nem tremolo (CC 27) no Slim: só o acordeão clássico seco; a página `/etutti/` ainda não conhece o Slim.
- A Teensy do J ficou gravada com a **bancada usb=midi** (versão final).

### Perguntas para o design
Nenhuma nova. Para a eletrônica: confirmar que o LED fica apagado com os dois pinos em alta impedância (ânodo no +3V3 e só os cátodos nos pinos), e o nível do pino 25 na partida por USB.
