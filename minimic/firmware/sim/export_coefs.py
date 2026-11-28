"""Escreve out/coeficientes.json: tudo o que o F2 precisa para gerar tabelas em C."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import chain as C

c = C.Chain()
d = {
    "sinc": {"ordem": c.N, "R": c.R, "escala_lut": C.FULL // (c.R ** c.N), "lookups_por_saida": int(c.T.shape[0]),
             "nucleo_inteiro_R^N": int(c.R ** c.N), "taps": int(len(C.sinc_kernel(c.N, c.R)))},
    "hb2": {"fs_in": c.fs1, "taps": len(c.hb2[1]), "qbits": c.QB, "beta": float(c.hb2[3]), "coef": [int(v) for v in c.hb2[1]]},
    "hb3": {"fs_in": c.fs1 // 2, "taps": len(c.hb3[1]), "qbits": c.QB, "beta": float(c.hb3[3]), "coef": [int(v) for v in c.hb3[1]]},
    "comp": {"qbits": 15, "coef": [int(v) for v in c.comp]},
    "dc": {"alpha": "3/8192 (diff>>12 + diff>>13)", "fc_hz": 48000 * 3 / 8192 / 6.283185, "frac_bits": 8,
           "arranque": "shift k = min(12, 1 + floor(log2(n+2))) nas primeiras 8192 amostras"},
    "ganho": {"passo_db": C.GAIN_STEP_DB, "n": C.GAIN_N, "q": C.GAIN_Q, "tabela": [int(v) for v in C.GAIN_TAB],
              "rampa": "g += (alvo-g) >> 9"},
    "medidor": {"db": C.METER_DB, "limiar_int24": [int(v) for v in C.METER_THR], "clip_int24": C.CLIP_THR,
                "sensor_int24": C.SENSOR_THR, "queda": "lvl -= (lvl>>9) + (lvl>>11) - (lvl>>13) por ms (~20 dB/s)",
                "sat_ms": C.SAT_MS, "pisca_periodo_ms": C.BLINK_PERIOD_MS},
}
json.dump(d, open(os.path.join(os.path.dirname(__file__), "out", "coeficientes.json"), "w"), indent=1)
print({k: (v if not isinstance(v, dict) else list(v)[:3]) for k, v in d.items()})
