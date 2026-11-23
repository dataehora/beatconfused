# Entrega ao agente `roteamento` · réguas da Student V4 (R11V4)

De: eletrônica. Para: roteamento. **Portão P das réguas: liberado pela SPEC R11V4 (item 4).** A placa principal **continua com o portão fechado: não a roteie.**
Você roteia **duas placas** (R8 e R4); as quatro variantes (R8, R8E, R4, R4E) saem delas (a variante "E" só monta o conector OUT: BOM/CPL, não Gerber).

## 1. O que você recebe (posicionamento CONGELADO)
| Placa | Arquivo | Esquema / netlist | Posições (u, v) | DRC sem trilhas |
|---|---|---|---|---|
| **R8** (8 posições, 147,6 x 14 x 1,2 mm) | `kicad/regua/student_v04_regua8.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | `kicad/regua/student_v04_regua8.kicad_sch`; `pcb/regua/build8/regua_netlist.net` | `pcb/regua/posicao_regua8.json` | 0 erros, 0 avisos, **80 ligações faltando**, paridade 0 |
| **R4** (4 posições, 73,6 x 14 x 1,2 mm) | `kicad/regua/student_v04_regua.kicad_pcb` | `kicad/regua/student_v04_regua.kicad_sch`; `pcb/regua/build/regua_netlist.net` | `pcb/regua/posicao_regua.json` | 0 erros, 0 avisos, **52 ligações faltando**, paridade 0 |

Zero trilha, zero via nos dois. **Não rode `posiciona_regua.py` sobre uma placa roteada** (ele recria a placa do zero): trabalhe numa **cópia** (sugestão: `kicad/regua/student_v04_regua8_roteada.kicad_pcb`, `..._regua_roteada.kicad_pcb`) e passe o caminho aos scripts de painel por `REGUA_BOARD` (item 6).

Quadro: u ao longo da fileira (0 = ponta da esquerda nominal; a placa vai de 0,2 a 147,4 na R8), v para o jogador (+v = frente, 0 = linha central). Placa x = 10 + u, y = 17 + v (KiCad, y para baixo).

## 2. O que NÃO pode mover (peças, furos, contorno)
Nenhuma peça muda de lugar, giro ou lado. Nenhum furo, entalhe, contorno, área de proibição nem texto de serigrafia. Se uma ligação não fecha sem mover algo, **pare e peça à eletrônica** (relatório) com a rede e o ponto: a eletrônica move e republica o posicionamento.
- **Todas as peças estão no FUNDO (B.Cu)**: TMAG5253 (U1..U8 na R8, U1..U4 na R4), 74HC595 (U9 na R8; U5 na R4), J1 (IN), J2 (OUT), R1 (330 ohm do QH'), C1..C8 (100 nF, um por sensor), C9 (100 nF do 595), C10 (10 uF). **R8: cada C_k fica na linha central, à direita do sensor (u + 1,75, v 0, pad +3V3 ao fundo-trás, GND à frente), entre os pinos 1 e 2 do TMAG.** **No topo (F.Cu) não há peça**: é onde a tecla se apoia. O DRC proíbe peça no topo.
- **Sensores nos centros das células:** u = 9,25 + 18,5 k (k = 0..7), v = 0. **595 (R8, R11V4 reposicionado): u 74,0, v 0, rot 90 (R4: u 27,75, v +4,2, inalterado).** **J1:** u 5,9, v −3,95, boca para −v (borda de trás). **J2:** u 121,5 (R8) / 47,5 (R4), v −3,95. **R1** ao lado do J2.
- **Furos furados (NPTH):** 2 pinos de tecla D1,70 por célula, em u_célula ± 5,08, v = 0. **Furos M2 D2,2** em v +5,2: **R8: u 18,5 / 37,0 / 111,0 / 129,5** (o instrumento de 32 teclas usa 18,5 + 129,5 nas fileiras 1 e 3 e 37 + 129,5 nas fileiras 2 e 4; o 111 não é usado nas 32 teclas, mas **fica** para as R8E); **R4: 18,5 / 37,0 / 55,5**. Contorno e 5 (R8: 9) entalhes de 2,0 x 4,3 mm na borda de trás, em u = 18,5 k (os das pontas são meios entalhes).
- **J2 e R1 existem nas duas placas.** Nas variantes sem OUT (R8, R4) eles **não são montados** (vão fora da BOM e do CPL): **rotear o J2 e o R1 completos** (a mesma placa serve às quatro variantes); R1 não montado deixa a rede QHP só no pino 9 do 595 e no pad de R1, o que não é um problema (sem trilha solta: é pad a pad).

## 3. Camadas e empilhamento
2 camadas, 1,2 mm, cobre 1 oz. **F.Cu (topo) está livre de peças**: tem só os furos e a área de proibição das cabeças de parafuso. Todo o resto do topo pode ser trilha ou plano. As peças e seus pads são em B.Cu.
**Áreas de proibição já na placa:**
- `M2 fundo (patamar 6,4)`: B.Cu, **sem peça** num quadrado de 6,4 mm em torno de cada furo M2 (trilha pode passar: embaixo há plástico).
- **`M2 topo (cabeça do parafuso D3,8)`: F.Cu, quadrado de 4,6 mm em torno de cada furo M2: sem trilha, sem via e sem plano** (R11V4: o design passou a usar **parafuso M2 passante com porca embaixo**, cabeça de 3,8 mm sobre o topo; cobre embaixo da cabeça de aço é curto).

## 4. Redes e o que é crítico
Rede (R8) · pinos · observação:
| Rede | Pinos | Observação |
|---|---|---|
| **OUT** | U1..U8 pino 4, J1.3, J2.3 | linha **analógica** dos sensores, **barramento de 148 mm**; **largura 0,2 mm (mín. 0,15)**; **0,3 mm de folga mínima de CLK, SER, QHP e QHP_J** (regra no `.kicad_dru`); **sem laço grande** (capacitância; ver §7) |
| **+3V3** | U1..U8 pino 1, C1..C10, U9.10/16, J1.1, J2.1 | **0,3 mm ou mais** de largura; um capacitor de 100 nF por TMAG **encostado no pino 1** (já posicionado: não alongue o laço C1-U1) |
| **GND** | U1..U8 pinos 2 e 5, C, U9.8/13/17(EP), J1.2/4/MP, J2.2/4/MP | **plano de GND no topo (F.Cu) e no fundo (B.Cu)**, costurados com vias; **sem ilhas de plano**; os pinos 2 e 5 do TMAG5253 são pads de GND vizinhos |
| **EN1..EN8** | U_k pino 3 ↔ U9 (QA..QH: 15, 1, 2, 3, 4, 5, 6, 7) | 2 pinos cada; **o 595 da R8 fica no meio (u 74): o maior EN tem ~65 mm**; use o **topo (F.Cu)**, onde não há peça: nas faixas v ∈ ±(1,3 .. 6,7), com folga dos pinos e do furo M2 (a capacidade sobra: ver §7) |
| **CLK** | U9.11, U9.12, J1.5, J2.5 | SRCLK e RCLK juntos; **0,3 mm de OUT** |
| **SER** | U9.14, J1.6 | DADO de entrada; **0,3 mm de OUT** |
| **QHP / QHP_J** | U9.9 → R1.1; R1.2 → J2.6 | cascata (só nas E); **0,3 mm de OUT** |
| NC | U9 QE..QH (R4 apenas: pinos 4 a 7) | sem ligação (deixar **sem** trilha) |
R4: mesmas redes, EN1..EN4, U5 = 595; J2 em u 47,5.
**Pinagem P6s** dos conectores (não mude): 1 +3V3, 2 GND, 3 OUT, 4 GND, 5 CLK, 6 DADO.

## 5. Regras (valem as do `.kicad_dru` e do `.kicad_pro` da placa)
- Trilha mínima **0,15 mm** (preferida 0,2), folga mínima **0,1 mm**, via **0,5 / furo 0,3**, furo a furo 0,25, cobre à borda **0,25 mm**, furo a cobre 0,2.
- **Nada nas áreas de proibição** (§3). **Nada no topo que seja peça.**
- **Ilhas de plano, trilhas soltas (pontas sem ligação) e vias soltas não valem**; todo aviso do DRC conta como falha.
- Passos e raios: 45 graus ou 90; sem cantos agudos.
- O TMAG5253 e o 595 são de passo 0,5 mm (X2SON-4 e DHVQFN-16): **saída dos pads por trilha curta e via a 0,5/0,3**, sem passar entre pads vizinhos.
- Não mexa no `.kicad_dru` das réguas exceto para **adicionar** regra mais estrita.

## 6. Como entregar (critério de aceitação e o que gerar)
**Aceite só com: DRC (com paridade com o esquema) = 0 erros e 0 avisos, 0 ligações faltando, 0 pontas soltas, 0 ilhas, nenhuma trilha abaixo do mínimo.** (`kicad-cli pcb drc --severity-all --schematic-parity`.)
Depois do aceite, na raiz do repositório, com o KiCad python:
1. `REGUA_BOARD=<placa roteada> REGUA_N=8 "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v04/pcb/regua/pacotes_regua.py` (BOM e CPL das variantes: não dependem das trilhas; refaz a conferência `cpl_jlc`).
2. Painéis com trilhas copiadas (cada um escreve Gerbers em `fab/regua_painel_SEM_ROTA_NAO_ENCOMENDAR/`; **mude o nome para `fab/regua/<variante>_painel<N>/` e tire o "SEM_ROTA" do nome quando as trilhas existirem**):
   - R8, 2 tiras: `MODO=regua REGUA_BOARD=... REGUA_N=8 PAINEL_N=2 python .../fab_regua.py`
   - R8, 4 tiras (alternativa): `PAINEL_N=4`
   - R4, 5 tiras: `REGUA_N=4 PAINEL_N=5`
3. Pacote final por variante em `fab/regua/<variante>_painel<N>/`: `gerbers.zip` (F.Cu, B.Cu, F/B Mask, F/B Paste, F/B Silk, Edge.Cuts + furação), `bom.csv`, `cpl.csv` (os dois últimos já estão lá); atualize `fab/regua/LEIAME_COTACAO.md` (o rascunho está pronto, é da eletrônica: reporte o que mudar).
4. **Verifique o painel** (kicad-cli DRC do painel, e a olho na pré-visualização do fundo): os scripts copiam trilhas, vias e zonas e refazem o contorno com abas de 3 mm e microfuros.

## 7. Roteabilidade (a conta da eletrônica; verifique antes de começar)
- **R8:** 80 ligações faltando em ~2 066 mm². O **topo está vazio de peças**: nas duas faixas v ∈ ±(1,3 .. 6,7) cabem ~18 trilhas de 0,2 mm com 0,1 de folga por faixa; as 7 EN longas (EN2..EN8) + OUT + CLK cabem **só no topo**, com vias 0,5/0,3 nos pads. O gargalo **não é espaço de linha, é a saída dos pads do 595 e do TMAG** (0,5 mm): faça as saídas curtas no fundo e suba por via.
- OUT é um **barramento em série pelos 8 sensores + J1 + J2**: roteie em cadeia (não em estrela); evite correr paralela a CLK/SER por mais de poucos mm (regra de 0,3 mm acima).
- **R11V4 (reposicionamento atendido):** o 595 foi para o meio (u 74) e os C1..C8 para a linha central, junto aos pinos 1 e 2 do sensor, para fechar o GND. **Refazer a R8 do zero** a partir de `student_v04_regua8.kicad_pcb` (a roteada anterior não vale mais). A R4 roteada continua como está.
- Os 8 pinos de EN e o OUT passam por **entre os pinos das teclas** (D1,7 em u_célula ± 5,08; furo a cobre 0,2).

## 8. O que NÃO é seu
Placa principal (portão P fechado); posição de qualquer peça ou furo; BOM/CPL (eletrônica); case. Relate em `ROTEAMENTO.md` (seu relatório) o método escolhido, o que falhou, e peça mudanças de posicionamento à eletrônica por lá.
