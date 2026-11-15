# eTutti Student V01 · resumo para a gestão (Chat)

15 nov 2026. Escrito pelo Code, a pedido do J, para abrir no Chat a análise de um possível novo conceito de design depois da apresentação do protótipo. Tudo o que está aqui está no `main` do repositório `dataehora/beatconfused`, em `etutti/hardware/student_v01/`.

## 1. O que é a Student V01

O primeiro eTutti que vai ser fabricado. É a placa do Viaggio MicroMod que o J roteou (pasta `viaggio_j1/`), levada até o pedido com o nome novo, mais firmware e um case de protótipo.

| | |
|---|---|
| Teclado | 28 teclas C-griff, G3–E5, grade de 18,5 mm, fileiras a 16,02 mm; fileiras de 7, 8, 7 e 6 teclas |
| Teclas | Gateron KS-20 magnéticas (Orange, 38 gf), um sensor Hall TMAG5253 sob cada uma, com velocity |
| Processador | módulo SparkFun MicroMod Teensy, encaixado em casa num conector M.2 |
| Som | codec SGTL5000 (fone) e amplificador MAX98357A com alto-falante fino Ø36 mm |
| Energia | USB-C, LiPo de 1 célula ~1000 mAh (503450, 3 fios), liga/desliga no clique do knob de volume |
| Interface | dois encoders com clique (volume; seletor de registro) e um LED bicolor |
| Placa | retângulo de 246,5 × 95 mm, cantos R 5, 4 camadas, 1,2 mm; tudo montado pela JLCPCB |
| Som do instrumento | acordeão amostrado, sete registros (L, ML, MM, MH, H, LH, M); a velocity age como pressão de fole |

## 2. Estado

**Projeto conferido e pronto para compra. Nada foi encomendado, impresso ou montado.** O J vai apresentar antes de comprar.

| Parte | Estado | Onde |
|---|---|---|
| Placa | roteada, DRC limpo, igual ao esquema | `kicad/`, `fab/` |
| Lista de montagem | os 42 códigos LCSC conferidos um a um; 5 estavam errados e foram corrigidos | `fornecimento/FORNECIMENTO.md` |
| Posições da montagem | refeitas a partir dos pads; a prévia da JLCPCB foi conferida pelo J | `fab/student_v01_cpl.csv` |
| Firmware | compila para o módulo; pinos e teclas conferidos contra a placa; **nunca rodou numa placa** | `FIRMWARE.md` |
| Modelo 3D | instrumento completo, com os modelos reais das peças | `model3d/` |
| Case do protótipo | modelado e conferido contra o modelo 3D; aprovado pelo J | `case/CASE.md` |
| Compras | lista e roteiro do pedido | `LISTA_DE_COMPRAS.md` |

Pedido previsto: 5 placas (o mínimo), 2 montadas, cerca de US$ 220 a 265 mais ENIG e frete. Fora disso: plate de FR-4, teclas, molas de 65 e 80 g para testar um peso de tecla próximo ao de um acordeão, bateria, alto-falante, o módulo (~£19) e a impressão do case.

## 3. O case do protótipo

Foi feito para tocar a primeira placa, não como forma final.

| | mm |
|---|---:|
| Por fora | 251,3 × 99,8 × 23,3 |
| Altura com os botões | 32 |
| Altura com os knobs | ~37 |
| Parede e fundo | 2 |

- Duas peças impressas, **retangular dos dois lados**, porque a placa é retangular.
- **Tampo perfurado sobre o teclado, como num acordeão:** uma chapa de 1,6 mm com um furo de 7 mm por tecla; só a haste de cada botão sai. O botão é uma peça nova, com haste de 5,6 mm e cabeça abaulada de 16,5 mm. Foi o ajuste que o J pediu.
- O fundo traz os 6 pilares que apoiam o teclado e o berço da bateria; abre-se o fundo inteiro, com 8 parafusos M2.
- USB-C e fone saem pela parede esquerda; knobs, LED e grade do alto-falante ficam no tampo, à esquerda do teclado.

## 4. O que um novo conceito de design tem de respeitar

Enquanto a placa for esta, estas medidas são fixas. Referencial: x para a direita, y para a frente (em direção a quem toca), origem no canto de trás à esquerda da placa; alturas a partir da face de cima da placa.

| | |
|---|---|
| Contorno da placa | x 2,5 a 249; y 2,5 a 97,5; cantos R 5 |
| Teclas | centros de x 89,2 a 218,7 e y 26,0 a 74,0 |
| Knobs | (20; 49) e (36; 49), a 16 mm um do outro: knobs de até 14 mm de diâmetro |
| LED | (50; 49) |
| USB-C e fone | na borda esquerda, em y 13 e y 25 |
| Alto-falante | previsto em (31; 78), sobre a placa |
| Furos M2 | 8; quatro deles entre as teclas |
| Apoios do teclado | 6 pilares sob a placa; sem eles a ponta direita cede ao tocar |
| Para cima | plate a 5,1; alojamento das teclas a 11,2; haste da tecla a 14,8; eixo do encoder a 24,5 (a conferir; pode ser 20) |
| Para baixo | módulo 4,7; conector da bateria 5,5; bateria na posição atual 6,4 |
| Curso da tecla | 4,1 mm |

O perfil A (canto esquerdo arredondado e ponta à direita, a linha pontilhada da serigrafia) **não cabe** nesta placa: os dois cantos da direita passam até 35 mm do perfil. Recortar a placa no perfil é barato (fora dele só há cobre de terra e 53 vias de costura; nenhuma peça ou trilha), mas o J decidiu manter o retângulo neste primeiro pedido.

## 5. O que está em aberto e é assunto de design

1. **A forma.** Retângulo (como está) ou perfil A, o que pede uma segunda placa recortada. É a decisão que mais muda o objeto.
2. **O peso das teclas.** A Orange tem 38 gf; uma tecla de acordeão acústico fica por volta de 80 a 95 g. Não existe tecla magnética pronta acima de ~60 gf; o caminho é trocar a mola, a testar com o protótipo.
3. **Os botões e o tampo perfurado.** A haste longa e a folga pequena no furo só se confirmam impressas. O tampo sobre as teclas é fino e pode pedir nervuras.
4. **O alto-falante.** Hoje fica entre a tampa e a placa, sem câmara atrás: grave fraco. Uma câmara própria muda o volume interno e talvez a forma.
5. **A bateria.** Só cabe num lugar sob a parte esquerda, por baixo das pernas dos encoders, e para trocá-la abre-se o fundo inteiro. Uma tampa de acesso, outra posição ou outro formato de célula são questões de design.
6. **Os knobs.** A 16 mm um do outro, limitam o diâmetro a 14 mm. Mudar isso é mudar a placa.
7. **O plate.** Tem o contorno herdado do Pocket; a forma final depende da tampa.
8. **Altura do eixo do encoder** (20 ou 24,5 mm): decide a altura e o tipo de knob.
9. **Materiais e acabamento:** o protótipo é plástico impresso. Madeira, resina ou outra coisa ficam em aberto, como no eTuttino (Seixo e Madeira).
10. **Entrada de expressão (fole):** o J deixou para uma V02. Pede mudança na placa.

## 6. O que o protótipo vai responder

Vale esperar por estas respostas antes de fechar um conceito novo:

- se o liga/desliga, a leitura dos sensores e a velocity funcionam como o firmware supõe;
- o peso de tecla preferido (38 gf, 65 g ou 80 g);
- se o botão de haste fica firme e se o tampo perfurado aguenta a mão;
- quanto som o alto-falante dá sem câmara;
- a autonomia real (estimada em 4,5 h com alto-falante e 6,6 h com fone);
- as alturas reais do módulo, do conector da bateria e do eixo do encoder.

## 7. Como seguimos trabalhando

O mesmo protocolo das outras vezes: o Chat decide a forma e escreve a especificação (uma `SPEC.md` com versão, "Mudanças desde a versão anterior" e "Tarefas para o Code"); o Code modela, confere o encaixe, responde num relatório e faz commit, PR e merge; o J leva um recado de uma linha entre os dois. O Code não edita a especificação, e o Chat não edita os arquivos do Code.

Para um conceito novo da Student, o Code já tem prontos: o modelo 3D do instrumento (`model3d/build.py`), a conferência de encaixe de qualquer case contra ele (`case/fit_check.py`) e as medidas da seção 4. Uma especificação que diga a forma externa, o material, onde ficam bateria e alto-falante e como se abre é o suficiente para começar.

## 8. Documentos

| Arquivo | O quê |
|---|---|
| `README.md` | as nove etapas da revisão, com cada decisão do J |
| `fornecimento/FORNECIMENTO.md` | códigos, estoque, custos, a correção das posições de montagem |
| `LISTA_DE_COMPRAS.md` | o que comprar e o roteiro do pedido |
| `FIRMWARE.md` | o que o firmware faz e o que só a placa vai dizer |
| `case/CASE.md` | o case do protótipo: medidas, montagem, folgas, limites |
| `model3d/img/` | as imagens do instrumento, com e sem o case |
