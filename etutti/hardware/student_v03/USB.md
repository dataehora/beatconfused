# Student V3 — o par USB (19 nov 2026)

Pedido do J: "eliminar a possibilidade de conexão USB instável, é crítico para o MIDI".

## O que havia (V3 de 18 nov)

| | D+ | D− |
|---|---|---|
| comprimento (do USB-C ao módulo) | 12,3 mm | 17,1 mm (diferença de ~5 mm) |
| vias | 0 | 2 (6,5 mm no topo) |
| larguras | 0,2 mm | 0,2 e 0,24 mm |
| plano de referência | In2 = pour de +3V3 com trilhas de sinal passando por baixo | idem |

A SPEC do V1 pedia diferença ≤ 2 mm, ≤ 2 vias por linha e GND contínuo por baixo. A V3 não cumpria a primeira e a terceira.

## O que é agora

`pcb/refaz_usb.py` (KiCad python) refaz o par e o que ele desloca; `pcb/costura_usb.py` costura a ilha de GND.

- **Tudo em B.Cu, do USB-C ao módulo, sem vias**: USB-C, USBLC6 e J101 estão no fundo. Caminhos de 45° escritos a partir dos pads (como o `route_usb.py` do V1), 0,2 mm de largura.
- **Comprimento** (do pad B6/A7 ao J101): **D+ 17,209 mm, D− 17,209 mm, diferença 0,000 mm**. Os dois cantos do trecho longo (esquerda, depois direita) trocam a linha de fora e quase se compensam; um pequeno trombone em D+ (0,69 mm de altura) fecha o resto. Limite da SPEC: 40 mm.
- **Acoplamento**: 0,327 mm centro a centro (vão 0,127 mm) onde os pads deixam, cerca de 6 mm dos 16 mm. Cálculo do projeto (`viaggio_micromod/pcb/build/impedance.json`, prepreg 7628 de 0,21 mm): ~92 Ω diferenciais acoplado. Fora desse trecho (abertura de 1,9 mm nos pads do USBLC6, passo de 0,5 mm do J101) as linhas ficam separadas e o valor sobe para ~115–125 Ω; como o conjunto tem ~100 ps de atraso (menos de 1/4 do tempo de subida do USB de alta velocidade), isso é um desvio pequeno e curto, não uma linha de transmissão longa. **É cálculo, não medida.**
- **In2 sob o par**: a In2 era o pour de +3V3. Agora há uma **ilha de GND** (prioridade sobre o +3V3) e uma **área proibida** para trilhas e vias sob o corredor; a ilha é ligada ao plano In1 por vias de GND (a do bolsão ao lado do USBLC6, 2 de costura e as que já havia).
- **Regras** (`.kicad_dru`): USB só em B.Cu, largura ≥ 0,19 mm, vão do par ≥ 0,127 mm, ≥ 0,25 mm de qualquer outra rede (o cobre de GND fica de fora).
- **R202** (resistor de 5,1 kΩ do CC2) passou para o lado norte do par, ao lado do pad de GND do USB-C, para o CC2 não cruzar o par. É a única peça que mudou de lugar (CPL).
- Vias do USBLC6: o pino 5 (VBUS) mantém a via entre as colunas do chip; o pino 2 (GND) ganhou uma via no bolsão a leste do pad.

Resultado: DRC com paridade só com as 3 larguras de EN_B já aceitas, 0 ligações faltando, paridade 0.

## O que não dá para garantir só no projeto

- Qualidade do sinal real (olho): só com osciloscópio rápido. Plano de teste na primeira placa: velocidade negociada ("High speed" no visualizador de USB), MIDI contínuo por minutos, dois cabos.
- Se ainda assim houvesse instabilidade, o próximo passo seria o controle de impedância da JLCPCB (taxa e prazo extras) e/ou um respin com o par totalmente acoplado.
