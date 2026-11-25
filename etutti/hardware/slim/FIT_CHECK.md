# eTutti Slim · FIT_CHECK (SPEC R8SL: Etapa 3a, roteamento da régua + firmware)

Resposta à **SPEC R8SL §8**. Relatórios: [ROTEAMENTO.md](ROTEAMENTO.md) (comparação dos métodos), [ELETRONICA.md](ELETRONICA.md) (LED em ânodo comum, última seção), [FIRMWARE.md](FIRMWARE.md) (seção R8SL), `pcb/regua/rota/`. **Parado nos portões C‑régua e F‑1. A principal não foi roteada; nada cotado ou comprado.**

## 1. Resumo

| Parte | Resultado |
|---|---|
| **Método de roteamento** | **híbrido**: a parte regular da régua (barramentos, derivações, 8 pistas EN, vias da cabeça) por script; só a cabeça (DATA, CLK, LATCH, OUT, +3V3) pelo roteador de grade próprio; GND por script. Nem o KiCadRoutingTools (v0.24.2, achado em `GitHub/KiCadRoutingTools`) nem o roteador próprio sozinhos fecharam; o híbrido fecha em ~6 s e é repetível (duas execuções, saídas idênticas). Números em `ROTEAMENTO.md` §3 |
| **Régua roteada** | `pcb/regua/rota/kicad/slim_regua_rota.kicad_pcb`; **DRC 0 erros / 0 avisos, 0 não ligados, paridade 0** (reconferido por mim com `kicad-cli --schematic-parity --refill-zones --all-track-errors`); 97 vias (24 de sinal, 73 de GND); 223 segmentos, 1042,7 mm de sinal; trilha mínima 0,15; OUT × DATA/CLK/LATCH ≥ 2,07 mm (regra ≥ 1,0); sem pontas soltas nem ilhas |
| **Grade** | Gerbers em `pcb/regua/rota/kicad/grade/fab/`, DRC 0/0/0; 8 furos 14,000 com dog‑bone, 2 M2 de Ø2,2 com a nota do escareado D4,4 × 90°, sem cobre. **Problema:** o escareado D4,4 deixa só **0,05 mm** de FR‑4 até o furo quadrado e consome 1,1 dos 1,2 mm |
| **Imagens da régua** | `pcb/regua/img/regua_frente.png`, `regua_verso.png`, `regua_cabeca_verso.png`, `grade.png` (notas das 4 fileiras em cada posição) |
| **LED do anel** | XINGLIGHT XL‑2012SURUGC (C965845), vermelho + verde puro, ânodo comum por ligação (pinos 2 e 4 no +3V3); ERC principal 0/0; principal reposicionada: DRC sem trilhas 0/0, paridade 0 |
| **Firmware** | produção (Teensy 4.1) e bancada (Teensy 4.0) **compilam sem avisos**; `check_pins` 15/15, `check_teclas` 32/32, `check_placa` 21/21; **roda no Teensy 4.0 do J** (gravado, enumera como "eTutti"); CPU de áudio 13–19 % (8 notas), pior caso 29,8 %; 8 blocos de áudio; flash 78,7 KB + 1,21 MB de amostras (produção), RAM1 61,9 KB, RAM2 22,4 KB |
| **Registros** | os 7 e o segmento de 4 ranks dão sinal no mixer de saída (picos 0,12–0,21, sem clip); **o som no fone não foi ouvido** por mim: é o que falta o J ouvir |

## 2. Achados

1. **Full Speed:** a rotina da V4 (`startup_late_hook`, `PFSC |=`) roda 300 ms depois do `usb_init()`: o host já enumerou em High Speed (medido PSPD = 2). O Slim faz um desconectar suave (RS = 0, PFSC, 60 ms, RS = 1) e fica em Full Speed (PSPD = 0). A V4 provavelmente tem o mesmo problema (não tocada).
2. **KiCadRoutingTools:** no padrão baixa sozinho as regras (trilha 0,127, via 0,25, vias em pad); estrito, não fecha LATCH/OUT; deixa vazios de 0,05–1 mm entre trilha e pad.
3. As amostras licenciadas continuam fora do Git (`etutti/firmware/slim/.gitignore`).
4. O verde puro (520 nm) tem Vf ~3,1 V: com R410 = 100 Ω e 3,3 V a corrente é ~2 mA (pode ficar fraco; trocar por 47 Ω se preciso).

## 3. Desvios da R8SL

1. O agente de roteamento não fez um commit por etapa (a árvore de trabalho está num ramo antigo): as etapas são idempotentes com estado em `estado.json`, e o commit é um só, no PR.
2. O roteamento da régua é híbrido e específico da R8 (não serve para a principal).
3. O som no fone não foi ouvido (só medido por `AudioAnalyzePeak`).

## Perguntas para o design

1. **Escareado M2 da grade:** D4,4 × 90° deixa 0,05 mm de FR‑4 até o furo quadrado. Reduzir o escareado (cabeça M2 DIN 965 ~3,8 mm: ~0,35 mm de parede), mudar o fixador (cabeça cilíndrica sem escareado) ou afastar os furos M2?
2. **Pistas EN em 0,15 mm** (padrão JLCPCB): aceita, ou quer 0,2 mm (+0,8 mm de placa na frente da régua)?
3. **LED verde:** 100 Ω dá ~2 mA no verde puro; troco o R410 por 47 Ω?
4. **Etapa 3b:** a principal (4 camadas, 120 peças) precisa de outro método; começo pelo escape do BGA?
