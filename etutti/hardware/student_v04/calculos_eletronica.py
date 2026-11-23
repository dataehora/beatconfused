"""eTutti Student V4 (R1V4 + R2V4): the electronics' numbers, all in one script (stdlib).

    python etutti/hardware/student_v04/calculos_eletronica.py

Prints (and writes calculos_eletronica.json): E2 (scan time, velocity resolution, OUT-line capacitance, current),
E3 (cost: F2 rulers x F1 flat board) and E4 helper numbers. Prices come from fornecimento/precos_jlc.json
(JLCPCB parts library, 21 Nov 2026). Every JLCPCB *service* figure (PCB, setup, stencil, Extended fee) is the J's
quote of 18 Nov 2026 for the V3, or an ESTIMATE where marked: the quote itself needs uploaded files.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.normpath(os.path.join(HERE, "..", "student_v03", "bom_v3.csv"))
PRICES = json.load(open(os.path.join(HERE, "fornecimento", "precos_jlc.json"), encoding="utf-8"))
RATE = 1.30
SETUP, STENCIL, EXT_FEE, SMT_N2 = 8.24, 1.55, 3.09, 3.2     # quote 18 Nov (SMT_N2 = estimate in the V3 page)
OUT = {}


# ---------------------------------------------------------------- E2: scan
def scan():
    t_on_max, t_on_typ = 45.0, 20.0            # us, TMAG5253 BAx, Electrical Characteristics (SBASAI5E, Apr 2026)
    tau = t_on_max / math.log(20)              # first-order model: 95 % at 45 us
    t_read = 6.0                               # us, 4 rows as 2 + 2 conversions on ADC1/ADC2 (estimate, ~3 us each)
    res = {"tau_us": round(tau, 1), "residual_pct": {}, "tables": {}}
    for w in (45, 60, 75, 90, 120, 135):
        res["residual_pct"][w] = round(100 * math.exp(-w / tau), 3)
    for keys, cols in ((28, 8), (44, 12), (60, 16), (76, 20)):
        row = {}
        for wait in (60, 90):
            step = wait + t_read + 4                       # + shift + margin
            full = cols * step / 1000
            row[wait] = {"step_us": step, "scan_ms": round(full, 2), "scan_hz": round(1000 / full)}
        # two OUT lines per row: half the columns
        row["2xOUT_60"] = round((cols / 2) * (60 + t_read + 4) / 1000, 2)
        row["hot_us"] = 60 + t_read + 4 + 160 / 5.0 / 1.0 * 0   # random access: the pattern is shifted while the old column is read
        res["tables"][keys] = row
    # velocity: 1 ms = 127, 80 ms = 1, log: steps per octave
    steps_per_oct = 126 / math.log2(80)
    res["vel_steps_per_octave"] = round(steps_per_oct, 1)
    for label, T in (("28@0.56ms", 0.56), ("76@1.4ms", 1.4), ("hot@0.07ms", 0.07), ("V3@0.25ms", 0.25)):
        # time between two thresholds = 1 ms: error +-T/2 (no interpolation), +-T/8 (with interpolation, estimate)
        err = lambda e: round(steps_per_oct * math.log2(1 + e / 1.0), 1)
        res.setdefault("vel_err_steps_at_1ms", {})[label] = {"sem_interpolar": err(T / 2), "interpolando": err(T / 8)}
    # OUT capacitance
    c_sensor, c_trace_per_cm, c_cable_per_cm, c_con, c_adc = 20.0, 0.7, 1.0, 3.0, 5.0     # pF; estimates except c_sensor (datasheet 'about 20 pF')
    caps = {}
    for rul in (2, 3, 4, 5):
        n = 4 * rul
        trace = rul * 7.4 * c_trace_per_cm                      # 74 mm of track per ruler
        cable = (rul) * 6 * c_cable_per_cm                      # 60 mm cable per link
        caps[rul] = {"sensores": n, "pF": round(n * c_sensor + trace + cable + 2 * rul * c_con + c_adc), "limite_pF": 1000}
    res["cap_OUT"] = caps
    # current: 4 sensors on at a time
    res["corrente_mA"] = {"F2_tip": 4 * 2.6, "F2_max": 4 * 5.0, "V3_14_sensores_tip": 14 * 2.6, "V3_max": 14 * 5.0}
    res["corrente_media_60us_de_70"] = round(4 * 2.6, 1)
    return res


# ---------------------------------------------------------------- E3: cost
def price(code, qty):
    p = PRICES[code]["tiers"]
    best = p[0][1]
    for n, v in p:
        if qty >= n:
            best = v
    return best


def bom_rows():
    return list(csv.DictReader(open(V3, encoding="utf-8")))


def parts_cost(rows, boards=2, skip_home=True):
    tot, ext = 0.0, set()
    for r in rows:
        if skip_home and r["montagem"].startswith("casa"):
            continue
        q = int(r["qtd"]) * boards
        tot += q * price(r["lcsc"], q)
        if r["classe"] == "Extended":
            ext.add(r["lcsc"])
    return round(tot, 2), len(ext)


def cost():
    rows = bom_rows()
    f1_parts, f1_ext = parts_cost(rows)
    # F2 main board: no muxes, no 74LVC, no sensors, no per-sensor/mux 100 nF (C601-603, C701-728)
    removed = {"74HC4067PW", "74LVC1G08", "74LVC1G04", "TMAG5253BA3IQDMRR"}
    keep = []
    for r in rows:
        if r["valor"] in removed:
            continue
        r = dict(r)
        if r["valor"] == "100nF":
            des = r["designadores"].split(",")
            des = [d for d in des if not (d.startswith("C601") or d.startswith("C602") or d.startswith("C603") or
                                          (d.startswith("C7") and len(d) == 4))]
            r["qtd"] = str(len(des))
        keep.append(r)
    f2_main_parts, f2_main_ext = parts_cost(keep)
    # + 4 row connectors (XYECONN SH-6, Extended), 4 x 100k pull-down, 2 x 100 ohm (Basic): small
    con = price("C160405", 8) * 4 * 2
    f2_main_parts += round(con + 8 * 0.002 + 6 * 0.002, 2)
    f2_main_ext += 1
    # one ruler: 4 TMAG, 1 x 74HC595D, 2 x SH-6, 5 x 100 nF, 1 x 10 uF 0805, 1 x 100 ohm
    def ruler_parts(n_rulers):
        tm = price("C22401868", 4 * n_rulers) * 4
        one = tm + price("C730243", n_rulers) + 2 * price("C160405", 2 * n_rulers) + 5 * price("C1525", 5 * n_rulers) + \
            price("C15850", n_rulers) + price("C25076", n_rulers)
        return one
    ruler_one_12 = ruler_parts(10)
    ruler_one_4 = ruler_parts(4)
    res = {"F1_pecas_2placas": f1_parts, "F1_tipos_ext": f1_ext,
           "F2_principal_pecas_2placas": round(f2_main_parts, 2), "F2_principal_tipos_ext": f2_main_ext,
           "regua_pecas_cada_12": round(ruler_one_12, 3), "regua_pecas_cada_4": round(ruler_one_4, 3),
           "reguas_10_pecas": round(10 * ruler_one_12, 2)}
    # ------------------------------------------------ the two orders, low/high
    def rng(lo, hi=None):
        return (lo, lo if hi is None else hi)
    common = {   # same in F1 and F2 (V3 page ranges, 15 Nov / "visto" or estimate); speaker: Dayton CE28MB-8 estimate
        "teclas Gateron KS-20 x28": rng(24.5, 26.6), "modulo MicroMod Teensy": rng(24.3, 29.2),
        "bateria 503450": rng(6.5, 10.4), "OLED + cabo SH 4 vias": rng(6.5, 13.0), "alto-falante Dayton CE28MB-8 (est.)": rng(5, 8),
        "tela acustica, espuma, silicone": rng(5.2, 10.4), "cabo USB-C": rng(0, 6.5), "kit M2,5 do modulo": rng(2.6, 5.2),
        "2 encoders EC11E (casa)": rng(4.0, 4.7)}
    f1 = {
        "placa principal 4L 246,5x95 (5 un., eng.+placa)": rng(39.5),
        "montagem: setup + estencil": rng(SETUP + STENCIL),
        "tipos Extended (%d x 3,09)" % f1_ext: rng(f1_ext * EXT_FEE),
        "pecas das 2 placas montadas": rng(f1_parts),
        "SMT e nitrogenio (est.)": rng(SMT_N2),
        "grade FR-4 escareada (est.)": rng(15, 30),
        "parafusos/porcas M2, pes de 80A (est.)": rng(10, 20),
        "cabos e conectores entre placas": rng(0),
        "impressao do case (est. por volume, V3)": rng(45 * RATE, 110 * RATE),
    }
    f2 = {
        "placa principal 4L ~85x95 (5 un.) (est.)": rng(14.5, 39.5),
        "reguas: 2L, paineis de 5 (5 un.) (est.)": rng(5, 12),
        "principal: setup + estencil": rng(SETUP + STENCIL),
        "reguas: setup + estencil": rng(SETUP + STENCIL),
        "tipos Extended principal (%d x 3,09)" % f2_main_ext: rng(f2_main_ext * EXT_FEE),
        "tipos Extended reguas (3 x 3,09: TMAG, SH-6, 74HC595BQ)": rng(3 * EXT_FEE),
        "pecas das 2 placas principais": rng(f2_main_parts),
        "pecas das 10 reguas montadas": rng(10 * ruler_one_12),
        "SMT e nitrogenio x2 (est.)": rng(2 * SMT_N2),
        "cabos SH 6 vias 8 un. (est.)": rng(3, 8),
        "parafusos/porcas M2, pes (est.)": rng(6, 12),
        "impressao do case F2 (MJF, design: FIT_CHECK 12.x)": rng(51.2),
    }
    def tot(d, keys=None):
        return (round(sum(v[0] for k, v in d.items() if keys is None or k in keys), 2),
                round(sum(v[1] for v in d.values()), 2))
    com = (round(sum(v[0] for v in common.values()), 2), round(sum(v[1] for v in common.values()), 2))
    res["comum"] = {k: v for k, v in common.items()}
    res["F1"] = {k: v for k, v in f1.items()}
    res["F2"] = {k: v for k, v in f2.items()}
    res["tot_F1"] = tot(f1)
    res["tot_F2"] = tot(f2)
    res["tot_comum"] = com
    res["F1_total"] = (round(tot(f1)[0] + com[0], 2), round(tot(f1)[1] + com[1], 2))
    res["F2_total"] = (round(tot(f2)[0] + com[0], 2), round(tot(f2)[1] + com[1], 2))
    for tag, a, b in (("pct_total", res["F2_total"], res["F1_total"]), ("pct_diferenca_so_variavel", res["tot_F2"], res["tot_F1"])):
        res[tag] = {"baixo": round(100 * (a[0] / b[0] - 1), 1), "alto": round(100 * (a[1] / b[1] - 1), 1),
                    "mesmo_cenario_baixo_alto": round(100 * (a[0] + a[1]) / (b[0] + b[1]) * 1 - 100, 1)}
    # module +16 : 4 rulers
    res["modulo_mais16"] = {
        "reguas_no_mesmo_pedido_USD": round(4 * ruler_one_4 + 4 * 8 / 30.0 + 4 * 0.6, 2),
        "pedido_separado_de_12_USD": round(SETUP + STENCIL + 2 * EXT_FEE + SMT_N2 + 10 * ruler_one_12 + 8 + 4 * 0.6, 2),
        "teclas_16_Gateron_USD": round(16 * 25.55 / 28, 2)}
    return res


def escala():
    """R5V4: cost of the whole instrument for 32 / 48 / 64 / 80 keys (F2, minimum JLCPCB order, no freight). Differences from the
    R4V4 table: 32 keys instead of 28 (the 8 rulers already carried 4 sensors each: the electronics do not change, only +4 Gateron keys
    and +4 buttons), the cables line (3-8) replaced by the recommended link D, and larger sizes order whole panels of 5 rulers."""
    base = cost()
    rp = base["regua_pecas_cada_12"]
    f2_lo, f2_hi = base["F2_total"]
    old_cables = base["F2"]["cabos SH 6 vias 8 un. (est.)"]
    f2_lo -= old_cables[0]
    f2_hi -= old_cables[1]
    key_lo, key_hi = 24.5 / 28, 26.6 / 28                 # US$ per KS-20 Orange (V3 page range)
    out = {}
    for keys in (32, 48, 64, 80):
        n_r = keys // 4
        panels = max(2, math.ceil(n_r / 5))               # assembled panels of 5 (JLCPCB minimum: 2)
        ordered = 5 * panels
        d_keys = keys - 28
        lo = f2_lo + d_keys * key_lo + (ordered - 10) * rp
        hi = f2_hi + d_keys * key_hi + (ordered - 10) * rp
        elos = keys // 4 - 4 + 4                           # 4 board links + 4 per extra module
        in_row = 4 * (keys // 16 - 1)
        link_solder = 4.0                                  # 30 AWG wire + flux (est.)
        link_cables_crimp = 4 * 0.6 + 30.0                 # 4 cables made at home: contacts/housings + a crimp tool (est.)
        out[keys] = {"reguas": n_r, "reguas_encomendadas": ordered, "paineis_montados": panels, "elos_na_fileira": in_row,
                     "elos_placa_regua": 4, "juntas_de_solda_D": 10 * in_row,
                     "min_montagem_D": round(4 * 1.5 + 5.0 * in_row), "min_montagem_B": round(5.0 * (in_row + 4)),
                     "sem_ligacao_USD": [round(lo, 2), round(hi, 2)],
                     "D_cabos_em_casa_USD": [round(lo + link_solder + link_cables_crimp, 2), round(hi + link_solder + link_cables_crimp, 2)],
                     "D_cabos_lote50_USD": [round(lo + link_solder + 150.0, 2), round(hi + link_solder + 150.0, 2)],
                     "B_tudo_soldado_USD": [round(lo + link_solder, 2), round(hi + link_solder, 2)],
                     "nota": "caixa/botoes: so o preco de 28 teclas do design (51,2) entra; 32 teclas usam o mesmo case (as 8 reguas ja estavam la); 48/64/80: a pedir ao design"}
    return out


def main():
    OUT["scan"] = scan()
    OUT["escala_R5V4"] = escala()
    OUT["custo"] = cost()
    json.dump(OUT, open(os.path.join(HERE, "calculos_eletronica.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(OUT, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
