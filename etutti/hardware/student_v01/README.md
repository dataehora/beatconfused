# eTutti Student V01 · a versão que será encomendada

Começada em 14 nov 2026. É a placa do **Viaggio J1** (`etutti/hardware/viaggio_j1/`, roteada pelo J e conferida nos passos M3 e M3b) levada até o pedido, com o nome novo. A J1 fica como está, para referência.

**Nada foi encomendado.** O J revisa o projeto em nove etapas e aprova cada uma antes da seguinte.

## Revisão, etapa por etapa

| # | Etapa | Estado | Decisão |
|---|---|---|---|
| 1 | Teclado | fechada (14 nov) | 28 teclas C-griff, G3–E5, grade de 18,5 mm, fileiras a 16,02; Gateron KS-20 magnética com um TMAG5253 sob cada tecla |
| 2 | Conceito | fechada (14 nov) | fone + alto-falante Ø36, USB-C, LiPo 1S ~1000 mAh, dois encoders com clique (volume liga/desliga, seletor), LED bicolor. Entrada de expressão (fole) fica para uma V02 |
| 3 | Forma e planta | fechada (14 nov) | placa retangular 246,5 × 95 mm, 4 camadas, 1,2 mm. A flexão é resolvida por 6 pilares Ø4 no fundo do case (P1–P6 do `viaggio_j1/FABRICACAO.md`), não por mais furos. A forma do plate fica para a etapa 7 |
| 4 | Esquema e peças | fechada (14 nov) | peças mantidas; sensores TMAG5253 por Global Sourcing da JLCPCB (o DRV5055 só volta se a cotação falhar); C307 = C162182 |
| 5 | Roteamento e conferências | fechada (14 nov) | placa igual à J1 depois do M3b, só o nome na serigrafia mudou (abaixo) |
| 7 | Modelo 3D completo | **em curso** | conjunto sem o case pronto em `model3d/` (abaixo); falta o case, que espera as decisões do J |
| 8 | Fornecimento | a fazer | cotação real na JLCPCB, Global Sourcing, alternativas; rever a compra de um módulo MicroMod antes das placas |
| 9 | Lista de compras e pedido | a fazer | lista final com quantidades e links; rotações do CPL conferidas na prévia da JLC |
| 6 | Firmware para esta placa | por último (decisão do J) | 28 teclas, 2 multiplexadores, pinos do MicroMod, bateria, liga/desliga, amplificador, acordeão amostrado |

## O que há nesta pasta

| | |
|---|---|
| `build.py` | copia o projeto KiCad da J1, troca o nome na serigrafia, roda o DRC e escreve `fab/` |
| `kicad/` | o projeto KiCad. Continua se chamando `viaggio_micromod`, porque o esquema guarda esse nome em cada peça. Abra `kicad/viaggio_micromod.kicad_pro` |
| `fab/` | Gerbers e furação (`student_v01_gerbers.zip`), BOM e CPL da JLCPCB, peças postas em casa, Gerbers do plate, imagens |
| `build.json` | o registro da última execução |
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
