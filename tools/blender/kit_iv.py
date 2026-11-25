import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
PREV = args[1]
ONLY = args[2].split(",") if len(args) > 2 else None


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def grad(lo, hi, z0, z1):
    return lambda p, n: lerp(lo, hi, (p.z - z0) / max(z1 - z0, 1e-3))


def hexc(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


class Piece:
    def __init__(self, seed=1):
        self.bm = bmesh.new()
        self.cid = self.bm.faces.layers.int.new("cid")
        self.fns = []
        self.rng = random.Random(seed)

    def tag(self, verts, col):
        self.fns.append(col)
        k = len(self.fns)

        for v in verts:
            for f in v.link_faces:
                if f[self.cid] == 0:
                    f[self.cid] = k

    def face(self, verts, col):
        f = self.bm.faces.new(verts)
        self.fns.append(col)
        f[self.cid] = len(self.fns)

        return f

    def prism(self, outline, z0, z1, col):
        lo = [self.bm.verts.new((x, y, z0)) for x, y in outline]
        hi = [self.bm.verts.new((x, y, z1)) for x, y in outline]
        n = len(outline)
        self.fns.append(col)
        k = len(self.fns)
        faces = [self.bm.faces.new(list(reversed(lo))), self.bm.faces.new(hi)]

        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((lo[i], lo[j], hi[j], hi[i])))

        for f in faces:
            f[self.cid] = k

    def box(self, c, size, col, rot=0.0):
        m = Matrix.Translation(Vector(c)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((size[0], size[1], size[2], 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self.tag(r["verts"], col)

    def span(self, a, b, w, h, col):
        a = Vector(a)
        b = Vector(b)
        d = b - a
        length = d.length
        yaw = math.atan2(d.y, d.x)
        pitch = math.atan2(d.z, Vector((d.x, d.y)).length)
        m = Matrix.Translation((a + b) / 2) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(-pitch, 4, "Y") @ Matrix.Diagonal((length, w, h, 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self.tag(r["verts"], col)

    def cone(self, c, r1, r2, h, segs, col, rot=0.0, sx=1.0, sy=1.0):
        m = Matrix.Translation(Vector(c) + Vector((0, 0, h / 2))) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((sx, sy, 1, 1))
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=m)
        self.tag(r["verts"], col)

    def blob(self, c, r, col, sz=1.0, sub=1):
        m = Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r, r, r * sz, 1))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0, matrix=m)

        for v in res["verts"]:
            v.co += Vector((self.rng.uniform(-1, 1), self.rng.uniform(-1, 1), self.rng.uniform(-1, 1))) * r * 0.08

        self.tag(res["verts"], col)

    def finish(self, name, jitter=0.05, under=0.72, bevel=0.0, ao=True, glow=0.0):
        me = bpy.data.meshes.new(name)
        bm = self.bm

        if bevel > 0:
            edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(35)]
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=1, affect="EDGES", profile=0.5, clamp_overlap=True)

            for _ in range(3):
                for f in bm.faces:
                    if f[self.cid] == 0:
                        for e in f.edges:
                            for g in e.link_faces:
                                if g[self.cid] != 0:
                                    f[self.cid] = g[self.cid]

        bm.normal_update()
        zmin = min(v.co.z for v in bm.verts)
        cols = {}

        for f in bm.faces:
            fn = self.fns[f[self.cid] - 1] if f[self.cid] > 0 else (1, 0, 1)
            k = 1 + self.rng.uniform(-jitter, jitter)

            if f.normal.z < -0.5:
                k *= under
            elif f.normal.z > 0.6:
                k *= 1.1

            per = []

            for loop in f.loops:
                c = fn(loop.vert.co, f.normal) if callable(fn) else fn
                occ = 0.62 + 0.38 * min(1.0, max(0.0, (loop.vert.co.z - zmin) / 0.9)) if ao else 1.0
                per.append(tuple(min(1.0, x * k * occ) for x in c))

            cols[f.index] = per

        self.bm.to_mesh(me)
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

        for poly in me.polygons:
            poly.use_smooth = False

            for j, li in enumerate(poly.loop_indices):
                c = cols[poly.index][j]
                attr.data[li].color = (c[0], c[1], c[2], 1 - glow)

        me.color_attributes.active_color = attr
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        mat = bpy.data.materials.get("kit") or bpy.data.materials.new("kit")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
        bsdf.inputs["Roughness"].default_value = 1.0
        me.materials.append(mat)
        self.bm.free()

        return obj


WOOD = hexc("7A5A3E")
WOOD_D = hexc("54402E")
WOOD_L = hexc("94744F")
MUD_LO = hexc("A8916A")
MUD_HI = hexc("C8B48C")
CAP = hexc("D8C8A2")
STRAW_LO = hexc("A88A55")
STRAW_HI = hexc("D2BA82")
DARK = hexc("3A302A")
GRASS_LO = hexc("6F8A4E")
GRASS_HI = hexc("8CA25E")
ACCENT_V = hexc("8C3B2E")
ACCENT_T = hexc("C27C3A")
STRATA = [hexc("8E6E55"), hexc("7A7A74"), hexc("A08A6E"), hexc("6E5E50"), hexc("8A7C6A"), hexc("5E5A58")]


def hut():
    p = Piece(3)
    floor = 1.2

    for sx in (-2.1, 2.1):
        for sy in (-2.1, 2.1):
            p.box((sx, sy, floor / 2), (0.2, 0.2, floor), WOOD_D)

    for i in range(7):
        y = -2.5 + i * 0.715 + 0.35
        p.box((0, y, floor + 0.12), (5.2, 0.66, 0.22), WOOD if i % 2 else WOOD_L)

    wall = grad(hexc("9C8156"), hexc("C9B07E"), floor, floor + 2.2)
    top = floor + 0.24
    hgt = 2.0
    z = top + hgt / 2
    p.box((0, 2.05, z), (4.2, 0.14, hgt), wall)
    p.box((-1.4, -2.05, z), (1.4, 0.14, hgt), wall)
    p.box((1.4, -2.05, z), (1.4, 0.14, hgt), wall)
    p.box((0, -2.05, top + 1.95), (1.4, 0.14, 0.3), wall)

    for sx in (-2.05, 2.05):
        p.box((sx, -1.3, z), (0.14, 1.5, hgt), wall)
        p.box((sx, 1.3, z), (0.14, 1.5, hgt), wall)
        p.box((sx, 0, top + 0.45), (0.14, 1.1, 0.9), wall)
        p.box((sx, 0, top + 1.85), (0.14, 1.1, 0.3), wall)
        p.box((sx * 1.02, 0, top + 0.95), (0.08, 1.2, 0.1), WOOD_D)

    for sx in (-2.1, 2.1):
        for sy in (-2.1, 2.1):
            p.box((sx, sy, top + hgt / 2), (0.24, 0.24, hgt + 0.1), WOOD_D)

    for sy in (-2.1, 2.1):
        p.box((0, sy, top + 0.05), (4.5, 0.18, 0.12), WOOD_D)
        p.box((0, sy, top + hgt), (4.5, 0.2, 0.16), WOOD_D)

    roof_z = top + hgt
    thatch = grad(STRAW_LO, STRAW_HI, roof_z, roof_z + 3)
    p.cone((0, 0, roof_z - 0.25), 4.6, 3.9, 0.45, 4, thatch, rot=math.pi / 4)
    p.cone((0, 0, roof_z + 0.2), 4.0, 0.25, 2.4, 4, thatch, rot=math.pi / 4)
    p.cone((0, 0, roof_z + 2.4), 0.5, 0.1, 0.6, 4, (0.6, 0.42, 0.22), rot=math.pi / 4)

    for sx in (-0.45, 0.45):
        p.span((sx, -3.9, 0), (sx, -2.6, floor + 0.2), 0.1, 0.12, WOOD_D)

    for k in range(4):
        t = (k + 0.5) / 4
        p.box((0, -3.9 + 1.3 * t, (floor + 0.2) * t), (0.95, 0.1, 0.07), WOOD)

    return p.finish("iv_hut", bevel=0.03)


def compound():
    p = Piece(5)
    half = 8.0
    t = 0.6
    hgt = 3.0
    worn = hexc("7E6A4E")
    wall = lambda pt, n: lerp(worn, MUD_HI, pt.z / 1.2) if pt.z < 1.2 else lerp(MUD_HI, CAP, (pt.z - 1.2) / 3)
    gate = 1.6
    vine = lambda pt, n: lerp(hexc("3F5A3A"), hexc("6F8A4E"), (pt.z - 1) / 2)

    def merlons(cx, cy, length, along_x):
        k = int(length / 1.7)

        for i in range(k):
            o = -length / 2 + 0.65 + i * length / k

            if along_x:
                p.box((cx + o, cy, hgt + 0.45), (0.6, t + 0.1, 0.5), wall)
            else:
                p.box((cx, cy + o, hgt + 0.45), (t + 0.1, 0.6, 0.5), wall)

    def run_x(x0, x1, y):
        length = x1 - x0
        cx = (x0 + x1) / 2
        p.box((cx, y, hgt / 2), (length, t, hgt), wall)
        p.box((cx, y, hgt + 0.1), (length + 0.1, t + 0.16, 0.2), CAP)
        p.box((cx, y, 0.2), (length + 0.06, t + 0.14, 0.4), worn)
        merlons(cx, y, length, True)

        for i in range(2):
            vx = x0 + p.rng.uniform(0.15, 0.85) * length
            p.box((vx, y + (t / 2 + 0.03) * (1 if y > 0 else -1), hgt - 0.9), (0.45, 0.05, p.rng.uniform(1.2, 2.2)), vine)

    def run_y(y0, y1, x):
        length = y1 - y0
        cy = (y0 + y1) / 2
        p.box((x, cy, hgt / 2), (t, length, hgt), wall)
        p.box((x, cy, hgt + 0.1), (t + 0.16, length + 0.1, 0.2), CAP)
        p.box((x, cy, 0.2), (t + 0.14, length + 0.06, 0.4), worn)
        merlons(x, cy, length, False)

        for i in range(2):
            vy = y0 + p.rng.uniform(0.15, 0.85) * length
            p.box((x + (t / 2 + 0.03) * (1 if x > 0 else -1), vy, hgt - 0.9), (0.05, 0.45, p.rng.uniform(1.2, 2.2)), vine)

    def tower(x, y):
        p.box((x, y, 2.2), (1.9, 1.9, 4.4), wall)
        p.box((x, y, 4.5), (2.1, 2.1, 0.22), CAP)

        for sx in (-0.7, 0.7):
            for sy in (-0.7, 0.7):
                p.box((x + sx, y + sy, 4.85), (0.5, 0.5, 0.5), wall)

        for k in range(3):
            p.box((x - 0.6 + k * 0.6, y, 3.9), (0.12, 2.3, 0.12), WOOD)

    run_x(-half, half, half)
    run_x(-half, -gate, -half)
    run_x(gate, half, -half)
    run_y(-half, half, -half)
    run_y(-half, half, half)

    for sx in (-half, half):
        for sy in (-half, half):
            tower(sx, sy)

    tower(-half, 0)
    tower(half, 0)
    tower(0, half)

    for k in range(7):
        x = -6 + k * 2
        p.box((x, half - 1.1, 1.0), (0.14, 0.14, 2.0), WOOD_D)
        p.box((x, half - 0.55, 1.0), (0.14, 0.14, 2.0), WOOD_D)

    p.box((0, half - 0.85, 2.05), (12.6, 1.1, 0.12), WOOD)

    for k in range(3):
        p.span((-6 + k * 4, half - 1.1, 0.1), (-4 + k * 4, half - 1.1, 1.95), 0.08, 0.08, WOOD_L)

    for s in (-1, 1):
        p.box((s * (gate + 0.45), -half - 0.5, 2.6), (0.7, 0.05, 1.8), ACCENT_V)
        p.box((s * (gate + 0.45), -half - 0.52, 2.2), (0.3, 0.05, 0.2), CAP)
        p.box((s * half, -half - 1.0, 3.3), (0.9, 0.05, 1.4), ACCENT_V)

    for s in (-1, 1):
        p.cone((s * half * 1.0 + s * 0.35, 0, 0), 0.75, 0.45, 2.6, 4, wall, rot=math.pi / 4, sx=0.7)
        p.cone((0, half + 0.35, 0), 0.75, 0.45, 2.6, 4, wall, rot=math.pi / 4, sy=0.7)

    for s in (-1, 1):
        p.box((s * (gate + 0.45), -half, 1.95), (0.9, 0.9, 3.9), wall)
        p.box((s * (gate + 0.45), -half, 3.95), (1.05, 1.05, 0.2), CAP)

    p.box((0, -half, 3.35), (2 * gate + 1.6, 0.45, 0.32), WOOD_D)

    for k in range(6):
        p.box((-1.5 + k * 0.6, -half - 0.35, 3.0), (0.14, 0.5, 0.14), WOOD)

    p.box((-gate + 0.7, -half - 0.6, 1.3), (1.5, 0.1, 2.6), WOOD, rot=0.5)
    p.box((gate + 0.1, -half + 0.6, 1.3), (1.5, 0.1, 2.6), WOOD_L, rot=-1.9)

    hx, hy, hw, hd, hh = 0.0, 3.6, 9.0, 6.0, 3.6
    house = grad(MUD_LO, MUD_HI, 0, hh)
    p.box((hx, hy, hh / 2), (hw, hd, hh), house)
    p.box((hx, hy, 0.25), (hw + 0.14, hd + 0.14, 0.5), MUD_LO)
    p.box((hx, hy, hh + 0.12), (hw + 0.2, hd + 0.2, 0.24), CAP)

    for sx in (-hw / 2, hw / 2):
        p.box((hx + sx, hy, hh + 0.55), (0.35, hd + 0.2, 0.6), house)

    p.box((hx, hy - hd / 2, hh + 0.55), (hw + 0.2, 0.35, 0.6), house)
    p.box((hx, hy + hd / 2, hh + 0.55), (hw + 0.2, 0.35, 0.6), house)

    for k in range(8):
        x = -hw / 2 + 0.6 + k * (hw - 1.2) / 7
        p.box((x, hy - hd / 2 - 0.3, hh - 0.35), (0.16, 0.7, 0.16), WOOD)

    front = hy - hd / 2
    p.box((-1.2, front - 0.02, 1.15), (1.2, 0.12, 2.3), DARK)
    p.box((-1.2, front - 0.1, 2.38), (1.6, 0.18, 0.16), WOOD)
    p.box((-1.2, front - 0.12, 1.1), (1.0, 0.1, 2.1), WOOD_L)

    for wx in (1.6, 3.2):
        p.box((wx, front - 0.02, 1.9), (0.8, 0.12, 0.7), DARK)
        p.box((wx, front - 0.1, 1.5), (1.05, 0.16, 0.1), WOOD)
        p.box((wx, front - 0.1, 2.3), (1.05, 0.16, 0.1), WOOD)

    for wy in (hy - 1.2, hy + 1.2):
        p.box((-hw / 2 - 0.02, wy, 1.9), (0.12, 0.7, 0.6), DARK)

    lx = 3.0
    for sx in (-0.35, 0.35):
        p.span((lx + sx, front - 1.3, 0), (lx + sx, front - 0.15, hh + 0.9), 0.1, 0.12, WOOD_D)

    for k in range(7):
        tt = (k + 0.6) / 7.5
        p.box((lx, front - 1.3 + 1.15 * tt, (hh + 0.9) * tt), (0.75, 0.08, 0.07), WOOD)

    wx, wy = -4.3, -3.4
    p.cone((wx, wy, 0), 0.95, 0.9, 0.85, 8, hexc("9A978E"))
    p.cone((wx, wy, 0.84), 0.72, 0.72, 0.03, 8, hexc("2F5E68"))
    p.box((wx - 0.85, wy, 1.2), (0.14, 0.14, 2.4), WOOD_D)
    p.box((wx + 0.85, wy, 1.2), (0.14, 0.14, 2.4), WOOD_D)
    p.box((wx, wy, 2.3), (1.9, 0.12, 0.12), WOOD)
    p.cone((wx, wy, 1.4), 0.2, 0.24, 0.32, 6, WOOD_L)

    for j, (jx, jy, s) in enumerate([(5.8, -6.6, 1.0), (6.6, -6.2, 0.8), (6.4, -5.3, 0.9), (-6.8, 5.4, 1.0)]):
        col = ACCENT_T if j % 2 else hexc("A8724A")
        p.cone((jx, jy, 0), 0.22 * s, 0.38 * s, 0.4 * s, 7, col)
        p.cone((jx, jy, 0.4 * s), 0.38 * s, 0.16 * s, 0.4 * s, 7, col)
        p.cone((jx, jy, 0.8 * s), 0.16 * s, 0.2 * s, 0.12 * s, 7, col)

    for k in range(4):
        p.span((-6.9, -1.0 + k * 0.35, 0.15 + (k % 2) * 0.2), (-5.2, -1.0 + k * 0.35, 0.15 + (k % 2) * 0.2), 0.3, 0.3, WOOD if k % 2 else WOOD_L)

    p.box((6.0, 2.0, 2.5), (3.0, 2.4, 0.06), ACCENT_V)
    p.box((6.0, 0.85, 1.25), (0.1, 0.1, 2.5), WOOD_D)
    p.box((7.4, 0.85, 1.25), (0.1, 0.1, 2.5), WOOD_D)

    return p.finish("iv_compound", bevel=0.0)


def tower():
    p = Piece(7)
    wall = grad(MUD_LO, MUD_HI, 0, 8)
    p.cone((0, 0, 0), 2.4, 2.0, 7.4, 4, wall, rot=math.pi / 4)
    p.box((0, 0, 7.5), (3.3, 3.3, 0.25), CAP)

    for s in (-1, 1):
        p.box((s * 1.5, 0, 8.1), (0.3, 3.3, 1.0), wall)
        p.box((0, s * 1.5, 8.1), (3.3, 0.3, 1.0), wall)

        for k in (-1, 0, 1):
            p.box((s * 1.5, k * 1.1, 8.8), (0.34, 0.6, 0.5), wall)
            p.box((k * 1.1, s * 1.5, 8.8), (0.6, 0.34, 0.5), wall)

    for k in range(4):
        p.box((-1.2 + k * 0.8, -1.75, 7.0), (0.14, 0.5, 0.14), WOOD)

    for z in (2.5, 5.0):
        p.box((0, -1.95, z), (0.25, 0.1, 0.7), DARK)
        p.box((1.95, 0, z), (0.1, 0.25, 0.7), DARK)

    p.box((0, -2.0, 1.0), (1.0, 0.12, 2.0), WOOD)

    return p.finish("iv_tower", bevel=0.06)


def bridge():
    p = Piece(9)

    for i in range(9):
        x = -2 + i * 0.5 + 0.25
        col = WOOD if i % 2 else WOOD_L
        p.box((x, p.rng.uniform(-0.05, 0.05), p.rng.uniform(-0.02, 0.02)), (0.44, 2.4, 0.1), col, rot=p.rng.uniform(-0.03, 0.03))

    for s in (-1, 1):
        p.box((0, s * 1.05, -0.12), (4.0, 0.16, 0.16), WOOD_D)
        p.box((-1.9, s * 1.25, 0.5), (0.14, 0.14, 1.2), WOOD_D)
        p.span((-1.9, s * 1.25, 1.0), (0, s * 1.25, 0.85), 0.05, 0.05, (0.72, 0.6, 0.4))
        p.span((0, s * 1.25, 0.85), (2.0, s * 1.25, 1.0), 0.05, 0.05, (0.72, 0.6, 0.4))

    return p.finish("iv_bridge", bevel=0.02)


def waterfall():
    p = Piece(11)
    depth = 34.0
    col = lambda pt, n: lerp((0.62, 0.86, 0.96), (0.9, 0.97, 1.0), (pt.z + depth) / depth * 0.5 + 0.5 if pt.z > -6 else (-pt.z - 6) / depth * 0.3)
    p.blob((0, 0.2, 0.1), 1.6, (0.92, 0.98, 1.0), sz=0.4)
    p.box((0, -1.5, -0.05), (3.0, 3.2, 0.12), (0.5, 0.78, 0.9))
    steps = 7
    w = 2.6

    for k in range(steps):
        z0 = -k * depth / steps
        z1 = -(k + 1) * depth / steps
        w2 = w + 0.35
        p.box((0, 0.3 + k * 0.12, (z0 + z1) / 2), ((w + w2) / 2, 0.25, (z0 - z1) + 0.3), col, rot=p.rng.uniform(-0.04, 0.04))

        for s in (-1, 1):
            p.box((s * (w / 2 - 0.3), 0.45 + k * 0.12, (z0 + z1) / 2), (0.35, 0.15, (z0 - z1) * 0.8), (0.95, 0.99, 1.0))

        w = w2

    for k in range(5):
        a = k * 1.25
        p.blob((math.cos(a) * 1.4, 1.2 + math.sin(a) * 0.8, -depth - 0.5), 1.5, (0.92, 0.97, 1.0), sz=0.6)

    return p.finish("iv_waterfall", jitter=0.02, under=0.95, ao=False, glow=0.4)


def underside(name, seed):
    p = Piece(seed)
    segs = 36
    rng = p.rng
    bands = [(0.0, 1.0), (-0.035, 1.0), (-0.08, 0.96), (-0.09, 0.9), (-0.15, 0.88), (-0.16, 0.82), (-0.27, 0.79), (-0.28, 0.72), (-0.4, 0.66), (-0.41, 0.56), (-0.52, 0.48), (-0.53, 0.38), (-0.64, 0.28), (-0.72, 0.16), (-0.8, 0.04)]
    noise = [rng.uniform(0.9, 1.08) for _ in range(segs)]
    noise = [(noise[i - 1] + noise[i] * 2 + noise[(i + 1) % segs]) / 4 for i in range(segs)]
    rings = []

    for j, (z, r) in enumerate(bands):
        ring = []

        for i in range(segs):
            a = i / segs * math.tau
            rr = r * (noise[i] if j > 0 else 1.0) * (1 + (rng.uniform(-0.03, 0.03) if j > 1 else 0))
            ring.append(p.bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z + (rng.uniform(-0.012, 0.012) if j > 1 else 0))))

        rings.append(ring)

    tip = p.bm.verts.new((0, 0, -0.95))

    def band_col(j):
        if j <= 1:
            return lambda pt, n: GRASS_LO

        base = hexc("9C6B45") if j <= 3 else STRATA[(j // 2) % len(STRATA)]

        def col(pt, n, base=base):
            if n.z > 0.45 and pt.z > -0.45:
                return lerp(GRASS_HI, GRASS_LO, -pt.z / 0.45)

            return lerp(base, tuple(c * 0.62 for c in base), -pt.z / 0.9)

        return col

    for j in range(len(rings) - 1):
        col = band_col(j)

        for i in range(segs):
            i2 = (i + 1) % segs
            p.face((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]), col)

    for i in range(segs):
        p.face((rings[-1][i], rings[-1][(i + 1) % segs], tip), band_col(len(rings)))

    p.face(list(reversed(rings[0])), GRASS_LO)

    for k in range(4):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.2, 0.45)
        p.cone((math.cos(a) * r, math.sin(a) * r, -0.6 - rng.uniform(0.1, 0.25)), 0.0, rng.uniform(0.06, 0.1), rng.uniform(0.2, 0.35), 5, lambda pt, n: lerp((0.36, 0.32, 0.34), (0.56, 0.44, 0.38), pt.z + 1))

    bmesh.ops.recalc_face_normals(p.bm, faces=p.bm.faces[:])

    return p.finish(name, jitter=0.06, under=0.9, ao=False)


def strata_rock(name, seed, layers):
    p = Piece(seed)
    rng = p.rng
    z = 0.0
    r = rng.uniform(1.4, 1.7)
    ox = 0.0
    oy = 0.0

    for k in range(layers):
        h = rng.uniform(0.45, 0.8)
        base = STRATA[(seed + k) % len(STRATA)]
        col = lambda pt, n, base=base: lerp(tuple(c * 0.85 for c in base), base, n.z * 0.5 + 0.5)
        p.cone((ox, oy, z - 0.05), r, r * rng.uniform(0.86, 0.95), h + 0.05, rng.choice([5, 6, 7]), col, rot=rng.uniform(0, 6.28), sx=rng.uniform(0.85, 1.15))
        z += h
        r *= rng.uniform(0.7, 0.86)
        ox += rng.uniform(-0.2, 0.2)
        oy += rng.uniform(-0.2, 0.2)

    p.cone((0, 0, -0.6), r * 0 + 1.6, 1.5, 0.6, 6, STRATA[seed % len(STRATA)])

    return p.finish(name, jitter=0.07, bevel=0.06)


def pine(name, seed, tiers):
    p = Piece(seed)
    rng = p.rng
    p.cone((0, 0, -0.3), 0.26, 0.16, 2.2, 6, WOOD_D)
    z = 1.3
    r = 2.3
    total = 1.3 + tiers * 1.55
    green = lambda pt, n: lerp(tuple(c * 0.78 for c in hexc("3A4A3C")), hexc("5E7350"), pt.z / total + n.z * 0.2)

    for k in range(tiers):
        h = 2.4 - k * 0.15
        p.cone((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), z), r, 0.08, h, 7, green, rot=rng.uniform(0, 6.28))
        z += 1.55
        r *= 0.74

    return p.finish(name, jitter=0.04)


def round_tree():
    p = Piece(21)
    p.cone((0, 0, 0), 0.32, 0.18, 3.6, 6, WOOD_D)
    p.span((0, 0, 2.6), (1.2, 0.3, 3.8), 0.18, 0.18, WOOD_D)
    green = lambda pt, n: lerp(hexc("3F5A3A"), hexc("7C9554"), (pt.z - 3) / 4 + n.z * 0.25)

    for c, r in [((0, 0, 4.6), 2.0), ((1.4, 0.4, 4.2), 1.5), ((-1.1, -0.6, 4.0), 1.4), ((0.2, -0.3, 5.8), 1.4), ((0.5, 1.2, 4.6), 1.3)]:
        p.blob(c, r, green, sz=0.85)

    return p.finish("iv_tree_round", jitter=0.05)


def cloud(name, seed):
    p = Piece(seed)
    rng = p.rng
    col = lambda pt, n: lerp((0.78, 0.86, 0.95), (1.0, 1.0, 1.0), pt.z / 4 + 0.5 + n.z * 0.25)

    for k in range(6):
        p.blob((rng.uniform(-5, 5), rng.uniform(-2.5, 2.5), rng.uniform(0, 1.6)), rng.uniform(2.2, 3.6), col, sz=0.6)

    return p.finish(name, jitter=0.02, under=0.92, ao=False, glow=0.2)


def flower_patch():
    p = Piece(31)
    rng = p.rng
    cols = [(0.96, 0.82, 0.3), (0.95, 0.5, 0.42), (0.98, 0.95, 0.9), (0.85, 0.5, 0.75)]

    for k in range(9):
        x = rng.uniform(-1.2, 1.2)
        y = rng.uniform(-1.2, 1.2)
        h = rng.uniform(0.35, 0.6)
        p.box((x, y, h / 2), (0.05, 0.05, h), (0.3, 0.52, 0.22))
        p.cone((x, y, h), 0.16, 0.05, 0.1, 5, rng.choice(cols))
        p.cone((x + 0.1, y, 0), 0.22, 0.0, 0.35, 3, (0.34, 0.6, 0.26), rot=rng.uniform(0, 6))

    return p.finish("iv_flowers", jitter=0.03)


def cliff(name, seed, w, h, d):
    p = Piece(seed)
    rng = p.rng
    z = 0.0
    k = 0
    inset = 0.0
    half = w / 2

    while z < h:
        lh = rng.uniform(2.0, 3.8) if z < h - 4 else h - z + 0.6
        n = 12
        pts = []

        for i in range(n + 1):
            x = -half + w * i / n
            end = abs(x) / half
            front = -d / 2 + inset + rng.uniform(-0.9, 0.9) + end ** 3 * d * 0.55
            pts.append((x * (1 - 0.02 * k), front))

        outline = pts + [(half * 0.96, d / 2), (-half * 0.96, d / 2)]
        base = STRATA[(seed + k) % len(STRATA)]
        col = lambda pt, nn, base=base: lerp(tuple(c * 0.8 for c in base), tuple(min(1, c * 1.12) for c in base), (pt.z % 3.2) / 3.2)
        top = z + lh >= h
        p.prism(outline, z - (0.4 if k else 1.5), z + lh, col)

        if top:
            cap = [(x * 0.98, y + 0.4) for x, y in pts] + [(half * 0.94, d / 2 - 0.3), (-half * 0.94, d / 2 - 0.3)]
            p.prism(cap, z + lh - 0.05, z + lh + 0.45, lambda pt, nn: hexc("9A9468"))

        z += lh
        inset += rng.uniform(0.2, 1.3)
        k += 1

    for i in range(5):
        x = rng.uniform(-half * 0.8, half * 0.8)
        p.cone((x, -d / 2 - rng.uniform(0.5, 2.0), -1.0), rng.uniform(1.2, 2.2), 0.6, rng.uniform(1.5, 3.0), 6, STRATA[i % len(STRATA)], rot=rng.uniform(0, 6))

    return p.finish(name, jitter=0.05, bevel=0.15)


def terrace():
    p = Piece(51)
    rng = p.rng
    stone = lambda pt, n: lerp(hexc("4F5154"), hexc("8A8A82"), (pt.z % 1.5) / 1.5 + n.z * 0.3)

    for k in range(3):
        z = k * 1.5
        y0 = -6 + k * 4.0
        w = 14 - k * 1.2
        front = [(-w / 2 + w * i / 8, y0 + rng.uniform(-0.15, 0.15) + (abs(i - 4) / 4) ** 2 * 1.2) for i in range(9)]
        outline = front + [(w / 2, 7), (-w / 2, 7)]
        p.prism(outline, z - 1.6, z + 1.5, stone)
        top = [(x, y + 0.25) for x, y in front] + [(w / 2 - 0.2, 6.8), (-w / 2 + 0.2, 6.8)]
        p.prism(top, z + 1.45, z + 1.62, lambda pt, n: hexc("6B7F4F"))

        for r in range(3):
            yy = y0 + 0.9 + r * 1.1

            for i in range(6):
                x = -w / 2 + 1.2 + i * (w - 2.4) / 5
                p.cone((x, yy, z + 1.6), 0.38, 0.12, 0.5, 5, lambda pt, n: lerp(hexc("3F5A3A"), hexc("7C9554"), n.z), rot=rng.uniform(0, 6))

    return p.finish("iv_terrace", jitter=0.05, bevel=0.06)


def orchard_tree():
    p = Piece(53)
    rng = p.rng
    p.cone((0, 0, 0), 0.16, 0.1, 1.6, 6, WOOD_D)
    green = lambda pt, n: lerp(hexc("3F5A3A"), hexc("7C9554"), (pt.z - 1.4) / 2 + n.z * 0.25)
    p.blob((0, 0, 2.2), 1.15, green, sz=0.85)
    p.blob((0.5, 0.2, 2.0), 0.8, green, sz=0.85)

    for k in range(9):
        a = rng.uniform(0, 6.28)
        e = rng.uniform(-0.3, 0.7)
        c = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * 1.12 + Vector((0, 0, 2.2))
        p.blob(c, 0.11, ACCENT_T if k % 3 else ACCENT_V, sub=1)

    return p.finish("iv_orchard", jitter=0.04)


def banner(p, x, y, z, h, w):
    p.box((x, y, z - h / 2), (w, 0.06, h), lambda pt, n: lerp(tuple(c * 0.8 for c in ACCENT_V), ACCENT_V, (pt.z - z + h) / h))
    p.box((x, y, z - h * 0.3), (w * 0.4, 0.07, 0.25), CAP)


def landmark():
    p = Piece(55)
    wall = grad(MUD_LO, MUD_HI, 0, 14)
    p.cone((0, 0, 0), 2.9, 2.3, 12.5, 4, wall, rot=math.pi / 4)

    for z in (4.0, 8.0):
        p.cone((0, 0, z), 2.6 - z * 0.04, 2.55 - z * 0.04, 0.6, 4, ACCENT_V, rot=math.pi / 4)

    p.box((0, 0, 12.6), (3.9, 3.9, 0.3), CAP)

    for s in (-1, 1):
        for k in (-1, 0, 1):
            p.box((s * 1.8, k * 1.2, 13.2), (0.4, 0.7, 0.9), wall)
            p.box((k * 1.2, s * 1.8, 13.2), (0.7, 0.4, 0.9), wall)

    p.cone((0, 0, 12.7), 1.6, 0.1, 2.6, 4, ACCENT_V, rot=math.pi / 4)
    p.box((0, 0, 16.5), (0.1, 0.1, 3.0), WOOD_D)
    p.box((0.75, 0, 17.4), (1.4, 0.05, 0.9), ACCENT_V)

    for z in (3.0, 6.5, 10.0):
        p.box((0, -2.15 + z * 0.045, z), (0.3, 0.12, 0.9), DARK)

    banner(p, 0, -2.25, 11.5, 4.0, 1.3)
    p.box((0, -2.3, 1.1), (1.2, 0.14, 2.2), ACCENT_V)

    for k in range(5):
        p.box((-1.6 + k * 0.8, -2.4, 12.1), (0.16, 0.6, 0.16), WOOD)

    return p.finish("iv_landmark", bevel=0.06)


def flag():
    p = Piece(57)
    p.cone((0, 0, 0), 0.4, 0.3, 0.4, 6, hexc("9A978E"))
    p.cone((0, 0, 0.4), 0.06, 0.05, 6.0, 6, WOOD_D)
    p.cone((0, 0, 6.4), 0.12, 0.0, 0.2, 6, CAP)

    for i in range(4):
        x0 = 0.05 + i * 0.5
        wave = math.sin(i * 1.4) * 0.15
        p.box((x0 + 0.25, wave, 5.6), (0.52, 0.05, 1.1 - i * 0.06), ACCENT_V if i % 3 != 2 else hexc("A8473A"), rot=math.sin(i * 1.4 + 0.7) * 0.3)

    return p.finish("iv_flag", jitter=0.03, bevel=0.01)


def gate():
    p = Piece(59)
    wall = grad(MUD_LO, MUD_HI, 0, 7)

    for s in (-1, 1):
        p.box((s * 9, 0, 3.0), (1.6, 1.6, 6.0), wall)
        p.box((s * 9, 0, 0.3), (1.9, 1.9, 0.6), MUD_LO)
        p.box((s * 9, 0, 6.1), (1.9, 1.9, 0.25), CAP)
        p.cone((s * 9, 0, 6.2), 1.0, 0.1, 1.3, 4, ACCENT_V, rot=math.pi / 4)

    p.box((0, 0, 6.6), (19.6, 1.2, 1.0), wall)
    p.box((0, 0, 6.6), (19.8, 1.26, 0.35), ACCENT_V)
    p.box((0, 0, 7.2), (20.0, 1.4, 0.2), CAP)

    for k in range(9):
        p.box((-8 + k * 2, -0.75, 6.0), (0.16, 0.5, 0.16), WOOD)

    banner(p, -4, -0.68, 6.1, 2.2, 1.1)
    banner(p, 4, -0.68, 6.1, 2.2, 1.1)
    banner(p, -4, 0.68, 6.1, 2.2, 1.1)
    banner(p, 4, 0.68, 6.1, 2.2, 1.1)

    return p.finish("iv_gate", bevel=0.06)


def ridge(name, seed, w, d, H, snow, haze=0.0):
    p = Piece(seed)
    rng = p.rng
    nx, ny = 30, 18
    step = H / 9
    ph = [rng.uniform(0, 6.28) for _ in range(4)]

    def height(x, y):
        t = (y + d / 2) / d
        side = max(0.0, 1 - (abs(x) / (w / 2)) ** 2.4)
        crest = H * (0.62 + 0.22 * math.sin(x * 0.07 + ph[0]) + 0.16 * math.sin(x * 0.19 + ph[1]))
        base = crest * (min(1.0, t * 1.25) ** 0.85) * side
        base += (math.sin(x * 0.5 + ph[2]) * math.sin(y * 0.4 + ph[3])) * 0.8 * side
        f = base / step
        lo = math.floor(f)
        fr = f - lo
        stepped = (lo + max(0.0, (fr - 0.6) / 0.4) ** 1.6) * step

        return stepped * 0.75 + base * 0.25 - (2.5 if t < 0.02 or side < 0.02 else 0)

    verts = []

    for j in range(ny + 1):
        row = []

        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            y = -d / 2 + d * j / ny
            row.append(p.bm.verts.new((x, y, height(x, y))))

        verts.append(row)

    tones = [hexc("8E6E55"), hexc("7A7A74"), hexc("9A8A72"), hexc("6E6A62")]
    haze_c = hexc("A9B6BD")

    def col(pt, n):
        rel = pt.z / H
        band = tones[int(max(pt.z, 0) / step) % len(tones)]

        if snow and rel > 0.78 and n.z > 0.35:
            c = lerp(hexc("C9CBC8"), hexc("DCDDDA"), (rel - 0.78) * 4)
        elif n.z > 0.82 and rel < 0.7:
            c = lerp(hexc("6B7F4F"), hexc("9A9468"), rel * 1.2)
        elif pt.z < 2.5:
            c = hexc("9A978E")
        else:
            c = lerp(band, tuple(min(1, v * 1.28) for v in band), rel)

        return lerp(c, haze_c, haze)

    for j in range(ny):
        for i in range(nx):
            a, b2, c, e = verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]
            p.face((a, b2, c), col)
            p.face((a, c, e), col)

    for k in range(int(w / 6)):
        x = rng.uniform(-w * 0.42, w * 0.42)
        y = -d / 2 + rng.uniform(1, 5)
        p.cone((x, y, height(x, y) - 0.4), rng.uniform(0.8, 1.8), rng.uniform(0.3, 0.7), rng.uniform(0.6, 1.4), 5, lerp(hexc("9A978E"), haze_c, haze), rot=rng.uniform(0, 6))

    return p.finish(name, jitter=0.05, ao=False)


def hay():
    p = Piece(61)
    straw = lambda pt, n: lerp(STRAW_LO, STRAW_HI, pt.z / 1.6 + n.z * 0.2)

    for x, y, z in [(0, 0, 0), (1.25, 0.1, 0), (0.6, 0.05, 0.85)]:
        p.box((x, y, z + 0.42), (1.2, 0.8, 0.84), straw)
        p.box((x, y, z + 0.42), (1.22, 0.06, 0.86), hexc("8A6A3A"))

    return p.finish("iv_hay", jitter=0.05, bevel=0.06)


def cart():
    p = Piece(63)
    p.box((0, 0, 0.95), (2.4, 1.3, 0.12), WOOD)

    for s in (-1, 1):
        p.box((0, s * 0.62, 1.25), (2.4, 0.08, 0.5), WOOD_L)
        p.box((s * 1.18, 0, 1.25), (0.08, 1.3, 0.5), WOOD_L)
        m = Matrix.Translation(Vector((0.2, s * 0.8, 0.55))) @ Matrix.Rotation(math.pi / 2, 4, "X")
        r = bmesh.ops.create_cone(p.bm, cap_ends=True, cap_tris=False, segments=10, radius1=0.55, radius2=0.55, depth=0.12, matrix=m)
        p.tag(r["verts"], WOOD_D)

    for s in (-1, 1):
        p.span((-1.2, s * 0.35, 0.95), (-3.0, s * 0.3, 0.6), 0.08, 0.08, WOOD_D)

    p.box((0.3, 0, 1.3), (1.1, 0.8, 0.6), STRAW_HI)

    return p.finish("iv_cart", jitter=0.04, bevel=0.03)


def fence():
    p = Piece(65)

    for k in range(3):
        x = -2 + k * 2
        p.box((x, 0, 0.6), (0.14, 0.14, 1.2), WOOD_D)

    for z in (0.45, 0.95):
        p.span((-2.1, 0, z), (2.1, 0, z + p.rng.uniform(-0.05, 0.05)), 0.07, 0.12, WOOD_L)

    return p.finish("iv_fence", jitter=0.06, bevel=0.02)


def bush():
    p = Piece(67)
    green = lambda pt, n: lerp(hexc("3F5A3A"), hexc("7C9554"), pt.z / 1.4 + n.z * 0.3)

    for c, r in [((0, 0, 0.5), 0.75), ((0.6, 0.2, 0.4), 0.55), ((-0.5, 0.3, 0.35), 0.5), ((0.1, -0.5, 0.35), 0.45)]:
        p.blob(c, r, green, sz=0.8)

    return p.finish("iv_bush", jitter=0.04)


def stall():
    p = Piece(81)

    for sx in (-1.6, 1.6):
        for sy in (-1.1, 1.1):
            p.box((sx, sy, 1.2), (0.14, 0.14, 2.4 if sy < 0 else 2.1), WOOD_D)

    p.box((0, -1.25, 0.5), (3.4, 0.5, 1.0), WOOD)
    p.box((0, -1.25, 1.03), (3.6, 0.7, 0.08), WOOD_L)
    awn = lambda pt, n: lerp(tuple(c * 0.82 for c in ACCENT_V), ACCENT_V, (pt.z - 2.1) / 0.5)

    for k in range(6):
        x = -1.55 + k * 0.62
        p.span((x, -1.6, 2.35), (x, 1.2, 2.1), 0.62, 0.05, awn if k % 2 == 0 else CAP)

    for k, c in enumerate([ACCENT_T, hexc("A8724A"), ACCENT_T, hexc("7C9554")]):
        p.cone((-1.1 + k * 0.7, -1.25, 1.07), 0.18, 0.12, 0.35, 7, c)

    p.box((1.0, 0.4, 0.3), (0.6, 0.6, 0.6), WOOD_L)
    p.box((1.3, 0.6, 0.25), (0.5, 0.5, 0.5), WOOD)

    return p.finish("iv_stall", jitter=0.05, bevel=0.02)


def platform():
    p = Piece(83)
    deck = 3.0

    for sx in (-1.8, 1.8):
        for sy in (-1.8, 1.8):
            p.box((sx, sy, deck / 2), (0.22, 0.22, deck), WOOD_D)

    for sx in (-1.8, 1.8):
        p.span((sx, -1.8, 0.3), (sx, 1.8, deck - 0.3), 0.1, 0.1, WOOD)

    for k in range(6):
        p.box((0, -1.75 + k * 0.7, deck + 0.05), (4.0, 0.62, 0.1), WOOD if k % 2 else WOOD_L)

    for s in (-1, 1):
        p.box((s * 1.95, 0, deck + 0.55), (0.1, 4.0, 0.1), WOOD_D)
        p.box((0, 1.95, deck + 0.55), (4.0, 0.1, 0.1), WOOD_D)

        for k in range(3):
            p.box((s * 1.95, -1.6 + k * 1.6, deck + 0.3), (0.1, 0.1, 0.6), WOOD_D)
            p.box((-1.6 + k * 1.6, 1.95, deck + 0.3), (0.1, 0.1, 0.6), WOOD_D)

    p.box((-1.2, 1.95, deck + 0.7), (1.0, 0.06, 0.6), ACCENT_V)

    for k in range(10):
        t = (k + 0.5) / 10
        p.box((0, -2.0 - 4.0 * t, deck * (1 - t) - 0.05), (1.4, 0.42, 0.08), WOOD_L)

    for s in (-0.72, 0.72):
        p.span((s, -2.0, deck), (s, -6.0, 0), 0.1, 0.18, WOOD_D)

    return p.finish("iv_platform", jitter=0.05, bevel=0.02)


def logs():
    p = Piece(85)
    bark = lambda pt, n: lerp(WOOD_D, WOOD, n.z * 0.5 + 0.5)

    for row, (n, z) in enumerate([(4, 0.25), (3, 0.68), (2, 1.1)]):
        for i in range(n):
            y = (i - (n - 1) / 2) * 0.5
            m = Matrix.Translation(Vector((p.rng.uniform(-0.1, 0.1), y, z))) @ Matrix.Rotation(math.pi / 2, 4, "Y")
            r = bmesh.ops.create_cone(p.bm, cap_ends=True, cap_tris=False, segments=7, radius1=0.24, radius2=0.24, depth=3.2, matrix=m)
            p.tag(r["verts"], bark)

    return p.finish("iv_logs", jitter=0.05)


def ruin_arch():
    p = Piece(87)
    stone = lambda pt, n: lerp(hexc("6E6A62"), hexc("A39C8E"), pt.z / 6 + n.z * 0.2)
    moss = lambda pt, n: lerp(hexc("4F6A3E"), hexc("6F8A4E"), n.z)

    for s in (-1, 1):
        for k in range(5):
            p.box((s * 2.4 + p.rng.uniform(-0.05, 0.05), 0, 0.55 + k * 1.05), (1.1 - k * 0.03, 1.1, 1.0), stone, rot=p.rng.uniform(-0.04, 0.04))

    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        p.box((math.cos(a) * 2.4, 0, 5.2 + math.sin(a) * 1.6), (0.9, 1.0, 0.7), stone, rot=0)

    p.box((0, 0, 6.95), (5.6, 1.15, 0.35), stone)
    p.box((-1.5, 0, 7.2), (2.0, 1.0, 0.18), moss)
    p.box((2.4, 0.56, 3.0), (0.6, 0.05, 2.4), moss)

    for k in range(4):
        p.cone((p.rng.uniform(-4, 4), p.rng.uniform(-1.5, 1.5), 0), 0.5, 0.2, 0.5, 5, stone, rot=p.rng.uniform(0, 6))

    return p.finish("iv_ruin_arch", jitter=0.07, bevel=0.06)


def ruin_pillar():
    p = Piece(89)
    stone = lambda pt, n: lerp(hexc("6E6A62"), hexc("A39C8E"), pt.z / 5 + n.z * 0.2)
    p.box((0, 0, 0.2), (1.6, 1.6, 0.4), stone)

    for k in range(4):
        p.cone((p.rng.uniform(-0.04, 0.04), p.rng.uniform(-0.04, 0.04), 0.4 + k * 0.9), 0.55, 0.52, 0.88, 8, stone, rot=k)

    p.cone((0, 0, 4.0), 0.52, 0.3, 0.4, 8, stone, rot=1, sx=1.2)
    p.box((0.4, 0, 4.4), (0.5, 0.6, 0.2), lambda pt, n: hexc("6F8A4E"))

    return p.finish("iv_ruin_pillar", jitter=0.07, bevel=0.04)


def flag_t():
    p = Piece(91)
    p.cone((0, 0, 0), 0.4, 0.3, 0.4, 6, hexc("9A978E"))
    p.cone((0, 0, 0.4), 0.06, 0.05, 5.0, 6, WOOD_D)

    for i in range(3):
        wave = math.sin(i * 1.4) * 0.15
        p.box((0.05 + i * 0.5 + 0.25, wave, 4.8), (0.52, 0.05, 0.9 - i * 0.12), ACCENT_T, rot=math.sin(i * 1.4 + 0.7) * 0.3)

    return p.finish("iv_flag_t", jitter=0.03, bevel=0.01)


builders = {
    "iv_hut": hut,
    "iv_compound": compound,
    "iv_tower": tower,
    "iv_bridge": bridge,
    "iv_waterfall": waterfall,
    "iv_under_a": lambda: underside("iv_under_a", 41),
    "iv_under_b": lambda: underside("iv_under_b", 42),
    "iv_rock_a": lambda: strata_rock("iv_rock_a", 1, 3),
    "iv_rock_b": lambda: strata_rock("iv_rock_b", 2, 4),
    "iv_rock_c": lambda: strata_rock("iv_rock_c", 4, 2),
    "iv_pine_a": lambda: pine("iv_pine_a", 5, 4),
    "iv_pine_b": lambda: pine("iv_pine_b", 6, 3),
    "iv_tree_round": round_tree,
    "iv_cloud": lambda: cloud("iv_cloud", 7),
    "iv_flowers": flower_patch,
    "iv_terrace": terrace,
    "iv_orchard": orchard_tree,
    "iv_landmark": landmark,
    "iv_flag": flag,
    "iv_gate": gate,
    "iv_ridge_a": lambda: ridge("iv_ridge_a", 71, 90, 55, 50, True),
    "iv_ridge_b": lambda: ridge("iv_ridge_b", 72, 70, 45, 36, False),
    "iv_range": lambda: ridge("iv_range", 73, 180, 70, 95, True, haze=0.0),
    "iv_hay": hay,
    "iv_stall": stall,
    "iv_platform": platform,
    "iv_logs": logs,
    "iv_ruin_arch": ruin_arch,
    "iv_ruin_pillar": ruin_pillar,
    "iv_flag_t": flag_t,
    "iv_cart": cart,
    "iv_fence": fence,
    "iv_bush": bush,
    "iv_cliff_a": lambda: cliff("iv_cliff_a", 3, 30, 22, 14),
    "iv_cliff_b": lambda: cliff("iv_cliff_b", 8, 26, 16, 12),
    "iv_cliff_c": lambda: cliff("iv_cliff_c", 11, 16, 11, 9),
}


def render(obj, path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.view_settings.view_transform = "Standard"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "VERTEX"
    scene.render.resolution_x = 420
    scene.render.resolution_y = 340
    scene.render.film_transparent = False
    scene.world = scene.world or bpy.data.worlds.new("w")
    scene.world.color = (0.55, 0.7, 0.85)
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    c = (lo + hi) / 2
    size = (hi - lo).length
    cam_data = bpy.data.cameras.new("c")
    cam_data.lens = 50
    cam = bpy.data.objects.new("c", cam_data)
    scene.collection.objects.link(cam)
    d = Vector((1.0, -1.3, 0.75)).normalized()
    cam.location = c + d * size * 1.45
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


for name, fn in builders.items():
    if ONLY and name not in ONLY:
        continue

    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = fn()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    kw = dict(filepath=f"{OUT}/{name}.glb", export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_normals=True, export_texcoords=False, export_materials="EXPORT")

    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color="ACTIVE", export_all_vertex_colors=False)
    except TypeError:
        bpy.ops.export_scene.gltf(**kw)

    render(obj, f"{PREV}/{name}.png")
    print("KIT", name, len(obj.data.polygons))
