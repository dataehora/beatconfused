"""eTutti Slim (R2SL): dimensioned section of the two magnetic knobs (option C) through the stem axis. Stdlib only.

    python etutti/hardware/slim/case/knobs_corte.py        -> case/img/knobs_corte.svg

Left: REGISTERS knob (platform of row 1, surface z = 14.0). Right: VOLUME knob (platform of row 4, surface z = 21.0), with the OFF magnet
and the Hall switch. z from the base's bottom. Main board: bottom z = 6.8 (set by the P2 jack, RESTRICOES_CASE R01), 1.2 mm thick, the
sensors and the Hall switch on its BOTTOM face. Every number below is a proposal of the Design; the fields are analytic estimates.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)

ZB_BOT, ZB_TOP = 6.8, 8.0            # main board
FLOOR = 1.6
WELL_D, WELL_DEPTH = 17.6, 1.2
LID_T = 1.5                          # material under the well floor
STEM_D, BEAR_D = 5.0, 5.4
HEAD_D, HEAD_Z0, HEAD_Z1 = 10.0, 9.0, 11.0
MAG_D, MAG_L, MAG_Z0 = 6.0, 2.0, 8.5
COLLAR_OD, COLLAR_H = 9.0, 3.0
KNOB_D, KNOB_TOP = 16.4, 4.8         # knob diameter, top above the platform surface
SK = 11.0                            # x offset of the second panel's axis relative to the first, in drawing units
INK, BLUE, RED, GREY, LID, KNOB, PCB, MAG = "#1d1d1f", "#1f5fa8", "#b3261e", "#8b8b8b", "#efe6d2", "#fbf9f3", "#2f6b3a", "#c0392b"


def build():
    W, H = 170, 52
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Arial,sans-serif">' % (W, H, W * 8, H * 8),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]

    def Z(z):   # drawing y (mm): z = 0 at y = 36
        return 36.0 - z

    def line(x0, z0, x1, z1, c=INK, w=0.15, dash=None):
        return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>' % (x0, Z(z0), x1, Z(z1), c, w, ' stroke-dasharray="%s"' % dash if dash else "")

    def rect(x0, z0, x1, z1, fill, c=INK, w=0.15, op=1):
        return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" stroke="%s" stroke-width="%.2f" opacity="%.2f"/>' % (
            x0, Z(z1), x1 - x0, z1 - z0, fill, c, w, op)

    def text(x, z, t, size=1.5, c=INK, anchor="start"):
        return '<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s">%s</text>' % (x, Z(z), size, c, anchor, t)

    def dim(x, z0, z1, label, side=1):
        xx = x + side * 0
        return (line(xx, z0, xx, z1, BLUE, 0.12) + line(xx - 0.5, z0, xx + 0.5, z0, BLUE, 0.12) + line(xx - 0.5, z1, xx + 0.5, z1, BLUE, 0.12)
                + text(xx + (0.8 if side > 0 else -0.8), (z0 + z1) / 2 - 0.4, label, 1.2, BLUE, "start" if side > 0 else "end"))

    for panel, (cx, zs, name, volume) in enumerate(((48.0, 14.0, "REGISTROS (fileira 1, tampo z 14,0)", False), (128.0, 21.0, "VOLUME (fileira 4, tampo z 21,0)", True))):
        zf = zs - WELL_DEPTH           # well floor
        zu = zf - LID_T                # lid underside under the well
        # lid slab: platform surface with the well, 1.5 mm floor, bearing collar
        o.append(rect(cx - 30, zu, cx - WELL_D / 2, zs, LID))
        o.append(rect(cx + WELL_D / 2, zu, cx + 30, zs, LID))
        o.append(rect(cx - WELL_D / 2, zu, cx - BEAR_D / 2, zf, LID))
        o.append(rect(cx + BEAR_D / 2, zu, cx + WELL_D / 2, zf, LID))
        o.append(rect(cx - COLLAR_OD / 2, zf, cx - BEAR_D / 2, zf + COLLAR_H, LID))
        o.append(rect(cx + BEAR_D / 2, zf, cx + COLLAR_OD / 2, zf + COLLAR_H, LID))
        # knob
        ztop = zs + KNOB_TOP
        o.append(rect(cx - KNOB_D / 2, zf + 0.3, cx + KNOB_D / 2, ztop, KNOB))
        o.append(rect(cx - 5.2, zf + 0.3, cx + 5.2, zf + COLLAR_H + 0.4, "#ffffff"))   # recess round the collar
        # stem: from inside the knob down through the bearing to the head
        o.append(rect(cx - STEM_D / 2, HEAD_Z1, cx + STEM_D / 2, ztop - 1.0, "#d9d9d9"))
        # head + magnets
        hw = (19.0 if volume else HEAD_D) / 2
        o.append(rect(cx - hw, HEAD_Z0, cx + hw, HEAD_Z1, "#d9d9d9"))
        o.append(rect(cx - MAG_D / 2, MAG_Z0, cx + MAG_D / 2, MAG_Z0 + MAG_L, MAG))
        o.append(text(cx, MAG_Z0 + 0.7, "N S", 1.1, "#ffffff", "middle"))
        if volume:
            mx = cx - 7.2
            o.append(rect(mx - 2, MAG_Z0, mx + 2, MAG_Z0 + MAG_L, MAG))
            o.append(text(mx, MAG_Z0 + 0.7, "OFF", 1.0, "#ffffff", "middle"))
        # board
        o.append(rect(cx - 24, ZB_BOT, cx + 24, ZB_TOP, PCB, op=0.9))
        o.append(rect(cx - 1.45, ZB_BOT - 1.65, cx + 1.45, ZB_BOT, "#555555"))        # TMAG5273 on the bottom face
        o.append(text(cx, ZB_BOT - 1.1, "TMAG5273", 0.9, "#ffffff", "middle"))
        if volume:
            o.append(rect(cx - 7.2 - 1.25, ZB_BOT - 1.05, cx - 7.2 + 1.25, ZB_BOT, "#555555"))   # DRV5032 on the bottom face
            o.append(text(cx - 7.2, ZB_BOT - 2.3, "DRV5032ZE", 0.9, INK, "middle"))
            o.append(rect(cx + 10.4, ZB_BOT - 0.6, cx + 11.8, ZB_BOT, "#d4a017"))        # LED 1615, reverse mount
            o.append(text(cx + 11.1, ZB_BOT - 1.6, "LED", 0.9, INK, "middle"))
        # floor
        o.append(rect(cx - 30, 0, cx + 30, FLOOR, GREY))
        # axis
        o.append(line(cx, 0, cx, ztop + 2, RED, 0.1, "1 0.6"))
        # dimensions (right side)
        xr = cx + 14.5
        o.append(dim(xr, zu, zs, "1,5 piso + 1,2 poco", 1))
        o.append(dim(xr + 7.5, zs, ztop, "4,8", 1))
        o.append(dim(cx - 14.5, HEAD_Z1, zu, "0,3 folga" if not volume else "%.1f folga" % (zu - HEAD_Z1), -1))
        o.append(dim(cx - 16.5, ZB_TOP, MAG_Z0, "0,5", -1))
        o.append(dim(cx - 19.0, MAG_Z0 + MAG_L / 2, ZB_BOT - 0.8, "ima-sensor 2,5 / 3,5 do centro", -1))
        o.append(text(cx - 24, ztop + 4.2 if volume else ztop + 4.0, name, 1.7, INK))
        notes = ["Haste Ø5,0 em mancal Ø5,4 (4,5 mm: 1,5 do piso + colar de 3,0 acima do piso)",
                 "Cabeca Ø%.0f (z 9,0-11,0) = retencao: a haste sobe de baixo, o knob entra por cima" % (19 if volume else 10),
                 "Ima Ø6 x 2,0 diametral, 0,5 mm acima da placa; 0,5 mm de pele de PA12 sobre ele"]
        if volume:
            notes.append("Ima de OFF Ø4 x 2,0 a 7,2 mm do eixo, sobre a chave Hall (campo ~100-120 mT)")
        for i, t in enumerate(notes):
            o.append(text(cx - 30, -2.5 - i * 1.7, t, 1.15, INK))
    o.append(text(2, -11.5, "eTutti Slim R2SL - knobs magneticos (opcao C): corte pelo eixo, cotas em mm. Placa principal: face de baixo em z 6,8 (P2 manda), 1,2 mm.", 1.3, INK))
    o.append("</svg>")
    open(os.path.join(OUT, "knobs_corte.svg"), "w", encoding="utf-8").write("\n".join(o))
    print("img/knobs_corte.svg")


if __name__ == "__main__":
    build()
