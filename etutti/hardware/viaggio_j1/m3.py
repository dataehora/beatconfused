"""eTutti Viaggio J1 -- step M3 of SPEC v2.4 (checks and fabrication) on J's routed board.

Run with KiCad 10's python, from anywhere:
    "C:/Program Files/KiCad/10.0/bin/python.exe" etutti/hardware/viaggio_j1/m3.py lote1

lote1  the adjustments of SPEC v2.4 (lot 1), on the board of BASE_COMMIT (main after PR #126 and
       the SPEC v2.4 commit):
   1. C202 / C206: the two 10 uF VSYS caps swap places, so each reference sits where its schematic
      function is (C202 = E3, charger output; C206 = E4, TPS63001 input). Same part, same nets.
   2. C210 (new, 10 uF 0603, E3): VSYS cap at the charger's OUT pins 10/11. No room on the back
      (searched: only with D205, its vias and four signals moved), so it is on the top side, over
      the pins: VSYS pad on the VSYS track, GND pad 0.85 mm from U202's thermal vias.
   3. C207 next to C208 (authorised ~7 mm): +3V3 pad joined to C208.1, GND pad in the B.Cu pour
      with its own vias; its old vias go, and the GND stitching vias under the new spot.
   4. C304: the GND via leaves the pad. J's +3V3 loop C305.1-C304.1 is redone (same net, 0.2) and
      C304 goes 0.55 mm into the room it leaves (turned to lie flat): only there its GND pad has a
      via of its own (the In2 line VOL_B, HP_L on F.Cu and I2S_BCLK on B.Cu close every other side).
   5. zones refilled, DRC: no new violation, 0 unconnected, parity 0.

Same writing method as energia.py (PR #120/#123/#126): the board is saved by pcbnew to a
temporary file and only the new tracks / vias / footprint, the removed tracks / vias, the changed
footprints and the refilled zones are spliced into the original text; every other block is
checked identical. The record goes to m3.json.
"""
import json
import math
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew                 # noqa: E402
import rota_restante as rr    # noqa: E402
import energia as en          # noqa: E402

BOARD = rr.BOARD
BUILD = rr.BUILD
REPO = en.REPO
MANIFEST = os.path.join(HERE, "m3.json")
BOARD_REL = en.BOARD_REL
BASE_COMMIT = "93aa0e3"
MM, TOMM, V = rr.MM, rr.TOMM, rr.V
FC, BC = pcbnew.F_Cu, pcbnew.B_Cu
KICAD_FP = "C:/Program Files/KiCad/10.0/share/kicad/footprints"
sys.path.insert(0, os.path.join(REPO, "etutti", "hardware", "viaggio_micromod", "pcb"))


def uid(*key):
    import uuid
    ns = uuid.UUID("3b8e6f0c-2d4a-4f61-8c7e-5a9d1e2f4b22")      # schematic.py's namespace
    return str(uuid.uuid5(ns, "/".join(str(k) for k in key)))


# ------------------------------------------------------------------ lot 1 geometry (mm, KiCad frame)
C210_AT = (60.76, 8.60, 270)           # top side; pad 1 (VSYS) (60.762; 7.825), pad 2 (GND) (60.762; 9.375)
C210_GND_VIA = (61.60, 9.40)           # U202 thermal via (GND, all layers)
C207_AT = (73.25, 5.70, 0)             # pad 1 (+3V3) (72.30; 5.70), pad 2 (GND) (74.20; 5.70)
C207_OLD_VIAS = [(66.933, 14.773), (67.15, 13.9), (63.867, 14.773), (63.7, 13.9)]
C207_STITCH = [(73.25, 5.75), (74.75, 5.75)]          # GND stitching vias under the new spot
C304_AT = (20.45, 35.89, 180)          # 0.55 mm into the loop's room; pad 1 (+3V3) east, pad 2 (GND) west
C304_GND_VIA_OLD = (20.0, 35.0)         # the via inside the old GND pad
# J's +3V3 loop C305.1 - C304.1: the pieces west of x 21.0 go
C304_LOOP = [((21.181, 34.954), (20.631, 35.503)), ((20.631, 35.503), (20.631, 36.457)),
             ((20.631, 36.457), (21.181, 37.006)), ((20.05, 35.93), (20.631, 35.93))]


def near(q, p, tol=0.01):
    return abs(TOMM(q.x) - p[0]) < tol and abs(TOMM(q.y) - p[1]) < tol


def find_via(b, net, p):
    v = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == net and near(t.GetPosition(), p)]
    if len(v) != 1:
        raise SystemExit("via %s em %s: %d achadas" % (net, p, len(v)))
    return v[0]


def find_track(b, net, a, e, layer=None):
    out = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net or (layer is not None and t.GetLayer() != layer):
            continue
        if (near(t.GetStart(), a) and near(t.GetEnd(), e)) or (near(t.GetStart(), e) and near(t.GetEnd(), a)):
            out.append(t)
    if len(out) != 1:
        raise SystemExit("trilha %s %s-%s: %d achadas" % (net, a, e, len(out)))
    return out[0]


def tracks_at(b, net, p):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net
            and (near(t.GetStart(), p) or near(t.GetEnd(), p))]


class Lot1:
    def __init__(self, b):
        self.b = b
        self.g = None           # built after the removals (the checker keeps the shapes of what it saw)
        self.keep = []          # removed items stay referenced
        self.drop = []          # uuids of removed tracks / vias
        self.dropped = []       # what they were
        self.changed = {}       # footprint uuid -> record
        self.new_fps = []

    def remove(self, t, why):
        u = t.m_Uuid.AsString()
        if t.GetClass() == "PCB_VIA":
            rec = {"via": t.GetNetname(), "em": [round(TOMM(t.GetPosition().x), 3), round(TOMM(t.GetPosition().y), 3)]}
        else:
            rec = {"trilha": t.GetNetname(), "camada": rr.LNAME[t.GetLayer()], "largura": round(TOMM(t.GetWidth()), 3),
                   "de": [round(TOMM(t.GetStart().x), 3), round(TOMM(t.GetStart().y), 3)],
                   "ate": [round(TOMM(t.GetEnd().x), 3), round(TOMM(t.GetEnd().y), 3)]}
        rec["por_que"] = why
        rec["uuid"] = u
        self.dropped.append(rec)
        self.drop.append(u)
        self.keep.append(t)
        self.b.Remove(t)

    def place(self, ref, x, y, rot, why):
        fp = self.b.FindFootprintByReference(ref)
        p = fp.GetPosition()
        x0, y0, r0 = TOMM(p.x), TOMM(p.y), fp.GetOrientationDegrees()
        fp.SetPosition(V(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        fp.BuildCourtyardCaches()
        self.changed[fp.m_Uuid.AsString()] = {"ref": ref, "de": [round(x0, 3), round(y0, 3), round(r0, 1)],
                                              "para": [x, y, rot], "distancia_mm": round(math.hypot(x - x0, y - y0), 2),
                                              "por_que": why}

    def via_spot(self, ref, num, net, w, rmax):
        """Nearest via position (0.025 grid) to a pad, outside it, with a straight stub that fits."""
        g = self.g
        pad = [p for p in self.b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
        c = pad.GetPosition()
        L = BC if pad.IsOnLayer(BC) else FC
        cands = []
        n = int(rmax / 0.025)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x, y = TOMM(c.x) + i * 0.025, TOMM(c.y) + j * 0.025
                r = math.hypot(x - TOMM(c.x), y - TOMM(c.y))
                if r <= rmax:
                    cands.append((r, x, y))
        cands.sort()
        for r, x, y in cands:
            P = V(MM(x), MM(y))
            if pad.GetEffectiveShape(L).Collide(pcbnew.SHAPE_CIRCLE(P, MM(rr.VIA_D / 2)), MM(0.1)):
                continue
            if g.chk.via_ok(P, net) and g.chk.track_ok(c, P, w, L, net):
                return (round(x, 3), round(y, 3))
        return None

    # 1. C202 <-> C206
    def swap_c202_c206(self):
        b = self.b
        a, c = b.FindFootprintByReference("C202"), b.FindFootprintByReference("C206")
        pa = (TOMM(a.GetPosition().x), TOMM(a.GetPosition().y), a.GetOrientationDegrees())
        pc = (TOMM(c.GetPosition().x), TOMM(c.GetPosition().y), c.GetOrientationDegrees())
        for fp in (a, c):
            nets = sorted(p.GetNetname() for p in fp.Pads())
            if nets != ["GND", "VSYS"] or fp.GetValue() != "10uF" or "C_0805" not in fp.GetFPIDAsString():
                raise SystemExit("%s nao e o 10 uF 0805 de VSYS" % fp.GetReference())
        self.place("C202", pc[0], pc[1], pc[2], "capacitor de VSYS do E3 (saida do carregador): vai para o lugar do C206")
        self.place("C206", pa[0], pa[1], pa[2], "capacitor de entrada do U204 (E4): vai para o lugar do C202")
        for ref, code in (("C202", "E3"), ("C206", "E4")):
            f = b.FindFootprintByReference(ref).GetField("Codigo")
            if f.GetText() != code:
                raise SystemExit("%s: Codigo %s, esperado %s" % (ref, f.GetText(), code))

    # 2. C210
    def add_c210(self):
        b = self.b
        fp = pcbnew.FootprintLoad(KICAD_FP + "/Capacitor_SMD.pretty", "C_0603_1608Metric")
        fp.SetParent(b)
        fp.SetFPIDAsString("Capacitor_SMD:C_0603_1608Metric")
        fp.SetReference("C210")
        fp.SetValue("10uF")
        fp.Reference().SetVisible(False)
        props = {"Codigo": "E3", "LCSC": "C19702", "Montagem": "JLC", "Datasheet": "",
                 "Description": "VSYS junto dos pinos OUT (10/11) do U202, no lado de cima (M3)", "Altura_mm": "0.95", "Cabe_sob_cartao": "sim"}
        for key, val in props.items():
            f = fp.GetField(key)
            if f is None:
                f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), key)
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
                fp.Add(f)
            f.SetText(val)
            f.SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH("/%s/%s" % (uid("sheet", "E"), uid("sym", "C210", 1))))
        fp.SetSheetname("E · Energia")
        fp.SetSheetfile("viaggio_micromod_E.kicad_sch")
        x, y, r = C210_AT
        fp.SetPosition(V(MM(x), MM(y)))
        fp.SetOrientationDegrees(r)
        nets = {"1": "VSYS", "2": "GND"}
        for p in fp.Pads():
            p.SetNet(b.FindNet(nets[p.GetNumber()]))
        b.Add(fp)
        fp.BuildCourtyardCaches()
        self.new_fps.append(fp.m_Uuid.AsString())
        pads = {p.GetNumber(): p for p in fp.Pads()}
        return {"ref": "C210", "lado": "cima (F.Cu)", "em": [x, y, r],
                "pad_VSYS": [round(TOMM(pads["1"].GetPosition().x), 3), round(TOMM(pads["1"].GetPosition().y), 3)],
                "pad_GND": [round(TOMM(pads["2"].GetPosition().x), 3), round(TOMM(pads["2"].GetPosition().y), 3)],
                "uuid": fp.m_Uuid.AsString()}

    def run(self):
        b = self.b
        rec = {}
        # 1
        self.swap_c202_c206()
        # 3: C207 out of its old spot first (its vias), then the stitching vias under the new one
        fp = b.FindFootprintByReference("C207")
        for (px, py) in C207_OLD_VIAS:
            net = "GND" if px > 65.4 else "+3V3"
            v = find_via(b, net, (px, py))
            for t in tracks_at(b, net, (px, py)):
                self.remove(t, "toco do C207 no lugar antigo")
            self.remove(v, "via do C207 no lugar antigo")
        for p in C207_STITCH:
            v = find_via(b, "GND", p)
            if tracks_at(b, "GND", p):
                raise SystemExit("via de costura em %s tem trilha" % (p,))
            self.remove(v, "via de costura de GND sob o novo lugar do C207")
        self.place("C207", *C207_AT, why="junto do C208 (autorizado, SPEC v2.4)")
        # 4: C304
        self.remove(find_via(b, "GND", C304_GND_VIA_OLD), "via de GND dentro do pad 2 do C304")
        for a, e in C304_LOOP:
            self.remove(find_track(b, "+3V3", a, e, BC), "laco de +3V3 C305.1-C304.1 (trilha do J, autorizada)")
        self.place("C304", *C304_AT, why="0,55 mm para o espaco do laco: so assim o pad de GND tem via fora dele "
                   "(VOL_B no In2, HP_L em F.Cu e I2S_BCLK em B.Cu fecham os outros lados)")
        # 2: C210
        rec["C210"] = self.add_c210()
        self.g = g = en.Geo(b)
        # pcbnew checks of the new copper (energia.Geo: exact shapes, class clearance + 0.005)
        pads = {p.GetNumber(): p for p in b.FindFootprintByReference("C210").Pads()}
        c2 = pads["2"].GetPosition()
        g.track("GND", FC, [(TOMM(c2.x), TOMM(c2.y)), C210_GND_VIA], 0.3, "C210.2 -> via termica do U202 (GND)")
        # C207: +3V3 to C208.1, GND vias
        p207 = {p.GetNumber(): p for p in b.FindFootprintByReference("C207").Pads()}
        p208 = {p.GetNumber(): p for p in b.FindFootprintByReference("C208").Pads()}
        a = (TOMM(p208["1"].GetPosition().x), TOMM(p208["1"].GetPosition().y))
        e = (TOMM(p207["1"].GetPosition().x), TOMM(p207["1"].GetPosition().y))
        g.track("+3V3", BC, [a, (71.4, 6.0), e], 0.6, "C208.1 -> C207.1 (+3V3)")
        # vias outside the part's body: GND ones east of pad 2, the +3V3 one west of pad 1
        rec["C207_vias_gnd"] = g.fan("C207", "2", "GND", 2, "C207.2 -> In1 (GND)", rmin=0.9, rmax=1.8,
                                     prefer=(C207_AT[0] + 2.6, C207_AT[1]))
        rec["C207_vias_3v3"] = g.fan("C207", "1", "+3V3", 1, "C207.1 -> In2 (+3V3)", rmin=0.9, rmax=1.8,
                                     prefer=(C207_AT[0] - 2.6, C207_AT[1]))
        # C304: +3V3 pad 1 to C305.1, C305.1 down to the junction with U301's +3V3; GND via
        p304 = {p.GetNumber(): p for p in b.FindFootprintByReference("C304").Pads()}
        q1, q2 = p304["1"].GetPosition(), p304["2"].GetPosition()
        g.track("+3V3", BC, [(21.181, 34.954), (21.181, TOMM(q1.y))], 0.2, "C305.1 -> C304.1 (+3V3)")
        g.track("+3V3", BC, [(21.181, TOMM(q1.y)), (21.181, 36.859)], 0.2, "C304.1 -> juncao com o U301 (+3V3)")
        g.track("+3V3", BC, [(TOMM(q1.x), TOMM(q1.y)), (21.181, TOMM(q1.y))], 0.2, "C304.1 (centro do pad)")
        spot = self.via_spot("C304", "2", "GND", 0.2, 1.3)
        if spot is None:
            raise SystemExit("C304.2: nenhuma via de GND fora do pad")
        g.via("GND", *spot, what="C304.2 -> In1 (GND), fora do pad")
        g.track("GND", BC, [(TOMM(q2.x), TOMM(q2.y)), spot], 0.2, "C304.2 -> via de GND")
        rec["C304_via_gnd"] = list(spot)
        return rec


# ------------------------------------------------------------------ saving (energia.save + new footprints)
def save(b, original, drop_uuids, new_uuids, changed_uuids, new_fp_uuids):
    tmp = os.path.join(BUILD, "m3_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for f in os.listdir(BUILD):
        if f.startswith("m3_tmp") and not f.endswith(".kicad_pcb"):
            os.remove(os.path.join(BUILD, f))
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    if "\r\n" in original and "\r\n" not in new:
        new = new.replace("\n", "\r\n")
    _h, b_new, _t = rr.top_blocks(new)
    h_old, b_old, t_old = rr.top_blocks(original)
    kind, buid = rr.kind, rr.block_uuid
    new_items = [x for x in b_new if kind(x) in ("segment", "via") and buid(x) in new_uuids]
    if len(new_items) != len(new_uuids):
        raise SystemExit("splice: %d new items in the saved copy, expected %d" % (len(new_items), len(new_uuids)))
    zones_new = {buid(x): x for x in b_new if kind(x) == "zone"}
    fps_new = {buid(x): x for x in b_new if kind(x) == "footprint"}
    add_fps = [fps_new[u] for u in new_fp_uuids]
    last_fp = max(i for i, x in enumerate(b_old) if kind(x) == "footprint")
    out, placed, dropped, zrep, frep = [], False, 0, 0, 0
    for i, blk in enumerate(b_old):
        k = kind(blk)
        if k in ("segment", "via", "arc") and buid(blk) in drop_uuids:
            dropped += 1
            continue
        if k == "footprint" and buid(blk) in changed_uuids:
            out.append(fps_new[buid(blk)])
            frep += 1
        elif k == "zone":
            if not placed:
                out.extend(new_items)
                placed = True
            if not rr.is_rule_zone(blk):
                out.append(zones_new[buid(blk)])
                zrep += 1
            else:
                out.append(blk)
        else:
            out.append(blk)
        if i == last_fp:
            out.extend(add_fps)
    if not placed:
        raise SystemExit("splice: no zone block in the original file")
    if frep != len(changed_uuids) or dropped != len(drop_uuids):
        raise SystemExit("splice: %d/%d footprints, %d/%d removals" % (frep, len(changed_uuids), dropped, len(drop_uuids)))
    text = h_old + "".join(out) + t_old
    _h2, b_chk, _t2 = rr.top_blocks(text)

    def keep(x, olds):
        k = kind(x)
        if k in ("segment", "via", "arc") and buid(x) in (drop_uuids if olds else new_uuids):
            return False
        if k == "zone" and not rr.is_rule_zone(x):
            return False
        if k == "footprint" and (buid(x) in changed_uuids or buid(x) in new_fp_uuids):
            return False
        return True
    keep_old = [x for x in b_old if keep(x, True)]
    keep_new = [x for x in b_chk if keep(x, False)]
    if keep_old != keep_new:
        raise SystemExit("splice: unchanged blocks differ")
    open(BOARD, "w", encoding="utf-8", newline="").write(text)
    return {"removidas": dropped, "zonas_repreenchidas": zrep, "novas": len(new_items),
            "footprints_mudados": frep, "footprints_novos": len(add_fps), "blocos_identicos": len(keep_old)}


# ------------------------------------------------------------------ DRC
def drc(tag):
    out = os.path.join(BUILD, "drc_m3_%s.json" % tag)
    subprocess.run([rr.KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all",
                    "--format", "json", "-o", out, BOARD], check=True, capture_output=True)
    d = json.load(open(out, encoding="utf-8"))
    v = Counter(x["type"] for x in d["violations"])
    return d, dict(v), len(d["unconnected_items"]), len(d["schematic_parity"])


def base_text():
    raw = subprocess.run(["git", "show", "%s:%s" % (BASE_COMMIT, BOARD_REL)], cwd=REPO, check=True,
                         capture_output=True).stdout.decode("utf-8").replace("\r\n", "\n")
    cur = open(BOARD, "rb").read(200)
    return raw.replace("\n", "\r\n") if b"\r\n" in cur else raw


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST, encoding="utf-8"))
    return {}


def write_manifest(m):
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def lote1():
    os.makedirs(BUILD, exist_ok=True)
    # always from the board of BASE_COMMIT
    open(BOARD, "w", encoding="utf-8", newline="").write(base_text())
    _d0, v0, u0, p0 = drc("base")
    print("base:", v0, "nao roteadas", u0, "paridade", p0)
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    L = Lot1(b)
    rec = L.run()
    en.refill(b)
    made = L.g.made
    sv = save(b, original, set(L.drop), set(made), set(L.changed), L.new_fps)
    d, v, u, p = drc("lote1")
    print("lote 1:", v, "nao roteadas", u, "paridade", p, sv)
    bad = {k: (v0.get(k, 0), n) for k, n in v.items() if n > v0.get(k, 0)}
    m = load_manifest()
    m["lote1"] = {"base_commit": BASE_COMMIT, "drc_base": {"violacoes": v0, "nao_roteadas": u0, "paridade": p0},
                  "drc": {"violacoes": v, "nao_roteadas": u, "paridade": p}, "gravacao": sv,
                  "pecas": list(L.changed.values()), "novas": rec, "removidos": L.dropped, "feito": L.g.log}
    write_manifest(m)
    if bad or u or p:
        raise SystemExit("lote 1: piorou %s, nao roteadas %d, paridade %d" % (bad, u, p))


FOTOS_L1 = {"energia": (55.0, 3.0, 78.0, 14.0, 50.0), "c304": (17.5, 32.0, 24.0, 39.0, 100.0)}


def fotos_lote1():
    b = pcbnew.LoadBoard(BOARD)
    for nm, (x0, y0, x1, y1, S) in FOTOS_L1.items():
        for L, ln, tt in ((FC, "fcu", "F.Cu"), (BC, "bcu", "B.Cu, visto de cima"), (pcbnew.In2_Cu, "in2", "In2.Cu")):
            en.picture(b, L, os.path.join(BUILD, "m3_lote1_%s_%s.png" % (nm, ln)),
                       "Viaggio J1 M3 lote 1 - %s - %s" % (nm, tt), (), box=(x0, y0, x1, y1), S=S)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "lote1":
        lote1()
        fotos_lote1()
    else:
        raise SystemExit(__doc__)
