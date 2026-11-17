# eTutti Student V3 — conceito da placa (sem roteamento, para aprovação)

A V3 é a V2 com a placa refeita para a **JLCPCB montar tudo pelo fundo** na montagem econômica. O tamanho da placa, o
teclado e o case ficam como na V2. Esta pasta tem a placa **posicionada e sem trilhas**; o roteamento só começa depois da
sua aprovação.

Ordem para regenerar (a partir da raiz do repositório):

```
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/build_sem_rota.py   # placa sem rota + pcb/colocacao.json
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/student_v03/auditoria_pinos.py  # tabelas pino a pino
python etutti/hardware/student_v03/bom_v3.py                                                  # BOM com Basic/Extended (consulta a JLCPCB)
```

Arquivos: `kicad/student_v03_sem_rota.kicad_pcb`, `renders/` (placa inteira e a metade esquerda, topo e fundo),
`bom_v3.csv`, `AUDITORIA.md`, `pcb/colocacao.json`, `pcb/drc_sem_rota.json`.

## O que mudou em relação à V2

| | V2 | V3 |
|---|---|---|
| Lado do topo | encoders, USB-C, 2 jacks, ESD, TVS, 4 passivos, J401, H101 | **só os 2 encoders** (e os pads dos fios do alto-falante) |
| USB-C, jacks, ESD, TVS, 4 passivos | topo | **fundo**, montados pela JLCPCB |
| Conector da tela (J401) | topo | fundo, com **fenda de 7 × 2,5 mm** na placa para o cabo subir à tela |
| H101 (espaçador do módulo) | Würth SMD (a econômica recusa) | **furo liso de 2,7 mm**: parafuso M2,5 pelo topo, espaçador de nylon de 2,5 mm, módulo, porca |
| Tracejado do case e posições alternativas (E1 v1, F2 v1) | na serigrafia | **removidos**, e todos os rótulos de setor da V1 |
| C307 (VAG do SGTL5000) | 150 nF | 100 nF (datasheet) |
| R203, R501 | 1,8 kΩ, 680 kΩ (Extended) | 2,2 kΩ, 1 MΩ (Basic) |
| D202–D205 | BAT54C (Extended) | BAV70 (Basic) |

Posições novas (mm, em `pcb/colocacao.json`): USB-C, J301 e J302 ficam onde estavam (x = 5,95 e 4,3, na borda esquerda,
mesmo y), agora no fundo. U201 (ESD) foi 2,1 mm, D201 (TVS) 1,4 mm, os passivos de microfone até 2,2 mm; C210 foi 6 mm
(para (64,8; 13,1)); J401 foi de (39; 33) para (35,5; 36,5) e a fenda ficou em x 32,0–39,0, y 29,9–32,4 (entre o módulo e o
conector, na direção da tela).

**Blocos de função.** Energia (BQ24074, TPS63001, indutor, bateria: x 60–75, y 5–27), som (SGTL5000 em x 24, MAX98357A
em (54; 85), jacks na borda esquerda), controle (encoders em x 20,5 e 38,5, y 42; botão Program; o módulo MicroMod em
x 28–50, y 7–29) ficam todos à esquerda do teclado, na área de interface. Os multiplexadores continuam na faixa de trás,
junto dos sensores, e o primeiro sensor fica a 38 mm do indutor, o componente magnético mais próximo.

Verificação da colocação: DRC do KiCad sem sobreposição de contornos de peças, sem erro de furo ou de borda; só os 449
"não conectados" (o ratsnest: ainda não há trilhas) e avisos de serigrafia.

## Custo estimado da JLCPCB (5 placas, 2 montadas)

| | US$ |
|---|---|
| Placa (engenharia 25,00 + placa 14,50, cotação de 18 nov) | 39,50 |
| Preparação e estêncil da montagem econômica | 9,79 |
| **17 tipos Extended × 3,09** (eram 16 na cotação; saíram BAT54C, R203, R501 e C307, entraram USB-C, jack, J401, ESD e TVS) | 52,53 |
| Peças (cotação: 65,00 para 31 linhas; as peças novas somam uns 3,00) | ~68 |
| SMT e nitrogênio | ~3,20 |
| **Total (estimativa)** | **~173** |

Contra os US$ 157,47 do Lite (com os mesmos 5 conectores no topo, soldados em casa), a V3 custa uns US$ 15 a mais na JLCPCB
e tira 11 peças da bancada. Para reduzir: **retirar o USBLC6 (ESD) e o SMF5.0A (TVS)** economiza 2 tipos Extended (US$ 6,18),
mas tira a proteção do USB. Não fiz isso; é decisão sua.

## Para você decidir antes do roteamento

1. As posições acima (veja `renders/esq_bottom.png`: a vista de baixo está espelhada para a borda esquerda ficar à esquerda).
2. **Conectores no fundo mudam o case.** O USB-C e os jacks passam a ficar abaixo da placa: as aberturas da parede esquerda
   do case sobem/descem de altura e a base passa a fazer parte delas. Isso entra na etapa do case, depois do roteamento.
3. A fenda do cabo da tela (7 × 2,5 mm) fica entre o módulo e o J401.
4. Proteção do USB (ESD e TVS): manter ou tirar.
5. Os três datasheets que não obtive (PJ-327A, TS-1187A, XC6206 da UMW): veja `AUDITORIA.md`.
