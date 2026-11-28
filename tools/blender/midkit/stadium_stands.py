import math

import arena_parts as A
from arena_parts import F, B, R, cyl, flat, rod, tilted, done, k


def seats():
    A.setup(101)
    W, D, H, ROWS = 1.5, 10.5, 6.3, 13
    tops = A.terrace_body(W, D, H, ROWS)

    for i, (ya, yb, zt) in enumerate(tops):
        A.seat_row(W, ya, zt, 3, "st_blue", "st_red", (1,) if i % 4 == 2 else ())

    flat((W, 0.5, 0.35), (0, D / 2 - 0.25, 5.7), "st_conc_d")

    return done("seats", 3000)


def terrace():
    A.setup(102)
    W, D, H, ROWS = 1.5, 9.0, 7.2, 15
    tops = A.terrace_body(W, D, H, ROWS, body="st_conc", lip="st_conc_l")

    for i, (ya, yb, zt) in enumerate(tops):
        flat((W, 0.1, 0.03), (0, yb - 0.3, zt), "st_conc_dd") if i % 2 == 0 else None

        if i % 3 == 1:
            for x in (-W / 2 + 0.08, W / 2 - 0.08):
                R((x, yb - 0.25, zt), (x, yb - 0.25, zt + 0.9), 0.03, "st_steel_d", 4)

            R((-W / 2, yb - 0.25, zt + 0.9), (W / 2, yb - 0.25, zt + 0.9), 0.035, "st_red", 6)
            R((-W / 2, yb - 0.25, zt + 0.5), (W / 2, yb - 0.25, zt + 0.5), 0.025, "st_steel_d", 4)

    flat((W, 0.5, 0.3), (0, D / 2 - 0.25, H - 0.6), "st_conc_d")

    return done("terrace", 3000)


def roof():
    A.setup(103)
    W = 1.5
    y0, y1 = -6.0, 6.0
    zf, zb = 8.7, 10.45
    ang = math.degrees(math.atan2(zb - zf, y1 - y0))
    L = math.hypot(y1 - y0, zb - zf)
    mid = ((y0 + y1) / 2, (zf + zb) / 2)

    A.profile_yz([(y0, zf - 0.18), (y1, zb - 0.18), (y1, zb), (y0, zf)], W, "st_roof")
    tilted((W - 0.04, L - 0.2, 0.02), (0, mid[0], mid[1] - 0.2), ang, "st_conc_dd")

    for x in (-0.5, 0, 0.5):
        tilted((0.06, L - 0.1, 0.07), (x, mid[0], mid[1] + 0.035), ang, "st_roof_light")

    B((W, 0.16, 0.7), (0, y0 + 0.08, zf - 0.55), "st_blue_d", 0.02)
    flat((W, 0.04, 0.12), (0, y0 - 0.0, zf - 0.38), "st_white")
    B((W, 0.5, 0.25), (0, y1 - 0.25, zb - 0.38), "st_roof_dark", 0.02)

    A.truss_yz((y0 + 0.25, zf - 0.2), (y1 - 0.45, zb - 0.2), 1.1, 0.0, 6)
    R((0, y1 - 0.45, zb - 1.3), (0, y1 - 0.45, 0.2), 0.04, "st_steel_d", 4)

    B((0.34, 0.46, zb - 1.5), (0, y1 - 0.45, 0.0), "st_blue_d", 0.02)
    flat((0.7, 0.7, 0.08), (0, y1 - 0.45, 0.0), "st_conc_d")

    for sx in (-1, 1):
        for sy in (-1, 1):
            flat((0.07, 0.07, 0.06), (sx * 0.27, y1 - 0.45 + sy * 0.27, 0.08), "st_steel")

    R((0, y1 - 0.45, 4.8), (0, y0 + 4.4, zf - 1.35), 0.05, "st_steel_d", 4)

    for x in (-0.45, 0.45):
        B((0.22, 0.3, 0.12), (x, y0 + 1.2, zf - 0.78), "st_steel_d", 0.01)
        flat((0.16, 0.2, 0.03), (x, y0 + 1.2, zf - 0.8), "st_white")

    return done("roof", 3000)


def gable():
    A.setup(104)
    L, T = 10.6, 1.63
    B((L, T, 0.5), (0, 0, 0), "st_conc_d", 0.02)

    holes = [(-3.2, 2.2, 1.0, 3.6), (-1.1, 2.2, 1.0, 3.6), (1.1, 2.2, 1.0, 3.6), (3.2, 2.2, 1.0, 3.6)]
    A.punched_wall(L - 1.6, 6.9, 0.7, holes, "st_conc", at=(0, 0, 0.5))

    for ox, oz, ow, oh in holes:
        for s in (-1, 1):
            B((ow + 0.3, 0.1, 0.12), (ox, s * 0.37, oz - 0.12), "st_conc_l", 0.01)
            B((ow + 0.3, 0.1, 0.12), (ox, s * 0.37, oz + oh), "st_conc_l", 0.01)

            for sx in (-1, 1):
                B((0.12, 0.1, oh + 0.24), (ox + sx * (ow / 2 + 0.09), s * 0.37, oz - 0.12), "st_conc_l", 0.01)

        A.louvre_slots(ox - ow / 2 + 0.05, ox + ow / 2 - 0.05, oz + 0.1, oz + oh - 0.1, 0.12, 9)

    A.profile_xz([(-L / 2 + 0.8, 0.0), (L / 2 - 0.8, 0.0), (L / 2 - 0.8, 1.4), (0, 2.45), (-L / 2 + 0.8, 1.4)], 0.7, "st_conc")
    k.move(A.jp.parts[-1], 0, 0, 7.4)

    for sx in (-1, 1):
        ang = math.degrees(math.atan2(2.45 - 1.4, L / 2 - 0.8))
        seg = math.hypot(L / 2 - 0.8, 1.05)
        s = flat((seg + 0.1, 0.95, 0.22), (0, 0, -0.11), "st_conc_l")
        k.rotate(s, sx * ang, "Y")
        k.move(s, sx * (L / 4 - 0.4), 0, 7.4 + 1.4 + 0.52 + 0.12)

        B((0.95, T, 7.9), (sx * (L / 2 - 0.5), 0, 0.5), "st_conc_l", 0.02)
        B((1.1, T + 0.1, 0.22), (sx * (L / 2 - 0.5), 0, 8.4), "st_conc_d", 0.01)

    for s in (-1, 1):
        flat((L - 1.6, 0.05, 0.45), (0, s * 0.37, 5.6), "st_red")
        A.vent_grille(0.9, 0.5, (-1.2, s * 0.36, 8.45)) if s < 0 else A.vent_grille(0.9, 0.5, (-1.2, s * 0.36, 8.45))
        A.vent_grille(0.9, 0.5, (1.2, s * 0.36, 8.45))
        d = A.disc(0.7, 0.05, (0, s * 0.37, 8.4), "st_blue_d", 14)
        A.disc(0.5, 0.06, (0, s * 0.39, 8.4), "st_white", 14)

    return done("gable", 3000)


def flood():
    A.setup(105)
    flat((1.5, 1.5, 0.12), (0, 0, 0), "st_conc_d")
    A.cyl(0.62, 0.35, (0, 0, 0.12), "st_steel_d", 12)

    for a in range(8):
        x = 0.62 * math.cos(math.radians(a * 45 + 22.5))
        y = 0.62 * math.sin(math.radians(a * 45 + 22.5))
        B((0.1, 0.1, 0.1), (x * 1.15, y * 1.15, 0.12), "st_steel", 0.01)

    A.cyl(0.46, 8.0, (0, 0, 0.45), "st_steel", 12, top=0.4)
    A.cyl(0.4, 8.0, (0, 0, 8.4), "st_conc", 12, top=0.34)
    A.cyl(0.34, 7.4, (0, 0, 16.3), "st_steel", 12, top=0.27)

    for z in (8.35, 16.25):
        A.cyl(0.46, 0.2, (0, 0, z), "st_steel_d", 12)

    for z in range(1, 23):
        flat((0.34, 0.06, 0.04), (0, -0.46, 0.6 + z * 0.95), "st_steel_d")

    for s in (-1, 1):
        R((s * 0.17, -0.44, 0.5), (s * 0.17, -0.44, 23.4), 0.022, "st_steel_d", 4)

    A.cyl(1.55, 0.16, (0, 0, 22.4), "st_conc_d", 12)
    A.cyl(1.5, 0.05, (0, 0, 22.56), "st_steel", 12)

    for a in range(12):
        t = math.radians(a * 30)
        R((1.5 * math.cos(t), 1.5 * math.sin(t), 22.6), (1.5 * math.cos(t), 1.5 * math.sin(t), 23.6), 0.025, "st_steel_d", 4)

    A.cyl(1.5, 0.05, (0, 0, 23.55), "st_steel_d", 12)

    A.lamp_bank(6.4, 3.2, (0, -0.55, 22.4), 6, 4, 0.34)
    B((6.6, 0.5, 0.18), (0, -0.7, 25.55), "st_steel_d", 0.01)

    for sx in (-1, 1):
        R((sx * 0.3, -0.1, 21.2), (sx * 2.5, -0.5, 22.4), 0.08, "st_steel_d", 4)

    B((0.9, 0.4, 3.0), (0, 0.15, 22.5), "st_steel_d", 0.02)

    return done("flood", 3000)


ALL = {"seats": seats, "terrace": terrace, "roof": roof, "gable": gable, "flood": flood}
