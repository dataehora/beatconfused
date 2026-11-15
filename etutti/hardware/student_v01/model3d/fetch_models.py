"""Downloads the 3D models (STEP) of the board's parts that KiCad's library lacks, from EasyEDA's
public model server, by LCSC code. Writes modelos/<ref>_<lcsc>.step and modelos/index.json
(the model's placement data as EasyEDA gives it). The folder is not in Git.

    python etutti/hardware/student_v01/model3d/fetch_models.py
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "modelos")
PARTS = {"encoder_EC11E": "C255515", "jack_PJ-327A": "C668605", "m2_91302-42-067": "C48985906",
         "jst_S3B-PH-SM4-TB": "C265101", "usbc_TYPE-C-31-M-12": "C165948", "botao_TS-1187A": "C318884",
         "led_1615": "C273605", "codec_SGTL5000": "C2651833"}
API = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"
STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/%s"


def get(url):
    # plain curl: the server refuses Python's default client and browser-like headers
    return subprocess.run(["curl", "-s", "-f", "--max-time", "90", url], check=True, capture_output=True).stdout


def main():
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for name, lcsc in PARTS.items():
        try:
            doc = json.loads(get(API % lcsc))
            shapes = doc["result"]["packageDetail"]["dataStr"]["shape"]
            node = next(json.loads(s.split("~", 1)[1]) for s in shapes if s.startswith("SVGNODE~"))
            a = node["attrs"]
            data = get(STEP % a["uuid"])
            if not data.lstrip().startswith(b"ISO-10303"):
                raise ValueError("not a STEP file (%d bytes)" % len(data))
            path = os.path.join(OUT, "%s_%s.step" % (name, lcsc))
            open(path, "wb").write(data)
            head = doc["result"]["packageDetail"]["dataStr"]["head"]
            index[name] = {"lcsc": lcsc, "file": os.path.basename(path), "bytes": len(data), "title": a.get("title"),
                           "c_origin": a.get("c_origin"), "c_rotation": a.get("c_rotation"), "z": a.get("z"),
                           "footprint_origin": [head.get("x"), head.get("y")]}
            print("ok   %-22s %s  %7d bytes  %s" % (name, lcsc, len(data), a.get("title")))
        except Exception as e:                                  # a part without a model stays a box
            index[name] = {"lcsc": lcsc, "error": str(e)}
            print("FAIL %-22s %s  %s" % (name, lcsc, e))
    json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
