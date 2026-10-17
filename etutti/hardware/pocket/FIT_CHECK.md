# eTuttino Pocket · fit check (design)

**SPEC atendida: v2, tarefa D1** (lado esquerdo e área de interface). 17 out 2026.
D2 (modelo CadQuery do Seixo) fica para depois da escolha do J.

Página de revisão para o J: `/etutti/pocket/revisao/` (só português, noindex).

## 1. O que foi feito

- **`shape.py`** (novo, só stdlib): a geometria em planta do Pocket, reutilizável no D2.
  - Teclas, abertura, chanfro, rampa e as paredes da direita seguem as regras do eTuttino.
  - O lado esquerdo vem de `VARIANTS`, com quatro parâmetros: `band`, `nose`, `corner` e `bulge`.
    - `band` é a largura da faixa da interface, da borda de cima da rampa até a parede, perpendicular à face.
    - `nose` é o raio da ponta do "<". `None` quer dizer concêntrica com a ponta da rampa.
    - `corner` é o raio mínimo de todas as outras quinas.
    - `bulge` é a flecha das faces.
  - Todos os contornos são convexos. As quinas são arredondadas por abertura morfológica (erosão e depois dilatação), sem nenhum canto vivo.
  - O D2 deve construir as paredes a partir de `outline()` e a rampa a partir de `opening()`/`ramp_top()`.
- **`variants.py`** (novo): o estudo D1.
  - Para cada variante, posiciona a interface:
    - knobs e LED, com folgas de no mínimo 5;
    - a grade, com no mínimo 6 da rampa;
    - o logo.
  - Encaixa por baixo, conferindo planta e altura contra o teto real (tampa plana, rampa por dentro, deck e placa de cima):
    - o alto-falante e a caixa dele;
    - a bateria;
    - a pilha Teensy + Audio Board, com o plugue de 90°;
    - a plaquinha dos knobs, com o potenciômetro com chave;
    - o USB e o fone de painel.
  - Gera `build/variants.json`, os desenhos em `case/renders/` (SVG + PNG) e a página de revisão.
- **`layout.py`** reescrito.
  - Usa `shape.py` e grava no `pocket.json` a variante recomendada, marcada como provisória.
  - **Não gera mais o `POWER.md`** (a SPEC v2 passa o orçamento de energia para a eletrônica). O `POWER.md` ficou como estava.
  - Mantém `keys_for`, `outlines`, `O_ETUTTINO`, `WIDTH` e `D_BTN`, que o `landing_svgs.py` usa.
- `etutti/landing_svgs.py` rodou de novo: os desenhos da página inicial e da `/etutti/pocket/` seguem o contorno novo. O código dele não mudou.

## 2. Premissas (iguais nas três variantes)

| Item | Valor reservado | Origem |
|---|---|---|
| Altura do teclado | tampa 17,4, topo das teclas 26,6, placa 6,5–7,7 | eTuttino, **sem mudança** |
| Interface | plana a 33 até y = 55, depois 13° para a frente; tampa de 2,5 | eTuttino |
| Placa principal (borda esquerda) | abertura − 3 (19,5 do centro das teclas) e uma língua sob a pilha | **conferir com a eletrônica** |
| Bateria | célula 603450, 6 × 34 × 50 (conferir). Berço de 54 × 35 (+0,5 em volta, +3 para os fios), z de 2,0 a 9,0 (com 0,5 para inchar) | SPEC §6 |
| Alto-falante | redondo, o maior padrão que couber (Ø 20/23/28/30/36/40/45/50). Profundidade de 5,5 para o Ø 36 (conferir) | SPEC §5 |
| Pilha | Teensy 4.0 sobre Audio Board Rev D a 3 da placa; 13 da Audio Board ao topo do USB; USB do Teensy a z 23,7 | pilha montada do J (eTuttino) |
| USB / fone | plugue micro-B de 90° (11 × 11 × 7,5) no Teensy, cabo curto, USB de painel 10 × 10 × 8 e jack Ø 8 × 10 na face esquerda, centro a z 22,5 | eTuttino |
| Potenciômetro com chave | **corpo de 10 × 12,5 em planta e 13,0 de altura** acima da plaquinha (o RK09K tem 6,5). Plaquinha de 1,6 a z 15,6–17,2, pernas até 14,1 | estimativa (conferir) |
| Encoder | EC11E, 12,4 × 13,2 × 6,5. O eixo fica mais longo: ~16 acima do corpo, eixo de 20 | eTuttino |
| Knobs | Ø 9, 16 entre volume e seletor, LED Ø 3,5 a 12 à direita, linha em y = 49 | SPEC §4 |

O que define a largura da faixa **não são os knobs** (com eles, ~44 bastariam). É a pilha Teensy + Audio Board atrás, com o plugue de 90° em linha.

- A pilha mede 38 × 37. Com a face de trás inclinada a 30°, ela precisa:
  - ficar atrás da plaquinha dos knobs: a Audio Board pode passar por baixo dela (1,8 de folga), o Teensy e o jack da Audio Board não podem;
  - ficar longe da rampa o bastante para o topo do USB (z 23,7) passar sob o lado de dentro dela.
- Cada variante usa a menor faixa (em passos de 1 mm) em que tudo coube.

## 3. As três variantes

Os números saem de `python etutti/hardware/pocket/variants.py`. As folgas de knob e LED são medidas da borda do knob à parede e à borda de cima da rampa.

| | A · Chevron | **B · Seixo (recomendada)** | C · Arco |
|---|---|---|---|
| Forma | "<" de faces retas, ponta R 30, quinas R 18 | uma curva só, concêntrica com a ponta da rampa (R 89), quinas R 24 | faces curvas (flecha 6), ponta R 24, quinas R 22 |
| Faixa da interface | 51 | 54 | 47 |
| **Comprimento** | **257,2** | **251,5** | **257,0** |
| Menor que o eTuttino (331) | 73,8 | 79,5 | 74,0 |
| Origem O (x do xp = 0) | 104,14 | 98,45 | 103,99 |
| Knobs (vol / sel / LED), y = 49 | 18,8 / 34,8 / 46,8 | 15,1 / 31,1 / 43,1 | 18,8 / 34,8 / 46,8 |
| Knob → parede / LED → rampa (mín. 5) | 11,3 / 12,0 | 10,1 / 10,0 | 11,7 / 11,9 |
| Maior alto-falante que cabe | Ø 38,9 | Ø 38,9 | Ø 38,9 |
| **Alto-falante reservado** | Ø 36 × 5,5 em (32,9; 77,5) | Ø 36 × 5,5 em (26,9; 77,5) | Ø 36 × 5,5 em (32,9; 77,5) |
| Borda do alto-falante → parede / rampa | 4,5 / 11,8 | 4,5 / 12,1 | 4,5 / 11,7 |
| **Volume traseiro fechado** | 9,5 cm³ | 9,5 cm³ | 9,5 cm³ |
| Caixa traseira | Ø 39 (parede 1,5), do alto-falante até 10,2 (fundo da caixa sobre a bateria) | igual | igual |
| Grade | 64 furos Ø 1,9, só sobre o cone; 13,3 da rampa, 6,0 da parede | 64 furos; 13,6 da rampa | 64 furos; 13,2 da rampa |
| **Bateria** (centro, ângulo, sobra) | (44; 72), 15°, 0,2 | (39; 73), 7,5°, 0,7 | (44; 67), 0°, 3,2 |
| **Pilha** (canto USB/VIN da Audio Board, ângulo) | (42; 4), 30° | (35; 3), 30° | (31; 7), 0° |
| Topo do USB do Teensy → teto da rampa | 0,5 | 2,1 | 0,8 |
| Cabo do plugue até o USB de painel | ~12 | ~14 | ~14 |
| Altura do teclado | igual ao eTuttino | igual | igual |

Em todas as variantes:

- a bateria fica no fundo, debaixo da plaquinha dos knobs e do alto-falante, fora da placa principal. Sai tirando o fundo, sem abrir a tampa;
- a pilha fica atrás, sob o logo, numa língua da placa principal, com o plugue apontando para a face de trás-esquerda;
- o USB de painel fica ao lado do plugue, e o fone fica mais à frente na mesma face;
- o potenciômetro com chave ocupa de z 17,2 a 30,2, a 0,2 da tampa.

Renders em `etutti/hardware/pocket/case/renders/`:

- `d1_comparacao`: as três sobrepostas;
- `d1_<A|B|C>_cima`: vista de cima com o eTuttino tracejado atrás;
- `d1_<A|B|C>_dentro`: lado esquerdo sem a tampa.

Conferi cada PNG olhando. Conferi a página a 375 px de largura: `scrollWidth` = 375, sem rolagem horizontal, e a tabela cabe sem rolar.

## 4. Recomendação: B · Seixo

É a mais curta (251,5, cerca de 5,5 a menos que A e C) e tem a cara do nome do case.

- O lado esquerdo é uma curva só, concêntrica com a ponta da rampa. A faixa da interface tem a mesma largura em todo o contorno, como pede a SPEC, e logo, knobs e grade ficam alinhados a ela.
- Não há quina: a curva encontra as faces de trás e da frente com raios grandes (R 24).
- Custo: o USB e o fone saem numa parede curva. O D2 precisa de um ressalto plano por dentro (ou um inserto) para os conectores de painel.

## 5. Mudanças de contrato no `pocket.json` (para a eletrônica)

O `pocket.json` agora é a variante B, com `"provisional": true`, `"variant": "B"` e `"variant_params"`. As chaves que o `landing_svgs.py` lê continuam: `keys`, `opening`, `box`, `length`, `controls.volume/select/led/grille`. O `controls.grille` agora é o **retângulo envolvente** da grade.

O que mudou e o que é novo:

- **`origin`** passou de 84 para **98,45**: as teclas andaram 14,45 para a direita. **O comprimento passou de 237,1 para 251,5.** `rows` (a grade da firmware) **não mudou**.
- Saiu a chave `power`, porque o orçamento de energia agora é da eletrônica.
- Chaves novas:
  - `heights`: as alturas do eTuttino que valem para o Pocket.
  - `chamfer`, `ramp` e `inner`: contornos da abertura + 4, da borda de cima da rampa e de dentro da parede.
  - `controls.grille_outline`, `holes` e `logo`: a grade de verdade, os furos e a área do logo.
  - `controls_board`: retângulo e z da plaquinha, do potenciômetro com chave (altura reservada de 13,0) e do encoder.
  - `speaker`: centro, Ø 36, profundidade, z da face, caixa e volume traseiro.
  - `battery`: retângulo do berço, ângulo e z de 2 a 9.
  - `stack`: Audio Board, Teensy, jack da Audio Board, plugue de 90°, ângulo e z.
  - `panel`: USB e fone de painel (posição na parede, normal e z).
  - `main_board.keys` e `main_board.tongue`: onde a placa principal pode ficar. **A bateria não fica sob ela.**
- O `pcb_envelope.json` do Pocket ainda não existe e sai no D2.

## Perguntas para a gestão

1. **Escolha da variante:** recomendo a B (Seixo, 251,5 mm). A A e a C ficam com ~257 mm. O J escolhe na página `/etutti/pocket/revisao/`.
2. **O "<" custa comprimento:** o Pocket passou de 237 (v1, face esquerda reta) para 251,5 (B).
   - Quem manda é a pilha Teensy + Audio Board atrás, com o plugue de 90° e os conectores de painel, e não os knobs.
   - Se a eletrônica puder usar uma pilha mais baixa (Teensy soldado direto na Audio Board, ~10 mm em vez de 13) ou um plugue mais curto, a faixa encolhe alguns milímetros. Vale pedir isso à eletrônica?
3. **Potenciômetro com chave:** reservei 13,0 mm de corpo. Para isso, a plaquinha dos knobs desceu para z 15,6–17,2 e o encoder precisa de um eixo de 20.
   - A eletrônica confirma a peça e a altura?
   - Se for mais baixo, sobra folga sobre a Audio Board, mas o comprimento não muda.
4. **Borda da placa principal:** supus que a placa pode acabar 19,5 mm do centro das teclas da esquerda (abertura − 3), com uma língua até a pilha, para a bateria ficar ao lado e não embaixo. A eletrônica aceita, com os 2 multiplexadores atrás da fileira 4?
5. **Alto-falante:** em todas cabe um redondo de Ø 38,9. Reservei Ø 36 × 5,5 com 9,5 cm³ fechados atrás.
   - O volume é pequeno porque a caixa apoia sobre a bateria.
   - Se a eletrônica escolher um alto-falante que peça mais volume, a caixa pode crescer para os lados no D2.
   - Ou serve um retangular, tipo 20 × 30?
6. **Linha dos knobs em y = 49** (no eTuttino é 45). Avancei para dar lugar à pilha atrás; o knob ainda fica na parte plana. Algum problema?
7. **Página inicial:** o `landing_svgs.py` desenha a grade como retângulo (`controls.grille`). Agora há `controls.grille_outline` (o desenho de verdade, quase redondo). Pedir à programação e som para usar o contorno?
