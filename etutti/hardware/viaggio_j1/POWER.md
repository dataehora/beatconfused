# eTutti Viaggio J1 · orçamento de energia (placa real, passo M3)

SPEC v2.4. Dono: eletrônica. Escrito no M3 a partir da placa `kicad/viaggio_micromod.kicad_pcb` (J1), das peças do BOM (`fab/viaggio_j1_bom.csv`) e das medidas do Pocket (`pocket/POWER.md`, Teensy 4.0 do J, 17 out 2026).

Origem de cada número: **datasheet**, **medido** (no Pocket) ou **estimativa (conferir)**. Nada foi medido nesta placa: ela ainda não existe.

## O caminho da energia na placa

| Trecho | Peça | O que a placa tem |
|---|---|---|
| USB-C → VBUS | J201, U201 (ESD), D201 (TVS) | 2 × 5,1 kΩ nos CC (R201/R202): carregador USB-C dá 5 V sem negociação |
| VBUS → carregador | U202 BQ24074 (E3) | USB500 (EN1 = 1, EN2 = 0): ≤ 500 mA da USB; carga ICHG = 890 / 1,8 kΩ = **0,49 A** (R203); ILIM 1,5 kΩ (R204) |
| Bateria ↔ carregador | J202 (E6), NTC no TS | LiPo 1S ~1000 mAh com NTC de 10 kΩ |
| OUT do carregador = VSYS | C202, C203, **C210 (novo, junto dos pinos OUT)** | VSYS = 4,4 V com USB, = VBAT sem USB |
| VSYS → 3,3 V | U204 TPS63001 + L201 2,2 µH (E4), C206 na entrada, C207/C208 na saída | buck-boost 3,3 V fixo; EN = EN_REQ (clique OU KEEP OU USB_HOLD) |
| VSYS → alto-falante | U501 MAX98357A (A1), C501 | direto no VSYS, fora do 3,3 V |
| 3,3 V → tudo o mais | J101 (módulo), U301 (codec, com U302 de 1,8 V), T1/T2, T3, 28 TMAG5253, LED | plano de +3V3 no In2 |

**Queda no cobre** (cobre externo de 35 µm, In2 de 17,5 µm; ρ = 1,72 × 10⁻⁸ Ω·m; estimativa pelo comprimento das rotas):

| Rota | Largura | Comprimento (aprox.) | Resistência | Queda no pior caso |
|---|---|---|---|---|
| VSYS, carregador → amplificador (C6) | 0,8 | ~70 mm | ~45 mΩ | ~45 mV a 1 A de pico do amplificador |
| VSYS, carregador → U204 | 0,8 | ~12 mm | ~8 mΩ | ~4 mV a 0,5 A |
| VBUS, USB-C → carregador (C2) | 0,8 | ~60 mm | ~37 mΩ | ~19 mV a 0,5 A |
| VBAT, J202 → carregador (C7) | 0,8 | ~20 mm | ~12 mΩ | ~10 mV a 0,8 A |
| entradas de pino (0,24–0,3, ≤ 1,1 mm cada) | | | ≤ 2 mΩ cada | desprezível |

## Consumidores no trilho de 3,3 V (mA)

Cenário recomendado da SPEC: sensores TMAG5253BA3 ligados por grupo (S3), módulo a 396 MHz.

| Consumidor | típ. fone | máx. fone | típ. alto-falante | máx. alto-falante | origem |
|---|---:|---:|---:|---:|---|
| Módulo MicroMod Teensy (RT1062) a 396 MHz | 69 | 83 | 69 | 83 | modelo do Pocket (conferir) |
| Módulo: MKL02 do bootloader + LED azul do pino 13 | 3 | 5 | 3 | 5 | estimativa (conferir) |
| Codec SGTL5000 (U301 + U302) | 20 | 40 | 12 | 20 | datasheet / Audio Board (conferir) |
| 28 TMAG5253BA3, 14 ligados por vez (EN_A: fileiras 1 e 3; EN_B: 2 e 4) | 36 | 70 | 36 | 70 | datasheet (2,6 típ. / 5 máx. por sensor) |
| 2 × 74HC4067 + 3 portas 74LVC1G | 0,1 | 0,2 | 0,1 | 0,2 | datasheet |
| LED I3 (PWM, uma cor) | 2 | 8 | 2 | 8 | estimativa |
| **Total no 3,3 V** | **130** | **206** | **122** | **186** | |

Alto-falante (no VSYS): 0,20 W médios típicos / 0,50 W no pior caso, classe D com 80–85 % de eficiência, mais 2,4 mA de repouso do MAX98357A (datasheet). Os watts médios são estimativa (conferir de ouvido com o A2).

## Autonomia tocando sem parar, bateria de 1000 mAh

Capacidade útil 85 % de 3,7 Wh = 3,15 Wh. TPS63001 a 90 % (típ.) / 86 % (pior).

| Cenário | fone típ. | fone pior | alto-falante típ. | alto-falante pior |
|---|---:|---:|---:|---:|
| TMAG5253BA3 por grupo, 396 MHz | **6,6 h** | 4,0 h | **4,5 h** | 2,3 h |
| o mesmo a 600 MHz (módulo ~100 mA) | 5,4 h | 3,4 h | 3,9 h | 2,1 h |

## Parado e desligado

| Estado | Consumo | Bateria cheia dura |
|---|---:|---:|
| Ligado, sem tocar (amplificador desligado, sensores lidos com liga/desliga) | ~95 mA no 3,3 V (estimativa) | ~9 h |
| Desligamento leve (módulo a 24 MHz, codec desligado, sensores a 20 Hz) | ~23 mA (conferir) | ~35 h |
| **Desligado** (EN do TPS63001 baixo) | BQ24074 ~6 µA + divisor da bateria R208/R209 (2 MΩ) ~1,9 µA + TPS63001 desligado ≤ 1 µA = **~9 µA** | anos (fica a autodescarga) |

O divisor R208/R209 fica sempre na bateria: 1,9 µA, aceito (é o preço de medir a bateria sem um transistor a mais).

## Carga pelo USB-C

| Situação | Corrente na bateria | Carga completa (estimativa) |
|---|---:|---:|
| 1000 mAh, desligado | 0,49 A | ~2,5 h |
| 1000 mAh, tocando com fone (~0,1 A tirados da OUT a 4,4 V) | ~0,39 A | ~3,0 h |

- Entrada limitada a 500 mA (USB500), o que qualquer porta USB 2.0 dá.
- Carga só entre 0 e 50 °C (NTC no TS; datasheet).
- Luz de carga: ~2,8 mA da USB, só com o aparelho desligado (Q202 a desvia quando o 3,3 V está ligado).

## Para conferir no protótipo

1. Corrente real do 3,3 V com o módulo a 600, 396 e 240 MHz.
2. Corrente dos 28 sensores e o campo do ímã do Gateron no fundo do curso.
3. Volume confortável no alto-falante (potência média real).
4. Eficiência do TPS63001 com a carga real; temperatura do L201.
5. Corrente com o aparelho desligado (esperado ~9 µA).
