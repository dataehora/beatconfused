# eTutti Student V01 · case do protótipo

15 nov 2026. Decisões do J: placa retangular mantida, então o case é retangular dos dois lados; bateria sob a placa, na frente à esquerda; abre-se o fundo inteiro; **o teclado é coberto por um tampo perfurado, e só a haste de cada tecla sai para fora, como num teclado de acordeão**. Com esse ajuste o J aprovou o case. **Nada foi impresso nem encomendado.** É um case para tocar o protótipo, não a forma final do instrumento (o perfil A fica para uma segunda placa).

```
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/case/case.py
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/case/fit_check.py
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/model3d/build.py --no-export
```

Arquivos para imprimir em `case/out/`, em STEP e STL: `fundo`, `tampa`, `espacador` (imprimir 4) e `capa` (imprimir 28). Imagens em `model3d/img/student_v01_case_*.png`.

## Medidas

| | mm |
|---|---:|
| Por fora | 251,3 × 99,8 × 23,3 |
| Parede e fundo | 2,0 |
| Folga entre a placa e a parede | 0,4 |
| Fundo interno, abaixo da face de cima da placa | 8,1 |
| Tampo, acima da placa | 13,2 |
| Tampo sobre o teclado (deck) | 1,6 de espessura, 0,4 acima do alojamento das teclas |
| Altura total com os botões | 32,0 (topo do botão a 21,9 acima da placa, 8,7 acima do tampo) |
| Altura total com os knobs | ~37 (eixo do encoder a 24,5, a conferir) |
| Plástico | ver `out/case.json` |

## As peças

**Fundo.** Bandeja sob a placa. As paredes sobem até a face de cima da placa.
- 8 ressaltos Ø6 sob os furos M2, com furo passante e rebaixo para a cabeça do parafuso;
- **os 6 pilares Ø4** que apoiam o teclado, nas posições calculadas no `viaggio_j1/FABRICACAO.md` (pior tecla 0,048 mm a 3 N);
- berço da bateria: nervuras baixas em três lados; o quarto lado é a parede da frente;
- furo Ø3 para alcançar o botão Program com um clipe;
- um rebaixo de 0,7 mm no topo da parede esquerda, sob o tubo do jack.

**Tampa.** Paredes da placa para cima e tampo plano, que cobre também o teclado.
- sobre as teclas o tampo é um deck de 1,6 mm com **28 furos Ø7**, um por tecla; por baixo, uma borda em volta do teclado desce até o plate e o prende;
- furos Ø8,4 para os dois encoders e Ø3,1 para um guia de luz de 3 mm sobre o LED (o guia agora precisa de ~12 mm de comprimento);
- grade de 85 furos Ø1,6 e um anel por baixo onde o alto-falante Ø36 encosta (colar);
- aberturas para o USB-C e o fone na parede esquerda, abertas embaixo, para a tampa descer sobre os conectores;
- 4 colunas Ø4,6 que recebem os parafusos.

**Capa (botão)**, 28: uma haste Ø5,6 que atravessa o furo do deck e encaixa na cruz da tecla, e uma cabeça abaulada Ø16,5 acima do tampo. Substitui a capa do Pocket, que tinha saia e não passaria pelo furo.

**Espaçador**, 4: anel de 3,45 mm entre a placa e o plate, nos quatro furos que ficam entre as teclas.

## Como fecha

8 parafusos M2 × 16 por baixo.

| Furos | Atravessam | Prendem em |
|---|---|---|
| H1 a H4 (fora do teclado) | fundo, placa | coluna da tampa (auto-atarraxante no plástico, furo guia Ø1,6) |
| H5 a H8 (entre as teclas) | fundo, placa, espaçador, plate | porca M2 sobre o plate |

Ordem de montagem: teclas no plate; plate sobre a placa com os 4 espaçadores e as 4 porcas; tampa; **por último os 28 botões, encaixados por cima, cada um pela sua haste**. Para abrir a tampa, tiram-se antes os botões.

## Conferência de encaixe (`fit_check.py`)

Nenhum ponto de nenhuma peça do instrumento fica mais de 0,15 mm dentro do plástico do fundo ou da tampa. Folgas:

| | mm |
|---|---:|
| Sob a bateria | 0,5 |
| Sob o conector da bateria (a peça mais alta de baixo) | 1,4 |
| Sob o módulo | 2,2 |
| Entre o deck e o alojamento das teclas | 0,4 |
| Em volta da haste do botão, no furo do deck | 0,7 |
| Entre o tampo e a cabeça de um botão apertado até o fim | 0,7 |
| Entre o alto-falante e a placa | 6,6 |
| Coluna do furo H1 até a borda do plate | 0,4 |

A conferência achou e eu corrigi três coisas: o alto-falante estava desenhado acima da tampa (agora encosta nela por baixo), o tubo do jack descia 0,25 mm sobre a parede do fundo (daí o rebaixo), e com o tampo mais alto o pé dos knobs entrava 0,5 mm nele (os knobs agora assentam 0,5 mm acima do tampo).

## O que a conferência não cobre

1. **Os botões.** A haste tem 6,8 mm entre a tecla e a cabeça e só 0,7 mm de folga no furo. Se a impressão sair torta ou a cruz ficar frouxa, o botão balança e pode raspar no furo. **Imprimir 3 ou 4 primeiro e testar numa tecla.** A cruz (4,15 × 1,30 mm, 3,8 de fundo) é a medida do Pocket, que também nunca foi impressa.
2. **O deck sobre as teclas** tem 1,6 mm e é sustentado só pela borda em volta do teclado. No meio ele pode ceder um pouco se alguém apoiar a mão; se ceder 0,4 mm, encosta nas teclas. Há espaço para nervuras entre as fileiras se for preciso.
3. **Pernas dos encoders e a bateria.** As pernas descem 2,3 mm sob a placa e a bateria fica logo abaixo. **Cortar as pernas a 1 mm depois de soldar** e pôr uma fita ou espuma fina entre elas e a bateria. O modelo não testa peça contra peça, só peça contra case.
4. **Os dois knobs.** Os eixos estão a 16 mm um do outro: knobs de até 14 mm de diâmetro. Acima do tampo sobram 11,3 mm de eixo para o knob (com o eixo a 24,5; só 6,8 se ele for de 20).
5. **Tolerâncias de impressão.** Furos e folgas estão em medida nominal. Numa impressora de filamento, os furos pequenos saem mais apertados: o furo guia de 1,6 pode precisar de uma broca, e os 28 furos de 7 mm podem pedir um escareador.
6. **Passagem do som.** O alto-falante fica entre a tampa e a placa, sem câmara fechada atrás. Para um protótipo serve; o grave será fraco.
7. **O plate ainda tem o contorno herdado do Pocket.** A tampa foi feita para ele como está.
8. **Fios da bateria e do alto-falante:** não foram desenhados; há espaço sob a placa e sob a tampa.

## Como fabricar

- **Impressão por filamento (PLA ou PETG)**: as duas peças grandes cabem numa mesa de 256 × 256 mm, deitadas. O fundo imprime com o chão para baixo; a tampa, de cabeça para baixo, com o tampo na mesa. Os botões imprimem de cabeça para baixo, com a cabeça na mesa. É o caminho mais barato para um protótipo.
- **Serviço de impressão (JLC3DP, PCBWay, Craftcloud)**: resina ou MJF, com os arquivos STEP. Para os botões a resina dá hastes mais retas e a cruz mais precisa.
