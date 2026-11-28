import math
import random

import lk
from mathutils import Matrix, Vector

box = lk.box
bar = lk.bar
tube = lk.tube
cyl = lk.cyl
lathe = lk.lathe
prism = lk.prism
ngon = lk.ngon
extrude = lk.extrude
blob = lk.blob
Part = lk.Part
Poly = lk.Poly


def part():
    return Part()


def face(pts, col, d=None, ao=True, cast=True, towards=None):
    out = Part()

    if d is not None and lk.LOD > d:
        return out

    f = Poly(pts, col, False, ao, cast)

    if towards is not None and f.normal().dot(Vector(towards)) < 0:
        f.pts.reverse()

    out.append(f)

    return out


def plate(x0, x1, z0, z1, y, col, d=None, ao=True, cast=False):
    return face([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col, d, ao, cast, (0, -1, 0))


def deck(x0, x1, y0, y1, z, col, d=None, ao=True, cast=False):
    return face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], col, d, ao, cast, (0, 0, 1))


def side(y0, y1, z0, z1, x, sign, col, d=None, ao=True, cast=False):
    return face([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], col, d, ao, cast, (sign, 0, 0))


def front(x0, x1, z0, z1, y, col, depth=0.015, c=0.0, d=None):
    return box(x0, y - depth, z0, x1, y, z1, col, c=c, skip="b", d=d)


def handle(x, z, length, y, col="steel_lt", vertical=False, d=0):
    if vertical:
        return box(x - 0.008, y - 0.028, z - length / 2, x + 0.008, y, z + length / 2, col, skip="b", d=d)

    return box(x - length / 2, y - 0.025, z - 0.008, x + length / 2, y, z + 0.008, col, skip="b", d=d)


def frame(x0, x1, z0, z1, y, w, col, depth=0.02, d=None):
    out = Part()
    out += box(x0, y - depth, z0, x1, y, z0 + w, col, skip="b", d=d)
    out += box(x0, y - depth, z1 - w, x1, y, z1, col, skip="b", d=d)
    out += box(x0, y - depth, z0 + w, x0 + w, y, z1 - w, col, skip="btd", d=d)
    out += box(x1 - w, y - depth, z0 + w, x1, y, z1 - w, col, skip="btd", d=d)

    return out


def louvres(x0, x1, z0, z1, y, n, slat, back="black", depth=0.04, d=1):
    out = Part()
    out += plate(x0, x1, z0, z1, y - 0.004, back, d=None)

    if lk.LOD >= 2:
        for i in range(max(1, n // 3)):
            za = z0 + (z1 - z0) * (i + 0.25) / max(1, n // 3)
            out += plate(x0, x1, za, za + (z1 - z0) / max(1, n // 3) * 0.4, y - 0.012, slat)

        return out

    step = (z1 - z0) / n

    for i in range(n):
        za = z0 + step * i + step * 0.18
        zb = za + step * 0.55
        out += face([(x0, y - depth, za), (x1, y - depth, za), (x1, y - 0.006, zb), (x0, y - 0.006, zb)], slat, d, True, False, (0, -1, 0.5))
        out += face([(x0, y - 0.006, za - step * 0.04), (x1, y - 0.006, za - step * 0.04), (x1, y - depth, za), (x0, y - depth, za)], "slate_dk", 0, True, False, (0, -1, -1))

    return out


def disc(cx, cz, y, r, col, n=8, depth=0.012, d=None, rim=None):
    m = lk.sides_for(n) if lk.LOD else n
    pts = [(cx + math.cos(2 * math.pi * (i + 0.5) / m) * r, cz + math.sin(2 * math.pi * (i + 0.5) / m) * r) for i in range(m)]

    return extrude(pts, y - depth, y, col, d=d, side=rim or col, caps="f")


def ring(cx, cz, y, r0, r1, col, n=8, depth=0.05, d=None, phase=None, side=None):
    out = Part()

    if d is not None and lk.LOD > d:
        return out

    ph = math.pi / n if phase is None else phase
    outer = [(cx + math.cos(2 * math.pi * i / n + ph) * r1, cz + math.sin(2 * math.pi * i / n + ph) * r1) for i in range(n)]
    inner = [(cx + math.cos(2 * math.pi * i / n + ph) * r0, cz + math.sin(2 * math.pi * i / n + ph) * r0) for i in range(n)]
    sc = side or col

    for i in range(n):
        j = (i + 1) % n
        a, b, c, e = outer[i], outer[j], inner[j], inner[i]
        out += face([(a[0], y - depth, a[1]), (b[0], y - depth, b[1]), (c[0], y - depth, c[1]), (e[0], y - depth, e[1])], col, towards=(0, -1, 0))
        mid = ((a[0] + b[0]) / 2 - cx, 0, (a[1] + b[1]) / 2 - cz)
        out += face([(a[0], y - depth, a[1]), (b[0], y - depth, b[1]), (b[0], y, b[1]), (a[0], y, a[1])], sc, towards=mid)

        if lk.LOD == 0:
            out += face([(e[0], y - depth, e[1]), (c[0], y - depth, c[1]), (c[0], y, c[1]), (e[0], y, e[1])], sc, towards=(-mid[0], 0, -mid[2]))

    return out


def puck(at, r, h, col, sides=8, top=None, d=None, rt=None):
    return cyl(at, r, h, col, sides=sides, smooth=False, caps=(False, top or col), d=d, rt=rt)


def rod(a, b, r, col, sides=4, d=None, caps=(False, False)):
    return tube([a, b], [r, r], sides, col, caps=caps, smooth=False, d=d, phase=math.pi / 4)


def loft(rings, cols, close=True, caps=(None, None), d=None, smooth=False, outward=None, wind=False):
    out = Part()

    if d is not None and lk.LOD > d:
        return out

    n = len(rings[0])

    for j in range(len(rings) - 1):
        mid = Vector((0, 0, 0))

        for p in rings[j] + rings[j + 1]:
            mid += Vector(p)

        mid /= 2 * n

        for i in range(n if close else n - 1):
            k = (i + 1) % n
            pts = []

            for p in (rings[j][i], rings[j][k], rings[j + 1][k], rings[j + 1][i]):
                p = Vector(p)

                if not pts or (p - pts[-1]).length > 1e-5:
                    pts.append(p)

            if len(pts) > 2 and (pts[0] - pts[-1]).length < 1e-5:
                pts.pop()

            if len(pts) < 3:
                continue

            col = cols(j, i) if callable(cols) else cols
            f = Poly(pts, col, smooth)
            ref = f.center() - (Vector(outward) if outward is not None else mid)

            if not wind and f.normal().dot(ref) < 0:
                f.pts.reverse()

            out.append(f)

    for end, cap in zip((0, -1), caps):
        if cap is None:
            continue

        f = Poly(rings[end], cap, False)
        other = rings[1 if end == 0 else -2]
        a = sum((Vector(p) for p in rings[end]), Vector()) / n
        b = sum((Vector(p) for p in other), Vector()) / n

        if f.normal().dot(a - b) < 0:
            f.pts.reverse()

        out.append(f)

    return out


def circle(r, n, z, cx=0.0, cy=0.0, phase=None, ry=None):
    ph = math.pi / n if phase is None else phase

    return [(cx + math.cos(2 * math.pi * i / n + ph) * r, cy + math.sin(2 * math.pi * i / n + ph) * (r if ry is None else ry), z) for i in range(n)]


def mirror_y(p):
    return p.copy().rot(180, "Z")


def rng(seed):
    return random.Random(seed)
