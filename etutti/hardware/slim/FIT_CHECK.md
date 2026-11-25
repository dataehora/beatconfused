# eTutti Slim · FIT_CHECK (SPEC R9SL, sessão A)

Resposta à **SPEC R9SL §8.1**. Detalhes: [ELETRONICA.md](ELETRONICA.md) (última seção), [ROTEAMENTO.md](ROTEAMENTO.md) (última seção), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (R27, R28, R35, R51). **Parado. Nada cotado ou comprado; a principal (BGA) não foi tocada.**

## 1. Resumo

| Parte | Resultado |
|---|---|
| Fixação | **2 × M2 só na ponta direita** (u = 163,0, v = ±3,6), sem escareado; régua e grade **160 → 167,5 mm**; furos do meio removidos. A cauda **não** recebeu furo (não cabe); reserva DIN 965 não aplicada |
| Folgas | furo à carcaça da tecla 8: 3,85 mm; cabeça Ø3,8 à carcaça: 3,05 mm; ponta das fileiras 1 e 3 a **0,75 mm** da parede interna |
| Régua | DRC **0/0**, não ligados **0**, paridade **0**, 99 vias; a rota híbrida foi refeita do zero em ~11 s, sem mudar o código |
| Grade | 155,5 × 16, sem escareado; DRC 0/0; Gerbers regenerados e conferidos |
| Base | os apoios contínuos acompanham os 167,5 mm (conferido: contínuos nas 4 fileiras); a porca (altura 1,6) fica acima do piso sem bolso novo; o tampo não mudou |
| R410 | 47 Ω (C25118); ERC principal 0/0, régua 0/0 |

## Perguntas para o design

1. **A cauda da régua fica sem parafuso.** *Problema:* os dois M2 só couberam na ponta direita; na esquerda, J1, U9, C9, C10 e a rota ocupam toda a largura (v ±7,5) entre u 0 e 14, e o furo mais a porca D4,6 não têm onde entrar. Sem nada na cauda, ela só é presa pelo apoio contínuo da base e pelo tampo por cima (a switch prende grade e régua entre as pontas). *Opções:* (a) aceitar, e ensaiar no protótipo se a cauda levanta; (b) uma **lingueta da base** de ~1 mm sobre o fim da cauda (não mexe na placa, só no case); (c) a **reserva**: voltar a 2 furos no meio com escareado DIN 965 (cabeça ~3,8 mm, parede de ~0,35 mm de FR‑4 até o furo da switch, risco de trincar); (d) alargar a cauda da régua em ~8 mm à esquerda, com o FFC e os cabos mais longos. *Recomendo (b).*
2. **Margem de 0,75 mm na ponta direita das fileiras 1 e 3.** *Problema:* a régua de 167,5 mm vai a x 146,25 e a parede interna está em 147,0. *Opções:* (a) aceitar 0,75 mm; (b) encurtar a ponta em 1 mm (furo em u = 162,0, ponta em 166,5; margem 1,75 mm, folga furo‑tecla 8 de 2,85); (c) alargar o case à direita em 1 mm. *Recomendo (a); o MJF segura ±0,3.*
