"""SPEC item 9: does the electronics fit the case?

    C:/Users/julia/.venvs/cadquery/Scripts/python.exe fit_check.py

Builds the parts as solids (sizes from datasheets / the current board, the
uncertain ones marked CHECK), places them in the interface area, and for
every configuration measures collisions and clearances against the Seixo
and Madeira shells. Writes FIT_CHECK.md (in Portuguese, it answers
SPEC.md) and renders/fit_*.png.

Everything here is in SPEC coordinates (y towards the player); collisions
don't care about the mirroring case.py applies to the exported files.
"""
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case as C  # noqa: E402
import keycap as K  # noqa: E402

box, cyl = C.box3, C.cyl

# ------------------------------------------------------------- the parts
# Teensy 4.0 + Audio Board Rev D. Audio Board 38.0 x 36.8 x 6.7 mm (SB
# Components listing, checked by the user on their own board); pin rows
# 15.24 apart, 14 pins at 2.54 along the 38.0 side. Where the header sits
# on it is scaled from PJRC's pin diagram (CHECK): 3.6 mm past pin 1 (USB
# end), 1.4 mm past pin 14, 12.8 mm beyond the 0-12 row (jack side), 8.8 mm
# beyond the VIN row.
AUDIO_L, AUDIO_W, AUDIO_H = 38.0, 36.8, 6.7
PAST_USB, PAST_VIN = 3.6, 8.76
AUDIO_LIFT = 3.0          # Audio Board above the main board on its header legs
BOARD_T = 1.6
USB_ON_TEENSY = 2.6       # micro-USB socket height on the Teensy
STACKS = {
    # the user's soldered stack: ~13 mm from under the Audio Board to the top of the Teensy's USB
    "M": {"label": "pilha montada (13 mm)", "height": 13.0},
    # the same stack lowered by 3-4 mm (the user says it can be): the Chorus case, at its tallest
    "R": {"label": "pilha reduzida (10 mm)", "height": 10.0},
}


def stack_gap(kind):
    return STACKS[kind]["height"] - 2 * BOARD_T - USB_ON_TEENSY


STACK_X0 = 20.0           # Audio Board's USB-end edge: room for the USB plug + panel parts
STACK_Y0 = 5.0            # Audio Board's back edge (VIN row at the back, jack side forward)

# interface board under the lid: volume pot, encoder, LED
POT = (9.8, 11.0, 6.5)    # Alps RK09K-type vertical 9 mm pot, body x, y, h -- CHECK
ENC = (12.4, 13.2, 6.5)   # Alps EC11E body -- CHECK
SUB_PINS = 1.5            # THT legs under the interface board, trimmed
KNOB_GAP, KNOB_BORE = 0.8, 6.0    # knob bottom over the surface, shaft engagement
STD_L = (15, 20, 25, 30)  # EC11 / RK09 shaft lengths, from the mounting face

# screen (eTuttiChorus): Waveshare 1.9" 170x320 module 51.2 x 27.3 mm
SCREEN_MOD = (51.2, 27.3, 4.0)    # CHECK thickness (glass + panel + PCB)
SCREEN_CONN = (8.0, 5.0, 3.0)     # GH1.25 connector on the back -- CHECK
SPEAKER = (28.0, 5.0)     # 28 mm speaker, depth -- CHECK
USB_PANEL = (10.0, 10.0, 8.0)     # panel micro-B receptacle behind the insert: x, y, z -- CHECK (<= 10 deep)
JACK_PANEL = (10.0, 8.0)  # panel jack body: length, diameter -- CHECK (<= 10 deep)
USB_PLUG = (11.0, 11.0, 7.5)      # right-angle micro-B plug on the Teensy: x, y, z (slim ones are 6) -- CHECK

COLOURS = {"pcb": "#1d6b3a", "stack": "#2e8b57", "teensy": "#3cb371", "usb": "#c0c0c0", "plug": "#444444",
           "audio": "#14532d", "sub": "#1d6b3a", "knobpart": "#b0b0b0", "screen": "#202840",
           "speaker": "#806040", "panel": "#909090", "led": "#40d060", "switch": "#26282c", "plate": "#111111"}


def stack(kind):
    zb = C.Z_PCB_TOP + AUDIO_LIFT              # Audio Board bottom
    za = zb + BOARD_T                          # ...top
    zt = za + stack_gap(kind)                  # Teensy bottom
    ax0 = STACK_X0
    p1 = ax0 + PAST_USB                        # pin 1 (USB end)
    cx = p1 + 6.5 * 2.54
    cy = STACK_Y0 + PAST_VIN + 7.62
    parts = []
    parts.append(("Audio Board", "audio", box(ax0, STACK_Y0, zb, ax0 + AUDIO_L, STACK_Y0 + AUDIO_W, za)))
    jy = cy + 7.62 + 7.2
    parts.append(("jack da Audio Board", "audio", box(ax0, jy - 3.0, za, ax0 + 13.0, jy + 3.0, zb + AUDIO_H)))
    parts.append(("codec", "audio", box(cx - 4, cy + 11, za, cx + 2, cy + 17, za + 0.9)))
    for ry in (cy - 7.62, cy + 7.62):
        parts.append(("barra de pinos", "stack", box(cx - 17.78, ry - 1.27, za, cx + 17.78, ry + 1.27, zt)))
        parts.append(("pinos + solda no Teensy", "usb", box(cx - 17.78, ry - 0.7, zt + BOARD_T, cx + 17.78, ry + 0.7, zt + BOARD_T + 1.4)))
    parts.append(("Teensy 4.0", "teensy", box(cx - 17.78, cy - 8.89, zt, cx + 17.78, cy + 8.89, zt + BOARD_T)))
    parts.append(("chips do Teensy", "teensy", box(cx - 4, cy - 5, zt + BOARD_T, cx + 6, cy + 5, zt + BOARD_T + 0.9)))
    usb_x0 = cx - 18.8
    parts.append(("micro-USB do Teensy", "usb", box(usb_x0, cy - 3.8, zt + BOARD_T, cx - 13.5, cy + 3.8, zt + BOARD_T + USB_ON_TEENSY)))
    zc = zt + BOARD_T + 1.3
    px, py, pz = USB_PLUG
    parts.append(("plugue micro-USB 90°", "plug", box(usb_x0 - px, cy - py / 2, zc - pz / 2, usb_x0, cy + py / 2, zc + pz / 2)))
    info = {"usb_top": zt + BOARD_T + USB_ON_TEENSY, "teensy_top": zt + BOARD_T, "cx": cx, "cy": cy, "usb_z": zc,
            "x": (ax0, ax0 + AUDIO_L), "y": (STACK_Y0, STACK_Y0 + AUDIO_W)}
    return parts, info


def interface_board(v):
    """Pot + encoder + LED on a small board hung under the lid: the bodies'
    tops touch the lid's underside."""
    y = C.VOLUME_XY[1]
    half = max(POT[1], ENC[1]) / 2
    ceiling = C.z_interface(y + half, v["top"]) - 0.2       # the lid is lowest at the bodies' front edge
    sub_top = ceiling - max(POT[2], ENC[2])
    parts = [("placa de interface", "sub", box(14.5, y - half - 0.4, sub_top - BOARD_T, 56.0, y + half + 0.4, sub_top))]
    for (x, yy), (bx, by, bh), name in ((C.VOLUME_XY, POT, "potenciômetro"), (C.SELECT_XY, ENC, "encoder")):
        parts.append((name, "knobpart", box(x - bx / 2, yy - by / 2, sub_top, x + bx / 2, yy + by / 2, sub_top + bh)))
        parts.append((name + " (pernas)", "knobpart", box(x - bx / 2, yy - by / 2, sub_top - BOARD_T - SUB_PINS, x + bx / 2, yy + by / 2, sub_top - BOARD_T)))
    lx, ly = C.LED_XY
    parts.append(("LED 3 mm", "led", cyl(lx, ly, sub_top, ceiling - 1.0, 3.0)))
    surface = C.z_interface(y)
    tip = surface + KNOB_GAP + KNOB_BORE
    info = {"sub_top": sub_top, "L_sub": tip - sub_top, "L_main": tip - C.Z_PCB_TOP,
            # LED tip: flush in the Seixo's hole; under the Madeira's acrylic window (as thick as the top)
            "surface": surface, "led_stand": (C.z_interface(ly) - (v["top"] if v is C.VERSIONS["madeira"] else 0.0))
            - sub_top - 5.3}
    return parts, info


def tilted(solid, y_pivot, z_pivot):
    """Turned to lie under the 13 deg part of the interface top."""
    return solid.rotate(cq.Vector(0, y_pivot, z_pivot), cq.Vector(1, y_pivot, z_pivot), -C.IF_SLOPE)


def chorus_parts(v):
    x0, y0, x1, y1 = C.SCREEN_ZONE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mx, my, mh = SCREEN_MOD
    ztop = C.z_interface(cy, v["top"]) - 0.2           # flat part: under the lid
    mod = box(cx - mx / 2, cy - my / 2, ztop - mh, cx + mx / 2, cy + my / 2, ztop)
    cxn, cyn, chn = SCREEN_CONN
    conn = box(cx - cxn / 2, cy - cyn / 2, ztop - mh - chn, cx + cxn / 2, cy + cyn / 2, ztop - mh)
    holes = C.grille_holes()
    gx = sum(p[0] for p in holes) / len(holes)
    gy = sum(p[1] for p in holes) / len(holes)
    d, h = SPEAKER
    zs = C.z_interface(gy, v["top"]) - 0.3              # its face parallel to the 13 deg lid, 0.3 under it
    spk = tilted(cyl(gx, gy, zs - h, zs, d), gy, zs)
    return [("tela 1,9\" (módulo)", "screen", mod),
            ("conector da tela", "screen", conn),
            ("alto-falante 28 mm", "speaker", spk)], (gx, gy)


def panel_parts(v):
    t = C.INSERT_WALL + 1.5      # behind the insert's flange (the wall is thinned there)
    ux, uy, uz = USB_PANEL
    (yu, zu), (yj, zj) = C.USB_YZ, C.JACK_YZ
    L, d = JACK_PANEL
    return [("USB de painel", "panel", box(t, yu - uy / 2, zu - uz / 2, t + ux, yu + uy / 2, zu + uz / 2)),
            ("jack de painel", "panel", cq.Solid.makeCylinder(d / 2, L, cq.Vector(t, yj, zj), cq.Vector(1, 0, 0)))]


def main_pcb(v):
    """The main board grown left under the interface (one board): the
    cavity's outline less 0.5 mm, notched round the screw bosses."""
    inner = C.contour_wp(C.box_contour()).offset2D(-v["wall"] - 0.5).wires().val()
    pcb = cq.Workplane("XY", origin=(0, 0, C.Z_PCB_BOT)).add(inner.translate(cq.Vector(0, 0, C.Z_PCB_BOT))).toPending().extrude(C.PCB_T).val()
    return pcb.cut(C.fuse([cyl(x, y, 0, 20, C.BOSS_D + 1.0) for x, y in C.screw_points()]))

# ------------------------------------------------------------- checks


def collide(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return float("nan")


def clearance(a, b):
    return a.distance(b)


def run(stack_kind, chorus, version):
    v = C.VERSIONS[version]
    shell = C.shell(v)
    fundo = C.fundo(v)
    parts, sinfo = stack(stack_kind)
    ib, iinfo = interface_board(v)
    parts += ib + panel_parts(v)
    parts.append(("placa principal", "pcb", main_pcb(v)))
    if chorus:
        cp, _ = chorus_parts(v)
        parts += cp
    rows = []
    for name, col, s in parts:
        vol = collide(s, shell) + collide(s, fundo)
        gap = min(clearance(s, shell), clearance(s, fundo))
        rows.append((name, vol, gap))
    # electronics against each other (only pairs that can meet)
    pair_hits = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            ni, nj = parts[i][0], parts[j][0]
            if parts[i][1] == parts[j][1] and parts[i][1] in ("audio", "stack", "teensy", "usb", "knobpart", "screen"):
                continue
            bbi, bbj = parts[i][2].BoundingBox(), parts[j][2].BoundingBox()
            if bbi.xmin > bbj.xmax + 3 or bbj.xmin > bbi.xmax + 3 or bbi.ymin > bbj.ymax + 3 or bbj.ymin > bbi.ymax + 3:
                continue
            vol = collide(parts[i][2], parts[j][2])
            gap = clearance(parts[i][2], parts[j][2])
            if gap < 1.0:
                pair_hits.append((ni, nj, vol, gap))
    return rows, pair_hits, sinfo, iinfo, parts, shell


def verdict(vol, gap):
    if vol > 0.01:
        return "**colide** (%.1f mm³)" % vol
    if gap < 0.5:
        return "justo (%.2f mm)" % gap
    return "ok (%.1f mm)" % gap


def max_stack(chorus, version):
    """Tallest stack (under the Audio Board to the USB top) that still fits (0.5 mm
    clear): the USB plug under the lid, and in the Chorus everything on
    the Teensy under the screen module and its connector."""
    v = C.VERSIONS[version]
    _, info = stack("R")
    cy = info["cy"]
    za = C.Z_PCB_TOP + AUDIO_LIFT + BOARD_T
    # plug top = za + gap + BOARD_T + 1.3 + USB_PLUG/2
    lid = C.z_interface(cy + USB_PLUG[1] / 2, v["top"])
    g = lid - 0.5 - (za + BOARD_T + 1.3 + USB_PLUG[2] / 2)
    if chorus:
        x0, y0, x1, y1 = C.SCREEN_ZONE
        ztop = C.z_interface(cy + 8.89, v["top"]) - 0.2 - SCREEN_MOD[2] - SCREEN_CONN[2]
        g = min(g, ztop - 0.5 - (za + BOARD_T + 2.6))       # the Teensy's USB socket / pins
        g = min(g, ztop + SCREEN_CONN[2] - 0.5 - (za + BOARD_T + 1.3 + USB_PLUG[2] / 2))
    return g + 2 * BOARD_T + USB_ON_TEENSY       # as a stack height, like STACKS


def interior_widths(v):
    """Free full-height width of the interface area in its front half,
    where the ramp's top edge runs straight (the narrowest part)."""
    left = v["wall"]
    right = C.ROW2_X[0] - (C.D_BTN / 2 + C.CLR_SIDE) - (C.RAMP_TOP_OFF + v["wall"])
    return left, right


def render_fit(parts, shell, path, mode="iso", section_y=None, title=""):
    """Pictures in the files' coordinates (mirrored, y away from the
    player), so they look like the instrument: interface on the left."""
    import pyvista as pv
    import tempfile
    tmp = tempfile.mkdtemp()
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1000))
    pl.set_background("#f3f1ec")

    def mesh(shape, name):
        p = os.path.join(tmp, name + ".stl")
        cq.exporters.export(cq.Workplane().add(C.to_file(shape)), p, tolerance=0.05)
        return pv.read(p)
    sh = mesh(shell, "shell")
    yf = C.WIDTH - section_y if section_y is not None else None
    xcut = section_y if mode == "xsection" else None
    if mode == "section":
        pl.add_mesh(sh.clip(normal=(0, 1, 0), origin=(0, yf, 0), invert=False), color="#d9d4cb")
    elif mode == "xsection":
        pl.add_mesh(sh.clip(normal=(1, 0, 0), origin=(xcut, 0, 0), invert=False), color="#d9d4cb")
    else:
        pl.add_mesh(sh.clip(normal=(1, 0, 0), origin=(118, 0, 0), invert=True), color="#d9d4cb", opacity=0.22)
    for i, (name, col, s) in enumerate(parts):
        m = mesh(s, "p%d" % i)
        if mode in ("section", "xsection"):
            m = (m.clip(normal=(0, 1, 0), origin=(0, yf, 0), invert=False) if mode == "section"
                 else m.clip(normal=(1, 0, 0), origin=(xcut, 0, 0), invert=False))
            if m.n_points == 0:
                continue
        op = {"pcb": 0.3, "screen": 0.55}.get(col, 1.0) if mode not in ("section", "xsection") else 1.0
        pl.add_mesh(m, color=COLOURS[col], opacity=op)
    pl.enable_anti_aliasing("ssaa")
    if mode == "section":
        pl.camera_position = [(46, -300, 17), (46, yf, 17), (0, 0, 1)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 29
        pl.add_text(title, position="upper_left", font_size=14, color="#333333")
    elif mode == "xsection":
        # looking along +x at the cut: the player's side (file y = 0) on the right
        pl.camera_position = [(-300, 50, 18), (xcut, 50, 18), (0, 0, 1)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 30
        pl.add_text(title, position="upper_left", font_size=14, color="#333333")
    elif mode == "top":
        pl.camera_position = [(58, 50, 400), (58, 50, 0), (0, 1, 0)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 54
    else:
        pl.camera_position = [(-95, -125, 150), (55, 50, 12), (0, 0, 1)]
        pl.camera.view_angle = 30
    pl.screenshot(path)
    pl.close()


def ramp_front_x(d):
    """Where a ramp edge (opening + d) meets the front face."""
    pts = C.ramp_edge(d, C.RAMP_FRONT_R)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 <= C.WIDTH <= y1:
            return x0 + (C.WIDTH - y0) * (x1 - x0) / (y1 - y0)


def deck_pocket(v):
    """The PCB area left of row 1, under the flat deck (between the ramp's
    inner foot and the plate's edge): its x span at a few y, and the
    headroom above the board."""
    foot = C.ROW2_X[0] - (C.D_BTN / 2 + C.CLR_SIDE) - (C.RAMP_FOOT_OFF + v["wall"])
    out = []
    for y in (62.0, 70.0, 78.0, 86.0, 92.0):
        plate = C.ROW2_X[0] - (C.D_BTN / 2 + C.CLR_SIDE) / C.COS + (y - C.ROW_Y[2]) * C.TAN - C.PLATE_OVERLAP / C.COS
        if y > C.ROW_Y[1] + C.D_BTN / 2 + C.CLR_FB:
            plate = 999.0
        sw = min(x for _, row, x, yy, _ in C.keys() if row == 1) - 7.0 if abs(y - C.ROW_Y[1]) < 8 else 999.0
        x_foot = foot
        if y > C.RAMP_STRAIGHT_TO:      # the foot curves away towards the front face
            r = C.RAMP_FRONT_R - v["wall"]
            cxf = foot - r
            dy = y - C.RAMP_STRAIGHT_TO
            x_foot = cxf + math.sqrt(max(r * r - dy * dy, 0.0)) if dy < r else cxf
        out.append((y, x_foot, min(plate, sw)))
    return out, C.Z_PLATE_TOP - C.Z_PCB_TOP, C.Z_PLATE_TOP - C.PLATE_T - C.Z_PCB_TOP


def keyboard_check():
    """Switches against each other (Gateron housing), plate web, caps
    against each other and the opening, switches against both shells."""
    x0 = C.O_KEYS + 3 * C.P
    a = K.switch(x0, C.ROW_Y[3])
    same = K.switch(x0 + C.P, C.ROW_Y[3])
    diag = K.switch(x0 + C.P / 2, C.ROW_Y[2])
    out = {"same_row": a.distance(same), "diagonal": a.distance(diag),
           "web_rows": C.ROW_PITCH - K.BOTTOM_W, "web_row": C.P - K.BOTTOM_W,
           "skirts": C.P - C.D_SKIRT, "buttons": C.P - C.D_BTN}
    sw = K.all_switches()
    for version in ("seixo", "madeira"):
        out["shell_" + version] = sw.distance(C.shell(C.VERSIONS[version]))
    return out


def main():
    out = []
    w = out.append
    zb = K.skirt_base_z()
    results = {}
    for sk in STACKS:
        for chorus in (False, True):
            for version in ("seixo", "madeira"):
                results[(sk, chorus, version)] = run(sk, chorus, version)
                print("done", sk, chorus, version)
    kb = keyboard_check()
    sM = stack("M")[1]
    iS = interface_board(C.VERSIONS["seixo"])[1]
    iM = interface_board(C.VERSIONS["madeira"])[1]
    ms = {(ch, v): max_stack(ch, v) for ch in (False, True) for v in ("seixo", "madeira")}
    length = C.ROW2_X[1] + C.D_BTN / 2 + C.CLR_SIDE + C.BOX_OFF

    w("# eTuttino — conferência do case (SPEC v6)\n")
    w("Gerado por `fit_check.py` a partir de `case.py` (CadQuery). As peças são sólidos com medidas "
      "de datasheet, da placa atual ou medidas por você; as incertas estão marcadas CHECK no código. "
      "Coordenadas da SPEC (y para quem toca). Folga = menor distância entre a peça e o case (tampa + fundo).\n")
    w("Mudanças da v6 aplicadas: tampa em volta das teclas em z = %.1f, saia das capas Ø%.1f, vinco R %.0f, "
      "LED da Madeira com furo e janela de acrílico (`madeira_led_janela`). Passo 18,5 e fim da rampa a 75° já "
      "estavam no modelo (PR #82).\n" % (C.Z_DECK, C.D_SKIRT, C.IF_CREASE_R))
    w("## Resumo\n")
    w("RESUMO_AQUI\n")
    w("Pilha mais alta que cabe (de baixo da Audio Board ao topo do USB do Teensy): **%.1f mm** no eTuttino Seixo, "
      "%.1f mm no eTuttino Madeira, **%.1f mm** no Chorus Seixo e %.1f mm no Chorus Madeira. A sua pilha tem ~13 mm.\n" % (
          ms[(False, "seixo")], ms[(False, "madeira")], ms[(True, "seixo")], ms[(True, "madeira")]))

    w("## 1. Teclado: passo %.2f mm, grade hexagonal\n" % C.P)
    w("Cada botão fica a **%.2f mm** dos seis vizinhos (lados e diagonais iguais, triângulos equiláteros). "
      "As fileiras ficam a %.2f × cos 30° = **%.2f mm** uma da outra, em y = %s (fileira 1 → 4). "
      "Folga da abertura: %.1f mm na frente e atrás, %.0f nas laterais. Comprimento total **%.1f mm**.\n" % (
          C.P, C.P, C.ROW_PITCH, ", ".join("%.2f" % C.ROW_Y[r] for r in (1, 2, 3, 4)), C.CLR_FB, C.CLR_SIDE, length))
    w("Medidas do Gateron KS-20 (desenho oficial KS-20TF10B045NW-X72): carcaça de cima 15,40 × 15,10 mm, "
      "11,10 mm da PCB ao topo da carcaça, placa a 5,00 mm, furo 14,00, curso 4,1 ± 0,2.\n")
    w("| Conferência | Folga |")
    w("|---|---|")
    w("| Carcaça × carcaça, mesma fileira | %.2f mm |" % kb["same_row"])
    w("| Carcaça × carcaça, diagonal (fileira vizinha) | %.2f mm (é o limite: passo mínimo ≈ 17,8 mm) |" % kb["diagonal"])
    w("| Teia da placa entre furos 14 × 14 | %.2f mm entre fileiras, %.2f mm na fileira |" % (kb["web_rows"], kb["web_row"]))
    w("| Botão Ø%.0f × vizinho | %.2f mm |" % (C.D_BTN, kb["buttons"]))
    w("| Saia Ø%.1f × vizinha (as seis, mesma fileira e diagonais) | %.2f mm |" % (C.D_SKIRT, kb["skirts"]))
    w("| Saia × borda da abertura | %.1f mm frente/trás, %.1f mm laterais |" % (
        C.CLR_FB - (C.D_SKIRT - C.D_BTN) / 2, C.CLR_SIDE - (C.D_SKIRT - C.D_BTN) / 2))
    w("| Switches × case | %.1f mm (Seixo), %.1f mm (Madeira) |" % (kb["shell_seixo"], kb["shell_madeira"]))
    w("")
    w("**Capas.** A saia redonda (Ø%.1f, parede de %.1f mm) não pode descer até os cantos da carcaça retangular do Gateron. "
      "Com o curso de %.1f mm, a base da saia fica a **%.2f mm acima da placa** com a tecla solta (z = %.2f; apertada, %.2f mm). "
      "A capa tem **%.2f mm** da base da saia ao topo (z = %.1f), com o tubo da haste por baixo. "
      "Entre a tampa (z %.1f) e a saia aparecem ~%.1f mm da carcaça escura. O topo da carcaça e a altura da haste não estão "
      "cotados no desenho do Gateron: o `keycap_test_4.stl` (4 capas) confirma isso nos switches reais.\n" % (
          C.D_SKIRT, K.SKIRT_WALL, K.TRAVEL, zb - C.Z_PLATE_TOP, zb, zb - C.Z_PLATE_TOP - K.TRAVEL,
          C.Z_KEY_TOP - zb, C.Z_KEY_TOP, C.Z_DECK, zb - C.Z_DECK))

    w("### Conferências pedidas na v6 (seção 9)\n")
    pressed = zb - K.TRAVEL
    w("1. **Tampa em z = %.1f × saia apertada.** A base da saia, com a tecla no fim do curso, fica em z = %.2f: "
      "**%.2f mm acima da tampa**. Ela não chega ao nível da tampa, então também não encosta na borda da abertura "
      "(que de qualquer forma está a %.1f mm na horizontal). A tampa mais grossa só cresce para cima: a face de baixo "
      "continua em z = %.1f, apoiada na placa, e nada da placa principal sob a faixa de %.1f mm muda. "
      "Switches × case: %.1f mm.\n" % (
          C.Z_DECK, pressed, pressed - C.Z_DECK, C.CLR_FB - (C.D_SKIRT - C.D_BTN) / 2, C.Z_PLATE_TOP, C.BOX_OFF,
          min(kb["shell_seixo"], kb["shell_madeira"])))
    w("2. **Saias Ø%.1f.** Na grade hexagonal os seis vizinhos ficam a %.1f mm, então a folga é **%.2f mm** em todas as "
      "direções, diagonais incluídas.\n" % (C.D_SKIRT, C.P, kb["skirts"]))
    w("3. **Fim da rampa.** A reta depois dos %.0f° só existe entre y ≈ %.1f e a face da frente; as bordas chegam à face em "
      "x ≈ %.1f (cima) e %.1f (baixo). A largura útil da interface (seção 2) e a faixa livre à esquerda da fileira 1 "
      "não mudam; a grade continua a 6 mm da rampa.\n" % (
          C.RAMP_FRONT_SWEEP, C.RAMP_STRAIGHT_TO + C.RAMP_FRONT_R * math.sin(math.radians(C.RAMP_FRONT_SWEEP)),
          ramp_front_x(C.RAMP_TOP_OFF), ramp_front_x(C.RAMP_FOOT_OFF)))
    w("4. **Madeira.** O reto da borda da abertura fica com **%.1f mm** (pedido: 2 mm), porque a tampa de %.1f mm "
      "apoia na placa e o chanfro desce %.1f mm (ver pergunta 1). O LED tem furo Ø%.1f passante e uma janela de "
      "acrílico difuso de Ø%.1f × %.1f mm colada rente (`out/madeira_led_janela.*`).\n" % (
          C.LID_T - C.CHAMFER_DROP, C.LID_T, C.CHAMFER_DROP, C.LED_HOLE_D,
          C.LED_HOLE_D - 2 * C.LED_WINDOW_CLR, C.VERSIONS["madeira"]["top"]))

    w("## 2. Teensy + Audio Board, tela, knobs, LED, alto-falante e conectores\n")
    lS, rS = interior_widths(C.VERSIONS["seixo"])
    lM, rM = interior_widths(C.VERSIONS["madeira"])
    w("Audio Board **38,0 × 36,8 × 6,7 mm** (anúncio da SB Components, conferido na sua placa), pilha montada de **~13 mm**. "
      "Largura útil da interface com altura total, na metade da frente (onde a rampa desce reta, o ponto mais estreito): "
      "%.1f mm no Seixo, %.1f mm na Madeira. Teto interno: z %.1f sob a parte plana (Seixo), caindo a 13° até z %.1f na frente.\n" % (
          rS - lS, rM - lM, C.z_interface(30, C.VERSIONS["seixo"]["top"]), C.z_interface(C.WIDTH, C.VERSIONS["seixo"]["top"])))
    pocket, head, head_plate = deck_pocket(C.VERSIONS["seixo"])
    w("**Por baixo da rampa e da tampa à esquerda da fileira 1** (Seixo). Ali o teto é a tampa do teclado: sobram "
      "**%.1f mm** acima da PCB (%.1f mm onde a placa de switches passa por cima). Faixa livre de placa de switches, por y: %s. "
      "Cabem peças baixas da placa principal (SMD, multiplexador, LDO, conectores baixos), não a pilha nem o alto-falante. "
      "Por baixo da rampa o teto sobe do nível da tampa até o da interface em ~%.1f mm na horizontal.\n" % (
          head, head_plate,
          "; ".join("y %.0f: x %.1f–%.1f" % (y, a_, b_) if b_ < 900 else "y %.0f: a partir de x %.1f" % (y, a_) for y, a_, b_ in pocket),
          (C.RAMP_TOP_OFF - C.RAMP_FOOT_OFF)))
    w("**Arranjo testado** (`renders/fit_top.png`): placa principal estendida por baixo da interface; pilha no canto de trás, "
      "fileira VIN atrás, USB para a face esquerda: Audio Board em x %.0f–%.0f, y %.0f–%.1f, Teensy em y %.1f–%.1f. "
      "Potenciômetro, encoder e LED numa plaquinha sob a tampa (y %.0f–%.0f), por cima da borda da Audio Board.\n" % (
          sM["x"][0], sM["x"][1], sM["y"][0], sM["y"][1], sM["cy"] - 8.89, sM["cy"] + 8.89,
          C.VOLUME_XY[1] - 7, C.VOLUME_XY[1] + 7))
    w("Ordem dos controles (v5): volume (%.0f; %.0f), seletor (%.0f; %.0f), LED (%.0f; %.0f); tela em x %.0f–%.0f.\n" % (
        C.VOLUME_XY + C.SELECT_XY + C.LED_XY + (C.SCREEN_ZONE[0], C.SCREEN_ZONE[2])))
    for sk in STACKS:
        info = stack(sk)[1]
        label = STACKS[sk]["label"]
        w("### %s\n" % (label[0].upper() + label[1:]))
        w("Topo do Teensy z = %.1f, topo do micro-USB z = %.1f, plugue USB de 90° até z = %.1f. Teto sobre o Teensy: "
          "z = %.1f (Seixo) / %.1f (Madeira).\n" % (
              info["teensy_top"], info["usb_top"], info["usb_z"] + USB_PLUG[2] / 2,
              C.z_interface(info["cy"], C.VERSIONS["seixo"]["top"]), C.z_interface(info["cy"], C.VERSIONS["madeira"]["top"])))
        w("| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |")
        w("|---|---|---|---|---|")
        seen = []
        for r in results[(sk, True, "seixo")][0]:
            if r[0] not in seen:
                seen.append(r[0])
        for name in seen:
            cells = []
            for chorus in (False, True):
                for version in ("seixo", "madeira"):
                    rows = [r for r in results[(sk, chorus, version)][0] if r[0] == name]
                    cells.append(verdict(max(r[1] for r in rows), min(r[2] for r in rows)) if rows else "—")
            w("| %s | %s |" % (name, " | ".join(cells)))
        w("")
        hits = {}
        for chorus in (False, True):
            for version in ("seixo", "madeira"):
                for x, y, vol, gap in results[(sk, chorus, version)][1]:
                    if vol > 0.01 or gap >= 0.05:
                        hits.setdefault((x, y), []).append(("Chorus " if chorus else "eTuttino ") + version.capitalize() + ": " + verdict(vol, gap))
        if hits:
            w("Entre peças (menos de 1 mm, sem contar as que se encostam de propósito):\n")
            for (x, y), lst in hits.items():
                w("- %s × %s — %s" % (x, y, "; ".join(sorted(set(lst)))))
            w("")
    w("Potenciômetro, encoder, tela e alto-falante aparecem como \"justo\" (0,2–0,3 mm) de propósito: ficam encostados "
      "por baixo da tampa. Figuras: `renders/fit_iso.png`, `fit_top.png` (eTuttino, pilha montada, Seixo, tampa transparente), "
      "`fit_section_M.png` (Chorus com a pilha de 13 mm, corte na linha do Teensy) `fit_section_R.png` (pilha reduzida), `fit_top_chorus.png` (Chorus em planta) e `fit_section_x.png` (corte de trás para a frente pelo alto-falante).\n")
    w("**Condições que continuam valendo:** plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura); "
      "peças de painel com no máximo ~10 mm de corpo atrás do inserto (na Madeira a parede é afinada para %.1f mm ali); "
      "potenciômetro, encoder e LED numa plaquinha sob a tampa, com pernas cortadas rente; fone de painel ligado por fio "
      "à Audio Board (um plugue reto de 3,5 mm não cabe).\n" % C.INSERT_WALL)

    w("## 3. Altura dos eixos\n")
    w("| Montagem | Eixo L (da face de montagem) | Padrão EC11 / RK09 |")
    w("|---|---|---|")
    for label, L in (("plaquinha sob a tampa, Seixo", iS["L_sub"]), ("plaquinha sob a tampa, Madeira", iM["L_sub"]),
                     ("na placa principal", iS["L_main"])):
        std = min(STD_L, key=lambda v: abs(v - L))
        w("| %s | %.1f mm | L = %d (%+.1f mm no knob) |" % (label, L, std, std - L))
    w("\nKnob Ø9 a %.1f mm da superfície, eixo %.0f mm dentro dele. O LED de 3 mm fica num espaçador de %.1f mm (Seixo) "
      "/ %.1f mm (Madeira) sobre a plaquinha.\n" % (KNOB_GAP, KNOB_BORE, iS["led_stand"], iM["led_stand"]))

    w("## 4. Espessura de parede\n")
    s_, m_ = C.VERSIONS["seixo"], C.VERSIONS["madeira"]
    w("| | Seixo (resina/MJF) | Madeira (carvalho, CNC) |")
    w("|---|---|---|")
    w("| Paredes | %.1f mm | %.1f mm (%.1f em volta do inserto) |" % (s_["wall"], m_["wall"], C.INSERT_WALL))
    w("| Tampa da interface | %.1f mm | %.1f mm |" % (s_["top"], m_["top"]))
    w("| Tampa em volta das teclas | %.1f mm, apoiada na placa | igual |" % C.LID_T)
    w("| Borda da abertura | arredondado %.0f × %.1f + %.1f mm reto | igual |" % (C.CHAMFER_W, C.CHAMFER_DROP, C.LID_T - C.CHAMFER_DROP))
    w("| Teia da grade | %.1f mm | igual |" % (C.GRILLE_PITCH - C.GRILLE_D))
    w("| LED | furo Ø%.1f | furo Ø%.1f + janela de acrílico difuso |" % (C.LED_HOLE_D, C.LED_HOLE_D))
    w("\nA Madeira precisa de duas fixações no CNC (de cima, e virada para o bolsão interno).\n")

    w("## 5. Perguntas para o design\n")
    q = []
    q.append("**Reto da borda da abertura.** A v6 pede 1 mm (Seixo) e 2 mm (Madeira) de reto abaixo do chanfro de 2 mm. "
             "Mas a tampa agora tem %.1f mm sobre a placa e apoia nela; com o chanfro de %.1f mm, sobram **%.1f mm de reto nas "
             "duas versões**. Para chegar a 1 / 2 mm haveria duas saídas: (a) um chanfro maior, de 4 × %.1f mm no Seixo e "
             "4 × %.1f mm na Madeira; (b) um rebaixo por baixo da tampa perto da abertura, e aí a tampa deixa de apoiar "
             "na placa ali. Ficamos com %.1f mm nas duas, ou qual das saídas?" % (
                 C.LID_T, C.CHAMFER_DROP, C.LID_T - C.CHAMFER_DROP, C.LID_T - 1.0, C.LID_T - 2.0, C.LID_T - C.CHAMFER_DROP))
    q.append("**Altura da tampa.** Com a saia Ø%.1f a base da saia sobe um pouco (uma saia mais estreita só passa pelos cantos "
             "do Gateron mais acima): solta em z = %.2f, apertada em z = %.2f. Entre a tampa (z %.1f) e a saia aparecem "
             "agora ~%.1f mm da carcaça. A tampa só pode subir mais ~%.1f mm (até a saia apertada menos 1 mm). Fica em %.1f?" % (
                 C.D_SKIRT, zb, zb - K.TRAVEL, C.Z_DECK, zb - C.Z_DECK, zb - K.TRAVEL - 1.0 - C.Z_DECK, C.Z_DECK))
    q.append("**Janela do LED (Madeira).** A janela tem a espessura da tampa (%.1f mm) e Ø%.1f. Recortar acrílico difuso "
             "nesse tamanho é chato. Uma alternativa é um condutor de luz redondo de 3 mm comprado pronto (light pipe), "
             "com a ponta lixada rente. Pode?" % (C.VERSIONS["madeira"]["top"], C.LED_HOLE_D - 2 * C.LED_WINDOW_CLR))
    q.append("**Próximo passo: PCB.** Com a v6, a caixa, a grade de teclas (passo 18,5, fileiras a %.2f mm) e a posição da "
             "pilha estão definidas. Dá para começar a refazer a PCB (`generate.py`/`build_pcb.py`) com este contorno "
             "interno, ou ainda há mudanças de forma previstas?" % C.ROW_PITCH)
    for i, t in enumerate(q, 1):
        w("%d. %s" % (i, t))
    w("")

    text = "\n".join(out).replace("RESUMO_AQUI", summarise(results))
    with open(os.path.join(HERE, "FIT_CHECK.md"), "w", encoding="utf-8") as f:
        f.write(text)
    R = os.path.join(HERE, "renders")
    os.makedirs(R, exist_ok=True)
    for old in ("fit_section_A.png", "fit_section_B.png", "fit_section_S.png"):
        if os.path.exists(os.path.join(R, old)):
            os.remove(os.path.join(R, old))
    rows, hits, sinfo, iinfo, parts, shell = results[("M", False, "seixo")]
    render_fit(parts, shell, os.path.join(R, "fit_iso.png"), "iso")
    render_fit(parts, shell, os.path.join(R, "fit_top.png"), "top")
    rows, hits, sinfo, iinfo, parts, shell = results[("R", True, "seixo")]
    render_fit(parts, shell, os.path.join(R, "fit_top_chorus.png"), "top")
    gx = sum(p[0] for p in C.grille_holes()) / len(C.grille_holes())
    render_fit(parts, shell, os.path.join(R, "fit_section_x.png"), "xsection", gx,
               "Chorus: corte em x = %.1f (alto-falante sob o plano a 13 graus, pilha, tela); frente a direita" % gx)
    for sk, title in (("M", "Chorus, pilha montada (13 mm): corte na linha do Teensy"),
                      ("R", "Chorus, pilha reduzida (10 mm): corte na linha do Teensy")):
        rows, hits, sinfo, iinfo, parts, shell = results[(sk, True, "seixo")]
        render_fit(parts, shell, os.path.join(R, "fit_section_%s.png" % sk), "section", sinfo["cy"], title)
    print("FIT_CHECK.md written")


def summarise(results):
    lines = []
    for sk in STACKS:
        for chorus in (False, True):
            bad = set()
            for version in ("seixo", "madeira"):
                rows, hits, *_ = results[(sk, chorus, version)]
                bad |= {r[0] for r in rows if r[1] > 0.01}
                bad |= {"%s × %s" % (a, b) for a, b, vol, gap in hits if vol > 0.01}
            model = "eTuttiChorus (tela + alto-falante)" if chorus else "eTuttino (sem tela)"
            if bad:
                lines.append("- **%s, %s: não cabe** — colide: %s." % (model, STACKS[sk]["label"], ", ".join(sorted(bad))))
            else:
                lines.append("- **%s, %s: cabe.**" % (model, STACKS[sk]["label"]))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
