# Liebling — FIRMWARE (programação e som)

**Atende:** SPEC **R3MIC**, só a versão A (2 × Infineon IM72D128, RP2040, USB 2 canais, 24 bits, 48 kHz).
**Etapa:** F1, simulação no PC. Nada foi comprado, nenhum hardware foi usado, nenhum firmware foi compilado ainda (o F2 vem depois).
Tudo está em `minimic/firmware/sim/` (Python, numpy, scipy, numba). Gráficos e números em `minimic/firmware/sim/out/`.

Reprodução (cerca de 45 s):
`C:/Users/julia/.venvs/cadquery/Scripts/python.exe minimic/firmware/sim/run_f1.py` (aceita grupos: `resp ruido dist alias sat ganho medidor cpu arranque`),
`export_coefs.py` (escreve `out/coeficientes.json`, a entrada das tabelas do F2) e `clock_plan.py` (planos de clock).

## 1. Resumo (números principais)

| Pergunta | Resultado da simulação | Meta / ficha |
|---|---|---|
| −3 dB nos graves, cadeia digital sozinha | ≈ 2,8 Hz (−0,33 dB em 10 Hz, −0,02 dB em 41 Hz) | — |
| −3 dB, sensor (1ª ordem 11 Hz, **hipótese**) + cadeia | **11,7 Hz** (−2,0 dB em 15 Hz; −0,32 dB em 41 Hz, a E1 do bayan) | ≤ 15 Hz: **cumpre** |
| Ondulação de 100 Hz a 16 kHz | −0,005 a +0,155 dB (pico em 14 kHz, por causa da compensação) | < 0,5 dB: **cumpre** |
| Fim da banda | +0,01 dB em 20 kHz, −0,64 em 22 kHz, −6,5 em 24 kHz | — |
| Excesso de ruído que a cadeia soma ao fluxo de bits | **+0,08 a +0,12 dB(A)** (sinc⁵) contra uma decimação ideal (parede de tijolo) | — |
| Faixa dinâmica do caminho digital (modulador sintético, 20 Hz–20 kHz) | 101 dB | — |
| Ruído total simulado (sensor + cadeia) | −108,4 dBFS(A) = 24,6 dB SPL(A), SNR 69,4 dB(A) | ficha 22,5 dB SPL(A) / 71,5 dB(A) (ver §4) |
| Distorção do caminho digital (sensor linear) | harmônicas < −133 dBc; THD+N −96 dB a −6 dBFS, limitado pelo ruído do modulador sintético | — |
| Rejeição de aliasing, 28 kHz a 1,4 MHz | **≥ 88 dB** dentro de 0–20 kHz (medida e analítica); o pior ponto é 28–32 kHz | meta própria ≥ 80 dB |
| Erro do ganho (29 degraus) | 0,0002 dB | — |
| Estalo no ganho (banda lateral fora de ±300 Hz) | rampa −91 dB (+1,5 dB), −80 dB (+42 dB); degrau seco: −70 e −54 dB | sem estalo |
| Medidor | limiares exatos a 1 kHz; queda **20,0 dB/s**; ataque no mesmo bloco de 1 ms | SPEC §3: ~20 dB/s |
| SAT | pisca a 8 Hz, dura 2 s depois do último evento, os dois vermelhos piscam junto | SPEC R3MIC §3 |
| **CPU no RP2040, 2 canais** | **91 Mciclos/s (pessimista) / 75 (otimista)**: 69 % / 56 % de um núcleo a 133 MHz; 59 % / 49 % a 153,6 MHz; 46 % / 37 % a 200 MHz | cabe |

Resposta curta às duas perguntas de risco: **sim, o filtro mantém os graves de 15–40 Hz** (o que corta é o sensor e o bloqueio de DC em 2,8 Hz, e juntos ficam em 11,7 Hz), e **cabe no RP2040**, com folga razoável só se o DSP ficar num núcleo e o USB e a interface no outro (§5, §8).

## 2. Cadeia simulada e parâmetros (a que vai para o F2)

Escala: 2²³ = fundo de escala (0 dBFS de seno, pico). Tudo em inteiros; o simulador usa a mesma aritmética (LUT de bytes, Q17, deslocamentos).

```
IM72D128 ×2 → linha PDM única, 3,072 MHz, 2 bits por período de clock (um por canal)
 → PIO (autopush de 32 bits, MSB = mais antigo) → DMA em blocos de 1 ms (192 words)
 → desentrelaçar (truque de bits, 20 operações por word) → 2 fluxos de 16 bits
 → sinc⁵ por LUT, R = 16  → 192 kHz       (10 consultas de 256 entradas int32 por saída)
 → meia-banda 23 taps, 192 → 96 kHz      (Q17)
 → meia-banda 71 taps,  96 → 48 kHz      (Q17)
 → compensação 3 taps [−0,0252  1,0504  −0,0252] (Q15)
 → bloqueio de DC 1ª ordem, ≈ 2,8 Hz
 → ganho 0…+42 dB, 29 passos de 1,5 dB, rampa de um polo → clamp ±(2²³−1)
 → USB (2 canais, 24 bits)  e  medidor / SAT
```

| Bloco | Parâmetros | Observação |
|---|---|---|
| Sinc⁵, R = 16 | núcleo de 76 taps (soma 16⁵ = 2²⁰), tabelas escaladas ×8 → fundo de escala exato 2²³ | Tabelas de 10 × 256 × 4 B = 10 KB em SRAM. Sinc⁴ custa 4,6 Mc/s a menos, mas deixa +0,35 a +0,85 dB(A) de ruído dobrado (modulador de 5ª e de 4ª ordem). Fica o sinc⁵. |
| Meia-banda 192 → 96 kHz | Kaiser β 10,06, 23 taps, banda passante 20 kHz, parada 76 kHz, projeto 100 dB | Q17: parada real −89 dB. 6 pares de taps. |
| Meia-banda 96 → 48 kHz | Kaiser β 8,96, 71 taps, passante 20 kHz, parada 28 kHz, projeto 90 dB | Q17: parada real −87 dB. 18 pares. Com Q15 a parada piorava para −77 dB: **Q17 é necessário** (sem custo, ver abaixo). |
| MAC no M0+ | dado de 24 bits dividido em duas metades de 12 bits × coeficiente de 18 bits | acumuladores de no máximo 2^29,8: cabem em 32 bits, 2 multiplicações de 32 bits por tap, sem 64 bits |
| Compensação | 3 taps Q15, +0,78 dB em 20 kHz | cancela a queda do sinc⁵ (−0,5 dB em 16 kHz) com erro residual de +0,15 dB |
| Bloqueio de DC | `dc += (d>>12) + (d>>13)`, 8 bits fracionários, α = 3/8192 → 2,8 Hz | arranque rápido: nas primeiras 8192 amostras o deslocamento cresce de 1 a 12 |
| Ganho | tabela de 29 valores Q24 (máximo 126 × 2²⁴, cabe em 31 bits), `g += (alvo−g) >> 9` (τ = 10,7 ms) | multiplicação 24 × 32 bits com produto de 64 bits (≈ 30 ciclos no M0+); 99 % do degrau em 29 ms (1,5 dB) e 49 ms (+42 dB) |
| Medidor | pico por bloco de 1 ms de max(\|L\|, \|R\|) depois do ganho; queda `lvl −= lvl>>9 + lvl>>11 − lvl>>13` por ms | limiares inteiros em `out/coeficientes.json` |
| SAT | (a) saída ≥ −0,1 dBFS (corte) ou (b) pico antes do ganho, depois do DC, ≥ −4,6 dBFS; 2 s a partir do último evento; pisca com período de 125 ms (8 Hz) e força os dois vermelhos a piscarem juntos | (b) é o limiar do **sensor simulado**: precisa de calibração com o sensor real (§4) |

Latência do caminho: cerca de 0,46 ms (HB de 71 taps a 96 kHz = 0,37 ms; o resto é pouco).

Formato dos bits no fio (ficha IM72D128VV01 v1.2, tabela 8): o canal com LR = GND põe o dado na borda de descida do CLK e o com LR = VDD na de subida, os dois na mesma linha, alta impedância na outra metade. O dado fica válido até 100 ns depois da borda (tDV) e vai a alta impedância 5 a 30 ns depois da próxima. Pressão positiva = mais 1s. O PIO lê duas vezes por período; os bits pares e ímpares da sequência são os dois canais (o simulador tem o desentrelaçamento verificado bit a bit).

## 3. Resultados detalhados

### 3.1 Resposta em frequência (`out/resposta_frequencia.png`)
Medida com tons de 10 Hz a 24 kHz entrando como fluxo PDM de verdade (ajuste de senoide, 33 frequências). Cadeia sozinha: −0,33 dB em 10 Hz, −0,15 em 15 Hz, −0,02 em 41 Hz, +0,14 em 16 kHz, +0,01 em 20 kHz. Com o sensor como filtro de 1ª ordem em 11 Hz: −3,77 dB em 10 Hz, −2,02 em 15 Hz, −0,32 em 41 Hz; −3 dB em 11,7 Hz. Se o sensor real for de 2ª ordem com −3 dB em 11 Hz, o conjunto fica em torno de 11,5 Hz (a ficha dá só "queda em 11 Hz", sem a ordem). Isso supõe que a queda de 11 Hz é a do sensor com a variante **VV01**; a V01 cai em 20 Hz e então o conjunto ficaria perto de 20 Hz, fora da meta: a E1 deve comprar a VV01.

### 3.2 Ruído e SNR (`out/ruido.png`, tabela em `resultados.json`)
Ruído do sensor modelado como branco, calibrado para SNR 71,5 dB(A) a 94 dB SPL (−36 dBFS). Com um modulador sintético de 5ª ordem (OBG 1,3, 1 bit), o ruído total fica em −108,4 dBFS(A), ou seja, 2,1 dB acima do alvo da ficha (−110,5). **Essa diferença é do modulador sintético, não da cadeia**: a mesma sequência de bits, decimada de forma ideal (parede de tijolo 20 Hz–20 kHz), dá −108,5 dBFS(A); a cadeia inteira soma só +0,08 dB(A) em cima disso (sinc⁴: +0,19; sem sensor, com modulador de 4ª ordem: +0,11 contra +0,84 do sinc⁴). O ruído de arredondamento dos inteiros está dentro desses números. O modulador real do IM72D128 já está contado nos 71,5 dB(A) da ficha, então o número que vale é o excesso da cadeia.
Sem filtro, o ruído de quantização do modulador sintético sobe forte acima de 8 kHz (ver gráfico); o sinc⁵ mais as meias-bandas o seguram.

### 3.3 Distorção (`out/distorcao.png`)
Sensor linear, sem ruído, bin coerente (FFT de 65 536 pontos, Blackman-Harris). Harmônicas 2 a 5 de 41 Hz e de 1 kHz: de −133 a −170 dBc. THD+N (20 Hz–20 kHz): 41 Hz a −6 dBFS −96,0 dB; 41 Hz a −26 dBFS −74,9 dB; 1 kHz a −6 dBFS −95,6 dB; acorde de lá menor com E1 (5 tons a −20 dBFS) −88,3 dB; acorde forte (5 tons a −18 dBFS) −90,5 dB. Esses números são o piso de ruído (o THD em si é o ruído de quantização do modulador sintético), não distorção da cadeia; não aparecem produtos de intermodulação acima do piso.

### 3.4 Aliasing (`out/alias.png`)
Tons de 0,3 de amplitude entrando em 26 kHz a 1,4 MHz, medida a amplitude na frequência dobrada: 28 a 32 kHz −90 a −92 dB, 36 a 100 kHz −93 a −131 dB, acima de 150 kHz −120 a −170 dB. Pior caso analítico (qualquer frequência que dobra para dentro de 0–20 kHz): −88,1 dB. Um tom de 37,5 kHz (a ressonância do sensor) cai em 10,5 kHz a −92,7 dB. Tons entre 20 e 28 kHz dobram para 20–28 kHz, fora da banda de interesse (26 kHz → 22 kHz a −25 dB, como em qualquer conversor de 48 kHz).

### 3.5 Saturação (`out/saturacao.png`)
- **Sensor** (soft-clip ajustado para 10 % de THD em 128 dB SPL, que é a definição de AOP da ficha; a 125 dB dá 1,4 %): 120 dB SPL = −10 dBFS sem distorção, 124 dB = 0,5 %, 128 dB = 10 %. Acima de 126 dB o pico de saída praticamente não sobe mais (−4,3 dBFS no modelo): o pico por amostra **não separa** 127 de 130 dB SPL. O limiar SAT do sensor em −4,6 dBFS acende a partir de 127 dB SPL (sem acender em 126). O que o limiar significa precisa ser calibrado com o sensor real (§7).
- **Ganho:** a 1 kHz e −30 dBFS o pico segue o ganho exatamente até +30 dB (0 dBFS); acima disso corta no limite de 24 bits (sem volta de fase, sem *wrap*) e a SAT acende por corte.

### 3.6 Ganho e estalos (`out/ganho.png`)
Erro máximo de 0,0002 dB nos 29 degraus. Com rampa de um polo (`>> 9`) a banda lateral de um degrau de +1,5 dB em 1 kHz fica em −91 dB (seco: −70 dB); o salto 0 → +42 dB fica em −80 dB (seco: −54 dB). A variação de ganho por amostra cai de 16 % (+1,5 dB seco) e 99 % (+42 dB seco) para 0,03 % e 0,2 %.

### 3.7 Medidor e SAT (`out/medidor.png`)
- Limiares: erro de 0,00 dB a 1 kHz nos 11 degraus (−0,1 dB no "0": o degrau 0 dBFS vale pico ≥ −0,1 dBFS, e é o mesmo limite do SAT por corte). A 8 kHz e 16 kHz, o pico **por amostra** subestima o pico verdadeiro em até 1,25 dB no pior caso de fase (6 e 3 amostras por ciclo). Para um medidor de LEDs é aceitável; o bayan tem energia útil abaixo de ~4 kHz (erro máximo 0,3 dB em 4 kHz).
- Ataque: um pulso de uma amostra a −10 dBFS acende na hora, no bloco de 1 ms em que ocorre (7 LEDs).
- Queda: 20,0 dB/s (o LED de −42 apaga 2,05 s depois de um pico de −1 dBFS).
- SAT: um corte de 0,5 s mantém o SAT piscando por 1,94 s depois do último corte (2437 ms no total), a 7,8 Hz medidos em janela finita (8 Hz de projeto); os LEDs de −3 e 0 dBFS seguem o SAT exatamente. Sem evento (pico de −6 dBFS) o SAT fica apagado.

### 3.8 Arranque (`out/arranque.png`)
O DC de saída do IM72D128 é −80 dBFS (LR = GND) ou **−40 dBFS** (LR = VDD) segundo a ficha. Com o bloqueio de DC só de 2,8 Hz o canal L leva 130 ms para cair abaixo de −60 dBFS (pico de −55 dBFS depois de 100 ms, que com +42 dB viram −13 dBFS). Com o arranque rápido leva 12 ms (−72 dBFS depois de 100 ms). **O firmware deve usar o arranque rápido e manter saída e medidor mudos por 50 ms depois de ligar o PDM** (a ficha tem tom ocioso de até 3 ms e um tempo de arranque de dezenas de ms, ±0,5 dB e ±0,2 dB; os valores no PDF que consegui ler ficaram embaralhados, a confirmar).

### 3.9 Carga de CPU (`out/cpu.png`)
Conta de ciclos por amostra no Cortex-M0+ (sem multiplicador de 64 bits, 1 ciclo por `MULS`, carga de SRAM em 2 ciclos). **Hipóteses:** código e tabelas em SRAM (não em flash/XIP), sem esperas de barramento (os DMA do PIO e do USB roubam alguns ciclos), um núcleo só.

| Bloco | Rotina | Mc/s pessimista | Mc/s otimista |
|---|---|---|---|
| Desentrelaçar | 26 ciclos por word (192 000 words/s) | 5,0 | 5,0 |
| Sinc⁵ por LUT | 10 consultas × (6 \| 5 ciclos) + 8 por saída, 2 × 192 k saídas/s | 26,1 | 22,3 |
| Meia-banda 192 → 96 | 6 pares × (14 \| 10 ciclos) + 20 por saída | 20,0 | 15,4 |
| Meia-banda 96 → 48 | 18 pares × (14 \| 10) + 20 por saída | 26,1 | 19,2 |
| Compensação, DC | 28 e 14 ciclos por amostra | 4,0 | 4,0 |
| Ganho (produto de 64 bits 30 \| 20 ciclos), clamp, rampa | por quadro de 2 canais | 4,3 | 3,4 |
| Medidor | | 0,6 | 0,6 |
| USB (cópia de 24 bits + interrupção TinyUSB a 1 kHz) | **estimativa a verificar no F2** | 4,0 | 4,0 |
| LEDs (charlieplex, medidor), botões, flash | estimativa | 1,0 | 1,0 |
| **Total** | | **91,2** | **74,8** |

| Clock | pessimista | otimista |
|---|---|---|
| 133 MHz | 69 % | 56 % |
| 153,6 MHz | 59 % | 49 % |
| 200 MHz | 46 % | 37 % |

(Só o DSP, sem USB e LEDs, a 133 MHz: 65 % pessimista.) Alavancas já medidas, caso apertasse: sinc⁴ (−4,6 Mc/s, mais ruído dobrado), banda passante de 18 kHz na última meia-banda (47 taps em vez de 71, −8,1 Mc/s), apagar os taps externos de ±1 do Q17, e o desentrelaçamento feito no próprio PIO com duas máquinas de estado (−5 Mc/s, mas tem risco de temporização, ver §6).

## 4. O que ficou como suposição

1. **Ficha lida:** IM72D128**VV01** v1.2 (2025-05-04): sensibilidade −36 dBFS a 1 kHz e 94 dB SPL (±1 dB), AOP 128 dB SPL (10 % THD), SNR 71,5 dB(A) a 3,072 MHz (70,5 a 2,4 MHz), queda em 11 Hz, clock até 3,072 MHz no modo de alto desempenho (430 µA típicos por sensor), L/R por pino. **Daqui sai "130 dB SPL = 0 dBFS de seno"**, então 128 dB SPL ≈ −2 dBFS, e a SPEC ("0 dBFS ≈ 128 dB SPL") está na ordem certa de grandeza. Os intervalos exatos de clock de cada modo e o tempo de arranque saíram embaralhados do PDF e não foram usados.
2. **Sensor sintético, não o real:** ruído branco com SNR 71,5 dB(A); queda de 11 Hz de 1ª ordem (a ficha dá só a frequência); saturação por soft-clip tipo `x / (1 + |x/0,606|¹⁰)^0,1` calibrada para dar 10 % de THD em 128 dB SPL (não é a curva real, que a ficha não dá); modulador de 5ª ordem, 1 bit, OBG 1,3 (o interno do IM72D128 é desconhecido). DC de −40 e −80 dBFS conforme a ficha. A 130 dB SPL e acima, o modulador de 4ª ordem com OBG 1,5 saía da estabilidade; por isso o de 5ª com OBG 1,3.
3. **Limiar SAT (b):** −4,6 dBFS pico após o DC e antes do ganho é calibrado no modelo; só com o sensor real (alto-falante a 128 dB SPL, F3) sabemos em que dBFS o sensor real corta. O limiar é uma constante.
4. **CPU:** hipóteses da §3.9; sem compilar para o M0+ não sei o número de ciclos real dos laços, nem a espera da flash (a conta supõe tudo em SRAM).
5. **Calibração absoluta** (−36 dBFS a 94 dB SPL ±1 dB) vale para os dois canais com a mesma sensibilidade nominal; o pareamento L/R de ±1 dB é da ficha e nada o corrige no firmware (SPEC: sem processamento além de ganho e DC).

## 5. Riscos

1. **Clock PDM: jitter.** Com cristal de 12 MHz e `sys_clk` de 133 MHz, o divisor do PIO é fracionário e a borda do CLK treme de ±1 ciclo de `sys` (7,5 ns). Para um modulador de tempo discreto o efeito é desprezível (−100 dB), para um de tempo contínuo não sei, e a ficha não diz. `clock_plan.py` mostra que **com o cristal de 12 MHz de sempre dá para ter `sys_clk` = 153,6 MHz exatos** (VCO 768 MHz, 64/5, PIO ÷ 5 com 10 ciclos por período de PDM) **e USB em 48,000 MHz exatos**, tudo com divisor inteiro; o preço é rodar o RP2040 20 % acima dos 133 MHz da ficha (tensão do regulador interno a 1,15 V, que o SDK permite; a conferir na Fase 2). Outra opção: 147,43 MHz (−190 ppm no PDM). Um cristal de 12,288 MHz também fecha exato (e dá USB exato com refdiv 2 / fb 125), mas **o USB de boot do RP2040 pressupõe 12 MHz** e deixaria de funcionar; só sobraria o SWD. **Pergunta ao design / eletrônica no fim.**
2. **Tempo do PIO.** Os dois sensores só garantem dado válido 100 ns depois da borda (tDV) e soltam 5 a 30 ns depois da próxima. Com 10 ciclos por período a 153,6 MHz (32,6 ns por ciclo), a leitura cai 130 ns depois de cada borda, com 30 ns de margem; precisa do bypass do sincronizador de entrada do pino DATA. Com 133 MHz fracionário a margem é parecida. Isso só se confirma na bancada (osciloscópio) na Fase 2.
3. **Carga de CPU de 59 a 69 % de um núcleo.** Cabe, mas um USB com muita carga de interrupção, ou uma cópia mal feita, pode comer a margem. Plano: DSP em interrupção de DMA a 1 kHz no **núcleo 1**; USB, LEDs, botões, flash no núcleo 0.
4. **Variante do sensor.** Só a **VV01** (11 Hz) cumpre "−3 dB em ≤ 15 Hz"; a V01 cai em 20 Hz (§3.1).
5. **Sensores a 128 dB SPL com o sistema do celular.** Android e iOS podem aplicar filtros de graves e AGC conforme o app; fora do nosso controle (SPEC §6).
6. **Gravação em flash do ganho** (3 s depois da última mudança, rodízio em 4 setores): bloqueia o núcleo que executa da flash por alguns ms durante o apagamento; usar o núcleo 0 (UI) com o DSP em SRAM no núcleo 1, para não haver falha no áudio.
7. **Toolchain não instalada.** `arduino-cli core list` só tem `arduino:avr` e `teensy:avr`, sem arduino-pico, pico-sdk, nem arm-none-eabi-gcc. O F2 precisa instalar um deles (pico-sdk com CMake ou o núcleo arduino-pico); pergunto antes de instalar.

## 6. Plano do F2

Blocos do firmware (pico-sdk ou arduino-pico, a decidir com o J; recomendo pico-sdk + TinyUSB pelo controle do DMA/PIO):

1. **Clock e PLL:** `sys` 153,6 MHz e USB 48 MHz exatos (cristal de 12 MHz); opção de compilação para 133 MHz fracionário.
2. **PIO** `pdm_stereo` (programa de 4 instruções com `side-set` para o CLK, 10 ciclos por período, duas leituras por período em 130 ns depois de cada borda, `in pins,1` com autopush de 32 bits, deslocamento à esquerda, bypass do sincronizador no pino DATA) e **DMA** em anel de 192 words (1 ms), duas cadeias de canais ping-pong.
3. **DSP** (núcleo 1, em RAM): desentrelaçar, sinc⁵ LUT, as duas meias-bandas, compensação, DC, ganho; coeficientes e tabelas geradas por script a partir de `out/coeficientes.json`.
4. **Medidor e SAT** a 1 ms; 11 + 1 LEDs diretos por GPIO com PWM por brilho (o azul e os vermelhos).
5. **Barra de ganho:** 15 LEDs por charlieplexing (5 pinos), no máximo 2 LEDs acesos (posição ou meio passo), varredura a ≥ 1 kHz.
6. **Botões − e +:** repetição ao segurar (500 ms, depois 8 passos/s), debounce de 10 ms, passo de 1,5 dB; padrão +12 dB.
7. **Flash:** ganho guardado 3 s depois da última mudança, em 4 setores de 4 KB com 16 slots cada (rodízio; ≈ 6 milhões de gravações).
8. **USB:** áudio de entrada, 2 canais, 24 bits, 48 kHz, 288 bytes por frame de 1 ms; fonte assíncrona (sem endpoint de feedback; pacotes de 47, 48 ou 49 amostras guiados pelo nível do FIFO). **Dois caminhos, decididos em celular real na Fase 2:** (a) UAC2 com TinyUSB (já tem classe de áudio no pico-sdk); (b) UAC1 (descritores próprios, driver de classe do TinyUSB escrito à mão). Eu não sei qual dos dois cada Android e cada iPhone aceita sem teste; é item de verificação F3, com modelo, sistema e resultado.
9. **Consumo:** medir no hardware; estimativa preliminar: RP2040 a 153,6 MHz com um núcleo em DSP, 25 a 35 mA (a confirmar), 2 sensores = 0,9 mA, LEDs conforme a eletrônica. Com o limite de 100 mA do USB. **Quem fecha é a `POWER.md`.**
10. **Verificação sem hardware no F2:** compilação limpa (arm-none-eabi), teste no PC do mesmo código C do DSP contra a simulação em Python (mesmos vetores de bits), medida de ciclos no simulador se houver, e checagem cruzada do mapa de pinos × `pcb/PINOS.md`.

### Pinos que preciso da eletrônica (peço, não decido o contrato `pcb/PINOS.md`)

| Função | Quantidade | Requisitos |
|---|---|---|
| PDM CLK | 1 GPIO (saída) | com resistor série curto (cerca de 100 Ω) perto do RP2040; cada sensor recebe o mesmo CLK |
| PDM DATA | 1 GPIO (entrada), linha única compartilhada pelos dois sensores | o PIO lê o pino de DATA; a ficha usa terminação RTERM no barramento; preciso saber o valor |
| Medidor | 12 GPIOs (11 LEDs + SAT azul), diretos | um resistor por LED; corrente por pino dentro do limite do RP2040 |
| Barra de ganho | 5 GPIOs (charlieplexing, 15 LEDs) | um resistor por pino; a eletrônica confirma contra 2 × 74HC595 |
| Botões − e + | 2 GPIOs (entrada, pull-up interno) | |
| LR dos sensores | fixo em hardware | L = LR no VDD (DC −40 dBFS), R = LR no GND (DC −80 dBFS); me diga qual lado é L na placa, a troca é só um bit |
| Cristal | 12 MHz (padrão) | o plano de clock da §5 depende dele; **não use 12,288 MHz** sem falar comigo (USB de boot) |
| Teste | SWD (2 pinos) + BOOTSEL | já previstos |

Contando CLK + DATA + 12 + 5 + 2 = **21 GPIOs**, como na SPEC.

## 7. Verificação que fica para a Fase 2 (não tentada)

Ruído próprio medido com o sensor tapado, resposta contra um microfone de referência, calibração do limiar SAT (b) a 128 dB SPL, jitter do CLK no osciloscópio, margem de tempo do PIO, consumo real, e a lista de celulares (modelo, sistema, resultado) para UAC1 × UAC2. Nada foi gravado em hardware do J.

## Perguntas para o design

1. **Cristal e clock (R3MIC, §5-1):** posso contar com o cristal de 12 MHz comum e rodar o RP2040 a **153,6 MHz** (20 % acima do nominal, com a tensão do regulador interno em 1,15 V)? Se a resposta for "só 133 MHz", o PDM sai do divisor fracionário e o jitter da borda vira questão de bancada.
2. **Sensor:** confirmam que só se compra a **IM72D128VV01** (queda em 11 Hz)? A V01 (20 Hz) não cumpre a meta de graves.
3. **Mudos no arranque:** tudo bem a saída ficar muda por ~50 ms depois de ligar (o DC de −40 dBFS do L precisa assentar), e que o medidor também não reaja nesse tempo?
4. **Pior caso do pico por amostra:** o medidor mostra o pico **por amostra**, que subestima em até 1,25 dB tons de 8–16 kHz. Aceito, ou prefere um estimador de pico verdadeiro (custa uns 3 Mc/s)?
5. **SAT do sensor:** aceitam que o limiar seja uma constante calibrada na Fase 2 (hoje −4,6 dBFS no modelo), em vez de "128 dB SPL" fixo na SPEC? O pico por amostra do sensor real quase não sobe entre 126 e 130 dB SPL, então "128 dB" só se define de forma indireta (ou por THD).
6. **Ferramentas:** posso instalar o pico-sdk (cmake, arm-none-eabi-gcc) ou o núcleo arduino-pico na máquina do J para o F2? Qual dos dois prefere?
7. **UAC:** começo o F2 em UAC2 (TinyUSB nativo) e deixo o UAC1 como segundo caminho documentado, ou o contrário?
8. **Pinos:** a eletrônica fecha os 21 GPIOs acima em `pcb/PINOS.md`? Preciso do valor de RTERM e do resistor série do CLK, e de qual lado é L.
