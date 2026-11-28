"""Liebling (R3MIC) F1: roda todas as medicoes e escreve out/*.png e out/resultados.json.

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe minimic/firmware/sim/run_f1.py [grupo ...]

Grupos: resp ruido dist alias sat ganho medidor cpu arranque (sem argumento = todos).
"""
import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import signal

sys.path.insert(0, os.path.dirname(__file__))
import pdm
import chain as C
from pdm import FCLK, FS, spl_to_amp, a_weight_db

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
RES_PATH = os.path.join(OUT, "resultados.json")
RES = json.load(open(RES_PATH)) if os.path.exists(RES_PATH) else {}
FULL = C.FULL
OSR = FCLK // FS
M = 65536
SETTLE = 16384
BIN = FS / M

plt.rcParams.update({
    "figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})
COL = {"a": "#2a6fb0", "b": "#d9622b", "c": "#3a9a5b", "d": "#7a4aa8", "k": "#333333"}
CHAIN = C.Chain()


def save():
    json.dump(RES, open(RES_PATH, "w"), indent=1, default=float)


def fig_save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)


def dbf(x):
    return 20 * np.log10(np.maximum(x, 1e-30))


def run_chain(acoustic, dcs=(-1e-4, -1e-4), noise=False, hpf=False, clip=False, seeds=(1, 2),
              order=5, obg=1.3, chain=None, dc_block=True):
    chain = chain or CHAIN
    bA = pdm.pdm_of(acoustic, dcs[0], noise, hpf, clip, seeds[0], order, obg)
    bB = pdm.pdm_of(acoustic, dcs[1], noise, hpf, clip, seeds[1], order, obg)
    y = chain.decimate(bA, bB)
    return chain.dc(y) if dc_block else y


def sine_fit(y, f, fs=FS):
    t = np.arange(y.size) / fs
    X = np.stack([np.sin(2 * np.pi * f * t), np.cos(2 * np.pi * f * t), np.ones_like(t), t / t[-1]], 1)
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    return np.hypot(c[0], c[1])


def coh_bin(f):
    return int(round(f / BIN))


def coh_signal(bins, amps_acoustic, nout):
    n = nout * OSR
    t = np.arange(n) / FCLK
    x = np.zeros(n)
    for k, a in zip(bins, amps_acoustic):
        x += a * np.sin(2 * np.pi * (k * BIN) * t + 0.3 * k)
    return x


def coh_run(bins, amps, **kw):
    nout = M + SETTLE + 64
    x = coh_signal(bins, amps, nout)
    z = run_chain(x, **kw)
    return z[SETTLE:SETTLE + M, :] / FULL


WIN = signal.windows.blackmanharris(M, sym=False)
WSUM = WIN.sum()


def spectrum_amp(z):
    """amplitude de pico por bin (dBFS de seno)."""
    S = np.abs(np.fft.rfft(z * WIN)) * 2 / WSUM
    return S


def metrics(z, bins, f_lo=20.0, f_hi=20000.0):
    S = spectrum_amp(z)
    mask = np.ones(S.size, dtype=bool)
    mask[:coh_bin(f_lo)] = False
    mask[coh_bin(f_hi):] = False
    tone_p = 0.0
    for k in bins:
        lo, hi = max(k - 4, 0), k + 5
        tone_p += np.sum(S[lo:hi] ** 2)
        mask[lo:hi] = False
    # soma de potencia -> como a janela BH tem ENBW 2.0 bins, normalizamos por ENBW
    enbw = M * np.sum(WIN ** 2) / WSUM ** 2
    resid_p = np.sum(S[mask] ** 2) / enbw
    return {"thdn_db": 10 * np.log10(resid_p / tone_p), "S": S, "tone_p": tone_p, "resid_p": resid_p}


# ======================================================================= resposta
def g_resp():
    print("[resp]")
    freqs = np.unique(np.round(np.concatenate([
        [10, 12, 14, 15, 16, 18, 20, 25, 30, 35, 41, 50, 63, 80, 100, 160, 250, 400, 630, 1000, 1600,
         2500, 4000, 6300, 8000, 10000, 12500, 14000, 16000, 18000, 20000, 22000, 24000]]), 3))
    amp = 0.05
    out = {"f": [], "chain_db": [], "sens_chain_db": []}
    for f in freqs:
        dur = max(0.9, 14.0 / f + 0.45)
        nout = int(dur * FS)
        t = np.arange(nout * OSR) / FCLK
        x = amp * np.sin(2 * np.pi * f * t + 0.5)
        for tag, hpf in (("chain_db", False), ("sens_chain_db", True)):
            z = run_chain(x, hpf=hpf)
            s0 = int(0.45 * FS)
            a = sine_fit(z[s0:, 0] / FULL, f)
            out[tag].append(dbf(a / amp))
        out["f"].append(f)
        print("  %7.1f Hz  chain %+7.3f dB  sensor+chain %+7.3f" % (f, out["chain_db"][-1], out["sens_chain_db"][-1]))
    f = np.array(out["f"])
    ch = np.array(out["chain_db"])
    sc = np.array(out["sens_chain_db"])
    ref = np.interp(1000, f, ch)
    ch_n = ch - ref
    sc_n = sc - ref
    # -3 dB (interpolacao em log f nas baixas)
    def f3(curve):
        sel = f <= 100
        lf = np.log10(f[sel])
        c = curve[sel]
        return float(10 ** np.interp(-3.0, c, lf))
    # ripple 100 Hz..16 kHz
    sel = (f >= 100) & (f <= 16000)
    RES["resp"] = {
        "f": f.tolist(), "chain_db": ch_n.tolist(), "sensor_chain_db": sc_n.tolist(),
        "ref_1k_db": float(ref),
        "f3_chain_hz": f3(ch_n), "f3_sensor_chain_hz": f3(sc_n),
        "ripple_chain_100_16k_db": [float(ch_n[sel].min()), float(ch_n[sel].max())],
        "ripple_sensor_chain_100_16k_db": [float(sc_n[sel].min()), float(sc_n[sel].max())],
        "at_16k_db": float(np.interp(16000, f, ch_n)), "at_20k_db": float(np.interp(20000, f, ch_n)),
        "at_41_db": float(np.interp(41, f, sc_n)), "at_15_db": float(np.interp(15, f, sc_n)),
        "at_10_db": float(np.interp(10, f, sc_n)),
    }
    # analitico (cada estagio, para o grafico fino)
    fa = np.logspace(np.log10(5), np.log10(24000), 600)
    sens1 = -10 * np.log10(1 + (11.0 / fa) ** 2)
    dcr = C.dc_response_db(fa)
    RES["resp"]["analytic_f3_dc_only_hz"] = float(np.interp(-3, dcr, fa))
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 6.5))
    ax[0].semilogx(f, ch_n, "o-", color=COL["a"], ms=3, label="cadeia digital (medida, PDM -> 48 kHz)")
    ax[0].semilogx(f, sc_n, "s-", color=COL["b"], ms=3, label="sensor (1a ordem 11 Hz, hipotese) + cadeia")
    ax[0].semilogx(fa, dcr, "--", color=COL["k"], lw=0.8, label="so o bloqueio de DC (analitico)")
    ax[0].axhline(-3, color="gray", lw=0.7)
    ax[0].axvline(15, color="gray", ls=":", lw=0.8)
    ax[0].text(15.5, -12, "15 Hz (meta)", fontsize=8)
    ax[0].set_xlim(8, 25000)
    ax[0].set_ylim(-14, 2)
    ax[0].set_ylabel("ganho (dB, 0 em 1 kHz)")
    ax[0].set_title("Resposta em frequencia, 10 Hz a 24 kHz")
    ax[0].legend(loc="lower right", fontsize=8)
    ax[1].semilogx(f, ch_n, "o-", color=COL["a"], ms=3, label="cadeia digital")
    ax[1].semilogx(f, sc_n, "s-", color=COL["b"], ms=3, label="sensor + cadeia")
    ax[1].axhspan(-0.5, 0.5, color=COL["c"], alpha=0.12, label="+-0.5 dB")
    ax[1].set_xlim(80, 25000)
    ax[1].set_ylim(-1.2, 1.2)
    ax[1].set_xlabel("frequencia (Hz)")
    ax[1].set_ylabel("ganho (dB)")
    ax[1].set_title("Detalhe da ondulacao (meta: < 0.5 dB ate 16 kHz)")
    ax[1].legend(fontsize=8)
    fig_save(fig, "resposta_frequencia.png")
    save()


# ======================================================================= ruido
def noise_psd(z):
    f, P = signal.welch(z, fs=FS, window="hann", nperseg=16384, noverlap=8192)
    return f, P          # P em (FS_amp^2)/Hz


def noise_levels(z):
    f, P = noise_psd(z)
    df = f[1] - f[0]
    sel = (f >= 20) & (f <= 20000)
    unw = np.sqrt(np.sum(P[sel]) * df)
    w = 10 ** (a_weight_db(f) / 20)
    aw = np.sqrt(np.sum(P[sel] * w[sel] ** 2) * df)
    return dbf(unw), dbf(aw), f, P


def g_ruido():
    print("[ruido]")
    dur = 2.4
    nout = int(dur * FS)
    x = np.zeros(nout * OSR)
    res = {}
    cases = {
        "ideal_sinc5": dict(noise=False, chain=CHAIN),
        "mic_sinc5": dict(noise=True, chain=CHAIN),
        "ideal_sinc4": dict(noise=False, chain=C.Chain(N=4)),
        "mic_sinc4": dict(noise=True, chain=C.Chain(N=4)),
        "ideal_sinc5_mod4": dict(noise=False, chain=CHAIN, order=4, obg=1.5),
        "ideal_sinc4_mod4": dict(noise=False, chain=C.Chain(N=4), order=4, obg=1.5),
    }
    spec = {}
    for name, kw in cases.items():
        kw = dict(kw)
        ch = kw.pop("chain")
        order = kw.pop("order", 5)
        obg = kw.pop("obg", 1.3)
        bA = pdm.pdm_of(x, -1e-4, kw["noise"], False, False, 1, order, obg)
        bB = pdm.pdm_of(x, -1e-4, kw["noise"], False, False, 2, order, obg)
        z = ch.dc(ch.decimate(bA, bB))
        zz = z[int(0.5 * FS):, 0] / FULL
        u, a, f, P = noise_levels(zz)
        # referencia "parede de tijolo": mesma sequencia de bits, banda 20-20k exata (Welch a 3.072 MHz)
        v = (2.0 * bA[int(0.5 * FCLK):] - 1.0)
        fb, Pb = signal.welch(v, fs=FCLK, window="hann", nperseg=1 << 17, noverlap=1 << 16)
        df = fb[1] - fb[0]
        sel = (fb >= 20) & (fb <= 20000)
        wA = 10 ** (a_weight_db(fb) / 20)
        ub = dbf(np.sqrt(np.sum(Pb[sel]) * df))
        ab = dbf(np.sqrt(np.sum(Pb[sel] * wA[sel] ** 2) * df))
        res[name] = {"unweighted_dbfs": float(u), "a_weighted_dbfs": float(a),
                     "brickwall_unweighted_dbfs": float(ub), "brickwall_a_dbfs": float(ab),
                     "excesso_a_db": float(a - ab), "excesso_unw_db": float(u - ub)}
        spec[name] = (f, P)
        print("  %-18s 20-20k: %7.2f dBFS  A: %7.2f   | brickwall %7.2f / %7.2f | excesso A %+.2f dB" % (name, u, a, ub, ab, a - ab))
    # referencia teorica do sensor (ficha): A-ponderado = -110.5 dBFS (ref. amplitude 1)
    sig_rms = 10 ** (pdm.SENS_DBFS / 20) / np.sqrt(2)
    target_a = dbf(sig_rms / 10 ** (pdm.SNR_A / 20))
    res["alvo_ficha_a_dbfs"] = float(target_a)
    res["snr_a_chain_total_db"] = float(dbf(sig_rms) - res["mic_sinc5"]["a_weighted_dbfs"])
    res["penalidade_ruido_db"] = float(res["mic_sinc5"]["a_weighted_dbfs"] - target_a)
    # SNR do caminho digital (ideal): seno de 94 dB SPL contra ruido do caminho
    res["snr_a_caminho_digital_db"] = float(dbf(sig_rms) - res["ideal_sinc5"]["a_weighted_dbfs"])
    # contra um seno de fundo de escala (rms = -3.01 dBFS)
    res["faixa_dinamica_caminho_db"] = float(-3.01 - res["ideal_sinc5"]["unweighted_dbfs"])
    RES["ruido"] = res
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for name, c, lab in (("mic_sinc5", COL["b"], "sensor sintetico (SNR 71.5 dB(A)) + cadeia sinc^5"),
                         ("ideal_sinc5", COL["a"], "caminho digital sozinho (modulador ideal), sinc^5"),
                         ("ideal_sinc4", COL["c"], "caminho digital sozinho, sinc^4")):
        f, P = spec[name]
        ax.semilogx(f[1:], 10 * np.log10(P[1:] * 1.0), color=c, lw=0.9, label=lab)
    fx = np.logspace(1, np.log10(24000), 200)
    s2 = pdm.white_sigma_for_snr_a() ** 2 / (FCLK / 2)
    ax.axhline(10 * np.log10(s2), color=COL["k"], ls="--", lw=0.8, label="ruido branco do sensor modelado")
    ax.set_xlim(10, 24000)
    ax.set_xlabel("frequencia (Hz)")
    ax.set_ylabel("densidade (dBFS^2/Hz)")
    ax.set_title("Ruido de fundo na saida de 48 kHz (entrada silenciosa)")
    ax.legend(fontsize=7, loc="upper right")
    fig_save(fig, "ruido.png")
    save()


# ======================================================================= distorcao
def g_dist():
    print("[dist]")
    res = {}
    cases = [
        ("41 Hz  -6 dBFS", [41.0], [10 ** (-6 / 20)]),
        ("41 Hz -26 dBFS", [41.0], [10 ** (-26 / 20)]),
        ("1 kHz  -6 dBFS", [1000.0], [10 ** (-6 / 20)]),
        ("1 kHz -26 dBFS", [1000.0], [10 ** (-26 / 20)]),
        ("1 kHz -36 dBFS (94 dB SPL)", [1000.0], [10 ** (-36 / 20)]),
        ("acorde La menor + E1", [41.2, 110.0, 130.81, 164.81, 261.63], [10 ** (-20 / 20)] * 5),
        ("acorde forte (5 x -18 dBFS) + 1 kHz", [41.2, 110.0, 164.81, 261.63, 1000.0], [10 ** (-18 / 20)] * 5),
    ]
    fig, axs = plt.subplots(3, 2, figsize=(9, 8))
    axs = axs.ravel()
    ip = 0
    for name, fr, am in cases:
        bins = [coh_bin(f) for f in fr]
        z = coh_run(bins, am)
        mA = metrics(z[:, 0], bins)
        mB = metrics(z[:, 1], bins)
        S = mA["S"]
        # harmonicas (so tom unico)
        hd = None
        if len(bins) == 1:
            k = bins[0]
            hd = {}
            for h in range(2, 6):
                if h * k < S.size - 5 and h * k * BIN < 20000:
                    hd["HD%d" % h] = float(dbf(S[h * k - 2:h * k + 3].max()) - dbf(S[k - 2:k + 3].max()))
        res[name] = {"thdn_db": float(mA["thdn_db"]), "thdn_db_B": float(mB["thdn_db"]),
                     "hd": hd, "level_dbfs_each": float(dbf(am[0]))}
        print("  %-40s THD+N(A) %7.2f dB  (B) %7.2f dB  %s" % (name, mA["thdn_db"], mB["thdn_db"], hd))
        if ip < 6:
            a = axs[ip]
            f = np.arange(S.size) * BIN
            a.semilogx(f[1:], dbf(S[1:]), color=COL["a"], lw=0.7)
            a.set_xlim(10, 24000)
            a.set_ylim(-160, 0)
            a.set_title(name + "   THD+N %.1f dB" % mA["thdn_db"], fontsize=8)
            a.set_xlabel("Hz")
            a.set_ylabel("dBFS")
            ip += 1
    RES["dist"] = res
    fig_save(fig, "distorcao.png")
    save()


# ======================================================================= alias
def hb_resp(q, fs_in, f, qb=None):
    qb = C.Chain.QB if qb is None else qb
    w = 2 * np.pi * np.asarray(f) / fs_in
    n = np.arange(len(q)) - (len(q) - 1) // 2
    H = np.zeros(np.shape(f), dtype=complex)
    for i, c in zip(n, q):
        H += c * np.exp(-1j * w * i)
    return np.abs(H) / (1 << qb)


def total_resp_db(chain, f):
    f = np.asarray(f, dtype=float)
    s = 10 ** (C.sinc_response_db(f, chain.N, chain.R) / 20)
    h2 = hb_resp(chain.hb2[1], chain.fs1, f)
    h3 = hb_resp(chain.hb3[1], chain.fs1 // 2, f)
    hc = hb_resp(chain.comp, FS, f, 15) if chain.comp is not None else 1.0
    return dbf(s * h2 * h3 * hc)


def g_alias():
    print("[alias]")
    res = {"pontos": []}
    freqs = [26000, 28000, 30000, 32000, 36000, 37500, 40000, 44000, 47000, 52000, 60000, 72000,
             76000, 90000, 100000, 150000, 180000, 190000, 194000, 200000, 250000, 372000, 380000,
             388000, 396000, 570000, 760000, 1000000, 1400000]
    amp = 0.3
    for f in freqs:
        k = coh_bin(f)
        fb = k * BIN
        # alias: freq de saida = |fb - round(fb/48000)*48000|
        fal = abs(fb - round(fb / FS) * FS)
        kal = coh_bin(fal)
        z = coh_run([k], [amp], hpf=False, clip=False)
        S = spectrum_amp(z[:, 0])
        a = S[max(kal - 2, 0):kal + 3].max() if kal > 4 else float('nan')
        rej = dbf(a / amp)
        res["pontos"].append({"f_in": fb, "f_alias": fal, "rejeicao_db": float(rej)})
        print("  in %9.0f Hz -> alias %7.0f Hz : %7.1f dB" % (fb, fal, rej))
    fa = np.linspace(0, 1.536e6, 60000)
    fa[0] = 1.0
    H = total_resp_db(CHAIN, fa)
    # pior caso: banda que cai em 0..20 kHz por dobra (f tal que |f - kFS| <= 20k, k>=1)
    folded = np.abs(fa - np.round(fa / FS) * FS)
    bad = (np.round(fa / FS) >= 1) & (folded <= 20000)
    res["pior_banda_alias_analitica_db"] = float(H[bad].max())
    # pior caso acima de 28 kHz ate 192k+-: so a banda de transicao mais proxima
    bad2 = bad & (fa >= 28000) & (fa < 96000 - 28000)
    res["pior_alias_28k_68k_db"] = float(H[bad2].max())
    bad3 = bad & (fa >= 68000)
    res["pior_alias_acima_68k_db"] = float(H[bad3].max())
    # tabela do sinc4 para comparar
    c4 = C.Chain(N=4)
    H4 = total_resp_db(c4, fa)
    res["pior_alias_acima_68k_sinc4_db"] = float(H4[bad3].max())
    res["hb_stop_ideal_db"] = {
        "hb2": float(dbf(hb_resp(CHAIN.hb2[0] * (1 << C.Chain.QB), CHAIN.fs1, np.linspace(76000, 96000, 500)).max())),
        "hb2_Q": float(dbf(hb_resp(CHAIN.hb2[1], CHAIN.fs1, np.linspace(76000, 96000, 500)).max())),
        "hb3": float(dbf(hb_resp(CHAIN.hb3[0] * (1 << C.Chain.QB), CHAIN.fs1 // 2, np.linspace(28000, 48000, 500)).max())),
        "hb3_Q": float(dbf(hb_resp(CHAIN.hb3[1], CHAIN.fs1 // 2, np.linspace(28000, 48000, 500)).max())),
    }
    for nm, st in (("hb2", CHAIN.hb2), ("hb3", CHAIN.hb3)):
        q = st[1]
        sa = int(np.abs(q).sum())
        res[nm + "_info"] = {"taps": int(len(q)), "pares_nao_nulos": int(((len(q) - 1) // 2 + 1) // 2),
                              "soma_abs_coef": sa / (1 << C.Chain.QB),
                              "bits_acum_hi": float(np.log2((1 << 11) * sa)), "bits_acum_lo": float(np.log2((1 << 12) * sa)),
                              "coef_max_bits": int(np.ceil(np.log2(np.abs(q).max()))) + 1}
    RES["alias"] = res
    fig, ax = plt.subplots(2, 1, figsize=(8, 7))
    ax[0].plot(fa / 1e3, H, color=COL["a"], lw=0.8, label="cadeia inteira (analitico), sinc^5")
    ax[0].plot(fa / 1e3, H4, color=COL["c"], lw=0.6, alpha=0.7, label="com sinc^4")
    pts = res["pontos"]
    ax[0].plot([p["f_in"] / 1e3 for p in pts], [p["rejeicao_db"] for p in pts], "o", color=COL["b"], ms=4,
               label="medido: tom em f_in, nivel na frequencia dobrada")
    ax[0].set_xscale("log")
    ax[0].set_xlim(1, 1536)
    ax[0].set_ylim(-160, 5)
    ax[0].set_xlabel("frequencia de entrada (kHz)")
    ax[0].set_ylabel("dB")
    ax[0].set_title("Resposta total e rejeicao de aliasing (PDM 3.072 MHz -> 48 kHz)")
    ax[0].legend(fontsize=8)
    z = np.linspace(0, 120000, 6000)
    z[0] = 1
    ax[1].plot(z / 1e3, total_resp_db(CHAIN, z), color=COL["a"])
    ax[1].axvspan(28, 76, color=COL["b"], alpha=0.08)
    ax[1].set_xlim(0, 120)
    ax[1].set_ylim(-160, 5)
    ax[1].set_xlabel("frequencia (kHz)")
    ax[1].set_ylabel("dB")
    ax[1].set_title("Zoom 0-120 kHz (faixa sombreada: dobra para a banda de audio, 28-76 kHz)")
    fig_save(fig, "alias.png")
    save()


# ======================================================================= saturacao
def g_sat():
    print("[sat]")
    res = {"sensor": [], "ganho": []}
    k = coh_bin(1000.0)
    spls = [110, 120, 124, 125, 126, 127, 127.5, 128, 129, 130, 132, 134]
    for spl in spls:
        a = float(spl_to_amp(spl))
        z = coh_run([k], [a], hpf=True, clip=True, noise=False)
        S = spectrum_amp(z[:, 0])
        f1 = S[k - 2:k + 3].max()
        h = np.sqrt(sum(S[h * k - 2:h * k + 3].max() ** 2 for h in range(2, 6)))
        peak = np.abs(z[:, 0]).max()
        zi = (z[:, 0] * FULL)
        pre = np.abs(zi).max()
        flag = pre >= C.SENSOR_THR
        res["sensor"].append({"spl": spl, "saida_dbfs_fund": float(dbf(f1)), "pico_dbfs": float(dbf(peak)),
                              "thd_pct": float(100 * h / f1), "flag_SAT": bool(flag)})
        print("  %6.1f dB SPL: fund %6.2f dBFS pico %6.2f THD %6.2f %%  SAT %s" % (spl, dbf(f1), dbf(peak), 100 * h / f1, flag))
    # saturacao por ganho: tom de 1 kHz a -30 dBFS (100 dB SPL) apos DC block
    amp = 10 ** (-30 / 20)
    nn = 48000
    t = np.arange(nn) / FS
    x = np.round(amp * np.sin(2 * np.pi * 1000 * t) * FULL).astype(np.int64)
    xs = np.stack([x, x], 1)
    for gi in range(0, C.GAIN_N, 2):
        y, g, cl = C.apply_gain(xs, np.full(nn, C.GAIN_TAB[gi], dtype=np.int64), C.GAIN_TAB[gi])
        peak = np.abs(y[:, 0]).max() / FULL
        clipped = bool(cl.any())
        res["ganho"].append({"ganho_db": 1.5 * gi, "pico_dbfs": float(dbf(peak)), "corte": clipped,
                             "pico_teorico_dbfs": -30 + 1.5 * gi})
    RES["sat"] = res
    sp = res["sensor"]
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.8))
    ax[0].plot([s["spl"] for s in sp], [s["pico_dbfs"] for s in sp], "o-", color=COL["a"], label="pico da saida (dBFS)")
    ax[0].plot([s["spl"] for s in sp], [s["spl"] - 130 for s in sp], "--", color="gray", label="ideal (SPL - 130)")
    ax[0].axhline(20 * np.log10(C.SENSOR_THR / FULL), color=COL["b"], lw=0.8)
    ax[0].text(110, 20 * np.log10(C.SENSOR_THR / FULL) + 0.6, "limiar SAT do sensor", color=COL["b"], fontsize=8)
    a2 = ax[0].twinx()
    a2.plot([s["spl"] for s in sp], [s["thd_pct"] for s in sp], "s-", color=COL["d"], ms=3)
    a2.set_ylabel("THD (%)", color=COL["d"])
    a2.set_yscale("log")
    a2.grid(False)
    ax[0].set_xlabel("nivel acustico (dB SPL, 1 kHz)")
    ax[0].set_ylabel("dBFS")
    ax[0].set_title("Sensor simulado (soft-clip ajustado a 10 % THD em 128 dB SPL)")
    ax[0].legend(fontsize=7, loc="lower right")
    gg = res["ganho"]
    ax[1].plot([g["ganho_db"] for g in gg], [g["pico_dbfs"] for g in gg], "o-", color=COL["a"], label="pico medido")
    ax[1].plot([g["ganho_db"] for g in gg], [g["pico_teorico_dbfs"] for g in gg], "--", color="gray", label="sem corte")
    ax[1].axhline(0, color=COL["b"], lw=0.8)
    ax[1].set_xlabel("ganho (dB), entrada 1 kHz a -30 dBFS")
    ax[1].set_ylabel("pico de saida (dBFS)")
    ax[1].set_title("Saturacao do ganho (clamp em 24 bits, sem volta)")
    ax[1].legend(fontsize=8)
    fig_save(fig, "saturacao.png")
    save()


# ======================================================================= ganho
def g_ganho():
    print("[ganho]")
    res = {}
    nn = 24000
    t = np.arange(nn) / FS
    amp = 10 ** (-60 / 20)
    x = np.round(amp * np.sin(2 * np.pi * 1000 * t) * FULL).astype(np.int64)
    xs = np.stack([x, x], 1)
    errs = []
    for gi in range(C.GAIN_N):
        y, g, cl = C.apply_gain(xs, np.full(nn, C.GAIN_TAB[gi], dtype=np.int64), C.GAIN_TAB[gi])
        a = sine_fit(y[2000:, 0] / FULL, 1000.0)
        errs.append(dbf(a / amp) - 1.5 * gi)
    res["erro_degrau_db"] = [float(e) for e in errs]
    res["erro_max_db"] = float(np.abs(errs).max())
    print("  erro maximo de ganho %.4f dB" % res["erro_max_db"])
    # clique: 1 kHz a -30 dBFS, degrau 0 -> 1.5 dB em t=0.2 s ; e 0 -> 42 dB com -60 dBFS
    def click(gi_from, gi_to, amp_db, shift):
        n = FS // 2
        t = np.arange(n) / FS
        a = 10 ** (amp_db / 20)
        xx = np.round(a * np.sin(2 * np.pi * 1000 * t) * FULL).astype(np.int64)
        xs = np.stack([xx, xx], 1)
        tgt = np.full(n, C.GAIN_TAB[gi_to], dtype=np.int64)
        tgt[:FS // 5] = C.GAIN_TAB[gi_from]
        if shift is None:    # degrau seco
            g = tgt.copy()
            y = (xs * g[:, None] + (1 << 23)) >> 24
        else:
            y, g, cl = C.apply_gain(xs, tgt, C.GAIN_TAB[gi_from], shift)
        return t, y[:, 0] / FULL, g / (1 << 24)
    out = {}
    for name, (g0, g1, adb) in {"1.5 dB": (0, 1, -30), "+42 dB": (0, 28, -60), "-1.5 dB": (10, 9, -30)}.items():
        _, y_seco, gs_seco = click(g0, g1, adb, None)
        t, y_ram, gs_ram = click(g0, g1, adb, 9)
        # banda lateral: espectro de 40 ms em volta do degrau, fora de +-300 Hz da portadora
        def side(y):
            seg = y[int(0.19 * FS):int(0.19 * FS) + 4096]
            S = np.abs(np.fft.rfft(seg * np.hanning(seg.size)))
            f = np.fft.rfftfreq(seg.size, 1 / FS)
            car = S[np.abs(f - 1000) < 60].max()
            far = S[(np.abs(f - 1000) > 300) & (f < 20000)].max()
            return dbf(far / car)
        out[name] = {"banda_lateral_seco_db": float(side(y_seco)), "banda_lateral_rampa_db": float(side(y_ram)),
                     "max_dg_por_amostra_rampa": float(np.abs(np.diff(gs_ram)).max() / gs_ram.max()),
                     "max_dg_por_amostra_seco": float(np.abs(np.diff(gs_seco)).max() / gs_seco.max()),
                     "tempo_ate_99pct_ms": float(1000 * (np.argmax(np.abs(gs_ram - gs_ram[-1]) < 0.01 * gs_ram[-1]
                                                                   * (np.arange(gs_ram.size) > FS // 5)
                                                                   ) - FS // 5) / FS)}
        # tempo de acomodacao: primeira amostra apos o degrau em que |g - alvo| < 1 %
        idx = np.where((np.abs(gs_ram - gs_ram[-1]) < 0.01 * gs_ram[-1]) & (np.arange(gs_ram.size) >= FS // 5))[0]
        out[name]["tempo_ate_99pct_ms"] = float(1000 * (idx[0] - FS // 5) / FS)
        print("  %-8s banda lateral: seco %.1f dB, rampa %.1f dB, acomoda %.1f ms" % (
            name, out[name]["banda_lateral_seco_db"], out[name]["banda_lateral_rampa_db"], out[name]["tempo_ate_99pct_ms"]))
        if name == "1.5 dB":
            wave = (t, y_seco, y_ram)
    res["degraus"] = out
    RES["ganho"] = res
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    ax[0].plot(np.arange(C.GAIN_N) * 1.5, errs, "o-", color=COL["a"], ms=3)
    ax[0].set_xlabel("ganho nominal (dB)")
    ax[0].set_ylabel("erro (dB)")
    ax[0].set_title("Erro do ganho (29 degraus)")
    t, ys, yr = wave
    s = slice(int(0.195 * FS), int(0.225 * FS))
    ax[1].plot(t[s] * 1e3, ys[s], color=COL["b"], lw=0.8, label="degrau seco")
    ax[1].plot(t[s] * 1e3, yr[s], color=COL["a"], lw=0.8, label="rampa (tau = 10.7 ms)")
    ax[1].set_xlabel("ms")
    ax[1].set_title("1 kHz a -30 dBFS, +1.5 dB em t = 200 ms")
    ax[1].legend(fontsize=7)
    _, y1, g1 = click(0, 28, -60, 9)
    ax[2].plot(np.arange(g1.size)[: FS // 2] / FS * 1e3, 20 * np.log10(g1), color=COL["a"])
    ax[2].set_xlabel("ms")
    ax[2].set_ylabel("ganho (dB)")
    ax[2].set_title("Salto 0 -> +42 dB")
    ax[2].set_xlim(190, 400)
    fig_save(fig, "ganho.png")
    save()


# ======================================================================= medidor
def tone_int(freq, db, n, phase=0.0):
    t = np.arange(n) / FS
    return np.round(10 ** (db / 20) * np.sin(2 * np.pi * freq * t + phase) * C.MAXOUT).astype(np.int64)


def g_medidor():
    print("[medidor]")
    res = {}
    # linearidade: pico de seno de x dB -> primeiro LED aceso, varredura fina
    lin = {}
    for freq in (1000.0, 8000.0, 16000.0):
        thr_meas = []
        for k, thr in enumerate(C.METER_DB):
            worst = None
            for ph in np.linspace(0.0, 2 * np.pi, 9)[:-1]:
                found = None
                for lvl in np.arange(thr - 4.0, min(thr + 4.0, 0.0 if k < 10 else 3.0), 0.05):
                    x = np.minimum(tone_int(freq, lvl, 480, ph), C.MAXOUT)
                    yy = np.stack([x, x], 1)
                    leds = C.run_meter(yy, np.zeros_like(yy), np.zeros(480, dtype=np.uint8))
                    if leds[:, k].any():
                        found = lvl
                        break
                if found is not None and (worst is None or found > worst):
                    worst = found
            thr_meas.append(worst)
        lin[str(int(freq))] = [None if t is None else float(t) for t in thr_meas]
        print("  %6.0f Hz: erro de limiar, pior fase (dB) %s" % (freq, [None if m is None else round(float(m - d), 2) for m, d in zip(thr_meas, C.METER_DB)]))
    res["limiar_medido_db"] = lin
    # ataque: um impulso de -10 dBFS
    x = np.zeros((480, 2), dtype=np.int64)
    x[100, 0] = int(C.MAXOUT * 10 ** (-10 / 20))
    L = C.run_meter(x, x, np.zeros(480, dtype=np.uint8))
    res["ataque_ms_ate_acender"] = int(np.argmax(L[:, 5])) - 100 // 48     # bloco do impulso = 2
    res["ataque_leds_acesos"] = int(L[2, :11].sum())
    # queda: um pico de 0 dBFS (um bloco) e silencio; instante em que cada LED apaga
    n = FS * 4
    x = np.zeros((n, 2), dtype=np.int64)
    x[10, 1] = C.MAXOUT
    L = C.run_meter(x, x, np.zeros(n, dtype=np.uint8))
    off = []
    for k in range(10):                   # sem SAT: so ate -3
        idx = np.where(~L[:, k])[0]
        idx = idx[idx > 2]
        off.append(float(idx[0]) if idx.size else float('nan'))
    # o 0 dBFS pode acionar SAT (clip) -> usa pico de -0.5 dB para a queda
    x[10, 1] = int(C.MAXOUT * 10 ** (-1.0 / 20))
    L = C.run_meter(x, x, np.zeros(n, dtype=np.uint8))
    off = []
    for k in range(10):
        idx = np.where(~L[:, k])[0]
        idx = idx[idx > 2]
        off.append(float(idx[0]) if idx.size else float('nan'))
    exp = [(-1.0 - d) / 20.1 * 1000 for d in C.METER_DB[:10]]
    res["queda_ms"] = {"medido": off, "esperado": exp}
    Ldec = L.copy()
    sl = np.polyfit(np.array(C.METER_DB[:10]), np.array(off), 1)[0]
    res["queda_db_por_s"] = float(-1000.0 / sl)
    print("  queda medida: %.1f dB/s" % res["queda_db_por_s"])
    # SAT: cenarios
    sc = {}
    # (a) corte: tom de -30 dBFS, ganho +42 dB (corta)
    n = FS * 5
    x = tone_int(1000, -30, n)
    xs = np.stack([x, x], 1)
    tgt = np.full(n, C.GAIN_TAB[28], dtype=np.int64)
    y, g, cl = C.apply_gain(xs, tgt, C.GAIN_TAB[28])
    # o tom so existe nos primeiros 0.5 s
    xs2 = xs.copy()
    xs2[FS // 2:] = 0
    y, g, cl = C.apply_gain(xs2, tgt, C.GAIN_TAB[28])
    L = C.run_meter(y, xs2, cl)
    sat = L[:, 11]
    ons = np.where(sat)[0]
    first, last = int(ons[0]), int(ons[-1])
    toggles = int(np.sum(np.diff(sat[first:last + 1].astype(int)) == 1))
    sc["corte"] = {"primeiro_ms": first, "ultimo_ms": last, "duracao_ms_depois_do_ultimo_evento": last - 500,
                   "piscadas_por_s": toggles / ((last - first) / 1000.0),
                   "vermelhos_seguem_SAT": bool(np.all(L[first:last + 1, 9] == L[first:last + 1, 11]) and
                                                np.all(L[first:last + 1, 10] == L[first:last + 1, 11]))}
    print("  SAT (corte): %s" % sc["corte"])
    # (b) sensor acima de ~128 dB: pico pre-ganho 0.6, ganho 0 dB (saida -4.4 dBFS, sem corte)
    x = np.zeros((n, 2), dtype=np.int64)
    x[:FS // 2] = np.stack([tone_int(1000, -4.4, FS // 2)] * 2, 1)
    tgt = np.full(n, C.GAIN_TAB[0], dtype=np.int64)
    y, g, cl = C.apply_gain(x, tgt, C.GAIN_TAB[0])
    L2 = C.run_meter(y, x, cl)
    ons = np.where(L2[:, 11])[0]
    sc["sensor"] = {"sat_ligado": bool(ons.size), "ultimo_ms": int(ons[-1]) if ons.size else None}
    # (c) sem evento: pico -6 dBFS
    x = np.zeros((n, 2), dtype=np.int64)
    x[:FS // 2] = np.stack([tone_int(1000, -6, FS // 2)] * 2, 1)
    y, g, cl = C.apply_gain(x, tgt, C.GAIN_TAB[0])
    L3 = C.run_meter(y, x, cl)
    sc["sem_evento"] = {"sat_ligado": bool(L3[:, 11].any())}
    res["sat"] = sc
    RES["medidor"] = res
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    a = ax[0, 0]
    for fq, c in (("1000", COL["a"]), ("8000", COL["c"]), ("16000", COL["b"])):
        err = [np.nan if m is None else m - d for m, d in zip(res["limiar_medido_db"][fq], C.METER_DB)]
        a.plot(C.METER_DB, err, "o-", color=c, ms=3, label="%s Hz" % fq)
    a.set_xlabel("limiar nominal (dBFS)")
    a.set_ylabel("erro do limiar (dB)")
    a.set_title("Degraus do medidor: erro com seno (pico por amostra)")
    a.legend(fontsize=8)
    a = ax[0, 1]
    a.plot(C.METER_DB[:10], res["queda_ms"]["medido"], "o", color=COL["a"], label="medido")
    a.plot(C.METER_DB[:10], res["queda_ms"]["esperado"], "-", color="gray", label="20 dB/s ideal")
    a.set_xlabel("degrau (dBFS)")
    a.set_ylabel("tempo aceso apos pico de -1 dBFS (ms)")
    a.set_title("Queda (~%.1f dB/s)" % res["queda_db_por_s"])
    a.legend(fontsize=8)
    a = ax[1, 0]
    tt = np.arange(L.shape[0])
    a.imshow(Ldec.T[:, :3000], aspect="auto", cmap="Greys", origin="lower", interpolation="nearest")
    a.set_yticks(range(12))
    a.set_yticklabels([str(d) for d in C.METER_DB] + ["SAT"], fontsize=7)
    a.set_xlabel("ms")
    a.set_title("Queda apos um pico de -1 dBFS (LEDs)")
    a.grid(False)
    a = ax[1, 1]
    Ls = C.run_meter(*(lambda yy, g_, cc: (yy, xs2, cc))(*C.apply_gain(xs2, np.full(n, C.GAIN_TAB[28], dtype=np.int64), C.GAIN_TAB[28])))
    a.imshow(Ls.T[:, :3200], aspect="auto", cmap="Greys", origin="lower", interpolation="nearest")
    a.set_yticks(range(12))
    a.set_yticklabels([str(d) for d in C.METER_DB] + ["SAT"], fontsize=7)
    a.set_xlabel("ms")
    a.set_title("Corte em 0-500 ms: SAT e vermelhos a 8 Hz por 2 s")
    a.grid(False)
    fig_save(fig, "medidor.png")
    save()


# ======================================================================= cpu
def g_cpu():
    print("[cpu]")
    res = {}
    for pess in (True, False):
        r = C.cpu_model(CHAIN, pess)
        tot = sum(r.values())
        res["pessimista" if pess else "otimista"] = {
            "itens_Mciclos_s": {k: v / 1e6 for k, v in r.items()}, "total_Mciclos_s": tot / 1e6,
            "carga_133MHz_pct": 100 * tot / 133e6, "carga_200MHz_pct": 100 * tot / 200e6,
            "carga_133MHz_pct_so_dsp": 100 * (tot - r['USB (copia 24 bits + IRQ TinyUSB, 1 kHz)'] - r['LEDs (charlieplex 5 pinos + medidor), botoes, flash']) / 133e6}
        print("  %s: %.1f Mc/s  133 MHz %.0f %%  200 MHz %.0f %%" % (
            "pess" if pess else "otim", tot / 1e6, 100 * tot / 133e6, 100 * tot / 200e6))
    # variantes
    var = {}
    for nm, ch in (("sinc4", C.Chain(N=4)),):
        r = C.cpu_model(ch, True)
        var[nm] = sum(r.values()) / 1e6
    res["variante_sinc4_pess_Mc"] = var
    # alternativa: HB3 com banda de passagem 18 kHz (menos taps)
    ch18 = C.Chain(hb3=(18e3, 90))
    res["hb3_fp18k"] = {"taps": ch18.hb3[2], "total_pess_Mc": sum(C.cpu_model(ch18, True).values()) / 1e6}
    RES["cpu"] = res
    fig, ax = plt.subplots(figsize=(8, 4.6))
    labs = list(C.cpu_model(CHAIN, True).keys())
    cols = plt.cm.tab20(np.linspace(0, 1, len(labs)))
    bottoms = [0, 0]
    for i, lab in enumerate(labs):
        vals = [res["pessimista"]["itens_Mciclos_s"][lab] / 133 * 100, res["otimista"]["itens_Mciclos_s"][lab] / 133 * 100]
        ax.barh(["pessimista (6/14/30 ciclos)", "otimista (5/10/20)"], vals, left=bottoms, color=cols[i], label=lab)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.axvline(100, color="red", lw=1)
    ax.set_xlabel("% de um nucleo a 133 MHz (a 200 MHz, multiplique por 0.665); linha vermelha = 100 %")
    ax.set_title("Carga estimada no RP2040, 2 canais, 48 kHz")
    ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2)
    ax.set_xlim(0, 110)
    fig_save(fig, "cpu.png")
    save()


# ======================================================================= arranque
def g_arranque():
    print("[arranque]")
    res = {}
    nout = int(0.6 * FS)
    x = np.zeros(nout * OSR)
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for fast, c in ((True, COL["a"]), (False, COL["b"])):
        ch = C.Chain(dc_fast=fast)
        y = run_chain(x, dcs=(-0.01, -1e-4), noise=True, chain=ch, dc_block=False)
        z = ch.dc(y)
        zz = z / FULL
        gain = 10 ** (42 / 20)
        pk = np.abs(zz[:, 0]) * gain
        res["fast" if fast else "lento"] = {
            "pico_L_dbfs_ms0_50": float(dbf(np.abs(zz[:FS // 20, 0]).max())),
            "pico_L_dbfs_ms100_600": float(dbf(np.abs(zz[FS // 10:, 0]).max())),
            "tempo_ate_abaixo_de_-60dBFS_ms": float(1000 * np.argmax(np.abs(zz[:, 0]) < 1e-3) / FS)}
        # primeiro instante em que o resto (|x| < 1e-3, 1000 amostras seguidas) fica abaixo
        env = np.convolve(np.abs(zz[:, 0]), np.ones(240) / 240, mode="same")
        ok = np.where(env > 1e-3)[0]
        res["fast" if fast else "lento"]["acomoda_ms"] = float(1000 * (ok[-1] if ok.size else 0) / FS)
        t = np.arange(zz.shape[0]) / FS * 1000
        ax[0].plot(t, 20 * np.log10(np.maximum(env, 1e-7)), color=c, label=("arranque rapido" if fast else "so 2.8 Hz"))
        print("  dc_fast=%s -> %s" % (fast, res["fast" if fast else "lento"]))
    ax[0].set_xlabel("ms apos ligar")
    ax[0].set_ylabel("envelope (dBFS), canal L (DC -40 dBFS)")
    ax[0].set_ylim(-140, -20)
    ax[0].legend(fontsize=8)
    ax[0].set_title("Arranque: DC de -40 dBFS do canal L")
    ax[1].axis("off")
    RES["arranque"] = res
    fig_save(fig, "arranque.png")
    save()


GROUPS = {"resp": g_resp, "ruido": g_ruido, "dist": g_dist, "alias": g_alias, "sat": g_sat,
          "ganho": g_ganho, "medidor": g_medidor, "cpu": g_cpu, "arranque": g_arranque}

if __name__ == "__main__":
    sel = sys.argv[1:] or list(GROUPS)
    for g in sel:
        t0 = time.time()
        GROUPS[g]()
        print("   (%.1f s)" % (time.time() - t0))
