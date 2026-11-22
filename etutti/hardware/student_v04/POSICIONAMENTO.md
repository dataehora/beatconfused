# eTutti Student V4 · portão P (posicionamento), R8V4 · partes 1 (placa principal) e 2 (régua)

**PARA APROVAÇÃO DO J. NÃO APROVADO.** Nada roteado (0 trilhas, 0 vias, na principal e na régua); nada encomendado (regra do J: nada é comprado até o protótipo inteiro estar fechado). Data: 22 nov 2026. **O roteamento só começa depois do "aprovado" do J nesta planta** (agente `roteamento`; ele nunca move peça: pedido de mudança volta para a eletrônica). Só 32 teclas, só a Student V4.

## 0. Para o J decidir

Aprovar (ou pedir mudança em) estas duas peças:
1. **Placa principal:** 75,05 x 95,1 mm, 4 camadas, 1,2 mm, 79 peças JLC no fundo + 2 encoders no topo (figuras 1 e 2 abaixo).
2. **Régua universal:** 73,6 x 14 x 1,2 mm, 2 camadas, 4 sensores + registrador + 2 conectores SH no fundo (figura 3). Painel de 5.

E, para o conjunto, a planta do instrumento de 32 teclas (figura 4), que é só conferência de encaixe.

### O que mudou desde a R7V4 (lista curta)
- **OUT da régua em u 47,5** (era 68,1); IN continua em u 5,9; C3 fora da pegada do OUT; **saíram os pads de solda LK1/LK2** (ligação H = cabo de estoque, sem solda).
- **Pinagem P6s** nos dois conectores da régua e em J601-J604: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO.
- **330 ohm** em R605/R606 (principal) e em R1 (QH' na régua); **R305 = 0 ohm** (bias do microfone de 2 kohm no total).
- Case (do design, fechado): **244 x 102 mm, de y −2 a y 100** (parede de trás 2 mm mais para trás; placa, teclas e interface mantêm seus y), postes de parede x 102,5 / 176,6 / 234 em y 5 e 93, 5 postes internos, 11 M2 e rebaixos por junção (seção 7).
- **Nada mudou de lugar na principal**; os pinos do Teensy são os mesmos.

## 1. Figuras (abra estas para decidir)

| Nº | Figura | Arquivo |
|---:|---|---|
| 1 | Principal, topo, blocos coloridos, furos e cotas | `pcb/img/principal_blocos_topo.png` |
| 2 | Principal, fundo (visto de baixo), blocos, conectores e cotas | `pcb/img/principal_blocos_fundo.png` |
| 3 | Régua, planta com todas as peças, conectores, furos, nome das notas | `pcb/regua/img/regua_planta.png` |
| 3b | Régua, cortes (através das 4 fileiras e ao longo) | `pcb/regua/img/regua_corte.png` |
| 4 | **Instrumento de 32 teclas, planta final de posicionamento** (nome de cada nota; C azul, F laranja; réguas, cabeçalhos, M2, postes, cabos de 45,8 e 50,8 mm) | `pcb/img/portao_p_instrumento.png` |
| 5 | **Planta geral oficial** do design (modelo real, R8V4, 32 teclas, nome das notas), zoom da interface e corte lateral | `case/renders/planta_geral_v4_r8.png`, `case/renders/planta_interface_v4_r8.png`, `case/renders/corte_interface_v4_r8.png` |
| 5b | Ligação H: cortes do rebaixo por fileira (fio de 45,8 e de 50,8 mm) e montagem em casa | `case/renders/ligacao_h_cortes_r8.png`, `ligacao_h_cortes_r8_50.png`, `ligacao_h_montagem_r8.png` |
| 6 | Corredores e ratsnest da principal | `pcb/img/topo.png`, `fundo.png`, `ratsnest.png` |
| 7 | Painel de réguas (sem rota) e painel da grade-régua | `pcb/regua/img/regua_painel_fundo.png`, `grade_regua_painel_topo.png` |
| 8 | Pinagem P6s contra os dois tipos de cabo (R7V4) | `pcb/regua/img/h_pinagem_r7.png` |

Reproduz (raiz do repositório): `python pcb/schematic.py` → KiCad python `pcb/posiciona_v4.py` → venv CadQuery `pcb/vistas_v4.py`, `pcb/blocos_v4.py`, `pcb/portao_p_r8.py` → `python bom_v4.py`; régua: `python pcb/regua/schematic_regua.py` → KiCad python `pcb/regua/posiciona_regua.py` → venv `pcb/regua/vistas_regua.py` → KiCad python `pcb/regua/fab_regua.py`. DRC: `kicad-cli pcb drc --schematic-parity --severity-all`.

---

# PARTE 1 · placa principal

## 2. A placa
- **75,05 x 95,1 mm** (x 2,45..77,5; y 2,45..97,55), cantos R 3, 4 camadas, 1,2 mm; In2 = GND inteira, In1 = +3V3. Só interface (sem tecla, sensor nem multiplexador). **83 peças no esquema; 79 montadas pela JLCPCB, todas no fundo**; em casa: 2 encoders (topo), alto-falante e ponto de teste.
- **Furos M2** (placa → tampa, via postes): H1 (62; 48), H2 (74; 93), H3 (6,5; 48,5), H4 (8; 91,5); módulo: H101 (42; 14), Ø2,7 (parafuso M2,5 + espaçador).
- **DRC sem trilhas (com paridade): 0 erros**, paridade esquema × placa **0**, 242 ligações faltando (esperado), **1 aviso `isolated_copper`** do plano +3V3 sem vias (esperado sem trilhas; some quando o roteador ligar o plano). **ERC 0/0.**

## 3. Blocos e conectores (figuras 1 e 2)

| Bloco | Onde (x; y em mm, y para o jogador) | Notas |
|---|---|---|
| **USB** (J201, ESD, TVS, 2 x 5,1 k) | parede esquerda, pads em **y 10,0** | par D+/D− em B.Cu sem via; 6,75 mm do USB-C ao M.2 (pedido ≤ 7), par de 7,07 mm (≤ 10) |
| **MicroMod** (M.2 J101 + H101) | J101 (22; 18); cartão 22 x 22 em x 24,7..44, y 7..29; H101 (42; 14) | peças sob o cartão ≤ 1,9 mm |
| **Energia** (carregador, conversor, indutor, J202) | canto de trás à direita (x 50..77, y 3..32) | o bloco mais denso (risco de roteamento) |
| **Áudio** (codec U301, OUT J301 y 36, IN J302 y 60, R305 0 ohm, R306/C311) | esquerda (x 2..26, y 28..65) | HP_VGND nunca no GND |
| **Interface** (2 encoders no topo, tela J401, Program) | encoders (20,5; 42) e (38,5; 42); J401 (48,95; 29,5); fenda do cabo 45,45..52,45 x 18,17..20,67 | knobs Ø15 |
| **Amplificador** | U501 (54; 88), pads (48,1; 94,5) | alto-falante e caixa são do design |
| **Fileiras** J601..J604 (SH 6 vias, P6s, bocas para +x) | todos na borda direita, boca em **x 77,4**, em **y 74,03 / 58,01 / 41,99 / 25,97** (fileiras 1..4) | cabo `A06SR06SR30K51B` até o IN da 1ª régua; R605/R606 330 ohm junto do J101 |

Pinagem de J601..J604 (P6s): 1 +3V3, 2 GND, 3 OUT_Rk, 4 GND, 5 SCAN_CLK, 6 SCAN_DATA; pull-down de 100 k por OUT_Rk (R601..R604).
Corredores reservados (regras no `.kicad_dru`): USB (B.Cu, 11..16; 8,2..11,2), barramento OUT/SCAN (x 25,5..34, y 8..54; faixa y 54..57 até x 70; espinha x 68,5..71), I2S do codec, I2S do amplificador (guarda de GND), áudio do fone, energia (0,8 mm), VSYS ao amplificador; OUT_Rk a 0,3 mm de CLK/DATA/I2S/MCLK. Ratsnest: 61 redes, 26 mm/cm²; mais carregada: energia e o entorno do J101.

## 4. BOM da principal e custo
79 peças, **31 linhas, 13 tipos Extended** (nenhum novo: R305 = 0 ohm C17168 e os 330 ohm C25104 são **Basic**), **US$ 17,87 de peças por placa** (`bom_v4.csv`). Extended: J101 (M.2), USB-C, S3B-PH (bateria), PJ-327A, SH-6 (clone), indutor, ESD, TVS, SGTL5000, BQ24074, TPS63001, MAX98357A, XC6206. **Impacto de R305/330 ohm: menor que US$ 0,01 por placa, 0 tipos Extended a mais.**

---

# PARTE 2 · régua universal (figuras 3 e 3b)

## 5. A régua (`kicad/regua/student_v04_regua.kicad_pcb`)
- **73,6 x 14,0 x 1,2 mm** (74 nominais menos 0,2 de folga em cada ponta), 2 camadas, cobre 1 oz. **14 peças, todas no fundo; nada no topo** (a tecla assenta ali). Quadro: u ao longo da fileira, v através (+v = jogador).
- **ERC 0/0; DRC sem trilhas: 0 erros, 0 avisos; paridade 0;** 52 ligações faltando (esperado).

| Ref | Peça | u; v (mm) | Altura |
|---|---|---|---|
| U1..U4 | TMAG5253BA3 (X2SON-4), um por tecla | u = 9,25 + 18,5 k; v 0 | 0,4 |
| **J1 ENTRADA** | SH-6 lateral, boca para trás (−v) | **u 5,9**; v −3,95 | 2,95 (+ plugue 3,6) |
| **J2 SAÍDA** | idem | **u 47,5** (era 68,1); v −3,95 (pegada u 42,8..52,2) | 2,95 (+ 3,6) |
| U5 | 74HC595 DHVQFN-16 2,5 x 3,5 | u 27,75; v +4,2 | 1,0 |
| C1..C4 | 100 nF, um por sensor | junto do VCC de cada TMAG; **C3 em u 47,9; v −0,47 (fora da pegada do J2)** | 0,55 |
| C5, C6 | 100 nF do 595; 10 µF | junto de U5; u 1,5 | 0,55 / 1,45 |
| R1 | **330 ohm** do QH' | u 53,0; v −2,45 (ao lado do J2) | 0,55 |

- **Pinagem P6s** em J1 e J2: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO (J1: SER; J2: QH' por R1).
- **Furos:** 8 de pino da tecla Ø1,70 (±5,08 do centro de cada célula) e M2 Ø2,2 a v +5,2 com patamar sem peças Ø6,4 embaixo; entalhes de 2,0 x 4,3 na borda de trás em u 0, 18,5, 37, 55,5 e 74. **M2 (R8V4 final, design): a régua universal FICA com os três furos Ø2,2 em u 18,5 / 37 / 55,5 (v +5,2), sem mudança; cada régua usa 1 ou 2 (11 M2 no total: fileira 1 = u 18,5 e 55,5 nas duas réguas; fileiras 2 e 4 = u 37; R3.0 = 18,5; R3.1 = 18,5 e 55,5).** Os pares propostos antes (u 12 / 15 / 26,5 / 47,5 / 62) caíam sob carcaça ou no 595 e foram descartados. O 595 (u 27,75) e o C5 (u 30,7) não mudaram. Patamar de Ø6,4 sem peças no fundo em volta de cada furo.
- Roteabilidade: 12 redes, ~346 mm de MST em ~1 030 mm² (34 mm/cm², GND e +3V3 incluídos); o topo (F.Cu) está livre, o roteador tem 2 camadas inteiras.
- **Painel** (`kicad/regua/student_v04_regua_painel.kicad_pcb`): 5 tiras, **87,6 x 92 mm**, trilhos de 5 mm, abas de 3 mm com microfuros, 4 furos de ferramenta, 3 fiduciais; 70 peças; Gerbers só de conferência (`fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/`, **sem rota, não encomendar**). Grade-régua (FR-4 1,6 mm sem cobre, 16 mm de largura): painel de 5 de 83,6 x 98 mm, Gerbers prontos, não encomendados.

## 6. BOM da régua e custo (32 teclas)
14 peças, **3 tipos Extended** (TMAG5253 C22401868, SH-6 C56123098, 74HC595BQ C730243) e 3 Basic (100 nF, 10 µF, 330 ohm C25104). ~US$ 2,3-2,9 de peças por régua; 10 montadas (pedido mínimo, 8 usadas + 2 de reserva) ≈ US$ 23-29 + 9,27 de taxa de Extended.
**Instrumento de 32 teclas (F2, pedido mínimo, sem frete, estimativas):** US$ 289,7-363,4 sem a ligação (a conta da R5V4, 296,6-370,3, com o case de US$ 51,2 trocado pelo **case de US$ 44,3** do design) + **11,4-12,1 dos 8 cabos de 50,8 mm** (10 comprados a 1,206) = **~US$ 301-376**. 0 juntas de solda, 0 tipos Extended novos. (Escala 48/64/80: só a validação do conceito, no `ELETRONICA.md`, sem tabelas.)

## 7. Planta do instrumento (figuras 4 e 5) e furos do design
- **Case 244 x 102 mm, de y −2 a y 100** (parede interna em y 0; a placa fica a 2,45 mm da parede de trás; antes 0,45). Quatro fileiras de 8 teclas, réguas em x 79,95 (fileiras 2 e 4) e 89,2 (1 e 3). Cabeçalhos IN/OUT no fundo de cada régua, boca para trás; cabo de 45,8 mm (cheio) e de 50,8 mm (tracejado) em cada junção e da placa à 1ª régua. As figuras 4 (minha, 32 teclas, C azul/F laranja) e 5 (do design, modelo real) mostram a mesma coisa; vale a 5 em caso de diferença de detalhe.
- **Furos que a eletrônica fixa:** M2/H da placa e H101 (seção 2); régua: 8 pinos Ø1,70 e 3 M2 Ø2,2 (seção 5).
- **Postes e M2 (do design):** postes de parede x 102,5 / 176,6 / 234 em y 5,0 e 93,0; 5 postes internos em (107,7; 68,69), (116,95; 52,67), (181,7; 36,65), (200,2; 68,69), (218,7; 36,65); 11 M2 (seção 5). **Rigidez da régua: 0,028 mm a 3 N no pior caso (≤ 0,05 ✓)**; os M2 não entram na conta (quem segura a tecla são os trilhos).
- **Cabo:** com 45,8 mm de fio útil a reta depois do plugue é de **3,3 mm** (não 5; o raio estático mínimo de 3 mm ainda cabe); com 50,8, 5,8 mm. Fileira 4, OUT em u 47,5: folga à parede de trás 3,29 mm (45,8) e 0,79 mm (50,8) além da margem de 0,5. Folga vertical do feixe às peças da régua de cima ≥ 2,3 mm. **Fita colada não fecha** (colisão de 0,03-0,19 mm nas fileiras 1 e 2 e dobra só no plano da fita): risco, ver seção 8.
- Fit check das 32 teclas (design): 0 mm³ em todos os pares. Case ≈ **US$ 44,3** (MJF, +US$ 0,64 pela profundidade).

## 8. Riscos aceitos (só a peça real fecha; nada é comprado antes do protótipo)
1. **Cabo `A06SR06SR30K51B`:** reto de verdade? 45,8 ou 50,8 mm de fio livre (reta de 3,3 mm com 45,8)? Fios soltos ou fita colada (**fita colada não fecha**: o laço em pé bate na régua de cima e a fita não dobra no plano; voltaria a cabo sob medida)? O desenho fecha com 45,8 e 50,8 e fios soltos. Cabo invertido não queima nada (P6s + 330 ohm), mas a varredura não funciona.
2. **Clone SH C56123098:** medidas e acoplamento com o plugue JST sem desenho do fabricante; 2,95 + 3,6 mm sob a régua (bolso da fileira 1: 6,9 mm).
3. **330 ohm** no CLK a 5 MHz: sobra margem; firmware pode descer a 2,5 MHz.
4. **Microfone com R305 = 0 ohm:** limiares do MIC_DET e partida de cápsulas que pedem mais de 3 V são cálculo; plano B (boost 9-10 V, ~US$ 6,5) só registrado.
5. **JLCPCB:** painel do cliente com abas e microfuros em montagem econômica; pads do DHVQFN-16 (C730243) contra o EasyEDA.
6. **Roteabilidade:** bloco de energia e pads 3/5 do M.2 apertados; 242 ligações faltando e 1 aviso `isolated_copper` até o roteamento.

## Perguntas do portão e respostas do design (R8V4)
1. **Rigidez com os M2 (um por régua nas fileiras 2-4):** 0,028 mm a 3 N no pior caso, ≤ 0,05 ✓; os M2 não mudam o número. Aceitar **11 M2** (retenção também pelos furos do deck e pelos pinos) é pergunta do design ao J.
2. **OUT em u 47,5 e R1 em u 53 nos entalhes e rebaixos:** fit check de 32 teclas 0 mm³; rebaixo de 39,8 x 22,5 mm por junção (25,0 com 50,8) a partir da boca do cabeçalho, entalhe de cabeçalho de 10,4 mm e de plugue de 7,4 mm; piso de 2,0 mm íntegro.
3. **Bolso da fileira 1 (6,9 mm) e profundidade de 102 mm:** cabeçalho 2,95 + plugue 3,6 cabe; queda do cabo 5,1 mm em 12,3 mm; folga vertical ≥ 2,3 mm. A fenda da tampa (y 18,2..20,7) e os J60k (x 77,4) seguem como estão.

**Depois do "aprovado" do J:** `roteamento` (principal e régua), depois `cpl_jlc.py`/BOM/CPL de fábrica e Gerbers finais.
