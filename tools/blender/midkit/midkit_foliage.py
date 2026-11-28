import math

import midkit_core as m


def blob(r, at, color, rng, sides=8, rings=4, squash=0.8, jitter=0.12):
    x, y, z = at
    prof = [(0, -r * squash)]

    for i in range(1, rings):
        a = -math.pi / 2 + math.pi * i / rings
        prof.append((r * math.cos(a), r * squash * math.sin(a)))

    prof.append((0, r * squash))
    ob = m.k.lathe("blob", prof, sides, (x, y, z), m.c(color))
    m.k.rotate(ob, rng.uniform(0, 360), "Z", (x, y, z))
    m.k.jitter(ob, r * jitter, seed=rng.randint(0, 999))

    return ob


def canopy(rng, clumps, z0, z1, dark="ap_leaf_d", mid="ap_leaf", light="ap_leaf_l"):
    items = []

    for x, y, z, r in clumps:
        t = (z - z0) / max(z1 - z0, 0.01)
        color = dark if t < 0.25 else mid if t < 0.7 else light
        items.append(blob(r, (x, y, z), color, rng))

    return items
