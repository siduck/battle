import math
import random

import bmesh
import common as m
import towers as tw
from common import add, flat, bar, place, k, N

ALL = {}


def bx(size, at, color, bevel=0.03):
    if min(size) < 0.1:
        return k.box("f", size, at, m.c(color))

    return k.beveled_box("b", size, at, m.c(color), max(bevel, 0.015))


def reg(fn):
    ALL[fn.__name__] = fn

    return fn


def done(name):
    return m.finish(name, fuse_soft=False)


def post(x, y, z, h, r, color, sides=8):
    return k.prism("p", sides * N // 2 if sides > 6 else sides, r, h, (x, y, z), m.c(color))


def blob(at, r, color, sy=1.0, jit=0.14, seed=0, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    rg = random.Random(seed)

    for v in bm.verts:
        v.co.x = v.co.x * (1 + rg.uniform(-jit, jit))
        v.co.y = v.co.y * (1 + rg.uniform(-jit, jit))
        v.co.z = v.co.z * sy * (1 + rg.uniform(-jit, jit))

    bm.verts.ensure_lookup_table()
    ob = k.lpm._object("blob", bm, m.c(color))
    k.move(ob, *at)

    return ob


def ring_bar(cx, cy, z, r, th, color, segs=10):
    pts = [(cx + r * math.cos(2 * math.pi * i / segs), cy + r * math.sin(2 * math.pi * i / segs)) for i in range(segs)]

    return [bar((pts[i][0], pts[i][1], z), (pts[(i + 1) % segs][0], pts[(i + 1) % segs][1], z), th, color, 4) for i in range(segs)]


@reg
def railing():
    m.setup(41)
    w = 4.0
    add(bx((w, 0.12, 0.12), (0, 0, 0), "ny_iron", 0.02))
    add(bar((-w / 2, 0, 0.88), (w / 2, 0, 0.88), 0.04, "ny_iron", 6))
    add(bar((-w / 2, 0, 0.5), (w / 2, 0, 0.5), 0.025, "ny_iron", 4))

    for i in range(17):
        add(flat((0.03, 0.03, 0.85), (-w / 2 + 0.03 + i * (w - 0.06) / 16, 0, 0.05), "ny_iron"))

    for x in (-w / 2 + 0.06, w / 2 - 0.06):
        add(bx((0.1, 0.1, 0.9), (x, 0, 0), "ny_iron_light", 0.015))
        add(k.prism("fin", 6, 0.06, 0.08, (x, 0, 0.9), m.c("ny_iron_light")))

    return done("railing")


@reg
def bikerack():
    m.setup(42)

    for i in range(4):
        x = -1.35 + i * 0.9
        add(bar((x, 0, 0.0), (x, 0, 0.7), 0.025, "ny_iron_light", 6))
        add(bar((x, 0, 0.7), (x + 0.3, 0, 0.9), 0.025, "ny_iron_light", 6))
        add(bar((x + 0.3, 0, 0.9), (x + 0.6, 0, 0.7), 0.025, "ny_iron_light", 6))
        add(bar((x + 0.6, 0, 0.7), (x + 0.6, 0, 0.0), 0.025, "ny_iron_light", 6))

    add(bx((3.6, 0.19, 0.05), (0, 0, 0), "ny_iron", 0.0))

    return done("bikerack")


@reg
def dumpster():
    m.setup(43)
    add(bx((3.0, 1.7, 1.0), (0, 0, 0.3), "ny_green", 0.05))
    add(bx((3.2, 1.8, 0.12), (0, 0, 1.3), "ny_green_dark", 0.02))

    for i in range(5):
        add(flat((0.05, 0.04, 0.9), (-1.2 + i * 0.6, -0.87, 0.35), "ny_green_dark"))

    for sx in (-1, 1):
        add(bx((0.2, 1.7, 0.3), (sx * 1.3, 0, 0), "ny_iron", 0.0))
        add(k.prism("wheel", 8, 0.12, 0.1, (sx * 1.3, -0.9, 0.0), m.c("ny_iron_light")))

    add(bx((1.4, 0.04, 0.25), (0.6, -0.86, 0.9), "ny_yellow", 0.0))

    return done("dumpster")


@reg
def hoarding():
    m.setup(44)
    w = 4.0
    add(bx((w, 0.12, 2.2), (0, 0.15, 0), "ny_green", 0.02))

    for i in range(8):
        add(flat((0.04, 0.02, 2.2), (-w / 2 + 0.25 + i * 0.5, -0.07, 0), "ny_green_dark"))

    add(bx((w + 0.1, 0.5, 0.12), (0, 0, 2.2), "ny_wood_dark", 0.02))
    add(bx((w + 0.1, 0.4, 0.12), (0, 0, 2.3), "ny_wood", 0.02))

    for x in (-w / 2 + 0.2, 0, w / 2 - 0.2):
        add(bx((0.14, 0.7, 0.14), (x, 0.0, 0), "ny_wood_dark", 0.01))
        add(bar((x, 0.3, 0.1), (x, -0.1, 2.0), 0.04, "ny_wood_dark", 4))

    add(bx((1.6, 0.03, 0.9), (0.9, -0.08, 1.0), "ny_cream", 0.0))
    add(flat((1.2, 0.02, 0.1), (0.9, -0.1, 1.55), "ny_red"))

    return done("hoarding")


@reg
def dining():
    m.setup(45)
    w, d = 4.0, 2.4
    add(bx((w, d, 0.18), (0, 0, 0), "ny_wood", 0.02))

    for x in (-w / 2 + 0.08, w / 2 - 0.08):
        for y in (-d / 2 + 0.08, d / 2 - 0.08):
            add(bx((0.12, 0.12, 2.2), (x, y, 0.18), "ny_wood_dark", 0.01))

    add(bx((w, 0.1, 1.0), (0, -d / 2 + 0.05, 0.18), "ny_wood_light" if "ny_wood_light" in k._INDEX else "ny_wood", 0.01))

    for i in range(10):
        add(flat((0.05, 0.06, 0.95), (-w / 2 + 0.3 + i * 0.38, -d / 2 + 0.05, 0.2), "ny_wood_dark"))

    add(bx((w, 0.1, 0.9), (0, d / 2 - 0.05, 0.18), "ny_wood", 0.01))
    add(bx((w + 0.3, d + 0.3, 0.12), (0, 0, 2.4), "ny_cream", 0.02))
    add(bx((w + 0.3, 0.3, 0.2), (0, -d / 2 - 0.1, 2.25), "ny_red", 0.02))

    for x in (-1.0, 1.0):
        add(bx((0.9, 0.9, 0.05), (x, 0.0, 0.8), "ny_wood_dark", 0.01))
        add(k.prism("leg", 6, 0.05, 0.6, (x, 0, 0.2), m.c("ny_iron")))

    return done("dining")


@reg
def canopy():
    m.setup(46)
    d = 4.0
    add(bx((2.31, d, 0.18), (0, 0, 3.2), "ny_green", 0.03))
    add(bx((2.31, 0.18, 0.5), (0, -d / 2, 2.9), "ny_green_dark", 0.02))

    for x in (-1.0, 1.0):
        add(k.prism("pole", 8, 0.05, 3.2, (x, -d / 2 + 0.2, 0), m.c("ny_iron_light")))
        add(bar((x, -d / 2 + 0.2, 3.0), (x, d / 2 - 0.1, 3.2), 0.04, "ny_iron_light", 4))

    add(bx((2.2, 0.04, 0.3), (0, -d / 2 - 0.02, 3.0), "ny_cream", 0.0))
    add(bar((-1.1, d / 2, 3.18), (1.1, d / 2, 3.18), 0.04, "ny_iron_light", 4))
    add(bx((2.1, 0.1, 0.5), (0, 0, 3.55), "ny_green_dark", 0.0))

    return done("canopy")


@reg
def escape():
    m.setup(47)
    items = m.fire_escape(4.0, 2, 2.0, 0.7, z0=0.0, x=0.0, depth=1.4, ladder=True)
    add(items)
    add(bx((4.0, 0.08, 0.1), (0, 0.66, 0), "ny_iron", 0.0))

    for x in (-1.9, 1.9):
        add(bar((x, 0.66, 0.0), (x, 0.66, 4.1), 0.04, "ny_iron", 4))

    return done("escape")


@reg
def hydrant():
    m.setup(48)
    add(k.prism("base", 16, 0.2, 0.12, (0, 0, 0), m.c("ny_red_dark")))
    add(k.lathe("body", [(0, 0.12), (0.15, 0.12), (0.14, 0.55), (0.18, 0.6), (0.17, 0.65), (0.1, 0.7), (0, 0.72)], 10 * N, (0, 0, 0), m.c("ny_red")))
    add(k.prism("cap", 8, 0.08, 0.08, (0, 0, 0.72), m.c("ny_yellow")))
    add(bar((-0.25, 0, 0.42), (0.25, 0, 0.42), 0.07, "ny_red", 8))

    for sx in (-1, 1):
        add(k.prism("nut", 6, 0.065, 0.08, (sx * 0.25, 0, 0.42), m.c("ny_yellow")))
        k.rotate(m.jp.parts[-1], 90, "Y", (sx * 0.25, 0, 0.42))

    add(bar((0, -0.15, 0.42), (0, -0.25, 0.42), 0.06, "ny_red", 8))

    return done("hydrant")


@reg
def globe():
    m.setup(49)
    add(k.prism("base", 10, 0.2, 0.3, (0, 0, 0), m.c("ny_green_dark"), radius_top=0.13))
    add(k.prism("pole", 10, 0.09, 3.2, (0, 0, 0.3), m.c("ny_green"), radius_top=0.06))
    add(k.prism("collar", 10, 0.16, 0.1, (0, 0, 3.4), m.c("ny_green_dark")))
    add(k.lathe("globe", [(0, 0), (0.18, 0.04), (0.38, 0.3), (0.4, 0.5), (0.3, 0.72), (0.12, 0.82), (0, 0.84)], 12 * N, (0, 0, 3.4), m.c("ny_cream")))
    add(k.prism("top", 10, 0.1, 0.06, (0, 0, 4.2), m.c("ny_green_dark")))

    return done("globe")


@reg
def hotdog():
    m.setup(50)
    add(bx((1.5, 0.9, 0.7), (0, 0, 0.55), "ny_yellow", 0.05))
    add(bx((1.54, 0.94, 0.12), (0, 0, 1.25), "ny_iron_light", 0.02))
    add(bx((1.2, 0.7, 0.05), (-0.1, 0, 1.35), "ny_cream", 0.0))

    for sx in (-1, 1):
        add(k.prism("wheel", 10, 0.3, 0.1, (sx * 0.65, -0.52, 0.3), m.c("ny_iron")))
        k.rotate(m.jp.parts[-1], 90, "X", (sx * 0.65, -0.52, 0.3))
        add(k.prism("hub", 6, 0.08, 0.12, (sx * 0.65, -0.55, 0.3), m.c("ny_conc")))
        k.rotate(m.jp.parts[-1], 90, "X", (sx * 0.65, -0.55, 0.3))

    add(bar((0.75, 0.0, 0.55), (1.0, 0.0, 0.85), 0.04, "ny_iron", 4))
    add(bar((-0.75, 0, 1.25), (-0.75, 0, 2.2), 0.03, "ny_iron", 4))
    add(bar((0.75, 0, 1.25), (0.75, 0, 2.2), 0.03, "ny_iron", 4))
    add(bx((1.9, 1.6, 0.08), (0, -0.2, 2.2), "ny_red", 0.02))
    add(bx((1.9, 0.06, 0.2), (0, -1.0, 2.05), "ny_white", 0.0))
    add(bx((1.2, 0.6, 0.04), (0, -0.62, 0.9), "ny_iron", 0.0))

    return done("hotdog")


@reg
def mailbox():
    m.setup(51)
    add(bx((0.62, 0.55, 0.12), (0, 0, 0), "ny_iron", 0.02))
    add(bx((0.58, 0.48, 0.7), (0, 0, 0.12), "ny_navy", 0.04))
    add(k.prism("dome", 16, 0.29, 0.5, (0, 0, 0.82), m.c("ny_navy")))
    k.rotate(m.jp.parts[-1], 90, "Y", (0, 0, 0.82))
    k.scale(m.jp.parts[-1], 1, 0.82, 1, (0, 0, 0.82))
    add(bx((0.38, 0.05, 0.08), (0, -0.28, 0.95), "ny_iron", 0.0))
    add(bx((0.4, 0.05, 0.3), (0, -0.25, 0.4), "ny_cream", 0.0))
    add(bar((-0.2, -0.3, 0.9), (0.2, -0.3, 0.9), 0.02, "ny_iron_light", 6))

    for sx in (-0.24, 0.24):
        for sy in (-0.2, 0.2):
            add(k.prism("foot", 8, 0.035, 0.12, (sx, sy, 0.0), m.c("ny_iron")))

    return done("mailbox")


@reg
def can():
    m.setup(52)
    add(k.prism("can", 16, 0.3, 0.9, (0, 0, 0), m.c("ny_green_dark"), radius_top=0.33))

    for z in (0.15, 0.45, 0.75):
        add(k.prism("rib", 16, 0.335, 0.04, (0, 0, z), m.c("ny_green")))

    add(k.prism("lid", 16, 0.36, 0.07, (0, 0, 0.9), m.c("ny_iron_light"), radius_top=0.3))
    add(k.prism("hdl", 6, 0.05, 0.04, (0, 0, 0.97), m.c("ny_iron")))
    add(k.prism("mouth", 16, 0.22, 0.06, (0, 0, 1.0), m.c("ny_iron")))

    for a in range(0, 360, 90):
        x, y = 0.34 * math.cos(math.radians(a)), 0.34 * math.sin(math.radians(a))
        add(bar((x, y, 0.05), (x * 1.02, y * 1.02, 0.88), 0.02, "ny_green", 6))

    return done("can")


@reg
def newsstand():
    m.setup(53)
    w, d = 2.5, 1.65
    add(bx((w, d, 0.15), (0, 0, 0), "ny_conc_dark", 0.02))
    add(bx((w - 0.1, d - 0.1, 1.6), (0, 0, 0.15), "ny_green", 0.04))
    add(flat((w - 0.6, 0.04, 0.9), (0, -d / 2 + 0.04, 0.85), "void"))
    add(flat((w - 0.7, 0.04, 0.35), (0, -d / 2 + 0.05, 0.9), "ny_yellow"))
    add(flat((w - 0.7, 0.04, 0.3), (0, -d / 2 + 0.05, 1.3), "ny_red"))
    add(bx((w, 0.5, 0.06), (0, -d / 2 - 0.15, 1.0), "ny_wood", 0.0))
    add(bx((w + 0.3, d + 0.3, 0.2), (0, 0, 1.75), "ny_green_dark", 0.03))
    add(bx((w + 0.1, 0.1, 0.35), (0, -d / 2 - 0.1, 1.95), "ny_red", 0.02))
    add(bx((w - 0.4, d - 0.4, 0.3), (0, 0, 1.95), "ny_green", 0.04))
    r = m.rng()
    inks = ("ny_red", "ny_yellow", "ny_navy", "ny_cream", "ny_orange", "ny_green_dark")

    for row in range(2):
        for i in range(7):
            mag = bx((0.28, 0.2, 0.36), (-w / 2 + 0.3 + i * 0.32, -d / 2 - 0.05 - row * 0.2, 1.06 + row * 0.04), r.choice(inks), 0.01)
            k.rotate(mag, -14, "X", (0, -d / 2 - 0.05 - row * 0.2, 1.06))
            add(mag)

    for i in range(4):
        add(bx((0.3, 0.42, 0.06), (-0.6 + i * 0.4, -d / 2 - 0.2, 1.06 + 0.02 * (i % 2)), r.choice(inks), 0.01))

    return done("newsstand")


@reg
def wallad():
    m.setup(54)
    add(bx((4.0, 0.08, 6.0), (0, 0, 0), "ny_cream", 0.0))
    add(flat((3.8, 0.03, 1.8), (0, -0.05, 4.0), "ny_red"))
    add(flat((3.8, 0.03, 1.8), (0, -0.05, 1.9), "ny_navy"))
    add(flat((2.4, 0.03, 0.5), (0, -0.07, 4.6), "ny_cream"))
    add(flat((1.6, 0.03, 0.4), (0, -0.07, 2.5), "ny_yellow"))
    add(flat((0.6, 0.03, 1.0), (-1.4, -0.07, 0.4), "ny_orange"))
    add(flat((2.0, 0.03, 0.35), (0.5, -0.07, 0.7), "ny_green"))

    return done("wallad")


@reg
def bench():
    m.setup(55)

    for sx in (-0.75, 0.75):
        add(bx((0.1, 0.6, 0.45), (sx, 0, 0), "ny_iron", 0.0))
        add(bar((sx, 0.2, 0.4), (sx, 0.3, 0.92), 0.035, "ny_iron", 4))

    for i in range(4):
        add(bx((1.8, 0.12, 0.05), (0, -0.25 + i * 0.14, 0.45), "ny_wood", 0.01))

    for i in range(3):
        add(bx((1.8, 0.04, 0.12), (0, 0.3, 0.55 + i * 0.16), "ny_wood", 0.0))

    add(bx((0.12, 0.65, 0.05), (-0.85, 0, 0.62), "ny_iron", 0.0))
    add(bx((0.12, 0.65, 0.05), (0.85, 0, 0.62), "ny_iron", 0.0))

    return done("bench")


@reg
def barricade():
    m.setup(56)

    for sx in (-1.0, 1.0):
        add(bar((sx, -0.3, 0.0), (sx, 0, 1.0), 0.04, "ny_iron_light", 4))
        add(bar((sx, 0.3, 0.0), (sx, 0, 1.0), 0.04, "ny_iron_light", 4))

    add(bx((2.4, 0.06, 0.28), (0, 0, 0.62), "ny_orange", 0.01))
    add(bx((2.4, 0.06, 0.28), (0, 0, 0.9), "ny_white", 0.01))

    for i in range(6):
        add(flat((0.12, 0.08, 0.28), (-1.0 + i * 0.4, -0.01, 0.62), "ny_white"))

    for sx in (-1.0, 1.0):
        add(bx((0.14, 0.7, 0.05), (sx, 0, 0), "ny_iron", 0.0))

    return done("barricade")


@reg
def sign():
    m.setup(57)
    add(bx((0.1, 0.9, 0.08), (0, 0, 2.1), "ny_iron", 0.0))
    add(bar((0, 0.45, 2.1), (0, 0.45, 2.4), 0.03, "ny_iron", 4))
    add(bx((0.07, 0.9, 0.7), (0, 0.0, 1.5), "ny_navy", 0.02))
    add(flat((0.02, 0.7, 0.3), (-0.045, 0.0, 1.85), "ny_cream"))
    add(flat((0.02, 0.5, 0.18), (-0.045, 0.0, 1.65), "ny_cream"))
    add(flat((0.02, 0.7, 0.3), (0.045, 0.0, 1.85), "ny_cream"))

    for yy in (-0.38, 0.38):
        add(bar((0, yy, 2.1), (0, yy, 1.4 + 0.7), 0.01, "ny_iron", 4))

    add(bx((0.12, 0.08, 0.3), (0, 0.5, 2.15), "ny_iron", 0.0))

    return done("sign")


@reg
def ac():
    m.setup(58)
    add(bx((1.5, 1.3, 0.8), (0, 0, 0.18), "ny_conc", 0.05))
    add(bx((1.6, 1.4, 0.18), (0, 0, 0.0), "ny_iron", 0.02))
    add(k.prism("fan", 10 * N // 2, 0.4, 0.08, (-0.3, 0, 0.98), m.c("ny_iron")))
    add(k.prism("hub", 6, 0.08, 0.1, (-0.3, 0, 0.98), m.c("ny_iron_light")))

    for i in range(4):
        add(flat((0.6, 0.03, 0.04), (0.4, -0.66, 0.35 + i * 0.12), "ny_iron_light"))

    add(bx((0.4, 0.5, 0.06), (0.5, 0.0, 0.98), "ny_conc_dark", 0.01))
    add(bar((-0.7, 0.66, 0.2), (-0.7, 0.66, 0.9), 0.03, "ny_iron_light", 4))

    return done("ac")


@reg
def billboard():
    m.setup(59)
    w, h = 7.44, 3.0
    add(bx((w, 0.3, h), (0, 0, 2.7), "ny_iron", 0.03))
    add(flat((w - 0.4, 0.04, h - 0.4), (0, -0.17, 2.9), "ny_cream"))
    add(flat((w - 0.8, 0.03, 1.0), (0, -0.2, 4.5), "ny_red"))
    add(flat((3.5, 0.03, 0.8), (-1.5, -0.2, 3.4), "ny_navy"))
    add(flat((2.2, 0.03, 0.8), (2.2, -0.2, 3.3), "ny_yellow"))
    add(bx((w + 0.2, 0.9, 0.1), (0, -0.4, 5.7), "ny_iron", 0.0))

    for x in (-2.8, 0, 2.8):
        add(bar((x, -0.4, 5.75), (x, -0.9, 5.95), 0.04, "ny_iron_light", 4))
        add(k.prism("lamp", 6, 0.12, 0.1, (x, -0.95, 5.9), m.c("ny_iron_light")))

    for x in (-2.8, 2.8):
        add(bx((0.3, 0.3, 2.7), (x, 0.0, 0.0), "ny_iron", 0.02))
        add(bar((x, 0.1, 0.1), (x, 0.9, 0.0), 0.05, "ny_iron", 4))

    add(bx((w - 0.5, 0.9, 0.08), (0, -0.4, 2.65), "ny_iron", 0.0))

    return done("billboard")


@reg
def watertower():
    m.setup(60)
    add(m.watertank((0, 0, 0), 1.0))

    for lx in (-1, 1):
        add(bar((lx * 0.7, -0.7 * lx, 0.9), (-lx * 0.7, 0.7 * lx, 1.8), 0.025, "ny_iron", 4))

    return done("watertower")


@reg
def scaffold():
    m.setup(61)
    w, d, lv = 4.0, 2.0, 3
    xs = (-w / 2 + 0.05, w / 2 - 0.05)
    ys = (-d / 2 + 0.05, d / 2 - 0.05)

    for x in xs:
        for y in ys:
            add(bar((x, y, 0), (x, y, 3.0), 0.045, "ny_iron_light", 4))

    for i in range(lv):
        z = i * 1.5

        for y in ys:
            add(bar((xs[0], y, z), (xs[1], y, z), 0.035, "ny_iron_light", 4))

        for x in xs:
            add(bar((x, ys[0], z), (x, ys[1], z), 0.035, "ny_iron_light", 4))

    for z in (1.5, 3.0):
        add(bx((w, d, 0.06), (0, 0, z - 0.06), "ny_wood", 0.0))

    add(bar((xs[0], ys[0], 0), (xs[1], ys[0], 1.5), 0.03, "ny_iron_light", 4))
    add(bar((xs[1], ys[0], 1.5), (xs[0], ys[0], 3.0), 0.03, "ny_iron_light", 4))

    add(flat((w, 0.03, 0.9), (0, ys[0], 2.1), "ny_green"))

    return done("scaffold")


@reg
def awning():
    m.setup(62)
    add(m.striped_awning(4.0, 1.0, "ny_red", "ny_white", slope=22, valance=0.3))
    add(bar((-2.0, 0.0, 0.05), (2.0, 0.0, 0.05), 0.04, "ny_iron", 4))

    return done("awning")


@reg
def bollard():
    m.setup(63)
    add(k.prism("b", 16, 0.16, 0.9, (0, 0, 0), m.c("ny_iron_light")))
    add(k.lathe("cap", [(0, 0), (0.18, 0), (0.18, 0.04), (0.12, 0.12), (0, 0.15)], 16, (0, 0, 0.9), m.c("ny_iron")))
    add(k.prism("band", 16, 0.165, 0.1, (0, 0, 0.45), m.c("ny_yellow")))
    add(k.prism("foot", 16, 0.22, 0.05, (0, 0, 0), m.c("ny_conc_dark")))

    return done("bollard")


@reg
def steam():
    m.setup(64)
    add(k.prism("base", 16, 0.34, 0.2, (0, 0, 0), m.c("ny_conc_dark")))
    add(k.prism("stack", 16, 0.3, 2.4, (0, 0, 0.2), m.c("ny_orange"), radius_top=0.24))

    for z in (0.7, 1.4, 2.1):
        add(k.prism("band", 16, 0.31, 0.12, (0, 0, z), m.c("ny_white")))

    add(k.prism("top", 16, 0.34, 0.1, (0, 0, 2.6), m.c("ny_conc_dark"), radius_top=0.18))
    add(k.prism("tip", 16, 0.2, 0.3, (0, 0, 2.7), m.c("ny_orange"), radius_top=0.2))

    return done("steam")


@reg
def lamp():
    m.setup(65)
    add(k.prism("base", 10, 0.22, 0.35, (0, 0, 0), m.c("ny_green_dark"), radius_top=0.14))
    add(k.prism("pole", 10, 0.1, 5.2, (0, 0, 0.35), m.c("ny_green"), radius_top=0.07))

    for sx in (-1, 1):
        add(bar((0, 0, 5.4), (sx * 1.1, 0, 5.95), 0.05, "ny_green", 6))
        add(bx((0.8, 0.28, 0.12), (sx * 1.2, 0, 5.8), "ny_iron", 0.02))
        add(bx((0.55, 0.2, 0.05), (sx * 1.22, 0, 5.77), "ny_cream", 0.0))

    add(k.prism("cap", 10, 0.14, 0.12, (0, 0, 5.5), m.c("ny_green_dark")))

    return done("lamp")


@reg
def tree():
    m.setup(66)
    add(k.prism("trunk", 8, 0.17, 2.6, (0, 0, 0), m.c("ny_wood_dark"), radius_top=0.1))
    add(bar((0, 0, 2.0), (0.7, 0.2, 3.1), 0.06, "ny_wood_dark", 6))
    add(bar((0, 0, 2.2), (-0.6, -0.3, 3.3), 0.06, "ny_wood_dark", 6))
    add(k.prism("grate", 8, 0.55, 0.04, (0, 0, 0), m.c("ny_iron")))
    add(blob((0, 0, 4.3), 1.45, "ny_leaf", 0.9, 0.12, 1, 2))
    add(blob((0.75, 0.4, 3.6), 0.95, "ny_leaf_dark", 0.85, 0.15, 2, 1))
    add(blob((-0.75, -0.3, 3.7), 0.95, "ny_leaf_dark", 0.85, 0.15, 3, 1))
    add(blob((0.2, -0.5, 5.0), 0.8, "ny_leaf_light", 0.85, 0.15, 4, 1))
    add(blob((-0.3, 0.5, 5.1), 0.7, "ny_leaf_light", 0.85, 0.15, 5, 1))

    return done("tree")


@reg
def theatersign():
    m.setup(67)
    add(bx((0.22, 0.3, 5.0), (0, 0.4, 0.5), "ny_red_dark", 0.04))
    add(bx((1.9, 0.3, 0.4), (0, 0.3, 5.4), "ny_navy", 0.03))
    add(flat((1.6, 0.03, 0.16), (0, 0.14, 5.52), "ny_cream"))

    for i in range(7):
        add(flat((0.55, 0.04, 0.5), (0.0, 0.24, 0.8 + i * 0.6), "ny_cream"))

    for i in range(10):
        add(k.prism("bulb", 6, 0.06, 0.06, (-0.85, 0.3, 0.6 + i * 0.5), m.c("ny_yellow")))

    add(bar((0, 0.4, 0.5), (0, 0.4, 0.2), 0.05, "ny_iron", 4))

    return done("theatersign")


@reg
def cone():
    m.setup(68)
    add(bx((0.56, 0.56, 0.05), (0, 0, 0), "ny_iron", 0.01))
    add(k.prism("c", 10 * N // 2, 0.21, 0.6, (0, 0, 0.05), m.c("ny_orange"), radius_top=0.05))
    add(k.prism("band", 10 * N // 2, 0.14, 0.14, (0, 0, 0.27), m.c("ny_white"), radius_top=0.11))

    return done("cone")


@reg
def light():
    m.setup(69)
    add(k.prism("base", 10, 0.2, 0.3, (0, 0, 0), m.c("ny_yellow"), radius_top=0.13))
    add(k.prism("pole", 10, 0.1, 4.6, (0, 0, 0.3), m.c("ny_yellow"), radius_top=0.08))
    add(bar((0, 0, 4.5), (1.3, 0, 4.9), 0.07, "ny_yellow", 8))
    add(bx((0.32, 0.3, 0.95), (1.2, 0, 4.1), "ny_iron", 0.04))

    for i, col in enumerate(("ny_red", "ny_yellow", "ny_green")):
        add(k.prism("lens", 8, 0.1, 0.05, (1.2, -0.17, 4.2 + i * 0.3), m.c(col)))
        k.rotate(m.jp.parts[-1], 90, "X", (1.2, -0.17, 4.2 + i * 0.3))

    add(bx((0.48, 0.07, 0.95), (-0.9, 0, 4.5), "ny_green", 0.01))
    add(bx((1.4, 0.06, 0.3), (-0.8, 0.0, 4.9), "ny_green", 0.01))
    add(flat((1.2, 0.02, 0.12), (-0.8, -0.04, 4.99), "ny_cream"))

    return done("light")


@reg
def pallet():
    m.setup(70)

    for i in range(3):
        add(bx((0.14, 1.2, 0.09), (-0.5 + i * 0.5, 0, 0.0), "ny_wood", 0.0))

    for i in range(5):
        add(bx((0.18, 1.2, 0.03), (-0.5 + i * 0.25, 0, 0.09), "ny_wood", 0.0))


    return done("pallet")


@reg
def palletload():
    m.setup(71)
    add(bx((1.04, 0.84, 0.12), (0, 0, 0.0), "ny_wood", 0.01))
    add(bx((1.0, 0.8, 1.0), (0, 0, 0.12), "ny_cream", 0.04))

    for z in (0.35, 0.7):
        add(bx((1.02, 0.82, 0.05), (0, 0, z), "ny_white", 0.0))

    add(bx((0.9, 0.04, 0.3), (0, -0.41, 0.6), "ny_orange", 0.0))
    add(flat((0.6, 0.02, 0.12), (0.0, -0.43, 0.82), "ny_iron"))

    return done("palletload")


@reg
def crates():
    m.setup(72)
    add(bx((0.75, 0.75, 0.45), (-0.38, 0.0, 0.0), "ny_wood", 0.03))
    add(bx((0.75, 0.75, 0.45), (0.38, 0.0, 0.0), "ny_wood_dark", 0.03))
    add(bx((0.7, 0.7, 0.45), (0.0, 0.0, 0.45), "ny_wood", 0.03))

    for x in (-0.38, 0.38):
        add(flat((0.77, 0.04, 0.08), (x, -0.38, 0.18), "ny_wood_dark"))


    return done("crates")


@reg
def chainlink():
    m.setup(73)
    w = 4.0

    for x in (-w / 2 + 0.04, 0, w / 2 - 0.04):
        add(k.prism("post", 8, 0.04, 1.75, (x, 0, 0), m.c("ny_iron_light")))

    add(bar((-w / 2, 0, 1.7), (w / 2, 0, 1.7), 0.025, "ny_iron_light", 4))
    add(bar((-w / 2, 0, 0.05), (w / 2, 0, 0.05), 0.02, "ny_iron_light", 4))
    add(flat((w - 0.1, 0.01, 1.6), (0, 0, 0.08), "ny_conc"))

    return done("chainlink")


@reg
def hvac():
    m.setup(74)
    add(bx((1.04, 0.99, 0.12), (0, 0, 0), "ny_conc_dark", 0.02))
    add(bx((0.98, 0.93, 0.8), (0, 0, 0.12), "ny_conc", 0.05))
    add(k.prism("fan", 16, 0.36, 0.06, (0, 0, 0.93), m.c("ny_iron")))
    add(k.prism("hub", 6, 0.07, 0.1, (0, 0, 0.93), m.c("ny_iron_light")))

    for i in range(5):
        add(flat((0.6, 0.02, 0.04), (0, -0.48, 0.25 + i * 0.1), "ny_iron_light"))


    return done("hvac")


@reg
def generator():
    m.setup(75)
    add(bx((4.0, 2.0, 0.15), (0, 0, 0), "ny_conc_dark", 0.02))
    add(bx((3.8, 1.8, 2.0), (0, 0, 0.15), "ny_green", 0.06))
    add(bx((3.9, 1.9, 0.12), (0, 0, 2.15), "ny_green_dark", 0.03))

    for i in range(6):
        add(flat((0.5, 0.03, 0.6), (-1.5 + i * 0.6, -0.92, 0.5), "ny_green_dark"))

    add(flat((0.9, 0.03, 0.6), (1.3, -0.93, 1.2), "ny_yellow"))
    add(k.prism("stack", 10 * N // 2, 0.12, 1.3, (-1.4, 0.4, 2.2), m.c("ny_iron")))
    add(k.prism("cap", 10 * N // 2, 0.2, 0.06, (-1.4, 0.4, 3.5), m.c("ny_iron_light"), radius_top=0.14))
    add(bx((0.5, 0.4, 0.4), (1.5, 0.3, 2.27), "ny_iron_light", 0.02))

    return done("generator")


@reg
def drum():
    m.setup(76)
    add(k.prism("d", 16, 0.29, 0.9, (0, 0, 0), m.c("ny_navy")))

    for z in (0.02, 0.45, 0.86):
        add(k.prism("rib", 16, 0.305, 0.05, (0, 0, z), m.c("ny_iron_light")))

    add(k.prism("lid", 16, 0.27, 0.03, (0, 0, 0.9), m.c("ny_iron")))
    add(k.prism("bung", 6, 0.05, 0.04, (0.12, 0.0, 0.93), m.c("ny_yellow")))

    return done("drum")


@reg
def picnic():
    m.setup(77)
    add(bx((1.8, 0.75, 0.07), (0, 0, 0.72), "ny_wood", 0.0))

    for sy in (-0.755 + 0.17, 0.755 - 0.17):
        add(bx((1.8, 0.28, 0.06), (0, sy, 0.42), "ny_wood", 0.0))

    for sx in (-0.65, 0.65):
        add(bar((sx, -0.3, 0.0), (sx, -0.05, 0.72), 0.045, "ny_wood_dark", 4))
        add(bar((sx, 0.3, 0.0), (sx, 0.05, 0.72), 0.045, "ny_wood_dark", 4))
        add(bx((0.1, 1.5, 0.08), (sx, 0, 0.0), "ny_wood_dark", 0.0))

    return done("picnic")


@reg
def stall():
    m.setup(78)

    for x in (-1.4, 1.4):
        for y in (-1.4, 1.4):
            add(bar((x, y, 0), (x, y, 2.6), 0.04, "ny_iron_light", 6))

    n = 12

    for i in range(n):
        col = "ny_red" if i % 2 == 0 else "ny_white"
        add(bx((3.0 / n, 3.0, 0.06), (-1.5 + 3.0 / n * (i + 0.5), 0, 2.6 + 0.0), col, 0.0))

    for sy in (-1, 1):
        for i in range(n):
            col = "ny_red" if i % 2 == 0 else "ny_white"
            add(flat((3.0 / n, 0.04, 0.3), (-1.5 + 3.0 / n * (i + 0.5), sy * 1.5, 2.3), col))

    add(bx((3.0, 0.6, 0.06), (0, -1.0, 0.9), "ny_wood", 0.0))
    add(bx((2.8, 0.6, 0.9), (0, -1.0, 0.0), "ny_navy", 0.02))
    add(bar((-1.4, -1.4, 2.6), (0, 0, 3.0), 0.03, "ny_iron_light", 4))
    add(bar((1.4, -1.4, 2.6), (0, 0, 3.0), 0.03, "ny_iron_light", 4))
    add(bar((-1.4, 1.4, 2.6), (0, 0, 3.0), 0.03, "ny_iron_light", 4))
    add(bar((1.4, 1.4, 2.6), (0, 0, 3.0), 0.03, "ny_iron_light", 4))

    return done("stall")


@reg
def planterbox():
    m.setup(79)
    add(bx((1.0, 1.0, 0.55), (0, 0, 0), "ny_conc", 0.04))
    add(bx((1.08, 1.08, 0.1), (0, 0, 0.55), "ny_conc_dark", 0.02))
    add(bx((0.8, 0.8, 0.05), (0, 0, 0.6), "ny_wood_dark", 0.0))
    add(blob((0, 0, 0.8), 0.38, "ny_leaf", 0.9, 0.15, 6, 1))
    add(blob((0.2, 0.15, 0.95), 0.25, "ny_leaf_light", 0.9, 0.15, 7, 1))
    add(blob((-0.2, -0.1, 0.85), 0.22, "ny_leaf_dark", 0.9, 0.15, 8, 1))

    return done("planterbox")


@reg
def hoop():
    m.setup(80)
    add(k.prism("base", 8, 0.2, 0.15, (0, 0, 0), m.c("ny_conc_dark")))
    add(k.prism("pole", 8, 0.07, 3.0, (0, 0, 0.15), m.c("ny_iron_light")))
    add(bar((0, 0, 2.9), (0, -0.65, 3.0), 0.05, "ny_iron_light", 6))
    add(bx((1.15, 0.05, 0.75), (0, -0.7, 2.9), "ny_white", 0.01))
    add(flat((0.5, 0.02, 0.4), (0, -0.74, 3.0), "ny_red"))
    ring = [bar((0.22 * math.cos(2 * math.pi * i / 8), -0.8 + 0.22 * math.sin(2 * math.pi * i / 8), 2.88), (0.22 * math.cos(2 * math.pi * (i + 1) / 8), -0.8 + 0.22 * math.sin(2 * math.pi * (i + 1) / 8), 2.88), 0.02, "ny_orange", 4) for i in range(8)]
    add(ring)
    add(k.prism("net", 8, 0.2, 0.35, (0, -0.8, 2.55), m.c("ny_white"), radius_top=0.1))

    return done("hoop")
