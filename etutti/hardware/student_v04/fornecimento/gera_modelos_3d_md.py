"""Student V4 (R13V4): writes fornecimento/MODELOS_3D.md from pcb/build/previa_fit_{principal,r8,r4}.json (made by pcb/previa_jlc.py). Stdlib.

    python etutti/hardware/student_v04/fornecimento/gera_modelos_3d_md.py

The fixed texts are in modelos_3d_topo.md and modelos_3d_fim.md (same folder).
"""
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "..", "pcb", "build")
EXPECT = {"J201": "-x (borda esquerda)", "J301": "-x (borda esquerda)", "J302": "-x (borda esquerda)", "J601": "+x (borda direita)", "J602": "+x (borda direita)",
          "J603": "+x (borda direita)", "J604": "+x (borda direita)", "J401": "+y (para a fenda do cabo)", "J202": "-y (para a baia da bateria)", "J101": "+x (para H101)"}


def table(board, title):
    d = json.load(open(os.path.join(B, "previa_fit_%s.json" % board), encoding="utf-8"))
    g = OrderedDict()
    for ref, v in d.items():
        g.setdefault((v["lcsc"], v["footprint"]), []).append((ref, v))
    out = ["### %s" % title, "", "| Refs | LCSC | Modelo 3D (EasyEDA) | Modelo | Erro de ajuste (mm) | Pino 1 do CPL (mm) | Marcador do pino 1 no modelo | Boca | Nota |",
           "|---|---|---|:-:|---:|---:|---|---|---|"]
    bad = []
    for (code, fp), items in g.items():
        refs = [r for r, _ in items]
        v = items[0][1]
        ea = max(x.get("erro_ajuste_mm", 0) or 0 for _, x in items)
        p1 = v.get("dist_pino1_mm")
        mk = v.get("marcador_pino1")
        if mk is None:
            mks = "-"
        elif not mk or "erro" in mk:
            mks = "sem marcador detectado"
        else:
            mks = ("ok (pads %s)" if mk["ok"] else "ERRO (pads %s)") % "/".join(mk["pads_proximos"])
        bo = v.get("boca")
        bos = "-"
        note = ""
        if bo:
            exp = EXPECT.get(refs[0], "")
            bos = "%s; esperado %s: %s" % (bo["boca"], exp, "ok" if exp.split(" ")[0] == bo["boca"].split(" ")[0] else "visual")
        if ea > 0.3:
            note = "modelo da biblioteca deslocado (c_origin da EasyEDA); o CPL está certo (pads); o KiCad usa o modelo corrigido"
            bad.append(code)
        if p1 is None:
            note += " pads com nomes diferentes: pino 1 conferido pela posição (erro máx. dos pads %.2f)" % v.get("dist_max_pads_mm", 0)
        rs = ", ".join(refs) if len(refs) <= 6 else "%s ... %s (%d)" % (refs[0], refs[-1], len(refs))
        out.append("| %s | %s | %s | sim | %.2f | %s | %s | %s | %s |" % (rs, code, v.get("modelo3d", "-"), ea, "-" if p1 is None else "%.2f" % p1, mks, bos, note.strip()))
    return "\n".join(out), bad


def main():
    a, bad_a = table("principal", "Placa principal (78 peças montadas pela JLCPCB, todas no fundo)")
    b, bad_b = table("r8", "Régua R8E em painel de 2 (a R8 é a mesma sem J2 e R1)")
    c, _ = table("r4", "Régua R4E em painel de 5 (só tabela; R8E, R4 e R4E repetem as mesmas peças)")
    top = open(os.path.join(HERE, "modelos_3d_topo.md"), encoding="utf-8").read().rstrip()
    fim = open(os.path.join(HERE, "modelos_3d_fim.md"), encoding="utf-8").read().rstrip()
    open(os.path.join(HERE, "MODELOS_3D.md"), "w", encoding="utf-8").write("\n\n".join([top, a, b, c, fim]) + "\n")
    print("ok", sorted(set(bad_a + bad_b)))


if __name__ == "__main__":
    main()
