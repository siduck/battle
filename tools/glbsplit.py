#!/usr/bin/env python3
import json
import struct
import sys

LIMIT = 65535
CELLS = 1666
SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def split(path):
    with open(path, "rb") as f:
        data = f.read()

    n = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + n])
    blob = data[28 + n:]
    views = doc["bufferViews"]
    accessors = doc["accessors"]

    if doc.get("animations") or doc.get("skins"):
        sys.exit(f"{path}: skinned or animated models are not handled")

    def elements(i):
        a = accessors[i]
        v = views[a["bufferView"]]
        size = SIZE[a["componentType"]] * WIDTH[a["type"]]
        stride = v.get("byteStride", size)
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)

        return [blob[start + k * stride:start + k * stride + size] for k in range(a["count"])]

    out = bytearray()
    new_views = []
    new_accessors = []

    def view(payload, extra):
        out.extend(b"\0" * (-len(out) % 4))
        new_views.append({"buffer": 0, "byteOffset": len(out), "byteLength": len(payload), **extra})
        out.extend(payload)

        return len(new_views) - 1

    def accessor(old, payload, count, extra):
        a = {k: v for k, v in accessors[old].items() if k not in ("bufferView", "byteOffset", "count", "min", "max")}
        a.update(bufferView=view(payload, extra), count=count)

        if "min" in accessors[old]:
            width = WIDTH[a["type"]]
            fmt = "<%d%s" % (width, {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[a["componentType"]])
            rows = list(struct.iter_unpack(fmt, payload if extra.get("byteStride") is None else b"".join(payload[k:k + struct.calcsize(fmt)] for k in range(0, len(payload), extra["byteStride"]))))
            a.update(min=[min(c) for c in zip(*rows)], max=[max(c) for c in zip(*rows)])

        new_accessors.append(a)

        return len(new_accessors) - 1

    for image in doc.get("images", []):
        if "bufferView" in image:
            v = views[image["bufferView"]]
            start = v.get("byteOffset", 0)
            image["bufferView"] = view(blob[start:start + v["byteLength"]], {})

    for mesh in doc["meshes"]:
        result = []

        for prim in mesh["primitives"]:
            if "targets" in prim or prim.get("mode", 4) != 4 or "indices" not in prim:
                sys.exit(f"{path}: only indexed triangle lists are handled")

            columns = {name: elements(i) for name, i in prim["attributes"].items()}
            code = {1: "B", 2: "H", 4: "I"}[SIZE[accessors[prim["indices"]]["componentType"]]]
            indices = [struct.unpack("<" + code, e)[0] for e in elements(prim["indices"])]
            positions = columns["POSITION"]
            parent = list(range(len(positions)))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]

                return x

            def join(x, y):
                parent[find(x)] = find(y)

            if accessors[prim["attributes"]["POSITION"]]["componentType"] != 5126:
                sys.exit(f"{path}: only float positions are handled")

            points = [struct.unpack("<3f", p) for p in positions]
            span = max(max(c) - min(c) for c in zip(*points))
            first = {}

            for k, p in enumerate(points):
                join(k, first.setdefault(tuple(round(c / span * CELLS) for c in p), k))

            for t in range(0, len(indices), 3):
                join(indices[t], indices[t + 1])
                join(indices[t], indices[t + 2])

            sizes = {}

            for k in range(len(positions)):
                root = find(k)
                sizes[root] = sizes.get(root, 0) + 1

            bins = []
            home = {}

            for root, size in sorted(sizes.items(), key=lambda s: -s[1]):
                if size > LIMIT:
                    sys.exit(f"{path}: one connected part has {size} vertices, splitting would leave a seam")

                slot = next((i for i, used in enumerate(bins) if used + size <= LIMIT), len(bins))

                if slot == len(bins):
                    bins.append(0)

                bins[slot] += size
                home[root] = slot

            for slot in range(len(bins)):
                remap = {}
                local = []

                for t in range(0, len(indices), 3):
                    if home[find(indices[t])] != slot:
                        continue

                    for k in indices[t:t + 3]:
                        local.append(remap.setdefault(k, len(remap)))

                attributes = {}

                for name, old in prim["attributes"].items():
                    size = len(columns[name][0])
                    stride = size + -size % 4
                    payload = b"".join(columns[name][k] + b"\0" * (stride - size) for k in remap)
                    attributes[name] = accessor(old, payload, len(remap), {"byteStride": stride, "target": 34962})

                a = {"bufferView": view(struct.pack("<%dH" % len(local), *local), {"target": 34963}), "componentType": 5123, "count": len(local), "type": "SCALAR"}
                new_accessors.append(a)
                result.append({**prim, "attributes": attributes, "indices": len(new_accessors) - 1})

            print(f"{path}: {len(positions)} vertices -> {bins}")

        mesh["primitives"] = result

    out.extend(b"\0" * (-len(out) % 4))
    doc.update(bufferViews=new_views, accessors=new_accessors, buffers=[{"byteLength": len(out)}])
    text = json.dumps(doc, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)

    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 28 + len(text) + len(out)))
        f.write(struct.pack("<I4s", len(text), b"JSON") + text)
        f.write(struct.pack("<I4s", len(out), b"BIN\0") + bytes(out))


for target in sys.argv[1:]:
    split(target)
