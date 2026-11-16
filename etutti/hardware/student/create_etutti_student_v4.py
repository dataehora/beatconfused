import math
import uuid

def uid():
    return str(uuid.uuid4())

def rot_pt(dx, dy, angle_deg):
    """Rotates local (dx, dy) by angle_deg (KiCad CCW convention)."""
    rad = math.radians(-angle_deg)
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry

def model_block(rel_path, offset_z=0.0, rot_z=0.0):
    """Embeds both KiCad 10 and KiCad 9 3D model paths so 3D Viewer renders automatically."""
    return f"""    (model "${{KICAD10_3DMODEL_DIR}}/{rel_path}"
      (offset (xyz 0 0 {offset_z:.2f})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot_z:.1f}))
    )
    (model "${{KICAD9_3DMODEL_DIR}}/{rel_path}"
      (offset (xyz 0 0 {offset_z:.2f})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot_z:.1f}))
    )"""

def generate_mounting_hole(ref, desc, x, y, net_gnd_idx):
    """M2.5 Mounting Hole (2.7mm drill, 5.0mm grounded copper pad + 3D stand-off ring)."""
    return f"""  (footprint "MountingHole:MountingHole_2.7mm_M2.5_Pad" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (property "Value" "{desc}" (at 0 3.6 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.15)) (justify mirror)))
    (fp_circle (center 0 0) (end 2.7 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (fp_circle (center 0 0) (end 2.7 0) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at 0 0) (size 5.0 5.0) (drill 2.7) (layers "*.Cu" "*.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
  )"""

def generate_irp_tactile_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    """
    14.0mm Circular Interdigitated Resistive Pad (IRP) on F.Cu with:
    - Raised Tactile Embossing Rim (F.Cu + F.Mask + F.SilkS)
    - Conductive C & F root-note tactile textures
    - Printed Note Name & Key Number on Top Silkscreen
    """
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")
    key_num = ref[3:]

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 0 8.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.1 1.1) (thickness 0.22))))',
        f'    (fp_text user "{ref}:{note_name}" (at 0 -3.5 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14)) (justify mirror)))',
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.55) (type solid)) (fill none) (layer "F.Cu") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.1 0) (stroke (width 0.65) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 7.45 0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.1) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',
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
            net_str = f'(net {net_sig_idx} "KEY_SIG_{key_num}")'

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
    lines.append(f'    (pad "2" thru_hole circle (at 6.0 0) (size 0.8 0.8) (drill 0.4) (layers "*.Cu") (net {net_sig_idx} "KEY_SIG_{key_num}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_0805_back(ref, desc, lcsc, x, y, angle, net1, net2, is_cap=False, is_led=False):
    """0805 SMD part on B.Cu with visible printed description + 3D model."""
    if is_led:
        m_path = "LED_SMD.3dshapes/LED_0805_2012Metric.wrl"
    elif is_cap:
        m_path = "Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl"
    else:
        m_path = "Resistor_SMD.3dshapes/R_0805_2012Metric.wrl"

    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -1.45 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.7 0.7) (thickness 0.12)) (justify mirror)))
    (property "Value" "{desc}" (at 0 1.45 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.7 0.7) (thickness 0.12)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (fp_rect (start -1.4 -0.85) (end 1.4 0.85) (stroke (width 0.12) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" smd roundrect (at -0.95 0 {angle:.1f}) (size 1.0 1.25) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net1} (uuid "{uid()}"))
    (pad "2" smd roundrect (at 0.95 0 {angle:.1f}) (size 1.0 1.25) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net2} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_sot23_5_back(ref, desc, lcsc, x, y, angle, net_map):
    """SOT-23-5 IC (LDO / LiPo Charger) on B.Cu with 3D model and printed description."""
    m_path = "Package_TO_SOT_SMD.3dshapes/SOT-23-5.wrl"
    return f"""  (footprint "Package_TO_SOT_SMD:SOT-23-5" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -2.4 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14)) (justify mirror)))
    (property "Value" "{desc}" (at 0 2.4 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.12)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (fp_rect (start -1.6 -1.6) (end 1.6 1.6) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" smd rect (at -1.1 -0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("1","")} (uuid "{uid()}"))
    (pad "2" smd rect (at -1.1 0.0 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("2","")} (uuid "{uid()}"))
    (pad "3" smd rect (at -1.1 0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("3","")} (uuid "{uid()}"))
    (pad "4" smd rect (at 1.1 0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("4","")} (uuid "{uid()}"))
    (pad "5" smd rect (at 1.1 -0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("5","")} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_ic_box_back(ref, desc, lcsc, x, y, angle, box_w, box_h, pins_per_side, pitch, net_map, model_rel=None, top_label=None):
    """Places ICs & Connectors on B.Cu with visible B.SilkS + optional F.SilkS labels & 3D models."""
    lines = [
        f'  (footprint "eTutti:{ref}_Back" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f} {angle:.1f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.3:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.14)) (justify mirror)))',
        f'    (property "Value" "{desc}" (at 0 {box_h/2 + 1.3:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.13)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))',
    ]
    if top_label:
        lines.append(f'    (fp_text user "{top_label}" (at 0 0 {angle:.1f}) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16))))')

    start_y = -((pins_per_side - 1) * pitch) / 2.0
    for i in range(pins_per_side):
        p_left = str(i + 1)
        p_right = str((pins_per_side * 2) - i)
        py = start_y + i * pitch
        n_left = net_map.get(p_left, "")
        n_right = net_map.get(p_right, "")
        lines.append(f'    (pad "{p_left}" smd rect (at {-box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.3 0.5) (layers "B.Cu" "B.Paste" "B.Mask") {n_left} (uuid "{uid()}"))')
        lines.append(f'    (pad "{p_right}" smd rect (at {box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.3 0.5) (layers "B.Cu" "B.Paste" "B.Mask") {n_right} (uuid "{uid()}"))')
    if model_rel:
        lines.append(model_block(model_rel))
    lines.append('  )')
    return "\n".join(lines)

def generate_tht_knob_top(ref, desc, x, y, net1, net2, net3, is_encoder=False):
    """Mounts Knobs on F.Cu (Top) so 3D shafts project upward and labels print on the front panel!"""
    m_path = (
        "Rotary_Encoder.3dshapes/RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm.wrl"
        if is_encoder else
        "Potentiometer_THT.3dshapes/Potentiometer_Alps_RK09K_Single_Vertical.wrl"
    )
    return f"""  (footprint "eTutti:{ref}_Top" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.15))))
    (property "Value" "{desc}" (at 0 7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.18))))
    (fp_circle (center 0 0) (end 5.2 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at -2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net1} (uuid "{uid()}"))
    (pad "2" thru_hole circle (at 0.0 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net2} (uuid "{uid()}"))
    (pad "3" thru_hole circle (at 2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net3} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def build_pcb():
    # --- HARMONIC MINIMALIST GEOMETRY ---
    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 38.50   # Tight 38.5mm left control wing
    KEY_ORIGIN_Y = 11.50   # 11.5mm top tangent buffer

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v4_Organic_3D")',
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

    # --- 1. ORGANIC TANGENT-TRIMMED BOARD OUTLINE (Edge.Cuts) ---
    board_poly = [
        (0.0, 4.0),
        (4.0, 0.0),
        (160.5, 0.0),
        (183.5, 40.0),
        (183.5, 49.0),
        (171.0, 72.5),
        (4.0, 72.5),
        (0.0, 68.5),
    ]
    for i in range(len(board_poly)):
        x1, y1 = board_poly[i]
        x2, y2 = board_poly[(i + 1) % len(board_poly)]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    out.append(f'  (gr_text "eTutti Student v4 | MicroMod + SGTL5000" (at 88.0 2.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.1 1.1) (thickness 0.2))))')

    # --- 2. 9 ANTI-FLEXION M2.5 MOUNTING HOLES ---
    mounting_holes = [
        ("MP1", "M2.5_TL", 27.5, 4.0),
        ("MP2", "M2.5_BL", 27.5, 68.5),
        ("MP3", "M2.5_TC", 105.0, 3.8),
        ("MP4", "M2.5_TR", 157.5, 4.5),
        ("MP5", "M2.5_BR", 167.5, 68.0),
        ("MP6", "M2.5_INT1", KEY_ORIGIN_X + 1.5 * PITCH_X, KEY_ORIGIN_Y + 0.5 * PITCH_Y),
        ("MP7", "M2.5_INT2", KEY_ORIGIN_X + 3.5 * PITCH_X, KEY_ORIGIN_Y + 1.5 * PITCH_Y),
        ("MP8", "M2.5_INT3", KEY_ORIGIN_X + 5.5 * PITCH_X, KEY_ORIGIN_Y + 1.5 * PITCH_Y),
        ("MP9", "M2.5_INT4", KEY_ORIGIN_X + 2.5 * PITCH_X, KEY_ORIGIN_Y + 2.5 * PITCH_Y),
    ]
    for m_ref, m_desc, mx, my in mounting_holes:
        out.append(generate_mounting_hole(m_ref, m_desc, mx, my, net_idx["GND"]))

    # --- 3. HARMONICALLY ALIGNED LEFT WING & DIAGONAL POCKET PLACEMENT ---
    out.append(generate_ic_box_back("J_HP", "3.5mm_PHONES_OUT", "C145898", 5.2, 10.0, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }, "Connector_Audio.3dshapes/Jack_3.5mm_CUI_SJ-3523-SMT_Horizontal.wrl", "PHONES OUT"))

    out.append(generate_ic_box_back("J_MIC", "3.5mm_MIC_IN", "C145898", 5.2, 19.0, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }, "Connector_Audio.3dshapes/Jack_3.5mm_CUI_SJ-3523-SMT_Horizontal.wrl", "MIC IN"))

    out.append(generate_ic_box_back("J_USBC", "USB-C_DATA_PWR", "C165948", 4.5, 29.5, 0.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }, "Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl", "USB-C"))
    out.append(generate_smd_0805_back("R_CC1", "5.1k_CC1", "C27834", 11.5, 27.8, 0.0, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_0805_back("R_CC2", "5.1k_CC2", "C27834", 11.5, 31.2, 0.0, net_tag("USB_CC2"), net_tag("GND")))

    # Isolated Audio Codec Section
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000_AUDIO", "C89941", 18.5, 14.5, 0.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl"))

    out.append(generate_sot23_5_back("U_1V8", "AP7313_1.8V_LDO", "C134077", 18.5, 7.5, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE_AUDIO", "C1002", 24.5, 7.5, 90.0, net_tag("+3V3"), net_tag("+3V3_ANA")))
    out.append(generate_smd_0805_back("C_1V8", "100nF_1V8", "C49678", 13.5, 7.5, 90.0, net_tag("+1V8_CODEC"), net_tag("GND"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF_ANA", "C15850", 18.5, 21.0, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    # Top-Surface Ergonomic Knobs
    out.append(generate_tht_knob_top("RV1", "VOLUME", 11.5, 44.0, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SOUND SELECT", 11.5, 60.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "STATUS_LED", "C2297", 21.5, 44.0, 90.0, net_tag("USER_LED"), net_tag("GND"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R_LED", "C17630", 21.5, 48.0, 90.0, net_tag("+3V3"), net_tag("USER_LED")))

    # --- HARMONIC 30° PARALLEL BUS CASCADE ---
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "MUX_KEYS_1-16", "C70001", 43.5, 11.5, 30.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF_MUX1", "C49678", 37.5, 4.5, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD_M2", "C2838503", 31.0, 29.5, 30.0, 18.0, 18.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "Package_DFN_QFN.3dshapes/QFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm.wrl"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k_SDA", "C17520", 23.0, 19.5, 30.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k_SCL", "C17520", 21.5, 22.5, 30.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_KEYS_17-28", "C70001", 34.0, 56.5, 30.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF_MUX2", "C49678", 27.5, 49.5, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    # Battery Management Section (Fixed: uses valid KiCad 'dash' stroke type)
    out.append(generate_sot23_5_back("U6", "MCP73831_LIPO_CHG", "C424093", 23.5, 56.5, 30.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_CHG_PROG", "C17604", 21.5, 61.0, 30.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_1000mAh_IN", "C295747", 25.5, 63.5, 30.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
    out.append(f'  (gr_rect (start 78.0 21.0) (end 128.0 51.0) (stroke (width 0.15) (type dash)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))')
    out.append(f'  (gr_text "1000mAh LiPo Battery Zone (Back)" (at 103.0 36.0 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror)))')

    # --- 4. 28-KEY C-GRIFF KEYBOARD + HARMONIC +30° PULL-DOWN RESISTORS ---
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

            r_x = x_mm + 4.2
            r_y = y_mm + 2.2
            r_angle = 30.0
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", f"10k_K{key_idx}", "C17414", r_x, r_y, r_angle, net_tag(sig_name), net_tag("GND")))

            p1_dx, p1_dy = rot_pt(-0.95, 0, r_angle)
            p2_dx, p2_dy = rot_pt(0.95, 0, r_angle)
            out.append(f'  (segment (start {x_mm+6.0:.3f} {y_mm:.3f}) (end {r_x+p1_dx:.3f} {r_y+p1_dy:.3f}) (width 0.25) (layer "B.Cu") (net {sig_id}) (uuid "{uid()}"))')
            via_x, via_y = r_x + p2_dx + 0.7, r_y + p2_dy - 0.7
            out.append(f'  (via (at {via_x:.3f} {via_y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')
            out.append(f'  (segment (start {r_x+p2_dx:.3f} {r_y+p2_dy:.3f}) (end {via_x:.3f} {via_y:.3f}) (width 0.25) (layer "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')

            key_idx += 1

    # --- 5. 4-LAYER ISOLATED COPPER PLANES MATCHING TANGENT CONTOUR ---
    poly_pts = " ".join([f"(xy {px:.2f} {py:.2f})" for px, py in board_poly])
    out.append(f"""  (zone (net {net_idx["GND"]}) (net_name "GND") (layer "In1.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts {poly_pts}))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3_ANA"]}) (net_name "+3V3_ANA") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 4.0) (xy 4.0 0.5) (xy 24.0 0.5) (xy 24.0 23.5) (xy 0.5 23.5)))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 25.5 0.5) (xy 160.0 0.5) (xy 183.0 40.0) (xy 183.0 49.0) (xy 170.5 72.0) (xy 4.0 72.0) (xy 0.5 68.5) (xy 0.5 25.0) (xy 25.5 25.0)))
  )""")

    out.append(")")

    with open("eTutti_Student.kicad_pcb", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Fixed and generated 'eTutti_Student.kicad_pcb' v4!")

if __name__ == "__main__":
    build_pcb()