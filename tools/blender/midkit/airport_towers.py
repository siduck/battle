import math

import midkit_core as m
import midkit_structures as st
import midkit_walls as wl


def glazed_face(w, h, at, facing, floors, bays, pier="ap_sand_l", band="ap_sand", frame_depth=0.35, base_h=0.0, band_h=0.55, first_h=None):
    x, y, z = at
    items = []
    fh = (h - base_h) / floors
    items.append(m.flat((w, 0.1, h - base_h), (0, 0.0, base_h), "ap_glass"))

    for f in range(floors):
        z0 = base_h + f * fh
        items.append(m.flat((w - 0.3, 0.04, (fh - band_h) * 0.4), (0, -0.04, z0 + band_h + (fh - band_h) * 0.6), "ap_glass_l"))
        items.append(m.bx((w, frame_depth, band_h), (0, -frame_depth / 2, z0), band, 0.03))

    items.append(m.bx((w, frame_depth, band_h), (0, -frame_depth / 2, h - band_h), band, 0.03))
    pw = w / bays

    for i in range(bays + 1):
        px = -w / 2 + i * pw
        items.append(m.bx((0.5, frame_depth + 0.12, h - base_h), (px, -(frame_depth + 0.12) / 2, base_h), pier, 0.04))

    for it in items:
        m.k.rotate(it, facing)
        m.k.move(it, x, y, z)

    return items


def tower():
    m.setup()
    P = []
    P.append(m.bx((12, 12, 0.2), (0, 0, 0), "ap_sand_d", 0.02))
    base_h = 7.5
    P += wl.plain_wall(11.0, base_h, (0, -5.5, 0.2), "ap_sand_l", plinth=0.8, cap="ap_sand", band=0.45, band_z=base_h - 1.1, band_color="ap_orange")
    P += wl.plain_wall(11.0, base_h, (0, 5.5, 0.2), "ap_sand_l", facing=180, plinth=0.8, cap="ap_sand")
    P += wl.plain_wall(11.0, base_h, (-5.5, 0, 0.2), "ap_sand_l", facing=-90, plinth=0.8, cap="ap_sand")
    P += wl.plain_wall(11.0, base_h, (5.5, 0, 0.2), "ap_sand_l", facing=90, plinth=0.8, cap="ap_sand")
    P.append(m.bx((11.6, 11.6, 0.3), (0, 0, base_h + 0.2), "ap_steel_d", 0.04))

    for i in range(3):
        P += m.window_on(1.6, 1.5, (-3.6 + i * 3.6, -5.5, 4.2), panes=2)
        P += m.window_on(1.6, 1.5, (-3.6 + i * 3.6, 5.5, 4.2), facing=180, panes=2)

    for s in (-1, 1):
        for i in range(3):
            P += m.window_on(1.4, 1.4, (s * 5.5, -3.6 + i * 3.6, 4.2), facing=-90 * s, panes=2)

    P += m.window_on(1.9, 2.3, (-1.5, -5.5, 0.9), panes=2)
    P.append(m.bx((2.4, 1.6, 0.18), (-1.5, -6.2, 3.35), "ap_orange", 0.03))
    P.append(m.bx((2.6, 1.4, 0.2), (-1.5, -6.3, 0.2), "ap_sand", 0.03))
    P += wl.ac_unit((4.0, -3.0, base_h + 0.5), size=(1.4, 1.0, 1.0))
    P += wl.vent_hood((-3.5, 3.0, base_h + 0.5), w=1.1, h=1.0)

    sh = 33.0
    r = 3.05
    P.append(m.cyl(r, sh - base_h - 0.2, (0, 0, base_h + 0.5), "ap_sand_l", 8))
    P.append(m.cyl(r + 0.25, 0.7, (0, 0, base_h + 0.5), "ap_sand_d", 8))
    P += [m.bx((0.9, 0.9, sh - base_h - 0.5), (sx * 2.45, sy * 2.45, base_h + 0.5), "ap_sand", 0.04) for sx in (-1, 1) for sy in (-1, 1)]

    for z in (12.0, 18.0, 24.0, 29.5):
        P.append(m.cyl(r + 0.3, 0.45, (0, 0, z), "ap_orange" if z == 24.0 else "ap_sand_d", 8))

    for i in range(4):
        a = math.radians(45 + i * 90)

        for z in (10.0, 15.0, 21.0, 27.0):
            wx, wy = math.cos(a) * (r * 0.93), math.sin(a) * (r * 0.93)
            slot = m.bx((0.45, 0.2, 1.4), (wx, wy, z), "ap_glass", 0.01)
            m.k.rotate(slot, math.degrees(a) + 90)
            m.k.move(slot, 0, 0, 0)
            P.append(slot)

    P.append(m.cyl(r + 0.15, 0.3, (0, 0, sh), "ap_steel_d", 8))
    cab_r = 5.1
    P.append(m.lathe([(0, sh), (r + 0.1, sh), (cab_r, sh + 1.7), (cab_r, sh + 2.0), (0, sh + 2.0)], (0, 0, 0), "ap_sand_d", 8))
    gz, gh = sh + 2.1, 3.0
    P.append(m.cyl(cab_r - 0.1, gh, (0, 0, gz), "ap_glass", 8))
    P.append(m.cyl(cab_r - 0.04, gh * 0.4, (0, 0, gz + gh * 0.6), "ap_glass_l", 8))

    for i in range(8):
        a = math.radians(22.5 + i * 45)
        px, py = math.cos(a) * (cab_r - 0.05), math.sin(a) * (cab_r - 0.05)
        post = m.bx((0.28, 0.28, gh + 0.1), (px, py, gz), "ap_steel_d", 0.02)
        P.append(post)

    P.append(m.cyl(cab_r + 0.1, 0.35, (0, 0, gz + gh), "ap_steel_d", 8))
    P.append(m.lathe([(0, gz + gh + 0.35), (cab_r + 0.45, gz + gh + 0.35), (cab_r + 0.45, gz + gh + 0.6), (cab_r - 0.2, gz + gh + 1.0), (1.2, gz + gh + 1.5), (0, gz + gh + 1.5)], (0, 0, 0), "ap_sand_l", 8))
    P.append(m.cyl(cab_r + 0.55, 0.12, (0, 0, gz - 0.1), "ap_steel", 8))

    for i in range(8):
        a = math.radians(i * 45)
        P.append(m.bar((math.cos(a) * (cab_r + 0.5), math.sin(a) * (cab_r + 0.5), gz), (math.cos(a) * (cab_r + 0.5), math.sin(a) * (cab_r + 0.5), gz + 1.0), 0.04, "ap_steel_d", 4))

    P.append(m.bar((0, 0, gz + gh + 1.5), (0, 0, 45.5), 0.1, "ap_steel_d", 6))
    P.append(m.bar((0.8, 0.5, gz + gh + 1.0), (0.8, 0.5, 43.0), 0.04, "ap_steel_d", 4))
    P.append(m.cyl(0.25, 0.4, (0, 0, 45.1), "ap_orange", 8))
    P.append(m.bx((1.2, 0.9, 0.9), (-2.0, 1.0, gz + gh + 1.2), "ap_steel_l", 0.03))
    ob = m.finish("tower", P, budget=12000)

    return ob


def hotel():
    m.setup()
    W, D, floors = 23.6, 15.6, 12
    P = []
    P.append(m.bx((W + 0.2, D + 0.2, 0.25), (0, 0, 0), "ap_sand_d", 0.02))
    pod = 4.8
    P += glazed_face(W, 39.4, (0, -D / 2, 0.25), 0, floors, 8, base_h=pod)
    P += glazed_face(W, 39.4, (0, D / 2, 0.25), 180, floors, 8, base_h=pod)
    P += glazed_face(D, 39.4, (-W / 2, 0, 0.25), -90, floors, 6, base_h=pod)
    P += glazed_face(D, 39.4, (W / 2, 0, 0.25), 90, floors, 6, base_h=pod)
    P += wl.plain_wall(W, pod, (0, -D / 2, 0.25), "ap_sand", plinth=0.5, plinth_color="ap_sand_d")
    P += wl.plain_wall(W, pod, (0, D / 2, 0.25), "ap_sand", facing=180, plinth=0.5)
    P += wl.plain_wall(D, pod, (-W / 2, 0, 0.25), "ap_sand", facing=-90, plinth=0.5)
    P += wl.plain_wall(D, pod, (W / 2, 0, 0.25), "ap_sand", facing=90, plinth=0.5)

    for i in range(5):
        P += m.window_on(2.2, 2.6, (-8.8 + i * 4.4, -D / 2, 1.0), panes=2) if i != 2 else []

    P.append(m.bx((5.2, 2.6, 0.3), (0, -D / 2 - 1.3, 3.7), "ap_orange", 0.04))
    P += [m.bx((0.3, 0.3, 3.7), (sx * 2.4, -D / 2 - 2.3, 0.25), "ap_steel_d", 0.02) for sx in (-1, 1)]
    P += m.window_on(3.4, 2.7, (0, -D / 2, 0.9), panes=2)
    P.append(m.bx((W + 0.6, D + 0.6, 0.6), (0, 0, 39.65 + 0.25), "ap_sand", 0.06))
    P.append(m.bx((W - 0.2, D - 0.2, 0.2), (0, 0, 40.5), "ap_steel_d", 0.02))
    P.append(m.bx((W + 0.2, 0.3, 0.9), (0, -D / 2 - 0.1, 40.2), "ap_sand_l", 0.04))
    P.append(m.bx((W + 0.2, 0.3, 0.9), (0, D / 2 + 0.1, 40.2), "ap_sand_l", 0.04))
    P.append(m.bx((0.3, D, 0.9), (-W / 2 - 0.1, 0, 40.2), "ap_sand_l", 0.04))
    P.append(m.bx((0.3, D, 0.9), (W / 2 + 0.1, 0, 40.2), "ap_sand_l", 0.04))
    P.append(m.bx((W - 6, 0.2, 0.4), (0, -D / 2 - 0.35, 36.4), "ap_orange", 0.03))
    P.append(m.bx((9.0, 6.0, 2.6), (-4.0, 1.0, 40.5), "ap_sand_l", 0.05))
    P.append(m.bx((9.4, 6.4, 0.25), (-4.0, 1.0, 43.1), "ap_steel_d", 0.03))
    P += m.window_on(2.0, 1.1, (-4.0, -2.0, 41.2), panes=2)
    P += wl.vent_hood((5.0, -2.0, 40.5), w=1.2, h=1.4)
    P += wl.vent_hood((8.0, 3.0, 40.5), w=1.2, h=1.4)
    P += wl.ac_unit((6.0, 4.5, 40.5), size=(1.6, 1.0, 1.1))
    P.append(m.cyl(0.07, 2.2, (4.0, -4.0, 40.5), "ap_steel_d", 6))
    P.append(m.bx((0.25, 0.25, 0.25), (4.0, -4.0, 42.7), "ap_orange", 0.02))
    ob = m.finish("hotel", P, budget=12000)

    return ob


def carpark():
    m.setup()
    W, D, levels, lh = 47.6, 31.6, 6, 3.4
    P = []
    P.append(m.bx((W + 0.2, D + 0.2, 0.2), (0, 0, 0), "ap_sand_d", 0.02))
    cols_x = [-W / 2 + 0.6 + i * (W - 1.2) / 8 for i in range(9)]
    cols_y = [-D / 2 + 0.6 + i * (D - 1.2) / 4 for i in range(5)]

    for cx in cols_x:
        for cy in cols_y:
            P.append(m.bx((0.6, 0.6, levels * lh), (cx, cy, 0.2), "ap_sand_l", 0.04))

    for L in range(1, levels + 1):
        z = L * lh
        P.append(m.bx((W, D, 0.45), (0, 0, z - 0.45), "ap_sand", 0.04, seg=1))

        if L < levels + 1:
            for ci in range(0, 9, 2):
                P.append(m.bx((0.8, D - 1.0, 0.35), (cols_x[ci], 0, z - 0.8), "ap_sand_d", 0.03, seg=1))

        zb = z - 0.0
        P.append(m.bx((W, 0.35, 1.0), (0, -D / 2 + 0.17, zb), "ap_sand_l", 0.04))
        P.append(m.bx((W, 0.35, 1.0), (0, D / 2 - 0.17, zb), "ap_sand_l", 0.04))
        P.append(m.bx((0.35, D - 0.7, 1.0), (-W / 2 + 0.17, 0, zb), "ap_sand_l", 0.04))
        P.append(m.bx((0.35, D - 0.7, 1.0), (W / 2 - 0.17, 0, zb), "ap_sand_l", 0.04))
        P.append(m.bx((W + 0.1, 0.4, 0.25), (0, -D / 2 + 0.17, zb + 0.5), "ap_orange" if L == levels else "ap_sand_d", 0.02))

    top = levels * lh
    P.append(m.bx((4.2, 5.2, top + 1.2), (W / 2 - 2.5, D / 2 - 3.0, 0.2), "ap_sand_l", 0.05))
    P.append(m.bx((4.6, 5.6, 0.3), (W / 2 - 2.5, D / 2 - 3.0, top + 1.4), "ap_steel_d", 0.03))

    for L in range(levels):
        P += m.window_on(1.2, 1.3, (W / 2 - 2.5, D / 2 - 5.6, L * lh + 1.6), panes=1)

    P.append(m.bx((1.4, 1.2, 0.18), (W / 2 - 2.5, D / 2 - 5.9, 0.2 + 2.3), "ap_orange", 0.03))


    for i in range(6):
        P.append(m.bx((1.2, 0.5, 0.18), (-W / 2 + 4 + i * 7, -D / 2 + 0.2, top + 0.2), "ap_white", 0.02))

    for L in range(levels):
        for i in range(3):
            P.append(m.bx((1.6, 0.25, 0.12), (-14 + i * 14, 0.0, (L + 1) * lh - 0.9), "ap_white", 0.02))

    ob = m.finish("carpark", P, budget=14000)

    return ob


ALL = {"tower": tower, "hotel": hotel, "carpark": carpark}
