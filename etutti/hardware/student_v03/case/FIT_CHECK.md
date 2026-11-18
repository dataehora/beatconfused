# eTutti Student V3 — FIT_CHECK do case (SPEC v8, ciclo 7)

Responde à **SPEC v8**, que fecha o desenho do case para o protótipo. **Nenhuma mudança de forma**: o modelo, o fit check (245 pares, 0 interferências) e os renders
são os do ciclo 6 (PR #172). Neste ciclo só se conferiu o verso da placa sob o pilar extra e se montou a lista do que falta medir.

## 0. Resumo

| Tarefa | Resultado |
|---|---|
| 1. Verso da placa sob o pilar extra | **Limpo.** Nada além do cobre de GND coberto de máscara; o pilar de (112,5; 67,5) fica onde está. |
| 2. Lista "Medir na primeira amostra" | Em §2: 8 itens, cada um com como medir e o parâmetro que muda. |
| 3. Limpeza opcional do `case.py` | **Não feita**: não há `Z_SPLIT` nem aba da V2 no código da V3 (busca em `geometria.py` e `case.py`); nada a tirar sem risco. |

## 1. Verso da placa sob o pilar extra (SPEC v8 item 1)

Conferido no arquivo da placa de encomenda (`kicad/student_v03.kicad_pcb`, KiCad python, face de baixo = a que o pilar toca), num círculo de **Ø 5,0 mm**
(Ø 4 do pilar + 0,5 de margem em volta) centrado em (112,5; 67,5):

| O que | Dentro do círculo |
|---|---|
| Vias (abertas ou não) | **nenhuma** (as mais próximas: 4 vias GND Ø 0,5 em (110/115; 65/70), a 3,54 mm do centro, 1,3 mm fora da borda do pilar) |
| Pads / ilhas expostas | nenhum |
| Peças do verso (caixas) | nenhuma |
| Trilhas em B.Cu | nenhuma |
| Cobre | só o plano de GND de B.Cu, sob a máscara (sem abertura) |

Resultado: nenhuma via aberta, ilha ou peça sob o pilar. Placa e pilar ficam como estão.
(As 4 vias vizinhas têm o modo de máscara "das regras da placa", sem abertura própria; estão fora do círculo de qualquer forma.)

## 2. Medir na primeira amostra

Lista única do que depende de peça real. Nenhuma forma muda até lá (SPEC v8 item 4).

| # | O que medir | Como | Parâmetro que muda |
|---|---|---|---|
| 1 | **Altura do USB-C** (centro) no fundo | Cupom da parede (`out/cupom_parede_tampa` + `cupom_parede_bandeja`, 25 mm da esquerda) sobre a placa montada; plugue real, ver se entra sem folga lateral e centrado | `USB_Z` (−2,9) em `geometria.py` |
| 2 | **Altura do eixo dos jacks** | Mesmo cupom, plugue P2 real (limite Ø 6,4) | `JACK_Z` (−4,0) em `geometria.py` |
| 3 | **Posição em x da frente das tomadas** (recuo de 0,3 até a parede) | Paquímetro: face da tomada até a borda da placa; soldagem JLCPCB ±0,1–0,2 | `CONN_FRONT_X` (= WALL + 0,3) em `geometria.py` |
| 4 | **Pilha do H101** (módulo, porca e parafuso M2,5 + espaçador 2,5) | Paquímetro de profundidade: do fundo da placa à ponta do parafuso/porca; ver se cabe o rebaixo | `H101_RECESS` (8 × 1,0) em `case.py` |
| 5 | **Boca do J401** (cabo da tela) | Olhar o conector soldado: para que lado abre e por onde o cabo entra | posição/rotação do cabo no modelo (percurso do cabo, só informativo; sem parâmetro de forma hoje) |
| 6 | **Eixo dos encoders**: comprimento (ponta a ~24,5 acima da placa) e comprimento do chato | Paquímetro de profundidade da ponta do eixo à placa; do chato à ponta | `KNOB["shaft_top"]` (24,5), `shaft_flat` (4,5), `bore_over` (0,5) em `case.py` |
| 7 | **Compressão real do pé sob 3 N** | Case montado sobre a mesa, peso de ~300 g sobre a tecla SW23, paquímetro de profundidade (ou relógio comparador) | `FOOT_H` (1,5); se passar de 0,02 mm, trocar por PU de 90A (E 15 MPa) |
| 8 | **OLED, bateria e plugues reais** | OLED: posição das ilhas e da área ativa e espessura; bateria 503450 com a placa e o NTC; plugues reais contra 12,35 × 6,5 e Ø 6,4 | `OLED_PCB`, `OLED_WINDOW`, `BATTERY` (case.py/geometria.py); aberturas `USB_OPENING`, `JACK_OPENING_D` |

## 3. Perguntas para o design

1. Algum item da lista deve ficar de fora (ou entrar) antes de o J encomendar o protótipo?
2. A limpeza do §0 (tarefa 3) fica como está: não há parâmetros só da V2 no código da V3 para tirar.

---

# Anexo — FIT_CHECK do ciclo 6 (SPEC v7, PR #172)

Responde à **SPEC v7**. Modelo regerado (`case.py`), fit check de 245 pares: **0 interferências**; a placa e a bandeja entram por baixo livres em todo o curso
(0 mm³ em todos os cursos testados). Nada foi impresso nem pedido. O ciclo 5 (SPEC v6) e o 4 estão no fim deste arquivo.

## 0. Resumo

| Tarefa | Resultado |
|---|---|
| 1. Tirar a prateleira | Feito: constantes, código e rebaixo saíram do `case.py`. |
| 2. Pés de 80A + apoio extra perto do SW2 | **Fecha: pior tecla 0,036 mm** (placa) / **0,040 mm provável, 0,047 pior caso** com pé de 80A. Apoio extra = pilar Ø 4 em (112,5; 67,5). |
| 3. Knob alto | Feito: furo em D até z 25,0, pele de 0,8, topo z 25,8 (11,3 sobre o tampo). Knob de 7 mm removido. |
| 4. Lista de compras | Abaixo (§4): 10 pés de PU/silicone ≥ 80A. |
| 5. fit_check / fit_extra / renders | Feitos. |

## 1. Prateleira
`SHELF_W/SHELF_Z/SHELF_ON` e a união da prateleira saíram do `case.py`; a bandeja é a de antes (folga 0,15 da parede, rente à borda da tampa).

## 2. Flexão com 80A e o apoio extra (`estudos/flexao.py`)
- Antes (4 pinos + 3 pilares): pior tecla SW2, 0,0492 mm.
- **Apoio extra:** pilar Ø 4 sem furo (como os da v2) em **(112,5; 67,5)**, a 7,3 mm do SW2 (116,95; 74,03). O local vem da lista de vãos livres do verso
  (≥ `PILLAR_CLEAR` de qualquer peça, ≥ 4 mm dos outros apoios), escolhido entre os 40 mais próximos pelo que mais reduz o pior caso. A bandeja ganha o pilar e um 10º rebaixo de pé.
- Resultado (placa nos apoios da borda + 4 pinos + 4 pilares, mesa rígida): pior tecla agora **SW23, 0,0361 mm** (SW2 caiu a 0,0135); nenhuma tecla acima de 0,05.
- Com o pé (E estimado), compressão provável (1/3 da carga num pé) e pior caso (os 3 N num pé):

| Pé | Pior tecla, provável | Pior caso |
|---|---|---|
| silicone 60A (4 MPa) | 0,044 mm | 0,058 mm |
| **PU/silicone 80A (8 MPa)** | **0,040 mm** | **0,047 mm** |
| PU duro 90A (15 MPa) | 0,038 mm | 0,042 mm |

Meta de ≤ 0,05 mm cumprida com 80A, mesmo no pior caso. O E dos pés é estimativa; o número real vem da peça (medir na primeira amostra).

## 3. Knob alto
Furo em D até **z 25,0** (0,5 sobre a ponta nominal 24,5), pele **0,8 mm**, topo **z 25,8** (11,3 sobre o tampo). Saia, corpo, folga e traço creme como estavam.
Encaixe no eixo 9,2 mm; folga do knob à tampa 0,8 mm. Sobra de eixo: a ponta fica 1,3 mm abaixo do topo. Peça: `out/knob.stl` (imprimir 2); `knob_7mm`/`knob_10mm` removidos.

## 4. Lista de compras (pés)
**10 unidades** de pé autoadesivo de PU ou silicone **≥ 80 Shore A**, Ø 8 × 1,5 mm: 4 sob os pinos, 4 sob os pilares (3 + o extra), 2 à esquerda. Não serve silicone macio comum (40–60A).

## 5. Perguntas para o design
1. O pilar extra em (112,5; 67,5) fica no verso da placa sem peça num raio de `PILLAR_CLEAR`; confirma que a placa não precisa de nenhuma marcação (ele só encosta no verso)?
2. Posso registrar a medida da dureza/compressão do pé como item da primeira amostra (compressão real a 3 N)?
3. Algo mais a tirar do `case.py` além da prateleira (código do `SHELF` não existe mais)?

---

# Anexo — FIT_CHECK do ciclo 5 (SPEC v6, PR #170)

Responde à **SPEC v6** (que mantém a v5, com os itens 2 e 6 substituídos). Modelo regerado (`case.py`), fit check de 245 pares: **0 interferências**
(placa e bandeja entram por baixo livres em todo o curso). Nada foi impresso nem pedido. O ciclo 4 (SPEC v4) está no fim deste arquivo.

## 0. Resumo

| Tarefa | Resultado |
|---|---|
| 1. Chanfro 4,0 × 3,5 nos quatro lados | **Feito.** Tampa sobre a grade com **1,4 mm** em toda a volta; cabeças escareadas escondidas. |
| 2. Encoder de eixo de 15 mm | **Não existe na família EC11E** (§2). **Segue o knob de 10 mm** (segunda opção da SPEC). |
| 3. Knob nas duas versões | Feito: `knob_7mm` e `knob_10mm` (STEP/STL); o de 10 mm é o `knob`. Render: `renders/knobs_7_e_10.png`. |
| 4. Prateleira + rebaixo da bandeja | **Não coube: a placa não passa pela prateleira (achado F).** Chave `SHELF_ON` no `case.py`, desligada. |
| 5. 9 pés | Feito: 9 rebaixos Ø 8,4 × 0,5 na bandeja e a peça `pe.stl` (Ø 8 × 1,5). Render: `renders/bandeja_de_baixo.png`. |
| 6. Flexão sobre os pés | Placa sozinha 0,0492 mm; **com a compressão do pé de silicone passa de 0,05** (achado G). |
| 7. Grade: cobre a Ø 4,4 + figura | Feito (`pcb/grade_fab.py`, `GRADE_ESCAREADA.md`, `renders/grade_escareada.png`). |
| 8. fit_check / fit_extra / renders | Feitos. |

## 1. Chanfro 4,0 × 3,5 (pergunta C2 e C4)

- `CHAMFER = (4.0, 3.5)`, R 1,5 nas duas arestas, chanfro interno acompanhando (parede de 2,0 na normal). Sulcos, legendas e logo como estavam.
- **C2 — tampa sobre a grade:** 1,4 mm (z 13,1 → 14,5) em toda a área da grade, inclusive na frente e no fundo, onde a borda da grade chega a 4,47 mm da
  parede externa; ali o teto inclinado do chanfro fica a 1,81 mm acima da grade (a medida é por conta do plano do chanfro; o corte do teto sobre a grade vale 1,4).
  Ponto mais fino: a boca do poço (parede reta de 0,2 mm sob o R 1,2 do poço, como na v4). A meta de ≥ 1,2 mm está cumprida.
- **C4 — postes de trás da tela:** ficam a **1,85 mm** do início do teto plano (a SPEC esperava ~1,8). Achado E resolvido sem mover nada.

## 2. Encoder, tarefa 1

Fonte: página da série EC11E da Alps (https://tech.alpsalpine.com/e/products/category/encorders/sub/01/series/ec11e/). **Todos os 9 modelos verticais
EC11E têm "actuator length 20 mm"**, eixo plano Ø 6; nenhum de 15 mm:

| Modelo | Detentes / pulsos | Chave |
|---|---|---|
| EC11E09204A4 / EC11E09244BS / EC11E09244AQ | 18 / 9 | sem / com 0,5 mm / com 1,5 mm |
| EC11E15204A3 / EC11E15244G1 / EC11E15244B2 | 30 / 15 | sem / com 0,5 mm / com 1,5 mm |
| EC11E1820402 / EC11E18244AU / EC11E18244A5 | 36 / 18 | sem / com 0,5 mm / com 1,5 mm |

- O "15" no código é **15 pulsos**, não o comprimento do eixo (o EC11E15244G1 tem eixo de 20 e dá a ponta a ~24,5, como a SPEC já avisa).
- Não conferi outras famílias nem outros fabricantes: as cotas da Alps estão em desenhos GIF que não consegui ler. A ponta acima da placa só se confirma
  com o desenho cotado de cada peça. Não encontrei nenhuma que cumprisse as cinco exigências com certeza.
- **Decisão neste ciclo:** segue o **knob de 10 mm**, como a SPEC manda quando não há encoder. Nenhuma troca de footprint nem de firmware
  (`ENC_STEPS_PER_DETENT = 2` continua valendo com o EC11E18244AU); a tarefa 3 (eletrônica) não se aplica.

## 3. Knobs, tarefa 2

| | knob de 7 mm | **knob de 10 mm (o que vale)** |
|---|---|---|
| Topo | z 21,5 (7,0 sobre o tampo) | z 25,0 (10,5 sobre o tampo) |
| Eixo | ponta a 19,5 (eixo de 15) | **ponta a 24,5** (EC11E18244AU inteiro) |
| Encaixe no eixo | 4,2 mm | **9,2 mm** (furo até z 24,8; a ponta fica com folga de 0,3 sob o fundo do furo) |
| Pele sobre o furo | 1,7 mm | 0,2 mm (o traço creme tem 0,3 mm de profundidade no de 10; 0,4 no de 7) |

- Mesmo desenho (saia Ø 12, corpo Ø 9, furo em D de Ø 6,2 com chato a 4,5 do eixo), só o corpo mais alto. No modelo do EasyEDA o eixo Ø 6 vai de 12,5
  a 24,5, então o encaixe de 9,2 mm fica todo no trecho de eixo. O comprimento do chato não foi medido (desenho da Alps em GIF).
- Nota: a SPEC pedia a ponta 0,5 mm abaixo do topo com o furo de 9,5 mm; com a ponta a 24,5 e o topo a 25,0 (10,5 sobre o tampo) a pele é de 0,5 mm acima da ponta,
  mas o furo de 0,3 mm de folga deixa só 0,2 mm de pele. Ver a pergunta 4.
- Folga da bucha do encoder ao teto: 1,0 mm (C10).

## 4. Prateleira da v5, achado F

A prateleira de 1,5 × 1,0 mm na base da parede **bloqueia a placa**: a placa entra na tampa por baixo e chega a **0,5 mm** da parede (a placa tem
borda a 2,5 mm; a parede, 2,0), então uma prateleira de 1,5 mm, em qualquer altura abaixo da placa, sobrepõe 1,0 mm a placa. No fit check (placa subindo
de 0,5 a 30 mm): **613 mm³ de interferência a 8 mm de curso** (de 1,8 a 20 mm³ nos cursos de 2 a 6 mm). Na cota original da v5 (z −10,1…−9,1) vale o mesmo.

- **Resolvido no modelo:** `SHELF_ON = False` no `case.py`; a bandeja volta ao contorno de antes (folga de 0,15 mm da parede, face de baixo rente à borda da tampa). O código
  da prateleira e do rebaixo da bandeja continua no arquivo.
- **O que a prateleira queria resolver (flexão no colo) fica coberto de outro modo:** com a bandeja rente, o contorno inteiro (parede da tampa + borda da bandeja)
  assenta na mesa ou no colo; é o caso "apoiada em todo o contorno" do estudo (§5).
- Opções, se o Chat quiser mesmo um ressalto: (a) pontas locais de 1,5 × 4 mm só onde a placa tem recorte; (b) mudar a montagem (a bandeja entra antes da placa, o que
  a SPEC v4 não permite pelos parafusos); (c) deixar como está. Recomendo (c): os pés e o contorno rente já resolvem.

## 5. Flexão com os pés, tarefas 4 e 5 (pergunta C3)

Estudo em `estudos/flexao.py` (grelha de vigas, 3 N numa tecla de cada vez). Os 9 pés ficam sob os 4 pinos, os 3 pilares e dois à esquerda,
(22; 10) e (22; 90), longe dos rebaixos dos parafusos e do H101 (fit check sem interferência).

| Caso | Pior tecla | Observação |
|---|---|---|
| Placa nos apoios da borda + 4 pinos + 3 pilares (mesa rígida, pés indeformáveis) | **0,0492 mm** (SW2) | passa da meta de 0,05 por 0,0008 |
| + compressão do pé de silicone 60A (E = 4 MPa), 1/3 da carga num pé | 0,057 mm | acima da meta |
| + pé 50A (E = 2,5 MPa), idem | 0,061 mm | acima |
| + pé 40A (E = 1,5 MPa), idem | 0,069 mm | acima |
| Pior caso (os 3 N inteiros num pé): 60A / 50A / 40A | 0,072 / 0,085 / 0,109 mm | |
| Colo, sem mesa: bandeja apoiada no contorno, PA12 MJF, nervuras ≈ 3 mm | 0,142 mm | só informativo |
| Colo: bandeja de ≈ 4 mm equivalente | 0,060 mm | com nervuras mais altas |

- **Achado G:** a placa sozinha já está no limite (0,0492). Com o pé de silicone o piso de 2 mm não flexiona (pino e pé alinhados), mas o pé se comprime:
  dz = F·h/(E·A), A = 50,3 mm², h = 1,5 mm. A pior tecla vai a 0,057–0,069 mm.
- **Como fechar:** pé **mais duro** (70A–80A ou PU duro, E ≥ 8 MPa: compressão provável ≈ 0,004 mm, pior caso ≈ 0,011 mm) ou **mais fino**
  (1,0 mm). Registrar a dureza na SPEC. O modelo de pé de silicone é estimativa (E do silicone varia muito); o número real vem da peça.
- **Nervuras mais leves:** não propus. Com os pés a bandeja não flexiona entre pino e pé; as nervuras servem ao piso e ao caso do colo (0,142 mm com 3 mm equivalentes).
- Grade (FR-4, 0,217 mm a 5 N, encosta nas teclas; alumínio 0,057 mm, não) e os outros números do estudo não mudaram.

## 6. Grade escareada só de fábrica, tarefa 6 (pergunta C6)

`GRADE_ESCAREADA.md` reescrito: sem "escarear em casa"; textos prontos para a JLCPCB e para a PCBWay; figura `renders/grade_escareada.png` (planta com os 10 furos
numerados + corte do cone). **Cobre recuado até Ø 4,4** nas duas faces (`pcb/grade_fab.py`, novo; os arquivos da V2 não foram tocados): distância mínima do
centro do furo ao cobre de 2,20 mm medida no arquivo preenchido; DRC com 0 erros (o aviso `isolated_copper` é inofensivo). **C6:** os círculos de Ø 4,4 não tocam
nos furos das teclas; perto da borda o cobre já recuava 0,5 mm do contorno, sem problema.

## 7. Perguntas para o design

1. **Prateleira:** concorda em **abandonar** a prateleira (achado F) e deixar a bandeja rente, apoiada no contorno? Ou quer as pontas locais (opção a)?
2. **Pé:** de que dureza? A 60A ou menos a pior tecla passa de 0,05 mm (achado G). Recomendo silicone 70A–80A ou PU duro, Ø 8 × 1,5, ou pé de 1,0 mm.
3. **Encoder:** sem eixo de 15 mm na família Alps EC11E, segue o knob de 10 mm. Quer que a eletrônica procure um EC11 de eixo curto de outro fabricante, para uma série futura, com a ponta cotada a partir da placa?
4. **Knob de 10 mm:** a pele de 0,2 mm sobre a ponta do eixo é fina. Prefere o furo passante, com a ponta do eixo à mostra, ou subir o knob 0,5 mm?
5. **Grade:** o pacote para a JLCPCB/PCBWay está pronto. Falta confirmar com a JLCPCB, no pedido, se o escareado cônico NPTH entra no pedido de placa da grade.

---

# Anexo — FIT_CHECK do ciclo 4 (SPEC v4, PR #166)


Autor: Claude Code · Resposta à `student_v03/SPEC.md` (v4). Modelo em `student_v03/case/` (cópia do da V2, que ficou intacta):
`case.py`, `fit_check.py`, `fit_extra.py`, `render.py`, `render_comparacao.py`; estudos em `student_v03/estudos/`;
números em `case/out/case.json`, `fit_check.json`, `fit_extra.json`.

## 1. Resultado

- Tampa de z −10,1 a **14,5** (case de **24,6 mm**), sem emenda na parede, chanfro inferior de 1,5 na tampa; fundo é uma **bandeja** de 2 mm com borda,
  nervuras, bossas, copos, pinos, pilares, berço da bateria (x 19,5–69,5) e rebaixo do H101. Furos de USB-C e dos jacks **inteiros na tampa**,
  fechados, nas alturas novas (`USB_Z` = −2,9, `JACK_Z` = −4,0, parâmetros em `geometria.py`).
- **fit_check: 245 pares testados, 0 interferências**; a placa (com tudo do fundo, o módulo, a porca e o parafuso do H101) sai e entra pelo
  fundo da tampa sem tocar a parede; a bandeja entra e sai pelo fundo com 0,15 mm de folga por lado; os plugues no limite entram até o batente.
- Pedaços de aferição prontos: **cupom da parede** (`cupom_parede_tampa` + `cupom_parede_bandeja`, 25 mm da esquerda).
- **Cinco achados precisam da sua decisão** (seção 3). Os dois mais sérios: a tampa fica com 0,5 mm sobre a grade na frente e no fundo, e a meta de
  flexão não fecha com a bandeja "no ar".

## 2. O que foi feito, tarefa por tarefa

| # | Tarefa | Estado |
|---|---|---|
| 1 | Cópia para `student_v03/case/`, V2 intacta | feito (furos lidos da placa V3: `pcb/export_furos.py` → `pcb/furos.json`; os mesmos da V2) |
| 2 | Tampa até −10,1, chanfro inferior 1,5, sem `Z_SPLIT`, sem aba | feito |
| 3 | Furos fechados nas alturas novas, chanfro 0,5 | feito |
| 4 | Bandeja: borda (topo −6,6, −7,6 nas zonas de conector y 9–23, 30–42, 54–66), nervuras, bossas, copos, pinos, pilares, Program, rebaixo H101 (Ø 8 × 1,0 sob (47,5; 14,0)) | feito; nervuras: grade de 1,2 × 4,1 mm, passo 12 mm, x 72–240, y 6–94, topo em z −4,0 |
| 5 | Berço da bateria x 19,5–69,5 | feito |
| 6 | Módulo OLED girado, centro (37,0; 20,1), postes (37 ± 11,65; 20,1 ± 11,9) | feito; percurso do cabo: ver C6 |
| 7 | Legendas OUT/IN em z −5,0 … −3,0, a 1,8 do furo; traço do "STUDENT · V2" 0,20 | feito (traço: 0,025 por lado) |
| 8 | Cor: tampa creme até embaixo, só a bandeja cinza; faixas até o chanfro | feito nos renders |
| 9 | Estudo de flexão | feito, **não fecha no ar** (achado C) |
| 10 | Estudo acústico | feito, **9,75 cm³** (achado D) |
| 11 | `fit_check.py` com a montagem do item 5 | feito |
| 12 | Cupom da parede | feito |
| 13 | Renders | feito: `renders/parede*.png`, `corte_jacks_y36.png` (y 36), `corte_fenda_x35.png` (fenda da tela), `corte.png` (fileiras), `bandeja_de_baixo.png`, `bandeja_de_cima.png`, `isometrico.png`, e `comparacao_v2_v3.png` / `comparacao_frente_v2_v3.png` (V2 e V3 lado a lado) |
| 14 | Tampo em 14,5: chanfro e sulcos 3,7 mais baixo (sulcos 4,3 / 6,5 / 8,7); poço de 1,55 com tampa de 1,4 e aresta R 1,2, sem aba | feito, com o achado A |
| 15 | Grade escareada | modelo feito; **o pedido na JLCPCB não foi confirmado**, ver `GRADE_ESCAREADA.md` |
| 16 | Knob sem luva; postes mais curtos; módulo OLED no teto novo | feito, com o achado B |
| 17 | Botões iguais; nada da tampa nova encosta no curso | feito: botão ao poço, solto e apertado, a ≥ 5,1 mm |
| 18 | Este arquivo | feito |

## 3. Achados que precisam de decisão

**A. A tampa sobre a grade, na frente e no fundo, tem só 0,5 mm.** A grade (21,5 mm em volta das teclas) chega a 4,47 mm da parede externa nessas duas
faixas, onde o chanfro de 30° (6 × 3,5) ainda está subindo: a face externa está em z ≈ 13,6 e a grade pede o teto em 13,1. Resultado: **0,51 mm de
tampa** sobre a borda da grade em toda a frente e todo o fundo (a V2 tinha o chanfro bem acima). O cálculo está em `fit_extra.json` (`C12_...`). Não cabe
em MJF/resina (≥ 0,8–1 mm). Alternativas (a SPEC decide):
1. chanfro de **4,0 × 3,5** só na frente e no fundo (a face externa chega a 14,5 em 4,0 mm da parede e a tampa fica com 1,4 mm);
2. grade menor na frente e no fundo (borda a ≥ 6 mm da parede): não cabe, porque os parafusos escareados (cabeça Ø 3,8) ficam a 18,5 mm da casca das teclas e precisam de ~2,5 mm de borda;
3. subir o tampo em frente e fundo (muda a proporção aprovada).
Recomendo a 1. Por ora o modelo tem os 0,51 mm (sem interferência: a tampa é cortada para a grade passar).

**B. O eixo do encoder tem 24,5 mm, não 20.** O modelo EasyEDA do EC11E18244AU (C202365, `case/modelos/`, fora do Git): corpo quadrado até z 4,5, colar Ø 8
até 5,0, bucha Ø 7 até 11,5, **eixo Ø 6 de 12,5 a 24,5** (a descrição do LCSC diz H24,5). Logo o eixo fica **10 mm acima do tampo** e **3,0 mm acima do topo do
knob** (z 21,5). Duas saídas: cortar o eixo em 20 (serra, 4,5 mm por encoder) e o knob encaixa 4,7 mm, ou um knob mais alto (a 24,5, +3 mm sobre o aprovado).
A bucha acaba 1,0 mm abaixo do teto (z 11,5 contra 12,5): **não entra no furo Ø 9,2 da tampa**, só o eixo passa por ele. O modelo da V3 assume o eixo cortado em 20.

**C. Flexão: com a bandeja "no ar" não chega a 0,05 mm.** (`estudos/flexao.json`)
- Placa com apoios rígidos (borda + 4 pinos + 3 pilares em (127,5; 32,5), (182,5; 62,5), (182,5; 32,5), os mesmos da V2): **0,049 mm** na pior tecla (SW2). ✔
- Mas os pinos e pilares apoiam numa **bandeja de 2 mm presa só pelos 6 parafusos**: uma carga de 3 N num apoio a faz ceder **2,06 mm** (MJF, E = 1,7 GPa) ou 1,40 mm (resina). Com a grade de nervuras (equivalente a uma placa de 3,0 mm) 0,61 mm; com 4,0 mm equivalentes, 0,26 mm. Apoiada **em todo o contorno**: 0,48 / 0,14 / 0,06 mm (MJF) e 0,33 / 0,10 / 0,04 mm (resina).
- Conclusão: a meta só fecha se a bandeja não ficar no ar. Opções: (i) a bandeja **sai 0,2–0,3 mm abaixo da borda da tampa**, apoiada na mesa (a SPEC pede "nunca saliente"); (ii) a parede da tampa ganha uma **prateleira interna** (z ≈ −9,1) onde a borda da bandeja se apoia em todo o contorno, e a carga vai à parede e à mesa; (iii) aceitar que a flexão da bandeja soma 0,1 a 0,3 mm. Recomendo a (ii), que não muda o exterior.
- O estudo da V2 também supôs apoios rígidos.

**D. Caixa acústica: 9,75 cm³ (V2: 10,4).** Com o piso em z 0,3, a extensão à esquerda (x 5) e um **segundo bloco alto à esquerda do anel do alto-falante**
(x 5–19,5, acrescentado por mim: sem ele eram 7,9 cm³), chega a 9,75 cm³. Pelo modelo de 2ª ordem (alto-falante nominal): fc 717 Hz (V2: 703), nível em 262 Hz
−16,4 dB (V2 −16,1), em 523 Hz −1,1 dB (V2 −0,7): **0,3 a 0,4 dB pior que a V2**. Com manta acústica (+15 %): 11,2 cm³ efetivos. Para chegar a 10,4 sem manta:
afinar as nervuras (−0,3 cm³ de material) ou ganhar 1,5 mm em y para o fundo (o berço da bateria não encosta).

**E. Postes da tela quase tangentes ao chanfro.** Os dois postes de trás ficam em y 8,2 (raio 1,6): começam a 0,06 mm do ponto em que o teto vira plano (y 6,54). Funciona, mas
sem margem: subir o módulo 0,5 mm em y (e a janela com ele) ou deslocar os postes de trás para y ≥ 8,7.

## 4. Respostas às perguntas C1–C13

- **C1 (modelos 3D).** XUNPU PJ-327A (STEP do EasyEDA em `case/modelos/`): corpo 14,2 × 8,6 × 5,4 mm; admitindo z = 0 no eixo (é o que a faixa −2,9 … +2,5 sugere), o **eixo fica 2,9 mm acima da face** (V3: z = **−4,1**, a SPEC usa −4,0) e o ponto mais baixo é 5,4 mm abaixo da face da placa: **z = −6,6** (a SPEC estimava −6,3). HRO TYPE-C-31-M-12: casca de 3,16 × 8,94, centro a 1,68 mm da face (V3: z ≈ −2,9 ✔), ponto mais baixo −4,46. **A posição em x da frente** não saiu do modelo (o deslocamento do footprint do EasyEDA para o do KiCad é de 6,6 mm no jack); fica o recuo de 0,3 da SPEC, a confirmar na amostra.
- **C2 (folgas da bandeja).** A menor é **0,24 mm** entre o U605 (74LVC1G08, x 154,6; y 10,5) e o copo da porca da grade em (160,0; 7,5), no plano. Depois: L201 0,8; J202 0,9; os jacks 1,10; USB-C 3,14. **H101:** a porca fica a 1,88 mm da bandeja, a ponta do parafuso (z −8,0) a 1,1 mm do fundo do rebaixo (z −9,1). Módulo MicroMod ao piso: 2,2 mm. Peças do fundo sob as nervuras (topo em −4,0): a mais alta do teclado tem 1,45 mm (fundo em z −2,65), folga ≥ 1,3 mm.
- **C3.** Face reta abaixo da boca: **1,7 mm** (USB-C) e **0,85 mm** (jacks) até o chanfro inferior (z −8,6); a parede na borda de baixo fica com 0,5 mm (2,0 − 1,5). 0,85 mm é imprimível em MJF e resina, mas é o ponto mais fino da parede esquerda.
- **C4 (bateria, x 19,5–69,5).** Até o J302: 3,0 mm (x); U501 0,70 mm, C502 1,15, R501 1,30 (z); C501 0,80 mm (y). Todas ≥ 0,5 mm em z. ✔
- **C5 (módulo da tela girado).** Até os encoders 6,4 mm; até a cabeça do parafuso do H101 7,8 mm; a borda de trás do módulo está em y 6,2, antes do plano do teto (y 6,54): o canto entra 0,34 mm na zona do chanfro, sem interferência (o plano está em z ≈ 12,3 ali). Postes: achado E.
- **C6 (J401).** Sem rotação (0°), em (35,5; 36,5), fenda em y 29,9–32,4, pinos do módulo em y ≈ 32,5. Subida de 12,0 mm (do fundo da placa ao fundo do módulo). **Percurso mínimo ≈ 21 mm**, folga de ~29 mm no cabo de 50 mm. **Para que lado a boca do conector abre** não consegui confirmar pelo footprint: a conferir na amostra ou no desenho da JST.
- **C7.** Ver o achado C: pilares e pinos como na V2, 0,049 mm (apoios rígidos); a bandeja é o que falta.
- **C8.** Caixa: 9,75 cm³; folga até o poste do H4 (y 91,5) 0,5 mm; até o plano do chanfro da esquerda, 0,4 mm (cortada por um prisma). Ver achado D.
- **C9.** Tampa **52,9 cm³** (V2 55,2); bandeja **64,5** com as nervuras (a base da V2: 64,0). Volume total praticamente igual.
- **C10.** Achado B. Corpo do encoder até z 4,5 (não 6,5 como eu supunha): folga da tampa 1,49 mm, não há corpo acima de 12,0, **sem rebaixo local** na tampa.
- **C11.** Achado D (ganho/perda em 262 e 523 Hz).
- **C12.** Tampa de 1,4 mm sobre a borda da grade: folga de 0,15 mm até a grade e as cabeças escareadas (rentes). Com R 1,2 numa tampa de 1,4 mm, a parede reta da boca do poço sobra com **0,2 mm**: é um canto arredondado, não uma parede, e imprime, mas é fino na ponta. **O trecho da frente e do fundo é o do achado A.**
- **C13.** Lateral entre o botão da 1ª fileira (Ø 15) e a aresta R 1,2 do poço: **5,0 mm** (12,5 − 7,5), solto e apertado; a distância mínima do botão apertado à tampa é 5,1 mm.

## 5. Perguntas para o design

1. **Achado A:** chanfro de 4,0 × 3,5 na frente e no fundo (recomendado), ou outra solução, para a tampa sobre a grade não ficar com 0,5 mm?
2. **Achado B:** cortar o eixo do encoder em 20 mm (4,5 mm de serra por unidade) ou aumentar o knob? Ou comprar a versão de eixo curto?
3. **Achado C:** prateleira interna na parede da tampa para a bandeja se apoiar em todo o contorno (recomendado), bandeja 0,2 mm saliente, ou aceitar a flexão?
4. **Achado D:** aceitar 9,75 cm³ (perda de 0,3–0,4 dB) ou pedir mais volume (por exemplo 1,5 mm a mais em y)?
5. **Achado E:** mover o módulo da tela e a janela 0,5 mm ou os postes de trás?
6. **Grade escareada:** o pedido na JLCPCB aceita o escareado ou fazemos em casa (`GRADE_ESCAREADA.md`)?
7. O texto final do "STUDENT · V2" (pergunta J2 da seção 12 da SPEC) continua em aberto; o modelo mantém "STUDENT · V2" com traço de 0,20 mm.
8. Quando houver a primeira placa montada: confirmar `USB_Z`, `JACK_Z`, a posição em x da frente das tomadas, a pilha do módulo (porca e parafuso) e a boca do J401. O cupom da parede serve para o teste.
