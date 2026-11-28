import math

from mathutils import Vector
from mathutils.bvhtree import BVHTree


def hemisphere(n):
    dirs = []
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        u = (i + 0.5) / n
        r = math.sqrt(u)
        a = i * golden
        dirs.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(1 - u))))

    return dirs


RAYS = hemisphere(28)


def bounds(bm):
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]

    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def ao(bm, dist, strength, ground=True, floor=0.0, sky=0.0):
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    lo, hi = bounds(bm)
    height = max(hi.z - lo.z, 0.01)
    cache = {}

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()

        for l in f.loops:
            key = (l.vert.index, round(n.x, 2), round(n.y, 2), round(n.z, 2))
            k = cache.get(key)

            if k is None:
                sides = []

                for sn in (1, -1):
                    p = l.vert.co + (c - l.vert.co) * 0.04 + n * (0.02 * sn)
                    o = 0.0

                    for d in RAYS:
                        w = t * d.x + b * d.y + n * (d.z * sn)
                        hit = tree.ray_cast(p, w, dist)

                        if hit[0] is not None:
                            o += 1 - hit[3] / dist
                        elif ground and w.z < -0.02:
                            tt = (floor - p.z) / w.z

                            if 0 < tt < dist:
                                o += 1 - tt / dist

                    sides.append(o)

                occ = min(sides)
                k = 1 - strength * min(1.0, occ / len(RAYS) * 1.6)

                if sky:
                    k *= 1 - sky + sky * min(1.0, max(0.0, (l.vert.co.z - lo.z) / height))

                cache[key] = k

            cc = l[col]
            l[col] = (cc[0] * k, cc[1] * k, cc[2] * k, 1.0)
