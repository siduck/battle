import math
import random

import nature_kit as nk
import timber_kit as tk

import forest_palette as fp

k = nk.k


def setup(seed):
    fp.setup(seed)


def finish(name, budget, **kw):
    kw.setdefault("flat", False)
    kw.setdefault("speckle", 0.04)
    kw.setdefault("grime", (0.3, 0.88))

    return nk.finish(name, budget, **kw)


def guy(items, a, b, r=0.014):
    items.append(nk.bar(a, b, r, "fo_rope", 4))
    items.append(nk.bar((b[0], b[1], 0.0), (b[0], b[1], 0.28), 0.03, "fo_wood", 5, taper=0.6))


def tent():
    setup(141)
    W, L, H = 2.8, 3.4, 2.15
    body = k.sweep("tent", [(-W / 2, 0), (W / 2, 0), (0, H)], L, (0, 0, 0), nk.idx("fo_tent"), axis="y")
    attr = body.data.attributes["lpm_color"]

    for p in body.data.polygons:
        n = p.normal

        if abs(n.y) > 0.8:
            attr.data[p.index].value = nk.idx("fo_tent_dk")
        elif n.x > 0:
            attr.data[p.index].value = nk.idx("fo_tent" if nk.hash01(p.center.x, p.center.y, p.center.z, 1) > 0.15 else "fo_tent_lt")
        elif n.x < -0.1:
            attr.data[p.index].value = nk.idx("fo_tent_dk" if nk.hash01(p.center.x, p.center.y, p.center.z, 2) > 0.2 else "fo_tent")

    items = [body]
    fy = -L / 2 - 0.02
    items.append(k.sweep("door", [(-0.6, 0), (0.6, 0), (0, 1.55)], 0.05, (0, fy, 0.02), nk.idx("fo_void"), axis="y"))
    items.append(k.sweep("flapl", [(-0.7, 0), (-0.05, 0), (-0.08, 1.5), (-0.55, 0.9)], 0.04, (0, fy - 0.03, 0.02), nk.idx("fo_canvas"), axis="y"))
    items.append(k.sweep("flapr", [(0.7, 0), (0.05, 0), (0.08, 1.5), (0.55, 0.9)], 0.04, (0, fy - 0.03, 0.02), nk.idx("fo_canvas"), axis="y"))
    items.append(nk.bevbox((W + 0.12, L + 0.1, 0.1), (0, 0, 0.0), "fo_canvas_dk", 0.02))
    items.append(nk.bar((0, -L / 2 - 0.4, H), (0, L / 2 + 0.4, H), 0.045, "fo_wood", 6))

    for sy in (-1, 1):
        guy(items, (0, sy * (L / 2 + 0.4), H), (0, sy * (L / 2 + 0.7), 0.0))

    for sx in (-1, 1):
        for sy in (-1, 1):
            guy(items, (sx * W / 2, sy * L / 3, 0.9), (sx * (W / 2 + 0.45), sy * L / 3, 0.0))

    nk.add(items)

    return finish("tent", 1500, grime=(0.3, 0.9))


def walltent():
    setup(142)
    W, D, WH, RH = 4.2, 3.6, 1.5, 1.4
    items = [nk.bevbox((W, D, WH), (0, 0, 0.0), "fo_canvas", 0.04), nk.bevbox((W + 0.1, D + 0.1, 0.12), (0, 0, 0.0), "fo_canvas_dk", 0.02)]
    roof = k.sweep("roof", [(-D / 2 - 0.25, 0), (D / 2 + 0.25, 0), (0, RH)], W + 0.5, (0, 0, WH), nk.idx("fo_canvas_dk"), axis="y")
    k.rotate(roof, 90)
    attr = roof.data.attributes["lpm_color"]

    for p in roof.data.polygons:
        if p.normal.z > 0.2:
            attr.data[p.index].value = nk.idx("fo_canvas_lt" if nk.hash01(p.center.x, p.center.y, p.center.z, 3) > 0.35 else "fo_canvas")

    items.append(roof)
    items.append(nk.bar((-W / 2 - 0.45, 0, WH + RH), (W / 2 + 0.45, 0, WH + RH), 0.05, "fo_wood", 6))
    fy = -D / 2
    items.append(nk.plain((1.1, 0.06, 1.2), (0.0, fy - 0.01, 0.1), "fo_void"))
    items.append(nk.plain((0.5, 0.05, 1.25), (-0.55, fy - 0.05, 0.1), "fo_canvas_lt"))
    items.append(nk.plain((0.5, 0.05, 1.25), (0.55, fy - 0.05, 0.1), "fo_canvas_lt"))

    for sx in (-1.6, 1.6):
        items.append(nk.plain((0.9, 0.05, 0.55), (sx, fy - 0.01, 0.6), "fo_void"))
        items.append(nk.plain((0.9, 0.03, 0.14), (sx, fy - 0.045, 1.0), "fo_canvas_dk"))

    items.append(nk.bar((1.3, D / 2 - 0.9, WH + 0.2), (1.3, D / 2 - 0.9, WH + RH + 1.25), 0.07, "fo_metal_dk", 6))
    items.append(nk.tube("hat", [(1.3, D / 2 - 0.9, WH + RH + 1.1), (1.3, D / 2 - 0.9, WH + RH + 1.3)], [0.14, 0.04], 6, "fo_metal_dk", cap_top="fo_metal_dk", cap_bottom=True))
    fly = nk.bevbox((W - 0.4, 1.2, 0.05), (0, 0, 0), "fo_canvas_lt", 0.01)
    k.rotate(fly, 12, "X")
    k.move(fly, 0, fy - 0.6, WH + 0.35)
    items.append(fly)

    for sx in (-W / 2 + 0.3, W / 2 - 0.3):
        items.append(nk.bar((sx, fy - 1.15, 0.0), (sx, fy - 1.15, WH + 0.15), 0.045, "fo_wood", 5))

    for sx in (-1, 1):
        guy(items, (sx * (W / 2 + 0.2), 0, WH + 0.2), (sx * (W / 2 + 0.6), D / 3, 0.0))
        guy(items, (sx * (W / 2 + 0.2), 0, WH + 0.2), (sx * (W / 2 + 0.6), -D / 3, 0.0))

    nk.add(items)

    return finish("walltent", 2500, grime=(0.3, 0.9))


def dome():
    setup(143)
    R, H = 1.85, 1.6
    prof = [(R, 0.0)] + [(R * math.sin(math.radians(d)), H * math.cos(math.radians(d))) for d in (84, 66, 46, 24)] + [(0.0, H)]
    body = k.lathe("dome", prof, 12, (0, 0, 0), nk.idx("fo_tent"))
    attr = body.data.attributes["lpm_color"]

    for p in body.data.polygons:
        c = p.center
        sector = int((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi) * 12)

        if c.z < 0.28:
            tone = "fo_canvas_dk"
        else:
            tone = "fo_tent_lt" if sector % 4 == 0 else "fo_tent" if sector % 2 else "fo_tent_dk"

        attr.data[p.index].value = nk.idx(tone)

    items = [body]
    fy = -R * 0.97
    items.append(k.sweep("door", [(-0.45, 0), (0.45, 0), (0.38, 0.75), (0, 1.0), (-0.38, 0.75)], 0.1, (0, fy + 0.0, 0.02), nk.idx("fo_void"), axis="y"))
    items.append(k.sweep("flap", [(-0.5, 0), (0.5, 0), (0.42, 0.82), (0, 1.08), (-0.42, 0.82)], 0.05, (0, fy - 0.03, 0.02), nk.idx("fo_canvas_dk"), axis="y"))
    items.append(k.sweep("door2", [(-0.3, 0.08), (0.3, 0.08), (0.26, 0.62), (0, 0.84), (-0.26, 0.62)], 0.05, (0, fy - 0.06, 0.02), nk.idx("fo_void"), axis="y"))

    for sx in (-1, 1):
        for sy in (-1, 1):
            a = math.atan2(sy, sx)
            guy(items, (math.cos(a) * R * 0.9, math.sin(a) * R * 0.9, 0.3), (math.cos(a) * (R + 0.9), math.sin(a) * (R + 0.9), 0.0))

    nk.add(items)

    return finish("dome", 1200, grime=(0.3, 0.9))


def firepit():
    setup(144)
    items = []
    rnd = random.Random(144)
    n = 11

    for i in range(n):
        a = 2 * math.pi * i / n
        r = 0.7 + rnd.uniform(-0.03, 0.03)
        items.append(nk.hull((math.cos(a) * r, math.sin(a) * r, 0), (rnd.uniform(0.42, 0.52), rnd.uniform(0.34, 0.4), rnd.uniform(0.26, 0.36)), 9, 100 + i, bevel=0.035, segments=1, painter=lambda p: "fo_stone_lt" if p.normal.z > 0.6 else "fo_stone_dk" if p.normal.z < 0.1 else "fo_stone", base_cut=0.4, rot=a))

    items.append(nk.tube("ash", [(0, 0, 0.02), (0, 0, 0.1)], [0.62, 0.58], 10, "fo_ash", cap_top="fo_char"))

    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        items.append(nk.bar((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.1), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.5 + 0.05 * (i % 2)), 0.045, "fo_char" if i % 2 else "fo_bark_dk", 5, taper=0.7))

    nk.add(items)

    return finish("firepit", 1100, grime=None)


def tripod():
    setup(145)
    items = []
    H = 1.65

    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        items.append(nk.bar((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.0), (math.cos(a) * 0.08, math.sin(a) * 0.08, H), 0.05, "fo_wood_dk" if i % 2 else "fo_wood", 5, taper=0.8))

    items.append(nk.tube("hub", [(0, 0, H - 0.06), (0, 0, H + 0.1)], [0.1, 0.09], 6, "fo_metal_dk", cap_top="fo_metal", cap_bottom=True))
    items.append(nk.bar((0, 0, H - 0.05), (0, 0, 0.85), 0.012, "fo_metal_dk", 4))
    prof = [(0.0, 0.0), (0.19, 0.0), (0.26, 0.1), (0.29, 0.2), (0.26, 0.3), (0.22, 0.3), (0.2, 0.26), (0.0, 0.26)]
    items.append(k.lathe("pot", prof, 10, (0, 0, 0.6), nk.idx("fo_char")))
    items.append(nk.tube("handle", [(-0.27, 0, 0.88), (0, 0, 1.0), (0.27, 0, 0.88)], [0.015, 0.015, 0.015], 4, "fo_metal_dk", cap_top=False))

    for i in range(3):
        a = 0.2 + i * 2.1
        items.append(nk.bar((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.1), (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.45), 0.04, "fo_char", 5))

    nk.add(items)

    return finish("tripod", 700, grime=None)


def deck_planks(x0, x1, y, z, width, along="x", tone=("fo_wood_lt", "fo_wood", "fo_wood_gray"), gap=0.015, plank=0.27, seed=0, thick=0.07):
    items = []
    n = max(1, int(round((x1 - x0) / plank)))
    w = (x1 - x0) / n
    rnd = random.Random(seed)

    for i in range(n):
        c = x0 + (i + 0.5) * w
        t = tone[0] if rnd.random() > 0.3 else tone[2] if rnd.random() > 0.5 else tone[1]
        wob = rnd.uniform(-0.01, 0.01)

        if along == "x":
            items.append(nk.bevbox((w - gap, width, thick), (c, y + wob, z), t, 0.012))
        else:
            items.append(nk.bevbox((width, w - gap, thick), (y + wob, c, z), t, 0.012))

    return items


def dock():
    setup(146)
    items = deck_planks(-1.6, 1.6, 0.0, 0.92, 2.56, "x", plank=0.2, seed=1)

    for sy in (-1.0, 0.0, 1.0):
        items.append(nk.bevbox((3.2, 0.2, 0.18), (0, sy, 0.72), "fo_wood_dk", 0.015))

    for sx in (-1.45, 1.45):
        for sy in (-1.1, 1.1):
            items.append(tk.post(sx, sy, 0.0, 1.22, 0.11, ("fo_wood_dk", "fo_wood")))

    for sx in (-1.45, 1.45):
        items.append(nk.bevbox((0.16, 2.56, 0.14), (sx, 0, 0.99), "fo_wood", 0.015))

    nk.add(items)

    return finish("dock", 1700, grime=(0.4, 0.9))


def pier():
    setup(147)
    items = deck_planks(-1.8, 1.8, 0.0, 1.0, 2.6, "y", plank=0.22, seed=2)

    for sy in (-1.0, 0.0, 1.0):
        items.append(nk.bevbox((0.2, 3.58, 0.18), (sy, 0, 0.8), "fo_wood_dk", 0.015))

    for sx in (-1.15, 1.15):
        for sy in (-1.6, 0.0, 1.6):
            items.append(tk.post(sx, sy, 0.0, 1.3, 0.12, ("fo_wood_dk", "fo_wood")))

    for sx in (-1.4, 1.4):
        items.append(nk.tube("lamp", [(sx, 1.6, 1.0), (sx, 1.6, 2.9)], [0.07, 0.055], 6, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk", cap_bottom=True))
        items.append(nk.bevbox((0.24, 0.24, 0.3), (sx, 1.6, 2.6), "fo_metal_dk", 0.02))
        items.append(nk.plain((0.18, 0.18, 0.22), (sx, 1.6, 2.64), "fo_cream"))

    nk.add(items)

    return finish("pier", 2000, grime=(0.4, 0.9))


def bridge_build(name, width, length, hump, seed, rails):
    setup(seed)
    items = []
    top = 0.5

    def zat(x):
        return top + hump * (1 - (x / (length / 2)) ** 2)

    for sy in (-width * 0.36, 0.0, width * 0.36):
        pts, radii = nk.refine([(-length / 2, sy, zat(-length / 2) - 0.3), (0, sy, zat(0) - 0.3), (length / 2, sy, zat(length / 2) - 0.3)], [0.2, 0.2, 0.2], 6)
        items.append(nk.tube("stringer", [(p[0], p[1], zat(p[0]) - 0.28) for p in pts], radii, 6, ["fo_log", "fo_log_lt", "fo_log_dk"], cap_top="fo_log_end", cap_bottom="fo_log_end"))

    n = int(length / 0.46)
    rnd = random.Random(seed)

    for i in range(n):
        x = -length / 2 + (i + 0.5) * length / n
        slope = -2 * hump * x / (length / 2) ** 2
        b = nk.bevbox((length / n - 0.03, width, 0.08), (x, rnd.uniform(-0.015, 0.015), zat(x) - 0.08), "fo_wood_lt" if rnd.random() > 0.3 else "fo_wood", 0.012)
        k.rotate(b, -math.degrees(math.atan(slope)), "Y", (x, 0, zat(x)))
        items.append(b)

    if rails:
        for sy in (-width / 2 + 0.1, width / 2 - 0.1):
            xs = [-length / 2 + 0.3 + i * (length - 0.6) / 4 for i in range(5)]

            for x in xs:
                items.append(tk.post(x, sy, zat(x) - 0.1, zat(x) + 1.0, 0.075))

            pts, radii = nk.refine([(x, sy, zat(x) + 1.02) for x in (xs[0], 0, xs[-1])], [0.06, 0.06, 0.06], 6)
            items.append(nk.tube("rail", [(p[0], sy, zat(p[0]) + 1.02) for p in pts], radii, 6, ["fo_wood", "fo_wood_lt"], cap_top="fo_wood_dk", cap_bottom="fo_wood_dk"))
            pts, radii = nk.refine([(x, sy, zat(x) + 0.55) for x in (xs[0], 0, xs[-1])], [0.045, 0.045, 0.045], 6)
            items.append(nk.tube("rail2", [(p[0], sy, zat(p[0]) + 0.55) for p in pts], radii, 5, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk", cap_bottom="fo_wood_dk"))

    for sx in (-length / 2, length / 2):
        items.append(nk.hull((sx + (0.25 if sx < 0 else -0.25), 0, 0), (0.9, width + 0.4, 0.5), 11, seed, bevel=0.04, painter=lambda p: "fo_stone_lt" if p.normal.z > 0.5 else "fo_stone", base_cut=0.4))

    nk.add(items)

    return finish(name, 3500, grime=(0.4, 0.9))


def bridge():
    return bridge_build("bridge", 2.9, 6.9, 0.0, 148, True)


def footbridge():
    return bridge_build("footbridge", 1.7, 6.9, 0.6, 149, True)


def ramp():
    setup(150)
    items = []
    L, W, H = 9.6, 4.6, 2.18
    slab = k.sweep("ramp", [(-L / 2, 0), (L / 2, 0), (L / 2, 0.18), (-L / 2, H)], W, (0, 0, 0), nk.idx("fo_stone"), axis="y")
    k.rotate(slab, 90)
    attr = slab.data.attributes["lpm_color"]

    for p in slab.data.polygons:
        if p.normal.z > 0.1:
            attr.data[p.index].value = nk.idx("fo_path" if nk.hash01(p.center.x, p.center.y, p.center.z, 6) > 0.3 else "fo_stone_lt")

    items.append(slab)

    for i in range(1, 12):
        y = -L / 2 + i * L / 12
        z = H - (H - 0.18) * (i / 12)
        items.append(nk.plain((W - 0.1, 0.07, 0.04), (0, y, z), "fo_stone_dk"))

    nk.add(items)

    return finish("ramp", 600, grime=None)


ALL = {
    "tent": tent,
    "walltent": walltent,
    "dome": dome,
    "firepit": firepit,
    "tripod": tripod,
    "dock": dock,
    "pier": pier,
    "bridge": bridge,
    "footbridge": footbridge,
    "ramp": ramp,
}
