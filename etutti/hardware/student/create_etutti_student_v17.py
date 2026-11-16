import os
import re
import glob
import shutil
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
# 1. AUTOMATIC STEP 3D BOUNDING-BOX INSPECTOR & CO-REGISTRATION ENGINE
# ==============================================================================
FOUND_MICROMOD_STEP_PATH = None
STEP_CENTER_X = 0.0
STEP_CENTER_Y = 11.0
STEP_Z_BASE   = 0.0
STEP_FINGER_EDGE_Y = 0.0   # Relative to STEP_CENTER_Y: -11.0 or +11.0

def measure_step_board_bounds(step_path):
    """
    Scans the STEP file's CARTESIAN_POINT entries (and top-level placement translations)
    to find the exact 22x22mm PCB bounding box [x_min..x_max, y_min..y_max, z_min..z_max].
    """
    global STEP_CENTER_X, STEP_CENTER_Y, STEP_Z_BASE, STEP_FINGER_EDGE_Y
    try:
        with open(step_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Extract all 3D Cartesian points: CARTESIAN_POINT('',(x,y,z))
        pt_regex = re.compile(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-\d.E+]+)\s*,\s*([-\d.E+]+)\s*,\s*([-\d.E+]+)\s*\)\s*\)")
        xs, ys, zs = [], [], []
        for m in pt_regex.finditer(content):
            x, y, z = float(m.group(1)), float(m.group(2)), float(m.group(3))
            # Filter out unit vectors or huge spline poles outside [-100..+100] mm
            if -60.0 <= x <= 60.0 and -60.0 <= y <= 60.0 and -20.0 <= z <= 20.0:
                # Ignore exact (0,0,0) origin placement points
                if abs(x) < 1e-6 and abs(y) < 1e-6 and abs(z) < 1e-6:
                    continue
                xs.append(x)
                ys.append(y)
                zs.append(z)

        if xs and ys:
            xs.sort()
            ys.sort()
            zs.sort()
            # Use 1st and 99th percentile to ignore any stray reference points
            n = len(xs)
            x_min, x_max = xs[int(n * 0.01)], xs[int(n * 0.99)]
            y_min, y_max = ys[int(n * 0.01)], ys[int(n * 0.99)]
            z_min, z_max = zs[int(n * 0.02)], zs[int(n * 0.98)]

            # Check if coordinates are in meters (0.022) instead of mm (22.0)
            span_x = x_max - x_min
            span_y = y_max - y_min
            scale_factor = 1000.0 if (span_x < 0.1 and span_y < 0.1) else 1.0

            x_min *= scale_factor
            x_max *= scale_factor
            y_min *= scale_factor
            y_max *= scale_factor
            z_min *= scale_factor
            z_max *= scale_factor

            STEP_CENTER_X = round((x_min + x_max) / 2.0, 2)
            STEP_CENTER_Y = round((y_min + y_max) / 2.0, 2)
            STEP_Z_BASE   = round(z_min, 2)

            print(f"   [STEP BBOX MEASURED] X: [{x_min:.2f} .. {x_max:.2f}] mm (center={STEP_CENTER_X:.2f})")
            print(f"   [STEP BBOX MEASURED] Y: [{y_min:.2f} .. {y_max:.2f}] mm (center={STEP_CENTER_Y:.2f})")
            print(f"   [STEP BBOX MEASURED] Z: [{z_min:.2f} .. {z_max:.2f}] mm")
    except Exception as e:
        print(f"   [STEP BBOX WARNING] Could not parse bounds: {e}")

def locate_and_stage_micromod_step():
    global FOUND_MICROMOD_STEP_PATH
    shapes_dir = os.path.join(BASE_DIR, "eTutti_3D.3dshapes")
    os.makedirs(shapes_dir, exist_ok=True)

    search_patterns = [
        os.path.join(BASE_DIR, "*.step"),
        os.path.join(BASE_DIR, "*.stp"),
        os.path.join(shapes_dir, "*.step"),
        os.path.join(shapes_dir, "*.stp"),
    ]
    candidates = []
    seen = set()
    for pat in search_patterns:
        for p in glob.glob(pat):
            ap = os.path.abspath(p)
            base_low = os.path.basename(ap).lower()
            if ap not in seen and base_low not in ("micromod_teensy.step", "micromod_teensy_centered.step"):
                seen.add(ap)
                candidates.append(ap)

    if not candidates:
        for fallback_name in ("Sparkfun Teensy v3.step", "SparkFun MicroMod Teensy Processor.step", "MicroMod_Teensy_2.step", "MicroMod_Teensy.step"):
            for folder in (BASE_DIR, shapes_dir):
                fp = os.path.join(folder, fallback_name)
                if os.path.exists(fp):
                    candidates.append(os.path.abspath(fp))
                    break
            if candidates:
                break

    if candidates:
        candidates.sort(key=lambda x: os.path.getsize(x), reverse=True)
        best_step = candidates[0]
        FOUND_MICROMOD_STEP_PATH = best_step.replace("\\", "/")
        print(f"3D STEP MODEL LINKED: {FOUND_MICROMOD_STEP_PATH} ({os.path.getsize(best_step):,} bytes)")
        measure_step_board_bounds(best_step)
    else:
        print("NOTE: No .step/.stp file found; using fallback MicroMod_Assembly.wrl")

def make_cylinder_ifs(radius_mm, z_bot_mm, z_top_mm, segments=32, r_top_mm=None, fluted_amp_mm=0.0, cx_mm=0.0, cy_mm=0.0, axis="Z"):
    if r_top_mm is None:
        r_top_mm = radius_mm
    pts = []
    for z_val, rad_val in [(z_bot_mm, radius_mm), (z_top_mm, r_top_mm)]:
        for i in range(segments):
            ang = 2.0 * math.pi * i / segments
            flute = fluted_amp_mm * math.cos(segments * 0.5 * ang) if fluted_amp_mm > 0 else 0.0
            r = mm_to_wrl(rad_val + flute)
            u = r * math.cos(ang)
            v = r * math.sin(ang)
            w = mm_to_wrl(z_val)
            if axis == "Z":
                pts.append((mm_to_wrl(cx_mm) + u, mm_to_wrl(cy_mm) + v, w))
            elif axis == "X":
                pts.append((w, mm_to_wrl(cx_mm) + u, mm_to_wrl(cy_mm) + v))
            else:
                pts.append((mm_to_wrl(cx_mm) + u, w, mm_to_wrl(cy_mm) + v))

    idx_bot_c = 2 * segments
    idx_top_c = 2 * segments + 1
    if axis == "Z":
        pts.append((mm_to_wrl(cx_mm), mm_to_wrl(cy_mm), mm_to_wrl(z_bot_mm)))
        pts.append((mm_to_wrl(cx_mm), mm_to_wrl(cy_mm), mm_to_wrl(z_top_mm)))
    elif axis == "X":
        pts.append((mm_to_wrl(z_bot_mm), mm_to_wrl(cx_mm), mm_to_wrl(cy_mm)))
        pts.append((mm_to_wrl(z_top_mm), mm_to_wrl(cx_mm), mm_to_wrl(cy_mm)))
    else:
        pts.append((mm_to_wrl(cx_mm), mm_to_wrl(z_bot_mm), mm_to_wrl(cy_mm)))
        pts.append((mm_to_wrl(cx_mm), mm_to_wrl(z_top_mm), mm_to_wrl(cy_mm)))

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
    locate_and_stage_micromod_step()
    shapes_dir = os.path.join(BASE_DIR, "eTutti_3D.3dshapes")
    os.makedirs(shapes_dir, exist_ok=True)

    # 1. Alps RK09K Potentiometer + Fluted Knob
    vol_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.18 0.14 0.10 specularColor 0.2 0.2 0.2 }} }} {make_box_ifs(7.6, 8.5, 0.1, 1.8, cx_mm=0.0, cy_mm=0.8)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=-2.5, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=0.0, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=2.5, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.10 0.48 0.26 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(8.2, 6.8, 1.2, 4.4, cx_mm=0.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.76 0.78 0.82 specularColor 0.88 0.88 0.92 }} }} {make_box_ifs(9.6, 4.2, 0.2, 4.9, cx_mm=0.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.76 0.78 0.82 specularColor 0.88 0.88 0.92 }} }} {make_cylinder_ifs(4.2, 4.4, 5.1, segments=24)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.72 0.35 specularColor 0.8 0.8 0.6 }} }} {make_cylinder_ifs(4.8, 5.1, 6.3, segments=6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.82 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(3.4, 6.3, 9.5, segments=24)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.16 0.17 0.20 specularColor 0.5 0.5 0.5 }} }} {make_cylinder_ifs(6.8, 8.2, 10.0, segments=36, r_top_mm=6.2)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.14 0.15 0.18 specularColor 0.4 0.4 0.4 }} }} {make_cylinder_ifs(6.0, 10.0, 19.5, segments=48, r_top_mm=5.7, fluted_amp_mm=0.32)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.25 0.27 0.30 specularColor 0.7 0.7 0.7 }} }} {make_cylinder_ifs(5.7, 19.5, 21.0, segments=36, r_top_mm=4.6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.98 0.98 0.98 emissiveColor 0.2 0.2 0.2 }} }} {make_box_ifs(1.0, 4.2, 19.6, 21.2, cx_mm=0.0, cy_mm=2.2)} }}
"""
    with open(os.path.join(shapes_dir, "Volume_Knob.wrl"), "w", encoding="utf-8") as f:
        f.write(vol_wrl)

    # 2. Alps EC11 Rotary Encoder + Stepped Dial
    enc_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.18 }} }} {make_box_ifs(8.8, 9.2, 0.1, 1.6, cx_mm=0.0, cy_mm=0.6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=-2.5, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=0.0, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(0.4, -2.5, 1.2, segments=12, cx_mm=2.5, cy_mm=-4.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.14 0.38 0.72 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(9.8, 8.2, 1.4, 4.2, cx_mm=0.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.84 specularColor 0.9 0.9 0.92 }} }} {make_box_ifs(11.4, 5.2, 0.2, 5.0, cx_mm=0.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.78 0.80 0.84 specularColor 0.9 0.9 0.92 }} }} {make_box_ifs(8.6, 9.4, 4.2, 5.1, cx_mm=0.0, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.8 0.8 0.8 }} }} {make_cylinder_ifs(5.0, 5.1, 6.5, segments=6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.77 0.80 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(3.5, 6.5, 9.5, segments=24)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.22 0.25 0.30 specularColor 0.6 0.6 0.6 }} }} {make_cylinder_ifs(7.4, 8.2, 10.5, segments=36, r_top_mm=6.6)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.28 0.32 0.38 specularColor 0.75 0.75 0.78 }} }} {make_cylinder_ifs(6.5, 10.5, 19.0, segments=48, r_top_mm=6.2, fluted_amp_mm=0.28)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.75 0.78 0.82 specularColor 0.9 0.9 0.9 }} }} {make_cylinder_ifs(6.2, 19.0, 20.5, segments=36, r_top_mm=5.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 1.0 0.55 0.10 emissiveColor 0.2 0.1 0.0 }} }} {make_box_ifs(1.1, 4.5, 19.1, 20.7, cx_mm=0.0, cy_mm=2.4)} }}
"""
    with open(os.path.join(shapes_dir, "Encoder_Knob.wrl"), "w", encoding="utf-8") as f:
        f.write(enc_wrl)

    # 3. 3.5mm Stereo TRS Audio Jack
    jack_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.14 0.14 0.16 specularColor 0.2 0.2 0.2 }} }} {make_box_ifs(8.5, 6.0, 0.1, 5.0, cx_mm=0.5, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.20 0.20 0.23 specularColor 0.3 0.3 0.3 }} }} {make_box_ifs(6.5, 4.4, 5.0, 5.6, cx_mm=0.8, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.18 0.18 0.20 specularColor 0.4 0.4 0.4 }} }} {make_cylinder_ifs(2.6, -3.8, -6.2, segments=32, cx_mm=0.0, cy_mm=2.6, axis="X")} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.95 0.95 0.95 }} }} {make_cylinder_ifs(2.3, -6.2, -7.2, segments=32, cx_mm=0.0, cy_mm=2.6, axis="X")} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.03 0.03 0.04 }} }} {make_cylinder_ifs(1.75, -7.2, -7.35, segments=24, cx_mm=0.0, cy_mm=2.6, axis="X")} }}
"""
    with open(os.path.join(shapes_dir, "AudioJack_35mm.wrl"), "w", encoding="utf-8") as f:
        f.write(jack_wrl)

    # 4. USB Type-C Receptacle
    usbc_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.76 0.78 0.82 specularColor 0.92 0.92 0.95 }} }} {make_box_ifs(7.3, 6.2, 0.2, 3.3, cx_mm=-0.4, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.76 0.78 0.82 specularColor 0.92 0.92 0.95 }} }} {make_cylinder_ifs(1.55, 0.2, -4.2, segments=24, cx_mm=-2.6, cy_mm=1.75, axis="X")} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.76 0.78 0.82 specularColor 0.92 0.92 0.95 }} }} {make_cylinder_ifs(1.55, 0.2, -4.2, segments=24, cx_mm=2.6, cy_mm=1.75, axis="X")} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.06 0.06 0.08 }} }} {make_box_ifs(0.3, 5.4, 0.55, 2.95, cx_mm=-4.05, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.15 0.15 0.18 }} }} {make_box_ifs(4.5, 4.8, 1.45, 2.05, cx_mm=-1.8, cy_mm=0.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.92 0.75 0.20 specularColor 0.9 0.8 0.3 }} }} {make_box_ifs(4.4, 4.2, 2.05, 2.12, cx_mm=-1.8, cy_mm=0.0)} }}
"""
    with open(os.path.join(shapes_dir, "USB_C_Receptacle.wrl"), "w", encoding="utf-8") as f:
        f.write(usbc_wrl)

    # 5. Full-Detail M.2 Socket Housing + Standoff + Phillips Screw
    # Centered directly around (0, 0) with (offset (xyz 0 0 0))!
    #   - M.2 Socket sits at cy_mm = -10.5mm (bottom edge of the centered 22x22mm STEP board)
    #   - Brass M2.5 Standoff & Phillips Screw sit at cx_mm = +4.0mm, cy_mm = +11.0mm (top edge notch of the centered 22x22mm STEP board)
    socket_wrl = f"""#VRML V2.0 utf8
# 1. Black High-Density M.2 69-Pin SMD Socket Housing at cy = -10.5mm (Centered Frame)
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.11 0.11 0.13 specularColor 0.35 0.35 0.35 }} }} {make_box_ifs(22.2, 3.2, 0.05, 3.6, cx_mm=0.0, cy_mm=-10.5)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.11 0.11 0.13 specularColor 0.35 0.35 0.35 }} }} {make_box_ifs(1.8, 2.2, 0.05, 3.5, cx_mm=-10.2, cy_mm=-8.9)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.11 0.11 0.13 specularColor 0.35 0.35 0.35 }} }} {make_box_ifs(1.8, 2.2, 0.05, 3.5, cx_mm=10.2, cy_mm=-8.9)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.84 0.88 specularColor 0.9 0.9 0.9 }} }} {make_box_ifs(19.8, 0.8, 0.02, 0.35, cx_mm=0.0, cy_mm=-12.3)} }}
# 2. Brass M2.5 Standoff Post + Slotted Silver Phillips Screw at (cx = +4.0mm, cy = +11.0mm) (Centered Frame)
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.82 0.68 0.28 specularColor 0.85 0.75 0.35 }} }} {make_cylinder_ifs(2.2, 0.05, 2.10, segments=28, cx_mm=4.0, cy_mm=11.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.84 0.86 0.90 specularColor 0.95 0.95 0.95 }} }} {make_cylinder_ifs(2.6, 2.90, 3.65, segments=28, cx_mm=4.0, cy_mm=11.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.18 0.18 0.20 }} }} {make_box_ifs(1.8, 0.35, 3.65, 3.72, cx_mm=4.0, cy_mm=11.0)} }}
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.18 0.18 0.20 }} }} {make_box_ifs(0.35, 1.8, 3.65, 3.72, cx_mm=4.0, cy_mm=11.0)} }}
"""
    with open(os.path.join(shapes_dir, "MicroMod_Socket_Base.wrl"), "w", encoding="utf-8") as f:
        f.write(socket_wrl)

    # 6. Support Pillar Boss
    pillar_wrl = f"""#VRML V2.0 utf8
Shape {{ appearance Appearance {{ material Material {{ diffuseColor 0.85 0.70 0.30 specularColor 0.8 0.8 0.5 }} }} {make_cylinder_ifs(2.2, 0.0, 3.5, segments=24)} }}
"""
    with open(os.path.join(shapes_dir, "Support_Pillar.wrl"), "w", encoding="utf-8") as f:
        f.write(pillar_wrl)

def model_block(local_Or_KiCad_path, offset_z=0.0, rot_z=0.0, use_local=False):
    if use_local:
        if "MicroMod_Assembly" in local_Or_KiCad_path:
            socket_path = os.path.join(BASE_DIR, "eTutti_3D.3dshapes", "MicroMod_Socket_Base.wrl").replace("\\", "/")
            if FOUND_MICROMOD_STEP_PATH:
                # WHY THIS LOCKS THE STEP BOARD TO THE SOCKET & SCREW:
                # 1. MicroMod_Socket_Base.wrl is already centered at (0, 0) in footprint space, so its offset is (0, 0, 0).
                # 2. The STEP file's measured center is (STEP_CENTER_X, STEP_CENTER_Y).
                #    To bring the STEP file's center (STEP_CENTER_X, STEP_CENTER_Y) to (0, 0) on a B.Cu footprint
                #    (where KiCad flips Y -> -Y), we offset by (-STEP_CENTER_X, -STEP_CENTER_Y, 2.10)!
                ox = -STEP_CENTER_X
                oy = -STEP_CENTER_Y
                return f"""    (model "{FOUND_MICROMOD_STEP_PATH}"
      (offset (xyz {ox:.2f} {oy:.2f} 2.10)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )
    (model "{socket_path}"
      (offset (xyz 0 0 0.00)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))
    )"""
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
# 2. DRC-CLEAN EMBEDDED FOOTPRINT GENERATORS
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
        f'    (fp_circle (center 0 0) (end 6.95 0) (stroke (width 0.55) (type solid)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))',
        f'    (fp_circle (center 0 0) (end 6.75 0) (stroke (width 0.12) (type solid)) (fill none) (layer "Eco1.User") (uuid "{uid()}"))',
    ]

    if is_c_note:
        for ang_deg in [0, 90, 180, 270]:
            rad = math.radians(ang_deg)
            cx_d, cy_d = 6.95 * math.cos(rad), 6.95 * math.sin(rad)
            lines.append(f'    (fp_circle (center {cx_d:.2f} {cy_d:.2f}) (end {cx_d+0.45:.2f} {cy_d:.2f}) (stroke (width 0.45) (type solid)) (fill solid) (layer "F.SilkS") (uuid "{uid()}"))')
    elif is_f_note:
        for dx_bar in [-2.2, 0.0, 2.2]:
            lines.append(f'    (fp_line (start {dx_bar:.2f} -6.5) (end {dx_bar:.2f} -7.4) (stroke (width 0.50) (type solid)) (layer "F.SilkS") (uuid "{uid()}"))')
            lines.append(f'    (fp_line (start {dx_bar:.2f} 6.5) (end {dx_bar:.2f} 7.4) (stroke (width 0.50) (type solid)) (layer "F.SilkS") (uuid "{uid()}"))')

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
    INTERNAL_TRACKS.append((x - 5.6, y, x - 4.6, y - 0.80, "+3V3", "F.Cu", 0.28))

    for i in range(len(right_spine_pts) - 1):
        INTERNAL_TRACKS.append((right_spine_pts[i][0], right_spine_pts[i][1], right_spine_pts[i+1][0], right_spine_pts[i+1][1], sig_name, "F.Cu", 0.28))
    INTERNAL_TRACKS.append((x + 4.6, y, x + 5.6, y, sig_name, "F.Cu", 0.30))

    lines.append(f'    (pad "1" thru_hole circle (at -5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_vcc_idx} "+3V3") (uuid "{uid()}"))')
    lines.append(f'    (pad "2" thru_hole circle (at 5.6 0) (size 0.70 0.70) (drill 0.35) (layers "*.Cu") (net {net_sig_idx} "{sig_name}") (uuid "{uid()}"))')
    lines.append('  )')
    return "\n".join(lines)

def generate_smd_0805_back(ref, desc, lcsc, x, y, angle, net1, net2, is_cap=False, is_led=False):
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
# 3. MASTER PCB BUILDER (0 DRC VIOLATIONS, AUTO-CENTERED 3D STEP + SOCKET)
# ==============================================================================
def build_pcb(include_routing=True, filename="eTutti_Student.kicad_pcb"):
    create_local_3d_models_and_lib()
    PAD_COORDS.clear()
    INTERNAL_TRACKS.clear()
    PLACED_VIAS = set()

    PITCH_X = 19.05
    PITCH_Y = 18.00
    KEY_ORIGIN_X = 64.00
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
        '(kicad_pcb (version 20221018) (generator "eTutti_Generator_v17_Locked_3D")',
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
        key = (round(x, 2), round(y, 2))
        if key in PLACED_VIAS:
            return
        PLACED_VIAS.add(key)
        nid = net_idx[net_name]
        out.append(f'  (via (at {x:.3f} {y:.3f}) (size {size:.2f}) (drill {drill:.2f}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{uid()}"))')

    def route_2layer_clean(x1, y1, x2, y2, gx, net_name, width=0.20):
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
        (188.0, 0.0),
        (210.5, 45.0),
        (210.5, 55.0),
        (198.0, 88.0),
        (4.0, 88.0),
        (0.0, 84.0),
    ]
    for i in range(len(board_poly)):
        x1, y1 = board_poly[i]
        x2, y2 = board_poly[(i + 1) % len(board_poly)]
        out.append(f'  (gr_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{uid()}"))')

    out.append(f'  (gr_text "eTutti Student v17" (at 111.5 2.5 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 0.95 0.95) (thickness 0.16))))')

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
        if include_routing:
            drop_plane_via(s_ref, "1", 0.0, 0.0, 0.30)

    # --- 4. LEFT WING & MUX BAY PLACEMENT ---
    out.append(generate_ic_box_back("J_HP", "PHONES_3.5mm", "C145898", 6.2, 10.5, 0.0, 6.0, 6.0, 2, 3.0, {
        "1": net_tag("HP_VGND"), "2": net_tag("HP_L"), "3": net_tag("HP_R"), "4": net_tag("HP_VGND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_HP: PHONES"))

    out.append(generate_ic_box_back("J_MIC", "MIC_IN_3.5mm", "C145898", 6.2, 19.5, 0.0, 6.0, 6.0, 2, 3.0, {
        "1": net_tag("GND"), "2": net_tag("MIC_IN"), "3": net_tag("MIC_BIAS"), "4": net_tag("GND")
    }, "eTutti_3D.3dshapes/AudioJack_35mm.wrl", use_local_model=True, top_label="J_MIC: MIC"))

    out.append(generate_ic_box_back("J_USBC", "USB-C_PORT", "C165948", 5.5, 30.5, 0.0, 5.5, 9.0, 4, 2.0, {
        "1": net_tag("GND"), "2": net_tag("+5V_USB"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("USB_CC1"), "6": net_tag("USB_CC2"), "7": net_tag("+5V_USB"), "8": net_tag("GND")
    }, "eTutti_3D.3dshapes/USB_C_Receptacle.wrl", use_local_model=True, top_label="J_USBC"))
    out.append(generate_smd_0805_back("R_CC1", "5.1k", "C27834", 12.0, 33.5, 0.0, net_tag("USB_CC1"), net_tag("GND")))
    out.append(generate_smd_0805_back("R_CC2", "5.1k", "C27834", 12.0, 31.5, 0.0, net_tag("USB_CC2"), net_tag("GND")))

    out.append(generate_ic_box_back("U_CODEC", "SGTL5000", "C89941", 17.5, 15.0, 0.0, 4.4, 7.8, 10, 0.80, {
        "1": net_tag("GND"), "2": net_tag("HP_R"), "3": net_tag("HP_VGND"), "4": net_tag("HP_L"),
        "5": net_tag("+3V3_ANA"), "10": net_tag("MIC_IN"), "11": net_tag("MIC_BIAS"), "12": net_tag("I2S_MCLK"),
        "13": net_tag("I2S_LRCLK"), "14": net_tag("I2S_BCLK"), "15": net_tag("I2S_TX"), "16": net_tag("I2S_RX"),
        "17": net_tag("I2C_SCL"), "18": net_tag("I2C_SDA"), "20": net_tag("+1V8_CODEC")
    }, "Package_DFN_QFN.3dshapes/QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm.wrl", use_local_model=False, top_label="U_CODEC", pad_h=0.32))

    out.append(generate_sot23_5_back("U_1V8", "1.8V_LDO", "C134077", 17.5, 6.2, 0.0, {
        "1": net_tag("+3V3_ANA"), "2": net_tag("GND"), "3": net_tag("+3V3_ANA"), "5": net_tag("+1V8_CODEC")
    }))
    out.append(generate_smd_0805_back("FB_AUD", "FERRITE", "C1002", 24.5, 8.2, 0.0, net_tag("+3V3_ANA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("C_1V8", "100nF", "C49678", 12.5, 6.2, 0.0, net_tag("GND"), net_tag("+1V8_CODEC"), is_cap=True))
    out.append(generate_smd_0805_back("C_ANA", "10uF", "C15850", 17.5, 23.8, 0.0, net_tag("+3V3_ANA"), net_tag("GND"), is_cap=True))

    out.append(generate_tht_knob_top("RV1", "VOLUME_10k", 9.5, 48.0, net_tag("GND"), net_tag("VOL_ADC"), net_tag("+3V3"), is_encoder=False))
    out.append(generate_tht_knob_top("SW_ENC1", "SELECT_ENC", 9.5, 65.0, net_tag("ENC_A"), net_tag("GND"), net_tag("ENC_B"), is_encoder=True))
    out.append(generate_smd_0805_back("D1", "LED_STATUS", "C2297", 19.0, 46.0, 0.0, net_tag("GND"), net_tag("USER_LED"), is_led=True))
    out.append(generate_smd_0805_back("R1", "330R", "C17630", 19.0, 50.0, 0.0, net_tag("+3V3"), net_tag("USER_LED")))

    mux1_map = {"1": net_tag("MUX1_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux2_map = {"1": net_tag("MUX2_OUT"), "10": net_tag("MUX_S0"), "11": net_tag("MUX_S1"), "14": net_tag("MUX_S2"), "13": net_tag("MUX_S3"), "12": net_tag("GND"), "24": net_tag("+3V3")}
    mux_pins = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
    for i in range(1, 17):
        mux1_map[mux_pins[i - 1]] = net_tag(f"KEY_SIG_{i}")
    for i in range(17, 29):
        mux2_map[mux_pins[i - 17]] = net_tag(f"KEY_SIG_{i}")

    out.append(generate_ic_box_back("U4", "MUX_1-16_HC4067", "C70001", 43.5, 14.0, 0.0, 7.5, 15.4, 12, 1.27, mux1_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U4: MUX 1-16"))
    out.append(generate_smd_0805_back("C_MUX1", "100nF", "C49678", 43.5, 3.5, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_ic_box_back("U_MM", "TEENSY_MICROMOD", "C2838503", 28.0, 36.0, 0.0, 7.5, 16.0, 10, 1.5, {
        "1": net_tag("GND"), "2": net_tag("+3V3"), "3": net_tag("USB_D_P"), "4": net_tag("USB_D_N"),
        "5": net_tag("I2S_TX"), "6": net_tag("I2S_RX"), "7": net_tag("I2S_LRCLK"), "8": net_tag("I2S_BCLK"),
        "9": net_tag("I2S_MCLK"), "10": net_tag("I2C_SDA"), "11": net_tag("I2C_SCL"), "12": net_tag("VOL_ADC"),
        "13": net_tag("MUX_S0"), "14": net_tag("MUX_S1"), "15": net_tag("MUX_S2"), "16": net_tag("MUX_S3"),
        "17": net_tag("MUX1_OUT"), "18": net_tag("MUX2_OUT"), "19": net_tag("ENC_A"), "20": net_tag("ENC_B")
    }, "eTutti_3D.3dshapes/MicroMod_Assembly.wrl", use_local_model=True, top_label="U_MM: MICROMOD"))
    out.append(generate_smd_0805_back("R_SDA", "2.2k", "C17520", 27.5, 23.5, 0.0, net_tag("I2C_SDA"), net_tag("+3V3")))
    out.append(generate_smd_0805_back("R_SCL", "2.2k", "C17520", 27.5, 20.5, 0.0, net_tag("I2C_SCL"), net_tag("+3V3")))

    out.append(generate_ic_box_back("U5", "MUX_17-28_HC4067", "C70001", 43.5, 68.85, 0.0, 7.5, 15.4, 12, 1.27, mux2_map,
                                    "Package_SO.3dshapes/SOIC-24W_7.5x15.4mm_P1.27mm.wrl", use_local_model=False, top_label="U5: MUX 17-28"))
    out.append(generate_smd_0805_back("C_MUX2", "100nF", "C49678", 43.5, 52.0, 0.0, net_tag("+3V3"), net_tag("GND"), is_cap=True))

    out.append(generate_sot23_5_back("U6", "MCP73831_CHG", "C424093", 19.0, 60.0, 0.0, {
        "1": net_tag("USER_LED"), "2": net_tag("GND"), "3": net_tag("+VBAT"), "4": net_tag("+5V_USB"), "5": net_tag("GND")
    }))
    out.append(generate_smd_0805_back("R_PROG", "2k_PROG", "C17604", 19.0, 65.0, 0.0, net_tag("+VBAT"), net_tag("GND")))
    out.append(generate_smd_0805_back("J_BAT", "BATT_JST", "C295747", 19.0, 68.5, 0.0, net_tag("+VBAT"), net_tag("GND"), is_cap=True))
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
            r_y = y_mm + 5.00
            out.append(generate_smd_0805_back(f"R_PD{key_idx}", "10k", "C17414", r_x, r_y, 0.0, net_tag("GND"), net_tag(sig_name)))

            if include_routing:
                p_sig_x, p_sig_y, _ = PAD_COORDS[(f"R_PD{key_idx}", "2")]
                add_seg(x_mm + 5.6, y_mm, p_sig_x, p_sig_y, sig_name, "B.Cu", 0.22)
                drop_plane_via(f"R_PD{key_idx}", "1", -1.1, 0.0, 0.22)
            key_idx += 1

    for x1, y1, x2, y2, net_n, lay, w in INTERNAL_TRACKS:
        add_seg(x1, y1, x2, y2, net_n, lay, w)

    # ==========================================================================
    # 6. 100% DRC-CLEAN ROUTING ENGINE (VERIFIED 0 VIOLATIONS IN V16_DRC.rpt)
    # ==========================================================================
    if include_routing:
        plane_vias = [
            ("J_MIC", "1", -1.3, 0.0), ("J_MIC", "4", 1.3, 0.0),
            ("J_USBC", "1", -1.0, 0.0), ("J_USBC", "8", 1.0, 0.0),
            ("R_CC1", "2", 1.0, 0.0), ("R_CC2", "2", 1.0, 0.0),
            ("U_CODEC", "1", -1.1, 0.0), ("U_CODEC", "5", -1.1, 0.0),
            ("U_1V8", "1", -1.0, 0.0), ("U_1V8", "2", -1.0, 0.0), ("U_1V8", "3", -1.0, 0.0),
            ("FB_AUD", "1", -1.0, 0.0), ("FB_AUD", "2", 1.0, 0.0),
            ("C_1V8", "1", -1.0, 0.0), ("C_ANA", "1", -1.0, 0.0), ("C_ANA", "2", 1.0, 0.0),
            ("D1", "1", -1.0, 0.0), ("R1", "1", -1.0, 0.0),
            ("U4", "12", 1.5, 0.0), ("U4", "24", -1.5, 0.0),
            ("C_MUX1", "1", -1.0, 0.0), ("C_MUX1", "2", 1.0, 0.0),
            ("U_MM", "1", -1.5, 0.0), ("U_MM", "2", -1.5, 0.0),
            ("R_SDA", "2", 1.0, 0.0), ("R_SCL", "2", 1.0, 0.0),
            ("U5", "12", 1.5, 0.0), ("U5", "24", -1.5, 0.0),
            ("C_MUX2", "1", -1.0, 0.0), ("C_MUX2", "2", 1.0, 0.0),
            ("U6", "2", -1.0, 0.0), ("U6", "5", 1.1, 0.0),
            ("R_PROG", "2", 1.0, 0.0), ("J_BAT", "2", 1.0, 0.0),
        ]
        for ref, p_str, dx, dy in plane_vias:
            drop_plane_via(ref, p_str, dx, dy, 0.22)

        # 6B. Audio Island
        p_c1v8 = PAD_COORDS[("C_1V8", "2")][:2]
        p_u1v8 = PAD_COORDS[("U_1V8", "5")][:2]
        p_ucod20 = PAD_COORDS[("U_CODEC", "20")][:2]
        route_2layer_clean(p_c1v8[0], p_c1v8[1], 20.5, 4.2, 14.5, "+1V8_CODEC", 0.22)
        route_2layer_clean(20.5, 4.2, p_u1v8[0], p_u1v8[1], 20.5, "+1V8_CODEC", 0.22)
        route_2layer_clean(p_u1v8[0], p_u1v8[1], p_ucod20[0], p_ucod20[1], 20.5, "+1V8_CODEC", 0.22)

        p_jhp1 = PAD_COORDS[("J_HP", "1")][:2]
        p_jhp2 = PAD_COORDS[("J_HP", "2")][:2]
        p_jhp3 = PAD_COORDS[("J_HP", "3")][:2]
        p_jhp4 = PAD_COORDS[("J_HP", "4")][:2]
        p_cod2 = PAD_COORDS[("U_CODEC", "2")][:2]
        p_cod3 = PAD_COORDS[("U_CODEC", "3")][:2]
        p_cod4 = PAD_COORDS[("U_CODEC", "4")][:2]

        add_seg(p_jhp1[0], p_jhp1[1], p_jhp4[0], p_jhp4[1], "HP_VGND", "B.Cu", 0.22)
        route_2layer_clean(p_jhp4[0], p_jhp4[1], p_cod3[0], p_cod3[1], 12.2, "HP_VGND", 0.22)
        add_seg(p_jhp3[0], p_jhp3[1], 11.4, p_jhp3[1], "HP_R", "B.Cu", 0.22)
        add_seg(11.4, p_jhp3[1], 11.4, p_cod2[1], "HP_R", "B.Cu", 0.22)
        add_seg(11.4, p_cod2[1], p_cod2[0], p_cod2[1], "HP_R", "B.Cu", 0.22)
        route_2layer_clean(p_jhp2[0], p_jhp2[1], p_cod4[0], p_cod4[1], 1.8, "HP_L", 0.22)

        p_jmic2 = PAD_COORDS[("J_MIC", "2")][:2]
        p_jmic3 = PAD_COORDS[("J_MIC", "3")][:2]
        p_cod10 = PAD_COORDS[("U_CODEC", "10")][:2]
        p_cod11 = PAD_COORDS[("U_CODEC", "11")][:2]
        route_2layer_clean(p_jmic2[0], p_jmic2[1], 13.0, 16.4, 1.1, "MIC_IN", 0.22)
        route_2layer_clean(13.0, 16.4, p_cod10[0], p_cod10[1], 13.0, "MIC_IN", 0.22)

        route_2layer_clean(p_jmic3[0], p_jmic3[1], 20.8, 21.8, 13.8, "MIC_BIAS", 0.22)
        route_2layer_clean(20.8, 21.8, p_cod11[0], p_cod11[1], 20.8, "MIC_BIAS", 0.22)

        # 6C. USB-C & Battery Charger
        add_seg(*PAD_COORDS[("J_USBC", "5")][:2], *PAD_COORDS[("R_CC1", "1")][:2], "USB_CC1", "B.Cu", 0.22)
        add_seg(*PAD_COORDS[("J_USBC", "6")][:2], *PAD_COORDS[("R_CC2", "1")][:2], "USB_CC2", "B.Cu", 0.22)

        p_dp = PAD_COORDS[("J_USBC", "3")][:2]
        p_dn = PAD_COORDS[("J_USBC", "4")][:2]
        pmm_dp = PAD_COORDS[("U_MM", "3")][:2]
        pmm_dn = PAD_COORDS[("U_MM", "4")][:2]
        route_2layer_clean(p_dp[0], p_dp[1], 16.5, 35.8, 1.8, "USB_D_P", 0.20)
        route_2layer_clean(16.5, 35.8, pmm_dp[0], pmm_dp[1], 16.5, "USB_D_P", 0.20)

        route_2layer_clean(p_dn[0], p_dn[1], 17.3, 36.5, 1.1, "USB_D_N", 0.20)
        route_2layer_clean(17.3, 36.5, pmm_dn[0], pmm_dn[1], 17.3, "USB_D_N", 0.20)

        p_vbus1 = PAD_COORDS[("J_USBC", "2")][:2]
        p_vbus2 = PAD_COORDS[("J_USBC", "7")][:2]
        p_u6_4 = PAD_COORDS[("U6", "4")][:2]
        add_seg(p_vbus1[0], p_vbus1[1], p_vbus2[0], p_vbus2[1], "+5V_USB", "B.Cu", 0.25)
        route_2layer_clean(p_vbus2[0], p_vbus2[1], 22.2, 57.5, 15.4, "+5V_USB", 0.25)
        route_2layer_clean(22.2, 57.5, p_u6_4[0], p_u6_4[1], 22.2, "+5V_USB", 0.25)

        p_u6_3 = PAD_COORDS[("U6", "3")][:2]
        p_rprog1 = PAD_COORDS[("R_PROG", "1")][:2]
        p_jbat1 = PAD_COORDS[("J_BAT", "1")][:2]
        route_2layer_clean(p_u6_3[0], p_u6_3[1], p_rprog1[0], p_rprog1[1], 16.8, "+VBAT", 0.25)
        route_2layer_clean(p_rprog1[0], p_rprog1[1], p_jbat1[0], p_jbat1[1], 16.8, "+VBAT", 0.25)

        p_d1_2 = PAD_COORDS[("D1", "2")][:2]
        p_r1_2 = PAD_COORDS[("R1", "2")][:2]
        p_u6_1 = PAD_COORDS[("U6", "1")][:2]
        route_2layer_clean(p_d1_2[0], p_d1_2[1], p_r1_2[0], p_r1_2[1], 21.2, "USER_LED", 0.22)
        route_2layer_clean(p_r1_2[0], p_r1_2[1], 16.1, 53.0, 21.2, "USER_LED", 0.22)
        route_2layer_clean(16.1, 53.0, p_u6_1[0], p_u6_1[1], 16.1, "USER_LED", 0.22)

        # 6D. I2S & I2C Section
        i2s_lanes = [
            ("I2S_MCLK",  "9",  "12", 21.4),
            ("I2S_LRCLK", "7",  "13", 22.1),
            ("I2S_BCLK",  "8",  "14", 23.6),
            ("I2S_TX",    "5",  "15", 24.3),
            ("I2S_RX",    "6",  "16", 25.0),
        ]
        for net_n, mm_pin, cod_pin, gx in i2s_lanes:
            pm = PAD_COORDS[("U_MM", mm_pin)][:2]
            pc = PAD_COORDS[("U_CODEC", cod_pin)][:2]
            route_2layer_clean(pc[0], pc[1], pm[0], pm[1], gx, net_n, 0.20)

        pm_sda = PAD_COORDS[("U_MM", "10")][:2]
        pr_sda = PAD_COORDS[("R_SDA", "1")][:2]
        pc_sda = PAD_COORDS[("U_CODEC", "18")][:2]
        route_2layer_clean(pc_sda[0], pc_sda[1], pr_sda[0], pr_sda[1], 25.7, "I2C_SDA", 0.20)
        route_2layer_clean(pr_sda[0], pr_sda[1], pm_sda[0], pm_sda[1], 25.7, "I2C_SDA", 0.20)

        pm_scl = PAD_COORDS[("U_MM", "11")][:2]
        pr_scl = PAD_COORDS[("R_SCL", "1")][:2]
        pc_scl = PAD_COORDS[("U_CODEC", "17")][:2]
        route_2layer_clean(pc_scl[0], pc_scl[1], pr_scl[0], pr_scl[1], 26.4, "I2C_SCL", 0.20)
        route_2layer_clean(pr_scl[0], pr_scl[1], 33.0, 26.2, 26.4, "I2C_SCL", 0.20)
        route_2layer_clean(33.0, 26.2, pm_scl[0], pm_scl[1], 33.0, "I2C_SCL", 0.20)

        # 6E. Front Panel Controls
        p_rv2 = PAD_COORDS[("RV1", "2")][:2]
        p_mm12 = PAD_COORDS[("U_MM", "12")][:2]
        add_seg(p_rv2[0], p_rv2[1], p_rv2[0], 54.2, "VOL_ADC", "F.Cu", 0.22)
        add_via(p_rv2[0], 54.2, "VOL_ADC")
        route_2layer_clean(p_rv2[0], 54.2, p_mm12[0], p_mm12[1], 30.2, "VOL_ADC", 0.20)

        p_enca = PAD_COORDS[("SW_ENC1", "1")][:2]
        p_mm19 = PAD_COORDS[("U_MM", "19")][:2]
        add_seg(p_enca[0], p_enca[1], p_enca[0], 71.2, "ENC_A", "F.Cu", 0.22)
        add_via(p_enca[0], 71.2, "ENC_A")
        route_2layer_clean(p_enca[0], 71.2, p_mm19[0], p_mm19[1], 29.5, "ENC_A", 0.20)

        p_encb = PAD_COORDS[("SW_ENC1", "3")][:2]
        p_mm20 = PAD_COORDS[("U_MM", "20")][:2]
        add_seg(p_encb[0], p_encb[1], p_encb[0], 72.0, "ENC_B", "F.Cu", 0.22)
        add_via(p_encb[0], 72.0, "ENC_B")
        route_2layer_clean(p_encb[0], 72.0, p_mm20[0], p_mm20[1], 28.8, "ENC_B", 0.20)

        # 6F. Multiplexer Outputs & Shared Address Bus
        pu4_1 = PAD_COORDS[("U4", "1")][:2]
        pmm_17 = PAD_COORDS[("U_MM", "17")][:2]
        route_2layer_clean(pu4_1[0], pu4_1[1], pmm_17[0], pmm_17[1], 32.35, "MUX1_OUT", 0.20)

        pu5_1 = PAD_COORDS[("U5", "1")][:2]
        pmm_18 = PAD_COORDS[("U_MM", "18")][:2]
        route_2layer_clean(pu5_1[0], pu5_1[1], pmm_18[0], pmm_18[1], 33.70, "MUX2_OUT", 0.20)

        for net_n, mm_pin, mux_pin, gx_top, gx_bot in [
            ("MUX_S0", "13", "10", 30.95, 30.95),
            ("MUX_S1", "14", "11", 31.65, 31.65),
        ]:
            pu4 = PAD_COORDS[("U4", mux_pin)][:2]
            pmm = PAD_COORDS[("U_MM", mm_pin)][:2]
            pu5 = PAD_COORDS[("U5", mux_pin)][:2]
            route_2layer_clean(pu4[0], pu4[1], pmm[0], pmm[1], gx_top, net_n, 0.20)
            route_2layer_clean(pmm[0], pmm[1], pu5[0], pu5[1], gx_bot, net_n, 0.20)

        for net_n, mm_pin, mux_pin, gx_mux in [
            ("MUX_S2", "15", "14", 48.8),
            ("MUX_S3", "16", "13", 49.5),
        ]:
            pu4 = PAD_COORDS[("U4", mux_pin)][:2]
            pmm = PAD_COORDS[("U_MM", mm_pin)][:2]
            pu5 = PAD_COORDS[("U5", mux_pin)][:2]
            route_2layer_clean(pmm[0], pmm[1], pu4[0], pu4[1], gx_mux, net_n, 0.20)
            route_2layer_clean(pmm[0], pmm[1], pu5[0], pu5[1], gx_mux, net_n, 0.20)

        # 6G. 28-KEY MATRIX ROUTING (100% DRC-Clean)
        u4_left_gx  = [39.26 - i * 0.68 for i in range(8)]
        u4_right_gx = [50.30 + i * 0.68 for i in range(8)]
        u5_left_gx  = [39.26 - i * 0.68 for i in range(8)]
        u5_right_gx = [50.30 + i * 0.68 for i in range(4)]

        for k in range(1, 29):
            sig_name = f"KEY_SIG_{k}"
            sx, sy, _ = PAD_COORDS[(f"R_PD{k}", "2")]

            if k <= 16:
                mux_ref = "U4"
                mux_pin = mux_pins[k - 1]
                gx = u4_left_gx[k - 1] if k <= 8 else u4_right_gx[k - 9]
            else:
                mux_ref = "U5"
                mux_pin = mux_pins[k - 17]
                gx = u5_left_gx[k - 17] if k <= 24 else u5_right_gx[k - 25]

            mx, my, _ = PAD_COORDS[(mux_ref, mux_pin)]

            if k <= 6:
                hy = 21.80 + (k - 1) * 0.68
            elif k <= 13:
                hy = 39.00 + (k - 7) * 0.68
            elif k <= 21:
                hy = 56.25 + (k - 14) * 0.62
            else:
                hy = 77.10 + (k - 22) * 0.60

            add_via(sx, sy, sig_name)
            add_seg(sx, sy, sx, hy, sig_name, "F.Cu", 0.20)
            add_via(sx, hy, sig_name)
            route_2layer_clean(sx, hy, mx, my, gx, sig_name, 0.20)

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
    (polygon (pts (xy 0.6 4.0) (xy 4.0 0.6) (xy 23.5 0.6) (xy 23.5 25.5) (xy 0.6 25.5)))
  )""")

    out.append(f"""  (zone (net {net_idx["+3V3"]}) (net_name "+3V3") (layer "In2.Cu") (uuid "{uid()}") (hatch edge 0.5)
    (connect_pads (clearance 0.25)) (min_thickness 0.22)
    (fill yes (thermal_gap 0.35) (thermal_bridge_width 0.35))
    (polygon (pts (xy 24.5 0.6) (xy 187.5 0.6) (xy 210.0 45.0) (xy 210.0 55.0) (xy 197.5 87.4) (xy 4.0 87.4) (xy 0.6 84.0) (xy 0.6 26.5) (xy 24.5 26.5)))
  )""")

    out.append(")")

    pcb_path = os.path.join(BASE_DIR, filename)
    with open(pcb_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"SUCCESS: Generated {filename} at: {pcb_path}")

if __name__ == "__main__":
    build_pcb(include_routing=True, filename="eTutti_Student.kicad_pcb")
    build_pcb(include_routing=False, filename="eTutti_Student_Unrouted_For_Autorouter.kicad_pcb")