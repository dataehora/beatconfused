"""Student V4 (R10V4, item 5): microphone through J302 only, electret (plug-in power) and dynamic. Stdlib; writes pcb/mic_ganho.json.

    python etutti/hardware/student_v04/pcb/mic_ganho.py

Numbers from the SGTL5000 datasheet (NXP, Table 4: MIC input level 2.83 Vpp = 1.0 Vrms at 3.3 V VDDA, MIC input impedance 2.9 kohm typ;
Table 29: CHIP_MIC_CTRL; Table 6: ADC SNR 90 dB at -60 dB input) and from the boards (R305 = 0 ohm, C309 1 uF, C310 NOT fitted since R10V4).
ASSUMED (marked, not in the datasheet): the internal 2 k resistor's tolerance (+-20 %), the preamplifier's equivalent input noise
(EIN, 3 uV A-weighted is used as a pessimistic value), the electret's sensitivity (-44 dBV/Pa at 2.2 kohm) and its self noise (60 dB SNR re 94 dB SPL).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
VB = 3.0                                    # MIC_BIAS (BIAS_VOLT = 7), at most VDDA - 0.2 V
RB = {"min": 1600.0, "nom": 2000.0, "max": 2400.0}   # internal 2 k, +-20 % (assumption)
ZIN = 2900.0                                # SGTL5000 MIC input impedance, typical (Table 4)
FS = 1.0                                    # V rms at the ADC full scale (2.83 Vpp), total gain 0 dB
EIN = 3e-6                                  # V rms, A-weighted, assumed preamplifier noise (pessimistic)
KT4 = 1.656e-20                             # 4 k T at 300 K
BW = 13000.0                                # A-weighted 20 kHz ~ 13 kHz of equivalent noise bandwidth
out = {}


def db(x):
    return 20 * math.log10(x)


def par(a, b):
    return a * b / (a + b)


# ---- 1. DC point of the tip with the bias ON (MIC_DET reads it) --------------------------------------------------------------------
dyn = {}
for rc in (70, 150, 300, 600, 800):
    dyn[rc] = {k: round(VB * rc / (r + rc), 3) for k, r in RB.items()}
ele = {}
for i in (0.1, 0.3, 0.5, 1.0, 1.5):
    ele[i] = {k: round(max(VB - i * 1e-3 * r, 0.0), 3) for k, r in RB.items()}
out["tip_dc_dinamico_V"] = dyn
out["tip_dc_eletreto_V_(sem_piso_do_FET)"] = ele
# an electret's FET needs about 1 V across it to stay in saturation (assumption: below ~1 V it is a 1-3 kohm resistor): floor
out["piso_eletreto_V"] = round(VB * 1000.0 / (RB["max"] + 1000.0), 2)
out["dinamico_max_600ohm_V"] = dyn[600]["min"]
out["limiar_sugerido_V"] = [0.85, 0.95]
# ---- 2. bias current in a dynamic coil, by mistake -----------------------------------------------------------------------------------
out["corrente_bobina_mA"] = {rc: round(VB / (RB["nom"] + rc) * 1e3, 2) for rc in (150, 300, 600)}
out["potencia_bobina_mW"] = {rc: round((VB / (RB["nom"] + rc)) ** 2 * rc * 1e3, 3) for rc in (150, 300, 600)}
# ---- 3. signal loss through the bias resistor (bias ON): load = 2 k || 2.9 k, against 2.9 k with the bias OFF ----------------------------
loss = {}
for rc in (150, 300, 600):
    on = par(RB["nom"], ZIN)
    loss[rc] = {"bias_ligado_dB": round(db(on / (rc + on)), 2), "bias_desligado_dB": round(db(ZIN / (rc + ZIN)), 2)}
out["perda_de_sinal_dinamico_dB"] = loss
# ---- 4. C310 = 100 nF at the tip (R305 = 0): the electret and the coil seen through it ----------------------------------------------
c = 100e-9
resp = {}
for f in (1000, 4000, 10000):
    xc = 1 / (2 * math.pi * f * c)
    zc = complex(0, -xc)
    zl_lf = par(par(RB["nom"], ZIN), 1e9)           # no capacitor
    # current source (electret): the load impedance magnitude
    zl = 1 / (1 / RB["nom"] + 1 / ZIN + 1 / zc)
    row = {"eletreto_dB": round(db(abs(zl) / zl_lf), 1)}
    for rc in (150, 300, 600):
        zt = 1 / (1 / RB["nom"] + 1 / ZIN + 1 / zc)
        row["dinamico_%d_dB" % rc] = round(db(abs(zt / (rc + zt)) / (zl_lf / (rc + zl_lf))), 1)
    resp[f] = row
out["C310_100nF_resposta_dB"] = resp
out["C310_corte_eletreto_Hz"] = round(1 / (2 * math.pi * par(RB["nom"], ZIN) * c))
# ---- 5. levels and SNR ---------------------------------------------------------------------------------------------------------------
SPL = (90, 100, 105, 114, 120)                       # singing at 1-3 cm (the 105 is the firmware's nominal), 90 = soft speech
mics = {"dinamico 0,45 mV/Pa (WH20-tipo, 150 ohm)": (0.45e-3, 150, "dyn"),
        "dinamico 1,7 mV/Pa (PRO 8HEx-tipo, 600 ohm)": (1.7e-3, 600, "dyn"),
        "eletreto comum -44 dBV/Pa (6,3 mV/Pa a 2,2 k)": (6.3e-3, 0, "ele")}
tab = {}
for name, (s, rc, kind) in mics.items():
    rows = {}
    # loading: the capsule is rated at 2.2 k; here 2 k || 2.9 k = 1.18 k (bias ON, C310 not fitted)
    adj = db(par(RB["nom"], ZIN) / 2200.0) if kind == "ele" else (loss[rc]["bias_ligado_dB"] if rc in loss else 0)
    sens = s * 10 ** (adj / 20)
    for spl in SPL:
        p = 10 ** ((spl - 94) / 20)
        v = sens * p
        # gain to put this level at -18 dBFS rms, rounded to the codec's steps (preamp 0/20/30/40 + ADC 0..22.5 dB in 1.5 dB steps)
        need = db(FS * 10 ** (-18 / 20) / v)
        pre = max([g for g in (0, 20, 30, 40) if g <= need] or [0])
        adc = min(max(round((need - pre) / 1.5) * 1.5, 0.0), 22.5)
        g = pre + adc
        # noise at the input: coil thermal + (electret self noise) + preamp EIN + ADC (90 dB below FS, referred to the input by the gain)
        th = math.sqrt(KT4 * rc * BW) if kind == "dyn" else 0.0
        selfn = sens * 10 ** (-60 / 20) if kind == "ele" else 0.0     # 60 dB SNR re 94 dB SPL = 1 Pa
        adcn = FS * 10 ** (-90 / 20) / 10 ** (g / 20)
        n_ideal = math.sqrt(th ** 2 + selfn ** 2 + adcn ** 2)
        n_real = math.sqrt(n_ideal ** 2 + EIN ** 2)
        full = db(v * 10 ** (62.5 / 20) / FS)
        rows[spl] = {"mV_rms": round(v * 1e3, 2), "ganho_p_-18dBFS_dB": round(need, 1), "ganho_escolhido_dB": g,
                     "dBFS_com_o_ganho_escolhido": round(db(v * 10 ** (g / 20) / FS), 1),
                     "SNR_dB_ideal": round(db(v / n_ideal), 1), "SNR_dB_com_EIN_3uV": round(db(v / n_real), 1),
                     "dBFS_ganho_max_62,5": round(full, 1)}
    tab[name] = {"sensibilidade_efetiva_mV_Pa": round(sens * 1e3, 3), "linhas": rows}
out["niveis"] = tab
out["fundo_de_escala_no_ganho_max_uV"] = round(FS / 10 ** (62.5 / 20) * 1e6, 0)
json.dump(out, open(os.path.join(HERE, "mic_ganho.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
