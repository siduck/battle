import ctypes
import json
import os
import struct
import sys

sys.path.insert(0, os.path.expanduser("~/.cache/battle/bpylib"))

import numpy as np

LIB = ctypes.CDLL(os.environ["MESHOPT_LIB"])
F32P = ctypes.POINTER(ctypes.c_float)
U32P = ctypes.POINTER(ctypes.c_uint)
SZ = ctypes.c_size_t


class Overdraw(ctypes.Structure):
    _fields_ = [("covered", ctypes.c_uint), ("shaded", ctypes.c_uint), ("overdraw", ctypes.c_float)]


LIB.meshopt_optimizeVertexCache.restype = None
LIB.meshopt_optimizeVertexCache.argtypes = [U32P, U32P, SZ, SZ]
LIB.meshopt_optimizeOverdraw.restype = None
LIB.meshopt_optimizeOverdraw.argtypes = [U32P, U32P, SZ, F32P, SZ, SZ, ctypes.c_float]
LIB.meshopt_optimizeVertexFetchRemap.restype = SZ
LIB.meshopt_optimizeVertexFetchRemap.argtypes = [U32P, U32P, SZ, SZ]
LIB.meshopt_analyzeOverdraw.restype = Overdraw
LIB.meshopt_analyzeOverdraw.argtypes = [U32P, SZ, F32P, SZ, SZ]

COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
NORM = {5121: 255.0, 5123: 65535.0}
THRESHOLD = float(os.environ.get("OVERDRAW_THRESHOLD", "1.05"))


def ptr(a, t):
    return a.ctypes.data_as(t)


def read_glb(path):
    data = open(path, "rb").read()
    off = 12
    doc = None
    blob = b""

    while off < len(data):
        size, kind = struct.unpack_from("<II", data, off)
        chunk = data[off + 8 : off + 8 + size]

        if kind == 0x4E4F534A:
            doc = json.loads(chunk)
        elif kind == 0x004E4942:
            blob = chunk

        off += 8 + size

    return doc, blob


def accessor(doc, blob, index):
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    dtype = COMPONENT[acc["componentType"]]
    width = WIDTH[acc["type"]]
    count = acc["count"]
    item = np.dtype(dtype).itemsize * width
    stride = view.get("byteStride", 0) or item
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.frombuffer(blob, dtype=np.uint8, count=stride * (count - 1) + item, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(count, stride), strides=(stride, 1))
    out = np.ascontiguousarray(rows[:, :item]).view(dtype).reshape(count, width)

    if acc.get("normalized") and acc["componentType"] in NORM:
        return out.astype(np.float32) / NORM[acc["componentType"]]

    return out


def single(doc, blob):
    nodes = [n for n in doc["nodes"] if "mesh" in n]
    prims = [p for n in nodes for p in doc["meshes"][n["mesh"]]["primitives"]]

    if len(nodes) != 1 or len(prims) != 1 or any(k in nodes[0] for k in ("matrix", "rotation", "scale", "translation")):
        return None

    prim = prims[0]
    a = prim["attributes"]

    if set(a) - {"POSITION", "NORMAL", "COLOR_0"} or "indices" not in prim:
        return None

    pos = np.ascontiguousarray(accessor(doc, blob, a["POSITION"])[:, :3], np.float32)
    nrm = np.ascontiguousarray(accessor(doc, blob, a["NORMAL"])[:, :3], np.float32) if "NORMAL" in a else None
    col = accessor(doc, blob, a["COLOR_0"]) if "COLOR_0" in a else None

    if col is not None and col.shape[1] == 3:
        col = np.hstack([col, np.ones((len(col), 1), np.float32)])

    idx = np.ascontiguousarray(accessor(doc, blob, prim["indices"]).reshape(-1), np.uint32)
    mat = doc["materials"][prim["material"]] if "material" in prim and "materials" in doc else None

    return pos, nrm, col, idx, mat


def overdraw(pos, idx):
    return LIB.meshopt_analyzeOverdraw(ptr(idx, U32P), len(idx), ptr(pos, F32P), len(pos), 12).overdraw


def optimize(pos, idx):
    a = np.zeros_like(idx)
    LIB.meshopt_optimizeVertexCache(ptr(a, U32P), ptr(idx, U32P), len(idx), len(pos))
    b = np.zeros_like(idx)
    LIB.meshopt_optimizeOverdraw(ptr(b, U32P), ptr(a, U32P), len(a), ptr(pos, F32P), len(pos), 12, THRESHOLD)
    remap = np.zeros(len(pos), np.uint32)
    unique = LIB.meshopt_optimizeVertexFetchRemap(ptr(remap, U32P), ptr(b, U32P), len(b), len(pos))
    order = np.zeros(unique, np.int64)
    used = remap != 0xFFFFFFFF
    order[remap[used]] = np.nonzero(used)[0]

    return order, np.ascontiguousarray(remap[b], np.uint32)


def pad4(b, fill=b"\0"):
    return b + fill * ((4 - len(b) % 4) % 4)


def write_glb(path, pos, nrm, col, idx, material):
    chunks = [("POSITION", pos.astype(np.float32).tobytes(), 5126, "VEC3", False)]

    if nrm is not None:
        chunks.append(("NORMAL", nrm.astype(np.float32).tobytes(), 5126, "VEC3", False))

    if col is not None:
        chunks.append(("COLOR_0", np.round(np.clip(col, 0, 1) * 255).astype(np.uint8).tobytes(), 5121, "VEC4", True))

    wide = len(pos) > 65535
    chunks.append(("indices", idx.astype(np.uint32 if wide else np.uint16).tobytes(), 5125 if wide else 5123, "SCALAR", False))
    views, accessors, blob, attrs = [], [], b"", {}

    for i, (name, data, ctype, kind, norm) in enumerate(chunks):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": 34963 if name == "indices" else 34962})
        blob = pad4(blob + data)
        acc = {"bufferView": i, "componentType": ctype, "count": len(idx) if name == "indices" else len(pos), "type": kind}

        if norm:
            acc["normalized"] = True

        if name == "POSITION":
            acc["min"] = pos.min(0).tolist()
            acc["max"] = pos.max(0).tolist()

        accessors.append(acc)

        if name != "indices":
            attrs[name] = i

    prim = {"attributes": attrs, "indices": len(chunks) - 1}
    doc = {"asset": {"version": "2.0", "generator": "dronefire glbpack"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
           "meshes": [{"primitives": [prim]}], "buffers": [{"byteLength": len(blob)}], "bufferViews": views, "accessors": accessors}

    if material is not None:
        doc["materials"] = [material]
        prim["material"] = 0

    js = pad4(json.dumps(doc, separators=(",", ":")).encode(), b" ")

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)


def process(path, analyze):
    doc, blob = read_glb(path)
    mesh = single(doc, blob)

    if mesh is None:
        print("skip", os.path.basename(path))

        return

    pos, nrm, col, idx, mat = mesh
    before = overdraw(pos, idx)

    if analyze:
        print(f"{os.path.basename(path)} tris {len(idx) // 3} verts {len(pos)} overdraw {before:.2f}")

        return

    order, idx2 = optimize(pos, idx)
    pos2 = np.ascontiguousarray(pos[order])
    after = overdraw(pos2, idx2)
    size = os.path.getsize(path)
    write_glb(path, pos2, nrm[order] if nrm is not None else None, col[order] if col is not None else None, idx2, mat)
    print(f"{os.path.basename(path)} overdraw {before:.2f} -> {after:.2f} size {size // 1024}K -> {os.path.getsize(path) // 1024}K")


analyze = os.environ.get("ANALYZE") == "1"

for p in sys.argv[1:]:
    process(p, analyze)
