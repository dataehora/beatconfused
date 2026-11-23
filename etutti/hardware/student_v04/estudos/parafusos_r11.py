"""R11V4 item 2: fasteners by use (ruler, lid posts / wall bosses / H1..H4, OLED), three options compared on stability, cracking, reassembly, cost.

    python etutti/hardware/student_v04/estudos/parafusos_r11.py   ->  estudos/parafusos_r11.json (and the tables printed)

Nothing here was bought or measured: prices are catalogue-level estimates for small quantities (2026, GBP/USD not converted, US$), the boss rules are the
manufacturers' general design rules (EJOT Delta PT / Wurth thread-forming screws for thermoplastics; Ruthex / CNC Kitchen-type heat-set inserts) quoted from
memory, NOT re-read from their data sheets in this session, and the cycle counts are engineering judgement. They are the inputs a prototype test must confirm
(cycle test: 20 assemblies of each joint on a printed PA12 MJF boss, then pull-out; FIT_CHECK R11V4 risk 3).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- joints of the 32-key instrument (count, what loads it, how many times it is taken apart in the life of the instrument)
USES = {
    "regua": {"n": 8, "ciclos_exigidos": 10, "carga": "levantar a regua (plugue SH: 1-2 N de extracao) e rattle; a forca das teclas passa pelos trilhos, nao pelo parafuso; trocas: extensao modular + regua defeituosa",
              "boss_D_modelo": 6.0, "tem_acesso_por_baixo": True},
    "tampa": {"n": 15, "ciclos_exigidos": 10, "carga": "pre-carga que segura a tampa na bandeja (5 internos + 6 de parede + 4 H); aberta a cada troca de regua e a cada servico",
              "boss_D_modelo": 5.0, "tem_acesso_por_baixo": True},
    "oled": {"n": 4, "ciclos_exigidos": 3, "carga": "peso do modulo (4,5 g) e choque (50 g = 2,2 N); montado uma vez, trocado so se falhar",
             "boss_D_modelo": 4.2, "tem_acesso_por_baixo": True},
}

# ---- options: price per fastener (US$, estimate), time (min), cycles the thread survives, boss rule (min outer D as a multiple of the screw's d), tools
OPT = {
    "A: formador de rosca (PT 2.0) direto na bossa": {"peca": 0.04, "extra": 0.0, "min": 0.5, "ciclos": 7, "boss_min_mult": 2.0, "ferramenta": 0.0, "pilot": 1.75,
                                                        "nota": "pre-carga relaxa 30-50 % em semanas (fluencia do PA12 na rosca); 5-10 remontagens; sem calor, sem inserto"},
    "B: parafuso de maquina M2 em inserto de latao": {"peca": 0.03, "extra": 0.09, "min": 2.0, "ciclos": 50, "boss_min_mult": 3.2, "ferramenta": 8.0, "pilot": 3.2,
                                                       "nota": "rosca metalica (50+ remontagens); o inserto quente deforma e tensiona a parede: regra D externo >= 2 x D do inserto (6,4 mm)"},
    "C: parafuso passante M2 + porca": {"peca": 0.05, "extra": 0.015, "min": 1.0, "ciclos": 1000, "boss_min_mult": 1.2, "ferramenta": 0.0, "pilot": 2.4,
                                         "nota": "rosca metalica dos dois lados, sem tensao radial na bossa; pre-carga mantida (parafuso comprido); exige acesso por baixo e bolso sextavado"},
}
D_SCREW = 2.0


def main():
    res = {"premissas": "estimativas de catalogo e regras gerais dos fabricantes, nada comprado nem medido", "usos": {}, "opcoes": {}, "escolha": {}}
    for on, o in OPT.items():
        res["opcoes"][on] = {k: v for k, v in o.items()}
    for un, u in USES.items():
        res["usos"][un] = {"n": u["n"], "carga": u["carga"], "ciclos_exigidos": u["ciclos_exigidos"], "boss_D_modelo": u["boss_D_modelo"]}
        tab = {}
        for on, o in OPT.items():
            boss_min = o["boss_min_mult"] * D_SCREW if on.startswith("A") else (6.4 if on.startswith("B") else o["boss_min_mult"] * 2.4 + 0.0)
            custo_pecas = u["n"] * (o["peca"] + o["extra"])
            tempo = u["n"] * o["min"]
            ok_ciclos = o["ciclos"] >= u["ciclos_exigidos"]
            ok_boss = u["boss_D_modelo"] >= boss_min - 1e-9
            tab[on] = {"custo_pecas_US$": round(custo_pecas, 2), "tempo_montagem_min": round(tempo, 1), "ciclos_ok": ok_ciclos, "boss_min_mm": round(boss_min, 1),
                       "boss_do_modelo_ok": ok_boss, "ferramenta_US$": o["ferramenta"], "pilot_mm": o["pilot"]}
        res["usos"][un]["comparacao"] = tab
    # adopted
    res["escolha"] = {"regua": "C: parafuso passante M2 (10/12/14/16 mm por fileira) + porca em bolso sextavado por baixo",
                      "tampa": "A: formador de rosca M2 (PT 2.0 x 8 por baixo; x 16 nos 4 H, que atravessam bandeja e placa), piloto 1,75 de 7 mm nos postes",
                      "oled": "A: formador de rosca M2 x 4 nos 4 postes D4,2 (piloto 1,75), o modulo tem furos de 2,5"}
    tot = {}
    for name, picks in (("adotado (C na regua, A na tampa e no OLED)", {"regua": "C", "tampa": "A", "oled": "A"}),
                        ("tudo A (formador de rosca)", {"regua": "A", "tampa": "A", "oled": "A"}),
                        ("tudo B (inserto)", {"regua": "B", "tampa": "B", "oled": "B"}),
                        ("regua C, tampa B, OLED A", {"regua": "C", "tampa": "B", "oled": "A"})):
        c = t = 0.0
        tools = set()
        for un, p in picks.items():
            o = [v for k, v in OPT.items() if k.startswith(p)][0]
            c += USES[un]["n"] * (o["peca"] + o["extra"])
            t += USES[un]["n"] * o["min"]
            if o["ferramenta"]:
                tools.add(o["ferramenta"])
        tot[name] = {"pecas_US$": round(c, 2), "ferramentas_US$": sum(tools), "tempo_min": round(t, 1)}
    res["totais_32_teclas"] = tot
    res["por_regua_acrescentada"] = {"A": round(2 * 0.04, 2), "B": round(2 * 0.12, 2), "C": round(2 * 0.065, 2)}
    json.dump(res, open(os.path.join(HERE, "parafusos_r11.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for un, u in res["usos"].items():
        print(un, u["n"], "juntas")
        for on, t in u["comparacao"].items():
            print("  ", on, t)
    for k, v in tot.items():
        print(k, v)


if __name__ == "__main__":
    main()
