import math
import uuid

def uid():
    return str(uuid.uuid4())

def generate_irp_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    """
    Generates a 14.0mm circular Interdigitated Resistive Pad (IRP) on F.Cu
    with exposed F.Mask (for ENIG gold contact with Velostat/conductive silicone)
    and a 14.0mm silkscreen guide circle.
    """
    lines = [
        f'  (footprint "eTutti:IRP_14mm_Circle" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.5 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 0 0 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.2 1.2) (thickness 0.2))))',
        # Outer 14.0mm Silkscreen Ring (Radius = 7.0mm)
        f'    (fp_circle (center 0 0) (end 7.0 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        # Exposed Solder Mask Circle (Radius = 6.8mm) so gold fingers are bare on top
        f'    (fp_circle (center 0 0) (end 6.8 0) (stroke (width 0.0) (type solid)) (fill solid) (layer "F.Mask") (uuid "{uid()}"))',
    ]

    # Create interdigitated horizontal fingers inside the 13.0mm active circle
    # Odd fingers = Pad 1 (+3V3), Even fingers = Pad 2 (KEY_SIG)
    finger_spacing = 0.8  # mm between interdigitated fingers
    radius = 6.2
    y_steps = [round(-5.6 + i * finger_spacing, 3) for i in range(15)]

    for idx, fy in enumerate(y_steps):
        half_chord = math.sqrt(max(0.0, radius**2 - fy**2)) - 0.5
        if half_chord <= 1.0:
            continue
        if idx % 2 == 0:
            # Connected to left bus (+3V3, Pad 1)
            cx = -0.3
            w = (half_chord * 2) - 0.6
            pad_num = "1"
            net_str = f'(net {net_vcc_idx} "+3V3")'
        else:
            # Connected to right bus (Signal to Mux, Pad 2)
            cx = 0.3
            w = (half_chord * 2) - 0.6
            pad_num = "2"
            net_str = f'(net {net_sig_idx} "KEY_SIG_{ref[3:]}")'

        lines.append(
            f'    (pad "{pad_num}" smd rect (at {cx:.3f} {fy:.3f}) (size {w:.3f} 0.35) (layers "F.Cu" "F.Mask") {net_str} (uuid "{uid()}"))'
        )

    # Left & Right vertical spine buses + Thru-vias to B.Cu routing
    lines.append(f'    (pad "1" thru_hole circle (at -6.2 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 6.2 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_sig_idx} "KEY_SIG_{ref[3:]}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_2pad(ref, val, x, y, pitch, w, h, net1, net2):
    return f"""  (footprint "eTutti:SMD_0805" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -1.5 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (property "Value" "{val}" (at 0 1.5 0) (layer "F.Fab") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "1" smd rect (at {-pitch/2:.3f} 0) (size {w:.2f} {h:.2f}) (layers "F.Cu" "F.Paste" "F.Mask") {net1} (uuid "{uid()}"))
    (pad "2" smd rect (at {pitch/2:.3f} 0) (size {w:.2f} {h:.2f}) (layers "F.Cu" "F.Paste" "F.Mask") {net2} (uuid "{uid()}"))
  )"""

def generate_ic_box(ref, val, x, y, box_w, box_h, pins_per_side, pitch, net_map):
    lines = [
        f'  (footprint "eTutti:{val}" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.5:.2f} 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'    (property "Value" "{val}" (at 0 {box_h/2 + 1.5:.2f} 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
    ]
    start_y = -((pins_per_side - 1) * pitch) / 2.0
    for i in range(pins_per_side):
        p_left = str(i + 1)
        p_right = str((pins_per_side * 2) - i)
        py = start_y + i * pitch
        n_left = net_map.get(p_left, "")
        n_right = net_map.get(p_right, "")
        lines.append(f'    (pad "{p_left}" smd rect (at {-box_w/2:.3f} {py:.3f}) (size 1.4 0.6) (layers "F.Cu" "F.Paste" "F.Mask") {n_left} (uuid "{uid()}"))')
        lines.append(f'    (pad "{p_right}" smd rect (at {box_w/2:.3f} {py:.3f}) (size 1.4 0.6) (layers "F.Cu" "F.Paste" "F.Mask") {n_right} (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def build_pcb():
    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 75.0
    KEY_ORIGIN_Y = 24.25
    BOARD_W = 227.40
    BOARD_H = 98.00

    # Define Master Nets
    net_names = [
        "", "GND", "+3V3", "+1V8_CODEC", "+5V_USB", "+VBAT", "+VBAT_SW",
        "USB_D_P", "USB_D_N", "USB_CC1", "USB_CC2",
        "I2S_TX", "I2S_RX", "I2S_LRCLK", "I2S_BCLK", "I2S_MCLK",
        "I2C_SDA", "I2C_SCL", "HP_L", "HP_R", "HP_VGND", "MIC_IN", "MIC_BIAS",
        "MUX_S0", "MUX_S1", "MUX_S2", "MUX_S3", "MUX1_OUT", "MUX2_OUT",
        "VOL_ADC", "ENC_A", "ENC_B", "USER_LED"
    ]
    for i in range(1, 29):
        net_names.append(f"KEY_SIG_{i}")

    net_idx = {name: i for i, name in enumerate(net_names)}
    def net_tag(name):
        return f'(net {net_idx[name]} "{name}")'

    out = [
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator")',
        '  (general (thickness 1.6))',
        '  (paper "A3")',
        '  (layers',
        '    (0 "F.Cu" signal)',
        '    (29 "In1.Cu" power)',
        '    (30 "In2.Cu" power)',
        '    (31 "B.Cu" signal)',
        '    (9 "F.Adhes" user "F.Adhesive")',
        '    (11 "B.Adhes" user "B.Adhesive")',
        '    (13 "F.Paste" user)',
        '    (15 "B.Paste" user)',
        '    (5 "F.SilkS" user "F.Silkscreen")',
        '    (7 "B.SilkS" user "B.Silkscreen")',
        '    (1 "F.Mask" user)',
        '    (3 "B.Mask" user)',
        '    (25 "Edge.Cuts" user)',
        '    (31 "F.CrtYd" user "F.Courtyard")',
        '    (35 "F.Fab" user)',
        '  )',
        '  (setup (pad_to_mask_clearance 0))'
    ]

    for i, n in enumerate(net_names):
        out.append(f'  (net {i} "{n}")')

    # 1. Board Outline (Edge.Cuts)
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    # 2. Left Control Bay Modules (MicroMod M.2, SGTL5000, Audio Jacks, USB-C, Controls, Battery)
    # MicroMod M.2 Socket + 22x22mm Processor Keepout Box
    out.append(generate_ic_box("U_MM", "SparkFun_MicroMod_M2_Socket", 32.0, 18.0, 22.0, 22.0, 12, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }))

    # SGTL5000 Audio Codec (U_CODEC) + AP7313-18 1.8V LDO (U_1V8)
    out.append(generate_ic_box("U_CODEC", "SGTL5000_QFN20", 52.0, 18.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_2pad("U_1V8", "AP7313_1.8V_LDO", 52.0, 25.0, 2.0, 1.0, 1.2, net_tag("+3V3"), net_tag("+1V8_CODEC")))
    out.append(generate_smd_2pad("C_1V8", "100nF", 52.0, 28.0, 1.8, 1.0, 1.2, net_tag("+1V8_CODEC"), net_tag("GND")))

    # Left Edge Ports: 3.5mm Headphone Out (J_HP), 3.5mm Mic In (J_MIC), Single USB-C (J_USBC)
    out.append(generate_ic_box("J_HP", "AudioJack_3.5mm_Stereo_Out", 6.0, 12.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }))
    out.append(generate_ic_box("J_MIC", "AudioJack_3.5mm_Mic_In", 6.0, 22.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }))
    out.append(generate_ic_box("J_USBC", "USB_C_Receptacle", 4.5, 33.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }))
    out.append(generate_smd_2pad("R_CC1", "5.1k", 12.0, 31.0, 1.8, 1.0, 1.2, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_2pad("R_CC2", "5.1k", 12.0, 35.0, 1.8, 1.0, 1.2, net_tag("USB_CC2"), net_tag("GND")))

    # Center-Left User Controls: Volume Knob (RV1), Selector Knob (SW_ENC1), Status LED (D1)
    out.append(generate_ic_box("RV1", "Volume_Pot_10k", 20.0, 52.0, 10.0, 10.0, 2, 5.0, {
        "1": net_tag("GND"), "2": net_tag("VOL_ADC"), "3": net_tag("+3V3")
    }))
    out.append(generate_ic_box("SW_ENC1", "Selector_Rotary_Encoder", 44.0, 52.0, 12.0, 12.0, 2, 5.0, {
        "1": net_tag("ENC_A"), "2": net_tag("GND"), "3": net_tag("ENC_B")
    }))
    out.append(generate_smd_2pad("D1", "Status_LED", 32.0, 43.0, 1.8, 1.0, 1.2, net_tag("USER_LED"), net_tag("GND")))
    out.append(generate_smd_2pad("R1", "330R", 32.0, 46.5, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("USER_LED")))

    # Bottom-Left 1000mAh LiPo Battery Outline + Charger (U6) + JST-PH (J_BAT)
    out.append(generate_smd_2pad("J_BAT", "JST_PH_1000mAh_LiPo", 14.0, 66.0, 2.0, 1.2, 1.8, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_2pad("U6", "MCP73831_Charger", 25.0, 66.0, 2.0, 1.2, 1.5, net_tag("+5V_USB"), net_tag("+VBAT")))
    out.append(f'  (gr_rect (start 8.0 63.0) (end 58.0 95.0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))')

    # Multiplexers U4 (Keys 1-16) & U5 (Keys 17-28)
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box("U4", "CD74HC4067_Mux1", 65.0, 36.0, 7.5, 15.4, 12, 1.27, mux1_map))
    out.append(generate_ic_box("U5", "CD74HC4067_Mux2", 65.0, 66.0, 7.5, 15.4, 12, 1.27, mux2_map))

    # 3. 28-Key C-Griff Circular 14.0mm Interdigitated Resistive Pads (IRP1..IRP28) & 10k Pull-Downs
    notes = [
        "A3", "C4", "D#4", "F#4", "A4", "C5",
        "G#3", "B3", "D4", "F4", "G#4", "B4", "D5",
        "G3", "A#3", "C#4", "E4", "G4", "A#4", "C#5", "E5",
        "A3", "C4", "D#4", "F#4", "A4", "C5", "D#5"
    ]
    rows = [
        {"count": 6, "x_offset": 1.0 * PITCH_X},
        {"count": 7, "x_offset": 0.5 * PITCH_X},
        {"count": 8, "x_offset": 0.0 * PITCH_X},
        {"count": 7, "x_offset": 0.5 * PITCH_X},
    ]

    key_idx = 1
    for r_idx, row in enumerate(rows):
        y_mm = KEY_ORIGIN_Y + (r_idx * PITCH_Y)
        for c_idx in range(row["count"]):
            x_mm = KEY_ORIGIN_X + row["x_offset"] + (c_idx * PITCH_X)
            sig_name = f"KEY_SIG_{key_idx}"
            out.append(generate_irp_footprint(f"IRP{key_idx}", notes[key_idx - 1], x_mm, y_mm, net_idx["+3V3"], net_idx[sig_name]))
            # Place 10k Pull-Down Resistor on Back Layer / Edge of Pad
            out.append(generate_smd_2pad(f"R_PD{key_idx}", "10k", x_mm, y_mm + 8.0, 1.8, 0.9, 1.0, net_tag(sig_name), net_tag("GND")))
            key_idx += 1

    # 4. Pre-configured Inner Copper Zones (In1.Cu = GND, In2.Cu = +3V3)
    out.append(f"""  (zone (net {net_idx["GND"]}) (net_name "GND") (layer "In1.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 0.5) (xy {BOARD_W-0.5:.2f} 0.5) (xy {BOARD_W-0.5:.2f} {BOARD_H-0.5:.2f}) (xy 0.5 {BOARD_H-0.5:.2f})))
  )""")
    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 0.5) (xy {BOARD_W-0.5:.2f} 0.5) (xy {BOARD_W-0.5:.2f} {BOARD_H-0.5:.2f}) (xy 0.5 {BOARD_H-0.5:.2f})))
  )""")

    out.append(")")

    with open("eTutti_Student.kicad_pcb", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Created 'eTutti_Student.kicad_pcb' successfully! Double-click it to open in KiCad.")

if __name__ == "__main__":
    build_pcb()