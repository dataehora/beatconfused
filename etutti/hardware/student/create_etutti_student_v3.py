import math
import uuid

def uid():
    return str(uuid.uuid4())

def rot_pt(dx, dy, angle_deg):
    """Rotates a local (dx, dy) offset by angle_deg (KiCad CCW convention)."""
    rad = math.radians(-angle_deg)
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry

def generate_irp_tactile_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    """
    14.0mm Circular Interdigitated Resistive Pad (IRP) on F.Cu with:
    - Raised Tactile Embossing Rim (F.Cu + F.Mask + F.SilkS)
    - Conductive C & F root-note tactile textures
    """
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.3 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14))))',
        f'    (property "Value" "{note_name}" (at 0 8.3 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))',
        # Raised Tactile Embossing Rim
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.55) (type solid)) (fill none) (layer "F.Cu") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.65) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.4 0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.1) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',
        # Exposed Bare-Gold Sensing Well
        f'    (fp_circle (center 0 0) (end 6.6 0) (stroke (width 0.0) (type solid)) (fill solid) (layer "F.Mask") (uuid "{uid()}"))',
    ]

    finger_spacing = 0.75
    radius = 6.0
    y_steps = [round(-5.25 + i * finger_spacing, 3) for i in range(15)]

    for idx, fy in enumerate(y_steps):
        half_chord = math.sqrt(max(0.0, radius**2 - fy**2)) - 0.4
        if half_chord <= 1.0:
            continue
        if idx % 2 == 0:
            cx = -0.25
            w = (half_chord * 2) - 0.5
            pad_num = "1"
            net_str = f'(net {net_vcc_idx} "+3V3")'
        else:
            cx = 0.25
            w = (half_chord * 2) - 0.5
            pad_num = "2"
            net_str = f'(net {net_sig_idx} "KEY_SIG_{ref[3:]}")'

        lines.append(
            f'    (pad "{pad_num}" smd rect (at {cx:.3f} {fy:.3f}) (size {w:.3f} 0.32) (layers "F.Cu" "F.Mask") {net_str} (uuid "{uid()}"))'
        )

    if is_c_note:
        for dx, dy in [(0.0, 0.0), (-1.8, 0.0), (1.8, 0.0), (0.0, -1.5), (0.0, 1.5)]:
            lines.append(
                f'    (pad "1" thru_hole circle (at {dx:.2f} {dy:.2f}) (size 0.95 0.95) (drill 0.55) (layers "*.Cu" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
            )
    elif is_f_note:
        for dy in [-1.5, 0.0, 1.5]:
            for dx in [-2.2, -1.1, 0.0, 1.1, 2.2]:
                lines.append(
                    f'    (pad "1" thru_hole circle (at {dx:.2f} {dy:.2f}) (size 0.85 0.85) (drill 0.5) (layers "*.Cu" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
                )

    lines.append(f'    (pad "1" thru_hole circle (at -6.0 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 6.0 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_sig_idx} "KEY_SIG_{ref[3:]}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_2pad_back(ref, val, lcsc, x, y, angle, pitch, w, h, net1, net2):
    """Places 0805 / 2-pad SMD parts on B.Cu at any custom rotation angle."""
    return f"""  (footprint "eTutti:SMD_0805_Back" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -1.4 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.12)) (justify mirror)))
    (property "Value" "{val}" (at 0 1.4 {angle:.1f}) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.12)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (pad "1" smd rect (at {-pitch/2:.3f} 0 {angle:.1f}) (size {w:.2f} {h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {net1} (uuid "{uid()}"))
    (pad "2" smd rect (at {pitch/2:.3f} 0 {angle:.1f}) (size {w:.2f} {h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {net2} (uuid "{uid()}"))
  )"""

def generate_ic_box_back(ref, val, lcsc, x, y, angle, box_w, box_h, pins_per_side, pitch, net_map):
    """Places ICs & Connectors on B.Cu with arbitrary non-orthogonal rotation (e.g. 30°, 32°, 45°)."""
    lines = [
        f'  (footprint "eTutti:{val}_Back" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f} {angle:.1f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.14)) (justify mirror)))',
        f'    (property "Value" "{val}" (at 0 {box_h/2 + 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.14)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))',
    ]
    start_y = -((pins_per_side - 1) * pitch) / 2.0
    for i in range(pins_per_side):
        p_left = str(i + 1)
        p_right = str((pins_per_side * 2) - i)
        py = start_y + i * pitch
        n_left = net_map.get(p_left, "")
        n_right = net_map.get(p_right, "")
        lines.append(f'    (pad "{p_left}" smd rect (at {-box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.3 0.5) (layers "B.Cu" "B.Paste" "B.Mask") {n_left} (uuid "{uid()}"))')
        lines.append(f'    (pad "{p_right}" smd rect (at {box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.3 0.5) (layers "B.Cu" "B.Paste" "B.Mask") {n_right} (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def build_pcb():
    # --- MINIMALIST COMPACT GEOMETRY ---
    PITCH_X = 19.05
    PITCH_Y = 16.50
    EDGE_BUFFER = 11.50        # 7.5mm tactile rim radius + 4.0mm minimal border!
    KEY_ORIGIN_X = 47.00       # Compact 47mm left bay (down from 75mm)
    KEY_ORIGIN_Y = EDGE_BUFFER # 11.50mm from top edge (down from 24.25mm)

    # Row 2 has 8 keys (indices 0..7): rightmost key center is KEY_ORIGIN_X + 7*19.05 = 180.35mm
    BOARD_W = round(KEY_ORIGIN_X + (7 * PITCH_X) + EDGE_BUFFER, 2)  # 191.85 mm (saved 35.5mm!)
    BOARD_H = round(KEY_ORIGIN_Y + (3 * PITCH_Y) + EDGE_BUFFER, 2)  # 72.50 mm  (saved 25.5mm!)

    net_names = [
        "", "GND", "+3V3", "+3V3_ANA", "+1V8_CODEC", "+5V_USB", "+VBAT", "+VBAT_SW",
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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v3_Minimalist")',
        '  (general (thickness 1.6))',
        '  (paper "A4")',
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
        '    (21 "Eco1.User" user "User.Eco1")',
        '    (25 "Edge.Cuts" user)',
        '    (31 "F.CrtYd" user "F.Courtyard")',
        '    (33 "B.CrtYd" user "B.Courtyard")',
        '    (35 "F.Fab" user)',
        '    (37 "B.Fab" user)',
        '  )',
        '  (setup (pad_to_mask_clearance 0))'
    ]

    for i, n in enumerate(net_names):
        out.append(f'  (net {i} "{n}")')

    # 1. Minimalist Board Outline (191.85mm x 72.50mm)
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    # 2. Isolated Analog Audio Island (Upper-Left Corner, X: 0..32mm, Y: 0..26mm)
    # 3.5mm Headphone Out (J_HP) & 3.5mm Mic In (J_MIC)
    out.append(generate_ic_box_back("J_HP", "PJ-320A_3.5mm_HP", "C145898", 5.5, 8.5, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }))
    out.append(generate_ic_box_back("J_MIC", "PJ-320A_3.5mm_MIC", "C145898", 5.5, 17.5, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }))

    # SGTL5000 Codec rotated at 45° right between J_HP/J_MIC and MicroMod I2S pins for ultra-short traces!
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000XNAA3", "C89941", 21.0, 12.5, 45.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }))
    # Ferrite Bead (FB_AUD) isolating +3V3 digital from +3V3_ANA audio rail
    out.append(generate_smd_2pad_back("FB_AUD", "600R_100MHz", "C1002", 28.0, 6.0, -30.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("+3V3_ANA")))
    out.append(generate_smd_2pad_back("U_1V8", "AP7313-18SAG", "C134077", 21.0, 5.5, 0.0, 2.0, 1.0, 1.2, net_tag("+3V3_ANA"), net_tag("+1V8_CODEC")))
    out.append(generate_smd_2pad_back("C_1V8", "100nF", "C49678", 16.0, 5.5, 0.0, 1.8, 1.0, 1.2, net_tag("+1V8_CODEC"), net_tag("GND")))
    out.append(generate_smd_2pad_back("C_ANA", "10uF", "C15850", 21.0, 19.5, 45.0, 1.8, 1.0, 1.2, net_tag("+3V3_ANA"), net_tag("GND")))

    # 3. Non-Orthogonal Rotated MicroMod M.2 (32°) & Multiplexers (30° / -30°) Nestled into Key Stagger
    # MicroMod rotated at 32° so it tucks cleanly parallel to the C-Griff Row 3 / Row 4 diagonal slope
    out.append(generate_ic_box_back("U_MM", "MicroMod_M2_Socket", "C2838503", 38.0, 22.0, 32.0, 22.0, 22.0, 12, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }))
    out.append(generate_smd_2pad_back("R_SDA", "2.2k", "C17520", 28.5, 14.5, 32.0, 1.8, 1.0, 1.2, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_2pad_back("R_SCL", "2.2k", "C17520", 27.0, 17.5, 32.0, 1.8, 1.0, 1.2, net_tag("I2C_SCL"), net_tag("+3V3")))

    # Multiplexer U4 (Keys 1-16) tilted at +30° inside the upper-left key stagger indent (under Row 4/3)
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    # Multiplexer U5 (Keys 17-28) tilted at -30° inside the lower-left key stagger indent (under Row 1/2)
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "CD74HC4067M96", "C70001", 53.5, 13.5, 30.0, 7.5, 15.4, 12, 1.27, mux1_map))
    out.append(generate_smd_2pad_back("C_MUX1", "100nF", "C49678", 48.0, 5.5, 30.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("GND")))

    out.append(generate_ic_box_back("U5", "CD74HC4067M96", "C70001", 44.5, 58.5, -30.0, 7.5, 15.4, 12, 1.27, mux2_map))
    out.append(generate_smd_2pad_back("C_MUX2", "100nF", "C49678", 39.0, 66.5, -30.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("GND")))

    # 4. Left-Edge USB-C, Compact Vertical Knobs, and Back-Under-Key LiPo Battery Placement
    out.append(generate_ic_box_back("J_USBC", "TYPE-C-31-M-12", "C165948", 4.5, 29.0, 0.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }))
    out.append(generate_smd_2pad_back("R_CC1", "5.1k", "C27834", 11.5, 27.0, 45.0, 1.8, 1.0, 1.2, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_2pad_back("R_CC2", "5.1k", "C27834", 11.5, 31.0, -45.0, 1.8, 1.0, 1.2, net_tag("USB_CC2"), net_tag("GND")))

    # Volume Knob (RV1) & Sound Selector Knob (SW_ENC1) stacked ergonomically in the 47mm Left Wing
    out.append(generate_ic_box_back("RV1", "Volume_Pot_10k", "Manual_THT", 14.0, 43.5, 15.0, 10.0, 10.0, 2, 5.0, {
        "1": net_tag("GND"), "2": net_tag("VOL_ADC"), "3": net_tag("+3V3")
    }))
    out.append(generate_ic_box_back("SW_ENC1", "Rotary_Encoder_EC11", "Manual_THT", 16.0, 60.0, -15.0, 12.0, 12.0, 2, 5.0, {
        "1": net_tag("ENC_A"), "2": net_tag("GND"), "3": net_tag("ENC_B")
    }))
    out.append(generate_smd_2pad_back("D1", "Status_LED", "C2297", 26.0, 48.0, 0.0, 1.8, 1.0, 1.2, net_tag("USER_LED"), net_tag("GND")))
    out.append(generate_smd_2pad_back("R1", "330R", "C17630", 26.0, 51.5, 0.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("USER_LED")))

    # Battery Charger tucked at 35° angle near bottom-left; 1000mAh LiPo pouch rests on B.Cu under the keys!
    out.append(generate_smd_2pad_back("J_BAT", "JST_PH_2P_SMD", "C295747", 32.0, 64.0, 35.0, 2.0, 1.2, 1.8, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_2pad_back("U6", "MCP73831T-2ACI", "C424093", 30.0, 58.0, 35.0, 2.0, 1.2, 1.5, net_tag("+5V_USB"), net_tag("+VBAT")))
    out.append(generate_smd_2pad_back("R_PROG", "2k", "C17604", 34.0, 58.0, 35.0, 1.8, 1.0, 1.2, net_tag("+VBAT"), net_tag("GND")))
    # Silkscreen outline showing 1000mAh LiPo Pouch (50x34mm) tucked cleanly under the center of the keyboard on B.Cu
    out.append(f'  (gr_rect (start 82.0 19.0) (end 132.0 53.0) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))')

    # 5. 28-Key C-Griff Circular 14.0mm Tactile IRP Matrix + Rotated 45° Pull-Down Resistors
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
            sig_id = net_idx[sig_name]

            out.append(generate_irp_tactile_footprint(f"IRP{key_idx}", notes[key_idx - 1], x_mm, y_mm, net_idx["+3V3"], sig_id))

            # Place 10k Pull-Down Resistor at a 45° diagonal angle tucked right next to the signal via (x+6.0, y)
            r_x = x_mm + 4.2
            r_y = y_mm + 2.2
            r_angle = 45.0
            out.append(generate_smd_2pad_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, r_angle, 1.8, 1.0, 1.2, net_tag(sig_name), net_tag("GND")))

            p1_dx, p1_dy = rot_pt(-0.9, 0, r_angle)
            p2_dx, p2_dy = rot_pt(0.9, 0, r_angle)
            out.append(f'  (segment (start {x_mm+6.0:.3f} {y_mm:.3f}) (end {r_x+p1_dx:.3f} {r_y+p1_dy:.3f}) (width 0.25) (layer "B.Cu") (net {sig_id}) (uuid "{uid()}"))')
            via_x, via_y = r_x + p2_dx + 0.8, r_y + p2_dy - 0.8
            out.append(f'  (via (at {via_x:.3f} {via_y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')
            out.append(f'  (segment (start {r_x+p2_dx:.3f} {r_y+p2_dy:.3f}) (end {via_x:.3f} {via_y:.3f}) (width 0.25) (layer "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')

            key_idx += 1

    # 6. 4-Layer Isolated Copper Planes:
    # In1.Cu: Full GND Shield Plane
    out.append(f"""  (zone (net {net_idx["GND"]}) (net_name "GND") (layer "In1.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 0.5) (xy {BOARD_W-0.5:.2f} 0.5) (xy {BOARD_W-0.5:.2f} {BOARD_H-0.5:.2f}) (xy 0.5 {BOARD_H-0.5:.2f})))
  )""")

    # In2.Cu Zone A: Isolated +3V3_ANA Low-Noise Audio Power Island (Upper-Left X: 0.5..31.0mm, Y: 0.5..23.5mm)
    out.append(f"""  (zone (net {net_idx["+3V3_ANA"]}) (net_name "+3V3_ANA") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 0.5) (xy 31.0 0.5) (xy 31.0 23.5) (xy 0.5 23.5)))
  )""")

    # In2.Cu Zone B: Main +3V3 Digital & Key Matrix Plane (Separated from Audio Island by a 1.5mm isolation moat)
    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 32.5 0.5) (xy {BOARD_W-0.5:.2f} 0.5) (xy {BOARD_W-0.5:.2f} {BOARD_H-0.5:.2f}) (xy 0.5 {BOARD_H-0.5:.2f}) (xy 0.5 25.0) (xy 32.5 25.0)))
  )""")

    out.append(")")

    with open("eTutti_Student.kicad_pcb", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Generated Minimalist 4-Layer 'eTutti_Student.kicad_pcb' ({BOARD_W}mm x {BOARD_H}mm)!")

if __name__ == "__main__":
    build_pcb()