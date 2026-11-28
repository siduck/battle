import math

import midkit_core as m
import midkit_structures as st
import midkit_walls as wl


def uld():
    m.setup()
    out = [(-0.75, 0.0), (1.0, 0.0), (1.0, 1.64), (-1.0, 1.64), (-1.0, 0.8)]
    P = [m.sweep_xz(out, 1.5, (0, 0, 0.0), "ap_steel_l")]
    P.append(m.bx((2.0, 1.57, 0.1), (0, 0, 0.0), "ap_steel_d", 0.02))

    for sy in (-1, 1):
        for i in range(9):
            x = -0.8 + i * 0.2

            if x < -0.6:
                continue

            P.append(m.flat((0.05, 0.03, 1.4), (x + 0.1, sy * 0.77, 0.12), "ap_steel"))

    for sx in (-1, 1):
        P.append(m.bx((0.1, 1.57, 0.1), (sx * 0.97, 0, 1.58), "ap_steel_d", 0.02))

    P.append(m.bx((2.0, 0.1, 0.1), (0, -0.74, 1.58), "ap_steel_d", 0.02))
    P.append(m.bx((2.0, 0.1, 0.1), (0, 0.74, 1.58), "ap_steel_d", 0.02))
    P.append(m.bx((1.75, 0.06, 1.3), (0.1, -0.78, 0.2), "ap_steel", 0.01))
    P.append(m.bx((0.1, 0.1, 1.58), (-0.99, -0.74, 0.0), "ap_steel_d", 0.02))
    P.append(m.bx((0.1, 0.1, 1.58), (0.99, -0.74, 0.0), "ap_steel_d", 0.02))

    for i in range(3):
        P.append(m.bx((0.06, 0.04, 1.0), (-0.5 + i * 0.55, -0.82, 0.3), "ap_steel_d", 0.0))

    P.append(m.bx((0.5, 0.04, 0.3), (0.55, -0.82, 1.1), "ap_orange", 0.0))
    P.append(m.bx((2.04, 0.2, 0.12), (0, -0.7, 0.0), "ap_steel_d", 0.02))
    ob = m.finish("uld", P, budget=1500, grime=None)

    return ob


def trolley():
    m.setup()
    P = [m.bx((0.54, 0.9, 0.05), (0, 0, 0.18), "ap_steel_d", 0.01)]

    for sx in (-1, 1):
        for sy in (-1, 1):
            P += m.tire(0.09, 0.05, (sx * 0.25, sy * 0.38, 0.09), axis="x")
            P.append(m.bar((sx * 0.25, sy * 0.38, 0.1), (sx * 0.25, sy * 0.38, 0.19), 0.015, "ap_steel_d", 4))

        P.append(m.bar((sx * 0.26, -0.43, 0.2), (sx * 0.26, -0.43, 1.05), 0.018, "ap_steel", 6))
        P.append(m.bar((sx * 0.26, -0.43, 1.05), (sx * 0.26, -0.2, 1.1), 0.018, "ap_steel", 6))
        P.append(m.bar((sx * 0.26, 0.43, 0.2), (sx * 0.26, 0.43, 0.6), 0.018, "ap_steel", 6))
        P.append(m.bar((sx * 0.26, -0.43, 0.6), (sx * 0.26, 0.43, 0.6), 0.015, "ap_steel", 4))
        P.append(m.bar((sx * 0.26, -0.43, 0.38), (sx * 0.26, 0.43, 0.38), 0.012, "ap_steel", 4))

    P.append(m.bar((-0.26, -0.2, 1.1), (0.26, -0.2, 1.1), 0.025, "ap_orange", 8))
    P.append(m.bar((-0.26, -0.43, 0.2), (0.26, -0.43, 0.2), 0.015, "ap_steel", 4))
    P.append(m.bar((-0.26, -0.43, 0.6), (0.26, -0.43, 0.6), 0.012, "ap_steel", 4))
    P.append(m.bar((-0.26, 0.43, 0.6), (0.26, 0.43, 0.6), 0.012, "ap_steel", 4))
    P.append(m.bar((-0.26, 0.43, 0.2), (0.26, 0.43, 0.2), 0.012, "ap_steel", 4))
    P.append(m.bx((0.54, 0.04, 0.2), (0, 0.44, 0.23), "ap_orange_d", 0.0))
    ob = m.finish("trolley", P, budget=1000, grime=None, cull=False)

    return ob


def pallet_parts(ox=0.0, oy=0.0, oz=0.0, w=1.2, d=1.2, color="ap_wood"):
    P = []

    for i in range(3):
        P.append(m.bx((w, 0.1, 0.022), (ox, oy - d / 2 + 0.05 + i * (d - 0.1) / 2, oz), color, 0.0))
        P.append(m.bx((0.1, 0.1, 0.1), (ox - w / 2 + 0.05 + i * (w - 0.1) / 2, oy - d / 2 + 0.05, oz + 0.022), "ap_wood_l", 0.0))
        P.append(m.bx((0.1, 0.1, 0.1), (ox - w / 2 + 0.05 + i * (w - 0.1) / 2, oy, oz + 0.022), "ap_wood_l", 0.0))
        P.append(m.bx((0.1, 0.1, 0.1), (ox - w / 2 + 0.05 + i * (w - 0.1) / 2, oy + d / 2 - 0.05, oz + 0.022), "ap_wood_l", 0.0))

    for i in range(5):
        P.append(m.bx((w, 0.145, 0.022), (ox, oy - d / 2 + 0.0725 + i * (d - 0.145) / 4, oz + 0.122), color, 0.0))

    return P


def pallet():
    m.setup()
    ob = m.finish("pallet", pallet_parts(), budget=400, grime=None, cull=False)

    return ob


def wrapped():
    m.setup()
    P = pallet_parts(w=1.04, d=0.84)
    n = 0

    for z in (0.144, 0.5, 0.86):
        for ix in (-1, 1):
            for iy in (-1, 1):
                col = "ap_sand" if (ix + iy + n) % 2 else "ap_sand_l"
                P.append(m.bx((0.5, 0.4, 0.35), (ix * 0.255, iy * 0.205, z), col, 0.02))
                P.append(m.flat((0.12, 0.012, 0.35), (ix * 0.255, iy * 0.205 - 0.206 if iy < 0 else iy * 0.205 + 0.206, z + 0.0), "ap_white"))
                n += 1

    P.append(m.bx((1.02, 0.82, 0.04), (0, 0, 1.17), "ap_steel_l", 0.01))

    for z in (0.3, 0.7, 1.05):
        P.append(m.bx((1.07, 0.87, 0.07), (0, 0, z), "ap_steel_l", 0.02))

    ob = m.finish("wrapped", P, budget=1200, grime=None)

    return ob


def ibc():
    m.setup()
    P = [m.bx((1.2, 1.0, 0.14), (0, 0, 0.0), "ap_steel_d", 0.02)]

    for sx in (-1, 1):
        P.append(m.bx((0.12, 1.0, 0.1), (sx * 0.5, 0, 0.14), "ap_steel", 0.01))

    P.append(m.bx((1.1, 0.9, 0.95), (0, 0, 0.2), "ap_white", 0.1, seg=2))
    P.append(m.bx((0.34, 0.34, 0.06), (0.3, 0.15, 1.15), "ap_steel_d", 0.02))
    P.append(m.cyl(0.1, 0.06, (0.3, 0.15, 1.17), "ap_orange", 10))

    for z in (0.18, 0.5, 0.82, 1.14):
        P.append(m.bar((-0.6, -0.5, z), (0.6, -0.5, z), 0.011, "ap_steel", 4))
        P.append(m.bar((-0.6, 0.5, z), (0.6, 0.5, z), 0.011, "ap_steel", 4))
        P.append(m.bar((-0.6, -0.5, z), (-0.6, 0.5, z), 0.011, "ap_steel", 4))
        P.append(m.bar((0.6, -0.5, z), (0.6, 0.5, z), 0.011, "ap_steel", 4))

    for i in range(6):
        x = -0.55 + i * 0.22
        P.append(m.bar((x, -0.5, 0.18), (x, -0.5, 1.14), 0.011, "ap_steel", 4))
        P.append(m.bar((x, 0.5, 0.18), (x, 0.5, 1.14), 0.011, "ap_steel", 4))

    for i in range(5):
        y = -0.4 + i * 0.2
        P.append(m.bar((-0.6, y, 0.18), (-0.6, y, 1.14), 0.011, "ap_steel", 4))
        P.append(m.bar((0.6, y, 0.18), (0.6, y, 1.14), 0.011, "ap_steel", 4))

    P.append(m.bx((0.3, 0.14, 0.18), (-0.15, -0.55, 0.14), "ap_steel_d", 0.02))
    P.append(m.cyl(0.05, 0.12, (-0.15, -0.6, 0.2), "ap_orange", 8))
    ob = m.finish("ibc", P, budget=1800, grime=None)

    return ob


def genset():
    m.setup()
    P = [m.bx((2.5, 1.0, 0.2), (0, 0, 0.0), "ap_steel_d", 0.03)]
    P.append(m.bx((2.4, 1.0, 1.35), (0, 0, 0.2), "ap_orange", 0.07))
    P.append(m.bx((2.5, 1.06, 0.12), (0, 0, 1.55), "ap_orange_d", 0.03))

    for i in range(6):
        P.append(m.flat((0.7, 0.03, 0.04), (-0.65, -0.52, 0.55 + i * 0.1), "ap_dark"))

    P.append(m.bx((0.8, 0.04, 0.7), (-0.65, -0.505, 0.5), "ap_steel_d", 0.01))
    P.append(m.bx((0.6, 0.04, 0.8), (0.45, -0.505, 0.45), "ap_orange_d", 0.01))
    P.append(m.bx((0.3, 0.05, 0.28), (0.45, -0.52, 0.85), "ap_dark", 0.01))
    P.append(m.flat((0.2, 0.02, 0.14), (0.45, -0.545, 0.9), "ap_glass_l"))
    P.append(m.bx((0.08, 0.08, 0.18), (0.78, -0.55, 0.95), "ap_steel", 0.01))
    P.append(m.bx((0.06, 0.06, 0.1), (0.14, -0.545, 0.3), "ap_steel", 0.01))
    P.append(m.cyl(0.09, 0.45, (-0.9, 0.25, 1.66), "ap_steel_d", 10))
    P.append(m.cyl(0.14, 0.04, (-0.9, 0.25, 2.1), "ap_steel", 10))
    P.append(m.cyl(0.12, 0.04, (-0.9, 0.25, 1.62), "ap_steel", 10))
    P.append(m.bx((0.3, 0.12, 0.1), (1.0, 0.0, 1.67), "ap_steel_d", 0.02))
    ob = m.finish("genset", P, budget=1800, grime=None)

    return ob


def container(name, body, trim, door):
    m.setup()
    W, L, H = 2.38, 5.4, 2.7
    P = [m.bx((W, L, 0.2), (0, 0, 0.15), "ap_steel_d", 0.02)]
    P.append(m.bx((W - 0.1, L - 0.1, 0.08), (0, 0, 2.77), body, 0.02))

    for s in (-1, 1):
        sheet = m.corrugated(L - 0.35, H - 0.4, (0, 0, 0.35), body, pitch=0.3, depth=0.07)

        for it in sheet:
            m.k.rotate(it, 90 if s < 0 else -90)
            m.k.move(it, s * (W / 2 - 0.02), -0.0, 0.0)

        P += sheet
        P.append(m.bx((0.12, L, 0.16), (s * (W / 2 - 0.06), 0, 0.28), trim, 0.02))
        P.append(m.bx((0.12, L, 0.16), (s * (W / 2 - 0.06), 0, 2.72), trim, 0.02))

        for sy in (-1, 1):
            P.append(m.bx((0.2, 0.2, H + 0.24), (s * (W / 2 - 0.1), sy * (L / 2 - 0.1), 0.15), trim, 0.03))

    P.append(m.bx((W, 0.16, 0.16), (0, -L / 2 + 0.08, 0.28), trim, 0.02))
    P.append(m.bx((W, 0.16, 0.16), (0, -L / 2 + 0.08, 2.72), trim, 0.02))
    P.append(m.bx((W - 0.2, 0.06, H - 0.2), (0, -L / 2 + 0.06, 0.44), body, 0.01))
    P.append(m.bx((W - 0.2, 0.16, 0.16), (0, L / 2 - 0.08, 0.28), trim, 0.02))
    P.append(m.bx((W - 0.2, 0.06, H - 0.2), (0, L / 2 - 0.06, 0.44), body, 0.01))

    for dx in (-0.45, -0.15, 0.15, 0.45):
        P.append(m.bar((dx, -L / 2 - 0.0, 0.5), (dx, -L / 2 - 0.0, 2.6), 0.022, "ap_steel_l", 6))

    for dx in (-0.45, 0.45):
        for z in (0.9, 1.5, 2.1):
            P.append(m.bx((0.08, 0.06, 0.1), (dx, -L / 2 - 0.04, z), "ap_steel_d", 0.0))

    P.append(m.bx((0.02 + W - 0.4, 0.04, 0.04), (0, -L / 2 - 0.02, 1.3), door, 0.0))
    P.append(m.bx((0.45, 0.03, 0.2), (0.55, -L / 2 - 0.03, 1.85), door, 0.0))
    P.append(m.bx((0.05, 0.1, 2.0), (0, -L / 2 - 0.04, 0.5), trim, 0.01))
    ob = m.finish(name, P, budget=3500, grime=None)

    return ob


def box():
    return container("box", "ap_orange_d", "ap_steel_d", "ap_dark")


def boxgrey():
    return container("boxgrey", "ap_steel", "ap_steel_d", "ap_dark")


def stair():
    m.setup()
    H, run, steps, w = 3.97, 4.0, 18, 1.0
    P = []
    sr = H / steps
    sd = run / steps
    y0 = -2.46

    for i in range(steps):
        P.append(m.bx((w - 0.1, sd + 0.04, 0.06), (0, y0 + (i + 0.5) * sd + 0.0, (i + 1) * sr - 0.06), "ap_steel", 0.0))
        P.append(m.bx((w - 0.1, 0.03, sr - 0.04), (0, y0 + i * sd + 0.02, i * sr + 0.02), "ap_steel_d", 0.0))

    for s in (-1, 1):
        st_ = m.sweep_xz([(0, 0.0), (run, H - 0.06), (run, H - 0.44), (0.0, -0.0 + 0.0)], 0.1, (0, 0, 0), "ap_steel_d")
        m.k.rotate(st_, 90)
        m.k.move(st_, s * (w / 2 - 0.02), y0, 0.0)
        P.append(st_)
        P.append(m.bar((s * (w / 2), y0, 0.95), (s * (w / 2), y0 + run, H + 0.9 - 0.0), 0.025, "ap_orange", 6))

        for i in range(0, steps + 1, 3):
            yy = y0 + i * sd
            zz = i * sr
            P.append(m.bar((s * (w / 2), yy, zz), (s * (w / 2), yy, zz + 0.95), 0.018, "ap_steel_d", 4))


    P.append(m.bx((w, 0.9, 0.1), (0, y0 + run + 0.45, H - 0.1), "ap_steel", 0.01))
    ob = m.finish("stair", P, budget=1800, grime=None, cull=False)

    return ob


def drum():
    m.setup()
    r, h = 0.29, 0.88
    prof = [(0, 0.0), (r * 0.93, 0.0), (r, 0.03), (r, 0.1), (r * 0.94, 0.14), (r * 0.94, 0.28), (r, 0.32), (r, 0.55), (r * 0.94, 0.59), (r * 0.94, 0.73), (r, 0.77), (r, h - 0.03), (r * 0.93, h), (r * 0.84, h), (r * 0.84, h - 0.03), (0, h - 0.03)]
    P = [m.lathe(prof, (0, 0, 0), "ap_blue_d", 14)]
    P.append(m.cyl(0.05, 0.03, (0.14, 0.0, h - 0.03), "ap_steel", 8))
    P.append(m.cyl(0.035, 0.03, (-0.12, 0.08, h - 0.03), "ap_steel_d", 8))
    P.append(m.cyl(r + 0.008, 0.07, (0, 0, 0.36), "ap_orange_d", 14))
    ob = m.finish("drum", P, budget=700, grime=None, cull=False)

    return ob


def cable():
    m.setup()
    R, Wd = 0.55, 0.9
    P = []
    discs = []

    for s in (-1, 1):
        d = m.cyl(R, 0.07, (0, 0, 0), "ap_wood", 16)
        discs.append(d)
        m.k.rotate(d, 90, "X")
        m.k.move(d, 0, s * Wd / 2, R)
        P.append(d)

        for i in range(8):
            a = i * math.pi / 4
            P.append(m.bx((0.1, 0.05, 0.06), (math.cos(a) * 0.4, s * (Wd / 2 + 0.05), R + math.sin(a) * 0.4), "ap_wood_l", 0.0))

    core = m.cyl(0.22, Wd, (0, 0, 0), "ap_wood_l", 12)
    m.k.rotate(core, 90, "X")
    m.k.move(core, 0, Wd / 2 - 0.0, R)
    P.append(core)
    wrap = m.cyl(0.42, Wd - 0.12, (0, 0, 0), "ap_dark", 16)
    m.k.rotate(wrap, 90, "X")
    m.k.move(wrap, 0, (Wd - 0.12) / 2, R)
    P.append(wrap)

    for i in range(5):
        ring = m.cyl(0.425, 0.05, (0, 0, 0), "ap_orange_d", 16)
        m.k.rotate(ring, 90, "X")
        m.k.move(ring, 0, -Wd / 2 + 0.14 + i * 0.16, R)
        P.append(ring)

    P.append(m.bar((0, -Wd / 2 - 0.1, R), (0, Wd / 2 + 0.1, R), 0.03, "ap_steel_d", 6))
    ob = m.finish("cable", P, budget=1500, grime=None)

    return ob


def vault():
    m.setup()
    P = [m.bx((2.0, 1.1, 0.12), (0, 0, 0.0), "ap_steel_d", 0.02)]
    P.append(m.bx((1.98, 1.1, 1.2), (0, 0, 0.12), "ap_green_d", 0.06))
    P.append(m.bx((2.0, 1.17, 0.14), (0, 0, 1.32), "ap_green", 0.04))

    for sx in (-1, 1):
        P.append(m.bx((0.9, 0.04, 1.0), (sx * 0.48, -0.57, 0.22), "ap_green", 0.015))
        P.append(m.bx((0.7, 0.03, 0.74), (sx * 0.48, -0.595, 0.35), "ap_green_d", 0.01))
        P.append(m.bx((0.06, 0.08, 0.28), (sx * 0.08, -0.6, 0.65), "ap_steel_l", 0.01))
        P.append(m.bx((0.08, 0.08, 0.1), (sx * 0.95, -0.58, 0.18), "ap_steel_d", 0.0))
        P.append(m.bx((0.08, 0.08, 0.1), (sx * 0.95, -0.58, 1.0), "ap_steel_d", 0.0))

    P.append(m.bx((0.12, 0.1, 0.3), (0, -0.6, 0.55), "ap_steel_d", 0.01))
    P.append(m.bx((0.3, 0.05, 0.14), (0.0, -0.6, 1.1), "ap_orange", 0.0))

    for sx in (-1, 1):
        P.append(m.bx((0.1, 0.14, 0.1), (sx * 0.94, 0.6, 1.4), "ap_steel_d", 0.01))
        P.append(m.bx((0.2, 0.15, 0.08), (sx * 0.9, 0.0, 1.5), "ap_steel_d", 0.0))

    ob = m.finish("vault", P, budget=1500, grime=None)

    return ob


def engine():
    m.setup()
    P = []
    zc = 1.95
    R = 1.2
    prof = [(1.0, 0.0), (1.16, 0.0), (R, 0.2), (R + 0.02, 0.8), (R, 1.6), (1.12, 2.6), (0.95, 3.3), (0.78, 3.9), (0.55, 4.45), (0.35, 4.5), (0.0, 4.5)]
    cowl = m.lathe(prof, (0, 0, 0), "ap_steel_l", 18)
    P.append(cowl)
    inner = m.lathe([(0.0, 0.0), (1.0, 0.0), (1.0, 0.25), (0.0, 0.25)], (0, 0, 0), "ap_dark", 18)
    P.append(inner)
    spin = m.lathe([(0, 0.0), (0.45, 0.0), (0.22, 0.55), (0, 0.8)], (0, 0, 0), "ap_steel", 14)
    spin_ = spin
    m.k.move(spin_, 0, 0, 0.1)
    P.append(spin_)

    for i in range(14):
        a = i * 2 * math.pi / 14
        blade = m.bx((0.12, 0.04, 0.5), (math.cos(a) * 0.65, math.sin(a) * 0.65, 0.12), "ap_steel", 0.0)
        m.k.rotate(blade, math.degrees(a) + 90 + 20, "Z", (math.cos(a) * 0.65, math.sin(a) * 0.65, 0.0))
        m.k.rotate(blade, 90, "X", (math.cos(a) * 0.65, math.sin(a) * 0.65, 0.12))
        blade.name = "blade"
        m.k.move(blade, 0, 0, 0.0)
        P.append(blade)

    P.append(m.cyl(R + 0.04, 0.1, (0, 0, 1.7), "ap_steel_d", 18))
    P.append(m.cyl(R - 0.02, 0.06, (0, 0, 2.55), "ap_steel_d", 18))
    P.append(m.cyl(0.62, 0.1, (0, 0, 3.7), "ap_steel_d", 14))
    P.append(m.cyl(0.35, 0.18, (0, 0, 4.5), "ap_dark", 12))

    for obj in P:
        m.k.rotate(obj, -90, "X")
        m.k.move(obj, 0, -2.25, zc)

    cradle = []

    for yy in (-0.9, 1.2):
        cradle.append(m.bx((2.2, 0.28, 0.2), (0, yy, 0.55), "ap_orange", 0.03))
        cradle.append(m.bx((0.2, 0.28, 1.0), (-1.0, yy, 0.55), "ap_orange", 0.03))
        cradle.append(m.bx((0.2, 0.28, 1.0), (1.0, yy, 0.55), "ap_orange", 0.03))

        for s in (-1, 1):
            cradle.append(m.bar((s * 0.9, yy, 1.15), (s * 0.55, yy, 0.8), 0.07, "ap_steel_d", 6))

    cradle.append(m.bx((0.3, 3.6, 0.2), (-0.9, 0.15, 0.4), "ap_orange_d", 0.03))
    cradle.append(m.bx((0.3, 3.6, 0.2), (0.9, 0.15, 0.4), "ap_orange_d", 0.03))

    for yy in (-1.0, 1.3):
        for s in (-1, 1):
            cradle += m.tire(0.28, 0.2, (s * 1.1, yy, 0.28), axis="x")

    cradle.append(m.bar((0, -1.6, 0.4), (0, -2.2, 0.35), 0.05, "ap_steel_d", 6))
    ob = m.finish("engine", P + cradle, budget=4000, grime=None)

    return ob


def cabin():
    m.setup()
    W, L, H = 3.9, 7.9, 2.7
    P = [m.bx((W, L, 0.25), (0, 0, 0.0), "ap_steel_d", 0.03)]

    for s in (-1, 1):
        P.append(m.bx((0.2, L, 0.15), (s * 1.4, 0, 0.25), "ap_steel_d", 0.02))

    z0 = 0.25
    P += wl.plain_wall(W, H, (0, -L / 2, z0), "ap_sand", cap=None, band=0.12, band_z=H - 0.4, band_color="ap_steel_d")
    P += wl.plain_wall(W, H, (0, L / 2, z0), "ap_sand", facing=180)
    P += wl.plain_wall(L, H, (-W / 2, 0, z0), "ap_sand", facing=-90)
    P += wl.plain_wall(L, H, (W / 2, 0, z0), "ap_sand", facing=90)

    for s in (-1, 1):
        for y in (-2.2, 0.2, 2.6):
            P += m.window_on(1.4, 1.1, (s * W / 2, y, z0 + 1.0), facing=-90 * s, panes=2, frame="ap_steel_d")

    P.append(m.bx((0.08, 1.0, 2.05), (W / 2 + 0.06, 3.1, z0), "ap_steel_d", 0.01))
    P.append(m.bx((0.08, 0.3, 0.55), (W / 2 + 0.12, 3.1, z0 + 1.15), "ap_glass", 0.0))
    P.append(m.bx((0.9, 1.4, 0.1), (W / 2 + 0.55, 3.1, z0 + 0.5), "ap_steel", 0.01))
    P.append(m.bx((W + 0.5, L + 0.5, 0.2), (0, 0, z0 + H), "ap_sand_l", 0.04))
    P.append(m.bx((W - 0.1, L - 0.1, 0.12), (0, 0, z0 + H + 0.2), "ap_steel_l", 0.02))
    P += wl.ac_unit((-0.6, -2.0, z0 + H + 0.3), size=(1.1, 0.8, 0.5))
    P += wl.vent_hood((0.6, 2.4, z0 + H + 0.3), w=0.5, h=0.4)
    ob = m.finish("cabin", P, budget=3500, grime=None)

    return ob


ALL = {
    "uld": uld,
    "trolley": trolley,
    "pallet": pallet,
    "wrapped": wrapped,
    "ibc": ibc,
    "genset": genset,
    "box": box,
    "boxgrey": boxgrey,
    "stair": stair,
    "drum": drum,
    "cable": cable,
    "vault": vault,
    "engine": engine,
    "cabin": cabin,
}
