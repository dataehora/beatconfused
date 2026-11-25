# eTutti Slim · Roteamento

Atende à **SPEC R8SL §8.1 (Etapa 3a)**: régua R8 (2 camadas, 1,2 mm, 8 TMAG5253 + 74HC595 + FFC de 8 vias) roteada e grade conferida. Agente `roteamento`: **nenhuma peça foi movida** (`pcb/regua/rota/confere_pecas.py`: 30 peças iguais às da placa posicionada). A placa principal **não** foi roteada (fora desta revisão). Nada cotado ou comprado.

## 1. Resultado (portão C-régua)

**Aceito pelo DRC.** `kicad-cli pcb drc --schematic-parity --refill-zones --all-track-errors --severity-all`, sobre `pcb/regua/rota/kicad/slim_regua_rota.kicad_pcb`:

| Critério | Pedido | Obtido |
|---|---|---|
| Erros DRC | 0 | **0** |
| Avisos DRC | 0 | **0** |
| Ligações faltando | 0 | **0** (sinais e GND) |
| Paridade com o esquema | 0 | **0** |
| Trilha abaixo do mínimo | nenhuma | menor trilha **0,15 mm** (regra: mínimo 0,15; JLCPCB padrão 0,127) |
| Pontas soltas | 0 | **0** (DRC + checagem própria, `rota/verifica.py`, que também aceita T de trilha em trilha) |
| Ilhas de plano | 0 | **0** (cada peça de cobre dos dois planos GND tem pad ou via GND) |
| Afastamento OUT × DATA/CLK/LATCH | ≥ 1,0 mm | **2,07 mm** (mínimo medido fora da zona do FFC) |

Números da placa: **97 vias** (0,5/0,3 na parte regular, 0,6/0,3 no resto), das quais **24 de sinal** (8 de +3V3 na cabeça, 16 de EN: duas por EN) e **73 de GND** (costura + um por pad onde o plano de baixo não chega + as dos sensores); trilhas de sinal **1042,7 mm** no total (+3V3 178,0; OUT 157,2; EN1..EN8 de 19,7 a 152,3; DATA 13,6; LATCH 9,0; CLK 6,3); 223 segmentos.

Estrutura do cobre (imagens abaixo):

- **Verso (B.Cu, lado das peças):** barramento **+3V3 em y = 33,11** (acima dos sensores, entre os keep-outs dos furos das teclas e a fileira de pads), barramento **OUT em y = 35,30** (abaixo), derivações curtas até os pads, DATA/CLK/LATCH na cabeça. Plano de GND também no verso, nas áreas livres.
- **Frente (F.Cu, lado das teclas):** o **plano de GND** (decisão da SPEC; costurado com 73 vias) e as **8 pistas EN** (0,15 mm, passo 0,30, faixa y 35,05..37,15, nada de peça em cima). A pista de EN_j sobe um degrau de 0,30 depois de cada sensor (curva de 45°, escalonada por pista para as curvas não correrem lado a lado).
- **Cabeça (J1, U9, C9, C10):** EN3..EN8 saem da fileira de baixo do U9 em **escada de vias** (0,5 × 0,65 mm), EN2 pelo pino da direita, EN1 pela fileira de cima. DATA/CLK/LATCH/OUT/+3V3 da cabeça foram roteadas pelo roteador próprio com a parte regular já desenhada.

Imagens (geradas por `rota/imagens.py`, **com o nome da nota em cada tecla**: uma régua R8 serve as 4 fileiras, então cada posição mostra as 4 notas, "fileira n  nota", das tabelas `NOTES` de `case/layout_slim.py`):

- `pcb/regua/img/regua_frente.png` (lado das teclas: plano, furos, pistas EN, posições 1..8 com as notas);
- `pcb/regua/img/regua_verso.png` (lado das peças, vista de baixo, placa virada: J1 e a posição 1 à direita);
- `pcb/regua/img/regua_cabeca_verso.png` (zoom da cabeça, sem espelhar);
- `pcb/regua/img/grade.png` (a grade).

## 2. Regras usadas (`pcb/regua/rota/prepara.py` → `.kicad_dru`)

- 2 camadas, 1,2 mm; trilha preferida **0,2** (mínimo 0,15: só as 8 pistas EN, que são níveis lógicos estáticos); folga de roteamento 0,15 (DRC 0,1 = o vão que a própria pegada do TMAG5253 já tem entre pads); via **0,5/0,3** (a parte regular) e **0,6/0,3**; tudo dentro do padrão sem custo extra da JLCPCB (≥ 0,127/0,127; furo 0,3). Folga cobre-furo 0,25 e cobre-borda 0,25 como na placa posicionada.
- **OUT longe de DATA/CLK/LATCH:** regra do `.kicad_dru` com **afastamento mínimo 1,0 mm** (borda a borda, em qualquer item da rede, pad ou trilha). Justificativa: OUT é a linha analógica dos 8 sensores (variação de mV na leitura); DATA/CLK/LATCH são bordas de 3,3 V de ns; o acoplamento cai com a distância, e 1,0 mm = 5 larguras de trilha, 6,7 vezes a folga padrão. **Exceção só dentro da área de regra "Zona FFC"** (x até 25,6 mm, 1,75 mm além dos pads do conector): ali OUT é o pino 3 ao lado do DATA, pino 4, com passo de 0,5 mm e vão de pad de 0,2 mm; o passo já impõe 0,2. O DRC confere as duas regras (mínimo medido fora da zona: 2,07 mm).
- **GND:** plano de cobre na **F.Cu** (lado das teclas) sobre todo o contorno; mais um plano de GND na B.Cu nas áreas livres (pour de apoio, ligação plena nos pads), costurado ao de cima por vias (passo 8 mm, mais as dos pads). Remoção de ilhas ligada; as duas peças menores do plano de baixo que ficariam presas (pads 7 e 8 do J1) têm via própria.
- Keep-outs de furo: uma área de regra por furo NPTH (raio do furo + 0,25 + 0,13: trilha e via proibidas, plano permitido) e a "Zona FFC", acrescentadas à placa pelo `prepara.py` (a placa posicionada em `pcb/kicad_regua/` não foi alterada). O `.kicad_dru` novo substitui o antigo, que tinha uma regra de footprint que o KiCad recusa ("A.Type == 'Footprint'").

## 3. Método escolhido e comparação

**Escolha (uma linha):** parte regular (barramentos, derivações dos sensores, as 8 pistas EN, a escada de vias da cabeça) **desenhada por script** (`fixa.py`), e só a cabeça (DATA, CLK, LATCH, OUT, +3V3 de J1/C9/C10/U9) pelo **roteador próprio de grade** (`rota_grade.py`, da família do `build_pcb.py` da V1, reescrito sobre máscaras numpy a 0,1 mm); GND por script (`gnd.py`). Foi o único método que **fecha** e é **repetível**; os dois roteadores automáticos sozinhos não fecharam.

KiCadRoutingTools: **encontrado** em `C:/Users/julia/OneDrive/Documentos/GitHub/KiCadRoutingTools` (versão 0.24.2, CLI `py_router/route.py`, núcleo Rust já compilado, roda no Python do sistema). Roteador próprio do repositório: o `viaggio_j1/rota_restante.py` está amarrado à placa de 4 camadas do MicroMod (In1/In2, `build_board.py` da V2) e o `Router` do `build_pcb.py` da V1 depende das globais da eTuttino; por isso reescrevi a ideia (A* de grade, cada rede só se junta à própria árvore, custo de via e de curva, retentativas com a rede que falhou na frente) em `rota_grade.py`, para a grade de 0,1 mm que os pads de 0,5 mm pedem. Todos os testes usaram a **mesma placa-base** (`prepara.py`), as **mesmas regras** (0,2/0,15, via 0,6/0,3, folga cobre-furo e borda) e `--escalation off` no KiCadRoutingTools.

| Método | Tempo | Vias (sinal) | Comprimento de sinal | Avisos DRC | Ligações de sinal abertas | Repete? |
|---|---|---|---|---|---|---|
| KiCadRoutingTools, padrão (`--escalation fab`) | 18 s | 36 | não medido | não medido | 1 rede falhou (LATCH) | não rodei de novo: **baixou sozinho** trilha para 0,127, via para 0,25, 7 vias em pad: **fora das regras** |
| KiCadRoutingTools estrito, 1 chamada com todas as redes | 13 s | 25 | 875 mm | 0 de placa | 2 redes falharam (LATCH, OUT) | sim |
| KiCadRoutingTools estrito, 6 ordens de grupos (A..F) | 40..57 s cada | 16..28 | 893..1073 mm | 0..2 | **4 a 9** abertas por ordem | sim |
| KiCadRoutingTools com barramentos desenhados por mim (`--keep-input-copper`), 3 ordens | ≈ 1 min cada | 15..30 | 1007..1110 mm | 0..1 | 2 a 3 (CLK/DATA/OUT) e, em outra ordem, 51 erros (trilhas se cruzando) | sim |
| Roteador próprio, as 13 redes sozinho (32 ordens aleatórias + retentativas, 5 em paralelo) | 12 a 380 s por ordem (mediana 94 s) | n/a | n/a | n/a | **0 de 32 fecharam** (falha quase sempre nas pistas EN 4..8 e no OUT) | sim |
| **Híbrido: `fixa.py` + roteador próprio na cabeça + `gnd.py`** | **0,4 + 3,8 + 0,8 s** (a cadeia toda com DRC, grade e imagens: **18 s**) | **24** | **1042,7 mm** | **0** | **0** | **sim** (2 execuções do zero: vias e trilhas idênticas; só a quebra de linha do polígono do plano mudou) |

Repetibilidade do KiCadRoutingTools medida: duas execuções iguais deram **arquivos idênticos** (sem uuid), 764 trilhas e 48 vias cada. Observações do KiCadRoutingTools: (a) deixa **vazios de 0,05..1 mm** entre a trilha e o pad que o DRC do KiCad acusa (3 a 9 ligações de sinal abertas) mesmo "completando" a rede; (b) ao rotear uma rede multi-pad (OUT, 9 pads; +3V3, 21 pads) depois de outra, **desfaz** trilhas já prontas de outras redes ("recovered"); (c) com a trilha na camada de cima e GND em plano, o passo de plano **apagou** o +3V3; (d) as regras de folga de furo NPTH (0,25) saíram 0,20..0,23 (corrigido com keep-outs). Ele é a melhor opção quando o espaço sobra; aqui o canal sob os sensores tem **2,4 mm** para 8 pistas EN + OUT.

Por que o híbrido: as 8 pistas EN pedem 8 × 0,3 mm de altura sob os sensores, e um roteador guloso, rede por rede, ocupa essa altura na ordem errada. Com a ordem das pistas fixada à mão (a mais perto do sensor fica por cima, subindo um degrau a cada sensor), o problema que sobra é só a cabeça, que o roteador próprio resolve em **3 s**.

## 4. Etapas retomáveis (`pcb/regua/rota/`)

`etapas.py` roda as etapas em ordem; cada uma é idempotente (hash das entradas em `estado.json`; sem mudança e com saída existente, pula). Uma sessão nova lê `estado.json` e continua. Nenhuma passa de 5 s, então nenhuma precisa de segundo plano (o roteador próprio sozinho em 13 redes levava minutos: esse caminho foi abandonado).

| Etapa | Script | Saída | Tempo |
|---|---|---|---|
| base | `prepara.py` | `kicad/base/` (placa posicionada + `.kicad_dru` + "Zona FFC" + keep-outs de furo + plano F.Cu) | 0,4 s |
| fixa | `fixa.py` | `kicad/fixo.kicad_pcb` (parte regular) | 0,4 s |
| sinais | `rota_grade.py` | `kicad/sinais.kicad_pcb` (cabeça) | 3,8 s |
| gnd | `gnd.py` | **`kicad/slim_regua_rota.kicad_pcb`** (final, com `.kicad_pro/.dru/.sch`) | 0,8 s |
| verifica | `verifica.py` | `build/verifica.json` (também em `estado.json`) | 4 s |
| grade | `grade.py` | `build/grade.json`, `kicad/grade/fab/` (Gerbers + furação) | 4 s |
| imagens | `imagens.py` | `pcb/regua/img/regua_*.png`, `grade.png` | 4 s |

Auxiliares: `metricas.py` (DRC + vias + comprimento), `confere_pecas.py` (nenhuma peça mudou), `ver.py` (recorte da placa), `krt_run.sh`/`krt_seq.sh`/`krt1.sh` (as chamadas do KiCadRoutingTools da comparação), `.gitignore` (ignora `build/` e os intermediários, que a cadeia refaz). Lições do repositório aplicadas: nenhum item solto removido antes de rotear; `SaveBoard` só depois de limpar (o `gnd.py` testa a folga de cada via e trilha contra o cobre de outras redes antes de pôr); objetos Python mantidos vivos após `board.Remove`; o roteador lê o contorno externo (os furos e os keep-outs entram como obstáculos próprios).

Para o integrador: nenhum commit foi feito (ramo e commits são dele). Os arquivos novos estão em `pcb/regua/rota/` e `pcb/regua/img/`, mais este relatório; **a placa roteada** é `pcb/regua/rota/kicad/slim_regua_rota.kicad_pcb`.

## 5. Grade (`rota/grade.py`, `pcb/kicad_regua/slim_grade.kicad_pcb`)

Conferida, não alterada. DRC da grade (`kicad-cli`): **0 erros, 0 avisos, 0 ligações**.

- Contorno **148,0 × 16,0 mm**; **8 furos quadrados de 14,00 mm** (lados retos medidos: 14,000 × 14,000), passo **18,5 mm**; **dog-bone** nos 4 cantos de cada furo (alívio circular que passa 0,35 mm do lado reto), ver `grade.png`.
- **2 furos M2 de 2,2 mm** (NPTH, em u = 49 e 123) com a nota "ESCAREAR M2 D4,4 x 90 gr (lado das teclas)" na camada de comentários; a furação do Gerber só tem os 2 furos de 2,2 (o escareado é a nota).
- **Sem cobre algum**: nenhuma trilha, zona ou pad de cobre; Gerbers de F.Cu/B.Cu vazios (474 bytes, só o cabeçalho). Logo, nenhum cobre perto dos furos.
- Gerbers e furação em `pcb/regua/rota/kicad/grade/fab/` (contorno, comentários, máscara, cobre vazio, `.drl`). Não foi encomendada nem cotada.
- **Problema achado (pedido abaixo):** o escareado D4,4 dos M2 deixa **0,05 mm** de FR-4 até o furo quadrado de 14,00 (os furos vizinhos terminam em x = 66,75 e 71,25 mm; o escareado vai de 66,8 a 71,2) e consome 1,1 dos 1,2 mm de espessura: o vão de 4,5 mm entre as teclas 2-3 e 6-7 não comporta um cone de 4,4 mm.

## 6. Pedidos à eletrônica

Nenhuma mudança de **posição de peça** é necessária para a régua: ela fecha na posição atual. Pedidos que não são de posição:

1. **Grade, escareado dos M2 (acima):** reduzir o escareado (parafuso M2 de cabeça chata DIN 965 tem cabeça de ~3,8 mm; D3,8 deixa ~0,35 mm de parede no topo) ou mudar o M2 de lugar (não existe vão maior no passo de 18,5) ou trocar por cabeça cilíndrica sem escareado e rebaixo no degrau. Decisão da eletrônica com o design.
2. **Pistas EN em 0,15 mm** (padrão JLCPCB, vão 0,15): foi a forma de caberem 8 pistas em 2,4 mm de altura sob os sensores. Se a eletrônica quiser 0,2 em tudo, só há como pedir mais altura de placa na frente (cerca de +0,8 mm na borda da frente da régua, o que muda o envelope do case). Hoje não é necessário.
3. **J1 (FFC):** as trilhas da cabeça passam por baixo do corpo do conector (pátio J1: x 20,05..24,05) na B.Cu, cobertas por máscara; conferir com o desenho do conector que o corpo não encosta no cobre (pedido de confirmação, não de mudança).

## 7. Problemas e limites

- O roteador automático por si só (nem o KiCadRoutingTools, nem o próprio) fechou a régua: a solução é semimanual (`fixa.py`), específica da régua R8; a **placa principal** (120 peças, 379 ligações) precisará de outro método (o KiCadRoutingTools em grupos é a primeira aposta, os críticos à mão como na régua).
- O `.kicad_dru` novo só vale para a régua roteada; a placa posicionada (`pcb/kicad_regua/`) mantém o antigo.
- A folga de 0,1 mm entre os pads do TMAG5253 é da pegada; o DRC da classe padrão foi mantido em 0,1 por isso (o roteamento usa 0,15).
- Estimativas de custo, tempo de entrega e compras: fora do escopo desta etapa.

## Perguntas para o design

1. A régua e a grade têm 1,2 mm; o escareado D4,4 dos M2 de fixação não cabe no vão de 4,5 mm entre as teclas (parede 0,05 mm). Que cabeça de parafuso e que escareado o case aceita (D3,8?), ou o M2 pode ir para fora da grade?
2. O corpo do conector FFC (KH-H1.0) cobre as trilhas da cabeça (x 20..24 mm, verso); o case tem folga para o conector e o cabo na altura da degrau 1 (z = 3,8 mm sob a régua)?
3. A pista EN mais baixa (F.Cu, y = 37,15, 0,15 mm de largura) chega a 0,28 mm da borda da frente da régua (y = 37,5; mínimo da JLCPCB e do DRC 0,25): alguma parte do case ou da grade encosta nessa borda, onde máscara riscada exporia o cobre?
