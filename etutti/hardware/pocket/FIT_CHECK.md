# eTuttino Pocket · fit check (design)

**SPEC atendida: v4, tarefas F1** (acabamento e fechamento do case, Seixo variante B) **e M1** (manual de montagem, §12). 18 out 2026.
O D2 (SPEC v3, o modelo) e o D1 (SPEC v2, as variantes) estão no histórico do git.

Página de revisão para o J: `/etutti/pocket/revisao/` (só português, noindex).

**Resultado: nenhuma divergência aberta contra o `pcb/PECAS.json` v3 (F2).** Zero colisões entre peças e case, entre peças e
entre as peças do case; 0 arestas abertas nos 9 STL; raios livres em 140/140 (teclas), 73/73 (grade), 3/3 (knobs e LED) e
10/10 (janelas do USB-C e do fone). Flexão da placa: 0,029 mm a 3 N (limite 0,05).

## 1. O que foi feito

Tudo em `etutti/hardware/pocket/case/` (CadQuery, venv `C:/Users/julia/.venvs/cadquery`). Ordem de rodar:

1. `case.py`: o modelo e as exportações em `case/out/` (STEP + STL, espelhados: `y_arquivo = 100 − y_SPEC`), agora com as capas.
2. `fit_check.py`: cada peça do `PECAS.json` contra o case e contra as outras, as peças do case entre si, volume da caixa,
   exportações (arestas abertas, raios), peso por material. Escreve `out/fit_check.json` e `renders/fit_*.png`.
3. `pcb_envelope.py`: `out/pcb_envelope.json` (contrato com a eletrônica) e `renders/pcb_envelope.png`.
4. `mechanics.py`: flexão da placa, `out/board_sag.json`.
5. `render.py`: `renders/seixo_*.png`.
6. `../layout.py`: `build/pocket.json` (versão 4).
7. `revisao.py`: a página de revisão; depois `python etutti/landing_svgs.py` (o código dele não mudou).

### As mudanças do F1

1. **Logo reto (Mudança 1).** "eTuttino" em Georgia Bold 9 (39,6 × 6,8) sobre "POCKET" em Arial Bold 4 espaçado (22,5 × 2,9),
   gravados a **0,4**, horizontais, legíveis para quem toca. O bloco (39,6 × 12,3) fica centrado na zona de trás da interface:
   na vertical, no meio da faixa y 4–39,5 (atrás das saias dos knobs, menos os 5 da SPEC); na horizontal, no meio da largura
   plana nessa altura. Centro em x 38,6, y 15,6–27,9. Folgas: 8,0 até a borda de fora, 10,7 até a aresta de cima da rampa,
   16,6 até as saias dos knobs. `renders/seixo_iface.png`.
2. **Bolso do plugue da bateria** para o par JST PH de 3 vias encaixado (`PECAS battery.connector_pocket_v4`: PHR-3 + macho
   em linha, 8,0 × 4,8 × 12,5).
   - Por dentro: **16,0 × 9,25 × 7,6** (x 10,0–26,0; y 40,8–50,05; z 2,0–9,6). Pedido: ≥ 14,5 × 9,0 × 6,0.
   - O par fica deitado, com o eixo em x: 1,75 livres em cada ponta, 0,6 de cada lado, 2,8 por cima.
   - **Para caber os 9,0 em y, o berço da bateria andou 2 mm para a direita e 2,5 para a frente**, para (40; 68,3).
     Atrás do bolso está o J_BAT (y até 38), e a coluna do parafuso em (5,3; 38,5) não deixa o bolso ir para a esquerda.
     O berço continua 58,5 × 36,5 × 7,6; folga até a casca 0,85 (era 0,39).
   - O bolso é aberto para o berço em toda a frente: por ali entram os fios da bateria, que saem do PCM na ponta esquerda.
   - O rabicho (~70 mm, do J_BAT) entra por um rasgo de 6 × 4 na parede de trás e no teto da ponta esquerda (x 10–16), o
     `pigtail_way_in`. O macho do rabicho fica à esquerda e o PHR-3 da bateria à direita.
   - Os parafusos da tampinha passaram de ±19 para ±17 do centro do berço, em (23; 89,95) e (57; 89,95): na posição nova, o da
     direita batia na coluna (63; 93,5). O pé de (75; 90) foi para (80; 90), fora da tampinha.
3. **Abas da plaquinha dos knobs** (x 27,0–35,2; y 40,0–42,5 e 56,0–57,5).
   - A de trás passa por cima da Audio Board: as pernas do encoder (z ≥ 14,08) ficam 1,78 acima dela e 1,8 do jack dela.
   - A da frente entrava 0,76 na parede da caixa do alto-falante. A parede agora tem um **rebaixo fechado**: x 26,5–35,7,
     até y 58,0, até z 18,5, com paredes de 1,5, aberto só para trás. Ele apoia no mesmo fundo colado, então a caixa continua
     vedada. Folga da aba ao rebaixo: 0,5 (pedido: parede em y ≥ 57,8 de x 26,7 a 35,5 e de z 14,0 a 17,5). O alto-falante
     fica 5,9 acima. `renders/fit_corte_x31.png`.
   - A caixa passou de 18,5 para **17,9 cm³** (15,2 contando o alto-falante inteiro). Agora o volume desconta o anel e o
     rebaixo.
4. **Fone Same Sky SJ1-3525N** (`PECAS headphone_jack.datasheet_dims`): furo de **Ø 6,3** (nariz Ø 6,0 ± 0,3), eixo a
   **z 26,4** (2,5 sobre a plaquinha). Rebaixo de fora Ø 10, com 2,2 de fundo para a parede ficar com 1,5 no furo (as
   "janelas" da Mudança 2). Corpo 12 × 11 × 5 modelado como na folha: 1,6 até a tampa, 0,15 radial no furo, 2,9 do plugue
   micro-B. O nariz Ø 6 com eixo a 2,5 desceria 0,5 abaixo do topo da plaquinha. Modelei ele com o fundo reto, apoiado na
   plaquinha. Pergunta 2.
5. **Plaquinha do painel** (`PECAS panel_board.holes_v4`, a solução da eletrônica).
   - **Furo 1** (u 4,0; v 10,3), sobre o plugue micro-B, recebe um **pino de localização** da tampa: poste Ø 4,4, pé de
     Ø 3,6 × 1,0 (passa 0,35 do R1, 0402) e pino Ø 2,0 × 1,4, que para 0,2 antes da face de baixo da plaquinha. Embaixo da
     plaquinha não há nada; o pino fica 0,65 acima do plugue.
   - **Furo 2** passou para (u 14,24; v 3,8) = xy (15,38; 23,92), entre o USB-C e o fone. Parafuso M2 × 6 autoatarraxante de
     baixo (a casca de cabeça para baixo na montagem) numa **costela de 3,0** da tampa, ligada ao ressalto da parede, com
     piloto de Ø 1,7. A eletrônica pediu ≤ 3,4. Fica 0,22 do corpo do USB-C e 0,21 do do fone.
   - Cabeça (Ø 3,8 × 1,3) sob a plaquinha: 3,0 do plugue micro-B, 2,8 acima do plugue do J_SPK, 1,6 do fone, 1,9 do USB-C.
   - **Aba de apoio** de 0,8 × 1,5 sob a borda da frente, nos 30 mm, ligada ao ressalto ("a borda apoia no ressalto
     inteiro"). Ela passa 0,45 das pernas da frente do USB-C, que ficam 0,8 abaixo.
   - **Perna de trás-esquerda da carcaça do USB-C:** cortada rente depois de soldar (o manual diz). As outras três ficam a 1,7
     do plugue.
6. **Materiais por peça (Mudança 5)**: tabela no §8; `case.MATERIALS` e `pocket.json → case.materials`.
7. **Capas** exportadas para `case/out/` (as do eTuttino, mesmas alturas): `keycap_natural` (12), `keycap_sharp` (11),
   `keycap_cf` (5) e `keycap_test_4`.

### Arquivos finais (`case/out/`)

| Arquivo | O que é | Material | Qtd | Volume |
|---|---|---|---:|---:|
| `seixo_tampa` | casca de cima: paredes, tampas, logo, grade, furos, janelas do USB-C e do fone, ressalto e aba do painel, pino e costela da plaquinha do painel, postes dos knobs, caixa do alto-falante com o rebaixo da aba, colunas | **resina** (SLA/DLP, de engenharia, tipo Tough/Grey) | 1 | 74,6 cm³ |
| `seixo_fundo` | fundo: pilares da placa, berço e bolso da bateria, rebaixo da tampinha, parafusos, pés | **MJF PA12** | 1 | 45,1 cm³ |
| `seixo_tampa_bateria` | tampinha da bateria, 2 × M2 escareados | **MJF PA12** | 1 | 3,3 cm³ |
| `seixo_caixa_fundo` | fundo da caixa do alto-falante, colado e vedado | **MJF PA12** | 1 | 2,2 cm³ |
| `plate` (+ `plate.dxf`) | placa dos switches | FR-4 1,6 | 1 | 13,2 cm³ |
| `keycap_natural` | capas das naturais | resina branca | 12 | 0,52 cm³ cada |
| `keycap_sharp` | capas dos sustenidos | resina preta | 11 | 0,52 cm³ cada |
| `keycap_cf` | Dó e Fá, com xadrez diagonal em relevo | resina branca | 5 | 0,49 cm³ cada |
| `keycap_test_4` | teste de 4 capas num canal | resina | 1 | 2,1 cm³ |

`switches.stl` é só para os renders.

## 2. A forma

Sem mudança desde o D2: 251,5 × 100, curva única de R 89,2 à esquerda, quinas de R 24, abertura com a regra do eTuttino,
rampa com R 5, R 1 nas arestas de cima das paredes (Mudança 3), interface plana a 33 até y 55 e 13° para a frente. Contorno
exato × `shape.py`: 0,03 mm. Lições do OCC seguidas: um loft só na abertura, splines de pontos densos e pareados, os R 5 um
depois do outro, a casca fica com o maior sólido e cada exportação é conferida (§9).

## 3. Peça por peça (`PECAS.json` v3 × espaço reservado)

`fit_check.py` lê o `PECAS.json` na hora. **Interseção zero** de cada peça com a casca, o fundo, a placa dos switches, o
fundo da caixa e a tampinha. Também entre os pares que dividem espaço e entre as próprias peças do case.

| Peça (PECAS) | Onde | Medida usada | Folga mínima |
|---|---|---|---|
| Potenciômetro RK097/RK0972S | corpo x 10,37–21,62, y 44,25–53,75, z 14,5–30,3 | 15,8 × 9,5 × 11,25; rosca Ø 7 | rosca no furo 0,15; → encoder 3,3; → plaquinha dos knobs 1,6 |
| Plaquinha do potenciômetro | x 21,62–23,22, y 43–55, z 13,8–29,8 | 1,6 | → encoder 0,62 (pernas cortadas a ≤ 1,0); → painel 4,5 |
| Encoder EC11E | (31,12; 49), placa a z 17,18 | 12,4 × 13,2 × 6,5; eixo de 20 | eixo no furo Ø 6,8: 0,4; → alto-falante 3,05 |
| LED 3 mm bicolor | (43,12; 49), topo a z 32,5 | Ø 3, aba Ø 3,8 | no furo Ø 3,5: 0,25 |
| Plaquinha dos knobs + 2 abas | x 23,22–50,6, y 42,5–56; abas x 27–35,2, y 40–42,5 e 56–57,5 | 1,6 + pernas de 1,5 | aba de trás → jack da Audio Board 1,8, → Audio Board 1,78; aba da frente → rebaixo da caixa 0,5, → fundo da caixa 1,98 |
| Conector SH-10 (fios) | x 46,4–50,6, y 43–55 | 12 × 4,25 × 6,25 | → LED 1,28; → casca 2,67 |
| Plaquinha do painel | corda y 9–37, z 22,3–23,9 | 30 × 13 × 1,6 | → plugue micro-B 0,45; apoiada na aba e no ressalto |
| USB-C TYPE-C-31-M-12 | (14,58; 16,66), z 25,53 | 8,94 × 7,35 × 3,26; pernas 0,8 abaixo, a de trás-esquerda cortada | 0,22 no furo; pernas → plugue 1,69, → aba 0,45 |
| ESD PRTR5V0U2X | plaquinha do painel, em cima | 2,9 × 1,3 × 1,1 | sem efeito no case (fora da faixa da costela, ver §6) |
| Fone SJ1-3525N | (8,66; 29,34), eixo z 26,4 | 12 × 11 × 5 + nariz Ø 6 × 3,3 | 0,15 radial no furo Ø 6,3; → tampa 1,6; → plugue 2,9 |
| Fixação do painel | pino no furo 1, M2 no furo 2 | pino Ø 2 × 1,4; cabeça Ø 3,8 × 1,3 | cabeça → plugue 3,0, → J_SPK 2,8, → fone 1,6, → USB-C 1,9 |
| Plugue micro-B 90° | x 20,3–31,3, y 14,9–25,9, z 14,35–21,85 | 11 × 11 × 7,5 | → casca (pino) 0,65; → USB-C 2,05 |
| Teensy + Audio Board (baixa) | Audio Board x 30–68, y 4–40,8, z 10,7–12,3 | 38 × 36,8; 8,7 | → tampa do deck 0,5; Teensy → rampa 1,27 |
| Bateria 603450 com NTC | berço 58,5 × 36,5 × 7,6, centro (40; 68,3) | 7 × 36 × 58 + 8 % | inchada → teto 0,24; berço → placa 0,5, → casca 0,85 |
| Par JST PH 3 vias encaixado | no bolso, centrado | 8,0 × 4,8 × 12,5 | 1,75 nas pontas, 0,6 dos lados; → bateria 0,88; → placa 2,33; → J_BAT 3,54 |
| J_BAT / J_SPK com plugue | placa principal, (12,6; 32) / (15,6; 23,5) | PH, 10,5 de altura | → casca 1,51 / 1,94; → plaquinha do painel 4,1 |
| Alto-falante CLS0361-L152 | (26,88; 77,54), inclinado 13° | Ø 36 × 6,0 | anel 0,3; membrana → grade ~1,07; → fundo da caixa 2,74 |
| Placa principal | `pcb_envelope.json` | 1,2 mm, z 6,5–7,7 | → paredes, colunas, berço e bolso: 0,5 |
| Teclas | 28 switches + capas | Gateron KS-20, capas do eTuttino | switch → casca 8,3; capa → abertura 10,3 |

## 4. Alturas sob a tampa (interface plana: tampa por dentro a z 30,5)

| O quê | Topo | Até a tampa |
|---|---:|---:|
| Corpo do potenciômetro | 30,3 | 0,2 (a rosca prende na tampa) |
| Peças da plaquinha do painel | 30,1 | 0,4 |
| Corpo do fone | 28,9 | 1,6 |
| Encoder (corpo) | 23,68 | o eixo atravessa |
| Plaquinha dos knobs | 17,18 | postes de Ø 5 até a tampa |
| Plugue do micro-B | 21,85 | 0,45 até a plaquinha do painel |
| Teto do berço / do bolso | 10,8 | fundo da caixa do alto-falante a 10,9 |

## 5. Caixa do alto-falante e grade

Sem mudança, exceto o rebaixo da aba: caixa fechada e vedada de **17,9 cm³** (15,2 no pior caso), paredes de 1,5 da tampa até
z 12,1 e fundo colado. O fundo agora para a 0,2 da parede da frente do case, que fecha a caixa ali; a cola preenche. No D2
ele entrava 28 mm³ na parede, e a conferência nova das peças do case entre si achou isso. Grade: 73 furos de Ø 2,1, 33,5 % do
cone, membrana a ~1,07.

## 6. O contrato com a placa: `case/out/pcb_envelope.json` (o que mudou, para a eletrônica)

- **`outline` (a placa principal muda):**
  - O recorte da bateria passou de x < 68,95, y > 45,85 para **x < 70,95, y > 48,35**. A placa ganha a faixa y 45,85–48,35
    (x < 68,95) e perde x 68,95–70,95 (y > 48,35).
  - O recorte do bolso passou de x < 24,0 para **x < 27,7** (y > 39,1, igual).
  - Conferi no `pocket.kicad_pcb` atual: não há cobre nem peça nas áreas perdidas. A trilha EN_B passa a 1,28 do canto
    novo (70,95; 48,35). Basta trocar o contorno, repreencher os planos e rodar o DRC.
- **`battery`**:
  - `bay_inside` em x 10,75–69,25, y 50,05–86,55;
  - `hatch_screws` em (23; 89,95) e (57; 89,95);
  - `connector_pocket` com `inside` x 10–26, y 40,8–50,06, e `size` [16,0; 9,25; 7,6];
  - `pigtail_way_in` em x 10–16, y 39,1–43,3, z 6,8–10,8.
- **`controls`**: novos `tabs` (as duas abas) e `tabs_note` (o rebaixo da caixa).
- **`panel`**:
  - `holes` agora traz `kind`: `pin` no furo 1 (poste Ø 4,4, pé Ø 3,6 × 1,0, pino Ø 2,0 × 1,4) e `screw` no furo 2
    (15,38; 23,918), uv (14,24; 3,8).
  - A costela do furo 2 pousa no **topo** da plaquinha em u 12,74–15,74, v 0–5,3: **nenhuma peça nessa faixa** (o ESD
    PRTR5V0U2X precisa ficar fora dela).
  - Novo `front_ledge`: a borda da frente apoia numa aba de 0,8 de fundo. Nada na face de baixo até v 0,8.
  - `jack`: `part`, `hole_d` 6,3, `z` 26,4, `outer_spot_face_depth` 2,22, `barrel_front_past_board_edge` 1,35.
- **`connector_zones.J_CTL`**: vai até y 48,35 (antes 45,85).
- **`levels`**: recalculados com o par JST, a cabeça do M2 do painel, as abas e o rebaixo.
- `spec` virou "pocket SPEC v4, task F1".
- Sem mudança: `keys`, `supports` (45 pilares + 2 de parafuso), `mounting_holes`, `stack`, `boss_keepouts`, `plate_*` e
  `speaker`.

## 7. Rigidez da placa

`mechanics.py` (grelha da FR-4 nua de 1,2 mm sobre o contorno novo, malha de 2 mm, 45 pilares + 28 pernas da pilha):
**0,029 mm no pior botão (C5, fileira 4) a 3 N**, média 0,011. Limite 0,05. A eletrônica tinha 0,021 com a placa real.

## 8. Fabricação

- **Materiais (Mudança 5):**
  - casca de cima em **resina** (o logo de 0,4 e as pontes de 0,9 da grade pedem a resolução dela);
  - fundo, tampinha da bateria e fundo da caixa em **MJF PA12** (resistência, preço);
  - capas em resina, brancas e pretas;
  - placa dos switches em FR-4.
- **No MJF:** abrir os pilotos M2 do fundo e da tampinha para Ø 1,8.
  - O bolso e o berço são abertos por baixo ou para o lado. Não há cavidade fechada com pó preso.
  - O bolso tem teto, mas é aberto na frente inteira.
- **Na resina:** a casca de cima imprime como está (±0,1–0,15). O rebaixo da caixa e a costela do painel não têm balanço
  maior que o da tampa.
- **Parafusos:**
  - fundo: 10 × M2,5 autoatarraxantes;
  - placa principal: 2 × M2 com porca;
  - plaquinha dos knobs: 2 × M2 nos postes;
  - plaquinha do painel: **1 × M2 × 6** na costela, mais o pino no outro furo;
  - tampinha: 2 × M2 escareados.
- **Espessuras:** as do D2. Novas:
  - rebaixo da caixa: 1,5;
  - costela do painel: 3,0, com 0,65 de parede em volta do piloto;
  - aba sob a plaquinha do painel: 1,5.
- **Peso:**
  - **Peças impressas: ~156 g**:
    - casca em resina: 88 g;
    - MJF: 51 g;
    - 28 capas: 17 g.
  - Placa dos switches em FR-4: ~24 g.
  - **Instrumento inteiro: ~420 g** (estimativa):
    - switches: 140 g;
    - placa principal: ~45 g;
    - pilha: ~10 g;
    - bateria: 22 g;
    - alto-falante: 8,6 g;
    - parafusos, knobs e plaquinhas: ~13 g.

## 9. Conferência das exportações

- **Arestas abertas ou não-manifold: 0** em todos os 9 STL (casca, fundo, tampinha, fundo da caixa, plate e as 4 capas).
- **Raios** na casca exportada:
  - abertura: 140/140 livres (5 por tecla, até a placa);
  - grade: 73/73;
  - knobs e LED: 3/3;
  - **novo**, de lado pelas janelas do USB-C e do fone, de fora até a borda da plaquinha: 10/10.
- **Peças do case entre si:** interseção 0 em todos os pares. Antes da correção, o boss da tampinha batia na coluna (63; 93,5)
  em 1 mm³, e o fundo da caixa na parede da frente em 28 mm³.

## 10. Renders (`etutti/hardware/pocket/case/renders/`)

- `seixo_iso`, `seixo_iface` (logo reto), `seixo_top`, `seixo_left` (janelas do USB-C e do fone), `seixo_below`.
- `fit_iso`, `fit_dentro`.
- Cortes:
  - `fit_corte_y21` (painel sobre o plugue);
  - `fit_corte_y44` (bolso e potenciômetro);
  - `fit_corte_y49` (linha dos knobs);
  - `fit_corte_y78` (alto-falante);
  - `fit_corte_x15`;
  - `fit_corte_x18` (bolso com o par JST);
  - `fit_corte_x30`;
  - `fit_corte_x31` (as duas abas, a da frente no rebaixo).
- `pcb_envelope` (com as abas).

Conferi as imagens olhando.

## 11. Mudanças de contrato

### `build/pocket.json` (version 4, spec v4, task F1)

- `controls`:
  - `logo_letters` agora são letras em linha reta (`up_deg` −90);
  - novos `logo_lines` (texto, fonte, corpo, centro, linha de base, largura, altura) e `logo_kind`;
  - `logo` (a zona) recalculada.
- `controls_board.tabs`: novo.
- `battery`: `rect`, `outside`, `centre` (40; 68,3) e `hatch_screws` mudaram; `connector_pocket` é novo.
- `panel.jack`: `part`, `hole_d` 6,3, `z` 26,4. `panel.holes`: novo (pino / parafuso).
- `main_board.outline` = o novo contorno do envelope.
- `case`: `files` com as capas, `materials`, `cap_counts`, `weight_g.v4_materials`.
- Sem mudança: teclas, `rows`, `origin` 98,45, comprimento 251,5, knobs e LED, grade, pilha.

### `case/out/pcb_envelope.json`

Ver §6. **Para a eletrônica (F2):**

1. trocar o contorno da placa principal (recortes novos) e rodar o DRC;
2. deixar livre no topo da plaquinha do painel a faixa da costela (u 12,74–15,74, v 0–5,3) e, embaixo, a borda da frente
   até v 0,8;
3. o furo 1 da plaquinha do painel continua Ø 2,2 (pino Ø 2,0).

## 12. Manual de montagem (M1)

Página: **`/etutti/pocket/manual/`** (`etutti/pocket/manual/index.html`), só em português, noindex/nofollow, linkada da
página provisória `/etutti/pocket/` ("Manual de montagem →", nas três línguas da página). É independente do manual do
eTuttino: `styles.css` e `lightbox.js` são cópias locais (mesmo estilo e mesmo lightbox, sem as `.lang-block`); usa
`shared/site-title.css?v=20261008`.

- **Rota única:** placa principal e plaquinha do painel montadas pela JLCPCB. Cada passo marca o que se solda em casa
  (etiqueta "em casa"). O conteúdo elétrico (solda, testes, valores, avisos da LiPo) é o do `pcb/MANUAL_ELETRICO.md`.
- **Ordem da SPEC:** 1 antes de começar, 2 capas de teste, 3 Teensy, 4 placa principal, 5 plate e switches,
  6 plaquinhas, 7 bateria e alto-falante, 8 fechar o case e 9 primeiros testes sem a firmware. A seção de firmware e
  calibração está marcada "em breve".
- **Tabelas geradas:**
  - lista do kit, lida de `pcb/fab/pocket_kit_bom.csv`;
  - esquemas dos cabos dos knobs, do painel e do micro-B;
  - polaridade da bateria.

  Quem escreve é o `manual3d/page_tables.py`, entre marcadores. A lista de peças (balões 1–38), o que imprimir (com o
  material) e os pontos de teste A–H estão escritos na página.

### Figuras: `etutti/hardware/pocket/manual3d/`

Adaptei o pipeline do eTuttino (`etutti/hardware/manual3d/`, sem mudar nada nele).

- `build.py` exporta as quatro placas do Pocket com `kicad-cli` (glb) e chama os outros três scripts:
  - `parts.py`: peças sem modelo 3D (Teensy, Audio Board, barras, switches, RK097, EC11E, LED, USB-C, plugues, bateria,
    alto-falante, parafusos). As posições vêm do `case.py`, do `pcb_envelope.json` e do `PECAS.json`.
  - `render_blender.py`, no Blender 5.2 (Cycles/OptiX).
  - `annotate.py`, cópia com cotas: balões, setas e cotas, saindo em `etutti/pocket/manual/img/`.
- Também copia os renders do KiCad (`pcb/fab/pocket_{top,bottom}.png`).
- A plaquinha do volume entra no Blender por uma rotação própria (ela fica em pé no plano y–z); a do painel, pelo
  referencial da corda.
- `build/` fica fora do git.

| Figura | Passo | Cobre (MANUAL_ELETRICO) |
|---|---|---|
| `r_hero` | abertura | — |
| `r_exploded` (balões) | 1 | — (lista de peças) |
| `r_section_y21`, `r_section_y49`, `r_section_x30` | 1 | **F-14** (Pocket montado em corte: pilha, bateria, alto-falante, plaquinhas) e o corte lateral do **F-06** |
| `r_keycap_test` | 2 | — |
| `l_teensy_cut` | 3 | **F-01** |
| `l_audio_wires` | 3 | **F-02** |
| `l_stack` + `r_stack` (cota 8,7) | 3 | **F-03** |
| `board_bottom`, `board_top` (renders do KiCad) | 4 | **F-04** |
| `l_connectors` | 4 | **F-05** |
| `l_stack_main` (calço de 3 mm, fios do fone) | 4 | **F-06** |
| `l_switches` | 5 | — |
| `l_pot_board` | 6 | **F-07** |
| `l_controls` | 6 | **F-08** |
| `l_joint` | 6 | **F-09** |
| `l_cable_ctl` + esquema SVG do cabo dos knobs | 6 | **F-12** |
| `l_panel` + esquema SVG do cabo do painel e do micro-B | 6 | **F-13** |
| `l_panel_under` (perna cortada, H1, H2) | 6 | **F-10** |
| `l_speaker` | 7 | — |
| esquema SVG da polaridade + `l_battery` | 7, 8 | **F-11** |
| `l_lid_boards`, `l_board_mount`, `l_close`, `l_caps` | 8 | — |
| `l_testpoints` + `l_tp_panel` (pontos A–H) | 9 | **F-15** (dividido em dois: na vista de cima, a plaquinha do painel cobre o J_BAT) |
| `r_led_red` / `r_led_off` | 9 | **F-16** |

Os números dos balões estão na "Lista de peças" do manual, e as letras A–H na tabela de pontos de teste. A figura F-11 virou
um esquema, sem render 3D da bateria com o multímetro.

### Achado ao montar a cena: a plaquinha do volume estava espelhada (corrigido)

`pcb/build_small_boards.py` usava X = 55 − y "visto do lado do potenciômetro". Visto desse lado, quem toca fica à direita,
então o X do KiCad tem de crescer para a frente. O pad de GND da junta de 90° caía num pad sem rede.

**A eletrônica corrigiu (plaquinha do volume v0.2, X = y − 43):**
- o GND da junta está em y 46,4 nas duas placas;
- pinos do potenciômetro ao longo de y: 3 VCC em 46,5, 2 cursor em 49,0, 1 GND em 51,5;
- chave: 5 em 46,5 e 4 em 51,5;
- pads do cabo, de y 44,2 a 53,0: JW5, JW1, JW2, JW3, JW4.

O sentido do volume não mudou (os pinos só entram de um jeito): girar para a direita, visto de cima, aumenta, pela
convenção da Alps. Conferir na peça.

Renderizei de novo, a partir do `pocket_pot.kicad_pcb` v0.2, todas as figuras que mostram essa plaquinha:
- `l_pot_board` e `l_joint`;
- `l_controls`, `l_cable_ctl`, `l_lid_boards` e `l_tp_panel`;
- `r_exploded` e `r_section_y49`.

A serigrafia "VOL v0.2" agora sai legível do lado do potenciômetro, e as pontas dos fios 1–5 seguem a ordem nova
(`parts.py`). O texto do manual não fala da ordem dos pads nem do sentido do volume, por isso não mudou. A página foi
conferida de novo: 375 px sem rolagem lateral, imagens e links com 200, console sem erros.

## Perguntas para a gestão

1. **Berço da bateria 2 mm para a direita e 2,5 para a frente** para o bolso do plugue ter os 9,0 pedidos. Muda o contorno da placa principal (só a borda, sem cobre na área), que a eletrônica refaz no F2. Aprova?
2. **Nariz do fone SJ1-3525N:** com Ø 6,0 e o eixo a 2,5 da plaquinha, ele passaria 0,5 abaixo do topo da plaquinha. Pela pegada do KiCad, a frente do corpo fica 1,95 para dentro da borda, então o nariz fica em parte sobre a placa. Modelei o nariz com o fundo reto. A eletrônica confere no desenho ou na peça antes do pedido das plaquinhas?
3. **Costela de 3,0 com o M2 da plaquinha do painel:** sobram 0,65 de parede em volta do piloto, na resina. Para o protótipo serve. Se rachar, a troca é um inserto ou um piloto de Ø 1,6. Aceita?
4. **Protótipo:** falta só o F2 trocar o contorno da placa principal. O ESD (U1, v 9,6 na plaquinha do painel de 18:29) já está fora da faixa da costela. Com isso, a parte física fica congelada. Pode encomendar? Casca de cima em resina; fundo, tampinha e fundo da caixa em MJF; capas em resina, primeiro o `keycap_test_4`.
5. ~~**Plaquinha do volume espelhada**~~ **Respondida:** a eletrônica corrigiu na v0.2 (X = y − 43, GND da junta em y 46,4 nas duas placas); as figuras foram refeitas (§12). Falta só conferir na peça que o volume sobe girando para a direita.
6. **Manual (M1):** as figuras F-11 e F-15 da eletrônica viraram, respectivamente, um esquema de polaridade e duas vistas de cima (placa principal / plaquinhas), porque a plaquinha do painel cobre o J_BAT na vista de cima. As posições exatas dos pads VUSB–VIN no verso do Teensy e dos três terminais do fone na Audio Board estão marcadas "(conferir)" no manual. Serve assim para o protótipo?
