"""eTuttino Pocket -- power budget and battery life (owner: eletrônica).

Stdlib only:  python etutti/hardware/pocket/pcb/power_budget.py
Rewrites etutti/hardware/pocket/POWER.md (Portuguese). Do not edit POWER.md
by hand: change the numbers here.

Replaces the budget that layout.py wrote for SPEC v1. Every figure is either
MEASURED (on J's Teensy 4.0 + Audio Board Rev D, 17 Oct 2026, throwaway
sketch built from etutti/firmware/etutti_synth with usb=serialmidi), from a
DATASHEET (link in ELETRONICA.md), or an ESTIMATE marked (conferir).
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
POWER_MD = os.path.join(os.path.dirname(HERE), "POWER.md")

N_KEYS = 28
BATT_MAH = 1000
V_BATT = 3.7            # average over the discharge
DERATE = 0.85           # usable fraction: cut-off at ~3.3 V, ageing, cold
V_RAIL = 3.3
BATT_OPTIONS = (1000, 1200)   # mAh: 603450 3-wire packs come as 1000 or 1200 (conferir)
I_IN_MAX = 500          # mA, BQ24074 USB500 mode
I_CHG = 500             # mA, fast-charge current
K_ISET = 890            # A*ohm (datasheet)
V_OUT_USB = 4.4         # V, BQ24074 OUT with USB present
CV_TAPER_H = 0.5        # h, constant-voltage tail (estimate)
R_CHG_LED = 1000        # ohm, charge light from VBUS 5 V
EFF_CONV = {"typ": 0.90, "max": 0.86}   # TPS63001 at 3.0-4.2 V in, 3.3 V / 0.1-0.3 A out (datasheet curve, conferir)

# ---- MEASURED on the Teensy (scratchpad pwrtest, 2.5 s per point) ----
# clock MHz: (audio CPU % with 8 voices x 4 reeds + reverb, 28-key/2-mux scan us avg)
MEASURED = {
    600: (8.5, 217), 528: (9.6, 226), 450: (11.3, 231), 396: (12.9, 235),
    300: (17.0, 249), 240: (21.2, 266), 198: (25.8, 286), 150: (33.7, 344),
}
SETTLE_US = 3.0                     # mux settle per channel (sketch)
READ_US_600 = (217 - 14 * SETTLE_US) / 28   # one analogRead at 600 MHz, ~6.25 us

# ---- Teensy 4.0 current vs ARM clock: ESTIMATE (conferir: medir) ----
# PJRC publishes ~100 mA at 600 MHz only. Model: I = 30 mA (USB, PLLs, flash,
# peripherals) + k * f * Vcore^2, Vcore from set_arm_clock() (Teensyduino
# 1.62 clockspeed.c), k fitted to 100 mA at 600 MHz.
def vcore(mhz):
    if mhz <= 240:
        return (950 + (mhz * 1e6 // 32e6) * 25) / 1000
    if mhz < 460:
        return 1.150
    if mhz <= 528:
        return 1.175
    return 1.250

K_CORE = 70.0 / (600 * vcore(600) ** 2)

def teensy_ma(mhz):
    return 30.0 + K_CORE * mhz * vcore(mhz) ** 2

# ---- Hall sensors (datasheets) ----
SENSORS = {
    "DRV5056A3": {"typ": 6.0, "max": 10.0, "ton_typ": 150, "ton_max": 300},
    "TMAG5253BA3": {"typ": 2.6, "max": 5.0, "ton_typ": 20, "ton_max": 45},
    "TMAG5253UA5": {"typ": 2.4, "max": 4.0, "ton_typ": 55, "ton_max": 130},
}

# ---- speaker amplifier PAM8302A on the battery (datasheet + estimate) ----
AMP_IQ = {"typ": 4.0, "max": 8.0}          # mA, no signal
P_SPK = {"typ": 0.20, "max": 0.50}         # W average into the speaker (conferir: ouvir)
EFF_AMP = {"typ": 0.80, "max": 0.85}       # class D at those levels

AUDIO_MA = {"fone": {"typ": 20.0, "max": 40.0},      # SGTL5000 driving 32 ohm phones (conferir)
            "alto-falante": {"typ": 12.0, "max": 20.0}}  # HP out only feeds the amp input (conferir)
LED_MA = {"typ": 2.0, "max": 8.0}          # one colour, PWM-dimmed
MUX_MA = {"typ": 0.1, "max": 0.2}          # 2 x CD74HC4067


def sensor_duty(name, gated):
    """Fraction of time a sensor is powered, and the scan period (us)."""
    s = SENSORS[name]
    scan = MEASURED[600][1]
    if not gated:
        return 1.0, scan
    # Two groups by the S3 address bit (channels 0-7 / 8-15 of both muxes),
    # each enabled only while it is read; wait ton_max after switching.
    group_read = 8 * (SETTLE_US + 2 * READ_US_600)
    period = 2 * (s["ton_max"] + group_read)
    return 0.5, period


SCENARIOS = [
    # key, label, sensor, gated, clock MHz, amp off in silence
    ("v1", "v1 (hoje): DRV5056, 600 MHz", "DRV5056A3", False, 600),
    ("tmag", "TMAG5253BA3 sempre ligado, 600 MHz", "TMAG5253BA3", False, 600),
    ("tmag_g", "TMAG5253BA3 por grupo (S3), 600 MHz", "TMAG5253BA3", True, 600),
    ("tmag_g396", "TMAG5253BA3 por grupo, 396 MHz", "TMAG5253BA3", True, 396),
    ("tmag_g240", "TMAG5253BA3 por grupo, 240 MHz", "TMAG5253BA3", True, 240),
]
RECOMMENDED = "tmag_g396"


def rail_rows(sensor, gated, mhz, out):
    duty, _ = sensor_duty(sensor, gated)
    s = SENSORS[sensor]
    t = teensy_ma(mhz)
    rows = [
        (f"Teensy 4.0 a {mhz} MHz (estimativa, conferir)", t, t * 1.2),
        (f"Audio Board (SGTL5000), saída {out} (conferir)", AUDIO_MA[out]["typ"], AUDIO_MA[out]["max"]),
        (f"{N_KEYS} sensores {sensor}" + (" ligados 50 % do tempo" if gated else ""),
         N_KEYS * s["typ"] * duty, N_KEYS * s["max"] * duty),
        ("2 x CD74HC4067", MUX_MA["typ"], MUX_MA["max"]),
        ("LED (uma cor, PWM)", LED_MA["typ"], LED_MA["max"]),
    ]
    return rows


def battery_w(rows, out, case):
    i_rail = sum(r[1] if case == "typ" else r[2] for r in rows)
    p = i_rail / 1000 * V_RAIL / EFF_CONV[case]
    if out == "alto-falante":
        p += P_SPK[case] / EFF_AMP[case] + AMP_IQ[case] / 1000 * V_BATT
    return i_rail, p


def hours(p_w):
    return BATT_MAH / 1000 * V_BATT * DERATE / p_w


def velocity_error(t_ms, dt_us):
    """Velocity units (of 127) moved by a timing error dt on a strike that
    takes t_ms between VEL_START and NOTE_ON_AT (firmware log map 1-80 ms)."""
    fast, slow = 1.0, 80.0
    x = lambda t: max(0.0, min(1.0, (math.log(slow) - math.log(max(t, 0.1))) / (math.log(slow) - math.log(fast))))
    return abs(126 * (x(t_ms) - x(t_ms + dt_us / 1000)))


def f(v, d=1):
    return f"{v:.{d}f}".replace(".", ",")


def main():
    L = []
    w = L.append
    w("# eTuttino Pocket · orçamento de energia")
    w("")
    w("Gerado por `pcb/power_budget.py` (eletrônica; não editar à mão). SPEC v3, tarefa E2 "
      "e E2b (sensor TMAG5253BA3 por grupo e 396 MHz decididos na v3; o clock final sai da medição da P1). "
      "A placa usa o TPS63001 (3,3 V fixo, LCSC C28060) no lugar do TPS63802: o encapsulamento VSON-HR "
      "do TPS63802 não tem desenho conferido na biblioteca do KiCad.")
    w("")
    w(f"Bateria LiPo 1S de **{BATT_MAH} mAh** (3,7 V médios), capacidade útil {int(DERATE * 100)} % "
      f"(corte em ~3,3 V, envelhecimento, frio) = {f(BATT_MAH / 1000 * V_BATT * DERATE, 2)} Wh.")
    w(f"Trilho único de 3,3 V pelo buck-boost TPS63001 (3,3 V fixo; eficiência {int(EFF_CONV['typ'] * 100)} % típica, "
      f"{int(EFF_CONV['max'] * 100)} % no pior caso, conferir). O amplificador do alto-falante (PAM8302A) vai "
      "direto na bateria (saída do carregador), fora do trilho de 3,3 V.")
    w("")
    w("Origem de cada número: **medido** no Teensy 4.0 + Audio Board Rev D do J (17 out 2026), "
      "**datasheet**, ou **estimativa (conferir)**.")
    w("")

    w("## Medido no Teensy do J (17 out 2026)")
    w("")
    w("Sketch descartável feito do `etutti_synth` atual (usb=serialmidi): `set_arm_clock()` em cada "
      "frequência, acorde de 8 notas com as 4 palhetas e reverb por 2,5 s, `AudioProcessorUsageMax()`, "
      "e o tempo de uma leitura de 28 teclas em 2 multiplexadores (14 canais × 2 `analogRead`, 3 µs de "
      "acomodação por canal, como no sketch). Sem placa de teclas: o tempo de leitura não depende do sensor.")
    w("")
    w("| Clock ARM | CPU do áudio (máx.) | leitura de 28 teclas | Teensy (estimativa) |")
    w("|---:|---:|---:|---:|")
    for mhz, (cpu, scan) in MEASURED.items():
        w(f"| {mhz} MHz | {f(cpu)} % | {scan} µs | {f(teensy_ma(mhz), 0)} mA |")
    w("")
    w("- A CPU do áudio escala com 1/clock: o motor de palhetas de hoje (8 vozes × 4 palhetas + reverb) "
      "usa só 8,5 % a 600 MHz e 34 % a 150 MHz. A 3ª palheta de 8' do Musette (P1) acrescenta ~25 % ao custo "
      "dos osciladores (estimativa).")
    w("- O ADC fica mais lento com o clock (o barramento IPG cai junto), mas a leitura de 28 teclas continua "
      "abaixo de 0,35 ms em todas as frequências.")
    w("- A corrente do Teensy **não foi medida** (não há medidor de corrente no PC do J). A coluna da direita "
      "é um modelo: 30 mA fixos + parcela dinâmica ∝ f·V², com a tensão do núcleo que o `set_arm_clock()` "
      "usa, ajustado aos ~100 mA a 600 MHz que a PJRC publica. Medir no protótipo.")
    w("")

    w("## Consumidores por cenário (mA no trilho de 3,3 V)")
    w("")
    for key, label, sensor, gated, mhz in SCENARIOS:
        if key not in ("v1", RECOMMENDED):
            continue
        tag = " (recomendado)" if key == RECOMMENDED else ""
        w(f"### {label}{tag}")
        w("")
        w("| Consumidor | típ. fone | máx. fone | típ. alto-falante | máx. alto-falante |")
        w("|---|---:|---:|---:|---:|")
        rf = rail_rows(sensor, gated, mhz, "fone")
        rs = rail_rows(sensor, gated, mhz, "alto-falante")
        for a, b in zip(rf, rs):
            name = a[0].replace(", saída fone", "")
            w(f"| {name} | {f(a[1])} | {f(a[2])} | {f(b[1])} | {f(b[2])} |")
        tf = (sum(r[1] for r in rf), sum(r[2] for r in rf))
        ts = (sum(r[1] for r in rs), sum(r[2] for r in rs))
        w(f"| **Total no trilho** | **{f(tf[0])}** | **{f(tf[1])}** | **{f(ts[0])}** | **{f(ts[1])}** |")
        w("")
    w(f"Alto-falante (na bateria): {f(P_SPK['typ'], 2)} W médios típicos / {f(P_SPK['max'], 2)} W no pior caso "
      f"(volume alto), classe D com {int(EFF_AMP['typ'] * 100)}–{int(EFF_AMP['max'] * 100)} % de eficiência, "
      f"mais {f(AMP_IQ['typ'], 0)}–{f(AMP_IQ['max'], 0)} mA de repouso do PAM8302A (datasheet). "
      "Os watts médios são estimativa (conferir com o alto-falante escolhido, de ouvido).")
    w("")

    w(f"## Autonomia tocando sem parar, bateria de {BATT_MAH} mAh")
    w("")
    w("| Cenário | fone típ. | fone pior | alto-falante típ. | alto-falante pior |")
    w("|---|---:|---:|---:|---:|")
    results = {}
    for key, label, sensor, gated, mhz in SCENARIOS:
        cells = []
        for out in ("fone", "alto-falante"):
            rows = rail_rows(sensor, gated, mhz, out)
            for case in ("typ", "max"):
                _, p = battery_w(rows, out, case)
                h = hours(p)
                results[(key, out, case)] = h
                cells.append(f"{f(h)} h")
        bold = "**" if key == RECOMMENDED else ""
        w(f"| {bold}{label}{bold} | " + " | ".join(f"{bold}{c}{bold}" for c in cells) + " |")
    w("")
    w("\"Pior\" = todos os consumidores no máximo do datasheet ao mesmo tempo e o conversor na pior "
      "eficiência; na prática fica entre as duas colunas.")
    w("")

    w("## Efeito do liga/desliga dos sensores na velocidade")
    w("")
    w("Os sensores de cada grupo (canais 0–7 e 8–15 dos dois multiplexadores, escolhidos pelo bit S3 do "
      "endereço) só ficam ligados enquanto o seu grupo é lido; depois de trocar de grupo a firmware espera "
      "o tempo de ligar (tON máximo do datasheet). Leitura de um grupo: 8 canais × (3 µs + 2 leituras de "
      f"{f(READ_US_600, 2)} µs) = {f(8 * (SETTLE_US + 2 * READ_US_600), 0)} µs a 600 MHz (medido).")
    w("")
    w("| Sensor e modo | tON máx. | período de leitura | leituras por tecla/s | amostras numa batida de 1 ms | erro de velocidade, batida de 1 ms | erro, batida de 10 ms |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for name, gated in (("DRV5056A3", False), ("DRV5056A3", True), ("TMAG5253BA3", False),
                        ("TMAG5253BA3", True), ("TMAG5253UA5", True)):
        _, period = sensor_duty(name, gated)
        err = 0.25 * period          # interpolated crossing, nonlinear travel: ~1/4 of a period (estimate)
        w(f"| {name} {'por grupo' if gated else 'sempre ligado'} | {SENSORS[name]['ton_max']} µs | "
          f"{f(period, 0)} µs | {f(1e6 / period, 0)} | {f(1000 / period)} | "
          f"±{f(velocity_error(1.0, err), 0)} | ±{f(velocity_error(10.0, err), 0)} |")
    w("")
    w("Erro de velocidade em unidades MIDI (1–127), com o mapa logarítmico da firmware (1 ms = 127, 80 ms = 1) "
      "e um erro de tempo de ~¼ do período por cruzamento (interpolação linear entre leituras; estimativa). "
      "Com o DRV5056 (tON até 300 µs) o liga/desliga por grupo derruba a leitura para ~1,2 kHz: a batida "
      "mais rápida cabe em ~1 amostra. **Não recomendado com o DRV5056.** Com o TMAG5253BA3 (tON ≤ 45 µs) "
      "a leitura fica em ~3 kHz e o erro é pequeno.")
    w("")

    w("## Parado, desligamento automático e desligado")
    w("")
    t24 = 20.0
    idle_rail = teensy_ma(396) + AUDIO_MA["alto-falante"]["typ"] + N_KEYS * SENSORS["TMAG5253BA3"]["typ"] * 0.15 + 1.0
    sleep_rail = t24 + 2.0 + N_KEYS * SENSORS["TMAG5253BA3"]["typ"] * 0.02
    idle_w = idle_rail / 1000 * V_RAIL / EFF_CONV["typ"]
    sleep_w = sleep_rail / 1000 * V_RAIL / 0.85
    w("| Estado | consumo | a bateria cheia dura |")
    w("|---|---:|---:|")
    w(f"| Ligado, sem tocar (amplificador desligado, sensores lidos a ~500 Hz com liga/desliga geral) | "
      f"~{f(idle_rail, 0)} mA no trilho | ~{f(hours(idle_w), 0)} h |")
    w(f"| Desligamento automático \"leve\" (Teensy a 24 MHz, codec desligado, sensores a 20 Hz; acorda numa tecla) | "
      f"~{f(sleep_rail, 0)} mA (conferir) | ~{f(hours(sleep_w), 0)} h |")
    w("| Desligamento automático \"de verdade\" (a firmware solta o KEEP e o conversor desliga) | "
      "~10 µA (carregador + divisor) | anos (fica a autodescarga da bateria) |")
    w("| Chave do volume desligada | ~10 µA | anos |")
    w("")
    w("O \"leve\" não é desligado: sozinho, um Pocket esquecido ligado gastaria a bateria em pouco mais de um dia. "
      "Por isso a SPEC v3 usa os dois estágios: leve depois de 15 min, KEEP baixo (desligado de verdade) depois de mais 30.")
    w("")

    w("## Carga pela USB-C")
    w("")
    i_play_rail = sum(r[1] for r in rail_rows("TMAG5253BA3", True, 396, "fone"))
    i_play_out = i_play_rail * V_RAIL / EFF_CONV["typ"] / V_OUT_USB
    w(f"BQ24074 em modo USB500 (EN1 = 1, EN2 = 0): no máximo {I_IN_MAX} mA da USB-C; corrente de carga "
      f"programada {I_CHG} mA (R_ISET = {f(K_ISET / I_CHG, 2)} kΩ, K_ISET = {K_ISET} AΩ; datasheet). Os 5,1 kΩ "
      "nos CC da USB-C pedem a corrente padrão da porta (500 mA em USB 2.0, até 1,5–3 A em carregadores "
      "USB-C), então qualquer cabo C-C ou A-C carrega.")
    w("")
    w("| Situação | corrente na bateria | carga completa (estimativa, conferir) |")
    w("|---|---:|---:|")
    for mah in BATT_OPTIONS:
        t_off = mah / I_CHG + CV_TAPER_H
        i_left = max(0.0, I_IN_MAX - i_play_out)
        i_bat = min(I_CHG, i_left)
        t_on = mah / i_bat + CV_TAPER_H
        w(f"| {mah} mAh, desligado | {I_CHG} mA | ~{f(t_off)} h |")
        w(f"| {mah} mAh, tocando com fone (o aparelho tira ~{f(i_play_out, 0)} mA da OUT a 4,4 V) | ~{f(i_bat, 0)} mA | ~{f(t_on)} h |")
    w("")
    w(f"Fase de tensão constante no fim da carga: +{f(CV_TAPER_H)} h (estimativa). A carga para fora de 0–50 °C "
      "(NTC de 10 kΩ, B 3435, no TS: corrente de 75 µA, desliga a 2,1 V = 28 kΩ ≈ 0 °C e a 0,3 V = 4 kΩ ≈ 50 °C; datasheet).")
    w("")
    w(f"**Luz de carga** (CHG do BQ24074 → P-MOSFET → {R_CHG_LED} Ω → diodo → vermelho do LED): "
      f"~{f((5.0 - 0.35 - 1.9) / R_CHG_LED * 1000, 1)} mA, tirados da USB, não da bateria. Acende também desligado.")
    w("")
    w("## Autonomia com outra capacidade")
    w("")
    w("A bateria de 3 fios que se acha em 603450 às vezes é de 1200 mAh (mesmo tamanho). Cenário recomendado, típico:")
    w("")
    w("| Bateria | com fone | com alto-falante |")
    w("|---|---:|---:|")
    for mah in BATT_OPTIONS:
        cells = []
        for out in ("fone", "alto-falante"):
            _, p = battery_w(rail_rows("TMAG5253BA3", True, 396, out), out, "typ")
            cells.append(f"{f(hours(p) * mah / BATT_MAH)} h")
        w(f"| {mah} mAh | " + " | ".join(cells) + " |")
    w("")

    w("## Para conferir no protótipo")
    w("")
    w("1. Corrente real do trilho de 3,3 V com o Teensy a 600, 396 e 240 MHz (multímetro em série com a bateria).")
    w("2. Corrente dos 28 sensores e o campo do ímã do Gateron no fundo do curso (escolhe TMAG5253UA5 ou BA3).")
    w("3. Volume confortável no alto-falante: potência média real (tensão RMS na bobina).")
    w("4. Eficiência do TPS63001 com a carga real.")
    w("5. Tempo de carga real e a temperatura da bateria tocando enquanto carrega.")
    w("")
    with open(POWER_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))

    for (key, out, case), h in sorted(results.items()):
        print(f"{key:10s} {out:13s} {case}: {h:.2f} h")
    print("wrote", POWER_MD)


if __name__ == "__main__":
    main()
