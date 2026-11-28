import math

from mathutils import Matrix, Vector

import fr_parts as p
from fr_kit import Mesh, hash01, pick


def barrel():
    m = Mesh(30)
    p.barrel(m, 0, 0, 0.0, 0.295, 0.8, 12, "wood")

    return m


def crate():
    m = Mesh(31)
    p.crate(m, -0.24, 0.0, 0.0, 1.1, 0.96, 0.99, 0, "wood")
    p.sack(m, 0.56, -0.18, 0.0, 0.88, 25)
    p.sack(m, 0.55, 0.26, 0.0, 0.66, -50, "straw")

    return m


def box():
    m = Mesh(32)
    p.crate(m, -0.45, 0.04, 0.0, 1.05, 1.12, 0.72, 0, "wood")
    p.crate(m, -0.5, 0.02, 0.72, 0.68, 0.7, 0.5, 14, "gray")
    p.crate(m, 0.5, 0.2, 0.0, 0.78, 0.72, 0.62, -9, "ochre", False)
    p.sack(m, 0.7, -0.32, 0.0, 0.9, 10)
    p.sack(m, 0.2, -0.38, 0.0, 0.74, 70, "straw")

    return m


def chest():
    m = Mesh(33)

    def trunk(x, z, w, d, h, fam, band):
        m.box((x - w / 2, -d / 2, z), (x + w / 2, d / 2, z + h * 0.72), fam, 0.035, skip="z" if z == 0 else "")
        m.box((x - w / 2 - 0.012, -d / 2 - 0.012, z + h * 0.72), (x + w / 2 + 0.012, d / 2 + 0.012, z + h), fam + "_d", 0.06)

        for s in (-0.3, 0.3):
            u = x + s * w
            m.box((u - 0.03, -d / 2 - 0.02, z + 0.01), (u + 0.03, d / 2 + 0.02, z + h + 0.008), band, skip="z")

        m.box((x - 0.06, -d / 2 - 0.035, z + h * 0.55), (x + 0.06, -d / 2, z + h * 0.78), "gold", skip="Y")

    trunk(0.0, 0.0, 1.06, 0.5, 0.52, "teal", "wood_x")
    trunk(-0.07, 0.52, 0.86, 0.44, 0.42, "red", "ochre_d")
    trunk(0.06, 0.94, 0.6, 0.38, 0.3, "wood", "iron")
    m.beam((-0.18, 0.0, 1.31), (0.3, 0.0, 1.31), 0.24, 0.16, "canvas", 0.07)

    return m


def bench():
    m = Mesh(34)
    p.trough(m, 0.0, 0.0, 1.8, 0.42, 0.5)

    for x in (-1.02, 0.0, 1.02):
        m.box((x - 0.07, 0.08 if x == 0 else -0.07, 0.0), (x + 0.07, 0.2 if x == 0 else 0.07, 1.32), "wood_d", 0.025, skip="z")

    m.beam((-1.1, 0.0, 1.39), (1.1, 0.0, 1.39), 0.15, 0.14, "wood", 0.035)

    m.box((0.42, -0.11, 1.1), (0.84, 0.11, 1.475), "red", 0.04)
    m.box((0.42, -0.12, 1.17), (0.84, 0.12, 1.23), "cream")

    return m


def fence():
    m = Mesh(35)

    for x in (-1.13, 0.0, 1.13):
        m.box((x - 0.075, -0.015, -0.45), (x + 0.075, 0.095, 1.37), "wood" if x else "wood_d", 0.02, skip="z")

    for k, z in enumerate((0.24, 0.65, 1.06)):
        split = -0.35 + 0.42 * k

        for j, (u0, u1) in enumerate(((-1.2, split - 0.006), (split + 0.006, 1.2))):
            dz = 0.02 * ((k + j) % 2) - 0.01
            col = ("wood_l", "gray_l", "wood_l", "wood", "gray_l", "wood_l")[k * 2 + j]
            m.beam((u0, -0.05, z + 0.16 + dz), (u1, -0.05, z + 0.16 - dz), 0.07, 0.3, col, 0.018)

    return m


def lantern():
    m = Mesh(36)
    m.prism((0, 0), -0.4, 0.22, 0.34, 0.3, 8, "stone_d", top="stone")
    m.prism((0, 0), 0.22, 0.42, 0.2, 0.17, 8, "stone")
    m.prism((0, 0), 0.42, 2.38, 0.105, 0.08, 8, lambda i, j: pick("wood_d", i, 1) if False else ("wood_d" if i % 2 else "wood"), top=False)

    for z in (0.5, 1.55, 2.3):
        m.prism((0, 0), z, z + 0.08, 0.125, 0.125, 8, "iron", bottom=True)

    m.prism((0, 0), 2.38, 2.48, 0.12, 0.27, 6, "iron_d", bottom=True)
    m.prism((0, 0), 2.48, 2.84, 0.2, 0.28, 6, "lamp", top=False)

    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        m.beam((math.cos(a) * 0.205, math.sin(a) * 0.205, 2.47), (math.cos(a) * 0.285, math.sin(a) * 0.285, 2.85), 0.035, 0.035, "iron_d", skip="xX")

    m.prism((0, 0), 2.83, 2.9, 0.42, 0.4, 6, "iron", bottom=True)
    m.prism((0, 0), 2.9, 3.1, 0.4, 0.11, 6, "iron_d", top=False)
    m.prism((0, 0), 3.1, 3.2, 0.12, 0.05, 6, "gold", bottom=True)

    return m


def pole():
    m = Mesh(37)
    m.tube([(0.0, 0.0, -0.6), (0.0, 0.0, 0.5), (0.02, 0.0, 3.4), (0.0, 0.0, 6.5)], [0.17, 0.16, 0.13, 0.095], 8, lambda i, j: "wood_d" if i % 3 == 0 else "wood", cap_top=False)
    m.prism((0, 0), 0.0, 0.26, 0.3, 0.22, 8, "stone_d", top="stone")

    for z in (1.25, 4.3):
        m.prism((0.01, 0), z, z + 0.09, 0.17 - z * 0.011, 0.17 - z * 0.011, 8, "iron", bottom=True)

    m.beam((0.62, 0.18, -0.35), (0.05, 0.01, 2.1), 0.11, 0.11, "wood_d", 0.02)
    m.prism((0, 0), 6.46, 6.58, 0.14, 0.14, 8, "wood_x", bottom=True)
    m.prism((0, 0), 6.58, 6.66, 0.12, 0.05, 8, "tin_d")
    m.prism((0, 0), 6.64, 6.72, 0.045, 0.06, 6, "teal")
    m.prism((0, 0), 6.72, 6.82, 0.085, 0.03, 6, "teal_l", bottom=True)
    return m


def watertower():
    m = Mesh(38)
    deck_z = 6.4

    def leg(sx, sy, z):
        k = 1.25 - 0.3 * z / deck_z

        return Vector((sx * k, sy * k, z))

    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for sx, sy in corners:
        m.beam(leg(sx, sy, 0.0), leg(sx, sy, deck_z), 0.2, 0.2, "wood_d", 0.035)
        m.box((sx * 1.25 - 0.17, sy * 1.25 - 0.17, -0.7), (sx * 1.25 + 0.17, sy * 1.25 + 0.17, 0.3), "stone", 0.05, skip="z")

    levels = [0.55, 2.45, 4.35, deck_z - 0.1]

    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]

        for k in range(len(levels) - 1):
            z0, z1 = levels[k], levels[k + 1]
            m.beam(leg(a[0], a[1], z1), leg(b[0], b[1], z1), 0.09, 0.14, "wood")
            first, second = (a, b) if k % 2 == 0 else (b, a)
            m.beam(leg(first[0], first[1], z0), leg(second[0], second[1], z1), 0.07, 0.07, "wood_l", skip="xX")

    p.deck(m, -1.38, 1.38, -1.38, 1.38, deck_z + 0.16, "wood")
    m.box((-1.4, -1.4, deck_z - 0.06), (1.4, 1.4, deck_z + 0.12), "wood_x", 0.03)
    z0 = deck_z + 0.16
    n = 14
    m.lathe((0, 0), [(1.14, z0), (1.2, z0 + 1.4), (1.15, z0 + 2.75)], n, lambda i, j: pick("red", i, 3), top=False)

    for z in (0.18, 0.95, 1.8, 2.52):
        r = 1.235
        m.prism((0, 0), z0 + z, z0 + z + 0.1, r, r, n, "iron", top="iron_l", bottom=True)

    zt = z0 + 2.75
    m.prism((0, 0), zt, zt + 0.12, 1.4, 1.42, n, "wood_x", bottom=True, top=False)
    m.lathe((0, 0), [(1.42, zt + 0.12), (0.8, zt + 0.66), (0.16, zt + 1.12)], n, lambda i, j: "tin" if i % 2 else "tin_l", top=False)
    m.prism((0, 0), zt + 1.08, zt + 1.28, 0.22, 0.12, n, "tin_d", top="tin_d")
    p.disc(m, 0, z0 + 1.38, 0.34, -1.19, "cream", 10, 0.06)
    p.disc(m, 0, z0 + 1.38, 0.16, -1.25, "teal", 10, 0.03)
    m.beam((0.75, -1.35, deck_z + 0.05), (0.75, -1.35, deck_z - 1.7), 0.14, 0.14, "iron")
    m.box((0.64, -1.46, deck_z - 1.95), (0.86, -1.24, deck_z - 1.68), "iron_d", 0.03)

    for s in (-0.18, 0.18):
        m.beam((s, 1.4, 0.0), (s, 1.1, deck_z + 0.1), 0.06, 0.06, "gray_d")

    for i in range(1, 16):
        t = i / 16.2
        y = 1.4 - 0.3 * t
        m.beam((-0.18, y, deck_z * t), (0.18, y, deck_z * t), 0.04, 0.04, "gray", skip="xX")

    return m


def headframe():
    m = Mesh(39)
    top = 8.7

    def leg(sx, sy, z):
        t = z / top

        return Vector((sx * (1.95 - 1.15 * t), sy * (1.95 - 1.15 * t), z))

    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for sx, sy in corners:
        m.beam(leg(sx, sy, 0.1), leg(sx, sy, top), 0.24, 0.24, "wood_d", 0.04)
        m.box((sx * 1.95 - 0.22, sy * 1.95 - 0.22, -0.9), (sx * 1.95 + 0.22, sy * 1.95 + 0.22, 0.28), "stone", 0.05, skip="z")

    levels = [0.4, 3.2, 5.9, top]

    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]

        for k in range(1, len(levels)):
            m.beam(leg(a[0], a[1], levels[k]), leg(b[0], b[1], levels[k]), 0.12, 0.18, "wood")

            if i != 0 or k > 1:
                first, second = (a, b) if (k + i) % 2 == 0 else (b, a)
                m.beam(leg(first[0], first[1], levels[k - 1]), leg(second[0], second[1], levels[k]), 0.09, 0.09, "wood_l", skip="xX")

    m.box((-1.05, -1.05, top - 0.02), (1.05, 1.05, top + 0.16), "wood_x", 0.04)
    wz = top + 1.0

    for s in (-0.28, 0.28):
        m.beam((s, -0.55, top + 0.1), (s, 0.0, wz), 0.12, 0.12, "iron")
        m.beam((s, 0.55, top + 0.1), (s, 0.0, wz), 0.12, 0.12, "iron")

    with m.at(0, 0, wz, yaw=90):
        n = 16
        outer = [(math.cos(2 * math.pi * i / n) * 0.82, math.sin(2 * math.pi * i / n) * 0.82) for i in range(n)]
        inner = [(x * 0.8, z * 0.8) for x, z in outer]

        for i in range(n):
            j = (i + 1) % n
            m.extrude([outer[i], outer[j], inner[j], inner[i]], -0.08, 0.08, "rust", "rust_d")

        for k in range(3):
            a = math.pi / 2 + k * 2 * math.pi / 3
            m.beam((0, 0, 0), (math.cos(a) * 0.68, 0, math.sin(a) * 0.68), 0.07, 0.1, "iron_l", skip="xX")

        p.disc(m, 0, 0, 0.17, 0.12, "iron_d", 8, 0.24)

    roof_z = top + 2.0

    for sx, sy in corners:
        m.beam((sx * 0.9, sy * 0.9, top + 0.1), (sx * 0.9, sy * 0.9, roof_z - 0.05), 0.11, 0.11, "wood_d")

    p.roof_y(m, -1.0, 1.0, -0.95, 0.95, [(-1.15, roof_z - 0.1), (0, roof_z + 0.48), (1.15, roof_z - 0.1)], "tin", "rust", 91, 0.1, "wood_d")
    m.beam((0.0, -0.78, wz), (0.0, -0.78, 1.55), 0.035, 0.035, "iron_d", skip="xX")
    m.lathe((0.0, -0.78), [(0.28, 0.9), (0.36, 1.5), (0.37, 1.55)], 10, "tin_d", top="ore", bottom=True)
    m.box((-0.85, -1.35, 0.0), (0.85, -0.2, 0.18), "wood_x", 0.03, skip="z")
    m.quad((-0.7, -1.2, 0.185), (0.7, -1.2, 0.185), (0.7, -0.35, 0.185), (-0.7, -0.35, 0.185), "void")

    with m.at(0.75, 0.95, 0.0):
        p.planks(m, -0.75, 0.75, 0.05, 1.55, "gray", (), 4)

        for yaw, y in ((180, 1.1),):
            with m.at(0, y, 0, yaw=yaw):
                p.planks(m, -0.75, 0.75, 0.05, 1.55, "gray", (), 5)

        for yaw, x in ((90, 0.75), (-90, -0.75)):
            with m.at(x, 0.55, 0, yaw=yaw):
                p.planks(m, -0.55, 0.55, 0.05, 1.55, "gray", (), 6)

        p.slope(m, -0.88, 0.88, (-0.18, 1.55), (1.25, 2.05), "tin", "rust", seed=93)

        for sx in (-0.75, 0.75):
            m.face(((sx, 0, 1.55), (sx, 1.1, 1.55), (sx, 1.1, 1.97))[:: 1 if sx > 0 else -1], "gray_d")

        m.quad((-0.75, 1.1, 1.55), (-0.75, 1.1, 1.97), (0.75, 1.1, 1.97), (0.75, 1.1, 1.55), "gray_d")
        m.box((-0.3, -0.05, 0.05), (0.3, 0.0, 1.3), "wood_x", skip="Y")

    p.crate(m, -1.2, 1.2, 0.0, 0.8, 0.8, 0.65, 15)
    p.barrel(m, -1.45, -0.2, 0.0, 0.3, 0.75, 10, "gray")

    return m


def orebin():
    m = Mesh(40)
    base = 2.35

    for sx in (-1, 1):
        for sy in (-1, 1):
            m.beam((sx * 1.38, sy * 1.38, 0.0), (sx * 1.12, sy * 1.12, base), 0.22, 0.22, "wood_d", 0.035)
            m.box((sx * 1.38 - 0.19, sy * 1.38 - 0.19, -0.7), (sx * 1.38 + 0.19, sy * 1.38 + 0.19, 0.2), "stone_d", 0.04, skip="z")

        m.beam((sx * 1.33, -1.33, 0.45), (sx * 1.16, 1.16, 1.95), 0.08, 0.12, "wood")
        m.beam((sx * 1.14, -1.14, 2.1), (sx * 1.14, 1.14, 2.1), 0.1, 0.18, "wood")

    m.beam((-1.33, 1.33, 0.45), (1.16, 1.16, 1.95), 0.12, 0.08, "wood")
    m.beam((-1.14, -1.14, 2.1), (1.14, -1.14, 2.1), 0.18, 0.1, "wood")
    m.beam((-1.14, 1.14, 2.1), (1.14, 1.14, 2.1), 0.18, 0.1, "wood")
    m.box((-1.2, -1.2, base - 0.1), (1.2, 1.2, base + 0.1), "wood_x", 0.035)
    steps = 5

    for k in range(steps):
        za = base + 0.1 + k * 0.33
        ra = 1.2 + k * 0.09
        rb = ra + 0.075
        zb = za + 0.31
        lo = [(-ra, -ra, za), (ra, -ra, za), (ra, ra, za), (-ra, ra, za)]
        hi = [(-rb, -rb, zb), (rb, -rb, zb), (rb, rb, zb), (-rb, rb, zb)]

        for i in range(4):
            j = (i + 1) % 4
            m.face((lo[i], lo[j], hi[j], hi[i]), pick("wood", k, i))
            nxt = ra + 0.09
            c = [(-nxt, -nxt, za + 0.33), (nxt, -nxt, za + 0.33), (nxt, nxt, za + 0.33), (-nxt, nxt, za + 0.33)]

            if k < steps - 1:
                m.face((hi[i], hi[j], c[j], c[i]), "wood_x")

    zt = base + 0.1 + steps * 0.33 - 0.02
    r = 1.62

    for sx in (-1, 1):
        for sy in (-1, 1):
            m.beam((sx * 1.2, sy * 1.2, base + 0.05), (sx * 1.62, sy * 1.62, zt + 0.05), 0.12, 0.12, "iron")

    for a, b in (((-r, -r), (r, -r)), ((r, -r), (r, r)), ((r, r), (-r, r)), ((-r, r), (-r, -r))):
        m.beam((a[0], a[1], zt + 0.04), (b[0], b[1], zt + 0.04), 0.13, 0.11, "iron_l")

    pts = [(-1.45, -1.45, zt - 0.12), (1.45, -1.45, zt - 0.12), (1.45, 1.45, zt - 0.12), (-1.45, 1.45, zt - 0.12), (0.2, 0.1, zt + 0.42), (-0.7, 0.4, zt + 0.2), (0.7, -0.5, zt + 0.22)]
    m.hull(pts, lambda n, c: pick("ore", c.x, c.y) if pick("ore", c.x, c.y) != "ore_d" else "ore", drop_bottom=zt)

    with m.at(0, -0.95, base - 0.05):
        m.beam((0, 0, 0), (0, -0.68, -0.75), 0.74, 0.07, "wood")

        for s in (-0.4, 0.4):
            m.beam((s, 0.05, 0.12), (s, -0.68, -0.62), 0.08, 0.28, "wood_d", 0.02)

        m.box((-0.42, -0.1, -0.05), (0.42, 0.04, 0.36), "iron", 0.02)

    for i in range(7):
        x = -0.65 + 1.3 * hash01(i, 1)
        y = -1.2 - 0.4 * hash01(i, 2)
        rock(m, x, y, 0.0, 0.2 + 0.14 * hash01(i, 3), 0.22, ("ore", "ore_l"), i)

    return m


def windmill():
    m = Mesh(41)
    top = 6.2

    def leg(sx, sy, z):
        t = z / top
        k = 1.28 - 1.0 * t

        return Vector((sx * k, sy * k * 1.1, z))

    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for sx, sy in corners:
        m.beam(leg(sx, sy, 0.0), leg(sx, sy, top), 0.16, 0.16, "wood_d", 0.03)
        v = leg(sx, sy, 0.0)
        m.box((v.x - 0.14, v.y - 0.14, -0.7), (v.x + 0.14, v.y + 0.14, 0.24), "stone", 0.04, skip="z")

    levels = [0.5, 2.3, 4.0, 5.4]

    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]

        for k in range(1, len(levels)):
            m.beam(leg(a[0], a[1], levels[k]), leg(b[0], b[1], levels[k]), 0.08, 0.12, "wood")
            first, second = (a, b) if (k + i) % 2 == 0 else (b, a)
            m.beam(leg(first[0], first[1], levels[k - 1]), leg(second[0], second[1], levels[k]), 0.06, 0.06, "wood_l", skip="xX")

    m.box((-0.42, -0.45, top - 0.1), (0.42, 0.45, top + 0.06), "wood_x", 0.03)
    hz = 6.78
    m.prism((0, 0), top + 0.04, hz - 0.1, 0.2, 0.17, 8, "iron", top=False)
    m.box((-0.2, -0.55, hz - 0.2), (0.2, 0.42, hz + 0.2), "teal", 0.08)
    m.beam((0, -0.5, hz), (0, -0.82, hz), 0.14, 0.14, "iron_d")
    n = 18

    with m.at(0, -0.84, hz):
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            b0, b1 = a - 0.09, a + 0.09
            c0, c1 = a - 0.13, a + 0.13
            pts = [
                (math.cos(b0) * 0.34, -0.015, math.sin(b0) * 0.34),
                (math.cos(c0) * 1.18, -0.07, math.sin(c0) * 1.18),
                (math.cos(c1) * 1.18, 0.04, math.sin(c1) * 1.18),
                (math.cos(b1) * 0.34, 0.015, math.sin(b1) * 0.34),
            ]
            m.sheet(pts, "cream" if i % 3 else "red")

        for radius in (0.5, 0.98):
            for i in range(n):
                a = 2 * math.pi * i / n
                b = 2 * math.pi * (i + 1) / n
                m.beam((math.cos(a) * radius, 0.04, math.sin(a) * radius), (math.cos(b) * radius, 0.04, math.sin(b) * radius), 0.035, 0.045, "iron_l", skip="xX")

        p.disc(m, 0, 0, 0.22, -0.02, "teal_d", 10, 0.12)

    m.beam((0, 0.4, hz), (0, 0.9, hz), 0.1, 0.14, "iron")
    vane = [(0.78, hz - 0.28), (1.9, hz - 0.78), (1.9, hz + 0.9), (1.42, hz + 1.08), (0.78, hz + 0.34)]

    with m.at(0, 0, 0, yaw=90):
        m.extrude(vane, -0.03, 0.03, "red", "red_d")

        for y in (-0.033, 0.033):
            m.face([(1.55, y, hz - 0.5), (1.72, y, hz - 0.58), (1.72, y, hz + 0.75), (1.55, y, hz + 0.82)][:: 1 if y < 0 else -1], "cream")

    m.beam((0, 0, top), (0, 0, 0.7), 0.05, 0.05, "iron_d", skip="xX")
    m.prism((0, 0), 0.0, 0.75, 0.18, 0.14, 8, "teal_d")
    p.trough(m, 0.0, -1.25, 2.2, 0.75, 0.6)
    m.beam((0, -0.1, 0.7), (0, -1.0, 0.68), 0.1, 0.1, "iron")

    return m


def rock(m, x, y, z, r, h, cols, seed, n=14):
    pts = []

    for i in range(n):
        a = 2 * math.pi * i / n + hash01(i, seed) * 0.7
        level = (0.0, 0.55, 0.92)[i % 3]
        rr = r * (1.0, 0.92, 0.52)[i % 3] * (0.75 + 0.35 * hash01(i, seed, 2))
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z + h * level * (0.8 + 0.3 * hash01(i, seed, 4))))

    pts.append((x, y, z + h))
    m.hull(pts, lambda nr, c: cols[1] if nr.z > 0.65 else cols[0], drop_bottom=z + 0.03)


def slab(m, x, y, z0, z1, rx, ry, col, seed, top=None, n=9, flare=0.08):
    rings = []

    for k, (t, s) in enumerate(((0.0, 1.0 - flare), (0.22, 1.0), (0.78, 0.97), (1.0, 0.84))):
        ring = []

        for i in range(n):
            a = 2 * math.pi * i / n + 0.35 * hash01(i, seed)
            q = s * (0.7 + 0.42 * hash01(i, seed, 3) + 0.08 * hash01(i, k, seed))
            ring.append((x + math.cos(a) * rx * q, y + math.sin(a) * ry * q, z0 + (z1 - z0) * (t + (0.08 * (hash01(i, k, seed, 5) - 0.5) if 0 < t < 1 else 0))))

        rings.append(ring)

    m.loft(rings, lambda i, j: col[0] if j != 2 else col[-1], cap_top=top or col[-1], cap_bottom=col[0] if z0 > 0.05 else None)


def rock_0():
    m = Mesh(50)
    rock(m, -0.08, 0.02, 0.0, 0.76, 1.6, ("rock_b", "rock_d"), 3, 18)
    rock(m, 0.42, -0.4, 0.0, 0.38, 0.62, ("rock_a", "rock_c"), 8, 12)
    rock(m, -0.45, 0.45, 0.0, 0.3, 0.42, ("rock_c", "rock_e"), 12, 10)

    return m


def stacked(seed, layers, rx, ry):
    m = Mesh(seed)
    z = 0.0

    for k, (h, sx, sy, dx, dy, col) in enumerate(layers):
        slab(m, dx, dy, z, z + h, rx * sx, ry * sy, col, seed * 7 + k)
        z += h * 0.985

    rock(m, rx * 0.55, -ry * 0.55, 0.0, rx * 0.42, 0.45, ("rock_a", "rock_c"), seed + 2, 10)
    rock(m, -rx * 0.62, ry * 0.5, 0.0, rx * 0.34, 0.32, ("rock_c", "rock_e"), seed + 5, 10)

    return m


def rock_1():
    return stacked(51, [(0.85, 1.0, 1.0, 0.0, 0.0, ("rock_a", "rock_c")), (0.35, 0.86, 0.84, 0.09, -0.06, ("rock_b", "rock_d")), (1.02, 0.9, 0.86, -0.04, 0.03, ("rock_c", "rock_e"))], 0.88, 0.88)


def rock_2():
    return stacked(52, [(0.8, 1.0, 1.0, 0.0, 0.0, ("rock_a", "rock_b")), (0.75, 0.74, 0.74, 0.08, 0.02, ("rock_b", "rock_c")), (0.28, 0.66, 0.66, 0.02, -0.02, ("rock_a", "rock_c")), (1.0, 0.82, 0.8, -0.06, 0.02, ("rock_c", "rock_e"))], 0.94, 0.96)


def rock_3():
    return stacked(53, [(1.0, 1.0, 1.0, 0.0, 0.0, ("rock_a", "rock_b")), (0.8, 0.72, 0.74, 0.06, 0.0, ("rock_b", "rock_c")), (0.35, 0.66, 0.66, -0.08, 0.05, ("rock_a", "rock_c")), (1.1, 0.68, 0.66, -0.05, -0.02, ("rock_b", "rock_d")), (0.3, 0.56, 0.56, 0.1, 0.0, ("rock_a", "rock_c")), (1.0, 0.72, 0.7, 0.04, 0.03, ("rock_c", "rock_e"))], 0.94, 0.9)


def rock_4():
    m = Mesh(54)
    rock(m, -0.04, 0.06, 0.0, 0.46, 1.3, ("rock_b", "rock_d"), 21, 18)
    rock(m, 0.14, -0.3, 0.0, 0.27, 0.6, ("rock_a", "rock_c"), 25, 12)

    return m


def pillar():
    m = Mesh(55)
    z = 0.0

    for k, (h, r, col) in enumerate(((1.05, 0.86, ("rock_a", "rock_b")), (0.4, 0.64, ("rock_b", "rock_c")), (0.95, 0.72, ("rock_b", "rock_d")), (0.45, 0.54, ("rock_a", "rock_c")), (0.75, 0.58, ("rock_c", "rock_d")), (0.3, 0.46, ("rock_b", "rock_c")), (0.5, 0.64, ("rock_d", "rock_e")))):
        slab(m, 0.12 * math.sin(k * 2.1), 0.1 * math.cos(k * 1.7), z, z + h, r, r * 0.94, col, 550 + k)
        z += h * 0.96

    rock(m, 0.5, -0.5, 0.0, 0.36, 0.5, ("rock_a", "rock_c"), 57, 10)

    return m


def mesa(seed, w, d, h, layers):
    m = Mesh(seed)
    n = 17
    jag = [0.82 + 0.26 * hash01(i, seed) for i in range(n)]

    def ring(radius, z, k, wob=0.09):
        out = []

        for i in range(n):
            a = 2 * math.pi * i / n + 0.14 * hash01(i, seed, 9)
            q = radius * jag[i] * (1 - wob / 2 + wob * hash01(i, k, seed))
            out.append((math.cos(a) * w / 2 * q, math.sin(a) * d / 2 * q, z))

        return out

    strata = ("rock_a", "rock_b", "rock_c", "rock_b", "rock_d", "rock_c", "rock_e")
    rings = [ring(1.08, -5.0, 0), ring(1.0, 0.0, 0), ring(0.86, h * 0.13, 1), ring(0.7, h * 0.19, 2)]
    cols = ["rock_b", "rock_a", "rock_a"]
    prev = 0.19
    k = 3

    for idx, (t, radius) in enumerate(layers):
        col = strata[idx % len(strata)]
        z0, z1 = h * prev, h * t
        rings.append(ring(radius, z0 + h * 0.006, k, 0.05))
        cols.append("rock_e" if idx % 2 else "rock_d")
        mid = z0 + (z1 - z0) * 0.55
        rings.append(ring(radius * 0.985, mid, k + 1))
        cols.append(col)
        rings.append(ring(radius * 0.965, z1, k + 2))
        cols.append(strata[(idx + 1) % len(strata)] if idx % 3 == 0 else col)
        prev = t
        k += 3

    m.loft(rings, lambda i, j: cols[j] if hash01(i, j, seed) > 0.14 else ("rock_a" if cols[j] != "rock_a" else "rock_b"), cap_top="sand")

    for i in range(7):
        a = 2 * math.pi * hash01(i, seed, 20)
        q = 0.72 + 0.12 * hash01(i, seed, 21)
        r = min(w, d) * (0.07 + 0.05 * hash01(i, seed, 22))
        x, y = math.cos(a) * (w / 2 - r) * q * 1.12, math.sin(a) * (d / 2 - r) * q * 1.12
        rock(m, x, y, 0.0, r, r * (1.1 + hash01(i, seed, 23)), ("rock_b", "rock_d"), seed + i, 10)

    return m


def mesa_0():
    return mesa(61, 13.4, 12.8, 34.0, [(0.42, 0.63), (0.47, 0.54), (0.67, 0.52), (0.72, 0.45), (0.92, 0.44), (1.0, 0.35)])


def mesa_1():
    return mesa(62, 21.2, 21.6, 28.0, [(0.38, 0.74), (0.44, 0.66), (0.66, 0.65), (0.72, 0.58), (0.93, 0.57), (1.0, 0.5)])


def mesa_2():
    return mesa(63, 19.2, 20.4, 30.0, [(0.4, 0.69), (0.62, 0.6), (0.67, 0.5), (0.86, 0.48), (0.91, 0.38), (1.0, 0.34)])


def ribbed(m, pts, radii, n=14, cols=("cact", "cact_d")):
    m.tube(pts, radii, n, lambda i, j: cols[0] if i % 2 == 0 else cols[1], cap_top="cact_l", rib=0.8)


def column(m, x, y, h, r, n=14):
    ribbed(m, [(x, y, -0.05), (x, y, h * 0.12), (x, y, h * 0.55), (x, y, h - r * 1.2), (x, y, h - r * 0.45), (x, y, h)], [r * 0.9, r, r * 1.03, r * 0.94, r * 0.66, r * 0.14], n)


def arm(m, az, base, reach, top, r, trunk=0.0):
    c, s = math.cos(az), math.sin(az)

    def at(d, z):
        return (c * d, s * d, z)

    ribbed(m, [at(trunk * 0.5, base), at(reach * 0.75, base + 0.06), at(reach, base + 0.34), at(reach, (base + top) / 2 + 0.2), at(reach, top - r), at(reach, top - r * 0.35), at(reach, top)], [r * 0.85, r * 0.95, r, r, r * 0.88, r * 0.6, r * 0.12], 10)


def flower(m, x, y, z, r):
    m.prism((x, y), z - r * 0.4, z + r * 0.35, r * 0.6, r, 6, "cream", top=False)
    m.prism((x, y), z + r * 0.35, z + r * 0.5, r, r * 0.3, 6, "cream", top="gold")


def palm_2():
    m = Mesh(70)
    column(m, 0, 0, 4.4, 0.26, 16)
    arm(m, math.radians(6), 1.5, 0.52, 3.3, 0.17, 0.26)
    arm(m, math.radians(160), 2.15, 0.5, 3.85, 0.155, 0.26)
    arm(m, math.radians(258), 1.0, 0.44, 2.15, 0.13, 0.26)
    flower(m, 0.03, 0.0, 4.41, 0.09)
    flower(m, 0.5, 0.06, 3.31, 0.07)
    rock(m, 0.32, -0.3, 0.0, 0.24, 0.2, ("rock_c", "rock_e"), 71, 8)

    return m


def cactus_0():
    m = Mesh(72)
    column(m, -0.04, 0, 3.2, 0.2, 14)
    arm(m, math.radians(12), 1.25, 0.38, 2.55, 0.12, 0.18)
    arm(m, math.radians(150), 0.75, 0.33, 1.7, 0.1, 0.18)
    flower(m, -0.05, 0.0, 3.22, 0.09)

    return m


def paddle(m, x, y, z, w, h, yaw, roll, col):
    with m.at(x, y, z, yaw=yaw, roll=roll):
        n = 10
        outline = []

        for i in range(n):
            a = 2 * math.pi * i / n - math.pi / 2
            sq = 0.72 + 0.28 * (math.sin(a) + 1) / 2
            outline.append((math.cos(a) * w / 2 * sq, h / 2 + math.sin(a) * h / 2))

        rim = [(u, 0.0, v) for u, v in outline]

        for s in (-1, 1):
            face = [(u * 0.74, s * 0.075, h / 2 + (v - h / 2) * 0.78) for u, v in outline]

            for i in range(n):
                j = (i + 1) % n
                m.orient([rim[i], rim[j], face[j], face[i]], (math.cos(2 * math.pi * i / n - math.pi / 2 + math.pi / n), s, math.sin(2 * math.pi * i / n - math.pi / 2 + math.pi / n)), col)

            m.orient(face, (0, s, 0), col + "_l" if col == "cact" else "cact")

            for k, (u, v) in enumerate(((-0.18, 0.38), (0.2, 0.55), (-0.05, 0.74), (0.08, 0.28))):
                cx, cz = u * w, v * h
                m.orient([(cx - 0.018, s * 0.081, cz), (cx, s * 0.081, cz - 0.022), (cx + 0.018, s * 0.081, cz), (cx, s * 0.081, cz + 0.022)], (0, s, 0), "straw_l")


def cactus_1():
    m = Mesh(73)
    pads = [
        (-0.05, 0.0, 0.0, 0.62, 0.8, 4, -3, "cact"),
        (-0.22, 0.02, 0.5, 0.46, 0.68, -10, -34, "cact"),
        (0.12, -0.03, 0.54, 0.5, 0.7, 14, 27, "cact_d"),
        (-0.04, 0.03, 0.66, 0.4, 0.58, 24, -4, "cact"),
        (-0.55, -0.01, 0.0, 0.52, 0.55, -24, -22, "cact_d"),
        (0.55, 0.02, 0.0, 0.56, 0.62, 14, 25, "cact"),
        (0.62, 0.03, 0.4, 0.34, 0.46, -6, 38, "cact"),
    ]

    for pad in pads:
        paddle(m, *pad)

    for x, y, z in ((-0.58, 0.02, 1.05), (-0.44, 0.03, 1.1), (0.44, -0.04, 1.18), (0.31, -0.03, 1.22), (-0.07, 0.04, 1.26), (0.86, 0.03, 0.77), (-0.7, -0.01, 0.51)):
        m.prism((x, y), z - 0.05, z + 0.03, 0.04, 0.062, 6, "fruit", top=False)
        m.prism((x, y), z + 0.03, z + 0.08, 0.062, 0.025, 6, "fruit")

    rock(m, 0.25, -0.1, 0.0, 0.16, 0.14, ("rock_c", "rock_e"), 74, 8)

    return m


def limb(m, pts, radii, seed, n=7):
    m.tube(pts, radii, n, lambda i, j: pick("dead", i, j, seed), cap_top="dead_l")


def deadtree():
    m = Mesh(74)
    limb(m, [(0.0, 0.0, -0.1), (0.04, 0.02, 0.5), (-0.1, 0.05, 1.6), (0.08, -0.04, 2.7), (-0.06, 0.0, 3.4)], [0.62, 0.42, 0.33, 0.3, 0.27], 1, 9)
    limb(m, [(-0.08, 0.0, 3.2), (-0.75, 0.15, 4.35), (-1.7, 0.3, 4.9), (-2.35, 0.22, 6.05), (-2.75, 0.35, 6.7)], [0.24, 0.19, 0.14, 0.09, 0.03], 2)
    limb(m, [(0.04, 0.0, 3.2), (0.55, -0.2, 4.6), (0.5, -0.5, 5.8), (1.05, -0.75, 7.0), (0.95, -0.9, 8.35)], [0.22, 0.18, 0.13, 0.08, 0.02], 3)
    limb(m, [(0.0, 0.05, 2.65), (0.9, 0.55, 3.45), (2.0, 0.95, 3.85), (2.75, 1.3, 4.9)], [0.19, 0.14, 0.09, 0.03], 4)
    limb(m, [(-0.04, 0.0, 3.35), (-0.25, -0.45, 4.7), (-0.9, -1.0, 5.5), (-1.0, -1.4, 6.6)], [0.17, 0.12, 0.08, 0.02], 5, 6)
    limb(m, [(-1.65, 0.3, 4.85), (-2.75, 0.5, 5.15), (-3.45, 0.75, 5.95)], [0.1, 0.065, 0.02], 6, 5)
    limb(m, [(0.52, -0.45, 5.5), (1.6, -0.35, 6.1), (2.35, -0.65, 7.15)], [0.1, 0.06, 0.015], 7, 5)
    limb(m, [(2.05, 0.98, 3.9), (3.1, 0.85, 4.15), (3.8, 1.05, 4.75)], [0.07, 0.045, 0.012], 8, 5)
    limb(m, [(0.5, -0.5, 5.8), (0.05, 0.15, 6.9), (0.15, 0.45, 7.7)], [0.08, 0.05, 0.012], 9, 5)
    limb(m, [(-2.3, 0.22, 5.95), (-1.75, 0.05, 6.75), (-1.8, -0.2, 7.35)], [0.065, 0.04, 0.012], 10, 5)

    for i in range(5):
        a = i * 1.26 + 0.3
        limb(m, [(math.cos(a) * 0.2, math.sin(a) * 0.2, 0.55), (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.12), (math.cos(a) * 1.05, math.sin(a) * 1.05, -0.06)], [0.2, 0.13, 0.04], 20 + i, 5)

    rock(m, 0.8, -0.5, 0.0, 0.28, 0.24, ("rock_c", "rock_e"), 79, 8)

    return m


def blob(m, x, y, z, rx, ry, rz, fam, seed, n=11):
    pts = []

    for i in range(n):
        t = 1 - 2 * (i + 0.5) / n
        a = i * 2.399963 + seed
        q = math.sqrt(1 - t * t)
        k = 0.78 + 0.34 * hash01(i, seed)
        pts.append((x + math.cos(a) * q * rx * k, y + math.sin(a) * q * ry * k, max(z + t * rz * k, 0.0)))

    m.hull(pts, lambda nr, c: fam + "_l" if nr.z > 0.55 else fam + "_d" if nr.z < -0.05 else fam, drop_bottom=0.02)


def scrub():
    m = Mesh(75)
    blob(m, 0.0, 0.0, 0.27, 0.34, 0.26, 0.27, "scrub", 2, 16)

    for i in range(13):
        a = i * 2.399963
        d = 0.38 * math.sqrt((i + 0.5) / 13)
        z = 0.54 - d * 0.78
        r = 0.15 + 0.04 * hash01(i, 75)
        blob(m, math.cos(a) * d, math.sin(a) * d * 0.72, z, r, r * 0.9, r * 0.82, "scrub", i * 5 + 3, 9)

    for i in range(5):
        a = i * 1.27 + 0.4
        m.tube([(math.cos(a) * 0.06, math.sin(a) * 0.05, 0.0), (math.cos(a) * 0.36, math.sin(a) * 0.27, 0.14)], [0.025, 0.008], 3, "dead_d", cap_top=False)

    return m


def tumbleweed():
    m = Mesh(76)
    c = Vector((0, 0, 0.38))

    for i in range(20):
        t = 1 - 2 * (i + 0.5) / 20
        a = i * 2.399963
        axis = Vector((math.cos(a) * math.sqrt(1 - t * t), math.sin(a) * math.sqrt(1 - t * t), t))
        u = axis.orthogonal().normalized()
        v = axis.cross(u).normalized()
        span = 2.2 + 2.0 * hash01(i, 4)
        start = 6.28 * hash01(i, 7)
        r = 0.3 + 0.08 * hash01(i, 9)
        pts = []

        for k in range(6):
            q = start + span * k / 5
            rr = r * (0.86 + 0.28 * hash01(i, k, 11))
            w = c + (u * math.cos(q) + v * math.sin(q)) * rr + axis * (0.09 * (hash01(i, k, 13) - 0.5))
            pts.append((w.x, w.y, max(w.z, 0.015)))

        m.tube(pts, [0.006, 0.016, 0.017, 0.016, 0.012, 0.004], 3, ("straw", "straw_d", "dead_l")[i % 3], cap_top=False)

    return m


def gravel():
    m = Mesh(77)

    for i in range(17):
        a = i * 2.399963
        d = 1.15 * math.sqrt((i + 0.5) / 17)
        r = 0.1 + 0.16 * hash01(i, 77) * (1.1 - d / 1.4)
        cols = (("ore", "ore_l"), ("rock_b", "rock_d"), ("stone_d", "stone"))[i % 3]
        pts = []

        for k in range(6):
            q = 6.28 * k / 6 + hash01(i, k)
            rr = r * (0.7 + 0.5 * hash01(i, k, 2))
            pts.append((math.cos(a) * d + math.cos(q) * rr, math.sin(a) * d + math.sin(q) * rr, 0.0))

        pts.append((math.cos(a) * d + r * 0.2, math.sin(a) * d, 0.04 + r * 0.24))
        m.hull(pts, lambda nr, c, cols=cols: cols[1] if nr.x + nr.y < 0 else cols[0], drop_bottom=0.02)

    return m


def walk():
    m = Mesh(78)
    n = 5
    w = 2.0 / n

    for i in range(n):
        a = -1.0 + i * w
        z = 0.3 - 0.012 * (i % 3)
        col = ("wood", "wood_d", "wood", "gray_d", "wood")[i]
        m.box((a + 0.012, -0.5, 0.2), (a + w - 0.012, 0.5, z), col, skip="z")

    for y in (-0.43, 0.43):
        m.box((-1.0, y - 0.065, -0.2), (1.0, y + 0.065, 0.2), "wood_x", skip="zZ")

    return m


def drift():
    m = Mesh(79)
    n = 22
    rings = []

    for k, (s, z) in enumerate(((1.0, -0.04), (0.82, 0.14), (0.56, 0.36), (0.28, 0.52))):
        ring = []

        for i in range(n):
            a = 2 * math.pi * i / n
            q = s * (0.9 + 0.14 * math.sin(a * 3 + 1) + 0.05 * hash01(i, k))
            ring.append((0.2 + math.cos(a) * 3.9 * q + 0.35 * k, math.sin(a) * 1.85 * q + 0.12 * k, z + 0.04 * math.sin(a * 2 + k)))

        rings.append(ring)

    m.loft(rings, lambda i, j: "sand_l" if j == 2 and i % 5 < 3 else "sand", cap_top="sand_l")

    for i in range(6):
        x = -2.6 + i * 1.05
        y = -1.45 if i % 2 else 1.4
        rock(m, x, y * (1 - 0.1 * abs(x) / 3), 0.0, 0.14 + 0.1 * hash01(i, 5), 0.2, ("rock_b", "rock_d"), 80 + i, 8)

    return m


def spoil():
    m = Mesh(81)
    m.push(Matrix.Diagonal((0.83, 0.75, 1.0, 1.0)))

    def mound(x, y, rx, ry, h, seed):
        pts = []

        for i in range(15):
            a = 2 * math.pi * i / 15
            q = 0.88 + 0.16 * hash01(i, seed)
            pts.append((x + math.cos(a) * rx * q, y + math.sin(a) * ry * q, 0.0))

        for i in range(8):
            a = 2 * math.pi * i / 8 + 0.3
            q = 0.5 + 0.18 * hash01(i, seed, 2)
            pts.append((x + math.cos(a) * rx * q, y + math.sin(a) * ry * q, h * (0.55 + 0.2 * hash01(i, seed, 3))))

        pts.append((x + 0.15, y - 0.1, h))
        m.hull(pts, lambda nr, c: ("ore_l" if hash01(c.x, c.y, seed) > 0.72 else "rock_a" if hash01(c.x, c.z, seed) > 0.6 else "ore"), drop_bottom=0.03)

    mound(-1.45, 0.1, 1.7, 1.55, 1.9, 3)
    mound(0.25, -0.35, 1.25, 1.2, 1.2, 9)

    for i in range(12):
        x = -2.7 + 3.9 * hash01(i, 31)
        y = -1.45 + 0.5 * hash01(i, 32) if i % 2 else 1.1 + 0.4 * hash01(i, 32)
        rock(m, x, y, 0.0, 0.16 + 0.16 * hash01(i, 33), 0.28, ("ore", "ore_l") if i % 3 else ("rock_b", "rock_d"), 90 + i, 8)

    for row, count in enumerate((4, 3, 2)):
        for i in range(count):
            y = -0.7 + i * 0.36 + row * 0.18
            z = 0.2 + row * 0.27
            m.box((1.45, y - 0.16, z - 0.14), (3.15 - 0.08 * ((i + row) % 3), y + 0.16, z + 0.14), pick("wood", i, row), 0.045)

    for x in (1.75, 2.75):
        m.box((x - 0.06, -0.92, 0.0), (x + 0.06, 0.55, 0.07), "wood_x", skip="z")

        for y in (-0.93, 0.56):
            m.box((x - 0.065, y - 0.05, 0.0), (x + 0.065, y + 0.05, 0.62), "wood_d", 0.02, skip="z")

    p.barrel(m, 2.45, 1.12, 0.0, 0.36, 0.95, 10, "gray")
    p.crate(m, 1.45, 1.1, 0.0, 0.75, 0.7, 0.6, 12)
    m.beam((-0.1, -1.6, 0.05), (-0.75, -0.95, 1.2), 0.07, 0.07, "wood_l")
    m.box((-0.2, -1.74, 0.0), (0.06, -1.5, 0.07), "iron", 0.02)

    return m


ALL = {
    "barrel": barrel,
    "crate": crate,
    "box": box,
    "chest": chest,
    "bench": bench,
    "fence": fence,
    "lantern": lantern,
    "pole": pole,
    "watertower": watertower,
    "headframe": headframe,
    "orebin": orebin,
    "windmill": windmill,
    "rock_0": rock_0,
    "rock_1": rock_1,
    "rock_2": rock_2,
    "rock_3": rock_3,
    "rock_4": rock_4,
    "pillar": pillar,
    "mesa_0": mesa_0,
    "mesa_1": mesa_1,
    "mesa_2": mesa_2,
    "saguaro": palm_2,
    "deadtree": deadtree,
    "cactus": cactus_0,
    "pear": cactus_1,
    "sage": scrub,
    "tumbleweed": tumbleweed,
    "gravel": gravel,
    "walk": walk,
    "drift": drift,
    "spoil": spoil,
}
