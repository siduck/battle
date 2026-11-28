import math
import random

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HEX = {
    "wood_l": "#b5926a",
    "wood": "#99764f",
    "wood_d": "#6f5239",
    "wood_x": "#4c382a",
    "gray_l": "#b8a68b",
    "gray": "#98836a",
    "gray_d": "#715f4c",
    "plas_l": "#dfcaa2",
    "plas": "#c9ad80",
    "plas_d": "#a58a62",
    "red_l": "#ae604a",
    "red": "#97493a",
    "red_d": "#743529",
    "teal_l": "#7b9c92",
    "teal": "#5f827a",
    "teal_d": "#47625e",
    "sage_l": "#a2a67a",
    "sage": "#86895f",
    "sage_d": "#666a49",
    "ochre_l": "#d1a65c",
    "ochre": "#b88a43",
    "ochre_d": "#8f6a33",
    "slate_l": "#8b99a0",
    "slate": "#6d7d86",
    "slate_d": "#52606a",
    "cream": "#e6d8b4",
    "cream_l": "#efe4c6",
    "cream_d": "#c8b78f",
    "shingle_l": "#8a5f47",
    "shingle": "#704a37",
    "shingle_d": "#55382b",
    "tin_l": "#aaa597",
    "tin": "#8d897d",
    "tin_d": "#6c6961",
    "rust_l": "#a66b45",
    "rust": "#8a5336",
    "rust_d": "#663c29",
    "iron_l": "#625a53",
    "iron": "#45403b",
    "iron_d": "#2f2c29",
    "glass": "#33434f",
    "glass_l": "#6c8691",
    "void": "#231c18",
    "stone_l": "#c4ab85",
    "stone": "#a78d6c",
    "stone_d": "#826c55",
    "rock_a": "#8f6a52",
    "rock_b": "#a9735a",
    "rock_c": "#b98a65",
    "rock_d": "#c9a077",
    "rock_e": "#d6b78d",
    "sand_l": "#d6c096",
    "sand": "#cbb088",
    "sand_d": "#b09670",
    "cact_l": "#a6af7f",
    "cact": "#8c9a66",
    "cact_d": "#6f7e51",
    "scrub_l": "#c0b98c",
    "scrub": "#a6a075",
    "scrub_d": "#847f5a",
    "straw_l": "#cfb175",
    "straw": "#b49459",
    "straw_d": "#8e7342",
    "canvas_l": "#ddcca4",
    "canvas": "#c6b28a",
    "canvas_d": "#a4906c",
    "dead_l": "#bea483",
    "dead": "#9e8064",
    "dead_d": "#765b45",
    "fruit": "#a5455a",
    "lamp": "#f4cd7a",
    "ember": "#d9793a",
    "water": "#5c7f80",
    "ore": "#6c5f57",
    "ore_l": "#8a7a6c",
    "gold": "#d8ac4c",
}


def rgb(name):
    h = HEX[name].lstrip("#")

    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def hash01(*v):
    h = 2166136261

    for x in v:
        h = ((h ^ int(round(x * 977))) * 16777619) & 0xFFFFFFFF

    return ((h >> 8) & 0xFFFF) / 65535.0


def pick(fam, *v):
    h = hash01(*v)

    if h < 0.2:
        return fam + "_l"

    if h > 0.82:
        return fam + "_d"

    return fam


FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    " ": ["00", "00", "00", "00", "00", "00", "00"],
}


class Mesh:
    def __init__(self, seed=1):
        self.faces = []
        self.stack = [Matrix.Identity(4)]
        self.blocks = []
        self.rnd = random.Random(seed)

    def push(self, m):
        self.stack.append(self.stack[-1] @ m)

    def pop(self):
        self.stack.pop()

    def at(self, x=0.0, y=0.0, z=0.0, yaw=0.0, tilt=0.0, roll=0.0):
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")

        if tilt:
            m = m @ Matrix.Rotation(math.radians(tilt), 4, "X")

        if roll:
            m = m @ Matrix.Rotation(math.radians(roll), 4, "Y")

        return Frame(self, m)

    def face(self, pts, col):
        m = self.stack[-1]
        self.faces.append(([m @ Vector(p) for p in pts], col))

    def quad(self, a, b, c, d, col):
        self.face((a, b, c, d), col)

    def tri(self, a, b, c, col):
        self.face((a, b, c), col)

    def block(self, x0, y0, x1, y1, h):
        self.blocks.append((x0, y0, x1, y1, h))

    def box(self, p0, p1, col, ch=0.0, skip=""):
        x0, y0, z0 = p0
        x1, y1, z1 = p1

        if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
            return

        ch = min(ch, (x1 - x0) * 0.3, (y1 - y0) * 0.3, (z1 - z0) * 0.3)

        if ch < 0.008:
            c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            sides = {"x": (0, 1, 3, 2), "X": (4, 6, 7, 5), "y": (0, 4, 5, 1), "Y": (2, 3, 7, 6), "z": (0, 2, 6, 4), "Z": (1, 5, 7, 3)}

            for key, ids in sides.items():
                if key not in skip:
                    self.face([c[i] for i in ids], col)

            return

        lo = (x0, y0, z0)
        hi = (x1, y1, z1)
        names = ("x", "y", "z")

        def corner(sx, sy, sz, axis):
            s = (sx, sy, sz)
            p = []

            for i in range(3):
                edge = hi[i] if s[i] else lo[i]

                if i != axis:
                    edge += -ch if s[i] else ch

                p.append(edge)

            return tuple(p)

        for axis in range(3):
            for side in (0, 1):
                key = names[axis].upper() if side else names[axis]

                if key in skip:
                    continue

                a, b = [i for i in range(3) if i != axis]
                ring = []

                for sa, sb in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    s = [0, 0, 0]
                    s[axis] = side
                    s[a] = sa
                    s[b] = sb
                    ring.append(corner(*s, axis))

                flip = (side == 0) != (axis == 1)
                self.face(ring[::-1] if flip else ring, col)

        for axis in range(3):
            a, b = [i for i in range(3) if i != axis]

            for sa in (0, 1):
                for sb in (0, 1):
                    ka = names[a].upper() if sa else names[a]
                    kb = names[b].upper() if sb else names[b]

                    if ka in skip or kb in skip:
                        continue

                    s0 = [0, 0, 0]
                    s0[a] = sa
                    s0[b] = sb
                    s1 = list(s0)
                    s1[axis] = 1
                    pts = [corner(*s0, a), corner(*s1, a), corner(*s1, b), corner(*s0, b)]
                    out = [0.0, 0.0, 0.0]
                    out[a] = 1 if sa else -1
                    out[b] = 1 if sb else -1
                    self.orient(pts, out, col)

        for sx in (0, 1):
            for sy in (0, 1):
                for sz in (0, 1):
                    keys = ("X" if sx else "x", "Y" if sy else "y", "Z" if sz else "z")

                    if any(k in skip for k in keys):
                        continue

                    pts = [corner(sx, sy, sz, 0), corner(sx, sy, sz, 1), corner(sx, sy, sz, 2)]
                    self.orient(pts, (1 if sx else -1, 1 if sy else -1, 1 if sz else -1), col)

    def orient(self, pts, out, col):
        a, b, c = Vector(pts[0]), Vector(pts[1]), Vector(pts[2])
        n = (b - a).cross(c - a)

        if n.dot(Vector(out)) < 0:
            pts = pts[::-1]

        self.face(pts, col)

    def beam(self, a, b, w, h, col, ch=0.0, skip=""):
        a = Vector(a)
        b = Vector(b)
        d = b - a
        length = d.length

        if length < 0.001:
            return

        x = d / length
        up = Vector((0, 0, 1)) if abs(x.z) < 0.95 else Vector((0, 1, 0))
        y = up.cross(x).normalized()
        z = x.cross(y).normalized()
        m = Matrix(((x.x, y.x, z.x, a.x), (x.y, y.y, z.y, a.y), (x.z, y.z, z.z, a.z), (0, 0, 0, 1)))
        self.push(m)
        self.box((0, -w / 2, -h / 2), (length, w / 2, h / 2), col, ch, skip)
        self.pop()

    def loft(self, rings, cols, cap_top=None, cap_bottom=None):
        for j in range(len(rings) - 1):
            lo = rings[j]
            hi = rings[j + 1]
            n = len(lo)

            for i in range(n):
                i2 = (i + 1) % n
                col = cols(i, j) if callable(cols) else cols
                quad = [lo[i], lo[i2], hi[i2], hi[i]]
                pts = []

                for p in quad:
                    if not pts or (Vector(p) - Vector(pts[-1])).length > 1e-5:
                        pts.append(p)

                if len(pts) > 2 and (Vector(pts[0]) - Vector(pts[-1])).length < 1e-5:
                    pts.pop()

                if len(pts) < 3:
                    continue

                if len(pts) == 4:
                    a, b, c, d = [Vector(p) for p in pts]
                    n1 = (b - a).cross(c - a)
                    n2 = (c - a).cross(d - a)

                    if n1.length > 1e-9 and n2.length > 1e-9 and n1.normalized().dot(n2.normalized()) < 0.999:
                        self.face((pts[0], pts[1], pts[2]), col)
                        self.face((pts[0], pts[2], pts[3]), col)

                        continue

                self.face(pts, col)

        if cap_top:
            self.face(list(rings[-1]), cap_top)

        if cap_bottom:
            self.face(list(rings[0])[::-1], cap_bottom)

    def ring(self, c, r, z, n, rot=0.0, sq=1.0, rib=1.0):
        out = []

        for i in range(n):
            a = 2 * math.pi * i / n + rot
            rr = r * (rib if i % 2 else 1.0)
            out.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * sq, z))

        return out

    def prism(self, c, z0, z1, r0, r1, n, col, top=True, bottom=False, rot=None, sq=1.0):
        rot = math.pi / n if rot is None else rot
        cap = (top if isinstance(top, str) else (col if isinstance(col, str) else col(0, 0))) if top else None
        low = (col if isinstance(col, str) else col(0, 0)) if bottom else None
        self.loft([self.ring(c, r0, z0, n, rot, sq), self.ring(c, r1, z1, n, rot, sq)], col, cap, low)

    def lathe(self, c, profile, n, col, top=True, bottom=False, rot=None):
        rot = math.pi / n if rot is None else rot
        rings = [self.ring(c, max(r, 0.001), z, n, rot) for r, z in profile]
        cap = (top if isinstance(top, str) else (col if isinstance(col, str) else col(0, len(profile) - 2))) if top else None
        low = (col if isinstance(col, str) else col(0, 0)) if bottom else None
        self.loft(rings, col, cap, low)

    def tube(self, pts, radii, n, col, cap_top=True, cap_bottom=False, rib=1.0, twist=0.0):
        pts = [Vector(p) for p in pts]
        rings = []
        prev = None

        for j, p in enumerate(pts):
            t = (pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]).normalized()

            if prev is None:
                up = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
                u = (up - t * up.dot(t)).normalized()
            else:
                u = (prev - t * prev.dot(t)).normalized()

            prev = u
            v = t.cross(u).normalized()
            ring = []

            for i in range(n):
                a = 2 * math.pi * i / n + twist * j
                rr = radii[j] * (rib if i % 2 else 1.0)
                ring.append(tuple(p + u * math.cos(a) * rr + v * math.sin(a) * rr))

            rings.append(ring)

        cap = (cap_top if isinstance(cap_top, str) else (col if isinstance(col, str) else col(0, len(pts) - 2))) if cap_top else None
        low = (col if isinstance(col, str) else col(0, 0)) if cap_bottom else None
        self.loft(rings, col, cap, low)

    def hull(self, points, col, drop_bottom=None):
        bm = bmesh.new()
        verts = [bm.verts.new(p) for p in points]
        res = bmesh.ops.convex_hull(bm, input=verts)
        doomed = [v for v in res.get("geom_interior", []) if isinstance(v, bmesh.types.BMVert)]

        if doomed:
            bmesh.ops.delete(bm, geom=doomed, context="VERTS")

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()

        for f in bm.faces:
            n = f.normal
            c = f.calc_center_median()

            if drop_bottom is not None and n.z < -0.6 and c.z < drop_bottom:
                continue

            self.face([tuple(v.co) for v in f.verts], col(n, c) if callable(col) else col)

        bm.free()

    def extrude(self, outline, y0, y1, col, side=None, back=True, front=True):
        pts = list(outline)
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))

        if area < 0:
            pts = pts[::-1]

        if front:
            self.face([(u, y0, z) for u, z in pts], col)

        if back:
            self.face([(u, y1, z) for u, z in pts][::-1], col)

        for i in range(len(pts)):
            a = pts[i]
            b = pts[(i + 1) % len(pts)]
            self.face([(a[0], y0, a[1]), (a[0], y1, a[1]), (b[0], y1, b[1]), (b[0], y0, b[1])], side or col)

    def sheet(self, pts, col):
        self.face(pts, col)
        self.face(pts[::-1], col)

    def text(self, word, x, z, height, col, depth):
        px = height / 7.0
        total = sum(len(FONT[ch][0]) + 1 for ch in word) - 1
        cur = x - total * px / 2

        for ch in word:
            rows = FONT[ch]

            for r, row in enumerate(rows):
                i = 0

                while i < len(row):
                    if row[i] != "1":
                        i += 1
                        continue

                    j = i

                    while j < len(row) and row[j] == "1":
                        j += 1

                    a = cur + i * px
                    b = cur + j * px
                    top = z + height - r * px
                    self.quad((a, depth, top - px), (b, depth, top - px), (b, depth, top), (a, depth, top), col)
                    i = j

            cur += (len(rows[0]) + 1) * px

    def tris(self):
        return sum(len(p) - 2 for p, _ in self.faces)


class Frame:
    def __init__(self, mesh, m):
        self.mesh = mesh
        self.m = m

    def __enter__(self):
        self.mesh.push(self.m)

        return self.mesh

    def __exit__(self, *a):
        self.mesh.pop()


def hemi(n):
    out = []

    for i in range(n):
        u = (i + 0.5) / n
        phi = i * 2.399963
        r = math.sqrt(u)
        out.append(Vector((r * math.cos(phi), r * math.sin(phi), math.sqrt(1 - u))))

    return out


def triangulate(points):
    if len(points) == 3:
        return [(0, 1, 2)]

    if len(points) == 4:
        return [(0, 1, 2), (0, 2, 3)]

    n = Vector((0, 0, 0))

    for i in range(len(points)):
        a = points[i]
        b = points[(i + 1) % len(points)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)

    n.normalize()
    left = list(range(len(points)))
    out = []
    guard = 0

    while len(left) > 3 and guard < 1000:
        guard += 1

        for k in range(len(left)):
            i0, i1, i2 = left[k - 1], left[k], left[(k + 1) % len(left)]
            a, b, c = points[i0], points[i1], points[i2]

            if (b - a).cross(c - b).dot(n) <= 1e-10:
                continue

            inside = False

            for j in left:
                if j in (i0, i1, i2):
                    continue

                p = points[j]

                if (b - a).cross(p - a).dot(n) > 1e-9 and (c - b).cross(p - b).dot(n) > 1e-9 and (a - c).cross(p - c).dot(n) > 1e-9:
                    inside = True
                    break

            if not inside:
                out.append((i0, i1, i2))
                left.pop(k)
                break

    out.append(tuple(left[:3]))

    return out


def finalize(mesh, ao=0.55, reach=1.4, dust=0.22, dust_h=0.9, lift=(0.92, 1.04), ground=True, bias=0.012, dust_tone=0.86):
    tris = []

    for pts, col in mesh.faces:
        mid = sum(pts, Vector((0, 0, 0))) / len(pts)

        for ids in triangulate(pts):
            p = [pts[i] for i in ids]
            n = (p[1] - p[0]).cross(p[2] - p[0])

            if n.length < 1e-7:
                continue

            tris.append((p, n.normalized(), col, mid))

    verts = [v for t in tris for v in t[0]]
    tree = BVHTree.FromPolygons(verts, [(i * 3, i * 3 + 1, i * 3 + 2) for i in range(len(tris))])
    kept = []

    for i, (p, n, col, mid) in enumerate(tris):
        c = (p[0] + p[1] + p[2]) / 3

        if ground and n.z < -0.9 and c.z < 0.02:
            continue

        if ground and max(v.z for v in p) < -0.02 and n.z < -0.5:
            continue

        hidden = True

        for s in [c] + [c + (v - c) * 0.85 for v in p]:
            hit = tree.ray_cast(s + n * 0.001, n, 0.025)

            if hit[0] is None or hit[2] == i:
                hidden = False
                break

        if not hidden:
            kept.append((p, n, col, mid))

    verts = [v for t in kept for v in t[0]]
    tree = BVHTree.FromPolygons(verts, [(i * 3, i * 3 + 1, i * 3 + 2) for i in range(len(kept))])
    dirs = hemi(24)
    cache = {}
    zmax = max((v.z for v in verts), default=1.0)
    sand = rgb("sand")
    out = []

    for p, n, col, center in kept:
        up = Vector((0, 0, 1)) if abs(n.z) < 0.95 else Vector((1, 0, 0))
        u = up.cross(n).normalized()
        w = n.cross(u)
        base = rgb(col)
        cols = []

        for v in p:
            to = center - v
            dist = to.length
            s = v + to * min(0.5, 0.16 / max(dist, 1e-6)) + n * bias
            key = (round(s.x, 2), round(s.y, 2), round(s.z, 2), round(n.x, 1), round(n.y, 1), round(n.z, 1))
            occ = cache.get(key)

            if occ is None:
                total = 0.0

                for d in dirs:
                    ray = u * d.x + w * d.y + n * d.z
                    hit = tree.ray_cast(s, ray, reach)
                    t = hit[3] if hit[0] is not None else None

                    if ground and ray.z < -1e-4 and s.z > 0:
                        g = -s.z / ray.z

                        if g < reach and (t is None or g < t):
                            t = g

                    if t is not None:
                        total += 1 - (t / reach) ** 2

                occ = total / len(dirs)
                cache[key] = occ

            k = 1 - ao * min(1.0, occ * 1.15)
            h = min(max(v.z / max(zmax, 0.01), 0.0), 1.0)
            k *= lift[0] + (lift[1] - lift[0]) * h ** 0.7
            dk = dust * max(0.0, 1 - max(v.z, 0.0) / dust_h) if col not in ("lamp", "ember", "void") else 0.0

            if col in ("lamp", "ember"):
                k = 1.0

            rgbv = [base[j] * (1 - dk) + sand[j] * dust_tone * dk for j in range(3)]
            shade = [rgbv[0] * k, rgbv[1] * k, rgbv[2] * (k + (1 - k) * 0.12)]
            cols.append(tuple(min(max(round(x * 85) / 85, 0.0), 1.0) for x in shade))

        out.append((p, n, cols))

    return out
