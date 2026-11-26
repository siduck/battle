import os, sys, math, random, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "salvage")
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|attach-|village|scarecrow|companion|steam-plume|puff-|cloud", re.I)
CITY = ""

CONCRETE = (0.62, 0.6, 0.55)
CONCRETE_D = (0.5, 0.48, 0.44)
SCREED = (0.56, 0.54, 0.5)
BLOCK = [(0.62, 0.6, 0.55), (0.58, 0.56, 0.51)]
MORTAR = (0.48, 0.46, 0.42)
TUBE = (0.44, 0.5, 0.48)
BOARD = [(0.6, 0.42, 0.24), (0.54, 0.37, 0.21), (0.66, 0.47, 0.28)]
TOE = (0.78, 0.56, 0.2)
RAIL = (0.36, 0.62, 0.54)
BLACK = (0.18, 0.17, 0.16)
REBAR = (0.5, 0.26, 0.12)
STEEL = (0.32, 0.36, 0.36)
DIRT = (0.38, 0.3, 0.2)
RUST = [(0.62, 0.3, 0.14), (0.54, 0.24, 0.1), (0.7, 0.38, 0.18), (0.46, 0.22, 0.12)]
MINT = [(0.42, 0.72, 0.62), (0.36, 0.64, 0.56)]
CREAM = (0.86, 0.8, 0.66)
BRASS = (0.8, 0.6, 0.22)
PLATE = [(0.5, 0.52, 0.5), (0.44, 0.46, 0.45), (0.58, 0.56, 0.5)]

F = [0.3, 3.9, 7.5, 11.1]
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

        if bevel > 0:
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

        if keep:
            pf.SKIP = re.compile(keep, re.I)
        elif drop:
            pf.SKIP = re.compile(old.pattern + "|" + drop, re.I)

        bm = load(path)
        pf.SKIP = old

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
        fv = 1 + rng.uniform(-0.035, 0.035)

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

    return {"file": os.environ["DIR"] + "/" + name + ".glb", "min": [min(v.x for v in vs), min(v.z for v in vs), -max(v.y for v in vs)], "max": [max(v.x for v in vs), max(v.z for v in vs), -min(v.y for v in vs)], "tris": tris}


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
        s = 0.0 if r % 2 == 0 else -0.3
        yy = y + r * course

        while s < lim:
            e = min(s + 0.6, lim)
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


def kitprop(name, src, scale=1.0, group="street", collide="box", k=None, drop=None, reach=1.2, strength=0.85, keep=None):
    reset()
    bm = piece(src, keep=keep, drop=drop)

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


def city(name, src, height):
    reset()
    bm = load(os.path.join(CITY, src + ".glb"))
    lo, hi = bounds(bm)
    normalize(bm, scale=height / (hi.z - lo.z))
    tint(bm, (0.92, 0.94, 1.0))
    info = export(bm, name)
    info["kind"] = "prop"
    info["group"] = "building"
    info["collide"] = "none"
    print("DONE", name, info["tris"])
    bm.free()

    return info


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



def plinth_solids(m):
    boxes = footprint(m.bm)

    for b in boxes:
        h = column_height(m.bm, b)
        small = (b[2] - b[0]) * (b[3] - b[1]) < 1.2
        h = min(h, 3.2) if small else h
        m.solid((b[0], -0.6, -b[3]), (b[2], h, -b[1]))
        add_box(m.bm, (b[0] + 0.02, b[1] + 0.02, -1.2), (b[2] - 0.02, b[3] - 0.02, 0.04), (0.42, 0.38, 0.32))


def house(name, parts, scale=1.15, extra=None):
    reset()
    m = Mesh()

    for p in parts:
        src, at, rot = p[0], p[1], p[2]
        drop = p[3] if len(p) > 3 else None
        kit(m, src, (at[0] * scale, at[1] * scale, at[2] * scale), rot=rot, scale=scale, drop=drop)

    if extra:
        extra(m)

    plinth_solids(m)

    return finish(m, name, size=0, reach=1.8, strength=0.8)


def deck(name, L=8.0, W=4.0, H=3.4, ramp=True):
    reset()
    m = Mesh()
    rng = random.Random(len(name))
    x0, x1, z0, z1 = -L / 2, L / 2, -W / 2, W / 2

    for k in range(int(L / 0.5)):
        x = x0 + k * 0.5
        m.box((x + 0.01, H - 0.12, z0), (x + 0.49, H, z1), rng.choice(PLATE + BOARD[:1]), jitter=0.05)

    m.box((x0, H - 0.3, z0), (x1, H - 0.12, z0 + 0.15), RUST[0])
    m.box((x0, H - 0.3, z1 - 0.15), (x1, H - 0.12, z1), RUST[0])
    m.solid((x0, H - 0.3, z0), (x1, H, z1))

    for x in (x0 + 0.2, 0.0, x1 - 0.2):
        for z in (z0 + 0.2, z1 - 0.2):
            cyl(m, (x, 0.0, z), 0.12, H - 0.12, "y", 8, STEEL)
            m.box((x - 0.25, 0.0, z - 0.25), (x + 0.25, 0.12, z + 0.25), CONCRETE_D)
            m.solid((x - 0.13, 0.0, z - 0.13), (x + 0.13, H, z + 0.13))

        m.beam((x, 0.3, z0 + 0.2), (x, H - 0.4, z1 - 0.2), 0.06, 0.06, STEEL)

    rail_run(m, x0, z1, x1, z1, H)
    rail_run(m, x1, z0, x1, z1, H)

    if not ramp:
        rail_run(m, x0, z0, x0, z1, H)
        rail_run(m, x0, z0, x1, z0, H)
    else:
        rail_run(m, x0 + 2.2, z0, x1, z0, H)
        rail_run(m, x0, z0, x0, z1, H)
        n = 14
        run = 9.0

        for q in range(n):
            za = z0 - run + q * run / n
            yy = H * (q + 1) / n
            m.box((x0 + 0.1, yy - 0.08, za), (x0 + 2.1, yy, za + run / n), rng.choice(BOARD), jitter=0.04)

        m.beam((x0 + 0.1, 0.0, z0 - run), (x0 + 0.1, H - 0.1, z0), 0.1, 0.14, RUST[1])
        m.beam((x0 + 2.1, 0.0, z0 - run), (x0 + 2.1, H - 0.1, z0), 0.1, 0.14, RUST[1])
        m.ramp((x0 + 0.1, 0.0, z0 - run), (x0 + 2.1, H, z0), "pz")
        m.beam((x0 + 2.2, 1.0, z0 - run), (x0 + 2.2, H + 1.0, z0), 0.05, 0.05, RAIL)
        m.solid((x0 + 2.15, 0.0, z0 - run), (x0 + 2.3, H + 1.1, z0))

    for k in range(3):
        x = x0 + 1.5 + k * 2.4
        m.box((x, H, z1 - 1.0), (x + 0.8, H + 0.8, z1 - 0.2), rng.choice(RUST), bevel=0.03)
        m.solid((x, H, z1 - 1.0), (x + 0.8, H + 0.8, z1 - 0.2))

    return finish(m, name, size=0, reach=1.6, strength=0.75)


def recolor(m, faces, c):
    bmesh.ops.recalc_face_normals(m.bm, faces=faces)

    for f in faces:
        for l in f.loops:
            l[m.col] = (c[0], c[1], c[2], 1.0)


def frame_of(d):
    d = d.normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized()
    v = d.cross(u).normalized()

    return d, u, v


def tcyl(m, a, b, r, c, seg=8, cap=True):
    pa = gpos(*a)
    pb = gpos(*b)
    d, u, v = frame_of(pb - pa)
    ra = []
    rb = []

    for i in range(seg):
        t = math.tau * i / seg
        o = (u * math.cos(t) + v * math.sin(t)) * r
        ra.append(m.bm.verts.new(pa + o))
        rb.append(m.bm.verts.new(pb + o))

    faces = [m.bm.faces.new([ra[i], ra[(i + 1) % seg], rb[(i + 1) % seg], rb[i]]) for i in range(seg)]

    if cap:
        faces.append(m.bm.faces.new(list(reversed(ra))))
        faces.append(m.bm.faces.new(rb))

    recolor(m, faces, c)


def torus(m, center, normal, R, r, c, seg=10, sides=4):
    n, u, v = frame_of(Vector(normal))
    o = gpos(*center)
    rings = []

    for i in range(seg):
        a = math.tau * i / seg
        radial = u * math.cos(a) + v * math.sin(a)
        ring = []

        for j in range(sides):
            b = math.tau * j / sides + math.pi / sides
            ring.append(m.bm.verts.new(o + radial * (R + r * math.cos(b)) + n * (r * math.sin(b))))

        rings.append(ring)

    faces = []

    for i in range(seg):
        a = rings[i]
        b = rings[(i + 1) % seg]

        for j in range(sides):
            k = (j + 1) % sides
            faces.append(m.bm.faces.new([a[j], a[k], b[k], b[j]]))

    recolor(m, faces, c)


def ibeam_t(m, a, b, size, c):
    pa = gpos(*a)
    pb = gpos(*b)
    d, u, v = frame_of(pb - pa)
    f = size / 2

    for off, w, h in ((v * f, size, 0.05), (-v * f, size, 0.05), (Vector((0, 0, 0)), 0.05, size)):
        qa = pa + off
        qb = pb + off
        game_a = (qa.x, qa.z, -qa.y)
        game_b = (qb.x, qb.z, -qb.y)
        m.beam(game_a, game_b, w, h, c)


def tyre(m, x, y, z, rng, flat=True):
    if flat:
        nrm = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 1.0)
    else:
        a = rng.uniform(0, math.tau)
        nrm = (math.cos(a), math.sin(a), rng.uniform(-0.4, 0.4))

    torus(m, (x, y, z), nrm, 0.36, 0.14, rng.choice([BLACK, (0.22, 0.21, 0.2), (0.15, 0.15, 0.15)]))


def drum_t(m, a, b, c):
    tcyl(m, a, b, 0.3, c, seg=10)
    pa = Vector(a)
    pb = Vector(b)

    for q in (0.3, 0.7):
        p = pa + (pb - pa) * q
        d = (pb - pa).normalized() * 0.04
        tcyl(m, tuple(p - d), tuple(p + d), 0.32, (c[0] * 0.75, c[1] * 0.75, c[2] * 0.75), seg=10, cap=False)


SCRAP = RUST + PLATE + PLATE + MINT + [BRASS, (0.62, 0.6, 0.55), (0.5, 0.54, 0.58), (0.72, 0.62, 0.42), (0.78, 0.74, 0.64), (0.36, 0.46, 0.62), (0.74, 0.58, 0.2), (0.6, 0.24, 0.18)]
PAINT = [(0.36, 0.46, 0.62), (0.74, 0.58, 0.2), (0.6, 0.24, 0.18), (0.42, 0.66, 0.58), (0.8, 0.76, 0.66), (0.4, 0.5, 0.36)]


def heap(name, seed, w=10.0, d=7.0, h=4.0):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    lobes = [(0.0, 0.0, w / 2, d / 2, h)]

    for i in range(2):
        a = rng.uniform(0, math.tau)
        lobes.append((math.cos(a) * w * 0.22, math.sin(a) * d * 0.22, w * rng.uniform(0.25, 0.34), d * rng.uniform(0.25, 0.34), h * rng.uniform(0.55, 0.8)))

    def top(x, z):
        best = 0.0

        for lx, lz, aw, ad, lh in lobes:
            e = ((x - lx) / aw) ** 2 + ((z - lz) / ad) ** 2

            if e < 1:
                best = max(best, lh * (1 - e) ** 0.8)

        return best

    def grad(x, z):
        e = 0.05

        return ((top(x + e, z) - top(x - e, z)) / (2 * e), (top(x, z + e) - top(x, z - e)) / (2 * e))

    for lx, lz, aw, ad, lh in lobes:
        y = 0.0

        while y < lh - 0.5:
            y1 = y + 0.6
            k = max(0.0, 1 - (y1 / lh) ** (1 / 0.8)) ** 0.5
            m.box((lx - aw * k * 0.78, y, lz - ad * k * 0.78), (lx + aw * k * 0.78, y1, lz + ad * k * 0.78), (0.3, 0.24, 0.19))
            y = y1

    count = int(w * d * 1.05)

    for i in range(count):
        a = rng.uniform(0, math.tau)
        r = math.sqrt(rng.uniform(0.0, 1.0)) * 0.97
        x = math.cos(a) * w / 2 * r
        z = math.sin(a) * d / 2 * r
        y = top(x, z)

        if y < 0.15:
            continue

        gx, gz = grad(x, z)
        gl = math.hypot(gx, gz)

        if gl > 1e-3 and rng.random() < 0.75:
            dx, dz = -gx / gl, -gz / gl
        else:
            ang = rng.uniform(0, math.tau)
            dx, dz = math.cos(ang), math.sin(ang)

        slope = min(gl, 2.0)
        ln = rng.uniform(1.2, 2.4)
        twist = rng.uniform(-0.5, 0.5)
        cx, cz = dx * math.cos(twist) - dz * math.sin(twist), dx * math.sin(twist) + dz * math.cos(twist)
        pa = (x - cx * ln / 2, y + slope * ln / 2 * 0.8 + rng.uniform(-0.1, 0.15), z - cz * ln / 2)
        pb = (x + cx * ln / 2, y - slope * ln / 2 * 0.8 + rng.uniform(-0.1, 0.15), z + cz * ln / 2)
        m.beam(pa, pb, rng.uniform(0.7, 1.5), rng.uniform(0.05, 0.22), rng.choice(SCRAP))

    for i in range(int(w * d / 4.5)):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.15, 0.95)
        x = math.cos(a) * w / 2 * r
        z = math.sin(a) * d / 2 * r
        yy = top(x, z)
        kind = rng.random()

        if kind < 0.2:
            ang = a + rng.uniform(-0.6, 0.6)
            ln = rng.uniform(3.0, 6.0)
            rise = rng.uniform(0.2, 0.75)
            pa = (x - math.cos(ang) * ln * 0.3, yy - 0.3, z - math.sin(ang) * ln * 0.3)
            pb = (x + math.cos(ang) * ln * 0.7, max(0.2, yy - 0.3 + ln * 0.7 * rise * rng.choice([1, 1, -0.5])), z + math.sin(ang) * ln * 0.7)
            ibeam_t(m, pa, pb, rng.uniform(0.24, 0.36), rng.choice(RUST + [STEEL, (0.74, 0.58, 0.2)]))
        elif kind < 0.34:
            ang = rng.uniform(0, math.tau)
            ln = rng.uniform(2.0, 4.0)
            rr = rng.uniform(0.14, 0.34)
            pa = (x, yy + rr - 0.1, z)
            pb = (x + math.cos(ang) * ln, max(rr, yy + rr - 0.1 + rng.uniform(-0.8, 0.9)), z + math.sin(ang) * ln)
            tcyl(m, pa, pb, rr, rng.choice(MINT + [BRASS, STEEL, RUST[2], (0.78, 0.74, 0.64)]))
        elif kind < 0.56:
            tyre(m, x, yy + 0.05, z, rng, flat=rng.random() < 0.5)
        elif kind < 0.7:
            ang = rng.uniform(0, math.tau)
            tilt = rng.uniform(0, 1)
            pa = (x, yy, z)
            pb = (x + math.cos(ang) * 0.9 * tilt, yy + 0.9 * (1 - tilt) + 0.3 * tilt, z + math.sin(ang) * 0.9 * tilt)
            drum_t(m, pa, pb, rng.choice(PAINT + [RUST[0]]))
        elif kind < 0.8:
            s = rng.uniform(0.6, 1.0)
            ang = rng.uniform(0, math.tau)
            m.beam((x - math.cos(ang) * s / 2, yy + s / 2 - 0.15, z - math.sin(ang) * s / 2), (x + math.cos(ang) * s / 2, yy + s / 2 - 0.05, z + math.sin(ang) * s / 2), s, s, rng.choice(BOARD + PAINT))
        elif kind < 0.9:
            ang = rng.uniform(0, math.tau)
            rr = rng.uniform(0.5, 0.85)
            pa = (x, yy + rr * 0.6, z)
            pb = (x + math.cos(ang) * 0.2, yy + rr * 0.6, z + math.sin(ang) * 0.2)
            tcyl(m, pa, pb, rr, rng.choice([STEEL, RUST[3], BRASS]), seg=10)
            tcyl(m, (x - math.cos(ang) * 0.12, yy + rr * 0.6, z - math.sin(ang) * 0.12), (x + math.cos(ang) * 0.34, yy + rr * 0.6, z + math.sin(ang) * 0.34), rr * 0.3, (0.28, 0.28, 0.28), seg=6)
        else:
            ang = rng.uniform(0, math.tau)
            ln = rng.uniform(2.2, 3.4)
            pa = (x - math.cos(ang) * ln / 2, yy + 0.2, z - math.sin(ang) * ln / 2)
            pb = (x + math.cos(ang) * ln / 2, yy + 0.2 + rng.uniform(0.3, 1.2), z + math.sin(ang) * ln / 2)
            m.beam(pa, pb, rng.uniform(1.1, 1.6), rng.uniform(0.7, 1.0), rng.choice(PAINT))

    for i in range(11):
        a = math.tau * i / 11 + rng.uniform(-0.2, 0.2)
        ex = math.cos(a) * (w / 2 + rng.uniform(0.2, 0.8))
        ez = math.sin(a) * (d / 2 + rng.uniform(0.2, 0.8))
        q = rng.uniform(0.5, 0.75)
        ix = math.cos(a) * w / 2 * q
        iz = math.sin(a) * d / 2 * q
        iy = max(0.8, top(ix, iz) * rng.uniform(0.6, 0.9))
        m.beam((ex, 0.05, ez), (ix, iy, iz), rng.uniform(1.0, 2.0), 0.06, rng.choice(PLATE + PAINT + RUST))

    for i in range(9):
        a = rng.uniform(0, math.tau)
        x = math.cos(a) * (w / 2 + rng.uniform(0.2, 1.8))
        z = math.sin(a) * (d / 2 + rng.uniform(0.2, 1.8))
        r = rng.random()

        if r < 0.4:
            tyre(m, x, 0.14, z, rng)
        elif r < 0.6:
            drum_t(m, (x, 0, z), (x, 0.9, z), rng.choice(PAINT))
        else:
            s = rng.uniform(0.5, 1.2)
            ang = rng.uniform(0, math.tau)
            m.beam((x - math.cos(ang) * s, 0.05, z - math.sin(ang) * s), (x + math.cos(ang) * s, 0.09, z + math.sin(ang) * s), rng.uniform(0.4, 0.9), 0.08, rng.choice(SCRAP))

    for tier in range(4):
        y0 = h * tier / 4
        y1 = h * (tier + 1) / 4
        k = max(0.0, 1 - (y1 / h) ** (1 / 0.8)) ** 0.5
        m.solid((-w / 2 * k * 0.7, y0 - 0.5 if tier == 0 else y0, -d / 2 * k * 0.7), (w / 2 * k * 0.7, y1, d / 2 * k * 0.7))

    return finish(m, name, size=0, reach=1.2, strength=0.45)


def debris(name, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)

    for i in range(26):
        x = rng.uniform(-2.2, 2.2)
        z = rng.uniform(-2.2, 2.2)
        ang = rng.uniform(0, math.tau)
        s = rng.uniform(0.15, 0.7)
        hh = rng.uniform(0.03, 0.12)

        if rng.random() < 0.25:
            tcyl(m, (x, 0.07, z), (x + math.cos(ang) * s * 2, 0.07, z + math.sin(ang) * s * 2), 0.07, rng.choice(RUST + [STEEL]), seg=5, cap=False)
        else:
            m.beam((x - math.cos(ang) * s, hh / 2, z - math.sin(ang) * s), (x + math.cos(ang) * s, hh / 2 + rng.uniform(-0.03, 0.06), z + math.sin(ang) * s), rng.uniform(0.15, 0.6), hh, rng.choice(SCRAP))

    return finish(m, name, size=0, reach=0.4, strength=0.3)


def tyre_stack(name, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)

    for i in range(5):
        torus(m, (rng.uniform(-0.06, 0.06), 0.14 + i * 0.27, rng.uniform(-0.06, 0.06)), (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 1.0), 0.36, 0.14, rng.choice([BLACK, (0.22, 0.21, 0.2)]))

    m.solid((-0.45, 0, -0.45), (0.45, 1.5, 0.45))

    return finish(m, name, size=0, reach=0.8, strength=0.5)


def tyre_one(name):
    reset()
    m = Mesh()
    torus(m, (0, 0.14, 0), (0.08, 0.0, 1.0), 0.36, 0.14, BLACK)

    return finish(m, name, size=0, reach=0.5, strength=0.4)


def pallet(name):
    reset()
    m = Mesh()
    wood = (0.72, 0.56, 0.34)

    for z in (-0.5, 0.0, 0.5):
        m.box((-0.6, 0.0, z - 0.05), (0.6, 0.1, z + 0.05), (wood[0] * 0.85, wood[1] * 0.85, wood[2] * 0.85))

    for x in (-0.5, -0.25, 0.0, 0.25, 0.5):
        m.box((x - 0.07, 0.1, -0.6), (x + 0.07, 0.14, 0.6), wood)

    return finish(m, name, size=0, reach=0.5, strength=0.4)


def barrel(name, c, tip=False):
    reset()
    m = Mesh()

    if tip:
        drum_t(m, (-0.45, 0.3, 0), (0.45, 0.3, 0), c)
        m.solid((-0.45, 0, -0.3), (0.45, 0.6, 0.3))
    else:
        drum_t(m, (0, 0, 0), (0, 0.9, 0), c)
        m.solid((-0.3, 0, -0.3), (0.3, 0.9, 0.3))

    return finish(m, name, size=0, reach=0.6, strength=0.4)


def girders(name, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)

    for x in (-2.0, 0.0, 2.0):
        m.box((x - 0.12, 0, -0.9), (x + 0.12, 0.18, 0.9), BOARD[1])

    for layer in range(3):
        for i in range(4 - layer):
            z = -0.6 + i * 0.4 + layer * 0.2
            y = 0.18 + layer * 0.3
            ibeam_t(m, (-3.0 + rng.uniform(-0.3, 0.3), y + 0.13, z), (3.0 + rng.uniform(-0.3, 0.3), y + 0.13, z), 0.26, rng.choice(RUST + [STEEL]))

    m.solid((-3.2, 0, -0.9), (3.2, 1.1, 0.9))

    return finish(m, name, size=0, reach=1.0, strength=0.6)


def kitx(name, src, scale=1.0, collide="box", sat=1.0, post=None, reach=1.2, group="street"):
    reset()
    bm = piece(src)
    normalize(bm, scale=scale)

    if sat != 1.0 or post:
        col = bm.loops.layers.float_color["Col"]
        k = post or (1, 1, 1)

        for f in bm.faces:
            for l in f.loops:
                c = l[col]
                g = (c[0] + c[1] + c[2]) / 3
                l[col] = tuple(min(1.0, (g + (c[i] - g) * sat) * k[i]) for i in range(3)) + (1.0,)

    bake(bm, reach=reach, strength=0.8, rays=12, grime=0.7)
    info = export(bm, name)
    info["kind"] = "prop"
    info["group"] = group
    info["collide"] = collide
    print("DONE", name, info["tris"])
    bm.free()

    return info


def plates(name, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)

    for k in range(6):
        x = -6 + k * 2.0
        h = rng.uniform(1.6, 2.6)
        c = rng.choice(PLATE + RUST)
        m.box((x + 0.02, 0, -0.08), (x + 1.98, h, 0.08), c, bevel=0.02)

        for r in range(3):
            m.box((x + 0.15 + r * 0.6, 0.2, 0.08), (x + 0.2 + r * 0.6, h - 0.2, 0.11), (c[0] * 0.75, c[1] * 0.75, c[2] * 0.75))

        m.box((x + 0.9, 0, -0.35), (x + 1.1, h * 0.7, -0.08), STEEL)
        m.solid((x, 0, -0.1), (x + 2.0, h, 0.1))

    return finish(m, name, size=0, reach=1.0, strength=0.7)


BLD = [
    ("hall_cottage", [("riveted-boiler-hall-da0c09", (0, 0, 0), 0), ("plate-cottage-9b52be", (0, 5.0, -2.0), math.pi), ("cowled-chimney-stack-de5055", (1.2, 5.0, 2.2), 0)]),
    ("terrace", [("plate-cottage-9b52be", (-4.0, 0, 0), 0), ("riveted-boiler-hall-da0c09", (0, 0, 2.0), math.pi / 2), ("plate-cottage-9b52be", (4.0, 0, 0), 0), ("roof-solar-array-c4b996", (4.0, 4.9, 0), 0)]),
    ("dome", [("copper-dome-dwelling-dc8848", (0, 0, 0), 0), ("corrugated-awning-e758eb", (0, 0, -2.6), 0)]),
    ("loft", [("gantry-loft-8da389", (0, 0, 0), 0), ("external-spiral-stair-e98a0a", (2.7, 0, 1.2), 0)]),
    ("conserv", [("glass-conservatory-a938d5", (0, 0, 0), 0), ("glass-cold-frame-3cf74e", (0, 0, -3.0), 0)]),
    ("shed", [("machine-shed-be7361", (0, 0, 0), 0)]),
    ("gate", [("arch-gatehouse-f4391b", (0, 0, 0), 0)]),
    ("cottage", [("plate-cottage-9b52be", (0, 0, 0), 0), ("corrugated-awning-e758eb", (0, 0, -2.6), 0), ("roof-solar-array-c4b996", (0, 4.9, 0), 0)]),
    ("silo", [("rolled-plate-silo-42304a", (0, 0, 0), 0), ("bolted-ladder-da8166", (0, 0, 2.2), 0)]),
    ("water", [("brass-water-tower-b0c6d9", (0, 0, 0), 0)]),
]

PROPS = [
    ("crate", "salvage-crate-3a7e1d", {"scale": 1.2}),
    ("fence", "salvage-fence-run-e9538a", {}),
    ("fgate", "salvage-fence-gate-42350a", {}),
    ("catwalk", "catwalk-gantry-run-f23cac", {}),
    ("platform", "catwalk-corner-ae4630", {}),
    ("pipe", "pipe-run-280a0d", {}),
    ("junction", "pipe-junction-5b146a", {}),
    ("drum", "cut-open-drum-planter-7c42e7", {}),
    ("butt", "brass-fitted-water-butt-3bca1b", {}),
    ("lamp", "brass-post-lamp-984201", {"collide": "cylinder"}),
    ("chimney", "cowled-chimney-stack-de5055", {}),
    ("panel", "gauge-and-valve-panel-f2164c", {}),
    ("planter", "ledge-planter-box-2f38f5", {}),
    ("crop", "bed-crop-plant-1d5ab7", {"collide": "none", "group": "bush"}),
    ("bale", "straw-bale-56facd", {}),
    ("tree", "fruit-tree-4bb1af", {"collide": "trunk", "group": "tree", "scale": 1.3}),
    ("bush", "leafy-bush-d37bba", {"collide": "none", "group": "bush", "scale": 1.2}),
    ("rock", "field-rock-5e37c6", {"group": "rock", "scale": 1.6}),
    ("tuft", "grass-tuft-62e90c", {"collide": "none", "group": "bush", "scale": 1.6}),
    ("flower", "wildflower-plant-cf4279", {"collide": "none", "group": "bush", "scale": 1.6}),
    ("tracker", "tilting-solar-tracker-48051b", {"collide": "cylinder"}),
    ("spinner", "oil-drum-wind-spinner-7c1a9d", {"collide": "cylinder"}),
    ("washing", "washing-line-06b44e", {"collide": "none"}),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "salvage")
    os.makedirs(pf.OUT, exist_ok=True)

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(pf.OUT, f))

    infos = {}

    for name, parts in BLD:
        infos[name] = house(name, parts)

    for fn in (lambda: deck("deck"), lambda: deck("deck_long", L=12.0, ramp=False), lambda: heap("heap_a", 3), lambda: heap("heap_b", 8, w=8, d=8, h=5.0), lambda: heap("heap_c", 13, w=14, d=6, h=3.2), lambda: plates("plates", 5)):
        info = fn()
        infos[info["file"].split("/")[-1][:-4]] = info

    for fn, collide in ((lambda: tyre_stack("tyres", 4), "box"), (lambda: tyre_one("tyre"), "none"), (lambda: debris("debris", 21), "none"), (lambda: pallet("pallet"), "none"), (lambda: barrel("barrel", RUST[0]), "cylinder"), (lambda: barrel("barrel_b", (0.36, 0.44, 0.56)), "cylinder"), (lambda: barrel("barrel_t", MINT[0], tip=True), "box"), (lambda: girders("girders", 6), "box")):
        info = fn()
        info["collide"] = collide
        info["group"] = "street"
        infos[info["file"].split("/")[-1][:-4]] = info

    infos["debris"]["group"] = "ground"
    infos["box"] = kitx("box", "x/cargo-container-fd73bc", scale=2.4, group="building")
    infos["box_rust"] = kitx("box_rust", "x/cargo-container-fd73bc", scale=2.4, sat=0.0, post=(1.3, 0.66, 0.42), group="building")
    infos["crane"] = kitx("crane", "x/yard-crane-316e4a", scale=2.2, collide="none", reach=2.0, group="building")
    infos["hull"] = kitx("hull", "x/salvaged-machine-hull-section-e18dc6", scale=2.0, reach=2.0, group="building")
    infos["wreck"] = kitx("wreck", "x/wreckage-chunk-39ddf9", scale=1.6, reach=1.6)
    infos["cable"] = kitx("cable", "x/signal-cable-drum-88e3f8")
    infos["skip"] = kitx("skip", "x/builder-s-skip-191d35")
    infos["rails"] = kitx("rails", "x/spare-rail-stack-99d443")
    infos["sleepers"] = kitx("sleepers", "x/sleeper-stack-67628e")

    for name, kind in (("puddle", "puddle"), ("gravel", "gravel")):
        infos[name] = decal(name, kind)

    for name, src, opts in PROPS:
        infos[name] = kitprop(name, src, **opts)

    path = os.path.join(root, "src/shared/maps", "salvage_kit.zig")
    emit_zig("salvage", infos, path)
    write_solids(path)


main()
