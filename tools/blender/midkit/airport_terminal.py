import math

import midkit_core as m
import midkit_structures as st
import midkit_walls as wl


def gatehouse():
    m.setup()
    P = [m.bx((8.0, 8.0, 0.18), (0, 0, 0), "ap_sand_d", 0.02)]
    P.append(m.bx((8.0, 8.0, 0.4), (0, 0, 4.05), "ap_sand", 0.05))
    P.append(m.bx((8.2, 8.2, 0.12), (0, 0, 3.93), "ap_steel_d", 0.02))
    P.append(m.bx((8.0, 0.3, 0.3), (0, -3.9, 3.7), "ap_orange", 0.03))
    P.append(m.bx((8.0, 0.3, 0.3), (0, 3.9, 3.7), "ap_orange", 0.03))

    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(m.cyl(0.22, 3.9, (sx * 3.5, sy * 3.5, 0.18), "ap_steel", 10))
            P.append(m.cyl(0.32, 0.25, (sx * 3.5, sy * 3.5, 0.18), "ap_steel_d", 10))

    P.append(m.bx((2.4, 3.6, 0.25), (0, 0, 0.18), "ap_sand_l", 0.04))
    P += wl.plain_wall(2.2, 0.9, (0, -1.6, 0.4), "ap_sand_l", plinth=0.0, cap="ap_sand")
    P += wl.plain_wall(2.2, 0.9, (0, 1.9, 0.4), "ap_sand_l", facing=180, cap="ap_sand")
    P += wl.plain_wall(3.2, 0.9, (-1.1, 0, 0.4), "ap_sand_l", facing=-90, cap="ap_sand")
    P += wl.plain_wall(3.2, 0.9, (1.1, 0, 0.4), "ap_sand_l", facing=90, cap="ap_sand")
    P.append(m.flat((2.0, 3.0, 0.1), (0, 0, 2.6), "ap_steel_d"))
    P.append(m.bx((2.5, 3.7, 0.2), (0, 0, 2.7), "ap_sand", 0.04))

    for s in (-1, 1):
        P.append(m.flat((2.0, 0.06, 1.2), (0, s * 1.6, 1.4), "ap_glass"))
        P.append(m.flat((0.06, 3.0, 1.2), (s * 1.0, 0.0, 1.4), "ap_glass"))

    for x in (-1.0, 0.0, 1.0):
        P.append(m.flat((0.06, 0.1, 1.2), (x, -1.6, 1.4), "ap_steel_d"))

    for y in (-1.6, 0.0, 1.6):
        P.append(m.flat((0.1, 0.06, 1.2), (-1.0, y, 1.4), "ap_steel_d"))

    P.append(m.bx((2.0, 0.1, 0.12), (0, -1.65, 1.4), "ap_steel_d", 0.0))

    for sx in (-1, 1):
        P.append(m.bx((0.5, 4.0, 0.35), (sx * 2.2, 0, 0.18), "ap_yellow", 0.04))

    P += m.hazard(7.0, 0.18, (0, -3.0, 0.2), axis_x=True)
    ob = m.finish("gatehouse", P, budget=4000)

    return ob


def lounge():
    m.setup()
    W, D, H = 7.8, 15.8, 8.6
    P = [m.bx((W, D, 0.3), (0, 0, 0), "ap_sand_d", 0.03)]
    zs = [0.3, 4.5]
    P.append(m.flat((0.06, D - 0.4, H - 0.5), (-W / 2 + 0.2, 0, 0.3), "ap_glass"))
    P.append(m.flat((0.06, D - 0.4, H - 0.5), (W / 2 - 0.2, 0, 0.3), "ap_glass"))
    P.append(m.flat((W - 0.4, 0.06, H - 0.5), (0, -D / 2 + 0.2, 0.3), "ap_glass"))
    P.append(m.flat((W - 0.4, 0.06, H - 0.5), (0, D / 2 - 0.2, 0.3), "ap_glass"))

    for sx in (-1, 1):
        P.append(m.flat((0.07, D - 0.5, (H - 0.5) * 0.35), (sx * (W / 2 - 0.2), 0, 0.3 + (H - 0.5) * 0.65), "ap_glass_l"))

    for sy in (-1, 1):
        P.append(m.flat((W - 0.5, 0.07, (H - 0.5) * 0.35), (0, sy * (D / 2 - 0.2), 0.3 + (H - 0.5) * 0.65), "ap_glass_l"))

    n = 8

    for i in range(n + 1):
        y = -D / 2 + 0.25 + i * (D - 0.5) / n

        for sx in (-1, 1):
            P.append(m.bx((0.3, 0.3, H - 0.5), (sx * (W / 2 - 0.2), y, 0.3), "ap_steel_d", 0.03))

    for i in range(1, 4):
        x = -W / 2 + 0.2 + i * (W - 0.4) / 4

        for sy in (-1, 1):
            P.append(m.bx((0.22, 0.3, H - 0.5), (x, sy * (D / 2 - 0.2), 0.3), "ap_steel_d", 0.03))

    for z in (3.0, 5.6):
        P.append(m.bx((W - 0.2, 0.2, 0.2), (0, -D / 2 + 0.2, z), "ap_steel_d", 0.02))
        P.append(m.bx((W - 0.2, 0.2, 0.2), (0, D / 2 - 0.2, z), "ap_steel_d", 0.02))
        P.append(m.bx((0.2, D - 0.2, 0.2), (-W / 2 + 0.2, 0, z), "ap_steel_d", 0.02))
        P.append(m.bx((0.2, D - 0.2, 0.2), (W / 2 - 0.2, 0, z), "ap_steel_d", 0.02))

    P.append(m.bx((W + 0.5, D + 0.5, 0.45), (0, 0, H - 0.2), "ap_sand", 0.05))
    P.append(m.bx((W + 0.6, 0.3, 0.35), (0, -D / 2 - 0.2, H + 0.25), "ap_orange", 0.03))
    P.append(m.bx((W + 0.6, 0.3, 0.35), (0, D / 2 + 0.2, H + 0.25), "ap_orange", 0.03))
    P += wl.ac_unit((0.0, -3.0, H + 0.25), size=(1.6, 1.1, 1.0))
    P += wl.ac_unit((0.0, 3.0, H + 0.25), size=(1.6, 1.1, 1.0))
    P.append(m.bx((2.2, 0.2, 0.9), (0, -D / 2 + 0.2, 0.3), "ap_orange", 0.02))
    P.append(m.bx((W - 0.4, 0.1, 0.1), (0, -D / 2 + 0.3, 1.0), "ap_steel", 0.0))
    ob = m.finish("lounge", P, budget=5000)

    return ob


def facade():
    m.setup()
    P = [m.bx((8.0, 4.0, 0.3), (0, 0, 0), "ap_sand_d", 0.02)]
    H = 9.4

    for sx in (-1, 1):
        P.append(m.bx((1.0, 4.0, H), (sx * 3.5, 0, 0.3), "ap_sand_l", 0.06))
        P.append(m.bx((1.2, 0.4, 0.7), (sx * 3.5, -1.8, 0.3), "ap_sand", 0.04))
        P.append(m.bx((0.3, 3.4, H - 1.4), (sx * 2.9, 0.0, 0.7), "ap_sand", 0.03))

    P.append(m.bx((8.0, 4.0, 0.7), (0, 0, H - 0.4), "ap_sand", 0.06))
    P.append(m.bx((8.0, 0.4, 0.3), (0, -1.9, H - 0.7), "ap_orange", 0.03))
    gh = H - 1.4
    P.append(m.flat((5.0, 0.08, gh), (0, 0.2, 0.3), "ap_glass"))
    P.append(m.flat((5.0, 0.09, gh * 0.4), (0, 0.15, 0.3 + gh * 0.6), "ap_glass_l"))

    for i in range(1, 5):
        P.append(m.bx((0.1, 0.2, gh), (-2.5 + i * 1.0, 0.1, 0.3), "ap_steel_d", 0.0))

    P.append(m.bx((5.0, 0.2, 0.12), (0, 0.1, 0.3 + gh * 0.55), "ap_steel_d", 0.0))
    P.append(m.bx((5.0, 0.25, 0.4), (0, 0.1, 0.3), "ap_steel_d", 0.02))
    P.append(m.bx((5.0, 1.2, 0.15), (0, -0.9, 3.4), "ap_sand", 0.03))

    for i in range(5):
        P.append(m.bx((0.1, 0.1, 0.5), (-2.0 + i * 1.0, -1.4, 3.4 - 0.5), "ap_steel_d", 0.0))

    for sx in (-1, 1):
        for i in range(3):
            P.append(m.bx((0.08, 0.1, H - 1.2), (sx * 3.5 - 0.3 + i * 0.3, -2.0, 0.9), "ap_sand", 0.0))

        P.append(m.bx((1.2, 0.5, 0.35), (sx * 3.5, -2.1, 3.4), "ap_sand_d", 0.03))
        P.append(m.cyl(0.09, 0.14, (sx * 3.5, -2.25, 5.2), "ap_white", 8))
        P.append(m.cyl(0.05, 0.16, (sx * 3.5, -2.1, 5.2), "ap_steel_d", 6))

    for i in range(4):
        P.append(m.bx((0.42, 0.34, 0.5), (-1.95 + i * 1.3, -1.45, 0.3), "ap_sand_d", 0.03))
        P.append(m.bx((0.34, 0.26, 0.24), (-1.95 + i * 1.3, -1.45, 0.8), "ap_leaf_d", 0.08, seg=1))

    P.append(m.bx((5.0, 0.18, 0.5), (0, 0.0, 0.3 + gh - 0.5), "ap_steel_d", 0.02))
    ob = m.finish("facade", P, budget=3500)

    return ob


def canopy():
    m.setup()
    P = []

    for sx in (-1, 1):
        P.append(m.cyl(0.26, 4.9, (sx * 3.4, 2.8, 0.12), "ap_steel", 12))
        P.append(m.cyl(0.4, 0.3, (sx * 3.4, 2.8, 0.12), "ap_steel_d", 12))
        P.append(m.bx((0.9, 0.9, 0.12), (sx * 3.4, 2.8, 0.0), "ap_sand_d", 0.02))
        P.append(m.bx((0.9, 7.8, 0.3), (sx * 3.4, 0.0, 4.9), "ap_steel_d", 0.03))

    P.append(m.bx((8.0, 8.0, 0.35), (0, 0, 5.0), "ap_sand", 0.05))
    P.append(m.bx((8.1, 0.3, 0.55), (0, -3.85, 5.0), "ap_orange", 0.04))
    P.append(m.bx((8.1, 0.3, 0.3), (0, 3.85, 5.0), "ap_sand_l", 0.04))
    P.append(m.bx((0.3, 7.6, 0.3), (-3.85, 0, 5.0), "ap_sand_l", 0.04))
    P.append(m.bx((0.3, 7.6, 0.3), (3.85, 0, 5.0), "ap_sand_l", 0.04))

    for i in range(3):
        P.append(m.bx((1.2, 0.5, 0.1), (-2.4 + i * 2.4, 0.0, 4.9), "ap_white", 0.01))

    P += m.hazard(8.0, 0.2, (0, -2.0, 0.12), axis_x=True)
    ob = m.finish("canopy", P, budget=3500)

    return ob


def bridge():
    m.setup()
    P = []
    zf = 4.0
    rx = -14.8
    P.append(m.cyl(1.9, 3.3, (rx, 0, zf), "ap_sand_l", 14))
    P.append(m.cyl(2.0, 0.22, (rx, 0, zf - 0.1), "ap_steel_d", 14))
    P.append(m.cyl(2.0, 0.22, (rx, 0, zf + 3.2), "ap_steel_d", 14))
    P.append(m.cyl(0.38, zf, (rx, 0, 0.0), "ap_steel", 10))
    P.append(m.bx((2.0, 2.0, 0.25), (rx, 0, 0.0), "ap_sand_d", 0.03))

    for i in range(6):
        a = math.radians(i * 60 + 20)
        P.append(m.bx((0.4, 0.1, 1.0), (rx + math.cos(a) * 1.92, math.sin(a) * 1.92, zf + 1.4), "ap_glass", 0.0))

    spans = ((-13.5, -5.0, 2.9, 2.75), (-5.0, 3.0, 2.65, 2.55), (3.0, 10.5, 2.4, 2.35))

    for x0, x1, w, h in spans:
        L = x1 - x0
        xc = (x0 + x1) / 2
        z0 = zf + 0.1 + (2.75 - h)
        P.append(m.bx((L, w, h), (xc, 0, z0), "ap_sand_l", 0.07))
        P.append(m.bx((L - 0.3, w + 0.08, 0.1), (xc, 0, z0 + h * 0.34), "ap_steel_d", 0.01))

        for s in (-1, 1):
            P.append(m.flat((L - 0.8, 0.05, h * 0.38), (xc, s * (w / 2 + 0.03), z0 + h * 0.4), "ap_glass"))
            P.append(m.flat((L - 0.8, 0.052, h * 0.1), (xc, s * (w / 2 + 0.03), z0 + h * 0.78), "ap_glass_l"))

        n = int(L / 1.6)

        for j in range(n + 1):
            for s in (-1, 1):
                P.append(m.bx((0.12, 0.1, h * 0.55), (x0 + 0.4 + j * (L - 0.8) / n, s * (w / 2 + 0.05), z0 + h * 0.36), "ap_steel_d", 0.0))

        P.append(m.bx((L, w + 0.12, 0.18), (xc, 0, z0 - 0.15), "ap_steel_d", 0.02))
        P.append(m.bx((L - 0.2, w - 0.4, 0.14), (xc, 0, z0 + h - 0.01), "ap_sand_d", 0.02))

    cx = 13.0
    P.append(m.bx((3.0, 2.3, 2.3), (cx, 0, zf + 0.2), "ap_orange", 0.07))
    P.append(m.bx((0.1, 2.0, 1.1), (cx + 1.5, 0, zf + 0.9), "ap_glass", 0.0))
    P.append(m.bx((3.2, 2.5, 0.2), (cx, 0, zf + 2.5), "ap_orange_d", 0.03))

    for i in range(7):
        P.append(m.bx((0.12, 3.0 - 0.25 * (i % 2 == 0), 2.4), (10.55 + i * 0.13, 0, zf + 0.1), "ap_dark" if i % 2 else "ap_steel_d", 0.01))

    P.append(m.bx((2.6, 0.6, 0.5), (cx, 0, zf - 0.5), "ap_steel_d", 0.04))

    for s in (-1, 1):
        P.append(m.bx((0.3, 0.3, zf - 0.8), (cx, s * 0.8, 0.8), "ap_steel", 0.02))
        P += m.tire(0.4, 0.3, (cx, s * 1.0, 0.4), axis="y")

    P.append(m.bx((1.6, 0.9, 0.3), (cx, 0, 0.8), "ap_steel_d", 0.03))
    P.append(m.bx((0.3, 2.4, 0.18), (cx + 1.55, 0, zf + 0.15), "ap_yellow", 0.02))
    ob = m.finish("bridge", P, budget=6000)

    return ob


def checkin():
    m.setup()
    P = [m.bx((2.0, 2.5, 0.12), (0, 0, 0), "ap_sand_d", 0.02)]
    P.append(m.bx((1.7, 2.3, 0.85), (0, 0, 0.12), "ap_sand", 0.05))
    P.append(m.bx((1.9, 2.5, 0.08), (0, 0, 0.97), "ap_sand_l", 0.02))
    P.append(m.bx((0.9, 1.7, 0.45), (-0.35, 0.0, 1.05), "ap_dark", 0.04))
    P.append(m.bx((0.7, 1.5, 0.35), (-0.35, 0.0, 1.45), "ap_steel_d", 0.03))
    P.append(m.flat((0.04, 1.3, 0.28), (-0.7, 0.0, 1.48), "ap_glass_l"))

    for yy in (-0.6, 0.6):
        P.append(m.bx((0.45, 0.4, 0.3), (0.3, yy, 1.05), "ap_steel_l", 0.03))
        P.append(m.flat((0.3, 0.02, 0.15), (0.3, yy - 0.2, 1.15), "ap_glass"))

    P.append(m.bx((0.5, 2.0, 0.1), (0.7, 0, 0.12), "ap_dark", 0.01))
    P.append(m.bx((1.6, 0.06, 0.4), (0, -1.16, 0.4), "ap_orange", 0.01))
    P.append(m.bx((1.2, 0.2, 0.08), (0.0, -1.25, 0.12), "ap_steel_d", 0.01))
    ob = m.finish("checkin", P, budget=1800)

    return ob


def seats():
    m.setup()
    P = [m.bar((-1.1, 0, 0.3), (1.1, 0, 0.3), 0.05, "ap_steel_d", 6)]

    for sx in (-1, 1):
        P.append(m.bx((0.1, 0.5, 0.06), (sx * 1.1, 0, 0.0), "ap_steel_d", 0.01))
        P.append(m.bar((sx * 1.1, -0.1, 0.05), (sx * 1.1, 0.0, 0.35), 0.035, "ap_steel_d", 6))
        P.append(m.bar((sx * 1.1, 0.1, 0.05), (sx * 1.1, 0.0, 0.35), 0.035, "ap_steel_d", 6))

    for i in range(4):
        x = -0.9 + i * 0.6
        P.append(m.bx((0.54, 0.5, 0.1), (x, -0.02, 0.38), "ap_blue", 0.04))
        P.append(m.bx((0.54, 0.1, 0.42), (x, 0.2, 0.46), "ap_blue_d", 0.04))
        P.append(m.bx((0.06, 0.4, 0.07), (x - 0.29, -0.02, 0.6), "ap_steel_d", 0.01))

    P.append(m.bx((0.06, 0.4, 0.07), (1.2, -0.02, 0.6), "ap_steel_d", 0.01))
    ob = m.finish("seats", P, budget=1200)

    return ob


def kiosk():
    m.setup()
    P = [m.bx((0.6, 0.57, 0.1), (0, 0, 0), "ap_steel_d", 0.02)]
    P.append(m.bx((0.34, 0.3, 1.15), (0, 0.08, 0.1), "ap_steel", 0.05))
    P.append(m.bx((0.54, 0.42, 0.42), (0, -0.0, 1.0), "ap_sand_d", 0.05))
    P.append(m.bx((0.46, 0.04, 0.3), (0, -0.215, 1.07), "ap_dark", 0.01))
    P.append(m.flat((0.4, 0.03, 0.22), (0, -0.23, 1.11), "ap_glass_l"))
    P.append(m.bx((0.46, 0.2, 0.06), (0, -0.2, 0.92), "ap_steel_d", 0.01))
    P.append(m.bx((0.3, 0.06, 0.1), (0, -0.2, 0.66), "ap_orange", 0.01))
    P.append(m.bx((0.18, 0.03, 0.12), (0.0, -0.14, 0.82), "ap_dark", 0.0))
    P.append(m.bx((0.5, 0.45, 0.07), (0, 0.0, 1.42), "ap_sand", 0.02))
    ob = m.finish("kiosk", P, budget=1000)

    return ob


def arch():
    m.setup()
    P = []

    for sx in (-1, 1):
        P.append(m.bx((0.18, 0.7, 2.2), (sx * 0.72, 0, 0.1), "ap_steel_l", 0.04))
        P.append(m.bx((0.3, 0.9, 0.12), (sx * 0.72, 0, 0.0), "ap_steel_d", 0.02))
        P.append(m.bx((0.06, 0.5, 1.6), (sx * 0.62, 0, 0.3), "ap_dark", 0.01))
        P.append(m.bx((0.1, 0.45, 0.1), (sx * 0.72, 0, 0.9), "ap_orange", 0.01))

    P.append(m.bx((1.62, 0.8, 0.28), (0, 0, 2.05), "ap_steel_l", 0.05))
    P.append(m.bx((0.4, 0.82, 0.08), (0, 0, 2.33), "ap_steel_d", 0.02))
    P.append(m.bx((0.32, 0.1, 0.16), (0, -0.4, 2.12), "ap_dark", 0.01))
    P.append(m.cyl(0.05, 0.04, (0.3, -0.42, 2.18), "ap_green", 8))
    P.append(m.bx((1.5, 0.8, 0.07), (0, 0, 0.0), "ap_dark", 0.01))
    ob = m.finish("arch", P, budget=1200)

    return ob


def depboard():
    m.setup()
    P = [m.bx((1.3, 0.45, 0.12), (0, 0, 0), "ap_steel_d", 0.02)]

    for sx in (-1, 1):
        P.append(m.bx((0.12, 0.2, 1.9), (sx * 0.5, 0, 0.12), "ap_steel", 0.03))

    P.append(m.bx((1.78, 0.34, 1.5), (0, 0, 1.4), "ap_steel_d", 0.06))
    P.append(m.bx((1.6, 0.04, 1.28), (0, -0.19, 1.51), "ap_void", 0.01))

    for i in range(9):
        row = i * 0.135
        P.append(m.flat((1.42, 0.02, 0.07), (0, -0.215, 1.57 + 1.0 * 0.0 + row * 0.0 + (i - 4) * 0.12 * -1), "ap_glass_l" if i % 2 else "ap_yellow"))

    P.append(m.bx((1.6, 0.36, 0.1), (0, 0, 2.9 - 0.1), "ap_steel", 0.02))
    P.append(m.flat((0.6, 0.04, 0.14), (0.0, -0.19, 2.55), "ap_orange"))
    ob = m.finish("depboard", P, budget=1500)

    return ob


ALL = {
    "gatehouse": gatehouse,
    "lounge": lounge,
    "facade": facade,
    "canopy": canopy,
    "bridge": bridge,
    "checkin": checkin,
    "seats": seats,
    "kiosk": kiosk,
    "arch": arch,
    "depboard": depboard,
}
