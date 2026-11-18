# eTutti Student V3 — FIT_CHECK do case (SPEC v4, ciclo 4)

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
