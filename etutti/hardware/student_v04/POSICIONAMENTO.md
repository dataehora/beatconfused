# eTutti Student V4 · posicionamento (portão P, partes 1, 2 e 3) · R5V4 (teclado de 32 teclas; ligação das réguas)

**NÃO APROVADO: quem aprova é o J.** Nada roteado (0 trilhas, 0 vias, na principal e na régua). Nenhum arquivo de `fab/` da principal ou da régua foi gerado para encomenda (só os da grade-régua, que não tem circuito). Data: 21 nov 2026. O agente `roteamento` só entra depois do "aprovado" das duas partes.

Reproduz, na ordem (raiz do repositório):
- **Parte 1 (principal):** `python pcb/schematic.py` → KiCad python `pcb/posiciona_v4.py` → venv CadQuery `pcb/vistas_v4.py` e `pcb/blocos_v4.py` → `python bom_v4.py`.
- **Parte 3 (R5V4, ligação):** `python pcb/regua/schematic_regua.py` → KiCad python `pcb/regua/posiciona_regua.py` (agora com os pads LK1/LK2) → venv CadQuery `pcb/regua/ligacao.py` (figuras e números) → KiCad python `pcb/regua/fab_regua.py` → `pcb/regua/vistas_regua.py`; custo: `python calculos_eletronica.py`.
- **Parte 2 (régua):** `python pcb/regua/schematic_regua.py` → KiCad python `pcb/regua/posiciona_regua.py` → venv CadQuery `pcb/regua/vistas_regua.py` → KiCad python `pcb/regua/fab_regua.py`.
- Instrumento inteiro e corte lateral (do **design**, `case/planta_v4.py`, `case/corte_v4.py`): `case/renders/planta_geral_v4.png`, `case/renders/corte_interface_v4.png`.

Figuras (abra estas para decidir):
| Figura | Arquivo |
|---|---|
| Instrumento inteiro, vista de cima (28 teclas, modelo real) | `case/renders/planta_geral_v4.png` |
| Corte lateral pela interface (alturas) | `case/renders/corte_interface_v4.png` |
| Principal, topo, blocos e cotas | `pcb/img/principal_blocos_topo.png` |
| Principal, fundo (visto de baixo), blocos e cotas | `pcb/img/principal_blocos_fundo.png` |
| Principal: corredores e ratsnest | `pcb/img/topo.png`, `fundo.png`, `ratsnest.png` |
| Régua, planta (transparência) | `pcb/regua/img/regua_planta.png` |
| Régua, cortes (através das 4 fileiras e ao longo) | `pcb/regua/img/regua_corte.png` |
| **R5V4** Ligação das réguas: opção recomendada (D), planta e corte (placa → 1ª régua; régua → régua) | `pcb/regua/img/ligacao_D.png` |
| R5V4 Opções A (cabo pronto de 15/25 mm), A-estoque (100 mm: não cabe), B (tudo soldado), C (FFC/FPC) | `pcb/regua/img/ligacao_A.png`, `ligacao_Astock.png`, `ligacao_B.png`, `ligacao_C.png` |
| **R5V4** Teclado de 32 teclas com o nome de cada nota (C azul, F laranja) e as 8 ligações | `pcb/regua/img/ligacao_teclado32.png` |
| Painel de réguas (sem rota) e painel da grade-régua | `pcb/regua/img/regua_painel_fundo.png`, `grade_regua_painel_topo.png` |

---

# PARTE 1 · placa principal

## 1. A placa
- **75,05 x 95,1 mm** (x 2,45..77,5; y 2,45..97,55), 4 camadas, 1,2 mm, cantos R 3. Só interface; **77 peças JLC, todas no fundo** (no topo só os 2 encoders, o furo do módulo e os pads do alto-falante). Sem tecla, sensor, multiplexador nem furo de grade.
- Furos M2: H2 (74; 93), H3 (6,5; 48,5), H4 (8; 91,5) como na V3 e **H1 em (62; 48)** (proposto); H101 (módulo, Ø2,7) em **(42,0; 14,0)**.
- **In2 = GND inteira**, In1 = +3V3. Os polígonos de GND de F.Cu/B.Cu vêm com o roteamento.
- Estado: DRC sem trilhas com paridade **0 erros de courtyard, furo, borda e altura sob o cartão; paridade 0**; 234 ligações faltando (esperado) e 1 aviso `isolated_copper` do plano +3V3 sem vias (some ao rotear).

## 2. Blocos (ver `principal_blocos_topo.png` e `principal_blocos_fundo.png`)
| Bloco | Onde (x; y em mm, y para o jogador) | Notas |
|---|---|---|
| **USB** (USB-C J201, ESD U201, TVS, 2 x 5,1 k) | parede esquerda, pads em **y 10,0** | furo na parede esquerda em **y 10**; par D+/D- em B.Cu sem via |
| **MicroMod** (M.2 J101 + H101) | J101 em (22; 18); cartão 22 x 22 em x 24,7..44, y 7..29; H101 (42; 14) | 5,5 mm à esquerda do que era na V3; peças sob o cartão ≤ 1,9 mm |
| **Energia** (carregador, conversor, indutor, J202 da bateria) | canto de trás à direita (x 50..77, y 3..32) | herdado da V3, bloco mais denso |
| **Áudio** (codec U301, OUT J301 y 36, IN J302 y 60) | esquerda (x 2..26, y 28..65) | HP_VGND nunca no GND |
| **Interface** (2 encoders no topo, tela J401, Program) | encoders em (20,5; 42) e (38,5; 42); J401 (48,95; 29,5); **fenda do cabo 45,45..52,45 x 18,17..20,67** (R4V4: boca do J401 para −y; o plugue ocupa y 21,2..26,2 e os fios saem a y ≈ 20,7, então a fenda foi para depois do plugue; era 22,17..24,67, sob o plugue; o design deve mover a janela/fenda da tampa, y 18,2..20,7) | knobs Ø15 tracejados |
| **Amplificador** (U501 + pads do alto-falante J501) | U501 (54; 88), pads (48,1; 94,5) | alto-falante e caixa são do design |
| **Fileiras** (J601..J604, SH 6 vias, bocas para +x) | **todos na borda direita, boca em x 77,4**, em y 74,03 / 58,01 / 41,99 / 25,97 | cabo SH até o J1 da régua (parte 2) |

## 3. USB-C e M.2
| | pedido | esta placa |
|---|---|---|
| USB-C (pads de sinal) a pads 3/5 do M.2 | ≤ 7 mm | **6,75 mm** |
| par D+/D- (USB-C → USBLC6 → pads 3/5), linha reta | ≤ 10 mm | **7,07 mm** |
| referência | In2 inteira | sim (par em B.Cu, sem via) |

## 4. O que mudou desde a planta do Chat (`spec_img/`)
1. **J602 (fileira 2) na borda**, boca em x 77,4 como os outros três (a planta do Chat o mostrava recuado, em x ~65..71, com área de plugue reservada). Como o conector de entrada da régua fica **por baixo dela**, a área de plugue de 6,5 x 10,4 mm saiu; a régua da fileira 2 (x 79,95) recebe o plugue do J602 sob a ponta (**janela no bolso: pergunta 1**).
2. Posição do USB-C, M.2 e H101 como a planta do Chat (aprovado pelo J): sem mudança.
3. Posições reais de peças pequenas (U501 em (54; 88), U301 (24; 35,5), J401 (48,95; 29,5), SW403 Program (52; 36)) vêm de `posicao_v4.json`; a planta do Chat as aproximava por caixas. Movidas pelo script em relação à V3: D205, D206 e U302.
4. Bateria, alto-falante (Dayton CE28MB-8) e caixa acústica são do design (`planta_geral_v4.png`); a eletrônica só confere que os pads J501 e o U501 ficam sob a caixa (ficam).
5. BOM: **13 tipos Extended** na principal (nada mudou); `bom_v4.csv`.

## 5. Corredores reservados e roteabilidade
USB (11..16; 8,2..11,2, B.Cu) · barramento OUT/SCAN (x 25,5..34, y 8..54; faixa y 54..57 até x 70; espinha x 68,5..71) · I2S codec · I2S amplificador (guarda de GND) · áudio do fone · energia (0,8 mm) · VSYS ao amplificador. Regras no `.kicad_dru`: OUT_Rk a 0,3 mm de CLK/DATA/I2S/MCLK; USB só em B.Cu; peças sob o cartão ≤ 1,9 mm.
Ratsnest: 61 redes (GND/+3V3 pelos planos), 1 844 mm de MST em 7 140 mm² = **26 mm/cm²**; a célula mais carregada é o bloco de energia e o entorno do J101. Riscos: pads 3/5 do M.2 e U201 apertados (4,3 mm entre USB-C e M.2); bloco de energia denso.

---

# PARTE 3 · ligação das réguas (R5V4, item 3 da SPEC): estudo e contrato

Para as 32 teclas: **8 ligações** = 4 da placa à 1ª régua (uma por fileira, 25 mm, desnível 0-7 mm) + **4 elos régua → régua** dentro da fileira (em linha, mesma altura, a 0,4 mm).
Cada módulo de +16 teclas acrescenta **4 elos** (48 teclas: 12 ligações; 64: 16; 80: 20). Cada ligação leva 5 condutores: +3V3, GND, OUT, CLK, DATA (SER na entrada, QH' na saída).
Figuras: `ligacao_<opção>.png` (4 painéis cada: planta placa → 1ª régua, planta régua → régua, corte pelo eixo x, corte ao longo da fileira).

## 10. Achado que decide: nenhum cabo de estoque tem o comprimento que a geometria pede
- O mais curto **pronto, com plugue SH nas duas pontas, 6 vias**, é de **100 mm** (Pololu #5543, 10 cm, 28 AWG, US$ 3,32; Pimoroni 100 mm em pacote de 4). Há também a JST ASSHSSH28B51 (51 mm; **não confirmei que seja de 6 vias**, Farnell). A geometria da R4V4 pede **15 mm** entre réguas e **25 mm** da placa.
- Sobra de **88 mm** (elo) e **75 mm** (placa → régua) de cabo de 6 fios: o laço teria ~20-28 mm de fundo (`ligacao_Astock.png`) e o bolso da fileira 1 tem 6,9 mm; o design já tinha achado que 50 mm não cabe. **Cabo de estoque não serve em nenhuma das 8 ligações.**
- Cabo de 15/25 mm só **sob medida** (cabo de montador): não achei cotação publicada de 15/25 mm. Referência: Newegg, SH 1,0 mm 6 pinos, 28 AWG, **300 mm, lote de 50 = US$ 152,5** (~US$ 3 por cabo). Sem cotação, **A é inviável hoje**.
- **FFC/FPC 1,0 mm** (opção C): jumper Molex 150390201 (31 mm, mesma face), o mais curto que achei; na biblioteca da JLCPCB só vi cabos soltos (C90533 7 cm, US$ 0,055, 998 em estoque; C62492 10 cm, 4 em estoque) e **nenhum conector FPC de 6 vias em estoque** (C48735 estava com estoque 0). Um FFC não dobra no plano: entre dois conectores de boca alinhada ele faz um arco de ~5 mm para baixo.

## 11. As opções (32 teclas = 8 ligações; minutos e dificuldade são estimativas minhas)
| | **A** cabos SH-6 prontos | **B** tudo soldado | **C** FFC/FPC com conector | **D** misto (**recomendada**) |
|---|---|---|---|---|
| O que é | plugue nas duas pontas; J1/J2 nas réguas e J601-J604 na placa (como a R4V4) | 5 pads de 1,4 x 0,7 mm a 1,0 mm em cada ponta de régua e na borda da placa; fio 28-30 AWG de 7-10 mm | conector ZIF 1,0 mm 6 vias nas pontas; jumper FFC | cabo SH-6 de 25 mm da placa à 1ª régua (4) + elo soldado de 5 fios dentro da fileira (4) |
| Achável hoje | só sob medida (sem cotação); o de estoque (100 mm) não cabe | sim (fio, solda) | conector em estoque: não achei | elo sim; os 4 cabos de 25 mm: sob medida, ou **crimpados em casa** |
| Custo (32 teclas) | cabos US$ 26,6 (estoque, não cabem) ou ~US$ 150 (lote de 50, ref.); 0 Extended a mais | **~US$ 4** (fio + fluxo); sai 1 tipo Extended das réguas (-3,09) se J1/J2 forem retirados | ~US$ 2,4 + **1 tipo Extended a mais** (+3,09 na régua e +3,09 na placa) | **~US$ 36** (4 cabos crimpados + ferramenta de US$ 30, que serve depois) ou ~US$ 154 (lote de 50), mais US$ 4 de fio |
| Montagem em casa (32 teclas) | ~12 min (8 plugues) | ~40 min, 80 juntas | ~24 min, 16 fechos ZIF | ~26 min: 40 juntas + 4 plugues (cabos crimpados: +1 h, uma vez) |
| Dificuldade | a mais fácil | a mais difícil (passo 1,0 mm, bolso estreito) | média; o fecho ZIF abre se mexido | média |
| Confiabilidade e troca de régua | boa; troca fácil | **a melhor eletricamente**; troca exige dessoldar 10 juntas | média | boa; troca = dessoldar o elo (5 fios) |
| Placa principal (J601-J604) | como está | **muda**: 4 conectores viram 4 grupos de 5 pads na borda | muda (conector FPC) | **não muda** |
| Régua | como está | J1/J2 saem; pads nas pontas | muda (FPC nas pontas) | **J1 + pads LK1/LK2** (J2 fica só para aceitar a opção A sem mexer: US$ 0,07 por régua) |
| Cresce com o módulo (+16 teclas) | +4 cabos de 15 mm sob medida | +4 elos (+20 min) | +4 jumpers + 8 fechos | +4 elos soldados (+20 min) |

**Por que D:** o J prefere comprar. D compra o que existe (conector, cabo) e solda só o que nenhum fornecedor vende no tamanho (um elo de 4,2 mm entre pads); **não muda a placa principal** (que o J já viu e aprovou em princípio); a régua serve a A, B e D, e a escolha final pode esperar o protótipo.
**Se o J não quiser pagar US$ 36-154 pelos 4 cabos de 25 mm, B custa US$ 4**, mas muda a placa (4 conectores viram pads; ~30 min de script). Ponto fraco da D: **os 4 cabos de 25 mm não existem prontos**: ou cotação com um montador (sem preço), ou crimpar em casa (contatos SSH-003T-P0.2 e caixas SHR-06V-S da JST, ferramenta de crimpagem), ou o plano B só na placa.

## 12. Contrato da recomendada (D), para o design ler
**Elo soldado régua → régua** (`pcb/regua/posicao_regua.json`; quadro u ao longo da fileira, v através, +v = jogador):
- LK1 (entrada) em **u = 2,1** e LK2 (saída) em **u = 71,9** (régua nominal 0..74), **5 pads de 1,4 (u) x 0,7 (v) mm, passo 1,0, centros v = -0,4, 0,6, 1,6, 2,6, 3,6** (pino 1 = v -0,4, para trás), no **fundo**. Ordem: 1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 SER (LK1) / QH' (LK2); o 6º condutor (OUT_B) não segue no elo. Cobre u 1,4..2,8 e 71,2..72,6; v -0,75..3,95.
- Entre os pads de duas réguas vizinhas: **4,2 mm de centro a centro** (0,4 de vão + 2 x 1,9); fio de 28-30 AWG, **7 mm, pontas de 1,4 mm estanhadas sobre os pads**; o fio fica **~1 mm abaixo** da face de baixo da régua (0,6 de fio + 0,4 de solda): bolso da fileira 1 = 6,9 mm, sobram ~5,9.
- **Espaço pedido ao design sob a junção** (v -0,9..4,0, u 70,9..76,8 em torno dela): livre de peças e de bossas da bandeja (as trilhas de trás e da frente ficam fora: v < -4,2 e v > 4,2). O **poste/nervura do entalhe de ponta (u ±1, v -7..-2,7)** fica fora do elo: o fio mais próximo (v = -0,4, borda -0,7) passa a 2,0 mm dele. Pinos da tecla: borda a 0,5 mm do pad (pinos em u 4,17 e 69,83; pads até 2,8 e desde 71,2).
- **Placa → régua (4 cabos de 25 mm):** J601-J604 como estão (boca para +x, x 77,4); J1 da régua em u = 5,9, v = -3,95, boca para trás (contrato da R4V4, sem mudança). Nas fileiras 2 e 4 a ponta da régua fica a 2,55 mm da borda da placa e o plugue de 5 mm entra sob ela: **por isso o cabo da placa vai ao J1 e não aos pads LK1** (o plugue ficaria sob os pads).
- J2 deixa de ter cabo na recomendada (o OUT da régua vai pelo elo). A janela do plugue de J2 e o entalhe de 8 mm na trilha da frente da fileira seguinte deixam de ser necessários, mas **ficam se o design quiser manter a opção A**.
- Cadeia de registradores com as 4 posições sempre ocupadas: **nada muda** (8 estágios por régua, 4 mortos, 8 x N + 1 pulsos: 17 / 25 / 33 / 41 em 32 / 48 / 64 / 80 teclas). Capacitância da linha OUT: cai um pouco, sem os cabos de 15 mm (D usa 25 mm só na placa).

---

# PARTE 2 · régua universal e grade-régua

## 6. A régua (`kicad/regua/student_v04_regua.kicad_pcb`)
- **73,6 x 14,0 x 1,2 mm**, 2 camadas (74 nominais menos 0,2 de folga em cada ponta), cobre 1 oz. **14 peças e 2 grupos de pads (LK1, LK2), tudo no fundo; nada no topo** (a tecla assenta ali). R5V4: ERC 0/0, paridade placa x esquema 0, **DRC sem trilhas: 0 erros, 0 avisos**; 60 ligações faltando (esperado).
- Quadro: u ao longo da fileira (0..74 nominais), v através (+v = frente, jogador), v = 0 na linha de centro.
- **Furadas:** 8 furos de pino da tecla **Ø1,70** (2 por tecla, ±5,08 do centro da célula, v = 0) e 2 furos **M2 Ø2,2 em (18,5; +5,2), (37; +5,2) e (55,5; +5,2)** (a régua é universal: cada fileira usa dois, 1: 18,5+55,5; 2: 37+55,5; 3 e 4: 18,5+37); patamar sem peças Ø6,4 embaixo em volta de cada M2. Entalhes de 2,0 x 4,3 na borda de trás em u = 0 (meio), 18,5, 37, 55,5 e 74 (meio).
- **Peças** (u; v; ver `regua_planta.png`):
| Ref | Peça | Posição | Altura |
|---|---|---|---|
| U1..U4 | TMAG5253 BA3 (X2SON-4) | u = 9,25 + 18,5 k; v = 0 (pino 1 VCC e 4 OUT para trás) | 0,4 |
| J1 (entrada) / J2 (saída) | JST SH 6 vias, lateral, clone XYECONN C56123098 | **u = 5,9 / 68,1 (contrato do design)**; v = −3,95; pinos ao longo de u, **boca para trás (−v)** | 4,3 **(conferir)** |
| U5 | 74HC595 em DHVQFN-16 2,5 x 3,5 (C730243) | u = 27,75; v = +4,2 (faixa da frente, entre os M2 de 18,5 e 37) | 1,0 |
| C1..C4 | 100 nF 0402, um por sensor, junto do VCC | atrás de cada sensor | 0,55 |
| C5, C6, R1 | 100 nF do 595, 10 µF 0805, 100 Ω de QH' | junto de U5, J1 e J2 | 0,55 / 1,45 |
- **Por que o 595 virou DHVQFN (Extended, +US$ 3,09 por pedido de régua):** o SOIC-16 do C5947 (Basic) tem **6,9 mm** de pads; a régua tem 14 mm com furos de pino a 10,16 mm no meio (vão livre de 6,64 mm entre pinos de teclas vizinhas) e metade de cada lado de 5,8 mm: não cabe em nenhuma posição. O TSSOP-16 é mais largo (7,2 mm). O DHVQFN-16 tem 3,5 x 4,5 e cabe na frente.
- **Conectores (R4V4, contrato do design, `FIT_CHECK.md` §3): IN em u = 5,9 e OUT em u = 68,1**, faixa de trás, boca para trás; o plugue passa sob a régua da fileira de cima por entalhe da bandeja. Cabe: o pátio do J1 (u 1,4..10,45) fica a 0,4 mm do entalhe de meia ponta e longe do sensor 1 (pads a u ≥ 9,0 em v ≥ −1,06; o conector termina em v −1,05). Antes eu os tinha em 31,2/42,8 (mais ao centro); o design mostrou que as pontas dão o laço de 15 mm do cabo. **Por que o SH-6 lateral fica atrás, com a boca para trás:** o conector tem 9,9 mm de largura e 4,3 de altura. Na linha de centro (v = 0) há furos de pino e sensores em quase todo u; na frente, o plugue bate na régua da fileira da frente (mais baixa, 2 ou 3 mm) e na trilha dela; para trás, o plugue passa **por cima** da régua da fileira de trás (mais alta) e só encontra a trilha dela. Fica entre os entalhes (u 20..36 e 38..54) e a 0,3 mm do borda.
- **Roteabilidade (ratsnest da régua):** 12 redes, 346 mm de MST em 1 030 mm² (**34 mm/cm²**, GND e +3V3 incluídos: ~185 mm de sinal); o topo (F.Cu) está livre de peças, só com os furos, então o roteador tem 2 camadas inteiras. OUT corre ao longo da régua (56 mm, passando entre os furos dos pinos a v = ±1,2); EN1 e EN4 são as mais longas (29 mm).

## 7. Contrato com o design (a atualizar no `FIT_CHECK.md`; **o contrato do design de R4V4 ainda não chegou**, esta é a proposta da eletrônica)
1. **Conectores** J1 e J2 = **contrato do design**: u = 5,9 e 68,1 do início da régua, v = −3,95, boca para **trás**; plugue de 7,6 mm em u, 5,0 além da borda de trás, z −1,2..−5,5. Janelas (início da régua): u 2,1..9,7 (J1) e 64,3..71,9 (J2), v −12..−7. Em cada fileira atrás de outra, a **trilha da fileira de trás precisa de uma janela de ~7 x 2,8 mm** (e a bandeja, nenhum degrau no caminho): ver `regua_corte.png`(a). A fileira 4 não tem nada atrás.
2. **Pocket** (sob a régua, v = −4,2..+4,2): TMAG 0,4 mm; 74HC595 de 1,0 mm **em v = +2,0..+6,6** (entra 2,4 mm no vão das trilhas da frente, 4,2..7: precisa de uma janela de ~5 x 3 mm na trilha da frente em u 35..39); capacitores 0,55 (10 µF: 1,45); pontas dos pinos da tecla **1,5 mm** abaixo da régua (v = 0).
3. **Cabos sob medida do design:** 15 mm de plugue a plugue entre réguas (J2 em u 68,1 a J1 em u 5,9+74: 11,8 mm de centro a centro) e 25 mm da principal à 1ª régua. Cabos curtos reduzem a capacitância da linha OUT (20 sensores + trilhas + 5 cabos de 15 mm: **~400 pF, estimativa**, contra 1 nF).
4. **M2:** a régua leva os **três** furos Ø2,2 (18,5, 37 e 55,5; v +5,2) e cada fileira usa dois (contrato do design); cabeça Ø3,8 no corredor entre teclas. **O 595 foi para u = 27,75, entre os M2 de 18,5 e 37.**
5. **Grade-régua** (mudança do contrato de R3V4): **largura 16,0 mm** (v −8..+8), não 14,0: as aberturas já têm **14,00 mm**, não sobraria material. Com 16,0 sobram 1,0 mm de cada lado e **4,5 mm entre aberturas**; 73,6 mm de comprimento, 1,6 mm FR-4, aberturas 14,00 x 14,00 com R0,5 (fresa) nos centros 9,25 + 18,5 k, os mesmos entalhes (4,3 de fundo a partir da nova borda de trás, 2,0 de largura). A fileira vizinha fica 16,02 mm adiante, **0,02 mm** de folga entre grades vizinhas, em z diferentes (2 ou 3 mm): sem conflito. **Pergunta ao design: 16,0 serve? E a espessura de 1,6 mm com 1,0 mm de borda é frágil?**

## 8. Painéis e arquivos (`pcb/regua/fab_regua.py`)
- **Painel de réguas** (`kicad/regua/student_v04_regua_painel.kicad_pcb`): 5 tiras de 73,6 x 14 a 2 mm uma da outra, **87,6 x 92 mm**, trilhos de 5 mm, 2 abas de 3 mm por borda longa com 3 microfuros Ø0,5 (passo 0,9), 4 furos de ferramenta Ø2,0, 3 fiduciais (1 mm de cobre, 2 mm de máscara) no trilho de baixo. 70 peças. **Sem rota**: o script copia as trilhas da régua unitária quando existirem. Gerbers só de conferência em `fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/`, com BOM e CPL **provisórios** (a rotação das peças vem do `cpl_jlc.py`, depois do portão).
- **Grade-régua**: `kicad/regua/student_v04_grade_regua.kicad_pcb` (uma) e **`student_v04_grade_regua_painel.kicad_pcb` (5, 83,6 x 98 mm, trilhos de 3 mm por não ser montado e ficar abaixo de 100 mm)**, FR-4 1,6 mm, 2 camadas **sem cobre** (só máscara sobre FR-4: o tom pode diferir do cobre, não importa debaixo da tampa), sem componentes, nome no verso. **Gerbers prontos: `fab/student_v04_grade_regua_painel_gerbers.zip`** (F.Cu/B.Cu vazias, máscara, serigrafia, contorno, furação). DRC da unitária: 0 erros e 1 aviso de altura de texto; do painel: só `invalid_outline` pelas aberturas das abas (esperado; **conferir com a JLCPCB** se aceita o contorno aberto nas abas ou se prefere V-cut/rota separada).
- BOM da régua (`bom_regua.csv`): 14 peças, **3 tipos Extended** (TMAG, SH-6, 74HC595BQ) e 3 Basic (100 nF, 10 µF, 100 Ω).

## 9. Custo (US$; detalhe e tabela no `ELETRONICA.md`)
**R5V4 (32 teclas):** as 8 réguas já tinham 4 sensores cada, então a eletrônica não muda; entram **+4 teclas Gateron (US$ 3,5-3,8)** e **+4 botões** (design). Sem a ligação: **296,6-370,3** (F2, pedido mínimo, sem frete). Com a recomendada (D): **+US$ 40 (cabos crimpados) a +158 (lote de 50)**; com B, **+US$ 4**. Escalas 48 / 64 / 80 (sem a ligação e sem o case do design): 322-397 / 348-424 / 362-439.
(abaixo, valores da R4V4, 28 teclas)
Régua: 2,33 de peças por régua (10 montadas = 23,28); 3 tipos Extended x 3,09 = 9,27 (eram 2 = 6,18). F2 de 28 teclas, pedido mínimo, sem frete: **296-375** (R3V4: 296-375, a troca do 595 custa ~US$ 4 no cenário baixo e fica dentro da faixa); com a grade-régua (2-8) e a ferragem (2-4): **300-387**, contra F1 332-477: **-10 % a -19 %**.

## Perguntas para o design (deste portão)
1. **Janela para o 74HC595**: ele desce 2,4 mm sobre o trilho da frente (u 26..30, v 4,2..7); o degrau aceita uma janela de ~5 x 3 mm ali, ou o 595 deve ir para o eixo? (Os plugues seguem o contrato do design.)
2. **Grade-régua:** o design disse "não muda (73,6 x 14)", mas aberturas de 14,00 mm numa tira de 14,0 mm não deixam material (isto é fisicamente impossível). Mantive **16,0 mm**; confirme ou diga outra largura.
3. (ver 2) grade-régua de 16,0 mm: serve às presilhas e ao deck?
4. Furo do USB-C na parede esquerda em **y 10** e o J602 na borda x 77,4: o plugue passa por baixo da ponta da régua da fileira 2 (x 79,95..82,4)? A planta do design já mostra isso, confirmar.
5. Furos da principal: H1 em (62; 48) e posição das pernas da interface.
