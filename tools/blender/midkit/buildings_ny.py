import masonry as mm
import towers as tw
import common as m
from common import add, bx, flat, place, solid, k

ALL = {}


def reg(fn):
    ALL[fn.__name__] = fn

    return fn


@reg
def tenement():
    return mm.masonry("tenement", 8, 9.2, 23, gh=4.2, cols=3, ground="storedoor", fire=True, awning=("ny_red", "ny_white"), seed=11, side_cols=2, door_x=2.2)


@reg
def cornerten():
    return mm.masonry("cornerten", 8.6, 13.2, 20, gh=4.2, cols=3, color="ny_brick_dark", ground="storedoor", fire=True, awning=("ny_green", "ny_cream"), seed=12, side_cols=4, ground_side="store", corner=True, tank=True)


@reg
def brownstone():
    return mm.masonry("brownstone", 8, 8, 17, gh=3.8, cols=3, color="ny_brown", trim="ny_brown_dark", ground="none", stoop_rise=1.2, seed=13, side_cols=2, roof=2, win=(1.1, 2.0))


@reg
def walkup():
    return mm.masonry("walkup", 4, 9.37, 13, gh=3.4, cols=1, color="ny_brick_light", ground="door", seed=14, side_cols=3, win=(1.1, 1.8), roof=1, fire=True)


@reg
def prewar():
    return mm.masonry("prewar", 16, 12, 41, gh=5.0, cols=5, color="ny_tan", trim="ny_lime_light", ground="door", seed=15, side_cols=2, back_cols=3, roof=4, tank=True, win=(1.3, 2.0))


@reg
def loft():
    return mm.masonry("loft", 12, 8.95, 20, gh=4.4, cols=4, color="ny_conc", trim="ny_iron_light", ground="store", seed=16, side_cols=2, roof=3, win=(2.2, 2.6), tank=True, fire=True)


@reg
def dept():
    def extra(bw, bd, gh, fh, n):
        place(m.striped_awning(bw - 1.0, 1.4, "ny_navy", "ny_cream", n=int((bw - 1) / 0.5)), 0, -bd / 2, gh - 0.5, 0)
        place(m.sign_box(7.0, 0.9, "ny_navy", "ny_cream"), 0, -bd / 2 - 0.1, gh + 0.5, 0)

    return mm.masonry("dept", 16, 12.75, 23, gh=5.0, cols=7, color="ny_lime", trim="ny_lime_light", ground="store", seed=17, side_cols=4, roof=4, win=(1.5, 2.0), extra=extra)


@reg
def school():
    def extra(bw, bd, gh, fh, n):
        place(m.glazed_door(2.4, 2.8), 0, -bd / 2 + 0.01, 0.4, 0)
        place(m.sign_box(5.0, 0.6, "ny_brick_dark", "ny_cream", letters=10), 0, -bd / 2 - 0.1, gh + 0.4, 0)

    return mm.masonry("school", 20, 12, 13.2, gh=4.4, cols=9, color="ny_brick_light", trim="ny_lime_light", ground="windows", seed=18, side_cols=3, roof=3, win=(1.3, 1.9), extra=extra, parap=0.9)


@reg
def bank():
    def extra(bw, bd, gh, fh, n):
        for x in (-3.6, -1.2, 1.2, 3.6):
            add(k.prism("col", 12 * m.N, 0.42, gh - 0.5, (x, -bd / 2 - 1.6, 0.5), m.c("ny_lime_light")))
            add(bx((1.0, 1.0, 0.3), (x, -bd / 2 - 1.6, 0.35), "ny_lime", 0.03))
            add(bx((1.0, 1.0, 0.35), (x, -bd / 2 - 1.6, gh - 0.1), "ny_lime", 0.03))

        add(bx((bw * 0.78, 2.4, 0.9), (0, -bd / 2 - 1.2, gh + 0.25), "ny_lime_light", 0.05))
        add(bx((bw * 0.78 + 0.6, 3.0, 0.3), (0, -bd / 2 - 1.0, gh + 1.15), "ny_lime", 0.04))

        for i in range(4):
            add(bx((bw * 0.78 + 1.6 - i * 0.3, 0.45, 0.2), (0, -bd / 2 - 3.1 + i * 0.4, 0.2 * (3 - i) - 0.2 + 0.2), "ny_lime", 0.02))

        solid(-bw * 0.4, -bd / 2 - 2.5, bw * 0.4, -bd / 2, -0.5, gh + 1.0)

    return mm.masonry("bank", 12, 12, 10.2, gh=5.4, cols=3, color="ny_lime", trim="ny_lime_light", ground="windows", seed=19, side_cols=3, roof=2, win=(1.2, 2.2), extra=extra, parap=0.9)


@reg
def repair():
    m.setup(20)
    w, d = 12, 8
    bw, bd = w - 0.4, d - 0.4
    m.plinth(bw, bd, 0.3)
    m.storey(bw, bd, 0, 5.0, "ny_brick",
             front=[("garage", -3.0, 0, 2.8, 2.9, {}), ("garage", 0.4, 0, 2.8, 2.9, {}), ("door", 3.8, 0.1, 1.2, 2.4, {}), ("lite", 4.9, 2.0, 0.9, 0.9, {})],
             back=[("louver", -2, 1.2, 2.0, 1.2, {}), ("door", 3, 0.1, 1.2, 2.4, {})], left=[("lite", x, 2.0, 1.0, 1.0, {}) for x in (-1.5, 1.5)], right=[("lite", x, 2.0, 1.0, 1.0, {}) for x in (-1.5, 1.5)])
    m.band(bw, bd, 4.8, "ny_conc", 0.3, 0.08)
    m.parapet(bw, bd, 5.1, 1.1, "ny_brick_dark", "ny_conc")
    place(m.sign_box(5.2, 0.75, "ny_yellow", "ny_iron", letters=8), 0, -bd / 2 - 0.05, 3.3, 0)
    m.roof_gear(bw, bd, 6.0, 2)
    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, 6.2)

    return m.finish("repair")


@reg
def firehouse():
    m.setup(21)
    w, d = 8, 8
    bw, bd = w - 0.4, d - 0.4
    m.plinth(bw, bd, 0.3)
    m.storey(bw, bd, 0, 4.2, "ny_brick_dark", front=[("garage", 0, 0, 3.8, 3.6, {"color": "ny_red"})], back=[("door", 0, 0.1, 1.2, 2.4, {})], left=[("lite", 0, 2.0, 1.0, 1.0, {})], right=[("lite", 0, 2.0, 1.0, 1.0, {})])
    m.storey(bw, bd, 4.2, 2.4, "ny_brick", front=[("sash", x, 0.5, 1.0, 1.5, {}) for x in (-2.2, 0, 2.2)], back=[("lite", x, 0.5, 1.0, 1.5, {}) for x in (-1.5, 1.5)], left=[("lite", 0, 0.5, 1.0, 1.5, {})], right=[("lite", 0, 0.5, 1.0, 1.5, {})])
    m.band(bw, bd, 4.1, "ny_lime", 0.3, 0.1)
    m.cornice(bw, bd, 6.5, "ny_lime", 0.5, 0.3)
    m.parapet(bw, bd, 6.7, 0.3, "ny_brick", "ny_lime")
    place(m.sign_box(3.2, 0.55, "ny_red", "ny_cream", letters=7), 0, -bd / 2 - 0.05, 3.6, 0)
    m.roof_gear(bw, bd, 6.9, 1)
    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, 7.0)

    return m.finish("firehouse")


@reg
def cornershop():
    return mm.masonry("cornershop", 8.85, 8.85, 7, gh=3.8, cols=2, color="ny_brick_light", trim="ny_lime_light", ground="storedoor", seed=22, side_cols=2, ground_side="store", awning=("ny_green", "ny_cream"), roof=2, parap=0.6, win=(1.1, 1.3), door_x=2.0)


@reg
def shoprow():
    m.setup(23)
    w, d = 12, 8.92
    bw, bd = w - 0.4, d - 0.4
    m.plinth(bw, bd, 0.2)
    m.storey(bw, bd, 0, 3.6, "ny_tan", front=[("store", -4.0 + i * 4.0, 0.3, 3.4, 2.5, {"bays": 2}) for i in range(3)], back=[("louver", x, 0.8, 1.5, 1.4, {}) for x in (-3.5, 0, 3.5)], left=[("lite", 0, 1.0, 1.1, 1.3, {})], right=[("lite", 0, 1.0, 1.1, 1.3, {})])
    m.band(bw, bd, 3.5, "ny_lime", 0.26, 0.1)
    m.parapet(bw, bd, 3.7, 0.9, "ny_tan_dark", "ny_lime")

    for i, (a, b) in enumerate((("ny_red", "ny_white"), ("ny_green", "ny_cream"), ("ny_navy", "ny_cream"))):
        place(m.striped_awning(3.3, 1.2, a, b), -4.0 + i * 4.0, -bd / 2, 2.9, 0)
        place(m.sign_box(2.6, 0.45, a, "ny_cream"), -4.0 + i * 4.0, -bd / 2 - 0.05, 3.3, 0)

    m.roof_gear(bw, bd, 3.8, 2)
    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, 4.66)

    return m.finish("shoprow")


@reg
def diner():
    m.setup(24)
    w, d = 8, 4
    bw, bd = w - 0.3, d - 0.3
    add(bx((bw, bd, 0.4), (0, 0, 0), "ny_conc_dark", 0.03))
    add(bx((bw, bd, 0.9), (0, 0, 0.4), "ny_red", 0.04))
    add(bx((bw + 0.2, bd + 0.2, 0.18), (0, 0, 3.3), "ny_iron_light", 0.03))
    add(bx((bw - 0.3, bd - 0.3, 0.5), (0, 0, 3.45), "ny_cream", 0.04))
    add(bx((bw + 0.3, bd + 0.3, 0.12), (0, 0, 3.95), "ny_red", 0.03))
    add(flat((bw - 0.2, bd - 0.2, 0.1), (0, 0, 4.07), "ny_tar"))

    for sy, fac in ((-1, 0), (1, 180)):
        place(tw.ribs(bw, 1.3, 3.3, 2.0, 1.45, "ny_iron_light", "ny_cream", 0.12, 0.05, 0.12, lit=0.0), 0, sy * bd / 2, 0, fac)

    for sx, fac in ((-1, -90), (1, 90)):
        place(tw.ribs(bd - 0.2, 1.3, 3.3, 2.0, 1.4, "ny_iron_light", "ny_cream", 0.12, 0.05, 0.12, lit=0.0), sx * bw / 2, 0, 0, fac)

    place(m.glazed_door(1.2, 2.2), 2.3, -bd / 2 + 0.02, 0.4, 0)
    place(m.striped_awning(5.0, 0.9, "ny_red", "ny_white", slope=14), -1.0, -bd / 2 - 0.1, 3.2, 0)
    place(m.sign_box(1.8, 0.8, "ny_navy", "ny_yellow", letters=4), 0, 0, 4.15, 0)
    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, 4.2)

    return m.finish("diner")


@reg
def subway():
    m.setup(25)
    w = 3.6
    add(bx((w, w, 0.25), (0, 0, 0), "ny_conc_dark", 0.02))

    for sx, sy, lx, ly in ((0, -w / 2 + 0.2, w, 0.4), (-w / 2 + 0.2, 0, 0.4, w - 0.8), (w / 2 - 0.2, 0, 0.4, w - 0.8), (0, w / 2 - 0.2, w, 0.4)):
        add(bx((lx, ly, 1.1), (sx, sy, 0.25), "ny_green_dark", 0.04))
        add(bx((lx + 0.1, ly + 0.1, 0.12), (sx, sy, 1.35), "ny_green", 0.02))

    for i in range(5):
        add(bx((w - 0.9, 0.3, 0.1), (0, -0.6 + i * 0.3, 0.16 - i * 0.02), "ny_conc", 0.01))

    for sx in (-1, 1):
        add(k.prism("post", 8, 0.07, 3.4, (sx * (w / 2 - 0.2), -w / 2 + 0.2, 1.4), m.c("ny_green")))
        add(k.lathe("globe", [(0, 0), (0.22, 0.05), (0.3, 0.3), (0.2, 0.55), (0.05, 0.62), (0, 0.62)], 10 * m.N, (sx * (w / 2 - 0.2), -w / 2 + 0.2, 4.7), m.c("ny_cream")))

    add(bx((w - 0.8, 0.14, 0.7), (0, -w / 2 + 0.2, 3.9), "ny_green", 0.02))
    add(flat((w - 1.0, 0.04, 0.5), (0, -w / 2 + 0.1, 4.0), "ny_cream"))
    solid(-w / 2, -w / 2, w / 2, -w / 2 + 0.4, -0.5, 1.5)
    solid(-w / 2, -w / 2, -w / 2 + 0.4, w / 2, -0.5, 1.5)
    solid(w / 2 - 0.4, -w / 2, w / 2, w / 2, -0.5, 1.5)
    solid(-w / 2, w / 2 - 0.4, w / 2, w / 2, -0.5, 1.5)

    return m.finish("subway")


def towerize(w, d, tiers, floor_h, bay, seed, color, pier, spandrel, **o):
    m.setup(seed)
    z = 0.0
    ground = 5.0

    for z1, inset in tiers:
        t_w, t_d = w - 2 * inset, d - 2 * inset

        if z == 0.0:
            m.plinth(t_w, t_d, 0.4)
            add(bx((t_w, t_d, ground), (0, 0, 0.0), "ny_conc_dark", 0.04))
            m.storey(t_w - 0.4, t_d - 0.4, 0, ground, "ny_conc_dark", front=[("store", 0, 0.4, t_w - 1.6, ground - 1.0, {"bays": max(3, int(t_w / 2.4))})],
                     back=[("louver", -t_w * 0.25, 0.6, 1.6, 1.6, {})], left=[("louver", 0, 0.6, 1.6, 1.6, {})], right=[("louver", 0, 0.6, 1.6, 1.6, {})])
            tw.tier(t_w, t_d, ground, z1, floor_h, bay, color=color, pier=pier, spandrel=spandrel, **o)
        else:
            tw.tier(t_w, t_d, z, z1, floor_h, bay, color=color, pier=pier, spandrel=spandrel, **o)

        m.cornice(t_w, t_d, z1 - 0.05, pier, 0.5, 0.3)
        z = z1

    return z


@reg
def deco():
    towerize(16, 16, [(18, 0.3), (34, 1.8), (46, 3.4), (52, 4.8)], 3.4, 3.2, 31, "ny_lime", "ny_lime_light", "ny_lime_dark", pier_w=0.7, sp_h=1.1, out=0.35, lit=0.1)
    w = 16 - 2 * 4.8

    for i in range(4):
        s = w - i * 1.5
        add(bx((s, s, 1.8), (0, 0, 52 + i * 1.8), "ny_lime_light" if i % 2 == 0 else "ny_lime", 0.06))

    add(k.prism("mast", 8, 0.18, 7.0, (0, 0, 59.2), m.c("ny_iron_light"), radius_top=0.04))

    for z, inset in ((18, 0.3), (34, 1.8), (46, 3.4)):
        ww = 16 - 2 * inset
        m.roof_gear(ww, ww, z, 2, False, int(z))

    solid(-7.7, -7.7, 7.7, 7.7, -0.5, 18)
    solid(-6.2, -6.2, 6.2, 6.2, 17.5, 34)
    solid(-4.6, -4.6, 4.6, 4.6, 33.5, 46)
    solid(-3.2, -3.2, 3.2, 3.2, 45.5, 60)

    return m.finish("deco", fuse_soft=False)


@reg
def slab():
    m.setup(32)
    w, d = 16, 12
    m.plinth(w - 0.4, d - 0.4, 0.4)
    add(bx((w - 0.4, d - 0.4, 5.0), (0, 0, 0), "ny_conc_dark", 0.04))
    m.storey(w - 0.8, d - 0.8, 0, 5.0, "ny_conc_dark", front=[("store", -2.5, 0.4, 8.0, 4.0, {"bays": 4}), ("door", 4.8, 0.4, 1.6, 2.8, {})], back=[("louver", -4, 0.6, 1.6, 1.6, {})], left=[("louver", 0, 0.6, 1.6, 1.6, {})], right=[("louver", 0, 0.6, 1.6, 1.6, {})])
    tw.tier(w - 0.4, d - 0.4, 5.0, 50.0, 3.0, 2.6, side_bay=3.0, color="ny_tan", pier="ny_tan_dark", spandrel="ny_brick", pier_w=0.4, sp_h=1.0, out=0.3, lit=0.08)
    m.parapet(w - 0.6, d - 0.6, 50.0, 0.9, "ny_tan_dark", "ny_conc")
    add(bx((5.0, 4.0, 3.2), (-3, 0, 50.1), "ny_tan_dark", 0.05))
    m.roof_gear(w, d, 50.1, 3, True)
    solid(-w / 2 + 0.2, -d / 2 + 0.2, w / 2 - 0.2, d / 2 - 0.2, -0.5, 51)

    return m.finish("slab", fuse_soft=False)


@reg
def office():
    m.setup(33)
    w = 8
    m.plinth(w - 0.4, w - 0.4, 0.4)
    add(bx((w - 0.4, w - 0.4, 4.6), (0, 0, 0), "ny_iron_light", 0.04))
    m.storey(w - 0.8, w - 0.8, 0, 4.6, "ny_iron_light", front=[("store", 0, 0.3, 6.0, 3.7, {"bays": 3, "frame": "ny_iron"})], back=[("louver", 0, 0.6, 1.6, 1.6, {})], left=[("louver", 0, 0.6, 1.6, 1.6, {})], right=[("louver", 0, 0.6, 1.6, 1.6, {})])
    tw.tier(w - 0.4, w - 0.4, 4.6, 29.0, 3.4, 1.9, color="ny_iron_light", pier="ny_conc", spandrel="ny_conc_dark", pier_w=0.22, sp_h=0.7, out=0.18, lit=0.2, glass="ny_glass", mullion=True)
    add(bx((w - 1.0, w - 1.0, 1.6), (0, 0, 29.0), "ny_conc", 0.05))
    add(bx((w - 2.2, w - 2.2, 1.4), (0, 0, 30.6), "ny_conc_dark", 0.05))
    add(k.prism("ant", 8, 0.12, 2.0, (0, 0, 30.0), m.c("ny_iron_light"), radius_top=0.03))
    m.roof_gear(w - 1, w - 1, 29.0, 2)
    solid(-w / 2 + 0.2, -w / 2 + 0.2, w / 2 - 0.2, w / 2 - 0.2, -0.5, 32.0)

    return m.finish("office", fuse_soft=False)


@reg
def garage():
    m.setup(34)
    w = d = 12
    fh = 3.9
    floors = 4
    add(bx((w - 0.4, d - 0.4, 0.3), (0, 0, 0), "ny_conc_dark", 0.02))

    def rails(z):
        add(bx((w - 0.4, 0.3, 1.0), (0, -d / 2 + 0.35, z), "ny_conc", 0.03))
        add(bx((0.3, d - 0.9, 1.0), (-w / 2 + 0.35, 0, z), "ny_conc", 0.03))
        add(bx((0.3, d - 0.9, 1.0), (w / 2 - 0.35, 0, z), "ny_conc", 0.03))
        add(bx((w - 0.4, 0.3, 1.0), (0, d / 2 - 0.35, z), "ny_conc", 0.03))

    for f in range(floors):
        z = 0.3 + f * fh
        add(bx((w - 0.4, d - 0.4, 0.35), (0, 0, z + fh - 0.35), "ny_conc", 0.03))
        rails(z + fh)

        for cx in (-w / 2 + 0.7, -2.0, 2.0, w / 2 - 0.7):
            for cy in (-d / 2 + 0.7, d / 2 - 0.7):
                add(bx((0.5, 0.5, fh - 0.35), (cx, cy, z), "ny_conc_dark", 0.02))

        add(flat((w - 1.0, 0.05, fh - 0.35), (0, d / 2 - 0.5, z), "void"))
        add(flat((0.05, d - 1.0, fh - 0.35), (-w / 2 + 0.5, 0, z), "void"))
        add(flat((0.05, d - 1.0, fh - 0.35), (w / 2 - 0.5, 0, z), "void"))

    add(bx((4.0, 3.0, 2.6), (3.5, 3.0, 0.3 + floors * fh), "ny_conc_dark", 0.04))
    place(m.sign_box(3.0, 0.9, "ny_navy", "ny_cream", letters=1), 3.0, -d / 2 - 0.1, 2.2, 0)
    solid(-w / 2 + 0.2, -d / 2 + 0.2, w / 2 - 0.2, d / 2 - 0.2, -0.5, 17.0)

    return m.finish("garage", fuse_soft=False)


@reg
def theater():
    m.setup(35)
    w, d = 12, 8
    bw, bd = w - 0.4, d - 0.4
    m.plinth(bw, bd, 0.3)
    m.storey(bw, bd, 0, 4.4, "ny_brick_dark", front=[("store", -3.0, 0.4, 3.6, 3.3, {"bays": 2}), ("door", 1.0, 0.4, 1.4, 2.8, {}), ("door", 2.8, 0.4, 1.4, 2.8, {})], back=[("louver", 0, 1.0, 2.0, 1.4, {})], left=[("lite", 0, 1.5, 1.0, 1.0, {})], right=[("lite", 0, 1.5, 1.0, 1.0, {})])
    m.storey(bw, bd, 4.4, 5.6, "ny_brick", front=[("sash", x, 1.6, 1.3, 2.2, {}) for x in (-3.5, 0, 3.5)])
    m.cornice(bw, bd, 9.8, "ny_lime", 0.6, 0.35)
    m.parapet(bw, bd, 10.3, 1.0, "ny_brick", "ny_lime")
    add(bx((bw - 1.0, 2.2, 0.35), (0, -bd / 2 - 1.1, 3.9), "ny_red_dark", 0.04))
    add(bx((bw - 0.8, 2.2, 0.8), (0, -bd / 2 - 1.1, 4.1), "ny_cream", 0.05))
    place(m.sign_box(bw - 1.6, 0.7, "ny_navy", "ny_cream", letters=10), 0, -bd / 2 - 2.2, 4.3, 0)
    m.roof_gear(bw, bd, 11.4, 2)
    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, 13.0)
    solid(-bw / 2 + 0.5, -bd / 2 - 2.2, bw / 2 - 0.5, -bd / 2, 3.8, 4.8)

    return m.finish("theater")
