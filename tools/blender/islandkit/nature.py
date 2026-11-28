import math
import random

from mathutils import Vector

import ck


def clump(at, size, tones, seed, sub=1, d=None, flat=0.7, jitter=0.2, accent=None, accent_p=0.0):
    return ck.blob(at, size, tones, sub=sub, jitter=jitter, seed=seed, flat=flat, d=d, accent=accent, accent_p=accent_p)


def limb(pts, radii, sides=6, col="trunk", seed=0, d=2):
    tones = (col, col + "_lt" if col == "trunk" else col, ck.shade(col, 0.86))

    return ck.tube(pts, radii, sides, lambda i, j: tones[int(ck.hash01(seed, i, j) * 3) % 3], caps=(False, True), smooth=False, d=d)


def gem(at, rx, rz, col, d=0):
    out = ck.Part()

    if ck.LOD > d:
        return out

    c = Vector(at)
    ring = [c + Vector((rx, 0, 0)), c + Vector((0, rx, 0)), c + Vector((-rx, 0, 0)), c + Vector((0, -rx, 0))]
    top = c + Vector((0, 0, rz))
    low = c - Vector((0, 0, rz))

    for i in range(4):
        a, b = ring[i], ring[(i + 1) % 4]
        out.append(ck.Poly([a, b, top], col, False, True, False))
        out.append(ck.Poly([b, a, low], ck.shade(col, 0.84), False, True, False))

    return out


def olive():
    out = ck.Part()
    tones = ("olive_lt", "olive", "olive_dk")
    out += limb([(0, 0, 0), (0.14, 0.06, 0.45), (-0.12, 0.0, 1.0), (0.1, 0.06, 1.6), (0.0, 0.0, 2.35)], [0.46, 0.3, 0.26, 0.2, 0.13], 7, "bark", 1)

    for k, a in enumerate((0.3, 2.5, 4.5)):
        foot = (math.cos(a) * 0.55, math.sin(a) * 0.45, 0.02)
        out += limb([foot, (math.cos(a) * 0.16, math.sin(a) * 0.12, 0.32)], [0.1, 0.17], 4, "bark", 3 + k, d=1)

    out += limb([(-0.08, 0.0, 1.05), (-0.85, 0.15, 1.75), (-1.35, 0.15, 2.45), (-2.1, 0.05, 2.7)], [0.19, 0.14, 0.1, 0.05], 5, "bark", 7)
    out += limb([(0.08, 0.04, 1.4), (0.8, -0.2, 2.05), (1.35, -0.25, 2.65), (2.2, -0.1, 2.75)], [0.18, 0.13, 0.09, 0.05], 5, "bark", 8)
    out += limb([(0.04, 0.05, 1.75), (0.3, 0.7, 2.5), (0.45, 1.05, 3.0)], [0.12, 0.08, 0.04], 4, "bark", 9)

    big = [((-2.12, 0.05, 2.85), (0.84, 0.82, 0.55)), ((2.1, -0.1, 2.92), (0.86, 0.85, 0.56)), ((-0.95, -0.25, 3.45), (0.98, 0.9, 0.66)), ((0.6, 0.15, 3.62), (1.05, 0.98, 0.66)), ((0.35, 1.15, 3.05), (0.8, 0.68, 0.5)), ((1.15, -0.95, 3.05), (0.8, 0.72, 0.48)), ((-0.4, -1.1, 2.75), (0.68, 0.62, 0.42))]

    for k, (at, size) in enumerate(big):
        out += clump(at, size, tones, 11 + k, d=2 if k < 5 else 1)

    for k, (at, s) in enumerate((((-2.55, -0.35, 2.45), 0.4), ((2.52, 0.3, 2.45), 0.42), ((-0.1, 0.45, 4.0), 0.5), ((-1.55, 0.75, 3.05), 0.52), ((1.55, 0.6, 3.25), 0.5))):
        out += clump(at, (s, s * 0.95, s * 0.66), tones, 31 + k, sub=0, d=1)

    return out


def cypress():
    out = ck.Part()
    out += ck.bar((0, 0, 0), (0, 0, 0.9), 0.14, "trunk", sides=5, taper=0.8, caps=(False, False))
    prof = ((0.55, 0.22), (0.95, 0.5), (1.6, 0.62), (2.4, 0.66), (3.3, 0.62), (4.2, 0.55), (5.1, 0.47), (5.9, 0.38), (6.6, 0.29), (7.2, 0.2), (7.65, 0.11))
    prof = prof if ck.LOD == 0 else prof[::2] if ck.LOD == 1 else (prof[0], prof[3], prof[7])
    sides = 9 if ck.LOD == 0 else 6 if ck.LOD == 1 else 5
    r = random.Random(5)
    rings = []

    for j, (z, rad) in enumerate(prof):
        ring = []

        for i in range(sides):
            a = 2 * math.pi * (i + 0.5 * (j % 2)) / sides
            rr = min(0.665, rad * r.uniform(0.87, 1.1))
            ring.append(Vector((math.cos(a) * rr, math.sin(a) * rr, z + r.uniform(-0.12, 0.12))))

        rings.append(ring)

    tones = ("cypress", "cypress", "cypress_dk", "cypress_lt")

    for j in range(len(rings) - 1):
        for i in range(sides):
            k = (i + 1) % sides

            if j % 2 == 0:
                tris = ((rings[j][i], rings[j][k], rings[j + 1][i]), (rings[j][k], rings[j + 1][k], rings[j + 1][i]))
            else:
                tris = ((rings[j][i], rings[j][k], rings[j + 1][k]), (rings[j][i], rings[j + 1][k], rings[j + 1][i]))

            for t, tri in enumerate(tris):
                out.append(ck.Poly(list(tri), tones[int(ck.hash01(j, i, t + 3.0) * 4) % 4]))

    tip = Vector((0.0, 0.0, 8.0))

    for i in range(sides):
        k = (i + 1) % sides
        out.append(ck.Poly([rings[-1][i], rings[-1][k], tip], "cypress_lt" if i % 2 else "cypress"))
        out.append(ck.Poly([rings[0][k], rings[0][i], Vector((0.0, 0.0, 0.72))], "cypress_dk"))

    return out


def lemon():
    out = ck.Part()
    tones = ("leaf_lt", "leaf", "leaf_dk")
    out += limb([(0, 0, 0), (0.07, 0.0, 0.7), (-0.03, 0.02, 1.4), (0.0, 0.0, 2.1)], [0.22, 0.15, 0.12, 0.07], 6, "trunk", 2)
    out += limb([(0.0, 0.0, 1.2), (-0.55, 0.1, 1.8), (-0.85, 0.1, 2.3)], [0.1, 0.07, 0.03], 4, "trunk", 3, d=1)
    out += limb([(0.02, 0.0, 1.35), (0.5, -0.12, 1.95), (0.85, -0.15, 2.45)], [0.1, 0.07, 0.03], 4, "trunk", 4, d=1)
    blobs = [((0.0, 0.0, 3.0), (0.95, 0.85, 0.78)), ((-0.82, 0.08, 2.5), (0.68, 0.7, 0.56)), ((0.84, -0.1, 2.55), (0.68, 0.7, 0.56)), ((0.15, 0.55, 2.5), (0.66, 0.5, 0.52)), ((-0.15, -0.55, 2.4), (0.66, 0.52, 0.5))]

    for k, (at, size) in enumerate(blobs):
        out += clump(at, size, tones, 50 + k, flat=0.75, jitter=0.15)

    for k in range(16):
        at, size = blobs[k % len(blobs)]
        a = k * 2.4
        e = -0.35 + 0.9 * ck.hash01(k, 6.0)
        p = (at[0] + math.cos(a) * math.cos(e) * size[0] * 0.98, at[1] + math.sin(a) * math.cos(e) * size[1] * 0.98, at[2] + math.sin(e) * size[2] * 0.9)
        out += gem(p, 0.12, 0.15, "lemon" if k % 3 else "lemon_dk")

    return out


def pine():
    out = ck.Part()
    tones = ("pine_lt", "pine", "pine_dk")
    out += limb([(0, 0, 0), (0.18, 0.0, 1.1), (0.02, 0.0, 2.6), (-0.2, 0.0, 3.8), (-0.05, 0.0, 5.0), (0.0, 0.0, 6.0)], [0.4, 0.28, 0.23, 0.2, 0.15, 0.08], 7, "trunk", 4)

    for k, (a, b) in enumerate((((-0.18, 0, 3.6), (-2.2, 0.45, 5.15)), ((-0.1, 0, 4.2), (2.1, -0.55, 5.3)), ((-0.1, 0, 4.4), (0.85, 1.7, 5.6)), ((-0.15, 0, 4.0), (-0.65, -1.7, 5.4)))):
        mid = Vector(a).lerp(Vector(b), 0.55) + Vector((0, 0, -0.18))
        out += limb([a, tuple(mid), b], [0.13, 0.09, 0.04], 4, "trunk", 60 + k)

    pads = [((0.0, 0.0, 6.25), (2.0, 1.8, 0.7)), ((-2.35, 0.5, 5.4), (1.25, 1.15, 0.48)), ((2.28, -0.6, 5.55), (1.32, 1.22, 0.5)), ((0.9, 2.0, 5.85), (1.25, 1.14, 0.48)), ((-0.65, -2.0, 5.65), (1.3, 1.12, 0.48)), ((1.3, 0.95, 6.35), (1.1, 1.0, 0.45)), ((-1.35, -0.55, 6.15), (1.15, 1.05, 0.46))]

    for k, (at, size) in enumerate(pads):
        out += clump(at, size, tones, 70 + k, flat=0.42, jitter=0.17, d=2 if k < 5 else 1)

    return out


def bush():
    tones = ("sage_lt", "sage", "sage_dk")
    out = clump((0.0, 0.0, 0.6), (0.78, 0.72, 0.74), tones, 90, flat=0.82, jitter=0.16)

    for k, (at, s) in enumerate((((-0.68, 0.15, 0.36), 0.4), ((0.66, -0.1, 0.4), 0.43), ((0.25, 0.5, 0.35), 0.38), ((-0.3, -0.52, 0.33), 0.37), ((0.35, -0.2, 1.0), 0.34))):
        out += clump(at, (s, s * 0.95, s * 0.9), tones, 91 + k, sub=0, flat=0.85, d=2 if k < 2 else 1)

    return out


def rbush():
    out = ck.Part()
    sets = (((-0.52, 0.05, 0.5), (0.62, 0.6, 0.6)), ((0.42, -0.08, 0.55), (0.68, 0.64, 0.62)), ((0.05, 0.35, 0.65), (0.52, 0.45, 0.5)), ((-0.08, -0.38, 0.35), (0.48, 0.42, 0.4)))

    for k, (at, size) in enumerate(sets):
        tones = ("leaf_lt", "leaf", "leaf_dk") if k % 2 else ("sage_lt", "leaf", "leaf_dk")
        out += clump(at, size, tones, 100 + k, flat=0.8, jitter=0.13, d=2 if k < 2 else 1)

    for k, (at, s) in enumerate((((-1.0, -0.1, 0.25), 0.26), ((0.98, 0.18, 0.28), 0.28), ((0.65, -0.52, 0.22), 0.24), ((-0.45, 0.45, 0.85), 0.28), ((0.3, -0.05, 0.98), 0.24))):
        out += clump(at, (s, s * 0.95, s * 0.85), ("leaf_lt", "leaf", "leaf_dk"), 110 + k, sub=0, flat=0.85, d=1)

    return out


def shrub():
    out = ck.box(-0.62, -0.62, 0.0, 0.62, 0.62, 0.17, "stone", c=0.05, skip="d")
    out += ck.box(-0.5, -0.5, 0.17, 0.5, 0.5, 0.2, "soil", skip="d")
    tones = ("leaf_lt", "leaf", "leaf_dk")
    out += ck.bar((0, 0, 0.18), (0, 0, 0.5), 0.08, "trunk", sides=4, caps=(False, False), d=2)
    out += ck.blob((0.0, 0.0, 0.78), (0.56, 0.54, 0.5), tones, sub=1, jitter=0.1, seed=120)

    for k in range(6):
        a = k * 1.05 + 0.4
        out += ck.blob((math.cos(a) * 0.4, math.sin(a) * 0.4, 0.62 + 0.38 * (k % 2)), (0.25, 0.25, 0.22), tones, sub=0, jitter=0.1, seed=121 + k, d=1)

    out += ck.blob((0.05, -0.03, 1.15), (0.28, 0.28, 0.2), tones, sub=0, jitter=0.1, seed=130, d=1)

    return out


def bougain():
    out = ck.Part()
    out += limb([(0.05, 0.0, 0.0), (-0.07, 0.03, 0.55), (0.06, 0.0, 1.15), (-0.06, 0.04, 1.7), (-0.35, 0.05, 2.35), (-0.9, 0.06, 2.75)], [0.12, 0.09, 0.08, 0.065, 0.045, 0.025], 5, "trunk", 5)
    out += limb([(-0.1, -0.02, 0.0), (0.05, -0.04, 0.6), (-0.07, 0.0, 1.2), (0.3, 0.05, 2.0), (0.85, 0.07, 2.55), (1.6, 0.07, 2.6)], [0.09, 0.07, 0.06, 0.05, 0.035, 0.02], 5, "trunk", 6)
    out += limb([(-0.35, 0.05, 2.35), (-0.15, 0.06, 2.9), (0.2, 0.06, 3.2)], [0.035, 0.025, 0.015], 4, "trunk", 7, d=1)
    out += limb([(-0.07, 0.03, 1.5), (-0.8, 0.07, 1.85), (-1.55, 0.07, 1.95)], [0.035, 0.022, 0.012], 4, "trunk", 8)
    spots = [(-0.95, 2.82), (-0.35, 3.0), (0.25, 3.18), (0.85, 2.82), (1.5, 2.72), (-1.5, 2.42), (-1.7, 1.95), (-1.05, 2.05), (0.35, 2.42), (1.92, 2.3), (-0.35, 2.52), (1.1, 2.25), (-0.7, 1.55), (0.55, 1.75), (1.72, 1.75), (0.0, 2.72), (-1.82, 2.5), (0.75, 3.12)]

    for k, (x, z) in enumerate(spots):
        bloom = k % 3 != 2
        tones = ("bloom_lt", "bloom", "bloom_dk") if bloom else ("leaf_lt", "leaf", "leaf_dk")
        s = 0.34 + 0.1 * ck.hash01(k, 8.0)
        out += ck.blob((x, 0.01 * (k % 3), z), (min(s, 0.34 if abs(x) > 1.7 else s), 0.19, s * 0.78), tones, sub=1 if k < 5 else 0, jitter=0.24, seed=140 + k, d=2 if k < 8 else 1)
        out += ck.blob((x + 0.24 * (-1) ** k, -0.07, z - 0.24), (0.17, 0.11, 0.14), ("leaf_lt", "leaf", "leaf_dk") if bloom else ("bloom_lt", "bloom", "bloom_dk"), sub=0, jitter=0.2, seed=170 + k, d=0)

    return out


def geranium():
    out = ck.box(-0.27, -0.24, 0.0, 0.27, 0.24, 0.6, "ochre", c=0.03, skip="dt")
    out += ck.box(-0.29, -0.26, 0.57, 0.29, 0.26, 0.63, "steel", c=0.018, d=1)
    out += ck.box(-0.285, -0.255, 0.0, 0.285, 0.255, 0.05, "steel", c=0.012, d=0, skip="dt")

    for y in (-0.243, 0.243):
        for x0, x1, z0, z1, col in ((-0.19, 0.19, 0.13, 0.47, "canvas"), (-0.13, 0.13, 0.31, 0.38, "terra"), (-0.13, 0.13, 0.2, 0.25, "teal")):
            if ck.LOD < 2 or z1 - z0 > 0.2:
                off = y + (-0.002 if y < 0 else 0.002) * (1 if col == "canvas" else 2)
                pts = [(x0, off, z0), (x1, off, z0), (x1, off, z1), (x0, off, z1)]
                out.append(ck.Poly(pts if y < 0 else pts[::-1], col, False, True, False))

    tones = ("leaf_lt", "leaf", "leaf_dk")

    for k, (x, y, z, s) in enumerate(((0.0, 0.0, 0.73, 0.24), (-0.2, 0.08, 0.68, 0.17), (0.2, -0.07, 0.7, 0.18), (0.08, 0.14, 0.78, 0.15), (-0.1, -0.15, 0.74, 0.16))):
        out += ck.blob((x, y, z), (s, s, s * 0.7), tones, sub=0, jitter=0.2, seed=200 + k, d=2 if k < 3 else 1)

    for k, (x, y, z) in enumerate(((-0.22, -0.1, 0.9), (0.02, 0.02, 1.07), (0.24, 0.05, 0.93), (0.1, -0.2, 0.86), (-0.12, 0.17, 0.96))):
        out += ck.bar((x * 0.4, y * 0.4, 0.68), (x, y, z), 0.012, "leaf_dk", sides=3, d=0, caps=(False, False))
        out += ck.blob((x, y, z + 0.02), (0.1, 0.1, 0.075), ("red_lt", "red", "red"), sub=0, jitter=0.22, seed=210 + k, d=2)

    return out


def basil():
    out = ck.lathe([(0.2, 0.0, "clay_dk"), (0.25, 0.06, "clay"), (0.34, 0.42, "clay"), (0.355, 0.43, "wall"), (0.365, 0.52, "wall"), (0.3, 0.53, "soil")], 10, smooth=False)
    out.append(ck.Poly([(p[0], p[1], 0.53) for p in ck.ngon(0.3, 10, phase=0.0)], "soil"))
    tones = ("leaf_lt", "leaf", "leaf_dk")
    out += ck.blob((0.0, 0.0, 0.7), (0.3, 0.3, 0.25), tones, sub=1, jitter=0.17, seed=220, flat=0.8)

    for k in range(6):
        a = k * 1.07
        out += ck.blob((math.cos(a) * 0.23, math.sin(a) * 0.23, 0.64 + 0.1 * (k % 2)), (0.13, 0.13, 0.11), tones, sub=0, jitter=0.2, seed=221 + k, d=1)

    return out


def boulder(at, size, seed, d=2, sub=1):
    return ck.blob(at, size, ("rock_lt", "rock", "rock_dk"), sub=sub, jitter=0.17, seed=seed, flat=0.62, d=d)


def rock():
    out = boulder((0.28, 0.0, 0.58), (0.9, 0.78, 0.95), 301)
    out += boulder((-0.68, 0.1, 0.34), (0.52, 0.55, 0.62), 302)
    out += boulder((-0.1, -0.55, 0.15), (0.34, 0.28, 0.3), 303, d=1, sub=0)
    out += boulder((0.92, -0.38, 0.14), (0.24, 0.26, 0.24), 304, d=0, sub=0)
    out += ck.blob((-0.5, -0.38, 0.04), (0.3, 0.22, 0.14), ("sage_lt", "sage", "sage_dk"), sub=0, seed=305, flat=0.3, d=0)

    return out


def crag(at, r, h, seed, sides=7):
    out = ck.Part()
    rnd = random.Random(seed)
    n = sides if ck.LOD == 0 else 5 if ck.LOD == 1 else 4
    levels = ((0.0, 1.0), (0.38, 0.86), (0.72, 0.56), (1.0, 0.14)) if ck.LOD < 2 else ((0.0, 1.0), (0.6, 0.68), (1.0, 0.14))
    lean = (rnd.uniform(-0.22, 0.22) * r, rnd.uniform(-0.22, 0.22) * r)
    rings = []
    phase = rnd.uniform(0, 6.28)

    for j, (t, k) in enumerate(levels):
        ring = []

        for i in range(n):
            a = phase + 2 * math.pi * (i + (0.3 if j % 2 else 0.0)) / n
            rr = r * k * rnd.uniform(0.8, 1.12)
            z = at[2] + h * t + (rnd.uniform(-0.09, 0.09) * h if j else 0.0)
            ring.append(Vector((at[0] + lean[0] * t + math.cos(a) * rr, at[1] + lean[1] * t + math.sin(a) * rr, min(z, at[2] + h))))

        rings.append(ring)

    for j in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            a, b, c, d = rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]

            for tri in ((a, b, c), (a, c, d)):
                tone = ("rock", "rock_lt", "rock_dk", "rock")[int(ck.hash01(seed, i, j, tri[1].x) * 4) % 4]
                p = ck.Poly(list(tri), tone)

                if p.normal().z > 0.55:
                    p.col = ck.rgb("rock_lt")

                out.append(p)

    top = ck.Poly(rings[-1], "rock_lt")
    out.append(top)

    return out


def outcrop():
    out = crag((0.0, 0.15, 0.0), 1.15, 3.26, 401, 8)
    out += crag((-1.05, -0.3, 0.0), 0.82, 1.85, 402)
    out += crag((1.05, 0.25, 0.0), 0.85, 1.55, 403)
    out += crag((0.45, -1.05, 0.0), 0.72, 1.15, 404, 6)
    out += crag((-0.55, 1.05, 0.0), 0.75, 1.3, 405, 6)

    for k, (x, y, s) in enumerate(((1.45, -0.9, 0.42), (-1.45, 0.75, 0.38), (-0.5, -1.45, 0.34), (1.35, 1.25, 0.4))):
        out += boulder((x, y, s * 0.4), (s, s, s * 0.8), 410 + k, d=1, sub=0)

    for k, (x, y, z, s) in enumerate(((-0.9, -1.15, 0.12, 0.32), (1.65, -0.15, 0.14, 0.28), (-0.35, -0.6, 1.2, 0.22))):
        out += ck.blob((x, y, z), (s, s, s * 0.6), ("sage_lt", "sage", "sage_dk"), sub=0, seed=420 + k, d=0)

    return out


def stone(x0, x1, hy0, hy1, z0, z1, seed):
    out = ck.Part()
    tone = ("wall_stone", "wall_stone", "wall_stone_dk", "wall_stone_warm", "wall_stone_lt", "wall_stone_dk")[int(ck.hash01(seed, 1.0) * 6) % 6]
    j = [(ck.hash01(seed, k, 2.0) - 0.5) * 0.07 for k in range(8)]
    cx0, cx1 = x0 + 0.012, x1 - 0.012
    zt0, zt1 = z1 + j[0] * 0.8, z1 + j[1] * 0.8

    for s in (-1, 1):
        y_out = s * (hy0 + j[2 if s < 0 else 3] * 0.9)
        y_in = s * (hy0 - 0.075)
        rim = [(cx0, y_in, z0), (cx1, y_in, z0), (cx1, y_in, zt1), (cx0, y_in, zt0)]
        face = [(cx0 + 0.07, y_out, z0 + 0.055), (cx1 - 0.07, y_out, z0 + 0.055 + j[4] * 0.5), (cx1 - 0.075, y_out, zt1 - 0.06), (cx0 + 0.065, y_out, zt0 - 0.06)]

        if ck.LOD == 1:
            flat = [(cx0, s * hy0, z0), (cx1, s * hy0, z0), (cx1, s * hy0, zt1), (cx0, s * hy0, zt0)]
            out.append(ck.Poly(flat if s < 0 else flat[::-1], tone))
            continue

        out.append(ck.Poly(face if s < 0 else face[::-1], tone))

        for i in range(4):
            k = (i + 1) % 4
            q = [rim[i], rim[k], face[k], face[i]]
            out.append(ck.Poly(q if s < 0 else q[::-1], ck.shade(tone, 1.04 if i == 2 else 0.94)))

    depth = hy0 - 0.075 if ck.LOD == 0 else hy0
    out.append(ck.Poly([(cx0, -depth, zt0), (cx1, -depth, zt1), (cx1, depth, zt1), (cx0, depth, zt0)], ck.shade(tone, 1.07)))

    if ck.LOD == 0 or x0 <= -1.99:
        out.append(ck.Poly([(cx0, -depth, z0), (cx0, -depth, zt0), (cx0, depth, zt0), (cx0, depth, z0)], tone, False, True, False))

    if ck.LOD == 0 or x1 >= 1.99:
        out.append(ck.Poly([(cx1, depth, z0), (cx1, depth, zt1), (cx1, -depth, zt1), (cx1, -depth, z0)], tone, False, True, False))

    return out


def swall():
    out = ck.Part()

    if ck.LOD >= 2:
        out += ck.box(-2.0, -0.33, 0.0, 2.0, 0.33, 0.62, "wall_stone_dk", skip="d")
        out += ck.box(-1.98, -0.28, 0.62, 1.98, 0.28, 1.24, "wall_stone", skip="d", taper=(1.0, 0.85))

        return out

    courses = ((0.0, 0.34, 0.385, 5), (0.34, 0.62, 0.355, 6), (0.62, 0.9, 0.33, 5), (0.9, 1.12, 0.3, 6))

    for r, (z0, z1, hy, n) in enumerate(courses):
        cuts = [-2.0]
        lift = [0.0]

        for i in range(1, n):
            cuts.append(-2.0 + 4.0 * (i + (ck.hash01(r, i, 4.0) - 0.5) * 0.8) / n)

        cuts.append(2.0)

        for i in range(n):
            wob = (ck.hash01(r, i, 6.0) - 0.5) * 0.07 if r < 3 else (ck.hash01(r, i, 6.0) - 0.5) * 0.1
            out += stone(cuts[i], cuts[i + 1], hy, hy, z0, z1 + wob, r * 17 + i + 1)

    if ck.LOD == 0:
        out += ck.box(-1.94, -0.2, 0.0, 1.94, 0.2, 1.02, "shadow", skip="dt")

    x = -1.98
    k = 0

    while x < 1.9:
        w = min(0.26 + 0.2 * ck.hash01(k, 9.0), 1.98 - x)

        if 1.98 - x - w < 0.18:
            w = 1.98 - x

        h = 0.14 + 0.13 * ck.hash01(k, 11.0)
        tone = ("wall_stone", "wall_stone_dk", "wall_stone_lt", "wall_stone", "wall_stone_warm")[k % 5]

        if ck.LOD == 0 or k % 2 == 0:
            grow = 1.0 if ck.LOD == 0 else 1.7
            out += ck.box(x + 0.012, -0.25, 1.08, min(1.98, x + w * grow) - 0.012, 0.25, 1.09 + h, tone, skip="d", taper=(0.82, 0.72), shear=((ck.hash01(k, 13.0) - 0.5) * 0.16, 0.0))

        x += w
        k += 1

    return out


def hay():
    out = ck.box(-0.7, -0.35, 0.0, 0.7, 0.35, 0.8, "straw", c=0.11, top="straw_lt", skip="d")

    for x in (-0.38, 0.38):
        out += ck.box(x - 0.045, -0.365, 0.0, x + 0.045, 0.365, 0.82, "umber", c=0.11, d=1, skip="d")

    for s in (-1, 1):
        for k, (half, col) in enumerate(((0.25, "straw_dk"), (0.17, "straw"), (0.09, "straw_dk"))):
            if ck.LOD == 0 or (ck.LOD == 1 and k == 0):
                x = s * (0.703 + 0.007 * k)
                pts = [(x, -half, 0.4 - half), (x, half, 0.4 - half), (x, half, 0.4 + half), (x, -half, 0.4 + half)]
                out.append(ck.Poly(pts if s > 0 else pts[::-1], col, False, True, False))

    if ck.LOD == 0:
        for k in range(10):
            x = -0.58 + (k * 0.47) % 1.14
            y = -0.2 + (k * 0.29) % 0.4
            out += ck.box(x, y, 0.795, x + 0.16, y + 0.035, 0.822, "straw_lt" if k % 2 else "straw_dk", skip="d")

    return out


def haystack():
    n = 14 if ck.LOD == 0 else 9 if ck.LOD == 1 else 6
    tiers = [(1.0, 0.0, 0.93, 0.5), (0.97, 0.44, 0.83, 0.94), (0.87, 0.88, 0.66, 1.32), (0.7, 1.27, 0.44, 1.62), (0.48, 1.57, 0.04, 1.82)]
    out = ck.Part()

    if ck.LOD >= 2:
        return ck.lathe([(0.98, 0.0, "straw_dk"), (0.9, 0.8, "straw"), (0.55, 1.5, "straw_lt"), (0.02, 1.845, "straw")], 7, smooth=False)

    for k, (rb, zb, rt, zt) in enumerate(tiers):
        low = []
        high = []

        for i in range(n):
            a = 2 * math.pi * i / n + k * 0.33
            f = 1.01 if i % 2 else 0.95
            low.append(Vector((math.cos(a) * rb * f, math.sin(a) * rb * f, max(0.0, zb + (0.0 if i % 2 else 0.05)))))
            high.append(Vector((math.cos(a) * rt, math.sin(a) * rt, zt)))

        for i in range(n):
            j = (i + 1) % n
            tone = ("straw", "straw_lt", "straw", "straw_dk")[int(ck.hash01(k, i, 15.0) * 4) % 4]
            out.append(ck.Poly([low[i], low[j], high[j], high[i]], tone))

            if k and ck.LOD < 2:
                out.append(ck.Poly([low[j], low[i], Vector((0, 0, zb + 0.12))], "straw_dk"))

    out += ck.bar((0, 0, 1.7), (0.03, 0.0, 1.845), 0.035, "wood_dk", sides=5, d=1)

    return out


PLANT = {"reach": 0.9, "ao": 0.45, "grime": 0.1, "grime_h": 0.5, "under": 0.1}
CANOPY = {"reach": 1.4, "ao": 0.42, "grime": 0.0, "under": 0.12, "speckle": 0.03}
STONE = {"reach": 0.8, "ao": 0.5, "grime": 0.16, "grime_h": 0.5}

ALL = {
    "olive": (olive, CANOPY),
    "cypress": (cypress, CANOPY),
    "lemon": (lemon, CANOPY),
    "pine": (pine, CANOPY),
    "bush": (bush, PLANT),
    "rbush": (rbush, PLANT),
    "shrub": (shrub, PLANT),
    "bougain": (bougain, {"reach": 0.7, "ao": 0.35, "grime": 0.0, "under": 0.08}),
    "geranium": (geranium, PLANT),
    "basil": (basil, PLANT),
    "rock": (rock, STONE),
    "outcrop": (outcrop, STONE),
    "swall": (swall, {"reach": 0.45, "ao": 0.5, "grime": 0.16, "grime_h": 0.45}),
    "hay": (hay, STONE),
    "haystack": (haystack, STONE),
}
