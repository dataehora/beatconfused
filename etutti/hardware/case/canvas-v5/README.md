# Canvas v5 · desenhos de referência da SPEC v5

> **Estes são os desenhos de referência da v5, não a forma final.** A forma final é a da `../SPEC.md` **v9** (congelada desde a v7: passo 18,5 em grade hexagonal, tampo a z 17,4, rampa reta na frente, plate de 1,6 mm…), modelada no `../case.py`. Para ver o case como ficou, use os renders em `../renders/` ou a página `/etutti/models/`.

Desenhos do Claude Chat que acompanharam a SPEC v5. Os números da SPEC são a referência; os desenhos servem para entender a forma geral. O canvas ao vivo (com os acabamentos trocáveis) é https://claude.ai/artifact/PjadX8XZX34prrsCt1ASE2 (privado).

| Arquivo | O que é |
|---|---|
| `seixo-v5-iso.png` / `.svg` | Isométrico do Seixo (plástico, acabamento areia), frente-esquerda |
| `madeira-v5-iso.png` / `.svg` | Isométrico da Madeira (carvalho branco), frente-esquerda |
| `seixo-v5.dc.html` | Prancha do Seixo: vista de cima, frontal, face esquerda, controles e especificação resumida |
| `madeira-v5.dc.html` | Prancha da Madeira, mesma estrutura |
| `botoes.dc.html` | Botão domo baixo com saia sobre Gateron: corte, cantos entre botões, versões natural / sustenido / Dó-Fá |
| `cores.dc.html` | Comparação de acabamentos (3 do Seixo, 2 da Madeira) |

Os `.dc.html` são o código-fonte das pranchas do canvas (formato Design Component do Claude). Fora do canvas eles não renderizam sozinhos, porque dependem do `support.js` do editor; a geometria está nos `<path>` SVG, em escala de 2 px = 1 mm, com y crescendo para quem toca (mesmo sistema da SPEC).
