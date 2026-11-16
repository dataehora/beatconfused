import math
import uuid

def uid():
    return str(uuid.uuid4())

def generate_irp_tactile_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    """
    14.0mm Circular Interdigitated Resistive Pad (IRP) on F.Cu (Top) with:
    1. Recessed bare-copper/ENIG sensing area (F.Mask opening, R=6.6mm)
    2. Raised Tactile Embossing Rim around perimeter (Stacked F.Cu + F.Mask + heavy F.SilkS from R=6.8 to 7.4mm)
    3. Conductive Tactile Texture inside 'C' (center dot cluster) and 'F' (3 tactile bars) keys
       tied to +3V3 so sensing is 100% preserved!
    """
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 0 8.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.1 1.1) (thickness 0.2))))',

        # --- 1. TACTILE EMBOSSING RIM AROUND BUTTON (R = 6.9mm to 7.5mm) ---
        # Stacked Copper + Solder Mask + Double-Thick Silkscreen Ring creates a physical raised ridge
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.6) (type solid)) (fill none) (layer "F.Cu") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.7) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.45 0) (stroke (width 0.3) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        # Cutout guide on User.Eco1 if user wants a laser-cut top overlay sheet
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.1) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',

        # --- 2. EXPOSED BARE COPPER/GOLD SENSING WELL (R = 6.6mm) ---
        f'    (fp_circle (center 0 0) (end 6.6 0) (stroke (width 0.0) (type solid)) (fill solid) (layer "F.Mask") (uuid "{uid()}"))',
    ]

    # --- 3. INTERDIGITATED SENSING FINGERS ---
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

    # --- 4. CONDUCTIVE TACTILE TEXTURE FOR 'C' AND 'F' ROOT NOTES ---
    # Uses tiny 0.45mm micro-vias/annular rings & raised conductive dots on the +3V3 fingers
    # so the finger feels a distinct texture through the Velostat without losing electrical contact!
    if is_c_note:
        # C-Note: Tactile Center Dimple + 4-Dot Cross Cluster (Braille-style feel)
        c_dots = [(0.0, 0.0), (-1.8, 0.0), (1.8, 0.0), (0.0, -1.5), (0.0, 1.5)]
        for dx, dy in c_dots:
            lines.append(
                f'    (pad "1" thru_hole circle (at {dx:.2f} {dy:.2f}) (size 0.95 0.95) (drill 0.55) (layers "*.Cu" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
            )
    elif is_f_note:
        # F-Note: Tactile Horizontal Ridges (3 raised drilled micro-bar rows)
        for dy in [-1.5, 0.0, 1.5]:
            for dx in [-2.2, -1.1, 0.0, 1.1, 2.2]:
                lines.append(
                    f'    (pad "1" thru_hole circle (at {dx:.2f} {dy:.2f}) (size 0.85 0.85) (drill 0.5) (layers "*.Cu" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
                )

    # Left (+3V3) & Right (KEY_SIG) Thru-Vias down to Back Layer (B.Cu)
    lines.append(f'    (pad "1" thru_hole circle (at -6.0 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 6.0 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_sig_idx} "KEY_SIG_{ref[3:]}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_2pad_back(ref, val, lcsc, x, y, pitch, w, h, net1, net2):
    """Places 0805 / 2-pad SMD parts on B.Cu (Back layer) for single-sided JLCPCB SMT assembly."""
    return f"""  (footprint "eTutti:SMD_0805_Back" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -1.5 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify mirror)))
    (property "Value" "{val}" (at 0 1.5 0) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 0) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (pad "1" smd rect (at {-pitch/2:.3f} 0) (size {w:.2f} {h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {net1} (uuid "{uid()}"))
    (pad "2" smd rect (at {pitch/2:.3f} 0) (size {w:.2f} {h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {net2} (uuid "{uid()}"))
  )"""

def generate_ic_box_back(ref, val, lcsc, x, y, box_w, box_h, pins_per_side, pitch, net_map):
    """Places ICs & SMD connectors on B.Cu (Back layer) so Top layer is 100% flat for playing."""
    lines = [
        f'  (footprint "eTutti:{val}_Back" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.5:.2f} 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))',
        f'    (property "Value" "{val}" (at 0 {box_h/2 + 1.5:.2f} 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 0) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))',
    ]
    start_y = -((pins_per_side - 1) * pitch) / 2.0
    for i in range(pins_per_side):
        p_left = str(i + 1)
        p_right = str((pins_per_side * 2) - i)
        py = start_y + i * pitch
        n_left = net_map.get(p_left, "")
        n_right = net_map.get(p_right, "")
        lines.append(f'    (pad "{p_left}" smd rect (at {-box_w/2:.3f} {py:.3f}) (size 1.4 0.55) (layers "B.Cu" "B.Paste" "B.Mask") {n_left} (uuid "{uid()}"))')
        lines.append(f'    (pad "{p_right}" smd rect (at {box_w/2:.3f} {py:.3f}) (size 1.4 0.55) (layers "B.Cu" "B.Paste" "B.Mask") {n_right} (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def build_pcb():
    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 75.0
    KEY_ORIGIN_Y = 24.25
    BOARD_W = 227.40
    BOARD_H = 98.00

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v2")',
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

    # 1. Board Outline (Edge.Cuts)
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    # 2. All SMD Electronics Mounted on B.Cu (Back Layer) for Single-Sided JLCPCB Assembly (<$30)
    # MicroMod M.2 Socket on Back Layer
    out.append(generate_ic_box_back("U_MM", "MicroMod_M2_Socket", "C2838503", 32.0, 18.0, 22.0, 22.0, 12, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }))

    # SGTL5000 Audio Codec + 1.8V LDO + Decoupling Caps on Back Layer
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000XNAA3", "C89941", 52.0, 18.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_2pad_back("U_1V8", "AP7313-18SAG", "C134077", 52.0, 25.0, 2.0, 1.0, 1.2, net_tag("+3V3"), net_tag("+1V8_CODEC")))
    out.append(generate_smd_2pad_back("C_1V8", "100nF", "C49678", 52.0, 28.0, 1.8, 1.0, 1.2, net_tag("+1V8_CODEC"), net_tag("GND")))
    out.append(generate_smd_2pad_back("C_CODEC", "100nF", "C49678", 52.0, 12.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("GND")))
    out.append(generate_smd_2pad_back("R_SDA", "2.2k", "C17520", 46.0, 16.0, 1.8, 1.0, 1.2, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_2pad_back("R_SCL", "2.2k", "C17520", 46.0, 19.0, 1.8, 1.0, 1.2, net_tag("I2C_SCL"), net_tag("+3V3")))

    # Left Edge Ports on Back Layer: Headphone Out (J_HP), Mic In (J_MIC), USB-C (J_USBC)
    out.append(generate_ic_box_back("J_HP", "PJ-320A_3.5mm_HP", "C145898", 6.0, 12.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }))
    out.append(generate_ic_box_back("J_MIC", "PJ-320A_3.5mm_MIC", "C145898", 6.0, 22.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }))
    out.append(generate_ic_box_back("J_USBC", "TYPE-C-31-M-12", "C165948", 4.5, 33.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }))
    out.append(generate_smd_2pad_back("R_CC1", "5.1k", "C27834", 12.0, 31.0, 1.8, 1.0, 1.2, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_2pad_back("R_CC2", "5.1k", "C27834", 12.0, 35.0, 1.8, 1.0, 1.2, net_tag("USB_CC2"), net_tag("GND")))

    # User Controls (Top-accessible shafts, soldered on Back)
    out.append(generate_ic_box_back("RV1", "Volume_Pot_10k", "Manual_THT", 20.0, 52.0, 10.0, 10.0, 2, 5.0, {
        "1": net_tag("GND"), "2": net_tag("VOL_ADC"), "3": net_tag("+3V3")
    }))
    out.append(generate_ic_box_back("SW_ENC1", "Rotary_Encoder_EC11", "Manual_THT", 44.0, 52.0, 12.0, 12.0, 2, 5.0, {
        "1": net_tag("ENC_A"), "2": net_tag("GND"), "3": net_tag("ENC_B")
    }))
    out.append(generate_smd_2pad_back("D1", "Status_LED", "C2297", 32.0, 43.0, 1.8, 1.0, 1.2, net_tag("USER_LED"), net_tag("GND")))
    out.append(generate_smd_2pad_back("R1", "330R", "C17630", 32.0, 46.5, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("USER_LED")))

    # LiPo Battery Charger & JST Jack on Back Layer
    out.append(generate_smd_2pad_back("J_BAT", "JST_PH_2P_SMD", "C295747", 14.0, 66.0, 2.0, 1.2, 1.8, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_2pad_back("U6", "MCP73831T-2ACI", "C424093", 25.0, 66.0, 2.0, 1.2, 1.5, net_tag("+5V_USB"), net_tag("+VBAT")))
    out.append(generate_smd_2pad_back("R_PROG", "2k", "C17604", 25.0, 70.0, 1.8, 1.0, 1.2, net_tag("+VBAT"), net_tag("GND")))
    out.append(f'  (gr_rect (start 8.0 63.0) (end 58.0 95.0) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))')

    # Multiplexers U4 & U5 on Back Layer (B.Cu)
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "CD74HC4067M96", "C70001", 65.0, 36.0, 7.5, 15.4, 12, 1.27, mux1_map))
    out.append(generate_smd_2pad_back("C_MUX1", "100nF", "C49678", 65.0, 26.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("GND")))
    out.append(generate_ic_box_back("U5", "CD74HC4067M96", "C70001", 65.0, 66.0, 7.5, 15.4, 12, 1.27, mux2_map))
    out.append(generate_smd_2pad_back("C_MUX2", "100nF", "C49678", 65.0, 56.0, 1.8, 1.0, 1.2, net_tag("+3V3"), net_tag("GND")))

    # 3. 28 Circular 14.0mm Tactile IRP Pads on Top (F.Cu) + 28 Pull-Down Resistors Directly Underneath on Back (B.Cu)
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

            # Top Layer Tactile IRP Sensor Pad (with C and F note conductive embossing)
            out.append(generate_irp_tactile_footprint(f"IRP{key_idx}", notes[key_idx - 1], x_mm, y_mm, net_idx["+3V3"], sig_id))

            # Back Layer (B.Cu) 10k Pull-Down Resistor hidden directly underneath each key!
            # Basic JLCPCB part C17414 (10k 0805)
            r_x = x_mm + 4.2
            r_y = y_mm
            out.append(generate_smd_2pad_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, 1.8, 1.0, 1.2, net_tag(sig_name), net_tag("GND")))

            # Pre-routed B.Cu copper trace from Key Signal Via (x+6.0, y) to R_PD Pad 1 (x+3.3, y)
            out.append(f'  (segment (start {x_mm+6.0:.3f} {y_mm:.3f}) (end {r_x-0.9:.3f} {r_y:.3f}) (width 0.25) (layer "B.Cu") (net {sig_id}) (uuid "{uid()}"))')
            # Pre-routed GND Via right next to R_PD Pad 2 (x+5.1, y) into In1.Cu GND plane
            out.append(f'  (via (at {r_x+1.8:.3f} {r_y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')
            out.append(f'  (segment (start {r_x+0.9:.3f} {r_y:.3f}) (end {r_x+1.8:.3f} {r_y:.3f}) (width 0.25) (layer "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')

            key_idx += 1

    # 4. Inner Copper Planes (In1.Cu = GND, In2.Cu = +3V3)
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
    print("Updated 'eTutti_Student.kicad_pcb' with Back-side SMT parts & Tactile C/F Embossing!")

if __name__ == "__main__":
    build_pcb()