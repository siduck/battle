import json
import math
import random
import struct

from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HEX = {
    "con_l": "#c4baa7", "con": "#aca291", "con_d": "#8b8274", "con_dd": "#686156",
    "dirt_l": "#9d8060", "dirt": "#7f6449", "dirt_d": "#604b38",
    "grav_l": "#aba395", "grav": "#8e877b", "grav_d": "#716b61",
    "sand_l": "#cbb085", "sand": "#b5986c", "sand_d": "#96794f",
    "yel_l": "#ddb656", "yel": "#c79834", "yel_d": "#9a742a",
    "ora_l": "#d98753", "ora": "#c46532", "ora_d": "#964a27",
    "wht": "#dcd4c2", "wht_d": "#bcb3a0",
    "stl_l": "#a7acab", "stl": "#7d8587", "stl_d": "#5a6164", "stl_dd": "#41474a",
    "ox_l": "#b06a4c", "ox": "#97513a", "ox_d": "#743d2d",
    "wd_ll": "#c4a070", "wd_l": "#aa8355", "wd": "#8c6741", "wd_d": "#664a30",
    "rb_l": "#96603f", "rb": "#7b4a33", "rb_d": "#5b3727",
    "blu_l": "#6d8fa5", "blu": "#50718b", "blu_d": "#3c576d",
    "grn_l": "#7e9268", "grn": "#627751", "grn_d": "#495a3d",
    "red_l": "#b66350", "red": "#9f4b3b", "red_d": "#7b392e",
    "dark": "#3b3734", "rubber": "#2e2c2a", "void": "#252120",
    "glass": "#415a67", "glass_l": "#6e8b97",
}


def c(name):
    h = HEX[name]

    return tuple(int(h[i : i + 2], 16) / 255 for i in (1, 3, 5))


def mul(col, k):
    return (min(1.0, col[0] * k), min(1.0, col[1] * k), min(1.0, col[2] * k))


DIRT = c("dirt")


def V(p):
    return Vector((float(p[0]), float(p[1]), float(p[2])))


class Mesh:
    def __init__(self, seed=7):
        self.polys = []
        self.rng = random.Random(seed)
        self.stack = [Matrix.Identity(4)]
        self.solids = []

    def push(self, at=(0, 0, 0), yaw=0.0, pitch=0.0, roll=0.0, scale=1.0):
        m = Matrix.Translation(V(at)) @ Matrix.Rotation(yaw, 4, "Y") @ Matrix.Rotation(pitch, 4, "X") @ Matrix.Rotation(roll, 4, "Z") @ Matrix.Scale(scale, 4)
        self.stack.append(self.stack[-1] @ m)

    def pop(self):
        self.stack.pop()

    def shade(self, col, amount):
        return mul(col, 1 + self.rng.uniform(-amount, amount))

    def poly(self, pts, col, normals=None):
        t = self.stack[-1]
        ps = [t @ V(p) for p in pts]

        if normals:
            r = t.to_3x3()
            normals = [(r @ V(n)).normalized() for n in normals]

        self.polys.append((ps, col, normals))

    def face(self, pts, col, inside, normals=None):
        ps = [V(p) for p in pts]
        n = newell(ps)
        cen = sum(ps, Vector()) / len(ps)

        if n.dot(cen - inside) < 0:
            ps.reverse()
            normals = normals[::-1] if normals else None

        self.poly(ps, col, normals)

    def disc(self, center, normal, r, col, seg=6):
        o = V(center)
        d = V(normal).normalized()
        ref = Vector((0, 0, 1)) if abs(d.y) > 0.95 else Vector((0, 1, 0))
        sx = d.cross(ref).normalized()
        sy = d.cross(sx).normalized()
        self.face([o + (sx * math.cos(math.tau * i / seg) + sy * math.sin(math.tau * i / seg)) * r for i in range(seg)], col, o - d)

    def box(self, a, b, col, bevel=0.0, skip="", sub=0.0):
        x0, y0, z0 = (min(a[i], b[i]) for i in range(3))
        x1, y1, z1 = (max(a[i], b[i]) for i in range(3))
        lo = (x0, y0, z0)
        hi = (x1, y1, z1)
        mid = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        bevel = min(bevel, min(x1 - x0, y1 - y0, z1 - z0) * 0.3)
        names = ("-x", "+x", "-y", "+y", "-z", "+z")
        skipped = {s for s in skip.split(",") if s}

        def corner(ix, iy, iz, axis):
            q = [hi[0] if ix else lo[0], hi[1] if iy else lo[1], hi[2] if iz else lo[2]]
            s = (ix, iy, iz)

            for k in range(3):
                if k != axis and names[k * 2 + s[k]] not in skipped:
                    q[k] += -bevel if s[k] else bevel

            return tuple(q)

        for axis in range(3):
            o = [k for k in range(3) if k != axis]

            for side in (0, 1):
                if names[axis * 2 + side] in skipped:
                    continue

                pts = []

                for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    s = [0, 0, 0]
                    s[axis] = side
                    s[o[0]] = u
                    s[o[1]] = v
                    pts.append(corner(s[0], s[1], s[2], axis))

                if sub:
                    self.grid(pts, col, mid, sub)
                elif bevel > 0:
                    nrm = [0, 0, 0]
                    nrm[axis] = 1 if side else -1
                    self.face(pts, col, mid, [tuple(nrm)] * 4)
                else:
                    self.face(pts, col, mid)

        if bevel <= 0:
            return

        def axis_normal(face_axis, s):
            nrm = [0, 0, 0]
            nrm[face_axis] = 1 if s[face_axis] else -1

            return tuple(nrm)

        for axis in range(3):
            o = [k for k in range(3) if k != axis]

            for u in (0, 1):
                for v in (0, 1):
                    n0 = names[o[0] * 2 + u]
                    n1 = names[o[1] * 2 + v]

                    if n0 in skipped or n1 in skipped:
                        continue

                    pts = []
                    nrms = []

                    for end, face_axis in ((0, o[0]), (1, o[0]), (1, o[1]), (0, o[1])):
                        s = [0, 0, 0]
                        s[axis] = end
                        s[o[0]] = u
                        s[o[1]] = v
                        pts.append(corner(s[0], s[1], s[2], face_axis))
                        nrms.append(axis_normal(face_axis, s))

                    self.face(pts, col, mid, nrms)

        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    if {names[ix], names[2 + iy], names[4 + iz]} & skipped:
                        continue

                    self.face([corner(ix, iy, iz, k) for k in range(3)], col, mid, [axis_normal(k, (ix, iy, iz)) for k in range(3)])

    def grid(self, pts, col, inside, size):
        a, b, cc, d = (V(p) for p in pts)
        nu = max(1, int(math.ceil((b - a).length / size)))
        nv = max(1, int(math.ceil((d - a).length / size)))

        def at(i, j):
            u = i / nu
            v = j / nv

            return a.lerp(b, u).lerp(d.lerp(cc, u), v)

        for i in range(nu):
            for j in range(nv):
                self.face([at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)], col, inside)

    def beam(self, a, b, w, h, col, bevel=0.0, caps=True, up=None, roll=0.0):
        pa = V(a)
        pb = V(b)
        d = (pb - pa).normalized()

        if up is None:
            up = Vector((0, 1, 0)) if abs(d.y) < 0.95 else Vector((0, 0, 1))

        sx = d.cross(V(up)).normalized()
        sy = sx.cross(d).normalized()

        if roll:
            r = Matrix.Rotation(roll, 4, d)
            sx = r @ sx
            sy = r @ sy

        hw = w / 2
        hh = h / 2
        bv = min(bevel, min(w, h) * 0.3)

        if bv > 0:
            prof = [(-hw + bv, -hh), (hw - bv, -hh), (hw, -hh + bv), (hw, hh - bv), (hw - bv, hh), (-hw + bv, hh), (-hw, hh - bv), (-hw, -hh + bv)]
        else:
            prof = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]

        ra = [pa + sx * u + sy * v for u, v in prof]
        rb = [pb + sx * u + sy * v for u, v in prof]
        mid = (pa + pb) / 2
        n = len(prof)

        sides = [-sy, sx, sy, -sx]

        for i in range(n):
            j = (i + 1) % n

            if bv > 0:
                ni = sides[i // 2]
                nj = sides[j // 2]
                self.face([ra[i], ra[j], rb[j], rb[i]], col, mid, [ni, nj, nj, ni])
            else:
                self.face([ra[i], ra[j], rb[j], rb[i]], col, mid)

        if caps in (True, "a"):
            self.face(ra, col, mid)

        if caps in (True, "b"):
            self.face(rb, col, mid)

    def cyl(self, a, b, r, col, seg=8, r2=None, caps="ab", chamfer=0.0, capcol=None, phase=None):
        pa = V(a)
        pb = V(b)
        d = (pb - pa).normalized()
        ref = Vector((0, 0, 1)) if abs(d.y) > 0.95 else Vector((0, 1, 0))
        sx = d.cross(ref).normalized()
        sy = d.cross(sx).normalized()
        r2 = r if r2 is None else r2
        ph = math.pi / seg if phase is None else phase
        length = (pb - pa).length

        def ring(h, rad):
            return [pa + d * h + (sx * math.cos(ph + math.tau * i / seg) + sy * math.sin(ph + math.tau * i / seg)) * rad for i in range(seg)]

        if chamfer > 0:
            rings = [ring(0, r - chamfer), ring(chamfer, r), ring(length - chamfer, r2), ring(length, r2 - chamfer)]
            tones = [mul(col, 1.1), col, mul(col, 1.1)]
        else:
            rings = [ring(0, r), ring(length, r2)]
            tones = [col]

        mid = (pa + pb) / 2

        for k in range(len(rings) - 1):
            lo, up = rings[k], rings[k + 1]
            inner = (sum(lo, Vector()) + sum(up, Vector())) / (2 * seg)

            for i in range(seg):
                j = (i + 1) % seg
                self.face([lo[i], lo[j], up[j], up[i]], tones[k], inner)

        if "a" in caps:
            self.face(rings[0], capcol or col, mid)

        if "b" in caps:
            self.face(rings[-1], capcol or col, mid)

    def tube(self, a, b, r, col, seg=4, caps=""):
        self.cyl(a, b, r, col, seg=seg, caps=caps)

    def lathe(self, origin, profile, cols, seg=12, axis=(0, 1, 0), phase=None):
        o = V(origin)
        d = V(axis).normalized()
        ref = Vector((0, 0, 1)) if abs(d.y) > 0.95 else Vector((0, 1, 0))
        sx = d.cross(ref).normalized()
        sy = d.cross(sx).normalized()
        ph = math.pi / seg if phase is None else phase
        rings = [[o + d * h + (sx * math.cos(ph + math.tau * i / seg) + sy * math.sin(ph + math.tau * i / seg)) * r for i in range(seg)] for r, h in profile]

        for k in range(len(profile) - 1):
            col = cols[k] if isinstance(cols, list) else cols
            r0, h0 = profile[k]
            r1, h1 = profile[k + 1]
            nr = h1 - h0
            nh = r0 - r1

            for i in range(seg):
                j = (i + 1) % seg
                pts = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]

                if r0 < 1e-4:
                    pts = [rings[k][i], rings[k + 1][j], rings[k + 1][i]]
                elif r1 < 1e-4:
                    pts = [rings[k][i], rings[k][j], rings[k + 1][i]]

                am = ph + math.tau * (i + 0.5) / seg
                out = (sx * math.cos(am) + sy * math.sin(am)) * nr + d * nh

                if newell(pts).dot(out) < 0:
                    pts.reverse()

                self.poly(pts, col)

    def extrude(self, outline, a0, a1, col, axis="x", caps=True, cols=None):
        def p(u, v, w):
            if axis == "x":
                return Vector((w, v, u))

            if axis == "z":
                return Vector((u, v, w))

            return Vector((u, w, v))

        n = len(outline)
        area = sum(outline[i][0] * outline[(i + 1) % n][1] - outline[(i + 1) % n][0] * outline[i][1] for i in range(n))
        pts = list(outline) if area > 0 else list(reversed(outline))
        edge_cols = cols if cols is None or area > 0 else list(reversed(cols[:-1])) + [cols[-1]]

        for i in range(n):
            u0, v0 = pts[i]
            u1, v1 = pts[(i + 1) % n]
            q = [p(u0, v0, a0), p(u1, v1, a0), p(u1, v1, a1), p(u0, v0, a1)]
            out = p(v1 - v0, -(u1 - u0), 0)

            if newell(q).dot(out) < 0:
                q.reverse()

            self.poly(q, edge_cols[i] if edge_cols else col)

        if not caps:
            return

        along = p(0, 0, 1)

        for tri in earclip(pts):
            for w, sign in ((a0, -1), (a1, 1)):
                q = [p(pts[i][0], pts[i][1], w) for i in tri]

                if newell(q).dot(along * sign * (1 if a1 > a0 else -1)) < 0:
                    q.reverse()

                self.poly(q, col)

    def rock(self, center, rx, ry, rz, col, squash=0.35):
        x, y, z = center
        j = self.rng.uniform
        top = (x + j(-0.2, 0.2) * rx, y + ry, z + j(-0.2, 0.2) * rz)
        bot = (x, y - ry * squash, z)
        a0 = j(0, 1.5)
        ring = [(x + math.cos(a0 + i * math.tau / 5) * rx * j(0.75, 1.1), y + j(-0.15, 0.3) * ry, z + math.sin(a0 + i * math.tau / 5) * rz * j(0.75, 1.1)) for i in range(5)]
        mid = V((x, y + ry * 0.1, z))

        for i in range(5):
            a = ring[i]
            b = ring[(i + 1) % 5]
            self.face([a, b, top], self.shade(col, 0.1), mid)
            self.face([a, b, bot], mul(col, 0.8), mid)

    def solid(self, a, b):
        self.solids.append((0, a[0], a[1], a[2], b[0], b[1], b[2]))

    def ramp(self, a, b, rise):
        self.solids.append(({"px": 1, "nx": 2, "pz": 3, "nz": 4}[rise], a[0], a[1], a[2], b[0], b[1], b[2]))


def newell(ps):
    n = Vector()

    for i in range(len(ps)):
        a = ps[i]
        b = ps[(i + 1) % len(ps)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)

    return n


def earclip(pts):
    idx = list(range(len(pts)))
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, cc):
        return cross(a, b, p) > 1e-9 and cross(b, cc, p) > 1e-9 and cross(cc, a, p) > 1e-9

    guard = 0

    while len(idx) > 3 and guard < 2000:
        guard += 1

        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, cc = pts[i0], pts[i1], pts[i2]

            if cross(a, b, cc) <= 1e-9:
                continue

            if any(inside(pts[j], a, b, cc) for j in idx if j not in (i0, i1, i2)):
                continue

            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            idx.pop(0)

    if len(idx) == 3:
        tris.append(tuple(idx))

    return tris


def hemi(n):
    out = []
    g = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        z = math.sqrt(1 - (i + 0.5) / n)
        r = math.sqrt(1 - z * z)
        out.append(Vector((math.cos(i * g) * r, math.sin(i * g) * r, z)))

    return out


def triangulate(polys):
    tris = []

    for ps, col, normals in polys:
        n = newell(ps)

        if n.length < 1e-8:
            continue

        n.normalize()

        for i in range(1, len(ps) - 1):
            t = (0, i, i + 1)

            if (ps[i] - ps[0]).cross(ps[i + 1] - ps[0]).length < 1e-7:
                continue

            tris.append(([ps[k] for k in t], n, col, ps, [normals[k] for k in t] if normals else None))

    return tris


def bake(m, reach=1.4, strength=0.7, floor=0.0, grime=0.8, rays=20, low=0.42, ground=True, lift=0.0):
    tris = triangulate(m.polys)
    verts = []
    faces = []

    for t in tris:
        k = len(verts)
        verts.extend(t[0])
        faces.append((k, k + 1, k + 2))

    tree = BVHTree.FromPolygons(verts, faces)
    dirs = hemi(rays)
    cache = {}
    out = []

    def sample(p, n):
        t = n.orthogonal().normalized()
        b = n.cross(t)
        occ = 0.0
        back = 0

        for d in dirs:
            w = t * d.x + b * d.y + n * d.z
            hit = tree.ray_cast(p, w, reach)

            if hit[0] is not None:
                if hit[1].dot(w) > 0.05:
                    back += 1

                occ += 1 - (hit[3] / reach) ** 2
            elif ground and w.y < -0.05 and p.y - floor > -0.05:
                dist = (p.y - floor) / -w.y

                if dist < reach:
                    occ += 1 - (dist / reach) ** 2

        return occ / rays, back / rays

    for corners, n, col, ps, normals in tris:
        cen = sum(ps, Vector()) / len(ps)
        cols = []

        for index, p in enumerate(corners):
            if normals:
                v = normals[index]
                key = (round(p.x, 3), round(p.y, 3), round(p.z, 3), round(v.x, 2), round(v.y, 2), round(v.z, 2))
            else:
                key = (round(p.x, 3), round(p.y, 3), round(p.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2), round(cen.x, 1), round(cen.y, 1), round(cen.z, 1))

            if key not in cache:
                to = cen - p
                dist = to.length
                occ = 0.0

                for pull in (min(0.12, dist * 0.3), dist * 0.5, dist):
                    q = p + (to.normalized() * pull if dist > 1e-5 else Vector()) + n * 0.015
                    occ, back = sample(q, n)

                    if back < 0.35:
                        break

                cache[key] = max(low, 1 - strength * occ)

            ao = cache[key]
            h = p.y - floor
            dirt = max(0.0, 1 - max(0.0, h) / 0.8) * grime if grime else 0.0
            k = ao * (1 - 0.14 * dirt) * (1 + lift * min(1.0, max(0.0, h / 12)))
            tint = mul(col, k)
            mixv = dirt * 0.22
            cols.append(tuple(tint[i] + (DIRT[i] * ao - tint[i]) * mixv for i in range(3)))

        out.append((corners, normals or [n, n, n], cols))

    return out


def write_glb(path, tris):
    prims = []
    cur = {"seen": {}, "pos": [], "nrm": [], "col": [], "idx": []}

    for corners, normals, cols in tris:
        if len(cur["pos"]) > 65000:
            prims.append(cur)
            cur = {"seen": {}, "pos": [], "nrm": [], "col": [], "idx": []}

        for p, n, col in zip(corners, normals, cols):
            cb = tuple(max(0, min(255, int(round(v * 255)))) for v in col)
            cb = tuple(min(255, (v + 1) // 3 * 3) for v in cb)
            key = (round(p.x, 4), round(p.y, 4), round(p.z, 4), round(n.x, 3), round(n.y, 3), round(n.z, 3), cb)
            j = cur["seen"].get(key)

            if j is None:
                j = len(cur["pos"])
                cur["seen"][key] = j
                cur["pos"].append((p.x, p.y, p.z))
                cur["nrm"].append((n.x, n.y, n.z))
                cur["col"].append(cb)

            cur["idx"].append(j)

    prims.append(cur)
    blob = bytearray()
    views = []
    acc = []
    out = []

    def push(data, target):
        while len(blob) % 4:
            blob.append(0)

        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)

        return len(views) - 1

    for pr in prims:
        base = len(acc)
        pos = pr["pos"]
        count = len(pos)
        mn = [min(p[k] for p in pos) for k in range(3)]
        mx = [max(p[k] for p in pos) for k in range(3)]
        acc.append({"bufferView": push(b"".join(struct.pack("<3f", *p) for p in pos), 34962), "componentType": 5126, "count": count, "type": "VEC3", "min": mn, "max": mx})
        acc.append({"bufferView": push(b"".join(struct.pack("<3f", *p) for p in pr["nrm"]), 34962), "componentType": 5126, "count": count, "type": "VEC3"})
        acc.append({"bufferView": push(b"".join(struct.pack("<4B", v[0], v[1], v[2], 255) for v in pr["col"]), 34962), "componentType": 5121, "normalized": True, "count": count, "type": "VEC4"})
        acc.append({"bufferView": push(struct.pack("<%dH" % len(pr["idx"]), *pr["idx"]), 34963), "componentType": 5123, "count": len(pr["idx"]), "type": "SCALAR"})
        out.append({"attributes": {"POSITION": base, "NORMAL": base + 1, "COLOR_0": base + 2}, "indices": base + 3, "material": 0})

    while len(blob) % 4:
        blob.append(0)

    doc = {
        "asset": {"version": "2.0", "generator": "dronefire construction kit"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": out}],
        "materials": [{"name": "kit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": views,
        "accessors": acc,
    }
    js = json.dumps(doc, separators=(",", ":")).encode()

    while len(js) % 4:
        js += b" "

    total = 12 + 8 + len(js) + 8 + len(blob)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))

    all_pos = [p for pr in prims for p in pr["pos"]]

    return len(tris), [min(p[k] for p in all_pos) for k in range(3)], [max(p[k] for p in all_pos) for k in range(3)]
