# eTutti Student V4 · relatório da eletrônica

**SPEC atendida: R1V4 a R8V4 (R8V4: 22 nov 2026, tarefa 2, seção logo abaixo; R7V4: 22 nov 2026, tarefas 1 e 2, seção logo abaixo, só estudo; R6V4: 22 nov 2026, seção logo abaixo; R5V4: tarefas 2 e 3).** As seções 0 a 7 abaixo são da R2V4; a **R3V4** (tarefas 4 e 5) está na seção R3V4 logo abaixo.
Data: 21 nov 2026. Nada foi posicionado, roteado, encomendado nem gerado em `fab/`: é estudo (Fase A). A V3, a V2 e a V1 não foram tocadas.
Scripts novos (reproduzem os números): `calculos_eletronica.py` (E2, E3), `fornecimento/precos_jlc.py` (preços e classe na
biblioteca da JLCPCB, 21 nov, curl de 2 em 2 s). Contrato com a programação: `pcb/PINOS.md` (rascunho já entregue).
Convenção: **(conferir)** = sem medida ou datasheet conferido; **estimativa** = conta minha, sem cotação.

## R8V4 · ligação H aplicada (régua e principal), R305 = 0 ohm, portão P (tarefa 2, parte da eletrônica)

**SPEC atendida: R8V4 (22 nov 2026), tarefa 2 (eletrônica).** Regra nova (J): **nada é comprado até o protótipo inteiro estar fechado**; o que só a peça real responde está na lista de riscos abaixo. Só 32 teclas, só a Student V4. **Nada roteado** (0 trilhas, 0 vias, principal e régua); nada encomendado. O portão P (planta final para o J aprovar) está em **`POSICIONAMENTO.md`**; o roteamento só começa depois do "aprovado".

### O que foi aplicado
1. **Régua** (`pcb/regua/schematic_regua.py`, `posiciona_regua.py`): **J2 (OUT) de u 68,1 para u 47,5**, J1 (IN) em u 5,9; os dois SM06B-SRSS-TB / clone C56123098, no fundo, boca para −y. **Pinagem P6s** nos dois: 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO (J1: SER do 595; J2: QH' por R1). **R1 de 330 ohm** (era 100). **C3 saiu da pegada do OUT** (agora u 47,9, v −0,47, ao lado do sensor U3: 0 mm² dentro da pegada de J2, u 42,8..52,2). **Saíram os pads LK1/LK2** (elo soldado da R5V4: na H não há solda; o 595 e o resto não mudam). Altura de J1/J2 corrigida para 2,95 mm (R7V4). ERC 0/0, netlist igual; **DRC sem trilhas: 0 erros, 0 avisos, paridade 0** (52 ligações faltando, esperado).
2. **Placa principal** (`pcb/schematic.py`, `posiciona_v4.py`): **J601..J604 em P6s** (pino 4 = GND, 5 = SCAN_CLK, 6 = SCAN_DATA; o NC sumiu), **R605/R606 = 330 ohm** (C25104), **R305 = 0 ohm** (C17168). **ERC 0/0**, netlist igual à V3 fora das mudanças listadas, **DRC sem trilhas: 0 erros, paridade 0**, 242 ligações faltando (esperado; eram 234: o GND do pino 4 de cada J60k e o DADO no pino 6 criam 8 pontas) e **1 aviso `isolated_copper` do plano +3V3 sem vias (esperado sem trilhas, some ao rotear; igual às revisões anteriores)**. Posicionamento: nenhuma peça mudou de lugar (os J60k têm o mesmo pátio).
3. **`pcb/PINOS.md`** (seção R8V4 no topo): **os pinos do Teensy não mudam**; só a ordem do conector e os 330 ohm. A firmware não depende da ordem do conector; `programacao-som` confirma contra o sketch da V4.
4. **Painel de réguas e Gerbers** regenerados (`pcb/regua/fab_regua.py`; conferência, **SEM ROTA, NÃO ENCOMENDAR**), `bom_regua.csv`, `bom_v4.csv`, figuras `pcb/img/*`, `pcb/regua/img/regua_planta.png` e `regua_corte.png`, e a figura do portão `pcb/img/portao_p_instrumento.png`.

### Custo do R305 = 0 ohm e dos 330 ohm
**Nenhum tipo Extended novo; impacto menor que US$ 0,01 por placa.** C17168 (0 ohm 0402, UNI-ROYAL 0402WGF0000TCE) e C25104 (330 ohm 0402, 0402WGF3300TCE) são **Basic** na biblioteca da JLCPCB (consulta de 22 nov: estoque 13,9 milhões e 2,1 milhões; US$ 0,0012 e 0,0011 a 1 unidade); trocam C25879 (R305) e C25076 (R605/R606, R1), que continuam na BOM (outras peças usam). Só há **+2 linhas Basic** na principal (31 linhas), sem taxa por tipo. Principal: 79 peças, **13 tipos Extended**, US$ 17,87 por placa; régua: 14 peças, **3 tipos Extended** (TMAG, SH-6, 74HC595BQ). Custo total de 32 teclas (F2, pedido mínimo, sem frete, estimativas): **US$ 296,6-370,3 sem a ligação (R5V4) + 11,4-12,1 dos 8 cabos `A06SR06SR30K51B` = ~US$ 301-376** (o case entra com o valor do design, **US$ 44,3**, no lugar dos US$ 51,2 da R5V4).

### Plano B do microfone (só registrado, não aplicado)
Se uma cápsula (por exemplo o Sennheiser ME 3, que a folha só especifica "10 V") não partir com 3,0 V e 2 kohm: **boost de 9-10 V ligado por GPIO** (MT3608 C84817 + indutor 10 uH + diodo SS14 + 2 capacitores de >= 16 V + realimentação + PMOS de desconexão + resistor de bias de 4,7-6,8 kohm; ~US$ 0,35 de peças + 2 tipos Extended = ~US$ 6,5; ~9 x 7 mm no fundo; C309 de >= 16 V; 1 GPIO, o pino 5 está livre). Fica para uma revisão futura da principal; **não há teste de bancada nem compra nesta fase**: é risco do protótipo.

### Riscos aceitos (só a peça real fecha; nada é comprado antes do protótipo fechado)
1. **Cabo `A06SR06SR30K51B`:** se é mesmo reto (pino k → pino k) e se os "50,8 mm" são entre plugues ou entre fios (45,8 ou 50,8 de fio livre): o desenho do design fecha com os dois (profundidade de 102 mm). **Fita colada x fios soltos:** colada só dobra no plano da fita (laço em pé não cabe: folga 0,02-0,35 mm); se o cabo vier colado, é risco a conferir na compra. Com cabo invertido não há dano, mas a varredura não funciona.
2. **Clone XYECONN C56123098:** medidas e compatibilidade com o plugue JST SR (06SR-3S) sem desenho do fabricante **(conferir)**; altura do conjunto 2,95 + 3,6 mm nominal.
3. **330 ohm:** a borda do CLK a 5 MHz perde ~7 ns (RC com ~20 pF): sobra margem; se algo falhar, cai a 2,5 MHz por firmware.
4. **Microfone:** limiares MIC_DET e partida do ME 3 a 3,0 V são cálculo; a leitura real só com o hardware.
5. **Painel de réguas:** aceitação do painel do cliente com abas e microfuros pela montagem econômica da JLCPCB; pads do DHVQFN-16 (C730243) contra o EasyEDA no `cpl_jlc.py` (depois do portão).
6. **Furos M2 da régua:** ficam **três** (u 18,5 / 37 / 55,5, v +5,2), como antes (o design descartou os pares u 12 / 15 / 26,5 / 47,5 / 62: caem sob carcaça ou no 595); 11 M2 no total (R1: 18,5 e 55,5; R2 e R4: 37; R3.0: 18,5; R3.1: 18,5 e 55,5). Rigidez 0,028 mm a 3 N (≤ 0,05 ✓). Fita colada não fecha: risco a conferir na compra.

### Perguntas para o design (R8V4)
Respondidas pelo `FIT_CHECK.md` R8V4: (1) M2: três furos na régua, 11 M2, rigidez 0,028 mm a 3 N; (2) OUT u 47,5 / R1 u 53: fit check 0 mm³, rebaixo 39,8 x 22,5 mm; (3) cabeçalho 2,95 + plugue 3,6 no bolso de 6,9 mm: cabe (folga vertical ≥ 2,3 mm), case de y −2 a 100.
1. O J aceita **11 M2** (um por régua nas fileiras 2-4)? (pergunta do design ao J; a régua não muda.)
2. A reta de 3,3 mm após o plugue com 45,8 mm de fio útil só se confere no protótipo: aceito como risco.

## R7V4 · ligação H (cabo SH de estoque + rebaixo) e microfone Sennheiser ME 3 (tarefas 1 e 2, parte da eletrônica)

**SPEC atendida: R7V4 (22 nov 2026), tarefas 1 e 2 (eletrônica).** **Só estudo:** esquema, posicionamento, régua, placa e `pcb/PINOS.md` **não mudaram** e não mudam antes de o J aprovar a ligação. Regras gerais da R7V4 aplicadas: só a versão de 32 teclas é detalhada (a seção 7 abaixo é a validação curta do conceito modular) e só a Student V4 entra nas contas. Medidas **(conferir)** = suposição minha ou ficha incompleta; **estimativa** = conta minha, sem cotação.
Script novo (números e figuras): `pcb/regua/ligacao_h_r7.py` → `pcb/regua/ligacao_h_r7.json` e `pcb/regua/img/h_*_r7.png`. Fontes lidas: JST `eSR_SZ.pdf` (desenhos do cabeçalho SM06B-SRSS-TB e do plugue 06SR-3S, 22 nov), páginas DigiKey/Pololu/Pimoroni, biblioteca da JLCPCB (curl), guia rápido e folha de especificação do ME 3 (Sennheiser), datasheet do SGTL5000.

### Resposta curta

- **A H é possível pelo lado elétrico: sim.** Sinais (CLK a 5 MHz em 46 mm de fio AWG 30, ~9 pF de cabo por fileira contra o limite de 1 nF da linha OUT), corrente (~2,6 mA por fileira) e queda de tensão (0,5 mV no GND ao longo de 2 elos) não são problema. O que a H pede da eletrônica é **a pinagem** e **uma posição melhor do cabeçalho OUT** (seção 2).
- **Ordem dos pinos: com 6 vias NENHUMA pinagem funciona com os dois tipos de cabo** (prova na seção 1). Duas saídas: **P6s + cabo reto** (barato; compre `A06SR06SR30K51B`) ou **P9 simétrica de 9 vias** (funciona com qualquer cabo, +~US$ 13 e +1 tipo Extended na principal). **Recomendo P6s + cabo reto**; P9 se o J quiser comprar cabo sem pensar no tipo. Nos dois casos a alimentação **nunca** inverte.
- **Cabos:** 8 de **50,8 mm** (4 placa → 1ª régua + 4 entre réguas), nenhum de 100 mm (a sobra de 65-74 mm não tem onde ficar).
- **Custo (32 teclas, só a ligação):** **~US$ 11,4-12,1** com P6s (G: 11,11; D: 36,40 com a ferramenta), zero solda, zero tipo Extended novo; P9 ~US$ 25. Impressão do case: valor da R6V4 do design, **~US$ 45,8 (inclui os berços da G, ~US$ 0,4); o rebaixo da H soma volume que o design calcula**.
- **O que impede a H, e a menor mudança:** com a régua do jeito que está (OUT em u 68,1, 11,8 mm do IN da seguinte) o cabo de 50,8 mm sobra **17,3 mm** e o U que guarda a sobra vai **19,5 mm para trás da boca**; atrás da fileira 4 só há **14,3 mm** até a parede do case. **Menor mudança: mover o cabeçalho OUT da régua de u 68,1 para u ≈ 49,5** (cabo quase esticado, U de ~10 mm). Descrita, **não aplicada**.
- **ME 3:** o plugue liga no J302 **como está** (ponta = sinal e alimentação; anel e luva = GND). Com 3 V de MIC_BIAS **não dá para garantir só pela folha** (ela só diz "10 V"); o nível e o ganho do SGTL5000 **sobram**; a detecção MIC_DET **cai na faixa** de microfone. Recomendo **testar na bancada antes de mudar a placa**; plano B (boost 9-10 V) custa ~US$ 6,5. Seção 6.
- **Alinhamento com o design:** o estudo de geometria do design (`case/ligacao_h.py`, em paralelo) usa comprimento livre de 44,0-50,8 mm e raio de dobra mínimo de 4 mm; as contas acima usam 45,8 mm e 6 mm. **Onde divergirem, valem as do `FIT_CHECK.md` (R7V4)**; as minhas são a checagem elétrica e do que a pinagem pede da régua.
- **Pendências:** tipo real (reto/invertido) de cada cabo comprado (continuidade com multímetro), cabo plano colado x fios soltos (decide se o U pode ficar deitado), medidas do clone XYECONN do cabeçalho, corrente do ME 3 com 3 V.

### 1. Cabos de estoque e ordem dos pinos (item 4)

**Cabos reais** (nenhum tem o desenho com a ordem dos pinos; a distinção vem dos títulos do distribuidor e do texto do vendedor):

| Cabo | Comprimento / fio | Pinagem | Estoque / preço | Fonte |
|---|---|---|---|---|
| JST **A06SR06SR30K51B** (plugue SR, 6 vias nas duas pontas) | 50,8 mm, AWG 30 | **reto**: o título do DigiKey não diz "Reversed" | 2 186 em estoque; US$ 1,42 (1), **1,206 (10)**, 1,03 (100) | [DigiKey 455-3011-ND](https://www.digikey.com/en/products/detail/jst-sales-america-inc/A06SR06SR30K51B/6009387) |
| JST **A06SR06SR30K51A** | 50,8 mm | **invertido** ("Socket to Socket, **Reversed**") | **0** (previsto 1 000 em 28 dez 2026); US$ 1,42 | [DigiKey 455-2999-ND](https://www.digikey.com/en/products/detail/jst-sales-america-inc/A06SR06SR30K51A/6009375) |
| JST A06SR06SR30K102A/B, 152, 203, 254 (4, 6, 8, 10 pol) | AWG 30 | A = invertido, B = reto (mesmo código) | **(conferir)** estoque de cada um | DigiKey |
| Pimoroni "JST SH cable 6 pin" | 100 ou 300 mm, 26 AWG | **invertido** (texto do vendedor: pino 1 de uma ponta no pino 6 da outra) | (conferir) | [Pimoroni](https://shop.pimoroni.com/products/jst-sh-cable-6-pin) |
| Pololu 5543 / 5544 / 5545 (10 / 16 / 25 cm) | 28 AWG, fios torcidos | **não informada** (só "preto no pino 1, vermelho no pino 2") | US$ 3,32 / 3,61 / 4,06; **esgotado** (encomenda) | [Pololu 5543](https://www.pololu.com/product/5543) |
| Adafruit/SparkFun Qwiic, STEMMA QT | 4 vias, 50-400 mm | simétrico, mas **só 4 vias** | | não serve (6 vias) |

- **Nomenclatura JST (a mesma dos dois tipos):** `…B` = pino k liga ao pino k; `…A` = "Reversed", pino k liga ao pino 7-k. O PDF `eSR_SZ.pdf` da JST traz só os desenhos dos conectores (plugue SR 06SR-3S, fio AWG 30 de 7 fios, isolante OD 0,54-0,58 mm, 0,7 A, contato 20 mOhm máx. inicial / 40 depois de ensaio); **o arranjo dos circuitos do cabo não está nele (conferir ao receber: continuidade entre os pinos 1 das duas pontas)**.
- **Todos esses cabos têm plugue (fêmea SR/SH) nas duas pontas**; o lado da placa é sempre o cabeçalho com pinos: `SM06B-SRSS-TB` / clone XYECONN `C56123098` (o SM06B-SRSS-TB está no mesmo PDF da série SR de plugue IDC; o plugue SR de IDC entrar no clone XYECONN é **conferir**).
- **Por que existem os dois tipos:** num cabo plano colado, com os dois plugues voltados para o mesmo lado, a volta em U só sai com meia torção e isso inverte a ordem dos pinos. Por isso o J viu "invertidos".

**Por que 6 vias não aceitam os dois tipos.** Um cabo invertido liga o pino k da saída da régua A ao pino 7-k da entrada da régua B. Para funcionar com os dois tipos, a rede do pino k tem de ser igual à do pino 7-k: **três redes distintas no máximo** em 6 vias (e 4 em 8). Preciso de cinco (+3V3, GND, OUT, CLK, DADO). Logo: ou 9 vias (4 pares espelhados + 1 central = 5 redes), ou um tipo só de cabo.

Figura `pcb/regua/img/h_pinagem_r7.png` (as três pinagens contra os dois cabos):

| Pinagem | Pinos 1..n | Cabo reto | Cabo invertido |
|---|---|---|---|
| **de hoje** (R5V4) | +3V3, GND, OUT, CLK, DADO, NC | funciona | não funciona, **sem inverter a alimentação** (o +3V3 cai no pino NC), mas CLK x OUT se encostam (o clock da MCU contra a saída de um TMAG) |
| **P6s** (recomendada, 6 vias) | **+3V3, GND, OUT, GND, CLK, DADO** | funciona | não funciona, **sem dano**: +3V3 x DADO, GND x CLK, OUT x GND; todas por resistor em série |
| **P9** (9 vias) | **GND, +3V3, OUT, CLK, DADO, CLK, OUT, +3V3, GND** | funciona | **funciona** (cada pino liga à mesma rede) |

- **P6s:** o OUT analógico fica entre dois GND (blindagem do sinal mais sensível), +3V3 e GND nunca são vizinhos espelhados (reverso: +3V3 encontra DADO, nunca GND), e a única mudança em relação a hoje é o **pino 4 = GND novo, CLK no 5, DADO no 6** (o pino NC some). Escolhida por busca exaustiva das 360 permutações que mantêm +3V3 e GND longe um do outro (pior caso: +3V3 x DADO). **Recomendo subir os resistores em série de CLK/DADO para 330 ohm** (R605/R606 na principal, o 100 ohm do QH' na régua): limita a 10 mA o pior caso de um cabo errado (33 mA com 100 ohm) e custa nada (330 ohm x ~20 pF = 7 ns contra 100 ns de meio período a 5 MHz). **(descrição; não aplicado.)**
- **P9:** GND nos pinos 1 e 9, +3V3 em 2 e 8, OUT em 3 e 7, CLK em 4 e 6, DADO no 5 (central). Funciona com qualquer cabo (reto ou invertido), dobra os contatos de alimentação (queda de GND 0,25 mV em vez de 0,5), e um cabo de outro tipo nunca é erro. Custo: cabeçalho JST `SM09B-SRSS-TB(LF)(SN)` **C160408** (US$ 0,35 a 10, estoque 2 582), mais largo (B = 11,0 mm; footprint ~12,4 x 5,55) e plugue de 10,0 mm. Existe cabo `A09SR09SR30K51A/B` no DigiKey (~763 em estoque, ~US$ 1,80, **conferir**); o de 10 vias (C160408 -> **C160409**, estoque 75 725) é a alternativa com mais estoque (+1,0 mm de largura).
- **Placa → 1ª régua: o mesmo cabo e a mesma pinagem** (J601-J604 acompanham a régua; os dois cabeçalhos ficam com a mesma ordem).
- **Como o J confere um cabo recebido:** continuidade do pino 1 de uma ponta com o pino 1 da outra (reto) ou com o 6 (invertido). Etiquetar.

### 2. Cabeçalho, raio de dobra e o que muda no layout da régua (item 2, minha parte)

**Medidas do fabricante** (JST `eSR_SZ.pdf`, página 3; `h_juncao_r7.png`):

| Peça | Altura | Fundo | Largura |
|---|---|---|---|
| `SM06B-SRSS-TB` lateral (SMT) | **2,95 mm** | 4,85 (footprint 5,55 ± 0,1) | 8,0 (9 vias: 11,0) |
| `BM06B-SRSS-TB` topo (SMT) | 4,9 | 2,9 | 8,0 |
| plugue `06SR-3S` | **3,6** | ~2,45 | 7,0 (9 vias: 10,0) |

- **Correção a números anteriores:** a altura do cabeçalho lateral é **2,95 mm**, não os 4,25-4,3 estimados (R4V4/R6V4): o conjunto cabeçalho + plugue ocupa **3,6 mm** sob a régua, e a fileira 1 (bolso de 6,9 mm) deixa **3,3 mm** livres. **O clone XYECONN `C56123098` não tem desenho dimensional lido por mim (conferir)**: o footprint dele no EasyEDA já é o da régua.
- **Raio de dobra: o desenho da JST não dá.** Fio AWG 30, 7 fios, isolante OD 0,56 mm. Regra adotada, de fio de ligação comum: **R ≥ 6 mm** (~10 x OD) e **3 mm** como mínimo estático absoluto, com uma **reta de 5 mm** depois do plugue (os fios saem do plugue de IDC sem alívio de tração) **(conferir com o cabo comprado)**. Cabo plano de 6 fios: 5,6 mm de largura (9 vias: 8,6); só dobra "deitado" (em torno do eixo da largura).
- **Cabeçalho lateral, boca para trás (−y), como na R4V4:** é a posição que cabe nos 6,15 mm da faixa de trás (footprint 5,55 + a boca 0,5 além da borda) e o plugue entra pela janela de plugue já existente. **Boca para os lados (±x) não serve:** os dois plugues se encontrariam nos 0,4 mm de vão entre as réguas (cada plugue tem 2,45 mm de fundo). **Cabeçalho de topo `BM06B` (boca para baixo)** só ajudaria o plug com a régua erguida, mas pede ~12 mm de curva vertical sob a régua (o bolso da fileira 1 tem 6,9): descartado.
- **Quanto de cabo, de verdade** (`ligacao_h_r7.json`; comprimento útil = 50,8 − 2 x 2,5 = 45,8 mm, **conferir como a JST mede** o comprimento):

| Elo | Caminho mínimo | Sobra com 50,8 mm | Sobra com 101,6 mm |
|---|---|---|---|
| placa → 1ª régua, fileiras 1 e 3 (J60k x 77,4 → IN em x0 + 5,9 = 95,1) | 32,0 | **13,8** | 64,6 |
| placa → 1ª régua, fileiras 2 e 4 (IN em 85,85) | 22,8 | **23,0** | 73,8 |
| entre réguas (OUT u 68,1 → IN da seguinte, d = 11,8 mm) | 28,5 | **17,3** | 68,1 |

Resposta ao "50 ou 100 mm": **só 50,8 mm**. Com 100 mm a sobra (65-74 mm) vira ~2 voltas de Ø 12 mm.
- **O problema da sobra:** o cabo de 50,8 mm entre réguas, com as bocas lado a lado, faz um U que vai **19,5 mm para trás** (reta 13,6 + raio 5,9); atrás da fileira 4 há **14,3 mm** até a parede (y = 2): **não cabe** (figura `h_teclado32_r7.png`, trecho em vermelho). Os U das fileiras 1-3 passam sob a régua da fileira de trás (o bolso dela é mais fundo: 8,9 / 10,9 / 13,9 mm), cabem em altura, mas pedem o rebaixo em planta (~40 x 20 mm por junção).
- **O que a pinagem e a posição do cabeçalho exigem do layout da régua (só descrição, nada aplicado):**
  1. **OUT de u 68,1 para u ≈ 49,5** (entre o U3 em 46,25 e o entalhe de u 54,5-56,5; footprint 44,8-54,2): d passa a 30,4 mm, o cabo de 50,8 mm fica quase esticado e o U cai para **~10 mm** (reta 4,3 + raio 6) - cabe atrás da fileira 4. O IN fica em u 5,9. (Para um cabo de 50,8 sem folga o valor exato seria d = 29,0, u = 50,9, mas bate no entalhe.) O número depende de como a JST mede o comprimento: ±5 mm de cabo = ±5 mm em d.
  2. **P6s:** re-numerar J1/J2 (pino 4 = GND novo; 5 = CLK; 6 = DADO; no OUT o pino 6 é o QH' por resistor, no IN é o SER) e o resistor do QH' de 100 para 330 ohm; o NC do pino 6 deixa de existir.
  3. **P9:** footprint de 9 vias (~12,4 x 5,55; plugue 10,0) no lugar do de 6; IN passa de u 5,9 para ~6,6 (para não sair da régua: 0,4..12,8) e C1 sai da frente; OUT em u ≈ 47,5 (41,3..53,7, livre do entalhe de 54,5; d ≈ 32,4 mm: o cabo de 50,8 mm fica no limite, reta de ~3 mm antes da dobra).
  4. **Principal:** J601-J604 acompanham a pinagem (P6s: só a ordem; P9: troca de peça, J401 da tela continua de 6 vias) e R605/R606 = 330 ohm.
  5. **Os conectores continuam no fundo da régua (nada no topo)** e a régua continua 74 x 14 x 1,2 (a largura de 14 mm não muda).

Figuras (todas com o nome da nota em cada tecla, C azul, F laranja, onde há teclado):
`pcb/regua/img/h_pinagem_r7.png` (ordem dos pinos), **`h_teclado32_r7.png`** (planta das 32 teclas com cabeçalhos, cabos e a parede), **`h_juncao_r7.png`** (planta e corte do elo E4 | G4 e a alternativa OUT'), `h_microfone_r7.png` (item 6).

### 3. Custo (item 6): 32 teclas contra a G (R6V4) e a D (R5V4), só a ligação

| US$ | **H + P6s (reto)** | **H + P9** | G (R6V4) | D (R5V4) |
|---|---:|---:|---:|---:|
| cabos de estoque (4 placa → 1ª + 4 entre réguas) | **11,4** (8 x 1,42; 12,1 comprando 10 a 1,206) | ~14,4 (8 x ~1,80, **conferir**) | 6,6 (2 cabos de 100 mm) | ~6,4 (cabos crimpados + elos) |
| cabeçalhos a mais nas 10 réguas pedidas (20) | 0 (o SH de 6 vias já estava) | +5,6 (JST 9 vias a 0,350 contra 0,069) | +0,9 e machos 0,46 | 0 |
| tipos Extended a mais | **0** (réguas: TMAG, SH-6 clone, 595; principal igual) | +1 na principal (+3,09; J401 fica de 6 vias) e +1,75 de peças | +1 (macho; +3,09) | 0 |
| ferramenta | 0 | 0 | 0 | 30 (crimpadora) |
| juntas de solda | **0** | **0** | 20 | 40 |
| **total da ligação** | **~11,4-12,1** | **~25** | 11,11 | 36,40 (6,40 sem a ferramenta) |
| ponte / berço / pigtail na base | nenhum | nenhum | 4 pontes + 4 pigtails + berços | |

- **Impressão do case** (valor do design, `FIT_CHECK.md` R6V4, MJF PA12, sem tabela por tamanho): **US$ 45,8** para 32 teclas, **já com os berços da G** (1,4 cm³ = ~US$ 0,4). Na H os berços somem e entra o **volume dos rebaixos**, que é do design (cada junção ~40 x 20 mm em planta; o volume cai no piso da bandeja). Não somei nada além disso; estimativa de ordem de grandeza: cada cm³ de PA12 custa ~US$ 0,28.
- **A H custa o mesmo que a G (+~US$ 0,3-1,0) e ~US$ 25 menos que a D; sem solda, sem peça nova, sem ponte nem berço.** P9 custa ~US$ 13 mais que P6s.
- **O SH continua sendo o único conector das réguas** (clone `C56123098`, estoque 5 971, 0,069; P9: JST original C160408).
- **Estimativas sem cotação:** o preço do cabo de 9 vias e a metade dos de 4/6 pol; a JLCPCB não monta cabos.

### 4. Lista para o usuário e plano B (item 5, minha parte)

**Lista (32 teclas, tudo "em casa", sem solda e sem ferramenta):**
1. 1 placa principal (JLCPCB, montada), 8 réguas (JLCPCB; o pedido mínimo traz 10: 2 sobressalentes), o case e os botões, a ferragem de sempre (M2, insertos).
2. **8 cabos JST `A06SR06SR30K51B` (50,8 mm, reto, plugue nas duas pontas); compre 10** (2 sobressalentes, preço de 10 unidades). **Não** compre o sufixo `A` nem o da Pimoroni (invertidos) com a pinagem P6s; com P9 qualquer sufixo serve.
3. Etiquetar na chegada: continuidade pino 1 - pino 1.

**Passos (descrição; as figuras de montagem são do design):** 1) deixar a base aberta, com os cabos nos rebaixos; 2) régua erguida, plugue no cabeçalho de baixo (boca para trás); 3) acomodar a sobra de ~10-17 mm no rebaixo; 4) descer a régua nos pinos e parafusar; 5) próxima régua; 6) a placa → 1ª régua é o mesmo plugue. Trocar uma régua: soltar o parafuso, erguer, puxar os dois plugues (sem solda). Acrescentar módulo: +4 réguas e +4 cabos de 50,8 mm.

**Se a H não fechar, o que a eletrônica muda (menor para maior):** (a) só o OUT para u ≈ 49,5 (item 2.1: cabo quase esticado, U de 10 mm); (b) P6s e 330 ohm; (c) P9 se o J quiser qualquer cabo; (d) como último recurso, o cabeçalho **de topo** `BM06B` (boca para baixo, 4,9 mm de altura) no lugar do lateral, que pede rebaixo vertical de ~12 mm sob a régua (não cabe no bolso de 6,9 da fileira 1 sem o rebaixo mais fundo).

### 5. Riscos que só o protótipo fecha

1. **Cabo plano colado ou fios soltos?** Num cabo colado o U só dobra "deitado" no eixo da largura (flat-wise), com a boca para trás o U fica em planta, sobre o piso: **edgewise é impossível**; com fios soltos tanto faz. Pedir 2 amostras e dobrar.
2. **Comprimento "50,8"**: é entre plugues ou entre fios? Muda a sobra em ± 5 mm.
3. **Altura do conjunto montado** (cabeçalho 2,95 + plugue encaixado) sob a régua: 3,6 mm nominal; o clone XYECONN e a tolerância de ±0,1 do footprint ainda sem medida **(conferir)**.
4. **Retenção:** o SH segura por atrito + trava de 3 pontos do plugue; a vibração do teclado é baixa, mas fica o teste de "bater a mão" com o case fechado.

### 6. Microfone Sennheiser ME 3 (tarefa 2, estudo de mesa; a placa não muda)

Fontes: [especificação do ME 3 (art. 508928)](https://www.sennheiser.com/globalassets/digizuite/41606-en-sp_1167_v2.1_me_3_product_specification_en.pdf), [guia rápido](https://www.sennheiser.com/globalassets/digizuite/41080-en-me_3_quick_guide_04_2025.pdf), SGTL5000 (Freescale, Tabela 6 e "Microphone Input"). Figura: `pcb/regua/img/h_microfone_r7.png`.

**(1) Pinagem do plugue.** O guia rápido (esquema "Connector assignment") mostra um plugue de **3 contatos** (ponta, anel, luva): **"+" na ponta; "−" abrange o anel e a luva juntos** (leitura do desenho: os dois ficam em GND). A folha de especificação traz só o "+/−" sem texto. Logo: **sinal e alimentação vêm na ponta** (condutor único, 2 fios), **o anel não é usado** (curto à luva). **No J302 como está** (ponta → MIC_J, anel pino 6 NC, luva → GND) **funciona**: o anel do plugue (GND) toca o contato NC do jack. **Conferir:** continuidade anel-luva com multímetro; o plugue tem colar de travamento (descrição de varejista; a folha não cita): ver se passa pelo furo do jack do case (pergunta ao design).

**(2) Alimentação.** A folha dá **um só número, "supply voltage 10 V"** (sem faixa, corrente, ruído nem impedância; as especificações de máximo SPL 150 dB e 1,6 mV/Pa valem a 10 V). O MIC_BIAS do SGTL5000 chega a **3,0 V** (VDDA − 0,2 V) por **2 kΩ internos + R305 2,2 kΩ = 4,2 kΩ** (ou 2 kΩ com R305 = 0 Ω, valor só de BOM).
- Tensão na ponta, V = 3,0 − I · R (figura): com **4,2 kΩ**, 0,2 / 0,3 / 0,5 mA dão **2,16 / 1,74 / 0,90 V**; com **2,0 kΩ**, **2,6 / 2,4 / 2,0 V**. A corrente do ME 3 é desconhecida **(suposição 0,2-0,5 mA, típico de cápsula com FET; conferir)**.
- **Funciona com 3 V? Não dá para garantir só pela folha.** Estágios a FET desse tipo costumam operar de ~1,5-2 V para cima (suposição), o que **com R305 = 0 Ω** (2 kΩ, V ≥ 2,0 V até 0,5 mA) é plausível; com 4,2 kΩ é marginal a partir de 0,35 mA. **Perda de nível máximo:** a excursão cai com a tensão disponível; mesmo 1 V de pico (3 V de bias, folga de 1 V) é ~600 Pa = ~150 dB SPL a 1,6 mV/Pa, então **o limite elétrico fica muito acima do canto a 2-3 cm (≤ 126 dB SPL)**: a perda de máximo não importa para voz. **Ruído:** o ruído é do FET e da cápsula e quase não depende da tensão; o ganho do seguidor pode cair 1-3 dB (suposição). A coisa que pode falhar de verdade é a **partida** abaixo de uma tensão mínima desconhecida.
- **Teste de bancada (30 min, sem mudar a placa):** fonte de 3,0 V + 2,0 kΩ (e depois 4,2 kΩ) → ME 3 na ponta; medir a tensão CC na ponta e a corrente; tom de 1 kHz de um alto-falante pequeno a 3 cm, medir o nível (esperado 1,6 mV/Pa) e a distorção a ~114 dB SPL.
- **Se precisar de mais (plano B): boost 9-10 V ligado só por GPIO,** o menor circuito: `MT3608` (C84817, Extended, US$ 0,063) + indutor `CD54` 10 µH (Extended, ~0,04) + diodo `SS14` (C2480, Basic, 0,019) + 2 capacitores (≥ 16-25 V, **conferir** se há Basic) + 2 resistores de realimentação (0402) + 1 PMOS de desconexão da carga (o MT3608 sozinho deixa ~VBAT − 0,3 V na saída desligado) + 1 resistor de bias 4,7-6,8 kΩ + 1 GPIO (pino 5 está livre). **Custo ≈ US$ 0,35 de peças + 2 tipos Extended (6,18) = ~US$ 6,5; ocupa ~9 x 7 mm no fundo da principal** (o design diria onde). Pede C309 de ≥ 16 V (hoje 10 V) e filtro RC no bias (a ondulação do boost entra direto no sinal de um microfone de 1,6 mV/Pa). A firmware só liga o boost quando o usuário escolher "Sennheiser" (um eletreto comum com 10 V na ponta pode sofrer): **detectar** o tipo não é possível só pela corrente. Não é "ligada só com microfone detectado": é "ligada só com o modo pro".
- **Opção sem peça nova:** bias a partir de VBAT (3,0-4,2 V) por PMOS + resistor: +~0,7 V; ondulação do amplificador classe D no mesmo trilho: **não recomendo**.

**(3) Ganho** (SGTL5000, Tabela 6, 3,3 V: fundo de escala do ADC **1,0 Vrms** **(conferir se vale para o caminho MIC com ganho 0)**; pré-amplificador 0 / 20 / 30 / 40 dB + 0 a 22,5 dB no ADC; SNR do ADC **90 dB**, entrada −60 dB). A tensão do ME 3 a 1,6 mV/Pa e a de um eletreto de −42 dBV/Pa (7,9 mV/Pa; 14 dB mais):

| Nível na cápsula | ME 3 (rms) | com +20 dB | com +30 dB | eletreto (rms) |
|---|---:|---:|---:|---:|
| 100 dB SPL (canto suave) | 3,2 mV | −30 dBFS | −20 dBFS | 16 mV |
| 114 dB SPL (canto normal) | 16 mV | −16 dBFS | −6 dBFS | 79 mV |
| 120 dB SPL | 32 mV | −10 dBFS | 0 dBFS (limite) | 158 mV |
| 126 dB SPL (grito) | 64 mV | −4 dBFS | clipa | 316 mV |

**Basta.** Canto a 2-3 cm (guia rápido: 2-3 cm) fica entre 100 e 120 dB SPL (estimativa: ~21 dB acima de um canto a 30 cm); o ME 3 pede **+20 dB (padrão) a +30 dB (canto suave)**; o eletreto, 0-20 dB. **Ruído:** o ADC sozinho (31 µV a 0 dB) vira 3 µV de entrada com +20 dB e 1 µV com +30 dB; o resistor de bias de 4,2 kΩ junto da saída do microfone soma ~1 µV (Johnson, só em parte curto-circuitado pela impedância de saída do FET); o pré-amplificador do SGTL5000 não tem ruído de entrada na folha. Estimativa: **~2-3 µV no total** = ~36-40 dB SPL equivalente com o ME 3 e a **SNR de 75-78 dB a 114 dB SPL** (~62-64 dB num canto de 100 dB). Com o eletreto a mesma eletrônica dá 14 dB melhor. **A cadeia de voz (expansor, YIN, vocoder)** vê o nível em dBFS: o ganho de +20 a +30 dB do ME 3 (contra 0-20 dB do eletreto) compensa os 14 dB e os limiares do expansor ficam iguais. Ruído da cápsula não está na folha. A curva de resposta do guia rápido mostra ~−59 dBV a 1 kHz, ~3 dB abaixo dos −55,9 dBV de 1,6 mV/Pa **(conferir; as contas usam 1,6 mV/Pa e o pior caso fica 3 dB pior, ainda com folga)** (referência: o SL Headmic 1 da mesma linha tem 27 dB(A)).

**(4) MIC_DET (pino 25; R306 100 kΩ, C311 100 nF; limiares 0,30 e 2,85 V).** Com a corrente I do microfone, V = 3,0 − I · R. **Fica na faixa "microfone" (0,30 a 2,85 V) para I entre 0,036 e 0,64 mA com 4,2 kΩ; entre 0,075 e 1,35 mA com 2 kΩ.** O ME 3 (suposição 0,2-0,5 mA) cai dentro nos dois casos: 2,16 a 0,90 V (4,2 kΩ) ou 2,6 a 2,0 V (2 kΩ). Só sairia da faixa com mais de 0,64 mA (leria como "curto") ou menos de 0,036 mA (leria como "nada"). **Cálculo; a medir com o ME 3 na primeira placa.**

**(5) Recomendação.**
1. **A placa como está serve aos dois microfones**, desde que o ME 3 parta com 3 V de bias: o plugue, a ponta, o anel NC, o ganho (+20/+30 dB) e a detecção estão todos dentro. **Mudança de BOM (não de placa) recomendada: R305 = 0 Ω** (2 kΩ em vez de 4,2 kΩ; o eletreto comum aguenta: o datasheet só pede o resistor externo se os internos não servem) - dá 0,6-1,1 V a mais de tensão na ponta para o ME 3. **Não é aplicada** (a R7V4 pede só estudo); a firmware já escolhe `BIAS_RESISTOR` (2 kΩ).
2. **O ME 3 só precisa de mais se o teste de bancada falhar:** aí o boost de 9-10 V (~US$ 6,5, +2 Extended, ~9 x 7 mm, 1 GPIO) entra numa revisão da principal. **Isso é o que impediria o ME 3 no J302 como está: a tensão mínima real da cápsula, desconhecida.**
3. Microfone de PC com bias no anel continua fora. Padrão continua o headset de eletreto comum.

### 7. Validação do conceito modular (regra geral 1; sem tabelas por tamanho)

- **A régua universal se repete:** 74 x 14 x 1,2 mm, 4 TMAG5253 + 1 74HC595 + 2 SH, o mesmo painel e a mesma BOM (3 tipos Extended); +16 teclas = +4 réguas (uma por fileira) e +4 cabos de 50,8 mm.
- **A cadeia e a varredura crescem sem mudar a placa principal:** a principal tem 4 conectores (um por fileira), OUT_Rk nos pinos 14/15/26/27 e SCAN_DATA/SCAN_CLK nos 2/3; o número de pulsos é 8N + 1 (N = réguas por fileira) e a capacitância da linha OUT (cabo de 1 pF/cm, 3 pF por conector) fica em ~490 pF com 5 réguas contra 1 nF (a H com cabo de 50,8 mm soma só ~9 pF por fileira).
- **O case cresce pela mesma regra de comprimento** (+74 mm por módulo); a H não acrescenta peça à base.

### Perguntas para o design (R7V4)
1. **Boca para trás (−y) com cabeçalho lateral SM06B (2,95 mm de altura, plugue de 3,6):** confirmam que o conjunto cabe no bolso da fileira 1 (6,9 mm; sobram 3,3) e que o plugue passa pela janela e pelo entalhe do trilho da fileira de trás como na R4V4?
2. **O cabeçalho OUT pode ir de u 68,1 para u ≈ 49,5?** O cabo passa a correr pela faixa de trás ao longo de ~30 mm (d = 30,4) e o U cai para ~10 mm; o rebaixo precisa de ~40 x 20 mm por junção (planta) em vez de uma janela só no fim. Há conflito com a bossa/entalhe de u 54,5-56,5 e com a parede atrás da fileira 4 (14,3 mm)?
3. **A sobra de 10-17 mm de cabo no rebaixo:** cabe deitada no piso (cabo com fios soltos) ou precisa de curva em pé (cabo colado: ~12 mm)? O rebaixo é planta + profundidade: qual profundidade o piso aceita sem furar o fundo?
4. **P6s (recomendada) ou P9 (qualquer cabo):** o design aceita o cabeçalho de 9 vias (footprint ~12,4 x 5,55; plugue de 10,0) na faixa de trás se o J escolher P9?
5. **Colar de travamento do plugue do ME 3:** o furo do jack IN deixa passar um colar de ~6-7 mm? (Descrição de varejista; a folha da Sennheiser não cita.)
6. **J (gestão):** (a) P6s + cabo reto `A06SR06SR30K51B` ou P9; (b) aceita o teste de bancada do ME 3 antes de qualquer mudança de placa; (c) R305 = 0 Ω na BOM da próxima revisão.

## R6V4 · conectores fixos entre réguas (item 1), entrada placa → régua (item 2), microfone (item 5)

**SPEC atendida: R6V4 (parte da eletrônica; atualizada em 22 nov 2026).** Nada roteado (portão P fechado). Medidas marcadas **(conferir)** vêm de ficha genérica ou de footprint do EasyEDA, não de desenho dimensional do fabricante.

### Peças reais achadas (biblioteca da JLCPCB / LCSC, 21-22 nov; todas Extended)
| Uso | Peça (LCSC) | Estoque | US$ (1 un.) | Medidas | Observação |
|---|---|---|---|---|---|
| **Fêmea 1x5, 1,27 mm, SMD vertical (a recomendada)** | SHOU HAN PM1.27-1x5PLT-H3.4-R **C55566451** | 864 | 0,115 | isolante 3,4 mm | footprint do EasyEDA não existe para o H3.4 |
| mesma, mais alta | SHOU HAN PM1.27-1x5PLT-H4.3-R **C55218862** | 3 147 | 0,115 | isolante 4,3; **pads 0,74 x 2,10 mm, pernas alternadas a 3,10 mm: footprint 6,76 x 5,20 mm, corpo só 2,0 mm de fundo** (EasyEDA) | o H3.4 deve ser parecido **(conferir)** |
| **Macho 1x5, 1,27 mm, SMD vertical (ponte e ponta do cabo de entrada)** | SHOU HAN PZ1.27-1x5PLT-L7.2-R **C55213903** | 2 303 | **0,019** | plástico 1,0 mm, pino de encaixe 4 mm | 4 mm de pino numa fêmea de 3,4 mm: sobra 0,6 mm de plástico fora **(conferir)** |
| (descartadas) | Harwin M50-3200545 C7297883 (ângulo reto 2x5) | **0** | 2,79 | | sem estoque |
| | Sullins PPPC051LGBN-RC C7327802 (a do J) | **0** | 0,86 | PTH, 2,54 | sem estoque; as fêmeas em ângulo 1x5 de 2,54 que existem (C35167, C225513, SHOU HAN C54876734) são PTH de **8,5 mm** de altura: não cabem no bolso de 6,9 |
| | BOOMELE 1.27-2P C49000 (ângulo reto 1,27) | 927 | 0,10 | só 2 vias, PTH | não serve |
Fichas lidas: a SHOU HAN do H3.4 que o LCSC serve é uma "specification for approval" genérica (contato de bronze fosforoso estanhado, placa de 1,2 a 1,6 mm, 7 páginas, **sem a folha de desenho**); por isso as medidas acima são do footprint do H4.3 no EasyEDA, não do fabricante.

### O que cada opção dá (resumo; planta e corte em `pcb/regua/img/conectores_*.png`)
- **E1 (a ideia literal: macho em ângulo à direita, fêmea em ângulo à esquerda): inviável com peças de estoque.** Não existe fêmea 1x5 de 1,27 mm em ângulo reto SMD no estoque (só a Harwin 2x5, estoque 0, e uma de 2 vias PTH); as de 2,54 mm medem 12,7 mm de comprimento e 8,5 mm de altura. E, mesmo achando a peça, a fileira de contatos fica ao longo de y e atravessa o eixo das teclas: bate no pino da 1ª tecla da régua seguinte (faixa livre de 6,6 mm).
- **E2 (ponte): viável, é a recomendada.** Fêmea SMD vertical (C55566451) **igual nas duas pontas de toda régua, boca para baixo**, no lugar do J1/J2: a mesma **faixa de trás** (v -6,9..-1,05, 5,84 mm) que o design já reservou, não a da frente: o footprint real tem **5,2 mm de fundo** (os pads alternados), e a faixa da frente (y +1,0..+4,1) só tem 3,1 mm, além do trilho da frente (v +4,2..+7). Na faixa de trás cabem 6,76 x 5,2 mm centrados em u = 5,6 (entrada: u 2,2..9,0, sobra 1,5 até o capacitor C1) e u = 68,1 (saída). **Ponte** = PCB de 1,2 mm (mesma espessura da régua, **no mesmo painel**) com dois machos C55213903 a 11,8 mm de centro a centro (J2 de A em u 68,1, J1 de B em 74,0 + 5,6). Altura sob a régua: fêmea 3,4 + 0,6 de pino que sobra + macho 1,0 + PCB 1,2 = **6,2 mm** (com a ponte em 0,8 mm: 5,8) contra 6,9 mm do bolso da fileira 1: **folga 0,7 mm (conferir)**; as fileiras 2 a 4 têm bolso de 8,9 / 10,9 / 13,9 mm. Sem conflito com pinos de tecla (v 0, a ponte está em v -6,9..-1,7), sensores (pads até v -1,06), 595 (v +4,2), M2 (v +5,2) e trilhos (frente); os capacitores C1/C4 ficam a 1,5 mm. Montagem: sobe-se a régua nos pinos da bandeja, desce-se sobre a ponte já posta no bolso. Retenção: atrito de 5 pinos de 1,27 mm (~0,5 N por pino; **conferir**); o design deve dar à ponte um rebaixo de 18,5 x 7 mm no piso (ela não tem para onde subir: a régua está presa por 2 M2 e pelo deck).
- **E3 (FFC/FPC 1,0 mm): fora.** O conector FPC de 6 vias que a JLCPCB tem em estoque não achei (C48735 estoque 0); +1 tipo Extended.
- **E4 (contato de mola SMD): descartada sem detalhar.** Existem contatos de mola SMD de 2 mm (BAT WIRELESS BWCD-L3W2.0H1.0 C2988082, US$ 0,076, 75 mil em estoque), mas pedem passo de 2,54 mm (5 contatos = 10 mm), pressão contínua e ponte com almofadas banhadas a ouro; sem retenção própria, o risco de ruído com vibração é o pior do conjunto.
- **Cartão de borda:** nenhum conector de borda de 1,27 mm para PCB de 1,2 mm achei no estoque; não cotei.

### Entrada placa → 1ª régua (item 2)
**Confirmado: encaixe rígido direto não serve.** Os planos das réguas são ZR = 0 / 2 / 4 / 7 mm acima do topo da placa e a fileira 1 só começa 11,7 mm depois da borda (as 2 e 4, 2,45 mm): uma ponte plana só alcança a fileira 1 (e ainda por cima numa distância de ~18 mm, longe demais para uma ponte de 11,8 mm); as outras três precisam de degrau de 2, 4 e 7 mm. **Proposta: pigtail de SH-6 cortado.** Compro 2 cabos SH-6 de 100 mm com plugue nas duas pontas ([Pololu #5543](https://www.pololu.com/product/5543), US$ 3,32), corto cada um ao meio e aparo para ~25 mm: saem 4 pigtails com plugue SH numa ponta (o plugue entra no J601..J604 da placa principal, que **não muda**) e fios livres na outra, **soldados em casa a um macho C55213903** (5 juntas por pigtail, 20 no total; o fio 6 é cortado) que entra na fêmea de entrada da régua. Só esse macho é novo; as outras três saídas (cabo pronto de 15/25 mm, fita IDC, adaptador) ficam piores: não existe cabo pronto com SH numa ponta e macho de 1,27 na outra; fita IDC pede 10 vias de 12,7 mm de largura; o adaptador seria outra PCB com SH + macho (~US$ 6 por lote com PCB, sem ganho).

### Custo (item 3, US$, só a ligação, 32 / 48 / 64 / 80 teclas; D = referência da R5V4: cabos crimpados em casa com ferramenta de US$ 30 + elos de fio)

| Teclas | Réguas | **G** (E2 + pigtail) US$ | D (R5V4) US$ | G - D | Juntas de solda G / D | Tiras sobrando no pedido de 10 réguas |
|---:|---|---:|---|---:|---|---:|
| 32 | 8 + 4 pontes | 11.11 | 36.40 (6.40 sem a ferramenta) | **-25.29** | 20 / 40 | 2 |
| 48 | 12 + 8 pontes | 11.73 | 36.40 (6.40 sem a ferramenta) | **-24.67** | 20 / 80 | 3 |
| 64 | 16 + 12 pontes | 12.35 | 36.40 (6.40 sem a ferramenta) | **-24.05** | 20 / 120 | 4 |
| 80 | 20 + 16 pontes | 21.50 | 36.40 (6.40 sem a ferramenta) | **-14.90** | 20 / 160 | 0 |

- **G custa menos que a D** (e bem menos juntas de solda), e **dentro do critério** de "até ~US$ 15 acima da D". Composição de G (32 teclas): fêmeas 0,12 - 0,069 SH a mais em 20 réguas montadas = 0,92; machos 0,45; **+1 tipo Extended (o macho C55213903) = 3,09**; 2 cabos SH de 100 mm = 6,64 (Pololu); sem painel extra enquanto sobrarem tiras (**80 teclas não sobra: +1 painel de 5 tiras, estimativa US$ 9**). Troca SH -> fêmea nas réguas: **o número de tipos Extended das réguas sobe de 3 para 4** (TMAG, fêmea, 595, macho); a placa principal **não muda de tipos** (J601-J604 continuam SH, como o J401 da tela).
- **Estimativas, sem cotação:** a ponte no painel das réguas (PCB 1,2 mm, mesmo pedido) e o cabo de 100 mm são os dois pontos fracos: a JLCPCB pode recusar peça "nua" misturada no painel econômico (a testar na cotação); o plano B da ponte é uma tira de 10 PCBs de 0,8 mm à parte (~US$ 3-8).
- **Recomendação (o J decide; D fica como reserva): G.** Réguas todas iguais (mesmo PCB), sem solda entre réguas, 20 juntas só no pigtail de entrada (feitas uma vez, com ferro, na bancada), troca de régua = puxar a régua para baixo. Riscos a medir no protótipo: folga de 0,7 mm sob a ponte na fileira 1, retenção do encaixe de 1,27 mm com vibração, resistência de contato de 5 pinos em série com +3V3/GND (1 A por pino, ficha), fêmea H3,4 sem footprint (use o do H4.3 e confira no desenho do fabricante).

### J2 da régua (item 2 da SPEC)
Segue o item 1: **na G os dois SH saem da régua** (J1 e J2 viram as duas fêmeas 1x5 de 1,27 mm, mesma peça); o SH deixa de existir nas réguas (-1 tipo Extended nas réguas; +2 = fêmea e macho). Economia pelo SH: o J2 (~US$ 0,08 por régua) deixa de importar. **Pendente (não aplicado):** o esquema e o posicionamento da régua (`pcb/regua/`) ainda são os da R5V4 (SH-6 em J1/J2, pads LK1/LK2); só mudo depois que o J escolher G, para não refazer a régua duas vezes.

### Microfone em J302 (item 5, aplicado: pequena mudança)
- **O pino 3 (contato da ponta) do PJ-327A não chega ao Teensy e não resolveria:** diria "tem plugue", não "tem microfone". **Falta algo na placa: sim, uma tomada de CC.** Mudança: **R306 100 k (MIC_J -> MIC_DET) + C311 100 nF (MIC_DET -> GND)**, MIC_DET no **pino 25** (ADC); o VOL_SW, que estava no 25, passa para o **pino 4** (livre, só digital). Duas peças Basic 0402 (C25741, C1525), sem tipo Extended novo.
- **Como distingue:** com o MIC_BIAS ligado (3,0 V, resistência total 4,2 k), sem carga MIC_J fica em 3,0 V; eletreto de 0,1 / 0,3 / 0,5 mA dá 2,6 / 1,7 / 0,9 V; dinâmico ~0,14 V. **Regra para a firmware: 0,30 V < v < 2,85 V = microfone de eletreto (liga os efeitos de voz); v >= 2,85 V = nada ou plugue de linha acoplado por capacitor (efeitos desligados); v <= 0,30 V = curto/fonte de baixa resistência (não liga).** Plugue de linha com saída DC-coupled e baixa impedância cairia na terceira faixa: tratado como "sem microfone" (o que se quer). Os limiares são **cálculo, a medir na primeira placa** com um eletreto e uma linha.
- **Limite:** microfone de PC com bias no **anel** (J302 pino 6 NC) não funciona; só cápsula na ponta (headset mono). Pergunta abaixo.
- Estado: `schematic.py` (**ERC 0/0**, netlist igual à V3 fora das mudanças listadas), `posiciona_v4.py` (R306, C311 no fundo ao lado do C309; **DRC sem trilhas: 0 erros, 1 aviso `isolated_copper` do plano +3V3 sem vias (como antes), paridade 0**), `bom_v4.csv` (79 peças, 13 tipos Extended, US$ 17,87). **A programação deve ler `pcb/PINOS.md` (seção "R6V4"): VOL_SW no pino 4, MIC_DET no 25.**

### Arquivos 32 teclas (item 4)
`geometria.py`: `ROWS` com 8 teclas por fileira (rows 2 e 4 em x 89,2; 1 e 3 em 98,45), `CASE` = 244 x 100 mm (R6V4: +4 mm de deck; 48/64/80: 318/392/466). `pcb/grade_fab.py` (a grade única do F1, com contorno de 32 teclas) foi regenerada como `fab/student_v04_grade_contorno32_gerbers.zip` (181,85 x 91,16 mm, 32 furos de botão, DRC 0 erros) **só como alternativa**: o contorno + 21,5 mm passa de x = 249 e **não cabe no case de 244 mm** (na F2 a grade é a grade-régua, que não depende do número de teclas). Painéis e Gerbers das réguas não mudam (`fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/`). `pcb/PINOS.md` corrigido para 32/48/64/80.

### Figuras desta revisão (todas com o nome da nota em cada tecla)
`pcb/regua/img/conectores_E1.png` (E1: inviável), **`conectores_E2.png`** (recomendada: planta e corte), `conectores_entrada.png` (placa -> 1ª régua: planta e corte com os degraus), `conectores_descartadas.png` (E3 FFC e E4 mola), **`conectores_teclado32.png`** (32 teclas, C azul, F laranja, fêmeas, 4 pontes, 4 pigtails). Reproduz: venv CadQuery `pcb/regua/conectores_r6.py`; custo: `python pcb/regua/custo_r6.py`.

### Perguntas para o design (R6V4)
1. A ponte e as duas fêmeas ocupam a **faixa de trás** (v -6,9..-1,05, 6,76 x 5,2 mm por fêmea; ponte de 18,2 x 6,8 mm) e descem **6,2 mm** sob a régua: o bolso da fileira 1 (6,9) tem folga de **0,7 mm**. Cabe o rebaixo de 18,5 x 7 mm no piso que prenda a ponte (retenção contra vibração)? E a janela de plugue do J1/J2 (e o entalhe da trilha da fileira seguinte) deixa de ser necessária: o design confirma que pode sumir?
2. O pigtail de entrada (25 mm, plugue SH + macho) segue o contrato da R4V4 (J601..J604 em x 77,4 boca +x; IN da régua em u 5,6 na faixa de trás)? O macho fica sob a régua com 6,2 mm de altura na fileira 1 (a mais apertada): cabe no desenho do design?
3. Com a G, a régua perde o SH (J1/J2 viram fêmeas 1x5): o design aprova trocar o contrato (boca para baixo, não para trás)? O plugue de 7,6 x 5,0 sai do bolso.
4. J (gestão): microfone de PC com bias no anel deve ser aceito (ligar o anel ao MIC_J exige trocar o jack ou o fio)?

## R5V4 · teclado de 32 teclas e ligação das réguas (tarefas 2 e 3)

Nada foi roteado, encomendado nem gerado para encomenda. Detalhe, planta e corte de cada opção, e o contrato para o design: **`POSICIONAMENTO.md`, parte 3 (seções 10 a 12)**. Figuras em `pcb/regua/img/`: `ligacao_D.png` (recomendada), `ligacao_A.png`, `ligacao_Astock.png`, `ligacao_B.png`, `ligacao_C.png` e `ligacao_teclado32.png` (32 teclas, nome de cada nota, C azul e F laranja, as 8 ligações). Números: `pcb/regua/ligacao.json` e `calculos_eletronica.json` (`escala_R5V4`). Reproduz: `python pcb/regua/schematic_regua.py`, KiCad python `pcb/regua/posiciona_regua.py`, venv CadQuery `pcb/regua/ligacao.py`, `python calculos_eletronica.py`.

**Recomendação: D (misto).** 4 cabos SH-6 de **25 mm** da placa à 1ª régua de cada fileira + **elo soldado de 5 fios** (28-30 AWG, 7 mm, entre 5 pads por ponta) entre réguas da mesma fileira.
- **Achado:** nenhum cabo SH-6 de estoque serve. O mais curto com plugue nas duas pontas é de **100 mm** ([Pololu #5543](https://www.pololu.com/product/5543), US$ 3,32; [Pimoroni](https://shop.pimoroni.com/products/jst-sh-cable-6-pin) 100 mm); sobrariam 88 mm (elo) e 75 mm (placa); o laço (~20-28 mm) não cabe no bolso de 6,9 mm. 15/25 mm só sob medida (sem cotação; referência: 300 mm, lote de 50, US$ 152,5 numa loja). FFC/FPC (C): jumper [Molex 150390201](https://www.molex.com/en-us/products/series-chart/15039) de 31 mm; conector FPC 1,0 mm de 6 vias em estoque na JLCPCB: não achei (C48735, estoque 0); mais 1 tipo Extended.
- **Custo da ligação (32 teclas, 8 ligações):** A com cabo de estoque US$ 26,6 (não cabe) / ~US$ 150 (lote de 50 sob medida, referência); B ~US$ 4; C ~US$ 2,4 + 6,18 de Extended; D ~US$ 36 (4 cabos crimpados em casa, ferramenta de US$ 30 que fica) ou ~US$ 154 (lote de 50) + US$ 4 de fio.
- **Montagem em casa (32 teclas), estimativa:** A ~12 min; B ~40 min (80 juntas de solda a 1,0 mm); C ~24 min; D ~26 min (40 juntas + 4 plugues); cada módulo de +16 teclas: +4 elos, +20 min em B/D.
- **Troca de régua:** A e D fáceis (D: dessoldar 5 fios); B e C pior. **Placa principal: D não muda** J601-J604; B os troca por pads; C por FPC.
- **Régua (contrato):** J1 (cabo da placa) como na R4V4 (u 5,9, v -3,95, boca para trás); **novos LK1/LK2: 5 pads de 1,4 x 0,7 mm a 1,0 mm em u = 2,1 e 71,9, v -0,4..3,6**, no fundo; J2 fica (sem cabo na D) só para a régua aceitar a opção A sem mexer. ERC 0/0, paridade 0, **DRC sem trilhas: 0 erros, 0 avisos**, 60 ligações faltando; BOM igual (3 tipos Extended); `bom_regua.csv`, painel e CPL provisório atualizados (LK não entra no CPL).

**32 teclas (item 1 da SPEC):** as 8 réguas já tinham 4 sensores cada: a eletrônica **não muda**; passam a ser **8 teclas em todas as fileiras**, fileira 4 de F#3 a D#5 (a régua dela começa em x 79,95). Mapa de notas: `FIRST_NOTE = {57, 55, 56, 54}` (só a fileira 4 mudou, era 57). **Cadeia de registradores: nada a ajustar** (8 estágios por régua, 4 mortos QE..QH, 8 x N + 1 pulsos: 17 / 25 / 33 / 41 em 32 / 48 / 64 / 80 teclas, varredura de 0,56 / 0,84 / 1,12 / 1,40 ms). `pcb/PINOS.md` atualizado (a programação ajusta `V4_KEYS`, `FIRST_NOTE` da fileira 4 e as 8 teclas por fileira; pinos iguais).

**Custo para 32 teclas (US$, F2, pedido mínimo de 10 réguas montadas, sem frete, estimativas como na R2V4):** **296,6-370,3** sem a ligação (+4 teclas Gateron 3,5-3,8, +4 botões do design; a linha "cabos" de 3-8 sai); com a recomendada D: **333-407** (cabos crimpados) ou **451-524** (lote de 50 sob medida); com B: **301-374**. Escalas (sem ligação, sem o case do design): **48 teclas 322-397** (15 réguas montadas), **64: 348-424** (20), **80: 362-439** (20). O preço do case de 48/64/80 teclas é do design.

**Cuidado com o que ficou por conferir:** o conector J1/J2 mede 4,3 mm de altura **(conferir)**; a altura do fio + solda sob a régua (~1 mm) e o vão sob a junção são do design; o tempo de montagem é meu palpite, sem protótipo; o lote de 50 cabos é só uma referência de preço (não cotei 15/25 mm); as medidas do FPC (C) não foram conferidas em desenho de fabricante.

## R4V4 · Fase B da régua e da grade-régua, planta do portão P (tarefas 1, 3 e 4)

Nada foi roteado, encomendado ou impresso. Detalhe, figuras e o contrato proposto ao design em **`POSICIONAMENTO.md`** (partes 1 e 2).
- **Esquema da régua** (`pcb/regua/schematic_regua.py`, `kicad/regua/`): 4 TMAG5253BA3 (X2SON-4), 1 registrador 595, 2 SH-6, 6 capacitores, 1 x 100 ohm; **ERC 0/0**, netlist igual ao declarado. O OUT do TMAG virou pino `tri_state` no símbolo (a saída é Hi-Z desligada: o ERC reclamava de "output contra output").
- **Troca do 595 (R4V4):** o SOIC-16 (C5947, Basic, 6,9 mm de pads) **não cabe na régua de 14 mm** com furos de pino a 10,16 mm: vão livre de 6,64 mm entre pinos vizinhos e 5,8 mm em cada metade. **74HC595BQ,115 (C730243), DHVQFN-16 2,5 x 3,5, Extended, US$ 0,176 (0,135 a 50)**, 137 412 em estoque. Custo: +1 tipo Extended nas réguas (**3 x 3,09 = 9,27**, antes 6,18) e +US$ 0,08 por régua. TSSOP-16 (C5948) tem 7,2 mm de pads: não serve. Footprint KiCad `DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm`, pad 17 = GND; **(conferir)** os pads contra o EasyEDA (`cpl_jlc.py`) depois do portão.
- **Posicionamento da régua** (`posiciona_regua.py`): 14 peças só no fundo, nada no topo; J1/J2 no fundo em **u = 5,9 / 68,1, boca para trás (contrato do design, `FIT_CHECK.md` §3; alinhado: DRC 0/0/0)**, na faixa de trás, longe dos furos de pino; o 595 na frente em u = 27,75. A régua leva **3 furos M2** (18,5, 37, 55,5): cada fileira usa 2 (contrato do design). Furos Ø2,2 para M2, pinos Ø1,70, entalhes de 2,0 x 4,3. **DRC 0 erros, 0 avisos, paridade 0** (51 ligações faltando, sem trilhas).
- **Grade-régua:** a largura de 14,0 mm do contrato anterior **não existe**: as aberturas já têm 14,00 mm. Fiz **16,0 mm** (1,0 mm de borda, 4,5 mm entre aberturas). Pergunta ao design. FR-4 1,6 mm, 2 camadas **sem cobre**, painel de 5 de **83,6 x 98 mm** (trilhos de 3 mm, sem montagem): **Gerbers prontos** em `fab/student_v04_grade_regua_painel_gerbers.zip`.
- **Painel de réguas:** 5 tiras, **87,6 x 92 mm** (o design dizia 88 x 84 sem contar os dois vãos e as abas), trilhos de 5 mm, abas de 3 mm com microfuros, fiduciais e furos de ferramenta; `fab_regua.py` replica a régua no painel (inclusive as trilhas, quando existirem). Os Gerbers atuais são **de conferência** (`fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/`, com CPL provisório). **Não confirmado** que a montagem econômica da JLCPCB aceite o painel do cliente com abas e microfuros (risco aceito, a testar na cotação).
- **Custo atualizado** (`calculos_eletronica.py`, preços de 21 nov): régua US$ 2,33 de peças (10 montadas: 23,28). **F2, 28 teclas: US$ 296-375** (a troca do 595 move ~US$ 4 no cenário baixo); com a grade-régua (2-8, **estimativa**, painel de 83,6 x 98 mm dentro de 100 x 100) e a ferragem (2-4): **300-387, contra F1 332-477: -10 % a -19 %**. +16 teclas: 13,72 de eletrônica no mesmo pedido.
- **J401 (tela):** a boca aponta para −y (confirmado: o plugue de 7,6 x 5,0 ocupa y 21,2..26,2). Os fios saem do plugue a y ≈ 20,7, **depois** da fenda antiga (22,17..24,67, que ficava sob o plugue): movi a fenda para **x 45,45..52,45, y 18,17..20,67** e reservei a área do plugue (DRC 0 erros, paridade 0). O design ajusta a fenda da tampa.
- **Placa principal:** J602 passou para a borda como os outros (a régua tem o conector por baixo e a área de plugue de 6,5 x 10,4 mm saiu); USB-C em y 10 e módulo/H101 5,5 mm à esquerda, como aprovado; resto igual (DRC 0 erros, paridade 0, BOM com os mesmos 13 tipos Extended). Blocos coloridos em `pcb/img/principal_blocos_{topo,fundo}.png`.
- Correção de números das seções 5.4 e 5.5 (R2V4): painel 88 x 84 -> **87,6 x 92**; furo de localização Ø2,4 -> **Ø2,2** (R3V4); o 595 e os conectores não ficam nas pontas (acima). O resto vale.

## R3V4 · painel régua + grade-régua e Fase B da placa principal

### R3.1 Painel régua + grade-régua (tarefa 4)
Sem o contrato do design (o `FIT_CHECK.md` ainda não define a grade-régua), usei o que o Chat pediu: **74 x 14 mm, mesmo contorno da régua**, 4 aberturas de 14,00 mm, FR-4, destacável por furinhos.
| | Só réguas (R2V4) | Régua + grade-régua no **mesmo painel** (1,2 mm) | Grade-régua em **pedido separado** (1,5/1,6 mm) |
|---|---|---|---|
| Painel | 5 réguas, 88 x 84 mm | 10 tiras (5 + 5): 84 x 168 ou lado a lado **160 x 84 mm** | réguas 88 x 84 + 5 grades 88 x 84 |
| Área / painel | 7 392 mm2 | 13 440 mm2 (1,8x), passa de 100 x 100 | 7 392 + 7 392 mm2 |
| 28 teclas (8 + 8) | 2 painéis | 2 painéis (sobram 2 + 2) | 2 painéis de régua + 2 de grade |
| Preço PCB (**estimativa**, 2 camadas, 5 painéis) | US$ 5-12 | **US$ 10-24** | US$ 5-12 + 4-10 (sem taxa de engenharia extra se 2 camadas lisas) |
| Espessura da grade | = régua, 1,2 mm | **1,2 mm** (o design confere o encaixe das presilhas) | 1,5 ou 1,6 mm, à escolha |
| Tipos Extended | 2 | 2 (a grade não leva peça) | 2 + 0 |
**A montagem econômica aceita partes sem componentes no painel?** Não consegui confirmar sem subir os arquivos: a JLCPCB monta só o que está no BOM/CPL, e painel do cliente com mouse bites é opção documentada; **não confirmado que a *econômica* aceite tiras vazias**. Risco aceito, a testar na cotação: se recusar, a grade-régua vai em pedido à parte (coluna 3), sem montagem. Os 2 mm entre tiras e os trilhos de 5 mm valem igual. **Recomendação:** pedido separado se o design achar que 1,2 mm não segura a tecla sem folga (a distância ímã-sensor da régua fica em 1,2 mm); painel único se 1,2 mm servir (menos pedidos, mesma taxa).

### R3.2 Esquema da placa principal (tarefa 5) · `pcb/schematic.py`, ERC 0/0, netlist OK, igual à V3 fora das mudanças listadas
- Folhas P, E, F, I, A como na V3; folha **R** nova: J601..J604 (JST SH 6 vias, clone XYECONN C56123098: 1 +3V3, 2 GND, 3 OUT_Rk, 4 SCAN_CLK, 5 SCAN_DATA, 6 reservado), pull-downs R601..R604 100 k, séries R605/R606 100 ohm (CLK/DATA comuns às 4 fileiras). **Sem sensores nem multiplexadores**; o 74HC595 fica nas réguas.
- Pinos como `pcb/PINOS.md` (14/15/26/27 = OUT_R1..4, 2/3 = DATA/CLK, CHG_STAT no 0). ADC1 e ADC2 em paralelo: os pinos 14, 15, 26, 27 são pads AD_B1 do RT1062, que ligam aos dois ADCs.
- **Tela**: J401 passou a ser o mesmo SH de 6 vias (4 usadas; pino 1 = +3V3 como nas fileiras, então um plugue trocado nunca inverte a alimentação).
- **Microfone** (datasheet do SGTL5000): MIC_BIAS 1,25-3,0 V, máx. VDDA - 0,2 V; BIAS_RESISTOR 2/4/8 k (0 desliga); ganho 0/20/30/40 dB; acoplamento série; Fig. 20 mostra 0,1 uF no MIC_BIAS: **adicionei C310**. R305 2,2 k fica (total 4,2 k com o resistor interno de 2 k da biblioteca; pode virar 0 ohm). C309 mantido em 1 uF (datasheet usa 0,1 uF). Falta: Zin do MIC **(conferir)**.
- **Alto-falante**: Dayton CE28MB-8 nos pads de J501; MAX98357A a 9 dB, VSYS 3,0-4,4 V: potência máxima ~0,8 W em 8 ohm, abaixo do 1 W RMS do alto-falante.
- **BOM** `bom_v4.csv`: 77 peças JLC, **13 tipos Extended** na principal (+ TMAG e SH-6 nas réguas = 15 < 17), peças US$ 17,87 por placa. Arquivos renomeados para V4 (`student_v04.*`, `pcb/schematic.py`, `pcb/posiciona_v4.py`, `bom_v4.py`).

### R3.3 Posicionamento (tarefa 5): resumo, detalhes em `POSICIONAMENTO.md`
75 x 95,1 mm, 77 peças no fundo, DRC sem trilhas **0 erros de courtyard/furos, paridade 0**, USB-C a **6,75 mm** dos pads 3/5, par **~7,1 mm**, In2 = GND inteira, corredores e regras no `.kicad_dru`. **Isto não é aprovação: o J aprova o portão P.**

### R3.4 O que a programação precisa ajustar (`pcb/PINOS.md` final)
Pulsos do acesso aleatório = **8 x N + 1** por fileira (a R2V4 dizia 160 para 20 colunas: errado); coluna 0 = régua mais perto da principal; **`FIRST_COL = {0,0,0,0}`** (as posições sem tecla ficam no fim da fileira, como no modelo do design); microfone pelo MIC do codec; J401 é SH-6.

### R3.5 Atualização do design (FIT_CHECK seção 5): grade-régua própria, custo e faixa do TMAG5253
- **Contrato novo:** grade-régua **73,6 x 14 x 1,6 mm FR-4 em desenho e pedido próprios** (1,2 mm não segura a KS-20); régua 74 x 14 x 1,2 com **furos Ø2,2 para M2** em (18,5; +5,2) e (55,5; +5,2); painel de 5. Isto **substitui** a coluna "mesmo painel" da R3.1 (a opção vira a de pedido separado, já recomendada). A régua não muda de espessura, então a distância ímã-sensor continua a da V3.
- **Custo da grade (estimativa, sem cotação):** 2 camadas lisas, só FR-4 e furos, **sem montagem**. Painel de 5 grades (88 x 84 mm, mesma geometria do de réguas), pedido mínimo de 5 painéis = 25 grades (28 teclas usam 8; 44 usam 12): **US$ 2-8** (placa de 100 x 100 de 2 camadas a US$ 2 na tabela da JLCPCB; mais caro se 1,6 mm e área maior). **Taxa de engenharia:** a de US$ 25 da cotação da V3 era de placa de 4 camadas; para 2 camadas lisas não a espero, mas **não confirmado**: pior caso +25. Frete junto com os outros pedidos. Parafusos M2 não magnéticos (16 x ~US$ 0,10) + porcas: +US$ 2-4.
- **F2 total, 28 teclas (R2V4 292-371):** + grade 2-8 + ferragem das réguas 2-4 = **US$ 296-383** (pior caso com taxa de engenharia da grade: 408), contra F1 332-477: **-11 % (baixo) a -20 % (alto)**; no pior caso, -14 %. Continua dentro do critério de 25 %.
- **Faixa do TMAG5253 BA3 (datasheet, SBASAI5E): linear +-80 mT** (BA1 +-20, BA2 +-40, BA4 +-160), 15 mV/mT (12,75-17,25) a 3,3 V, Vq 1,65 V (1,61-1,69). **O "+-60 mT" da linha 157 estava errado** (o do BA1 é 60 mV/mT). Com 15 mV/mT x 110 mT daria +-1,65 V, mas esse é o limite teórico do swing, não a faixa linear garantida. A KS-20 dá 90,5 +-8 mT no fundo (905 Gs): **passa dos 80 mT lineares em até 18 mT**; ao fundo a saída vai a ~3,0 V (3,1 V no máximo), ainda sem saturar no trilho (a curva de linearidade, Fig. 6-3, não foi lida aqui), mas **na última fração do curso a resposta deixa de ser linear**. A firmware calibra o repouso e o fundo por tecla (EEPROM) e usa os limiares de 45 % / 30 %, então o efeito é de curva, não de tecla morta; o disparo e o velocity (12 %->45 %) ficam longe do fundo. **Risco aceito, a medir na primeira placa.** Fallback: **BA4 (+-160 mT, 7,5 mV/mT)**: 90 mT dá +-0,68 V (metade da resolução), mesmo footprint e mesmo preço de classe (Extended, conferir código LCSC).

### Perguntas para o design (R3V4)
1. Furo do USB-C na parede da esquerda em **y 10** (era 16) e módulo/H101 5,5 mm à esquerda, ou USB na parede de trás?
2. Posição dos furos M2 da placa principal (propus H1 em 62;48) e fenda do cabo da tela (45..52; 22..25).
3. Régua da fileira 2 começa em x 79,95 (só 2,5 mm da borda da placa): conector da régua e plugues a 9 mm um do outro, boca do conector da régua?
4. Grade-régua: 1,2 mm segura a KS-20 sem folga? Define painel único ou pedido separado (R3.1).

## 0. Resumo

| Pergunta | Resposta |
|---|---|
| A varredura sem multiplexador funciona? | **Sim.** TMAG5253 BA3: liga em 20 us típico, **45 us máximo** (a 95 %). Com 60 us de espera + 6 us de leitura: **28 teclas em 0,56 ms, 76 em 1,4 ms** (a V3 ~0,25 ms, estimativa). Velocity pede interpolação e varredura rápida da coluna "quente" (§2). |
| OUT compartilhado aguenta? | **Sim:** 20 sensores + trilha + cabos = **~490 pF** estimados, limite do datasheet 1000 pF. |
| Corrente | 4 sensores ligados: **10,4 mA típico, 20 mA máximo** (V3: 36 mA típico, 14 sensores). |
| Pinos | Sobram: usa 27 dos 46; **livres 1, 4, 5, 13, 29-45**. Cabe 76 teclas, e 8 linhas OUT se for preciso. |
| Registrador | **74HC595D, LCSC C5947, SO-16, é Basic** (US$ 0,10). Os 74HC164 e 4094 são todos Extended. |
| Custo F2 x F1 (28 teclas, pedido mínimo, sem frete) | **F2 US$ 292-371 (com a impressão MJF real do design, US$ 51,2), F1 US$ 332-477: F2 sai 12 a 22 % mais barata, não mais cara.** Passa no critério de 25 % com folga (§3). (O design cita 296-375: diferença de ~US$ 4 em ferragem.) |
| Custo de +16 teclas na F2 | eletrônica **~US$ 13** (4 réguas no mesmo pedido) + teclas US$ 14,6; ver §3.4. |
| Par USB | ≤ 10 mm, B.Cu sobre In2 (GND inteiro), **w 0,24 / s 0,15 mm = 91 ohm** no empilhamento JLC04121H-7628 (§4). |
| Régua | 4 sensores + 1 595 + 2 conectores JST SH 6 vias (clone XYECONN, US$ 0,07), 2 camadas, **74 x 14 x 1,2 mm, painel de 5 (88 x 84 mm)** (§5). |
| Alto-falante real | **Dayton Audio CE28MB-8**: Ø 28 x 4,5 mm, Fs 623 Hz, Qts 1,63, Vas 21,5 cm3 (§1.3). |

## 1. E1 · a BOM da V3, linha a linha

Fonte: `student_v03/bom_v3.csv` (34 linhas, 130 peças, 17 tipos Extended) e preços de 21 nov (`precos_jlc.json`).
"Basic" = sem taxa de US$ 3,09 por tipo. Pacote x footprint: as linhas da V3 já foram conferidas pelo `cpl_jlc.py` e pela
`AUDITORIA.md` da V3 e **não mudam**; os dois códigos novos estão marcados.

### 1.1 Linhas que ficam, e se há Basic

| Linha (código LCSC) | Classe | Existe Basic equivalente? | Decisão na F2 |
|---|---|---|---|
| 100 nF C1525, 1 uF C52923, 2,2 uF C12530, 10 uF C19702 / C15850 | Basic | já são | ficam; 41 de 100 nF caem para 10 na principal (31 vão para as réguas ou somem) |
| Resistores C25076, C25905, C25879, C25867, C25744, C25741, C26083, ferrite C1002, BAV70 C68978, AO3401A C15127, TS-1187A C318884 | Basic | já são | ficam |
| SMF5.0A C151296 (D201, TVS) | Extended | **não**: SMAJ5.0A (C113952, SMA) também é Extended e maior | fica (decisão do J: TVS e USBLC6 ficam) |
| USBLC6-2SC6 C7519 | Extended | **não** (UMW C2687116 e TECH PUBLIC C558442 também Extended, US$ 0,05 contra 0,16: só preço) | fica; trocar por UMW economiza US$ 0,2, sem relevância |
| J202 JST PH 3 vias C265101 (bateria) | Extended | não (clones PH2.0 C668618/C668620 também Extended; só 2 vias nas buscas) | fica o JST original (plugue da bateria) |
| J401 SM04B-SRSS-TB C160404 (tela) | Extended | não | fica; **ou** usar o mesmo SH de 6 vias da régua e um cabo de 6 fios (corta 1 tipo, US$ 3,09) |
| J301/J302 PJ-327A XUNPU C49284723 | Extended | não há jack 3,5 mm Basic | fica |
| L201 2,2 uH C167825 (FNR4020S) | Extended | não (os 2,2 uH baratos são 0603/0805 de sinal, sem a corrente do TPS63001) | fica |
| J101 M.2 C48985906 | Extended | não | fica; **pacote x footprint conferido na V3** |
| U301 SGTL5000 C2651833, U501 MAX98357A C910544, U204 TPS63001 C28060, U202 BQ24074 C54313 | Extended | não há equivalente Basic | ficam |
| U302 XC6206P182MR C347373 (1,8 V do codec) | Extended | não: ME6211C18M5G-N (C236671) e AP2112K-1.8 (C176944) também Extended | fica |
| J201 USB-C HRO C165948 | Extended | não | fica |
| TMAG5253BA3 C22401868 | Extended | não | fica, agora só nas réguas (1 tipo no pedido das réguas) |
| EC11E18244AU C202365 (casa) | Extended | n/a | solda em casa, fora do pedido |

### 1.2 Linhas que somem da placa principal na F2

| Linha | Qtd | Por quê |
|---|---:|---|
| 74HC4067PW C179326 (U601, U602) | 2 | sem multiplexador (E2) |
| 74LVC1G04 C7827, 74LVC1G08 C7666 (U603-U605) | 3 | só geravam EN_A/EN_B a partir de S3 e SENS_EN |
| TMAG5253 (U701-U728) e os 28 x 100 nF C7xx | 28 + 28 | vão para as réguas (32 sensores: 8 réguas x 4) |
| C601-C603 | 3 | decoupling dos multiplexadores |

**Resultado: 17 tipos Extended na F1 caem para 14 na principal (13 + o conector SH-6) mais 2 nas réguas (TMAG e SH-6), 16 no total.** A meta da R1V4
("menos que 17") é cumprida por 1 tipo, e por 2 se o SH-6 servir também à tela (J401), **sem perder função**.

### 1.3 O que entra de novo (códigos conferidos na biblioteca da JLCPCB, 21 nov)

| Peça | Código | Classe | Estoque | Preço | Observação |
|---|---|---|---:|---|---|
| 74HC595D,118 (Nexperia), SO-16 | **C5947** | **Basic** | 305 318 | US$ 0,10 (0,08 a 50) | footprint SOIC-16 de 3,9 mm de corpo **(conferir pads no EasyEDA, como o `cpl_jlc.py` faz)** |
| Conector SH 6 vias, lateral, 1,0 mm (XYECONN XY-SM06B-SRSS-TB) | **C56123098** | Extended | 5 971 | US$ 0,069 (0,055 a 100) | clone do JST SM06B-SRSS-TB; o original C160405 custa US$ 0,90. **Clone: conferir o footprint e o ajuste do plugue** |
| Alternativas de conector | C225115 (CJT 1,25 mm, 6 vias, US$ 0,12), C38036 (1,25 mm, US$ 0,07), C48735 (FPC 1,0 mm, **estoque 0**) | Extended | | | só Extended: nenhuma é Basic |

**Alto-falante real (decisão 7): Dayton Audio CE28MB-8** ([folha de dados](https://www.daytonaudio.com/images/resources/285-147--dayton-audio-ce28mb-8-spec-sheet.pdf)):
Ø 28 mm x 4,5 mm (cabe nos 5 mm da V3), 8 ohm, Re 7,54 ohm, Le 0,45 mH, **Fs 623 Hz, Qms 2,22, Qes 6,16, Qts 1,63**, **Vas 0,0215 L**, Sd 4,52 cm2, Xmax 0,1 mm,
Mms 0,087 g, SPL 81 dB a 2,83 V/1 m, 1 W RMS / 2 W máx., resposta 620 Hz-20 kHz. Fios soldados em J501 (como na V3). Não está na JLCPCB: compra em loja (preço ~US$ 5-8, estimativa).
**Alternativas com folha de dados** (resultados de busca; **não conferidas aqui**): Visaton K 28 WP-8 (Fs 700 Hz, 76 dB), Same Sky CLS0281 (Fs 500 Hz), Taoglas SPKM.28.8.A (Fs 580 Hz).
Para a caixa: Vas 21,5 cm3 com Qts 1,63 é um alto-falante **sem graves** por natureza; a caixa de 9,75 cm3 da V3 coloca a ressonância perto de 1 kHz
(estudo `estudos/acustica.py` do design); isso vale para qualquer 28 mm. **(conferir: refazer `acustica.py` com estes parâmetros é tarefa do design.)**

## 2. E2 · varredura sem multiplexador (R1V4 §5.2)

Datasheet: [TMAG5253](https://www.ti.com/lit/ds/symlink/tmag5253.pdf) (SBASAI5E, rev. abr 2026; lido em PDF).

### 2.1 Valores do datasheet que entram nas contas

| Parâmetro | BAx (bipolar, o BA3 da V3) | UAx (unipolar) |
|---|---|---|
| tON, do EN subir até OUT a 95 % (CLoad 100 pF) | **20 us típico, 45 us máximo** | 55 / **130 us** |
| Corrente ativa a 3,3 V | 2,6 mA típico, 5 mA máximo | 1,9-2,6 típico, 3,3-4 máx. |
| Corrente desligado (EN baixo) | 8 nA típico | idem |
| Largura de banda | 15 kHz (-3 dB) | idem |
| Resistência de saída | ativo 1,27 (ohm); desligado 9 (Mohm); **a coluna de unidades saiu embaralhada na extração do PDF: (conferir)** | |
| Carga capacitiva | até **1 nF** na saída | |
| Sensibilidade BA3, 3,3 V | 15 mV/mT, repouso 1,65 V (1,61-1,69) | |

A SPEC cita < 25 us (bipolar) e < 60 us (unipolar) como típicos; o datasheet lido (rev. abr 2026) dá 20 / 55 us típicos e **45 / 130 us máximos**; a conta usa o máximo.
Com o BA3 da V3, a conta usa **45 us**. (Se alguém trocar para a variante unipolar, a varredura de 28 teclas passa de 0,56 para ~1,5 ms.)

### 2.2 Princípio

```
                       OUT_R1 ----------- (14)  fileira 1 (frente): 1 fio analógico, 7 ou 8 ... 19 sensores em paralelo
 MicroMod Teensy ----- OUT_R2 ----------- (15)  fileira 2
                       OUT_R3 ----------- (26)  fileira 3
                       OUT_R4 ----------- (27)  fileira 4
                       SCAN_CLK ---------- (3)  \  comuns às 4 fileiras
                       SCAN_DATA --------- (2)  /

 fileira k:  [principal]--cabo--[régua 1: 595 + 4 TMAG]--cabo--[régua 2: ...]--cabo--[...]
                                 SER->QA QB QC QD (EN dos 4 sensores)   QH'-> SER da próxima
                                 OUT dos 4 sensores ligados na mesma linha OUT_Rk (barramento)
```
Ao ligar a coluna c, **um sensor por fileira** responde, cada um na sua linha OUT. As 4 linhas são lidas juntas (2 no ADC1, 2 no ADC2).

### 2.3 Tempo de varredura (45 us é o MÁXIMO do datasheet; a espera usada tem margem)

Modelo: passo = espera + leitura das 4 linhas (~6 us, 2 + 2 conversões em 2 ADCs, **estimativa**, ~3 us cada) + deslocamento do 595 (<1 us, 5 MHz).
O resíduo de assentamento usa um polo único calibrado em "95 % em 45 us" (tau = 15 us, **modelo, não medida**).

| Espera após o EN | Resíduo da coluna anterior | Passo | 28 teclas (8 colunas) | 44 (12) | 60 (16) | 76 (20) |
|---:|---:|---:|---:|---:|---:|---:|
| 45 us (o máximo, "95 %") | 5,0 % | 55 us | 0,44 ms | 0,66 | 0,88 | 1,10 |
| **60 us (valor da V3)** | **1,8 %** | **70 us** | **0,56 ms (1,8 kHz)** | 0,84 | 1,12 | **1,40 ms (0,71 kHz)** |
| 90 us (12 bits limpos) | 0,25 % | 100 us | 0,80 ms | 1,20 | 1,60 | 2,00 ms |
| 60 us com **2 linhas OUT por fileira** (pinos 38-41, **conferir**) | 1,8 % | 70 us | 0,28 ms | 0,42 | 0,56 | 0,70 ms |

Resíduo é o erro de leitura (fração da diferença entre a coluna anterior e esta). Com diferença de até ~1 V (BA3 em +-80 mT: 15 mV/mT x 80 = 1,2 V; ver R3.5), 60 us deixa até ~18 mV
(~1,2 mT); **a firmware deve ler a coluna k depois de uma coluna k-1 em repouso, ou usar 90 us**. Calibração de repouso por tecla absorve o resto.

### 2.4 Resolução de velocity

O firmware da V1 usa 1 ms = 127 e 80 ms = 1 (log): **19,9 passos de velocity por oitava de tempo**. Para o intervalo de 1 ms (o mais rápido):

| Varredura | Erro sem interpolar (+-T/2) | Interpolando entre duas leituras (+-T/8, **estimativa**) |
|---|---:|---:|
| V3, 0,25 ms | +-3,4 passos | +-0,9 |
| **F2 28 teclas, 0,56 ms** | **+-7,1** | **+-1,9** |
| F2 76 teclas, 1,4 ms | +-15,3 | +-4,6 |
| **varredura rápida da coluna quente, 0,07 ms** | +-1,0 | +-0,3 |

**Conclusão:** em 28 teclas a F2 basta **com interpolação** (+-2 passos no extremo mais rápido, igual à V3 sem interpolar). Em 76 teclas, só com **varredura rápida da
coluna quente** (ou 2 linhas OUT por fileira + interpolação). A varredura rápida é possível porque o 595 aceita **acesso aleatório**: empurrar o padrão de 8N bits
leva 160 pulsos de 200 ns = 32 us **durante** a leitura anterior ou como parte do passo (`PINOS.md`). Isso é trabalho do `programacao-som` (P1/P2).

### 2.5 Capacitância da linha OUT (limite 1 nF)

Suposições: sensor 20 pF (o próprio datasheet usa "cerca de 20 pF" para chegar a 50 sensores), trilha 0,7 pF/cm, cabo 1 pF/cm (60 mm por elo), 3 pF por conector, 5 pF no ADC
(**todos estimativa, menos os 20 pF**):

| Réguas na fileira | Sensores | C total | Margem até 1 nF |
|---:|---:|---:|---:|
| 2 (28 teclas) | 8 | ~200 pF | 5x |
| 3 (44) | 12 | ~300 pF | 3,3x |
| 4 (60) | 16 | ~390 pF | 2,5x |
| **5 (76)** | **20** | **~490 pF** | **2x** |

Com a saída ativa de 1,27 ohm e o pull-down de 100 kohm (sugerido no datasheet) a linha carrega e descarrega em ns: o limite de tempo é o tON interno, não a linha.

### 2.6 Corrente

Só 4 sensores ligados por vez: **10,4 mA típico, 20 mA máximo** (V3: 14 ligados = 36 mA típico, 70 mA máximo). Os 595 gastam < 0,1 mA cada. Com a varredura contínua
a corrente média é ~10,4 mA; em repouso (nenhuma tecla há 2 s) a firmware pode reduzir a taxa de varredura e baixar para ~1 mA. A economia sobre a V3 é ~26 mA em ~100 mA do
instrumento (ver `POWER.md` da Viaggio; um `POWER.md` da V4 vem com a Fase B).

### 2.7 Pinos do MicroMod Teensy (detalhe em `pcb/PINOS.md`)

Precisa: 4 ADC (OUT) + 2 (VBAT, HP_DET) + DADO + CLOCK + I2S (4) + I2C (2) + 2 encoders (6) + KEEP, AMP_SD, CHG_STAT. **Total 27 de 46 pinos.** Os 4 OUT ficam em
**14, 15, 26, 27** (CHG_STAT passa do 26 para o 0); todo o resto mantém o número da V3, então o firmware existente não muda de pino. 76 teclas **não pedem pino extra**.

### 2.8 CPU

Busca ocupada de 60 us por passo ocuparia 100 % do laço principal a 28 teclas; o áudio roda em interrupção e não é afetado, mas o resto do laço (MIDI, OLED) ficaria sem tempo.
**Estimativa:** com a varredura por máquina de estados (IntervalTimer a 70-100 us, 2 ISRs por passo de ~2-4 us), a carga fica em **~5 % (28 teclas) e ~8 % (76)**; a síntese do
acordeão amostrado mediu 12-20 % no Teensy 4.0 (CLAUDE.md). **Não medido:** o MicroMod não está disponível; é conta. Cabe a P1 confirmar.

## 3. E3 · verificação de custo (R2V4, item 2)

### 3.1 Base e o que é estimativa

- **Visto na biblioteca da JLCPCB em 21 nov:** preço de cada peça (por faixa de quantidade), classe Basic/Extended.
- **Da cotação do J de 18 nov (V3):** placa de 4 camadas 246,5 x 95 mm, 5 un., engenharia 25,00 + placa 14,50 = 39,50; montagem econômica pelo fundo: preparação 8,24 e estêncil 1,55; US$ 3,09 por tipo Extended.
- **Estimativa (sem cotação):** placa principal da F2 (4 camadas, ~85 x 95 mm: **US$ 14,50 a 39,50**; se a taxa de engenharia de 25 não valer para a placa menor, vai para o piso), régua 2 camadas
  (US$ 5-12), SMT e nitrogênio (3,2 por montagem, valor da página da V3), cabos SH prontos (US$ 3-8), ferragem, impressão do case da F1 (US$ 58-143 = faixa da V3, por volume). **Impressão da F2: US$ 51,2 (MJF, número do design, FIT_CHECK 12.x).** Frete, IVA e alfândega ficam de fora.
- Mínimos da JLCPCB: **2 placas montadas** e 5 placas nuas por desenho. Na F1: 1 desenho. Na F2: **2 desenhos** (principal e régua), cada um com a sua preparação e o seu estêncil.
  Uma montagem de régua = **1 painel de 5 réguas** (design fechou 88 x 84 mm); 2 painéis montados = **10 réguas** (28 teclas usam 8, sobram 2; **44 teclas usam 12: já não cabem no pedido mínimo, pedem +1 painel montado**).

### 3.2 A tabela (US$, pedido mínimo, 28 teclas; baixo-alto)

| Item | F1 plana (V3, só referência) | F2 réguas |
|---|---:|---:|
| Placa principal (PCB) | 39,50 (4L, 246,5 x 95) | 14,50-39,50 (4L, ~85 x 95) **estimativa** |
| Réguas (PCB, 5 painéis de 5) | - | 5-12 **estimativa** |
| Montagem principal: preparação + estêncil | 9,79 | 9,79 |
| Montagem réguas: preparação + estêncil | - | 9,79 |
| Tipos Extended x 3,09 | 17 tipos = 52,53 | principal 14 = 43,26 + réguas 2 = 6,18 -> **49,44** |
| Peças, 2 placas principais montadas | 65,18 | 36,04 |
| Peças, 10 réguas montadas (40 TMAG etc.) | - | 22,54 |
| SMT e nitrogênio | 3,20 | 6,40 |
| Grade FR-4 escareada | 15-30 **estimativa** | 0 (a T3 é a tampa) |
| Parafusos, porcas, pés | 10-20 **estimativa** | 6-12 **estimativa** |
| Cabos SH 6 vias (8) e conectores | 0 | 3-8 **estimativa** (conectores já nas peças) |
| Impressão do case | 58,5-143 **estimativa, V3** | **51,2 (MJF, design)** |
| **Subtotal que difere** | **253,7-363,2** | **213,7-256,7** |
| Comum às duas: teclas 25,6, módulo 27, bateria 8, OLED+cabo 10, alto-falante CE28MB-8 6,5, tela acústica 8, USB 3, kit M2,5 4, 2 encoders 4,4 | 78,6-114,0 | 78,6-114,0 |
| **Total do instrumento de 28 teclas** | **332-477** | **292-371** |
| **Diferença F2 contra F1** | | **-12 % (baixo) / -22 % (alto)**; no subtotal que difere: -16 % / -29 % |

A parte da F1 que corresponde só à eletrônica (39,50 + 9,79 + 52,53 + 65,18 + 3,2 = 170) bate com a faixa de US$ 172-183 da V3.
**Pior canto** (F2 alto 371 contra F1 baixo 332) = **+12 %**, ainda abaixo de 25 %. Para a F2 passar de F1 + 25 % no cenário central, faltaria a F2 custar **~US$ 120 a mais** em itens hoje estimados (PCB principal, painel de réguas recusado e refeito pela JLCPCB, ferragem): improvável. **Sigo sem parar (R2V4, item 2).**

### 3.3 Onde a F2 ganha e onde perde

| | Ganha | Perde |
|---|---|---|
| Placa grande de 4 camadas, grade e impressão | 0 a -25 (PCB principal menor), -15 a -30 (sem grade), impressão MJF 51,2 contra 58,5-143 | |
| Multiplexadores e lógica | -3 tipos Extended (-9,27), -29 de peças | |
| Segunda montagem (réguas) | | +9,79 de preparação, +6,18 de Extended, +3,2 de SMT, +5-12 de PCB |
| Cabos | | +3-8 |
| Flexão da placa | a régua apoiada inteira no degrau tende a 0 mm de flexão | |

**Se for preciso reduzir a F2** (não é, mas ficam as alavancas, em ordem de ganho): (a) tela no mesmo SH-6 da régua: -3,09; (b) régua e principal no **mesmo pedido**
(JLCPCB cobra a preparação por desenho: não ajuda); (c) **solda direta entre réguas** no lugar de conectores: -6,18 (tipo SH-6 das réguas) -8 de cabos, +25 min de solda em casa e perde a troca fácil (§5.2);
(d) 28 teclas usam 8 das 10 réguas montadas: 2 sobram; (e) trocar USBLC6 por clone: -0,2.

### 3.4 Custo incremental de cada módulo de +16 teclas na F2

| | US$ |
|---|---:|
| 4 réguas no mesmo pedido das primeiras (peças + PCB + 4 cabos) | **~13** |
| 4 réguas em pedido separado (10 réguas montadas) | ~52 |
| 16 teclas Gateron | 14,6 |
| 16 botões + 74 mm de case | a pedir ao design (28 teclas = 51,2) |
| Eletrônica da principal | 0 (a principal não cresce) |

As 10 réguas do pedido mínimo cobrem 28 teclas (8); **44 teclas pedem 12 réguas: +1 painel montado** (a preparação e os tipos Extended das réguas já estão pagos só se for no mesmo pedido; senão ~US$ 52). 60 teclas (16 réguas) pedem 2 painéis montados a mais.
Na F1 cada módulo alarga a placa de 4 camadas em 74 mm: o preço da PCB principal sobe com a área (estimativa não feita: fora do escopo da R2V4, que pede a F1 só no caso de 28).

## 4. E4 · par USB (R1V4 §5.4)

**Empilhamento padrão JLCPCB para 1,2 mm, 4 camadas: JLC04121H-7628** (F.Cu 35 um, prepreg 7628 de 0,2104 mm Dk 4,4, In1 15 um, núcleo 0,6, In2, prepreg 0,2104, B.Cu).
Publicado pela JLCPCB, vale **sem pedir controle de impedância**. Solver 2D da Viaggio (`viaggio/pcb/impedance.py`, comparado com IPC-2141A e com um ponto do calculador da JLCPCB):

| w (mm) | s (mm) | Zdiff (solver) | IPC-2141A |
|---:|---:|---:|---:|
| 0,20 | 0,127 | 91,7 | 98,4 |
| 0,22 | 0,127 | 88,7 | 94,2 |
| **0,24** | **0,15** | **91,2** | 93,7 |
| 0,26 | 0,15 | 88,4 | 90,0 |

**Proposta: w = 0,24 mm, s = 0,15 mm -> 91 ohm** (+-10 % na largura de fabrica = ~86-96 ohm). As camadas externas são simétricas: o par vai em **B.Cu sobre In2 = GND inteiro** (a In1 fica
para +3V3 e sinais lentos). As peças do USB (USB-C, USBLC6, J101) ficam no fundo, então **sem via**.
1. **Comprimento <= 10 mm** (V3: 17,2). Critério físico: tempo de subida do USB de alta velocidade 500 ps / (6 x 5,6 ps/mm, e_eff 2,85) = **14,8 mm** é o comprimento "elétricamente curto";
   **10 mm cabe com folga de 1,5x mesmo se a conexão negociar 480 Mbit/s.** A 12 Mbit/s (tempo de subida >= 4 ns, 118 mm) é irrelevante. Diferença entre D+ e D-: <= 0,15 mm.
2. **Referência contínua:** a In2 inteira sob o par e 1 mm de cada lado, sem fenda, sem trilha de sinal na In2 sob ele; ilhas de cobre da In2 só de GND. O pour de +3V3 da V3 na In2 **não** pode repetir.
3. **Full Speed:** é do `programacao-som` (P1): o bit PFSC do PORTSC1; se não for possível, 1 + 2 bastam.
4. **Posicionamento (Fase B):** USB-C e M.2 lado a lado. Orçamento do trecho: pad do USB-C -> USBLC6 ~2,5 mm, através do ESD ~1,5, até o pad 3/5 do J101 ~5-6 mm = **~9-10 mm. Só fecha se o USB-C ficar a <= 7 mm da linha dos pads 3/5 do M.2 (estimativa de geometria, a confirmar ao posicionar).**
   O resistor R202 do CC2 fica fora do corredor, como na V3.

É cálculo, não medida: o teste da primeira placa (velocidade negociada, MIDI contínuo) continua valendo.

## 5. E5 · a régua universal de 4 teclas (R2V4, itens 3 e 5)

### 5.1 Esquema de princípio (uma régua, tudo no fundo)

```
 Conector IN (SH 6 vias)          74HC595D (U1, SO-16)                          4 x TMAG5253BA3 (U2..U5)
 1 +3V3 ------+------------------ VCC(16)    C1 100 nF + C2 10 uF 0805 junto ao pino     VCC(1) <- +3V3, 100 nF cada
 2 GND -------+------------------ GND(8), OE(13)                                          GND(2)
 3 OUT --------+----------------- (barramento) -----------------------------------------> OUT(4) dos 4 sensores unidos
 4 CLK  --------------------------- SRCLK(11) + RCLK(12) juntos                            EN(3) <- QA(15) QB(1) QC(2) QD(3)
 5 SER  --------------------------- SER(14)         SRCLR(10) -> +3V3
 6 reservado (OUT_B)                QH'(9) -> pino 5 do conector OUT (cascata)    QE-QH (4-7): sem uso
 Conector OUT (SH 6 vias): 1 +3V3, 2 GND, 3 OUT, 4 CLK, 5 = QH' (por 100 ohm), 6 reservado -- iguais aos do IN por trilha direta
```
- 14 peças por régua: 4 TMAG, 1 595, 2 SH-6, 6 capacitores (5 x 100 nF + 1 x 10 uF), 1 x 100 ohm no QH'.
- Pull-down de 100 kohm por linha OUT e os 100 ohm de CLK/DATA ficam na **placa principal**.
- **Nada no topo da régua.** Os 4 sensores, o 595 e os conectores ficam no fundo, no bolso do degrau; no topo só as 2 furações das teclas.
- Pino 5 do conector de entrada é SER e, no de saída, QH': o cabo de elo é 1:1 e liga QH' (régua k) ao SER (régua k+1).
- **Partida:** as saídas do 595 não são Hi-Z na partida; a firmware dá 8N pulsos com DATA = 0 antes de ler. Janela de dezenas de us com colunas ligadas ao acaso: **risco aceito**
  (cada sensor leva >= 20 us para sair do desligado; a janela de pulso tem 0,1 us por estágio).

### 5.2 Forma de ligação em cadeia (elos: principal -> régua 1 -> régua 2...)

28 teclas = 8 réguas = 4 elos principal-régua 1 e 4 elos régua 1-régua 2 = **8 elos**, 20 conectores (16 nas réguas, 4 na principal).

| | **A. JST SH 6 vias + cabo pronto** (recomendada) | B. FFC/FPC 1,0 mm | C. Solda direta (barra de pinos ou fios) |
|---|---|---|---|
| Peça no pedido da JLCPCB | SH-6 lateral, clone C56123098 (US$ 0,07), **Extended** | FPC 1,0 mm C48735, **estoque 0**; outros tipos não pesquisados | nenhuma |
| Custo de 8 elos | 20 x 0,07 = 1,4 + 8 cabos SH ~US$ 3-8 (estimativa) = **~5-9** | cabos FFC 6P, 7 cm = US$ 0,06 cada (C90533, estoque 998) + conectores: ~2 | ~1 de fio/pinos |
| Tipo Extended a mais | +1 na principal e +1 nas réguas = **+6,18** | idem | **0** |
| Montagem em casa | encaixar 8 cabos: ~5 min | encaixar e travar 20 fechos ZIF: ~15 min, frágil | soldar 48 pontos: ~25 min |
| Confiabilidade | boa: trava por atrito, cabo fino; **vibração de teclado é baixa** | média: o fecho ZIF abre se mexido | **a melhor**, mas troca de régua exige dessoldar |
| Altura sob o degrau | SH lateral ~**4,3 mm (conferir no datasheet da JST)** | ~2,5 mm (FPC1.0 C48735, "PH2.5") | ~2 mm (fio) |
| Troca de régua/sensor | fácil | média | difícil |

Recomendo **A**, com C como alternativa se a diferença de 6,18 + 8 incomodar. A ordem de montagem permite A e C no mesmo projeto: os pads de C ficam ao lado do SH.
O SH exige bolso de ~4,5 mm sob as pontas da régua; a fileira 1 tem o degrau mais baixo: se o piso+degrau for menor que isso, o conector da ponta fica **fora** do apoio, pendurado na emenda. **É pergunta para o design.**

### 5.3 OUT compartilhado, cabo incluso

20 sensores + 5 réguas de trilha + 5 cabos de 60 mm + 10 conectores = **~490 pF (estimativa)** contra 1 nF do datasheet (2x de margem; ver §2.5). Cabos de 60 mm: o ideal é <= 100 mm.
Cada elo leva CLK em série pelos 5 CIs da cadeia: com 100 ohm de série e ~150 pF de carga, tau = 15 ns, bem dentro dos 200 ns por pulso.

### 5.4 Painel de réguas e montagem pelo fundo

- **Geometria (design fechou: 74 x 14,0 mm; a proposta inicial era 12):** régua de **74 x 14 mm** (4 x 18,5 de passo para o sensor ficar centrado em cada célula e o passo atravessar a emenda entre réguas), 1,2 mm, 2 camadas, cobre 1 oz.
  Largura 14 mm: o SO-16 tem 6 mm de corpo; as teclas (14 mm de corpo) apoiam nos furos e a borda pode sobrar 1 mm de cada lado (**design confere**).
- **Painel (design):** 5 réguas, **88 x 84 mm**, dentro de 100 x 100, separadas por **mouse bites** (V-cut não serve: o conector fica na borda). Dois painéis montados = 10 réguas.
- **A JLCPCB monta pelo fundo um painel assim?** A V3 já usou montagem econômica **só pelo fundo** numa placa única. **Painel feito pelo cliente com mouse bites e trilhos de 5 mm é uma opção
  documentada da JLCPCB, mas eu não consegui confirmar o aceite da montagem econômica com painel de cliente sem subir os arquivos: RISCO ACEITO, a testar na cotação.** Se recusar: pedir o painel
  pela própria JLCPCB ("Panel by JLCPCB", 1 x 6), custo da cotação.
- **Pontos de atenção:** conectores na ponta pedem trilho; fiduciais de painel (2 no trilho); o SO-16 e os X2SON de 0,5 mm de passo são do tamanho que a JLCPCB faz sem custo extra (como na V3).

### 5.5 Encaixe no degrau e distância ímã-sensor

- **Localização (design):** **2 furos de Ø 2,4 mm** em (18,5; +5,2) e (55,5; +5,2) da régua (37 mm entre eles), entalhes de 2,0 x 4,3 mm na borda de trás. Tolerância NPTH da JLCPCB (+-0,1 mm, **a confirmar**): erro de posição ~0,15 mm, do mesmo tamanho do da V3 pelos furos H1-H10. (Substitui a proposta anterior de furo redondo + oblongo a 66 mm.)
- **Bolso no degrau:** 4 bolsos de sensor (**1,8 x 2,2 x 0,8 mm**, o X2SON tem 0,4 mm de altura), 1 de 595 (**7 x 11 x 2,2 mm**, SO-16 de 1,75 mm de altura), 2 de conector (**bolso livre de 8,4 mm no design; conferir a altura do SH**).
- **Distância ímã-sensor igual à da V3:** a régua é de **1,2 mm** como a placa da V3, o sensor está no fundo dela, e a tecla se apoia na face de cima da régua pelos 2 pinos: a distância entre o ímã da KS-20 e o sensor
  é **a mesma pela construção** (espessura da placa + altura do sensor). **A tolerância de espessura da JLCPCB (+-10 % = +-0,12 mm) é a mesma da V3; a calibração do firmware (repouso por tecla medido na partida) continua valendo.**
  **(conferir)** que o degrau não encosta nos sensores (fundo do bolso).
- O degrau escalonado (passos de 2, 2 e 3 mm) só muda a **altura** da régua; a distância ímã-sensor não depende dela.

## 6. O que a programação precisa ajustar

`pcb/PINOS.md` (rascunho novo; a V3 não tinha `PINOS.md` próprio, vale o da `viaggio_micromod/pcb/PINOS.md` com estas mudanças):
1. **Somem** MUX_S0-S3 (0-3), SENS_EN (4), MUX_R_COM/L_COM (14/15) e a tabela `KEY_INPUT`: a tecla vira (fileira, coluna).
2. **OUT_R1..R4 = 14, 15, 26, 27** (ADC). **CHG_STAT: 26 -> 0.** **SCAN_DATA = 2, SCAN_CLK = 3.** O resto não muda de pino.
3. Varredura: coluna a coluna, **60 us** de espera (ou 90), leitura das 4 linhas, 8N pulsos com DATA = 0 na partida, **atraso de 1 pulso** na saída travada, **4 estágios mortos** entre réguas, acesso aleatório por padrão
   de 8N bits + 1 pulso. Detalhe e tabela de tempo em `PINOS.md`.
4. Velocity: **interpolar** o instante dos limiares e **varrer só a coluna quente** quando uma tecla sair do repouso; sem isso 76 teclas não resolvem 1 ms.
5. CPU: varredura por IntervalTimer (máquina de estados), não por espera ocupada.

## 7. Pendências e riscos aceitos

| Item | Impacto se estiver errado |
|---|---|
| Unidade da ROUT do TMAG5253 (extração do PDF embaralhada) | baixo: só afeta a carga das 19 saídas desligadas em paralelo com a ativa |
| Modelo de assentamento de 1 polo (tau 15 us) | a espera de 60 us pode precisar de 90 us; custa 0,24 ms a mais na varredura de 28 |
| Painel de réguas na montagem econômica da JLCPCB | recusa = pedido de painel pela JLCPCB (custo da cotação) |
| Altura real do SH lateral e do clone XYECONN | muda o bolso e o degrau da fileira 1 |
| Taxa de engenharia da placa principal pequena | +25 de custo (já no cenário alto) |
| Pinos 38-41 com ADC no MicroMod | só importa para 2 linhas OUT por fileira |
| Saídas do 595 na partida | microssegundos com colunas ligadas; risco baixo |
| Preço e número de impressão da F2 | design ainda não entregou |

## Perguntas para o design

1. **Conectores nas pontas da régua:** o SH 6 vias lateral tem ~4,3 mm de altura **(conferir)**. A fileira 1 tem o degrau mais baixo: cabe um bolso de ~4,5 mm sob as pontas, ou o conector fica fora do apoio, na emenda entre réguas?
2. **Emenda entre réguas:** o elo de 60 mm precisa de um canal entre réguas (ou um vão de ~10 mm). A régua de 74 mm com passo contínuo atravessa a emenda; confirme que o vão de cabo cabe sem sacrificar o degrau.
3. Régua 74 x 14 mm, 2 furos Ø 2,4 e entalhes 2,0 x 4,3: **recebido, adotado** (FIT_CHECK 12.x). Confirmar só a altura real do SH no bolso de 8,4 mm.
4. Impressão MJF da F2 = US$ 51,2: **adotada na tabela**; falta o número por módulo de +16.
5. **Posição do USB-C e do M.2 na principal:** o USB-C precisa ficar a <= 7 mm da linha dos pads 3/5 do M.2 (par <= 10 mm); isso é compatível com o lado esquerdo e a parede da F2?
6. **Alto-falante:** refazer `estudos/acustica.py` com o Dayton CE28MB-8 (Fs 623 Hz, Qts 1,63, Vas 21,5 cm3, Sd 4,52 cm2); ou prefere outro 28 mm com Fs menor?

## Perguntas para o design (R4V4)
1. **Janela do 595** (1,0 mm de altura, u 26..30, v 4,2..7 sobre o trilho da frente): ~5 x 3 mm; aceita, ou ele vai para o eixo?
2. **Grade-régua:** "73,6 x 14" com aberturas de 14,00 é impossível (sem material). Fiz **16,0 mm**; serve às presilhas e ao deck? Confirme ou dê outra largura.
3. Os 3 furos M2 por régua (18,5, 37, 55,5), usando 2 por fileira, como no contrato: confirmado.
4. Altura do SH lateral (4,3 mm, **conferir** no desenho da JST/XYECONN) e do 595 (1,0 mm).
5. O furo do USB-C em y 10 e os furos H1..H4 da principal (H1 em 62; 48): confirmados?

## Perguntas para o design (R5V4)
1. **Espaço sob a junção entre réguas** (v -0,9..4,0, u 70,9..76,8 em torno dela): fica livre de peças e de bossas da bandeja, com o poste do entalhe de ponta (u ±1, v -7..-2,7) fora do elo? O fio e a solda ficam ~1 mm abaixo da face de baixo da régua.
2. **A fileira 4 agora começa em x 79,95** (alinhada com a fileira 2). O cabo da placa (J604) à régua 1 da fileira 4 segue o mesmo contrato da fileira 2 (J1 em u 5,9, boca para trás)? Como a fileira 3 fica atrás da 2, e a fileira 4 não tem nada atrás, o plugue da fileira 4 passa sob o quê?
3. **Cabos de 25 mm (placa → 1ª régua):** o J vai cotar sob medida, crimpar em casa ou soldar (B só na placa)? Se for crimpar, o design confirma o comprimento (25 mm) e o raio da curva do feixe de 5 fios na planta atual.
4. Se o J escolher B (tudo soldado), o design aceita **retirar J601-J604 da planta** (pads na borda direita da placa, x ~75)? Isso muda só a placa principal (eu reposiciono).
5. J2 sem cabo na D deixa a janela de plugue e o entalhe de 8 mm na trilha da frente sem uso: o design pode tirá-los, ou mantém para a opção A?
