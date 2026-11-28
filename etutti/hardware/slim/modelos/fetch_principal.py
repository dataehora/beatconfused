"""Slim (R12SL): downloads the EasyEDA STEP of the main board's parts that were still boxes in the 3D scene, by LCSC code, in small batches with a pause
(EasyEDA answers about 15 requests, then 403 for some minutes).  Plain python + plain curl.

    python etutti/hardware/slim/modelos/fetch_principal.py

Files go to modelos/baixados/<nome>_<LCSC>.step (not in Git) and the log to modelos/principal_fetch.json.  A part already downloaded is skipped, so the script can be run again.
Each part costs 2 requests (the component API, then the STEP): BATCH parts per round, PAUSE seconds between rounds, and a longer wait after a refusal.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "baixados")
PARTS = {"ind_L0603_120R_L101": "C14709", "ind_L0805_4u7_L102": "C63166", "bav70_D101": "C68978", "w25q64_U103": "C5362615", "xtal_32k_Y102": "C32346",
         "smf5v0_D201": "C151296", "usblc6_U201": "C7519", "ao3400a_Q201": "C20917", "jst_SM03B-SRSS_J202": "C160403", "fb_0603_FB301": "C19330",
         "xc6206_U302": "C347373", "led_0805_RGCA_D401": "C965845", "mkl02_U102": "C2056583"}
API = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"
STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/%s"
BATCH, PAUSE, WAIT_403 = 5, 240, 420


def get(url):
    return subprocess.run(["curl", "-s", "-f", "--max-time", "90", url], check=True, capture_output=True).stdout


def main():
    os.makedirs(OUT, exist_ok=True)
    log_path = os.path.join(HERE, "principal_fetch.json")
    log = json.load(open(log_path, encoding="utf-8")) if os.path.exists(log_path) else {}
    todo = [(n, c) for n, c in PARTS.items() if not os.path.exists(os.path.join(OUT, "%s_%s.step" % (n, c)))]
    done_round = 0
    fails = {}
    while todo:
        name, lcsc = todo[0]
        path = os.path.join(OUT, "%s_%s.step" % (name, lcsc))
        try:
            doc = json.loads(get(API % lcsc))
            res = doc["result"]
            title = res.get("title", "")
            shapes = res["packageDetail"]["dataStr"]["shape"]
            node = next((json.loads(s.split("~", 1)[1]) for s in shapes if s.startswith("SVGNODE~")), None)
            if node is None:
                log[name] = {"lcsc": lcsc, "erro": "sem modelo 3D no EasyEDA", "titulo": title}
                print("SEM MODELO %s %s %s" % (name, lcsc, title), flush=True)
                todo.pop(0)
                continue
            a = node["attrs"]
            data = get(STEP % a["uuid"])
            if not data.lstrip().startswith(b"ISO-10303"):
                raise ValueError("not a STEP file (%d bytes)" % len(data))
            open(path, "wb").write(data)
            log[name] = {"lcsc": lcsc, "arquivo": os.path.basename(path), "bytes": len(data), "titulo": a.get("title") or title}
            print("ok   %-24s %s %7d bytes %s" % (name, lcsc, len(data), a.get("title")), flush=True)
            todo.pop(0)
            done_round += 1
        except Exception as e:  # noqa: BLE001
            fails[name] = fails.get(name, 0) + 1
            print("FALHOU %s %s: %s (tentativa %d) -> espera %d s" % (name, lcsc, e, fails[name], WAIT_403), flush=True)
            if fails[name] >= 3:
                log[name] = {"lcsc": lcsc, "erro": str(e)}
                todo.pop(0)
            json.dump(log, open(log_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            time.sleep(WAIT_403)
            continue
        json.dump(log, open(log_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        time.sleep(4)
        if done_round >= BATCH and todo:
            print("lote feito, pausa de %d s" % PAUSE, flush=True)
            time.sleep(PAUSE)
            done_round = 0
    print("FIM", flush=True)


if __name__ == "__main__":
    sys.exit(main())
