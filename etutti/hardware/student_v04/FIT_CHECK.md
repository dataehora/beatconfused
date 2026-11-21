# eTutti Student V4 — FIT_CHECK (design)

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
