import math

import jp
from jp import add, bar, bx, c, flat

k = jp.k


def B(size, at, color, bevel=0.02):
    if jp.MID and bevel > 0 and 0.03 <= min(size) < k.MIN_BEVEL_SIZE:
        return add(k.chamfer(flat(size, at, color), min(bevel, min(size) * 0.2)))

    return add(bx(size, at, color, bevel))


def done(name, budget):
    return jp.finish(name, budget * (3 if jp.MID else 1), fuse_soft=False)


def F(size, at, color):
    return add(flat(size, at, color))


def R(a, b, r, color, sides=6):
    return add(bar(a, b, r, color, sides))


def cyl(r, h, at, color, sides=8, top=None, face=False):
    n = sides * jp.N
    ob = k.prism("cyl", n, r, h, at, c(color), radius_top=top, rotate=(180 / n - 90 if face else 0))

    return add(ob)


def turn(profile, at, color, sides=10, face=False):
    n = sides * jp.N
    ob = k.lathe("lathe", profile, n, at, c(color))

    if face:
        k.rotate(ob, 180 / n - 90, "Z", at)

    return add(ob)


def disc(r, t, at, color, sides=8):
    x, y, z = at
    ob = k.prism("disc", sides * jp.N, r, t, (x, z, 0), c(color))
    k.rotate(ob, 90, "X")
    k.move(ob, 0, y, 0)

    return add(ob)


def side_disc(r, t, at, color, sides=8):
    x, y, z = at
    ob = k.prism("disc", sides * jp.N, r, t, (0, z, -t / 2), c(color))
    k.rotate(ob, 90, "X")
    k.rotate(ob, 90, "Z")
    k.move(ob, x, y, 0)

    return add(ob)


def tilted(size, mid, angle, color, axis="X"):
    ob = flat(size, (0, 0, -size[2] / 2), color)
    k.rotate(ob, angle, axis)
    k.move(ob, *mid)

    return add(ob)


def profile_x(outline, length, x, color):
    ob = k.sweep("prof", outline, length, (0, 0, 0), c(color), axis="y")
    k.rotate(ob, 90)
    k.move(ob, x, 0, 0)

    return add(ob)


def blob(r, at, color, squash=0.85):
    x, y, z = at
    h = r * squash
    prof = [(0, -h), (r * 0.72, -h * 0.7), (r, 0), (r * 0.72, h * 0.7), (0, h)]
    ob = k.lathe("blob", prof, 6 if not jp.MID else 10, at, c(color))
    k.rotate(ob, jp.rng.uniform(0, 60), "Z", at)

    return add(ob)


def glyph(cx, y, cz, s, ink, axis_y=True, pattern=None):
    p = pattern if pattern is not None else jp.rng.randrange(5)
    t = 0.012
    shapes = (
        [(0, 0.42, 0.8, 0.16), (0, -0.42, 0.8, 0.16), (-0.32, 0, 0.16, 0.7), (0.32, 0, 0.16, 0.7)],
        [(0, 0.28, 0.6, 0.16), (0, -0.3, 0.9, 0.16)],
        [(-0.32, 0, 0.15, 0.85), (0, 0.05, 0.15, 0.95), (0.32, -0.05, 0.15, 0.85)],
        [(0, 0.42, 0.8, 0.15), (0, -0.42, 0.8, 0.15), (0.32, 0, 0.15, 0.7)],
        [(0, 0.42, 0.85, 0.15), (-0.34, -0.08, 0.15, 0.85), (0.34, -0.08, 0.15, 0.85)],
    )

    for dx, dz, w, h in shapes[p % len(shapes)]:
        F((w * s, t, h * s), (cx + dx * s, y, cz + dz * s - h * s / 2), ink)


def ac():
    jp.setup(31)

    for x in (-0.3, 0.3):
        B((0.1, 0.38, 0.07), (x, 0, 0), "jp_alu_dark", 0.01)

    B((0.86, 0.3, 0.5), (0, 0.02, 0.07), "jp_cream_light", 0.03)
    B((0.9, 0.34, 0.04), (0, 0.02, 0.56), "jp_cream", 0.01)
    gx, gz = -0.13, 0.32
    disc(0.2, 0.02, (gx, -0.13, gz), "jp_cream_dark", 10)
    disc(0.17, 0.025, (gx, -0.13, gz), "void", 10)

    for a in (0, 60, 120):
        blade = flat((0.07, 0.02, 0.3), (gx, -0.165, gz - 0.15), "jp_alu_dark")
        k.rotate(blade, a, "Y", (gx, -0.165, gz))
        add(blade)

    disc(0.045, 0.02, (gx, -0.17, gz), "jp_alu", 8)

    for dz in (-0.12, -0.04, 0.04, 0.12):
        w = 2 * math.sqrt(max(0.18 ** 2 - dz ** 2, 0))
        F((w, 0.02, 0.02), (gx, -0.18, gz + dz - 0.01), "jp_alu_dark")

    F((0.02, 0.02, 0.36), (gx, -0.181, gz - 0.18), "jp_alu_dark")
    F((0.2, 0.02, 0.38), (0.29, -0.135, 0.14), "jp_alu")

    for z in (0.2, 0.26, 0.32):
        F((0.14, 0.02, 0.02), (0.29, -0.145, z), "jp_alu_dark")

    F((0.04, 0.02, 0.1), (0.29, -0.145, 0.42), "jp_cream_dark")
    B((0.05, 0.1, 0.34), (0.445, 0.08, 0.08), "jp_cream_dark", 0.01)
    F((0.72, 0.02, 0.38), (0, 0.175, 0.13), "jp_alu_dark")

    for z in (0.2, 0.3, 0.4):
        F((0.7, 0.03, 0.02), (0, 0.18, z), "jp_cream_dark")

    return done("ac", 600)


def crate():
    jp.setup(32)
    w, d, h = 0.44, 0.41, 0.36
    F((w - 0.04, d - 0.04, 0.03), (0, 0, 0), "jp_slate_dark")

    for sy in (-1, 1):
        F((w - 0.02, 0.03, h - 0.05), (0, sy * (d / 2 - 0.02), 0), "jp_slate")
        B((w, 0.045, 0.05), (0, sy * (d / 2 - 0.0225), h - 0.05), "jp_slate", 0.01)

        for z in (0.05, 0.16):
            for x in (-0.13, 0, 0.13):
                F((0.1, 0.012, 0.08), (x, sy * (d / 2 - 0.004), z), "jp_slate_dark")

        F((0.3, 0.012, 0.035), (0, sy * (d / 2 - 0.003), 0.262), "jp_red")

    for sx in (-1, 1):
        F((0.03, d - 0.06, h - 0.05), (sx * (w / 2 - 0.02), 0, 0), "jp_slate")
        B((0.045, d, 0.05), (sx * (w / 2 - 0.0225), 0, h - 0.05), "jp_slate", 0.01)
        F((0.012, 0.16, 0.05), (sx * (w / 2 - 0.004), 0, 0.23), "void")

        for y in (-0.08, 0.08):
            F((0.012, 0.1, 0.1), (sx * (w / 2 - 0.004), y, 0.06), "jp_slate_dark")

    for y in (-0.1, 0, 0.1):
        F((w - 0.06, 0.02, 0.16), (0, y, 0.03), "jp_slate_dark")

    for x in (-0.073, 0.073):
        F((0.02, d - 0.06, 0.16), (x, 0, 0.03), "jp_slate_dark")

    return done("crate", 600)


def bikerack():
    jp.setup(33)

    for y in (-0.31, 0.31):
        B((2.03, 0.06, 0.05), (0, y, 0), "jp_alu_dark", 0.01)

    for x in (-0.98, 0.98):
        F((0.05, 0.68, 0.04), (x, 0, 0.0), "jp_alu_dark")

    for i in range(7):
        x = -0.9 + i * 0.3
        pts = [(-0.31, 0.05), (-0.22, 0.44), (0.22, 0.44), (0.31, 0.05)]

        for (ya, za), (yb, zb) in zip(pts, pts[1:]):
            R((x, ya, za), (x, yb, zb), 0.02, "jp_alu", 6)

        F((0.02, 0.4, 0.03), (x, 0, 0.18), "jp_alu_dark")

    R((-0.95, 0, 0.44), (0.95, 0, 0.44), 0.02, "jp_alu_dark", 6)

    return done("bikerack", 900)


def mirror():
    jp.setup(34)
    py, mz = 0.27, 1.96
    cyl(0.1, 0.06, (0, py, 0), "jp_concrete", 8)
    cyl(0.045, 1.95, (0, py, 0.06), "jp_maple", 8)
    cyl(0.055, 0.04, (0, py, 2.01), "jp_red_dark", 8)

    for z in (mz - 0.12, mz + 0.12):
        B((0.12, 0.12, 0.06), (0, py, z - 0.03), "jp_red_dark", 0.01)
        R((0, py, z), (0, -0.15, z), 0.025, "jp_red_dark", 6)

    back = k.lathe("mback", [(0, 0), (0.3, 0), (0.44, 0.05), (0.46, 0.12), (0.43, 0.13)], 12 * jp.N, (0, 0, 0), c("jp_maple"))
    face = k.lathe("mface", [(0.4, 0.12), (0.3, 0.17), (0.16, 0.195), (0, 0.2)], 12 * jp.N, (0, 0, 0), c("jp_glass_light"))
    shine = k.lathe("mshine", [(0.1, 0.0), (0, 0.01)], 8 * jp.N, (-0.13, 0.12, 0.185), c("jp_sign"))

    for ob in (back, face, shine):
        k.rotate(ob, 90, "X")
        k.rotate(ob, -8, "X")
        k.move(ob, 0, -0.15, mz)
        add(ob)

    F((0.3, 0.01, 0.08), (0, py - 0.05, 1.3), "jp_sign")

    return done("mirror", 700)


def awning():
    jp.setup(35)
    w, n = 4.0, 12
    sw = w / n
    yb, zb, yf, zf = 0.56, 1.27, -0.52, 0.68
    length = math.hypot(yb - yf, zb - zf)
    ang = math.degrees(math.atan2(zb - zf, yb - yf))

    for i in range(n):
        col = "jp_red_dark" if i % 2 == 0 else "jp_cream"
        x = -w / 2 + sw * (i + 0.5)
        tilted((sw, length, 0.03), (x, (yb + yf) / 2, (zb + zf) / 2), ang, col)
        F((sw, 0.03, 0.24), (x, yf - 0.02, zf - 0.23), col)
        tab = k.sweep("tab", [(-sw / 2, 0), (sw / 2, 0), (0, -0.07)], 0.03, (x, yf - 0.02, zf - 0.23), c(col), axis="y")
        add(tab)

    B((w, 0.06, 0.08), (0, yb + 0.02, zb - 0.02), "jp_alu_dark", 0.01)
    R((-w / 2, yf + 0.01, zf - 0.01), (w / 2, yf + 0.01, zf - 0.01), 0.025, "jp_alu_dark", 6)

    for sx in (-1, 1):
        cheek = k.sweep("cheek", [(yf, zf - 0.24), (yb, zb - 0.32), (yb, zb), (yf, zf)], 0.03, (0, 0, 0), c("jp_red_dark"), axis="y")
        k.rotate(cheek, 90)
        k.move(cheek, sx * (w / 2 - 0.015), 0, 0)
        add(cheek)

    for x in (-1.9, -0.65, 0.65, 1.9):
        R((x, yb - 0.02, 0.08), (x, yf + 0.06, zf - 0.03), 0.022, "jp_alu_dark", 6)
        B((0.1, 0.04, 0.18), (x, yb + 0.02, 0), "jp_alu_dark", 0.01)

    ob = done("awning", 900)
    k.shade_volume(ob, (-2.1, yf + 0.02, -0.1), (2.1, yb - 0.05, zb - 0.06), 0.72)

    return ob


def planter():
    jp.setup(36)
    B((0.9, 0.32, 0.06), (0, 0, 0), "jp_grey_dark", 0.01)
    B((0.94, 0.34, 0.3), (0, 0, 0.04), "jp_grey", 0.03)
    B((1.0, 0.4, 0.06), (0, 0, 0.32), "jp_cream", 0.02)
    F((0.86, 0.28, 0.02), (0, 0, 0.365), "jp_wood_dark")

    for sy in (-1, 1):
        for x in (-0.16, 0.16):
            F((0.02, 0.012, 0.24), (x, sy * 0.171, 0.07), "jp_grey_dark")

    cols = ("jp_cherry", "jp_sign", "jp_yellow", "jp_cherry_dark")

    for i, x in enumerate((-0.33, -0.11, 0.11, 0.33)):
        y = jp.rng.uniform(-0.04, 0.04)
        blob(0.11, (x, y, 0.4), "jp_leaf" if i % 2 else "jp_leaf_dark", 0.6)

        for j in range(3):
            fx = x + jp.rng.uniform(-0.07, 0.07)
            fy = y + jp.rng.uniform(-0.06, 0.06)
            B((0.05, 0.05, 0.04), (fx, fy, 0.43 + jp.rng.uniform(0, 0.02)), cols[(i + j) % 4], 0.0)

    return done("planter", 600)


def guardrail():
    jp.setup(37)
    front = [(-0.06, 0.86), (-0.105, 0.82), (-0.105, 0.76), (-0.075, 0.70), (-0.105, 0.64), (-0.105, 0.58), (-0.06, 0.54)]
    back = [(y + 0.025, z) for y, z in reversed(front)]
    profile_x(front + back, 4.0, 0, "jp_cream_light")

    for x in (-1.0, 1.0):
        cyl(0.085, 0.08, (x, 0.01, 0), "jp_concrete", 8, face=True)
        cyl(0.07, 0.9, (x, 0.01, 0.06), "jp_alu_dark", 8, face=True)
        turn([(0.072, 0), (0.06, 0.03), (0, 0.04)], (x, 0.01, 0.96), "jp_slate_dark", 8)
        B((0.12, 0.08, 0.2), (x, -0.03, 0.6), "jp_slate_dark", 0.01)
        F((0.06, 0.02, 0.06), (x, -0.065, 0.88), "jp_maple_light")

        for dz in (0.66, 0.74):
            F((0.04, 0.02, 0.03), (x, -0.112, dz), "jp_alu_dark")

    for x in (-1.9, 0, 1.9):
        for dz in (0.66, 0.74):
            F((0.035, 0.02, 0.03), (x, -0.112, dz), "jp_alu_dark")

    return done("guardrail", 600)


def meter():
    jp.setup(38)
    B((0.44, 0.26, 0.06), (0, 0.02, 0), "jp_grey_dark", 0.01)
    B((0.48, 0.28, 0.56), (0, 0.02, 0.06), "jp_grey", 0.025)
    B((0.536, 0.338, 0.07), (0, 0.0, 0.62), "jp_cream_light", 0.02)
    fy = -0.12
    F((0.4, 0.012, 0.48), (0, fy - 0.004, 0.1), "jp_grey_dark")
    F((0.38, 0.014, 0.46), (0, fy - 0.008, 0.11), "jp_grey")
    F((0.26, 0.02, 0.2), (0, fy - 0.012, 0.32), "jp_alu_dark")
    F((0.22, 0.02, 0.16), (0, fy - 0.02, 0.34), "jp_glass_light")
    disc(0.06, 0.012, (-0.04, fy - 0.03, 0.43), "jp_sign", 8)
    F((0.012, 0.012, 0.05), (-0.04, fy - 0.045, 0.43), "jp_char")
    F((0.07, 0.012, 0.025), (0.06, fy - 0.03, 0.37), "jp_char")

    for z in (0.16, 0.2, 0.24):
        F((0.2, 0.014, 0.015), (0, fy - 0.014, z), "jp_grey_dark")

    F((0.03, 0.03, 0.08), (0.15, fy - 0.02, 0.22), "jp_alu_dark")

    for z in (0.18, 0.48):
        F((0.02, 0.03, 0.06), (-0.195, fy - 0.015, z), "jp_alu_dark")

    R((0.12, 0.08, 0.06), (0.12, 0.08, 0.0), 0.03, "jp_alu_dark", 6)

    return done("meter", 500)


def noren():
    jp.setup(39)
    R((-0.66, 0.0, 0.74), (0.66, 0.0, 0.74), 0.03, "jp_wood", 6)

    for sx in (-1, 1):
        cyl(0.04, 0.05, (sx * 0.68, 0, 0.72), "jp_wood_dark", 6)
        F((0.04, 0.07, 0.04), (sx * 0.62, 0.01, 0.72), "jp_alu_dark")

    pw = 0.31
    pats = (0, 2, 1, 3)

    for i in range(4):
        x = -0.48 + i * 0.32
        y = -0.012 if i % 2 else 0.006
        F((pw, 0.025, 0.66), (x, y, 0.0), "jp_indigo")

        for lx in (-0.1, 0.0, 0.1):
            F((0.05, 0.07, 0.05), (x + lx, 0.0, 0.705), "jp_tile_dark")

        glyph(x, y - 0.018, 0.36, 0.2, "jp_sign", pattern=pats[i])

    F((1.26, 0.03, 0.03), (0, 0.0, 0.64), "jp_tile_dark")

    return done("noren", 600)


def lantern():
    jp.setup(40)
    r, h, z0 = 0.17, 0.38, 0.05
    prof = [(0, 0), (r * 0.62, 0)]

    for i in range(1, 8):
        t = i / 8
        prof.append((r * (0.62 + 0.38 * math.sin(math.pi * t) ** 0.6), h * t))

    prof += [(r * 0.62, h), (0, h)]
    turn(prof, (0, 0, z0), "jp_red", 12, face=True)

    for f in (0.3, 0.7):
        rr = r * (0.62 + 0.38 * math.sin(math.pi * f) ** 0.6)
        cyl(rr + 0.004, 0.012, (0, 0, z0 + h * f - 0.006), "jp_red_dark", 12, face=True)

    cyl(0.11, 0.05, (0, 0, 0.0), "jp_char", 10)
    cyl(0.11, 0.04, (0, 0, z0 + h - 0.005), "jp_char", 10)
    ap = r * math.cos(math.pi / (12 * jp.N))
    F((0.13, 0.02, 0.2), (0, -ap + 0.006, z0 + 0.09), "jp_sign")
    glyph(0, -ap - 0.006, z0 + 0.19, 0.15, "jp_char", pattern=1)
    R((-0.04, 0, 0.475), (0.04, 0, 0.475), 0.0125, "jp_char", 4)

    for sx in (-1, 1):
        R((sx * 0.04, 0, z0 + h + 0.03), (sx * 0.04, 0, 0.475), 0.0125, "jp_char", 4)

    return done("lantern", 500)


def drum():
    jp.setup(41)
    turn([(0, 0), (0.27, 0), (0.29, 0.03), (0.29, 0.86), (0.27, 0.89), (0, 0.89)], (0, 0, 0), "jp_slate", 12, face=True)

    for z in (0.28, 0.58):
        cyl(0.3, 0.05, (0, 0, z), "jp_slate_dark", 12, face=True)

    cyl(0.255, 0.012, (0, 0, 0.885), "jp_slate_dark", 12, face=True)

    for x, y in ((-0.14, 0.08), (0.15, -0.06)):
        cyl(0.04, 0.03, (x, y, 0.89), "jp_tile", 6)

    ap = 0.29 * math.cos(math.pi / (12 * jp.N))
    F((0.22, 0.012, 0.16), (0, -ap - 0.002, 0.38), "jp_sign")
    F((0.14, 0.014, 0.03), (0, -ap - 0.007, 0.46), "jp_indigo")

    return done("drum", 600)


def potted():
    jp.setup(42)
    turn([(0, 0), (0.22, 0), (0.29, 0.44), (0, 0.44)], (0, 0, 0), "jp_tile", 10)
    cyl(0.32, 0.07, (0, 0, 0.42), "jp_tile_light", 10)
    cyl(0.28, 0.02, (0, 0, 0.48), "jp_wood_dark", 10)
    R((0, 0, 0.48), (0, 0, 0.75), 0.04, "jp_bark", 6)
    blob(0.3, (0, 0, 1.1), "jp_leaf", 0.95)

    for i in range(5):
        a = i * 72 + 20
        rr = 0.27
        blob(0.2, (rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a)), 0.86 + 0.06 * (i % 2)), ("jp_leaf_dark", "jp_leaf", "jp_leaf_light")[i % 3], 0.9)

    blob(0.18, (0.05, -0.05, 1.25), "jp_leaf_light", 0.9)

    return done("potted", 700)


def ramen():
    jp.setup(43)

    for sx in (-1, 1):
        x = sx * 0.84
        side_disc(0.3, 0.06, (x, 0.16, 0.3), "jp_wood_dark", 10)
        side_disc(0.24, 0.07, (x, 0.16, 0.3), "jp_wood", 10)
        side_disc(0.06, 0.1, (x, 0.16, 0.3), "jp_char", 6)

        for a in (0, 60, 120):
            sp = flat((0.075, 0.03, 0.44), (x, 0.16, 0.08), "jp_wood_dark")
            k.rotate(sp, a, "X", (x, 0.16, 0.3))
            add(sp)

    R((-0.8, 0.16, 0.3), (0.8, 0.16, 0.3), 0.03, "jp_char", 6)

    for x in (-0.68, 0.68):
        for y in (-0.1, 0.48):
            B((0.06, 0.06, 0.32), (x, y, 0), "jp_wood_dark", 0.0)

    B((1.56, 0.72, 0.06), (0, 0.2, 0.28), "jp_wood_dark", 0.02)
    B((1.5, 0.66, 0.6), (0, 0.2, 0.34), "jp_wood", 0.02)

    for i in range(7):
        F((0.02, 0.012, 0.56), (-0.63 + i * 0.21, -0.134, 0.36), "jp_wood_dark")

    B((0.62, 0.03, 0.22), (0.3, -0.148, 0.55), "jp_sign", 0.0)

    for i, x in enumerate((0.12, 0.3, 0.48)):
        glyph(x, -0.17, 0.66, 0.13, "jp_red_dark", pattern=i)

    B((1.62, 0.38, 0.05), (0, -0.26, 0.92), "jp_wood_light", 0.01)
    B((1.5, 0.66, 0.04), (0, 0.2, 0.94), "jp_wood_light", 0.01)

    for x in (-0.6, 0.6):
        F((0.04, 0.28, 0.04), (x, -0.27, 0.88), "jp_wood_dark")

    cyl(0.15, 0.24, (0.36, 0.3, 0.98), "jp_alu", 10)
    cyl(0.16, 0.03, (0.36, 0.3, 1.22), "jp_alu_dark", 10)
    cyl(0.1, 0.16, (0.0, 0.32, 0.98), "jp_alu_dark", 8)

    for i in range(3):
        cyl(0.07, 0.04, (-0.42, 0.3, 0.98 + i * 0.045), "jp_sign", 8, top=0.075)

    for x in (-0.72, 0.72):
        for y in (-0.08, 0.5):
            B((0.07, 0.07, 0.95), (x, y, 0.94), "jp_wood_dark", 0.01)

    B((1.5, 0.07, 0.08), (0, 0.5, 1.82), "jp_wood_dark", 0.01)
    B((1.5, 0.07, 0.08), (0, -0.08, 1.8), "jp_wood_dark", 0.01)
    yb, zb, yf, zf = 0.62, 2.03, -0.62, 1.86
    length = math.hypot(yb - yf, zb - zf)
    ang = math.degrees(math.atan2(zb - zf, yb - yf))
    tilted((1.87, length, 0.06), (0, 0, (zb + zf) / 2 + 0.03), ang, "jp_red_dark")
    F((1.87, 0.03, 0.16), (0, yf, zf - 0.12), "jp_red_dark")
    F((1.87, 0.032, 0.04), (0, yf, zf - 0.12), "jp_wood_dark")

    for i in range(4):
        x = -0.52 + i * 0.35
        F((0.33, 0.025, 0.32), (x, yf + 0.06, 1.42), "jp_indigo")
        glyph(x, yf + 0.04, 1.6, 0.14, "jp_sign", pattern=(1, 3, 0, 2)[i])

    R((-0.72, yf + 0.06, 1.75), (0.72, yf + 0.06, 1.75), 0.02, "jp_wood_dark", 6)
    lx, ly = -0.82, -0.5
    turn([(0, 0), (0.07, 0), (0.095, 0.08), (0.095, 0.16), (0.07, 0.24), (0, 0.24)], (lx, ly, 1.36), "jp_red", 8, face=True)

    for z in (1.34, 1.59):
        cyl(0.06, 0.03, (lx, ly, z), "jp_char", 8)

    R((lx, ly, 1.62), (lx, ly, 1.8), 0.012, "jp_char", 4)
    ob = done("ramen", 2500)
    k.shade_volume(ob, (-0.9, -0.62, 0.95), (0.9, 0.62, 1.8), 0.82)

    return ob


def postbox():
    jp.setup(44)
    B((0.3, 0.3, 0.06), (0, 0, 0), "jp_char", 0.01)
    B((0.18, 0.18, 0.42), (0, 0, 0.04), "jp_red_dark", 0.02)
    B((0.5, 0.48, 0.05), (0, 0, 0.44), "jp_red_dark", 0.01)
    B((0.48, 0.46, 0.66), (0, 0, 0.47), "jp_red", 0.03)
    B((0.53, 0.51, 0.03), (0, 0, 1.13), "jp_red_dark", 0.01)
    seg = 6 * jp.N
    arch = [(0.24 * math.cos(math.pi * i / seg), 0.24 * math.sin(math.pi * i / seg)) for i in range(seg + 1)]
    add(k.sweep("top", arch, 0.46, (0, 0, 1.155), c("jp_red"), axis="y"))
    fy = -0.23

    B((0.44, 0.06, 0.03), (0, fy - 0.025, 1.03), "jp_red_dark", 0.0)

    for x in (-0.11, 0.11):
        F((0.17, 0.014, 0.035), (x, fy - 0.004, 0.98), "void")

    F((0.38, 0.012, 0.38), (0, fy - 0.004, 0.52), "jp_red_dark")
    F((0.36, 0.014, 0.36), (0, fy - 0.007, 0.53), "jp_red")
    F((0.18, 0.016, 0.11), (0, fy - 0.01, 0.74), "jp_sign")

    for z in (0.76, 0.8):
        F((0.13, 0.018, 0.02), (0, fy - 0.012, z), "jp_char")

    F((0.04, 0.03, 0.08), (0.14, fy - 0.015, 0.62), "jp_alu")
    F((0.1, 0.016, 0.02), (0, fy - 0.004, 1.22), "jp_sign")
    F((0.02, 0.016, 0.06), (0, fy - 0.004, 1.17), "jp_sign")

    return done("postbox", 600)


def shutter():
    jp.setup(45)
    F((4.0, 0.3, 0.03), (0, 0, 0), "jp_concrete")

    for sx in (-1, 1):
        B((0.14, 0.2, 2.15), (sx * 1.92, 0, 0.03), "jp_cream_dark", 0.02)

    top = 2.16
    rib = 0.09 if not jp.MID else 0.06
    n = int((top - 0.1) / rib)

    for i in range(n):
        z = top - (i + 1) * rib
        F((3.72, 0.04 + 0.015 * (i % 2), rib), (0, -0.02 - 0.008 * (i % 2), z), "jp_alu" if i % 2 else "jp_alu_dark")

    F((3.72, 0.02, top - 0.1), (0, 0.02, 0.1), "jp_alu_dark")
    B((3.72, 0.1, 0.1), (0, -0.02, top - n * rib - 0.1), "jp_slate_dark", 0.01)

    for x in (-0.6, 0.6):
        F((0.16, 0.04, 0.04), (x, -0.09, 0.1), "jp_alu")

    F((0.06, 0.03, 0.06), (0, -0.085, 0.12), "jp_char")

    for i in range(8):
        F((0.2, 0.012, 0.04), (-1.4 + i * 0.4, -0.05, 1.92), "void")

    B((3.84, 0.56, 0.44), (0, 0.0, 2.16), "jp_cream", 0.03)

    for sx in (-1, 1):
        B((0.08, 0.6, 0.46), (sx * 1.96, 0.0, 2.15), "jp_cream_dark", 0.02)

    F((3.84, 0.012, 0.03), (0, -0.282, 2.4), "jp_cream_dark")
    F((3.84, 0.012, 0.03), (0, -0.282, 2.22), "jp_cream_dark")

    return done("shutter", 1200)


def board():
    jp.setup(46)
    ang = math.degrees(math.atan2(0.23, 0.98))

    for side in (0, 1):
        items = []
        items.append(flat((0.05, 0.04, 1.0), (-0.31, 0, 0), "jp_wood"))
        items.append(flat((0.05, 0.04, 1.0), (0.31, 0, 0), "jp_wood"))
        items.append(flat((0.67, 0.04, 0.06), (0, 0, 0.94), "jp_wood"))
        items.append(flat((0.57, 0.04, 0.05), (0, 0, 0.26), "jp_wood"))
        items.append(flat((0.57, 0.025, 0.62), (0, 0.004, 0.31), "jp_char"))
        items.append(flat((0.57, 0.025, 0.14), (0, 0.004, 0.12), "jp_cream"))

        for i, (w, z) in enumerate(((0.34, 0.8), (0.42, 0.7), (0.26, 0.6), (0.38, 0.5), (0.3, 0.4))):
            items.append(flat((w, 0.012, 0.04), (-0.2 + w / 2, -0.012, z), "jp_sign" if i else "jp_yellow"))

        items.append(flat((0.08, 0.012, 0.06), (0.16, -0.012, 0.69), "jp_cherry"))
        items.append(flat((0.3, 0.012, 0.04), (-0.05, -0.012, 0.17), "jp_red_dark"))

        for it in items:
            if side:
                k.rotate(it, 180)

            k.rotate(it, -ang if side == 0 else ang, "X", (0, 0, 1.0))
            add(it)

    R((-0.3, 0, 1.0), (0.3, 0, 1.0), 0.02, "jp_alu_dark", 6)

    for sx in (-1, 1):
        R((sx * 0.31, -0.08, 0.4), (sx * 0.31, 0.08, 0.4), 0.0125, "jp_alu_dark", 4)

    return done("board", 600)


def stonefence():
    jp.setup(47)
    B((4.0, 0.26, 0.3), (0, 0, 0), "jp_sand_dark", 0.02)
    B((4.0, 0.3, 0.05), (0, 0, 0.3), "jp_cream", 0.01)

    for x in (-1.6, -0.6, 0.4, 1.4):
        F((0.02, 0.27, 0.27), (x + jp.rng.uniform(-0.1, 0.1), 0, 0.02), "jp_grey_dark")

    for z in (0.52, 0.76):
        r = add(bx((4.0, 0.14, 0.12), (0, 0, z), "jp_sand", 0.02))
        k.jitter(r, 0.006, seed=int(z * 100))

    for x in (-1.0, 1.0):
        B((0.28, 0.28, 0.86), (x, 0, 0.02), "jp_sand", 0.025)
        B((0.36, 0.36, 0.07), (x, 0, 0.88), "jp_cream", 0.015)
        add(k.box("cap", (0.3, 0.3, 0.05), (x, 0, 0.95), c("jp_cream"), (0.25, 0.25)))
        F((0.2, 0.012, 0.03), (x, -0.142, 0.66), "jp_sand_dark")

    for x in (-1.5, -0.5, 0.0, 0.5, 1.5):
        B((0.1, 0.1, 0.24), (x, 0, 0.6), "jp_sand_dark", 0.0)

    return done("stonefence", 600)


def bin():
    jp.setup(48)
    cyl(0.285, 0.08, (0, 0, 0), "jp_char", 12, face=True)
    turn([(0, 0), (0.27, 0), (0.28, 0.72), (0, 0.72)], (0, 0, 0.08), "jp_grey", 12, face=True)
    turn([(0, 0), (0.296, 0), (0.29, 0.04), (0.2, 0.09), (0, 0.1)], (0, 0, 0.8), "jp_slate_dark", 12, face=True)
    ap = 0.27 * math.cos(math.pi / (12 * jp.N))
    F((0.36, 0.02, 0.18), (0, -ap - 0.006, 0.55), "jp_slate_dark")
    F((0.3, 0.02, 0.12), (0, -ap - 0.012, 0.58), "void")
    cyl(0.282, 0.04, (0, 0, 0.4), "jp_green", 12, face=True)

    for z in (0.24, 0.3):
        cyl(0.278, 0.012, (0, 0, z), "jp_grey_dark", 12, face=True)

    return done("bin", 600)


def lamp():
    jp.setup(49)
    py = 0.8
    B((0.36, 0.36, 0.12), (0, py, 0), "jp_concrete", 0.02)
    cyl(0.11, 0.5, (0, py, 0.12), "jp_slate_dark", 8)
    cyl(0.075, 4.3, (0, py, 0.62), "jp_slate", 8, top=0.055)
    turn([(0.06, 0), (0.04, 0.06), (0, 0.08)], (0, py, 4.92), "jp_slate_dark", 8)
    R((0, py, 4.55), (0, 0.4, 4.82), 0.04, "jp_slate", 6)
    R((0, 0.4, 4.82), (0, -0.62, 4.88), 0.035, "jp_slate", 6)
    B((0.34, 0.66, 0.12), (0, -0.66, 4.8), "jp_slate_dark", 0.03)
    F((0.26, 0.52, 0.02), (0, -0.66, 4.785), "jp_sign")
    B((0.2, 0.3, 0.06), (0, -0.62, 4.92), "jp_slate", 0.01)

    for z in (2.62, 3.62):
        R((-0.42, py, z), (0.42, py, z), 0.02, "jp_slate_dark", 6)

    for sx, col in ((-1, "jp_indigo"), (1, "jp_indigo")):
        x = sx * 0.26
        F((0.3, 0.025, 0.96), (x, py, 2.64), col)
        F((0.3, 0.03, 0.04), (x, py, 2.64), "jp_tile_dark")

        for f in (-1, 1):
            glyph(x, py + f * 0.016, 3.1, 0.16, "jp_sign", pattern=(0 if sx < 0 else 2))
            glyph(x, py + f * 0.016, 3.38, 0.12, "jp_sign", pattern=(3 if sx < 0 else 1))

    F((0.16, 0.012, 0.4), (0, py - 0.075, 1.6), "jp_sign")

    for z in (1.75, 1.85):
        F((0.1, 0.014, 0.04), (0, py - 0.078, z), "jp_indigo")

    return done("lamp", 900)


def cone():
    jp.setup(50)
    B((0.44, 0.44, 0.04), (0, 0, 0), "jp_char", 0.0)
    cyl(0.2, 0.03, (0, 0, 0.04), "jp_char", 10, top=0.17)
    h = 0.62
    turn([(0, 0), (0.17, 0), (0.035, h), (0, h)], (0, 0, 0.04), "jp_maple", 10)

    def rad(z):
        return 0.17 - 0.135 * z / h

    for z0, z1 in ((0.2, 0.3), (0.38, 0.46)):
        cyl(rad(z0) + 0.005, z1 - z0, (0, 0, 0.04 + z0), "jp_sign", 10, top=rad(z1) + 0.005)

    cyl(0.045, 0.04, (0, 0, 0.64), "jp_maple", 10, top=0.03)

    return done("cone", 400)


def signal():
    jp.setup(51)
    px, py = -1.5, 0.12
    B((0.4, 0.4, 0.1), (px, py, 0), "jp_concrete", 0.02)
    cyl(0.11, 0.4, (px, py, 0.1), "jp_alu_dark", 8)
    cyl(0.085, 4.4, (px, py, 0.5), "jp_alu", 8, top=0.07)
    turn([(0.075, 0), (0.05, 0.06), (0, 0.1)], (px, py, 4.9), "jp_alu_dark", 8)
    R((px, py, 4.55), (1.0, py, 4.55), 0.05, "jp_alu", 6)
    R((px, py, 4.0), (-0.7, py, 4.53), 0.03, "jp_alu", 6)
    hy = 0.05
    B((1.2, 0.3, 0.36), (0.95, hy, 4.37), "jp_alu_dark", 0.03)
    B((0.12, 0.12, 0.12), (0.95, hy, 4.5), "jp_alu_dark", 0.0)

    for x, col in ((0.6, "jp_green"), (0.95, "jp_maple_light"), (1.3, "jp_red_dark")):
        disc(0.12, 0.02, (x, hy - 0.15, 4.55), "jp_char", 10)
        disc(0.1, 0.025, (x, hy - 0.15, 4.55), col, 10)
        F((0.3, 0.26, 0.03), (x, hy - 0.28, 4.69), "jp_alu_dark")

        for sx in (-1, 1):
            F((0.025, 0.26, 0.17), (x + sx * 0.14, hy - 0.28, 4.52), "jp_alu_dark")

    B((0.64, 0.04, 0.22), (-0.8, py, 4.24), "jp_indigo", 0.01)

    for x in (-0.98, -0.82, -0.66):
        glyph(x, py - 0.025, 4.35, 0.1, "jp_sign")

    R((-0.8, py, 4.46), (-0.8, py, 4.53), 0.012, "jp_alu_dark", 4)
    B((0.26, 0.2, 0.52), (px, py - 0.18, 2.4), "jp_alu_dark", 0.02)
    F((0.18, 0.02, 0.18), (px, py - 0.285, 2.66), "jp_red_dark")
    F((0.18, 0.02, 0.18), (px, py - 0.285, 2.44), "jp_green")
    F((0.3, 0.2, 0.03), (px, py - 0.18, 2.92), "jp_alu_dark")
    B((0.14, 0.1, 0.2), (px, py - 0.12, 1.05), "jp_yellow", 0.0)
    F((0.06, 0.02, 0.06), (px, py - 0.175, 1.12), "jp_char")

    return done("signal", 1200)


def pole():
    jp.setup(52)
    H = 7.75

    def rad(z):
        return 0.165 - 0.055 * z / H

    cyl(0.21, 0.12, (0, 0, 0), "jp_concrete", 8)
    cyl(0.165, H, (0, 0, 0), "jp_grey", 8, top=0.11)
    
    for i in range(3):
        z0 = 0.12 + i * 0.56
        cyl(rad(z0) + 0.012, 0.3, (0, 0, z0), "jp_yellow", 8, top=rad(z0 + 0.3) + 0.012)

    for z, half, xs in ((7.7, 0.55, (0.3, 0.95)), (7.15, 0.95, (0.15, 0.6, 1.6)), (6.6, 0.75, (0.25, 1.25))):
        dx = half * 0.75
        B((half * 2, 0.1, 0.1), (dx, 0, z), "jp_alu_dark", 0.01)
        R((dx + half * 0.7, 0, z), (0, 0, z - 0.45), 0.02, "jp_alu_dark", 4)

        for x in xs:
            turn([(0, 0), (0.06, 0), (0.035, 0.16), (0, 0.16)], (x, 0, z + 0.1), "jp_sign", 6 if jp.MID else 4)

            for sy in (-1, 1):
                R((x, sy * 0.04, z + 0.22), (x, sy * 4.09, z + 0.03), 0.0125, "jp_char", 4)

    turn([(0, 0), (0.05, 0), (0.07, 0.05), (0.035, 0.09), (0, 0.1)], (0, 0, H + 0.0), "jp_sign", 6)

    ty = -0.42
    cyl(0.2, 0.62, (0, ty, 5.6), "jp_alu", 8)
    cyl(0.215, 0.05, (0, ty, 6.2), "jp_alu_dark", 8)

    for z in (5.75, 6.1):
        B((0.08, 0.3, 0.06), (0, -0.24, z), "jp_alu_dark", 0.0)

    for a in (0, 90, 180, 270):
        fin = flat((0.03, 0.1, 0.42), (0, ty - 0.22, 5.7), "jp_alu_dark")
        k.rotate(fin, a, "Z", (0, ty, 0))
        add(fin)

    for x in (-0.08, 0.08):
        turn([(0, 0), (0.03, 0), (0.04, 0.04), (0.02, 0.08), (0, 0.08)], (x, ty, 6.25), "jp_sign", 6)
        R((x, ty, 6.33), (x * 7.75, -0.05, 6.8), 0.0125, "jp_char", 4)

    for sy in (-1, 1):
        R((0.2, sy * 0.15, 4.92), (0.2, sy * 4.09, 4.82), 0.025, "jp_char", 6)

    R((0.2, -0.15, 4.92), (0.2, 0.15, 4.92), 0.025, "jp_char", 6)
    B((0.06, 0.1, 0.1), (0.15, 0, 4.86), "jp_alu_dark", 0.0)
    B((0.16, 0.5, 0.16), (0.2, -1.0, 4.82), "jp_char", 0.02)

    for i in range(9):
        z = 2.2 + i * 0.45
        sx = 1 if i % 2 else -1
        r = rad(z)
        R((sx * r * 0.8, 0, z), (sx * (r + 0.18), 0, z), 0.015, "jp_alu_dark", 4)

    r = rad(2.2)
    F((0.24, 0.03, 0.56), (0, -r - 0.01, 1.92), "jp_sign")

    for z in (2.3, 2.15, 2.0):
        F((0.16, 0.012, 0.06), (0, -r - 0.03, z), "jp_indigo")

    return done("pole", 2500)


def vending():
    jp.setup(53)
    by = 0.03
    fy = by - 0.35
    B((1.0, 0.66, 0.08), (0, by, 0), "jp_char", 0.01)
    B((1.04, 0.7, 1.74), (0, by, 0.08), "jp_cream_light", 0.03)
    B((1.11, 0.76, 0.08), (0, by, 1.82), "jp_cream", 0.02)
    F((0.98, 0.03, 0.16), (0, fy - 0.01, 1.6), "jp_red")

    for i, x in enumerate((-0.25, 0.0, 0.25)):
        glyph(x, fy - 0.028, 1.68, 0.11, "jp_sign", pattern=i)

    for sx in (-1, 1):
        F((0.014, 0.66, 0.06), (sx * 0.52, by, 1.5), "jp_red")

    F((0.96, 0.03, 0.72), (0, fy - 0.01, 0.84), "jp_alu_dark")
    F((0.9, 0.02, 0.66), (0, fy - 0.025, 0.87), "jp_glass")
    cols = ("jp_red", "jp_indigo", "jp_green", "jp_yellow", "jp_sign", "jp_maple_light", "jp_wood_light", "jp_cherry")

    for row, z in enumerate((0.95, 1.15, 1.35)):
        F((0.86, 0.025, 0.02), (0, fy - 0.03, z - 0.02), "jp_alu")

        for i in range(7):
            x = -0.36 + i * 0.12
            F((0.085, 0.03, 0.13), (x, fy - 0.04, z), cols[(i * 3 + row * 5) % len(cols)])
            F((0.05, 0.03, 0.025), (x, fy - 0.04, z - 0.055), "jp_sign" if (i + row) % 3 else "jp_red")

    F((0.24, 0.03, 0.46), (0.33, fy - 0.01, 0.3), "jp_alu_dark")
    F((0.03, 0.02, 0.07), (0.27, fy - 0.03, 0.62), "void")
    F((0.12, 0.02, 0.025), (0.37, fy - 0.03, 0.52), "void")
    F((0.12, 0.02, 0.05), (0.35, fy - 0.03, 0.4), "jp_green")
    F((0.04, 0.03, 0.04), (0.39, fy - 0.03, 0.62), "jp_alu")
    F((0.6, 0.02, 0.4), (-0.17, fy - 0.006, 0.36), "jp_sign")

    for i, (w, z) in enumerate(((0.36, 0.64), (0.46, 0.56), (0.3, 0.48))):
        F((w, 0.012, 0.04), (-0.4 + w / 2, fy - 0.016, z), "jp_indigo" if i else "jp_red_dark")

    F((0.7, 0.03, 0.18), (-0.1, fy - 0.01, 0.1), "jp_char")
    F((0.64, 0.02, 0.11), (-0.1, fy - 0.03, 0.13), "jp_alu_dark")

    return done("vending", 1000)


def kanji():
    jp.setup(54)
    x0, bw = -0.08, 0.44
    B((bw, 0.1, 2.24), (x0, 0, 0.08), "jp_sign", 0.02)

    for sx in (-1, 1):
        B((0.05, 0.13, 2.3), (x0 + sx * (bw / 2 + 0.025), 0, 0.04), "jp_wood", 0.01)

    B((bw + 0.12, 0.16, 0.06), (x0, 0, 2.34), "jp_wood_dark", 0.01)
    B((bw + 0.1, 0.13, 0.05), (x0, 0, 0.0), "jp_wood_dark", 0.01)

    for side in (-1, 1):
        for i, z in enumerate((1.9, 1.42, 0.94, 0.46)):
            glyph(x0, side * 0.056, z, 0.3, "jp_red_dark", pattern=(i + (0 if side < 0 else 2)) % 4)

    for z in (0.4, 1.95):
        B((0.16, 0.04, 0.04), (0.25, 0, z), "jp_alu_dark", 0.0)
        R((0.19, 0, z - 0.02), (0.31, 0, z - 0.22), 0.0125, "jp_alu_dark", 4)
        B((0.03, 0.12, 0.3), (0.33, 0, z - 0.24), "jp_alu_dark", 0.0)

    return done("kanji", 700)


def bench():
    jp.setup(55)

    for y in (-0.19, -0.06, 0.07):
        B((1.6, 0.12, 0.045), (0, y, 0.42), "jp_wood", 0.012)

    for y, z in ((0.17, 0.56), (0.2, 0.72)):
        s = bx((1.6, 0.035, 0.13), (0, 0, -0.065), "jp_wood", 0.01)
        k.rotate(s, -12, "X")
        k.move(s, 0, y, z + 0.065)
        add(s)

    for x in (-0.65, 0.65):
        F((0.05, 0.05, 0.42), (x, -0.2, 0), "jp_char")
        R((x, 0.12, 0.0), (x, 0.24, 0.86), 0.025, "jp_char", 4)
        F((0.05, 0.42, 0.04), (x, -0.04, 0.38), "jp_char")
        F((0.06, 0.5, 0.03), (x, -0.0, 0.0), "jp_char")

    return done("bench", 500)


def track():
    jp.setup(56)
    F((4.0, 4.0, 0.03), (0, 0, 0), "jp_tile_dark")
    F((2.2, 4.0, 0.034), (0, 0, 0), "jp_concrete")

    for sx in (-1, 1):
        F((0.1, 4.0, 0.038), (sx * 1.12, 0, 0), "jp_grey")

    for i in range(7):
        y = -2 + (i + 0.5) * 4 / 7
        F((1.9, 0.22, 0.038), (0, y, 0), "jp_wood_dark")

    for sx in (-1, 1):
        x = sx * 0.72
        F((0.06, 4.0, 0.04), (x - sx * 0.06, 0, 0), "jp_char")
        F((0.07, 4.0, 0.05), (x, 0, 0), "jp_alu")
        F((0.03, 4.0, 0.042), (x + sx * 0.05, 0, 0), "jp_alu_dark")

    for x in (-1.6, 1.5):
        F((0.02, 4.0, 0.031), (x, 0, 0), "jp_grey_dark")

    return jp.finish("track", 400, fuse_soft=False, gradient=False)


def blockwall():
    jp.setup(57)
    B((4.0, 0.34, 0.14), (0, 0, 0), "jp_concrete", 0.02)
    F((3.99, 0.13, 1.4), (0, 0, 0.14), "jp_grey_dark")
    bw, bh = 0.4, 0.2
    rows = 7

    for r in range(rows):
        z = 0.14 + r * bh
        off = 0 if r % 2 == 0 else bw / 2
        x = -2.0 - off

        while x < 2.0:
            x0, x1 = max(x, -2.0), min(x + bw, 2.0)
            pierced = r in (4, 5) and -0.8 < (x0 + x1) / 2 < 0.8 and r % 2 == 0
            col = "jp_grey" if jp.rng.random() > 0.18 else "jp_concrete"

            if x1 - x0 > 0.05:
                if pierced:
                    for sy in (-1, 1):
                        F((x1 - x0 - 0.012, 0.012, bh - 0.012), ((x0 + x1) / 2, sy * 0.071, z + 0.006), col)

                    F((x1 - x0 - 0.12, 0.17, bh - 0.11), ((x0 + x1) / 2, 0, z + 0.055), "void")
                else:
                    F((x1 - x0 - 0.012, 0.15, bh - 0.012), ((x0 + x1) / 2, 0, z + 0.006), col)

            x += bw

    B((4.0, 0.2, 0.06), (0, 0, 0.14 + rows * bh), "jp_concrete", 0.015)

    return done("blockwall", 1100)


ALL = {
    "ac": ac,
    "crate": crate,
    "bikerack": bikerack,
    "mirror": mirror,
    "awning": awning,
    "planter": planter,
    "guardrail": guardrail,
    "meter": meter,
    "noren": noren,
    "lantern": lantern,
    "drum": drum,
    "potted": potted,
    "ramen": ramen,
    "postbox": postbox,
    "shutter": shutter,
    "board": board,
    "stonefence": stonefence,
    "bin": bin,
    "lamp": lamp,
    "cone": cone,
    "signal": signal,
    "pole": pole,
    "vending": vending,
    "kanji": kanji,
    "bench": bench,
    "track": track,
    "blockwall": blockwall,
}
