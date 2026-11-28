import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("BPYLIB") or os.path.expanduser("~/.cache/battle/bpylib"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "meshlod"))

ARGS = sys.argv[1:]
del sys.argv[1:]

import meshlod as ml
import numpy as np

os.environ.setdefault("PAINT_EDGE", "0.45")
ml.PAINT_EDGE = float(os.environ["PAINT_EDGE"])
BLEND = 0.3
COVER = ("walk", "gravel", "tumbleweed")
SMALL = ("barrel", "crate", "box", "chest", "bench", "fence", "lantern", "pole", "cactus", "pear", "sage", "saguaro", "deadtree")
LEVELS = {"house": "0.042", "small": "0.016 0.05", "mid": "0.025 0.075", "mesa": "0.1"}
SKIP_LOD = ("rock_0", "rock_4", "windmill")


def level(name):
    if name.startswith("house_"):
        return LEVELS["house"]

    if name.startswith("mesa_"):
        return LEVELS["mesa"]

    return LEVELS["small"] if name in SMALL else LEVELS["mid"]


def cluster(pos, col, idx):
    spots = {}
    remap = np.zeros(len(pos), np.uint32)
    groups = []

    for i in np.unique(idx):
        key = tuple(np.round(pos[i] * 2000).astype(np.int64))
        near = spots.setdefault(key, [])

        for g in near:
            if np.abs(col[i][:3] - groups[g][1]).max() < BLEND:
                groups[g][2].append(i)
                remap[i] = g
                break
        else:
            near.append(len(groups))
            remap[i] = len(groups)
            groups.append((i, col[i][:3].copy(), [i]))

    first = np.array([g[0] for g in groups], np.int64)
    wpos = np.ascontiguousarray(pos[first], np.float32)
    wcol = np.ascontiguousarray([col[g[2]].mean(axis=0) for g in groups], np.float32)

    return wpos, wcol, np.ascontiguousarray(remap[idx], np.uint32), first


def process(path):
    name = os.path.basename(path)[:-4]
    stem = path[:-4]
    doc, blob = ml.read_glb(path)
    pos, nrm, col, idx = ml.gather(doc, blob)
    flat = ml.is_flat(pos, nrm, idx)
    wpos, wcol, welded, src_of = cluster(pos, col, idx)
    lock = ml.protect_flags(wpos, wcol)
    material = {"name": "kit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}

    for k in (1, 2):
        if os.path.exists(f"{stem}.lod{k}.glb"):
            os.remove(f"{stem}.lod{k}.glb")

    if os.path.exists(f"{stem}.lods"):
        os.remove(f"{stem}.lods")

    report = [name, str(len(idx) // 3)]

    if name not in COVER and name not in SKIP_LOD:
        current = welded
        total = 0.0
        errors = []

        for budget in (float(e) for e in level(name).split()):
            simplified, error = ml.simplify(wpos, wcol, welded, 3, budget, lock)

            if len(simplified) == 0 or len(simplified) >= len(current) * 0.75 or len(current) < 900:
                continue

            total = max(error, total)
            current = simplified
            rp, rn, rc, ri = ml.build_render(wpos, nrm, wcol, current, True, src_of)
            ml.write_glb(f"{stem}.lod{len(errors) + 1}.glb", rp, rn, rc, ri, material)
            errors.append(total)
            report.append(f"L{len(errors)} {len(current) // 3} {total * 100:.1f}cm")

        if errors:
            with open(f"{stem}.lods", "w") as f:
                f.write(" ".join(f"{e:.5f}" for e in errors) + "\n")

    print(" ".join(report))


folder = ARGS[0]

for f in sorted(os.listdir(folder)):
    if f.endswith(".glb") and ".lod" not in f:
        process(os.path.join(folder, f))
