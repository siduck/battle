import math

from mathutils import Vector

import ck
import common as c
from track import pick, prismx

W = ck.Part


def L():
    return ck.LOD


def disc(x, z, r, y, col, facing=-1, n=None, squash=1.0):
    n = n or pick(12, 8, 6)
    pts = [(x + math.cos(2 * math.pi * i / n) * r, y, z + math.sin(2 * math.pi * i / n) * r * squash) for i in range(n)]

    return c.face(pts, col, (0, facing, 0))


def pump():
    out = W()
    cx = -0.055
    out += ck.box(-0.43, -0.277, 0.0, 0.33, 0.277, 0.08, "iron", c=0.025)

    def shell(w, z0, zs, z1, n):
        pts = [(cx - w, z0), (cx + w, z0)]

        for i in range(n + 1):
            t = math.pi * i / n
            pts.append((cx + w * math.copysign(abs(math.cos(t)) ** 0.6, math.cos(t)), zs + (z1 - zs) * math.sin(t) ** 0.8))

        return pts

    n = pick(10, 5, 3)
    out += ck.extrude(shell(0.39, 0.07, 1.5, 1.72, n), -0.21, 0.21, "pump", force=True)

    for y0, y1, caps in ((-0.232, -0.21, "f"), (0.21, 0.232, "b")):
        out += ck.extrude(shell(0.325, 0.12, 1.46, 1.65, n), y0, y1, "steel_lt", force=True, caps=caps)
        yy = y0 - 0.006 if caps == "f" else y1 + 0.006
        face = -1 if caps == "f" else 1
        out += c.plate(cx - 0.27, cx + 0.27, 0.17, 0.82, yy, "pump", face)

        if L() < 2:
            out += disc(cx, 1.2, 0.22, yy, "iron_lt", face)
            out += disc(cx, 1.2, 0.18, yy + face * 0.006, "off_white", face)
            out += c.plate(cx - 0.17, cx + 0.15, 0.4, 0.66, yy + face * 0.006, "off_white", face, d=0)

    out += c.stroke((cx, 1.2), (cx + 0.11, 1.3), -0.254, 0.022, "sign") if L() == 0 else W()
    out += c.text("27", cx - 0.01, -0.254, 0.46, 0.14, "sign") if L() == 0 else W()
    out += ck.cyl((cx, 0, 1.68), 0.09, 0.12, "steel", sides=pick(8, 5, 4), d=1)
    n = pick(14, 9, 7)
    ring = [(cx + math.cos(2 * math.pi * i / n) * 0.245, 2.015 + math.sin(2 * math.pi * i / n) * 0.245) for i in range(n)]
    out += ck.extrude(ring, -0.11, 0.11, "off_white", force=True)

    for face, y in ((-1, -0.118), (1, 0.118)):
        out += disc(cx, 2.015, 0.19, y, "orange", face, n)

        if L() == 0:
            word = c.text("GAS", 0.0, -0.01, 1.95, 0.13, "off_white")

            if face > 0:
                word.rot(180)

            out += word.move(x=cx, y=y)

    for z in (0.95, 1.4):
        out += ck.box(0.31, -0.07, z, 0.38, 0.07, z + 0.07, "steel", d=0)

    out += ck.box(0.36, -0.1, 1.05, 0.45, 0.0, 1.3, "steel_dk", c=0.025, d=1)
    out += c.rod((0.42, -0.05, 1.28), (0.5, -0.12, 1.42), 0.025, "steel", d=0)
    path = [(0.34, 0.1, 0.92), (0.45, 0.1, 0.7), (0.49, 0.06, 0.35), (0.42, 0.02, 0.1), (0.36, -0.04, 0.3), (0.4, -0.06, 0.75), (0.41, -0.06, 1.06)]

    if L() == 2:
        path = [path[0], path[3], path[-1]]

    out += ck.tube(path, [0.028] * len(path), pick(6, 4, 3), "rubber_dk", smooth=False, d=2)

    return out


def drum():
    out = W()
    n = pick(14, 9, 6)

    if L() == 2:
        out += ck.lathe([(0.29, 0.0, "drum"), (0.29, 0.32, "drum_band"), (0.29, 0.6, "drum"), (0.29, 0.9)], n, smooth=False)
    else:
        out += ck.lathe([(0.27, 0.0, "drum_dk"), (0.3, 0.02, "drum_dk"), (0.3, 0.06, "drum"), (0.282, 0.075, "drum"), (0.282, 0.28, "drum_dk"), (0.306, 0.295, "drum_dk"), (0.306, 0.33, "drum_dk"), (0.285, 0.345, "drum_band"), (0.285, 0.57, "drum_dk"), (0.306, 0.585, "drum_dk"), (0.306, 0.62, "drum_dk"), (0.282, 0.635, "drum"), (0.282, 0.83, "drum"), (0.3, 0.84, "drum_dk"), (0.3, 0.89, "steel_dk"), (0.27, 0.9, "drum_dk"), (0.26, 0.87)], n, smooth=False)

    out += c.face([(math.cos(2 * math.pi * i / ck.sides_for(n)) * 0.27, math.sin(2 * math.pi * i / ck.sides_for(n)) * 0.27, 0.9 if L() == 2 else 0.872) for i in range(ck.sides_for(n))], "drum", (0, 0, 1))

    for x, y, r in ((0.13, -0.08, 0.05), (-0.12, 0.1, 0.03)):
        out += ck.cyl((x, y, 0.87), r, 0.028, "steel", sides=7, d=0)

    return out


def phone():
    out = W()
    out += ck.box(-0.6, -0.53, 0.0, 0.6, 0.53, 0.1, "steel_dk", c=0.03)

    for x in (-0.49, 0.49):
        for y in (-0.42, 0.42):
            out += ck.box(x - 0.065, y - 0.065, 0.1, x + 0.065, y + 0.065, 1.96, "phone", c=0.025, skip="d")

    def wall(width, glazed=True):
        part = W()
        part += c.plate(-width / 2, width / 2, 0.1, 1.9, 0.02, "glass")
        part += c.plate(-width / 2, width / 2, 0.1, 1.9, 0.03, "glass", 1)
        part += ck.box(-width / 2, -0.02, 0.1, width / 2, 0.04, 0.42, "phone", d=2, skip="lr")
        part += ck.box(-width / 2, -0.02, 1.78, width / 2, 0.04, 1.9, "phone", d=2, skip="lr")

        if L() < 2:
            part += ck.box(-0.016, -0.005, 0.42, 0.016, 0.03, 1.78, "phone_lt", d=1, skip="bdt")

            for z in (0.86, 1.32):
                part += ck.box(-width / 2, -0.008, z, width / 2, 0.028, z + 0.035, "phone_lt", d=1, skip="blr")

        if L() == 0:
            part += c.face([(-width / 2 + 0.05, 0.016, 1.45), (-width / 2 + 0.16, 0.016, 1.45), (-width / 2 + 0.05, 0.016, 1.68)], "glass_sky", (0, -1, 0), ao=False)

        return part

    out += wall(0.85).move(y=-0.44)
    out += wall(0.72).rot(90).move(x=0.51)
    out += wall(0.85).rot(180).move(y=0.44)
    out += wall(0.72).rot(-90).move(x=-0.51)
    out += ck.box(-0.37, -0.485, 0.12, -0.31, -0.45, 1.88, "phone_dk", d=1, skip="b")
    out += ck.box(0.31, -0.485, 0.12, 0.37, -0.45, 1.88, "phone_dk", d=1, skip="b")
    out += ck.box(0.22, -0.52, 0.95, 0.27, -0.47, 1.25, "steel_lt", d=0)
    out += ck.box(-0.55, -0.48, 1.9, 0.55, 0.48, 2.12, "phone", c=0.03)

    for part, dist in ((0, -0.482), (180, 0.482)):
        sign = c.plate(-0.42, 0.42, 1.935, 2.085, -0.002, "canvas")
        sign += c.text("PHONE", 0.0, -0.008, 1.955, 0.11, "sign")

        if part:
            sign.rot(part)

        out += sign.move(y=dist)

    out += ck.box(-0.6, -0.53, 2.1, 0.6, 0.53, 2.18, "phone_dk", c=0.025, d=1)
    out += ck.box(-0.54, -0.47, 2.18, 0.54, 0.47, 2.3, "phone", c=0.04, taper=(0.7, 0.66), skip="d")
    out += ck.box(-0.15, 0.2, 0.8, 0.15, 0.37, 1.3, "iron_lt", c=0.03, d=0)

    return out


def picnic():
    out = W()
    n = pick(5, 1, 1)

    for i in range(n):
        w = 0.72 / n
        y0 = -0.36 + i * w
        out += ck.box(-0.9, y0, 0.69, 0.9, y0 + w - (0.015 if n > 1 else 0), 0.75, "wood_lt" if i % 2 == 0 else "plank", c=0.012 if L() == 0 else 0.0)

    for s in (-1, 1):
        for i in range(pick(2, 1, 1)):
            w = 0.25 / pick(2, 1, 1)
            y0 = 0.505 + i * w
            ya, yb = sorted((s * y0, s * (y0 + w - (0.012 if L() == 0 else 0))))
            out += ck.box(-0.9, ya, 0.39, 0.9, yb, 0.45, "wood_lt" if i == 0 else "plank", c=0.012 if L() == 0 else 0.0)

    for x in (-0.62, 0.62):
        for s in (-1, 1):
            out += c.beam((x, s * 0.62, 0.02), (x, s * 0.17, 0.69), 0.075, "iron_dk", d=1 if s else 0)

        out += ck.box(x - 0.035, -0.74, 0.32, x + 0.035, 0.74, 0.39, "iron_dk", d=1)
        out += ck.box(x - 0.035, -0.32, 0.62, x + 0.035, 0.32, 0.69, "iron_dk", d=0)

    out += c.beam((-0.6, 0.0, 0.34), (0.6, 0.0, 0.66), 0.05, "iron", d=0)
    out += ck.cyl((0.35, -0.08, 0.75), 0.04, 0.1, "awn_rust", sides=7, d=0)

    return out


def light():
    out = W()
    n = pick(10, 6, 4)
    out += ck.cyl((0, 0.1, 0.0), 0.12, 0.07, "iron_dk", sides=n, d=1)
    out += ck.cyl((0, 0.1, 0.07), 0.08, 0.1, "iron", sides=n, rt=0.055, d=1)
    out += ck.cyl((0, 0.1, 0.05), 0.048, 2.1, "iron_dk", sides=pick(8, 5, 4))
    out += ck.box(-0.23, -0.065, 2.1, 0.23, 0.269, 3.1, "lamp_teal", c=0.05)
    out += ck.box(-0.2, -0.11, 2.14, 0.2, -0.06, 3.06, "iron", c=0.025, d=2)

    for z, col in ((2.3, "lens_green"), (2.61, "lens_amber"), (2.92, "lens_red")):
        out += disc(0.0, z, 0.115, -0.118, col)

        if L() < 2:
            m = pick(6, 4, 3)
            arc = [math.pi * (0.05 + 0.9 * i / m) for i in range(m + 1)]

            for a0, a1 in zip(arc, arc[1:]):
                p = [(math.cos(a0) * 0.14, -0.11, z + math.sin(a0) * 0.14), (math.cos(a1) * 0.14, -0.11, z + math.sin(a1) * 0.14), (math.cos(a1) * 0.15, -0.255, z + math.sin(a1) * 0.13), (math.cos(a0) * 0.15, -0.255, z + math.sin(a0) * 0.13)]
                out.append(ck.Poly(p, "iron_dk"))
                out.append(ck.Poly(list(reversed(p)), "black", False, True, False))

        if L() == 0:
            out += disc(-0.03, z + 0.035, 0.028, -0.123, "lamp_glass", n=6)

    out += ck.cyl((0, 0.1, 3.1), 0.07, 0.05, "iron_lt", sides=n, d=1)
    out += ck.cyl((0, 0.1, 3.15), 0.035, 0.04, "iron_dk", sides=6, d=0)

    for z in (2.35, 2.85):
        out += ck.box(-0.245, 0.05, z, 0.245, 0.15, z + 0.04, "teal_dk", d=0)

    return out


def lamp():
    out = W()
    px = -0.9
    n = pick(9, 5, 4)
    out += ck.lathe([(0.22, 0.0, "pole_dk"), (0.22, 0.09, "pole"), (0.15, 0.14, "pole"), (0.1, 0.42, "orange"), (0.12, 0.43, "orange"), (0.12, 0.52, "orange"), (0.085, 0.54)], n, (px, 0, 0), smooth=False)
    path = [(px, 0, 0.5), (px, 0, 1.55), (px, 0, 3.25), (px + 0.07, 0, 3.58), (px + 0.28, 0, 3.8), (px + 0.58, 0, 3.87), (px + 0.88, 0, 3.8), (px + 1.12, 0, 3.7)]

    if L() == 1:
        path = [path[0], path[2], path[4], path[6], path[7]]

    if L() == 2:
        path = [path[0], path[2], path[5], path[7]]

    radii = [0.075] + [0.062] * 2 + [0.055] * (len(path) - 3)
    out += ck.tube(path, radii[:len(path)], pick(8, 5, 3), "pole", smooth=False, caps=(False, True))
    out += ck.cyl((px, 0, 1.52), 0.09, 0.09, "pole_dk", sides=n, d=0)
    out += c.rod((px + 0.97, 0, 3.775), (px + 1.12, 0, 3.7), 0.085, "orange", sides=pick(8, 5, 4), caps=(True, True), d=1)
    dome = [(0.14, 3.58), (1.12, 3.5), (1.12, 3.62), (1.02, 3.82), (0.82, 3.94), (0.52, 3.96), (0.28, 3.86), (0.14, 3.7)]

    if L() == 2:
        dome = [(0.14, 3.58), (1.12, 3.5), (0.92, 3.9), (0.3, 3.92)]

    mid = ck.extrude(dome, -0.24, 0.24, "lamp_teal", force=True, caps="")
    out += mid

    for s in (-1, 1):
        inner = [(0.63 + (x - 0.63) * 0.86, 3.72 + (z - 3.72) * 0.84) for x, z in dome]

        for i in range(len(dome)):
            j = (i + 1) % len(dome)
            out += c.face([(dome[i][0], s * 0.24, dome[i][1]), (dome[j][0], s * 0.24, dome[j][1]), (inner[j][0], s * 0.31, inner[j][1]), (inner[i][0], s * 0.31, inner[i][1])], "lamp_teal", (0, s, 0))

        out += c.face([(p[0], s * 0.31, p[1]) for p in inner], "lamp_teal", (0, s, 0))

    out += ck.box(0.2, -0.23, 3.43, 1.06, 0.23, 3.56, "iron_dk", c=0.04, d=1, shear=(0.0, 0.0))
    out += c.face([(0.3, -0.17, 3.375), (0.96, -0.17, 3.37), (0.96, 0.17, 3.37), (0.3, 0.17, 3.375)], "lamp_glass", (0, 0, -1), ao=False)

    if L() < 2:
        for p, q, nrm in (((0.3, -0.17), (0.96, -0.17), (0, -1, 0)), ((0.96, -0.17), (0.96, 0.17), (1, 0, 0)), ((0.96, 0.17), (0.3, 0.17), (0, 1, 0)), ((0.3, 0.17), (0.3, -0.17), (-1, 0, 0))):
            out += c.face([(p[0], p[1], 3.37), (q[0], q[1], 3.37), (q[0], q[1], 3.44), (p[0], p[1], 3.44)], "lamp_glass", nrm)

    return out


def soda():
    out = W()

    def arch(w, z0, zs, z1, n):
        pts = [(-w, z0), (w, z0)]

        for i in range(n + 1):
            t = math.pi * i / n
            pts.append((w * math.copysign(abs(math.cos(t)) ** 0.5, math.cos(t)), zs + (z1 - zs) * math.sin(t) ** 0.75))

        return pts

    n = pick(10, 6, 4)
    out += ck.box(-0.37, -0.3, 0.0, 0.37, 0.3, 0.07, "iron_dk", d=1)
    out += ck.extrude(arch(0.355, 0.05, 1.28, 1.5, n), -0.27, 0.3, "soda", force=True)
    out += ck.extrude(arch(0.29, 1.19, 1.29, 1.43, n), -0.3, -0.27, "canvas", force=True, caps="f")
    out += c.text("SODA", 0.0, -0.31, 1.23, 0.14, "soda_dk", w=0.5)

    for z in (0.69, 1.14):
        out += ck.box(-0.373, -0.285, z, 0.373, 0.31, z + 0.035, "teal_deep", d=1)

    out += ck.box(-0.3, -0.295, 0.72, 0.3, -0.26, 1.12, "teal_dk", c=0.02, d=1, skip="b")
    out += c.plate(-0.25, 0.25, 0.77, 1.07, -0.301, "glass")

    if L() == 0:
        for i in range(4):
            x = -0.17 + i * 0.115
            col = ("awn_rust", "mustard", "teal_lt", "off_white")[i]
            out += c.plate(x - 0.032, x + 0.032, 0.8, 0.94, -0.306, col)
            out += c.plate(x - 0.014, x + 0.014, 0.94, 0.99, -0.306, col)

    out += ck.box(0.07, -0.305, 0.43, 0.2, -0.27, 0.64, "steel", c=0.015, d=1, skip="b")
    out += c.plate(0.12, 0.15, 0.5, 0.6, -0.311, "black", d=0)
    out += ck.box(0.1, -0.3, 0.32, 0.2, -0.265, 0.39, "steel_lt", d=0)
    out += ck.box(-0.19, -0.3, 0.17, 0.07, -0.265, 0.34, "steel_dk", d=1, skip="b")
    out += c.plate(-0.16, 0.04, 0.19, 0.31, -0.306, "black")
    out += ck.box(-0.3, -0.29, 0.07, 0.3, -0.265, 0.13, "steel", d=0)

    for x in (-0.358, 0.358):
        out += ck.box(x - 0.015, -0.285, 0.07, x + 0.015, -0.24, 0.69, "soda_dk", d=0)

    return out


def ice():
    out = W()
    out += ck.box(-0.714, -0.36, 0.0, 0.714, 0.36, 0.13, "wood", c=0.035)
    out += ck.box(-0.66, -0.31, 0.12, 0.66, 0.31, 0.7, "off_white", c=0.06 if L() == 0 else 0.0)
    out += ck.box(-0.668, -0.318, 0.33, 0.668, 0.318, 0.55, "teal", d=2, skip="td")
    out += c.text("ICE", 0.0, -0.326, 0.355, 0.17, "off_white", t=0.035)

    for s in (-1, 1):
        x0, x1 = sorted((s * 0.015, s * 0.65))
        out += ck.box(x0, -0.32, 0.7, x1, 0.32, 0.78, "steel_lt", c=0.025, d=2)
        out += ck.box(x0 + 0.07, -0.25, 0.775, x1 - 0.07, 0.23, 0.8, "white", d=1)

        for x in (s * 0.25, s * 0.41):
            out += ck.box(x - 0.015, -0.2, 0.8, x + 0.015, -0.165, 0.838, "iron", d=0)

        out += ck.box(min(s * 0.24, s * 0.42), -0.2, 0.82, max(s * 0.24, s * 0.42), -0.165, 0.838, "iron_lt", d=0)

        for x in (s * 0.2, s * 0.5):
            out += ck.box(x - 0.05, 0.29, 0.68, x + 0.05, 0.36, 0.8, "wood_dk", d=0)

    out += ck.cyl((0.52, -0.33, 0.18), 0.028, 0.08, "steel", sides=6, d=0)
    out += c.rod((0.52, -0.32, 0.24), (0.58, -0.36, 0.24), 0.018, "steel", d=0)

    return out


def cans():
    out = W()

    for x in (-0.32, 0.32):
        for y0, y1 in ((-0.25, -0.1), (0.25, 0.15)):
            out += c.beam((x, y0, 0.02), (x, y1, 0.92), 0.055, "iron_dk", d=2)

        out += ck.box(x - 0.039, -0.271, 0.0, x + 0.039, -0.2, 0.04, "iron", d=0)
        out += ck.box(x - 0.039, 0.2, 0.0, x + 0.039, 0.271, 0.04, "iron", d=0)

    out += c.plate(-0.3, 0.3, 0.12, 0.9, 0.2, "black", -1, d=2)
    out += c.plate(-0.3, 0.3, 0.12, 0.9, 0.206, "iron_dk", 1)
    labels = (("awn_rust", "off_white"), ("teal_dk", "mustard"), ("brick_dk", "mustard"))

    for row, z in enumerate((0.15, 0.43, 0.71)):
        y = -0.215 + row * 0.04
        out += ck.box(-0.32, y, z - 0.035, 0.32, 0.2, z, "iron", d=1)

        for i in range(3):
            x = -0.19 + i * 0.19
            a0, b0 = labels[2 - row]
            m = pick(9, 5, 4)

            if L() == 2:
                out += c.plate(x - 0.075, x + 0.075, z, z + 0.2, y + 0.03, a0 if i != 1 else b0)
                continue

            if L() == 1:
                out += ck.lathe([(0.075, 0.0, a0), (0.075, 0.07, b0), (0.075, 0.14, a0), (0.075, 0.2)], 7, (x, y + 0.1, z), smooth=False)
            else:
                out += ck.lathe([(0.072, 0.0, "steel"), (0.078, 0.015, a0), (0.078, 0.065, b0), (0.078, 0.13, a0), (0.078, 0.185, "steel_lt"), (0.07, 0.2, "steel"), (0.0, 0.2)], 9, (x, y + 0.1, z), smooth=False)

    out += ck.box(-0.25, -0.1, 0.9, 0.25, -0.04, 1.1, "steel_lt", c=0.025, d=2)
    out += c.text("OIL", 0.0, -0.108, 0.945, 0.12, "red_dk")
    out += c.beam((-0.32, -0.08, 0.92), (0.32, -0.08, 0.92), 0.045, "iron_lt", d=1)

    return out


def post(x, z1, t=0.09, col="steel_dk", holes=True):
    out = W()
    out += ck.box(x - t / 2, -0.02, 0.0, x + t / 2, 0.06, z1, col, c=0.015 if L() == 0 else 0.0, skip="d")

    if holes and L() == 0:
        for k in range(int((z1 - 0.3) / 0.22)):
            z = 0.2 + k * 0.22
            out += c.plate(x - 0.012, x + 0.012, z, z + 0.03, -0.024, "iron_dk")

    return out


def shield():
    out = W()
    out += post(0.0, 2.58, 0.1, "steel")
    out += ck.box(-0.12, -0.074, 0.0, 0.12, 0.074, 0.05, "iron", d=0)
    shape = [(0.0, 0.94), (0.28, 1.01), (0.5, 1.17), (0.58, 1.42), (0.54, 1.66), (0.64, 1.86), (0.52, 2.07), (0.36, 2.0), (0.18, 2.07), (0.0, 2.01), (-0.18, 2.07), (-0.36, 2.0), (-0.52, 2.07), (-0.64, 1.86), (-0.54, 1.66), (-0.58, 1.42), (-0.5, 1.17), (-0.28, 1.01)]

    if L() == 2:
        shape = [shape[i] for i in (0, 2, 5, 6, 9, 12, 13, 16)]

    out += ck.extrude(shape, -0.062, -0.025, "off_white", force=True)
    inner = [(x * 0.92, 1.55 + (z - 1.55) * 0.9) for x, z in shape]
    out += c.face([(p[0], -0.066, p[1]) for p in inner], "sign", (0, -1, 0))
    white = [(x * 0.84, 1.55 + (z - 1.55) * 0.81) for x, z in shape]
    out += c.face([(p[0], -0.07, p[1]) for p in white], "off_white", (0, -1, 0))
    field = [(-0.42, 1.2), (0.42, 1.2), (0.47, 1.45), (0.4, 1.7), (-0.4, 1.7), (-0.47, 1.45)]
    out += c.face([(p[0], -0.073, p[1]) for p in field], "sign", (0, -1, 0))
    out += c.text("27", 0.0, -0.077, 1.26, 0.38, "off_white", t=0.075)
    out += c.text("ROUTE", 0.0, -0.077, 1.76, 0.16, "sign")
    out += ck.box(-0.48, -0.062, 2.2, 0.48, -0.025, 2.6, "off_white", c=0.02, d=2)
    out += c.plate(-0.43, 0.43, 2.245, 2.555, -0.068, "sign")
    out += c.text("NORTH", 0.0, -0.075, 2.305, 0.19, "off_white", w=0.74)

    for z in (1.12, 2.4):
        out += ck.cyl((0, 0.06, z), 0.028, 0.02, "iron", sides=6, d=0)

    return out


def mileage():
    out = W()

    for x in (-0.82, 0.82):
        out += ck.box(x - 0.07, -0.0, 0.0, x + 0.07, 0.129, 2.9, "iron_lt", c=0.02 if L() == 0 else 0.0, skip="d")
        out += ck.box(x - 0.085, -0.015, 2.9, x + 0.085, 0.129, 3.0, "iron_dk", c=0.035, d=1)
        out += ck.box(x - 0.1, -0.02, 0.0, x + 0.1, 0.129, 0.08, "conc_dk", d=0)

    for z, word, num in ((2.31, "MESA", "12"), (1.7, "GULCH", "4"), (1.09, "TOWN", "31")):
        out += ck.box(-1.07, -0.07, z, 1.07, -0.005, z + 0.5, "off_white", c=0.03, d=2)
        out += c.plate(-1.02, 1.02, z + 0.04, z + 0.46, -0.076, "steel_dk")
        out += c.plate(-0.995, 0.995, z + 0.065, z + 0.435, -0.08, "off_white")
        out += c.text(word, -0.34, -0.088, z + 0.13, 0.24, "sign", w=1.15)
        out += c.plate(0.46, 0.92, z + 0.1, z + 0.4, -0.086, "sign")
        out += c.text(num, 0.69, -0.094, z + 0.155, 0.19, "off_white")

        for x in (-0.82, 0.82):
            out += ck.box(x - 0.025, -0.095, z + 0.44, x + 0.025, -0.082, z + 0.475, "iron_dk", d=0)

    return out


def sidewalk():
    out = W()

    if L() > 0:
        out += c.face([(-2.0, -2.0, 0.045), (2.0, -2.0, 0.045), (2.0, 2.0, 0.045), (-2.0, 2.0, 0.045)], "paver", (0, 0, 1), ao=False)

        return out

    out += c.face([(-2.0, -2.0, 0.03), (2.0, -2.0, 0.03), (2.0, 2.0, 0.03), (-2.0, 2.0, 0.03)], "joint", (0, 0, 1), ao=False, cast=False)
    cols = ("paver", "paver_lt", "paver", "paver", "paver_dk", "paver", "paver")

    for i in range(5):
        x0 = -2.0 + i * 0.8
        cut = (0.0, 0.04, -0.03, 0.02, -0.02)[i]

        for k, (ya, yb) in enumerate(((-2.0, cut - 0.012), (cut + 0.012, 2.0))):
            col = cols[(i + k * 3) % 7]
            out += c.face([(x0 + 0.014, ya + 0.012, 0.048), (x0 + 0.786, ya + 0.012, 0.048), (x0 + 0.786, yb - 0.012, 0.048), (x0 + 0.014, yb - 0.012, 0.048)], col, (0, 0, 1), ao=False, cast=False)

    return out


def ibc():
    out = W()
    out += ck.box(-0.6, -0.5, 0.1, 0.6, 0.5, 0.17, "iron", c=0.015 if L() == 0 else 0.0, d=2)

    for x in (-0.52, 0.0, 0.52):
        out += ck.box(x - 0.08, -0.49, 0.0, x + 0.08, 0.49, 0.1, "iron_dk", d=2, skip="dt")

    out += ck.box(-0.54, -0.44, 0.17, 0.54, 0.44, 0.47, "drum_dk", d=2, skip="d")
    out += ck.box(-0.54, -0.44, 0.47, 0.54, 0.44, 1.07, "off_white", c=0.07 if L() == 0 else 0.0, skip="d")
    xs = pick((-0.575, -0.345, -0.115, 0.115, 0.345, 0.575), (-0.575, -0.19, 0.19, 0.575), (-0.575, 0.575))
    ys = pick((-0.475, -0.237, 0.0, 0.237, 0.475), (-0.475, 0.0, 0.475), (-0.475, 0.475))

    def strip(p, q, n, t=0.022):
        a = Vector(p)
        b = Vector(q)
        d = (b - a).normalized()
        s = d.cross(Vector(n)).normalized() * (t / 2)
        part = c.face([a - s, b - s, b + s, a + s], "steel", n, cast=False)

        if L() == 0:
            part += c.face([a - s, b - s, b + s, a + s], "steel_dk", (-n[0], -n[1], -n[2]), cast=False)

        return part

    for s in (-1, 1):
        for x in xs:
            out += strip((x, s * 0.478, 0.17), (x, s * 0.478, 1.11), (0, s, 0))

        for y in ys:
            out += strip((s * 0.578, y, 0.17), (s * 0.578, y, 1.11), (s, 0, 0))

        for z in pick((0.36, 0.56, 0.76, 0.96, 1.1), (0.45, 0.78, 1.1), (1.1,)):
            out += strip((-0.585, s * 0.481, z), (0.585, s * 0.481, z), (0, s, 0), 0.026)
            out += strip((s * 0.581, -0.485, z), (s * 0.581, 0.485, z), (s, 0, 0), 0.026)

    for y in (-0.237, 0.237):
        out += ck.box(-0.58, y - 0.014, 1.09, 0.58, y + 0.014, 1.115, "steel", d=0)

    out += ck.cyl((0.0, 0.0, 1.065), 0.13, 0.05, "iron", sides=pick(10, 7, 5), d=1)
    out += ck.cyl((0.0, 0.0, 1.11), 0.09, 0.05, "iron_dk", sides=pick(8, 6, 4), d=1)
    out += ck.box(-0.07, -0.5, 0.19, 0.07, -0.43, 0.33, "iron_lt", c=0.02, d=1)
    out += ck.box(-0.1, -0.501, 0.33, 0.1, -0.47, 0.355, "red", d=0)
    out += c.plate(-0.28, 0.28, 0.62, 0.9, -0.488, "canvas", d=1)

    for k in range(3):
        out += c.plate(-0.22, 0.2 - k * 0.07, 0.66 + k * 0.075, 0.695 + k * 0.075, -0.492, "teal_dk", d=0)

    return out


ALL = {
    "pump": (pump, {"errors": (0.01, 0.045)}),
    "drum": (drum, {"errors": (0.008, 0.035)}),
    "phone": (phone, {"errors": (0.012, 0.05)}),
    "picnic": (picnic, {"errors": (0.01, 0.045)}),
    "light": (light, {"errors": (0.01, 0.045)}),
    "lamp": (lamp, {"errors": (0.01, 0.04)}),
    "soda": (soda, {"errors": (0.008, 0.04)}),
    "ice": (ice, {"errors": (0.008, 0.035)}),
    "cans": (cans, {"errors": (0.006, 0.03)}),
    "shield": (shield, {"errors": (0.012, 0.05)}),
    "mileage": (mileage, {"errors": (0.012, 0.05)}),
    "sidewalk": (sidewalk, {"errors": (0.006,), "ao": 0.0, "grime": 0.0, "speckle": 0.012}),
    "ibc": (ibc, {"errors": (0.008, 0.04)}),
}
