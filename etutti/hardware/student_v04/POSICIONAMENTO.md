# eTutti Student V4 · posicionamento da placa principal (portão P, parte 1) · R3V4

**NÃO APROVADO: quem aprova é o J.** Nada roteado (0 trilhas, 0 vias), nada gerado em `fab/`. Data: 21 nov 2026.
Reproduz: `python pcb/schematic.py` → KiCad python `pcb/posiciona_v4.py` → venv CadQuery `pcb/vistas_v4.py` → `python bom_v4.py`.
Arquivos: `kicad/student_v04.kicad_pcb` (+ `.kicad_dru`, `.kicad_pro`), `pcb/posicao_v4.json`, `pcb/img/{topo,fundo,ratsnest}.png`.

## 1. A placa
- **75,05 x 95,1 mm** (x 2,45..77,5; y 2,45..97,55), 4 camadas, 1,2 mm, cantos R 3. Só interface; **77 peças JLC, todas no fundo** (só os 2 encoders e os pads do alto-falante no topo).
- Derivada das posições da V3 (peças que ficam), com o que muda abaixo. Sem tecla, sensor, multiplexador nem furo de grade. Furos M2: H2 (74;93), H3 (6,5;48,5), H4 (8;91,5) como na V3 e **H1 novo em (62;48)** (a V3 tinha 4 furos do lado da interface; a posição é proposta) mais H101 (módulo, Ø2,7).
- **In2 = GND inteira** (sem ilha, sem keep-out), In1 = +3V3. Os polígonos de GND de F.Cu/B.Cu vêm com o roteamento (sem trilhas só "esfomeiam" os pads).

## 2. USB-C e M.2 (item 7)
| | R3V4 pede | Esta placa |
|---|---|---|
| USB-C (linha dos pads de sinal) a pads 3/5 do M.2 | ≤ 7 mm | **6,75 mm** |
| par D+/D- (USB-C → USBLC6 → pads 3/5), estimado em linha reta | ≤ 10 mm | **7,07 mm** |
| referência | In2 inteira | sim; par em B.Cu (USB-C, U201 e J101 no fundo, sem via) |
Como: o USB-C continua na parede da esquerda, mas **sobe de y 16 para y 10,0** (os pads B6/A7 ficam na altura dos pads 3/5: 9,25 / 9,75, par reto) e o **J101 (M.2) e o que o acompanha sobem para a esquerda 5,5 mm** (pads ímpares em x 16,73). Consequência para o **design**: o furo do USB-C na parede da esquerda passa de y 16 para **y 10**, e o módulo MicroMod e o parafuso H101 ficam 5,5 mm mais à esquerda (H101 em x 42,0). Alternativa se o furo não puder subir: USB-C na parede de trás (não feita).

## 3. Conectores de fileira (J601..J604, JST SH 6 vias, bocas para +x)
Em y = 74,03 / 58,01 / 41,99 / 25,97 (centros das fileiras). As réguas das fileiras 1, 3, 4 começam em x = 89,2 / 89,2 / 98,45, então a boca fica na borda (x 77,4; 11,8 mm de vão para dois plugues e a curva do cabo). **A régua da fileira 2 começa em x = 79,95: só 2,5 mm de vão.** Por isso o J602 tem a boca em x = 70,95 e a área de 6,5 x 10,4 mm à frente dela é reservada (área de regra "plugue J602", sem peças). *(Vão de plugue de 9 mm: estimativa; conferir no desenho da JST.)* Pergunta ao design: o conector da régua olha para -x no pocket?

## 4. Corredores reservados (camada Cmts.User, `posicao_v4.json`)
USB (11..16; 8,2..11,2, B.Cu) · barramento OUT/SCAN: desce em x 25,5..34 de y 8 a 54, faixa horizontal y 54..57 até x 70, espinha vertical x 68,5..71 (F.Cu quase livre, vias para os pads do fundo) · I2S codec (19..30; 20..34) · I2S amplificador (26..54; 58..86, guarda de GND) · áudio do fone (6..26; 28..62) · energia (50..77; 3..20) · VSYS ao amplificador (x 55..58, y 20..86, 0,8 mm). Regras novas no `.kicad_dru`: OUT_Rk a 0,3 mm de CLK/DATA/I2S/MCLK; CLK/DATA/OUT ≥ 0,2 mm; USB só em B.Cu; peças sob o cartão MicroMod ≤ 1,9 mm.

## 5. DRC sem trilhas (kicad-cli, com paridade)
**0 erros de courtyard, furos, borda, altura sob o cartão; paridade placa × esquema 0.** O que aparece: 234 "ligações faltando" (esperado: sem trilhas) e **1 aviso** `isolated_copper` no plano +3V3 da In1 (sem vias ainda; some ao rotear). As 3 peças que a busca precisou mover (D205, D206, U302) estão em `posicao_v4.json` (`movidas`).

## 6. BOM e custo (JLCPCB, 21 nov; `bom_v4.csv`)
29 linhas, 77 peças, **13 tipos Extended** (o SH-6 serve às 4 fileiras e à tela) + 2 nas réguas = **15 < 17** da V3. Peças US$ 17,87 por placa (2 montadas = 35,7). Montagem econômica: 13 x 3,09 = 40,2 + 8,24 + 1,55 + SMT 3,2. PCB 4 camadas 75 x 95: US$ 14,5 a 39,5 (**estimativa**, taxa de engenharia 25). **Principal ≈ US$ 103 a 128** (2 placas, sem frete).

## 7. Roteabilidade (ratsnest, `pcb/img/ratsnest.png`)
61 redes (GND/+3V3 pelos planos), 1 844 mm de MST em 7 140 mm²: **26 mm/cm²**. Célula mais carregada 61 mm / 25 mm² no bloco de energia (canto de trás à direita) e ao redor do J101; o campo central é livre. F.Cu está praticamente vazia: o barramento das fileiras corre lá. Riscos: pares de pads 3/5 e U201 apertados (4,3 mm entre USB-C e M.2); J602 e o cabo de 2,5 mm; bloco de energia denso (herdado da V3).

## Perguntas para o design (deste portão)
1. USB-C na parede da esquerda em **y 10** (era 16) e módulo/H101 **5,5 mm à esquerda**: serve? Senão, USB na parede de trás.
2. Furos da placa: H2/H3/H4 como na V3 e H1 em (62; 48): confirma ou dá as posições dos pés da interface.
3. Régua da fileira 2 começa em x 79,95: o conector da régua e o do J602 podem ficar a 9 mm um do outro (plugue + curva)? Posição e boca do conector em cada ponta da régua.
4. Fenda do cabo da tela em (45,5..52,5; 22,2..24,7) (foi 32..39; 29,9): o OLED continua em (25..49; 15,5..28,5)? O conector SH-6 da tela é mais largo (9,8 mm).
