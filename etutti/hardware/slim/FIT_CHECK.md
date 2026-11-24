# eTutti Slim · FIT_CHECK (SPEC R1SL, etapa 1 — portão A)

Resumo da etapa 1 e conferência dos envelopes do case contra os STEP e os PN escolhidos (SPEC §8, item 3). Relatórios das outras duas partes: [ELETRONICA.md](ELETRONICA.md) e [FIRMWARE.md](FIRMWARE.md). **Parado no portão A: nada foi posicionado, roteado, cotado ou comprado.**

## 1. Resumo

| Parte | Resultado |
|---|---|
| Eletrônica | Esquemas da **principal** (119 peças, 93 redes) e da **régua R8** (20 peças) com **ERC 0/0**; BOM conferida (50 códigos); mapa de pinos; lógica de energia; escada de 7 posições |
| Programação e som | `etutti/firmware/slim/slim.ino` **compila** para Teensy 4.1 (`usb=midi`, 396 MHz); 16/16 pinos batem com o `PINOS.md`; motor de som ainda placeholder; autonomia estimada ~8 h |
| Design | Envelopes conferidos abaixo; 14 STEP baixados e medidos; STEP que faltam listados |
| Desvios da SPEC | (1) RT1062 DVL6B × DVJ6B; (2) sem pot com chave na JLCPCB; (3) peças mid-mount não montáveis pela JLCPCB; (4) bateria sem NTC de 3 fios achada |

## 2. Conferências que passaram

| Item | SPEC | Conferido | Resultado |
|---|---|---|---|
| STEP do switch KS‑33D | caixa 14,60 × 14,60; do topo da haste ao fim do poste ≈ 13,05 (9,35 acima da PCB + 1,2 PCB + 2,5 abaixo) | 14,60 × 14,60 × **13,10** (`fornecimento/gateron/KS-33D_FB_POM_Mini.stp`) | ✔ coerente |
| Régua R8 | ≈ 15 × 160 mm | 8 × 18,5 = 148 + cauda de 14 = 162 mm; os 15 mm cabem entre fileiras de 16,02 mm (folga 1,02, em alturas diferentes) | ✔ |
| Pontas do teclado (planta x −90…149) | | fileira 1: última tecla em x = 129,5; fileira 4: 120,25; as réguas terminam ≈ 9 mm depois; sobram ≥ 9 mm até 149 | ✔ |
| Cauda das réguas × faixa da principal | faixa ≈ 24 mm junto às caudas | as caudas ocupam x ≈ −32,5 (fileira 2) … −9,25; a faixa de 24 mm ao lado deixa os knobs em x = −46 no centro dela | ✔ |
| USB‑C na parede de trás, centro x = −66 | 24 mm da parede esquerda | STEP do TYPE-C-31-M-14: 11,45 × 8,56 × 3,16 | ✔ longe das quinas; ⚠ o case precisa do recorte da peça mid-mount (a placa entra na fenda do conector) |
| P2 na parede esquerda, centro y = 59,5 | 11 mm da parede de trás | bateria termina em y = 54; jack tem ~6 mm de largura: 56,5…62,5 | ✔ 2,5 mm de folga até a baia |
| Pilha dos botões (fileira 1) | 10,85 topo da carcaça; botão 18,55 | confere com “PCB→topo 5,85” do desenho Gateron (5,0 + 5,85) | ✔ |
| Altura sobre a régua (z 3,8…5,0), peças de cima | só os knobs e conectores de cima | ver §3 | ⚠ |

## 3. Conflitos de altura (o case não decide, mas é preciso saber)

Folga abaixo da placa, pela SPEC: face de baixo da régua z = 3,8 − piso z = 1,6 = **2,2 mm** (para a placa principal, **depende do z dela**: ver pergunta 4). Peças de baixo (montagem JLCPCB só por baixo):

| Peça | Altura (STEP) | Cabe em 2,2 mm? |
|---|---|---|
| TMAG5253 (régua) | 0,41 | ✔ |
| 74HC595 DHVQFN (régua) | 1,03 | ✔ |
| RT1062 DVL6B | 1,51 | ✔ |
| BQ24075, TPS63001, SGTL5000 | 0,6–0,76 | ✔ |
| Cristal 24 MHz, LED 1615 | 0,72 / 0,6 | ✔ |
| TS-1187A (PROG) | 1,55 | ✔ |
| Ferrites e passivos 0402–0805 | ≤ 1,3 | ✔ |
| **FFC 8 vias C66953 (régua e principal)** | **2,1 (z −0,1…2,0)** | ⚠ sobram 0,1 mm; o FFC entra pela lateral e é fino, mas não há margem para tolerância |
| **Indutor FNR4020S2R2MT** | **2,61** | ✘ passa 0,4 mm; precisa de um indutor ≤ 1,9 mm ou de um bolso no piso |
| **JST PH S3B-PH-SM4-TB** (bateria) | **5,5** | ✘ não cabe por baixo; ver pergunta 4 |
| USB‑C mid-mount | 3,16 (a placa passa pelo meio) | depende de como o case recorta a parede |

Peças de cima (montadas em casa, são de furo passante):

| Peça | Medida | Observação |
|---|---|---|
| **Chave rotativa SRBV** | STEP aproximado (SRBV141404): **18,2 × 19,9 × 26,5**, eixo chega a **21,9 mm acima da face da placa**, pinos 4,6 mm abaixo | com a placa a z = 5,0 a ponta do eixo fica em z ≈ 27, **13 mm acima** do tampo (≈ 14 mm em y = 0). Não existe knob “baixo em poço de 1,2 mm” com esse eixo: o eixo/bucha (M9, porca de 11 mm) têm de ser encurtados ou a placa dos knobs desce (impossível: z = −1,9 pediria um piso negativo) |
| Pinos da SRBV por baixo | 4,6 − 1,2 (placa) = 3,4 mm abaixo da placa | passam do piso (2,2 mm): cortar ao rente depois de soldar, ou bolso |
| **Pot 9 mm com chave** | sem STEP (peça não escolhida) | o corpo do RK097 mede ~ 9,5 × 11,4 mm; o eixo de 15 mm tem o mesmo problema da SRBV |

## 4. STEP que faltam (o J fornece ou aprova a fonte)

| Peça | Situação |
|---|---|
| Switch KS‑33D | ✔ recebido |
| **Pot com chave** | ✖ peça não escolhida |
| **Chave rotativa de 7 posições** | ◐ só o modelo de **outra** SRBV (141404, EasyEDA); falta o STEP do **SRBV170501** (a Alps oferece STEP no site: o J ou o Code baixam com a OK dele) |
| **P2 3,5 mm mid-mount** | ✖ nenhum candidato com estoque |
| **Bateria** | ✖ o J manda quando escolher |
| **RT1062 DVJ6B (12 × 12, 0,8)** | ✖ sem modelo no EasyEDA (o DVL6B 10 × 10 tem) |
| **MKL02** | ✖ (peça PJRC, não há STEP público conhecido; QFN-16 3×3 é a caixa) |
| USB‑C mid-mount, BQ24075, SGTL5000, TPS63001, TMAG5253, 74HC595, FFC, JST, LED, cristal, indutor, PROG | ✔ baixados em `modelos/baixados/` (fora do Git) e medidos |

Os modelos baixados do EasyEDA são **aproximados** (caixa e pinos); servem para a conferência de alturas, não para renders finais (a SPEC §3 exige modelos realistas nos renders: avisar o J antes de qualquer render).

## 5. Pontos abertos que não dependem do design

- Pulso de partida da energia (C205 × R210) e Full Speed do USB: só a bancada fecha (ver `ELETRONICA.md`).
- Nada de posicionamento: orientação do BGA, canais de escape, localização do RT1062 “entre os knobs, na altura da fileira 3” ficam para a etapa 2.

## Perguntas para o design

1. **RT1062: DVJ6B (12 × 12, 0,8 mm, mapa de bolas já no esquema, 1 em estoque, só consignável) ou DVL6B (10 × 10 mm, a peça que a SPEC nomeia, 64 em estoque, passo mais fino e footprint novo)?** A SPEC escreve “DVL6B (BGA196 12 × 12, passo 0,8)”, que são duas peças diferentes. Define a área e o escape do BGA no posicionamento (etapa 2).
2. **Pot com chave:** não existe na JLCPCB. O J prefere (a) uma peça de distribuidor com chave rotativa verdadeira (candidatos Alps RK097 com chave rotativa, Same Sky PTN09S1; o Code lê os datasheets antes) montada em casa, ou (b) trocar por pot comum + comparador (sem o “clique”)?
3. **Eixo da chave de 7 posições:** a SRBV tem ~22 mm de eixo acima da placa. Aceitar (a) **encurtar o eixo** (cortar ~8–10 mm) e usar knob baixo, (b) um knob mais alto (o topo do botão passa de 25 mm), ou (c) trocar a chave por outra de perfil baixo (o Code procura; sem candidata hoje)?
4. **Qual é o z da placa principal?** Se for o da fileira 1 (z 3,8…5,0), o indutor (2,6 mm), o FFC (2,1 mm) e o JST PH da bateria (5,5 mm) não cabem sob ela com o piso de 1,6 mm. Opções: bolsos no piso sob a faixa (a SPEC só proíbe “furos”), peças mais baixas (indutor ≤ 1,9 mm, FFC de 1,0 mm, conector da bateria de 2,95 mm), ou rebaixar a faixa da principal.
5. **Peças mid-mount (USB‑C, P2):** montadas à mão (a JLCPCB provavelmente não as monta pela face de baixo). O case recorta a parede sob a placa; as pernas ficam dos dois lados: a ranhura da parede precisa de ~1,6 mm de espessura da placa; o J concorda com o recorte e com a montagem manual?
6. **Bateria:** o LP402764‑1000 tem **máximos iguais ao envelope** (28 × 68,5 mm de baia, folga 0 × 0,5 mm). Pedir ao fabricante **27 × 66 típico com NTC de 3 fios**, ou aumentar a baia em 1 mm? Qual o conector (JST PH, ZHL1.25)?
7. **FFC de 2,1 mm sobre a cauda:** trocar para a versão de 1,0 mm (C3250113 KH-FPC0.5-H1.0SMT-8P, 2374 em estoque; contato dos dois lados, a conferir) se o piso não ganhar bolso?
