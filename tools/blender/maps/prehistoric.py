import os, sys, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pf
from pf import *
from mathutils.bvhtree import BVHTree

BASE_SKIP = pf.SKIP
pf.SKIP = re.compile(BASE_SKIP.pattern + r"|wisp|steam|billow", re.I)
STEAMY = {"steamspring", "steamvent"}
EXTRA = os.path.join(pf.P, "extra")
_make_prop = pf.make_prop


def make_prop_steam(name, src, **kw):
    keep = pf.SKIP
    pf.SKIP = BASE_SKIP if name in STEAMY else keep
    info = _make_prop(name, src, **kw)
    pf.SKIP = keep

    return info


pf.make_prop = make_prop_steam

SNOW = (0.9, 0.93, 0.97)
SNOWY = {}
TINT = {"karst": (0.7, 0.72, 0.62), "karst_big": (0.7, 0.72, 0.62), "arch": (0.95, 0.92, 0.86)}
RAYS = 16


def hemisphere(n):
    out = []

    for i in range(n):
        u = (i + 0.5) / n
        r = math.sqrt(u)
        a = i * 2.399963
        out.append((r * math.cos(a), r * math.sin(a), math.sqrt(1 - u)))

    return out


DIRS = hemisphere(RAYS)


def smoothstep(a, b, v):
    t = min(max((v - a) / (b - a), 0.0), 1.0)

    return t * t * (3 - 2 * t)


def snowify(bm, amount=0.95, start=0.5):
    col = bm.loops.layers.float_color["Col"]
    bm.normal_update()

    for f in bm.faces:
        k = amount * smoothstep(start, start + 0.25, f.normal.z)

        if k <= 0:
            continue

        for l in f.loops:
            c = l[col]
            l[col] = (c[0] + (SNOW[0] - c[0]) * k, c[1] + (SNOW[1] - c[1]) * k, c[2] + (SNOW[2] - c[2]) * k, 1.0)


def bake_ao(bm, strength=0.62):
    bm.normal_update()
    bm.verts.index_update()
    lo, hi = bounds(bm)
    size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    reach = min(max(size * 0.28, 0.6), 3.2)
    tree = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    cache = {}

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()

        for l in f.loops:
            key = (l.vert.index, round(n.x, 1), round(n.y, 1), round(n.z, 1))
            occ = cache.get(key)

            if occ is None:
                o = l.vert.co + (c - l.vert.co) * 0.1 + n * 0.012
                s = 0.0

                for d in DIRS:
                    w = t * d[0] + b * d[1] + n * d[2]
                    hit = tree.ray_cast(o, w, reach)
                    dist = hit[3] if hit[0] is not None else None

                    if w.z < -0.05 and o.z > 0.0:
                        g = o.z / -w.z

                        if g < reach and (dist is None or g < dist):
                            dist = g

                    if dist is not None:
                        s += 1 - dist / reach

                occ = min(s / len(DIRS) * 1.5, 1.0)
                cache[key] = occ

            k = 1 - strength * occ
            cc = l[col]
            l[col] = (cc[0] * k, cc[1] * k, cc[2] * k, 1.0)


_export = pf.export


def export_baked(bm, name):
    if name in TINT:
        tint(bm, TINT[name])

    if name in SNOWY:
        snowify(bm, start=SNOWY[name])

    bake_ao(bm)

    return _export(bm, name)


pf.export = export_baked

BUILDINGS = [
    ("arch", "cave-overhang-arch-b3ef4e", {"scale": 1.1, "plinth": None}),
    ("cave", "smuggler-cave-mouth-69a07e", {"scale": 2.6, "plinth": None}),
    ("karst", "karst-limestone-peak-ee1b76", {"scale": 2.4, "plinth": None}),
    ("karst_big", "karst-limestone-peak-ee1b76", {"scale": 3.6, "plinth": None}),
]

PROPS = [
    ("araucaria", "araucaria-monkey-puzzle-7c109d", {"group": "tree", "collide": "trunk", "scale": 0.6}),
    ("redwood", "dawn-redwood-001c29", {"group": "tree", "collide": "trunk", "scale": 0.85}),
    ("ginkgo", "ginkgo-tree-baa895", {"group": "tree", "collide": "trunk", "scale": 1.0}),
    ("cycad", "cycad-05ad50", {"group": "tree", "collide": "cylinder", "scale": 1.3}),
    ("treefern", "tree-fern-78320e", {"group": "tree", "collide": "cylinder", "scale": 1.0}),
    ("palm", "palm-tree-a307da", {"group": "tree", "collide": "cylinder", "scale": 1.5}),
    ("sapling", "palm-sapling-ef7ae4", {"group": "bush", "collide": "none", "scale": 1.4}),
    ("magnolia", "flowering-magnolia-dd76cb", {"group": "tree", "collide": "trunk", "scale": 1.1}),
    ("williamsonia", "williamsonia-7b0a4f", {"group": "tree", "collide": "cylinder", "scale": 1.3}),
    ("snag", "dead-snag-0b1891", {"group": "tree", "collide": "cylinder", "scale": 1.2}),
    ("scorched", "scorched-tree-e927a3", {"group": "tree", "collide": "trunk", "scale": 1.0}),
    ("bamboo", "bamboo-grove-clump-7c747d", {"group": "tree", "collide": "cylinder", "scale": 1.1}),
    ("horsetail", "giant-horsetail-stand-3a4f94", {"group": "bush", "collide": "cylinder", "scale": 1.0}),
    ("fern", "fern-clump-90ff4b", {"group": "ground", "collide": "none", "scale": 1.4}),
    ("shrub", "williamsoniella-flowering-shrub-dc53ae", {"group": "bush", "collide": "none", "scale": 1.5}),
    ("moss", "club-moss-mat-edcb1b", {"group": "ground", "collide": "none", "scale": 1.6}),
    ("mushroom", "giant-mushroom-cluster-868de6", {"group": "bush", "collide": "none", "scale": 1.6}),
    ("litter", "ginkgo-leaf-litter-9784e9", {"group": "ground", "collide": "none", "scale": 2.0}),
    ("lotus", "lotus-flower-cluster-bc129a", {"group": "ground", "collide": "none", "scale": 1.4}),
    ("lilies", "lily-pad-cluster-457382", {"group": "ground", "collide": "none", "scale": 1.5}),
    ("reeds", "river-reed-cluster-cba87e", {"group": "bush", "collide": "none", "scale": 1.3}),
    ("hollow", "hollow-log-329fd7", {"group": "street", "collide": "box", "scale": 1.6}),
    ("fungus", "bracket-fungus-log-2deef4", {"group": "street", "collide": "box", "scale": 1.2}),
    ("petrified", "petrified-log-413693", {"group": "street", "collide": "box", "scale": 2.4}),
    ("stump", "moss-covered-stump-7253ab", {"group": "street", "collide": "cylinder", "scale": 1.6}),
    ("driftwood", "driftwood-wrack-pile-a505a5", {"group": "street", "collide": "none", "scale": 1.3}),
    ("columns", "basalt-column-outcrop-f1339d", {"group": "rock", "collide": "box", "scale": 2.2}),
    ("fernrock", "fern-covered-boulder-2e0375", {"group": "rock", "collide": "box", "scale": 2.0}),
    ("volcanic", "volcanic-boulder-cluster-7e29ea", {"group": "rock", "collide": "box", "scale": 2.2}),
    ("lavapile", "lava-rock-pile-d56d19", {"group": "rock", "collide": "box", "scale": 1.8}),
    ("obsidian", "obsidian-shard-cluster-c8f5d3", {"group": "street", "collide": "box", "scale": 1.6}),
    ("geode", "mineral-geode-cluster-299927", {"group": "street", "collide": "box", "scale": 1.5}),
    ("stones", "river-stone-cluster-0b55bc", {"group": "ground", "collide": "none", "scale": 1.6}),
    ("scoria", "red-scoria-rock-35bb9c", {"group": "rock", "collide": "box", "scale": 3.0}),
    ("basalt", "basalt-boulder-a1929c", {"group": "rock", "collide": "box", "scale": 3.0}),
    ("boulder", "large-coastal-boulder-a2cab1", {"group": "rock", "collide": "box", "scale": 2.2, "k": (0.92, 0.9, 0.86)}),
    ("fang", "obsidian-fang-rock-67e326", {"group": "rock", "collide": "box", "scale": 2.0}),
    ("mud", "bubbling-mud-pool-a1c8ac", {"group": "ground", "collide": "none", "scale": 1.8}),
    ("fumarole", "fumarole-vent-8280ba", {"group": "street", "collide": "box", "scale": 1.8}),
    ("geyser", "geyser-cone-2b5033", {"group": "street", "collide": "none", "scale": 1.8}),
    ("spring", "hot-spring-pool-26312c", {"group": "street", "collide": "none", "scale": 2.0}),
    ("steamspring", "hot-spring-pool-26312c", {"group": "street", "collide": "none", "scale": 2.6}),
    ("steamvent", "fumarole-vent-8280ba", {"group": "street", "collide": "box", "scale": 2.4}),
    ("boardwalk", os.path.join(EXTRA, "boardwalk-run-461f03.glb"), {"group": "street", "collide": "box", "scale": 1.0}),
    ("ropebridge", "rope-bridge-span-159f8c", {"group": "street", "collide": "none", "scale": 2.4}),
]

run("prehistoric", BUILDINGS, PROPS)
