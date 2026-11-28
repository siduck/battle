import json
import os
import struct
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fr_buildings
import fr_kit
import fr_props

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.environ.get("OUT") or os.path.join(ROOT, "src", "client", "assets", "props", "frontier")
ZIG = os.path.join(ROOT, "src", "shared", "maps", "desert_kit.zig")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]

HOUSE = dict(ao=0.55, reach=1.5, dust=0.24, dust_h=1.1, bias=0.065)
PROP = dict(ao=0.5, reach=0.6, dust=0.2, dust_h=0.5)
ROCK = dict(ao=0.42, reach=1.1, dust=0.38, dust_h=0.7)
PLANT = dict(ao=0.42, reach=0.5, dust=0.14, dust_h=0.4)

STYLE = {
    "watertower": dict(ao=0.5, reach=1.2, dust=0.2, dust_h=0.8),
    "headframe": dict(ao=0.5, reach=1.2, dust=0.22, dust_h=1.0),
    "orebin": dict(ao=0.55, reach=1.0, dust=0.22, dust_h=0.8),
    "windmill": dict(ao=0.5, reach=0.9, dust=0.2, dust_h=0.8),
    "rock_0": ROCK,
    "rock_1": ROCK,
    "rock_2": ROCK,
    "rock_3": ROCK,
    "rock_4": ROCK,
    "pillar": ROCK,
    "spoil": ROCK,
    "mesa_0": dict(ao=0.4, reach=5.0, dust=0.36, dust_h=6.0, lift=(0.98, 1.06), dust_tone=0.95),
    "mesa_1": dict(ao=0.4, reach=5.0, dust=0.36, dust_h=6.0, lift=(0.98, 1.06), dust_tone=0.95),
    "mesa_2": dict(ao=0.4, reach=5.0, dust=0.36, dust_h=6.0, lift=(0.98, 1.06), dust_tone=0.95),
    "saguaro": PLANT,
    "cactus": PLANT,
    "pear": PLANT,
    "sage": PLANT,
    "deadtree": dict(ao=0.45, reach=0.8, dust=0.2, dust_h=0.8),
    "tumbleweed": dict(ao=0.3, reach=0.3, dust=0.0, dust_h=0.4),
    "gravel": dict(ao=0.25, reach=0.3, dust=0.2, dust_h=0.2),
    "walk": dict(ao=0.3, reach=0.35, dust=0.1, dust_h=0.4, lift=(0.95, 1.02)),
    "drift": dict(ao=0.12, reach=0.5, dust=0.0, dust_h=0.4, lift=(0.99, 1.01)),
}

KINDS = [
    ("house_0", "none", "building"),
    ("house_1", "none", "building"),
    ("house_3", "none", "building"),
    ("house_4", "none", "building"),
    ("house_6", "none", "building"),
    ("house_7", "none", "building"),
    ("house_8", "none", "building"),
    ("house_10", "none", "building"),
    ("house_11", "none", "building"),
    ("barrel", "box", "street"),
    ("crate", "box", "street"),
    ("box", "box", "street"),
    ("chest", "box", "street"),
    ("bench", "box", "street"),
    ("fence", "box", "street"),
    ("lantern", "cylinder", "street"),
    ("pole", "cylinder", "street"),
    ("watertower", "box", "building"),
    ("headframe", "box", "building"),
    ("orebin", "box", "building"),
    ("windmill", "box", "building"),
    ("rock_0", "box", "rock"),
    ("rock_1", "box", "rock"),
    ("rock_2", "box", "rock"),
    ("rock_3", "box", "rock"),
    ("rock_4", "box", "rock"),
    ("pillar", "box", "building"),
    ("mesa_0", "box", "rock"),
    ("mesa_1", "box", "rock"),
    ("mesa_2", "box", "rock"),
    ("saguaro", "trunk", "tree"),
    ("deadtree", "trunk", "tree"),
    ("cactus", "cylinder", "bush"),
    ("pear", "cylinder", "bush"),
    ("sage", "none", "bush"),
    ("tumbleweed", "none", "ground"),
    ("gravel", "none", "ground"),
    ("walk", "none", "ground"),
    ("drift", "none", "rock"),
    ("spoil", "box", "building"),
]


def write_glb(path, tris):
    lookup = {}
    pos, nrm = array("f"), array("f")
    col = bytearray()
    idx = array("H")
    lo = [1e9] * 3
    hi = [-1e9] * 3

    for p, n, cols in tris:
        gn = (n.x, n.z, -n.y)

        for v, c in zip(p, cols):
            g = (v.x, v.z, -v.y)
            rgba = (round(c[0] * 255), round(c[1] * 255), round(c[2] * 255), 255)
            key = (round(g[0], 4), round(g[1], 4), round(g[2], 4), round(gn[0], 3), round(gn[1], 3), round(gn[2], 3), rgba)
            at = lookup.get(key)

            if at is None:
                at = len(lookup)
                lookup[key] = at
                pos.extend(g)
                nrm.extend(gn)
                col.extend(rgba)

                for i in range(3):
                    lo[i] = min(lo[i], g[i])
                    hi[i] = max(hi[i], g[i])

            idx.append(at)

    count = len(lookup)
    assert count <= 65535
    lo = [array("f", [v])[0] for v in lo]
    hi = [array("f", [v])[0] for v in hi]
    chunks = [pos.tobytes(), nrm.tobytes(), bytes(col), idx.tobytes()]
    views, blob = [], b""

    for i, chunk in enumerate(chunks):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(chunk), "target": 34963 if i == 3 else 34962})
        blob += chunk + b"\0" * ((4 - len(chunk) % 4) % 4)

    doc = {
        "asset": {"version": "2.0", "generator": "dronefire frontier"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"name": "kit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": count, "type": "VEC3", "min": lo, "max": hi},
            {"bufferView": 1, "componentType": 5126, "count": count, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "normalized": True, "count": count, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": len(idx), "type": "SCALAR"},
        ],
    }
    js = json.dumps(doc, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(blob)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)

    return {"tris": len(idx) // 3, "min": lo, "max": hi}


def zig_table(info):
    f3 = lambda v: ".{ %.3f, %.3f, %.3f }" % tuple(v)
    lines = ['const api = @import("api.zig");', "", "pub const K = enum {"]
    lines += ["    %s," % name for name, _, _ in KINDS]
    lines += ["};", "", "pub const kit = api.Kit(K);", "", "pub const table = [_]api.Info{"]

    for name, collide, group in KINDS:
        i = info[name]
        lines.append('    .{ .file = "frontier/%s.glb", .scale = 1.00, .collide = .%s, .group = .%s, .foliage = false, .min = %s, .max = %s },' % (name, collide, group, f3(i["min"]), f3(i["max"])))

    lines += ["};", "", "pub fn blocks(e: K) []const [5]f32 {", "    return switch (e) {"]

    for name, _, _ in KINDS:
        if not name.startswith("house_"):
            continue

        rows = ", ".join(".{ %.2f, %.2f, %.2f, %.2f, %.2f }" % (b[0], -b[3], b[2], -b[1], b[4]) for b in info[name]["blocks"])
        lines.append("        .%s => &.{ %s }," % (name, rows))

    lines += ["        else => &.{},", "    };", "}", ""]

    with open(ZIG, "w") as f:
        f.write("\n".join(lines))


def main():
    os.makedirs(OUT, exist_ok=True)
    registry = dict(fr_buildings.ALL)
    registry.update(fr_props.ALL)
    cache = os.path.join(os.environ.get("INFO", OUT + "/.."), "frontier_info.json")
    info = {}

    if os.path.exists(cache):
        with open(cache) as f:
            info = json.load(f)

    for name, _, _ in KINDS:
        if ONLY and name not in ONLY:
            continue

        mesh = registry[name]()
        style = HOUSE if name.startswith("house_") else STYLE.get(name, PROP)
        tris = fr_kit.finalize(mesh, **style)
        entry = write_glb(os.path.join(OUT, name + ".glb"), tris)
        entry["blocks"] = mesh.blocks
        info[name] = entry
        size = [round(entry["max"][i] - entry["min"][i], 2) for i in range(3)]
        print("BUILT", name, entry["tris"], size, [round(v, 2) for v in entry["min"]], [round(v, 2) for v in entry["max"]])

    with open(cache, "w") as f:
        json.dump(info, f)

    if all(name in info for name, _, _ in KINDS):
        zig_table(info)

    print("TOTAL", sum(i["tris"] for i in info.values()), len(info))


main()
