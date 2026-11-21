"""eTutti Student V3: the speaker's closed box and its bass (SPEC v4 item 10, task 10).

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe etutti/hardware/student_v03/estudos/acustica.py

A closed box behind a small speaker is a second-order high-pass: the air in the box is a spring
added to the cone's own, so the resonance goes up from fs to

    fc = fs * sqrt(1 + Vas / Vb)        Qtc = Qts * sqrt(1 + Vas / Vb)

(Vas = the volume of air as stiff as the cone's suspension, Vb = the box). Below fc the level
falls 12 dB per octave.

The speaker is a 28 x 5 mm, 8 ohm, 2 W micro-speaker. Makers of this size publish fs and the
sensitivity, rarely Vas and Qts, so the study runs a nominal speaker and a range round it:

    fs   450 Hz (range 380-550: what 28 mm parts of 5 mm give)
    Qts  1.2    (0.9-1.6)
    Vas  15 cm3 (8-25), from fs, a moving mass of 0.2 g and a 23 mm cone:
         Vas = rho c^2 Sd^2 / ((2 pi fs)^2 Mms)

These must be replaced by the bought part's numbers (or measured: fs and Qts come from one
impedance sweep, Vas from a second sweep in a known box).

Writes estudos/acustica.json and estudos/acustica.png.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_JSON = os.path.join(HERE, "..", "case", "out", "r4_28.json")
RHO, C = 1.18, 343.0
NOMINAL = {"fs": 623.0, "qts": 1.63, "sd_cm2": 4.52, "mms_g": 0.087, "vas_cm3": 21.5}     # Dayton CE28MB-8 datasheet (R4V4)
RANGE = {"fs": (560.0, 690.0), "qts": (1.4, 1.9), "vas": (18.0, 26.0)}    # +-10 % round the datasheet values
LOWEST_NOTE = 196.0        # G3


def vas_cm3(fs, sd_cm2, mms_g):
    return RHO * C ** 2 * (sd_cm2 * 1e-4) ** 2 / ((2 * math.pi * fs) ** 2 * mms_g * 1e-3) * 1e6


def box(fs, qts, vas, vb):
    a = math.sqrt(1 + vas / vb)
    return fs * a, qts * a


def level_db(f, fc, qtc):
    s = (f / fc) ** 2
    return 10 * np.log10(s ** 2 / ((1 - s) ** 2 + s / qtc ** 2))


def f3(fc, qtc):
    a = 1 / (2 * qtc ** 2) - 1
    return fc * math.sqrt(a + math.sqrt(a * a + 1))


def main():
    modelled = json.load(open(CASE_JSON, encoding="utf-8"))["caixa_acustica"]["camara_cm3"] \
        if os.path.exists(CASE_JSON) else 3.9
    vas = NOMINAL["vas_cm3"]
    boxes = [("caixa em L da R4V4, como modelada", modelled), ("a mesma, com manta acustica (+15 %)", modelled * 1.15),
             ("caixa redonda da SPEC v1 (3,9 cm3)", 3.9), ("caixa em L da V2 (10,4 cm3)", 10.4), ("caixa de 12 cm3", 12.0), ("caixa de 20 cm3", 20.0),
             ("sem caixa: o case inteiro (~150 cm3, vazando)", 150.0)]
    f = np.logspace(math.log10(100), math.log10(5000), 300)
    out = {"alto_falante": dict(NOMINAL, vas_cm3=round(vas, 1), nota="valores nominais de um micro alto-falante de 28 x 5 mm; "
                                "trocar pelos do datasheet da peca comprada"),
           "faixas": RANGE, "caixas": []}
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, vb in boxes:
        fc, qtc = box(NOMINAL["fs"], NOMINAL["qts"], vas, vb)
        lo = box(RANGE["fs"][0], RANGE["qts"][0], RANGE["vas"][0], vb)
        hi = box(RANGE["fs"][1], RANGE["qts"][1], RANGE["vas"][1], vb)
        rec = {"caixa": name, "vb_cm3": round(vb, 2), "fc_hz": round(fc), "qtc": round(qtc, 2),
               "pico_db": round(float(level_db(np.array([fc]), fc, qtc)[0]), 1), "f3_hz": round(f3(fc, qtc)),
               "fc_faixa_hz": [round(lo[0]), round(hi[0])],
               "nivel_db": {str(int(x)): round(float(level_db(np.array([x]), fc, qtc)[0]), 1) for x in (196, 262, 392, 523, 784, 1047)}}
        out["caixas"].append(rec)
        ax.semilogx(f, level_db(f, fc, qtc), label="%s: fc %d Hz, Qtc %.1f" % (name, round(fc), qtc))
    ax.axvline(LOWEST_NOTE, color="gray", ls=":")
    ax.text(LOWEST_NOTE * 1.02, -38, "G3, a nota mais grave", color="gray", fontsize=8)
    ax.set_ylim(-40, 12)
    ax.set_xlabel("frequencia (Hz)")
    ax.set_ylabel("nivel em relacao aos medios (dB)")
    ax.set_title("Student V4 (R4V4): Dayton CE28MB-8 em caixa fechada (modelo de 2a ordem, alto-falante nominal)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "acustica.png"), dpi=130)
    a, b = out["caixas"][2], out["caixas"][0]
    v2 = out["caixas"][3]
    out["ganho_da_V3_sobre_a_V2_db"] = {k: round(b["nivel_db"][k] - v2["nivel_db"][k], 1) for k in a["nivel_db"]}
    out["ganho_da_caixa_em_L_sobre_a_v1_db"] = {k: round(b["nivel_db"][k] - a["nivel_db"][k], 1) for k in a["nivel_db"]}
    # the firmware's high-pass on the speaker (SPEC v2: ~300 Hz, taken here as 2nd order): what is left of each note
    hp = lambda fq: float(10 * np.log10((fq / 300.0) ** 4 / (1 + (fq / 300.0) ** 4)))
    out["corte_de_graves_300_hz_db"] = {k: round(hp(float(k)), 1) for k in a["nivel_db"]}
    json.dump(out, open(os.path.join(HERE, "acustica.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("Vas nominal %.1f cm3" % vas)
    for r in out["caixas"]:
        print("%-46s Vb %5.1f  fc %4d (%d-%d)  Qtc %.2f  pico %+.1f dB  F3 %4d  %s" % (
            r["caixa"], r["vb_cm3"], r["fc_hz"], r["fc_faixa_hz"][0], r["fc_faixa_hz"][1], r["qtc"], r["pico_db"], r["f3_hz"],
            r["nivel_db"]))
    print("L vs v1:", out["ganho_da_caixa_em_L_sobre_a_v1_db"])
    print("corte 300 Hz:", out["corte_de_graves_300_hz_db"])


if __name__ == "__main__":
    main()
