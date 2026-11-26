import math
import random

import bmesh
import jp
from jp import add, bar, bx, flat, place
from mathutils import Vector

k = jp.k


def hull(points, color):
    bm = bmesh.new()

    for p in points:
        bm.verts.new(p)

    res = bmesh.ops.convex_hull(bm, input=bm.verts)
    junk = list({v for v in res["geom_interior"] + res["geom_unused"] if isinstance(v, bmesh.types.BMVert)})
    bmesh.ops.delete(bm, geom=junk, context="VERTS")
    bmesh.ops.dissolve_limit(bm, angle_limit=0.02, verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    return k.lpm._object("hull", bm, jp.c(color))


def blob(at, r, color, seed, n=12, rough=0.18, floor=None):
    rnd = random.Random(seed)
    n = n * (2 if jp.MID else 1)
    pts = []

    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996 + rnd.uniform(-0.3, 0.3)
        s = 1 + rnd.uniform(-rough, rough)
        p = Vector((at[0] + rr * math.cos(a) * r[0] * s, at[1] + rr * math.sin(a) * r[1] * s, at[2] + z * r[2] * s))

        if floor is not None:
            p.z = max(p.z, floor)

        pts.append(p)

    return hull(pts, color)


def wheel(x, y, z, r, w, color="jp_char", hub="jp_alu_dark", sides=8):
    tyre = k.prism("tyre", sides * jp.N, r, w, (0, 0, -w / 2), jp.c(color))
    cap = k.prism("hub", 6 * jp.N, r * 0.45, w + 0.02, (0, 0, -w / 2 - 0.01), jp.c(hub))

    for ob in (tyre, cap):
        k.rotate(ob, 90, "Y")
        k.move(ob, x, y, z)

    return [tyre, cap]


def slab(length, width, thick, a, b, color):
    ax, az = a
    bx_, bz = b
    run = math.hypot(bx_ - ax, bz - az)
    ob = flat((run, width, thick), (0, 0, -thick / 2), color)
    k.rotate(ob, -math.degrees(math.atan2(bz - az, bx_ - ax)), "Y")
    k.move(ob, (ax + bx_) / 2, 0, (az + bz) / 2)

    return ob


def gable(w, d, rise, z, over=0.22, color="jp_tile", wall="jp_wood", rows=None):
    rows = rows or max(4, int((w / 2 + over) / 0.34)) * jp.N
    half = w / 2 + over
    drop = over * rise / (w / 2)
    length = d + over * 2
    items = []

    for side in (-1, 1):
        items.append(k.sweep("roof", jp.slope_profile(half, rise, -drop, rows, side, th=0.1, step=0.04), length, (0, 0, z), jp.c(color), axis="y"))

    items.append(bx((0.26, length + 0.04, 0.16), (0, 0, z + rise - 0.08), color + "_dark", 0.03))

    for sy in (-1, 1):
        tri = k.sweep("gable", [(-w / 2, -0.1), (w / 2, -0.1), (0, rise - 0.22)], jp.T, (0, sy * (d / 2 - jp.T / 2), z), jp.c(wall), axis="y")
        jp.soft.append(tri)
        items.append(tri)

        for side in (-1, 1):
            items.append(k.sweep("barge", [(0, rise + 0.03), (side * half, -drop + 0.03), (side * half, -drop - 0.12), (0, rise - 0.12)], 0.07, (0, sy * (length / 2 + 0.02), z), jp.c("jp_char"), axis="y"))

    for sx in (-1, 1):
        items.append(bx((0.07, length + 0.04, 0.16), (sx * (half + 0.02), 0, z - drop - 0.15), "jp_char", 0.01))

    return items


def battens(width, height, holes, color, step=0.42, skip=()):
    items = []
    n = int(width / step)

    for i in range(n + 1):
        x = -width / 2 + 0.06 + i * (width - 0.12) / n

        if any(abs(x - hx) < hw / 2 + 0.08 for hx, hw in holes):
            continue

        items.append(flat((0.07, 0.05, height - 0.22), (x, -0.025, 0), color))

    return items


def wheelie():
    jp.setup(41)
    body = k.beveled_box("bin", (0.56, 0.58, 0.95), (0, 0.0, 0.06), jp.c("jp_metal"), 0.03, taper_top=(1.1, 1.08))
    add(body)

    for z in (0.32, 0.62):
        add(flat((0.6, 0.62, 0.05), (0, 0.0, z), "jp_metal"))

    add(flat((0.32, 0.02, 0.3), (0, -0.3, 0.6), "jp_tile_light"))
    add(bx((0.66, 0.68, 0.07), (0, 0.005, 1.01), "jp_tile", 0.02))
    add(flat((0.5, 0.06, 0.04), (0, -0.33, 0.98), "jp_tile_dark"))
    add(bx((0.5, 0.12, 0.05), (0, 0.06, 1.06), "jp_tile", 0.015))
    add(bar((-0.27, 0.33, 0.98), (0.27, 0.33, 0.98), 0.025, "jp_char", 6))

    for sx in (-1, 1):
        add(flat((0.05, 0.06, 0.08), (sx * 0.24, 0.3, 0.93), "jp_char"))
        add(flat((0.06, 0.12, 0.2), (sx * 0.2, 0.26, 0.0), "jp_char"))

    add(bar((-0.29, 0.25, 0.1), (0.29, 0.25, 0.1), 0.02, "jp_alu_dark", 4))
    add(wheel(-0.27, 0.25, 0.1, 0.1, 0.06))
    add(wheel(0.27, 0.25, 0.1, 0.1, 0.06))
    add(flat((0.4, 0.06, 0.06), (0, -0.25, 0.0), "jp_char"))

    return jp.finish("wheelie", 600, fuse_soft=False)


def shed():
    jp.setup(42)
    w = 3.5
    d = 3.5
    h = 2.45
    z0 = 0.16
    fy = -d / 2
    side = d - 2 * jp.T
    add(bx((w + 0.14, d + 0.14, z0), (0, 0, 0), "jp_concrete", 0.03))
    front = [(-0.7, 0, 0.95, 2.05), (0.95, 1.05, 0.75, 0.75)]
    place(jp.wall(w, h, front, "jp_wood_light"), 0, fy, z0, 0)
    place(k_shift(jp.door(0.95, 2.05, "jp_tile", frame="jp_cream"), -0.7, 0, 0), 0, fy, z0, 0)
    place(k_shift(jp.window(0.75, 0.75, "jp_wood", frame="jp_cream"), 0.95, 0, 1.05), 0, fy, z0, 0)
    place(battens(w, h, [(-0.7, 0.95), (0.95, 0.75)], "jp_wood"), 0, fy, z0, 0)
    place(jp.wall(w, h, [], "jp_wood_light"), 0, -fy, z0, 180)
    place(battens(w, h, [], "jp_wood"), 0, -fy, z0, 180)
    place(jp.wall(side, h, [(0.3, 1.0, 1.0, 0.75)], "jp_wood_light"), w / 2, 0, z0, 90)
    place(k_shift(jp.window(1.0, 0.75, "jp_wood", frame="jp_cream"), 0.3, 0, 1.0), w / 2, 0, z0, 90)
    place(battens(side, h, [(0.3, 1.0)], "jp_wood"), w / 2, 0, z0, 90)
    place(jp.wall(side, h, [], "jp_wood_light"), -w / 2, 0, z0, -90)
    place(battens(side, h, [], "jp_wood"), -w / 2, 0, z0, -90)

    for sx in (-1, 1):
        for sy in (-1, 1):
            add(flat((0.16, 0.16, h), (sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), z0), "jp_cream"))

    add(bx((w + 0.12, d + 0.12, 0.14), (0, 0, z0 + h - 0.3), "jp_cream", 0.02))
    add(bx((0.95, 0.24, 0.2), (0.95, fy - 0.12, z0 + 0.82), "jp_wood_dark", 0.02))

    for i in range(4):
        add(flat((0.1, 0.1, 0.08), (0.65 + i * 0.2, fy - 0.12, z0 + 1.02), ("jp_cherry", "jp_sign", "jp_cherry_dark", "jp_sign")[i]))

    add(bx((1.3, 0.36, 0.1), (-0.7, fy - 0.18, 0), "jp_concrete", 0.02))
    add(gable(w, d, 1.38, z0 + h, over=0.24, color="jp_tile", wall="jp_wood_light"))
    add(flat((0.24, 0.05, 0.24), (0, fy - 0.03, z0 + h + 0.55), "jp_char"))

    for i in range(3):
        add(flat((0.03, 0.06, 0.18), (-0.06 + i * 0.06, fy - 0.035, z0 + h + 0.58), "jp_wood_dark"))

    add(jp.pipe(w / 2 + 0.02, fy + 0.12, 0.0, z0 + h - 0.1))

    return jp.finish("shed", 2500, fuse_soft=False)


def k_shift(items, x, y, z):
    for it in items:
        k.move(it, x, y, z)

    return items


def toolshed():
    jp.setup(43)
    w = 1.8
    d = 1.62
    z0 = 0.12
    zf = 2.4
    zb = 2.2
    body = k.sweep("body", [(-d / 2, 0), (d / 2, 0), (d / 2, zb - z0), (-d / 2, zf - z0)], w, (0, 0, z0), jp.c("jp_cream"), axis="y")
    k.rotate(body, 90)
    k.chamfer(body, 0.02)
    add(body)

    for sx in (-1, 1):
        for sy in (-1, 0, 1):
            add(bx((0.22, 0.4, z0), (sx * 0.75, sy * 0.6, 0), "jp_concrete", 0.02))

    add(bx((w + 0.04, d + 0.04, 0.1), (0, 0, z0), "jp_alu_dark", 0.015))

    for i in range(7):
        y = -d / 2 + 0.2 + i * (d - 0.4) / 6
        top = zf + (zb - zf) * (y + d / 2) / d - 0.12

        for sx in (-1, 1):
            add(flat((0.03, 0.06, top - z0 - 0.12), (sx * (w / 2 + 0.01), y, z0 + 0.1), "jp_cream_dark"))

    for i in range(8):
        x = -w / 2 + 0.18 + i * (w - 0.36) / 7
        add(flat((0.06, 0.03, zb - z0 - 0.24), (x, d / 2 + 0.01, z0 + 0.1), "jp_cream_dark"))

    fy = -d / 2
    add(flat((w - 0.1, 0.05, 0.16), (0, fy - 0.02, zf - 0.3), "jp_cream_dark"))
    add(flat((w - 0.1, 0.06, 0.06), (0, fy - 0.03, z0 + 0.1), "jp_alu_dark"))
    add(flat((w - 0.1, 0.06, 0.06), (0, fy - 0.03, zf - 0.37), "jp_alu_dark"))

    for sx in (-1, 1):
        leaf = bx((0.8, 0.04, 1.84), (sx * 0.42, fy - 0.03, z0 + 0.16), "jp_metal", 0.012)
        add(leaf)

        for z in (0.55, 1.15, 1.75):
            add(flat((0.66, 0.02, 0.05), (sx * 0.42, fy - 0.055, z0 + z), "jp_tile_light"))

        add(bar((sx * 0.08, fy - 0.08, z0 + 0.85), (sx * 0.08, fy - 0.08, z0 + 1.15), 0.018, "jp_alu", 4))

        for z in (0.95, 1.05):
            add(flat((0.03, 0.05, 0.03), (sx * 0.08, fy - 0.06, z0 + z), "jp_alu_dark"))

    add(flat((0.06, 0.04, 0.1), (0, fy - 0.08, z0 + 1.2), "jp_char"))
    add(flat((0.02, 0.05, 1.84), (0, fy - 0.035, z0 + 0.16), "jp_char"))
    rd = 2.0
    run = rd
    pitch = (zf - zb) / d
    zt = zf + 0.24
    roof = k.sweep("roof", [(-rd / 2, zt), (rd / 2, zt - pitch * run), (rd / 2, zt - pitch * run - 0.08), (-rd / 2, zt - 0.08)], 2.0, (0, 0, 0), jp.c("jp_tile"), axis="y")
    k.rotate(roof, 90)
    add(roof)

    for i in range(9):
        x = -0.92 + i * 0.23
        add(bar((x, -rd / 2, zt + 0.01), (x, rd / 2, zt - pitch * run + 0.01), 0.025, "jp_tile_light", 4))

    add(bx((2.04, 0.08, 0.16), (0, -rd / 2, zt - 0.2), "jp_tile_dark", 0.01))
    add(bx((2.04, 0.08, 0.12), (0, rd / 2, zt - pitch * run - 0.16), "jp_tile_dark", 0.01))
    add(sweep_wedge(-w / 2 - 0.02, d, zf, zb))
    add(sweep_wedge(w / 2 + 0.02, d, zf, zb))

    return jp.finish("toolshed", 1500, fuse_soft=False)


def sweep_wedge(x, d, zf, zb):
    ob = k.sweep("wedge", [(-d / 2 - 0.1, zf + 0.12), (d / 2 + 0.1, zb + 0.12), (d / 2 + 0.1, zb - 0.02), (-d / 2 - 0.1, zf - 0.02)], 0.05, (0, 0, 0), jp.c("jp_tile_dark"), axis="y")
    k.rotate(ob, 90)
    k.move(ob, x, 0, 0)

    return ob


def fence():
    jp.setup(44)
    w = 4.0
    h = 1.8

    for x in (-1.94, 0, 1.94):
        add(bx((0.12, 0.12, h - 0.02), (x, 0, 0), "jp_wood_dark", 0.015))

    for z in (0.28, 1.45):
        add(flat((w - 0.1, 0.045, 0.09), (0, 0.035, z), "jp_wood"))

    rnd = random.Random(4)
    n = 26
    bw = (w - 0.2) / n

    for i in range(n):
        x = -w / 2 + 0.1 + bw * (i + 0.5)

        if abs(x) < 0.08:
            continue

        top = h - 0.1 + rnd.uniform(-0.015, 0.015)
        add(flat((bw - 0.022, 0.025, top - 0.05), (x, -0.0, 0.05), "jp_wood_light" if i % 5 else "jp_sand_dark"))

    add(bx((w, 0.16, 0.05), (0, 0, h - 0.07), "jp_wood_dark", 0.012))
    add(flat((w - 0.1, 0.03, 0.08), (0, -0.025, h - 0.2), "jp_wood"))

    for x in (-1.94, 0, 1.94):
        add(bx((0.16, 0.16, 0.05), (x, 0, h - 0.05), "jp_wood_dark", 0.012))
        add(flat((0.16, 0.14, 0.06), (x, 0, 0), "jp_concrete"))

    return jp.finish("fence", 700, fuse_soft=False)


def bamboo():
    jp.setup(45)
    h = 1.6
    rnd = random.Random(5)

    for sx in (-1, 1):
        add(k.prism("post", 8 * jp.N, 0.075, h, (sx * 0.9, 0, 0), jp.c("jp_wood_dark")))
        add(bx((0.2, 0.3, 0.07), (sx * 0.9, 0, 0), "jp_grey", 0.015))
        add(k.prism("cap", 8 * jp.N, 0.082, 0.04, (sx * 0.9, 0, h - 0.04), jp.c("jp_char")))

    n = 21
    sp = 1.68 / n

    for i in range(n):
        x = -0.84 + sp * (i + 0.5)
        top = h - 0.14 + rnd.uniform(-0.01, 0.01)
        r = sp / 2 - 0.003
        pole = bar((x, 0, 0.06), (x, 0, top), r, "jp_sand" if i % 3 else "jp_wood_light", 4 if not jp.MID else 6)
        add(pole)

    for z in (0.3, 0.8, 1.3):
        for sy in (-1, 1):
            add(bar((-0.86, sy * 0.05, z), (0.86, sy * 0.05, z), 0.026, "jp_sand_dark", 4))

        for x in (-0.6, -0.2, 0.2, 0.6):
            add(flat((0.07, 0.17, 0.1), (x + (0.05 if z == 0.8 else 0), 0, z - 0.05), "jp_char"))

    add(bx((1.76, 0.13, 0.1), (0, 0, h - 0.17), "jp_wood_light", 0.02))
    add(bar((-0.88, 0, h - 0.06), (0.88, 0, h - 0.06), 0.045, "jp_sand", 6))

    for x in (-0.45, 0.0, 0.45):
        add(bx((0.07, 0.15, 0.13), (x, 0, h - 0.13), "jp_char", 0.012))

    return jp.finish("bamboo", 1200, fuse_soft=False)


def shirt(x, y, top, color, w=0.42, hgt=0.52):
    items = [flat((w, 0.025, hgt), (x, y, top - hgt), color)]

    for sx in (-1, 1):
        s = flat((0.14, 0.024, 0.3), (0, 0, -0.3), color)
        k.rotate(s, sx * 28, "Y")
        k.move(s, x + sx * (w / 2 - 0.02), y, top - 0.02)
        items.append(s)

    items.append(flat((0.14, 0.03, 0.05), (x, y, top - 0.05), "jp_sign" if color != "jp_sign" else "jp_cream_dark"))

    return items


def pants(x, y, top, color):
    items = [flat((0.36, 0.025, 0.14), (x, y, top - 0.14), color)]

    for sx in (-1, 1):
        items.append(flat((0.16, 0.025, 0.5), (x + sx * 0.095, y, top - 0.62), color))

    return items


def laundry():
    jp.setup(46)
    h = 1.2
    lines = (-0.18, 0.18)

    for sx in (-1, 1):
        x = sx * 1.9
        add(bx((0.18, 0.4, 0.1), (x, 0, 0), "jp_concrete", 0.02))
        add(bar((x, 0, 0.1), (x, 0, h - 0.04), 0.035, "jp_alu_dark", 6))
        add(bx((0.07, 0.46, 0.05), (x, 0, h - 0.07), "jp_alu_dark", 0.012))

        for y in lines:
            add(flat((0.05, 0.05, 0.05), (x, y, h - 0.09), "jp_char"))

    for y in lines:
        add(bar((-1.9, y, h - 0.06), (1.9, y, h - 0.06), 0.013, "jp_alu", 4))

    top = h - 0.07
    fy, by = lines
    add(shirt(-1.3, fy, top, "jp_sign"))
    add(flat((0.42, 0.022, 0.6), (-0.65, fy, top - 0.6), "jp_slate"))
    add(flat((0.42, 0.022, 0.06), (-0.65, fy - 0.003, top - 0.5), "jp_slate_dark"))
    add(pants(0.0, fy, top, "jp_indigo"))
    add(shirt(0.68, fy, top, "jp_cherry_dark", 0.38, 0.46))
    add(flat((0.3, 0.022, 0.34), (1.32, fy, top - 0.34), "jp_sand"))
    add(flat((0.9, 0.022, 0.62), (-1.0, by, top - 0.62), "jp_cream_light"))
    add(flat((0.4, 0.022, 0.5), (0.25, by, top - 0.5), "jp_sand_dark"))
    add(flat((0.36, 0.022, 0.42), (1.0, by, top - 0.42), "jp_slate"))

    for x, y in ((-1.48, fy), (-1.12, fy), (-0.82, fy), (-0.48, fy), (-0.15, fy), (0.15, fy), (0.52, fy), (0.84, fy), (1.2, fy), (1.44, fy), (-1.4, by), (-0.6, by), (0.08, by), (0.42, by), (0.85, by), (1.15, by)):
        add(flat((0.03, 0.04, 0.07), (x, y, top - 0.03), "jp_yellow" if int((x + 2) * 10) % 2 else "jp_alu"))

    return jp.finish("laundry", 700, fuse_soft=False)


def bed():
    jp.setup(47)
    s = 1.0
    hb = 0.3

    for r in range(4):
        a = r * 90
        for i, z in enumerate((0.0, 0.15)):
            b = flat((s - 0.1, 0.05, 0.14), (0, -s / 2 + 0.03, z), "jp_wood" if i == 0 else "jp_wood_light")
            k.rotate(b, a)
            add(b)

        cap = flat((s, 0.09, 0.04), (0, -s / 2 + 0.045, hb), "jp_wood_light")
        k.rotate(cap, a)
        add(cap)

    for sx in (-1, 1):
        for sy in (-1, 1):
            add(flat((0.08, 0.08, hb + 0.02), (sx * (s / 2 - 0.04), sy * (s / 2 - 0.04), 0), "jp_wood_dark"))

    add(flat((s - 0.12, s - 0.12, 0.02), (0, 0, hb - 0.04), "jp_wood_dark"))
    rnd = random.Random(7)
    spots = [(-0.28, -0.26), (0.02, -0.3), (0.29, -0.24), (-0.3, 0.02), (0.0, 0.0), (0.28, 0.04), (-0.25, 0.28), (0.04, 0.29), (0.3, 0.3)]
    flowers = ("jp_cherry", "jp_sign", "jp_yellow", "jp_cherry_dark", "jp_maple_light")

    for i, (x, y) in enumerate(spots):
        add(blob((x, y, hb - 0.02), (0.13, 0.12, 0.09), ("jp_leaf", "jp_leaf_dark", "jp_leaf_light")[i % 3], 30 + i, n=8, floor=hb - 0.02))

        for j in range(2 if i % 2 else 3):
            a = rnd.uniform(0, 6.28)
            fx = x + math.cos(a) * 0.07
            fy = y + math.sin(a) * 0.07
            add(k.prism("fl", 5, 0.05, 0.025, (fx, fy, hb + 0.05 + rnd.uniform(0, 0.03)), jp.c(flowers[(i + j) % len(flowers)])))

    return jp.finish("bed", 700, fuse_soft=False)


def pane(size, at, color):
    return flat(size, at, color)


def greenhouse():
    jp.setup(48)
    w = 4.0
    d = 6.0
    knee = 0.45
    eave = 2.35
    rise = 2.05
    hw = w / 2 - 0.08
    hd = d / 2
    bays = 6
    by = d / bays
    pitch = math.degrees(math.atan2(rise, hw))
    slope = math.hypot(hw, rise)
    fr = "jp_alu"
    add(flat((hw * 2 - 0.2, d - 0.2, 0.03), (0, 0, 0), "jp_grey"))

    for sx in (-1, 1):
        add(bx((0.16, d, knee), (sx * (hw - 0.08), 0, 0), "jp_concrete", 0.02))
        add(bx((0.2, d + 0.04, 0.05), (sx * (hw - 0.08), 0, knee), "jp_grey", 0.012))

    add(bx((hw * 2 - 0.32, 0.16, knee), (0, hd - 0.08, 0), "jp_concrete", 0.02))

    for x0, x1 in ((-hw + 0.16, -0.55), (0.55, hw - 0.16)):
        add(bx((x1 - x0, 0.16, knee), ((x0 + x1) / 2, -hd + 0.08, 0), "jp_concrete", 0.02))

    for sx in (-1, 1):
        x = sx * (hw - 0.06)

        for i in range(bays + 1):
            y = -hd + 0.04 + i * (d - 0.08) / bays
            add(flat((0.07, 0.07, eave - knee), (x, y, knee), fr))

        add(flat((0.09, d, 0.08), (x, 0, eave - 0.08), fr))
        add(flat((0.07, d, 0.05), (x, 0, 1.35), fr))

        for i in range(bays):
            y = -hd + by * (i + 0.5)
            add(pane((0.02, by - 0.08, 1.35 - knee - 0.05), (x + sx * 0.01, y, knee + 0.05), "jp_glass"))

            if (sx == 1 and i == 2) or (sx == -1 and i == 4):
                p = pane((0.02, by - 0.1, eave - 1.4 - 0.09), (0, 0, -(eave - 1.4 - 0.09)), "jp_glass_light")
                k.rotate(p, sx * 16, "Y")
                k.move(p, x + sx * 0.05, y, eave - 0.1)
                add(p)
                add(flat((0.05, by - 0.1, 0.04), (x + sx * 0.03, y, 1.4), "jp_char"))
            else:
                add(pane((0.02, by - 0.08, eave - 1.4 - 0.09), (x + sx * 0.01, y, 1.4), "jp_glass_light" if i % 2 else "jp_glass"))

    for i in range(bays + 1):
        y = -hd + 0.04 + i * (d - 0.08) / bays

        for sx in (-1, 1):
            add(bar((sx * (hw - 0.02), y, eave + 0.06), (0, y, eave + rise + 0.06), 0.035, fr, 4))

    add(bx((0.12, d + 0.04, 0.1), (0, 0, eave + rise - 0.06), fr, 0.015))

    for sx in (-1, 1):
        for i in range(bays):
            y = -hd + by * (i + 0.5)
            col = "jp_glass_light" if (i + (sx > 0)) % 2 else "jp_glass"

            if sx == 1 and i == 1:
                low = pane((slope * 0.6 - 0.06, by - 0.04, 0.025), (0, 0, -0.0125), col)
                k.rotate(low, pitch, "Y")
                k.move(low, hw * 0.7, y, eave + rise * 0.3 + 0.02)
                add(low)
                vent = pane((slope * 0.4 - 0.06, by - 0.12, 0.025), ((slope * 0.4 - 0.06) / 2, 0, -0.0125), "jp_glass_light")
                k.rotate(vent, pitch - 16, "Y")
                k.move(vent, 0.04, y, eave + rise + 0.03)
                add(vent)
                add(flat((0.05, by - 0.06, 0.05), (hw * 0.4 + 0.02, y, eave + rise * 0.6 - 0.02), fr))
                continue

            p = pane((slope - 0.04, by - 0.04, 0.025), (0, 0, -0.0125), col)
            k.rotate(p, sx * pitch, "Y")
            k.move(p, sx * hw / 2, y, eave + rise / 2 + 0.02)
            add(p)

    for sy in (-1, 1):
        y = sy * (hd - 0.03)
        tri = k.sweep("gl", [(-hw + 0.1, 0), (hw - 0.1, 0), (0, rise - 0.1)], 0.02, (0, y, eave), jp.c("jp_glass_light" if sy < 0 else "jp_glass"), axis="y")
        add(tri)
        add(flat((w - 0.1, 0.08, 0.08), (0, y, eave - 0.08), fr))
        add(flat((0.07, 0.07, rise), (0, y, eave), fr))

        for x in (-hw + 0.06, hw - 0.06):
            add(flat((0.07, 0.07, eave - knee), (x, y, knee), fr))

        if sy > 0:
            for x in (-hw / 2, 0, hw / 2):
                add(flat((0.06, 0.07, eave - knee), (x, y, knee), fr))

            for i in range(4):
                x = -hw + hw / 2 * (i + 0.5)
                add(pane((hw / 2 - 0.08, 0.02, eave - knee - 0.1), (x, y, knee + 0.05), "jp_glass" if i % 2 else "jp_glass_light"))
        else:
            for x in (-0.55, 0.55):
                add(flat((0.07, 0.08, eave - 0.08), (x, y, 0), fr))

            for x0, x1 in ((-hw + 0.06, -0.55), (0.55, hw - 0.06)):
                add(pane((x1 - x0 - 0.06, 0.02, eave - knee - 0.1), ((x0 + x1) / 2, y, knee + 0.05), "jp_glass"))

            add(flat((1.04, 0.08, 0.06), (0, y, 2.1), fr))
            add(flat((1.04, 0.04, 0.03), (0, y - 0.02, 0), "jp_alu_dark"))
            add(flat((1.04, 0.05, 0.05), (0, y, 2.15), "jp_alu_dark"))
            add(bx((0.9, 0.05, 2.0), (-1.05, y - 0.09, 0.05), "jp_alu", 0.01))
            add(pane((0.76, 0.02, 1.0), (-1.05, y - 0.12, 0.95), "jp_glass_light"))
            add(pane((0.76, 0.02, 0.7), (-1.05, y - 0.12, 0.17), "jp_glass"))

    for sx in (-1, 1):
        x = sx * (hw - 0.55)
        add(bx((0.62, d - 1.4, 0.05), (x, 0.3, 0.8), "jp_wood_light", 0.012))
        add(bx((0.4, d - 1.6, 0.04), (x + sx * 0.1, 0.3, 1.45), "jp_wood_light", 0.012))

        for y in (-2.2, 0.3, 2.8):
            for dx in (-0.26, 0.26):
                add(flat((0.05, 0.05, 0.8), (x + dx, y - 0.0, 0), "jp_wood"))

            add(flat((0.04, 0.04, 0.65), (x + sx * 0.26, y, 0.85), "jp_wood"))

        for j, y in enumerate((-2.0, -1.3, -0.6, 0.1, 0.8, 1.5, 2.2)):
            add(k.prism("pot", 6 * jp.N, 0.1, 0.14, (x - sx * 0.12, y, 0.85), jp.c("jp_maple"), radius_top=0.13))
            add(blob((x - sx * 0.12, y, 1.08), (0.16, 0.16, 0.13), ("jp_leaf", "jp_leaf_dark", "jp_leaf_light")[j % 3], 60 + j + sx * 10, n=8))

            if j % 2 == 0:
                add(k.prism("pot", 6 * jp.N, 0.07, 0.1, (x + sx * 0.12, y + 0.3, 1.49), jp.c("jp_maple")))
                add(blob((x + sx * 0.12, y + 0.3, 1.65), (0.11, 0.11, 0.1), "jp_leaf_dark", 80 + j + sx * 10, n=8))

    return jp.finish("greenhouse", 2500, fuse_soft=False)


def grill():
    jp.setup(49)
    zt = 0.74
    lw = 0.62
    ld = 0.4

    for sx in (-1, 1):
        for sy in (-1, 1):
            add(bar((sx * lw / 2, sy * ld / 2, 0.06 if sx < 0 else 0.02), (sx * lw / 2, sy * ld / 2, zt), 0.022, "jp_char", 4))

    add(wheel(-lw / 2 - 0.04, -ld / 2, 0.09, 0.09, 0.05))
    add(wheel(-lw / 2 - 0.04, ld / 2, 0.09, 0.09, 0.05))
    add(bar((-lw / 2 - 0.04, -ld / 2 - 0.03, 0.09), (-lw / 2 - 0.04, ld / 2 + 0.03, 0.09), 0.02, "jp_alu_dark", 4))

    for sy in (-1, 1):
        add(flat((0.05, 0.05, 0.04), (lw / 2, sy * ld / 2, 0.0), "jp_char"))

    for i in range(5):
        add(flat((lw, 0.07, 0.03), (0, -ld / 2 + 0.04 + i * (ld - 0.08) / 4, 0.26), "jp_wood_light"))

    for sy in (-1, 1):
        add(flat((lw + 0.04, 0.03, 0.04), (0, sy * ld / 2, 0.24), "jp_char"))

    add(bx((0.62, 0.42, 0.18), (0, 0, zt), "jp_char", 0.02))
    add(flat((0.7, 0.5, 0.04), (0, 0, zt + 0.17), "jp_char"))
    r = 0.25
    segs = 4 * jp.N
    pts = [(r * math.cos(math.pi * i / segs), r * math.sin(math.pi * i / segs)) for i in range(segs + 1)]
    lid = k.sweep("lid", pts, 0.66, (0, 0, zt + 0.21), jp.c("jp_tile_dark"), axis="y")
    k.rotate(lid, 90)
    k.move(lid, 0, 0, 0)
    add(lid)

    for x in (-0.33, 0.33):
        cap = k.sweep("lidend", pts, 0.03, (0, 0, zt + 0.21), jp.c("jp_char"), axis="y")
        k.rotate(cap, 90)
        k.move(cap, x, 0, 0)
        add(cap)

    add(bar((-0.2, -r - 0.07, zt + 0.32), (0.2, -r - 0.07, zt + 0.32), 0.02, "jp_alu", 6))

    for x in (-0.18, 0.18):
        add(flat((0.03, 0.08, 0.03), (x, -r - 0.03, zt + 0.31), "jp_alu_dark"))

    add(k.prism("thermo", 6 * jp.N, 0.04, 0.02, (0, 0, 0), jp.c("jp_sign")))
    k.rotate(parts_last(), 90, "X")
    k.move(parts_last(), 0, -r * 0.62, zt + 0.42)
    add(bx((0.09, 0.09, 0.05), (0.18, 0.0, zt + 0.21 + r - 0.01), "jp_char", 0.01))

    for sx in (-1, 1):
        x0 = sx * 0.35
        x1 = sx * 0.58
        add(flat((0.05, 0.38, 0.03), (sx * 0.47, 0, zt + 0.11), "jp_char"))

        for i in range(4):
            add(flat((0.22, 0.085, 0.03), ((x0 + x1) / 2, -0.15 + i * 0.1, zt + 0.14), "jp_wood_light"))

        add(bar((sx * 0.33, 0, zt - 0.04), (sx * 0.5, 0, zt + 0.11), 0.015, "jp_char", 4))

    for x in (-0.12, 0.0, 0.12):
        add(flat((0.07, 0.03, 0.06), (x, -0.215, zt + 0.06), "jp_alu_dark"))

    return jp.finish("grill", 900, fuse_soft=False)


def parts_last():
    return jp.parts[-1]


def barrow():
    jp.setup(50)
    tw = 0.34 * 1.45
    td = 0.52 * 1.42
    r0 = 0.5 * math.sqrt(2)
    r1 = r0 * 1.43
    tray = k.lathe("tray", [(0, 0), (r0, 0), (r1, 0.3), (r1 - 0.06, 0.3), (r0 - 0.06, 0.05), (0, 0.05)], 4, (0, 0, 0), jp.c("jp_metal"))
    k.rotate(tray, 45)
    k.scale(tray, 0.34, 0.52, 1)
    k.paint(tray, jp.c("jp_tile_dark"), lambda c, n, i: c.z > 0.02 and (n.x * c.x + n.y * c.y < -0.001 or n.z > 0.5) and c.z < 0.299)
    k.move(tray, 0, -0.06, 0.42)
    add(tray)

    for sx in (-1, 1):
        add(flat((0.035, td + 0.03, 0.035), (sx * (tw / 2 + 0.005), -0.06, 0.705), "jp_tile"))

    for sy in (-1, 1):
        add(flat((tw + 0.04, 0.035, 0.035), (0, -0.06 + sy * (td / 2 + 0.005), 0.705), "jp_tile"))

    wy = -0.5
    wz = 0.18
    add(wheel(0, wy, wz, 0.18, 0.08, sides=10))
    add(bar((-0.06, wy, wz), (0.06, wy, wz), 0.02, "jp_alu_dark", 4))

    for sx in (-1, 1):
        add(bar((sx * 0.06, wy, wz), (sx * 0.18, -0.2, 0.4), 0.022, "jp_alu_dark", 4))
        add(bar((sx * 0.18, -0.2, 0.4), (sx * 0.235, 0.5, 0.52), 0.026, "jp_wood_light", 6))
        add(bar((sx * 0.235, 0.5, 0.52), (sx * 0.245, 0.64, 0.54), 0.03, "jp_char", 6))
        add(bar((sx * 0.19, 0.18, 0.43), (sx * 0.2, 0.25, 0.0), 0.02, "jp_alu_dark", 4))
        add(flat((0.05, 0.1, 0.03), (sx * 0.2, 0.25, 0.0), "jp_char"))

    add(bar((-0.2, 0.2, 0.2), (0.2, 0.2, 0.2), 0.015, "jp_alu_dark", 4))

    return jp.finish("barrow", 700, fuse_soft=False)


def olive():
    jp.setup(51)
    pot = k.lathe("pot", [(0, 0), (0.26, 0), (0.32, 0.44), (0.36, 0.46), (0.36, 0.54), (0.31, 0.54), (0.3, 0.5), (0, 0.5)], 8 * jp.N, (0, 0, 0), jp.c("jp_sand_dark"))
    k.paint(pot, jp.c("jp_wood_dark"), lambda c, n, i: n.z > 0.8 and c.z < 0.52 and c.z > 0.3)
    k.paint(pot, jp.c("jp_sand"), lambda c, n, i: c.z > 0.45 and not (n.z > 0.8 and c.z < 0.52))
    add(pot)
    add(k.prism("band", 8 * jp.N, 0.305, 0.05, (0, 0, 0.18), jp.c("jp_sand")))
    add(bar((0, 0, 0.45), (0.04, 0.02, 0.95), 0.06, "jp_bark", 6))
    add(bar((0.04, 0.02, 0.95), (-0.05, -0.02, 1.3), 0.05, "jp_bark", 6))
    add(bar((0.04, 0.02, 0.95), (0.32, 0.05, 1.32), 0.035, "jp_bark", 5))
    add(bar((-0.05, -0.02, 1.3), (-0.35, 0.1, 1.5), 0.03, "jp_bark", 5))
    add(bar((-0.05, -0.02, 1.3), (0.05, -0.2, 1.6), 0.03, "jp_bark", 5))
    canopy = [
        ((-0.05, 0.0, 1.62), (0.42, 0.4, 0.34), "jp_leaf"),
        ((0.38, 0.08, 1.48), (0.32, 0.32, 0.27), "jp_leaf_dark"),
        ((-0.4, 0.12, 1.55), (0.3, 0.32, 0.27), "jp_leaf_light"),
        ((0.12, -0.3, 1.5), (0.3, 0.28, 0.25), "jp_metal"),
        ((-0.15, 0.32, 1.48), (0.28, 0.28, 0.24), "jp_leaf_dark"),
        ((0.15, 0.1, 1.8), (0.28, 0.28, 0.2), "jp_leaf"),
    ]

    for i, (at, r, col) in enumerate(canopy):
        add(blob(at, r, col, 90 + i, n=12))

    return jp.finish("olive", 900, fuse_soft=False)


def firewood():
    jp.setup(52)
    w = 2.0
    rnd = random.Random(12)

    for sy in (-1, 1):
        add(bx((w - 0.1, 0.1, 0.1), (0, sy * 0.22, 0), "jp_wood_dark", 0.015))

    for sx in (-1, 1):
        for sy in (-1, 1):
            hgt = 0.94 if sy < 0 else 1.0
            add(flat((0.09, 0.09, hgt), (sx * 0.95, sy * 0.3, 0), "jp_wood_dark"))

        add(flat((0.07, 0.6, 0.08), (sx * 0.95, 0, 0.15), "jp_wood"))
        add(bar((sx * 0.95, -0.3, 0.15), (sx * 0.95, 0.3, 0.95), 0.025, "jp_wood", 4))

    r = 0.08
    row = 0
    z = 0.1 + r

    while z < 0.95:
        off = (row % 2) * r
        x = -0.88 + r + off

        while x < 0.88 - r + 0.01:
            rr = r * rnd.uniform(0.85, 1.05)
            dy = rnd.uniform(-0.03, 0.03)
            log = bar((x, -0.27 + dy, z), (x, 0.27 + dy, z), rr, "jp_bark", 5)
            k.rotate(log, rnd.uniform(0, 70), "Y", (x, 0, z))
            k.paint(log, jp.c("jp_sand" if rnd.random() > 0.3 else "jp_sand_dark"), lambda c, n, i: abs(n.y) > 0.9)
            add(log)
            x += r * 2

        row += 1
        z += r * 1.75

    zt = 1.1
    pitch = 0.12
    roof = k.sweep("roof", [(-0.49, zt - pitch), (0.49, zt), (0.49, zt - 0.06), (-0.49, zt - pitch - 0.06)], w, (0, 0, 0), jp.c("jp_tile"), axis="y")
    k.rotate(roof, 90)
    add(roof)

    for i in range(8):
        x = -0.875 + i * 0.25
        add(bar((x, -0.49, zt - pitch + 0.005), (x, 0.49, zt + 0.005), 0.02, "jp_tile_light", 4))

    add(flat((w, 0.06, 0.1), (0, -0.46, zt - pitch - 0.14), "jp_wood"))
    add(flat((w, 0.06, 0.08), (0, 0.3, 0.92), "jp_wood"))

    return jp.finish("firewood", 1500, fuse_soft=False)


def compost():
    jp.setup(53)
    w = 0.88
    d = 0.96
    h = 0.74

    for sx in (-1, 1):
        for sy in (-1, 1):
            add(bx((0.08, 0.08, h + 0.03), (sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), 0), "jp_wood_dark", 0.012))

    for i in range(4):
        z = 0.03 + i * 0.18
        col = "jp_wood_light" if i % 2 else "jp_wood"

        for sx in (-1, 1):
            add(flat((0.03, d - 0.08, 0.14), (sx * (w / 2 - 0.02), 0, z), col))

        add(flat((w - 0.08, 0.03, 0.14), (0, d / 2 - 0.02, z), col))

        if i < 2:
            add(flat((w - 0.08, 0.03, 0.14), (0, -d / 2 + 0.02, z), col))

    for sx in (-1, 1):
        add(flat((0.03, 0.04, 0.6), (sx * (w / 2 - 0.1), -d / 2 - 0.015, 0.03), "jp_wood_dark"))

    add(flat((w - 0.08, 0.03, 0.14), (0.0, -d / 2 - 0.03, 0.0), "jp_wood"))
    k.rotate(parts_last(), 8, "X", (0, -d / 2, 0))
    add(blob((0, 0.02, 0.32), (0.38, 0.42, 0.34), "jp_wood_dark", 101, n=14, floor=0.03))
    add(blob((-0.12, -0.08, 0.52), (0.18, 0.16, 0.1), "jp_leaf_dark", 102, n=8))
    add(blob((0.14, 0.12, 0.5), (0.16, 0.18, 0.1), "jp_sand_dark", 103, n=8))
    add(blob((0.12, -0.18, 0.46), (0.12, 0.12, 0.08), "jp_bark", 104, n=8))

    return jp.finish("compost", 700, fuse_soft=False)


def leaf(at, length, yaw, tilt, color):
    ob = k.sweep("leaf", [(0, 0), (length * 0.32, length * 0.3), (0, length), (-length * 0.32, length * 0.3)], 0.022, (0, 0, 0), jp.c(color), axis="y")
    k.rotate(ob, -tilt, "Y")
    k.rotate(ob, yaw)
    k.move(ob, *at)

    return ob


def flower(at, rad, lean=12):
    x, y, z = at
    n = 10 * jp.N
    pts = []

    for i in range(n * 2):
        a = math.pi * i / n
        rr = rad if i % 2 == 0 else rad * 0.62
        pts.append((rr * math.cos(a), rr * math.sin(a)))

    petals = k.sweep("petals", pts, 0.03, (0, 0, 0), jp.c("jp_yellow"), axis="y")
    disc = k.prism("disc", 8 * jp.N, rad * 0.5, 0.06, (0, 0, 0), jp.c("jp_wood_dark"))
    k.rotate(disc, 90, "X")
    k.move(disc, 0, -0.02, 0)
    back = k.prism("calyx", 6 * jp.N, rad * 0.42, 0.08, (0, 0, 0), jp.c("jp_leaf_dark"), radius_top=rad * 0.2)
    k.rotate(back, -90, "X")
    k.move(back, 0, 0.01, 0)
    items = [petals, disc, back]

    for ob in items:
        k.rotate(ob, lean, "X")
        k.move(ob, x, y, z)

    return items


def sunflower():
    jp.setup(54)
    heads = [((-0.18, 0.0, 1.58), 0.2, (-0.05, 0.02)), ((0.2, -0.02, 1.32), 0.17, (0.08, -0.01)), ((-0.02, 0.03, 1.0), 0.14, (0.0, 0.04))]
    add(blob((0, 0, 0.0), (0.2, 0.12, 0.08), "jp_wood_dark", 110, n=8, floor=0.0))

    for (hx, hy, hz), rad, (bx_, by_) in heads:
        add(bar((bx_, by_, 0.0), (bx_ + (hx - bx_) * 0.5, hy + 0.04, hz * 0.55), 0.025, "jp_leaf_dark", 5))
        add(bar((bx_ + (hx - bx_) * 0.5, hy + 0.04, hz * 0.55), (hx, hy + 0.06, hz - rad * 0.3), 0.022, "jp_leaf_dark", 5))
        add(flower((hx, hy - 0.04, hz), rad))

    rnd = random.Random(14)
    spots = [(-0.05, 0.3, 30, "jp_leaf"), (0.05, 0.42, 150, "jp_leaf_dark"), (-0.12, 0.65, 200, "jp_leaf"), (0.12, 0.75, -20, "jp_leaf_light"), (0.0, 0.95, 160, "jp_leaf"), (-0.1, 1.15, 10, "jp_leaf_dark"), (0.15, 1.05, 190, "jp_leaf")]

    for x, z, yaw, col in spots:
        add(leaf((x, rnd.uniform(-0.02, 0.02), z), rnd.uniform(0.24, 0.3), yaw, 55, col))

    return jp.finish("sunflower", 900, fuse_soft=False)


def rock():
    jp.setup(55)
    rnd = random.Random(21)
    n = 22 * (2 if jp.MID else 1)
    pts = []

    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996 + rnd.uniform(-0.4, 0.4)
        s = 1 + rnd.uniform(-0.14, 0.1)
        p = Vector((rr * math.cos(a) * 0.46 * s, rr * math.sin(a) * 0.45 * s, 0.1 + z * 0.5 * s))
        p.x += p.z * 0.12
        p.z = min(max(p.z, 0.0), 0.44 + 0.08 * math.cos(a))
        pts.append(p)

    ob = hull(pts, "jp_grey")
    k.paint(ob, jp.c("jp_grey_dark"), lambda c, n, i: n.z < 0.35)
    k.paint(ob, jp.c("jp_concrete"), lambda c, n, i: 0.35 <= n.z < 0.6 and i % 3 == 0)
    add(ob)
    small = blob((0.36, -0.28, 0.04), (0.13, 0.11, 0.1), "jp_grey_dark", 22, n=8, floor=0.0)
    k.paint(small, jp.c("jp_grey"), lambda c, n, i: n.z > 0.6)
    add(small)

    return jp.finish("rock", 300, fuse_soft=False)


ALL = {
    "wheelie": wheelie,
    "shed": shed,
    "toolshed": toolshed,
    "fence": fence,
    "bamboo": bamboo,
    "laundry": laundry,
    "bed": bed,
    "greenhouse": greenhouse,
    "grill": grill,
    "barrow": barrow,
    "olive": olive,
    "firewood": firewood,
    "compost": compost,
    "sunflower": sunflower,
    "rock": rock,
}
