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
        k = int(length / 1.5)

        for i in range(k):
            o = -length / 2 + 0.6 + i * length / k

            if along_x:
                p.box((cx + o, cy, hgt + 0.55), (0.75, t + 0.24, 0.8), wall)
                p.box((cx + o, cy, hgt + 0.98), (0.85, t + 0.32, 0.08), CAP)
            else:
                p.box((cx, cy + o, hgt + 0.55), (t + 0.24, 0.75, 0.8), wall)
                p.box((cx, cy + o, hgt + 0.98), (t + 0.32, 0.85, 0.08), CAP)

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

    walk = hgt - 0.95
    inner = half - t / 2 - 0.5

    for (ax, ay, bx, by) in [(-half + 1.2, inner, half - 1.2, inner), (-inner, -half + 1.2, -inner, half - 1.2), (inner, -half + 1.2, inner, half - 1.2)]:
        cxw = (ax + bx) / 2
        cyw = (ay + by) / 2
        along_x = abs(bx - ax) > abs(by - ay)
        length = abs(bx - ax) if along_x else abs(by - ay)
        p.box((cxw, cyw, walk), (length, 1.0, 0.12) if along_x else (1.0, length, 0.12), WOOD)

        for k in range(int(length / 2) + 1):
            o = -length / 2 + k * length / max(int(length / 2), 1)
            bxk = cxw + (o if along_x else 0)
            byk = cyw + (0 if along_x else o)
            nx = 0 if along_x else (0.45 if bxk > 0 else -0.45)
            ny = (0.45 if byk > 0 else -0.45) if along_x else 0
            p.span((bxk - nx * 0.9, byk - ny * 0.9, walk - 0.05), (bxk + nx * 0.6, byk + ny * 0.6, walk - 0.9), 0.1, 0.1, WOOD_D)
            p.box((bxk - nx * 1.0, byk - ny * 1.0, walk + 0.5), (0.09, 0.09, 1.0), WOOD_D)

        p.box((cxw - (0 if along_x else (0.95 if cxw > 0 else -0.95)), cyw - ((0.95 if cyw > 0 else -0.95) if along_x else 0), walk + 0.95), (length, 0.08, 0.08) if along_x else (0.08, length, 0.08), WOOD)

    for s2 in (-1, 1):
        lx = s2 * (half - 1.6)
        for sx in (-0.3, 0.3):
            p.span((lx + sx, half - 2.2, 0), (lx + sx, half - 1.2, walk + 0.1), 0.08, 0.1, WOOD_D)
        for k in range(6):
            tt = (k + 0.7) / 6.5
            p.box((lx, half - 2.2 + 1.0 * tt, (walk + 0.1) * tt), (0.65, 0.07, 0.06), WOOD)

    gy = -half
    p.box((0, gy, hgt + 0.75), (2 * gate + 2.4, t + 0.5, 1.5), wall)
    p.box((0, gy, hgt + 1.55), (2 * gate + 2.6, t + 0.6, 0.14), CAP)

    for k in range(5):
        p.box((-gate - 0.9 + k * (2 * gate + 1.8) / 4, gy, hgt + 1.95), (0.6, t + 0.5, 0.7), wall)

    for sx in (-0.9, 0.0, 0.9):
        p.box((sx, gy - t / 2 - 0.26, hgt + 0.8), (0.14, 0.04, 0.7), DARK)

    p.box((0, gy - 0.05, 2.98), (2 * gate + 0.6, t + 0.35, 0.36), CAP)
    p.box((0, gy - t / 2 - 0.2, 3.02), (0.5, 0.08, 0.5), QUOIN)

    for k in range(9):
        x = -gate + 0.18 + k * (2 * gate - 0.36) / 8
        p.box((x, gy, 2.15), (0.07, 0.07, 1.6), IRON)
        p.cone((x, gy, 1.2), 0.0, 0.05, 0.16, 4, IRON)

    for k in range(4):
        p.box((0, gy, 1.55 + k * 0.42), (2 * gate - 0.1, 0.06, 0.06), IRON)

    for sx in (-1, 1):
        banner(p, sx * (gate + 2.6), gy - t / 2 - 0.05, hgt - 0.1, 2.4, 1.0)
        banner(p, sx * half, gy - 1.02, 4.3, 2.0, 0.8)

    for sx in (-half, half):
        for sy in (-half, half):
            for (dx, dy) in ((0, -1), (-1, 0) if sx < 0 else (1, 0)):
                p.box((sx + dx * 0.97, sy + dy * 0.97 if dy else sy, 2.6), (0.12 if dx else 0.1, 0.1 if dx else 0.12, 0.75), DARK)

    return ray_ao(p.finish("iv_compound", bevel=0.02))


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


STONE_LO = hexc("9A9282")
STONE_HI = hexc("BCB2A0")
QUOIN = hexc("CEC4B0")
SLATE_LO = hexc("4E5560")
SLATE_HI = hexc("6C7480")
TIMBER = hexc("8A6440")
TIMBER_D = hexc("5A3E28")
PLANK_A = hexc("AE7E50")
PLANK_B = hexc("986C44")
IRON = hexc("3A3A3E")
SHUTTERS = [hexc("8C3B2E"), hexc("3F6A5C"), hexc("2F5E68")]
BLOOMS = [hexc("C8443A"), hexc("D86A8A"), hexc("E0B040"), hexc("F0E6D8")]
LEAVES = hexc("4F6E3A")
GLOW_WARM = hexc("FFD08A")
POT = hexc("A8603E")


def ray_ao(obj, strength=0.22, reach=1.6):
    from mathutils.bvhtree import BVHTree

    me = obj.data
    verts = [v.co.copy() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    zmin = min(v.z for v in verts)
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    g = len(verts)
    verts += [Vector((lo.x - 20, lo.y - 20, zmin)), Vector((hi.x + 20, lo.y - 20, zmin)), Vector((hi.x + 20, hi.y + 20, zmin)), Vector((lo.x - 20, hi.y + 20, zmin))]
    polys.append((g, g + 1, g + 2, g + 3))
    tree = BVHTree.FromPolygons(verts, polys)
    rng = random.Random(3)
    dirs = []

    while len(dirs) < 20:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))

        if 0.05 < d.length <= 1:
            dirs.append(d.normalized())

    attr = me.color_attributes["Col"]
    cache = {}

    for poly in me.polygons:
        n = poly.normal

        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            key = (vi, round(n.x, 2), round(n.y, 2), round(n.z, 2))

            if key not in cache:
                origin = me.vertices[vi].co * 0.9 + poly.center * 0.1 + n * 0.01
                hits = 0.0
                total = 0

                for d in dirs:
                    if d.dot(n) <= 0.05:
                        d = d - n * (2 * d.dot(n))

                    if d.dot(n) <= 0.05:
                        continue

                    total += 1
                    loc, _, _, dist = tree.ray_cast(origin, d, reach)

                    if loc is not None:
                        hits += 1 - dist / reach

                cache[key] = hits / max(total, 1)

            k = 1 - strength * cache[key]
            c = attr.data[li].color
            attr.data[li].color = (c[0] * k, c[1] * k, c[2] * k * (1 + 0.04 * cache[key]), c[3])

    return obj


def gable_roof(p, cx, cy, w, d, z0, rise, over_s, over_g, col_lo, col_hi, ridge_col):
    half = d / 2 + over_s
    slope = math.atan2(rise, d / 2)
    length = math.hypot(d / 2 + over_s, rise + over_s * math.tan(slope))
    roof = lambda pt, n: lerp(col_lo, col_hi, (pt.z - z0) / max(rise, 0.1))

    for s in (-1, 1):
        my = cy + s * (d / 4 + over_s / 2)
        mz = z0 + rise / 2 - over_s * math.tan(slope) / 2
        m = Matrix.Translation(Vector((cx, my, mz))) @ Matrix.Rotation(-s * slope, 4, "X") @ Matrix.Diagonal((w + 2 * over_g, length, 0.2, 1))
        r = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
        p.tag(r["verts"], roof)

        for k in range(5):
            t = (k + 0.5) / 5
            yy = cy + s * (half - t * half)
            zz = z0 + rise * t - over_s * math.tan(slope) * (1 - t)
            m2 = Matrix.Translation(Vector((cx, yy, zz + 0.12))) @ Matrix.Rotation(-s * slope, 4, "X") @ Matrix.Diagonal((w + 2 * over_g + 0.04, 0.05, 0.06, 1))
            r2 = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m2)
            p.tag(r2["verts"], tuple(c * 0.82 for c in col_lo))

        for e in (-1, 1):
            m3 = Matrix.Translation(Vector((cx + e * (w / 2 + over_g), my, mz - 0.05))) @ Matrix.Rotation(-s * slope, 4, "X") @ Matrix.Diagonal((0.12, length + 0.05, 0.36, 1))
            r3 = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m3)
            p.tag(r3["verts"], TIMBER_D)

    p.box((cx, cy, z0 + rise + 0.12), (w + 2 * over_g + 0.1, 0.36, 0.22), ridge_col)


def gable_end(p, cx, cy, w, d, z0, rise, col):
    for e in (-1, 1):
        x = cx + e * w / 2
        a = p.bm.verts.new((x, cy - d / 2, z0))
        b = p.bm.verts.new((x, cy + d / 2, z0))
        c = p.bm.verts.new((x, cy, z0 + rise))
        f = p.face([a, b, c] if e > 0 else [c, b, a], col)

        for k in range(-2, 3):
            hh = rise * (1 - abs(k) / 2.6)

            if hh > 0.3:
                p.box((x + e * 0.03, cy + k * d / 6, z0 + hh / 2), (0.06, 0.09, hh), TIMBER_D)


def window(p, x, y, z, ww, wh, face, shutter, flowers=False, open_l=True):
    p.box((x, y + face * 0.06, z), (ww, 0.16, wh), DARK)
    p.box((x, y + face * 0.12, z - wh / 2 - 0.06), (ww + 0.3, 0.22, 0.12), QUOIN)
    p.box((x, y + face * 0.12, z + wh / 2 + 0.07), (ww + 0.22, 0.2, 0.14), TIMBER_D)

    for s in (-1, 1):
        p.box((x + s * (ww / 2 + 0.04), y + face * 0.12, z), (0.08, 0.2, wh), TIMBER_D)

    p.box((x, y + face * 0.11, z), (0.05, 0.08, wh), TIMBER)
    p.box((x, y + face * 0.11, z + wh * 0.05), (ww, 0.08, 0.05), TIMBER)

    for s in (-1, 1):
        if s == -1 and not open_l:
            p.box((x - ww / 4, y + face * 0.14, z), (ww / 2, 0.06, wh), shutter)
            continue

        hx = x + s * (ww / 2 + 0.3)
        p.box((hx, y + face * 0.12, z), (0.52, 0.06, wh + 0.04), shutter)

        p.box((hx, y + face * 0.16, z), (0.46, 0.03, 0.05), tuple(c * 0.75 for c in shutter))

    if flowers:
        by = y + face * 0.32
        p.box((x, by, z - wh / 2 - 0.22), (ww + 0.2, 0.32, 0.26), TIMBER)

        for k in range(5):
            fx = x - ww / 2 + 0.1 + k * ww / 4
            p.box((fx, by, z - wh / 2 - 0.0), (0.26, 0.22, 0.2), LEAVES, rot=0.4 * k)
            p.box((fx + 0.06, by - face * 0.06, z - wh / 2 + 0.1), (0.13, 0.13, 0.13), BLOOMS[(k + int(x * 3)) % len(BLOOMS)], rot=0.7 * k)


def mountain_house(name, seed, w, d, var):
    p = Piece(seed)
    rng = p.rng
    g = 3.0
    u = 2.8
    jet = 0.22
    shutter = SHUTTERS[var % len(SHUTTERS)]
    stone = lambda pt, n: lerp(STONE_LO, STONE_HI, (pt.z + 1.0) / (g + 1.0))
    front = -d / 2

    p.box((0, 0, (g - 1.6) / 2), (w, d, g + 1.6), stone)
    p.box((0, 0, -0.6), (w + 0.3, d + 0.3, 1.4), tuple(c * 0.85 for c in STONE_LO))

    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(5):
                big = k % 2 == 0
                qx = 0.62 if big else 0.4
                qy = 0.4 if big else 0.62
                p.box((sx * (w / 2 - qx / 2 + 0.03), sy * (d / 2 - qy / 2 + 0.03), 0.3 + k * 0.56), (qx, qy, 0.5), QUOIN)

    for k in range(int(w * 1.3)):
        sx = rng.uniform(-w / 2 + 0.5, w / 2 - 0.5)
        sz = rng.uniform(0.3, g - 0.4)
        p.box((sx, front - 0.02, sz), (rng.uniform(0.35, 0.7), 0.06, rng.uniform(0.22, 0.34)), lerp(STONE_LO, QUOIN, rng.uniform(0.1, 0.7)))

    dx = -w / 4 if var != 1 else w / 4
    p.box((dx, front + 0.05, 1.12), (1.25, 0.2, 2.24), DARK)
    p.box((dx, front - 0.02, 1.1), (1.05, 0.08, 2.15), shutter if var == 2 else TIMBER)

    for k in range(4):
        p.box((dx, front - 0.07, 0.35 + k * 0.5), (1.0, 0.03, 0.06), TIMBER_D)

    p.box((dx, front - 0.12, 2.38), (1.75, 0.34, 0.3), QUOIN)

    for s in (-1, 1):
        p.box((dx + s * 0.78, front - 0.1, 1.15), (0.3, 0.3, 2.3), QUOIN)

    p.box((dx + 0.36, front - 0.08, 1.05), (0.08, 0.06, 0.08), IRON)

    for k in range(3):
        p.box((dx, front - 0.35 - k * 0.32, -0.08 - k * 0.32), (1.8 + k * 0.2, 0.34, 0.32), lerp(QUOIN, STONE_LO, k * 0.35))

    p.box((dx - 0.95, front - 0.25, 2.2), (0.06, 0.3, 0.06), IRON)
    p.blob((dx - 0.95, front - 0.42, 2.05), 0.13, GLOW_WARM, sz=1.2, sub=1)

    wx = w / 4 if var != 1 else -w / 4
    window(p, wx, front, 1.5, 0.9, 1.0, -1, shutter, flowers=False)

    if w > 7:
        window(p, -w / 2 + 0.9 if var != 1 else w / 2 - 0.9, front, 1.5, 0.7, 0.9, -1, shutter, open_l=False)

    for s in (-1, 1):
        p.box((s * (w / 2 + 0.05), d / 6, 1.6), (0.12, 0.8, 0.9), DARK)
        p.box((s * (w / 2 + 0.12), d / 6, 1.12), (0.2, 1.05, 0.12), QUOIN)

    p.box((0, 0, g + 0.08), (w + 2 * jet, d + 2 * jet, 0.18), TIMBER_D)

    for k in range(int(w / 0.9)):
        p.box((-w / 2 + 0.45 + k * 0.9, front - jet + 0.05, g - 0.06), (0.16, 0.5, 0.16), TIMBER_D)

    uw = w + 2 * jet
    ud = d + 2 * jet
    p.box((0, 0, g + 0.18 + u / 2), (uw - 0.04, ud - 0.04, u), PLANK_A)
    nb = int(uw / 0.42)

    for k in range(nb):
        x = -uw / 2 + 0.12 + k * uw / nb
        col = PLANK_A if k % 2 else PLANK_B
        p.box((x, -ud / 2 - 0.01, g + 0.18 + u / 2), (uw / nb - 0.02, 0.04, u), col)
        p.box((x, ud / 2 + 0.01, g + 0.18 + u / 2), (uw / nb - 0.02, 0.04, u), col)

    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * (uw / 2 - 0.08), sy * (ud / 2 - 0.08), g + 0.18 + u / 2), (0.2, 0.2, u), TIMBER_D)

    p.box((0, -ud / 2 - 0.04, g + 0.24), (uw, 0.1, 0.12), TIMBER_D)
    p.box((0, -ud / 2 - 0.04, g + 0.18 + u - 0.06), (uw, 0.1, 0.12), TIMBER_D)

    for k in (-1, 1):
        p.span((k * uw / 4 - 0.6, -ud / 2 - 0.05, g + 0.3), (k * uw / 4 + 0.6, -ud / 2 - 0.05, g + 0.18 + u - 0.1), 0.1, 0.06, TIMBER_D)

    uz = g + 0.18 + 1.45
    nwin = 2 if w < 8 else 3

    for i in range(nwin):
        x = -uw / 2 + uw * (i + 0.5) / nwin
        window(p, x, -ud / 2, uz, 0.8, 1.0, -1, shutter, flowers=True, open_l=(i + var) % 2 == 0)

    for s in (-1, 1):
        p.box((s * (uw / 2 + 0.02), 0, uz), (0.1, 0.8, 0.9), DARK)
        p.box((s * (uw / 2 + 0.06), 0, uz + 0.52), (0.12, 1.0, 0.1), TIMBER_D)

    if var != 2:
        bz = g + 0.18
        bd = 1.15
        bw = uw * 0.62
        bx = 0 if var == 0 else uw * 0.12
        p.box((bx, -ud / 2 - bd / 2, bz - 0.02), (bw, bd, 0.14), TIMBER)

        for k in range(3):
            kx = bx - bw / 2 + 0.2 + k * (bw - 0.4) / 2
            p.span((kx, -ud / 2, bz - 0.9), (kx, -ud / 2 - bd + 0.1, bz - 0.08), 0.12, 0.12, TIMBER_D)

        for s in (-1, 1):
            p.box((bx + s * (bw / 2 - 0.05), -ud / 2 - bd / 2, bz + 0.5), (0.1, bd, 0.08), TIMBER_D)

        p.box((bx, -ud / 2 - bd + 0.05, bz + 0.98), (bw, 0.1, 0.1), TIMBER_D)
        p.box((bx, -ud / 2 - bd + 0.05, bz + 0.55), (bw, 0.06, 0.06), TIMBER_D)

        nbal = int(bw / 0.22)

        for k in range(nbal):
            p.box((bx - bw / 2 + 0.11 + k * bw / nbal, -ud / 2 - bd + 0.05, bz + 0.5), (0.05, 0.05, 0.9), TIMBER)

        for k in range(int(bw / 0.7)):
            fx = bx - bw / 2 + 0.35 + k * 0.7
            p.box((fx, -ud / 2 - bd - 0.08, bz + 0.85), (0.5, 0.22, 0.2), POT if k % 2 else TIMBER)
            p.box((fx, -ud / 2 - bd - 0.08, bz + 1.02), (0.32, 0.26, 0.22), LEAVES, rot=0.5 * k)
            p.box((fx + 0.08, -ud / 2 - bd - 0.14, bz + 1.14), (0.14, 0.14, 0.14), BLOOMS[k % len(BLOOMS)], rot=0.8 * k)

    z0 = g + 0.18 + u
    rise = 2.3 if var != 1 else 2.6
    gable_end(p, 0, 0, uw - 0.02, ud - 0.02, z0, rise, PLANK_B)
    gable_roof(p, 0, 0, uw, ud, z0, rise, 0.85, 0.7, SLATE_LO, SLATE_HI, hexc("34383C"))

    cx = uw / 2 - 1.0 if var != 1 else -uw / 2 + 1.0
    p.box((cx, ud / 4, z0 + rise * 0.55), (0.75, 0.75, rise * 1.3), stone)
    p.box((cx, ud / 4, z0 + rise * 1.25), (0.95, 0.95, 0.16), QUOIN)

    for s in (-1, 1):
        p.box((cx + s * 0.22, ud / 4, z0 + rise * 1.36), (0.18, 0.5, 0.2), QUOIN)

    if var == 1:
        sx = uw / 2 + 0.75
        for k in range(10):
            t = k / 9
            p.box((sx, d / 2 - 0.4 - t * (d - 1.2), 0.15 + t * (g - 0.1)), (1.2, 0.42, 0.3 + t * (g - 0.1) * 0 + 0.3), lerp(QUOIN, STONE_LO, 0.3))

        p.box((sx, d / 2 - 0.4 - 0.5 * (d - 1.2), (g + 0.15) / 2 - 0.2), (1.1, d - 1.0, g - 0.6), stone)
        p.box((sx + 0.55, 0, g + 0.55), (0.06, d - 1.0, 0.06), IRON)

        for k in range(6):
            p.box((sx + 0.55, -d / 2 + 0.9 + k * (d - 1.8) / 5, g + 0.3), (0.05, 0.05, 0.5), IRON)

    lx = -uw / 2 + 0.4 if var != 1 else uw / 2 - 0.4
    p.box((lx, -d / 2 - 0.3, 2.6), (0.06, 0.5, 0.06), IRON)
    p.box((lx, -d / 2 - 0.55, 2.4), (0.24, 0.24, 0.3), IRON)
    p.blob((lx, -d / 2 - 0.55, 2.38), 0.1, GLOW_WARM, sz=1.3, sub=1)

    for k in range(3):
        x = rng.uniform(-w / 2 + 0.6, w / 2 - 0.6)
        if abs(x - dx) < 1.2:
            continue
        p.box((x, front - 0.45, 0.25), (0.5, 0.5, 0.5), POT)
        p.box((x, front - 0.45, 0.66), (0.5, 0.5, 0.38), LEAVES, rot=0.6)

    obj = p.finish(name, jitter=0.03, bevel=0.0)

    return ray_ao(obj)


def vl_paving():
    p = Piece(91)
    cols = [hexc("8E887C"), hexc("9A9486"), hexc("847E72"), hexc("A29C8E")]
    n = 5
    s = 4.0 / n

    for i in range(n):
        for j in range(n):
            off = 0.5 * s if j % 2 else 0
            for part in range(2 if j % 2 else 1):
                x0 = -2 + i * s + off - (s if part else 0)
                if x0 < -2 - s / 2 or x0 > 2 - s / 2 + 0.01:
                    continue
                x0c = max(x0, -2)
                x1c = min(x0 + s, 2)
                if x1c - x0c < 0.15:
                    continue
                p.box(((x0c + x1c) / 2, -2 + j * s + s / 2, -0.02), (x1c - x0c - 0.06, s - 0.06, 0.12), p.rng.choice(cols))

    p.box((0, 0, -0.1), (4.0, 4.0, 0.12), hexc("5E5A52"))

    return p.finish("vl_paving", jitter=0.02, ao=False)


def vl_steps():
    p = Piece(92)
    cols = [hexc("9A9486"), hexc("8E887C")]

    for k in range(6):
        p.box((0, -1.5 + k * 0.5 + 0.25 + 0.5 * 0, -0.6 + k * 0.18 + 0.09), (3.0, 3.0 - k * 0.5, 0.18 + 0.0), cols[k % 2])

    for s in (-1, 1):
        p.box((s * 1.65, 0, 0.0), (0.3, 3.0, 1.2), hexc("7E786E"))

    return p.finish("vl_steps", jitter=0.02, bevel=0.02)


def vl_fountain():
    p = Piece(93)
    stone = lambda pt, n: lerp(STONE_LO, QUOIN, (pt.z + 0.2) / 1.6)
    p.cone((0, 0, 0), 2.2, 2.2, 0.7, 10, stone)
    p.cone((0, 0, 0.62), 1.9, 1.9, 0.1, 10, hexc("3FA6A0"))
    p.cone((0, 0, 0), 0.45, 0.35, 1.8, 8, stone)
    p.cone((0, 0, 1.8), 0.9, 0.6, 0.25, 8, stone)
    p.cone((0, 0, 1.98), 0.7, 0.7, 0.05, 8, hexc("3FA6A0"))
    p.cone((0, 0, 2.05), 0.16, 0.1, 0.6, 6, stone)

    return ray_ao(p.finish("vl_fountain", jitter=0.03, bevel=0.03))


THATCH_LO = hexc("9A7A44")
THATCH_HI = hexc("D8BC7E")
BAMBOO = hexc("B8A060")
BAMBOO_D = hexc("8A7440")
ROPE = hexc("C2A878")
CLOTHS = [hexc("D0563E"), hexc("2F8E8A"), hexc("E0A83C"), hexc("B8487A")]


def island_hut():
    p = Piece(13)
    floor = 1.75
    w, d = 4.4, 4.4
    cloth = CLOTHS[0]

    for sx in (-w / 2 + 0.1, 0, w / 2 - 0.1):
        for sy in (-d / 2 + 0.1, d / 2 - 0.1):
            p.cone((sx, sy, -0.3), 0.13, 0.11, floor + 0.3, 7, BAMBOO_D)

    for sy in (-d / 2 + 0.1, d / 2 - 0.1):
        p.span((-w / 2 + 0.1, sy, 0.2), (w / 2 - 0.1, sy, floor - 0.1), 0.06, 0.06, BAMBOO_D)

    deck_d = d + 1.6
    n = 14

    for i in range(n):
        y = -deck_d / 2 + (i + 0.5) * deck_d / n - 0.8
        p.box((0, y, floor + 0.08), (w + 0.4, deck_d / n - 0.04, 0.14), WOOD if i % 3 else WOOD_L, rot=p.rng.uniform(-0.01, 0.01))

    for sy in (-deck_d / 2 - 0.8, d / 2 + 0.1):
        p.box((0, sy + (0.05 if sy > 0 else 0.05), floor - 0.05), (w + 0.5, 0.16, 0.16), WOOD_D)

    py = -d / 2 - 1.45
    for sx in (-w / 2, -w / 4, w / 4, w / 2):
        p.cone((sx, py, floor), 0.07, 0.07, 0.95, 6, BAMBOO)

    for hz in (0.5, 0.92):
        p.cone((-w / 2, py, floor + hz), 0.05, 0.05, w, 6, BAMBOO, rot=0) if False else p.span((-w / 2, py, floor + hz), (-0.6, py, floor + hz), 0.07, 0.07, BAMBOO)
        p.span((0.6, py, floor + hz), (w / 2, py, floor + hz), 0.07, 0.07, BAMBOO)

    top = floor + 0.16
    hgt = 2.2
    wall = lambda pt, n: lerp(hexc("8E7448"), hexc("BFA272"), (pt.z - top) / hgt)

    for side in (-1, 1):
        nb = 18

        for k in range(nb):
            x = -w / 2 + (k + 0.5) * w / nb
            if side == -1 and abs(x) < 0.55:
                continue
            col = BAMBOO if k % 2 else BAMBOO_D
            p.cone((x, side * d / 2, top), 0.11, 0.11, hgt, 6, lambda pt, n, c=col: lerp(tuple(v * 0.8 for v in c), c, (pt.z - top) / hgt))

        for k in range(18):
            y = -d / 2 + (k + 0.5) * d / 18
            if abs(y) < 0.55:
                continue
            col = BAMBOO if k % 2 else BAMBOO_D
            p.cone((side * w / 2, y, top), 0.11, 0.11, hgt, 6, lambda pt, n, c=col: lerp(tuple(v * 0.8 for v in c), c, (pt.z - top) / hgt))

    for side in (-1, 1):
        p.box((side * (w / 2 + 0.04), 0, top + 1.25), (0.08, 1.1, 0.9), DARK)
        p.box((side * (w / 2 + 0.1), 0, top + 0.78), (0.1, 1.3, 0.08), WOOD_D)
        p.box((side * (w / 2 + 0.1), 0, top + 1.72), (0.1, 1.3, 0.08), WOOD_D)

    p.box((0, -d / 2 + 0.04, top + 1.0), (1.1, 0.08, 2.0), DARK)
    p.box((0, -d / 2 - 0.05, top + 2.05), (1.4, 0.12, 0.12), WOOD_D)

    for k in range(5):
        p.box((-0.44 + k * 0.22, -d / 2 - 0.06, top + 1.3), (0.2, 0.03, 1.4 - (k % 2) * 0.2), CLOTHS[(k + 1) % len(CLOTHS)])

    for sx in (-w / 2, w / 2):
        for sy in (-d / 2, d / 2):
            p.cone((sx, sy, top), 0.16, 0.14, hgt + 0.3, 6, WOOD_D)

    rz = top + hgt
    p.box((0, 0, rz + 0.05), (w + 0.4, d + 0.4, 0.14), WOOD_D)

    eave = w / 2 + 0.75
    rr = eave * 1.414
    thatch = lambda pt, n: lerp(THATCH_LO, THATCH_HI, 0.2 + (pt.z - rz) / 3.2)
    p.cone((0, 0, rz - 0.3), rr + 0.25, rr, 0.38, 4, thatch, rot=math.pi / 4)
    p.cone((0, 0, rz + 0.05), rr, 0.35, 3.0, 4, thatch, rot=math.pi / 4)

    for j in range(44):
        t = j / 44
        side = int(t * 4)
        u = t * 4 - side
        corners = [(-eave, -eave), (eave, -eave), (eave, eave), (-eave, eave)]
        a = corners[side]
        b2 = corners[(side + 1) % 4]
        fx = a[0] + (b2[0] - a[0]) * u
        fy = a[1] + (b2[1] - a[1]) * u
        p.box((fx * 1.02, fy * 1.02, rz - 0.36 - p.rng.uniform(0, 0.08)), (0.4, 0.4, 0.22), THATCH_LO, rot=side * math.pi / 2)

    for k in range(3):
        zz = rz + 0.75 + k * 0.75
        kk = 1 - (zz - rz) / 3.05
        p.cone((0, 0, zz), rr * kk + 0.06, rr * kk + 0.02, 0.06, 4, tuple(c * 0.85 for c in THATCH_LO), rot=math.pi / 4)

    p.cone((0, 0, rz + 2.95), 0.5, 0.2, 0.35, 4, WOOD_D, rot=math.pi / 4)
    p.cone((0, 0, rz + 3.25), 0.08, 0.03, 0.6, 5, WOOD_D)

    for sx in (-1, 1):
        lx = sx * (w / 2 + 0.6)
        p.box((lx * 0.94, -d / 2 - 1.0, rz - 0.25), (0.05, 0.05, 0.4), ROPE)
        p.cone((lx * 0.94, -d / 2 - 1.0, rz - 0.75), 0.17, 0.14, 0.32, 6, hexc("C84C2E"))
        p.blob((lx * 0.94, -d / 2 - 1.0, rz - 0.6), 0.12, GLOW_WARM, sz=1.1, sub=1)

    aw = w * 0.7
    for k in range(7):
        x0 = -aw / 2 + k * aw / 7
        p.box((x0 + aw / 14, -d / 2 - 0.8, rz - 0.2 - 0.1 * math.sin(k)), (aw / 7 - 0.02, 1.4, 0.05), CLOTHS[(k // 2) % len(CLOTHS)], rot=0)

    for sx in (-aw / 2, aw / 2):
        p.cone((sx, -d / 2 - 1.5, floor), 0.06, 0.06, rz - floor - 0.15, 6, BAMBOO_D)

    for sx in (-0.45, 0.45):
        p.span((sx, -d / 2 - 1.6 - 1.7, -0.1), (sx, -d / 2 - 1.55, floor + 0.12), 0.1, 0.12, BAMBOO_D)

    for k in range(5):
        t = (k + 0.5) / 5
        p.box((0, -d / 2 - 3.3 + 1.7 * t, (floor + 0.2) * t), (0.95, 0.16, 0.07), WOOD)

    for j, (bx, by) in enumerate([(-w / 2 - 0.4, d / 2 - 0.4), (w / 2 + 0.35, -0.6)]):
        p.cone((bx, by, floor + 0.15), 0.25, 0.3, 0.5, 8, hexc("A8603E"))
        p.blob((bx, by, floor + 0.85), 0.42, LEAVES, sz=0.9, sub=1)
        p.blob((bx + 0.1, by - 0.2, floor + 1.05), 0.14, BLOOMS[j], sz=0.9, sub=1)

    return ray_ao(p.finish("iv_hut", jitter=0.03, bevel=0.015), strength=0.25)


def rope_bridge():
    p = Piece(19)

    for i in range(10):
        x = -2 + i * 0.4 + 0.2
        p.box((x, p.rng.uniform(-0.04, 0.04), p.rng.uniform(-0.02, 0.02)), (0.34, 2.0 + p.rng.uniform(-0.1, 0.1), 0.08), WOOD if i % 2 else WOOD_L, rot=p.rng.uniform(-0.04, 0.04))

    for s in (-1, 1):
        p.box((0, s * 0.85, -0.1), (4.0, 0.12, 0.12), WOOD_D)
        p.cone((-2.0, s * 1.15, -0.2), 0.09, 0.07, 1.4, 6, BAMBOO_D)
        p.span((-2.0, s * 1.15, 1.15), (0, s * 1.15, 0.95), 0.05, 0.05, ROPE)
        p.span((0, s * 1.15, 0.95), (2.0, s * 1.15, 1.15), 0.05, 0.05, ROPE)
        p.span((-2.0, s * 1.15, 0.6), (0, s * 1.15, 0.45), 0.035, 0.035, ROPE)
        p.span((0, s * 1.15, 0.45), (2.0, s * 1.15, 0.6), 0.035, 0.035, ROPE)

        for k in range(5):
            x = -1.6 + k * 0.8
            hz = 1.12 - 0.2 * (1 - (x / 2) ** 2)
            p.span((x, s * 1.15, hz), (x, s * 0.88, 0.0), 0.025, 0.025, ROPE)

    p.cone((-2.0, 1.15, 1.2), 0.0, 0.0, 0.0, 4, ROPE) if False else None
    p.box((-1.98, -1.15, 1.32), (0.04, 0.04, 0.3), ROPE)
    p.cone((-1.98, -1.15, 1.0), 0.13, 0.1, 0.24, 6, hexc("C84C2E"))
    p.blob((-1.98, -1.15, 1.12), 0.09, GLOW_WARM, sz=1.1, sub=1)

    return ray_ao(p.finish("iv_bridge", jitter=0.03, bevel=0.012), strength=0.2)


def island_dock():
    p = Piece(23)

    for i in range(16):
        y = -4 + i * 0.5 + 0.25
        p.box((0, y, 0), (2.4, 0.46, 0.12), WOOD if i % 2 else WOOD_L, rot=p.rng.uniform(-0.02, 0.02))

    for sx in (-1.1, 1.1):
        p.box((sx, 0, -0.15), (0.16, 8.0, 0.16), WOOD_D)

        for sy in (-3.8, -1.3, 1.3, 3.8):
            p.cone((sx, sy, -2.5), 0.12, 0.11, 3.2, 7, BAMBOO_D)

    for sy in (-3.8, 3.8):
        for sx in (-1.1, 1.1):
            p.span((sx, sy, 0.7), (sx, sy, 0.7), 0.01, 0.01, ROPE) if False else None

    p.cone((1.1, 3.8, 0.0), 0.12, 0.11, 1.3, 7, BAMBOO_D)
    p.box((1.1, 3.8, 1.45), (0.04, 0.04, 0.3), ROPE)
    p.cone((1.1, 3.8, 1.12), 0.15, 0.12, 0.28, 6, hexc("C84C2E"))
    p.blob((1.1, 3.8, 1.26), 0.1, GLOW_WARM, sz=1.1, sub=1)

    for j in range(3):
        p.cone((-0.5 + j * 0.45, 2.6, 0.06), 0.18, 0.16, 0.4, 8, WOOD if j % 2 else hexc("A8603E"))

    p.span((-0.9, -2.2, 0.08), (0.6, -3.4, 0.08), 0.06, 0.06, ROPE)

    return ray_ao(p.finish("iv_dock", jitter=0.03, bevel=0.012), strength=0.2)


def island_lantern():
    p = Piece(29)
    p.cone((0, 0, 0), 0.12, 0.09, 2.6, 7, BAMBOO_D)
    p.span((0, 0, 2.45), (0.55, 0, 2.5), 0.06, 0.06, BAMBOO_D)
    p.box((0.55, 0, 2.3), (0.03, 0.03, 0.3), ROPE)
    p.cone((0.55, 0, 1.82), 0.2, 0.16, 0.36, 7, hexc("C84C2E"))
    p.cone((0.55, 0, 2.16), 0.12, 0.04, 0.12, 7, hexc("8A3020"))
    p.blob((0.55, 0, 1.98), 0.13, GLOW_WARM, sz=1.1, sub=1)
    p.cone((0, 0, 0), 0.35, 0.3, 0.14, 7, hexc("8E887C"))

    return p.finish("iv_lantern", jitter=0.03, bevel=0.01, glow=0.0)


def island_clothline():
    p = Piece(31)

    for x in (-3.0, 3.0):
        p.cone((x, 0, 0), 0.09, 0.07, 3.0, 7, BAMBOO_D)

    p.span((-3.0, 0, 2.85), (0, 0, 2.55), 0.03, 0.03, ROPE)
    p.span((0, 0, 2.55), (3.0, 0, 2.85), 0.03, 0.03, ROPE)

    for k in range(9):
        x = -2.6 + k * 0.65
        sag = 2.55 + 0.3 * (x / 3.0) ** 2
        p.box((x, 0, sag - 0.32), (0.42, 0.03, 0.55 + 0.12 * (k % 2)), CLOTHS[k % len(CLOTHS)], rot=0.12 * math.sin(k * 1.7))

    return p.finish("iv_clothline", jitter=0.03, bevel=0.005)


def island_boardwalk():
    p = Piece(37)

    for i in range(6):
        y = -1.25 + i * 0.5 + 0.25
        p.box((p.rng.uniform(-0.04, 0.04), y, 0.06), (1.5 + p.rng.uniform(-0.08, 0.08), 0.44, 0.08), WOOD if i % 2 else WOOD_L, rot=p.rng.uniform(-0.03, 0.03))

    for sx in (-0.6, 0.6):
        p.box((sx, 0, -0.02), (0.1, 2.6, 0.1), BAMBOO_D)

    return p.finish("iv_boardwalk", jitter=0.03, ao=False)


OLIVE_LO = hexc("4F543C")
OLIVE_HI = hexc("6E7452")
CONC = hexc("9A978E")
CONC_D = hexc("6C6A64")
CORR = hexc("8C9094")
CORR_D = hexc("6A6E72")
HAZARD = hexc("C9A23A")
GLASS_D = hexc("2C3440")


def barracks():
    p = Piece(61)
    w, d, h = 14.0, 6.4, 3.2
    wall = lambda pt, n: lerp(OLIVE_LO, OLIVE_HI, (pt.z - 0.5) / h)
    p.box((0, 0, 0.25), (w + 0.6, d + 0.6, 0.5), CONC_D)

    for k in range(int(w / 0.5)):
        x = -w / 2 + 0.25 + k * 0.5
        for side in (-1, 1):
            p.box((x, side * d / 2, 0.5 + h / 2), (0.48, 0.12, h), wall)

    for k in range(int(d / 0.5)):
        y = -d / 2 + 0.25 + k * 0.5
        for side in (-1, 1):
            p.box((side * w / 2, y, 0.5 + h / 2), (0.12, 0.48, h), wall)

    p.box((0, 0, 0.5 + h / 2), (w - 0.1, d - 0.1, h - 0.05), wall)

    for k in range(5):
        x = -w / 2 + 1.6 + k * (w - 3.2) / 4
        if k == 2:
            continue
        for side in (-1, 1):
            y = side * (d / 2 + 0.05)
            p.box((x, y, 2.3), (1.3, 0.1, 1.0), GLASS_D)
            p.box((x, y + side * 0.06, 1.75), (1.6, 0.18, 0.12), CONC)
            p.box((x, y + side * 0.06, 2.84), (1.6, 0.16, 0.12), CONC_D)
            for sx in (-1, 1):
                p.box((x + sx * 0.72, y + side * 0.06, 2.3), (0.12, 0.16, 1.1), CONC_D)
            p.box((x, y + side * 0.07, 2.3), (0.06, 0.08, 1.0), CONC_D)

    for side in (-1, 1):
        y = side * (d / 2 + 0.05)
        p.box((0, y, 1.6), (1.3, 0.12, 2.2), hexc("3E4A3A"))
        p.box((0, y + side * 0.08, 2.8), (1.7, 0.18, 0.16), CONC_D)
        for sx in (-1, 1):
            p.box((sx * 0.72, y + side * 0.08, 1.6), (0.14, 0.18, 2.3), CONC_D)
        for k in range(3):
            p.box((0, y + side * (0.45 + k * 0.32), 0.42 - k * 0.14), (1.9, 0.32, 0.16), CONC)
        p.box((0, y + side * 1.1, 3.25), (2.4, 2.2, 0.08), CORR_D)
        for sx in (-1.05, 1.05):
            p.box((sx, y + side * 2.1, 1.85), (0.08, 0.08, 2.8), IRON)
        p.box((0.55, y + side * 0.1, 3.0), (0.3, 0.16, 0.18), IRON)
        p.blob((0.55, y + side * 0.2, 2.93), 0.08, GLOW_WARM, sz=1.0, sub=1)

    rz = 0.5 + h
    pitch = 0.18
    for side in (-1, 1):
        for k in range(int((w + 0.8) / 0.32)):
            x = -w / 2 - 0.4 + k * 0.32 + 0.16
            col = CORR if k % 2 else CORR_D
            m = Matrix.Translation(Vector((x, side * (d / 4 + 0.2), rz + 0.32 - 0.0))) @ Matrix.Rotation(-side * pitch, 4, "X") @ Matrix.Diagonal((0.3, d / 2 + 0.6, 0.06 + 0.04 * (k % 2), 1))
            r = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
            p.tag(r["verts"], col)
    p.box((0, 0, rz + 0.62), (w + 0.9, 0.3, 0.14), CORR_D)
    for e in (-1, 1):
        a = p.bm.verts.new((e * w / 2, -d / 2, rz))
        b2 = p.bm.verts.new((e * w / 2, d / 2, rz))
        c = p.bm.verts.new((e * w / 2, 0, rz + 0.6))
        p.face([a, b2, c] if e > 0 else [c, b2, a], OLIVE_LO)

    for sx in (-w / 2 + 1.2, w / 2 - 1.2):
        p.box((sx, d / 2 + 0.45, 1.4), (0.9, 0.7, 0.7), CORR)
        p.box((sx, d / 2 + 0.81, 1.4), (0.6, 0.04, 0.5), CORR_D)

    sx0 = w / 2 + 0.07
    p.box((sx0, -1.5, 2.3), (0.06, 1.5, 1.0), CONC_D)
    p.box((sx0 + 0.02, -1.5, 2.3), (0.05, 1.36, 0.86), hexc("E6E2D6"))

    for k in range(5):
        p.box((sx0 + 0.04, -2.1 + k * 0.3, 1.97), (0.04, 0.14, 0.12), HAZARD if k % 2 == 0 else hexc("2E2E30"), rot=0)

    tri = [(sx0 + 0.05, -1.5, 2.72), (sx0 + 0.05, -1.78, 2.22), (sx0 + 0.05, -1.22, 2.22)]
    a = p.bm.verts.new(tri[0])
    b2 = p.bm.verts.new(tri[1])
    c = p.bm.verts.new(tri[2])
    p.face([a, b2, c], HAZARD)
    p.box((sx0 + 0.06, -1.5, 2.43), (0.03, 0.05, 0.2), hexc("2E2E30"))
    p.box((sx0 + 0.06, -1.5, 2.28), (0.03, 0.05, 0.05), hexc("2E2E30"))
    p.box((-w / 2 - 0.2, 1.6, 0.9), (0.22, 0.22, 1.8), CONC_D)
    p.cone((-w / 2 + 0.3, -d / 2 - 0.5, 0.5), 0.35, 0.35, 0.9, 8, hexc("5E6A48"))
    p.cone((-w / 2 + 1.0, -d / 2 - 0.5, 0.5), 0.35, 0.35, 0.9, 8, hexc("5E6A48"))

    return ray_ao(p.finish("mil_barracks", jitter=0.03, bevel=0.0), strength=0.22)


def comms():
    p = Piece(63)
    hgt = 16.0
    p.box((0, 0, 0.2), (3.2, 3.2, 0.4), CONC)

    for sx in (-1, 1):
        for sy in (-1, 1):
            p.span((sx * 1.2, sy * 1.2, 0.4), (sx * 0.35, sy * 0.35, hgt), 0.1, 0.1, CORR_D)

    for k in range(9):
        z0 = 0.4 + k * (hgt - 0.4) / 9
        z1 = 0.4 + (k + 1) * (hgt - 0.4) / 9
        s0 = 1.2 - (1.2 - 0.35) * (z0 - 0.4) / (hgt - 0.4)
        s1 = 1.2 - (1.2 - 0.35) * (z1 - 0.4) / (hgt - 0.4)
        for (ax, ay, bx, by) in [(-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)]:
            p.span((ax * s0, ay * s0, z0), (bx * s1, by * s1, z1), 0.05, 0.05, CORR)
            p.span((ax * s0, ay * s0, z0), (bx * s0, by * s0, z0), 0.05, 0.05, CORR)

    p.cone((0, 0, hgt), 0.06, 0.04, 3.0, 6, CORR_D)
    p.blob((0, 0, hgt + 3.0), 0.1, hexc("FF5040"), sz=1.0, sub=1)

    for (z, yaw) in [(11.0, 0.4), (13.5, 2.6)]:
        cx = math.cos(yaw) * 0.9
        cy = math.sin(yaw) * 0.9
        m = Matrix.Translation(Vector((cx, cy, z))) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
        r = bmesh.ops.create_cone(p.bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.75, radius2=0.2, depth=0.35, matrix=m)
        p.tag(r["verts"], hexc("D8D6CE"))

    for z in (6.0, 9.0):
        for yaw in (0.0, 2.1, 4.2):
            p.box((math.cos(yaw) * 0.8, math.sin(yaw) * 0.8, z), (0.18, 0.4, 1.4), hexc("C8C6BE"), rot=yaw)

    p.box((2.2, 0, 1.1), (1.6, 1.4, 1.4), OLIVE_HI)
    p.box((2.2, 0, 1.86), (1.8, 1.6, 0.1), CORR_D)
    p.box((2.2, -0.71, 1.0), (0.7, 0.04, 1.1), OLIVE_LO)

    return ray_ao(p.finish("mil_comms", jitter=0.03, bevel=0.0), strength=0.2)


PAINT = [hexc("D8CFB8"), hexc("C9B18A"), hexc("B8C4B0"), hexc("D6B79A"), hexc("BFC7CC")]
AWN = [hexc("C2563E"), hexc("2F7E78"), hexc("D49A3A"), hexc("5A6E9A")]


def hangar_doors():
    p = Piece(67)

    for side in (-1, 1):
        zc = side * 7.2
        p.box((0, zc, 3.4), (0.3, 5.4, 6.8), CORR_D)

        for k in range(18):
            p.box((-0.18, zc - 2.55 + k * 0.3, 3.4), (0.06, 0.16, 6.6), CORR if k % 2 else CORR_D)

        p.box((-0.2, zc, 6.85), (0.4, 5.6, 0.2), CONC_D)
        p.box((-0.2, zc, 0.1), (0.4, 5.6, 0.2), CONC_D)
        p.box((-0.24, zc, 2.6), (0.08, 5.0, 0.6), HAZARD)

        for k in range(5):
            p.box((-0.27, zc - 2.0 + k * 1.0, 2.6), (0.06, 0.4, 0.62), hexc("2E2E30"))

    p.box((0.1, 0, 7.15), (0.5, 20.2, 0.3), IRON)

    return ray_ao(p.finish("mil_hangar_doors", jitter=0.03, bevel=0.0), strength=0.18)


def sv_shop(name, seed, w, d, h, col, awn):
    p = Piece(seed)
    col = tuple(min(1.0, c * 1.12) for c in col)
    wall = lambda pt, n: lerp(tuple(c * 0.96 for c in col), col, (pt.z) / h)
    p.box((0, 0, 0.15), (w + 0.4, d + 0.4, 0.3), CONC_D)
    p.box((0, 0, h / 2 + 0.3), (w, d, h), wall)
    p.box((0, -d / 2 - 0.02, 0.62), (w + 0.05, 0.1, 0.6), tuple(c * 0.7 for c in col))
    p.box((0, 0, h + 0.45), (w + 0.25, d + 0.25, 0.3), CONC)

    for sx in (-1, 1):
        p.box((sx * (w / 2 - 0.2), -d / 2 - 0.08, h / 2 + 0.3), (0.3, 0.2, h), CONC)

    sw = w * 0.62
    p.box((-w * 0.12, -d / 2 + 0.03, 1.55), (sw, 0.1, 2.3), GLASS_D)

    for k in range(int(sw / 0.25)):
        p.box((-w * 0.12 - sw / 2 + 0.12 + k * 0.25, -d / 2 - 0.02, 2.4), (0.22, 0.05, 0.75), CORR if k % 2 else CORR_D)

    for k in range(4):
        p.box((-w * 0.12 - sw / 2 + k * sw / 3, -d / 2 - 0.04, 1.55), (0.1, 0.12, 2.3), CONC_D)

    p.box((w * 0.36, -d / 2 + 0.03, 1.2), (0.95, 0.1, 2.0), hexc("4A3A2E"))
    p.box((w * 0.36, -d / 2 - 0.04, 2.28), (1.2, 0.12, 0.14), CONC_D)
    p.box((-w * 0.12, -d / 2 - 0.08, h - 0.15), (sw + 0.4, 0.12, 0.6), awn)
    p.box((-w * 0.12, -d / 2 - 0.1, h - 0.15), (sw - 0.2, 0.12, 0.36), hexc("EDE6D4"))

    for k in range(7):
        x0 = -w * 0.12 - sw / 2 + k * sw / 7
        m = Matrix.Translation(Vector((x0 + sw / 14, -d / 2 - 0.8, h - 0.65))) @ Matrix.Rotation(-0.35, 4, "X") @ Matrix.Diagonal((sw / 7 - 0.02, 1.6, 0.05, 1))
        r = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
        p.tag(r["verts"], awn if k % 2 else hexc("EDE6D4"))

    for k in range(7):
        x0 = -w * 0.12 - sw / 2 + k * sw / 7 + sw / 14
        p.box((x0, -d / 2 - 1.55, h - 0.98), (sw / 7 - 0.04, 0.04, 0.2), awn if k % 2 else hexc("EDE6D4"))

    p.box((w / 2 - 1.0, d / 4, h + 0.95), (1.1, 0.9, 0.7), CORR)
    p.cone((-w / 2 + 1.2, d / 4, h + 0.6), 0.6, 0.6, 1.2, 10, hexc("4F6A7A"))
    p.box((w / 2 + 0.25, 0.4, 2.2), (0.5, 0.8, 0.6), CORR)

    for k in range(3):
        p.box((-w / 2 + 0.6 + k * 0.6, -d / 2 - 0.9, 0.55), (0.45, 0.45, 0.5), hexc("8A6440") if k % 2 else hexc("A88A55"))

    p.box((w * 0.36 + 0.75, -d / 2 - 0.1, 2.45), (0.05, 0.3, 0.05), IRON)
    p.blob((w * 0.36 + 0.75, -d / 2 - 0.3, 2.35), 0.09, GLOW_WARM, sz=1.0, sub=1)

    return ray_ao(p.finish(name, jitter=0.02, bevel=0.0, under=0.9, ao=False), strength=0.08)


def sv_shed():
    p = Piece(71)
    w, d, h = 10.0, 7.0, 3.6
    p.box((0, 0, 0.15), (w + 0.4, d + 0.4, 0.3), CONC_D)

    for side in (-1, 1):
        for k in range(int(w / 0.3)):
            p.box((-w / 2 + 0.15 + k * 0.3, side * d / 2, h / 2 + 0.3), (0.28, 0.08 + 0.04 * (k % 2), h), CORR if k % 2 else CORR_D)

    for side in (-1, 1):
        for k in range(int(d / 0.3)):
            p.box((side * w / 2, -d / 2 + 0.15 + k * 0.3, h / 2 + 0.3), (0.08 + 0.04 * (k % 2), 0.28, h), CORR if k % 2 else CORR_D)

    p.box((0, 0, h / 2 + 0.3), (w - 0.1, d - 0.1, h - 0.05), CORR_D)
    p.box((-1.5, -d / 2 - 0.04, 1.65), (3.2, 0.1, 2.7), hexc("6E3A2E"))

    for k in range(9):
        p.box((-1.5, -d / 2 - 0.1, 0.5 + k * 0.3), (3.1, 0.04, 0.06), hexc("8A4A38"))

    p.box((2.8, -d / 2 - 0.02, 2.2), (1.4, 0.08, 0.9), GLASS_D)

    for side in (-1, 1):
        m = Matrix.Translation(Vector((0, side * (d / 4 + 0.15), h + 0.55))) @ Matrix.Rotation(-side * 0.22, 4, "X") @ Matrix.Diagonal((w + 0.7, d / 2 + 0.5, 0.08, 1))
        r = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
        p.tag(r["verts"], hexc("8E5A40"))

    p.box((0, 0, h + 0.88), (w + 0.8, 0.3, 0.12), CORR_D)
    p.cone((w / 2 + 0.6, d / 2 - 1.0, 0.3), 0.7, 0.7, 1.6, 10, hexc("3F6A5C"))

    return ray_ao(p.finish("sv_shed", jitter=0.02, bevel=0.0, under=0.9, ao=False), strength=0.08)


def sv_watertower():
    p = Piece(73)
    hgt = 9.0

    for sx in (-1, 1):
        for sy in (-1, 1):
            p.span((sx * 2.2, sy * 2.2, 0), (sx * 1.6, sy * 1.6, hgt), 0.18, 0.18, IRON)

    for z in (2.5, 5.5):
        s0 = 2.2 - 0.6 * z / hgt
        for (ax, ay, bx, by) in [(-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)]:
            p.span((ax * s0, ay * s0, z), (bx * s0, by * s0, z), 0.08, 0.08, IRON)
            p.span((ax * s0, ay * s0, z - 2.5), (bx * s0, by * s0, z), 0.05, 0.05, IRON)

    p.cone((0, 0, hgt), 2.6, 2.6, 3.2, 14, lambda pt, n: lerp(hexc("6E8A9A"), hexc("9AB4C0"), (pt.z - hgt) / 3.2))
    p.cone((0, 0, hgt + 3.2), 2.7, 0.3, 1.1, 14, hexc("5A6E7A"))

    for k in range(3):
        p.cone((0, 0, hgt + 0.5 + k * 1.1), 2.66, 2.66, 0.08, 14, hexc("4E606C"))

    p.box((0, -2.7, hgt + 0.2), (5.8, 0.5, 0.1), IRON)

    for k in range(10):
        p.box((-2.6 + k * 0.58, -2.95, hgt + 0.7), (0.04, 0.04, 1.0), IRON)

    p.box((0, -2.95, hgt + 1.2), (5.8, 0.05, 0.05), IRON)

    for k in range(16):
        p.box((2.4, -1.9, 0.3 + k * 0.56), (0.5, 0.06, 0.05), IRON)

    for sx in (-0.25, 0.25):
        p.box((2.4 + sx, -1.9, hgt / 2), (0.05, 0.05, hgt), IRON)

    return ray_ao(p.finish("sv_watertower", jitter=0.03, bevel=0.0), strength=0.15)


def sv_fuel():
    p = Piece(79)
    p.box((0, 0, 0.08), (14.0, 9.0, 0.16), CONC)

    for sx in (-4.5, 4.5):
        for sy in (-2.2, 2.2):
            p.box((sx, sy, 2.6), (0.4, 0.4, 5.0), CONC)

    p.box((0, 0, 5.3), (13.0, 7.0, 0.6), hexc("E6E2D6"))
    p.box((0, -3.52, 5.3), (13.0, 0.06, 0.6), AWN[0])
    p.box((0, 3.52, 5.3), (13.0, 0.06, 0.6), AWN[0])
    p.box((0, 0, 4.98), (12.6, 6.6, 0.04), hexc("C8C4B8"))

    for k in range(4):
        p.box((-4.5 + k * 3, 0, 4.95), (1.6, 0.5, 0.06), GLOW_WARM)

    for sx in (-3.0, 3.0):
        p.box((sx, 0, 0.35), (2.6, 1.0, 0.4), CONC_D)
        p.box((sx, 0, 1.25), (0.9, 0.6, 1.6), hexc("D8D2C4"))
        p.box((sx, -0.32, 1.45), (0.6, 0.04, 0.5), GLASS_D)
        p.box((sx, 0, 2.15), (1.0, 0.7, 0.2), AWN[0])
        p.box((sx + 0.5, -0.32, 0.9), (0.08, 0.1, 0.5), IRON)

    p.box((0, 6.5, 1.75), (8.0, 4.0, 3.5), lambda pt, n: lerp(hexc("C8C0AC"), hexc("DED6C2"), pt.z / 3.5))
    p.box((0, 4.48, 1.4), (5.0, 0.06, 2.0), GLASS_D)
    p.box((0, 4.44, 3.0), (8.2, 0.12, 0.7), AWN[0])
    p.box((0, 4.42, 3.0), (6.0, 0.12, 0.36), hexc("EDE6D4"))
    p.box((0, 6.5, 3.6), (8.3, 4.3, 0.2), CONC)
    p.box((-6.6, -4.2, 3.5), (0.3, 0.3, 7.0), CONC_D)
    p.box((-6.6, -4.2, 6.6), (1.8, 0.3, 1.8), hexc("E6E2D6"))
    p.box((-6.6, -4.36, 6.6), (1.5, 0.04, 1.5), AWN[0])

    return ray_ao(p.finish("sv_fuel", jitter=0.03, bevel=0.0), strength=0.18)


def hangar_lamps():
    p = Piece(87)

    for row in (-4.5, 0.0, 4.5):
        for k in range(6):
            x = -11 + k * 4.4
            p.box((x, row, 0), (2.6, 0.35, 0.12), hexc("FFF2D0"))

    for row in (-8.6, 8.6):
        p.box((0, row, -4.5), (26.0, 0.16, 0.3), hexc("FFE6B0"))
        p.box((0, row * 0.97, -6.8), (26.0, 0.12, 0.22), hexc("FFE6B0"))

    for k in range(4):
        z = -6.0 + k * 4.0
        p.box((13.3, z, -4.0), (0.12, 2.8, 1.4), hexc("FFF4DC"))

    p.box((13.3, 0, -1.6), (0.12, 10.0, 0.3), hexc("FFE6B0"))

    return p.finish("mil_hangar_lamps", jitter=0.0, ao=False, glow=0.95)


def bench():
    p = Piece(89)

    for k in range(3):
        p.box((0, -0.25 + k * 0.25, 0.45), (1.8, 0.2, 0.05), WOOD if k % 2 else WOOD_L)

    p.box((0, 0.32, 0.8), (1.8, 0.06, 0.4), WOOD)

    for sx in (-0.75, 0.75):
        p.box((sx, 0, 0.22), (0.08, 0.6, 0.44), IRON)
        p.box((sx, 0.32, 0.62), (0.08, 0.06, 0.4), IRON)

    return p.finish("sv_bench", jitter=0.03)


def hangar_lining():
    p = Piece(91)
    segs = 18
    L = 27.4
    rx, rz = 9.35, 9.7
    pts = [(math.cos(math.pi * k / segs) * rx, math.sin(math.pi * k / segs) * rz) for k in range(segs + 1)]

    for k in range(segs):
        (y0, z0), (y1, z1) = pts[k], pts[k + 1]
        col = lerp(hexc("8C8A82"), hexc("C8C4B8"), (z0 + z1) / 2 / rz)
        a = p.bm.verts.new((-L / 2, y0, z0))
        b2 = p.bm.verts.new((L / 2, y0, z0))
        c = p.bm.verts.new((L / 2, y1, z1))
        d = p.bm.verts.new((-L / 2, y1, z1))
        p.face([a, b2, c, d], col)

    for k in range(7):
        x = -L / 2 + 1.0 + k * (L - 2.0) / 6
        for j in range(segs):
            (y0, z0), (y1, z1) = pts[j], pts[j + 1]
            p.span((x, y0 * 0.985, z0 * 0.985), (x, y1 * 0.985, z1 * 0.985), 0.18, 0.18, hexc("6A6862"))

    for (y0, z0), (y1, z1) in [(pts[k], pts[k + 1]) for k in range(segs)]:
        pass

    b0 = p.bm.verts.new((L / 2 - 0.05, -rx, 0))
    b1 = p.bm.verts.new((L / 2 - 0.05, rx, 0))
    top = [p.bm.verts.new((L / 2 - 0.05, y, z)) for (y, z) in pts]
    p.face([b0] + top[::-1][:-1] + [b1] if False else top[::-1], hexc("B8B4A8"))

    return p.finish("mil_hangar_lining", jitter=0.0, ao=False)


PANEL = hexc("D6D4CE")
PANEL_D = hexc("B8B6B0")
TEAL = hexc("2F7E7A")


def fc_office():
    p = Piece(101)
    w, d = 12.6, 10.6
    fl = 3.6
    p.box((0, 0, 0.15), (w + 0.6, d + 0.6, 0.3), CONC_D)

    for f in range(2):
        z0 = 0.3 + f * fl
        p.box((0, 0, z0 + fl / 2), (w, d, fl), lambda pt, n: lerp(PANEL_D, PANEL, 0.4 + (pt.z) / 9))
        p.box((0, 0, z0 + 0.45), (w + 0.12, d + 0.12, 0.9), PANEL_D)

        for side in (-1, 1):
            p.box((0, side * (d / 2 + 0.03), z0 + 2.05), (w - 0.8, 0.08, 1.4), GLASS_D)
            for k in range(9):
                p.box((-w / 2 + 0.4 + k * (w - 0.8) / 8, side * (d / 2 + 0.08), z0 + 2.05), (0.1, 0.12, 1.5), CONC_D)
            p.box((0, side * (d / 2 + 0.1), z0 + 1.3), (w - 0.6, 0.16, 0.1), CONC_D)
            p.box((0, side * (d / 2 + 0.1), z0 + 2.8), (w - 0.6, 0.16, 0.1), CONC_D)

        for side in (-1, 1):
            p.box((side * (w / 2 + 0.03), 0, z0 + 2.05), (0.08, d - 1.2, 1.4), GLASS_D)
            for k in range(7):
                p.box((side * (w / 2 + 0.08), -d / 2 + 0.6 + k * (d - 1.2) / 6, z0 + 2.05), (0.12, 0.1, 1.5), CONC_D)

    p.box((0, 0, 0.3 + 2 * fl + 0.2), (w + 0.3, d + 0.3, 0.4), CONC)

    for sx in (-1, 1):
        p.box((sx * (w / 2 - 0.4), 0, 0.3 + fl), (0.5, d + 0.2, 2 * fl), TEAL)

    rz = 0.3 + 2 * fl + 0.4
    for (ax, ay) in [(-3.5, -2.5), (-1.0, -2.5), (1.5, -2.5)]:
        p.box((ax, ay, rz + 0.55), (1.6, 1.3, 1.1), CORR)
        p.box((ax, ay - 0.66, rz + 0.55), (1.2, 0.04, 0.8), CORR_D)
        p.cone((ax, ay, rz + 1.1), 0.45, 0.45, 0.06, 12, hexc("3A3A3E"))

    p.box((3.8, 2.0, rz + 1.2), (2.4, 2.4, 2.4), PANEL_D)
    p.box((4.6, -3.0, rz + 0.15), (0.6, 0.6, 3.0), CORR_D)

    p.box((0, -d / 2 - 0.25, rz + 1.1), (6.0, 0.14, 1.4), TEAL)
    p.box((0, -d / 2 - 0.32, rz + 1.1), (5.4, 0.04, 0.9), hexc("E6E2D6"))
    for k in range(4):
        p.box((-2.0 + k * 1.3, -d / 2 - 0.36, rz + 1.1), (0.9, 0.03, 0.45), TEAL if k % 2 else HAZARD)
    for sx in (-2.6, 2.6):
        p.box((sx, -d / 2 - 0.25, rz + 0.2), (0.12, 0.12, 0.6), IRON)

    p.box((0, -d / 2 - 1.4, 3.3), (4.2, 2.8, 0.18), CONC)
    for sx in (-1.9, 1.9):
        p.box((sx, -d / 2 - 2.6, 1.8), (0.16, 0.16, 3.0), IRON)
    p.box((0, -d / 2 + 0.02, 1.5), (2.2, 0.1, 2.4), GLASS_D)
    p.box((0, -d / 2 - 0.05, 1.5), (0.08, 0.12, 2.4), CONC_D)
    for k in range(3):
        p.box((0, -d / 2 - 0.5 - k * 0.32, 0.25 - k * 0.1), (3.0, 0.32, 0.12), CONC)

    for (sx, sy) in [(w / 2 + 0.3, 2.0), (w / 2 + 0.3, -1.0), (-w / 2 - 0.3, 1.0)]:
        p.box((sx, sy, 4.6), (0.6, 0.9, 0.7), CORR)
        p.box((sx * 1.04, sy, 4.6), (0.04, 0.6, 0.5), CORR_D)

    p.box((-w / 2 - 0.15, -2.5, 3.6), (0.2, 0.2, 7.0), CORR_D)
    p.box((-w / 2 - 0.15, 3.5, 3.6), (0.2, 0.2, 7.0), CORR_D)

    for (lx, ly) in [(-w / 2 + 0.8, -d / 2 - 0.12), (w / 2 - 0.8, -d / 2 - 0.12)]:
        p.box((lx, ly, 3.0), (0.4, 0.24, 0.16), IRON)
        p.blob((lx, ly - 0.08, 2.92), 0.1, GLOW_WARM, sz=1.0, sub=1)

    return ray_ao(p.finish("fc_office", jitter=0.02, bevel=0.0, under=0.9, ao=False), strength=0.1)


def fc_workshop():
    p = Piece(103)
    w, d, h = 13.6, 10.0, 5.2
    p.box((0, 0, 0.15), (w + 0.6, d + 0.6, 0.3), CONC_D)
    p.box((0, 0, 0.3 + h / 2), (w, d, h), lambda pt, n: lerp(PANEL_D, PANEL, (pt.z) / h))

    for side in (-1, 1):
        for k in range(int(w / 0.35)):
            p.box((-w / 2 + 0.17 + k * 0.35, side * (d / 2 + 0.03), 0.3 + h / 2 + 0.8), (0.3, 0.06, h - 1.6), PANEL if k % 2 else PANEL_D)

    p.box((0, -d / 2 - 0.02, 0.9), (w + 0.05, 0.12, 1.2), CONC)

    for dx in (-3.2, 3.2):
        p.box((dx, -d / 2 - 0.06, 2.3), (4.0, 0.12, 4.0), hexc("8E949A"))
        for k in range(13):
            p.box((dx, -d / 2 - 0.12, 0.45 + k * 0.3), (3.9, 0.04, 0.06), hexc("A8AEB4"))
        p.box((dx, -d / 2 - 0.12, 4.45), (4.4, 0.24, 0.4), CONC_D)
        for sx in (-2.1, 2.1):
            p.box((dx + sx, -d / 2 - 0.14, 2.3), (0.14, 0.2, 4.0), HAZARD)
            for k in range(6):
                p.box((dx + sx, -d / 2 - 0.25, 0.5 + k * 0.7), (0.15, 0.03, 0.3), hexc("2E2E30"))

    for k in range(4):
        x0 = -w / 2 + k * w / 4
        m = Matrix.Translation(Vector((x0 + w / 8, 0, 0.3 + h + 0.75))) @ Matrix.Rotation(-0.62, 4, "Y") @ Matrix.Diagonal((w / 4 * 1.17, d + 0.4, 0.1, 1))
        r = bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
        p.tag(r["verts"], CORR)
        p.box((x0 + w / 4 - 0.06, 0, 0.3 + h + 0.78), (0.06, d, 1.5), GLASS_D)

    p.box((0, -d / 2 - 0.25, 0.3 + h + 0.3), (5.0, 0.12, 0.9), hexc("E6E2D6"))
    p.box((0, -d / 2 - 0.3, 0.3 + h + 0.3), (4.6, 0.04, 0.5), TEAL)

    for k in range(12):
        z = 0.3 + k * 0.45
        p.box((w / 2 + 1.0 + (0 if k < 12 else 0), -d / 2 + 1.0 + k * 0.6, z), (1.0, 0.6, 0.12), IRON)
    p.box((w / 2 + 1.0, -d / 2 + 1.0 + 6.9, 5.4), (1.4, 1.6, 0.12), IRON)
    for k in range(10):
        p.box((w / 2 + 1.5, -d / 2 + 0.7 + k * 0.8, 0.9 + k * 0.45), (0.05, 0.05, 1.0), HAZARD)
    p.span((w / 2 + 1.5, -d / 2 + 0.7, 1.4), (w / 2 + 1.5, -d / 2 + 7.9, 6.3), 0.06, 0.06, HAZARD)

    for k in range(3):
        p.cone((-w / 2 - 0.6, -d / 2 + 2.0 + k * 0.9, 0.3), 0.36, 0.36, 1.0, 10, [TEAL, HAZARD, hexc("8C3B2E")][k])

    p.span((-w / 2 - 0.2, d / 2 - 1.0, 0.4), (-w / 2 - 0.2, d / 2 - 1.0, 6.4), 0.18, 0.18, CORR_D)
    p.span((-w / 2 - 0.2, d / 2 - 1.0, 6.3), (2.0, d / 2 - 1.0, 6.3), 0.16, 0.16, CORR_D)

    for lx in (-3.2, 3.2):
        p.box((lx, -d / 2 - 0.35, 4.95), (0.5, 0.3, 0.16), IRON)
        p.blob((lx, -d / 2 - 0.45, 4.86), 0.11, GLOW_WARM, sz=1.0, sub=1)

    return ray_ao(p.finish("fc_workshop", jitter=0.02, bevel=0.0, under=0.9, ao=False), strength=0.1)


def fc_pipebridge():
    p = Piece(107)
    span = 14.0
    for sx in (-span / 2, span / 2):
        for sy in (-0.9, 0.9):
            p.box((sx, sy, 3.2), (0.3, 0.3, 6.4), CORR_D)
        p.box((sx, 0, 6.3), (0.3, 2.2, 0.3), CORR_D)
        p.span((sx, -0.9, 0.4), (sx, 0.9, 6.0), 0.1, 0.1, CORR_D)
    p.box((0, -0.9, 6.3), (span, 0.25, 0.3), CORR_D)
    p.box((0, 0.9, 6.3), (span, 0.25, 0.3), CORR_D)
    for k, (y, r, c) in enumerate([(-0.55, 0.22, hexc("C8C4B8")), (-0.05, 0.28, TEAL), (0.5, 0.18, HAZARD)]):
        m = Matrix.Translation(Vector((0, y, 6.7 + r))) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        rr = bmesh.ops.create_cone(p.bm, cap_ends=True, cap_tris=False, segments=10, radius1=r, radius2=r, depth=span + 1.0, matrix=m)
        p.tag(rr["verts"], c)
        for x in (-span / 2 + 2, 0, span / 2 - 2):
            p.box((x, y, 6.7 + r), (0.18, r * 2 + 0.1, r * 2 + 0.1), CONC_D)
    for x in (-3.5, 3.5):
        p.box((x, -1.15, 5.9), (2.4, 0.06, 0.6), HAZARD)
        p.box((x, -1.17, 5.9), (2.0, 0.04, 0.3), hexc("2E2E30"))

    return ray_ao(p.finish("fc_pipebridge", jitter=0.02, bevel=0.0, ao=False), strength=0.12)


builders = {
    "iv_hut": island_hut,
    "iv_compound": compound,
    "iv_tower": tower,
    "iv_bridge": rope_bridge,
    "iv_dock": island_dock,
    "iv_lantern": island_lantern,
    "iv_boardwalk": island_boardwalk,
    "mil_barracks": barracks,
    "mil_comms": comms,
    "mil_hangar_doors": hangar_doors,
    "sv_shop_a": lambda: sv_shop("sv_shop_a", 81, 8.0, 6.5, 3.4, PAINT[0], AWN[0]),
    "sv_shop_b": lambda: sv_shop("sv_shop_b", 82, 7.0, 6.0, 3.2, PAINT[2], AWN[1]),
    "sv_shop_c": lambda: sv_shop("sv_shop_c", 83, 9.0, 6.5, 3.6, PAINT[3], AWN[2]),
    "sv_shed": sv_shed,
    "sv_watertower": sv_watertower,
    "sv_fuel": sv_fuel,
    "mil_hangar_lamps": hangar_lamps,
    "mil_hangar_lining": hangar_lining,
    "sv_bench": bench,
    "fc_office": fc_office,
    "fc_workshop": fc_workshop,
    "fc_pipebridge": fc_pipebridge,
    "iv_clothline": island_clothline,
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
    "vl_house_a": lambda: mountain_house("vl_house_a", 101, 7.2, 6.0, 0),
    "vl_house_b": lambda: mountain_house("vl_house_b", 102, 6.4, 5.6, 1),
    "vl_house_c": lambda: mountain_house("vl_house_c", 103, 8.4, 6.4, 2),
    "vl_paving": vl_paving,
    "vl_steps": vl_steps,
    "vl_fountain": vl_fountain,
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
