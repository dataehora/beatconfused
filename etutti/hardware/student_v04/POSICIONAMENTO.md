# eTutti Student V4 · portão P (posicionamento), R11V4 · principal com o OLED real e as fixações novas, réguas R8 (sem OUT) e R4

**PARA APROVAÇÃO DO J. NÃO APROVADO.** Nada roteado (0 trilhas, 0 vias, na principal e nas réguas); nada encomendado nem cotado como compra. Data: 22 nov 2026. **A placa principal continua com o portão fechado: o roteamento dela só começa depois do "aprovado" do J.** O das réguas está liberado pela SPEC R11V4 (entrega em `pcb/regua/ROTEAMENTO_ENTREGA.md`).

**Status (23 nov): a principal foi roteada e aceita (DRC 0/0/0, paridade 0) e os arquivos de fábrica estão em `fab/principal/` (Gerbers de 4 camadas, BOM, CPL, folha de cotação); nada encomendado. O portão P continua o que o J aprovou (as mudanças de posição foram internas ao USB e ao codec, nada que o case vê).** **R12V4, 4ª entrega (23 nov):** R605 girado 90° (26,275; 16,5), C305 −1,0 mm em x, C303 e C310 +0,5 mm em y; nada que o case vê mudou. **R12V4, 3ª entrega (23 nov):** C306 +1,5 mm e FB301 +1,2 mm em x, R605 −0,15 mm em x (limite do pátio do J101; o pedido era −1,0), C209 e R216 −0,8 mm em y; nada que o case vê mudou. **R12V4, 2ª entrega (23 nov):** U301 +2,0 mm em x, R105 +1,5 mm em y e o desacoplamento leste do codec (C301, C302, C306, C307, FB301) junto; nada que o case vê mudou. **R12V4 (23 nov 2026):** a principal teve **3 peças reposicionadas** a pedido do roteamento: **U201 girado 90° (rot 180 em x 13,435; y 9,5)** e R201/R202 (+0,5 / −0,25 mm em y); nada que o case vê mudou (conectores, furos, contorno, alturas). O `.kicad_dru` ganhou a área `vsys_estreito` (VSYS ≥ 0,5 mm entre C206, U204 e C210). Ver `pcb/ROTEAMENTO_ENTREGA_PRINCIPAL.md` e `ELETRONICA.md` (R12V4). O portão P da principal fica **como estava para o J** (a mudança é interna ao grupo USB, sem efeito no case); figuras regeneradas.

## R11V4 · o que mudou na planta de posicionamento
1. **Tela OLED real (Adafruit 326)** no lugar do módulo genérico: PCB 29,2 x 26,7 mm (+ orelhas, 31,75 mm), vidro 26,7 x 19,26, área ativa 21,74 x 10,86 **centrada na janela de 24 x 13**, 4 postes da tampa nos furos Ø2,5 do módulo (24,13 x 26,67 mm, conferir). **J401 passou a um SH de 4 vias, ordem Qwiic**, para o cabo Qwiic de estoque. A **fenda do cabo** ficou em x 44,45..51,45; y 18,17..20,67 (a principal foi reposicionada por script; DRC sem trilhas **0 erros, 1 aviso `isolated_copper` esperado, 242 faltando, paridade 0; ERC 0/0**). Nenhuma outra peça da principal mudou de lugar.
2. **Fixações (design):** réguas por **parafuso M2 passante com porca embaixo** (2 por régua, **8 no total**; fileiras 1 e 3 em u 18,5 + 129,5, fileiras 2 e 4 em u 37 + 129,5); postes da tampa, bossas de parede, H1..H4 e OLED com parafuso formador de rosca direto no plástico (detalhes e justificativa em `FIT_CHECK.md`, R11V4, do design). **Na régua** isso pediu **área sem cobre no topo, 4,6 mm em cada furo M2** (cabeça do parafuso de 3,8 mm sobre o topo da régua): já aplicada.
3b. **Reposicionamento da R8 (pedido do roteamento, 22 nov):** a R8 roteada não fechou o GND dos capacitores (bolsões entre o tronco de +3V3 e os sinais). Aplicado o menor ajuste, **só na R8**: (1) **74HC595 (U9) de u 27,75 / v +4,2 para u 74,0 / v 0 (rot 90, meio da régua, entre as células 4 e 5, |v| ≤ 1,9: sem corte de trilho da frente)**; o maior EN cai de ~111 para ~65 mm; (2) **C1..C8 passam para a linha central, ao lado direito de cada sensor (u + 1,75, v 0, rot 270): pad +3V3 ao fundo-trás (v −0,48) e pad GND à frente (v +0,48)**, entre o pino 1 (+3V3) e o pino 2 (GND) do TMAG, pernas de ~1 mm, sem bolsão de GND do lado errado; C9 (do 595) em u 78,2 / v +1,75. Não mudaram: furos, J1, J2, R1, sensores, terminações (idênticas à R4). ERC 0/0, DRC sem trilhas 0 erros e 0 avisos, 80 faltando, paridade 0. **A R4 NÃO recebe o ajuste:** já foi aceita roteada (DRC 0/0/0), BOM e terminações são as mesmas (as posições internas de 595 e capacitores não são terminação) e o recorte de trilho do design em u 25,5..32 continua valendo para ela. 
3. **Réguas:** o instrumento de 32 teclas usa **4 x R8 sem OUT e sem o resistor da cascata** (R8 e R8E são a mesma placa; só a BOM muda). R4 sem mudança de placa.

**Confirmado em 23 nov:** o portão P da principal continua válido (nada mudou na principal desde a R11V4; a R8 foi reposicionada, 595 em u 74, e o design já aplicou isso no modelo). As figuras do design `*_r11` estão incorporadas na tabela abaixo (planta geral, interface, corte da interface, e os isométricos da base `iso_base_r11_*.png` / `iso_base_r11.pdf`, `corte_base_r11.png`).

## Figuras (abra estas para decidir)
| Nº | Figura | Arquivo |
|---:|---|---|
| 1 | **Instrumento de 32 teclas, planta final do posicionamento** (principal + 4 x R8 sem OUT; nome de cada nota, C azul, F laranja; cabeçalhos IN, M2 e postes; cabos de 45,8 e 50,8 mm) | `pcb/img/portao_p_r11_instrumento.png` |
| 2 | **Planta geral oficial do design** (modelo real, OLED Adafruit 326, 4 x R8, nome das notas, C e F em xadrez) | `case/renders/planta_geral_v4_r11.png` |
| 3 | **Interface: planta com o OLED real** (placa, vidro, área ativa, janela, postes, fenda e cabo) | `case/renders/planta_interface_v4_r11.png` |
| 4 | Corte da interface (OLED, tampa, placa) | `case/renders/corte_interface_v4_r11.png` |
| 5 | Principal, topo e fundo, blocos, conectores e cotas | `pcb/img/principal_blocos_topo.png`, `principal_blocos_fundo.png` |
| 6 | **Régua R8** (planta com as notas A3 C4 D#4 F#4 A4 C5 D#5 F#5, C azul e F laranja; conectores, furos; J2 só nas E) e cortes | `pcb/regua/img/regua8_planta.png`, `regua8_corte.png` |
| 7 | R4 (planta e cortes) | `pcb/regua/img/regua_planta.png`, `regua_corte.png` |
| 8 | Painéis: R4 de 5, R8 de 2 e de 4 tiras, mesma escala contra 100 x 100 mm | `pcb/regua/img/regua8_painel.png` |
| 9 | Painéis em KiCad (fundo) | `pcb/regua/img/regua_R8_painel_de_2_fundo.png`, `regua_R8_painel_de_4_fundo.png`, `regua_R4_painel_de_5_fundo.png` |
| 10 | Base e isométricos (do design) | `case/renders/corte_base_r11.png`, `iso_base_r11_frente_esq.png`, `iso_base_r11_tras_dir.png`, `iso_base_r11_topo.png`, `iso_base_r11_ocultas.png`, `iso_base_r11.pdf` |

## Para o J decidir
1. Aprovar a **principal** (75,05 x 95,1 mm, 4 camadas, 1,2 mm, 78 peças JLC no fundo + 2 encoders no topo) com o OLED Adafruit 326 e o J401 de 4 vias (+1 tipo Extended, US$ 3,09 por pedido; módulo ~US$ 17,5 contra ~US$ 3 de um genérico).
2. Aprovar a **R8** (uma por fileira, sem OUT) e a **R4** (extensões), com as quatro variantes por BOM.
3. Painel de 2 tiras (44 mm) ou de 4 (76 mm)?

---

# (anexo) portão P da R10V4, referência

# eTutti Student V4 · portão P (posicionamento), R10V4 · principal, régua R8 e régua R4

**PARA APROVAÇÃO DO J. NÃO APROVADO.** Nada roteado (0 trilhas, 0 vias, na principal e nas réguas); nada encomendado nem cotado como compra (regra do J: nada é comprado até o protótipo inteiro estar fechado). Data: 22 nov 2026. **O roteamento só começa depois do "aprovado" do J nesta planta** (agente `roteamento`; ele nunca move peça: pedido de mudança volta para a eletrônica). Só 32 teclas, só a Student V4.

## 0. Para o J decidir

Aprovar (ou pedir mudança em) estas três peças:
1. **Placa principal:** 75,05 x 95,1 mm, 4 camadas, 1,2 mm, 78 peças JLC no fundo + 2 encoders no topo (figuras 1 e 2).
2. **Régua R8 (a do instrumento de 32 teclas):** 147,6 x 14 x 1,2 mm, 2 camadas, 8 sensores + 1 registrador + 2 conectores SH no fundo (figura 3). **4 x R8**, uma por fileira.
3. **Régua R4 (só para os instrumentos de 48 e 80 teclas, sempre na ponta do agudo):** 73,6 x 14 mm, a de sempre (figura 3c).
E, para o conjunto, a planta do instrumento de 32 teclas (figuras 4 e 5), que é só conferência de encaixe.

### O que mudou desde a R8V4 (lista curta)
- **Régua R8 nova** (8 posições, um 74HC595 usando os 8 estágios, terminações **idênticas** às da R4: IN em u 5,9, OUT a 26,5 mm da ponta direita, P6s, 330 ohm, altura, boca para −y). **8 x R4 viram 4 x R8:** 4 cabos em vez de 8, sem junção régua–régua, 8 M2 em vez de 11 (dois por régua), 8 plugues em vez de 16.
- **Furos de fixação (contrato fechado pelo design):** a R8 tem 4 M2 (u 18,5 / 37 / 111 / 129,5, v +5,2); cada fileira usa um par (contrato do design). A R4 não mudou (3 furos).
- **Varredura:** coluna = estágio, 9 pulsos de acesso aleatório com 32 teclas (eram 17), passada em ordem de 8 pulsos; 0,56 ms (igual). `pcb/PINOS.md` atualizado.
- **Microfone:** eletreto (plug-in) e dinâmico só pelo J302; **C310 (100 nF no MIC_BIAS) passa a "não montar"** (cortava o agudo com R305 = 0 ohm); o ME 3 e o boost de 9-10 V saíram. A principal tem 78 peças montadas (era 79); nenhuma peça mudou de lugar.
- Nada mais mudou na principal: mesmos pinos do Teensy, mesmos blocos.

## 1. Figuras (abra estas para decidir)

| Nº | Figura | Arquivo |
|---:|---|---|
| 1 | Principal, topo, blocos coloridos, furos e cotas | `pcb/img/principal_blocos_topo.png` |
| 2 | Principal, fundo (visto de baixo), blocos, conectores e cotas | `pcb/img/principal_blocos_fundo.png` |
| 3 | **Régua R8**, planta com todas as peças, conectores, furos, nome das notas (A3 C4 D#4 F#4 A4 C5 D#5 F#5; C azul, F laranja) | `pcb/regua/img/regua8_planta.png` |
| 3b | R8, cortes (através das 4 fileiras e ao longo) | `pcb/regua/img/regua8_corte.png` |
| 3c | R4 (sem mudança): planta e cortes | `pcb/regua/img/regua_planta.png`, `regua_corte.png` |
| 3d | Painéis: R4 de 5 tiras, R8 de 2 e de 4 tiras, mesma escala, contra os 100 x 100 mm | `pcb/regua/img/regua8_painel.png` |
| 4 | **Instrumento de 32 teclas, planta final de posicionamento** (4 x R8; nome de cada nota; C azul, F laranja; cabeçalhos, M2, postes, cabos de 45,8 e 50,8 mm) | `pcb/img/portao_p_r10_instrumento.png` |
| 5 | **Planta geral oficial** do design (modelo real, 4 x R8, nome das notas), zoom da interface e corte lateral | `case/renders/planta_geral_v4_r10.png`, `planta_interface_v4_r10.png`, `corte_interface_v4_r10.png` |
| 5b | Base robusta e isométrico da base (do design) | `case/renders/iso_base_r10.png`, `iso_base_r10_detalhe.png`, `corte_base_r10.png` |
| 6 | Corredores e ratsnest da principal | `pcb/img/topo.png`, `fundo.png`, `ratsnest.png` |

Reproduz (raiz do repositório): `python pcb/schematic.py` → KiCad python `pcb/posiciona_v4.py` → venv CadQuery `pcb/vistas_v4.py`, `pcb/blocos_v4.py`, `pcb/portao_p_r10.py` → `python bom_v4.py`; réguas: `[REGUA_N=8] python pcb/regua/schematic_regua.py` → KiCad python `[REGUA_N=8] pcb/regua/posiciona_regua.py` → venv `[REGUA_N=8] pcb/regua/vistas_regua.py`, `pcb/regua/painel_r8.py`; custo `pcb/regua/custo_r10.py`; microfone `pcb/mic_ganho.py`. DRC: `kicad-cli pcb drc --schematic-parity --severity-all`.

---

# PARTE 1 · placa principal

## 2. A placa
- **75,05 x 95,1 mm** (x 2,45..77,5; y 2,45..97,55), cantos R 3, 4 camadas, 1,2 mm; In2 = GND inteira, In1 = +3V3. Só interface (sem tecla, sensor nem multiplexador). **83 peças no esquema; 78 montadas pela JLCPCB, todas no fundo** (C310 não montado: pad e posição mantidos); em casa: 2 encoders (topo), alto-falante e ponto de teste.
- **Furos M2** (placa → tampa, via postes): H1 (62; 48), H2 (74; 93), H3 (6,5; 48,5), H4 (8; 91,5); módulo: H101 (42; 14), Ø2,7 (parafuso M2,5 + espaçador).
- **DRC sem trilhas (com paridade): 0 erros**, paridade esquema × placa **0**, 242 ligações faltando (esperado), **1 aviso `isolated_copper`** do plano +3V3 sem vias (esperado sem trilhas; some quando o roteador ligar o plano). **ERC 0/0.**

## 3. Blocos e conectores (figuras 1 e 2)

| Bloco | Onde (x; y em mm, y para o jogador) | Notas |
|---|---|---|
| **USB** (J201, ESD, TVS, 2 x 5,1 k) | parede esquerda, pads em **y 10,0** | par D+/D− em B.Cu sem via; 6,75 mm do USB-C ao M.2, par de 7,07 mm |
| **MicroMod** (M.2 J101 + H101) | J101 (22; 18); cartão 22 x 22 em x 24,7..44, y 7..29; H101 (42; 14) | peças sob o cartão ≤ 1,9 mm |
| **Energia** (carregador, conversor, indutor, J202) | canto de trás à direita (x 50..77, y 3..32) | o bloco mais denso (risco de roteamento) |
| **Áudio** (codec U301, OUT J301 y 36, IN J302 y 60, R305 0 ohm, R306/C311; **C310 não montado**) | esquerda (x 2..26, y 28..65) | HP_VGND nunca no GND; microfone eletreto ou dinâmico só pelo J302 |
| **Interface** (2 encoders no topo, tela J401, Program) | encoders (20,5; 42) e (38,5; 42); J401 (48,95; 29,5); fenda do cabo 45,45..52,45 x 18,17..20,67 | knobs Ø15 |
| **Amplificador** | U501 (54; 88), pads (48,1; 94,5) | alto-falante e caixa são do design |
| **Fileiras** J601..J604 (SH 6 vias, P6s, bocas para +x) | borda direita, boca em **x 77,4**, em **y 74,03 / 58,01 / 41,99 / 25,97** (fileiras 1..4) | **cabo `A06SR06SR30K51B` até o IN da R8 da fileira (4 cabos)**; R605/R606 330 ohm junto do J101 |

Pinagem de J601..J604 (P6s): 1 +3V3, 2 GND, 3 OUT_Rk, 4 GND, 5 SCAN_CLK, 6 SCAN_DATA; pull-down de 100 k por OUT_Rk (R601..R604). Corredores reservados (regras no `.kicad_dru`) e ratsnest como na R8V4 (61 redes, 26 mm/cm²; mais carregada: energia e o entorno do J101).

## 4. BOM da principal e custo
78 peças, **31 linhas, 13 tipos Extended**, **US$ 17,87 de peças por placa** (`bom_v4.csv`; o C310 saiu sem mudar o custo: 0,0025 de peça). Extended: J101 (M.2), USB-C, S3B-PH (bateria), PJ-327A, SH-6 (clone), indutor, ESD, TVS, SGTL5000, BQ24074, TPS63001, MAX98357A, XC6206.

---

# PARTE 2 · régua R8 (figuras 3, 3b, 3d)

## 5. A R8 (`kicad/regua/student_v04_regua8.kicad_pcb`)
- **147,6 x 14,0 x 1,2 mm** (148 nominais menos 0,2 de folga em cada ponta), 2 camadas, cobre 1 oz. **22 peças, todas no fundo; nada no topo** (a tecla assenta ali). Quadro: u ao longo da fileira, v através (+v = jogador).
- **ERC 0/0; DRC sem trilhas: 0 erros, 0 avisos; paridade 0;** 80 ligações faltando (esperado).

| Ref | Peça | u; v (mm) | Altura |
|---|---|---|---|
| U1..U8 | TMAG5253BA3 (X2SON-4), um por tecla | u = 9,25 + 18,5 k; v 0 | 0,4 |
| **J1 ENTRADA** | SH-6 lateral, boca para trás (−v) | **u 5,9**; v −3,95 | 2,95 (+ plugue 3,6) |
| **J2 SAÍDA** | idem | **u 121,5** (26,5 mm da ponta direita nominal, como na R4); v −3,95 | 2,95 (+ 3,6) |
| U9 | 74HC595 DHVQFN-16 2,5 x 3,5, **8 estágios usados** (QA..QH = EN1..EN8) | u 27,75; v +4,2 (**o mesmo lugar da R4**) | 1,0 |
| C1..C8 | 100 nF, um por sensor | junto do VCC de cada TMAG; C7 em u 122,0; v −0,47 (fora da pegada do J2) | 0,55 |
| C9, C10 | 100 nF do 595; 10 µF | junto de U9; u 1,5 | 0,55 / 1,45 |
| R1 | 330 ohm do QH' | u 127,0; v −2,45 (ao lado do J2) | 0,55 |

- **Terminações R4 = R8** (conferido por script nos dois `posicao_regua*.json`): J1 na mesma posição, J2 a 26,5 mm da ponta direita nominal, pinagem P6s pad a pad idêntica, altura 2,95 mm, boca −v, R1 a (+5,5; +1,5) do J2, 595 e C do 595 no mesmo lugar. R8 → R4 ou R8 → R8 usam o mesmo cabo (OUT → IN seguinte: 32,4 mm).
- **Furos:** 16 de pino da tecla Ø1,70 (±5,08 do centro de cada célula); **M2 Ø2,2 (inserto), patamar sem peças Ø6,4 embaixo, em u 18,5 / 37 / 111 / 129,5, v +5,2** (contrato do design: um par por fileira, fileiras 1 e 3 = 18,5 + 129,5, 2 e 4 = 37 + 111); entalhes de 2,0 x 4,3 mm na borda de trás em múltiplos de 18,5. (R4 sem mudança: 3 M2 em u 18,5 / 37 / 55,5, fileiras com R4 usam 2 ou 1.)
- Roteabilidade: 15 redes, ~2 100 mm² (EN1..EN8 individuais, OUT, CLK, SER, QHP, +3V3, GND); o topo (F.Cu) está livre.
- **Painel (figura 3d):** a R8 não cabe em 100 x 100 mm. **Recomendado: 2 tiras, 161,6 x 44 mm (71 cm²), abas e microfuros; 2 painéis montados = 4 R8.** Alternativa: 4 tiras de 161,6 x 76 mm (lado menor ≥ 70 mm; 8 R8). Gerbers do painel da R8 não gerados (nada será pedido agora). A R4 mantém o painel de 5 (87,6 x 92 mm).

## 6. BOM da R8 e custo (32 teclas, estimativas; nada cotado)
R8: 22 peças, **3 tipos Extended** (TMAG5253 C22401868, SH-6 C56123098, 74HC595BQ C730243) e 3 Basic; ~US$ 4,3-5,5 de peças por régua; 4 montadas ≈ US$ 17-22 + 9,27 de taxa de Extended (a mesma da R4).
**Instrumento de 32 teclas (F2, pedido mínimo, sem frete):** a conta da R8V4 era **~US$ 301-376** (8 x R4, 8 cabos); com **4 x R8**: cabos 4 (−US$ 4,8-5,7), peças −US$ 6, PCB das réguas ±, soma variável **−US$ 9 a −11 sem reserva** (−3 a +2 com 2 R8 de reserva) ⇒ **~US$ 290-367** nas réguas e cabos, **+ ~US$ 4,2 do case** (do design: **~US$ 48,5** contra 44,3, por causa da base robusta com riser cheio, +15 cm³) ⇒ **~US$ 294-371**. 0 juntas de solda, 0 tipos Extended novos; montagem em casa ~8 min menor (palpite). O preço do PCB acima de 100 x 100 mm é o ponto não cotado.

## 7. R4 (figura 3c)
Continua como estava (14 peças, 3 Extended, 73,6 x 14 mm, OUT em u 47,5, 3 M2). Só entra nos instrumentos de 48 e 80 teclas, sempre na ponta do agudo (coluna = estágio, estágios mortos só no fim da cadeia). Não detalhada além disso.

---

# PARTE 3 · instrumento e riscos

## 8. Planta do instrumento (figuras 4 e 5) e furos do design
- **Case 244 x 102 mm, de y −2 a y 100.** Quatro fileiras de 8 teclas, **uma R8 por fileira** (x 79,95 nas fileiras 2 e 4, 89,2 nas 1 e 3 — nomes de nota: fileira 1 A3..F#5; 2 G3..E5; 3 G#3..F5; 4 F#3..D#5). Cabeçalho IN no fundo de cada régua com o cabo de 45,8 mm (cheio) ou 50,8 mm (tracejado) da placa; **o OUT fica sem cabo** (terminação modular). As figuras 4 (minha) e 5 (do design, modelo real) mostram a mesma coisa; vale a 5 em caso de diferença.
- **Furos que a eletrônica fixa:** M2/H da placa e H101 (seção 2); régua: 16 pinos Ø1,70 e 4 M2 Ø2,2 (seção 5, contrato do design). Postes, base robusta, isométrico e OLED: do design (`FIT_CHECK.md`, figuras 5 e 5b).

## 9. Riscos aceitos (só a peça real fecha; nada é comprado antes do protótipo)
1. **Cabo `A06SR06SR30K51B`:** reto de verdade? 45,8 ou 50,8 mm de fio livre? fios soltos ou fita colada (a colada não fecha)? Cabo invertido não queima nada, mas a varredura não funciona. Agora são **4 cabos**, não 8.
2. **Clone SH C56123098:** medidas e acoplamento com o plugue JST sem desenho do fabricante; 2,95 + 3,6 mm sob a régua.
3. **330 ohm** no CLK a 5 MHz: sobra margem; firmware pode descer a 2,5 MHz (9 pulsos = 3,6 us).
4. **Microfone:** limiares do MIC_DET, ruído do pré-amplificador do codec (3 uV é suposição) e do MIC_BIAS sem o C310 são cálculo; o dinâmico de ≥ 700 ohm e o eletreto de ≥ 1 mA se tocam em MIC_DET (menu "Tipo mic"). Sem boost, sem peça nova.
5. **JLCPCB:** o painel da R8 passa de 100 x 100 mm (preço por área não cotado) e o de 2 tiras tem 44 mm de lado (< 70 mm: a JLCPCB pode acrescentar trilho ou recusar; saída: painel de 4 tiras); aceitação de painel do cliente com abas e microfuros; pads do DHVQFN-16 (C730243) contra o EasyEDA no `cpl_jlc.py`.
6. **Roteabilidade:** bloco de energia e pads 3/5 do M.2 apertados; 242 ligações faltando na principal e 80 na R8 (1 aviso `isolated_copper` até o roteamento).
7. **Do design (`FIT_CHECK.md` R10V4):** folga vertical do plugue à régua de trás de **1,7 mm** (fileiras 1 e 2; 2,7 mm na 3): pinça fina ou plugar antes de descer a régua de trás; inserto M2 em PA12 MJF (parede de 1,4 mm). O 595 da R8 está em |v| ≤ 3,9 com recorte do trilho da frente (mesma posição da R4).

## 10. Perguntas do portão
1. Aprova a principal, a **R8** (e a R4 como peça modular) e a planta de 32 teclas?
2. Com ou sem **2 R8 de reserva** (3 painéis montados, US$ ~9-11 de peças a mais; as sobras servem de início de um instrumento de 64 teclas)?
3. Aceita o risco do painel de 44 mm de lado (saída: 4 tiras)?

**Depois do "aprovado" do J:** `roteamento` (principal e R8; a R4 só se for usada), depois `cpl_jlc.py`/BOM/CPL de fábrica e Gerbers finais.
