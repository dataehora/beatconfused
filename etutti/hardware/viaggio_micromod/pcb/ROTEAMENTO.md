# eTutti Viaggio MicroMod · placa para rotear

**SPEC v2.3, passo M2, 25 out 2026.** A placa está posicionada e sem trilhas. Quem roteia é o J, no
KiCad com o Freerouting, pelo guia "Viaggio: roteamento no KiCad, passo a passo".

**Não rode o `build_board.py` sobre a placa que o J rotear:** ele refaz o
`kicad/viaggio_micromod.kicad_pcb` do zero e apaga as trilhas.

**O par USB (USB_DP/USB_DN) já está roteado e travado** (`route_usb.py`, 25 out 2026, refeito com o
U201 girado 180°): não apague nem mova essas trilhas e vias, não rode o `build_board.py`, e pule o
item "USB: rote o par à mão" abaixo.

O par passa pelo U201 e cerca dois pinos dele. Cada um precisa de uma via 0,5/0,3, e os dois lugares
foram testados no DRC numa cópia da placa:
- **VBUS, pad 5 (lado esquerdo do U201):** via em **(16,30; 12,25)**, ligada ao pad por trilha de
  **0,8** (a regra Corrente vale também no pátio do U201). Folgas: 0,58 às trilhas USB e 0,55 ao pad.
- **GND, pad 2 (lado direito):** via em **(21,07; 12,25)**, trilha curta até o pad. Folgas: 0,12 ao
  pad, 0,16 ao D+ e 0,13 ao pad 15 do J101 (B.Cu). Não há outro lugar: à direita começa a fileira
  de pads do J101.

## Arquivos

| Arquivo | O que é |
|---|---|
| `kicad/viaggio_micromod.kicad_pro` + `.kicad_pcb` | **a placa a rotear**: 141 peças do esquema + 28 switches + 8 furos M2, classes, regras, empilhamento, zona de GND no In1. Sem trilhas nem vias |
| `kicad/viaggio_micromod.kicad_dru` | regras próprias (vias, sinais, USB, Corrente, altura sob o cartão) |
| `kicad/viaggio_micromod.kicad_sch` (+ 6 folhas) | o esquema. A placa está ligada a ele: F8 não troca nada |
| `build/viaggio_micromod.dsn` | Specctra DSN para o Freerouting avulso (o plugin gera o seu) |
| `build/viaggio_micromod_top.png`, `_bottom.png`, `_posicionamento.svg` | o posicionamento, para conferir |
| `build/viaggio_micromod_handoff.json` | DRC da entrega, posições, desvios do JSON, peças sob o cartão |

Refazer a entrega (só antes de rotear): `python schematic.py`, depois
`"C:/Program Files/KiCad/10.0/bin/python.exe" build_board.py`.

## Camadas (JLC04121H-7628, 1,2 mm)

| Camada | Uso | Tipo no KiCad |
|---|---|---|
| F.Cu | cima: knobs, USB-C, fone, E2, **par USB** | signal |
| In1.Cu | **GND inteiro, sem cortes** (zona "L2 GND") | power |
| In2.Cu | **trilhas**; sem nenhuma área agora (GND e 3,3 V entram no M3) | signal |
| B.Cu | baixo: módulo P1, chips, sensores, rota principal | signal |

## Classes e regras

| Classe | Redes | Largura | Folga | Via |
|---|---|---|---|---|
| Default | sinais | 0,2 (mínimo 0,15 na entrada de pinos finos) | 0,1 | 0,5 / 0,3 |
| USB | USB_DP, USB_DN | **0,24, vão 0,15** em F.Cu sobre o In1 (Zdiff ≈ 91 Ω, `build/impedance.json`) | 0,1 | 0,5 / 0,3 |
| Corrente | VBUS, VSYS, VBAT, BB_L1, BB_L2 | **≥ 0,8**, salvo dentro dos pátios de E1, E3, E4, E6, A1 e J101 | 0,2 | 0,5 / 0,3 (várias) |

- USB: rote o par à mão (Rotear → Par diferencial) em F.Cu, do J201 pelo U201 até junto do J101, e
  desça com o par de vias colado ao conector. Fora do pátio do J101, o `.kicad_dru` acusa trilha USB
  fora do F.Cu. O Freerouting não faz par diferencial.
- Sob o cartão do MicroMod (retângulo tracejado no B.SilkS, área de regra `cartao_MicroMod`): só
  peças de até 1,9 mm. O DRC acusa se uma peça com `Cabe_sob_cartao = nao` entrar lá.
- Anel de 3,5 mm sem cobre em volta dos 8 furos M2 (áreas de regra).
- O `.kicad_dru` não é lido pelo Freerouting: ele usa as larguras das classes.
