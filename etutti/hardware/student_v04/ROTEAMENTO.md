# ROTEAMENTO · Student V4 (agente `roteamento`)

**SPEC atendida: R11V4 (item 4: portão P das réguas liberado; a placa principal continua fechada e NÃO foi roteada).**
Data: 22 nov 2026. Entrega recebida: `pcb/regua/ROTEAMENTO_ENTREGA.md`. Nenhuma peça, furo, contorno, área de proibição ou texto foi movido; as placas entregues (`student_v04_regua.kicad_pcb`, `student_v04_regua8.kicad_pcb`) ficaram intactas: o trabalho está em **cópias** `*_roteada.*` (com `.kicad_pro`, `.kicad_dru` e `.kicad_sch` copiados com o mesmo nome, para o DRC com paridade funcionar).

## Resultado (R11V4, R8 refeita)

| Placa | Arquivo | DRC (`--severity-all --schematic-parity`) | Situação |
|---|---|---|---|
| **R4** (4 posições) | `kicad/regua/student_v04_regua_roteada.kicad_pcb` | **0 erros, 0 avisos, 0 ligações faltando, paridade 0** | **ACEITA** |
| **R8** (8 posições; vale também para a R8E) | `kicad/regua/student_v04_regua8_roteada.kicad_pcb` | **0 erros, 0 avisos, 0 ligações faltando, paridade 0** | **ACEITA** (refeita do zero sobre o posicionamento novo: 595 em u 74, C1..C8 na linha central, C9 em u 78,2) |

Ambas em **2 camadas, 1,2 mm** (a entrega vinha com a pilha de 4 camadas do V3), planos de GND no topo e no fundo costurados, sem ilhas, sem pontas soltas, nenhuma trilha < 0,15 mm, áreas de 4,6 mm sob as cabeças dos M2 respeitadas, OUT a 0,3 mm de CLK/SER/QHP. **+3V3: R4 48 de 73 trechos a 0,3 mm, R8 63 de 96**; o resto a 0,2 mm (saídas de pads de 0,25 mm): desvio da entrega, ver pergunta 3.

R8: o pedido de mover o 595 e os capacitores resolveu os bolsões de GND. Resultado da 5a execução da última série (4 a 17 itens de DRC nas outras; o Freerouting não é determinístico). Comando: `cd pcb/regua/rota; GMAX=600000 python melhor.py 8 6`. Tentativas com pré-rotear SER ou escapes no 595 pioraram.

Imagens (olhadas): `pcb/regua/img/regua_R{4,8}_roteada_{topo,fundo}.png`, vistas de cima, sem espelhar.

## Método e justificativa

1. **Roteador de grade próprio** (`pcb/regua/rota/lib_rota.py`, A* a 0,05 mm, 2 camadas, vias 0,5/0,3, folgas e áreas de proibição lidas da placa): bom para o que é apertado e local. O `rota_restante.py` do repo é amarrado à J1 (listas de peças, camadas In1/In2) e não serve para uma régua de 14 mm.
2. **Freerouting 2.5.0 em linha de comando** (já instalado em `%LOCALAPPDATA%\freerouting`): DSN exportado pelo pcbnew, planos de GND como `plane`, SES importado. Foi o que fechou o conjunto (o A* puro, mesmo com rip-up, ficava trocando de rede aberta).
3. **Misto, nesta ordem** (`roda_regua.sh N` = `fr_run.py` + `post.py`):
   - GND local à mão: pads 2 e 5 do TMAG5253 e os do 595 ligados entre si (`gnd.py`);
   - **escapes** (pad, trilha curta, via) de OUT e de todos os pads de GND, pelo A* próprio: fixam por onde os pinos de 0,5 mm saem e evitam pads de GND isolados; OUT sai à mão porque a folga de 0,3 mm de CLK/SER/QHP não existe no Freerouting;
   - Freerouting liga o resto (largura 0,2 na R4; 0,15 na R8, a 0,2 faltavam 2 a 5 ligações);
   - pós (`post.py`): corrige trilhas < 0,15 mm que o Freerouting faz nos pescoços, costura de GND (`costura.py`: reenche os planos, acha fragmentos fora do conjunto principal e põe via ou trilha curta), remove vias e pontas soltas apontadas pelo próprio DRC (`limpa_drc`), alarga +3V3 para 0,3 mm onde o DRC deixa e volta onde não deixa.
4. O Freerouting não é determinístico entre execuções (e a R8 muda muito); `melhor.py N k` roda o pipeline k vezes e guarda a melhor placa. A R8 foi a melhor de 8 execuções (itens de DRC: 8, 9, 5, 5, 17, 8, 6, 5).
5. Retomável: `pcb/regua/rota/estado.json` (por placa: status, método, DRC final, comando). Cada etapa é idempotente (refaz a cópia `*_roteada` a partir da placa entregue). Sem commit (o integrador faz). `python vista_rota.py placa prefixo x0 x1 escala` desenha as imagens.

Tempo: R4 cerca de 2 min por execução (Freerouting 25 s); R8 de 3 a 13 min por execução (costura é o trecho lento). Total desta sessão com tentativas: algumas horas, a maior parte em tentativas de A* puro que não convergiram.

## Para a eletrônica gerar Gerbers, BOM, CPL e painéis 

- **R4 (pronta para isso):** `REGUA_BOARD=<raiz>/etutti/hardware/student_v04/kicad/regua/student_v04_regua_roteada.kicad_pcb REGUA_N=4 PAINEL_N=5`, com `pacotes_regua.py` e `fab_regua.py` (`MODO=regua`) conforme a entrega, §6. Arquivos finais da R4: `kicad/regua/student_v04_regua_roteada.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, `.kicad_sch`). Atenção: os scripts de painel copiam trilhas, vias e **zonas**; os planos de GND estão preenchidos (a placa foi salva reenchida) e o painel precisa de nova verificação de DRC.
- **R8:** `kicad/regua/student_v04_regua8_roteada.kicad_pcb` (aceita): `REGUA_N=8 PAINEL_N=2` (ou 4).
- A cópia está em **2 camadas**: confira que `fab_regua.py` não exporta In1/In2 e que o empilhamento 1,2 mm de 2 camadas é o que a cotação espera.
- Não rodei `pacotes_regua.py` nem `fab_regua.py` (BOM, CPL, painéis e cotação são da próxima fase da eletrônica). Não alterei `.kicad_dru` das placas entregues; as cópias têm o mesmo `.kicad_dru`.

## Lições novas (para o próximo roteador)

- O **Freerouting 2.5 roteia as réguas muito melhor que o A* guloso**, mas desconhece a regra OUT a 0,3 mm e faz pescoços de 0,10 a 0,12 mm; corrigir depois. A largura de classe 0,15 abre caminho onde 0,2 deixa 2 a 5 ligações abertas.
- Plano de GND em 2 camadas com ilhas removidas só "existe" onde há via ou pad âncora; sem vias de costura o plano do topo some. Fragmentos do plano contam como ligações abertas no DRC (itens "Zone ... GND").
- Pad de GND do TMAG5253 (pino 2 + almofada central) fica isolado se o Freerouting o cerca; o escape pré-roteado resolve.
- Alargar +3V3 depois de costurar o GND pode isolar pad de GND vizinho; `post.py` volta a largura nesse caso.
- Conectividade "por células" do meu A* não vale para trilhas do Freerouting (pontas fora da grade): para fechar o que sobra usar o par de itens do DRC (`fecha_par.py`).
- `pcbnew.LoadBoard` de placa com pilha de 4 camadas: `SetCopperLayerCount(2)` basta; o `BuildDefaultStackupList` não está exposto no Python.

## Perguntas para o design

1. +3V3 a 0,2 mm em parte dos trechos (R4 25 de 73, R8 33 de 96; resto a 0,3 mm) é aceitável? A corrente é de alguns mA, mas a entrega pedia 0,3 mm ou mais.
2. As réguas ficaram em **2 camadas**: confirma que a cotação e o empilhamento esperam 2 camadas?
3. O 595 da R8 em u 74, v 0 (rot 90) fica entre os pinos de tecla do vão central: o design confirma que o trilho/rebaixo do case aceita?
