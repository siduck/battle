import os, sys, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|spray|plume|wisp|summit-cross|book-door", re.I)

SNOW = (0.9, 0.93, 0.97)
SNOWY = {"cabin": 0.5, "aframe": 0.35, "logcabin": 0.5, "washhouse": 0.5, "ranger": 0.5, "lookout": 0.5, "pine": 0.3, "pines": 0.3, "slab": 0.45, "cordwood": 0.5, "van": 0.6, "plough": 0.6, "board": 0.5, "trailsign": 0.5, "picnic": 0.6, "bank": 0.3}
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
    if name in SNOWY:
        snowify(bm, start=SNOWY[name])

    bake_ao(bm)

    return _export(bm, name)


pf.export = export_baked

BUILDINGS = [
    ("chalet", "alpine-chalet-47d59e", {"scale": 1.35}),
    ("barn", "alpine-hay-barn-3965e5", {"scale": 1.3}),
    ("refuge", "mountain-refuge-hut-32ab1e", {"scale": 1.3}),
    ("patrol", "piste-patrol-hut-17a90a", {"scale": 1.2}),
    ("starthut", "race-start-hut-c6d405", {"scale": 1.15}),
    ("base", "ski-lift-base-station-924491", {"scale": 1.25}),
    ("top", "lift-top-station-46d313", {"scale": 1.2}),
    ("cabin", "porch-log-cabin-d2f3ef", {"scale": 1.25}),
    ("aframe", "a-frame-cabin-6cb550", {"scale": 1.25}),
    ("logcabin", "log-cabin-4fac3b", {"scale": 1.2}),
    ("washhouse", "timber-wash-house-c7e7d5", {"scale": 1.2}),
    ("ranger", "hip-roof-ranger-station-581dd5", {"scale": 1.2}),
    ("lookout", "splay-leg-lookout-tower-6fae7e", {"scale": 1.3, "plinth": None}),
]

PROPS = [
    ("spruce", "snow-laden-spruce-36716e", {"group": "tree", "collide": "trunk"}),
    ("larch", "windblown-larch-abb99c", {"group": "tree", "collide": "trunk"}),
    ("rowan", "bare-mountain-rowan-10e72e", {"group": "tree", "collide": "trunk"}),
    ("pine", "tall-pine-tree-ab4108", {"group": "tree", "collide": "trunk", "k": (0.82, 0.92, 0.9)}),
    ("pines", "campground-pine-stand-0bf4f2", {"group": "tree", "collide": "trunk", "k": (0.85, 0.95, 0.92)}),
    ("dwarf", "dwarf-pine-mat-faee77", {"group": "bush", "collide": "none"}),
    ("outcrop", "rock-outcrop-158ac3", {"group": "rock", "collide": "box"}),
    ("boulders", "boulder-field-cluster-08e364", {"group": "rock", "collide": "box"}),
    ("slab", "large-boulder-a29b99", {"group": "rock", "collide": "box", "k": (0.85, 0.87, 0.92)}),
    ("scree", "scree-heap-42cce5", {"group": "ground", "collide": "none"}),
    ("cairn", "stone-cairn-a9bf48", {"group": "street", "collide": "cylinder"}),
    ("falls", "frozen-waterfall-5d1fc6", {"group": "rock", "collide": "none"}),
    ("logs", "snow-capped-log-pile-8719e7", {"group": "street", "collide": "box"}),
    ("cordwood", "cordwood-pile-b5229b", {"group": "street", "collide": "box"}),
    ("fence", "snow-fence-run-55a09a", {"group": "street", "collide": "box"}),
    ("barrier", "avalanche-barrier-run-02a615", {"group": "street", "collide": "box"}),
    ("net", "safety-net-run-ecf381", {"group": "street", "collide": "box"}),
    ("bank", "ploughed-snowbank-run-5d60bd", {"group": "street", "collide": "box"}),
    ("fort", "kids-snow-fort-c31153", {"group": "street", "collide": "box"}),
    ("trough", "frozen-water-trough-61c835", {"group": "street", "collide": "box"}),
    ("drum", "groomer-fuel-drum-9d56e6", {"group": "street", "collide": "box"}),
    ("winch", "groomer-winch-anchor-8f2495", {"group": "street", "collide": "box"}),
    ("exploder", "avalanche-gas-exploder-78b46f", {"group": "street", "collide": "box"}),
    ("cannon", "snow-cannon-cc3ea5", {"group": "street", "collide": "box"}),
    ("flood", "piste-floodlight-mast-a31cf2", {"group": "street", "collide": "cylinder"}),
    ("pylon", "lift-pylon-4e4385", {"group": "building", "collide": "none"}),
    ("rope", "haul-rope-span-6ad505", {"group": "building", "collide": "none"}),
    ("chair", "chairlift-chair-2beb2b", {"group": "street", "collide": "none"}),
    ("gondola", "gondola-cabin-c05230", {"group": "street", "collide": "box"}),
    ("tow", "rope-tow-run-c0fbbd", {"group": "street", "collide": "box"}),
    ("marker", "piste-marker-pole-7480c3", {"group": "street", "collide": "none"}),
    ("gate", "slalom-gate-7f4875", {"group": "street", "collide": "none"}),
    ("finger", "alpine-fingerpost-d47349", {"group": "street", "collide": "cylinder"}),
    ("wayfinder", "wayfinder-post-961fcd", {"group": "street", "collide": "cylinder"}),
    ("mast", "weather-station-mast-f84278", {"group": "street", "collide": "cylinder"}),
    ("bench", "alpine-bench-32fa62", {"group": "street", "collide": "box"}),
    ("skirack", "timber-ski-rack-8239d1", {"group": "street", "collide": "box"}),
    ("boards", "snowboard-rack-ecad90", {"group": "street", "collide": "box"}),
    ("skis", "ski-and-pole-stack-9d4d53", {"group": "street", "collide": "none"}),
    ("firepit", "cleared-fire-pit-399cda", {"group": "street", "collide": "none"}),
    ("probe", "probe-and-shovel-set-06d115", {"group": "ground", "collide": "none"}),
    ("toboggan", "wooden-toboggan-940bbc", {"group": "ground", "collide": "none"}),
    ("akja", "akja-rescue-sledge-a3727f", {"group": "street", "collide": "box"}),
    ("sled", "snowmobile-e0fef3", {"group": "street", "collide": "box"}),
    ("board", "camp-notice-board-c0be42", {"group": "street", "collide": "box", "scale": 1.3}),
    ("trailsign", "trailhead-sign-aa29e1", {"group": "street", "collide": "box", "scale": 1.3}),
    ("picnic", "heavy-timber-picnic-table-1ac060", {"group": "street", "collide": "box", "scale": 1.2}),
]

run("alpine", BUILDINGS, PROPS)
