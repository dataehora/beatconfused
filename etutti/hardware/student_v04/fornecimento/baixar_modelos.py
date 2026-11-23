"""Student V4 (R13V4, item 2): baixa o modelo 3D (STEP) de cada codigo LCSC montado pela JLCPCB (principal + reguas) da EasyEDA.

    python etutti/hardware/student_v04/fornecimento/baixar_modelos.py            # so o que falta
    python etutti/hardware/student_v04/fornecimento/baixar_modelos.py --lento 30  # segundos entre pedidos

Pasta de saida: fornecimento/modelos3d/ (FORA do git, ver .gitignore): <LCSC>.step + <LCSC>.json (resposta da API cortada ao pacote).
Indice tracked: fornecimento/modelos3d_indice.json (uuid do modelo, origem, giro, z, nome, bytes; "sem modelo" quando a EasyEDA nao tem).
Reaproveita STEP ja baixados nas pastas das versoes anteriores (so leitura). curl simples, sem rajadas: a EasyEDA recusa depois de ~12 pedidos.
"""
import csv, json, os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "modelos3d")
IDX = os.path.join(HERE, "modelos3d_indice.json")
API = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"
STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/%s"
REUSE = {"C255515": "student_v01/model3d/modelos/encoder_EC11E_C255515.step", "C668605": "student_v01/model3d/modelos/jack_PJ-327A_C668605.step",
         "C48985906": "student_v01/model3d/modelos/m2_91302-42-067_C48985906.step", "C265101": "student_v01/model3d/modelos/jst_S3B-PH-SM4-TB_C265101.step",
         "C165948": "student_v01/model3d/modelos/usbc_TYPE-C-31-M-12_C165948.step", "C318884": "student_v01/model3d/modelos/botao_TS-1187A_C318884.step",
         "C49284723": "student_v03/case/modelos/jack_PJ-327A_XUNPU_C49284723.step", "C202365": "student_v03/case/modelos/encoder_EC11E18244AU_C202365.step"}


def get(url):
    return subprocess.run(["curl", "-s", "-f", "--max-time", "90", url], capture_output=True).stdout


def codes():
    cs = []
    for p in ("fab/principal/bom.csv", "fab/regua/R8E_painel2/bom.csv", "fab/regua/R4E_painel5/bom.csv"):
        cs += [r["LCSC Part #"] for r in csv.DictReader(open(os.path.join(HERE, "..", p), encoding="utf-8"))]
    return list(dict.fromkeys(cs))


def main():
    wait = float(sys.argv[sys.argv.index("--lento") + 1]) if "--lento" in sys.argv else 20.0
    os.makedirs(OUT, exist_ok=True)
    idx = json.load(open(IDX, encoding="utf-8")) if os.path.exists(IDX) else {}
    for c in codes() + list(REUSE):
        step = os.path.join(OUT, c + ".step")
        if c in idx and os.path.exists(step):
            continue
        raw = get(API % c)
        try:
            doc = json.loads(raw)["result"]["packageDetail"]
        except Exception:
            print("FALHA API", c, raw[:80]); time.sleep(wait); continue
        open(os.path.join(OUT, c + ".json"), "wb").write(raw)
        node = next((json.loads(s.split("~", 1)[1]) for s in doc["dataStr"]["shape"] if s.startswith("SVGNODE~")), None)
        head = doc["dataStr"]["head"]
        rec = {"footprint_origin": [head.get("x"), head.get("y")], "titulo": doc.get("title")}
        if node is None:
            rec["modelo"] = False
            idx[c] = rec; print("SEM MODELO", c); time.sleep(wait); continue
        a = node["attrs"]
        rec.update({"modelo": True, "uuid": a.get("uuid"), "c_origin": a.get("c_origin"), "c_rotation": a.get("c_rotation"), "z": a.get("z"), "nome3d": a.get("title")})
        if c in REUSE and os.path.exists(os.path.join(HW, REUSE[c])):
            shutil.copyfile(os.path.join(HW, REUSE[c]), step); rec["origem_step"] = "copiado de " + REUSE[c]
        else:
            time.sleep(3)
            data = get(STEP % a["uuid"])
            if not data.lstrip().startswith(b"ISO-10303"):
                print("STEP INVALIDO", c, len(data)); idx[c] = rec; rec["modelo"] = False; rec["erro"] = "step nao veio"; time.sleep(wait); continue
            open(step, "wb").write(data)
        rec["bytes"] = os.path.getsize(step)
        idx[c] = rec
        json.dump(idx, open(IDX, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("ok", c, rec["nome3d"], rec["bytes"])
        time.sleep(wait)
    json.dump(idx, open(IDX, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
