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
