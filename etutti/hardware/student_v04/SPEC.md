# eTutti Student V4 — SPEC v1

Data: 21 nov 2026 · Autor: Claude Chat (gestão e design) · Destino: Claude Code
Base: Student V3 (`student_v03/`, fechada para o protótipo, nada encomendado). A V3, a V2 e a V1 ficam como referência e **não são alteradas**.

Protocolo (igual ao da V3): o Chat escreve esta SPEC (v1, v2…, cada uma com "Mudanças desde a versão anterior" e "Tarefas para o Code"). O Code modela, verifica e responde no `FIT_CHECK.md` desta pasta, que termina com "Perguntas para o design". Depois faz commit → PR → merge. O Code nunca edita a SPEC. O J relata ao Chat: "SPEC vN atendida — PR #x; relatórios atualizados".

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
| 10 | USB 90 Ω | Resolver **por desenho**, sem pedir impedância controlada nem etapas extras à JLCPCB (§5.4). |
| 11 | DRC | 0 erros, **0 avisos**, 0 ligações faltando, paridade 0. Sem exceções herdadas. |
| 12 | Fixação das teclas | Em escolha. O Chat apresenta alternativas (§3), o Code quantifica e o J decide. |
| 13 | Fixação do case | Depois que a fixação das teclas for escolhida. |
| 14 | Fileiras | Estudar fileiras escalonadas pelo case inferior, com botões todos iguais (§4). |
| 15 | Processo do case | O mais barato. Se a diferença for pequena, tudo na JLC (JLCPCB + JLC3DP). |
| 16 | Acabamento e logo | **Fora da V4 até fechar o hardware.** Nada de faixas, cores, rebaixos nem textos no modelo. |
| 17 | Parede sem emenda | Desejável, mas podem ser estudadas outras partições se otimizarem fabricação e custo. |
| 18 | Pasta | `etutti/hardware/student_v04/`, sem logo. |
| 19 | Página e manual | Depois. |

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
| **A — Arquitetura** (esta SPEC) | Estudo das alternativas de fixação e de fileiras, varredura dos sensores, capacidade do Teensy, custo comparado, escolha de peças, processo do case. | O J escolhe as alternativas (SPEC v2). |
| **B — Esquema e posicionamento** | Esquema, BOM com Basic/Extended, placa(s) posicionadas **sem trilhas**, case conceitual integrado. | **Portão P:** relatório de congelamento + aprovação explícita do J. |
| **C — Roteamento** | Placa(s) roteadas pelo agente de roteamento. | DRC 0/0/0 + paridade 0 + relatório. |
| **D — Case detalhado e fabricação** | Case final de 28 teclas, fit check integrado, flexão, acústica, Gerbers/BOM/CPL, arquivos de impressão, custo. | FIT_CHECK sem pendências e decisão do J de encomendar ou não. |

Firmware (§9) corre ao lado de todas as fases.

---

## 3. Fixação das teclas: alternativas

Na V3, a tecla se apoia na placa pelos 2 pinos de plástico, e a grade de FR-4 (com 10 espaçadores, 10 parafusos escareados, 10 porcas e os copos da bandeja) impede que ela saia. A meta do J é **teclado firme, sem folga, ao menor custo**.

| Alt. | Como funciona | A favor | Contra / risco |
|------|---------------|---------|----------------|
| **T1 — Grade FR-4 simplificada** | Mantém a grade, mas **sem escareado e sem parafusos próprios**: ela fica presa por pressão entre a tampa e espaçadores ou postes. A tecla encaixa na grade como num teclado comum. | Sensação comprovada, já que é como os teclados low-profile são feitos. Tolerância de FR-4 de fábrica. | Mais um pedido de placa (com custo e frete). Com fileiras escalonadas (§4) seriam 4 grades. |
| **T2 — Tampa como grade (encaixe)** | O deck interno da tampa tem a abertura e a espessura de grade do desenho da Gateron, e a tecla encaixa nas presilhas direto no plástico impresso. | Zero peças a mais. Duas peças só. | Depende da tolerância da impressão. O plástico pode ceder com o tempo nas presilhas (fluência), e a folga volta. O deck pode fletir entre as teclas. |
| **T3 — Tampa prende o corpo da tecla contra a placa (captura)** | A tecla fica posicionada **lateralmente pelos 2 pinos na placa**, com furos de fábrica precisos. O deck da tampa desce sobre o **ombro do corpo** de cada tecla e a prende verticalmente com pequena interferência, por nervuras de esmagamento que absorvem a tolerância. É a ideia do J ("a tampa fecha o conjunto") com contato garantido. | Zero peças a mais. O alinhamento vem da placa (preciso), não da impressão. As nervuras toleram a variação do processo. | O furo do pino tem jogo e só a pré-carga vertical tira a folga. Precisa do desenho do corpo da KS-20 para saber onde há ombro para apoiar. O deck tem de ser rígido. |
| **T4 — Só pinos, tampa sem contato** | A tecla fica só nos pinos e a tampa apenas fecha. | Mais simples. | Folga lateral e vertical: a tecla pode até sair. **Entra só como referência** para medir quanto T3 melhora. |

**Avaliação preliminar do Chat:** T3 é a candidata principal, porque junta duas peças só, custo zero de peça extra e alinhamento de fábrica. T1 é a alternativa de segurança. T2 só vale se a tolerância publicada do processo escolhido couber na janela do encaixe da Gateron.

**O que o Code precisa fazer para o J decidir (tarefa D1):**
- obter o **desenho dimensional da KS-20** usada (o modelo exato da lista de compras: Orange), com corpo, ombro, pinos, presilhas, abertura e espessura de grade recomendadas e posição do ímã;
- para cada alternativa: pilha de tolerâncias (furo de pino da JLCPCB, tolerância publicada do processo de impressão), folga lateral e vertical resultantes, inclinação da tecla sob 3 N na borda do botão, e flexão do deck entre apoios;
- custo de cada alternativa (peças, pedido, montagem) e minutos de montagem em casa.

---

## 4. Arquitetura das fileiras: plana ou escalonada

### 4.1 As duas opções

| Opção | Como é | Botões |
|-------|--------|--------|
| **R1 — Placa única plana** (como a V3) | Todos os sensores numa placa. As 4 alturas vêm das hastes dos botões. | 4 alturas de haste (21,9 / 23,9 / 25,9 / 28,9). |
| **R2 — Réguas escalonadas** | Placa principal só com a interface (Teensy, energia, áudio, conectores). Os sensores vão em **réguas de sensores** apoiadas em **degraus do case inferior**, uma altura por fileira (passos de 2, 2 e 3 mm, como hoje). | **Um botão só**, igual em todas as fileiras: mesma altura e mesma sensação ao tocar. |

### 4.2 Proposta para R2: régua universal de 4 teclas

- **Um único desenho de régua com 4 posições** (passo 18,5), usado em todas as fileiras. O deslocamento de meio passo entre fileiras vem da posição da régua no case, não do desenho.
- **28 teclas = 2 réguas por fileira = 8 réguas** (32 posições). As posições sem tecla ficam cobertas pela tampa, 4 no total (fileiras de 7, 8, 7 e 6).
- **Cada módulo de +16 = mais 1 régua por fileira = 4 réguas.** 44 = 12 réguas, 60 = 16, 76 = 20. A conta fecha exatamente com os módulos de 16 do J.
- A régua se apoia **contínua sobre o degrau** do case inferior. A flexão sob a tecla tende a zero, e a meta de 0,05 mm fica fácil de cumprir.
- As réguas se ligam em cadeia dentro de cada fileira (ver §5.2). A forma de ligação (conector, cabo, solda) é tarefa de estudo (E3).
- Combinação natural: **R2 + T3.** A tampa escalonada prende teclas e réguas ao mesmo tempo contra os degraus, sem parafuso nenhum na área do teclado.

### 4.3 O que o Code compara (tarefa E3 + D2)

Para R1 e R2, combinadas com T1 e T3:
- **custo JLCPCB** por instrumento e por pedido mínimo: placa(s) por desenho, montagem por desenho (setup, estêncil, US$ 3,09 por tipo Extended **por desenho**), réguas a mais para os módulos;
- custo de conectores e cabos, e minutos de montagem em casa;
- confiabilidade da ligação entre réguas;
- tamanho e camadas da placa principal em R2 (2 ou 4 camadas; ≤ 100 × 100 mm baixa o preço?);
- distância ímã-sensor, que tem de ser igual nas duas opções para a calibração do firmware valer;
- como cada opção escala para 44, 60 e 76.

### 4.4 Faixa de notas dos módulos (premissa a confirmar)

Cada módulo acrescenta 4 colunas, ou seja, uma oitava, **para o agudo**. A forma do final direito se repete: 44 = G3–E6 (como o eTuttino de 44), 60 = G3–E7, 76 = G3–E8. Se o J preferir que os módulos estendam para o grave, muda só o mapa de notas.

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
- em R2, a coluna é ligada por um **registrador de deslocamento em cada régua** (tipo 74HC164/595, conferir se há Basic) em cadeia, andando um "1" pela cadeia. Assim a régua é **idêntica em qualquer posição**: entram e saem só VCC, GND, OUT, DADO, CLOCK (e o que mais o estudo pedir);
- em R1 vale o mesmo, ou EN direto de pinos do Teensy.

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
- Em R2, a placa principal fica só na área de interface e tem de ser a menor possível.
- Em R1, revisar o contorno da V3 para o novo case.

### 5.4 USB sem impedância controlada

Objetivo: eliminar o risco **por desenho**, sem opções extras no pedido.
1. **Par curto:** USB-C o mais perto possível do conector M.2, com o par de D+/D− **≤ 10 mm** (hoje 17,2 mm).
2. **Referência contínua:** o par corre numa camada externa com **plano de GND inteiro logo abaixo**. A largura e o espaço são calculados para ~90 Ω com o **empilhamento padrão publicado da JLCPCB** para 1,2 mm, que vale sem pedir controle de impedância. Sem via, sem cruzar fenda.
3. **Firmware em Full Speed (12 Mbit/s):** MIDI precisa de muito menos. Verificar no core Teensyduino 1.60 se o i.MX RT1062 pode ser forçado a Full Speed (bit PFSC do PORTSC1). A 12 Mbit/s, um par de poucos milímetros é eletricamente curto, e a impedância deixa de importar.

Com 1 + 2 + 3 o risco fica praticamente eliminado. Se o item 3 não for possível, 1 + 2 sozinhos já deixam o par bem dentro do que funciona em placas comuns. O Code confirma no relatório.

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
- O roteamento propriamente dito fica para a **SPEC da Fase C**. Nesta v1, o Code só cria e documenta o agente.

---

## 7. O que a amostra iria responder: agora por desenho

| Incógnita da V3 | Como resolver na V4 |
|-----------------|---------------------|
| Altura do USB-C e dos jacks, recuo das tomadas | Desenho dimensional e STEP do fabricante (HRO, XUNPU PJ-327A ou as peças novas) montados no modelo. |
| Pilha do módulo no H101 | Desenho da SparkFun (MicroMod Teensy) + datasheet do conector M.2 + espaçador e parafuso escolhidos. |
| Lado da boca do J401 | Desenho do conector JST SH escolhido. |
| Eixo e chato dos encoders | Datasheet Alps EC11E (o desenho dá a ponta a ~24,5 mm; adotar o datasheet, não o footprint). |
| Compressão do pé sob 3 N | Dureza Shore A → módulo pela tabela do material, e cálculo. Em R2 a flexão pode deixar de depender dos pés. |
| OLED, bateria, plugues | Desenhos dos fornecedores. Se faltar desenho, escolher outra peça que tenha. |
| Par USB | §5.4. |
| Escareado na JLCPCB | Desaparece se a grade sair ou ficar sem escareado (T1). |

Os modelos STEP vêm do EasyEDA pelo código LCSC (`model3d/fetch_models.py` da V1, sem rajadas). Se o acesso de rede falhar, o Code pede o arquivo ao J em vez de pular a verificação.

---

## 8. Case de duas peças

- **Duas peças:** case superior e case inferior. A placa entra por baixo, como na V3, salvo se o estudo mostrar partição melhor (decisão 17: a parede sem emenda é desejável, não obrigatória).
- **Sem acabamento:** nada de faixas, cores, logo ou rebaixos de pintura no modelo.
- **Processo pelo menor custo:** cotar na JLC3DP todos os processos que servem (resinas SLA, MJF, SLS, FDM) pelo volume real das peças. O processo também tem de atender à tolerância exigida pela fixação escolhida (§3). Outros fornecedores só entram se forem **≥ 15% mais baratos no total com frete** (critério do Chat; o J pode mudar).
- **Orientação de impressão sem suporte nas faces que o dedo toca**, se o processo usar suporte.
- **Paramétrico para 28/44/60/76:** o comprimento cresce 4 × 18,5 = 74 mm por módulo. Verificar o tamanho máximo de impressão de cada processo. Se 60 ou 76 não couberem numa peça, indicar onde dividir.
- A fixação do case (parafusos, insertos) fica para a SPEC v2, depois da escolha da fixação das teclas (decisão 13).

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

**Fase A — estudos (tudo no `FIT_CHECK.md`, salvo onde indicado)**
3. **[Design]** D1: desenho dimensional da KS-20 (o modelo da lista de compras) e estudo das alternativas T1–T4 (§3): tolerâncias, folgas, inclinação a 3 N, flexão do deck, custo, montagem.
4. **[Design]** D2: case conceitual para R1 e para R2 (degraus, réguas, interface), duas peças, com as partições possíveis (§8) e o tamanho por versão (28/44/60/76).
5. **[Design]** D3: cotação JLC3DP por processo para as peças de D2 e a tolerância publicada de cada processo. Apontar o mais barato que atende à fixação.
6. **[Eletrônica]** E1: revisão da BOM da V3 linha a linha (Basic × Extended, alternativas, pacote × footprint) e escolha do alto-falante real.
7. **[Eletrônica]** E2: varredura sem multiplexador (§5.2), com contas, pinos e esquema de princípio. Em `ELETRONICA.md`.
8. **[Eletrônica]** E3: comparação de custo e montagem R1 × R2 (§4.3), com a régua universal de 4 teclas e a forma de ligação entre réguas.
9. **[Eletrônica]** E4: proposta do par USB (§5.4), com distância, camada, largura e espaço pelo empilhamento padrão da JLCPCB e cálculo de ~90 Ω.
10. **[Programação e som]** P1: capacidade do Teensy para 76 teclas (pinos, ADC, tempo de varredura, CPU com síntese) e se Full Speed USB pode ser forçado. Em `FIRMWARE.md`.
11. **[Programação e som]** P2: começar o firmware da V4 (§9, itens 1–3) sobre o sketch existente, com a varredura parametrizada.
12. **[Design]** Fechar o `FIT_CHECK.md` com uma **tabela de decisão** (T × R): custo, firmeza, montagem, risco, escalabilidade, e a recomendação do Code. Terminar com "Perguntas para o design".

**Não fazer nesta versão:** posicionar peças definitivamente, rotear, detalhar o case final, gerar arquivos de fabricação.
