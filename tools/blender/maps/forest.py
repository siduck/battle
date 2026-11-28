import os, sys, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|wisp|steam", re.I)

OWN = os.environ.get("OWN", "")
STONE = (0.47, 0.47, 0.43)
_load = pf.load


def own(name):
    path = os.path.join(OWN, name + ".glb") if OWN else ""

    return path if path and os.path.exists(path) else None


def load_own(path, door_to=None):
    if not (OWN and os.path.abspath(path).startswith(os.path.abspath(OWN))):
        return _load(path, door_to)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()

    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        me = o.data
        src = me.color_attributes[0]
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)

        for layer in list(tmp.loops.layers.float_color):
            tmp.loops.layers.float_color.remove(layer)
        for layer in list(tmp.loops.layers.color):
            tmp.loops.layers.color.remove(layer)

        col = tmp.loops.layers.float_color.new("Col")
        tmp.faces.ensure_lookup_table()

        for f, p in zip(tmp.faces, me.polygons):
            for l, li in zip(f.loops, p.loop_indices):
                c = src.data[li].color
                l[col] = (c[0], c[1], c[2], 1.0)

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    return bm


pf.load = load_own

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

BUILDINGS = [
    ("logcabin", "log-cabin-4fac3b", {"scale": 1.4}),
    ("ranger", "ranger-station-ef6407", {"scale": 1.35}),
    ("lookout", "fire-lookout-tower-75a129", {"scale": 1.6, "plinth": None}),
    ("woodshed", "open-woodshed-050a0a", {"scale": 1.3}),
    ("outhouse", "forest-outhouse-e968d1", {"scale": 1.25}),
    ("leanto", "lean-to-shelter-f0709f", {"scale": 1.4}),
    ("aframe", "a-frame-cabin-6cb550", {"scale": 1.3}),
    ("porch", "porch-log-cabin-d2f3ef", {"scale": 1.2}),
    ("washhouse", "timber-wash-house-c7e7d5", {"scale": 1.2}),
    ("hiproof", "hip-roof-ranger-station-581dd5", {"scale": 1.25}),
]

PROPS = [
    ("oak", "broadleaf-oak-997c22", {"group": "tree", "collide": "trunk"}),
    ("birch", "birch-tree-181b33", {"group": "tree", "collide": "trunk"}),
    ("maple", "maple-tree-65fa12", {"group": "tree", "collide": "trunk"}),
    ("pine", "tall-pine-tree-ab4108", {"group": "tree", "collide": "trunk"}),
    ("young", "young-pine-0d7695", {"group": "tree", "collide": "trunk"}),
    ("dead", "dead-tree-6795fa", {"group": "tree", "collide": "trunk"}),
    ("pines", "campground-pine-stand-0bf4f2", {"group": "tree", "collide": "trunk"}),
    ("stump", "tree-stump-ec3f48", {"group": "street", "collide": "cylinder", "scale": 2.0}),
    ("roots", "exposed-tree-roots-e1409c", {"group": "street", "collide": "none", "scale": 1.6}),
    ("bush", "round-bush-cd2ac0", {"group": "bush", "collide": "none", "scale": 2.2}),
    ("fern", "fern-plant-1559b8", {"group": "ground", "collide": "none", "scale": 1.7}),
    ("tuft", "grass-tuft-a40a08", {"group": "ground", "collide": "none", "scale": 2.6}),
    ("reeds", "reed-bed-bbbefb", {"group": "bush", "collide": "none", "scale": 1.5}),
    ("cattail", "cattail-reed-6abbb3", {"group": "ground", "collide": "none", "scale": 1.5}),
    ("flower", "wildflower-68d3a1", {"group": "ground", "collide": "none", "scale": 2.4}),
    ("toadstool", "toadstool-257a4a", {"group": "ground", "collide": "none", "scale": 2.0}),
    ("lily", "lily-pad-86edbb", {"group": "ground", "collide": "none", "scale": 2.5}),
    ("boulder", "large-boulder-a29b99", {"group": "rock", "collide": "box", "scale": 2.4}),
    ("rock", "medium-rock-e08405", {"group": "rock", "collide": "box", "scale": 2.4}),
    ("spire", "rock-spire-13819c", {"group": "rock", "collide": "box", "scale": 2.4}),
    ("fallen", "fallen-log-1685fb", {"group": "street", "collide": "box", "scale": 1.6}),
    ("firewood", "firewood-stack-8a2899", {"group": "street", "collide": "box", "scale": 1.6}),
    ("cordwood", "cordwood-pile-b5229b", {"group": "street", "collide": "box", "scale": 1.3}),
    ("barrel", "wooden-barrel-ab50ca", {"group": "street", "collide": "box", "scale": 1.25}),
    ("bench", "wooden-bench-02e2c8", {"group": "street", "collide": "box", "scale": 1.15}),
    ("picnic", "campsite-picnic-table-361d51", {"group": "street", "collide": "box", "scale": 1.15}),
    ("table", "heavy-timber-picnic-table-1ac060", {"group": "street", "collide": "box", "scale": 1.2}),
    ("well", "stone-well-2b4717", {"group": "street", "collide": "box", "scale": 1.4}),
    ("kiosk", "trail-map-kiosk-be8618", {"group": "street", "collide": "box", "scale": 1.3}),
    ("sign", "trail-signpost-bd29a7", {"group": "street", "collide": "cylinder", "scale": 1.3}),
    ("lantern", "lantern-post-f47665", {"group": "street", "collide": "cylinder", "scale": 1.3}),
    ("fence", "wooden-fence-section-5f04b7", {"group": "street", "collide": "box", "scale": 1.3}),
    ("gate", "wooden-fence-gate-a8735f", {"group": "street", "collide": "box", "scale": 1.3}),
    ("tent", "camp-tent-3c5c89", {"group": "street", "collide": "box", "scale": 1.4}),
    ("walltent", "canvas-wall-tent-de8a04", {"group": "street", "collide": "box", "scale": 1.3}),
    ("dome", "dome-tent-9ee59d", {"group": "street", "collide": "box", "scale": 1.3}),
    ("firepit", "stone-fire-pit-4136b0", {"group": "street", "collide": "none", "scale": 1.5}),
    ("tripod", "campfire-cook-tripod-d95a1e", {"group": "street", "collide": "none", "scale": 1.3}),
    ("cooler", "camp-cooler-8ba941", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("dock", "dock-platform-section-b36e7c", {"group": "street", "collide": "none", "scale": 1.6}),
    ("pier", "lake-dock-run-f5380e", {"group": "street", "collide": "none", "scale": 1.5}),
    ("bridge", "log-plank-bridge-a5f74f", {"group": "street", "collide": "none", "scale": 1.8}),
    ("footbridge", "creek-footbridge-d35cf7", {"group": "street", "collide": "none", "scale": 1.8}),
    ("ramp", "boat-launch-ramp-dbde11", {"group": "street", "collide": "none", "scale": 1.2}),
    ("rack", "canoe-rack-c8126e", {"group": "street", "collide": "box", "scale": 1.2}),
    ("lights", "string-light-run-01ba14", {"group": "street", "collide": "none", "scale": 1.35}),
    ("stone", "slab-path-stone-e526f7", {"group": "ground", "collide": "none", "scale": 1.6}),
]

def swap(entries, building):
    out = []

    for name, src, opts in entries:
        mine = own(name)

        if not mine:
            out.append((name, src, opts))
            continue

        keep = {k: v for k, v in opts.items() if k in ("group", "collide")}
        keep["scale"] = 1.0

        if building:
            keep = {"scale": 1.0, "plinth": STONE}

        out.append((name, mine, keep))

    return out


run("forest", swap(BUILDINGS, True), swap(PROPS, False))
