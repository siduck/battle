import math
import random

from mathutils import Vector

import ak
from ak import Part, tube, blob, prism, extrude, hash01
from kit import *

V = Vector


def tier(cx, cy, z, r, h, n, seed, rim, under, top, snow=True, droop=0.15, edge=0.11, green=0.0):
    part = Part()
    rnd = random.Random(seed)
    turn = rnd.uniform(0, 6.28)
    a, b, c = [], [], []

    for i in range(n):
        t = 2 * math.pi * i / n + turn
        tip = i % 2 == 0
        k = (1.0 if tip else 0.83) * rnd.uniform(0.93, 1.04)
        zz = z + (0.0 if tip else droop * h) + rnd.uniform(-0.02, 0.03) * h
        a.append(V((cx + math.cos(t) * r * k, cy + math.sin(t) * r * k, zz)))
        b.append(V((cx + math.cos(t) * r * k * 0.95, cy + math.sin(t) * r * k * 0.95, zz + edge * h)))
        c.append(V((cx + math.cos(t) * r * k * 0.56, cy + math.sin(t) * r * k * 0.56, z + h * (0.5 if tip else 0.55))))

    apex = V((cx, cy, z + h))
    hub = V((cx, cy, z + h * 0.34))

    def cap(i, j):
        if not snow:
            return top[(i + j + seed) % len(top)]

        if hash01(seed, i, j) < green:
            return rim

        return top[0] if (i + seed) % 3 else top[1]

    for i in range(n):
        k = (i + 1) % n
        part += poly([a[k], a[i], hub], under, out=(0, 0, -1))
        part += poly([a[i], a[k], b[k]], rim)
        part += poly([a[i], b[k], b[i]], rim)

        if ak.LOD == 0 or (ak.LOD == 1 and n > 7):
            part += poly([b[i], b[k], c[k]], cap(i, 0))
            part += poly([b[i], c[k], c[i]], cap(i, 0))
            part += poly([c[i], c[k], apex], cap(i, 1))
        else:
            part += poly([b[i], b[k], apex], cap(i, 0))

    return part


def conifer(cx, cy, h, r, base, tiers, n, seed, rim, under, top, snow=True, trunk=0.18, green=0.0):
    out = Part()
    n = (n, max(7, n - 4), 5 if n < 10 else 6)[ak.LOD]
    count = (tiers, tiers if n > 7 else tiers - 1, max(3, tiers - 2))[ak.LOD]
    out += tube([(cx, cy, 0), (cx, cy, base + h * 0.2)], [trunk, trunk * 0.7], (7, 5, 4)[ak.LOD], "bark_d", caps=(False, False), smooth=False)
    span = h - base
    th = span / (1 + (count - 1) * 0.56)

    for i in range(count):
        u = i / max(1, count - 1)
        rr = r * (1.0 - 0.7 * u)
        z = base + i * th * 0.56
        out += tier(cx, cy, z, rr, th * (1.0 if i < count - 1 else 1.02), n if i < count - 2 else max(6, n - 2), seed * 13 + i, rim, under, top, snow=snow, green=green)

    return out


def spruce():
    out = [conifer(0, 0, 6.05, 1.5, 0.82, 7, 14, 1, "pine_d", "pine_k", ("snow", "snow_s"), trunk=0.21, green=0.06)]
    out.append(mound((0.05, 0.0, 0.0), 1.18, 1.1, 0.24, seed=2))

    return out


def pine():
    out = [conifer(0, 0, 9.0, 1.82, 1.0, 7, 14, 4, "pine_l", "pine_d", ("pine", "pine"), snow=False, trunk=0.27)]

    return out


def pines():
    out = []

    for i, (x, y, h, r) in enumerate(((0.05, 0.55, 9.0, 1.12), (-1.15, -0.2, 6.9, 1.08), (1.1, 0.05, 6.2, 1.1), (-0.15, -1.0, 4.9, 1.04))):
        out.append(conifer(x, y, h, r, 0.7, 5 if i < 2 else 4, 9, 20 + i, ("pine", "pine_d", "pine", "pine_d")[i], "pine_k", (("pine_d", "pine_d"), ("pine_k", "pine_d"), ("pine_d", "pine"), ("pine", "pine_d"))[i], snow=False, trunk=0.14))
        out.append(mound((x + 0.1, y - 0.1, 0.0), 0.55, 0.5, 0.14, seed=i, n=8, d=1))


    out.append(rock((1.4, -1.25, 0), 0.26, 0.22, 0.24, seed=5, d=1))
    out.append(rock((-1.75, 1.2, 0), 0.3, 0.24, 0.26, seed=8, d=1))

    return out


def limb(pts, r0, r1, col, sides, d=None, snow=0.0, seed=0):
    out = Part()

    if d is not None and ak.LOD > d:
        return out

    pts = [V(p) for p in pts]
    n = len(pts)
    radii = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    out += tube(pts, radii, (sides, max(3, sides - 2), 3)[ak.LOD], col, caps=(False, True), smooth=False, d=2)

    if snow and ak.LOD == 0:
        for i in range(n - 1):
            if hash01(seed, i, 3) < snow:
                a = pts[i].lerp(pts[i + 1], 0.12)
                b = pts[i].lerp(pts[i + 1], 0.88)
                lift = V((0, 0, radii[i] * 0.85))
                w = radii[i] * 1.12 + 0.008
                out += tube([a + lift, a.lerp(b, 0.5) + lift * 1.3, b + lift * 0.9], [w * 0.4, w, w * 0.3], 5, "snow", caps=(True, True), smooth=False, squash=(1.0, 0.75))

    return out


def larch():
    out = []
    trunk = [(-2.75, -1.0, 0.0), (-2.95, -1.05, 1.2), (-2.85, -1.08, 2.6), (-2.45, -1.05, 3.9), (-1.75, -0.95, 5.0), (-0.85, -0.85, 5.9), (0.3, -0.75, 6.35)]
    out.append(limb(trunk, 0.34, 0.07, "bark_d", 7, snow=0.5, seed=77))

    if ak.LOD == 0:
        for z in (0.6, 1.5, 2.4, 3.2):
            out.append(rock((-3.17 + max(0, z - 2.4) * 0.45, -1.05, z), 0.14, 0.16, 0.2, seed=int(z * 7), tones=("snow", "snow_s", "snow"), cap=False, n=5))

    arms = (
        [(-2.8, -1.07, 2.7), (-1.5, -1.2, 3.15), (0.0, -1.3, 3.2), (1.7, -1.5, 3.0), (3.9, -1.6, 2.85)],
        [(-2.55, -1.05, 3.6), (-1.1, -0.35, 4.05), (0.7, 0.35, 4.2), (2.4, 1.1, 3.95), (3.9, 1.65, 3.7)],
        [(-2.0, -1.0, 4.6), (-0.5, -1.15, 5.05), (1.3, -1.05, 5.1), (2.8, -0.9, 4.9), (3.9, -0.8, 4.7)],
        [(-1.3, -0.9, 5.45), (0.4, -0.2, 6.0), (1.7, 0.2, 6.05), (2.9, 0.55, 5.8)],
        [(-0.85, -0.85, 5.9), (0.5, -1.35, 6.65), (1.8, -1.55, 6.9), (2.85, -1.6, 6.75)],
        [(-2.75, -1.08, 3.0), (-3.35, -0.2, 3.9), (-3.0, 0.7, 4.45), (-2.2, 1.55, 4.55)],
        [(-2.1, -1.0, 4.4), (-2.5, -1.5, 5.4), (-1.8, -1.65, 6.2), (-0.7, -1.6, 6.7)],
    )

    for i, a in enumerate(arms):
        out.append(limb(a, 0.15 - 0.006 * i, 0.02, "bark_g" if i % 2 else "bark_d", 5, snow=1.0, seed=i))

        for j in range(1, len(a) - 1):
            p = V(a[j])
            s = 1 if (i + j) % 2 else -1
            q = p + V((0.85, s * 0.45, 0.12 + 0.2 * hash01(i, j)))
            q.y = max(-1.75, min(1.75, q.y))
            q.x = min(3.95, q.x)
            q.z = min(6.97, q.z)
            out.append(limb([p, p.lerp(q, 0.55) + V((0, 0, 0.1)), q], 0.05, 0.012, "bark_d", 3, d=1, snow=0.45, seed=i * 9 + j))

    out.append(mound((-2.35, -0.85, 0.0), 1.5, 0.9, 0.3, seed=4))

    return out


def rowan():
    out = [limb([(0.05, 0.1, 0), (-0.05, 0.05, 1.0), (0.02, 0.0, 1.55)], 0.2, 0.15, "bark_g", 7)]
    rnd = random.Random(7)
    mains = ((-1.45, -0.7, 3.1), (1.5, 0.35, 3.25), (-0.35, 1.45, 3.7), (0.55, -1.2, 3.9), (-0.6, 0.1, 4.6), (0.65, 0.7, 4.45))

    for i, (x, y, z) in enumerate(mains):
        a = V((0.02, 0.0, 1.15 + 0.1 * (i % 4)))
        e = V((x, y, z))
        m = a.lerp(e, 0.5) + V((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0.22))
        out.append(limb([a, m, e], 0.1, 0.035, "bark_g", 5, snow=0.75, seed=i))

        for j, u in enumerate((0.45, 0.75, 1.0)):
            p = a.lerp(m, u * 2) if u <= 0.5 else m.lerp(e, (u - 0.5) * 2)
            dx, dy = x * 0.45 + rnd.uniform(-0.55, 0.55), y * 0.45 + rnd.uniform(-0.55, 0.55)
            q = p + V((dx, dy, rnd.uniform(0.3, 0.7)))
            q.x = max(-2.16, min(2.16, q.x))
            q.y = max(-2.13, min(2.13, q.y))
            q.z = min(5.0, q.z)
            mid = p.lerp(q, 0.5) + V((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.06))
            out.append(limb([p, mid, q], 0.04, 0.01, "bark_g", 3, d=1, snow=0.6, seed=i * 7 + j))

            if (i + j) % 2 == 0 and ak.LOD == 0:
                for k in range(3):
                    off = V((rnd.uniform(-0.09, 0.09), rnd.uniform(-0.09, 0.09), -0.07 - 0.04 * k))
                    out.append(blob(q + off, (0.055, 0.055, 0.055), "red" if k else "red_d", sub=0, seed=i * 11 + j + k, d=0))

            tw = q + V((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0.15, 0.4)))
            tw.z = min(5.03, tw.z)
            tw.x = max(-2.18, min(2.18, tw.x))
            tw.y = max(-2.15, min(2.15, tw.y))
            out.append(limb([mid, tw], 0.022, 0.008, "bark_d", 3, d=0))

    out.append(mound((0.05, 0.1, 0.0), 0.85, 0.75, 0.2, seed=9))

    return out


def dwarf():
    out = [mound((0, 0, 0), 1.2, 1.15, 0.22, seed=3, col="snow_s")]
    spots = ((-0.82, -0.35, 0.62), (-0.55, 0.62, 0.72), (0.25, 0.8, 0.78), (0.82, 0.3, 0.6), (0.72, -0.6, 0.55), (-0.05, -0.82, 0.55), (-0.95, 0.2, 0.55), (0.1, 0.1, 0.8))

    for i, (x, y, z) in enumerate(spots):
        out.append(limb([(x * 0.35, y * 0.35, 0.05), (x * 0.8, y * 0.8, z * 0.75)], 0.075, 0.045, "bark_d", 5, d=1))
        out.append(blob((x, y, z), (0.43 if i < 7 else 0.5, 0.4, 0.28), ("pine", "pine_d", "pine_k"), sub=1 if i % 3 == 0 else 0, jitter=0.2, seed=i + 3, flat=0.55))

        if ak.LOD == 0:
            out.append(blob((x * 1.04 + 0.2, y * 1.04 - 0.16, z - 0.1), (0.24, 0.22, 0.17), ("pine_l", "pine", "pine_d"), sub=0, jitter=0.2, seed=i + 30))

    out.append(rock((0.05, 0.02, 0.72), 0.82, 0.7, 0.36, seed=6, tones=("snow_s", "snow_s", "snow"), top=0.55, n=9))

    for i, (x, y, z) in enumerate(((-0.75, -0.2, 0.8), (0.68, 0.42, 0.82), (0.5, -0.55, 0.72), (-0.35, 0.66, 0.94))):
        out.append(mound((x, y, z), 0.34, 0.3, 0.2, seed=i + 8, n=8, d=1))

    return out


def outcrop():
    t = ("rock", "rock_d", "rock_l")
    out = [rock((0.0, 0.05, 0.0), 0.7, 0.68, 1.82, seed=3, tones=("rock_d", "rock_d", "rock"), top=0.3, n=7)]

    for i, (x, y, z, rx, ry, h) in enumerate(((-0.7, -0.2, 0.0, 0.48, 0.46, 1.02), (0.62, 0.22, 0.0, 0.46, 0.5, 1.22), (0.18, -0.68, 0.0, 0.5, 0.42, 0.7), (-0.28, 0.72, 0.0, 0.55, 0.42, 0.82), (0.85, -0.52, 0.0, 0.34, 0.34, 0.52), (-0.88, 0.55, 0.0, 0.32, 0.34, 0.45), (-0.45, -0.86, 0.0, 0.3, 0.28, 0.34))):
        out.append(rock((x, y, z), rx, ry, h, seed=i + 11, tones=t, n=7 if i < 4 else 6, d=1 if i > 4 else None))

    out.append(rock((0.1, -1.0, 0), 0.2, 0.18, 0.18, seed=40, d=0))
    out.append(mound((0.0, 0.0, 0.0), 1.14, 1.12, 0.14, seed=1, col="snow_s", d=1))

    return out


def boulders():
    t = ("rock", "rock_d", "rock_l")
    out = [mound((0, 0, 0), 1.24, 0.99, 0.18, seed=5, n=12)]

    for i, (x, y, rx, ry, h) in enumerate(((0.16, 0.3, 0.38, 0.36, 1.38), (-0.5, 0.18, 0.36, 0.34, 1.06), (0.66, -0.05, 0.34, 0.34, 0.8), (-0.05, -0.3, 0.26, 0.25, 0.68), (0.4, -0.52, 0.3, 0.28, 0.46), (-0.62, -0.4, 0.24, 0.22, 0.4), (-0.28, -0.6, 0.17, 0.16, 0.3))):
        out.append(rock((x, y, 0.04), rx, ry, h, seed=i + 21, tones=t, top=0.74, n=7 if i < 3 else 6, d=1 if i > 4 else None))

    for i, (x, y) in enumerate(((-0.95, -0.05), (0.95, 0.3), (0.85, -0.6))):
        out.append(rock((x, y, 0.05), 0.13, 0.12, 0.14, seed=i + 50, d=0))

    return out


def slab():
    out = [rock((0.0, 0.0, 0.0), 1.05, 0.66, 0.52, seed=9, tones=("rock_w", "rock", "rock_l"), top=0.78, n=11)]
    out.append(rock((-0.82, -0.42, 0.0), 0.24, 0.2, 0.24, seed=14, d=1))
    out.append(rock((0.78, 0.44, 0.0), 0.28, 0.2, 0.2, seed=17, d=1))

    for i, (x, y, z, rx) in enumerate(((0.45, -0.6, 0.12, 0.28), (-0.5, -0.55, 0.06, 0.2), (0.96, -0.15, 0.2, 0.16))):
        out.append(blob((x, y, z), (rx, 0.09, rx * 0.5), ("moss", "moss", "green_d"), sub=0, jitter=0.25, seed=i, d=0))

    return out


def scree():
    out = [mound((0, 0, 0), 1.24, 1.22, 0.22, seed=8, col="snow_s", n=12)]
    rnd = random.Random(12)
    for i in range((24, 14, 8)[ak.LOD]):
        a = i * 2.399963
        d = 1.04 * math.sqrt((i + 0.5) / (24, 14, 8)[ak.LOD])
        x, y = math.cos(a) * d, math.sin(a) * d
        z = 0.2 * (1 - d / 1.25) + 0.02
        s = rnd.uniform(0.15, 0.27) * (1.15 - d * 0.3) * (1.0, 1.2, 1.4)[ak.LOD]
        out.append(rock((x, y, z), s, s * rnd.uniform(0.75, 1.0), s * rnd.uniform(0.8, 1.2), seed=i + 60, tones=("rock", "rock_l", "stone"), cap=i % 4 == 1, n=5, top=0.65))

    return out


def slab_stone(x, y, z, r, h, seed, col):
    rnd = random.Random(seed)
    n = (7, 6, 5)[ak.LOD]
    turn = rnd.uniform(0, 1.0)
    pts = [(x + math.cos(2 * math.pi * i / n + turn) * r * rnd.uniform(0.86, 1.08), y + math.sin(2 * math.pi * i / n + turn) * r * rnd.uniform(0.82, 1.0)) for i in range(n)]

    return prism(pts, z, z + h, col, c=min(0.045, h * 0.3), top=("stone_l" if col != "snow" else col), bottom=True)


def cairn():
    out = []
    z = 0.0
    sizes = (0.49, 0.45, 0.41, 0.37, 0.33, 0.29, 0.26)

    if ak.LOD == 2:
        out.append(rock((0, 0, 0), 0.46, 0.46, 1.1, seed=2, top=0.5, n=6, cap=False))
        z = 1.1

    for i, r in enumerate(sizes if ak.LOD < 2 else ()):
        h = 0.17 - i * 0.004
        out.append(slab_stone(0.035 * math.sin(i * 2.1), 0.035 * math.cos(i * 1.7), z, r * 0.92, h - 0.008, i + 5, ("stone", "stone_d", "rock_l")[i % 3]))

        if i < 3 and ak.LOD == 0:
            for k in range(2):
                a = i * 2.3 + k * 3.0
                out.append(rock((math.cos(a) * r * 0.78, math.sin(a) * r * 0.78, z), 0.11, 0.1, 0.11, seed=i * 5 + k, cap=False, n=5))

        z += h

    out.append(slab_stone(0.0, 0.0, z - 0.01, 0.32, 0.16, 30, "snow"))
    out.append(mound((0.0, 0.0, 0.0), 0.5, 0.5, 0.1, seed=3, d=1))

    return out


def falls():
    out = []
    shape = [(-1.34, 0.0), (1.34, 0.0), (1.22, 2.1), (1.3, 3.45), (0.9, 3.8), (0.35, 3.6), (-0.35, 3.64), (-0.92, 3.86), (-1.28, 3.42), (-1.2, 1.9)]
    out.append(extrude(shape, 0.02, 0.42, "snow_s", side="snow", force=True))

    for face_, base_y, k in ((-1, 0.02, 0), (1, 0.42, 1)):
        reach = 1.0 if face_ < 0 else 0.85

        for i, x in enumerate((-0.9, -0.62, -0.34, -0.04, 0.28, 0.58, 0.88)):
            r = 0.14 + 0.07 * hash01(i, 5, k)
            b = (0.2 + 0.1 * hash01(i, 9, k)) * reach
            h = 3.3 + 0.2 * hash01(i, 2, k)
            col = ("ice", "snow_s", "ice_m", "ice", "snow_d", "ice_m", "ice")[(i + k * 3) % 7]
            y = lambda o: base_y + face_ * o
            out.append(tube([(x * 1.13, y(b + 0.12), 0.1), (x * 1.04, y(b * 0.35), 0.95), (x, y(0.07), 2.1), (x * 0.96, y(0.05), h)], [r * 1.45, r * 0.75, r, r * 0.85], (7, 5, 4)[ak.LOD], col, caps=(False, True), smooth=False))

        for i in range(8):
            x = -0.96 + i * 0.27
            z = 3.42 - 0.14 * hash01(i, 3, k)
            ln = 0.5 + 1.1 * hash01(i, 7, k)
            y = base_y + face_ * (0.2 + 0.07 * hash01(i, 1, k))
            out.append(tube([(x, y, z), (x, y - face_ * 0.04, z - ln)], [0.085, 0.008], (5, 4, 3)[ak.LOD], ("ice", "snow_w", "ice_m")[i % 3], caps=(True, False), smooth=False, d=1))

    for i, x in enumerate((-0.74, -0.26, 0.24, 0.72)):
        out.append(tube([(x, 0.72, 3.15), (x, 0.55, 3.56), (x, 0.22, 3.68 + 0.08 * (i % 2)), (x, -0.1, 3.54), (x, -0.2, 3.18)], [0.08, 0.22, 0.27, 0.22, 0.08], (7, 5, 4)[ak.LOD], "snow" if i % 2 else "snow_w", caps=(True, True), smooth=False, squash=(1.15, 0.8)))

    t = ("stone", "stone_l", "rock_l")

    for s in (-1, 1):
        for i, (x, z, rx, ry, h) in enumerate(((1.4, 0.0, 0.46, 0.7, 1.7), (1.36, 1.5, 0.42, 0.55, 1.4), (1.1, 2.75, 0.4, 0.5, 0.95), (1.75, 0.0, 0.42, 0.5, 0.8))):
            out.append(rock((s * x, 0.2, z), rx, ry, h, seed=i + (3 if s > 0 else 13), tones=("snow_s", "snow_d", "snow") if i % 2 else t, top=0.62, n=7))

    n = (14, 10, 7)[ak.LOD]
    rim = ring(2.18, 0.89, 0.02, n, 4, 0.05)
    mid = ring(1.55, 0.64, 0.15, n, 5, 0.08)
    out.append(loft([rim, mid], ["snow_d"], apex=(0.0, 0.0, 0.2), top=lambda i: "ice" if i % 3 else "snow_d"))

    for i, (x, y, r) in enumerate(((-0.66, -0.4, 0.28), (0.5, -0.5, 0.2), (0.82, 0.62, 0.3), (-0.4, 0.66, 0.22), (0.05, -0.55, 0.16))):
        out.append(rock((x, y, 0.08), r, r * 0.8, r * 1.2, seed=i + 80, tones=("snow", "snow_s", "ice"), cap=False, n=6, top=0.45, d=1 if i > 2 else None))

    return out


OPT = dict(errors=(0.008, 0.03), reach=1.1, ao=0.45, grime=0.06, grime_h=0.5, under=0.16)

ALL = {n: (f, dict(OPT)) for n, f in (("spruce", spruce), ("larch", larch), ("rowan", rowan), ("pine", pine), ("pines", pines), ("dwarf", dwarf), ("outcrop", outcrop), ("boulders", boulders), ("slab", slab), ("scree", scree), ("cairn", cairn), ("falls", falls))}
