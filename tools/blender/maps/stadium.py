import os, sys, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|wisp|steam|icosphere", re.I)

SNOW = (0.9, 0.93, 0.97)
SNOWY = {}
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

F = os.path.expanduser("~/.cache/polyfork/forest/")

BUILDINGS = [
    ("clubhouse", "clubhouse-8570d2", {"scale": 1.3}),
    ("firstaid", "first-aid-room-module-56b78b", {"scale": 1.25}),
    ("toilets", "toilet-block-da51a4", {"scale": 1.25}),
    ("pressbox", "press-box-55553b", {"scale": 1.3}),
    ("kiosk", "refreshment-kiosk-406f65", {"scale": 1.25}),
    ("booth", "ticket-booth-d127f8", {"scale": 1.25}),
    ("turnstile", "turnstile-bank-9294b4", {"scale": 1.25}),
    ("tunnel", "players-tunnel-4a210b", {"scale": 1.3}),
    ("gate", "main-entrance-gate-bb6357", {"scale": 1.4, "plinth": None}),
]

PROPS = [
    ("seats", "grandstand-seating-run-fc9023", {"group": "building", "collide": "none", "scale": 1.5}),
    ("roof", "stand-roof-run-cfd457", {"group": "building", "collide": "none", "scale": 1.5}),
    ("terrace", "terrace-step-run-b631a9", {"group": "building", "collide": "none", "scale": 1.5}),
    ("gable", "stand-gable-end-53847a", {"group": "building", "collide": "none", "scale": 1.5}),
    ("flood", "floodlight-mast-4482be", {"group": "building", "collide": "cylinder", "scale": 1.6}),
    ("hoarding", "advertising-hoarding-run-efe4bc", {"group": "street", "collide": "box", "scale": 1.4}),
    ("mesh", "mesh-perimeter-fence-run-ffce82", {"group": "street", "collide": "box", "scale": 1.2}),
    ("wall", "perimeter-wall-run-adc811", {"group": "street", "collide": "box", "scale": 1.2}),
    ("goal", "match-goal-a98b60", {"group": "street", "collide": "none", "scale": 1.0}),
    ("tgoal", "training-goal-50f1ca", {"group": "street", "collide": "none", "scale": 1.0}),
    ("roller", "pitch-roller-21c373", {"group": "street", "collide": "box", "scale": 1.3}),
    ("tarp", "rolled-pitch-tarpaulin-c8a93f", {"group": "street", "collide": "box", "scale": 1.6}),
    ("trolley", "goal-net-trolley-f5bd28", {"group": "street", "collide": "box", "scale": 1.3}),
    ("linecart", "line-marking-cart-2f7b12", {"group": "street", "collide": "box", "scale": 1.2}),
    ("ballcart", "ball-cart-8274fd", {"group": "street", "collide": "box", "scale": 1.2}),
    ("dummy", "tackle-dummy-06aba2", {"group": "street", "collide": "cylinder", "scale": 1.1}),
    ("medtent", "sideline-medical-tent-ce1649", {"group": "street", "collide": "box", "scale": 1.2}),
    ("scaffold", "scaffold-camera-platform-b6702c", {"group": "street", "collide": "box", "scale": 1.2}),
    ("inflatable", "inflatable-team-tunnel-c71c5c", {"group": "street", "collide": "box", "scale": 1.1}),
    ("dugout", "team-dugout-ddb70c", {"group": "street", "collide": "box", "scale": 1.2}),
    ("bench", "substitutes-bench-ea0ef7", {"group": "street", "collide": "box", "scale": 1.2}),
    ("scoreboard", "match-scoreboard-58f51e", {"group": "street", "collide": "box", "scale": 1.6}),
    ("clock", "stadium-clock-post-4d1ce8", {"group": "street", "collide": "cylinder", "scale": 1.2}),
    ("horn", "pa-horn-post-212ec8", {"group": "street", "collide": "cylinder", "scale": 1.3}),
    ("flagpole", "flag-pole-015e53", {"group": "street", "collide": "cylinder", "scale": 1.0}),
    ("bin", "ground-litter-bin-aaaba0", {"group": "street", "collide": "cylinder", "scale": 1.3}),
    ("kitbag", "kit-bag-7d617f", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("crate", "water-bottle-crate-78c8db", {"group": "ground", "collide": "none", "scale": 1.4}),
    ("stretcher", "touchline-stretcher-f08e97", {"group": "street", "collide": "none", "scale": 1.1}),
    ("tactics", "tactics-board-21cfd2", {"group": "street", "collide": "box", "scale": 1.2}),
    ("cones", "marker-cone-set-8fab80", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("ladder", "agility-ladder-2a8267", {"group": "ground", "collide": "none", "scale": 2.0}),
    ("bags", "agility-bag-set-e25fcd", {"group": "ground", "collide": "none", "scale": 1.0}),
    ("hurdle", "athletics-hurdle-164f6f", {"group": "street", "collide": "none", "scale": 1.1}),
    ("blocks", "starting-blocks-9d8848", {"group": "ground", "collide": "none", "scale": 1.2}),
    ("discus", "discus-cage-2e0e7b", {"group": "street", "collide": "none", "scale": 1.1}),
    ("highjump", "high-jump-apparatus-84ac1d", {"group": "street", "collide": "box", "scale": 1.1}),
    ("longjump", "long-jump-pit-9d28e4", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("shotput", "shot-put-circle-a12cb9", {"group": "ground", "collide": "none", "scale": 1.2}),
    ("minibus", "team-minibus-f14295", {"group": "street", "collide": "box", "scale": 1.15}),
    ("cornerflag", "corner-flag-0b43b0", {"group": "street", "collide": "none", "scale": 1.0}),
    ("chain", "chain-crew-set-f2efdc", {"group": "street", "collide": "none", "scale": 1.0}),
    ("medbag", "first-aid-bag-8a7f09", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("yardmark", "sideline-yard-marker-029dcc", {"group": "ground", "collide": "none", "scale": 1.6}),
    ("oak", F + "broadleaf-oak-997c22.glb", {"group": "tree", "collide": "trunk"}),
    ("birch", F + "birch-tree-181b33.glb", {"group": "tree", "collide": "trunk"}),
    ("pine", F + "tall-pine-tree-ab4108.glb", {"group": "tree", "collide": "trunk"}),
    ("bush", F + "round-bush-cd2ac0.glb", {"group": "bush", "collide": "none", "scale": 2.2}),
    ("parkbench", F + "wooden-bench-02e2c8.glb", {"group": "street", "collide": "box", "scale": 1.15}),
]

run("stadium", BUILDINGS, PROPS)
