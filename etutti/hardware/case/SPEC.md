# eTutti · case paramétrico (Seixo e Madeira) · v8

**Versão 8 — forma congelada desde a v7.** Substitui a v7, implementada nos PRs #86 e #87 (as versões anteriores continuam no histórico do git). Cada versão nova deste arquivo ganha um número e a seção "Mudanças desde a versão anterior". O resultado da verificação de cada versão fica no `FIT_CHECK.md`, com as "Perguntas para o design" no fim. Os desenhos de referência continuam em `canvas-v5/` (forma geral; as medidas desta SPEC prevalecem).

## Mudanças desde a versão anterior (v7)

Respostas às perguntas da PCB v0.6 no `FIT_CHECK.md` (PRs #86 e #87). **A forma externa continua congelada**; só mudam o fundo e o que vem depois.

1. **Pilares do fundo**: aprovados como estão no modelo, um no centro de cada triângulo de três teclas vizinhas (61) mais 3 sob a interface.
2. **Fixação da placa sob a interface**: **dois parafusos M2 por baixo**, pelo fundo, nos pilares (30; 60) e (12; 70), com furos correspondentes na placa principal. Sem espuma.
3. **Plate em FR-4 de 1,6 mm**, aceito: os botões ficam 0,1 mm mais altos (topo em z ≈ 26,6). Nada muda na caixa.
4. **Próxima etapa: a plaquinha de controles** (seção 10), e o firmware lendo o potenciômetro e o encoder.
5. **Manuais de montagem e figuras 3D**: refazer só depois do protótipo.

Especificação para o Claude Code gerar o modelo 3D do case do eTuttino, nas duas versões:

- **Seixo**: plástico, impressão em resina ou MJF, uma cor só.
- **Madeira**: carvalho branco (white oak), CNC de 3 eixos em duas fixações (a de cima e o bolsão interno por baixo), acabamento a óleo.

As duas versões têm exatamente a mesma geometria; só mudam o material e a fabricação. Os desenhos de referência estão em `canvas-v5/` (Seixo, Madeira, Botões sobre Gateron, Cores).

Medidas em mm. Tudo que estiver marcado **(conferir)** é estimativa do conceito e precisa ser confirmado com a peça real ou o datasheet.

## 1. Sistema de coordenadas

- **x**: da face esquerda (x = 0) para a direita, ao longo do comprimento.
- **y**: de trás (y = 0) para a frente (y = 100), onde fica quem toca.
- **z**: da mesa (z = 0) para cima.

Esse sistema é canhoto. Mantenha a convenção já usada no `case.py`: modelar em coordenadas da SPEC e espelhar na exportação (`y_arquivo = 100 − y_SPEC`).

## 2. Teclado C-griff (eTuttino, 44 teclas, G3–E6)

- Passo entre botões: `P = 18,5`, igual para os seis vizinhos (grade hexagonal, triângulos equiláteros). Diâmetro do botão: `D = 15` (raio 7,5).
- Distância entre fileiras: `P · cos 30° = 16,02`. O teclado fica centrado na largura (y = 50).
- Centros das fileiras em y:

  | Fileira | Posição | y |
  |---|---|---|
  | 1 | mais perto de quem toca | 74,03 |
  | 2 | | 58,01 |
  | 3 | | 41,99 |
  | 4 | | 25,97 |

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
- Botões das pontas da fileira 2: (94,75; 58,01) e (298,25; 58,01).

## 3. Área do teclado (abertura na tampa)

### Folgas

- Nas laterais: 1 botão (15 mm), medido perpendicular à borda dos botões. A folga segue as duas diagonais das fileiras, a 30° da vertical, formando "<" à esquerda e ">" à direita.
- Na frente e atrás: o que sobra com a caixa de 100 mm e a faixa de 10,3 mm, ~8,2 mm.

### Contorno da abertura

Hexágono derivado das folgas acima (o `case.py` calcula os vértices a partir de `P`):

- Os dois vértices laterais (na altura da fileira 2) são arredondados com R 22,5, concêntricos aos botões das pontas da fileira 2. Assim a folga fica igual em toda a volta.
- Os quatro cantos de 120° têm R 6.

### Chanfro

- Arredondado, de 4 mm em planta e 2 mm de queda, nas quatro bordas da abertura, no mesmo material e na mesma cor da tampa. Abaixo dele, a borda tem 2,7 mm de reto vertical, nas duas versões.
- Contorno externo do chanfro = abertura + 4 mm (vértices laterais R 26,5; cantos R 10).

### Dentro da abertura

- Placa preta de 1,5 mm com furos de 14 × 14 mm (padrão MX) nos centros dos botões.
- Switches Gateron magnéticos de carcaça escura.
- PCB com sensor Hall sob cada switch.

## 4. Caixa

### Contorno em planta

- **Largura**: 100 constante (y de 0 a 100).
- **Lado direito, frente e trás**: seguem a área do teclado a ~6 mm do chanfro externo, o que equivale à abertura + 10,3 mm. Vértice do lado direito com R 32,8, concêntrico ao botão da ponta direita da fileira 2; cantos com R 16,3.
- **Lado esquerdo**: reto em x = 0, cantos com R 16.
- **Comprimento total**: ~331,1 mm.

### Paredes e alturas

- Paredes externas verticais, a 90° da mesa, sem chanfro nem arredondamento de perfil.
- **Área do teclado**: tampa em z = 17,4 (4,7 mm sobre a borda da placa de switches). Topo dos botões em z = 26,5. Conferir que a saia, com a tecla apertada, não toca a tampa.
- **Área de interface** (à esquerda da área do teclado): bloco elevado.
  - **Plano** em z = 33 de y = 0 até y = 55, só sob a tela e os controles. O vinco em y = 55 deixa os controles centrados entre a tela e o vinco (folgas de ~5 mm).
  - De y = 55 até a borda da frente, **desce a 13°** e chega a z ≈ 22,6 em y = 100. A grade fica nesse plano inclinado, voltada para quem toca.
  - O vinco entre o plano e a parte a 13° é arredondado com R 10.
- **Transição** entre interface e teclado: rampa seguindo o mesmo "<".
  - **metade de trás** (de y = 0 até a fileira 2): segue a diagonal "<".
    - borda de cima: abertura + 12,7, com arco R 35,2 concêntrico ao botão da ponta esquerda da fileira 2;
    - borda de baixo: o chanfro externo (abertura + 4), arco R 26,5.
  - **metade da frente**: em vez de voltar pela diagonal, a rampa desce reta (paralela a y) até y = 86. Dali curva com R 14 por 75° e segue reta até a face da frente, chegando em x ≈ 47,4 (borda de cima) e x ≈ 56,1 (borda de baixo).
  - Isso deixa uma área de tampa plana, na altura do teclado, à esquerda da fileira 1, com espaço para a mão que toca os graves;
  - **as duas bordas da rampa arredondadas com R 5**, e nenhum canto vivo na interface do lado do teclado, para não machucar a mão que toca.

## 5. Área de interface, de trás para a frente

| Item | Posição / medidas |
|---|---|
| Zona da tela | x 8–62, y 5–35. Opções: rebaixo raso de 1,5 (conferir), tela rente, ou sem tela (eTuttino) com gravação ou adesivo |
| Tela | 1,9″ 320 × 170. Área visível ~43 × 23 centrada na zona (conferir datasheet do módulo) |
| Volume | potenciômetro contínuo, eixo em (20; 45), knob Ø 9 |
| Seletor de instrumento | encoder com clique e giro infinito, eixo em (37; 45), knob Ø 9 |
| LED | Ø 3,5 em (52; 45), à direita dos knobs. Seixo: furo. Madeira: furo com condutor de luz redondo de 3 mm (light pipe), ponta lixada rente |
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
  - saia que abre até Ø 16,5 na base (2 mm entre saias vizinhas, passo 18,5);
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
- Fresagem de 3 eixos em duas fixações: de cima (contorno, abertura, chanfro, rebaixo da tela, furação) e virada (bolsão interno).
- Borda da abertura com 2,7 mm de reto abaixo do chanfro, como no Seixo.
- LED: furo com condutor de luz redondo de 3 mm pronto (light pipe), ponta lixada rente à madeira.
- Tampa de fundo fina.
- Sem filetes nem texturas aplicadas.

## 9. A conferir no modelo

Premissas que continuam valendo (do `FIT_CHECK.md` da v5):

- Pilha Teensy + Audio Board: **~13 mm no eTuttino** (cabe, com até 16,9 mm no Seixo). **≤ 10 mm no eTuttiChorus** (com 13 mm o plugue micro-USB de 90° bate na tela).
- Potenciômetro, encoder e LED numa plaquinha presa por baixo da tampa (eixos L = 15).
- Plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura); conectores de painel com no máximo ~10 mm de corpo atrás do inserto.
- Fone de painel ligado por fio à Audio Board.
- Paredes: Seixo 2,5 mm; Madeira 4 mm (2,5 mm em volta do inserto) e tampa de 3 mm.
- PCB e placa de switches refeitas com fileiras a **16,02 mm** e passo 18,5 (etapa separada).

O que verificar nesta versão:

1. Furos M2 nos pilares (30; 60) e (12; 70): passagem pelo fundo, rebaixo para a cabeça do parafuso e furos na placa principal, longe de trilhas e componentes.
2. Plate de 1,6 mm: confirmar que a tampa e as saias continuam com folga.

## 10. Entregáveis pedidos ao Claude Code (v8)

1. **Fundo e placa principal**: os dois furos M2 da seção 9 (caixa: fundo com passagem e rebaixo; placa: furos de montagem). Regerar a PCB (DRC e conferência do firmware como sempre) e exportar o case.
2. **Plate**: espessura 1,6 mm (FR-4) no modelo e nos arquivos de fabricação.
3. **Plaquinha de controles**, como PCB própria:
   - potenciômetro RK09K (volume, contínuo), encoder EC11 com clique e botão (seletor de instrumento), ambos com eixo L = 15, nas posições (20; 45) e (37; 45);
   - LED de 3 mm vermelho/verde em (52; 45), num espaçador que leve a ponta até o furo da tampa (no Seixo; na Madeira, logo abaixo do light pipe);
   - conector JST PH de 8 vias, ligado por cabo ao J3 da placa principal;
   - presa por baixo da tampa da interface; conferir no `fit_check.py` contra a pilha, o USB e o jack de painel.
4. **Firmware**: ler o potenciômetro como volume e o encoder como seletor de instrumento (girar troca, clique confirma ou volta ao padrão), sem mudar o mapa de notas. Compilar e conferir.
5. `FIT_CHECK.md`: registrar a v8 e terminar com "Perguntas para o design".
