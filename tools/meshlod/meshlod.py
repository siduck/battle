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


class Stream(ctypes.Structure):
    _fields_ = [("data", ctypes.c_void_p), ("size", ctypes.c_size_t), ("stride", ctypes.c_size_t)]


SZ = ctypes.c_size_t
VP = ctypes.c_void_p

LIB.meshopt_generateVertexRemapMulti.restype = SZ
LIB.meshopt_generateVertexRemapMulti.argtypes = [U32P, U32P, SZ, SZ, ctypes.POINTER(Stream), SZ]
LIB.meshopt_generateVertexRemap.restype = SZ
LIB.meshopt_generateVertexRemap.argtypes = [U32P, U32P, SZ, VP, SZ, SZ]
LIB.meshopt_simplifyWithAttributes.restype = SZ
LIB.meshopt_simplifyWithAttributes.argtypes = [U32P, U32P, SZ, F32P, SZ, SZ, F32P, SZ, F32P, SZ, VP, SZ, ctypes.c_float, ctypes.c_uint, F32P]
LIB.meshopt_generatePositionRemap.restype = None
LIB.meshopt_generatePositionRemap.argtypes = [U32P, F32P, SZ, SZ]
LIB.meshopt_optimizeVertexCache.restype = None
LIB.meshopt_optimizeVertexCache.argtypes = [U32P, U32P, SZ, SZ]
LIB.meshopt_optimizeVertexFetch.restype = SZ
LIB.meshopt_optimizeVertexFetch.argtypes = [VP, U32P, SZ, VP, SZ, SZ]

ERROR_ABSOLUTE = 1 << 2
PRUNE = 1 << 3
PERMISSIVE = 1 << 5
PROTECT = 1 << 1
PAINT_EDGE = float(os.environ.get("PAINT_EDGE", "0.12"))
CREASE = float(os.environ.get("CREASE", "38"))
COLOR_WEIGHT = float(os.environ.get("COLOR_WEIGHT", "0.05"))
ERRORS = tuple(float(e) for e in os.environ.get("LOD_ERRORS", "0.01 0.04").split())

COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


def ptr(a, t):
    return a.ctypes.data_as(t)


def read_glb(path):
    data = open(path, "rb").read()
    magic, _, total = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67
    off = 12
    doc = None
    blob = b""

    while off < total:
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
    stride = view.get("byteStride", 0) or np.dtype(dtype).itemsize * width
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.frombuffer(blob, dtype=np.uint8, count=stride * (count - 1) + np.dtype(dtype).itemsize * width, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(count, stride), strides=(stride, 1)) if count > 0 else raw.reshape(0, stride)
    out = np.ascontiguousarray(rows[:, : np.dtype(dtype).itemsize * width]).view(dtype).reshape(count, width)

    if acc.get("normalized") and acc["componentType"] in NORM:
        return out.astype(np.float32) / NORM[acc["componentType"]]

    return out.astype(np.float32) if dtype == np.float32 or acc["type"] != "SCALAR" else out


def node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T

    t = np.array(node.get("translation", [0, 0, 0]), dtype=np.float64)
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = np.array(node.get("scale", [1, 1, 1]), dtype=np.float64)
    r = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t

    return m


def gather(doc, blob):
    pos, nrm, col, idx = [], [], [], []
    base = 0
    roots = doc["scenes"][doc.get("scene", 0)]["nodes"]
    stack = [(n, np.eye(4)) for n in roots]

    while stack:
        ni, parent = stack.pop()
        node = doc["nodes"][ni]
        world = parent @ node_matrix(node)

        for c in node.get("children", []):
            stack.append((c, world))

        if "mesh" not in node:
            continue

        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode", 4) != 4:
                continue

            a = prim["attributes"]
            p = accessor(doc, blob, a["POSITION"])[:, :3].astype(np.float64)
            n = accessor(doc, blob, a["NORMAL"])[:, :3].astype(np.float64) if "NORMAL" in a else np.zeros_like(p)
            count = len(p)
            c = accessor(doc, blob, a["COLOR_0"]) if "COLOR_0" in a else np.ones((count, 4), np.float32)

            if c.shape[1] == 3:
                c = np.hstack([c, np.ones((count, 1), np.float32)])

            mat = doc["materials"][prim["material"]] if "material" in prim and "materials" in doc else {}
            factor = np.array(mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1]), dtype=np.float32)
            c = c * factor
            pw = (world @ np.hstack([p, np.ones((count, 1))]).T).T[:, :3]
            nw = (np.linalg.inv(world[:3, :3]).T @ n.T).T
            length = np.linalg.norm(nw, axis=1, keepdims=True)
            nw = nw / np.where(length > 0, length, 1)
            i = accessor(doc, blob, prim["indices"]).reshape(-1).astype(np.uint32) if "indices" in prim else np.arange(count, dtype=np.uint32)

            pos.append(pw)
            nrm.append(nw)
            col.append(c)
            idx.append(i + base)
            base += count

    return (
        np.ascontiguousarray(np.vstack(pos), dtype=np.float32),
        np.ascontiguousarray(np.vstack(nrm), dtype=np.float32),
        np.ascontiguousarray(np.clip(np.vstack(col), 0, 1), dtype=np.float32),
        np.ascontiguousarray(np.concatenate(idx), dtype=np.uint32),
    )


def is_flat(pos, nrm, idx):
    tri = idx.reshape(-1, 3)
    face = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    length = np.linalg.norm(face, axis=1, keepdims=True)
    face = face / np.where(length > 0, length, 1)
    dots = np.einsum("ij,ikj->ik", face, nrm[tri])

    return np.mean(dots > 0.995) > 0.97


def weld(pos, col, idx):
    remap = np.zeros(len(pos), np.uint32)
    q = np.ascontiguousarray(np.round(col * 255).astype(np.float32))
    streams = (Stream * 2)(Stream(pos.ctypes.data, 12, 12), Stream(q.ctypes.data, 16, 16))
    unique = LIB.meshopt_generateVertexRemapMulti(ptr(remap, U32P), ptr(idx, U32P), len(idx), len(pos), streams, 2)
    first = np.full(unique, -1, np.int64)
    order = np.arange(len(pos))
    first[remap[::-1]] = order[::-1]

    return remap[idx], first


def protect_flags(pos, col):
    remap = np.zeros(len(pos), np.uint32)
    LIB.meshopt_generatePositionRemap(ptr(remap, U32P), ptr(pos, F32P), len(pos), 12)
    hi = np.full((len(pos), 3), -1.0, np.float32)
    lo = np.full((len(pos), 3), 2.0, np.float32)
    np.maximum.at(hi, remap, col[:, :3])
    np.minimum.at(lo, remap, col[:, :3])
    spread = (hi - lo).max(axis=1)[remap]

    return np.ascontiguousarray(np.where(spread > PAINT_EDGE, PROTECT, 0).astype(np.uint8))


def simplify(pos, col, idx, target, error, lock=None):
    out = np.zeros(len(idx), np.uint32)
    attrs = np.ascontiguousarray(col[:, :3], dtype=np.float32)
    weights = np.full(3, COLOR_WEIGHT, np.float32)
    result = ctypes.c_float(0)
    options = ERROR_ABSOLUTE | PRUNE | (PERMISSIVE if lock is not None else 0)
    n = LIB.meshopt_simplifyWithAttributes(
        ptr(out, U32P), ptr(idx, U32P), len(idx), ptr(pos, F32P), len(pos), 12,
        ptr(attrs, F32P), 12, ptr(weights, F32P), 3, lock.ctypes.data if lock is not None else None,
        target, ctypes.c_float(error), options, ctypes.pointer(result),
    )

    return out[:n].copy(), float(result.value)


def crease_normals(pos, tri):
    face = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    length = np.linalg.norm(face, axis=1, keepdims=True)
    unit = face / np.where(length > 0, length, 1)
    keys = np.round(pos[tri].reshape(-1, 3) * 1e5).astype(np.int64)
    _, group = np.unique(keys, axis=0, return_inverse=True)
    group = group.reshape(-1)
    owner = np.repeat(np.arange(len(tri)), 3)
    order = np.argsort(group, kind="stable")
    bounds = np.flatnonzero(np.diff(group[order])) + 1
    cos = np.cos(np.radians(CREASE))
    out = np.repeat(unit, 3, axis=0).copy()

    for members in np.split(order, bounds):
        if len(members) < 2:
            continue

        faces = owner[members]
        fn = unit[faces]
        fw = face[faces]
        close = (fn @ fn.T) >= cos
        summed = close.astype(np.float64) @ fw
        norm = np.linalg.norm(summed, axis=1, keepdims=True)
        out[members] = summed / np.where(norm > 0, norm, 1)

    return out


def build_render(pos, nrm, col, idx, flat, src_of):
    tri = idx.reshape(-1, 3)

    if flat:
        p = pos[tri].reshape(-1, 3)
        face = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
        length = np.linalg.norm(face, axis=1, keepdims=True)
        face = face / np.where(length > 0, length, 1)
        n = np.repeat(face, 3, axis=0)
    else:
        p = pos[tri].reshape(-1, 3)
        n = crease_normals(pos, tri)

    c = col[tri].reshape(-1, 4)
    key = np.ascontiguousarray(np.hstack([p, np.round(n * 1000) / 1000, np.round(c * 255)]).astype(np.float32))
    remap = np.zeros(len(key), np.uint32)
    seq = np.arange(len(key), dtype=np.uint32)
    unique = LIB.meshopt_generateVertexRemap(ptr(remap, U32P), ptr(seq, U32P), len(seq), key.ctypes.data, len(key), key.shape[1] * 4)
    first = np.zeros(unique, np.int64)
    first[remap[::-1]] = np.arange(len(key))[::-1]
    out_idx = np.ascontiguousarray(remap.astype(np.uint32))
    opt = np.zeros_like(out_idx)
    LIB.meshopt_optimizeVertexCache(ptr(opt, U32P), ptr(out_idx, U32P), len(out_idx), unique)
    vp = np.ascontiguousarray(p[first], np.float32)
    vn = np.ascontiguousarray(n[first], np.float32)
    vc = np.ascontiguousarray(c[first], np.float32)
    packed = np.ascontiguousarray(np.hstack([vp, vn, vc]).astype(np.float32))
    fetched = np.zeros_like(packed)
    count = LIB.meshopt_optimizeVertexFetch(fetched.ctypes.data, ptr(opt, U32P), len(opt), packed.ctypes.data, unique, packed.shape[1] * 4)

    return fetched[:count, :3], fetched[:count, 3:6], fetched[:count, 6:10], opt


def pad4(b, fill=b"\0"):
    return b + fill * ((4 - len(b) % 4) % 4)


def write_glb(path, pos, nrm, col, idx, material):
    assert len(pos) <= 65535
    cu8 = np.round(np.clip(col, 0, 1) * 255).astype(np.uint8)
    chunks = [pos.astype(np.float32).tobytes(), nrm.astype(np.float32).tobytes(), cu8.tobytes(), idx.astype(np.uint16).tobytes()]
    views, blob = [], b""

    for i, chunk in enumerate(chunks):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(chunk), "target": 34963 if i == 3 else 34962})
        blob = pad4(blob + chunk)

    doc = {
        "asset": {"version": "2.0", "generator": "dronefire meshlod"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [material],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(pos), "type": "VEC3", "min": pos.min(0).tolist(), "max": pos.max(0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": len(pos), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "normalized": True, "count": len(pos), "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": len(idx), "type": "SCALAR"},
        ],
    }
    js = pad4(json.dumps(doc, separators=(",", ":")).encode(), b" ")
    total = 12 + 8 + len(js) + 8 + len(blob)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)


def process(path):
    doc, blob = read_glb(path)
    pos, nrm, col, idx = gather(doc, blob)
    flat = is_flat(pos, nrm, idx)
    welded, src_of = weld(pos, col, idx)
    wpos = np.ascontiguousarray(pos[src_of], np.float32)
    wcol = np.ascontiguousarray(col[src_of], np.float32)
    lock = protect_flags(wpos, wcol)
    material = {"name": "kit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}
    stem = path[:-4]
    base_tris = len(idx) // 3
    current = welded
    total_error = 0.0
    report = [f"{os.path.basename(stem)} {base_tris}"]
    errors = []

    if os.environ.get("REBASE"):
        bp, bn, bc, bi = build_render(wpos, nrm, wcol, welded, flat, src_of)
        write_glb(path, bp, bn, bc, bi, material)

    for level, budget in enumerate(ERRORS, 1):
        simplified, error = simplify(wpos, wcol, welded, 3, budget, lock)

        if len(simplified) == 0 or len(simplified) >= len(current) * 0.8:
            continue

        total_error = max(error, total_error)
        current = simplified
        rp, rn, rc, ri = build_render(wpos, nrm, wcol, current, flat, src_of)
        write_glb(f"{stem}.lod{len(errors) + 1}.glb", rp, rn, rc, ri, material)
        errors.append(total_error)
        report.append(f"L{len(errors)} {len(current) // 3} tris {total_error * 100:.1f}cm")

    for level in range(len(errors) + 1, len(ERRORS) + 1):
        if os.path.exists(f"{stem}.lod{level}.glb"):
            os.remove(f"{stem}.lod{level}.glb")

    if os.environ.get("LOD0"):
        rp, rn, rc, ri = build_render(wpos, nrm, wcol, welded, flat, src_of)
        write_glb(path, rp, rn, rc, ri, material)
        report.append(f"L0 {len(ri) // 3}")

    with open(f"{stem}.lods", "w") as f:
        f.write(" ".join(f"{e:.5f}" for e in errors) + "\n")

    print(" ".join(report) + (" flat" if flat else " smooth"))


for p in sys.argv[1:]:
    process(p)
