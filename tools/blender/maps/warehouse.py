import os, sys, math, random, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "warehouse")
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|attach-|shunter", re.I)
CITY = ""
LX = os.path.expanduser("~/.cache/polyfork/labx")

CONCRETE = (0.62, 0.61, 0.58)
CONCRETE_D = (0.48, 0.48, 0.47)
SCREED = (0.56, 0.56, 0.54)
BLOCK = [(0.6, 0.59, 0.56)]
MORTAR = (0.48, 0.46, 0.42)
TUBE = (0.56, 0.6, 0.64)
BOARD = [(0.66, 0.48, 0.27), (0.6, 0.43, 0.24), (0.7, 0.52, 0.3)]
TOE = (0.86, 0.66, 0.12)
RAIL = (0.9, 0.7, 0.1)
BLACK = (0.16, 0.16, 0.17)
REBAR = (0.46, 0.25, 0.13)
STEEL = (0.34, 0.37, 0.42)
DIRT = (0.36, 0.34, 0.31)
CLAD = [(0.42, 0.5, 0.58), (0.38, 0.46, 0.54)]
CLAD_B = [(0.36, 0.48, 0.4), (0.32, 0.43, 0.36)]
CLAD_C = [(0.56, 0.24, 0.18), (0.5, 0.21, 0.16)]
ROOF = (0.5, 0.52, 0.54)
UPRIGHT = (0.16, 0.34, 0.6)
BEAM = (0.9, 0.46, 0.12)
SHUTTER = (0.6, 0.62, 0.62)
HAZARD = (0.92, 0.72, 0.1)
FLOORC = (0.58, 0.58, 0.56)

F = [0.3]
SOLIDS = {}


def gpos(x, y, z):
    return Vector((x, -z, y))


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new("Col")
        self.solids = []
        self.rng = random.Random(7)

    def box(self, a, b, c, bevel=0.0, solid=False, jitter=0.0, skip=()):
        x0, y0, z0 = a
        x1, y1, z1 = b
        lo = (x0, -z1, y0)
        hi = (x1, -z0, y1)
        vs = [self.bm.verts.new((hi[0] if i & 1 else lo[0], hi[1] if i & 2 else lo[1], hi[2] if i & 4 else lo[2])) for i in range(8)]
        named = {"bottom": (0, 2, 3, 1), "top": (4, 5, 7, 6), "zhi": (0, 1, 5, 4), "zlo": (2, 6, 7, 3), "xlo": (0, 4, 6, 2), "xhi": (1, 3, 7, 5)}
        quads = [q for n, q in named.items() if n not in skip]
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
    elif kind == "lane":
        flat_poly(m, [(-0.12, -1.5), (0.12, -1.5), (0.12, 1.5), (-0.12, 1.5)], 0.03, (0.86, 0.68, 0.14))
    elif kind == "bay":
        flat_poly(m, [(-0.08, -2.5), (0.08, -2.5), (0.08, 2.5), (-0.08, 2.5)], 0.03, (0.86, 0.86, 0.82))
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

    if k == "decross":
        col = bm.loops.layers.float_color["Col"]

        for f in bm.faces:
            for l in f.loops:
                c = l[col]

                if c[0] > 0.45 and c[1] < 0.35 and c[2] < 0.35:
                    l[col] = (0.8, 0.8, 0.78, 1.0)
    elif k:
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



def mat_color(mat):
    if mat is None:
        return (0.8, 0.8, 0.8)

    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                c = n.inputs["Base Color"].default_value
                return tuple(max(0.0, min(1.0, v)) ** (1 / 2.2) for v in c[:3])

    c = mat.diffuse_color
    return tuple(max(0.0, min(1.0, v)) ** (1 / 2.2) for v in c[:3])


def load_any(path, door_to=None):
    reset()
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()

    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        if pf.SKIP.search(o.name):
            continue

        me = o.data
        src = me.color_attributes[0] if len(me.color_attributes) else None
        mats = [s.material for s in o.material_slots]
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
            mc = mat_color(mats[p.material_index] if p.material_index < len(mats) else None)

            for l, li in zip(f.loops, p.loop_indices):
                c = src.data[li].color_srgb if src is not None else mc

                l[col] = (c[0], c[1], c[2], 1.0)

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    return bm


pf.load = load_any
load = load_any
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




def clad_box(m, a, b, cols, along_x, rib=0.7, outside=0):
    x0, y0, z0 = a
    x1, y1, z1 = b
    m.box(a, b, cols[0])
    m.solid(a, b)

    if along_x:
        x = x0 + 0.05
        k = 0

        while x < x1 - 0.1:
            e = min(x + rib * 0.5, x1)

            for z in ((z0 - 0.04,) if outside < 0 else (z1,) if outside > 0 else (z0 - 0.04, z1)):
                m.box((x, y0, z), (e, y1, z + 0.04), cols[k % 2] if k % 2 else (cols[0][0] * 0.9, cols[0][1] * 0.9, cols[0][2] * 0.9), skip=("bottom", "top", "zhi" if z < z0 else "zlo"))

            x += rib
            k += 1
    else:
        z = z0 + 0.05
        k = 0

        while z < z1 - 0.1:
            e = min(z + rib * 0.5, z1)

            for x in ((x0 - 0.04,) if outside < 0 else (x1,) if outside > 0 else (x0 - 0.04, x1)):
                m.box((x, y0, z), (x + 0.04, y1, e), (cols[0][0] * 0.9, cols[0][1] * 0.9, cols[0][2] * 0.9), skip=("bottom", "top", "xhi" if x < x0 else "xlo"))

            z += rib
            k += 1


def wall_run(m, along_x, fixed0, fixed1, a0, a1, y0, y1, openings, cols, outside=0):
    cuts = sorted(openings)
    p = a0

    def seg(s, e, ya, yb, ribbed=True):
        if e - s < 0.01 or yb - ya < 0.01:
            return

        if along_x:
            lo, hi = (s, ya, fixed0), (e, yb, fixed1)
        else:
            lo, hi = (fixed0, ya, s), (fixed1, yb, e)

        if ya < y0 + 1.6 and ribbed:
            split = min(yb, y0 + 1.5)
            m.box(lo, (hi[0], split, hi[2]), CONCRETE_D)
            m.solid(lo, (hi[0], split, hi[2]))

            if yb > split:
                clad_box(m, (lo[0], split, lo[2]), hi, cols, along_x, outside=outside)
        else:
            clad_box(m, lo, hi, cols, along_x, outside=outside)

    for a, b, oy0, oy1, shut in cuts:
        seg(p, a, y0, y1)
        seg(a, b, oy1, y1, ribbed=False)

        if along_x:
            m.box((a - 0.12, y0, fixed0 - 0.08), (a, oy1 + 0.12, fixed1 + 0.08), HAZARD)
            m.box((b, y0, fixed0 - 0.08), (b + 0.12, oy1 + 0.12, fixed1 + 0.08), HAZARD)
            m.box((a - 0.12, oy1, fixed0 - 0.1), (b + 0.12, oy1 + 0.45, fixed1 + 0.1), STEEL)

            if shut > 0:
                for q in range(int(shut / 0.4)):
                    yy = oy1 - (q + 1) * 0.4
                    m.box((a, yy, (fixed0 + fixed1) / 2 - 0.03), (b, yy + 0.37, (fixed0 + fixed1) / 2 + 0.03), SHUTTER)

                m.solid((a, oy1 - shut, fixed0), (b, oy1, fixed1))
        else:
            m.box((fixed0 - 0.08, y0, a - 0.12), (fixed1 + 0.08, oy1 + 0.12, a), HAZARD)
            m.box((fixed0 - 0.08, y0, b), (fixed1 + 0.08, oy1 + 0.12, b + 0.12), HAZARD)

        p = b

    seg(p, a1, y0, y1)



FONT = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["111", "101", "101", "101", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "110"],
    "-": ["000", "000", "111", "000", "000"],
    " ": ["000", "000", "000", "000", "000"],
}


def text_width(s, px):
    return (len(s) * 4 - 1) * px


def face_box(m, o, right, normal, a0, a1, y0, y1, d0, d1, c):
    pts = []

    for a in (a0, a1):
        for d in (d0, d1):
            pts.append((o[0] + right[0] * a + normal[0] * d, o[1] + right[1] * a + normal[1] * d))

    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    m.box((min(xs), y0, min(zs)), (max(xs), y1, max(zs)), c)


def text(m, s, o, right, normal, y, px, c, depth=0.05):
    a = 0.0

    for ch in s:
        g = FONT.get(ch, FONT[" "])

        for r, row in enumerate(g):
            yy = y + (4 - r) * px
            col = 0

            while col < 3:
                if row[col] != "1":
                    col += 1
                    continue

                e = col

                while e < 3 and row[e] == "1":
                    e += 1

                face_box(m, o, right, normal, a + col * px, a + e * px, yy, yy + px, 0.0, depth, c)
                col = e

        a += 4 * px


def sign(m, s, centre, right, normal, y, px, bg, fg, pad=None):
    pad = pad if pad is not None else px * 1.2
    w = text_width(s, px)
    o = (centre[0] - right[0] * w / 2, centre[1] - right[1] * w / 2)
    face_box(m, o, right, normal, -pad, w + pad, y - pad, y + 5 * px + pad, 0.0, 0.06, bg)
    face_box(m, o, right, normal, -pad - 0.06, w + pad + 0.06, y - pad - 0.06, y + 5 * px + pad + 0.06, -0.01, 0.04, (bg[0] * 0.6, bg[1] * 0.6, bg[2] * 0.6))
    text(m, s, (o[0] + normal[0] * 0.06, o[1] + normal[1] * 0.06), right, normal, y, px, fg)


def steel_stair(m, x0, x1, z0, z1, y0, y1, c=(0.4, 0.43, 0.46)):
    n = max(2, int(round((y1 - y0) / 0.25)))
    run = (x1 - x0) / n
    rise = (y1 - y0) / n

    for i in range(n):
        xa = x0 + run * i
        xb = x0 + run * (i + 1)
        m.box((min(xa, xb), y0 + rise * (i + 1) - 0.06, z0 + 0.06), (max(xa, xb), y0 + rise * (i + 1), z1 - 0.06), c)

    for z in (z0, z1 - 0.08):
        m.beam((x0, y0 + 0.1, z + 0.04), (x1, y1 - 0.05, z + 0.04), 0.08, 0.3, (0.3, 0.32, 0.34))
        m.beam((x0, y0 + 1.0, z + 0.04), (x1, y1 + 1.0, z + 0.04), 0.05, 0.05, RAIL)

        for i in range(0, n + 1, 4):
            px = x0 + run * i
            m.box((px - 0.025, y0 + rise * i, z + 0.015), (px + 0.025, y0 + rise * i + 1.0, z + 0.065), RAIL)

    m.ramp((min(x0, x1), y0, z0), (max(x0, x1), y1, z1), "px" if x1 > x0 else "nx")


def roof_strip(m, x, top, ridge, zeave, w, th, c, u0=0.0, u1=1.0):
    m.beam((x, top + (ridge - top) * u0, zeave * (1 - u0)), (x, top + (ridge - top) * u1, zeave * (1 - u1)), w, th, c)


def exterior(m, W, D, top, ridge, fl, cols, st, docks, rear, rng):
    X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
    trim = st["trim"]
    dark = (cols[0][0] * 0.55, cols[0][1] * 0.55, cols[0][2] * 0.55)

    for z, zo in ((Z0, -1), (Z1, 1)):
        m.box((X0 - 0.12, top - 0.7, z - 0.1 if zo < 0 else z - 0.02), (X1 + 0.12, top + 0.05, z + 0.02 if zo < 0 else z + 0.1), trim)
        m.box((X0 - 0.2, top - 0.1, z - 0.32 if zo < 0 else z + 0.08), (X1 + 0.2, top + 0.1, z - 0.08 if zo < 0 else z + 0.32), (0.3, 0.31, 0.33))

    for x in (X0, X1):
        for z in (Z0, Z1):
            m.box((x - 0.14, fl, z - 0.14), (x + 0.14, top, z + 0.14), trim)

    for z, zo in ((Z0, -1), (Z1, 1)):
        x = X0 + 2.0

        while x < X1 - 1:
            zz = z + zo * 0.2
            m.box((x - 0.07, 0.0, zz - 0.07), (x + 0.07, top, zz + 0.07), st.get("pipe", (0.3, 0.31, 0.33)))
            m.box((x - 0.12, 0.0, zz - 0.12), (x + 0.12, 0.3, zz + 0.12), (0.3, 0.31, 0.33))
            x += 16.0

    for k in range(docks):
        cx = X0 + W * (k + 0.5) / docks
        y = fl + 4.62
        m.box((cx - 2.05, fl, Z0 - 0.45), (cx - 1.8, fl + 4.6, Z0 - 0.02), (0.14, 0.14, 0.15))
        m.box((cx + 1.8, fl, Z0 - 0.45), (cx + 2.05, fl + 4.6, Z0 - 0.02), (0.14, 0.14, 0.15))
        m.box((cx - 2.05, fl + 4.45, Z0 - 0.45), (cx + 2.05, fl + 4.75, Z0 - 0.02), (0.14, 0.14, 0.15))
        sign(m, "%02d" % (k + 1), (cx, Z0 - 0.48), (-1, 0), (0, -1), y + 0.35, 0.11, (0.95, 0.95, 0.92), (0.12, 0.13, 0.15), pad=0.1)
        m.box((cx + 0.9, y + 0.3, Z0 - 0.6), (cx + 1.4, y + 0.5, Z0 - 0.1), (0.25, 0.26, 0.28))
        m.box((cx + 0.95, y + 0.28, Z0 - 0.58), (cx + 1.35, y + 0.3, Z0 - 0.12), (1.0, 0.98, 0.86))

    if st.get("canopy"):
        cy = st["canopy"]
        m.beam((X0 - 0.2, cy + 0.25, Z0 - 0.1), (X1 + 0.2, cy + 0.25, Z0 - 0.1), 0.1, 0.1, trim)
        m.box((X0 - 0.2, cy - 0.12, Z0 - 3.9), (X1 + 0.2, cy + 0.05, Z0), (0.42, 0.44, 0.46))
        m.box((X0 - 0.2, cy - 0.45, Z0 - 4.0), (X1 + 0.2, cy + 0.1, Z0 - 3.85), trim)
        x = X0 + 8

        while x < X1 - 1:
            m.beam((x, cy - 0.12, Z0 - 3.6), (x, cy - 1.8, Z0 - 0.05), 0.12, 0.12, (0.3, 0.31, 0.33))
            x += 8

    sx = st.get("sign_x", 0.0)
    sy = st["sign_y"]
    sign(m, st["sign"], (sx, Z0 - 0.12), (-1, 0), (0, -1), sy, st["sign_px"], st["sign_bg"], st["sign_fg"])

    if st.get("rear_sign"):
        sign(m, st["rear_sign"], (0.0, Z1 + 0.12), (1, 0), (0, 1), sy, st["sign_px"], st["sign_bg"], st["sign_fg"])

    gx = X1 + 0.06
    letter = st.get("gable")

    if letter:
        sign(m, letter, (gx, 0.0), (0, -1), (1, 0), top - 2.6, 0.55, st["sign_bg"], st["sign_fg"], pad=0.5)
        sign(m, letter, (X0 - 0.06, 0.0), (0, 1), (-1, 0), top - 2.6, 0.55, st["sign_bg"], st["sign_fg"], pad=0.5)

    for x in (X0 - 0.06, X1 + 0.06):
        sgn = 1 if x > 0 else -1

        for k in range(5):
            y = fl + 3.0 + k * 0.22
            m.box((x - 0.06 if sgn > 0 else x - 0.08, y, D / 4 - 1.0), (x + 0.08 if sgn > 0 else x + 0.06, y + 0.12, D / 4 + 1.0), (0.3, 0.31, 0.33))

        m.box((x - 0.04, fl + 2.9, D / 4 - 1.1), (x + 0.04, fl + 4.1, D / 4 + 1.1), (0.5, 0.52, 0.54))
        m.box((x - 0.05 if sgn > 0 else x - 1.3, fl + 2.7, -1.3), (x + 1.3 if sgn > 0 else x + 0.05, fl + 2.85, 1.3), (0.36, 0.38, 0.4))

    n = int(W)

    for side in (-1, 1):
        zeave = (Z0 - 0.4) if side < 0 else (Z1 + 0.4)

        for i in range(n):
            x = X0 + 0.5 + i

            if i % 3 == 0:
                roof_strip(m, x, top, ridge, zeave, 0.07, 0.24, st.get("roof_rib", (0.4, 0.42, 0.44)))

        x = X0 + 6

        while x < X1 - 4:
            roof_strip(m, x, top, ridge, zeave, 1.4, 0.26, (0.72, 0.8, 0.84), 0.2, 0.8)
            x += 10

    x = X0 + 6

    while x < X1 - 4:
        m.box((x - 0.5, ridge + 0.1, -0.5), (x + 0.5, ridge + 0.6, 0.5), (0.55, 0.57, 0.6))
        m.box((x - 0.6, ridge + 0.6, -0.6), (x + 0.6, ridge + 0.7, 0.6), (0.4, 0.42, 0.44))
        x += 12

    if st.get("office"):
        ox0 = X0 + W / (2 * max(rear, 1)) + 3
        ox1 = ox0 + st["office"]

        m.box((ox0 - 0.4, fl + 0.6, Z1), (ox1 + 0.2, fl + 6.4, Z1 + 0.07), (0.84, 0.84, 0.8), skip=("zlo",))

        for y0 in (fl + 1.0, fl + 4.6):
            x = ox0

            while x + 1.6 <= ox1:
                m.box((x, y0 - 0.1, Z1 - 0.02), (x + 1.6, y0 + 1.4, Z1 + 0.08), (0.62, 0.64, 0.66))
                m.box((x + 0.1, y0, Z1 + 0.08), (x + 1.5, y0 + 1.2, Z1 + 0.1), (0.22, 0.32, 0.4))
                m.box((x + 0.78, y0, Z1 + 0.08), (x + 0.82, y0 + 1.2, Z1 + 0.12), (0.9, 0.9, 0.88))
                x += 2.0

        sx0 = ox1 + 1.0
        ly = fl + 4.0
        m.box((sx0 + 6.0, ly - 0.2, Z1), (sx0 + 8.0, ly, Z1 + 1.6), (0.4, 0.43, 0.46))
        m.solid((sx0 + 6.0, ly - 0.2, Z1), (sx0 + 8.0, ly, Z1 + 1.6))
        rail_run(m, sx0 + 8.0, Z1, sx0 + 8.0, Z1 + 1.6, ly)
        rail_run(m, sx0 + 6.0, Z1 + 1.6, sx0 + 8.0, Z1 + 1.6, ly, solid=False)

        for px in (sx0 + 6.1, sx0 + 7.9):
            m.box((px - 0.05, 0.0, Z1 + 1.45), (px + 0.05, ly - 0.2, Z1 + 1.55), (0.3, 0.32, 0.34))

        m.box((sx0 + 6.4, ly, Z1 - 0.02), (sx0 + 7.6, ly + 2.2, Z1 + 0.06), (0.86, 0.86, 0.84))
        m.box((sx0 + 6.5, ly, Z1 + 0.06), (sx0 + 7.5, ly + 2.1, Z1 + 0.09), (0.3, 0.42, 0.5))
        steel_stair(m, sx0, sx0 + 6.0, Z1 + 0.05, Z1 + 1.25, 0.0, ly)


def shed(name, W, D, H, cols, docks, rear, mezz=True, seed=1, st=None):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
    fl = 1.2
    t = 0.25
    top = fl + H

    m.box((X0 - 0.3, -1.0, Z0 - 0.3), (X1 + 0.3, fl, Z1 + 0.3), CONCRETE_D, bevel=0.04)
    m.solid((X0 - 0.3, -1.0, Z0 - 0.3), (X1 + 0.3, fl, Z1 + 0.3))

    m.box((X0 + 0.3, fl, Z0 + 0.3), (X1 - 0.3, fl + 0.01, Z1 - 0.3), FLOORC, skip=("bottom",))

    for z in (-2.2, 2.2):
        m.box((X0 + 1, fl + 0.01, z - 0.08), (X1 - 1, fl + 0.015, z + 0.08), HAZARD)

    m.box((X0 - 0.3, -1.0, Z0 - 4.0), (X1 + 0.3, fl, Z0 - 0.3), CONCRETE, bevel=0.03)
    m.solid((X0 - 0.3, -1.0, Z0 - 4.0), (X1 + 0.3, fl, Z0 - 0.3))
    m.box((X0 - 0.3, fl - 0.02, Z0 - 4.0), (X1 + 0.3, fl + 0.005, Z0 - 3.8), HAZARD)

    for sgn in (-1, 1):
        xe = X1 + 0.3 if sgn > 0 else X0 - 0.3
        xr = xe + sgn * 7.0
        n = 10

        for q in range(n):
            xa = xe + sgn * 7.0 * q / n
            xb = xe + sgn * 7.0 * (q + 1) / n
            yy = fl * (1 - (q + 1) / n)
            m.box((min(xa, xb), -0.6, Z0 - 4.0), (max(xa, xb), yy + fl / n, Z0 - 0.3), CONCRETE if q % 2 else SCREED)

        m.ramp((min(xe, xr), -0.6, Z0 - 4.0), (max(xe, xr), fl, Z0 - 0.3), "nx" if sgn > 0 else "px")

    ops = []

    for k in range(docks):
        cx = X0 + W * (k + 0.5) / docks
        shut = rng.choice([0.0, 0.0, 1.6, 2.4])
        ops.append((cx - 1.8, cx + 1.8, fl, fl + 4.4, shut))

    wall_run(m, True, Z0, Z0 + t, X0, X1, fl, top, ops, cols, outside=-1)
    rops = []

    for k in range(rear):
        cx = X0 + W * (k + 0.5) / rear
        rops.append((cx - 1.0, cx + 1.0, fl, fl + 2.6, 0.0))

    wall_run(m, True, Z1 - t, Z1, X0, X1, fl, top, rops, cols, outside=1)
    wall_run(m, False, X0, X0 + t, Z0 + t, Z1 - t, fl, top, [(-1.0, 1.0, fl, fl + 2.6, 0.0)], cols, outside=-1)
    wall_run(m, False, X1 - t, X1, Z0 + t, Z1 - t, fl, top, [], cols, outside=1)

    for k in range(rear):
        cx = X0 + W * (k + 0.5) / rear
        n = 8

        for q in range(n):
            za = Z1 + 6.0 * q / n
            zb = Z1 + 6.0 * (q + 1) / n
            m.box((cx - 1.2, -0.6, za), (cx + 1.2, fl * (1 - q / n), zb), CONCRETE)

        m.ramp((cx - 1.2, -0.6, Z1), (cx + 1.2, fl, Z1 + 6.0), "nz")

    n = 8

    for q in range(n):
        za = -1.0 + 2.0 * 0
        xa = X0 - 6.0 * (q + 1) / n
        xb = X0 - 6.0 * q / n
        m.box((xa, -0.6, -1.2), (xb, fl * (1 - q / n), 1.2), CONCRETE)

    m.ramp((X0 - 6.0, -0.6, -1.2), (X0, fl, 1.2), "px")

    ridge = top + 2.0
    m.beam((0, top, Z0 - 0.4), (0, ridge, 0), W + 0.8, 0.16, ROOF)
    m.beam((0, top, Z1 + 0.4), (0, ridge, 0), W + 0.8, 0.16, ROOF)
    m.box((X0 - 0.4, ridge - 0.1, -0.3), (X1 + 0.4, ridge + 0.12, 0.3), (0.42, 0.44, 0.46))

    for sx in (X0, X1):
        tmp = [(sx, top, Z0), (sx, ridge, 0.0), (sx, top, Z1)]
        vs = [m.bm.verts.new(gpos(*p)) for p in tmp]
        f = m.bm.faces.new(vs if sx > 0 else list(reversed(vs)))

        for l in f.loops:
            l[m.col] = (cols[0][0], cols[0][1], cols[0][2], 1.0)

        vs2 = [m.bm.verts.new(gpos(p[0] - (0.05 if sx > 0 else -0.05), p[1], p[2])) for p in tmp]
        f2 = m.bm.faces.new(list(reversed(vs2)) if sx > 0 else vs2)

        for l in f2.loops:
            l[m.col] = (cols[0][0] * 0.8, cols[0][1] * 0.8, cols[0][2] * 0.8, 1.0)

    for k in range(1, int(W / 8)):
        x = X0 + k * 8

        for z in (Z0 + 0.4, Z1 - 0.4):
            m.ibeam((x, fl, z), (x, top, z), 0.35, STEEL, vertical=True)
            m.solid((x - 0.18, fl, z - 0.18), (x + 0.18, top, z + 0.18))

        m.beam((x, top - 0.3, Z0 + 0.4), (x, ridge - 0.4, 0), 0.25, 0.4, STEEL)
        m.beam((x, top - 0.3, Z1 - 0.4), (x, ridge - 0.4, 0), 0.25, 0.4, STEEL)
        m.beam((x, top - 0.4, Z0 + 0.4), (x, top - 0.4, Z1 - 0.4), 0.06, 0.06, STEEL)

        for z in (-D / 4, D / 4):
            m.box((x - 0.02, top - 2.2, z - 0.02), (x + 0.02, top - 0.4, z + 0.02), BLACK)
            cyl(m, (x, top - 2.6, z), 0.35, 0.4, "y", 10, (0.3, 0.32, 0.34))
            m.box((x - 0.25, top - 2.62, z - 0.25), (x + 0.25, top - 2.58, z + 0.25), (0.98, 0.98, 0.92))

    for k in range(int(W / 6)):
        x = X0 + 3 + k * 6

        for z in (Z0 + 0.1, Z1 - 0.1):
            m.box((x - 1.2, top - 1.6, z - 0.06), (x + 1.2, top - 0.8, z + 0.06), (0.62, 0.72, 0.78))

    if mezz:
        mx0 = X1 - 12.0
        my = fl + 4.0
        m.box((mx0, my - 0.2, Z0 + t), (X1 - t, my, Z1 - t), (0.46, 0.5, 0.52))
        m.solid((mx0, my - 0.2, Z0 + t), (X1 - t, my, Z1 - t))

        for k in range(int((D - 1) / 4) + 1):
            z = Z0 + 1.0 + k * 4.0

            if z > Z1 - 0.8:
                break

            m.ibeam((mx0, fl, z), (mx0, my - 0.2, z), 0.25, UPRIGHT, vertical=True)
            m.solid((mx0 - 0.13, fl, z - 0.13), (mx0 + 0.13, my, z + 0.13))

        rail_run(m, mx0, Z0 + 3.4, mx0, Z1 - t, my)
        n = 16
        sz0, sz1 = Z0 + 0.4, Z0 + 2.2
        xb = mx0 - 6.8

        for q in range(n):
            xa = xb + 6.8 * q / n
            m.box((xa, fl + (my - fl) * q / n, sz0), (xa + 6.8 / n, fl + (my - fl) * (q + 1) / n, sz1), (0.42, 0.45, 0.48))

        m.ramp((xb, fl, sz0), (mx0, my, sz1), "px")
        m.beam((xb, fl + 1.0, sz1 + 0.05), (mx0, my + 1.0, sz1 + 0.05), 0.05, 0.05, HAZARD)
        m.solid((xb, fl, sz1 + 0.02), (mx0, my + 1.0, sz1 + 0.12))

        for k in range(3):
            x = mx0 + 2 + k * 3.4
            m.box((x, fl, Z1 - 3.0), (x + 2.8, fl + 2.6, Z1 - t), (0.82, 0.82, 0.8))
            m.box((x + 0.4, fl + 1.0, Z1 - 3.02), (x + 2.4, fl + 2.0, Z1 - 3.0), (0.2, 0.3, 0.36))
            m.solid((x, fl, Z1 - 3.0), (x + 2.8, fl + 2.6, Z1 - t))

    if st:
        exterior(m, W, D, top, ridge, fl, cols, st, docks, rear, rng)

    return finish(m, name, size=0, reach=2.0, strength=0.6)


def rack(name, full=True, seed=1):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    bays = 3
    L = 2.7
    Dp = 1.1
    Hh = 4.8
    x0 = -bays * L / 2

    for k in range(bays + 1):
        x = x0 + k * L

        for z in (-Dp / 2, Dp / 2):
            m.box((x - 0.05, 0, z - 0.04), (x + 0.05, Hh, z + 0.04), UPRIGHT)

        for y in range(1, 9):
            m.beam((x, y * 0.55 - 0.3, -Dp / 2), (x, y * 0.55, Dp / 2), 0.03, 0.03, UPRIGHT)

        m.box((x - 0.15, 0, -Dp / 2 - 0.15), (x + 0.15, 0.6, -Dp / 2 - 0.05), HAZARD)

    for lv, y in enumerate((0.15, 1.75, 3.35)):
        for z in (-Dp / 2, Dp / 2):
            m.box((x0, y, z - 0.06), (x0 + bays * L, y + 0.12, z + 0.06), BEAM)

        for k in range(bays):
            for s in range(2):
                if not full and rng.random() < 0.45:
                    continue

                cx = x0 + k * L + 0.7 + s * 1.3
                base = y + 0.12
                m.box((cx - 0.6, base, -0.5), (cx + 0.6, base + 0.14, 0.5), BOARD[rng.randint(0, 2)])
                h = rng.uniform(0.9, 1.35)
                c = rng.choice([(0.72, 0.6, 0.42), (0.66, 0.54, 0.36), (0.8, 0.8, 0.82), (0.3, 0.46, 0.62), (0.76, 0.7, 0.56)])
                m.box((cx - 0.55, base + 0.14, -0.45), (cx + 0.55, base + 0.14 + h, 0.45), c, bevel=0.03)

    m.solid((x0 - 0.1, 0, -Dp / 2 - 0.1), (x0 + bays * L + 0.1, Hh, Dp / 2 + 0.1))

    return finish(m, name, size=0, reach=1.6, strength=0.8)


def cartons(name, seed):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    m.box((-0.6, 0.0, -0.5), (0.6, 0.04, 0.5), BOARD[0])

    for x in (-0.55, -0.05, 0.45):
        m.box((x, 0.04, -0.5), (x + 0.1, 0.11, 0.5), BOARD[1], skip=("bottom",))

    m.box((-0.6, 0.11, -0.5), (0.6, 0.15, 0.5), BOARD[2], skip=("bottom",))
    browns = [(0.66, 0.5, 0.32), (0.72, 0.56, 0.36), (0.6, 0.45, 0.28), (0.76, 0.62, 0.42)]
    y = 0.15
    top = 0.0

    for layer in range(rng.randint(2, 3)):
        h = rng.uniform(0.32, 0.42)
        cols = 2 if rng.random() < 0.6 else 3
        w = 1.16 / cols
        rows = 2

        for i in range(cols):
            for j in range(rows):
                if layer > 0 and rng.random() < 0.15:
                    continue

                x0 = -0.58 + i * w + 0.01
                z0 = -0.48 + j * 0.48 + 0.01
                c = rng.choice(browns)
                hh = h * rng.uniform(0.92, 1.0)
                m.box((x0, y, z0), (x0 + w - 0.02, y + hh, z0 + 0.46), c, skip=("bottom",))
                m.box((x0 + w / 2 - 0.04, y + hh, z0), (x0 + w / 2 + 0.04, y + hh + 0.005, z0 + 0.46), (0.82, 0.7, 0.5), skip=("bottom",))

                if rng.random() < 0.4:
                    m.box((x0 + 0.08, y + hh * 0.4, z0 - 0.005), (x0 + 0.26, y + hh * 0.7, z0), (0.92, 0.92, 0.9), skip=("zhi",))

        y += h
        top = y

    m.solid((-0.6, 0.0, -0.5), (0.6, top, 0.5))

    return finish(m, name, size=0, reach=0.6, strength=0.5)


def mast(name):
    reset()
    m = Mesh()
    cyl(m, (0, 0, 0), 0.6, 0.6, "y", 12, CONCRETE_D)
    cyl(m, (0, 0.6, 0), 0.18, 13.0, "y", 10, (0.56, 0.58, 0.6))
    m.box((-1.4, 13.4, -0.15), (1.4, 13.6, 0.15), STEEL)

    for x in (-1.1, -0.37, 0.37, 1.1):
        m.box((x - 0.3, 13.1, -0.35), (x + 0.3, 13.5, 0.05), (0.3, 0.32, 0.34))
        m.box((x - 0.25, 13.08, -0.32), (x + 0.25, 13.1, 0.0), (0.98, 0.98, 0.9))

    m.solid((-0.6, 0, -0.6), (0.6, 13.6, 0.6))

    return finish(m, name, size=0, reach=1.0, strength=0.6)


PROPS = [
    ("load", "stretch-wrapped-pallet-load-b4169b", {}),
    ("pallet", "timber-eur-pallet-a1f655", {}),
    ("tote", "ibc-tote-88385a", {}),
    ("barrier", "pedestrian-safety-barrier-run-2afeca", {}),
    ("bumper", "dock-bumper-94978d", {"collide": "none"}),
    ("sign", "hanging-aisle-sign-0b372d", {"collide": "none"}),
    ("bench", "packing-bench-302f02", {}),
]

DX = os.path.expanduser("~/.cache/polyfork/depotx/")
CX = os.path.expanduser("~/.cache/polyfork/construction/")
AX = os.path.expanduser("~/.cache/polyfork/airport/")

BUILDS = [
    ("cargo", AX + "cargo-shed-bcb2a8.glb", 1.25),
    ("brick", DX + "brick-depot-warehouse-3dd642.glb", 1.6),
]

EXTRA = [
    ("cabin", CX + "site-cabin-e9ee10.glb", {"scale": 1.0, "group": "building"}),
    ("fueltank", DX + "depot-fuel-tank-55a00e.glb", {"scale": 1.2, "group": "building"}),
    ("crate", DX + "cargo-crate-9afc44.glb", {"scale": 1.4}),
    ("skip", CX + "builder-s-skip-191d35.glb", {"scale": 1.1}),
    ("orange", CX + "crash-barrier-run-b47d1d.glb", {"scale": 1.0}),
    ("precast", CX + "precast-concrete-stack-8945ac.glb", {"scale": 1.0}),
    ("dumpy", CX + "builder-s-dumpy-bag-89fd1b.glb", {"scale": 1.1}),
    ("pdrum", DX + "plastic-drum-da992f.glb", {"scale": 1.1, "collide": "cylinder"}),
    ("tubes", CX + "scaffold-material-stack-836dd2.glb", {"scale": 1.0}),
    ("gantry", CX + "loading-gantry-34460f.glb", {"scale": 1.2, "group": "building"}),
    ("cone", CX + "site-traffic-cone-d3ce94.glb", {"scale": 1.0, "collide": "none"}),
    ("carton", DX + "cardboard-delivery-box-59cc68.glb", {"scale": 0.7, "collide": "none"}),
]

XPROPS = [
    ("tree", "broad-canopy-shade-tree-e7c4a2", {"collide": "trunk", "group": "tree"}),
    ("shrub", "columnar-evergreen-shrub-35a00b", {"collide": "cylinder", "group": "bush", "scale": 1.3}),
    ("hedge", "clipped-hedge-section-11a067", {"group": "bush"}),
    ("light", "cobra-head-street-light-3e25b8", {"collide": "cylinder"}),
    ("booth", "campus-coffee-kiosk-ec2395", {}),
    ("fence", "mesh-fence-panel-11d4e2", {}),
    ("genset", "standby-generator-enclosure-9d48f6", {"k": "decross"}),
    ("tank", "fuel-tank-3a0111", {"scale": 1.6}),
    ("htank", "horizontal-tank-6e9b8b", {"scale": 1.8}),
    ("hvac", "hvac-condenser-unit-a41b8d", {"scale": 1.3}),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "warehouse")
    os.makedirs(pf.OUT, exist_ok=True)

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(pf.OUT, f))

    infos = {}
    builds = [
        lambda: shed("shed_a", 64, 32, 9.0, CLAD, 8, 2, seed=3, st=dict(trim=(0.9, 0.9, 0.87), sign="DEPOT 1", sign_y=7.9, sign_px=0.24, sign_x=-14.0, sign_bg=(0.92, 0.92, 0.9), sign_fg=(0.14, 0.26, 0.46), rear_sign="DEPOT 1", gable="1", canopy=7.25, office=10, pipe=(0.86, 0.86, 0.84))),
        lambda: shed("shed_b", 48, 28, 8.0, CLAD_B, 6, 1, seed=5, st=dict(trim=(0.2, 0.22, 0.24), sign="COLD STORE", sign_y=7.35, sign_px=0.18, sign_x=8.0, sign_bg=(0.94, 0.94, 0.92), sign_fg=(0.16, 0.36, 0.26), rear_sign="COLD STORE", gable="2", canopy=7.0, office=8, roof_rib=(0.3, 0.32, 0.34))),
        lambda: shed("shed_c", 72, 24, 7.5, CLAD_C, 9, 2, mezz=False, seed=9, st=dict(trim=(0.88, 0.86, 0.8), sign="DEPOT 3", sign_y=6.7, sign_px=0.2, sign_x=-20.0, sign_bg=(0.9, 0.88, 0.82), sign_fg=(0.5, 0.16, 0.12), rear_sign="DISPATCH", gable="3", office=10, pipe=(0.88, 0.86, 0.8))),
        lambda: rack("rack", True, 2),
        lambda: rack("rack_half", False, 4),
        lambda: container("box_red", (0.66, 0.22, 0.14)),
        lambda: container("box_blue", (0.16, 0.34, 0.56)),
        lambda: container("box_green", (0.22, 0.42, 0.3)),
        lambda: container("box_office", (0.86, 0.84, 0.78), office=True),
        drums,
        jersey,
        lambda: mast("mast"),
        lambda: cartons("cartons", 4),
        lambda: cartons("cartons_b", 11),
    ]

    for fn in builds:
        info = fn()
        infos[info["file"].split("/")[-1][:-4]] = info

    for name, kind in (("puddle", "puddle"), ("tracks", "tracks"), ("lane", "lane"), ("bay", "bay")):
        infos[name] = decal(name, kind)

    for name, src, opts in PROPS:
        infos[name] = kitprop(name, src, **opts)

    for name, src, opts in XPROPS:
        infos[name] = kitprop(name, os.path.join(LX, src + ".glb"), **opts)

    for name, src, opts in EXTRA:
        infos[name] = kitprop(name, src, **opts)

    for name, src, sc in BUILDS:
        reset()
        infos[name] = pf.make_building(name, src, scale=sc, plinth=CONCRETE_D)

    path = os.path.join(root, "src/shared/maps", "warehouse_kit.zig")
    emit_zig("warehouse", infos, path)
    write_solids(path)


main()
