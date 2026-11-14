# eTutti StudentViaggio · mapa de pinos

Os pinos são os do Viaggio MicroMod / J1 (`../../viaggio_micromod/pcb/PINOS.md`), com estas diferenças:

| Pino do Teensy MicroMod | Viaggio J1 | StudentViaggio |
|---|---|---|
| 4 | `SENS_EN` (liga os sensores Hall) | livre, sem ligação |
| 14 (A0) | comum do mux direito, saída dos sensores | comum do mux direito, com R602 (10 k) ao 3,3 V |
| 15 (A1) | comum do mux esquerdo, saída dos sensores | comum do mux esquerdo, com R601 (10 k) ao 3,3 V |
| 0, 1, 2, 3 | endereço dos mux (S0–S3) | igual |

## Leitura de uma tecla

- Cada tecla é um pente de cobre: metade no GND, metade na entrada do mux.
- Com a tecla escolhida pelo endereço, a tensão no pino é `3,3 V × Rtecla / (Rtecla + 10 k)`.
- Tecla solta: 3,3 V (fundo de escala). Quanto mais forte o toque, menor a tensão.
- Não há mais os grupos `EN_A` / `EN_B` nem a espera de 45 µs depois de trocar o S3.

## Teclas e canais (lidos da netlist; iguais aos da placa J1)

| Tecla | Nota | Fileira | Mux | Canal | Pino do Teensy |
|---|---|---|---|---|---|
| K01 | A3 | 1 | U601 | 5 | 15 (A1) |
| K02 | C4 | 1 | U601 | 4 | 15 (A1) |
| K03 | D#4 | 1 | U601 | 1 | 15 (A1) |
| K04 | F#4 | 1 | U601 | 3 | 15 (A1) |
| K05 | A4 | 1 | U602 | 2 | 14 (A0) |
| K06 | C5 | 1 | U602 | 1 | 14 (A0) |
| K07 | D#5 | 1 | U602 | 0 | 14 (A0) |
| K08 | G3 | 2 | U601 | 9 | 15 (A1) |
| K09 | A#3 | 2 | U601 | 10 | 15 (A1) |
| K10 | C#4 | 2 | U601 | 15 | 15 (A1) |
| K11 | E4 | 2 | U601 | 13 | 15 (A1) |
| K12 | G4 | 2 | U602 | 13 | 14 (A0) |
| K13 | A#4 | 2 | U602 | 11 | 14 (A0) |
| K14 | C#5 | 2 | U602 | 14 | 14 (A0) |
| K15 | E5 | 2 | U602 | 15 | 14 (A0) |
| K16 | G#3 | 3 | U601 | 2 | 15 (A1) |
| K17 | B3 | 3 | U601 | 7 | 15 (A1) |
| K18 | D4 | 3 | U601 | 6 | 15 (A1) |
| K19 | F4 | 3 | U602 | 4 | 14 (A0) |
| K20 | G#4 | 3 | U602 | 6 | 14 (A0) |
| K21 | B4 | 3 | U602 | 5 | 14 (A0) |
| K22 | D5 | 3 | U602 | 3 | 14 (A0) |
| K23 | A3 | 4 | U601 | 12 | 15 (A1) |
| K24 | C4 | 4 | U601 | 11 | 15 (A1) |
| K25 | D#4 | 4 | U601 | 8 | 15 (A1) |
| K26 | F#4 | 4 | U602 | 9 | 14 (A0) |
| K27 | A4 | 4 | U602 | 8 | 14 (A0) |
| K28 | C5 | 4 | U602 | 10 | 14 (A0) |
