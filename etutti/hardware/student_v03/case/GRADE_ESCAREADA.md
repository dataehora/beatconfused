# Grade de FR-4 da V3: furos escareados (SPEC v4, item 12 e tarefa 15)

A grade é a mesma da V2 (mesmo contorno, 10 furos de Ø 2,3 mm nas mesmas posições, 1,6 mm): os arquivos de fábrica são os da V2,
`student_v02/fab/student_v02_grade_gerbers.zip` (gerados por `student_v02/pcb/grade_fab.py`). **O que muda é só o escareado**, que o
Gerber não descreve:

- parafuso M2 × 16 de **cabeça escareada** (ISO 7046 / DIN 965, cabeça Ø 3,8 mm), **rente à face de cima** da grade (z 12,95);
- escareado a **90°**, de Ø 3,8 mm na face de cima até o furo de Ø 2,3 mm: **0,75 mm de profundidade** (cabe nos 1,6 mm da grade);
- modelo no STEP: `case/out/grade.step` (os 10 cones estão lá, a 90° e rentes).

Para o pedido na JLCPCB: **não confirmei** que o pedido de placa aceite furo escareado por opção do formulário. O que faço aqui é
deixar o desenho (acima) para você escrever na observação do pedido, ou pedir o escareado à parte (usinagem). Se a JLCPCB recusar, as
saídas são: escarear em casa com uma broca de 90° (0,75 mm, 10 furos), ou usar o parafuso de cabeça baixa de 3,8 mm sobre um furo
liso e deixar 0,4 mm de cabeça acima da grade (o teto sobre a grade tem 0,15 mm de folga: não cabe, ver `FIT_CHECK.md`).
