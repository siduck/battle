import math
import random

import arch as a
import ck
from beach import planks


def rail():
    out = ck.Part()
    out += ck.box(-2.0, -0.075, 0.0, 2.0, 0.075, 0.12, "stone", d=1, skip="d")

    for x in (-1.92, 0.0):
        out += ck.box(x - 0.065, -0.065, 0.0, x + 0.065, 0.065, 1.05, "navy", skip="dt")

    out += ck.box(-2.0, -0.085, 1.05, 2.0, 0.085, 1.15, "trim", c=0.025)
    xs = [-1.62 + i * 0.31 for i in range(5)] + [0.31 + i * 0.31 for i in range(6)]

    for i, x in enumerate(xs):
        if ck.LOD == 2 or (ck.LOD == 1 and i % 2):
            continue

        out += ck.tube([(x, 0, 0.1), (x, 0, 1.06)], 0.024, 4, "navy_lt", caps=(False, False), smooth=False, d=1)

    return out


def lamp():
    out = ck.Part()
    out += ck.prism(ck.ngon(0.3, 8), 0.0, 0.14, "stone", c=0.035, d=1)
    out += ck.lathe([(0.2, 0.12, "navy_dk"), (0.17, 0.36, "navy_dk"), (0.1, 0.48, "navy"), (0.085, 0.62, "navy")], 8, smooth=False)
    out += ck.tube([(0, 0, 0.6), (0, 0, 3.12)], [0.075, 0.05], 8, "navy", caps=(False, False), smooth=False)

    for z, r in ((0.66, 0.115), (1.5, 0.1), (3.02, 0.095)):
        out += ck.cyl((0, 0, z), r, 0.07, "gold", sides=8, smooth=False, caps=(True, True), d=0)

    out += ck.lathe([(0.05, 3.1, "navy_dk"), (0.2, 3.2, "navy_dk"), (0.2, 3.25, "navy_dk")], 6, smooth=False)
    out += ck.lathe([(0.17, 3.25, "glass_warm"), (0.27, 3.66, "glass_warm")], 6, smooth=False)

    for i in range(6):
        ang = 2 * math.pi * i / 6
        out += ck.bar((math.cos(ang) * 0.175, math.sin(ang) * 0.175, 3.25), (math.cos(ang) * 0.275, math.sin(ang) * 0.275, 3.66), 0.018, "navy_dk", sides=3, caps=(False, False), d=0)

    out += ck.lathe([(0.32, 3.66, "navy_dk"), (0.33, 3.71, "navy"), (0.19, 3.82, "navy"), (0.07, 3.88, "gold"), (0.07, 3.92, "gold"), (0.0, 4.0, "gold")], 6, smooth=False)
    out.append(ck.Poly([(math.cos(2 * math.pi * i / 6) * 0.32, -math.sin(2 * math.pi * i / 6) * 0.32, 3.66) for i in range(6)], "navy_dk"))

    return out


def bench():
    out = ck.Part()

    for x in (-0.9, 0.0, 0.9):
        frame = ck.Part()
        frame += ck.box(-0.04, -0.46, 0.0, 0.04, -0.36, 0.44, "iron", d=2)
        frame += ck.box(-0.04, 0.36, 0.0, 0.04, 0.46, 0.44, "iron", d=2)
        frame += ck.box(-0.045, -0.48, 0.38, 0.045, 0.48, 0.44, "iron_dk", d=1)
        frame += ck.box(-0.04, -0.09, 0.0, 0.04, 0.09, 0.95, "iron", taper=(1.0, 0.45))
        frame += ck.box(-0.05, -0.5, 0.0, 0.05, -0.32, 0.05, "iron_dk", d=0)
        frame += ck.box(-0.05, 0.32, 0.0, 0.05, 0.5, 0.05, "iron_dk", d=0)
        out += frame.move(x, 0, 0)

    for s in (-1, 1):
        for i, y in enumerate((0.15, 0.28, 0.41)):
            out += ck.box(-1.0, s * y - 0.057, 0.44, 1.0, s * y + 0.057, 0.495, ("wood_lt", "wood")[i % 2], d=2)

        for i, (z, y) in enumerate(((0.6, 0.115), (0.76, 0.095))):
            out += ck.box(-1.0, s * y - 0.027, z, 1.0, s * y + 0.027, z + 0.12, ("wood", "wood_lt")[i % 2], d=2, shear=(0.0, -s * 0.014))

    out += ck.box(-1.0, -0.07, 0.9, 1.0, 0.07, 0.95, "wood_dk", c=0.016, d=1)

    return out


def bin_():
    out = ck.Part()
    out += ck.prism(ck.ngon(0.4, 8), 0.0, 0.1, "iron_dk", c=0.025, d=1)
    out += ck.cyl((0, 0, 0.08), 0.31, 0.58, "iron_dk", sides=8, rt=0.35, smooth=False, caps=(False, False))

    if ck.LOD < 2:
        for i in range(12):
            ang = 2 * math.pi * i / 12
            c, s = math.cos(ang), math.sin(ang)
            slat = ck.box(-0.062, -0.02, 0.1, 0.062, 0.02, 0.66, "teal" if i % 2 else "teal_lt", c=0.012, taper=(1.12, 1.0))
            slat.move(0, -0.345, 0).rot(math.degrees(ang))
            out += slat

    out += ck.lathe([(0.41, 0.62, "navy_dk"), (0.42, 0.7, "navy"), (0.38, 0.76, "navy"), (0.22, 0.86, "navy"), (0.14, 0.88, "void"), (0.0, 0.82, "void")], 10, smooth=False)
    out += ck.cyl((0, 0, 0.855), 0.05, 0.045, "gold", sides=6, d=0)

    return out


def phone():
    out = ck.Part()
    out += ck.box(-0.6, -0.53, 0.0, 0.6, 0.53, 0.14, "stone", c=0.04)

    for x in (-0.49, 0.49):
        for y in (-0.43, 0.43):
            out += ck.box(x - 0.065, y - 0.065, 0.14, x + 0.065, y + 0.065, 1.98, "red", c=0.022)

    inner = a.rect(-0.45, -0.39, 0.45, 0.39)

    for i in range(4):
        p, q = inner[i], inner[(i + 1) % 4]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        part = ck.box(0.0, -0.03, 0.14, ln, 0.02, 0.62, "red_dk" if i == 2 else "red", c=0.012, skip="lr")
        part += ck.box(0.12, -0.045, 0.24, ln - 0.12, -0.03, 0.52, "red_lt", d=0, skip="b")
        part.append(ck.Poly([(0.0, 0.0, 0.62), (ln, 0.0, 0.62), (ln, 0.0, 1.8), (0.0, 0.0, 1.8)], "glass_lt" if i in (0, 3) else "glass"))

        for z in (0.98, 1.38):
            part += ck.box(0.0, -0.025, z, ln, 0.0, z + 0.045, "red", d=0, skip="blr")

        part += ck.box(0.0, -0.04, 1.8, ln, 0.02, 1.98, "red", c=0.012, skip="lr")
        part += ck.box(0.16, -0.052, 1.84, ln - 0.16, -0.04, 1.94, "canvas", d=1, skip="b")
        out += a.onto(p, q, part)

    out += ck.box(-0.59, -0.52, 1.98, 0.59, 0.52, 2.09, "red_dk", c=0.035)
    out += a.hip(a.rect(-0.52, -0.46, 0.52, 0.46), a.rect(-0.24, -0.2, 0.24, 0.2), 2.09, 2.24, "red", rows=2)
    out += ck.cbox(0.3, 0.26, 0.06, (0, 0, 2.24), "red_dk", c=0.02, d=1)
    out += ck.box(-0.18, 0.2, 0.9, 0.18, 0.35, 1.4, "iron_dk", c=0.03, d=1)

    return out


def flowers(x0, x1, y0, y1, z, seed, n, scale=1.0):
    out = ck.Part()
    r = random.Random(seed)

    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n + r.uniform(-0.04, 0.04)
        y = r.uniform(y0, y1)
        s = r.uniform(0.13, 0.19) * scale
        out += ck.blob((x, y, z + s * 0.35), (s * 1.15, s, s * 0.85), ("leaf_lt", "leaf", "leaf_dk"), sub=0, seed=seed + i, jitter=0.22, d=2 if i % 2 == 0 else 1)

        for k in range(2):
            fx = x + r.uniform(-s, s) * 0.8
            fy = y + r.uniform(-s, s) * 0.8
            col = ("bloom", "bloom_lt", "gold", "cream_lt")[(i + seed) % 4]
            out += ck.blob((fx, fy, z + s * r.uniform(0.9, 1.2)), (0.055 * scale, 0.055 * scale, 0.045 * scale), col, sub=0, seed=i * 3 + k, d=1 if k == 0 else 0)

    return out


def planter():
    out = ck.Part()
    out += ck.box(-0.86, -0.31, 0.0, 0.86, 0.31, 0.08, "stone_dk", c=0.025, d=1)
    out += ck.box(-0.84, -0.29, 0.06, 0.84, 0.29, 0.42, "wood", c=0.02)

    for z in (0.19, 0.31):
        out += ck.box(-0.852, -0.302, z, 0.852, 0.302, z + 0.015, "wood_dk", d=0, skip="td")

    for x in (-0.84, 0.84):
        for y in (-0.29, 0.29):
            out += ck.cbox(0.13, 0.13, 0.52, (x, y, 0.0), "trim", c=0.028, d=1)

    for y in (-0.31, 0.31):
        out += ck.box(-0.9, y - 0.05, 0.4, 0.9, y + 0.05, 0.48, "trim", c=0.022, d=1)

    for x in (-0.85, 0.85):
        out += ck.box(x - 0.05, -0.3, 0.4, x + 0.05, 0.3, 0.48, "trim", c=0.022, d=1)

    out += ck.box(-0.8, -0.26, 0.36, 0.8, 0.26, 0.43, "soil", d=2)
    out += flowers(-0.76, 0.76, -0.14, 0.14, 0.42, 4, 7)

    return out


def stall():
    out = ck.Part()
    out += ck.box(-1.05, -0.56, 0.0, 1.05, -0.44, 0.86, "wood", c=0.025)

    for i in range(7):
        x = -1.05 + (i + 0.5) * 2.1 / 7
        out += ck.box(x - 0.12, -0.585, 0.08, x + 0.12, -0.56, 0.8, "wood_lt" if i % 2 else "wood", c=0.012, d=1, skip="b")

    out += ck.box(-1.12, -0.66, 0.86, 1.12, 0.1, 0.95, "wood_lt", c=0.03)

    for sx in (-1.0, 1.0):
        out += ck.box(sx - 0.05, 0.0, 0.0, sx + 0.05, 0.1, 0.86, "wood_dk", c=0.014, d=1)

    for x in (-1.06, 1.06):
        out += ck.cbox(0.09, 0.09, 1.98, (x, -0.56, 0.0), "trim", c=0.02)
        out += ck.cbox(0.09, 0.09, 2.24, (x, 0.56, 0.0), "trim", c=0.02)

    out += a.striped_awning(-1.18, 1.18, 0.62, 2.42, 1.3, 0.42, "teal", "canvas", n=7, valance=0.18, cheeks=False)
    out += ck.box(-1.18, 0.6, 2.36, 1.18, 0.66, 2.42, "teal_dk", c=0.02, d=1)

    for k, (cx, col) in enumerate(((-0.75, "red_lt"), (0.0, "gold"), (0.75, "leaf_lt"))):
        crate = ck.box(-0.3, -0.24, 0.0, 0.3, 0.24, 0.14, "wood_dk", c=0.018)
        n = 8 if ck.LOD == 0 else 3

        for i in range(n):
            crate += ck.blob((-0.2 + (i % 4) * 0.135, -0.1 + (i // 4) * 0.19, 0.16), (0.075, 0.08, 0.065), col, sub=0, seed=i + k * 9, jitter=0.1, d=1)

        crate.rot(12, "X").move(cx, -0.32, 0.97)
        out += crate

    out += ck.box(-0.75, 0.15, 0.0, -0.15, 0.55, 0.42, "wood", c=0.03, d=1)
    out += ck.box(0.15, 0.2, 0.0, 0.65, 0.55, 0.3, "wood_dk", c=0.03, d=1)

    return out


def bunting():
    out = ck.Part()
    sag = lambda x: 0.5 + 0.48 * (x / 1.99) ** 2
    n = 10 if ck.LOD == 0 else 5
    pts = [(-1.99 + 3.98 * i / n, 0.0, sag(-1.99 + 3.98 * i / n)) for i in range(n + 1)]
    out += ck.tube(pts, 0.014, 3, "drift_lt", caps=(False, False), ao=False, d=2)
    cols = ("red", "canvas", "navy_lt", "gold", "teal_lt")
    count = 11 if ck.LOD < 2 else 6

    for i in range(count):
        x = -1.8 + 3.6 * i / (count - 1)
        w = 0.15 if ck.LOD < 2 else 0.24
        z0, z1 = sag(x - w), sag(x + w)
        y = math.sin(i * 2.1) * 0.05
        out += ck.quad([(x - w, 0.0, z0), (x, y, (z0 + z1) / 2 - 0.36), (x + w, 0.0, z1)], cols[i % len(cols)], double=True, ao=False)

    return out


def shelter():
    out = ck.Part()
    out += ck.box(-1.98, -0.9, 0.0, 1.98, 0.9, 0.08, "walk", c=0.025)

    for x in (-1.86, 1.86):
        out += ck.cbox(0.12, 0.12, 2.06, (x, 0.5, 0.06), "navy", c=0.025)

    out += ck.cbox(0.12, 0.12, 0.87, (0.0, 0.5, 0.06), "navy", c=0.025)

    for x in (-1.86, 1.86):
        out += ck.cbox(0.12, 0.12, 2.0, (x, -0.72, 0.06), "navy", c=0.025)

    out += ck.box(-1.84, 0.47, 0.18, 1.84, 0.54, 0.95, "cream", c=0.015)

    for i in range(12):
        x = -1.68 + i * 3.36 / 11

        if abs(x) < 0.1:
            continue

        out += ck.box(x - 0.012, 0.455, 0.22, x + 0.012, 0.47, 0.9, "cream_dk", d=0, skip="b")

    for x0, x1 in ((-1.8, 1.8),):
        out.append(ck.Poly([(x0, 0.5, 0.95), (x1, 0.5, 0.95), (x1, 0.5, 1.88), (x0, 0.5, 1.88)], "glass_lt"))
        out.append(ck.Poly([(x1, 0.512, 0.95), (x0, 0.512, 0.95), (x0, 0.512, 1.88), (x1, 0.512, 1.88)], "glass"))

    out += ck.box(-1.86, 0.44, 0.93, 1.86, 0.57, 1.01, "trim", c=0.022, d=1)
    out += ck.box(-1.9, 0.44, 1.86, 1.9, 0.57, 2.0, "navy_dk", c=0.025, d=1)

    for x in (-1.86, 1.86):
        out += ck.box(x - 0.04, -0.2, 0.18, x + 0.04, 0.46, 0.95, "cream_dk", c=0.012, d=1)
        out.append(ck.Poly([(x - 0.006, -0.18, 0.95), (x - 0.006, 0.45, 0.95), (x - 0.006, 0.45, 1.8), (x - 0.006, -0.18, 1.55)][::-1], "glass_lt"))
        out.append(ck.Poly([(x + 0.006, -0.18, 0.95), (x + 0.006, 0.45, 0.95), (x + 0.006, 0.45, 1.8), (x + 0.006, -0.18, 1.55)], "glass_lt"))

    out += ck.box(-1.78, 0.02, 0.42, 1.78, 0.44, 0.5, "wood_lt", c=0.022)

    for x in (-1.2, 0.0, 1.2):
        out += ck.box(x - 0.05, 0.14, 0.08, x + 0.05, 0.4, 0.42, "iron", c=0.015, d=1)

    prof = [(-0.99, 2.04), (-0.74, 2.24), (-0.3, 2.37), (0.2, 2.35), (0.66, 2.22), (0.86, 2.08)]
    grid = [[(-2.0, y, z), (2.0, y, z)] for y, z in prof]

    for i in range(len(prof) - 1):
        (y0, z0), (y1, z1) = prof[i], prof[i + 1]
        n = 8 if ck.LOD == 0 else 1

        for k in range(n):
            x0, x1 = -2.0 + 4.0 * k / n, -2.0 + 4.0 * (k + 1) / n
            out.append(ck.Poly([(x0, y0, z0 + 0.03), (x1, y0, z0 + 0.03), (x1, y1, z1 + 0.03), (x0, y1, z1 + 0.03)], "teal" if k % 2 == 0 else "teal_lt"))

        out.append(ck.Poly([(-2.0, y1, z1 - 0.04), (2.0, y1, z1 - 0.04), (2.0, y0, z0 - 0.04), (-2.0, y0, z0 - 0.04)], "trim_dk"))

    for x, s in ((-2.0, -1), (2.0, 1)):
        for (y0, z0), (y1, z1) in zip(prof, prof[1:]):
            f = ck.Poly([(x, y0, z0 - 0.07), (x, y1, z1 - 0.07), (x, y1, z1 + 0.03), (x, y0, z0 + 0.03)], "trim")

            if f.normal().x * s < 0:
                f.pts.reverse()

            out.append(f)

    out += ck.box(-2.0, -1.0, 1.96, 2.0, -0.94, 2.1, "trim", c=0.02, d=1)
    out += ck.box(-2.0, 0.83, 1.99, 2.0, 0.89, 2.12, "trim", c=0.02, d=1)

    for x in (-1.86, 1.86):
        out += ck.box(x - 0.045, -0.9, 2.02, x + 0.045, 0.7, 2.12, "navy_dk", c=0.015, d=1)

    return out


def awning():
    out = ck.Part()
    out += a.striped_awning(-2.0, 2.0, 0.6, 1.28, 1.18, 0.72, "red", "canvas", n=10, valance=0.26, cheeks=True)
    out += ck.box(-2.0, 0.54, 1.22, 2.0, 0.6, 1.33, "trim_dk", c=0.018, d=1)
    out += ck.tube([(-2.0, -0.57, 0.56), (2.0, -0.57, 0.56)], 0.028, 5, "iron_lt", caps=(True, True), d=0)

    for x in (-1.9, 1.9):
        out += ck.bar((x, 0.58, 0.08), (x, -0.5, 0.55), 0.022, "iron", sides=4, d=1)

    return out


def shed():
    out = ck.Part()
    out += ck.box(-1.46, -1.4, 0.0, 1.46, 1.42, 0.14, "stone_dk", c=0.035)
    body = a.rect(-1.32, -1.26, 1.32, 1.28)
    ops = {0: [a.door(0.82, 0.98, 1.88, leaf="red_dk", trim="trim_dk", depth=0.1, fan=0.0) | {"z": 0.14}, a.win(1.95, 1.0, 0.62, 0.68, trim="trim", depth=0.1)], 1: [a.win(1.27, 1.1, 0.7, 0.6, trim="trim", depth=0.1)]}
    out += a.shell(body, 0.14, 2.15, "sage_dk", ops)

    for i in range(4):
        p, q = body[i], body[(i + 1) % 4]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        part = ck.Part()
        n = int(ln / 0.27)

        for k in range(1, n):
            u = k * ln / n
            hit = any(abs(u - o["x"]) < o["w"] / 2 + 0.1 for o in ops.get(i, ()))
            spans = [(0.16, 2.14)]

            if hit:
                o = next(o for o in ops[i] if abs(u - o["x"]) < o["w"] / 2 + 0.1)
                spans = [(0.16, o["z"] - 0.12), (o["z"] + o["h"] + 0.16, 2.14)]

            for z0, z1 in spans:
                if z1 - z0 > 0.1:
                    part += ck.box(u - 0.018, -0.022, z0, u + 0.018, 0.0, z1, "sage", d=0, skip="btd")

        out += a.onto(p, q, part)

    for p in body:
        out += ck.cbox(0.13, 0.13, 2.03, (p[0], p[1], 0.14), "trim", c=0.025, d=1)

    out += a.gable(-1.32, 1.32, -1.26, 1.28, 2.15, 0.78, "slate", "sage_dk", axis="y", over=0.17, rows=5, thick=0.09, trim="trim_dk")
    out += a.disc((0.0, -1.29, 2.45), 0.15, "void", 8, 0.04, d=1)
    out += ck.box(-1.12, -1.47, 0.0, -0.22, -1.32, 0.1, "wood_dk", c=0.02, d=1)
    out += ck.lathe([(0.0, 0.0, "teal_dk"), (0.15, 0.0, "teal"), (0.17, 0.5, "teal"), (0.18, 0.56, "iron_dk"), (0.0, 0.55, "iron_dk")], 8, (1.25, -1.34, 0.0), smooth=False, d=1)

    return out


def fence():
    out = ck.Part()
    n = 14 if ck.LOD < 2 else 1

    if ck.LOD == 2:
        out += ck.box(-2.0, -0.04, 0.0, 2.0, 0.04, 1.68, "drift")
    else:
        for i in range(n):
            x0 = -2.0 + i * 4.0 / n
            col = ("drift", "drift_lt", "drift", "wood_lt")[int(ck.hash01(i, 8.2) * 4)]
            h = 1.66 + 0.06 * (i % 2)
            y = -0.012 if i % 2 else 0.012
            out += ck.box(x0 + 0.01, y - 0.032, 0.03, x0 + 4.0 / n - 0.01, y + 0.032, h, col, d=2, skip="d")

    for x in (-1.92, 1.92):
        out += ck.box(x - 0.08, -0.08, 0.0, x + 0.08, 0.08, 1.74, "wood_dk", c=0.025, d=2)
        out += ck.prism(ck.ngon(0.1, 4, x, 0.0), 1.73, 1.8, "wood", c=0.03, d=1)

    return out


def kerb():
    out = ck.Part()

    for i in range(4):
        x0 = -2.0 + i
        profile = [(-0.22, -0.6), (0.22, -0.6), (0.22, 0.15), (0.17, 0.2), (-0.17, 0.2), (-0.22, 0.15)]
        stone = ck.extrude(profile, -x0 - 0.992, -x0 - 0.008, "stone_lt" if i % 2 else "stone", force=True, side=lambda k, p, q: None if k == 0 else ("stone_lt" if i % 2 else "stone"))
        out += stone.rot(90)

    return out


def tile(cells_x, cells_y, cols, grout, z, seed, bond=False, band=None):
    out = ck.Part()
    out.append(ck.Poly([(-2.0, -2.0, z - 0.015), (2.0, -2.0, z - 0.015), (2.0, 2.0, z - 0.015), (-2.0, 2.0, z - 0.015)], grout, False, False, False))
    w, h = 4.0 / cells_x, 4.0 / cells_y

    for j in range(cells_y):
        offs = [-2.0 + i * w for i in range(cells_x + 1)]

        if bond and j % 2:
            offs = [-2.0] + [-2.0 + (i + 0.5) * w for i in range(cells_x)] + [2.0]

        for i, (x0, x1) in enumerate(zip(offs, offs[1:])):
            col = cols[int(ck.hash01(i, j, seed) * len(cols))]

            if band is not None and j == band[0]:
                col = band[1] if i % 2 == 0 else ck.shade(band[1], 1.08)

            y0, y1 = -2.0 + j * h, -2.0 + (j + 1) * h
            g = 0.014
            out.append(ck.Poly([(x0 + g, y0 + g, z), (x1 - g, y0 + g, z), (x1 - g, y1 - g, z), (x0 + g, y1 - g, z)], col, False, False, False))

    return out


def paving():
    return tile(4, 5, ("pave", "pave", "pave_mid", "pave_dk"), "grout", 0.05, 3, bond=True)


def sidewalk():
    return tile(4, 4, ("walk", "walk", "walk_lt", "walk_dk"), "grout", 0.05, 6, bond=True)


def deck():
    out = ck.Part()
    cols = ("pier", "pier", "pier_lt", "drift")

    for i in range(10):
        y0 = -2.0 + i * 0.4
        col = cols[int(ck.hash01(i, 3.9) * len(cols))]
        out += ck.box(-2.0, y0 + 0.012, -0.09, 2.0, y0 + 0.388, 0.0, col, c=0.0, d=2, skip="d")

    for x in (-1.8, 1.8):
        out += ck.box(x - 0.11, -2.0, -0.3, x + 0.11, 2.0, -0.09, "pier_dk", skip="t")

    for y in (-2.0, 1.84):
        out += ck.box(-2.0, y, -0.26, 2.0, y + 0.16, -0.09, "pier_dk", skip="t", d=2)

    out.append(ck.Poly([(-2.0, -2.0, -0.095), (-2.0, 2.0, -0.095), (2.0, 2.0, -0.095), (2.0, -2.0, -0.095)], "pier_dk", False, False, False))

    return out


def piles():
    out = ck.Part()

    for x in (-1.8, 1.8):
        for y in (-1.8, 1.8):
            out += ck.tube([(x, y, -6.0), (x, y, -3.2), (x, y, -2.72), (x, y, -0.28)], [0.18, 0.17, 0.165, 0.15], 7, lambda i, j: "pine_dk" if j == 1 else "pier_dk" if j == 0 else "pier", caps=(False, False), smooth=False)

            if ck.LOD < 2:
                for s in (-1, 1) if False else (1,):
                    iy = -1 if y > 0 else 1
                    ix = -1 if x > 0 else 1
                    out += ck.bar((x, y + iy * 0.1, -1.45), (x, y + iy * 0.95, -0.34), 0.07, "pier_dk", sides=4, caps=(False, False), d=1)
                    out += ck.bar((x + ix * 0.1, y, -1.45), (x + ix * 0.95, y, -0.34), 0.07, "pier_dk", sides=4, caps=(False, False), d=1)

            out += ck.box(x - 0.2, y - 0.2, -0.42, x + 0.2, y + 0.2, -0.3, "pier_dk", d=0)

    return out


def jetty():
    out = ck.Part()

    for i in range(10):
        y0 = -2.0 + i * 0.4
        col = ("pier", "pier_lt", "drift", "pier")[int(ck.hash01(i, 6.4) * 4)]
        out += ck.box(-1.86, y0 + 0.015, 1.84, 1.86, y0 + 0.385, 1.955, col, d=2)

    for x in (-1.72, 1.72):
        out += ck.box(x - 0.1, -2.0, 1.62, x + 0.1, 2.0, 1.84, "pier_dk", c=0.025)

    for x in (-1.85, 1.85):
        for y in (-1.75, 0.0, 1.75):
            out += ck.tube([(x, y, 0.0), (x, y, 0.55), (x, y, 1.88)], [0.15, 0.14, 0.125], 7, lambda i, j: "pine_dk" if j == 0 else "pier_dk", caps=(False, "wood_lt"), smooth=False)

            if ck.LOD == 0:
                out += ck.torus((x, y, 1.74), 0.14, 0.025, "rope", segs=8, sides=3, axis="Z", d=0)

    for y in (-1.75, 1.75):
        out += ck.box(-1.85, y - 0.08, 1.46, 1.85, y + 0.08, 1.64, "pier_dk", c=0.022, d=1)

        for x, s in ((-1.85, 1), (1.85, -1)):
            out += ck.bar((x + s * 0.08, y, 0.7), (x + s * 0.8, y, 1.5), 0.06, "pier", sides=4, caps=(False, False), d=1)

    return out


def ribbon(points, widths, z, col, seed=0):
    out = ck.Part()
    top = [(x, y + w / 2, z) for (x, y), w in zip(points, widths)]
    low = [(x, y - w / 2, z) for (x, y), w in zip(points, widths)]

    for i in range(len(points) - 1):
        pts = [low[i], low[i + 1], top[i + 1], top[i]]
        clean = [pts[0]]

        for p in pts[1:]:
            if math.dist(p, clean[-1]) > 1e-4:
                clean.append(p)

        if len(clean) > 2 and math.dist(clean[0], clean[-1]) < 1e-4:
            clean.pop()

        if len(clean) > 2:
            out.append(ck.Poly(clean, col, False, False, False))

    return out


def foam():
    out = ck.Part()
    lod = ck.LOD
    near = ck.mix("foam", (0.478, 0.737, 0.698), 0.22)
    segs = 28 if lod == 0 else 10
    last = None

    for i in range(segs + 1):
        t = i / segs
        x = -3.5 + 7.0 * t
        y = math.sin(t * 12.6 + 1) * 0.14 + math.sin(t * 31.0) * 0.035
        gap = math.sin(t * math.pi * 4.0 + 0.4)
        w = max(0.0, abs(gap) - 0.25) * (0.1 + 0.05 * ck.hash01(i, 3.1))
        here = ((x, y - w / 2, 0.022), (x, y + w / 2, 0.022))

        if last is not None and last[1][1] - last[0][1] + w > 0.004:
            pts = [last[0], here[0], here[1], last[1]]
            clean = [p for k, p in enumerate(pts) if math.dist(p, pts[k - 1]) > 1e-4]

            if len(clean) > 2:
                out.append(ck.Poly(clean, near, False, False, False))

        last = here

    count = 34 if lod == 0 else 12

    for k in range(count):
        t = (k + 0.15 + 0.7 * ck.hash01(k, 1.7)) / count
        x = -3.45 + 6.9 * t
        side = (ck.hash01(k, 5.3) - 0.5) * 2.0
        y = math.sin(t * 12.6 + 1) * 0.14 + side * abs(side) * 0.5 + (0.07 if side > 0 else -0.07)
        far = min(1.0, abs(side))
        size = (0.035 + 0.075 * ck.hash01(k, 8.9) * (1.0 - 0.55 * far)) * (1.0 if lod == 0 else 1.3)
        sides = (7 if size > 0.07 else 6) if lod == 0 else 4
        col = ck.mix("foam", (0.478, 0.737, 0.698), 0.12 + 0.5 * far)
        z = 0.024 + 0.00025 * k
        ring = []

        for j in range(sides):
            a = math.tau * j / sides + ck.hash01(k, 2.2) * 6.0
            ring.append((x + math.cos(a) * size * 1.35, y + math.sin(a) * size * 0.8, z))

        out.append(ck.Poly(ring, col, False, False, False))

    return out


def ripple():
    out = ck.Part()

    for k, (cx, cy, ln, wd) in enumerate(((-3.4, 0.1, 2.0, 0.17), (-1.2, -0.3, 1.5, 0.12), (0.7, 0.28, 2.3, 0.18), (2.9, -0.15, 1.9, 0.14), (-2.1, 0.4, 0.9, 0.08), (1.9, -0.4, 0.8, 0.08))):
        m = 7
        sp = [(cx - ln / 2 + ln * i / m, cy + math.sin(i / m * math.pi) * 0.1) for i in range(m + 1)]
        out += ribbon(sp, [0.6 * wd * math.sin(i / m * math.pi) for i in range(m + 1)], 0.014, ck.mix("ripple", (0.478, 0.737, 0.698), 0.35))

    return out


def trunk(pts, radii, sides=7):
    return ck.tube(pts, radii, sides, lambda i, j: "trunk_lt" if i % 3 == 0 else "trunk", caps=(False, False), smooth=False)


def clump(at, size, tones, seed, d=2, sub=1):
    return ck.blob(at, size, tones, sub=sub, jitter=0.17, seed=seed, flat=0.62, d=d)


def tree():
    out = ck.Part()
    out += trunk([(0, 0, -0.1), (0.03, -0.02, 1.1), (-0.03, 0.02, 2.4), (0.0, 0.0, 3.5)], [0.24, 0.17, 0.14, 0.1])
    out += ck.cyl((0, 0, -0.1), 0.34, 0.34, "trunk", sides=7, rt=0.2, smooth=False, caps=(False, False), d=1)

    for end, z0, r in (((-0.78, 0.2, 3.5), 2.3, 0.08), ((0.72, -0.3, 3.7), 2.6, 0.07), ((0.2, 0.7, 3.6), 2.5, 0.06)):
        out += ck.tube([(0, 0, z0), end], [r, r * 0.5], 5, "trunk", caps=(False, False), smooth=False, d=1)

    tones = ("leaf_lt", "leaf", "leaf_dk")
    parts = (((0.0, 0.0, 4.55), (1.18, 1.15, 1.02), 1), ((-0.8, 0.25, 3.85), (0.72, 0.74, 0.66), 2), ((0.82, -0.3, 4.0), (0.7, 0.68, 0.62), 3), ((0.18, 0.76, 3.92), (0.66, 0.62, 0.58), 4), ((-0.2, -0.78, 4.05), (0.68, 0.62, 0.56), 5), ((0.1, 0.05, 5.4), (0.72, 0.74, 0.6), 6), ((-0.7, -0.3, 4.85), (0.55, 0.55, 0.46), 7), ((0.74, 0.46, 4.8), (0.54, 0.52, 0.46), 8))

    for i, (at, size, seed) in enumerate(parts):
        if ck.LOD == 2 and i not in (0, 1, 2, 5):
            continue

        out += clump(at, size, tones, seed + 20, sub=1)

    return out


def pine():
    out = ck.Part()
    out += trunk([(0.0, 0.0, -0.1), (0.1, 0.0, 1.2), (0.38, 0.05, 2.7), (0.45, 0.05, 4.1), (0.3, 0.0, 5.3)], [0.34, 0.25, 0.2, 0.15, 0.08], 8)
    limbs = (((0.3, 0.05, 2.6), (-1.5, -0.4, 4.2), (-2.35, -0.55, 4.85)), ((0.42, 0.05, 3.4), (1.5, 0.5, 4.7), (2.2, 0.8, 5.15)), ((0.42, 0.05, 4.0), (-0.4, 1.0, 5.1), (-0.7, 1.7, 5.4)), ((0.4, 0.0, 4.2), (1.0, -0.9, 5.2), (1.3, -1.6, 5.5)))

    for pts in limbs:
        out += ck.tube(list(pts), [0.12, 0.085, 0.04], 5, "trunk", caps=(False, False), smooth=False, d=2)

    tones = ("pine_lt", "pine", "pine_dk")
    pads = (((-2.35, -0.55, 4.95), (1.32, 1.2, 0.56)), ((2.28, 0.8, 5.2), (1.35, 1.18, 0.56)), ((-0.72, 1.82, 5.45), (1.38, 1.38, 0.58)), ((1.35, -1.72, 5.5), (1.32, 1.4, 0.58)), ((0.15, -0.05, 6.1), (1.8, 1.7, 0.86)), ((-1.15, -1.1, 5.55), (1.1, 1.05, 0.52)), ((1.25, 0.55, 5.9), (1.05, 1.0, 0.52)))

    for i, (at, size) in enumerate(pads):
        if ck.LOD == 2 and i >= 5:
            continue

        out += ck.blob(at, size, tones, sub=1, jitter=0.17, seed=40 + i, flat=0.36, d=2)

        if ck.LOD == 0:
            out += clump((at[0] + 0.55 * math.cos(i * 2.3), at[1] + 0.55 * math.sin(i * 2.3), at[2] + size[2] * 0.45), (size[0] * 0.45, size[1] * 0.45, size[2] * 0.62), tones, 70 + i, d=0, sub=0)

            for k in range(2):
                ang = i * 1.7 + k * 2.9
                rim = (at[0] + math.cos(ang) * size[0] * 0.86, at[1] + math.sin(ang) * size[1] * 0.86, at[2] - size[2] * 0.12 + 0.1 * (k % 2))
                out += ck.blob(rim, (size[0] * 0.3, size[1] * 0.3, size[2] * 0.42), tones, sub=0, seed=140 + i * 5 + k, jitter=0.22, d=0)

    return out


def shrub():
    out = ck.Part()
    tones = ("leaf_lt", "leaf", "leaf_dk")
    parts = (((0.0, 0.0, 0.55), (0.46, 0.45, 0.6)), ((-0.28, -0.18, 0.32), (0.31, 0.3, 0.34)), ((0.3, 0.1, 0.34), (0.29, 0.3, 0.36)), ((0.04, 0.3, 0.36), (0.28, 0.26, 0.34)), ((0.12, -0.26, 0.66), (0.26, 0.26, 0.28)))

    for i, (at, size) in enumerate(parts):
        if ck.LOD == 2 and i > 2:
            continue

        out += clump(at, size, tones, 90 + i, sub=1)

    r = random.Random(6)

    for i in range(10):
        ang = r.uniform(0, 6.28)
        z = r.uniform(0.4, 0.95)
        rr = 0.44 * math.cos((z - 0.55) * 1.7)
        out += ck.blob((math.cos(ang) * rr, math.sin(ang) * rr, z), (0.055, 0.055, 0.05), "bloom_lt" if i % 3 else "cream_lt", sub=0, seed=i, d=0)

    return out


def tamarisk():
    out = ck.Part()
    stems = (((0.0, 0.0), (-0.45, -0.2, 1.1), (-0.72, -0.3, 1.6)), ((0.05, 0.02), (0.4, 0.3, 1.2), (0.68, 0.4, 1.75)), ((-0.02, 0.05), (0.0, 0.1, 1.2), (0.08, -0.05, 1.95)), ((0.0, -0.05), (0.3, -0.4, 0.9), (0.55, -0.62, 1.35)))

    for (bx, by), mid, end in stems:
        out += ck.tube([(bx, by, -0.05), mid, end], [0.1, 0.065, 0.03], 5, "trunk", caps=(False, False), smooth=False, d=2)

    tones = ("tam", "tam", "tam_dk")
    pads = (((-0.72, -0.3, 1.66), (0.55, 0.52, 0.45)), ((0.7, 0.42, 1.82), (0.56, 0.54, 0.48)), ((0.06, -0.05, 2.06), (0.66, 0.64, 0.47)), ((0.58, -0.64, 1.42), (0.5, 0.48, 0.4)), ((-0.35, 0.5, 1.5), (0.52, 0.5, 0.42)), ((-0.1, -0.2, 1.45), (0.5, 0.48, 0.42)))

    for i, (at, size) in enumerate(pads):
        if ck.LOD == 2 and i > 3:
            continue

        out += ck.blob(at, size, tones, sub=1, jitter=0.24, seed=110 + i, flat=0.7, accent=None)

    r = random.Random(8)

    for i in range(10):
        at, size = pads[i % len(pads)]
        ang = r.uniform(0, 6.28)
        el = r.uniform(0.15, 1.25)
        p = (at[0] + math.cos(ang) * math.cos(el) * size[0], at[1] + math.sin(ang) * math.cos(el) * size[1], at[2] + math.sin(el) * size[2])
        out += ck.blob(p, (0.12, 0.11, 0.1), ("bloom_lt", "bloom", "bloom") if i % 3 else ("tam", "tam", "tam_dk"), sub=0, seed=i, jitter=0.25, d=1 if i % 4 == 1 else 0)

    return out


ALL = {
    "rail": (rail, {"reach": 0.5, "ao": 0.45}),
    "lamp": (lamp, {"reach": 0.5, "ao": 0.45}),
    "bench": (bench, {"reach": 0.5}),
    "bin": (bin_, {"reach": 0.4}),
    "phone": (phone, {"reach": 0.7}),
    "planter": (planter, {"reach": 0.5}),
    "stall": (stall, {"reach": 0.9}),
    "bunting": (bunting, {"ao": 0.0, "ground": False, "grime": 0.0, "under": 0.0}),
    "shelter": (shelter, {"reach": 1.1}),
    "awning": (awning, {"reach": 0.6, "ao": 0.4, "ground": False, "under": 0.22}),
    "shed": (shed, {"reach": 0.9}),
    "fence": (fence, {"reach": 0.3, "ao": 0.45}),
    "kerb": (kerb, {"ao": 0.0, "grime": 0.0, "ground": False, "lods": False}),
    "paving": (paving, {"ao": 0.0, "grime": 0.0, "ground": False, "lods": False, "speckle": 0.012, "under": 0.0}),
    "sidewalk": (sidewalk, {"ao": 0.0, "grime": 0.0, "ground": False, "lods": False, "speckle": 0.012, "under": 0.0}),
    "deck": (deck, {"ao": 0.35, "reach": 0.4, "ground": False, "under": 0.2}),
    "piles": (piles, {"ao": 0.45, "reach": 0.8, "ground": False}),
    "jetty": (jetty, {"ao": 0.5, "reach": 0.9, "ground": False, "under": 0.18}),
    "foam": (foam, {"ao": 0.0, "grime": 0.0, "ground": False, "lods": False, "speckle": 0.0, "under": 0.0}),
    "ripple": (ripple, {"ao": 0.0, "grime": 0.0, "ground": False, "lods": False, "speckle": 0.0, "under": 0.0}),
    "tree": (tree, {"reach": 1.6, "ao": 0.55, "grime": 0.0, "speckle": 0.035}),
    "pine": (pine, {"reach": 1.6, "ao": 0.55, "grime": 0.0, "speckle": 0.035}),
    "shrub": (shrub, {"reach": 0.5, "ao": 0.5, "speckle": 0.035}),
    "tamarisk": (tamarisk, {"reach": 0.8, "ao": 0.45, "speckle": 0.035}),
}
