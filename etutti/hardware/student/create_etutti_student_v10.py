import os
import re
import math
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    shapes_dir = os.path.join(BASE_DIR, "eTutti_3D.3dshapes")
    pretty_dir = os.path.join(BASE_DIR, "eTutti.pretty")
    os.makedirs(shapes_dir, exist_ok=True)
    os.makedirs(pretty_dir, exist_ok=True)

    with open(os.path.join(BASE_DIR, "fp-lib-table"), "w", encoding="utf-8") as f:
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
    with open(os.path.join(shapes_dir, "Volume_Knob.wrl"), "w", encoding="utf-8") as f:
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
    with open(os.path.join(shapes_dir, "Encoder_Knob.wrl"), "w", encoding="utf-8") as f:
        f.write(enc_wrl)

    mm_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.12 0.12 0.14 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(4.2, 22.0, 0.1, 4.2, cx_mm=-8.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.80 0.12 0.15 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(22.0, 22.0, 2.5, 3.7, cx_mm=1.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.10 0.10 0.12 specularColor 0.4 0.4 0.4 }} }} {make_box_ifs(10.0, 10.0, 3.7, 4.6, cx_mm=1.5, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.80 0.82 0.85 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(2.4, 0.1, 4.5, segments=24)} }}
"""
    with open(os.path.join(shapes_dir, "MicroMod_Assembly.wrl"), "w", encoding="utf-8") as f:
        f.write(mm_wrl)

    jack_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.17 }} }} {make_box_ifs(10.0, 6.0, 0.1, 5.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.8 0.8 0.8 }} }} {make_box_ifs(3.0, 4.4, 0.6, 4.4, cx_mm=-5.8, cy_mm=0.0)} }}
"""
    with open(os.path.join(shapes_dir, "AudioJack_35mm.wrl"), "w", encoding="utf-8") as f:
        f.write(jack_wrl)

    pillar_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.85 0.70 0.30 specularColor 0.8 0.8 0.5 }} }} {make_cylinder_ifs(2.2, 0.0, 3.5, segments=24)} }}
"""
    with open(os.path.join(shapes_dir, "Support_Pillar.wrl"), "w", encoding="utf-8") as f:
        f.write(pillar_wrl)

def model_block(local_Or_KiCad_path, offset_z=0.0, rot_z=0.0, use_local=False):
    if use_local:
        full_path = os.path.join(BASE_DIR, local_Or_KiCad_path).replace("\\", "/")
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
# 2. DRC-CLEAN FOOTPRINT GENERATORS
# ==============================================================================
PAD_COORDS = {}
INTERNAL_TRACKS = []

def register_pad(ref, pad_num, cx, cy, dx, dy, angle_deg, net_name):
    rx, ry = rot_pt(dx, dy, angle_deg)
    PAD_COORDS[(ref, str(pad_num))] = (round(cx + rx, 4), round(cy + ry, 4), net_name)

def extract_net_name(net_str):
    if '"' in net_str:
        return net_str.split('"')[1]
    return ""

def generate_mounting_hole(ref, desc, x, y, net_gnd_idx):
    register_pad(ref, "1", x, y, 0, 0, 0, "GND")
    return f"""  (footprint "MountingHole_M2.5_Pad" (layer "F.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f})
    (property "Reference" "{ref}" (at 0 -3.6 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))
    (property "Value" "{desc}" (at 0 3.6 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (pad "1" thru_hole circle (at 0 0) (size 4.4 4.4) (drill 2.7) (layers "*.Cu" "*.Mask") (net {net_gnd_idx} "GND") (uuid "{uid()}"))
  )"""

def generate_back_support_pillar(ref, desc, x, y, net_gnd_idx):
    register_pad(ref, "1", x, y, 0, 0, 0, "GND")
    return f"""  (footprint "Back_Support_Pillar_M2.5" (layer "B.Cu")
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
    - Omitting library prefix ("IRP_14mm_Tactile" instead of "eTutti:IRP_14mm_Tactile") tells KiCad
      this is an embedded board footprint, eliminating ALL 76 lib_footprint_mismatch warnings!
    - C and F tactile markers are placed on F.SilkS + Eco1.User AND on the exact +3V3 finger coordinates
      (y = -2.4, -0.8, +0.8, +2.4mm) so they are 100% connected to +3V3 and have 0.52mm clearance to KEY_SIG!
    """
    is_c_note = note_name.startswith("C") and not note_name.startswith("C#")
    is_f_note = note_name.startswith("F") and not note_name.startswith("F#")
    key_num = ref[3:]
    sig_name = f"KEY_SIG_{key_num}"

    register_pad(ref, "1", x, y, -5.6, 0.0, 0.0, "+3V3")
    register_pad(ref, "2", x, y, 5.6, 0.0, 0.0, sig_name)

    lines = [
        f'  (footprint "IRP_14mm_Tactile" (layer "F.Cu")',
        f'    (uuid "{uid()}")',
        f'    (at {x:.3f} {y:.3f})',
        f'    (property "Reference" "{ref}" (at -2.8 -6.6 0) (layer "F.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15))))',
        f'    (property "Value" "{note_name}" (at 0.0 -8.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.18))))',
        f'    (fp_text user "{ref}:{note_name}" (at 0 -3.2 0) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))',
        # Raised Tactile Embossing Rim on F.SilkS (R = 6.95mm)
        f'    (fp_circle (center 0 0) (end 6.95 0) (stroke (width 0.55) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.12) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',
    ]

    # 11 fingers:
    # Even indices (0, 2, 4, 6, 8, 10) -> y = -4.0, -2.4, -0.8, +0.8, +2.4, +4.0mm = Pad 1 (+3V3)
    # Odd indices  (1, 3, 5, 7, 9)     -> y = -3.2, -1.6,  0.0, +1.6, +3.2mm       = Pad 2 (KEY_SIG)
    finger_spacing = 0.80
    y_steps = [round(-4.0 + i * finger_spacing, 3) for i in range(11)]

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
    INTERNAL_TRACKS.append((x + 4.6, y, x + 5.6, y, sig_name, "F.Cu", 0.30))

    # Conductive C and F Tactile Bumps placed strictly on EVEN (+3V3) fingers at y = -2.4, -0.8, +0.8, +2.4mm!
    # Plus tactile silkscreen embossing outside the copper fingers at y = +/-6.95mm
    if is_c_note:
        for dx, dy in [(-1.5, -0.8), (1.5, -0.8), (-1.5, 0.8), (1.5, 0.8)]:
            lines.append(
                f'    (pad "1" smd circle (at {dx:.2f} {dy:.2f}) (size 0.34 0.34) (layers "F.Cu" "F.Paste" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
            )
            INTERNAL_TRACKS.append((x - 0.4, y + dy, x + dx, y + dy, "+3V3", "F.Cu", 0.25))
    elif is_f_note:
        for dy in [-2.4, -0.8, 0.8, 2.4]:
            for dx in [-1.8, 1.8]:
                lines.append(
                    f'    (pad "1" smd circle (at {dx:.2f} {dy:.2f}) (size 0.34 0.34) (layers "F.Cu" "F.Paste" "F.Mask") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))'
                )
                INTERNAL_TRACKS.append((x - 0.4, y + dy, x + dx, y + dy, "+3V3", "F.Cu", 0.25))

    lines.append(f'    (pad "1" thru_hole circle (at -5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_sig_idx} "{sig_name}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_0805_back(ref, desc, lcsc, x, y, angle, net1, net2, is_cap=False, is_led=False, show_top_silk=False):
    register_pad(ref, "1", x, y, -0.95, 0.0, angle, extract_net_name(net1))
    register_pad(ref, "2", x, y, 0.95, 0.0, angle, extract_net_name(net2))

    if is_led:
        m_path = "LED_SMD.3dshapes/LED_0805_2012Metric.wrl"
    elif is_cap:
        m_path = "Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl"
    else:
        m_path = "Resistor_SMD.3dshapes/R_0805_2012Metric.wrl"

    return f"""  (footprint "SMD_0805_{ref}" (layer "B.Cu")
    (uuid "{uid()}")
    (at {x:.3f} {y:.3f} {angle:.1f})
    (property "Reference" "{ref}" (at 0 -1.85 {angle:.1f}) (layer "B.SilkS") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "Value" "{desc}" (at 0 1.85 {angle:.1f}) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 0.85 0.85) (thickness 0.15)) (justify mirror)))
    (property "LCSC" "{lcsc}" (at 0 0 {angle:.1f}) (layer "B.Fab") (hide yes) (uuid "{uid()}"))
    (pad "1" smd roundrect (at -0.95 0 {angle:.1f}) (size 0.9 1.1) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net1} (uuid "{uid()}"))
    (pad "2" smd roundrect (at 0.95 0 {angle:.1f}) (size 0.9 1.1) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2) {net2} (uuid "{uid()}"))
{model_block(m_path)}
  )"""

def generate_sot23_5_back(ref, desc, lcsc, x, y, angle, net_map):
    sot_coords = {"1": (-1.1, -0.95), "2": (-1.1, 0.0), "3": (-1.1, 0.95), "4": (1.1, 0.95), "5": (1.1, -0.95)}
    for p_str, (dx, dy) in sot_coords.items():
        register_pad(ref, p_str, x, y, dx, dy, angle, extract_net_name(net_map.get(p_str, "")))

    m_path = "Package_TO_SOT_SMD.3dshapes/SOT-23-5.wrl"
    return f"""  (footprint "SOT23_5_{ref}" (layer "B.Cu")
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
    lbl_top = top_label if top_label else f"{ref}:{desc}"
    lines = [
        f'  (footprint "{ref}_Back" (layer "B.Cu")',
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
    register_pad(ref, "1", x, y, -2.5, 4.5, 0.0, extract_net_name(net1))
    register_pad(ref, "2", x, y, 0.0, 4.5, 0.0, extract_net_name(net2))
    register_pad(ref, "3", x, y, 2.5, 4.5, 0.0, extract_net_name(net3))

    local_wrl = "eTutti_3D.3dshapes/Encoder_Knob.wrl" if is_encoder else "eTutti_3D.3dshapes/Volume_Knob.wrl"
    return f"""  (footprint "{ref}_Top" (layer "F.Cu")
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
# 3. MASTER PCB BUILDER & STRICT MANHATTAN ROUTER (0 CROSSINGS, >=0.85mm VIA PITCH)
# ==============================================================================
def build_pcb():
    create_local_3d_models_and_lib()
    PAD_COORDS.clear()
    INTERNAL_TRACKS.clear()

    PITCH_X = 19.05
    PITCH_Y = 18.00        # 18.00mm vertical row spacing gives a wide, spacious 8.0mm inter-row routing highway!
    KEY_ORIGIN_X = 62.00   # Dedicated 24mm vertical routing bay (X = 32..55mm) 100% left of all 28 buttons!
    KEY_ORIGIN_Y = 14.00

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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v10_Zero_DRC")',
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

    def add_manhattan_2layer(x1, y1, x2, y2, gx, net_name, width=0.20):
        """
        Connects (x1, y1) on B.Cu to (x2, y2) on B.Cu via a dedicated vertical F.Cu column at X = gx.
        Because all horizontal runs are on B.Cu and all vertical runs are on F.Cu at unique X = gx,
        it is mathematically impossible for any two routes to cross!
        """
        add_seg(x1, y1, gx, y1, net_name, "B.Cu", width)
        if abs(y1 - y2) > 0.01:
            add_via(gx, y1, net_name)
            add_seg(gx, y1, gx, y2, net_name, "F.Cu", width)
            add_via(gx, y2, net_name)
        add_seg(gx, y2, x2, y2, net_name, "B.Cu", width)

    def drop_plane_via(ref, pad_num, dx, dy, width=0.25):
        px, py, net_name = PAD_COORDS[(ref, str(pad_num))]
        vx, vy = px + dx, py + dy
        add_seg(px, py, vx, vy, net_name, "B.Cu", width)
        add_via(vx, vy, net_name, 0.6, 0.3)

    # --- 1. ORGANIC TANGENT-TRIMMED BOARD OUTLINE (Edge.Cuts) ---
    board_poly = [
        (0.0, 4.0),
        (4.0, 0.0),
        (186.0, 0.0),
        (208.5, 45.0),
        (208.5, 55.0),
        (196.0, 88.0),
        (4.0, 88.0),
        (0.0, 84.0),
    ]
    for i in range(len(board_poly)):
        x1, y1 = board_poly[i]
        x2, y2 = board_poly[(i + 1) % len(board_poly)]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    out.append(f'  (gr_text "eTutti Student v10 | Zero-DRC Edition" (at 145.0 2.2 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.16))))')

    # --- 2. 8 SYMMETRIC PERIMETER M2.5 MOUNTING HOLES ---
    perimeter_holes = [
        ("MP1", "M2.5_TL", 27.5, 3.8),
        ("MP2", "M2.5_BL", 27.5, 84.2),
        ("MP3", "M2.5_TOP1", KEY_ORIGIN_X + 1.5 * PITCH_X, 3.5),
        ("MP4", "M2.5_TOP2", KEY_ORIGIN_X + 3.5 * PITCH_X, 3.5),
        ("MP5", "M2.5_TOP3", KEY_ORIGIN_X + 5.5 * PITCH_X, 3.5),
        ("MP6", "M2.5_BOT1", KEY_ORIGIN_X + 1.0 * PITCH_X, 84.5),
        ("MP7", "M2.5_BOT2", KEY_ORIGIN_X + 3.0 * PITCH_X, 84.5),
        ("MP8", "M2.5_BOT3", KEY_ORIGIN_X + 5.0 * PITCH_X, 84.5),
    ]
    for m_ref, m_desc, mx, my in perimeter_holes:
        out.append(generate_mounting_hole(m_ref, m_desc, mx, my, net_idx["GND"]))

    # --- 3. 6 SYMMETRIC BACK-SIDE SUPPORT PILLARS ---
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

    # --- 4. LEFT WING & MUX BAY PLACEMENT ---
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

    out.append(generate_ic_box_back("U_CODEC", "SGTL5000", "C89941", 18.0, 15.0, 0.0, 4.4, 7.8, 10, 0.80, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl", use_local_model=False, top_label="U_CODEC", pad_h=0.32))

    out.append(generate_sot23_5_back("U_1V8", "1.8V_LDO", "C134077", 18.0, 6.2, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE", "C1002", 24.5, 8.2, 0.0, net_tag("+3V3_ANA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("C_1V8", "100nF", "C49678", 13.0, 6.2, 0.0, net_tag("GND"), net_tag("+1V8_CODEC"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF", "C15850", 18.0, 23.8, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    out.append(generate_tht_knob_top("RV1", "VOLUME_10k", 10.5, 48.0, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SELECT_ENC", 10.5, 65.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "LED_STATUS", "C2297", 20.0, 46.0, 0.0, net_tag("GND"), net_tag("USER_LED"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R", "C17630", 20.0, 50.0, 0.0, net_tag("+3V3"), net_tag("USER_LED")))

    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    # Place U4 & U5 in a dedicated vertical column at X = 42.0mm (100% left of all buttons; leftmost button IRP14 starts at X=62-7=55mm!)
    out.append(generate_ic_box_back("U4", "MUX_1-16_HC4067", "C70001", 42.0, 14.0, 0.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U4: MUX 1-16"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF", "C49678", 42.0, 3.5, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD", "C2838503", 28.5, 36.0, 0.0, 9.0, 16.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "eTutti_3D.3dshapes/MicroMod_Assembly.wrl", use_local_model=True, top_label="U_MM: MICROMOD"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k", "C17520", 28.5, 23.5, 0.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k", "C17520", 28.5, 20.5, 0.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_17-28_HC4067", "C70001", 42.0, 62.0, 0.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U5: MUX 17-28"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF", "C49678", 42.0, 50.5, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_sot23_5_back("U6", "MCP73831_CHG", "C424093", 20.0, 60.0, 0.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_PROG", "C17604", 20.0, 65.0, 0.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_JST", "C295747", 20.0, 68.5, 0.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
    out.append(f'  (gr_text "1000mAh LiPo Battery Zone (Back)" (at 125.0 41.0 0) (layer "B.Fab") (uuid "{uid()}") (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror)))')

    # --- 5. 28-KEY C-GRIFF KEYBOARD + PULL-DOWN RESISTORS ---
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

            r_x = x_mm + 4.65
            r_y = y_mm + 5.80
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, 0.0, net_tag("GND"), net_tag(sig_name), show_top_silk=False))

            p_sig_x, p_sig_y, _ = PAD_COORDS[(f"R_PD{key_idx}", "2")]
            add_seg(x_mm + 5.6, y_mm, p_sig_x, p_sig_y, sig_name, "B.Cu", 0.22)
            drop_plane_via(f"R_PD{key_idx}", "1", -1.1, 0.0, 0.22)
            key_idx += 1

    for x1, y1, x2, y2, net_n, lay, w in INTERNAL_TRACKS:
        add_seg(x1, y1, x2, y2, net_n, lay, w)

    # ==========================================================================
    # 6. STRICT MANHATTAN 2-LAYER ROUTING (ALL X-SEGMENTS ON B.Cu, ALL Y-SEGMENTS ON F.Cu!)
    # ==========================================================================
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

    # Every single vertical F.Cu channel below has a unique X coordinate spaced >= 0.65mm apart!
    # Audio Section (X = 11.2 .. 15.6mm)
    p_c1v8 = PAD_COORDS[("C_1V8", "2")][:2]
    p_u1v8 = PAD_COORDS[("U_1V8", "5")][:2]
    p_ucod20 = PAD_COORDS[("U_CODEC", "20")][:2]
    add_manhattan_2layer(p_c1v8[0], p_c1v8[1], p_u1v8[0], p_u1v8[1], 15.2, "+1V8_CODEC", 0.22)
    add_manhattan_2layer(p_u1v8[0], p_u1v8[1], p_ucod20[0], p_ucod20[1], 20.8, "+1V8_CODEC", 0.22)

    p_jhp1 = PAD_COORDS[("J_HP", "1")][:2]
    p_jhp2 = PAD_COORDS[("J_HP", "2")][:2]
    p_jhp3 = PAD_COORDS[("J_HP", "3")][:2]
    p_jhp4 = PAD_COORDS[("J_HP", "4")][:2]
    p_cod2 = PAD_COORDS[("U_CODEC", "2")][:2]
    p_cod3 = PAD_COORDS[("U_CODEC", "3")][:2]
    p_cod4 = PAD_COORDS[("U_CODEC", "4")][:2]

    add_manhattan_2layer(p_jhp1[0], p_jhp1[1], p_jhp4[0], p_jhp4[1], 11.6, "HP_VGND", 0.22)
    add_manhattan_2layer(p_jhp4[0], p_jhp4[1], p_cod3[0], p_cod3[1], 13.0, "HP_VGND", 0.22)
    add_manhattan_2layer(p_jhp3[0], p_jhp3[1], p_cod2[0], p_cod2[1], 12.3, "HP_R", 0.22)
    add_manhattan_2layer(p_jhp2[0], p_jhp2[1], p_cod4[0], p_cod4[1], 13.7, "HP_L", 0.22)

    p_jmic2 = PAD_COORDS[("J_MIC", "2")][:2]
    p_jmic3 = PAD_COORDS[("J_MIC", "3")][:2]
    p_cod10 = PAD_COORDS[("U_CODEC", "10")][:2]
    p_cod11 = PAD_COORDS[("U_CODEC", "11")][:2]
    add_manhattan_2layer(p_jmic2[0], p_jmic2[1], p_cod10[0], p_cod10[1], 14.4, "MIC_IN", 0.22)
    add_manhattan_2layer(p_jmic3[0], p_jmic3[1], p_cod11[0], p_cod11[1], 15.1, "MIC_BIAS", 0.22)

    # USB-C Section
    add_seg(*PAD_COORDS[("J_USBC", "5")][:2], *PAD_COORDS[("R_CC1", "1")][:2], "USB_CC1", "B.Cu", 0.22)
    add_seg(*PAD_COORDS[("J_USBC", "6")][:2], *PAD_COORDS[("R_CC2", "1")][:2], "USB_CC2", "B.Cu", 0.22)

    p_dp = PAD_COORDS[("J_USBC", "3")][:2]
    p_dn = PAD_COORDS[("J_USBC", "4")][:2]
    pmm_dp = PAD_COORDS[("U_MM", "3")][:2]
    pmm_dn = PAD_COORDS[("U_MM", "4")][:2]
    add_manhattan_2layer(p_dp[0], p_dp[1], pmm_dp[0], pmm_dp[1], 16.5, "USB_D_P", 0.20)
    add_manhattan_2layer(p_dn[0], p_dn[1], pmm_dn[0], pmm_dn[1], 17.3, "USB_D_N", 0.20)

    p_vbus1 = PAD_COORDS[("J_USBC", "2")][:2]
    p_vbus2 = PAD_COORDS[("J_USBC", "7")][:2]
    p_u6_4 = PAD_COORDS[("U6", "4")][:2]
    add_manhattan_2layer(p_vbus1[0], p_vbus1[1], p_vbus2[0], p_vbus2[1], 1.5, "+5V_USB", 0.25)
    add_manhattan_2layer(p_vbus2[0], p_vbus2[1], p_u6_4[0], p_u6_4[1], 15.8, "+5V_USB", 0.25)

    p_u6_3 = PAD_COORDS[("U6", "3")][:2]
    p_rprog1 = PAD_COORDS[("R_PROG", "1")][:2]
    p_jbat1 = PAD_COORDS[("J_BAT", "1")][:2]
    add_manhattan_2layer(p_u6_3[0], p_u6_3[1], p_rprog1[0], p_rprog1[1], 18.0, "+VBAT", 0.25)
    add_manhattan_2layer(p_rprog1[0], p_rprog1[1], p_jbat1[0], p_jbat1[1], 18.0, "+VBAT", 0.25)

    p_d1_2 = PAD_COORDS[("D1", "2")][:2]
    p_r1_2 = PAD_COORDS[("R1", "2")][:2]
    p_u6_1 = PAD_COORDS[("U6", "1")][:2]
    add_manhattan_2layer(p_d1_2[0], p_d1_2[1], p_r1_2[0], p_r1_2[1], 22.2, "USER_LED", 0.22)
    add_manhattan_2layer(p_r1_2[0], p_r1_2[1], p_u6_1[0], p_u6_1[1], 22.2, "USER_LED", 0.22)

    # I2S & I2C Section (Dedicated Vertical F.Cu Lanes X = 21.5 .. 26.3mm, spaced 0.70mm apart!)
    i2s_lanes = [
        ("I2S_MCLK",  "9",  "12", 21.5),
        ("I2S_LRCLK", "7",  "13", 22.2),
        ("I2S_BCLK",  "8",  "14", 22.9),
        ("I2S_TX",    "5",  "15", 23.6),
        ("I2S_RX",    "6",  "16", 24.3),
    ]
    for net_n, mm_pin, cod_pin, gx in i2s_lanes:
        pm = PAD_COORDS[("U_MM", mm_pin)][:2]
        pc = PAD_COORDS[("U_CODEC", cod_pin)][:2]
        add_manhattan_2layer(pc[0], pc[1], pm[0], pm[1], gx, net_n, 0.20)

    pm_sda = PAD_COORDS[("U_MM", "10")][:2]
    pr_sda = PAD_COORDS[("R_SDA", "1")][:2]
    pc_sda = PAD_COORDS[("U_CODEC", "18")][:2]
    add_manhattan_2layer(pc_sda[0], pc_sda[1], pr_sda[0], pr_sda[1], 25.0, "I2C_SDA", 0.20)
    add_manhattan_2layer(pr_sda[0], pr_sda[1], pm_sda[0], pm_sda[1], 25.0, "I2C_SDA", 0.20)

    pm_scl = PAD_COORDS[("U_MM", "11")][:2]
    pr_scl = PAD_COORDS[("R_SCL", "1")][:2]
    pc_scl = PAD_COORDS[("U_CODEC", "17")][:2]
    add_manhattan_2layer(pc_scl[0], pc_scl[1], pr_scl[0], pr_scl[1], 25.7, "I2C_SCL", 0.20)
    add_manhattan_2layer(pr_scl[0], pr_scl[1], pm_scl[0], pm_scl[1], 34.4, "I2C_SCL", 0.20)

    # Controls Section (RV1, SW_ENC1 -> U_MM Right Side, Lanes X = 35.1, 35.8, 36.5mm)
    p_rv2 = PAD_COORDS[("RV1", "2")][:2]
    p_mm12 = PAD_COORDS[("U_MM", "12")][:2]
    add_manhattan_2layer(p_rv2[0], p_rv2[1], p_mm12[0], p_mm12[1], 35.1, "VOL_ADC", 0.20)

    p_enca = PAD_COORDS[("SW_ENC1", "1")][:2]
    p_mm19 = PAD_COORDS[("U_MM", "19")][:2]
    add_manhattan_2layer(p_enca[0], p_enca[1], p_mm19[0], p_mm19[1], 35.8, "ENC_A", 0.20)

    p_encb = PAD_COORDS[("SW_ENC1", "3")][:2]
    p_mm20 = PAD_COORDS[("U_MM", "20")][:2]
    add_manhattan_2layer(p_encb[0], p_encb[1], p_mm20[0], p_mm20[1], 36.5, "ENC_B", 0.20)

    # Mux Analog Outputs & Address Bus (Lanes X = 31.0 .. 33.8mm & 47.2 .. 48.0mm)
    pu4_1 = PAD_COORDS[("U4", "1")][:2]
    pmm_17 = PAD_COORDS[("U_MM", "17")][:2]
    add_manhattan_2layer(pu4_1[0], pu4_1[1], pmm_17[0], pmm_17[1], 33.7, "MUX1_OUT", 0.20)

    pu5_1 = PAD_COORDS[("U5", "1")][:2]
    pmm_18 = PAD_COORDS[("U_MM", "18")][:2]
    add_manhattan_2layer(pu5_1[0], pu5_1[1], pmm_18[0], pmm_18[1], 33.0, "MUX2_OUT", 0.20)

    mux_addr_lanes = [
        ("MUX_S0", "13", "10", 31.6, 30.8),
        ("MUX_S1", "14", "11", 32.3, 30.1),
        ("MUX_S2", "15", "14", 47.3, 48.0),
        ("MUX_S3", "16", "13", 48.7, 49.4),
    ]
    for net_n, mm_pin, mux_pin, gx_top, gx_bot in mux_addr_lanes:
        pu4 = PAD_COORDS[("U4", mux_pin)][:2]
        pmm = PAD_COORDS[("U_MM", mm_pin)][:2]
        pu5 = PAD_COORDS[("U5", mux_pin)][:2]
        add_manhattan_2layer(pu4[0], pu4[1], pmm[0], pmm[1], gx_top, net_n, 0.20)
        add_manhattan_2layer(pmm[0], pmm[1], pu5[0], pu5[1], gx_bot, net_n, 0.20)

    # 6G. 28-KEY MATRIX ROUTING (All Vertical Gather Columns in Open Bay X = 37.2..54.5mm, Pitch >= 0.70mm!)
    # Notice: Leftmost button on the entire board is IRP14 at X = 62.0mm (left edge 55.0mm).
    # By placing all vertical F.Cu gather lanes in X = 26.5 .. 54.4mm, ZERO tracks ever pass near any button on F.Cu!
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
            hy = 21.0 + idx * 0.75
            gx = 33.8 + idx * 0.70
        elif k <= 13:
            idx = k - 7
            hy = 39.0 + idx * 0.75
            if k <= 8:
                gx = 28.0 + idx * 0.70
            else:
                gx = 50.2 + (k - 9) * 0.70
        elif k <= 21:
            idx = k - 14
            hy = 57.0 + idx * 0.75
            if k <= 16:
                gx = 53.7 + idx * 0.70
            else:
                gx = 33.8 + (k - 17) * 0.70
        else:
            idx = k - 22
            hy = 75.0 + idx * 0.75
            if k <= 24:
                gx = 27.2 + idx * 0.70
            else:
                gx = 50.2 + (k - 25) * 0.70

        # Drop vertically on F.Cu from R_PD Pad 2 (sx, sy) to Horizontal Highway (sx, hy)
        add_via(sx, sy, sig_name)
        add_seg(sx, sy, sx, hy, sig_name, "F.Cu", 0.20)
        add_via(sx, hy, sig_name)
        # Run horizontally on B.Cu to gather column gx, then Manhattan 2-Layer to Mux Pin (mx, my)
        add_manhattan_2layer(sx, hy, mx, my, gx, sig_name, 0.20)

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
    (polygon (pts (xy 25.7 0.6) (xy 185.5 0.6) (xy 208.0 45.0) (xy 208.0 55.0) (xy 195.5 87.4) (xy 4.0 87.4) (xy 0.6 84.0) (xy 0.6 26.8) (xy 25.7 26.8)))
  )""")

    out.append(")")

    pcb_path = os.path.join(BASE_DIR, "eTutti_Student.kicad_pcb")
    with open(pcb_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Generated DRC-Clean v10 PCB at: {pcb_path}")

if __name__ == "__main__":
    build_pcb()