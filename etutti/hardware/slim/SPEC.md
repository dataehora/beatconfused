# eTutti Slim — SPEC R13SL

## Mudanças desde a R12SL (25 nov 2026)

Resposta do J à sessão A4 (PR #236): **tudo aprovado.**

1. **Teclado 1,5 mm à direita (`KEY_DX`) e case de 247,0 × 89,1 mm: aceitos.** A placa principal fica como está no `main` (posicionamento da R9SL, **faixa de 22,2 mm**). Os números de faixa de 18,4 e 20,7 mm citados nas R10SL a R12SL **nunca valeram**. Esta revisão os substitui.
2. **Parede da guia de 0,615 mm (0,65 nos cantos), com alívio de 0,35 mm e 0,50 mm até o U9: aceita.** Fica registrada como risco a ensaiar no protótipo. Plano B: inserto de latão, sem mexer em mais nada.
3. **Modelo 3D do MKL02 (U102):** baixar do EasyEDA pelo código **C2056583** (MKL02Z32VFG4R, a mesma peça em fita, HUQFN16 3 × 3). Conferir que o encapsulamento do modelo bate com o footprint. A peça continua consignada da PJRC, porque o chip da loja vem sem o bootloader; o código serve só para o modelo.
4. **Regra de verificação (nova, vale para todas as sessões, por causa do erro das A2/A3):**
   - todo script que gera ou altera placa, modelo ou case **termina com código de erro (≠ 0)** quando falha ou não grava. Mensagens como `no free spot` passam a ser erro, não aviso;
   - antes de relatar um DRC, um fit check ou um número, o Code confere que **o arquivo lido foi gravado nesta execução** (data e hora) e lê a saída inteira do script, não só a última linha;
   - o relatório diz qual arquivo foi verificado e quando ele foi gravado.

   Os scripts que já existem (`posiciona_principal.py`, `posiciona_regua.py`, `etapas.py`, `case.py`, `fit_check.py`, `montagem.py`, `cena_*.py`) são ajustados a esta regra na sessão A5.
5. **Sessão B (BGA):** começa **depois** da A5, numa sessão nova do Code, sobre a placa principal do `main` com a **faixa de 22,2 mm** (§8.2, corrigida abaixo).

---


## Mudanças desde a R11SL (25 nov 2026)

Resposta do J à sessão A3 (PR #234): **tudo aprovado.**

1. **Faixa da principal: 20,7 mm, aceita.** A sessão B confirma no B2 se o escape do RT1062 cabe nela.
2. **Case encurtado para ~245,5 mm** (−2,5 mm, só à direita), com folga de ~3,35 mm entre a régua e a parede direita nas fileiras 1 e 3. Exterior aprovado pelo J. O Code ajusta para o valor redondo mais próximo que mantenha a folga ≥ 3,0 mm e informa o número final.
3. **Guia da porca: parede de 0,7 mm aceita, com um alívio de ~0,4 mm** na face da guia voltada para o U9. Assim a guia não encosta no chip com a tolerância de ±0,3 mm do MJF. Folga final guia–U9 ≥ 0,5 mm. O resultado vai para o `RESTRICOES_CASE.md`, com o teste no protótipo registrado como risco.
4. **Cabo FFC de 20 mm, mantido.** A barriga fica ~2 mm abaixo do tampo e a sobra de cabo facilita o encaixe com a régua fora.
5. **Modelos 3D:**
   - Cabo FFC, M2, porca e espaçador desenhados pelas medidas da norma: **aceitos**.
   - As peças da principal que estão em caixa (D101, D102, D201, D401, FB301, J202, L101, L102, Q201–Q209, SW403, U102, U103, U201, U302, Y102) ganham o **STEP do EasyEDA pelo código LCSC**, baixado em lotes pequenos com `curl` simples. A API recusa depois de ~15 consultas, então espere entre lotes.
   - O que não for obtido vai **listado ao J**, com o código LCSC e o fabricante, para ele fornecer.
6. **Sessão B (BGA):** a placa principal não muda com os itens 2 a 5. A sessão B pode **recomeçar já, a partir do `main` atual**, em paralelo com a sessão A4.

---


## Mudanças desde a R10SL (25 nov 2026)

Resposta do J à sessão A2 (PR #231). Fica decidido o item 1 abaixo, que substitui a fixação da R10SL. **As perguntas 2 (faixa da principal, 18,4 mm) e 3 (folga de 1,75 mm na parede direita) seguem em aberto.** O J decide as duas depois de ver o modelo de montagem do item 2.

1. **Fixação da régua: um M2 centralizado em cada ponta, igual dos dois lados** (corrigido pelo J no mesmo dia). Os parafusos servem principalmente para prender a régua ao case.
   - **Esquerda:** 1 × M2 no eixo (v = 0), entre a tecla 1 e o conjunto controlador + conector. A partir da ponta esquerda: J1 (FFC, boca para −x) → U9 com C9 e C10 → **M2** → tecla 1. J1 e o controlador ficam numa **ponta curta em balanço**, além do parafuso.
   - **Direita:** sai o par de M2 (v = ±3,6). Entra **1 × M2 no eixo (v = 0)**, logo depois da tecla 8, com a ponta da régua o mais curta possível.
   - **Montante (trilhos) de apoio:** **dos dois lados, os trilhos terminam exatamente no parafuso**, numa **guia centralizada** (ressalto no eixo com o bolso da porca), que fecha o montante da mesma forma compacta nas duas pontas. Nada da régua além dos parafusos se apoia na base.
   - **2 pontos no eixo por régua** posicionam a régua e não forçam nada se um dos furos for **oblongo ao longo da régua** (sugestão: redondo na esquerda, que fica perto do FFC, e oblongo na direita). O Code confirma ou propõe outra coisa.
   - **A régua deve ficar o mais curta possível nas duas pontas.** Informe:
     - o comprimento novo, comparado com a R9SL (167,5) e a R10SL (171,3);
     - quanto a faixa da principal recupera em relação aos 18,4 mm;
     - a folga nova até a parede direita.
   - **Informe, para a ponta em balanço:**
     - o comprimento dela;
     - a flecha estimada ao encaixar o FFC (empurrão de 5 N no J1);
     - se o FFC de 20 mm ainda alcança nas 4 fileiras.
   - **A grade:** diga se é presa pelos dois M2.
2. **Modelo 3D de montagem (pedido do J para decidir o que está pendente).**
   - **Base:** modelo 3D da caixa inferior (base) com trilhos, guias centralizadas, bolsos das porcas, baia da bateria e postes da principal.
   - **Sequência de montagem, uma imagem por passo,** sempre com modelos 3D realistas e detalhados:
     1. a base vazia, com as porcas nos bolsos;
     2. a principal e a bateria, se entrarem antes das réguas. O Code propõe a ordem e justifica;
     3. a 4. cada régua, **com o seu cabo FFC já conectado**, posicionada na base e **parafusada junto com a grade**, uma fileira por passo (fileira 1 a 4);
     4. por fim as **switches KS‑33D** encaixadas na grade e na régua, que fecham a montagem.
   - **Vistas:** cada passo em isométrico, mais dois detalhes, um da ponta esquerda (guia, M2, balanço) e um da ponta direita (2 M2). As teclas levam o nome da nota, conforme a regra do projeto.
   - **Modelos 3D:**
     - KS‑33D da Gateron;
     - conector FFC C3250113 e cabo FFC 8 vias;
     - M2 e porcas;
     - VARTA 523450;
     - placa principal pelo GLB do KiCad.
     Se faltar o modelo realista de alguma peça, **o Code avisa o J** e diz qual é, em vez de desenhar uma caixa.
   - Entregar também o **STEP da base** e um **STEP (ou GLB) do conjunto montado**, para o J girar o modelo.
3. **Sessão B (escape do BGA):** a placa principal mudou desde que a §8.2 foi escrita. A faixa caiu de 22,2 para 18,4 mm na R10SL e vai mudar de novo com o item 1. **A sessão B deve recomeçar a partir do `main` atual** (depois desta sessão A3, se ainda não tiver avançado além do B1). No B2, ela informa se o escape do RT1062 cabe na largura da faixa resultante e quanta folga sobra.
4. **Regra das imagens (R10SL item 4) continua valendo.** Corrigir também o título de `pcb/principal/img/planta_principal.png`, que ainda diz "SPEC R4SL".

---


## Mudanças desde a R9SL (25 nov 2026)

Resposta do J à sessão A (PR #228). A sessão B (escape do BGA, §8.2) segue como estava, em paralelo.

1. **Um parafuso em cada ponta da régua, simétricos** (corrigido pelo J no mesmo dia). **A lingueta não será usada.**
   - **Direita: fica como foi feita na sessão A (PR #228)**: 2 × M2 em u = 163,0, v = ±3,6, a 3 mm da tecla 8. Não mexer.
   - **Esquerda (cauda): novo parafuso, espelho do da direita**, com a mesma disposição em v e a mesma distância até a ponta da régua. Na cauda há pouca largura, por isso o Code informa também se cabe um só M2 em v = 0 e deixa a decisão ao J.
   - **Onde abrir o espaço (proposta do J):** a régua cresce para a esquerda. Da ponta esquerda para a direita, a ordem passa a ser:
     1. **conector do FFC (J1)**, ainda na ponta e com a boca para −x;
     2. **o(s) M2**;
     3. **o controlador (U9) com C9 e C10**;
     4. a tecla 1.
   - Medir o quanto a régua cresce e conferir:
     - a folga da nova ponta até a placa principal;
     - se o FFC de 20 mm ainda alcança, nas 4 fileiras;
     - a folga até a parede esquerda e até a baia da bateria.
     Se não couber, não mude a ordem. Informe o problema com números e opções.
   - Mesmo sistema da direita: porca sextavada sob a régua, cabeça por cima. A grade fica presa pelo M2 da direita e pelas switches. Se ela não alcançar a cauda, isso deve ficar dito.
2. **Case 1 mm mais largo.** Planta **248,0 × 89,1** (parede direita interna em x 148,0). A folga da régua mais longa (fileiras 1 e 3) até a parede passa a ≥ 1,75 mm. **Mudança externa aprovada pelo J.** Se o item 1 mudar o comprimento da régua, recalcule essa folga; o mínimo é 1,5 mm.
3. **Resumo dos limitantes do case (novo, para otimização futura).** No `RESTRICOES_CASE.md`, acima da tabela, uma seção **"Resumo dos limitantes"**, organizada por cota do case:
   - comprimento (esquerda e direita);
   - profundidade (frente e trás);
   - altura (piso, divisão base/tampo, tampo, botões);
   - cada parede com furo.

   Para cada cota, informar:
   - quais itens R## a definem hoje e com que folga;
   - quanto se ganharia se cada um mudasse;
   - o que custaria mudar (peça, placa ou risco).

   Os itens da R10SL entram aí: M2 nas pontas, régua alongada à esquerda, folga da parede direita e o case 248,0. **Só registrar.** Nenhuma otimização será feita agora; o J decide depois o que analisar.
4. **Imagens (regra do J):** todo relatório lista **todas** as imagens e renders gerados ou atualizados na sessão, mesmo os que não têm relação com as decisões, com caminho e uma linha de legenda. A mensagem de volta também os lista. Os títulos de `pcb/regua/img/planta_regua.png` ("160,0 × 15,0") e `pcb/regua/img/grade.png` ("148 × 16") estão desatualizados: os títulos e as cotas devem sair das variáveis do modelo.

---


## Mudanças desde a R8SL (25 nov 2026)

Resposta do J ao PR #226. **Portão F‑1 fechado:** o J ouviu os 7 registros no Teensy 4.0, todos tocam. **Portão C‑régua aprovado** com o ajuste de furos do item 1 (refazer a rota só onde os furos mudam).

1. **Fixação da régua e da grade só nas pontas.** Sai o M2 escareado do meio do teclado (deixava 0,05 mm de FR‑4 até o furo da switch). Régua e grade ficam presas por M2 **fora das teclas**: na cauda e depois da posição 8 (ou onde couber nas pontas). Entre as pontas, a switch prende na grade, os pinos dela entram na régua, a base dá apoio contínuo e o tampo limita a subida. **Reserva**, se não houver espaço nas pontas: escareado menor para cabeça DIN 965 (~3,8 mm, parede de ~0,35 mm), registrado como risco.
2. **Pistas EN de 0,15 mm: aceitas** (padrão JLCPCB, só sinal lógico).
3. **R410 (LED verde) = 47 Ω**; brilho final ajustado por PWM no firmware.
4. **Etapa 3b começa pelo escape do BGA do RT1062, numa etapa e sessão do Code dedicadas, com relato passo a passo ao J** (§8.2). Salvaguarda: se o escape não fechar em **2 sessões**, o J roteia o restante da principal com o Freerouting (como no Viaggio) e o Code entrega a placa, as regras e o DSN prontos.
5. **Regra de comunicação (J):** as perguntas ao J trazem contexto suficiente (o problema, os números e as opções) para ele decidir sem abrir os relatórios do Code. Vale para o `FIT_CHECK.md` e para a mensagem de volta.

---

## Mudanças desde a R7SL (25 nov 2026)

O J aprovou o plano de etapas (abaixo). Começam **em paralelo**: a **Etapa 3a (roteamento da régua R8 + grade)** e a **frente de firmware completo**. Cada uma é independente da outra.

**Plano de etapas (cada uma termina num portão que o J aprova):**

| Etapa | Entrega | Portão |
|---|---|---|
| 3a | Roteamento da régua R8 (2 camadas) + grade | C‑régua |
| 3b | Roteamento da placa principal (4 camadas), em sessões curtas: escape do BGA → alimentação/planos → par USB → resto | C‑principal |
| 4 | Gerbers, BOM e CPL JLCPCB (só por baixo, CPL pelos pads do EasyEDA), firmware × placa roteada, rigidez, conferência completa do case | D (pronto para cotar) |
| 5 | Case final (acabamento, STEP/STL), manual de montagem | E |
| 6 | Cotação — **só quando o J mandar** | — |
| 7 | Protótipo: compra, montagem, ensaios na ordem de risco (4 botões, ímãs dos knobs, corrente em OFF, USB, teclado) | final |
| paralela | Firmware completo, testável no Teensy 4.0 do J | F‑1 |

---

## Mudanças desde a R6SL (25 nov 2026)

Respostas do J às 3 perguntas do PR #223. **Etapa 2 fechada.** Sem tarefa nova para o Code: o próximo passo é a decisão do J sobre a próxima etapa.

1. **LED do anel: verde puro em ânodo comum** (no lugar do verde‑amarelo de cátodo comum). O firmware inverte a lógica dos pinos 13 (R) e 5 (G). Aplicar junto com a próxima tarefa de eletrônica.
2. **FFC:** aceita a faixa da principal 0,3 mm mais curta (vão 5,8 nas fileiras 2 e 4), fileira 4 com R 3,1.
3. **Ensaio do pontilhado (4 botões):** testar **0,4 × 0,15**, **0,5 × 0,18** e **0,6 × 0,25** (lado × fundo, mm); o J escolhe pelo tato.

---

## Mudanças desde a R5SL (25 nov 2026)

Resposta do J ao PR #221 (5 perguntas). **Portão B da placa principal aprovado** com os ajustes abaixo; esta revisão **fecha a Etapa 2**. Depois dela, o Code para e espera o J.

1. **Botão mais baixo (cabeça Ø15 × 3,8, metade da R5SL)**, fiel ao botão de acordeon cromático profissional. Modelo do Chat em `conceito/botao3d/` (STL branco liso, preto liso e branco com textura; renders; script Blender `mk.py`) e corte em `conceito/img/botao_baixo.png`.
   - Perfil da cabeça: base plana; **lateral reta de 1,6 mm**; borda arredondada (quarto de elipse 1,3 radial × 1,15 vertical); **domo esférico** até o topo a 3,8 mm.
   - **Não mudam:** haste Ø10 × 5,85, pino Ø5,4 com cruz fêmea, furo do tampo Ø11, **folga de 2,0 mm sobre a borda alta do furo no fim do curso**.
   - Topos em repouso: **24,0 / 26,0 / 28,0 / 31,0** (fileiras 1–4); apertado: 20,5 / 22,5 / 24,5 / 27,5. **Altura do instrumento 31,0** (era 34,7). O Code confere com o tampo real.
   - **Textura de C e F: pontilhado diagonal, como na V4** (não mais a covinha). Ponto de partida: quadradinhos de 0,5 mm rebaixados 0,18 mm, grade a 45° com passo de 1,1 mm, dentro de Ø11 no domo. O Code confere o que a SLA reproduz bem; o ensaio dos 4 botões decide.
   - Cores: naturais brancas, sustenidos pretos, C e F brancos com o pontilhado. Material SLA tough; acabamento na fase de cotação. Sem feltro (o botão não encosta no case).
2. **FFC: 20 mm sob medida, os 4 iguais.** Na fileira 4 o raio da curva no corte é 2,9 mm, abaixo do mínimo estimado (3,0): o Code confere o raio mínimo na folha do cabo e ajusta a curva ou o comprimento.
3. **Bateria substituta BAK LP‑523450‑1S‑3 (Farnell UK 2077888) aceita como reserva**; folha em `fornecimento/bateria/BAK_LP-523450-1S-3_Farnell2077888.pdf`: 950 mAh, máx. 5,2 × 34,5 × 52, PCM + **NTC 10 k em 3 fios**, conector Molex 5264‑0300 (trocado pelo rabicho SH), carga ≤ 0,5 C (20–45 °C), **descarga contínua máx. 0,5 C (≈475 mA)**. O Code confirma que o pico de consumo do instrumento fica abaixo de 475 mA; senão a BAK sai da lista. Sem STEP: envelope da folha. A principal continua a VARTA 56457 201 016.
4. **Saia do knob Ø18,4 no poço Ø19,0:** aprovada.
5. **LED do anel: bicolor 0805 ou 1206 na face de cima, soldado em casa** (o 1615 é pequeno demais para solda manual).

---

## Mudanças desde a R4SL (25 nov 2026)

Resposta do J à Etapa 2b (PR #219, 8 perguntas do `FIT_CHECK.md`). **Condição do portão B da régua cumprida** (apoio contínuo provado). A placa principal está aprovada nas linhas gerais; esta revisão fecha os pontos abaixo e **redefine o botão**. Ao terminar, o Code para no **portão B da placa principal** (fechamento da Etapa 2).

1. **Bateria VARTA 1/LPP 523450 S PCM W (56457 201 016) aprovada**, case com **247,0 mm** (+8,0). **Risco de fornecimento registrado:** 2 peças no CPC UK (BT07248) em 25 nov, Farnell com 28 semanas, e nada se compra antes de o protótipo fechar. O Code lista **1–2 substitutas diretas** (classe 34 × 50 × 5, NTC 10 k em 3 fios, à venda no Reino Unido, folha e STEP confiáveis) e confere que a **baia de 36 × 60 aceita todas sem mudar o case**; se alguma não couber, diz quanto a baia teria de crescer.
2. **Knobs em S2 com saia:** a saia esconde o vão em cunha atrás (2,0 / 2,6 mm); o knob de volume 1,0 mm mais alto fica aceito. Ímã horizontal, como pedido.
3. **Botão redefinido (substitui o estudo da R4SL; perguntas 3 e 4 ficam superadas).** Referência: `conceito/img/botao_acordeon.png` (script em `conceito/scripts/botao_acordeon.py`).
   - **Forma: cópia do botão comum de acordeon.** Cabeça **Ø15 × 7,5 mm**, lateral cilíndrica, topo levemente abaulado (flecha 1,0 mm), borda R1. **Haste Ø10** (cobre o topo da haste da switch, 9,4 × 6,5). Na ponta, **pino Ø5,4 com cruz fêmea** (4,2 × 1,04, 3,0 de fundo; interferência ≈ 0,06 conforme o estudo da R4SL), que entra na cruz MX da KS‑33D dentro do poço Ø5,67.
   - **Alturas: a cabeça nunca entra no case.** No fim do curso, a base da cabeça fica **2,0 mm acima da borda mais alta do furo** (a de trás, porque o tampo é inclinado 7,1°). Na fileira 1: base da cabeça **20,2** em repouso / **16,7** apertado; topo **27,7** / **24,2**; borda alta do furo 14,7; haste da base da cabeça ao topo da haste da switch **5,8**. As outras fileiras somam os degraus 2/2/3; **a mesma peça serve as 4 fileiras**. O Code confirma os números com o tampo real de cada fileira e corrige se a borda alta de alguma fileira for diferente.
   - **Furo do tampo: Ø11, sem rebaixo** (era Ø16 com rebaixo Ø17). Só a haste passa; folga radial 0,5 para a haste Ø10.
   - **Altura do instrumento aceita:** os botões ficam ~9 mm mais altos que no conceito (fileira 4: topo ~34,7). O Design atualiza a vista lateral e a altura total no `RESTRICOES_CASE.md` (muda o lado de fora).
   - **Material: resina SLA "tough"** (opção B), peça única. **Cores do teclado bayan: naturais brancas, sustenidos pretos; C e F com textura** (o Design propõe uma textura tátil que a SLA faça bem e que não incomode o dedo). **Acabamento (lixa, verniz, brilho) fica para a fase de cotação.**
   - Ensaio com 4 botões antes de imprimir os 32, no plano do protótipo.
4. **Cabo FFC:** **30 mm de série com curva em S**, se o corte provar que a curva cabe com o raio mínimo do cabo; senão, 20 mm sob medida.
5. **Par USB 36 mm (38–42 roteado): aceito** (Full Speed). O RT1062 fica onde está.
6. **LED do anel:** primeiro conferir o LED reverso 1615 na folha de dados (janela na placa, 0,5 mm entre fileiras de pads); se não fechar, o LED passa para a **face de cima, soldado em casa**.
7. **Pinagem invertida dos FFC no esquema da principal: aprovada** (a régua não muda).

---

## Mudanças desde a R3SL (25 nov 2026)

Resposta do J à Etapa 2a (PR #215). **Portão B da régua aprovado, com uma condição:** provar em corte o apoio contínuo das réguas (item 1). Começa a **Etapa 2b: posicionamento da placa principal**.

1. **Apoio das réguas (condição do portão B):** a cena 3D mostra as caudas sobre duas "pernas" com vão embaixo. A regra é **base sólida, apoio contínuo em todo o comprimento, o mesmo tipo de apoio nas 4 fileiras, sem furos no piso**. O Design mostra **um corte longitudinal por fileira**, de ponta a ponta (cauda incluída). Se houver vão, corrige.
2. **Folga axial dos registros 0,8 mm:** aceita (pele de PA12 de 0,5 sobre o ímã Ø6 × 2,5).
3. **Plataforma dos knobs no tampo inclinado (7,1°):** cortes das três soluções, para o J decidir, **de preferência com o ímã sem inclinação**:
   - **S1** — disco plano de Ø26 (hoje): 2,6 mm acima do tampo na frente e 0,6 abaixo atrás;
   - **S2 (preferida)** — a plataforma segue a inclinação (tampo + 1,0); **eixo do knob vertical, ímã horizontal**; topo do knob plano e horizontal (tem de ser simétrico, senão parece bambolear ao girar); fundo do poço horizontal, mais fundo atrás que na frente;
   - **S3** — eixo perpendicular ao tampo (ímã inclinado 7,1°), só como referência, com o erro de ângulo estimado no sensor.
   Vale para os dois knobs (registros e volume). O modelo oficial segue a S2 até o J decidir, salvo impedimento.
4. **Furo da grade: 14,00 nominal com alívio nos cantos** (dog‑bone, como nas placas de teclado). A tolerância da fresa (±0,1) entra como risco no `RESTRICOES_CASE.md`.
5. **Painel régua + grade:** fica para a fase de cotação (que só começa quando o J mandar).
6. **Parafuso M2 da régua: escareado, rente à grade** (grade escareada, como na V3).
7. **Orientação das switches confirmada:** ímã/sensor para o jogador, guia de luz para trás.
8. **Comprimento do FFC:** decidido nesta etapa (2b), com a placa principal posicionada.
9. **Bateria: o Code escolhe uma e ela vira o padrão do case** (revisado 25 nov, 13h30). Há várias candidatas; o J quer **uma** escolha, com dados confiáveis.
   - **Requisitos:**
     - LiPo 1S 3,7 V, **≥ 1000 mAh**, com PCM;
     - **NTC 10 k em 3 fios** (preferido; sem NTC só com justificativa e o resistor de 10 k no TS);
     - fios (sem conector de pressão), descarga ≥ 1 A;
     - tamanho que caiba na baia da frente‑esquerda com o menor crescimento do case à esquerda; **espessura ≤ 5,5 mm**.
   - **Compra:** à venda para **Londres**, **em estoque**, **em quantidade unitária**, num distribuidor do Reino Unido ou que entregue lá (Farnell UK, RS UK, Mouser, DigiKey, Rapid, The Pi Hut, Pimoroni…). Guardar o link, o código do distribuidor e a data da consulta. **Nada é comprado.**
   - **Dados confiáveis:** folha de dados do **fabricante** (medidas máximas, NTC, PCM, carga) e **STEP do fabricante ou do distribuidor**. Se a folha se contradisser, usar o valor mais conservador e registrar.
   - **Candidatas já conhecidas** (todas VARTA, com fios, PCM, NTC 10 k B 3380):
     - 1/LPP 523450 S PCM W — VKB 56457 201 016 (folha) / 56457 201 012 (STEP); ≈ 34,5 × 52 × 5,35; 1000 mAh (a folha diz também 1400, contradição); **STEP e folha do J** em `fornecimento/bateria/`;
     - 1/LPP 503562 S PCM W — VKB 56456 201 012; 63,5 × 35,5 × 5,1; 1200 mAh; **STEP e folha do J** em `fornecimento/bateria/`;
     - 1/LPP 503759 8HH PCM W — VKB 56427 201 018 (Farnell 2531265) / 56427 201 022; 60,5 × 37,5 × 5,4; 1400 mAh; sem STEP.
     Outras marcas podem entrar se atenderem aos requisitos melhor.
   - **Entrega:** tabela comparativa no `ELETRONICA.md` (medidas, capacidade, NTC, distribuidor, estoque, preço unitário visto, link, data, STEP sim/não), **a escolha justificada**, e a escolhida aplicada no case (baia, crescimento à esquerda, folga sob a placa, saída dos fios e do rabicho SH), no `RESTRICOES_CASE.md` e na corrente de carga do BQ24075 (≤ 0,5 C). Se o STEP da escolhida não existir, pedir ao J no `FIT_CHECK.md`.
10. **Estudo do botão (novo), para projetar e comprar.** Pela leitura do STEP da KS‑33D: a haste tem uma **cruz macho tipo MX** (braços de 4,0 mm, largura ≈1,1 mm, ≈3,3 mm de altura) dentro de um **poço redondo de Ø5,67**. O botão precisa de um **pino redondo de Ø ≤ 5,5 com soquete em cruz fêmea** e encaixe firme. O estudo define:
    - encaixe na cruz: medidas do soquete e interferência por processo (MJF PA12, resina SLA), retenção e desmontagem;
    - diâmetros do pino, da cabeça e da saia;
    - **folga radial para o furo do tampo** (hoje Ø16, rebaixo Ø17) com o curso de 3,5 mm sem raspar, inclusive com o botão inclinado pela folga da haste;
    - altura da cabeça (fileira por fileira, com o case);
    - processo, material, acabamento e onde encomendar (sem cotação);
    - STEP do botão e corte cotado com a switch e o tampo. Medidas conferidas contra o desenho da Gateron.

---

## Mudanças desde a R2SL (25 nov 2026)

Resposta do J ao portão A da R2SL (PR #213, 7 perguntas do `FIT_CHECK.md`). **Portão A aprovado.** Começa a **Etapa 2 pela régua (2a)**; a placa principal (2b) vem numa sessão própria, depois do portão B da régua.

1. **Placa principal com a face de baixo em z 6,8** (definida pelo P2) **e bolso de 0,6 mm no piso sob o P2**, como margem para a leitura ambígua do STEP (pergunta 1). Os furos do USB‑C (z ≈ 5,2) e do P2 (z ≈ 4,0) ficam aprovados.
2. **Bateria = B3, LPP 503759 8HH** (1400 mAh, PCM, NTC 10 k, 3 fios; Farnell 56427 201 018): **case +10,5 mm à esquerda** (pergunta 2). B1 e B2 saem.
3. **Plataforma dos registros +1,0 mm** (exterior, só essa plataforma; as teclas não mudam): folga axial 1,3 mm e **ímã Ø6 × 2,5** (pergunta 3).
4. **Anel de LED leitoso** no volume, peça separada no tampo, Ø23,2/Ø20,8 × 1,5, em material translúcido (resina SLA ou acrílico; o MJF não é translúcido) (pergunta 4).
5. **Plugue da bateria JST SH 3 vias** (J202, face de baixo): **rabicho SH já crimpado**, emendado aos fios da bateria com solda e termo‑retrátil; crimpar SH à mão não (pergunta 5).
6. **Knob retido pela cabeça da haste**: montagem com o tampo virado, o knob por último (pergunta 6).
7. **OFF do volume às 7h30** visto de cima (12 h = trás do instrumento, 225° na convenção matemática), do mesmo lado da posição 1 dos registros; o volume sobe no sentido horário por **270°** até o máximo às 4h30. Ímã do OFF a 7,2 mm do eixo, no batente anti‑horário (pergunta 7).
8. **Desvios da R2SL aceitos:** OFF com latch SET/KILL; DRV5032**ZE**; indutor FNR3015 de 1,5 mm; conector SH da bateria. **Risco de fornecimento registrado:** TMAG5273A2 com 60 peças em estoque.

---

## Mudanças desde a R1SL (25 nov 2026)

Resposta do J ao portão A da Etapa 1 (PR #210) e às 7 perguntas do `FIT_CHECK.md`. **O portão A continua aberto**: a R2SL fecha os pontos pendentes e a Etapa 1 é refeita só no que mudou (§8).

1. **RT1062 = MIMXRT1062DVJ6B, BGA196 12 × 12 mm, passo 0,8** (pergunta 1). O "DVL6B" da R1SL era erro de nome. Peça **consignada** (não depender do estoque da JLCPCB). STEP, símbolo e footprint da SamacSys em `modelos/rt1062/` (PR #211): a eletrônica confere o footprint do esquema contra o da biblioteca.
2. **Knobs = opção C, magnéticos, sem eixo** (perguntas 2 e 3). Somem o pot com chave e a chave rotativa SRBV: nada de peça de furo, bucha M9 ou porca no tampo. Detalhe em §4.
3. **USB‑C e P2 = as mesmas peças e o mesmo jeito da V4** (pergunta 5): HRO TYPE‑C‑31‑M‑12 (C165948) e XUNPU PJ‑327A (C49284723), montados pela JLCPCB na face de baixo, na borda da placa. Deixam de ser mid‑mount.
4. **Regra de alturas e o novo `RESTRICOES_CASE.md`** (pergunta 4). Peça que não cabe sob a placa segue a ordem: (a) peça equivalente mais baixa; (b) passa para a face de cima (soldada em casa); (c) **o conjunto sobe** até caber. Todo fator que limita a forma do case vai para o registro novo (§3.1), mantido pelo Design e atualizado a cada etapa.
5. **Bateria** (pergunta 6): o caminho aprovado continua (LP402764 de 2 fios + resistor de 10 k no TS se não houver NTC; baia +1 mm), **mas o Code estuda baterias maiores de fabricante com folha de dados e distribuidor**, e o J aceita **alongar o case para a esquerda**. Detalhe em §4.
6. **FFC de 1,0 mm** (C3250113, pergunta 7), montado pela JLCPCB; o J só encaixa os cabos.
7. **Par USB de 30–35 mm aceito** (pergunta 4 da `ELETRONICA.md`), com o firmware **forçando Full Speed**.
8. **Fluxo do repositório:** cada revisão da SPEC entra no `main` por PR (o Chat faz). O ramo `slim-r1sl` do J é cópia antiga e não entra; o PR #132 (placa de teste de teclas) foi fechado.

---

Versão nova e **independente do Student V4**. Tudo que o Slim precisa está nesta pasta (`etutti/hardware/slim/`). O V4 serve só como fonte de aprendizado: nenhum arquivo daqui depende de arquivos do V4, e nada do V4 é alterado.

- Revisões deste SPEC: **R1SL, R2SL, R3SL…** Cada revisão começa com "Mudanças desde a anterior". Os relatórios citam a revisão que atendem.
- Protocolo: Chat mantém o SPEC → Code implementa e responde em `FIT_CHECK.md`, que termina com **"Perguntas para o design"** → J aprova os portões.
- Três agentes do Code: **Design**, **Eletrônica**, **Programação e som**.
- **Fora do escopo até o J avisar:** cotação, compra e pedido de placas. Nada é comprado, nem amostra.

---

## 0. Etapas e portões

O trabalho segue em 3 etapas. Nenhuma começa antes do portão anterior aprovado pelo J. **Posicionamento e roteamento são feitos separadamente para a régua e para a placa principal**, cada um na sua sessão, para economizar contexto.

| Etapa | Sessões | Entrega | Portão |
|---|---|---|---|
| **1. Validação de componentes e lógica** | 1a Eletrônica · 1b Programação e som · 1c Design (envelopes e STEP) | BOM com PN, esquemático KiCad, ERC 0/0, mapa de pinos, lógica de energia, lista de STEP, `ELETRONICA.md`, `FIRMWARE.md` | **A**: J aprova componentes e lógica |
| **2. Posicionamento** | 2a Régua R8 (+ grade) · 2b Placa principal | Planta cotada de cada placa, cena 3D com o case, `POSICIONAMENTO.md` | **B**: J aprova o posicionamento de cada placa |
| **3. Roteamento** | 3a Régua R8 · 3b Placa principal | Placas roteadas, DRC 0 erros / 0 avisos, `ROTEAMENTO.md` | **C**: J aprova |

---

## 1. Teclado (entradas fixas — o case nunca decide alturas)

- C‑griff, 4 fileiras, 32 teclas, malha hexagonal: **passo 18,5 mm** na fileira, **16,02 mm** entre fileiras.
- **Degraus entre fileiras 1→2→3→4: 2,0 · 2,0 · 3,0 mm** (padrão bayan, igual ao V4). Fileira 1 = a mais perto do músico e a mais baixa.
- Origem das coordenadas: centro da tecla A3 da fileira 1. x para a direita (agudos), y para trás.
- Deslocamento por fileira: fileiras 1 e 3 em x = 0; fileiras 2 e 4 em x = −9,25.

| Fileira | Notas (8) |
|---|---|
| 1 | A3 C4 D#4 F#4 A4 C5 D#5 F#5 |
| 2 | G3 A#3 C#4 E4 G4 A#4 C#5 E5 |
| 3 | G#3 B3 D4 F4 G#4 B4 D5 F5 |
| 4 | F#3 A3 C4 D#4 F#4 A4 C5 D#5 |

- **Botões: todos iguais**, domo convexo com saia, Ø15. Pretos (sustenidos), brancos, e brancos com pontos (C e F). Encaixe novo para a cruz da KS‑33D (4,0 × 1,1 em cilindro Ø5,7). Nunca há botões de alturas diferentes.
- Toda visualização de teclado leva o nome das notas.

## 2. Switch

**Gateron LP Magnetic Jade Pro, KS‑33DD10B060NW‑D276** (toda em POM). Desenho e STEP em `fornecimento/gateron/`.

| Item | Valor |
|---|---|
| Carcaça de cima | 14,60 × 14,60 (topo 12,7) |
| Corpo de baixo / furo da grade | 14,00 / 14,00 (+0,05/−0,02) |
| Grade (placa) | 1,20 mm; topo a 2,5 mm da PCB |
| PCB → topo da carcaça | 5,85 |
| Curso total | 3,5 ± 0,2 (haste rente à carcaça no fundo) |
| Força inicial | 40 ± 10 gf |
| Fluxo N | 75 ± 10 Gs (repouso) · 680 ± 70 Gs (fundo) |
| PCB | 2 furos Ø1,70 a 10,15 mm + furo Ø5,20 central (o poste Ø5,0 atravessa) |
| Abaixo da PCB | pinos ≈1,65 e poste 2,5 mm abaixo da face de baixo |
| Sensor Hall | verso da PCB, a 4,3 mm do centro (desenho “Layout of PCB”) |

Montagem como teclado mecânico: o switch prende na **grade** e encaixa na **régua**; régua + grade formam um conjunto sólido (2 espaçadores M2 por régua). **O tampo não prende as teclas**: só encosta ou fica a ≤0,3 mm das carcaças.

Comparação com a KS‑20 do V4: `conceito/img/sw_cmp.svg`.

## 3. Case — conceito aprovado (G v7), a rever após o detalhe eletrônico

- Planta **239 × 89 mm**, x de −90 a 149, y de −18,5 a 70,6. Material MJF PA12, tampo + base, sem autoatarraxante.
- **Tampo derivado das fileiras**: plano inclinado de 7,1° pelas fileiras 1–3 (degraus iguais), degrau suave de +1,0 mm entre y = 35 e 39 (completa os 3 mm da fileira 4), depois curva convexa até a borda de trás. Bordas: frente R4, trás R6. Função de referência: `conceito/scripts/sec7.py` (`S(y)`).
- **Furo Ø16** em cada tecla e **rebaixo Ø17** com fundo plano no nível do topo da carcaça + 1,8 mm. Parede mínima entre rebaixos: 1,5 mm.
- **Nenhum furo no piso.** Todas as réguas usam o mesmo tipo de apoio: berço contínuo sobre o degrau da base, com bolso de ≈2,8 mm sob cada poste e piso de ≥1,0 mm sob o bolso.

Pilha da fileira 1 (fileiras 2, 3, 4: +2, +4, +7):

| Cota (mm, do fundo da base) | |
|---|---|
| 1,6 | piso |
| 3,8 → 5,0 | régua (face de baixo → de cima) |
| 6,3 → 7,5 | grade |
| 10,85 | topo da carcaça |
| 14,35 | haste em repouso |
| 11,15 | face de baixo do tampo sobre as carcaças (folga 0,3) |
| 12,65 | fundo do rebaixo (1,5 mm de material) |
| 14,0 | superfície do tampo no centro da tecla |
| 14,55 / 18,55 | saia / topo do botão em repouso (saia a 0,2 da carcaça no fundo de curso) |

Resultado: borda da frente ≈11 mm, tampo máx. ≈22 mm, topo dos botões 18,6 → 25,6 mm.

Renders de conceito: `conceito/img/v7_iso_esq_com.jpg`, `v7_iso_esq_sem.jpg`. Cortes: `L_secA.svg`, `L_secB.svg`.

### 3.1 Registro de restrições do case — `RESTRICOES_CASE.md` (novo na R2SL)

Tudo que limita ou empurra a forma do case fica registrado, para ser gerenciado como risco: altura de peça, folga sob a placa, conector na parede, baia da bateria, curso do knob, raio de cabo, tolerância de impressão etc. Dono: **Design**. Atualizado a cada etapa (e a cada revisão da SPEC); o `FIT_CHECK.md` resume as mudanças.

| Coluna | Conteúdo |
|---|---|
| ID | R01, R02… (não reutilizar números) |
| Fator | o que limita (ex.: "altura do JST da bateria sob a placa") |
| Peça e medida | PN, medida e **fonte** (datasheet, STEP, medida estimada) |
| Onde | zona do case (x, y, z) |
| Efeito no case | mm que o case cresce ou sobe, ou "nenhum" |
| Folga | margem que sobra, mm |
| Alternativas | as opções da regra (a)/(b)/(c) e o custo de cada uma |
| Decisão | quem decidiu e quando, ou "aberto" |
| Estado | aberto · resolvido · aceito como risco |

Regra: **qualquer item que mude o lado de fora do case** (contorno, altura, parede, furo) aparece em destaque no `FIT_CHECK.md` e só vale depois do J aprovar. O que só mexe por dentro é decidido pelo Code e registrado.

**Renders Blender detalhados:** só o isométrico frontal do lado dos knobs, com e sem botões, e **só quando o J pedir**. Sempre com modelos 3D realistas dos componentes; se faltar um STEP, avisar o J.

## 4. Interface e energia

- **Knobs magnéticos, sem eixo (opção C, R2SL)**, em poços (Ø17,6, 1,2 mm de fundo) nas plataformas: **registros** em (−46, 0) na fileira 1, **volume** em (−46, 48,06) na fileira 4. Corte de referência: `conceito/img/knobs_opcoes.png` (coluna C).
  - **Knob:** peça impressa, topo ≈ +4,8 mm sobre o tampo (≈ altura do botão da fileira), **haste** que atravessa um furo‑mancal no fundo do poço e desce até ≈0,5 mm acima da placa principal. Retenção pela cabeça da haste (R3SL): knob por cima, haste por baixo, montado com o tampo virado e o knob por último; o knob não sai puxando.
  - **Ímã diametral** (**Ø6 × 2,5** NdFeB, R3SL; a plataforma dos registros sobe 1,0 mm para caber) na ponta da haste, sobre um **sensor de ângulo** na **face de baixo** da placa (montado pela JLCPCB), lendo através da placa: ímã → sensor ≈ 0,5 + 1,2 + chip. Sensor: TMAG5273 ou equivalente (AS5600, MT6701…), **o Code escolhe e justifica** pelo campo no sensor, resolução, consumo e endereço I²C (dois sensores no mesmo barramento do SGTL5000). Se a placa subir pela regra de alturas, só a haste muda de comprimento.
  - **Cliques:** moldados no poço/haste (esfera com mola ou flexão do PA12, **o Design propõe e justifica**), com batentes. A vida útil do clique em PA12 é risco a registrar.
- **Volume: contínuo, sem passos.** O clique ao sair de OFF, no sentido horário, liga o instrumento e acende o LED; daí até o fim do curso só sobe o volume (volume digital, lido do sensor de ângulo). **OFF em hardware:** um segundo ímã no knob, na posição OFF, sobre uma **chave Hall de microcorrente** (DRV5032 ou equivalente, alimentada direto pela bateria) que comanda o SYSOFF no lugar da chave do pot: knob em OFF e sem USB = bateria desconectada, como na R1SL. Consumo em OFF ≤ alguns µA (o Code calcula a autonomia em prateleira). Marcação: arco contínuo que engrossa no sentido horário, com ponto de OFF.
- **Registros: seletor absoluto de 7 posições** (ângulo lido pelo sensor; o firmware arredonda para a posição e guarda a última), no sentido horário a partir de baixo‑esquerda, a 45°:

| Pos. | Registro | Pontos (L embaixo, M no meio esq./centro/dir., H em cima) |
|---|---|---|
| 1 | L | L |
| 2 | LM | L + M esquerdo |
| 3 | M | M esquerdo |
| 4 | MM | M esquerdo + M direito (centro vazio) |
| 5 | MH | M esquerdo + H |
| 6 | LH | L + H |
| 7 | H | H |

  Desenho: `conceito/img/knobs7.svg`.
- **LED:** bicolor (verde/vermelho, laranja pela mistura), montagem reversa na face de baixo, aceso num **anel leitoso** em volta do knob de volume: peça separada no tampo, Ø23,2/Ø20,8 × 1,5, resina SLA ou acrílico (R3SL). Estados do V4: verde tocando, verde breve a cada 2 s em repouso, laranja ao ler as teclas na partida e carregando, vermelho lento bateria baixa, vermelho rápido codec ou régua sem resposta.
- **Bateria:** baia própria na frente‑esquerda.
  - **A definir pelo Code na R4SL** (item 9 das Mudanças): uma bateria à venda para Londres, em estoque, com folha de dados e STEP confiáveis; ela vira o padrão do case. Plugue JST SH 3 vias por rabicho crimpado emendado aos fios. Nada é comprado.
- **Conectores (aprovados):**
  - **USB‑C** na **parede de trás**, centro em x = −66 (24 mm da parede esquerda; se o case crescer para a esquerda pela bateria, a distância à quina cresce junto).
  - **P2 3,5 mm OUT** na **parede esquerda**, centro em y = 59,5 (11 mm da parede de trás).
  - **Peças e montagem da V4 (R2SL):** HRO TYPE‑C‑31‑M‑12 (C165948) e XUNPU PJ‑327A (C49284723), na **face de baixo**, na borda da placa, montados pela JLCPCB. A altura deles sob a placa entra na regra de alturas (§5.2).
  - Ambos afastados das quinas o quanto o layout permitir; o Code pode afastar mais se couber.
- **Energia:** BQ24075 (carregador + caminho de energia com SYSOFF). A **chave Hall do OFF do volume** controla o SYSOFF (R2SL; era a chave do pot), mas uma lógica mantém o SYSOFF baixo sempre que há USB, porque com SYSOFF alto o BQ24075 também para de carregar. Knob em OFF e sem USB: bateria desconectada.
- **Com USB, as mesmas funções do V4:** MIDI USB class‑compliant “eTutti” com velocity; o USB acorda, alimenta e carrega mesmo com o knob em OFF; desligamento suave com cabo; USB Full Speed (12 Mbit/s), **forçado no firmware** (o par tem 30–35 mm). Só na bateria: desliga sozinho após 15 min sem uso ou com bateria vazia.
- **Botão PROG:** dentro do case, só acessível abrindo a base.
- Áudio: só saída OUT para fone, sem microfone e sem alto‑falante.

## 5. Placas

### 5.1 Régua R8 (×4, idênticas, montadas uma vez)
- 15 × ≈167,5 mm (R9SL; pode mudar com a R10SL item 1), 2 camadas, 1,2 mm. Cauda além da primeira tecla, com o conector por baixo, fora da área das teclas. **Fixação (R11SL): 1 × M2 em v = 0 em cada ponta (esquerda entre a tecla 1 e U9; direita logo depois da tecla 8); trilhos terminam nos dois parafusos, em guias centralizadas; ponta esquerda em balanço com J1 e U9/C9/C10.**
- 8 × **TMAG5253** na face de baixo, na posição do desenho Gateron (4,3 mm do centro), saída analógica compartilhada; habilitação por **74HC595** na cauda (esquema do V4). O BA3 (±80 mT lineares) cobre os 68 mT do fundo de curso.
- Footprint KS‑33D: 2 × Ø1,70 + Ø5,20.
- **Grade** FR‑4 1,2 mm com furos 14,00, no mesmo painel da régua se a JLCPCB aceitar.
- Conector **FFC 8 vias 0,5 mm, 1,0 mm de altura** (C3250113, R2SL; conferir se o contato é dos dois lados) na cauda (face de baixo): GND, 3V3, OUT, DADO, CLOCK, LATCH, GND, GND. Cabos FFC prontos, retos, um por fileira.

### 5.2 Placa principal
- Faixa vertical de ≈24 × 82 mm junto às caudas das réguas, mais um pé de ≈31 × 14 mm atrás, até a parede esquerda (USB‑C, P2, energia). 4 camadas. Montagem JLCPCB **só na face de baixo**, peças Basic primeiro.
- **Teensy 4.1 chip‑down:** **MIMXRT1062DVJ6B** (BGA196 12 × 12, passo 0,8; peça consignada; STEP e biblioteca em `modelos/rt1062/`), flash QSPI 64 Mbit, **MKL02 com bootloader PJRC** (só a PJRC vende; prever peça consignada), cristal 24 MHz, 32,768 kHz opcional, indutor do DCDC, sequência de energia pela referência PJRC (sem atraso RC no DCDC_PSWITCH).
- **O RT1062 é posicionado primeiro**: entre os knobs, na altura da fileira 3. Zona de escape livre de 2,5 mm em volta e corredores reservados: ADC → conectores das réguas; QSPI → flash; XTAL; USB e I2S → pé da placa. A orientação do BGA sai do mapa de esferas.
- SGTL5000 (codec com driver de fone), LDO 3,3 V, ESD USB, PTC, conector da bateria, lógica SYSOFF, LED reverso, **2 sensores de ângulo + chave Hall do OFF** (face de baixo, sob os knobs).
- **Regra de alturas (R2SL).** Folga sob a placa = face de baixo da placa − topo do piso (com a placa na régua da fileira 1: 3,8 − 1,6 = 2,2 mm). Peça que não cabe, nesta ordem:
  1. **equivalente mais baixa** (ex.: indutor do TPS63001 ≤ 1,9 mm; conector de bateria baixo ou fios soldados em pads);
  2. **face de cima**, soldada em casa (ex.: conector da bateria; há espaço entre a placa e o tampo);
  3. **subir o conjunto** (placa principal mais alta, em pilares) até caber.
  USB‑C e P2 da V4 ficam por baixo (são montados pela JLCPCB): eles provavelmente definem a altura da placa principal. Cada caso vai para o `RESTRICOES_CASE.md` com a folga resultante. Bolsos no piso são permitidos; furos não.
- Plano preliminar: `conceito/img/MB5_detail.svg` e `P1e_layout.svg`.
- Par USB: ≈30–35 mm, **aceito** (R2SL) com Full Speed forçado no firmware; 90 Ω diferenciais como boa prática.

## 6. Ferramentas

- O J instalou no computador dele o KiCad 9/10 e o **KiCadRoutingTools** (drandyhaas/KiCadRoutingTools: plugin e CLI, `bga_fanout.py`, roteador A*).
- **Cabe ao Code decidir** se e quando usar o KiCadRoutingTools, e validar se o resultado é melhor que o fluxo usado antes (Freerouting e scripts). Sempre numa cópia do `.kicad_pcb`. A comparação usa: DRC 0/0, nada sem rota, número de vias, comprimento do par USB e das linhas analógicas. O resultado vai no relatório.
- Se o Code rodar na nuvem, ele repete a instalação no ambiente dele.

## 7. Modelos 3D (STEP)

Sempre modelos realistas e detalhados. O que faltar vai para o `FIT_CHECK.md` para o J fornecer.

| Peça | Situação (R2SL) |
|---|---|
| Switch KS‑33D | ✔ `fornecimento/gateron/` |
| RT1062 DVJ6B | ✔ `modelos/rt1062/` (SamacSys, fornecido pelo J) |
| USB‑C C165948, P2 C49284723 | ◐ puxar do EasyEDA pelo LCSC (os mesmos da V4) |
| TMAG5273, DRV5032ZE, ímãs Ø6 × 2,5 | ◐ chips pelo EasyEDA; ímãs = cilindros pelas medidas |
| JST SH 3 vias | ✖ falta (o Code busca no EasyEDA) |
| Anel leitoso do LED | desenho próprio (Design) |
| Bateria | ◐ STEP das VARTA 523450 e 503562 em `fornecimento/bateria/`; o da escolhida, se for outra, o Code busca ou pede ao J |
| MKL02 | ✖ sem STEP público: caixa QFN‑16 3 × 3 pelo desenho da NXP |
| Demais peças JLCPCB | ✔ EasyEDA (`modelos/baixados/`, fora do Git) |
| Pot com chave, SRBV | — saíram do projeto na R2SL |

## 8. Tarefas abertas — sessões do Code

A §8.1 (sessão A da R9SL) foi concluída no PR #228. A §8.2 (sessão B, BGA) continua valendo. A R10SL acrescentou a §8.3 (feita no PR #231). A R11SL acrescentou a §8.4 (feita no PR #234). A R12SL acrescentou a §8.5 (feita no PR #236). A R13SL acrescenta a §8.6 (sessão A5); a sessão B começa depois dela (R13SL item 5).

### 8.1 Sessão A — ajustes da régua e da principal [Eletrônica + Design + Roteamento]

1. **Eletrônica:**
   - furos M2 da régua e da grade nas pontas (item 1), com o furo cego da cauda e da ponta direita conferido contra a base do case;
   - R410 = 47 Ω (item 3);
   - ERC 0/0 nas duas placas.
2. **Design:**
   - base do case com os apoios/porcas dos M2 nas novas posições;
   - grade sem escareado no meio;
   - `RESTRICOES_CASE.md` atualizado.
3. **Roteamento:** refazer na régua só o que os furos deslocam, pelo método híbrido da R8SL. Aceite C‑régua: DRC 0/0, 0 não ligados, paridade 0.
4. Gerbers da grade conferidos de novo.
5. `FIT_CHECK.md` com as perguntas **já com contexto** (item 5).
6. Parar.

### 8.2 Sessão B — Etapa 3b‑1: escape do BGA do RT1062 [Roteamento, sessão dedicada]

**Uma sessão própria do Code, só para isto. Em cada passo o Code para, mostra o resultado ao J numa mensagem curta, com imagem, e só segue quando o J disser "siga".**

**Base (R13SL):** a placa principal do `main`, com o posicionamento da R9SL e a **faixa de 22,2 mm** (x −58,5…−36,3). A sessão B começa **depois da A5**, numa sessão nova do Code, e segue a regra de verificação da R13SL item 4. Se não houver nenhum outro trabalho do Code rodando ao mesmo tempo, ela pode usar a pasta principal; senão, usa uma worktree git própria.

- **B1 — Regras e camadas.** Proponha e justifique, sem cotação:
  - stack‑up de 4 camadas da JLCPCB;
  - via para o BGA de 0,8 mm (furo e anel dentro do padrão da JLCPCB, ou o custo extra, se exigir);
  - largura e folga entre bolas;
  - papel de cada camada (sinal / GND / 3V3);
  - regras no `.kicad_dru`.
- **B2 — Plano de escape.**
  - Mapa das 196 bolas: anel por anel, em qual camada cada uma sai e por que lado.
  - Bolas não usadas e de alimentação ligadas aos planos.
  - Pares e sinais sensíveis (USB, I²S, cristal, flash) com o caminho previsto.
  - Imagem do mapa.
- **B3 — Escape.**
  - Rodar o `bga_fanout.py` do KiCadRoutingTools (ou o método melhor que o B1/B2 indicarem) só no RT1062 e vizinhos imediatos (cristal, desacoplamentos, flash, MKL02).
  - DRC dessa região.
  - Imagem.
- **B4 — Avaliação.**
  - Quantas bolas escaparam e o que falta.
  - Se o resto da placa parece roteável pelo mesmo método.
  - Recomendação: seguir com o Code ou passar ao J com o Freerouting (item 4).

Aceite da 3b‑1: todas as bolas usadas com escape até fora da sombra do BGA, DRC da região 0/0, paridade 0. Estado em `slim/pcb/principal/rota/estado.json`, um commit por passo concluído, `ROTEAMENTO.md` atualizado. Nada de cotação ou compra.

### 8.3 Sessão A2 — fixação da régua nas duas pontas e case 248,0 [Eletrônica + Design + Roteamento]

Pode rodar em paralelo à sessão B: não mexe na principal, salvo se o item 1(b) da R10SL encostar nela.

1. **Eletrônica:** parafuso(s) da cauda como espelho do da direita (R10SL item 1). Ordem a partir da ponta esquerda: J1 → M2 → U9/C9/C10 → tecla 1. A ponta direita não muda.
   - Informar o novo comprimento da régua, as folgas até a principal, a parede esquerda e a bateria, e o alcance do FFC de 20 mm nas 4 fileiras.
   - Dizer se cabe um M2 único em v = 0 na cauda, como alternativa para o J decidir.
   - ERC 0/0.
2. **Roteamento:** refazer a rota da régua pelo método híbrido (`etapas.py`). Aceite C‑régua: DRC 0/0, 0 não ligados, paridade 0. Gerbers da grade conferidos.
3. **Design:**
   - case 248,0;
   - porcas e apoios dos dois M2 na base;
   - folga até a parede direita recalculada;
   - seção "Resumo dos limitantes" no `RESTRICOES_CASE.md` (R10SL item 3);
   - títulos das figuras corrigidos (item 4).
4. `FIT_CHECK.md` com as perguntas **já com contexto** e a lista de **todas** as imagens geradas.
5. Commit → PR → merge. Parar.


### 8.4 Sessão A3 — um M2 central em cada ponta e modelo de montagem [Eletrônica + Design + Roteamento]

Substitui a fixação da cauda feita na §8.3.

1. **Eletrônica:**
   - cauda reorganizada (R11SL item 1): J1 → U9/C9/C10 → M2 em v = 0 → tecla 1;
   - ponta direita com 1 M2 em v = 0 no lugar do par;
   - régua o mais curta possível nas duas pontas;
   - furo de cada ponta: redondo ou oblongo, com justificativa;
   - ERC 0/0;
   - principal reposicionada para devolver à faixa o que a régua liberar. DRC 0/0, paridade 0.
2. **Roteamento:** refazer a rota da régua pelo método híbrido (`etapas.py`). Aceite: DRC 0/0, 0 não ligados, paridade 0. Gerbers da grade conferidos.
3. **Design:**
   - trilhos terminando nos dois M2, cada um numa guia centralizada com o bolso da porca;
   - folgas recalculadas;
   - `RESTRICOES_CASE.md` e "Resumo dos limitantes" atualizados;
   - **modelo 3D da base e sequência de montagem** (R11SL item 2), com os STEP/GLB.
4. `FIT_CHECK.md`:
   - as perguntas já com contexto;
   - as perguntas 2 e 3 da A2 recolocadas com os números novos;
   - a lista de **todas** as imagens geradas, com caminho e uma linha de legenda.
5. Commit → PR → merge. Parar.

### 8.5 Sessão A4 — case 245,5, alívio da guia e modelos 3D [Design + Eletrônica]

Não mexe na placa principal nem na rota da régua. Pode rodar em paralelo à sessão B.

1. **Design:**
   - case encurtado à direita (R12SL item 2), com o número final e a folga;
   - alívio da guia voltada para o U9 (item 3);
   - fit check sem interferência;
   - `RESTRICOES_CASE.md` e "Resumo dos limitantes" atualizados;
   - `base.step` e `conjunto.glb` regenerados;
   - os 7 passos de montagem re-renderizados.
2. **Eletrônica:** baixar do EasyEDA os STEP das peças da principal que estão em caixa (item 5). Os modelos vão para `slim/modelos/` (ou para a pasta já usada pelos scripts de cena) e entram na cena da principal e nos passos 2 a 7. Listar o que faltar.
3. `FIT_CHECK.md` com as perguntas com contexto e a lista de **todas** as imagens geradas, com caminho e uma linha de legenda.
4. Commit → PR → merge. Parar.

### 8.6 Sessão A5 — regra de verificação e modelo do MKL02 [Eletrônica + Design + Roteamento]

Curta. Não muda a geometria.

1. **Regra de verificação (R13SL item 4):** ajustar os scripts listados para terminarem com erro quando falham ou não gravam. Cada um é testado de duas formas: uma vez com sucesso e uma vez forçando a falha (por exemplo, uma faixa estreita no posicionador), mostrando o código de saída ≠ 0.
2. **MKL02:** baixar o STEP do EasyEDA pelo código C2056583, conferir com o footprint, pôr na cena da principal e nos passos 2 a 7. Re-renderizar o que mudar.
3. **Re-verificar tudo sobre o `main` atual**, seguindo a regra nova:
   - DRC da principal e da régua (0/0, paridade 0), com o nome do arquivo e a data de gravação de cada um;
   - fit check;
   - corrigir em `ELETRONICA.md` e `RESTRICOES_CASE.md` qualquer resto das faixas de 18,4 e 20,7 mm.
4. `FIT_CHECK.md` com as perguntas já com contexto e a lista de **todas** as imagens geradas.
5. Commit → PR → merge. Parar.
