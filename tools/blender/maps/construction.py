import os, sys, math, random, re, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "construction")
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|icosphere|attach-|crane-seat|groundworker|banksman|surveyor|erector", re.I)
CITY = os.path.expanduser("~/.cache/polyfork/cextra")

CONCRETE = (0.6, 0.59, 0.56)
CONCRETE_D = (0.5, 0.49, 0.47)
SCREED = (0.55, 0.54, 0.52)
BLOCK = [(0.6, 0.59, 0.56), (0.56, 0.55, 0.52), (0.63, 0.62, 0.58), (0.53, 0.52, 0.5)]
MORTAR = (0.5, 0.49, 0.47)
TUBE = (0.56, 0.6, 0.64)
BOARD = [(0.66, 0.48, 0.27), (0.6, 0.43, 0.24), (0.7, 0.52, 0.3)]
TOE = (0.86, 0.66, 0.12)
RAIL = (0.9, 0.7, 0.1)
BLACK = (0.16, 0.16, 0.17)
REBAR = (0.46, 0.25, 0.13)
PLY = (0.78, 0.55, 0.28)
FORM = (0.78, 0.22, 0.14)
STEEL = (0.34, 0.37, 0.42)
SHEET = (0.2, 0.42, 0.62)
PILE = (0.32, 0.35, 0.38)
WALER = (0.85, 0.62, 0.12)
DIRT = (0.42, 0.33, 0.24)

F = [0.3, 3.9, 7.5, 11.1, 14.7]
SOLIDS = {}


def gpos(x, y, z):
    return Vector((x, -z, y))


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new("Col")
        self.solids = []
        self.rng = random.Random(7)

    def box(self, a, b, c, bevel=0.0, solid=False, jitter=0.0):
        x0, y0, z0 = a
        x1, y1, z1 = b
        lo = (x0, -z1, y0)
        hi = (x1, -z0, y1)
        vs = [self.bm.verts.new((hi[0] if i & 1 else lo[0], hi[1] if i & 2 else lo[1], hi[2] if i & 4 else lo[2])) for i in range(8)]
        quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        fs = [self.bm.faces.new([vs[i] for i in q]) for q in quads]

        if jitter:
            k = 1 + self.rng.uniform(-jitter, jitter)
            c = (c[0] * k, c[1] * k, c[2] * k)

        for f in fs:
            for l in f.loops:
                l[self.col] = (c[0], c[1], c[2], 1.0)

        if bevel >= 0.035:
            es = list({e for f in fs for e in f.edges})
            res = bmesh.ops.bevel(self.bm, geom=vs + es, offset=bevel, segments=1, affect="EDGES", clamp_overlap=True)
            w = (min(1, c[0] * 1.12 + 0.02), min(1, c[1] * 1.12 + 0.02), min(1, c[2] * 1.12 + 0.02), 1.0)
            flat = (c[0], c[1], c[2], 1.0)

            for f in res["faces"]:
                f.normal_update()
                n = f.normal
                strip = max(abs(n.x), abs(n.y), abs(n.z)) < 0.95

                for l in f.loops:
                    l[self.col] = w if strip else flat

        if solid:
            self.solids.append((0, x0, y0, z0, x1, y1, z1))

    def tube(self, a, b, r, c):
        x0, y0, z0 = a
        x1, y1, z1 = b
        self.box((min(x0, x1) - r, min(y0, y1) - r, min(z0, z1) - r), (max(x0, x1) + r, max(y0, y1) + r, max(z0, z1) + r), c)

    def beam(self, a, b, w, h, c):
        pa = gpos(*a)
        pb = gpos(*b)
        d = (pb - pa).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        sx = d.cross(up).normalized() * (w / 2)
        sy = d.cross(sx).normalized() * (h / 2)
        vs = [self.bm.verts.new(p + (sx if i & 1 else -sx) + (sy if i & 2 else -sy)) for p in (pa, pb) for i in range(4)]
        quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]

        for q in quads:
            f = self.bm.faces.new([vs[i] for i in q])

            for l in f.loops:
                l[self.col] = (c[0], c[1], c[2], 1.0)

    def ibeam(self, a, b, size, c, vertical=False):
        x0, y0, z0 = a
        x1, y1, z1 = b
        t = 0.03
        f = size / 2

        if vertical:
            cx = (x0 + x1) / 2
            cz = (z0 + z1) / 2
            self.box((cx - f, y0, cz - f), (cx + f, y1, cz - f + t * 1.5), c)
            self.box((cx - f, y0, cz + f - t * 1.5), (cx + f, y1, cz + f), c)
            self.box((cx - t, y0, cz - f), (cx + t, y1, cz + f), c)
        elif abs(x1 - x0) > abs(z1 - z0):
            cy = (y0 + y1) / 2
            cz = (z0 + z1) / 2
            self.box((x0, cy + f - t * 1.5, cz - f * 0.6), (x1, cy + f, cz + f * 0.6), c)
            self.box((x0, cy - f, cz - f * 0.6), (x1, cy - f + t * 1.5, cz + f * 0.6), c)
            self.box((x0, cy - f, cz - t), (x1, cy + f, cz + t), c)
        else:
            cy = (y0 + y1) / 2
            cx = (x0 + x1) / 2
            self.box((cx - f * 0.6, cy + f - t * 1.5, z0), (cx + f * 0.6, cy + f, z1), c)
            self.box((cx - f * 0.6, cy - f, z0), (cx + f * 0.6, cy - f + t * 1.5, z1), c)
            self.box((cx - t, cy - f, z0), (cx + t, cy + f, z1), c)

    def ramp(self, a, b, rise):
        self.solids.append(({"px": 1, "nx": 2, "pz": 3, "nz": 4}[rise], a[0], a[1], a[2], b[0], b[1], b[2]))

    def solid(self, a, b):
        self.solids.append((0, a[0], a[1], a[2], b[0], b[1], b[2]))

    def merge(self, src):
        me = bpy.data.meshes.new("m")
        src.to_mesh(me)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)


CACHE = {}


def piece(src, keep=None, drop=None):
    key = (src, keep, drop)

    if key not in CACHE:
        path = src if os.path.isabs(src) else os.path.join(P, src + ".glb")
        old = pf.SKIP

        if drop:
            pf.SKIP = re.compile(old.pattern + "|" + drop, re.I)

        bm = load(path)
        pf.SKIP = old

        if keep:
            pass

        CACHE[key] = bm

    return CACHE[key].copy()


def kit(m, src, at, rot=0.0, scale=1.0, center=True, drop=None, k=None):
    bm = piece(src, drop=drop)

    if k:
        tint(bm, k)

    if center:
        lo, hi = bounds(bm)
        bm.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))

    sc = scale if isinstance(scale, tuple) else (scale, scale, scale)
    bm.transform(Matrix.Translation(gpos(*at)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))
    m.merge(bm)
    bm.free()


def hemi(n):
    out = []
    g = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        z = math.sqrt(1 - (i + 0.5) / n)
        r = math.sqrt(1 - z * z)
        a = i * g
        out.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))

    return out


def densify(bm, size):
    for _ in range(6):
        long = [e for e in bm.edges if e.calc_length() > size]

        if not long:
            break

        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)


def bake(bm, reach=2.2, strength=0.75, rays=16, floor=0.0, grime=0.9, seed=1):
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    dirs = hemi(rays)
    rng = random.Random(seed)
    cache = {}

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b2 = n.cross(t)
        cen = f.calc_center_median()
        fv = 1

        for l in f.loops:
            co = l.vert.co
            key = (round(co.x, 2), round(co.y, 2), round(co.z, 2), round(n.x, 1), round(n.y, 1), round(n.z, 1))

            if key not in cache:
                p = co + (cen - co) * 0.04 + n * 0.02
                occ = 0.0

                for d in dirs:
                    w = t * d.x + b2 * d.y + n * d.z
                    hit = tree.ray_cast(p, w, reach)

                    if hit[0] is not None:
                        occ += 1 - (hit[3] / reach) ** 2
                    elif w.z < -0.05 and p.z - floor > -0.05:
                        dist = (p.z - floor) / -w.z

                        if dist < reach:
                            occ += 1 - (dist / reach) ** 2

                ao = 1 - strength * occ / len(dirs)
                h = co.z - floor
                g = 1 - grime * 0.22 * max(0, 1 - h / 0.9) if grime else 1
                cache[key] = (ao * g, max(0, 1 - h / 0.9) * grime)

            ao, dirt = cache[key]
            c = l[col]
            r = c[0] * ao * fv
            gg = c[1] * ao * fv
            bb = c[2] * ao * fv
            r = r + (DIRT[0] * ao - r) * dirt * 0.25
            gg = gg + (DIRT[1] * ao - gg) * dirt * 0.25
            bb = bb + (DIRT[2] * ao - bb) * dirt * 0.25
            l[col] = (r, gg, bb, 1.0)


def export_split(bm, name, limit=18000):
    bm.faces.ensure_lookup_table()
    groups = []
    cur = []
    count = 0

    for f in bm.faces:
        n = len(f.verts) - 2

        if count + n > limit and cur:
            groups.append(cur)
            cur = []
            count = 0

        cur.append(f.index)
        count += n

    if cur:
        groups.append(cur)

    if len(groups) == 1:
        return export(bm, name)

    objs = []
    mat = bpy.data.materials.new("kit")
    mat.use_nodes = True

    for n2 in mat.node_tree.nodes:
        if n2.type == "BSDF_PRINCIPLED":
            n2.inputs["Base Color"].default_value = (1, 1, 1, 1)
            n2.inputs["Roughness"].default_value = 1.0

    for gi, g in enumerate(groups):
        part_bm = bm.copy()
        part_bm.faces.ensure_lookup_table()
        keep = set(g)
        bmesh.ops.delete(part_bm, geom=[f for f in part_bm.faces if f.index not in keep], context="FACES")
        me = bpy.data.meshes.new("%s_%d" % (name, gi))
        part_bm.to_mesh(me)
        part_bm.free()
        me.materials.append(mat)

        for ca in [c for c in me.color_attributes if c.name != "Col"]:
            me.color_attributes.remove(ca)

        me.color_attributes.active_color = me.color_attributes["Col"]
        me.color_attributes.render_color_index = 0
        ob = bpy.data.objects.new("%s_%d" % (name, gi), me)
        bpy.context.scene.collection.objects.link(ob)
        objs.append(ob)

    for o in bpy.context.scene.objects:
        o.select_set(o in objs)

    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(filepath=os.path.join(pf.OUT, name + ".glb"), export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=True)

    try:
        bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_colors=True, **kw)

    vs = [v.co for v in bm.verts]
    tris = sum(len(f.verts) - 2 for f in bm.faces)

    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    return {"file": "construction/" + name + ".glb", "min": [min(v.x for v in vs), min(v.z for v in vs), -max(v.y for v in vs)], "max": [max(v.x for v in vs), max(v.z for v in vs), -min(v.y for v in vs)], "tris": tris}


def finish(m, name, size=1.2, reach=2.2, strength=0.75):
    if size:
        densify(m.bm, size)

    bake(m.bm, reach=reach, strength=strength)
    info = export_split(m.bm, name)
    info["kind"] = "custom"
    info["group"] = "building"
    info["collide"] = "none"
    SOLIDS[name] = m.solids
    print("DONE", name, info["tris"], len(m.solids))
    m.bm.free()

    return info


def rail_run(m, x0, z0, x1, z1, y, solid=True, gap=None):
    h = 1.1
    lx = abs(x1 - x0)
    lz = abs(z1 - z0)
    n = max(1, int(round(max(lx, lz) / 2.0)))

    for i in range(n + 1):
        t = i / n
        px = x0 + (x1 - x0) * t
        pz = z0 + (z1 - z0) * t
        m.box((px - 0.04, y, pz - 0.04), (px + 0.04, y + h, pz + 0.04), RAIL)

    if lx >= lz:
        for hh, c in ((h, RAIL), (0.55, BLACK)):
            m.box((min(x0, x1), y + hh - 0.05, z0 - 0.03), (max(x0, x1), y + hh + 0.02, z0 + 0.03), c)
        m.box((min(x0, x1), y, z0 - 0.02), (max(x0, x1), y + 0.15, z0 + 0.02), TOE)

        if solid:
            m.solid((min(x0, x1), y, z0 - 0.08), (max(x0, x1), y + h, z0 + 0.08))
    else:
        for hh, c in ((h, RAIL), (0.55, BLACK)):
            m.box((x0 - 0.03, y + hh - 0.05, min(z0, z1)), (x0 + 0.03, y + hh + 0.02, max(z0, z1)), c)
        m.box((x0 - 0.02, y, min(z0, z1)), (x0 + 0.02, y + 0.15, max(z0, z1)), TOE)

        if solid:
            m.solid((x0 - 0.08, y, min(z0, z1)), (x0 + 0.08, y + h, max(z0, z1)))


def blockwall(m, x0, z0, x1, z1, y, h, rng):
    course = 0.3
    rows = int(h / course)
    along_x = abs(x1 - x0) >= abs(z1 - z0)
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    a = min(x0, x1) if along_x else min(z0, z1)
    t = 0.1
    full = rows - 2

    def rect(s0, e0, ya, yb, inset=0.0):
        if along_x:
            return (a + s0, ya, z0 - t + inset), (a + e0, yb, z0 + t - inset)

        return (x0 - t + inset, ya, a + s0), (x0 + t - inset, yb, a + e0)

    for r in range(rows):
        lim = length if r < full else length * rng.uniform(0.35, 0.95)
        s = 0.0 if r % 2 == 0 else -0.6
        yy = y + r * course

        while s < lim:
            e = min(s + 1.2, lim)
            s0 = max(s, 0)

            if e - s0 > 0.06:
                lo, hi = rect(s0 + 0.006, e - 0.006, yy + 0.008, yy + course - 0.004)
                m.box(lo, hi, rng.choice(BLOCK))

            s = e

        lo, hi = rect(0, lim, yy, yy + course, 0.02)
        m.box(lo, hi, MORTAR)

        if r >= full:
            lo, hi = rect(0, lim, yy, yy + course)
            m.solid(lo, hi)

    lo, hi = rect(0, length, y, y + full * course)
    m.solid(lo, hi)


def stair(m, x0, x1, z0, z1, y0, y1):
    n = int(round((y1 - y0) / 0.3))
    run = (x1 - x0) / n
    rise = (y1 - y0) / n

    for i in range(n):
        xa = x0 + run * i
        xb = x0 + run * (i + 1)
        lo = min(xa, xb)
        hi = max(xa, xb)
        m.box((lo, y0 + rise * i, z0), (hi, y0 + rise * (i + 1), z1), CONCRETE if i % 2 else SCREED, bevel=0.015)

    m.box((min(x0, x1), y0, z0 - 0.08), (max(x0, x1), y1, z0), CONCRETE_D)
    m.box((min(x0, x1), y0, z1), (max(x0, x1), y1, z1 + 0.08), CONCRETE_D)
    m.ramp((min(x0, x1), y0, z0), (max(x0, x1), y1, z1), "px" if x1 > x0 else "nx")

    for i in range(0, n + 1, 3):
        px = x0 + run * i
        m.box((px - 0.03, y0 + rise * i, z0 - 0.06), (px + 0.03, y0 + rise * i + 1.0, z0 - 0.0), RAIL)

    m.tube((x0, y0 + 1.0, z0 - 0.03), (x1, y1 + 1.0, z0 - 0.03), 0.025, RAIL)


def slab(m, y, x0, x1, z0, z1, holes, deck=False):
    cuts_x = sorted({x0, x1} | {h[0] for h in holes if x0 < h[0] < x1} | {h[1] for h in holes if x0 < h[1] < x1})
    cuts_z = sorted({z0, z1} | {h[2] for h in holes if z0 < h[2] < z1} | {h[3] for h in holes if z0 < h[3] < z1})

    for i in range(len(cuts_x) - 1):
        for j in range(len(cuts_z) - 1):
            ax, bx = cuts_x[i], cuts_x[i + 1]
            az, bz = cuts_z[j], cuts_z[j + 1]
            cx = (ax + bx) / 2
            cz = (az + bz) / 2

            if any(h[0] <= cx <= h[1] and h[2] <= cz <= h[3] for h in holes):
                continue

            m.solid((ax, y - 0.3, az), (bx, y, bz))

            if not deck:
                m.box((ax, y - 0.3, az), (bx, y, bz), CONCRETE)
                continue

            m.box((ax, y - 0.3, az), (bx, y - 0.22, bz), (0.6, 0.62, 0.64))
            m.box((ax + 0.03, y - 0.22, az + 0.03), (bx - 0.03, y - 0.02, bz - 0.03), (0.5, 0.53, 0.56))
            r = az + 0.3

            while r < bz - 0.2:
                m.box((ax + 0.08, y - 0.02, r), (bx - 0.08, y + 0.03, r + 0.04), REBAR)
                r += 0.6

            r = ax + 0.3

            while r < bx - 0.2:
                m.box((r, y - 0.02, az + 0.08), (r + 0.04, y + 0.025, bz - 0.08), REBAR)
                r += 1.2

    if not deck:
        m.box((x0 - 0.02, y - 0.32, z0 - 0.02), (x1 + 0.02, y - 0.22, z0 + 0.12), CONCRETE_D)
        m.box((x0 - 0.02, y - 0.32, z1 - 0.12), (x1 + 0.02, y - 0.22, z1 + 0.02), CONCRETE_D)


def tower(name, X0, X1, Z0, Z1, nf, core, partial, walls, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    W = X1 - X0
    hole_a = (X0 + 1.8, X0 + 8.7, Z0 + 0.4, Z0 + 2.8)
    hole_b = (X1 - 8.7, X1 - 1.8, Z1 - 2.8, Z1 - 0.4)
    cbox = (5.2, 10.6, -1.4, 5.4) if core else None
    mid = round(X0 + W * 0.58)
    mx = (X0 + X1) / 2
    mz = (Z0 + Z1) / 2
    top_y = F[nf]

    m.box((X0 - 0.6, -1.0, Z0 - 0.6), (X1 + 0.6, 0.3, Z1 + 0.6), CONCRETE_D, bevel=0.06)
    m.solid((X0 - 0.6, -1.0, Z0 - 0.6), (X1 + 0.6, 0.3, Z1 + 0.6))

    for i in range(1, nf):
        slab(m, F[i], X0, X1, Z0, Z1, [hole_a if i % 2 else hole_b])

    top_hole = hole_a if nf % 2 else hole_b

    if partial:
        slab(m, top_y, X0, mid, Z0, Z1, [top_hole])
        slab(m, top_y, mid, X1, Z0, Z1, [top_hole] + ([cbox] if cbox else []), deck=True)
    else:
        slab(m, top_y, X0, X1, Z0, Z1, [top_hole])

    nx = max(2, round(W / 8)) + 1
    nz = max(2, round((Z1 - Z0) / 9)) + 1
    cols_x = [X0 + 0.25 + (W - 0.5) * k / (nx - 1) for k in range(nx)]
    cols_z = [Z0 + 0.25 + (Z1 - Z0 - 0.5) * k / (nz - 1) for k in range(nz)]

    def in_core(cx, cz):
        return cbox and cbox[0] - 0.2 < cx < cbox[1] + 0.2 and cbox[2] - 0.2 < cz < cbox[3] + 0.2

    for i in range(nf):
        for cx in cols_x:
            for cz in cols_z:
                if in_core(cx, cz):
                    continue

                m.box((cx - 0.25, F[i], cz - 0.25), (cx + 0.25, F[i + 1] - 0.3, cz + 0.25), CONCRETE, bevel=0.03, solid=True)

    for cx in cols_x:
        for cz in cols_z:
            if in_core(cx, cz):
                continue

            poured = not partial or cx < mid
            h = 0.9 if poured else 0.0

            if poured:
                m.box((cx - 0.25, top_y, cz - 0.25), (cx + 0.25, top_y + h, cz + 0.25), CONCRETE, bevel=0.03)

            for q in range(4):
                ox = -0.15 if q % 2 else 0.15
                oz = -0.15 if q < 2 else 0.15
                m.box((cx + ox - 0.02, top_y + h, cz + oz - 0.02), (cx + ox + 0.02, top_y + h + 1.2, cz + oz + 0.02), REBAR)

            m.solid((cx - 0.25, top_y, cz - 0.25), (cx + 0.25, top_y + h + 1.2, cz + 0.25))

    if cbox:
        cx0, cx1, cz0, cz1 = cbox
        top = top_y + 4.2
        m.box((cx0, 0.3, cz0), (cx1, top, cz0 + 0.3), CONCRETE, bevel=0.04)
        m.box((cx0, 0.3, cz1 - 0.3), (cx1, top, cz1), CONCRETE, bevel=0.04)
        m.box((cx0, 0.3, cz0), (cx0 + 0.3, top, cz1), CONCRETE, bevel=0.04)
        m.box((cx1 - 0.3, 0.3, cz0), (cx1, top, cz1), CONCRETE, bevel=0.04)
        m.solid((cx0, 0.3, cz0), (cx1, top, cz1))

        for side, (a, b) in enumerate(((cz0 - 0.35, cz0), (cz1, cz1 + 0.35))):
            m.box((cx0 - 0.35, top - 2.6, a), (cx1 + 0.35, top + 0.6, b), FORM, bevel=0.03)
            m.box((cx0 - 0.35, top + 0.6, a - 0.6 if side == 0 else b), (cx1 + 0.35, top + 0.7, a if side == 0 else b + 0.6), BOARD[0])

        for a, b in ((cx0 - 0.35, cx0), (cx1, cx1 + 0.35)):
            m.box((a, top - 2.6, cz0 - 0.35), (b, top + 0.6, cz1 + 0.35), FORM, bevel=0.03)

        for x in (cx0 + 0.8, cx1 - 0.8):
            m.box((x - 0.06, top - 2.6, cz0 - 0.9), (x + 0.06, top + 1.4, cz0 - 0.35), RAIL)

        m.box((cx0 + 0.6, F[1] - 0.2, cz0 - 0.02), (cx0 + 2.2, F[1] + 2.2, cz0 + 0.02), SHEET)

    for i in range(nf):
        if i % 2 == 0:
            stair(m, X0 + 2.0, X0 + 8.5, Z0 + 0.6, Z0 + 2.6, F[i], F[i + 1])
        else:
            stair(m, X1 - 2.0, X1 - 8.5, Z1 - 2.6, Z1 - 0.6, F[i], F[i + 1])

    for i in range(1, nf + 1):
        h = hole_a if i % 2 else hole_b
        y = F[i]

        if i % 2:
            rail_run(m, h[0], h[3], h[1] - 1.4, h[3], y)
            rail_run(m, h[0], h[2], h[0], h[3], y)
        else:
            rail_run(m, h[0] + 1.4, h[2], h[1], h[2], y)
            rail_run(m, h[1], h[2], h[1], h[3], y)

    for i in range(1, nf + 1):
        y = F[i]
        rail_run(m, X0, Z1 + 0.05, mx - 1.5, Z1 + 0.05, y)
        rail_run(m, mx + 1.5, Z1 + 0.05, X1, Z1 + 0.05, y)
        rail_run(m, X1 + 0.05, Z0 + 0.5, X1 + 0.05, mz - 1.5, y)
        rail_run(m, X1 + 0.05, mz + 1.5, X1 + 0.05, Z1, y)

        if i > 1:
            rail_run(m, X0 - 0.05, Z0 + 0.5, X0 - 0.05, Z0 + 6.5, y)

        rail_run(m, X0 - 0.05, Z0 + 7.5, X0 - 0.05, Z1, y)

    sx0, sx1 = X0 - 1.0, X1 + 1.0
    sz0, sz1 = Z0 - 1.55, Z0 - 0.15
    std = [sx0 + q * 2.6 for q in range(int((sx1 - sx0) / 2.6) + 1)]
    sx1 = std[-1]

    for x in std:
        for z in (sz0, sz1):
            m.box((x - 0.035, 0.0, z - 0.035), (x + 0.035, top_y + 2.0, z + 0.035), TUBE)
            m.box((x - 0.12, 0.0, z - 0.12), (x + 0.12, 0.06, z + 0.12), STEEL)
            m.solid((x - 0.05, 0.0, z - 0.05), (x + 0.05, top_y + 2.0, z + 0.05))

    for i in range(1, nf + 1):
        y = F[i]

        for q in range(5):
            zz = sz0 + 0.1 + q * 0.26
            m.box((sx0, y - 0.05, zz), (sx1, y, zz + 0.24), BOARD[(q + i) % 3], jitter=0.04)

        m.solid((sx0, y - 0.06, sz0), (sx1, y, sz1))
        m.box((sx0, y, sz0 - 0.02), (sx1, y + 0.15, sz0 + 0.02), TOE)

        for hh in (0.55, 1.05):
            m.tube((sx0, y + hh, sz0 - 0.07), (sx1, y + hh, sz0 - 0.07), 0.024, TUBE)

        m.solid((sx0, y, sz0 - 0.1), (sx1, y + 1.1, sz0))
        m.solid((sx0 - 0.1, y, sz0), (sx0, y + 1.1, sz1))
        m.solid((sx1, y, sz0), (sx1 + 0.1, y + 1.1, sz1))

        for x in std:
            m.tube((x, y - 0.1, sz0), (x, y - 0.1, sz1), 0.024, TUBE)

        if i < nf:
            for q in range(0, len(std) - 1, 2):
                m.beam((std[q], y + 0.2, sz0 - 0.07), (std[q + 1], y + 3.4, sz0 - 0.07), 0.05, 0.05, TUBE)

    for i, x in enumerate(std[:-1]):
        if i % 3 == 1 and nf > 2:
            m.box((x + 0.1, F[2] + 0.4, sz0 - 0.12), (x + 2.5, F[2] + 1.5, sz0 - 0.09), (0.12, 0.3, 0.58))
            m.box((x + 0.25, F[2] + 0.75, sz0 - 0.13), (x + 2.35, F[2] + 1.15, sz0 - 0.125), (0.92, 0.92, 0.9))

    wx0, wx1 = X0 - 2.6, X0 - 0.2
    za0 = Z0 + 7.0
    run = 9.0
    n = 12
    m.box((wx0, F[1] - 0.25, Z0 - 0.2), (wx1, F[1], za0), BOARD[1])
    m.solid((wx0, F[1] - 0.25, Z0 - 0.2), (wx1, F[1], za0))

    for q in range(n):
        za = za0 + run * q / n
        zb = za0 + run * (q + 1) / n
        yy = F[1] - (q + 1) * F[1] / n
        m.box((wx0 + 0.1, yy - 0.06, za), (wx1 - 0.1, yy + 0.01, zb), BOARD[q % 3])
        m.box((wx0 + 0.1, yy - 0.06, zb - 0.04), (wx1 - 0.1, yy + 0.04, zb), TOE)

    m.ramp((wx0, 0.0, za0), (wx1, F[1], za0 + run), "nz")
    m.beam((wx0, F[1] - 0.2, za0), (wx0, 0.0, za0 + run), 0.1, 0.12, STEEL)
    m.beam((wx1, F[1] - 0.2, za0), (wx1, 0.0, za0 + run), 0.1, 0.12, STEEL)

    for z in (za0, za0 + 3, za0 + 6):
        yy = (za0 + run - z) / run * F[1]
        m.box((wx0 - 0.04, 0, z - 0.04), (wx0 + 0.04, yy + 1.1, z + 0.04), TUBE)
        m.box((wx1 - 0.04, 0, z - 0.04), (wx1 + 0.04, yy - 0.1, z + 0.04), TUBE)

    m.beam((wx0, F[1] + 1.0, za0), (wx0, 1.0, za0 + run), 0.05, 0.05, RAIL)
    m.solid((wx0 - 0.1, 0.0, za0), (wx0, F[1] + 1.1, za0 + run))

    for z in (Z0 - 0.2,):
        m.box((wx0 - 0.04, 0, z - 0.04), (wx0 + 0.04, F[1] + 1.1, z + 0.04), TUBE)
        m.box((wx1 - 0.04, 0, z - 0.04), (wx1 + 0.04, F[1], z + 0.04), TUBE)

    rail_run(m, wx0, Z0 - 0.2, wx0, za0, F[1])

    for lvl, x0, z0, x1, z1, h in walls:
        blockwall(m, x0, z0, x1, z1, F[lvl], h, rng)

    for i in range(1, nf):
        for q in range(8):
            x = rng.uniform(X0 + 1, X1 - 3)
            z = rng.uniform(Z0 + 1, Z1 - 2)
            m.box((x, F[i], z), (x + rng.uniform(0.6, 1.6), F[i] + 0.008, z + rng.uniform(0.6, 1.4)), (0.52, 0.51, 0.49))

    return finish(m, name, size=5.0, reach=4.0, strength=0.9)


MAIN_WALLS = [
    (1, -11.9, 3.0, -6.0, 3.0, 2.0),
    (1, -2.0, -4.0, -2.0, 3.0, 1.2),
    (1, -4.5, 5.0, 1.5, 5.0, 2.4),
    (2, -11.9, -3.0, -5.0, -3.0, 1.3),
    (2, -1.0, 2.0, -1.0, 8.6, 2.6),
    (2, 1.5, -4.0, 4.5, -4.0, 1.0),
    (3, -8.0, 1.0, -8.0, 8.6, 1.6),
    (3, -3.0, -5.5, 3.0, -5.5, 2.2),
    (0, -11.9, -5.5, -11.9, 1.5, 2.4),
    (0, 1.0, 8.75, 4.5, 8.75, 1.6),
    (0, -3.0, -1.0, -3.0, 4.5, 1.1),
]

SMALL_WALLS = [
    (0, -7.9, -2.5, -7.9, 0.5, 2.1),
    (0, 1.0, -1.0, 6.0, -1.0, 1.2),
    (0, -4.0, 2.0, -4.0, 5.9, 2.4),
    (1, -6.0, 1.0, -1.0, 1.0, 2.0),
    (1, 3.0, -5.9, 7.9, -5.9, 1.4),
    (2, -2.0, -2.0, -2.0, 2.5, 1.6),
    (2, 2.0, -1.0, 7.0, -1.0, 2.4),
    (3, -7.0, 1.5, -3.0, 1.5, 1.0),
]


def crane():
    reset()
    m = Mesh()

    for k in range(3):
        kit(m, "tower-crane-mast-1784a3", (0, k * 13.75, 0), center=False, drop="foot" if k else None)

    kit(m, "tower-crane-top-d8d9c9", (0, 42.5, 0), center=False)
    m.solid((-2.0, 0, -2.0), (2.0, 42.5, 2.0))

    for x, z in ((-3.0, -3.0), (3.0, -3.0), (-3.0, 3.0), (3.0, 3.0)):
        m.box((x - 0.9, 0.0, z - 0.9), (x + 0.9, 0.9, z + 0.9), CONCRETE_D, bevel=0.05, solid=True)

    return finish(m, "crane", size=0, reach=1.5, strength=0.6)


def cabins():
    reset()
    m = Mesh()
    cab = "site-cabin-e9ee10"

    for k in range(3):
        kit(m, cab, (k * 4.1, 0.0, 0.0), center=True)
        m.solid((k * 4.1 - 2.0, 0.0, -4.0), (k * 4.1 + 2.0, 3.39, 2.0))

    for k in range(2):
        kit(m, cab, (k * 4.1 + 2.05, 3.4, 0.0), center=True)
        m.solid((k * 4.1 + 0.05, 3.39, -4.0), (k * 4.1 + 4.05, 6.78, 2.0))

    y = 3.4
    m.box((-2.05, y - 0.14, 2.0), (10.25, y, 3.8), STEEL)
    m.solid((-2.05, y - 0.14, 2.0), (10.25, y, 3.8))

    for k in range(14):
        x = -2.0 + k * 0.88
        m.box((x, y, 2.02), (x + 0.82, y + 0.02, 3.78), (0.4, 0.43, 0.46))

    rail_run(m, -2.05, 3.8, 10.25, 3.8, y)
    rail_run(m, 10.25, 2.0, 10.25, 3.8, y)

    for x in (-2.0, 2.0, 6.0, 10.2):
        m.box((x - 0.07, 0.0, 3.62), (x + 0.07, y - 0.14, 3.76), STEEL, solid=True)

    n = 12
    x0 = -2.05 - n * 0.6

    for k in range(n):
        xa = x0 + k * 0.6
        yy = y * (k + 1) / n
        m.box((xa, yy - 0.06, 2.1), (xa + 0.6, yy, 3.75), (0.45, 0.48, 0.5))
        m.box((xa, 0.0, 3.72), (xa + 0.05, yy, 3.8), STEEL) if k % 4 == 0 else None

    m.ramp((x0, 0.0, 2.05), (-2.05, y, 3.75), "px")
    m.tube((x0, 1.1, 3.82), (-2.05, y + 1.1, 3.82), 0.03, RAIL)
    m.solid((x0, 0.0, 3.8), (-2.05, y + 1.1, 3.9))

    return finish(m, "cabins", size=0, reach=1.8, strength=0.7)


def frame():
    reset()
    m = Mesh()
    bay = "steel-frame-bay-91d3b6"
    nx, nz = 5, 3
    H = 3.6
    lift_a = (0, 0)
    lift_b = (4, 0)
    open_top = {(0, 2), (2, 1), (4, 2), (1, 0)}

    for li in range(2):
        for i in range(nx):
            for j in range(nz):
                if li == 1 and (i, j) in ((4, 2), (0, 2)):
                    continue

                x = i * 4.0 - 2.0
                z = j * 4.0 - 2.0
                y = (li + 1) * H
                m.ibeam((x, y - 0.32, z), (x + 4.0, y - 0.12, z), 0.2, STEEL)
                m.ibeam((x, y - 0.32, z + 4.0), (x + 4.0, y - 0.12, z + 4.0), 0.2, STEEL)
                m.ibeam((x, y - 0.32, z), (x, y - 0.12, z + 4.0), 0.2, STEEL)
                m.ibeam((x + 4.0, y - 0.32, z), (x + 4.0, y - 0.12, z + 4.0), 0.2, STEEL)

                if (i + j + li) % 4 == 1 and (j == 0 or j == nz - 1):
                    zz = z if j == 0 else z + 4.0
                    m.beam((x + 0.1, li * H + 0.1, zz), (x + 3.9, y - 0.35, zz), 0.08, 0.08, RAIL)
                    m.beam((x + 3.9, li * H + 0.1, zz), (x + 0.1, y - 0.35, zz), 0.08, 0.08, RAIL)

    for i in range(nx + 1):
        for j in range(nz + 1):
            x = i * 4.0 - 2.0
            z = j * 4.0 - 2.0
            top = H if (i, j) in ((5, 3), (0, 3)) else 2 * H
            m.ibeam((x, 0.0, z), (x, top, z), 0.28, STEEL, vertical=True)
            m.box((x - 0.3, 0.0, z - 0.3), (x + 0.3, 0.06, z + 0.3), CONCRETE_D)
            m.solid((x - 0.14, 0.0, z - 0.14), (x + 0.14, top, z + 0.14))

    for li in (1, 2):
        y = li * H

        for i in range(nx):
            for j in range(nz):
                if li == 1 and (i, j) == lift_a:
                    continue

                if li == 2 and ((i, j) in open_top or (i, j) == lift_b):
                    continue

                if li == 2 and (i, j) in ((4, 2), (0, 2)):
                    continue

                x = i * 4.0 - 2.0
                z = j * 4.0 - 2.0
                m.box((x + 0.02, y - 0.12, z + 0.02), (x + 3.98, y, z + 3.98), (0.6, 0.62, 0.64))

                for r in range(8):
                    m.box((x + r * 0.5 + 0.06, y, z + 0.06), (x + r * 0.5 + 0.32, y + 0.02, z + 3.94), (0.5, 0.53, 0.56))

                m.solid((x, y - 0.12, z), (x + 4.0, y, z + 4.0))

    def flight(cell, y0, rise):
        x = cell[0] * 4.0 - 2.0
        z = cell[1] * 4.0 - 2.0
        n = 12

        for k in range(n):
            xa = x + 0.2 + k * 0.3 if rise == "px" else x + 3.8 - (k + 1) * 0.3
            yy = y0 + H * (k + 1) / n
            m.box((xa, yy - 0.08, z + 0.3), (xa + 0.3, yy, z + 1.8), (0.42, 0.45, 0.48))

        m.box((x + 0.2, y0, z + 0.25), (x + 3.8, y0 + 0.08, z + 0.3), STEEL)
        m.box((x + 0.2, y0, z + 1.8), (x + 3.8, y0 + 0.08, z + 1.85), STEEL)
        m.ramp((x + 0.2, y0, z + 0.3), (x + 3.8, y0 + H, z + 1.8), rise)
        m.tube((x + 0.2, y0 + 1.0 + (0 if rise == "px" else H), z + 1.9), (x + 3.8, y0 + 1.0 + (H if rise == "px" else 0), z + 1.9), 0.03, RAIL)

        if y0 > 0:
            m.box((x + 0.2, y0 - 0.12, z + 0.3), (x + 3.8, y0, z + 1.8), (0.5, 0.53, 0.56))

    flight(lift_a, 0.0, "px")
    flight(lift_b, H, "nx")

    for li in (1, 2):
        y = li * H

        for i in range(nx):
            if not (li == 1 and i == 0):
                rail_run(m, i * 4.0 - 2.0, -2.05, i * 4.0 + 2.0, -2.05, y)

            if li == 1 or i not in (0, 4):
                rail_run(m, i * 4.0 - 2.0, nz * 4.0 - 1.95, i * 4.0 + 2.0, nz * 4.0 - 1.95, y)

        for j in range(nz):
            if not (li == 1 and j == 0) and not (li == 2 and j == 2):
                rail_run(m, -2.05, j * 4.0 - 2.0, -2.05, j * 4.0 + 2.0, y)

            if not (li == 2 and j == 2):
                rail_run(m, nx * 4.0 - 1.95, j * 4.0 - 2.0, nx * 4.0 - 1.95, j * 4.0 + 2.0, y)

    for k in range(6):
        x = 1.0 + k * 0.5
        m.box((x, H, 7.0), (x + 0.4, H + 0.25, 9.0), STEEL if k % 2 else (0.42, 0.45, 0.48))

    return finish(m, "frame", size=5.0, reach=1.6, strength=0.7)


def pilewall():
    reset()
    m = Mesh()
    L = 8.0
    H = 7.6
    n = 13

    for k in range(n):
        x = -L / 2 + k * L / n
        d = 0.18 if k % 2 else 0.0
        m.box((x, -H + 0.4, -0.1 + d), (x + L / n * 0.55, 0.4, 0.06 + d), PILE)
        m.box((x + L / n * 0.45, -H + 0.4, -0.04), (x + L / n, 0.4, 0.22), (0.3, 0.33, 0.36))

    for y in (-1.2, -3.6, -6.0):
        m.box((-L / 2, y, 0.25), (L / 2, y + 0.4, 0.55), WALER, bevel=0.03)

    for x in (-2.6, 1.4):
        m.box((x, -3.7, 0.55), (x + 0.25, -1.1, 0.75), STEEL)

    m.box((-L / 2, 0.38, -0.12), (L / 2, 0.48, 0.3), (0.38, 0.29, 0.22))
    m.solid((-L / 2, -H + 0.4, -0.12), (L / 2, 0.4, 0.3))

    return finish(m, "pilewall", size=1.0, reach=1.2, strength=0.6)


def container(name, c, office=False):
    reset()
    m = Mesh()
    L, Wd, H = 6.06, 2.44, 2.59
    x0, x1, z0, z1 = -L / 2, L / 2, -Wd / 2, Wd / 2
    dark = (c[0] * 0.72, c[1] * 0.72, c[2] * 0.72)
    m.box((x0 + 0.1, 0.12, z0 + 0.04), (x1 - 0.1, H - 0.1, z1 - 0.04), c)
    q = 0

    x = x0 + 0.25

    while x < x1 - 0.3:
        for z in (z0, z1 - 0.06):
            m.box((x, 0.15, z), (x + 0.14, H - 0.12, z + 0.06), dark if q % 2 else c)
        x += 0.28
        q += 1

    for cx in (x0, x1 - 0.16):
        for cz in (z0, z1 - 0.16):
            m.box((cx, 0.0, cz), (cx + 0.16, H, cz + 0.16), (0.3, 0.3, 0.31))

    for y in (0.0, H - 0.14):
        m.box((x0, y, z0), (x1, y + 0.14, z0 + 0.12), dark)
        m.box((x0, y, z1 - 0.12), (x1, y + 0.14, z1), dark)
        m.box((x0, y, z0), (x0 + 0.12, y + 0.14, z1), dark)
        m.box((x1 - 0.12, y, z0), (x1, y + 0.14, z1), dark)

    m.box((x1 - 0.1, 0.15, z0 + 0.12), (x1 - 0.02, H - 0.14, z1 - 0.12), dark)

    for zz in (-0.75, -0.3, 0.3, 0.75):
        m.box((x1 - 0.02, 0.2, zz - 0.03), (x1 + 0.03, H - 0.2, zz + 0.03), (0.42, 0.42, 0.43))

    m.box((x1 - 0.02, 0.2, -0.01), (x1 + 0.01, H - 0.2, 0.01), (0.2, 0.2, 0.2))

    if office:
        for wx in (-1.6, 0.6):
            m.box((wx, 1.0, z0 - 0.03), (wx + 1.1, 1.9, z0 + 0.02), (0.9, 0.9, 0.88))
            m.box((wx + 0.06, 1.06, z0 - 0.04), (wx + 1.04, 1.84, z0 - 0.02), (0.24, 0.34, 0.42))

        m.box((-0.2, 0.15, z1 - 0.02), (0.75, 2.1, z1 + 0.03), (0.82, 0.82, 0.8))

    m.solid((x0, 0, z0), (x1, H, z1))

    return finish(m, name, size=0, reach=1.0, strength=0.55)


def cyl(m, base, r, h, axis, seg, c, cap=True):
    tmp = bmesh.new()
    col = tmp.loops.layers.float_color.new("Col")
    bmesh.ops.create_cone(tmp, cap_ends=cap, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=h)

    for v in tmp.verts:
        v.co.z += h / 2

    if axis == "x":
        tmp.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    elif axis == "z":
        tmp.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))

    tmp.transform(Matrix.Translation(gpos(*base)))

    for f in tmp.faces:
        for l in f.loops:
            l[col] = (c[0], c[1], c[2], 1.0)

    me = bpy.data.meshes.new("c")
    tmp.to_mesh(me)
    tmp.free()
    m.bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def pipes():
    reset()
    m = Mesh()
    r = 0.6
    L = 2.4
    pos = [(-1.25, 0.0), (0.0, 0.0), (1.25, 0.0), (-0.62, 1.08), (0.62, 1.08)]

    for i, (x, y) in enumerate(pos):
        cc = (0.56, 0.55, 0.52) if i % 2 else (0.52, 0.51, 0.48)
        cyl(m, (x, y, -L / 2), r, L, "z", 18, cc)
        cyl(m, (x, y + 0.12, -L / 2 - 0.005), r - 0.12, L + 0.01, "z", 18, (0.34, 0.33, 0.32))

    for z in (-0.8, 0.8):
        m.box((-2.0, 0.0, z - 0.08), (2.0, 0.1, z + 0.08), BOARD[1])

    m.solid((-1.85, 0.0, -L / 2), (1.85, 2.2, L / 2))

    return finish(m, "pipes", size=0, reach=1.2, strength=0.7)


def drums():
    reset()
    m = Mesh()
    m.box((-1.1, 0.0, -1.1), (1.1, 0.14, 1.1), BOARD[0])
    cols = [(0.18, 0.32, 0.6), (0.18, 0.32, 0.6), (0.66, 0.18, 0.12), (0.2, 0.42, 0.24)]

    for i, (x, z) in enumerate(((-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5))):
        cyl(m, (x, 0.14, z), 0.29, 0.88, "y", 14, cols[i])

        for y in (0.42, 0.72):
            cyl(m, (x, 0.14 + y, z), 0.3, 0.035, "y", 14, (cols[i][0] * 0.7, cols[i][1] * 0.7, cols[i][2] * 0.7), cap=False)

    m.solid((-1.1, 0.0, -1.1), (1.1, 1.02, 1.1))

    return finish(m, "drums", size=0, reach=0.8, strength=0.6)


def spool():
    reset()
    m = Mesh()
    cyl(m, (-0.55, 0.85, 0), 0.85, 0.1, "x", 16, BOARD[0])
    cyl(m, (0.45, 0.85, 0), 0.85, 0.1, "x", 16, BOARD[0])
    cyl(m, (-0.45, 0.85, 0), 0.55, 0.9, "x", 16, (0.12, 0.12, 0.13))
    m.box((-0.7, 0.0, -0.3), (0.7, 0.1, 0.3), BOARD[2])
    m.solid((-0.6, 0.0, -0.75), (0.6, 1.7, 0.75))

    return finish(m, "spool", size=0, reach=0.8, strength=0.6)


def silo():
    reset()
    m = Mesh()
    cyl(m, (0, 4.5, 0), 1.6, 9.0, "y", 20, (0.82, 0.82, 0.8))
    cyl(m, (0, 13.5, 0), 1.65, 0.25, "y", 20, (0.6, 0.6, 0.6))
    tmp = bmesh.new()
    col = tmp.loops.layers.float_color.new("Col")
    bmesh.ops.create_cone(tmp, cap_ends=False, segments=20, radius1=0.25, radius2=1.6, depth=2.5)
    tmp.transform(Matrix.Translation(Vector((0, 0, 3.25))))

    for f in tmp.faces:
        for l in f.loops:
            l[col] = (0.78, 0.78, 0.76, 1.0)

    me = bpy.data.meshes.new("c")
    tmp.to_mesh(me)
    tmp.free()
    m.bm.from_mesh(me)
    bpy.data.meshes.remove(me)

    for x, z in ((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)):
        m.ibeam((x, 0.0, z), (x, 5.0, z), 0.24, (0.36, 0.38, 0.42), vertical=True)
        m.box((x - 0.3, 0.0, z - 0.3), (x + 0.3, 0.15, z + 0.3), CONCRETE_D)
        m.solid((x - 0.14, 0.0, z - 0.14), (x + 0.14, 5.0, z + 0.14))

    for y in (1.2, 3.6):
        m.box((-1.25, y, -1.25), (1.25, y + 0.12, -1.15), (0.36, 0.38, 0.42))
        m.box((-1.25, y, 1.15), (1.25, y + 0.12, 1.25), (0.36, 0.38, 0.42))

    for y in (6.0, 9.0, 12.0):
        cyl(m, (0, y, 0), 1.63, 0.12, "y", 20, (0.88, 0.62, 0.1), cap=False)

    m.box((-0.25, 0.4, 1.62), (0.25, 13.7, 1.66), (0.4, 0.42, 0.45))

    for y in range(2, 14):
        m.box((-0.25, y, 1.6), (0.25, y + 0.04, 1.75), (0.4, 0.42, 0.45))

    m.box((-0.6, 13.75, -0.6), (0.6, 14.3, 0.6), (0.6, 0.6, 0.6))
    m.box((-0.15, 0.2, -0.15), (0.15, 2.0, 0.15), (0.5, 0.5, 0.5))
    m.solid((-1.6, 5.0, -1.6), (1.6, 13.8, 1.6))

    return finish(m, "silo", size=0, reach=1.5, strength=0.6)


def jersey():
    reset()
    m = Mesh()
    rng = random.Random(3)

    for row in range(2):
        off = 0.0 if row == 0 else 0.8

        for i in range(3):
            x = -2.4 + off + i * 1.6

            if row == 1 and i == 2:
                continue

            c = (0.52, 0.51, 0.48) if (i + row) % 2 else (0.47, 0.46, 0.44)
            m.box((x + 0.02, row * 0.8, -0.4), (x + 1.58, row * 0.8 + 0.78, 0.4), c, bevel=0.05, jitter=0.03)

            for q in (0.4, 1.2):
                m.box((x + q - 0.12, row * 0.8 + 0.78, -0.12), (x + q + 0.12, row * 0.8 + 0.86, 0.12), c)

    m.solid((-2.4, 0.0, -0.4), (2.4, 0.8, 0.4))
    m.solid((-1.6, 0.8, -0.4), (1.6, 1.6, 0.4))

    return finish(m, "blocks", size=0, reach=0.9, strength=0.6)


def timber():
    reset()
    m = Mesh()
    rng = random.Random(9)

    for z in (-0.9, 0.0, 0.9):
        m.box((-2.0, 0.0, z - 0.06), (2.0, 0.1, z + 0.06), (0.4, 0.3, 0.2))

    for layer in range(5):
        y = 0.1 + layer * 0.16

        for i in range(8):
            z = -1.0 + i * 0.25
            ln = rng.uniform(-0.15, 0.15)
            m.box((-2.0 + ln, y, z + 0.01), (2.0 + ln, y + 0.15, z + 0.23), rng.choice(BOARD), jitter=0.05)

    m.box((-0.05, 0.1, -1.03), (0.05, 0.95, 1.03), (0.15, 0.32, 0.6))
    m.solid((-2.0, 0.0, -1.0), (2.0, 0.92, 1.0))

    return finish(m, "timber", size=0, reach=0.8, strength=0.55)


def starter():
    reset()
    m = Mesh()

    m.box((-0.8, 0.0, -0.8), (0.8, 0.45, 0.8), CONCRETE_D)
    m.box((-0.3, 0.45, -0.3), (0.3, 1.5, 0.3), CONCRETE)

    for q in range(4):
        ox = -0.18 if q % 2 else 0.18
        oz = -0.18 if q < 2 else 0.18
        m.box((ox - 0.025, 1.5, oz - 0.025), (ox + 0.025, 2.6, oz + 0.025), REBAR)

    m.box((-0.24, 2.3, -0.24), (0.24, 2.34, 0.24), REBAR)
    m.solid((-0.8, 0.0, -0.8), (0.8, 0.45, 0.8))
    m.solid((-0.3, 0.45, -0.3), (0.3, 2.6, 0.3))

    return finish(m, "starter", size=0, reach=1.0, strength=0.6)


def rebarmat():
    reset()
    m = Mesh()

    for i in range(13):
        x = -3.0 + i * 0.5
        m.box((x - 0.02, 0.12, -1.6), (x + 0.02, 0.16, 1.6), REBAR)

    for i in range(7):
        z = -1.5 + i * 0.5
        m.box((-3.1, 0.16, z - 0.02), (3.1, 0.2, z + 0.02), REBAR)

    for x in (-2.5, 0.0, 2.5):
        for z in (-1.0, 1.0):
            m.box((x - 0.06, 0.0, z - 0.06), (x + 0.06, 0.12, z + 0.06), (0.3, 0.3, 0.3))

    return finish(m, "rebarmat", size=0, reach=0.5, strength=0.4)


def flat_poly(m, pts, y, c):
    vs = [m.bm.verts.new(gpos(x, y, z)) for x, z in pts]
    f = m.bm.faces.new(list(reversed(vs)))
    f.normal_update()

    if f.normal.z < 0:
        f.normal_flip()

    for l in f.loops:
        l[m.col] = (c[0], c[1], c[2], 1.0)


def decal(name, kind):
    reset()
    m = Mesh()
    rng = random.Random(len(name))

    if kind == "tracks":
        for side in (-0.95, 0.95):
            for k in range(10):
                z0 = -5 + k
                w0 = 0.3 + rng.uniform(-0.04, 0.04)
                cx = side + math.sin(k * 0.4) * 0.1
                c = (0.36, 0.3, 0.24) if k % 2 else (0.33, 0.27, 0.22)
                flat_poly(m, [(cx - w0, z0), (cx + w0, z0), (cx + w0 * 0.9, z0 + 1.0), (cx - w0 * 0.9, z0 + 1.0)], 0.03, c)
    elif kind == "puddle":
        n = 16
        pts = []

        for i in range(n):
            a = i / n * math.tau
            r = 1.6 + math.sin(a * 3 + 1) * 0.35 + rng.uniform(-0.15, 0.15)
            pts.append((math.cos(a) * r * 1.3, math.sin(a) * r))

        flat_poly(m, pts, 0.03, (0.24, 0.2, 0.16))
        flat_poly(m, [(x * 0.82, z * 0.82) for x, z in pts], 0.035, (0.2, 0.23, 0.27))
        flat_poly(m, [(x * 0.4 + 0.3, z * 0.3 - 0.2) for x, z in pts], 0.04, (0.34, 0.4, 0.46))
    else:
        for i in range(160):
            x = rng.uniform(-1.8, 1.8)
            z = rng.uniform(-1.8, 1.8)

            if x * x + z * z > 3.3:
                continue

            r = rng.uniform(0.05, 0.12)
            g = rng.uniform(0.32, 0.5)
            c = (g, g * 0.97, g * 0.92)
            a = rng.uniform(0, 3)
            ps = [(x + math.cos(a + q * 2.1) * r, z + math.sin(a + q * 2.1) * r) for q in range(3)]
            top = m.bm.verts.new(gpos(x, r * 0.35 + 0.02, z))
            base = [m.bm.verts.new(gpos(px, 0.0, pz)) for px, pz in ps]

            for q in range(3):
                f = m.bm.faces.new([base[q], base[(q + 1) % 3], top])
                f.normal_update()

                if f.normal.z < 0:
                    f.normal_flip()

                for l in f.loops:
                    l[m.col] = (c[0] * (0.8 + q * 0.1), c[1] * (0.8 + q * 0.1), c[2] * (0.8 + q * 0.1), 1.0)

    bmesh.ops.remove_doubles(m.bm, verts=m.bm.verts, dist=0.0001)
    info = export(m.bm, name)
    info["kind"] = "prop"
    info["group"] = "ground"
    info["collide"] = "none"
    SOLIDS[name] = []
    print("DONE", name, info["tris"])
    m.bm.free()

    return info


def kitprop(name, src, scale=1.0, group="street", collide="box", k=None, drop=None, reach=1.2, strength=0.85):
    reset()
    bm = piece(src, drop=drop)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale)
    bake(bm, reach=reach, strength=strength, rays=12, grime=0.7)
    info = export(bm, name)
    info["kind"] = "prop"
    info["group"] = group
    info["collide"] = collide
    print("DONE", name, info["tris"])
    bm.free()

    return info



def decimate(bm, ratio):
    me = bpy.data.meshes.new("dec")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("dec", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm.clear()
    bm.from_mesh(me2)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(me2)


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



def city(name, src, height):
    reset()
    bm = load(os.path.join(CITY, src + ".glb"))
    lo, hi = bounds(bm)
    normalize(bm, scale=height / (hi.z - lo.z))
    tint(bm, (0.92, 0.94, 1.0))
    decimate(bm, 0.45)
    info = export(bm, name)
    info["kind"] = "prop"
    info["group"] = "building"
    info["collide"] = "none"
    print("DONE", name, info["tris"])
    bm.free()

    return info


PROPS = [
    ("fence", "mesh-site-fence-run-a798a0", {}),
    ("hoarding", "site-hoarding-run-0273b4", {}),
    ("barrier", "crash-barrier-run-b47d1d", {}),
    ("cone", "site-traffic-cone-d3ce94", {"collide": "none"}),
    ("lights", "temporary-traffic-light-04c866", {}),
    ("skip", "builder-s-skip-191d35", {}),
    ("bag", "builder-s-dumpy-bag-89fd1b", {}),
    ("mixer", "cement-mixer-on-a-8fb979", {}),
    ("pallet", "material-pallet-6af263", {}),
    ("precast", "precast-concrete-stack-8945ac", {"k": (0.8, 0.8, 0.8)}),
    ("scafstack", "scaffold-material-stack-836dd2", {"k": (0.85, 0.85, 0.85)}),
    ("rebar", "rebar-assembly-889031", {}),
    ("toilet", "portable-toilet-a3f1a2", {}),
    ("genset", "site-generator-298792", {}),
    ("vault", "site-tool-vault-200e38", {}),
    ("shelter", "smoking-shelter-7e149f", {}),
    ("lamp", "site-lighting-tower-674c45", {"collide": "cylinder"}),
    ("sign", "site-safety-sign-board-5408d5", {}),
    ("spoil", "spoil-heap-9aaa11", {"group": "rock", "reach": 2.5}),
    ("tplate", "trench-plate-30c3a3", {"collide": "none", "group": "ground"}),
    ("formwork", "formwork-wall-panel-run-52e9f5", {}),
    ("core", "concrete-core-section-39af7c", {"k": (0.82, 0.82, 0.82)}),
    ("mud", "mud-and-rut-tile-858785", {"collide": "none", "group": "ground"}),
    ("scaffold", "scaffold-bay-4e051b", {}),
    ("sitecabin", "site-cabin-e9ee10", {}),
    ("framebay", "steel-frame-bay-91d3b6", {"collide": "none"}),
    ("gantry", "loading-gantry-34460f", {"collide": "none"}),
    ("tunnel", "pedestrian-walkway-tunnel-0b194e", {"collide": "none"}),
    ("ibc", os.path.expanduser("~/.cache/polyfork/cprc_x/%s.glb") % "ibc-tote-88385a", {}),
    ("wrap", os.path.expanduser("~/.cache/polyfork/cprc_x/%s.glb") % "stretch-wrapped-pallet-load-b4169b", {}),
    ("sandbags", os.path.expanduser("~/.cache/polyfork/cprc_x/%s.glb") % "sandbag-wall-section-7075ee", {}),
    ("pedbar", os.path.expanduser("~/.cache/polyfork/cprc_x/%s.glb") % "pedestrian-safety-barrier-run-2afeca", {"collide": "none"}),
]

CITYS = [
    ("city_deco", "art-deco-setback-tower-b3a788", 70),
    ("city_office", "office-tower-1538cc", 44),
    ("city_slab", "postwar-apartment-slab-cee5f9", 52),
    ("city_prewar", "prewar-apartment-house-1081a6", 40),
]


def write_solids(path):
    out = ["", "pub const solids = struct {"]

    for name, sol in SOLIDS.items():
        out.append("    pub const %s = [_][7]f32{" % name)

        for s in sol:
            out.append("        .{ %s }," % ", ".join("%.3f" % v for v in s))

        out.append("    };")

    out.append("};")
    out.append("")

    with open(path, "a") as f:
        f.write("\n".join(out))


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "construction")
    os.makedirs(pf.OUT, exist_ok=True)

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(pf.OUT, f))

    infos = {}

    for fn in (lambda: tower("tower", -12, 12, -9, 9, 4, True, True, MAIN_WALLS, 11), lambda: tower("tower2", -8, 8, -6, 6, 3, False, False, SMALL_WALLS, 5), crane, cabins, frame, pilewall, lambda: container("box_red", (0.66, 0.22, 0.14)), lambda: container("box_blue", (0.16, 0.34, 0.56)), lambda: container("box_green", (0.22, 0.42, 0.3)), lambda: container("box_office", (0.86, 0.84, 0.78), office=True), pipes, drums, spool, silo, jersey, timber, starter, rebarmat):
        info = fn()
        infos[info["file"].split("/")[-1][:-4]] = info

    for name, kind in (("tracks", "tracks"), ("puddle", "puddle"), ("gravel", "gravel")):
        infos[name] = decal(name, kind)

    for name, src, opts in PROPS:
        infos[name] = kitprop(name, src, **opts)

    for name, src, h in CITYS:
        infos[name] = city(name, src, h)

    path = os.path.join(root, "src/shared/maps", "construction_kit.zig")
    emit_zig("construction", infos, path)
    write_solids(path)
    squeeze_dir(pf.OUT)


main()
