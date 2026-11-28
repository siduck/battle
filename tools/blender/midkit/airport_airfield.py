import math

import midkit_core as m
import midkit_structures as st
import midkit_walls as wl


def tank():
    m.setup()
    P = [m.bx((15.8, 15.8, 0.2), (0, 0, 0), "ap_sand_d", 0.02)]

    for s in (-1, 1):
        P.append(m.bx((16.0, 0.5, 1.3), (0, s * 7.75, 0.0), "ap_sand", 0.05))
        P.append(m.bx((0.5, 15.0, 1.3), (s * 7.75, 0, 0.0), "ap_sand", 0.05))
        P.append(m.bx((16.2, 0.7, 0.15), (0, s * 7.75, 1.3), "ap_sand_l", 0.02))
        P.append(m.bx((0.7, 15.0, 0.15), (s * 7.75, 0, 1.3), "ap_sand_l", 0.02))

    r, h = 6.1, 10.6
    z0 = 0.5
    P.append(m.cyl(r + 0.25, 0.5, (0, 0, 0.2), "ap_sand_d", 24))
    P.append(m.cyl(r, h, (0, 0, z0), "ap_sand_l", 24))

    for i in range(5):
        P.append(m.cyl(r + 0.07, 0.16, (0, 0, z0 + 0.5 + i * 2.1), "ap_sand", 24))

    P.append(m.cyl(r + 0.1, 0.9, (0, 0, z0 + 7.4), "ap_orange", 24))
    P.append(m.cyl(r + 0.2, 0.3, (0, 0, z0 + h), "ap_steel_d", 24))
    P.append(m.lathe([(0, z0 + h + 0.3), (r + 0.05, z0 + h + 0.3), (r - 0.4, z0 + h + 0.8), (2.0, z0 + h + 1.9), (1.2, z0 + h + 2.2), (0, z0 + h + 2.3)], (0, 0, 0), "ap_steel_l", 24))
    P.append(m.cyl(0.9, 0.35, (0, 0, z0 + h + 2.2), "ap_steel_d", 12))
    P.append(m.cyl(0.35, 0.6, (0, 0, z0 + h + 2.5), "ap_steel", 12))
    sr = r + 0.65
    turns = 1.0
    steps = 34
    zt = z0 + h + 0.3
    a0 = math.radians(-35)

    for i in range(steps):
        t = i / (steps - 1)
        a = a0 + turns * 2 * math.pi * t
        px, py = math.cos(a) * sr, math.sin(a) * sr
        z = 0.35 + t * (zt - 0.35 - 0.1)
        tread = m.bx((0.85, 0.48, 0.07), (px, py, z), "ap_steel", 0.0)
        m.k.rotate(tread, math.degrees(a) + 90, "Z", (px, py, z))
        P.append(tread)

        if i % 2 == 0:
            P.append(m.bar((px + math.cos(a) * 0.4, py + math.sin(a) * 0.4, z), (px + math.cos(a) * 0.4, py + math.sin(a) * 0.4, z + 0.95), 0.018, "ap_steel_d", 4))

    for i in range(steps - 1):
        t0, t1 = i / (steps - 1), (i + 1) / (steps - 1)
        pts = []

        for t in (t0, t1):
            a = a0 + turns * 2 * math.pi * t
            pts.append((math.cos(a) * (sr + 0.4), math.sin(a) * (sr + 0.4), 0.35 + t * (zt - 0.45) + 0.95))

        P.append(m.bar(pts[0], pts[1], 0.03, "ap_steel_d", 4))

    ap = a0 + turns * 2 * math.pi
    px, py = math.cos(ap) * sr, math.sin(ap) * sr
    P.append(m.bx((1.6, 1.6, 0.1), (px * 0.93, py * 0.93, zt - 0.05), "ap_steel", 0.01))
    seg = 20

    for i in range(seg):
        a, b = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        pa = (math.cos(a) * (r + 0.05), math.sin(a) * (r + 0.05), zt)
        pb = (math.cos(b) * (r + 0.05), math.sin(b) * (r + 0.05), zt)
        P.append(m.bar((pa[0], pa[1], zt + 1.0), (pb[0], pb[1], zt + 1.0), 0.03, "ap_steel_d", 4))
        P.append(m.bar((pa[0], pa[1], zt + 0.5), (pb[0], pb[1], zt + 0.5), 0.02, "ap_steel_d", 4))
        P.append(m.bar(pa, (pa[0], pa[1], zt + 1.0), 0.025, "ap_steel_d", 4))

    P.append(m.bar((r - 0.1, 3.0, 1.0), (r + 1.8, 3.0, 1.0), 0.17, "ap_steel_d", 10))
    P.append(m.bar((r + 1.8, 3.0, 1.0), (r + 1.8, 3.0, 0.45), 0.17, "ap_steel_d", 10))
    P.append(m.cyl(0.3, 0.12, (r + 1.8, 3.0, 1.0), "ap_orange", 10))
    P.append(m.bar((r + 1.8, 3.0, 0.45), (7.2, 3.0, 0.45), 0.2, "ap_steel_d", 10))
    P.append(m.bar((7.2, 3.0, 0.45), (7.2, 4.8, 0.45), 0.17, "ap_steel_d", 10))
    P.append(m.cyl(0.4, 0.2, (r + 0.6, 3.0, 1.0), "ap_orange_d", 10))

    for i in range(3):
        a = math.radians(160 + i * 18)
        P.append(m.bx((0.5, 0.5, 0.2), (math.cos(a) * (r - 0.3), math.sin(a) * (r - 0.3), z0 + h + 0.7), "ap_steel_d", 0.02))

    ob = m.finish("tank", P, budget=7000)

    return ob


def radar():
    m.setup()
    P = [m.bx((6.0, 6.0, 0.25), (0, 0, 0), "ap_sand_d", 0.02)]
    zt = 13.0
    base, top = 2.25, 0.95

    def corner(sx, sy, z):
        t = z / zt
        w = base + (top - base) * t

        return (sx * w, sy * w, z)

    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(m.bar(corner(sx, sy, 0.1), corner(sx, sy, zt), 0.14, "ap_steel_d", 6))
            P.append(m.bx((0.7, 0.7, 0.3), (sx * base, sy * base, 0.0), "ap_sand", 0.03))

    levels = [0.2, 3.5, 6.8, 10.0, zt]

    for i in range(len(levels) - 1):
        za, zb = levels[i], levels[i + 1]
        corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]

        for j in range(4):
            a, b = corners[j], corners[(j + 1) % 4]
            pa, pb = corner(a[0], a[1], za), corner(b[0], b[1], zb) if (i + j) % 2 == 0 else corner(b[0], b[1], za)
            qa, qb = (corner(a[0], a[1], zb), corner(b[0], b[1], za)) if (i + j) % 2 == 0 else (corner(a[0], a[1], za), corner(b[0], b[1], zb))
            P.append(m.bar(qa, qb, 0.05, "ap_steel", 4))

        for j in range(4):
            a, b = corners[j], corners[(j + 1) % 4]
            P.append(m.bar(corner(a[0], a[1], zb), corner(b[0], b[1], zb), 0.07, "ap_steel_d", 4))

    P.append(m.bx((3.2, 3.2, 0.3), (0, 0, zt), "ap_steel_d", 0.03))
    P += m.railing(3.2, 1.0, (0, -1.6, zt + 0.3), "ap_steel_d", axis="x")
    P += m.railing(3.2, 1.0, (0, 1.6, zt + 0.3), "ap_steel_d", axis="x")
    P += m.railing(3.2, 1.0, (-1.6, 0, zt + 0.3), "ap_steel_d", axis="y")
    P += m.railing(3.2, 1.0, (1.6, 0, zt + 0.3), "ap_steel_d", axis="y")
    P.append(m.cyl(0.55, 1.6, (0, 0, zt + 0.3), "ap_sand_l", 12))
    P.append(m.cyl(0.8, 0.5, (0, 0, zt + 1.9), "ap_steel_d", 12))
    P.append(m.cyl(0.3, 1.6, (0, 0, zt + 2.2), "ap_steel", 12))
    cw, rh, rz = 7.4, 4.0, 15.6
    arc = []
    n = 8

    for i in range(n + 1):
        x = -cw / 2 + cw * i / n
        arc.append((x, -0.6 + (x / (cw / 2)) ** 2 * 0.7))

    out = arc + [(x, y + 0.22) for x, y in reversed(arc)]
    P.append(m.sweep_xy(out, rh, (0, 0.0, rz), "ap_sand_l"))

    for i in range(6):
        x = -cw / 2 + 0.3 + i * (cw - 0.6) / 5
        P.append(m.bx((0.18, 0.5, rh), (x, 0.38, rz), "ap_steel_d", 0.02))

    for z in (rz + 0.2, rz + rh * 0.5 - 0.1, rz + rh - 0.3):
        P.append(m.bx((cw - 0.2, 0.3, 0.2), (0, 0.45, z), "ap_steel_d", 0.02))

    P.append(m.bx((0.9, 0.7, rh * 0.7), (0, 0.6, rz + rh * 0.15), "ap_steel", 0.03))
    P.append(m.bx((3.0, 2.4, 2.6), (2.8, 2.9, 0.0), "ap_sand_l", 0.05))
    P.append(m.bx((3.3, 2.7, 0.25), (2.8, 2.9, 2.6), "ap_steel_d", 0.03))
    P += m.window_on(0.9, 0.9, (2.2, 1.7, 1.2), panes=1)
    P.append(m.bx((0.9, 0.1, 2.0), (3.6, 1.7, 0.0), "ap_steel_d", 0.01))
    P.append(m.cyl(0.05, 2.0, (-0.3, 1.0, zt + 0.3), "ap_steel_d", 6))
    ob = m.finish("radar", P, budget=6000)

    return ob


def vor():
    m.setup()
    P = []
    r = 4.4
    P.append(m.lathe([(0, 0.7), (r, 0.9), (r + 0.1, 1.05), (r, 1.2), (1.2, 1.3), (0, 1.3)], (0, 0, 0), "ap_steel", 16))
    P.append(m.cyl(r * 0.2, 0.7, (0, 0, 0.0), "ap_steel_d", 10))

    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        px, py = math.cos(a) * r * 0.82, math.sin(a) * r * 0.82
        P.append(m.cyl(0.18, 0.75, (px, py, 0.0), "ap_steel_d", 6))

    prof = [(0, 1.3), (1.55, 1.3), (1.6, 1.5), (1.45, 1.7), (1.35, 5.8), (1.5, 6.0), (1.6, 6.4), (1.2, 7.3), (0.6, 8.0), (0, 8.4)]
    P.append(m.lathe(prof, (0, 0, 0), "ap_white", 14))
    P.append(m.cyl(1.65, 0.25, (0, 0, 6.0), "ap_orange", 14))
    P.append(m.cyl(0.14, 0.4, (0, 0, 8.35), "ap_steel_d", 8))
    P.append(m.cyl(0.18, 0.35, (0, 0, 8.4), "ap_orange", 8))

    for i in range(8):
        a = math.radians(i * 45)
        px, py = math.cos(a) * 3.2, math.sin(a) * 3.2
        P.append(m.cyl(0.3, 0.3, (px, py, 1.25), "ap_sand_l", 8))
        P.append(m.cyl(0.14, 1.0, (px, py, 1.55), "ap_white", 8))
        P.append(m.cyl(0.2, 0.12, (px, py, 2.45), "ap_steel_d", 8))

    P.append(m.cyl(r + 0.2, 0.12, (0, 0, 0.7), "ap_steel_d", 16))
    ob = m.finish("vor", P, budget=4000)

    return ob


def flood():
    m.setup()
    P = [m.cyl(0.55, 0.3, (0, 0, 0.0), "ap_steel_d", 8)]
    P.append(m.lathe([(0, 0.3), (0.5, 0.3), (0.4, 0.9), (0.3, 1.2), (0.2, 14.2), (0, 14.2)], (0, 0, 0), "ap_steel", 8))
    P.append(m.cyl(0.38, 0.55, (0, 0, 1.2), "ap_steel_d", 8))
    P += m.bolts([(math.cos(a * math.pi / 2) * 0.43, math.sin(a * math.pi / 2) * 0.43, 0.3) for a in range(4)], r=0.05, h=0.07)
    P.append(m.cyl(0.95, 0.12, (0, 0, 13.7), "ap_steel", 8))
    P += [m.bar((math.cos(a * math.pi / 4) * 0.95, math.sin(a * math.pi / 4) * 0.95, 13.8), (math.cos(a * math.pi / 4) * 0.95, math.sin(a * math.pi / 4) * 0.95, 14.7), 0.025, "ap_steel_d", 4) for a in range(8)]
    P.append(m.cyl(0.95, 0.07, (0, 0, 14.6), "ap_steel_d", 8))
    P.append(m.cyl(0.38, 0.55, (0, 0, 14.2), "ap_steel_d", 8))
    P.append(m.bx((2.5, 0.5, 1.5), (0, 0, 14.9), "ap_steel_d", 0.05))
    P.append(m.bx((2.62, 0.62, 0.12), (0, 0, 16.3), "ap_steel", 0.02))

    for row in range(2):
        for i in range(4):
            x = -0.95 + i * 0.633
            lens = m.cyl(0.24, 0.06, (0, 0, 0), "ap_white", 10)
            m.k.rotate(lens, 90, "X")
            m.k.move(lens, x, -0.28, 15.25 + row * 0.62)
            P.append(lens)
            ring = m.cyl(0.28, 0.05, (0, 0, 0), "ap_steel", 10)
            m.k.rotate(ring, 90, "X")
            m.k.move(ring, x, -0.26, 15.25 + row * 0.62)
            P.append(ring)

    P.append(m.bx((2.5, 0.12, 0.15), (0, 0.3, 15.6), "ap_steel", 0.01))
    P.append(m.cyl(0.07, 0.4, (0.9, 0, 16.4), "ap_orange", 8))
    ob = m.finish("flood", P, budget=3500)

    return ob


def localizer():
    m.setup()
    L = 24.4
    P = [m.bx((L, 0.5, 0.35), (0, 0.0, 0.0), "ap_sand_d", 0.03)]
    P.append(m.bx((L, 0.12, 0.16), (0, 0.55, 0.45), "ap_steel_d", 0.01))
    n = 14

    for i in range(n):
        x = -L / 2 + 1.0 + i * (L - 2.0) / (n - 1)
        P.append(m.bx((0.34, 0.34, 0.45), (x, 0.0, 0.35), "ap_sand", 0.03))
        P.append(m.bx((0.9, 0.12, 2.5), (x, 0.0, 0.7), "ap_white", 0.03))
        P.append(m.bx((0.6, 0.14, 0.12), (x, -0.07, 1.5), "ap_steel_d", 0.01))
        P.append(m.bx((0.5, 0.14, 0.12), (x, -0.07, 2.25), "ap_steel_d", 0.01))
        P.append(m.bx((0.1, 0.5, 0.2), (x, 0.3, 1.2), "ap_steel_d", 0.01))

    P.append(m.bx((1.3, 1.1, 1.2), (L / 2 - 0.65, 1.2, 0.0), "ap_sand_l", 0.04))
    P.append(m.bx((1.45, 1.25, 0.15), (L / 2 - 0.65, 1.2, 1.2), "ap_steel_d", 0.02))
    ob = m.finish("localizer", P, budget=3500)

    return ob


def deflector():
    m.setup()
    P = [m.bx((4.0, 2.7, 0.2), (0, 0, 0), "ap_sand_d", 0.02)]
    ang = 52.0
    L = 3.6
    sheet = m.corrugated(3.8, L, (0, 0, 0), "ap_steel_l", pitch=0.5, depth=0.1, axis="x")

    for it in sheet:
        m.k.rotate(it, 180)
        m.k.rotate(it, 90 - ang, "X")
        m.k.move(it, 0, 1.05, 0.2)

    P += sheet

    for s in (-1, 1):
        tri = m.sweep_xz([(0, 0), (2.4, 0), (0.3, 3.1)], 0.16, (0, 0, 0), "ap_steel_d")
        m.k.rotate(tri, 90)
        m.k.move(tri, s * 1.92, -1.2, 0.2)
        P.append(tri)

    P.append(m.bx((4.0, 0.3, 0.3), (0, 1.2, 0.2), "ap_steel_d", 0.03))
    P.append(m.bx((3.9, 0.22, 0.28), (0, -0.25, 3.2), "ap_orange", 0.03))
    P += m.hazard(3.8, 0.28, (0, -1.28, 0.22), axis_x=True)
    ob = m.finish("deflector", P, budget=3000)

    return ob


def edge():
    m.setup()
    P = [m.cyl(0.18, 0.05, (0, 0, 0), "ap_steel_d", 10)]
    P.append(m.cyl(0.08, 0.28, (0, 0, 0.05), "ap_orange", 8))
    P.append(m.cyl(0.14, 0.05, (0, 0, 0.28), "ap_steel_d", 10))
    P.append(m.lathe([(0, 0.33), (0.12, 0.33), (0.13, 0.4), (0.09, 0.47), (0, 0.49)], (0, 0, 0), "ap_white", 10))
    P += m.bolts([(0.14, 0, 0.05), (-0.14, 0, 0.05)], r=0.02, h=0.03)
    ob = m.finish("edge", P, budget=500, grime=None)

    return ob


def twysign():
    m.setup()
    P = [m.bx((1.9, 0.3, 0.06), (0, 0, 0), "ap_steel_d", 0.01)]

    for sx in (-1, 1):
        P.append(m.bx((0.1, 0.1, 0.8), (sx * 0.85, 0, 0.06), "ap_steel", 0.02))

    P.append(m.bx((2.12, 0.14, 0.78), (0, 0, 0.78), "ap_yellow", 0.04))
    P.append(m.bx((1.95, 0.05, 0.62), (0, -0.075, 0.86), "ap_dark", 0.01))
    P.append(m.bx((0.6, 0.05, 0.6), (-0.6, -0.1, 0.87), "ap_yellow", 0.01))
    P.append(m.bx((0.14, 0.05, 0.4), (-0.6, -0.12, 0.97), "ap_dark", 0.0))
    P.append(m.bx((0.5, 0.05, 0.14), (0.15, -0.1, 1.1), "ap_yellow", 0.0))
    P.append(m.sweep_xz([(0.0, 0.0), (0.0, 0.46), (0.36, 0.23)], 0.05, (0.45, -0.1, 0.94), "ap_yellow"))
    ob = m.finish("twysign", P, budget=1200)

    return ob


def windsock():
    m.setup()
    P = [m.cyl(0.45, 0.2, (0, 0, 0), "ap_sand_d", 8)]
    P.append(m.lathe([(0, 0.2), (0.3, 0.2), (0.22, 0.6), (0.14, 6.0), (0, 6.0)], (0, 0, 0), "ap_steel_l", 8))
    P.append(m.cyl(0.14, 0.4, (0, 0, 5.9), "ap_steel_d", 8))
    P.append(m.cyl(0.55, 0.06, (0, 0, 6.2), "ap_steel_d", 12))
    P.append(m.bar((0, 0, 6.2), (0, -2.2, 6.2), 0.04, "ap_steel_d", 4))
    P.append(m.bx((0.18, 0.18, 0.18), (0, -2.15, 6.1), "ap_orange_d", 0.02))
    segs = 5
    L = 2.2

    for i in range(segs):
        r0 = 0.5 - 0.05 * i
        r1 = 0.5 - 0.05 * (i + 1)
        y0 = 0.2 + i * (L - 0.2) / segs
        y1 = 0.2 + (i + 1) * (L - 0.2) / segs
        col = "ap_orange" if i % 2 == 0 else "ap_white"
        cone = m.k.prism("s", 12, r0, y1 - y0, (0, 0, 0), m.c(col), radius_top=r1)
        m.k.rotate(cone, -90, "X")
        m.k.move(cone, 0, y0, 6.2)
        P.append(cone)

    ob = m.finish("windsock", P, budget=1500)

    return ob


def vdgs():
    m.setup()
    P = [m.bx((1.5, 0.9, 0.12), (0, 0, 0), "ap_steel_d", 0.02)]
    P.append(m.bx((0.5, 0.5, 1.6), (0, 0, 0.12), "ap_steel", 0.05))
    P.append(m.bx((0.62, 0.62, 0.12), (0, 0, 1.0), "ap_orange", 0.02))
    P.append(m.bx((1.5, 0.6, 0.78), (0, 0, 1.62), "ap_steel_d", 0.06))
    P.append(m.bx((1.34, 0.05, 0.54), (0, -0.31, 1.74), "ap_void", 0.01))

    for i in range(5):
        P.append(m.flat((0.2, 0.02, 0.38), (-0.52 + i * 0.26, -0.335, 1.82), "ap_yellow" if i % 2 else "ap_red"))

    P.append(m.bx((1.6, 0.66, 0.08), (0, 0, 2.4 - 0.08), "ap_steel", 0.02))
    ob = m.finish("vdgs", P, budget=1500)

    return ob


def lamp():
    m.setup()
    P = [m.cyl(0.42, 0.25, (0, 0, 0), "ap_sand_d", 8)]
    P.append(m.lathe([(0, 0.25), (0.3, 0.25), (0.2, 0.8), (0.11, 1.4), (0.08, 7.5), (0, 7.5)], (0, 0, 0), "ap_steel", 8))
    P += m.bolts([(0.33, 0, 0.25), (-0.33, 0, 0.25), (0, 0.33, 0.25), (0, -0.33, 0.25)], r=0.04, h=0.05)
    P.append(m.cyl(0.14, 0.4, (0, 0, 7.4), "ap_steel_d", 8))

    for s in (-1, 1):
        P.append(m.bar((0, s * 0.06, 7.6), (0, s * 1.3, 8.0), 0.05, "ap_steel_d", 6))
        head = m.bx((0.5, 0.95, 0.2), (0, s * 1.55, 7.8), "ap_steel_l", 0.06)
        P.append(head)
        P.append(m.bx((0.4, 0.8, 0.04), (0, s * 1.55, 7.77), "ap_glass_l", 0.0))
        P.append(m.bx((0.3, 0.45, 0.1), (0, s * 1.5, 7.98), "ap_steel_d", 0.03))

    ob = m.finish("lamp", P, budget=1500)

    return ob


def lighttower():
    m.setup()
    P = [m.bx((1.6, 3.2, 0.3), (0, 0.1, 0.55), "ap_orange", 0.05)]
    P.append(m.bx((1.5, 2.2, 0.55), (0, 0.4, 0.85), "ap_orange_d", 0.05))
    P.append(m.bx((0.9, 1.2, 0.5), (0, 0.4, 1.4), "ap_steel_d", 0.04))
    P.append(m.bar((0, -1.5, 0.7), (0, -2.4, 0.75), 0.05, "ap_steel_d", 6))
    P.append(m.cyl(0.1, 0.12, (0, -2.4, 0.7), "ap_steel", 8))

    for sx in (-1, 1):
        P += m.tire(0.35, 0.22, (sx * 0.95, 0.5, 0.35), axis="x")

    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(m.bar((sx * 0.7, sy * 1.3 + 0.1, 0.65), (sx * 1.0, sy * 1.65 + 0.1, 0.1), 0.045, "ap_steel_d", 4))
            P.append(m.bx((0.25, 0.25, 0.06), (sx * 1.0, sy * 1.65 + 0.1, 0.0), "ap_steel", 0.01))

    zs = [(1.9, 0.14), (4.4, 0.115), (6.9, 0.09)]

    for z, r in zs:
        P.append(m.cyl(r, 2.6, (0, 0.4, z - 0.0), "ap_steel_l", 8))
        P.append(m.cyl(r * 1.3, 0.2, (0, 0.4, z + 2.4 - 0.0), "ap_steel_d", 8))

    P.append(m.bx((1.2, 0.3, 0.1), (0, 0.4, 8.8), "ap_steel_d", 0.02))

    for row in range(2):
        for sx in (-1, 1):
            P.append(m.bx((0.8, 0.3, 0.38), (sx * 0.48, 0.4, 8.85 + row * 0.42), "ap_steel_d", 0.03))
            P.append(m.bx((0.62, 0.04, 0.26), (sx * 0.48, 0.23, 8.91 + row * 0.42), "ap_white", 0.0))
    ob = m.finish("lighttower", P, budget=3000)

    return ob


def bollards():
    m.setup()
    P = [m.bx((4.0, 0.5, 0.1), (0, 0, 0), "ap_sand_d", 0.02)]

    for i in range(5):
        x = -1.8 + i * 0.9
        P.append(m.bx((0.4, 0.4, 0.08), (x, 0, 0.1), "ap_steel_d", 0.02))
        P.append(m.lathe([(0, 0.18), (0.13, 0.18), (0.13, 0.9), (0.09, 1.1), (0.0, 1.15)], (x, 0, 0), "ap_steel", 10))
        P.append(m.cyl(0.14, 0.14, (x, 0, 0.62), "ap_yellow", 10))
        P.append(m.cyl(0.14, 0.04, (x, 0, 0.9), "ap_orange", 10))

    ob = m.finish("bollards", P, budget=1500)

    return ob


def barrier():
    m.setup()
    P = [m.bx((0.6, 0.6, 0.1), (-1.8, 0, 0), "ap_sand_d", 0.02)]
    P.append(m.bx((0.46, 0.46, 1.0), (-1.8, 0, 0.1), "ap_steel_l", 0.05))
    P.append(m.bx((0.5, 0.5, 0.08), (-1.8, 0, 1.1), "ap_steel_d", 0.02))
    P.append(m.bx((0.1, 0.34, 0.3), (-1.8, -0.24, 0.55), "ap_dark", 0.01))
    P.append(m.cyl(0.05, 0.04, (-1.8, -0.24, 0.9), "ap_green", 8))
    P.append(m.cyl(0.1, 0.18, (-1.55, 0, 0.9), "ap_steel_d", 10))
    n = 8

    for i in range(n):
        x = -1.55 + 0.05 + i * (3.6 / n)
        P.append(m.bx((3.6 / n - 0.01, 0.1, 0.13), (x + 3.6 / n / 2, 0, 0.98), "ap_orange" if i % 2 else "ap_white", 0.01))

    P.append(m.bx((0.3, 0.12, 0.16), (-1.7, 0, 0.98), "ap_steel_d", 0.01))
    P.append(m.bx((0.3, 0.14, 0.2), (-1.55 - 0.25, 0, 0.95), "ap_steel_d", 0.02))
    P.append(m.bx((0.14, 0.3, 0.62), (2.0, 0, 0.0), "ap_steel_d", 0.02))
    P.append(m.bx((0.3, 0.3, 0.06), (2.0, 0, 0.62), "ap_orange", 0.01))
    ob = m.finish("barrier", P, budget=1500)

    return ob


def crashbar():
    m.setup()
    P = []
    P.append(m.bx((4.0, 0.06, 0.44), (0, -0.02, 0.5), "ap_steel_l", 0.01))
    P.append(m.bx((4.0, 0.1, 0.1), (0, -0.04, 0.62), "ap_steel", 0.01))
    P.append(m.bx((4.0, 0.1, 0.1), (0, -0.04, 0.78), "ap_steel", 0.01))

    for x in (-1.9, 0.0, 1.9):
        P.append(m.bx((0.14, 0.2, 1.2), (x, 0.12, 0.0), "ap_steel_d", 0.02))
        P.append(m.bx((0.12, 0.14, 0.14), (x, -0.1, 0.62), "ap_steel_d", 0.01))

    P.append(m.bx((4.0, 0.08, 0.14), (0, 0.0, 1.1), "ap_orange", 0.01))
    P.append(m.bx((0.1, 0.1, 0.1), (-1.9, -0.02, 1.0), "ap_white", 0.0))
    ob = m.finish("crashbar", P, budget=1200)

    return ob


def fence():
    m.setup()
    L, H = 4.9, 2.1
    P = []

    for x in (-L / 2, L / 2):
        P.append(m.cyl(0.05, H + 0.08, (x, 0, 0), "ap_steel", 6))
        P.append(m.cyl(0.075, 0.1, (x, 0, H + 0.08), "ap_steel_d", 6))

    P.append(m.bar((-L / 2, 0, H), (L / 2, 0, H), 0.035, "ap_steel", 6))
    P.append(m.bar((-L / 2, 0, 0.1), (L / 2, 0, 0.1), 0.03, "ap_steel", 6))
    P.append(m.bar((-L / 2, 0, H / 2), (L / 2, 0, H / 2), 0.015, "ap_steel_d", 4))
    n = 22

    for i in range(n + 1):
        x = -L / 2 + 0.07 + i * (L - 0.14) / n
        P.append(m.bar((x, 0.0, 0.1), (x, 0.0, H), 0.011, "ap_steel_l", 4))

    for j in range(3):
        z = 0.4 + j * 0.55
        P.append(m.bar((-L / 2, 0.0, z), (L / 2, 0.0, z + 0.3), 0.007, "ap_steel_d", 4))

    P.append(m.bx((0.3, 0.2, 0.1), (-L / 2, 0.0, 0.0), "ap_sand_d", 0.01))
    P.append(m.bx((0.3, 0.2, 0.1), (L / 2, 0.0, 0.0), "ap_sand_d", 0.01))
    ob = m.finish("fence", P, budget=800, cull=False, grime=None)

    return ob


def rail():
    m.setup()
    P = []

    for x in (-0.85, 0.85):
        P.append(m.bx((0.14, 0.26, 0.08), (x, 0, 0.0), "ap_steel_d", 0.01))

    for x in (-0.85, 0.85):
        P.append(m.bar((x, -0.12, 0.0), (x, 0.0, 1.05), 0.03, "ap_steel_d", 6))
        P.append(m.bar((x, 0.12, 0.0), (x, 0.0, 1.05), 0.03, "ap_steel_d", 6))
        P.append(m.bx((0.14, 0.3, 0.06), (x, 0.0, 0.0), "ap_steel_d", 0.01))

    P.append(m.bar((-0.88, 0, 1.05), (0.88, 0, 1.05), 0.032, "ap_steel_d", 6))
    P.append(m.bar((-0.88, 0, 0.2), (0.88, 0, 0.2), 0.03, "ap_steel_d", 6))
    n = 8

    for i in range(n):
        x = -0.85 + 0.0 + i * 1.7 / n
        P.append(m.bx((1.7 / n - 0.01, 0.04, 0.32), (x + 1.7 / n / 2, 0.0, 0.62), "ap_orange" if i % 2 else "ap_white", 0.0))

    P.append(m.bx((1.7, 0.04, 0.1), (0, 0, 0.5), "ap_steel_d", 0.0))
    ob = m.finish("rail", P, budget=700, grime=None)

    return ob


def chock():
    m.setup()
    P = []

    for s in (-1, 1):
        wedge = m.sweep_xz([(-0.25, 0.0), (0.25, 0.0), (0.25, 0.1), (-0.25, 0.26)], 0.42, (0, 0, 0), "ap_yellow")
        wedge2 = m.bx((0.1, 0.42, 0.26), (-0.22, 0, 0.0), "ap_yellow", 0.03)
        m.k.move(wedge, s * 0.4, 0.0, 0.0)
        m.k.move(wedge2, s * 0.4, 0.0, 0.0)
        P += [wedge, wedge2]

        for i in range(4):
            P.append(m.bx((0.04, 0.38, 0.03), (s * 0.4 - 0.12 + i * 0.1, 0, 0.1 + (i * 0.04)), "ap_rubber", 0.0))

    P.append(m.bar((-0.15, 0.0, 0.12), (0.15, 0.0, 0.12), 0.015, "ap_dark", 4))
    ob = m.finish("chock", P, budget=700, grime=None)

    return ob


def cone():
    m.setup()
    P = [m.bx((0.35, 0.35, 0.05), (0, 0, 0), "ap_orange_d", 0.02)]
    P.append(m.lathe([(0, 0.05), (0.14, 0.05), (0.09, 0.4), (0.05, 0.7), (0.035, 0.75), (0, 0.75)], (0, 0, 0), "ap_orange", 12))
    P.append(m.cyl(0.098, 0.1, (0, 0, 0.25), "ap_white", 12, top=0.08))
    P.append(m.cyl(0.07, 0.08, (0, 0, 0.5), "ap_white", 12, top=0.06))
    ob = m.finish("cone", P, budget=400, grime=None, cull=False)

    return ob


ALL = {
    "tank": tank,
    "radar": radar,
    "vor": vor,
    "flood": flood,
    "localizer": localizer,
    "deflector": deflector,
    "edge": edge,
    "twysign": twysign,
    "windsock": windsock,
    "vdgs": vdgs,
    "lamp": lamp,
    "lighttower": lighttower,
    "bollards": bollards,
    "barrier": barrier,
    "crashbar": crashbar,
    "fence": fence,
    "rail": rail,
    "chock": chock,
    "cone": cone,
}
