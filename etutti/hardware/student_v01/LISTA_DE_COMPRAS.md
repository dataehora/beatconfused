# eTutti Student V01 · etapa 9 · lista de compras e roteiro do pedido

15 nov 2026. **Nada foi encomendado.** Decisões do J: o mínimo de placas, teclas Orange, bateria de 3 fios, módulo MicroMod comprado depois. Preços vistos em 15 nov 2026, sem frete e sem impostos; conferir na hora.

## Quantas placas

- A JLCPCB fabrica no mínimo **5 placas**. É o menor pedido que existe.
- A montagem é feita em no mínimo **2** delas, segundo a página de protótipos da JLCPCB. A página não diz isso com todas as letras para a montagem "Standard", que é a que esta placa precisa (peças dos dois lados): **conferir o campo "PCBA Qty" na tela do pedido**.
- **Pedido: 5 placas, 2 montadas.** Uma placa montada sozinha não é uma opção que a JLCPCB ofereça, e a segunda custa só as peças (~US$ 35): as taxas fixas são as mesmas. Ela fica de reserva para o caso de uma falha de montagem ou de um acidente na bancada.
- As 3 placas nuas que sobram não têm uso prático (os chips são pequenos demais para soldar em casa).

## Pedido 1 · JLCPCB: placa com montagem

Arquivos, todos em `etutti/hardware/student_v01/fab/`:

| Campo do pedido | Arquivo ou valor |
|---|---|
| Gerbers | `student_v01_gerbers.zip` |
| BOM | `student_v01_bom.csv` |
| CPL (posições) | `student_v01_cpl.csv` |

| Parâmetro | Valor |
|---|---|
| Camadas | 4 |
| Tamanho | 246,5 × 95 mm (a página lê dos Gerbers) |
| Quantidade | 5 |
| Espessura | **1,2 mm** |
| Empilhamento | **JLC04121H-7628** |
| Acabamento | **ENIG** |
| Cor | verde |
| Vias | tampadas (tented), o padrão |
| Montagem | **Standard**, **os dois lados**, PCBA Qty **2** |
| Peças | fornecidas pela JLCPCB, todas pelo código da lista |

Roteiro na página, na ordem:

1. Enviar os Gerbers e preencher os parâmetros acima. Conferir que a página mostra 4 camadas e o contorno certo.
2. Ligar "PCB Assembly", escolher Standard, os dois lados, quantidade 2.
3. Enviar o BOM e o CPL. **Todas as 42 linhas têm de aparecer como encontradas e com estoque.** Se alguma faltar, parar e me dizer qual: há alternativas levantadas para as mais curtas (`fornecimento/FORNECIMENTO.md`, item 3).
4. **Prévia da montagem: conferir peça a peça.** É o passo que nenhuma conferência minha substitui, porque só a página mostra os modelos da JLCPCB sobre a placa. Olhar com cuidado:
   - os 28 sensores sob as teclas (U701 a U728): o ponto do pino 1 de cada um sobre a marca do pino 1 da placa;
   - o conector do módulo (J101) e o espaçador (H101);
   - o USB-C (J201), o jack (J301) e o conector da bateria (J202): a boca para fora, sobre os pads;
   - o LED (D401) e o botão Program (SW403);
   - os chips U202, U204, U301 e U501: o pino 1.
   Se uma peça aparecer girada ou deslocada, a página deixa corrigir ali mesmo. Uma captura de tela dessa prévia me basta para conferir junto.
5. Os dois encoders (SW401, SW402) são de furo passante: a página pergunta se a JLCPCB os solda à mão. Sim.
6. Ler o preço final. Deve ficar perto da estimativa abaixo; se vier muito acima, parar.

Estimativa para 5 placas com 2 montadas:

| Item | US$ |
|---|---:|
| PCB de 4 camadas, 5 unidades | ~34, mais o ENIG |
| Preparação da montagem dos dois lados | ~51 |
| Estênceis | ~17 |
| Taxa por tipo de peça estendida (25 tipos) | ~40 a 75 |
| Peças para 2 placas | ~70 a 80 |
| Juntas e solda dos encoders | ~8 |
| **Total** | **~220 a 265, mais ENIG e frete** |

Com 5 montadas seriam ~335 a 370. A diferença é pequena porque quase tudo é taxa fixa.

## Pedido 2 · JLCPCB: plate das teclas

| Parâmetro | Valor |
|---|---|
| Gerbers | `fab/student_v01_plate_gerbers.zip` |
| Camadas | 2 (sem cobre útil) |
| Espessura | **1,6 mm** |
| Quantidade | 5 (o mínimo) |
| Acabamento | HASL, o mais barato |
| Cor | preta, se quiser que não apareça entre as teclas |
| Preço | ~US$ 8 a 15 |

Pode ir no mesmo carrinho do pedido 1, para pagar um frete só.

**Ressalva:** o plate ainda tem o contorno herdado do Pocket. Ele serve para tocar o protótipo; a forma definitiva sai com o case.

## Compras fora da JLCPCB, para um instrumento

| Peça | Quantidade | Onde | Preço visto |
|---|---:|---|---|
| Teclas **Gateron KS-20 Magnetic Orange** (38 gf) | 1 pacote de 35 (usa 28) | loja da Gateron; Chosfox | US$ 24,50 a 26,60 |
| Bateria LiPo **503450**, 3,7 V, ~1000 mAh, **3 fios**, plugue JST PH de 2,0 mm | 1 | eBay, Amazon | ~£5 a £8 |
| Alto-falante fino Ø36 mm, 8 Ω, até ~4,6 mm de altura | 1 | Mouser, DigiKey (ex.: PUI AS03608MR) | não cotado |
| Parafuso M2.5 × 3 mm, cabeça chata | 1 | ferragem | centavos |
| Parafusos M2 | 8 | ferragem | centavos; o comprimento sai com o case |
| Cabo USB-C | 1 | — | — |

Compras adiadas por decisão do J ou por dependerem do case:

| Peça | Quando |
|---|---|
| Módulo **SparkFun MicroMod Teensy** (DEV-16402), £18,69 sem IVA na DigiKey UK | depois; sem ele a placa não liga |
| 2 knobs para eixo de 6 mm chanfrado | depois de confirmar a altura do eixo (24,5 mm, a conferir) |
| 28 capas das teclas, impressas | com o case |
| Case, com os 6 pilares de apoio | etapa adiada |

### A bateria de 3 fios: conferir antes de ligar

Os anúncios de 503450 com plugue de 3 pinos não dizem o que é o terceiro fio, e a ordem dos fios no plugue varia de vendedor para vendedor. Antes de encaixar na placa:

1. Medir com multímetro entre o fio preto e o terceiro fio: deve dar **cerca de 10 kΩ** à temperatura ambiente. Se der outra coisa, o terceiro fio não é o NTC que a placa espera.
2. Conferir a ordem dos fios contra o conector J202 da placa: **pino 1 = positivo, pino 2 (o do meio) = NTC, pino 3 = negativo** (do esquema, `viaggio_micromod/pcb/schematic.py`; o pino 1 está marcado na serigrafia do verso). Se estiver trocada, os terminais do plugue saem com um alfinete e se recolocam na ordem certa. **Positivo e negativo invertidos danificam a placa.**

## O que falta antes de tocar

1. Firmware para esta placa (etapa 6, a próxima).
2. O módulo MicroMod.
3. Um apoio sob o teclado. Sem os pilares do case a ponta direita da placa cede ao tocar; para testar na bancada, calços de ~7 mm sob a placa nos seis pontos dos pilares resolvem.
