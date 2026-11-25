# eTutti Slim · FIT_CHECK (SPEC R6SL, fim da Etapa 2)

Resposta à **SPEC R6SL §8**. Relatórios: [ELETRONICA.md](ELETRONICA.md) (última seção), [POSICIONAMENTO.md](POSICIONAMENTO.md), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (62 itens), [FIRMWARE.md](FIRMWARE.md), `estudos/botao/`. **Etapa 2 fechada; parado à espera do J. Nada cotado, comprado ou amostrado; sem rotas.**

## 1. Resumo da R6SL

| Parte | Resultado |
|---|---|
| **Botão baixo** | cabeça Ø15 × 3,8 (lateral reta 1,6, borda em quarto de elipse 1,3 × 1,15, domo esférico R≈18,4); haste Ø10 × 5,85, pino Ø5,4, furo Ø11 e folga 2,0 inalterados; **STEP** `estudos/botao/botao.step` (branco/preto, liso) e `botao_textura.step` (C/F) |
| Alturas (tampo real) | topo em repouso **24,0 / 26,0 / 28,0 / 31,0**; apertado 20,5 / 22,5 / 24,5 / 27,5; **folga no fim do curso 2,00 / 2,00 / 2,00 / 2,07**; **altura do instrumento 31,0** (era 34,7); cortes em `estudos/botao/botao_cortes_4fileiras.png` |
| Pontilhado de C e F | quadrados 0,5 mm, fundo 0,18, grade a 45°, passo 1,1, dentro de Ø11 no domo, **como pedido** (modelo válido, ~80 quadrados por botão). **SLA:** entalhes de 0,4–0,5 mm × 0,18 estão no limite do que as resinas gravam bem (laser ~0,14, camada 0,05) e retêm resina na lavagem; a SLA reproduz, mas o domo faz o fundo plano de cada quadrado ficar inclinado: **o ensaio dos 4 botões decide**; se falhar, quadrados de 0,6 × 0,25 |
| FFC | **20 mm, os 4 iguais.** Não achei folha do cabo (é sob medida) nem raio mínimo estático para 1,0 mm × 0,3 mm; mantive a regra 10 × T = 3,0. **Fileira 4: R 2,89 → 3,10** encurtando 0,3 mm a faixa da principal (vão 5,8 nas fileiras 2 e 4); R 3,27 / 8,66 / 7,81 / 3,10 |
| Bateria BAK 1S-3 | pico estimado **~325 mA** na bateria (250 mA a 3,3 V) contra 475 mA: **fica como reserva**; carga 0,43 C; cabe na baia 36 × 60 |
| LED do anel | **EKINGLUX E6C0805RYGC2UDA-A21 (C375546)**, 0805 vermelho/verde-amarelo, face de cima, soldado em casa; pinos **13 (R) e 5 (G)** (os mesmos) |
| Placa principal | DRC sem trilhas **0/0**, paridade **0**, ERC **0/0**; `check_placa.py` **21/21**; 120 peças |
| Planta do teclado | `case/img/planta_teclado.png` (nomes, pontilhado em C e F) |

## 2. O que muda o lado de fora

Botões Ø15 × 3,8: **altura total 31,0** (R57/R58). A planta (247,0 × 89,1) é a mesma; a faixa interna da placa ficou 0,3 mm mais curta.

## 3. Desvios da R6SL

1. O verde do LED é **verde-amarelo** (568 nm): o 0805 bicolor de pads independentes mais simples; o de verde puro achado (C965845) é ânodo comum e inverteria o firmware.
2. **Sem STEP** do LED (caixa na cena 3D) e sem folha do cabo FFC.
3. O pontilhado de 0,18 mm está no limite da SLA (ver acima).

## Perguntas para o design

1. **LED:** serve o verde-amarelo (laranja com os dois), ou prefere o verde puro em ânodo comum, mudando a polaridade do firmware?
2. **FFC:** aceita a faixa da principal 0,3 mm mais curta (vão 5,8 nas fileiras 2 e 4) para a fileira 4 chegar a R 3,1, ou prefere manter 5,5 com R 2,9?
3. **Pontilhado:** o ensaio dos 4 botões testa 0,5 × 0,18 e 0,6 × 0,25; algum outro tamanho?
