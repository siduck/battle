import math

from mathutils import Vector

import ck
import common as c
from track import pick

W = ck.Part


def L():
    return ck.LOD


def outline(cx, cy, rx, ry, n, seed, jitter=0.05, square=0.72, grooves=()):
    out = []

    for i in range(n):
        ang = 2 * math.pi * i / n - math.pi / 2
        u, v = math.cos(ang), math.sin(ang)
        x = math.copysign(abs(u) ** square, u) * rx
        y = math.copysign(abs(v) ** square, v) * ry
        k = 1 + (ck.hash01(i * 3.7, seed, 1.3) - 0.5) * 2 * jitter

        for gx, depth, width in grooves:
            off = abs(x - gx)

            if off < width:
                k *= 1 - depth * (1 - off / width)

        out.append((cx + x * k, cy + y * k))

    return out


def stack(levels, top, seed=0):
    out = W()

    for k, ((pa, za), (pb, zb, col)) in enumerate(zip([(l[0], l[1]) for l in levels], levels[1:])):
        n = len(pa)

        for i in range(n):
            j = (i + 1) % n
            shade = 1.0 + (ck.hash01(i // 2 * 5.1, seed) - 0.5) * 0.08
            pts = [(pa[i][0], pa[i][1], za), (pa[j][0], pa[j][1], za), (pb[j][0], pb[j][1], zb), (pb[i][0], pb[i][1], zb)]

            if abs(za - zb) < 0.05:
                out.append(ck.Poly(pts, ck.shade(col, shade)))
                continue

            out.append(ck.Poly([pts[0], pts[1], pts[2]], ck.shade(col, shade)))
            out.append(ck.Poly([pts[0], pts[2], pts[3]], ck.shade(col, shade)))

    p, z, _ = levels[-1]
    out.append(ck.Poly([(q[0], q[1], z) for q in p], top))

    return out


def mesa():
    out = W()
    m = pick(18, 8, 10)
    angles = [2 * math.pi * (i + 0.5) / m for i in range(m)]
    flute = {}

    if L() < 2:
        for gx in (-3.4, 3.4):
            for dx, dip in ((-1.1, 0.0), (0.0, 1.0), (1.1, 0.0)):
                u = math.copysign(abs((gx + dx) / 11.8) ** (1 / 0.52), gx + dx)

                for side in (1, -1):
                    ang = (side * math.acos(u)) % (2 * math.pi)
                    angles = [q for q in angles if abs(q - ang) > 0.09 or q in flute]
                    angles.append(ang)
                    flute[ang] = dip

    def ring(rx, ry, z, seed, jit, cut):
        out = []

        for ang in sorted(angles):
            u, v = math.cos(ang), math.sin(ang)
            x = math.copysign(abs(u) ** 0.52, u) * rx
            y = math.copysign(abs(v) ** 0.52, v) * ry
            k = 1 + (ck.hash01(ang * 5.3, seed, 1.3) - 0.5) * 2 * jit
            dip = flute.get(ang, 0.0)
            out.append((0.4 + x * k, y * k * (1 - dip * cut)))

        return out

    spec = [
        (0.0, 15.55, 11.65, None, 1, 0.025),
        (1.6, 14.6, 11.1, "rock_sand", 1, 0.06),
        (3.6, 13.2, 9.95, "rock_sand", 1, 0.07),
        (5.8, 12.05, 8.95, "rock_lt", 2, 0.025),
        (9.2, 11.85, 8.8, "rock_lt", 2, 0.025),
        (12.1, 11.75, 8.72, "rock", 2, 0.025),
        (12.35, 12.5, 9.35, "rock_deep", 2, 0.025),
        (13.7, 12.4, 9.28, "rock_band", 2, 0.025),
        (13.75, 10.45, 7.7, "rock_band", 2, 0.025),
        (15.2, 10.45, 7.72, "rock_lt", 2, 0.025),
        (16.0, 10.45, 7.72, "rock_cap", 2, 0.025),
        (17.2, 10.4, 7.68, "rock_lt", 2, 0.025),
        (17.35, 11.05, 8.2, "rock_deep", 2, 0.025),
        (19.7, 10.85, 8.05, "rock_band", 2, 0.025),
        (19.75, 8.9, 6.45, "rock_band", 6, 0.04),
        (21.0, 8.95, 6.5, "rock_cap", 6, 0.04),
        (21.25, 9.8, 7.2, "rock_deep", 6, 0.04),
        (23.4, 9.7, 7.12, "rock_lt", 6, 0.04),
        (24.0, 8.9, 6.4, "rock_lt", 6, 0.04),
    ]

    if L() == 1:
        spec = [row for i, row in enumerate(spec) if i not in (1, 4, 9, 11)]

    if L() == 2:
        spec = [spec[i] for i in (0, 3, 5, 7, 8, 13, 14, 16, 18)]

    levels = [(ring(rx, ry, z, s, j, 0.13 if z > 4 else 0.0), z, col) for z, rx, ry, col, s, j in spec]
    out += stack(levels, "rock_lt", 3)
    m = pick(8, 6, 4)
    sp = [(0.0, 2.2, None), (4.0, 1.5, "rock_sand"), (10.5, 1.25, "rock_lt"), (11.6, 1.35, "rock_cap"), (13.2, 1.25, "rock_lt"), (14.4, 1.4, "rock_band"), (16.8, 1.15, "rock_band"), (17.4, 0.75, "rock_sand")]
    if L() == 2:
        sp = [sp[i] for i in (0, 1, 4, 5, 7)]

    out += stack([(outline(-13.7, -1.0, r, r, m, 9 + i // 2, 0.09, 0.9), z, col) for i, (z, r, col) in enumerate(sp)], "rock_band", 8)

    if L() < 2:
        rubble = ((-5.5, -10.3, 1.3, 2.3), (-2.8, -10.9, 0.9, 1.6), (-0.9, -10.5, 0.6, 1.9), (6.9, -9.9, 0.75, 2.6), (3.0, -11.3, 0.5, 0.9), (-11.0, -8.2, 0.8, 1.6), (10.5, 8.4, 1.1, 2.0), (-4.0, 10.2, 0.9, 2.2))

        for i, (x, y, s, z) in enumerate(rubble):
            if L() == 1 and i % 3:
                continue

            out += ck.blob((x, y, z), (s, s * 0.75, s * 0.55), ("rock_lt", "rock", "rock_dk"), sub=0, jitter=0.28, seed=i + 40, d=1)

    return out


def slab(cx, cy, rx, ry, z0, z1, side, lip, top, seed, n):
    h = z1 - z0
    a0 = outline(cx, cy, rx * 0.91, ry * 0.9, n, seed, 0.07, 0.6)
    a1 = outline(cx, cy, rx, ry, n, seed, 0.07, 0.6)
    a2 = outline(cx, cy, rx * 0.985, ry * 0.98, n, seed, 0.07, 0.6)
    a3 = outline(cx, cy, rx * 0.9, ry * 0.88, n, seed, 0.07, 0.6)

    if L() == 2:
        return stack([(a1, z0, None), (a1, z1, side)], top, seed)

    if L() == 1:
        return stack([(a0, z0, None), (a1, z0 + h * 0.4, side), (a3, z1, lip)], top, seed)

    return stack([(a0, z0, None), (a1, z0 + h * 0.3, side), (a2, z0 + h * 0.68, side), (a3, z1, lip)], top, seed)


def outcrop():
    out = W()
    n = pick(13, 7, 5)
    layers = [
        (-0.5, 0.0, 2.15, 1.42, 0.0, 0.62, "rock", "rock_band", "rock"),
        (-0.58, 0.0, 2.14, 1.45, 0.6, 1.2, "rock_lt", "rock_band", "rock_band"),
        (-0.42, 0.1, 2.0, 1.18, 1.18, 1.88, "rock_dk", "rock", "rock"),
        (-0.56, -0.02, 2.14, 1.45, 1.86, 2.5, "rock_band", "rock_lt", "rock_lt"),
        (-0.32, 0.02, 1.92, 1.26, 2.48, 2.98, "rock", "rock_lt", "rock_lt"),
        (-0.52, 0.0, 1.3, 0.95, 2.96, 3.38, "rock_band", "rock_lt", "rock_lt"),
    ]

    for i, (cx, cy, rx, ry, z0, z1, side, lip, top) in enumerate(layers):
        out += slab(cx, cy, rx, ry, z0, z1, side, lip, top, i + 2, n)

    m = pick(10, 6, 5)
    spec = [(0.0, 0.9, 1.15, None), (0.85, 0.83, 1.08, "rock"), (1.15, 0.84, 1.1, "rock_band"), (2.15, 0.76, 1.0, "rock_lt"), (2.42, 0.78, 1.02, "rock_band"), (3.15, 0.72, 0.94, "rock_lt"), (3.42, 0.56, 0.74, "rock")]
    if L() == 2:
        spec = [spec[i] for i in (0, 2, 3, 5)]

    out += stack([(outline(1.98, 0.14, rx, ry, m, 20, 0.07, 0.55), z, col) for z, rx, ry, col in spec], "rock_lt", 12)

    if L() < 2:
        for i, (x, y, s) in enumerate(((-2.35, -1.3, 0.2), (0.15, -1.32, 0.17), (0.72, -1.25, 0.27), (1.12, -1.38, 0.14), (-1.0, 1.32, 0.18), (2.45, 1.2, 0.22))):
            if L() == 1 and i % 2:
                continue

            out += ck.blob((x, y, s * 0.45), (s, s * 0.8, s * 0.62), ("rock_lt", "rock", "rock_dk"), sub=0, jitter=0.3, seed=i + 7, d=1)

        out += ck.blob((2.05, -0.95, 0.03), (0.75, 0.45, 0.2), ("rock_sand", "rock_sand", "rock_sand"), sub=0, jitter=0.15, seed=3, d=1)

    return out


def lump(p, r, tones, seed, squash=0.82):
    return ck.blob(p, (r, r * 0.9, r * squash), tones, sub=0, jitter=0.2, seed=seed, d=9)


def josh_clump(p, k, seed):
    out = W()
    x, y, z = p
    tones = ("josh_lt", "josh", "josh_dk")

    if L() == 2:
        return lump((x, y, z), 0.46 * k, tones, seed, 0.8)

    out += lump((x, y, z), 0.34 * k, tones, seed)
    sats = ((-0.33, -0.08, 0.04), (0.33, 0.06, 0.07), (0.02, -0.28, 0.2), (-0.1, 0.27, 0.16), (0.07, -0.02, 0.38))

    if L() == 1:
        sats = sats[1:2] + sats[4:5]

    for i, (dx, dy, dz) in enumerate(sats):
        out += lump((x + dx * k, y + dy * k, z + dz * k), (0.23 if L() == 0 else 0.3) * k, tones, seed * 7 + i, 0.85)

    if L() == 0:
        for i, (dx, dy, dz) in enumerate(((-0.52, -0.1, 0.12), (0.5, -0.12, 0.2), (0.1, 0.0, 0.58))):
            out += ck.blob((x + dx * k, y + dy * k, z + dz * k), (0.075, 0.07, 0.07), ("mustard", "josh_lt", "josh_lt"), sub=0, jitter=0.1, seed=seed + i)

    return out


def joshua():
    out = W()
    n = pick(8, 5, 4)
    out += ck.tube([(0.0, 0.0, 0.0), (0.0, 0.0, 0.3), (0.02, 0.0, 1.2), (0.0, 0.0, 2.25)], [0.42, 0.3, 0.27, 0.24], n, "bark", smooth=False, caps=(False, True))

    if L() < 2:
        rows = pick(5, 2, 0)

        for k in range(rows):
            z = 0.45 + k * (1.55 / rows)
            m = pick(7, 5, 0)

            for i in range(m):
                ang = 2 * math.pi * (i + 0.5 * (k % 2)) / m
                u = Vector((math.cos(ang), math.sin(ang), 0))
                t = Vector((-u.y, u.x, 0))
                base = Vector((0, 0, z))
                a0 = base + u * 0.27 - t * 0.11 + Vector((0, 0, 0.28))
                a1 = base + u * 0.27 + t * 0.11 + Vector((0, 0, 0.28))
                b1 = base + u * 0.39 + t * 0.07
                b0 = base + u * 0.39 - t * 0.07
                col = ("bark_lt", "dry", "bark")[(i + k) % 3]
                out += c.face([a0, a1, b1, b0], col, u)
                if L() == 0:
                    out += c.face([b0, b1, base + u * 0.26 + t * 0.08, base + u * 0.26 - t * 0.08], "bark_dk", u * 0.2 + Vector((0, 0, -1)), cast=False)

    arms = [
        [(0.0, 0.0, 2.15), (-0.4, 0.0, 2.75), (-0.95, -0.05, 3.35), (-1.98, -0.12, 3.72)],
        [(-0.95, -0.05, 3.35), (-1.25, 0.2, 3.9), (-1.48, 0.38, 4.45)],
        [(0.0, 0.0, 2.15), (-0.25, 0.05, 3.0), (-0.5, -0.15, 3.75), (-0.78, -0.35, 4.55)],
        [(-0.25, 0.05, 3.0), (-0.1, 0.15, 4.25), (0.02, 0.2, 5.42)],
        [(0.0, 0.0, 2.15), (0.42, -0.02, 2.65), (0.9, 0.05, 3.7), (0.92, 0.25, 4.82)],
        [(0.9, 0.05, 3.7), (1.35, -0.2, 4.15), (1.72, -0.32, 4.5)],
        [(0.42, -0.02, 2.65), (1.3, 0.05, 3.0), (1.92, -0.05, 3.28), (2.25, -0.1, 3.68)],
    ]

    for i, path in enumerate(arms):
        main = i in (0, 2, 4)
        r0 = 0.19 if main else 0.13

        if L() == 2:
            path = [path[0], path[-2], path[-1]]

        radii = [r0 - (r0 - 0.085) * k / (len(path) - 1) for k in range(len(path))]
        out += ck.tube(path, radii, pick(6, 4, 3), "bark" if i % 2 == 0 else "bark_dk", smooth=False, caps=(False, False))

        if L() == 0:
            end = Vector(path[-1])
            prev = Vector(path[-2])
            out += ck.tube([end.lerp(prev, 0.42), end.lerp(prev, 0.05)], [0.14, 0.17], 7, "dry", smooth=False, caps=(True, False))

    tips = [((-2.12, -0.12, 3.8), 0.96), ((-1.55, 0.4, 4.62), 0.94), ((-0.84, -0.38, 4.78), 0.92), ((0.03, 0.2, 5.42), 0.95), ((0.93, 0.27, 5.02), 0.93), ((1.8, -0.34, 4.66), 0.95), ((2.22, -0.1, 3.78), 0.9)]

    for i, (p, k) in enumerate(tips):
        out += josh_clump(p, k, i + 2)

    return out


def creosote():
    out = W()
    green = [(0.02, 0.05, 2.42), (0.22, -0.25, 2.38), (-0.6, -0.2, 2.08), (-0.58, 0.25, 1.85), (-1.24, -0.05, 1.58), (0.42, 0.3, 1.72), (0.12, -0.55, 1.42), (0.62, -0.4, 1.5), (1.05, 0.15, 1.75), (1.24, -0.3, 1.5), (0.86, 0.55, 1.34), (1.27, 0.1, 0.98), (-0.48, -0.65, 1.05), (-0.82, 0.45, 0.95), (0.08, -0.8, 0.85), (-0.15, 0.75, 1.5), (-0.2, 0.2, 2.22)]
    brown = [(-1.26, 0.2, 1.05), (-0.4, -0.35, 1.36), (-0.18, 0.55, 1.1), (0.28, -0.3, 1.12)]
    base = Vector((0.0, 0.0, 0.12))
    out += ck.blob((0.0, 0.0, 0.02), (0.48, 0.44, 0.14), ("rock_sand", "rock_sand", "rock_lt"), sub=0, jitter=0.18, seed=5, d=1)
    out += ck.tube([(0.0, 0.0, 0.0), (0.0, 0.0, 0.32)], [0.17, 0.12], pick(7, 5, 4), "bark_dk", smooth=False)
    trunks = [(-0.42, -0.1, 1.15), (-0.2, 0.2, 1.4), (0.05, 0.0, 1.7), (0.4, -0.15, 1.1), (0.62, 0.2, 1.0)]

    for i, t in enumerate(trunks):
        if L() == 2 and i % 2:
            continue

        mid = base.lerp(Vector(t), 0.5) + Vector((0, 0, 0.1))
        out += ck.tube([base, mid, t], [0.07, 0.052, 0.035], pick(5, 3, 3), "bark" if i % 2 else "bark_dk", smooth=False)

    for i, p in enumerate(green + brown):
        dead = i >= len(green)

        if (L() == 2 and i not in (0, 4, 9, 12, 14)) or (L() == 1 and i in (1, 3, 8, 10, 16, 19)):
            continue

        near = min(trunks, key=lambda t: (Vector(t) - Vector(p)).length)

        if L() == 0:
            out += ck.tube([near, p], [0.032, 0.014], 3, "bark", smooth=False)
        elif L() == 1:
            out += c.face([(near[0] - 0.02, near[1], near[2]), (near[0] + 0.02, near[1], near[2]), (p[0], p[1], p[2])], "bark", (0, -1, 0))

        tones = ("bark_lt", "bark", "bark_dk") if dead else ("leaf_lt", "leaf", "leaf_dk")

        if L() == 0:
            out += lump(p, 0.18, tones, i)
            out += lump((p[0] + 0.14, p[1] - 0.04, p[2] - 0.07), 0.13, tones, i + 31)

            if not dead and i % 3 == 0:
                out += lump((p[0] - 0.11, p[1] + 0.06, p[2] + 0.07), 0.12, tones, i + 57)

                if i % 2 == 0:
                    out += ck.blob((p[0] + 0.03, p[1] - 0.17, p[2] + 0.04), (0.055, 0.05, 0.05), ("mustard", "mustard", "gold"), sub=0, jitter=0.1, seed=i)
        else:
            out += lump(p, 0.26 if L() == 1 else 0.4, tones, i)

    return out


def ribbed(path, radii, ribs, col, deep=0.14, cap=True):
    out = W()
    n = ribs * 2 if L() == 0 else pick(0, 8, 5)
    pts = [Vector(p) for p in path]
    rings = []
    ref = Vector((0, 1, 0))

    for k, p in enumerate(pts):
        t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        u = ref.cross(t).normalized()
        v = t.cross(u)
        ring = []

        for i in range(n):
            ang = 2 * math.pi * i / n
            r = radii[k] * (1.0 if L() or i % 2 == 0 else 1 - deep)
            ring.append(p + u * math.cos(ang) * r + v * math.sin(ang) * r)

        rings.append(ring)

    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        mid = (pts[k] + pts[k + 1]) / 2

        for i in range(n):
            j = (i + 1) % n
            shade = col if L() or (i // 2) % 2 == 0 else "cactus_dk" if i % 2 else col
            q = [a[i], a[j], b[j], b[i]]

            for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                centre = (tri[0] + tri[1] + tri[2]) / 3
                out += c.face(list(tri), shade, centre - mid)

    if cap:
        last = rings[-1]
        tip = pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 0.7

        for i in range(n):
            j = (i + 1) % n
            tri = [last[i], last[j], tip]
            out += c.face(tri, "cactus_lt", (tri[0] + tri[1] + tri[2]) / 3 - pts[-1])

    return out


def saguaro():
    out = W()
    trunk = [(0, 0, 0.0), (0, 0, 0.25), (0, 0, 1.6), (0, 0, 3.3), (0, 0, 4.4), (0, 0, 4.72), (0, 0, 4.86)]
    tr = [0.36, 0.4, 0.43, 0.42, 0.36, 0.27, 0.17]
    left = [(-0.25, 0, 1.66), (-0.72, 0, 1.66), (-1.0, 0, 1.78), (-1.09, 0, 2.1), (-1.09, 0, 3.0), (-1.09, 0, 3.35), (-1.09, 0, 3.52)]
    lr = [0.22, 0.22, 0.23, 0.25, 0.23, 0.18, 0.11]
    right = [(0.25, 0, 1.72), (0.7, 0, 1.72), (0.96, 0, 1.84), (1.06, 0, 2.12), (1.06, 0, 2.62), (1.06, 0, 2.92), (1.06, 0, 3.08)]
    rr = [0.22, 0.22, 0.23, 0.25, 0.23, 0.18, 0.11]

    if L() == 2:
        trunk, tr = [trunk[i] for i in (0, 3, 5, 6)], [tr[i] for i in (0, 3, 5, 6)]
        left, lr = [left[i] for i in (0, 2, 4, 6)], [lr[i] for i in (0, 2, 4, 6)]
        right, rr = [right[i] for i in (0, 2, 4, 6)], [rr[i] for i in (0, 2, 4, 6)]

    out += ribbed(trunk, tr, 11, "cactus")
    out += ribbed(left, lr, 8, "cactus")
    out += ribbed(right, rr, 8, "cactus")

    if L() == 0:
        def dot(p, nrm, s=0.028):
            nrm = Vector(nrm).normalized()
            t, b = ck.basis(nrm)
            p = Vector(p) + nrm * 0.012

            return c.face([p - t * s, p - b * s, p + t * s, p + b * s], "tan", nrm, ao=False, cast=False)

        for rib in range(11):
            ang = 2 * math.pi * rib / 11

            for k in range(6):
                z = 0.5 + k * 0.7 + (rib % 3) * 0.14
                r = 0.43 if z < 3.4 else 0.38
                u = Vector((math.cos(ang), math.sin(ang), 0))

                if z < 4.4:
                    out += dot(u * r + Vector((0, 0, z)), u)

        for x, z1 in ((-1.09, 3.1), (1.06, 2.7)):
            for ang in (-2.4, -1.57, -0.75, 0.75, 1.57, 2.4):
                u = Vector((math.cos(ang), math.sin(ang), 0))

                for z in (2.2, z1 - 0.1):
                    out += dot(Vector((x, 0, z)) + u * 0.25, u, 0.022)

    out += ck.blob((0.52, -0.12, 0.08), (0.36, 0.27, 0.2), ("rock_lt", "rock_sand", "rock"), sub=0, jitter=0.2, seed=9, d=1)

    if L() < 2:
        out += ck.blob((0.06, -0.38, 0.65), (0.16, 0.08, 0.22), ("dry", "bark_lt", "bark"), sub=0, jitter=0.15, seed=4, d=1)

    return out


ALL = {
    "mesa": (mesa, {"errors": (0.05, 0.3), "reach": 5.0, "ao": 0.45, "grime": 0.1, "grime_h": 3.0, "speckle": 0.02}),
    "outcrop": (outcrop, {"errors": (0.012, 0.05)}),
    "joshua": (joshua, {"errors": (0.012, 0.045), "ao": 0.4}),
    "creosote": (creosote, {"errors": (0.008, 0.03), "ao": 0.35}),
    "saguaro": (saguaro, {"errors": (0.01, 0.04), "ao": 0.4}),
}
