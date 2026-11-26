"""Runner of the ruler routing stages (R8SL 3a). Plain python; each stage is idempotent and resumable through estado.json.

    python etapas.py [--force etapa] [--only etapa]       etapas: base, fixa, sinais, gnd, verifica, grade, imagens

State (estado.json): per stage {feito, segundos, hash_entrada, saida, ...}. A stage whose input hash (the files it reads) is unchanged and whose output exists is skipped.
The long stage (sinais, minutes) is started by this runner with the same command you can run by hand; run it in the background:
    python etapas.py --only sinais > build/sinais.log 2>&1 &
An interrupted run just starts the stage again (nothing is half-written: every stage writes its output at the end).
Commit per finished stage is the integrator's job (no git here).
"""
import hashlib, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..")))
import verificacao as V  # noqa: E402
KP = "C:/Program Files/KiCad/10.0/bin/python.exe"
VP = "C:/Users/julia/.venvs/cadquery/Scripts/python.exe"
EST = os.path.join(HERE, "estado.json")
K = os.path.join(HERE, "kicad")
SRC = os.path.join(HERE, "..", "..", "kicad_regua", "slim_regua.kicad_pcb")


def sha(*paths):
    h = hashlib.sha1()
    for p in paths:
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


def load():
    return json.load(open(EST)) if os.path.exists(EST) else {}


def save(e):
    json.dump(e, open(EST, "w"), indent=1)


def sh(cmd, env=None):
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, **(env or {})))
    return r, round(time.time() - t, 1)


STAGES = {
    "base": dict(inp=[SRC, os.path.join(HERE, "prepara.py")], out=os.path.join(K, "base", "slim_regua.kicad_pcb"),
                 cmd=lambda: [KP, os.path.join(HERE, "prepara.py")]),
    "fixa": dict(inp=[os.path.join(K, "base", "slim_regua.kicad_pcb"), os.path.join(HERE, "fixa.py")], out=os.path.join(K, "fixo.kicad_pcb"),
                 cmd=lambda: [KP, os.path.join(HERE, "fixa.py")]),
    "sinais": dict(inp=[os.path.join(K, "fixo.kicad_pcb"), os.path.join(HERE, "rota_grade.py")], out=os.path.join(K, "sinais.kicad_pcb"),
                   cmd=lambda: [KP, "-u", os.path.join(HERE, "rota_grade.py"), os.path.join(K, "fixo.kicad_pcb"), os.path.join(K, "sinais.kicad_pcb"),
                                "--order=CLK,LATCH,DATA,OUT,+3V3"]),
    "gnd": dict(inp=[os.path.join(K, "sinais.kicad_pcb"), os.path.join(HERE, "gnd.py")], out=os.path.join(K, "slim_regua_rota.kicad_pcb"),
                cmd=lambda: [KP, os.path.join(HERE, "gnd.py"), os.path.join(K, "sinais.kicad_pcb"), os.path.join(K, "slim_regua_rota.kicad_pcb")]),
    "verifica": dict(inp=[os.path.join(K, "slim_regua_rota.kicad_pcb"), os.path.join(HERE, "verifica.py")], out=os.path.join(HERE, "build", "verifica.json"),
                     cmd=lambda: [KP, os.path.join(HERE, "verifica.py"), os.path.join(K, "slim_regua_rota.kicad_pcb")]),
    "grade": dict(inp=[os.path.join(HERE, "..", "..", "kicad_regua", "slim_grade.kicad_pcb"), os.path.join(HERE, "grade.py")], out=os.path.join(HERE, "build", "grade.json"),
                  cmd=lambda: [KP, os.path.join(HERE, "grade.py")]),
    "imagens": dict(inp=[os.path.join(K, "slim_regua_rota.kicad_pcb"), os.path.join(HERE, "imagens.py")], out=os.path.join(HERE, "..", "img", "regua_frente.png"),
                    cmd=lambda: [KP, os.path.join(HERE, "imagens.py"), "dump", os.path.join(K, "slim_regua_rota.kicad_pcb"), os.path.join(HERE, "build", "regua_geom.json")],
                    cmd2=lambda: [VP, os.path.join(HERE, "imagens.py"), "draw", os.path.join(HERE, "build", "regua_geom.json"), os.path.join(HERE, "..", "img")]),
}


def main():
    args = sys.argv[1:]
    force = args[args.index("--force") + 1] if "--force" in args else None
    only = args[args.index("--only") + 1] if "--only" in args else None
    e = load()
    for name, st in STAGES.items():
        if only and name != only:
            continue
        h = sha(*st["inp"])
        rec = e.get(name, {})
        if rec.get("feito") and rec.get("hash_entrada") == h and os.path.exists(st["out"]) and force != name:
            print("[%s] ja feita (%s)" % (name, rec.get("segundos")))
            continue
        print("[%s] rodando..." % name, flush=True)
        t_ini = time.time()
        r, secs = sh(st["cmd"]())
        if "cmd2" in st and r.returncode == 0:
            r2, s2 = sh(st["cmd2"]())
            secs += s2
            r = r2
        tail = (r.stdout or "")[-400:] + (r.stderr or "")[-200:]
        gravou = os.path.exists(st["out"]) and os.path.getmtime(st["out"]) >= t_ini - 1.0      # R13SL: the stage's output must have been written in THIS run
        e[name] = {"feito": r.returncode == 0 and gravou, "segundos": secs, "hash_entrada": h, "saida": os.path.relpath(st["out"], HERE), "cauda": tail}
        if name in ("verifica", "grade") and os.path.exists(st["out"]):
            e[name]["resultado"] = json.load(open(st["out"]))
        save(e)
        print("[%s] %s em %.1fs" % (name, "ok" if e[name]["feito"] else "FALHOU", secs))
        if not e[name]["feito"]:
            print("ERRO: etapa %s falhou (codigo %d, saida gravada agora: %s). Cauda:\n%s" % (name, r.returncode, gravou, tail))
            sys.exit(1)
    vf = os.path.join(HERE, "build", "verifica.json")
    if only is None or only in ("verifica", "grade"):
        for f in (vf, os.path.join(HERE, "build", "grade.json"), os.path.join(K, "slim_regua_rota.kicad_pcb")):
            print("ARQUIVO %s | gravado %s" % (os.path.relpath(f, HERE), V.data(f)))
        if os.path.exists(vf) and not json.load(open(vf)).get("aceito", False):
            print("ERRO: verifica.json diz aceito = false (DRC com erro/aviso, nao ligado, paridade ou regra de OUT)")
            sys.exit(1)


main()
