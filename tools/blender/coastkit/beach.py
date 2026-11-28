import math
import random

import arch as a
import ck


def planks(x0, x1, y0, y1, z0, z1, cols, n, axis="x", gap=0.02, c=0.012, seed=0, d=None):
    out = ck.Part()

    if ck.LOD == 2:
        return ck.box(x0, y0, z0, x1, y1, z1, cols[0], d=d)

    for i in range(n):
        col = cols[int(ck.hash01(i, seed, 4.2) * len(cols))]

        if axis == "x":
            w = (y1 - y0) / n
            out += ck.box(x0, y0 + i * w + gap / 2, z0, x1, y0 + (i + 1) * w - gap / 2, z1, col, c=c, d=d)
        else:
            w = (x1 - x0) / n
            out += ck.box(x0 + i * w + gap / 2, y0, z0, x0 + (i + 1) * w - gap / 2, y1, z1, col, c=c, d=d)

    return out


def weatherboards(u0, u1, z0, z1, col, holes=(), apex=None, h=0.19, lip=0.032):
    out = ck.Part()
    rows = max(1, int(round((z1 - z0) / h)))
    step = (z1 - z0) / rows
    mid = (u0 + u1) / 2

    for r in range(rows):
        za, zb = z0 + r * step, z0 + (r + 1) * step
        tone = ck.shade(col, 1.0 if r % 2 == 0 else 0.955)
        cuts = sorted({za, zb, *[v for hole in holes for v in hole[2:] if za < v < zb]})

        for lo, hi in zip(cuts, cuts[1:]):
            ya = -lip * (zb - lo) / step
            yb = -lip * (zb - hi) / step
            spans = [(u0, u1)]

            for ha, hb, hz0, hz1 in holes:
                if hz0 < (lo + hi) / 2 < hz1:
                    spans = [s for p, q in spans for s in ((p, min(q, ha)), (max(p, hb), q)) if s[1] - s[0] > 1e-3]

            for p, q in spans:
                pts = [(p, ya, lo), (q, ya, lo), (q, yb, hi), (p, yb, hi)]

                if apex:
                    k0 = (apex - lo) / (apex - z0)
                    k1 = (apex - hi) / (apex - z0)
                    pts = [(mid + (p - mid) * k0, ya, lo), (mid + (q - mid) * k0, ya, lo)]
                    pts += [(mid + (q - mid) * k1, yb, hi), (mid + (p - mid) * k1, yb, hi)] if k1 > 1e-3 else [(mid, yb, hi)]

                out.append(ck.Poly(pts, tone))

                if lo == za:
                    a0, a1 = pts[0][0], pts[1][0]
                    out.append(ck.Poly([(a0, 0.0, lo), (a1, 0.0, lo), (a1, ya, lo), (a0, ya, lo)], ck.shade(col, 0.68)))

    return out


def hut():
    out = ck.Part()
    wall = ck.mix("teal", "sage_dk", 0.45)
    w, y0, y1 = 1.86, -1.3, 2.18
    floor, top, apex = 1.2, 3.48, 4.7

    for px in (-1.87, 1.87):
        for py in (-1.2, 2.12):
            out += ck.box(px - 0.13, py - 0.13, -0.4, px + 0.13, py + 0.13, 1.08, "wood_dk", c=0.035, d=2)

    out += ck.box(-2.0, -1.46, 1.05, 2.0, 2.38, floor, "pier_dk", c=0.03)

    window = a.win(w - 0.9, 2.12, 0.98, 0.96, n=1, lintel="none", sill=False, depth=0.14)
    entry = a.win(w + 0.9, floor, 1.12, 1.88, depth=0.18, reveal=ck.shade("wood_dk", 0.8))
    entry["kind"] = "void"
    walls = (((-w, y0), (w, y0), 1.0, (window, entry)), ((w, y0), (w, y1), 1.04, ()), ((w, y1), (-w, y1), 0.96, ()), ((-w, y1), (-w, y0), 1.04, ()))

    for p, q, k, ops in walls:
        tone = ck.shade(wall, k)

        if ck.LOD:
            out += a.facade(p, q, floor, top, tone, ops)
            continue

        holes = [(o["x"] - o["w"] / 2, o["x"] + o["w"] / 2, o["z"], o["z"] + o["h"]) for o in ops]
        part = weatherboards(0.0, math.hypot(q[0] - p[0], q[1] - p[1]), floor, top, tone, holes)

        for o in ops:
            part += a.fill(o, tone)

        out += a.onto(p, q, part)

    case = ck.Part()

    for o in (window, entry):
        u0, u1 = o["x"] - o["w"] / 2, o["x"] + o["w"] / 2
        z0, z1 = o["z"], o["z"] + o["h"]

        for p, q in ((u0 - 0.1, u0), (u1, u1 + 0.1)):
            case += ck.box(p, -0.065, z0, q, 0.01, z1, "trim", c=0.018, d=1, skip="b")

        case += ck.box(u0 - 0.12, -0.075, z1, u1 + 0.12, 0.01, z1 + 0.11, "trim", c=0.02, d=1, skip="b")

    ux = window["x"]
    case += ck.box(ux - 0.67, -0.14, 2.0, ux + 0.67, 0.02, 2.12, "trim", c=0.025, d=1, skip="b")
    out += a.onto((-w, y0), (w, y0), case)

    for p, q in (((-w, y0), (w, y0)), ((w, y1), (-w, y1))):
        if ck.LOD:
            tri = ck.Part([ck.Poly([(0.0, 0.0, top), (2 * w, 0.0, top), (w, 0.0, apex)], wall)])
        else:
            tri = weatherboards(0.0, 2 * w, top, apex, wall, apex=apex)

        out += a.onto(p, q, tri)

    for px in (-w, w):
        for py in (y0, y1):
            out += ck.box(px - 0.075, py - 0.075, floor, px + 0.075, py + 0.075, 3.42, "trim", c=0.022, d=1, skip="d")

    out += ck.box(-1.96, -1.44, 3.21, 1.96, y0, 3.48, "trim", c=0.03, d=2)
    out += a.gable(-w, w, -1.4, 2.31, top, 1.24, ck.mix("slate_dk", "wood_dk", 0.3), None, axis="y", over=0.14, rows=5, trim=ck.mix("slate", "wood", 0.3), ridge=ck.mix("iron", "wood_dk", 0.4), thick=0.09)

    if ck.LOD < 2:
        out += ck.box(0.9, y0 + 0.12, 2.2, 1.46, y0 + 0.17, 3.08, ck.shade("trim_dk", 0.62), c=0.012, d=1, skip="b")

    face = y0 + 0.03 if ck.LOD < 2 else y0 - 0.09
    out += ck.box(0.35, face, floor, 1.45, face + 0.07, 2.2, "trim_dk", c=0.018, d=2)

    for px in (0.45, 0.93):
        out += ck.box(px, face - 0.022, 1.32, px + 0.42, face, 2.06, ck.shade("trim_dk", 0.86), c=0.01, d=0, skip="b")

    out += ck.box(1.28, face - 0.075, 1.75, 1.36, face - 0.02, 1.84, "gold_dk", c=0.015, d=0)
    out += ck.box(0.49, face - 0.055, 1.42, 0.95, face - 0.025, 2.2, "blue_lt", c=0.012, d=1)
    out += ck.box(0.49, face - 0.058, 2.18, 0.95, face + 0.095, 2.24, "blue_lt", c=0.018, d=1)
    out += ck.box(0.488, face - 0.059, 1.52, 0.952, face - 0.05, 1.62, "canvas", d=0, skip="b")

    for px in (0.3, 1.44):
        out += ck.box(px, -2.455, 0.0, px + 0.06, -2.25, floor, "pier_lt", d=2, shear=(0.0, 0.93))

    for i in range(4):
        z = 0.24 * (i + 1)
        y = -2.35 + z * 0.775
        out += ck.box(0.36, y - 0.13, z - 0.06, 1.44, y + 0.13, z, "pier", c=0.012, d=2)

    return out


def tower():
    out = ck.Part()

    for sx in (-1.6, 1.6):
        for sy in (-1.6, 1.6):
            out += ck.tube([(sx, sy, 0.0), (sx * 0.84, sy * 0.84, 3.0)], [0.13, 0.11], 6, "trim", caps=(False, False), smooth=False)
            out += ck.cbox(0.42, 0.42, 0.12, (sx, sy, 0.0), "pier_dk", c=0.03, d=1)

    for sx in (-1, 1):
        for sy in (-1, 1):
            out += ck.bar((sx * 1.41, sy * 1.41, 2.1), (sx * 0.6, sy * 1.41, 2.88), 0.06, "trim_dk", sides=4, d=1)
            out += ck.bar((sx * 1.41, sy * 1.41, 2.1), (sx * 1.41, sy * 0.6, 2.88), 0.06, "trim_dk", sides=4, d=1)

    out += ck.box(-1.82, -1.82, 2.84, 1.82, 1.82, 3.0, "pier_dk", c=0.035)
    out += planks(-1.95, 1.95, -1.95, 1.95, 3.0, 3.1, ("pier", "pier_lt"), 9, seed=5, c=0.0)
    x, y0, y1 = 1.25, -0.7, 1.5
    body = a.rect(-x, y0, x, y1)
    out += a.shell(body, 3.1, 3.95, "red", {})
    ops = {0: [a.win(x, 3.98, 1.95, 0.95, n=3, lintel="none", sill=False, depth=0.14)], 1: [a.win(1.1, 3.98, 1.6, 0.95, n=2, lintel="none", sill=False, depth=0.14)], 2: [a.win(x, 4.1, 0.9, 0.75, lintel="none", depth=0.1)], 3: [a.win(1.1, 3.98, 1.6, 0.95, n=2, lintel="none", sill=False, depth=0.14)]}
    out += a.shell(body, 3.95, 5.1, "canvas", ops)
    out += a.band(body, 3.86, 4.0, 0.07, "trim", c=0.025, top="red_dk")

    for p in body:
        out += ck.cbox(0.15, 0.15, 2.0, (p[0], p[1], 3.1), "trim", c=0.03, d=1)

    out += a.striped_awning(-1.28, 1.28, -0.74, 5.14, 0.6, 0.18, "red", "canvas", valance=0.1)
    out += a.band(body, 5.04, 5.16, 0.08, "trim", c=0.03)
    roof = a.rect(-1.62, -1.12, 1.62, 1.86)
    out += a.hip(roof, a.rect(-0.35, 0.15, 0.35, 0.6), 5.16, 5.92, "navy", rows=4, cap="navy_dk")
    out += ck.blob((0.0, 0.37, 6.03), (0.13, 0.13, 0.13), "gold", sub=1, jitter=0.0, d=1)

    for px, py in ((-1.82, -1.82), (-0.7, -1.82), (0.7, -1.82), (1.82, -1.82), (1.82, 0.0), (1.82, 1.82), (0.0, 1.82), (-1.82, 1.82), (-1.82, 0.0)):
        out += ck.cbox(0.09, 0.09, 0.82, (px, py, 3.1), "trim", c=0.018, d=2)

    for p, q in (((-1.88, -1.82), (-0.66, -1.82)), ((0.66, -1.82), (1.88, -1.82)), ((1.82, -1.88), (1.82, 1.88)), ((-1.82, -1.88), (-1.82, 1.88)), ((-1.88, 1.82), (1.88, 1.82))):
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        part = ck.box(0.0, -0.07, 3.9, ln, 0.07, 3.99, "red", c=0.025, d=2)
        n = max(2, int(ln / 0.3))

        for k in range(n):
            u = (k + 0.5) * ln / n
            part += ck.box(u - 0.022, -0.022, 3.1, u + 0.022, 0.022, 3.9, "trim_dk", d=0)

        out += a.onto(p, q, part)

    count = 10 if ck.LOD < 2 else 4
    ramp = ck.Part()

    for i in range(count):
        z = 0.2 + (i + 1) * 2.82 / count
        x_at = -1.95 + (i) * 1.3 / count
        ramp += ck.box(x_at, -2.0, z - 0.09, x_at + 1.3 / count + 0.12, -1.84, z, "pier_lt", c=0.015, d=2)

    out += ramp
    out += ck.tube([(-1.97, -1.92, 0.05), (-0.55, -1.92, 2.92)], 0.07, 4, "pier_dk", caps=(True, True), smooth=False)
    out += ck.box(-0.62, -1.98, 3.5, 0.62, -1.9, 3.72, "canvas", c=0.03, d=1)
    out += a.letters(-0.45, 0.45, -1.985, 3.54, 0.14, "red_dk", seed=2, n=5)
    out += ck.torus((-1.05, -1.93, 3.55), 0.24, 0.07, lambda t: "red" if int(t * 4) % 2 == 0 else "canvas", segs=12, sides=6, axis="Y", d=1)

    return out


def cubicles():
    out = ck.Part()
    out += ck.box(-3.98, -0.9, 0.0, 3.98, 0.9, 0.16, "stone", c=0.035)
    doors = ("navy", "red", "teal", "gold", "navy", "red")
    ops = []

    for i in range(6):
        cx = -3.9 + 7.8 * (i + 0.5) / 6
        ops.append(a.door(cx + 3.9, 0.82, 1.72, leaf=doors[i], lintel="none", depth=0.12, fan=0.0) | {"z": 0.16})

    body = a.rect(-3.9, -0.74, 3.9, 0.82)
    out += a.facade(body[0], body[1], 0.16, 1.98, "cream_lt", ops)
    out += a.facade(body[1], body[2], 0.16, 1.98, "cream")
    out += a.facade(body[2], body[3], 0.16, 1.98, "cream")
    out += a.facade(body[3], body[0], 0.16, 1.98, "cream")

    for i in range(7):
        px = -3.9 + 7.8 * i / 6
        out += ck.box(px - 0.09, -0.84, 0.16, px + 0.09, -0.72, 1.98, "trim", c=0.025, d=1)
        out += ck.box(px - 0.05, 0.8, 0.16, px + 0.05, 0.86, 1.98, "cream_dk", c=0.015, d=0)

    for i in range(6):
        cx = -3.9 + 7.8 * (i + 0.5) / 6
        out += a.disc((cx, -0.77, 1.93), 0.045, "canvas", 6, 0.03, d=0)

    out += a.band(body, 1.92, 2.0, 0.06, "trim", c=0.025, detail=1)
    out += a.gable(-3.97, 3.97, -0.92, 0.92, 1.98, 0.17, "teal", "cream", axis="x", over=0.0, rows=2, thick=0.05)

    for i in range(1, 6):
        px = -3.9 + 7.8 * i / 6
        out += ck.tube([(px, -0.9, 2.02), (px, 0.0, 2.19), (px, 0.9, 2.02)], 0.03, 4, "teal_dk", caps=(False, False), smooth=False, d=0)

    return out


def parasol():
    out = ck.Part()
    out += ck.tube([(0, 0, 0.0), (0.02, 0, 1.0), (0.0, 0, 2.0)], 0.035, 6, "wood_lt", d=2)
    out += ck.cyl((0, 0, 0.0), 0.17, 0.09, "stone_dk", sides=8, rt=0.1, d=1)
    n = 10 if ck.LOD < 2 else 6
    rings = ((1.1, 1.62), (0.82, 1.85), (0.42, 1.99), (0.03, 2.04))

    if ck.LOD > 0:
        rings = (rings[0], rings[1], rings[3])

    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        col = "red" if i % 2 == 0 else "canvas"
        grid = []

        for r, z in rings:
            grid.append([(math.cos(a1) * r, math.sin(a1) * r, z), (math.cos(a0) * r, math.sin(a0) * r, z)])

        out += ck.sheet(grid, col, thick=0.018)

        if ck.LOD == 0:
            r, z = rings[0]
            p0 = (math.cos(a0) * r, math.sin(a0) * r, z)
            p1 = (math.cos(a1) * r, math.sin(a1) * r, z)
            am = (a0 + a1) / 2
            pm = (math.cos(am) * r * 1.0, math.sin(am) * r * 1.0, z - 0.13)
            out += ck.quad([p0, (p0[0], p0[1], z - 0.06), pm, (p1[0], p1[1], z - 0.06), p1], ck.shade(col, 0.92), double=True, ao=False)

        out += ck.bar((0, 0, 1.55), (math.cos(a0) * 0.8, math.sin(a0) * 0.8, 1.83), 0.012, "wood", sides=3, caps=(False, False), d=0)

    out += ck.blob((0, 0, 2.07), (0.055, 0.055, 0.06), "gold", sub=0, jitter=0.0, d=1)

    return out


def lounger():
    out = ck.Part()

    for sx in (-0.42, 0.42):
        out += ck.box(sx - 0.045, -0.93, 0.26, sx + 0.045, 0.72, 0.35, "wood", c=0.015)

        for py in (-0.82, 0.62):
            out += ck.box(sx - 0.05, py - 0.05, 0.0, sx + 0.05, py + 0.05, 0.27, "wood_dk", c=0.012, d=1)

        out += ck.bar((sx * 1.1, -0.45, 0.46), (sx * 1.1, 0.12, 0.46), 0.035, "wood_lt", sides=5, d=1)

        for py in (-0.42, 0.09):
            out += ck.bar((sx * 1.1, py, 0.32), (sx * 1.1, py, 0.46), 0.025, "wood_dk", sides=4, d=0)

    out += planks(-0.38, 0.38, -0.9, 0.3, 0.3, 0.34, ("wood_lt", "wood"), 6, seed=3, d=2, c=0.0)
    out += ck.box(-0.37, -0.9, 0.34, 0.37, 0.24, 0.44, "teal", c=0.04)

    for py in (-0.55, -0.15):
        out += ck.box(-0.372, py - 0.07, 0.335, 0.372, py + 0.07, 0.443, "canvas", c=0.035, d=0)

    back = ck.box(-0.37, 0.0, 0.0, 0.37, 0.74, 0.1, "teal", c=0.04)
    back += ck.box(-0.372, 0.24, -0.003, 0.372, 0.38, 0.103, "canvas", c=0.035, d=0)
    back += ck.box(-0.4, 0.02, -0.05, 0.4, 0.72, 0.0, "wood", c=0.012, d=1)
    back += ck.tube([(-0.3, 0.64, 0.14), (0.3, 0.64, 0.14)], 0.075, 8, "canvas", caps=(True, True), d=1)
    back.rot(42, "X").move(0, 0.24, 0.35)
    out += back
    out += ck.bar((-0.34, 0.66, 0.3), (-0.34, 0.6, 0.6), 0.025, "wood_dk", sides=4, d=1)
    out += ck.bar((0.34, 0.66, 0.3), (0.34, 0.6, 0.6), 0.025, "wood_dk", sides=4, d=1)

    return out


def deckchair():
    out = ck.Part()

    for sx in (-0.27, 0.27):
        out += ck.bar((sx, -0.42, 0.34), (sx, 0.16, 0.12), 0.028, "wood_lt", sides=4)
        out += ck.bar((sx, 0.16, 0.12), (sx, 0.42, 0.88), 0.028, "wood_lt", sides=4)
        out += ck.bar((sx, -0.42, 0.34), (sx, -0.38, 0.0), 0.028, "wood", sides=4, d=1)
        out += ck.bar((sx, 0.38, 0.76), (sx, 0.42, 0.0), 0.026, "wood", sides=4, d=1)

    prof = [(-0.43, 0.355), (-0.2, 0.24), (0.04, 0.2), (0.17, 0.27), (0.27, 0.5), (0.39, 0.85)]
    cols = 4 if ck.LOD == 0 else 2
    xs = [-0.25 + 0.5 * i / cols for i in range(cols + 1)]
    grid = [[(x, y, z) for x in xs] for y, z in prof]
    out += ck.sheet(grid, lambda c, r: "gold" if c % 2 == 0 else "canvas", thick=0.015)

    for y, z in ((-0.43, 0.34), (0.4, 0.87)):
        out += ck.bar((-0.29, y, z), (0.29, y, z), 0.024, "wood_dk", sides=5, d=1)

    return out


def windbreak():
    out = ck.Part()
    stakes = [(-0.96, 0.94), (-0.62, -0.5), (0.0, -0.96), (0.62, -0.5), (0.96, 0.94)]
    cols = ("navy", "canvas", "red", "canvas", "teal", "canvas")
    k = 0

    for (ax, ay), (bx, by) in zip(stakes, stakes[1:]):
        n = 4 if ck.LOD == 0 else 2

        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            s0, s1 = math.sin(t0 * math.pi) * 0.07, math.sin(t1 * math.pi) * 0.07
            p0 = (ax + (bx - ax) * t0, ay + (by - ay) * t0)
            p1 = (ax + (bx - ax) * t1, ay + (by - ay) * t1)
            col = cols[k % len(cols)]
            k += 1
            out += ck.sheet([[(p0[0], p0[1], 0.14), (p1[0], p1[1], 0.14)], [(p0[0], p0[1], 1.08 - s0), (p1[0], p1[1], 1.08 - s1)]], col, thick=0.02)

    for i, (x, y) in enumerate(stakes):
        out += ck.tube([(x, y, 0.0), (x, y, 1.12)], 0.037, 6, "wood", caps=(False, False), d=2)
        out += ck.lathe([(0.037, 1.12, "wood_lt"), (0.055, 1.15, "wood_lt"), (0.0, 1.2, "wood_lt")], 6, (x, y, 0.0), smooth=False, d=1)

    return out


def driftwood():
    out = ck.Part()
    main = [(-0.2, -1.26, 0.17), (-0.06, -0.55, 0.2), (0.0, 0.2, 0.2), (-0.08, 0.85, 0.18), (-0.14, 1.28, 0.16)]
    out += ck.tube(main, [0.2, 0.21, 0.19, 0.18, 0.15], 8, lambda i, j: "drift_lt" if i % 4 == 0 else "drift_dk" if i % 5 == 0 else "drift", caps=("wood_lt", "wood_lt"), smooth=False)

    for y, z in ((-1.285, 0.17), (1.305, 0.16)):
        out += a.disc((-0.2 if y < 0 else -0.14, y, z), 0.08, "wood", 8, 0.02, d=0)

    out += ck.tube([(0.0, -0.1, 0.32), (0.16, 0.02, 0.6), (0.2, 0.08, 0.78)], [0.11, 0.08, 0.065], 6, "drift", caps=(False, "wood_lt"), smooth=False)
    out += ck.tube([(-0.1, 0.62, 0.28), (-0.34, 0.74, 0.46)], [0.08, 0.05], 6, "drift_dk", caps=(False, "wood_lt"), smooth=False, d=1)
    out += ck.tube([(0.34, -0.5, 0.1), (0.38, 0.2, 0.11), (0.45, 0.8, 0.09)], [0.11, 0.1, 0.075], 7, "drift_lt", caps=("wood_lt", "wood_lt"), smooth=False)

    for i, (x, y, r) in enumerate(((0.46, -0.9, 0.11), (-0.45, -0.3, 0.12), (0.4, 1.12, 0.09), (-0.46, 0.2, 0.07))):
        out += ck.blob((x, y, r * 0.45), (r, r * 1.15, r * 0.7), ("stone_lt", "stone", "stone_dk"), sub=0, seed=i + 4, flat=0.6, d=1)

    return out


def pots():
    out = ck.Part()

    def pot(cx, cy, z, turn, seed):
        p = ck.Part()
        p += ck.box(-0.2, -0.24, 0.0, 0.2, 0.24, 0.045, "wood_dk", c=0.012)
        n = 7 if ck.LOD == 0 else 4
        ring = [(math.cos(math.pi * i / (n - 1)) * 0.19, 0.04 + math.sin(math.pi * i / (n - 1)) * 0.23) for i in range(n)]

        if ck.LOD < 2:
            for yy in (-0.215, 0.215):
                for u, v in zip(ring, ring[1:]):
                    p += ck.bar((u[0], yy, u[1]), (v[0], yy, v[1]), 0.016, "wood_lt", sides=4, caps=(False, False))

            for u in ring[1:-1]:
                p += ck.bar((u[0], -0.22, u[1]), (u[0], 0.22, u[1]), 0.012, "rope", sides=3, caps=(False, False))

        core = [(x * 0.84, 0.04 + (zz - 0.04) * 0.84) for x, zz in ring]
        p += ck.extrude(core, -0.19, 0.19, "void" if ck.LOD < 2 else "wood", force=True, side="iron_dk" if ck.LOD < 2 else "wood")
        p += ck.torus((0.0, -0.236, 0.14), 0.065, 0.016, "teal", segs=8, sides=3, axis="Y", d=0)

        return p.rot(turn).move(cx, cy, z)

    out += pot(-0.19, 0.0, 0.0, 3, 1)
    out += pot(0.2, 0.0, 0.0, -4, 2)
    out += pot(0.0, 0.0, 0.285, 8, 3)
    out += pot(0.02, 0.0, 0.57, -9, 4)
    out += ck.torus((0.3, 0.02, 0.31), 0.09, 0.022, "rope", segs=10, sides=4, axis="Z", d=1)
    out += ck.blob((0.34, 0.17, 0.07), (0.065, 0.065, 0.07), "red_lt", sub=1, jitter=0.0, d=1)

    return out


def nets():
    out = ck.Part()
    heaps = ((-0.35, 0.0, 0.62, 0.45, 0.36, "teal"), (0.45, 0.08, 0.5, 0.4, 0.28, "teal_dk"), (0.05, -0.18, 0.42, 0.34, 0.4, "rope"), (-0.82, -0.05, 0.3, 0.28, 0.2, "teal_dk"))

    for i, (x, y, rx, ry, rz, c) in enumerate(heaps):
        out += ck.blob((x, y, rz * 0.35), (rx, ry, rz), (ck.shade(c, 1.12), ck.rgb(c), ck.shade(c, 0.76)), sub=1, jitter=0.24, seed=i + 2, flat=0.36)

    for i, (x, y, z, rr) in enumerate(((-0.55, -0.3, 0.36, 0.1), (-0.15, -0.42, 0.34, 0.095), (0.55, -0.2, 0.32, 0.11), (0.2, 0.3, 0.38, 0.09), (-0.75, 0.2, 0.2, 0.085), (0.9, 0.2, 0.17, 0.09))):
        out += ck.blob((x, y, z), (rr, rr, rr), "red_lt" if i % 2 == 0 else "gold", sub=1, jitter=0.0, d=1, smooth=True)

    out += ck.torus((0.96, -0.2, 0.05), 0.22, 0.04, "rope", segs=14, sides=5, axis="Z", d=1)
    out += ck.torus((0.97, -0.19, 0.12), 0.18, 0.036, "rope", segs=14, sides=5, axis="Z", d=0)
    out += ck.tube([(-1.2, -0.3, 0.03), (-0.8, -0.45, 0.06), (-0.35, -0.5, 0.18), (0.05, -0.34, 0.5), (0.4, -0.3, 0.3), (0.75, -0.45, 0.04)], 0.025, 4, "rope", caps=(True, True), d=1)
    out += ck.tube([(-0.7, 0.35, 0.05), (-0.35, 0.1, 0.4), (0.1, 0.2, 0.37), (0.5, 0.45, 0.08)], 0.018, 4, "drift_lt", caps=(True, True), d=0)

    return out


def fishcrate():
    out = ck.Part()
    out += ck.box(-0.2, -0.32, 0.0, 0.2, 0.32, 0.05, "navy_dk", c=0.012)

    for z in (0.07, 0.155):
        for sx in (-0.2, 0.17):
            out += ck.box(sx, -0.29, z, sx + 0.03, 0.29, z + 0.065, "navy_lt", c=0.008)

        for sy in (-0.32, 0.29):
            out += ck.box(-0.2, sy, z, 0.2, sy + 0.03, z + 0.065, "navy_lt", c=0.008)

    for sx in (-0.175, 0.175):
        for sy in (-0.295, 0.295):
            out += ck.box(sx - 0.028, sy - 0.028, 0.03, sx + 0.028, sy + 0.028, 0.235, "navy_dk", c=0.008, d=1)

    out += ck.box(-0.17, -0.29, 0.05, 0.17, 0.29, 0.15, "foam_dk", d=2)
    r = random.Random(9)

    for i in range(9):
        out += ck.blob((-0.11 + (i % 3) * 0.11 + r.uniform(-0.02, 0.02), -0.18 + (i // 3) * 0.18 + r.uniform(-0.03, 0.03), 0.17), (0.065, 0.075, 0.045), ("foam", "foam", "foam_dk"), sub=0, seed=i, jitter=0.25, d=1)

    return out


def rod():
    out = ck.Part()
    out += ck.lathe([(0.0, 0.0, "iron"), (0.095, 0.0, "teal"), (0.12, 0.27, "teal_dk"), (0.135, 0.28, "teal_dk"), (0.1, 0.27, "void"), (0.0, 0.2, "void")], 8, (-0.2, 0.0, 0.0), smooth=False)
    pts = [(-0.24, 0.0, 0.12), (0.1, 0.0, 0.55), (0.55, 0.0, 0.89), (1.1, 0.0, 1.1)]
    out += ck.tube(pts, [0.022, 0.017, 0.011, 0.006], 5, "iron_dk", caps=(True, True), d=2)
    out += ck.tube([(-0.2, 0.0, 0.17), (-0.04, 0.0, 0.38)], [0.034, 0.032], 6, "wood_lt", caps=(True, True), d=1)
    out += a.disc((0.03, -0.045, 0.41), 0.06, "steel", 8, 0.045, d=1)
    out += ck.tube([(1.1, 0.0, 1.095), (1.1, 0.0, 0.34)], 0.004, 3, "drift_lt", caps=(False, False), d=0)
    out += ck.blob((1.08, 0.0, 0.32), (0.03, 0.03, 0.045), "red_lt", sub=0, jitter=0.0, d=0)
    out += ck.box(-1.08, -0.095, 0.0, -0.55, 0.095, 0.2, "red", c=0.03)
    out += ck.box(-1.1, -0.1, 0.2, -0.53, 0.1, 0.27, "red_dk", c=0.03, d=1)
    out += ck.tube([(-0.94, 0.0, 0.26), (-0.9, 0.0, 0.34), (-0.72, 0.0, 0.34), (-0.68, 0.0, 0.26)], 0.014, 4, "iron", caps=(False, False), d=0)

    return out


def buoy():
    out = ck.Part()
    out += ck.cbox(0.62, 0.62, 0.14, (0, 0.05, 0), "stone", c=0.045)
    out += ck.cbox(0.16, 0.14, 0.9, (0, 0.08, 0.14), "wood_dk", c=0.025)
    shield = [(-0.43, 0.72), (0.43, 0.72), (0.5, 0.9), (0.5, 1.3), (0.28, 1.48), (-0.28, 1.48), (-0.5, 1.3), (-0.5, 0.9)]
    out += ck.extrude(shield, -0.04, 0.08, "navy", side="navy_dk", force=True)
    out += ck.extrude([(-0.34, 1.46), (0.34, 1.46), (0.2, 1.55), (-0.2, 1.55)], -0.08, 0.12, "trim", d=1)
    out += ck.torus((0.0, -0.11, 1.09), 0.29, 0.092, lambda t: "red" if int(t * 8) % 2 == 0 else "canvas", segs=16, sides=7, axis="Y")
    out += a.disc((0.0, -0.06, 1.09), 0.07, "gold", 8, 0.05, d=0)
    out += ck.box(-0.3, -0.07, 0.78, 0.3, -0.04, 0.84, "canvas", d=0)

    return out


def flag():
    out = ck.Part()
    out += ck.cyl((0, 0, 0), 0.34, 0.12, "stone_dk", sides=8, rt=0.26)
    out += ck.cyl((0, 0, 0.12), 0.09, 0.22, "iron", sides=8, rt=0.06, d=1)
    pole = [(0.0, 0.0, 0.2), (-0.015, 0.0, 2.2), (0.0, 0.0, 4.2), (0.1, 0.0, 5.3), (0.34, 0.0, 5.84), (0.7, 0.0, 5.97)]
    out += ck.tube(pole, [0.04, 0.036, 0.03, 0.024, 0.018, 0.012], 6, "trim", caps=(False, True))
    left = [(-0.01, 2.0), (0.0, 3.1), (0.015, 4.2), (0.09, 5.2), (0.3, 5.76), (0.68, 5.93)]
    right = [(0.42, 2.25), (0.72, 3.0), (0.98, 4.0), (1.12, 4.85), (1.08, 5.5), (0.84, 5.84)]
    cols = 3 if ck.LOD == 0 else 2
    grid = []

    for (lx, lz), (rx, rz) in zip(left, right):
        row = []

        for c in range(cols + 1):
            t = c / cols
            row.append((lx + (rx - lx) * t, math.sin(t * math.pi * 1.4 + lz * 1.3) * 0.07 * t, lz + (rz - lz) * t))

        grid.append(row)

    bands = ("teal", "teal", "canvas", "gold", "teal")

    out += ck.sheet(grid, lambda c, r: bands[min(r, len(bands) - 1)], thick=0.012, ao=False)

    return out


def dunefence():
    out = ck.Part()
    r = random.Random(11)
    n = 25 if ck.LOD == 0 else 13 if ck.LOD == 1 else 6

    for i in range(n):
        x = -1.93 + i * 3.86 / (n - 1)
        h = r.uniform(0.9, 1.24) - 0.16 * abs(math.sin(x * 1.3))
        y = math.sin(x * 1.7) * 0.2 + r.uniform(-0.03, 0.03)
        lean = r.uniform(-0.025, 0.025)
        back = r.uniform(-0.08, 0.08)
        col = ("drift", "drift_lt", "drift_dk", "wood_lt")[int(r.random() * 4)]
        w = 0.05 if ck.LOD < 2 else 0.14
        out += ck.box(x - w, y - 0.022, -0.04, x + w, y + 0.022, h, col, d=2, shear=(lean, back), taper=(0.7, 1.0))

        if ck.LOD == 0:
            out.append(ck.Poly([(x + lean - w * 0.7, y - 0.022 + back, h), (x + lean + w * 0.7, y - 0.022 + back, h), (x + lean * 1.05, y + back, h + 0.07)], col))

    for i, x in enumerate((-1.94, 0.05, 1.94)):
        y = math.sin(x * 1.7) * 0.2
        out += ck.tube([(x, y + 0.08, -0.05), (x, y + 0.1, 1.28)], [0.07, 0.06], 6, "wood_dk", smooth=False, d=1)

    return out


def walkover():
    out = ck.Part()
    steps = 11 if ck.LOD < 2 else 4

    for i in range(steps):
        t0 = i / steps
        y0 = 2.0 - 4.0 * t0
        y1 = 2.0 - 4.0 * (i + 1) / steps
        z = 0.42 + (i + 1) / steps * 1.34

        if ck.LOD == 0:
            out += planks(-0.82, 0.82, y1, y0, z - 0.08, z, ("pier", "pier_lt", "drift"), 2, seed=i, c=0.0)
        else:
            out += ck.box(-0.82, y1, z - 0.08, 0.82, y0, z, "pier_lt" if i % 2 else "pier")

        out += ck.box(-0.78, y1 + 0.01, z - 0.24, 0.78, y1 + 0.07, z - 0.08, "pier_dk", d=1)

    for sx in (-0.87, 0.87):
        outline = [(-2.0, 1.3), (2.0, -0.04), (2.0, 0.34), (-2.0, 1.68)]
        side = ck.extrude(outline, -0.05, 0.05, "pier", force=True)
        side.rot(90).move(sx, 0, 0)
        out += side

        for y, z in ((-1.7, 1.3), (-0.55, 0.92), (0.6, 0.54)):
            out += ck.cbox(0.14, 0.14, z + 0.35, (sx * 0.8, y, -0.35), "pier_dk", d=2, skip="d")

        for y, z in ((-1.88, 0.0), (-0.65, 0.0), (0.65, 0.0), (1.88, 0.0)):
            top = 2.28 - (y + 1.98) / 3.96 * 1.38
            out += ck.cbox(0.13, 0.13, top - 0.1, (sx * 1.03, y, 0.1), "drift_dk", c=0.025, d=2)

        out += ck.tube([(sx * 1.03, -1.98, 2.3), (sx * 1.03, 1.98, 0.92)], 0.062, 5, "drift", caps=(True, True), smooth=False)

    return out


def groyne():
    out = ck.Part()
    heights = (1.38, 1.22, 1.42, 1.27, 1.34)

    for i, h in enumerate(heights):
        x = -1.8 + i * 0.9
        side = 0.46 if i % 2 == 0 else -0.46
        y = 0.0
        out += ck.tube([(x, y, -0.1), (x + 0.02, y, h)], [0.2, 0.17], 7, "pier_dk", caps=(False, "wood_lt"), smooth=False)
        out += ck.tube([(x, y, 0.98), (x, y, 1.08)], [0.215, 0.21], 7, "iron_dk", caps=(False, False), smooth=False, d=0)
        out += ck.tube([(x, y, -0.1), (x, y, 0.22)], [0.24, 0.215], 7, "pine_dk", caps=(False, False), smooth=False, d=1)

    cols = ("pier", "drift_dk", "pier", "pier_lt")

    for k in range(4):
        z = 0.04 + k * 0.23
        out += ck.box(-2.0, -0.11, z, 2.0, 0.11, z + 0.215, cols[k], skip="d")

    for i, (x, y, r) in enumerate(((-1.35, 0.42, 0.27), (-0.45, -0.45, 0.2), (0.5, 0.4, 0.22), (1.38, -0.4, 0.25), (1.7, 0.44, 0.17))):
        out += ck.blob((x, y, r * 0.3), (r * 1.2, r * 0.75, r * 0.8), ("stone", "rock", "stone_dk"), sub=0, seed=i + 1, jitter=0.26, flat=0.5, d=1)

    return out


def rock(x, y, z, sx, sy, sz, seed, tones=("stone", "rock", "stone_dk")):
    return ck.blob((x, y, z), (sx, sy, sz), tones, sub=1, jitter=0.2, seed=seed, flat=0.55)


def seawall():
    out = ck.Part()
    rows = ((0.0, 0.46, -0.62), (0.46, 0.9, -0.46), (0.9, 1.32, -0.32), (1.32, 1.62, -0.22))
    r = random.Random(5)

    if ck.LOD == 2:
        out += ck.box(-2.0, -0.45, -0.2, 2.0, 0.9, 1.62, "stone")
    else:
        out += ck.box(-2.0, -0.18, -0.4, 2.0, 0.9, 1.6, "stone_dk", skip="d")

        for k, (z0, z1, yf) in enumerate(rows):
            x = -2.0
            first = 0.55 if k % 2 else 1.0

            while x < 1.99:
                w = first if x == -2.0 else r.uniform(0.75, 1.15)
                x1 = min(2.0, x + w)

                if 2.0 - x1 < 0.3:
                    x1 = 2.0

                col = ("stone", "stone_lt", "stone", "stone_dk")[int(r.random() * 3.4)]
                out += a.panel(x + 0.012, x1 - 0.012, z0 + 0.012, z1 - 0.012, yf - r.uniform(0.0, 0.04), 0.0, col)
                x = x1

    out += ck.box(-2.0, -0.4, 1.62, 2.0, 1.12, 1.85, "stone_lt", c=0.07)
    out += ck.box(-2.0, -0.3, 1.52, 2.0, -0.16, 1.62, "stone_dk", d=0)

    for i, (x, y, s) in enumerate(((-1.45, -0.82, 0.42), (-0.5, -0.9, 0.3), (0.3, -0.84, 0.44), (1.35, -0.88, 0.34))):
        out += ck.blob((x, y, s * 0.18), (s * 1.15, s * 0.65, s * 0.72), ("rock", "stone_dk", "stone_dk"), sub=0, jitter=0.26, seed=i + 12, flat=0.45, d=1)

    return out


ALL = {
    "hut": (hut, {"reach": 0.7, "ao": 0.45}),
    "tower": (tower, {}),
    "cubicles": (cubicles, {}),
    "parasol": (parasol, {"reach": 0.8, "ao": 0.5}),
    "lounger": (lounger, {"reach": 0.6}),
    "deckchair": (deckchair, {"reach": 0.5, "ao": 0.5}),
    "windbreak": (windbreak, {"reach": 0.6, "ao": 0.45}),
    "driftwood": (driftwood, {"reach": 0.6}),
    "pots": (pots, {"reach": 0.5}),
    "nets": (nets, {"reach": 0.6}),
    "fishcrate": (fishcrate, {"reach": 0.3, "grime_h": 0.1}),
    "rod": (rod, {"reach": 0.4, "grime_h": 0.2}),
    "buoy": (buoy, {"reach": 0.6}),
    "flag": (flag, {"reach": 0.6}),
    "dunefence": (dunefence, {"reach": 0.6, "grime_h": 0.4}),
    "walkover": (walkover, {"reach": 0.8}),
    "groyne": (groyne, {"reach": 0.8}),
    "seawall": (seawall, {"reach": 1.0}),
}
