# eTutti Viaggio J1 · passo M3 (conferência e fabricação)

Atende a **SPEC v2.4** (`etutti/hardware/viaggio_micromod/SPEC.md`, "Tarefas para o Code (v2.4)"), sobre a placa `kicad/viaggio_micromod.kicad_pcb` do `main` depois do PR #126 e do commit 93aa0e3. Branch `viaggio-j1-m3`.

Medidas em mm, no referencial do KiCad (x para a direita, y para baixo, isto é, em direção ao músico). **(conferir)** = estimativa a confirmar com a peça real ou o datasheet.

## Estado dos lotes

| Lote | O quê | Estado |
|---|---|---|
| 1 | ajustes pedidos na v2.4 | **feito** (commit deste lote) |
| 2 | conferências: DRC final, placa × firmware 28/28, flexão, alturas | a fazer |
| 3 | fabricação: Gerbers, furação, BOM/CPL, plate, POWER.md, imagens | a fazer |

Se a sessão cair, a próxima parte do último lote enviado (`git log` da branch) e desta tabela.

## Como rodar

```
python etutti/hardware/viaggio_micromod/pcb/schematic.py          (esquema, ERC, BOM preliminar)
copiar viaggio_micromod/pcb/kicad/viaggio_micromod_E.kicad_sch para viaggio_j1/kicad/
"C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote1
```

- O `lote1` sempre parte da placa do commit 93aa0e3 (tirada do Git), faz os ajustes e grava pelo **mesmo método dos PRs #120/#123/#126**: o pcbnew salva uma cópia, e só os objetos novos, removidos e mudados, mais as 4 zonas repreenchidas, entram no arquivo original. O script confere bloco a bloco, por uuid, que todo o resto ficou idêntico (4008 blocos).
- `.kicad_pro`, `.kicad_prl` e `.kicad_dru` não mudaram.
- O registro de tudo (peças, trilhas, vias, removidos, DRC) fica em `m3.json`.
- Cada trilha e via nova é conferida com as formas exatas do pcbnew antes de entrar (folga da classe + 0,005), pela classe `Geo` do `energia.py`.

## Lote 1 · ajustes (v2.4)

### 1. C202 / C206: referência e `Codigo` batendo com a função

**Decisão:** trocar as duas peças de lugar na placa, sem mexer no esquema.
- No esquema, o C202 é o capacitor de VSYS do carregador (E3) e o C206 é o capacitor de VSYS do conversor (E4). O PR #126 tinha posto o **C202** na entrada do U204 e o **C206** no norte do bloco, ao contrário da função.
- As duas são a mesma peça (10 µF 0805, C15850), com as mesmas redes (VSYS/GND). Então basta trocá-las de lugar na placa:
  - C206 (E4) vai para (69,60; 12,25; 180), a entrada do U204 (VIN, pino 5);
  - C202 (E3) vai para (64,67; 5,18; 180), o capacitor de VSYS no norte do bloco.
- Assim o esquema continua como o `schematic.py` gera, sem renumerar nada. Na placa mudam só a posição dos dois footprints. Trilhas e vias ficam iguais.
- **Atenção a quem lê o `COBRE.md`:** lá, "C202" é o capacitor de entrada do U204. Agora esse lugar é do C206.

### 2. Capacitor de VSYS junto dos pinos OUT (10/11) do U202: C210, no lado de cima

- **Peça nova no esquema:** C210, 10 µF 0603, VSYS/GND, `Codigo` E3, LCSC **C19702** (Samsung CL10A106KP8NNNC, 10 V, básica). Entra pelo `viaggio_micromod/pcb/schematic.py`, que regenera a folha E. A folha vai copiada para `viaggio_j1/kicad/`. ERC 0/0 no esquema do J1.
- **No verso não coube.** Procurei todas as posições a até 4 mm dos pinos (grade de 0,1, 4 rotações), mesmo sem o D205 e sem as vias de costura. Nenhuma passou. O canto a oeste dos pinos tem as 2 vias de VSYS, o D205 e as trilhas de VOL_SW, CHGLED, CHG_N e CHG_EN1. Mover o D205 obrigaria a refazer essas quatro redes.
- **No lado de cima coube, sem mover nada:** C210 em (60,76; 8,60; 270), em F.Cu, logo acima dos pinos OUT (que estão no verso, em x 60,56).
  - O pad de VSYS, em (60,76; 7,83), fica sobre a ponta da trilha de VSYS de F.Cu que sai das 2 vias dos pinos OUT. O caminho do pino ao capacitor é de ~3 mm, contra ~6 mm do capacitor mais perto antes.
  - O pad de GND, em (60,76; 9,38), vai por 0,85 mm de F.Cu a 0,3 até a via térmica do U202 em (61,60; 9,40). O retorno entra direto no pad térmico do carregador.
- **Montagem:** a placa já é montada dos dois lados (E1, E2, F2 e o LED estão em cima). O C210 é só mais uma peça 0603 no lado de cima, na área do logo. Altura 0,95.

### 3. C207 junto do C208

- O C207 (10 µF de +3V3) foi de (65,40; 13,90) para **(73,25; 5,70; 0)**, a 3,55 mm do C208 (de centro a centro). Distância percorrida: 11,35 mm.
- O pad de +3V3 (72,30; 5,70) liga ao C208.1 por 1,65 mm de B.Cu a 0,6, passando pela via de +3V3 do C208 em (71,40; 6,00).
- Vias novas, fora do corpo da peça: 2 de GND a leste do pad 2, em (75,10; 5,70) e (74,78; 4,83), e 1 de +3V3 a oeste do pad 1, em (71,47; 5,36).
- Saíram as 4 vias e os 4 tocos do lugar antigo, e 2 vias de costura de GND que ficavam sob o lugar novo, em (73,25; 5,75) e (74,75; 5,75).

### 4. C304: via de GND fora do pad

- Saiu a via de GND de dentro do pad 2, em (20,00; 35,00).
- Saíram 4 trilhas de +3V3 do laço do J entre C305.1 e C304.1, todas a 0,2 em B.Cu.
- **Só abrir o laço não bastou.** Uma via de GND colada ao C304, onde ele estava, não cabe em nenhum lado:
  - a leste, a linha **VOL_B** do In2 (x 20,894);
  - a oeste e ao sul, a **I2S_BCLK** em B.Cu (x 19,41 e a diagonal);
  - ao norte, a via e a trilha de F.Cu da **I2S_BCLK**;
  - ao sul, também a **HP_L** em F.Cu.
- **Solução:** o C304 andou **0,59 mm** para o espaço que o laço deixou, para (20,45; 35,89; 180), deitado. Foi a menor distância numa busca a até 2 mm.
  - O pad 2 (GND) tem agora a sua própria via em (19,97; 35,22), a 0,7 mm, ligada por 0,2. A via fica fora do pad.
  - O pad 1 (+3V3) fica na trilha nova de +3V3 do J refeita: C305.1 → C304.1 → junção com o U301 em (21,18; 36,86), toda a 0,2 em B.Cu, reta em x 21,181.
- A mudança está registrada como pergunta para a gestão, porque a v2.4 autorizou a trilha, não o movimento do C304. Ele já tinha andado 1,56 mm no PR #126.

### 5. DRC do lote 1

`kicad-cli pcb drc --schematic-parity --severity-all`, com o `.kicad_dru` da placa:

| | Base (93aa0e3) | Lote 1 |
|---|---|---|
| track_width | 7 (do J: 3 EN_B, 4 MUX_S0) | 7 (as mesmas) |
| clearance, short, furos, pátios, ponte de máscara, borda | 0 | 0 |
| ligações não feitas | 0 | **0** |
| paridade com o esquema | 0 (1 com o esquema novo, que já tem o C210) | **0** |

Nenhuma violação nova.

### Imagens do lote 1

Em `build/`, olhadas:
- `m3_lote1_energia_fcu.png`, `_bcu.png`, `_in2.png`: o bloco de energia, com o C210 em cima e o C207 junto do C208;
- `m3_lote1_c304_fcu.png`, `_bcu.png`, `_in2.png`: o C304 com a via fora do pad.

### Fora da pasta do J1

- O `viaggio_micromod/pcb/schematic.py` ganhou o C210. O `bom_preliminar.csv` e a folha E de `viaggio_micromod/pcb/kicad/` foram regenerados.
- A placa do M2 em `viaggio_micromod/pcb/kicad/` (sem roteamento) não tem o C210. Ela não é mais a placa que segue (SPEC v2.4) e não foi mexida.
