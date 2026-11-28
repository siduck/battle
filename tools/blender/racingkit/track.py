import math

from mathutils import Vector

import arch as a
import ck
import common as c

W = ck.Part


def L():
    return ck.LOD


def pick(a0, a1, a2):
    return (a0, a1, a2)[ck.LOD]


def prismx(profile, x0, x1, col, caps=True, skip=()):
    out = W()
    n = len(profile)
    cy = sum(p[0] for p in profile) / n
    cz = sum(p[1] for p in profile) / n

    for i in range(n):
        if i in skip:
            continue

        p, q = profile[i], profile[(i + 1) % n]
        mid = Vector((0, (p[0] + q[0]) / 2 - cy, (p[1] + q[1]) / 2 - cz))
        nrm = Vector((0, q[1] - p[1], p[0] - q[0]))

        if nrm.dot(mid) < 0:
            nrm.negate()

        out += c.face([(x0, p[0], p[1]), (x1, p[0], p[1]), (x1, q[0], q[1]), (x0, q[0], q[1])], col, nrm)

    if caps:
        out += c.face([(x0, p[0], p[1]) for p in profile], col, (-1, 0, 0))
        out += c.face([(x1, p[0], p[1]) for p in profile], col, (1, 0, 0))

    return out


def tower():
    out = W()
    foot, top = 3.0, 1.95

    def leg(sx, sy, z):
        t = (z - 0.3) / 10.0
        r = foot + (top - foot) * t

        return (sx * r, sy * r, z)

    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))

    for sx, sy in corners:
        out += c.beam(leg(sx, sy, 0.3), leg(sx, sy, 10.3), 0.3, "timber")
        x, y = sx * foot, sy * foot
        out += ck.box(x - 0.36, y - 0.36, 0.0, x + 0.36, y + 0.36, 0.32, "conc_dk", c=0.06, d=1)

    levels = [0.7, 3.9, 7.1, 10.1]

    for i in range(4):
        sa, sb = corners[i], corners[(i + 1) % 4]

        for k, (za, zb) in enumerate(zip(levels, levels[1:])):
            out += c.rod(leg(*sa, za), leg(*sb, zb), pick(0.045, 0.06, 0.08), "shingle_lt", sides=4, d=1)

            if L() == 0:
                out += c.rod(leg(*sb, za), leg(*sa, zb), 0.045, "shingle_lt", sides=4)

            out += c.beam(leg(*sa, zb), leg(*sb, zb), 0.14, "wood_dk", d=1)

    out += ck.cyl((0, 0, 0.0), 0.28, 11.0, "timber", sides=pick(8, 6, 4))
    out += ck.cyl((0, 0, 1.0), 0.36, 0.2, "steel_dk", sides=8, d=0)
    deck = ck.ngon(3.92, pick(12, 10, 8))
    out += c.slabs([(deck, 10.15), (deck, 10.4)], "wood_dk", top="wood", bottom="shingle_lt")
    out += c.ledge(deck, 10.28, 10.46, 0.08, "iron", c=0.03)
    n = len(deck)

    for i in range(n):
        p, q = deck[i], deck[(i + 1) % n]
        out += c.beam((p[0], p[1], 10.4), (p[0], p[1], 11.5), 0.09, "iron", d=1)

        for z in (11.0, 11.48):
            out += c.beam((p[0], p[1], z), (q[0], q[1], z), 0.07, "iron_lt", d=1 if z > 11.2 else 0)

    sides = pick(18, 12, 8)
    out += ck.lathe([(2.55, 10.4, "iron"), (2.95, 11.1, "steel_dk"), (3.0, 12.4, "iron_lt"), (3.08, 12.45, "iron_lt"), (3.08, 12.65, "teal"), (3.0, 12.7, "teal"), (3.0, 15.1, "iron_lt"), (3.08, 15.15, "iron_lt"), (3.08, 15.35, "white"), (3.0, 15.4, "steel"), (3.0, 16.6, "iron_lt"), (3.1, 16.65, "iron_lt"), (3.1, 16.85)], sides, smooth=False)
    out += ck.lathe([(3.45, 16.8, "white_dk"), (3.4, 16.95, "white"), (1.9, 18.05, "white_lt"), (0.35, 19.0, "steel_dk"), (0.3, 19.4, "steel_dk"), (0.4, 19.45, "steel_dk"), (0.12, 20.0)], pick(12, 10, 8), smooth=False)
    out += c.face([(p[0], p[1], 16.8) for p in ck.ngon(3.45, pick(12, 10, 8))], "iron_dk", (0, 0, -1))

    if L() == 0:
        for i in range(12):
            ang = 2 * math.pi * i / 12 + 0.13
            x, y = math.cos(ang) * 3.0, math.sin(ang) * 3.0

            for z in (11.5, 14.0, 16.1):
                out += ck.blob((x, y, z), (0.07, 0.07, 0.07), "steel_dk", sub=0, jitter=0.0)

        out += c.rod((3.92, -0.28, 0.2), (3.92, -0.28, 11.4), 0.035, "iron_lt")
        out += c.rod((3.92, 0.28, 0.2), (3.92, 0.28, 11.4), 0.035, "iron_lt")

        for k in range(30):
            z = 0.5 + k * 0.35
            out += c.rod((3.92, -0.28, z), (3.92, 0.28, z), 0.022, "steel_dk", sides=4)

        for z in (2.5, 6.5, 9.8):
            out += c.beam((3.92, 0.0, z), leg(1, 1, z), 0.06, "iron")

    return out


def stand():
    out = W()
    prof = [(-3.5, 0.0)]

    for k in range(7):
        prof.append((-3.5 + k, 0.45 * (k + 1)))
        prof.append((-2.5 + k, 0.45 * (k + 1)))

    prof[-1] = (3.28, 3.15)
    prof += [(3.28, 3.95), (3.5, 3.95), (3.5, 0.0)]

    for i in range(len(prof) - 1):
        p, q = prof[i], prof[i + 1]
        flat = abs(p[1] - q[1]) < 1e-4
        col = "conc_lt" if flat else "conc"

        out += c.face([(-0.5, p[0], p[1]), (0.5, p[0], p[1]), (0.5, q[0], q[1]), (-0.5, q[0], q[1])], col, (0, -(q[1] - p[1]), q[0] - p[0]))

    for sgn in (-1, 1):
        x = sgn * 0.5

        for k in range(7):
            y0 = -3.5 + k
            y1 = min(y0 + 1.0, 3.28)
            out += c.face([(x, y0, 0.0), (x, y1, 0.0), (x, y1, 0.45 * (k + 1)), (x, y0, 0.45 * (k + 1))], "conc_dk", (sgn, 0, 0))

        out += c.face([(x, 3.28, 0.0), (x, 3.5, 0.0), (x, 3.5, 3.95), (x, 3.28, 3.95)], "conc", (sgn, 0, 0))

    if L() == 0:
        for k in range(7):
            y = -3.5 + k
            z = 0.45 * (k + 1)
            out += c.face([(-0.5, y + 0.02, z + 0.004), (0.5, y + 0.02, z + 0.004), (0.5, y + 0.1, z + 0.004), (-0.5, y + 0.1, z + 0.004)], "mustard" if k == 0 else "off_white", (0, 0, 1), cast=False)

    for k in range(1, 7):
        y = -3.5 + k + 0.75
        z = 0.45 * (k + 1)

        for x in (-0.25, 0.25):
            if L() == 2:
                out += c.plate(x - 0.2, x + 0.2, z + 0.12, z + 0.8, y, "seat")
                out += c.plate(x - 0.2, x + 0.2, z + 0.12, z + 0.8, y + 0.01, "seat_dk", 1)
                continue

            out += ck.box(x - 0.2, y - 0.3, z + 0.28, x + 0.2, y + 0.05, z + 0.36, "seat", d=1)
            out += ck.box(x - 0.2, y, z + 0.32, x + 0.2, y + 0.09, z + 0.8, "seat", c=0.03 if L() == 0 else 0.0, d=1, shear=(0.0, 0.07), skip="d")

            if L() == 0:
                out += ck.box(x - 0.04, y - 0.12, z, x + 0.04, y - 0.04, z + 0.28, "iron_lt", skip="dt")

    out += ck.box(-0.5, 3.26, 3.93, 0.5, 3.5, 4.0, "steel", d=0)
    out += ck.box(-0.11, 3.3, 3.98, 0.11, 3.49, 4.3, "red", c=0.03, d=1)

    return out


def roof():
    out = W()

    for y in (3.18, 3.82):
        out += ck.box(-0.09, y - 0.1, 0.0, 0.09, y + 0.1, 7.1, "iron", c=0.025 if L() == 0 else 0.0, d=2, skip="d")

    n = pick(4, 3, 0)

    for k in range(n):
        z0 = 0.3 + k * 6.6 / n
        z1 = z0 + 6.6 / n
        y0, y1 = (3.25, 3.75) if k % 2 == 0 else (3.75, 3.25)
        out += c.beam((0.0, y0, z0), (0.0, y1, z1), 0.07, "iron_dk")
        out += c.beam((0.0, 3.25, z1), (0.0, 3.75, z1), 0.06, "iron_dk", d=0)

    def under(y):
        return 6.72 + (y + 3.84) / 1.04 * 0.28 if y < -2.8 else 7.0 + (y + 2.8) / 6.76 * 0.14

    def chord(y):
        return 6.6 + (y + 3.6) / 6.7 * -1.05

    panel = [(-3.84, under(-3.84)), (-2.8, 7.0), (3.96, 7.14), (3.96, 7.28), (-2.8, 7.14), (-3.84, 6.84)]
    for i, (p0, p1) in enumerate(zip(panel, panel[1:] + panel[:1])):
        toward = ((0, 0, -1), (0, 0, -1), (0, 1, 0), (0, 0, 1), (0, 0, 1), (0, -1, 0))[i]
        out += c.face([(-0.5, p0[0], p0[1]), (0.5, p0[0], p0[1]), (0.5, p1[0], p1[1]), (-0.5, p1[0], p1[1])], "iron_dk" if i < 2 else "iron", toward)

    for x, s in ((-0.5, -1), (0.5, 1)):
        for i, j in ((0, 1), (1, 2)):
            out += c.face([(x, panel[i][0], panel[i][1]), (x, panel[j][0], panel[j][1]), (x, panel[5 - j][0], panel[5 - j][1]), (x, panel[5 - i][0], panel[5 - i][1])], "iron", (s, 0, 0))

    if L() == 0:
        for x in (-0.46, 0.0, 0.46):
            for ya, yb in ((-3.8, -2.8), (-2.8, 3.9)):
                za = under(ya) + 0.15
                zb = (7.0 if yb == -2.8 else under(yb)) + 0.15
                out += c.beam((x, ya, za), (x, yb, zb), 0.06, "iron")

        for y in (-1.2, 1.2, 3.3):
            out += c.beam((-0.5, y, under(y) - 0.03), (0.5, y, under(y) - 0.03), 0.07, "iron_lt")

    out += c.plate(-0.5, 0.0, 6.68, 6.86, -3.88, "red", d=1)
    out += c.plate(0.0, 0.5, 6.68, 6.86, -3.88, "off_white", d=1)
    out += c.plate(-0.5, 0.5, 6.68, 6.86, -3.865, "iron", 1, d=1)
    out += c.beam((0.0, -3.6, chord(-3.6)), (0.0, 3.1, chord(3.1)), 0.11, "iron", d=2)

    if L() < 2:
        m = pick(5, 3, 0)

        for k in range(m):
            ya = -3.6 + k * 6.7 / m
            yb = ya + 6.7 / m
            ym = (ya + yb) / 2
            out += c.beam((0.0, ya, chord(ya)), (0.0, ym, under(ym)), 0.055, "iron")
            out += c.beam((0.0, ym, under(ym)), (0.0, yb, chord(yb)), 0.055, "iron")

    return out


def billboard():
    out = W()
    out += ck.box(-4.0, -1.0, 3.0, 4.0, -0.82, 6.5, "off_white", c=0.03)
    y = -1.012

    for x0, x1, z0, z1 in ((-4.0, 4.0, 6.34, 6.5), (-4.0, 4.0, 3.0, 3.16), (-4.0, -3.84, 3.16, 6.34), (3.84, 4.0, 3.16, 6.34)):
        out += ck.box(x0, -1.06, z0, x1, -0.99, z1, "steel_lt", c=0.02, d=1, skip="b")

    for (x0, z0, x1, z1, col) in ((-3.2, 5.72, 1.7, 5.46, "teal_dk"), (-2.3, 5.06, 2.7, 4.8, "mustard"), (-1.3, 4.4, 3.35, 4.14, "ranch_red")):
        out += c.face([(x0, y, z0), (x1, y, z1), (x1, y, z1 + 0.34), (x0, y, z0 + 0.34)], col, (0, -1, 0))

    sun = [(-2.75 + math.cos(2 * math.pi * i / 12) * 0.55, 4.22 + math.sin(2 * math.pi * i / 12) * 0.55) for i in range(12)]
    out += c.face([(p[0], y - 0.004, p[1]) for p in sun], "orange", (0, -1, 0))
    out += c.text("NEXT EXIT", 0.2, y - 0.008, 3.4, 0.46, "sign", w=4.2)
    out += c.text("MOTEL", 2.78, y - 0.008, 5.6, 0.5, "ranch_red", w=1.9)
    out += ck.box(-4.15, -1.14, 6.5, 4.15, -0.5, 6.67, "white", c=0.04)

    for x in (-3.55, -1.18, 1.18, 3.55):
        out += ck.box(x - 0.09, -0.8, 0.0, x + 0.09, -0.58, 6.5, "wood", c=0.025 if L() == 0 else 0.0, skip="d")
        out += c.beam((x, 1.68, 0.05), (x, -0.62, 4.5), 0.13, "wood_lt")

        out += c.beam((x, -1.68, 2.86), (x, -0.8, 2.86), 0.1, "wood", d=1)

        if x != 1.18:
            out += c.beam((x, -0.82, 2.0), (x, -1.45, 2.84), 0.08, "wood", d=0)

    for xa, xb in ((-3.55, -1.18), (-1.18, 1.18), (1.18, 3.55)):
        out += c.beam((xa, -0.6, 0.5), (xb, -0.6, 2.8), 0.09, "wood_dk", d=1)
        out += c.beam((xb, -0.6, 0.5), (xa, -0.6, 2.8), 0.09, "wood_dk", d=1)
        out += c.beam((xa, -0.74, 3.3), (xb, -0.74, 6.2), 0.07, "wood_dk", d=0)
        out += c.beam((xb, -0.74, 3.3), (xa, -0.74, 6.2), 0.07, "wood_dk", d=0)

    out += c.plate(-4.0, 4.0, 3.0, 6.5, -0.815, "mortar", 1)
    n = pick(10, 3, 1)

    for k in range(n if L() == 0 else 1):
        if L() == 0:
            y0 = -1.77 + k * 0.075
            out += ck.box(-3.9, y0, 2.9, 3.9, y0 + 0.05, 2.96, "wood_lt" if k % 2 else "wood")
        else:
            out += ck.box(-3.9, -1.77, 2.9, 3.9, -1.0, 2.96, "wood_lt")

    for x in (-3.9, -1.95, 0.0, 1.95, 3.9):
        out += c.beam((x, -1.72, 2.92), (x, -1.72, 3.72), 0.06, "steel", d=1)

    for z in (3.32, 3.7):
        out += c.beam((-3.93, -1.72, z), (3.93, -1.72, z), 0.05, "steel_lt", d=1)

    for x in (-2.6, 0.0, 2.6):
        out += c.beam((x, -1.12, 6.62), (x, -1.62, 6.52), 0.04, "iron", d=0)
        out += ck.box(x - 0.16, -1.74, 6.42, x + 0.16, -1.56, 6.54, "iron_lt", c=0.025, d=0)

    return out


def pylon():
    out = W()
    out += ck.box(-0.6, -0.6, 0.0, 0.6, 0.6, 0.2, "iron_lt", c=0.05)
    out += ck.box(-0.5, -0.5, 0.2, 0.5, 0.5, 0.38, "steel_dk", c=0.05, d=1)
    out += ck.box(-0.26, -0.2, 0.36, 0.26, 0.16, 0.95, "rust_dk", c=0.04, taper=(1.12, 1.0))
    out += ck.box(-0.29, -0.2, 0.95, 0.29, 0.14, 4.18, "white", c=0.05, taper=(1.9, 1.0))

    for z in (2.095, 2.745, 3.395):
        out += ck.box(-0.82, -0.28, z, 0.82, 0.18, z + 0.565, "tan", c=0.06)
        out += c.plate(-0.75, 0.75, z + 0.06, z + 0.505, -0.287, "ranch_red")
        out += c.plate(-0.7, 0.7, z + 0.1, z + 0.465, -0.293, "white_lt")

    for z, a0 in ((3.395, "GAS"), (2.745, "OIL"), (2.095, "EATS")):
        out += c.text(a0, 0.0, -0.302, z + 0.14, 0.29, "sign", w=1.2)

    def arch(w, z0, zs, z1, n):
        pts = [(-w, z0), (w, z0)]

        for i in range(n + 1):
            t = math.pi * i / n
            pts.append((w * math.copysign(abs(math.cos(t)) ** 0.5, math.cos(t)), zs + (z1 - zs) * math.sin(t) ** 0.7))

        return pts

    n = pick(10, 6, 4)
    out += ck.extrude(arch(0.86, 4.14, 5.25, 6.0, n), -0.28, 0.19, "teal", force=True)
    out += ck.extrude(arch(0.77, 4.23, 5.22, 5.91, n), -0.295, -0.28, "white_lt", force=True, caps="f")
    out += ck.extrude(arch(0.69, 4.31, 5.2, 5.83, n), -0.31, -0.295, "teal_dk", force=True, caps="f")
    star = []

    for i in range(10):
        r = 0.34 if i % 2 == 0 else 0.15
        t = math.pi / 2 + i * math.pi / 5
        star.append((math.cos(t) * r, 5.2 + math.sin(t) * r))

    out += c.face([(p[0], -0.318, p[1]) for p in star], "mustard", (0, -1, 0))
    out += c.text("STOP", 0.0, -0.318, 4.48, 0.3, "white_lt")

    for z, a0 in ((3.395, "GAS"), (2.745, "OIL"), (2.095, "EATS")):
        out += c.plate(-0.75, 0.75, z + 0.06, z + 0.505, 0.187, "ranch_red", 1)
        out += c.plate(-0.7, 0.7, z + 0.1, z + 0.465, 0.193, "white_lt", 1)
        out += c.text(a0, 0.0, -0.002, z + 0.14, 0.29, "sign", w=1.2).rot(180).move(y=0.201)

    out += ck.extrude(arch(0.77, 4.23, 5.22, 5.91, n), 0.19, 0.205, "white_lt", force=True, caps="b")
    out += ck.extrude(arch(0.69, 4.31, 5.2, 5.83, n), 0.205, 0.22, "teal_dk", force=True, caps="b")
    out += c.face([(p[0], 0.228, p[1]) for p in star], "mustard", (0, 1, 0))
    out += c.text("STOP", 0.0, -0.002, 4.48, 0.3, "white_lt").rot(180).move(y=0.228)

    return out


def dsign():
    out = W()
    out += ck.box(-0.72, -0.32, 0.0, 0.79, 0.32, 0.12, "steel", c=0.03)
    out += ck.box(-0.6, -0.25, 0.12, 0.65, 0.25, 0.21, "steel_dk", c=0.025, d=1)

    for x in (-0.51, 0.58):
        out += ck.cyl((x, 0.01, 0.1), 0.075, 3.8, "iron", sides=pick(10, 6, 4))

    arrow = [(-1.45, 4.03), (-1.45, 2.78), (-1.22, 2.55), (0.85, 2.55), (0.85, 2.42), (1.45, 2.76), (1.0, 3.12), (0.95, 2.92), (-1.05, 2.92), (-1.05, 4.0), (-1.16, 3.9), (-1.25, 4.03), (-1.34, 3.9)]
    out += ck.extrude(arrow, -0.26, -0.1, "orange", force=True)
    inner = [(-1.35, 3.78), (-1.35, 2.82), (-1.18, 2.65), (0.98, 2.65), (1.0, 2.62), (1.28, 2.77), (1.05, 2.96), (1.0, 2.82), (-1.15, 2.82), (-1.15, 3.78)]
    out += c.face([(p[0], -0.268, p[1]) for p in inner], "rust_dk", (0, -1, 0))
    dots = [(-1.25, 3.7 - k * 0.22) for k in range(5)] + [(-1.1 + k * 0.24, 2.735) for k in range(9)]
    out += c.bulbs(dots, -0.276, 0.05, "lamp_glass")
    out += ck.box(-0.95, -0.24, 3.03, 1.03, 0.06, 3.86, "lamp_teal", c=0.09)
    out += c.plate(-0.84, 0.92, 3.12, 3.77, -0.248, "sign")
    out += c.text("EATS", 0.04, -0.256, 3.24, 0.42, "mustard", t=0.07)
    out += c.plate(-0.84, 0.92, 3.12, 3.77, 0.066, "sign", 1)
    word = c.text("EATS", -0.04, -0.03, 3.24, 0.42, "mustard", t=0.07).rot(180)
    out += word.move(y=0.044)
    out += ck.box(-0.64, -0.13, 3.83, 0.69, 0.1, 4.16, "lamp_teal", c=0.07)
    out += c.plate(-0.55, 0.6, 3.9, 4.09, -0.138, "awn_blue")
    out += c.text("OPEN", 0.025, -0.146, 3.93, 0.13, "off_white")

    for z in (3.22, 3.66):
        out += c.beam((-0.55, 0.02, z), (0.62, 0.02, z), 0.07, "steel_lt", d=0)

    return out


def camtower():
    out = W()

    for x in (-1.28, 1.28):
        for y in (-1.18, 1.18):
            out += ck.cyl((x, y, 0.0), 0.07, 5.9, "iron_lt", sides=pick(8, 5, 4))
            out += ck.box(x - 0.12, y - 0.12, 0.0, x + 0.12, y + 0.12, 0.06, "iron", d=0)
            out += c.beam((x, y, 5.9), (x, y, 6.94), 0.08, "steel", d=1)

    levels = [0.25, 1.9, 3.9, 5.7]
    sides = (((-1.28, -1.18), (1.28, -1.18)), ((1.28, -1.18), (1.28, 1.18)), ((1.28, 1.18), (-1.28, 1.18)), ((-1.28, 1.18), (-1.28, -1.18)))

    for i, (p, q) in enumerate(sides):
        for k, (za, zb) in enumerate(zip(levels, levels[1:])):
            out += c.rod((p[0], p[1], za), (q[0], q[1], zb), pick(0.035, 0.045, 0.05), "steel", sides=4, d=1)

            if L() == 0:
                out += c.rod((q[0], q[1], za), (p[0], p[1], zb), 0.035, "steel", sides=4)

            out += c.beam((p[0], p[1], zb), (q[0], q[1], zb), 0.07, "iron_lt", d=1)

        for z in (6.45, 6.93):
            out += c.beam((p[0], p[1], z), (q[0], q[1], z), 0.07, "steel_lt", d=1)

    for k in range(pick(8, 1, 1)):
        w = 2.8 / pick(8, 1, 1)
        x0 = -1.4 + k * w
        out += ck.box(x0, -1.3, 5.82, x0 + w - 0.02, 1.3, 5.98, "wood_trim" if k % 2 == 0 else "tan_dk", c=0.015)

    for sx in (-1, 1):
        x = sx * 1.34
        m = pick(5, 1, 1)

        for k in range(m):
            w = 2.36 / m
            y0 = -1.18 + k * w
            xa = x + (sx * (0.03 if k % 2 else -0.005) if m > 1 else 0.0)
            xb = x + (sx * (-0.005 if k % 2 else 0.03) if m > 1 else 0.0)
            out += c.face([(xa, y0, 2.6), (xb, y0 + w, 2.6), (xb, y0 + w, 5.25), (xa, y0, 5.25)], "cam_blue" if k % 2 == 0 else "cam_blue_dk", (sx, 0, 0))

        out += c.face([(x - sx * 0.02, -1.18, 2.6), (x - sx * 0.02, 1.18, 2.6), (x - sx * 0.02, 1.18, 5.25), (x - sx * 0.02, -1.18, 5.25)], "cam_blue_dk", (-sx, 0, 0))

    for k in range(pick(5, 1, 1)):
        w = 2.36 / pick(5, 1, 1)
        x0 = -1.18 + k * w
        out += c.face([(x0, 1.25, 2.6), (x0 + w, 1.25, 2.6), (x0 + w, 1.25, 5.25), (x0, 1.25, 5.25)], "cam_blue" if k % 2 == 0 else "cam_blue_dk", (0, 1, 0))

    out += c.face([(-1.18, 1.23, 2.6), (1.18, 1.23, 2.6), (1.18, 1.23, 5.25), (-1.18, 1.23, 5.25)], "cam_blue_dk", (0, -1, 0))
    out += c.plate(-0.7, 0.7, 3.5, 4.4, 1.262, "off_white", 1, d=1)
    out += c.text("LIVE", 0.0, -0.02, 3.72, 0.45, "red_dk").rot(180).move(y=1.25)

    for x in (-1.22, -0.8):
        out += c.beam((x, -1.34, 0.02), (x, -1.34, 5.95), 0.06, "steel_lt", d=1)

    for k in range(pick(19, 6, 0)):
        z = 0.28 + k * pick(0.31, 0.95, 1.0)
        out += c.beam((-1.22, -1.34, z), (-0.8, -1.34, z), 0.04, "steel")

    out += ck.box(0.2, -0.3, 5.98, 0.62, 0.1, 6.2, "iron_dk", c=0.04, d=1)
    out += ck.box(0.28, -0.62, 6.28, 0.54, -0.1, 6.52, "iron", c=0.05, d=1)
    out += ck.cyl((0.41, -0.2, 6.0), 0.045, 0.3, "iron_lt", sides=6, d=0)
    out += c.rod((-1.34, -0.9, 5.2), (-1.36, -1.0, 0.1), 0.025, "iron_dk", d=0)

    for z in (1.2, 3.2, 4.4):
        out += ck.box(-1.39, -1.03, z, -1.31, -0.95, z + 0.12, "red", d=0)

    return out


def shade():
    out = W()
    tops = {(-1, -1): 5.9, (1, 1): 5.9, (-1, 1): 4.78, (1, -1): 4.78}
    hold = {}

    for (sx, sy), h in tops.items():
        foot = (sx * 4.0, sy * 4.0, 0.12)
        tip = (sx * 4.66, sy * 4.66, h - 0.04)
        out += c.rod(foot, tip, 0.12, "steel", sides=pick(8, 5, 4), caps=(True, True))
        out += ck.box(sx * 4.0 - 0.38, sy * 4.0 - 0.38, 0.0, sx * 4.0 + 0.38, sy * 4.0 + 0.38, 0.2, "conc_lt", c=0.05, d=1)
        hold[(sx, sy)] = tip

    zc = {(-1, -1): 5.45, (1, -1): 4.45, (1, 1): 5.45, (-1, 1): 4.45}
    n = pick(8, 5, 3)

    def at(u, v):
        pinch_u = 1.0 - 0.17 * (1 - (2 * v - 1) ** 2)
        pinch_v = 1.0 - 0.17 * (1 - (2 * u - 1) ** 2)
        x = (2 * u - 1) * 3.75 * pinch_u
        y = (2 * v - 1) * 3.75 * pinch_v
        z = (zc[(-1, -1)] * (1 - u) * (1 - v) + zc[(1, -1)] * u * (1 - v) + zc[(1, 1)] * u * v + zc[(-1, 1)] * (1 - u) * v)
        z -= 0.35 * math.sin(math.pi * u) * math.sin(math.pi * v)

        return (x, y, z)

    for i in range(n):
        for j in range(n):
            q = [at(i / n, j / n), at((i + 1) / n, j / n), at((i + 1) / n, (j + 1) / n), at(i / n, (j + 1) / n)]
            col = "off_white" if (i * 8 // n) % 4 < 2 else "canvas"

            for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                out.append(ck.Poly(list(tri), col, True, False, True))
                low = [(p[0], p[1], p[2] - 0.03) for p in reversed(tri)]
                out.append(ck.Poly(low, "white_dk", True, False, False))

    if L() == 0:
        for i in range(n):
            for p, q in ((at(i / n, 0), at((i + 1) / n, 0)), (at(i / n, 1), at((i + 1) / n, 1)), (at(0, i / n), at(0, (i + 1) / n)), (at(1, i / n), at(1, (i + 1) / n))):
                out += c.rod(p, q, 0.035, "steel_dk", sides=4)

    for (sx, sy), tip in hold.items():
        corner = at(0 if sx < 0 else 1, 0 if sy < 0 else 1)
        out += c.rod(corner, tip, 0.025, "iron", sides=4, d=1)

    return out


def waving(x0, x1, z0, z1, nx, nz, wave, colour, y=0.0):
    out = W()

    def at(i, k):
        u = i / nx
        v = k / nz

        return (x0 + (x1 - x0) * u, y + math.sin(u * math.pi * 2.2) * wave * u, z0 + (z1 - z0) * v - 0.07 * u * u)

    for i in range(nx):
        for k in range(nz):
            q = [at(i, k), at(i + 1, k), at(i + 1, k + 1), at(i, k + 1)]
            col = colour(i, k)
            out.append(ck.Poly(q, col, False, False, True))
            out.append(ck.Poly([(p[0], p[1] + 0.006, p[2]) for p in reversed(q)], col, False, False, False))

    return out


def redflag():
    out = W()
    px = -0.55
    out += ck.box(px - 0.6, -0.6, 0.0, px + 0.6, 0.6, 0.17, "white", c=0.04)
    out += ck.box(px - 0.48, -0.48, 0.17, px + 0.48, 0.48, 0.29, "white_lt", c=0.03, d=1)
    out += ck.lathe([(0.2, 0.29, "steel"), (0.19, 0.5, "white_lt"), (0.15, 0.6, "white_lt"), (0.12, 3.0, "steel_dk"), (0.14, 3.1, "white_lt"), (0.075, 7.2)], pick(8, 5, 4), (px, 0, 0), smooth=False)
    out += ck.blob((px, 0, 7.32), (0.16, 0.16, 0.16), ("gold", "gold", "tan_dk"), sub=1 if L() == 0 else 0, jitter=0.0)
    out += waving(px + 0.07, 1.15, 5.95, 7.12, pick(8, 4, 2), 1, 0.14, lambda i, k: "red")

    if L() < 2:
        out += waving(px + 0.07, px + 0.2, 5.95, 7.1, 1, 1, 0.0, lambda i, k: "off_white", y=-0.012)

    out += c.rod((px + 0.04, -0.13, 1.45), (px + 0.02, -0.13, 7.05), 0.012, "tan", sides=3, d=0)
    out += ck.box(px - 0.1, -0.2, 1.4, px + 0.1, -0.1, 1.47, "iron_lt", d=0)

    return out


def flag():
    out = W()
    px = -0.53
    out += ck.cyl((px, 0, 0.0), 0.035, 2.5, "steel", sides=pick(7, 4, 3))
    out += ck.cyl((px, 0, 0.0), 0.047, 0.08, "iron_lt", sides=6, d=0)
    out += ck.blob((px, 0, 2.54), (0.05, 0.05, 0.05), "steel_lt", sub=0, jitter=0.0)
    nx, nz = pick((8, 5), (8, 5), (4, 3))
    out += waving(px + 0.03, 0.58, 1.74, 2.46, nx, nz, 0.075, lambda i, k: "black" if (i + k) % 2 == 0 else "off_white")

    return out


def rail():
    out = W()
    prof = [(-0.1, 0.44), (-0.17, 0.5), (-0.105, 0.58), (-0.105, 0.66), (-0.17, 0.74), (-0.1, 0.8)]

    if L() == 2:
        prof = [(-0.14, 0.44), (-0.14, 0.8)]

    for i in range(len(prof) - 1):
        p, q = prof[i], prof[i + 1]
        col = "steel_lt" if i % 2 == 0 else "steel"
        out += c.face([(-2.0, p[0], p[1]), (2.0, p[0], p[1]), (2.0, q[0], q[1]), (-2.0, q[0], q[1])], col, (0, -1, 0))

    out += c.face([(-2.0, -0.09, 0.44), (2.0, -0.09, 0.44), (2.0, -0.09, 0.8), (-2.0, -0.09, 0.8)], "steel_dk", (0, 1, 0))
    out += c.face([(-2.0, -0.1, 0.8), (2.0, -0.1, 0.8), (2.0, -0.088, 0.8), (-2.0, -0.088, 0.8)], "steel_lt", (0, 0, 1))

    for x in (-1.38, 1.38):
        out += ck.box(x - 0.08, 0.04, 0.0, x + 0.08, 0.17, 0.74, "iron_lt", d=2, skip="d")
        out += ck.box(x - 0.1, -0.09, 0.52, x + 0.1, 0.04, 0.72, "iron", d=0, skip="fb")

        if L() == 0:
            out += ck.box(x - 0.03, -0.12, 0.6, x + 0.03, -0.105, 0.64, "iron_dk", skip="b")

    for x in (-0.9, 0.9):
        out += c.plate(x - 0.21, x + 0.21, 0.575, 0.665, -0.112, "orange", d=0)

    return out


def fence():
    out = W()
    n = pick(11, 11, 3)
    w = 1.6 / n

    for i in range(n):
        x0, x1 = -0.8 + i * w, -0.8 + (i + 1) * w
        col = "off_white" if i % 2 == 0 else "awn_rust"
        out += c.plate(x0, x1, 0.27, 1.0, -0.02, col)
        out += c.plate(x0, x1, 0.27, 1.0, 0.02, col, 1)

    out += c.face([(-0.8, -0.03, 1.0), (0.8, -0.03, 1.0), (0.8, 0.03, 1.0), (-0.8, 0.03, 1.0)], "iron_dk", (0, 0, 1))

    for s in (-1, 1):
        x = s * 0.86
        out += ck.cyl((x, 0, 0.04), 0.045, 0.98, "iron_dk", sides=pick(6, 4, 3))

        if L() < 2:
            out += ck.cyl((x, 0, 1.0), 0.056, 0.05, "iron", sides=6 if L() == 0 else 4)
            out += ck.cyl((x, 0, 0.0), 0.14, 0.04, "iron_dk", sides=7 if L() == 0 else 4)

    for y in (-0.042, 0.042):
        out += ck.box(-0.84, y - 0.014, 0.62, 0.84, y + 0.014, 0.67, "iron_dk", d=0, skip="lr")

    out += ck.box(-0.84, -0.014, 0.25, 0.84, 0.014, 0.285, "iron_dk", d=0, skip="lr")

    return out


def jersey():
    out = W()

    for i in range(2):
        x0, x1 = -1.98 + i * 2.0, -0.02 + i * 2.0
        col = "conc" if i == 0 else "conc_lt"
        prof = [(-0.32, 0.0), (0.32, 0.0), (0.32, 0.18), (0.19, 0.34), (0.12, 0.85), (-0.12, 0.85), (-0.19, 0.34), (-0.32, 0.18)]

        if L() == 2:
            prof = [(-0.32, 0.0), (0.32, 0.0), (0.12, 0.85), (-0.12, 0.85)]

        out += prismx(prof, x0, x1, col, skip=(0,))

        for s in (-1, 1):
            def y(z):
                return s * (0.19 - (z - 0.34) / 0.51 * 0.07 + 0.006)

            for xa, xb, cc in ((x0 + 0.28, x0 + 0.9, "red"), (x0 + 1.06, x0 + 1.68, "off_white")):
                out += c.face([(xa, y(0.5), 0.5), (xb, y(0.5), 0.5), (xb, y(0.72), 0.72), (xa, y(0.72), 0.72)], cc, (0, s, 0.1))

        if L() == 0:
            out += ck.box(x0 + 0.4, -0.06, 0.85, x0 + 0.52, 0.06, 0.862, "conc_dk")
            out += ck.box(x1 - 0.52, -0.06, 0.85, x1 - 0.4, 0.06, 0.862, "conc_dk")

            for s in (-1, 1):
                out += c.face([(x0 + 0.5, s * 0.322, 0.01), (x0 + 0.85, s * 0.322, 0.01), (x0 + 0.78, s * 0.322, 0.11), (x0 + 0.58, s * 0.322, 0.11)], "conc_dk", (0, s, 0), cast=False)
                out += c.face([(x1 - 0.85, s * 0.322, 0.01), (x1 - 0.5, s * 0.322, 0.01), (x1 - 0.58, s * 0.322, 0.11), (x1 - 0.78, s * 0.322, 0.11)], "conc_dk", (0, s, 0), cast=False)

    return out


def ring(cx, cy, z, profile, n, cols, phase=0.0):
    out = W()

    for k in range(len(profile) - 1):
        r0, z0 = profile[k]
        r1, z1 = profile[k + 1]

        for i in range(n):
            a0 = 2 * math.pi * i / n + phase
            a1 = 2 * math.pi * (i + 1) / n + phase
            pts = [(cx + math.cos(a0) * r0, cy + math.sin(a0) * r0, z + z0), (cx + math.cos(a1) * r0, cy + math.sin(a1) * r0, z + z0), (cx + math.cos(a1) * r1, cy + math.sin(a1) * r1, z + z1), (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1, z + z1)]
            out.append(ck.Poly(pts, cols[k]))

    return out


def tyrewall():
    out = W()

    if L() == 2:
        for k in range(3):
            if k < 2:
                out += ck.box(-1.98, -0.36, k * 0.29, 1.98, 0.36, k * 0.29 + 0.29, "rubber" if k else "rubber_dk", skip="d")
            else:
                for i in range(5):
                    out += ck.box(-1.98 + i * 0.8, -0.36, 0.58, -1.22 + i * 0.8, 0.36, 0.88, "red" if i % 2 == 0 else "off_white", skip="d")
    else:
        n = 8
        ph = math.pi / 8

        for i in range(5):
            x = -1.6 + i * 0.8

            for k in range(3):
                z = k * 0.292
                col = ("red" if i % 2 == 0 else "off_white") if k == 2 else ("rubber_dk" if k == 0 else "rubber")

                if L() == 1:
                    out += ring(x, 0.0, z, [(0.39, 0.02), (0.39, 0.27)], n, [col], ph)
                else:
                    out += ring(x, 0.0, z, [(0.34, 0.0), (0.395, 0.07), (0.395, 0.21), (0.34, 0.28)], n, [col, col, col], ph)

            out += ring(x, 0.0, 0.584, [(0.34 if L() == 0 else 0.39, 0.28 if L() == 0 else 0.27), (0.2, 0.29)], n, ["red" if i % 2 == 0 else "off_white"], ph)
            out += ring(x, 0.0, 0.584, [(0.2, 0.29), (0.17, 0.12)], n, ["black"], ph)
            out += c.face([(x + math.cos(2 * math.pi * j / n + ph) * 0.17, math.sin(2 * math.pi * j / n + ph) * 0.17, 0.705) for j in range(n)], "black", (0, 0, 1))

    out += ck.box(-2.0, 0.36, 0.05, 2.0, 0.42, 0.85, "seat", d=2)

    for x in (-1.7, 0.0, 1.7):
        out += ck.box(x - 0.05, 0.4, 0.0, x + 0.05, 0.435, 0.88, "steel_dk", d=0)

    return out


def tyres():
    out = W()
    offs = ((0.0, 0.0, 0.0), (0.012, -0.008, 0.31), (-0.012, 0.006, 0.16), (0.006, 0.01, 0.42))

    if L() == 2:
        out += ring(0.0, 0.0, 0.0, [(0.42, 0.0), (0.44, 0.48), (0.42, 0.92)], 7, ["rubber_dk", "rubber"])
        out += c.face([(math.cos(2 * math.pi * j / 7) * 0.42, math.sin(2 * math.pi * j / 7) * 0.42, 0.92) for j in range(7)], "dust_rubber", (0, 0, 1))
        out += c.face([(math.cos(2 * math.pi * j / 7) * 0.2, math.sin(2 * math.pi * j / 7) * 0.2, 0.923) for j in range(7)], "black", (0, 0, 1))

        return out

    n = 10 if L() == 0 else 8

    for k in range(4):
        ox, oy, ph = offs[k]
        z = k * 0.237
        body = "rubber" if k % 2 else "rubber_lt"

        if L() == 0:
            out += ring(ox, oy, z, [(0.31, 0.0), (0.405, 0.03), (0.42, 0.12), (0.405, 0.205), (0.31, 0.237)], n, ["rubber_dk", body, body, "rubber_dk"], ph)

            for i in range(n):
                ang = 2 * math.pi * (i + 0.5) / n + ph
                u = Vector((math.cos(ang), math.sin(ang), 0))
                t = Vector((-u.y, u.x, 0))
                base = Vector((ox, oy, z))

                def p(r, s, h):
                    v = base + u * r + t * s

                    return (v.x, v.y, v.z + h)

                outer = [p(0.445, -0.085, 0.055), p(0.445, 0.085, 0.055), p(0.445, 0.085, 0.185), p(0.445, -0.085, 0.185)]
                inner = [p(0.39, -0.1, 0.035), p(0.39, 0.1, 0.035), p(0.39, 0.1, 0.205), p(0.39, -0.1, 0.205)]
                out += c.face(outer, body, u)

                for j, nrm in ((0, Vector((0, 0, -1))), (1, t), (2, Vector((0, 0, 1))), (3, -t)):
                    m = (j + 1) % 4
                    out += c.face([inner[j], inner[m], outer[m], outer[j]], body, nrm + u * 0.3)
        else:
            out += ring(ox, oy, z, [(0.36, 0.0), (0.43, 0.06), (0.43, 0.18), (0.36, 0.237)], n, ["rubber_dk", body, "rubber_dk"], ph)

    ox, oy, ph = offs[3]
    z = 3 * 0.237
    r0 = 0.31 if L() == 0 else 0.36
    out += ring(ox, oy, z, [(r0, 0.237), (0.27, 0.247), (0.21, 0.235)], n, ["dust_rubber", "rubber_lt"], ph)
    out += ring(ox, oy, z, [(0.21, 0.235), (0.19, 0.02)], n, ["black"], ph)
    out += c.face([(ox + math.cos(2 * math.pi * j / n + ph) * 0.19, oy + math.sin(2 * math.pi * j / n + ph) * 0.19, z + 0.02) for j in range(n)], "black", (0, 0, 1))

    return out


def kerb():
    out = W()

    for i in range(4):
        x0, x1 = -2.0 + i, -1.0 + i
        col = "red" if i % 2 == 0 else "off_white"
        prof = [(-0.6, -0.3), (-0.6, 0.04), (-0.5, 0.08), (0.5, 0.08), (0.6, 0.04), (0.6, -0.3)]

        if L() > 0:
            prof = [(-0.6, -0.3), (-0.6, 0.07), (0.6, 0.07), (0.6, -0.3)]

        out += prismx(prof, x0, x1, col, caps=False, skip=(len(prof) - 1,))

    for x, s, col in ((-2.0, -1, "red"), (2.0, 1, "off_white")):
        out += c.face([(x, -0.6, -0.3), (x, -0.6, 0.04), (x, -0.5, 0.08), (x, 0.5, 0.08), (x, 0.6, 0.04), (x, 0.6, -0.3)], col, (s, 0, 0))

    return out


def curb():
    out = W()

    for i in range(pick(4, 1, 1)):
        w = 4.0 / pick(4, 1, 1)
        x0 = -2.0 + i * w
        x1 = x0 + w - (0.025 if L() == 0 else 0.0)
        col = "conc_lt" if i % 2 == 0 else "conc"
        prof = [(-0.2, -0.6), (-0.2, 0.08), (-0.22, 0.1), (-0.22, 0.15), (-0.18, 0.18), (0.18, 0.18), (0.22, 0.15), (0.22, 0.1), (0.2, 0.08), (0.2, -0.6)]

        if L() > 0:
            prof = [(-0.21, -0.6), (-0.21, 0.18), (0.21, 0.18), (0.21, -0.6)]

        out += prismx(prof, x0, x1, col, caps=True, skip=(len(prof) - 1,))

    if L() == 0:
        out += prismx([(-0.19, -0.6), (-0.19, 0.14), (0.19, 0.14), (0.19, -0.6)], -1.99, 1.99, "joint", caps=False, skip=(3,))

    return out


def line():
    out = W()
    pts = [(-1.2, -0.065), (-1.14, -0.08), (1.17, -0.08), (1.2, -0.04), (1.19, 0.07), (1.13, 0.08), (-1.17, 0.08), (-1.2, 0.04)]

    if L() > 0:
        pts = [(-1.2, -0.08), (1.2, -0.08), (1.2, 0.08), (-1.2, 0.08)]

    out += c.face([(p[0], p[1], 0.02) for p in pts], "off_white", (0, 0, 1), ao=False)

    return out


def start():
    out = W()

    for i in range(14):
        for j in range(2):
            col = "off_white" if (i + j) % 2 == 0 else "black"
            out += c.face([(-7.0 + i, -1.0 + j, 0.02), (-6.0 + i, -1.0 + j, 0.02), (-6.0 + i, j, 0.02), (-7.0 + i, j, 0.02)], col, (0, 0, 1), ao=False)

    return out


def lift():
    out = W()

    for s in (-1, 1):
        x0, x1 = sorted((s * 0.84, s * 1.45))
        out += ck.box(x0, -2.4, 0.9, x1, 2.4, 0.98, "iron_lt", d=2)

        for x in (x0, x1):
            out += ck.box(x - 0.035, -2.4, 0.86, x + 0.035, 2.4, 1.1, "iron", c=0.015 if L() == 0 else 0.0, d=1)

        for e in (-1, 1):
            out += prismx([(e * 2.4, 0.9), (e * 2.4, 0.98), (e * 2.667, 1.12), (e * 2.667, 1.06)], x0 - 0.03, x1 + 0.03, "steel_dk")

        if L() == 0:
            for k in range(11):
                y = -2.1 + k * 0.42
                out += ck.box(x0 + 0.07, y, 0.98, x1 - 0.07, y + 0.07, 1.0, "steel_dk", skip="d")

            out += c.plate(x0, x1, 0.87, 0.91, -2.401, "mustard")

    out += ck.cyl((-0.3, 0, 0.0), 0.5, 0.14, "steel_dk", sides=pick(14, 8, 6))
    out += ck.cyl((-0.3, 0, 0.14), 0.36, 0.05, "iron", sides=pick(12, 8, 5), d=1)
    out += ck.cyl((-0.28, 0, 0.14), 0.13, 0.46, "iron_lt", sides=pick(10, 6, 4))
    out += ck.cyl((-0.28, 0, 0.6), 0.09, 0.36, "steel_lt", sides=pick(10, 6, 4))
    out += ck.box(-0.84, -0.25, 0.9, 0.84, 0.25, 1.03, "iron", c=0.03 if L() == 0 else 0.0)
    out += ck.box(-0.84, -0.14, 1.03, 0.25, 0.14, 1.07, "iron_dk", d=0)
    out += ck.box(0.52, -0.8, 0.0, 0.76, -0.56, 0.06, "iron_dk", d=1)
    out += ck.cyl((0.64, -0.68, 0.0), 0.055, 1.28, "iron", sides=pick(8, 5, 4))
    out += ck.box(0.55, -0.77, 1.18, 0.73, -0.59, 1.36, "steel_dk", c=0.04, d=1)
    out += c.rod((0.64, -0.68, 1.34), (0.74, -0.72, 1.48), 0.022, "steel", d=0)
    out += ck.blob((0.75, -0.72, 1.49), (0.05, 0.05, 0.05), "red", sub=0, jitter=0.0)
    out += c.rod((0.58, -0.68, 0.1), (-0.15, -0.2, 0.1), 0.025, "iron_dk", d=0)

    return out


LOW = {"errors": (0.012, 0.05)}
ALL = {
    "tower": (tower, {"errors": (0.025, 0.1)}),
    "stand": (stand, {"errors": (0.012, 0.045), "ao": 0.45}),
    "roof": (roof, {"errors": (0.012, 0.045)}),
    "billboard": (billboard, {"errors": (0.015, 0.07)}),
    "pylon": (pylon, LOW),
    "dsign": (dsign, LOW),
    "camtower": (camtower, {"errors": (0.015, 0.06)}),
    "shade": (shade, LOW),
    "redflag": (redflag, LOW),
    "flag": (flag, {"errors": (0.012, 0.04), "ao": 0.25}),
    "rail": (rail, {"errors": (0.008, 0.035)}),
    "fence": (fence, {"errors": (0.008, 0.03), "ao": 0.4}),
    "jersey": (jersey, {"errors": (0.008, 0.04)}),
    "tyrewall": (tyrewall, {"errors": (0.008, 0.035)}),
    "tyres": (tyres, {"errors": (0.006, 0.028)}),
    "kerb": (kerb, {"errors": (0.008,), "ao": 0.0, "grime": 0.0, "speckle": 0.0}),
    "curb": (curb, {"errors": (0.008,), "ao": 0.2, "grime": 0.0}),
    "line": (line, {"lods": False, "ao": 0.0, "grime": 0.0, "speckle": 0.0}),
    "start": (start, {"lods": False, "ao": 0.0, "grime": 0.0, "speckle": 0.0}),
    "lift": (lift, LOW),
}
