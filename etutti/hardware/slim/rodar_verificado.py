"""eTutti Slim (R13SL item 4): runs a command, shows ALL its output, its exit code and the date of the files you name. Stdlib only.

    python etutti/hardware/slim/rodar_verificado.py [--arquivos a.json,b.kicad_pcb] -- <command> [args...]

Exit code = the command's (so a failing script is never hidden by a pipeline).  With --arquivos, each file must have been written AFTER the command started, else exit 3.
"""
import os
import subprocess
import sys
import time


def main():
    a = sys.argv[1:]
    arquivos = []
    if a and a[0] == "--arquivos":
        arquivos = [x for x in a[1].split(",") if x]
        a = a[2:]
    if a and a[0] == "--":
        a = a[1:]
    if not a:
        print("uso: rodar_verificado.py [--arquivos a,b] -- comando ...")
        return 2
    t0 = time.time()
    r = subprocess.run(a)
    print("--- codigo de saida: %d" % r.returncode)
    rc = r.returncode
    for p in arquivos:
        if not os.path.exists(p):
            print("ARQUIVO %s: inexistente" % p)
            rc = rc or 3
            continue
        m = os.path.getmtime(p)
        ok = m >= t0 - 1.0
        print("ARQUIVO %s: gravado %s %s" % (p, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(m)), "(nesta execucao)" if ok else "(NAO nesta execucao)"))
        if not ok:
            rc = rc or 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
