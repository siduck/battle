import math
import random

import bmesh
import nature_kit as nk
from mathutils import Vector

import forest_palette as fp
import forest_trees as ft


def rock_paint(seed, moss=0.7):
    def paint(p):
        n = p.normal
        c = p.center
        h = nk.hash01(c.x, c.y, c.z, seed)

        if n.z > 0.78 and h < moss:
            return "fo_moss" if h < moss * 0.6 else "fo_moss_lt"

        if n.z > 0.45:
            return "fo_stone_lt" if h > 0.25 else "fo_stone"

        if n.z < 0.1:
            return "fo_stone_dk" if h > 0.3 else "fo_stone"

        return "fo_stone" if h > 0.2 else "fo_stone_lt"

    return paint


def setup(seed):
    fp.setup(seed)


def rock():
    setup(21)
    nk.add(nk.hull((0, 0, 0), (2.3, 2.15, 1.3), 15, 1, bevel=0.07, segments=2, painter=rock_paint(1), base_cut=0.5))
    nk.add(nk.hull((-0.55, 1.0, 0), (0.7, 0.6, 0.5), 11, 2, bevel=0.04, painter=rock_paint(2, 0.3), base_cut=0.4))

    return nk.finish("rock", 700, flat=False, grime=None)


def boulder():
    setup(22)
    nk.add(nk.hull((0.1, 0, 0), (3.6, 3.1, 1.55), 18, 3, bevel=0.1, segments=2, painter=rock_paint(3), base_cut=0.5))
    nk.add(nk.hull((-1.9, 0.3, 0), (1.6, 1.4, 1.0), 13, 4, bevel=0.06, painter=rock_paint(4, 0.4), base_cut=0.4))
    nk.add(nk.hull((1.9, -0.7, 0), (1.5, 1.2, 0.8), 12, 5, bevel=0.06, painter=rock_paint(5, 0.4), base_cut=0.4))
    nk.add(nk.hull((0.9, 1.1, 0), (0.7, 0.6, 0.45), 9, 6, bevel=0.04, painter=rock_paint(6, 0.2), base_cut=0.3))

    return nk.finish("boulder", 1100, flat=False, grime=None)


def spire():
    setup(23)
    nk.add(nk.hull((0, 0, 0), (3.1, 3.4, 3.4), 20, 7, bevel=0.1, segments=2, painter=rock_paint(7, 0.5), base_cut=0.3, strata=0.0, irregular=0.14))
    nk.add(nk.hull((0.1, 0.1, 2.7), (2.2, 2.3, 3.2), 18, 8, bevel=0.09, segments=2, painter=rock_paint(8, 0.2), base_cut=0.9, taper=0.25, irregular=0.12))
    nk.add(nk.hull((0.0, 0.0, 5.1), (1.35, 1.4, 3.3), 15, 9, bevel=0.07, segments=2, painter=rock_paint(9, 0.0), base_cut=0.9, taper=0.65, irregular=0.1))
    nk.add(nk.hull((-1.1, 0.8, 0), (1.1, 1.0, 2.2), 12, 10, bevel=0.06, painter=rock_paint(10, 0.3), base_cut=0.3, taper=0.5))

    return nk.finish("spire", 1400, flat=False, grime=None)


def stump():
    setup(24)
    pts = [(0, 0, 0), (0, 0, 0.12), (0, 0, 0.4), (0, 0, 0.78)]
    items = [nk.tube("stump", pts, [0.72, 0.58, 0.5, 0.48], 10, ft.bark(24), cap_top="fo_log_end", jit=0.12, seed=24)]
    items.append(nk.tube("ring", [(0, 0, 0.778), (0, 0, 0.8)], [0.34, 0.34], 10, "fo_log_ring", cap_top="fo_log_ring"))
    items.append(nk.tube("core", [(0, 0, 0.798), (0, 0, 0.812)], [0.14, 0.14], 8, "fo_log_dk", cap_top="fo_log_dk"))
    r = random.Random(24)

    for i in range(6):
        a = 2 * math.pi * i / 6 + r.uniform(-0.3, 0.3)
        ln = r.uniform(0.72, 0.84)
        items.append(nk.tube("root", [(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.5), (math.cos(a) * ln * 0.6, math.sin(a) * ln * 0.6, 0.18), (math.cos(a) * ln, math.sin(a) * ln, -0.02)], [0.2, 0.14, 0.06], 5, ["fo_bark", "fo_bark_lt", "fo_bark_dk"], cap_top=False))

    nk.add(items)

    return nk.finish("stump", 500, flat=False)


def roots():
    setup(25)
    items = [nk.hull((0, 0, 0), (1.5, 1.3, 0.7), 11, 11, bevel=0.05, painter=lambda p: "fo_earth" if p.normal.z > 0.3 else "fo_earth_lt", base_cut=0.4)]
    r = random.Random(25)

    for i in range(8):
        a = 2 * math.pi * i / 8 + r.uniform(-0.25, 0.25)
        ln = r.uniform(1.4, 2.0)
        ex = math.cos(a) * ln
        ey = math.sin(a) * ln * 0.66
        h = r.uniform(0.75, 1.0)
        pts = [(ex * 0.05, ey * 0.05, h), (ex * 0.3, ey * 0.3, h * 0.92), (ex * 0.6, ey * 0.6, h * 0.5), (ex, ey, -0.03)]
        items.append(nk.tube("root", pts, [0.26, 0.2, 0.13, 0.05], 6, ["fo_bark", "fo_bark_lt", "fo_bark_dk"], cap_top=False, jit=0.2, seed=i))

    items.append(nk.hull((0, 0, 0.55), (0.62, 0.6, 0.5), 10, 12, bevel=0.04, painter=lambda p: "fo_bark_lt", base_cut=0.5))
    nk.add(items)

    return nk.finish("roots", 900, flat=False)


def bush():
    setup(26)
    tones = ("fo_leaf_hi", "fo_leaf", "fo_leaf_lo")
    items = []
    spots = [((-0.85, 0.0, 0.62), (0.9, 0.8, 0.7)), ((0.0, 0.1, 0.8), (1.05, 0.9, 0.85)), ((0.95, -0.1, 0.6), (0.85, 0.75, 0.62)), ((-0.25, -0.45, 0.52), (0.7, 0.62, 0.55)), ((0.45, 0.45, 0.58), (0.72, 0.62, 0.58))]

    for i, (at, size) in enumerate(spots):
        items.append(nk.blob(at, size, tones if at[2] > 0.5 else ("fo_leaf", "fo_leaf_lo", "fo_leaf_dk"), sub=1, seed=50 + i, jitter=0.16, flat_bottom=0.35))

    items.append(nk.chips((0, 0, 0.55), (1.8, 1.0, 0.7), 10, ("fo_leaf_hi", "fo_leaf"), 7, length=0.22))
    r = random.Random(26)

    for i in range(6):
        a = r.uniform(0, 6.28)
        d = r.uniform(0.3, 1.0)
        p = (math.cos(a) * d * 1.0, math.sin(a) * d * 0.6, r.uniform(0.7, 1.05))
        items.append(nk.hull(p, (0.1, 0.1, 0.1), 6, i, bevel=0, painter=lambda q: "fo_accent_dk", base_cut=0.0, irregular=0.0))

    nk.add(items)

    return nk.finish("bush", 900)


def frond(items, base, yaw, length, rise, width, segs, colors, droop=0.5):
    bm = bmesh.new()
    names = []
    spine = []
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    px = -sy
    py = cy

    for i in range(segs + 1):
        t = i / segs
        z = rise * (t * 1.7 - 0.9 * t * t)
        spine.append(Vector((base[0] + cy * length * t, base[1] + sy * length * t, base[2] + z)))

    sv = [bm.verts.new(p) for p in spine]
    wing = []

    for i in range(1, segs + 1):
        t = i / (segs + 1)
        w = width * math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.8
        p = spine[i]
        wing.append((bm.verts.new(p + Vector((px * w, py * w, -w * droop))), bm.verts.new(p + Vector((-px * w, -py * w, -w * droop)))))

    for i in range(segs):
        a = sv[i]
        b = sv[i + 1]

        if i == 0:
            l1, r1 = wing[0]
            tris = [(a, l1, b), (a, b, r1)]
        else:
            l0, r0 = wing[i - 1]
            l1, r1 = wing[i]
            tris = [(a, l0, l1), (a, l1, b), (a, r1, r0), (a, b, r1)] if i < segs else [(a, l0, b), (a, b, r0)]

        for tri in tris:
            n = (tri[1].co - tri[0].co).cross(tri[2].co - tri[0].co)

            if n.z < 0:
                tri = (tri[0], tri[2], tri[1])

            bm.faces.new(tri)
            names.append(colors[0] if (i + len(names)) % 3 else colors[1])
            back = [bm.verts.new(v.co + Vector((0, 0, -0.012))) for v in reversed(tri)]
            bm.faces.new(back)
            names.append(colors[2])

    ob = nk.k.lpm._object("frond", bm, 0)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        attr.data[p.index].value = nk.idx(names[p.index])

    items.append(ob)


def fern():
    setup(27)
    items = []
    r = random.Random(27)

    for i in range(11):
        yaw = 2 * math.pi * i / 11 + r.uniform(-0.2, 0.2)
        ln = r.uniform(0.7, 0.88)
        frond(items, (0, 0, 0.04), yaw, ln, r.uniform(0.95, 1.45) if i % 2 else r.uniform(0.5, 0.95), 0.2, 5, ("fo_grass", "fo_grass_tip", "fo_grass_dk"))

    nk.add(items)

    return nk.finish("fern", 900, flat=False, speckle=0.07, grime=None)


def tuft():
    setup(28)
    nk.add(nk.blades((0, 0, 0), 15, 0.32, 0.9, "fo_grass", 5, lean=0.4, width=0.045, tiles=["fo_grass", "fo_grass_dk", "fo_grass", "fo_grass_tip"]))

    return nk.finish("tuft", 400, flat=False, speckle=0.08, grime=None)


def reeds():
    setup(29)
    items = []

    for i, (cx, cy) in enumerate([(-1.3, 0.0), (0.2, 0.25), (1.35, -0.1), (-0.3, -0.45)]):
        items += nk.blades((cx, cy, 0), 11, 0.55, 0.95, "fo_reed", 30 + i, lean=0.22, width=0.04, tiles=["fo_reed", "fo_reed_dk", "fo_reed"], hmin=0.6)

    nk.add(items)

    return nk.finish("reeds", 900, flat=False, speckle=0.06, grime=None)


def cattail():
    setup(30)
    items = []

    for i, (x, y, h) in enumerate([(0.0, 0.0, 1.8), (0.2, 0.1, 1.5), (-0.18, 0.08, 1.3)]):
        items.append(nk.tube("stem", [(x, y, 0), (x + 0.03, y, h * 0.5), (x + 0.06 * (i - 1), y, h * 0.8)], [0.028, 0.022, 0.02], 4, "fo_reed", cap_top=False))
        zc = h * 0.78
        items.append(nk.tube("head", [(x + 0.06 * (i - 1), y, zc), (x + 0.06 * (i - 1), y, zc + 0.12), (x + 0.06 * (i - 1), y, zc + 0.26)], [0.055, 0.07, 0.04], 6, "fo_cattail", cap_top="fo_cattail"))
        items.append(nk.tube("tip", [(x + 0.06 * (i - 1), y, zc + 0.26), (x + 0.06 * (i - 1), y, zc + 0.4)], [0.012, 0.004], 4, "fo_reed_dk", cap_top=False))

    items += nk.blades((0, 0, 0), 4, 0.15, 1.1, "fo_reed", 3, lean=0.35, width=0.04, tiles=["fo_reed", "fo_reed_dk"])
    nk.add(items)

    return nk.finish("cattail", 400, flat=False, grime=None)


def petals(items, at, n, length, width, color, tilt, yaw0=0.0):
    bm = bmesh.new()
    names = []

    for i in range(n):
        a = yaw0 + 2 * math.pi * i / n
        c = math.cos(a)
        s = math.sin(a)
        base = Vector(at)
        tip = base + Vector((c * length, s * length, length * tilt))
        mid = base + Vector((c * length * 0.55, s * length * 0.55, length * tilt * 0.4))
        l = mid + Vector((-s * width, c * width, 0))
        r = mid + Vector((s * width, -c * width, 0))
        v = [bm.verts.new(p) for p in (base, l, tip, r)]
        f = bm.faces.new(v)

        if f.normal.z < 0:
            f.normal_flip()

        names.append(color)
        back = [bm.verts.new(p.co + Vector((0, 0, -0.008))) for p in reversed(v)]
        g = bm.faces.new(back)

        if g.normal.z > 0:
            g.normal_flip()

        names.append(color + "_dk" if color + "_dk" in nk.k._INDEX else color)

    ob = nk.k.lpm._object("petals", bm, 0)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        attr.data[p.index].value = nk.idx(names[p.index])

    items.append(ob)


def flower():
    setup(31)
    items = [nk.tube("stem", [(0, 0, 0), (0.02, 0, 0.35), (0.0, 0.02, 0.62)], [0.02, 0.016, 0.014], 4, "fo_grass_dk", cap_top=False)]
    items.append(nk.tube("centre", [(0, 0.02, 0.62), (0, 0.02, 0.67)], [0.045, 0.04], 6, "fo_accent_dk", cap_top="fo_accent_dk"))
    petals(items, (0, 0.02, 0.665), 7, 0.17, 0.05, "fo_flower", 0.12)

    for yaw in (0.9, 3.6):
        petals(items, (0, 0, 0.1 + 0.05 * (yaw > 2)), 1, 0.26, 0.06, "fo_grass", 0.5, yaw)

    nk.add(items)

    return nk.finish("flower", 200, flat=False, grime=None)


def toadstool():
    setup(32)
    items = []

    for i, (x, y, h, r) in enumerate([(0, 0, 0.4, 0.3), (0.38, 0.22, 0.26, 0.2), (-0.3, 0.3, 0.2, 0.15)]):
        items.append(nk.tube("stem", [(x, y, 0), (x, y, h * 0.5), (x, y, h)], [r * 0.3, r * 0.22, r * 0.25], 7, ["fo_cream", "fo_wood_lt"], cap_top=False))
        cap = nk.k.lathe("cap", [(0, h + r * 0.75), (r * 0.5, h + r * 0.68), (r * 0.9, h + r * 0.36), (r, h + r * 0.08), (r * 0.6, h)], 9, (x, y, 0), nk.idx("fo_mush"))
        attr = cap.data.attributes["lpm_color"]

        for p in cap.data.polygons:
            c = p.center
            h01 = nk.hash01(c.x, c.y, c.z, 7)
            attr.data[p.index].value = nk.idx("fo_cream" if h01 < 0.17 and p.normal.z > 0.35 else "fo_mush" if h01 > 0.3 else "fo_mush_dk")

        items.append(cap)

    nk.add(items)

    return nk.finish("toadstool", 500, flat=False, grime=None)


def lily():
    setup(33)
    items = []

    for i, (x, y, r, a0) in enumerate([(0, 0, 0.72, 0.35), (-0.45, 0.3, 0.3, 1.2)]):
        bm = bmesh.new()
        n = 14
        c = bm.verts.new((x, y, 0.02))
        ring = []

        for j in range(n + 1):
            a = a0 + 0.35 + (2 * math.pi - 0.35) * j / n
            ring.append(bm.verts.new((x + math.cos(a) * r, y + math.sin(a) * r * 0.95, 0.05 + 0.015 * (j % 2))))

        names = []

        for j in range(n):
            f = bm.faces.new((c, ring[j], ring[j + 1]))

            if f.normal.z < 0:
                f.normal_flip()

            names.append("fo_pad" if j % 3 else "fo_pad_dk")

        ob = nk.k.lpm._object("pad", bm, 0)
        attr = ob.data.attributes["lpm_color"]

        for p in ob.data.polygons:
            attr.data[p.index].value = nk.idx(names[p.index])

        items.append(ob)

    petals(items, (0.12, -0.1, 0.05), 6, 0.14, 0.05, "fo_cream", 0.5)
    nk.add(items)

    return nk.finish("lily", 200, flat=False, grime=None, cull=False)


def log_pile(name, cols, rows, length, r, seed, size_w, posts, sides=6, stagger=True, roof=False):
    setup(seed)
    rnd = random.Random(seed)
    items = []
    step = r * 2.05

    for j in range(rows):
        n = cols - (j % 2 if stagger else 0)
        x0 = -(cols - 1) * step / 2 + (step / 2 if stagger and j % 2 else 0)

        for i in range(n):
            x = x0 + i * step + rnd.uniform(-0.015, 0.015)
            z = r + j * step * 0.9
            rr = r * rnd.uniform(0.88, 1.05)
            items.append(nk.tube("log", [(x, -length / 2 + rnd.uniform(-0.04, 0.04), z), (x, length / 2, z)], [rr, rr], sides, ["fo_log", "fo_log_lt", "fo_log_dk"], cap_top="fo_log_end", cap_bottom="fo_log_end", seed=i + j))

    top = r + (rows - 1) * step * 0.9 + r * 1.3

    for sx in (-1, 1):
        for sy in posts:
            items.append(nk.tube("post", [(sx * (size_w / 2 + 0.02), sy, 0), (sx * (size_w / 2 + 0.02), sy, top + 0.06)], [0.055, 0.045], 5, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk"))

    if roof:
        items.append(nk.bevbox((size_w + 0.4, length + 0.3, 0.05), (0, 0, top + 0.06), "fo_wood_gray", 0.01))

    nk.add(items)

    return nk.finish(name, 900, flat=False, grime=(0.4, 0.82))


def firewood():
    return log_pile("firewood", 6, 4, 0.8, 0.14, 40, 1.78, (-0.32, 0.32), 6)


def cordwood():
    return log_pile("cordwood", 9, 4, 0.55, 0.14, 41, 2.5, (-0.2, 0.2), 5, roof=False)


def fallen():
    setup(34)
    sides = 10

    def pick(i, j):
        if i == 7 and nk.hash01(i, j, 3) < 0.55:
            return "fo_moss"

        h = nk.hash01(i, j, 5)

        return "fo_bark_lt" if h < 0.3 else "fo_bark_dk" if h > 0.78 else "fo_bark"

    pts, radii = nk.refine([(-2.2, 0, 0.5), (-1.0, 0.04, 0.5), (0.3, -0.03, 0.5), (1.5, 0.05, 0.48), (2.25, 0.0, 0.46)], [0.56, 0.5, 0.48, 0.44, 0.4], 3)
    items = [nk.tube("log", pts, radii, sides, pick, cap_top="fo_log_end", cap_bottom="fo_log_end", jit=0.12, seed=34)]
    items.append(nk.tube("ring", [(2.245, 0, 0.46), (2.262, 0, 0.46)], [0.26, 0.26], 8, "fo_log_ring", cap_top="fo_log_ring"))
    items.append(nk.tube("ring", [(-2.195, 0, 0.5), (-2.212, 0, 0.5)], [0.3, 0.3], 8, "fo_log_ring", cap_top="fo_log_ring"))

    for x, side, ln in [(-1.1, 1, 0.6), (0.2, -1, 0.5), (1.2, 1, 0.45)]:
        items.append(nk.tube("stub", [(x, side * 0.3, 0.7), (x + 0.1, side * (0.3 + ln * 0.5), 0.7 + ln * 0.8), (x + 0.15, side * (0.3 + ln * 0.6), 0.5 + ln * 1.2)], [0.1, 0.07, 0.045], 5, ["fo_bark", "fo_bark_dk"], cap_top="fo_log_end"))

    for a, ln in [(0.9, 0.7), (-0.7, 0.8), (2.4, 0.6), (-2.1, 0.7)]:
        items.append(nk.tube("root", [(-2.1, math.sin(a) * 0.2, 0.5), (-2.3 - ln * 0.3, math.sin(a) * ln * 0.6, 0.4 + 0.2 * math.cos(a)), (-2.25 - ln * 0.6, math.sin(a) * ln, 0.1)], [0.2, 0.12, 0.05], 5, ["fo_bark", "fo_bark_dk"], cap_top=False))

    nk.add(items)

    return nk.finish("fallen", 800, flat=False)


ALL = {
    "stump": stump,
    "roots": roots,
    "bush": bush,
    "fern": fern,
    "tuft": tuft,
    "reeds": reeds,
    "cattail": cattail,
    "flower": flower,
    "toadstool": toadstool,
    "lily": lily,
    "boulder": boulder,
    "rock": rock,
    "spire": spire,
    "fallen": fallen,
    "firewood": firewood,
    "cordwood": cordwood,
}
