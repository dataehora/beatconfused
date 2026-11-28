# Liebling (Batschauer) — Eletrônica, E1 (peças) e E2 (custo e energia)

**Atende:** SPEC **R3MIC** (versão A: 2 × IM72D128 PDM + RP2040), blocos R3MIC §7 (ajustes às tarefas) e §12 da R2MIC.
**Data das consultas:** 28 nov 2026. **Nada foi comprado nem encomendado** (Fase 1).
**Autor:** agente `mic-eletronica`. Só escrevi em `minimic/pcb/`, `minimic/ELETRONICA.md` e `minimic/POWER.md`.

**Convenção dos números:** **ficha** = datasheet do fabricante (citado); **loja** = biblioteca de peças da JLCPCB/LCSC no dia
da consulta (preço, estoque, Basic/Extended); **conta** = cálculo meu a partir de fichas/lojas; **estimativa** = sem cotação nem ficha.
Consulta de preço repetível: `python minimic/pcb/consulta_jlc.py "<busca ou código>"` e `python minimic/pcb/custo_e2.py`
(curl na biblioteca da JLCPCB, 2 s entre pedidos; resultados em `minimic/pcb/build/`).

---

## Resumo (o que decidir primeiro)

| # | Achado | Efeito |
|---|---|---|
| 1 | **IM72D128VV01 (11 Hz) está com estoque 0 na JLCPCB/LCSC** (loja, 28 nov); a V01 (20 Hz) tem 4 837 un. na JLCPCB. Distribuidor: Element14 mostra 2 300 un. (NZ) e 3 645 (MY); Future Electronics 0 em estoque, prazo 30 semanas, MOQ 5 000 | **Risco nº 1.** A meta R3MIC "−3 dB em ≤ 15 Hz" só é possível com a VV01 (a V01 já está −3 dB em 20 Hz, só no sensor) |
| 2 | Os plugues USB-C **machos de placa com eixo no plano da placa** que a JLCPCB lista (JXTCONN MBB008 e MAB169, tipo "clamp plate") são desenhados para **placa de 0,80 mm** (ficha). **Não existe nenhum para 1,2 mm** na biblioteca. Os machos de 1,2 mm/THT que achei são **verticais** (eixo perpendicular à placa) | A SPEC fixa 1,2 mm. **Pergunta nº 1 ao design:** placa de 0,8 mm? |
| 3 | O plugue "clamp" tem terminais **nas duas faces**; a montagem Economic solda **uma face só** | A face de baixo do plugue (e as pernas da carcaça) fica à mão, ou montagem Standard (duas faces) |
| 4 | O **verde 0805 Basic** (KT-0805G) é "Emerald 525 nm", **Vf 2,6-3,1 V**; azul e branco também ~3 V. Com GPIO a 3,3 V sobra de 0 a 0,6 V | O brilho do verde/azul/branco com resistor direto no GPIO varia muito. Proposta: lado baixo a 5 V com **ULN2003A (Basic)** para verde + SAT |
| 5 | O canal R (SELECT = VDD) sai com **DC de −40 dBFS** (L: −80 dBFS), ficha | O primeiro LED do medidor (−42 dBFS) acende até o bloqueio de DC assentar. Pedido ao firmware |
| 6 | O clock PDM de 3,072 MHz **não sai exato** de um cristal de 12 MHz (PLL do RP2040) | Sugestão: **2,4 MHz com sysclk de 120 MHz** (÷ 50 = 48 kHz exato), −1 dB de SNR. Pedido ao firmware |
| 7 | Soma dos máximos de ficha, medidor todo aceso: ≈ 98 mA (fecha por 2 mA); uso realista ≈ 58 mA (ver `POWER.md`) | Fecha ≤ 100 mA, mas com margem fina no pior pior caso |
| 8 | Custo de peças por placa (conta, VV01): **US$ 6,59 a 10 un. e 5,88 a 100 un.**; com taxas de pedido e PCB (estimativa): **≈ US$ 10,7-13,9 (10 un.) e ≈ 6,6-7,9 (100 un.)** | Dentro do alvo da SPEC (≤ US$ 10 por placa montada em lote de 100). Com V01: +US$ 0,77 a 100 un. |

---

## E1 — Peças conferidas na fonte

### E1.1 Microfone: IM72D128 (e fallback IM69D130)

Fontes: datasheet **IM72D128V01** v1.01 (2022-05-05, PDF do LCSC `…/b44a2e9f4223ecf8b5b0d8417b7f8e21.pdf`, é o V01 apesar de ligado ao código da VV01);
datasheet **IM72D128VV01** rev. 1.1 (2025, versão em chinês no site da Infineon `infineon-im72d128v-datasheet-cn.pdf`; a Infineon diz que o original em inglês é o documento de controle);
página da peça na JLCPCB (`jlcpcb.com/partdetail/C5119248` e `C36405960`); Element14 e Future Electronics (via busca).

| Item | **IM72D128V01** | **IM72D128VV01** | IM69D130 (fallback) |
|---|---|---|---|
| SNR a 3,072 MHz | 72 dB(A) (ficha) | **71,5** dB(A) (ficha) | 69 dB(A) (ficha, via distribuidor; não li o PDF) |
| SNR a 2,4 MHz / 1,536 MHz | 71,5 / 68 (ficha) | 70,5 / 70 (ficha) | — |
| AOP (10 % THD) | 128 dB SPL (ficha) | 128 dB SPL (ficha) | 130 dB SPL (ficha, via distribuidor) |
| Sensibilidade | −36 dBFS a 94 dB SPL, ±1 dB (ficha) | idem (ficha) | — |
| **Queda de graves (−3 dB)** | **20 Hz** (ficha) | **11 Hz** (ficha); limites a 10 Hz: −1,5/−4,5 dB (ficha) | tabela: −5 dB a 25 Hz, −1,5 dB a 60 Hz (ficha parcial) |
| Corrente a 3,072 MHz, VDD 1,8 V | 980 típ. / 1 120 máx. µA (ficha) | **430 típ. / 525 máx.** µA (ficha) | ~980 µA (de memória, não conferido) |
| Corrente a 2,4 MHz | 820 / 945 µA (ficha) | 390 µA (ficha; máx. não lido) | — |
| Alimentação | 1,62-3,6 V (ficha) | 1,62-3,6 V (ficha) | — |
| Clock PDM aceito | 2,9-3,3 MHz (alto desempenho), 2,0-2,6 MHz, 1,2-1,65, 0,45-0,85 MHz (ficha) | 2,9-3,4; 1,9-2,6; 1,17-1,70; 0,73-1,02 MHz (ficha) | — |
| Partida | 20 ms (±0,5 dB) / 50 ms (±0,2 dB) após VDD e clock; tom ocioso (1010…) em 3 ms (ficha) | idem (ficha) | — |
| PSR | −80 dBFS com 100 mVpp (200 Hz-20 kHz); −86 dBFS(A) a 217 Hz (ficha) | idem (ficha) | — |
| Encapsulamento | PG-LLGA-5-3, **4 × 3 × 1,2 mm**, porta **por baixo** (furo na placa Ø 0,8 mm recomendado) (ficha) | idem (ficha) | LGA-5 4 × 3 mm |
| Pinagem | 1 DATA, 2 VDD, 3 CLOCK, **4 SELECT**, 5 GND (anel redondo com a porta) (ficha) | 1 DATA, 2 VDD, 3 CLOCK, **4 LR**, 5 GND (ficha) | — |
| SELECT / LR | GND = canal "DATA1": dado na **borda de descida** do clock; VDD = "DATA2": borda de **subida**; fora do seu turno a saída fica em alta impedância (dois microfones dividem uma linha) (ficha) | idem | — |
| DC de saída | **SELECT em GND: −80 dBFS; em VDD: −40 dBFS** (ficha, §3.4) | idem | — |
| Capacitores (ficha) | 1 µF perto do VDD "para melhor SNR" e 100 nF; resistor de ~100 Ω em série na saída é opcional | idem | — |
| Reflow | MSL 1, pico 260 °C; **não aplicar vácuo na porta, não lavar, sem ultrassom** (ficha) | idem | — |
| **JLCPCB** | **C5119248**, Extended, SMT **Economic e Standard**, dificuldade "High", MSL 1 (loja, página da peça) | **C36405960**, Extended, SMT Economic e Standard (loja) | **C536262** (V01), Extended |
| **Estoque JLCPCB** | **4 837** (loja) | **0** (loja) | 992 (loja) |
| **Preço JLCPCB, 10 / 100 un.** | US$ 2,6476 / 2,0505 (loja) | US$ 1,7224 / 1,6650 (loja, **mas estoque 0, o preço é de tabela**) | US$ 2,6312 / 2,0144 (loja) |
| Distribuidor | — | Element14: 2 300 (NZ) e 3 645 (MY) em estoque; Future: estoque 0, 30 semanas, MOQ 5 000 a US$ 1,44 (busca, a reconferir) | — |
| Global Sourcing | a página da peça não indica | não indica (estoque 0 = não montável hoje) | — |

**Leituras.**
- O sensor **não** limita o bayan: a fundamental E1 (41 Hz) cai −0,9 dB com a V01 e −0,3 dB com a VV01 (conta: passa-altas de 1ª ordem com corte em 20 e 11 Hz).
  A 15 Hz a V01 já está em ≈ −4,4 dB e a VV01 em ≈ −1,9 dB (conta). **Só a VV01 permite a meta R3MIC (−3 dB em ≤ 15 Hz na cadeia)**, e mesmo ela fica sem folga (o bloqueio de DC de 3 Hz do firmware soma ≈ −0,2 dB a 15 Hz).
- A VV01 é **2,3 vezes mais econômica** (0,43 contra 0,98 mA) e **0,5 dB pior em SNR** (71,5 contra 72 dB(A)); para 2 mics isso poupa ≈ 1,1 mA (conta). Preço de tabela também menor (−US$ 0,9 por sensor a 10 un.).
- **Dois microfones numa linha:** a ficha mostra exatamente essa ligação (Figura 11 da V01): CLOCK comum, DATA comum, **um em GND e o outro em VDD**. O RP2040 amostra a mesma linha nas duas bordas do clock. Não há risco de colisão (um fica em alta impedância enquanto o outro dirige).
- **Porta por baixo:** o furo Ø 0,8 mm atravessa a placa; a espuma Ø 10 vai **na face oposta à do microfone** (informação para o design e para a E4).
- **Estoque (risco nº 1):** a peça de que a meta precisa (VV01) **não pode ser montada hoje pela JLCPCB**. Caminhos, do mais simples ao mais caro: (a) **V01 no primeiro lote** (estoque 4 837, +US$ 1,85 por placa a 10 un. e +0,77 a 100, conta; perde as metas de 15 Hz, os graves do bayan continuam bons); (b) esperar o estoque da VV01 na JLCPCB (não há previsão na loja); (c) comprar a VV01 em distribuidor e enviar à JLCPCB como peça consignada, ou soldar em casa (ar quente; LLGA 4 × 3 mm, MSL 1). **Decisão do J, só na Fase 2.**
- IM69D130 serve de plano B (estoque 992, mesma classe de preço, mesmo encapsulamento), mas **perde 0,5 dB em ruído e tem pior resposta em graves** (−5 dB a 25 Hz): fica como último recurso.

### E1.2 Microcontrolador, flash e cristal

Fontes: LCSC/JLCPCB (loja); datasheet RP2040 (Raspberry Pi, `pip-assets.raspberrypi.com/…RP-008371-DS-2-rp2040-datasheet.pdf`, tabela 658 e figura 173);
datasheet W25Q16JV (LCSC `…00c0cda1ff35fc6f66162467dae0bd73.pdf`).

| Peça | Código | Pacote (loja) | Classe | Estoque | US$ 10 un. / 100 un. (por unidade) | Observação |
|---|---|---|---|---|---|---|
| **RP2040** | **C2040** | LQFN-56 (7×7) | **Extended** | 89 457 | 1,0023 / 0,8580 | −20…+85 °C (loja). Só este código tem estoque; os outros (C2961140, C2761095…) têm 0. Footprint pretendido: QFN-56 7×7, passo 0,4, pad térmico ≈ 3,2 mm: **conferir contra o EasyEDA na E3** |
| Flash **W25Q16JVSNIQ** (16 Mbit, QSPI) | **C2456211** | SOIC-8 | Extended | 20 354 | 0,9695 / 0,7234 | **SNIQ = SOIC-8 150 mil (corpo 3,9 mm)**, não 208 mil (o "SSIQ" é 208 mil). Footprint `SOIC-8_3.9x4.9mm_P1.27mm`. ICC de leitura: 6 mA típ. / **18 mA máx.** a 80 MHz; 8/20 mA a 104 MHz; gravação/apagamento 20/25 mA (ficha) |
| Flash Basic (plano B de classe) | C97521 W25Q128JVSIQ | SOIC-8-208mil | **Basic** | 61 499 | 1,8701 / (ver `custo_e2`) | 128 Mbit, **208 mil** (footprint diferente). Basic, mas +US$ 0,59 por placa a 10 un. (o tipo Extended dilui em 10 placas) |
| **Cristal 12 MHz** | **C9002** YXC X322512MSB4SI | SMD3225-4P | **Basic** | 491 332 | 0,0901 / 0,0711 | ±10 ppm, CL 20 pF, **ESR 80 Ω** (loja). A recomendação da Raspberry Pi é um cristal de ESR baixo (o ABM8-272 do Pico): **ESR 80 Ω é a dúvida desta escolha**; conferir no capítulo de cristal do datasheet do RP2040 antes da E3 (risco baixo/médio, resistor de 1 kΩ em série na saída) |

**RP2040, consumo (ficha, tabela 658 e figura 173):** "popcorn" DVDD 10,9 típ./16,6 máx. mA, IOVDD 24,8/35,5 mA (o programa de teste liga muitos pinos); modo BOOTSEL: DVDD 9,4/14,7, IOVDD 1,2/4,3, **USB_VDD 1,4/2,0 mA**. Figura 173 (FFT nos dois núcleos): DVDD ≈ 29-37 mA a 125 MHz, inclinação ≈ 0,29 mA/MHz (**leitura do gráfico, ±2 mA**).

### E1.3 LDO 3,3 V e filtro dos microfones

A ficha dos microfones diz: PSR de −80 dBFS com 100 mVpp (conta: o ruído de uma fonte de 50 µV rms entra a −137 dBFS, muito abaixo do piso de −108 dBFS do sensor). O que pesa é a **ondulação de baixa frequência** que o próprio RP2040 e os LEDs fazem no 3,3 V, não o ruído do regulador.

| LDO | Código | Pacote | Classe | Estoque | US$ 10 / 100 | Notas |
|---|---|---|---|---|---|---|
| **XC6206P332MR (Torex)** — **escolha** | **C5446** | SOT-23 (3 pinos) | **Basic** | 461 517 | 0,1334 / 0,1068 | 200 mA, queda ≈ 250 mV a 100 mA, VIN até 6,0 V, Iq 1 µA típ.; **Pd 250 mW em SOT-23**; **PSRR ruim: ≈ 30 dB a 1 kHz e ≈ 15-20 dB a 3-10 kHz** (ficha, figura 11). **Pinagem SOT-23: 1 = VSS, 2 = VOUT, 3 = VIN** (ficha; armadilha: não é a de outros LDOs) |
| TLV75533PDBVR | C404027 | SOT-23-5 | Extended | 63 040 | 0,12 / ~0,09 | 500 mA, ruído e PSRR bem melhores (de memória; não li a ficha) |
| RT9013-33GB | C47773 | SOT-23-5 | Extended | 306 433 | 0,1351 / — | idem |
| TPS7A2033 | C2862740 | SOT-23-5 | Extended | 65 181 | 0,2035 / — | ultrabaixo ruído, mais caro |

**Escolha: XC6206 (Basic) + filtro RC só para os microfones.** Argumento (conta): com a PSRR de 30 dB a 1 kHz, uma ondulação de 20 mV no 3,3 V (carga dos LEDs e do núcleo) vai a ≈ 20 mV no microfone; o filtro **R = 22 Ω (C25092, Basic) + C = 10 µF (C19702, Basic)** põe o polo em ≈ 720 Hz (≈ −3 dB a 720 Hz, −20 dB a 7 kHz) com queda de apenas ≈ 44 mV de corrente de 2 mA, mais o **1 µF + 100 nF por microfone** que a ficha recomenda. Os dois microfones usam o mesmo filtro. Se a medição na Fase 2 mostrar ruído de alimentação audível, troca-se o LDO pelo TLV75533 (+US$ 0,30 por placa a 10 un.; pino a pino não: SOT-23-5, outro footprint).
**Calor:** pior caso de carga ≈ 98 mA com VBUS de 5,25 V: 0,19 W (conta), abaixo dos 250 mW da ficha, mas com Tj ≈ 100 °C a 25 °C de ambiente (θJA ≈ 400 K/W deduzido de Pd). **Ver `POWER.md` e a proposta de tirar os LEDs verde/azul do 3,3 V.**

### E1.4 Plugue USB-C macho (o ponto mecânico)

Requisito: eixo no plano da placa, na borda de 72 mm, carcaça metálica, pernas soldadas; montável pela JLCPCB.
Fontes: desenhos dos fabricantes (PDFs do LCSC), páginas das peças na JLCPCB (`partdetail`).

A biblioteca da JLCPCB tem pouquíssimos conectores **machos**. A busca por "Type-C male" devolve sobretudo **fêmeas** com o campo "Gender" errado na loja (por exemplo, C3151751 SHOU HAN GTJB040 e C3039321 aparecem como "male", mas a ficha mostra que o primeiro é tomada de chapa e o segundo, macho vertical). **Li os desenhos** dos candidatos:

| Peça | Código | Tipo (ficha) | Placa | Retenção da carcaça | Comprimento externo | Classe, estoque, US$ 10 un. / 120 un. | Conclusão |
|---|---|---|---|---|---|---|---|
| **JXTCONN TYPE-C-MBB008** | **C53432944** | macho de **chapa (clamp)**, 24 contatos, USB 2.0, 5 A | **0,80 ± 0,05 mm**; entalhe na borda da placa **6,25 mm × 0,65 mm**; 24 terminais a 0,5 mm, pernas SMD | **laser weld 100 N mín.; carcaça 15 kgf (≈ 147 N) de extração** (ficha) | 10,25 ± 0,08 mm, plugue 8,25 × 2,4 mm | Extended, 245, US$ 0,4183 / 0,3134 | **Escolha** (a mais firme que achei em plano) |
| JXTCONN TYPE-C-MAB169 | C53432943 | macho de chapa, **16 contatos**, 3 A | 0,80 ± 0,05 mm; contorno de placa em degraus (7,90 / 7,20 / 6,50 mm, 6,30 mm de profundidade) | carcaça **50 N mín.** | 10,25 mm | Extended, 155, US$ 0,3631 (1 un.) / 0,2868 (50) | Funciona (USB 2.0 + CC), **3 vezes menos firme** na ficha e estoque menor |
| Hanbo MC-239 / BXCONN TYPE-C-24P-GON-LT | C3039321 / C54444662 | macho **vertical** (eixo ⟂ à placa), 11,1 mm de altura, pernas THT | 0,8 ± 0,1 mm (ficha) | 4 pernas THT + terminais THT: o mais firme mecanicamente | 11,1 mm | Extended, 374 / 371 | **Não serve** ao conceito "queixo" em linha (o plugue sairia perpendicular à placa) |
| SHOU HAN GTJB040 e outras "clamp plate" | C3151751 etc. | **fêmea** (tomada) | — | — | — | — | descartadas (são receptáculos) |

**Achados que mudam o projeto (perguntas ao design, abaixo):**
1. **Placa de 0,8 mm, não 1,2 mm.** Nenhum macho de chapa da biblioteca é para 1,2 mm (conta/ficha: MBB008 e MAB169 pedem 0,80 ± 0,05 mm). A JLCPCB faz 0,8 mm sem sobretaxa de 2 camadas (conferir na cotação). A rigidez de 72 × 22 × 0,8 mm é o que o estudo de alavanca do design precisa checar.
2. **Duas faces.** O plugue de chapa tem terminais de contato (12 por face no MBB008) e pernas da carcaça **em cima e embaixo**. Economic solda **uma face**; a outra metade (e as pernas) ficam à mão, ou Standard (duas faces, preparação e estêncil em dobro, conta ≈ +US$ 10). **Pergunta à JLCPCB (DFM) na Fase 2.**
3. **Corrente de contato.** O MBB008 tem 24 contatos mas só usamos VBUS, GND, D+, D−, CC (A5). No plugue **a B5 é VCONN**: o resistor Rd de 5,1 kΩ vai **só no CC (A5)**; B5 fica sem conexão (conta, regra do USB Type-C para dispositivo com plugue; **conferir na E3**).
4. **Resistência mecânica real não foi medida.** A ficha dá a retenção da carcaça, não a da solda sobre uma placa de 0,8 mm sob alavanca de 36 mm. **Teste de Fase 2** (puxar/torcer em 5 placas); a mitigação barata é epóxi/adesivo no plugue ou mais pontos de solda.

### E1.5 Botões táteis SMD baixos (− e +)

| Peça | Código | Corpo | Altura | Força | Classe | Estoque | US$ 10 / 100 | |
|---|---|---|---|---|---|---|---|---|
| **TS-1187A-B-A-B (XKB)** | **C318884** | SMD-4P 5,1 × 5,1 mm | **1,5 mm** | 1,6 N | **Basic** | 620 598 | 0,0197 / 0,0150 | **Escolha** (loja) |
| ALPS SKRPACE010 | C139797 | 4,2 × 3,2 mm | 2,5 mm | 2,6 N | Extended | 129 150 | 0,0665 / 0,054 | alternativa mais compacta, mais alta e Extended |

Conferir o footprint de 4 pinos (SPST, 2 + 2 ligados) com o EasyEDA na E3.

### E1.6 LEDs

Fonte: loja (JLCPCB/LCSC, parâmetros do fabricante). Todos os códigos de 0603/0805/1206 conferidos pelo encapsulamento da loja.

| Uso | Peça | Código | Pacote | Classe | Estoque | Vf (loja) | I típ. (loja) | US$/un. 10 / 100 |
|---|---|---|---|---|---|---|---|---|
| Barra de ganho, branco | KT-0603W (KENTO) | **C2290** | 0603 | **Basic** | 2 217 933 | 2,6-3,1 V | 5 mA (360 mcd, lente amarela) | 0,0123 / 0,0083 |
| Medidor verde (6) | KT-0805G (KENTO), "Emerald" 525 nm | **C2297** | 0805 | **Basic** | 2 817 615 | **2,6-3,1 V** | 5 mA (430 mcd) | 0,0165 / 0,0128 |
| Medidor amarelo (3) | KT-0805Y | **C2296** | 0805 | **Basic** | 388 163 | 1,8-2,4 V | — (175 mcd) | 0,0149 / 0,0149 |
| Medidor vermelho (2) | NCD0805R1 (Nationstar) | **C84256** | 0805 | **Basic** | 3 408 947 | 1,6-2,6 V | 25 mA máx. (195 mcd) | 0,0134 / 0,0134 |
| SAT azul | KT-1206B (KENTO) | **C72691** | **1206** | **Extended** | **1 102** | **3,1 V** | 5 mA (30-70 mcd) | 0,0212 / 0,0212 |
| (alternativa SAT 0805 azul) | KT-0805B | C2293 | 0805 | Extended | 38 816 | 3,1 V | 5 mA (100 mcd) | — |

**Achados:**
- Todos os LEDs são **Basic exceto o azul**: o azul custa **um tipo Extended (US$ 3,09 por pedido)**. Não existe azul Basic na biblioteca (busquei 0603, 0805 e 1206). Estoque do KT-1206B é **baixo (1 102)**, suficiente para ≤ 1 100 placas (risco baixo).
- **O verde Basic não é verde comum** (525 nm, InGaN): Vf 2,6-3,1 V. Os GPIOs do RP2040 sobem a 3,3 V (VOH ≈ 3,2 V com 4 mA, conta): sobram **0,1 a 0,6 V** para o resistor, a corrente varia de ≈ 0,3 a 1,8 mA com R = 330 Ω e o brilho dos 6 verdes seria desigual. Branco (2,6-3,1 V) e azul (3,1 V) têm o mesmo problema. Vermelho (1,6-2,6 V) e amarelo (1,8-2,4 V) estão bem a 3,3 V (≈ 3-4 mA com 330 Ω).
- **Proposta (E3 decide):** acionar **verde (6) + SAT azul (1) = 7 LEDs** pelo lado baixo a **5 V** com um único **ULN2003A SOIC-16 (C7512, Basic, 7 canais, 382 345 em estoque, US$ 0,1447 a 1 un.; 0,0934 a 150)**: o brilho passa a não depender da Vf, o LDO deixa de carregar essa corrente e o custo é ≈ +US$ 0,15/placa. Vermelho e amarelo (5) ficam direto nos GPIOs. **Branco da barra de ganho:** continua por charlieplex a 3,3 V (resistor de 1 kΩ, ≈ 0,3-0,6 mA com Vf 2,6-2,9 V; "fraco", como a SPEC quer, mas varia ± 2:1, **medir na Fase 2**).
  Custos e área: um SOIC-16 (≈ 10 × 4 mm) cabe na faixa de 22 mm; **pergunta 3 ao design**.

### E1.7 Barra de ganho: charlieplexing × 2 × 74HC595

| | Charlieplex (5 pinos) | 2 × 74HC595 |
|---|---|---|
| Peças | **5 resistores** (1 kΩ, Basic) | 2 CI SO-16 **Basic** (C5947, 430 704 em estoque, US$ 0,0749 a 50 un.) + **15 resistores** |
| GPIOs | 5 (de ≈ 9 livres, conta) | 3 (SER, SRCLK, RCLK) |
| Custo adicional por placa | ≈ US$ 0,007 | ≈ US$ 0,17 (conta: 2 × 0,0944 a 10 un. + 10 resistores a mais) |
| Área na placa | mínima | 2 × SO-16 (10 × 4 mm cada) + 10 resistores: pesa em 72 × 22 mm |
| Brilho | multiplexado 1/5: pico 5 × a média; Vf do branco ≈ 2,7 V a 3,3 V deixa pouca folga | corrente estática por LED, mesma folga de Vf |
| Firmware | varredura periódica (timer/PIO), 5 fases | PIO/SPI, estático |
| Fantasma | possível se a varredura atrasar; **dois vizinhos acesos = fases diferentes**, sem problema | nenhum |

**Conclusão (E1; a E3 confirma):** **charlieplex**, pela área e por zero CI; o 74HC595 é viável (Basic, mesmo encapsulamento de todo o resto) e fica como plano B se o brilho do charlieplex a 3,3 V não servir. Ambos ficam sem folga de tensão para o branco: a Fase 2 mede.

### E1.8 Conferência código LCSC × encapsulamento × footprint pretendido

| Ref | Código | Pacote da loja | Footprint pretendido | Estado |
|---|---|---|---|---|
| MK1, MK2 | C36405960 / C5119248 | LLGA-5 / SMD-5P (4 × 3 × 1,2) | footprint próprio da ficha (pads da Fig. 13) | **conferido contra a ficha**; checar o EasyEDA por `cpl_jlc.py` na E4 |
| U1 | C2040 | LQFN-56 (7×7) | QFN-56 7×7, passo 0,4, EP 3,2 | a conferir (E3); C2961140 diz "QFN-56-EP" mas tem estoque 0 |
| U2 | C2456211 | SOIC-8 | SOIC-8 3,9 mm (150 mil) | **SNIQ = 150 mil** (ficha) |
| Y1 | C9002 | SMD3225-4P | cristal 3,2 × 2,5 | ok |
| U3 | C5446 | SOT-23 (3 pinos) | SOT-23, **1 = GND, 2 = OUT, 3 = IN** | **pinagem conferida na ficha** |
| J1 | C53432944 | SMD (clamp) | footprint próprio do desenho | **conferido contra o desenho; placa 0,8 mm** |
| SW1-2 | C318884 | SMD-4P 5,1 × 5,1 | 5,1 × 5,1, 4 pinos | ok |
| LEDs | C2290 / C2297 / C2296 / C84256 / C72691 | 0603 / 0805 / 0805 / 0805 / 1206 | idem | **conferido** (anotado na loja) |
| Passivos | C25104, C11702, C25744, C25905, C25092, C25100 (0402); C1525, C52923, C1555 (0402); C19702 (0603) | 0402 / 0603 | idem | **conferido**; ATENÇÃO: valores dos códigos "0402WGF…" são lidos como 3 dígitos + multiplicador (C25092 = 22 Ω, **não** 220 Ω; C25104 = 330 Ω) |
| (opc.) U4 ESD | C2687116 USBLC6-2SC6 | SOT-23-6 | SOT-23-6 | ok |
| (opc.) U5 ULN2003A | C7512 | SOIC-16 | SOIC-16 3,9 mm | ok |

---

## E2 — Custo por placa, montagem Economic

Convenção de custo (conta, `minimic/pcb/custo_e2.py`, preços por faixa da loja a 28 nov, pedido total = qtd por placa × N):
**Extended = US$ 3,09 por tipo por pedido** (cotação de 18 nov da Student V3, repetida), **preparação Economic 8,24**, **estêncil 1,55** (idem); SMT/nitrogênio **3,20** (cotação de 18 nov) ou ≈ 0,0017 US$/junta × 290 juntas × N (**estimativa**, valor lembrado, não conferido).
PCB 72 × 22 mm, 2 camadas, preta fosca, ENIG: **sem cotação**; a JLCPCB cobra "≈ US$ 20 por m²" de ENIG (busca, página de ajuda, data incerta), o que é pouco em 15,8 cm²; o resto (placa, engenharia) vem da cotação, **não feita**. **Estimativa: US$ 10-40 total a 10 un.; US$ 40-120 a 100 un.**

### BOM por placa (VV01, plugue MBB008, charlieplex, medidor direto nos GPIOs)

| Ref | Peça | LCSC | Qtd | Classe |
|---|---|---|---|---|
| MK1-2 | IM72D128VV01 | C36405960 | 2 | **Ext** |
| U1 | RP2040 | C2040 | 1 | **Ext** |
| U2 | W25Q16JVSNIQ | C2456211 | 1 | **Ext** |
| J1 | plugue JXTCONN MBB008 | C53432944 | 1 | **Ext** |
| D27 | LED 1206 azul (SAT) | C72691 | 1 | **Ext** |
| R-usb | 0402 27 Ω (D+, D−) | C25100 | 2 | **Ext** |
| Y1 | 12 MHz | C9002 | 1 | Basic |
| U3 | XC6206 3,3 V | C5446 | 1 | Basic |
| SW1-2 | tátil TS-1187A | C318884 | 2 | Basic |
| D1-15 | LED 0603 branco | C2290 | 15 | Basic |
| D16-21 | LED 0805 verde | C2297 | 6 | Basic |
| D22-24 | LED 0805 amarelo | C2296 | 3 | Basic |
| D25-26 | LED 0805 vermelho | C84256 | 2 | Basic |
| R | 330 Ω ×12, 1 kΩ ×6, 10 kΩ ×2, 5,1 kΩ ×1, 22 Ω ×1 (0402) | C25104, C11702, C25744, C25905, C25092 | 22 | Basic |
| C | 100 nF ×12, 1 µF ×4 (0402); 10 µF ×3 (0603); 22 pF ×2 (0402) | C1525, C52923, C19702, C1555 | 21 | Basic |

**6 tipos Extended** (IM72D128, RP2040, flash, plugue, LED azul, 27 Ω) e **16 tipos Basic**; 79 peças por placa (conta). A tabela completa com preço de cada linha está em `minimic/pcb/build/custo_e2.md` (regerável).

### Custo (conta, US$)

| | **10 placas** | **100 placas** |
|---|---|---|
| Peças por placa (loja, VV01 a preço de tabela) | **6,59** | **5,88** |
| Tipos Extended × 3,09 | 18,54 | 18,54 |
| Preparação 8,24 + estêncil 1,55 | 9,79 | 9,79 |
| SMT (3,20 fixo, ou por junta) | 3,20-4,85 | 3,20-49,3 |
| **Taxas do pedido** | 31,5-33,2 | 31,5-77,6 |
| **Taxas por placa** | 3,15-3,33 | 0,32-0,78 |
| **Montada sem PCB, por placa** | **9,74-9,92** | **6,20-6,66** |
| PCB por placa (estimativa) | 1,0-4,0 | 0,4-1,2 |
| **Total por placa (estimativa)** | **≈ 10,7-13,9** | **≈ 6,6-7,9** |

Alvo da SPEC (§13 R2MIC): **≤ US$ 10 por placa montada em lote de 100** → **atendido com folga (≈ 6,6-7,9)**; a 10 placas o alvo não é atendido (≈ 10,7-13,9) por causa das taxas fixas. O valor mais incerto é a PCB (ENIG + preta fosca) e o SMT por junta: **cotar no portal antes da Fase 2**.

### Variações (diferença por placa, conta)

| Opção | 10 un. | 100 un. |
|---|---|---|
| **V01 no lugar da VV01** (estoque na JLCPCB hoje; só 20 Hz) | **+1,85** | **+0,77** |
| Plugue MAB169 (16 P) no lugar do MBB008 | −0,06 | −0,09 |
| ESD USBLC6-2SC6 a mais (1 tipo Extended) | +0,36 | +0,07 |
| Flash Basic W25Q128JVSIQ no lugar da W25Q16 (−1 tipo Extended) | +0,59 | +0,72 |
| LDO TLV75533 (Extended) | +0,30 | +0,02 |
| ULN2003A (Basic) + 7 resistores a mais (não está na tabela do script; estimativa) | ≈ +0,17 | ≈ +0,12 |

### Basic × Extended: onde cada Extended vem de

IM72D128, RP2040, flash QSPI, plugue e LED azul **não têm equivalente Basic** (busquei flash Basic: só a 128 Mbit/208 mil, mais cara; azul: nenhum; plugue: nenhum; microfone: único). O **27 Ω** é Extended em 0402 e 0603; com 22 Ω (Basic C25092) cairia um tipo (US$ 3,09 por pedido), mas a Raspberry Pi pede 27 Ω nas linhas USB e **não conferi** que 22 Ω basta (risco baixo; E3 decide).

### Estoque (risco por peça, ≤ 100 placas)

| Peça | Estoque na JLCPCB | Cobre | Risco |
|---|---|---|---|
| **IM72D128VV01** | **0** | **0 placas** | **ALTO** |
| IM72D128V01 | 4 837 | 2 418 placas | baixo |
| Plugue MBB008 | 245 | 245 placas | **médio** (≤ 245 placas por lote) |
| Plugue MAB169 | 155 | 155 placas | médio |
| LED azul KT-1206B | 1 102 | 1 102 placas | baixo |
| RP2040, flash, LDO, tudo mais | ≥ 20 000 | — | baixo |

---

## Riscos, em ordem

1. **Estoque do IM72D128VV01 = 0** (JLCPCB e LCSC). Sem ele a meta de graves (≤ 15 Hz) não fecha; com a V01 (estoque 4 837) tudo fecha menos esse número. Sem as duas, não há placa.
2. **Plugue em linha só para placa de 0,8 mm**, e com terminais nas duas faces (montagem Economic cobre uma). A SPEC pede 1,2 mm.
3. **Brilho dos LEDs a 3,3 V** (verde, branco, azul): variação grande; resolver com 5 V (ULN2003A) ou aceitar a variação e medir.
4. **Cristal de ESR 80 Ω** (loja) contra o que o RP2040 pede: conferir antes de fechar o esquema.
5. **DC do canal R** a −40 dBFS e clock PDM não exato (itens do firmware, abaixo).
6. **Calor do LDO** (0,19 W de 250 mW) no pior pior caso; some se os 7 LEDs saírem do 3,3 V.
7. Número de **juntas/SMT** e o preço da PCB (ENIG, preta fosca) são estimativas: cotar.

## Pedidos ao firmware (para o relatório da integração; não editei nada do firmware)

1. **Clock PDM:** 3,072 MHz exatos não saem de um cristal de 12 MHz (a conta de PLL do RP2040 não tem solução inteira: 122,88 e 147,456 MHz). Opção: **PDM a 2,4 MHz com sysclk de 120 MHz (÷ 50)** → 48 kHz exatos, no intervalo "alto desempenho" 2,0-2,6 MHz, **−1 dB de SNR** (ficha: VV01 70,5 contra 71,5 dB(A)), −1,5 mA no RP2040 e −40 µA por microfone. A 3,0 MHz (sysclk 144 MHz) dá OSR 62,5: não inteiro.
2. **DC offset:** L = −80 dBFS, R = −40 dBFS (ficha). O bloqueio de DC de 3 Hz (τ ≈ 53 ms) leva ≈ 0,4 s para assentar; o medidor não deve acender o LED de −42 dBFS nesse intervalo (a varredura de partida cobre).
3. **Partida do microfone:** 20 ms (±0,5 dB) a 50 ms (±0,2 dB) depois do VDD e do clock; o tom ocioso dura 3 ms. Não mostrar medida antes de 50 ms.
4. **Resolução de ganho:** 1,5 dB por toque sobre 24 bits não pede nada de hardware.

## Perguntas para o design

Respostas necessárias antes da E3 (esquema) e da E4 (posicionamento).

1. **Espessura da placa: 0,8 mm ou 1,2 mm?** Os machos USB-C em linha com a placa que a JLCPCB monta (MBB008 e MAB169) pedem **0,80 ± 0,05 mm**. Em 1,2 mm só existe plugue vertical (eixo perpendicular). O estudo de alavanca precisa dizer se uma placa de 72 × 22 × 0,8 mm segura 6-8 g a 36 mm do plugue sem flexionar demais (R3MIC §1, D1).
2. **Entalhe e contorno do plugue na borda de 72 mm:** MBB008 pede entalhe de **6,25 mm × 0,65 mm** centrado no plugue (desenho do fabricante); o plugue tem 8,25 mm de largura e **10,25 mm de comprimento** além da borda. Confirmar com o contorno do `pcb_envelope.json`.
3. **LEDs a 5 V com ULN2003A?** Para o brilho do verde (6) e do SAT azul (1) não depender da Vf, proponho um **ULN2003A SOIC-16** (≈ 10 × 4 mm) na face da placa, perto do medidor. Cabe na faixa de 22 mm e na ordem das cores? Ou o design prefere LEDs só a 3,3 V e aceita brilho desigual?
4. **Face dos microfones e da espuma:** porta por baixo, furo Ø 0,8 mm, **microfone e todos os componentes na mesma face (Economic)**, espuma Ø 10 na face oposta. Confirmar que a face dos componentes é a de trás ou a da frente do conceito.
5. **Plugue com terminais nas duas faces:** aceitar solda manual dessa metade (Fase 2) ou pagar montagem Standard? Se o J preferir, pergunto à JLCPCB (DFM) na Fase 2.
6. **V01 ou VV01 no primeiro lote?** A meta de 15 Hz só fecha com a VV01, hoje sem estoque; a V01 monta já e custa +US$ 0,77 por placa a 100 un. (conta). Decisão do J.
7. **SAT em 1206:** o KT-1206B (30-70 mcd a 5 mA, Vf 3,1 V) é o único azul 1206 com estoque (1 102). Aceita o 0805 azul (KT-0805B, 100 mcd, estoque 38 816) se o brilho do 1206 não bastar?

Fontes (todas consultadas em 28 nov 2026): datasheets IM72D128V01 (LCSC) e IM72D128VV01 rev. 1.1 (Infineon); RP2040 datasheet (Raspberry Pi); W25Q16JV (Winbond via LCSC); XC6206 (Torex via LCSC); desenhos JXTCONN TYPE-C-MBB008 e MAB169, Hanbo MC-239, BXCONN TYPE-C-24P-GON-LT (LCSC); páginas `jlcpcb.com/partdetail/…`; biblioteca de peças da JLCPCB (API `selectSmtComponentList`); Element14, Future Electronics e Octopart (via busca; Octopart bloqueado). Scripts: `minimic/pcb/consulta_jlc.py`, `minimic/pcb/custo_e2.py`.
