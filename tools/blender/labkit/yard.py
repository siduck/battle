import math

import lk
from common import *
from mathutils import Matrix, Vector


def chamfered(hx, hy, cut, z):
    return [(-hx + cut, -hy, z), (hx - cut, -hy, z), (hx, -hy + cut, z), (hx, hy - cut, z), (hx - cut, hy, z), (-hx + cut, hy, z), (-hx, hy - cut, z), (-hx, -hy + cut, z)]


def crate():
    out = part()
    body = [chamfered(0.60, 0.59, 0.09, 0.0), chamfered(0.66, 0.65, 0.11, 0.08), chamfered(0.66, 0.65, 0.11, 1.0), chamfered(0.62, 0.61, 0.10, 1.04), chamfered(0.62, 0.61, 0.10, 1.07), chamfered(0.655, 0.645, 0.11, 1.09), chamfered(0.655, 0.645, 0.11, 1.22), chamfered(0.55, 0.54, 0.09, 1.30)]
    cols = ("graphite_dk", "slate", "graphite", "black", "slate_dk", "slate", "slate_lt")
    out += loft(body, lambda j, i: cols[j], caps=("black", "slate"))
    out += loft([chamfered(0.68, 0.67, 0.115, 0.52), chamfered(0.68, 0.67, 0.115, 0.65)], "rust", caps=("rust_dk", "rust_lt"))

    for z in (0.54, 0.63):
        out += loft([chamfered(0.684, 0.674, 0.117, z - 0.008), chamfered(0.684, 0.674, 0.117, z + 0.008)], "rust_dk", d=0)

    for ang, off in ((0, 0.65), (90, 0.66), (180, 0.65), (-90, 0.66)):
        face_p = part()
        face_p += plate(-0.44, 0.44, 0.15, 0.50, -off - 0.002, "black")
        face_p += plate(-0.44, 0.44, 0.67, 0.96, -off - 0.002, "black")

        for x in (-0.235, 0.235):
            for z0, col in ((0.325, "steel"), (0.815, "steel_lt")):
                r = 0.125 if z0 < 0.5 else 0.13
                face_p += disc(x, z0, -off - 0.002, r, col, n=8, depth=0.022, d=1, rim="slate_lt")
                face_p += plate(x - 0.035, x + 0.035, z0 - 0.035, z0 + 0.035, -off - 0.026, "slate_dk", d=0)

        for x in (-0.50, 0.50):
            face_p += box(x - 0.035, -off - 0.025, 0.1, x + 0.035, -off, 0.49, "slate_lt", skip="b", d=0)
            face_p += box(x - 0.035, -off - 0.025, 0.69, x + 0.035, -off, 0.99, "slate_lt", skip="b", d=0)

        out += face_p.rot(ang, "Z")

    for x in (-0.15, 0.15):
        out += box(x - 0.085, -0.71, 0.49, x + 0.085, -0.66, 0.69, "rust_dk", c=0.016, skip="b")
        out += plate(x - 0.04, x + 0.04, 0.55, 0.63, -0.712, "copper", d=0)

    out += deck(-0.45, 0.45, -0.44, 0.44, 1.303, "black", cast=True)

    for x in (-0.22, 0.22):
        for y in (-0.22, 0.23):
            out += puck((x, y, 1.30), 0.14, 0.02, "steel", sides=8, top="steel_lt", d=1)
            out += deck(x - 0.035, x + 0.035, y - 0.035, y + 0.035, 1.323, "slate", d=0)

    return out


def battery():
    out = part()
    outline = [(-0.63, 0.0), (0.63, 0.0), (0.75, 0.14), (0.75, 1.62), (0.57, 1.80), (-0.57, 1.80), (-0.75, 1.62), (-0.75, 0.14)]
    out += extrude(outline, -0.46, 0.52, "slate", side=lambda i, a, b: "slate_lt" if min(a[1], b[1]) > 1.6 else ("graphite" if max(a[1], b[1]) < 0.2 else "slate_dk"), force=True)
    out += box(-0.66, 0.50, 0.12, 0.66, 0.54, 1.66, "graphite", c=0.012, skip="f", d=1)
    inner = [(-0.50, 0.13), (0.50, 0.13), (0.58, 0.22), (0.58, 1.53), (0.49, 1.62), (-0.49, 1.62), (-0.58, 1.53), (-0.58, 0.22)]
    outer = [(-0.62, 0.05), (0.62, 0.05), (0.70, 0.15), (0.70, 1.60), (0.56, 1.74), (-0.56, 1.74), (-0.70, 1.60), (-0.70, 0.15)]

    for i in range(8):
        j = (i + 1) % 8
        out += face([(outer[i][0], -0.50, outer[i][1]), (outer[j][0], -0.50, outer[j][1]), (inner[j][0], -0.50, inner[j][1]), (inner[i][0], -0.50, inner[i][1])], "slate_lt" if i in (3, 4, 5) else "slate", towards=(0, -1, 0))
        mid = ((outer[i][0] + outer[j][0]) / 2, 0, (outer[i][1] + outer[j][1]) / 2 - 0.9)
        out += face([(outer[i][0], -0.50, outer[i][1]), (outer[j][0], -0.50, outer[j][1]), (outer[j][0], -0.46, outer[j][1]), (outer[i][0], -0.46, outer[i][1])], "slate_dk", towards=mid)
        out += face([(inner[i][0], -0.50, inner[i][1]), (inner[j][0], -0.50, inner[j][1]), (inner[j][0], -0.462, inner[j][1]), (inner[i][0], -0.462, inner[i][1])], "black", d=1, towards=(-mid[0], 0, -mid[2]))

    out += extrude(inner, -0.464, -0.461, "black", caps="f", side=None, force=True)
    out += box(-0.46, -0.495, 1.23, 0.46, -0.464, 1.51, "graphite", c=0.012, skip="b", d=1)
    out += plate(-0.41, 0.41, 1.28, 1.46, -0.497, "teal_lt")
    out += plate(-0.37, -0.05, 1.40, 1.425, -0.499, "screen", d=0)

    for i, h in enumerate((0.05, 0.08, 0.065, 0.11, 0.09, 0.12, 0.1)):
        out += plate(0.0 + i * 0.055, 0.035 + i * 0.055, 1.30, 1.30 + h, -0.499, "screen", d=0)

    for x in (-0.37, -0.185, 0.0, 0.185, 0.37):
        out += disc(x, 1.03, -0.464, 0.068, "copper", n=6, depth=0.07, d=1, rim="rust_dk")
        out += disc(x, 1.03, -0.534, 0.028, "rust_dk", n=6, depth=0.008, d=0)

    out += box(-0.44, -0.53, 0.69, -0.30, -0.464, 0.77, "red", c=0.012, skip="b", d=1)
    out += plate(-0.22, 0.02, 0.71, 0.75, -0.466, "steel", d=0)

    for i in range(4):
        x = -0.43 + i * 0.072
        out += box(x, -0.50, 0.27, x + 0.036, -0.464, 0.50, "steel", skip="b", d=1)

    for z in (0.30, 0.46, 0.62):
        out += box(0.12, -0.55 if z < 0.4 else -0.53, z, 0.43, -0.464, z + 0.12, "steel_dk", c=0.012, skip="b", d=1)
        out += plate(0.17, 0.30, z + 0.045, z + 0.075, -0.552 if z < 0.4 else -0.532, "graphite", d=0)
        out += plate(0.34, 0.38, z + 0.045, z + 0.075, -0.552 if z < 0.4 else -0.532, "screen", d=0)

    for x in (-0.315, 0.0, 0.315):
        out += puck((x, -0.2, 1.79), 0.135, 0.07, "copper", sides=6, top="copper", d=1)
        out += puck((x, -0.2, 1.855), 0.055, 0.025, "graphite", sides=6, d=0)

    for z in (0.22, 0.62, 1.02, 1.42):
        for s in (-1, 1):
            out += side(-0.28, 0.34, z, z + 0.05, s * 0.751, s, "graphite", d=0)

    for x in (-0.42, 0.42):
        for z in (0.33, 1.47):
            out += disc(x, z, -0.54, 0.055, "steel_lt", n=6, depth=0.008, d=0).rot(180, "Z")

    return out


def solar():
    out = part()
    y0, z0 = -1.07, 0.48
    y1, z1 = 1.07, 1.55
    ang = math.atan2(z1 - z0, y1 - y0)
    length = math.hypot(y1 - y0, z1 - z0)
    m = Matrix.Translation(Vector((0, y0, z0))) @ Matrix.Rotation(ang, 4, "X")

    for xa, xb in ((-1.99, -0.68), (-0.655, 0.655), (0.68, 1.99)):
        p = part()
        p += box(xa, 0.0, -0.04, xb, length, 0.012, "steel_dk", top="steel_lt")
        p += deck(xa + 0.045, xb - 0.045, 0.045, length - 0.045, 0.016, "glass_dd")
        nx, ny = (2, 3) if lk.LOD == 0 else (1, 1)
        cw = (xb - xa - 0.11) / nx
        ch = (length - 0.11) / ny

        for i in range(nx):
            for j in range(ny):
                cx0 = xa + 0.055 + i * cw + 0.014
                cy0 = 0.055 + j * ch + 0.014
                p += deck(cx0, cx0 + cw - 0.028, cy0, cy0 + ch - 0.028, 0.021, "solar_lt" if (i + j) % 2 else "solar")

                if lk.LOD == 0:
                    p += face([(cx0 + 0.04, cy0 + 0.04, 0.024), (cx0 + 0.12, cy0 + 0.04, 0.024), (cx0 + cw * 0.62, cy0 + ch - 0.07, 0.024), (cx0 + cw * 0.62 - 0.08, cy0 + ch - 0.07, 0.024)], "teal_lt", cast=False, towards=(0, 0, 1)) if (i + j) % 3 == 0 else part()

        out += p.xform(m)

    for y in (-0.54, 0.69):
        z = z0 + (y - y0) * (z1 - z0) / (y1 - y0) - 0.10
        out += box(-2.0, y - 0.05, z - 0.055, 2.0, y + 0.05, z + 0.03, "slate_lt", c=0.012)

    for x in (-1.335, 0.0, 1.335):
        for y in (-0.54, 0.69):
            z = z0 + (y - y0) * (z1 - z0) / (y1 - y0) - 0.14
            out += box(x - 0.04, y - 0.04, 0.05, x + 0.04, y + 0.04, z, "slate", skip="td")
            out += box(x - 0.11, y - 0.12, 0.0, x + 0.11, y + 0.12, 0.07, "graphite", c=0.018, skip="d", d=1)

        out += rod((x, -0.50, 0.12), (x, 0.66, 0.90), 0.028, "slate_dk", d=1)

    out += box(-0.25, 0.62, 0.45, 0.25, 0.68, 0.75, "white_dk", c=0.012, d=1)
    out += plate(-0.17, -0.03, 0.56, 0.66, 0.618, "teal", d=0)

    return out


def fan(cx, cy, z, r):
    out = part()
    out += lk.torus((cx, cy, z + 0.03), r, 0.035, "slate", segs=14, sides=4, axis="Z")
    out += face(circle(r, 12, z - 0.012, cx, cy), "black", towards=(0, 0, 1))

    for i in range(5):
        a = i * math.pi * 2 / 5
        pts = []

        for rr, da in ((0.06, -0.15), (r * 0.9, -0.1), (r * 0.9, 0.55), (0.06, 0.5)):
            pts.append((cx + math.cos(a + da) * rr, cy + math.sin(a + da) * rr, z + (0.012 if da > 0.2 else -0.006)))

        out += face(pts, "slate_dk", d=1, cast=False, towards=(0, 0, 1))

    out += puck((cx, cy, z - 0.01), 0.085, 0.055, "slate_lt", sides=8, d=1)

    return out


def hvac():
    out = part()
    out += box(-0.676, -0.643, 0.0, 0.676, 0.643, 0.10, "concrete_lt", c=0.025, skip="d")

    for x in (-0.46, 0.46):
        for y in (-0.40, 0.46):
            out += box(x - 0.08, y - 0.07, 0.095, x + 0.08, y + 0.07, 0.20, "graphite", skip="td", d=1)

    out += box(-0.58, -0.52, 0.19, 0.58, 0.62, 1.22, "panel", c=0.026, skip="t")
    out += box(-0.60, -0.545, 1.17, 0.60, 0.64, 1.28, "white_dk", c=0.035)
    out += fan(0.0, 0.045, 1.30, 0.415)
    out += louvres(-0.47, 0.47, 0.34, 1.06, -0.521, 8, "steel", back="graphite_dk", depth=0.035)
    out += frame(-0.51, 0.51, 0.30, 1.10, -0.52, 0.045, "white_dk", depth=0.045, d=1)
    out += box(-0.02, -0.575, 0.30, 0.02, -0.555, 1.10, "white_dk", skip="b", d=1)

    for x in (-0.545, 0.545):
        for z in (0.24, 1.13):
            out += disc(x, z, -0.52, 0.018, "slate", n=6, d=0)

    out += box(0.575, -0.29, 0.55, 0.66, -0.03, 0.84, "slate_lt", c=0.014, d=1)
    out += side(-0.22, -0.10, 0.62, 0.72, 0.662, 1, "teal", d=0)
    out += side(-0.25, 0.05, 0.98, 1.10, 0.582, 1, "white", d=0)
    out += tube([(0.62, -0.16, 0.55), (0.62, -0.16, 0.36), (0.62, 0.62, 0.36)], 0.03, 5, "slate", caps=(False, True), smooth=False, d=1)
    out += tube([(0.61, -0.08, 0.55), (0.61, -0.08, 0.27), (0.61, 0.62, 0.27)], 0.022, 4, "copper", caps=(False, True), smooth=False, d=0)

    for z in (0.40, 0.55, 0.70, 0.85):
        out += side(-0.36, 0.42, z, z + 0.05, -0.582, -1, "slate_lt", d=0)
        out += plate(-0.4, 0.4, z, z + 0.05, -0.622, "slate_lt", d=0).rot(180, "Z")

    return out


def pallet():
    out = part()

    for y in (-0.43, 0.0, 0.43):
        out += box(-0.60, y - 0.07, 0.0, 0.60, y + 0.07, 0.025, "wood_dd", skip="d", d=1)

        for x in (-0.53, 0.0, 0.53):
            out += box(x - 0.065, y - 0.065, 0.02 if lk.LOD == 0 else 0.0, x + 0.065, y + 0.065, 0.12, "wood_dd", skip="td")

    for y in (-0.43, 0.0, 0.43):
        out += box(-0.60, y - 0.07, 0.118, 0.60, y + 0.07, 0.14, "wood_dk", d=1)

    if lk.LOD:
        out += box(-0.60, -0.50, 0.10, 0.60, 0.50, 0.165, "wood")
    else:
        for x in (-0.55, -0.37, -0.18, 0.0, 0.18, 0.37, 0.55):
            out += box(x - 0.05, -0.50, 0.138, x + 0.05, 0.50, 0.165, "wood" if int(abs(x) * 10) % 2 else "wood_dk", skip="d")

    tones = ("steel", "steel_lt", "slate_lt", "steel_dk")

    for k, (z0, z1) in enumerate(((0.165, 0.42), (0.425, 0.68), (0.685, 0.94))):
        if lk.LOD >= 2:
            out += box(-0.54, -0.45, z0, 0.54, 0.45, z1, tones[k % 3], skip="d")

            continue

        xs = (-0.54, -0.18, 0.18, 0.54) if k % 2 == 0 else (-0.54, -0.27, 0.12, 0.54)
        ys = (-0.45, 0.02, 0.45) if k != 1 else (-0.45, -0.05, 0.45)

        for i in range(3):
            for j in range(2):
                col = tones[(i * 2 + j + k) % 4]
                out += box(xs[i] + 0.004, ys[j] + 0.004, z0, xs[i + 1] - 0.004, ys[j + 1] - 0.004, z1, col, c=0.014, skip="d")

    for z in (0.26, 0.655):
        for s in (-1, 1):
            out += plate(-0.545, 0.545, z, z + 0.03, -0.455, "graphite").rot(0 if s < 0 else 180, "Z")
            out += side(-0.455, 0.455, z, z + 0.03, s * 0.545, s, "graphite")

    p = box(-0.17, -0.11, 0.94, 0.13, 0.11, 1.07, "steel_lt", c=0.012, skip="d")
    p.rot(18, "Z", (0, 0, 0))
    out += p
    out += box(0.14, -0.12, 0.94, 0.42, 0.02, 0.975, "steel", skip="d", d=1)
    out += plate(-0.40, -0.22, 0.80, 0.90, -0.453, "canvas", d=0)
    out += plate(-0.385, -0.30, 0.86, 0.88, -0.455, "teal", d=0)

    return out


def barrier():
    out = part()
    prof = [(-0.29, 0.0), (-0.30, 0.24), (-0.17, 0.36), (-0.10, 0.96), (-0.07, 1.0), (0.07, 1.0), (0.10, 0.96), (0.17, 0.36), (0.30, 0.24), (0.29, 0.0)]

    if lk.LOD >= 2:
        prof = [(-0.29, 0.0), (-0.25, 0.3), (-0.09, 1.0), (0.09, 1.0), (0.25, 0.3), (0.29, 0.0)]

    for k, (xa, xb) in enumerate(((-1.97, -0.68), (-0.645, 0.645), (0.68, 1.97))):
        rings = [[(xa, y * 0.93, z - 0.012 * (z > 0.9)) for y, z in prof], [(xa + 0.04, y, z) for y, z in prof], [(xb - 0.04, y, z) for y, z in prof], [(xb, y * 0.93, z - 0.012 * (z > 0.9)) for y, z in prof]]

        def col(j, i, n=len(prof)):
            zs = (prof[i][1] + prof[(i + 1) % n][1]) / 2

            if zs > 0.97:
                return "orange_lt"

            return "orange_dk" if zs < 0.3 or j != 1 else "orange"

        out += loft(rings, col, caps=("orange_dk", "orange_dk"), outward=None)

        for x0, x1 in ((xa + 0.06, xa + 0.34), (xb - 0.34, xb - 0.06)):
            out += box(x0, -0.27, 0.0, x1, 0.27, 0.075, "orange_dk", c=0.016, skip="d", d=1)

        for turn in (0, 180):
            f = part()
            f += face([(-0.50, -0.148, 0.80), (0.50, -0.148, 0.80), (0.50, -0.134, 0.92), (-0.50, -0.134, 0.92)], "white", cast=False, towards=(0, -1, 0))

            if lk.LOD < 2:
                for i in (0, 2):
                    x = -0.42 + i * 0.28
                    f += face([(x, -0.151, 0.80), (x + 0.16, -0.151, 0.80), (x + 0.22, -0.137, 0.92), (x + 0.06, -0.137, 0.92)], "red", d=1, cast=False, towards=(0, -1, 0))

                for x in (-0.28, 0.28):
                    zt, zb = 0.68, 0.42
                    yt, yb = -0.134 - 0.004, -0.163 - 0.004
                    f += face([(x - 0.15, yb, zb), (x + 0.15, yb, zb), (x + 0.15, yt, zt), (x - 0.15, yt, zt)], "wine_dk", d=1, cast=False, towards=(0, -1, 0))
                    f += face([(x - 0.12, yb - 0.003, zb + 0.015), (x + 0.12, yb - 0.003, zb + 0.015), (x + 0.12, (yt + yb) / 2 - 0.003, (zt + zb) / 2 - 0.05), (x - 0.12, (yt + yb) / 2 - 0.003, (zt + zb) / 2 - 0.05)], "black", d=0, cast=False, towards=(0, -1, 0))

            out += f.rot(turn, "Z").move((xa + xb) / 2, 0, 0)

        out += puck(((xa + xb) / 2 + (0.02 if k == 1 else 0.0), 0.0, 0.998), 0.055, 0.025, "graphite", sides=6, d=0)

    for x in (-1.99, -0.665, 0.665, 1.99):
        out += rod((x, 0.0, 0.30), (x, 0.0, 1.03), 0.012, "steel", d=1)
        out += box(x - 0.045 if abs(x) < 1 else x - 0.012, -0.06, 0.24, x + 0.045 if abs(x) < 1 else x + 0.008, 0.06, 0.32, "graphite_dk", d=0)

    out += puck((1.805, 0.0, 0.99), 0.12, 0.05, "orange", sides=8, d=1)
    out += puck((1.805, 0.0, 1.035), 0.095, 0.05, "graphite", sides=8, d=1)
    out += lathe([(0.075, 1.08, "amber"), (0.07, 1.18, "amber"), (0.035, 1.235, "amber"), (0.0, 1.24, "amber")], 7, at=(1.805, 0, 0), smooth=False, d=1)

    return out


def dish():
    out = part()
    base = [circle(1.93, 8, 0.0, 0.0, 0.42, phase=math.pi / 8), circle(1.93, 8, 0.22, 0.0, 0.42), circle(1.68, 8, 0.38, 0.0, 0.4), circle(0.98, 8, 2.9, 0.0, 0.4), circle(1.10, 8, 3.0, 0.0, 0.4), circle(1.10, 8, 3.34, 0.0, 0.4), circle(0.85, 8, 3.45, 0.0, 0.4)]
    cols = ("graphite", "slate_lt", "slate_dk", "slate", "slate_lt", "slate")
    out += loft(base, lambda j, i: cols[j], caps=(None, "slate_lt"))

    if lk.LOD == 0:
        for i in (4, 5, 6):
            a = math.pi / 8 + i * math.pi / 4
            b = a + math.pi / 4
            m = (a + b) / 2
            for z, r in ((0.9, 1.48), (2.35, 1.12)):
                tx, ty = -math.sin(m), math.cos(m)
                cx, cy = math.cos(m) * r, 0.4 + math.sin(m) * r
                out += face([(cx - tx * 0.28, cy - ty * 0.28, z - 0.22), (cx + tx * 0.28, cy + ty * 0.28, z - 0.22), (cx + tx * 0.24 - math.cos(m) * 0.11, cy + ty * 0.24 - math.sin(m) * 0.11, z + 0.22), (cx - tx * 0.24 - math.cos(m) * 0.11, cy - ty * 0.24 - math.sin(m) * 0.11, z + 0.22)], "graphite_dk", cast=False, towards=(math.cos(m), math.sin(m), 0.3))

        out += box(-0.35, -1.38, 0.35, 0.35, -1.12, 1.25, "white_dk", c=0.03, d=0)
        out += plate(-0.2, 0.05, 0.9, 1.1, -1.385, "teal", d=0)

    for s in (-1, 1):
        out += box(s * 1.04, 0.03, 3.38, s * 0.78, 0.86, 4.55, "slate", c=0.07)
        out += rod((s * 0.8, 0.45, 4.35), (s * 1.12, 0.45, 4.35), 0.18, "steel_dk", sides=7, d=1, caps=(True, True))

    out += box(-0.82, 0.05, 3.40, 0.82, 0.95, 3.75, "slate_dk", c=0.06)
    out += box(-0.55, 0.25, 3.7, 0.55, 1.18, 4.62, "slate", c=0.12)
    n = Vector((0.0, -math.cos(math.radians(33)), math.sin(math.radians(33))))
    u = Vector((1.0, 0.0, 0.0))
    v = Vector((0.0, math.sin(math.radians(33)), math.cos(math.radians(33))))
    c = Vector((0.0, -0.36, 5.70))
    segs = (14, 10, 8)[lk.LOD]

    def rim(r, depth):
        return [tuple(c - n * depth + u * (math.cos(2 * math.pi * i / segs) * r) + v * (math.sin(2 * math.pi * i / segs) * r)) for i in range(segs)]

    front_r = ((0.35, 0.60), (1.2, 0.45), (1.95, 0.24), (2.50, 0.0))

    if lk.LOD >= 2:
        front_r = ((0.35, 0.60), (1.7, 0.3), (2.50, 0.0))

    rings = [rim(r, d) for r, d in front_r]
    out += loft(rings, lambda j, i: ("steel_lt" if i % 2 else "white_dk") if j == len(rings) - 2 else ("white_dk" if i % 2 else "panel"), caps=("steel", None), outward=tuple(c - n * 6))

    for f in out[-(segs * (len(rings) - 1) + 1):]:
        if f.normal().dot(n) < 0:
            f.pts.reverse()

    back = [rim(2.55, -0.03), rim(2.55, 0.08), rim(2.0, 0.42), rim(1.0, 0.74), rim(0.45, 0.82)]
    out += loft(back, lambda j, i: ("steel_lt", "steel", "steel_dk", "slate_lt")[j], caps=(None, "slate"), outward=tuple(c + n * 0.9))
    out += loft([rim(2.55, -0.03), rim(2.47, -0.03)], "white", outward=tuple(c - n * 5))
    focus = c + n * 1.35

    low = c - v * 2.44 + n * 0.02
    elbow = c - v * 2.15 + n * 0.85
    out += tube([tuple(low), tuple(elbow), tuple(focus)], [0.075, 0.06, 0.05], 5, "steel_dk", caps=(False, False), smooth=False)

    out += tube([tuple(c - n * 0.55), tuple(c + n * 0.7), tuple(focus - n * 0.1)], [0.2, 0.12, 0.16], 8, "rust_dk", caps=(False, False), smooth=False, d=1)
    out += tube([tuple(focus - n * 0.15), tuple(focus + n * 0.12), tuple(focus + n * 0.45)], [0.30, 0.30, 0.18], 8, lambda i, j: "rust" if j == 0 else "rust_lt", caps=(True, "copper"), smooth=False)

    if lk.LOD == 0:
        for a in range(0, 360, 45):
            rad = math.radians(a + 22)
            p0 = c + u * (math.cos(rad) * 0.5) + v * (math.sin(rad) * 0.5) - n * 0.84
            p1 = c + u * (math.cos(rad) * 2.2) + v * (math.sin(rad) * 2.2) - n * 0.36
            out += rod(tuple(p0), tuple(p1), 0.04, "slate_lt")

    return out


def radiator():
    out = part()

    for x in (-1.25, 1.25):
        out += box(x - 0.23, -0.18, 0.0, x + 0.23, 0.18, 0.07, "graphite", c=0.018, skip="d")
        out += box(x - 0.15, -0.09, 0.06, x + 0.15, 0.09, 0.34, "graphite_dk", skip="td", taper=(0.75, 0.75))
        out += box(x - 0.18, -0.12, 0.29, x + 0.18, 0.12, 0.40, "slate_dk", c=0.016, d=1)

    out += box(-2.0, -0.11, 0.38, 2.0, 0.11, 0.47, "steel_lt", c=0.016)
    out += box(-2.0, -0.11, 1.70, 2.0, 0.11, 1.80, "steel_lt", c=0.016, top="copper")

    for x in (-2.0, 1.90):
        out += box(x, -0.11, 0.46, x + 0.10, 0.11, 1.71, "steel", skip="td")

    out += plate(-1.91, 1.91, 0.46, 1.71, -0.012, "graphite")
    out += plate(-1.91, 1.91, 0.46, 1.71, -0.012, "graphite").rot(180, "Z")
    n = (22, 11, 5)[lk.LOD]
    w = 3.82 / n

    for i in range(n):
        x = -1.91 + w * (i + 0.5)

        for turn in (0, 180):
            f = part()
            f += face([(-w * 0.17, -0.088, 0.47), (w * 0.17, -0.088, 0.47), (w * 0.17, -0.088, 1.70), (-w * 0.17, -0.088, 1.70)], "steel", cast=False, towards=(0, -1, 0))

            if lk.LOD < 2:
                for sx, col in ((-1, "slate_lt"), (1, "slate")):
                    f += face([(sx * w * 0.17, -0.088, 0.47), (sx * w * 0.30, -0.016, 0.47), (sx * w * 0.30, -0.016, 1.70), (sx * w * 0.17, -0.088, 1.70)], col, cast=False, towards=(sx, -0.3, 0))

            out += f.move(x if turn == 0 else -x, 0, 0).rot(turn, "Z")

    if lk.LOD == 0:
        for s in (-1, 1):
            out += plate(-1.92, 1.92, 1.06, 1.10, -0.092, "steel_dk").rot(0 if s < 0 else 180, "Z")

            for x in (-1.95, -0.65, 0.65, 1.95):
                out += disc(x, 0.425, -0.11, 0.025, "slate", n=6).rot(0 if s < 0 else 180, "Z")
                out += disc(x, 1.75, -0.11, 0.025, "slate", n=6).rot(0 if s < 0 else 180, "Z")

    return out


def floodmast():
    out = part()
    hub = (0.0, -0.22, 1.52)

    for fx, fy in ((0.0, 0.80), (-0.93, -0.80), (0.93, -0.80)):
        out += rod(hub, (fx, fy, 0.06), 0.055, "slate", sides=4)
        out += puck((fx, fy, 0.0), 0.09, 0.06, "graphite_dk", sides=6)
        out += rod((fx * 0.52, -0.22 + (fy + 0.22) * 0.52, 0.76), (0.0, -0.22, 0.60), 0.025, "slate_dk", d=1)

    out += cyl((0, -0.22, 0.40), 0.085, 2.65, "slate_lt", sides=8, smooth=False, caps=(True, True))
    out += cyl((0, -0.22, 1.33), 0.19, 0.38, "slate_dk", sides=8, smooth=False, caps=(True, True), d=1)
    out += cyl((0, -0.22, 0.50), 0.12, 0.2, "graphite", sides=8, smooth=False, caps=(True, True), d=0)
    out += cyl((0, -0.22, 2.96), 0.115, 0.20, "steel", sides=8, smooth=False, caps=(True, True), d=1)
    out += cyl((0, -0.22, 3.10), 0.065, 1.72, "graphite", sides=7, smooth=False, caps=(False, True))
    out += plate(-0.07, 0.07, 1.44, 1.60, -0.412, "copper", d=0)
    out += box(-1.05, -0.28, 4.79, 1.05, -0.12, 4.89, "slate_lt", c=0.016)
    out += box(-1.05, -0.28, 5.55, 1.05, -0.12, 5.656, "slate_lt", c=0.016)

    for x in (-1.02, 1.02):
        out += box(x - 0.03, -0.24, 4.88, x + 0.03, -0.16, 5.56, "slate", skip="td")

    for s in (-1, 1):
        xa, xb = sorted((s * 0.10, s * 0.94))
        out += box(xa, -0.50, 4.92, xb, -0.24, 5.52, "panel_dk", c=0.045)
        out += box(xa - 0.005, -0.57, 5.49, xb + 0.005, -0.46, 5.55, "slate_dk", c=0.012, d=1)
        out += plate(xa + 0.05, xb - 0.05, 4.97, 5.47, -0.503, "graphite")
        cx = (xa + xb) / 2
        out += ring(cx, 5.22, -0.50, 0.11, 0.19, "steel", n=10, depth=0.03, d=1)
        out += disc(cx, 5.22, -0.505, 0.11, "lamp", n=10, depth=0.012)

        for z in (5.02, 5.42):
            out += plate(cx - 0.3, cx - 0.23, z - 0.02, z + 0.02, -0.505, "slate_lt", d=0)
            out += plate(cx + 0.23, cx + 0.3, z - 0.02, z + 0.02, -0.505, "slate_lt", d=0)

        out += box(cx - 0.13, -0.24, 5.05, cx + 0.13, -0.17, 5.35, "slate_dk", skip="f", d=0)

    out += tube([(0.07, -0.15, 4.75), (0.12, -0.12, 3.6), (0.1, -0.14, 1.75)], 0.012, 3, "black", caps=(False, False), smooth=False, d=0)

    return out


def horizontal(x, ry, rz, zc, n):
    return [(x, math.cos(2 * math.pi * (i + 0.5) / n) * ry, zc + math.sin(2 * math.pi * (i + 0.5) / n) * rz) for i in range(n)]


def htank():
    out = part()
    n = (16, 10, 8)[lk.LOD]
    prof = [(-2.16, 0.40), (-2.04, 0.68), (-1.80, 0.90), (-1.45, 0.985), (1.45, 0.985), (1.80, 0.90), (2.04, 0.68), (2.16, 0.40)]

    if lk.LOD >= 2:
        prof = [(-2.16, 0.45), (-1.7, 0.95), (1.7, 0.95), (2.16, 0.45)]

    rings = [horizontal(x, r, r, 1.35, n) for x, r in prof]

    def col(j, i):
        s = math.sin(2 * math.pi * (i + 1.0) / n)

        if s < -0.15:
            return "teal" if abs(prof[j][0]) < 1.7 else "teal_dk"

        return "white_dk" if abs(prof[j][0]) < 1.7 and abs(prof[j + 1][0]) < 1.7 else "panel"

    out += loft(rings, col, caps=("panel_dk", "panel_dk"))

    if lk.LOD == 0:
        for x in (-0.55, 0.55):
            out += loft([horizontal(x - 0.025, 0.998, 0.998, 1.35, n), horizontal(x + 0.025, 0.998, 0.998, 1.35, n)], lambda j, i: "teal_dk" if math.sin(2 * math.pi * (i + 1.0) / n) < -0.15 else "panel_dk")

    for x in (-1.28, 1.28):
        out += loft([horizontal(x - 0.09, 1.048, 1.048, 1.35, n), horizontal(x + 0.09, 1.048, 1.048, 1.35, n)], "graphite", caps=("graphite_dk", "graphite_dk"))
        out += box(x - 0.235, -1.01, 0.0, x + 0.235, 1.01, 0.11, "slate_dk", c=0.025, skip="d")

        for y in (-0.80, 0.80):
            out += box(x - 0.09, y - 0.09, 0.10, x + 0.09, y + 0.09, 0.82, "graphite", skip="d")

    out += puck((0.0, 0.0, 2.31), 0.24, 0.07, "steel_dk", sides=8, top="steel", d=1)
    out += puck((0.0, 0.0, 2.37), 0.09, 0.03, "graphite", sides=6, d=0)
    out += disc(0.0, 1.30, -0.99, 0.19, "steel_lt", n=10, depth=0.02, d=1)
    out += disc(0.0, 1.30, -1.01, 0.12, "canvas", n=10, depth=0.006, d=0)
    out += plate(0.0, 0.09, 1.295, 1.315, -1.02, "red", d=0)
    out += plate(0.45, 0.95, 1.55, 1.80, -0.955, "canvas", d=1)
    out += plate(0.50, 0.90, 1.70, 1.75, -0.962, "teal_dk", d=0)

    return out


def tank():
    out = part()
    n = (16, 10, 8)[lk.LOD]
    prof = [(1.05, 0.93, "slate_lt"), (1.78, 1.03, "steel"), (2.0, 1.28, "panel"), (2.0, 2.2, "steel_lt"), (2.0, 2.26, "panel"), (2.0, 3.30, "panel"), (2.08, 3.30, "rust"), (2.08, 4.0, "rust"), (2.0, 4.0, "panel"), (2.0, 5.06, "panel"), (1.93, 5.40, "steel_lt"), (1.68, 5.80, "panel"), (1.22, 6.12, "steel_lt"), (0.62, 6.32, "steel_lt"), (0.0, 6.37, "steel_lt")]

    if lk.LOD >= 2:
        prof = [prof[i] for i in (0, 2, 5, 6, 7, 8, 9, 11, 14)]

    out += lathe(prof, 16, smooth=False)
    out += face(circle(1.05, lk.sides_for(16), 0.93), "graphite", towards=(0, 0, -1))
    out += puck((0, 0, 6.28), 0.42, 0.12, "steel_dk", sides=8, top="steel", d=1)

    for z in (3.36, 3.94):
        out += cyl((0, 0, z - 0.02), 2.095, 0.04, "rust_dk", sides=n, smooth=False, caps=(False, False), d=0)

    for ang in (0, 90, 180, 270):
        leg = part()
        leg += box(-0.17, -1.85, 0.08, 0.17, -1.48, 1.73, "slate", c=0.03, skip="d")
        leg += box(-0.29, -1.93, 0.0, 0.29, -1.42, 0.10, "slate_dk", c=0.025, skip="d")
        leg += box(-0.22, -2.03, 1.45, 0.22, -1.84, 1.80, "steel_dk", c=0.025, d=1)

        if lk.LOD == 0:
            for x in (-0.2, 0.2):
                leg += puck((x, -1.78, 0.095), 0.045, 0.03, "steel", sides=6)

        out += leg.rot(ang, "Z")

    out += lk.torus((0, 0, 0.62), 1.62, 0.05, "slate_dk", segs=16, sides=4, axis="Z", d=1)

    if lk.LOD == 0:
        for i in range(8):
            a = math.pi / 8 + i * math.pi / 4
            x, y = math.cos(a), math.sin(a)
            out += rod((x * 2.005, y * 2.005, 1.32), (x * 2.005, y * 2.005, 3.28), 0.018, "steel")
            out += rod((x * 2.005, y * 2.005, 4.02), (x * 2.005, y * 2.005, 5.04), 0.018, "steel")

    hatch = disc(0.0, 2.55, -1.955, 0.34, "steel_dk", n=10, depth=0.09, d=1, rim="slate_lt") + disc(0.0, 2.55, -2.045, 0.2, "steel", n=10, depth=0.025, d=0)
    out += hatch
    out += plate(-0.42, 0.42, 4.35, 4.75, -2.0, "canvas", d=1)
    out += plate(-0.32, 0.32, 4.62, 4.68, -2.005, "teal", d=0)

    return out


def mini_dish(at, yaw, r):
    out = part()
    n = (10, 7, 6)[lk.LOD]

    def rim(rr, y):
        return [(math.cos(2 * math.pi * i / n) * rr, y, math.sin(2 * math.pi * i / n) * rr) for i in range(n)]

    out += loft([rim(r, -0.06), rim(r * 0.62, 0.07), rim(0.08, 0.12)], lambda j, i: "steel_lt" if j else "steel", caps=(None, "slate"), outward=(0, -1.5, 0))
    inner = loft([rim(r, -0.06), rim(r * 0.5, 0.0), rim(0.05, 0.03)], lambda j, i: "white" if i % 2 else "white_dk", caps=(None, "panel"), outward=(0, 3, 0))

    for f in inner:
        if f.normal().y > 0:
            f.pts.reverse()

    out += inner
    out += rod((0, 0.0, 0), (0, -0.28, 0), 0.025, "graphite")
    out += box(-0.05, -0.34, -0.05, 0.05, -0.26, 0.05, "rust_dk", d=1)
    out.rot(yaw, "Z").move(*at)

    return out


def mast():
    out = part()
    cx, cy = -0.10, 0.245
    top_z = 6.58

    def leg(i, z):
        t = z / top_z
        h = 0.92 + (0.22 - 0.92) * t
        sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]

        return (cx + sx * h, cy + sy * h, z)

    for i in range(4):
        out += rod(leg(i, 0.0), leg(i, top_z), 0.065, "slate", sides=4)
        x, y, _ = leg(i, 0.0)
        out += box(x - 0.13, y - 0.13, 0.0, x + 0.13, y + 0.13, 0.09, "graphite", skip="d", d=1)

    levels = [0.15, 1.52, 2.95, 4.2, 5.42, 6.5] if lk.LOD < 2 else [0.15, 2.95, 5.2, 6.5]

    for k in range(len(levels) - 1):
        z0, z1 = levels[k], levels[k + 1]

        for i in range(4):
            j = (i + 1) % 4
            a, b = (i, j) if (k + i) % 2 == 0 else (j, i)
            out += rod(leg(a, z0), leg(b, z1), 0.032, "graphite", sides=3)

            if lk.LOD < 2:
                out += rod(leg(i, z1), leg(j, z1), 0.03, "graphite_dk", sides=3, d=1)

    out += box(cx - 0.36, cy - 0.36, 6.52, cx + 0.36, cy + 0.36, 6.70, "slate_dk", c=0.03)
    out += puck((cx, cy, 6.69), 0.23, 0.12, "slate_lt", sides=8, d=1)
    out += cyl((cx, cy, 6.75), 0.08, 1.35, "slate", sides=6, rt=0.055, smooth=False, caps=(False, True))
    out += puck((cx, cy, 8.0), 0.095, 0.10, "steel", sides=8, top="steel_lt", d=1)
    out += cyl((cx, cy, 8.08), 0.042, 0.62, "steel_dk", sides=5, rt=0.03, smooth=False, caps=(False, False))
    out += cyl((cx, cy, 8.68), 0.048, 0.42, "rust", sides=6, rt=0.012, smooth=False, caps=(True, True))

    out += cyl((cx, cy, 6.80), 0.115, 0.55, "slate_lt", sides=6, rt=0.08, smooth=False, caps=(False, True), d=1)

    out += mini_dish((1.12, -0.95, 4.75), 48, 0.62)
    out += rod((0.28, -0.1, 4.62), (1.10, -0.93, 4.74), 0.045, "slate_dk", d=1)
    out += mini_dish((-1.1, 1.05, 3.35), 228, 0.6)
    out += rod((-0.52, 0.62, 3.25), (-1.08, 1.03, 3.35), 0.045, "slate_dk", d=1)
    out += box(cx - 0.2, cy - 0.78, 1.0, cx + 0.2, cy - 0.62, 1.52, "white_dk", c=0.025, d=1)
    out += plate(cx - 0.1, cx + 0.1, 1.28, 1.38, cy - 0.782, "teal", d=0)

    return out


def pipe():
    out = part()
    n = (12, 8, 6)[lk.LOD]

    for yc in (-0.235, 0.235):
        def ring_at(x, r):
            return horizontal(x, r, r, 0.55, n)

        shift = lambda ring_: [(p[0], p[1] + yc, p[2]) for p in ring_]
        out += loft([shift(ring_at(-1.93, 0.178)), shift(ring_at(1.93, 0.178))], lambda j, i: "steel_dk" if (i + 1) % n > n / 2 else "steel", caps=(None, None))

        for x0, x1 in ((-2.0, -1.84), (1.84, 2.0)):
            out += loft([shift(ring_at(x0, 0.208)), shift(ring_at(x1, 0.208))], "slate_lt", caps=("slate", "slate"))
            end = x0 if x0 < 0 else x1
            sgn = -1 if end < 0 else 1
            out += face([(end + sgn * 0.001, y, z) for _, y, z in shift(ring_at(end, 0.11))], "black", d=1, cast=False, towards=(sgn, 0, 0))

        for x in (-0.42, 0.42):
            out += loft([shift(ring_at(x - 0.05, 0.192)), shift(ring_at(x + 0.05, 0.192))], "teal" if x < 0 else "slate", d=1)

        for x in (-1.0, 1.0):
            out += loft([shift(ring_at(x - 0.1, 0.20)), shift(ring_at(x + 0.1, 0.20))], "graphite", d=1)
            out += box(x - 0.1, yc - 0.11, 0.70, x + 0.1, yc + 0.11, 0.78, "slate", c=0.016, d=0)

    for x in (-1.0, 1.0):
        out += box(x - 0.17, -0.72, 0.0, x + 0.17, 0.72, 0.07, "slate_dk", c=0.018, skip="d")

        for s in (-1, 1):
            out += rod((x, s * 0.58, 0.06), (x, s * 0.34, 0.36), 0.075, "graphite", sides=4)

        out += box(x - 0.13, -0.50, 0.30, x + 0.13, 0.50, 0.41, "graphite", c=0.016)

    return out


def genset():
    out = part()
    out += box(-2.0, -1.0, 0.14, 2.0, 1.0, 0.42, "slate_dk", c=0.045)
    out += box(-1.89, -0.93, 0.0, 1.89, 0.93, 0.16, "graphite_dk", c=0.025, skip="d")
    out += box(-1.90, -0.87, 0.41, 1.90, 0.87, 2.36, "steel_dk", c=0.035, skip="d")

    for x in (-1.90, 1.90):
        for y in (-0.88, 0.88):
            out += box(x - 0.06, y - 0.06, 0.41, x + 0.06, y + 0.06, 2.36, "slate_lt", c=0.016, skip="td", d=1)

    out += box(-1.96, -0.96, 2.34, 1.96, 0.96, 2.44, "slate", c=0.025)
    out += box(-1.72, -0.76, 2.43, 1.72, 0.76, 2.50, "steel_dk", c=0.025, skip="d")

    for x in (-1.6, -0.55, 0.5):
        out += deck(x, x + 0.012, -0.74, 0.74, 2.502, "slate", d=0)

    for x0, x1 in ((-1.66, -0.84), (-0.82, 0.0), (0.0 + 0.02, 0.84), (0.86, 1.66)):
        out += louvres(x0 + 0.05, x1 - 0.05, 0.82, 1.98, -0.875, 9, "steel_lt", back="graphite")
        out += frame(x0, x1, 0.76, 2.04, -0.87, 0.055, "slate_lt", depth=0.05, d=1)

    back = part()

    for x0, x1 in ((-1.70, -0.30), (0.30, 1.70)):
        back += louvres(x0 + 0.05, x1 - 0.05, 0.82, 1.94, -0.875, 9, "steel_lt", back="graphite")
        back += frame(x0, x1, 0.76, 2.0, -0.87, 0.055, "slate_lt", depth=0.05, d=1)

    back += handle(0.0, 1.35, 0.3, -0.87, "graphite", vertical=True)
    out += back.rot(180, "Z")

    for s in (-1, 1):
        d = part()
        d += front(-0.58, 0.58, 0.62, 2.18, -1.90, "steel", depth=0.022, c=0.008)
        d += handle(0.40, 1.35, 0.22, -1.922, "graphite", vertical=True)
        d += plate(-0.36, -0.02, 1.65, 1.92, -1.924, "graphite_dk", d=1)
        d += plate(-0.31, -0.12, 1.75, 1.84, -1.926, "screen", d=0)

        for z in (0.78, 1.9):
            d += box(-0.60, -1.94, z, -0.54, -1.90, z + 0.14, "slate", skip="b", d=0)

        out += d.rot(90 * s, "Z")

    out += cyl((1.03, 0.42, 2.48), 0.17, 0.07, "graphite", sides=10, smooth=False, caps=(False, True))
    out += cyl((1.03, 0.42, 2.5), 0.095, 1.0, "graphite_dk", sides=10, smooth=False, caps=(False, False))
    out += cyl((1.03, 0.42, 3.38), 0.12, 0.17, "graphite", sides=10, smooth=False, caps=(True, "black"))

    for x in (-1.55, 1.55):
        for y in (-0.6, 0.6):
            out += box(x - 0.12, y - 0.05, 2.49, x + 0.12, y + 0.05, 2.58, "graphite", c=0.012, skip="d", d=1)

    for x in (-1.5, -0.5, 0.5, 1.5):
        out += disc(x, 0.28, -1.0, 0.03, "steel", n=6, d=0)

    out += plate(-1.5, -1.0, 0.50, 0.66, -0.874, "teal", d=1)

    return out


OPTS = {"ao": 0.48, "reach": 0.9, "grime": 0.12, "grime_h": 0.5}
THIN = {"ao": 0.3, "reach": 0.8, "grime": 0.08, "grime_h": 0.4}

ALL = {
    "crate": (crate, {"ao": 0.48, "reach": 0.9, "grime": 0.12, "grime_h": 0.5, "errors": (0.012, 0.045)}),
    "battery": (battery, OPTS),
    "solar": (solar, THIN),
    "hvac": (hvac, OPTS),
    "pallet": (pallet, OPTS),
    "barrier": (barrier, OPTS),
    "dish": (dish, {"ao": 0.38, "reach": 1.6, "grime": 0.1, "grime_h": 0.8}),
    "radiator": (radiator, {"ao": 0.28, "reach": 0.4, "grime": 0.1, "grime_h": 0.4}),
    "floodmast": (floodmast, THIN),
    "htank": (htank, OPTS),
    "tank": (tank, {"ao": 0.42, "reach": 1.8, "grime": 0.1, "grime_h": 1.0}),
    "mast": (mast, THIN),
    "pipe": (pipe, OPTS),
    "genset": (genset, OPTS),
}
