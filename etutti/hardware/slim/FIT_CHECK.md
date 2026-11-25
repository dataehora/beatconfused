# eTutti Slim · FIT_CHECK (SPEC R5SL, fechamento da Etapa 2 — portão B da placa principal)

Resposta à **SPEC R5SL §8**. Relatórios: [ELETRONICA.md](ELETRONICA.md) (bateria substitutas e LED, última seção), [POSICIONAMENTO.md](POSICIONAMENTO.md), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (62 itens, 6 novos), [FIRMWARE.md](FIRMWARE.md), `estudos/botao/`. **Parado no portão B da placa principal: sem rotas, nada cotado, comprado ou amostrado.**

## 1. Resumo da R5SL

| Parte | Resultado |
|---|---|
| **Botão de acordeon** | cabeça Ø15 × 7,5 (flecha 1,0, borda R1), haste Ø10 × 5,85, pino Ø5,4 × 3,0, cruz fêmea 4,2 × 1,04 × 3,0; **STEP `estudos/botao/botao.step`** (+ `botao_textura.step`); **uma peça nas 4 fileiras** |
| Alturas (tampo real de cada fileira) | base em repouso 20,2 / 22,2 / 24,2 / 27,2; **topo em repouso 27,7 / 29,7 / 31,7 / 34,7**; apertado 24,2 / 26,2 / 28,2 / 31,2; **folga no fim do curso 2,00 / 2,00 / 2,00 / 2,07** (a borda alta da fileira 4 é 21,63: a curva de trás a baixa 0,07) |
| Textura de C e F | covinha côncava Ø5,0 × 0,4 no centro do domo (SLA faz bem, sem aresta para o dedo; alternativa: anel em relevo) |
| Tampo | furos **Ø11 sem rebaixo** (modelo oficial refeito, tampo válido); altura total do instrumento **34,7 mm** (era 26,8, o topo do knob de volume); folga radial haste×furo 0,5 (0,10 no pior caso com jogo da haste e inclinação estimados) |
| Knobs S2 com saia | saia Ø18,4 no poço Ø19,0, sobe 0,5 acima da borda de trás, corpo Ø16,4; parede de 0,9 até o anel de LED: `case/img/knobs_s123.png` |
| Bateria | substituta direta: **BAK LP-523450-IS-3** (Farnell UK 2077888, £ 18,31, 218 em estoque, 950 mAh, 51 × 33,5 × 5), cabe na baia 36 × 60; **NTC, conector e STEP por confirmar** (a folha da BAK não pôde ser baixada); Varta 503562/503759 não cabem (+4 mm / +1,5 mm) |
| FFC | **30 mm de série com S não cabe**: o vão é 5,5 mm e o S usa só 5,6–7,3 mm de cabo, sobrariam 16–18 mm; **20 mm sob medida**; raio no corte 3,3 / 7,8 / 7,8 / **2,9** (mín. estimado 3,0): `case/ffc_s.py` |
| LED do anel | a folha do 1615 não tem montagem reversa nem janela: **face de cima, soldado em casa** |
| Placa principal | DRC sem trilhas **0/0**, paridade **0**, ERC **0/0**; 120 peças; mesma planta (69,0 × 77,1) |
| Pinos × placa | `check_placa.py` **21/21** |
| Planta do teclado | `case/img/planta_teclado.png` (nome em cada botão; naturais brancas, sustenidos pretos, C e F com a covinha) |

## 2. Cortes e figuras

| Pedido | Arquivo |
|---|---|
| Botão, repouso e apertado, 4 fileiras, tampo real | `estudos/botao/botao_cortes_4fileiras.png`, `botao.json` |
| Knobs S2 com saia | `case/img/knobs_s123.png` |
| Planta do teclado com notas | `case/img/planta_teclado.png` |
| S do FFC | `case/out/ffc_s.json` (cálculo; sem figura) |
| Placa e cena 3D | `pcb/principal/img/planta_principal.png`, `case/renders/cena_principal_*.png`, `corte_principal_*.png` |

## 3. O que muda o lado de fora (já aceito pelo J na R5SL)

Botões Ø15 × 7,5 mais altos (altura total 34,7), furos Ø11, knobs com saia Ø18,4 (poço Ø19,0). Planta 247,0 × 89,1 inalterada.

## 4. Desvios da R5SL

1. **FFC de 30 mm não cabe** (o S só vale com cabo de 13–14 mm); fica 20 mm sob medida.
2. **Substituta da bateria sem NTC/STEP confirmados**: só uma substituta direta achada (a BAK); a segunda fonte é a própria VARTA em outro código (Farnell UK 4062501, 28 semanas).
3. A figura dos cortes do botão tem rótulos que se sobrepõem um pouco em repouso (números certos no `botao.json`).

## Perguntas para o design

1. **FFC:** aprova 20 mm sob medida (os 4 iguais) já que 30 mm de série não cabe num vão de 5,5 mm? Ou aceita aumentar o vão entre régua e placa para dar lugar a um S de 30 mm?
2. **Bateria BAK LP-523450-IS-3:** podemos trazer a folha e o STEP da BAK (o PDF não baixou aqui) para confirmar NTC e conector? Aceita 950 mAh (~7,7 h)?
3. **Textura de C e F:** covinha Ø5,0 × 0,4 ou prefere o anel em relevo?
4. **Saia do knob:** saia Ø18,4 e poço Ø19,0 (parede de 0,9 até o anel de LED) servem, ou quer o corpo todo Ø18,4?
5. **LED na face de cima:** a 1615 soldada em casa (pads 0,5 mm) serve, ou troco por um LED maior de solda manual (0805 bicolor)?
