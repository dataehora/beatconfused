import os
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

# ==============================================================================
# 1. AUTO-GENERATOR FOR GUARANTEED 3D VRML (.WRL) MODELS (KNOBS + MICROMOD + ICs)
# ==============================================================================
# Note: In KiCad VRML (.wrl), 1 unit = 2.54 mm (0.1 inch). So mm / 2.54 = VRML units.
def mm_to_wrl(val_mm):
    return val_mm / 2.54

def create_local_3d_models():
    os.makedirs("eTutti_3D.3dshapes", exist_ok=True)

    # 1A. 3D Volume Potentiometer + Black Cylindrical Knob Cap (Projects from Top F.Cu)
    s_base_x, s_base_y, s_base_z = mm_to_wrl(9.5), mm_to_wrl(9.5), mm_to_wrl(5.0)
    r_bushing, h_bushing = mm_to_wrl(3.5), mm_to_wrl(5.0)
    r_knob, h_knob = mm_to_wrl(6.0), mm_to_wrl(12.0)
    r_marker = mm_to_wrl(0.8)

    knob_wrl = f"""#VRML V2.0 utf8
Transform {{
  translation 0 0 {mm_to_wrl(2.5):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.18 0.45 0.25 specularColor 0.3 0.3 0.3 }} }}
      geometry Box {{ size {s_base_x:.4f} {s_base_y:.4f} {s_base_z:.4f} }}
    }}
  ]
}}
Transform {{
  translation 0 0 {mm_to_wrl(7.0):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.75 0.75 0.78 specularColor 0.8 0.8 0.8 }} }}
      geometry Cylinder {{ radius {r_bushing:.4f} height {h_bushing:.4f} }}
    }}
  ]
}}
Transform {{
  translation 0 0 {mm_to_wrl(14.5):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.18 specularColor 0.4 0.4 0.4 }} }}
      geometry Cylinder {{ radius {r_knob:.4f} height {h_knob:.4f} }}
    }}
  ]
}}
Transform {{
  translation 0 {mm_to_wrl(3.5):.4f} {mm_to_wrl(20.6):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.95 0.95 0.95 }} }}
      geometry Cylinder {{ radius {r_marker:.4f} height {mm_to_wrl(0.5):.4f} }}
    }}
  ]
}}
"""
    with open("eTutti_3D.3dshapes/Volume_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(knob_wrl)

    # 1B. 3D Rotary Encoder + Stepped Metallic Selector Knob (Projects from Top F.Cu)
    s_enc_x, s_enc_y, s_enc_z = mm_to_wrl(11.5), mm_to_wrl(11.5), mm_to_wrl(5.5)
    r_eknob, h_eknob = mm_to_wrl(7.0), mm_to_wrl(13.0)

    enc_wrl = f"""#VRML V2.0 utf8
Transform {{
  translation 0 0 {mm_to_wrl(2.75):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.20 0.35 0.65 specularColor 0.4 0.4 0.4 }} }}
      geometry Box {{ size {s_enc_x:.4f} {s_enc_y:.4f} {s_enc_z:.4f} }}
    }}
  ]
}}
Transform {{
  translation 0 0 {mm_to_wrl(7.5):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.78 0.78 0.80 specularColor 0.85 0.85 0.85 }} }}
      geometry Cylinder {{ radius {r_bushing:.4f} height {h_bushing:.4f} }}
    }}
  ]
}}
Transform {{
  translation 0 0 {mm_to_wrl(15.0):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.25 0.28 0.32 specularColor 0.7 0.7 0.7 }} }}
      geometry Cylinder {{ radius {r_eknob:.4f} height {h_eknob:.4f} }}
    }}
  ]
}}
"""
    with open("eTutti_3D.3dshapes/Encoder_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(enc_wrl)

    # 1C. 3D SparkFun MicroMod M.2 Socket + Teensy MicroMod Processor Card + Standoff Screw (Mounted on B.Cu)
    mm_wrl = f"""#VRML V2.0 utf8
# Black M.2 Edge Connector Socket along left edge of module
Transform {{
  translation {mm_to_wrl(-8.0):.4f} 0 {mm_to_wrl(2.1):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.12 0.12 0.14 specularColor 0.3 0.3 0.3 }} }}
      geometry Box {{ size {mm_to_wrl(4.2):.4f} {mm_to_wrl(22.0):.4f} {mm_to_wrl(4.2):.4f} }}
    }}
  ]
}}
# SparkFun Red/Blue Teensy MicroMod 22x22mm Processor Carrier Board
Transform {{
  translation {mm_to_wrl(1.0):.4f} 0 {mm_to_wrl(3.2):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.82 0.12 0.15 specularColor 0.3 0.3 0.3 }} }}
      geometry Box {{ size {mm_to_wrl(22.0):.4f} {mm_to_wrl(22.0):.4f} {mm_to_wrl(1.2):.4f} }}
    }}
  ]
}}
# NXP i.MX RT1062 ARM Cortex-M7 MCU Chip on top of MicroMod
Transform {{
  translation {mm_to_wrl(1.5):.4f} 0 {mm_to_wrl(4.3):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.10 0.10 0.12 specularColor 0.4 0.4 0.4 }} }}
      geometry Box {{ size {mm_to_wrl(10.0):.4f} {mm_to_wrl(10.0):.4f} {mm_to_wrl(1.0):.4f} }}
    }}
  ]
}}
# M2.5 Metal Standoff & Screw at right edge of MicroMod
Transform {{
  translation {mm_to_wrl(11.5):.4f} 0 {mm_to_wrl(2.2):.4f}
  rotation 1 0 0 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.80 0.80 0.85 specularColor 0.9 0.9 0.9 }} }}
      geometry Cylinder {{ radius {mm_to_wrl(2.2):.4f} height {mm_to_wrl(4.4):.4f} }}
    }}
  ]
}}
"""
    with open("eTutti_3D.3dshapes/MicroMod_Assembly.wrl", "w", encoding="utf-8") as f:
        f.write(mm_wrl)

    # 1D. 3D Audio Jack 3.5mm Stereo / Mic Box
    jack_wrl = f"""#VRML V2.0 utf8
Transform {{
  translation 0 0 {mm_to_wrl(2.5):.4f}
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.15 }} }}
      geometry Box {{ size {mm_to_wrl(10.0):.4f} {mm_to_wrl(6.0):.4f} {mm_to_wrl(5.0):.4f} }}
    }}
  ]
}}
Transform {{
  translation {mm_to_wrl(-5.5):.4f} 0 {mm_to_wrl(2.5):.4f}
  rotation 0 0 1 1.5708
  children [
    Shape {{
      appearance Appearance {{ material Material {{ diffuseColor 0.75 0.75 0.78 specularColor 0.8 0.8 0.8 }} }}
      geometry Cylinder {{ radius {mm_to_wrl(2.2):.4f} height {mm_to_wrl(3.0):.4f} }}
    }}
  ]
}}
"""
    with open("eTutti_3D.3dshapes/AudioJack_35mm.wrl", "w", encoding="utf-8") as f:
        f.write(jack_wrl)

def model_block(local_Or_KiCad_path, offset_z=0.0, rot_z=0.0, use_local=False):
    """Links either our guaranteed local 3D model or KiCad's built-in 3D library."""
    if use_local:
        full_path = os.path.abspath(local_Or_KiCad_path).replace("\\", "/")
        return f"""    (model "{full_path}"
      (offset (xyz 0 0 {offset_z:.2f})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot_z:.1f}))
    )"""
    return f"""    (model "${{KICAD10_3DMODEL_DIR}}/{local_Or_KiCad_path}"
      (offset (xyz 0 0 {offset_z:.2f})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot_z:.1f}))
    )
    (model "${{KICAD9_3DMODEL_DIR}}/{local_Or_KiCad_path}"
      (offset (xyz 0 0 {offset_z:.2f})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rot_z:.1f}))
    )"""

# ==============================================================================
# 2. FOOTPRINT GENERATORS WITH EXPLICIT NAMES ON ALL CHIPS, RESISTORS & CAPS
# ==============================================================================
def generate_mounting_hole(ref, desc, x, y, net_gnd_idx):
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
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")
    key_num = ref[3:]

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 0 8.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.1 1.1) (thickness 0.22))))',
        f'    (fp_text user "{ref}:{note_name}" (at -1.5 -3.5 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14)) (justify mirror)))',
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

def generate_smd_0805_back(ref, desc, lcsc, x, y, angle, net1, net2, is_cap=False, is_led=False, show_top_silk=True):
    """
    0805 SMD resistor/capacitor/LED on B.Cu with:
    - Combined 'REF:VALUE' label clearly printed on B.SilkS (and F.Fab/F.SilkS if in Left Control Wing)
    - Standard 3D model
    """
    if is_led:
        m_path = "LED_SMD.3dshapes/LED_0805_2012Metric.wrl"
    elif is_cap:
        m_path = "Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl"
    else:
        m_path = "Resistor_SMD.3dshapes/R_0805_2012Metric.wrl"

    top_label_line = ""
    if show_top_silk:
        top_label_line = f'    (fp_text user "{ref}:{desc}" (at 0 -1.65 {angle:.1f}) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.65 0.65) (thickness 0.12))))\n'

    return f"""  (footprint "Resistor_SMD:R_0805_2012Metric" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -1.55 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.14)) (justify mirror)))
    (property "Value" "{desc}" (at 0 1.55 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.7 0.7) (thickness 0.12)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
{top_label_line}    (fp_rect (start -1.4 -0.85) (end 1.4 0.85) (stroke (width 0.12) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" smd roundrect (at -0.95 0 {angle:.1f}) (size 1.0 1.25) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net1} (uuid "{uid()}"))
    (pad "2" smd roundrect (at 0.95 0 {angle:.1f}) (size 1.0 1.25) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net2} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_sot23_5_back(ref, desc, lcsc, x, y, angle, net_map):
    """SOT-23-5 IC on B.Cu with visible Reference & Description on BOTH B.SilkS and F.SilkS."""
    m_path = "Package_TO_SOT_SMD.3dshapes/SOT-23-5.wrl"
    return f"""  (footprint "Package_TO_SOT_SMD:SOT-23-5" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -2.4 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.15)) (justify mirror)))
    (property "Value" "{desc}" (at 0 2.4 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.13)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (fp_text user "{ref}:{desc}" (at 0 -2.4 {angle:.1f}) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.7 0.7) (thickness 0.12))))
    (fp_rect (start -1.6 -1.6) (end 1.6 1.6) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" smd rect (at -1.1 -0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("1","")} (uuid "{uid()}"))
    (pad "2" smd rect (at -1.1 0.0 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("2","")} (uuid "{uid()}"))
    (pad "3" smd rect (at -1.1 0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("3","")} (uuid "{uid()}"))
    (pad "4" smd rect (at 1.1 0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("4","")} (uuid "{uid()}"))
    (pad "5" smd rect (at 1.1 -0.95 {angle:.1f}) (size 1.1 0.6) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("5","")} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_ic_box_back(ref, desc, lcsc, x, y, angle, box_w, box_h, pins_per_side, pitch, net_map, model_rel=None, use_local_model=False, top_label=None):
    """Places ICs & Connectors on B.Cu with explicit names on B.SilkS AND F.SilkS."""
    lbl_top = top_label if top_label else f"{ref}: {desc}"
    lines = [
        f'  (footprint "eTutti:{ref}_Back" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f} {angle:.1f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16)) (justify mirror)))',
        f'    (property "Value" "{desc}" (at 0 {box_h/2 + 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.14)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
        # Center name inside the IC body on B.SilkS + Top F.SilkS so it is always visible from both sides!
        f'    (fp_text user "{ref}" (at 0 0 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16)) (justify mirror)))',
        f'    (fp_text user "{lbl_top}" (at 0 0 {angle:.1f}) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))',
        f'    (fp_rect (start {-box_w/2:.2f} {-box_h/2:.2f}) (end {box_w/2:.2f} {box_h/2:.2f}) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
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
    if model_rel:
        lines.append(model_block(model_rel, use_local=use_local_model))
    lines.append('  )')
    return "\n".join(lines)

def generate_tht_knob_top(ref, desc, x, y, net1, net2, net3, is_encoder=False):
    """Mounts Knobs on F.Cu (Top) linked to our guaranteed local 3D Knob VRML models!"""
    local_wrl = "eTutti_3D.3dshapes/Encoder_Knob.wrl" if is_encoder else "eTutti_3D.3dshapes/Volume_Knob.wrl"
    return f"""  (footprint "eTutti:{ref}_Top" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16))))
    (property "Value" "{desc}" (at 0 7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.18))))
    (fp_text user "{ref}:{desc}" (at 0 -7.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14)) (justify mirror)))
    (fp_circle (center 0 0) (end 5.5 0) (stroke (width 0.18) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at -2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net1} (uuid "{uid()}"))
    (pad "2" thru_hole circle (at 0.0 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net2} (uuid "{uid()}"))
    (pad "3" thru_hole circle (at 2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net3} (uuid "{uid()}"))
{model_block(local_wrl, use_local=True)}
  )"""

def build_pcb():
    # First generate the local 3D .wrl files so Knobs, Audio Jacks & MicroMod always render in 3D Viewer!
    create_local_3d_models()

    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 38.50
    KEY_ORIGIN_Y = 11.50

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v5_Full3D_Labels")',
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

    out.append(f'  (gr_text "eTutti Student v5 | MicroMod + SGTL5000" (at 88.0 2.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.1 1.1) (thickness 0.2))))')

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

    # --- 3. LEFT WING & DIAGONAL POCKET PLACEMENT WITH GUARANTEED 3D MODELS & FULL LABELS ---
    out.append(generate_ic_box_back("J_HP", "PHONES_3.5mm", "C145898", 5.2, 10.0, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_HP: PHONES OUT"))

    out.append(generate_ic_box_back("J_MIC", "MIC_IN_3.5mm", "C145898", 5.2, 19.0, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_MIC: MIC IN"))

    out.append(generate_ic_box_back("J_USBC", "USB-C_PORT", "C165948", 4.5, 29.5, 0.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }, "Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl", use_local_model=False, top_label="J_USBC: USB-C"))
    out.append(generate_smd_0805_back("R_CC1", "5.1k", "C27834", 11.5, 27.8, 0.0, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_0805_back("R_CC2", "5.1k", "C27834", 11.5, 31.2, 0.0, net_tag("USB_CC2"), net_tag("GND")))

    # Isolated Audio Codec Section
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000", "C89941", 18.5, 14.5, 0.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl", use_local_model=False, top_label="U_CODEC: SGTL5000"))

    out.append(generate_sot23_5_back("U_1V8", "1.8V_LDO", "C134077", 18.5, 7.5, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE", "C1002", 24.5, 7.5, 90.0, net_tag("+3V3"), net_tag("+3V3_ANA")))
    out.append(generate_smd_0805_back("C_1V8", "100nF", "C49678", 13.5, 7.5, 90.0, net_tag("+1V8_CODEC"), net_tag("GND"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF", "C15850", 18.5, 21.0, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    # Top-Surface Ergonomic Knobs (Now using guaranteed local 3D VRML models!)
    out.append(generate_tht_knob_top("RV1", "VOLUME_10k", 11.5, 44.0, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SELECT_ENC", 11.5, 60.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "LED_STATUS", "C2297", 21.5, 44.0, 90.0, net_tag("USER_LED"), net_tag("GND"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R", "C17630", 21.5, 48.0, 90.0, net_tag("+3V3"), net_tag("USER_LED")))

    # --- HARMONIC 30° PARALLEL BUS CASCADE ---
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "MUX_1-16_HC4067", "C70001", 43.5, 11.5, 30.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U4: MUX 1-16"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF", "C49678", 37.5, 4.5, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    # MicroMod M.2 Socket + Processor Card (Now uses our guaranteed local MicroMod_Assembly.wrl 3D model!)
    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD", "C2838503", 31.0, 29.5, 30.0, 18.0, 18.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "eTutti_3D.3dshapes/MicroMod_Assembly.wrl", use_local_model=True, top_label="U_MM: TEENSY MICROMOD"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k", "C17520", 23.0, 19.5, 30.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k", "C17520", 21.5, 22.5, 30.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_17-28_HC4067", "C70001", 34.0, 56.5, 30.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U5: MUX 17-28"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF", "C49678", 27.5, 49.5, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    # Battery Management Section
    out.append(generate_sot23_5_back("U6", "MCP73831_CHG", "C424093", 23.5, 56.5, 30.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_PROG", "C17604", 21.5, 61.0, 30.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_JST", "C295747", 25.5, 63.5, 30.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
    out.append(f'  (gr_rect (start 78.0 21.0) (end 128.0 51.0) (stroke (width 0.15) (type dash)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))')
    out.append(f'  (gr_text "1000mAh LiPo Battery Zone (Back)" (at 103.0 36.0 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror)))')

    # --- 4. 28-KEY C-GRIFF KEYBOARD + HARMONIC +30° PULL-DOWN RESISTORS WITH CLEAR LABELS ---
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
            # Pull-down resistors on back: show_top_silk=False so they don't clutter the front playing pads,
            # while B.SilkS clearly displays R_PD1..28 and 10k!
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, r_angle, net_tag(sig_name), net_tag("GND"), show_top_silk=False))

            p1_dx, p1_dy = rot_pt(-0.95, 0, r_angle)
            p2_dx, p2_dy = rot_pt(0.95, 0, r_angle)
            out.append(f'  (segment (start {x_mm+6.0:.3f} {y_mm:.3f}) (end {r_x+p1_dx:.3f} {r_y+p1_dy:.3f}) (width 0.25) (layer "B.Cu") (net {sig_id}) (uuid "{uid()}"))')
            via_x, via_y = r_x + p2_dx + 0.7, r_y + p2_dy - 0.7
            out.append(f'  (via (at {via_x:.3f} {via_y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')
            out.append(f'  (segment (start {r_x+p2_dx:.3f} {r_y+p2_dy:.3f}) (end {via_x:.3f} {via_y:.3f}) (width 0.25) (layer "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')

            key_idx += 1

    # --- 5. 4-LAYER ISOLATED COPPER PLANES ---
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
    print("Generated 'eTutti_3D.3dshapes/' and 'eTutti_Student.kicad_pcb' v5 with all 3D models & full labels!")

if __name__ == "__main__":
    build_pcb()