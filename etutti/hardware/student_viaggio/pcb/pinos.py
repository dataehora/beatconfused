"""Write PINOS.md (the differences from the Viaggio J1 and the key / mux channel table).

    python etutti/hardware/student_viaggio/pcb/pinos.py        (after schematic.py)

The table is read from the netlist schematic.py exported, so it is the board's.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr as S  # noqa: E402

CHAN = {"9": 0, "8": 1, "7": 2, "6": 3, "5": 4, "4": 5, "3": 6, "2": 7, "23": 8, "22": 9, "21": 10, "20": 11,
        "19": 12, "18": 13, "17": 14, "16": 15}
HEAD = """# eTutti StudentViaggio · mapa de pinos

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
"""


def main():
    tree = S.parse(open(os.path.join(HERE, "build", "student_viaggio_netlist.net"), encoding="utf-8").read())
    where = {}
    for n in S.find(S.first(tree, "nets"), "net"):
        name = S.first(n, "name")[1].lstrip("/")
        if not name.startswith("OUT_K"):
            continue
        for x in S.find(n, "node"):
            ref, pin = S.first(x, "ref")[1], S.first(x, "pin")[1]
            if ref in ("U601", "U602"):
                where[name] = (ref, CHAN[pin])
    keys = {int(r["switch"][2:]): r for r in
            csv.DictReader(open(os.path.join(HERE, "..", "..", "pocket", "pcb", "build", "pocket_keys.csv")))}
    rows = []
    for n in range(1, 29):
        ref, ch = where["OUT_K%02d" % n]
        k = keys[n]
        rows.append("| K%02d | %s | %s | %s | %d | %s |" % (n, k["note"], k["row"], ref, ch,
                                                           "15 (A1)" if ref == "U601" else "14 (A0)"))
    used = {v for v in where.values()}
    if len(rows) != 28 or len(used) != 28:
        raise SystemExit("key table: %d keys on %d mux inputs" % (len(rows), len(used)))
    open(os.path.join(HERE, "PINOS.md"), "w", encoding="utf-8", newline="\n").write(HEAD + "\n".join(rows) + "\n")
    print("PINOS.md: 28 teclas em 28 entradas (U601: %d, U602: %d)" % (
        sum(1 for r, _ in used if r == "U601"), sum(1 for r, _ in used if r == "U602")))


if __name__ == "__main__":
    main()
