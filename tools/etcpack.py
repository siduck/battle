import io
import json
import os
import struct
import sys

sys.path.insert(0, os.environ.get("PYLIB", os.path.expanduser("~/.cache/battle/pylib")))

import etcpak
from PIL import Image


def glb(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    doc = json.loads(b[20 : 20 + n])

    return doc, b[20 + n + 8 :]


def image_bytes(doc, blob, index):
    view = doc["bufferViews"][doc["images"][index]["bufferView"]]
    start = view.get("byteOffset", 0)

    return blob[start : start + view["byteLength"]]


def levels(im):
    out = [im]

    while min(out[-1].size) > 4:
        w, h = out[-1].size
        out.append(out[-1].resize((max(4, w // 2), max(4, h // 2)), Image.LANCZOS))

    return out


def encode(im, alpha):
    w, h = im.size
    data = im.tobytes()

    if alpha:
        return etcpak.compress_etc2_rgba(data, w, h)

    return etcpak.compress_etc2_rgb(data, w, h)


def pack(path):
    doc, blob = glb(path)
    stem = path[:-4]
    written = 0

    for i, mat in enumerate(doc.get("materials", [])):
        tex = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture")

        if tex is None:
            continue

        source = doc["textures"][tex["index"]]["source"]
        im = Image.open(io.BytesIO(image_bytes(doc, blob, source))).convert("RGBA")
        w, h = im.size

        if w % 4 or h % 4 or w & (w - 1) or h & (h - 1):
            continue

        alpha = im.getextrema()[3][0] < 255
        chain = levels(im)
        out = bytearray(b"DFE2")
        out += struct.pack("<HHBB", w, h, len(chain), 1 if alpha else 0)

        for level in chain:
            data = encode(level, alpha)
            out += struct.pack("<I", len(data)) + data

        open(f"{stem}.m{i + 1}.etc", "wb").write(out)
        written += 1

    return written


total = 0

for arg in sys.argv[1:]:
    paths = [os.path.join(arg, f) for f in sorted(os.listdir(arg)) if f.endswith(".glb")] if os.path.isdir(arg) else [arg]

    for p in paths:
        total += pack(p)

print("ETC", total)
