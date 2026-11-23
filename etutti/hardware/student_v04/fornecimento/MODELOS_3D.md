# Modelos 3D, posição, giro e pino 1 das peças montadas pela JLCPCB (R13V4)

23 nov 2026. Gerado por `fornecimento/gera_modelos_3d_md.py` a partir de `pcb/previa_jlc.py` (pré-visualização própria) e `fornecimento/baixar_modelos.py` (STEP da EasyEDA por código LCSC; pasta `fornecimento/modelos3d/` fora do git; índice `modelos3d_indice.json` no git).

## Resultado
- **Modelo 3D: todos os 34 códigos montados (principal + réguas) têm STEP na EasyEDA.** Nenhuma peça sem modelo. Os SH originais JST (C160405 e C160404) têm modelo; os clones (C56123098, C51940130) não tinham (404), por isso foram trocados.
- **Pino 1 e giro: nenhum erro.** O pad "1" de cada footprint da EasyEDA, passado pelas regras do CPL (`cpl_jlc.py`, fundo espelhado), cai a no máximo 0,25 mm do pad "1" da placa; os demais pads numerados idem. Nos CIs de 5 ou mais pads, o marcador do pino 1 **do próprio modelo** (a cova na tampa do corpo, achada na geometria do STEP) cai junto do pino 1 (U201, U202, U204, U301, TMAG5253 e 74HC595 das réguas). O **U501 (MAX98357)** e os SOT-23 (D202, D203, D205, D206, Q203, U302) **não têm marcador na geometria**: a orientação deles vem do desenho dos terminais (erro 0 no giro nominal). SW403, L201, FB301, capacitores e resistores não têm polaridade.
- **Boca dos conectores: sem erro** (tabelas): USB-C e os dois jacks viram para a borda esquerda, J601 a J604 para a borda direita, J401 para a fenda do cabo, J202 para a baia da bateria; o M.2 (J101) tem o corpo simétrico em x e a boca foi conferida na figura (encaixe para o espaçador H101).
- **Erro de ajuste ≤ 0,3 mm: todos, exceto 4 códigos** cujo modelo da **biblioteca da EasyEDA** vem deslocado do footprint (o `c_origin` do modelo não coincide com o centro dos pads): **C15850 (10 µF 0805, 8 peças na principal e 1 por régua, 1,35 mm), C1002 (FB301, 1,65 mm), C7519 (U201, 0,92 mm) e C19702 (C210, 0,40 mm)**. É só a **aparência** na pré-visualização (corpo desenhado fora dos pads): o **CPL está certo** (posição e giro vêm dos pads, erro ≤ 0,25 mm) e a solda não depende do modelo. Equivalentes Basic com modelo melhor não existem; um Extended custa US$ 3,09 por tipo por pedido; **não troquei**. O KiCad (`kicad/*_3d.kicad_pcb`) mostra os 4 já corrigidos.
- A regra de colocação da EasyEDA que reproduzi (testada nos 34 modelos): o **centro do corpo (xy) do STEP vai para o `c_origin`**, o **ponto mais baixo fica na cota `z`**, giro pelo `c_rotation`; o `c_origin` do C730243 (74HC595) vem com erro de unidade (400,300 contra 4000,3000) e foi tomado como 0. **Se a JLCPCB usar outra regra, a figura dela difere da minha só nesses pequenos deslocamentos**; pino 1 e boca não dependem dela.

## Figuras (pré-visualização própria, igual à da JLCPCB)
`pcb/img/previa_jlc_principal_bottom.png`, `previa_jlc_principal_top.png`, `previa_jlc_r8_bottom.png`, `previa_jlc_r8_top.png`: modelos nas posições do `cpl.csv` sobre a placa, referência escrita em cada peça, **anel vermelho = pad 1 da placa**; no topo da principal, as peças de casa só com os pads. A vista de baixo é espelhada (placa virada em torno do eixo vertical). Em KiCad com os mesmos STEP ligados: `kicad/student_v04_roteada_3d.kicad_pcb` e `kicad/regua/student_v04_regua8_roteada_3d.kicad_pcb` (cópias; as placas roteadas não foram tocadas; caminhos relativos para `fornecimento/modelos3d/kicad/`, fora do git), renders `pcb/img/modelos3d_{principal,r8}_{bottom,top}.png`. Reproduzir: KiCad python `pcb/previa_dados.py principal|r8|r4`; venv CadQuery `pcb/previa_jlc.py fit|draw`, `pcb/modelos_kicad.py`; KiCad python `pcb/liga_modelos.py`.

## Tabelas (erro de ajuste = maior distância de um pad ao corpo do modelo; 0 = todos os pads sob o modelo)

### Placa principal (78 peças montadas pela JLCPCB, todas no fundo)

| Refs | LCSC | Modelo 3D (EasyEDA) | Modelo | Erro de ajuste (mm) | Pino 1 do CPL (mm) | Marcador do pino 1 no modelo | Boca | Nota |
|---|---|---|:-:|---:|---:|---|---|---|
| C101 ... C501 (8) | C15850 | C0805_L2.0-W1.3-H1.3 | sim | 1.40 | 0.05 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| C102 ... C502 (11) | C1525 | C0402_L1.0-W0.5-H0.5 | sim | 0.00 | 0.06 | - | - |  |
| C210 | C19702 | C0603_L1.6-W0.8-H0.8 | sim | 0.40 | 0.07 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| C301, C303, C306 | C12530 | C0402_L1.0-W0.5-H0.5 | sim | 0.00 | 0.06 | - | - |  |
| C309 | C52923 | C0402_L1.0-W0.5-H0.5 | sim | 0.00 | 0.06 | - | - |  |
| D201 | C151296 | SOD-123FL_L2.8-W1.8-LS3.7-RD-1 | sim | 0.00 | 0.25 | - | - |  |
| D202, D203, D205, D206 | C68978 | SOT-23-3L_L2.9-W1.6-H1.1-LS2.8-P0.95 | sim | 0.00 | 0.11 | - | - |  |
| FB301 | C1002 | L0603_L1.6-W0.8-H0.5_BEAD | sim | 1.65 | 0.09 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| J101 | C48985906 | PCIE-SMD_75P-P0.50_91302-42-067RCM | sim | 0.20 | 0.00 | - | +y (cima); esperado +x (para H101): visual |  |
| J201 | C165948 | USB-C_SMD-TYPE-C-31-M-12_1 | sim | 0.00 | - | - | -x (esquerda); esperado -x (borda esquerda): ok | pads com nomes diferentes: pino 1 conferido pela posição (erro máx. dos pads 0.03) |
| J202 | C265101 | CONN-SMD_PH2.00-WS-3P | sim | 0.00 | 0.00 | - | -y (baixo); esperado -y (para a baia da bateria): ok |  |
| J301, J302 | C49284723 | AUDIO-SMD_XUNPU_PJ-327A | sim | 0.00 | - | - | -x (esquerda); esperado -x (borda esquerda): ok | pads com nomes diferentes: pino 1 conferido pela posição (erro máx. dos pads 0.23) |
| J401 | C160404 | CONN-SMD_SR1.00-WS-4P | sim | 0.00 | 0.00 | - | +y (cima); esperado +y (para a fenda do cabo): ok |  |
| J601, J602, J603, J604 | C160405 | CONN-SMD_SR1.00-WS-6P | sim | 0.00 | 0.00 | - | +x (direita); esperado +x (borda direita): ok |  |
| L201 | C167825 | IND-SMD_L4.0-W4.0-H2.6_FNR40XXS | sim | 0.00 | 0.00 | - | - |  |
| Q203 | C15127 | SOT-23-3P_L2.9-W1.3-H1.0-LS2.4-P0.95 | sim | 0.00 | 0.14 | - | - |  |
| R105, R216 | C25076 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R201, R202 | C25905 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R203, R301, R302 | C25879 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R204 | C25867 | R0402_L1.0-W0.5-H0.4 | sim | 0.00 | 0.08 | - | - |  |
| R205, R214 | C25744 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R206 ... R604 (11) | C25741 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R208, R209, R212, R304, R501 | C26083 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R305 | C17168 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| R605, R606 | C25104 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| SW403 | C318884 | SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5 | sim | 0.00 | 0.03 | - | - |  |
| U201 | C7519 | SOT-23-6_L2.9-W1.6-H1.5-LS2.8-P0.95 | sim | 0.92 | 0.01 | ok (pads 2/1) | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| U202 | C54313 | QFN-16_L3.0-W3.0-P0.50-EP1.7 | sim | 0.00 | 0.06 | ok (pads 16/1) | - |  |
| U204 | C28060 | VSON-10_L3.0-W3.0-H0.6-P0.50_TPS | sim | 0.00 | 0.10 | ok (pads 1/2) | - |  |
| U301 | C2651833 | QFN-20_L3.0-W3.0-P0.40-BL-EP1.7 | sim | 0.00 | 0.04 | ok (pads 20/1) | - |  |
| U302 | C347373 | SOT-23-3L_L2.9-W1.6-H1.1-LS2.8-P0.95 | sim | 0.00 | 0.02 | - | - |  |
| U501 | C910544 | TQFN-16_L3.0-W3.0-P0.50-BL-EP1.5 | sim | 0.00 | 0.06 | - | - |  |

### Régua R8E em painel de 2 (a R8 é a mesma sem J2 e R1)

| Refs | LCSC | Modelo 3D (EasyEDA) | Modelo | Erro de ajuste (mm) | Pino 1 do CPL (mm) | Marcador do pino 1 no modelo | Boca | Nota |
|---|---|---|:-:|---:|---:|---|---|---|
| C1-1 ... C9-2 (18) | C1525 | C0402_L1.0-W0.5-H0.5 | sim | 0.00 | 0.06 | - | - |  |
| C10-1, C10-2 | C15850 | C0805_L2.0-W1.3-H1.3 | sim | 1.35 | 0.05 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| J1-1, J1-2, J2-1, J2-2 | C160405 | CONN-SMD_SR1.00-WS-6P | sim | 0.00 | 0.00 | - | - |  |
| R1-1, R1-2 | C25104 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| U1-1 ... U8-2 (16) | C22401868 | X2SON-4_L1.4-W1.1-P0.50-TR-EP | sim | 0.10 | 0.07 | - | - |  |
| U9-1, U9-2 | C730243 | DHVQFN-16_L3.5-W2.5-H1.0-P0.50 | sim | 0.00 | 0.03 | - | - |  |

### Régua R4E em painel de 5 (só tabela; R8E, R4 e R4E repetem as mesmas peças)

| Refs | LCSC | Modelo 3D (EasyEDA) | Modelo | Erro de ajuste (mm) | Pino 1 do CPL (mm) | Marcador do pino 1 no modelo | Boca | Nota |
|---|---|---|:-:|---:|---:|---|---|---|
| C1-1 ... C5-5 (25) | C1525 | C0402_L1.0-W0.5-H0.5 | sim | 0.05 | 0.06 | - | - |  |
| C6-1, C6-2, C6-3, C6-4, C6-5 | C15850 | C0805_L2.0-W1.3-H1.3 | sim | 1.35 | 0.05 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |
| J1-1 ... J2-5 (10) | C160405 | CONN-SMD_SR1.00-WS-6P | sim | 0.00 | 0.00 | - | - |  |
| R1-1, R1-2, R1-3, R1-4, R1-5 | C25104 | R0402_L1.0-W0.5-H0.4 | sim | 0.05 | 0.08 | - | - |  |
| U1-1 ... U4-5 (20) | C22401868 | X2SON-4_L1.4-W1.1-P0.50-TR-EP | sim | 0.10 | 0.07 | - | - |  |
| U5-1, U5-2, U5-3, U5-4, U5-5 | C730243 | DHVQFN-16_L3.5-W2.5-H1.0-P0.50 | sim | 1142.50 | 0.03 | - | - | modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido |

## Peças montadas em casa: modelo na cena do instrumento (`student_v04/case`)
| Peça | Modelo na cena | Fiel? |
|---|---|---|
| OLED Adafruit 326 | placa com orelhas, furos, vidro, área ativa, corpos dos 2 SH4 | **fiel** (medidas lidas do arquivo de placa da Adafruit) |
| Encoders EC11E18244AU (C202365) | caixa 12 x 13,4 x 4,5 + eixo D com chato | **só caixa/cilindro** (STEP da EasyEDA já baixado em `student_v03/case/modelos/`, não ligado) |
| MicroMod Teensy | cartão 22 x 22 mais uma caixa | **só caixa** |
| Alto-falante Dayton CE28MB-8 | cilindro Ø28 x 4,5 | **só cilindro** |
| Bateria 503450 | caixa 34 x 50 x 5 | **só caixa** |
| Teclas KS-20 Orange | corpo, aba cônica e haste | **aproximado** (desenho da Gateron; o STEP KS-20T existe em `fornecimento/gateron/`) |
| Parafusos, porcas, pés | cilindros e hexágonos | só formas |
Pendência de fidelidade, sem efeito na compra: ligar os STEP do EC11E, do MicroMod e da KS-20 à cena (pedido ao design).

## Riscos
1. A regra de colocação da EasyEDA foi deduzida dos dados dos 34 modelos, não de documentação: a figura da JLCPCB pode diferir nos 4 códigos acima.
2. O marcador do pino 1 foi achado na geometria; um marcador só pintado (sem relevo) não aparece.
3. A pré-visualização real da JLCPCB é a conferência final (lista na folha de cotação de cada placa).
