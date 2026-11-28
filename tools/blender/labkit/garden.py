import math

import lk
from common import *
from mathutils import Vector

LEAF = ("leaf_lt", "leaf", "leaf_dk")
LEAF_L = ("leaf_lt", "leaf_lt", "leaf")
LEAF_D = ("leaf", "leaf_dk", "leaf_dk")
OLIVE = ("olive_lt", "olive", "olive_dk")
OLIVE_L = ("olive_lt", "olive_lt", "olive")


def clump(b, tones, sub, seed, jitter=0.13):
    x0, x1, y0, y1, z0, z1 = b
    at = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    k = 1.0 - jitter * 0.45 if sub else 1.04
    size = ((x1 - x0) / 2 * k, (y1 - y0) / 2 * k, (z1 - z0) / 2 * k)

    return blob(at, size, tones, sub=sub, jitter=jitter, seed=seed)


def fence():
    out = part()

    for x in (-0.91, 0.91):
        out += box(x - 0.09, -0.072, 0.0, x + 0.09, 0.072, 1.72, "steel_lt", skip="dt")

        if lk.LOD == 0:
            out += box(x - 0.09, -0.072, 1.72, x + 0.09, 0.072, 1.80, "white_dk", taper=(0.62, 0.55), skip="d")

            for y, s in ((-0.075, -1), (0.075, 1)):
                out += face([(x - 0.05, y, 0.92), (x + 0.05, y, 0.92), (x + 0.05, y, 1.1), (x - 0.05, y, 1.1)], "teal_dk", ao=False, cast=False, towards=(0, s, 0))
        else:
            out += deck(x - 0.09, x + 0.09, -0.072, 0.072, 1.78, "white_dk")

    def strip(x0, x1, z0, z1, y, col):
        a = face([(x0, -y, z0), (x1, -y, z0), (x1, -y, z1), (x0, -y, z1)], col, cast=False, towards=(0, -1, 0))
        b = face([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col, cast=False, towards=(0, 1, 0))

        return a + b

    for z0, z1 in ((0.58, 0.76), (1.01, 1.19)):
        out += strip(-0.82, 0.82, z0, z1, 0.005, "slate_dk")

    if lk.LOD < 2:
        n = 9 if lk.LOD == 0 else 5

        for i in range(n):
            x = -0.82 + 1.64 * (i + 1) / (n + 1)
            out += strip(x - 0.016, x + 0.016, 0.1, 1.74, 0.034, "steel_dk")

    rails = ((0.1, 0.15), (0.36, 0.385), (1.42, 1.445), (1.69, 1.745)) if lk.LOD == 0 else ((0.1, 0.16), (1.68, 1.745))

    for z0, z1 in rails:
        out += strip(-0.82, 0.82, z0, z1, 0.022, "graphite" if z1 - z0 < 0.04 else "slate")

    return out


def hedge():
    out = part()
    prof = [(-0.185, 0.0), (-0.225, 0.2), (-0.222, 0.62), (-0.15, 0.815), (0.0, 0.862), (0.15, 0.815), (0.222, 0.62), (0.225, 0.2), (0.185, 0.0)]

    if lk.LOD == 1:
        prof = [prof[i] for i in (0, 2, 3, 4, 5, 6, 8)]
    elif lk.LOD == 2:
        prof = [prof[i] for i in (0, 2, 4, 6, 8)]

    n = (11, 5, 2)[lk.LOD]
    r = rng(31)
    rings = []

    for s in range(n + 1):
        x = -1.0 + 2.0 * s / n
        ring = []

        for k, (y, z) in enumerate(prof):
            end = s in (0, n)
            ky = 1.0 if end or lk.LOD == 2 else 0.72 + r.random() * 0.34
            kz = 1.0 if end or z == 0 or lk.LOD == 2 else 0.86 + r.random() * 0.17
            dx = 0 if end else (r.random() - 0.5) * 0.11
            ring.append((x + dx, max(-0.235, min(0.235, y * ky)), min(0.89, z * kz)))

        rings.append(ring)

    for s in range(n):
        for k in range(len(prof) - 1):
            q = [rings[s][k], rings[s + 1][k], rings[s + 1][k + 1], rings[s][k + 1]]

            for t, tri in enumerate(((q[0], q[1], q[2]), (q[0], q[2], q[3]))):
                c = sum((Vector(p) for p in tri), Vector()) / 3
                h = lk.hash01(s, k, t, 4.2)

                if c.z > 0.7:
                    col = "hedge_lt" if h > 0.35 else "hedge"
                elif c.z > 0.28:
                    col = "hedge" if h > 0.3 else ("hedge_lt" if h > 0.15 else "hedge_dk")
                else:
                    col = "hedge_dk" if h > 0.4 else "hedge"

                f = Poly(tri, col)

                if f.normal().dot(c - Vector((c.x, 0, 0.35))) < 0:
                    f.pts.reverse()

                out.append(f)

    for x, s in ((-1.0, -1), (1.0, 1)):
        pts = [(x, y, z) for y, z in prof]
        out += face(pts, "hedge_dk", towards=(s, 0, 0))

    if lk.LOD < 2:
        spots = [(-0.74, -0.13, 0.62), (-0.46, 0.1, 0.78), (-0.2, -0.14, 0.45), (0.08, 0.03, 0.8), (0.34, 0.13, 0.55), (0.55, -0.1, 0.74), (0.78, 0.08, 0.76), (-0.62, 0.13, 0.36), (0.68, -0.13, 0.35), (0.22, -0.12, 0.68), (-0.3, 0.14, 0.62), (-0.86, -0.04, 0.76)]

        for i, (x, y, z) in enumerate(spots[: 12 if lk.LOD == 0 else 5]):
            sy = min(0.105, 0.238 - abs(y))
            tones = ("hedge_lt", "hedge_lt" if i % 3 else "hedge", "hedge_dk")
            out += blob((x, y, min(z, 0.775)), (0.155, sy * 0.95, 0.12), tones, sub=0, jitter=0.1, seed=i * 7 + 3)

    return out


def shrub():
    out = part()
    out += cyl((0, 0.0, 0.0), 0.11, 0.72, "bark_dk", sides=6, rt=0.085, smooth=False, caps=(False, False))
    prof = [(0.12, 0.48), (0.44, 0.6), (0.565, 0.86), (0.37, 1.30), (0.5, 1.42), (0.31, 1.86), (0.42, 1.98), (0.23, 2.40), (0.30, 2.52), (0.17, 2.88), (0.09, 3.05), (0.0, 3.12)]

    if lk.LOD == 2:
        prof = [(0.12, 0.48), (0.55, 0.88), (0.38, 1.6), (0.38, 2.0), (0.2, 2.8), (0.0, 3.12)]

    n = (9, 6, 5)[lk.LOD]
    r = rng(8)
    rings = []

    for j, (rad, z) in enumerate(prof):
        ring = []

        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (j % 2)) / n
            k = 1.0 if rad == 0 else 0.9 + r.random() * 0.17
            ring.append((math.cos(a) * rad * k, math.sin(a) * rad * k * 1.03, z + (r.random() - 0.5) * 0.08 * (rad > 0.15)))

        rings.append(ring)

    def col(j, i):
        a, b = prof[j][0], prof[j + 1][0]
        h = lk.hash01(j, i, 2.7)

        if b > a:
            return "pine_dk" if h > 0.3 else "pine"

        return "pine_lt" if h > 0.55 else "pine"

    out += loft(rings, col, caps=("pine_dk", None))

    if lk.LOD == 0:
        for j, (rad, z) in enumerate(((0.47, 0.84), (0.40, 1.45), (0.32, 2.02), (0.21, 2.55))):
            for i in range(3):
                a = 2.1 * i + j * 0.9
                out += blob((math.cos(a) * rad * 0.8, math.sin(a) * rad * 0.8, z), (rad * 0.34, rad * 0.34, 0.13), ("pine_lt", "pine", "pine_dk"), sub=0, jitter=0.1, seed=j * 5 + i)

    return out


def limb(pts, radii, sides=5):
    return tube(pts, radii, sides, lambda i, j: "bark" if i % 2 else "bark_dk", caps=(False, False), smooth=False)


def tree():
    out = part()
    cx, cy = 0.2, 0.15
    out += tube([(cx, cy, 0.0), (cx, cy, 0.28), (cx + 0.02, cy + 0.01, 0.85), (cx - 0.02, cy, 2.9), (cx - 0.05, cy + 0.05, 4.3), (cx, cy, 5.8)], [0.40, 0.29, 0.23, 0.20, 0.17, 0.11], 7, lambda i, j: "bark" if i % 3 else "bark_dk", caps=(False, False), smooth=False)
    out += limb([(0.15, 0.2, 3.5), (-0.7, 0.35, 4.4), (-1.65, 0.55, 5.5)], [0.14, 0.11, 0.06]) if lk.LOD < 2 else part()
    out += limb([(0.25, 0.05, 3.6), (1.0, -0.35, 4.5), (1.9, -0.6, 5.5)], [0.14, 0.1, 0.06]) if lk.LOD < 2 else part()
    out += limb([(0.25, 0.25, 3.85), (0.55, 0.95, 4.6), (0.9, 1.7, 5.6)], [0.13, 0.09, 0.05]) if lk.LOD < 2 else part()

    if lk.LOD == 0:
        out += limb([(0.15, 0.05, 4.2), (-0.35, -0.8, 4.9), (-0.8, -1.5, 5.7)], [0.11, 0.08, 0.04], 4)

        for i in range(4):
            a = i * 1.6 + 0.4
            out += tube([(cx + math.cos(a) * 0.5, cy + math.sin(a) * 0.5, 0.0), (cx + math.cos(a) * 0.18, cy + math.sin(a) * 0.18, 0.42)], [0.1, 0.05], 3, "bark_dk", caps=(False, False), smooth=False)

    out += clump((-2.75, 3.0, -3.0, 2.95, 5.3, 8.54), LEAF, 1, 2, 0.12)
    out += clump((-2.0, 3.1, -2.35, 2.85, 4.89, 6.3), LEAF_D, 1 if lk.LOD == 0 else 0, 4, 0.12)
    side_clumps = [
        ((-3.67, -1.08, -0.6, 2.12, 5.22, 7.28), LEAF_L, 1),
        ((1.34, 3.67, -2.5, 0.2, 5.2, 7.12), LEAF, 1),
        ((-0.05, 2.47, 1.25, 3.32, 5.31, 7.0), LEAF_L, 1),
        ((1.46, 3.55, -0.25, 2.18, 5.1, 6.86), LEAF_L, 0),
        ((-2.15, 0.0, -3.0, -0.62, 5.12, 6.86), LEAF, 1),
        ((-0.2, 2.1, -3.25, -1.05, 5.08, 6.7), LEAF, 0),
        ((-2.02, 0.0, 1.14, 3.22, 5.15, 6.82), LEAF, 0),
        ((-3.0, -0.96, -1.56, 0.36, 5.03, 6.66), LEAF_L, 0),
        ((0.9, 2.66, 0.55, 2.54, 5.06, 6.48), LEAF_D, 0),
    ]

    for i, (b, tones, sub) in enumerate(side_clumps[: 5 if lk.LOD == 2 else 9]):
        out += clump(b, tones, sub, 20 + i * 3, 0.15)

    if lk.LOD == 0:
        for i, at in enumerate(((-1.35, -1.15, 7.5), (1.4, 0.75, 7.7), (0.1, -1.7, 7.35), (-1.15, 1.45, 7.45), (2.1, -0.8, 6.95))):
            out += blob(at, (0.72, 0.72, 0.52), LEAF_L if i % 2 == 0 else LEAF, sub=0, jitter=0.12, seed=60 + i)

    return out


def tree2():
    out = part()
    cx = cy = 0.065
    ring_o = [circle(r, 8, z, cx, cy) for r, z in ((1.17, 0.0), (1.17, 0.15), (1.09, 0.2), (0.9, 0.2), (0.86, 0.11))]
    out += loft(ring_o, lambda j, i: ("stone_dk", "stone", "stone", "stone_dk")[j], wind=True)
    out += face(circle(0.87, 8, 0.12, cx, cy), "soil", towards=(0, 0, 1))
    out += tube([(cx, cy, 0.05), (cx, cy, 0.4), (cx + 0.02, cy, 1.3), (cx - 0.03, cy + 0.03, 2.4), (cx, cy, 3.4)], [0.28, 0.2, 0.17, 0.15, 0.1], 7, lambda i, j: "bark" if i % 3 else "bark_dk", caps=(False, False), smooth=False)
    out += limb([(0.03, 0.08, 1.7), (-0.45, 0.1, 2.6), (-0.98, 0.2, 3.4)], [0.12, 0.09, 0.05]) if lk.LOD < 2 else part()
    out += limb([(0.08, 0.08, 1.8), (0.45, 0.3, 2.7), (0.95, 0.62, 3.5)], [0.11, 0.08, 0.05]) if lk.LOD < 2 else part()
    out += limb([(0.07, 0.03, 2.2), (0.15, -0.5, 2.8), (0.3, -1.0, 3.5)], [0.09, 0.06, 0.04], 4) if lk.LOD < 2 else part()
    out += clump((-1.5, 1.66, -1.76, 1.72, 2.85, 5.85), LEAF, 1, 3, 0.12)
    items = [
        ((0.37, 2.03, -1.55, 0.2, 3.2, 4.68), LEAF_L, 1),
        ((-2.03, -0.45, -1.3, 0.46, 3.12, 4.52), LEAF, 1),
        ((0.34, 2.03, 0.02, 1.56, 3.26, 4.62), LEAF_D, 0),
        ((-1.93, -0.3, -0.18, 1.44, 3.08, 4.46), LEAF_L, 1),
        ((-0.32, 0.96, -1.78, -0.3, 2.96, 4.22), LEAF_L, 0),
        ((-1.1, 0.25, 0.46, 1.78, 3.0, 4.24), LEAF, 0),
        ((0.52, 1.87, -0.5, 0.69, 2.88, 4.0), LEAF_L, 0),
        ((-1.08, 0.25, -1.32, -0.1, 2.70, 3.88), LEAF_D, 0),
        ((-0.03, 1.12, -1.21, 0.09, 2.62, 3.72), LEAF, 0),
        ((-0.27, 0.88, 0.32, 1.6, 2.86, 3.9), LEAF_L, 0),
    ]

    for i, (b, tones, sub) in enumerate(items[: 4 if lk.LOD == 2 else 10]):
        out += clump(b, tones, sub, 40 + i * 3, 0.15)

    if lk.LOD == 0:
        for i, at in enumerate(((-0.8, -0.7, 5.25), (0.95, 0.5, 5.2), (-0.4, 0.95, 5.15), (0.75, -0.85, 5.0))):
            out += blob(at, (0.45, 0.45, 0.36), LEAF_L if i % 2 == 0 else LEAF, sub=0, jitter=0.12, seed=80 + i)

    return out


def pit():
    out = part()
    out += box(-0.50, -0.50, 0.0, 0.50, 0.50, 0.045, "graphite", skip="d")
    out += deck(-0.43, 0.43, -0.43, 0.43, 0.047, "soil")

    for i in range(5):
        y = -0.36 + i * 0.18
        out += box(-0.43, y - 0.022, 0.045, -0.22, y + 0.022, 0.062, "slate", skip="d", d=0)
        out += box(0.22, y - 0.022, 0.045, 0.43, y + 0.022, 0.062, "slate", skip="d", d=0)

    out += tube([(0, 0, 0.03), (0, 0, 0.32), (0, 0, 2.2), (0.02, -0.03, 4.4), (0, 0, 6.3)], [0.24, 0.19, 0.17, 0.14, 0.08], 8, lambda i, j: "birch_dk" if lk.hash01(i, j, 1.3) > 0.78 else "birch", caps=(False, False), smooth=False)

    for z, r in ((0.7, 0.188), (2.45, 0.178), (3.5, 0.165)):
        out += cyl((0.0, 0.0, z), r, 0.05, "birch_dk", sides=8, smooth=False, caps=(False, False), d=0)

    out += cyl((0, 0, 1.35), 0.205, 0.28, "slate_lt", sides=8, smooth=False, caps=(True, True), d=1)
    out += plate(-0.12, 0.1, 1.26, 1.77, -0.213, "canvas", d=1)
    out += plate(-0.085, 0.065, 1.62, 1.69, -0.215, "teal", d=0)

    for z in (1.47, 1.54):
        out += plate(-0.085, 0.065, z, z + 0.022, -0.215, "slate", d=0)

    out += side(-0.1, 0.1, 1.3, 1.58, 0.215, 1, "petal", d=0)

    for a, b, c in (((0, 0, 2.9), (-0.25, -0.35, 3.8), (-0.5, -0.65, 4.7)), ((0, 0, 3.1), (0.3, -0.3, 3.9), (0.55, -0.55, 4.8)), ((0, 0, 3.2), (0.0, 0.25, 4.2), (0.02, 0.6, 5.2))):
        out += tube([a, b, c], [0.09, 0.065, 0.04], 5, "birch_dk", caps=(False, False), smooth=False)

    items = [
        ((-1.2, 1.28, -1.6, 1.04, 5.63, 7.98), OLIVE, 1),
        ((-2.58, -0.25, -1.37, 0.81, 5.04, 7.06), OLIVE, 1),
        ((0.24, 2.37, -0.87, 1.23, 5.16, 7.06), OLIVE_L, 1),
        ((-0.18, 1.85, -1.82, 0.21, 4.24, 6.15), OLIVE, 1),
        ((-1.08, 0.9, -0.22, 1.83, 4.77, 6.65), OLIVE_L, 1),
        ((-1.68, 0.2, -1.83, 0.0, 4.22, 6.03), OLIVE, 1),
    ]

    for i, (b, tones, sub) in enumerate(items):
        out += clump(b, tones, sub, 91 + i * 2, 0.13)

    if lk.LOD == 0:
        for i, at in enumerate(((-1.5, 0.2, 7.0), (1.2, -0.5, 7.0), (0.3, 0.9, 7.2), (-0.2, -1.2, 6.7), (1.75, 0.5, 6.5))):
            out += blob(at, (0.5, 0.5, 0.4), OLIVE_L if i % 2 == 0 else OLIVE, sub=0, jitter=0.12, seed=110 + i)

    return out


def flowers():
    out = part()
    out += box(-0.62, -0.62, 0.0, 0.62, 0.62, 0.02, "wood_dd", skip="d", d=1)

    if lk.LOD == 0:
        courses = ((0.0, 0.095, 0.69, "wood_dk"), (0.1, 0.195, 0.675, "wood"), (0.2, 0.3, 0.70, "wood"))
    else:
        courses = ((0.0, 0.3, 0.70, "wood"),)

    for z0, z1, r, col in courses:
        top = "wood_lt" if z1 > 0.29 else col

        for s in (-1, 1):
            out += box(-r, s * r, z0, r, s * 0.575, z1, col, top=top, skip="d")
            out += box(s * r, -0.575, z0, s * 0.575, 0.575, z1, col, top=top, skip="dfb")

    if lk.LOD == 0:
        for sx in (-1, 1):
            for sy in (-1, 1):
                out += box(sx * 0.70, sy * 0.70, 0.0, sx * 0.63, sy * 0.63, 0.315, "wood_dk", top="wood", skip="d")

    out += deck(-0.58, 0.58, -0.58, 0.58, 0.245, "soil", cast=True)
    heads = [(0.145, -0.475, "pink"), (0.205, -0.185, "bloom"), (0.49, 0.44, "pink"), (-0.115, -0.47, "petal"), (0.48, -0.15, "pink"), (-0.19, 0.46, "petal"), (-0.49, 0.17, "bloom"), (0.17, 0.49, "bloom"), (0.49, 0.12, "petal"), (-0.31, -0.31, "pink"), (-0.47, 0.47, "pink"), (0.16, 0.12, "pink"), (-0.17, 0.1, "petal"), (0.43, -0.45, "bloom"), (-0.46, -0.1, "petal"), (-0.08, 0.27, "bloom")]
    r = rng(17)

    for k, (x, y, col) in enumerate(heads):
        h = 0.45 + r.random() * 0.075
        a0 = r.random() * 6.28
        rr = 0.074

        if lk.LOD == 2:
            if k % 2:
                continue

            out += face([(x + math.cos(a0 + i * 1.571) * 0.09, y + math.sin(a0 + i * 1.571) * 0.09, h) for i in range(4)], col, towards=(0, 0, 1))
            out += blob((x, y, 0.3), (0.12, 0.12, 0.08), ("leaf", "leaf_dk", "leaf_dk"), sub=0, jitter=0.1, seed=k)

            continue

        if lk.LOD == 1:
            out += face([(x + math.cos(a0 + i * 1.257) * 0.08, y + math.sin(a0 + i * 1.257) * 0.08, h) for i in range(5)], col, towards=(0, 0, 1))
            out += tube([(x, y, 0.24), (x, y, h)], 0.012, 3, "leaf_dk", caps=(False, False), smooth=False, d=1)
        else:
            c = (x, y, h - 0.012)

            for i in range(5):
                a = a0 + i * 1.2566
                p0 = (x + math.cos(a - 0.5) * rr * 0.72, y + math.sin(a - 0.5) * rr * 0.72, h + 0.008)
                tip = (x + math.cos(a) * rr * 1.04, y + math.sin(a) * rr * 1.04, h + 0.018)
                p1 = (x + math.cos(a + 0.5) * rr * 0.72, y + math.sin(a + 0.5) * rr * 0.72, h + 0.008)
                out += face([c, p0, tip, p1], col if i % 2 == 0 else tuple(min(1, v * 1.12) for v in lk.rgb(col)), ao=False, cast=False, towards=(0, 0, 1))

            out += cyl((x, y, h - 0.008), 0.024, 0.026, "amber", sides=5, rt=0.012, smooth=False, caps=(False, True))
            out += tube([(x, y, 0.24), (x, y, h - 0.01)], 0.011, 3, "leaf_dk", caps=(False, False), smooth=False)

        for i in range(2 if lk.LOD == 0 else 1):
            a = a0 + 1.0 + i * 2.7
            z = 0.28 + r.random() * 0.05
            dx, dy = math.cos(a), math.sin(a)
            pts = [(x, y, z - 0.02), (x + dx * 0.07 - dy * 0.042, y + dy * 0.07 + dx * 0.042, z + 0.02), (x + dx * 0.13, y + dy * 0.13, z + 0.015), (x + dx * 0.07 + dy * 0.042, y + dy * 0.07 - dx * 0.042, z + 0.02)]
            out += face(pts, "leaf" if i == 0 else "leaf_lt", ao=False, cast=False, towards=(0, 0, 1))

    return out


def cup(x, y, z, h=0.13, r=0.042, col="canvas", band="teal"):
    out = part()
    out += cyl((x, y, z), r * 0.78, h * 0.4, col, sides=7, rt=r * 0.88, smooth=False, caps=(False, False), d=1)
    out += cyl((x, y, z + h * 0.4), r * 0.9, h * 0.3, band, sides=7, rt=r * 0.97, smooth=False, caps=(False, False), d=1)
    out += cyl((x, y, z + h * 0.7), r * 0.97, h * 0.18, col, sides=7, rt=r, smooth=False, caps=(False, False), d=1)
    out += cyl((x, y, z + h * 0.88), r * 1.1, h * 0.12, "wood_dd", sides=7, smooth=False, caps=(True, True), d=1)

    return out


def planter():
    out = part()
    out += box(-0.43, -0.43, 0.0, 0.43, 0.43, 0.06, "graphite", skip="d")
    out += box(-0.47, -0.47, 0.05, 0.47, 0.47, 0.61, "stone_dd", c=0.02, skip="t")

    for ang in (0, 90, 180, 270):
        p = part()
        p += front(-0.37, 0.37, 0.13, 0.52, -0.47, "stone_dk", depth=0.008, d=0)
        p += plate(-0.37, 0.37, 0.29, 0.31, -0.480, "stone_dd", d=0)
        out += p.rot(ang, "Z")

    for s in (-1, 1):
        out += box(-0.50, s * 0.50, 0.592, 0.50, s * 0.40, 0.67, "wood_lt", c=0.012, skip="d")
        out += box(s * 0.50, -0.40, 0.592, s * 0.40, 0.40, 0.67, "wood", c=0.012, skip="dfb")

    out += deck(-0.41, 0.41, -0.41, 0.41, 0.625, "soil", cast=True)

    if lk.LOD == 0:
        r = rng(4)

        for i, x in enumerate((-0.285, -0.095, 0.095, 0.285)):
            for j, y in enumerate((-0.285, -0.095, 0.095, 0.285)):
                inner = i in (1, 2) and j in (1, 2)
                z = 0.74 + (0.045 if inner else 0.0) + r.random() * 0.02
                out += blob((x, y, z), (0.11, 0.11, 0.105 + r.random() * 0.02), LEAF_L if (i + j) % 3 == 0 else LEAF, sub=0, jitter=0.09, seed=i * 4 + j)
    else:
        for i, x in enumerate((-0.2, 0.2)):
            for j, y in enumerate((-0.2, 0.2)):
                out += blob((x, y, 0.74), (0.22, 0.22, 0.14), LEAF_L if (i + j) % 2 == 0 else LEAF, sub=0, jitter=0.09, seed=i * 4 + j)

    out += cup(0.03, -0.445, 0.67, 0.2, 0.048)

    return out


def cwall():
    out = part()

    for x in (-0.425, 0.425):
        out += box(x - 0.075, -0.08, 0.0, x + 0.075, 0.08, 0.16, "stone_dk", c=0.012, skip="d")
        out += box(x - 0.065, -0.066, 0.15, x + 0.065, 0.066, 1.62, "stone", skip="dt")
        out += box(x - 0.075, -0.08, 1.60, x + 0.075, 0.08, 1.68, "stone_dk", skip="d")
        out += box(x - 0.07, -0.074, 1.67, x + 0.07, 0.074, 1.80, "stone_lt", c=0.022, skip="d")

        for y, s in ((-0.069, -1), (0.069, 1)):
            for z0, z1, col in ((0.28, 0.98, "stone_dk"), (1.12, 1.48, "stone_lt")):
                out += face([(x - 0.038, y, z0), (x + 0.038, y, z0), (x + 0.038, y, z1), (x - 0.038, y, z1)], col, d=0, cast=False, towards=(0, s, 0))

    n = (7, 5, 3)[lk.LOD]
    w = (0.007, 0.012, 0.022)[lk.LOD]

    for i in range(n):
        x = -0.33 + 0.66 * (i + 1) / (n + 1)
        out += box(x - w, -0.016, 0.07, x + w, 0.016, 1.62, "graphite", skip="td")

    for z0, z1 in ((0.05, 0.10), (1.24, 1.28), (1.60, 1.65)):
        out += box(-0.36, -0.022, z0, 0.36, 0.022, z1, "slate_dk", skip="lr", d=1 if z0 == 1.24 else None)

    for x in (-0.335, 0.33):
        out += box(x - 0.018, -0.024, 0.05, x + 0.018, 0.024, 1.65, "slate_dk", skip="td")

    for z in (0.28, 1.37):
        out += box(-0.355, -0.032, z - 0.025, -0.30, 0.032, z + 0.025, "graphite_dk", d=0)

    out += box(0.20, -0.035, 0.84, 0.27, 0.035, 0.92, "steel_dk", d=0)

    return out


def bench():
    out = part()

    for x in (-0.755, 0.755):
        out += box(x - 0.10, -0.215, 0.0, x + 0.10, 0.215, 0.05, "graphite", c=0.012, skip="d")
        out += box(x - 0.08, -0.19, 0.04, x + 0.08, 0.19, 0.34, "slate_dk", c=0.016, skip="dt")
        out += box(x - 0.092, -0.205, 0.30, x + 0.092, 0.205, 0.335, "graphite", skip="t", d=0)

    out += box(-1.0, -0.25, 0.33, 1.0, 0.25, 0.45, "stone", c=0.026, top="stone_lt")

    for y in (-0.085, 0.085):
        out += deck(-0.975, 0.975, y - 0.007, y + 0.007, 0.451, "stone_dk", d=0)

    out += deck(-0.04, 0.30, -0.22, 0.08, 0.453, "canvas", d=1)
    out += deck(-0.01, 0.27, 0.025, 0.055, 0.455, "teal", d=0)

    for y in (-0.19, -0.15, -0.11):
        out += deck(-0.01, 0.10, y, y + 0.012, 0.455, "slate_lt", d=0)

    out += cup(0.20, -0.04, 0.453, 0.19, 0.055, "wood_dk", "canvas")

    return out


def square(h, z, cx=0.0, cy=0.0):
    return [(cx - h, cy - h, z), (cx + h, cy - h, z), (cx + h, cy + h, z), (cx - h, cy + h, z)]


def lamp():
    out = part()
    out += box(-0.25, -0.25, 0.0, 0.25, 0.25, 0.14, "stone_dk", c=0.025, skip="d")
    out += loft([square(0.21, 0.13), square(0.175, 0.2), square(0.165, 0.5), square(0.13, 0.58), square(0.095, 3.58), square(0.13, 3.62)], lambda j, i: ("stone_dk", "stone", "stone_dk", "stone", "stone_dd")[j], caps=(None, "stone_dd"))

    if lk.LOD == 0:
        for z, h in ((0.78, 0.15), (3.35, 0.12)):
            out += box(-h, -h, z, h, h, z + 0.05, "stone_dd", skip="")

    out += box(-0.13, -0.13, 3.62, 0.13, 0.13, 3.70, "slate_lt", skip="")
    out += loft([square(0.125, 3.70), square(0.175, 4.2)], "lamp")

    for sx in (-1, 1):
        for sy in (-1, 1):
            out += rod((sx * 0.135, sy * 0.135, 3.68), (sx * 0.187, sy * 0.187, 4.21), 0.017, "stone_dd", d=1)

    out += loft([square(0.19, 4.19), square(0.25, 4.22), square(0.25, 4.27), square(0.10, 4.41), square(0.05, 4.42)], lambda j, i: ("stone_dd", "stone_dd", "slate", "slate_dk")[j], caps=("stone_dd", "slate_dk"))
    out += cyl((0, 0, 4.41), 0.045, 0.09, "stone_dd", sides=6, rt=0.01, smooth=False, d=0)

    return out


def streetlight():
    out = part()
    py = 1.035
    out += box(-0.52, 0.51, 0.0, 0.52, 1.56, 0.50, "concrete_lt", c=0.07, skip="d")
    out += box(-0.40, 0.63, 0.50, 0.40, 1.44, 0.62, "concrete", c=0.035, skip="d")
    out += tube([(0, py, 0.6), (0, py, 0.95), (0, py, 7.25)], [0.30, 0.215, 0.095], 8, "steel_lt", caps=(False, False), smooth=False)

    for z, r in ((0.62, 0.32), (2.9, 0.19), (7.12, 0.135)):
        out += cyl((0, py, z), r, 0.1, "steel", sides=8, smooth=False, caps=(True, True), d=0)

    out += tube([(0, py, 7.2), (0, 0.86, 7.55), (0, 0.45, 7.76), (0, -0.2, 7.76)], [0.095, 0.085, 0.075, 0.07], 6, "steel", caps=(True, False), smooth=False)
    out += tube([(0, py - 0.08, 6.65), (0, 0.45, 7.7)], 0.03, 4, "steel_dk", caps=(False, False), smooth=False, d=0)
    out += loft([[(-0.26, -1.42, 7.50), (0.26, -1.42, 7.50), (0.28, -0.16, 7.50), (-0.28, -0.16, 7.50)], [(-0.35, -1.56, 7.62), (0.35, -1.56, 7.62), (0.35, -0.11, 7.62), (-0.35, -0.11, 7.62)], [(-0.33, -1.50, 7.80), (0.33, -1.50, 7.80), (0.33, -0.13, 7.80), (-0.33, -0.13, 7.80)], [(-0.18, -1.22, 7.99), (0.18, -1.22, 7.99), (0.2, -0.3, 7.99), (-0.2, -0.3, 7.99)]], lambda j, i: ("steel", "white_dk", "white")[j], caps=("slate", "white_dk"))
    out += box(-0.18, -1.37, 7.40, 0.18, -0.34, 7.51, "amber", c=0.02, skip="t")
    out += box(-0.09, 0.73, 1.14, 0.09, 0.79, 1.46, "slate_lt", skip="b", d=1)
    out += plate(-0.035, 0.035, 1.36, 1.39, 0.728, "teal", d=0)

    return out


def chair():
    out = part()
    out += box(-0.23, -0.235, 0.415, 0.23, 0.235, 0.455, "wood", c=0.012, top="wood_lt")
    out += box(-0.19, -0.195, 0.37, 0.19, 0.195, 0.415, "wood_dd", skip="t", d=0)

    for x in (-0.195, 0.165):
        out += box(x, -0.215, 0.0, x + 0.032, -0.183, 0.42, "wood_dd", skip="td")
        out += box(x, 0.183, 0.0, x + 0.032, 0.215, 0.72, "wood_dd", skip="d")

    out += box(-0.215, 0.175, 0.68, 0.215, 0.225, 0.85, "wood_lt", c=0.014)
    out += box(-0.18, 0.19, 0.55, 0.18, 0.21, 0.60, "wood", d=0)

    return out


def cafe():
    out = part()
    out += prism(ngon(0.20, 8, 0.0, 0.21), 0.0, 0.05, "graphite", c=0.015)
    out += cyl((0.0, 0.21, 0.04), 0.05, 0.64, "black", sides=7, smooth=False, caps=(False, False))
    out += cyl((0.0, 0.21, 0.64), 0.12, 0.06, "graphite", sides=8, rt=0.18, smooth=False, caps=(False, False), d=0)
    out += prism(ngon(0.395, 12, 0.0, 0.21), 0.69, 0.75, "wood_lt", c=0.018, bottom=True)

    if lk.LOD == 0:
        for y in (0.07, 0.35):
            out += deck(-0.33, 0.33, y - 0.005, y + 0.005, 0.751, "wood")

    left = chair().rot(90, "Z").move(-0.585, 0.205, 0.0)
    right = chair().rot(-90, "Z").move(0.585, 0.205, 0.0)
    near = chair().rot(180, "Z").move(0.0, -0.362, 0.0)
    out += left + right + near
    out += cup(-0.17, 0.30, 0.75, 0.095, 0.038, "white", "teal")
    out += cup(0.18, 0.12, 0.75, 0.095, 0.038, "canvas", "wine")

    return out


def tent():
    out = part()
    eave = 2.58
    corners = [(-1.80, -1.80), (1.80, -1.80), (1.80, 1.80), (-1.80, 1.80)]

    for k in range(4):
        a = Vector((corners[k][0], corners[k][1], eave))
        b = Vector((corners[(k + 1) % 4][0], corners[(k + 1) % 4][1], eave))
        ta = Vector((a.x * 0.31, a.y * 0.31, 3.08))
        tb = Vector((b.x * 0.31, b.y * 0.31, 3.08))
        cuts = (0.0, 0.3, 0.7, 1.0)

        for i in range(3):
            col = "canvas" if i == 1 else ("wine" if k % 2 else "wine_lt")
            out += face([a.lerp(b, cuts[i]), a.lerp(b, cuts[i + 1]), ta.lerp(tb, cuts[i + 1]), ta.lerp(tb, cuts[i])], col, towards=(0, 0, 1))
            out += face([a.lerp(b, cuts[i]) - Vector((0, 0, 0.02)), a.lerp(b, cuts[i + 1]) - Vector((0, 0, 0.02)), ta.lerp(tb, cuts[i + 1]) - Vector((0, 0, 0.02)), ta.lerp(tb, cuts[i]) - Vector((0, 0, 0.02))], "wine_dk", cast=False, towards=(0, 0, -1))

        apex = Vector((0, 0, 3.60))
        sa = Vector((ta.x * 0.78, ta.y * 0.78, 3.10))
        sb = Vector((tb.x * 0.78, tb.y * 0.78, 3.10))
        out += face([sa, sb, apex], "wine" if k % 2 else "wine_lt", towards=(sa.x + sb.x, sa.y + sb.y, 1.0))
        out += face([ta, tb, sb, sa], "wine_dk", towards=(0, 0, 1))
        out += rod(a, ta, 0.02, "wine_dk", d=0)

        mid = (a + b) / 2
        nx, ny = (mid.x / 1.8, mid.y / 1.8)
        n = 6 if lk.LOD == 0 else 1

        for i in range(n):
            p0 = a.lerp(b, i / n)
            p1 = a.lerp(b, (i + 1) / n)
            col = "wine_dk" if i % 2 == 0 else "wine"
            drop = [p0, p1, p1 - Vector((0, 0, 0.2)), p1.lerp(p0, 0.5) - Vector((0, 0, 0.28 if lk.LOD == 0 else 0.2)), p0 - Vector((0, 0, 0.2))]
            out += face(drop, col, towards=(nx, ny, 0))
            out += face([p - Vector((nx * 0.015, ny * 0.015, 0)) for p in drop], "wine_dk", cast=False, towards=(-nx, -ny, 0))

    out += plate(-0.95, 0.95, 2.40, 2.54, -1.815, "canvas", d=1)
    out += plate(-0.55, 0.55, 2.455, 2.485, -1.818, "teal", d=0)

    for x in (-1.62, 1.62):
        for y in (-1.62, 1.62):
            out += rod((x, y, 0.1), (x, y, 2.6), 0.032, "steel", sides=5)
            out += cyl((x, y, 0.0), 0.15, 0.1, "graphite", sides=8, smooth=False, caps=(False, False))
            out += cyl((x, y, 0.1), 0.12, 0.16, "graphite", sides=8, rt=0.05, smooth=False, d=0)

    out += box(-1.75, 1.715, 0.02, 1.75, 1.755, 2.40, "wine_dk")

    for x in (-0.9, 0.0, 0.9):
        out += side(1.70, 1.714, 0.1, 2.3, x, 1, "wine", d=0)
        out += plate(x - 0.012, x + 0.012, 0.06, 2.36, 1.713, "wine", d=0)

    out += box(-1.72, -1.61, 1.02, 1.72, -1.09, 1.08, "wood", top="wood_lt", c=0.012)

    for x in (-1.45, 1.45):
        for y in (-1.55, -1.15):
            out += rod((x, y, 0.0), (x, y, 1.03), 0.022, "graphite", d=1)

    out += box(-1.05, -1.45, 1.08, -0.78, -1.24, 1.13, "petal", d=1)
    out += box(-0.22, -1.48, 1.08, 0.02, -1.30, 1.12, "teal", d=1)
    out += box(0.14, -1.42, 1.08, 0.40, -1.24, 1.115, "teal_lt", d=1)
    out += lathe([(0.07, 1.08, "canvas_dk"), (0.14, 1.16, "teal_dk"), (0.11, 1.17, "canvas"), (0.0, 1.19, "canvas")], 8, at=(1.05, -1.35, 0), smooth=False, d=1)

    return out


def planks(x0, x1, z0, z1, y, n, cols=("wood_dk", "wood_dd")):
    out = part()
    n = n if lk.LOD == 0 else 1
    w = (x1 - x0) / n

    for i in range(n):
        out += plate(x0 + i * w + (0.008 if i else 0), x0 + (i + 1) * w, z0, z1, y, cols[i % 2], cast=True)

    return out


def kiosk():
    out = part()
    out += box(-0.80, -0.48, 0.0, 0.80, 1.24, 2.46, "wood_dd", skip="dt")
    out += planks(-0.80, 0.80, 0.0, 0.94, -0.488, 8, ("wood_dk", "wood"))
    out += planks(-0.80, -0.62, 0.94, 2.46, -0.488, 1)
    out += planks(0.62, 0.80, 0.94, 2.46, -0.488, 1)
    out += planks(-0.62, 0.62, 2.02, 2.46, -0.488, 5)

    for ang, w, off in ((90, 1.72, 0.808), (-90, 1.72, 0.808)):
        p = planks(-w / 2, w / 2, 0.0, 2.46, -off, 8, ("wood_dk", "wood"))
        p.rot(ang, "Z").move(0, 0.38, 0)
        out += p

    back = planks(-0.80, 0.80, 0.0, 2.46, -1.248, 7, ("wood_dk", "wood"))
    out += back.rot(180, "Z")

    for x in (-0.88, 0.88):
        for y in (-0.45, 1.15):
            out += box(x - 0.09, y - 0.09, 0.0, x + 0.09, y + 0.09, 2.46, "wood", c=0.016, skip="dt")
            out += box(x - 0.1, y - 0.1, 0.0, x + 0.1, y + 0.1, 0.12, "graphite", skip="d", d=0)

    for s in (-1, 1):
        out += box(s * 0.98, -0.36, 0.86, s * 0.88, 1.07, 0.96, "wood_lt", d=1)
        out += box(s * 0.97, -0.36, 2.28, s * 0.88, 1.07, 2.38, "wood_dk", d=1)

    out += plate(-0.62, 0.62, 1.02, 2.0, -0.492, "black")

    for z in (1.38, 1.66):
        out += box(-0.55, -0.50, z, 0.55, -0.493, z + 0.035, "wood_dd", skip="b", d=0)

        for i, x in enumerate((-0.4, -0.2, 0.05, 0.28, 0.42)):
            out += plate(x - 0.045, x + 0.045, z + 0.035, z + 0.13 + 0.03 * (i % 2), -0.497, ("canvas_dk", "teal_dk", "wood")[i % 3], d=0)

    out += frame(-0.68, 0.68, 0.96, 2.06, -0.488, 0.07, "wood_lt", depth=0.035, d=1)
    out += box(-0.80, -0.75, 0.98, 0.80, -0.49, 1.05, "wood_lt", c=0.016)

    for x in (-0.62, 0.62):
        out += rod((x, -0.50, 0.72), (x, -0.70, 0.99), 0.025, "wood_dk", d=0)

    n = 6 if lk.LOD == 0 else 1

    for i in range(n):
        x0 = -0.78 + 1.56 * i / n
        x1 = -0.78 + 1.56 * (i + 1) / n - (0.01 if n > 1 else 0)
        col = "wood_lt" if i % 2 == 0 else "wood"
        top = [(x0, -0.50, 2.05), (x1, -0.50, 2.05), (x1, -1.27, 1.62), (x0, -1.27, 1.62)]
        out += face(top, col, towards=(0, -0.5, 1))
        out += face([(p[0], p[1], p[2] - 0.035) for p in top], "wood_dk", cast=False, towards=(0, 0.5, -1))

    out += box(-0.79, -1.275, 1.585, 0.79, -1.245, 1.63, "wood_dk", d=1)

    for x in (-0.72, 0.72):
        out += rod((x, -0.52, 1.55), (x, -1.18, 1.65), 0.014, "graphite", d=0)

    out += box(-0.66, -0.73, 2.24, 0.66, -0.58, 2.80, "white_dk", c=0.025)
    out += plate(-0.58, 0.58, 2.31, 2.73, -0.735, "canvas")
    out += plate(-0.58, 0.58, 2.31, 2.37, -0.737, "teal", d=1)
    out += disc(-0.30, 2.54, -0.736, 0.115, "teal_dk", n=10, d=1)
    out += disc(-0.30, 2.54, -0.747, 0.06, "canvas", n=8, d=0, depth=0.003)

    for z, x1 in ((2.60, 0.45), (2.47, 0.30)):
        out += plate(-0.08, x1, z, z + 0.05, -0.737, "slate", d=0)

    out += box(-1.0, -0.58, 2.46, 1.0, 1.27, 2.62, "slate", c=0.035, top="slate_dk")
    out += box(-0.88, -0.46, 2.62, 0.88, 1.15, 2.68, "graphite", c=0.02, skip="d")

    for z in (0.62, 1.12, 1.62):
        w = part()
        w += frame(-0.17, 0.17, z, z + 0.34, -0.814, 0.035, "wood_lt", depth=0.02, d=1)
        w += plate(-0.14, 0.14, z + 0.03, z + 0.31, -0.818, "glass_dd")
        w += face([(-0.1, -0.821, z + 0.06), (-0.05, -0.821, z + 0.06), (0.08, -0.821, z + 0.28), (0.03, -0.821, z + 0.28)], "glass_dk", d=0, ao=False, cast=False, towards=(0, -1, 0))
        out += w.rot(90, "Z").move(0, 0.38, 0)

    door = part()
    door += frame(-0.44, 0.44, 0.0, 2.12, -1.25, 0.06, "wood_lt", depth=0.02, d=1)
    door += handle(0.28, 1.05, 0.14, -1.27, "graphite", vertical=True)
    out += door.rot(180, "Z")

    return out


def mapboard():
    out = part()

    for x in (-0.64, 0.64):
        out += box(x - 0.07, -0.055, 0.0, x + 0.07, 0.05, 2.26, "stone", c=0.016, skip="d")
        out += box(x - 0.09, -0.12, 0.0, x + 0.09, 0.12, 0.07, "stone_dd", c=0.016, skip="d", d=1)

    out += box(-0.71, -0.04, 0.882, 0.71, 0.04, 1.958, "stone_dk", c=0.012)

    for s in (-1, 1):
        p = part()
        p += frame(-0.71, 0.71, 0.88, 1.96, -0.04, 0.075, "stone_lt", depth=0.025, d=1)
        p += plate(-0.62, 0.62, 0.97, 1.87, -0.043, "canvas")
        patches = [(-0.56, -0.30, 1.62, 1.80, "wood"), (-0.56, -0.34, 1.34, 1.52, "olive"), (-0.56, -0.28, 1.05, 1.22, "wood_lt"), (-0.18, 0.22, 1.24, 1.66, "olive"), (-0.08, 0.10, 1.34, 1.52, "olive_lt"), (-0.18, 0.04, 1.05, 1.16, "bloom"), (0.32, 0.56, 1.64, 1.80, "olive_dk"), (0.30, 0.56, 1.30, 1.50, "wood"), (0.24, 0.52, 1.04, 1.18, "olive"), (-0.14, 0.14, 1.72, 1.80, "slate_lt")]

        for x0, x1, z0, z1, col in patches:
            p += plate(x0, x1, z0, z1, -0.046, col, d=1)

        for x, z in ((-0.67, 1.36), (0.67, 1.65)):
            p += plate(x - 0.07, x + 0.07, z - 0.09, z + 0.09, -0.068, "amber", d=1)
            p += plate(x - 0.045, x + 0.045, z - 0.02, z + 0.01, -0.070, "teal_dk", d=0)

        p += disc(0.02, 1.44, -0.046, 0.028, "red", n=6, d=0)
        p += plate(0.30, 0.50, 0.905, 0.95, -0.068, "teal", d=0)

        if s > 0:
            p.rot(180, "Z")

        out += p

    for y in (-0.205, 0.205):
        out += box(-0.61, y - 0.008, 2.255, 0.61, y + 0.008, 2.29, "stone_dd", d=1)

        for i in range(7 if lk.LOD == 0 else 0):
            x = -0.55 + i * 0.172
            for s in (-1, 1):
                out += face([(x - 0.065, y + s * 0.006, 2.258), (x + 0.065, y + s * 0.006, 2.258), (x, y + s * 0.006, 2.12)], ("wine", "teal", "canvas")[i % 3], cast=False, towards=(0, s, 0))

    out += loft([[(-0.75, -0.25, 2.26), (0.75, -0.25, 2.26), (0.75, 0.25, 2.26), (-0.75, 0.25, 2.26)], [(-0.75, -0.25, 2.30), (0.75, -0.25, 2.30), (0.75, 0.25, 2.30), (-0.75, 0.25, 2.30)], [(-0.70, -0.08, 2.40), (0.70, -0.08, 2.40), (0.70, 0.08, 2.40), (-0.70, 0.08, 2.40)]], lambda j, i: "stone_lt" if j else "stone", caps=("stone_dk", "stone_lt"))

    return out


def banner():
    out = part()
    out += box(-0.25, -0.25, 0.0, 0.25, 0.25, 0.30, "stone_dk", c=0.04, skip="d")
    out += box(-0.18, -0.18, 0.29, 0.18, 0.18, 0.46, "stone", c=0.04, skip="d")
    out += loft([square(0.075, 0.45), square(0.055, 4.94)], "stone", caps=(None, "stone_dd"))

    for z in (0.62, 2.5):
        out += box(-0.095, -0.095, z, 0.095, 0.095, z + 0.06, "stone_dd", d=0)

    out += box(-0.92, -0.028, 4.86, 0.92, 0.028, 4.94, "stone_dd")

    for s in (-1, 1):
        for za, zb, col in ((4.82, 3.34, "wine"), (3.34, 3.14, "canvas"), (3.14, 2.86, "wine_dk")):
            for side_y, to in ((-0.01, -1), (0.01, 1)):
                out += face([(s * 0.14, side_y, za), (s * 0.84, side_y, za), (s * 0.84, side_y, zb), (s * 0.14, side_y, zb)], col, towards=(0, to, 0))

        for turn in (0, 180):
            badge = disc(0.0, 4.10, -0.012, 0.17, "canvas", n=10, depth=0.004, d=1) + disc(0.0, 4.10, -0.017, 0.085, "teal", n=8, depth=0.004, d=0)
            out += badge.rot(turn, "Z").move(s * 0.49, 0, 0)

        out += box(s * 0.13, -0.035, 2.80, s * 0.85, 0.035, 2.88, "stone_lt", d=1)
        out += box(s * 0.20, -0.016, 4.80, s * 0.26, 0.016, 4.88, "stone_dk", d=0)
        out += box(s * 0.72, -0.016, 4.80, s * 0.78, 0.016, 4.88, "stone_dk", d=0)

    return out


def fountain():
    out = part()

    def octo(h, cut, z):
        return [(-h + cut, -h, z), (h - cut, -h, z), (h, -h + cut, z), (h, h - cut, z), (h - cut, h, z), (-h + cut, h, z), (-h, h - cut, z), (-h, -h + cut, z)]

    rings = [octo(2.40, 0.55, 0.0), octo(2.40, 0.55, 0.22), octo(2.26, 0.52, 0.24), octo(2.26, 0.52, 0.52), octo(2.36, 0.55, 0.56), octo(2.36, 0.55, 0.70), octo(2.28, 0.52, 0.72), octo(2.02, 0.45, 0.72), octo(1.97, 0.44, 0.56)]
    cols = ("stone_dk", "stone", "stone_dk", "stone", "stone", "stone_lt", "stone_lt", "water_dk")
    out += loft(rings, lambda j, i: cols[j], wind=True)
    out += face(octo(1.99, 0.45, 0.62), "water_dk", towards=(0, 0, 1), cast=True)

    if lk.LOD < 2:
        out += loft([octo(1.55, 0.42, 0.623), octo(1.2, 0.35, 0.624)], "water", outward=(0, 0, -5))

    out += prism(ngon(0.48, 8), 0.58, 0.72, "stone", c=0.04, top="stone_lt")
    out += cyl((0, 0, 0.70), 0.2, 0.18, "stone_dk", sides=8, rt=0.14, smooth=False, caps=(False, True))
    out += tube([(0, 0, 0.85), (0, 0, 2.2), (0, 0, 3.2), (0, 0, 3.75), (0, 0, 3.88)], [0.11, 0.075, 0.055, 0.12, 0.02], 6, lambda i, j: "water_lt" if j > 1 else "water", caps=(False, False), smooth=False)

    for k in range(8):
        diag = k % 2 == 0
        a = math.pi / 4 * k + math.pi / 4
        dx, dy = math.cos(a), math.sin(a)

        if diag:
            path = [(0.1, 0.9), (0.2, 2.3), (0.38, 3.35), (0.65, 3.55), (0.95, 3.0), (1.2, 1.9), (1.38, 0.64)]
            radii = [0.06, 0.05, 0.045, 0.045, 0.05, 0.055, 0.075]
        else:
            path = [(0.3, 0.78), (0.52, 1.75), (0.8, 2.28), (1.1, 2.36), (1.34, 1.85), (1.5, 0.64)]
            radii = [0.045, 0.038, 0.035, 0.038, 0.045, 0.062]

        if lk.LOD:
            path = path[::2] + ([path[-1]] if len(path) % 2 == 0 else [])
            radii = radii[::2] + ([radii[-1]] if len(radii) % 2 == 0 else [])

        out += tube([(dx * r, dy * r, z) for r, z in path], radii, 4, lambda i, j: "water_lt" if j % 2 else "water", caps=(False, False), smooth=False, d=None if diag else 1)

        if lk.LOD == 0:
            end = path[-1][0]
            out += lk.torus((dx * end, dy * end, 0.63), 0.15, 0.018, "water_lt", segs=8, sides=3, axis="Z")

            for t, z in ((0.9, 0.80), (1.12, 0.74)):
                out += blob((dx * end * t, dy * end * t, z), (0.04, 0.04, 0.06), ("water_lt", "water_lt", "water"), sub=0, jitter=0.1, seed=k)

    out += box(0.60, -2.24, 0.72, 1.06, -2.04, 1.06, "slate_lt", c=0.045, skip="d")
    out += plate(0.62, 1.04, 0.84, 0.91, -2.245, "teal", d=0)
    out += lk.torus((0.83, -2.14, 1.08), 0.11, 0.016, "graphite", segs=8, sides=4, axis="Y")
    out += cup(1.32, -2.12, 0.72, 0.2, 0.055, "wood_dk", "canvas")

    return out


OPTS = {"ao": 0.5, "reach": 1.0, "grime": 0.1, "grime_h": 0.5}
LEAFY = {"ao": 0.42, "reach": 1.4, "grime": 0.0, "under": 0.18, "errors": (0.04, 0.11)}

ALL = {
    "fence": (fence, {"ao": 0.22, "reach": 0.5, "grime": 0.1, "grime_h": 0.4}),
    "hedge": (hedge, {"ao": 0.45, "reach": 0.5, "grime": 0.12, "grime_h": 0.35, "errors": (0.035, 0.1)}),
    "shrub": (shrub, LEAFY),
    "tree": (tree, LEAFY),
    "tree2": (tree2, LEAFY),
    "pit": (pit, LEAFY),
    "flowers": (flowers, {"ao": 0.4, "reach": 0.35, "grime": 0.08, "grime_h": 0.2}),
    "planter": (planter, OPTS),
    "cwall": (cwall, {"ao": 0.32, "reach": 0.6, "grime": 0.1, "grime_h": 0.4}),
    "bench": (bench, OPTS),
    "lamp": (lamp, OPTS),
    "streetlight": (streetlight, OPTS),
    "cafe": (cafe, OPTS),
    "tent": (tent, {"ao": 0.38, "reach": 1.0, "grime": 0.1, "grime_h": 0.5, "under": 0.05}),
    "kiosk": (kiosk, OPTS),
    "mapboard": (mapboard, OPTS),
    "banner": (banner, {"ao": 0.3, "reach": 0.7, "grime": 0.08}),
    "fountain": (fountain, {"ao": 0.35, "reach": 1.0, "grime": 0.08, "grime_h": 0.3}),
}
