# eTutti Student V01 · etapa 8 · fornecimento

15 nov 2026. **Nada foi encomendado nem posto em carrinho.** Preços em US$ sem frete e sem impostos, salvo onde diz libra. Tudo o que vem de uma página de loja é uma foto do dia: conferir de novo na hora do pedido.

```
python etutti/hardware/student_v01/fornecimento/conferir_bom.py 5
```

O script consulta, para cada código LCSC da lista de montagem, a LCSC (o que a peça é, encapsulamento, preço) e a biblioteca de peças da JLCPCB (estoque da linha de montagem, básica ou estendida), e grava `bom_lcsc.json`. A comparação do encapsulamento com o footprint foi lida linha a linha por mim na tabela que ele imprime.

## 1. Conferência dos códigos LCSC: 5 correções

Nenhuma conferência anterior comparava o código LCSC com a peça real. Das 42 linhas da lista, 37 estavam certas e 5 foram corrigidas:

| Peça | Código antigo | O que o código antigo é | Código novo | Consequência se o pedido saísse assim |
|---|---|---|---|---|
| U301, codec | C511764 | SGTL5000XNAA3, QFN-32 de 5 × 5 | **C2651833** (SGTL5000XNLA3R2, QFN-20 de 3 × 3) | a peça não cabe no footprint |
| **R203**, corrente de carga | C25811 | **200 kΩ** em 0603 | **C25871** (1,8 kΩ 0402) | a bateria carregaria a ~4 mA em vez de 490 mA, e a peça é maior que o footprint |
| **R401**, LED vermelho | C25190 | **27 Ω** em 0603 | **C25099** (270 Ω 0402) | LED com dez vezes a corrente, e a peça é maior que o footprint |
| U601, U602, multiplexadores | C547038 | 74HC4067PW em tubo, **estoque 0** na JLCPCB | **C179326** (74HC4067PW,118, em rolo, 28 105 em estoque) | montagem parada por falta de peça |
| 28 × TMAG5253 e o espaçador H101 | sem código (Global Sourcing) | — | **C22401868** e **C7496631** | ver o item 2 |

As correções estão no `viaggio_micromod/pcb/schematic.py` (esquema regenerado, ERC 0/0), na placa da J1 e nesta pasta. DRC da Student V01 depois delas: 0 ligações faltando, paridade com o esquema 0.

## 2. Global Sourcing deixou de ser necessário

- **TMAG5253BA3IQDMRR** está na biblioteca da JLCPCB como **C22401868**: 9 130 em estoque, US$ 0,37 cada em 100 ou mais. São 140 para 5 placas.
- **Espaçador Würth 9774025151R** está como **C7496631**: 988 em estoque. A LCSC não lista esse código (só a JLCPCB), então o preço só aparece na cotação.

Com isso a lista inteira tem código, e somem o frete, o manuseio e a espera do Global Sourcing. O plano B dos sensores (DRV5055) não é necessário.

## 3. Estoque na JLCPCB que pede atenção

Todas as 42 linhas têm estoque para 5 placas. As mais curtas:

| Peça | Estoque | Preciso para 5 placas |
|---|---:|---:|
| Encoder EC11E18244A5 | 318 | 10 |
| Conector M.2 91302-42-067RCE | 553 | 5 |
| Indutor FNR4020S2R2MT | 718 | 5 |
| Capacitor de 150 nF (C307) | 963 | 5 |
| Codec SGTL5000XNLA3R2 | 970 | 5 |
| Espaçador 9774025151R | 988 | 5 |

Alternativas já levantadas para o C307: CCTC C7393865 e YAGEO C505466 (`viaggio_j1/FABRICACAO.md`).

## 4. Custo das peças montadas

- **US$ 34,4 por placa** em peças (preço LCSC na quantidade de 5 placas), mais o espaçador. A estimativa anterior era 24,3.
- A diferença é o codec: **US$ 9,35**, contra 1,80 na estimativa, que usava o preço do código errado.
- Maiores itens por placa: 28 sensores 10,5; codec 9,4; 2 encoders 4,2; carregador 2,1; conversor 1,6.
- 17 tipos de peça são básicas e 25 são estendidas. A JLCPCB cobra uma taxa por tipo estendido.

Custo estimado de **5 placas montadas** (ordem de grandeza; a cotação real da JLCPCB, com os arquivos enviados, é que vale):

| Item | US$ |
|---|---:|
| PCB de 4 camadas, 246,5 × 95, 1,2 mm, ENIG, 5 unidades | ~34 + ENIG |
| Montagem dos dois lados: preparação e estênceis | ~67 |
| Taxa por tipo de peça estendida (25 tipos) | ~40 a 75 |
| Peças, 5 placas | ~175 |
| Solda das juntas e dos 2 encoders à mão | ~10 |
| Plate de FR-4 de 1,6 mm, 5 unidades | ~8 |
| **Total** | **~335 a 370, mais ENIG e frete** |

Isso dá cerca de US$ 70 por placa montada.

## 5. Peças fora da placa, por instrumento

| Peça | Quantidade | Onde, preço visto | Observação |
|---|---:|---|---|
| Módulo SparkFun MicroMod Teensy (DEV-16402) | 1 | DigiKey UK, £18,69 sem IVA, 259 em estoque; SparkFun, US$ 24,95 | The Pi Hut e SK Pang estavam sem estoque |
| Teclas Gateron KS-20 magnéticas | 28 | loja da Gateron ou Ukeebs, US$ 21 o pacote de 35 (White, 30 gf); Orange (38 gf) por US$ 24,50 | um pacote por instrumento, sobram 7 |
| Bateria LiPo 503450, ~1000 mAh | 1 | eBay e Amazon, cerca de £5 a £8 | **ver o ponto abaixo sobre o NTC** |
| Alto-falante fino Ø36 mm, 8 Ω | 1 | não cotado; ordem de £3 a £5 | escolher junto com o case |
| Knobs para eixo de 6 mm chanfrado | 2 | não cotado; ordem de £1 a £2 cada | depende da altura do eixo (item 6) |
| Capas das teclas | 28 | impressas (o arquivo do Pocket serve) | com o case |
| Parafuso M2.5 × 3 do módulo, parafusos M2 | 1 + 8 | ferragem comum | |

**Bateria com NTC.** A placa espera uma bateria de 3 fios, com o NTC de 10 kΩ no terceiro. As 503450 fáceis de achar têm 2 fios; algumas são vendidas com conector de 3 pinos, mas os anúncios não dizem o que é o terceiro fio. Duas saídas:
1. Comprar a de 3 fios e medir o terceiro fio com um multímetro antes de ligar (deve dar cerca de 10 kΩ para o negativo à temperatura ambiente).
2. Usar uma de 2 fios e pôr um resistor de 10 kΩ entre o pino do NTC e o negativo, no próprio plugue. Funciona, mas o carregador deixa de ver a temperatura da bateria.

Para um primeiro protótipo a saída 2 é aceitável se a carga for sempre vigiada. Para algo que fica com outra pessoa, a 1.

## 6. Altura do eixo do encoder: 24,5 mm, não 20

- A Alps e a Farnell dão "comprimento do atuador 20 mm". A Arrow dá "altura do produto 24,5 mm", e o modelo 3D da LCSC tem o eixo terminando a 24,5 mm da placa.
- Leitura mais provável: os 20 mm são o comprimento do eixo, e a ponta fica a 24,5 mm da placa. O nome do footprint do KiCad ("H20mm") e o campo `Altura_mm` da placa (20) estão 4,5 mm baixos.
- Não li o desenho da Alps. **Conferir no desenho ou com a peça na mão antes de desenhar o case e de comprar os knobs.** Para a placa não muda nada.
- Com 24,5 mm, o knob passa da capa das teclas (18,9 mm) em 6 a 7 mm.

## 7. Onde fabricar

- **JLCPCB** é a escolha natural: todos os códigos da lista são da biblioteca dela, e os arquivos em `fab/` estão no formato dela.
- **PCBWay** faz o mesmo serviço, mas compra as peças caso a caso pelo código do fabricante; a lista teria de ser refeita com esses códigos e a cotação é manual. Só vale se a JLCPCB recusar algo.
- **Plate de FR-4:** um segundo pedido de PCB simples na mesma JLCPCB (`fab/student_v01_plate_gerbers.zip`).
- **Case e capas:** JLC3DP, PCBWay ou Craftcloud, quando o case existir.

## 8. O que só a cotação e a prévia da JLCPCB respondem

1. O preço real com ENIG e a taxa das peças estendidas.
2. O preço do espaçador C7496631.
3. As rotações e posições de cada peça na prévia da montagem, sobretudo o conector M.2, o espaçador, o jack, o LED, o conector da bateria, o botão Program, o USB-C e os 28 sensores (o pino 1 decide a leitura).

## 9. Posições e rotações da montagem (CPL), refeitas em 15 nov

Ao configurar o pedido, o J viu na prévia da JLCPCB os knobs, o jack e o USB fora do lugar e o conector do módulo virado. **O arquivo de posições anterior estava errado e a montagem sairia errada.** Ele usava a origem de cada footprint do KiCad e uma tabela genérica de rotações; a JLCPCB posiciona cada peça pelo footprint que ela própria tem para o código LCSC, que pode ter outra origem e outra orientação.

`fornecimento/cpl_jlc.py` refaz o arquivo peça por peça: baixa o footprint da JLCPCB (EasyEDA) de cada código, encontra o giro e o deslocamento que põem os pads dele sobre os pads da placa (pelo número do pad quando os dois footprints numeram igual, senão pela posição), e escreve a posição da origem dele e esse giro.

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/fornecimento/cpl_jlc.py
```

**37 das 140 peças mudaram:**

| Peça | O que estava errado |
|---|---|
| **28 sensores TMAG5253** | **girados 180°**. O desenho dos pads é igual nos dois sentidos, então a prévia não mostraria nada estranho, mas o pino 1 ficaria trocado e nenhuma tecla funcionaria |
| Conector do módulo (J101) | girado 180° e 1,5 mm fora |
| Encoders (SW401, SW402) | girados 90° e 7,7 mm fora |
| Jack (J301) | 6,6 mm fora |
| USB-C (J201) | 1,5 mm fora |
| Conector da bateria (J202) | girado 180° |
| Carregador (U202), conversor (U204), proteção do USB (U201) | girados 90° |

As outras 103 saíram iguais às de antes. Isso inclui peças do verso com desenho assimétrico (SOT-23, SOT-23-5, TSSOP-24), o que confirma que a convenção de espelhamento do verso usada no cálculo é a mesma da tabela antiga onde ela estava certa.

O erro máximo entre os pads dos dois footprints depois do ajuste é de 0,5 mm (jack), por diferenças de desenho dos próprios footprints; nas outras peças fica abaixo de 0,4 mm.

**O que continua valendo:** o cálculo supõe que a JLCPCB posiciona pelo footprint da EasyEDA. Os erros que o J viu são exatamente os que o cálculo encontrou, o que apoia a suposição, mas a prévia da JLCPCB continua sendo a conferência final. Duas peças não têm orientação a conferir: o espaçador (um pad só) e o botão Program (igual girado 180°).

**O conector do módulo:** o footprint que a JLCPCB tem para o C48985906 tem a falha dos pinos em outro lugar (desenho de outra chave), mas a peça é a certa: a LCSC a descreve como "M.2-E Key, 67P, 4,2 mm". Na prévia, o desenho dos pads do conector pode não coincidir pino a pino com a placa nessa região; o corpo e as duas fileiras devem coincidir.

## Perguntas para o J

1. **Um módulo MicroMod agora?** A DigiKey UK tem em estoque. Com ele na mão eu testo o firmware antes de as placas chegarem, e se confirma o encaixe.
2. **Quantas placas:** 5 é o mínimo da JLCPCB. Montar as 5, ou montar 2 e receber 3 nuas? A montagem parcial reduz as peças, não as taxas fixas.
3. **Teclas:** White (30 gf, mais leve) ou Orange (38 gf)?
4. **Bateria:** saída 1 ou 2 do item 5?
