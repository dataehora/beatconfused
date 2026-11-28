# Liebling (Batschauer) — Orçamento de corrente (R3MIC, E2)

**Atende:** SPEC **R3MIC** (2 × IM72D128 + RP2040, medidor de 12 LEDs diretos + barra de ganho de 15 LEDs em charlieplex), meta **≤ 100 mA** do VBUS.
**Data:** 28 nov 2026. Números marcados como na `ELETRONICA.md`: **ficha**, **loja**, **conta**, **estimativa**.
Fontes: datasheet RP2040 (tabela 658, figura 173), W25Q16JV (ICC), IM72D128V01 e VV01 (corrente por clock), XC6206 (Pd, Iq), páginas de LED da loja (Vf).

## Resultado

| | Corrente do VBUS | Sobra para 100 mA |
|---|---|---|
| **Pior caso empilhado** (todos os máximos de ficha ao mesmo tempo, medidor todo aceso, ganho em 2 LEDs), variante A | **97,4 mA** | **2,6 mA (2,6 %)** |
| Idem, variante B (verde + SAT a 5 V pelo ULN2003A, LEDs a ≈ 2 mA) | **94,6 mA** | **5,4 mA** |
| **Pior caso realista** (RP2040 a 2/3 da carga máxima, flash com cache, medidor todo aceso) | **57,5 mA** | **42,5 mA** |
| Varredura de partida (15 LEDs de ganho, medidor apagado), pior caso | 69,9 mA | 30,1 mA |

**Fecha ≤ 100 mA, mas o pior caso empilhado fecha por pouco** (2,6 mA). Regra de projeto proposta: **a soma das correntes de LED, tudo aceso, ≤ 36 mA** (pior Vf), e o firmware limita o brilho médio (PWM) se precisar. Com os valores abaixo, a variante B tem uma folga um pouco maior e tira ≈ 22 mA do LDO.

## Premissas e valores

- **Tudo vem do VBUS de 5 V por um LDO linear** (XC6206): a corrente do VBUS é a do 3,3 V (mais Iq de 1 µA, ficha) mais a dos LEDs ligados ao 5 V.
- **Clock do sistema 125 MHz**; PDM a 3,072 MHz (conta; com 2,4 MHz e 120 MHz sobram ≈ 1,6 mA).
- **USB:** a Type-C anuncia ≥ 500 mA para um dispositivo USB 2.0 (regra da especificação, conta); 100 mA é meta própria da SPEC. O descritor declara 50 unidades (100 mA).
- **Capacitância no VBUS:** 10 µF na entrada do LDO (conta; a regra de partida a quente da USB é ≤ 10 µF).

### Consumo sem os LEDs

| Bloco | Pior caso (mA) | Típico de uso (mA) | Origem |
|---|---|---|---|
| RP2040 DVDD (núcleo, 125 MHz, 2 núcleos a plena carga) | **37** | 25 | ficha fig. 173 (leitura do gráfico ±2 mA): 29-37 mA; típico = 2/3 do máx. (conta). A 144 MHz seriam ≈ 43 |
| RP2040 IOVDD (pads, PDM, QSPI) | 4,3 | 1,2 | ficha, tabela 658 (BOOTSEL) |
| RP2040 USB_VDD (PHY) | 2,0 | 1,4 | ficha, tabela 658 |
| Flash W25Q16JV, leitura | **18** | 4 | ficha: ICC3 6 mA típ. e 18 mA máx. a 80 MHz (o clock do flash é ≈ 62 MHz); gravação 20/25 mA ocorre só 3 s depois de mexer no ganho |
| 2 × IM72D128VV01 a 3,072 MHz | 1,05 | 0,86 | ficha: 525 µA máx. e 430 típ. por microfone |
| (2 × V01 no lugar) | (2,24) | (1,96) | ficha: 1 120 / 980 µA por microfone → **+1,2 mA** |
| LDO XC6206, Iq | 0,003 | 0,001 | ficha |
| **Subtotal sem LEDs** | **62,35** | **32,5** | conta |

### LEDs — variante A (medidor direto nos GPIOs a 3,3 V, resistor 330 Ω)

Corrente por LED = (VOH − Vf) / R, com VOH ≈ 3,2 V (conta) e Vf nos limites da loja:

| LED | Qtd | Vf (loja) | mA por LED (Vf mín. → máx.) | Pior caso (mA) | Típico (mA) |
|---|---|---|---|---|---|
| Vermelho 0805 | 2 | 1,6-2,6 V | 4,8 → 1,8 | 9,7 | 7,3 |
| Amarelo 0805 | 3 | 1,8-2,4 V | 4,2 → 2,4 | 12,7 | 10,0 |
| Verde "Emerald" 0805 | 6 | **2,6-3,1 V** | 1,8 → 0,3 | 10,9 | 6,4 |
| Azul 1206 (SAT) | 1 | 3,1 V | ≈ 0,6 | 0,6 | 0,3 |
| **Medidor, todo aceso** | 12 | | | **33,9 ≈ 34** | 24,0 |
| Barra de ganho: 2 LEDs (meio degrau) a 0,5 mA médios | 2 | | | 1,0 | 1,0 |
| Barra de ganho: 15 LEDs (varredura de partida, medidor apagado) | 15 | | | 7,5 | 7,5 |

Os 6 verdes e o azul recebem **menos de 2 mA** e variam de 6 vezes entre unidades (a folga de tensão é de 0,1 a 0,6 V): **o orçamento fecha, mas o brilho é o problema**, não a corrente.

**Pior caso empilhado A:** 62,35 + 33,9 + 1,0 = **97,3 ≈ 97,4 mA**. **Realista A:** 32,5 + 24,0 + 1,0 = **57,5 mA**.

### LEDs — variante B (6 verdes + SAT a 5 V por ULN2003A, resistor 680 Ω; vermelho e amarelo diretos a 3,3 V com 680 Ω)

| Grupo | Qtd | mA por LED | Pior caso (mA) | Onde passa |
|---|---|---|---|---|
| Verde + azul pelo ULN2003A, lado baixo, VCE(sat) ≈ 0,9 V, R = 680 Ω | 7 | 2,2 (Vf 2,6) → 1,5 (Vf 3,1) | 15,4 | **VBUS direto (5 V)**, não passa pelo LDO |
| Entradas do ULN2003A (2,7 kΩ internos a 3,3 V) | 7 | ≈ 0,7 | 4,9 | 3,3 V (a ficha do ULN é de memória, **conferir**) |
| Vermelho (2) + amarelo (3), R = 680 Ω | 5 | 2,4 → 2,1 | 10,9 | 3,3 V |
| **Subtotal LEDs de medidor** | | | **31,2** | |
| Barra de ganho: 2 LEDs | | | 1,0 | 3,3 V |

**Pior caso empilhado B:** 62,35 + 31,2 + 1,0 = **94,6 mA**. A corrente pelo LDO é 62,35 + 4,9 + 10,9 + 1,0 = **79,2 mA**, contra 97,4 mA na A.

## LDO: dissipação (conta)

| | Variante A | Variante B |
|---|---|---|
| Corrente no LDO, pior caso | 97,4 mA | 79,2 mA |
| P = (5,25 V − 3,3 V) × I | **0,19 W** | **0,154 W** |
| Limite (ficha, Pd em SOT-23) | 0,25 W | 0,25 W |
| Tj a 25 °C de ambiente (θJA ≈ 400 K/W, deduzido do Pd) | ≈ 101 °C | ≈ 87 °C |
| Tj a 40 °C de ambiente | ≈ 116 °C | ≈ 102 °C |

O pior caso A fica a 76 % do limite da ficha e perto de 125 °C no sol dentro do carro (celular em live ao ar livre). A variante B ou o TLV75533 (SOT-23-5) dão folga. A ficha do XC6206 só dá Pd, não dá θJA; o número é dedução.

## Pontos para a E3 e o firmware

1. **Regra de LED:** soma das correntes dos LEDs, tudo aceso, ≤ **36 mA** no pior caso de Vf (hoje: A = 34, B = 31). O firmware pode reduzir o PWM do medidor se a corrente medida subir (não há sensor de corrente na placa; é regra de projeto, não medição).
2. **PDM a 2,4 MHz, sysclk 120 MHz:** −1,6 mA no pior caso (conta), −1 dB de SNR (ficha). Já pedido ao firmware na `ELETRONICA.md`.
3. **Gravação do ganho** (flash 20-25 mA por ≈ 1-4 ms por página, ficha): ocorre 3 s depois da última mudança, mesma ordem de grandeza da leitura; incluída no pior caso (18 mA de leitura < 25 mA de gravação: **+ 7 mA nesse instante**, que ainda cabe: 97,4 + 7 = 104 mA nos poucos milissegundos, só se tudo mais estiver no máximo). **Mitigar:** gravar com o medidor em baixo brilho ou entre varreduras.
4. **Medir na Fase 2:** corrente real no VBUS (microamperímetro) com e sem LEDs, em 3 celulares; temperatura do LDO em ambiente de 40 °C.
5. **Capacitores:** 10 µF na entrada do LDO (limite de partida a quente) e 10 µF na saída (+ 100 nF por pino do RP2040).

## Perguntas para o design

1. A variante B (ULN2003A, 5 V para verde e SAT) é aceitável em área e ordem das cores na placa de 72 × 22 mm, ou o design prefere tudo a 3,3 V (variante A, brilho desigual no verde e no azul)?
2. O medidor deve atingir o brilho máximo (≈ 3 mA/LED) o tempo todo, ou o firmware pode usar brilho de ≈ 2 mA com PWM sem desagradar o J? A diferença é de ≈ 10 mA no pior caso.
3. Vale gastar 0,02-0,30 US$ por placa num LDO melhor (TLV75533, SOT-23-5) só para ganhar folga térmica e de ruído, ou fica o XC6206 Basic?
