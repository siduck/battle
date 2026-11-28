import math
import random

import arena_parts as A
import jp
from arena_parts import F, B, R, cyl, flat, rod, tilted, done, k
from jp import add


def lying(r, length, at, color, sides=12, axis="x", top=None):
    ob = k.prism("lying", sides * jp.N, r, length, (0, 0, 0), jp.c(color), radius_top=top)
    k.move(ob, 0, 0, -length / 2)

    if axis == "x":
        k.rotate(ob, 90, "Y")
    else:
        k.rotate(ob, 90, "X")

    k.move(ob, *at)

    return add(ob)


def ball(at, r=0.11, color="st_red"):
    x, y, z = at
    prof = [(0, -r), (r * 0.7, -r * 0.7), (r, 0), (r * 0.7, r * 0.7), (0, r)]
    ob = k.lathe("ball", prof, 6, (x, y, z), jp.c(color))
    k.rotate(ob, 90, "Y", (x, y, z))

    return add(ob)


def net_lines(a, b, n, drop=(0, 0, 0), color="st_net", r=0.006):
    from mathutils import Vector

    for i in range(n + 1):
        t = i / n
        p = Vector(a) + (Vector(b) - Vector(a)) * t
        rod(p, p + Vector(drop), r, color, 4)


def goal_frame(w, h, depth, post, back_h, mesh_gap):
    xs = w / 2 + post
    y0, y1 = -depth / 2, depth / 2

    for sx in (-1, 1):
        R((sx * xs, y0, 0), (sx * xs, y0, h), post, "st_white", 8)
        R((sx * xs, y0, 0), (sx * xs, y1, 0), post * 0.7, "st_white", 6)
        R((sx * xs, y0, h), (sx * xs, y1, back_h), post * 0.7, "st_white", 6)
        R((sx * xs, y1, back_h), (sx * xs, y1, 0), post * 0.7, "st_white", 6)

    R((-xs - post, y0, h), (xs + post, y0, h), post, "st_white", 8)
    R((-xs, y1, back_h), (xs, y1, back_h), post * 0.7, "st_white", 6)
    R((-xs, y1, 0), (xs, y1, 0), post * 0.7, "st_white", 6)

    n = int(2 * xs / mesh_gap)

    for i in range(n + 1):
        x = -xs + i * 2 * xs / n
        R((x, y0, h), (x, y1, back_h), 0.006, "st_net", 4)
        R((x, y1, back_h), (x, y1, 0.0), 0.006, "st_net", 4)

    m = int(depth / mesh_gap)

    for j in range(1, m + 1):
        y = y0 + j * depth / m
        z = h + (back_h - h) * j / m
        R((-xs, y, z), (xs, y, z), 0.006, "st_net", 4)

    q = int(back_h / mesh_gap)

    for j in range(1, q + 1):
        z = back_h * j / (q + 1)
        R((-xs, y1, z), (xs, y1, z), 0.006, "st_net", 4)

    for sx in (-1, 1):
        for j in range(1, 5):
            z = h * j / 5
            R((sx * xs, y0, z), (sx * xs, y1, z * back_h / h), 0.006, "st_net", 4)


def goal():
    A.setup(61)
    goal_frame(7.32, 2.44, 2.0, 0.06, 1.9, 0.5)

    return done("goal", 2500)


def tgoal():
    A.setup(62)
    goal_frame(2.8, 1.07, 1.0, 0.05, 0.8, 0.4)

    return done("tgoal", 1500)


def tarp():
    A.setup(63)
    lying(0.5, 3.0, (0, 0.0, 0.5), "st_blue_d", 14)

    for x in (-0.9, 0.0, 0.9):
        lying(0.52, 0.12, (x, 0.0, 0.5), "st_char", 14)

    lying(0.38, 0.06, (1.51, 0.0, 0.5), "st_blue_dd", 12)
    lying(0.18, 0.06, (1.54, 0.0, 0.5), "st_blue_d", 10)
    lying(0.04, 3.4, (0, 0.0, 0.5), "st_wood_l", 8)
    flat((2.9, 1.5, 0.03), (0, 1.0, 0.0), "st_blue")
    flat((2.9, 0.06, 0.06), (0, 1.75, 0.03), "st_blue_d")
    B((0.16, 0.5, 0.08), (-1.2, 0.0, 0.0), "st_wood_d", 0.01)
    B((0.16, 0.5, 0.08), (1.2, 0.0, 0.0), "st_wood_d", 0.01)

    return done("tarp", 1200)


def dummy():
    A.setup(64)
    cyl(0.38, 0.14, (0, 0, 0), "st_char", 12, top=0.34)
    cyl(0.07, 0.3, (0, 0, 0.14), "st_steel_d", 8)
    cyl(0.27, 1.45, (0, 0, 0.3), "st_blue_d", 12, top=0.24)
    cyl(0.245, 0.14, (0, 0, 1.74), "st_blue_d", 12, top=0.17)

    for z, col in ((0.5, "st_white"), (1.25, "st_red")):
        cyl(0.285, 0.1, (0, 0, z), col, 12, top=0.27)


    return done("dummy", 900)


def sled():
    A.setup(65)

    for sy in (-1, 1):
        y = sy * 0.5
        R((-1.3, y, 0.1), (1.0, y, 0.1), 0.05, "st_steel_d", 6)
        R((1.0, y, 0.1), (1.3, y, 0.4), 0.05, "st_steel_d", 6)
        B((2.4, 0.1, 0.05), (0, y, 0.0), "st_steel", 0.0)

    for x in (-1.0, 0.0, 0.9):
        R((x, -0.5, 0.1), (x, 0.5, 0.1), 0.04, "st_steel_d", 4)

    for sy in (-1, 1):
        y = sy * 0.3
        R((-0.7, y, 0.1), (-0.95, y, 1.4), 0.05, "st_steel", 6)


    for sy in (-1, 1):
        pad = jp.bx((0.4, 0.45, 1.25), (0, 0, 0), jp.c("st_red") if False else "st_red", 0.05)
        k.rotate(pad, -10, "Y")
        k.move(pad, -1.0, sy * 0.3, 0.7)
        add(pad)

    for i in range(4):
        cyl(0.22 - i * 0.0, 0.07, (0.6 + i * 0.0, 0.0, 0.18 + i * 0.07), "st_char", 12)

    cyl(0.04, 0.8, (0.6, 0.0, 0.18), "st_steel", 6)
    flat((0.12, 1.0, 0.04), (-1.1, 0.0, 1.8), "st_steel_d")
    R((-1.1, -0.45, 1.8), (-1.1, 0.45, 1.8), 0.03, "st_steel_d", 4)

    return done("sled", 1800)


def rack():
    A.setup(66)
    w, d = 2.6, 0.65

    for sx in (-1, 1):
        for sy in (-1, 1):
            B((0.06, 0.06, 1.9), (sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), 0.0), "st_steel_d", 0.01)

    for z in (0.15, 0.7, 1.25, 1.8):
        B((w, d, 0.04), (0, 0, z), "st_wood_l" if z < 1.7 else "st_steel", 0.01)

    for z in (0.15, 0.7, 1.25):
        for i in range(10):
            x = -w / 2 + 0.2 + i * 0.245
            ball((x, -0.08 if i % 2 else 0.08, z + 0.04 + 0.11), 0.11, "st_red" if i % 3 == 0 else "st_white" if i % 3 == 1 else "st_blue")

    B((w - 0.1, 0.04, 0.04), (0, -d / 2, 1.5), "st_steel", 0.0)

    for i in range(5):
        x = -1.0 + i * 0.5

    for sx in (-1, 1):
        flat((0.07, d + 0.1, 0.06), (sx * (w / 2 - 0.03), 0, 0.0), "st_steel_d")


    for i in range(4):
        cyl(0.11 - i * 0.02, 0.06, (-0.9, 0.0, 1.84 + i * 0.06), "st_mustard", 8)

    return done("rack", 2500)


def tactics():
    A.setup(67)
    B((1.2, 0.07, 0.9), (0, 0, 0.82), "st_steel_d", 0.02)
    flat((1.1, 0.04, 0.8), (0, -0.05, 0.87), "st_white")

    for z in (0.95, 1.55):
        flat((0.9, 0.03, 0.02), (0, -0.075, z), "st_blue")

    for x in (-0.44, 0.44):
        flat((0.02, 0.03, 0.62), (x, -0.075, 0.95), "st_blue")

    for sx in (-1, 1):
        for z in (1.08, 1.4):
            flat((0.2, 0.03, 0.02), (sx * 0.34, -0.075, z), "st_blue")

        for x in (0.25,):
            flat((0.02, 0.03, 0.32), (sx * 0.24, -0.075, 1.08), "st_blue")

    for x, z, col in ((-0.3, 1.2, "st_red"), (0.1, 1.3, "st_red"), (0.35, 1.2, "st_blue_d"), (-0.15, 1.0, "st_blue_d")):
        A.disc(0.04, 0.02, (x, -0.085, z), col, 8)

    B((1.2, 0.18, 0.04), (0, -0.07, 0.78), "st_steel", 0.01)

    for sx in (-1, 1):
        R((sx * 0.55, -0.0, 1.72), (sx * 0.75, -0.55, 0.0), 0.03, "st_steel_d", 4)

    R((0.0, 0.3, 1.72), (0.0, 0.6, 0.0), 0.03, "st_steel_d", 4)

    return done("tactics", 900)


def cones():
    A.setup(68)

    for i in range(8):
        y = -2.0 + i * 0.57
        prof = [(0.13, 0.0), (0.13, 0.03), (0.1, 0.1), (0.055, 0.45), (0.03, 0.6), (0.0, 0.62)]
        ob = k.lathe("cone", [(0.01, 0.0)] + prof, 10, (0, y, 0), jp.c("st_red" if i % 2 else "st_mustard"))
        add(ob)
        cyl(0.07, 0.04, (0, y, 0.25), "st_white", 10, top=0.065)

    return done("cones", 1200)


def hurdle():
    A.setup(69)

    for sx in (-1, 1):
        x = sx * 0.55
        B((0.06, 0.8, 0.04), (x, 0.0, 0.0), "st_steel_d", 0.0)
        R((x, 0.3, 0.02), (x, 0.3, 0.9), 0.025, "st_steel", 6)

    B((1.3, 0.05, 0.28), (0, 0.3, 0.64), "st_white", 0.01)
    B((1.3, 0.055, 0.1), (0, 0.3, 0.74), "st_red", 0.0)
    B((1.3, 0.055, 0.06), (0, 0.3, 0.62), "st_red", 0.0)

    return done("hurdle", 600)


def discus():
    A.setup(70)
    R0 = 4.3
    h = 5.4
    cyl(1.2, 0.05, (0, 0, 0), "st_conc", 14)
    cyl(1.25, 0.03, (0, 0, 0), "st_conc_d", 14)
    posts = []

    for i in range(7):
        t = math.radians(-90 + 45 + i * 45 - 0)
        t = math.radians(-135 + 270 * i / 6 - 90 + 90)
        x, y = R0 * math.cos(t), R0 * math.sin(t)
        posts.append((x, y))
        cyl(0.09, h, (x, y, 0.0), "st_steel_d", 8, top=0.06)
        B((0.4, 0.4, 0.06), (x, y, 0.0), "st_conc_d", 0.01)

    for (xa, ya), (xb, yb) in zip(posts, posts[1:]):
        for j in range(1, 7):
            z = j * 0.8
            R((xa, ya, z), (xb, yb, z), 0.012, "st_net", 4)

        L = math.hypot(xb - xa, yb - ya)
        n = int(L / 0.45)

        for m in range(1, n):
            u = m / n
            x, y = xa + (xb - xa) * u, ya + (yb - ya) * u
            R((x, y, 0.05), (x, y, h - 0.1), 0.008, "st_net", 4)

        R((xa, ya, h - 0.05), (xb, yb, h - 0.05), 0.02, "st_steel", 4)

    return done("discus", 3500)


def highjump():
    A.setup(71)
    B((5.4, 4.0, 0.8), (0, 0.2, 0.0), "st_blue_d", 0.08)
    B((5.45, 4.05, 0.08), (0, 0.2, 0.0), "st_char", 0.01)
    B((5.0, 3.6, 0.04), (0, 0.2, 0.8), "st_blue", 0.01)
    flat((5.0, 0.05, 0.06), (0, 0.2, 0.83), "st_white")

    for i in range(1, 4):
        flat((0.05, 3.6, 0.06), (-2.5 + i * 1.25, 0.2, 0.82), "st_blue_dd")

    for sx in (-1, 1):
        x = sx * 2.0
        B((0.7, 0.8, 0.05), (x, -2.0, 0.0), "st_steel_d", 0.01)
        R((x, -2.0, 0.05), (x, -2.0, 2.42), 0.04, "st_steel", 6)
        B((0.1, 0.14, 0.1), (x - sx * 0.1, -2.0, 2.0), "st_steel_d", 0.01)

    R((-1.95, -2.0, 2.0), (1.95, -2.0, 2.0), 0.015, "st_white", 6)

    return done("highjump", 1500)


def cornerflag():
    A.setup(72)
    cyl(0.025, 1.5, (-0.3, 0, 0.0), "st_white", 8, top=0.018)
    cyl(0.07, 0.04, (-0.3, 0, 0.0), "st_char", 8)
    A.profile_xz([(0.0, 0.0), (0.66, 0.15), (0.0, 0.34)], 0.015, "st_red")
    k.move(A.jp.parts[-1], -0.28, 0, 1.12)
    B((0.07, 0.07, 0.04), (-0.3, 0, 1.5), "st_mustard", 0.0)

    return done("cornerflag", 500)


def kitbag():
    A.setup(73)
    B((1.0, 0.5, 0.36), (0, 0, 0.04), "st_blue_d", 0.1)
    B((0.34, 0.46, 0.3), (-0.4, 0, 0.1), "st_blue_dd", 0.08)
    B((0.34, 0.46, 0.3), (0.4, 0, 0.1), "st_blue_dd", 0.08)
    flat((0.9, 0.51, 0.03), (0, 0, 0.36), "st_char")
    flat((0.7, 0.03, 0.02), (0, -0.255, 0.3), "st_steel")
    B((0.5, 0.08, 0.2), (0, -0.28, 0.06), "st_blue", 0.03)
    flat((0.3, 0.02, 0.1), (0.0, -0.325, 0.15), "st_white")

    for sx in (-1, 1):
        R((sx * 0.2, 0.0, 0.4), (sx * 0.15, 0.0, 0.52), 0.015, "st_char", 4)

    R((-0.15, 0.0, 0.52), (0.15, 0.0, 0.52), 0.02, "st_char", 6)

    return done("kitbag", 800)


def crate():
    A.setup(74)
    B((0.52, 0.4, 0.04), (0, 0, 0.0), "st_red", 0.0)

    for sy in (-1, 1):
        B((0.52, 0.03, 0.2), (0, sy * 0.185, 0.0), "st_red", 0.01)

    for sx in (-1, 1):
        B((0.03, 0.4, 0.2), (sx * 0.245, 0, 0.0), "st_red", 0.01)

    for sx in (-1, 0, 1):
        pass

    for i in range(4):
        for j in range(3):
            x = -0.195 + i * 0.13
            y = -0.125 + j * 0.125
            cyl(0.045, 0.2, (x, y, 0.04), "st_blue_l", 6, top=0.045)
            cyl(0.022, 0.1, (x, y, 0.24), "st_blue_l", 6, top=0.02)
            cyl(0.026, 0.02, (x, y, 0.34), "st_white", 6)

    flat((0.52, 0.03, 0.06), (0, -0.215, 0.11), "st_white")

    return done("crate", 1200)


ALL = {
    "goal": goal,
    "tgoal": tgoal,
    "tarp": tarp,
    "dummy": dummy,
    "sled": sled,
    "rack": rack,
    "tactics": tactics,
    "cones": cones,
    "hurdle": hurdle,
    "discus": discus,
    "highjump": highjump,
    "cornerflag": cornerflag,
    "kitbag": kitbag,
    "crate": crate,
}
