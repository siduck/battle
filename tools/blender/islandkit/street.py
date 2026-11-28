import math

from mathutils import Vector

import ck


def disc(r, z, col, n, cx=0.0, cy=0.0):
    return ck.Part([ck.Poly([(p[0], p[1], z) for p in ck.ngon(r, n, cx, cy, phase=0.0)], col)])


def chair_part(cx=0.0, cy=0.0, turn=0.0, col="blue"):
    out = ck.Part()

    for x in (-0.19, 0.19):
        out += ck.box(x - 0.025, -0.215, 0.0, x + 0.025, -0.165, 0.46, col, skip="d", d=2)
        out += ck.box(x - 0.027, 0.165, 0.0, x + 0.027, 0.215, 0.9, col, skip="d", d=2)
        out += ck.box(x - 0.034, 0.16, 0.89, x + 0.034, 0.222, 0.92, ck.shade(col, 1.12), c=0.01, d=0)
        out += ck.box(x - 0.012, -0.165, 0.16, x + 0.012, 0.165, 0.19, ck.shade(col, 0.88), d=0, skip="fb")

    for y in (-0.19, 0.19):
        out += ck.box(-0.17, y - 0.012, 0.24, 0.17, y + 0.012, 0.27, ck.shade(col, 0.88), d=0, skip="lr")

    out += ck.box(-0.22, -0.222, 0.43, 0.22, 0.2, 0.48, col, c=0.014, d=2)
    out += ck.box(-0.18, -0.185, 0.48, 0.18, 0.155, 0.502, "wicker", c=0.01, d=1, skip="d")

    for z, h in ((0.62, 0.045), (0.72, 0.045), (0.81, 0.08)):
        out += ck.box(-0.17, 0.172, z, 0.17, 0.205, z + h, col, d=1, skip="lr")

    return out.rot(turn).move(cx, cy, 0)


def chair():
    return chair_part()


def legs(hx, hy, z, r, col, d=2):
    out = ck.Part()

    for sx in (-1, 1):
        for sy in (-1, 1):
            out += ck.bar((sx * hx, sy * hy, 0.0), (sx * hx * 0.92, sy * hy * 0.92, z), r * 0.75, col, sides=4, taper=1.25, caps=(False, False), d=d)

    return out


def cup(x, y, z, col="wall_lt"):
    return ck.cyl((x, y, z), 0.03, 0.065, col, sides=6, rt=0.036, smooth=False, caps=(False, True), d=0)


def taverna():
    out = ck.Part()
    hx, hy, z = 0.4, 0.36, 0.76
    out += legs(0.33, 0.29, z - 0.05, 0.03, "wood")
    out += ck.box(-hx + 0.02, -hy + 0.02, z - 0.08, hx - 0.02, hy - 0.02, z - 0.02, "wood_dk", skip="td", d=1)
    n = 5 if ck.LOD == 0 else 1
    over = 0.045

    for i in range(n):
        for j in range(n):
            x0 = -hx - over + 2 * (hx + over) * i / n
            x1 = -hx - over + 2 * (hx + over) * (i + 1) / n
            y0 = -hy - over + 2 * (hy + over) * j / n
            y1 = -hy - over + 2 * (hy + over) * (j + 1) / n
            col = "blue_lt" if (i + j) % 2 == 0 else "wall_lt"
            out.append(ck.Poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], col))

    ex, ey = hx + over, hy + over
    ring = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)]

    for i in range(4):
        a, b = Vector((ring[i][0], ring[i][1], z)), Vector((ring[(i + 1) % 4][0], ring[(i + 1) % 4][1], z))
        m = 5 if ck.LOD == 0 else 1

        for k in range(m):
            p, q = a.lerp(b, k / m), a.lerp(b, (k + 1) / m)
            col = "blue" if (k + i) % 2 == 0 else "wall"
            low_p = Vector((p.x * 1.005, p.y * 1.005, z - 0.15))
            low_q = Vector((q.x * 1.005, q.y * 1.005, z - 0.15))
            out.append(ck.Poly([low_p, low_q, q, p], col))

            if ck.LOD == 0:
                out.append(ck.Poly([p, q, low_q, low_p], ck.shade(col, 0.8), False, True, False))

    out += ck.cyl((0.1, 0.06, z), 0.05, 0.16, "terra", sides=7, rt=0.025, smooth=False, d=1)
    out += cup(-0.16, -0.12, z)
    out += cup(0.17, -0.18, z)

    for sy in (-1, 1):
        out += chair_part(0.0, 0.0, 0.0 if sy > 0 else 180.0).move(0.0, sy * 0.68, 0.0)

    return out


def kafe():
    out = ck.Part()
    z = 0.76
    out += legs(0.27, 0.27, z - 0.04, 0.024, "green_dk")

    for sy in (-1, 1):
        out += ck.bar((-0.25, sy * 0.25, 0.64), (0.25, sy * 0.25, 0.64), 0.012, "green_dk", sides=3, d=0, caps=(False, False))
        out += ck.bar((sy * 0.25, -0.25, 0.64), (sy * 0.25, 0.25, 0.64), 0.012, "green_dk", sides=3, d=0, caps=(False, False))

    out += ck.box(-0.33, -0.33, z - 0.045, 0.33, 0.33, z, "green", c=0.012, skip="t")
    out += ck.box(-0.345, -0.345, z, 0.345, 0.345, z + 0.028, "wall_lt", c=0.01)
    z += 0.028
    out += ck.box(-0.2, -0.15, z, 0.14, 0.15, z + 0.03, "wood_dk", c=0.008, d=1, skip="d")

    if ck.LOD == 0:
        for side, (a, b) in enumerate(((-0.185, -0.04), (-0.02, 0.125))):
            for k in range(5):
                x0 = a + (b - a) * k / 5
                x1 = a + (b - a) * (k + 1) / 5
                col = "wood_lt" if (k + side) % 2 else "terra"
                out.append(ck.Poly([(x0, -0.135, z + 0.032), (x1, -0.135, z + 0.032), ((x0 + x1) / 2, -0.03, z + 0.032)], col, False, True, False))
                out.append(ck.Poly([(x1, 0.135, z + 0.032), (x0, 0.135, z + 0.032), ((x0 + x1) / 2, 0.03, z + 0.032)], col, False, True, False))

    out += cup(0.24, 0.18, z)
    out += cup(-0.27, -0.22, z)
    out += ck.cyl((0.24, -0.2, z), 0.032, 0.11, "glass_lt", sides=6, smooth=False, d=0)

    return out


def lamp():
    out = ck.box(-0.225, -0.225, 0.0, 0.225, 0.225, 0.14, "stone", c=0.035, skip="d")
    out += ck.box(-0.17, -0.17, 0.14, 0.17, 0.17, 0.5, "stone_lt", c=0.03, skip="d")
    out += ck.box(-0.19, -0.19, 0.5, 0.19, 0.19, 0.56, "stone", c=0.02, d=1)
    out += ck.lathe([(0.095, 0.56, "iron_dk"), (0.075, 0.66, "iron"), (0.045, 0.74, "iron"), (0.036, 2.0, "iron_dk"), (0.052, 2.04, "iron_dk"), (0.052, 2.1, "iron_dk"), (0.033, 2.14, "iron"), (0.028, 2.9, "iron")], 6, smooth=False)
    arc = [(0.0, 0.0, 2.88), (0.0, -0.02, 3.04), (0.0, -0.1, 3.12), (0.0, -0.19, 3.09), (0.0, -0.245, 2.98), (0.0, -0.25, 2.84)]
    out += ck.tube(arc, 0.022, 4, "iron", caps=(False, False), smooth=False)
    cy = arc[-1][1]
    out += ck.lathe([(0.035, 2.86, "iron_dk"), (0.15, 2.76, "iron"), (0.14, 2.73, "iron_dk")], 6, at=(0, cy, 0), smooth=False)
    out += ck.lathe([(0.085, 2.46, "glass_warm"), (0.12, 2.73, "glass_warm")], 6, at=(0, cy, 0), smooth=False)
    out += ck.lathe([(0.03, 2.38, "iron_dk"), (0.1, 2.44, "iron_dk"), (0.095, 2.47, "iron")], 6, at=(0, cy, 0), smooth=False)

    for i in range(6):
        a = 2 * math.pi * i / 6
        out += ck.bar((math.cos(a) * 0.088, cy + math.sin(a) * 0.088, 2.46), (math.cos(a) * 0.123, cy + math.sin(a) * 0.123, 2.74), 0.009, "iron_dk", sides=3, d=0, caps=(False, False))

    out += ck.tube([(0.0, 0.025, 2.55), (0.0, 0.11, 2.72), (0.0, 0.06, 2.86), (0.0, 0.0, 2.8)], 0.012, 3, "iron", caps=(False, False), smooth=False, d=0)

    return out


def nets():
    out = ck.Part()
    out += ck.blob((0.0, 0.0, 0.1), (0.9, 0.67, 0.26), ("rope_dk", "net", "net"), sub=1, jitter=0.1, seed=501, flat=0.38)
    piles = ((("terra_lt", "terra", "terra_dk"), (-0.35, 0.08, 0.27), (0.5, 0.42, 0.26)), (("rope", "rope_dk", "net"), (0.33, -0.1, 0.28), (0.48, 0.4, 0.27)), (("teal_lt", "teal", "teal_dk"), (0.12, 0.28, 0.3), (0.34, 0.28, 0.2)))

    for k, (tones, at, size) in enumerate(piles):
        out += ck.blob(at, size, tones, sub=1, jitter=0.2, seed=502 + k, flat=0.55)

    cords = (((-0.8, -0.22, 0.17), (-0.45, -0.15, 0.5), (-0.02, -0.05, 0.45), (0.35, -0.28, 0.54), (0.78, -0.2, 0.2)), ((-0.62, 0.4, 0.2), (-0.15, 0.2, 0.55), (0.25, 0.25, 0.52), (0.65, 0.35, 0.22)))

    for k, pts in enumerate(cords):
        out += ck.tube(pts, 0.018, 3, "blue" if k else "rope", caps=(False, False), smooth=False, d=1)

    floats = ((-0.62, -0.3, 0.31), (-0.38, -0.2, 0.52), (-0.08, -0.12, 0.49), (0.28, -0.3, 0.56), (0.6, -0.26, 0.38), (0.4, 0.3, 0.47), (-0.78, 0.2, 0.17), (0.72, 0.2, 0.17))

    for k, at in enumerate(floats):
        out += ck.blob(at, (0.072, 0.072, 0.065), ("red_lt", "float", "float") if k % 3 else ("wall_lt", "wall", "wall_dk"), sub=0, jitter=0.02, seed=520 + k, d=2 if k < 4 else 1)

    sheet = ck.ngon(0.7, 10, phase=0.2)
    out.append(ck.Poly([(p[0] * 1.42, p[1] * 1.01, 0.025) for p in sheet], "wood_dk"))

    return out


def pot():
    prof = [(0.17, 0.0, "clay_dk"), (0.19, 0.06, "clay_dk"), (0.17, 0.09, "clay"), (0.33, 0.3, "clay"), (0.372, 0.5, "clay_lt"), (0.33, 0.68, "clay"), (0.24, 0.78, "clay_dk"), (0.22, 0.83, "clay"), (0.3, 0.87, "clay_lt"), (0.295, 0.95, "clay_lt"), (0.22, 0.95, "clay_dk"), (0.2, 0.8, "shadow"), (0.18, 0.79, "void")]
    out = ck.lathe(prof, 12, smooth=False)
    out.append(ck.Poly([(p[0], p[1], 0.79) for p in ck.ngon(0.18, 12, phase=0.0)], "void"))

    for s in (-1, 1):
        out += ck.tube([(s * 0.23, 0, 0.8), (s * 0.38, 0, 0.79), (s * 0.425, 0, 0.68), (s * 0.345, 0, 0.58)], 0.03, 5, "clay", caps=(False, False), smooth=False, d=1)

    out += ck.lathe([(0.368, 0.46, "wall_dk"), (0.38, 0.5, "wall_dk"), (0.368, 0.54, "wall_dk")], 12, smooth=False, d=0)

    return out


def jar():
    prof = [(0.19, 0.0, "umber_dk"), (0.23, 0.04, "umber"), (0.33, 0.28, "umber"), (0.36, 0.5, "umber_lt"), (0.33, 0.66, "umber"), (0.24, 0.76, "umber_dk"), (0.19, 0.8, "umber"), (0.23, 0.83, "umber_lt"), (0.23, 0.87, "umber_dk"), (0.16, 0.88, "wood_dk"), (0.15, 0.93, "wood"), (0.06, 0.95, "wood_dk")]
    out = ck.lathe(prof, 12, smooth=False)
    out.append(ck.Poly([(p[0], p[1], 0.95) for p in ck.ngon(0.06, 12, phase=0.0)], "wood_dk"))
    out += ck.blob((0, 0, 0.965), (0.045, 0.045, 0.028), "stone_lt", sub=0, seed=1, d=1)

    for s in (-1, 1):
        out += ck.tube([(s * 0.3, 0, 0.7), (s * 0.372, 0, 0.66), (s * 0.35, 0, 0.55)], 0.026, 4, "umber_dk", caps=(False, False), smooth=False, d=1)

    out += ck.lathe([(0.185, 0.785, "rope"), (0.21, 0.805, "rope"), (0.185, 0.825, "rope")], 12, smooth=False, d=0)

    return out


def barrel():
    out = ck.Part()
    n = 14 if ck.LOD == 0 else 8 if ck.LOD == 1 else 6
    profile = ((0.355, 0.0), (0.425, 0.24), (0.44, 0.46), (0.425, 0.68), (0.355, 0.9)) if ck.LOD < 2 else ((0.36, 0.0), (0.44, 0.46), (0.36, 0.9))

    for j in range(len(profile) - 1):
        (r0, z0), (r1, z1) = profile[j], profile[j + 1]

        for i in range(n):
            a0 = 2 * math.pi * i / n
            a1 = 2 * math.pi * (i + 1) / n
            tone = ("wood", "wood_lt", "wood", "wood_dk")[(i * 3 + i // 3) % 4]
            pts = [(math.cos(a0) * r0, math.sin(a0) * r0, z0), (math.cos(a1) * r0, math.sin(a1) * r0, z0), (math.cos(a1) * r1, math.sin(a1) * r1, z1), (math.cos(a0) * r1, math.sin(a0) * r1, z1)]
            out.append(ck.Poly(pts, tone))

    out += ck.lathe([(0.355, 0.9, "wood_dk"), (0.365, 0.92, "wood_lt"), (0.32, 0.92, "wood_dk"), (0.31, 0.88, "wood_dk")], n, smooth=False, d=1)
    strips = 5 if ck.LOD == 0 else 0

    if ck.LOD:
        r = 0.31 if ck.LOD == 1 else 0.36
        z = 0.885 if ck.LOD == 1 else 0.9
        out.append(ck.Poly([(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z) for i in range(n)], "wood"))

    for k in range(strips):
        xa = -0.31 + 0.62 * k / strips
        xb = -0.31 + 0.62 * (k + 1) / strips
        ya = math.sqrt(max(0.0, 0.31 ** 2 - xa ** 2)) or 0.07
        yb = math.sqrt(max(0.0, 0.31 ** 2 - xb ** 2)) or 0.07
        out.append(ck.Poly([(xa, -ya, 0.885), (xb, -yb, 0.885), (xb, yb, 0.885), (xa, ya, 0.885)], "wood_lt" if k % 2 else "wood"))

    for z, r in ((0.1, 0.392), (0.26, 0.432), (0.64, 0.434), (0.8, 0.396)):
        out += ck.lathe([(r - 0.006, z - 0.035, "iron"), (r + 0.008, z - 0.025, "iron_lt"), (r + 0.008, z + 0.025, "iron"), (r - 0.006, z + 0.035, "iron")], n, smooth=False, d=1)

    return out


def sack():
    prof = [(0.2, 0.0, "burlap_dk"), (0.27, 0.07, "burlap"), (0.285, 0.24, "burlap"), (0.24, 0.4, "burlap"), (0.14, 0.52, "burlap_dk"), (0.075, 0.57, "rope_dk"), (0.07, 0.6, "burlap_dk"), (0.14, 0.7, "burlap"), (0.08, 0.725, "burlap_dk")]
    out = ck.Part()
    n = 10 if ck.LOD == 0 else 6
    rings = []

    for j, (r, z, col) in enumerate(prof):
        ring = []

        for i in range(n):
            a = 2 * math.pi * i / n
            k = 1 + (ck.hash01(i, j, 17.0) - 0.5) * (0.2 if r > 0.1 else 0.12)

            if j >= 7:
                k *= 1.0 if i % 2 else 0.7

            ring.append(Vector((math.cos(a) * r * k * 0.99, math.sin(a) * r * k * 0.96, z)))

        rings.append(ring)

    for j in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            out.append(ck.Poly([rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]], prof[j][2]))

    out.append(ck.Poly(rings[-1], "burlap_dk"))
    out += ck.torus((0, 0, 0.575), 0.083, 0.018, "rope", segs=8, sides=4, axis="Z", d=0)

    return out


def parasol():
    out = ck.lathe([(0.31, 0.0, "stone_dk"), (0.31, 0.07, "stone"), (0.16, 0.12, "stone_lt"), (0.07, 0.16, "stone_lt"), (0.05, 0.22, "stone")], 8, smooth=False)
    out += ck.cyl((0, 0, 0.2), 0.032, 2.43, "wood_dk", sides=6, smooth=False, caps=(False, False), d=2)
    n = 8
    rim = ck.ngon(1.358, n, phase=0.0)
    mid = ck.ngon(0.8, n, phase=0.0)
    apex = Vector((0, 0, 2.6))

    for i in range(n):
        j = (i + 1) % n
        tone = "terra" if i % 2 else "canvas"
        a = Vector((rim[i][0], rim[i][1], 2.08))
        b = Vector((rim[j][0], rim[j][1], 2.08))
        c = Vector((mid[i][0], mid[i][1], 2.4))
        d = Vector((mid[j][0], mid[j][1], 2.4))
        under = ck.shade(tone, 0.8)

        for pts in ((a, b, d, c), (c, d, apex)):
            out.append(ck.Poly(list(pts), tone))
            out.append(ck.Poly([p - Vector((0, 0, 0.018)) for p in reversed(pts)], under))

        e = (a + b) / 2 - Vector((0, 0, 0.17))
        out.append(ck.Poly([a, e, b], ck.shade(tone, 0.92)))

        if ck.LOD < 2:
            out.append(ck.Poly([a, b, e], under))

        out += ck.bar((0, 0, 2.12), (c.x, c.y, c.z - 0.04), 0.013, "wood", sides=3, d=0, caps=(False, False))

    out += ck.blob((0, 0, 2.645), (0.055, 0.055, 0.043), "wood_lt", sub=0, seed=2, d=1)

    return out


def bollard():
    out = ck.box(-0.33, -0.24, 0.0, 0.33, 0.24, 0.11, "stone", c=0.035, skip="d")
    out += ck.lathe([(0.17, 0.11, "iron_dk"), (0.17, 0.14, "iron"), (0.105, 0.17, "iron"), (0.09, 0.34, "iron"), (0.17, 0.39, "iron_lt"), (0.18, 0.44, "iron_lt"), (0.12, 0.49, "iron_lt"), (0.04, 0.512, "iron")], 10, smooth=False)
    out.append(ck.Poly([(p[0], p[1], 0.512) for p in ck.ngon(0.04, 10, phase=0.0)], "iron"))
    out += ck.bar((-0.2, 0, 0.3), (0.2, 0, 0.3), 0.035, "iron", sides=6, d=1)
    out += ck.torus((0, 0, 0.205), 0.13, 0.027, "rope", segs=10, sides=4, axis="Z", d=1)
    out += ck.tube([(0.12, -0.05, 0.2), (0.21, -0.13, 0.13), (0.28, -0.18, 0.135)], 0.025, 4, "rope", caps=(False, True), smooth=False, d=1)

    return out


def rope():
    out = ck.Part()

    for k, (R, z, tone) in enumerate(((0.34, 0.06, "rope_dk"), (0.31, 0.14, "rope"), (0.27, 0.22, "rope"))):
        out += ck.torus((0.01 * (k % 2), -0.012 * k, z), R, 0.062, lambda t, tone=tone: tone if int(t * 28) % 2 else ck.shade(tone, 0.88), segs=14, sides=5, axis="Z", d=2)

    out += ck.tube([(0.25, 0.02, 0.24), (0.38, -0.1, 0.2), (0.37, -0.3, 0.07), (0.18, -0.37, 0.045)], 0.043, 5, "rope", caps=(False, True), smooth=False, d=1)

    return out


SMALL = {"reach": 0.45, "ao": 0.45, "grime": 0.14, "grime_h": 0.3}

ALL = {
    "chair": (chair, SMALL),
    "taverna": (taverna, SMALL),
    "kafe": (kafe, SMALL),
    "lamp": (lamp, {"reach": 0.45, "ao": 0.4, "grime": 0.12, "grime_h": 0.5}),
    "nets": (nets, SMALL),
    "pot": (pot, SMALL),
    "jar": (jar, SMALL),
    "barrel": (barrel, SMALL),
    "sack": (sack, SMALL),
    "parasol": (parasol, {"reach": 0.6, "ao": 0.35, "grime": 0.08, "grime_h": 0.3}),
    "bollard": (bollard, SMALL),
    "rope": (rope, SMALL),
}
