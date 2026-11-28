import math
import random

from mathutils import Vector

import arch as a
import ck

GLYPHS = {
    "A": "00,03,14,23,20 01,21",
    "B": "00,04,14,23,12,21,10,00 02,12",
    "C": "24,04,00,20",
    "D": "00,04,14,23,21,10,00",
    "E": "24,04,00,20 02,12",
    "F": "24,04,00 02,12",
    "G": "24,04,00,20,22,12",
    "H": "00,04 20,24 02,22",
    "I": "10,14 00,20 04,24",
    "K": "00,04 24,02,20",
    "L": "04,00,20",
    "M": "00,04,12,24,20",
    "N": "00,04,20,24",
    "O": "00,04,24,20,00",
    "P": "00,04,24,22,02",
    "R": "00,04,24,22,02 12,20",
    "S": "24,04,02,22,20,00",
    "T": "04,24 14,10",
    "U": "04,00,20,24",
    "V": "04,10,24",
    "X": "00,24 04,20",
    "W": "04,00,12,20,24",
    "Y": "04,12,24 12,10",
    "0": "00,04,24,20,00",
    "1": "03,14,10 00,20",
    "2": "04,24,22,02,00,20",
    "3": "04,24,20,00 02,22",
    "4": "04,02,22 24,20",
    "5": "24,04,02,22,20,00",
    "6": "24,04,00,20,22,02",
    "7": "04,24,10",
    "8": "00,04,24,20,00 02,22",
    "9": "20,24,04,02,22",
}


def stroke(p, q, y, t, col):
    p = Vector((p[0], 0, p[1]))
    q = Vector((q[0], 0, q[1]))
    d = q - p

    if d.length < 1e-5:
        return ck.Part()

    d.normalize()
    s = Vector((-d.z, 0, d.x)) * (t / 2)
    p = p - d * (t / 2)
    q = q + d * (t / 2)
    pts = [p - s, q - s, q + s, p + s]
    off = Vector((0, y, 0))
    f = ck.Poly([v + off for v in pts], col, False, False, False)

    if f.normal().y > 0:
        f.pts.reverse()

    return ck.Part([f])


def text(word, cx, y, z, h, col, w=None, t=None, gap=0.3):
    out = ck.Part()
    gw = h * 0.5
    sp = h * gap
    space = h * 0.35
    total = sum(space if ch == " " else gw + sp for ch in word) - sp

    if w and total > w:
        k = w / total
    else:
        k = 1.0

    t = (t or h * 0.15) * max(k, 0.8)

    if ck.LOD >= 2:
        out.append(ck.Poly([(cx - total * k / 2, y, z + h * 0.2), (cx + total * k / 2, y, z + h * 0.2), (cx + total * k / 2, y, z + h * 0.8), (cx - total * k / 2, y, z + h * 0.8)], col, False, False, False))

        return out

    cur = cx - total * k / 2
    n = 0

    for ch in word:
        if ch == " ":
            cur += space * k
            continue

        for path in GLYPHS[ch].split():
            pts = [(cur + int(c[0]) / 2 * gw * k, z + int(c[1]) / 4 * h) for c in path.split(",")]

            for p, q in zip(pts, pts[1:]):
                out += stroke(p, q, y - 0.0004 * (n % 5), t, col)
                n += 1

        cur += (gw + sp) * k

    return out


def face(pts, col, toward, ao=True, cast=True, smooth=False):
    f = ck.Poly(pts, col, smooth, ao, cast)

    if f.normal().dot(Vector(toward)) < 0:
        f.pts.reverse()

    return ck.Part([f])


def plate(x0, x1, z0, z1, y, col, toward=-1, d=None):
    if d is not None and ck.LOD > d:
        return ck.Part()

    return face([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col, (0, toward, 0))


def roundrect(x0, y0, x1, y1, r, n=4):
    if ck.LOD == 1:
        n = max(2, n // 2)

    if ck.LOD == 2:
        n = 1

    out = []

    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            ang = math.radians(a0 + 90 * i / n)
            out.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))

    return out


def slabs(rings, col, top=None, bottom=None):
    out = ck.Part()

    for k, ((pa, za), (pb, zb)) in enumerate(zip(rings, rings[1:])):
        c = col[k] if isinstance(col, (list, tuple)) and not isinstance(col[0], float) else col
        n = len(pa)

        for i in range(n):
            j = (i + 1) % n
            pts = [(pa[i][0], pa[i][1], za), (pa[j][0], pa[j][1], za), (pb[j][0], pb[j][1], zb), (pb[i][0], pb[i][1], zb)]
            uniq = []

            for p in pts:
                if not uniq or (Vector(p) - Vector(uniq[-1])).length > 1e-4:
                    uniq.append(p)

            if len(uniq) > 2 and (Vector(uniq[0]) - Vector(uniq[-1])).length < 1e-4:
                uniq.pop()

            if len(uniq) > 2:
                out.append(ck.Poly(uniq, c))

    if top:
        p, z = rings[-1]
        out.append(ck.Poly([(q[0], q[1], z) for q in p], top))

    if bottom:
        p, z = rings[0]
        out.append(ck.Poly([(q[0], q[1], z) for q in reversed(p)], bottom))

    return out


def ledge(poly, z0, z1, d, col, top=None, c=0.025):
    if top:
        return a.band(poly, z0, z1, d, col, c=c, top=top)

    out = a.band(poly, z0, z1, d, col, c=c, cap=False)
    outer = a.offset(poly, d - (c if ck.LOD == 0 else 0.0))
    inner = a.offset(poly, -0.02)
    n = len(poly)

    for i in range(n):
        j = (i + 1) % n
        out += face([(outer[i][0], outer[i][1], z1), (outer[j][0], outer[j][1], z1), (inner[j][0], inner[j][1], z1), (inner[i][0], inner[i][1], z1)], col, (0, 0, 1))

    return out


def vent_pipe(x, y, z, h, col="steel_dk"):
    out = ck.cyl((x, y, z), 0.11, h, col, sides=8, caps=(False, True), d=1)
    out += ck.cyl((x, y, z + h), 0.2, 0.09, "steel", sides=8, rt=0.12, caps=(True, True), d=1)

    return out


def ac_unit(x, y, z, w=0.9, dp=0.8, h=0.45):
    out = ck.box(x - w / 2, y - dp / 2, z + 0.08, x + w / 2, y + dp / 2, z + h, "steel_lt", c=0.04, d=1)
    out += ck.box(x - w / 2 + 0.08, y - dp / 2 + 0.08, z, x + w / 2 - 0.08, y + dp / 2 - 0.08, z + 0.1, "iron", d=1)
    out += ck.cyl((x + w * 0.18, y, z + h), min(w, dp) * 0.28, 0.04, "iron_lt", sides=8, caps=(False, True), d=0)

    for i in range(3):
        zz = z + 0.15 + i * (h - 0.2) / 3
        out += ck.box(x - w / 2 + 0.1, y - dp / 2 - 0.015, zz, x + w * 0.1, y - dp / 2 + 0.01, zz + 0.05, "iron_lt", d=0, skip="b")

    return out


def wall_vent(x, y, z, w=0.45, h=0.32, facing=-1):
    y0, y1 = sorted((y, y + facing * 0.06))
    out = ck.box(x - w / 2, y0, z, x + w / 2, y1, z + h, "iron_lt", c=0.015, d=1)

    for i in range(3):
        zz = z + 0.05 + i * (h - 0.08) / 3
        s0, s1 = sorted((y + facing * 0.05, y + facing * 0.085))
        out += ck.box(x - w / 2 + 0.05, s0, zz, x + w / 2 - 0.05, s1, zz + 0.035, "iron_dk", d=0)

    return out


def lantern(x, y, z, facing=-1):
    y0, y1 = sorted((y, y + facing * 0.16))
    out = ck.box(x - 0.09, y0, z + 0.14, x + 0.09, y1, z + 0.2, "iron", d=0)
    s0, s1 = sorted((y + facing * 0.04, y + facing * 0.14))
    out += ck.box(x - 0.06, s0, z - 0.04, x + 0.06, s1, z + 0.14, "lamp_glass", c=0.02, d=0)

    return out


def bulbs(pts, y, r, col):
    out = ck.Part()

    if ck.LOD > 0:
        return out

    for x, z in pts:
        out.append(ck.Poly([(x - r, y, z), (x, y, z - r), (x + r, y, z), (x, y, z + r)], col, False, False, False))

    return out


def rod(p, q, r, col, sides=5, d=None, caps=(False, False)):
    if d is not None and ck.LOD > d:
        return ck.Part()

    if ck.LOD == 2:
        sides = 3

    return ck.tube([p, q], r, sides, col, caps=caps, smooth=False, d=2)


def beam(p, q, t, col, d=None):
    if d is not None and ck.LOD > d:
        return ck.Part()

    p = Vector(p)
    q = Vector(q)
    tan = (q - p).normalized()
    u, v = ck.basis(tan)
    u *= t / 2
    v *= t / 2
    out = ck.Part()
    ra = [p - u - v, p + u - v, p + u + v, p - u + v]
    rb = [r + (q - p) for r in ra]
    mid = (p + q) / 2

    for i in range(4):
        j = (i + 1) % 4
        pts = [ra[i], ra[j], rb[j], rb[i]]
        centre = (pts[0] + pts[2]) / 2
        out += face(pts, col, centre - mid)

    return out


def rng(seed):
    return random.Random(seed)
