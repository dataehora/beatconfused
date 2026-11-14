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

lote2  checks (final DRC, board x firmware, heights).
lote3  fabrication files in fab/ (`lote3 --sem-plate` keeps the plate's files as they are).
m3b    step M3b of SPEC v2.5 on the board of commit 4b25bb1: LCSC fields of C307 / FB301 / R501,
       Altura_mm of SW403 (20 -> 1.5) and the two board-name silkscreen texts. Only those 6 blocks are
       rewritten (each in exactly one line); tracks, vias, zones and footprint positions are checked
       identical by uuid. Then run `lote3 --sem-plate`.

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


# ====================================================================== lot 2: checks
POCKET_KEYS = os.path.join(REPO, "etutti", "hardware", "pocket", "pcb", "build", "pocket_keys.csv")
PINOS = os.path.join(REPO, "etutti", "hardware", "viaggio_micromod", "pcb", "PINOS.md")
FIRST_NOTE = [57, 55, 56, 57]     # Pocket (same keyboard): rows 1..4
FIRST_COL = [1, 0, 1, 1]
GRID_COLS = 8
# 74HC4067: channel -> pin (schematic.py chan_pin)
CHAN_PIN = {0: "9", 1: "8", 2: "7", 3: "6", 4: "5", 5: "4", 6: "3", 7: "2", 8: "23", 9: "22", 10: "21",
            11: "20", 12: "19", 13: "18", 14: "17", 15: "16"}
PIN_CHAN = {v: k for k, v in CHAN_PIN.items()}
# multiplexer index as in the Pocket firmware: 0 = COM on pin 14 (A0), 1 = COM on pin 15 (A1)
MUX_OF_COM = {"MUX_R_COM": 0, "MUX_L_COM": 1}
# J101 pad -> net the contract (PINOS.md) puts on it
J101_CONTRACT = {"19": "MUX_S0", "17": "MUX_S1", "47": "MUX_S2", "32": "MUX_S3", "10": "SENS_EN",
                 "34": "MUX_R_COM", "38": "MUX_L_COM"}
MUX_CTRL = {"10": "MUX_S0", "11": "MUX_S1", "14": "MUX_S2", "13": "MUX_S3", "15": "GND", "12": "GND", "24": "+3V3"}
# gates of T3 (pad: net)
GATES = {"U603": {"2": "MUX_S3", "4": "NS3"}, "U604": {"1": "NS3", "2": "SENS_EN", "4": "EN_A"},
         "U605": {"1": "MUX_S3", "2": "SENS_EN", "4": "EN_B"}}


def key_check(b):
    """Board x firmware: every TMAG5253 (U7nn under SWnn) reaches one multiplexer channel, in the
    channel half its EN group is switched on with (S3 = 0: EN_A, channels 0-7; S3 = 1: EN_B, 8-15).
    Returns (rows, table, problems)."""
    import csv
    keys = list(csv.DictReader(open(POCKET_KEYS, encoding="utf-8")))
    bad = []

    def pad_net(fp, n):
        return [p.GetNetname() for p in fp.Pads() if p.GetNumber() == n][0]
    j101 = b.FindFootprintByReference("J101")
    for pad, net in J101_CONTRACT.items():
        if pad_net(j101, pad) != net:
            bad.append("J101.%s: %s, contrato %s" % (pad, pad_net(j101, pad), net))
    muxes = {}
    for ref in ("U601", "U602"):
        fp = b.FindFootprintByReference(ref)
        com = pad_net(fp, "1")
        muxes[ref] = (fp, MUX_OF_COM[com])
        for pad, net in MUX_CTRL.items():
            if pad_net(fp, pad) != net:
                bad.append("%s.%s: %s, esperado %s" % (ref, pad, pad_net(fp, pad), net))
    for ref, pads in GATES.items():
        fp = b.FindFootprintByReference(ref)
        for pad, net in pads.items():
            if pad_net(fp, pad) != net:
                bad.append("%s.%s: %s, esperado %s" % (ref, pad, pad_net(fp, pad), net))
    table = [[-1] * GRID_COLS for _ in range(4)]
    rows = []
    for k in keys:
        n = int(k["switch"][2:])
        sw, se = b.FindFootprintByReference("SW%d" % n), b.FindFootprintByReference("U7%02d" % n)
        row, col, midi = int(k["row"]), int(k["col"]), int(k["midi"])
        dx = TOMM(se.GetPosition().x - sw.GetPosition().x)
        dy = TOMM(se.GetPosition().y - sw.GetPosition().y)
        out, en_net = pad_net(se, "4"), pad_net(se, "3")
        found = [(ref, m, PIN_CHAN[p.GetNumber()]) for ref, (fp, m) in muxes.items() for p in fp.Pads()
                 if p.GetNetname() == out and p.GetNumber() in PIN_CHAN]
        note = FIRST_NOTE[row - 1] + 3 * (col - FIRST_COL[row - 1])
        ok = len(found) == 1 and abs(dx) < 0.01 and abs(dy) < 0.01 and note == midi
        ok = ok and en_net == ("EN_A" if found[0][2] < 8 else "EN_B") and se.IsFlipped()
        if ok:
            table[row - 1][col] = found[0][1] * 16 + found[0][2]
        else:
            bad.append("SW%d/U7%02d: mux %s, EN %s, desvio (%.3f; %.3f), nota %d/%d" % (n, n, found, en_net, dx, dy,
                                                                                    note, midi))
        rows.append({"tecla": "SW%d" % n, "sensor": "U7%02d" % n, "fileira": row, "coluna": col, "midi": midi,
                     "nota": k["note"], "saida": out, "mux": found[0][0] if found else None,
                     "canal": found[0][2] if found else None, "en": en_net,
                     "rotacao_sensor": se.GetOrientationDegrees(),
                     "key_input": table[row - 1][col],
                     "pocket_v03": (0 if k["mux"] == "U51" else 1) * 16 + int(k["mux_channel"])})
    return rows, table, bad


def key_block(table):
    body = ",\n".join("  {%s}" % ", ".join("%3d" % v for v in r) for r in table)
    return "```c\nconst int8_t VIAGGIO_KEY_INPUT[4][8] = {\n" + body + ",\n};\n```"


def write_pinos(table, n_ok):
    t = open(PINOS, encoding="utf-8").read()
    a, e = "<!-- BEGIN KEY_INPUT (viaggio_j1/m3.py) -->", "<!-- END KEY_INPUT -->"
    blk = a + "\n" + key_block(table) + "\n\nConferido pelo `viaggio_j1/m3.py lote2` na placa J1: %d/28.\n" % n_ok + e
    if a not in t:
        raise SystemExit("PINOS.md sem o marcador do KEY_INPUT")
    t = t[:t.index(a)] + blk + t[t.index(e) + len(e):]
    open(PINOS, "w", encoding="utf-8", newline="").write(t)


HEIGHT_FIX = {"SW403": 1.5}      # TS-1187A: Altura_mm 20 came from the "SW40" (encoder) row of build_board.py


def heights(b):
    side = {"cima": [], "baixo": []}
    for fp in b.GetFootprints():
        f = fp.GetField("Altura_mm")
        h = HEIGHT_FIX.get(fp.GetReference(), float(f.GetText()) if f and f.GetText() else 0.0)
        bb = fp.GetBoundingBox(False)
        side["baixo" if fp.IsFlipped() else "cima"].append(
            {"ref": fp.GetReference(), "altura_mm": h,
             "codigo": fp.GetFieldText("Codigo") if fp.HasField("Codigo") else "",
             "x": round(TOMM(fp.GetPosition().x), 2), "y": round(TOMM(fp.GetPosition().y), 2),
             "caixa": [round(TOMM(bb.GetLeft()), 2), round(TOMM(bb.GetTop()), 2),
                       round(TOMM(bb.GetRight()), 2), round(TOMM(bb.GetBottom()), 2)]})
    for k in side:
        side[k].sort(key=lambda r: -r["altura_mm"])
    return side


def thin_tracks(b):
    """Pin-entry neckings: Corrente tracks under 0.8, USB under 0.22, other nets under 0.2, by net."""
    out = {}
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        net, w = t.GetNetname(), round(TOMM(t.GetWidth()), 3)
        k = rr.klass(net)
        lim = 0.8 if k == "Corrente" else (0.22 if k == "USB" else 0.2)
        if w < lim - 1e-6:
            L = TOMM(t.GetLength())
            r = out.setdefault(net, {"classe": k, "trilhas": 0, "comprimento_mm": 0.0, "larguras": set(),
                                     "mais_longa_mm": 0.0})
            r["trilhas"] += 1
            r["comprimento_mm"] += L
            r["larguras"].add(w)
            r["mais_longa_mm"] = max(r["mais_longa_mm"], L)
    for r in out.values():
        r["comprimento_mm"] = round(r["comprimento_mm"], 2)
        r["mais_longa_mm"] = round(r["mais_longa_mm"], 2)
        r["larguras"] = sorted(r["larguras"])
    return out


def lote2():
    m = load_manifest()
    original = open(BOARD, encoding="utf-8", newline="").read()
    b = pcbnew.LoadBoard(BOARD)
    d0 = json.load(open(os.path.join(BUILD, "drc_m3_lote1.json"), encoding="utf-8"))
    ids = {it["uuid"] for v in d0["violations"] if v["type"] == "track_width" for it in v["items"]}
    g = en.Geo(b)
    widened, kept = [], []
    for t in list(b.GetTracks()):
        u = t.m_Uuid.AsString()
        if u not in ids:
            continue
        rec = {"rede": t.GetNetname(), "camada": rr.LNAME[t.GetLayer()], "largura": round(TOMM(t.GetWidth()), 3),
               "de": [round(TOMM(t.GetStart().x), 4), round(TOMM(t.GetStart().y), 4)],
               "ate": [round(TOMM(t.GetEnd().x), 4), round(TOMM(t.GetEnd().y), 4)], "uuid": u}
        g.chk.skip = {u}
        g.chk.rebuild()
        ok = g.chk.track_ok(t.GetStart(), t.GetEnd(), 0.15, t.GetLayer(), t.GetNetname())
        rec["por_que"] = "" if ok else g.chk.why
        g.chk.skip = None
        if ok:
            t.SetWidth(MM(0.15))
            widened.append(rec)
        else:
            kept.append(rec)
    g.chk.rebuild()
    en.refill(b)
    uu = {r["uuid"] for r in widened}
    sv = save(b, original, uu, uu, set(), [])
    d, v, u, p = drc("final")
    print("DRC final:", v, "nao roteadas", u, "paridade", p, sv)
    b = pcbnew.LoadBoard(BOARD)
    rows, table, bad = key_check(b)
    n_ok = sum(1 for r in rows if r["key_input"] >= 0)
    print("placa x firmware: %d/28, %d problemas" % (n_ok, len(bad)))
    for x in bad:
        print("  ", x)
    if not bad:
        write_pinos(table, n_ok)
    m["lote2"] = {"drc": {"violacoes": v, "nao_roteadas": u, "paridade": p}, "gravacao": sv,
                  "track_width_alargadas": widened, "track_width_mantidas": kept,
                  "afinacoes": thin_tracks(b), "teclas": rows, "key_input": table, "problemas": bad,
                  "alturas": heights(b)}
    write_manifest(m)
    hard = {k: n for k, n in v.items() if k != "track_width"}
    if bad or u or p or hard or v.get("track_width", 0) != len(kept):
        raise SystemExit("lote 2: falhou (%s, %d problemas de teclas)" % (v, len(bad)))


# ====================================================================== lot 3: fabrication (nothing is ordered)
import csv as _csv          # noqa: E402
import re as _re            # noqa: E402
import zipfile as _zip      # noqa: E402

FAB = os.path.join(HERE, "fab")
PLATE_PCB = os.path.join(HERE, "kicad", "viaggio_j1_plate.kicad_pcb")
POCKET_PLATE_DXF = os.path.join(REPO, "etutti", "hardware", "pocket", "case", "out", "plate.dxf")
GERBER_LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
# LCSC codes the schematic lacked at M3. Since M3b (SPEC v2.5) the schematic and the board carry them
# (FB301 C1002, R501 C4131, C307 C162182), so nothing is patched here any more.
LCSC_FIX = {}
# order parameters of the board, recorded with the fab files (nothing is ordered)
ORDER = {"camadas": 4, "espessura_mm": 1.2, "empilhamento": "JLC04121H-7628", "acabamento": "ENIG",
         "acabamento_decidido": "SPEC v2.5 (decisao do J)", "mascara": "verde, vias tampadas (tented)",
         "vias_mm": "0,5 / furo 0,3", "trilha_minima_mm": 0.12, "folga_minima_mm": 0.1}
# parts JLC does not place (fitted at home or no part at all)
NOT_ASSEMBLED = ("Gateron", "MountingHole", "TestPoint", "SolderWire")
# rotation offsets of JLC's part models against KiCad's library (the table of the kicad-jlcpcb-tools
# plugin, by footprint name); bottom side: angle mirrored (180 - a) first. (conferir na previa da JLC)
ROT_FIX = [(r"^SOT-23", 180), (r"^TSSOP-", 270), (r"^VQFN-", 270), (r"^QFN-", 270), (r"^TQFN-", 270),
           (r"^Texas_DRC", 270), (r"^Texas_X2SON", 270)]


def kcli(*args):
    subprocess.run([rr.KICAD_CLI] + list(args), check=True, capture_output=True)


def zipdir(d, z):
    with _zip.ZipFile(z, "w", _zip.ZIP_DEFLATED) as zf:
        for n in sorted(os.listdir(d)):
            zf.write(os.path.join(d, n), n)


def gerbers(board, name, layers):
    d = os.path.join(BUILD, "gerbers_" + name)
    os.makedirs(d, exist_ok=True)
    for n in os.listdir(d):
        os.remove(os.path.join(d, n))
    kcli("pcb", "export", "gerbers", "--output", d + os.sep, "--layers", layers, board)
    kcli("pcb", "export", "drill", "--output", d + os.sep, "--format", "excellon", "--excellon-separate-th",
         "--excellon-units", "mm", board)
    z = os.path.join(FAB, name + "_gerbers.zip")
    zipdir(d, z)
    return z, sorted(os.listdir(d))


def jlc_rotation(fp):
    a = fp.GetOrientationDegrees()
    if fp.IsFlipped():
        a = 180.0 - a
    name = str(fp.GetFPID().GetLibItemName())
    corr = next((c for rx, c in ROT_FIX if _re.search(rx, name)), 0)
    return (a + corr) % 360, corr


def bom_cpl(b):
    groups, cpl, out = {}, [], []
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        name = str(fp.GetFPID().GetLibItemName())
        ref = fp.GetReference()
        mont = fp.GetFieldText("Montagem") if fp.HasField("Montagem") else ""
        if any(k in name for k in NOT_ASSEMBLED) or mont.startswith("sem peca"):
            out.append((ref, fp.GetValue(), mont or "fora da montagem"))
            continue
        lcsc = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
        note = ""
        if ref in LCSC_FIX:
            lcsc, note = LCSC_FIX[ref]
        gs = "Global Sourcing" in mont
        comment = fp.GetValue() + (" [GLOBAL SOURCING JLCPCB, sem codigo LCSC]" if gs else "")
        if not lcsc and not gs:
            raise SystemExit("BOM: %s (%s) sem codigo LCSC e fora do Global Sourcing" % (ref, fp.GetValue()))
        key = (comment, name, lcsc)
        groups.setdefault(key, []).append(ref)
        rot, corr = jlc_rotation(fp)
        p = fp.GetPosition()
        cpl.append([ref, fp.GetValue(), name, "%.4fmm" % TOMM(p.x), "%.4fmm" % -TOMM(p.y), "%g" % rot,
                    "Bottom" if fp.IsFlipped() else "Top", corr])
    bom = os.path.join(FAB, "viaggio_j1_bom.csv")
    with open(bom, "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (c, n, l), refs in sorted(groups.items(), key=lambda kv: kv[0][1]):
            w.writerow([c, ",".join(sorted(refs, key=lambda r: (r.rstrip("0123456789"), int(_re.sub(r"\D", "", r) or 0)))),
                        n, l])
    path = os.path.join(FAB, "viaggio_j1_cpl.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        for r in cpl:
            w.writerow(r[:7])
    fora = os.path.join(FAB, "viaggio_j1_fora_da_montagem.csv")
    with open(fora, "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["referencia", "peca", "por que"])
        for r in out:
            w.writerow(r)
        w.writerow(["MOD1", "SparkFun MicroMod Teensy (DEV-16402)", "em casa: encaixar no J101"])
        w.writerow(["SCR1", "parafuso M2.5 x 3 (kit SparkFun)", "em casa: prende o modulo no H101"])
        w.writerow(["PLATE", "plate FR-4 1,6 mm", "pedido a parte (viaggio_j1_plate_gerbers.zip)"])
        w.writerow(["A2", "alto-falante fino 36 mm", "em casa: fios soldados no J501"])
        w.writerow(["BAT", "LiPo 1S ~1000 mAh com NTC (3 fios)", "em casa: no J202"])
    nrot = Counter((r[7], r[6]) for r in cpl)
    return {"bom_linhas": len(groups), "pecas_montadas": len(cpl),
            "cima": sum(1 for r in cpl if r[6] == "Top"), "baixo": sum(1 for r in cpl if r[6] == "Bottom"),
            "correcoes_rotacao": {"%s %s" % k: n for k, n in nrot.items()},
            "fora": [r[0] for r in out]}


def read_dxf(path):
    L = [l.strip() for l in open(path, encoding="utf-8", errors="replace").read().splitlines()]
    ents, cur, insec = [], None, False
    for c, v in zip(L[0::2], L[1::2]):
        if c == "2" and v == "ENTITIES":
            insec = True
        if c == "0":
            if cur:
                ents.append(cur)
                cur = None
            if v == "ENDSEC":
                insec = False
            if insec and v in ("LINE", "ARC"):
                cur = {"t": v}
            continue
        if cur is not None and c in ("10", "20", "11", "21", "40", "50", "51"):
            cur[c] = float(v)
    return ents


def build_plate(b):
    """The Pocket's switch plate (pocket/case/out/plate.dxf, y mirrored: y = 100 - y_dxf, which puts
    its cutouts on the J1 keys) with the Pocket's screw notches closed by their chords, the 28
    14 mm cutouts at the J1 switches and 2.2 mm holes at the J1 M2 holes inside it."""
    ents = read_dxf(POCKET_PLATE_DXF)
    keys = [(TOMM(f.GetPosition().x), TOMM(f.GetPosition().y)) for f in b.GetFootprints()
            if "Gateron" in str(f.GetFPID().GetLibItemName())]
    holes = [(f.GetReference(), TOMM(f.GetPosition().x), TOMM(f.GetPosition().y)) for f in b.GetFootprints()
             if "MountingHole" in str(f.GetFPID().GetLibItemName())]
    pb = pcbnew.BOARD()
    pb.GetDesignSettings().SetBoardThickness(MM(1.6))

    def seg(a, e, layer=pcbnew.Edge_Cuts):
        s = pcbnew.PCB_SHAPE(pb)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(MM(a[0]), MM(a[1])))
        s.SetEnd(V(MM(e[0]), MM(e[1])))
        s.SetLayer(layer)
        s.SetWidth(MM(0.1))
        pb.Add(s)

    def arc(cx, cy, r, a0, a1):
        s = pcbnew.PCB_SHAPE(pb)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        P = lambda a: V(MM(cx + r * math.cos(math.radians(a))), MM(cy + r * math.sin(math.radians(a))))
        s.SetArcGeometry(P(a0), P((a0 + a1) / 2), P(a1))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        pb.Add(s)

    flip = lambda x, y: (x, 100.0 - y)
    n_seg = n_arc = n_chord = 0
    for e in ents:
        if e["t"] == "LINE":
            if abs(math.hypot(e["11"] - e["10"], e["21"] - e["20"]) - 14.0) < 0.01:
                continue                      # Pocket cutouts: redrawn from the J1 switches
            seg(flip(e["10"], e["20"]), flip(e["11"], e["21"]))
            n_seg += 1
        else:
            cx, cy, r, a0, a1 = e["10"], e["20"], e["40"], e["50"], e["51"]
            if a1 < a0:
                a1 += 360
            P = lambda a: flip(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            if abs(r - 3.5) < 0.01:           # the Pocket's screw notches: closed by their chord
                seg(P(a0), P(a1))
                n_chord += 1
                continue
            # mirrored arc: centre flipped, angles negated and swapped
            fc = flip(cx, cy)
            arc(fc[0], fc[1], r, -a1, -a0)
            n_arc += 1
    h = 7.0
    for x, y in keys:
        pts = [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h), (x - h, y - h)]
        for a, e in zip(pts, pts[1:]):
            seg(a, e)
    outl = pcbnew.SHAPE_POLY_SET()
    pb.GetBoardPolygonOutlines(outl, False)
    lib = KICAD_FP + "/MountingHole.pretty"
    inside = []
    for r, x, y in holes:
        if outl.OutlineCount() and outl.Contains(V(MM(x), MM(y))):
            m = pcbnew.FootprintLoad(lib, "MountingHole_2.2mm_M2")
            m.SetReference(r)
            m.Reference().SetVisible(False)
            m.SetPosition(V(MM(x), MM(y)))
            pb.Add(m)
            inside.append(r)
    t = pcbnew.PCB_TEXT(pb)
    t.SetText("eTutti Viaggio J1 - plate FR-4 1,6 mm (M3)")
    t.SetPosition(V(MM(160.0), MM(88.5)))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(V(MM(1.2), MM(1.2)))
    pb.Add(t)
    pcbnew.SaveBoard(PLATE_PCB, pb)
    d = os.path.join(BUILD, "drc_m3_plate.json")
    kcli("pcb", "drc", "--format", "json", "--severity-error", "-o", d, PLATE_PCB)
    dj = json.load(open(d, encoding="utf-8"))
    return {"linhas": n_seg, "arcos": n_arc, "entalhes_fechados": n_chord, "recortes": len(keys),
            "furos_m2": inside, "drc_erros": len(dj["violations"]), "contorno_ok": outl.OutlineCount()}


def renders(board, base, sides=("top", "bottom")):
    out = []
    for s in sides:
        p = os.path.join(FAB, "%s_%s.png" % (base, s))
        kcli("pcb", "render", "--side", s, "--width", "2400", "--height", "1000", "--quality", "high", "--zoom", "2.1",
             "--output", p, board)
        out.append(os.path.basename(p))
    return out


def lote3(plate=True):
    """plate=False (M3b: `lote3 --sem-plate`) keeps the plate's files in fab/ as they are."""
    os.makedirs(FAB, exist_ok=True)
    m = load_manifest()
    b = pcbnew.LoadBoard(BOARD)
    ds = b.GetDesignSettings()
    rec = {"espessura_mm": round(TOMM(ds.GetBoardThickness()), 2), "camadas_cobre": b.GetCopperLayerCount()}
    if rec["espessura_mm"] != ORDER["espessura_mm"] or rec["camadas_cobre"] != ORDER["camadas"]:
        raise SystemExit("placa: %s, pedido: %s" % (rec, ORDER))
    rec["pedido"] = dict(ORDER)
    z, files = gerbers(BOARD, "viaggio_j1", GERBER_LAYERS)
    rec["gerbers"] = {"zip": os.path.basename(z), "arquivos": files}
    rec.update(bom_cpl(b))
    if plate:
        rec["plate"] = build_plate(b)
        zp, pf = gerbers(PLATE_PCB, "viaggio_j1_plate", "F.Cu,B.Cu,F.Silkscreen,F.Mask,B.Mask,Edge.Cuts")
        rec["plate"]["zip"] = os.path.basename(zp)
        rec["imagens"] = renders(BOARD, "viaggio_j1") + renders(PLATE_PCB, "viaggio_j1_plate", ("top",))
    else:
        rec["plate"] = dict(m.get("lote3", {}).get("plate", {}), refeito=False)
        rec["imagens"] = renders(BOARD, "viaggio_j1") + ["viaggio_j1_plate_top.png (do M3, nao refeita)"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    rec["vias"] = {"total": len(vias), "diametros": sorted({round(TOMM(v.GetWidth(pcbnew.F_Cu)), 3) for v in vias}),
                   "furos": sorted({round(TOMM(v.GetDrillValue()), 3) for v in vias})}
    widths = sorted({round(TOMM(t.GetWidth()), 3) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"})
    rec["trilha_minima_mm"] = widths[0]
    m["lote3" if plate else "m3b_fab"] = rec
    write_manifest(m)
    print(json.dumps(rec, indent=1, ensure_ascii=False)[:3000])


# ====================================================================== M3b (SPEC v2.5): codes, silkscreen, height
# Only footprint fields and two silkscreen texts change: no track, via, zone, position or rotation.
M3B_LCSC = {"C307": "C162182", "FB301": "C1002", "R501": "C4131"}
M3B_HEIGHT = {"SW403": ("20", "1.5")}
M3B_TEXT = {"987abc19-c76d-45dc-b04a-e14d4ec2f892": ("eTutti Viaggio MicroMod - placa principal - SPEC v2.3 passo M2",
                                                      "F.Silkscreen"),
            "947ad9bc-a10a-4ca2-805c-82892b2b0dd6": ("eTutti Viaggio MicroMod - verso: modulo, chips, sensores TMAG5253",
                                                      "B.Silkscreen")}
M3B_NEW_TEXT = "eTutti Viaggio MicroMod · J1 · SPEC v2.5"
M3B_BASE = "4b25bb1"


def m3b():
    kind, buid = rr.kind, rr.block_uuid
    original = open(BOARD, encoding="utf-8", newline="").read()
    base = subprocess.run(["git", "show", "%s:%s" % (M3B_BASE, BOARD_REL)], cwd=REPO, check=True,
                          capture_output=True).stdout.decode("utf-8")
    if base.replace("\r\n", "\n") != original.replace("\r\n", "\n"):
        raise SystemExit("m3b: a placa nao e a do commit %s" % M3B_BASE)
    _d0, v0, u0, p0 = drc("m3b_base")
    print("base:", v0, "nao roteadas", u0, "paridade", p0)
    b = pcbnew.LoadBoard(BOARD)
    changed, log = {}, []
    for ref, code in M3B_LCSC.items():
        fp = b.FindFootprintByReference(ref)
        old = fp.GetFieldText("LCSC")
        if old:
            raise SystemExit("%s: LCSC ja e %s" % (ref, old))
        fp.GetField("LCSC").SetText(code)
        changed[fp.m_Uuid.AsString()] = ref
        log.append({"ref": ref, "campo": "LCSC", "de": old, "para": code})
    for ref, (old, new) in M3B_HEIGHT.items():
        fp = b.FindFootprintByReference(ref)
        if fp.GetFieldText("Altura_mm") != old:
            raise SystemExit("%s: Altura_mm %s, esperado %s" % (ref, fp.GetFieldText("Altura_mm"), old))
        fp.GetField("Altura_mm").SetText(new)
        changed[fp.m_Uuid.AsString()] = ref
        log.append({"ref": ref, "campo": "Altura_mm", "de": old, "para": new})
    texts = {}
    for d in b.GetDrawings():
        u = d.m_Uuid.AsString()
        if u in M3B_TEXT:
            old, layer = M3B_TEXT[u]
            if d.GetClass() != "PCB_TEXT" or d.GetText() != old or b.GetLayerName(d.GetLayer()) != layer:
                raise SystemExit("texto %s: %r em %s" % (u, d.GetText(), b.GetLayerName(d.GetLayer())))
            d.SetText(M3B_NEW_TEXT)
            texts[u] = layer
            log.append({"texto": layer, "uuid": u, "de": old, "para": M3B_NEW_TEXT})
    if len(texts) != 2:
        raise SystemExit("m3b: %d textos achados" % len(texts))
    tmp = os.path.join(BUILD, "m3b_tmp.kicad_pcb")
    pcbnew.SaveBoard(tmp, b)
    for f in os.listdir(BUILD):
        if f.startswith("m3b_tmp") and not f.endswith(".kicad_pcb"):
            os.remove(os.path.join(BUILD, f))
    new = open(tmp, encoding="utf-8", newline="").read()
    os.remove(tmp)
    if "\r\n" in original and "\r\n" not in new:
        new = new.replace("\n", "\r\n")
    _h, b_new, _t = rr.top_blocks(new)
    h_old, b_old, t_old = rr.top_blocks(original)
    want = set(changed) | set(texts)
    repl = {buid(x): x for x in b_new if kind(x) in ("footprint", "gr_text") and buid(x) in want}
    if set(repl) != want:
        raise SystemExit("m3b: blocos achados na copia %d/%d" % (len(repl), len(want)))
    out, diffs = [], {}
    for blk in b_old:
        u = buid(blk) if kind(blk) in ("footprint", "gr_text") else None
        if u in want:
            # the replacement may differ from the original only in the lines carrying the new values
            lo, ln = blk.splitlines(), repl[u].splitlines()
            if len(lo) != len(ln):
                raise SystemExit("m3b: %s mudou de tamanho (%d -> %d linhas)" % (u, len(lo), len(ln)))
            dl = [(a.strip(), c.strip()) for a, c in zip(lo, ln) if a != c]
            diffs[changed.get(u, texts.get(u))] = dl
            out.append(repl[u])
        else:
            out.append(blk)
    for who, dl in diffs.items():
        if len(dl) != 1:
            raise SystemExit("m3b: %s mudou em %d linhas: %s" % (who, len(dl), dl))
    text = h_old + "".join(out) + t_old
    _h2, b_chk, _t2 = rr.top_blocks(text)
    same = [x for x in b_chk if not ((kind(x) in ("footprint", "gr_text")) and buid(x) in want)]
    same_old = [x for x in b_old if not ((kind(x) in ("footprint", "gr_text")) and buid(x) in want)]
    if same != same_old or len(b_chk) != len(b_old):
        raise SystemExit("m3b: blocos nao mudados diferem")
    # tracks, vias, zones and footprint positions compared by uuid with the base board
    def geo(blocks):
        g = {}
        for x in blocks:
            k = kind(x)
            if k in ("segment", "via", "arc", "zone"):
                g[buid(x)] = x
            elif k == "footprint":
                at = _re.search(r"\n\t\t\(at [^)]*\)", x)
                lay = _re.search(r'\n\t\t\(layer "[^"]*"\)', x)
                pads = _re.findall(r'\(pad "[^"]*" [^\n]*\n\t+\(at [^)]*\)', x)
                g[buid(x)] = (at.group(0) if at else None, lay.group(0) if lay else None, tuple(pads))
        return g
    g_old, g_new = geo(b_old), geo(b_chk)
    if g_old != g_new:
        bad = [u for u in g_old if g_old[u] != g_new.get(u)]
        raise SystemExit("m3b: cobre ou posicao mudou: %s" % bad[:5])
    open(BOARD, "w", encoding="utf-8", newline="").write(text)
    d, v, u, p = drc("m3b")
    print("M3b:", v, "nao roteadas", u, "paridade", p)
    hard = {k: n for k, n in v.items() if k != "track_width"}
    m = load_manifest()
    m["m3b"] = {"base_commit": M3B_BASE, "drc_base": {"violacoes": v0, "nao_roteadas": u0, "paridade": p0},
                "drc": {"violacoes": v, "nao_roteadas": u, "paridade": p}, "mudancas": log,
                "linhas_mudadas": {k: [list(x) for x in dl] for k, dl in diffs.items()},
                "gravacao": {"blocos_trocados": len(want), "blocos_identicos": len(same_old),
                             "trilhas_vias_zonas_posicoes_iguais": len(g_old)}}
    write_manifest(m)
    if hard or u or p or v.get("track_width", 0) != 3:
        raise SystemExit("m3b: DRC falhou (%s, %d nao roteadas, paridade %d)" % (v, u, p))


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
    elif arg == "lote2":
        lote2()
    elif arg == "lote3":
        lote3(plate="--sem-plate" not in sys.argv)
    elif arg == "m3b":
        m3b()
    else:
        raise SystemExit(__doc__)
