"""eTutti Slim (R13SL item 4): the verification rule for every script that makes or changes a board, a model or the case. Stdlib only.

Rule (the A2/A3 mistake: a script printed "no free spot", wrote nothing, and a DRC of the OLD file was reported):
  1. a script ends with a non-zero exit code when it fails OR when an output file was not written in THIS run;
  2. before reporting a DRC, a fit check or a number, the file it came from is checked to have been written in this run (date and time printed);
  3. the report names the file checked and when it was written; the script's WHOLE output is read, never only its last line.

Use:
    import verificacao as V
    T0 = V.inicio()                                  # first thing in main()
    ...
    V.forcar("nome_do_script")                       # (before writing) SLIM_FORCAR_FALHA=nome_do_script makes the script fail here: used to TEST the rule
    V.exige([path1, path2], T0, "nome_do_script")    # last thing: every file exists and was written after T0, prints "VERIFICADO <file> gravado <date time>", else exit 3
    V.falha("message")                               # any failure: prints "ERRO: ..." and exits 1

A shell pipeline hides a failing script (`script | tail -1` returns tail's status): run scripts with `python etutti/hardware/slim/rodar_verificado.py <command...>`, which shows the whole
output, the exit code and the date of the files named with --arquivos.
"""
import os
import sys
import time


def inicio():
    return time.time()


def _fmt(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def falha(msg, codigo=1):
    print("ERRO: %s" % msg, flush=True)
    sys.exit(codigo)


def forcar(nome):
    """test hook: SLIM_FORCAR_FALHA=<nome> (or 'todos') makes this point fail, as a failed placement would."""
    alvo = os.environ.get("SLIM_FORCAR_FALHA", "")
    if alvo and alvo in (nome, "todos"):
        falha("falha FORCADA para teste (%s): nada foi gravado" % nome, 4)


def exige(paths, t0, nome=""):
    ruim = []
    for p in paths:
        if not os.path.exists(p):
            ruim.append("%s nao existe" % p)
        elif os.path.getmtime(p) < t0 - 1.0:
            ruim.append("%s NAO foi gravado nesta execucao (gravado %s, execucao iniciada %s)" % (p, _fmt(os.path.getmtime(p)), _fmt(t0)))
    if ruim:
        for r in ruim:
            print("ERRO: %s" % r, flush=True)
        sys.exit(3)
    for p in paths:
        print("VERIFICADO %s | gravado %s" % (os.path.relpath(p) if os.path.isabs(p) and os.path.commonpath([os.getcwd(), p]) == os.getcwd() else p, _fmt(os.path.getmtime(p))), flush=True)


def data(path):
    return _fmt(os.path.getmtime(path)) if os.path.exists(path) else "(inexistente)"
