import json
import math
import random
import struct

from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon

import palette

LOD = 0
SIZE_CUT = (0.0, 0.045, 0.16)
SIDE_SCALE = (1.0, 0.62, 0.45)


def rgb(c):
    if isinstance(c, str):
        h = palette.COLORS[c].lstrip("#")

        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    return tuple(c)


def shade(c, k):
    c = rgb(c)

    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def mix(a, b, t):
    a = rgb(a)
    b = rgb(b)

    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def hash01(*vals):
    h = 2166136261

    for v in vals:
        h = ((h ^ (int(round(v * 997)) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF

    return ((h >> 8) & 0xFFFF) / 65535.0


class Poly:
    __slots__ = ("pts", "col", "smooth", "ao", "cast")

    def __init__(self, pts, col, smooth=False, ao=True, cast=True):
        self.pts = [Vector(p) for p in pts]
        self.col = rgb(col)
        self.smooth = smooth
        self.ao = ao
        self.cast = cast

    def normal(self):
        n = Vector((0, 0, 0))
        p = self.pts

        for i in range(len(p)):
            a = p[i]
            b = p[(i + 1) % len(p)]
            n.x += (a.y - b.y) * (a.z + b.z)
            n.y += (a.z - b.z) * (a.x + b.x)
            n.z += (a.x - b.x) * (a.y + b.y)

        return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

    def center(self):
        c = Vector((0, 0, 0))

        for p in self.pts:
            c += p

        return c / len(self.pts)


class Part(list):
    def __add__(self, other):
        return Part(list(self) + list(other))

    def move(self, x=0.0, y=0.0, z=0.0):
        d = Vector((x, y, z))

        for f in self:
            f.pts = [p + d for p in f.pts]

        return self

    def xform(self, m):
        flip = m.determinant() < 0

        for f in self:
            f.pts = [m @ p for p in f.pts]

            if flip:
                f.pts.reverse()

        return self

    def rot(self, deg, axis="Z", pivot=(0, 0, 0)):
        p = Vector(pivot)

        return self.xform(Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p))

    def mirror(self, axis=0):
        s = [1.0, 1.0, 1.0]
        s[axis] = -1.0

        return self.xform(Matrix.Diagonal((s[0], s[1], s[2], 1.0)))

    def copy(self):
        return Part(Poly(f.pts, f.col, f.smooth, f.ao, f.cast) for f in self)

    def paint(self, col):
        for f in self:
            f.col = rgb(col)

        return self


def keep(dims, d):
    if d is not None:
        return LOD <= d

    if LOD == 0:
        return True

    s = sorted(dims)

    return s[1] >= SIZE_CUT[LOD]


def sides_for(n):
    if LOD == 0:
        return n

    return max(3 if n < 5 else 4, int(round(n * SIDE_SCALE[LOD])))


def box(x0, y0, z0, x1, y1, z1, col, c=0.0, top=None, skip="", d=None, taper=(1.0, 1.0), ao=True, cast=True, shear=(0.0, 0.0)):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    out = Part()

    if not keep((x1 - x0, y1 - y0, z1 - z0), d):
        return out

    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy, hz = (x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2
    topc = col if top is None else top

    def warp(p):
        t = (p[2] - z0) / max(z1 - z0, 1e-6)
        sx = 1 + (taper[0] - 1) * t
        sy = 1 + (taper[1] - 1) * t

        return (cx + (p[0] - cx) * sx + shear[0] * t, cy + (p[1] - cy) * sy + shear[1] * t, p[2])

    def add(pts, colour, tag):
        if tag and tag in skip:
            return

        out.append(Poly([warp(p) for p in pts], colour, False, ao, cast))

    if LOD > 0 or c <= 0 or min(hx, hy, hz) < c * 1.2:
        add([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], col, "f")
        add([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], col, "b")
        add([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], col, "l")
        add([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], col, "r")
        add([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], topc, "t")
        add([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], col, "d")

        return out

    h = (hx, hy, hz)
    mid = (cx, cy, (z0 + z1) / 2)

    def v(sx, sy, sz, axis):
        s = (sx, sy, sz)

        return tuple(mid[i] + s[i] * (h[i] - (0 if i == axis else c)) for i in range(3))

    tags = {(0, -1): "l", (0, 1): "r", (1, -1): "f", (1, 1): "b", (2, -1): "d", (2, 1): "t"}

    for axis in range(3):
        a, b = [i for i in range(3) if i != axis]

        for s in (-1, 1):
            ring = []

            for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                sg = [0, 0, 0]
                sg[axis] = s
                sg[a] = sa
                sg[b] = sb
                ring.append(v(sg[0], sg[1], sg[2], axis))

            if (s > 0) == (axis == 1):
                ring.reverse()

            add(ring, topc if (axis == 2 and s > 0) else col, tags[(axis, s)])

    for a, b in ((0, 1), (0, 2), (1, 2)):
        o = 3 - a - b

        for sa in (-1, 1):
            for sb in (-1, 1):
                if (a == 2 and tags[(a, sa)] in skip) or (b == 2 and tags[(b, sb)] in skip):
                    continue

                sg = [0, 0, 0]
                sg[a] = sa
                sg[b] = sb
                sg[o] = -1
                p0 = v(sg[0], sg[1], sg[2], a)
                p1 = v(sg[0], sg[1], sg[2], b)
                sg[o] = 1
                p2 = v(sg[0], sg[1], sg[2], b)
                p3 = v(sg[0], sg[1], sg[2], a)
                pts = [p0, p1, p2, p3]
                f = Poly([warp(p) for p in pts], topc if (b == 2 and sb > 0) else col, False, ao, cast)
                outward = Vector((0, 0, 0))
                outward[a] = sa
                outward[b] = sb

                if f.normal().dot(outward) < 0:
                    f.pts.reverse()

                out.append(f)

    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                if sz < 0 and "d" in skip:
                    continue

                pts = [v(sx, sy, sz, 0), v(sx, sy, sz, 1), v(sx, sy, sz, 2)]
                f = Poly([warp(p) for p in pts], topc if sz > 0 else col, False, ao, cast)

                if f.normal().dot(Vector((sx, sy, sz))) < 0:
                    f.pts.reverse()

                out.append(f)

    return out


def cbox(w, dp, h, at, col, **kw):
    x, y, z = at

    return box(x - w / 2, y - dp / 2, z, x + w / 2, y + dp / 2, z + h, col, **kw)


def basis(t):
    a = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
    u = a.cross(t).normalized()
    v = t.cross(u).normalized()

    return u, v


def tube(pts, radii, sides, col, caps=(False, True), smooth=True, d=None, squash=(1.0, 1.0), phase=0.0, ao=True, cast=True):
    pts = [Vector(p) for p in pts]
    out = Part()

    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(pts)

    length = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))

    if not keep((max(radii) * 2, max(radii) * 2, length), d):
        return out

    if LOD == 2 and len(pts) > 3:
        idx = list(range(0, len(pts), 2))

        if idx[-1] != len(pts) - 1:
            idx.append(len(pts) - 1)

        pts = [pts[i] for i in idx]
        radii = [radii[i] for i in idx]

    n = sides_for(sides)
    rings = []
    u = None

    for j, p in enumerate(pts):
        t = (pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]).normalized()

        if u is None:
            u, v = basis(t)
        else:
            v = t.cross(u).normalized()
            u = v.cross(t).normalized()

        ring = []

        for i in range(n):
            a = 2 * math.pi * i / n + phase
            ring.append(p + u * (math.cos(a) * radii[j] * squash[0]) + v * (math.sin(a) * radii[j] * squash[1]))

        rings.append(ring)

    def colour(i, j):
        return col(i, j) if callable(col) else col

    for j in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            quad = [rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]]
            clean = [quad[0]]

            for q in quad[1:]:
                if (q - clean[-1]).length > 1e-5:
                    clean.append(q)

            if len(clean) > 2 and (clean[0] - clean[-1]).length < 1e-5:
                clean.pop()

            if len(clean) > 2:
                out.append(Poly(clean, colour(i, j), smooth, ao, cast))

    if caps[0] and radii[0] > 1e-4:
        out.append(Poly(list(reversed(rings[0])), caps[0] if isinstance(caps[0], str) else colour(0, 0), False, ao, cast))

    if caps[1] and radii[-1] > 1e-4:
        out.append(Poly(rings[-1], caps[1] if isinstance(caps[1], str) else colour(0, len(rings) - 2), False, ao, cast))

    return out


def bar(a, b, r, col, sides=6, taper=1.0, caps=(True, True), **kw):
    return tube([a, b], [r, r * taper], sides, col, caps=caps, **kw)


def cyl(at, r, h, col, sides=10, rt=None, smooth=True, caps=(False, True), d=None, **kw):
    x, y, z = at

    return tube([(x, y, z), (x, y, z + h)], [r, r if rt is None else rt], sides, col, caps=caps, smooth=smooth, d=d, **kw)


def lathe(profile, sides, at=(0, 0, 0), smooth=True, d=None, phase=0.0, squash=(1.0, 1.0)):
    x, y, z = at
    out = Part()
    rmax = max(p[0] for p in profile)
    zs = [p[1] for p in profile]

    if not keep((rmax * 2, rmax * 2, max(zs) - min(zs)), d):
        return out

    n = sides_for(sides)

    for j in range(len(profile) - 1):
        r0, z0, col = profile[j]
        r1, z1 = profile[j + 1][0], profile[j + 1][1]

        for i in range(n):
            a0 = 2 * math.pi * i / n + phase
            a1 = 2 * math.pi * (i + 1) / n + phase
            pts = []

            for r, zz, a in ((r0, z0, a0), (r0, z0, a1), (r1, z1, a1), (r1, z1, a0)):
                p = Vector((x + math.cos(a) * r * squash[0], y + math.sin(a) * r * squash[1], z + zz))

                if not pts or (p - pts[-1]).length > 1e-5:
                    pts.append(p)

            if len(pts) > 2 and (pts[0] - pts[-1]).length < 1e-5:
                pts.pop()

            if len(pts) > 2:
                c = col(i) if callable(col) else col
                out.append(Poly(pts, c, smooth, True, True))

    return out


def extrude(outline, y0, y1, col, d=None, side=None, caps="fb", ao=True, cast=True, force=False):
    out = Part()
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]

    if not force and not keep((max(xs) - min(xs), abs(y1 - y0), max(zs) - min(zs)), d):
        return out

    area = sum(outline[i][0] * outline[(i + 1) % len(outline)][1] - outline[(i + 1) % len(outline)][0] * outline[i][1] for i in range(len(outline)))
    pts = list(outline) if area > 0 else list(reversed(outline))
    y0, y1 = min(y0, y1), max(y0, y1)
    n = len(pts)

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        c = side(i, a, b) if callable(side) else (side or col)

        if c is None:
            continue

        out.append(Poly([(a[0], y0, a[1]), (a[0], y1, a[1]), (b[0], y1, b[1]), (b[0], y0, b[1])], c, False, ao, cast))

    convex = all((pts[(i + 1) % n][0] - pts[i][0]) * (pts[(i + 2) % n][1] - pts[(i + 1) % n][1]) - (pts[(i + 1) % n][1] - pts[i][1]) * (pts[(i + 2) % n][0] - pts[(i + 1) % n][0]) >= -1e-9 for i in range(n))

    if convex:
        tris = [list(range(n))]
    else:
        tris = [list(t) for t in tessellate_polygon([[Vector((p[0], p[1], 0)) for p in pts]])]

    for t in tris:
        for y, tag, face in ((y0, "f", -1), (y1, "b", 1)):
            if tag not in caps:
                continue

            f = Poly([(pts[i][0], y, pts[i][1]) for i in t], col, False, ao, cast)

            if f.normal().y * face < 0:
                f.pts.reverse()

            out.append(f)

    return out


def prism(outline, z0, z1, col, c=0.0, d=None, top=None, bottom=False, ao=True, cast=True):
    out = Part()
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]

    if not keep((max(xs) - min(xs), max(ys) - min(ys), z1 - z0), d):
        return out

    n = len(outline)
    area = sum(outline[i][0] * outline[(i + 1) % n][1] - outline[(i + 1) % n][0] * outline[i][1] for i in range(n))
    pts = list(outline) if area > 0 else list(reversed(outline))
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    zt = z1 - c if (c > 0 and LOD == 0) else z1

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        out.append(Poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], zt), (a[0], a[1], zt)], col, False, ao, cast))

    cap = pts

    if zt < z1:
        cap = []

        for p in pts:
            dx, dy = p[0] - cx, p[1] - cy
            ln = math.hypot(dx, dy)
            k = max(0.0, 1 - c * 1.3 / max(ln, 1e-4))
            cap.append((cx + dx * k, cy + dy * k))

        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            e, f = cap[(i + 1) % n], cap[i]
            out.append(Poly([(a[0], a[1], zt), (b[0], b[1], zt), (e[0], e[1], z1), (f[0], f[1], z1)], top or col, False, ao, cast))

    out.append(Poly([(p[0], p[1], z1) for p in cap], top or col, False, ao, cast))

    if bottom:
        out.append(Poly([(p[0], p[1], z0) for p in reversed(pts)], col, False, ao, cast))

    return out


def ngon(r, n, cx=0.0, cy=0.0, phase=None, ry=None):
    ph = math.pi / n if phase is None else phase

    return [(cx + math.cos(2 * math.pi * i / n + ph) * r, cy + math.sin(2 * math.pi * i / n + ph) * (r if ry is None else ry)) for i in range(n)]


def quad(pts, col, double=False, d=None, ao=True, cast=True, smooth=False):
    out = Part()

    if d is not None and LOD > d:
        return out

    out.append(Poly(pts, col, smooth, ao, cast))

    if double:
        n = out[0].normal()
        out.append(Poly([Vector(p) - n * 0.012 for p in reversed(pts)], col, smooth, ao, cast))

    return out


def sheet(grid, col, thick=0.015, d=None, ao=True):
    out = Part()
    rows = len(grid)
    cols = len(grid[0])

    if d is not None and LOD > d:
        return out

    step_c = 1 if LOD == 0 else 2
    ci = list(range(0, cols, step_c))
    ri = list(range(0, rows, step_c))

    if ci[-1] != cols - 1:
        ci.append(cols - 1)

    if ri[-1] != rows - 1:
        ri.append(rows - 1)

    g = [[Vector(grid[r][c]) for c in ci] for r in ri]

    for r in range(len(g) - 1):
        for c in range(len(g[0]) - 1):
            pts = [g[r][c], g[r][c + 1], g[r + 1][c + 1], g[r + 1][c]]
            colour = col(ci[c], ri[r]) if callable(col) else col
            n = Poly(pts, colour).normal()

            for tri in ((pts[0], pts[1], pts[2]), (pts[0], pts[2], pts[3])):
                if (tri[1] - tri[0]).cross(tri[2] - tri[0]).length < 1e-6:
                    continue

                out.append(Poly(tri, colour, False, ao, True))
                out.append(Poly([p - n * thick for p in reversed(tri)], shade(colour, 0.86), False, ao, True))

    return out


ICO = None


def ico(level):
    t = (1 + 5 ** 0.5) / 2
    vs = [Vector(v).normalized() for v in ((-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1))]
    fs = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]

    for _ in range(level):
        cache = {}
        nf = []

        def mid(a, b):
            key = (min(a, b), max(a, b))

            if key not in cache:
                cache[key] = len(vs)
                vs.append(((vs[a] + vs[b]) / 2).normalized())

            return cache[key]

        for a, b, c in fs:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]

        fs = nf

    return vs, fs


def blob(at, size, tones, sub=1, jitter=0.14, seed=0, flat=None, d=None, smooth=False, accent=None, accent_p=0.0, spin=None):
    out = Part()

    if not keep((size[0] * 2, size[1] * 2, size[2] * 2), d):
        return out

    level = max(0, sub - LOD)
    vs, fs = ico(level)
    r = random.Random(seed)
    m = Matrix.Rotation(r.uniform(0, 6.28) if spin is None else spin, 4, "Z")
    pts = []

    for v in vs:
        f = 1 + r.uniform(-jitter, jitter)
        n = m @ v
        p = Vector((n.x * size[0] * f, n.y * size[1] * f, n.z * size[2] * f))

        if flat is not None and p.z < -flat * size[2]:
            p.z = -flat * size[2]

        pts.append(p + Vector(at))

    if isinstance(tones, str):
        tones = (tones, tones, tones)

    for k, (a, b, c) in enumerate(fs):
        poly = Poly([pts[a], pts[b], pts[c]], tones[1], smooth)
        n = poly.normal()
        h = hash01(seed, k, 3.1)
        tone = tones[0] if n.z > 0.45 else tones[1] if n.z > -0.15 else tones[2]

        if h > 0.86:
            tone = tones[1] if tone == tones[0] else tones[2]
        elif h < 0.1:
            tone = tones[0]

        if accent and n.z > -0.1 and hash01(seed, k, 7.7) < accent_p:
            tone = accent

        poly.col = rgb(tone)
        out.append(poly)

    return out


def torus(center, R, r, col, segs=14, sides=6, axis="Y", d=None, arc=1.0):
    out = Part()

    if not keep((R * 2, R * 2, r * 2), d):
        return out

    n = sides_for(segs)
    m = sides_for(sides)
    rings = []

    for i in range(int(n * arc) + (0 if arc >= 1 else 1)):
        a = 2 * math.pi * i / n
        ring = []

        for j in range(m):
            b = 2 * math.pi * j / m
            rr = R + r * math.cos(b)
            ring.append(Vector((math.cos(a) * rr, math.sin(a) * rr, math.sin(b) * r)))

        rings.append(ring)

    count = len(rings) if arc >= 1 else len(rings) - 1

    for i in range(count):
        i2 = (i + 1) % len(rings)

        for j in range(m):
            j2 = (j + 1) % m
            c = col(i / n) if callable(col) else col
            out.append(Poly([rings[i][j], rings[i2][j], rings[i2][j2], rings[i][j2]], c, True))

    rot = Matrix.Identity(4)

    if axis == "Y":
        rot = Matrix.Rotation(math.radians(90), 4, "X")
    elif axis == "X":
        rot = Matrix.Rotation(math.radians(90), 4, "Y")

    return out.xform(Matrix.Translation(Vector(center)) @ rot)


def join(item):
    out = Part()

    for it in item:
        if isinstance(it, Poly):
            out.append(it)
        else:
            out.extend(join(it))

    return out


def hemisphere(n):
    out = []
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        z = 1 - (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * golden
        out.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))

    return out


DIRS = hemisphere(32)


def tree_of(polys):
    verts = []
    faces = []

    for f in polys:
        if not f.cast:
            continue

        base = len(verts)
        verts.extend(f.pts)
        faces.append(list(range(base, base + len(f.pts))))

    if not faces:
        return None

    return BVHTree.FromPolygons(verts, faces)


def cull(polys, tree, ground):
    out = []

    for f in polys:
        n = f.normal()
        c = f.center()

        if ground and n.z < -0.9 and max(p.z for p in f.pts) < 0.02:
            continue

        if tree is None:
            out.append(f)
            continue

        pts = [c] + [c.lerp(p, 0.92) for p in f.pts]

        if all(tree.ray_cast(p + n * 0.0015, n, 0.012)[0] is not None for p in pts):
            continue

        out.append(f)

    return out


class Baker:
    def __init__(self, tree, opts):
        self.tree = tree
        self.reach = opts.get("reach", 1.5)
        self.strength = opts.get("ao", 0.55)
        self.ground = opts.get("ground", True)
        self.grime = opts.get("grime", 0.14)
        self.grime_h = opts.get("grime_h", 0.8)
        self.under = opts.get("under", 0.14)
        self.cache = {}

    def occlusion(self, p, n):
        if self.tree is None:
            return 0.0

        key = (round(p.x, 2), round(p.y, 2), round(p.z, 2), round(n.x, 1), round(n.y, 1), round(n.z, 1))
        got = self.cache.get(key)

        if got is not None:
            return got

        t, b = basis(n)
        start = p + n * 0.02
        hit = 0.0

        for d in DIRS:
            w = t * d.x + b * d.y + n * d.z
            loc, _, _, dist = self.tree.ray_cast(start, w, self.reach)
            best = dist if loc is not None else None

            if self.ground and w.z < -0.02 and start.z > -0.01:
                g = start.z / -w.z

                if g < self.reach and (best is None or g < best):
                    best = g

            if best is not None:
                hit += (1 - best / self.reach) ** 0.7

        occ = hit / len(DIRS)
        self.cache[key] = occ

        return occ

    def factor(self, p, n, ao):
        k = 1.0

        if ao:
            k -= self.strength * min(1.0, self.occlusion(p, n) * 1.25)

        if self.ground and self.grime:
            k *= 1 - self.grime * max(0.0, 1 - max(p.z, 0.0) / self.grime_h) * (1 - max(0.0, n.z))

        k *= 1 - self.under * max(0.0, -n.z)

        return max(0.36, k)


def inset_point(p, c):
    d = c - p
    ln = d.length

    if ln < 1e-5:
        return p

    return p + d * (min(ln * 0.3, 0.22) / ln)


def render_mesh(polys, baker, opts):
    speckle = opts.get("speckle", 0.025)
    top = opts.get("top", 1.0)
    zs = [p.z for f in polys for p in f.pts]
    lo, hi = min(zs), max(zs)
    smooth_normals = {}

    for f in polys:
        if f.smooth:
            n = f.normal()

            for p in f.pts:
                smooth_normals.setdefault((round(p.x, 4), round(p.y, 4), round(p.z, 4)), []).append((n, f.col))

    verts = {}
    data = []
    index = []

    for f in polys:
        n = f.normal()
        c = f.center()
        k_face = 1.0

        if speckle and not f.smooth:
            k_face = 1 + (hash01(c.x, c.y, c.z) - 0.5) * 2 * speckle

        corner = []
        floor_k = 0.0

        if not f.smooth:
            size = max((p - c).length for p in f.pts)

            if size > 0.3:
                spread = 0.36 - 0.28 * min(1.0, (size - 0.3) / 1.0)
                lifted = c + n * 0.0
                floor_k = baker.factor(lifted, n, f.ao) - spread

        for p in f.pts:
            vn = n

            if f.smooth:
                near = [m for m, _ in smooth_normals[(round(p.x, 4), round(p.y, 4), round(p.z, 4))] if m.dot(n) > 0.72]
                acc = Vector((0, 0, 0))

                for m in near:
                    acc += m

                vn = acc.normalized() if acc.length > 1e-6 else n
                sample = p
            else:
                sample = inset_point(p, c)

            k = max(baker.factor(sample, vn, f.ao), floor_k) * k_face

            if top != 1.0:
                k *= 0.95 + (top - 0.95) * (p.z - lo) / max(hi - lo, 1e-4)

            col = tuple(max(0, min(255, int(round(f.col[i] * k * 255 / 2.0)) * 2)) for i in range(3))
            gp = (round(p.x, 4), round(p.z, 4), round(-p.y, 4))
            gn = (round(vn.x, 2), round(vn.z, 2), round(-vn.y, 2))
            key = (gp, gn, col)
            j = verts.get(key)

            if j is None:
                j = len(data)
                verts[key] = j
                data.append(key)

            corner.append(j)

        if len(f.pts) == 3:
            tris = [(0, 1, 2)]
        elif len(f.pts) == 4:
            a = Vector(data[corner[0]][2])
            b = Vector(data[corner[2]][2])
            c1 = Vector(data[corner[1]][2])
            d = Vector(data[corner[3]][2])
            tris = [(0, 1, 2), (0, 2, 3)] if (a - b).length <= (c1 - d).length else [(0, 1, 3), (1, 2, 3)]
        else:
            m = len(f.pts)
            t, bt = basis(n)
            flat = [Vector((p.dot(t), p.dot(bt), 0)) for p in f.pts]
            tris = []

            for tri in tessellate_polygon([flat]):
                a, b, cc = (f.pts[i] for i in tri)

                if (b - a).cross(cc - a).dot(n) < 0:
                    tri = (tri[0], tri[2], tri[1])

                tris.append(tuple(tri))

            if len(tris) < m - 2:
                tris = [(0, i, i + 1) for i in range(1, m - 1)]

        for a, b, cc in tris:
            ids = (corner[a], corner[b], corner[cc])

            if len(set(ids)) == 3:
                index.extend(ids)

    return data, index


def write_glb(path, data, index):
    assert len(data) <= 65535, path
    reach = max(max(abs(c) for c in v[0]) for v in data)
    step = max(reach, 1e-3) / 32767.0
    pos = b"".join(struct.pack("<4h", *[int(round(c / step)) for c in v[0]], 0) for v in data)
    nrm = b"".join(struct.pack("<4b", *[max(-127, min(127, int(round(c * 127)))) for c in v[1]], 0) for v in data)
    col = b"".join(struct.pack("<4B", v[2][0], v[2][1], v[2][2], 255) for v in data)
    ind = struct.pack("<%dH" % len(index), *index)
    blob_ = bytearray()
    views = []

    for i, chunk in enumerate((pos, nrm, col, ind)):
        while len(blob_) % 4:
            blob_.append(0)

        view = {"buffer": 0, "byteOffset": len(blob_), "byteLength": len(chunk), "target": 34963 if i == 3 else 34962}

        if i < 2:
            view["byteStride"] = 8 if i == 0 else 4

        views.append(view)
        blob_.extend(chunk)

    while len(blob_) % 4:
        blob_.append(0)

    mn = [min(v[0][i] for v in data) for i in range(3)]
    mx = [max(v[0][i] for v in data) for i in range(3)]
    qn = [int(round(c / step)) for c in mn]
    qx = [int(round(c / step)) for c in mx]
    doc = {
        "extensionsUsed": ["KHR_mesh_quantization"],
        "extensionsRequired": ["KHR_mesh_quantization"],
        "asset": {"version": "2.0", "generator": "dronefire coastkit"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "scale": [step, step, step]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2}, "indices": 3, "material": 0}]}],
        "materials": [{"name": "kit", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}],
        "buffers": [{"byteLength": len(blob_)}],
        "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5122, "count": len(data), "type": "VEC3", "min": qn, "max": qx},
            {"bufferView": 1, "componentType": 5120, "normalized": True, "count": len(data), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "normalized": True, "count": len(data), "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": len(index), "type": "SCALAR"},
        ],
    }
    js = json.dumps(doc, separators=(",", ":")).encode()

    while len(js) % 4:
        js += b" "

    total = 12 + 8 + len(js) + 8 + len(blob_)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob_), 0x004E4942) + bytes(blob_))

    return mn, mx
