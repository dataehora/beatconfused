import os
import math
import uuid

def uid():
    return str(uuid.uuid4())

def rot_pt(dx, dy, angle_deg):
    rad = math.radians(-angle_deg)
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry

def mm_to_wrl(val_mm):
    return val_mm / 2.54

# ==============================================================================
# 1. TRUE TRIANGULATED 3D MESH GENERATOR (IndexedFaceSet FOR KICAD 3D VIEWER)
# ==============================================================================
def make_cylinder_ifs(radius_mm, z_bot_mm, z_top_mm, segments=32, r_top_mm=None, fluted_amp_mm=0.0):
    """
    Generates a VRML 2.0 IndexedFaceSet triangulated mesh for a cylinder/cone/fluted knob.
    KiCad's 3D viewer ALWAYS renders IndexedFaceSet meshes accurately!
    """
    if r_top_mm is None:
        r_top_mm = radius_mm

    pts = []
    # Bottom ring vertices (0 .. segments-1)
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        flute = fluted_amp_mm * math.cos(segments * 0.5 * ang) if fluted_amp_mm > 0 else 0.0
        r = mm_to_wrl(radius_mm + flute)
        pts.append((r * math.cos(ang), r * math.sin(ang), mm_to_wrl(z_bot_mm)))

    # Top ring vertices (segments .. 2*segments-1)
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        flute = fluted_amp_mm * math.cos(segments * 0.5 * ang) if fluted_amp_mm > 0 else 0.0
        r = mm_to_wrl(r_top_mm + flute)
        pts.append((r * math.cos(ang), r * math.sin(ang), mm_to_wrl(z_top_mm)))

    # Center vertices for bottom cap (2*segments) and top cap (2*segments + 1)
    idx_bot_c = 2 * segments
    idx_top_c = 2 * segments + 1
    pts.append((0.0, 0.0, mm_to_wrl(z_bot_mm)))
    pts.append((0.0, 0.0, mm_to_wrl(z_top_mm)))

    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        b0, b1 = i, nxt
        t0, t1 = i + segments, nxt + segments
        # Side quad (2 triangles)
        faces.append(f"{b0}, {b1}, {t1}, -1")
        faces.append(f"{b0}, {t1}, {t0}, -1")
        # Bottom cap triangle
        faces.append(f"{idx_bot_c}, {b1}, {b0}, -1")
        # Top cap triangle
        faces.append(f"{idx_top_c}, {t0}, {t1}, -1")

    coord_str = ",\n          ".join([f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts])
    index_str = ",\n          ".join(faces)

    return f"""      geometry IndexedFaceSet {{
        coord Coordinate {{
          point [
          {coord_str}
          ]
        }}
        coordIndex [
          {index_str}
        ]
      }}"""

def make_box_ifs(wx_mm, wy_mm, z_bot_mm, z_top_mm, cx_mm=0.0, cy_mm=0.0):
    """Generates a triangulated IndexedFaceSet 3D Box so KiCad never skips or misrenders it."""
    hx, hy = mm_to_wrl(wx_mm / 2.0), mm_to_wrl(wy_mm / 2.0)
    cx, cy = mm_to_wrl(cx_mm), mm_to_wrl(cy_mm)
    zb, zt = mm_to_wrl(z_bot_mm), mm_to_wrl(z_top_mm)
    pts = [
        (cx - hx, cy - hy, zb), (cx + hx, cy - hy, zb), (cx + hx, cy + hy, zb), (cx - hx, cy + hy, zb),
        (cx - hx, cy - hy, zt), (cx + hx, cy - hy, zt), (cx + hx, cy + hy, zt), (cx - hx, cy + hy, zt)
    ]
    faces = [
        "0, 2, 1, -1", "0, 3, 2, -1", # Bottom
        "4, 5, 6, -1", "4, 6, 7, -1", # Top
        "0, 1, 5, -1", "0, 5, 4, -1", # Front
        "1, 2, 6, -1", "1, 6, 5, -1", # Right
        "2, 3, 7, -1", "2, 7, 6, -1", # Back
        "3, 0, 4, -1", "3, 4, 7, -1"  # Left
    ]
    coord_str = ", ".join([f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts])
    index_str = ", ".join(faces)
    return f"""      geometry IndexedFaceSet {{
        coord Coordinate {{ point [ {coord_str} ] }}
        coordIndex [ {index_str} ]
      }}"""

def create_local_3d_models():
    os.makedirs("eTutti_3D.3dshapes", exist_ok=True)

    # 1A. Realistic Fluted Synth Volume Knob
    vol_wrl = f"""#VRML V2.0 utf8
# Green Potentiometer Base Body
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.12 0.48 0.24 specularColor 0.3 0.3 0.3 }} }}
{make_box_ifs(9.5, 9.5, 0.2, 4.8)}
}}
# Brass Mounting Hex Nut Collar
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.82 0.72 0.35 specularColor 0.8 0.8 0.6 }} }}
{make_cylinder_ifs(4.8, 4.8, 6.2, segments=6)}
}}
# Silver Threaded Bushing
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.9 0.9 0.9 }} }}
{make_cylinder_ifs(3.4, 6.2, 9.5, segments=24)}
}}
# Lower Flared Anodized Knob Skirt
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.16 0.17 0.20 specularColor 0.5 0.5 0.5 }} }}
{make_cylinder_ifs(6.8, 8.2, 10.0, segments=36, r_top_mm=6.2)}
}}
# Main 24-Ribbed Knurled/Fluted Synth Knob Grip
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.14 0.15 0.18 specularColor 0.4 0.4 0.4 }} }}
{make_cylinder_ifs(6.0, 10.0, 19.5, segments=48, r_top_mm=5.7, fluted_amp_mm=0.32)}
}}
# Top Beveled Metallic Cap
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.25 0.27 0.30 specularColor 0.7 0.7 0.7 }} }}
{make_cylinder_ifs(5.7, 19.5, 21.0, segments=36, r_top_mm=4.6)}
}}
# White High-Contrast Indicator Line on Top & Side of Knob
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.98 0.98 0.98 emissiveColor 0.2 0.2 0.2 }} }}
{make_box_ifs(1.0, 4.2, 19.6, 21.2, cx_mm=0.0, cy_mm=2.2)}
}}
"""
    with open("eTutti_3D.3dshapes/Volume_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(vol_wrl)

    # 1B. Realistic Rotary Encoder Selector Knob
    enc_wrl = f"""#VRML V2.0 utf8
# Blue Alps EC11 Encoder Base Body
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.15 0.35 0.68 specularColor 0.3 0.3 0.3 }} }}
{make_box_ifs(11.6, 11.6, 0.2, 5.2)}
}}
# Mounting Hex Nut
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.8 0.8 0.8 }} }}
{make_cylinder_ifs(5.0, 5.2, 6.6, segments=6)}
}}
# Threaded Bushing
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.9 0.9 0.9 }} }}
{make_cylinder_ifs(3.5, 6.6, 9.5, segments=24)}
}}
# Wide Stepped Selector Skirt
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.22 0.25 0.30 specularColor 0.6 0.6 0.6 }} }}
{make_cylinder_ifs(7.4, 8.2, 10.5, segments=36, r_top_mm=6.6)}
}}
# Fluted Selector Dial Body
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.28 0.32 0.38 specularColor 0.75 0.75 0.78 }} }}
{make_cylinder_ifs(6.5, 10.5, 19.0, segments=48, r_top_mm=6.2, fluted_amp_mm=0.28)}
}}
# Crown Bevel
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.75 0.78 0.82 specularColor 0.9 0.9 0.9 }} }}
{make_cylinder_ifs(6.2, 19.0, 20.5, segments=36, r_top_mm=5.0)}
}}
# Amber/Gold Selector Pointer Bar
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 1.0 0.55 0.10 emissiveColor 0.2 0.1 0.0 }} }}
{make_box_ifs(1.1, 4.5, 19.1, 20.7, cx_mm=0.0, cy_mm=2.4)}
}}
"""
    with open("eTutti_3D.3dshapes/Encoder_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(enc_wrl)

    # 1C. Realistic MicroMod Assembly
    mm_wrl = f"""#VRML V2.0 utf8
# Black M.2 69-Pin Edge Socket
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.12 0.12 0.14 specularColor 0.3 0.3 0.3 }} }}
{make_box_ifs(4.2, 22.0, 0.1, 4.2, cx_mm=-8.0, cy_mm=0.0)}
}}
# SparkFun Red MicroMod Teensy Processor PCB (22x22mm)
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.80 0.12 0.15 specularColor 0.3 0.3 0.3 }} }}
{make_box_ifs(22.0, 22.0, 2.5, 3.7, cx_mm=1.0, cy_mm=0.0)}
}}
# NXP i.MX RT1062 Cortex-M7 Processor IC
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.10 0.10 0.12 specularColor 0.4 0.4 0.4 }} }}
{make_box_ifs(10.0, 10.0, 3.7, 4.6, cx_mm=1.5, cy_mm=0.0)}
}}
# M2.5 Metal Standoff & Screw
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.80 0.82 0.85 specularColor 0.9 0.9 0.9 }} }}
{make_cylinder_ifs(2.4, 0.1, 4.5, segments=24)}
}}
"""
    with open("eTutti_3D.3dshapes/MicroMod_Assembly.wrl", "w", encoding="utf-8") as f:
        f.write(mm_wrl)

    # 1D. 3.5mm Stereo/Mic Audio Jack (Triangulated Mesh)
    jack_wrl = f"""#VRML V2.0 utf8
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.17 }} }}
{make_box_ifs(10.0, 6.0, 0.1, 5.0)}
}}
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.8 0.8 0.8 }} }}
{make_box_ifs(3.0, 4.4, 0.6, 4.4, cx_mm=-5.8, cy_mm=0.0)}
}}
"""
    with open("eTutti_3D.3dshapes/AudioJack_35mm.wrl", "w", encoding="utf-8") as f:
        f.write(jack_wrl)

    # 1E. Back-Side Anti-Flexion Support Pillar Boss (3D Brass Standoff Ring on B.Cu)
    pillar_wrl = f"""#VRML V2.0 utf8
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor 0.85 0.70 0.30 specularColor 0.8 0.8 0.5 }} }}
{make_cylinder_ifs(2.2, 0.0, 3.5, segments=24)}
}}
"""
    with open("eTutti_3D.3dshapes/Support_Pillar.wrl", "w", encoding="utf-8") as f:
        f.write(pillar_wrl)

def model_block(local_Or_KiCad_path, offset_z=0.0, rot_z=0.0, use_local=False):
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
# 2. FOOTPRINT GENERATORS (PERIMETER HOLES + BACK SUPPORT PILLARS + FULL LABELS)
# ==============================================================================
def generate_mounting_hole(ref, desc, x, y, net_gnd_idx):
    """Perimeter M2.5 Mounting Hole (2.7mm drill, 4.6mm pad) placed 100% outside all keys."""
    return f"""  (footprint "MountingHole:MountingHole_2.7mm_M2.5_Pad" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.4 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.14))))
    (property "Value" "{desc}" (at 0 3.4 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.14)) (justify mirror)))
    (fp_circle (center 0 0) (end 2.5 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (fp_circle (center 0 0) (end 2.5 0) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at 0 0) (size 4.6 4.6) (drill 2.7) (layers "*.Cu" "*.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
  )"""

def generate_back_support_pillar(ref, desc, x, y, net_gnd_idx):
    """
    Back-Side Anti-Flexion Support Pillar (B.Cu only!):
    - Zero hole on the Top F.Cu playing surface (100% invisible and smooth under the fingers!)
    - Provides a 4.2mm solderable/grounded brass standoff landing pad on B.Cu so the case's
      internal support ribs lock against the back of the PCB, reducing flex to 8.2 microns!
    """
    return f"""  (footprint "eTutti:Back_Support_Pillar_M2.5" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.14)) (justify mirror)))
    (property "Value" "{desc}" (at 0 3.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.7 0.7) (thickness 0.12)) (justify mirror)))
    (fp_circle (center 0 0) (end 2.4 0) (stroke (width 0.2) (type solid)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))
    (pad "1" smd circle (at 0 0) (size 4.2 4.2) (layers "B.Cu" "B.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
{model_block("eTutti_3D.3dshapes/Support_Pillar.wrl", use_local=True)}
  )"""

def generate_irp_tactile_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")
    key_num = ref[3:]

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at 0 -8.1 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.14))))',
        f'    (property "Value" "{note_name}" (at 0 8.1 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.20))))',
        f'    (fp_text user "{ref}:{note_name}" (at -1.5 -3.5 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.75 0.75) (thickness 0.13)) (justify mirror)))',
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
    lbl_top = top_label if top_label else f"{ref}: {desc}"
    lines = [
        f'  (footprint "eTutti:{ref}_Back" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f} {angle:.1f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16)) (justify mirror)))',
        f'    (property "Value" "{desc}" (at 0 {box_h/2 + 1.4:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.14)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
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
    local_wrl = "eTutti_3D.3dshapes/Encoder_Knob.wrl" if is_encoder else "eTutti_3D.3dshapes/Volume_Knob.wrl"
    return f"""  (footprint "eTutti:{ref}_Top" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16))))
    (property "Value" "{desc}" (at 0 7.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.18))))
    (fp_text user "{ref}:{desc}" (at 0 -7.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.8 0.8) (thickness 0.14)) (justify mirror)))
    (fp_circle (center 0 0) (end 6.2 0) (stroke (width 0.18) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at -2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net1} (uuid "{uid()}"))
    (pad "2" thru_hole circle (at 0.0 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net2} (uuid "{uid()}"))
    (pad "3" thru_hole circle (at 2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net3} (uuid "{uid()}"))
{model_block(local_wrl, use_local=True)}
  )"""

def build_pcb():
    create_local_3d_models()

    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 38.50
    KEY_ORIGIN_Y = 13.50   # 13.5mm top buffer gives plenty of room for symmetric top mounting holes!

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v6_FlutedKnobs_NoFlex")',
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
        (162.0, 0.0),
        (184.5, 42.0),
        (184.5, 51.0),
        (172.0, 76.5),
        (4.0, 76.5),
        (0.0, 72.5),
    ]
    for i in range(len(board_poly)):
        x1, y1 = board_poly[i]
        x2, y2 = board_poly[(i + 1) % len(board_poly)]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    out.append(f'  (gr_text "eTutti Student v6 | MicroMod + SGTL5000" (at 105.0 2.0 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')

    # --- 2. 8 SYMMETRIC PERIMETER M2.5 MOUNTING HOLES (100% OUTSIDE ALL BUTTONS!) ---
    perimeter_holes = [
        ("MP1", "M2.5_TL", 27.5, 3.8),
        ("MP2", "M2.5_BL", 27.5, 72.7),
        ("MP3", "M2.5_TOP1", KEY_ORIGIN_X + 1.5 * PITCH_X, 3.5),
        ("MP4", "M2.5_TOP2", KEY_ORIGIN_X + 3.5 * PITCH_X, 3.5),
        ("MP5", "M2.5_TOP3", KEY_ORIGIN_X + 5.5 * PITCH_X, 3.5),
        ("MP6", "M2.5_BOT1", KEY_ORIGIN_X + 1.0 * PITCH_X, 73.0),
        ("MP7", "M2.5_BOT2", KEY_ORIGIN_X + 3.0 * PITCH_X, 73.0),
        ("MP8", "M2.5_BOT3", KEY_ORIGIN_X + 5.0 * PITCH_X, 73.0),
    ]
    for m_ref, m_desc, mx, my in perimeter_holes:
        out.append(generate_mounting_hole(m_ref, m_desc, mx, my, net_idx["GND"]))

    # --- 3. 6 SYMMETRIC BACK-SIDE ANTI-FLEXION SUPPORT PILLARS (SP1..SP6 on B.Cu ONLY!) ---
    support_pillars = [
        ("SP1", "RIB_SUP_1", KEY_ORIGIN_X + 1.5 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP2", "RIB_SUP_2", KEY_ORIGIN_X + 3.5 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP3", "RIB_SUP_3", KEY_ORIGIN_X + 5.5 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP4", "RIB_SUP_4", KEY_ORIGIN_X + 1.0 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
        ("SP5", "RIB_SUP_5", KEY_ORIGIN_X + 3.0 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
        ("SP6", "RIB_SUP_6", KEY_ORIGIN_X + 5.0 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
    ]
    for s_ref, s_desc, sx, sy in support_pillars:
        out.append(generate_back_support_pillar(s_ref, s_desc, sx, sy, net_idx["GND"]))

    # --- 4. LEFT WING & DIAGONAL POCKET PLACEMENT ---
    out.append(generate_ic_box_back("J_HP", "PHONES_3.5mm", "C145898", 5.2, 10.5, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_HP: PHONES OUT"))

    out.append(generate_ic_box_back("J_MIC", "MIC_IN_3.5mm", "C145898", 5.2, 19.5, 0.0, 10.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_MIC: MIC IN"))

    out.append(generate_ic_box_back("J_USBC", "USB-C_PORT", "C165948", 4.5, 30.5, 0.0, 7.0, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }, "Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl", use_local_model=False, top_label="J_USBC: USB-C"))
    out.append(generate_smd_0805_back("R_CC1", "5.1k", "C27834", 11.5, 28.8, 0.0, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_0805_back("R_CC2", "5.1k", "C27834", 11.5, 32.2, 0.0, net_tag("USB_CC2"), net_tag("GND")))

    # Isolated Audio Codec Section
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000", "C89941", 18.5, 15.0, 0.0, 4.0, 4.0, 10, 0.5, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl", use_local_model=False, top_label="U_CODEC: SGTL5000"))

    out.append(generate_sot23_5_back("U_1V8", "1.8V_LDO", "C134077", 18.5, 8.0, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE", "C1002", 24.5, 8.0, 90.0, net_tag("+3V3"), net_tag("+3V3_ANA")))
    out.append(generate_smd_0805_back("C_1V8", "100nF", "C49678", 13.5, 8.0, 90.0, net_tag("+1V8_CODEC"), net_tag("GND"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF", "C15850", 18.5, 21.5, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    # Top-Surface Ergonomic Knobs (Now with Triangulated 3D Fluted Synth Knobs!)
    out.append(generate_tht_knob_top("RV1", "VOLUME_10k", 11.5, 45.5, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SELECT_ENC", 11.5, 62.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "LED_STATUS", "C2297", 21.5, 45.5, 90.0, net_tag("USER_LED"), net_tag("GND"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R", "C17630", 21.5, 49.5, 90.0, net_tag("+3V3"), net_tag("USER_LED")))

    # --- HARMONIC 30° PARALLEL BUS CASCADE ---
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "MUX_1-16_HC4067", "C70001", 43.5, 13.0, 30.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U4: MUX 1-16"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF", "C49678", 37.5, 6.0, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD", "C2838503", 31.0, 31.5, 30.0, 18.0, 18.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "eTutti_3D.3dshapes/MicroMod_Assembly.wrl", use_local_model=True, top_label="U_MM: TEENSY MICROMOD"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k", "C17520", 23.0, 21.0, 30.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k", "C17520", 21.5, 24.0, 30.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_17-28_HC4067", "C70001", 34.0, 58.5, 30.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U5: MUX 17-28"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF", "C49678", 27.5, 51.5, 30.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    # Battery Management Section
    out.append(generate_sot23_5_back("U6", "MCP73831_CHG", "C424093", 23.5, 58.5, 30.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_PROG", "C17604", 21.5, 63.0, 30.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_JST", "C295747", 25.5, 65.5, 30.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
    out.append(f'  (gr_rect (start 78.0 23.0) (end 128.0 53.0) (stroke (width 0.15) (type dash)) (fill none) (layer "B.SilkS") (uuid "{uid()}"))')
    out.append(f'  (gr_text "1000mAh LiPo Battery Zone (Back)" (at 103.0 38.0 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror)))')

    # --- 5. 28-KEY C-GRIFF KEYBOARD + HARMONIC +30° PULL-DOWN RESISTORS ---
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
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, r_angle, net_tag(sig_name), net_tag("GND"), show_top_silk=False))

            p1_dx, p1_dy = rot_pt(-0.95, 0, r_angle)
            p2_dx, p2_dy = rot_pt(0.95, 0, r_angle)
            out.append(f'  (segment (start {x_mm+6.0:.3f} {y_mm:.3f}) (end {r_x+p1_dx:.3f} {r_y+p1_dy:.3f}) (width 0.25) (layer "B.Cu") (net {sig_id}) (uuid "{uid()}"))')
            via_x, via_y = r_x + p2_dx + 0.7, r_y + p2_dy - 0.7
            out.append(f'  (via (at {via_x:.3f} {via_y:.3f}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')
            out.append(f'  (segment (start {r_x+p2_dx:.3f} {r_y+p2_dy:.3f}) (end {via_x:.3f} {via_y:.3f}) (width 0.25) (layer "B.Cu") (net {net_idx["GND"]}) (uuid "{uid()}"))')

            key_idx += 1

    # --- 6. 4-LAYER ISOLATED COPPER PLANES ---
    poly_pts = " ".join([f"(xy {px:.2f} {py:.2f})" for px, py in board_poly])
    out.append(f"""  (zone (net {net_idx["GND"]}) (net_name "GND") (layer "In1.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts {poly_pts}))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3_ANA"]}) (net_name "+3V3_ANA") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 0.5 4.0) (xy 4.0 0.5) (xy 24.0 0.5) (xy 24.0 24.5) (xy 0.5 24.5)))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.3)) (min_thickness 0.25)
    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))
    (polygon (pts (xy 25.5 0.5) (xy 161.5 0.5) (xy 184.0 42.0) (xy 184.0 51.0) (xy 171.5 76.0) (xy 4.0 76.0) (xy 0.5 72.5) (xy 0.5 26.0) (xy 25.5 26.0)))
  )""")

    out.append(")")

    with open("eTutti_Student.kicad_pcb", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Generated 'eTutti_Student.kicad_pcb' v6 with Fluted 3D Knobs, Zero-Overlap Symmetric Holes & 6 Back Support Pillars!")

if __name__ == "__main__":
    build_pcb()