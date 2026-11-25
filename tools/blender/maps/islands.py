import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DIR"] = "islands"
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|^icosphere|shadow|ground.?plane|^plane", re.I)

X = os.path.join(os.path.dirname(P.rstrip("/")), "islands_x")
CUBE = "cube-house-module-a9b8e8"
CAVE = "cave-house-front-ed6b36"
ARCH = "arched-passage-56393e"
M = 4.4
TIER = 3.3
PLASTER = (0.95, 0.93, 0.89)
SHADE = (0.86, 0.84, 0.8)
GROUT = (0.62, 0.58, 0.52)
STONES = [(0.86, 0.81, 0.72), (0.82, 0.77, 0.68), (0.89, 0.85, 0.77), (0.8, 0.75, 0.66)]
BLUE = (0.13, 0.36, 0.72)
WOOD = (0.42, 0.3, 0.2)
FOAM = (0.93, 0.97, 0.98)
LIMESTONE = (1.0, 0.93, 0.8)


def fresh():
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    return bm


def merge(bm, other):
    me = bpy.data.meshes.new("m")
    other.to_mesh(me)
    other.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def paint(bm, c):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            l[col] = (c[0], c[1], c[2], 1.0)


def outward(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def warm_whites(bm, k=(0.93, 0.87, 0.75)):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]

            if min(c[0], c[1], c[2]) > 0.72:
                l[col] = (c[0] * k[0], c[1] * k[1], c[2] * k[2], 1.0)


def desat(bm, amount, k=(1, 1, 1)):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            g = (c[0] + c[1] + c[2]) / 3
            l[col] = tuple(min(1.0, (c[i] + (g - c[i]) * amount) * k[i]) for i in range(3)) + (1.0,)


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


def tiles(bm, x0, y0, x1, y1, z, n, seed):
    add_box(bm, (x0, y0, z - 0.12), (x1, y1, z - 0.02), GROUT)
    sx = (x1 - x0) / n
    sy = (y1 - y0) / n
    k = seed

    for i in range(n):
        for j in range(n):
            k = (k * 1103515245 + 12345) & 0x7FFFFFFF
            c = STONES[k % len(STONES)]
            add_box(bm, (x0 + i * sx + 0.04, y0 + j * sy + 0.04, z - 0.1), (x0 + (i + 1) * sx - 0.04, y0 + (j + 1) * sy - 0.04, z), c)


def block():
    bm = fresh()
    h = M / 2
    add_box(bm, (-h, -h, -17.0), (h, h, -0.3), PLASTER)
    add_box(bm, (-h - 0.04, -h - 0.04, -0.34), (h + 0.04, h + 0.04, -0.1), SHADE)
    add_box(bm, (-h - 0.02, -h - 0.02, -17.0), (h + 0.02, h + 0.02, -16.2), (0.8, 0.76, 0.68))
    tiles(bm, -h, -h, h, h, 0.0, 4, 7)

    return bm


def quay():
    bm = fresh()
    h = M / 2
    add_box(bm, (-h, -h, -6.0), (h, h, -0.3), (0.78, 0.72, 0.62))

    for i in range(4):
        z = -0.3 - (i + 1) * 0.55
        add_box(bm, (-h - 0.03, -h - 0.03, z - 0.05), (h + 0.03, h + 0.03, z), (0.66, 0.6, 0.52))

    add_box(bm, (-h - 0.04, -h - 0.04, -0.34), (h + 0.04, h + 0.04, -0.1), (0.9, 0.86, 0.78))
    tiles(bm, -h, -h, h, h, 0.0, 3, 11)

    return bm


def recolor(bm, accent, wall):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            mx = max(c[0], c[1], c[2])
            mn = min(c[0], c[1], c[2])

            if mx - mn > 0.15 and c[2] > c[0]:
                k = (c[0] + c[1] + c[2]) / 3 / 0.4
                l[col] = (min(1, accent[0] * k), min(1, accent[1] * k), min(1, accent[2] * k), 1.0)
            elif mn > 0.7:
                l[col] = (c[0] * wall[0], c[1] * wall[1], c[2] * wall[2], 1.0)


def rim(bm, top, e=2.2):
    add_box(bm, (-e, -e, top), (e, -e + 0.22, top + 0.28), SHADE)
    add_box(bm, (-e, e - 0.22, top), (e, e, top + 0.28), SHADE)
    add_box(bm, (-e, -e, top), (-e + 0.22, e, top + 0.28), SHADE)
    add_box(bm, (e - 0.22, -e, top), (e, e, top + 0.28), SHADE)


def dome_cap(bm, top, r=1.45, c=BLUE):
    d = bmesh.new()
    dc = d.loops.layers.float_color.new("Col")
    bmesh.ops.create_uvsphere(d, u_segments=20, v_segments=10, radius=r)
    bmesh.ops.delete(d, geom=[v for v in d.verts if v.co.z < -0.01], context="VERTS")
    outward(d)

    for v in d.verts:
        v.co.z += top

    for f in d.faces:
        for l in f.loops:
            l[dc] = (c[0], c[1], c[2], 1.0)

    merge(bm, d)


def house(floors, dome=False, accent=None, wall=(1, 1, 1), spin=0, pergola=False):
    bm = fresh()

    for f in range(floors):
        part(bm, CUBE, (0, 0, f * 3.0), ((spin + f) % 4) * math.pi / 2)

    if accent is not None or wall != (1, 1, 1):
        recolor(bm, accent or BLUE, wall)

    lo, hi = bounds(bm)
    c = (lo + hi) / 2
    bm.transform(Matrix.Scale(1.1, 4) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z))))

    top = floors * TIER
    rim(bm, top)

    if dome:
        add_box(bm, (-1.3, -1.3, top), (1.3, 1.3, top + 0.7), PLASTER)
        add_box(bm, (-1.38, -1.38, top + 0.62), (1.38, 1.38, top + 0.74), SHADE)
        dome_cap(bm, top + 0.72, 1.4, accent or BLUE)
    else:
        sx = 1.3 if spin % 2 else -1.3
        add_box(bm, (sx - 0.3, 1.2, top), (sx + 0.3, 1.8, top + 1.1), PLASTER)
        add_box(bm, (sx - 0.38, 1.12, top + 1.1), (sx + 0.38, 1.88, top + 1.22), SHADE)
        add_box(bm, (sx - 0.16, 1.34, top + 1.22), (sx + 0.16, 1.66, top + 1.4), (0.55, 0.5, 0.46))

    if pergola:
        for px in (-1.9, 1.9):
            add_box(bm, (px - 0.08, -1.9 - 0.08, top), (px + 0.08, -1.9 + 0.08, top + 2.3), WOOD)
        for px in (-1.9, 1.9):
            add_box(bm, (px - 0.08, 0.2 - 0.08, top), (px + 0.08, 0.2 + 0.08, top + 2.3), WOOD)
        for k in range(7):
            y = -2.0 + k * 0.38
            add_box(bm, (-2.1, y - 0.04, top + 2.3), (2.1, y + 0.04, top + 2.4), (0.55, 0.4, 0.26))
        add_box(bm, (-2.05, -2.0, top + 2.22), (-1.85, 0.3, top + 2.3), WOOD)
        add_box(bm, (1.85, -2.0, top + 2.22), (2.05, 0.3, top + 2.3), WOOD)

        for k in range(14):
            x = -1.8 + (k * 0.71) % 3.6
            y = -1.9 + (k * 0.53) % 2.1
            add_box(bm, (x - 0.25, y - 0.2, top + 2.4), (x + 0.25, y + 0.2, top + 2.62), (0.3, 0.48, 0.2) if k % 3 else (0.72, 0.2, 0.46))

    return bm


def module(src, accent=None):
    bm = fresh()
    part(bm, src, (0, 0, 0), 0)

    if accent is not None:
        recolor(bm, accent, (1, 1, 1))

    lo, hi = bounds(bm)
    c = (lo + hi) / 2
    bm.transform(Matrix.Scale(1.1, 4) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z))))
    lo, hi = bounds(bm)
    top = hi.z
    add_box(bm, (-2.2, -2.2, top), (2.2, -2.2 + 0.22, top + 0.28), SHADE)
    add_box(bm, (-2.2, 2.2 - 0.22, top), (2.2, 2.2, top + 0.28), SHADE)

    return bm


def stair():
    bm = fresh()
    n = 12
    run = M
    rise = TIER
    d = run / n
    r = rise / n
    w = 1.3
    h = M / 2

    for i in range(n):
        y0 = -i * d
        y1 = -(i + 1) * d
        top = (i + 1) * r
        add_box(bm, (-w, y1, -1.0), (w, y0, top - 0.06), PLASTER)
        add_box(bm, (-w, y1, top - 0.06), (w, y0 + 0.05, top), STONES[i % 2])

    add_box(bm, (-h, -run, -1.0), (-w, 0, rise + 0.9), PLASTER)
    add_box(bm, (w, -run, -1.0), (h, 0, rise + 0.9), PLASTER)
    add_box(bm, (-h - 0.03, -run - 0.03, rise + 0.9), (-w + 0.03, 0.03, rise + 1.0), SHADE)
    add_box(bm, (w - 0.03, -run - 0.03, rise + 0.9), (h + 0.03, 0.03, rise + 1.0), SHADE)

    for i in range(1, n, 1):
        y = -i * d
        z = i * r
        add_box(bm, (-h, y - d, z - 2.2), (-w, y, z + 0.9), PLASTER)
        add_box(bm, (w, y - d, z - 2.2), (h, y, z + 0.9), PLASTER)

    bm2 = fresh()
    merge(bm2, bm)

    return bm2


def parapet():
    bm = fresh()
    h = M / 2
    add_box(bm, (-h, -0.18, 0.0), (h, 0.18, 0.85), PLASTER)
    add_box(bm, (-h - 0.03, -0.22, 0.85), (h + 0.03, 0.22, 0.95), SHADE)

    return bm


def windmill():
    bm = fresh()
    t = bmesh.new()
    t.loops.layers.float_color.new("Col")
    bmesh.ops.create_cone(t, cap_ends=True, segments=20, radius1=2.6, radius2=2.3, depth=7.0)

    outward(t)

    for v in t.verts:
        v.co.z += 3.5

    paint(t, (1.0, 0.99, 0.96))
    merge(bm, t)
    add_box(bm, (-2.75, -2.75, 0.0), (2.75, 2.75, 0.5), (0.8, 0.76, 0.68))
    roof = bmesh.new()
    roof.loops.layers.float_color.new("Col")
    bmesh.ops.create_cone(roof, cap_ends=True, segments=20, radius1=2.5, radius2=0.05, depth=2.4)

    outward(roof)

    for v in roof.verts:
        v.co.z += 8.2

    paint(roof, (0.42, 0.3, 0.2))
    merge(bm, roof)
    add_box(bm, (-0.55, -2.75, 0.4), (0.55, -2.2, 2.5), BLUE)
    add_box(bm, (1.4, -2.45, 4.2), (1.9, -2.1, 4.9), BLUE)
    add_box(bm, (-1.9, -2.45, 3.0), (-1.4, -2.1, 3.7), BLUE)
    add_box(bm, (-0.2, -3.6, 7.2), (0.2, -2.2, 7.6), WOOD)
    hub = Vector((0, -3.5, 7.4))

    for k in range(8):
        a = k * math.pi / 4
        s = bmesh.new()
        s.loops.layers.float_color.new("Col")
        add_box(s, (-0.07, -0.07, 0.0), (0.07, 0.07, 5.2), WOOD)
        add_box(s, (0.07, -0.02, 1.6), (1.15, 0.02, 4.9), (0.95, 0.92, 0.84))
        s.transform(Matrix.Translation(hub) @ Matrix.Rotation(a, 4, "Y"))
        merge(bm, s)

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
    n = 10

    for i in range(n):
        x0 = -length / 2 + i * length / n
        x1 = x0 + length / n * 0.8
        y = math.sin(i * 0.7 + seed) * 0.4
        add_box(bm, (x0, y - 0.12, 0.0), (x1, y + 0.12, 0.02), (0.62, 0.86, 0.88))

    return bm


def quarry_face():
    bm = fresh()
    k = 3

    for j in range(3):
        x = -3.0 - (j % 2) * 0.6

        while x < 3.0:
            k = (k * 1103515245 + 12345) & 0x7FFFFFFF
            w = min(1.1 + (k % 7) * 0.14, 3.0 - x)
            z0 = j * 0.95
            d = 0.05 + (k % 5) * 0.07
            c = LIMESTONE if k % 3 else (0.9, 0.84, 0.72)
            add_box(bm, (max(x, -3.0), -d, z0), (x + w - 0.04, 0.8, z0 + 0.93), (c[0] * 0.94, c[1] * 0.92, c[2] * 0.88))
            x += w

    add_box(bm, (-3.0, -0.1, 2.85), (3.0, 0.8, 2.95), (0.82, 0.76, 0.62))

    return bm


def stone_block():
    bm = fresh()
    add_box(bm, (-1.0, -0.6, 0.0), (1.0, 0.6, 1.1), (0.92, 0.86, 0.74))
    add_box(bm, (-0.95, -0.55, 1.1), (0.95, 0.55, 1.14), (0.86, 0.8, 0.68))

    return bm


def ext(name, src, scale=1.0, k=None, ao=True, rot=0.0, post=None):
    path = src if src.startswith("/") else (os.path.join(X, src + ".glb") if os.path.exists(os.path.join(X, src + ".glb")) else os.path.join(P, src + ".glb"))
    bm = load(path)

    if post:
        post(bm)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale, rot=rot)

    return bm


PIECES = [
    ("block", block, {"group": "building", "collide": "none", "ao": False}),
    ("quay", quay, {"group": "building", "collide": "none", "ao": False}),
    ("cube1", lambda: house(1), {"group": "building", "collide": "none"}),
    ("cube1b", lambda: house(1, accent=(0.2, 0.5, 0.38), spin=1), {"group": "building", "collide": "none"}),
    ("cube1c", lambda: house(1, accent=(0.66, 0.3, 0.2), wall=(1.0, 0.95, 0.86), spin=2), {"group": "building", "collide": "none"}),
    ("cube1p", lambda: house(1, accent=(0.13, 0.36, 0.72), spin=1, pergola=True), {"group": "building", "collide": "none"}),
    ("cube2", lambda: house(2), {"group": "building", "collide": "none"}),
    ("cube2b", lambda: house(2, accent=(0.2, 0.5, 0.38), wall=(1.0, 0.96, 0.9), spin=1), {"group": "building", "collide": "none"}),
    ("cube2c", lambda: house(2, accent=(0.72, 0.52, 0.16), wall=(1.0, 0.92, 0.8), spin=2), {"group": "building", "collide": "none"}),
    ("cube3", lambda: house(3, accent=(0.1, 0.5, 0.6), spin=3), {"group": "building", "collide": "none"}),
    ("dome1", lambda: house(1, dome=True), {"group": "building", "collide": "none"}),
    ("dome2", lambda: house(2, dome=True), {"group": "building", "collide": "none"}),
    ("cave1", lambda: module(CAVE), {"group": "building", "collide": "none"}),
    ("arch", lambda: module(ARCH), {"group": "building", "collide": "none"}),
    ("stair", stair, {"group": "building", "collide": "none"}),
    ("parapet", parapet, {"group": "building", "collide": "none", "ao": False}),
    ("windmill", windmill, {"group": "building", "collide": "none", "ao": False}),
    ("foam", lambda: foam(7.0, 0.9, 1), {"group": "ground", "collide": "none", "ao": False}),
    ("ripple", lambda: ripple(9.0, 4), {"group": "ground", "collide": "none", "ao": False}),
    ("qface", quarry_face, {"group": "building", "collide": "none"}),
    ("sblock", stone_block, {"group": "street", "collide": "box"}),
    ("solar", lambda: ext("solar", "solar-water-heater-db1039"), {"group": "building", "collide": "none"}),
    ("light", lambda: ext("light", "mole-lighthouse-c690b4", 1.3), {"group": "building", "collide": "box"}),
    ("boathouse", lambda: ext("boathouse", "boathouse-cf20e6", 1.1), {"group": "building", "collide": "box"}),
    ("olive", lambda: ext("olive", "olive-tree-3cb4a4", 1.08), {"group": "tree", "collide": "trunk"}),
    ("cypress", lambda: ext("cypress", "pencil-cypress-73f3f4", 1.0), {"group": "bush", "collide": "cylinder"}),
    ("lemon", lambda: ext("lemon", "fruit-tree-4bb1af", 0.95, (0.85, 0.95, 0.7)), {"group": "tree", "collide": "trunk"}),
    ("agave", lambda: ext("agave", "flowering-agave-84b67c", 1.0), {"group": "bush", "collide": "cylinder"}),
    ("bougain", lambda: ext("bougain", "bougainvillea-cb4728", 1.2), {"group": "bush", "collide": "none"}),
    ("geranium", lambda: ext("geranium", "geraniums-in-olive-oil-70e682", 2.0), {"group": "bush", "collide": "none"}),
    ("basil", lambda: ext("basil", "basil-pot-125949", 2.4), {"group": "bush", "collide": "none"}),
    ("bush", lambda: ext("bush", "bush-8bb596", 2.2, (0.86, 0.9, 0.66)), {"group": "bush", "collide": "none"}),
    ("rbush", lambda: ext("rbush", "round-bush-cd2ac0", 1.9, (0.78, 0.82, 0.58)), {"group": "bush", "collide": "none"}),
    ("pine", lambda: ext("pine", "sculpted-pine-e45d4f", 2.2, (0.86, 0.92, 0.8)), {"group": "tree", "collide": "trunk"}),
    ("shrub", lambda: ext("shrub", "trimmed-foundation-shrub-616ce0", 1.5, (0.72, 0.8, 0.56), post=lambda bm: desat(bm, 0.25)), {"group": "bush", "collide": "none"}),
    ("laundry", lambda: ext("laundry", "laundry-line-run-dcbc64", 1.0), {"group": "street", "collide": "none"}),
    ("gwall", lambda: ext("gwall", "low-garden-wall-run-a34d05", 1.0), {"group": "street", "collide": "none"}),
    ("swall", lambda: ext("swall", "low-stone-wall-8a8ea3", 2.0, (1.12, 1.0, 0.84), post=lambda bm: desat(bm, 0.75)), {"group": "street", "collide": "none"}),
    ("taverna", lambda: ext("taverna", "taverna-table-set-6b4bc1", 1.0), {"group": "street", "collide": "box"}),
    ("kafe", lambda: ext("kafe", "kafeneio-table-6d2b91", 1.15), {"group": "street", "collide": "box"}),
    ("chair", lambda: ext("chair", "painted-taverna-chair-f4e97e", 1.0), {"group": "street", "collide": "box"}),
    ("lamp", lambda: ext("lamp", "harbour-lamp-post-3d8032", 0.9), {"group": "street", "collide": "cylinder"}),
    ("boat", lambda: ext("boat", "caique-fishing-boat-262c24", 1.0), {"group": "street", "collide": "box"}),
    ("truck", lambda: ext("truck", "three-wheeled-delivery-mini-744094", 1.0), {"group": "street", "collide": "box"}),
    ("melon", lambda: ext("melon", "melon-cart-75f0cc", 1.0), {"group": "street", "collide": "box"}),
    ("nets", lambda: ext("nets", "fishing-net-heap-d0ce10", 1.0), {"group": "street", "collide": "box"}),
    ("pot", lambda: ext("pot", "clay-storage-pot-626452", 1.9), {"group": "street", "collide": "cylinder"}),
    ("jar", lambda: ext("jar", "clay-wine-jar-8eea26", 1.4), {"group": "street", "collide": "cylinder"}),
    ("barrel", lambda: ext("barrel", "barrel-aadc94", 1.0), {"group": "street", "collide": "box"}),
    ("sack", lambda: ext("sack", "grain-sack-401d96", 1.0), {"group": "street", "collide": "none"}),
    ("barrow", lambda: ext("barrow", "wheelbarrow-0f8406", 1.1), {"group": "street", "collide": "box"}),
    ("tractor", lambda: ext("tractor", "compact-tractor-35b84b", 1.0), {"group": "car", "collide": "box"}),
    ("moped", lambda: ext("moped", "delivery-moped-1aa2ce", 1.0), {"group": "street", "collide": "box"}),
    ("parasol", lambda: ext("parasol", "cafe-parasol-61a313", 1.0, (0.95, 0.95, 1.0)), {"group": "street", "collide": "cylinder"}),
    ("hay", lambda: ext("hay", "hay-bale-079e8c", 1.6), {"group": "street", "collide": "box"}),
    ("haystack", lambda: ext("haystack", "haystack-77b0dd", 1.0), {"group": "street", "collide": "box"}),
    ("rock", lambda: ext("rock", "large-coastal-boulder-a2cab1", 1.0, (1.05, 1.0, 0.9)), {"group": "rock", "collide": "box"}),
    ("outcrop", lambda: ext("outcrop", "rock-outcrop-158ac3", 1.6, (1.08, 1.02, 0.88), post=lambda bm: (warm_whites(bm), desat(bm, 0.5))), {"group": "rock", "collide": "box"}),
    ("pallet", lambda: ext("pallet", "material-pallet-6af263", 1.1, (1.08, 1.02, 0.88)), {"group": "street", "collide": "box"}),
    ("digger", lambda: ext("digger", "mini-excavator-cbe1ae", 1.2), {"group": "car", "collide": "box"}),
    ("bollard", lambda: ext("bollard", "mooring-bollard-2d4bc9", 0.8), {"group": "street", "collide": "cylinder"}),
    ("rope", lambda: ext("rope", "rope-coil-776dcc", 1.2), {"group": "street", "collide": "none"}),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props/islands")
    os.makedirs(pf.OUT, exist_ok=True)
    only = os.environ.get("ONLY", "")
    infos = {}

    for name, fn, opts in PIECES:
        bm = fn()

        if opts.get("ao", True):
            bake_ao(bm)

        info = export(bm, name)
        bm.free()
        info["kind"] = "prop"
        info["group"] = opts["group"]
        info["collide"] = opts["collide"]
        infos[name] = info
        print("DONE", name, info["tris"], [round(v, 2) for v in info["min"]], [round(v, 2) for v in info["max"]])

    emit_zig("islands", infos, os.path.join(root, "src/shared/maps/islands_kit.zig"))


main()
