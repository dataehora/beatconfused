# Grade de FR-4 da V3: furos escareados, só de fábrica (SPEC v6, item 2)

A grade é a da V2 (mesmo contorno, 28 furos de Ø 6,2 mm para os botões, 10 furos de Ø 2,3 mm para os parafusos, 1,6 mm),
**com o cobre recuado em volta dos 10 furos do parafuso**. O escareado é feito pelo fabricante da placa da grade: **nunca em casa**
(a alternativa "escarear em casa" da v5 saiu, por decisão do J).

Arquivos (V3, a V2 não foi tocada):

- `student_v03/pcb/grade_fab.py` (KiCad python) gera `student_v03/kicad/student_v03_grade.kicad_pcb` e
  `student_v03/fab/student_v03_grade_gerbers.zip`. DRC: 0 erros (só o aviso `isolated_copper`, inofensivo: a grade não tem circuito).
- **Cobre recuado até Ø 4,4** em volta dos 10 furos, nas duas faces: áreas sem cobre (rule areas) de 64 lados cujo círculo inscrito é de Ø 4,4.
  Medido no arquivo preenchido: a distância mínima do centro do furo ao cobre é **2,20 mm** nas duas faces (= Ø 4,4).
  O resto continua como na V2: cobre a 0,5 mm do contorno e dos furos, máscara preta fosca nas duas faces.
- Modelo 3D: `case/out/grade.step` (os 10 cones já estão lá, a 90°, rentes).
- Figura para o pedido (planta + corte): `case/renders/grade_escareada.png` (gerada por `case/grade_figura.py`).

## Especificação

| | |
|---|---|
| Furos | 10, NPTH, Ø 2,3 mm (posições: `G.grid_screws()`, numerados 1–10 na figura) |
| Escareado | cone, **90°**, boca **Ø 3,8 mm**, pela **face de cima** (a do teclado) |
| Profundidade | 0,75 mm (sobram 0,85 mm dos 1,6 mm; a regra pede ≥ 0,2) |
| Cobre | recuado até Ø 4,4 mm nas duas faces (a regra pede a boca a ≥ 0,2 mm de cobre: 3,8 + 0,4 = 4,2, com margem) |
| Parafuso | M2 × 16 de cabeça escareada (ISO 7046), cabeça Ø 3,8, rente à face de cima |
| Outros furos | 28 de Ø 6,2 mm, lisos |

Regras da JLCPCB para o escareado (https://jlcpcb.com/help/article/countersink-hole-process), todas atendidas: só cone, em PTH ou NPTH;
pelo menos 0,2 mm de placa abaixo do cone; boca a pelo menos 0,2 mm de cobre; informar diâmetro da boca e do furo, ângulo, tipo, lado
e uma figura.

## Texto pronto: observação do pedido na JLCPCB (primeira opção)

Pedir a grade **junto com a placa principal**, como pedido de placa nua (2 camadas, 1,6 mm, máscara preta fosca nas duas faces,
qualquer acabamento: não há cobre exposto). No campo de observações / "Remark":

```
COUNTERSUNK HOLES (custom process): 10 NPTH holes, drill 2.3 mm, countersink on the TOP side only,
cone 90 degrees, countersink mouth diameter 3.8 mm, depth 0.75 mm (leaves 0.85 mm of the 1.6 mm board).
Copper is already pulled back to 4.4 mm diameter around each of the 10 holes on both layers.
The 10 hole positions are marked 1-10 in the attached figure (grade_escareada.png). The other 28 holes
(6.2 mm) are plain, no countersink. Please contact me before production if anything cannot be made.
```

Anexar `case/renders/grade_escareada.png`. A JLCPCB revisa o arquivo antes de produzir e, se não puder fazer, avisa e devolve o valor:
não há risco de receber a grade sem escareado sem saber.

## Texto pronto: PCBWay (segunda opção, se a JLCPCB recusar)

A PCBWay lista furo escareado NPTH entre as capacidades (tolerância de ±0,2 mm para furos < 10 mm): https://www.pcbway.com/capabilities.html.
A grade é uma placa separada, sem montagem, então trocar de fábrica só para ela não muda nada na placa principal. No pedido, "Special requests":

```
Countersunk (conical) holes: 10 NPTH holes, finished drill 2.3 mm, countersink on the TOP side, 90 degree
cone, mouth diameter 3.8 mm, depth 0.75 mm. Board 1.6 mm, 2 layers, matte black solder mask both sides,
no exposed copper. Copper keep-out of 4.4 mm diameter around each countersunk hole is already in the files.
Hole positions are shown in the attached figure (numbered 1-10). Tolerance +/-0.2 mm on the mouth is fine.
```

Mesmos arquivos Gerber (`student_v03_grade_gerbers.zip`) e a mesma figura.

## O que continua fora

- A alternativa do parafuso de cabeça baixa sobre furo liso continua fora: não cabe sob a tampa (a folga sobre a grade é 0,15 mm).
- Escarear em casa: **fora**, nem como plano B.
