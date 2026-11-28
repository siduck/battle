import math

import arena_parts as A
import jp
from arena_parts import F, B, R, cyl, flat, rod, tilted, done, k
from jp import add, shift
from mathutils import Vector


def wire_panel(w, h, x, y, z0, gap_v, gap_h, color="st_steel", t=0.014):
    n = int(w / gap_v)

    for i in range(n + 1):
        flat((t, t, h), (x - w / 2 + i * w / n, y, z0), color)

    m = int(h / gap_h)

    for j in range(m + 1):
        flat((w, t, t), (x, y + 0.012, z0 + j * h / m), color)


def mesh():
    A.setup(31)
    w, h = 2.4, 2.88
    B((w, 0.16, 0.2), (0, 0, 0), "st_conc_d", 0.02)

    for sx in (-1, 1):
        B((0.1, 0.1, h), (sx * (w / 2 - 0.05), 0, 0.0), "st_blue_d", 0.01)
        B((0.16, 0.16, 0.08), (sx * (w / 2 - 0.05), 0, h), "st_blue_dd", 0.01)

    for z in (0.25, h - 0.18):
        B((w - 0.2, 0.06, 0.06), (0, 0, z), "st_blue_d", 0.01)

    wire_panel(w - 0.2, h - 0.5, 0, 0, 0.3, 0.1, 0.2)
    B((w - 0.2, 0.05, 0.05), (0, 0, h / 2 + 0.1), "st_blue_d", 0.01)


    return done("mesh", 1200)


def wall():
    A.setup(32)
    w, h = 2.4, 2.88
    B((w, 0.2, 0.35), (0, 0, 0), "st_conc_d", 0.02)
    B((w - 0.1, 0.16, h - 0.65), (0, 0, 0.35), "st_conc", 0.02)
    B((w, 0.24, 0.16), (0, 0, h - 0.3), "st_conc_l", 0.02)
    B((w + 0.04, 0.3, 0.14), (0, 0, h - 0.14), "st_conc_l", 0.02)

    for sx in (-1, 1):
        B((0.22, 0.26, h - 0.3), (sx * (w / 2 - 0.11), 0, 0.15), "st_conc_l", 0.02)

    for sx in (-0.55, 0.55):
        flat((0.7, 0.04, 1.5), (sx, -0.1, 0.65), "st_conc_d")
        flat((0.5, 0.05, 1.3), (sx, -0.115, 0.75), "st_conc")

    flat((w - 0.3, 0.05, 0.26), (0, -0.1, h - 0.62), "st_blue_d")

    return done("wall", 900)


def fence():
    A.setup(33)
    w, h = 3.5, 2.0
    wire_panel(w - 0.1, h - 0.1, 0, 0, 0.05, 0.12, 0.25, "st_steel", 0.016)

    for sx in (-1, 1):
        B((0.07, 0.07, h), (sx * (w / 2 - 0.035), 0, 0.0), "st_steel_d", 0.01)

    for z in (0.0, h - 0.07):
        B((w, 0.06, 0.07), (0, 0, z), "st_steel_d", 0.01)

    for sx in (-1, 1):
        x = sx * (w / 2 - 0.3)
        B((0.1, 1.0, 0.07), (x, 0, 0.0), "st_steel", 0.01)
        B((0.1, 0.1, 0.4), (x, 0, 0.07), "st_steel", 0.01)
        B((0.1, 0.14, 0.14), (x, 0.0, 0.2), "st_steel_d", 0.01)

    return done("fence", 1500)


def rail():
    A.setup(34)

    for sx in (-1, 1):
        x = sx * 0.9
        B((0.22, 0.28, 0.06), (x, 0, 0), "st_conc_d", 0.01)
        R((x, 0, 0.06), (x, 0, 1.0), 0.04, "st_blue_d", 8)

    R((-0.95, 0, 1.0), (0.95, 0, 1.0), 0.04, "st_red", 8)
    R((-0.9, 0, 0.55), (0.9, 0, 0.55), 0.03, "st_blue_d", 6)

    return done("rail", 500)


def bin():
    A.setup(35)
    cyl(0.3, 0.06, (0, 0, 0), "st_conc_d", 12)
    cyl(0.28, 0.7, (0, 0, 0.06), "st_char", 12)

    for i in range(12):
        t = math.radians(i * 30)
        R((0.3 * math.cos(t), 0.3 * math.sin(t), 0.08), (0.3 * math.cos(t), 0.3 * math.sin(t), 0.78), 0.028, "st_blue_d", 4)

    cyl(0.33, 0.07, (0, 0, 0.78), "st_blue_d", 12)
    cyl(0.31, 0.04, (0, 0, 0.85), "st_blue_dd", 12, top=0.2)
    cyl(0.14, 0.03, (0, 0, 0.86), "st_char", 10)

    return done("bin", 500)


def bench():
    A.setup(36)

    for i, y in enumerate((-0.2, -0.03, 0.14)):
        B((2.4, 0.15, 0.05), (0, y, 0.42), "st_wood", 0.01)

    for z in (0.62, 0.8):
        s = A.jp.flat((2.4, 0.04, 0.14), (0, 0, -0.07), "st_wood")
        k.rotate(s, -12, "X")
        k.move(s, 0, 0.26 + (z - 0.62) * 0.2, z)
        add(s)

    for sx in (-1, 1):
        x = sx * 1.05
        flat((0.05, 0.5, 0.05), (x, -0.0, 0.38), "st_steel_d")
        R((x, -0.22, 0.0), (x, -0.22, 0.4), 0.025, "st_steel_d", 4)
        R((x, 0.2, 0.0), (x, 0.28, 0.9), 0.025, "st_steel_d", 4)
        flat((0.06, 0.5, 0.03), (x, 0.0, 0.0), "st_steel_d")

    return done("bench", 600)


def picnic():
    A.setup(37)
    B((1.8, 0.85, 0.05), (0, 0, 0.72), "st_wood", 0.01)

    for i in range(4):
        flat((1.8, 0.03, 0.02), (0, -0.33 + i * 0.22, 0.7), "st_wood_d")

    for sy in (-1, 1):
        B((1.8, 0.28, 0.05), (0, sy * 0.62, 0.43), "st_wood", 0.01)

    for sx in (-1, 1):
        x = sx * 0.7

        for sy in (-1, 1):
            R((x, sy * 0.72, 0.0), (x, sy * 0.1, 0.72), 0.03, "st_wood_d", 4)

        flat((0.07, 1.5, 0.05), (x, 0, 0.4), "st_wood_d")

    return done("picnic", 700)


def ptoilet():
    A.setup(38)
    B((1.2, 1.2, 0.1), (0, 0, 0), "st_conc_d", 0.01)
    B((1.15, 1.15, 2.2), (0, 0, 0.1), "st_blue", 0.04)
    A.profile_yz([(-0.62, 2.3), (0.62, 2.48), (0.62, 2.55), (-0.62, 2.38)], 1.25, "st_blue_d")
    flat((0.8, 0.05, 1.85), (0, -0.59, 0.2), "st_blue_d")
    flat((0.66, 0.04, 1.7), (0, -0.62, 0.28), "st_blue_l" if False else "st_blue")
    B((0.08, 0.06, 0.2), (0.25, -0.65, 1.0), "st_steel", 0.01)
    flat((0.12, 0.04, 0.12), (0.25, -0.65, 1.28), "st_red")
    A.vent_grille(0.5, 0.18, (0, -0.58, 2.05), 3)
    R((0.4, 0.4, 2.3), (0.4, 0.4, 2.62), 0.025, "st_steel_d", 4)
    flat((0.5, 0.04, 0.2), (0, -0.6, 2.2), "st_white")

    return done("ptoilet", 900)


def generator():
    A.setup(39)
    w, d = 2.5, 1.0

    for sx in (-1, 1):
        flat((0.1, d, 0.12), (sx * 1.1, 0, 0.0), "st_steel_d")

    B((w, d, 0.1), (0, 0, 0.1), "st_steel_d", 0.01)
    B((w - 0.1, d - 0.1, 1.3), (0, 0, 0.2), "st_blue_d", 0.04)
    B((w - 0.3, d - 0.3, 0.06), (0, 0, 1.52), "st_blue", 0.01)
    A.vent_grille(0.9, 0.7, (-0.5, -d / 2 - 0.0, 0.55), 6)
    A.vent_grille(0.6, 0.5, (0.65, -d / 2 - 0.0, 0.7), 4)
    cyl(0.16, 0.5, (0.9, 0.1, 1.55), "st_steel_d", 10)
    cyl(0.2, 0.05, (0.9, 0.1, 2.0), "st_steel", 10)
    B((0.4, 0.5, 0.3), (-0.9, 0.0, 1.55), "st_red", 0.02)
    cyl(0.05, 0.1, (-0.9, 0.0, 1.85), "st_steel_d", 6)
    A.handrail((-1.2, -0.45, 1.58), (1.2, -0.45, 1.58), 0.28, 0.8, 0.02, "st_steel_d", mid=False)

    return done("generator", 1500)


def jersey():
    A.setup(40)
    out = [(-0.325, 0), (0.325, 0), (0.325, 0.2), (0.19, 0.55), (0.14, 0.8), (-0.14, 0.8), (-0.19, 0.55), (-0.325, 0.2)]
    A.profile_yz(out, 0.96, "st_conc", -0.5)
    A.profile_yz(out, 0.96, "st_conc_l", 0.5)

    for x in (-0.5, 0.5):
        flat((0.4, 0.36, 0.03), (x, 0, 0.8), "st_conc_l")

    flat((0.05, 0.8, 0.5), (0.0, 0, 0.0), "st_conc_dd")
    flat((0.04, 0.4, 0.04), (0.0, 0, 0.82), "st_steel_d")
    return done("jersey", 600)


def waterbar():
    A.setup(41)
    out = [(-0.3, 0), (0.3, 0), (0.3, 0.2), (0.24, 0.75), (0.15, 1.1), (0.1, 1.2), (-0.1, 1.2), (-0.15, 1.1), (-0.24, 0.75), (-0.3, 0.2)]
    A.profile_yz(out, 1.9, "st_red", -1.0)
    A.profile_yz(out, 1.9, "st_white", 1.0)

    for x in (-1.0, 1.0):
        flat((0.3, 0.2, 0.1), (x, 0, 1.2), "st_conc_dd")
        flat((0.9, 0.04, 0.16), (x, -0.255, 0.45), "st_conc_dd")
        flat((0.9, 0.04, 0.16), (x, 0.255, 0.45), "st_conc_dd")

    B((0.2, 0.3, 0.7), (0, 0, 0.1), "st_steel_d", 0.01)

    return done("waterbar", 900)


def stall():
    A.setup(42)
    s = 3.0
    h = 2.3
    B((s - 0.3, s - 0.3, 0.06), (0, 0, 0), "st_conc_d", 0.01)

    for sx in (-1, 1):
        for sy in (-1, 1):
            R((sx * 1.4, sy * 1.4, 0.06), (sx * 1.4, sy * 1.4, h), 0.035, "st_steel", 6)
            B((0.2, 0.2, 0.05), (sx * 1.4, sy * 1.4, 0.0), "st_steel_d", 0.01)

    ob = k.lathe("roof", [(0.01, 3.0), (2.12, 2.3), (2.12, 2.1)], 4, (0, 0, 0), jp.c("st_blue_l"))
    k.rotate(ob, 45, "Z")
    k.move(ob, 0, 0, 0)
    add(ob)

    for i in range(4):
        t = math.radians(i * 90)

    for sy in (-1, 1):
        for i in range(6):
            x = -1.5 + i * 0.6
            flat((0.3, 0.03, 0.3), (x + 0.15, sy * 1.5, h - 0.05), "st_white" if i % 2 else "st_blue_d")

    for sx in (-1, 1):
        for i in range(6):
            y = -1.5 + i * 0.6
            flat((0.03, 0.3, 0.3), (sx * 1.5, y + 0.15, h - 0.05), "st_white" if i % 2 else "st_blue_d")

    B((2.4, 0.7, 0.9), (0, -0.3, 0.06), "st_wood_l", 0.03)
    B((2.5, 0.8, 0.05), (0, -0.3, 0.96), "st_conc_l", 0.01)
    flat((2.4, 0.04, 0.4), (0, -0.67, 0.4), "st_blue_d")

    for x in (-0.7, 0.0, 0.7):
        B((0.4, 0.3, 0.3), (x, -0.3, 1.01), "st_wood", 0.02)

    return done("stall", 2000)


def pallet():
    A.setup(43)

    for y in (-0.36, 0.0, 0.36):
        B((1.04, 0.1, 0.09), (0, y, 0.0), "st_wood_l", 0.01)

    for i in range(5):
        B((1.04, 0.14, 0.02), (0, -0.34 + i * 0.17, 0.09), "st_wood", 0.0)

    for sx in (-1, 1):
        for sy in (-1, 1):
            pass

    for z in (0.12, 0.62):
        for sx in (-1, 1):
            B((0.5, 0.8, 0.48), (sx * 0.26, 0, z), "st_wood_l" if z < 0.5 else "st_conc_l", 0.02)

    for z in (0.3, 0.55, 0.8, 1.05):
        flat((1.06, 0.84, 0.03), (0, 0, z + 0.1), "st_white")

    flat((0.3, 0.02, 0.2), (0.0, -0.43, 0.7), "st_red")

    return done("pallet", 800)


def planter():
    A.setup(44)
    B((1.0, 1.0, 0.5), (0, 0, 0), "st_conc", 0.04)
    B((1.06, 1.06, 0.1), (0, 0, 0.5), "st_conc_l", 0.02)
    B((0.84, 0.84, 0.04), (0, 0, 0.5), "st_wood_d", 0.0)
    flat((0.8, 0.04, 0.2), (0, -0.51, 0.15), "st_conc_d")
    import nature
    for at, size, col in (((0.0, 0.0, 0.8), (0.42, 0.42, 0.34), "jp_leaf"), ((-0.18, 0.1, 0.72), (0.28, 0.28, 0.24), "jp_leaf_dark"), ((0.2, -0.1, 0.78), (0.26, 0.26, 0.24), "jp_leaf_light")):
        add(nature.blob(at, size, ("jp_leaf_light", col, "jp_leaf_dark"), seed=hash(at) % 50))

    return done("planter", 900)


def banner():
    A.setup(45)
    B((1.84, 0.5, 0.1), (0, 0, 0), "st_conc_d", 0.02)
    cyl(0.06, 4.9, (-0.7, 0, 0.1), "st_steel_d", 8)
    cyl(0.1, 0.12, (-0.7, 0, 0.1), "st_steel", 8)
    B((1.6, 0.04, 0.08), (0.2, 0, 4.8), "st_steel_d", 0.0)
    R((-0.7, 0, 4.6), (-0.1, 0, 4.85), 0.025, "st_steel_d", 4)
    flat((1.1, 0.03, 3.2), (0.25, -0.0, 1.55), "st_blue")
    flat((1.1, 0.04, 0.5), (0.25, -0.0, 3.5), "st_red")
    flat((1.1, 0.04, 0.18), (0.25, -0.0, 2.9), "st_white")
    flat((1.1, 0.04, 0.5), (0.25, -0.0, 1.55), "st_blue_d")
    flat((0.7, 0.045, 0.14), (0.25, -0.0, 2.3), "st_white")
    B((1.14, 0.06, 0.06), (0.25, 0, 3.2 + 1.55 - 0.02), "st_steel_d", 0.0)

    return done("banner", 800)


def parasol():
    A.setup(46)
    B((0.9, 0.9, 0.08), (0, 0, 0), "st_conc_d", 0.02)
    cyl(0.28, 0.14, (0, 0, 0.08), "st_conc", 10)
    cyl(0.035, 2.5, (0, 0, 0.1), "st_steel_d", 8)
    ob = k.lathe("canopy", [(0.01, 2.69), (0.45, 2.62), (0.95, 2.45), (1.36, 2.18), (1.36, 2.1), (0.95, 2.34), (0.45, 2.54), (0.01, 2.6)], 8, (0, 0, 0), jp.c("st_blue_l"))
    add(ob)

    for i in range(8):
        t = math.radians(i * 45 + 22.5)
        R((0.0, 0, 2.55), (1.28 * math.cos(t), 1.28 * math.sin(t), 2.16), 0.012, "st_steel_d", 4)

    cyl(1.37, 0.12, (0, 0, 2.06), "st_red", 16, top=1.34)
    cyl(0.07, 0.1, (0, 0, 2.66), "st_steel_d", 6)

    return done("parasol", 900)


def flagpole():
    A.setup(47)
    cyl(0.14, 0.12, (-0.9, 0, 0), "st_conc_d", 10)
    cyl(0.07, 8.8, (-0.9, 0, 0.12), "st_steel", 10, top=0.035)
    cyl(0.09, 0.06, (-0.9, 0, 0.05), "st_steel_d", 10)
    cyl(0.08, 0.14, (-0.9, 0, 8.86), "st_steel_d", 8)

    for i in range(8):
        x = -0.85 + i * 0.22
        wave = 0.07 * math.sin(i * 0.9)
        flat((0.23, 0.02, 1.2), (x + 0.1, wave, 7.5), "st_red" if i < 8 else "st_red")

    for i in range(8):
        x = -0.85 + i * 0.22
        wave = 0.07 * math.sin(i * 0.9)
        flat((0.23, 0.025, 0.4), (x + 0.1, wave, 7.9), "st_white")


    return done("flagpole", 800)


def scoreboard():
    A.setup(48)
    W = 4.8

    for sx in (-1, 1):
        x = sx * 2.0
        B((0.3, 0.3, 5.3), (x, 0.0, 0.0), "st_steel_d", 0.02)
        B((0.7, 0.7, 0.15), (x, 0.0, 0.0), "st_conc_d", 0.02)

        for sy in (-1, 1):
            R((x, 0.0, 3.8), (x, 0.35, 0.1), 0.05, "st_steel_d", 4)


    B((W, 0.5, 2.2), (0, 0.0, 5.2), "st_char", 0.04)
    B((W + 0.2, 0.56, 0.16), (0, 0.0, 7.4), "st_steel_d", 0.02)
    B((W + 0.2, 0.56, 0.16), (0, 0.0, 5.06), "st_steel_d", 0.02)
    flat((W - 0.3, 0.05, 0.3), (0, -0.27, 7.0), "st_conc_l")
    flat((2.2, 0.06, 0.18), (0, -0.28, 7.04), "st_blue_d")

    segs = {"a": (0.1, 0.9, 0.5, 0.1), "b": (0.5, 0.5, 0.1, 0.5), "c": (0.5, 0.1, 0.1, 0.5), "d": (0.1, 0.0, 0.5, 0.1), "e": (0.0, 0.1, 0.1, 0.5), "f": (0.0, 0.5, 0.1, 0.5), "g": (0.1, 0.45, 0.5, 0.1)}
    digits = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd"}

    def digit(ch, x0, z0, s):
        for sg in digits[ch]:
            sx, sz, sw, sh = segs[sg]
            flat((sw * s, 0.05, sh * s), (x0 + (sx + sw / 2) * s, -0.28, z0 + sz * s * 0.0 + sz * s), "st_white")

    z0 = 5.55
    s = 1.0
    pos = [(-1.9, "2"), (-1.2, "1"), (0.7, "0"), (1.4, "3")]

    for x, ch in pos:
        digit(ch, x, z0, s * 1.2)

    for sy in (-0.25, 0.25):
        flat((0.12, 0.05, 0.12), (0.0, -0.28, z0 + 0.55 + sy), "st_mustard")

    flat((4.4, 0.04, 0.12), (0, -0.28, 5.28), "st_red")


    for sx in (-1, 1):
        B((0.9, 0.5, 0.3), (sx * 1.0, 0.0, 7.56), "st_steel_d", 0.02)

    return done("scoreboard", 2500)


def make_text_font():
    return {
        "A": ["010", "101", "111", "101", "101"],
        "C": ["011", "100", "100", "100", "011"],
        "I": ["111", "010", "010", "010", "111"],
        "K": ["101", "101", "110", "101", "101"],
        "L": ["100", "100", "100", "100", "111"],
        "N": ["101", "111", "111", "101", "101"],
        "O": ["010", "101", "101", "101", "010"],
        "R": ["110", "101", "110", "101", "101"],
        "T": ["111", "010", "010", "010", "010"],
        "V": ["101", "101", "101", "101", "010"],
        "Z": ["111", "001", "010", "100", "111"],
        "D": ["110", "101", "101", "101", "110"],
        "G": ["011", "100", "101", "101", "011"],
        "E": ["111", "100", "110", "100", "111"],
        "4": ["101", "101", "111", "001", "001"],
        " ": ["000", "000", "000", "000", "000"],
    }


FONT = make_text_font()


def word(s, cx, z0, px, y, color, out=-1):
    wdt = (len(s) * 4 - 1) * px
    x = cx - wdt / 2

    for ch in s:
        rows = FONT[ch]

        for r, bits in enumerate(rows):
            zt = z0 + (4 - r) * px
            i = 0

            while i < 3:
                if bits[i] != "1":
                    i += 1
                    continue

                j = i

                while j < 3 and bits[j] == "1":
                    j += 1

                flat((px * (j - i), 0.02, px), (x + (i + j) * px / 2, y, zt), color)
                i = j

        x += 4 * px


def adboard(name, bg, fg, acc, text, seed):
    A.setup(seed)
    B((6.0, 0.14, 1.0), (0, 0, 0.1), "st_char", 0.02)
    flat((5.9, 0.05, 0.86), (0, -0.09, 0.17), bg)
    flat((5.9, 0.06, 0.1), (0, -0.095, 0.17), acc)
    flat((5.9, 0.06, 0.06), (0, -0.095, 0.9), acc)
    word(text, 0.4, 0.34, 0.1, -0.12, fg)
    A.disc(0.25, 0.04, (-1.6, -0.12, 0.34 + 0.25) , acc, 12)
    A.disc(0.12, 0.05, (-1.6, -0.14, 0.34 + 0.25), bg, 12)
    flat((5.9, 0.03, 0.6), (0, 0.075, 0.25), "st_conc_d")

    for x in (-2.4, 0, 2.4):
        B((0.1, 0.7, 0.08), (x, 0.0, 0.0), "st_steel_d", 0.01)
        R((x, 0.05, 0.85), (x, 0.33, 0.06), 0.035, "st_steel_d", 4)

    return done(name, 2500)


def ad_red():
    return adboard("ad_red", "st_red", "st_white", "st_mustard", "VOLTA", 51)


def ad_navy():
    return adboard("ad_navy", "st_blue_d", "st_white", "st_blue_l", "NORDA AIR", 52)


def ad_gold():
    return adboard("ad_gold", "st_mustard", "st_char", "st_red", "KICKZ", 53)


def sback(name, kind, seed):
    A.setup(seed)
    B((6.0, 0.9, 0.7), (0, 0, 0), "st_conc", 0.02)
    B((6.0, 0.15, 0.12), (0, -0.4, 0.0), "st_conc_d", 0.01)

    for i in range(6):
        x = -2.5 + i
        flat((0.94, 0.12, 4.7), (x, 0.0, 0.7), "st_steel" if i % 2 == 0 else "st_blue_l")
        flat((0.06, 0.15, 4.7), (x - 0.5, 0.0, 0.7), "st_steel_d")

    B((6.0, 0.8, 1.1), (0, 0.0, 5.4), "st_blue_d", 0.02)
    B((6.0, 0.9, 0.2), (0, 0.0, 6.5), "st_conc_l", 0.02)
    B((6.0, 0.95, 0.25), (0, 0.0, 6.7), "st_steel_d", 0.02)
    flat((6.0, 0.06, 0.1), (0, -0.4, 5.62), "st_red")

    if kind == "gate":
        B((2.6, 0.2, 3.3), (0, -0.4, 0.12), "st_steel_d", 0.01)
        flat((2.3, 0.05, 3.1), (0, -0.52, 0.12), "st_conc_dd")

        for i in range(11):
            flat((2.3, 0.04, 0.05), (0, -0.55, 0.3 + i * 0.27), "st_steel_d")

        B((3.0, 0.8, 0.14), (0, -0.0, 3.4), "st_conc_d", 0.01)
        B((2.2, 0.1, 0.7), (0, -0.4, 3.65), "st_blue_d", 0.01)
        word("GATE 4", 0, 3.72, 0.1, -0.46, "st_white")

        for sx in (-1, 1):
            B((0.7, 0.4, 1.4), (sx * 2.2, -0.35, 1.0), "st_conc_d", 0.02)

            for i in range(5):
                flat((0.64, 0.04, 0.06), (sx * 2.2, -0.56, 1.1 + i * 0.22), "st_steel")
    else:
        for i in range(4):
            x = -2.25 + i * 1.5
            flat((1.0, 0.08, 2.0), (x, -0.43, 1.1), "st_conc_d")
            flat((0.84, 0.1, 1.84), (x, -0.45, 1.18), "st_glass")
            flat((0.84, 0.11, 0.8), (x, -0.46, 2.2), "st_glass_l")
            flat((0.06, 0.12, 1.84), (x, -0.46, 1.18), "st_conc_d")

        for sx in (-1, 1):
            R((sx * 2.9, -0.45, 0.2), (sx * 2.9, -0.45, 5.4), 0.06, "st_steel_d", 6)

    return done(name, 3000)


def sback_gate():
    return sback("sback_gate", "gate", 54)


def sback_wall():
    return sback("sback_wall", "wall", 55)


def scaffold():
    A.setup(56)
    w = 2.2
    h = 5.2

    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * w / 2, sy * w / 2
            R((x, y, 0.0), (x, y, h + 1.0), 0.05, "st_steel", 8)
            B((0.3, 0.3, 0.06), (x, y, 0.0), "st_conc_d", 0.01)

    for z in (0.5, 2.0, 3.5, h):
        for sx in (-1, 1):
            R((sx * w / 2, -w / 2, z), (sx * w / 2, w / 2, z), 0.035, "st_steel_d", 4)
            R((-w / 2, sx * w / 2, z), (w / 2, sx * w / 2, z), 0.035, "st_steel_d", 4)

    for i in range(3):
        z0 = 0.5 + i * 1.5
        z1 = z0 + 1.5 if i < 2 else h
        sgn = 1 if i % 2 == 0 else -1

        for sx in (-1, 1):
            R((sx * w / 2, -sgn * w / 2, z0), (sx * w / 2, sgn * w / 2, z1), 0.03, "st_steel_d", 4)
            R((-sgn * w / 2, sx * w / 2, z0), (sgn * w / 2, sx * w / 2, z1), 0.03, "st_steel_d", 4)

    for i in range(7):
        flat((w + 0.2, 0.3, 0.05), (0, -w / 2 + 0.15 + i * 0.33, h + 0.0), "st_wood_l" if i % 2 else "st_wood")

    A.handrail((-w / 2, -w / 2, h + 0.05), (w / 2, -w / 2, h + 0.05), 1.0, 1.1, 0.03, "st_steel_d")
    A.handrail((-w / 2, w / 2, h + 0.05), (w / 2, w / 2, h + 0.05), 1.0, 1.1, 0.03, "st_steel_d")
    A.handrail((w / 2, -w / 2, h + 0.05), (w / 2, w / 2, h + 0.05), 1.0, 1.1, 0.03, "st_steel_d")

    for sx in (-1, 1):
        R((sx * 0.25, w / 2 + 0.12, 0.0), (sx * 0.25, w / 2 + 0.12, h + 0.9), 0.03, "st_steel", 4)

    for i in range(18):
        flat((0.5, 0.04, 0.04), (0, w / 2 + 0.12, 0.3 + i * 0.3), "st_steel")

    B((0.9, 0.5, 0.6), (0.2, 0.0, h + 0.1), "st_char", 0.03)
    B((0.45, 0.45, 0.35), (0.3, -0.5, h + 0.1), "st_steel_d", 0.03)

    return done("scaffold", 2500)


def medtent():
    A.setup(57)
    w, d = 4.0, 4.6
    h = 2.5

    for sx in (-1, 1):
        for sy in (-1, 1):
            R((sx * w / 2 * 0.92, sy * d / 2 * 0.92, 0.0), (sx * w / 2 * 0.92, sy * d / 2 * 0.92, h), 0.04, "st_steel", 6)
            B((0.25, 0.25, 0.05), (sx * w / 2 * 0.92, sy * d / 2 * 0.92, 0.0), "st_steel_d", 0.01)

    A.profile_xz([(-2.175, h), (0, h + 1.1), (2.175, h)], 4.95, "st_white")

    for sy in (-1, 1):
        for i in range(8):
            x = -w / 2 * 1.1 + 0.55 * i + 0.275
            flat((0.55, 0.04, 0.3), (x, sy * d / 2 * 1.08, h - 0.28), "st_blue_d" if i % 2 else "st_white")

    for sx in (-1, 1):
        for i in range(9):
            y = -d / 2 * 1.08 + 0.55 * i + 0.275
            flat((0.04, 0.55, 0.3), (sx * w / 2 * 1.1, y, h - 0.28), "st_blue_d" if i % 2 else "st_white")

    B((2.0, 0.8, 0.8), (0, 0.8, 0.0), "st_steel", 0.03)
    B((2.1, 0.9, 0.05), (0, 0.8, 0.8), "st_white", 0.01)
    B((0.5, 0.35, 0.3), (-0.5, 0.8, 0.85), "st_steel_d", 0.02)
    B((0.6, 0.4, 0.35), (0.5, 0.75, 0.85), "st_red", 0.02)
    B((0.7, 0.4, 0.5), (-1.3, -0.8, 0.0), "st_steel_d", 0.02)
    flat((0.6, 0.04, 0.2), (-1.3, -1.02, 0.25), "st_red")

    return done("medtent", 2500)


def inflatable():
    A.setup(58)
    a, b = 3.0, 3.52
    t = 0.55
    n = 14
    for i in range(n):
        t0 = math.pi * i / n
        t1 = math.pi * (i + 1) / n
        panel = [(a * math.cos(t0), b * math.sin(t0)),
                 (a * math.cos(t1), b * math.sin(t1)),
                 ((a - t) * math.cos(t1), (b - t) * math.sin(t1)),
                 ((a - t) * math.cos(t0), (b - t) * math.sin(t0))]
        A.profile_xz(panel, 6.6, "st_blue" if i % 2 == 0 else "st_blue_d")
        for y in (-2.75, 0, 2.75):
            trim = [((a + 0.07) * math.cos(t0), (b + 0.07) * math.sin(t0)),
                    ((a + 0.07) * math.cos(t1), (b + 0.07) * math.sin(t1)),
                    panel[2], panel[3]]
            A.profile_xz(trim, 0.36, "st_white", y=y)

    for sx in (-1, 1):
        B((0.2, 6.2, 0.14), (sx * (a - t / 2), 0.0, 0.0), "st_steel_d", 0.01)

    return done("inflatable", 2500)


def dugout():
    A.setup(59)
    w, d, h = 6.0, 2.4, 2.4
    flat((w, d, 0.1), (0, 0, 0), "st_conc_d")
    B((w, 0.14, h), (0, d / 2 - 0.07, 0.1), "st_blue", 0.02)

    for sx in (-1, 1):
        B((0.14, d, h), (sx * (w / 2 - 0.07), 0, 0.1), "st_blue", 0.02)

    A.profile_yz([(-d / 2 - 0.5, h - 0.05), (d / 2 + 0.1, h + 0.25), (d / 2 + 0.1, h + 0.1), (-d / 2 - 0.5, h - 0.25)], w + 0.3, "st_blue_d")
    flat((w - 0.2, 0.06, 0.12), (0, -d / 2 - 0.45, h - 0.38), "st_white")


    for i in range(2):
        B((w - 0.6, 0.45, 0.06), (0, d / 2 - 0.55 - i * 0.0, 0.45), "st_wood_l", 0.01)

    B((w - 0.6, 0.06, 0.4), (0, d / 2 - 0.4, 0.7), "st_wood", 0.01)

    for x in (-2.3, 0.0, 2.3):
        flat((0.08, 0.35, 0.4), (x, d / 2 - 0.55, 0.1), "st_steel_d")

    flat((w - 0.4, 0.04, 0.9), (0, d / 2 - 0.15, 1.2), "st_blue_d")
    flat((1.6, 0.05, 0.4), (0, d / 2 - 0.16, 1.5), "st_white")

    return done("dugout", 2500)


ALL = {
    "mesh": mesh,
    "wall": wall,
    "fence": fence,
    "rail": rail,
    "bin": bin,
    "bench": bench,
    "picnic": picnic,
    "ptoilet": ptoilet,
    "generator": generator,
    "jersey": jersey,
    "waterbar": waterbar,
    "stall": stall,
    "pallet": pallet,
    "planter": planter,
    "banner": banner,
    "parasol": parasol,
    "flagpole": flagpole,
    "scoreboard": scoreboard,
    "ad_red": ad_red,
    "ad_navy": ad_navy,
    "ad_gold": ad_gold,
    "sback_gate": sback_gate,
    "sback_wall": sback_wall,
    "scaffold": scaffold,
    "medtent": medtent,
    "inflatable": inflatable,
    "dugout": dugout,
}
