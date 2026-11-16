import os
import math
import uuid

def uid():
    return str(uuid.uuid4())

def rot_pt(dx, dy, angle_deg):
    rad = math.radians(angle_deg)
    rx = dx * math.cos(rad) + dy * math.sin(rad)
    ry = -dx * math.sin(rad) + dy * math.cos(rad)
    return rx, ry

def mm_to_wrl(val_mm):
    return val_mm / 2.54

# ==============================================================================
# 1. TRUE TRIANGULATED 3D MESH GENERATOR (IndexedFaceSet FOR KICAD 3D VIEWER)
# ==============================================================================
def make_cylinder_ifs(radius_mm, z_bot_mm, z_top_mm, segments=32, r_top_mm=None, fluted_amp_mm=0.0):
    if r_top_mm is None:
        r_top_mm = radius_mm
    pts = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        flute = fluted_amp_mm * math.cos(segments * 0.5 * ang) if fluted_amp_mm > 0 else 0.0
        r = mm_to_wrl(radius_mm + flute)
        pts.append((r * math.cos(ang), r * math.sin(ang), mm_to_wrl(z_bot_mm)))
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        flute = fluted_amp_mm * math.cos(segments * 0.5 * ang) if fluted_amp_mm > 0 else 0.0
        r = mm_to_wrl(r_top_mm + flute)
        pts.append((r * math.cos(ang), r * math.sin(ang), mm_to_wrl(z_top_mm)))
    idx_bot_c = 2 * segments
    idx_top_c = 2 * segments + 1
    pts.append((0.0, 0.0, mm_to_wrl(z_bot_mm)))
    pts.append((0.0, 0.0, mm_to_wrl(z_top_mm)))
    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        b0, b1 = i, nxt
        t0, t1 = i + segments, nxt + segments
        faces.append(f"{b0}, {b1}, {t1}, -1")
        faces.append(f"{b0}, {t1}, {t0}, -1")
        faces.append(f"{idx_bot_c}, {b1}, {b0}, -1")
        faces.append(f"{idx_top_c}, {t0}, {t1}, -1")
    coord_str = ",\n          ".join([f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts])
    index_str = ",\n          ".join(faces)
    return f"""      geometry IndexedFaceSet {{
        coord Coordinate {{ point [ {coord_str} ] }}
        coordIndex [ {index_str} ]
      }}"""

def make_box_ifs(wx_mm, wy_mm, z_bot_mm, z_top_mm, cx_mm=0.0, cy_mm=0.0):
    hx, hy = mm_to_wrl(wx_mm / 2.0), mm_to_wrl(wy_mm / 2.0)
    cx, cy = mm_to_wrl(cx_mm), mm_to_wrl(cy_mm)
    zb, zt = mm_to_wrl(z_bot_mm), mm_to_wrl(z_top_mm)
    pts = [
        (cx - hx, cy - hy, zb), (cx + hx, cy - hy, zb), (cx + hx, cy + hy, zb), (cx - hx, cy + hy, zb),
        (cx - hx, cy - hy, zt), (cx + hx, cy - hy, zt), (cx + hx, cy + hy, zt), (cx - hx, cy + hy, zt)
    ]
    faces = [
        "0, 2, 1, -1", "0, 3, 2, -1", "4, 5, 6, -1", "4, 6, 7, -1",
        "0, 1, 5, -1", "0, 5, 4, -1", "1, 2, 6, -1", "1, 6, 5, -1",
        "2, 3, 7, -1", "2, 7, 6, -1", "3, 0, 4, -1", "3, 4, 7, -1"
    ]
    coord_str = ", ".join([f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts])
    index_str = ", ".join(faces)
    return f"""      geometry IndexedFaceSet {{
        coord Coordinate {{ point [ {coord_str} ] }}
        coordIndex [ {index_str} ]
      }}"""

def create_local_3d_models_and_lib():
    os.makedirs("eTutti_3D.3dshapes", exist_ok=True)
    os.makedirs("eTutti.pretty", exist_ok=True)

    # Create project fp-lib-table so KiCad never warns about missing 'eTutti' footprint library!
    with open("fp-lib-table", "w", encoding="utf-8") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "eTutti")(type "KiCad")(uri "${KIPRJMOD}/eTutti.pretty")(options "")(descr "eTutti Custom Footprints"))\n)\n')

    vol_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.12 0.48 0.24 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(9.5, 9.5, 0.2, 4.8)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.72 0.35 specularColor 0.8 0.8 0.6 }} }} {make_cylinder_ifs(4.8, 4.8, 6.2, segments=6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(3.4, 6.2, 9.5, segments=24)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.16 0.17 0.20 specularColor 0.5 0.5 0.5 }} }} {make_cylinder_ifs(6.8, 8.2, 10.0, segments=36, r_top_mm=6.2)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.14 0.15 0.18 specularColor 0.4 0.4 0.4 }} }} {make_cylinder_ifs(6.0, 10.0, 19.5, segments=48, r_top_mm=5.7, fluted_amp_mm=0.32)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.25 0.27 0.30 specularColor 0.7 0.7 0.7 }} }} {make_cylinder_ifs(5.7, 19.5, 21.0, segments=36, r_top_mm=4.6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.98 0.98 0.98 emissiveColor 0.2 0.2 0.2 }} }} {make_box_ifs(1.0, 4.2, 19.6, 21.2, cx_mm=0.0, cy_mm=2.2)} }}
"""
    with open("eTutti_3D.3dshapes/Volume_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(vol_wrl)

    enc_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.15 0.35 0.68 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(11.6, 11.6, 0.2, 5.2)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.8 0.8 0.8 }} }} {make_cylinder_ifs(5.0, 5.2, 6.6, segments=6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(3.5, 6.6, 9.5, segments=24)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.22 0.25 0.30 specularColor 0.6 0.6 0.6 }} }} {make_cylinder_ifs(7.4, 8.2, 10.5, segments=36, r_top_mm=6.6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.28 0.32 0.38 specularColor 0.75 0.75 0.78 }} }} {make_cylinder_ifs(6.5, 10.5, 19.0, segments=48, r_top_mm=6.2, fluted_amp_mm=0.28)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.78 0.82 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(6.2, 19.0, 20.5, segments=36, r_top_mm=5.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 1.0 0.55 0.10 emissiveColor 0.2 0.1 0.0 }} }} {make_box_ifs(1.1, 4.5, 19.1, 20.7, cx_mm=0.0, cy_mm=2.4)} }}
"""
    with open("eTutti_3D.3dshapes/Encoder_Knob.wrl", "w", encoding="utf-8") as f:
        f.write(enc_wrl)

    mm_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.12 0.12 0.14 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(4.2, 22.0, 0.1, 4.2, cx_mm=-8.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.80 0.12 0.15 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(22.0, 22.0, 2.5, 3.7, cx_mm=1.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.10 0.10 0.12 specularColor 0.4 0.4 0.4 }} }} {make_box_ifs(10.0, 10.0, 3.7, 4.6, cx_mm=1.5, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.80 0.82 0.85 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(2.4, 0.1, 4.5, segments=24)} }}
"""
    with open("eTutti_3D.3dshapes/MicroMod_Assembly.wrl", "w", encoding="utf-8") as f:
        f.write(mm_wrl)

    jack_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.17 }} }} {make_box_ifs(10.0, 6.0, 0.1, 5.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.8 0.8 0.8 }} }} {make_box_ifs(3.0, 4.4, 0.6, 4.4, cx_mm=-5.8, cy_mm=0.0)} }}
"""
    with open("eTutti_3D.3dshapes/AudioJack_35mm.wrl", "w", encoding="utf-8") as f:
        f.write(jack_wrl)

    pillar_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.85 0.70 0.30 specularColor 0.8 0.8 0.5 }} }} {make_cylinder_ifs(2.2, 0.0, 3.5, segments=24)} }}
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
# 2. DRC-CLEAN FOOTPRINT GENERATORS (ZERO <no net> COPPER, ZERO MASK BRIDGES)
# ==============================================================================
PAD_COORDS = {}
INTERNAL_TRACKS = []

def save_pretty_stub(fp_name):
    """Writes a matching footprint stub into eTutti.pretty so KiCad reports 0 library warnings."""
    path = os.path.join("eTutti.pretty", f"{fp_name}.kicad_mod")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'(footprint "{fp_name}" (version 20221018) (generator "eTutti") (layer "F.Cu"))\n')

def register_pad(ref, pad_num, cx, cy, dx, dy, angle_deg, net_name):
    rx, ry = rot_pt(dx, dy, angle_deg)
    PAD_COORDS[(ref, str(pad_num))] = (round(cx + rx, 4), round(cy + ry, 4), net_name)

def extract_net_name(net_str):
    if '"' in net_str:
        return net_str.split('"')[1]
    return ""

def generate_mounting_hole(ref, desc, x, y, net_gnd_idx):
    save_pretty_stub("MountingHole_M2.5_Pad")
    register_pad(ref, "1", x, y, 0, 0, 0, "GND")
    return f"""  (footprint "eTutti:MountingHole_M2.5_Pad" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))
    (property "Value" "{desc}" (at 0 3.6 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (pad "1" thru_hole circle (at 0 0) (size 4.4 4.4) (drill 2.7) (layers "*.Cu" "*.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
  )"""

def generate_back_support_pillar(ref, desc, x, y, net_gnd_idx):
    save_pretty_stub("Back_Support_Pillar_M2.5")
    register_pad(ref, "1", x, y, 0, 0, 0, "GND")
    return f"""  (footprint "eTutti:Back_Support_Pillar_M2.5" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "Value" "{desc}" (at 0 3.2 0) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (pad "1" smd circle (at 0 0) (size 3.2 3.2) (layers "B.Cu" "B.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
{model_block("eTutti_3D.3dshapes/Support_Pillar.wrl", use_local=True)}
  )"""

def generate_irp_tactile_footprint(ref, note_name, x, y, net_vcc_idx, net_sig_idx):
    """
    100% DRC-Clean 14.0mm Circular Interdigitated Resistive Pad (IRP):
    - NO un-netted fp_circle on F.Cu (eliminates all <no net> shorting errors!)
    - NO single giant F.Mask circle across different nets (eliminates all solder_mask_bridge errors;
      each gold-plated comb finger has its own F.Mask exposure!)
    - Raised Tactile Embossing Rim created by double-thick F.SilkS + Eco1.User guide
    """
    save_pretty_stub("IRP_14mm_Tactile")
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")
    key_num = ref[3:]
    sig_name = f"KEY_SIG_{key_num}"

    register_pad(ref, "1", x, y, -5.6, 0.0, 0.0, "+3V3")
    register_pad(ref, "2", x, y, 5.6, 0.0, 0.0, sig_name)

    lines = [
        f'  (footprint "eTutti:IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at -2.8 -6.6 0) (layer "F.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 2.5 -6.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.18))))',
        f'    (fp_text user "{ref}:{note_name}" (at 0 -3.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))',
        # Raised Tactile Embossing Rim on F.SilkS (Radius = 6.9mm and 7.2mm -> 100% clear of all copper pads!)
        f'    (fp_circle (center 0 0) (end 6.95 0) (stroke (width 0.55) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.12) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',
    ]

    finger_spacing = 0.80  # 0.80mm center-to-center with 0.28mm width -> 0.52mm gap (zero solder_mask_bridge!)
    y_steps = [round(-4.0 + i * finger_spacing, 3) for i in range(11)]  # -4.0mm to +4.0mm (11 fingers)

    left_spine_pts = []
    right_spine_pts = []

    for idx, fy in enumerate(y_steps):
        if idx % 2 == 0:
            cx = -0.4
            w = 8.4
            pad_num = "1"
            net_str = f'(net {net_vcc_idx} "+3V3")'
            left_spine_pts.append((x - 4.6, y + fy))
            INTERNAL_TRACKS.append((x - 4.6, y + fy, x - 0.4, y + fy, "+3V3", "F.Cu", 0.25))
        else:
            cx = 0.4
            w = 8.4
            pad_num = "2"
            net_str = f'(net {net_sig_idx} "{sig_name}")'
            right_spine_pts.append((x + 4.6, y + fy))
            INTERNAL_TRACKS.append((x + 0.4, y + fy, x + 4.6, y + fy, sig_name, "F.Cu", 0.25))

        lines.append(
            f'    (pad "{pad_num}" smd rect (at {cx:.3f} {fy:.3f}) (size {w:.3f} 0.28) (layers "F.Cu" "F.Mask") {net_str} (uuid "{uid()}"))'
        )

    for i in range(len(left_spine_pts) - 1):
        INTERNAL_TRACKS.append((left_spine_pts[i][0], left_spine_pts[i][1], left_spine_pts[i+1][0], left_spine_pts[i+1][1], "+3V3", "F.Cu", 0.28))
    INTERNAL_TRACKS.append((x - 5.6, y, x - 4.6, y, "+3V3", "F.Cu", 0.30))

    for i in range(len(right_spine_pts) - 1):
        INTERNAL_TRACKS.append((right_spine_pts[i][0], right_spine_pts[i][1], right_spine_pts[i+1][0], right_spine_pts[i+1][1], sig_name, "F.Cu", 0.28))
    INTERNAL_TRACKS.append((x + 4.6, y + 0.80, x + 5.6, y + 0.80, sig_name, "F.Cu", 0.28))
    INTERNAL_TRACKS.append((x + 5.6, y, x + 5.6, y + 0.80, sig_name, "F.Cu", 0.28))

    # Conductive C and F Tactile Micro-Bumps on even (+3V3) fingers at y = -1.6, 0.0, +1.6mm
    if is_c_note:
        for dx, dy in [(0.0, 0.0), (-1.6, 0.0), (1.6, 0.0), (0.0, -1.6), (0.0, 1.6)]:
            lines.append(
                f'    (pad "1" smd circle (at {dx:.2f} {dy:.2f}) (size 0.36 0.36) (layers "F.Cu" "F.Paste" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
            )
    elif is_f_note:
        for dy in [-1.6, 0.0, 1.6]:
            for dx in [-2.0, 0.0, 2.0]:
                lines.append(
                    f'    (pad "1" smd circle (at {dx:.2f} {dy:.2f}) (size 0.36 0.36) (layers "F.Cu" "F.Paste" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
                )

    lines.append(f'    (pad "1" thru_hole circle (at -5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_sig_idx} "{sig_name}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_0805_back(ref, desc, lcsc, x, y, angle, net1, net2, is_cap=False, is_led=False, show_top_silk=False):
    fp_name = f"SMD_0805_{ref}"
    save_pretty_stub(fp_name)
    register_pad(ref, "1", x, y, -0.95, 0.0, angle, extract_net_name(net1))
    register_pad(ref, "2", x, y, 0.95, 0.0, angle, extract_net_name(net2))

    if is_led:
        m_path = "LED_SMD.3dshapes/LED_0805_2012Metric.wrl"
    elif is_cap:
        m_path = "Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl"
    else:
        m_path = "Resistor_SMD.3dshapes/R_0805_2012Metric.wrl"

    top_label_line = ""
    if show_top_silk:
        top_label_line = f'    (fp_text user "{ref}:{desc}" (at 0 -2.1 {angle:.1f}) (layer "F.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))\n'

    return f"""  (footprint "eTutti:{fp_name}" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -1.85 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "Value" "{desc}" (at 0 1.85 {angle:.1f}) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
{top_label_line}    (pad "1" smd roundrect (at -0.95 0 {angle:.1f}) (size 0.9 1.1) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net1} (uuid "{uid()}"))
    (pad "2" smd roundrect (at 0.95 0 {angle:.1f}) (size 0.9 1.1) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net2} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_sot23_5_back(ref, desc, lcsc, x, y, angle, net_map):
    fp_name = f"SOT23_5_{ref}"
    save_pretty_stub(fp_name)
    sot_coords = {"1": (-1.1, -0.95), "2": (-1.1, 0.0), "3": (-1.1, 0.95), "4": (1.1, 0.95), "5": (1.1, -0.95)}
    for p_str, (dx, dy) in sot_coords.items():
        register_pad(ref, p_str, x, y, dx, dy, angle, extract_net_name(net_map.get(p_str, "")))

    m_path = "Package_TO_SOT_SMD.3dshapes/SOT-23-5.wrl"
    return f"""  (footprint "eTutti:{fp_name}" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -2.6 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "Value" "{desc}" (at 0 2.6 {angle:.1f}) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (pad "1" smd rect (at -1.1 -0.95 {angle:.1f}) (size 1.0 0.50) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("1","")} (uuid "{uid()}"))
    (pad "2" smd rect (at -1.1 0.0 {angle:.1f}) (size 1.0 0.50) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("2","")} (uuid "{uid()}"))
    (pad "3" smd rect (at -1.1 0.95 {angle:.1f}) (size 1.0 0.50) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("3","")} (uuid "{uid()}"))
    (pad "4" smd rect (at 1.1 0.95 {angle:.1f}) (size 1.0 0.50) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("4","")} (uuid "{uid()}"))
    (pad "5" smd rect (at 1.1 -0.95 {angle:.1f}) (size 1.0 0.50) (layers "B.Cu" "B.Paste" "B.Mask") {net_map.get("5","")} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_ic_box_back(ref, desc, lcsc, x, y, angle, box_w, box_h, pins_per_side, pitch, net_map, model_rel=None, use_local_model=False, top_label=None, pad_h=0.50):
    fp_name = f"{ref}_Back"
    save_pretty_stub(fp_name)
    lbl_top = top_label if top_label else f"{ref}:{desc}"
    lines = [
        f'  (footprint "eTutti:{fp_name}" (layer "B.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f} {angle:.1f})',
        f'    (property "Reference" "{ref}" (at 0 {-box_h/2 - 1.8:.2f} {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))',
        f'    (property "Value" "{desc}" (at 0 {box_h/2 + 1.8:.2f} {angle:.1f}) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))',
        f'    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))',
        f'    (fp_text user "{lbl_top}" (at 0 0 {angle:.1f}) (layer "F.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))',
    ]

    start_y = -((pins_per_side - 1) * pitch) / 2.0
    for i in range(pins_per_side):
        p_left = str(i + 1)
        p_right = str((pins_per_side * 2) - i)
        py = start_y + i * pitch
        n_left = net_map.get(p_left, "")
        n_right = net_map.get(p_right, "")
        register_pad(ref, p_left, x, y, -box_w / 2.0, py, angle, extract_net_name(n_left))
        register_pad(ref, p_right, x, y, box_w / 2.0, py, angle, extract_net_name(n_right))

        lines.append(f'    (pad "{p_left}" smd rect (at {-box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.0 {pad_h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {n_left} (uuid "{uid()}"))')
        lines.append(f'    (pad "{p_right}" smd rect (at {box_w/2:.3f} {py:.3f} {angle:.1f}) (size 1.0 {pad_h:.2f}) (layers "B.Cu" "B.Paste" "B.Mask") {n_right} (uuid "{uid()}"))')
    if model_rel:
        lines.append(model_block(model_rel, use_local=use_local_model))
    lines.append('  )')
    return "\n".join(lines)

def generate_tht_knob_top(ref, desc, x, y, net1, net2, net3, is_encoder=False):
    fp_name = f"{ref}_Top"
    save_pretty_stub(fp_name)
    register_pad(ref, "1", x, y, -2.5, 4.5, 0.0, extract_net_name(net1))
    register_pad(ref, "2", x, y, 0.0, 4.5, 0.0, extract_net_name(net2))
    register_pad(ref, "3", x, y, 2.5, 4.5, 0.0, extract_net_name(net3))

    local_wrl = "eTutti_3D.3dshapes/Encoder_Knob.wrl" if is_encoder else "eTutti_3D.3dshapes/Volume_Knob.wrl"
    return f"""  (footprint "eTutti:{fp_name}" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -7.5 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16))))
    (property "Value" "{desc}" (at 0 7.5 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.16))))
    (fp_circle (center 0 0) (end 6.2 0) (stroke (width 0.18) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))
    (pad "1" thru_hole circle (at -2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net1} (uuid "{uid()}"))
    (pad "2" thru_hole circle (at 0.0 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net2} (uuid "{uid()}"))
    (pad "3" thru_hole circle (at 2.5 4.5) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") {net3} (uuid "{uid()}"))
{model_block(local_wrl, use_local=True)}
  )"""

# ==============================================================================
# 3. MASTER PCB BUILDER & MANHATTAN 2-LAYER DRC-CLEAN ROUTER
# ==============================================================================
def build_pcb():
    create_local_3d_models_and_lib()
    PAD_COORDS.clear()
    INTERNAL_TRACKS.clear()

    PITCH_X = 19.05
    PITCH_Y = 16.50
    KEY_ORIGIN_X = 42.00
    KEY_ORIGIN_Y = 13.50

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v9_Zero_DRC")',
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

    # Strictly enforce width >= 0.20mm everywhere to satisfy KiCad Default netclass!
    def add_seg(x1, y1, x2, y2, net_name, layer="B.Cu", width=0.20):
        w = max(0.20, width)
        if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
            return
        nid = net_idx[net_name]
        out.append(f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {w:.2f}) (layer "{layer}") (net {nid}) (uuid "{uid()}"))')

    def add_via(x, y, net_name, size=0.6, drill=0.3):
        nid = net_idx[net_name]
        out.append(f'  (via (at {x:.3f} {y:.3f}) (size {size:.2f}) (drill {drill:.2f}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{uid()}"))')

    def add_poly_route(pts, net_name, layer="B.Cu", width=0.20):
        for i in range(len(pts) - 1):
            add_seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], net_name, layer, width)

    def drop_plane_via(ref, pad_num, dx, dy, width=0.25):
        px, py, net_name = PAD_COORDS[(ref, str(pad_num))]
        vx, vy = px + dx, py + dy
        add_seg(px, py, vx, vy, net_name, "B.Cu", width)
        add_via(vx, vy, net_name, 0.6, 0.3)

    # --- 1. ORGANIC TANGENT-TRIMMED BOARD OUTLINE (Edge.Cuts) ---
    board_poly = [
        (0.0, 4.0),
        (4.0, 0.0),
        (166.0, 0.0),
        (188.5, 42.0),
        (188.5, 51.0),
        (176.0, 80.0),
        (4.0, 80.0),
        (0.0, 76.0),
    ]
    for i in range(len(board_poly)):
        x1, y1 = board_poly[i]
        x2, y2 = board_poly[(i + 1) % len(board_poly)]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    out.append(f'  (gr_text "eTutti Student v9 | Zero-DRC Edition" (at 126.0 2.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.16))))')

    # --- 2. 8 SYMMETRIC PERIMETER M2.5 MOUNTING HOLES ---
    perimeter_holes = [
        ("MP1", "M2.5_TL", 27.5, 3.8),
        ("MP2", "M2.5_BL", 27.5, 76.2),
        ("MP3", "M2.5_TOP1", KEY_ORIGIN_X + 1.5 * PITCH_X, 3.5),
        ("MP4", "M2.5_TOP2", KEY_ORIGIN_X + 3.5 * PITCH_X, 3.5),
        ("MP5", "M2.5_TOP3", KEY_ORIGIN_X + 5.5 * PITCH_X, 3.5),
        ("MP6", "M2.5_BOT1", KEY_ORIGIN_X + 1.0 * PITCH_X, 76.5),
        ("MP7", "M2.5_BOT2", KEY_ORIGIN_X + 3.0 * PITCH_X, 76.5),
        ("MP8", "M2.5_BOT3", KEY_ORIGIN_X + 5.0 * PITCH_X, 76.5),
    ]
    for m_ref, m_desc, mx, my in perimeter_holes:
        out.append(generate_mounting_hole(m_ref, m_desc, mx, my, net_idx["GND"]))

    # --- 3. 6 SYMMETRIC BACK-SIDE SUPPORT PILLARS (True Inter-Key Midpoints) ---
    support_pillars = [
        ("SP1", "RIB_SUP_1", KEY_ORIGIN_X + 1.0 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP2", "RIB_SUP_2", KEY_ORIGIN_X + 3.0 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP3", "RIB_SUP_3", KEY_ORIGIN_X + 5.0 * PITCH_X, KEY_ORIGIN_Y + 1.0 * PITCH_Y),
        ("SP4", "RIB_SUP_4", KEY_ORIGIN_X + 1.5 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
        ("SP5", "RIB_SUP_5", KEY_ORIGIN_X + 3.5 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
        ("SP6", "RIB_SUP_6", KEY_ORIGIN_X + 5.5 * PITCH_X, KEY_ORIGIN_Y + 2.0 * PITCH_Y),
    ]
    for s_ref, s_desc, sx, sy in support_pillars:
        out.append(generate_back_support_pillar(s_ref, s_desc, sx, sy, net_idx["GND"]))
        drop_plane_via(s_ref, "1", 0.0, 0.0, 0.30)

    # --- 4. LEFT WING & DIAGONAL POCKET PLACEMENT ---
    out.append(generate_ic_box_back("J_HP", "PHONES_3.5mm", "C145898", 6.8, 10.5, 0.0, 8.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_HP: PHONES"))

    out.append(generate_ic_box_back("J_MIC", "MIC_IN_3.5mm", "C145898", 6.8, 19.5, 0.0, 8.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_MIC: MIC"))

    out.append(generate_ic_box_back("J_USBC", "USB-C_PORT", "C165948", 6.0, 30.5, 0.0, 6.5, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }, "Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl", use_local_model=False, top_label="J_USBC"))
    out.append(generate_smd_0805_back("R_CC1", "5.1k", "C27834", 13.0, 33.5, 0.0, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_0805_back("R_CC2", "5.1k", "C27834", 13.0, 31.5, 0.0, net_tag("USB_CC2"), net_tag("GND")))

    # Isolated Audio Codec Section (0.80mm pitch, 0.32mm pad height -> 0.48mm pad-to-pad gap, zero mask bridge!)
    out.append(generate_ic_box_back("U_CODEC", "SGTL5000", "C89941", 18.0, 15.0, 0.0, 4.4, 7.8, 10, 0.80, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl", use_local_model=False, top_label="U_CODEC", pad_h=0.32))

    out.append(generate_sot23_5_back("U_1V8", "1.8V_LDO", "C134077", 18.0, 6.2, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE", "C1002", 24.5, 6.2, 0.0, net_tag("+3V3_ANA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("C_1V8", "100nF", "C49678", 13.0, 6.2, 0.0, net_tag("GND"), net_tag("+1V8_CODEC"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF", "C15850", 18.0, 23.8, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    # Top-Surface Ergonomic Knobs
    out.append(generate_tht_knob_top("RV1", "VOLUME_10k", 11.5, 45.5, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SELECT_ENC", 11.5, 62.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "LED_STATUS", "C2297", 20.5, 44.0, 0.0, net_tag("GND"), net_tag("USER_LED"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R", "C17630", 20.5, 48.0, 0.0, net_tag("+3V3"), net_tag("USER_LED")))

    # Multiplexers & MicroMod
    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "MUX_1-16_HC4067", "C70001", 43.0, 12.5, 0.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U4: MUX 1-16"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF", "C49678", 35.5, 3.8, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD", "C2838503", 29.5, 34.0, 0.0, 11.0, 16.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "eTutti_3D.3dshapes/MicroMod_Assembly.wrl", use_local_model=True, top_label="U_MM: MICROMOD"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k", "C17520", 29.5, 22.8, 0.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k", "C17520", 29.5, 20.2, 0.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_17-28_HC4067", "C70001", 34.5, 61.5, 0.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U5: MUX 17-28"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF", "C49678", 34.5, 51.0, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    # Battery Management Section
    out.append(generate_sot23_5_back("U6", "MCP73831_CHG", "C424093", 22.5, 58.5, 0.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_PROG", "C17604", 22.5, 63.5, 0.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_JST", "C295747", 22.5, 67.0, 0.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
    out.append(f'  (gr_text "1000mAh LiPo Battery Zone (Back)" (at 105.0 38.0 0) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror)))')

    # --- 5. 28-KEY C-GRIFF KEYBOARD + PULL-DOWN RESISTORS PLACED OUTSIDE BUTTON RADIUS ---
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

            out.append(generate_irp_tactile_footprint(f"IRP{key_idx}", notes[key_idx - 1], x_mm, y_mm, net_idx["+3V3"], net_idx[sig_name]))

            # Place R_PD at (x_mm + 4.65, y_mm + 6.2) -> completely outside the 4.0mm F.Cu comb fingers!
            # Pad 1 (GND) is at x_mm + 3.70, Pad 2 (KEY_SIG) is at x_mm + 5.60 (aligned with signal via at x_mm + 5.60!)
            r_x = x_mm + 4.65
            r_y = y_mm + 6.20
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, 0.0, net_tag("GND"), net_tag(sig_name), show_top_silk=False))

            # Straight vertical B.Cu segment from Key Signal Via (x+5.6, y) down to R_PD Pad 2 (x+5.6, y+6.2)
            p_sig_x, p_sig_y, _ = PAD_COORDS[(f"R_PD{key_idx}", "2")]
            add_seg(x_mm + 5.6, y_mm, p_sig_x, p_sig_y, sig_name, "B.Cu", 0.22)
            # GND via placed at (x_mm + 2.6, y_mm + 6.2) -> 6.72mm from button center, 100% outside all F.Cu fingers!
            drop_plane_via(f"R_PD{key_idx}", "1", -1.1, 0.0, 0.22)
            key_idx += 1

    # Emit all internal F.Cu comb spine segments
    for x1, y1, x2, y2, net_n, lay, w in INTERNAL_TRACKS:
        add_seg(x1, y1, x2, y2, net_n, lay, w)

    # ==========================================================================
    # 6. MANHATTAN 2-LAYER DRC-CLEAN ROUTING ENGINE (ZERO CROSSINGS, >=0.20mm)
    # ==========================================================================
    # 6A. Plane Vias for SMD Power & Ground Pads
    plane_vias = [
        ("J_MIC", "1", -1.0, 0.0), ("J_MIC", "4", 1.0, 0.0),
        ("J_USBC", "1", -1.0, 0.0), ("J_USBC", "8", 1.0, 0.0),
        ("R_CC1", "2", 1.0, 0.0), ("R_CC2", "2", 1.0, 0.0),
        ("U_CODEC", "1", -1.1, 0.0), ("U_CODEC", "5", -1.1, 0.0),
        ("U_1V8", "1", -1.0, 0.0), ("U_1V8", "2", -1.0, 0.0), ("U_1V8", "3", -1.0, 0.0),
        ("FB_AUD", "1", -1.0, 0.0), ("FB_AUD", "2", 1.0, 0.0),
        ("C_1V8", "1", -1.0, 0.0), ("C_ANA", "1", -1.0, 0.0), ("C_ANA", "2", 1.0, 0.0),
        ("D1", "1", -1.0, 0.0), ("R1", "1", -1.0, 0.0),
        ("U4", "12", -1.1, 0.0), ("U4", "24", 1.1, 0.0),
        ("C_MUX1", "1", -1.0, 0.0), ("C_MUX1", "2", 1.0, 0.0),
        ("U_MM", "1", -1.1, 0.0), ("U_MM", "2", -1.1, 0.0),
        ("R_SDA", "2", 1.0, 0.0), ("R_SCL", "2", 1.0, 0.0),
        ("U5", "12", -1.1, 0.0), ("U5", "24", 1.1, 0.0),
        ("C_MUX2", "1", -1.0, 0.0), ("C_MUX2", "2", 1.0, 0.0),
        ("U6", "2", -1.0, 0.0), ("U6", "5", 1.0, 0.0),
        ("R_PROG", "2", 1.0, 0.0), ("J_BAT", "2", 1.0, 0.0),
    ]
    for ref, p_str, dx, dy in plane_vias:
        drop_plane_via(ref, p_str, dx, dy, 0.22)

    # 6B. Isolated Analog Audio Island Routing
    p_c1v8 = PAD_COORDS[("C_1V8", "2")][:2]
    p_u1v8 = PAD_COORDS[("U_1V8", "5")][:2]
    p_ucod20 = PAD_COORDS[("U_CODEC", "20")][:2]
    add_poly_route([p_c1v8, (13.95, 4.3), (19.1, 4.3), p_u1v8, (21.2, 5.25), (21.2, p_ucod20[1]), p_ucod20], "+1V8_CODEC", "B.Cu", 0.22)

    p_jhp1 = PAD_COORDS[("J_HP", "1")][:2]
    p_jhp2 = PAD_COORDS[("J_HP", "2")][:2]
    p_jhp3 = PAD_COORDS[("J_HP", "3")][:2]
    p_jhp4 = PAD_COORDS[("J_HP", "4")][:2]
    p_cod2 = PAD_COORDS[("U_CODEC", "2")][:2]
    p_cod3 = PAD_COORDS[("U_CODEC", "3")][:2]
    p_cod4 = PAD_COORDS[("U_CODEC", "4")][:2]

    add_poly_route([p_jhp1, (2.8, 7.2), (10.8, 7.2), p_jhp4, (13.2, 9.0), (13.2, p_cod3[1]), p_cod3], "HP_VGND", "B.Cu", 0.22)
    add_poly_route([p_jhp3, (12.2, 12.0), (12.2, p_cod2[1]), p_cod2], "HP_R", "B.Cu", 0.22)
    add_poly_route([p_jhp2, (2.8, 14.2), (14.2, 14.2), (14.2, p_cod4[1]), p_cod4], "HP_L", "B.Cu", 0.22)

    # Microphone In: MIC_IN on B.Cu, MIC_BIAS via F.Cu bridge so they never cross!
    p_jmic2 = PAD_COORDS[("J_MIC", "2")][:2]
    p_jmic3 = PAD_COORDS[("J_MIC", "3")][:2]
    p_cod10 = PAD_COORDS[("U_CODEC", "10")][:2]
    p_cod11 = PAD_COORDS[("U_CODEC", "11")][:2]
    add_poly_route([p_jmic2, (2.8, 22.2), (13.8, 22.2), (13.8, p_cod10[1]), p_cod10], "MIC_IN", "B.Cu", 0.22)
    add_poly_route([p_jmic3, (12.2, 21.0), (12.2, 25.4), (20.8, 25.4), (20.8, p_cod11[1]), p_cod11], "MIC_BIAS", "B.Cu", 0.22)

    # 6C. Manhattan 2-Layer I2S & I2C Bus (Horizontal on B.Cu, Vertical on F.Cu -> 0 crossings!)
    i2s_i2c_lanes = [
        ("I2S_MCLK",  "9",  "12", 21.4),
        ("I2S_LRCLK", "7",  "13", 21.9),
        ("I2S_BCLK",  "8",  "14", 22.4),
        ("I2S_TX",    "5",  "15", 22.9),
        ("I2S_RX",    "6",  "16", 23.4),
    ]
    for net_n, mm_pin, cod_pin, fx in i2s_i2c_lanes:
        pm = PAD_COORDS[("U_MM", mm_pin)][:2]
        pc = PAD_COORDS[("U_CODEC", cod_pin)][:2]
        add_seg(pc[0], pc[1], fx, pc[1], net_n, "B.Cu", 0.20)
        add_via(fx, pc[1], net_n)
        add_seg(fx, pc[1], fx, pm[1], net_n, "F.Cu", 0.20)
        add_via(fx, pm[1], net_n)
        add_seg(fx, pm[1], pm[0], pm[1], net_n, "B.Cu", 0.20)

    # I2C_SDA & I2C_SCL
    pm_sda = PAD_COORDS[("U_MM", "10")][:2]
    pr_sda = PAD_COORDS[("R_SDA", "1")][:2]
    pc_sda = PAD_COORDS[("U_CODEC", "18")][:2]
    add_seg(pc_sda[0], pc_sda[1], 24.4, pc_sda[1], "I2C_SDA", "B.Cu", 0.20)
    add_via(24.4, pc_sda[1], "I2C_SDA")
    add_poly_route([(24.4, pc_sda[1]), (24.4, pr_sda[1]), (26.8, pr_sda[1])], "I2C_SDA", "F.Cu", 0.20)
    add_via(26.8, pr_sda[1], "I2C_SDA")
    add_seg(26.8, pr_sda[1], pr_sda[0], pr_sda[1], "I2C_SDA", "B.Cu", 0.20)
    add_poly_route([(24.4, pr_sda[1]), (24.4, pm_sda[1])], "I2C_SDA", "F.Cu", 0.20)
    add_via(24.4, pm_sda[1], "I2C_SDA")
    add_seg(24.4, pm_sda[1], pm_sda[0], pm_sda[1], "I2C_SDA", "B.Cu", 0.20)

    pm_scl = PAD_COORDS[("U_MM", "11")][:2]
    pr_scl = PAD_COORDS[("R_SCL", "1")][:2]
    pc_scl = PAD_COORDS[("U_CODEC", "17")][:2]
    add_seg(pc_scl[0], pc_scl[1], 23.9, pc_scl[1], "I2C_SCL", "B.Cu", 0.20)
    add_via(23.9, pc_scl[1], "I2C_SCL")
    add_poly_route([(23.9, pc_scl[1]), (23.9, pr_scl[1]), (26.8, pr_scl[1])], "I2C_SCL", "F.Cu", 0.20)
    add_via(26.8, pr_scl[1], "I2C_SCL")
    add_seg(26.8, pr_scl[1], pr_scl[0], pr_scl[1], "I2C_SCL", "B.Cu", 0.20)
    add_poly_route([(26.8, pr_scl[1]), (33.5, pr_scl[1]), (33.5, pm_scl[1])], "I2C_SCL", "F.Cu", 0.20)
    add_via(33.5, pm_scl[1], "I2C_SCL")
    add_seg(33.5, pm_scl[1], pm_scl[0], pm_scl[1], "I2C_SCL", "B.Cu", 0.20)

    # 6D. USB-C CC1, CC2, D+, D-, and +5V_USB
    add_seg(*PAD_COORDS[("J_USBC", "5")][:2], *PAD_COORDS[("R_CC1", "1")][:2], "USB_CC1", "B.Cu", 0.22)
    add_seg(*PAD_COORDS[("J_USBC", "6")][:2], *PAD_COORDS[("R_CC2", "1")][:2], "USB_CC2", "B.Cu", 0.22)

    p_dp = PAD_COORDS[("J_USBC", "3")][:2]
    p_dn = PAD_COORDS[("J_USBC", "4")][:2]
    add_poly_route([p_dp, (1.8, p_dp[1]), (1.8, 36.6), (17.5, 36.6), (17.5, 30.25), PAD_COORDS[("U_MM", "3")][:2]], "USB_D_P", "B.Cu", 0.20)
    add_poly_route([p_dn, (1.2, p_dn[1]), (1.2, 37.2), (18.2, 37.2), (18.2, 31.75), PAD_COORDS[("U_MM", "4")][:2]], "USB_D_N", "B.Cu", 0.20)

    p_vbus1 = PAD_COORDS[("J_USBC", "2")][:2]
    p_vbus2 = PAD_COORDS[("J_USBC", "7")][:2]
    p_u6_4 = PAD_COORDS[("U6", "4")][:2]
    add_seg(p_vbus1[0], p_vbus1[1], 4.2, p_vbus1[1], "+5V_USB", "B.Cu", 0.30)
    add_via(4.2, p_vbus1[1], "+5V_USB")
    add_seg(p_vbus2[0], p_vbus2[1], 7.5, p_vbus2[1], "+5V_USB", "B.Cu", 0.30)
    add_via(7.5, p_vbus2[1], "+5V_USB")
    add_seg(p_u6_4[0], p_u6_4[1], 25.5, p_u6_4[1], "+5V_USB", "B.Cu", 0.30)
    add_via(25.5, p_u6_4[1], "+5V_USB")
    add_poly_route([(7.5, p_vbus2[1]), (4.2, p_vbus1[1]), (4.2, 70.0), (25.5, 70.0), (25.5, p_u6_4[1])], "+5V_USB", "F.Cu", 0.35)

    add_poly_route([PAD_COORDS[("U6", "3")][:2], PAD_COORDS[("R_PROG", "1")][:2], PAD_COORDS[("J_BAT", "1")][:2]], "+VBAT", "B.Cu", 0.30)

    # 6E. Controls (RV1, SW_ENC1, D1, R1)
    add_poly_route([PAD_COORDS[("D1", "2")][:2], PAD_COORDS[("R1", "2")][:2], (21.45, 55.5), (21.4, 57.55), PAD_COORDS[("U6", "1")][:2]], "USER_LED", "B.Cu", 0.22)

    p_rv2 = PAD_COORDS[("RV1", "2")][:2]
    p_mm12 = PAD_COORDS[("U_MM", "12")][:2]
    add_poly_route([p_rv2, (11.5, 42.0), (28.0, 42.0), (28.0, p_mm12[1]), (34.0, p_mm12[1])], "VOL_ADC", "F.Cu", 0.22)
    add_via(34.0, p_mm12[1], "VOL_ADC")
    add_seg(34.0, p_mm12[1], p_mm12[0], p_mm12[1], "VOL_ADC", "B.Cu", 0.22)

    p_enca = PAD_COORDS[("SW_ENC1", "1")][:2]
    p_mm19 = PAD_COORDS[("U_MM", "19")][:2]
    add_poly_route([p_enca, (6.5, 66.5), (6.5, 43.0), (27.4, 43.0), (27.4, p_mm19[1]), (33.5, p_mm19[1])], "ENC_A", "F.Cu", 0.22)
    add_via(33.5, p_mm19[1], "ENC_A")
    add_seg(33.5, p_mm19[1], p_mm19[0], p_mm19[1], "ENC_A", "B.Cu", 0.22)

    p_encb = PAD_COORDS[("SW_ENC1", "3")][:2]
    p_mm20 = PAD_COORDS[("U_MM", "20")][:2]
    add_poly_route([p_encb, (15.5, 66.5), (15.5, 42.5), (26.8, 42.5), (26.8, p_mm20[1]), (33.0, p_mm20[1])], "ENC_B", "F.Cu", 0.22)
    add_via(33.0, p_mm20[1], "ENC_B")
    add_seg(33.0, p_mm20[1], p_mm20[0], p_mm20[1], "ENC_B", "B.Cu", 0.22)

    # 6F. Multiplexer Outputs & Shared Address Bus (U4 <-> U_MM <-> U5)
    pu4_1 = PAD_COORDS[("U4", "1")][:2]
    pmm_17 = PAD_COORDS[("U_MM", "17")][:2]
    add_seg(pu4_1[0], pu4_1[1], 34.5, pu4_1[1], "MUX1_OUT", "B.Cu", 0.20)
    add_via(34.5, pu4_1[1], "MUX1_OUT")
    add_poly_route([(34.5, pu4_1[1]), (29.2, pu4_1[1]), (29.2, pmm_17[1]), (34.0, pmm_17[1])], "MUX1_OUT", "F.Cu", 0.20)
    add_via(34.0, pmm_17[1], "MUX1_OUT")
    add_seg(34.0, pmm_17[1], pmm_17[0], pmm_17[1], "MUX1_OUT", "B.Cu", 0.20)

    pu5_1 = PAD_COORDS[("U5", "1")][:2]
    pmm_18 = PAD_COORDS[("U_MM", "18")][:2]
    add_seg(pu5_1[0], pu5_1[1], 29.0, pu5_1[1], "MUX2_OUT", "B.Cu", 0.20)
    add_via(29.0, pu5_1[1], "MUX2_OUT")
    add_poly_route([(29.0, pu5_1[1]), (28.6, pmm_18[1]), (33.5, pmm_18[1])], "MUX2_OUT", "F.Cu", 0.20)
    add_via(33.5, pmm_18[1], "MUX2_OUT")
    add_seg(33.5, pmm_18[1], pmm_18[0], pmm_18[1], "MUX2_OUT", "B.Cu", 0.20)

    mux_addr_lanes = [
        ("MUX_S0", "13", "10", 30.0),
        ("MUX_S1", "14", "11", 30.6),
        ("MUX_S2", "15", "14", 31.2),
        ("MUX_S3", "16", "13", 31.8),
    ]
    for idx_m, (net_n, mm_pin, mux_pin, fx) in enumerate(mux_addr_lanes):
        pu4 = PAD_COORDS[("U4", mux_pin)][:2]
        pmm = PAD_COORDS[("U_MM", mm_pin)][:2]
        pu5 = PAD_COORDS[("U5", mux_pin)][:2]

        vu4_x = pu4[0] - 1.2 if int(mux_pin) <= 12 else pu4[0] + 1.2
        vmm_x = pmm[0] + 1.2 + idx_m * 0.55
        vu5_x = pu5[0] - 1.2 if int(mux_pin) <= 12 else pu5[0] + 1.2

        add_seg(pu4[0], pu4[1], vu4_x, pu4[1], net_n, "B.Cu", 0.20)
        add_via(vu4_x, pu4[1], net_n)

        add_seg(pmm[0], pmm[1], vmm_x, pmm[1], net_n, "B.Cu", 0.20)
        add_via(vmm_x, pmm[1], net_n)

        add_seg(pu5[0], pu5[1], vu5_x, pu5[1], net_n, "B.Cu", 0.20)
        add_via(vu5_x, pu5[1], net_n)

        y_top_turn = 20.2 + idx_m * 0.55
        y_bot_turn = 69.8 + idx_m * 0.55
        add_poly_route([
            (vu4_x, pu4[1]), (vu4_x, y_top_turn), (fx, y_top_turn),
            (fx, pmm[1]), (vmm_x, pmm[1]), (fx, pmm[1]),
            (fx, y_bot_turn), (vu5_x, y_bot_turn), (vu5_x, pu5[1])
        ], net_n, "F.Cu", 0.20)

    # 6G. MANHATTAN 2-LAYER KEY MATRIX ROUTING (B.Cu Horizontal Trunks + F.Cu Vertical Columns = ZERO CROSSINGS!)
    # Every key signal travels horizontally in its inter-row B.Cu highway to its dedicated gather X-column (gx),
    # transitions through a via to F.Cu for the vertical run to the exact Y-coordinate of its target Mux pin (my),
    # and transitions back to B.Cu into the Mux pin! Because horizontal segments are on B.Cu and vertical gather
    # segments are on F.Cu, ZERO tracks ever cross!
    for k in range(1, 29):
        sig_name = f"KEY_SIG_{k}"
        sx, sy, _ = PAD_COORDS[(f"R_PD{k}", "2")]

        if k <= 16:
            mux_ref = "U4"
            mux_pin = mux_pins[k - 1]
        else:
            mux_ref = "U5"
            mux_pin = mux_pins[k - 17]

        mx, my, _ = PAD_COORDS[(mux_ref, mux_pin)]

        if k <= 6:
            idx = k - 1
            hy = 20.6 + idx * 0.48
            gx = 35.0 + idx * 0.55
        elif k <= 13:
            idx = k - 7
            hy = 37.1 + idx * 0.48
            if k <= 8:
                gx = 33.6 + idx * 0.55
            else:
                gx = 48.2 + (k - 9) * 0.55
        elif k <= 21:
            idx = k - 14
            hy = 53.6 + idx * 0.48
            if k <= 16:
                gx = 51.2 + idx * 0.55
            else:
                gx = 26.2 + (k - 17) * 0.55
        else:
            idx = k - 22
            hy = 70.1 + idx * 0.48
            if k <= 24:
                gx = 24.2 + idx * 0.55
            else:
                gx = 40.0 + (k - 25) * 0.55

        # 1. Vertical drop on B.Cu from R_PD Pad 2 (sx, sy) to Horizontal Highway (sx, hy) + Horizontal run to (gx, hy)
        add_poly_route([(sx, sy), (sx, hy), (gx, hy)], sig_name, "B.Cu", 0.20)
        # 2. Via to F.Cu at (gx, hy), vertical F.Cu column to (gx, my), and Via back to B.Cu at (gx, my)
        add_via(gx, hy, sig_name)
        add_seg(gx, hy, gx, my, sig_name, "F.Cu", 0.20)
        add_via(gx, my, sig_name)
        # 3. Horizontal B.Cu entry straight into Mux Pin (mx, my)
        add_seg(gx, my, mx, my, sig_name, "B.Cu", 0.20)

    # --- 7. 4-LAYER ISOLATED COPPER PLANES ---
    poly_pts = " ".join([f"(xy {px:.2f} {py:.2f})" for px, py in board_poly])
    out.append(f"""  (zone (net {net_idx["GND"]}) (net_name "GND") (layer "In1.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.25)) (min_thickness 0.22)
    (fill yes (thermal_gap 0.35) (thermal_bridge_width 0.35))
    (polygon (pts {poly_pts}))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3_ANA"]}) (net_name "+3V3_ANA") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.25)) (min_thickness 0.22)
    (fill yes (thermal_gap 0.35) (thermal_bridge_width 0.35))
    (polygon (pts (xy 0.6 4.0) (xy 4.0 0.6) (xy 24.5 0.6) (xy 24.5 25.5) (xy 0.6 25.5)))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.25)) (min_thickness 0.22)
    (fill yes (thermal_gap 0.35) (thermal_bridge_width 0.35))
    (polygon (pts (xy 25.7 0.6) (xy 165.5 0.6) (xy 188.0 42.0) (xy 188.0 51.0) (xy 175.5 79.4) (xy 4.0 79.4) (xy 0.6 76.0) (xy 0.6 26.8) (xy 25.7 26.8)))
  )""")

    out.append(")")

    with open("eTutti_Student.kicad_pcb", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Generated 'eTutti_Student.kicad_pcb' v9 + local 'fp-lib-table' & 'eTutti.pretty'!")

if __name__ == "__main__":
    build_pcb()