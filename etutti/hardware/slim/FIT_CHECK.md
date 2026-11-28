# eTutti Slim · FIT_CHECK (SPEC R13SL, sessão A5)

Resposta à **SPEC R13SL §8.6**. Não muda a geometria. Detalhes: [ELETRONICA.md](ELETRONICA.md) (as seções R10SL e R11SL agora têm um aviso de correção no topo), [RESTRICOES_CASE.md](RESTRICOES_CASE.md). **Parado. A sessão B (BGA) não foi iniciada; nada cotado ou comprado.**

## 1. Regra de verificação (R13SL item 4)

**Como ela falhou nas A2/A3 (diagnóstico):** `posiciona_principal.py` já terminava com código ≠ 0 (`raise SystemExit("... no free spot")`), mas eu o rodava dentro de um pipeline (`script | tail -1 && drc`), que devolve o código do `tail` (0) e esconde a falha; o DRC então leu o arquivo antigo.

**O que foi feito:** `verificacao.py` (novo) e `rodar_verificado.py` (novo: roda o comando mostrando a saída INTEIRA, o código de saída e a data dos arquivos pedidos; sai com 3 se um arquivo não foi gravado nesta execução). **9 scripts ajustados** (terminam com código ≠ 0 quando falham ou quando uma saída não foi gravada nesta execução, e imprimem `VERIFICADO <arquivo> | gravado <data hora>`): `pcb/posiciona_principal.py`, `pcb/principal/drc_principal.py` (apaga o relatório antigo antes e imprime a placa verificada com a data), `pcb/regua/posiciona_regua.py`, `pcb/regua/rota/etapas.py`, `case/case.py`, `case/fit_check.py` (sai 1 se houver interferência), `case/montagem.py`, `case/cena_regua.py`, `case/cena_principal.py`.

| Script | Sucesso (código; arquivos gravados nesta execução) | Falha forçada (código; o que sobrou) |
|---|---|---|
| `posiciona_principal.py` | 0; `slim_principal.kicad_pcb` e `posicao_principal.json` gravados 2026-11-26 00:00:08 | **2** com faixa estreita (`SLIM_ENVELOPE` com faixa −39,0): `ERRO: C124: no free spot ... NOTHING was written`; os dois arquivos seguem com a data antiga (22:52:41), "NAO nesta execucao" |
| `drc_principal.py` | 0; relatório 00:00:10, placa verificada (gravada 00:00:08) | (herda a regra: apaga o relatório antes; sem relatório novo sai 3) |
| `posiciona_regua.py` | 0; régua, grade e `posicao_regua.json` gravados 23:51:53 | **4** (`SLIM_FORCAR_FALHA`): "nada foi gravado"; arquivos inalterados (20:53:15) |
| `etapas.py` | 0; `verifica.json` 23:52:12, `grade.json` 23:52:16, `slim_regua_rota.kicad_pcb` 23:51:59 | **1** com `R_TW=0.9` (o roteador não fecha): `ERRO: etapa sinais falhou ...`; estado `feito: false` |
| `case.py` | 0; `base.step`, `tampo.step`, `anel_led.step`, `numeros.json` gravados 23:52:38–40 | **1** com `SLIM_CASE_RIGHT=-120`: "case sem largura"; `base.step` com data antiga |
| `fit_check.py` | 0; 0 interferências em 349 pares (`fit_check.json` 00:05:31) | **1** com `SLIM_FIT_DESLOCA=regua0:0,0,9`: 1 interferência (régua 0 dentro do tampo, 1,1 mm) |
| `montagem.py` | 0; 21 PNG, `conjunto.glb`, `base.step` gravados 00:04:37 | **4** (`SLIM_FORCAR_FALHA`) |
| `cena_regua.py` | 0; 5 PNG gravados 00:00:26–29 | **4** (`SLIM_FORCAR_FALHA`) |
| `cena_principal.py` | 0; 5 PNG e `cena_principal.json` gravados 00:03:58–04:03 | **4** (`SLIM_FORCAR_FALHA`) |

Observações: (a) o roteador de grade da régua grava `sinais.kicad_pcb` mesmo quando falha (a rota fica incompleta); o código de saída é 1 e `etapas.py` marca `feito: false`, e depois do teste rodei tudo de novo com sucesso; (b) os ganchos de teste (`SLIM_FORCAR_FALHA`, `SLIM_ENVELOPE`, `SLIM_STRIP_X1`, `SLIM_ENV_OUT`, `SLIM_CASE_RIGHT`, `SLIM_FIT_DESLOCA`) ficam nos scripts e só agem se a variável existir; (c) o teste de falha forçada do `fit_check.py` regravou o `fit_check.json` com a interferência, e eu rodei de novo com sucesso (00:05:31) antes de relatar.

## 2. MKL02 (U102)

**STEP baixado** do EasyEDA pelo código **C2056583** (título do modelo: `QFN-16_L3.0-W3.0-P0.50-TL-EP1.9`; 1,3 MB). **Confere com o footprint** `QFN-16-1EP_3x3mm_P0.5mm_EP1.9x1.9mm`: corpo 3,02 × 3,02 mm (footprint 3 × 3), passo 0,5, pad térmico 1,9, as bolas/pads de ±1,5125 mm coincidem com o contorno do modelo; altura 0,75 mm. A cena usa o modelo para o U102 (a BOM continua sem código: peça consignada da PJRC). A principal agora tem **120 modelos reais e 0 caixas**.

## 3. Re-verificação sobre o `main`, com a regra nova

| Verificação | Arquivo verificado | Gravado em | Resultado |
|---|---|---|---|
| DRC da principal (`drc_principal.py`, `kicad-cli`, com paridade) | `pcb/kicad_principal/slim_principal.kicad_pcb` | **2026-11-26 00:00:08** (nesta sessão, pelo `posiciona_principal.py`, que reproduz a placa do `main`) | **0 erros, 0 avisos, paridade 0** (379 ligações abertas: sem rotas, como deve ser) |
| DRC da régua (`kicad-cli pcb drc --schematic-parity --refill-zones --all-track-errors`) | `pcb/regua/rota/kicad/slim_regua_rota.kicad_pcb` | **2026-11-25 23:51:59** | **0 violações, 0 não ligados, paridade 0** |
| DRC da grade | `pcb/regua/rota/kicad/grade/slim_grade.kicad_pcb` | **2026-11-25 23:52:12** | **0 violações, 0 não ligados** (a grade não tem esquema: paridade não se aplica) |
| Fit check | `case/out/fit_check.json` | **2026-11-26 00:05:31** | **0 interferências em 349 pares** |
| `check_placa.py` (pinos × placa) | `pcb/principal/posicao_principal.json` | 2026-11-26 00:00:08 | 21/21 |

**Faixa da principal confirmada: 22,2 mm** (x −58,5…−36,3; abas até −26,75). **Restos de 18,4 / 20,7 mm corrigidos em:** `ELETRONICA.md` (aviso de correção no topo das seções R10SL e R11SL e quatro frases reescritas). `RESTRICOES_CASE.md` não tinha restos (já corrigido na A4: R44 = 22,2 mm; os outros "18,4" e "20,7" ali são o Ø18,4 da saia do knob e a altura 20,7 do botão apertado). A SPEC mantém os números antigos só como histórico das revisões.

## 4. Imagens geradas ou atualizadas nesta sessão

| Caminho | Legenda |
|---|---|
| `case/renders/montagem_p1_iso.png` / `_esq` / `_dir` | passo 1: a base com as porcas nos bolsos |
| `case/renders/montagem_p2_iso.png` / `_esq` / `_dir` | passo 2: bateria e principal, agora com o MKL02 real (120 modelos, 0 caixas) |
| `case/renders/montagem_p3_*.png` a `montagem_p6_*.png` (iso, esq, dir) | passos 3 a 6: réguas das fileiras 1 a 4 com cabo e grade |
| `case/renders/montagem_p7_iso.png` / `_esq` / `_dir` | passo 7: as 32 switches com os nomes das notas |
| `case/renders/cena_principal_baixo.png` / `cena_principal_iso.png` | principal vista de baixo e isométrica, com o MKL02 |
| `case/renders/corte_principal_registros.png` / `corte_principal_volume.png` / `corte_principal_longitudinal.png` | cortes da principal sob os knobs e no comprimento |
| `case/renders/cena_iso.png` / `corte_tecla.png` / `corte_tecla_4fileiras.png` / `corte_cauda.png` / `corte_longitudinal.png` | cena das réguas e cortes (regerados) |
| `pcb/regua/img/regua_frente.png` / `regua_verso.png` / `regua_cabeca_verso.png` / `grade.png` | régua roteada (lados das teclas e das peças), detalhe da cabeça e grade, regerados pela etapa `imagens` do `etapas.py` |

## Perguntas para o design

Nenhuma bloqueante. Duas de contexto:

1. **Ganchos de teste nos scripts de produção.** *Problema:* para provar a falha forçada de cada script deixei variáveis de ambiente (`SLIM_FORCAR_FALHA` e outras) que só agem se existirem. *Opções:* (a) manter (recomendo: permitem repetir o teste); (b) tirar depois da A5, ficando só o teste na mensagem.
2. **`posiciona_principal.py` e a faixa mínima.** *Problema:* o posicionador não fecha em faixa menor que 22,2 mm (falhou em 20,7 com dois conjuntos de pilares e em 19,5). *Opções:* (a) a sessão B parte desta placa e informa no B2 se o RT1062 cabe nela (como na SPEC); (b) antes, dar ao posicionador uma faixa menor à mão para ganhar largura (fora desta sessão).
