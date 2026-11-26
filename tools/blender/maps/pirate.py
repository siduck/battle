import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DIR"] = "pirate"
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|^icosphere|shadow|ground.?plane|^plane|parrot|trader|officer|captain|deckhand|jolly|skull", re.I)

CACHE = os.path.dirname(P.rstrip("/"))
FOAM = (0.93, 0.97, 0.98)


def src_of(src):
    if src.startswith("/"):
        return src

    for d in ("pirate", "pirate_x", "coast", "islands_x"):
        p = os.path.join(CACHE, d, src + ".glb")

        if os.path.exists(p):
            return p

    return os.path.join(P, src + ".glb")


X = os.path.expanduser("~/.cache/polyfork/cprc_x")


def xp(i):
    return os.path.join(X, i + ".glb")


def squeeze(path):
    raw = open(path, "rb").read()
    jlen = struct.unpack("<I", raw[12:16])[0]
    doc = json.loads(raw[20:20 + jlen])
    bin0 = raw[20 + jlen + 8:]
    acc = doc["accessors"]
    views = doc["bufferViews"]
    sizes = {5126: 4, 5123: 2, 5125: 4, 5121: 1}
    comps = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}

    def read(i):
        a = acc[i]
        v = views[a["bufferView"]]
        n = comps[a["type"]]
        ct = a["componentType"]
        fmt = {5126: "f", 5123: "H", 5125: "I", 5121: "B"}[ct]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", sizes[ct] * n)
        out = []

        for k in range(a["count"]):
            out.append(struct.unpack_from("<%d%s" % (n, fmt), bin0, off + k * stride))

        if a.get("normalized"):
            d = {5123: 65535.0, 5121: 255.0}[ct]
            out = [tuple(x / d for x in t) for t in out]

        return out

    blob = bytearray()
    new_views = []
    new_acc = []

    def push(data, target):
        while len(blob) % 4:
            blob.append(0)

        new_views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)

        return len(new_views) - 1

    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            pos = read(at["POSITION"])
            nor = read(at["NORMAL"]) if "NORMAL" in at else [(0.0, 1.0, 0.0)] * len(pos)
            col = read(at["COLOR_0"]) if "COLOR_0" in at else [(1.0, 1.0, 1.0, 1.0)] * len(pos)
            idx = [t[0] for t in read(prim["indices"])] if "indices" in prim else list(range(len(pos)))
            seen = {}
            vp, vn, vc, out = [], [], [], []

            for i in idx:
                p = pos[i]
                n = nor[i]
                c = tuple(max(0, min(255, int(round(x * 255)))) for x in col[i][:3])
                key = (round(p[0], 4), round(p[1], 4), round(p[2], 4), round(n[0], 2), round(n[1], 2), round(n[2], 2), c)
                j = seen.get(key)

                if j is None:
                    j = len(vp)
                    seen[key] = j
                    vp.append(p)
                    vn.append(n)
                    vc.append(c)

                out.append(j)

            big = len(vp) > 65535
            base = len(new_acc)
            pv = push(b"".join(struct.pack("<3f", *p) for p in vp), 34962)
            nv = push(b"".join(struct.pack("<3f", *n) for n in vn), 34962)
            cv = push(b"".join(struct.pack("<4B", c[0], c[1], c[2], 255) for c in vc), 34962)
            iv = push(struct.pack("<%d%s" % (len(out), "I" if big else "H"), *out), 34963)
            mn = [min(p[k] for p in vp) for k in range(3)]
            mx = [max(p[k] for p in vp) for k in range(3)]
            new_acc.append({"bufferView": pv, "componentType": 5126, "count": len(vp), "type": "VEC3", "min": mn, "max": mx})
            new_acc.append({"bufferView": nv, "componentType": 5126, "count": len(vp), "type": "VEC3"})
            new_acc.append({"bufferView": cv, "componentType": 5121, "normalized": True, "count": len(vp), "type": "VEC4"})
            new_acc.append({"bufferView": iv, "componentType": 5125 if big else 5123, "count": len(out), "type": "SCALAR"})
            prim["attributes"] = {"POSITION": base, "NORMAL": base + 1, "COLOR_0": base + 2}
            prim["indices"] = base + 3

    while len(blob) % 4:
        blob.append(0)

    doc["accessors"] = new_acc
    doc["bufferViews"] = new_views
    doc["buffers"] = [{"byteLength": len(blob)}]
    js = json.dumps(doc, separators=(",", ":")).encode()

    while len(js) % 4:
        js += b" "

    total = 12 + 8 + len(js) + 8 + len(blob)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(blob), 0x004E4942))
        f.write(blob)


def squeeze_dir(d):
    for f in sorted(os.listdir(d)):
        if f.endswith(".glb"):
            squeeze(os.path.join(d, f))



def fresh():
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    return bm


def desat(bm, amount, k=(1, 1, 1)):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            g = (c[0] + c[1] + c[2]) / 3
            l[col] = tuple(min(1.0, (c[i] + (g - c[i]) * amount) * k[i]) for i in range(3)) + (1.0,)


def swap(src, dst, tol=0.09):
    def go(bm):
        col = bm.loops.layers.float_color["Col"]

        for f in bm.faces:
            for l in f.loops:
                c = l[col]

                if max(abs(c[i] - src[i]) for i in range(3)) < tol:
                    k = sum(c[:3]) / max(sum(src), 1e-3)
                    l[col] = (min(1, dst[0] * k), min(1, dst[1] * k), min(1, dst[2] * k), 1.0)

    return go


def woodify(bm):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]

            if max(c[:3]) - min(c[:3]) < 0.1:
                g = (c[0] + c[1] + c[2]) / 3
                l[col] = (g * 0.62, g * 0.42, g * 0.26, 1.0)


def hemisphere(n):
    out = []
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        z = 1 - (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * golden
        out.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))

    return out


DIRS = hemisphere(28)


def bake_ao(bm, reach=2.2, strength=0.6, floor=0.35, floor_h=0.9, sky=0.12):
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    lo, hi = bounds(bm)
    shade = {}

    for v in bm.verts:
        n = v.normal if v.normal.length > 0.5 else Vector((0, 0, 1))
        t = n.orthogonal().normalized()
        bt = n.cross(t)
        p = v.co + n * 0.015
        hit = 0.0

        for d in DIRS:
            w = t * d.x + bt * d.y + n * d.z
            loc, nor, idx, dist = bvh.ray_cast(p, w, reach)

            if loc is not None:
                hit += (1 - dist / reach) ** 0.5

        occ = hit / len(DIRS)
        k = 1 - strength * occ
        k *= 1 - floor * max(0.0, 1 - (v.co.z - lo.z) / floor_h) * (1 - max(0.0, n.z))
        k *= 1 - sky * max(0.0, -n.z)
        shade[v.index] = max(0.3, k)

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            k = shade[l.vert.index]
            l[col] = (c[0] * k, c[1] * k, c[2] * k, 1.0)


def ext(src, scale=1.0, k=None, rot=0.0, post=None):
    bm = load(src_of(src))

    if post:
        post(bm)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale, rot=rot)

    return bm


def foam(length=7.0, width=0.9, seed=1):
    bm = fresh()
    n = 14
    k = seed

    for i in range(n):
        k = (k * 1103515245 + 12345) & 0x7FFFFFFF
        x0 = -length / 2 + i * length / n
        x1 = x0 + length / n + 0.05
        w = width * (0.55 + (k % 100) / 220)
        y = math.sin(i * 0.9 + seed) * 0.18
        add_box(bm, (x0, y - w / 2, 0.0), (x1, y + w / 2, 0.035), FOAM)

        if k % 3 == 0:
            add_box(bm, (x0 + 0.1, y + w / 2 + 0.25, 0.0), (x1 - 0.1, y + w / 2 + 0.5, 0.025), (0.8, 0.92, 0.94))

    return bm


def ripple(length=9.0, seed=4):
    bm = fresh()

    for i in range(10):
        x0 = -length / 2 + i * length / 10
        x1 = x0 + length / 10 * 0.8
        y = math.sin(i * 0.7 + seed) * 0.4
        add_box(bm, (x0, y - 0.12, 0.0), (x1, y + 0.12, 0.02), (0.62, 0.86, 0.88))

    return bm


def b(name, src, scale=1.0, post=None, k=None, rot=0.0):
    return (name, lambda: ext(src, scale, k, rot, post), {"group": "building", "collide": "none", "kind": "building"})


def p(name, src, scale=1.0, group="street", collide="box", post=None, k=None, ao=True, rot=0.0):
    return (name, lambda: ext(src, scale, k, rot, post), {"group": group, "collide": collide, "ao": ao})


def g(name, fn, group="street", collide="none", ao=True):
    return (name, fn, {"group": group, "collide": collide, "ao": ao})


PIECES = [
    b("tavern", "cove-tavern-5861a6", 1.15),
    b("warehouse", "dock-warehouse-bf0967", 1.2),
    b("shack", "fisherman-shack-ea9b2b", 1.1),
    b("boatshed", "shipwright-boat-shed-9cbbc1", 1.2),
    b("cave", "smuggler-cave-mouth-69a07e", 2.4),
    p("tower", "lookout-watchtower-f1a5ce", 1.2, group="building", collide="none"),
    p("battery", "battery-wall-section-51b723", group="building"),
    p("crane", "dock-cargo-crane-ccd97f", group="building", collide="none"),
    p("galleon", "pirate-galleon-2e9aea", group="building", collide="none"),
    p("brig", "pirate-brigantine-c29c57", group="building", collide="none"),
    p("sloop", "pirate-sloop-d8ead0", group="building", collide="none"),
    p("hull", "pirate-sloop-hull-89cd04", group="building", collide="none"),
    p("wreck", "wrecked-hull-section-ca6755", 1.4, group="building", collide="none"),
    p("pier", "pier-deck-section-7047d7", group="building", collide="none"),
    p("gangplank", "gangplank-572d4e", collide="none"),
    p("mooring", "mooring-post-2b83a4", collide="cylinder"),
    p("lantern", "dock-lantern-post-5e58a4", collide="cylinder"),
    p("torch", "torch-stake-d82a2c", collide="none"),
    p("barrel", "barrel-8d63c4"),
    p("crate", "cargo-crate-9afc44", 1.2),
    p("wcrate", "wooden-crate-b9c96a"),
    p("sack", "cargo-sack-3cd3ab", collide="none"),
    p("capstan", "capstan-fa3917"),
    p("cannon", "deck-cannon-17849e", 1.3),
    p("swivel", "swivel-gun-e06c4e", collide="cylinder"),
    p("chest", "treasure-chest-c2ac4f"),
    p("anchor", "ship-anchor-c2b4f1", 1.4),
    p("wheel", "ship-s-wheel-7e7426", collide="none"),
    p("rope", "rope-coil-776dcc", collide="none"),
    p("netrack", "drying-net-rack-93ec3b", collide="none"),
    p("signboard", "hanging-signboard-c10e01", collide="cylinder"),
    p("palisade", "palisade-fence-section-471b1b", collide="none"),
    p("campfire", "campfire-4390aa", collide="none"),
    p("stump", "tree-stump-00f3bf"),
    p("driftwood", "driftwood-log-90340b"),
    p("balls", "cannonball-f87cdc", 2.2, collide="none"),
    p("palm", "palm-tree-a307da", 1.1, group="tree", collide="trunk"),
    p("sapling", "palm-sapling-ef7ae4", 1.2, group="bush", collide="none"),
    p("fern", "tropical-fern-bush-c70147", 1.5, group="bush", collide="none"),
    p("banana", "banana-plant-978d7f", 1.2, group="tree", collide="cylinder"),
    p("bamboo", "bamboo-grove-clump-7c747d", 1.2, group="tree", collide="cylinder"),
    p("treefern", "tree-fern-78320e", 1.2, group="tree", collide="trunk"),
    p("grass", "beach-grass-tuft-0e699f", 2.0, group="ground", collide="none", ao=False),
    p("boulder", "large-boulder-a29b99", 1.4, group="rock"),
    p("coastal", "large-coastal-boulder-a2cab1", 1.6, group="rock"),
    p("mrock", "medium-rock-e08405", 1.3, group="rock"),
    p("spire", "rock-spire-13819c", 2.0, group="rock"),
    p("karst", "karst-limestone-peak-ee1b76", 3.0, group="building", collide="none", k=(0.84, 0.82, 0.76)),
    p("stack", "sea-stack-369791", 2.6, group="building", collide="none"),
    p("tent", xp("canvas-ridge-tent-f0df0d"), 1.5, group="building", collide="none"),
    p("walltent", xp("canvas-wall-tent-de8a04"), 1.4, group="building", collide="none"),
    p("bigtent", xp("soldiers-tent-4bd5b9"), 1.5, group="building", collide="none"),
    p("flag", xp("flagpole-7b7806"), 1.4, collide="cylinder", post=woodify),
    p("tarp", xp("camouflage-net-canopy-ce6249"), 1.4, group="building", collide="none", k=(1.05, 0.92, 0.78)),
    p("freight", xp("freight-crate-and-sack-f49cbb"), 1.0),
    g("foam", lambda: foam(7.0, 0.9, 1), "ground", "none", ao=False),
    g("ripple", lambda: ripple(9.0, 4), "ground", "none", ao=False),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props/pirate")
    os.makedirs(pf.OUT, exist_ok=True)
    infos = {}

    for name, fn, opts in PIECES:
        bm = fn()
        building = opts.get("kind") == "building"
        blocks = []

        if building:
            boxes = footprint(bm)

            for bx in boxes:
                h = column_height(bm, bx)
                small = (bx[2] - bx[0]) * (bx[3] - bx[1]) < 1.2
                add_box(bm, (bx[0] + 0.02, bx[1] + 0.02, -1.5), (bx[2] - 0.02, bx[3] - 0.02, 0.03), (0.62, 0.58, 0.54))
                blocks.append([round(bx[0], 3), round(-bx[3], 3), round(bx[2], 3), round(-bx[1], 3), round(min(h, 3.2) if small else h, 3)])

        if opts.get("ao", True):
            bake_ao(bm)

        lo, hi = bounds(bm)
        info = export(bm, name)
        bm.free()
        info["kind"] = "building" if building else "prop"
        info["group"] = opts["group"]
        info["collide"] = opts["collide"]

        if building:
            info["blocks"] = blocks
            info["w"] = round(max(hi.x - lo.x, 1), 2)
            info["d"] = round(max(hi.y - lo.y, 1), 2)

        infos[name] = info
        print("DONE", name, info["tris"], [round(v, 2) for v in info["min"]], [round(v, 2) for v in info["max"]], len(blocks))

    emit_zig("pirate", infos, os.path.join(root, "src/shared/maps/pirate_kit.zig"))
    squeeze_dir(pf.OUT)


main()
