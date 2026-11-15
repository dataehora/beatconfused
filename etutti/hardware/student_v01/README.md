# eTutti Student V01 · a versão que será encomendada

**Encerrado em 15 nov 2026: projeto conferido e pronto para compra.** O que vem depois é do J (apresentar, encomendar) e da gestão (um possível novo conceito de design): ver `RESUMO-PARA-O-CHAT.md`.

Começada em 14 nov 2026. É a placa do **Viaggio J1** (`etutti/hardware/viaggio_j1/`, roteada pelo J e conferida nos passos M3 e M3b) levada até o pedido, com o nome novo. A J1 fica como está, para referência.

**Nada foi encomendado.** O J revisou o projeto em nove etapas. Em 15 nov 2026 a prévia da montagem na JLCPCB foi conferida pelo J e o projeto ficou **pronto para compra**, aguardando a apresentação dele para aprovação.

## Revisão, etapa por etapa

| # | Etapa | Estado | Decisão |
|---|---|---|---|
| 1 | Teclado | fechada (14 nov) | 28 teclas C-griff, G3–E5, grade de 18,5 mm, fileiras a 16,02; Gateron KS-20 magnética com um TMAG5253 sob cada tecla |
| 2 | Conceito | fechada (14 nov) | fone + alto-falante Ø36, USB-C, LiPo 1S ~1000 mAh, dois encoders com clique (volume liga/desliga, seletor), LED bicolor. Entrada de expressão (fole) fica para uma V02 |
| 3 | Forma e planta | fechada (14 nov) | placa retangular 246,5 × 95 mm, 4 camadas, 1,2 mm. A flexão é resolvida por 6 pilares Ø4 no fundo do case (P1–P6 do `viaggio_j1/FABRICACAO.md`), não por mais furos. A forma do plate fica para a etapa 7 |
| 4 | Esquema e peças | fechada (14 nov) | peças mantidas. Na etapa 8 a conferência dos códigos corrigiu 5 deles, e os sensores TMAG5253 passaram a ser peça de biblioteca da JLCPCB (sem Global Sourcing) |
| 5 | Roteamento e conferências | fechada (14 nov) | placa igual à J1 depois do M3b, só o nome na serigrafia mudou (abaixo) |
| 7 | Modelo 3D completo | conjunto e **case do protótipo** fechados (15 nov) | `model3d/` e `case/CASE.md`: case retangular de duas peças, 251 × 100 × 23 mm, tampo perfurado sobre o teclado e botões de haste, conferido contra o conjunto; **aprovado pelo J** |
| 8 | Fornecimento | fechada (15 nov) | `fornecimento/FORNECIMENTO.md`: 5 códigos LCSC corrigidos, Global Sourcing dispensado. Decisões do J: o mínimo de placas, teclas Orange, bateria de 3 fios, módulo MicroMod comprado depois |
| 9 | Lista de compras e pedido | fechada (15 nov) | `LISTA_DE_COMPRAS.md`: 5 placas com 2 montadas, plate, teclas Orange, molas de 65 e 80 g, bateria de 3 fios |
| 6 | Firmware para esta placa | fechada (15 nov) | `FIRMWARE.md`: o mesmo sketch, compilado para o Teensy MicroMod; pinos 27/27 e teclas 28/28 contra a placa (`firmware_check.py`). Nunca rodou numa placa |

## O que há nesta pasta

| | |
|---|---|
| `build.py` | copia o projeto KiCad da J1, troca o nome na serigrafia, roda o DRC e escreve `fab/` |
| `kicad/` | o projeto KiCad. Continua se chamando `viaggio_micromod`, porque o esquema guarda esse nome em cada peça. Abra `kicad/viaggio_micromod.kicad_pro` |
| `fab/` | Gerbers e furação (`student_v01_gerbers.zip`), BOM e CPL da JLCPCB, peças postas em casa, Gerbers do plate, imagens |
| `build.json` | o registro da última execução |
| `RESUMO-PARA-O-CHAT.md` | o resumo do projeto para a gestão, para abrir a análise de um novo conceito de design |
| `FIRMWARE.md`, `firmware_check.py` | o relatório do firmware e a conferência dos pinos dele contra a placa |
| `LISTA_DE_COMPRAS.md` | o que comprar e o roteiro do pedido na JLCPCB |
| `case/` | o case do protótipo: `case.py` (CadQuery), `fit_check.py`, `CASE.md`, arquivos para imprimir em `out/` |
| `fornecimento/` | `conferir_bom.py` consulta cada código na LCSC e na JLCPCB; `FORNECIMENTO.md` é o relatório da etapa 8 |
| `model3d/` | o instrumento em 3D: `build.py` monta o conjunto e escreve `img/` e `heights.json` |

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v01/build.py
```

O script não escreve nada em `viaggio_j1/`. **Não edite a placa à mão nesta pasta:** o script copia a da J1 por cima. Uma mudança na placa entra na J1 (ou neste script) e é copiada.

## Etapa 5 · o que foi conferido (14 nov 2026)

- **Diferença para a J1:** duas linhas do arquivo da placa, os dois textos de serigrafia, que passam a dizer "eTutti Student V01". Nenhuma trilha, via, zona ou peça mudou.
- **DRC** (`kicad-cli pcb drc --schematic-parity --severity-all`): 0 erros de folga, curto, furo ou serigrafia; **0 ligações faltando; paridade com o esquema 0**. Ficam os 3 trechos de 0,12 mm da EN_B junto do sensor U711, aceitos na SPEC v2.5 (a JLCPCB faz 0,09).
- **BOM e CPL:** iguais aos da J1, byte a byte. 42 linhas, 140 peças montadas (11 em cima, 129 embaixo). Sem código LCSC só as duas de Global Sourcing: 28 × TMAG5253BA3 e o espaçador H101.
- **Vindo da J1, sem refazer:** placa × firmware 28/28, flexão (0,048 mm na pior tecla com os 6 pilares), alturas por lado, orçamento de energia. Estão em `viaggio_j1/FABRICACAO.md` e `viaggio_j1/POWER.md`.
- **Pedido:** 4 camadas, 1,2 mm, JLC04121H-7628, ENIG, vias 0,5 / 0,3 tampadas.

## O que só se confirma com peças na mão

1. O encaixe e a altura do módulo MicroMod no conector M.2 (~6–6,5 mm abaixo da placa, estimado).
2. O espaçador Würth 9774025151R e o furo dele.
3. A altura do conector da bateria J202 (6,0 mm, estimada).
4. A junção de uma trilha do USB sob o corpo do conector USB-C.
5. O consumo real: nada foi medido nesta placa.
6. As rotações do CPL, que só aparecem na prévia da JLCPCB.

## Etapa 7 · o conjunto em 3D, sem o case (15 nov 2026)

```
"C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/student_v01/model3d/build.py
```

Referencial do modelo: x para a direita, y para trás (o y do KiCad com o sinal trocado), z para cima, **z = 0 no lado de cima da placa**. Imagens em `model3d/img/`; o modelo para abrir num visualizador 3D sai em `model3d/build/student_v01.gltf` (fora do Git, 20 MB).

**De onde vem cada peça**
- Placa, serigrafia e as peças que a biblioteca do KiCad tem: exportadas pelo `kicad-cli`.
- **Encoders, USB-C, jack, conector M.2, conector da bateria, botão Program e LED:** o modelo STEP de cada peça, baixado da EasyEDA pelo código LCSC com `model3d/fetch_models.py`, para `model3d/modelos/` (fora do Git). A biblioteca oficial do KiCad não tem modelo para essas peças. As pastas `student/` e `studentBK/` também não: as duas trazem os mesmos sete arquivos.
- Chips QFN/VSON e sensores X2SON: caixas do tamanho do pátio, com a altura do campo `Altura_mm`.
- Módulo MicroMod Teensy: o STEP da SparkFun da pasta do J (`student/eTutti_3D.3dshapes/`, fora do Git).
- Knobs e pilar: os modelos VRML da mesma pasta (formas simples geradas por script).
- Teclas (Gateron KS-20 + a capa do Pocket), plate, bateria e alto-falante: feitos no script a partir das medidas.

**Erro achado ao baixar os modelos, corrigido:** o código LCSC do codec U301 era **C511764**, que é o SGTL5000XN**A**A3 (QFN-32 de 5 × 5). A placa usa o SGTL5000XN**L**A3 (QFN-20 de 3 × 3), que é o **C2651833**. Corrigido no `viaggio_micromod/pcb/schematic.py`, na folha F, na placa da J1 e nos BOMs; a paridade continua 0. A `SPEC.md` do Viaggio MicroMod ainda cita o código antigo (é da gestão). **Na etapa 8, conferir o encapsulamento de todos os códigos LCSC do BOM contra o footprint.**

**Alturas medidas no modelo** (`model3d/heights.json`)

| Para cima, a partir da placa | mm |
|---|---:|
| plate (1,6 mm), face de cima | 5,1 |
| alojamento da tecla | 11,2 |
| haste da tecla solta | 14,8 |
| capa da tecla solta | 18,9 |
| eixo do encoder: **24,5 no modelo da EasyEDA, 20 no footprint e na Farnell** (conferir no desenho da Alps) | 20–24,5 |

| Para baixo, a partir da face de baixo da placa | mm |
|---|---:|
| conector do módulo (M.2), corpo | 4,2 |
| **módulo MicroMod montado** (espaçador 2,5 + cartão + peças) | **4,7** |
| conector da bateria J202, pelo modelo (o campo da placa dizia 6,0) | 5,5 |
| pernas dos encoders, sem cortar | 2,3 |

O módulo era a maior estimativa em aberto (6–6,5 mm). Pelo modelo da SparkFun são 4,7 mm, então quem manda na profundidade do fundo é o conector da bateria.

**Posições provisórias, a decidir com o case**
- **Bateria:** LiPo 503450 (5 × 34 × 50 mm, ~1000 mAh) sob a placa, na frente à esquerda, centro em (29; 70) do KiCad, de pé (50 mm no sentido frente-trás). É o único lugar sob a parte esquerda onde ela cabe entre os furos H3 e H4. Fica por baixo das pernas dos encoders, que então precisam ser cortadas a 1 mm; com 0,4 mm de espuma, o fundo da bateria fica a 6,4 mm da placa.
- **Alto-falante:** Ø36 × 4,6, em cima, na frente à esquerda, colado sob a tampa, com a face em z = 9.
- **Fundo interno do case:** 6,9 mm abaixo da placa, o que dá pilares de 6,9 mm.
