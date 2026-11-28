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
    kw.setdefault("grime", (0.35, 0.85))

    return nk.finish(name, budget, **kw)


def barrel():
    setup(121)
    parts = k.barrel("barrel", 0.36, 1.1, (0, 0, 0), color="fo_wood", band="fo_metal_dk", sides=12)
    nk.add(parts)

    return finish("barrel", 700)


def bench():
    setup(122)
    items = []

    for i in range(3):
        items.append(nk.bevbox((2.0, 0.15, 0.07), (0, -0.2 + i * 0.16, 0.5), "fo_wood" if i % 2 else "fo_wood_lt", 0.012))

    for sx in (-0.85, 0.85):
        items.append(nk.bar((sx, -0.3, 0.0), (sx, -0.26, 0.5), 0.05, "fo_wood_dk", 5))
        items.append(nk.bar((sx, 0.24, 0.0), (sx, 0.3, 1.0), 0.05, "fo_wood_dk", 5))
        items.append(nk.bar((sx, -0.28, 0.2), (sx, 0.27, 0.2), 0.035, "fo_wood_dk", 5))

    for i in range(3):
        slat = nk.bevbox((2.0, 0.045, 0.14), (0, 0.27 + i * 0.015, 0.65 + i * 0.16), "fo_wood" if i % 2 == 0 else "fo_wood_lt", 0.01)
        items.append(slat)

    nk.add(items)

    return finish("bench", 500)


def picnic():
    setup(123)
    items = []

    for i in range(5):
        items.append(nk.bevbox((2.3, 0.17, 0.07), (0, -0.4 + i * 0.2, 0.74), "fo_wood" if i % 2 else "fo_wood_lt", 0.012))

    for sy in (-1, 1):
        for j in range(2):
            items.append(nk.bevbox((2.3, 0.17, 0.07), (0, sy * (0.72 + j * 0.19), 0.42), "fo_wood_lt" if j else "fo_wood", 0.012))

    for sx in (-0.85, 0.85):
        for sy in (-1, 1):
            items.append(nk.bar((sx, 0, 0.72), (sx, sy * 0.78, 0.0), 0.05, "fo_wood_dk", 5))

        items.append(nk.bar((sx, -0.85, 0.34), (sx, 0.85, 0.34), 0.04, "fo_wood_dk", 5))

    nk.add(items)

    return finish("picnic", 900)


def table():
    setup(124)
    items = []

    for i in range(3):
        items.append(nk.bevbox((2.16, 0.55, 0.14), (0, -0.58 + i * 0.58, 0.7), "fo_wood_lt" if i % 2 == 0 else "fo_wood", 0.02))

    for sy in (-1, 1):
        items.append(nk.tube("bench", [(-1.0, sy * 0.76, 0.3), (1.0, sy * 0.76, 0.3)], [0.17, 0.17], 6, ["fo_log", "fo_log_lt"], cap_top="fo_log_end", cap_bottom="fo_log_end", squash=(1.0, 0.8)))

    for sx in (-0.8, 0.8):
        for sy in (-0.55, 0.55):
            items.append(nk.bevbox((0.14, 0.14, 0.72), (sx, sy, 0.0), "fo_wood_dk", 0.015))

        items.append(nk.bevbox((0.1, 1.2, 0.1), (sx, 0, 0.32), "fo_wood_dk", 0.012))

        for sy in (-1, 1):
            items.append(nk.bevbox((0.1, 0.1, 0.32), (sx, sy * 0.76, 0.0), "fo_wood_dk", 0.012))

    nk.add(items)

    return finish("table", 900)


def well():
    setup(125)
    items = []
    rnd = random.Random(125)

    for course in range(3):
        n = 10
        r = 0.88 - course * 0.02

        for i in range(n):
            a = 2 * math.pi * (i + course * 0.5) / n
            b = nk.bevbox((0.58, 0.34, 0.32), (0, 0, 0), ("fo_stone", "fo_stone_lt", "fo_stone_dk")[rnd.randrange(3)], 0.04)
            k.rotate(b, math.degrees(a) + 90)
            k.move(b, math.cos(a) * r, math.sin(a) * r, course * 0.3)
            items.append(b)

    items.append(nk.tube("water", [(0, 0, 0.35), (0, 0, 0.4)], [0.62, 0.62], 10, "fo_water", cap_top="fo_water"))

    for sx in (-0.95, 0.95):
        items.append(tk.post(sx, 0.0, 0.5, 2.0, 0.09))

    items.append(nk.bar((-1.05, 0, 1.6), (1.05, 0, 1.6), 0.09, "fo_wood_lt", 6))
    items.append(nk.bar((0.95, 0.12, 1.6), (1.15, 0.12, 1.6), 0.05, "fo_metal", 5))
    items += tk.shingle_roof(2.3, 1.7, 0.75, (0, 0, 2.0), overhang=0.25, rows=4)
    items.append(nk.bar((0, 0, 1.6), (0, 0, 0.85), 0.018, "fo_rope", 4))
    items.append(nk.tube("bucket", [(0, 0, 0.65), (0, 0, 0.85)], [0.11, 0.14], 7, "fo_wood", cap_top=False, cap_bottom="fo_wood_dk"))
    nk.add(items)

    return finish("well", 1500)


def kiosk():
    setup(126)
    items = []

    for sx in (-0.8, 0.8):
        items.append(nk.bevbox((0.14, 0.14, 2.3), (sx, 0, 0), "fo_wood_dk", 0.015))

    items.append(nk.bevbox((1.72, 0.1, 1.15), (0, -0.04, 0.95), "fo_wood", 0.02))
    items.append(nk.bevbox((1.5, 0.04, 0.95), (0, -0.1, 1.05), "fo_cream", 0.01))
    rnd = random.Random(126)

    for i in range(7):
        items.append(nk.plain((rnd.uniform(0.18, 0.5), 0.02, 0.05), (rnd.uniform(-0.55, 0.55), -0.13, 1.2 + rnd.uniform(0, 0.7)), "fo_accent_dk" if i % 3 == 0 else "fo_moss"))

    items.append(nk.plain((0.5, 0.02, 0.4), (-0.4, -0.13, 1.15), "fo_moss_lt"))
    items.append(nk.bevbox((1.7, 0.12, 0.1), (0, -0.04, 0.8), "fo_wood_dk", 0.015))
    items += tk.shingle_roof(1.87, 0.7, 0.36, (0, 0, 2.28), overhang=0.16, rows=3)
    nk.add(items)

    return finish("kiosk", 1100)


def arrow(length, h, thick):
    return [(0.0, 0.0), (length - h * 0.6, 0.0), (length, h / 2), (length - h * 0.6, h), (0.0, h)]


def sign():
    setup(127)
    items = [nk.tube("post", [(0, 0, 0), (0, 0, 1.2), (0, 0, 2.2)], [0.13, 0.11, 0.1], 8, ["fo_wood", "fo_wood_lt", "fo_wood_dk"], cap_top=False, cap_bottom=True)]
    items.append(nk.tube("cap", [(0, 0, 2.2), (0, 0, 2.38), (0, 0, 2.55)], [0.12, 0.07, 0.015], 8, "fo_wood_dk", cap_top=False))
    items.append(nk.hull((0, 0, 0), (0.7, 0.62, 0.22), 9, 3, bevel=0.03, painter=lambda p: "fo_stone_lt" if p.normal.z > 0.5 else "fo_stone", base_cut=0.3))

    for z, yaw, ln, col in [(1.15, 70, 0.95, "fo_wood_lt"), (1.5, -25, 1.2, "fo_wood"), (1.85, 135, 0.8, "fo_wood_lt")]:
        plate = k.sweep("plate", arrow(ln, 0.28, 0.05), 0.05, (0, 0, 0), nk.idx(col), axis="y")
        k.rotate(plate, yaw)
        k.move(plate, 0.0, 0.0, z)
        items.append(plate)

    nk.add(items)

    return finish("sign", 800)


def lantern():
    setup(128)
    items = [nk.tube("post", [(0, 0, 0), (0, 0, 1.5), (0, 0, 3.0)], [0.12, 0.1, 0.08], 8, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk", cap_bottom=True)]
    items.append(nk.hull((0, 0, 0), (0.6, 0.6, 0.25), 9, 4, bevel=0.03, painter=lambda p: "fo_stone_lt" if p.normal.z > 0.5 else "fo_stone", base_cut=0.3))
    items.append(nk.bar((0, 0, 2.95), (0, 0.9, 2.95), 0.05, "fo_wood_dk", 5))
    items.append(nk.bar((0, 0.05, 2.35), (0, 0.8, 2.92), 0.04, "fo_wood_dk", 5))
    items.append(nk.bar((0, 0.9, 2.95), (0, 0.9, 2.78), 0.012, "fo_metal_dk", 4))
    items.append(nk.bevbox((0.26, 0.26, 0.34), (0, 0.9, 2.46), "fo_metal_dk", 0.02))
    items.append(nk.plain((0.2, 0.2, 0.26), (0, 0.9, 2.5), "fo_cream"))
    items.append(nk.bevbox((0.34, 0.34, 0.07), (0, 0.9, 2.8), "fo_metal_dk", 0.015, taper=(0.55, 0.55)))
    nk.add(items)

    return finish("lantern", 700)


def fence():
    setup(129)
    items = []

    for sx in (-1.2, 1.2):
        items.append(nk.bevbox((0.16, 0.2, 1.1), (sx, 0.04, 0), "fo_wood_dk", 0.015))
        items.append(nk.bevbox((0.16, 0.2, 0.12), (sx, 0.04, 1.1), "fo_wood_dk", 0.01, taper=(0.1, 0.1)))

    for z in (0.35, 0.78):
        items.append(nk.bevbox((2.4, 0.08, 0.11), (0, 0.13, z), "fo_wood_dk", 0.01))

    for i in range(9):
        x = -1.04 + i * 0.26
        items.append(nk.bevbox((0.17, 0.05, 0.9), (x, -0.02, 0.05), "fo_wood" if i % 2 else "fo_wood_lt", 0.01))
        items.append(nk.bevbox((0.17, 0.05, 0.2), (x, -0.02, 0.95), "fo_wood" if i % 2 else "fo_wood_lt", 0.0, taper=(0.02, 1.0)))

    nk.add(items)

    return finish("fence", 900)


def gate():
    setup(130)
    items = []

    for sx in (-1.25, 1.25):
        items.append(nk.bevbox((0.2, 0.3, 1.5), (sx, 0.04, 0), "fo_wood_dk", 0.02))
        items.append(nk.bevbox((0.2, 0.3, 0.14), (sx, 0.04, 1.5), "fo_wood_dk", 0.01, taper=(0.1, 0.1)))

    for z in (0.3, 0.9):
        items.append(nk.bevbox((2.3, 0.08, 0.12), (0, 0.13, z), "fo_wood", 0.01))

    items.append(nk.bar((-1.1, 0.14, 0.3), (1.1, 0.14, 0.95), 0.05, "fo_wood_lt", 4))

    for i in range(8):
        x = -0.98 + i * 0.28
        items.append(nk.bevbox((0.18, 0.05, 0.95), (x, -0.02, 0.1), "fo_wood" if i % 2 else "fo_wood_lt", 0.01))
        items.append(nk.bevbox((0.18, 0.05, 0.2), (x, -0.02, 1.05), "fo_wood" if i % 2 else "fo_wood_lt", 0.0, taper=(0.02, 1.0)))

    items.append(nk.bevbox((0.1, 0.1, 0.2), (1.0, -0.08, 0.7), "fo_metal_dk", 0.01))
    nk.add(items)

    return finish("gate", 900)


def cooler():
    setup(131)
    items = [
        nk.bevbox((0.88, 0.52, 0.4), (0, 0, 0.04), "fo_cooler", 0.04),
        nk.bevbox((0.92, 0.56, 0.14), (0, 0, 0.44), "fo_cream", 0.035),
        nk.bevbox((0.2, 0.06, 0.1), (0, -0.28, 0.36), "fo_metal_dk", 0.01),
    ]

    for sx in (-1, 1):
        items.append(nk.bar((sx * 0.44, -0.08, 0.28), (sx * 0.5, -0.08, 0.34), 0.03, "fo_metal_dk", 5))
        items.append(nk.bar((sx * 0.5, -0.08, 0.34), (sx * 0.5, 0.08, 0.34), 0.03, "fo_metal_dk", 5))

    nk.add(items)

    return finish("cooler", 500)


def rack():
    setup(132)
    items = []

    for sy in (-0.85, 0.85):
        for sx in (-2.7, 0.0, 2.7):
            items.append(nk.bevbox((0.2, 0.2, 2.1), (sx, sy, 0), "fo_wood_dk", 0.02))

        for z in (1.0, 1.9):
            items.append(nk.tube("rail", [(-2.9, sy, z), (2.9, sy, z)], [0.1, 0.1], 6, ["fo_log", "fo_log_lt"], cap_top="fo_log_end", cap_bottom="fo_log_end"))

    for sx in (-2.7, 2.7):
        items.append(nk.bar((sx, -0.85, 2.1), (sx, 0.85, 2.1), 0.08, "fo_wood", 5))

    pts, radii = nk.refine([(-2.3, 0, 2.3), (-1.0, 0, 2.2), (1.0, 0, 2.2), (2.3, 0, 2.3)], [0.08, 0.36, 0.36, 0.08], 3)

    for sy, col in ((-0.85, "fo_tent"), (0.85, "fo_canvas")):
        pp = [(p[0], sy, p[2] + 0.02) for p in pts]
        items.append(nk.tube("canoe", pp, radii, 8, [col, col + "_dk" if col + "_dk" in nk.k._INDEX else col], cap_top=col, cap_bottom=col, squash=(1.0, 0.5)))

    nk.add(items)

    return finish("rack", 1800, flat=False)


def lights():
    setup(133)
    items = []

    for sx in (-2.6, 2.6):
        items.append(nk.tube("pole", [(sx, 0, 0), (sx, 0, 1.8), (sx, 0, 3.5)], [0.08, 0.065, 0.05], 6, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk", cap_bottom=True))

    n = 12
    pts = []

    for i in range(n + 1):
        t = i / n
        pts.append((-2.6 + 5.2 * t, 0, 3.5 - 0.55 * math.sin(math.pi * t)))

    items.append(nk.tube("wire", pts, [0.012] * (n + 1), 4, "fo_metal_dk", cap_top=False))

    for i in range(1, n):
        p = pts[i]
        items.append(nk.tube("bulb", [(p[0], 0, p[2] - 0.02), (p[0], 0, p[2] - 0.2)], [0.03, 0.08], 6, "fo_flower", cap_top="fo_cream"))

    nk.add(items)

    return finish("lights", 600, grime=None)


def stone():
    setup(134)
    nk.add(nk.hull((0, 0, 0), (1.7, 1.1, 0.1), 10, 5, bevel=0.025, segments=1, painter=lambda p: "fo_path" if p.normal.z > 0.5 else "fo_stone", base_cut=0.5, irregular=0.12))

    return finish("stone", 200, grime=None)


ALL = {
    "barrel": barrel,
    "bench": bench,
    "picnic": picnic,
    "table": table,
    "well": well,
    "kiosk": kiosk,
    "sign": sign,
    "lantern": lantern,
    "fence": fence,
    "gate": gate,
    "cooler": cooler,
    "rack": rack,
    "lights": lights,
    "stone": stone,
}
