import math

from mathutils import Vector

import ak
from ak import Part, box, cyl, tube, extrude, hash01
from kit import *

TIMBER = ("wood", "wood", "wood_d", "wood_l")
DARK = ("wood_d", "wood_d", "wood_k", "wood")
GREY = ("wood_g", "wood_g", "wood_gd")
SIDES = ("f", "r", "b", "l")


def on(side, dist, part, along=0.0, z=0.0):
    return face(part, side, dist, along, z)


def walls(hx, hy, z0, z1, fn, holes=None, y0=None):
    out = Part()
    holes = holes or {}

    for side in SIDES:
        span, dist = (hx, hy) if side in "fb" else (hy, hx)
        out += on(side, dist, fn(-span, span, z0, z1, holes.get(side, ()), SIDES.index(side)))

    return out


def hole(x, z, w, h, pad_=0.06):
    return (x - w / 2 - pad_, x + w / 2 + pad_, z - pad_, z + h + pad_)


def glazing(side, dist, items, **kw):
    out = Part()

    for x, z, w, h in items:
        out += on(side, dist, window(w, h, **kw), x, z)

    return out


def corner_posts(hx, hy, z0, z1, w, col):
    out = Part()

    for sx in (-1, 1):
        for sy in (-1, 1):
            out += box(sx * hx - w / 2, sy * hy - w / 2, z0, sx * hx + w / 2, sy * hy + w / 2, z1, col, c=0.04, skip="d")

    return out


def chalet():
    out = [plinth(-5.73, -4.38, 5.73, 4.58), plinth(-2.2, 4.5, 2.7, 5.08)]
    gx, gy = 5.36, 4.03
    wins = [(-3.3, 1.22, 1.24, 1.55), (3.3, 1.22, 1.24, 1.55)]
    side_w = [(-2.04, 1.22, 1.28, 1.55), (2.04, 1.22, 1.28, 1.55)]
    gholes = {"f": [hole(*w) for w in wins] + [(-0.8, 0.8, 0, 2.9)], "b": [hole(*w) for w in wins], "l": [hole(*w) for w in side_w], "r": [hole(*w) for w in side_w]}
    out.append(core(-gx, -gy, gx, gy, 0, 3.34, "plaster"))
    out.append(walls(gx, gy, 0.0, 0.62, lambda a, b, z0, z1, h, i: stones(a - 0.08, b + 0.08, z0, z1, rows=2, w=0.85, out=0.14, holes=h, seed=i), gholes))

    for sx in (-1, 1):
        for sy in (-1, 1):
            for i, z in enumerate((0.64, 1.26, 1.88, 2.5)):
                w = 0.62 if i % 2 == 0 else 0.46
                out.append(box(sx * (gx + 0.1) - sx * w, sy * (gy + 0.1) - sy * (1.08 - w), z, sx * (gx + 0.1), sy * (gy + 0.1), z + 0.52, "stone" if i % 2 else "stone_l", c=0.07))

    out.append(on("f", gy, door(1.34, 2.5, "wood", "wood_d"), 0, 0.12))
    out.append(on("f", gy, box(-1.0, -0.55, 0, 1.0, 0.0, 0.12, "stone_l", c=0.03, skip="b")))

    for side, dist, items in (("f", gy, wins), ("b", gy, wins), ("l", gx, side_w), ("r", gx, side_w)):
        out.append(glazing(side, dist, items, shutters="wood", frame="wood_l"))

    ux, uy = 5.4, 4.2
    uf = [(-3.17, 4.78, 1.3, 1.66), (3.17, 4.78, 1.3, 1.66), (0.0, 4.78, 1.3, 1.66)]
    ub = [(-3.17, 4.78, 1.3, 1.66), (3.17, 4.78, 1.3, 1.66)]
    us = [(-2.04, 4.74, 1.28, 1.56), (2.04, 4.74, 1.28, 1.56)]
    uholes = {"f": [hole(*w) for w in uf], "b": [hole(*w) for w in ub], "l": [hole(*w) for w in us], "r": [hole(*w) for w in us]}
    out.append(core(-ux + 0.01, -uy + 0.01, ux - 0.01, uy - 0.01, 3.34, 6.5, "wood_d"))

    for s in (-1, 1):
        out.append(poly([(s * ux, -uy, 3.5), (s * ux, uy, 3.5), (s * ux, uy, 6.45), (s * ux, -uy, 6.45)], "plaster", out=(s, 0, 0)))

    for side, i in (("f", 0), ("b", 2)):
        out.append(on(side, uy, boards(-ux, ux, 3.5, 6.45, TIMBER if i == 0 else DARK, h=0.34, holes=uholes[side], seed=i + 4)))

    out.append(walls(ux, uy, 3.28, 3.52, lambda a, b, z0, z1, h, i: box(a - 0.1, -0.16, z0, b + 0.1, 0.0, z1, "wood_k", c=0.04, skip="b")))
    out.append(corner_posts(ux, uy, 3.3, 6.5, 0.26, "wood_k"))

    for side, dist, items in (("f", uy, uf), ("b", uy, ub), ("l", ux, us), ("r", ux, us)):
        out.append(glazing(side, dist, items, shutters="wood_l", frame="wood_l"))

    for side in ("l", "r", "b"):
        span, dist = (gy, gx) if side != "b" else (gx, gy)

        for i in range(5):
            u = -span + 0.55 + (2 * span - 1.1) * i / 4
            out.append(on(side, dist, box(-0.13, -0.34, 3.06, 0.13, 0.0, 3.3, "wood_l", c=0.03, skip="b", d=0), u))

    for y, o in ((-uy, -1), (uy, 1)):
        out.append(poly([(-ux, y, 6.45), (ux, y, 6.45), (ux, y, 7.0), (0, y, 9.0), (-ux, y, 7.0)], "wood_k", out=(0, o, 0)))
        side = "f" if o < 0 else "b"
        top = lambda x: 8.82 - abs(x) / 5.4 * 1.98
        out.append(on(side, uy, planks(-4.6, 4.6, 6.62, 7.5, ("wood_d", "wood_k"), w=0.42, seed=8, top=top)))
        out.append(on(side, uy, box(-5.4, -0.14, 6.42, 5.4, 0.0, 6.66, "wood", c=0.03, skip="b")))
        out.append(on(side, uy, box(-0.14, -0.1, 6.6, 0.14, 0.0, 8.85, "wood", c=0.03, skip="b", d=1)))

    out.append(box(-5.2, -5.27, 3.32, 5.2, -uy, 3.54, "wood_d", c=0.04, top="wood"))

    for x in (-5.1, -2.55, 0.0, 2.55, 5.1):
        out.append(beam((x, -uy, 2.85), (x, -5.05, 3.3), 0.18, 0.2, "wood_k", d=1))
        out.append(box(x - 0.1, -5.31, 3.4, x + 0.1, -5.11, 5.02, "wood", c=0.03))

    shape = [(-0.16, 0.0), (0.16, 0.0), (0.16, 0.22), (0.07, 0.42), (0.07, 0.62), (0.16, 0.84), (0.16, 1.08), (-0.16, 1.08), (-0.16, 0.84), (-0.07, 0.62), (-0.07, 0.42), (-0.16, 0.22)]

    for i in range(23):
        x = -4.84 + 9.68 * i / 22

        if abs(abs(x) - 2.55) < 0.12 or abs(x) < 0.12:
            continue

        if ak.LOD == 0:
            out.append(extrude([(x + px, 3.62 + pz) for px, pz in shape], -5.24, -5.18, "wood_l", d=0))

    if ak.LOD > 0:
        out.append(box(-5.0, -5.22, 3.62, 5.0, -5.18, 4.66, "wood", d=2, cast=True))

    for s in (-1, 1):
        out.append(rail([(s * 5.15, -5.18, 3.5), (s * 5.15, -4.3, 3.5)], 1.38, "wood", post=0.12, snow=True, d=1))

    out.append(box(-5.3, -5.37, 4.7, 5.3, -5.08, 4.92, "wood", c=0.04))
    out.append(pad(-5.26, -5.38, 5.26, -5.05, 4.9, 0.17, seed=3, d=1))
    out.append(gable_roof(6.72, -5.3, 5.3, 6.5, 9.1, deck="shingle", wood="wood_l", under="wood_d", th=0.22, snow=0.42, start=0.015, seed=2))
    out.append(box(-0.2, -5.38, 9.02, 0.2, 5.38, 9.2, "wood", c=0.04, d=1))
    out.append(box(-0.55, 1.35, 8.0, 0.55, 2.45, 9.66, "stone", c=0.08))
    out.append(on("f", -1.35, stones(-0.55, 0.55, 8.7, 9.6, rows=2, w=0.5, out=0.05, seed=9), 0))
    out.append(box(-0.68, 1.22, 9.66, 0.68, 2.58, 9.84, "stone_d", c=0.04))
    out.append(pad(-0.66, 1.24, 0.66, 2.56, 9.82, 0.18, seed=4))
    out.append(on("b", gy, drift(-4.5, 4.5, 0.0, 0.82, 1.55, seed=5)))
    out.append(on("l", gx, drift(-3.4, 0.4, 0.0, 0.34, 0.5, seed=6, d=1)))

    return out


def log_wall(axis, u0, u1, fixed, z0, z1, r, seed, over=0.26, holes=()):
    out = Part()
    n = max(1, int(round((z1 - z0) / (r * 1.86))))
    step = (z1 - z0) / n

    if ak.LOD > 0:
        n = max(1, n // 3) if ak.LOD == 1 else 1
        step = (z1 - z0) / n
        r = step * 0.55

    for j in range(n):
        z = z0 + step * (j + 0.5)
        zz = z + (step * 0.25 if axis == "y" and ak.LOD == 0 else 0.0)
        col = ("wood", "wood_d", "wood")[int(hash01(seed, j) * 2.99)]
        spans = [(u0 - over, u1 + over)]

        for h0, h1, h2, h3 in holes:
            if zz + r * 0.5 > h2 and zz - r * 0.5 < h3:
                spans = [s for a, b in spans for s in ((a, min(b, h0)), (max(a, h1), b)) if s[1] - s[0] > 0.1]

        for a, b in spans:
            p0 = (a, fixed, zz) if axis == "x" else (fixed, a, zz)
            p1 = (b, fixed, zz) if axis == "x" else (fixed, b, zz)
            out += log(p0, p1, min(r, step * 0.56), col, "end", sides=(6, 5, 4)[ak.LOD], ends=(a == u0 - over or ak.LOD == 0, b == u1 + over or ak.LOD == 0), phase=math.pi / 6)

    return out


def log_box(x0, y0, x1, y1, z0, z1, r, holes, seed=0):
    out = Part()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out += core(x0 + r * 0.4, y0 + r * 0.4, x1 - r * 0.4, y1 - r * 0.4, z0, z1, "wood_k")
    out += log_wall("x", x0, x1, y0 + r * 0.5, z0, z1, r, seed, holes=holes.get("f", ()))
    out += log_wall("x", x0, x1, y1 - r * 0.5, z0, z1, r, seed + 1, holes=holes.get("b", ()))
    out += log_wall("y", y0, y1, x0 + r * 0.5, z0, z1 - r * 0.5, r, seed + 2, holes=holes.get("l", ()))
    out += log_wall("y", y0, y1, x1 - r * 0.5, z0, z1 - r * 0.5, r, seed + 3, holes=holes.get("r", ()))

    return out


def chimney_stack(x0, y0, x1, y1, z0, z1, seed=0):
    out = Part()

    if ak.LOD > 0:
        return box(x0, y0, z0, x1, y1, z1, "stone", skip="d")

    n = max(1, int(round((z1 - z0) / 0.42)))
    h = (z1 - z0) / n
    out += box(x0 + 0.08, y0 + 0.08, z0, x1 - 0.08, y1 - 0.08, z1, "stone_k", skip="d")

    for j in range(n):
        along = (x1 - x0) >= (y1 - y0)
        split = 0.35 + 0.3 * hash01(seed, j)

        for k, (a, b) in enumerate(((0.0, split), (split, 1.0))):
            if along:
                xa, xb, ya, yb = x0 + (x1 - x0) * a, x0 + (x1 - x0) * b, y0, y1
            else:
                xa, xb, ya, yb = x0, x1, y0 + (y1 - y0) * a, y0 + (y1 - y0) * b

            g = hash01(seed, j, k) * 0.04
            c = ("stone", "stone_l", "stone_d")[int(hash01(seed, j, k, 5) * 2.99)]
            out += box(xa + 0.012 - g, ya - g, z0 + j * h + 0.015, xb - 0.012 + g, yb + g, z0 + (j + 1) * h - 0.015, c, c=0.05)

    return out


def barn():
    out = [plinth(-2.88, -4.18, 3.08, 4.78), plinth(-1.88, 4.6, 0.58, 5.28)]
    n = 0

    for x in (-2.34, 2.34):
        for y in (-3.35, 0.0, 3.35):
            for k in range(5 if ak.LOD == 0 else 1):
                z = k * 0.23 if ak.LOD == 0 else 0.0
                h = 0.21 if ak.LOD == 0 else 1.1
                wide = 0.43 - (0.05 if k % 2 else 0.0) + (0.06 if k == 4 else 0.0)
                out.append(rock((x, y, z), wide, wide, h, seed=n * 9 + k, tones=("stone", "stone_d", "stone_l"), cap=False, n=6, top=0.84))

            n += 1

    out.append(box(-2.78, -4.08, 1.08, 2.78, 4.08, 1.26, "wood_k", c=0.04))

    for x in (-2.55, 0.0, 2.55):
        out.append(box(x - 0.14, -4.12, 0.98, x + 0.14, 4.12, 1.1, "wood_d", d=0))

    holes = {"f": [(-1.62, 0.12, 1.1, 2.95)]}
    out.append(log_box(-2.38, -3.66, 2.38, 3.66, 1.24, 2.66, 0.17, holes, seed=3))
    out.append(core(-2.22, -3.5, 2.22, 3.5, 2.62, 3.4, "black"))

    for side, dist, span in (("f", 3.62, 2.34), ("b", 3.62, 2.34), ("l", 2.34, 3.62), ("r", 2.34, 3.62)):
        m = int(span * 2 / 0.42)

        for i in range(m):
            u = -span + (i + 0.5) * span * 2 / m
            out.append(on(side, dist, box(-0.13, -0.07, 2.64, 0.13, 0.0, 3.36, "wood_l" if i % 3 == 0 else "wood", skip="bdt", d=1), u))

        out.append(on(side, dist, box(-span - 0.12, -0.12, 3.3, span + 0.12, 0.0, 3.46, "wood_d", c=0.03, skip="b")))

    for y, o in ((-3.9, -1), (3.9, 1)):
        side = "f" if o < 0 else "b"
        out.append(poly([(-2.6, y, 3.38), (2.6, y, 3.38), (2.6, y, 3.78), (0, y, 5.05), (-2.6, y, 3.78)], "wood_k", out=(0, o, 0)))
        top = lambda x: 4.95 - abs(x) / 2.6 * 1.2
        out.append(on(side, 3.9, planks(-2.6, 2.6, 3.38, 4.0, ("wood_gd", "wood_d", "wood_g"), w=0.37, seed=5, top=top)))
        out.append(on(side, 3.93, box(-2.7, -0.08, 3.36, 2.7, 0.0, 3.52, "wood_d", c=0.02, skip="b")))

    out.append(on("f", 3.72, door(1.5, 1.66, "wood_l", "wood_d", n=4), -0.76, 1.18))

    for i, (z, y) in enumerate(((0.0, -4.28), (0.28, -3.98))):
        out.append(box(-1.52, y, z, 0.1, -3.55, z + 0.3, "wood_g", c=0.04, top="wood_l"))

    out.append(box(-0.05, -3.97, 1.02, 1.13, -3.55, 1.3, "wood_d", c=0.03))
    out.append(gable_roof(3.86, -5.12, 5.12, 3.36, 5.14, deck="wood_gd", wood="wood", under="wood_d", th=0.18, snow=0.24, start=0.05, seed=7, tile="wood_g"))

    for i in range(7):
        y = -4.4 + i * 1.47
        out.append(box(-0.42, y - 0.4, 5.22, 0.42, y + 0.4, 5.38, "wood_g", c=0.04, d=1))
        out.append(pad(-0.5, y - 0.36, 0.5, y + 0.36, 5.36, 0.15, seed=i, d=1))

    for i in range(10):
        s = -1 if i % 2 else 1
        x = s * (1.1 + 1.9 * hash01(i, 4))
        y = -4.2 + i * 0.93
        z = 5.14 - abs(x) / 3.86 * 1.78 + 0.2
        out.append(rock((x, y, z), 0.34, 0.3, 0.3, seed=i + 40, n=6, d=1))

    out.append(on("b", 3.8, drift(-2.8, 2.8, 0.0, 1.2, 1.45, seed=2)))
    out.append(mound((0.0, 3.0, 0), 1.9, 1.1, 0.58, seed=4, d=1))
    out.append(mound((0.0, -0.05, 0), 2.0, 0.9, 0.55, seed=8, d=1))
    out.append(mound((0.0, -3.3, 0), 1.45, 0.9, 0.5, seed=12, d=1))

    return out


def refuge():
    h = 2.83
    out = [plinth(-2.88, -2.88, 3.08, 3.08), plinth(-3.38, -2.38, 3.08, -1.42), plinth(-2.38, -3.38, -0.42, -2.88)]
    out.append(core(-h + 0.03, -h + 0.03, h - 0.03, h - 0.03, 0, 3.0, "wood_gk"))
    door_x = 0.52
    win = (0.0, 1.5, 1.0, 0.86)
    holes = {"f": [(door_x - 0.72, door_x + 0.72, 0, 3.25)], "r": [hole(-0.9, 1.7, 1.0, 0.86)], "l": [hole(0.3, 1.7, 1.0, 0.86)]}
    out.append(walls(h, h, 0.0, 1.02, lambda a, b, z0, z1, hh, i: stones(a - 0.06, b + 0.06, z0, z1, tones=("stone_d", "stone_k", "stone"), rows=3, w=0.72, out=0.13, holes=hh, seed=i + 2), {"f": [(door_x - 0.72, door_x + 0.72, 0, 3)]}))

    for side in ("r", "b", "l"):
        out.append(on(side, h, boards(-h, h, 1.0, 2.95, GREY, h=0.27, holes=holes.get(side, ()), seed=ord(side))))

    top = lambda x: 4.55 - abs(x) / h * 1.62
    out.append(poly([(-h, -h + 0.02, 2.9), (h, -h + 0.02, 2.9), (0, -h + 0.02, 4.52)], "wood_gk", out=(0, -1, 0)))
    out.append(poly([(-h, h - 0.02, 2.9), (h, h - 0.02, 2.9), (0, h - 0.02, 4.52)], "wood_gk", out=(0, 1, 0)))
    out.append(on("f", h, planks(-h, h, 1.0, 2.9, GREY, w=0.4, holes=[(door_x - 0.72, door_x + 0.72, 0, 3.25)], seed=11, top=top)))
    out.append(on("b", h, planks(-h, h, 2.9, 3.0, GREY, w=0.4, seed=13, top=top)))

    for x in (-2.2, -1.42, -0.55, 1.62, 2.35):
        out.append(on("f", h + 0.04, box(-0.055, -0.06, 1.02, 0.055, 0.0, top(x) - 0.08, "black", skip="b", d=0), x))

    out.append(corner_posts(h, h, 0.95, 3.0, 0.22, "wood"))
    out.append(on("f", h + 0.02, door(1.08, 2.3, "wood", "wood_d"), door_x, 0.24))
    out.append(on("f", h + 0.07, box(-0.72, -0.07, 2.84, 0.72, 0.0, 3.14, "wood_l", c=0.03, skip="b"), door_x))
    out.append(box(door_x - 0.68, -h - 0.55, 0, door_x + 0.68, -h, 0.22, "stone", c=0.05))
    out.append(on("r", h, window(1.0, 0.86, "wood_l"), -0.9, 1.7))
    out.append(on("l", h, window(1.0, 0.86, "wood_l"), 0.3, 1.7))

    for z in (0.5, 0.98):
        out.append(box(-2.3, -3.3 + (0.0 if z < 0.7 else 0.36), z, -0.85, -2.98 + (0.0 if z < 0.7 else 0.16), z + (0.12 if z < 0.7 else 0.22), "wood_l", c=0.03, d=1))

    for x in (-2.15, -1.0):
        out.append(box(x - 0.08, -3.26, 0, x + 0.08, -3.08, 0.52, "wood_d", d=1))

    out.append(pad(-2.28, -3.3, -1.6, -3.0, 0.62, 0.1, d=0))
    out.append(gable_roof(3.86, -3.56, 3.56, 2.9, 4.98, deck="shingle", wood="wood", under="wood_d", th=0.2, snow=0.3, start=0.06, seed=12))
    out.append(cyl((1.25, 0.55, 3.9), 0.13, 1.72, "black", sides=8, smooth=False))
    out.append(cyl((1.25, 0.55, 5.62), 0.19, 0.11, "steel_d", sides=8, smooth=False, caps=(True, True)))
    out.append(cyl((1.25, 0.55, 4.6), 0.28, 0.2, "steel_d", sides=8, smooth=False, d=1))
    out.append(rock((3.0, 0.9, 0.0), 0.62, 1.5, 1.7, seed=3, tones=("snow", "snow_s", "snow"), n=8, top=0.35))
    out.append(on("b", h + 0.05, drift(-2.6, 1.2, 0.0, 0.5, 0.75, seed=9, d=1)))

    return out


def patrol():
    x0, x1, y0, y1 = -1.93, 1.9, -1.93, 1.9
    out = [plinth(-2.36, -2.36, 2.1, 2.1), core(x0, y0, x1, y1, 0.14, 3.3, "wood_gk"), box(x0 - 0.06, y0 - 0.06, 0.0, x1 + 0.06, y1 + 0.06, 0.2, "stone_d", c=0.04)]
    win = hole(-0.83, 1.58, 1.24, 1.3)
    door_h = (0.4, 1.66, 0.1, 3.25)
    side_h = hole(0.0, 1.34, 1.5, 1.44)
    holes = {"f": [win, door_h], "r": [side_h], "l": [side_h]}

    for i, side in enumerate(SIDES):
        out.append(on(side, 1.92, boards(-1.9, 1.9, 0.2, 3.26, ("wood_g", "wood_g", "wood_gd") if side in "fb" else ("wood_gd", "wood_g"), h=0.3, holes=holes.get(side, ()), seed=i + 20)))

    out.append(corner_posts(1.9, 1.9, 0.1, 3.3, 0.2, "wood_d"))
    out.append(on("f", 1.93, window(1.24, 1.3, "wood_l", panes=1), -0.83, 1.58))

    for i in range(5):
        out.append(on("f", 2.0, box(-0.58, -0.06, 2.12 + i * 0.14, 0.58, 0.0, 2.22 + i * 0.14, "steel", skip="b", d=0), -0.83))

    out.append(on("f", 1.94, door(0.9, 2.38, "wood", "red", f=0.12), 1.03, 0.16))
    out.append(on("f", 1.97, box(-0.5, -0.1, 2.68, 0.5, 0.0, 3.22, "orange", c=0.04, skip="b"), 1.03))

    if ak.LOD == 0:
        for i in range(12):
            a = i * math.pi / 6
            b = (i + 1) * math.pi / 6
            c = "white" if (i // 3) % 2 == 0 else "red"
            y = -2.09
            ringpts = [(1.03 + math.cos(t) * r, y, 2.95 + math.sin(t) * r) for t, r in ((a, 0.2), (b, 0.2), (b, 0.09), (a, 0.09))]
            out.append(poly(ringpts, c, out=(0, -1, 0)))

    for side in ("r", "l"):
        out.append(on(side, 1.93, window(1.5, 1.44, "wood_l"), 0.0, 1.34))

    out.append(box(-2.38, -2.38, 3.28, 2.38, 2.38, 3.52, "wood_d", c=0.05))

    for i in range(7):
        x = -2.15 + i * 0.72
        out.append(box(x - 0.07, -2.42, 3.16, x + 0.07, -1.9, 3.3, "wood_k", d=0))

    out.append(pad(-2.36, -2.36, 2.36, 2.36, 3.5, 0.66, seed=6, bevel=0.34, jit=0.1))
    out.append(icicles((-2.2, -2.36, 3.3), (0.2, -2.36, 3.3), 7, 0.34, seed=2))
    out.append(cyl((1.35, 1.55, 3.6), 0.035, 1.96, "steel_d", sides=5, smooth=False))
    out.append(box(1.22, 1.52, 4.85, 1.35, 1.58, 4.9, "steel_d", d=0))
    out.append(box(1.19, 1.5, 4.74, 1.25, 1.6, 4.98, "steel", d=0))
    out.append(on("f", 1.92, drift(-1.75, 0.05, 0.0, 0.34, 0.56, seed=3)))
    out.append(on("r", 1.92, drift(-1.5, 1.2, 0.0, 0.32, 0.4, seed=5, d=1)))

    return out


def clock(y, z, r):
    out = Part()
    n = (12, 8, 6)[ak.LOD]
    out += tube([(0, y, z), (0, y - 0.09, z)], [r * 1.18, r * 1.18], n, "wood_k", caps=(False, True), smooth=False)
    out += tube([(0, y - 0.09, z), (0, y - 0.115, z)], [r, r], n, "white", caps=(False, True), smooth=False)

    for a, ln in ((math.radians(60), r * 0.62), (math.radians(-35), r * 0.82)):
        out += beam((0, y - 0.13, z), (math.cos(a) * ln, y - 0.13, z + math.sin(a) * ln), 0.025, 0.035, "black", d=0, up=(0, 1, 0))

    return out


def starthut():
    out = [plinth(-1.13, -2.28, 1.33, -1.82), plinth(-1.13, -1.9, -0.67, 2.28), plinth(0.37, -0.78, 1.33, 0.68), plinth(-0.63, 0.72, 1.33, 2.28)]
    out.append(box(-1.14, -2.28, 0.05, 1.14, 2.28, 0.23, "wood_d", c=0.03, top="wood_gd"))

    if ak.LOD == 0:
        for i in range(9):
            y = -2.2 + i * 0.2
            out.append(box(-0.9, y, 0.22, 0.9, y + 0.17, 0.25, "wood_g" if i % 2 else "wood_gd", skip="d"))

    for s in (-1, 1):
        xa, xb = sorted((s * 1.14, s * 0.9))
        out.append(pad(xa, -2.28, xb, -0.5, 0.2, 0.2, seed=s + 3))

    out.append(pad(-1.12, 1.62, 1.12, 2.28, 0.2, 0.26, seed=9))
    out.append(box(-0.9, 1.5, 0.23, 0.9, 1.58, 2.86, "wood_k", skip="d"))
    out.append(on("b", 1.57, boards(-0.92, 0.92, 0.23, 2.83, TIMBER, h=0.28, seed=2)))
    out.append(on("f", -1.5, boards(-0.9, 0.9, 0.23, 2.83, DARK, h=0.28, holes=[(-0.7, 0.7, 2.2, 2.65)], seed=3)))
    out.append(on("f", -1.47, box(-0.72, -0.06, 2.2, 0.72, 0.0, 2.65, "canvas", c=0.03, skip="b")))

    for s, side in ((-1, "l"), (1, "r")):
        out.append(box(s * 0.92 - 0.04, -0.42, 0.23, s * 0.92 + 0.04, 1.54, 2.86, "wood_k", skip="d"))
        along = s * 0.55
        part = boards(-0.97, 0.97, 0.23, 2.83, TIMBER, h=0.28, holes=[(-0.45 - along + s * 0.16, 0.45 - along + s * 0.16, 1.2, 2.62)] if s > 0 else (), seed=s + 7)
        out.append(on(side, 0.95, part, along))

    out.append(on("r", 0.96, window(0.66, 1.24, "wood_l", panes=1), 0.16, 1.28))

    for x in (-0.95, 0.95):
        for y in (-0.46, 1.58):
            out.append(box(x - 0.1, y - 0.1, 0.2, x + 0.1, y + 0.1, 2.9, "wood_k", c=0.03, skip="d"))

    out.append(box(-0.92, 0.98, 0.95, 0.92, 1.45, 1.05, "wood_l", c=0.02, d=1))
    out.append(box(-1.02, -0.55, 2.74, 1.02, -0.4, 2.92, "wood_d", c=0.03))

    for y, o in ((-0.5, -1), (1.58, 1)):
        out.append(poly([(-0.98, y, 2.84), (0.98, y, 2.84), (0, y, 3.52)], "wood", out=(0, o, 0)))

    out.append(gable_roof(1.14, -0.72, 1.76, 2.86, 3.6, deck="shingle", wood="wood_d", under="wood_k", th=0.14, snow=0.3, start=0.02, seed=4, rafters=False, cell=0.7))
    out.append(clock(-0.76, 3.12, 0.22))

    for x in (-0.82, 0.82):
        out.append(box(x - 0.07, -1.98, 0.2, x + 0.07, -1.84, 1.2, "wood_k", c=0.02))
        out.append(box(x - 0.09, -2.0, 1.2, x + 0.09, -1.82, 1.32, "orange", c=0.03))

    out.append(box(-0.76, -1.94, 0.82, 0.76, -1.88, 0.9, "red", d=2))
    out.append(box(-0.35, -1.945, 0.815, 0.0, -1.875, 0.905, "white", d=0))
    out.append(box(-1.08, -2.14, 0.2, -0.98, -2.04, 1.55, "wood_k"))
    out.append(box(-1.13, -2.2, 0.95, -0.93, -1.98, 1.22, "steel", c=0.03))

    return out


def sheave_frame(y, z_top, spread, beam_hw):
    out = Part()

    for s in (-1, 1):
        a = Vector((s * 3.15, y, 0.05))
        b = Vector((s * 1.5, y, z_top))
        out += beam(a, b, 0.34, 0.34, "steel", c=0.05)
        out += box(s * 3.2 - 0.5, y - 0.8, 0.0, s * 3.2 + 0.5, y + 0.8, 0.3, "stone", c=0.08)
        out += pad(s * 3.2 - 0.46, y - 0.76, s * 3.2 + 0.46, y - 0.2, 0.28, 0.16, d=1)

    prev = None

    for i, z in enumerate((1.9, 4.1, 6.3)):
        hx = 3.15 - (3.15 - 1.5) * z / z_top
        out += beam((-hx, y, z), (hx, y, z), 0.18, 0.2, "steel_d")

        if prev:
            s = -1 if i % 2 else 1
            out += beam((-s * prev[0], y, prev[1]), (s * hx, y, z), 0.14, 0.14, "steel_d", d=1)

        prev = (hx, z)

    out += beam((-3.15 + 0.3, y, 0.4), (1.5 + 1.2, y, 1.9), 0.14, 0.14, "steel_d", d=1)
    out += box(-beam_hw, y - 0.27, z_top - 0.18, beam_hw, y + 0.27, z_top + 0.3, "steel", c=0.07)
    out += pad(-beam_hw + 0.5, y - 0.25, beam_hw - 0.5, y + 0.25, z_top + 0.28, 0.16, seed=7, d=1)

    for s in (-1, 1):
        out += box(s * spread - 0.28, y - 0.12, z_top + 0.25, s * spread + 0.28, y + 0.12, z_top + 0.6, "steel_d", c=0.03)
        out += wheel((s * spread, y, z_top + 0.98), 0.48, "blue", axis="X", segs=12, spokes=4, w=0.2)

    return out


def base():
    out = [plinth(-6.48, -4.23, -5.52, 4.23), plinth(5.52, -4.23, 6.48, 4.23), plinth(6.5, -3.73, 6.98, 4.23), plinth(-2.48, -3.23, 2.48, -0.27), plinth(-2.0, -6.23, -1.5, -3.25), plinth(1.5, -6.23, 2.0, -4.25), plinth(-2.48, 5.27, 1.48, 5.73), plinth(-1.98, -0.25, 1.98, 0.75)]
    out.append(box(-6.5, -4.0, 0.0, 6.5, 6.25 * 0.64, 0.23, "steel_d", c=0.04, top="steel"))

    if ak.LOD == 0:
        for i in range(12):
            x = -5.6 + i * 1.02
            out.append(box(x, -3.9, 0.22, x + 0.06, 3.9, 0.255, "steel_d", skip="d"))

    for x in (-3.2, 3.2):
        out.append(box(x - 0.5, -6.25, 0.0, x + 0.5, -4.0, 0.3, "stone", c=0.08))

    for sx in (-1, 1):
        for y in (-3.72, 0.0, 3.72):
            w = 0.27 if y else 0.16
            out.append(box(sx * 6.2 - w, y - w, 0.17, sx * 6.2 + w, y + w, 3.34, "wood", c=0.05, skip="d"))
            out.append(box(sx * 6.2 - w - 0.07, y - w - 0.07, 0.17, sx * 6.2 + w + 0.07, y + w + 0.07, 0.42, "steel_d", c=0.04, d=1))

            if y:
                out.append(beam((sx * 6.2, y, 2.3), (sx * 5.0, y, 3.1), 0.2, 0.2, "wood_d", d=1))
                out.append(beam((sx * 6.2, y, 2.3), (sx * 6.2, y - math.copysign(1.1, y), 3.12), 0.2, 0.2, "wood_d", d=1))

        out.append(box(sx * 6.18 - 0.18, -4.05, 3.08, sx * 6.18 + 0.18, 4.05, 3.36, "wood_d", c=0.05))
        side = "r" if sx > 0 else "l"
        out.append(box(sx * 6.07 - 0.05, -3.6, 0.2, sx * 6.07 + 0.05, 3.6, 1.2, "steel", skip="d"))
        out.append(on(side, 6.12, planks(-3.55, 3.55, 0.25, 1.18, ("wood_gd", "wood_g"), w=0.44, seed=sx + 4)))
        out.append(on(side, 6.11, box(-3.6, -0.1, 1.16, 3.6, 0.04, 1.3, "wood_l", c=0.02)))
        out.append(poly([(sx * 6.0, -3.6, 1.28), (sx * 6.0, 3.6, 1.28), (sx * 6.0, 3.6, 3.08), (sx * 6.0, -3.6, 3.08)], "glass", out=(-sx, 0, 0)))

        for y in (-2.7, -0.9, 0.9, 2.7):
            out.append(on(side, 6.08, window(1.56, 1.5, "wood", sill=False, glass="glass"), y, 1.42))

    for y in (-3.62, 3.62):
        out.append(box(-6.4, y - 0.16, 3.06, 6.4, y + 0.16, 3.34, "wood_d", c=0.05))
        o = -1 if y < 0 else 1
        yy = o * 3.52
        out.append(poly([(-5.7, yy, 3.3), (5.7, yy, 3.3), (5.7, yy, 3.52), (0, yy, 6.1), (-5.7, yy, 3.52)], "steel", out=(0, o, 0)))
        out.append(poly([(-5.7, yy - o * 0.04, 3.3), (5.7, yy - o * 0.04, 3.3), (5.7, yy - o * 0.04, 3.52), (0, yy - o * 0.04, 6.1), (-5.7, yy - o * 0.04, 3.52)], "steel_d", out=(0, -o, 0)))
        side = "f" if o < 0 else "b"
        top = lambda x: 5.9 - abs(x) / 5.7 * 2.45
        out.append(on(side, 3.54, planks(-5.0, 5.0, 3.38, 4.2, ("steel_l", "steel"), w=0.55, seed=6, top=top)))
        out.append(on(side, 3.62, box(-2.0, -0.08, 3.6, 2.0, 0.0, 4.55, "wood_l", c=0.05, skip="b")))
        out.append(on(side, 3.69, box(-1.75, -0.05, 3.76, 1.75, 0.0, 4.4, "blue_d", skip="b", d=1)))

        for i in range(5):
            x = -1.36 + i * 0.6
            out.append(on(side, 3.73, box(x, -0.04, 3.92, x + 0.34, 0.0, 4.26, "white", c=0.01, skip="b", d=0)))

    out.append(gable_roof(7.42, -4.38, 4.38, 2.86, 6.34, deck="shingle", wood="wood_l", under="wood_d", th=0.22, snow=0.4, start=0.06, seed=5))
    out.append(box(-0.22, -4.46, 6.24, 0.22, 4.46, 6.46, "wood", c=0.04, d=1))
    out.append(cyl((0.0, -1.75, 0.2), 0.72, 1.2, "stone_k", sides=8, smooth=False, rt=0.5, caps=(False, True)))
    out.append(cyl((0.0, -1.75, 1.35), 0.3, 0.55, "black", sides=8, smooth=False))
    out.append(wheel((0.0, -1.75, 1.94), 2.35, "blue", axis="Z", segs=18, spokes=6, w=0.3))
    out.append(box(-0.7, -0.62, 0.2, 0.7, 0.38, 1.15, "steel", c=0.08))
    out.append(box(-0.5, -0.66, 0.62, -0.05, -0.62, 0.98, "yellow", d=0))

    for x in (-2.42, 2.42):
        out.append(cable((x, -1.75, 1.95), (x, 4.0, 2.0), 0.035, d=1))

    for x in (-4.0, -2.9, 2.9, 4.0):
        out.append(rail([(x, -4.0, 0.22), (x, -2.2, 0.22)], 0.9, "steel_l", post=0.07, step=0.9, d=1, mid=False))

    out.append(sheave_frame(5.25, 8.6, 2.35, 2.94))
    out.append(on("r", 6.2, drift(-3.2, 3.6, 0.0, 0.68, 0.9, seed=4)))
    out.append(on("b", 3.85, drift(-5.9, -3.9, 0.0, 0.5, 0.6, seed=8, d=1)))

    return out


def top():
    out = []
    feet = ((-3.75, -3.0), (3.75, -3.0), (-3.75, 5.0), (3.75, 5.0))

    for i, (x, y) in enumerate(feet):
        sy = -1 if y < 0 else 1
        sx = -1 if x < 0 else 1
        out.append(plinth(x - 0.48, y - 0.48, x + 0.48, y + 0.48))
        out.append(plinth(x - 0.48 + sx * 0.5, y - 0.4, x + 0.48 + sx * 0.45, y + 0.4, z1=0.0))
        out.append(box(x - 0.55, y - 0.55, 0.0, x + 0.55, y + 0.55, 0.45, "stone", c=0.1))
        out.append(beam((x + sx * 0.05, y, 0.4), (sx * 3.0, y - sy * 0.9, 3.7), 0.36, 0.36, "steel_d", c=0.06))
        out.append(box(x - 0.28, y - 0.28, 0.42, x + 0.28, y + 0.28, 0.6, "steel", c=0.03, d=1))
        out.append(mound((x, y + sy * 0.15, 0.1), 0.62, 0.55, 0.52, seed=i, d=1))

    for x in (-3.4, 3.4):
        out.append(beam((x, -2.4, 2.1), (x, 4.1, 2.1), 0.16, 0.18, "steel", d=1))
        out.append(beam((x, -2.25, 2.1), (x * 0.9, 1.0, 3.6), 0.13, 0.13, "steel", d=1))
        out.append(beam((x, 4.0, 2.1), (x * 0.9, 1.0, 3.6), 0.13, 0.13, "steel", d=1))

    out.append(box(-4.14, -4.4, 3.52, 4.14, 5.34, 3.96, "steel", c=0.08, top="steel_d"))

    for x in (-3.6, -1.2, 1.2, 3.6):
        out.append(box(x - 0.12, -4.3, 3.3, x + 0.12, 5.2, 3.55, "steel_d", d=1))

    ramp = [(-2.45, -6.0, 3.32), (2.45, -6.0, 3.32), (2.45, -4.38, 3.94), (-2.45, -4.38, 3.94)]
    out.append(poly(ramp, "steel_d", out=(0, -0.3, 1)))
    out.append(poly([(x, y, z - 0.16) for x, y, z in ramp], "steel", out=(0, 0.3, -1)))

    for s in (-1, 1):
        out.append(beam((s * 2.42, -6.0, 3.3), (s * 2.42, -4.36, 3.92), 0.18, 0.3, "wood_l", c=0.03))

    out.append(box(-2.45, -6.04, 3.16, 2.45, -5.94, 3.34, "yellow", d=1))
    t = 0.12

    for s in (-1, 1):
        side = "r" if s > 0 else "l"
        out.append(box(s * 3.36 - t, -2.4, 3.96, s * 3.36, 4.62, 10.98, "steel_d", skip="d") if s > 0 else box(s * 3.36, -2.4, 3.96, s * 3.36 + t, 4.62, 10.98, "steel_d", skip="d"))
        out.append(on(side, 3.37, planks(-4.55 if s < 0 else -2.35, 2.35 if s < 0 else 4.55, 4.0, 10.9, ("steel", "steel", "steel_l"), w=0.78, holes=[(-0.8, 0.8, 5.35, 6.75)], seed=s + 9)))
        out.append(on(side, 3.4, window(1.4, 1.2, "wood", sill=False, panes=3), 0.0, 5.45))

        for y in (-2.38, 1.1, 4.58):
            out.append(box(s * 3.42 - 0.17, y - 0.17, 3.96, s * 3.42 + 0.17, y + 0.17, 11.0, "wood", c=0.04, skip="d"))

        out.append(box(s * 3.42 - 0.13, -2.4, 7.8, s * 3.42 + 0.13, 4.6, 8.05, "wood_d", d=1))
        out.append(box(s * 3.2 - 0.14, -2.62, 9.35, s * 3.2 + 0.14, -2.38, 9.7, "lamp", c=0.04, d=1))

    out.append(box(-3.36, 4.5, 3.96, 3.36, 4.62, 10.98, "steel", skip="d"))
    out.append(on("b", 4.62, planks(-3.3, 3.3, 4.0, 10.9, ("steel", "steel_l", "steel"), w=0.82, holes=[(-2.4, 2.4, 5.4, 6.65)], seed=3)))

    for x in (-1.55, 0.0, 1.55):
        out.append(on("b", 4.64, window(1.4, 1.1, "wood", sill=False, panes=1), x, 5.45))

    out.append(box(-3.45, -2.52, 10.55, 3.45, -2.24, 11.0, "wood", c=0.05))
    out.append(box(-1.6, -2.56, 10.15, 1.6, -2.46, 10.6, "wood_l", c=0.04))
    out.append(box(-1.4, -2.6, 10.24, 1.4, -2.54, 10.5, "blue_d", d=1))

    for y, o in ((-2.42, -1), (4.6, 1)):
        out.append(poly([(-3.42, y, 10.95), (3.42, y, 10.95), (0, y, 12.55)], "steel", out=(0, o, 0)))
        out.append(box(-3.5, y - 0.07, 10.9, 3.5, y + 0.07, 11.1, "wood_d", d=1))

    out.append(gable_roof(3.95, -2.78, 5.16, 10.98, 12.72, deck="shingle", wood="wood_l", under="wood_d", th=0.18, snow=0.34, start=0.03, seed=9))
    out.append(icicles((-3.9, -2.75, 10.85), (-3.9, 5.1, 10.85), 9, 0.5, seed=1))
    out.append(icicles((3.9, -2.75, 10.85), (3.9, 5.1, 10.85), 9, 0.5, seed=5))
    out.append(box(-0.6, -3.84, 3.94, 0.6, -2.64, 4.4, "stone_k", c=0.08))
    out.append(box(-0.34, -3.55, 4.35, 0.34, -2.93, 9.2, "black", c=0.1, taper=(0.75, 0.75)))
    out.append(wheel((0.0, -3.24, 9.6), 2.28, "blue", axis="Z", segs=18, spokes=6, w=0.34))
    out.append(box(-0.5, -3.74, 9.75, 0.5, -2.4, 10.02, "teal_l", c=0.06))
    out.append(box(-1.14, 1.62, 3.96, 0.42, 2.88, 5.36, "steel_d", c=0.1))
    out.append(box(0.5, 1.86, 3.96, 1.32, 2.52, 5.9, "steel", c=0.08))

    for s in (-1, 1):
        out.append(rail([(s * 2.55, -4.3, 3.96), (s * 4.05, -4.3, 3.96), (s * 4.05, -2.4, 3.96)], 1.05, "steel_l", post=0.08, step=0.8))
        out.append(cable((s * 2.32, -3.24, 9.6), (s * 2.32, -5.4, 9.55), 0.04, d=1))

    out.append(pad(-4.1, 4.66, 4.1, 5.32, 3.94, 0.22, seed=4, d=1))

    return out


def porch_deck(x0, x1, y0, y1, z, col="wood_g"):
    out = Part()
    out += box(x0, y0, z - 0.13, x1, y1, z, "wood_d", c=0.03, top=col)

    if ak.LOD == 0:
        n = int((x1 - x0) / 0.42)

        for i in range(n):
            a = x0 + (x1 - x0) * i / n
            out += box(a + 0.015, y0 + 0.04, z - 0.01, a + (x1 - x0) / n - 0.015, y1, z + 0.025, col if i % 3 else "wood", skip="d")

    return out


def cabin():
    out = [plinth(-4.2, -1.9, 4.2, 4.4), plinth(-4.3, -4.6, -3.2, -1.8), plinth(3.2, -4.6, 4.3, -1.8), plinth(-1.0, -5.0, 1.0, -4.4), plinth(4.0, 0.0, 4.98, 2.4)]
    out.append(walls_ring(-4.06, -1.82, 4.06, 4.34, 0.0, 0.46, seed=2))
    wins = [(-2.38, 1.52, 1.42, 1.48), (2.38, 1.52, 1.42, 1.48)]
    holes = {"f": [hole(-2.38, 1.52, 1.42, 1.48, 0.1), hole(2.38, 1.52, 1.42, 1.48, 0.1), (-0.85, 0.85, 0, 3.45)], "b": [hole(0.0, 1.5, 1.4, 1.3, 0.1)], "l": [hole(1.25, 1.55, 1.3, 1.3, 0.1)]}
    out.append(log_box(-3.88, -1.66, 3.88, 4.16, 0.46, 3.76, 0.19, holes, seed=1))

    for x, z, w, h in wins:
        out.append(on("f", 1.69, window(w, h, "wood_l", shutters=None), x, z))

    out.append(on("b", 4.19, window(1.4, 1.3, "wood_l", shutters="wood_l"), 0.0, 1.5))
    out.append(on("l", 3.91, window(1.3, 1.3, "wood_l", shutters="wood_l"), -1.25, 1.55))
    out.append(on("f", 1.72, door(1.34, 2.8, "wood_g", "wood_l"), 0.0, 0.5))
    n = 7

    for x, o in ((-3.78, -1), (3.78, 1)):
        for j in range(n if ak.LOD == 0 else 0):
            z = 3.82 + j * 0.34
            q = 1 - (z - 3.55) / (6.35 - 3.55)

            if q <= 0.04:
                continue

            out.append(log((x, 1.25 - 3.1 * q, z), (x, 1.25 + 3.2 * q, z), 0.185, "wood" if j % 2 else "wood_d", "end", sides=6, phase=math.pi / 6))

        out.append(poly([(x - o * 0.05, -1.7, 3.7), (x - o * 0.05, 4.2, 3.7), (x - o * 0.05, 1.25, 6.35)], "wood_d" if ak.LOD else "wood_k", out=(o, 0, 0)))

    roof = gable_roof((3.05, 3.75), -5.0, 5.0, (3.62, 3.08), 6.48, deck="shingle", wood="wood_d", under="wood_k", th=0.18, snow=0.28, start=0.04, seed=6)
    out.append(roof.rot(90).move(0, 1.25, 0))
    out.append(porch_deck(-4.25, 4.25, -4.28, -1.84, 0.34))
    e = [(-5.0, -4.62, 3.34), (5.0, -4.62, 3.34), (5.0, -1.6, 3.9), (-5.0, -1.6, 3.9)]
    out.append(poly(e, "shingle", out=(0, -0.2, 1)))
    out.append(poly([(x, y, z - 0.14) for x, y, z in e], "wood_d", out=(0, 0.2, -1)))
    out.append(beam((-5.0, -4.62, 3.26), (5.0, -4.62, 3.26), 0.14, 0.2, "wood", c=0.03))

    for s in (-1, 1):
        out.append(beam((s * 4.96, -4.62, 3.27), (s * 4.96, -1.6, 3.83), 0.12, 0.2, "wood", d=1))

    out.append(slope_snow((-4.9, -4.55, 3.36), (4.9, -4.55, 3.36), (4.9, -1.75, 3.9), (-4.9, -1.75, 3.9), 0.22, seed=3, ridge=False, start=0.03))

    for x in (-4.1, -1.35, 1.35, 4.1):
        out.append(box(x - 0.11, -4.4, 0.3, x + 0.11, -4.18, 3.2, "wood", c=0.04))
        out.append(beam((x, -4.29, 2.7), (x + (0.45 if x < 0 else -0.45), -4.29, 3.15), 0.1, 0.1, "wood_d", d=0))

    for s in (-1, 1):
        out.append(rail([(s * 1.35, -4.28, 0.34), (s * 4.1, -4.28, 0.34)], 0.95, "wood_l", post=0.09, step=0.9, d=1, snow=True))

    out.append(box(-0.95, -4.62, 0.0, 0.95, -4.28, 0.2, "wood_g", c=0.04))
    out.append(chimney_stack(4.0, 0.2, 4.94, 2.3, 0.0, 2.2, seed=3))
    out.append(box(4.0, 0.5, 2.2, 4.9, 2.0, 2.95, "stone_d", c=0.1, taper=(0.86, 0.62)))
    out.append(chimney_stack(4.04, 0.78, 4.82, 1.74, 2.9, 7.34, seed=8))
    out.append(box(3.94, 0.68, 7.32, 4.92, 1.84, 7.46, "stone_l", c=0.04))
    out.append(pad(3.98, 0.72, 4.88, 1.8, 7.44, 0.11, seed=2))
    out.append(on("b", 4.3, drift(-3.8, 3.8, 0.0, 0.55, 0.9, seed=11, d=1)))
    out.append(mound((-4.3, 2.8, 0), 0.7, 1.5, 0.7, seed=5, d=1))

    return out


def walls_ring(x0, y0, x1, y1, z0, z1, seed=0, rows=1):
    out = Part()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    out += core(x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, z0, z1, "stone_k")

    for i, side in enumerate(SIDES):
        span, dist = (hx, hy) if side in "fb" else (hy, hx)
        part = stones(-span, span, z0, z1, rows=rows, w=0.8, out=0.07, seed=seed + i)
        part = on(side, dist - 0.05, part)
        out += part.move(cx, cy, 0)

    return out


def aframe():
    out = [plinth(-2.5, -5.0, 2.5, 4.95), plinth(2.4, -5.48, 2.98, -4.2, z1=0.0)]
    apex = 6.4

    for s in (-1, 1):
        e0, e1 = (s * 2.5, -3.12, 0.06), (s * 2.5, 4.98, 0.06)
        r1, r0 = (0.0, 4.98, apex), (0.0, -3.12, apex)
        out.append(courses(e0, e1, r1, r0, "roofg", "roofg_l", n=13, lift=0.07, seed=s + 5, split=1.35))
        inner = [(s * 2.3, -3.1, 0.04), (s * 2.3, 4.96, 0.04), (0.0, 4.96, apex - 0.5), (0.0, -3.1, apex - 0.5)]
        out.append(poly(inner, "wood_k", out=(-s, 0, -0.5)))

        for y, o in ((-3.12, -1), (4.98, 1)):
            out.append(beam((s * 2.46, y, 0.0), (0.0, y, apex - 0.04), 0.2, 0.34, "wood_r", c=0.04, up=(s, 0, 0.4)))

        out.append(slope_snow((s * 0.95, -3.0, 3.98), (s * 0.95, 4.86, 3.98), (0.0, 4.86, apex + 0.03), (0.0, -3.0, apex + 0.03), 0.16, seed=7, start=0.1, wave=0.12))
        out.append(on("r" if s > 0 else "l", 2.2, drift(-3.6, 4.4, 0.0, 0.34, 0.55, seed=s + 8), s * 0.45))

    for y, o in ((-2.56, -1), (4.62, 1)):
        k = (2.5 - 0.2) / apex
        tri = [(-2.28, y, 0.42), (2.28, y, 0.42), (0.0, y, apex - 0.35)]
        out.append(poly(tri, "glass" if o < 0 else "wood_k", out=(0, o, 0)))

    wid = lambda z: 2.28 * (1 - (z - 0.42) / (apex - 0.35 - 0.42))
    out.append(poly([(-wid(3.3) * 0.7, -2.58, 3.45), (-0.06, -2.58, 5.3), (-0.06, -2.58, 3.45)], "glass_l", d=0, out=(0, -1, 0)))

    for x in (-1.5, -0.74, 0.74, 1.5):
        h = 0.42 + (1 - abs(x) / 2.28) * (apex - 0.77)
        out.append(box(x - 0.07, -2.68, 0.42, x + 0.07, -2.55, h, "wood_r", c=0.02, skip="bd", d=1))

    for z in (0.45, 3.12, 4.3):
        w = wid(z)
        out.append(box(-w, -2.7, z - 0.07, w, -2.55, z + 0.09, "wood", c=0.02, skip="b", d=1))

    out.append(box(-0.06, -2.65, 3.2, 0.06, -2.55, apex - 0.6, "wood_r", skip="b", d=1))
    out.append(on("f", 2.62, door(1.12, 2.4, "wood_r", "wood"), 0.0, 0.48))
    out.append(box(-0.42, -2.88, 3.2, 0.42, -2.7, 3.46, "wood_l", c=0.03))
    out.append(on("b", 4.62, planks(-2.2, 2.2, 0.42, 0.5, ("wood_d", "wood_k", "wood"), w=0.36, seed=4, top=lambda x: 0.42 + max(0.05, 1 - abs(x) / 2.28) * (apex - 0.9))))
    out.append(on("b", 4.68, window(0.8, 0.8, "wood_l"), 0.0, 2.2))
    out.append(porch_deck(-2.42, 2.42, -5.0, -2.6, 0.45))
    out.append(pad(-2.44, -5.02, -1.35, -4.55, 0.43, 0.14, seed=6, d=1))
    out.append(pad(1.3, -5.02, 2.44, -4.2, 0.43, 0.16, seed=8, d=1))
    out.append(on("b", 4.98, drift(-2.2, 2.2, 0.0, 0.4, 0.5, seed=5, d=1)))
    out.append(box(-0.28, -5.0, 0.44, 0.28, -4.86, 0.49, "wood_d", d=0))
    out.append(box(2.5, -4.9, 0.0, 2.96, -3.4, 0.5, "wood_d", c=0.04))
    out.append(pad(2.5, -4.9, 2.97, -3.4, 0.48, 0.18, seed=3, d=1))
    out.append(cyl((0.82, 3.05, 3.6), 0.13, 3.98, "black", sides=8, smooth=False))
    out.append(cyl((0.82, 3.05, 7.58), 0.2, 0.12, "steel_d", sides=8, smooth=False, caps=(True, True), rt=0.08))
    out.append(box(0.62, 2.85, 4.1, 1.04, 3.28, 4.55, "steel_d", c=0.05, d=1))
    out.append(box(-0.14, -3.2, apex - 0.12, 0.14, 5.04, apex + 0.04, "wood_d", d=1))

    return out


def logcabin():
    out = [plinth(-3.0, -3.55, 3.0, 3.55), plinth(-3.55, -4.17, -2.2, -2.9, z1=0.0), plinth(2.4, 2.8, 3.38, 4.17, z1=0.0)]
    out.append(box(-2.95, -3.55, 0.0, 2.95, 3.55, 0.16, "stone", c=0.05))
    side_h = (-1.56, -0.12, 1.3, 2.43)
    holes = {"f": [(-0.86, 0.86, 0, 2.75)], "b": [hole(0.0, 1.38, 1.3, 1.06, 0.1)], "r": [(side_h[0] - 0.12, side_h[1] + 0.12, 1.15, 2.6)]}
    out.append(log_box(-2.8, -3.42, 2.8, 3.42, 0.14, 3.5, 0.2, holes, seed=9))
    out.append(on("f", 3.45, door(1.34, 2.28, "wood_d", "wood"), 0.0, 0.14))
    out.append(on("f", 3.5, box(-1.0, -0.16, 2.48, 1.0, 0.0, 2.7, "wood_l", c=0.03, skip="b")))
    out.append(on("r", 2.83, window(1.4, 1.12, "wood", panes=2), -0.84, 1.3))
    out.append(on("b", 3.45, window(1.3, 1.1, "wood", panes=2), 0.0, 1.36))

    for y, o in ((-3.32, -1), (3.32, 1)):
        side = "f" if o < 0 else "b"
        out.append(poly([(-3.0, y, 3.4), (3.0, y, 3.4), (0, y, 6.3)], "wood_k", out=(0, o, 0)))
        top = lambda x: 3.4 + max(0.03, 1 - abs(x) / 3.0) * 2.82
        out.append(on(side, 3.33, planks(-2.9, 2.9, 3.46, 3.5, ("wood_d", "wood_k", "wood_d"), w=0.38, seed=7 + o, top=top)))
        out.append(on(side, 3.38, box(-3.05, -0.14, 3.36, 3.05, 0.0, 3.58, "wood", c=0.03, skip="b")))

        for x in (-1.5, 0.0, 1.5):
            out.append(on(side, 3.38, box(-0.09, -0.08, 3.55, 0.09, 0.0, top(x) - 0.15, "wood", skip="bd", d=1), x))

    out.append(gable_roof(3.56, -4.15, 4.15, 2.88, 6.4, deck="wood_gd", wood="wood_d", under="wood_k", th=0.18, snow=0.2, start=0.07, seed=15, tile="wood_g", cell=0.95))
    out.append(box(-0.28, -4.17, 6.36, 0.28, 4.17, 6.55, "wood_d", c=0.05))
    out.append(pad(-0.24, -4.0, 0.24, 4.0, 6.5, 0.07, seed=1, d=0))
    out.append(on("l", 2.9, drift(-2.6, 2.4, 0.0, 0.55, 0.7, seed=13, d=1)))

    return out


def washhouse():
    out = [plinth(-4.45, -2.2, 4.45, 2.2), plinth(-4.8, -2.58, -3.8, -2.1, z1=0.0), plinth(3.8, -2.58, 4.8, -2.1, z1=0.0), box(-4.49, -2.23, 0.0, 4.49, 2.23, 0.18, "stone_l", c=0.05)]
    zf, zb = 3.36, 2.74
    out.append(box(-4.2, -1.98, 0.16, 4.2, 1.98, zb, "wood_k", skip="d"))
    xs = (-3.15, -1.05, 1.05, 3.15)
    doors = [(x - 0.66, x + 0.66, 0.0, 2.86) for x in xs]
    out.append(on("f", 2.0, planks(-4.25, 4.25, 0.18, zf - 0.05, ("wood_d", "wood_d", "wood", "wood_k"), w=0.3, holes=doors + [(-4.2, 4.2, 2.86, 3.22)], seed=3)))
    out.append(on("b", 2.0, planks(-4.25, 4.25, 0.18, zb - 0.04, ("wood_d", "wood", "wood_d"), w=0.34, seed=4)))

    for i, x in enumerate(xs):
        out.append(on("f", 2.02, door(0.96, 2.46, "wood_r" if i % 2 else "wood", "wood_l", n=3, f=0.12, ledges=False), x, 0.18))

        for k in range(3):
            out.append(on("f", 2.13, box(-0.2, -0.05, 2.02 + k * 0.12, 0.2, 0.0, 2.07 + k * 0.12, "black", skip="b", d=0), x))

        out.append(on("f", 1.98, box(-0.9, -0.04, 2.84, 0.9, 0.0, 3.24, "black", skip="b"), x))

        for k in range(3):
            out.append(on("f", 2.02, box(-0.88, -0.1, 2.9 + k * 0.11, 0.88, -0.02, 2.95 + k * 0.11, "wood_g", skip="b", d=1), x))

    for x in (-4.22, -2.1, 0.0, 2.1, 4.22):
        out.append(box(x - 0.11, -2.14, 0.16, x + 0.11, -1.98, 3.36, "wood_k", c=0.03, skip="d", d=1))

    for s in (-1, 1):
        side = "r" if s > 0 else "l"
        x = s * 4.22
        out.append(poly([(x, -2.0, zb), (x, 2.0, zb), (x, -2.0, zf)], "wood_k", out=(s, 0, 0)))
        top = lambda u, s=s: zf + (zb - zf) * ((u * s + 2.0) / 4.0)
        out.append(on(side, 4.24, planks(-2.0, 2.0, 0.18, zb, ("wood_d", "wood", "wood_d"), w=0.3, seed=s + 5, top=top)))
        out.append(on(side, 4.31, box(-2.0, -0.06, 1.55, 2.0, 0.0, 1.72, "wood_gd", skip="b", d=1)))

    e = [(-4.8, -2.4, 3.56), (4.8, -2.4, 3.56), (4.8, 2.4, 2.82), (-4.8, 2.4, 2.82)]
    out.append(poly(e, "tin", out=(0, 0.15, 1)))
    out.append(poly([(x, y, z - 0.12) for x, y, z in e], "wood_k", out=(0, -0.15, -1)))
    out.append(beam((-4.8, -2.4, 3.49), (4.8, -2.4, 3.49), 0.1, 0.16, "wood_d"))
    out.append(beam((-4.8, 2.4, 2.76), (4.8, 2.4, 2.76), 0.1, 0.14, "wood_d"))

    for s in (-1, 1):
        out.append(beam((s * 4.76, -2.4, 3.49), (s * 4.76, 2.4, 2.76), 0.1, 0.16, "wood_d"))

    if ak.LOD == 0:
        for i in range(17):
            x = -4.5 + i * 0.5625
            out.append(beam((x, -2.42, 3.61), (x, 2.42, 2.86), 0.17, 0.1, "tin_d" if i % 3 == 0 else "tin", c=0.0))

    out.append(slope_snow((-4.7, 2.3, 2.9), (4.7, 2.3, 2.9), (4.7, -1.5, 3.5), (-4.7, -1.5, 3.5), 0.15, seed=21, ridge=False, start=0.08, wave=0.14))
    out.append(pad(-4.7, -2.3, -3.2, -1.4, 3.5, 0.12, seed=3, d=1))
    out.append(pad(1.0, -2.2, 3.4, -1.45, 3.46, 0.1, seed=4, d=1))
    out.append(on("f", 2.14, box(-0.04, -0.2, 2.38, 0.04, 0.0, 2.44, "black", d=0), 0.0))
    out.append(box(-0.11, -2.42, 2.02, 0.11, -2.22, 2.32, "lamp", c=0.04))
    out.append(box(-0.14, -2.45, 2.31, 0.14, -2.19, 2.39, "black", c=0.02, d=0))

    for z in (0.62, 0.96):
        out.append(box(4.7 if z < 0.8 else 4.34, -0.6, z, 5.16 if z < 0.8 else 4.46, 1.4, z + (0.1 if z < 0.8 else 0.3), "wood_l", c=0.025))

    for y in (-0.45, 1.25):
        out.append(box(4.92, y - 0.07, 0.0, 5.06, y + 0.07, 0.62, "wood_d"))

    out.append(on("b", 2.1, drift(-4.0, 4.0, 0.0, 0.3, 0.55, seed=6, d=1)))

    return out


def lookout():
    out = []
    deck = 7.55

    def leg(sx, sy, z):
        k = 2.4 + (1.86 - 2.4) * z / deck

        return Vector((sx * k, sy * k, z))

    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(beam(leg(sx, sy, 0.1), leg(sx, sy, deck), 0.26, 0.26, "wood_d", c=0.05))
            out.append(box(sx * 2.4 - 0.2, sy * 2.4 - 0.2, 0.0, sx * 2.4 + 0.2, sy * 2.4 + 0.2, 0.26, "stone_l", c=0.06))

    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    levels = (0.6, 2.9, 5.15, 7.3)

    for i in range(4):
        a = corners[i]
        b = corners[(i + 1) % 4]

        for z in levels[1:-1]:
            out.append(beam(leg(*a, z), leg(*b, z), 0.13, 0.17, "wood", ext=0.06))

        for j in range(3):
            lo, hi = levels[j], levels[j + 1]
            p, q = (a, b) if (i + j) % 2 else (b, a)
            out.append(beam(leg(*p, lo), leg(*q, hi), 0.11, 0.11, "wood_d", d=2 if j != 1 else 1))

    flights = ((0.05, 2.9, -1, 1), (2.9, 5.15, 1, -1), (5.15, 7.45, -1, 1))

    for j, (z0, z1, ya, yb) in enumerate(flights):
        y0, y1 = ya * 1.35, yb * 1.35
        x = -0.42 + (j % 2) * 0.84

        for s in (-0.38, 0.38):
            out.append(beam((x + s, y0, z0), (x + s, y1, z1), 0.07, 0.18, "wood", d=1))

        n = 10 if ak.LOD == 0 else 0

        for k in range(n):
            u = (k + 0.5) / n
            y = y0 + (y1 - y0) * u
            z = z0 + (z1 - z0) * u
            out.append(box(x - 0.38, y - 0.13, z, x + 0.38, y + 0.13, z + 0.06, "wood_l", d=0))

        out.append(box(-1.0, y1 - 0.3, z1 - 0.07, 1.0, y1 + 0.3, z1 + 0.02, "wood", d=1))

    out.append(box(-2.6, -2.6, deck - 0.12, 2.6, 2.6, deck + 0.26, "wood_d", c=0.06, top="wood_g"))
    out.append(rail([(-2.46, -2.46, 7.8), (2.46, -2.46, 7.8), (2.46, 2.46, 7.8), (-2.46, 2.46, 7.8), (-2.46, -2.46, 7.8)], 1.28, "wood", post=0.12, step=1.2, snow=True))
    out.append(core(-1.86, -1.86, 1.86, 1.86, 7.8, 11.3, "wood_r"))

    for i, side in enumerate(SIDES):
        out.append(on(side, 1.87, boards(-1.86, 1.86, 7.82, 9.2, ("wood_r", "wood_r", "wood"), h=0.28, holes=[(-0.62, 0.62, 7.7, 10.5)] if side == "f" else (), seed=i + 30)))
        out.append(on(side, 1.88, box(-1.9, -0.12, 9.18, 1.9, 0.0, 9.34, "wood_l", c=0.02, skip="b")))

        if side == "f":
            out.append(on(side, 1.9, door(0.98, 2.36, "wood_r", "wood_l", n=3), 0.0, 7.82))

            for x in (-1.24, 1.24):
                out.append(on(side, 1.9, window(0.94, 1.46, "wood_l", panes=2, sill=False), x, 9.42))
        else:
            for x in (-1.2, 0.0, 1.2):
                out.append(on(side, 1.9, window(0.98, 1.46, "wood_l", panes=2, sill=False), x, 9.42))

        out.append(on(side, 1.9, box(-1.98, -0.1, 11.04, 1.98, 0.0, 11.32, "wood_d", c=0.02, skip="b")))

    out.append(corner_posts(1.88, 1.88, 7.8, 11.3, 0.22, "wood_d"))
    sq = lambda h, z: [Vector((-h, -h, z)), Vector((h, -h, z)), Vector((h, h, z)), Vector((-h, h, z))]
    out.append(loft([sq(2.5, 11.28), sq(2.5, 11.4)], ["wood_d"]))
    out.append(poly(list(reversed(sq(2.5, 11.28))), "wood_k", out=(0, 0, -1)))
    out.append(loft([sq(2.5, 11.38), sq(2.5, 11.42)], ["roofg_d"], apex=(0, 0, 12.15), top="roofg"))
    out.append(loft([sq(2.3, 11.5), sq(2.24, 11.68), sq(1.25, 12.12)], ["snow_s", "snow"], apex=(0, 0, 12.41), top="snow"))
    out.append(cyl((0, 0, 12.1), 0.07, 0.31, "wood_d", sides=6, smooth=False, d=1))

    return out


OPT = dict(reach=1.7, ao=0.52, grime=0.1, grime_h=0.9, under=0.16)

ALL = {n: (f, dict(OPT, errors=(0.01, 0.045))) for n, f in (("chalet", chalet), ("barn", barn), ("refuge", refuge), ("patrol", patrol), ("starthut", starthut), ("base", base), ("top", top), ("cabin", cabin), ("aframe", aframe), ("logcabin", logcabin), ("washhouse", washhouse), ("lookout", lookout))}
