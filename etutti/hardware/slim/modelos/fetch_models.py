"""Slim: downloads the STEP models of the chosen parts from EasyEDA's public model server (by LCSC code) into modelos/baixados/
and measures each one's bounding box (CadQuery). Writes modelos/index.json. The STEP files are not in Git (see .gitignore).

    python etutti/hardware/slim/modelos/fetch_models.py            # fetch what is missing, then measure   (plain python)
    "C:/Users/julia/.venvs/cadquery/Scripts/python.exe" etutti/hardware/slim/modelos/fetch_models.py --measure

EasyEDA answers about a dozen requests, then 403 for some minutes: the script stops at the first refusal and can be run again.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "baixados")
PARTS = {"usbc_TYPE-C-31-M-12": "C165948", "jack_PJ-327A_XUNPU": "C49284723", "ffc_8p_05_h1": "C3250113",
         "tmag5273A2": "C3020565", "tmag5273B2": "C41935525", "drv5032ZE": "C266118", "ind_FNR3015": "C167747",
         "bq24075": "C15464", "tmag5253": "C22401868", "hc595_dhvqfn": "C730243", "sgtl5000": "C2651833",
         "jst_S3B-PH": "C265101", "led_1615": "C273605", "tps63001": "C28060", "xtal_24M_3225": "C524739",
         "botao_TS-1187A": "C318884", "usbc_TYPE-C-31-M-14": "C223907", "ffc_8p_05_h2": "C66953"}
API = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"
STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/%s"


def get(url):
    return subprocess.run(["curl", "-s", "-f", "--max-time", "90", url], check=True, capture_output=True).stdout


def fetch():
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(HERE, "index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    for name, lcsc in PARTS.items():
        path = os.path.join(OUT, "%s_%s.step" % (name, lcsc))
        if os.path.exists(path):
            continue
        try:
            doc = json.loads(get(API % lcsc))
            shapes = doc["result"]["packageDetail"]["dataStr"]["shape"]
            node = next(json.loads(s.split("~", 1)[1]) for s in shapes if s.startswith("SVGNODE~"))
            a = node["attrs"]
            data = get(STEP % a["uuid"])
            if not data.lstrip().startswith(b"ISO-10303"):
                raise ValueError("not a STEP file (%d bytes)" % len(data))
            open(path, "wb").write(data)
            index[name] = {"lcsc": lcsc, "file": os.path.basename(path), "bytes": len(data), "title": a.get("title")}
            print("ok   %-22s %s %7d bytes %s" % (name, lcsc, len(data), a.get("title")), flush=True)
        except Exception as e:
            index[name] = {"lcsc": lcsc, "error": str(e)}
            print("FAIL %-22s %s %s" % (name, lcsc, e), flush=True)
            if "22" in str(e):          # curl exit 22 = HTTP error (403): stop, try again later
                break
        time.sleep(3)
    json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)


def measure():
    import cadquery as cq
    idx_path = os.path.join(HERE, "index.json")
    index = json.load(open(idx_path, encoding="utf-8"))
    for name, rec in index.items():
        if "file" not in rec:
            continue
        shape = cq.importers.importStep(os.path.join(OUT, rec["file"]))
        bb = shape.val().BoundingBox()
        rec["bbox_mm"] = {"x": [round(bb.xmin, 2), round(bb.xmax, 2)], "y": [round(bb.ymin, 2), round(bb.ymax, 2)],
                          "z": [round(bb.zmin, 2), round(bb.zmax, 2)], "size": [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)]}
        print("%-22s %s  size %s  z %s..%s" % (name, rec["lcsc"], rec["bbox_mm"]["size"], rec["bbox_mm"]["z"][0], rec["bbox_mm"]["z"][1]))
    json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    if "--measure" in sys.argv:
        measure()
    else:
        fetch()
