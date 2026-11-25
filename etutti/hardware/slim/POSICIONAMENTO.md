# eTutti Slim · Posicionamento da régua R8 e da grade (SPEC R3SL, Etapa 2a — portão B da régua)

Atende a **SPEC R3SL §8, item 2**. Posicionado: a **régua R8** e a **grade**. **Nada roteado** (nenhuma trilha), **a placa principal não foi posicionada**, nada cotado ou comprado. Independente da V4.

## 1. Resultado

| Item | Valor |
|---|---|
| Régua R8 | **160,0 × 15,0 × 1,2 mm**, 2 camadas; **20 peças** elétricas (8 TMAG5253, 74HC595, FFC, 8 + 1 + 1 capacitores) na face de baixo + 8 conjuntos de furos da KS‑33D + 2 furos M2 |
| DRC sem trilhas (`pcb/regua/drc_regua.py`) | **0 erros, 0 avisos**; 72 itens “não ligados” = a ratsnest (ainda não há trilhas); **paridade com o esquema 0** |
| Grade | **148,0 × 16,0 × 1,2 mm**, FR‑4, 8 furos de 14,03 (cantos R0,5), 2 furos M2 de 2,2; sem cobre; DRC 0/0 |
| Régua + grade no mesmo painel da JLCPCB | **a conferir**: mesma espessura (1,2 mm) e mesmo acabamento; proposta de painel ≈ 164 × 42 mm com trilho de separação de 2,0 mm (`pcb/regua/img/planta_regua.svg`, bloco 4) |
| TMAG5253 a 4,3 mm do centro | **sim** (lado do jogador); o desenho Gateron **não define pino 1**: a orientação foi conferida contra o footprint do EasyEDA (o que a JLCPCB posiciona) e o lado do ímã contra o STEP (§3) |
| FFC | origem em u = 2,2, v = 0 (a 2,2 mm da ponta esquerda); **boca para −u (esquerda)**; cabo reto de **~50 mm** (padrão) até a principal (estimativa: a principal não está posicionada) |
| Índice × posição × nota | **32/32 batem com o sketch** (`etutti/firmware/slim/check_teclas.py`) |

Arquivos: `pcb/regua/posiciona_regua.py` (KiCad python), `pcb/regua/posicao_regua.json` (o contrato com o 3D e com a rota), `pcb/kicad_regua/slim_regua.kicad_pcb`, `slim_grade.kicad_pcb`, `slim_regua.kicad_dru`, `pcb/regua/planta_regua.py` → `pcb/regua/img/planta_regua.{svg,png}`, `case/cena_regua.py` → `case/renders/*.png`.

## 2. Planta cotada

`pcb/regua/img/planta_regua.png` (e `.svg`): régua com as cotas (cauda 14,0; passo 18,5; sensor a 4,3; M2 em u = 49,0 e 123,0), as **quatro fileiras com o nome da nota e o índice em cada tecla**, a grade e o painel.

Quadro: **u** ao longo da régua a partir da ponta esquerda (0…160), **v** através, **+v para o jogador**, v = 0 na linha do centro das teclas; no KiCad x = 20 + u, y = 30 + v.

| Parte | u (mm) | v (mm) | giro | observação |
|---|---|---|---|---|
| Teclas 1…8 (furos da KS‑33D: poste Ø5,2 + 2 pinos Ø1,7 a ±5,075) | 21,25 + 18,5 (k − 1) | 0 | — | eixo dos pinos ao longo da régua |
| **U1…U8 TMAG5253** (face de baixo) | = u da tecla | **+4,3** | 180° | VCC/GND na fileira de trás (v +4,05), EN/OUT na da frente (v +4,55); o pad VCC fica do lado da cauda |
| **C1…C8** 100 nF | u − 2,0 | +4,05 | 180° | pad 1 (+3V3) junto ao pad VCC; o pad GND vai para o plano de cima por um via |
| **J1 FFC** | 2,2 | 0 | 90° | boca na ponta esquerda; pad 1 (GND) fica **na frente** |
| **U9 74HC595** | 9,2 | 0 | 180° | a fileira Q (pinos 2…7) voltada para a frente |
| C9 100 nF (do 595) | 6,0 | −3,4 | 90° | |
| C10 10 µF 0805 | 11,6 | −4,9 | 0° | |
| **M2 (furos Ø2,2)** | 49,0 e 123,0 | 0 | — | nos vãos entre as teclas 2‑3 e 6‑7 |

Folgas (conferidas pelo DRC): cobre–furo 0,25 (regra), cobre–borda 0,25; vias Ø0,5 / furo 0,3; trilhas ≥ 0,15 (preferida 0,2).

## 3. Sensor e chave: conferência com o desenho Gateron

- **Posição:** “Layout of PCB”: furo central Ø5,20 e dois furos Ø1,70 a 10,15 mm um do outro; o sensor (retângulo hachurado) fica **abaixo** do centro, no sentido oposto ao guia de luz. Distância usada: **4,3 mm** (SPEC).
- **Lado do ímã no STEP da KS‑33D:** o centroide das seções (z +0,4 e +4,4 acima da PCB) desloca-se para −y e a janela do guia de luz está em +y. A chave foi orientada com o **guia de luz para trás** e o **ímã/sensor para o jogador**: sensor em v = +4,3.
- **Pino 1:** o desenho não define pino 1. Os pads seguem o footprint do EasyEDA do C22401868 (o que a JLCPCB posiciona): **VCC e GND atrás, EN e OUT na frente**, para que o barramento EN e o OUT corram pela faixa da frente. A polaridade do campo não importa: o firmware usa o desvio absoluto em relação ao repouso.
- **Plano de roteamento (etapa 3), não feito:** `corredores` em `posicao_regua.json`: EN (oito lanes) e OUT na faixa da frente (v +5,15…+7,25), EN na camada de cima com um via por sensor e OUT na de baixo; +3V3 em trilha de 0,3 mm atrás dos sensores (v ≈ +3,1…+3,5); GND em plano na face de cima.

## 4. Regras (`slim_regua.kicad_dru`)

Vias 0,5 / 0,3; trilhas ≥ 0,15 (opt 0,2); **OUT a ≥ 0,3 mm de DADO, CLOCK e LATCH**; **nenhuma peça na face de cima** (lado das teclas), só cobre de trilha e plano; áreas de proibição: porca M2 (Ø5,4, embaixo) e cabeça do parafuso (Ø4,8, em cima) em volta dos dois furos M2.

## 5. Grade e painel

Grade: 148,0 × 16,0 (u 12,0…160,0 de cada régua, só sobre a área das teclas; a cauda fica livre). **Furo 14,03** (a SPEC pede 14,00 +0,05/−0,02: meio da faixa), **cantos R0,5** (o raio mínimo da fresa da JLCPCB não foi confirmado: pergunta 3). Espaçadores M2 de 1,3 mm entre régua e grade (topo da grade a 2,5 da PCB, como no desenho Gateron).

## 6. Cena 3D com o case (modelos realistas)

Montada por `case/cena_regua.py`: as **4 réguas** com seus componentes (STEP do EasyEDA: TMAG5253, 74HC595, FFC; 0402 e 0805 da biblioteca 3D do KiCad), **32 KS‑33D** (STEP da Gateron, assentados a 5,85 da PCB), grades, espaçadores, parafusos e porcas M2, a **base** (trilhos de apoio, bolsos, baia B3, bolso do P2, furos do USB‑C e do P2) e o **tampo** com as plataformas.

- `case/renders/cena_iso.png`: as quatro réguas nos seus degraus, sem o tampo.
- `case/renders/corte_tecla.png` e `corte_tecla_4fileiras.png`: corte transversal numa tecla (x = 37).
- `case/renders/corte_cauda.png`: corte na cauda (pads do FFC).
- `case/renders/corte_longitudinal.png`: corte pelo centro da fileira 1.

## 7. O que ficou de fora (de propósito)

Roteamento das duas placas; a placa principal; o CPL/BOM com a rotação por EasyEDA (etapa 3); cotação e compra. **Riscos:** TMAG5253 com 2912 peças na JLCPCB (229 na LCSC): 32 por instrumento; FFC C3250113 com 2374; o painel régua + grade é a confirmar.

## Perguntas para o design

As perguntas estão no fim de `FIT_CHECK.md`.
