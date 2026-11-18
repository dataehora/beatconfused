# eTutti Student — SPEC v7 do case (placa V3)

Data: 18 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code
Responde às 5 perguntas do FIT_CHECK do ciclo 5 (PR #170). Tudo o que não é mencionado aqui continua como na v6, na v5 e na v4 (anexos abaixo) e no modelo do PR #170.

## Mudanças desde a v6

### 1. Prateleira: abandonada (pergunta 1)

- Fica a **opção (c)** do Code: sem prateleira e sem pontas locais. `SHELF_ON = False` passa a ser a decisão, não um teste. O código da prateleira pode sair do `case.py`.
- A bandeja continua rente à borda da tampa, com 0,15 de folga da parede, sobre os 9 pés. No colo, o case apoia no contorno (bandeja + borda da tampa). É só informativo, como já estava.

### 2. Pés: poliuretano duro e um apoio a mais perto da pior tecla (pergunta 2)

- **Pé:** poliuretano (ou silicone) de **≥ 80 Shore A**, Ø 8 × 1,5, autoadesivo, no mesmo rebaixo de Ø 8,4 × 0,5. A dureza fica registrada na lista de compras. O silicone macio comum (40–60A) não serve.
- **Margem para a meta:** a placa sozinha já está em 0,0492 mm, no limite. O Code procura **um apoio a mais** (pino ou pilar, com pé embaixo) perto da pior tecla (SW2, em (116,95; 74,03)):
  - num vão entre teclas sem peça do fundo, a ≥ 1 mm de qualquer peça;
  - pode ser um pilar Ø 4 sem furo, como os da v2, se não houver lugar para um pino com ponta.
- **Meta:** pior tecla **≤ 0,05 mm a 3 N** com os pés de 80A, na mesa.
  - Se mesmo com o apoio extra não fechar, **aceito até 0,055 mm**. 5 µm a mais não se sentem no dedo. Registrar o número.
  - Se precisar passar disso, voltar antes de mudar mais nada.

### 3. Encoder: fica o EC11E18244AU com o knob de 10 mm (pergunta 3)

- O protótipo usa o EC11E18244AU inteiro, **sem corte**, com o knob alto do item 4.
- **Não** procurar agora um encoder de outro fabricante. Isso fica registrado como tarefa de eletrônica para quando a Student for para série, e não faz parte deste ciclo.

### 4. Knob alto: pele de 0,8 mm sobre o furo (pergunta 4)

- **Nada de furo passante**: a ponta do eixo não aparece.
- O furo em D termina em **z 25,0**, 0,5 mm acima da ponta nominal (24,5), o que dá folga para a tolerância do eixo.
- A pele sobre o furo fica com **0,8 mm**, então o topo do knob vai para **z 25,8** (11,3 sobre o tampo). Saia, corpo, folga da saia ao tampo e traço creme ficam como estão: só o corpo cresce 0,8.
- O knob de 7 mm sai do modelo, e o `knob` passa a ser este. Renders: o isométrico com os knobs novos.

### 5. Grade escareada (pergunta 5)

- Nada muda no modelo. A confirmação é com o próprio pedido: o J sobe a grade na JLCPCB com o texto de `GRADE_ESCAREADA.md` e só paga depois que a revisão aceitar o escareado. Se a JLCPCB recusar, vai para a PCBWay (SPEC v6, item 2).

## Tarefas para o Code

1. **[Design]** Tirar a prateleira do `case.py` (item 1).
2. **[Design]** Pés de 80A no estudo de flexão. Procurar e modelar o apoio extra perto do SW2 (pino ou pilar na bandeja, pé embaixo) e dizer a pior tecla (item 2).
3. **[Design]** Knob alto: furo em D até z 25,0, pele de 0,8, topo em z 25,8. Remover o knob de 7 mm (item 4).
4. **[Design]** Lista de compras: pé de PU/silicone ≥ 80A, Ø 8 × 1,5, 10 unidades (9 + o apoio extra, se houver).
5. **[Design]** `fit_check.py`, `fit_extra.py`, renders (isométrico, bandeja de baixo) e FIT_CHECK.md terminando com "Perguntas para o design".

---

# Anexo — SPEC v6 (referência)


Data: 18 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code
Revisão curta da v5, a pedido do J: **nenhum corte de eixo e nenhum escareado em casa, nem como plano B.** Muda só os itens 2 e 6 da v5. Todo o resto da v5 vale como está (anexo abaixo).

## Mudanças desde a v5

### 1. Encoders: sem corte de eixo (substitui o item 2 da v5)

O EC11E18244AU tem a ponta do eixo a 24,5 mm da placa. No modelo do EasyEDA: corpo até 4,5, bucha até 11,5, eixo até 24,5. Os "20 mm" do catálogo da Alps são medidos a partir do corpo: 4,5 + 20 = 24,5. Logo, **um EC11E de eixo de 15 mm deixa a ponta em ~19,5**, que é exatamente o que o knob de 7 mm precisa (topo em 21,5, encaixe de ~5 mm).

**Primeira opção: trocar o encoder por um de eixo de 15 mm.**
- Exigências, conferidas no datasheet antes de escolher:
  - mesmo footprint do EC11E (5 pinos + 2 abas, mesmo passo);
  - vertical, com chave de pressão;
  - eixo Ø 6 com o chato em D até a ponta, com ≥ 4 mm de chato;
  - ponta a **19,0 … 20,5** mm acima da placa;
  - detentes e pulsos na razão de 2 detentes por pulso (como 18/36 ou 15/30), para manter `ENC_STEPS_PER_DETENT = 2` no firmware.
- Primeiro a família EC11E da Alps; se não houver em estoque, um compatível com EC11 de outro fabricante, nas mesmas condições.
- Os encoders são soldados em casa, então a peça pode vir de qualquer distribuidor (LCSC, Mouser, Digi-Key, Farnell), não precisa estar na biblioteca da JLCPCB.
- **Atenção:** "eixo de 20 mm" no catálogo da Alps não basta. Pela conta acima, peças de 20 mm (como o EC11E18244AU e o EC11E15244G1) dão a ponta em ~24,5. A medida que vale é **a ponta acima da placa**.

**Segunda opção, se nenhum encoder servir: knob de 10 mm** (+3 mm sobre o aprovado), com o eixo de 24,5 inteiro.
- Mesmo desenho "chapéu retrô" (saia, corpo, traço creme), só o corpo mais alto.
- Furo do knob com 9,5 mm de profundidade: a ponta do eixo fica 0,5 mm abaixo do topo.

**O que muda para o Code:** modelar as duas versões do knob (7 e 10 mm) e trocar o modelo do encoder pelo escolhido. Se a peça escolhida for outra, a eletrônica confere o footprint e o firmware (`ENC_STEPS_PER_DETENT`). A frase "cortar o eixo", da v5 e de qualquer manual, sai.

### 2. Grade: escareado só de fábrica (substitui o item 6 da v5)

O escareado da grade é feito pelo fabricante da placa da grade, **nunca em casa**:
- **JLCPCB (primeira opção):** oferece furo escareado cônico como serviço opcional do pedido. As regras da JLCPCB e as nossas medidas estão abaixo.
- **PCBWay (segunda opção, sem passar por casa):** se a JLCPCB recusar na revisão do pedido, a grade vai para a PCBWay, que lista furo escareado NPTH entre as capacidades (tolerância de ±0,2 mm para furos < 10 mm). Como a grade é uma placa separada, sem montagem, trocar de fábrica só para ela não muda nada na placa principal.

Regras da JLCPCB para o furo escareado, já atendidas pelo nosso desenho:
- só cone, em PTH ou NPTH;
- pelo menos 0,2 mm de placa abaixo do cone;
- a boca a pelo menos 0,2 mm de cobre, trilhas e ilhas;
- no pedido: diâmetro da boca e do furo, ângulo, tipo, lado e uma figura de onde ficam os furos.

Fonte: https://jlcpcb.com/help/article/countersink-hole-process (PCBWay: https://www.pcbway.com/capabilities.html)

**Especificação (a mesma da v5):** 10 furos NPTH Ø 2,3, boca Ø 3,8, 90°, pela face de cima, 0,75 de profundidade (sobram 0,85 dos 1,6). Cobre recuado até **Ø 4,4** em volta dos 10 furos, nas duas faces.

**Quanto ao risco:**
- A JLCPCB revisa o arquivo antes da produção e, se não puder fazer, avisa e devolve o valor. Não há risco de receber a grade sem escareado sem saber.
- Pedir a grade **junto com a placa principal**: se precisar ir para a PCBWay, ainda há tempo antes de montar.

**O que muda para o Code:**
- O `GRADE_ESCAREADA.md` perde a alternativa "escarear em casa" e ganha o texto pronto para os dois pedidos (JLCPCB e PCBWay), com a figura.
- A alternativa do "parafuso de cabeça baixa sobre furo liso" continua fora (não cabe sob a tampa).

## Tarefas para o Code

1. **[Design]** Procurar o encoder de eixo de 15 mm nas condições do item 1. No FIT_CHECK: código, fabricante, distribuidor, estoque, ponta acima da placa, comprimento do chato e se o footprint é o mesmo. Se não houver, dizer por quê e seguir com o knob de 10 mm.
2. **[Design]** Knob nas duas versões (7 mm para o eixo de 15; 10 mm para o eixo de 24,5), com renders das duas lado a lado no isométrico.
3. **[Eletrônica]** Só se o encoder escolhido não for o EC11E: conferir o footprint, os pinos (A, B, C, chave) e `ENC_STEPS_PER_DETENT`, e atualizar a lista de compras.
4. **[Design]** `GRADE_ESCAREADA.md`: textos dos pedidos na JLCPCB e na PCBWay, a figura (planta + corte) e o cobre recuado até Ø 4,4 no arquivo da grade. Nada de escarear em casa.
5. Tudo o mais da v5 (tarefas 1 e 3 a 9 dela) continua valendo. FIT_CHECK.md terminando com "Perguntas para o design".

---

# Anexo — SPEC v5 (referência; os itens 2 e 6 foram substituídos acima)


Data: 18 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code
Responde ao FIT_CHECK do ciclo 4 (`student_v03/case/FIT_CHECK.md`, PR #166) e ao `PROMPT-CHAT-SPEC-V5.md` (PR #167).
Canvas do conceito: https://claude.ai/artifact/2xeBWDz7PnhAhXUK7pcHGy

Tudo o que não é mencionado aqui continua como na **SPEC v4** (anexo abaixo) e no modelo do PR #166.

## Resumo das decisões

| Achado | Decisão |
|---|---|
| A. Tampa de 0,51 mm sobre a grade na frente e no fundo | **Chanfro de 4,0 × 3,5 nos quatro lados** (antes 6,0 × 3,5). Não só na frente e no fundo: o chanfro continua igual em volta toda, e isto também resolve o achado E. |
| B. Eixo do encoder com 24,5 mm | **Protótipo: cortar o eixo em 20,0 mm**, se a parte chata do eixo continuar com ≥ 4 mm depois do corte. Se não continuar, o knob cresce 3 mm. **Série:** procurar um encoder de eixo mais curto com o mesmo footprint. |
| C. Bandeja cedendo no ar | **Prateleira interna na tampa + pés de borracha sob os pinos e os pilares.** A carga das teclas vai direto para a mesa. |
| D. Caixa acústica de 9,75 cm³ | **Aceita.** 0,3–0,4 dB não se ouve num alto-falante de 28 mm. A manta acústica fica como teste opcional no protótipo. |
| E. Postes da tela a 0,06 mm do chanfro do teto | **Resolvido pelo item A:** com o chanfro de 4,0, o teto fica plano a partir de ~4,8 mm da parede. Módulo, janela e postes ficam onde estão. |
| Grade escareada | **Pedir à JLCPCB**, que oferece furo escareado cônico como serviço opcional. Se recusar, escarear em casa. |
| Boca do J401 | **A confirmar na amostra** (item 7). |

---

## Mudanças desde a v4

### 1. Chanfro da borda superior: 4,0 × 3,5 nos quatro lados (achado A)

- O chanfro passa de 6,0 × 3,5 (30°) para **4,0 × 3,5 (~41°)**, igual nos quatro lados. As duas arestas continuam com **R 1,5**.
- Altura do chanfro igual: z 11,0 → 14,5. Os sulcos (4,3 / 6,5 / 8,7) e tudo abaixo deles não mudam.
- O chanfro interno da tampa acompanha o externo, com a parede de 2,0 medida na normal.
- **Resultado esperado:**
  - a tampa sobre a borda da grade, na frente e no fundo, volta a ter ~1,4 mm, e as cabeças escareadas ficam escondidas, como pede a SPEC v1;
  - o teto interno fica plano a partir de ~4,8 mm da parede, e não 6,5 (ver item 5).
- **Por que nos quatro lados, e não só na frente e no fundo:**
  - o chanfro igual em volta toda é parte do conceito aprovado;
  - dois chanfros diferentes se encontrariam nos cantos de R 9 com uma transição torta, difícil de modelar e de ver.
- **Não muda:**
  - **logo:** começa em x 8,6 e fica no plano, ainda mais longe do chanfro;
  - **faixas Retrô:** continuam sobre o tampo, o chanfro e a parede da frente;
  - **legendas OUT/IN:** ficam na parede, abaixo dos sulcos.
- **Medida mínima:** a tampa sobre a grade precisa de **≥ 1,2 mm** em qualquer ponto, inclusive na transição do R 1,5. Se der menos, voltar com o número antes de mudar o chanfro.

### 2. Encoders: eixo de 24,5 mm (achado B)

O EC11E18244AU tem o eixo de 24,5 mm acima da placa, 3,0 mm acima do topo do knob (z 21,5).

- **Protótipo:** o J corta o eixo em **20,0 mm acima da face de cima da placa**, sem trocar a peça. O knob de 7 mm encaixa 4,7 mm.
  - **Condição:** a parte chata (o "D") do eixo tem de continuar com **≥ 4 mm** depois do corte, para o knob não girar em falso. O Code mede no modelo do EasyEDA ou no desenho da Alps quanto do eixo é chato a partir da ponta (pergunta C1).
  - Se o chato tiver menos que 8,5 mm (4,5 de corte + 4 de encaixe), **não cortar**: o knob passa a ter **10 mm** de altura (+3), com o mesmo desenho "chapéu retrô" esticado no corpo e a mesma saia. O Code modela as duas versões de knob e diz qual vale.
- **Como o J mede e corta** (vai para o manual de montagem):
  1. Encoder soldado. Medir com o paquímetro da face de cima da placa até a ponta do eixo: deve dar 24,5.
  2. Marcar 20,0 a partir da placa, ou seja, 4,5 a partir da ponta.
  3. Cortar com uma serra de arco pequena, segurando o eixo com um alicate entre o corte e a bucha, para o esforço não ir para o encoder. Limar a rebarba.
  4. Conferir 20,0 ± 0,2.
  - O corte se faz **antes** de soldar o encoder, se der. Com a peça solta, o eixo vai preso numa morsa com mordente de madeira.
- **Série (registro para depois, não é tarefa agora):** procurar um EC11E vertical de eixo curto (ponta a ~20 mm da placa), com o mesmo footprint, a mesma bucha, clique e 18/36. Tarefa de eletrônica quando a V3 for para série.

### 3. Bandeja: prateleira na tampa e pés sob os apoios (achado C)

A placa só fica dentro da meta (≤ 0,05 mm a 3 N) com apoios rígidos. O que faltava era dar à bandeja esse apoio rígido. Ficam as duas medidas juntas:

- **Prateleira interna na tampa:** um ressalto de **1,5 mm de largura × 1,0 mm de altura** na base da parede, por dentro (z −10,1 … −9,1), a volta toda.
  - A bandeja ganha um **rebaixo na borda** que se assenta nele. A face de baixo da bandeja continua **rente** à borda da tampa, entre os ressaltos.
  - A prateleira fica bem abaixo dos furos dos conectores (boca mais baixa: −7,75), então não precisa de interrupção.
  - De baixo, aparece um aro creme de 3,5 mm (parede + prateleira) em volta da bandeja cinza.
- **Pés de borracha:** pés autoadesivos de silicone, **Ø 8 × 1,5 mm**, num rebaixo de Ø 8,4 × 0,5 na face de baixo da bandeja. Ficam 1,0 mm para fora.
  - **Sob os 4 pinos e os 3 pilares:** H5 (98,45; 52,67), H6 (153,95; 31,31), H7 (153,95; 63,35), H8 (209,45; 52,67) e (127,5; 32,5), (182,5; 62,5), (182,5; 32,5).
  - **2 à esquerda:** em ~(22; 10) e ~(22; 90). Afastar o que for preciso dos alojamentos de cabeça de parafuso e do rebaixo do H101.
  - Os pés levam a força de cada tecla direto à mesa. A tampa fica 1,0 mm acima da mesa e não balança.
- **Meta, com o case sobre uma mesa rígida:** a pior tecla com **≤ 0,05 mm a 3 N**, somando placa e bandeja. Os pés entram como apoios rígidos no estudo.
  - Registrar também o caso sem mesa, com o case no colo, só para informação.
- As nervuras ficam como estão (grade de 12 mm, topo em −4,0). Se o estudo mostrar que com os pés elas podem ser mais baixas ou mais esparsas, o Code propõe (menos material, mais volume livre).

### 4. Caixa acústica: 9,75 cm³ aceitos (achado D)

- Fica como modelada no ciclo 4, com o bloco alto à esquerda do anel.
- **Manta acústica opcional:** enchimento solto de poliéster, cerca de metade do volume. Fica como teste de ouvido no protótipo, e o manual cita como opcional.
- Nada de mover a bateria ou a tela por isso.

### 5. Postes da tela (achado E)

- Com o chanfro de 4,0 (item 1), os postes de trás (y 8,2, raio 1,6) ficam a ~1,8 mm do início do teto plano.
- **Não mover** o módulo, a janela nem os postes. Conferir a nova folga (pergunta C4).

### 6. Grade: escareado na JLCPCB

A JLCPCB faz furo escareado cônico, em PTH ou NPTH, como serviço opcional do pedido de placa. Regras:
- tem de sobrar pelo menos 0,2 mm de placa abaixo do cone;
- a boca do cone tem de ficar a pelo menos 0,2 mm de cobre, trilhas e ilhas;
- no pedido se informam o diâmetro da boca, o do furo, o ângulo, o tipo (NPTH), o lado e uma figura de onde ficam.

Fonte: https://jlcpcb.com/help/article/countersink-hole-process

- **Nossos 10 furos:** NPTH Ø 2,3, boca Ø 3,8, **90°**, pela face de cima, 0,75 de profundidade. Sobram 0,85 mm dos 1,6, mais que o mínimo de 0,2.
- **Mudança no arquivo da grade:** o cobre sob a máscara hoje recua 0,5 mm do furo (até Ø 3,3) e entraria no cone. Recuar o cobre em volta dos 10 furos até **Ø 4,4** (boca de Ø 3,8 + 0,2 + margem), nas duas faces.
- **Pedido:** escrever na observação do pedido a especificação acima e anexar a figura (planta com os 10 furos marcados + corte de um cone). O Code gera a figura.
- **Se a JLCPCB recusar ou cobrar caro demais:** o J escareia em casa com uma broca escareadora de 90° (Ø ≥ 4), na furadeira de bancada com batente. Profundidade de 0,75: a cabeça do parafuso fica rente. Testar antes num pedaço de FR-4 que sobrar.
- O cone fica sob a tampa, e o FR-4 aparente ali não se vê.

### 7. Pendências que dependem de peça real

- **J401, boca do conector:** fica **a confirmar na amostra**. Se a boca não abrir para a fenda (para y menor), o cabo faz uma curva em U de raio ≥ 2 mm sob a placa: com 50 mm de cabo e ~21 de percurso, sobra comprimento.
  - **Como o J confere:** na placa montada, olhar o J401 por baixo. Anotar se a abertura, onde entra o plugue, aponta para a fenda (para o fundo do case) ou para o músico.
- **Encoders:** comprimento do eixo e do chato (item 2), com o paquímetro.
- **Alturas do USB-C e dos jacks, frente das tomadas e pilha do H101:** como na v4, pelo cupom da parede.
  - O jack XUNPU do modelo do EasyEDA dá o eixo em −4,1 e o fundo em −6,6 (a SPEC usava −4,0 e −6,3). **Manter `JACK_Z = −4,0`** até a amostra: o furo Ø 6,5 aceita 0,1 de diferença.
  - A folga da bandeja até o fundo do jack, com o −6,6, ainda é ≥ 1,0. O Code confirma (pergunta C5).

### 8. Logo

Continua "eTUTTI" + "STUDENT · V2" (decisão do J de 18 nov: o texto final muda só na última versão). Não é mais uma pergunta em aberto.

---

## Tarefas para o Code

1. **[Design]** Chanfro superior de 4,0 × 3,5 nos quatro lados, com R 1,5 nas duas arestas e o chanfro interno acompanhando (item 1). A tampa sobre a grade com ≥ 1,2 mm em todos os pontos, sem corte na tampa para a grade passar.
2. **[Design]** Knob: confirmar o comprimento do chato do eixo. Modelar o knob de 7 mm (eixo cortado em 20) e o de 10 mm (eixo inteiro). Dizer qual vale (item 2).
3. **[Design]** Prateleira de 1,5 × 1,0 na tampa e rebaixo na borda da bandeja; bandeja rente à borda da tampa (item 3).
4. **[Design]** 9 pés: rebaixos de Ø 8,4 × 0,5 na bandeja, nas posições do item 3. Os pés entram no modelo como peça (`pe.stl`, Ø 8 × 1,5).
5. **[Design]** Estudo de flexão com a bandeja sobre os pés (mesa rígida) e, para informação, no colo. Meta ≤ 0,05 mm a 3 N, placa + bandeja. Propor nervuras mais leves, se der.
6. **[Design]** Arquivo da grade: cobre recuado até Ø 4,4 em volta dos 10 furos, nas duas faces. Figura do escareado para o pedido (planta + corte) em `case/GRADE_ESCAREADA.md`, com o texto pronto para a observação do pedido na JLCPCB (item 6).
7. **[Design]** `fit_check.py` e `fit_extra.py` de novo, com a medida da tampa sobre a grade em toda a volta.
8. **[Design]** Renders: isométrico e comparação v4 × v5 (mesmo ângulo), corte pela frente (y ≈ 95) mostrando a tampa sobre a grade, vista de baixo (bandeja, aro e pés).
9. FIT_CHECK.md atualizado, terminando com "Perguntas para o design".

## Perguntas para o Code (medidas a conferir no modelo)

- **C1.** Comprimento da parte chata do eixo do EC11E18244AU, a partir da ponta (modelo do EasyEDA, desenho da Alps). Quanto sobra de chato com o corte em 20,0?
- **C2.** Espessura mínima da tampa sobre a grade em toda a volta, com o chanfro de 4,0, e onde ela fica.
- **C3.** Flexão: pior tecla sobre os pés (mesa) e no colo; quanto a bandeja soma em cada caso.
- **C4.** Folga dos postes de trás da tela até o início do teto plano, com o chanfro de 4,0.
- **C5.** Folga da bandeja (borda e piso) ao fundo dos jacks com o −6,6 do modelo do XUNPU.
- **C6.** O cobre recuado da grade até Ø 4,4 encosta em alguma coisa do desenho da grade, como contorno, furos das teclas ou texto?

## Depende de amostra física

- Comprimento real do eixo e do chato dos encoders (item 2).
- Boca do J401 (item 7).
- `USB_Z`, `JACK_Z`, frente das tomadas e pilha do H101: pelo cupom da parede, como na v4.
- Pés: a dureza do silicone e a altura real depois de colados (~1,5).

---

# Anexo — SPEC v4 (referência)


Data: 18 nov 2026 · Autor: Claude Chat (design) · Destino: Claude Code
Responde a `student_v03/CASE_IMPACTO.md`, às 3 perguntas do FIT_CHECK do ciclo 3 da V2 e às respostas do J de 18 nov (itens 12 e 13).
Canvas do conceito: https://claude.ai/artifact/2xeBWDz7PnhAhXUK7pcHGy

**Base deste ciclo:** o modelo da V2 (SPEC v3 + FIT_CHECK do ciclo 3) e a placa V3 (`kicad/student_v03.kicad_pcb`).
Copiar `student_v02/case/` para `student_v03/case/` e trabalhar só na cópia: **a V2 não muda**.
Tudo o que não é mencionado aqui continua como na SPEC v3, v2 e v1 (anexos da `student_v02/SPEC.md`).

Coordenadas como sempre: x para a direita (0–252), y para o músico (0–100), **z = 0 no topo da placa**, placa de 1,2 mm
(fundo em z = −1,2), case de z −10,1 a **14,5** (o tampo desce 3,7 mm, item 12).

---

## Resumo das decisões

| Pergunta do Code | Decisão |
|---|---|
| 1. Furos de USB-C e jacks | **Tirar a divisão base/tampa da parede.** A tampa desce até z −10,1 e a base vira uma **bandeja de fundo** embutida nela. Os três furos ficam inteiros na tampa, **fechados**, como na V2. |
| 2. Ordem de montagem | **Igual à da V2:** tampa de cabeça para baixo, a placa entra por cima nela, e o fundo fecha. As tomadas pendem para o lado aberto e não cruzam a parede. |
| 3. "Base do teclado abaixo do case" | **Resposta do J: o teclado fica mais exposto, sem uma borda do case no caminho dos dedos.** O poço passa de 5,25 para **1,55 mm**: o tampo desce 3,7 mm (z 18,2 → **14,5**) e o case passa de 28,3 para **24,6 mm** de altura. Teclas, grade e botões não mudam (item 12). |
| 4. Cabo da tela | **Módulo OLED girado 180°** (pinos para a frente, logo acima da fenda). Cabo JST SH de 4 vias de **50 mm**, com os fios soldados no módulo. Os 15 mm do resumo não chegam. |
| 5. Fundo | Alívio para a porca e o parafuso do H101. A **bateria vai 6,5 mm para a direita**, porque na posição da V2 ela bate no jack IN. Alto-falante sem mudança de lugar. |
| 6. Simplificações | Fundo plano sem aba nem parede; nenhuma emenda nas paredes; knob sem luva (o eixo de 20 mm agora chega ao knob); poço sem aba. |

---

## Mudanças desde a v3

### 1. Divisão base/tampa: sai da parede (opção recomendada entre as três estudadas)

Faixa vertical que os furos ocupam na parede esquerda, já com o chanfro de 0,5 da boca: **z −7,75 … +1,1**.

| Opção | Resultado | Decisão |
|---|---|---|
| A. Plano em −4,0, meio furo em cada peça | Emenda atravessando os três furos e degrau na entrada do plugue quando as peças não casam. A aba da base passaria exatamente onde ficam as tomadas. O J recusou emendas na parede esquerda na SPEC v2. | Não |
| B. Plano acima dos furos (z ≈ +2) | Base alta e rígida, montagem natural. Mas a faixa cinza sobe para 12 mm (de 28,3), muda a proporção aprovada do Retrô, e as legendas ficam no cinza. Só sobra 0,9 mm de material acima da boca do USB-C. | Não |
| **C. Plano no fundo: bandeja embutida na tampa** | Os furos ficam inteiros numa peça creme, com a mesma geometria já conferida na V2 (recuo de 0,3, chanfro, limites de plugue). **As quatro paredes ficam sem emenda.** A montagem é a mesma da V2. Custo: o fundo perde as paredes e precisa de borda e nervuras para continuar rígido (item 6). | **Sim** |

Geometria:

- **Tampa:** de z **−10,1** a **14,5** (item 12), paredes de 2,0. A quina inferior externa passa a ser da tampa: chanfro de 1,5, como o da base da V2.
- **Fundo (bandeja):** placa de 2,0 (z −10,1 a −8,1, a mesma altura do piso da V2) que entra na tampa com 0,15 de folga por lado. A face de baixo fica rente à borda da tampa, podendo ficar até 0,3 recuada e **nunca saliente**, para o case apoiar sempre na borda da tampa.
- Saem a aba da base que entrava na tampa (`LIP_*`) e o plano `Z_SPLIT`.

### 2. Furos dos conectores: fechados, novas alturas

| Furo | Centro / eixo | Faixa do furo | Faixa da boca (chanfro 0,5) |
|---|---|---|---|
| USB-C 12,8 × 7,0, R 3,5 (y 16,0) | z **−2,9** | −6,4 … +0,6 | −6,9 … +1,1 |
| OUT Ø 6,5 (y 36,0) | z **−4,0** | −7,25 … −0,75 | −7,75 … −0,25 |
| IN Ø 6,5 (y 60,0) | z **−4,0** | −7,25 … −0,75 | −7,75 … −0,25 |

- Continuam **fechados**: a frente das tomadas fica 0,3 atrás da face interna da parede (x das peças não mudou). Os limites de plugue continuam os da V2: corpo até 12,35 × 6,5 no USB-C e Ø 6,4 no P2.
- Abaixo da boca dos jacks sobram 0,85 mm de parede reta até o chanfro inferior (z −8,6) e 2,35 mm até a borda. Conferir (pergunta C7).
- Os valores de z são estimados (a V2 espelhada em torno da placa). Ficam como parâmetros (`USB_Z`, `JACK_Z`) para mudar só esse número quando houver amostra (seção 11).

### 3. Acabamento Retrô: a faixa cinza da parede sai

Sem divisão na parede, não há mais a peça cinza de z −10,1 a −4,0.

- **Padrão deste ciclo:** a tampa é **creme até embaixo** (o chanfro inferior também) e **só a bandeja do fundo é cinza** (#9C9B96). De lado, o case fica um bloco creme único.
- As faixas vermelha, laranja e amarela descem pela parede da frente **até o chanfro inferior** (antes iam até −4,0).
- **Alternativa para o J (seção 12):** pintar de cinza só o chanfro inferior de 1,5 mm, como uma "sola". Não pintar uma faixa até −4,0: a linha de cor passaria pelo eixo dos jacks e pareceria a emenda que foi recusada.

### 4. Legendas OUT e IN

- Mesmo lado de cada furo e mesma fonte, altura (2,0) e tinta (#2B2925) da v3.
- **Centradas no eixo dos jacks:** z −5,0 a −3,0 (antes 1,8 a 3,8).
- **Começam 1,8 mm depois da borda do furo** (antes 1,3), ou seja, 1,3 mm depois da boca chanfrada. Isto responde à pergunta 2 do FIT_CHECK.

### 5. Ordem de montagem

1. **Placa:** soldar os 2 encoders em casa. Encaixar o módulo MicroMod e prendê-lo no H101 (parafuso pelo topo, espaçador, módulo, porca, ver item 8). Colocar as teclas Gateron.
2. **Grade de FR-4:** 10 × M2 × 16 com espaçadores de 11,35 e porcas por baixo, como na V2. Depois os botões nas hastes.
3. **Cabo da tela:** encaixar o pigtail no J401 (fundo) e passar os fios soltos **de baixo para cima pela fenda**. O conector não passa na fenda de 2,5 mm. Soldar os fios no módulo OLED e prender um pouco de cola quente sobre as soldas, para aliviar a tensão.
4. **Tampa (de cabeça para baixo):** colar o acrílico. Prender a caixa acústica com o alto-falante (2 × M2 × 5) e soldar os fios no J501. Prender o módulo OLED nos 4 postes. Com isso a placa já está presa à tampa pelos fios, que têm folga para isso.
5. **Placa na tampa:** descer a placa, com o topo para baixo. Os botões passam pelo poço e os eixos dos encoders pelos furos dos knobs. As tomadas pendem para o lado aberto, sem cruzar a parede, e terminam alinhadas aos furos. Na V3 isso continua funcionando porque nenhuma peça passa à frente da face interna da parede.
6. **Bateria** no berço da bandeja, ligada ao J202.
7. **Fundo:** 6 × M2 × 14 nos mesmos lugares da V2 (H1–H4, H9, H10), não ferrosos perto dos sensores, como antes.
8. **Knobs** nos eixos.

**Para trocar o módulo MicroMod** (operação rara): tirar o fundo, desligar o J401 e a bateria, tirar os knobs, levantar a placa uns 3 cm (os fios do alto-falante e da tela seguram) e soltar os 4 parafusos do módulo OLED. A placa sai inteira e o parafuso do H101 fica acessível pelo topo. É uma limitação aceita. Fica a nota para uma próxima placa: uma porca SMD no topo, soldada em casa, permitiria soltar o módulo só tirando o fundo.

### 6. Bandeja do fundo: rigidez e o que ela carrega

O que já existia continua igual: bossas dos 6 parafusos, copos das porcas da grade, 4 pinos Ø 5 com ponta e 3 pilares Ø 4 sob o teclado, e o furo de acesso ao botão Program em (52; 36).

O que muda:

- **Borda (bandeja rasa):** aba de 1,2 de espessura junto à parede interna da tampa, com o topo em z −6,6.
  - **Nas três zonas dos conectores** (y 9–23, 30–42 e 54–66), o topo da aba baixa para **z ≤ −7,6**. Assim ela fica pelo menos 1,3 abaixo dos jacks e fora do caminho do plugue.
  - A aba também posiciona a bandeja na tampa.
- **Nervuras:** sob a área do teclado, só onde o estudo de flexão pedir. O topo delas fica em z ≤ −4,0, pelo menos 2 mm abaixo das peças do fundo, com o espaço livre conferido contra o CPL da V3.
- **Rigidez:** a meta continua **≤ 0,05 mm a 3 N** na pior tecla. A V2 chegava a 0,049 com a base de parede alta; uma placa de 2 mm sozinha não chega.
  - Se borda e nervuras não bastarem, o Code propõe 2 a 4 parafusos extras bandeja ↔ tampa, em bossas na parede da tampa abaixo da placa, sem atravessar a placa.
- **Alívio do H101:** rebaixo de Ø 8 × 1,0 no piso, sob (47,5; 14,0): o piso fica com 1,0 ali (item 8).

### 7. Tela: módulo girado e cabo

- **Girar o módulo OLED 180°**, com a borda dos pinos para a frente.
  - O centro do módulo passa para (37,0; **20,1**): é o centro da janela menos os 1,9 mm de deslocamento da área ativa.
  - O módulo ocupa y ≈ 6,2 … 34,0 e os postes ficam em (37 ± 11,65; 20,1 ± 11,9). A janela, o acrílico e o filete não mudam.
  - Os pinos ficam em y ≈ 32,5, logo à frente da fenda (y 29,9 … 32,4, x 32 … 39). Os fios descem quase em linha reta: uns 9 mm do módulo até a placa (com o teto em 12,5, item 12), mais 1,2 da fenda e uns 3 mm até o J401. Sem o giro, os fios teriam de passar por baixo do módulo inteiro até os pinos, em y ≈ 11.
  - **Firmware:** girar a imagem 180° (`setRotation(2)` / remapeamento de segmento e COM do SSD1306). Registrar nas notas da firmware.
- **Cabo:** pigtail JST SH de 4 vias, **50 mm** (comprimento padrão Qwiic), conector no J401 e fios soldados direto nas ilhas do módulo, **sem barra de pinos**.
  - O percurso mínimo é de uns 20–25 mm. O resto é a folga para a etapa 4 da montagem, dobrada no vão de ~9 mm entre a placa e o módulo, sem tocar os encoders.
- **Raio de curvatura:** não é crítico, porque são fios soltos de 28–30 AWG e não um cabo flat. Basta ≥ 2 mm, sem dobrar os fios na borda da fenda.
- **Suporte:** nenhuma peça a mais. Só a cola quente sobre as soldas do módulo.

### 8. Fixação do módulo MicroMod (H101)

- Pilha, de cima para baixo: parafuso **M2,5 × 8 de nylon** pelo topo, placa (1,2), espaçador de nylon (2,5), módulo (1,0), **porca M2,5 de nylon** (2,0).
- A porca vai até z ≈ −6,7 e a ponta do parafuso até ≈ −8,0. O rebaixo de 1,0 do item 6 deixa 1,1 de folga.
- Se o Code achar M2,5 × 7, a ponta para em −7,0 e o rebaixo pode sair. Com M2,5 × 6 a porca não pega a rosca inteira.

### 9. Bateria: muda de lugar

Na posição da V2 (x 13–63, y 56–90, z −8,1 a −2,9) a bateria **ocupa o espaço do jack IN**. O J302 agora está no fundo, com corpo até x ≈ 16,9 entre y 54,9 e 65,2, e desce até z ≈ −6,3.

- **Nova posição:** x **19,5 … 69,5**, y 56 … 90, mesma altura. As nervuras do berço vão junto.
- Por cima ficam U501, C502 e R501 (fundo). O C501 fica logo atrás, em y ≥ 90,6. Conferir a folga (pergunta C4).
- O cabo de 3 fios vai até o J202 (fundo, em (64,5; 26,5)) pelo piso, preso nas nervuras do berço.

### 10. Caixa acústica: o que a V3 libera

O topo da placa sob a caixa e à esquerda dela ficou vazio: os jacks e o J401 saíram dali.

- **Piso da caixa:** pode descer de z 0,8 para 0,3 (0,3 acima das trilhas e das ilhas do topo).
- **Ampliação (obrigatória com o teto em 12,5, item 12):** estender a caixa para a esquerda até x ≈ 5. É livre por dentro sob o logo, entre o poste do H3 (y 48,5) e o do H4 (y 91,5), respeitando o plano interno do chanfro. A meta é **≥ 10,4 cm³** (a V2), de preferência 12 ou mais.
  - Refazer `acustica.py` com o volume final: ressonância e nível em 262 e 523 Hz.
  - Se não chegar a 10,4 cm³, voltar com as alternativas antes de mexer no tampo.

### 11. Respostas ao FIT_CHECK do ciclo 3 (V2)

1. **"STUDENT · V2" com traço de 0,15:** engrossar para **0,20 mm**. Medir de novo e manter **1,4 mm livres** até o "eTUTTI" na borda das letras novas. O texto em si é a pergunta J2 da seção 12.
2. **"OUT"/"IN":** afastar, sim. Já está no item 4 (começo a 1,8 da borda do furo).
3. **Manual:** o limite de plugues vai só no manual da Student. Os manuais do eTuttino não mudam.

### 12. Poço raso: o teclado fica exposto (resposta do J à pergunta 3)

O J quer o teclado mais exposto, **sem uma borda do case no caminho dos dedos até as teclas**: se houver rebaixo, de 1 a 2 mm.

**Como:** o tampo inteiro desce 3,7 mm, de z 18,2 para **z 14,5**. Teclas, grade (z 11,35 … 12,95) e botões ficam onde estão, e **o poço passa de 5,25 para 1,55 mm**. O case continua com altura fixa e uniforme, agora de **24,6 mm** (z −10,1 … 14,5).

Por que assim e não subindo a grade (e os botões) até perto do tampo:
- a grade continua 0,15 acima dos alojamentos das teclas, que a seguram quando um dedo aperta fora do botão (estudo de flexão da V2 válido);
- os botões, as hastes e a altura dos botões em relação à placa não mudam;
- o instrumento fica 3,7 mm mais baixo, em vez de 3,7 mm mais alto.

| Medida | v3 (V2) | v4 |
|---|---|---|
| Tampo (z) | 18,2 | **14,5** |
| Altura do case | 28,3 | **24,6** |
| Teto interno da tampa (tampa de 2,0) | 16,2 | **12,5** |
| Profundidade do poço (tampo até a grade) | 5,25 | **1,55** |
| Topo dos botões acima do tampo, fileiras 1–4 | 3,7 / 5,7 / 7,7 / 10,7 | **7,4 / 9,4 / 11,4 / 14,4** |
| Altura total com os botões (fileira 4) | 39,0 | 39,0 (igual: só o tampo desceu) |
| Chanfro da borda superior | 6,0 × 3,5, z 14,7–18,2 | **6,0 × 3,5, z 11,0–14,5** |
| Sulcos (centros) | 8,0 / 10,2 / 12,4 | **4,3 / 6,5 / 8,7** |

**Borda do poço**
- A tampa sobre a borda da grade fica com **1,4 mm** (14,5 até 13,1, 0,15 acima da grade). Fora dessa faixa a tampa continua com 2,0.
- A aba que formava a parede do poço desaparece: a própria tampa fina é a parede.
- A aresta de cima do poço fica com **R 1,2**, sem quina viva no caminho dos dedos. O R 2,5 da v1 não cabe em 1,55 mm.
- Em planta, o contorno do poço não muda (15,0 mm dos centros das teclas).

**Parafusos da grade:** não cabe mais a cabeça abaulada sob a tampa (sobram 0,15 mm).
- Passam a ser **M2 × 16 de cabeça escareada** (ISO 7046 / DIN 965, cabeça Ø 3,8), **rentes à face da grade**, em furos escareados a 90° na grade de FR-4. A JLCPCB faz furo escareado em placa: pedir no pedido da grade.
- Mesma pilha da V2: espaçador de 11,35, placa e porca no copo da bandeja. O M2 × 16 escareado mede 16 da face da cabeça: sobram os mesmos 0,25 além da porca.
- Continuam não ferrosos (latão ou inox A2), como todos os parafusos perto dos sensores.

**Área de interface com o teto em 12,5**
- **Tela:** o módulo desce junto com o teto (vidro 0,1 abaixo do ressalto do acrílico, como antes). O fundo do módulo fica em z ≈ 9,3, e o caminho dos fios fica uns 4 mm mais curto. O cabo de 50 mm continua (item 7).
- **Encoders:** o eixo de 20 mm termina 5,5 acima do tampo, então o knob (7 mm) encaixa 5,5 mm direto no eixo. **A luva do knob deixa de ser necessária:** o knob volta a ser uma peça simples. Ver C10.
- **Alto-falante:**
  - o alto-falante desce junto com o tampo e a caixa acústica fica mais baixa;
  - a ampliação para a esquerda do item 10 passa a ser **obrigatória**;
  - meta: **pelo menos os 10,4 cm³ da V2**, de preferência 12 ou mais.
- **Postes** dos parafusos da tampa e da tela: mais curtos, mesma posição.
- **Parede esquerda:** a faixa lisa vai de z −8,6 (chanfro inferior) a 3,9 (borda de baixo do sulco mais baixo). Os furos (até +1,1) e as legendas (−5,0 … −3,0) cabem, com 2,8 mm livres acima da boca do USB-C.
- Logo, janela, filete, knobs e grade do alto-falante: **as mesmas posições em planta** sobre o tampo novo.

### 13. Respostas do J sobre o logo e as cores

- **Logo:** fica como está ("eTUTTI" + "STUDENT · V2"). O texto final muda só na última versão. Neste ciclo vale apenas o traço de 0,20 do item 11.
- **Fundo e cores:** aprovado o padrão do item 3 (tampa creme até embaixo, só a bandeja cinza). As cores serão estudadas no case final, depois de testar o protótipo. **O que importa agora é a parte física do case.**

---

## Valores que mudam em relação à v3

| Item | v3 (placa V2) | v4 (placa V3) |
|---|---|---|
| Divisão base/tampa | plano em z −4,0, a volta toda | **nenhuma na parede**: tampa de −10,1 a 14,5; bandeja de −10,1 a −8,1 (+ borda até −6,6) |
| Base | peça cinza com parede e aba | **bandeja plana com borda**, embutida na tampa |
| Quina inferior (chanfro 1,5) | na base | **na tampa** |
| USB-C, centro do furo | z +1,7 | **z −2,9** |
| OUT e IN, eixo do furo | z +2,8 | **z −4,0** |
| Legendas OUT/IN | z 1,8–3,8, a 1,3 do furo | **z −5,0 … −3,0, a 1,8 do furo** |
| Cor da parede | creme acima de −4,0, cinza abaixo | **creme até embaixo**; só o fundo é cinza |
| Faixas Retrô na parede da frente | até −4,0 | **até o chanfro inferior** |
| Módulo OLED | pinos para trás, centro y 23,9 | **girado 180°**, centro y 20,1 |
| Cabo da tela | no topo | **pigtail JST SH de 50 mm**, fios soldados no módulo, pela fenda |
| H101 | espaçador SMD | **M2,5 × 8 nylon + espaçador 2,5 + porca nylon**; rebaixo Ø 8 × 1,0 no fundo |
| Bateria | x 13–63 | **x 19,5–69,5** (y 56–90 igual) |
| Caixa acústica | piso externo em z 0,8 | piso pode ir a 0,3; ampliada para a esquerda; **≥ 10,4 cm³** com o teto em 12,5 |
| Tampo / altura do case | 18,2 / 28,3 | **14,5 / 24,6** |
| Poço | 5,25, aba da tampa, borda R 2,5 | **1,55**, tampa de 1,4 sobre a grade, borda R 1,2 |
| Sulcos | 8,0 / 10,2 / 12,4 | **4,3 / 6,5 / 8,7** |
| Parafusos da grade | M2 × 16 cabeça abaulada | **M2 × 16 escareado, rente à grade**; grade com furos escareados |
| Knob | com luva que desce pelo furo | **sem luva**, preso direto no eixo |
| Traço do "STUDENT · V2" | ~0,15 | **0,20** |

---

## Tarefas para o Code

1. **[Design]** Copiar `student_v02/case/` para `student_v03/case/` e apontar `BOARD_JSON` e o resto para a placa V3. A V2 fica intacta.
2. **[Design]** Tampa até z −10,1 com o chanfro inferior de 1,5; tirar `Z_SPLIT`, a aba e a parede da base (itens 1 e 3).
3. **[Design]** Furos com as novas alturas parametrizadas (`USB_Z = −2,9`, `JACK_Z = −4,0`), fechados, com o chanfro de 0,5 na boca (item 2).
4. **[Design]** Bandeja do fundo com borda, rebaixos da borda nos conectores, nervuras, bossas, copos, pinos, pilares, furo do Program e rebaixo do H101 (itens 6 e 8).
5. **[Design]** Berço da bateria na nova posição (item 9).
6. **[Design]** Módulo OLED girado 180° e postes movidos; percurso do cabo modelado como um feixe de Ø 2 do J401, pela fenda, até os pinos (item 7).
7. **[Design]** Legendas OUT/IN no eixo dos jacks e 0,5 mais longe do furo; traço do "STUDENT · V2" com 0,20 (itens 4 e 11).
8. **[Design]** Faixas Retrô até o chanfro inferior; bandeja cinza, tampa creme inteira (item 3).
9. **[Design]** **Estudo de flexão** com a bandeja (meta ≤ 0,05 mm a 3 N). Se não fechar, propor os parafusos extras do item 6.
10. **[Design]** **Estudo acústico** da caixa ampliada (item 10).
11. **[Design]** `fit_check.py`, com a montagem do item 5:
    - placa descendo na tampa invertida, com as tomadas no fundo;
    - bandeja fechando sem tocar nas peças do fundo;
    - plugues no limite entrando até o batente.
12. **[Design]** **Cupom de teste da parede:** um STL com só os 25 mm da esquerda da tampa (os três furos e as legendas) e um pedaço da bandeja. Serve para imprimir e testar na primeira placa montada antes da tampa inteira.
13. **[Design]** Renders: parede esquerda, corte pelo eixo dos jacks (y 36), corte pela fenda da tela (x 35,5), corte pelas fileiras (o poço novo), vista de baixo da bandeja e isométrico. Um isométrico lado a lado com a v3, para o J ver o teclado exposto.
14. **[Design]** Tampo em z 14,5 (case de 24,6): chanfro e sulcos descem 3,7; poço de 1,55 com tampa de 1,4 sobre a borda da grade e aresta R 1,2, sem aba (item 12).
15. **[Design]** Parafusos da grade escareados: furos escareados no arquivo de fabricação da grade (`grade_fab.py`) e a nota para o pedido na JLCPCB (item 12).
16. **[Design]** Knob sem luva, encaixado direto no eixo de 20 mm; postes da tampa e da tela encurtados; módulo OLED no teto novo (item 12).
17. **[Design]** Botões: as mesmas peças da V2. Conferir só que nada da tampa nova encosta neles no curso inteiro.
18. FIT_CHECK.md novo em `student_v03/case/`, terminando com "Perguntas para o design".

## Perguntas para o Code (medidas a conferir no modelo)

- **C1.** Pelos modelos 3D do HRO TYPE-C-31-M-12 e do XUNPU PJ-327A: o ponto mais baixo de cada corpo, o centro e o eixo reais em z, e a posição em x da frente de cada um. Confirma o recuo de 0,3?
- **C2.** Folga entre a bandeja (piso e borda) e cada peça do fundo, com a menor medida e onde ela fica. Pior caso esperado: a porca e o parafuso do H101, os jacks sobre a borda rebaixada e os copos da grade.
- **C3.** Material da tampa abaixo da boca dos jacks e do USB-C até o chanfro inferior. Os 0,85 mm de face reta bastam na impressão (MJF/resina)?
- **C4.** Bateria na nova posição: folga até o J302 (x), até o U501, o C502 e o R501 (z) e até o C501 (y). Quero ≥ 0,5 em z.
- **C5.** Módulo OLED girado: folga até o plano interno do chanfro de trás (borda em y ≈ 6,2), até os encoders e até a cabeça do parafuso do H101. Os postes caem na parte plana do teto?
- **C6.** J401: para que lado abre a boca do conector? O feixe de fios sai na direção da fenda? Qual o comprimento real do percurso?
- **C7.** Estudo de flexão: deslocamento na pior tecla com a bandeja (com e sem nervuras) e a rigidez da bandeja entre os 6 parafusos.
- **C8.** Volume e ganho da caixa ampliada, e folga até o poste do H4 e até o plano interno do chanfro.
- **C10.** Encoders com o teto em 12,5: altura real do corpo e da bucha do EC11E18244AU. Se o corpo quadrado passar de z ≈ 12,0, a tampa ganha um rebaixo local por dentro em volta do furo do knob. A bucha pode entrar no furo Ø 9,2. Onde o eixo termina (20 ou 24,5, ver `ELETRONICA.md` da V2)? Se forem 24,5, o eixo passaria do topo do knob (z 21,5) e teria de ser cortado a ~20.
- **C11.** Caixa acústica com o teto em 12,5: volume e ganho em 262 e 523 Hz.
- **C12.** Tampa de 1,4 sobre a borda da grade: folga até as cabeças escareadas e até a grade; a faixa fina aguenta a impressão (MJF/resina)?
- **C13.** Folga lateral dos botões da 1ª fileira até a aresta R 1,2 do poço, apertados e soltos.
- **C9.** Peso e volume de material da tampa nova e da bandeja, comparados com a tampa e a base da V2 (para o custo de impressão).

## Depende de amostra física (primeira placa montada pela JLCPCB)

- **Altura real** do USB-C (centro) e dos jacks (eixo) no fundo. Os valores −2,9 e −4,0 são a V2 espelhada. Só se mudam `USB_Z` e `JACK_Z`, depois de testar o **cupom da parede** (tarefa 12).
- **Recuo de 0,3 até a parede:** a posição em x da frente das tomadas como a JLCPCB soldou (tolerância de colocação ±0,1–0,2).
- **Pilha do módulo MicroMod** com o espaçador de 2,5: a altura real da porca e do parafuso, e se o rebaixo do H101 é preciso.
- **Módulo OLED comprado:** posição das ilhas dos pinos, deslocamento da área ativa (o 1,9 mm é estimado) e espessura.
- **Bateria 503450 real:** medidas com a placa de proteção e o NTC, e o comprimento dos fios.
- **Encoders:** altura do corpo e da bucha, e comprimento real do eixo (C10).
- **Plugues reais** (USB-C e P2) contra os limites de 12,35 × 6,5 e Ø 6,4.
