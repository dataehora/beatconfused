# eTutti Slim · FIT_CHECK (SPEC R11SL, sessão A3)

Resposta à **SPEC R11SL §8.4** (substitui a fixação da A2). Detalhes: [ELETRONICA.md](ELETRONICA.md) e [ROTEAMENTO.md](ROTEAMENTO.md) (últimas seções), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (R27, R28, R29, R35, R44–R46, R51, R63, R64 e o "Resumo dos limitantes"). **Parado. A sessão B (BGA) não foi tocada; nada cotado ou comprado.**

## 1. Resumo

| Parte | Resultado |
|---|---|
| Fixação | **1 × M2 no eixo (v = 0) em cada ponta**: esquerda u = 13,1 (**redondo**), direita u = 161,9 (**oblongo 3,2 × 2,2 ao longo da régua**); ordem J1 → U9/C9/C10 → M2 → tecla 1; o par da direita e o par da cauda saíram |
| Régua | **164,9 mm** (R9SL 167,5; R10SL 171,3); ponta em balanço 13,1 mm (J1 a 10,9); flecha com 5 N no J1 **0,05 mm** (estimativa); FFC de 20 mm alcança nas 4 fileiras (raios 3,27 / 8,66 / 7,81 / 3,10); **grade presa pelos dois M2** (u 10,1…164,9) |
| Base | os trilhos terminam exatamente nos dois M2; em cada um uma guia centrada Ø6,0 com o bolso sextavado da porca: ok nas 4 fileiras; apoio contínuo conferido entre os M2 |
| Principal | faixa **20,7 mm** (era 18,4; devolveu 2,3); DRC sem trilhas 0/0, paridade 0; `check_placa` 21/21 |
| Rota da régua | DRC **0/0**, não ligados **0**, paridade **0**, 98 vias; ERC 0/0 (principal e régua); grade DRC 0/0, Gerbers conferidos (o oblongo sai como rasgo no arquivo de furação) |
| Folgas | régua → parede direita **5,85 mm** (fileiras 1 e 3) / 15,1 (2 e 4); ponta esquerda → principal 5,5 / 5,8; → parede esquerda 73,3 / 64,0; → baia 36,1 / 26,8 |
| Montagem | 7 passos, 21 imagens, base em STEP e conjunto em GLB (ver §2 e §4) |

## 2. Sequência de montagem (ordem proposta e justificativa)

1. **Base vazia com as 8 porcas nos bolsos** das guias (uma por M2): as porcas só entram por cima e antes de tudo.
2. **Bateria na baia e depois a principal nos 5 pilares** (plugue JST da bateria, M2 autoatarraxantes): a principal entra antes das réguas porque os conectores FFC (J601–J604) ficam na face de baixo da placa, com a boca para +x, e o cabo é encaixado neles com a régua ainda fora; se as réguas entrassem antes, a ponta do cabo teria de ser empurrada no conector por baixo da aba da placa. A bateria vai antes da placa porque a placa cobre parte da baia.
3. a 6. **Cada régua, fileira 1 a 4, com o cabo de 20 mm já ligado ao seu J1**; o outro extremo do cabo é encaixado na principal e a régua desce nas guias e trilhos e é parafusada **junto com a grade** (M2 × 6: cabeça, grade, espaçador de 1,3, régua, porca no bolso). A fileira 1 (mais baixa) primeiro: as seguintes ficam mais altas e não atrapalham o acesso.
7. **As 32 switches KS‑33D** encaixam de cima na grade e na régua e fecham o conjunto (os 32 nomes de nota aparecem).

Cada passo tem o isométrico e dois detalhes (esquerda e direita). **Modelos usados:** KS‑33D (STEP da Gateron), conector FFC C3250113, TMAG5253, 74HC595 e capacitores (STEP do EasyEDA e biblioteca do KiCad), a principal com 97 peças reais e VARTA 523450 (STEP do fabricante). **Faltam modelos realistas (aviso):** (a) o **cabo FFC de 20 mm** (é sob medida: está desenhado como fita 0,3 × 4,5 mm no comprimento certo); (b) **parafuso M2 × 6, porca M2 e espaçador de 1,3** (desenhados pelas dimensões da norma, sem STEP do fabricante); (c) na principal ficaram em **caixa**: D101, D102, D201, D401 (LED 0805), FB301, J202 (JST SH 3 vias), L101, L102, Q201–Q209, SW403, U102 (MKL02), U103 (flash), U201, U302, Y102. Entregues: `case/montagem/base.step` (a base) e `case/montagem/conjunto.glb` (conjunto montado com as 32 switches; partes pesadas simplificadas em 25 %).

## 3. Imagens geradas ou atualizadas nesta sessão

| Caminho | Legenda |
|---|---|
| `case/renders/montagem_p1_iso.png` / `_esq` / `_dir` | passo 1: a base com as porcas nos bolsos; detalhe das guias esquerda e direita da fileira 1 |
| `case/renders/montagem_p2_iso.png` / `_esq` / `_dir` | passo 2: bateria e principal; detalhes da faixa com os conectores FFC e da baia |
| `case/renders/montagem_p3_iso.png` / `_esq` / `_dir` | passo 3: régua da fileira 1 com cabo e grade; detalhes da ponta esquerda (cabo, guia, balanço) e da direita (M2 oblongo) |
| `case/renders/montagem_p4_*.png` (iso, esq, dir) | passo 4: régua da fileira 2 |
| `case/renders/montagem_p5_*.png` (iso, esq, dir) | passo 5: régua da fileira 3 |
| `case/renders/montagem_p6_*.png` (iso, esq, dir) | passo 6: régua da fileira 4 |
| `case/renders/montagem_p7_iso.png` / `_esq` / `_dir` | passo 7: as 32 switches, com o nome das notas |
| `pcb/regua/img/planta_regua.png` (+ `.svg`) | planta cotada da régua (164,9 × 15,0), das 4 fileiras com as notas, da grade (154,8 × 16,0) e do painel |
| `pcb/regua/img/regua_frente.png` / `regua_verso.png` | régua roteada, lado das teclas e lado das peças, com as notas |
| `pcb/regua/img/regua_cabeca_verso.png` | detalhe da cabeça: J1, U9, C9, C10, o furo do M2 e o 1º sensor |
| `pcb/regua/img/grade.png` | grade 154,8 × 16,0: 8 furos 14,00 com dog‑bone, M2 redondo e oblongo |
| `pcb/principal/img/planta_principal.png` | planta da principal (faixa 20,7 mm; título corrigido para "SPEC R11SL") |
| `case/img/planta_teclado.png` | planta do teclado com os nomes das notas |
| `case/img/knobs_s123.png` | S1/S2/S3 dos knobs (regerada) |
| `case/renders/cena_iso.png` / `corte_tecla.png` / `corte_tecla_4fileiras.png` / `corte_cauda.png` / `corte_longitudinal.png` | cena 3D das 4 réguas e cortes (regerados com a nova fixação) |
| `case/renders/corte_apoio_4fileiras.png` | apoio contínuo entre os M2, uma fileira por corte |
| `case/renders/cena_principal_baixo.png` / `cena_principal_iso.png` / `corte_principal_registros.png` / `corte_principal_volume.png` / `corte_principal_longitudinal.png` | principal e cortes sob os knobs (regerados) |

## 4. Desvios da R11SL

1. A ponta esquerda cresceu **1,5 mm**, não "o mínimo": com 0,5 e 1,0 mm J1 e U9 ficam tão perto que a rota não fecha (ver ROTEAMENTO.md).
2. As guias têm parede de **0,7 mm** em volta do bolso da porca (Ø6,0 para caber ao lado de U9): é o mínimo do MJF.
3. O cabo FFC, o M2, a porca e o espaçador da montagem não têm modelo do fabricante (ver §2).

## Perguntas para o design

1. **Faixa da principal: 20,7 mm (A2, pergunta 2).** *Problema:* a régua precisa de 1,5 mm de cauda a mais, e o vão do FFC (5,5/5,8) não pode diminuir. *Números:* a faixa foi de 22,2 (R9SL) a 18,4 (R10SL) e voltou a **20,7**; o posicionamento fecha (DRC 0/0, paridade 0). Para a sessão B (BGA) sobram 20,7 mm entre a baia (x −58,8) e a ponta da régua. *Opções:* (a) aceitar 20,7 (recomendo); (b) devolver até 1 mm só trocando a ordem das peças da cauda (U9 depois do M2 não cabe ao lado da tecla 1): não há ganho sem mudar o esquema.
2. **Folga à parede direita (A2, pergunta 3): agora 5,85 mm** (fileiras 1 e 3), 15,1 (2 e 4). *Problema:* o case está em 248,0 por causa da régua antiga; com a régua de 164,9 mm sobra folga. *Opções:* (a) manter 248,0 (nada a refazer); (b) voltar o case a ~**243,9** (folga de 1,75 mm), 4,1 mm mais curto: base, tampo e planta se refazem (muda o exterior); (c) uma folga intermediária (ex.: 245,5 com 3,35 mm).
3. **Guia com parede de 0,7 mm.** *Problema:* a guia Ø6,0 (porca de 4,6 entre cantos) deixa 0,7 mm de parede no MJF PA12; U9 está a 0,15 mm da guia, então não cresce. *Opções:* (a) aceitar 0,7 mm; (b) bolso da porca com 4,4 entre cantos (porca M2 de 4,0 entre faces tem 4,62 entre cantos: não cabe); (c) mudar a porca para a de flange ou usar inserto de latão de 3,5 mm de diâmetro (muda a lista de compra).
4. **Cabo FFC de 20 mm forma uma barriga de 5,5 a 5,8 mm no vão.** *Problema:* o S só gasta 5,6 a 7,5 mm de cabo; sobram ~6 mm. *Números:* a barriga da fileira 1 sobe até z ≈ 10,5 (a principal está em 8,0 e o tampo, ≥ 12,5, fica a ~2 mm); nas outras fileiras sobra mais; um cabo sob medida de **15 mm** deixa a barriga em ~1 mm. *Opções:* (a) 20 mm (como está); (b) 15 mm (menos folga para o encaixe e a troca); (c) 30 mm só se o vão crescer.
5. **Modelos que faltam para a montagem.** Fornecer os STEP do cabo FFC, de M2 × 6 / porca / espaçador e, se quiser, das peças em caixa da principal (MKL02, flash, JST SH 3 vias, SOT‑23, cristal) ou aceitar as caixas nos passos 2 a 7.
