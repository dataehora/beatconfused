# eTutti Slim · FIT_CHECK (SPEC R12SL, sessão A4)

Resposta à **SPEC R12SL §8.5**. Detalhes: [ELETRONICA.md](ELETRONICA.md) (a última seção **corrige** o que as seções R10SL/R11SL diziam da principal), [RESTRICOES_CASE.md](RESTRICOES_CASE.md) (R27, R29, R44–R46, R63, R65 e o "Resumo dos limitantes"). **Parado. A rota da régua e a principal não mudaram; a sessão B (BGA) não foi tocada; nada cotado ou comprado.**

## 0. Correção importante (erro meu nas sessões A2 e A3)

Eu relatei a principal como "reposicionada" (faixa 18,4 e depois 20,7 mm, DRC 0/0). **Não foi:** o posicionador termina com `no free spot` quando a faixa é menor que a original e não grava nada, e eu li só o DRC (do arquivo antigo). A principal do `main` é a da R9SL (faixa 22,2 mm) e **não cabe em menos**: ensaiei 20,7 e 19,5 mm agora e o posicionador falha nos dois. Consequência: com a régua 1,5 mm mais longa à esquerda, a ponta dela invadia as abas da placa em 4 mm (a figura da A3 já mostrava o cabo saindo de dentro da placa). **Correção:** o teclado inteiro passou 1,5 mm para a direita (`KEY_DX`); a principal e a rota ficam como estão, as pontas esquerdas das réguas voltam aos x de antes e o vão do FFC fica 5,5 / 5,8 mm.

## 1. Resumo

| Parte | Resultado |
|---|---|
| Case | **247,0 × 89,1** (não 245,5: o teclado ficou 1,5 mm à direita); folga régua → parede direita **3,35 mm** (fileiras 1 e 3), 12,6 (2 e 4); ponta esquerda → principal 5,5 / 5,8; → parede esquerda 74,75 / 65,5 |
| Guia | alívio de 0,35 mm (plano a 2,65 do eixo) na face voltada para U9: folga guia–U9 **0,50 mm**; parede do bolso 0,65 mm nos cantos e **0,615 mm** na face aliviada (a de 0,7 pedida não fecha com a folga de 0,5: ver pergunta 2) |
| Fit check | **0 interferências** em 349 pares (`case/fit_check.py`, `case/out/fit_check.json`): base, tampo, réguas, grades, 32 switches, cabos, ferragens, principal, bateria |
| Modelos 3D | **12 STEP baixados do EasyEDA de 12 códigos** + SW403 (que já estava baixado e agora é posicionado) = 22 das 23 peças que eram caixa; **falta 1** (abaixo) |
| Arquivos | `case/montagem/base.step` e `case/montagem/conjunto.glb` regenerados; 7 passos re-renderizados |

## 2. Modelos 3D baixados (EasyEDA, por código LCSC)

D101 e D102 BAV70 C68978; D201 SMF5.0A C151296; D401 XL‑2012SURUGC C965845; FB301 C19330; J202 SM03B‑SRSS‑TB C160403; L101 C14709; L102 C63166; Q201–Q209 AO3400A C20917; U103 W25Q64JVSSIM C5362615; U201 USBLC6‑2SC6 C7519; U302 XC6206P182MR C347373; Y102 32,768 kHz C32346; SW403 TS‑1187A C318884 (já baixado). Dois modelos são genéricos do encapsulamento (BAV70 e XC6206 usam o mesmo SOT‑23‑3L; L101 e FB301 o mesmo 0603). **Falta:** **U102 = NXP MKL02Z32VFG4** (Kinetis KL02, HUQFN16 3 × 3 mm, SOT1581) — peça consignada da PJRC, **sem código LCSC**: forneça o STEP do fabricante (NXP/PJRC); fica em caixa até lá. Achado: o STEP do P2 (PJ‑327A) tem o zero no eixo do cilindro (corpo de z −2,9 a +2,5) e vem girado 90° em relação ao footprint; a cena agora o desce 2,8 mm e o gira, e ele fica entre z 1,5 e 6,9, a 0,4 mm da parede esquerda e dentro do pátio.

## 3. Imagens geradas ou atualizadas nesta sessão

| Caminho | Legenda |
|---|---|
| `case/renders/montagem_p1_iso.png` / `_esq` / `_dir` | passo 1: base com as porcas nos bolsos (guias com o alívio de 0,35 na face de U9); detalhes das guias |
| `case/renders/montagem_p2_iso.png` / `_esq` / `_dir` | passo 2: bateria e principal (agora com os modelos reais); detalhes dos conectores FFC e da baia |
| `case/renders/montagem_p3_*.png` a `montagem_p6_*.png` (iso, esq, dir) | passos 3 a 6: réguas das fileiras 1 a 4 com cabo e grade; pontas esquerda e direita |
| `case/renders/montagem_p7_iso.png` / `_esq` / `_dir` | passo 7: as 32 switches, com os nomes das notas |
| `case/renders/cena_principal_baixo.png` / `cena_principal_iso.png` | principal vista de baixo e isométrica, com os 22 modelos novos |
| `case/renders/corte_principal_registros.png` / `corte_principal_volume.png` / `corte_principal_longitudinal.png` | cortes da principal sob os knobs e no comprimento |
| `case/renders/cena_iso.png` / `corte_tecla.png` / `corte_tecla_4fileiras.png` / `corte_cauda.png` / `corte_longitudinal.png` | cena das réguas e cortes (teclado 1,5 mm à direita) |
| `case/renders/corte_apoio_4fileiras.png` | apoio contínuo entre os M2 |
| `case/img/planta_teclado.png` | planta do teclado com as notas, case de 247,0 |
| `case/img/knobs_s123.png` | S1/S2/S3 dos knobs |
| `pcb/regua/img/planta_regua.png` (+ `.svg`) | planta cotada da régua e da grade (regerada) |
| `pcb/principal/img/planta_principal.png` | planta da principal (a mesma placa; faixa 22,2 mm) |

## 4. Desvios da R12SL

1. **Case 247,0, não ~245,5**, e **teclado 1,5 mm à direita**: sem isso a principal teria de ter faixa menor, e o posicionador não fecha.
2. **Parede da guia 0,615 mm** (0,65 nos cantos), não 0,7: o alívio de 0,35 e a folga de 0,5 a U9 não deixam mais.
3. **U102 (MKL02) segue em caixa**: sem código LCSC.

## Perguntas para o design

1. **Teclado 1,5 mm à direita, case 247,0 (substitui a pergunta 2 da A3).** *Problema:* a régua precisou de 1,5 mm de cauda; a principal não cabe numa faixa menor que 22,2 mm (o posicionador falha em 20,7 e 19,5), então ou o teclado anda ou a principal muda. *Números:* com o teclado 1,5 mm à direita a folga à parede direita fica 3,35 mm em 247,0 (a pedida era ≥ 3,0 em ~245,5: o ganho de 1,5 mm no case não existe mais). *Opções:* (a) aceitar 247,0 com o teclado deslocado (recomendo; só o exterior e a posição das teclas mudam); (b) manter 245,5 e o teclado onde estava, o que exige uma faixa de 20,7 mm: a principal teria de ser refeita (sessão B ou à mão) com o BGA já no meio; (c) 246,0, folga 2,35 (abaixo dos 3,0).
2. **Parede da guia 0,615 mm.** *Problema:* a guia Ø6,0 com a face de U9 aliviada deixa 0,615 mm entre o bolso e a face plana; a de 0,7 pedida exigiria folga de 0,4 a U9 (pátio de U9; o corpo real está mais longe). *Opções:* (a) aceitar 0,615 e ensaiar no protótipo (recomendo); (b) folga a U9 0,40 e parede 0,7; (c) porca com flange ou inserto de latão.
3. **MKL02 (U102).** Fornecer o STEP da NXP MKL02Z32VFG4 (HUQFN16 3 × 3) ou aceitar a caixa.
