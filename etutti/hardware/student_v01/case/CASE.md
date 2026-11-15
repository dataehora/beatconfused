# eTutti Student V01 · case do protótipo

15 nov 2026. Decisões do J: placa retangular mantida, então o case é retangular dos dois lados; bateria sob a placa, na frente à esquerda; abre-se o fundo inteiro. **Nada foi impresso nem encomendado.** É um case para tocar o protótipo, não a forma final do instrumento (o perfil A fica para uma segunda placa).

```
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/case/case.py
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/case/fit_check.py
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/model3d/build.py --no-export
```

Arquivos para imprimir em `case/out/`: `fundo`, `tampa` e `espacador` (imprimir 4), em STEP e STL. Imagens em `model3d/img/student_v01_case_*.png`.

## Medidas

| | mm |
|---|---:|
| Por fora | 251,3 × 99,8 × 19,9 |
| Parede e fundo | 2,0 |
| Folga entre a placa e a parede | 0,4 |
| Fundo interno, abaixo da face de cima da placa | 8,1 |
| Tampa, acima da placa | 9,8 |
| Altura total com as teclas | 29,0 (capas a 18,9 acima da placa) |
| Altura total com os knobs | ~36 (eixo do encoder a 24,5, a conferir) |
| Plástico | fundo 63 cm³, tampa 46 cm³ |

## As peças

**Fundo.** Bandeja sob a placa. As paredes sobem até a face de cima da placa.
- 8 ressaltos Ø6 sob os furos M2, com furo passante e rebaixo para a cabeça do parafuso;
- **os 6 pilares Ø4** que apoiam o teclado, nas posições calculadas no `viaggio_j1/FABRICACAO.md` (pior tecla 0,048 mm a 3 N);
- berço da bateria: nervuras baixas em três lados; o quarto lado é a parede da frente;
- furo Ø3 para alcançar o botão Program com um clipe;
- um rebaixo de 0,7 mm no topo da parede esquerda, sob o tubo do jack.

**Tampa.** Paredes da placa para cima e tampo plano de 2 mm.
- uma abertura só em volta das 28 teclas, com uma borda que desce até o plate e o prende;
- furos Ø8,4 para os dois encoders e Ø3,1 para um guia de luz de 3 mm sobre o LED;
- grade de 85 furos Ø1,6 e um anel por baixo onde o alto-falante Ø36 encosta (colar);
- aberturas para o USB-C e o fone na parede esquerda, abertas embaixo, para a tampa descer sobre os conectores;
- 4 colunas Ø4,6 que recebem os parafusos.

**Espaçador** (4): anel de 3,45 mm entre a placa e o plate, nos quatro furos que ficam entre as teclas.

## Como fecha

8 parafusos M2 × 16 por baixo.

| Furos | Atravessam | Prendem em |
|---|---|---|
| H1 a H4 (fora do teclado) | fundo, placa | coluna da tampa (auto-atarraxante no plástico, furo guia Ø1,6) |
| H5 a H8 (entre as teclas) | fundo, placa, espaçador, plate | porca M2 sobre o plate |

A ordem de montagem: teclas no plate, plate sobre a placa com os 4 espaçadores, porcas nos 4 parafusos do meio; depois a tampa, com os outros 4.

## Conferência de encaixe (`fit_check.py`)

Nenhum ponto de nenhuma peça do instrumento fica mais de 0,15 mm dentro do plástico do fundo ou da tampa. Folgas:

| | mm |
|---|---:|
| Sob a bateria | 0,5 |
| Sob o conector da bateria (a peça mais alta de baixo) | 1,4 |
| Sob o módulo | 2,2 |
| Entre o alto-falante e a placa | 3,2 |
| Tampa acima do USB-C / do jack | 4,6 / 3,1 |
| Entre a tampa e a capa de uma tecla apertada até o fim | 1,0 |
| Coluna do furo H1 até a borda do plate | 0,4 |

A conferência achou e eu corrigi duas coisas: o alto-falante estava desenhado acima da tampa (agora encosta nela por baixo), e o tubo do jack descia 0,25 mm sobre a parede do fundo (daí o rebaixo).

## O que a conferência não cobre

1. **Pernas dos encoders e a bateria.** As pernas descem 2,3 mm sob a placa e a bateria fica logo abaixo. **Cortar as pernas a 1 mm depois de soldar** e pôr uma fita ou espuma fina entre elas e a bateria. O modelo não testa peça contra peça, só peça contra case.
2. **Os dois knobs.** Os eixos estão a 16 mm um do outro. Knobs de até 14 mm de diâmetro cabem; os da imagem (13,6 e 14,8) quase se tocam.
3. **Altura do eixo do encoder** (24,5 ou 20 mm): decide a altura do knob, não o case.
4. **Tolerâncias de impressão.** Furos e folgas estão em medida nominal. Numa impressora de filamento, os furos pequenos saem mais apertados: o furo guia de 1,6 pode precisar de uma broca.
5. **Passagem do som.** O alto-falante fica entre a tampa e a placa, sem câmara fechada atrás. Para um protótipo serve; o grave será fraco.
6. **O plate ainda tem o contorno herdado do Pocket.** A tampa foi feita para ele como está.
7. **Fios da bateria e do alto-falante:** não foram desenhados; há espaço sob a placa e sob a tampa.

## Como fabricar

- **Impressão por filamento (PLA ou PETG)**: as duas peças cabem numa mesa de 256 × 256 mm, deitadas. O fundo imprime com o chão para baixo; a tampa, de cabeça para baixo, com o tampo na mesa. É o caminho mais barato para um protótipo.
- **Serviço de impressão (JLC3DP, PCBWay, Craftcloud)**: resina ou MJF, com os arquivos STEP. Acabamento melhor; pedir cotação com os dois arquivos.
