"""Writes pcb/PINOS.md: the Slim's RT1062 pin map (Teensy 4.1 pin numbers) and the ball positions that matter for placing the BGA.

    python etutti/hardware/slim/pcb/pinos.py

Reads the nets declared in schematic.py (P1_NETS) and rt1062_balls.json. The firmware sketch pins are checked against this by
etutti/firmware/slim/check_pins.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import schematic as M  # noqa: E402

BALLS = json.load(open(os.path.join(HERE, "rt1062_balls.json")))
NAME2BALL = {v: k for k, v in BALLS.items()}
# Teensy 4.1 pin -> RT1062 pad (from the Teensy 4.1 schematic)
T41 = {0: "GPIO_AD_B0_03", 1: "GPIO_AD_B0_02", 2: "GPIO_EMC_04", 3: "GPIO_EMC_05", 4: "GPIO_EMC_06", 5: "GPIO_EMC_08",
       6: "GPIO_B0_10", 7: "GPIO_B1_01", 8: "GPIO_B1_00", 9: "GPIO_B0_11", 10: "GPIO_B0_00", 11: "GPIO_B0_02",
       12: "GPIO_B0_01", 13: "GPIO_B0_03", 14: "GPIO_AD_B1_02", 15: "GPIO_AD_B1_03", 16: "GPIO_AD_B1_07",
       17: "GPIO_AD_B1_06", 18: "GPIO_AD_B1_01", 19: "GPIO_AD_B1_00", 20: "GPIO_AD_B1_10", 21: "GPIO_AD_B1_11",
       22: "GPIO_AD_B1_08", 23: "GPIO_AD_B1_09", 24: "GPIO_AD_B0_12", 25: "GPIO_AD_B0_13", 26: "GPIO_AD_B1_14",
       27: "GPIO_AD_B1_15"}
PAD2PIN = {v: k for k, v in T41.items()}

FUNC = {
    "CHG_STAT": ("in", "~CHG do BQ24075 (0 = carregando), pull-up 100k"), "PGOOD_N": ("in", "~PGOOD do BQ24075 (0 = USB presente)"),
    "SCAN_DATA_P": ("out", "DADO do 74HC595 das 4 reguas (100 ohm em serie)"), "SCAN_CLK_P": ("out", "CLOCK (SRCLK) das reguas"),
    "SCAN_LATCH_P": ("out", "LATCH (RCLK) das reguas"), "LED_G": ("out PWM", "LED verde"), "LED_R": ("out PWM", "LED vermelho"),
    "I2S_TX": ("I2S", "SAI1 TX_DATA0 -> SGTL5000 DIN"), "KEEP": ("out", "segura o sistema ligado (Q203)"),
    "OUT_R1": ("ADC", "saida analogica da fileira 1 (a mais baixa)"), "OUT_R2": ("ADC", "fileira 2"),
    "OUT_R3": ("ADC", "fileira 3"), "OUT_R4": ("ADC", "fileira 4 (a mais alta)"),
    "VBAT_S": ("ADC", "VBAT/2 (1M/1M)"), "VOL_W": ("ADC", "cursor do pot de volume (0..3,3 V)"),
    "REG_ADC": ("ADC", "escada da chave de 7 posicoes"), "SW_S": ("ADC", "estado do knob: SWV/2 (>= 1,0 V = ligado)"),
    "I2C_SDA": ("I2C", "Wire SDA (SGTL5000 0x0A)"), "I2C_SCL": ("I2C", "Wire SCL"), "I2S_LRCLK": ("I2S", "LRCLK"),
    "I2S_BCLK": ("I2S", "BCLK"), "AUD_MCLK_P": ("I2S", "MCLK 11,3 MHz (100 ohm em serie)"),
}


def main():
    rows = []
    for ball_name, net in M.P1_NETS.items():
        if net in FUNC:
            pad = ball_name
            rows.append((PAD2PIN.get(pad, 99), net, pad, NAME2BALL[pad], FUNC[net]))
    rows.sort()
    L = ["# eTutti Slim · mapa de pinos (R1SL, etapa 1)", "",
         "Contrato entre a eletronica e a programacao. Numeracao da Teensy 4.1 (`teensy:avr:teensy41`); o processador e o RT1062 chip-down da propria placa. "
         "Gerado por `pcb/pinos.py` a partir de `pcb/schematic.py`; conferido contra o sketch por `etutti/firmware/slim/check_pins.py`.", "",
         "## Pinos usados", "", "| Pino | Rede | Pad RT1062 | Bola | Tipo | Funcao |", "|---:|---|---|---|---|---|"]
    for pin, net, pad, ball, (kind, what) in rows:
        L.append("| %d | %s | %s | %s | %s | %s |" % (pin, net, pad, ball, kind, what))
    L += ["", "Pinos de ADC das 4 linhas OUT: 14, 15, 26, 27 (cada um pertence aos dois conversores, ADC1 e ADC2: leitura em paralelo de duas fileiras de cada vez).",
          "Livres para o futuro: 6-9, 11, 12, 17, 28+ (so os pinos de borda da Teensy 4.1 que existem como pad: os demais precisam de bolas fora do mapa usado).", "",
          "## Bolas que mandam no posicionamento do BGA (12 x 12, 14 x 14, passo 0,8; colunas 1-14, linhas A-P sem I e O)", ""]
    groups = {
        "USB (D+, D-)": ["USB_OTG1_DP", "USB_OTG1_DN"], "Flash QSPI": [n for n in BALLS.values() if n.startswith("GPIO_SD_B1_") and M.P1_NETS.get(n, "").startswith("FLASH")],
        "Cristal 24 MHz e 32 kHz": ["XTALI", "XTALO", "RTC_XTALI", "RTC_XTALO"],
        "I2S e I2C": [n for n, net in M.P1_NETS.items() if net in ("I2S_TX", "I2S_LRCLK", "I2S_BCLK", "AUD_MCLK_P", "I2C_SDA", "I2C_SCL")],
        "ADC (4 fileiras)": [n for n, net in M.P1_NETS.items() if net in ("OUT_R1", "OUT_R2", "OUT_R3", "OUT_R4")],
        "ADC (knobs, bateria)": [n for n, net in M.P1_NETS.items() if net in ("VOL_W", "REG_ADC", "SW_S", "VBAT_S")],
        "Varredura": [n for n, net in M.P1_NETS.items() if net in ("SCAN_DATA_P", "SCAN_CLK_P", "SCAN_LATCH_P")],
        "Bootloader (MKL02)": [n for n, net in M.P1_NETS.items() if net.startswith("BL_") or net in ("PSWITCH", "POR_B")],
        "Energia do DCDC": ["DCDC_LP", "DCDC_IN", "DCDC_IN_Q", "DCDC_SENSE", "DCDC_PSWITCH"],
    }
    L += ["| Grupo | Bolas |", "|---|---|"]
    for g, names in groups.items():
        L.append("| %s | %s |" % (g, ", ".join("%s (%s)" % (NAME2BALL[n], n.replace("GPIO_", "")) for n in names if n in NAME2BALL)))
    def side(ball):
        r, c = ball[0], int(ball[1:])
        s = []
        if r in "ABC": s.append("N")
        if r in "LMNP": s.append("S")
        if c <= 3: s.append("O")
        if c >= 12: s.append("L")
        return "".join(s) or "centro"
    sides = {}
    for g, names in groups.items():
        for n in names:
            if n in NAME2BALL:
                sides.setdefault(g, set()).add(side(NAME2BALL[n]))
    L += ["", "Lado da matriz (N = linhas A-C, S = L-P, O = colunas 1-3, L = 12-14; as letras cardeais valem para o desenho do esquema do NXP, nao para a placa; "
          "a orientacao final sai do posicionamento): " + "; ".join("%s: %s" % (g, "/".join(sorted(v))) for g, v in sides.items()), "",
          "## Notas", "",
          "- ONOFF e deixado sem ligacao (a Teensy 4.1 sem botao); PMIC_ON_REQ tem 100 k para GND; o 3,3 V nao depende dele (sobe com o OUT do BQ24075).",
          "- Bolas SD_B1_05 (N3) e EMC_23 (G2) sem ligacao, como no Viaggio; sem PSRAM (pinos 48-54 livres).",
          "- A SPEC pede o MIMXRT1062DVL6B (LCSC C2847497, 64 em estoque), que e o BGA **10 x 10 mm de 0,65 mm**; o mapa de bolas daqui e o do **12 x 12 mm de 0,8 mm (DVJ6B**, LCSC C3216699, 1 em estoque). "
          "Os nomes das bolas sao os mesmos nos dois (conferir na NXP); so o footprint muda. Decisao do J: ver `ELETRONICA.md`.", ""]
    open(os.path.join(HERE, "PINOS.md"), "w", encoding="utf-8").write("\n".join(L))
    print("PINOS.md: %d pinos" % len(rows))


if __name__ == "__main__":
    main()
