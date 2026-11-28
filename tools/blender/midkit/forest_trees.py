import math
import random

import nature_kit as nk
from mathutils import Vector

import forest_palette as fp


def bark(seed, base="fo_bark", lt="fo_bark_lt", dk="fo_bark_dk", moss=True):
    def pick(i, j):
        h = nk.hash01(i, j, seed)

        if moss and j == 0 and h < 0.45:
            return "fo_moss"

        if h < 0.28:
            return lt

        if h > 0.78:
            return dk

        return base

    return pick


def birch_bark(seed):
    def pick(i, j):
        h = nk.hash01(i, j, seed)

        if h < 0.3:
            return "fo_birch_mark"

        return "fo_birch" if h < 0.85 else "fo_stone_lt"

    return pick


def trunk(height, r0, r1, seed, lean=(0.0, 0.0), sides=10, colors=None, flare=1.45, rings=6, roots=4, root_len=0.9):
    pts = []
    radii = []

    for j in range(rings):
        u = j / (rings - 1)
        z = height * u ** 1.05
        pts.append((lean[0] * u * u, lean[1] * u * u, z))
        f = 1 + (flare - 1) * max(0.0, 1 - u * height / 0.9) ** 2
        radii.append((r0 + (r1 - r0) * u) * f)

    items = [nk.tube("trunk", pts, radii, sides, colors or bark(seed), cap_top="fo_bark_dk", jit=0.1, seed=seed)]
    r = random.Random(seed)

    for i in range(roots):
        a = 2 * math.pi * i / roots + r.uniform(-0.4, 0.4)
        ln = root_len * r.uniform(0.7, 1.1)
        p0 = (math.cos(a) * r0 * 0.5, math.sin(a) * r0 * 0.5, r0 * 1.0)
        p1 = (math.cos(a) * (r0 + ln * 0.55), math.sin(a) * (r0 + ln * 0.55), r0 * 0.35)
        p2 = (math.cos(a) * (r0 + ln), math.sin(a) * (r0 + ln), -0.02)
        items.append(nk.tube("root", [p0, p1, p2], [r0 * 0.5, r0 * 0.34, r0 * 0.16], 5, ["fo_bark", "fo_bark_lt", "fo_bark_dk"], cap_top=False))

    return items


def branch(a, b, r0, r1, color=("fo_bark", "fo_bark_lt"), sides=6, bend=0.12):
    a = Vector(a)
    b = Vector(b)
    m = (a + b) / 2 + Vector((0, 0, bend * (b - a).length))

    return nk.tube("branch", [a, m, b], [r0, (r0 + r1) / 2, r1], sides, list(color), cap_top=False)


def layered(items, seed, rings, tones_for, accent=None, accent_p=0.0, top=None):
    r = random.Random(seed)
    n = 0

    for count, rad, z0, z1, size, squash in rings:
        phase = r.uniform(0, 6.28)

        for i in range(count):
            a = phase + 2 * math.pi * i / count + r.uniform(-0.2, 0.2)
            rr = rad * r.uniform(0.85, 1.12)
            z = r.uniform(z0, z1)
            s = size * r.uniform(0.85, 1.15)
            at = (math.cos(a) * rr, math.sin(a) * rr, z)
            items.append(nk.blob(at, (s, s, s * squash), tones_for(z), sub=1, seed=seed * 10 + n, jitter=0.17, flat_bottom=0.45, accent=accent, accent_p=accent_p))
            n += 1

    if top:
        at, size, tones = top
        items.append(nk.blob(at, size, tones, sub=1, seed=seed + 90, jitter=0.12, flat_bottom=0.4, accent=accent, accent_p=accent_p))


def oak():
    nk_setup(11)
    items = trunk(3.3, 0.34, 0.24, 11, lean=(0.15, 0.05), root_len=1.0)
    hi = ("fo_leaf_hi", "fo_leaf", "fo_leaf_lo")
    lo = ("fo_leaf", "fo_leaf_lo", "fo_leaf_dk")
    r = random.Random(11)

    for i in range(6):
        a = 2 * math.pi * i / 6 + r.uniform(-0.3, 0.3)
        items.append(branch((0.12, 0.04, 2.6 + 0.15 * (i % 3)), (math.cos(a) * 1.0 + 0.15, math.sin(a) * 1.0, 3.9), 0.13, 0.06))

    layered(items, 11, [(6, 1.38, 3.6, 4.1, 1.1, 0.72), (4, 0.9, 4.5, 5.0, 1.05, 0.78), (2, 0.4, 5.5, 5.9, 0.9, 0.8)], lambda z: hi if z > 4.4 else lo, top=((0.1, 0, 5.4), (1.25, 1.2, 1.05), hi))
    items.append(nk.chips((0.1, 0, 4.7), (2.7, 2.6, 1.4), 18, ("fo_leaf_hi", "fo_leaf"), 3, length=0.34))
    nk.add(items)

    return nk.finish("oak", 2500)


def maple():
    nk_setup(12)
    items = trunk(2.6, 0.3, 0.17, 12, lean=(-0.1, 0.0), root_len=0.8)
    hi = ("fo_maple_hi", "fo_maple", "fo_maple_lo")
    lo = ("fo_maple", "fo_maple_lo", "fo_leaf_dk")
    r = random.Random(12)

    for i in range(6):
        a = 2 * math.pi * i / 6 + r.uniform(-0.3, 0.3)
        items.append(branch((0, 0, 2.2 + 0.1 * (i % 3)), (math.cos(a) * 0.8, math.sin(a) * 0.8, 3.6), 0.1, 0.05))

    layered(items, 12, [(5, 1.1, 3.3, 3.8, 0.9, 0.75), (3, 0.7, 4.2, 4.7, 0.86, 0.8), (2, 0.35, 5.1, 5.4, 0.74, 0.85)], lambda z: hi if z > 4.0 else lo, accent="fo_accent_lt", accent_p=0.045, top=((0, 0, 4.9), (1.0, 0.95, 0.9), hi))
    items.append(nk.chips((0, 0, 4.2), (2.0, 2.0, 1.2), 16, ("fo_maple_hi", "fo_accent_lt"), 4, length=0.3))
    nk.add(items)

    return nk.finish("maple", 2200)


def birch():
    nk_setup(13)
    items = trunk(4.4, 0.2, 0.085, 13, lean=(0.28, -0.1), sides=8, colors=birch_bark(13), flare=1.3, roots=3, root_len=0.5, rings=9)
    r = random.Random(13)
    tones = ("fo_birch_hi", "fo_birch_leaf", "fo_birch_lo")
    spots = [((0.35, -0.1, 5.7), (0.85, 0.85, 1.05)), ((-0.55, 0.45, 4.9), (0.8, 0.75, 0.95)), ((0.95, 0.35, 4.6), (0.75, 0.7, 0.9)), ((0.2, -0.85, 4.3), (0.7, 0.7, 0.85)), ((-0.35, -0.5, 6.0), (0.62, 0.6, 0.8))]

    for i, (at, size) in enumerate(spots):
        items.append(nk.blob(at, size, tones, sub=1, seed=40 + i, jitter=0.13))
        items.append(branch((0.2 + 0.2 * (i % 2), -0.05, 3.5 + 0.3 * i), (at[0] * 0.8, at[1] * 0.8, at[2] - 0.55), 0.06, 0.03, ("fo_birch", "fo_birch_mark"), 5))

    items.append(nk.chips((0.2, -0.1, 5.0), (1.5, 1.3, 1.4), 12, ("fo_birch_hi", "fo_birch_leaf"), 5, length=0.26))
    nk.add(items)

    return nk.finish("birch", 1800)


def pine_parts(h, r_base, seed, tiers=7, trunk_r=0.28, at=(0, 0), start=1.6, tilt=0.0):
    r = random.Random(seed)
    x0, y0 = at
    items = [nk.tube("trunk", [(x0, y0, 0), (x0, y0, 0.3), (x0, y0, h * 0.55), (x0 + tilt, y0, h * 0.95)], [trunk_r * 1.5, trunk_r * 1.1, trunk_r * 0.6, 0.12], 8, bark(seed, moss=True), cap_top="fo_bark_dk")]
    span = h - start
    colors = [("fo_pine", "fo_pine_hi", "fo_pine_dk"), ("fo_pine_hi", "fo_pine", "fo_pine_dk"), ("fo_pine", "fo_pine", "fo_pine_dk")]

    for i in range(tiers):
        u = i / (tiers - 1)
        z = start + span * u * 0.86
        rad = r_base * (1 - 0.72 * u ** 0.9) * r.uniform(0.94, 1.06)
        ht = max(0.9, (span - span * u * 0.86) / (tiers - i) * 1.9 + 0.3)
        ht = min(ht, h - z + 0.05)
        items.append(nk.tier((x0 + tilt * u, y0, z), rad, ht, sides=6, colors=colors[i % 3], seed=seed + i, drop=0.16))

    return items


def pine():
    nk_setup(14)
    nk.add(pine_parts(9.0, 1.85, 14, tiers=6))

    return nk.finish("pine", 1500)


def young():
    nk_setup(15)
    nk.add(pine_parts(3.0, 0.92, 15, tiers=4, trunk_r=0.1, start=0.35))

    return nk.finish("young", 700)


def pines():
    nk_setup(16)
    nk.add(pine_parts(9.0, 1.6, 16, tiers=4, trunk_r=0.3, at=(0, 0), start=1.8))
    nk.add(pine_parts(7.2, 1.35, 17, tiers=3, trunk_r=0.22, at=(-1.5, 0.8), start=1.3, tilt=0.12))
    nk.add(pine_parts(5.8, 1.1, 18, tiers=3, trunk_r=0.18, at=(1.2, -1.0), start=1.0, tilt=-0.1))

    return nk.finish("pines", 2400)


def dead():
    nk_setup(17)
    pts = [(0, 0, 0), (0.05, 0, 0.5), (0.2, 0.05, 1.8), (0.05, 0.1, 3.0), (-0.1, 0.08, 4.2), (0.0, 0.0, 4.9)]
    radii = [0.46, 0.34, 0.27, 0.22, 0.16, 0.06]
    items = [nk.tube("trunk", pts, radii, 8, bark(17, "fo_dead", "fo_dead_lt", "fo_dead_dk", moss=False), cap_top="fo_dead_lt", jit=0.14, seed=17)]
    r = random.Random(17)

    for i in range(5):
        a = 2 * math.pi * i / 5 + r.uniform(-0.3, 0.3)
        ln = 0.7 + 0.2 * (i % 2)
        items.append(nk.tube("root", [(math.cos(a) * 0.2, math.sin(a) * 0.2, 0.5), (math.cos(a) * (0.35 + ln * 0.6), math.sin(a) * (0.35 + ln * 0.6), 0.15), (math.cos(a) * (0.3 + ln), math.sin(a) * (0.3 + ln), -0.02)], [0.16, 0.11, 0.05], 5, ["fo_dead", "fo_dead_dk"], cap_top=False))

    limbs = [(2.2, 0.4, 1.35, 0.9, 0.5), (2.8, 3.6, 1.2, 1.0, 0.45), (3.3, 2.1, 1.3, 0.8, 0.55), (3.8, 5.2, 1.0, 0.95, 0.42), (4.2, 0.9, 0.9, 1.1, 0.3), (1.6, 4.4, 0.9, 0.5, 0.4)]

    for z, ang, ln, rise, rr in limbs:
        dx = math.cos(ang) * ln
        dy = math.sin(ang) * ln
        base = (0.1, 0.06, z)
        tip = (0.1 + dx, 0.06 + dy, z + rise)
        items.append(branch(base, tip, 0.12 * rr * 2, 0.04, ("fo_dead", "fo_dead_dk"), 6, bend=0.05))
        fork = (0.1 + dx * 0.6, 0.06 + dy * 0.6, z + rise * 0.55)
        items.append(branch(fork, (fork[0] + dy * 0.45, fork[1] - dx * 0.45, fork[2] + 0.55), 0.06, 0.025, ("fo_dead_dk", "fo_dead"), 5, bend=0.0))

    nk.add(items)

    return nk.finish("dead", 1200, flat=False)


def nk_setup(seed):
    fp.setup(seed)


ALL = {"oak": oak, "maple": maple, "birch": birch, "pine": pine, "young": young, "dead": dead, "pines": pines}
