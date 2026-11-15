"""Minimal GLB reader: triangles of every mesh with its node transform and base colour.

KiCad's GLB is in metres with Y up. `read()` returns one (points_mm, faces, rgb, name) per material,
already in the model's frame: x right, y = -y_kicad, z up, millimetres.
"""
import json
import struct

import numpy as np

DTYPE = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    m = np.eye(4)
    if "rotation" in node:
        x, y, z, w = node["rotation"]
        m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    if "scale" in node:
        m[:3, :3] = m[:3, :3] * np.array(node["scale"], dtype=float)
    if "translation" in node:
        m[:3, 3] = node["translation"]
    return m


def read(path):
    raw = open(path, "rb").read()
    n_json = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + n_json])
    blob = raw[20 + n_json + 8:]

    def accessor(i):
        a = doc["accessors"][i]
        v = doc["bufferViews"][a["bufferView"]]
        n = NCOMP[a["type"]]
        dt = np.dtype(DTYPE[a["componentType"]])
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0)
        if stride and stride != dt.itemsize * n:
            arr = np.ndarray((a["count"], n), dtype=dt, buffer=blob, offset=off, strides=(stride, dt.itemsize))
        else:
            arr = np.frombuffer(blob, dtype=dt, count=a["count"] * n, offset=off).reshape(a["count"], n)
        return np.array(arr)

    by_mat = {}

    def visit(i, parent):
        node = doc["nodes"][i]
        m = parent @ _matrix(node)
        if "mesh" in node:
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                p = accessor(prim["attributes"]["POSITION"]).astype(float)
                p = p @ m[:3, :3].T + m[:3, 3]
                f = (accessor(prim["indices"]).reshape(-1, 3) if "indices" in prim
                     else np.arange(len(p)).reshape(-1, 3)).astype(np.int64)
                pts, faces = by_mat.setdefault(prim.get("material", -1), ([], []))
                faces.append(f + sum(len(q) for q in pts))
                pts.append(p)
        for c in node.get("children", []):
            visit(c, m)

    for root in doc["scenes"][doc.get("scene", 0)]["nodes"]:
        visit(root, np.eye(4))
    out = []
    for mat, (pts, faces) in by_mat.items():
        p = np.vstack(pts) * 1000.0
        p = np.column_stack([p[:, 0], -p[:, 2], p[:, 1]])        # Y-up metres -> z-up mm
        info = doc["materials"][mat] if mat >= 0 else {}
        rgba = info.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.6, 0.6, 0.6, 1.0])
        out.append((p, np.vstack(faces), tuple(rgba[:3]), info.get("name", "")))
    return out
