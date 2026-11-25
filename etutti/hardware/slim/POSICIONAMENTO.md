# eTutti Slim · Posicionamento (R4SL: placa principal, Etapa 2b; régua R8 e grade, R3SL, abaixo)

Atende a **SPEC R3SL §8, item 2**. Posicionado: a **régua R8** e a **grade**. **Nada roteado** (nenhuma trilha), **a placa principal não foi posicionada**, nada cotado ou comprado. Independente da V4.

## A. Placa principal (SPEC R4SL, Etapa 2b — portão B da placa principal)

Atende à **SPEC R4SL §8, item 2**. **Nenhuma rota**, nada cotado ou comprado. Posicionada por `pcb/posiciona_principal.py` (KiCad python, ~5 min; lê `pcb/build/slim_netlist.net` e `case/envelope_principal.json`, o contrato do Design) → `pcb/kicad_principal/slim_principal.kicad_pcb`, `slim_principal.kicad_pro`, `pcb/principal/posicao_principal.json` (posições, pads, alturas: a entrada da planta, da cena 3D e da rota). Nunca rodar por cima de uma placa roteada.

### A.1 Resultado

| Item | Valor |
|---|---|
| Placa | **69,0 × 77,1 mm** (x −95,8 … −26,8, y −9,0 … 68,1), 2721 mm², **4 camadas**, 1,2 mm, face de baixo em z 6,8 |
| Forma | faixa de **22,5 mm** (x −58,5 … −36,0) sob os knobs; duas abas (fileiras 1 e 3) até x −26,75; pé de 37,3 × 21,1 mm até a parede esquerda; chanfro de 3,0 × 2,8 na quina de trás à esquerda; fora da baia (a parede da baia toca z 7,0 > 6,8) |
| Peças | **120**, todas na **face de baixo** (47 E · 40 P · 13 F · 12 R · 8 I) + 5 furos M2 (D2,2) nos pilares |
| DRC sem trilhas (`pcb/principal/drc_principal.py`) | **0 erros, 0 avisos**; 379 itens “não ligados” = a ratsnest; **paridade com o esquema 0** |
| RT1062 | no centro da faixa, **(−47,25; 33,0)**, rotação 0 (a que minimiza a distância aos conectores, USB, I²S e flash); **zona de escape 2,5 mm**: retângulo **x −55,75…−38,75, y 24,5…41,5** (17,0 mm), vazio de peças; 196 bolas conferidas na R3SL |
| Corredores (indicativos, a rota decide) | ADC (OUT_R1…R4) → os 4 FFC pela borda direita da faixa; QSPI → flash U103 e cristais Y101/Y102 logo abaixo (y 14–22); I²S/USB → pé da placa (esquerda/atrás); I²C → sensores dos knobs |
| Par USB | USB-C **J201 (−66,0; 64,2)** → ESD U201 → bolas do RT1062: **36 mm** em linha reta (J201→U201→bola; Manhattan 47 mm); o aceito era 30–35: **~1–6 mm acima**, roteado deve dar ~38–42 mm (pergunta 6) |
| FFC | **J601…J604** alinhados com as caudas: y = 0 / 16,02 / 32,05 / 48,07, boca para **+x**; **folga horizontal 5,5 mm nas 4 fileiras** (as abas das fileiras 1 e 3 igualam as da 2 e 4); desnível régua→placa −3,0 / −1,0 / +1,0 / +4,0 mm |
| Cabo FFC | **4 iguais, retos, 20 mm sob medida** (estimativa, sem cotação): 5,5 de vão + 2 × 3,4 até os contatos + ~1,5 de folga e o desnível; de série, 30 mm com uma curva em S é a alternativa (pergunta 5) |
| Pinagem do FFC | **invertida no esquema** (pino n da principal = pino 9−n da régua): as bocas se olham e o cabo reto mantém a posição de cada condutor |
| Knobs | **U401** (registros, TMAG5273A2) em (−46; 0) e **U402** (volume, B2) em (−46; 48,06), no eixo, face de baixo; **U403** (DRV5032ZE) em (−51,09; 42,97), a 7,2 mm do eixo do volume a 225°; **D401** (LED) a 11,0 mm do eixo, atrás (−46; 59,06), no anel; **janela do LED na placa: ainda por definir com a folha do LED** (pergunta 7) |
| Conectores | **J301 (P2)** na parede esquerda (y 59,5), boca para −x (pad 1 do lado da parede); **J202 (JST SH)** em (−71,0; 51,5), boca para −y, para a baia, a 3,2 mm do passa-fios (x −82…−74) |
| Pilares | (−55,5; −7), (−40,5; 8,5), (−40,0; 63,5), (−93,0; 52,0), (−75,0; 64,0): discos de 6,4 mm sem peça |
| Alturas | maior peça sob a placa: **P2 5,0** (folga 5,2 com o bolso de 0,6 sob ele: sobra 0,2 + 0,6); USB-C 3,25; JST SH 2,9; SOIC-8 1,75; BGA 1,6; resto ≤ 1,5 |
| Folga das peças | 0,2 mm entre pátios, 0,3 da borda, nada na zona de escape nem num pilar |

### A.2 Planta cotada e blocos por função

`pcb/principal/img/planta_principal.png` (e `.svg`; `pcb/principal/planta_principal.py`): contorno, cotas, as 4 réguas (verde), a baia, os pilares, o círculo da plataforma e do anel, a zona de escape e **os blocos por cor**: **P** processador (RT1062 + flash + MKL02 + cristais + desacoplamento), **E** energia/USB (BQ24075, TPS63001, indutor, latch, USB-C, ESD, PTC), **F** áudio (SGTL5000, XC6206, P2), **I** knobs (sensores, chave Hall, LED, PROG), **R** réguas (4 FFC e as séries do scan). Vista **de cima** (frente embaixo); as peças estão no verso (tracejado). Quadro: x, y do instrumento; no KiCad X = 200 + x, Y = 100 − y.

### A.3 Cena 3D com o case, as réguas, a bateria e os knobs

`case/cena_principal.py` (CadQuery + PyVista; `case/renders/`): `cena_principal_baixo.png` (a placa vista de baixo, peças e bateria), `cena_principal_iso.png` (base, réguas, placa, bateria, knobs; sem o tampo), `corte_principal_registros.png`, `corte_principal_volume.png`, `corte_principal_longitudinal.png`. **Modelos reais:** RT1062 (SamacSys), USB-C, P2, FFC, TMAG5273 ×2, DRV5032, SGTL5000, BQ24075, TPS63001, FNR3015, cristal, LED, botão PROG (STEP do EasyEDA pelo código LCSC), passivas 0402/0603/0805 (biblioteca 3D do KiCad), **bateria VARTA** (STEP do fabricante), KS‑33D (Gateron). **Em caixa (sem STEP):** ver `case/out/cena_principal.json` (W25Q64, MKL02, JST SH, SOT‑23/SOD/QFN pequenos). Os knobs são sólidos simples a partir dos números do Design (S2). Não é o render Blender: o Blender só quando o J pedir.

---

## B. Régua R8 e grade (R3SL, Etapa 2a; grade atualizada na R4SL: furo 14,00 com dog-bone e M2 escareado)

## 1. Resultado

| Item | Valor |
|---|---|
| Régua R8 | **160,0 × 15,0 × 1,2 mm**, 2 camadas; **20 peças** elétricas (8 TMAG5253, 74HC595, FFC, 8 + 1 + 1 capacitores) na face de baixo + 8 conjuntos de furos da KS‑33D + 2 furos M2 |
| DRC sem trilhas (`pcb/regua/drc_regua.py`) | **0 erros, 0 avisos**; 72 itens “não ligados” = a ratsnest (ainda não há trilhas); **paridade com o esquema 0** |
| Grade | **148,0 × 16,0 × 1,2 mm**, FR‑4, 8 furos de **14,00 com dog‑bone** (círculos de R0,6 recuados 0,25 nos cantos; R4SL), 2 furos M2 de 2,2 **escareados D4,4 × 90° pelo lado das teclas** (nota no arquivo; a JLCPCB/PCBWay fazem o escareado); sem cobre; DRC 0/0 |
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

Grade: 148,0 × 16,0 (u 12,0…160,0 de cada régua, só sobre a área das teclas; a cauda fica livre). **Furo 14,00** nominal (SPEC R4SL item 4) com **dog‑bone** nos cantos; a tolerância da fresa (±0,1) é risco (R28/R41). Parafuso M2 **escareado**, rente à grade (item 6). Espaçadores M2 de 1,3 mm entre régua e grade (topo da grade a 2,5 da PCB, como no desenho Gateron).

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
