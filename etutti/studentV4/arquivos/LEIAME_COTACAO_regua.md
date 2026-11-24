# Réguas da Student V4 · como cotar na JLCPCB (R13V4)

**Estado (23 nov 2026): PACOTES PRONTOS PARA COTAR, nada encomendado.** Gerbers dos painéis das réguas **roteadas** (agente `roteamento`: R4 e R8 com DRC 0 erros, 0 avisos, 0 faltando, paridade 0), BOM e CPL de cada variante. Os preços abaixo são **estimativas** (`pcb/regua/custo_r11.py`), não cotações.

## Conteúdo de cada pasta `fab/regua/<variante>_painel<N>/`
`gerbers.zip` (F.Cu, B.Cu, F/B Mask, F/B Paste, F/B Silkscreen, Edge.Cuts, furação PTH e NPTH, job: **só 2 camadas de cobre, nenhuma In1/In2**), `bom.csv`, `cpl.csv`. R8 e R8E (e R4 e R4E) levam **o mesmo `gerbers.zip`**; mudam só `bom.csv` e `cpl.csv`.

## Os dois desenhos e as quatro variantes
Há **dois desenhos de placa** (R8 e R4). A "variante com OUT" (R8E, R4E) é o **mesmo Gerber** da sem OUT: só a BOM e o CPL mudam (J2 e R1 montados ou não). Por isso a JLCPCB monta **uma variante por pedido** (todas as placas de um pedido saem iguais).

| Variante | Posições | OUT (J2 + R1 de 330 ohm) | Gerber | Uso |
|---|---:|---|---|---|
| **R8** | 8 | não montado | R8 | **32 teclas (4 x)**; ponta direita de 64 e 80 |
| **R8E** | 8 | montado | R8 (o mesmo) | primeira R8 de 48, 64 e 80 |
| **R4** | 4 | não montado | R4 | ponta direita de 48 e 80 |
| **R4E** | 4 | montado | R4 (o mesmo) | reserva do conceito |

O OUT custa **US$ 0,07 por régua** (J2 + R1), por isso não vale um segundo desenho (a placa sem OUT teria o mesmo comprimento: ele é ditado pelos sensores).

## Pacotes (um por variante e leiaute de painel)
`bom.csv` (formato JLCPCB: Comment, Designator, Footprint, LCSC Part #) e `cpl.csv` (Designator, Val, Package, Mid X, Mid Y, Rotation, Layer = Bottom). Os designadores do painel são `U1-1`, `U1-2`... (referência da régua, hífen, número da tira). Posições e rotações pelo método do `cpl_jlc.py` (pads da EasyEDA assentados nos pads da placa; fundo espelhado).

| Pasta | Painel (mm) | Réguas por painel | Peças por painel |
|---|---|---:|---:|
| `R8_painel2/`, `R8E_painel2/` | **161,6 x 44** (alvo) | 2 | 40 / 44 |
| `R8_painel4/`, `R8E_painel4/` | 161,6 x 76 (alternativa se a JLCPCB recusar o de 44) | 4 | 80 / 88 |
| `R4_painel5/`, `R4E_painel5/` | 87,6 x 92 | 5 | 60 / 70 |

## O que marcar na JLCPCB (sugestão, conferir na tela da cotação)
- **PCB:** 2 camadas, **1,2 mm**, cobre 1 oz, máscara qualquer cor, **acabamento HASL sem chumbo** (mais barato) **ou ENIG** (planeza melhor para os pads de 0,5 mm do X2SON e do DHVQFN-16; cote os dois: a diferença é o que importa), contagem de furos pequena (mín. 0,3 mm), **sem** borda dourada, **sem** impedância controlada.
- **Painel:** "Panel by Customer" (o painel já vem pronto, com trilhos de 5 mm, abas de 3 mm com microfuros, furos de ferramenta D2,0 e 3 fiduciais). **Não** V-cut (o contorno tem entalhes).
- **Montagem (PCBA):** **só o fundo (Bottom)**; econômica se aceitar o painel (o lado menor de 44 mm está abaixo dos 70 mm mínimos da montagem padrão: **pode ser recusado ou a JLCPCB acrescentar trilho**; a saída é o painel de 4 tiras, 76 mm); "Tooling holes: added by customer"; confirmar a orientação das peças na **pré-visualização** (pino 1 do 595 e dos TMAG5253, orientação do J1) antes de pagar.
- **Peças:** todas em estoque na biblioteca da JLCPCB (conferido em 21-22 nov). **3 tipos Extended** por pedido (TMAG5253BA3 C22401868, 74HC595BQ C730243, JST SM06B-SRSS-TB(LF)(SN) C160405; US$ 3,09 por tipo); capacitores 100 nF (C1525) e 10 uF (C15850) e o resistor 330 ohm (C25104) são Basic.
- **Não montar / em casa:** nenhuma peça em casa nas réguas (tudo é montado pela JLCPCB); os cabos SH (`A06SR06SR30K51B` e os de 25 mm) e as teclas vêm de outro lado.

## Quantidades (mínimos da JLCPCB)
5 painéis de PCB no mínimo, **2 montados** no mínimo. Para o instrumento de 32 teclas (4 x R8): **2 painéis de 2 = 4 R8 montadas, exato**; sobram 3 painéis nus (6 R8 sem peças). Para 4 R4 (48/80 teclas) o mínimo monta 10.

## Estimativa por pedido (US$; `custo_r11.json`; faixa baixo-alto = preço na quantidade do pedido a 1 peça)
| Variante | Painel | Réguas montadas | Peças | PCB | Fixo (preparação, estêncil, 3 Extended, SMT) | **Pedido** | Por régua |
|---|---|---:|---:|---:|---:|---:|---:|
| **R8** | 161,6 x 44 | 4 | 20,3-24,9 | 4,8-17,1 | 22,3 | **47,3-64,2** | 11,8-16,1 |
| R8E | 161,6 x 44 | 4 | 23,9-28,5 | 4,8-17,1 | 22,3 | 50,9-67,8 | 12,7-17,0 |
| R8 (painel de 4) | 161,6 x 76 | 8 | 40,5-49,7 | 8,3-29,5 | 22,3 | 71,1-101,5 | 8,9-12,7 |
| R4 | 87,6 x 92 | 10 | 29,3-36,6 | 5,4-12,9 | 22,3 | 57,0-71,8 | 5,7-7,2 |
| R4E | 87,6 x 92 | 10 | 36,7-45,6 | 5,4-12,9 | 22,3 | 64,3-80,8 | 6,4-8,1 |

(R13V4: com o SH original o pedido da R8 subiu cerca de US$ 3,3, da R4 cerca de US$ 6,8.) A cotação do J (~70 para o painel de 2) passa a ~73.

O PCB acima de 100 x 100 mm usa o fator 1,0-1,5 **suposto** (a JLCPCB cobra por área acima disso; **não cotado**): é o número que a cotação real do J mais deve mudar.

## O que muda entre as variantes (resumo)
Só a BOM/CPL: R8 e R4 **sem** J2 e R1; R8E e R4E **com**. Os Gerbers, os furos, os painéis e o roteamento são os mesmos por comprimento. Os conectores IN (J1) ficam em u 5,9 em todas; o OUT (J2), quando montado, em u 121,5 (R8) ou 47,5 (R4), sempre a 26,5 mm da ponta direita.

## Conferências feitas (23 nov)
- **Gerbers:** 2 camadas de cobre (zip sem In1/In2). **Planos de GND** F.Cu e B.Cu preenchidos em cada tira, **uma rede de GND por tira** no painel (as tiras são placas separadas): DRC do painel **0 ligações faltando, 0 pontas soltas, 0 erros de folga, 0 avisos**.
- **DRC dos painéis (KiCad, regras das réguas): só `invalid_outline`** (R8 de 2: 14; R8 de 4: 27; R4 de 5: 22), que é o contorno **aberto nas abas** (a JLCPCB trata a linha da borda como o caminho da fresa), e, na R4, 5 avisos `npth_inside_courtyard` (microfuro de aba a 2,4 mm do furo M2, 1,05 mm de folga real). Nada de folga de cobre, furo ou máscara. As abas (3 mm, microfuros D0,5 a 0,9 mm) estão em u 16 e 65 (R4) e 14, 83 e 138 (R8), **fora** dos vias, dos pads do J1 e dos furos (a posição 10 mm da versão anterior caía no pad de fixação do J1).
- **CPL:** posição e giro das 7 famílias de peças **pelo método do `cpl_jlc.py`** (pads da EasyEDA assentados nos pads da placa, por número de pino; erro máximo 0,08 mm). **J1 (e J2): giro 180 no fundo**; **J401 da principal: giro 180** (fit por número de pino, erro 0,0003 mm); J601..J604: 270. O J1 (e o J2) agora é o **JST original C160405**, com modelo 3D na JLCPCB; mesmos pads do clone: giro 180 no fundo, inalterado. Ver `fornecimento/MODELOS_3D.md` e `pcb/img/previa_jlc_r8_{bottom,top}.png`.
- **Códigos LCSC** (biblioteca da JLCPCB, 21-22 nov): TMAG5253BA3 C22401868, 74HC595BQ C730243, SM06B-SRSS-TB(LF)(SN) original C160405 (Extended, US$ 0,90; o clone C56123098, US$ 0,07, fica como opção de produção, sem modelo 3D), 100 nF C1525, 10 uF C15850, 330 ohm C25104 (Basic); todos em estoque.
- **+3V3 a 0,2 mm** em parte dos trechos, junto a pads de 0,25 mm (X2SON e DHVQFN): **aceito** (corrente de ~2,5 mA, o mínimo da JLCPCB é 0,1 mm, 0,15 mm de projeto).

## Riscos (a conferir na cotação)
1. **Lado de 44 mm do painel R8 de 2 tiras** (< 70 mm da montagem padrão): a JLCPCB pode acrescentar trilho (custo não informado) ou recusar; o painel de 4 tiras (76 mm) é a saída. Outra: mandar **uma tira só** e pedir à JLCPCB para fazer o painel ("Panel by JLCPCB", abas com microfuros).
2. **Aceite do painel do cliente:** o contorno com abas fica "aberto" no DRC do KiCad (a JLCPCB deve tratar as linhas como caminho de fresa); se o engenheiro estranhar, ele pede confirmação: responder que as abas são intencionais.
3. **Corpo do C15850 (10 uF 0805) deslocado** na pré-visualização: erro da biblioteca, não do CPL (`MODELOS_3D.md`).
4. **Pads do DHVQFN-16 (74HC595BQ, 0,5 mm) e do X2SON:** footprint do original (C730243 buscado na EasyEDA); em HASL a planeza dos pads de 0,5 mm é o ponto fraco: cotar também ENIG.
5. **PCB acima de 100 x 100 mm:** o fator 1,0-1,5 do preço é suposição.

## Lista de conferência do J na pré-visualização da JLCPCB (R13V4)
Compare com `pcb/img/previa_jlc_r8_bottom.png` (e `MODELOS_3D.md`):
1. **J1 (SH de 6 vias, e J2 nas E):** a boca para o lado de **cima** do desenho (a borda de trás da régua), o pino 1 no anel vermelho; J1 em u 5,9 (à direita no desenho de baixo, espelhado).
2. **74HC595 (U9):** o ponto do corpo no canto do anel vermelho (pino 1).
3. **Os 8 TMAG5253 (U1..U8):** o desenho é simétrico girado 180: **confira só o ponto do pino 1** de cada um, no anel (o modelo tem a cova do pino 1; o corpo é de 1,4 x 1,1 mm).
4. O corpo do **C10 (10 uF 0805)** pode aparecer deslocado dos pads (modelo da biblioteca): normal.
Se algo diferir, mande o print.

**R15V4 (24 nov):** cotação real do J para a R8 em painel de 2 (5 painéis, 2 montados = 4 réguas): **US$ 72** (a estimativa da tabela acima era 47,3-64,2). Total do protótipo atualizado em `../COMPRA.md`.
