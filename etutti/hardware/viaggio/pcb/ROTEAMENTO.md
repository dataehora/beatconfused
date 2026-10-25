# eTutti Viaggio · roteamento manual (KiCad + Freerouting)

**25 out 2026, SPEC v2.1, passo 3.2.** Decisão do J: o roteamento é feito por ele no KiCad, com o
plugin Freerouting. O Code entrega a placa posicionada, as regras e o DSN; nada aqui está roteado.

## Arquivos

| Arquivo | O que é |
|---|---|
| `kicad/viaggio.kicad_pro` + `viaggio.kicad_pcb` | **a placa a rotear**: todas as 179 peças + 28 switches + 8 furos posicionados, zonas preenchidas, classes de rede, regras, empilhamento, serigrafia. Sem trilhas nem vias |
| `kicad/viaggio.kicad_dru` | regras próprias (BGA, sinais, USB, corrente), lidas pelo DRC do KiCad |
| `kicad/viaggio.kicad_sch` (+ 6 folhas) | o esquema. A placa está ligada a ele: "Atualizar placa a partir do esquema" (F8) não troca nada |
| `build/viaggio.dsn` | o mesmo, em Specctra DSN, para o Freerouting avulso (o plugin gera o seu) |
| `kicad/viaggio_rota_P_parcial.kicad_pcb` | o roteamento parcial do setor P que o roteador do Code deixou (18 erros de DRC, 3 ligações faltando). **Só referência**: os relógios e o par USB dele estão bons e podem ser copiados |
| `build/viaggio_top.png`, `viaggio_bottom.png`, `viaggio_posicionamento.svg` | o posicionamento, para conferir |
| `build/viaggio_handoff.json` | DRC da entrega: **0 erros**, paridade com o esquema 0, 2 avisos de ilha de cobre (normal sem trilhas), **499 ligações a rotear** |

Não rode o `build_board.py` depois de começar a rotear: ele refaz o `viaggio.kicad_pcb` do zero.
Se precisar refazer a entrega, rode `build_board.py` e depois `handoff_freerouting.py`.

## Empilhamento (JLCPCB JLC04121H-7628, 4 camadas, 1,2 mm)

| Camada | Uso (SPEC §5) | Espessura |
|---|---|---|
| F.Cu (1) | cima: knobs, conectores, capacitores do P1 | 35 µm |
| prepreg 7628 | | 0,2104 mm, εr 4,4 |
| In1.Cu (2) | **GND inteiro, sem cortes** (tipo "power" na placa) | 15 µm |
| núcleo | | 0,6 mm, εr 4,36 |
| In2.Cu (3) | GND com ilhas de +3V3 e VDD_SOC sob o setor P (tipo "power") | 15 µm |
| prepreg 7628 | | 0,2104 mm |
| B.Cu (4) | baixo: quase todos os chips, rota principal | 35 µm |

In1 e In2 estão marcadas como **power (plano)**: o Freerouting não passa trilha nelas e liga as redes
GND, +3V3 e VDD_SOC aos planos por vias. **Fora do setor P não há ilha de +3V3 no In2**, então o
+3V3 dos sensores, multiplexadores e codec sai em trilha. Se preferir, aumente a ilha do +3V3 no In2
antes de rotear (corredor C3 e setor T); o GND do In1 tem de ficar inteiro.

## Classes de rede e regras

| Classe | Redes | Largura | Folga | Via |
|---|---|---|---|---|
| Default | todos os sinais | 0,2 (0,1 dentro do pátio do BGA) | 0,1 | 0,45 / furo 0,2 |
| USB | USB_DP, USB_DN | **0,24, vão 0,15 (par diferencial)** | 0,1 | 0,45 / 0,2 |
| Corrente | VBUS, VSYS, VBAT, BB_L1, BB_L2 | **≥ 0,8** | 0,1 | 0,45 / 0,2 (use várias) |
| Nucleo | DCDC_IN, DCDC_LP, VDD_SOC | 0,4 | 0,1 | 0,45 / 0,2 |

- **USB 90 Ω:** 0,24 / 0,15 em F.Cu sobre o In1 dá Zdiff ≈ 91,2 Ω. Conta em `build/impedance.json`,
  feita pelo `impedance.py` (solver 2D, máscara 15 µm); a IPC-2141 dá 93,7 Ω. Comprimento ≤ 40 mm, no
  máximo um par de vias. O Freerouting não faz par diferencial: **rote o USB à mão** (Rotear → Par
  diferencial, tecla 6) e fixe as trilhas antes de rodar o plugin.
- **Vias:** 0,45 mm de diâmetro, furo 0,2. O script do Code registrou que a JLCPCB faz esse furo sem
  custo extra a partir de 0,45 **(conferir no orçamento: em algumas épocas o furo grátis começa em
  0,3)**. Se o orçamento cobrar, troque para 0,5/0,3 nas classes (Configurações da placa → Classes
  de rede) antes de rotear. Com 0,3 de furo, a saída do BGA de 0,8 continua possível: via no centro
  de 4 bolas, folga ≈ 0,1.
- **BGA (P1, verso):** pads de 0,35 NSMD, passo 0,8. Saída em **dog-bone** (via entre 4 bolas), nunca
  via no pad. Cabe 1 trilha de 0,2 entre bolas vizinhas (vão 0,45 = 0,2 + 2 × 0,1). A regra de 0,1
  dentro do pátio do BGA está só no `.kicad_dru`, que o Freerouting não lê: ele usa os 0,2 da classe.
- Folga ao cobre da borda: 0,3. Furo a furo: 0,2. Anel livre de 3,5 em volta dos 8 furos M2 (áreas
  de regra, já na placa).

## Ordem de roteamento (SPEC §4)

À mão primeiro, depois o Freerouting para o resto:

1. **Relógios** (P5 → P1): Y101/Y102 e os capacitores, ≤ 5 mm, sem nada passando por baixo. A zona
   "GND cristais" no B.Cu fica embaixo deles. À mão.
2. **Saída do BGA e capacitores:** os capacitores do P1 estão no F.Cu, sobre o BGA. Faça o leque do
   BGA à mão, ou deixe para o Freerouting com as vias de alimentação primeiro: cada bola de GND,
   +3V3 e VDD_SOC com a sua via para o plano. O leque de alimentação do roteamento parcial está bom e
   pode ser copiado.
3. **USB C1** (E1 → E2 → P1): par diferencial à mão, sobre GND contínuo. O parcial tem um par de
   25,4 mm com skew de 0,01 mm, mas com um curto com uma trilha de GND junto da via: não copie aquela
   via.
4. **Memórias P3/P4:** ≤ 15 mm, comprimentos iguais ± 2 mm, sem vias se der.
5. **Fontes chaveadas** (E3, E4, DCDC do P1): indutor e capacitores colados ao chip, na mesma camada,
   várias vias ao GND. À mão.
6. **Corrente** (C2, C6, C7): classe Corrente ≥ 0,8 ou áreas no In2. À mão ou com o plugin.
7. **Áudio analógico** (C4): curto, longe do E4. Saída do A1 (chaveada) em par curto, longe do fone.
8. **I2S/I2C** (C5): o MCLK passa pelo R105, já junto do P1. Sempre sobre GND.
9. **Analógico das teclas** (C3): as 2 saídas dos mux com GND dos dois lados, **≥ 10 mm do indutor
   L201 (E4)**.
10. **Digital das teclas, digital lento:** o Freerouting.

Corredores (SPEC §5, linhas em `concept/rev2/out/viaggio_rev2.json` → `corridors`): C1 USB F.Cu,
C2 VBUS borda de trás, C3 teclas pelo B.Cu atrás da fileira 4, C4 fone B.Cu, C5 I2S B.Cu, C6 SYS,
C7 bateria.

## Freerouting no KiCad

1. Abra `kicad/viaggio.kicad_pro` no KiCad 10 e a placa. **Se o KiCad já estava aberto nesta placa,
   recarregue o arquivo** (Arquivo → Reverter): o arquivo em disco mudou em 25 out, à 01h30.
2. Rote à mão os itens 1–5 acima. Selecione o que estiver pronto e fixe com "Travar" (L), para o
   Freerouting não mexer.
3. Ferramentas → Plugins externos → Freerouting. O plugin exporta o DSN, roda o Freerouting e
   importa o SES sozinho. No Freerouting avulso: abra `build/viaggio.dsn`, rote, e exporte o
   `.ses`; no KiCad, Arquivo → Importar → Sessão Specctra.
4. Opções sugeridas do Freerouting:
   - camadas F.Cu e B.Cu (In1/In2 já aparecem como plano);
   - custo de via moderado, para o leque do BGA usar dog-bones;
   - deixe o otimizador ("optimize") rodar no fim.
5. Depois de importar: tecla B (preencher zonas), DRC com "Testar paridade com o esquema". Ligações
   não roteadas devem dar 0.
6. Os Gerbers, a BOM e o CPL da JLC ficam para o passo 3.4. O Code gera esses arquivos a partir da
   sua placa roteada, sem refazê-la.

## Peças que saíram alguns milímetros do `viaggio_rev2.json`

O posicionamento é o do `build_board.py`: cada código no seu ponto, passivos junto do chip.

- **Setor P:** posições à mão em `PLACE_P`, para o leque do BGA:
  - MKL02 sobre as bolas do bootloader (37,05; 5,95), em vez de (46; 9);
  - flash à esquerda das bolas da flash (23; 20,6), em vez de (47,5; 18);
  - PSRAM sob as bolas da PSRAM (37,65; 24), em vez de (47,5; 26,5);
  - cristal de 24 MHz ao lado do XTALI/XTALO (25,7; 10,5), em vez de (26; 23).
- **Entrega:** 4 peças movidas em passos de 0,1 mm para tirar sobreposições de pátio:
  - Y101 (−0,17; −0,10);
  - C121 (−0,20; 0);
  - C104 (−0,33; +0,35);
  - C120 (−0,10; −0,03).
- O pátio dos 8 furos M2 passou a ser a cabeça do parafuso (Ø 3,8). O de antes (Ø 4,95) encostava
  nos switches em volta. O anel livre de cobre de 3,5 continua.
