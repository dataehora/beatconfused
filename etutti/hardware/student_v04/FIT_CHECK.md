# eTutti Student V4 — FIT_CHECK (design)

## R6V4 — atendida (22 nov 2026, tarefas de Design: itens 1 e 3)

Nada foi encomendado, impresso ou montado. As seções R5V4 e anteriores valem, menos onde esta diz o contrário. Peças e medidas: **as reais da eletrônica** (`ELETRONICA.md`, R6V4); o que ainda é estimativa está marcado **(conferir)** (a ficha da fêmea H3,4 não tem folha de desenho: uso o footprint do irmão H4,3).
Reproduz (venv CadQuery; `case/out/` fora do git): `case/case_r4.py 0 1 2 3` (modelo + interferências; já com o elo E2) → `case/juncao_v6.py --tudo` (opções, figuras, `case/out/juncao_r6.json`) → `case/planta_v4.py`, `case/corte_teclado_v5.py`. Dados das opções: `case/juncao_r6.py`.
Imagens novas (`case/renders/`, com o **nome da nota em cada tecla**, C e F destacados): **`juncao_opcoes_r6.png`** (planta da junção E4|G4 e corte da F#4|A4 de E1, E1c, E2, E2b, F), **`juncao_E2_r6.png`** (a recomendada: planta, dois cortes, montagem), `juncao_placa_r6.png` (placa → 1ª régua). Atualizadas para 244 mm: `planta_geral_v4.png`, `corte_chanfro_v5.png`.

### 1. Item 3 — case +4 mm, chanfro, mesa FDM

- `CASE_LEN` 240 → **244 mm** (`layout_r4.py`); módulos **318 / 392 / 466** (48 / 64 / 80 teclas). Régua mais à direita termina em x 237,0, parede interna em 242,0: folga de 5,0 (era 1,0); **deck plano da borda do último botão (236,2) até o começo do chanfro (242): 5,8 mm** (era 1,8), 7,8 mm até a borda externa. Chanfro 2,0 x 2,0 em cima e 1,0 x 1,0 embaixo (aprovados) mantidos; nenhuma interseção nova.
- **FDM 250 x 250: a tampa de 32 teclas (244 x 100) cabe**, com 3 mm de sobra de cada lado em x: só com mesa de 250 inteira e sem aba/brim maior que ~2,5 mm (Prusa MK4 250, Bambu A1 256; não Ender 3, 220). 48 teclas (318) e acima: MJF/SLA/FDM grande.
- Volumes (com o berço do elo E2, abaixo) e impressão MJF PA12 (US$ 0,275/g, 1,01 g/cm³, sem cotação):

| Teclas | Comprimento | Tampa + base (cm³) | Massa | Impressão (US$) | R5V4 (240) |
|---|---|---|---|---|---|
| 32 | 244 | 88,1 + 76,8 = **164,9** | 167 g | **~45,8** | 44,4 |
| 48 | 318 | 113,7 + 106,7 = 220,4 | 223 g | ~61,2 | 59,2 |
| 64 | 392 | 139,2 + 136,6 = 275,8 | 279 g | ~76,6 | 74,0 |
| 80 | 466 | 164,8 + 166,4 = 331,2 | 335 g | ~92,0 | 88,9 |

(+US$ 1,4 pelos 4 mm e ~0,3 por módulo pelos berços.)

### 2. Item 1 — geometria das opções de junção (planta e corte: `juncao_opcoes_r6.png`)

Dados de partida conferidos no modelo: régua 73,6 x 14 x 1,2 (passo 74,0, vão 0,4); **faixa livre no eixo entre o pino da última tecla de A e o da 1ª de B = 6,64 mm** (confere com o Chat); pinos D1,7 com furo D1,7 e M2 com folga de ~0,1 mm: **a régua não anda em x**. Bolso sob a régua: **6,9 / 8,9 / 10,9 / 13,9 mm** (fileiras 1-4).

| Opção | Peças (medidas) | Altura sob a régua | Folga no bolso da fil. 1 | Conflitos no modelo (4 junções, 32 teclas) | Veredito |
|---|---|---|---|---|---|
| **E1** macho/fêmea em ângulo, pinos ao longo de x (esboço: fêmea 5,6, macho 3,1) | não existe peça 1x5 de 1,27 em ângulo, SMD, em estoque (ELETRONICA) | 3,4 | 3,5 | **pinos das teclas 13,6 mm³**; J1/J2 94-145 mm³; C6 31 mm³ | **inviável** |
| **E1c** o mesmo com <= 3,3 mm de fundo (peça hipotética) | não existe | 3,4 | 3,5 | pinos 0; J1/J2 59-65 mm³, C6 | geometria quase serve, **montagem impossível** |
| **E2** fêmea igual nas duas pontas + ponte com 2 machos, por baixo (C55566451, C55213903) | fêmea 6,76 x 5,2 x 3,4 em u 5,9 / 68,1, faixa de **trás** (v -6,9..-1,7); macho 1,0 (+0,6 de vão); ponte PCB 1,2 x 19,8 x 5,3 | **6,2** | **0,7** (ponte de 0,8 mm: 1,1) | **0 mm³** com tudo, em 32 / 48 / 64 / 80 | **recomendada** |
| E2b machos nas réguas + ponte com fêmeas | (estimativa) macho 1,5 + fêmea 3,4 + 0,8 | 5,7 | 1,2 | R1 3 mm³, C6 41 mm³ (faixa da frente) | pinos expostos na régua solta; pior que E2 |
| F contatos de mola contra pads | (estimativa) mola 3,0 montada, passo 2,0, ponte 20,8 | 3,8 | 3,1 | R1, C6 (faixa da frente) | reserva; a eletrônica descartou (retenção, ruído) |
| cartão de borda | nenhum para PCB de 1,2 mm (eletrônica); também encaixaria em x | — | — | — | fora |

**Por que o E1 está morto, com dois motivos que independem da peça:** (a) a fileira de contatos fica ao longo de y e atravessa o pino da 1ª tecla de B (o footprint de 5,6 mm bate nele: 13,6 mm³; mesmo com 3,3 mm sobra o J1/J2 de 9,4 mm no fundo da régua); (b) o encaixe é em x: a régua B teria de deslizar ~3 mm, mas só se posiciona pelos 8 pinos D1,7 e pelo M2 (folga 0,1 mm); "montar a fileira da direita para a esquerda" não existe. Inclinar a régua como num módulo de memória exigiria ~20 graus em torno do conector e não cabe no bolso.

**E2, números (`juncao_r6.json`, `juncao_E2_r6.png`):**
- **Fit check 32 / 48 / 64 / 80 teclas (4 / 8 / 12 / 16 junções): 0 mm³** de ponte, machos, fêmeas, berço e macho do pigtail contra bandeja, pinos de tecla, sensores, parafusos M2, cabeçalhos, plugue e tampa; mais todos os pares do R5V4 (as colunas de sensibilidade carcaça +0,5 / +0,8 mm seguem as de sempre: 8,3 / 50,4 mm³ em 32). Nenhum poste a menos de 18,5 mm de uma junção; a faixa de trás não alcança os M2 (v +5,2).
- **Bolso da fileira 1: ponte a 6,2 mm de 6,9 (0,7 mm de folga).** No piso o berço da fileira 1 é um bloco de só 0,5 mm mais duas abas (0,3 mm das pontas da ponte); nas fileiras 2 / 3 / 4 o bloco sobe 2,7 / 4,7 / 7,7 mm (berços no total: 1,4 / 2,8 / 4,2 / 5,6 cm³ em 32 / 48 / 64 / 80). **A folga de 0,7 mm some com tolerância de PCB, piso e altura da fêmea; a ponte de 0,8 mm dá 1,1.**
- **Trilho de trás:** o mesmo entalhe do cabeçalho de antes (10,4 mm) em cada ponta de régua; ficam **70 %** do trilho de trás (100 % o da frente); nenhum entalhe encontra M2 ou poste (`conflicts()` vazio). Sai o entalhe de plugue sob a régua de trás (o macho do pigtail é pequeno).
- **Faixa de trás, não a da frente do esboço do Chat:** a fêmea real tem footprint de 5,2 mm de fundo (pads alternados) e a faixa da frente só tem 3,1 mm até o trilho; concordo com a eletrônica. No modelo J1 e J2 viram a fêmea (`SOCK_*`, `LINK = "E2"`, `J2_FITTED = True` em `layout_r4.py`).
- **C6 e R1 da régua** (faixa da frente) **não conflitam** com E2; conflitariam com E2b e F. LK1/LK2 e o SH J1/J2 da R5V4 saem (eletrônica).
- **Montagem (vertical, sem deslizar):** bandeja para cima → ponte no berço (machos para cima) → as duas réguas descem sobre os machos (curso 3,4 mm, 5 contatos) → M2 → tampa com as teclas. **Desmontagem:** tampa, 2 M2, régua para cima; a ponte fica no berço. **Retenção:** o M2 fixa a altura da régua e o berço a da ponte: o encaixe não sobe nem desce sozinho, só um parafuso solto o libera; a ponte pesa < 1 g. Risco: a tolerância de ±0,2 mm em x entre M2 e ponte pede entrada cônica nos machos (conferir).

### 3. Placa principal → 1ª régua (item 2): encaixe rígido é impossível; o pigtail

| Fileira | Início da régua (x) | Vão da borda da placa (77,5) | Desnível (z) | Pigtail, plugue SH → macho (modelo) |
|---|---|---|---|---|
| 1 | 89,20 | **11,7** | 0 | 16,8 mm |
| 2 | 79,95 | **2,45** | 2,0 | 8,8 mm |
| 3 | 89,20 | **11,7** | 4,0 | 16,8 mm |
| 4 | 79,95 | **2,45** | 7,0 | 8,8 mm |

- **Confirmado:** além do desnível de 0 a 7 mm e do vão de 2,45 ou 11,7 mm, a placa fica presa por 4 posts e as réguas por M2 nas bossas: duas cadeias de tolerância sem folga para um encaixe cego. Uma ponte plana só alcançaria a fileira 1 (e a ~18 mm), as fileiras 2-4 pedem degraus de 2, 4 e 7 mm. Cabo flexível é obrigatório.
- **Desenhado** (`juncao_placa_r6.png`): pigtail com plugue SH no J60x (a placa não muda) e fios soldados a um macho 1x5 que sobe na fêmea de entrada (a do J1, faixa de trás), com os fios saindo para -x. Comprimentos = corda 3D x 1,25 + 4 mm: **os ~25 mm da eletrônica fazem laço nas fileiras 2 e 4 (aparar a ~9 mm) e sobram 8 mm nas 1 e 3**; peça cortes por fileira. Nas fileiras 2 e 4 o plugue SH (x 77,4..82,4) fica sob o início da régua, como antes; a folga dele ao macho do pigtail é para medir com as peças reais.

### Pendências
- E2 depende da **fêmea H3,4 real**: altura do isolante (3,4), footprint (6,76 x 5,2 do H4,3), pino do macho (4 mm numa fêmea de 3,4: 0,6 mm de plástico fora). Se a fêmea passar de 3,6 mm a fileira 1 perde a folga: ponte de 0,8 mm ou rebaixo do piso sob o berço.
- Contrato para a eletrônica: J1/J2 da régua = fêmea 1x5 de 6,76 x 5,2 x 3,4 (u 5,9 / 68,1, v -6,9..-1,7); a **ponte** é uma PCB de 1,2 x 19,8 x 5,3 mm com dois machos a 11,8 mm entre centros. Nada muda em `pcb_envelope` nem na placa principal.

### Perguntas para o design
1. A folga de 0,7 mm sob a ponte na fileira 1 é aceitável (ou ponte de 0,8 mm, ou piso rebaixado 0,5 mm sob o berço)?
2. Pode ir o pigtail em dois comprimentos (17 mm nas fileiras 1 e 3, 9 mm nas 2 e 4)?
3. O J aceita um berço de 4 a 16 blocos pequenos no piso (1,4 a 5,6 cm³ no total), com o macho do pigtail solto?
4. A mesa FDM de 250 mm do J é inteira (sem brim largo)? Senão a tampa de 32 teclas vai para MJF/SLA.

---

## R5V4 — atendida (21 nov 2026, tarefas 1 e 2 sua parte)

Respondo à **R5V4** (SPEC do Chat). Nada foi encomendado, impresso ou montado. As seções R4V4 e anteriores abaixo valem, menos onde esta diz o contrário.
Números regeneráveis (venv CadQuery; `case/out/` fica fora do git): `case/layout_r4.py` (posições, nomes das notas) → `case/case_r4.py 0 1 2 3` (modelo + interferências; 41 / 93 / 155 / 160 s) → `estudos/r5v4.json` (resumo copiado) → `case/planta_v4.py`, `case/corte_v4.py`, `case/corte_teclado_v5.py`, `case/conector_v4.py`, `case/ligacao_v5.py`.
Imagens novas (`case/renders/`), todas com o **nome da nota em cada tecla** onde há teclas (naturais brancas, sustenidos pretos, C e F em xadrez diagonal): **`planta_geral_v4.png`** (instrumento inteiro, 32 teclas), `planta_interface_v4.png`, **`corte_chanfro_v5.png`** (quatro cortes: frente, trás, ponta direita, parede esquerda), `corte_interface_v4.png`, `ruler_conector_v4.png`, **`ligacao_elo_v5.png`** (opções A–D, planta e corte), **`ligacao_placa_v5.png`** (os 4 cabos placa → régua).

### 1. Teclado de 32 teclas (item 1)

| Fileira | Notas (conferidas contra `spec_img/teclado_32.png`) | 1ª régua começa em x |
|---|---|---|
| 1 (frente, y 74,03) | A3 C4 D#4 F#4 A4 C5 D#5 **F#5** | 89,20 |
| 2 (y 58,01) | G3 A#3 C#4 E4 G4 A#4 C#5 E5 | 79,95 |
| 3 (y 41,99) | G#3 B3 D4 F4 G#4 B4 D5 **F5** | 89,20 |
| 4 (trás, y 25,97) | **F#3** A3 C4 D#4 F#4 A4 C5 **D#5** | **79,95** (era 98,45) |

- Em `layout_r4.py`: `ROWS` (32 posições, 8 réguas cheias), `FIRST_MIDI`, `note_name()`; o modelo (`case_r4.py`) passa a usar essas linhas no lugar das da `geometria.py` (que não é minha e continua com as 28 teclas da R4V4; a eletrônica e o roteamento têm o `posicao_v4.json` e os seus próprios scripts).
- **M2 da fileira 4** = os da fileira 2 (37 e 55,5): com a régua deslocada para 79,95, o M2 de 18,5 cairia no entalhe do plugue da fileira 3 (era a mesma razão da fileira 2 na R4V4). `conflicts()` = vazio nos 4 tamanhos.
- **Postes internos** continuam nos centroides dos triângulos de 3 teclas: 5 / 8 / 11 / 14. Conferência nova (`post_checks`): distância da lâmina de 1,4 x 4,0 até a carcaça mais próxima **0,85 mm** (a lâmina fica no corredor entre teclas); distância até a junção de réguas **mínima 18,5 mm** (nenhum poste em junção); o pino redondo D5,4 fica abaixo da régua e não toca tecla. Nenhum poste mudou de lugar em relação ao critério da R4V4; os dois de parede da ponta direita passaram de x = L-8 para **L-10** (o canto interno agora é arredondado R4: L-8 ficava 2,2 mm do centro do arco).

### 2. Comprimento do case: 252 -> **240 mm**

- **Régua mais à direita termina em x = 237,0** (corpo; 237,2 nominal). A SPEC dizia ≈ 237,6: aquilo supunha réguas a 74,4 mm de passo; o passo real é 4 x 18,5 = 74,0 mm, com os 0,4 mm de vão tirados dos 0,2 mm de recuo de cada régua. As fileiras 2 e 4 acabam em 227,75.
- **Regra de margem adotada:** face interna da parede da ponta = corpo da régua + **1,0 mm** (folga da bandeja de 0,15 mm + o que a régua e a bandeja precisam para não se tocarem por dilatação e montagem); parede 2,0 mm. Logo 237,0 + 1,0 + 2,0 = **240,0 mm**. Resta, da borda do botão (raio 8,25 no último, em x 227,95 + 8,25 = 236,2) até o fim do chanfro: 1,8 mm de deck plano; até a borda externa: 3,8 mm. É pouco para apoiar um dedo; se o J quiser mais "beira" à direita, cada milímetro de comprimento custa ~0,7 cm³ de PA12 (US$ 0,18). **Módulos:** 240 + 74 x n = **314 / 388 / 462 mm** (para 48 / 64 / 80 teclas).
- Largura 100 mm, altura 24,7 (frente) e 31,7 (trás), como antes. **Com 240 mm a tampa de 32 teclas passa a caber numa mesa FDM de 250 x 250** (a de 252 não cabia); 48 teclas (314) só em MJF/SLS/SLA/FDM grande; 64 e 80 (388, 462) como já era na R4V4 (SLA/FDM grande; MJF só com partição).

### 3. Chanfro e cantos (item 2)

- **Proposta: chanfro de 2,0 x 2,0 mm a 45 graus na aresta externa de cima**, em todo o contorno (frente, trás, ponta direita e parede esquerda; a ponta direita acompanha o deck escalonado, num só loft; nos 4 cantos R6 o chanfro é um cone, sem emenda), e **1,0 x 1,0 mm na aresta de baixo** (onde a mão levanta o instrumento). Mostrados em corte em `corte_chanfro_v5.png` (A, B, C, D).
- Por que 2,0: a parede tem 2,0 mm e o telhado 2,5 (teclado) ou 2,0 (interface); com 2,0 x 2,0 sobra de material, medido na perpendicular ao chanfro até o canto da cavidade, **1,77 mm no teclado e 1,41 mm na interface** (acima do mínimo de parede de ~1 mm do MJF, a confirmar com a gráfica). Um chanfro de 3 mm deixaria 0,71 mm de telhado no ponto de menos material na interface; 1 mm é pouco para "suavizar a pegada". O chanfro termina exatamente sobre a linha da parede de 2 mm na planta (linha fina da `planta_geral_v4.png`).
- **Cantos em planta (R6 aprovado):** no modelo da R4V4 o R6 só estava desenhado na planta; agora a tampa tem R6 por fora e **R4 por dentro** e a bandeja R3,85. Consequência verificada: `tampa x placa` e as demais interferências da interface seguem **0** (folgas analíticas do canto: placa 0,22 mm; face do USB-C 0,27 e 0,30 mm). **Achado:** com o canto R6 o furo do USB-C (12,8 em y 10, de y 3,6 a 16,4) invade a parte curva da parede; o corte tinha 2,6 mm de profundidade e deixaria uma lasca de parede de 0,2 mm; passei o corte para 4,5 mm de profundidade.

### 4. Fit check em 32 / 48 / 64 / 80 teclas (volume da interseção, mm³)

| Teclas | Comprimento | Réguas | Postes int. + parede | Tampa x teclas (nominal) | Carcaça +0,5 mm | Carcaça +0,8 mm | Demais pares |
|---|---|---|---|---|---|---|---|
| 32 | 240 | 8 | 5 + 6 | **0** | 8,3 | 50,4 | **0** |
| 48 | 314 | 12 | 8 + 8 | **0** | 12,5 | 75,6 | **0** |
| 64 | 388 | 16 | 11 + 10 | **0** | 16,6 | 100,7 | **0** |
| 80 | 462 | 20 | 14 + 12 | **0** | 20,8 | 125,9 | **0** |

"Demais pares" = tampa, bandeja, réguas, grades, parafusos, teclas, cabeçalhos, plugues, pinos, sensores entre si, e a interface (placa, módulo, bateria, alto-falante, caixa, OLED, encoders, knobs) contra tampa e bandeja: tudo 0. A folga crítica continua sendo a rampa do degrau 3 (a carcaça +0,5 mm toca ~0,45 mm; é o que a coluna +0,5 mede). Cabos de 25 mm (placa) e 15 mm (elo) com folga de trilho >= 0,05 mm como na R4V4; entalhes: nenhum conflito com M2 ou poste.

### 5. Volumes e custo de impressão (MJF PA12, US$ 0,275/g, 1,01 g/cm³; só preço por grama, sem cotação)

| Teclas | Comprimento | Tampa + base | Massa | Impressão (US$) | R4V4 (28/44/60/76) |
|---|---|---|---|---|---|
| 32 | 240 | 86,7 + 73,2 = **159,9 cm³** | 161 g | **~44,4** | 46,7 (168,2 cm³) |
| 48 | 314 | 112,3 + 101,0 = 213,3 | 215 g | ~59,2 | ~61,4 |
| 64 | 388 | 137,8 + 128,8 = 266,6 | 269 g | ~74,0 | ~76,2 |
| 80 | 462 | 163,4 + 156,6 = 320,0 | 323 g | ~88,9 | ~90,9 |

O custo cresce ~**US$ 14,8 por módulo** (valores com a ligação D: entalhes de plugue do OUT tirados, a base ganhou ~1 cm³). As 4 teclas a mais não somam plástico (a tampa ganha 4 furos); o que cai é o comprimento (-12 mm). **Custo das 4 teclas e botões a mais (eletrônica):** 4 TMAG5253 + 4 botões; o número de réguas não muda (8, já eram 4 posições cada).

### 6. Ligação das réguas: opções A-D e recomendada D, com os valores reais da eletrônica

A eletrônica fechou (`ELETRONICA.md` seção R5V4; `POSICIONAMENTO.md` parte 3, seções 10-12; `pcb/regua/ligacao.json`): **D (misto)** = 4 cabos SH-6 de **25 mm** da placa ao J1 da 1ª régua + **elo soldado de 5 fios** entre réguas da mesma fileira (5 pads 1,4 x 0,7 mm em u = 2,1 e 71,9, v -0,4..3,6, fio 28-30 AWG de ~7 mm, ~1 mm abaixo da régua); o J2 da régua fica sem cabo. **Concordo com ela: coincide com a recomendação geométrica do design.** Parâmetros em `case/layout_r4.py` (`LINK = "D"`, `J2_FITTED`, `LK_*`, `link_box`) e `case/ligacao_v5.py` (`PARTS`); o modelo `case_r4.py` já usa D (cabos só placa -> régua, elos como envelope sob a junção).

**Verificação no modelo (32 / 48 / 64 / 80 teclas, todas as junções: 4 / 8 / 12 / 16):** elos x bandeja, pinos, sensores, parafusos, cabeçalhos e réguas = **0 mm³** em todos; o resto do fit check segue 0 (seção 4). Folgas: pad mais próximo ao pino da última/primeira tecla **0,5 mm**; ao trilho (|y| 4,2) **0,25 mm** (pad até y 3,95); o espaço sob a junção (v -0,9..4,0, u 70,9..76,8) está **livre de peças, de bossas e de postes**: nenhum poste cai a menos de 18,5 mm de uma junção (por construção, ver seção 1), então o poste do entalhe de ponta (u ±1) **nunca** coincide com um elo. O fio e a solda (1 mm, envelope 1,4) ficam a 5,5 a 12,5 mm acima do piso da bolsa. Opções (envelopes; `ligacao_elo_v5.png`: planta e corte de A, B, C, D na junção das réguas 1|2 da fileira 2): **A** (cabo SH nas pontas, com 100 mm de estoque) 0 mm³ contra a bandeja com os entalhes de plugue, mas a sobra de ~86 mm é o problema que a eletrônica apontou (a bolsa tem 8,4 mm de largura e 5,4 mm livres abaixo dos pinos); **B** e **D** 0; **C** (FPC 6 x 0,5, profundidade 3,9 supostos) **bate no pino da última tecla (8,4 mm³ em 32 teclas) e no cabeçalho J2 (50 mm³)**: só com conector raso (<= 3,0 mm) e J2 fora da régua.

**Os 4 cabos placa -> 1ª régua** (`ligacao_placa_v5.png`): desnível **0 / 2 / 4 / 7 mm**; distância reta 3D **17,8 / 13,1 / 18,3 / 14,7 mm**; o cabo de 25 mm sobra **7,2 / 11,9 / 6,7 / 10,3 mm** (laço livre sobre o piso entre a borda da placa e as réguas, x 78 a 95). A curva da planta tem raio livre da ordem de 5-8 mm (laço nas fileiras 1 e 3, de onde o plugue chega por trás); **não medi o raio mínimo do feixe de 5 fios**: para um cabo de 25 mm o comprimento sobra, mas se o J crimpar o cabo sob medida convém cortá-lo em ~20 mm, o que ainda deixa 2 a 7 mm de folga.

**Respostas à eletrônica (suas 5 perguntas):**
1. **Espaço sob a junção:** livre, ver acima (0 mm³ em todas as junções de 32 a 80 teclas; o poste do entalhe de ponta não cai em junção).
2. **Fileira 4 em x 79,95:** o cabo da placa (J604) segue o **mesmo contrato da fileira 2** (J1 em u 5,9, boca para trás); o plugue da fileira 4 (y 13,5-18,5, atrás da régua) **não passa sob nada**: não há fileira atrás, só o piso e o telhado (z 19,1), e a lateral é a parede (y 2). Os plugues das fileiras 1, 2 e 3 entram na bolsa da fileira de trás pelo entalhe do trilho da frente dela. M2 da fileira 4 = os da fileira 2 (37 e 55,5).
3. **Cabos de 25 mm:** o comprimento de 25 mm **serve** nas 4 fileiras (folga 6,7 a 11,9 mm); o raio do feixe não foi medido (ver acima).
4. **Retirar J601-J604 se o J escolher B:** o design **aceita**. A parede da interface (x 77,5) não depende dos conectores; sumiriam os 4 plugues da primeira régua e seus 4 entalhes, e os pads na borda direita da placa (x ~75) ficam sob o telhado da interface, sem conflito de altura. Só muda a placa principal.
5. **Janela do J2:** **a janela de plugue (entalhe de 8 mm no trilho da frente da fileira de trás) sai** (já tirada do modelo: os trilhos da frente das fileiras 2, 3 e 4 ficam com 87-89 %, 88-99 % e 87-89 % do comprimento, antes 79-87 %). O **entalhe do cabeçalho no trilho de trás da própria régua fica enquanto o J2 estiver soldado**: o corpo do cabeçalho tem 4,25 mm de altura e ocupa a faixa do trilho (y -7,5 a -1,35). Se a eletrônica **tirar o J2 do BOM** na D (a régua só aceitaria a opção A com um furo a mais), o entalhe também sai (`J2_FITTED = False`) e o trilho de trás fica inteiro (hoje 70 %).

Recomendação do design: **D**, como a eletrônica. Custo da impressão com D (menos entalhes): ver seção 5. Montagem: a solda dos elos é feita com a régua apoiada no trilho, pelo lado de baixo: o J precisa de acesso por baixo da junção antes de fechar a bandeja (aberta, a bolsa tem 6,9 a 13,9 mm de altura).

### 7. Notas, achados e pendências

1. A `geometria.py` da raiz da V4 ainda tem as 28 teclas (não é minha): o modelo, a planta e os cortes usam `layout_r4.py`. Pedido à eletrônica/gestão: atualizar `G.ROWS` se outros scripts (grade, `fab`) dependerem dela. A `grade_fab` usa `G.KEYS` (28 teclas) e **precisa ser regenerada para 32**; não é minha.
2. `fit_check.py`/`fit_extra.py` (herdados da V3) não foram tocados; o fit check da V4 é o do `case_r4.py`.
3. Chanfro e cantos só no modelo da tampa; os renders fotográficos da V4 (se houver) precisam ser refeitos depois.

### Perguntas para o design

1. **Margem da ponta direita:** 1,8 mm de deck plano depois da borda do último botão (3,8 até a borda externa) basta ao J? Se não, quanto (cada mm de comprimento custa ~US$ 0,18)?
2. **Chanfro 2,0 x 2,0 em cima e 1,0 x 1,0 embaixo:** aprovado, ou prefere raio em vez de chanfro (um raio de 2 mm deixa 2,0 mm de material no mesmo ponto, contra 1,41 mm do chanfro; é mais caro de modelar e de verificar)?
3. **J2 na régua:** a eletrônica tira o J2 do BOM na D (o entalhe de cabeçalho no trilho de trás some e o trilho volta a 100 %) ou mantém (BOM igual, aceita a opção A)?
4. A `geometria.py` e a `grade_fab` passam para 32 teclas: quem faz (eletrônica?) e quando?

---

## R4V4 — atendida (21 nov 2026, tarefas 2, 3, 1 sua parte e 6)

Respondo à **R4V4** (SPEC do Chat). Nada foi encomendado, impresso ou montado. As seções R3V4 e anteriores abaixo continuam valendo, menos onde esta diz o contrário.
Números regeneráveis (venv CadQuery; `case/out/` fica fora do git):
`case/layout_r4.py` (posições, uma só fonte) → `case/case_r4.py 0 1 2 3` (modelo + conferência de interferência, ~1 min por tamanho; escreve `case/out/r4_<n>.{stl,json}` e eu copiei o resumo para `estudos/r4v4.json`) → `case/planta_v4.py`, `case/corte_v4.py`, `case/conector_v4.py` (figuras) → `estudos/acustica.py` (Dayton).
Imagens (`case/renders/`): **`planta_geral_v4.png`** (instrumento inteiro), `planta_interface_v4.png` (zoom da interface), **`corte_interface_v4.png`** (cortes A-A em x = 37 e B-B em x = 28), `ruler_conector_v4.png` (zona do conector da régua).

### 0. Correções da eletrônica aplicadas (depois da primeira entrega)

1. **J401 com a boca para -y** (plugue em y 21,2..26,2, fios saem a y ≈ 20,7): a **fenda da tela passou para (45,45..52,45; 18,17..20,67)** e o modelo e as três figuras foram regerados com ela (a fenda é só da placa; a **janela 24 x 13 da tampa não mudou**: a fenda fica sob o módulo OLED, que cobre o corte, e a parte x 45,45..49 dela está sob a janela mas atrás do vidro). Os fios saem do plugue a y 20,7 e sobem pela fenda 0,5 mm adiante: curva aberta, sem volta de 180°. A pergunta 3 (abaixo) fica **respondida**; resta só confirmar que o cabo chega da fenda aos pinos do módulo (y 34,0), ~14 mm no plano.
2. **Grade-régua de 16,0 mm de largura** (a eletrônica: painel de 83,6 x 98): **serve**, e o modelo foi refeito com ela (0 mm³ de interferência em tampa, bandeja, réguas, teclas e parafusos, 28 teclas; o resultado dos outros tamanhos não muda, só a largura da grade).
   - **Presilhas:** a janela de 1,36 mm é na espessura (1,6 mm está dentro), não na largura; com 1,0 mm de material em volta da abertura de 14,00 as presilhas (que prendem em x, nos lados do furo) têm onde apoiar. Serve melhor que 14,0, que não deixava material.
   - **Largura x régua:** a grade fica 1,0 mm mais larga que a régua em cada lado (y ±8,0 contra ±7,0). A grade está 3,4 a 5,0 acima da régua, sem tocá-la, e não toca o trilho (que está sob a régua).
   - **Vizinhas:** entre fileiras a grade de uma fica a 16,02 - 16,0 = **0,02 mm** da outra em planta, mas em alturas diferentes (2 / 2 / 3 mm), então não há contato; e a carcaça das teclas (meia largura 7,55) fica 0,47 mm da borda da grade da fileira vizinha.
   - **Deck:** a grade (z 3,4..5,0) está a mais de 7 mm sob o deck: sem efeito. **Entalhe dos postes** na grade passou a abrir até a nova borda (y -8,1..-2,7 em vez de -7,1..-2,7).
   - **Encaixe na régua de 14:** não há encaixe físico entre as duas; a grade assenta sobre as teclas e o corpo de baixo de 5,00 mm é o espaçador. Contrato: **grade-régua 73,6 x 16,0 x 1,6**, abertura 14,00 +0,03/-0,02 em y centrada, entalhes 2,0 x 5,4 (do bordo de trás até y -2,7) em x = 0 / 18,5 / 37 / 55,5 / 74.

### 1. Decisões do item 2 aplicadas no modelo (`case_r4.py`)

| Decisão | No modelo |
|---|---|
| Grade-régua 1,6 mm FR-4, desenho próprio | 73,6 x 14 x 1,6, 4 aberturas 14,00; fica a 3,4 acima do topo da régua (ombro 5,00) |
| Deck 2,5 mm, 5 / 8 / 11 / 14 postes | idem (28 / 44 / 60 / 76). **Os postes não caem mais na junção de duas réguas** (x = 0 / 74 da régua) |
| Folga 1,0; botão a ZR + 22,8 | idem; teto da interface em z 12,6 e topo em 14,6 (nível do deck da fileira 1) |
| M2 não magnético, inserto na bossa do degrau, furo da régua Ø2,2 | **a bossa Ø6 não existia no modelo da R3V4** (só havia o trilho de 2,8 mm, e o inserto Ø3,2 vazava 0,6 mm para o bolso). Agora há bossa Ø6 do piso até a face de baixo da régua, com piloto Ø3,2 x 6. Posições por fileira: ver seção 3 |
| KS-20 Orange | envelope do STEP + desenho (R3V4) |
| USB-C na parede esquerda em y 10; módulo e H101 5,5 mm à esquerda | furo 12,8 x 7 em y 10 (z -2,9); rebaixo da bandeja em (42; 14) |

**Fit check, 28 / 44 / 60 / 76 teclas** (volume da interseção, mm³): tampa x teclas (carcaça + haste + botão apertado) 0 / 0 / 0 / 0; tampa, bandeja, grades, réguas, parafusos e teclas entre si: **0 em todos os pares e tamanhos**; tampa x carcaças com **+0,5 mm**: 6 / 10 / 15 / 19; com +0,8 mm: 38 / 63 / 88 / 113 (como na R3V4: a folga crítica continua sendo a rampa do degrau 3, ~0,45 mm). Altura externa 24,7 mm na frente e 31,7 atrás. Volume tampa + base: 28 teclas 93,6 + 74,6 = 168,2 cm³ (a R3V4 dava 174,8: sem os dois postes de parede da interface); 44: 221,2; 60: 274,2; 76: 327,1 cm³.
Interface (28 teclas): **0 mm³** entre tampa, bandeja, placa, módulo, bateria, alto-falante, caixa acústica, OLED, encoders e knobs, e entre as peças do fundo da placa (altura estimada) e a bateria, o módulo e a caixa.

### 2. Interface real: posições, folgas, achados

**O que mudou desde a planta do Chat** (`planta_geral_v4.png` contra `spec_img/planta_geral.png`):
1. **Bateria** (503450: 34 x 50 x 5): a posição da V3 (x 19,5..69,5; y 56..90) **bate no J602** (corpo do SH de 4,25 mm em x 64,3..70,95, y 53..63) e no jack IN. Nova posição, sob a placa, com o lado maior no eixo y: **x 17,4..51,4, y 40..90, z -8,1..-3,1**. Sob ela só ficam C309, C310 e C502 (0,5 a 1 mm) nos 1,9 mm entre a placa e a bateria. Os fios saem pela ponta de y 40, rumo ao J202 (64,5; 26,5): passam entre o SW403 (x ≥ 48,2) e o J202 (x ≥ 58,85), ~40 mm de fio. Ferros do berço (1,2 x 2,0) só no lado direito, no fundo e no lado esquerdo além do jack (y ≥ 66).
2. **Alto-falante Dayton CE28MB-8** (Ø28 x 4,5) em (37; 73,1), face a z 11,3 e fundo a 6,8; a caixa (retângulo 5..66 x 57,5..88,7, parte alta desde x 54,5, 0,3 < z < 12,0) é a da V3 e **cabe sem mudar**; câmara **10,41 cm³**. Os fios saem pelo furo de 1,6 mm em x 49,5 rumo aos pads do J501 (48,1..51,8; 94,45).
3. **Tela:** o módulo OLED 27,3 x 27,8 (centro em (37; 20,1), z 9,4..12,5) e a **janela 24 x 13 em (25..49; 15,5..28,5)** funcionam como na V3; os 4 postes do módulo ficam em (25,35 / 48,65; 8,2 / 32,0). A **fenda do cabo (45,45..52,45; 18,17..20,67, corrigida: ver seção 0)** fica dentro do módulo em x ≤ 50,65 (a parte até 52,45 passa da borda dele) e a ponta dos pinos do módulo (virado 180°) está em y 34,0.
4. **Knobs:** eixos em (28; 44,5) e (46; 44,5) (o pad C do encoder + 7,5 mm); chapéu a z 25,9, ponta do eixo 24,5, furo Ø9,2 no teto.
5. **Botão PROG** (SW403, fundo da placa em (52; 36)): furo Ø3,0 na bandeja, para um palito por baixo.
6. **Furos H1..H4 contra os postes da tampa:** a tampa ganha 4 postes **Ø5,4** (Ø4,6 na V3; Ø6 encostava 0,2 mm na caixa acústica em H4) com inserto M2 Ø3,2, em H1 (62; 48), H2 (74; 93), H3 (6,5; 48,5), H4 (8; 91,5), apoiados no topo da placa; a bandeja ganha bossas Ø6 por baixo (parafuso por baixo, rebaixo Ø4,4 x 2,2). **Saíram os dois postes de parede (7; 12) e (7; 88) da R3V4:** o de y 12 ficava em cima do USB-C. Os quatro postes não tocam encoders, caixa, OLED nem bateria.
7. **Quina do case: R6, não R9.** Com a quina R9 da V3 (parede interna R7) a **placa (cantos R3) invade a parede em 1,0 mm** e a quina do corpo do USB-C em y 5,5 fica 0,64 mm dentro dela. Com **R6** (interna R4) sobram **0,22 mm** da placa e **0,27 / 0,30 mm** do USB-C. O modelo 3D ainda tem quinas retas (como a R3V4: acabamento fica para depois); a conta é analítica (`layout_r4.inner_corner_clearance`). Alternativas: cantos R6,5 da placa (como na V3) ou USB-C em y 16.

**Acústica com o Dayton** (`estudos/acustica.py`: Fs 623 Hz, Qts 1,63, Vas 21,5 cm³, Sd 4,52 cm²; faixa ±10 %): caixa da R4V4 (10,4 cm³) → **fc 1 091 Hz (925-1 290), Qtc 2,85, pico +9,1 dB, F3 718 Hz**; G3 (196 Hz) sai a **-29,6 dB**, C4 -24 dB, G4 (392) -16,7 dB, C5 (523) -10,7 dB, e há **+8,5 dB em 1 kHz**. Com 12 cm³ (manta) fc só cai para 1 042 Hz; com 20 cm³, 897 Hz; sem caixa (150 cm³), 666 Hz. A caixa quase não decide: o alto-falante é sem graves por construção. Ajudaria o DSP (corte de graves em 300 Hz mais uma queda de ~8 dB perto de 1 kHz) ou um alto-falante de Fs menor.

### 3. Conector de entrada da régua (tarefa 3): achado e contrato novo

**Achado.** O SH lateral **não cabe no eixo da régua**: os pinos da tecla (2 x Ø1,7 a ±5,08 do centro, 1,5 mm abaixo da régua) e o sensor estão no eixo y = 0, e entre dois pinos vizinhos sobram só **6,6 mm** (x = 15,2..21,8, 33,7..40,3, 52,2..58,8 da régua); o cabeçalho (6,15 de fundo) mais o plugue (5,0) pedem 11 mm livres, e o plugue passa na altura dos pinos. As pontas (x 0..3,3 e 70,7..74) são menores ainda; o SH na ponta, como a eletrônica tinha desenhado, também esbarra no primeiro pino da régua seguinte. O problema não é só o J602: é a posição do conector na régua.

**Contrato novo** (`layout_r4.py`, `conector_v4.py`, `ruler_conector_v4.png`): os dois conectores (IN e OUT) ficam na **faixa de trás** da régua (y de -7,5 a -1,35 do eixo da fileira; o bolso do sensor termina em ±1,1), **boca para -y**, com a boca 0,5 mm além da borda de trás. **O plugue passa por baixo da régua da fileira seguinte**, que é mais alta (2/2/3 mm); atrás da fileira 4 não há nada.
- **IN centrado em x = 5,9 e OUT em x = 68,1**, do começo da régua (74,0 de comprimento). Pegada do cabeçalho 9,4 x 6,15 (do footprint do J601: 9,89 x 6,65 com pátio); plugue estimado 7,6 x 5,0 x 3,9, eixo de acoplamento 3,3 abaixo do topo da régua. **Altura do cabeçalho 4,25 (estimativa; conferir no desenho da JST/XYECONN):** cabe nos 6,9 mm sob a fileira 1 (sobram 1,4).
- **Zona proibida** para as outras peças do fundo da régua: x 0..11,1 e 62,9..74, y -7,5..-1,35. As demais (595, 6 capacitores, resistor) ficam **no eixo, entre os pinos, ou na faixa da frente (y +1,35..+7), fora dos furos M2**. **O 595 em SO-16 (9,9 de comprimento, ~6 entre pads) não cabe nas janelas de 6,6 mm no sentido do eixo nem na faixa de 5,3 mm: pedir TSSOP-16 (5,0 x 6,4) ou outra posição** (pergunta à eletrônica).
- **Cabo (elo) SH-SH 6 vias de medida:** **15 mm** de plugue a plugue entre réguas da mesma fileira (alça de ~3,6 mm de fundo sob a régua seguinte) e **25 mm** da placa principal à primeira régua. Um cabo pronto de 50 mm não cabe (alça de ~15 mm). Folgas mínimas do feixe (3,5 mm de largura) aos trilhos, bossas M2 e postes: **0,8 mm** (J601 → régua 1, o pior), 2,1 a 5,8 nos demais.
- **Entalhes na bandeja:** (a) no trilho de trás da própria régua, 10,4 mm sob cada cabeçalho (começam na ponta da régua, sem toco), restam **70 %** do trilho; (b) no trilho da frente da **fileira seguinte**, 8,0 mm por plugue (mais largo onde passa também o cabo da placa principal, só fileira 1 → 2, porque a régua da fileira 2 começa 9,25 mm antes). Restam 79 a 100 % do trilho da frente. A régua (flexão 0,0013 mm no meio do vão) apoia bem assim.
- **Parafusos M2 por fileira, para nenhuma bossa bater num entalhe:** fileira 1: x 18,5 e 55,5; fileira 2: **37 e 55,5**; fileiras 3 e 4: **18,5 e 37** (sempre em y +5,2). A distância entre os dois fica em 37 ou 18,5 mm: eles só prendem a régua ao degrau (ela já é guiada pelo sanduíche com a grade). Em relação à R3V4, **só muda a posição dos 2 furos Ø2,2 da régua nas fileiras 2 a 4**.
- **3D:** 0 mm³ de interferência entre cabeçalhos e plugues e a bandeja, os pinos das teclas, os sensores, as réguas e os parafusos, em 28 / 44 / 60 / 76 teclas.

**Contrato da régua atualizado** (para a eletrônica): 74,0 x 14,0 x 1,2 mm, peças só no fundo, nada no topo; 2 furos NPTH Ø2,2 em y +5,2 nos x acima (por fileira), zona livre Ø4,2 no topo e Ø6,4 no fundo; entalhes 2,0 x 4,3 na borda de trás em x = 0 / 18,5 / 37 / 55,5 / 74 como antes; 2 furos de pino Ø1,70 por tecla; **IN e OUT na faixa de trás, boca para -y**, centros em x = 5,9 e 68,1; sensor e pinos no eixo. A grade-régua muda para 73,6 x 16,0 x 1,6 (seção 0).

### 4. Planta e corte oficiais (tarefa 1, minha parte)

`planta_geral_v4.png` mostra, do modelo real: contorno do case (R6) e parede de 2 mm, placa principal e peças (cores por bloco), módulo, bateria, alto-falante e caixa, módulo OLED, janela e fenda, encoders e knobs, PROG, furos e postes da tampa (H1..H4, 5 internos, 8 de parede), as 8 réguas com teclas, os 16 parafusos M2, cabeçalhos, plugues, cabos e entalhes. `corte_interface_v4.png` corta em x = 37 (tampa, caixa, alto-falante, OLED, placa, módulo, bateria, bandeja) e em x = 28 (encoder e knob), com as alturas:

| Nível (z, 0 = topo da placa) | mm |
|---|---|
| fundo da caixa / piso da bandeja | -10,1 / -8,1 |
| bateria | -8,1..-3,1 |
| módulo (cartão) | -5,9..-1,2 (4,7 sob a placa) |
| placa | -1,2..0 |
| caixa acústica | 0,3..12,0 (câmara 1,3..10,8) |
| alto-falante | 6,8..11,3 |
| OLED (placa + vidro) | 9,4..12,5 |
| teto / topo da interface | 12,6 / 14,6 |
| bucha do encoder / ponta do eixo / topo do knob | 11,5 / 24,5 / 25,9 |

### 5. Limites desta passada (não verificado)
1. Alturas do SH, do plugue SHR-06V-S e das peças baixas da placa são **estimativas**; o módulo (4,7 sob a placa) vem do modelo da V01.
2. Sem cotação nem prova de cabo SH sob medida (15 e 25 mm).
3. Quinas R6: só conta analítica; o 3D não tem raio na planta.
4. Nada foi testado com a placa real; o corte é do modelo.

---

## R3V4 — atendida (21 nov 2026, tarefas 1, 2, 3, 7 e 8)

Respondo à **R3V4** (SPEC do Chat). As seções R1V4/R2V4 abaixo continuam valendo, menos onde esta diz o contrário. Nada foi encomendado, impresso ou montado.
Fontes: `fornecimento/gateron/KS-20TO10B050NW-Y64_Orange.pdf` (desenho de 19 out 2023, p. 5) e `KS-20T_20210922.stp`. Números regeneráveis:
`estudos/ks20_step.py` → `ks20_step.json`; `estudos/t3g.py` → `t3g.json`; `case/case_t3g.py` → `case/out/t3g_<n>.{stl,json}` (+ STEP de tampa e base em 28 e 76);
`case/render_t3g.py` → `case/renders/t3g_28_{iso,explodido,corte}.png` (o corte é só ilustrativo: o recorte do STL não fecha a face).
**Como li o desenho:** a 900 dpi, 90,0 px/mm a partir da cota 5,00; erro de leitura ±0,03 mm. Onde não há cota, marquei **(medido)** ou **(estimado)**.

### 1. KS-20 Orange: o que o desenho e o STEP dizem (tarefa 1)

| Item | Valor | Origem |
|---|---|---|
| Ombro de cima (face de baixo da carcaça de cima) | **5,00 ±0,05** do assento | cota do PDF |
| Orifício da grade / espessura recomendada | **14,00 +0,03/−0,02**, chanfro C0,2; placa **1,50 +0,01/−0,05** | PDF, "Mounting options" (p. 2) |
| Topo (colar em volta da haste) | **11,10** (±0,4 da tabela geral) | PDF; STEP: topo em z = 11,95 com assento em 0,85 = 11,10, confere |
| Carcaça de cima | 15,40 × 15,10 (abas até 16,10 ±0,4, em trechos de ~2 mm) | PDF; STEP: 16,10 × 15,06, confere |
| Corpo de baixo / sobre as pontas das presilhas | 14,00 ±0,03 / **15,00 ±0,3** (14,70 ±0,3 no outro eixo) | PDF |
| **Topo plano** (medido no STEP) | colar de ~**11,3 × 10,4 mm** na cota 11,10; ombro de ~13,5 × 12,3 a 10,6; a área de apoio real é só ~22 mm² (casca em moldura) | STEP |
| Pinos | **2 × Ø1,70 ±0,05 (furo)**, 10,16 entre centros, 2,70 ±0,1 abaixo do assento | PDF. **O diâmetro do pino continua sem cota**: no STEP não há pinos |
| Haste | cruz 4,00 × 1,30, ponta a 13,8 do assento (**medido**; o modelo R2V4 usava 14,7, estimado) | PDF |
| Curso, força, fluxo | 4,1 ±0,2; 38 ±10 gf; 102 ±15 Gs (0,3 mm) e 905 ±80 Gs (fundo, polo N) | PDF |
| Ímã no fundo | **0,3 ±0,05 mm acima da placa** com a tecla apertada | PDF, corte |

**O STEP não é do mesmo desenho que o PDF.** É uma KS-20T de 2021: tem um poste central (4,0 abaixo do assento) no lugar dos 2 pinos de Ø1,70, dois postinhos de haste a y = ±5,4 em vez da cruz central, e a parte de baixo é uma rampa lisa (de 10 a 14,44 mm) sem as presilhas discretas. **Vale o PDF** para pinos, furos e haste; o STEP serve só para o envelope da carcaça de cima, que o fit check usa. (Quem usar o STEP para a furação da régua errará: 1 poste central contra 2 furos a ±5,08.)

**Janela das presilhas (lida na vista da frente do PDF):** o flanco de cima do dente (a face que segura a grade por baixo) vai da raiz a **3,69** do assento, na parede do braço, até a ponta a **3,16**, 0,58 mm para fora (15,00 sobre as pontas). No furo de 14,00 (x = 7,00) o flanco está a **3,64**. A grade fica entre o ombro (5,00) e esse flanco:
- **janela nominal 1,36 mm** (até 1,84 se a borda tocar a ponta);
- grade de **1,50** (a recomendada): fundo a 3,50, 0,14 abaixo do flanco: o dente entra 0,15 mm sob a borda e o braço fica em mola (pré-carga de cunha, o projeto da Gateron);
- grade de **1,6** (JLC padrão, ±10 % = 1,44–1,76): fundo a 3,40, penetração 0,26, dentro da janela;
- grade de **1,2** (JLC ±0,12): fundo a 3,80, 0,11 acima da raiz: **folga vertical 0,16 mm nominal, de −0,01 a +0,33 com as tolerâncias; o dente não toca o furo**.

**Resposta à pergunta do item 2: as presilhas NÃO seguram 1,2 mm sem folga vertical.** A grade fica solta entre o dente e o ombro.

### 2. T3-G (tarefa 2)

#### 2.1 Espessura da grade: alternativas a / b / c

| | (a) painel inteiro 1,6 | **(b) grade em 1,6, desenho próprio** | (c) espuma R2V4 (plano B do J) | (d) grade 1,2 no mesmo painel |
|---|---|---|---|---|
| Presilha | dentro da janela | dentro da janela | não usa | **folga 0,16 (−0,01…+0,33)** |
| Distância ímã–sensor | **+0,4 mm**: fluxo no fundo 905 → **~657 Gs** (dipolo ajustado, 3,55 mm no fundo); sem dado do fabricante para o sensor no verso de 1,6; a calibração muda | **igual à V3** (régua 1,2) | igual | igual |
| Pedido | 1 painel | painel de régua + painel de grade, **no mesmo pedido** (2 desenhos; **estimativa** US$ 3–8 pelas grades de 2 camadas, mais a taxa de "desenho diferente" da JLC, a confirmar) | 0 | 0 (a grade vai no painel da régua) |
| Pré-carga / pilha ±1,1 | zero | zero | espuma 2–4 N | zero |
| Risco | muda o sensor | checar 1,44–1,76 na janela (ok) | MJF + espuma de PE sem silicone | tecla com 0,16–0,33 de folga e ~1° de inclinação |

O dipolo foi ajustado aos dois pontos do PDF: (d₀−0,3)/(d₀−4,1) = (905/102)^(1/3) dá 3,55 mm no fundo e 7,65 no repouso (confere com 0,3 + 1,2 + ~0,4 do sensor + ~1,5 de meio ímã). Excursão do BA3 (15 mV/mT): 1,22 V, 3,01 V no fundo, abaixo de 3,3 V.
**Recomendação do design: (b).** Não mexe na régua nem na calibração e fecha a presilha. Se o Chat preferir um só painel, o (d) funciona (a tecla assenta na régua por gravidade e atrito dos pinos; a grade só trava o plano), mas perde a rigidez "de fábrica" do sanduíche.

#### 2.2 Como a T3-G funciona (corrigindo uma premissa)

A grade **flutua nas presilhas**; ela não define a altura da tecla. A tecla assenta na régua pelo corpo de baixo (2 pinos de 2,70 em furos de Ø1,70, com 1,5 mm saindo no bolso) e a grade trava o plano e a inclinação das 4 teclas (furo de 14,00 ±0,03 contra corpo de 14,00 ±0,03, em vez da folga de 0,125 por pino). Um **espaçador rígido** entre grade e régua não serve: ±0,16 de espessura da grade viraria ±0,16 de altura de assento (a distância ímã–sensor mudaria). Por isso a fixação ao degrau **não passa pela grade**.

#### 2.3 Fixação ao degrau: escolha e justificativa

Opções: 2 apoios no deck × 2 M2 não magnéticos por régua. **Escolhi 2 M2 por régua.** Um apoio do deck sobre a grade rígida de FR-4 tem a mesma pilha de ±0,6 (RSS) da R2V4: sem elemento mole, ou fica solto ou esmaga. O parafuso não depende dessa pilha.
- M2 (A4 ou latão, cabeça panela Ø3,8 × 1,6) nos mesmos dois pontos dos antigos pinos, **(18,5; +5,2) e (55,5; +5,2)** da régua, no corredor entre teclas (4,5 mm livres no nível do assento, 3,1 acima da grade). Furo da régua **Ø2,2** (era Ø2,4).
- Rosca: inserto de latão Ø3,2 termofixado numa **bossa Ø6** do degrau, sob a régua (o degrau 1 tem 6,9 mm). A cabeça fica 1,6 acima da régua e o fundo da grade a 3,4: **folga 1,8**.
- Sem pinos na bandeja. Montagem: bandeja → réguas → parafusos (16 em 28 teclas) → blocos "grade + 4 teclas" nos pinos → tampa → botões.
- Custo: 16 parafusos + 16 insertos, **US$ 2–5 (estimativa)**. A tampa passa de 18 para 5 postes + 8 de parede = **13 parafusos** pelo fundo.

#### 2.4 Deck sem pré-carga

- **Folga nominal deck–topo: 1,0 mm** (carcaça 11,10 → fundo do deck a 12,1 sobre a régua). Tentei 0,8: no degrau 3 mm (fileira 3 → 4) restam só 0,3 entre a aba da carcaça da fileira de cima e o fundo do deck baixo; com 1,0 há 0,5. Pilha (carcaça ±0,4, régua ±0,12, impressão ±0,3 em cada peça): ±1,12 pior caso, **±0,60 RSS**; o deck toca a carcaça em ~5 % dos casos, **sem força** (não há pré-carga).
- **Deck de 2,5 mm (era 3,0).** Critério novo: o deck só precisa **não tocar a tecla com 3 N da mão** e dar boa sensação (a pré-carga de 28 teclas acabou). Grade de vigas, 28 teclas, flecha com 3 N numa tecla (mm, `estudos/t3g.json`):

| deck | 0 postes | 5 postes | 10 postes |
|---|---|---|---|
| 2,0 | 1,04 | 0,24 | 0,18 |
| **2,5** | 0,53 | **0,12** | 0,09 |
| 3,0 | 0,31 | 0,07 | 0,05 |

  Para 76 teclas, 14 postes dão 0,13 (2,5 mm). Escolhi **2,5 mm com 5 / 8 / 11 / 14 postes internos** (28 / 44 / 60 / 76), contra 3,0 mm e 10 / 16 / 22 / 28. O modelo é pessimista (a casca e as rampas enrijecem). **Se o Chat mantiver ≤ 0,05 mm a 3 N, é deck de 3,0 com 10 postes** (+0,5 mm de altura).
- **Haste do botão:** topo da cabeça em ZR + **22,8** (R2V4: 22,9; V3 fileira 1: 21,9). O botão apertado deixa a saia 0,6 mm acima do deck (0,2 na R2V4).
- **Furo Ø8 ainda vale.** Lateral: tampa × base (folga 0,15 e ±0,4 % em 250 mm, correlacionado) + furo Ø2,2 com parafuso Ø2,0 (±0,1) + grade 14,00 ±0,03 = ~0,6 pior caso, contra 1,2 mm por lado do furo Ø8 sobre a haste de Ø5,6.
- **Altura da caixa: 24,7 mm na frente e 31,7 atrás** (R2V4: 25,2 / 32,2): −0,5 mm.

#### 2.5 Fit check, 28 / 44 / 60 / 76 (`case_t3g.py`, volume da interseção, mm³)

| Par | 28 | 44 | 60 | 76 |
|---|---|---|---|---|
| tampa × teclas (carcaça + haste + botão apertado), nominal | 0 | 0 | 0 | 0 |
| tampa × grades, réguas, parafusos, base | 0 | 0 | 0 | 0 |
| base × teclas, réguas, grades, cabeças dos parafusos | 0 | 0 | 0 | 0 |
| grades × teclas, réguas, parafusos | 0 | 0 | 0 | 0 |
| tampa × carcaças com **+0,5 mm** (sem botão) | 6 | 10 | 15 | 19 |
| tampa × carcaças com +0,8 mm | 38 | 63 | 88 | 113 |

O ponto crítico é a rampa do degrau 3: **a folga até a tampa é de ~0,45 mm** para uma carcaça alta demais (o envelope é conservador: carcaça cheia de 15,4 × 15,1 até 8,6; a R2V4 usava 8,4). Todas as interseções estão na rampa da fileira 3 → 4.

#### 2.6 Flexão

Régua apoiada nos dois trilhos (bolso de 10 mm), 3 N no meio do vão: 0,0013 mm (FR-4 24 GPa, 14 × 1,2 mm). Deck: ver 2.4. Placa principal: sem mudança desde a R2V4.

#### 2.7 Volumes e custo de impressão (MJF PA12, US$ 0,275/g)

| Teclas | Comprimento | Volume tampa + base | Massa (1,01 g/cm³) | Impressão (US$) | R2V4 |
|---|---|---|---|---|---|
| 28 | 252 | 95,5 + 79,3 = **174,8 cm³** | 177 g | **~48,6** | 51,2 |
| 44 | 326 | 121,5 + 109,3 = 230,8 | 233 g | ~64,1 | ~67,6 |
| 60 | 400 | 147,4 + 139,4 = 286,8 | 290 g | ~79,7 (não cabe em MJF numa peça) | ~84 |
| 76 | 474 | 173,3 + 169,4 = 342,7 | 346 g | ~95,2 (não cabe em MJF numa peça) | ~101 |

Só o preço por grama publicado; cotação real não feita.

#### 2.8 Plano B

A espuma (R2V4) **não é necessária**: a T3-G passa nos números. Fica só de reserva se a grade de 1,6 for recusada.

### 3. KS-20 × Gateron Low Profile Magnetic Jade (tarefa 3)

**Limite da pesquisa:** não achei desenho oficial nem STEP da Low Profile Jade (a página de especificações da Gateron deu 403 e a NuPhy 429; não insisti, sem rajadas). Os dados são de lojas; o que é **estimado** está marcado.

| Critério | KS-20 Orange (desenho e STEP em mãos) | Low Profile Magnetic Jade |
|---|---|---|
| Grade | 14,00, placa 1,50 (+0,01/−0,05); janela 1,36–1,84 | "14,00 × 1,2" é premissa da SPEC: **não verificada** (sem desenho) |
| Fluxo no fundo | 905 ±80 Gs | **680 ±70 Gs** (NuPhy) |
| Curso | 4,1 ±0,2 | **3,5** (ThockKing); NuPhy: acionamento 0,1–3,3; Keeb-finder: 3,0. Fontes discordam |
| Altura | 11,10 do assento ao topo; caixa 24,7/31,7 | **menor, valor desconhecido** (estimativa: 4–5 mm a menos na caixa) |
| Haste / pinos | cruz 4,0 × 1,3; 2 pinos Ø1,70 | **desconhecidos** |
| Força | 38 ±10 gf (Orange); molas de 65 e 80 g na lista de compras | 30 ±10 gf inicial, 50 ±10 final (NuPhy); **molas pesadas: não achei** |
| Preço | já na lista da V1 | US$ 0,89 por tecla (MaxGaming); US$ 55,95 sem tamanho de pacote (NuPhy) |
| Curso útil no BA3 (dipolo, 1,2 mm, **estimado**) | excursão 815 Gs = 1,22 V; 765 Gs/mm no fundo; fundo a 3,01 V | 593 Gs = 0,89 V; 575 Gs/mm no fundo (**supondo** o mesmo ímã e a mesma distância) |
| Sensação de botão de acordeão | curso 4,1, 38 gf | curso curto ajuda, mas 30 gf é mais leve que o "peso de baian" |

Os dois dão curso útil de sobra (0,89 V e 1,22 V de excursão contra 3,3 V, sem saturar); o sensor não decide.
**Recomendação: ficar com a KS-20.** A Jade LP não tem desenho nem STEP em mãos, o encaixe do botão e a furação são desconhecidos (mudariam régua, grade, botão e caixa), a força é menor que a desejada e não achei molas pesadas. O ganho (caixa ~4–5 mm mais baixa, **estimado**) não paga o risco. Reavaliar se o J conseguir o desenho oficial.

### 4. Recomendação final (tarefa 8)

1. **T3-G com grade-régua de 1,6 mm em desenho próprio (b)**, fixação por **2 parafusos M2 por régua**, deck 2,5 mm sem pré-carga. A espuma fica de reserva.
2. **KS-20 Orange**, não a Low Profile Jade.
3. Custo (conforme o `ELETRONICA.md` §3, F2 US$ 292–371, 12–22 % abaixo da F1): a impressão cai de 51,2 para ~48,6 (28 teclas) e entram **US$ 3–8** de grades (estimativa) e **US$ 2–5** de ferragem: efeito líquido de ~+US$ 3–10 (≈ +1–3 %). A F2 continua mais barata que a F1.

### 5. Contrato com a eletrônica: régua + grade-régua

**Régua** (muda só a furação): 74,0 × 14,0 × 1,2 mm (73,6 com 0,2 de folga de cada lado na cadeia), nada no topo.
- **2 furos NPTH Ø2,2 (era Ø2,4)** em (18,5; +5,2) e (55,5; +5,2) a partir do início da régua, para M2 pan Ø3,8: zona livre de cobre e de peças Ø4,2 no topo; no **fundo, zona livre de peças Ø6,4** em volta de cada furo (a bossa do degrau encosta ali).
- 2 furos de peg Ø1,70 ±0,05 por tecla (10,16 entre centros, centrados na tecla) e pads do sensor, como na V3.
- Entalhes de 2,0 × 4,3 na borda de trás (postes), como na R2V4.

**Grade-régua** (nova): **73,6 × 14,0 × 1,6 mm** FR-4, JLCPCB 2 camadas, 1,6 mm padrão, sem componentes, sem teste elétrico.
- 4 aberturas **quadradas 14,00 +0,03/−0,02 × 14,00**, centros a 9,25 + 18,5·i do início, cantos R ≤ 0,5 (fresa da JLC), chanfro C0,2 só se a JLC aceitar.
- Os mesmos entalhes 2,0 × 4,3 nos corredores (offsets 18,5, 37 e 55,5 da borda de trás; meios-entalhes em 0 e 74): a tampa só tem 5/8/11/14 postes, mas o desenho universal basta.
- **Painel:** 5 grades por painel (~88 × 84 como o da régua), destacável por furinhos; 28 teclas usam 8 grades, **10 no pedido mínimo** (2 painéis). A montagem SMT só concerne à régua. A grade pode ir no mesmo pedido como 2º desenho (confirmar a cobrança).
- Se o Chat escolher a opção (d) (1,2 mm no painel da régua): o desenho da grade é o mesmo, com 1,2 mm de espessura, e entra no painel da régua.

### 6. Perguntas para o design (R3V4)

1. **Grade 1,6 mm em desenho próprio (b)** ou 1,2 mm no painel da régua (d, com 0,16 mm de folga)? Recomendo o (b).
2. **Deck 2,5 mm com 5 postes (0,12 mm a 3 N, modelo pessimista)** ou 3,0 mm com 10 postes (0,05)? Recomendo 2,5; o Chat fixa o critério de rigidez.
3. **Folga deck–carcaça de 1,0 mm** (a rampa do degrau 3 pede) e **cabeça do botão a ZR + 22,8**: aprovado?
4. **M2 por régua** (16 em 28 teclas, nos pontos dos antigos pinos), furo da régua Ø2,4 → Ø2,2: aprovado?
5. **O STEP da KS-20T não é a Orange**: o J pode pedir à Gateron o STEP da KS-20TO10B050NW-Y64? Falta também o diâmetro do pino (estimado 1,55–1,60).
6. **Low Profile Jade:** o J consegue desenho, STEP e molas pesadas? Sem isso a recomendação é a KS-20.
7. **Para a eletrônica:** o `ELETRONICA.md` fala em "BA3 em ±60 mT" (linha 123) e 15 mV/mT (linha 90): com 1,65 V a faixa chega a ±110 mT. A KS-20 vai a 90 mT no fundo; confirmar a faixa do BA3, senão o fim do curso satura.
8. O corte `t3g_28_corte.png` é pobre (mostra os botões empilhados); um corte limpo fica para a passada de fechamento.

---

## Passada anterior (R1V4/R2V4)

Responde à **R1V4** (tarefas D1 e D4) e à **R2V4** (D2 só para a F2, D3). Primeira passada, 21 nov 2026. Nada foi encomendado, impresso ou montado.
**A tarefa 12 (tabela de custo e riscos da F2 × F1 e "Perguntas para o design") não foi feita:** ela espera os números da eletrônica (segunda passada).
No fim há só uma lista de **pendências e dúvidas desta passada**, que não substitui aquela seção.

Arquivos (tudo em `student_v04/`):

| Arquivo | O que é |
|---|---|
| `case/case_f2.py` | modelo CadQuery paramétrico da F2 (`python case_f2.py 0 1 2 3` = 28/44/60/76 teclas); faz o fit check de interferência |
| `case/render_f2.py` | imagens em `case/renders/f2_*.png` |
| `case/out/f2_<n>_{tampa,base,reguas,teclas,espuma}.stl` + `f2_<n>.json` | modelos (STEP só de tampa e base para 28 e 76) |
| `estudos/t3_deck.py` → `t3_deck.json` | pilha de tolerâncias, folga dos pinos, flexão do deck, parede |
| `estudos/ks20_desenho.py` → `case/renders/ks20_pilha_T3.png` | desenho dimensional da KS-20 na pilha T3 |

Quadro de referência: x para a direita, y_spec para o jogador (fileira 1 na frente), **z = 0 no topo da placa principal = topo da régua da fileira 1**. O modelo é espelhado em y na exportação (destro).

---

## D1 — KS-20 e detalhamento da T3 (R1V4 §3)

### D1.1 Desenho dimensional

Fonte: desenho oficial da Gateron **KS-20TF10B045NW-X72** (2023-09-13), baixado do site da Gateron (PDF de 5 páginas, p. 5 = desenho cotado). **Não achei o desenho do modelo Orange** (KS-20 Orange 38 gf); o corpo é o da mesma família KS-20T, e o Orange só muda mola e cor. Conferir o desenho do Orange antes do portão (ver pendências).

| Item | Valor (mm) | Observação |
|---|---|---|
| Carcaça de cima | 15,40 × 15,10 | 15,40 ao longo da fileira (pinos esquerda-direita) |
| Do assento (placa) até o topo da carcaça | **11,10** | tolerância **não indicada** → tabela geral do desenho: >10~30 = **±0,4** |
| Face de apoio da placa de aço | 5,00 ±0,05 acima do assento | essa face **aponta para baixo**: não serve de ombro para a tampa |
| Cobertura afunilada | 2,70 ±0,1 de altura | a largura do topo plano **não é cotada** (estimei 11,4) |
| Corpo de baixo | 14,00 ±0,05 (outro eixo 14,70 ±0,3) | furo de placa recomendado 14,00 +0,03/−0,02 |
| Furos dos pinos na PCB | 2 × Ø1,70 ±0,05, 10,16 entre centros | pads do sensor 0,8 × 0,8 a 1,27 de passo |
| Diâmetro do pino | não cotado | estimado 1,55–1,60 |
| Haste (cruz) | 4,00 +0,05/−0,10 × 1,30 ±0,04 | |
| Curso total | 4,10 ±0,2 (4,10 ±0,05 no corte) | |
| Fluxo do ímã (polo N) | 102 ±15 Gs (início), 905 ±80 Gs (fundo) | a mesma calibração da V3 vale, pois a distância ímã-sensor não muda (régua de 1,2 mm, sensor no verso, como na V3) |
| Força inicial | 30 ±10 gf (X72) | a Orange é 38 gf: só a mola |

Figura: `case/renders/ks20_pilha_T3.png` (corte pela largura da fileira 1 com a pilha toda).

### D1.2 Onde a tampa apoia na tecla (e a primeira surpresa)

O desenho mostra que **a KS-20 não tem ombro voltado para cima**: o único "ombro" cotado (5,00) é a face de baixo da carcaça de cima, onde a placa de aço assenta. A única superfície que a tampa alcança por cima é o **topo plano da carcaça (11,10)**, em volta da abertura da haste. Contato: um anel entre o furo Ø8,0 do deck e a borda do topo (estimado 11,4 de largura), com 4 apoios de 11 × 11 mm no total ≈ 66 mm² (a espuma abaixo). Com o furo Ø8 sobra ~1,7 mm de anel por lado (não cotado: ver pendências).

### D1.3 Pilha vertical: o número que muda a T3

Cadeia entre o plano de encaixe tampa×base (face de cima da bandeja = fundo dos postes) e o fundo do deck: degrau da base + régua (1,2) + carcaça (11,10) + folga/espuma. Tolerâncias publicadas (`t3_deck.py`):

| Caso | Pior caso | RSS |
|---|---|---|
| Publicada: carcaça ±0,4 (tabela do desenho), impressão ±0,3 (MJF/SLS/FDM ≤100 mm), régua ±0,12 | **±1,12 mm** | ±0,60 |
| SLA 8001 (impressão ±0,2) | ±0,92 | ±0,50 |
| "Típico" suposto: carcaça ±0,1, impressão ±0,15 (**não publicado**) | ±0,52 | ±0,26 |

**Achado (afeta a T3 como a SPEC a descreveu):** nervuras de esmagamento rígidas **não aguentam essa janela**. Uma nervura impressa de PA12 só amassa com ~30 N (ponta de 0,2 × 3 mm, limite de 48 MPa); a janela publicada de 1,1 mm exigiria que algumas teclas fossem esmagadas e outras ficassem soltas. A T3 só fecha com **um elemento que dê 2,2 mm de curso mantendo força pequena**.

**Proposta (para a F2):** **anel de espuma** de PE (ou EVA) de célula fechada **sem silicone** (a Gateron avisa sobre siloxano), 2,0 mm livre → 1,0 mm comprimido (50%), recortado, entre o topo da carcaça e o fundo do deck. É 1 folha de ~US$ 3–8 recortada a laser (estimativa, não cotada), ou 28 anéis colados no deck. Resultados:
- a espuma absorve a janela publicada (±0,6 RSS) entre 20% e 80% de compressão; no pior caso absoluto (±1,12) o deck pode tocar a carcaça: **risco aceito**, com o remédio de trocar a espessura da espuma (ou o degrau por 0,3 mm) depois de medir;
- pré-carga por tecla **2–4 N (estimada**: PE 33 kg/m³, 50%, 66 mm²; sem medida). Basta 0,21 N para segurar a tecla (cálculo da amarração abaixo);
- verificado no modelo: **0 mm³ de interferência** entre a tampa e as 28 carcaças + botões apertados, no nominal e com todas as carcaças 0,5 mm mais altas; a interferência só começa com +0,8…1,0 mm (rampa do degrau 4);
- se a espuma não for aceita, o plano B é a **T1** (abaixo).

### D1.4 Folga lateral e inclinação

- Furo do pino Ø1,70 ±0,05, mais a tolerância de furação não metalizada da JLCPCB (±0,05, a conferir): furo máximo 1,80. Com pino estimado 1,55: folga radial até **0,125 mm** por pino, ou 0,25 mm em x e 0,125 em y, e giro de até **1,4°** no plano. É o jogo da tecla se **nada** a prender; com a pré-carga o giro fica por atrito, e a posição lateral que importa é a da haste no furo do deck (Ø8, folga 1,2 mm por lado ante o tubo Ø5,6 do botão).
- **Inclinação a 3 N na borda do botão:** o botão tem 8 mm de raio e a base da tecla 7 mm; 3 N sobre a borda fica 1 mm fora do apoio, o que pede uma amarração de **3 × 1 / 14 = 0,21 N**. A pré-carga de 2–4 N cobre 10 vezes: **a carcaça não levanta nem tomba**. O que sobra de inclinação é o jogo do **tubo do botão na haste** (não é da T3).
- Posição lateral acumulada em 250 mm: a tolerância publicada é ±0,4% (**±1,0 mm** em MJF/SLS/FDM; SLA 0,3% = ±0,75). Isso passa da folga de 0,7 que o furo Ø7 tinha, então o furo ficou em **Ø8,0**. Os furos da tampa e os pinos da base vêm do mesmo processo e do mesmo lote, então o erro real é correlacionado (e menor).

### D1.5 Rigidez do deck (`estudos/t3_deck.py`, grelha de vigas, malha 4 mm, PA12 E = 1,8 GPa da JLC3DP, líquida dos furos Ø8)

Pré-carga de **1 N por tecla** (a espuma real dá 2–4, e o efeito é linear: multiplique). O deck é apoiado em todo o contorno pelas paredes (que são pregadas aos pontos de fixação, ver D4) e por postes internos nos triângulos entre teclas.

| 28 teclas | postes internos | flecha máx. com pré-carga | com 3 N numa tecla (no deck) |
|---|---|---|---|
| deck **2 mm** | 0 | 5,5 mm | 1,04 |
| deck 2 mm | 10 | 0,11 | 0,18 |
| deck **3 mm** | 0 | 1,6 | 0,31 |
| **deck 3 mm** | **10** | **0,032 mm** | **0,053 mm** |
| deck 3 mm | 19 (todos) | 0,016 | 0,033 |

Para 76 teclas (malha 6 mm): deck 3 mm com 28 postes internos, 0,030 mm e 0,053 mm. **O deck de 3 mm com um poste a cada ~2,7 teclas cumpre a meta de 0,05 mm** (3 N: 0,053, no limite). O perfil escalonado **não ajuda** (os 7 mm de desnível em 100 mm de vão não fazem arco: 233 mm de flecha de 1D contra 239 mm da placa plana, só como confirmação de que o deck precisa dos postes internos).

Consequência de forma: **deck 3 mm** (não 2) e, para manter o curso do botão, a haste do botão único ficou **1 mm mais longa** que a da V3 (topo da cabeça em ZR + 22,9; a V3 tinha 21,9 / 23,9 / 25,9 / 28,9 com hastes diferentes). Isso é uma mudança que o Chat precisa aprovar.

### D1.6 Montagem em casa e troca de tecla

1. Bandeja sobre a mesa; réguas (já ligadas em cadeia com a placa principal) nos pinos de 2 mm; ver Encaixe.
2. Teclas nos furos das réguas: os pinos de plástico só entram, **não há solda** (os pads de 0,8 do desenho são do sensor/LED).
3. Anéis de espuma sobre o topo de cada tecla (ou já colados no deck).
4. Tampa de cima para baixo sobre as hastes; os postes passam pelos entalhes das réguas.
5. Virar o conjunto, 18 parafusos M2 pelo fundo (D4). Depois, os botões, de cima, no encaixe da haste.

**Trocar uma tecla:** abrir os 18 parafusos, levantar a tampa, puxar a tecla da régua: ~5 min. Os botões saem sem abrir (puxar).

### D1.7 Se algum número falhar: T1

A T1 (grade de FR-4 1,6 mm) na F2 seria **4 grades, uma por degrau** (fileiras de 7–8 teclas), pedidas à JLCPCB como um painel só. Estimativa (não cotada): US$ 10–20 por 5 grades de ~150 × 17 mm (a taxa de engenharia domina) e, como a KS-20 **não tem ombro voltado para cima**, a grade teria de ser o apoio de 5,00 mm por baixo da carcaça de cima: a tecla encaixaria na grade e a grade ficaria 5 mm acima do assento (o que aprofunda o bolso e muda as alturas dos degraus). A T1 elimina a espuma e a janela de 2,2 mm, e custa as 4 grades e a altura. **Plano B** se o teste da espuma falhar.

---

## D4 — Fixação do case compatível com a T3 (R1V4 §8)

Premissas: a pré-carga total é pequena (28 teclas × 2–4 N = 56–110 N, ou seja ~5 N por ponto com 18 pontos), então **o número de pontos é decidido pela flecha do deck e da parede, não pela força**.

**Achado de geometria:** um poste entre teclas **não cabe** como cilindro: o corredor entre duas teclas da mesma fileira tem **18,5 − 15,4 = 3,1 mm** em x (e 0,92 mm em y entre fileiras). O poste usa, então, **uma lâmina de 1,4 mm** (x) × 4 mm (y) no corredor, descendo da tampa, e só **abaixo da régua** engrossa para uma bossa redonda Ø5 com o inserto. A régua leva um **entalhe de 2,0 × 5,2 mm** na borda de trás, nas posições 0 / 18,5 / 37 / 55,5 mm do começo (as 4 posições de cada régua; a posição 0 é meio entalhe em cada régua vizinha). Só os triângulos "do tipo a" (duas teclas da fileira r, uma da r+1) são usados: ficam sempre na borda de trás das réguas das fileiras 1–3 (19 posições livres para 28 teclas; usei 10).

| | S1 — parafuso M2 + inserto | S2 — encaixes impressos | S3 — só borda |
|---|---|---|---|
| Como | inserto de latão Ø3,2 termo-fixado na bossa (6 mm), parafuso M2×8 (latão ou A4; **não magnético**) pelo fundo da bandeja (rebaixo Ø4,2 × 1,0) | lâmina do poste termina em gancho (farpa) que entra num furo da bandeja; 4 parafusos nos cantos | parafusos só nas paredes (12) |
| Pontos (28 teclas) | **10 internos (triângulos) + 8 de parede = 18 parafusos** (de parede: 6 nas paredes longas a ≤80 mm, 2 do lado da interface) | 10 internos de encaixe + 14 de parede de encaixe + 4 parafusos | 12 de parede |
| Escala 44 / 60 / 76 | 16+10 / 22+12 / 28+14 | idem | 12+ |
| Flecha do deck 3 mm (pré-carga 1 N/tecla) | **0,032 mm** | igual (ponto é ponto, com mais folga do gancho: +0,1 mm a conferir) | **1,6 mm** (inaceitável) |
| Flecha da parede entre pontos (2 × 20 mm, 0,22 N/mm) | 80 mm: 0,049 mm; 60 mm: 0,016 | idem | 120 mm: 0,25 mm |
| Custo de fixador (estimativa) | 18 insertos ~US$ 0,05–0,3 + 18 parafusos ~US$ 0,05–0,15: **US$ 2–8** | quase 0 | ~US$ 1–4 |
| Montagem em casa | ~25 min (18 inserções com ferro + 18 parafusos) | ~5 min, sem ferramenta | ~10 min |
| Reabertura | fácil (muitas vezes) | desgasta a farpa de PA12 (fluência, centenas de ciclos?) | fácil |
| Risco | inserto em furo ±0,3 da MJF (furo piloto Ø3,2 pede Ø3,0 de projeto + conferência) | tolerância ±0,3 do encaixe, fluência da farpa com pré-carga constante | o deck infla: reprovado |

**Recomendação do design: S1** (parafuso + inserto) para o protótipo: é a única que fecha 0,05 mm com folga e se reabre sem desgaste; **S2 é a variante barata para a série** se a farpa passar num teste de fluência. S3 está reprovada pelos números.

Nenhum parafuso aparece na área do teclado (todos entram pelo fundo; a face de cima só tem os furos Ø8 das hastes).

---

## D2 — Case conceitual da F2 (R2V4)

Sem acabamento, sem logo, sem letreiros (decisão 16): a interface é um envelope; o que se modelou são os degraus, as réguas, o deck e as fixações.

### D2.1 Arquitetura

- **Base (bandeja):** piso 2,0 mm, **dois trilhos por fileira** (cada trilho de 2,8 mm, a |y| = 4,2…7,0 do centro da fileira (régua de 14,0)) com altura 6,9 / 8,9 / 10,9 / 13,9 mm acima do piso (degraus de 0 / 2 / 4 / 7 mm da régua; o topo do trilho é o fundo da régua). Entre os trilhos fica um **bolso contínuo** de 10 mm de largura, aberto até a interface (pelo bolso passam o cabo e as pontas dos pinos da tecla). Dois **pinos Ø2,0 × 2,5** por régua, no trilho da frente (y +5,2), nos corredores entre teclas (início + 18,5 e + 55,5 mm), guiam a régua em furos Ø2,4 (a localização é do pino, ±0,4 mm; o furo Ø8 do deck absorve). **Zero parafuso na área do teclado.**
- **Réguas:** 74,0 × 14,0 × 1,2 mm (4 posições a 18,5), 0,4 mm de folga entre uma e outra na cadeia. 28 teclas = 8 réguas (32 posições, 4 vazias: fileiras 7/8/7/6), +4 réguas por módulo: 44 = 12, 60 = 16, 76 = 20. Sensores/registrador/conector ficam **no verso**, no bolso (altura livre sob a régua: 6,9 mm na fileira 1; nenhuma peça no topo).
- **Tampa:** paredes de 2,0 mm, **deck de 3,0 mm escalonado** (faixas planas de cada fileira ligadas por **rampas de 60°** de 2 / 2 / 3 mm, porque com 45° a rampa do degrau 3 mm batia na carcaça da fileira de cima), furos Ø8 por tecla, telhado de interface plano a 15,1 mm (= nível do deck da fileira 1). Postes: lâmina no corredor + bossa Ø5 abaixo da régua; bossas de parede Ø6.
- **Placa principal:** só na área de interface (x < 79 mm), envelope assumido 75 × 95 mm, topo em z = 0. Cabos de cada fileira correm no bolso até o primeiro conector da régua. *(Tamanho e posição da placa são da eletrônica; aqui é só o espaço.)*
- **Largura constante:** 100 mm; paredes externas verticais. Altura externa: **25,2 mm na frente, 32,2 mm atrás** (a V3 tinha 24,6 mm): o deck sobe 7 mm no total, como a escada dos degraus. As rampas e as bordas vivas do deck na mão do jogador (hoje sem raio nem chanfro) ficam para a fase de acabamento.

Imagens (`case/renders/`): `f2_28_iso.png` (fechada), `f2_28_explodido.png`, `f2_28_corte_x.png` (corte x = 107,7 mm: botões das fileiras 4 e 2 pelo meio), `f2_28_corte_y.png` (corte pela fileira 3), `f2_28_planta_base.png` (bandeja + réguas + postes), `f2_tamanhos.png` (28/44/60/76, vista de cima), `f2_76_iso.png`.

### D2.2 Fit check (modelo, 28 e 76 teclas, mesmo resultado em 44 e 60)

Interferência (volume da interseção, mm³), `case_f2.py`:

| Par | 28 / 44 / 60 / 76 |
|---|---|
| tampa × teclas (carcaça + haste + botão apertado), nominal | 0 / 0 / 0 / 0 |
| tampa × teclas com carcaça 0,5 mm mais alta | 0 / 0 / 0 / 0 (a interferência aparece em +0,8 a +1,0 mm) |
| base × teclas, base × réguas, tampa × réguas, tampa × base | 0 |

Folgas de projeto: botão apertado fica 0,2 mm acima do deck (a rampa começa 8,6 mm atrás do centro da fileira inferior, fora do raio da saia, 8,25); a espuma comprimida deixa 1,0 mm entre carcaça e deck. A espuma não entra na interferência (é o elemento que amassa).

### D2.3 Tamanho para 28 / 44 / 60 / 76

Cada módulo de +16 acrescenta 4 colunas (74 mm) e **4 réguas**. Largura 100 mm, altura 25,2/32,2 mm em todos.

| Teclas | Comprimento | Réguas | Postes internos + de parede | Volume tampa + base | Massa PA12 (1,01 g/cm³) |
|---|---|---|---|---|---|
| 28 | 252 mm | 8 | 10 + 8 | 104,7 + 79,4 = **184,1 cm³** | 186 g |
| 44 | 326 mm | 12 | 16 + 10 | 134,6 + 109,4 = **244,0 cm³** | 246 g |
| 60 | 400 mm | 16 | 22 + 12 | 164,4 + 139,5 = **303,9 cm³** | 307 g |
| 76 | 474 mm | 20 | 28 + 14 | 194,2 + 169,5 = **363,7 cm³** | 367 g |

O custo cresce ~ **US$ 17 por módulo** (MJF, 60 cm³ de plástico por módulo + 4 réguas). O piso de 2 mm (~48 cm³ em 28 teclas) é um terço da base: é onde dá para economizar depois (nervuras).

### D2.4 Partições possíveis (decisão 17)

| | Partição | Parede sem emenda | Observação |
|---|---|---|---|
| **A (modelada)** | **tampa** (paredes + deck + postes) e **bandeja** (piso + degraus) | **sim**: a única emenda é a linha do fundo, rente à mesa | igual à V3; a bandeja entra por baixo da tampa, 0,15 mm de folga por lado; parafusos de baixo; o deck imprime na orientação "com o aro para baixo" (SLA/FDM: suportes só **dentro** do telhado, escondidos; MJF não tem suporte) |
| B | **corpo** (piso + paredes + degraus) e **deck/tampa plana** com os postes | não: emenda em volta no topo do deck, onde a mão encosta | a bandeja não é mais removível; só vale se a tampa imprimir de cabeça para baixo sem suporte, o que o deck escalonado impede (as faixas em alturas diferentes pedem suporte na face de cima) |
| C | A, mais **corte em x** para 60 e 76 teclas (MJF tem 370 × 276 mm) | quase | o corte tem de passar pelos corredores entre teclas, mas os corredores de fileiras vizinhas estão deslocados meio passo: a emenda é **em zigue-zague** por faixa (uma emenda por fileira), com meia-lapa e 2 parafusos de cada lado. Em 60 teclas: corte em x ≈ 326 (peças de 326 e 74+) |

**O que cabe numa peça** (volume de impressão da JLC3DP, 21 nov 2026; `help/article/3d-printing-design-guideline`):

| Processo / material | Volume máx. (mm) | 28 | 44 | 60 | 76 |
|---|---|---|---|---|---|
| SLA 8001, Grey, JLC Black e outras | 780 × 780 × 530 | sim | sim | sim | sim |
| MJF PA12 / PA12S / PA11 | 370 × 276 × 360 | sim | sim (326) | **não** (400; na diagonal da mesa não cabe: 400 × 100 não cabe em 370 × 276) | **não** |
| SLS 3201PA-F / 3301PA | 350 × 350 × 400 | sim | sim (326) | não | não |
| FDM ABS / ASA / PA12-CF | 580 × 480 × 480 | sim | sim | sim | sim (474) |
| FDM PLA-P / TPU | 250 × 250 × 300 | não (252) | não | não | não |

Uma tampa de 252 mm **não cabe** em PLA FDM (250). Sinal para 60 e 76 teclas: SLA ou ABS (uma peça), ou MJF com a partição C.

---

## D3 — Cotação e tolerância por processo (JLC3DP)

**Limite desta rodada:** a cotação instantânea da JLC3DP exige envio do arquivo e (as páginas avisaram) conta; **não consegui cotar** os STL. Só um preço por unidade é **publicado**: **MJF PA12 a US$ 0,275/g** (depois do corte de 21,5% de dez 2025; sem imposto). Para SLA, SLS e FDM a JLC3DP só publica "a partir de US$ 0,30–1,00" por peça (o mínimo). Os valores abaixo são **estimativas** para ordem de grandeza (assinaladas), e o J pode fazer a cotação real enviando `case/out/f2_28_tampa.stl` e `f2_28_base.stl` (já espelhados, em mm; 105 e 79 cm³) em jlc3dp.com/3d-printing-quote.

### D3.1 Tolerâncias publicadas e limites de projeto

| Processo (material) | Tolerância do modelo | Furos | Parede mín. (100 × 100 / 200 × 200) | Pino mín. | Fluência / observação |
|---|---|---|---|---|---|
| MJF (PA12) | ±0,3 mm até 100 mm; **±0,4%** acima | ±0,3 | 2,0 / 2,0 mm | Ø2,0 (altura 2–4) | PA12: módulo 1,8 GPa, resistência 48 MPa; fluência baixa à pré-carga de 2–4 N em 18 pontos |
| SLA (8001 e outras) | ±0,2 mm até 100; ±0,3% acima; ±0,15 após 1–3 dias | ±0,3 | 1,5 / 2,0 | Ø1,0 | resina: módulo 2,1 GPa, mais frágil; ótima superfície no deck |
| SLS (3201PA-F) | ±0,3 / 0,4% | ±0,3 | 2,0 / 2,0 | Ø2,0 | parecido com MJF |
| FDM (ABS, PLA-P) | ±0,3 / 0,4% | ±0,4 | 2,0 / 2,5 | Ø2,0 | camadas e empenamento em peças planas de 250+ mm; **fora** da T3 por tolerância e acabamento da face do dedo |

Checagem das peças do modelo com esses limites: paredes 2,0 mm ✓; lâminas dos postes 1,4 mm (parede mínima 1,0–1,5: ✓ no limite); pinos Ø2,0 × 2,5 (limite Ø2,0 e 2–4 mm: ✓ no limite); furos de fixação Ø2,4 ✓; furo piloto Ø3,2 ±0,3 (o inserto pede 3,0 a 3,2: conferir); abertura de saída do pó ou da resina: a tampa é aberta embaixo ✓; a bandeja é aberta ✓.

Para a T3 (tolerância de pilha ±0,6 RSS): **nenhum** processo da JLC3DP muda o resultado de forma decisiva (SLA melhora de 0,60 para 0,50); a espuma é que resolve.

### D3.2 Preço por peça (28 teclas) e por tamanho

| | Volume (cm³) | MJF PA12 **publicado** (US$ 0,275/g × 1,01 g/cm³) | SLA 8001 (**estimativa**, sem preço publicado) | FDM ABS (**estimativa**) |
|---|---|---|---|---|
| Tampa 28 | 104,7 | **29,1** | ~ 10–25 | ~ 8–20 |
| Bandeja 28 | 79,4 | **22,1** | ~ 8–20 | ~ 6–15 |
| **Total 28** | 184,1 | **51,2** | ~ 18–45 | ~ 14–35 |
| Total 44 | 244,0 | 67,8 | ~ 24–60 | ~ 18–45 |
| Total 60 (MJF: 2 peças por parte) | 303,9 | 84,4 | ~ 30–75 | ~ 23–55 |
| Total 76 | 363,7 | 101,0 | ~ 36–90 | ~ 27–65 |

As colunas SLA e FDM são **chute de ordem de grandeza** (US$ 0,10–0,25 por cm³ e US$ 0,075–0,2 por cm³ de volume final, respectivamente): sem preço publicado, **não valem para decisão**. Frete e imposto não entram.

**O mais barato que atende a T3 e à fixação:** pelos números **publicados**, **MJF PA12 a US$ ~51** (28 teclas) é o único com preço firme, cabe numa peça até 44 teclas e tolera a pré-carga da espuma; SLA 8001 pode sair mais barato (e é o melhor em tolerância, ±0,2) mas depende da cotação. **Se a cotação de SLA ficar abaixo de ~US$ 51 para o mesmo par de STL, SLA vence** (a decisão 15 pede ≥15% de vantagem total com frete para outro fornecedor; entre processos da própria JLC3DP, vale o menor). Sem acabamento, sem pós-processo (spray custa à parte, não incluído).

**Sugestões para baixar o volume** (não aplicadas, por serem fase B): piso de 2 mm com nervuras de 1,2 mm no lugar de placa cheia (−30% do piso ≈ −US$ 6 por bandeja); trilhos vazados.

---

## Riscos aceitos e o que não pôde ser verificado

1. **Desenho do KS-20 Orange** não encontrado; usei o do X72 (mesma família). **Largura do topo plano** e **diâmetro do pino** não são cotados (estimei 11,4 e 1,55–1,60). Se o topo plano for menor, a espuma toca a rampa do cone, com mais força lateral.
2. **11,10 sem tolerância no desenho:** adotei o ±0,4 da tabela geral. Se a peça real for ±0,1, a pilha cai a ±0,26 e a espuma fica folgada.
3. **Espuma:** a rigidez (2–4 N por tecla) é **estimada**; falta medir uma amostra (um recorte de PE 33 kg/m³, 2 mm). Sem teste não dá para afirmar a pré-carga nem a fluência da espuma.
4. **MJF/SLA não foram cotados** (sem conta). Só o MJF tem preço publicado.
5. **Fluência do PA12 sob a pré-carga** dos 18 pontos: calculada só como pequena (5 N por ponto); não medida.
6. **Flexão do deck** é um modelo de grelha plana; o deck real tem as rampas e os postes, então os números são de ordem. A 3 N numa tecla, 0,053 mm ficou **3 µm acima** da meta de 0,05 (aceito).
7. **Geometria da interface** não foi modelada (envelope). A altura de 15,1 mm do telhado e a posição do limite (x = 79) são provisórias.
8. A interpretação de que o 11,10 e o 5,00 do desenho partem do assento (e não de baixo dos pinos) vem do `keycap.py` da V1 e da figura; **dois valores de partida** (11,10 e 5,00) precisam da conferência com o desenho do Orange.

## Mudanças que a eletrônica precisa saber (contrato das réguas, não houve `pcb_envelope.json` novo)

- Régua: **74,0 × 14,0 × 1,2 mm** (15,6 na primeira passada; ver 12.2), 4 posições a 18,5 mm (centros em 9,25 + 18,5k); folga de 0,2 mm por ponta.
- **2 furos Ø2,4** (não metalizados) a (18,5; +5,2) e (55,5; +5,2) do início da régua e do centro da fileira, y_spec para o jogador (borda da frente).
- **Entalhes** (reservar sem cobre/componente) de 2,0 × 4,3 mm na **borda de trás**, abertos para a borda, em x = 0 (meio entalhe em cada ponta de régua), 18,5, 37,0 e 55,5 mm. Só as réguas das fileiras 1–3 usam (a 4 não tem); réguas "universais" levam todos.
- Bolso embaixo (verso): largura livre de 8,4 mm no meio (|y| < 4,2), altura **6,9 mm** (fileira 1) a 13,9 mm; sensor no verso a (centro, 0), com as pontas dos pinos da tecla pendendo no bolso (~2 mm).
- Distância ímã-sensor igual à da V3 (régua 1,2 mm, sensor no verso).
- Chegada dos cabos à placa principal: pelo bolso, sem passar por baixo do piso.

## Pendências e dúvidas desta passada (não é a tabela da tarefa 12)

- Baixar o desenho do **KS-20 Orange** (ou pedir ao J a foto da folha) e conferir 11,10, 5,00, o topo plano e o pino.
- **Mudanças que dependem do Chat:** (a) T3 com **espuma** em vez de nervuras de esmagamento (a pilha ±1,1 mm não fecha com nervuras); (b) **deck de 3 mm** e **haste do botão +1 mm** (topo da cabeça em ZR + 22,9); (c) **rampas de 60°**; (d) caixa com altura 25,2 / 32,2 mm.
- Cotar na JLC3DP: `f2_28_tampa.stl` + `f2_28_base.stl` em MJF PA12 e em SLA 8001; comparar com a tabela D3.2.
- Segunda passada: tabela de custo e riscos da F2 × F1 e "Perguntas para o design" (tarefa 12), com os números da eletrônica (régua, painel, conectores).

---

## Tarefa 12 — custo e riscos da F2 (F1 só de referência), R2V4 item 5

Base: `ELETRONICA.md` (tabela 3.2, 28 teclas, pedido mínimo, baixo–alto). O número do design entra no lugar da faixa da V3.

### 12.1 Custo (US$, 28 teclas)

| | F1 (referência, V3) | F2 (eletrônica, faixa V3 de impressão) | **F2 com o meu preço de impressão** |
|---|---:|---:|---:|
| Impressão do case | 58,5–143 (estimativa V3) | 58,5–143 | **51,2** (MJF PA12, preço publicado, 184 cm³; um ponto, **não** faixa) |
| Total do instrumento | 332–477 | 304–467 | **296–375** |
| F2 contra F1 | | −8,5 % / −2,1 % | **−10,7 % (296/332) / −21,4 % (375/477)** |
| Se a F1 também imprimir a US$ 51 (F1 324–385) | | | −8,6 % / −2,6 % |

O limite de 25 % (R2V4 item 2) **não** é atingido em canto nenhum: o pior canto da eletrônica (F2 alto 467 contra F1 baixo 332, +40 %) cai para 375/332 = **+13 %** com o preço de impressão firme. A impressão era o 3º item que "podia estourar": deixou de ser. Resta o risco de a JLCPCB recusar o painel de réguas (eletrônica §5.4). **Módulo de +16:** impressão ~US$ 17 (60 cm³ de PA12 + 4 réguas) + eletrônica ~13 + teclas 14,6 (tabela 3.4 da eletrônica) = **~US$ 45 por módulo** no pedido mínimo. Tipos Extended: números da eletrônica (16 contra 17 na F1); o design não acrescenta nenhum (espuma, insertos e parafusos não são da JLCPCB).

### 12.2 Reconciliação da régua (a eletrônica propôs 74 × 12; eu tinha 15,6)

| Largura | Cabe no meu desenho? | Painel de 100 × 100 |
|---|---|---|
| 12,0 | **não**: os pinos de localização a \|y\| = 5,2 deixam 0,05 mm de parede; o bolso do 595 (7 mm) só sobra com trilhos de 2,5 mm; o entalhe do poste fica com 3 mm | 6 réguas |
| 15,6 (1ª passada) | sim, mas **6 réguas dão 113,6 mm: estoura 100 × 100** | 5 réguas |
| **14,0 (adotada)** | **sim**: trilhos 4,2–7,0, bolso livre 8,4 mm (595 de 7 mm e conector de 6 mm cabem), furos Ø2,4 a \|y\| = 5,2 (parede 0,6), entalhe 2,0 × 4,3 | **5 réguas** = 5 × 14 + 4 × 2 + 10 = **88 × 84 mm** |

Consequência para a eletrônica: painel de **5** réguas, não 6: 28 teclas (8 réguas) = 2 painéis (10 réguas, 2 de sobra); 44 teclas (12) = 3 painéis; +1 painel de PCB nas contas (~US$ 0,5–2), o resto igual. **Modelo regerado com 14,0: 0 mm³ de interferência em 28/44/60/76.** O furo de localização é redondo (Ø2,4) a 18,5 e 55,5 mm do começo, **não** "2,1 e oblongo a 66 mm".

### 12.3 Tabela de decisão F2 × F1 (com T3)

| Critério | **F2 (réguas em degraus)** | F1 (placa plana, referência) |
|---|---|---|
| Custo (28 teclas) | **US$ 296–375** (impressão firme) | 332–477 |
| Firmeza das teclas | T3 **com espuma** (achado D1.3): pré-carga 2–4 N estimada; deck 3 mm com 10 postes = 0,032 mm; régua apoiada inteira no degrau (flexão ~0). **Plano B T1:** 4 grades de FR-4, ~US$ 10–20 (estimativa), sem espuma, mas aprofunda o bolso | a T3 tem o mesmo problema da pilha de ±1,1 mm; a V3 usava grade FR-4 escareada (US$ 15–30) |
| Montagem em casa | réguas em pinos, 8 elos de cabo, 18 parafusos + insertos (~25 min), espuma: **mais passos**, mas tudo reabre | menos peças; placa grande e grade parafusada |
| Risco | espuma não medida; topo plano e pino estimados; painel de réguas na JLCPCB não confirmado; tampa mais alta (32,2 mm atrás) | custo da PCB grande; 4 hastes de botão diferentes (a F2 usa um só) |
| Escala 44 / 60 / 76 | **~US$ 45 por módulo**; case +17; MJF em 1 peça até 44, partição em zigue-zague acima | a PCB principal cresce 74 mm de 4 camadas por módulo (não calculado) |
| Botão | um só (haste +1 mm em relação à V3) | 4 alturas de haste |

**Recomendação do design:** seguir com **F2 + T3 com espuma + fixação S1**, em MJF PA12 para 28 e 44 teclas (SLA só se a cotação real vier ≥15 % abaixo); **T1 como plano B** se a espuma falhar no teste. Antes do portão P: medir uma amostra de espuma, conferir o desenho do KS-20 Orange e a aceitação do painel pela JLCPCB.

### 12.4 Respostas à eletrônica (as perguntas 1–3 são do design; 4–6 também respondidas)

1. **Conectores nas pontas:** **cabe.** O bolso é um canal contínuo de 8,4 mm entre os trilhos, com 6,9 mm livres sob a régua da fileira 1 (13,9 na 4); o SH de 4,3–4,5 mm e ~8 × 6 mm entra. O canal não é interrompido entre réguas (0,4 mm de vão): o conector da ponta **fica no apoio**, não pendurado na emenda.
2. **Emenda:** o elo de 60 mm corre no canal; **não precisa** de vão de 10 mm.
3. **Largura e furos:** 12 mm **não** confere; adotei **14,0 mm**, painel de 5 (12.2). Furos: 2 × Ø2,4 redondos a (18,5; +5,2) e (55,5; +5,2); entalhes 2,0 × 4,3 mm na borda de trás em x = 0, 18,5, 37 e 55,5 mm.
4. **Número de impressão:** **US$ 51,2** (MJF PA12, 184 cm³, 186 g); 44/60/76 teclas: 67,8 / 84,4 / 101,0 (US$ 0,275/g publicado).
5. **USB-C × M.2:** compatível em princípio (a F2 não mexe na parede esquerda; placa em x < 79 como na V3). **Não modelei** a posição do USB-C nesta passada: confirmar no posicionamento (fase B).
6. **Alto-falante CE28MB-8:** **não feito** (depende do leiaute da interface, fase B); refaço `acustica.py` quando a interface for posicionada.

---

## Perguntas para o design

1. **Aprova a T3 com espuma** (anel de PE sem silicone, 2 mm → 1 mm comprimido) no lugar das nervuras de esmagamento, com a T1 como plano B? (A pilha publicada de ±1,1 mm não fecha com nervuras.)
2. **Aprova o deck de 3 mm** (10 postes internos em 28 teclas, flecha de 0,03 mm)?
3. **Aprova a haste do botão único 1 mm mais longa** (topo da cabeça em ZR + 22,9; a V3 tinha 21,9–28,9)?
4. **Aprova as rampas de 60°** entre os degraus (com 45° a do degrau de 3 mm bate na carcaça da fileira de cima) e o telhado de interface em 15,1 mm?
5. **Aprova o furo do deck Ø8** (era Ø7; a posição acumulada em 250 mm é ±1,0 mm publicada)?
6. **Aprova a altura externa de 25,2 mm na frente e 32,2 mm atrás** (a V3 tinha 24,6)? As quinas e rampas ficam sem raio até o acabamento.
7. **Aprova a régua de 74 × 14 mm** (painel de 5, não 6) e a eletrônica ajustar as contas de painel?
8. **Processo:** o J cota `f2_28_tampa.stl` e `f2_28_base.stl` em MJF e SLA antes do portão, ou seguimos com o MJF a US$ 51?
9. **Peça de teste impressa (decisão 21):** 2 réguas + 8 teclas reais com espuma e deck mediriam a pilha e a pré-carga por ~US$ 15 de MJF. Vale fazer antes de fechar o hardware?

---

## Perguntas para o design (R4V4)

1. **Conectores da régua na faixa de trás, boca para -y** (seção R4V4 3) em vez de nas pontas: aprova? É a única posição achada em que o plugue SH passa sem bater nos pinos das teclas. O custo: entalhes na bandeja (restam 70 % do trilho de trás) e **cabos SH sob medida** (15 e 25 mm). Alternativas: FFC de 1,0 mm com conector baixo, ou solda direta (opção C da eletrônica).
2. **Parafusos M2 por fileira** (1: 18,5/55,5; 2: 37/55,5; 3 e 4: 18,5/37): aprova a mudança dos 2 furos Ø2,2 da régua nas fileiras 2 a 4?
3. **Tela:** respondida (seção 0): fenda em y 18,17..20,67 com o J401 de boca para -y. Resta confirmar o comprimento do cabo da fenda aos pinos do módulo (~14 mm no plano).
4. **Quina do case R6** (a V3 usava R9): aprova, ou prefere cantos R6,5 da placa (como na V3) com R9? Com R9 e a placa em R3, a placa invade a parede 1,0 mm.
5. **Bateria** sob a placa em x 17,4..51,4, y 40..90 (a posição da V3 bate no J602): aprova? A eletrônica confirma que não há peça alta no fundo da placa nessa região (só C309, C310, C502).
6. **Alto-falante Dayton:** o pico de +9 dB em 1 kHz e os -30 dB em G3 pedem EQ no firmware ou um alto-falante de Fs mais baixo (Same Sky CLS0281, Fs 500 Hz). Seguimos com o Dayton e EQ?
7. **Postes da tampa H1..H4 Ø5,4** com inserto M2 (V3: Ø4,6 sem inserto): aprova? H1 (62; 48) é posição proposta pela eletrônica.
8. **Para a eletrônica:** o 595 em SO-16 não cabe nas janelas da régua; TSSOP-16 ou outra posição? Confirmar a altura real do SH (4,25) e do plugue.
