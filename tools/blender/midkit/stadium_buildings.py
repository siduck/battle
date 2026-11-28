import math

import arena_parts as A
import buildings as bd
import jp
from arena_parts import F, B, R, cyl, flat, rod, tilted, done, k
from jp import add, shift

win = bd.win
door = bd.door


def hull(name, w, d, h, wall, front, back=(), left=(), right=(), roof="flat", rise=1.2, seed=1, budget=6000, plinth="st_conc_d", band="st_conc_d", parapet=0.45, overhang=0.35):
    A.setup(seed)
    bd.plinth(w, d, plinth)
    bd.storey(w, 0, h, wall, front=front, back=back, left=left, right=right, depth=d)
    bd.band(w, h - 0.02, band, 0.2, 0.06, depth=d)

    if roof == "flat":
        add(jp.flat_roof(w, d, h + 0.18, parapet, wall, "st_conc_l"))
    elif roof == "gable":
        add(jp.gable_roof(w, d, rise, h + 0.18, overhang, wall, color="st_roof"))

    return d / 2


def roof_unit(x, y, z, w=0.9, d=0.7, h=0.55):
    B((w, d, h), (x, y, z), "st_steel", 0.02)
    A.vent_grille(w * 0.6, h * 0.6, (x, y - d / 2 - 0.0, z + h * 0.2), 4)


def clubhouse():
    d = hull("clubhouse", 15.6, 10.4, 4.9, "st_conc_l", [
        ("glass", 0, 0, 4.6, 2.7, {"bays": 3}),
        win(-5.6, 1.0, 2.2, 1.4, screen=True),
        win(5.6, 1.0, 2.2, 1.4, screen=True),
        win(-2.9, 3.35, 1.6, 1.1),
        win(0, 3.35, 1.6, 1.1),
        win(2.9, 3.35, 1.6, 1.1),
        win(-5.6, 3.35, 2.2, 1.1),
        win(5.6, 3.35, 2.2, 1.1),
    ], back=[door(-5.0, 1.6, 2.2, glass=True), door(5.0, 1.6, 2.2, glass=True), win(0, 1.0, 3.0, 1.3), win(-2.4, 3.35, 1.6, 1.1), win(2.4, 3.35, 1.6, 1.1)],
        left=[win(-2.5, 1.0, 1.5, 1.3), win(2.5, 1.0, 1.5, 1.3), win(0, 3.35, 3.0, 1.1)],
        right=[win(-2.5, 1.0, 1.5, 1.3), win(2.5, 1.0, 1.5, 1.3), win(0, 3.35, 3.0, 1.1)], seed=11, budget=9000)
    fy = -d / 2
    B((7.1, 2.65, 0.32), (0, fy - 1.32, 3.0), "st_red", 0.04)
    flat((7.1, 0.09, 0.22), (0, fy - 2.62, 3.02), "st_white")

    for sx in (-1, 1):
        R((sx * 3.2, fy - 2.43, 0), (sx * 3.2, fy - 2.43, 3.0), 0.11, "st_steel_d", 8)
        B((0.4, 0.4, 0.15), (sx * 3.2, fy - 2.43, 0), "st_conc_d", 0.02)

    add(shift(jp.sign(5.2, 0.7, "st_blue_d", "st_white"), 0, fy, 3.55))

    for i in range(3):
        B((4.8 - i * 0.0, 0.36, 0.15), (0, fy - 2.5 - 0.36 * i, 0.15 * (2 - i)), "st_conc_l", 0.01)

    roof_unit(-4.5, 1.5, 5.1, 1.4, 1.0, 0.8)
    roof_unit(-2.5, 1.5, 5.1, 1.4, 1.0, 0.8)
    roof_unit(4.0, -1.0, 5.1, 1.0, 1.0, 0.7)
    B((1.6, 1.6, 0.9), (5.0, 2.5, 5.1), "st_conc_l", 0.02)
    flat((1.5, 0.2, 0.5), (5.0, 1.65, 5.1), "st_char")
    add(shift(jp.pipe(-7.5, fy - 0.05, 0.05, 5.4, "st_steel_d"), 0, 0, 0))

    return done("clubhouse", 9000)


def firstaid():
    d = hull("firstaid", 5.0, 3.8, 3.0, "st_white", [
        door(-1.2, 1.2, 2.1, glass=True),
        win(1.2, 1.0, 1.6, 1.2),
    ], back=[win(0, 1.0, 1.8, 1.2)], left=[win(0, 1.0, 1.4, 1.2)], right=[win(0, 1.0, 1.4, 1.2)], seed=12, budget=4000, band="st_red")
    fy = -d / 2
    add(shift(jp.awning(2.0, 0.9, "st_blue_d", "st_white"), -1.2, fy, 2.5))

    B((1.8, 1.2, 0.12), (-1.2, fy - 0.6, 0.0), "st_conc_l", 0.01)
    A.handrail((-0.3, fy - 1.2, 0.12), (-0.3, fy - 0.1, 0.12), 0.9, 0.7, 0.025, "st_steel")
    A.handrail((-2.1, fy - 1.2, 0.12), (-2.1, fy - 0.1, 0.12), 0.9, 0.7, 0.025, "st_steel")
    add(shift(jp.sign(0.9, 0.36, "st_red", "st_white", letters=3), 1.2, fy, 2.2))
    roof_unit(1.2, 0.3, 3.4, 1.1, 0.9, 0.6)
    roof_unit(-1.0, 0.6, 3.4, 0.8, 0.8, 0.5)

    return done("firstaid", 4000)


def toilets():
    d = hull("toilets", 7.5, 3.75, 3.0, "st_conc_l", [
        door(-2.6, 0.9, 2.1, leaf="st_blue_d"),
        door(-1.3, 0.9, 2.1, leaf="st_blue_d"),
        door(1.3, 0.9, 2.1, leaf="st_blue_d"),
        door(2.6, 0.9, 2.1, leaf="st_blue_d"),
        win(0, 2.0, 1.0, 0.5),
    ], back=[win(-2.2, 2.0, 1.0, 0.5), win(0, 2.0, 1.0, 0.5), win(2.2, 2.0, 1.0, 0.5)], left=[win(0, 2.0, 1.0, 0.5)], right=[win(0, 2.0, 1.0, 0.5)],
        roof="gable", rise=1.5, seed=13, budget=5000, band="st_blue_d")
    fy = -d / 2
    A.louvre_slots(-0.6, 0.6, 0.6, 1.8, fy - 0.0, 6, "st_char")
    add(shift(jp.sign(0.5, 0.5, "st_blue_d", "st_white", letters=1), -1.95, fy, 2.4))
    add(shift(jp.sign(0.5, 0.5, "st_red", "st_white", letters=1), 1.95, fy, 2.4))

    return done("toilets", 5000)


def pressbox():
    d = hull("pressbox", 6.5, 3.9, 3.0, "st_blue", [
        ("glass", 0, 0.5, 5.4, 2.2, {"bays": 4}),
        door(-2.6, 0.9, 2.1),
    ], back=[door(2.4, 1.0, 2.1), win(-1.0, 1.0, 2.0, 1.2)], left=[win(0, 1.2, 1.4, 1.0)], right=[win(0, 1.2, 1.4, 1.0)], seed=14, budget=5000, band="st_blue_d")
    fy = -d / 2
    B((7.0, 1.1, 0.16), (0, fy - 0.5, 3.1), "st_conc_l", 0.02)
    flat((7.0, 0.05, 0.3), (0, fy - 1.05, 3.1), "st_blue_d")

    for sx in (-1, 1):
        R((sx * 3.2, fy - 0.9, 0.0), (sx * 3.2, fy - 0.9, 3.1), 0.05, "st_steel_d", 6)

    B((5.6, 0.9, 0.12), (0, fy - 0.45, 0.0), "st_conc_l", 0.01)
    R((2.4, 1.2, 3.6), (2.4, 1.2, 6.5), 0.035, "st_steel_d", 6)
    R((2.0, 1.2, 5.6), (2.8, 1.2, 5.6), 0.02, "st_steel", 4)
    roof_unit(-1.5, 0.5, 3.4, 1.2, 0.9, 0.6)

    return done("pressbox", 5000)


def kiosk():
    d = hull("kiosk", 3.75, 3.7, 2.7, "st_conc_l", [
        ("shutter", 0, 0.0, 2.4, 2.0, {"open": 0.65}),
    ], back=[door(0, 0.9, 2.0)], left=[win(0, 1.2, 1.2, 0.8)], right=[win(0, 1.2, 1.2, 0.8)], roof="gable", rise=1.1, seed=15, budget=3000, band="st_red")
    fy = -d / 2
    add(shift(jp.awning(3.2, 1.0, "st_red", "st_white"), 0, fy, 2.55))
    B((2.6, 0.5, 0.08), (0, fy - 0.3, 1.0), "st_wood", 0.01)

    for sx in (-1, 1):
        B((0.5, 0.5, 0.9), (sx * 1.0, fy - 0.35, 0.0), "st_conc_d", 0.02)

    return done("kiosk", 3000)


def booth():
    A.setup(16)
    w, d = 2.5, 2.5
    bd.plinth(w, d, "st_conc_d")
    bd.storey(w, 0, 2.3, "st_blue", front=[("glass", 0, 0.95, 1.7, 1.2, {"bays": 2})], back=[door(0, 0.8, 2.0)], left=[win(0, 1.0, 1.0, 1.0)], right=[win(0, 1.0, 1.0, 1.0)], depth=d)
    fy = -d / 2
    B((2.0, 0.5, 0.08), (0, fy - 0.2, 0.95), "st_conc_l", 0.01)
    B((3.0, 3.0, 0.2), (0, 0, 2.3), "st_red", 0.02)
    flat((3.0, 0.06, 0.1), (0, fy - 0.72, 2.3), "st_white")
    B((0.9, 0.3, 0.3), (0, 0.0, 2.5), "st_conc_d", 0.02)

    return done("booth", 2500)


def turnstile():
    A.setup(17)
    w, d = 3.75, 2.5
    flat((w, d, 0.1), (0, 0, 0), "st_conc_d")

    for sx in (-1, 1):
        for sy in (-1, 1):
            B((0.18, 0.18, 3.0), (sx * 1.7, sy * 1.05, 0.1), "st_steel_d", 0.01)

    B((w, d, 0.2), (0, 0, 3.1), "st_blue_d", 0.02)
    flat((w - 0.2, d - 0.2, 0.05), (0, 0, 3.3), "st_conc_l")
    flat((w, 0.05, 0.1), (0, -d / 2 - 0.0, 3.15), "st_white")

    for x in (-0.75, 0.75):
        B((0.4, 0.4, 1.0), (x, 0, 0.1), "st_steel", 0.03)
        cyl(0.14, 0.2, (x, 0, 1.1), "st_steel_d", 10)

        for a in (0, 120, 240):
            t = math.radians(a + 20)
            R((x, 0, 1.2), (x + 0.55 * math.cos(t), 0.55 * math.sin(t), 1.2), 0.03, "st_steel_d", 6)

        flat((0.14, 0.1, 0.06), (x, -0.2, 1.1), "st_red")

    for x in (-0.0,):
        B((0.4, 0.4, 1.0), (x, 0, 0.1), "st_steel", 0.03)

    A.handrail((-1.7, -0.95, 0.1), (-1.7, 0.95, 0.1), 1.0, 0.6, 0.03, "st_steel")
    A.handrail((1.7, -0.95, 0.1), (1.7, 0.95, 0.1), 1.0, 0.6, 0.03, "st_steel")

    flat((0.8, 0.05, 0.3), (0, -1.2, 2.8), "st_white")

    return done("turnstile", 3000)


def tunnel():
    A.setup(18)
    w, d, h = 5.2, 3.88, 3.4
    B((w, d, h), (0, 0, 0), "st_conc", 0.04)
    A.profile_xz([(-1.05, 0), (-1.05, 1.55), (-0.9, 2.0), (-0.55, 2.3), (0, 2.45), (0.55, 2.3), (0.9, 2.0), (1.05, 1.55), (1.05, 0)], 0.5, "st_char", y=-d / 2 - 0.05)
    B((w + 0.2, d + 0.2, 0.28), (0, 0, h), "st_conc_l", 0.03)

    A.profile_xz([(-1.25, 0), (-1.25, 1.65), (-1.05, 2.15), (-0.6, 2.5), (0, 2.65), (0.6, 2.5), (1.05, 2.15), (1.25, 1.65), (1.25, 0)], 0.16, "st_blue_d", y=-d / 2 - 0.1)

    for sx in (-1, 1):
        B((0.5, 0.5, h + 0.28), (sx * (w / 2 - 0.25), -d / 2 - 0.05, 0), "st_conc_l", 0.02)

    B((4.8, 0.2, 0.4), (0, -d / 2 - 0.05, 2.75), "st_red", 0.01)
    B((2.5, 1.3, 0.14), (0, -d / 2 - 0.65, 0.0), "st_conc_l", 0.02)

    for sx in (-1, 1):
        A.handrail((sx * 1.4, -d / 2 - 1.3, 0.14), (sx * 1.4, -d / 2 - 0.1, 0.14), 0.95, 0.7, 0.03, "st_steel")

    A.handrail((-w / 2 + 0.3, -d / 2 + 0.3, h + 0.28), (w / 2 - 0.3, -d / 2 + 0.3, h + 0.28), 0.9, 0.8, 0.025, "st_steel_d")

    for sx in (-1, 1):
        A.vent_grille(0.9, 0.5, (sx * 2.2, d / 2 - 0.0, 1.5), 4)

    return done("tunnel", 4000)


def gate():
    A.setup(19)
    w, d = 8.4, 4.12
    pw = 2.2

    for sx in (-1, 1):
        x = sx * (w / 2 - pw / 2)
        B((pw, d, 5.4), (x, 0, 0), "st_conc", 0.04)
        B((pw + 0.3, d + 0.3, 0.3), (x, 0, 5.4), "st_conc_l", 0.03)
        B((0.5, 0.5, 0.5), (x, -d / 2 + 0.5, 5.7), "st_conc_d", 0.02)
        B((0.5, 0.5, 0.5), (x, d / 2 - 0.5, 5.7), "st_conc_d", 0.02)

        for z in (0.8, 1.9, 3.0, 4.1):
            flat((pw + 0.1, d + 0.1, 0.07), (x, 0, z), "st_conc_d")

        A.vent_grille(0.8, 0.8, (x, -d / 2 - 0.0, 3.5), 5)

    B((w, 1.6, 1.4), (0, -0.8, 5.4), "st_blue_d", 0.04)
    B((w + 0.2, 1.8, 0.25), (0, -0.8, 6.8), "st_conc_l", 0.02)
    flat((w - 0.6, 0.06, 0.28), (0, -1.62, 5.6), "st_red")
    flat((3.6, 0.06, 0.34), (0, -1.62, 6.1), "st_white")
    flat((w, 0.4, 0.08), (0, 0.3, 5.3), "st_conc_dd")

    for z in (0.1,):
        flat((w - 2 * pw, d, 0.12), (0, 0, z - 0.1), "st_conc_d")

    for sx in (-1, 1):
        x = sx * (w / 2 - pw)
        for i in range(8):
            R((x - sx * 0.1, -d / 2 + 0.25 + i * 0.5, 0.1), (x - sx * 0.1, -d / 2 + 0.25 + i * 0.5, 2.2), 0.025, "st_steel_d", 4)

    return done("gate", 4000)


def store():
    A.setup(20)
    w, d, h = 5.2, 3.9, 3.0
    B((w, d, 0.2), (0, 0, 0), "st_conc_d", 0.01)
    flat((w, d, h), (0, 0, 0.1), "st_steel")

    for i in range(int(w / 0.25) + 1):
        x = -w / 2 + i * w / int(w / 0.25)
        flat((0.1, 0.06, h - 0.3), (x, -d / 2 - 0.02, 0.2), "st_steel_d")
        flat((0.1, 0.06, h - 0.3), (x, d / 2 + 0.02, 0.2), "st_steel_d")

    for i in range(int(d / 0.25) + 1):
        y = -d / 2 + i * d / int(d / 0.25)
        flat((0.06, 0.1, h - 0.3), (-w / 2 - 0.02, y, 0.2), "st_steel_d")
        flat((0.06, 0.1, h - 0.3), (w / 2 + 0.02, y, 0.2), "st_steel_d")

    A.profile_yz([(-d / 2 - 0.4, h - 0.1), (d / 2 + 0.4, h + 0.9), (d / 2 + 0.4, h + 1.0), (-d / 2 - 0.4, h)], w + 0.5, "st_roof")
    flat((1.9, 0.14, 2.15), (-0.8, -d / 2 - 0.1, 0.2), "st_blue_d")
    flat((1.7, 0.1, 1.95), (-0.8, -d / 2 - 0.18, 0.3), "st_blue")
    flat((0.1, 0.12, 1.95), (-0.8, -d / 2 - 0.22, 0.3), "st_blue_d")
    B((0.22, 0.1, 0.1), (-0.15, -d / 2 - 0.25, 1.1), "st_steel", 0.01)
    B((1.2, 0.1, 1.0), (1.5, -d / 2 - 0.05, 1.0), "st_conc_dd", 0.01)
    flat((1.0, 0.04, 0.8), (1.5, -d / 2 - 0.12, 1.1), "st_glass")

    B((0.9, 0.6, 0.6), (2.0, -d / 2 - 0.45, 0.0), "st_wood", 0.03)
    B((0.9, 0.6, 0.6), (2.0, -d / 2 - 0.45, 0.6), "st_wood_d", 0.03)
    A.vent_grille(0.6, 0.4, (0, d / 2 + 0.05, 2.2), 4)

    return done("store", 3000)


def snackbox():
    A.setup(21)
    w, d, h = 6.0, 2.4, 2.6
    flat((w - 0.2, d - 0.2, 0.2), (0, 0, 0), "st_char")
    flat((w, d, h), (0, 0, 0.2), "st_blue")

    for i in range(int(w / 0.2)):
        x = -w / 2 + 0.1 + i * 0.2
        for sy in (-1, 1):
            flat((0.1, 0.06, h - 0.2), (x, sy * (d / 2 + 0.02), 0.3), "st_blue_d")

    for i in range(int(d / 0.2)):
        y = -d / 2 + 0.1 + i * 0.2

        for sx in (-1, 1):
            flat((0.06, 0.1, h - 0.2), (sx * (w / 2 + 0.02), y, 0.3), "st_blue_d")

    flat((w + 0.05, d + 0.05, 0.12), (0, 0, h + 0.2), "st_blue_dd")
    flat((w - 0.1, d - 0.1, 0.06), (0, 0, h + 0.32), "st_steel")

    fy = -d / 2 - 0.06
    B((3.0, 0.2, 1.3), (-0.5, fy - 0.05, 0.9), "st_char", 0.02)
    B((3.4, 0.7, 0.08), (-0.5, fy - 0.4, 1.05), "st_wood", 0.01)
    add(shift(jp.awning(3.4, 1.1, "st_red", "st_white"), -0.5, fy, 2.4))
    flat((1.2, 0.05, 1.2), (2.2, fy - 0.03, 0.5), "st_conc_dd")
    flat((1.0, 0.05, 1.0), (2.2, fy - 0.07, 0.6), "st_steel_d")

    for x in (-1.4, -0.5, 0.4):
        cyl(0.19, 0.06, (x, fy - 0.9, 0.62), "st_wood_l", 8)
        cyl(0.04, 0.62, (x, fy - 0.9, 0.0), "st_steel_d", 6)

    return done("snackbox", 3000)


def shelter():
    A.setup(22)
    s = 8.0
    h = 3.4
    flat((s, s, 0.12), (0, 0, 0), "st_conc_d")

    for sx in (-1, 1):
        for sy in (-1, 1):
            B((0.3, 0.3, h), (sx * 3.2, sy * 3.2, 0.12), "st_wood_d", 0.02)
            B((0.55, 0.55, 0.1), (sx * 3.2, sy * 3.2, 0.12), "st_conc", 0.01)

    for sx in (-1, 1):
        B((0.22, 7.6, 0.4), (sx * 3.2, 0, h), "st_wood", 0.02)
        B((7.6, 0.22, 0.4), (0, sx * 3.2, h + 0.1), "st_wood", 0.02)

    prof = [(-4.0, 0.0), (4.0, 0.0), (0.0, 2.7)]
    for sx in (-1, 1):
        pass

    ob = k.lathe("roof", [(0.01, 2.7), (5.2, 0.0), (5.2, -0.16), (0.01, 2.54)], 4, (0, 0, h + 0.5), jp.c("st_roof"))
    k.rotate(ob, 45, "Z")
    add(ob)

    for i in range(4):
        t = math.radians(45 + i * 90)
        R((0, 0, h + 3.2), (4.6 * math.cos(t) * 0.95, 4.6 * math.sin(t) * 0.95, h + 0.35), 0.1, "st_wood_d", 4)

    B((1.8, 0.7, 0.08), (0, -1.0, 0.82), "st_wood_l", 0.01)
    B((1.8, 0.7, 0.08), (0, 1.0, 0.82), "st_wood_l", 0.01)
    B((1.8, 0.8, 0.08), (0, 0, 0.78), "st_wood_l", 0.01)

    for sy in (-1, 1):
        for sx in (-0.7, 0.7):
            B((0.08, 0.7, 0.7), (sx, sy * 1.0, 0.12), "st_wood_d", 0.01)

    for sx in (-0.7, 0.7):
        B((0.08, 0.7, 0.7), (sx, 0, 0.12), "st_wood_d", 0.01)

    return done("shelter", 4000)


ALL = {
    "clubhouse": clubhouse,
    "firstaid": firstaid,
    "toilets": toilets,
    "pressbox": pressbox,
    "kiosk": kiosk,
    "booth": booth,
    "turnstile": turnstile,
    "tunnel": tunnel,
    "gate": gate,
    "store": store,
    "snackbox": snackbox,
    "shelter": shelter,
}
