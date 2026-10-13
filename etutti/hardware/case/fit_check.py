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
# Teensy 4.0 + Audio Board Rev D, as on the current board (generate.py /
# assembly3d.py): pin rows 15.24 apart, 14 pins at 2.54; Audio Board 5 mm
# past pin 1 (USB end), 2 mm past pin 14, 14 mm beyond the 0-12 row (jack
# side), 9.5 mm beyond the VIN row.
AUDIO_LIFT = 3.0          # Audio Board above the main board on its header legs
BOARD_T = 1.6
STACKS = {
    # female stacking headers 8.5 + the Teensy's 2.5 spacer: 19.8 mm to the USB top
    "A": {"label": "pilha atual (soquetes 8,5 mm, 19,8 mm)", "gap": 8.5 + 2.5},
    # Teensy soldered straight onto the Audio Board's pins (2.5 mm spacer only)
    "B": {"label": "pilha baixa (Teensy soldado na Audio Board, 11,3 mm)", "gap": 2.5},
}
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
    s = STACKS[kind]
    zb = C.Z_PCB_TOP + AUDIO_LIFT              # Audio Board bottom
    za = zb + BOARD_T                          # ...top
    zt = za + s["gap"]                         # Teensy bottom
    ax0 = STACK_X0
    p1 = ax0 + 5.0                             # pin 1 (USB end)
    cx = p1 + 6.5 * 2.54
    cy = STACK_Y0 + 9.5 + 7.62
    parts = []
    parts.append(("Audio Board", "audio", box(ax0, STACK_Y0, zb, ax0 + 40.0, STACK_Y0 + 9.5 + 15.24 + 14.0, za)))
    jy = cy + 7.62 + 7.2
    parts.append(("jack da Audio Board", "audio", box(ax0, jy - 3.0, za, ax0 + 13.0, jy + 3.0, za + 5.0)))
    parts.append(("codec", "audio", box(cx - 4, cy + 11, za, cx + 2, cy + 17, za + 0.9)))
    for ry in (cy - 7.62, cy + 7.62):
        parts.append(("barra de pinos", "stack", box(cx - 17.78, ry - 1.27, za, cx + 17.78, ry + 1.27, zt)))
        parts.append(("pinos + solda no Teensy", "usb", box(cx - 17.78, ry - 0.7, zt + BOARD_T, cx + 17.78, ry + 0.7, zt + BOARD_T + 1.4)))
    parts.append(("Teensy 4.0", "teensy", box(cx - 17.78, cy - 8.89, zt, cx + 17.78, cy + 8.89, zt + BOARD_T)))
    parts.append(("chips do Teensy", "teensy", box(cx - 4, cy - 5, zt + BOARD_T, cx + 6, cy + 5, zt + BOARD_T + 0.9)))
    usb_x0 = cx - 18.8
    parts.append(("micro-USB do Teensy", "usb", box(usb_x0, cy - 3.8, zt + BOARD_T, cx - 13.5, cy + 3.8, zt + BOARD_T + 2.6)))
    zc = zt + BOARD_T + 1.3
    px, py, pz = USB_PLUG
    parts.append(("plugue micro-USB 90°", "plug", box(usb_x0 - px, cy - py / 2, zc - pz / 2, usb_x0, cy + py / 2, zc + pz / 2)))
    info = {"usb_top": zt + BOARD_T + 2.6, "teensy_top": zt + BOARD_T, "cx": cx, "cy": cy, "usb_z": zc,
            "x": (ax0, ax0 + 40.0), "y": (STACK_Y0, STACK_Y0 + 38.74)}
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
            "surface": surface, "led_stand": (C.z_interface(ly) - (C.GHOST_SKIN if v is C.VERSIONS["madeira"] else 0.0))
            - sub_top - 5.3}
    return parts, info


def tilted(solid, y_pivot, z_pivot):
    ang = math.degrees(math.atan((C.Z_IF_BACK - C.Z_IF_FRONT) / C.WIDTH))
    return solid.rotate(cq.Vector(0, y_pivot, z_pivot), cq.Vector(1, y_pivot, z_pivot), -ang)


def chorus_parts(v):
    x0, y0, x1, y1 = C.SCREEN_ZONE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mx, my, mh = SCREEN_MOD
    ztop = C.z_interface(cy, v["top"]) - 0.2
    mod = box(cx - mx / 2, cy - my / 2, ztop - mh, cx + mx / 2, cy + my / 2, ztop)
    cxn, cyn, chn = SCREEN_CONN
    conn = box(cx - cxn / 2, cy - cyn / 2, ztop - mh - chn, cx + cxn / 2, cy + cyn / 2, ztop - mh)
    holes = C.grille_holes()
    gx = sum(p[0] for p in holes) / len(holes)
    gy = sum(p[1] for p in holes) / len(holes)
    d, h = SPEAKER
    zs = C.z_interface(gy + d / 2, v["top"]) - 0.3
    return [("tela 1,9\" (módulo)", "screen", tilted(mod, cy, ztop)),
            ("conector da tela", "screen", tilted(conn, cy, ztop)),
            ("alto-falante 28 mm", "speaker", cyl(gx, gy, zs - h, zs, d))], (gx, gy)


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
    shell = C.shell(v, ghost_led=(version == "madeira"))
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


def max_gap(chorus, version):
    """Largest Teensy-to-Audio-Board spacing that still fits (0.5 mm
    clear): the USB plug under the lid, and in the Chorus everything on
    the Teensy under the screen module and its connector."""
    v = C.VERSIONS[version]
    _, info = stack("B")
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
    return g


def interior_widths(v):
    """Free full-height width of the interface area at row 2 (the narrowest)."""
    left = v["wall"]
    right = C.ROW2_X[0] - (C.D_BTN / 2 + C.CLR_SIDE) - (C.TRANS_TOP_OFF + v["wall"])
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
    if mode == "section":
        pl.add_mesh(sh.clip(normal=(0, 1, 0), origin=(0, yf, 0), invert=False), color="#d9d4cb")
    else:
        pl.add_mesh(sh.clip(normal=(1, 0, 0), origin=(118, 0, 0), invert=True), color="#d9d4cb", opacity=0.22)
    for i, (name, col, s) in enumerate(parts):
        m = mesh(s, "p%d" % i)
        if mode == "section":
            m = m.clip(normal=(0, 1, 0), origin=(0, yf, 0), invert=False)
            if m.n_points == 0:
                continue
        op = {"pcb": 0.3, "screen": 0.55}.get(col, 1.0) if mode != "section" else 1.0
        pl.add_mesh(m, color=COLOURS[col], opacity=op)
    pl.enable_anti_aliasing("ssaa")
    if mode == "section":
        pl.camera_position = [(46, -300, 17), (46, yf, 17), (0, 0, 1)]
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = 29
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


def main():
    out = []
    w = out.append
    zb = K.skirt_base_z()
    results = {}
    for sk in ("A", "B"):
        for chorus in (False, True):
            for version in ("seixo", "madeira"):
                results[(sk, chorus, version)] = run(sk, chorus, version)
                print("done", sk, chorus, version)
    sA = stack("A")[1]
    sB = stack("B")[1]
    iS = interface_board(C.VERSIONS["seixo"])[1]
    iM = interface_board(C.VERSIONS["madeira"])[1]

    w("# eTuttino — conferência da eletrônica no case (SPEC item 9)\n")
    w("Gerado por `fit_check.py` a partir de `case.py` (CadQuery). As peças são sólidos com as medidas "
      "de datasheet ou da placa atual; as incertas estão marcadas *conferir* no código. "
      "Coordenadas da SPEC (y para quem toca). Folga = menor distância entre a peça e o case (tampa + fundo).\n")
    w("## Resumo\n")
    w("RESUMO_AQUI\n")

    w("**Condições para caber (pilha B):**\n\n"
      "1. Teensy mais baixo que hoje. O espaço entre a Audio Board e o Teensy pode ser no máximo "
      "%.1f mm no eTuttino (Seixo) / %.1f mm (Madeira) e %.1f / %.1f mm no Chorus. Hoje são 11 mm "
      "(soquete 8,5 + espaçador 2,5). Teensy soldado direto nos pinos da Audio Board (2,5 mm, como a PJRC monta) cabe em todos. "
      "No eTuttino, um soquete baixo (~4–5 mm) ainda deixa o Teensy removível.\n"
      "2. Plugue micro-USB de 90° (≤ 11 mm a partir do conector, ≤ 7,5 mm de altura) no cabo até o USB de painel.\n"
      "3. Peças de painel com no máximo ~10 mm de corpo atrás do inserto: senão batem no potenciômetro (x = 20). "
      "Na Madeira a parede é afinada para %.1f mm em volta do inserto (bolsão por dentro).\n"
      "4. Potenciômetro, encoder e LED numa plaquinha sob a tampa, com pernas cortadas rente (~1,5 mm). "
      "Por baixo dela passa a borda da Audio Board, com o jack dela.\n"
      "5. O jack de painel ligado por fio aos pinos de fone da Audio Board, ou por um plugue de 90°. Um plugue reto de 3,5 mm "
      "não cabe entre a Audio Board e a parede.\n" % (
          max_gap(False, "seixo"), max_gap(False, "madeira"), max_gap(True, "seixo"), max_gap(True, "madeira"), C.INSERT_WALL))

    w("## 0. Antes de tudo: a grade das teclas mudou\n")
    w("A SPEC põe as fileiras a **16,5 mm** uma da outra (74,8 / 58,3 / 41,8 / 25,3), com meio passo de "
      "deslocamento: uma grade hexagonal (19,05 × cos 30° = 16,50), onde cada botão fica a 19,05 mm dos seis "
      "vizinhos. A PCB atual (`generate.py`, PR #77/#78) tem as fileiras a **19,05 mm** (grade MX retangular, "
      "267 × 97,2 mm). Ou seja, **a placa atual não serve neste case**: a PCB e a placa de switches têm que ser "
      "refeitas na grade nova. Notas, fileiras e firmware não mudam (a ordem C-griff é a mesma), só a geometria. "
      "Cabe com folga: switches a 2,5 mm entre fileiras (16,5 − 14), carcaça de cima a 1,5 mm, "
      "e sobram ~15 mm atrás da fileira 4 e na frente da fileira 1 para os multiplexadores, como hoje.\n")

    w("## 1. Teensy + Audio Board, tela, knobs, LED, alto-falante e conectores (9.1)\n")
    lS, rS = interior_widths(C.VERSIONS["seixo"])
    lM, rM = interior_widths(C.VERSIONS["madeira"])
    w("**Largura útil.** O ponto mais estreito da área de interface, na fileira 2, tem %.1f mm em cima "
      "(x = 0 até o começo do declive, x = %.1f: o arco R 32,8 em volta do botão G3 corta o vértice vivo 56,6 da SPEC). "
      "A cavidade com altura total vai de x = %.1f a %.1f no Seixo (%.1f mm) e de %.1f a %.1f na Madeira (%.1f mm). "
      "Os ~68 mm da SPEC são o vértice da abertura das teclas (68,49), não o espaço interno. Abaixo do declive "
      "a cavidade continua (o teto desce até a tampa das teclas, z = %.1f), então peças baixas podem ir mais para a direita.\n" % (
          C.ROW2_X[0] - 22.5 - C.TRANS_TOP_OFF, C.ROW2_X[0] - 22.5 - C.TRANS_TOP_OFF, lS, rS, rS - lS, lM, rM, rM - lM, C.Z_PLATE_TOP))
    w("**Arranjo testado** (vista de cima em `renders/fit_top.png`): placa principal estendida para a esquerda por baixo "
      "da interface (uma placa só; a pilha continua presa só pelas pernas dos headers). A pilha fica no canto de trás, "
      "fileira VIN atrás, USB virado para a face esquerda: Audio Board em x %.0f–%.0f, y %.0f–%.1f; Teensy em y %.1f–%.1f. "
      "A borda esquerda fica a 20 mm da parede para caber o plugue USB de 90° e as peças de painel. "
      "Potenciômetro, encoder e LED vão numa plaquinha de interface pendurada sob a tampa (y 37–53), "
      "por cima da borda da Audio Board.\n" % (
          sA["x"][0], sA["x"][1], sA["y"][0], sA["y"][1], sA["cy"] - 8.89, sA["cy"] + 8.89))
    for sk in ("A", "B"):
        info = stack(sk)[1]
        w("### Pilha %s — %s\n" % (sk, STACKS[sk]["label"]))
        w("Topo do Teensy z = %.1f, topo do micro-USB z = %.1f, plugue USB de 90° até z = %.1f. Teto interno sobre o Teensy: "
          "z = %.1f (Seixo) / %.1f (Madeira).\n" % (
              info["teensy_top"], info["usb_top"], info["usb_z"] + USB_PLUG[2] / 2,
              C.z_interface(info["cy"], C.VERSIONS["seixo"]["top"]), C.z_interface(info["cy"], C.VERSIONS["madeira"]["top"])))
        w("| Peça | eTuttino Seixo | eTuttino Madeira | Chorus Seixo | Chorus Madeira |")
        w("|---|---|---|---|---|")
        names = [r[0] for r in results[(sk, True, "seixo")][0]]
        seen = set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            cells = []
            for chorus in (False, True):
                for version in ("seixo", "madeira"):
                    rows = [r for r in results[(sk, chorus, version)][0] if r[0] == name]
                    if not rows:
                        cells.append("—")
                        continue
                    vol = max(r[1] for r in rows)
                    gap = min(r[2] for r in rows)
                    cells.append(verdict(vol, gap))
            w("| %s | %s |" % (name, " | ".join(cells)))
        w("")
        hits = {}
        for chorus in (False, True):
            for version in ("seixo", "madeira"):
                for a, b, vol, gap in results[(sk, chorus, version)][1]:
                    key = (a, b)
                    hits.setdefault(key, []).append(("Chorus " if chorus else "eTuttino ") + version.capitalize() + ": " + verdict(vol, gap))
        if hits:
            w("Entre peças (menos de 1 mm):\n")
            for (a, b), lst in hits.items():
                w("- %s × %s — %s" % (a, b, "; ".join(sorted(set(lst)))))
            w("")

    w("## 2. Altura dos eixos (9.2)\n")
    w("Knob Ø9 a %.1f mm da superfície, eixo entrando %.0f mm no knob. Superfície em y = 45: z = %.2f.\n" % (KNOB_GAP, KNOB_BORE, iS["surface"]))
    w("| Montagem | Comprimento L do eixo (da face de montagem) | Padrão EC11 / RK09 |")
    w("|---|---|---|")
    for label, L in (("plaquinha sob a tampa, Seixo", iS["L_sub"]), ("plaquinha sob a tampa, Madeira", iM["L_sub"]),
                     ("na placa principal (z %.1f)" % C.Z_PCB_TOP, iS["L_main"])):
        std = min(STD_L, key=lambda s: abs(s - L))
        w("| %s | %.1f mm | L = %d (%+.1f mm no knob) |" % (label, L, std, std - L))
    w("\nNa placa principal os corpos (z %.1f–%.1f) bateriam na Audio Board/jack na pilha do canto de trás, "
      "e o eixo de 30 mm fica comprido e com folga lateral; a plaquinha sob a tampa usa eixos L = 15 (os mais comuns) e "
      "deixa os knobs baixos. O LED de 3 mm na mesma plaquinha precisa ficar %.1f mm acima dela no Seixo "
      "(ponta rente ao furo) e %.1f mm na Madeira (por baixo da pele de %.1f mm): um espaçador de LED resolve.\n" % (
          C.Z_PCB_TOP, C.Z_PCB_TOP + ENC[2], iS["led_stand"], iM["led_stand"], C.GHOST_SKIN))

    w("## 3. Saias de 17 mm (9.3)\n")
    w("- Vizinhos: passo 19,05 nas seis direções (a grade é hexagonal), saias Ø17 → **2,05 mm** entre saias. Ok para dedos e para imprimir; "
      "não dá para aumentar a saia além de ~18 mm.\n"
      "- Saia × borda da abertura: %.1f mm na frente/atrás e %.1f mm nas laterais (a folga da SPEC é medida do Ø15).\n"
      "- Saia × carcaça do switch: uma saia redonda Ø17 (Ø15,4 por dentro) sobre a carcaça quadrada do MX bate nos cantos "
      "se descer muito. Com curso de %.1f mm a base da saia tem que ficar a **%.1f mm acima da placa** com a tecla solta "
      "(z = %.2f), e a capa fica com %.2f mm de altura até o topo (z = 26,5) — um domo baixo de fato, com o tubo da haste "
      "por baixo. Consequência visual: entre a tampa (z 15,7) e a saia aparecem ~%.0f mm da carcaça do switch — "
      "por isso carcaça escura. Números de carcaça e haste são MX nominais: conferir com o Gateron KS-20 e com o teste de 4 capas.\n" % (
          C.CLR_FB - (C.D_SKIRT - C.D_BTN) / 2, C.CLR_SIDE - (C.D_SKIRT - C.D_BTN) / 2,
          K.TRAVEL, zb - C.Z_PLATE_TOP, zb, C.Z_KEY_TOP - zb, zb - C.Z_DECK))

    w("## 4. Espessura de parede (9.4)\n")
    s, m = C.VERSIONS["seixo"], C.VERSIONS["madeira"]
    w("| | Seixo (resina/MJF) | Madeira (carvalho, CNC) |")
    w("|---|---|---|")
    w("| Paredes laterais | %.1f mm | %.1f mm |" % (s["wall"], m["wall"]))
    w("| Tampa da interface | %.1f mm | %.1f mm |" % (s["top"], m["top"]))
    w("| Tampa em volta das teclas | %.1f mm (z %.1f–%.1f, apoiada na placa) | igual |" % (C.LID_T, C.Z_PLATE_TOP, C.Z_DECK))
    w("| Borda da abertura | arredondado 4 × %.1f + %.1f mm reto | igual — é o ponto mais frágil na madeira |" % (C.CHAMFER_DROP, C.LID_T - C.CHAMFER_DROP))
    w("| Teia da grade | %.1f mm entre furos | igual |" % (C.GRILLE_PITCH - C.GRILLE_D))
    w("| Fundo | %.1f mm, encaixado dentro das paredes | %.1f mm |" % (C.FLOOR_T, C.FLOOR_T))
    w("| LED | furo Ø%.1f | pele de %.1f mm por cima |" % (C.LED_HOLE_D, C.GHOST_SKIN))
    w("")
    w("- Resina e MJF: 2,5 mm é confortável (mínimo prático ~1,5–2). A borda de 1 mm da abertura passa, mas é melhor 1,2+ em resina frágil.\n"
      "- Madeira: 4 mm nas paredes e 3 mm na tampa são o mínimo sensato para carvalho. A borda da abertura (1 mm de altura reta, "
      "fibra cruzada nas pontas do hexágono) pode lascar: aumentar `CHAMFER_DROP`/`LID_T` só na Madeira ou deixar a borda mais grossa. "
      "Pele de 0,8 mm de carvalho branco quase não deixa a luz passar: testar numa sobra (0,5 mm e um LED forte costumam ser necessários).\n"
      "- A SPEC diz \"fresagem de 3 eixos de cima, numa fixação só\" incluindo o bolsão interno — não dá: o bolsão é por baixo. "
      "São **duas fixações**: de cima (contorno, abertura, arredondado, rebaixo da tela, furos) e virada (bolsão, rebaixo do fundo, "
      "bosses, teto inclinado da interface com fresa de topo esférico). Os cantos internos do bolsão já têm raio ≥ 12 mm.\n")

    w("## 5. Outras observações da SPEC\n")
    w("- O texto do item 4 diz que a borda de cima do declive é \"abertura + 20,3\", mas o vértice que ele dá, (56,6; 58,3), "
      "é abertura + 10,3 — o espelho do lado direito. Usei o vértice (`TRANS_TOP_OFF = 10.3`).\n"
      "- O contorno da grade passa ~1,2 mm da borda do declive no canto (75,5; 89). Os furos que cairiam no declive são "
      "descartados (`GRILLE_KEEP`); sobram %d furos.\n"
      "- Os vértices da caixa da SPEC usam a frente em y = 100,1 (74,8 + 15 + 10,3); o modelo prende a frente em y = 100 "
      "(diferença de 0,05 mm no x do vértice da frente).\n"
      "- O sistema de coordenadas da SPEC é canhoto (x direita, y para quem toca, z para cima). Modelado ao pé da letra, o instrumento "
      "sai espelhado num CAD. Os arquivos exportados são espelhados para y = 100 − y_SPEC (y para trás), "
      "e o instrumento fica certo: interface à esquerda de quem toca.\n" % len(C.grille_holes()))

    text = "\n".join(out)
    summary = summarise(results)
    text = text.replace("RESUMO_AQUI", summary)
    with open(os.path.join(HERE, "FIT_CHECK.md"), "w", encoding="utf-8") as f:
        f.write(text)
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    R = os.path.join(HERE, "renders")
    rows, hits, sinfo, iinfo, parts, shell = results[("B", True, "seixo")]
    render_fit(parts, shell, os.path.join(R, "fit_iso.png"), "iso")
    render_fit(parts, shell, os.path.join(R, "fit_top.png"), "top")
    render_fit(parts, shell, os.path.join(R, "fit_section_B.png"), "section", sinfo["cy"],
               "Chorus, pilha baixa: corte na linha do Teensy (y = %.1f)" % sinfo["cy"])
    rows, hits, sinfo, iinfo, partsA, shellA = results[("A", True, "seixo")]
    render_fit(partsA, shellA, os.path.join(R, "fit_section_A.png"), "section", sinfo["cy"],
               "Chorus, pilha atual (19,8 mm): o Teensy entra na tela")
    print("FIT_CHECK.md written")


def summarise(results):
    lines = []
    for sk in ("A", "B"):
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
