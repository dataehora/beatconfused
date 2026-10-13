# eTutti · case paramétrico (Seixo e Madeira) · v5

**Esta é a versão mais recente da especificação e substitui o `SPEC.md` (v4).** O `SPEC.md` fica no repositório como histórico do que foi implementado no PR #81. Os desenhos desta versão estão em `canvas-v5/`.

## Mudanças desde a v4 (`SPEC.md`)

1. **Interface plana + 13°** (seção 4): plana a z = 33 só sob a tela e os controles, até y = 55; dali desce a 13° até a borda da frente (z ≈ 22,6). Antes era um plano único inclinado ~3° (33 → 28).
2. **Rampa entre interface e teclado** (seção 4): a borda de cima passa a ser abertura + 12,7 (era "+ 20,3", com o vértice errado). Na metade da frente a rampa desce reta e curva para a borda (R 14) em vez de voltar pela diagonal. Bordas arredondadas com R 5.
3. **Controles** (seção 5): da esquerda para a direita, volume (20; 45), seletor (37; 45) e LED (52; 45).
4. **Zona da tela** (seção 5): x 8–62 (era 10–64).
5. **Grade** (seção 5): retângulo x 8–53, y 61–94, no plano a 13°, com 6 mm de folga do vinco, da rampa e da borda. Não invade mais a rampa.
6. **Dó e Fá** com xadrez diagonal em relevo (eram só os Dós, com ranhuras).
7. **Madeira**: carvalho branco (white oak); CNC em **duas** fixações (correção do FIT_CHECK).
8. **Seção 9** atualizada com as conclusões do `FIT_CHECK.md` (pilha baixa, plaquinha de controles, plugue USB de 90°).


Especificação para o Claude Code gerar o modelo 3D do case do eTuttino, nas duas versões:

- **Seixo**: plástico, impressão em resina ou MJF, uma cor só.
- **Madeira**: carvalho branco (white oak), CNC de 3 eixos em duas fixações (a de cima e o bolsão interno por baixo), acabamento a óleo.

As duas versões têm exatamente a mesma geometria; só mudam o material e a fabricação. Os desenhos de referência estão em `canvas-v5/` (Seixo v5, Madeira v5, Botões sobre Gateron, Cores).

Medidas em mm. Tudo que estiver marcado **(conferir)** é estimativa do conceito e precisa ser confirmado com a peça real ou o datasheet.

## 1. Sistema de coordenadas

- **x**: da face esquerda (x = 0) para a direita, ao longo do comprimento.
- **y**: de trás (y = 0) para a frente (y = 100), onde fica quem toca.
- **z**: da mesa (z = 0) para cima.

Esse sistema é canhoto. Mantenha a convenção já usada no `case.py`: modelar em coordenadas da SPEC e espelhar na exportação (`y_arquivo = 100 − y_SPEC`).

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
- **Área de interface** (à esquerda da área do teclado): bloco elevado.
  - **Plano** em z = 33 de y = 0 até y = 55, só sob a tela e os controles. O vinco em y = 55 deixa os controles centrados entre a tela e o vinco (folgas de ~5 mm).
  - De y = 55 até a borda da frente, **desce a 13°** e chega a z ≈ 22,6 em y = 100. A grade fica nesse plano inclinado, voltada para quem toca.
  - O vinco entre o plano e a parte a 13° é arredondado.
- **Transição** entre interface e teclado: rampa seguindo o mesmo "<".
  - **metade de trás** (y de 0 a 58,3): segue a diagonal "<".
    - borda de cima: abertura + 12,7, com arco R 35,2 concêntrico ao botão da ponta da fileira 2 (94,475; 58,3);
    - borda de baixo: o chanfro externo (abertura + 4), arco R 26,5.
  - **metade da frente**: em vez de voltar pela diagonal, a rampa desce reta (borda de cima em x ≈ 59,3; borda de baixo em x ≈ 68,0) até y = 86. Dali curva com R 14 até a borda da frente, chegando em x ≈ 45,3 (cima) e x ≈ 54,0 (baixo).
  - Isso deixa uma área de tampa plana, na altura do teclado, à esquerda da fileira 1, com espaço para a mão que toca os graves;
  - **as duas bordas da rampa arredondadas com R 5**, e nenhum canto vivo na interface do lado do teclado, para não machucar a mão que toca.

## 5. Área de interface, de trás para a frente

| Item | Posição / medidas |
|---|---|
| Zona da tela | x 8–62, y 5–35. Opções: rebaixo raso de 1,5 (conferir), tela rente, ou sem tela (eTuttino) com gravação ou adesivo |
| Tela | 1,9″ 320 × 170. Área visível ~43 × 23 centrada na zona (conferir datasheet do módulo) |
| Volume | potenciômetro contínuo, eixo em (20; 45), knob Ø 9 |
| Seletor de instrumento | encoder com clique e giro infinito, eixo em (37; 45), knob Ø 9 |
| LED | Ø 3,5 em (52; 45), à direita dos knobs. Na Madeira, LED "fantasma": parede de madeira < 1 mm por cima |
| Grade | furos Ø 1,9 a passo de 4 |

Contorno da grade:

Retângulo de x 8 a 53 e y 61 a 94, com cantos R 3. O canto da frente à direita tem R 8, concêntrico à curva da rampa.

A grade fica toda no plano a 13°, com folga de 6 mm do vinco, da rampa e da borda da frente. A borda esquerda fica alinhada com a da tela, em x = 8. A grade é a saída do alto-falante de 28 mm no eTuttiChorus e a ventilação no eTuttino.

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

Premissas que vêm do `FIT_CHECK.md` (v4) e continuam valendo:

- Pilha baixa: Teensy soldado direto na Audio Board, ~11,3 mm.
- Potenciômetro, encoder e LED numa plaquinha presa por baixo da tampa, com eixos de L = 15.
- Plugue micro-USB de 90° no cabo até o USB de painel; conectores de painel com no máximo ~10 mm de corpo atrás do inserto.
- Fone de painel ligado por fio à Audio Board.
- Paredes: Seixo 2,5 mm; Madeira 4 mm (2,5 mm em volta do inserto) e tampa de 3 mm.
- PCB e placa de switches refeitas na grade de 16,5 mm entre fileiras (etapa separada).

O que precisa ser verificado de novo, porque a geometria mudou:

1. Rodar o `fit_check.py` contra a v5. A rampa agora desce reta na metade da frente, então a interface fica mais estreita na frente (borda de cima em x ≈ 45–59 em vez de ~81). Conferir se a pilha baixa, o alto-falante de 28 mm (Chorus) e os conectores continuam cabendo, e se a eletrônica pode avançar por baixo da rampa e da área livre de tampa à esquerda da fileira 1.
2. Teto interno sob o plano de 13° (z cai para ~22,6 na frente) contra a pilha e o alto-falante.
3. Folga das saias de 17 mm (passo 19,05) com o Gateron KS-20 real, usando o `keycap_test_4.stl`.
4. LED fantasma na Madeira: testar numa sobra se a pele de 0,8 mm deixa a luz passar.

## 10. Entregáveis pedidos ao Claude Code (v5)

Em `etutti/hardware/case/`, atualizando os arquivos que já existem (não criar outros do zero):

1. `case.py`: aplicar as mudanças da v5, mantendo todos os parâmetros no topo.
2. `fit_check.py` e `FIT_CHECK.md`: rodar de novo contra a v5 (seção 9) e registrar o resultado.
3. `keycap.py`: marcação de Dó e Fá com xadrez diagonal.
4. Reexportar STEP e STL (Seixo: tampa e fundo; Madeira: corpo e tampa de fundo; inserto; placa de switches) e regerar os renders.
5. `README.md`: apontar para a `SPEC-v5.md` como versão atual.
