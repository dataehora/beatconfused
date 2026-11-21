# eTutti Student V4 — SPEC R3V4

Data: 21 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #181 (FIT_CHECK, ELETRONICA e FIRMWARE da R2V4). Tudo o que não é mencionado aqui continua como na R2V4 e na R1V4 (anexos abaixo). Os relatórios citam "R3V4".

## Mudanças desde a R2V4

### 1. Desenho e modelo da KS-20 Orange (pendência resolvida)

O J enviou o desenho oficial da **KS-20TO10B050NW-Y64 (Orange)** e o modelo 3D da série KS-20T. Os arquivos estão em `fornecimento/gateron/`. Nada de estimar o que eles cotam.

O que o desenho confirma:
- O corpo é o mesmo da X72.
- **5,00 ±0,05** do assento até a face de baixo da carcaça de cima: é o **ombro de cima** da grade.
- Grade de 14,00 +0,03/−0,02, com as presilhas por baixo.
- **11,10** até o topo, sem tolerância própria (vale a tabela geral, ±0,4).
- Pinos em Ø1,70 ±0,05 a 10,16 mm.
- 38 ±10 gf, 4,1 ±0,2 mm de curso, 102/905 Gs.

Medir no STEP: largura do topo plano, diâmetro do pino e a janela das presilhas, ou seja, a espessura de grade que elas aceitam.

### 2. Fixação das teclas: a KS-20 já tem os dois ombros

A KS-20 é uma tecla de montar em grade. A carcaça de cima apoia **por cima** da grade, na cota 5,00 ±0,05, e as presilhas travam **por baixo**. A pilha de ±1,1 mm da R2V4 aparece só porque a tampa apertava o **topo** da tecla (11,10 ±0,4). O ombro de 5,00 é 8 vezes mais preciso.

**Nova candidata principal (T3-G, "grade da régua"):**
- Cada régua ganha uma **grade-régua de FR-4** com 4 aberturas de 14,00 mm, no **mesmo painel e no mesmo desenho da régua** (destacável por furinhos). Assim não há pedido novo nem taxa de engenharia, só um painel maior.
- A tecla encaixa na grade-régua pelas presilhas. O conjunto (grade-régua + 4 teclas) assenta na régua pelos pinos. O corpo de baixo da tecla (5,00) é o espaçador entre grade e régua.
- A régua e a grade-régua formam um sanduíche rígido e preciso de fábrica. **Sem espuma**, sem pilha de impressão no aperto.
- A tampa (deck) **não precisa mais de pré-carga**: ela só cobre, com folga, e segura o sanduíche contra o degrau. Por exemplo, por 2 apoios por régua no deck ou 2 parafusos M2 não magnéticos por régua no degrau. O design escolhe e justifica.
- A espessura padrão da régua é 1,2 mm, e a grade de teclado comum é 1,5 mm. O design confere no STEP se as presilhas da KS-20 seguram uma grade de 1,2 mm **sem folga vertical**. Se não segurarem, comparar: (a) painel inteiro em 1,6 mm, o que muda a distância ímã-sensor e a calibração (o fabricante cota o fluxo com placa de 1,2 mm); (b) grade-régua num desenho separado de 1,5 ou 1,6 mm, com taxa de engenharia; (c) a espuma da R2V4.
- **Plano B aprovado pelo J: T3 com anéis individuais de espuma** (PU microcelular tipo Poron, sem silicone, 2 → 1 mm). Usar só se a T3-G falhar nos números.

Com a T3-G, o deck de 3 mm, os 10 postes internos e a haste 1 mm mais longa da R2V4 **podem não ser mais necessários**: o design refaz esses números para o deck sem pré-carga.

### 3. Alternativa a estudar: Gateron Low Profile Magnetic Jade

Pedido do J. Comparar com a KS-20 antes de fechar a régua:
- grade recomendada de 14,00 mm e **1,2 mm**, a mesma espessura da régua (pode permitir grade-régua no mesmo painel sem conflito);
- fluxo no fundo de ~680 Gs (a KS-20 tem 905), curso total ~3,5 mm (KS-20: 4,1) e altura menor, que **baixaria a caixa** (hoje 25,2 / 32,2 mm);
- a ver: desenho oficial e STEP, haste (o encaixe do botão muda e o botão é nosso, impresso), pinos e furação, disponibilidade de molas mais pesadas para o peso de baian que o J quer, preço e fornecimento, e se o fluxo dá curso útil suficiente no TMAG5253 BA3 através de 1,2 mm de placa.
- Critérios: firmeza, sensação parecida com a de um botão de acordeão (curso curto ajuda), altura da caixa, custo, risco.

### 4. Decisões do J sobre as perguntas do PR #181

| Tema | Decisão |
|---|---|
| Altura da caixa | **Perfil escalonado aceito** (25,2 na frente, 32,2 mm atrás com a KS-20). |
| Processo | **MJF PA12** (US$ 51 com 28 teclas). Sem cotação de SLA. |
| Peça de teste impressa | Decidir **no fim do hardware** (mantida a decisão 21). |
| Microfone | **Entrada de voz para modulação e efeitos**, tocados junto com o teclado. Verificar se o Teensy roda tudo junto (item 6). |
| Demais respostas do Chat ao PR #181 | Aprovadas: rampas de 60°, furo de Ø8 (se ainda valer com a T3-G), régua de 74 × 14 em painel de 5, fixação S1 do case, conectores JST SH-6 (clone, com a tela no mesmo conector), alto-falante Dayton CE28MB-8, ADC1 e ADC2 em paralelo, desligamento suave com USB, mapa de notas do usuário e notas até E7 para a fase da página. |

### 5. Varredura: leitura quente sem prejudicar acordes

- Ler ADC1 e ADC2 em paralelo (biblioteca ADC do Teensyduino).
- A leitura quente **alterna entre todas as colunas com tecla em movimento** (rodízio), de modo que, num acorde, a segunda nota também tenha velocity e nenhuma tecla fique mais de **~2 ms** sem leitura.
- A contagem de pulsos do firmware está certa: 8 × N + 1 por fileira, com as 4 fileiras em paralelo. A coluna 0 é a régua mais perto da placa principal. A eletrônica corrige o `PINOS.md`.

### 6. Microfone: voz com efeitos junto com o teclado

- **Hardware:** microfone de eletreto no jack IN com alimentação pelo plugue (polarização do SGTL5000, entrada MIC com pré-amplificador). Conferir no esquema e no datasheet a polarização, o ganho e o nível de linha como alternativa.
- **Firmware:** definir um conjunto inicial de efeitos e medir ou estimar a CPU de cada um, junto com a síntese do acordeão (8 vozes, 4 palhetas) e a varredura:
  - vocoder com o teclado como portadora;
  - harmonizador ou deslocador de altura;
  - eco e reverberação na voz;
  - mistura voz + teclado.
- Dizer se cabe a 396 MHz ou se pede 600 MHz, e o que isso custa em bateria. Se não couber tudo, propor o que cortar.

### 7. Fase B: o que começa já

A placa principal (só interface) não depende da escolha da tecla. Começa já:
- **esquema completo da placa principal** com BOM Basic/Extended, ERC 0/0 e `PINOS.md` final;
- **posicionamento da placa principal** (sem trilhas), com o USB-C a ≤ 7 mm dos pads 3/5 do M.2 (par ≤ 10 mm), a In2 inteira como GND, os conectores das 4 fileiras e o da tela;
- o `POSICIONAMENTO.md` da placa principal para o **portão P (parte 1)**.

A **régua** espera a decisão da tecla (itens 2 e 3). Esquema e posicionamento da régua formam o portão P (parte 2), na R4V4.

## Tarefas para o Code (R3V4)

1. **[Design]** Medir no STEP da KS-20 o topo plano, o pino e a janela das presilhas (item 1).
2. **[Design]** Estudar a **T3-G** (item 2): espessura de grade aceita, sanduíche régua + grade-régua, fixação ao degrau, deck sem pré-carga (refazer espessura, postes, haste e altura da caixa), fit check em 28/44/60/76.
3. **[Design]** Estudar a **Low Profile Magnetic Jade** (item 3) contra a KS-20, numa tabela com os critérios do item 3 e a recomendação.
4. **[Eletrônica]** Painel régua + grade-régua: área, preço estimado e se a montagem econômica aceita um painel com partes sem componentes.
5. **[Eletrônica]** Fase B da placa principal (item 7): esquema, ERC, BOM, `PINOS.md` final (com o microfone do item 6) e posicionamento sem trilhas, com `POSICIONAMENTO.md` para o portão P parte 1.
6. **[Programação e som]** Item 5 (rodízio na leitura quente, ADC duplo) e item 6 (efeitos de voz e orçamento de CPU), em `FIRMWARE.md`.
7. **[Design]** Corrigir no `CLAUDE.md` a régua de 74 × 12 para **74 × 14 mm** e registrar os arquivos da Gateron.
8. **[Design]** Fechar o `FIT_CHECK.md` com a recomendação **T3-G ou espuma** e **KS-20 ou Low Profile**, e terminar com "Perguntas para o design".

---

# Anexo — SPEC R2V4 (referência)

Data: 21 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Nomenclatura e protocolo como na R1V4 (anexo abaixo). Tudo o que não é mencionado aqui continua como na R1V4. O Code atende R1V4 e R2V4 juntas, num só ciclo, e o relatório cita "R2V4".

## Mudanças desde a R1V4

### 1. Fileiras: F2 escolhida (decisão 14)

O J aceitou a **F2: réguas de sensores em degraus no case inferior, com botão único**, combinada com a **T3**, e pede para verificar o que acontece com o custo.

- A **régua universal de 4 teclas** (§4.2 da R1V4) passa a ser a base do projeto. Para 28 teclas são 8 réguas, e cada módulo de +16 acrescenta 4.
- A placa principal fica só na área de interface (Teensy, energia, áudio, conectores, tela, encoders).
- O case inferior tem 4 degraus (passos de 2, 2 e 3 mm), e cada régua se apoia inteira no seu degrau. O deck da tampa acompanha os degraus e prende teclas e réguas (T3).
- Um modelo só de botão, com a mesma haste em todas as fileiras.
- A F1 deixa de ser projetada. Ela fica apenas como **referência de custo**, calculada a partir dos números da V3.

### 2. Verificação de custo (portão de custo)

A escolha está feita, mas o custo tem de ser confirmado antes da Fase B:
- custo por instrumento de 28 teclas e por pedido mínimo da JLCPCB, separado em placa principal, réguas, montagem (setup, estêncil, tipos Extended por desenho), cabos e conectores, e impressão do case;
- a mesma conta para a F1 (com os números da V3) e a diferença entre as duas;
- custo incremental de cada módulo de +16 na F2;
- **se a F2 sair mais de 25% mais cara que a F1** no protótipo de 28 teclas, o Code apresenta onde está a diferença e as formas de reduzi-la antes de seguir. Exemplos: régua de 2 camadas, painel com várias réguas num desenho só, conector mais barato ou solda direta. Abaixo disso, segue sem parar. O limite de 25% é critério do Chat, e o J pode mudar.

### 3. Régua: o que definir já nesta rodada

- **Ligação em cadeia** dentro da fileira e da fileira até a placa principal: comparar conector com cabo pronto (JST SH ou similar, com Basic se houver), FFC/FPC e solda direta de barra de pinos. Pesar custo, montagem em casa, confiabilidade e altura disponível sob o degrau. Nenhuma peça no topo da régua, onde fica a tecla.
- **Sinais:** VCC, GND, OUT da fileira e a cadeia de habilitação (DADO, CLOCK) com registrador de deslocamento, conforme a §5.2 da R1V4. Confirmar o registrador (Basic, se possível) e se o OUT compartilhado aguenta a carga de 20 sensores mais o cabo.
- **Painel:** ver se várias réguas cabem num desenho só, com destaque por furinhos (mouse bites) ou V-cut, para pagar uma taxa de preparação só. Confirmar que a JLCPCB monta pelo fundo um painel assim.
- **Encaixe no degrau:** como a régua é localizada (pinos do case em furos da régua ou rebaixo) e o bolso no degrau para os sensores e o registrador do fundo da régua.
- **Distância ímã-sensor:** igual à da V3, para que a calibração do firmware continue valendo.

## Tarefas para o Code (R2V4, somadas às da R1V4)

1. **[Eletrônica]** E3 passa a ser a **verificação de custo** do item 2, com a F1 só como referência. Em `ELETRONICA.md`, com a tabela de custo.
2. **[Eletrônica]** E5: esquema de princípio da régua (4 sensores, registrador, desacoplamento, conector), a forma de ligação escolhida e a viabilidade do painel (item 3).
3. **[Design]** D2 passa a ser só a F2: case conceitual com os 4 degraus, réguas, deck escalonado da T3, placa principal na interface e partições possíveis. Tamanho para 28, 44, 60 e 76.
4. **[Programação e som]** P1 e P2 partem da F2: varredura por fileira (4 linhas OUT) com a cadeia de registradores, para N réguas por fileira.
5. **[Design]** A tabela de decisão da tarefa 12 da R1V4 vira **tabela de custo e riscos da F2** (com a F1 de referência). Terminar com "Perguntas para o design".

---

# Anexo — SPEC R1V4 (referência)

Nomenclatura: **RnV4** = revisão n da SPEC da placa/instrumento V4 (R1V4, R2V4…). Os relatórios do Code citam sempre a revisão que atendem.

Data: 21 nov 2026 · Autor: Claude Chat (gestão e design) · Destino: Claude Code
Base: Student V3 (`student_v03/`, fechada para o protótipo, nada encomendado). A V3, a V2 e a V1 ficam como referência e **não são alteradas**.

Protocolo (igual ao da V3): o Chat escreve esta SPEC (R1V4, R2V4…, cada uma com "Mudanças desde a versão anterior" e "Tarefas para o Code"). O Code modela, verifica e responde no `FIT_CHECK.md` desta pasta, que termina com "Perguntas para o design". Depois faz commit → PR → merge. O Code nunca edita a SPEC. O J relata ao Chat: "SPEC RnV4 atendida — PR #x; relatórios atualizados". O Chat mescla cada revisão da SPEC no main automaticamente.

---

## 0. Decisões do J (21 nov 2026)

| # | Tema | Decisão |
|---|------|---------|
| 1 | Amostra da V3 | **Não haverá amostra.** A V4 parte do desenho atual e otimiza custo de protótipo. As incógnitas da V3 são resolvidas **por desenho, datasheets, desenhos do fabricante e integração virtual** (modelos STEP montados). |
| 2 | Custo | Protótipo de estudo, sem teto definido. Mesmo assim, toda escolha é comparada por custo. |
| 3 | Firmware | Em paralelo com o hardware. |
| 4 | O que é fixo | **Só o arranjo das teclas** (C-griff, passo 18,5, fileiras a 16,02, hexagonal) **e as 4 fileiras.** Tudo o mais pode mudar: tela, knobs, som, conectores, bateria, tamanho da placa e do case. As "medidas fixas" da V3 viram referência, não restrição. |
| 4b | Modularidade | O teclado de 28 teclas cresce em módulos de **+16 teclas** (44, 60, 76), mantendo a forma do final direito. Eletrônica detalhada e case final **só para 28**, mas o projeto tem de permitir as outras versões por parâmetro. Verificar se o Teensy dá conta de 76. |
| 5 | Montagem JLCPCB | Só pelo fundo. Sempre procurar peça **Basic** antes de Extended. |
| 6 | Placa | 1,2 mm. Se a grade sai ou fica é **decisão de estudo** (§3). |
| 7 | Alto-falante | Escolher um modelo real já na V4. |
| 8 | Fases | Posicionamento → **portão de aprovação do J** → roteamento numa SPEC própria (§6). |
| 9 | Roteamento | Todo pelo Code, por um **agente de roteamento** dedicado. O agente escolhe o método e tem de sobreviver a sessões interrompidas (§6.3). |
| 10 | USB 90 Ω | **Decidido:** o novo desenho do §5.4 (par curto, referência contínua, Full Speed), sem impedância controlada nem etapas extras à JLCPCB. |
| 11 | DRC | 0 erros, **0 avisos**, 0 ligações faltando, paridade 0. Sem exceções herdadas. |
| 12 | Fixação das teclas | **T3 escolhida** (a tampa prende o corpo da tecla contra a placa, §3). |
| 13 | Fixação do case | Com a T3 escolhida, entra em estudo nesta revisão (§8). |
| 14 | Fileiras | F1 (plana) × F2 (escalonada, botões iguais) em estudo (§4). O Chat apresentou a comparação visual ao J; a decisão vem na R2V4. |
| 15 | Processo do case | O mais barato. Outro fornecedor só se for **≥ 15% mais barato no total com frete** (aprovado); senão, tudo na JLC. |
| 16 | Acabamento e logo | **Fora da V4 até fechar o hardware.** Nada de faixas, cores, rebaixos nem textos no modelo. |
| 17 | Parede sem emenda | Desejável, mas podem ser estudadas outras partições se otimizarem fabricação e custo. |
| 18 | Pasta | `etutti/hardware/student_v04/`, sem logo. |
| 19 | Página e manual | Depois. |
| 20 | Ordem dos módulos | Padrão: 1º módulo para o agudo, 2º para o grave, e assim por diante. É só o mapa de notas padrão: o usuário reconfigura, e os 6 registros padrão de acordeão também trazem o seu mapa (§4.4). |
| 21 | Peça de teste impressa | Decidir ao finalizar o hardware, por preço e pelo risco que ela eliminaria. |

---

## 1. Mudanças desde a V3

1. **Fim da dependência da amostra.** Cada incógnita da lista "medir na primeira amostra" da V3 vira uma tarefa de datasheet ou de modelo do fabricante (§7). O que não puder ser resolvido assim é declarado como **risco aceito** no FIT_CHECK, com o impacto se estiver errado.
2. **Fixo só o teclado.** Placa, interface e case podem ser refeitos. A V3 deixa de ser contrato e passa a ser o ponto de partida.
3. **Teclado modular** (28 → 44 → 60 → 76) e verificação da capacidade do Teensy (§4.3, §5.2).
4. **Fixação das teclas e arquitetura das fileiras em aberto**, com alternativas a quantificar (§3, §4).
5. **Varredura dos sensores revista:** o TMAG5253 deixa a saída em alta impedância quando desligado, o que pode **eliminar os multiplexadores** (§5.2).
6. **USB resolvido por desenho** (§5.4).
7. **Roteamento separado do posicionamento**, com portão de aprovação e agente dedicado (§6).
8. **Case de duas peças com processo pelo menor custo**, sem acabamento (§8).
9. **Firmware completo em paralelo** (§9).

---

## 2. Fases da V4

| Fase | O que entrega | Como fecha |
|------|---------------|------------|
| **A — Arquitetura** (esta SPEC) | Detalhamento da T3, fixação do case, estudo das fileiras, varredura dos sensores, capacidade do Teensy, custo comparado, escolha de peças, processo do case. | O J escolhe as alternativas (R2V4). |
| **B — Esquema e posicionamento** | Esquema, BOM com Basic/Extended, placa(s) posicionadas **sem trilhas**, case conceitual integrado. | **Portão P:** relatório de congelamento + aprovação explícita do J. |
| **C — Roteamento** | Placa(s) roteadas pelo agente de roteamento. | DRC 0/0/0 + paridade 0 + relatório. |
| **D — Case detalhado e fabricação** | Case final de 28 teclas, fit check integrado, flexão, acústica, Gerbers/BOM/CPL, arquivos de impressão, custo. | FIT_CHECK sem pendências e decisão do J de encomendar ou não. |

Firmware (§9) corre ao lado de todas as fases.

---

## 3. Fixação das teclas: T3 escolhida

Na V3, a tecla se apoia na placa pelos 2 pinos de plástico, e a grade de FR-4 (com 10 espaçadores, 10 parafusos escareados, 10 porcas e os copos da bandeja) impede que ela saia. A meta do J é **teclado firme, sem folga, ao menor custo**.

| Alt. | Como funciona | A favor | Contra / risco |
|------|---------------|---------|----------------|
| **T1 — Grade FR-4 simplificada** | Mantém a grade, mas **sem escareado e sem parafusos próprios**: ela fica presa por pressão entre a tampa e espaçadores ou postes. A tecla encaixa na grade como num teclado comum. | Sensação comprovada, já que é como os teclados low-profile são feitos. Tolerância de FR-4 de fábrica. | Mais um pedido de placa (com custo e frete). Com fileiras escalonadas (§4) seriam 4 grades. |
| **T2 — Tampa como grade (encaixe)** | O deck interno da tampa tem a abertura e a espessura de grade do desenho da Gateron, e a tecla encaixa nas presilhas direto no plástico impresso. | Zero peças a mais. Duas peças só. | Depende da tolerância da impressão. O plástico pode ceder com o tempo nas presilhas (fluência), e a folga volta. O deck pode fletir entre as teclas. |
| **T3 — Tampa prende o corpo da tecla contra a placa (captura)** | A tecla fica posicionada **lateralmente pelos 2 pinos na placa**, com furos de fábrica precisos. O deck da tampa desce sobre o **ombro do corpo** de cada tecla e a prende verticalmente com pequena interferência, por nervuras de esmagamento que absorvem a tolerância. É a ideia do J ("a tampa fecha o conjunto") com contato garantido. | Zero peças a mais. O alinhamento vem da placa (preciso), não da impressão. As nervuras toleram a variação do processo. | O furo do pino tem jogo e só a pré-carga vertical tira a folga. Precisa do desenho do corpo da KS-20 para saber onde há ombro para apoiar. O deck tem de ser rígido. |
| **T4 — Só pinos, tampa sem contato** | A tecla fica só nos pinos e a tampa apenas fecha. | Mais simples. | Folga lateral e vertical: a tecla pode até sair. **Entra só como referência** para medir quanto T3 melhora. |

**Decisão do J (21 nov): T3.** A tabela fica como registro. T1 é o plano B, e só volta se os números da T3 falharem (folga ou inclinação acima do aceitável). T2 e T4 saem.

**Detalhamento da T3 (tarefa D1):**
- obter o **desenho dimensional da KS-20** usada (o modelo exato da lista de compras: Orange), com corpo, ombro, pinos, presilhas, abertura e espessura de grade recomendadas e posição do ímã;
- onde o deck apoia no corpo da tecla (ombro), a área de contato e a folga para o curso da haste;
- nervuras de esmagamento: forma, número por tecla e interferência nominal, de modo que a pior combinação de tolerâncias (furo de pino da JLCPCB, tolerância publicada do processo de impressão) ainda deixe pré-carga e nenhuma folga;
- folga lateral pelos pinos na placa (diâmetro do furo para os pinos da KS-20) e inclinação da tecla sob 3 N na borda do botão;
- rigidez do deck: flexão entre apoios com as 28 teclas pré-carregadas, e com 3 N numa tecla;
- ordem de montagem em casa e se a tecla pode ser trocada depois;
- se algum desses números falhar, dizer quanto e comparar com T1.

---

## 4. Arquitetura das fileiras: plana ou escalonada

### 4.1 As duas opções

| Opção | Como é | Botões |
|-------|--------|--------|
| **F1 — Placa única plana** (como a V3) | Todos os sensores numa placa. As 4 alturas vêm das hastes dos botões. | 4 alturas de haste (21,9 / 23,9 / 25,9 / 28,9). |
| **F2 — Réguas escalonadas** | Placa principal só com a interface (Teensy, energia, áudio, conectores). Os sensores vão em **réguas de sensores** apoiadas em **degraus do case inferior**, uma altura por fileira (passos de 2, 2 e 3 mm, como hoje). | **Um botão só**, igual em todas as fileiras: mesma altura e mesma sensação ao tocar. |

### 4.2 Proposta para F2: régua universal de 4 teclas

- **Um único desenho de régua com 4 posições** (passo 18,5), usado em todas as fileiras. O deslocamento de meio passo entre fileiras vem da posição da régua no case, não do desenho.
- **28 teclas = 2 réguas por fileira = 8 réguas** (32 posições). As posições sem tecla ficam cobertas pela tampa, 4 no total (fileiras de 7, 8, 7 e 6).
- **Cada módulo de +16 = mais 1 régua por fileira = 4 réguas.** 44 = 12 réguas, 60 = 16, 76 = 20. A conta fecha exatamente com os módulos de 16 do J.
- A régua se apoia **contínua sobre o degrau** do case inferior. A flexão sob a tecla tende a zero, e a meta de 0,05 mm fica fácil de cumprir.
- As réguas se ligam em cadeia dentro de cada fileira (ver §5.2). A forma de ligação (conector, cabo, solda) é tarefa de estudo (E3).
- Combinação natural: **F2 + T3.** A tampa escalonada prende teclas e réguas ao mesmo tempo contra os degraus, sem parafuso nenhum na área do teclado.

### 4.3 O que o Code compara (tarefa E3 + D2)

Para F1 e F2, ambas com T3:
- **custo JLCPCB** por instrumento e por pedido mínimo: placa(s) por desenho, montagem por desenho (setup, estêncil, US$ 3,09 por tipo Extended **por desenho**), réguas a mais para os módulos;
- custo de conectores e cabos, e minutos de montagem em casa;
- confiabilidade da ligação entre réguas;
- tamanho e camadas da placa principal em F2 (2 ou 4 camadas; ≤ 100 × 100 mm baixa o preço?);
- distância ímã-sensor, que tem de ser igual nas duas opções para a calibração do firmware valer;
- como cada opção escala para 44, 60 e 76.

### 4.4 Módulos e notas (decisão 20)

- **Fisicamente**, o módulo entra sempre do lado direito, e a forma do final direito se repete. Cada módulo acrescenta 4 colunas, ou seja, uma oitava.
- **O mapa de notas é do firmware.** O padrão alterna: 1º módulo para o agudo, 2º para o grave, e assim por diante. 28 = G3–E5, 44 = G3–E6, 60 = G2–E6, 76 = G2–E7. Na prática, a versão de 60 toca o teclado transposto uma oitava abaixo.
- O usuário reconfigura o mapa, e cada um dos 6 registros padrão de acordeão traz o seu.

---

## 5. Eletrônica

### 5.1 Regras de peças

- Montagem JLCPCB **só pelo fundo**. No topo, apenas o que já era feito em casa (encoders, e o que a alternativa escolhida pedir).
- Para cada linha da BOM: existe Basic equivalente? Se não existe, dizer por quê. Meta: **menos tipos Extended que os 17 da V3**, sem perder função.
- Conferir pacote × footprint de **cada** código LCSC e gerar o CPL pelos pads do EasyEDA (lições da V1/V3: `cpl_jlc.py`, números de pad iguais aos da peça nova).
- USBLC6 e SMF5.0A ficam. O USB acorda o instrumento, sem trinco de energia.
- Parafusos e porcas não magnéticos perto das teclas.
- **Alto-falante real** (decisão 7): escolher um modelo com datasheet (Ø, altura, sensibilidade, Fs, Qts, Vas se houver) disponível na LCSC/JLC ou em fornecedor comum, e refazer a caixa acústica para ele.

### 5.2 Varredura dos sensores sem multiplexador

Datasheet do TMAG5253: com EN em nível baixo a saída OUT fica em **alta impedância**, e várias unidades podem dividir a mesma linha analógica. A TI cita até ~50 sensores por linha, pelo limite de 1 nF de carga. O ligar leva < 25 µs (bipolar) ou < 60 µs (unipolar) típicos.

Proposta a verificar (tarefa E2):
- **uma linha OUT por fileira** (4 entradas analógicas do Teensy), com os sensores da fileira ligados nela;
- **uma linha EN por coluna**, comum às 4 fileiras. Ao ligar a coluna k, os 4 sensores dela respondem, um em cada linha OUT, e são lidos juntos;
- em F2, a coluna é ligada por um **registrador de deslocamento em cada régua** (tipo 74HC164/595, conferir se há Basic) em cadeia, andando um "1" pela cadeia. Assim a régua é **idêntica em qualquer posição**: entram e saem só VCC, GND, OUT, DADO, CLOCK (e o que mais o estudo pedir);
- em F1 vale o mesmo, ou EN direto de pinos do Teensy.

**Contas que o Code tem de fazer:**
- tempo de varredura para 28 e 76 teclas, com o tempo de ligar **máximo** do datasheet (não o típico) e a variante de sensibilidade escolhida;
- se a resolução de velocity basta (o firmware da V1 usa 1 ms = 127 e 80 ms = 1). Se não basta, dividir cada fileira em 2 linhas OUT;
- capacitância da linha OUT com 20 sensores e trilhas/cabos;
- corrente média (só 4 sensores ligados por vez);
- pinos livres do MicroMod Teensy para 4–8 ADC + DADO/CLOCK + tela, I2S, encoders, USB, bateria e microfone;
- carga de CPU com síntese + varredura a 76 teclas.

Se a proposta falhar em algum ponto, o Code explica onde e propõe a menor mudança (por exemplo, voltar aos multiplexadores só para os módulos).

### 5.3 Placa

- 1,2 mm (decisão 6). As camadas ficam livres: 2 se couber, 4 se precisar.
- Em F2, a placa principal fica só na área de interface e tem de ser a menor possível.
- Em F1, revisar o contorno da V3 para o novo case.

### 5.4 USB sem impedância controlada (decidido)

O J aprovou este desenho, que elimina o risco **por desenho**, sem opções extras no pedido. Os três itens são requisitos:
1. **Par curto:** USB-C o mais perto possível do conector M.2, com o par de D+/D− **≤ 10 mm** (hoje 17,2 mm).
2. **Referência contínua:** o par corre numa camada externa com **plano de GND inteiro logo abaixo**. A largura e o espaço são calculados para ~90 Ω com o **empilhamento padrão publicado da JLCPCB** para 1,2 mm, que vale sem pedir controle de impedância. Sem via, sem cruzar fenda.
3. **Firmware em Full Speed (12 Mbit/s):** MIDI precisa de muito menos. Verificar no core Teensyduino 1.60 se o i.MX RT1062 pode ser forçado a Full Speed (bit PFSC do PORTSC1). A 12 Mbit/s, um par de poucos milímetros é eletricamente curto, e a impedância deixa de importar.

Com 1 + 2 + 3 o risco fica praticamente eliminado. Se o item 3 não for possível, 1 + 2 sozinhos já deixam o par bem dentro do que funciona em placas comuns. O Code confirma no relatório. O posicionamento (Fase B) coloca o USB-C e o M.2 lado a lado já pensando no item 1.

---

## 6. Posicionamento, portão e roteamento

### 6.1 Fase B: posicionamento

- Todas as peças posicionadas, **sem nenhuma trilha**, com as faces corretas e as regras (`.kicad_dru`) prontas.
- Os corredores de roteamento são reservados já no posicionamento: barramento OUT de cada fileira, par USB, áudio, alimentação.

### 6.2 Portão P: relatório de congelamento

O Code entrega `POSICIONAMENTO.md` com:
- vistas de topo e fundo (PNG) com as zonas e os corredores;
- a placa montada no case conceitual (folgas, alturas, conectores na parede);
- DRC sem trilhas: 0 erros de courtyard e furos;
- estimativa de roteabilidade: densidade do ratsnest por região e um ensaio de roteamento descartável, se o agente quiser;
- BOM com Basic/Extended e custo estimado.

**Nada é roteado antes do "aprovado" do J.** Depois do portão, mover peça exige nova aprovação.

### 6.3 Agente de roteamento

O Code cria `.claude/agents/roteamento.md`, um agente só para rotear. Requisitos:
- **Dono só do roteamento:** lê a placa posicionada e as regras, escreve trilhas, vias e zonas. **Nunca move peça.** Se uma rede não passa, registra um pedido de mudança de posicionamento para o agente de eletrônica, que volta ao portão.
- **Escolhe o método** (roteador próprio do repo, Freerouting em linha de comando, à mão por script, ou misto) e justifica no relatório. Sugestão: críticos à mão por script (USB, áudio, alimentação, barramentos OUT), depois o resto.
- **Retomável:** cada etapa é um script **idempotente** que lê `pcb/rota/estado.json` (etapas feitas, rede por rede, tentativas, último DRC) e continua de onde parou. Cada etapa concluída gera **commit** num ramo de trabalho. Uma sessão nova lê o estado e segue, sem refazer nada.
- **Etapas curtas:** nenhuma etapa depende de mais de ~10 min contínuos. Rotinas longas rodam em segundo plano com log de progresso.
- **Aceite:** DRC 0 erros e **0 avisos**, 0 ligações faltando, paridade 0, nenhuma trilha abaixo da largura mínima da regra, sem pontas soltas, planos sem ilhas. Relatório em `ROTEAMENTO.md`.
- O roteamento propriamente dito fica para a **SPEC da Fase C**. Nesta R1V4, o Code só cria e documenta o agente.

---

## 7. O que a amostra iria responder: agora por desenho

| Incógnita da V3 | Como resolver na V4 |
|-----------------|---------------------|
| Altura do USB-C e dos jacks, recuo das tomadas | Desenho dimensional e STEP do fabricante (HRO, XUNPU PJ-327A ou as peças novas) montados no modelo. |
| Pilha do módulo no H101 | Desenho da SparkFun (MicroMod Teensy) + datasheet do conector M.2 + espaçador e parafuso escolhidos. |
| Lado da boca do J401 | Desenho do conector JST SH escolhido. |
| Eixo e chato dos encoders | Datasheet Alps EC11E (o desenho dá a ponta a ~24,5 mm; adotar o datasheet, não o footprint). |
| Compressão do pé sob 3 N | Dureza Shore A → módulo pela tabela do material, e cálculo. Em F2 a flexão pode deixar de depender dos pés. |
| OLED, bateria, plugues | Desenhos dos fornecedores. Se faltar desenho, escolher outra peça que tenha. |
| Par USB | §5.4. |
| Escareado na JLCPCB | Desaparece se a grade sair ou ficar sem escareado (T1). |

Os modelos STEP vêm do EasyEDA pelo código LCSC (`model3d/fetch_models.py` da V1, sem rajadas). Se o acesso de rede falhar, o Code pede o arquivo ao J em vez de pular a verificação.

---

## 8. Case de duas peças

- **Duas peças:** case superior e case inferior. A placa entra por baixo, como na V3, salvo se o estudo mostrar partição melhor (decisão 17: a parede sem emenda é desejável, não obrigatória).
- **Sem acabamento:** nada de faixas, cores, logo ou rebaixos de pintura no modelo.
- **Processo pelo menor custo:** cotar na JLC3DP todos os processos que servem (resinas SLA, MJF, SLS, FDM) pelo volume real das peças. O processo também tem de atender à tolerância exigida pela T3 (§3) e não pode ceder sob a pré-carga das nervuras com o tempo (fluência). Outros fornecedores só entram se forem **≥ 15% mais baratos no total com frete** (decisão 15).
- **Orientação de impressão sem suporte nas faces que o dedo toca**, se o processo usar suporte.
- **Paramétrico para 28/44/60/76:** o comprimento cresce 4 × 18,5 = 74 mm por módulo. Verificar o tamanho máximo de impressão de cada processo. Se 60 ou 76 não couberem numa peça, indicar onde dividir.
- **Fixação do case (decisão 13, agora em estudo):** com a T3, o case superior tem de manter a pré-carga sobre todas as teclas. Propor 2–3 soluções: só parafusos e porcas (não magnéticos), insertos de latão termofixados, encaixes impressos + poucos parafusos. Para cada uma: número e posição dos pontos (sem parafuso visível na área do teclado), flexão do deck entre pontos, custo e montagem.

---

## 9. Firmware (em paralelo)

Do mais urgente ao menos:
1. Mapa de pinos da V4 como contrato (`pcb/PINOS.md`), gerado junto com o esquema.
2. Varredura nova (§5.2): ligar coluna, ler as fileiras, calibração por tecla, velocity, para 28 teclas e parametrizada até 76.
3. Tela OLED girada 180° (`setRotation(2)`), percentual de bateria, HP_DET, microfone, acordar por USB, KEEP pela atividade do usuário.
4. Full Speed USB (§5.4, item 3), se for possível.
5. Medir a carga de CPU por simulação ou estimativa a 76 teclas (o Teensy MicroMod não está disponível para medir; dizer se a conta é estimada).

Compila com `teensy:avr:teensyMM:usb=midi,speed=396`. O sketch continua compilando também para o eTuttino (Teensy 4.0).

---

## 10. Fora desta versão

Acabamento, cores e logo · página e manual · quantidade e série · encomenda.

---

## Tarefas para o Code

**Preparação**
1. **[Eletrônica]** Montar a base de `student_v04/` a partir da V3: só os **scripts** e as fontes (esquema, geometria, pcb, case, estudos, fornecimento), sem `fab/`, renders nem saídas geradas. Um `README.md` com a ordem de execução. A V3 não é alterada.
2. **[Eletrônica]** Criar o agente `.claude/agents/roteamento.md` (§6.3), e atualizar os agentes `design`, `eletronica` e `programacao-som` para incluir a Student V4 nas pastas de cada um. Documentar no `CLAUDE.md`.

**Fase A — estudos (tudo no `FIT_CHECK.md`, salvo onde indicado; cada relatório cita "R1V4")**
3. **[Design]** D1: desenho dimensional da KS-20 (o modelo da lista de compras) e detalhamento da T3 (§3): apoio no ombro, nervuras, tolerâncias, folgas, inclinação a 3 N, rigidez do deck, montagem.
3b. **[Design]** D4: fixação do case compatível com a T3 (§8), com 2–3 soluções comparadas.
4. **[Design]** D2: case conceitual para F1 e para F2 (degraus, réguas, interface), duas peças, com as partições possíveis (§8) e o tamanho por versão (28/44/60/76).
5. **[Design]** D3: cotação JLC3DP por processo para as peças de D2 e a tolerância publicada de cada processo. Apontar o mais barato que atende à fixação.
6. **[Eletrônica]** E1: revisão da BOM da V3 linha a linha (Basic × Extended, alternativas, pacote × footprint) e escolha do alto-falante real.
7. **[Eletrônica]** E2: varredura sem multiplexador (§5.2), com contas, pinos e esquema de princípio. Em `ELETRONICA.md`.
8. **[Eletrônica]** E3: comparação de custo e montagem F1 × F2 (§4.3), com a régua universal de 4 teclas e a forma de ligação entre réguas.
9. **[Eletrônica]** E4: proposta do par USB (§5.4), com distância, camada, largura e espaço pelo empilhamento padrão da JLCPCB e cálculo de ~90 Ω.
10. **[Programação e som]** P1: capacidade do Teensy para 76 teclas (pinos, ADC, tempo de varredura, CPU com síntese) e se Full Speed USB pode ser forçado. Em `FIRMWARE.md`.
11. **[Programação e som]** P2: começar o firmware da V4 (§9, itens 1–3) sobre o sketch existente, com a varredura parametrizada.
12. **[Design]** Fechar o `FIT_CHECK.md` com uma **tabela de decisão** F1 × F2 (com T3): custo, firmeza, montagem, risco, escalabilidade, e a recomendação do Code. Terminar com "Perguntas para o design".

**Não fazer nesta versão:** posicionar peças definitivamente, rotear, detalhar o case final, gerar arquivos de fabricação.
