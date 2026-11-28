"""Liebling (R3MIC) F1: cadeia de decimacao em inteiros, no estilo do RP2040.

PDM (2 canais, 1 linha, 3.072 MHz por canal)
  -> desentrelaca (word de 32 bits = 16 pares A/B)
  -> sinc^N por LUT de bytes, R = 16 (-> 192 kHz)         [tabelas int32]
  -> meia-banda 192 -> 96 kHz (Q15)
  -> meia-banda  96 -> 48 kHz (Q15)
  -> compensacao de droop do sinc (3 taps, Q15)
  -> bloqueio de DC (1a ordem, ~2.8 kHz... ~2.8 Hz, so deslocamentos)
  -> ganho (0..+42 dB, 1.5 dB, rampa de um polo) -> clamp 24 bits
  -> medidor / SAT

Escala: 2^23 = fundo de escala (1.0).  Todas as contas inteiras cabem em int64 aqui
e a maior soma parcial cabe em 2^53 (float64 exato); no RP2040 o MAC vira
2 x (16x16) por tap (ver cpu_model).
"""
import numpy as np
from numba import njit
from scipy import signal

FS = 48_000
FS_BIT = 3_072_000
FULL = 1 << 23            # 1.0
MAXOUT = FULL - 1


# ------------------------------------------------------------------ desentrelacar
def interleave_words(bits_a, bits_b):
    """a,b: arrays 0/1.  Sequencia A0 B0 A1 B1 ...; MSB = mais antigo.
    Devolve uint32 (n/16 words)."""
    n = (min(bits_a.size, bits_b.size) // 16) * 16
    seq = np.empty(2 * n, dtype=np.uint8)
    seq[0::2] = bits_a[:n]
    seq[1::2] = bits_b[:n]
    by = np.packbits(seq).reshape(-1, 4)
    return (by[:, 0].astype(np.uint32) << 24) | (by[:, 1].astype(np.uint32) << 16) | \
           (by[:, 2].astype(np.uint32) << 8) | by[:, 3].astype(np.uint32)


def unshuffle32(w):
    """Truque de bits (Hacker's Delight): separa bits pares (A) e impares (B).
    Devolve (a16, b16), cada um 16 bits com o mais antigo no MSB."""
    w = w.astype(np.uint64) & 0xFFFFFFFF
    x = w
    # "perfect unshuffle": bits em posicao 2k+1 (A, mais antigos) -> metade alta
    t = (x ^ (x >> 1)) & 0x22222222; x = x ^ t ^ (t << 1)
    t = (x ^ (x >> 2)) & 0x0C0C0C0C; x = x ^ t ^ (t << 2)
    t = (x ^ (x >> 4)) & 0x00F000F0; x = x ^ t ^ (t << 4)
    t = (x ^ (x >> 8)) & 0x0000FF00; x = x ^ t ^ (t << 8)
    x &= 0xFFFFFFFF
    return (x >> 16).astype(np.uint32), (x & 0xFFFF).astype(np.uint32)


UNSHUFFLE_OPS = 4 * 5          # ~20 operacoes de 1 ciclo + carga/guarda


# ------------------------------------------------------------------ sinc por LUT
def sinc_kernel(N=5, R=16):
    h = np.ones(1, dtype=np.int64)
    box = np.ones(R, dtype=np.int64)
    for _ in range(N):
        h = np.convolve(h, box)
    return h                                   # soma = R^N


def sinc_tables(N=5, R=16):
    h = sinc_kernel(N, R)
    gain = R ** N
    scale = FULL // gain                       # inteiro (R=16,N=5: 8; R=16,N=4: 128)
    assert FULL % gain == 0
    nb = -(-len(h) // 8)
    hp = np.zeros(nb * 8, dtype=np.int64)
    hp[:len(h)] = h * scale
    T = np.zeros((nb, 256), dtype=np.int64)
    for m in range(nb):
        for v in range(256):
            s = 0
            for j in range(8):
                s += (2 * ((v >> j) & 1) - 1) * hp[8 * m + j]
            T[m, v] = s
    assert np.abs(T).max() < 2 ** 31
    return T


def sinc_decimate(bytes_, T, R=16):
    """bytes_: uint8, MSB=mais antigo.  R/8 bytes por saida."""
    bpf = R // 8
    nf = bytes_.size // bpf
    nb = T.shape[0]
    y = np.zeros(nf, dtype=np.int64)
    base = bpf * np.arange(nf) + (bpf - 1)
    for m in range(nb):
        idx = base - m
        ok = idx >= 0
        vals = np.where(ok, bytes_[np.clip(idx, 0, None)], 0)
        y += np.where(ok, T[m][vals], 0)
    return y


def sinc_response_db(f, N=5, R=16, fin=FS_BIT):
    x = np.pi * f / fin
    with np.errstate(all='ignore'):
        h = np.abs(np.sin(R * x) / (R * np.sin(x))) ** N
    h = np.where(np.abs(np.sin(x)) < 1e-12, 1.0, h)
    return 20 * np.log10(np.maximum(h, 1e-30))


# ------------------------------------------------------------------ meia-banda
def halfband(fs_in, fpass, atten_db, qbits=17):
    """Kaiser, 4m+3 taps, zeros nas posicoes pares != 0.  Devolve (float, int Q15)."""
    width = 2 * (fs_in / 4 - fpass) / (fs_in / 2)      # banda de transicao normalizada
    N, beta = signal.kaiserord(atten_db, width)
    N = int(N)
    while N % 4 != 3:
        N += 1
    n = np.arange(N) - (N - 1) // 2
    h = 0.5 * np.sinc(n / 2.0) * np.kaiser(N, beta)
    h[(n % 2 == 0) & (n != 0)] = 0.0
    h /= h.sum()
    q = np.round(h * (1 << qbits)).astype(np.int64)
    q[(N - 1) // 2] += (1 << qbits) - q.sum()           # soma exata = 1.0
    return h, q, N, beta


def fir_decimate2(x, q, qbits=17):
    """y[m] = sum q[i] x[2m - i] >> qbits (arredondado).  x em float64 exato."""
    s = np.convolve(x.astype(np.float64), q.astype(np.float64), mode='full')[:x.size]
    s = s[::2]
    return np.floor((s + (1 << (qbits - 1))) / (1 << qbits)).astype(np.int64)


def fir_same(x, q, qbits=15):
    s = np.convolve(x.astype(np.float64), q.astype(np.float64), mode='full')[:x.size]
    return np.floor((s + (1 << (qbits - 1))) / (1 << qbits)).astype(np.int64)


def comp_taps(a=0.0252, qbits=15):
    q = np.round(np.array([-a, 1 + 2 * a, -a]) * (1 << qbits)).astype(np.int64)
    q[1] += (1 << qbits) * 1 + int(round(2 * a * (1 << qbits))) * 0   # mantem
    # DC gain = 1 + 2a - 2a = 1  -> soma exata
    q[1] = (1 << qbits) - q[0] - q[2]
    return q


# ------------------------------------------------------------------ DC block
@njit(cache=True)
def dc_block(x, kfast_start=True, dc0=0):
    """dc += (diff>>12) + (diff>>13)  (alpha = 3/8192 -> 2.8 Hz a 48 kHz), 8 bits
    fracionarios.  Arranque rapido: primeiras amostras usam shift crescente."""
    n = x.shape[0]
    y = np.empty(n, dtype=np.int64)
    dc = np.int64(dc0) << 8
    for i in range(n):
        xi = np.int64(x[i]) << 8
        diff = xi - dc
        if kfast_start and i < 8192:
            # k = 1 + floor(log2(i+2)), limitado a 12
            k = 1
            m = i + 2
            while m > 1:
                m >>= 1
                k += 1
            if k > 12:
                k = 12
            dc += diff >> k
        else:
            dc += (diff >> 12) + (diff >> 13)
        y[i] = x[i] - (dc >> 8)
    return y


def dc_response_db(f, fs=FS):
    a = 3.0 / 8192.0
    # y = x - dc;  dc[n+1] = dc[n] + a (x - dc[n])  -> H = (1-z^-1)/(1-(1-a) z^-1)... aproximacao 1a ordem
    w = 2 * np.pi * np.asarray(f) / fs
    z = np.exp(1j * w)
    # dc[n] = a z^-1/(1 - (1-a) z^-1) x ;  y = x - dc
    H = 1 - a / (z - (1 - a))
    return 20 * np.log10(np.abs(H))


# ------------------------------------------------------------------ ganho
GAIN_STEP_DB = 1.5
GAIN_N = 29                         # 0 .. 42 dB
GAIN_Q = 24
GAIN_TAB = np.round(10 ** (GAIN_STEP_DB * np.arange(GAIN_N) / 20) * (1 << GAIN_Q)).astype(np.int64)
assert GAIN_TAB.max() < 2 ** 31


@njit(cache=True)
def apply_gain(x, tgt, g0, shift=9):
    """x: (n,2) int64; tgt: (n,) alvo (Q24, int); rampa: g += (tgt-g)>>shift.
    Devolve y (clampado), g(n), flag de corte, pico pre-clamp."""
    n = x.shape[0]
    y = np.empty((n, 2), dtype=np.int64)
    gs = np.empty(n, dtype=np.int64)
    clipped = np.zeros(n, dtype=np.uint8)
    g = np.int64(g0)
    mx = np.int64(8388607)
    for i in range(n):
        d = tgt[i] - g
        if d > -(1 << shift) and d < (1 << shift):
            g = tgt[i]
        else:
            g += d >> shift
        gs[i] = g
        c = 0
        for ch in range(2):
            v = (x[i, ch] * g + (1 << 23)) >> 24
            if v > mx:
                v = mx
                c = 1
            elif v < -mx:
                v = -mx
                c = 1
            y[i, ch] = v
        clipped[i] = c
    return y, gs, clipped


# ------------------------------------------------------------------ medidor
METER_DB = [-42, -36, -30, -24, -20, -16, -12, -9, -6, -3, 0]
METER_COL = ['G'] * 6 + ['Y'] * 3 + ['R'] * 2
TOL0 = -0.1                          # "0 dBFS" = pico >= -0.1 dBFS
METER_THR = np.array([int(round(MAXOUT * 10 ** ((d if d < 0 else TOL0) / 20))) for d in METER_DB])
CLIP_THR = int(round(MAXOUT * 10 ** (TOL0 / 20)))
DECAY_SHIFTS = (9, 11, -13)         # lvl -= lvl>>9 + lvl>>11 - lvl>>13 por ms  (~20.1 dB/s)
SENSOR_THR = int(10 ** (-4.6 / 20) * FULL)   # pre-ganho, pos-DC: -4.6 dBFS (~126.5 dB SPL no modelo; calibrar com o sensor real)
SAT_MS = 2000
BLINK_PERIOD_MS = 125                # 8 Hz


class Meter:
    """Atualizado a cada 1 ms (48 amostras).  Ataque instantaneo."""

    def __init__(self):
        self.lvl = 0
        self.sat_t = 0
        self.t = 0

    def step(self, blk_peak_out, blk_peak_pre, blk_clip):
        """blk_peak_out: max(|L|,|R|) pos-ganho; blk_peak_pre: pre-ganho."""
        lvl = self.lvl
        lvl = lvl - (lvl >> 9) - (lvl >> 11) + (lvl >> 13)
        if blk_peak_out > lvl:
            lvl = blk_peak_out
        self.lvl = lvl
        ev = blk_clip or (blk_peak_out >= CLIP_THR) or (blk_peak_pre >= SENSOR_THR)
        if ev:
            self.sat_t = SAT_MS
        elif self.sat_t > 0:
            self.sat_t -= 1
        leds = [lvl >= t for t in METER_THR]
        sat_on = False
        if self.sat_t > 0:
            sat_on = (self.t % BLINK_PERIOD_MS) < (BLINK_PERIOD_MS // 2 + 1)
            leds[-1] = sat_on
            leds[-2] = sat_on
        self.t += 1
        return leds, sat_on if self.sat_t > 0 else False


def run_meter(y, pre, clipped, fs=FS):
    """y,pre: (n,2).  Devolve array (nblk, 12) bool [11 LEDs + SAT] e tempo ms."""
    blk = fs // 1000
    nb = y.shape[0] // blk
    m = Meter()
    out = np.zeros((nb, 12), dtype=bool)
    for b in range(nb):
        s = slice(b * blk, (b + 1) * blk)
        po = int(np.abs(y[s]).max())
        pp = int(np.abs(pre[s]).max())
        c = bool(clipped[s].any())
        leds, sat = m.step(po, pp, c)
        out[b, :11] = leds
        out[b, 11] = sat
    return out


# ------------------------------------------------------------------ cadeia inteira
class Chain:
    QB = 17                      # bits fracionarios dos coeficientes das meias-bandas
    def __init__(self, N=5, R=16, hb2=(20e3, 100), hb3=(20e3, 90), comp=0.0252,
                 dc_fast=True):
        self.N, self.R = N, R
        self.T = sinc_tables(N, R)
        fs1 = FS_BIT // R
        self.fs1 = fs1
        self.hb2 = halfband(fs1, *hb2)
        self.hb3 = halfband(fs1 // 2, *hb3)
        self.comp = comp_taps(comp) if comp else None
        self.dc_fast = dc_fast

    def decimate(self, bits_a, bits_b, drop=0):
        """PDM -> 48 kHz inteiro (antes do DC block).  (n,2)."""
        words = interleave_words(bits_a, bits_b)
        a16, b16 = unshuffle32(words)
        out = []
        for w in (a16, b16):
            by = np.empty(w.size * 2, dtype=np.uint8)
            by[0::2] = (w >> 8) & 255
            by[1::2] = w & 255
            y1 = sinc_decimate(by, self.T, self.R)
            y2 = fir_decimate2(y1, self.hb2[1], self.QB)
            y3 = fir_decimate2(y2, self.hb3[1], self.QB)
            if self.comp is not None:
                y3 = fir_same(y3, self.comp)
            out.append(y3)
        n = min(o.size for o in out)
        return np.stack([o[:n] for o in out], axis=1)

    def dc(self, x, dc0=(0, 0)):
        return np.stack([dc_block(x[:, 0], self.dc_fast, dc0[0]),
                         dc_block(x[:, 1], self.dc_fast, dc0[1])], axis=1)


# ------------------------------------------------------------------ modelo de CPU
def cpu_model(chain: Chain, pess=True):
    """Ciclos/s do Cortex-M0+ para 2 canais.  Hipoteses explicitas (ver FIRMWARE.md):
    pess=True : lookup+soma = 6 ciclos, MAC de par = 14, mult 64 bits = 30
    pess=False: 5, 10, 20.  Codigo e tabelas em SRAM (nao em flash/XIP), sem esperas de barramento."""
    lk = 6 if pess else 5
    mac = 14 if pess else 10
    m64 = 30 if pess else 20
    words = FS_BIT * 2 / 32
    r = {}
    r['desentrelacar (1 word = 16 pares)'] = words * (UNSHUFFLE_OPS + 6)
    nlk = chain.T.shape[0]                           # lookups por saida do sinc
    r['sinc^%d LUT (%d lookups/saida)' % (chain.N, nlk)] = 2 * chain.fs1 * (nlk * lk + 8)
    pairs2 = ((len(chain.hb2[1]) - 1) // 2 + 1) // 2   # pares nao nulos (indices impares)
    r['meia-banda 192->96 (%d pares)' % pairs2] = 2 * (chain.fs1 // 2) * (pairs2 * mac + 20)
    pairs3 = ((len(chain.hb3[1]) - 1) // 2 + 1) // 2
    r['meia-banda 96->48 (%d pares)' % pairs3] = 2 * FS * (pairs3 * mac + 20)
    r['compensacao 3 taps'] = 2 * FS * (2 * 8 + 12)
    r['bloqueio de DC'] = 2 * FS * 14
    r['ganho (mult 64 bits) + clamp + rampa'] = FS * (2 * (m64 + 8) + 14)
    r['medidor (max por amostra, 1 ms)'] = FS * 2 * 5 + 1000 * 150
    r['USB (copia 24 bits + IRQ TinyUSB, 1 kHz)'] = 1000 * 4000
    r['LEDs (charlieplex 5 pinos + medidor), botoes, flash'] = 1.0e6
    return r


if __name__ == "__main__":
    c = Chain()
    print(c.hb2[2:], c.hb3[2:])
    for pess in (True, False):
        r = cpu_model(c, pess)
        tot = sum(r.values())
        print(pess, tot / 1e6, tot / 133e6 * 100, tot / 200e6 * 100)
