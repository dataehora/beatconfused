# Placa principal da Student V4 · como cotar na JLCPCB (R12V4)

**Estado (23 nov 2026): ARQUIVOS PRONTOS PARA COTAR, nada encomendado nem cotado como compra.** Gerados por `fab_principal.py` a partir da placa **roteada** (`kicad/student_v04_roteada.kicad_pcb`), sem rodar `posiciona_v4.py`. Preços **estimados** (`ELETRONICA.md`, R12V4), não cotações.

## Arquivos (esta pasta)
| Arquivo | O que é |
|---|---|
| `student_v04_gerbers.zip` | Gerbers + furação: **4 camadas de cobre** (F.Cu, In1.Cu, In2.Cu, B.Cu), pasta F/B, serigrafia F/B, máscara F/B, contorno, furação Excellon PTH (250) e NPTH (13), job |
| `bom.csv` | BOM no formato JLCPCB (Comment, Designator, Footprint, LCSC Part #): **32 linhas, 78 peças** |
| `cpl.csv` | CPL (Designator, Val, Package, Mid X, Mid Y, Rotation, Layer): **78 peças, todas no fundo (Bottom), 0 no topo** |
| `fora_da_montagem.csv` | o que a JLCPCB **não** monta: C310 (não montar), encoders SW401/SW402, pads do alto-falante J501, TP101, furos H1..H4 e H101 |
| `conferencias.json` | DRC, camadas, furos, códigos LCSC (classe, estoque, preço) |
| `student_v04_top.png`, `student_v04_bottom.png` | renders da placa |

## Conferências feitas
- **Placa:** 4 camadas, **1,2 mm**, 75,05 x 95,1 mm. **DRC com paridade da roteada: 0 violações, 0 não conectadas, 0 paridade.**
- **Gerbers x placa:** 4 arquivos de cobre (F_Cu, In1_Cu, In2_Cu, B_Cu); **furação: 250 PTH e 13 NPTH nos arquivos = 250 e 13 contados na placa** (vias + furos metalizados; furos não metalizados).
- **BOM x CPL:** as mesmas 78 referências (todas no fundo). **C310 não montado** (pad e posição mantidos para um 220-470 pF opcional); **R305 = 0 ohm** (C17168); **J401 = SH de 4 vias XY-SM04B-SRSS-TB (C51940130)**; **R605 e R606 = 330 ohm** (C25104); R216 e R105 = 100 ohm.
- **Códigos LCSC** (biblioteca da JLCPCB, 21-23 nov): os 32 têm estoque e preço; **14 tipos Extended** (US$ 3,09 por tipo), o resto Basic. Encapsulamento x footprint: o modelo da biblioteca da JLCPCB (coluna `modelo` de `conferencias.json`) é o do footprint do KiCad em todas as linhas (conferido pelo nome e pelo ajuste de pads do CPL); **conferir de novo na pré-visualização**. Estoque mais baixo: SGTL5000 (C2651833, 1 150), M.2 (C48985906, 553), PJ-327A (C49284723, 3 259), BQ24074 (C54313, 2 837).
- **CPL (método `cpl_jlc.py`):** pads da EasyEDA assentados nos pads da placa, **por número de pino em 20 das 22 famílias** (erro máximo 0,28 mm no BAV70, 0,25 no SMF5.0A, 0,23 no jack: dentro da tolerância de posicionamento); **por posição de pads em J201 (USB-C, erro 0,12 mm) e SW403 (botão Program, erro 0,03 mm; a posição se ajusta a 0 ou 180 graus: o botão é simétrico, mas confira na pré-visualização)**.
- **Clones SH:** XY-SM06B (C56123098, J601..J604) e XY-SM04B (C51940130, J401) **não existem na API da EasyEDA (404)**: usei o footprint do **original JST** (C160405 / C160404), com os mesmos pads. **Marcar a conferir na pré-visualização** o giro e o pino 1 dos cinco conectores SH.
- **BB_L1/BB_L2 (aceito):** os fios do indutor têm 0,35 mm por ~1 mm dentro do pátio do U204 (pinos de 0,5 mm). **Aceito:** ~1,4 mohm, ~6 mW a 2 A de pico; a corrente média no indutor é bem menor; o mínimo da JLCPCB é 0,09 mm.

## O que marcar na JLCPCB (sugestão; conferir na tela da cotação)
- **PCB:** 4 camadas, **1,2 mm**, pilha **JLC04121H-7628** (a da V3; conferir na tela), vias **0,5 / furo 0,3** (mínimo de furo 0,3 mm), trilha mínima 0,15 mm, folga 0,1 mm, **acabamento ENIG** (decisão do J na V3; o QFN-20 do SGTL5000 de passo 0,4 mm e o M.2 pedem pads planos; HASL é mais barato: cote os dois), máscara verde, **vias tampadas (tented)**, sem borda dourada, **sem impedância controlada** (o par USB tem 7,4 mm: 90 ohm só por cálculo, conferir).
- **Montagem (PCBA):** **só o fundo (Bottom)**, montagem econômica (se aceitar a placa de 75 x 95 mm), "Tooling holes: added by JLCPCB" (a placa não tem trilho; a JLCPCB acrescenta), confirmar a orientação na **pré-visualização** antes de pagar.
- **Quantidades mínimas:** **5 placas nuas e 2 montadas**; para as 32 teclas basta **1** montada: a segunda sai como reserva (US$ ~18 de peças).

## O que conferir na pré-visualização (o pino 1 e o giro)
1. **Pino 1** de **U201** (USBLC6, SOT-23-6), **U202** (BQ24074, VQFN-16), **U204** (TPS63001, DRC-10), **U301** (SGTL5000, QFN-20), **U302** (XC6206, SOT-23-3), **U501** (MAX98357A, TQFN-16); **BAV70** (D202, D203, D205, D206) e **SMF5.0A** (D201, polaridade); **AO3401A** (Q203, SOT-23).
2. **Giro dos conectores SH** J601..J604 (270 graus), J401 (180) e **J202** (JST PH, 180), **USB-C J201** (90), **jacks J301, J302** (180) e **M.2 J101** (270): confira a boca e o pino 1 contra o desenho do design (`FIT_CHECK.md`), principalmente os clones SH.
3. **Indutor L201** e o botão **SW403** (simétrico).

## Peças compradas à parte e montadas em casa (não vão na BOM da JLCPCB)
Módulo **SparkFun MicroMod Teensy (DEV-16402)** no M.2 + **parafuso M2,5 com espaçador de 2,5 mm** no H101; **OLED Adafruit 326** (US$ 17,50) e **cabo Qwiic / STEMMA QT de 50 mm** (~US$ 1) ao J401; **4 cabos SH** da placa às réguas (`A06SR06SR30K51B`, 45,8-50,8 mm); **4 réguas R8** (pedido à parte, `fab/regua/`); **bateria LiPo 1S 503450 (3 fios, NTC)** no J202; **alto-falante CE28MB-8** (fios soldados no J501); **2 encoders EC11E18244AU com os knobs** (solda em casa); **32 teclas Gateron KS-20 Orange**; **parafusos M2 passantes com porcas** e os de rosca para plástico (pelo design).

## Estimativa de custo (32 teclas, US$, pedido mínimo, sem frete/IVA; `ELETRONICA.md` R12V4)
Principal: PCB 14,5-39,5 (**estimativa**, 4L 75 x 95) + preparação e estêncil 9,79 + 14 Extended x 3,09 = 43,26 + peças das 2 montadas 35,7 + SMT 3,2 = **106,4-131,4**. Réguas (4 R8, pedido à parte): **44,0-60,9**. Cabos SH 4,8-5,7. OLED + cabo Qwiic 18,5. Ferragem 6-12 (estimativa). Case MJF ~48,5 (valor do design). Teclas, módulo, bateria, alto-falante, caixa acústica, USB, kit M2,5 e encoders (itens comuns da E3, reescalados para 32 teclas): ~90-131. **Total ≈ US$ 318-408** (o piso usa os preços por quantidade e o PCB mínimo; o teto, o preço de 1 peça e o PCB de 39,50).

## Riscos
1. **Clones SH sem footprint na EasyEDA** (cinco conectores): giro e pino 1 só se confirmam na pré-visualização.
2. **Preço do PCB principal** (engenharia de 25 pode ou não valer para 75 x 95 mm): estimativa.
3. **Estoque baixo** do M.2 (553) e do SGTL5000 (1 150): conferir na hora.
4. **Tooling holes / trilho:** a placa não tem trilho; a JLCPCB acrescenta (custo possível).
5. **Par USB** sem controle de impedância (7,4 mm, sobre In2 = GND): conferir na bancada.
6. **SW403 e J201** casados por posição de pads (não por número): conferir.
