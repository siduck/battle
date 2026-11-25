import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
import os
import random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
ZIG = args[1]

os.makedirs(OUT, exist_ok=True)


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


SAND = rgb(232, 192, 148)
SAND_DEEP = rgb(214, 170, 126)
SAGE = rgb(146, 182, 152)
TERRA = rgb(204, 112, 88)
TERRA_FLOOR = rgb(208, 128, 104)
FLOOR = rgb(228, 228, 224)
WOOD = rgb(206, 164, 108)
SOIL = rgb(120, 104, 74)
OUTER = rgb(226, 204, 168)

SUN = Vector((0.45, 0.68, -0.58)).normalized()
SHADE = (0.66, 0.71, 0.84)
TILE = 37.5
HALF = 75.0
STEP = 0.6

verts = []
faces = []
face_col = []
occluders_v = []
occluders_f = []
boxes = []
ramps = []
palms = []
spawns = []
weapons = []


def add_face(pts, col):
    base = len(verts)
    verts.extend(pts)
    faces.append(tuple(range(base, base + len(pts))))
    face_col.append(col)


def grid(o, u, v, want, col, step=STEP):
    o = Vector(o)
    u = Vector(u)
    v = Vector(v)

    if u.cross(v).dot(Vector(want)) < 0:
        u, v = v, u

    nu = max(1, math.ceil(u.length / step))
    nv = max(1, math.ceil(v.length / step))
    idx = {}

    for i in range(nu + 1):
        for j in range(nv + 1):
            idx[(i, j)] = len(verts)
            verts.append(o + u * (i / nu) + v * (j / nv))

    for i in range(nu):
        for j in range(nv):
            faces.append((idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
            face_col.append(col)


def visual_box(x0, y0, z0, x1, y1, z1, col, bottom=False):
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    grid((x0, y1, z0), (dx, 0, 0), (0, 0, dz), (0, 1, 0), col)
    grid((x0, y0, z0), (dx, 0, 0), (0, dy, 0), (0, 0, -1), col)
    grid((x0, y0, z1), (dx, 0, 0), (0, dy, 0), (0, 0, 1), col)
    grid((x0, y0, z0), (0, 0, dz), (0, dy, 0), (-1, 0, 0), col)
    grid((x1, y0, z0), (0, 0, dz), (0, dy, 0), (1, 0, 0), col)

    if bottom:
        grid((x0, y0, z0), (dx, 0, 0), (0, 0, dz), (0, -1, 0), col)


def box(x0, y0, z0, x1, y1, z1, col, solid=True):
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    visual_box(x0, y0, z0, x1, y1, z1, col, bottom=y0 > 0.05)

    if solid:
        boxes.append((x0, y0, z0, x1, y1, z1))


def frame(axis, cs, ct, s, y, t):
    if axis == "x":
        return Vector((cs + s, y, ct + t))

    return Vector((ct + t, y, cs + s))


def arch(axis, cs, ct, width, span, ys, top, depth, col):
    r = span / 2
    hw = width / 2
    hd = depth / 2

    def sbox(s0, y0, t0, s1, y1, t1):
        a = frame(axis, cs, ct, s0, y0, t0)
        b = frame(axis, cs, ct, s1, y1, t1)
        box(a.x, a.y, a.z, b.x, b.y, b.z, col)

    sbox(-hw, 0, -hd, -r, ys, hd)
    sbox(r, 0, -hd, hw, ys, hd)

    corner_l = math.atan2(top - ys, -hw)
    corner_r = math.atan2(top - ys, hw)
    angles = [math.pi * (1 - k / 24) for k in range(25)]
    angles = sorted(set([round(a, 6) for a in angles + [corner_l, corner_r]]), reverse=True)

    def outer(a):
        c, sn = math.cos(a), math.sin(a)
        ts = []

        if c < -1e-6:
            ts.append(-hw / c)

        if c > 1e-6:
            ts.append(hw / c)

        if sn > 1e-6:
            ts.append((top - ys) / sn)

        t = min(ts) if ts else hw

        return (c * t, ys + sn * t)

    for side in (1, -1):
        tt = hd * side
        n = frame(axis, 0, 0, 0, 0, side) - frame(axis, 0, 0, 0, 0, 0)

        for i in range(len(angles) - 1):
            a0, a1 = angles[i], angles[i + 1]
            p0 = (r * math.cos(a0), ys + r * math.sin(a0))
            p1 = (r * math.cos(a1), ys + r * math.sin(a1))
            q0 = outer(a0)
            q1 = outer(a1)

            for k in range(3):
                f0, f1 = k / 3, (k + 1) / 3
                pts2 = [
                    (p0[0] + (q0[0] - p0[0]) * f0, p0[1] + (q0[1] - p0[1]) * f0),
                    (p1[0] + (q1[0] - p1[0]) * f0, p1[1] + (q1[1] - p1[1]) * f0),
                    (p1[0] + (q1[0] - p1[0]) * f1, p1[1] + (q1[1] - p1[1]) * f1),
                    (p0[0] + (q0[0] - p0[0]) * f1, p0[1] + (q0[1] - p0[1]) * f1),
                ]
                pts = [frame(axis, cs, ct, p[0], p[1], tt) for p in pts2]
                nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0])

                if nrm.dot(n) < 0:
                    pts.reverse()

                add_face(pts, col)


    for i in range(len(angles) - 1):
        a0, a1 = angles[i], angles[i + 1]
        p0 = (r * math.cos(a0), ys + r * math.sin(a0))
        p1 = (r * math.cos(a1), ys + r * math.sin(a1))
        pts = [frame(axis, cs, ct, p0[0], p0[1], -hd), frame(axis, cs, ct, p1[0], p1[1], -hd), frame(axis, cs, ct, p1[0], p1[1], hd), frame(axis, cs, ct, p0[0], p0[1], hd)]
        mid = (pts[0] + pts[2]) / 2
        centre = frame(axis, cs, ct, 0, ys, 0)
        inward = centre - Vector((mid.x, mid.y, mid.z))
        nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0])

        if nrm.dot(inward) < 0:
            pts.reverse()

        add_face(pts, col)

    a = frame(axis, cs, ct, -hw, top, -hd)
    b = frame(axis, cs, ct, hw, top, hd)
    lo = Vector((min(a.x, b.x), top, min(a.z, b.z)))
    hi = Vector((max(a.x, b.x), top, max(a.z, b.z)))
    grid((lo.x, top, lo.z), (hi.x - lo.x, 0, 0), (0, 0, hi.z - lo.z), (0, 1, 0), col)

    for sgn in (-1, 1):
        e0 = frame(axis, cs, ct, sgn * hw, ys, -hd)
        e1 = frame(axis, cs, ct, sgn * hw, ys, hd)
        out = frame(axis, 0, 0, sgn, 0, 0) - frame(axis, 0, 0, 0, 0, 0)
        grid((e0.x, ys, e0.z), (e1.x - e0.x, 0, e1.z - e0.z), (0, top - ys, 0), (out.x, 0, out.z), col)

    def solid(s0, y0, t0, s1, y1, t1):
        a = frame(axis, cs, ct, s0, y0, t0)
        b = frame(axis, cs, ct, s1, y1, t1)
        boxes.append((min(a.x, b.x), y0, min(a.z, b.z), max(a.x, b.x), y1, max(a.z, b.z)))

    solid(-hw, ys, -hd, -r + 0.5, top, hd)
    solid(r - 0.5, ys, -hd, hw, top, hd)
    solid(-hw, ys + r * 0.92, -hd, hw, top, hd)


def stairs(x0, z0, x1, z1, y0, rise, direction, col):
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    n = max(2, round(rise / 0.25))

    for k in range(n):
        f0 = k / n
        f1 = (k + 1) / n
        h = y0 + rise * f1

        if direction == "pos_z":
            box(x0, y0, z0 + (z1 - z0) * f0, x1, h, z1, col, solid=False)
        elif direction == "neg_z":
            box(x0, y0, z0, x1, h, z1 - (z1 - z0) * f0, col, solid=False)
        elif direction == "pos_x":
            box(x0 + (x1 - x0) * f0, y0, z0, x1, h, z1, col, solid=False)
        else:
            box(x0, y0, z0, x1 - (x1 - x0) * f0, h, z1, col, solid=False)

    ramps.append(((x0, y0, z0), (x1, y0 + rise, z1), direction))


def crate(x, y, z, s):
    h = s / 2
    box(x - h, y, z - h, x + h, y + s, z + h, WOOD)


def planter(x, z, kind):
    box(x - 1.2, 0, z - 1.2, x + 1.2, 0.8, z + 1.2, TERRA)
    visual_box(x - 1.0, 0.8, z - 1.0, x + 1.0, 0.86, z + 1.0, SOIL)
    palms.append((x, 0.8, z, kind))


def palm_occluder(x, y, z, kind):
    top = 7.6 if kind == 0 else 5.3
    lean = 1.1 if kind == 0 else 0.7
    rad = 2.8 if kind == 0 else 2.1
    tx, ty = x + lean, y + top
    base = len(occluders_v)
    seg = 6

    for k in range(seg):
        a = 2 * math.pi * k / seg
        occluders_v.append(Vector((x + 0.18 * math.cos(a), y, z + 0.18 * math.sin(a))))
        occluders_v.append(Vector((tx + 0.15 * math.cos(a), ty, z + 0.15 * math.sin(a))))

    for k in range(seg):
        a = 2 * k
        b = 2 * ((k + 1) % seg)
        occluders_f.append((base + a, base + b, base + b + 1, base + a + 1))

    for k in range(7):
        a = 2 * math.pi * k / 7
        dx, dz = math.cos(a), math.sin(a)
        px, pz = -dz, dx
        b2 = len(occluders_v)
        w = 0.55
        occluders_v.append(Vector((tx + px * 0.1, ty, z + pz * 0.1)))
        occluders_v.append(Vector((tx + dx * rad * 0.55 + px * w, ty - 0.2, z + dz * rad * 0.55 + pz * w)))
        occluders_v.append(Vector((tx + dx * rad, ty - 1.0, z + dz * rad)))
        occluders_v.append(Vector((tx + dx * rad * 0.55 - px * w, ty - 0.2, z + dz * rad * 0.55 - pz * w)))
        occluders_f.append((b2, b2 + 1, b2 + 2, b2 + 3))


def build():
    box(-75, 0, 72, 75, 8, 75, SAND)
    box(-75, 0, -75, 75, 8, -72, SAND)
    box(-75, 0, -72, -72, 8, 72, SAND)
    box(72, 0, -72, 75, 8, 72, SAND)

    planter(-2.2, -1.6, 0)
    planter(2.2, 1.6, 1)
    box(-0.9, 0, -0.9, 0.9, 1.4, 0.9, SAGE)

    sym = []

    def S(kind, *a):
        sym.append((kind, a))

    S("box", -60, 0, 60, -40, 11, 72, SAGE)
    S("box", -72, 0, 48, -60, 9, 72, SAND_DEEP)
    S("box", -70, 0, 38, -64, 15, 44, TERRA)
    S("box", -72, 0, -30, -62, 10, -8, SAGE)
    S("box", 20, 0, 64, 50, 7, 72, SAND_DEEP)

    for cx in (-9, 0, 9):
        S("arch", "x", cx, 16, 9, 6, 4.5, 8.5, 1.4, SAND)

    S("box", -22, 0, 15.3, -13.5, 5, 16.7, SAND)
    S("box", 13.5, 0, 15.3, 22, 5, 16.7, SAND)

    S("box", -30, 0, 6, -22, 6, 40, SAND)
    S("box", -30, 0, -40, -22, 6, -6, SAND)
    S("arch", "z", 0, -26, 12, 8, 3, 8, 8, SAGE)
    S("box", -23, 6, 8, -22, 7.1, 38, SAND)
    S("box", -30, 6, 22, -29, 7.1, 38, SAND)
    S("box", -23, 6, -38, -22, 7.1, -8, SAND)
    S("stairs", -34, -38, -30, -26, 0, 6, "pos_z", SAND_DEEP)

    S("box", -62, 0, 22, -40, 1.5, 40, SAND_DEEP)
    S("stairs", -56, 17, -48, 22, 0, 1.5, "pos_z", SAND_DEEP)
    S("stairs", -40, 29, -35, 35, 0, 1.5, "neg_x", SAND_DEEP)
    S("box", -62, 1.5, 22, -53, 2.7, 22.8, SAGE)
    S("crate", -58, 1.5, 36, 1.4)
    S("crate", -56.6, 1.5, 36, 1.4)
    S("crate", -57.3, 2.9, 36, 1.4)
    S("crate", -46, 1.5, 26, 1.2)
    S("crate", -44, 1.5, 38, 1.4)

    S("box", -55, 0, -12, -45, 1.3, -11.2, SAND)
    S("box", -40, 0, -24, -38.8, 1.3, -14, SAND)
    S("crate", -50, 0, 2, 1.4)
    S("crate", -48.6, 0, 2, 1.4)
    S("crate", -36, 0, -34, 1.2)
    S("crate", -60, 0, -40, 1.4)
    S("crate", -58.6, 0, -41, 1.4)
    S("arch", "x", -48, -45, 14, 8, 4, 8, 1.6, SAGE)
    S("box", -72, 0, -45.8, -55, 6, -44.2, SAND)
    S("box", -41, 0, -45.8, -34.5, 6, -44.2, SAND)

    S("planter", -14, 30, 0)
    S("planter", 14, 30, 1)
    S("planter", -64, 4, 1)
    S("crate", -4, 0, 26, 1.4)
    S("crate", -2.6, 0, 26, 1.4)
    S("crate", -3.3, 1.4, 26, 1.4)
    S("crate", 6, 0, 40, 1.2)
    S("crate", 18, 0, 44, 1.4)
    S("box", -8, 0, 46, 8, 1.3, 46.8, SAGE)
    S("crate", -10, 0, 58, 1.4)
    S("crate", 10, 0, 62, 1.4)
    S("box", -20.7, 0, 47.3, -19.3, 6, 48.7, SAGE)
    S("box", 19.3, 0, 47.3, 20.7, 6, 48.7, SAGE)

    for flip in (1, -1):
        for kind, a in sym:
            a = list(a)

            if flip == -1:
                if kind == "box":
                    a = [-a[3], a[1], -a[5], -a[0], a[4], -a[2], a[6]]
                elif kind == "arch":
                    axis, cs, ct = a[0], a[1], a[2]

                    if axis == "x":
                        a[1], a[2] = -cs, -ct
                    else:
                        a[1], a[2] = -cs, -ct
                elif kind == "stairs":
                    opp = {"pos_z": "neg_z", "neg_z": "pos_z", "pos_x": "neg_x", "neg_x": "pos_x"}
                    a = [-a[2], -a[3], -a[0], -a[1], a[4], a[5], opp[a[6]], a[7]]
                elif kind == "crate":
                    a[0], a[2] = -a[0], -a[2]
                elif kind == "planter":
                    a[0], a[1] = -a[0], -a[1]

            if kind == "box":
                box(*a)
            elif kind == "arch":
                arch(*a)
            elif kind == "stairs":
                stairs(*a)
            elif kind == "crate":
                crate(*a)
            elif kind == "planter":
                planter(*a)

    patches = [(-8, -8, 8, 8), (-62, -6, -44, 6), (44, -6, 62, 6), (-12, 52, 12, 66), (-12, -66, 12, -52)]
    solids_flat = [b for b in boxes if b[1] <= 0.01 and b[4] > 0.5]
    n = int(2 * HALF / 0.5)

    for i in range(n):
        for j in range(n):
            x0 = -HALF + i * 0.5
            z0 = -HALF + j * 0.5
            cx, cz = x0 + 0.25, z0 + 0.25

            if any(b[0] < cx < b[3] and b[2] < cz < b[5] for b in solids_flat):
                continue

            col = FLOOR

            if any(p[0] <= cx <= p[2] and p[1] <= cz <= p[3] for p in patches):
                col = TERRA_FLOOR

            faces.append((len(verts), len(verts) + 1, len(verts) + 2, len(verts) + 3))
            verts.extend([Vector((x0, 0, z0)), Vector((x0, 0, z0 + 0.5)), Vector((x0 + 0.5, 0, z0 + 0.5)), Vector((x0 + 0.5, 0, z0))])
            face_col.append(col)

    for lo, hi in (((-100, -100), (100, -HALF)), ((-100, HALF), (100, 100)), ((-100, -HALF), (-HALF, HALF)), ((HALF, -HALF), (100, HALF))):
        grid((lo[0], 0, lo[1]), (hi[0] - lo[0], 0, 0), (0, 0, hi[1] - lo[1]), (0, 1, 0), OUTER, step=5.0)

    for p in palms:
        palm_occluder(*p)

    for k in range(6):
        x = (-15 + 6 * k)
        spawns.append((x, 0, 62 if k % 2 == 0 else 57, math.pi))
        spawns.append((-x, 0, -62 if k % 2 == 0 else -57, 0.0))

    wl = [(-51, 1.5, 31), (-26, 0, 0), (-45, 0, -20), (-26, 6, -20), (-10, 0, 36), (-60, 0, 12), (0, 0, 10), (-40, 0, 50)]

    for w in wl:
        weapons.append(w)
        weapons.append((-w[0], w[1], -w[2]))


def bake():
    tv = list(verts) + occluders_v
    tf = [tuple(f) for f in faces] + [tuple(i + len(verts) for i in f) for f in occluders_f]
    tree = BVHTree.FromPolygons(tv, tf)
    rng = random.Random(11)
    hemi = []

    while len(hemi) < 10:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))

        if 0.1 < d.length <= 1:
            hemi.append(d.normalized())

    jit = []

    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        o = Vector((math.cos(a), 0, math.sin(a))) * 0.035
        jit.append((SUN + o).normalized())

    colours = {}
    cache = {}

    for fi, f in enumerate(faces):
        p0, p1, p3 = verts[f[0]], verts[f[1]], verts[f[-1]]
        n = (p1 - p0).cross(p3 - p0).normalized()
        col = face_col[fi]
        out = []

        for vi in f:
            q = verts[vi]
            key = (round(q.x, 3), round(q.y, 3), round(q.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2))

            if key not in cache:
                origin = verts[vi] + n * 0.04
                lit = 1.0

                if n.dot(SUN) > 0.02:
                    seen = 0

                    for d in jit:
                        loc, _, _, _ = tree.ray_cast(origin, d, 160.0)

                        if loc is None:
                            seen += 1

                    lit = seen / len(jit)

                occ = 0.0
                total = 0

                for d in hemi:
                    if d.dot(n) < 0:
                        d = -d

                    if d.dot(n) < 0.08:
                        continue

                    total += 1
                    loc, _, _, dist = tree.ray_cast(origin, d, 2.6)

                    if loc is not None:
                        occ += 1 - dist / 2.6

                occ = occ / max(total, 1)
                cache[key] = (lit, occ)

            lit, occ = cache[key]
            ao = 1 - 0.42 * occ
            out.append(tuple(col[c] * (SHADE[c] + (1 - SHADE[c]) * lit) * ao for c in range(3)))

        colours[fi] = out

    return colours


def export(colours):
    tiles = {}

    for fi, f in enumerate(faces):
        c = sum((verts[v] for v in f), Vector()) / len(f)
        tx = min(max(int((c.x + HALF) // TILE), 0), 3)
        tz = min(max(int((c.z + HALF) // TILE), 0), 3)
        tiles.setdefault(tz * 4 + tx, []).append(fi)

    info = []

    for t in range(16):
        tx, tz = t % 4, t // 4
        cx = -HALF + (tx + 0.5) * TILE
        cz = -HALF + (tz + 0.5) * TILE
        fl = tiles.get(t, [])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        me = bpy.data.meshes.new("t")
        pts = []
        polys = []
        loop_cols = []

        for fi in fl:
            f = faces[fi]
            start = len(pts)

            for k, vi in enumerate(f):
                p = verts[vi]
                pts.append((p.x - cx, -(p.z - cz), p.y))
                loop_cols.append(colours[fi][k])

            polys.append(tuple(range(start, start + len(f))))

        me.from_pydata(pts, [], polys)
        me.update()
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

        for li, lp in enumerate(me.loops):
            c = loop_cols[li]
            attr.data[li].color = (min(c[0], 1), min(c[1], 1), min(c[2], 1), 1.0)

        ob = bpy.data.objects.new("t", me)
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.0005)
        bpy.ops.object.mode_set(mode="OBJECT")
        mat = bpy.data.materials.new("courtyard")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        me.materials.append(mat)
        me.color_attributes.active_color = me.color_attributes["Col"]
        me.color_attributes.render_color_index = me.color_attributes.find("Col")
        path = os.path.join(OUT, "t%d.glb" % t)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT", export_attributes=True)
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        info.append((t, cx, cz, (lo[0], lo[2], -hi[1]), (hi[0], hi[2], -lo[1]), os.path.getsize(path), len(me.polygons)))
        print("TILE", t, os.path.getsize(path), len(me.polygons))

    return info


def write_zig(info):
    L = []
    L.append("const geom = @import(\"geom.zig\");")
    L.append("")
    L.append("pub const Ramp = struct { min: [3]f32, max: [3]f32, rise: geom.Rise };")
    L.append("")
    L.append("pub const boxes = [_][6]f32{")

    for b in boxes:
        L.append("    .{ %s }," % ", ".join("%.3f" % v for v in b))

    L.append("};")
    L.append("")
    L.append("pub const ramps = [_]Ramp{")

    for lo, hi, d in ramps:
        L.append("    .{ .min = .{ %.3f, %.3f, %.3f }, .max = .{ %.3f, %.3f, %.3f }, .rise = .%s }," % (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2], d))

    L.append("};")
    L.append("")
    L.append("pub const palms = [_][4]f32{")

    for p in palms:
        L.append("    .{ %.3f, %.3f, %.3f, %d }," % p)

    L.append("};")
    L.append("")
    L.append("pub const spawns = [_][4]f32{")

    for s in spawns:
        L.append("    .{ %.3f, %.3f, %.3f, %.4f }," % s)

    L.append("};")
    L.append("")
    L.append("pub const weapons = [_][3]f32{")

    for w in weapons:
        L.append("    .{ %.3f, %.3f, %.3f }," % w)

    L.append("};")
    L.append("")
    L.append("pub const tiles = [_][2]f32{")

    for t in info:
        L.append("    .{ %.3f, %.3f }," % (t[1], t[2]))

    L.append("};")

    with open(ZIG, "w") as fh:
        fh.write("\n".join(L) + "\n")

    for t in info:
        lo, hi = t[3], t[4]
        print("PROPINFO    .{ .file = \"courtyard/t%d.glb\", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ %.3f, %.3f, %.3f }, .max = .{ %.3f, %.3f, %.3f } }," % (t[0], lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


build()
print("GEOM", len(verts), len(faces), len(boxes), len(ramps))
cols = bake()
print("BAKED")
write_zig(export(cols))
