# eTutti Viaggio MicroMod · relatório da eletrônica

## Par USB refeito com o U201 girado 180° (SPEC v2.3, respostas da gestão ao PR #120, 25 out 2026)

A gestão respondeu às duas perguntas do PR #120. Primeiro, girar o U201 (E2, USBLC6-2SC6) 180° e
refazer o par reto, sem a volta e sem o laço. Segundo, conferir no desenho da HRO a junção do D−
sob o corpo do USB-C. As regras não mudaram:
- F.Cu fora do pátio do J101, 0,24/0,15, 45°;
- vias 0,5/0,3 só no pátio do J101;
- no máximo 40 mm por rede, 2 mm de diferença e 2 vias por rede;
- tudo travado.

Nenhuma outra rede foi roteada.

**Antes de rodar o `build_board.py`**, contei as trilhas da placa do PR #120: 53 segmentos, 2 vias,
nenhum arco, **todos de USB_DP/USB_DN**. Então ele podia rodar.

| Medida | USB_DP | USB_DN |
|---|---|---|
| Comprimento J201 → J101 (caminho do sinal) | **21,50 mm** | **21,97 mm** |
| Cobre total da rede (com a junção dos dois pads do J201) | 23,47 mm | 24,73 mm |
| Vias (0,5/0,3, dentro do pátio do J101) | **1** | **1** |

- **Diferença de comprimento: 0,47 mm** no caminho do sinal e 1,26 mm no cobre total. Antes eram
  32,90/32,74 mm, com laço.
- **O caminho:**
  - O par sai do J201 em F.Cu, com o D− em cima, e se abre a 45° em volta do pad 5 (VBUS) do U201:
    o D− sobe para a fileira de cima (pads 4 → 3), o D+ desce para a de baixo (6 → 1).
  - Atravessa o chip pelos próprios pads (passagem direta) e se fecha de novo à direita do pad 2
    (GND).
  - Sobe pela borda do J101, passa da fileira de pads, vira para leste e depois para o sul, entre as
    fileiras de pinos.
  - Desce pelas duas vias lado a lado: D+ em (23,86; 9,55), D− em (24,48; 9,55), 0,62 entre
    centros. Tocos de 0,20 em B.Cu levam o D+ ao pad 3 e o D− ao pad 5.
- **Por que o gancho no J101.** O J101 pede o D+ (pad 3) acima do D− (pad 5), a ordem contrária à
  do par. Numa camada só, a ordem se inverte quando o par chega aos pads andando para oeste, e isso
  pede uma volta perto do conector.
  - No PR #120 essa volta era para a esquerda: o D+ ficava por fora e ganhava ~2,2 mm.
  - Agora são duas viradas para a direita, e o D− fica por fora. Isso compensa os ~1,9 mm que o D+
  sobe à direita do U201, de uma fileira de pads à outra. Por isso não há laço nem sanfona.
- **Junção do D− (J201):** ficou como estava, em F.Cu sob a traseira do conector, sem via (ver o
  desenho abaixo). As duas vias por rede continuam sendo só as do J101.
- **Peças:** só o U201 mudou de rotação. Na mesma posição (18,9; 12,25), agora com rot 180. O D201
  andou 0,015 mm (17,000 → 16,985): o `build_board.py` põe cada passivo no centro dos pads da
  rede dele, e o pad de VBUS do U201 trocou de lado. Nenhuma outra peça mudou de lugar, lado ou
  rotação.
- **DRC** (`kicad-cli pcb drc --schematic-parity --severity-all`, com o `.kicad_dru` da placa):

  | | Violações | Paridade | Não roteadas |
  |---|---|---|---|
  | antes (placa do PR #120) | 0 | 0 | 423 |
  | `build_board.py` (U201 girado, sem trilhas) | 0 | 0 | 431 |
  | depois do `route_usb.py` | **0** | **0** | **423** |

  USB_DP e USB_DN ficam com **0 ligações faltando**. Saiu limpo na **1ª tentativa**.
- **O que o `build_board.py` reescreveu (git diff).** Comparei a placa nova com a do PR #120 peça a
  peça, no pcbnew:
  - mesmas 177 peças, as mesmas 1047 figuras e textos e as mesmas zonas;
  - posições, lados e redes de pads iguais, fora o U201 (rotação) e o D201 (0,015 mm);
  - o cabeçalho do `.kicad_pcb` (setup, empilhamento, camadas) é idêntico byte a byte;
  - o `.kicad_pro` não mudou;
  - o `.kicad_dru` só mudou o fim de linha e foi restaurado do git.

  O diff do `.kicad_pcb` é grande (~41 mil linhas) porque o `build_board.py` cria a placa do zero e
  cada objeto ganha um UUID novo. Os caminhos que ligam as peças ao esquema são os mesmos 141. O DSN,
  o SVG e o `_drc.json` mudam pelo mesmo motivo.
- **Imagens**, conferidas: `pcb/build/route_usb_top.png` (F.Cu) e `pcb/build/route_usb_bottom.png`
  (B.Cu visto de cima, sem espelhar), grade de 1 mm. `pcb/build/viaggio_micromod_top.png` mostra o
  U201 girado. O `_bottom.png` saiu igual. Essas duas são do `build_board.py`, sem trilhas.

### Vias que o J vai pôr no U201

O par cerca dois pinos do U201. Os lugares abaixo foram testados numa cópia da placa (fora do
repositório), com via 0,5/0,3 e trilha até o pad. O DRC deu 0 violações de folga; só acusou a via
de VBUS "solta", porque ainda não liga a nada.

| Pino | Via em | Trilha até o pad | Folgas |
|---|---|---|---|
| **VBUS, pad 5** (esquerda, entre D− e D+) | **(16,30; 12,25)** | **0,8** (a regra Corrente não isenta o pátio do U201) | 0,58 às trilhas USB, 0,55 ao pad 5, 0,58 ao pad GND do R201 (B.Cu) |
| **GND, pad 2** (direita, entre D− e D+) | **(21,07; 12,25)** | curta, 0,3 | 0,12 ao pad 2, 0,16 ao D+, 0,13 ao pad 15 do J101 (B.Cu, sem rede) |

A via de GND não tem outro lugar: logo à direita começa a fileira de pads do J101, no verso. Os
pinos do J201 saem como antes: GND, VBUS e CC1 para cima, acima do par; CC2, VBUS e GND por baixo.

### Junção do D− e o desenho da HRO

O desenho é o **HRO TYPE-C-31-M-12, folha 1 de 1, rev. A, 08/12/2020**, lido com o WebFetch.
- O link da LCSC (`lcsc.com/datasheet/C165948.pdf`) devolve só uma página HTML.
- O PDF que abriu foi o da HQ Online:
  [file1.huaqiu.com/.../wKgZPGmqPlGAaTPnAAHNXNNJTw8053.pdf](https://file1.huaqiu.com/web3/M00/4D/71/wKgZPGmqPlGAaTPnAAHNXNNJTw8053.pdf).
- O WebFetch guarda a cópia em cache na pasta de resultados de ferramentas da sessão, fora do
  repositório. Nenhum arquivo foi baixado para o projeto.

O que o desenho mostra:
- **Vista de cima** (alto, à esquerda): corpo de **8,94 × 7,35**. As pernas dos contatos passam
  **0,40 ± 0,10** da traseira do corpo. No footprint do KiCad, a traseira do corpo (F.Fab) fica em
  **x 8,35**, e os pads vão de 8,02 a 9,47.
- **Vista de baixo** (embaixo, à esquerda, cota **6,28**): a chapa metálica cobre a parte de baixo
  só por 6,28 a partir da frente. O resto até a traseira é a faixa de plástico do isolador, de onde
  saem as pernas. Os dois pinos de plástico de posicionamento (Ø 0,50, a 5,78 um do outro; furos
  Ø 0,65 do footprint em x 7,30) ficam nessa faixa.
- **Na placa:** a frente do corpo está em x 1,05, então a chapa de baixo termina perto de **x 7,33**.
  A junção do D− ocupa **x 7,63 a 8,07** (trilha de 0,24 centrada em 7,75). Fica ~0,3 atrás do fim
  da chapa, sob o plástico, entre os pinos de posicionamento e a traseira. **Não há metal da
  carcaça sobre esse trecho.** As pernas laterais da carcaça (pads SH em x 7,83) ficam nas pontas,
  em y 8,68 e 17,32, longe da trilha.
- **(conferir)** O desenho não cota a faixa de plástico diretamente. Os ~0,3 saem da diferença
  7,35 − 6,28 e da posição dos pinos. A trilha também fica coberta pela máscara.
- Por isso a **junção ficou como estava, sem via**, e a regra "USB só em F.Cu" não foi afrouxada.

Refazer só o USB (depois do `build_board.py`, se ele precisar rodar de novo antes do J rotear):

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/route_usb.py
```

`PINOS.md`, `POWER.md`, o esquema e o `.kicad_dru` não mudaram. `pcb/ROTEAMENTO.md` ganhou os dois
lugares de via do U201.

### Perguntas para a gestão (par USB, U201 girado)

1. **Gancho na entrada do J101:** o par passa 0,6 mm além da fileira de pads (até y 8,4), vira e
   desce entre as fileiras. É isso que iguala os comprimentos sem laço. Aceitável assim, ou prefere
   a descida direta do PR #120? Ela deixaria uns 3,6 mm de diferença e pediria um laço de novo.
2. **Via de GND do U201 em (21,07; 12,25):** fica com 0,12–0,16 de folga, acima do mínimo de 0,1.
   Aceita, ou prefere que o par se feche mais à direita para abrir espaço? O par passaria por cima
   da fileira de pads do J101, sem mudar de camada.
3. **Junção do D−:** pela vista de baixo do desenho da HRO não há metal ali, e ela ficou sem via.
   Confirmar com uma peça de verdade quando chegar **(conferir)**.

## Par USB roteado, 1ª versão (PR #120, substituída pela seção acima)

O J autorizou o Code a rotear **só** USB_DP e USB_DN. Nenhuma outra rede foi tocada. Não houve
roteador nem busca de caminho: o `pcb/route_usb.py` (python do KiCad 10) escreve cada segmento com
coordenadas calculadas a partir dos pads do J201, do U201 e do J101. Ele parte da placa do PR #119,
não roda o `build_board.py`, trava (locked) todas as trilhas e vias e reenche só as zonas. Pode ser
rodado de novo: apaga antes as trilhas e vias que ele mesmo gravou (UUIDs em
`build/route_usb.json`) e para sem salvar se houver trilha USB que não seja dele. O diff do
`.kicad_pcb` traz só as trilhas e vias novas e o preenchimento da zona de GND do In1. O
`SaveBoard` do pcbnew reescrevia o `.kicad_pro`, o empilhamento e as fontes; o script não deixa
isso acontecer.

| Medida | USB_DP | USB_DN |
|---|---|---|
| Comprimento J201 → J101 (caminho do sinal) | **32,90 mm** | **32,74 mm** |
| Cobre total da rede (com a junção dos dois pads do J201) | 34,87 mm | 35,50 mm |
| Vias (0,5/0,3, dentro do pátio do J101) | **1** | **1** |

- **Diferença de comprimento: 0,15 mm** no caminho do sinal e 0,63 mm no cobre total.
- **Largura 0,24 e vão 0,15** em F.Cu, sobre o GND do In1, sempre a 45°. Dentro do pátio do J101,
  os dois tocos em B.Cu que chegam aos pads 3 e 5 têm 0,20.
- **J201:** os dois pads de D− (B7, A7) se unem em F.Cu por trás da fileira de pads, sob o corpo
  do conector, a x 7,75. Os dois de D+ (A6, B6) se unem à direita da fileira. Não há via de união.
- **J201 → U201 → J101, todo em F.Cu:** o par passa por baixo do U201, faz a volta pelo lado
  direito dele e entra nos pads 6/4. Atravessa o chip pelos próprios pads (6→1, 4→3, ligação
  direta), sai pela esquerda, sobe e volta por cima do U201 até o J101. As duas vias ficam entre
  as fileiras de pinos do J101. Os tocos em B.Cu ligam D+ ao pad 3 e D− ao pad 5.
- **Por que a volta.** Do J201 o D− sai sempre acima do D+: os pads vêm na ordem D−, D+, D−, D+, e
  numa camada só é impossível outra saída. No U201 (rot 0) o D+ está na fileira de cima. O
  `.kicad_dru` só deixa trilha USB fora do F.Cu dentro do pátio do J101. A volta em U é o único
  jeito de inverter o par sem trocar de camada. O D− compensa o comprimento com um laço no lado
  esquerdo do U201.
- **DRC** (`kicad-cli pcb drc --schematic-parity --severity-all`, com o `.kicad_dru` da placa):

  | | Violações | Paridade | Não roteadas |
  |---|---|---|---|
  | antes | 0 | 0 | 431 |
  | depois | **0** | **0** | **423** |

  As 8 ligações a menos são as do USB: USB_DP e USB_DN ficam com **0 ligações faltando**. Saiu
  limpo na 1ª tentativa de DRC. A 1ª versão tinha 4,8 mm de diferença de comprimento; na 2ª
  entraram o laço e a volta do D− junto da do D+.
- **Imagens ampliadas**, conferidas: `pcb/build/route_usb_top.png` (F.Cu) e
  `pcb/build/route_usb_bottom.png` (B.Cu visto de cima, sem espelhar), grade de 1 mm.
- **Para o J, ao rotear o resto:** o par em F.Cu cerca dois pinos do U201. Cada um precisa de uma
  via:
  - **GND, pad 2:** o lugar da via fica dentro do laço do D−, à esquerda do pad, em torno de
    (16,6; 12,25). Há bastante espaço.
  - **VBUS, pad 5:** o lugar fica entre o pad e a volta do D+, em (21,05; 12,25). As folgas são de
    0,14 ao pad e à trilha e de 0,11 ao pad 15 do J101, em B.Cu.
  - Os pinos de cima do J201 (GND, VBUS, CC1) saem para cima e para a direita, acima do par. Os de
    baixo (CC2, VBUS, GND) saem por baixo do par.
- **Junção do D− sob o corpo do USB-C (conferir):** a trilha passa até 0,4 mm além do fim dos pads (x 7,63 a 7,87),
  sob a traseira do HRO TYPE-C-31-M-12, coberta pela máscara. Conferir no desenho da HRO se a
  carcaça metálica não encosta ali.
- **Arquivo aberto no KiCad:** no começo havia um `~viaggio_micromod.kicad_pcb.lck` (VISION/julia),
  que no fim já tinha sumido. Se alguma janela do KiCad ainda tiver a placa antiga aberta, feche
  sem salvar e abra de novo, senão o par USB se perde.

Refazer só o USB:

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/route_usb.py
```

O script sai com erro se o DRC não der 0/0, se faltar ligação no USB, se uma rede passar de 40 mm,
se a diferença passar de 2 mm, se uma rede tiver mais de 2 vias ou se algo ficar destravado.
`PINOS.md`, `POWER.md` e o esquema não mudaram.

### Perguntas para a gestão (par USB), já respondidas: U201 girado e junção conferida (seção acima)

1. **Volta em torno do U201 ou U201 girado 180°?** Girado, o D+ do U201 fica embaixo, na mesma
   ordem em que o par sai do J201. O par iria reto do J201 pelo U201 até o J101, com cerca de 20 mm
   (estimativa), sem volta nem laço de compensação. Isso muda o posicionamento (`build_board.py`)
   e o `route_usb.py`. Como o J ainda não roteou, dá para fazer agora. Fica a volta atual (33 mm,
   DRC limpo) ou giro o U201?
2. **Junção do D− sob o corpo do USB-C:** aceitável, ou prefere a união por via? A união por via
   pede afrouxar a regra "USB só em F.Cu" dentro do pátio do J201 e gasta mais 2 vias no D−.

**SPEC v2.3, passo M2 (placa para rotear), 25 out 2026.** Dono: eletrônica. A placa está posicionada
e **sem trilhas e sem vias**: nenhum roteador foi usado (o `router.py` do v2.1 não foi copiado nem
importado). Nada foi encomendado.

## Passo M2: resultado

| Conferência | Resultado |
|---|---|
| ERC do esquema | **0 erros, 0 avisos** |
| Netlist do KiCad × lista do script | igual (99 redes, 141 peças, 6 folhas) |
| DRC da entrega (`kicad-cli pcb drc --schematic-parity --severity-all`) | **0 erros, 0 avisos** |
| Paridade com o esquema | **0** |
| Ligações a rotear | **431** (T 220, E 98, F 31, P 12, A 11, I 7, entre setores 52) |
| `.kicad_dru` | compila no KiCad 10.0.7 sem erro; as 6 regras próprias disparam num teste com violações de propósito |
| Peças sob o cartão do MicroMod | C101 (1,45), C102 (0,55), R301 (0,4), R302 (0,4): **todas ≤ 1,9 mm** |
| Peças fora do perfil A | nenhuma, além de E1 e F2 (permitidas) |
| Sobreposição de pátios | nenhuma; nenhuma peça precisou ser empurrada |

Por setor, as 431 ligações: T 220, E 98, F 31, E-P 14, P 12, A 11, F-P 11, I-P 8, P-T 7, I 7,
A-F 3, E-I 3, E-T 2, e 1 em cada um de A-E, A-I, A-P e F-I.

### O que foi feito

- **M2a, esquema** (`pcb/schematic.py`, `pcb/footprints.py`):
  - **J101 = UMAX 91302-42-067RCE** (LCSC C48985906) no lugar do LOTES. O footprint foi refeito pelo
    desenho da UMAX e se chama `M.2_E_H4.2_UMAX_91302-42-067`. O do M1, com o nome do TE, foi apagado.
  - **H101 continua o Würth 9774025151R** por Global Sourcing (ver abaixo).
  - **E2 no lado de cima** (U201 e o TVS D201). O esquema não guarda lado: ficou na nota das duas
    peças ("lado de cima, junto do USB-C (SPEC v2.3)"), no `bom_preliminar.csv`, e o lado de fato está
    no `build_board.py`.
  - `bom_preliminar.csv` regerado (J101 e notas). **`PINOS.md` não mudou:** nenhum pino mudou.
- **M2b, placa** (`pcb/build_board.py`, um script só, que junta o `build_board.py` e o
  `handoff_freerouting.py` do v2.1, sem a parte de roteamento):
  - contorno 246,5 × 95 com cantos R 5; 8 furos M2 do contrato, com anel livre de cobre de 3,5 (áreas
    de regra) e pátio do tamanho da cabeça do parafuso (Ø 3,8);
  - serigrafia: perfil A pontilhado, E1/F2 do v1 tracejados, área do logo, códigos P1…T4 e o
    contorno do cartão do MicroMod no B.SilkS;
  - todas as peças pelo `concept/out/viaggio_micromod.json`, com os passivos junto dos seus chips;
  - a placa ligada ao esquema (F8 limpo), com redes `unconnected-(...)` nos pinos livres;
  - empilhamento JLC04121H-7628 de 1,2 mm. **In1 = GND**, tipo power, com uma zona de GND inteira.
    **In2 = signal, sem nenhuma área.** F.Cu e B.Cu são signal;
  - classes, regras, `.kicad_dru`, DSN e imagens. O DRC tem de dar 0 erros, senão o script sai com
    erro. Também sai com erro se houver peça alta sob o cartão, trilha ou via na placa, ou falha do DSN.
- **`pcb/ROTEAMENTO.md`** curto: arquivos, camadas, classes, e "não rode o `build_board.py` sobre a
  placa que o J rotear".

Para refazer a entrega (só antes de rotear):

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_micromod/pcb/build_board.py
```

São ~1 min. Saídas em `pcb/build/`:
- `viaggio_micromod.dsn`;
- `viaggio_micromod_top.png` e `_bottom.png`;
- `viaggio_micromod_posicionamento.svg`;
- `viaggio_micromod_handoff.json`, com DRC, posições, desvios e peças sob o cartão.

### O conector J101

| | |
|---|---|
| Peça | **UMAX 91302-42-067RCE**: M.2 Key E, 67 contatos (75 posições), passo 0,5, **altura 4,2**, contatos com 15 µin de ouro, SMD em ângulo reto, fita e carretel |
| Código | **LCSC / JLCPCB C48985906**, peça estendida |
| Estoque | **622 peças na LCSC, lido em 25 out 2026** (todas "envio imediato"; preço US$ 1,26 em 1 peça, 1,04 em 10). A página da JLCPCB (`jlcpcb.com/partdetail/C48985906`) não mostra o estoque a um leitor sem navegador: **não consegui ler o estoque da JLC**. O número é o da LCSC, que abastece a montagem da JLC. Conferir no carrinho da JLC antes de pedir |
| Desenho | [UMAX C-91302-42 rev C (dez 2024), 5 folhas](https://datasheet.lcsc.com/datasheet/pdf/fa57621554b717c54a395d0658cff748.pdf?productCode=C48985906) |
| Por que não o LOTES | o **LOTES APCI0108-P001A (C841659) tem estoque 0** na LCSC (mesmo dia), e a altura dele é 4,05 na página |

Medidas conferidas na folha 2 do desenho ("PCB layout"), iguais ao footprint do TE 2199230-4 usado
no M1:

- pads de **0,30 ± 0,03 × 1,55 ± 0,03**, passo 0,5 em cada fileira;
- fileira ímpar (1…75) de **4,5 a 6,05** da linha dos furos; fileira par (2…74) de **1,5 a 3,05**
  do outro lado (total 9,1);
- pino 1 a **9,25** e pino 2 a **9,0** da linha de centro;
- furos sem cobre: **Ø 1,10 ± 0,05** do lado do pino 1 e **Ø 1,60 ± 0,05** (datum X), a **20,0** um
  do outro;
- pinos de fixação de **1,20 × 2,75**, a **±10,35** do centro, centrados a **4,5** da linha dos furos;
- corpo de 21,85 × 8,35 com as pernas, altura máxima **4,20** (folha 1); pinos-guia de Ø 0,90 e
  Ø 1,45 (folha 1).

O desenho mostra o pino 1 à esquerda e a fileira ímpar em cima. O footprint é esse desenho girado
180° (pino 1 em +x, fileira ímpar em +y): uma rotação, não um espelho. O furo de 1,1 continua do lado
do pino 1, como no desenho e no footprint da SparkFun.

### H101 (espaçador)

- Fica o **Würth 9774025151R** (M2.5 × 2,5) por Global Sourcing, como a SPEC v2.3 aceita.
- Procurei um equivalente com estoque na LCSC e não achei de 2,5 mm:
  - **YIYUAN SMTSOM2.520BTR** (C5301776, M2.5, "L2+1,53"): estoque 0;
  - **YIYUAN SMTSOM2.565BTR** (C5301782): 6,5 mm, alto demais;
  - os PEM SMTSO-M25 têm 3 e 6 mm.
- O footprint não mudou: pad de 6,0 com furo metalizado de 3,7. **O furo atravessa a placa** e aparece
  em cima, na área do logo, em (47,5; 14).

### Onde as peças saíram do JSON, e por quê

| Peça | No JSON | Na placa | Por quê |
|---|---|---|---|
| **P1** (J101 + cartão + H101) | centro (37; 17), 22 × 27, conector ao longo de x | **conector ao longo de y**, na borda esquerda do setor P: pátio x 21,1–30,9, y 6,7–29,3, origem em (27,5; 18), rot 90 no verso. Pino 1 atrás (y pequeno), **cartão para +x**: x 30,2–49,5, y 7–29. Espaçador H101 em **(47,5; 14)** | A SPEC deixa a orientação livre. Assim os pads do USB (3 e 5) ficam de frente para o E2, a ~4 mm (o par E1 → E2 → J101 fica com ~15 mm, em vez de ~25 com o conector deitado). Os pads do I2S (50–58) ficam em y ≈ 21–23, a ~14 mm do F1 (24; 35,5). Ocupa o mesmo setor P |
| **E2** (U201) | (14; 13), lado de baixo | **(18,9; 12,2), lado de cima** | O lado vem da SPEC v2.3. Os 4,9 mm para a direita põem o chip dentro do perfil A (SPEC §2: só E1 e F2 ficam fora). Ele fica na linha do par USB que sai do E1 |
| D201 (TVS do VBUS, E2) | — | em cima, (17; 15,5) | vai junto com o E2 |
| R201/R202 (CC do E1) | — | no verso, sob o E2 | deixam o lado de cima livre para o par USB |
| A2 (J501) | (31; 78), o alto-falante | pads dos fios em (46,5; 84), em cima | o alto-falante fica no case; os fios saem perto do A1, como no v2.1 |
| E4 (U204 + L201) | (72; 9) | lado a lado centrados em (72; 9): U204 em 69,5, L201 em 74,2 | dois corpos no mesmo ponto, como no v2.1 |
| T3 (U603–U605) | (150; 10,5) | lado a lado centrados no ponto | idem |
| TP101 | — | fora do cartão, em (29,8; 5,2) | tem de dar para alcançar com o módulo encaixado |

O resto está no ponto do JSON, com centro no pátio. Os passivos ficam no lugar livre mais perto dos
pads do chip que dividem rede com eles (C101 no pad 74, C102 no pad 2 do J101). Todos ficam dentro do
perfil A, fora do anel dos furos M2, e no lado de cima nunca sob uma tecla.

### Classes, vias e regras

| Classe | Redes | Largura | Folga |
|---|---|---|---|
| Default | sinais | 0,2 (mínimo 0,15) | 0,1 |
| USB | USB_DP, USB_DN | 0,24, vão 0,15 | 0,1 |
| Corrente | VBUS, VSYS, VBAT, BB_L1, BB_L2 | 0,8 | 0,2 |

- **Vias 0,5 / furo 0,3 em todas as classes.**
- A classe Nucleo do v2.1 saiu: as redes dela (DCDC do RT1062) não existem mais. As regras usam "não
  é USB nem Corrente".
- **USB: 0,24 / 0,15 em F.Cu sobre o In1.** O empilhamento é o mesmo; a conta continua a do
  `build/impedance.json`: Zdiff 91,2 Ω (solver 2D) e 93,7 Ω (IPC-2141). Não rodei o `impedance.py` de
  novo.
- **`.kicad_dru`**: todos os números com "mm", e nenhuma regra cita a classe "Default". São 7 regras:
  1. vias ≥ 0,5 / furo ≥ 0,3;
  2. sinais (não USB, não Corrente): mínimo 0,15;
  3. USB: 0,22–0,26, vão 0,14–0,20, fora dos pátios de J201, U201 e J101;
  4. USB só em F.Cu fora do pátio do J101;
  5. Corrente: mínimo 0,8 fora dos pátios de J201 (E1), U202 (E3), U204 (E4), J202 (E6), U501 (A1) e
     J101;
  6. Corrente dentro desses pátios: mínimo 0,15 (a afinação na entrada dos pinos);
  7. sob o cartão: uma asserção sobre o campo `Cabe_sob_cartao` de cada peça. O script o escreve a
     partir da altura (campo `Altura_mm`), porque a asserção do KiCad 10 não compara números (testei:
     `getField('Altura_mm') <= 1.9` passa até com 2,0).
- **Prova de que compila:** numa cópia da placa no scratchpad pus uma violação de cada tipo: trilha
  de sinal de 0,12, VSYS de 0,5 fora dos pátios, USB no B.Cu, via de 0,45/0,2 e o L201 (2,0 mm) sob o
  cartão. O `kicad-cli pcb drc` acusou todas, cada uma com o nome da sua regra própria, e não deu
  nenhum erro de leitura do `.kicad_dru`.
- **Área de regra `cartao_MicroMod`**, no B.Cu, sobre o retângulo do cartão. Ela não proíbe nada; serve
  de condição para a regra 7. Na placa de agora há 4 peças sob o cartão, todas de até 1,45 mm.

## Passo M1 (esquema, SPEC v2.2, PR #117)

### O que foi feito

- **Pasta nova** `viaggio_micromod/pcb/`, copiada de `viaggio/pcb/` com o projeto KiCad renomeado
  para `viaggio_micromod`:
  - arquivos, folhas e bibliotecas: `viaggio_micromod.kicad_sym`, `viaggio_micromod.pretty`, sym/fp-lib-table;
  - caminhos e títulos nos scripts;
  - saídas em `build/viaggio_micromod_*`.
- **Vieram:**
  - `schematic.py` (adaptado);
  - `footprints.py` (reescrito);
  - `sexpr.py`;
  - `snap.py` e `impedance.py`, com `build/impedance.json`. O empilhamento é o mesmo; não rodei de novo.
- **Ficaram de fora** (só serviam ao RT1062 na placa):
  - `rt1062_balls.json`, `router.py`, `viaggio_rota_P_parcial.kicad_pcb`;
  - o footprint BGA-196.
- **Ficaram de fora até o passo M2:**
  - `build_board.py` e `handoff_freerouting.py`: o primeiro importa o `router.py` e roteia o setor P;
    os dois serão copiados e ajustados no M2;
  - `ROTEAMENTO.md`;
  - o `fab/` e qualquer `.kicad_pcb`.
- **Folha P** reescrita:
  - J101, o conector M.2 Key E de 4,2 mm;
  - H101, o espaçador SMD M2.5;
  - TP101, o pad de teste do RESET#;
  - C101/C102, 10 µF + 100 nF no 3,3 V junto do conector;
  - R105, os 100 Ω do MCLK, mantido junto do conector.
- **Saíram:** RT1062, MKL02 e o seu LED, W25Q64, PSRAM, os dois cristais, indutor, ferrite e
  capacitores do DCDC do RT1062, diodos do SNVS, e o **E5** inteiro (LDO XC6206P332 + porta U206).
- **Folha E:** o EN do TPS63001 passa a ser o próprio EN_REQ. O USB_HOLD agora depende do **PWR_EN**
  (pad 3.3V_EN) em vez do +3V3 (ver "Liga/desliga" abaixo). Entraram 3 peças: R217 1 kΩ, R218
  100 kΩ e C213 1 µF.
- **Folhas F, I, A, T:** sem mudança de circuito. Muda só o nome da biblioteca do jack e do LED.
- **Resultado** de `python etutti/hardware/viaggio_micromod/pcb/schematic.py`:
  - **ERC: 0 erros, 0 avisos;**
  - **netlist do KiCad = lista do script** (99 redes, 141 peças no esquema, 6 folhas);
  - PWR_FLAG em BB_VINA, GND, SGTL_VDDA e VBUS.
- **`pcb/PINOS.md`** na numeração do Teensy MicroMod. **`pcb/bom_preliminar.csv`** regerado: 64
  linhas, incluindo o módulo e o parafuso, "em casa".

### O conector, pad por pad

A fonte é o **esquema da SparkFun** (`Hardware/MicroMod-Teensy.sch` em
[github.com/sparkfun/MicroMod_Teensy_Processor](https://github.com/sparkfun/MicroMod_Teensy_Processor)).

- Li as ligações rede por rede: pad do J1 → bola do RT1062 → pino do Teensy.
- Confirmei com o [guia do MicroMod Teensy](https://learn.sparkfun.com/tutorials/micromod-teensy-processor-hookup-guide/all).
- As 67 linhas do `MM_PADS` do `schematic.py` foram comparadas por script com o esquema da SparkFun,
  sem diferença.

| Pad | Nome MicroMod | No Teensy MicroMod | No Viaggio |
|---|---|---|---|
| 1, 7, 33, 36, 39, 45, 75 + 2 pinos de fixação | GND | GND | GND |
| 2, 74 | 3.3V | 3,3 V do módulo (antes da chave interna) | +3V3 de E4 |
| 3, 5 | USB_D+ / USB_D− | USB1 | USB-C pelo U201 |
| 4 | 3.3V_EN | **pino 28 (GPIO_EMC_32)** | PWR_EN |
| 6 | RESET# | **ONOFF do RT1062** | clique do volume (D205) + TP101 |
| 9 | USB_VIN | USB1_VBUS (por ferrite e jumper MEAS) | VBUS |
| 11 | BOOT# | PROGRAM do MKL02 (pull-up no módulo) | botão Program I4 |
| 72 | RTC_3V | VDD_SNVS_IN, por diodo | sem ligação |
| demais | ver `pcb/PINOS.md` | pinos 0–45 | 27 sinais, os mesmos números do v2.1 |

### Liga/desliga: o pad 3.3V_EN e o "desligar de verdade com USB"

**O que o pad 4 (3.3V_EN) faz no MicroMod Teensy.** É só o **pino 28** do Teensy (GPIO_EMC_32), um
GPIO comum. Não é o PMIC_ON_REQ.

- Na regra MicroMod ("Designing with MicroMod"), a placa-mãe põe um pull-up nele e o liga ao EN do
  seu regulador. O processador o baixa para cortar o 3,3 V.
- No Teensy ele é solto na partida, no reset e no bootloader.

**O módulo não expõe o PMIC_ON_REQ.** Ele fica dentro do módulo: liga a chave Q2/Q1, que passa o
3,3 V dos pads 2/74 para o "3.3V_CONTROLLED". Esse trilho alimenta o RT1062 (menos o SNVS) e o MKL02.

- O SNVS é alimentado pelo próprio 3,3 V do conector (diodo D2) ou pelo RTC_3V (pad 72).
- **O ONOFF do RT1062 sai no pad 6**, com o nome "RESET#". No esquema da SparkFun a rede chama
  ON/OFF e vai à bola M6.

**Conclusão pela regra P da SPEC:** o 3.3V_EN não é o pedido de desligar do processador. O EN de E4
**não** pode ser "3.3V_EN E EN_REQ". Também não vale usar o 3.3V_EN como EN direto, que é o costume
MicroMod: a gravação reinicia o RT1062, e o regulador cairia no meio dela.

**O que ficou no esquema** (a opção mais segura, que só depende do que confirmei no esquema da
SparkFun):

- **EN de E4 = EN_REQ** = clique do volume OU KEEP (pino 10) OU USB_HOLD.
- **USB_HOLD = VBUS E PWR_EN_S** (U203). PWR_EN_S é o pino 28 com:
  - pull-up de 100 kΩ (R218), o pull-up que a regra MicroMod pede;
  - 1 kΩ em série (R217);
  - 1 µF para o GND (C213).
- Solto (reset, bootloader, firmware que não sabe do pino), o pino 28 fica alto. Com USB, a placa
  continua ligada, e a gravação funciona como no v2.1.
- **Para desligar de verdade com USB, a firmware baixa o pino 28 e o KEEP.** O EN cai quando o
  clique é solto, e o módulo, o codec e os sensores ficam sem energia. Só o carregador continua, e
  a luz de carga aparece (como a SPEC pede).
- O C213 (τ = 100 ms) segura o PWR_EN_S baixo enquanto o 3,3 V cai (≪ 1 ms). A placa não religa
  sozinha quando o pino 28 fica solto ao apagar.
- A SPEC pede o desligar de verdade com USB: **cumprido, sem SNVS e sem LDO sempre ligado**. Saem o
  E5 e o U206. Desligado sem USB, sobra só o BQ24074 (~6 µA, datasheet), menos que no v2.1
  (~25–35 µA).

**Proteção do botão preso: fica.** O módulo expõe o ON/OFF (pad 6), então o D205 leva o clique do
volume ao ONOFF, como no v2.1.

- A firmware grava `BTN_PRESS_TIME` = 10 s no `SNVS_LPCR`. Com o clique preso 10 s, o SNVS desliga
  o RT1062 pela chave interna do módulo.
- Para travamentos sem clique, a firmware usa também o watchdog.
- **Cuidado:** um clique curto no ONOFF com o módulo ligado gera só uma interrupção do SNVS; não é
  reset. O "RESET#" do MicroMod, no Teensy, não reinicia. O TP101 serve para medir, não para
  reiniciar.

### Peças novas

| Código | Peça | LCSC | Montagem | Datasheet |
|---|---|---|---|---|
| P1 (J101) | ~~LOTES APCI0108-P001A~~ (no M2: **UMAX 91302-42-067RCE**, C48985906, ver acima) | C841659 (estendida) | JLC | [LCSC C841659](https://www.lcsc.com/datasheet/C841659.pdf); referência do footprint: [TE 2199230-4 rev B3](https://cdn.sparkfun.com/assets/9/c/e/b/6/MicroMod_M.2_Connector_Datasheet_TE_2199230-4.pdf) |
| P1 (H101) | **Würth 9774025151R**, espaçador SMD M2.5, 2,5 mm (o da SparkFun) | sem código confirmado | JLC Global Sourcing (conferir) | [Würth WA-SMSI 9774025151R](https://cdn.sparkfun.com/assets/f/d/2/b/e/MicroMod_Reflowable_Standoff.pdf) |
| P1 (MOD1) | SparkFun MicroMod Teensy (DEV-16402) | — | em casa | [produto](https://www.sparkfun.com/sparkfun-micromod-teensy-processor.html), [esquema/Eagle](https://github.com/sparkfun/MicroMod_Teensy_Processor), [guia](https://learn.sparkfun.com/tutorials/micromod-teensy-processor-hookup-guide/all) |
| P1 (SCR1) | parafuso M2.5 × 3, cabeça chata | — | em casa | vem no [KIT-16549](https://www.sparkfun.com/sparkfun-micromod-diy-carrier-kit-5-pack.html) |
| P1 (TP101) | pad de teste Ø1,5 | — | sem peça | — |
| E3 | R217 1 kΩ, R218 100 kΩ, C213 1 µF (0402) | C11702, C25741, C52923 (básicas) | JLC | — |

Os demais (E1–E4, E6, F, I, A, T) seguem os do Viaggio v2.1, com os mesmos códigos LCSC
(`bom_preliminar.csv`).

#### Footprints (`pcb/footprints.py` → `kicad/viaggio_micromod.pretty/`)

- **`M.2_Socket_E_H4.2_MicroMod`** (no M2: `M.2_E_H4.2_UMAX_91302-42-067`, mesmas medidas), tirado do desenho TE 2199230 rev B3, folha 3 ("recommended PCB
  outline"). Confere pad a pad com o footprint "M.2-CONNECTOR-E" da biblioteca SparkFun, usado nos
  carriers Data Logging e ATP.
  - 34 pads ímpares e 33 pares de 0,3 × 1,55, passo de 0,5 em cada fileira, com o pino n em
    x = 9,25 − 0,25 (n − 1);
  - fileira ímpar a 4,5–6,05 da linha dos furos, fileira par a 1,5–3,05;
  - dois pinos de fixação de 1,2 × 2,75 em (±10,35; 4,5);
  - furos sem cobre de Ø1,1 (lado do pino 1) e Ø1,6 em (±10; 0).
  - No F.Fab: o cartão de 22 × 22 e o lugar do espaçador em **(+4,0; −20,0)** do conector, onde a
    SparkFun o põe nos dois carriers (4,06/19,94 e 4,01/19,99).
- **`Standoff_SMD_M2.5_H2.5`**: pad de Ø6,0 e furo de 3,7, como no desenho da Würth. Fiz o pad
  metalizado, como a SparkFun (6,0/3,9), para o DRC não ver furo sem cobre dentro de pad. Rede GND.

### Consumo e autonomia

Não mudou o orçamento do v2.1, salvo:

- o módulo (RT1062 a 600 MHz, ~100 mA ativo, conferir) no lugar do RT1062 na placa;
- desligado: ~6 µA (só o BQ24074), em vez de ~25–35 µA, porque saiu o SNVS sempre alimentado.

O `POWER.md` fica para o M3, com a placa, como a SPEC §7 manda.

### O que a programação precisa ajustar

- **fqbn `teensy:avr:teensyMM`** em vez de `teensy:avr:teensy41`. O PC do J tem o Teensyduino 1.62,
  que já lista "Teensy MicroMod".
- **Pinos:** os mesmos 0–26 do v2.1. Nada muda nos `#define` de teclas, encoders, LED, I2S e I2C.
- **Novo, pino 28 (PWR_EN):**
  - na partida, deixar como entrada (sem pull-down);
  - para desligar com USB, `OUTPUT` + `LOW` e mais o KEEP baixo;
  - com USB, um clique curto já deixa a placa ligada: se o clique for solto antes de 2 s, desligar
    assim.
- **Sai o desligamento do SNVS** (`SNVS_LPCR` TOP/DP_EN) para desligar com USB.
- **Fica o `BTN_PRESS_TIME` = 10 s** no `SNVS_LPCR`. Somar o watchdog.
- **Pino 13** também acende o LED azul do módulo (~1,3 mA). O LED de erro do bootloader agora é o
  amarelo do módulo.
- Detalhes em `pcb/PINOS.md`.

## Consumo e autonomia

Sem mudança desde o M1: o módulo consome ~100 mA a 600 MHz (conferir), e desligado sem USB fica só o
BQ24074 (~6 µA). O `POWER.md` fica para o M3, como a SPEC §7 manda.

## O que a programação precisa ajustar

Nada novo no M2: o `PINOS.md` não mudou. Continua valendo o que o M1 pediu: fqbn
`teensy:avr:teensyMM`, pinos 0–26 do v2.1 e pino 28 = PWR_EN.

## Itens (conferir)

1. **Estoque do J101 na JLCPCB:**
   - lido só o da LCSC: 622 peças em 25 out 2026;
   - a página da JLC não mostra o estoque sem navegador;
   - conferir no carrinho da JLC antes de pedir.
2. **Altura do cartão no UMAX:**
   - a folha 1 do desenho UMAX mostra **2,85 ref.** no esquema de encaixe;
   - o TE 2199230-4 dá 2,48 ref. para o cartão, e a SparkFun usa o espaçador de 2,5 mm;
   - se a altura do contato no UMAX for mesmo 2,85, o cartão fica ~0,35 mm inclinado sobre 20 mm. Isso
     pede um espaçador de ~3 mm, ou o cartão sente a flexão;
   - conferir com a peça na mão, ou com uma pergunta à UMAX.
3. **Posição do espaçador:** (+4,0; −20,0) do conector, que na placa dá (47,5; 14).
   - A especificação MicroMod põe o parafuso 4 mm à direita da linha de centro do cartão, o que
     confirma o +4.
   - O −20 vem de dois carriers da SparkFun.
   - Conferir com o módulo na mão.
4. **Espaçador H101:**
   - o Würth fica por Global Sourcing; não há equivalente LCSC de 2,5 mm com estoque;
   - o furo de 3,7 atravessa a placa: no lado de cima, fica na área do logo;
   - conferir o desenho Würth: furo metalizado ou sem cobre.
5. **Alturas da tabela `HEIGHT_MM`** do `build_board.py` (máximos de datasheet ou modelo 3D): 0805
   1,45; SOT-23 1,45; QFN 1,0; TSSOP 1,2; X2SON 0,4; FNR4020 2,0; TS-1187A 1,5; JST PH SMD 6,0. Sob
   o cartão só estão 0805 e 0402.
6. **Altura do conjunto sob a placa** (espaçador + cartão + peças do módulo): medir o módulo, a SPEC
   estima 6–7 mm.
7. **Pino 28 em reset** e **consumo do módulo**: como no M1, conferir no protótipo.

## Perguntas para a gestão

1. **P1 de pé (conector ao longo de y, cartão para +x):** a SPEC deixa a orientação livre, e assim o
   USB e o I2S ficam mais curtos. O retângulo do P1 fica x 21–49,5, y 6,7–29,3, dentro do setor P.
   Aceitam? O design precisa saber disso para o furo do fundo do case.
2. **E2 4,9 mm à direita do JSON** (18,9 em vez de 14), para ficar dentro do perfil A. Aceitam, ou o
   perfil A deve passar a incluir o E2, como já inclui E1 e F2?
3. **Espaçador:** se o UMAX confirmar o cartão a 2,85 mm (item 2 acima), trocamos para um espaçador de
   3 mm (por exemplo o PEM SMTSO-M25-3ET, por Global Sourcing)? Ou compramos um conector UMAX junto com o
   módulo (pergunta 1 da SPEC §8) e medimos antes do M3?
4. **Estoque do J101:** 622 na LCSC hoje. Reservamos já (US$ 1,26 cada) ou esperamos o fim do
   roteamento?
