"""Liebling (R3MIC) F1: sensor sintetico + modulador delta-sigma PDM.

Tudo em amplitude relativa ao fundo de escala (1.0 = 0 dBFS de seno, pico).
Ficha IM72D128VV01 (Infineon, v1.2, 2025-05-04): 1 kHz, 94 dB SPL = -36 dBFS
(+-1 dB), AOP 128 dB SPL (10 % THD), SNR 71.5 dB(A) a 3.072 MHz, LFRO 11 Hz,
DC de saida -80 dBFS (LR=GND) ou -40 dBFS (LR=VDD).
"""
import numpy as np
from numba import njit
from scipy import signal

FCLK = 3_072_000          # clock PDM (Hz)
FS = 48_000               # saida (Hz)
OSR = FCLK // FS          # 64
SENS_DBFS = -36.0         # dBFS a 94 dB SPL
SPL_FULL = 94.0 - SENS_DBFS   # 130 dB SPL = 0 dBFS (seno de pico)
SNR_A = 71.5              # dB(A), ficha
AOP = 128.0


def spl_to_amp(spl):
    return 10 ** ((np.asarray(spl, dtype=float) - SPL_FULL) / 20.0)


def amp_to_dbfs(a):
    return 20 * np.log10(np.maximum(np.abs(a), 1e-30))


# ---------------------------------------------------------------- A-weighting
def a_weight_db(f):
    f = np.asarray(f, dtype=float)
    f2 = f ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return 20 * np.log10(np.maximum(ra, 1e-30)) + 2.0


# ---------------------------------------------------------------- modulador
def design_ntf(order=4, obg=1.5):
    """NTF monica: zeros em z=1, polos Butterworth passa-altas; ajusta fc para OBG."""
    w = np.linspace(1e-4, np.pi, 4096)
    best = None
    lo, hi = 0.005, 0.45
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        b, a = signal.butter(order, mid, 'high')   # fc normalizado a Nyquist
        B = np.poly(np.ones(order))                 # (1 - z^-1)^order
        A = a / a[0]
        _, h = signal.freqz(B, A, worN=w)
        g = np.max(np.abs(h))
        if g > obg:
            hi = mid
        else:
            lo = mid
        best = (B, A, g)
    return best


@njit(cache=True)
def _dsm(x, bm, am):
    """y = x + NTF e, 1 bit +-1.  s = ((B-A)/A) e ; u = x + s."""
    n = x.shape[0]
    order = bm.shape[0] - 1
    y = np.empty(n, dtype=np.int8)
    e_hist = np.zeros(order + 1)
    s_hist = np.zeros(order + 1)
    for i in range(n):
        s = 0.0
        for k in range(1, order + 1):
            s += (bm[k] - am[k]) * e_hist[k - 1] - am[k] * s_hist[k - 1]
        u = x[i] + s
        v = 1.0 if u >= 0.0 else -1.0
        e = v - u
        for k in range(order - 1, 0, -1):
            e_hist[k] = e_hist[k - 1]
            s_hist[k] = s_hist[k - 1]
        e_hist[0] = e
        s_hist[0] = s
        y[i] = 1 if v > 0 else 0
    return y


_NTF_CACHE = {}


def modulate(x, order=4, obg=1.5):
    key = (order, obg)
    if key not in _NTF_CACHE:
        B, A, g = design_ntf(order, obg)
        _NTF_CACHE[key] = (B, A, g)
    B, A, _ = _NTF_CACHE[key]
    return _dsm(np.ascontiguousarray(x, dtype=np.float64), B.astype(np.float64), A.astype(np.float64))


# ---------------------------------------------------------------- sensor
def softclip(x, L, p):
    return x / (1.0 + np.abs(x / L) ** p) ** (1.0 / p)


def thd_of_clip(amp, L, p, n=1 << 16):
    t = np.arange(n) / n
    k = 17
    y = softclip(amp * np.sin(2 * np.pi * k * t), L, p)
    Y = np.abs(np.fft.rfft(y)) / n * 2
    f = Y[k]
    h = np.sqrt(sum(Y[k * m] ** 2 for m in range(2, 6)))
    return h / f


def fit_clip(p=6.0, target=0.10, amp=None):
    from scipy.optimize import brentq
    amp = float(spl_to_amp(AOP)) if amp is None else amp
    L = brentq(lambda L: thd_of_clip(amp, L, p) - target, 0.45, 1.5)
    return L


CLIP_P = 10.0
CLIP_L = fit_clip(CLIP_P)


_NOISE_SIGMA = {}


def white_sigma_for_snr_a(snr_a=SNR_A, fs=FCLK):
    """sigma do ruido branco (a fs=FCLK) que da SNR (A) no 94 dB SPL.
    sinal = seno de pico 10^(-36/20) -> rms /sqrt2; ruido A-ponderado 20..20k."""
    key = (snr_a, fs)
    if key in _NOISE_SIGMA:
        return _NOISE_SIGMA[key]
    sig_rms = 10 ** (SENS_DBFS / 20) / np.sqrt(2)
    target = sig_rms / 10 ** (snr_a / 20)
    f = np.linspace(20, 20000, 20000)
    w = 10 ** (a_weight_db(f) / 20)
    # ruido branco de variancia s2 em fs: densidade S = s2/(fs/2) por Hz
    # variancia A-ponderada em 20..20k = S * int w^2 df
    iw = np.trapezoid(w ** 2, f)
    sigma = target / np.sqrt(iw / (fs / 2))
    _NOISE_SIGMA[key] = sigma
    return sigma


def make_sensor_input(acoustic, dc=-1e-4, noise=True, hpf=True, clip=True, seed=1,
                      snr_a=SNR_A):
    """acoustic: amplitude relativa (3.072 MHz).  Devolve a entrada do modulador."""
    x = np.asarray(acoustic, dtype=np.float64)
    if clip:
        x = softclip(x, CLIP_L, CLIP_P)
    if hpf:
        # 1a ordem, -3 dB em 11 Hz (hipotese; a ficha so da LFRO = 11 Hz)
        a = np.exp(-2 * np.pi * 11.0 / FCLK)
        x = signal.lfilter([(1 + a) / 2, -(1 + a) / 2], [1, -a], x)
    x = x + dc
    if noise:
        rng = np.random.default_rng(seed)
        x = x + rng.standard_normal(x.size) * white_sigma_for_snr_a(snr_a)
    return x


def tone(freq, spl_or_amp, n, amp_is_spl=True, phase=0.0, fs=FCLK):
    a = float(spl_to_amp(spl_or_amp)) if amp_is_spl else float(spl_or_amp)
    t = np.arange(n) / fs
    return a * np.sin(2 * np.pi * freq * t + phase)


def pdm_of(acoustic, dc=-1e-4, noise=True, hpf=True, clip=True, seed=1, order=5, obg=1.3):
    return modulate(make_sensor_input(acoustic, dc, noise, hpf, clip, seed), order, obg)


if __name__ == "__main__":
    print("CLIP_L", CLIP_L, "thd 125", thd_of_clip(float(spl_to_amp(125)), CLIP_L, CLIP_P),
          "thd 128", thd_of_clip(float(spl_to_amp(128)), CLIP_L, CLIP_P))
    B, A, g = design_ntf(4, 1.5)
    print("OBG", g)
    print("sigma", white_sigma_for_snr_a())
