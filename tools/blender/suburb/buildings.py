import math

import jp
from jp import add, bx, flat, place, shift

D = 3.4
FY = -D / 2


def opening(kind, w, h, color, **o):
    if kind == "win":
        return jp.window(w, h, color, rail=o.get("rail", False), screen=o.get("screen", False), panes=o.get("panes", 2))

    if kind == "door":
        return jp.door(w, h, o.get("leaf", "jp_wood"), glass=o.get("glass", False))

    if kind == "glass":
        return jp.glassfront(w, h, bays=o.get("bays", 3))

    if kind == "shutter":
        return jp.shutter(w, h, o.get("open", 0.35))

    return []


def facade(width, height, color, spec=(), extra=()):
    holes = []
    items = []

    for kind, x, z, w, h, o in spec:
        holes.append((x, z, w, h))
        items += shift(opening(kind, w, h, color, **o), x, 0, z)

    return jp.wall(width, height, holes, color) + items + list(extra)


def storey(w, z, h, color, front=(), back=(), left=(), right=(), fx=(), bxx=(), lx=(), rx=(), depth=D):
    fy = -depth / 2
    place(facade(w, h, color, front, fx), 0, fy, z, 0)
    place(facade(w, h, color, back, bxx), 0, -fy, z, 180)
    side = depth - 2 * jp.T
    place(facade(side, h, color, left, lx), -w / 2, 0, z, -90)
    place(facade(side, h, color, right, rx), w / 2, 0, z, 90)


def band(w, z, color="jp_cream_dark", h=0.2, out=0.08, depth=D):
    b = bx((w + out * 2, depth + out * 2, h), (0, 0, z), color, 0.02)
    jp.soft.append(b)
    add(b)


def plinth(w, depth=D, color="jp_concrete"):
    add(bx((w + 0.1, depth + 0.1, 0.18), (0, 0, -0.02), color, 0.02))


def win(x, z, w, h, **o):
    return ("win", x, z, w, h, o)


def door(x, w=0.9, h=2.05, **o):
    return ("door", x, 0, w, h, o)


def shop2():
    jp.setup(21)
    w = 4.0
    plinth(w)
    storey(w, 0, 3.0, "jp_wood",
           front=[("shutter", 0, 0, 3.0, 2.45, {"open": 0.45})],
           back=[door(-0.9), win(0.9, 1.1, 0.8, 0.8)],
           left=[win(0.4, 1.2, 0.7, 0.7)],
           rx=jp.meter((-0.6, 0, 1.3)))
    add(shift(jp.sign(3.2, 0.42, "jp_sign", "jp_indigo"), 0, FY, 2.52))
    add(shift(jp.hisashi(w, 0.55), 0, FY, 3.05))
    band(w, 3.0, "jp_wood_dark", 0.2)
    storey(w, 3.2, 2.6, "jp_cream",
           front=[win(0, 0.8, 1.7, 1.15, rail=True)],
           back=[win(0.6, 0.9, 1.2, 1.0, screen=True)],
           right=[win(-0.3, 1.0, 0.6, 0.7)])
    add(jp.ac_unit((1.4, FY - 0.15, 3.35)))
    add(jp.pipe(w / 2 - 0.15, FY - 0.05, 0.05, 5.8))
    add(jp.gable_roof(w, D, 1.4, 5.8, overhang=0.3, wall_color="jp_cream"))

    return jp.finish("shop2", 14000)


def shop3():
    jp.setup(22)
    w = 4.0
    plinth(w)
    storey(w, 0, 3.1, "jp_grey",
           front=[("glass", -0.25, 0, 3.0, 2.5, {"bays": 3})],
           back=[door(0.8)],
           left=[win(0.2, 1.3, 0.6, 0.7)])
    add(shift(jp.awning(3.4, 0.9, "jp_indigo", "jp_sign"), -0.2, FY, 2.75))
    add(shift(jp.sign(3.6, 0.42, "jp_indigo", "jp_sign"), 0, FY, 2.62))

    far = jp.FAR

    for i, z in enumerate((3.1, 5.9)):
        jp.FAR = far or i == 1
        band(w, z, "jp_mint_dark", 0.18, 0.05)
        storey(w, z + 0.18, 2.62, "jp_mint",
               front=[win(-0.3, 0.85, 2.4, 1.3, screen=True, panes=3)],
               back=[win(0.5, 1.0, 1.0, 0.9)],
               left=[win(0.1, 1.0, 0.6, 0.8)])
        add(jp.ac_unit((1.35, FY - 0.15, z + 0.35)))

    jp.FAR = far
    add(shift(jp.vsign(3.6, 0.55, "jp_yellow", "jp_red_dark"), w / 2 - 0.2, FY - 0.35, 3.5))
    add(jp.flat_roof(w, D, 8.7, 0.55, "jp_mint"))
    add(jp.ac_unit((-0.8, 0.6, 8.7)))
    add(jp.pipe(-w / 2 + 0.15, FY - 0.05, 0.05, 8.7))

    return jp.finish("shop3", 16000)


def corner():
    jp.setup(23)
    w = 4.0
    plinth(w)
    storey(w, 0, 3.1, "jp_pink",
           front=[("glass", 0, 0, 3.2, 2.5, {"bays": 3})],
           right=[("glass", -0.1, 0, 2.4, 2.5, {"bays": 2})],
           back=[door(-0.8)],
           left=[win(0.3, 1.3, 0.6, 0.7)])
    add(shift(jp.sign(3.8, 0.45, "jp_green", "jp_sign"), 0, FY, 2.65))
    right_sign = jp.sign(3.0, 0.45, "jp_green", "jp_sign")
    place(right_sign, w / 2, 0, 2.65, 90)

    far = jp.FAR

    for i, z in enumerate((3.1, 5.9)):
        jp.FAR = far or i == 1
        band(w, z, "jp_pink_dark", 0.18, 0.06)
        storey(w, z + 0.18, 2.62, "jp_pink",
               front=[win(-0.6, 0.9, 1.6, 1.2, rail=True), win(1.2, 1.1, 0.7, 0.9)],
               right=[win(0.2, 0.9, 1.4, 1.2, screen=True)],
               back=[win(0.4, 1.0, 0.9, 0.9)],
               left=[win(-0.2, 1.0, 0.6, 0.8)])

    jp.FAR = far
    add(jp.ac_unit((-1.4, FY - 0.15, 3.45)))
    add(jp.flat_roof(w, D, 8.7, 0.7, "jp_pink"))
    add(jp.tank((0.8, 0.4, 8.7)))
    add(jp.pipe(-w / 2 + 0.15, -FY + 0.05, 0.05, 8.7))

    return jp.finish("corner", 16000)


def wide():
    jp.setup(24)
    w = 8.0
    plinth(w)
    storey(w, 0, 3.0, "jp_ochre",
           front=[("shutter", -1.9, 0, 3.2, 2.45, {"open": 0.6}), ("glass", 2.0, 0, 3.0, 2.45, {"bays": 2})],
           back=[door(-2.5), win(1.5, 1.1, 1.2, 0.9), win(-0.6, 1.2, 0.7, 0.7)],
           left=[win(0, 1.2, 0.8, 0.8)],
           right=[win(0.4, 1.2, 0.7, 0.7)])
    add(shift(jp.sign(3.4, 0.45, "jp_sign", "jp_red_dark"), -1.9, FY, 2.5))
    add(shift(jp.sign(3.2, 0.45, "jp_indigo", "jp_sign"), 2.0, FY, 2.5))
    add(shift(jp.awning(3.2, 0.85, "jp_green", "jp_sign"), 2.0, FY, 2.45))
    add(shift(jp.hisashi(w, 0.5), 0, FY, 3.05))
    band(w, 3.0, "jp_ochre_dark", 0.2)
    storey(w, 3.2, 2.6, "jp_ochre",
           front=[win(-2.6, 0.8, 1.5, 1.15, rail=True), win(0, 0.8, 1.5, 1.15, rail=True), win(2.6, 0.8, 1.5, 1.15, rail=True)],
           back=[win(-2.0, 0.9, 1.2, 1.0), win(2.0, 0.9, 1.2, 1.0, screen=True)],
           left=[win(0.3, 1.0, 0.6, 0.7)],
           right=[win(-0.3, 1.0, 0.6, 0.7)])
    add(jp.ac_unit((-1.3, FY - 0.15, 3.3)))
    add(jp.ac_unit((1.3, -FY + 0.15, 3.3), 180))
    add(jp.pipe(w / 2 - 0.15, FY - 0.05, 0.05, 5.8))
    add(jp.gable_roof(w, D, 1.6, 5.8, overhang=0.3, wall_color="jp_ochre"))

    return jp.finish("wide", 24000)


def konbini():
    jp.setup(25)
    w = 8.0
    plinth(w)
    storey(w, 0, 2.75, "jp_cream_light",
           front=[("glass", -1.0, 0, 5.4, 2.45, {"bays": 4}), ("glass", 2.85, 0, 1.6, 2.45, {"bays": 1})],
           back=[door(2.6, glass=False), win(-1.5, 1.4, 1.0, 0.6)],
           left=[win(0, 1.4, 1.2, 0.6)],
           right=[])

    for i, (col, h) in enumerate((("jp_green", 0.22), ("jp_sign", 0.12), ("jp_indigo", 0.22))):
        z = 2.75 + sum(hh for _, hh in (("jp_green", 0.22), ("jp_sign", 0.12), ("jp_indigo", 0.22))[:i])
        b = bx((w + 0.16, D + 0.16, h), (0, 0, z), col, 0.015)
        add(b)

    add(flat((w, D, 0.08), (0, 0, 3.31), "jp_concrete"))
    add(shift(jp.sign(1.6, 0.5, "jp_sign", "jp_green", letters=3), -2.6, FY - 0.09, 2.73))
    add(jp.ac_unit((-2.0, 0.5, 3.39), 180))
    add(jp.ac_unit((-0.9, 0.5, 3.39), 180))
    add(jp.meter((w / 2 + 0.07, 0.8, 1.2)))

    return jp.finish("konbini", 14000)


def parlour():
    jp.setup(26)
    w = 8.0
    plinth(w)
    storey(w, 0, 3.2, "jp_slate",
           front=[("glass", 0, 0, 5.0, 2.6, {"bays": 4})],
           back=[door(-2.5), door(2.5)],
           left=[win(0, 1.3, 0.8, 0.8)],
           right=[win(0, 1.3, 0.8, 0.8)])
    storey(w, 3.2, 5.6, "jp_slate",
           back=[win(-2.0, 1.2, 1.0, 1.0), win(2.0, 1.2, 1.0, 1.0), win(-2.0, 4.0, 1.0, 1.0), win(2.0, 4.0, 1.0, 1.0)],
           left=[win(0, 2.5, 0.8, 0.8)],
           right=[win(0, 2.5, 0.8, 0.8)])
    add(bx((w - 0.4, 0.2, 4.6), (0, FY - 0.1, 3.7), "jp_indigo", 0.03))
    tiles = ("jp_yellow", "jp_red", "jp_sign", "jp_cherry", "jp_green", "jp_yellow", "jp_sign")
    strokes = (((0, 0.3, 0.7, 0.14), (0, 0, 0.14, 0.75)), ((0, 0.25, 0.65, 0.13), (-0.18, 0, 0.13, 0.6), (0.18, 0, 0.13, 0.6)), ((0, 0.32, 0.7, 0.12), (0, 0.05, 0.7, 0.12), (0, -0.22, 0.7, 0.12)), ((0, 0.3, 0.62, 0.12), (0, -0.2, 0.62, 0.12), (-0.25, 0.05, 0.12, 0.62), (0.25, 0.05, 0.12, 0.62)), ((-0.22, 0.05, 0.12, 0.7), (0.0, -0.25, 0.55, 0.12)))

    for row, n in enumerate((4, 3)):
        lw = 1.35
        total = n * lw + (n - 1) * 0.2

        for i in range(n):
            col = tiles[(row * 4 + i) % len(tiles)]
            x = -total / 2 + lw / 2 + i * (lw + 0.2)
            z = 6.75 - row * 1.65
            add(bx((lw, 0.12, 1.35), (x, FY - 0.24, z), col, 0.03))
            ink = "jp_indigo" if col in ("jp_yellow", "jp_sign", "jp_cherry") else "jp_sign"

            for sx, sz, sw, sh in strokes[(row * 3 + i) % len(strokes)]:
                add(flat((sw * lw * 0.7, 0.03, sh * 1.1), (x + sx * lw * 0.6, FY - 0.31, z + 0.675 + sz * 1.0 - sh * 0.55), ink))

    for i in range(9):
        add(flat((0.16, 0.05, 0.16), (-3.4 + i * 0.85, FY - 0.23, 8.1), "jp_sign"))
        add(flat((0.16, 0.05, 0.16), (-3.4 + i * 0.85, FY - 0.23, 3.85), "jp_sign"))

    add(shift(jp.awning(5.4, 0.8, "jp_red", "jp_sign"), 0, FY, 2.95))
    add(jp.flat_roof(w, D, 8.8, 0.5, "jp_slate"))
    add(jp.ac_unit((-2.2, 0.5, 8.8), 180))
    add(jp.ac_unit((2.2, 0.5, 8.8), 180))

    return jp.finish("parlour", 24000)


def apartment(floors=3, name="apartment"):
    jp.setup(27 + floors)
    wall = "jp_blue" if floors > 3 else "jp_sand"
    w = 12.0
    fh = 2.8
    body_front = -0.7
    body_back = 1.2
    depth = body_back - body_front
    cy = (body_front + body_back) / 2
    plinth(w, 4.0)
    units = (-4.5, -1.5, 1.5, 4.5)

    far = jp.FAR

    for f in range(floors):
        jp.FAR = far or f >= 2
        z = f * fh
        front = []

        for ux in units:
            front.append(("door", ux - 0.55, 0, 0.85, 2.0, {"leaf": "jp_slate"}))
            front.append(("win", ux + 0.6, 1.1, 0.8, 0.8, {}))

        back = [("win", ux, 0.15, 1.8, 2.0, {"panes": 2}) for ux in units]
        place(facade(w, fh, wall, front), 0, body_front, z, 0)
        place(facade(w, fh, wall, back), 0, body_back, z, 180)
        side = depth - 2 * jp.T
        place(facade(side, fh, wall, [("win", 0, 1.0, 0.6, 0.8, {})] if f else []), -w / 2, cy, z, -90)
        place(facade(side, fh, wall), w / 2, cy, z, 90)

        if f > 0:
            slab = bx((w, 1.0, 0.16), (0, -1.2, z - 0.16), "jp_concrete", 0.02)
            add(slab)
            add(flat((w, 0.08, 0.55), (0, -1.66, z), "jp_slate"))
            add(jp.railing(w, 0.45, (0, -1.66, z + 0.55), bars=False))

            for ux in units:
                add(flat((0.04, 1.0, 0.04), (ux, -1.2, z + 2.6), "jp_alu_dark"))

        balc = []
        for ux in units:
            balc += shift(jp.balcony(2.6, 0.75, 0, 0, ac=(f + int(ux)) % 2 == 0, laundry=(f + int(ux)) % 3 == 0, solid=True), ux, 0, 0)

        place(balc, 0, body_back, z + 0.02 if f else 0.18, 180)
        add(bx((w + 0.08, depth + 0.08, 0.12), (0, cy, z + fh - 0.12), wall + "_dark", 0.015))

    jp.FAR = far

    for f in range(1, floors):
        z0 = (f - 1) * fh
        steps = 14
        run = 3.6
        x0 = -w / 2 + 0.2 if f % 2 else w / 2 - 0.2 - run
        direction = 1

        if jp.FAR:
            ramp = jp.flat((run, 0.9, 0.06), (x0 + run / 2, -1.2, z0), "jp_alu_dark")
            jp.k.rotate(ramp, 37.9 if f % 2 else -37.9, "Y", (x0 if f % 2 else x0 + run, -1.2, z0))
            add(ramp)
            continue

        for i in range(steps):
            sx = x0 + (i + 0.5) * run / steps if f % 2 else x0 + run - (i + 0.5) * run / steps
            add(bx((run / steps + 0.02, 0.9, 0.06), (sx, -1.2, z0 + (i + 1) * fh / steps - 0.06), "jp_alu_dark", 0.005))

        for sgn in (0, 1):
            xa = x0 if f % 2 else x0 + run
            xb = x0 + run if f % 2 else x0
            add(jp.bar((xa, -1.68, z0 + 1.0 if sgn else z0 + 0.1), (xb, -1.68, z0 + fh + (1.0 if sgn else 0.1)), 0.02, "jp_alu_dark", 4))

    add(shift(jp.flat_roof(w, depth, floors * fh, 0.5, wall), 0, cy, 0))
    add(jp.flat((w, 1.0, 0.14), (0, -1.2, floors * fh - 0.14), "jp_concrete"))
    add(jp.flat((w, 0.08, 0.5), (0, -1.66, floors * fh), "jp_slate"))
    add(jp.tank((-4.0, cy, floors * fh)))
    add(jp.ac_unit((3.5, cy, floors * fh), 180))

    return jp.finish(name, 40000 if floors <= 3 else 80000, fuse_soft=floors <= 3)


def tower():
    return apartment(6, "tower")


def barhut():
    jp.setup(29)
    w = 4.0
    d = 3.0
    plinth(w, d, "jp_concrete")
    lattice = []

    for i in range(7):
        lattice.append(flat((0.04, 0.04, 2.0), (-1.2 + i * 0.4, 0.06, 0), "jp_wood_dark"))

    for z in (0.5, 1.0, 1.5):
        lattice.append(flat((2.4, 0.04, 0.04), (0, 0.06, z), "jp_wood_dark"))

    front = [("glass", -0.0, 0, 2.4, 2.0, {"bays": 2})]
    place(facade(w, 2.35, "jp_wood", front, lattice), 0, -d / 2, 0, 0)
    place(facade(w, 2.35, "jp_wood", [win(0.8, 1.1, 0.8, 0.6)]), 0, d / 2, 0, 180)
    place(facade(d - 2 * jp.T, 2.35, "jp_wood", [win(0, 1.2, 0.7, 0.6)]), -w / 2, 0, 0, -90)
    place(facade(d - 2 * jp.T, 2.35, "jp_wood"), w / 2, 0, 0, 90)

    for i in range(5):
        add(flat((0.4, 0.02, 0.75), (-0.88 + i * 0.44, -d / 2 - 0.06, 1.25), "jp_indigo"))

    add(flat((2.3, 0.05, 0.06), (0, -d / 2 - 0.06, 2.0), "jp_wood_dark"))
    add(jp.lantern((1.55, -d / 2 - 0.3, 1.2)))
    add(jp.gable_roof(w, d, 0.95, 2.35, overhang=0.45, wall_color="jp_wood", color="jp_tile"))

    return jp.finish("barhut", 9000)


def roof():
    jp.setup(30)
    add(jp.gable_roof(4.0, D, 1.6, 0.4, overhang=0.3, wall_color="jp_cream"))
    add(flat((4.0, D, 0.4), (0, 0, 0), "jp_cream"))

    return jp.finish("roof", 5000, fuse_soft=False)


ALL = {
    "parlour": parlour,
    "apartment": apartment,
    "tower": tower,
    "barhut": barhut,
    "konbini": konbini,
    "corner": corner,
    "shop3": shop3,
    "shop2": shop2,
    "wide": wide,
    "roof": roof,
}
