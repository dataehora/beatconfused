# eTutti Student V4 — SPEC R15V4

Data: 23 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Complementa a R14V4: o Code atende a R14V4 primeiro e depois esta, no mesmo PR ou no seguinte. Tudo o que não é mencionado aqui continua como nas revisões anteriores. Os relatórios citam "R15V4".

**Regras que continuam:**
- só o instrumento de 32 teclas detalhado;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

## 1. Serigrafia da placa principal (Eletrônica)

Na pré-visualização da JLCPCB e no 3D do KiCad os textos da serigrafia ficam empilhados e ilegíveis: referências e valores (inclusive os códigos LCSC, como "C25741") de todas as peças 0402/0603, uma em cima da outra. Limpar, **só na serigrafia** (nenhuma trilha, pad, via, zona ou posição muda):

- **Fica na serigrafia** (o que ajuda quem monta em casa):
  - nome e versão da placa;
  - rótulos dos conectores: J601–J604 como "FILEIRA 1…4 / ROW 1…4" (J601 = fileira 1), J401 "OLED", J202 "BAT", J201 "USB", J301/J302 com a função de cada um, pads do alto-falante "SPK + / −";
  - "PROG" junto ao SW403;
  - marcas de pino 1 e de polaridade;
  - furos H1..H4 e H101 se ajudarem na montagem.
- **Sai da serigrafia** para a camada de fabricação (F.Fab/B.Fab), onde continua no KiCad e nos desenhos de montagem: todas as outras referências e todos os valores, incluindo os campos de código LCSC e os textos "sem peça (pad)" e "não montar".
- **Nenhum texto sobre pad nem sobre outro texto.** Altura e traço dentro do mínimo da JLCPCB (o Code confirma os números). Checagens de serigrafia do KiCad (sobreposição e texto sobre cobre exposto) com **0**.
- **Régua:** só conferir que já atende (parece limpa); não mexer se atender.
- **Depois:** DRC 0 erros e 0 avisos, 0 faltando, paridade 0, cobre idêntico ao da roteada (comparar os Gerbers de cobre, máscara e furação: só a serigrafia pode mudar). Regenerar `fab/principal/` e os renders, e o 3D do KiCad (`*_3d.kicad_pcb`).

## 2. Configuração de compra da principal (Eletrônica, `fab/COMPRA.md` e página)

- **Specify Stackup = No.** O empilhamento padrão da JLCPCB basta: o par USB é Full Speed e tem 7,4 mm; não há linha de impedância controlada. Um empilhamento especificado obriga a montagem Standard.
- **PCBA Type = Economic sempre que a placa permitir.** A JLCPCB passou a principal para Standard ao subir BOM e CPL, sem aviso. Nenhuma peça é "Standard only" (o J conferiu). Suspeitas, pela tabela de capacidades:
  - o U301 (SGTL5000), com pinos a 0,4 mm, no limite do Economic;
  - USB-C e jacks passando da borda.
  
  O J vai testar e informa o resultado. Se for o codec, fica Standard (cerca de US$ 24 a mais). Se forem as peças na borda, o Code avalia tirá-las da montagem e passá-las para as peças soldadas em casa, e informa o custo e o risco antes de mudar.
- Cotação real da principal com Standard: US$ 158 (placa 25,50 + montagem 132,62; setup 25,75, stencil 8,27, peças 46,29, carga dos alimentadores 49,60, SMT 2,21, embalagem 0,50; montagem em 3–4 dias, sem custo extra).

## 3. Opção futura registrada (Eletrônica, só texto)

Em `ELETRONICA.md`, uma nota curta: **"RT1062 na placa (chip-down) para produção em quantidade (≥ ~50 unidades)"**:
- ganho estimado de cerca de US$ 10 por placa e de alguns milímetros de altura;
- custo de um projeto novo da seção do processador (o fan-out do BGA foi o que parou o Viaggio), de 6 a 8 tipos Extended a mais e do chip de bootloader da PJRC.

Não é feito agora: o protótipo segue com o MicroMod.

## Tarefas para o Code (R15V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Eletrônica | limpar a serigrafia da principal e regenerar o pacote (item 1) |
| 2 | Eletrônica | configuração de compra e opção futura (itens 2 e 3) |
| 3 | Programação e som | página: imagens da placa novas e "Como pedir" com Specify Stackup = No |

**Perguntas que o Chat espera:**
- os renders novos da principal (topo e fundo) mostrando a serigrafia limpa;
- a confirmação de que o cobre não mudou.

---

# Anexo — SPEC R14V4 (referência)

Data: 23 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #204 (relatórios da R13V4) e às cotações e pré-visualizações da JLCPCB que o J fez. Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R14V4".

**Regras que continuam:**
- planta, corte e isométrico da base a cada mudança dela;
- nome da nota em cada tecla;
- só o instrumento de 32 teclas detalhado até a compra;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

## Cotação e pré-visualização da JLCPCB (J, 23 nov)

- **Placa principal: US$ 158** (5 placas, 2 montadas; ENIG, JLC04121H-7628, JST originais). A estimativa do Code era 113–138: o J manda ao Chat a decomposição; o Code usa US$ 158 como valor real.
- **Régua R8, painel de 2: US$ 72** (5 painéis, 2 montados = 4 réguas). Bate com a estimativa (~73).
- **Pré-visualização conferida pelo Chat contra as figuras do Code: bate.**
  - **Principal:** J601–J604 na borda dos cabos, USB-C e os dois jacks na borda oposta, J401, J202, SW403, M.2 e os CIs nos lugares das figuras do Code, com o pino 1 no mesmo canto.
  - **Régua:** J1 IN com corpo e boca, 8 TMAG5253, 74HC595 e C10 nos lugares.
  - Os 4 modelos deslocados da EasyEDA não aparecem como problema na tela da JLCPCB.
- O texto de serigrafia "J2 OUT (só nas E)" aparece na R8: aceito (ajuda a quem monta uma R8E).

## Decisões

1. **Costelas de pressão** nos bolsos sextavados das porcas M2 (opção proposta pelo design): a porca fica presa ao virar a base.
2. **Pés adesivos** colados direto na face de baixo da base, sem rebaixo.
3. **Recomendações do Chat aceitas** (o J não se opôs):
   - os 15 parafusos da tampa em **M2 × 14**;
   - a eletrônica confirma o giro do MicroMod pelo desenho da SparkFun;
   - a página segue a ordem de montagem do design;
   - os 4 modelos deslocados da EasyEDA ficam como estão.

## Tarefas

### 1. Espaço dos parafusos M2 das réguas: conferência e figura (Design)

O J quer ver que os parafusos cabem. O relatório R11V4 diz "cabeça Ø3,8 sobre a régua, no vão de 3,1 mm entre carcaças (fit check 0)": explicar com números como uma cabeça de 3,8 cabe num vão de 3,1 (a que altura estão a cabeça, as abas das carcaças e a grade-régua).

**Figura** `case/renders/regua_parafusos_r14.png`: vista de cima de uma R8, em escala, com a grade-régua e os 2 parafusos M2 encaixados:
- **metade esquerda com as teclas KS-20 montadas;**
- **metade direita sem teclas**, mostrando a grade, os furos dos pinos, os sensores, o 74HC595, o J1 e as cabeças dos parafusos;
- cotas: cabeça até a carcaça vizinha, cabeça até a borda da janela da grade, cabeça até o trilho;
- nome da nota sobre cada posição de tecla;
- um corte no eixo de um parafuso (régua, grade, cabeça, porca no bolso com as costelas, trilho).

**Acesso da ferramenta:** o passo 8 aperta os parafusos com as teclas já montadas. Conferir que a ponta da chave (dizer qual: Phillips #0, sextavada 1,5 ou Torx) e a haste passam entre as carcaças até a cabeça. Se não passarem, mudar a ordem (parafusos antes das teclas, sem tirar a grade) ou o parafuso (cabeça menor, sextavado interno), e dizer qual.

### 2. Renders conferidos peça por peça (Design)

- **Conectores e cabos fora do lugar nos renders:** no `passo_8` os plugues IN e os cabos aparecem soltos fora das réguas e do case, e há barras pretas finas passando das pontas das réguas (fileiras 1 a 3). Na JLCPCB os conectores estão no lugar certo da placa. Conferir cada peça da cena contra as placas e o case:
  - J1 de cada régua na posição do CPL;
  - cabos pelo túnel até J601–J604;
  - grade-régua do comprimento certo.
  
  Corrigir e renderizar de novo todas as figuras afetadas.
- **Janela do OLED** em `foto_instrumento`: parece um recorte vazio. Mostrar a tela (acesa, com a tela de estado do firmware, `telas_oled.py`) atrás do acrílico.
- **Alto-falante, bateria, capas, parafusos, pés:** continuam primitivas com medidas reais (aceito).

### 3. Costelas de pressão e pés (Design)

- **Costelas** nos bolsos das 8 porcas M2, incluindo o bolso da porca fina da fileira 4 (parede fina, risco 5 do R11V4): número, altura e interferência (o design propõe ~0,1 mm), para MJF PA12. Conferir que a porca entra com o dedo ou com o parafuso puxando e não cai com a base virada.
- **Pés adesivos:** escolher o produto (redondo, adesivo 3M, borracha ou silicone, altura 1–2 mm), posições a ≥ 9 mm de furos e bolsos, quantidade (6 ou mais se a figura pedir). Mandar para `fab/COMPRA.md` (loja e código).
- Fit check das 32 teclas e figuras da base (planta, corte, isométrico, `iso_base_r14`).

### 4. Eletrônica

- **MicroMod:** confirmar giro e altura pelo desenho de montagem da SparkFun (folga de 0,3 mm sob a placa).
- **`MODELOS_3D.md`:** corrigir a tabela da R4E (74HC595 com "1142,50 mm", o mesmo erro de unidade já tratado na R8).
- **`fab/COMPRA.md`:** cotações reais (principal US$ 158, R8 US$ 72), M2 × 14 na tampa, pés escolhidos, total novo do protótipo.

### 5. Página e manual (Programação e som)

- Ordem e textos dos passos do design (R13V4), com M2 × 14, costelas de pressão (o passo 7 deixa de pedir fita) e pés adesivos.
- **Botão PROG:** dizer que se aperta com um palito pelo furo de Ø3 da base, e mostrar onde fica (figura).
- Incluir a figura da tarefa 1 no passo 8.
- Valores reais da JLCPCB em "Peças" e "Como pedir".
- Conferir no navegador outra vez (pt e en, 375 px, imagens e links).

## Tarefas para o Code (R14V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Design | parafusos M2 das réguas: números, acesso da ferramenta e figura (tarefa 1) |
| 2 | Design | costelas de pressão, pés adesivos, fit check e figuras da base (tarefa 3) |
| 3 | Design | renders conferidos e refeitos (tarefa 2) |
| 4 | Eletrônica | MicroMod, tabela R4E, `COMPRA.md` com valores reais (tarefa 4) |
| 5 | Programação e som | página e manual atualizados (tarefa 5) |

**Perguntas que o Chat espera nos relatórios:**
- a figura dos parafusos sobre a régua e a resposta sobre o acesso da ferramenta (e a ordem de montagem, se mudar);
- os renders corrigidos (o que estava fora do lugar e por quê);
- o total do protótipo com as cotações reais;
- o link da página atualizada.

---

# Anexo — SPEC R13V4 (referência)

Data: 23 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #201 (relatórios da R12V4) e à primeira cotação do J. Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R13V4".

**Regras que continuam:**
- planta, corte e isométrico da base a cada mudança dela;
- nome da nota em cada tecla;
- só o instrumento de 32 teclas detalhado até a compra;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

**Objetivo desta revisão: fechar o projeto para compra.** Toda peça das duas placas tem de aparecer no lugar e no giro certos, com um modelo 3D fiel, antes de o J encomendar.

## Cotação do J (23 nov)

- **Régua R8, painel de 2 réguas:** cerca de US$ 70 (5 painéis nus, 2 montados = 4 réguas = 32 sensores). É o painel escolhido.
- **Placa principal:** cerca de US$ 105, com:
  - **ENIG** (escolhido pelo J: passo fino no M.2, USB-C e codec);
  - empilhamento **JLC04121H-7628** (espessura real 1,12 mm ± 10 %, aceita);
  - vias "Plugged", via mínima 0,3/(0,4/0,45), sem controle de impedância.
- **Problema achado na pré-visualização da JLCPCB:** os conectores SH clone **XY-SM06B-SRSS-TB (C56123098)** aparecem sem corpo (sem modelo 3D), tanto em J1 das réguas quanto em J601–J604 da principal. Não dá para conferir giro e pino 1.

## Mudanças desde a R12V4

### 1. Conectores SH originais JST (Eletrônica)

- **J1 das réguas (R8, R8E, R4, R4E) e J601–J604 da principal:** de C56123098 para o **JST SM06B-SRSS-TB(LF)(SN), C160405** (mesmos pads, mesma altura; cerca de US$ 0,90 contra 0,07; no protótipo, cerca de US$ 7 a mais).
- **J401 (OLED):** de C51940130 para o **JST SM04B-SRSS-TB(LF)(SN), C160404**, pelo mesmo motivo de fidelidade (cerca de US$ 0,20).
- Conferir no EasyEDA que os dois códigos têm modelo 3D e que os pads do footprint deles batem com os da placa (`cpl_jlc.py`; os números dos pads iguais aos do componente novo, a lição dos jacks da V3).
- **Os clones ficam registrados** em `ELETRONICA.md` como opção para produção em quantidade, com a nota de que não têm modelo 3D na JLCPCB.
- Regenerar BOM e CPL de `fab/principal/` e de todos os pacotes de `fab/regua/`, e as folhas de cotação.

### 2. Conferência de posição e modelo 3D de todas as peças (Eletrônica)

Para cada peça montada pela JLCPCB nas duas placas (principal e R8; R8E/R4/R4E só a tabela):
1. **Modelo 3D:** baixar o STEP do EasyEDA pelo código LCSC (`fetch_models.py`, curl simples, sem rajadas: o EasyEDA recusa depois de uns doze pedidos) e anotar se existe. Peça sem modelo na JLCPCB é peça que o J não consegue conferir: trocar por um equivalente com modelo ou explicar por que não dá.
2. **Posição e giro:** montar uma **pré-visualização própria igual à da JLCPCB**: cada modelo do EasyEDA posto na posição e no giro do CPL (as mesmas regras do `cpl_jlc.py`, fundo espelhado), sobre a placa. Conferir:
   - o corpo cai sobre os pads (erro de ajuste em mm);
   - o pino 1 cai no pad 1 de cada CI, diodo, conector e polarizado (U*, D*, Q*, J*, L201 se tiver polaridade);
   - os conectores SH, o USB-C e os jacks com a boca para a borda certa.
3. **Placa em KiCad com modelos 3D fiéis:** ligar os mesmos STEP aos footprints (caminho relativo, a pasta de modelos fica fora do git como antes) e gerar renders do fundo e do topo da principal e da R8 com todos os corpos.
4. **Peças montadas em casa** (encoders EC11E18244AU, MicroMod, OLED Adafruit 326, alto-falante, bateria, teclas KS-20, parafusos): confirmar que cada uma tem modelo fiel na cena do instrumento (`model3d`/case) e listar as que ainda são caixas.

**Entrega:** `fornecimento/MODELOS_3D.md` (tabela: referência, código LCSC, modelo 3D sim/não, erro de ajuste, pino 1 ok, boca do conector ok) e as figuras `pcb/img/previa_jlc_principal_bottom.png`, `previa_jlc_principal_top.png`, `previa_jlc_r8_bottom.png`, `previa_jlc_r8_top.png`, com as referências escritas sobre as peças. **Critério de aceitação: nenhuma peça sem modelo, nenhum erro de pino 1 ou de boca, erro de ajuste ≤ 0,3 mm.**

### 3. O que o J confere depois (Eletrônica escreve, o J faz)

Na folha de cotação de cada placa, uma lista curta do que o J compara entre a pré-visualização da JLCPCB e as figuras do item 2: os 4 SH da principal, o J401, o USB-C, os 2 jacks, o J202 da bateria, o pino 1 de U202/U204/U301/U501 e, na régua, o J1, o 74HC595 e o giro dos 8 TMAG5253 (simétricos: conferir pelo ponto do pino 1).

### 4. Configuração de compra de cada item (Eletrônica)

Um arquivo, `fab/COMPRA.md`, com **tudo o que o J marca ou preenche em cada loja, item por item**, na ordem das telas, para que a compra seja copiar e conferir. Nada é comprado; o arquivo só deixa a compra pronta.

**JLCPCB, placa principal** (as escolhas já feitas pelo J; o Code confere e completa):

| Campo | Valor |
|---|---|
| Layers | 4 |
| Delivery Format | Single PCB |
| PCB Thickness | 1.2 mm |
| Specify Stackup | Yes → JLC04121H-7628 (1,12 mm real, aceito) |
| Material | FR4 TG135 |
| Surface Finish | ENIG |
| Outer / Inner Copper | 1 oz / 0,5 oz |
| Specify Layer Sequence | No |
| Via Covering | Plugged |
| Min via hole/diameter | 0.3 mm / (0.4/0.45 mm) |
| Board Outline Tolerance | ±0.2 mm (Regular) |
| Impedance control | não |
| Confirm Production file | No |
| Mark on PCB | Remove Mark |
| Electrical Test | Flying Probe Fully Test |
| Demais opções avançadas | No |
| PCB Assembly | ligado |
| PCBA Type | Economic |
| Assembly Side | Bottom Side |
| PCBA Qty | 2 (o mínimo; o Code confirma) |
| Tooling holes | Added by JLCPCB |
| Confirm Parts Placement | Yes no primeiro pedido, se for grátis (o Code confere; a JLCPCB manda a posição para o J aprovar antes de soldar) |
| Stencil / Fixture Storage | No |
| Parts Selection | By Customer (Self-Service) |
| BOM / CPL | `fab/principal/bom.csv` / `cpl.csv` |

**JLCPCB, régua R8 em painel de 2:** a mesma tabela, com: 2 camadas, Panel by Customer (1 coluna × 2 linhas, sem V-cut), HASL sem chumbo, sem stackup, 5 painéis nus, 2 montados (4 réguas), Tooling holes **Added by Customer** (o Code confere se o painel os tem; se não, Added by JLCPCB), BOM "Complete File". Para R8E, R4 e R4E, só as linhas que mudam.

**Demais itens**, cada um com loja (pelo menos uma no Reino Unido quando existir), código ou link, quantidade e opções a escolher:
- módulo SparkFun MicroMod Teensy;
- OLED Adafruit 326 + cabo Qwiic de 50 mm;
- cabos SH 6 vias A06SR06SR30K51B (4 + reserva? o Code propõe, o J decide);
- bateria 503450 de 3 fios com NTC;
- alto-falante Dayton CE28MB-8;
- teclas Gateron KS-20 Orange (32) e molas opcionais;
- capas das teclas;
- encoders EC11E18244AU e knobs;
- parafusos M2 (passantes por fileira, porcas, porca fina, PT formadores de rosca), pés de silicone;
- case em MJF PA12 (arquivos STL, material, cor, acabamento, opções do serviço).

O mesmo conteúdo vai para a página (item 5), na seção "Como pedir".

### 5. Página do modelo e manual completo (Programação e som, com figuras do Design)

Fechar a **página da Student V4** em `/etutti/studentV4/` (sem link na home, `noindex`, como as da V2/V3), escrita por script (`student_v04/pagina.py`, textos e preços lá), em **português e inglês** (um `.lang-block` por língua). O leitor é **alguém que nunca viu o projeto**: precisa entender o que é, pedir, montar e tocar sem outra ajuda.

Seções:
1. **O que é:** um acordeão cromático C-griff eletrônico de 32 teclas com sensores Hall e velocidade, som próprio (alto-falante, fones, MIDI USB); foto do instrumento pronto.
2. **Como funciona:** diagrama de blocos (réguas de sensores → varredura → MicroMod Teensy → codec/amplificador → saídas; bateria e carga; OLED e encoders); como a tecla vira nota e velocidade; o conceito modular em um parágrafo (48/64/80 teclas, sem detalhar).
3. **O teclado:** planta com o nome da nota em cada tecla; C-griff e B-griff.
4. **Peças:** lista por área e por fornecedor, com preço (faixas, como nas páginas anteriores) e total; o que vem montado da JLCPCB e o que é soldado ou montado em casa; ferramentas necessárias.
5. **Como pedir:** o conteúdo do `fab/COMPRA.md`, passo a passo, com as telas da JLCPCB descritas (o que subir, o que marcar, o que conferir na pré-visualização com as figuras do item 2).
6. **Montagem:** sequência completa, da frente para trás, **um passo por figura** em vista explodida com peças numeradas (renders fotográficos no Blender como na V3, versão em linhas se ajudar): separar as réguas do painel, soldar o que é de casa (encoders, fios do alto-falante), módulo MicroMod e parafuso, OLED, bateria, teclas nas réguas, réguas na base com cabos e parafusos (ordem e comprimento por fileira), tampa, capas, pés. Cuidados (LiPo, pó de fibra, torque do parafuso formador de rosca, ESD).
7. **Primeiro uso:** gravar o firmware (Teensyduino ou o arquivo `.hex` com o Teensy Loader), primeira ligação, calibração das teclas, o que o LED e a tela mostram.
8. **A interface:** os dois knobs (girar, clicar, segurar), a árvore completa do menu do OLED com uma figura de cada tela (simulada a partir do firmware), registros, instrumentos, volume, tipo de microfone e modos, bateria e desligamento, MIDI no computador.
9. **Problemas comuns** e o que fazer.
10. **Arquivos:** links para Gerbers, BOM/CPL, STL do case, firmware.

Conferir no navegador (cada língua, 375 px sem rolagem lateral, todas as imagens e links abrem). Prioridade: depois dos itens 1–3, porque as figuras de montagem usam os modelos 3D fiéis.

### 6. Firmware e case

Não mudam (os conectores trocados têm os mesmos pads). O firmware não precisa ser recompilado; o case só é conferido se o corpo do JST original for diferente do clone em altura ou profundidade (o design confere o túnel e o encaixe do plugue).

## Tarefas para o Code (R13V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Eletrônica | trocar os SH pelos originais JST e regenerar os pacotes de fábrica (item 1) |
| 2 | Eletrônica | conferência de modelo 3D, posição, giro e pino 1 de todas as peças, pré-visualização própria e renders (item 2) |
| 3 | Eletrônica | lista de conferência para o J nas folhas de cotação (item 3) |
| 4 | Eletrônica | `fab/COMPRA.md` com a configuração de compra de cada item (item 4) |
| 5 | Design | renders fotográficos do instrumento e da montagem, passo a passo, com os modelos fiéis (item 5, seções 1 e 6) |
| 6 | Programação e som | página `/etutti/studentV4/` com o manual completo, em pt e en, e as telas do menu (item 5) |
| — | Design | só se o corpo do JST original mudar algo que o case vê (item 6) |

**Perguntas que o Chat espera nos relatórios:**
- o custo novo da principal e da R8 com os JST originais;
- a tabela de modelos 3D, com toda peça sem modelo ou com ajuste ruim e o que foi feito;
- as quatro figuras de pré-visualização;
- `fab/COMPRA.md` pronto, com o total do protótipo;
- a página publicada e conferida, com o link;
- qualquer coisa que o Code precise do J (por exemplo, prints da pré-visualização da JLCPCB depois de subir os pacotes novos).

---

# Anexo — SPEC R12V4 (referência)

Data: 23 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #199 (relatórios da R11V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R12V4".

**Regras que continuam:**
- planta, corte e isométrico da base a cada mudança dela;
- nome da nota em cada tecla;
- só o instrumento de 32 teclas detalhado até a compra;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

## Decisões do J sobre a R11V4

1. **OLED Adafruit 326:** aprovado, compra à parte da JLCPCB, com o cabo Qwiic de estoque. J401 em SH de 4 vias, ordem Qwiic.
2. **Portão P da placa principal: APROVADO.** O posicionamento está fechado (`POSICIONAMENTO.md` R11V4, `pcb/img/portao_p_r11_instrumento.png`).
3. **Cotação das réguas:** o J cota os pacotes de `fab/regua/` (painel da R8 de 2 ou 4 réguas, réguas de reserva) e passa o resultado ao Chat. Isso não bloqueia o roteamento.

## Mudanças desde a R11V4

### 1. Roteamento da placa principal (Roteamento)

O agente **`roteamento`** começa agora, sobre o posicionamento aprovado. As regras do agente valem:
- **escolha do método:** o agente escolhe e justifica;
- **etapas:** idempotentes e retomáveis (`pcb/rota/estado.json`), um commit por etapa terminada no ramo de trabalho, etapas curtas, as longas em segundo plano;
- **nunca move peça:** se uma rede não fechar por falta de espaço, pede à eletrônica a menor mudança de posição, que volta ao J **só se mexer em conector, furo, contorno ou em algo que o case vê**;
- **par USB** como no estudo E4 (≤ 10 mm, In2 = GND, Full Speed);
- **aceitação:** DRC **0 erros e 0 avisos**, 0 ligações faltando, paridade 0, nenhuma trilha abaixo do mínimo, nenhuma ponta solta, nenhuma ilha de plano.

### 2. Arquivos de fábrica da placa principal (Eletrônica, depois do roteamento)

Com a placa roteada e aceita:
- **Gerbers e furação;**
- **BOM e CPL:**
  - formato JLCPCB;
  - montagem só no fundo;
  - posições e giros pelo `cpl_jlc.py`;
  - todos os códigos LCSC conferidos (encapsulamento contra footprint, estoque, Basic/Extended);
  - C310 marcado "não montar";
  - R305 = 0 Ω;
  - J401 SH-4.
- **Folha curta de cotação** no mesmo molde da das réguas (`fab/principal/LEIAME_COTACAO.md`): opções a marcar, quantidades mínimas, peças compradas à parte e montadas em casa (módulo MicroMod, OLED Adafruit 326, cabo Qwiic, cabos SH das réguas, bateria, alto-falante, teclas, parafusos e porcas), o que conferir na pré-visualização (pino 1 dos CIs, giro dos conectores SH, USB-C, jacks).
- **Nada é encomendado.** O J cota quando quiser.

### 3. Firmware da V4 (Programação e som; pode correr em paralelo)

Conferir o sketch próprio da V4 contra a placa roteada:
- pinos do `PINOS.md` contra as redes do J101;
- 4 × R8 sem OUT, 9 pulsos por varredura;
- OLED SSD1306 em 0x3D, imagem girada 180°;
- menu "Tipo mic" e bias por registro.

Compilar só a V4.

### 4. Case (Design; só se o roteamento pedir)

O case não muda nesta revisão. Se a eletrônica ou o roteamento pedirem uma mudança de algo que o case vê, o design a confere (fit check das 32 teclas) e a reporta antes de aplicar.

## Tarefas para o Code (R12V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Roteamento | rotear a placa principal (item 1) até a aceitação |
| 2 | Eletrônica | arquivos de fábrica e folha de cotação da principal (item 2) |
| 3 | Programação e som | firmware da V4 contra a placa roteada (item 3) |
| — | Design | só se o roteamento pedir (item 4) |

**Perguntas que o Chat espera nos relatórios:**
- a placa principal roteada e aceita (números do DRC);
- qualquer mudança de posição que o roteamento tenha pedido;
- o pacote de fábrica da principal pronto para cotar;
- o firmware conferido contra a placa.

---

# Anexo — SPEC R11V4 (referência)

Data: 22 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #197 (relatórios da R10V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R11V4".

**Regras que continuam:**
- planta, corte e isométrico da base a cada mudança dela;
- nome da nota em cada tecla;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

**Regra 1, ajustada:** só o instrumento de **32 teclas** é detalhado até orçamento e compra. **As quatro variantes de régua** (item 3) são detalhadas até o **pacote de cotação da JLCPCB**, para o J cotar e comparar sozinho.

## Decisões do J sobre a R10V4

- **Parede cheia entre degraus (riser):** aprovada. O custo é pequeno e garante a estabilidade do teclado.
- **Montagem da frente para trás** (o cabo ligado antes de descer a régua de trás): aprovada, procedimento oficial.
- **Painel da R8:** o alvo é **2 painéis com 2 réguas cada** (161,6 × 44 mm). O J vai conferir com os Gerbers (item 4) se a JLCPCB aceita.
- **Réguas de reserva:** de preferência nenhuma. Decide-se no orçamento, com os Gerbers.
- **Fixação do OLED e regra do autoatarraxante:** ver item 2 (a regra cai).

## Mudanças desde a R10V4

### 1. OLED: escolher o modelo e detalhar (Design + Eletrônica)

Fazer com o OLED o que foi feito com o alto-falante: **selecionar um modelo real** e detalhar o projeto em torno dele.
- **Modelo escolhido:**
  - fabricante e referência, com fornecedor (de preferência LCSC/JLCPCB ou outro com desenho mecânico publicado);
  - desenho mecânico: placa, vidro, área ativa, furos, conector;
  - controlador (SSD1306 / SH1106 ou outro) e tensão;
  - interface I²C compatível com J401 (JST SH, ordem Qwiic) ou o cabo necessário;
  - preço.
- **Detalhar com as medidas reais:**
  - área ativa centrada na janela, substituindo o deslocamento de 1,9 mm suposto;
  - apoios e fixação (item 2);
  - folgas com a tampa;
  - caminho do cabo até J401.
- Se nenhum modelo com desenho publicado couber na janela atual (24 × 13), propor a menor mudança da janela ou do modelo.
- Firmware: confirmar o controlador e a resolução no menu (PT/EN com acentos) e no tamanho de fonte.
- Entregar planta, corte e isométrico da interface com o OLED real.

### 2. Parafusos: a solução mais econômica que garante a estabilidade (Design)

**A exigência de "sem autoatarraxante" sai.** A regra passa a ser: **a solução mais econômica que garanta a estabilidade das placas** (réguas, OLED, placa principal, tampa), sabendo que as teclas são tocadas e geram forças repetidas.
- **Comparar pelo menos:**
  - parafuso formador de rosca para plástico (tipo PT/Delta PT ou equivalente) direto na bossa;
  - parafuso de máquina em inserto de latão (quente ou de pressão);
  - parafuso passante com porca.
  
  Para cada um: diâmetro, comprimento e bitola.
- **Critérios:**
  - **estabilidade:** sem folga nem afrouxamento sob a força repetida das teclas;
  - **vibração e impacto absorvidos sem rachar o PA12 (MJF):** bossa com diâmetro, furo-piloto, raios e nervuras pelas regras do fabricante do parafuso ou do inserto, sem cantos vivos que concentrem tensão; dizer se vale uma arruela, ou um apoio elástico onde ajudar;
  - **desmontagem:** quantas vezes a régua pode ser trocada sem perder a rosca (o conjunto é modular e montado em casa);
  - **custo:** peças, insertos, ferramentas e tempo de montagem.
- **Adotar a melhor opção** para cada uso (pode ser diferente na régua, no OLED e na tampa) e justificar.
- Os pontos de fixação podem ser revistos com o parafuso novo. Na R10V4 as fileiras 2 e 4 ficaram com 74 mm entre parafusos; se o parafuso novo liberar um par mais afastado, melhor.

### 3. Réguas: OUT só quando há extensão; quatro variantes para cotação (Eletrônica + Design)

Para baixar o custo e simplificar, **a régua só tem conector OUT quando precisa estender**. O instrumento de 32 teclas usa **4 réguas de 8 posições com IN e sem OUT**.

**As quatro variantes:**

| Variante | Posições | Conector OUT | Uso |
|---|---:|---|---|
| **R8** | 8 | não | **32 teclas** (4 ×); ponta direita de 64 e 80 |
| **R8E** | 8 | sim | primeira R8 de 48, 64 e 80 |
| **R4** | 4 | não | ponta direita de 48 e 80 |
| **R4E** | 4 | sim | reserva do conceito (fica como variante cotável) |

**A eletrônica decide**, com o menor custo e o menor número de desenhos, se cada comprimento é:
- **uma só placa** (OUT e o resistor da cascata como itens montados ou não na BOM); ou
- **placas distintas**: se a placa sem OUT ficar mais simples ou menor de forma que pague um desenho a mais.

Em todas: IN em u 5,9; mesma pinagem P6s; mesmas terminações; furos de fixação conforme o item 2.

**No case de 32 teclas:** sem cabeçalho OUT, sem plugue OUT e sem recorte de OUT. Rever o que isso libera (pontos de fixação, trilhos, parede).

### 4. Pacotes de cotação JLCPCB das quatro variantes (Eletrônica + Roteamento)

O J vai cotar e comparar as réguas sozinho. Para cada variante, entregar um **pacote completo e pronto para subir na JLCPCB**:
- Gerbers e furação (zip);
- BOM e CPL no formato da JLCPCB, com códigos LCSC conferidos e rotações pelo método de `cpl_jlc.py`;
- **painel**:
  - R8: 2 réguas por painel, 161,6 × 44 mm (alvo); se houver risco de recusa, também o de 4 réguas como alternativa;
  - R4: o de 5;
- uma folha curta (`fab/regua/LEIAME_COTACAO.md`) com espessura, camadas, acabamento, opções da JLCPCB a marcar, quantidades sugeridas e o que muda entre as variantes.

**Portão P das réguas: liberado nesta revisão.** Um pacote de cotação precisa de Gerbers completos.
- **Sequência:** a eletrônica fecha o esquema e o posicionamento das variantes (com OUT só onde há extensão e os furos do item 2) → o agente `roteamento` roteia as placas de régua.
- **Critério de aceitação:** DRC 0 erros e 0 avisos, 0 ligações faltando, paridade 0 → gera os pacotes.
- **A placa principal continua com o portão fechado.**

### 5. Isométrico detalhado da base (Design)

O J quer conferir **todas as linhas da base**, só ela, para entender os pontos de apoio:
- só a base (bandeja), sem tampa nem réguas;
- **arestas desenhadas** (linhas de contorno visíveis, de preferência também as ocultas tracejadas numa vista à parte);
- em **várias vistas**: isométrico da frente-esquerda e da trás-direita, mais uma vista de cima;
- os **pontos de apoio destacados e numerados**: trilhos, parede cheia, paredes de ponta, bossas dos parafusos, postes e túneis de cabo;
- a posição de cada tecla marcada sobre o trilho, **com o nome da nota**;
- uma legenda com o que cada número apoia (que régua, que tecla);
- resolução suficiente para ampliar (PNG grande ou PDF vetorial).

### 6. Portão P da placa principal

Continua **fechado**. Depois desta revisão, a planta de posicionamento da placa principal é reapresentada (com o OLED real e as fixações novas) para a aprovação do J.

## Tarefas para o Code (R11V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Design + Eletrônica | item 1: OLED real escolhido e detalhado |
| 2 | Design | item 2: parafusos (comparação, escolha por uso, bossas contra trincas, pontos de fixação revistos) |
| 3 | Eletrônica + Design | item 3: OUT só com extensão; as 4 variantes R8, R8E, R4, R4E; case de 32 sem OUT |
| 4 | Roteamento | item 4: rotear as placas de régua (portão P das réguas liberado) |
| 5 | Eletrônica | item 4: pacotes de cotação das 4 variantes + painéis + `LEIAME_COTACAO.md` |
| 6 | Design | item 5: isométricos detalhados da base, com arestas, apoios numerados e notas |
| — | Roteamento | placa principal: aguarda o portão P |

**Perguntas que o Chat espera nos relatórios:**
- o OLED escolhido;
- o parafuso escolhido para cada uso e por quê;
- uma placa ou duas por comprimento de régua;
- os 4 pacotes prontos para cotar;
- a planta da placa principal para o portão P.

---

# Anexo — SPEC R10V4 (referência)

Data: 22 nov 2026 · Autor: Claude Chat · Destino: Claude Code
**Substitui as tarefas da R9V4** (ainda não atendida): o que valia da R9V4 foi trazido para cá, ajustado. Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R10V4".

**Regras que continuam:**
- planta, corte e **isométrico da base** a cada mudança dela;
- nome da nota em cada tecla;
- só a Student V4;
- nada é comprado antes de o protótipo fechar.

**Regra 1, reescrita:** só a versão de **32 teclas** é detalhada (elétrica, case, firmware). Das outras, só a validação do conceito modular.

## Mudanças desde a R9V4

### 1. Duas réguas padrão: 4 e 8 posições (mudança principal)

O conjunto modular passa a ter **dois modelos de régua**, ambos com as mesmas terminações:
- **R4:** a régua de hoje, 4 posições.
- **R8:** nova, 8 posições, mesmo passo de 18,5 mm, ~148 mm de comprimento.

Nas duas:
- **cabeçalho SH de entrada à esquerda e de saída à direita**, pinagem P6s e mesma geometria de junção (o OUT fica à mesma distância da ponta direita que na R4);
- qualquer régua liga a qualquer outra pelo mesmo cabo.

| Teclas | Réguas por fileira (da placa para o agudo) | Réguas no total | Extensão (notas) | Comprimento do case |
|---:|---|---|---|---:|
| **32** (detalhado) | R8 | **4 × R8** | F#3–F#5 (25) | 244 mm |
| 48 | R8 + R4 | 4 × R8 + 4 × R4 | F#3–F#6 (37) | 318 mm |
| 64 | R8 + R8 | 8 × R8 | F#2–F#6 (49) | 392 mm |
| 80 | R8 + R8 + R4 | 8 × R8 + 4 × R4 | F#2–F#7 (61) | 466 mm |

**Regras da tabela:**
- A R4 fica sempre **na ponta direita, no agudo** (decisão do J).
- A extensão segue a ordem padrão das oitavas do mapa de notas (1º módulo no agudo, 2º no grave). A distribuição física das réguas não muda essa regra.
- Os comprimentos do case não mudam (mesmo passo e mesma regra).

**O que isso muda no modelo de 32 teclas:**
- **uma régua por fileira**: não há junção régua–régua, nem cabo entre réguas, nem rebaixo de junção. Ficam só os 4 cabos da placa à 1ª régua;
- o cabeçalho de saída continua na R8 (terminação modular), sem cabo no modelo de 32.

**Tarefas:**
1. **Eletrônica, régua R8:**
   - esquema: 8 TMAG5253 e **um** 74HC595 usando os 8 estágios (a R4 deixa 4 mortos);
   - posicionamento com IN/OUT e furos de fixação (item 3);
   - DRC sem trilhas 0/0, paridade 0;
   - painel da R8 e custo: o painel passa de 100 × 100 mm? Qual o arranjo mais barato na JLCPCB?
   - varredura: pulsos por fileira e tempo de passada para 32 teclas (8 estágios por régua), atualizando `pcb/PINOS.md` se mudar.
2. **R4:** continua como está (já desenhada), só como peça do conjunto modular. Não detalhar além do que existe; conferir só que as terminações da R4 e da R8 são idênticas (posição relativa do OUT, pinagem, altura).
3. **Custo do modelo de 32 teclas com 4 × R8** contra a solução de 8 × R4 da R8V4: peças, tipos Extended, painel, cabos (4 em vez de 8), juntas e tempo de montagem.
4. **Firmware** (sketch próprio da V4): 8 estágios por régua, mapa das 32 teclas, `V4_KEYS`. Validação curta de que 48/64/80 só mudam o número de réguas e estágios.
5. **Validação do conceito modular** (curta, sem figuras por tamanho): as combinações da tabela fecham com as mesmas terminações, cabos e regra de case.

### 2. Base do case: robustez (Design)

Com uma régua por fileira e sem junções, revisar a base priorizando a **robustez do conjunto**:
- **Montantes (trilhos) rígidos:** altura, espessura e continuidade conferidas contra a carga da tecla. Flexão da régua ≤ 0,05 mm a 3 N, e também do próprio montante.
- **Fechar os espaços onde couber, principalmente na frente das réguas:** a face frontal de cada degrau pode virar parede cheia, ligando trilhos e piso.
- **Sempre garantir:**
  - o caminho e o rebaixo dos 4 cabos da placa;
  - o acesso para ligar o plugue com a régua erguida e para montar e trocar a régua;
  - a folga das peças de baixo da régua (sensores, 595, cabeçalhos, pinos).
- O volume a mais entra no custo de impressão (MJF), informado.
- Entregar planta, cortes e **isométrico da base** (sem e com réguas, com as notas), mostrando o que foi fechado.

### 3. Fixação da régua: dois pontos por régua (Design + Eletrônica)

- **Dois pontos de fixação por régua**, para travar giro e levantamento. Na R8 de 148 mm há mais vãos entre carcaças: escolher os dois mais afastados que não conflitem com nada.
- **Parafusos permitidos:** M2, ou menores (M1,6 / M1,4), sempre com **rosca de máquina em inserto**. **Sem parafuso autoatarraxante.**
- Critérios:
  - zero conflito com plugues, cabos, cabeçalhos, pinos, sensores, 595 e postes;
  - bossa imprimível;
  - rigidez ≤ 0,05 mm.
- Definir os furos da R8 e da R4. Na R4, dois pontos se couberem; senão, explicar.
- Mostrar em planta, corte e isométrico.

### 4. OLED no corte da interface (Design; vinha da R9V4)

No `corte_interface_v4_r8.png`, o vidro do OLED não parece centrado na janela, e o módulo aparece sem apoio. Conferir:
- a área ativa do vidro contra a janela, pelo desenho do módulo;
- os 4 postes de apoio, num corte que passe por eles;
- as folgas.

Corrigir o modelo se estiver errado.

### 5. Microfone: eletreto e dinâmico, só pelo plugue de 3,5 mm (Eletrônica + Programação e som)

- **Suportar, na eletrônica e no firmware:**
  - microfones **de condensador com alimentação de plug-in** (eletreto, 2–5 V pelo plugue: headsets e lapelas comuns);
  - microfones **dinâmicos** comuns.
- **Conexão só pelo jack de 3,5 mm (J302).** Adaptadores (XLR etc.) são problema do usuário: o projeto não estuda nem fornece adaptador.
- **Fora do escopo:**
  - condensadores de estúdio com phantom de 48 V;
  - microfone de PC com bias no anel.
- **Sai do projeto:** o Sennheiser ME 3 como referência e o boost de 9–10 V, inclusive dos relatórios como plano B.
- **Estudar, de preferência sem mudar a placa:**
  1. **Bias:** ligado para eletreto (MIC_BIAS 3,0 V, 2 kΩ, R305 = 0 Ω) e desligado para dinâmico (registro do SGTL5000). Dizer se o bias por engano numa bobina de 150–600 Ω faz mal.
  2. **Detecção (MIC_DET):** regra que distingue nada / eletreto / dinâmico; uma bobina dá ~0,2–0,7 V com 2 kΩ, perto do limiar de curto (0,30 V). Se não der para distinguir com segurança, item de menu **"tipo de microfone"** (eletreto / dinâmico).
  3. **Ganho e ruído:**
     - casos de referência: dinâmico de 0,45 e de 1,7 mV/Pa (sensibilidades de headsets dinâmicos comuns) e eletreto comum;
     - voz cantada a 1–3 cm;
     - resultado em dBFS e relação sinal/ruído com o ganho máximo do SGTL5000;
     - se faltar ganho, a menor mudança e o custo.
  4. Os efeitos de voz continuam só com microfone detectado (ou declarado no menu) na entrada IN.

### 6. Portão P

Continua **fechado**. Depois desta revisão, a planta de posicionamento (principal, R8 e R4) é reapresentada para a aprovação do J. O roteamento só começa depois disso.

## Tarefas para o Code (R10V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Eletrônica | item 1: régua R8 (esquema, posicionamento, painel, custo, varredura); terminações iguais às da R4; custo 4 × R8 contra 8 × R4 |
| 2 | Design | item 2: base robusta para 4 × R8 (montantes, frentes fechadas, cabos e montagem garantidos); item 3 (dois pontos, sem autoatarraxante) com a eletrônica; item 4 (OLED); planta, cortes e isométricos |
| 3 | Eletrônica + Programação e som | item 5: microfones eletreto e dinâmico pelo 3,5 mm (bias, detecção, ganho, menu) |
| 4 | Programação e som | firmware da V4: 4 × R8, 8 estágios por régua, mapa das 32 teclas; validação curta dos outros tamanhos |
| — | Roteamento | aguarda o portão P |

**Perguntas que o Chat espera nos relatórios:**
- o custo e a montagem de 4 × R8 contra 8 × R4;
- a base revista, com o que foi fechado;
- os dois pontos de fixação;
- o OLED corrigido;
- o que eletreto e dinâmico pedem da placa e do firmware;
- a planta de posicionamento para o portão P.

---

# Anexo — SPEC R9V4 (referência; tarefas substituídas pela R10V4)

Data: 22 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #194 (relatórios da R8V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R9V4".

**Regras que continuam:**
- resumos visuais de planta e corte;
- nome da nota em cada tecla;
- só 32 teclas detalhadas, só a Student V4;
- nada é comprado antes de o protótipo fechar.

**Regra nova:** junto da planta e do corte, entregar **uma vista isométrica da base (bandeja)** sempre que a base mudar. O Chat fez a primeira a partir do modelo oficial: `spec_img/iso_base_r9.png` (script `spec_img/iso_base_r9.py`; painel A só a base, painel B com réguas, conectores, cabos, M2 e notas). O design pode melhorá-la (render real, cortes de detalhe da junção).

## Decisões do J sobre a R8V4

- Case de **102 mm**: aprovado.
- Riscos do cabo (comprimento útil, fios soltos ou fita) conferidos só na compra: aceito.
- **Portão P: ainda fechado.** Os itens 1 a 3 abaixo precisam fechar antes do roteamento.

## Mudanças desde a R8V4

### 1. Segundo ponto de fixação da régua (Design + Eletrônica)

O J quer **dois pontos de fixação por régua**, para garantir que ela não gire nem levante. Estudar:
1. **Outras posições:** todos os vãos entre carcaças ao longo da régua (não só u 18,5 / 37 / 55,5), nas duas faixas, frente (v +5,2) e trás, e em outras posições de v. Também as pontas da régua, na junção. A posição do furo na régua pode mudar (a eletrônica atualiza a régua).
2. **Parafusos menores:**
   - M1,6 (cabeça ~Ø3,0) ou M1,4 com inserto;
   - parafuso autoatarraxante para plástico (por exemplo PT/plastite ~Ø1,7–2,0) direto na bossa, sem inserto;
   - ver se cabem onde o M2 (cabeça Ø3,8, bossa Ø6) não cabe.
3. **Critérios:**
   - dois pontos por régua, separados o suficiente para travar a rotação;
   - zero conflito com plugues, cabos (45,8 e 50,8), cabeçalhos, pinos, sensores, 595, postes e rebaixos;
   - bossa imprimível (MJF) e inserto ou rosca confiável;
   - rigidez ≤ 0,05 mm a 3 N.
4. **Entregar:**
   - as opções com planta, corte e isométrico da base (com as notas nas teclas);
   - a recomendada;
   - o que muda na régua (furos) e no case.
5. Se nenhuma opção der dois pontos em alguma régua, explicar o porquê e quantificar com o pior caso de carga: tecla apertada na ponta e retorno da mola. Isso mostra se o ponto único, mais o sanduíche régua + grade + teclas + deck, segura a régua contra giro e levantamento.

### 2. OLED desalinhado no corte da interface (Design)

No `corte_interface_v4_r8.png` (corte A-A, x = 37):
- o vidro do OLED (y ~12–28) não parece centrado na janela da tampa (y ~15,5–28,5);
- o módulo parece **solto**, sem apoio visível, ao contrário do alto-falante, que aparece encaixado na caixa.

Conferir:
- **Desenho real do módulo:** a área ativa do vidro centrada na janela. Se o deslocamento de 1,9 mm de `oled_centre()` estiver certo, mostrar a cota da área ativa contra a janela.
- **Apoios no corte:** os 4 postes `oled_posts()` e o aperto do módulo devem aparecer no corte (ou num corte extra que passe por eles).
- **Folgas:** vidro–janela e módulo–teto.

Corrigir o modelo se estiver errado e refazer o corte.

### 3. Microfone: microfones dinâmicos de headset (Eletrônica + Programação e som)

**O Sennheiser ME 3 sai como referência, e o boost de 9–10 V é abandonado** (sai também do plano B).

Novas referências, ligadas por fio:
- **Audio-Technica PRO 8HEx:** dinâmico hipercardioide, 1,7 mV/Pa, 600 Ω, XLR macho.
- **Shure WH20XLR:** dinâmico cardioide, −67 dBV/Pa (0,45 mV/Pa), 150 Ω nominal (200 Ω real), XLR macho.

São **dinâmicos** (bobina móvel): não pedem alimentação, e o bias DC é desnecessário. O headset de eletreto comum continua suportado.

Estudar, de preferência **sem mudar a placa**:
1. **Ligação:** adaptador passivo XLR fêmea → plugue de 3,5 mm desbalanceado (pino 2 → ponta; pinos 1 e 3 → luva). Conferir que funciona no J302 como está e se o anel NC atrapalha.
2. **Bias:**
   - com o microfone dinâmico, o MIC_BIAS deve ficar **desligado** (o SGTL5000 desliga por registro, BIAS_RESISTOR = 0);
   - dizer se o bias de 3 V com 2 kΩ através da bobina (~1 mA) faz mal ou só desloca o diafragma, para decidir se basta desligar por software.
3. **Detecção (MIC_DET):**
   - com 2 kΩ, uma bobina de 150–600 Ω dá ~0,2–0,7 V, que cai perto do limiar de "curto" (0,30 V) e se mistura com o eletreto de corrente alta;
   - propor a regra que distingue **nada / linha / eletreto / dinâmico**, ou dizer que não dá;
   - nesse caso, um item de menu "tipo de microfone" (eletreto / dinâmico) que desliga o bias e libera os efeitos de voz;
   - os efeitos de voz continuam só com microfone na entrada IN.
4. **Ganho e ruído:**
   - SGTL5000 com +40 dB e o ADC;
   - voz cantada a 1–3 cm do headset (o WH20 especifica a resposta a 8 mm);
   - dizer o nível em dBFS e a relação sinal/ruído para 0,45 e 1,7 mV/Pa;
   - se faltar ganho, qual a menor mudança: um pré-amplificador simples na placa, o custo e os tipos Extended.
5. **Recomendação:** o que a placa e o firmware precisam para eletreto e dinâmico, com o mínimo de peças.

### 4. Portão P

Continua **fechado** até o J aprovar os itens 1 a 3. Então a planta é reapresentada (se mudar) para a aprovação final e o roteamento.

## Tarefas para o Code (R9V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Design + Eletrônica | item 1: segundo ponto de fixação (posições, parafusos menores, opções, recomendação, isométrico) |
| 2 | Design | item 2: OLED (alinhamento, apoios, corte refeito) |
| 3 | Eletrônica + Programação e som | item 3: microfones dinâmicos (adaptador, bias, detecção, ganho, recomendação); retirar ME 3 e boost dos relatórios |
| — | Roteamento | aguarda o portão P |

**Perguntas que o Chat espera nos relatórios:**
- a fixação de dois pontos recomendada (ou a prova de que um basta);
- o OLED corrigido;
- o que é preciso para os microfones dinâmicos.

---

# Anexo — SPEC R8V4 (referência)

Data: 22 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #192 (relatórios da R7V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R8V4".

**Regras que continuam:**
- resumos visuais de **planta e corte**;
- **nome da nota em cada tecla**;
- as regras gerais da R7V4: só 32 teclas detalhadas e só a Student V4.

**Regra nova (J): nada é comprado até o protótipo inteiro estar fechado.** Nem amostras de cabo. As dúvidas que só a peça real responde ficam como risco no relatório. O projeto deve ser robusto a elas (item 1.3).

## Mudanças desde a R7V4

### 1. Ligação H aprovada

1. **Cabeçalho OUT da régua em u 47,5** (recomendação do Chat, aprovada).
   - O C3 sai da pegada do OUT (eletrônica).
   - O IN continua em u 5,9.
   - Os dois são o SM06B-SRSS-TB (ou o clone C56123098), no fundo, com a boca para trás (−y).
2. **Pinagem P6s:** +3V3, GND, OUT, GND, CLK, DADO.
   - Vale na entrada e na saída da régua e em J601–J604.
   - Os resistores em série de CLK/DADO passam a 330 Ω: R605/R606 na principal e o do QH' na régua.
   - O cabo previsto é o JST **A06SR06SR30K51B** (50,8 mm, reto).
3. **Robustez ao cabo não medido** (consequência da regra de compra):
   - Ainda não se sabe se o comprimento útil é 45,8 ou 50,8 mm, nem se os fios são soltos ou em fita colada.
   - **Comprimento:** o desenho deve fechar nas quatro fileiras com **45,8 e com 50,8 mm**, com folga ≥ 0,5 mm.
     - Com o OUT em 47,5 isso falha na fileira 4 para 50,8 (−1,2 mm).
     - Resolver pela menor mudança, nesta ordem:
       1. aumentar a profundidade do case atrás da fileira 4 (a largura passa de 100 mm para o necessário, ~102 mm; dizer o custo);
       2. só se isso for pior, outra posição do OUT.
   - **Fio solto x fita colada:** dizer o que acontece com uma fita colada e se algum ajuste barato do rebaixo a acomoda. Se não houver, fica registrado como risco a conferir na compra.
4. **Mudanças no case aprovadas** (as quatro da R7V4):
   - postes de parede em x 102,5 / 176,6 / 234;
   - os 2 postes internos novos;
   - os pares de M2 por fileira;
   - os rebaixos por junção.
   
   Saem o berço e tudo o que era da G. **Conferir a rigidez da régua** com os M2 mais próximos entre si (21–50 mm): flexão ≤ 0,05 mm a 3 N, como antes.
5. **Montagem:** a sequência da R7V4 (da fileira da frente para a de trás; régua erguida → plugue → desce → M2) entra no relatório como procedimento oficial. Inclui a pinça fina para trocar uma régua.

### 2. Microfone

- **R305 = 0 Ω na BOM** (aprovado): 2 kΩ de bias no total, mais tensão para microfones que pedem mais.
- O ME 3 era só uma referência; o J não tem um. **Sem teste de bancada e sem o boost de 9–10 V** nesta fase.
- O plano B do boost fica registrado no relatório para uma revisão futura.

### 3. Aplicar tudo e apresentar o portão P

Com os itens 1 e 2 decididos, esta revisão **aplica as mudanças** e **apresenta o portão P**:
- **Régua:** esquema e posicionamento com OUT em u 47,5, C3 movido, P6s e 330 Ω. DRC sem trilhas: 0 erros, 0 avisos; paridade 0.
- **Placa principal:**
  - J601–J604 na pinagem P6s;
  - R605/R606 de 330 Ω;
  - R305 de 0 Ω;
  - DRC sem trilhas: 0 erros, paridade 0;
  - posicionamento final.
- **Case:** `LINK = "H"` no modelo oficial (`case_r4.py`). Fit check só das 32 teclas: cabos (45,8 e 50,8), plugues, rebaixos, postes, M2 e réguas. Mais a profundidade do item 1.3.
- **Firmware** (sketch próprio da V4): a pinagem P6s não muda pinos do Teensy; conferir que nada depende da ordem antiga do conector.
- **Portão P:** entregar ao J a **planta final de posicionamento da placa principal e da régua**, com blocos, conectores, furos e as figuras de sempre, para aprovação. O **roteamento só começa depois de o J aprovar** essa planta.

## Tarefas para o Code (R8V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Design | item 1.3 (comprimento 45,8/50,8 e fita colada) e 1.4 (postes, M2, rebaixos, rigidez); `LINK = "H"`; fit check das 32 teclas; montagem oficial (1.5) |
| 2 | Eletrônica | régua (OUT u 47,5, C3, P6s, 330 Ω), principal (J601–J604 P6s, R605/R606 330 Ω, R305 0 Ω), DRC e paridade; planta do portão P |
| 3 | Programação e som | conferir o firmware da V4 contra a P6s; compilar só a V4 |
| — | Roteamento | aguarda a aprovação do portão P pelo J |

**Perguntas que o Chat espera nos relatórios:**
- a profundidade (ou posição) que fecha com os dois comprimentos de cabo, e quanto custa;
- a rigidez com os novos M2;
- a planta do portão P pronta para o J aprovar.

---

# Anexo — SPEC R7V4 (referência)

Data: 22 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #189 (relatórios da R6V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R7V4".

**Regras que continuam:** resumos visuais de **planta e corte** para cada decisão; **nome da nota em cada tecla** em toda figura do teclado.

**Regras gerais do projeto (novas, 22 nov, decisão do J; valem para esta e para todas as revisões seguintes):**
1. **Escopo do teclado: só 32 teclas.**
   - Todo detalhamento (modelo, fit check, figuras, custo, montagem, firmware) é feito só para a versão de **32 teclas**.
   - As versões de 48, 64 e 80 teclas **não são detalhadas**. Delas só se faz a **validação do conceito modular**, numa seção curta:
     - a régua universal se repete;
     - a cadeia de ligação e a varredura crescem sem mudar a placa principal;
     - o case cresce pela mesma regra de comprimento.
   - Não fazer figuras, tabelas de custo nem fit check por tamanho.
2. **Escopo de versões: só a Student V4.**
   - No detalhamento das 32 teclas e no firmware, não considerar nenhuma versão anterior (Student V01, V2, V3, Lite, Viaggio, Pocket) nem o eTuttino, eTutti ou eTuttiChorus.
   - A única versão em que se trabalha, que se compila e que se verifica é a **Student V4 modular**.
   - Os arquivos das outras versões ficam no repositório como estão, congelados. Não são atualizados, nem mantidos compilando, nem conferidos.
   - Podem ser lidos como referência, mas nada do relatório depende deles.

**Ordem desta revisão (pedido do J):** o item 1 é um **estudo dedicado da ligação**, feito **antes de qualquer outro passo**. Nenhuma mudança de esquema, posicionamento ou case entra antes de o J aprovar a ligação. O item 3 (microfone) é só estudo de mesa, sem mudar a placa.

## Mudanças desde a R6V4

### 1. Ligação das réguas: estudo dedicado da opção "H" (cabo SH de estoque + rebaixo na base)

**Modelo de fornecimento (novo, decisão do J):**
- case, réguas e placa de interface são fornecidos **em separado**;
- as réguas vêm como peças de um conjunto modular: a fábrica **nunca** monta réguas no case nem as liga;
- todo o encaixe e a ligação são feitos **em casa, pelo usuário**.

**Restrições:**
- nenhum componente a mais e nenhuma fixação a mais na base do case: **sem ponte e sem berço** (a opção G da R6V4 fica suspensa);
- os comprimentos de cabo podem variar.

**O conceito H, descrito pelo J:**
1. A placa principal tem **4 conectores SH** (J601–J604, como hoje), um por fileira.
2. Cada régua tem um **SH de entrada** embaixo, perto da ponta esquerda, e um **SH de saída** embaixo, na ponta direita (o mesmo cabeçalho SM06B-SRSS, ou o clone C56123098).
   - Nota de nomenclatura: no sistema SH o lado da placa é sempre o cabeçalho com pinos ("macho"); as duas pontas do cabo são o plugue ("fêmea").
3. A base do case tem um **rebaixo** sob a zona de conectores de cada régua. Por ele:
   - o cabo passa antes de a régua ser posta;
   - o cabo é ligado à régua;
   - a régua desce e é parafusada.
4. Entre réguas de uma fileira, um **cabo SH de estoque de ~50 mm** liga a saída de uma régua à entrada da seguinte.
   - Existe jumper JST original de 6 vias com 50,8 mm: A06SR06SR30K51B, em estoque na DigiKey; o mesmo jumper existe também em 4", 6" e 12".
5. Da placa à 1ª régua: cabo SH de estoque (50 ou 100 mm). O rebaixo guarda a sobra.

**O que o estudo precisa responder (Design + Eletrônica), com desenhos reais:**
1. **Viabilidade geral:**
   - o cabo de 50 mm (e o de 100 mm da placa) cabe no rebaixo, com a régua no lugar, sem pressionar sensores, pinos de tecla ou o 595?
   - qual profundidade e largura de rebaixo isso pede?
   - o que muda no piso (espessura, rigidez sob a régua, trilhos e bossas M2), no volume e no custo de impressão?
2. **Posição e orientação dos cabeçalhos na régua:**
   - boca para trás (−y), como na R4V4, para os lados (±x) ou outra;
   - a posição deve deixar o plugue entrar com a régua **erguida** acima do degrau (o cabo tem de ser longo o bastante para isso) e depois descer sem dobrar o cabo contra a régua;
   - conferir com o desenho do fabricante a altura do cabeçalho e o raio de dobra mínimo do cabo de 28–32 AWG.
3. **Posicionamento geral das réguas sobre o case** (pedido do J para decidir):
   - planta de **todas** as réguas da versão de 32 teclas com conectores, rebaixos e caminho de cada cabo (dos módulos, só a validação do conceito: regra geral 1);
   - cortes do rebaixo em cada fileira, porque os degraus mudam a altura: a fileira 1 tem o bolso mais raso.
4. **Ordem dos pinos dos cabos:**
   - alguns cabos SH prontos são "invertidos" (com o cabo plano, os dois plugues ficam do mesmo lado, e o pino 1 de uma ponta liga ao pino 6 da outra);
   - a pinagem da entrada e da saída da régua (e de J601–J604) deve funcionar com o cabo comprado, de preferência com os dois tipos de cabo; se não der, dizer qual comprar;
   - um cabo ao contrário nunca pode inverter a alimentação.
5. **Montagem em casa:**
   - passos com figuras, do cabo solto à régua parafusada;
   - como trocar uma régua;
   - como acrescentar um módulo.
6. **Custo:**
   - custo da versão de 32 teclas contra a G e a D: peças da régua, cabos de estoque, tipos Extended, impressão do case (sem tabela por tamanho: regra geral 1);
   - o SH continua sendo o único conector das réguas.
7. **Se a H não fechar:** dizer exatamente o que impede e qual a menor mudança que a faria funcionar. Exemplos de ajuste: outra posição do cabeçalho, outro comprimento de cabo, rebaixo mais fundo ou um degrau maior na fileira 1.

### 2. Case: aprovado

- 244 mm.
- Chanfro de 2 × 2 em cima e 1 × 1 embaixo.
- Borda direita de 5,8 mm.

**Tamanho e custo (orientação do J):** não há limite fixo de tamanho. Considerar os limites que mudam o custo: a mesa de impressão de 250 mm, as faixas de preço do MJF por volume e o painel de 100 × 100 mm da JLCPCB. Se o desenho passar um pouco de um desses limites, propor a redução que o faça caber.

### 3. Microfone: eletreto comum **e** Sennheiser ME 3 (estudo de mesa)

O J quer que a entrada IN aceite, além de uma cápsula de eletreto comum, um microfone profissional como o **Sennheiser ME 3** (art. 508928).

Dados do fabricante:
- condensador pré-polarizado, cardioide;
- sensibilidade de 1,6 mV/Pa;
- conector de 3,5 mm;
- tensão de alimentação de 10 V.

**Tarefa (Eletrônica, só estudo; a placa não muda nesta revisão):**
1. **Pinagem do plugue do ME 3** (quick guide e folha de especificação da Sennheiser): o sinal e a alimentação vêm na ponta? O anel é usado? Funciona no J302 como está (cápsula na ponta, anel NC)?
2. **Alimentação:**
   - o MIC_BIAS do SGTL5000 chega a 3,0 V, contra os 10 V especificados;
   - o ME 3 funciona com 3 V? Com que perda de nível máximo e de ruído?
   - se precisar de mais, qual a menor solução (fonte de bias de 5–10 V com resistor, ligada só com microfone detectado) e quanto custa em peças, tipos Extended e espaço.
3. **Ganho:** 1,6 mV/Pa fica ~14 dB abaixo de uma cápsula comum de −42 dBV/Pa. O ganho do SGTL5000 (até 40 dB + ADC) basta para voz cantada a 2–3 cm com boa relação sinal/ruído?
4. **Detecção (MIC_DET):** com a corrente do ME 3, a tensão cai dentro da faixa "microfone" dos limiares da R6V4?
5. **Recomendação:** o que a placa precisa ter para servir aos dois microfones, ou por que não dá.

O padrão continua sendo o headset de eletreto comum com a cápsula na ponta. Microfone de PC com bias no anel continua fora (decisão do J).

### 4. Adiados para depois do protótipo

- **Modos de voz:** os detalhes do harmonizador (mistura seca/ajudada, tecla sozinha no modo intervalo, padrão de vozes) ficam como estão até haver instrumento para testar. O firmware atual já basta.
- **Espanhol na tela:** depois do protótipo.

### 5. Portão P

Continua **fechado** até o J escolher a ligação (item 1).

## Tarefas para o Code (R7V4)

| Ordem | Área | Tarefa |
|---|---|---|
| 1 | Design + Eletrônica | **estudo da ligação H** (item 1): viabilidade, posicionamento geral das réguas, rebaixos, cabos, pinagem, montagem, custo; planta e corte com as notas; nenhuma mudança de projeto antes da aprovação do J |
| 2 | Eletrônica | estudo de mesa do microfone ME 3 + eletreto (item 3), sem mudar a placa |
| 3 | Programação e som + integração | aplicar a regra geral 2 ao firmware: a V4 passa a ter **sketch próprio** (por exemplo `etutti/firmware/student_v4/`, só com o caminho da V4, 32 teclas); o sketch compartilhado `etutti_synth/` fica congelado como está; compila-se e confere-se só a V4. Atualizar `CLAUDE.md` e os arquivos dos agentes (`.claude/agents/`) com as duas regras gerais |
| — | Roteamento | aguarda o portão P |

**Perguntas que o Chat espera nos relatórios:**
- a H é possível? Se sim, com qual rebaixo, qual cabo e qual custo; se não, o que impede e qual a menor mudança que a faria funcionar;
- o ME 3 funciona como está ou precisa de quê.

---

# Anexo — SPEC R6V4 (referência)

Data: 21 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #187 (relatórios da R5V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R6V4".

**Regras que continuam:**
- resumos visuais de **planta e corte** para cada decisão;
- **nome da nota em cada tecla** em toda figura do teclado.

## Mudanças desde a R5V4

### 1. Ligação das réguas: estudo de conectores fixos (mudança principal; a D fica suspensa)

O J prefere não soldar a cadeia de réguas. A arquitetura que ele quer:
- um **conector na placa principal** liga a um **conector fêmea na 1ª régua** de cada fileira;
- cada régua tem uma **entrada fêmea à esquerda** e uma **saída macho à direita**;
- as réguas de uma fileira se ligam em série, de encaixe, sem solda nem cabo.

Referência dada pelo J: Sullins **PPPC051LGBN-RC** (fêmea de 5 vias, passo 2,54, em ângulo, PTH). Esse tamanho é só a ideia: a peça deve ser SMD no fundo, montada pela JLCPCB, e caber na bolsa.

**Pré-análise do Chat** (`spec_img/juncao_r6.png`, script `juncao_r6.py`; medidas dos conectores **estimadas**):
- Na junção, a faixa livre no eixo da régua tem só **6,6 mm** entre o pino da última tecla de A e o da primeira de B.
- **E1, a ideia literal** (macho em ângulo no fim de A entrando numa fêmea em ângulo no início de B, pinos ao longo de x):
  - a fileira de contatos fica ao longo de y, atravessando o eixo;
  - uma fêmea de 1,27 com pads (~5,6 mm de fundo) bate no pino da 1ª tecla de B;
  - só serve se existir uma fêmea com **≤ 3,3 mm de fundo, pads incluídos**, ou montada na borda;
  - a montagem pede deslizar cada régua ~3 mm em x antes de parafusar: a fileira é montada da direita para a esquerda.
- **E2, alternativa:**
  - fêmea igual nas duas pontas de cada régua, de boca para baixo, com a fileira de contatos **ao longo de x** na faixa da frente (y +1,0 a +4,1), longe dos pinos e sensores;
  - uma **ponte** (PCB pequena com dois machos 1×5) liga as duas réguas por baixo;
  - a régua desce na vertical sobre a ponte ao ser posta nos trilhos;
  - altura estimada de ~5,2 mm na bolsa de 6,9 mm da fileira 1;
  - as pontes podem ir no mesmo painel das réguas.
  
  Não é o "macho à direita" do J, mas atende ao objetivo dele: sem solda, réguas todas iguais.

**Tarefa (Design + Eletrônica):** estudar com desenhos reais de fabricante e fechar uma recomendação.
1. **Junção régua–régua:**
   - **E1:** procurar fêmeas em ângulo de perfil curto, inclusive montadas na borda, nos passos de 1,27, 1,0 e 2,0 mm.
   - **E2:** a ponte, com ponte macho ou ponte fêmea com machos nas réguas.
   - Qualquer outra família que caiba: placa-a-placa coplanar, card-edge, contatos de mola.
   - Para cada opção: peças LCSC/JLCPCB (classe Basic/Extended, estoque, preço), altura na bolsa da fileira 1 (6,9 mm) com folga, conflito com pinos, sensores, 595, bossas M2 e trilhos, modo de montar e desmontar, e retenção (o encaixe não pode soltar com a vibração do tocar).
2. **Placa principal → 1ª régua:**
   - Dado do modelo: o topo da placa (z 0) é o plano da fileira 1. As fileiras 2 e 4 começam 2,45 mm depois da borda da placa, mas 2 e 7 mm mais altas; as fileiras 1 e 3 começam 11,7 mm depois.
   - Um encaixe rígido direto parece impossível. Confirmar, e propor o cabo com conector nas duas pontas que chega à fêmea de entrada da régua.
   - Caminhos possíveis: cabo pronto do mesmo sistema, cabo de fita/IDC fácil de crimpar em casa, o SH de 100 mm cortado ao meio (solda só na placa), ou adaptador.
3. **Custo:** tabela 32/48/64/80 contra a D: peças, tipos Extended a mais ou a menos, pontes e montagem.
   - Se o SH sair das réguas, sai também um tipo Extended (US$ 3,09).
   - Orientação do J: aceitável se o custo **não for muito mais alto**. Referência do Chat para 32 teclas: até ~US$ 15 acima da D. O J decide.
4. **Entregas:**
   - planta e corte de cada opção na junção (com as notas das teclas);
   - fit check 32/48/64/80;
   - recomendação.
   
   A D continua como plano de reserva.

### 2. J2 da régua

A economia de tirar o J2 é pequena: ~US$ 0,07 da peça mais as juntas, ≈ **US$ 0,08 por régua**, US$ 0,8 nas 10 réguas montadas. O tipo Extended continua, porque o J1 usa a mesma peça. A decisão sobre o J2 **segue o item 1**: se a cadeia passar para conectores fixos, os dois SH podem sair da régua.

### 3. Case: borda direita +4 mm e chanfro

- Aprovado **+4 mm** de deck plano depois do último botão. O case de 32 teclas fica com **244 mm**, e os de 48/64/80 com 318/392/466 mm. Conferir se a tampa ainda cabe na mesa FDM de 250 mm.
- Aprovado o chanfro externo **2 × 2 mm em cima e 1 × 1 mm embaixo**.

### 4. Arquivos de 32 teclas

- `geometria.py` e `pcb/grade_fab.py` passam para 32 teclas (eletrônica).
- A grade-régua sai do contorno de 32 teclas.

### 5. Voz e microfone

- **Padrão: microfone de headset**, a ~2–3 cm da boca. O limiar do expansor e os ganhos de fábrica são calibrados para isso.
- Os **efeitos de voz** (expansor, harmonizador e supressor de microfonia) **só se ativam com um microfone ligado na entrada IN** (J302):
  - sem microfone, os itens de voz somem do menu (ou aparecem desativados);
  - a eletrônica confirma como detectar o plugue (o contato de chave da ponta do PJ-327A, pino 3, chega a um pino do Teensy?) e diz se falta algo na placa;
  - um plugue de linha (sem microfone) não deve ligar os efeitos de voz; se o hardware não conseguir distinguir, dizer.
- Com microfone: supressor de microfonia desligado por padrão; alto-falante nunca salvo ligado (como a R5V4 propôs).

### 6. Harmonizador "seguir a tecla"

- Três modos:
  - **exato:** como está;
  - **ajuda:** puxa a voz só em parte para a nota tocada, com intensidade ajustável no menu;
  - **intervalo:** mantém a distância entre as notas, com a voz natural.
- **Até 4 vozes** (3 ou 4, escolha no menu). Conferir memória, CPU e latência com 4 vozes junto com o acordeão de 4 registros.

### 7. Tela

- Idiomas: **português e inglês**, com minúsculas e acentos (fonte com acentos, ~+2 KB). A escolha fica no menu.
- Os textos ficam numa tabela fácil de estender para outros idiomas depois.

### 8. Respostas da R5V4 aprovadas sem mudança

- Clique curto do seletor age ao soltar.
- Alto-falante nunca salvo ligado.
- Passada de 80 teclas.
- CCs e mapa de notas do usuário na fase da página.
- Página da V4 com simulação clicável da interface: continua para depois do hardware.

### 9. Portão P

Continua **fechado**. A placa principal depende da ligação escolhida no item 1 (J601–J604 ou pads), e a régua também. O J libera o roteamento numa próxima revisão, depois de escolher a ligação.

## Tarefas para o Code (R6V4)

| Área | Tarefa |
|---|---|
| Design | item 1 (geometria das opções na junção, planta e corte, fit check 32–80); item 3 (244 mm, chanfro); figura do teclado com notas em toda planta |
| Eletrônica | item 1 (peças, classe, preço, custo 32–80, cabo placa → régua); item 2; item 4; item 5 (detecção do microfone em J302) |
| Programação e som | item 5 (efeitos só com microfone, padrão headset); item 6 (3 modos, até 4 vozes, medir CPU e memória); item 7 (PT/EN com acentos) |
| Roteamento | aguarda o portão P |

**Perguntas que o Chat espera nos relatórios:** a recomendação de ligação (E1, E2 ou outra) com custo e figura; como detectar o microfone; CPU e memória com 4 vozes.

---

# Anexo — SPEC R5V4 (referência)

Data: 21 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #185 (relatórios da R4V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R5V4".

**Regra nova para todos os relatórios (pedido do J):** sempre que possível, entregar **resumos visuais de planta e de corte** de cada decisão. Toda figura do teclado, de agora em diante, mostra **o nome da nota em cada tecla** (C e F destacados).

## Mudanças desde a R4V4

### 1. Teclado de 32 teclas: réguas sempre cheias (mudança principal)

Para seguir o conceito modular, **toda posição de toda régua tem tecla**. A V4 passa de 28 para **32 teclas** (8 réguas × 4). Figura do Chat: `spec_img/teclado_32.png` (script `spec_img/teclado32.py`).

| Fileira | Antes (28) | Agora (32) | Início da 1ª régua (x) |
|---|---|---|---|
| 1 (frente) | A3–D#5 (7) | **A3–F#5** (8) | 89,2 (igual) |
| 2 | G3–E5 (8) | **G3–E5** (8, igual) | 79,95 (igual) |
| 3 | G#3–D5 (7) | **G#3–F5** (8) | 89,2 (igual) |
| 4 (trás) | A3–C5 (6) | **F#3–D#5** (8) | **79,95**: um botão para a esquerda, alinhada com a fileira 2 |

- Teclas novas: F#5 (fil. 1), F5 (fil. 3), F#3 e D#5 (fil. 4).
- A fileira 4 continua nas colunas da fileira 2, um semitom abaixo dela em cada coluna (F#3 sob G3).
- **Módulos:** cada módulo continua acrescentando 1 régua por fileira (+16 teclas). As versões passam a ser **32, 48, 64 e 80** (no lugar de 28/44/60/76). A ordem padrão das oitavas do mapa de notas não muda (1º módulo agudo, 2º grave…).
- O que refazer:
  - posições das réguas e furos da fileira 4;
  - deck e furos dos botões (32);
  - postes (que não podem cair numa junção de réguas nem numa tecla);
  - entalhes, cabos e trilhos;
  - comprimento do case: a ponta direita vai até x ≈ 237,6. O design **reduz o comprimento** se a regra de margem permitir e informa o novo total;
  - fit check em 32 / 48 / 64 / 80;
  - custo (+4 teclas e +4 botões);
  - firmware: `V4_KEYS` 32 / 48 / 64 / 80, mapa de notas, varredura e tempos;
  - a cadeia de registradores, que agora usa as 4 posições de todas as réguas.
- A placa principal não muda por isso. O cabo da fileira 4 fica tão curto quanto o da fileira 2.

### 2. Aprovações do J

| Tema | Decisão |
|---|---|
| Quinas | **Canto vivo R6 aprovado**, só com um **chanfro na aresta externa** para suavizar a pegada. O design propõe a medida do chanfro e mostra em corte. |
| Alto-falante | **Conceito de "alto-falante de estudo" aprovado.** O firmware aplica equalização na saída do alto-falante (corte abaixo de ~300 Hz e redução do pico perto de 1 kHz, ajustáveis). O som completo é para fone e AUX. |
| Menu | **Confirmado** como no `FIRMWARE.md` §4. **Para a página da V4 (fase futura):** incluir uma simulação web da interface (tela OLED + 2 knobs clicáveis com o mouse) que reproduza o menu e as entradas do usuário. |
| Portão P | A placa principal está aprovada **em princípio**. Os conectores das fileiras (J601–J604) dependem do item 3. O roteamento da placa principal **começa depois** que o J escolher a ligação das réguas (R6V4). |

### 3. Ligação das réguas: comprar de preferência, soldar é possível

**Quantos condutores:** **5 por ligação**: +3V3, GND, OUT da fileira, CLK e DATA (SER na entrada e QH' na saída). O SH-6 tem um 6º pino reservado (OUT_B), sem uso hoje.

**Quantas ligações (32 teclas):**
- **4 cabos placa → 1ª régua**, um por fileira, ~25 mm, com desnível de 0–7 mm;
- **4 elos régua → régua dentro da fileira**. As duas réguas da mesma fileira ficam **na mesma altura e em linha**, a 0,4 mm uma da outra.

Cada módulo de +16 acrescenta mais 4 elos.

O Code estuda e compara, **com planta e corte de cada opção**:
- **(A) Comprar pronto:**
  - cabos JST SH de 6 vias com plugue nas duas pontas;
  - achar fornecedor e os comprimentos mínimos realmente vendidos (15 / 25 mm ou o mais curto que exista);
  - se o mais curto for maior, dizer se a geometria aceita a sobra (alça sob a régua) ou o que muda.
- **(B) Elo soldado entre réguas da mesma fileira:** como estão em linha e na mesma altura, a junção pode ser uma ponte curta: 5 ou 6 pads em cada ponta da régua (no fundo), ligados por:
  - fios finos (silicone 28–30 AWG);
  - um pedaço de barra de pinos de 1,27 mm em ângulo;
  - ou um "jumper" de cabo plano (FFC/FPC) soldado.

  Sem conector e sem plugue. Avaliar o espaço sob a régua, a resistência mecânica e a troca de uma régua.
- **(C) FFC/FPC com conector** (passo 0,5 ou 1,0 mm), em qualquer comprimento: conector, altura, disponibilidade Basic/Extended.
- **(D) Misto:** cabo comprado só da placa às réguas (4) e elo soldado (B) dentro da fileira.

Para cada opção, dizer:
- custo (peças, tipos Extended, cabos);
- minutos de montagem e de solda em casa, e o nível de dificuldade para um amador;
- confiabilidade e facilidade de troca;
- impacto na placa principal (J601–J604) e na régua;
- recomendação.

O J prefere comprar, mas aceita soldar.

### 4. Alto-falante: qual tamanho daria graves decentes (só informação)

Resposta do Chat ao J. Não é tarefa.

Para uma nota como G3 (196 Hz) soar com nível razoável, o alto-falante precisa de ressonância (Fs) abaixo de ~150–200 Hz e de uma caixa fechada de volume comparável ao seu Vas.
- Na prática: um driver de ~50 mm de faixa larga, numa caixa de ~200–300 cm³, com ~20–25 mm de profundidade só para ele.
- Isso é 20 a 30 vezes a caixa atual (10 cm³) e mais alto que a interface inteira.

Ordem de grandeza, não cálculo. Conclusão: **no formato atual, grave decente só no fone/AUX**, e o alto-falante fica como alto-falante de estudo.

## Tarefas para o Code (R5V4)

1. **[Design]** Teclado de 32 teclas (item 1):
   - modelo, fit check em 32 / 48 / 64 / 80 e novo comprimento do case;
   - chanfro externo (item 2);
   - planta geral e corte atualizados, **com nomes das notas**.
2. **[Design + Eletrônica]** Estudo da ligação das réguas (item 3), com planta e corte de cada opção e recomendação.
3. **[Eletrônica]** Contrato da régua e da placa principal conforme a opção recomendada (sem rotear); custo atualizado para 32 teclas.
4. **[Programação e som]**
   - `V4_KEYS` 32 / 48 / 64 / 80, mapa de notas e varredura com réguas cheias;
   - equalização do alto-falante (item 2);
   - compilação das três placas.
5. **[Todos]** Relatórios com figuras de planta e corte; `CLAUDE.md` atualizado (32 teclas, módulos de 48/64/80). Terminar com "Perguntas para o design".

---

# Anexo — SPEC R4V4 (referência)

Data: 21 nov 2026 · Autor: Claude Chat · Destino: Claude Code
Responde ao PR #183 (relatórios da R3V4). Tudo o que não é mencionado aqui continua como nas revisões anteriores (anexos abaixo). Os relatórios citam "R4V4".

## Mudanças desde a R3V4

### 1. STEP da KS-20

O J reenviou `KS-20T-20210922.stp`. É o **mesmo arquivo** que já está em `fornecimento/gateron/` (SHA-1 idêntico). Continua valendo o que o design achou:
- é a revisão de 2021, com poste central e dois postinhos de haste;
- **serve só para o envelope da carcaça de cima** (fit check e renders);
- pinos, furação e haste vêm do **desenho PDF da Orange**.

Nenhuma ação.

### 2. Decisões aprovadas (respostas do Chat ao PR #183, sem objeção do J)

| Tema | Decisão |
|---|---|
| Grade-régua | **(b): FR-4 de 1,6 mm em desenho próprio**, sem montagem, painel de 5, no mesmo pedido das réguas. A espuma sai de cena (fica só como registro). |
| Deck | **2,5 mm com 5 / 8 / 11 / 14 postes** (28 / 44 / 60 / 76 teclas). O critério antigo de 0,05 mm a 3 N era para a placa sob o sensor; o deck agora não toca as teclas. |
| Folga deck–carcaça e botão | 1,0 mm; topo da cabeça do botão a ZR + 22,8. |
| Fixação da régua | 2 M2 não magnéticos por régua, com inserto na bossa do degrau; furo da régua Ø2,2. |
| Tecla | **KS-20 Orange.** A Low Profile Jade sai do estudo (só volta se aparecerem desenho, STEP e molas pesadas). |
| Sensor | **TMAG5253 BA3 mantido.** O último trecho do curso passa da faixa linear de ±80 mT (risco aceito, a medir na 1ª placa). O BA4 fica de reserva, no mesmo footprint. |
| Varredura | Rodar num `IntervalTimer` com prioridade acima do áudio. **396 MHz por padrão**; 600 MHz só se a medição na placa pedir. |
| Placa principal | USB-C na parede esquerda em **y 10**, módulo e H101 5,5 mm à esquerda: **aprovado**. |
| Conector da fileira 2 | O J602 fica com só 2,5 mm de vão. O conector de **entrada da régua vai por baixo dela, no bolso**, longe da ponta, para o plugue e a curva do cabo caberem sem mexer na placa principal. Design e eletrônica definem juntos e atualizam o contrato da régua. |

### 3. Portão P, parte 1: o J quer ver a planta antes de aprovar

O J **só aprova o posicionamento depois de ver uma planta geral**. O roteamento da placa principal **não começa** antes disso.

O Chat desenhou uma planta preliminar a partir de `pcb/posicao_v4.json` (`spec_img/planta_geral.png`, `spec_img/placa_blocos.png`, script `spec_img/planta_chat.py`). A bateria e o alto-falante estão nas posições da V3, **a confirmar**. O Code faz a versão oficial, com o modelo real:
- **Instrumento inteiro, vista de cima**, com:
  - contorno do case, placa principal, réguas e teclas;
  - bateria, alto-falante e caixa acústica, tela e janela, knobs, botão;
  - USB-C e jacks na parede, furos e postes da tampa, cabos das fileiras.
- **Placa principal**, topo e fundo, com os blocos coloridos e rotulados (USB, MicroMod, energia, áudio, interface, fileiras) e as cotas principais.
- **Um corte lateral pela interface**: placa, módulo, bateria, alto-falante, tela, knobs e tampa, com as alturas.
- Tudo em `POSICIONAMENTO.md`, com uma lista curta do que mudou desde a planta do Chat.

### 4. Voz e microfone (respostas do J)

1. **Saída da voz:**
   - Por padrão, a voz e os efeitos de voz saem **só no fone ou no AUX** (jack OUT).
   - O usuário pode ativar a saída pelo alto-falante; ao ativar, a tela mostra um **aviso de possível microfonia**.
2. **Filtro de amplitude da captação (anti-microfonia):**
   - Opção de configuração no firmware: limiar ajustável da porta de ruído/expansor na entrada, com ataque, retenção e soltura, e passa-altas.
   - Objetivo: só passa a voz de um **microfone bem próximo da boca**.
   - Estudar também um supressor automático de microfonia (filtros notch que seguem a frequência que realimenta) e dizer o custo de CPU.
3. **Harmonizador que segue a tecla:**
   - Nova opção, ativável pelo usuário: o harmonizador desloca a voz **para a(s) nota(s) tocada(s) no teclado**.
   - Precisa detectar a afinação da voz (YIN ou autocorrelação) e escolher o deslocamento.
   - Mantém o modo de intervalo fixo.
   - Estimar CPU e latência.
4. **Controle pelos knobs e pela tela:**
   - Ativar e desativar efeitos (e os ajustes de voz, saída e configuração) será feito com **os 2 knobs navegando um menu visual na tela OLED**.
   - O programação e som propõe:
     - a árvore do menu;
     - os gestos, sem conflitar com o liga/desliga (clique de 2 s no volume). Sugestão: clique longo no seletor abre o menu, o seletor navega e confirma, o volume ajusta o valor e o clique do volume volta;
     - as telas (128 × 64).
   - Implementar no driver OLED existente. Os CCs continuam valendo para a página.

## Tarefas para o Code (R4V4)

1. **[Eletrônica + Design]** Planta geral do portão P parte 1 (item 3) e `POSICIONAMENTO.md` atualizado. **Roteamento só depois do "aprovado" do J.**
2. **[Design]** Aplicar as decisões do item 2 no modelo; posição real da bateria, do alto-falante e da caixa acústica com o Dayton CE28MB-8 (`acustica.py`); conferir a janela e a fenda da tela, e os furos H1–H4 contra os postes da tampa.
3. **[Design + Eletrônica]** Conector de entrada da régua por baixo, no bolso (item 2), e contrato da régua atualizado.
4. **[Eletrônica]** Fase B da régua e da grade-régua:
   - esquema e posicionamento da régua (sem trilhas);
   - Gerbers da grade-régua de 1,6 mm;
   - painéis;
   - `POSICIONAMENTO.md` parte 2, também com planta e corte, para o portão P parte 2.
5. **[Programação e som]**
   - Item 4 inteiro: saída da voz, filtro de amplitude e supressor de microfonia, harmonizador que segue a tecla, menu pelos knobs e pela tela.
   - Varredura em `IntervalTimer`.
   - Tudo em `FIRMWARE.md`, com o menu desenhado em texto ou imagem para aprovação.
6. **[Design]** Atualizar o `CLAUDE.md` com as decisões da R4V4. Fechar o `FIT_CHECK.md` com "Perguntas para o design".

---

# Anexo — SPEC R3V4 (referência)

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
