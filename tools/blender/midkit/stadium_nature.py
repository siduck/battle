import math
import random

import arena_parts as A
import jp
import nature
from arena_parts import done, k
from jp import add


def canopy(clusters, tones, seed, sub=2):
    return [nature.blob(at, size, tones, sub=sub, seed=seed + i) for i, (at, size) in enumerate(clusters)]


def broadleaf(name, h, spread, trunk_h, tones, n, seed, bark="jp_bark", budget=4000):
    A.setup(seed)
    r = random.Random(seed)
    items = [nature.trunk((0, 0, 0), (0.0, 0, trunk_h), 0.22, 0.13, bark)]
    clusters = [((0.0, 0, h - spread * 0.55), (spread * 0.62, spread * 0.6, spread * 0.42))]

    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.3, 0.3)
        rad = spread * r.uniform(0.45, 0.62)
        z = h - spread * r.uniform(0.75, 1.05)
        at = (math.cos(a) * rad, math.sin(a) * rad, z)
        s = spread * r.uniform(0.38, 0.5)
        clusters.append((at, (s, s, s * 0.78)))
        items.append(nature.trunk((0, 0, trunk_h * 0.75), (at[0] * 0.7, at[1] * 0.7, z - s * 0.4), 0.08, 0.05, bark))

    items += canopy(clusters, tones, seed)
    add(items)

    return jp.finish(name, budget, fuse_soft=False, gradient=False)


def oak():
    return broadleaf("oak", 7.0, 3.0, 3.2, ("jp_leaf_light", "jp_leaf", "jp_leaf_dark"), 7, 81)


def birch():
    A.setup(82)
    r = random.Random(82)
    items = [nature.trunk((0, 0, 0), (0.1, 0, 4.2), 0.13, 0.07, "st_white")]

    for z in (0.6, 1.3, 2.0, 2.8, 3.5):
        items.append(nature.trunk((0.02, 0, z), (0.03, 0, z + 0.07), 0.14, 0.14, "st_conc_dd"))

    clusters = [((0.1, 0, 5.4), (1.0, 1.0, 1.0)), ((0.3, 0.3, 4.6), (0.8, 0.8, 0.7)), ((-0.4, -0.2, 4.5), (0.8, 0.8, 0.7)), ((0.0, -0.5, 5.1), (0.7, 0.7, 0.8)), ((-0.2, 0.5, 5.3), (0.65, 0.65, 0.7))]

    for at, _ in clusters[1:]:
        items.append(nature.trunk((0.1, 0, 3.4), (at[0] * 0.8, at[1] * 0.8, at[2] - 0.4), 0.05, 0.03, "st_white"))

    items += canopy(clusters, ("jp_leaf_light", "jp_leaf", "jp_leaf_dark"), 82)
    add(items)

    return jp.finish("birch", 4000, fuse_soft=False, gradient=False)


def pine():
    A.setup(83)
    items = [nature.trunk((0, 0, 0), (0, 0, 3.0), 0.24, 0.1, "jp_bark")]
    tiers = 6

    for i in range(tiers):
        z = 1.2 + i * 1.25
        r = 1.8 - i * 0.28
        h = 2.0 - i * 0.12
        n = 9 * jp.N
        prof = [(0.01, 0.0), (r, 0.0), (r * 0.82, 0.18), (r * 0.9, 0.1)]
        ob = k.lathe("tier", [(0.01, 0.0), (r, 0.0), (r * 0.62, h * 0.45), (r * 0.78, h * 0.4), (0.01, h)], n, (0, 0, z), jp.c("st_pine"))
        k.rotate(ob, i * 23, "Z", (0, 0, z))
        items.append(ob)
        under = k.lathe("under", [(0.01, 0.0), (r * 0.98, 0.0), (r * 0.9, -0.12), (0.01, -0.12)], n, (0, 0, z), jp.c("st_pine_d"))
        k.rotate(under, i * 23, "Z", (0, 0, z))
        items.append(under)

    add(items)

    return jp.finish("pine", 4000, fuse_soft=False, gradient=False)


def bush():
    A.setup(84)
    items = canopy([((0.0, 0, 0.55), (0.95, 0.7, 0.55)), ((-0.8, 0.1, 0.45), (0.62, 0.55, 0.45)), ((0.85, -0.05, 0.42), (0.58, 0.55, 0.42)), ((0.1, 0.3, 0.9), (0.55, 0.5, 0.4))], ("jp_leaf_light", "jp_leaf", "jp_leaf_dark"), 84)
    add(items)

    return jp.finish("bush", 1500, fuse_soft=False, gradient=False)


ALL = {"oak": oak, "birch": birch, "pine": pine, "bush": bush}
