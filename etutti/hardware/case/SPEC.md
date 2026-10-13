# eTutti · case paramétrico (Seixo e Madeira)

Especificação para o Claude Code gerar o modelo 3D do case do eTuttino, nas duas versões:

- **Seixo**: plástico, impressão em resina ou MJF, uma cor só.
- **Madeira**: carvalho branco (white oak), CNC de 3 eixos numa fixação só, acabamento a óleo.

As duas versões têm exatamente a mesma geometria; só mudam o material e a fabricação. Os desenhos de referência estão no canvas "eTutti case concepts" (Seixo v5, Madeira v5, Botões sobre Gateron).

Medidas em mm. Tudo que estiver marcado **(conferir)** é estimativa do conceito e precisa ser confirmado com a peça real ou o datasheet.

## 1. Sistema de coordenadas

- **x**: da face esquerda (x = 0) para a direita, ao longo do comprimento.
- **y**: de trás (y = 0) para a frente (y = 100), onde fica quem toca.
- **z**: da mesa (z = 0) para cima.

## 2. Teclado C-griff (eTuttino, 44 teclas, G3–E6)

- Passo entre botões: `P = 19,05`. Diâmetro do botão: `D = 15` (raio 7,5).
- Centros das fileiras em y:

  | Fileira | Posição | y |
  |---|---|---|
  | 1 | mais perto de quem toca | 74,8 |
  | 2 | | 58,3 |
  | 3 | | 41,8 |
  | 4 | | 25,3 |

- Origem do teclado: `O = 104`. O centro de um botão fica em `x = O + xp · P`.
- Nota `n` em semitons a partir de G3 (G3 = 0). A fileira e o `xp` de cada nota:

  | Condição | Fileira | `xp` | Faixa |
  |---|---|---|---|
  | `n % 3 == 2` e `n ≤ 32` | 1 | `(n − 2) / 3` | |
  | `n % 3 == 0` e `n ≤ 33` | 2 | `n / 3 − 0,5` | |
  | `n % 3 == 1` e `n ≤ 31` | 3 | `(n − 1) / 3` | |
  | `n = 2, 5, …, 29` | 4 | `(n − 2) / 3 + 0,5` | duplica a fileira 1 |

- **Sustenidos (botão preto)**: `(n + 7) % 12 ∈ {1, 3, 6, 8, 10}`.
- **Dós e Fás** (C4, F4, C5, F5, C6 = n 5, 10, 17, 22, 29): botão branco com xadrez diagonal em relevo no topo, para achar no tato.
- Botões das pontas da fileira 2: (94,475; 58,3) e (304,025; 58,3).

## 3. Área do teclado (abertura na tampa)

### Folgas

- Nas laterais: 1 botão (15 mm), medido perpendicular à borda dos botões. A folga segue as duas diagonais das fileiras, a 30° da vertical, formando "<" à esquerda e ">" à direita.
- Na frente e atrás: ½ botão (7,5 mm).

### Contorno da abertura

Hexágono com vértices vivos:

```
(96,21; 10,3) → (302,29; 10,3) → (330,01; 58,3) → (311,82; 89,8) → (86,68; 89,8) → (68,49; 58,3)
```

- Os dois vértices laterais (y = 58,3) são arredondados com R 22,5, concêntricos aos botões das pontas da fileira 2. Assim a folga fica igual em toda a volta.
- Os quatro cantos de 120° têm R 6.

### Chanfro

- Arredondado, de 4 mm, nas quatro bordas da abertura, no mesmo material e na mesma cor da tampa.
- Contorno externo do chanfro = abertura + 4 mm:

  ```
  (93,90; 6,3) → (304,60; 6,3) → (334,62; 58,3) → (314,13; 93,8) → (84,37; 93,8) → (63,88; 58,3)
  ```

  - vértices laterais com R 26,5;
  - cantos com R 10.

### Dentro da abertura

- Placa preta de 1,5 mm com furos de 14 × 14 mm (padrão MX) nos centros dos botões.
- Switches Gateron magnéticos de carcaça escura.
- PCB com sensor Hall sob cada switch.

## 4. Caixa

### Contorno em planta

- **Largura**: 100 constante (y de 0 a 100).
- **Lado direito, frente e trás**: seguem a área do teclado a ~6 mm do chanfro externo, o que equivale à abertura + 10,3 mm. Vértices vivos do lado direito:

  ```
  (308,24; 0) → (341,90; 58,3) → (317,77; 100)
  ```

  - vértice com R 32,8, concêntrico ao botão (304,025; 58,3);
  - cantos com R 16,3.
- **Lado esquerdo**: reto em x = 0, cantos com R 16.
- **Comprimento total**: ~336,8 mm.

### Paredes e alturas

- Paredes externas verticais, a 90° da mesa, sem chanfro nem arredondamento de perfil.
- **Área do teclado**: tampa em z = 15,7. Topo dos botões em z = 26,5.
- **Área de interface** (à esquerda da área do teclado): bloco elevado com o topo inclinado para quem toca, de z = 33 em y = 0 até z = 28 em y = 100 (~3°).
- **Transição** entre interface e teclado: face inclinada, seguindo o mesmo "<".
  - borda de cima: linha a abertura + 20,3 (vértice (56,6; 58,3));
  - borda de baixo: o chanfro externo.

## 5. Área de interface, de trás para a frente

| Item | Posição / medidas |
|---|---|
| Zona da tela | x 10–64, y 5–35. Opções: rebaixo raso de 1,5 (conferir), tela rente, ou sem tela (eTuttino) com gravação ou adesivo |
| Tela | 1,9″ 320 × 170. Área visível ~43 × 23 centrada na zona (conferir datasheet do módulo) |
| Volume | potenciômetro contínuo, eixo em (20; 45), knob Ø 9 |
| Seletor de instrumento | encoder com clique e giro infinito, eixo em (37; 45), knob Ø 9 |
| LED | Ø 3,5 em (52; 45), à direita dos knobs. Na Madeira, LED "fantasma": parede de madeira < 1 mm por cima |
| Grade | furos Ø 1,9 a passo de 4 |

Contorno da grade:

```
(13; 60) → (55; 60) → (58; 63) → (75,5; 89) → (73; 92) → (13; 92) → (10; 89) → (10; 63)
```

A borda direita da grade segue a diagonal. A grade é a saída do alto-falante de 28 mm no eTuttiChorus e a ventilação no eTuttino.

## 6. Conexões (face esquerda, x = 0)

- **USB**: Micro-B de painel, centro em y ≈ 36, z ≈ 19,5. Ligado ao Teensy 4.0 por um cabo curto (~10 cm).
- **Fone**: jack 3,5 mm de painel, centro em y ≈ 56, z ≈ 19,5. Ligado à saída de fone da Audio Board.
- **Inserto**: os dois ficam num inserto preto impresso de ~36 × 11 mm, rente à parede.
- As placas não precisam encostar na parede.

## 7. Botões (capas)

- Um só modelo: domo baixo com saia.
  - topo convexo de Ø 15;
  - saia que abre até Ø 17 na base;
  - encaixe em cruz padrão MX.
- Altura tal que o topo fique em z = 26,5 com o switch montado (conferir a altura do Gateron usado).
- Três arquivos:

  | Arquivo | Cor (Seixo) | Cor (Madeira) | Detalhe |
  |---|---|---|---|
  | natural | branco | madrepérola | |
  | sustenido | preto | ébano | |
  | Dó e Fá | branco | madrepérola | xadrez diagonal em relevo no topo |

## 8. Fabricação

### Seixo

- Tampa e fundo em uma cor só, sem luz inferior nem peças decorativas.
- Fundo parafusado por baixo (conferir pontos de fixação na PCB).

### Madeira

- Carvalho branco (white oak); carvalho escuro como alternativa.
- Bloco bruto ~350 × 110 × 40 mm.
- Fresagem de 3 eixos de cima: contorno, abertura, chanfro, rebaixo da tela, furação, bolsão interno.
- Tampa de fundo fina.
- Sem filetes nem texturas aplicadas.

## 9. A conferir no modelo

1. Teensy 4.0 + Audio Board (pilha de 19,8 mm), módulo da tela, potenciômetro, encoder, LED, alto-falante de 28 mm (Chorus) e os dois conectores de painel cabem na área de interface. Ela tem ~68 mm no ponto mais estreito, na altura da fileira 2.
2. Altura dos eixos do potenciômetro e do encoder para os knobs ficarem baixos.
3. Folga das saias de 17 mm entre vizinhos (passo 19,05).
4. Espessura de parede para impressão e para CNC.

## 10. Entregáveis pedidos ao Claude Code

Em `etutti/hardware/case/`:

1. `case.py` paramétrico (CadQuery), com todas as medidas acima como parâmetros no topo do arquivo.
2. Exportar STEP e STL do Seixo (tampa e fundo) e da Madeira (corpo e tampa de fundo).
3. `keycap.py` com as três capas em STL, para imprimir o teste de quatro capas em quatro switches vizinhos.
4. Renders PNG (isométrico frente-esquerda, vista de cima, face esquerda) das duas versões.
5. `README.md` curto explicando os parâmetros e como regenerar os arquivos.
6. Opcional: atualizar a página `/etutti/models/` com os novos renders.
