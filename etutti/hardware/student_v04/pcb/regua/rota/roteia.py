"""Roteamento das reguas R8 e R4 da Student V4 (R11V4). Etapas idempotentes e retomaveis.

Uso (python do KiCad, da raiz do repo):
    python roteia.py N etapa [net ...]
N = 8 ou 4. Etapas: prep | sinais | gnd | drc | tudo
O estado fica em pcb/regua/rota/estado.json (chave "R8"/"R4"). Nunca move peca.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew  # noqa: E402
from lib_rota import *  # noqa: E402,F401,F403
import lib_rota as R  # noqa: E402

V4 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
KD = os.path.join(V4, "kicad", "regua")
STATE = os.path.join(HERE, "estado.json")
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

CFG = {
    8: dict(orig="student_v04_regua8", novo="student_v04_regua8_roteada", ens=8),
    4: dict(orig="student_v04_regua", novo="student_v04_regua_roteada", ens=4),
}

# rede -> (largura preferida, largura minima, multiplicador de camada (F,B), custo de via)
PLAN = [
    ("OUT", 0.2, 0.2, (1.0, 1.35), 30.0),
    ("+3V3", 0.3, 0.2, (1.3, 1.0), 25.0),
    ("CLK", 0.2, 0.15, (1.0, 1.2), 25.0),
    ("SER", 0.2, 0.15, (1.0, 1.2), 25.0),
    ("QHP", 0.2, 0.15, (1.0, 1.2), 25.0),
    ("QHP_J", 0.2, 0.15, (1.0, 1.2), 25.0),
]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def paths(n):
    c = CFG[n]
    return (os.path.join(KD, c["orig"] + ".kicad_pcb"), os.path.join(KD, c["novo"] + ".kicad_pcb"))


def prep(n, st):
    orig, novo = paths(n)
    c = CFG[n]
    if st.get("prep") and os.path.exists(novo):
        log("prep ja feito")
        return
    for ext in (".kicad_pro", ".kicad_dru", ".kicad_prl"):
        s = os.path.join(KD, c["orig"] + ext)
        if os.path.exists(s):
            shutil.copy(s, os.path.join(KD, c["novo"] + ext))
    for suf in ("", ):
        s = os.path.join(KD, c["orig"] + ".kicad_sch")
        shutil.copy(s, os.path.join(KD, c["novo"] + ".kicad_sch"))
    b = pcbnew.LoadBoard(orig)
    ds = b.GetDesignSettings()
    b.SetCopperLayerCount(2)
    try:
        ds.GetStackupDescriptor().BuildDefaultStackupList(ds, 2)
    except Exception as e:  # noqa
        log("stackup padrao nao reconstruido: %s" % e)
    pcbnew.SaveBoard(novo, b)
    st["prep"] = True
    st["nets"] = {}
    log("prep: copia 2 camadas em " + novo)


LANE = {"OUT": -1.6, "+3V3": -2.3, "CLK": -3.0, "SER": -3.6, "QHP": -4.2, "QHP_J": -4.2,
        "EN1": 1.4, "EN2": 1.7, "EN3": 2.0, "EN4": 2.3, "EN5": 2.6, "EN6": -4.8, "EN7": -5.4, "EN8": -6.0}


def route_net(ctx, net, wpref, wmin, lm, vc, st, force=False):
    """Liga todos os componentes da rede (pads + escapes + trilhas) em um so, por A*."""
    rec = st.setdefault("nets", {}).setdefault(net, {"tentativas": 0})
    ok_all = True
    guard = 0
    while True:
        comps = [c for c in components(ctx, net) if c[1]]  # so componentes com pad
        if len(comps) <= 1:
            break
        guard += 1
        if guard > 40:
            ok_all = False
            break
        comps = [c for c in comps if c[2]]
        if len(comps) <= 1:
            break
        comps.sort(key=lambda c: min(ctx.g.pt(i, j)[0] for (L, i, j) in c[0]))
        A = comps[0]
        ax = sum(ctx.g.pt(i, j)[0] for (L, i, j) in A[0]) / len(A[0])
        ay = sum(ctx.g.pt(i, j)[1] for (L, i, j) in A[0]) / len(A[0])
        # destino: componente mais proximo
        def d(c):
            return min((ctx.g.pt(i, j)[0] - ax) ** 2 + (ctx.g.pt(i, j)[1] - ay) ** 2 for (L, i, j) in list(c[0])[::3])
        others = sorted(comps[1:], key=d)
        done = False
        for Bc in others[:2]:
            bx, by = min(((ctx.g.pt(i, j)), (i, j)) for (L, i, j) in Bc[0] for _ in [0]
                         )[0] if False else (None, None)
            # celula do destino mais proxima de A
            best = min(Bc[2], key=lambda c: (ctx.g.pt(c[1], c[2])[0] - ax) ** 2 + (ctx.g.pt(c[1], c[2])[1] - ay) ** 2)
            tx, ty = ctx.g.pt(best[1], best[2])
            for w in ([wpref, wmin] if wpref != wmin else [wpref]):
                t0 = time.time()
                path, why = ctx.route(net, w, A[2], Bc[2], (tx, ty), layer_mult=lm, via_cost=vc,
                                      extra=lane_cost(ctx, LANE[net], 1.0) if (net in LANE and os.environ.get("LANES") == "1") else None)
                log("  %s %s -> %s w=%.2f: %s (%.1fs)" % (net, A[1][:2], Bc[1][:2], w, why, time.time() - t0))
                if path:
                    ctx.write_path(net, w, path)
                    ctx.refresh()
                    rec.setdefault("largura", {})["%s>%s" % (A[1][0], Bc[1][0])] = w
                    done = True
                    break
            if done:
                break
        if not done:
            ok_all = False
            rec.setdefault("falhas", []).append(A[1][0])
            break
    rec["tentativas"] += 1
    rec["feito"] = ok_all
    return ok_all


def escapes(ctx, n, st, only=None):
    """Escape curto de cada pad de sinal para uma via (ordem: 595 primeiro). Fixa onde cada pino sai."""
    b = ctx.b
    c = CFG[n]
    nets = [x for x in sorted({p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads()})
            if x and not x.startswith("unconnected") and (x != "GND" or (only and "GND" in only))]
    jobs = []
    for net in nets:
        pads = ctx.net_pads(net)
        taken = []
        for p in sorted(pads, key=lambda p: p[3][0]):
            is595 = p[0].startswith("U9.") or (n == 4 and p[0].startswith("U5."))
            if only is None and not is595:
                continue
            if only is not None and net not in only and not (os.environ.get('ESC595') == '1' and is595 and net != 'GND'):
                continue
            if any(abs(p[3][0] - q[3][0]) < 1.3 and abs(p[3][1] - q[3][1]) < 1.3 for q in taken):
                continue
            taken.append(p)
            jobs.append((net, p))
    jobs.sort(key=lambda jb: (0 if jb[1][0].startswith("U9") or (n == 4 and jb[1][0].startswith("U5")) else
                              (1 if jb[0] == "+3V3" else 2), jb[1][3][0]))
    g = ctx.g
    for net, p in jobs:
        bl, viab = ctx.masks(net, 0.2)
        free = [~bl[F], ~bl[B]]
        cx, cy = p[3]
        i0, i1, j0, j1 = g.ix(cx - 3.2), g.ix(cx + 3.2), g.iy(cy - 3.2), g.iy(cy + 3.2)
        cand = set()
        r = p[1]
        for j in range(max(j0, 0), min(j1, g.ny)):
            for i in range(max(i0, 0), min(i1, g.nx)):
                if viab[j, i] or not (free[F][j, i] and free[B][j, i]):
                    continue
                x, y = g.pt(i, j)
                dx = max(r[0] - x, 0, x - r[2])
                dy = max(r[1] - y, 0, y - r[3])
                if (dx * dx + dy * dy) ** 0.5 < 0.62:
                    continue
                cand.add((B, i, j))
        tree = ctx.pad_cells(p[1], p[2])
        for cc in components(ctx, net):
            if p[0] in cc[1]:
                tree = set(cc[0])
        path, why = ctx.route(net, 0.2, tree, cand, None, layer_mult=(1.0, 1.0), via_cost=1e9, via_ok=False,
                              maxexp=400000)
        if not path:
            log("  escape %s %s: %s" % (net, p[0], why))
            st.setdefault("escapes_falha", []).append("%s %s" % (net, p[0]))
            continue
        _, i, j = path[-1]
        ctx.bucket = []
        ctx.write_path(net, 0.2, path + [(F, i, j)])
        for it in ctx.bucket:
            ctx.esc_ids.add(it.m_Uuid.AsString())
        ctx.bucket = None
        ctx.esc_pads.add(p[0])
        ctx.refresh()
    log("escapes feitos: %d pads" % len(jobs))


def default_order(n):
    d = {p[0]: p for p in PLAN}
    plan = [d["+3V3"], d["OUT"], d["CLK"], d["SER"], d["QHP"], d["QHP_J"]]
    for k in range(CFG[n]["ens"], 0, -1):
        plan.append(("EN%d" % k, 0.2, 0.15, (1.0, 1.25), 25.0))
    return plan


def prune_vias(b):
    """Remove vias que so tocam uma camada (escapes nao usados)."""
    n_rem = 0
    for _ in range(3):
        tr = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T]
        keep = []
        rem = []
        for v in [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]:
            p = v.GetPosition()
            touch = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 0}
            for t in tr:
                if t.GetNetname() != v.GetNetname():
                    continue
                for e in (t.GetStart(), t.GetEnd()):
                    if abs(e.x - p.x) < 2000 and abs(e.y - p.y) < 2000:
                        touch[t.GetLayer()] += 1
            if not (touch[pcbnew.F_Cu] and touch[pcbnew.B_Cu]):
                rem.append(v)
        for v in rem:
            b.Remove(v)
            KEEP.append(v)
        n_rem += len(rem)
        if not rem:
            break
    return n_rem


KEEP = []


def prune_dangling(b):
    """Remove trilhas com ponta solta (nao toca pad, via nem outra trilha da mesma rede)."""
    import math
    total = 0
    while True:
        tr = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T]
        vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        pads = [(p, p.GetNetname()) for fp in b.GetFootprints() for p in fp.Pads()]
        rem = []

        def ok_end(t, e):
            for v in vias:
                if v.GetNetname() == t.GetNetname() and abs(v.GetX() - e.x) < 2000 and abs(v.GetY() - e.y) < 2000:
                    return True
            for p, n in pads:
                if n == t.GetNetname() and p.IsOnLayer(t.GetLayer()) and p.HitTest(e):
                    return True
            for o in tr:
                if o is t or o.GetNetname() != t.GetNetname() or o.GetLayer() != t.GetLayer():
                    continue
                s, f = o.GetStart(), o.GetEnd()
                dx, dy = f.x - s.x, f.y - s.y
                L2 = dx * dx + dy * dy
                u = 0 if L2 == 0 else max(0, min(1, ((e.x - s.x) * dx + (e.y - s.y) * dy) / L2))
                if math.hypot(e.x - (s.x + u * dx), e.y - (s.y + u * dy)) < 2500:
                    return True
            return False
        for t in tr:
            if not (ok_end(t, t.GetStart()) and ok_end(t, t.GetEnd())):
                rem.append(t)
        for t in rem:
            b.Remove(t)
            KEEP.append(t)
        total += len(rem)
        if not rem:
            return total


def limpa_drc(n, st, max_it=6):
    """Remove pontas e vias soltas apontadas pelo proprio DRC do KiCad (uuid), ate nao restar nenhuma."""
    orig, novo = paths(n)
    total = 0
    for _ in range(max_it):
        d = drc(n, st, tag="_limpa")
        ids = []
        for v in d.get("violations", []):
            if v.get("type") in ("track_dangling", "via_dangling"):
                for it in v.get("items", []):
                    ids.append(it["uuid"])
        if not ids:
            break
        b = pcbnew.LoadBoard(novo)
        by = {str(t.m_Uuid.AsString()): t for t in b.GetTracks()}
        for u in ids:
            if u in by:
                b.Remove(by[u])
                KEEP.append(by[u])
                total += 1
        pcbnew.SaveBoard(novo, b)
    log("limpeza por DRC: %d itens removidos" % total)
    return total


def sinais(n, st, only=None):
    """Roteia as redes de sinal: escapes fixos (pads -> vias), depois cada rede por A*; as que falham
    sao refeitas por rip-up (desfaz uma rede vizinha, roteia a que falhou, roteia a desfeita de novo;
    se as duas nao fecham, restaura)."""
    orig, novo = paths(n)
    base = default_order(n)
    st["prep"] = False
    prep(n, st)
    st["nets"] = {}
    b = pcbnew.LoadBoard(novo)
    ctx = Ctx(b)
    st["escapes_falha"] = []
    escapes(ctx, n, st)
    pcbnew.SaveBoard(novo, b)
    save_state(STATE, st_all)
    buckets = {}
    spec = {p[0]: p for p in base}

    def run(net):
        (_, wp, wm, lm, vc) = spec[net]
        ctx.bucket = []
        t0 = time.time()
        ok = route_net(ctx, net, wp, wm, lm, vc, st)
        buckets.setdefault(net, []).extend(ctx.bucket)
        ctx.bucket = None
        st["nets"][net]["segundos"] = round(time.time() - t0, 1)
        log("%s: %s em %.1fs" % (net, "OK" if ok else "FALHOU", time.time() - t0))
        return ok

    def rip(net):
        for it in buckets.get(net, []):
            b.Remove(it)
        buckets[net] = []
        ctx.refresh()

    def center(net):
        pts = [(mm(p.GetX()), mm(p.GetY())) for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]
        return (sum(x for x, y in pts) / len(pts), sum(y for x, y in pts) / len(pts)) if pts else (0, 0)

    failed = []
    for p in base:
        if ctx.net_pads(p[0]):
            if not run(p[0]):
                failed.append(p[0])
    for rnd in range(3):
        still = []
        for f in failed:
            rip(f)
            if run(f):
                continue
            rip(f)
            # candidatos: redes ja roteadas, as mais proximas (pelo centro) primeiro
            cands = [x for x in buckets if x != f and buckets[x] and x not in failed]
            fx, fy = center(f)
            cands.sort(key=lambda x: min(((it.GetX() - nm(fx)) ** 2 + (it.GetY() - nm(fy)) ** 2) if hasattr(it, "GetX") else 1e30
                                         for it in buckets[x][:50]))
            solved = False
            for rr in cands:
                saved = list(buckets[rr])
                rip(rr)
                okf = run(f)
                okr = run(rr) if okf else False
                if okf and okr:
                    log("rip-up: %s refeita para abrir caminho a %s" % (rr, f))
                    st.setdefault("ripups", []).append("%s abre caminho a %s" % (rr, f))
                    solved = True
                    break
                rip(f)
                rip(rr)
                for it in saved:
                    b.Add(it)
                buckets[rr] = saved
                ctx.refresh()
            if not solved:
                still.append(f)
        failed = still
        if not failed:
            break
    log("vias soltas removidas: %d" % prune_vias(b))
    pcbnew.SaveBoard(novo, b)
    st["sinais_ok"] = not failed
    st["redes_falhas"] = failed
    save_state(STATE, st_all)
    return not failed


def drc(n, st, tag=""):
    orig, novo = paths(n)
    out = os.path.join(HERE, "drc_R%d%s.json" % (n, tag))
    subprocess.run([CLI, "pcb", "drc", "--severity-all", "--schematic-parity", "--format", "json", "-o", out, novo],
                   capture_output=True, text=True)
    d = json.load(open(out, encoding="utf-8"))
    cnt = {}
    for k in ("violations", "unconnected_items", "schematic_parity"):
        for v in d.get(k, []):
            key = "%s/%s" % (k[:4], v.get("type"))
            sev = v.get("severity")
            cnt["%s:%s" % (sev, key)] = cnt.get("%s:%s" % (sev, key), 0) + 1
    st["drc"] = cnt
    log("DRC R%d: %s" % (n, cnt))
    return d


if __name__ == "__main__":
    n = int(sys.argv[1])
    etapa = sys.argv[2]
    only = sys.argv[3:] or None
    st_all = load_state(STATE)
    st = st_all.setdefault("R%d" % n, {})
    if etapa in ("prep", "tudo"):
        prep(n, st)
        save_state(STATE, st_all)
    if etapa in ("sinais", "tudo"):
        sinais(n, st, only)
        limpa_drc(n, st)
    if etapa in ("drc", "sinais", "tudo", "gnd"):
        drc(n, st)
    save_state(STATE, st_all)
