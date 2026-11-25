# eTutti Slim · FIT_CHECK (SPEC R10SL, sessão A2)

Resposta à **SPEC R10SL §8.3**. Detalhes: [ELETRONICA.md](ELETRONICA.md) e [ROTEAMENTO.md](ROTEAMENTO.md) (últimas seções), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) ("Resumo dos limitantes", R27, R28, R44–R46, R51, R63). **Parado. A sessão B (BGA) não foi tocada; nada cotado ou comprado.**

## 1. Resumo

| Parte | Resultado |
|---|---|
| Fixação | direita inalterada (2 × M2, 4,5 da ponta, v = ±3,6); **cauda: 2 × M2 em u = 6,7, v = ±4,2**; régua **171,3 mm** (+3,8 à esquerda), grade **168,6 mm** e alcança a cauda; ordem J1 → M2 → U9/C9/C10 → tecla 1 cumprida |
| Um M2 em v = 0 na cauda | cabe (cresce só 2,4 mm; C9 a 0,15 da porca): ver pergunta 1 |
| Folgas | ponta esquerda → principal 5,5 / 5,8 mm (FFC de 20 mm alcança nas 4 fileiras); → parede esquerda 70,9 / 61,7 mm; → baia 33,8 / 24,5 mm; régua → parede direita **1,75 mm** (fileiras 1 e 3) e 11,0 (2 e 4) |
| Rota da régua | DRC **0/0**, não ligados **0**, paridade **0**, 98 vias; ERC 0/0 (principal e régua); Gerbers da grade conferidos (DRC 0/0) |
| Principal | faixa e abas recuaram 3,8 mm, posicionamento refeito: DRC sem trilhas 0/0, paridade 0; `check_placa` 21/21 |
| Case | 248,0 × 89,1; base com os bolsos dos trilhos para as porcas da cauda (R63); apoio contínuo conferido nas 4 fileiras |
| Limitantes | seção nova em `RESTRICOES_CASE.md`: 10 cotas; as 3 que mais limitam: **direita (1,75 mm)**, **divisão base/tampo (0,2 mm no P2)** e **esquerda (0,3 mm da faixa à baia)** |

## 2. Imagens geradas ou atualizadas nesta sessão

| Caminho | Legenda |
|---|---|
| `pcb/regua/img/planta_regua.png` (+ `.svg`) | planta cotada da régua (171,3 × 15,0), das 4 fileiras com a nota em cada tecla, da grade (168,6 × 16,0) e do painel; títulos e cotas saem agora das variáveis |
| `pcb/regua/img/regua_frente.png` | régua roteada, lado das teclas (GND, furos), com as notas |
| `pcb/regua/img/regua_verso.png` | régua roteada, lado das peças (vista de baixo) |
| `pcb/regua/img/regua_cabeca_verso.png` | detalhe da cabeça: J1, os 2 M2 da cauda, U9, C9, C10 e o 1º sensor |
| `pcb/regua/img/grade.png` | grade 168,6 × 16,0, 8 furos 14,00 com dog-bone e 4 M2 sem escareado (título das variáveis) |
| `pcb/principal/img/planta_principal.png` | planta da principal (faixa 3,8 mm mais curta, pilares movidos) |
| `case/img/planta_teclado.png` | planta do teclado com o nome das notas, case de 248,0 |
| `case/img/knobs_s123.png` | S1/S2/S3 dos knobs (regerada com o modelo atual) |
| `case/renders/cena_iso.png` | cena 3D das 4 réguas, grades, switches e case (isométrica) |
| `case/renders/corte_tecla.png` / `corte_tecla_4fileiras.png` | corte por uma tecla e pelas 4 fileiras |
| `case/renders/corte_cauda.png` | corte da cauda da régua com a grade |
| `case/renders/corte_longitudinal.png` | corte longitudinal de uma fileira |
| `case/renders/corte_apoio_4fileiras.png` | prova do apoio contínuo, 1 corte por fileira |
| `case/renders/cena_principal_baixo.png` / `cena_principal_iso.png` | principal vista de baixo e isométrica com o case |
| `case/renders/corte_principal_registros.png` / `corte_principal_volume.png` / `corte_principal_longitudinal.png` | cortes da principal sob os knobs e no comprimento |

## 3. Desvios da R10SL

1. O par da cauda ficou a **8,4 mm (v = ±4,2)**, não 7,2: com 7,2 o corredor J1 → U9 tinha 2,6 mm entre as porcas e a rota não fechava.
2. O furo da cauda está a **6,7 mm da ponta**, não 4,5 (o espelho exato da direita): a porca bateria no pátio de J1.
3. A principal teve de perder **3,8 mm de faixa** (e os dois pilares da direita recuaram): é o preço de manter o vão do FFC; a sessão B precisa partir desta placa.

## Perguntas para o design

1. **Par ou um parafuso só na cauda?** *Problema:* 4 pontos de fixação numa régua de 171,3 mm de FR‑4 são hiperestáticos: o comprimento entre as duas pontas tem tolerância (furo ±0,1 em cada ponta, mais a variação do material); se não houver folga, ela trava ou empena. *Números:* o par custa **3,8 mm** de crescimento à esquerda (e 3,8 mm de faixa da principal); um M2 em v = 0 custa **2,4 mm**, deixa C9 a 0,15 mm da porca (apertado) e torna a fixação isostática (3 pontos). *Opções:* (a) manter o par e fazer o furo da cauda **oblongo** (2,2 × 3,2 ao longo da régua) para absorver a tolerância; (b) trocar por 1 × M2 em v = 0; (c) manter o par redondo e ensaiar no protótipo. *Recomendo (a); (b) se a faixa da principal apertar.*
2. **A faixa da principal ficou 3,8 mm mais curta (de 22,2 para 18,4 mm).** *Problema:* a régua mais longa à esquerda invade a faixa, e o vão do FFC (5,5/5,8) não pode diminuir (a curva da fileira 4 perderia o raio de 3,1). *Números:* o posicionamento ainda fecha (DRC 0/0, paridade 0), mas sobra menos espaço para a sessão B (BGA). *Opções:* (a) aceitar a faixa de 18,4; (b) o um‑M2 de v = 0 devolve 1,4 mm; (c) um S mais suave com vão maior devolve até ~2 mm ao custo de raio.
3. **Folga da régua à parede direita: 1,75 mm** (mínimo 1,5). *Opções:* aceitar (MJF ±0,3), ou encurtar a ponta direita em 1 mm (furo em u = 165,8: 2,85 mm do furo à carcaça da tecla 8, margem 2,75 da parede).
