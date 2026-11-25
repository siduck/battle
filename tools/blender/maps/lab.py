import os, sys, math, random, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "lab")
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|attach-|researcher|technician|student|scientist|founder", re.I)
CITY = ""
LX = os.path.expanduser("~/.cache/polyfork/labx")

CONCRETE = (0.66, 0.66, 0.63)
CONCRETE_D = (0.46, 0.47, 0.47)
SCREED = (0.6, 0.6, 0.58)
BLOCK = [(0.62, 0.6, 0.55)]
MORTAR = (0.48, 0.46, 0.42)
TUBE = (0.6, 0.63, 0.66)
BOARD = [(0.6, 0.42, 0.24), (0.54, 0.37, 0.21), (0.66, 0.47, 0.28)]
TOE = (0.16, 0.5, 0.52)
RAIL = (0.55, 0.58, 0.6)
BLACK = (0.14, 0.15, 0.16)
REBAR = (0.5, 0.26, 0.12)
STEEL = (0.36, 0.39, 0.42)
DIRT = (0.36, 0.34, 0.3)
PANEL = (0.84, 0.84, 0.8)
PANEL_B = (0.76, 0.77, 0.74)
TEAL = (0.12, 0.46, 0.48)
TEAL_L = (0.3, 0.62, 0.62)
FRAME = (0.22, 0.24, 0.26)
FLOOR = (0.7, 0.71, 0.68)
FLOOR_B = (0.62, 0.66, 0.64)
CEIL = (0.82, 0.82, 0.8)
PLINTH = (0.4, 0.41, 0.42)
ACCENT = (0.86, 0.5, 0.16)

F = [0.3, 4.3, 8.3]
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


ROOMS = {}


def wall_x(m, z0, z1, x0, x1, y0, y1, openings, c, frame=True):
    cuts = sorted(openings)
    x = x0

    for a, b, oy0, oy1 in cuts:
        if a > x:
            m.box((x, y0, z0), (a, y1, z1), c)
            m.solid((x, y0, z0), (a, y1, z1))

        if oy0 > y0:
            m.box((a, y0, z0), (b, oy0, z1), c)
            m.solid((a, y0, z0), (b, oy0, z1))
            m.box((a - 0.04, oy0 - 0.06, z0 - 0.06), (b + 0.04, oy0, z1 + 0.06), FRAME)

        if oy1 < y1:
            m.box((a, oy1, z0), (b, y1, z1), c)
            m.solid((a, oy1, z0), (b, y1, z1))

        if frame:
            m.box((a, oy0, z0 - 0.02), (a + 0.08, oy1, z1 + 0.02), FRAME)
            m.box((b - 0.08, oy0, z0 - 0.02), (b, oy1, z1 + 0.02), FRAME)
            m.box((a, oy1 - 0.08, z0 - 0.02), (b, oy1, z1 + 0.02), FRAME)

        x = b

    if x < x1:
        m.box((x, y0, z0), (x1, y1, z1), c)
        m.solid((x, y0, z0), (x1, y1, z1))


def wall_z(m, x0, x1, z0, z1, y0, y1, openings, c, frame=True):
    cuts = sorted(openings)
    z = z0

    for a, b, oy0, oy1 in cuts:
        if a > z:
            m.box((x0, y0, z), (x1, y1, a), c)
            m.solid((x0, y0, z), (x1, y1, a))

        if oy0 > y0:
            m.box((x0, y0, a), (x1, oy0, b), c)
            m.solid((x0, y0, a), (x1, oy0, b))
            m.box((x0 - 0.06, oy0 - 0.06, a - 0.04), (x1 + 0.06, oy0, b + 0.04), FRAME)

        if oy1 < y1:
            m.box((x0, oy1, a), (x1, y1, b), c)
            m.solid((x0, oy1, a), (x1, y1, b))

        if frame:
            m.box((x0 - 0.02, oy0, a), (x1 + 0.02, oy1, a + 0.08), FRAME)
            m.box((x0 - 0.02, oy0, b - 0.08), (x1 + 0.02, oy1, b), FRAME)
            m.box((x0 - 0.02, oy1 - 0.08, a), (x1 + 0.02, oy1, b), FRAME)

        z = b

    if z < z1:
        m.box((x0, y0, z), (x1, y1, z1), c)
        m.solid((x0, y0, z), (x1, y1, z1))


def floor_slab(m, y, x0, x1, z0, z1, holes, top=FLOOR, under=CEIL):
    cuts_x = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    cuts_z = sorted({z0, z1} | {h[2] for h in holes} | {h[3] for h in holes})

    for i in range(len(cuts_x) - 1):
        for j in range(len(cuts_z) - 1):
            ax, bx = cuts_x[i], cuts_x[i + 1]
            az, bz = cuts_z[j], cuts_z[j + 1]
            cx = (ax + bx) / 2
            cz = (az + bz) / 2

            if any(h[0] <= cx <= h[1] and h[2] <= cz <= h[3] for h in holes):
                continue

            m.box((ax, y - 0.3, az), (bx, y - 0.04, bz), under)
            m.box((ax, y - 0.04, az), (bx, y, bz), top)
            m.solid((ax, y - 0.3, az), (bx, y, bz))


def flight(m, x_bottom, x_top, z0, z1, y0, y1):
    n = int(round((y1 - y0) / 0.25))
    step = (x_top - x_bottom) / n

    for i in range(n):
        xa = x_bottom + step * i
        xb = x_bottom + step * (i + 1)
        m.box((min(xa, xb), y0, z0), (max(xa, xb), y0 + (y1 - y0) * (i + 1) / n, z1), SCREED if i % 2 else CONCRETE)
        m.box((min(xa, xb), y0 + (y1 - y0) * (i + 1) / n - 0.02, z0), (min(xa, xb) + 0.05, y0 + (y1 - y0) * (i + 1) / n, z1), TEAL)

    m.ramp((min(x_bottom, x_top), y0, z0), (max(x_bottom, x_top), y1, z1), "px" if x_top > x_bottom else "nx")
    m.beam((x_bottom, y0 + 1.0, z0 - 0.05), (x_top, y1 + 1.0, z0 - 0.05), 0.05, 0.05, RAIL)

    for i in range(0, n + 1, 4):
        x = x_bottom + step * i
        m.box((x - 0.025, y0, z0 - 0.08), (x + 0.025, y0 + (y1 - y0) * i / n + 1.0, z0 - 0.03), RAIL)

    m.solid((min(x_bottom, x_top), y0, z0 - 0.12), (max(x_bottom, x_top), y1 + 1.0, z0 - 0.02))


def rail(m, x0, z0, x1, z1, y):
    rail_run(m, x0, z0, x1, z1, y)


def lab_building(name, W, D, nf, seed, roof=True, entry_z=True):
    reset()
    m = Mesh()
    rng = random.Random(seed)
    X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
    t = 0.3
    cw = 1.6
    rooms = []
    hole_up = (X1 - 8.3, X1 - 0.3, Z1 - 2.5, Z1 - 0.3)
    hole_roof = (X0 + 0.3, X0 + 8.3, Z1 - 2.5, Z1 - 0.3)
    levels = [0.3 + 4.0 * i for i in range(nf + 1)]

    m.box((X0 - 0.4, -1.0, Z0 - 0.4), (X1 + 0.4, 0.3, Z1 + 0.4), PLINTH, bevel=0.04)
    m.box((X0 + t, 0.26, Z0 + t), (X1 - t, 0.3, Z1 - t), FLOOR)
    m.solid((X0 - 0.4, -1.0, Z0 - 0.4), (X1 + 0.4, 0.3, Z1 + 0.4))

    for i in range(1, nf):
        floor_slab(m, levels[i], X0 + t, X1 - t, Z0 + t, Z1 - t, [hole_up] if i == 1 else [hole_up])

    roof_holes = [hole_roof] if roof else []
    floor_slab(m, levels[nf], X0, X1, Z0, Z1, roof_holes, top=(0.56, 0.57, 0.56), under=CEIL)

    for i in range(nf):
        y0 = levels[i]
        y1 = levels[i + 1] - 0.3
        bays = int(W / 4)

        for side, (za, zb) in enumerate(((Z0, Z0 + t), (Z1 - t, Z1))):
            ops = []

            for k in range(bays):
                bx0 = X0 + k * 4
                mid = bays // 2

                if i == 0 and k == mid and (entry_z or side == 0):
                    ops.append((bx0 + 0.8, bx0 + 3.2, y0, y0 + 2.8))
                elif k in (0, bays - 1):
                    continue
                elif side == 1 and k * 4 + X0 >= X1 - 8.3 and i < nf:
                    ops.append((bx0 + 0.6, bx0 + 3.4, y0 + 1.6, y0 + 2.9))
                else:
                    ops.append((bx0 + 0.5, bx0 + 3.5, y0 + 1.0, y0 + 2.9))

            wall_x(m, za, zb, X0, X1, y0, y1, ops, PANEL if (i + side) % 2 == 0 else PANEL_B)

            for a, b, oy0, oy1 in ops:
                if oy0 > y0 + 0.5:
                    mx = (a + b) / 2
                    m.box((mx - 0.04, oy0, za - 0.03), (mx + 0.04, oy1, zb + 0.03), FRAME)

        for (xa, xb) in ((X0, X0 + t), (X1 - t, X1)):
            ops = []

            if i == 0:
                ops.append((-cw, cw, y0, y0 + 2.8))
            else:
                ops.append((-cw, cw, y0 + 1.0, y0 + 2.9))

            for zc in (Z0 + 4.2, Z1 - 4.2):
                if abs(zc) > cw + 2.2:
                    ops.append((zc - 1.4, zc + 1.4, y0 + 1.0, y0 + 2.9))

            wall_z(m, xa, xb, Z0 + t, Z1 - t, y0, y1, ops, PANEL_B if i % 2 == 0 else PANEL)

        west = X0 + t + 9.6
        east = X1 - t - 9.6
        span = east - west
        parts = max(1, int(round(span / 8.0))) if span > 4 else 0
        room_xs = [X0 + t, west] + [west + span * q / parts for q in range(1, parts)] + ([east] if span > 4 else []) + [X1 - t]

        for zc, (za, zb) in ((cw, (cw, cw + 0.2)), (-cw, (-cw - 0.2, -cw))):
            ops = []

            for r in range(len(room_xs) - 1):
                a = room_xs[r]
                b = room_xs[r + 1]
                c = (a + b) / 2
                ops.append((c - 0.8, c + 0.8, y0, y0 + 2.4))

                if rng.random() < 0.5 and b - a > 6:
                    ops.append((a + 0.8, a + 2.6, y0 + 1.0, y0 + 2.2))

            ops = sorted(ops)
            wall_x(m, za, zb, X0 + t, X1 - t, y0, y1, ops, (0.78, 0.8, 0.78))
            edge_z = za - 0.015 if zc > 0 else zb + 0.015
            sx = X0 + t

            for a, b2, oy0, oy1 in ops + [(X1 - t, X1 - t, y0, y1)]:
                if a > sx + 0.05:
                    m.box((sx, y0, min(edge_z, (za + zb) / 2)), (a, y0 + 0.12, max(edge_z, (za + zb) / 2)), FRAME)
                    m.box((sx, y0 + 1.05, min(edge_z, (za + zb) / 2)), (a, y0 + 1.2, max(edge_z, (za + zb) / 2)), ACCENT if i % 2 else TEAL_L)

                sx = b2

        for r in range(1, len(room_xs) - 1):
            xr = room_xs[r]
            wall_z(m, xr - 0.1, xr + 0.1, cw + 0.2, Z1 - t, y0, y1, [], (0.8, 0.8, 0.77), frame=False)
            wall_z(m, xr - 0.1, xr + 0.1, Z0 + t, -cw - 0.2, y0, y1, [], (0.8, 0.8, 0.77), frame=False)

        for r in range(len(room_xs) - 1):
            a = room_xs[r] + 0.1
            b = room_xs[r + 1] - 0.1
            north = (a, cw + 0.2, b, Z1 - t)
            south = (a, Z0 + t, b, -cw - 0.2)
            stair_n = (i < nf - 1 and b > X1 - 1) or (i == nf - 1 and roof and a < X0 + 1) or (i > 0 and b > X1 - 1)
            rooms.append((north[0], north[1], north[2], north[3], y0, 1 if stair_n else 0))
            rooms.append((south[0], south[1], south[2], south[3], y0, 0))

        m.box((X0 - 0.05, y1, Z0 - 0.05), (X1 + 0.05, y1 + 0.3, Z0 + 0.05), TEAL)
        m.box((X0 - 0.05, y1, Z1 - 0.05), (X1 + 0.05, y1 + 0.3, Z1 + 0.05), TEAL)
        m.box((X0 - 0.05, y1, Z0 - 0.05), (X0 + 0.05, y1 + 0.3, Z1 + 0.05), TEAL)
        m.box((X1 - 0.05, y1, Z0 - 0.05), (X1 + 0.05, y1 + 0.3, Z1 + 0.05), TEAL)

        if i < nf - 1:
            flight(m, X1 - 1.0, X1 - 8.0, Z1 - 2.3, Z1 - 0.5, y0, levels[i + 1])
        elif roof:
            flight(m, X0 + 1.0, X0 + 8.0, Z1 - 2.3, Z1 - 0.5, y0, levels[i + 1])

        m.box((X0 + t, y0, -cw), (X1 - t, y0 + 0.02, cw), FLOOR_B)
        m.box((X0 + t, y0 + 0.02, -0.12), (X1 - t, y0 + 0.025, 0.12), TEAL)

        for xx in range(int(X0 + 3), int(X1 - 2), 4):
            m.box((xx - 0.6, y1 - 0.06, -0.35), (xx + 0.6, y1 - 0.01, 0.35), (0.98, 0.98, 0.95))

        for r in range(len(room_xs) - 1):
            cxr = (room_xs[r] + room_xs[r + 1]) / 2

            for zz in ((cw + Z1 - t) / 2, (Z0 + t - cw) / 2):
                m.box((cxr - 1.2, y1 - 0.06, zz - 0.3), (cxr + 1.2, y1 - 0.01, zz + 0.3), (0.98, 0.98, 0.95))

    for i in range(1, nf):
        y = levels[i]
        rail(m, hole_up[0], hole_up[2], hole_up[1] - 0.2, hole_up[2], y)

    top = levels[nf]

    if roof:
        rail(m, hole_roof[0] + 1.5, hole_roof[2], hole_roof[1], hole_roof[2], top)
        rail(m, hole_roof[1], hole_roof[2], hole_roof[1], hole_roof[3], top)

    for (a, b) in (((X0, Z0), (X1, Z0 + 0.25)), ((X0, Z1 - 0.25), (X1, Z1)), ((X0, Z0), (X0 + 0.25, Z1)), ((X1 - 0.25, Z0), (X1, Z1))):
        m.box((a[0], top, a[1]), (b[0], top + 1.0, b[1]), PANEL_B)
        m.box((a[0] - 0.03, top + 1.0, a[1] - 0.03), (b[0] + 0.03, top + 1.08, b[1] + 0.03), (0.6, 0.62, 0.62))
        m.solid((a[0], top, a[1]), (b[0], top + 1.0, b[1]))

    units = []

    for k in range(int(W / 10)):
        ux = X0 + 6 + k * 10
        uz = rng.uniform(Z0 + 2.5, Z0 + 4.0)
        units.append((ux, uz))
        m.box((ux - 1.2, top, uz - 0.9), (ux + 1.2, top + 1.6, uz + 0.9), (0.72, 0.73, 0.72), bevel=0.04)

        for g in range(5):
            m.box((ux - 1.0 + g * 0.42, top + 0.3, uz - 0.92), (ux - 0.78 + g * 0.42, top + 1.4, uz - 0.9), (0.3, 0.32, 0.34))

        cyl(m, (ux, top + 1.6, uz), 0.5, 0.12, "y", 12, (0.3, 0.32, 0.34))
        m.solid((ux - 1.2, top, uz - 0.9), (ux + 1.2, top + 1.6, uz + 0.9))
        m.box((ux - 0.15, top + 0.1, uz + 0.9), (ux + 0.15, top + 0.4, Z1 - 3), (0.5, 0.52, 0.54))

    sx = X0 + W * 0.55
    m.box((sx, top, -1.2), (sx + 3.0, top + 0.5, 1.2), (0.6, 0.62, 0.62))
    m.box((sx + 0.15, top + 0.5, -1.05), (sx + 2.85, top + 0.62, 1.05), (0.2, 0.36, 0.42))
    m.solid((sx, top, -1.2), (sx + 3.0, top + 0.62, 1.2))

    ROOMS[name] = rooms
    info = finish(m, name, size=2.0, reach=3.4, strength=0.85)

    return info


def kitx(name, src, height=None, **opts):
    path = os.path.join(LX, src + ".glb")

    if height:
        reset()
        bm = load(path)
        lo, hi = bounds(bm)
        opts["scale"] = height / (hi.z - lo.z)
        bm.free()

    return kitprop(name, path, **opts)


PROPS = [
    ("island", "island-bench-spine-d046b2", {}),
    ("wallbench", "wall-bench-spine-8c30d2", {}),
    ("hood", "walk-in-fume-hood-bbc294", {}),
    ("bsc", "biosafety-cabinet-a46204", {}),
    ("freezer", "ultra-low-freezer-9a84fb", {}),
    ("fridge", "glass-door-sample-fridge-386715", {}),
    ("gascab", "gas-cylinder-cabinet-cea23b", {}),
    ("shelf", "chemical-shelving-rack-3a188c", {}),
    ("lockers", "ppe-locker-bank-60dd99", {}),
    ("desk", "write-up-desk-38763a", {}),
    ("stool", "lab-stool-022713", {"collide": "none"}),
    ("optics", "optics-table-66db15", {}),
    ("glovebox", "glovebox-737c45", {}),
    ("laminar", "laminar-flow-hood-d730bd", {}),
    ("cart", "mobile-bench-cart-4b3ff5", {}),
    ("dewar", "nitrogen-dewar-wheeled-c9986e", {"collide": "cylinder"}),
    ("sink", "sink-unit-with-drying-c5d11a", {}),
    ("shower", "safety-shower-and-eyewash-1f5f20", {"collide": "none"}),
    ("airlock", "air-shower-airlock-cabin-ed83ae", {}),
    ("incubator", "co2-incubator-198c16", {}),
    ("autoclave", "autoclave-d34434", {}),
    ("firepoint", "fire-point-station-dfd230", {"collide": "none"}),
    ("vented", "vented-chemical-storage-cabinet-91b061", {}),
]

XPROPS = [
    ("ward", "multi-storey-ward-block-2bac82", {"scale": 1.3, "group": "building"}),
    ("annexe", "clinic-annexe-0f56d1", {"scale": 1.2, "group": "building"}),
    ("genset", "standby-generator-enclosure-9d48f6", {}),
    ("canopy", "entrance-canopy-8378c5", {"collide": "none", "group": "building"}),
    ("bollard", "illuminated-bollard-9af752", {"collide": "cylinder"}),
    ("totem", "wayfinding-totem-sign-dbb4be", {}),
    ("hedge", "clipped-hedge-section-11a067", {"group": "bush"}),
    ("fence", "mesh-fence-panel-11d4e2", {}),
    ("tree", "broad-canopy-shade-tree-e7c4a2", {"collide": "trunk", "group": "tree"}),
    ("tree2", "ornamental-front-yard-tree-c6781a", {"collide": "trunk", "group": "tree", "scale": 1.3}),
    ("shrub", "columnar-evergreen-shrub-35a00b", {"collide": "cylinder", "group": "bush", "scale": 1.3}),
    ("bush", "trimmed-foundation-shrub-616ce0", {"collide": "none", "group": "bush", "scale": 1.2}),
    ("hvac", "hvac-condenser-unit-a41b8d", {"scale": 1.3}),
    ("bench", "campus-bench-0d6036", {}),
    ("bikes", "campus-bike-rack-386d4d", {}),
    ("lamp", "campus-lamp-post-579291", {"collide": "cylinder"}),
    ("fountain", "campus-plaza-fountain-a0cab1", {"scale": 1.6}),
    ("planter", "campus-planter-box-10970a", {}),
    ("cwall", "campus-wall-run-6a35e0", {}),
    ("pit", "tree-in-pit-grate-ea8010", {"collide": "trunk", "group": "tree"}),
    ("dish", "comms-dish-7b129a", {"scale": 2.2}),
    ("tank", "fuel-tank-3a0111", {"scale": 1.6}),
    ("htank", "horizontal-tank-6e9b8b", {"scale": 1.8}),
    ("solar", "solar-array-rack-789c93", {}),
    ("mast", "antenna-mast-0954b0", {"collide": "cylinder", "scale": 2.6}),
    ("cylinder", "medical-gas-cylinder-a2d6a7", {"collide": "cylinder"}),
    ("streetlight", "cobra-head-street-light-3e25b8", {"collide": "cylinder"}),
    ("kiosk", "campus-coffee-kiosk-ec2395", {}),
]


def write_rooms(path):
    out = ["", "pub const rooms = struct {"]

    for name, rs in ROOMS.items():
        out.append("    pub const %s = [_][6]f32{" % name)

        for r in rs:
            out.append("        .{ %s }," % ", ".join("%.3f" % v for v in r))

        out.append("    };")

    out.append("};")
    out.append("")

    with open(path, "a") as f:
        f.write("\n".join(out))


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "lab")
    os.makedirs(pf.OUT, exist_ok=True)

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(pf.OUT, f))

    infos = {}

    for name, W, D, nf, seed in (("lab_big", 40, 20, 2, 3), ("lab_mid", 32, 16, 2, 7), ("lab_low", 24, 16, 1, 11)):
        infos[name] = lab_building(name, W, D, nf, seed)

    for name, kind in (("puddle", "puddle"),):
        infos[name] = decal(name, kind)

    for name, src, opts in PROPS:
        infos[name] = kitprop(name, src, **opts)

    for name, src, opts in XPROPS:
        if name in ("ward", "annexe", "canopy", "solar", "genset"):
            opts = dict(opts)
            opts["k"] = "decross"

        infos[name] = kitprop(name, os.path.join(LX, src + ".glb"), **opts)

    path = os.path.join(root, "src/shared/maps", "lab_kit.zig")
    emit_zig("lab", infos, path)
    write_solids(path)
    write_rooms(path)


main()
