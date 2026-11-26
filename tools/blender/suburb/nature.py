import math

import bmesh
import jp
from jp import add
from mathutils import Vector

k = jp.k


def blob(at, size, tones, sub=None, jitter=0.1, seed=0):
    import random

    r = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub if sub is not None else jp.N + 1, radius=1.0)

    for v in bm.verts:
        n = v.co.normalized()
        f = 1.0 + r.uniform(-jitter, jitter)
        v.co = Vector((n.x * size[0] * f, n.y * size[1] * f, n.z * size[2] * f))

    bm.transform(__import__("mathutils").Matrix.Translation(Vector(at)))
    ob = k.lpm._object("blob", bm, jp.c(tones[1]))
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        nz = p.normal.z
        side = p.normal.x * 0.5 - p.normal.y * 0.5
        t = tones[0] if nz > 0.45 or (nz > 0.1 and side > 0.2) else tones[1] if nz > -0.35 else tones[2]
        attr.data[p.index].value = jp.c(t)

    return ob


def trunk(base, top, r0, r1, color="jp_bark", sides=6):
    a = Vector(base)
    b = Vector(top)
    d = (b - a).length
    ob = k.prism("trunk", sides * jp.N, r0, d, (0, 0, 0), jp.c(color), radius_top=r1)
    q = (b - a).normalized().to_track_quat("Z", "Y")
    ob.data.transform(q.to_matrix().to_4x4())
    k.move(ob, a.x, a.y, a.z)

    return ob


def canopy(clusters, tones, seed):
    items = []

    for i, (at, size) in enumerate(clusters):
        items.append(blob(at, size, tones, seed=seed + i))

    return items


def tree_generic(name, h, spread, trunk_h, tones, n, seed, lean=0.0, budget=4000, cluster_scale=1.0):
    jp.setup(seed)
    import random

    r = random.Random(seed)
    items = [trunk((0, 0, 0), (lean, 0, trunk_h), 0.22 * cluster_scale, 0.14 * cluster_scale)]
    clusters = [((lean, 0, h - spread * 0.55), (spread * 0.62, spread * 0.6, spread * 0.42))]

    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.3, 0.3)
        rad = spread * r.uniform(0.45, 0.62)
        z = h - spread * r.uniform(0.75, 1.05)
        at = (lean + math.cos(a) * rad, math.sin(a) * rad, z)
        s = spread * r.uniform(0.38, 0.5) * cluster_scale
        clusters.append((at, (s, s, s * 0.78)))
        items.append(trunk((lean * 0.8, 0, trunk_h * 0.75), (at[0] * 0.7, at[1] * 0.7, z - s * 0.4), 0.08 * cluster_scale, 0.05))

    items += canopy(clusters, tones, seed)
    add(items)

    return jp.finish(name, budget, fuse_soft=False, gradient=False)


def tree():
    return tree_generic("tree", 7.6, 3.1, 3.6, ("jp_leaf_light", "jp_leaf", "jp_leaf_dark"), 8, 41, budget=6000, cluster_scale=0.85)


def cherry():
    jp.setup(42)
    import random

    r = random.Random(42)
    items = [trunk((0, 0, 0), (0.25, 0, 2.2), 0.24, 0.17)]
    clusters = []

    for i in range(8):
        a = 2 * math.pi * i / 8 + r.uniform(-0.25, 0.25)
        rad = r.uniform(1.1, 1.75)
        z = r.uniform(3.6, 4.8)
        tip = (0.25 + math.cos(a) * rad, math.sin(a) * rad, z)
        items.append(trunk((0.25, 0, 2.0), (tip[0] * 0.8, tip[1] * 0.8, z - 0.5), 0.11, 0.06))
        s = r.uniform(0.75, 1.0)
        clusters.append((tip, (s * 1.05, s * 1.05, s * 0.7)))

    clusters.append(((0.25, 0, 5.1), (1.3, 1.25, 0.85)))
    items += canopy(clusters, ("jp_cherry_light", "jp_cherry", "jp_cherry_dark"), 42)
    add(items)

    return jp.finish("cherry", 6000, fuse_soft=False, gradient=False)


def maple():
    jp.setup(43)
    import random

    r = random.Random(43)
    items = [trunk((0, 0, 0), (0, 0, 2.6), 0.16, 0.1)]
    clusters = [((0, 0, 5.2), (1.25, 1.2, 1.05)), ((0, 0, 4.0), (1.45, 1.4, 0.8))]

    for i in range(7):
        a = 2 * math.pi * i / 7 + r.uniform(-0.3, 0.3)
        at = (math.cos(a) * 0.95, math.sin(a) * 0.95, r.uniform(3.3, 4.8))
        clusters.append((at, (0.75, 0.75, 0.6)))
        items.append(trunk((0, 0, 2.2), (at[0] * 0.7, at[1] * 0.7, at[2] - 0.4), 0.07, 0.04))

    items += canopy(clusters, ("jp_maple_light", "jp_maple", "jp_red_dark"), 43)
    add(items)

    return jp.finish("maple", 6000, fuse_soft=False, gradient=False)


def bush():
    jp.setup(44)
    items = canopy([((0, 0, 0.3), (0.5, 0.36, 0.34)), ((-0.25, 0.05, 0.25), (0.34, 0.3, 0.26)), ((0.3, -0.04, 0.24), (0.3, 0.28, 0.24))], ("jp_leaf_light", "jp_leaf", "jp_leaf_dark"), 44)
    add(items)

    return jp.finish("bush", 800, fuse_soft=False, gradient=False)


ALL = {
    "cherry": cherry,
    "tree": tree,
    "maple": maple,
    "bush": bush,
}
