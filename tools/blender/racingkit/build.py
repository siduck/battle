import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import buildings
import ck
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.environ.get("OUT") or os.path.join(ROOT, "src", "client", "assets", "props", "racing")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
ERRORS = (0.012, 0.055)

REG = {}

for name in ("buildings", "track", "street", "nature"):
    if os.path.exists(os.path.join(HERE, name + ".py")):
        REG.update(__import__(name).ALL)

ZIG = open(os.path.join(ROOT, "src", "shared", "maps", "racing_kit.zig")).read()
BOUNDS = {m[0]: ([float(v) for v in m[1].split(",")], [float(v) for v in m[2].split(",")]) for m in re.findall(r'"racing/(\w+)\.glb".*?\.min = \.\{(.*?)\}, \.max = \.\{(.*?)\}', ZIG)}
BLOCKS = {m[0]: [[float(v) for v in b.split(",")] for b in re.findall(r"\.\{ ([^{}]+) \}", m[1])] for m in re.findall(r"kit\.of\(\.(\w+)\).*blocks = &\.\{(.*)\} \},", ZIG)}


def footings(name):
    out = ck.Part()

    for x0, z0, x1, z1, _ in BLOCKS.get(name, []):
        a, b, c, d = x0 + 0.02, -z1 + 0.02, x1 - 0.02, -z0 - 0.02

        for f in ck.box(a, b, -1.5, c, d, 0.0, "footing", skip="d", ao=False, cast=False, d=9):
            if f.normal().z < 0.5:
                out.append(f)

    return out


def audit(name, polys, tree):
    owners = [p for p in polys if p.cast]

    if not owners:
        return

    pts = [p for f in owners for p in f.pts]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    mid = (lo + hi) / 2
    radius = (hi - lo).length / 2 + 1
    step = max(0.04, radius / 130)
    hits = {}
    total = 0

    for k in range(16):
        ang = 2 * math.pi * k / 16 + 0.11
        for el in (0.04, 0.5):
            d = Vector((math.cos(ang) * math.cos(el), math.sin(ang) * math.cos(el), math.sin(el)))
            t, bt = ck.basis(d)
            n = int(radius / step)

            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    start = mid + d * radius * 2 + t * (i * step) + bt * (j * step)

                    if abs((start - mid).dot(t)) > radius:
                        continue

                    loc, nor, idx, dist = tree.ray_cast(start, -d, radius * 4)

                    if loc is None or loc.z < 0.05:
                        continue

                    total += 1

                    if owners[idx].normal().dot(d) < -0.12:
                        hits[idx] = hits.get(idx, 0) + 1

    worst = sorted(hits.items(), key=lambda kv: -kv[1])[:5]
    share = sum(hits.values()) / max(total, 1)

    if share > 0.002:
        out = []

        for idx, count in worst:
            f = owners[idx]
            c = f.center()
            out.append((count, tuple(round(v, 2) for v in c), tuple(round(v, 1) for v in f.normal()), tuple(round(v, 2) for v in f.col)))

        print("BUILT_AUDIT %s %.2f%%" % (name, share * 100), out, flush=True)


def build(name, fn, opts):
    ck.LOD = 0
    full = ck.join([fn(), footings(name)])
    tree = ck.tree_of(full)

    if os.environ.get("AUDIT"):
        audit(name, full, tree)

    levels = [0, 1, 2] if opts.get("lods", True) else [0]
    stats = []

    for lod in levels:
        ck.LOD = lod
        polys = full if lod == 0 else ck.join([fn(), footings(name)])
        own = tree if lod == 0 else ck.tree_of(polys)
        baker = ck.Baker(own, opts)
        polys = ck.cull(polys, own, opts.get("ground", True))
        data, index = ck.render_mesh(polys, baker, opts)
        suffix = "" if lod == 0 else ".lod%d" % lod
        path = os.path.join(OUT, name + suffix + ".glb")

        if lod and len(index) // 3 > stats[-1][0] * 0.82:
            break

        mn, mx = ck.write_glb(path, data, index)
        stats.append((len(index) // 3, os.path.getsize(path), mn, mx))

    for lod in range(len(stats), 3):
        stale = os.path.join(OUT, name + ".lod%d.glb" % lod)

        if lod and os.path.exists(stale):
            os.remove(stale)

    for stale in (name + ".lod.glb", name + ".lods"):
        if os.path.exists(os.path.join(OUT, stale)):
            os.remove(os.path.join(OUT, stale))

    if len(stats) > 1:
        with open(os.path.join(OUT, name + ".lods"), "w") as f:
            f.write(" ".join("%.5f" % e for e in opts.get("errors", ERRORS)[:len(stats) - 1]) + "\n")

    mn, mx = stats[0][2], stats[0][3]
    info = {"tris": [s[0] for s in stats], "bytes": sum(s[1] for s in stats), "min": [round(v, 3) for v in mn], "max": [round(v, 3) for v in mx]}
    lo, hi = BOUNDS[name]
    glo = (mn[0], mn[1], mn[2])
    ghi = (mx[0], mx[1], mx[2])
    off = []

    for i, axis in enumerate("xyz"):
        for tag, got, want in (("lo", glo[i], lo[i]), ("hi", ghi[i], hi[i])):
            if name in BLOCKS and i == 1 and tag == "lo":
                continue

            if abs(got - want) > max(0.12, 0.02 * (hi[i] - lo[i])):
                off.append("%s%s %.2f/%.2f" % (axis, tag, got, want))

    print("BUILT", name, info["tris"], info["bytes"], " ".join(off), flush=True)

    return info


os.makedirs(OUT, exist_ok=True)

for name, (fn, opts) in REG.items():
    if ONLY and name not in ONLY:
        continue

    build(name, fn, opts)
