# eTutti Slim · Firmware (SPEC R1SL, etapa 1 — portão A)

Atende a **SPEC R1SL §8, item 2**. Sketch próprio e independente da V4: `etutti/firmware/slim/` (`slim.ino`, `name.c` = nome USB “eTutti”, `check_pins.py`). **Compila** para Teensy 4.1:

```powershell
& "C:/Program Files/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe" compile --fqbn teensy:avr:teensy41:usb=midi,speed=396 etutti/firmware/slim
```

Resultado (24 nov 2026, Teensyduino 1.60): flash 65 KB de código + 9,8 KB de dados, RAM1 17,5 KB de variáveis, RAM2 13 KB. **Nunca rodou numa placa Slim** (ela não existe); só compilou. `check_pins.py` confere os 16 pinos do sketch contra `pcb/PINOS.md`: 0 erros.

## O que o sketch faz hoje

| Função | Como | Estado |
|---|---|---|
| **Varredura das 32 teclas** | 4 linhas analógicas lidas **em paralelo** (pinos 14, 15, 26, 27); DADO/CLOCK/LATCH comuns às 4 réguas; um “1” caminha pelo 74HC595 de cada régua: DADO = 1 só no 1º pulso, 1 pulso de CLOCK + 1 de LATCH por coluna; 60 µs de espera por coluna (TMAG5253BA3: 20 µs típ./45 µs máx. de ligação); depois 9 pulsos com DADO = 0 limpam a cadeia | compila; temporização por estimativa |
| **Modelo da tecla** | desvio absoluto da leitura em relação ao repouso (medido na partida, 16 quadros) → curso pelo modelo do dipolo (B ∝ 1/d³, raiz cúbica) entre repouso e fundo (fundo aprendido por tecla); nota liga a 45 %, desliga a 30 %; velocity = tempo de 12 % a 45 % do curso em escala logarítmica (1 ms = 127, 80 ms = 1). Mesmos limiares do sketch da V4, que **também nunca rodaram com sensor real** | compila |
| **7 registros** | ADC do pino 24; 3 leituras iguais seguidas; entre posições (> 3,15 V) mantém a última; envia **CC 26** com a máscara (bit 0 L, bit 1 M esquerdo, bit 2 M direito, bit 3 H: L, LM, M, MM, MH, LH, H) | compila; o **motor de som ainda é placeholder** (só muda a forma de onda) |
| **Volume contínuo** | cursor do pot no pino 22, filtro de 1 polo, `codec.volume()` e **CC 7** de volta quando muda | compila |
| **LED** (R pino 13, G pino 5) | verde tocando; verde breve a cada 2 s em repouso; laranja ao ler as teclas na partida (0,6 s) e carregando; vermelho lento bateria < 3,45 V sem USB; vermelho rápido codec ou régua sem resposta (qualquer sensor com leitura presa a um trilho) | compila |
| **Energia** | `setup()` põe **KEEP (pino 10) = 1 primeiro de tudo**; a cada 20 ms: knob ligado = SW_S ≥ 1,0 V; KEEP = knob ligado e sem desligamento automático e sem bateria vazia; **15 min sem uso (sem USB)** ou **bateria < 3,3 V por 5 s** → KEEP = 0 → o hardware solta o SYSOFF e a placa morre; **soft off** com USB e knob em OFF: mudo, MIDI vivo, LED de carga | compila; a lógica de hardware está na seção 3 do `ELETRONICA.md` |
| **USB MIDI class-compliant “eTutti”** | `usb=midi`, velocity, nome por `name.c`; recebe CC 26 | compila |
| **Full Speed forçado** | **não feito** (precisa da placa; ver `ELETRONICA.md` §6.6) | pendente |

## O que NÃO está aqui (etapas seguintes)

- **O motor de acordeão** (palhetas amostradas, 7 registros reais, brilho por velocity, tremolo CC 27): os dados vêm da biblioteca licenciada do J e **não** podem ser copiados nem publicados; o Slim usa 8 vozes simples (seno/serra) só para soar. Quando o motor for trazido, os registros passam a chamar os 4 bancos (L, M esquerdo, M direito, H).
- Funções que a V4 tinha e o Slim ainda não: página web (`/etutti/`) não conhece o Slim; EEPROM (fundo das teclas aprendido, registro guardado); relatório do conferido de sensores na tela (o Slim não tem tela).
- Watchdog.

## CPU e bateria (**estimativas**, não medidas)

- **CPU de áudio:** o motor definitivo mede ~12 % (MM) a ~20 % (todos os bancos) com 8 notas num RT1062 (medição da V4 em Teensy 4.0, mesmo núcleo); o motor placeholder deste sketch **não foi medido** (sem placa). A varredura roda no `loop()`, **abaixo** do áudio (a interrupção do áudio a preempta): **não custa CPU de áudio**; custa só corrente (o núcleo nunca dorme).
- **Taxa de varredura:** 8 colunas × (60 µs de espera + 4 × ~5 µs de ADC + 0,5 µs de pulsos) ≈ 0,65 ms por quadro ≈ **1,5 kHz**; o `analogRead` de 4 linhas **não** é paralelo no hardware (ADC1/ADC2 só em paralelo com a biblioteca `ADC`): ganho possível de ~20 µs por coluna se for preciso.
- **Corrente a 3,3 V:** núcleo a 396 MHz ~70 mA (a 600 MHz ~100 mA), 4 TMAG5253 ligados por vez ~8 mA (2 mA cada), SGTL5000 com fone ~15–20 mA, resto (flash, LED, divisores) ~5 mA → **~100 mA**; na bateria, com o TPS63001 a ~90 %: **~100 mA**.
- **Autonomia da LiPo de 1000 mAh** (80–85 % utilizáveis): **~8 h a 396 MHz**, ~6 h a 600 MHz. Desligado (SYSOFF alto): só fugas, da ordem de µA.

## Contrato com a eletrônica

Todos os pinos vêm de `etutti/hardware/slim/pcb/PINOS.md`; se o mapa mudar, `check_pins.py` quebra. As constantes de temporização (`T_ON_US`, limiares) saem da TMAG5253 e da SPEC §5.1 e devem ser **afinadas por tato** quando houver uma régua real: velocity, limiares de nota ligada/desligada, ganho (`COUNTS_PER_GS`).

## Perguntas

Sem perguntas para o design. Para a eletrônica: confirmar o pulso de partida (C205 × R210, `ELETRONICA.md` §3) e o Full Speed (§6.6).
