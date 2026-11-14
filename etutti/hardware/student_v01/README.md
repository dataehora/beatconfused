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
| 5 | Roteamento e conferências | pronta para o J ver | placa igual à J1 depois do M3b, só o nome na serigrafia mudou (abaixo) |
| 6 | Firmware para esta placa | a fazer | 28 teclas, 2 multiplexadores, pinos do MicroMod, bateria, liga/desliga, amplificador, acordeão amostrado |
| 7 | Modelo 3D completo | a fazer | placa, módulo, teclas, plate, bateria, alto-falante, case com os 6 pilares. Usar os modelos de `etutti/hardware/student/eTutti_3D.3dshapes/` (pedido do J) |
| 8 | Fornecimento | a fazer | cotação real na JLCPCB, Global Sourcing, alternativas; rever a compra de um módulo MicroMod antes das placas |
| 9 | Lista de compras e pedido | a fazer | lista final com quantidades e links; rotações do CPL conferidas na prévia da JLC |

## O que há nesta pasta

| | |
|---|---|
| `build.py` | copia o projeto KiCad da J1, troca o nome na serigrafia, roda o DRC e escreve `fab/` |
| `kicad/` | o projeto KiCad. Continua se chamando `viaggio_micromod`, porque o esquema guarda esse nome em cada peça. Abra `kicad/viaggio_micromod.kicad_pro` |
| `fab/` | Gerbers e furação (`student_v01_gerbers.zip`), BOM e CPL da JLCPCB, peças postas em casa, Gerbers do plate, imagens |
| `build.json` | o registro da última execução |

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
