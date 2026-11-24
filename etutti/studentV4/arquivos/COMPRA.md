# Student V4 (32 teclas) · COMPRA.md: o que marcar e preencher em cada loja (R15V4)

24 nov 2026 (R15V4; texto de 23 nov, R13V4, corrigido com as cotações reais do J e a decisão de empilhamento/acabamento). **Nada foi comprado, cotado como compra nem subido.** A regra do projeto continua: nada se compra antes de o protótipo fechar. Este arquivo deixa a compra pronta para copiar e conferir. Convenções: **visto** = preço visto numa página de loja ou na biblioteca da JLCPCB (data indicada, sem frete e sem imposto); **estim.** = conta minha, sem cotação; **(conferir)** = sem medida ou página conferida agora. Moeda: US$ (a libra é suposição de 1,30 US$ por £). Páginas das lojas não foram abertas nesta rodada (só a biblioteca da JLCPCB, por curl, e as páginas de 15 a 22 nov): **confira estoque, preço e a loja do Reino Unido na hora.**

Arquivos que vão para a JLCPCB (todos nesta pasta):
- principal: `principal/student_v04_gerbers.zip`, `principal/bom.csv`, `principal/cpl.csv`
- réguas R8 (painel de 2): `regua/R8_painel2/gerbers.zip`, `bom.csv`, `cpl.csv`
- folhas de apoio: `principal/LEIAME_COTACAO.md`, `regua/LEIAME_COTACAO.md`, `../fornecimento/MODELOS_3D.md`

## 1. JLCPCB · placa principal (pedido 1)

Telas na ordem da página de pedido (Instant Quote). Valor = o que marcar.

| # | Campo | Valor | Observação |
|---|---|---|---|
| 1 | Upload | `principal/student_v04_gerbers.zip` | a página deve ler 75,05 x 95,1 mm, 4 camadas |
| 2 | Base Material | FR-4 | |
| 3 | Layers | 4 | |
| 4 | Dimensions | lido do Gerber | conferir 75,05 x 95,1 |
| 5 | PCB Qty | 5 | mínimo; as 3 nuas sobram |
| 6 | Product Type / Delivery Format | Industrial/Consumer, **Single PCB** | |
| 7 | PCB Thickness | **1.2 mm** | |
| 8 | Specify Stackup | **No** (R15V4) | o empilhamento padrão da JLCPCB basta: o par USB é Full Speed e tem 7,4 mm, não há linha de impedância controlada. **Um empilhamento especificado obriga a montagem Standard.** (A R13V4 pedia JLC04121H-7628; não vale mais.) |
| 9 | Material Type | FR4 **TG135** | |
| 10 | Surface Finish | **ENIG** ou **HASL sem chumbo** (o J decide na hora, ver a nota abaixo da tabela) | ENIG = decisão do J (passo fino: M.2, USB-C, QFN 0,4 mm); Au 1 U" é o padrão |
| 11 | Outer / Inner Copper | **1 oz / 0.5 oz** | |
| 12 | Specify Layer Sequence | No | |
| 13 | Via Covering | **Plugged** | decisão do J |
| 14 | Min via hole size/diameter | **0.3 mm / (0.4/0.45 mm)** | a placa usa vias 0,5/0,3: ok |
| 15 | Board Outline Tolerance | ±0.2 mm (Regular) | |
| 16 | Impedance Control | **não** | o par USB (7,4 mm) é só cálculo |
| 17 | Confirm Production file | No | |
| 18 | Mark on PCB | **Remove Mark** | |
| 19 | Electrical Test | **Flying Probe Fully Test** | |
| 20 | Demais opções avançadas (cor, serigrafia, borda dourada, ...) | defaults / No | cor verde |
| 21 | **PCB Assembly** | ligado | |
| 22 | PCBA Type | **Economic** | o site pode passar para Standard sozinho ao subir BOM e CPL: ver a nota abaixo (erro do site com ENIG, confirmado pelo suporte) |
| 23 | Assembly Side | **Bottom Side** | as 78 peças estão no fundo, 0 no topo |
| 24 | PCBA Qty | **2** | mínimo; uma para o instrumento, outra reserva (a segunda custa só peças, ~US$ 21) |
| 25 | Tooling holes | **Added by JLCPCB** | a placa não tem trilho |
| 26 | Confirm Parts Placement | **Yes** no primeiro pedido, **se for grátis** | a JLCPCB manda a posição para o J aprovar antes de soldar; é o que torna a conferência de pino 1 e boca definitiva |
| 27 | Stencil / Fixture storage | No | |
| 28 | Parts Selection | **By Customer (Self-Service)** | |
| 29 | BOM / CPL | `principal/bom.csv` / `principal/cpl.csv` | |

**ENIG ou HASL, e por que o site passa a montagem para Standard (R15V4, achado do J em 24 nov):** com **ENIG** a JLCPCB passa o PCBA para **Standard** ao subir BOM e CPL. **O suporte da JLCPCB confirmou que é um erro do site.** Nenhuma peça da BOM é "Standard only"; o codec, as peças perto da borda e a placa de 75 x 95 mm **não** são a causa; nada muda na BOM nem na montagem. O J refaz a cotação quando o erro for corrigido. Se o erro continuar, a alternativa é **HASL sem chumbo**: **placa cerca de US$ 12 mais barata** e **Economic**, **cerca de US$ 24 mais barato no total**. As duas opções ficam registradas; o J escolhe na hora de pedir (HASL perde um pouco de planeza nos pads de 0,4-0,5 mm do QFN-20 e do M.2; ENIG foi a escolha do J por isso).

**Na tela da BOM:** as 32 linhas devem aparecer **encontradas e com estoque** (14 tipos Extended); C310 **não** está na BOM (não montar). **Estoque mais baixo (conferir):** M.2 C48985906 (553), SGTL5000 C2651833 (1 150), BQ24074 C54313 (2 837), PJ-327A C49284723 (3 259), SM04B C160404 (4 511). Qualquer linha sem estoque: parar e avisar.
**Na tela de posições (pré-visualização):** use a lista de conferência de `principal/LEIAME_COTACAO.md` contra `pcb/img/previa_jlc_principal_bottom.png`. Peças de furo passante: **não há** na BOM (os 2 encoders e o alto-falante são de casa).
**Cotação real do J (24 nov, ENIG, PCBA Standard porque o site trocou): US$ 158** = placa 25,50 + montagem 132,62 (setup 25,75, stencil 8,27, peças 46,29, carga dos alimentadores 49,60, SMT 2,21, embalagem 0,50); montagem em 3-4 dias, sem custo extra. **É o valor oficial** (substitui a estimativa 113,4-138,4). Com HASL e Economic: **cerca de US$ 134** (-24; estimativa a partir da informação do J, não cotada). Mínimo 5 placas nuas, 2 montadas.
Tabela da principal: bate com a do J (4 camadas, 1,2 mm, ENIG, 1 oz/0,5 oz, Plugged 0,3/0,4/0,45, Flying Probe, Economic, Bottom, Qty 2, tooling by JLCPCB); **a única mudança da R15V4 é Specify Stackup = No.** A serigrafia da placa foi limpa na R15V4 (`principal/LEIAME_COTACAO.md`): a pré-visualização mostra só os rótulos.

## 2. JLCPCB · régua R8 em painel de 2 (pedido 2, outro pedido: uma variante por pedido)

Mesma tabela da principal, com as diferenças:

| Campo | Valor | Observação |
|---|---|---|
| Upload | `regua/R8_painel2/gerbers.zip` | painel 161,6 x 44 mm |
| Layers | **2** | só F.Cu e B.Cu |
| Delivery Format | **Panel by Customer: 1 coluna x 2 linhas**, sem V-cut, sem edge rails extras | o painel traz trilhos de 5 mm, abas de 3 mm com microfuros D0,5 e furos de ferramenta D2,0 |
| PCB Thickness | 1.2 mm | |
| Specify Stackup | No | |
| Surface Finish | **HASL lead-free** | ENIG é opção se a JLCPCB reclamar da planeza do X2SON e do DHVQFN (pads de 0,5 mm): cote os dois |
| Copper | 1 oz | |
| Via Covering / vias | defaults; mín. 0,3 mm | |
| PCB Qty | **5 painéis** | = 10 réguas nuas |
| PCBA Qty | **2 painéis** | = **4 réguas montadas = 32 sensores** |
| Assembly Side | Bottom | |
| Tooling holes | **Added by Customer** | o painel os tem (D2,0 + 3 fiduciais); se a JLCPCB não aceitar o painel: Added by JLCPCB |
| Confirm Parts Placement | Yes (se grátis) | |
| BOM | `regua/R8_painel2/bom.csv` (Complete File) | 5 linhas, 3 Extended: TMAG5253BA3 C22401868, 74HC595BQ C730243, SM06B JST C160405 |
| CPL | `regua/R8_painel2/cpl.csv` | designadores `U1-1`, `J1-1`... |

**Mínimos:** 5 painéis nus, **2 montados**: o instrumento de 32 teclas usa exatamente os 2 (4 R8); sobram 3 painéis nus (6 R8 sem peças).
**Risco principal:** o lado de 44 mm do painel é menor que os 70 mm da montagem padrão: a JLCPCB pode recusar, acrescentar trilho (custo não informado) ou pedir o painel de 4 (`R8_painel4/`, 161,6 x 76 mm, 8 réguas montadas, ~US$ 71-102) ou "Panel by JLCPCB" com 1 tira.
**Cotação real do J (23 nov): US$ 72** (5 painéis, 2 montados = 4 réguas), valor oficial (a estimativa era 47,3-64,2).
**Outras variantes** (só as linhas que mudam): **R8E** (primeira régua de 48/64/80 teclas): mesmo Gerber, `regua/R8E_painel2/bom.csv` e `cpl.csv` (com J2 e R1), pedido à parte; **R4 / R4E:** `regua/R4_painel5/` (gerbers diferentes: painel 87,6 x 92 mm, 5 tiras), 5 painéis nus, 2 montados = 10 réguas; fora das 32 teclas.

## 3. Itens fora da JLCPCB

Lojas do Reino Unido citadas são as que tenho como prováveis; **nenhuma foi aberta agora (conferir)**. Preços: visto na data indicada ou estim.

| # | Item | Qtd (32 teclas) | Loja (Reino Unido primeiro, se houver) / código | Opções a escolher | Preço |
|---|---|---:|---|---|---|
| 1 | **SparkFun MicroMod Teensy** (DEV-16402; RT1062, 16 MB; **sem PSRAM**) | 1 (+0) | DigiKey UK, Mouser UK, Pimoroni/The Pi Hut (conferir estoque), SparkFun | com a **fita/parafuso M2,5 x 3** (vem no módulo? conferir; senão comprar M2,5 x 3 e o espaçador de 2,5 mm do H101) | £18,69 sem IVA na DigiKey UK (visto 15 nov) = ~US$ 24 |
| 2 | **OLED Adafruit 326** (0,96", SSD1306, STEMMA QT) | 1 | Adafruit (US$ 17,50, 1-9); no Reino Unido: Pimoroni ou The Pi Hut costumam revender a Adafruit (conferir) | **endereço 0x3D de fábrica** (o firmware tenta 0x3D e 0x3C); não escolher o modelo sem STEMMA QT | US$ 17,50 (visto 22 nov) |
| 3 | **Cabo Qwiic / STEMMA QT de 50 mm** (Adafruit 4210 ou SparkFun PRT-14426) | 1 (+1 reserva) | Adafruit, SparkFun, Pimoroni | SH de 4 vias nas duas pontas, **pino a pino**, 50 mm (o menor); não o de uma ponta solta | ~US$ 1 (visto 22 nov) |
| 4 | **Cabos SH 6 vias** `A06SR06SR30K51B` (JST, 50,8 mm, pino a pino) | **4 + 2 reserva = 6** | DigiKey UK, Mouser UK, Farnell UK (código JST) | **comprimento 50,8 mm (a de 300 mm não)**; **reto**, não cruzado; conferir **antes de comprar** se o código é o de 50 mm (o do design supõe fio livre de 45,8-50,8 mm, **não medido**) | US$ 1,2-1,4 cada (visto 22 nov, biblioteca JLCPCB/LCSC); 4 = ~5,7 |
| 5 | **Bateria LiPo 503450** 3,7 V ~1 000 mAh, **3 fios com NTC**, plugue **JST PH 2,0 mm de 3 pinos** | 1 | eBay UK, Amazon UK, Pimoroni | **3 fios** (o terceiro = NTC 10 kΩ); ordem dos fios do plugue varia: **medir 10 kΩ** entre preto e o terceiro e conferir pino 1 = + (J202) **antes de ligar** | £5-8 (visto 15 nov) |
| 6 | **Alto-falante Dayton CE28MB-8** (Ø28 x 4,5 mm, 8 Ω) | 1 | Parts Express (EUA); no Reino Unido: conferir (Farnell/CPC/Cool Components não costumam ter) | 8 Ω; pedir a fs (ressonância) se houver | ~US$ 7-10 (estim., conferir) |
| 7 | **Teclas Gateron KS-20 Magnetic Orange** (KS-20TO10B050NW-Y64, 38 gf) | **32** (1 pacote de 35) | loja da Gateron, Chosfox (UK: conferir) | **Orange**; pacote de 35 | US$ 24,50-26,60 (visto 15 nov) |
| 8 | Molas longas (opcional, para mais peso) | 1 pacote de 65 g e 1 de 80 g | lojas de teclado mecânico UK (Candykeys, Cherry Keebs: conferir) | 20-22 mm, ~65 g e ~80 g; **não testado** que encaixam na KS-20 | poucas libras (visto 15 nov) |
| 9 | **Capas das teclas** (um desenho só para todas as fileiras) | 32 | impressas, mesmo serviço do case (MJF/resina) | arquivos `case/out/capa*.stl` (cor: branco para naturais, preto para sustenidos, pontos em C e F) | incluso no case (estim.) |
| 10 | **Encoders Alps EC11E18244AU** (C202365, eixo 20 mm, 18 pulsos/36 detentes) | 2 (+1) | LCSC (US$ 1,92 no lote de 10, visto 16 nov); Mouser/DigiKey UK (Alps Alpine EC11E18244AU) | **eixo D de 20 mm** (não o EC11E18244A5 de 25 mm); com clique | ~US$ 2 cada |
| 11 | **Knobs** (chapéu de 10 mm para eixo D de 6 mm) | 2 | impressos (arquivo `knob`) ou loja | eixo com chato | incluso no case |
| 12 | **Parafusos M2 passantes** (régua): 8, **2 de cada comprimento M2 x 10, 12, 14, 16** (fileiras 1 a 4) | 8 (+4) | ferragem online UK (Accu, Bolt Base, Ebay) | **aço inox A2**, cabeça panela, **não magnético** (sensores Hall); sempre pedir M2 x 10 / 12 / 14 / 16 | centavos (estim. US$ 0,03-0,05) |
| 13 | **Porcas M2** | 6 normais + **2 finas (1,2 mm) para a fileira 4** | idem | A2, não magnéticas | US$ 0,015 |
| 14 | **Parafusos formadores de rosca M2 (PT 2,0)**: **tampa, 15 x M2 x 14** (H1..H4, 5 postes internos, 6 postes de parede); **OLED, 4 x M2 x 4** | 19 (+10 reserva) | idem | cabeça panela, inox ou aço; **reaplicar o parafuso formador de rosca tem limite (5-10 vezes, estimativa)** | US$ 0,04 |
| 15 | **Pés adesivos** (colados direto na face de baixo da base, sem rebaixo): **3M Bumpon SJ5302** (poliuretano, 70A+ de dureza: Shore A 72, hemisférico, **Ø7,94 x 2,2 mm**, adesivo acrílico) · loja **RS Components UK, código 179-4811** (pacote de 80). **Posições (x; y na planta, mm, a ≥ 9 mm de qualquer furo ou bolso e ≥ 7 mm da borda):** (9; 7), (9; 66), (72; 26), (63; 90), (134; 7), (150; 90), (212; 7), (234; 81) | **8** (1 pacote de 80 sobra para trocas) | RS Components UK (179-4811); alternativa: Farnell/Rapid, SJ5302 | altura de 2,2 mm (a lista pedia 1-2: é o menor Bumpon 3M achado); a RS UK mostra também uma ficha "buffer preto" no 192-5624: **confira a cor e a altura na página antes de pedir** (o SJ5302 da 3M é transparente) | pacote de 80: preço **não lido** (estim. £5-8) |
| 16 | **MicroMod no H101**: parafuso de **náilon M2,5 x 8** + **porca de náilon M2,5** + **espaçador de náilon de 2,5 mm** | **2 parafusos, 2 porcas, 2 espaçadores** (1 + 1 reserva) | ferragem (Accu, Bolt Base, eBay UK) | o parafuso atravessa **placa 1,2 + espaçador 2,5 + módulo ~1,0 = 4,7 mm** e fecha na porca (~2 mm): 4,7 + 2 = 6,7, então **M2,5 x 8** (x 6 não fecha); **conferir a espessura real do módulo** e que a ponta (1,3 mm além da porca) não toca a base: pedido ao design | centavos (estim.) |
| 17 | **Case em MJF PA12** (tampa, base, e os impressos 9 e 11) | 1 jogo | JLC3DP, PCBWay, Craftcloud (Reino Unido: via Craftcloud/Shapeways; conferir) | **material PA12 MJF**, cor **cinza/preto** (tintável, pintar depois), acabamento **tingido/alisado se houver**, **sem** vapor-smoothing nas roscas (conferir com o serviço), **paredes mínimas 0,58 mm** nos bolsos hexagonais da fileira 4; arquivos STL de `student_v04/case/out/` (tampa, base, capas, knob); **não enviar o STL das réguas** | ~US$ 46-51 (estim. do design, MJF; não cotado) |
| 18 | Ferramentas | — | — | ferro de solda (fios do alto-falante, encoders), multímetro (NTC), chave Phillips pequena, **chave de torque** se houver | — |
| 19 | **Grade-régua FR-4 1,6 mm** (a grade do teclado: placa nua, sem montagem, sem peças) | **1 painel** (5 é o mínimo da JLCPCB, as demais ficam de reserva) | **JLCPCB**, mesmo carrinho da principal (um frete só) | upload `student_v04_grade_regua_painel_gerbers.zip` (esta pasta, `fab/`; vem de `pcb/grade_fab.py`); **2 camadas, 1,6 mm, FR-4 TG135, HASL sem chumbo, máscara preta fosca, 5 painéis, sem montagem**; **conferir quantas grades cabem num painel** (ver `student_v04_grade_contorno32_gerbers.zip` para a grade de 32 teclas inteira) | US$ 8-15 (**estim.**: placa pequena de 2 camadas + engenharia; não cotado) |

## 4. Totais do protótipo de 32 teclas (US$, sem frete, sem imposto)

| Grupo | Faixa (US$) | Tipo |
|---|---:|---|
| Principal (PCB + montagem, 2 montadas) | 158 | **cotação real do J, 24 nov** (ENIG, PCBA Standard; com HASL + Economic ~134) |
| Réguas 4 x R8 (painel de 2) | 72 | **cotação real do J, 23 nov** |
| Grade-régua FR-4 1,6 mm (JLCPCB, item 19) | 8-15 | **estim.** |
| Cabos SH (6) + cabo Qwiic | 8-10 | visto 22 nov |
| OLED Adafruit 326 | 17,5 | visto 22 nov |
| Ferragem (M2 passantes e porcas, PT, M2,5 náilon, pés; itens 12-16) | 6-12 | **estim.** |
| Case MJF (inclui capas, knobs e caixa acústica) | 46-51 | **estim.** (não cotado) |
| Teclas, módulo, bateria, alto-falante, encoders, molas, cabo USB-C (MicroMod ~24 + KS-20 24,5-26,6 + molas 3-8 + bateria 6-10 + alto-falante 7-10 + encoders 4-6 + USB-C 3-8) | 71,5-92,6 | misto: visto 15 nov (módulo, teclas, bateria) e **estim.** |
| **Total (soma das linhas)** | **387-428** | R15V4; a soma das linhas é o número oficial (**363-404** com HASL + Economic na principal); era 318-401 na R13V4, com a principal e as réguas estimadas |

As duas placas já são cotações reais (158 e 72); nas demais linhas o piso usa preços por quantidade e o teto, o preço de 1 peça.

## 5. O que o J faz, na ordem
1. Subir a principal (seção 1) até a **pré-visualização das posições**; comparar com `pcb/img/previa_jlc_principal_bottom.png` e a lista de `principal/LEIAME_COTACAO.md`; mandar o print ao Chat/Code. Não pagar ainda.
2. Subir a R8 (seção 2); ver se a JLCPCB aceita o painel de 44 mm; comparar com `previa_jlc_r8_bottom.png`.
3. Cotar o case MJF (STL) em 2 ou 3 serviços.
4. Só depois que o protótipo fechar: os itens da seção 3.
