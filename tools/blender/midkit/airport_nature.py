import math
import random

import midkit_core as m
import midkit_foliage as fo


def tree():
    m.setup()
    rng = random.Random(11)
    P = []
    P.append(m.lathe([(0, 0.0), (0.5, 0.0), (0.38, 0.5), (0.27, 1.6), (0.22, 3.2), (0, 3.2)], (0, 0, 0), "ap_bark", 8))

    for i in range(4):
        a = math.radians(i * 90 + 20)
        P.append(m.bar((0.0, 0.0, 2.6), (math.cos(a) * 1.9, math.sin(a) * 1.9, 4.6 + (i % 2) * 0.5), 0.12, "ap_bark", 6))

    P += fo.canopy(rng, [(0, 0, 5.6, 2.3), (2.2, 0.6, 5.0, 1.9), (-2.1, -0.4, 5.1, 1.9), (0.3, 2.1, 5.0, 1.8), (0.0, -2.2, 4.9, 1.8), (1.2, 1.2, 7.0, 1.7), (-1.1, -1.0, 7.0, 1.6), (0.0, 0.2, 7.3, 1.2), (2.6, -1.4, 4.6, 1.2), (-2.5, 1.4, 4.7, 1.2)], z0=4.0, z1=8.5)
    ob = m.finish("tree", P, budget=2500, grime=None, cull=False, gradient=None)

    return ob


def pine():
    m.setup()
    rng = random.Random(5)
    P = [m.lathe([(0, 0.0), (0.3, 0.0), (0.2, 0.8), (0.1, 6.0), (0, 6.0)], (0, 0, 0), "ap_bark", 8)]
    tiers = [(1.8, 1.0, 2.6), (1.55, 2.2, 2.4), (1.3, 3.4, 2.2), (1.05, 4.6, 2.0), (0.8, 5.8, 1.8), (0.5, 7.0, 1.5)]

    for i, (r, z, h) in enumerate(tiers):
        col = "ap_leaf_d" if i % 2 == 0 else "ap_leaf"
        cone = m.k.prism("t", 9, r, h, (0, 0, z), m.c(col), radius_top=0.08)
        m.k.jitter(cone, 0.07, seed=i)
        skirt = m.k.prism("sk", 9, r * 0.98, 0.35, (0, 0, z), m.c("ap_leaf_d"), radius_top=r * 0.78)
        m.k.rotate(skirt, 20)
        P += [cone, skirt]

    P.append(m.cyl(0.07, 1.8, (0, 0, 7.2), "ap_leaf", 6, top=0.01))
    ob = m.finish("pine", P, budget=1800, grime=None, cull=False, gradient=None)

    return ob


def shrub():
    m.setup()
    P = [m.lathe([(0, 0.0), (0.4, 0.0), (0.44, 0.35), (0.32, 1.4), (0.2, 2.1), (0, 2.4)], (0, 0, 0), "ap_leaf_d", 9)]
    P.append(m.lathe([(0, 0.35), (0.38, 0.35), (0.4, 0.9), (0.27, 1.8), (0.14, 2.2), (0, 2.4)], (0.0, 0.0, 0.0), "ap_leaf", 9))

    for i, a in enumerate((0, 120, 240)):
        r = math.radians(a)
        P.append(m.lathe([(0, 0.0), (0.2, 0.0), (0.22, 0.6), (0.12, 1.1), (0, 1.3)], (math.cos(r) * 0.26, math.sin(r) * 0.26, 0.5 + i * 0.35), "ap_leaf_l", 7))

    P.append(m.cyl(0.09, 0.2, (0, 0, 0.0), "ap_bark", 6))
    ob = m.finish("shrub", P, budget=900, grime=None, cull=False, gradient=None)

    return ob


def hedge():
    m.setup()
    P = [m.bx((4.0, 0.8, 1.3), (0, 0, 0.0), "ap_leaf_d", 0.22, seg=3)]
    P.append(m.bx((3.9, 0.7, 0.45), (0, 0, 1.15), "ap_leaf", 0.2, seg=3))
    rng = random.Random(3)

    for i in range(7):
        x = -1.65 + i * 0.55
        P.append(m.bx((0.62, 0.62, 0.3), (x, rng.uniform(-0.04, 0.04), 1.4 + rng.uniform(0, 0.08)), "ap_leaf_l" if i % 2 else "ap_leaf", 0.12, seg=2))

    for i in range(6):
        x = -1.7 + i * 0.68
        P.append(m.bx((0.3, 0.84, 0.5), (x, 0, 0.0), "ap_leaf_d", 0.08, seg=1))

    ob = m.finish("hedge", P, budget=1500, grime=None, cull=False, gradient=None)

    return ob


ALL = {"tree": tree, "pine": pine, "shrub": shrub, "hedge": hedge}
