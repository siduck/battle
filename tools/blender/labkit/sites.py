import math

import lk
from common import *
from mathutils import Vector

C8 = math.cos(math.pi / 8)


def octa(h, z, cy=0.0):
    return circle(h / C8, 8, z, 0.0, cy, phase=math.pi / 8)


def stack(levels, cols, caps=(None, None), n=8):
    if n == 8:
        rings = [octa(h, z) for h, z in levels]
    else:
        rings = [circle(h, n, z) for h, z in levels]

    return loft(rings, lambda j, i: cols[j], caps=caps, wind=True)


def wall_quad(a, b, z0, z1, col, out_off=0.0, u0=0.0, u1=1.0, d=None, cast=True):
    a = Vector((a[0], a[1], 0))
    b = Vector((b[0], b[1], 0))
    t = b - a
    nrm = Vector((t.y, -t.x, 0)).normalized()
    mid = (a + b) / 2

    if nrm.dot(mid) < 0:
        nrm.negate()

    p0 = a + t * u0 + nrm * out_off
    p1 = a + t * u1 + nrm * out_off

    return face([(p0.x, p0.y, z0), (p1.x, p1.y, z0), (p1.x, p1.y, z1), (p0.x, p0.y, z1)], col, d=d, cast=cast, towards=tuple(nrm))


def polar(r, a, z):
    return (math.cos(a) * r, math.sin(a) * r, z)


def ctower():
    out = part()
    out += box(-2.48, -2.48, 0.0, 2.48, 2.48, 0.24, "concrete_dk", c=0.05, skip="d")
    out += box(-2.38, -2.38, 0.22, 2.38, 2.38, 2.08, "concrete", skip="dt")
    out += box(-2.48, -2.48, 2.05, 2.48, 2.48, 2.56, "white_dk", c=0.06)
    out += box(-2.2, -2.2, 2.55, 2.2, 2.2, 2.74, "concrete_dk", c=0.05, skip="d")

    for ang in (0, 90, 180, 270):
        f = part()
        xs = ((-2.0, -1.15), (-0.98, -0.13), (0.13, 0.98), (1.15, 2.0)) if ang else ((-2.0, -1.15), (1.15, 2.0))

        for x0, x1 in xs:
            f += plate(x0, x1, 0.5, 1.78, -2.385, "glass_dd", cast=True)
            f += frame(x0 - 0.06, x1 + 0.06, 0.44, 1.84, -2.38, 0.07, "white", depth=0.05, d=1)
            f += face([(x0 + 0.12, -2.39, 0.6), (x0 + 0.28, -2.39, 0.6), (x0 + 0.62, -2.39, 1.68), (x0 + 0.46, -2.39, 1.68)], "teal_dk", d=0, cast=False, towards=(0, -1, 0))

        for x in (-2.34, 2.22):
            f += box(x, -2.47, 0.22, x + 0.12, -2.38, 2.08, "concrete_lt", skip="btd", d=1)

        if ang == 0:
            f += frame(-0.8, 0.8, 0.22, 1.98, -2.38, 0.1, "white", depth=0.08)
            f += plate(-0.7, 0.7, 0.22, 1.88, -2.40, "slate_dk", cast=True)
            f += plate(-0.012, 0.012, 0.22, 1.88, -2.403, "graphite_dk", d=1)

            for x in (-0.38, 0.38):
                f += plate(x - 0.22, x + 0.22, 1.05, 1.68, -2.404, "glass_dd", d=1)
                f += handle(x * 0.35, 0.95, 0.3, -2.41, "steel_lt", vertical=True)

            f += plate(-1.0, 1.0, 2.16, 2.42, -2.487, "teal", d=None)

        out += f.rot(ang, "Z")

    out += stack([(1.98, 2.7), (1.98, 3.0), (1.84, 3.1), (1.70, 18.1)], ("slate_lt", "slate", "panel"))

    if lk.LOD < 2:
        for z in (5.6, 8.2, 10.9, 13.6, 16.2):
            h = 1.84 - (z - 3.1) / 15.0 * 0.14
            out += stack([(h + 0.07, z - 0.09), (h + 0.07, z + 0.09)], ("white_dk",), caps=("panel_dk", "white"))

    for i in range(8):
        a = i * math.pi / 4
        h0, h1 = 1.84, 1.70
        face_dir = (math.cos(a), math.sin(a))

        if i in (6, 2, 0):
            for z in (4.0, 9.4, 14.8):
                h = h0 - (z - 3.1) / 15.0 * 0.14 + 0.012
                tx, ty = -face_dir[1], face_dir[0]
                px, py = face_dir[0] * h, face_dir[1] * h
                pts = [(px - tx * 0.22, py - ty * 0.22, z), (px + tx * 0.22, py + ty * 0.22, z), (px + tx * 0.22 - face_dir[0] * 0.009, py + ty * 0.22 - face_dir[1] * 0.009, z + 0.95), (px - tx * 0.22 - face_dir[0] * 0.009, py - ty * 0.22 - face_dir[1] * 0.009, z + 0.95)]
                out += face(pts, "glass_dd", d=1, cast=False, towards=(face_dir[0], face_dir[1], 0))

        va = a + math.pi / 8
        out += rod(polar(h0 / C8 + 0.02, va, 3.0), polar(h1 / C8 + 0.02, va, 18.1), 0.05, "white_dk", d=0)

    out += stack([(1.70, 18.05), (1.88, 18.3), (1.88, 18.55), (2.75, 19.8)], ("white", "teal", "panel_dk"))
    out += stack([(2.75, 19.8), (3.65, 19.85), (3.65, 20.12), (3.4, 20.12)], ("white", "white", "panel_dk"), caps=(None, "slate_dk"))
    out += stack([(2.85, 20.1), (2.85, 20.45), (3.02, 21.35)], ("panel", "glass_dd"))
    out += stack([(3.02, 21.35), (3.30, 21.48), (3.30, 21.72), (3.1, 21.76)], ("white_dk", "white", "white_dk"), caps=(None, "slate"))
    out += stack([(2.82, 21.72), (3.08, 23.38)], ("glass_dd",))
    out += stack([(3.08, 23.36), (3.72, 23.55), (3.72, 23.84), (3.45, 23.95)], ("panel_dk", "white", "white_dk"), caps=(None, "slate"))
    out += stack([(2.55, 23.93), (2.45, 24.35), (1.7, 24.65)], ("slate_lt", "slate_dk"), caps=(None, "graphite"))

    for i in range(8):
        a0 = octa(1.0, 0)[i]
        a1 = octa(1.0, 0)[(i + 1) % 8]
        a0 = Vector(a0)
        a1 = Vector(a1)

        for u in (0.0, 0.5):
            lo = a0.lerp(a1, u)
            out += rod((lo.x * 2.84, lo.y * 2.84, 20.45), (lo.x * 3.05, lo.y * 3.05, 21.38), 0.055, "white", d=1 if u else None)
            out += rod((lo.x * 2.83, lo.y * 2.83, 21.72), (lo.x * 3.11, lo.y * 3.11, 23.4), 0.06, "white", d=1 if u else None)

            for r, z0, zs in ((3.58, 20.12, (20.43, 20.74)), (3.20, 21.74, (22.1, 22.42))):
                out += rod((lo.x * r, lo.y * r, z0), (lo.x * r, lo.y * r, zs[1]), 0.03, "steel_lt", sides=3, d=0 if u else 1)

        for r, zs in ((3.58, (20.43, 20.74)), (3.20, (22.1, 22.42))):
            for z in zs:
                out += rod((a0.x * r, a0.y * r, z), (a1.x * r, a1.y * r, z), 0.025, "steel_lt", sides=3, d=1 if z == zs[0] else 2)

        if lk.LOD == 0:
            for u in (0.14, 0.6):
                lo, hi = a0.lerp(a1, u), a0.lerp(a1, u + 0.09)
                out += face([(lo.x * 2.90, lo.y * 2.90, 21.95), (hi.x * 2.90, hi.y * 2.90, 21.95), (hi.x * 3.04, hi.y * 3.04, 22.95), (lo.x * 3.04, lo.y * 3.04, 22.95)], "glass_dk", cast=False, towards=(lo.x, lo.y, 0))

    out += puck((0, 0, 24.62), 0.62, 0.22, "steel", sides=8, top="steel_lt")
    out += cyl((0, 0, 24.8), 0.16, 1.5, "slate_lt", sides=8, rt=0.11, smooth=False, caps=(False, True))
    out += cyl((0, 0, 26.25), 0.075, 1.6, "slate", sides=6, rt=0.045, smooth=False, caps=(False, True))
    out += blob((0, 0, 27.99), (0.24, 0.24, 0.22), ("orange_lt", "red", "red_dk"), sub=0, jitter=0.0, seed=1)

    for x, y, top in ((1.35, 0.75, 27.3), (-1.2, 1.0, 26.4), (-0.85, -1.35, 25.8)):
        out += puck((x, y, 24.5), 0.14, 0.28, "slate_lt", sides=6, d=1)
        out += cyl((x, y, 24.75), 0.045, top - 24.75, "steel_dk", sides=4, rt=0.02, smooth=False, caps=(False, True))

    out += lathe([(0.48, 24.5, "panel"), (0.52, 24.85, "white"), (0.36, 25.15, "white"), (0.0, 25.28, "white")], 8, at=(1.0, -1.0, 0), smooth=False, d=1)

    return out


def otower():
    out = part()

    for x in (-2.35, 2.35):
        out += box(x - 0.15, -2.5, 0.08, x + 0.15, 2.5, 0.43, "graphite", c=0.03)

    out += box(-2.46, 2.15, 0.10, 2.46, 2.45, 0.40, "graphite_dk", c=0.03)

    for x0, x1 in ((-2.46, -0.75), (0.75, 2.46)):
        out += box(x0, -2.45, 0.10, x1, -2.15, 0.40, "graphite_dk", c=0.03)

    for y in (-1.17, 1.17):
        out += box(-2.25, y - 0.15, 0.10, 2.25, y + 0.15, 0.32, "graphite_dk", skip="d", d=1)

    for x in (-2.15, 2.15):
        for y in (-2.15, 2.15):
            out += box(x - 0.29, y - 0.29, 0.0, x + 0.29, y + 0.29, 0.68, "slate", c=0.08, skip="d")
            out += puck((x, y, 0.67), 0.12, 0.05, "steel", sides=6, d=0)

    out += stack([(1.75, 0.1), (1.75, 0.7), (1.40, 1.0), (1.36, 12.34)], ("slate", "slate_lt", "panel"), caps=(None, None))

    for z in (4.1, 5.95, 7.8, 9.65, 11.5):
        out += stack([(1.39, z - 0.13), (1.48, z - 0.07), (1.48, z + 0.07), (1.39, z + 0.13)], ("white_dk", "white", "white_dk"))

    if lk.LOD < 2:
        for z in (4.6, 8.3, 10.15):
            out += plate(-0.2, 0.2, z, z + 0.8, -1.40, "glass_dd")
            out += frame(-0.28, 0.28, z - 0.08, z + 0.88, -1.385, 0.08, "slate_lt", depth=0.04, d=0)

        for i in (1, 3, 5, 7):
            a = i * math.pi / 4 + math.pi / 8
            out += rod(polar(1.36 / C8 + 0.03, a, 1.0), polar(1.36 / C8 + 0.03, a, 12.3), 0.055, "slate_lt", d=1)

        for k in range(18 if lk.LOD == 0 else 0):
            z = 1.4 + k * 0.6
            out += box(-0.3, 1.38, z, 0.3, 1.45, z + 0.05, "slate", d=0)

    n = 8
    hatch = [(math.cos(2 * math.pi * i / n + math.pi / n) * 1.875 / C8, 1.875 + math.sin(2 * math.pi * i / n + math.pi / n) * 1.875 / C8) for i in range(n)]
    out += extrude(hatch, -2.22, -0.9, "slate_lt", side=lambda i, a, b: "white_dk" if min(a[1], b[1]) > 2.4 else "slate", force=True)
    out += ring(0, 1.875, -2.22, 1.40, 1.875 / C8, "rust", n=8, depth=0.2, side="rust_dk")
    out += ring(0, 1.875, -2.22, 1.20, 1.40 / C8 * 0.98, "graphite", n=8, depth=0.08, d=1)
    out += disc(0, 1.875, -2.24, 1.25, "steel_dk", n=8, depth=0.12, rim="graphite")
    out += ring(0, 1.875, -2.36, 0.55, 0.82, "slate_lt", n=10, depth=0.08, d=1, side="slate")
    out += disc(0, 1.875, -2.37, 0.55, "graphite_dk", n=10, depth=0.02, d=1)
    out += disc(0, 1.875, -2.40, 0.20, "teal_dk", n=8, depth=0.02, d=0)

    if lk.LOD == 0:
        for i in range(8):
            a = i * math.pi / 4
            out += disc(math.cos(a) * 1.62, 1.875 + math.sin(a) * 1.62, -2.43, 0.075, "copper", n=6, depth=0.04)

    out += stack([(1.36, 12.3), (1.5, 12.35), (2.25, 12.7), (2.25, 12.95)], ("slate", "white_dk", "white"))
    out += stack([(2.08, 12.9), (2.2, 14.12)], ("teal_dk",))
    out += stack([(2.28, 14.08), (2.28, 14.32), (2.05, 14.55), (1.25, 14.92), (0.62, 15.02)], ("white", "white_dk", "panel", "steel_lt"), caps=("slate", "slate_lt"))

    base = [Vector(p) for p in octa(1.0, 0)]

    for i in range(8):
        a0, a1 = base[i], base[(i + 1) % 8]

        for u in (0.0, 0.5):
            lo = a0.lerp(a1, u)
            out += rod((lo.x * 2.095, lo.y * 2.095, 12.9), (lo.x * 2.215, lo.y * 2.215, 14.12), 0.055 if u == 0 else 0.035, "white_dk", d=1 if u else None)

        if lk.LOD < 2:
            lo, hi = a0.lerp(a1, 0.12), a0.lerp(a1, 0.4)
            out += face([(lo.x * 2.13, lo.y * 2.13, 13.05), (hi.x * 2.13, hi.y * 2.13, 13.05), (hi.x * 2.215, hi.y * 2.215, 13.95), (lo.x * 2.215, lo.y * 2.215, 13.95)], "teal", d=1, cast=False, towards=(lo.x, lo.y, 0))

    out += box(-0.45, -0.35, 14.98, 0.45, 0.55, 15.20, "white_dk", c=0.05, skip="d")
    out += box(-0.30, -0.22, 15.19, 0.30, 0.40, 15.262, "slate_lt", c=0.02, skip="d", d=1)

    return out


def pane(pts, col, towards, glint=None, off=0.012):
    out = face(pts, col, towards=towards)

    if glint and lk.LOD == 0:
        a, b, c, d = (Vector(p) for p in pts)
        n = Vector(towards).normalized() * off
        lo0, lo1 = a.lerp(b, 0.12), a.lerp(b, 0.28)
        hi0, hi1 = d.lerp(c, 0.50), d.lerp(c, 0.66)
        p0, p1 = lo0.lerp(hi0, 0.12) + n, lo1.lerp(hi1, 0.12) + n
        p2, p3 = lo1.lerp(hi1, 0.86) + n, lo0.lerp(hi0, 0.86) + n
        out += face([tuple(p0), tuple(p1), tuple(p2), tuple(p3)], glint, cast=False, ao=False, towards=towards)

    return out


def glass():
    out = part()
    out += box(-3.2, -4.8, 0.0, 3.2, 4.8, 0.18, "stone_dk", c=0.05, skip="d")

    for s in (-1, 1):
        out += box(s * 3.17, -4.77, 0.16, s * 2.97, 4.77, 0.96, "brick", skip="d")
        out += box(s * 3.2, -4.8, 0.94, s * 2.94, 4.8, 1.12, "stone", c=0.03)

    for x0, x1 in ((-2.97, -0.8), (0.8, 2.97)):
        out += box(x0, -4.77, 0.16, x1, -4.57, 0.96, "brick", skip="dlr")
        out += box(x0 - (0.0), -4.80, 0.94, x1, -4.54, 1.12, "stone", c=0.03)

    out += box(-2.97, 4.57, 0.16, 2.97, 4.77, 0.96, "brick", skip="dlr")
    out += box(-2.94, 4.54, 0.94, 2.94, 4.80, 1.12, "stone", c=0.03, skip="lr")

    if lk.LOD == 0:
        for k, z in enumerate((0.36, 0.55, 0.74)):
            for s in (-1, 1):
                out += side(-4.77, 4.77, z, z + 0.022, s * 3.172, s, "brick_dk")

                for j in range(12):
                    y = -4.5 + j * 0.78 + (0.39 if k % 2 else 0)

                    if y < 4.6:
                        out += side(y, y + 0.03, z - 0.17, z, s * 3.173, s, "brick_dk")

            out += plate(-2.9, -0.85, z, z + 0.022, -4.772, "brick_dk")
            out += plate(0.85, 2.9, z, z + 0.022, -4.772, "brick_dk")
            out += plate(-2.9, 2.9, z, z + 0.022, -4.772, "brick_dk").rot(180, "Z")

    ys = (-4.70, -2.88, -0.96, 0.96, 2.88, 4.70)

    for s in (-1, 1):
        for i in range(5):
            y0, y1 = ys[i], ys[i + 1]
            ym = (y0 + y1) / 2
            x = s * 3.08

            for a, b in ((y0, ym), (ym, y1)):
                quad_ = [(x, a, 1.10), (x, b, 1.10), (x, b, 3.55), (x, a, 3.55)]
                out += pane(quad_, "pane" if (i + (a == ym)) % 2 else "pane_lt", (s, 0, 0), "glint" if a == y0 else None, 0.012)

            out += box(x - s * 0.02, ym - 0.025, 1.10, x + s * 0.045, ym + 0.025, 3.55, "stone_lt", skip="td", d=1)

        for y in ys:
            out += box(s * 2.98, y - 0.08, 1.08, s * 3.17, y + 0.08, 3.62, "stone", c=0.02, skip="d")

        out += box(s * 3.07, -4.7, 2.72, s * 3.13, 4.7, 2.80, "stone_lt", skip="fb", d=1)
        out += box(s * 2.96, -4.80, 3.52, s * 3.2, 4.80, 3.72, "stone_lt", c=0.03)

        eave = Vector((s * 3.13, 0, 3.70))
        ridge = Vector((s * 0.08, 0, 6.86))
        up = Vector((s * 0.72, 0, 0.70)).normalized()

        for i in range(5):
            y0, y1 = ys[i], ys[i + 1]
            ym = (y0 + y1) / 2

            for a, b in ((y0, ym), (ym, y1)):
                quad_ = [(eave.x, a, eave.z), (eave.x, b, eave.z), (ridge.x, b, ridge.z), (ridge.x, a, ridge.z)]
                out += pane(quad_, "pane_lt" if (i + (a == ym)) % 2 else "pane", tuple(up), "glint" if a == ym else None, 0.014)

            out += rod((eave.x + up.x * 0.03, ym, eave.z + up.z * 0.03), (ridge.x + up.x * 0.03, ym, ridge.z + up.z * 0.03), 0.035, "stone_lt", d=1)

        for y in ys:
            out += rod((eave.x + up.x * 0.05, y, eave.z + up.z * 0.05), (ridge.x + up.x * 0.05, y, ridge.z + up.z * 0.05), 0.085, "stone", sides=4, caps=(True, True))

        for t in (0.5,):
            p = eave.lerp(ridge, t) + up * 0.05
            out += rod((p.x, -4.7, p.z), (p.x, 4.7, p.z), 0.04, "stone_lt", d=1)

    out += box(-0.16, -4.78, 6.78, 0.16, 4.78, 7.00, "stone", c=0.04)
    out += box(-0.07, -4.72, 6.98, 0.07, 4.72, 7.12, "stone_dk", c=0.025, skip="d", d=1)

    for sgn in (-1, 1):
        g = part()
        y = -4.66

        if sgn < 0:
            panes_x = ((-2.98, -1.9), (-1.9, -0.86), (0.86, 1.9), (1.9, 2.98))
        else:
            panes_x = ((-2.98, -1.5), (-1.5, 0.0), (0.0, 1.5), (1.5, 2.98))

        for k, (x0, x1) in enumerate(panes_x):
            g += pane([(x0, y, 1.10), (x1, y, 1.10), (x1, y, 3.55), (x0, y, 3.55)], "pane" if k % 2 else "pane_lt", (0, -1, 0), "glint" if k in (0, 2) else None)
            g += box(x0 - 0.045, y - 0.06, 1.10, x0 + 0.045, y, 3.55, "stone_lt", skip="btd", d=1)

        g += face([(-3.05, y, 3.6), (-1.05, y, 3.6), (-1.05, y, 5.78)], "pane_lt", towards=(0, -1, 0))
        g += face([(-1.05, y, 3.6), (1.05, y, 3.6), (1.05, y, 5.78), (0.0, y, 6.84), (-1.05, y, 5.78)], "pane", towards=(0, -1, 0))
        g += face([(1.05, y, 3.6), (3.05, y, 3.6), (1.05, y, 5.78)], "pane_lt", towards=(0, -1, 0))
        g += box(-3.05, y - 0.08, 3.50, 3.05, y, 3.70, "stone", skip="b")

        for x, zt in ((-1.05, 5.80), (1.05, 5.80)):
            g += box(x - 0.055, y - 0.065, 3.68, x + 0.055, y, zt, "stone_lt", skip="bd")

        g += box(-1.62, y - 0.055, 4.98, -1.05, y, 5.06, "stone_lt", skip="b", d=1)
        g += box(1.05, y - 0.055, 4.98, 1.62, y, 5.06, "stone_lt", skip="b", d=1)

        for s in (-1, 1):
            g += rod((s * 3.1, y - 0.05, 3.62), (0.0, y - 0.05, 6.86), 0.09, "stone", caps=(True, True))

        if lk.LOD == 0:
            g += face([(-0.7, y - 0.012, 3.9), (-0.4, y - 0.012, 3.9), (0.35, y - 0.012, 5.7), (0.05, y - 0.012, 5.7)], "glint", cast=False, ao=False, towards=(0, -1, 0))

        if sgn > 0:
            g.rot(180, "Z")

        out += g

    out += frame(-0.80, 0.80, 0.0, 3.34, -4.66, 0.14, "stone_lt", depth=0.11)
    out += box(-0.66, -4.72, 0.04, 0.66, -4.66, 3.20, "slate_lt", skip="b", c=0.02)

    for x0, x1 in ((-0.52, -0.07), (0.07, 0.52)):
        out += plate(x0, x1, 1.55, 2.95, -4.724, "glass_dd", cast=True)
        out += front(x0, x1, 0.30, 1.30, -4.72, "slate", depth=0.02, c=0.008, d=1)

    out += handle(0.30, 1.42, 0.2, -4.724, "graphite")
    out += box(-0.9, -4.80, 3.32, 0.9, -4.66, 3.46, "teal_dk", c=0.025, skip="b")
    m_a, m_b = Vector((2.30, 0, 4.58)), Vector((1.25, 0, 5.67))
    up = Vector((0.72, 0, 0.70)).normalized()
    pts = [m_a + up * 0.2 + Vector((0, -2.5, 0)), m_a + up * 0.2 + Vector((0, -1.35, 0)), m_b + up * 0.2 + Vector((0, -1.35, 0)), m_b + up * 0.2 + Vector((0, -2.5, 0))]
    out += face([tuple(p) for p in pts], "graphite", towards=tuple(up))
    inner = [pts[0].lerp(pts[2], 0.1), pts[1].lerp(pts[3], 0.1), pts[2].lerp(pts[0], 0.1), pts[3].lerp(pts[1], 0.1)]
    out += face([tuple(p + up * 0.012) for p in inner], "glass_dk", cast=False, towards=tuple(up))

    for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
        out += rod(tuple(pts[a]), tuple(pts[b]), 0.045, "stone_lt", d=1)

    for p in (pts[0], pts[1]):
        out += rod(tuple(p), tuple(p - up * 0.2), 0.04, "slate", d=0)

    return out


def gmod():
    out = part()
    prof = [(-2.80, 0.0), (-2.80, 0.42), (-2.70, 0.50), (-2.70, 2.73), (-2.16, 3.50), (-1.12, 4.08), (1.12, 4.08), (2.16, 3.50), (2.70, 2.73), (2.70, 0.50), (2.80, 0.42), (2.80, 0.0)]
    xs = (-5.50, -3.45, -1.40, 0.65, 2.70, 4.78)

    def ring_x(x, k=1.0):
        return [(x, y * k, z * k) for y, z in prof]

    for s in range(len(xs) - 1):
        a, b = ring_x(xs[s]), ring_x(xs[s + 1])

        for i in range(len(prof) - 1):
            y0, z0 = prof[i]
            y1, z1 = prof[i + 1]
            nrm = Vector((0, (z0 - z1), (y1 - y0))).normalized()

            if nrm.dot(Vector((0, (y0 + y1) / 2, (z0 + z1) / 2 - 1.8))) < 0:
                nrm.negate()

            glassy = 2 <= i <= 8
            col = ("slate_dk" if i in (0, 10) else "slate_lt") if not glassy else ("glass_dd" if i in (2, 8) else "glass_dk")

            if glassy and (s + i) % 2 == 0 and i not in (2, 8):
                col = "pane"

            quad_ = [a[i], b[i], b[i + 1], a[i + 1]]
            out += pane(quad_, col, tuple(nrm), "glass_dk" if glassy and i in (2, 8) else None, 0.014)

    for x in xs:
        w = 0.085
        inner = ring_x(x - w, 1.0)
        outer = []

        for y, z in prof:
            outer.append((y + math.copysign(0.02 if z < 3.0 else 0.05, y), z + (0.055 if z > 0.45 else 0.0)))

        for i in range(1, len(prof) - 2):
            y0, z0 = outer[i]
            y1, z1 = outer[i + 1]
            xa, xb = max(-5.6, x - w), min(5.6, x + w)
            nrm = Vector((0, (z0 - z1), (y1 - y0))).normalized()

            if nrm.dot(Vector((0, (y0 + y1) / 2, (z0 + z1) / 2 - 1.8))) < 0:
                nrm.negate()

            out += face([(xa, y0, z0), (xb, y0, z0), (xb, y1, z1), (xa, y1, z1)], "steel_lt", towards=tuple(nrm))

            for xx, sg in ((xa, -1), (xb, 1)):
                out += face([(xx, y0, z0), (xx, y1, z1), (xx, prof[i + 1][0], prof[i + 1][1]), (xx, prof[i][0], prof[i][1])], "steel", d=1, cast=False, towards=(sg, 0, 0))

    for s in (-1, 1):
        out += box(-5.56, s * 2.80, 0.0, 4.82, s * 2.66, 0.44, "graphite", c=0.04, skip="d")
        out += box(-5.50, s * 2.775, 1.84, 4.78, s * 2.70, 1.92, "steel", skip="lr", d=1)
        out += box(-5.50, s * 2.77, 2.68, 4.78, s * 2.64, 2.80, "steel_lt", skip="lr", d=1)
        out += rod((-5.45, s * 1.70, 3.80), (4.78, s * 1.70, 3.80), 0.05, "steel", d=1)

        for x in (-4.5, -0.4, 3.7):
            v = part()
            v += box(x - 0.35, s * 2.80, 0.12, x + 0.35, s * 2.76, 0.34, "slate_lt", d=0)
            out += v

    out += box(-5.50, -0.20, 4.06, 4.80, 0.20, 4.20, "steel", c=0.035, skip="d")
    back = [(y, z) for y, z in prof]
    out += face([(-5.50, y, z) for y, z in back], "glass_dd", towards=(-1, 0, 0))

    for y in (-1.35, 0.0, 1.35):
        zt = 3.95 if y == 0 else 3.9
        out += box(-5.56, y - 0.06, 0.45, -5.50, y + 0.06, zt, "steel_lt", skip="r")

    out += box(-5.57, -2.7, 2.66, -5.50, 2.7, 2.79, "steel_lt", skip="r", d=1)
    out += box(-5.60, -2.8, 0.0, -5.50, 2.8, 0.46, "graphite", skip="rd")

    def oct_yz(x, h, cz, k=1.0):
        return [(x, math.cos(2 * math.pi * i / 8 + math.pi / 8) * h * k / C8, cz + math.sin(2 * math.pi * i / 8 + math.pi / 8) * h * k / C8) for i in range(8)]

    out += face([(4.78, y, z) for y, z in prof], "panel", towards=(1, 0, 0))
    cz = 2.07
    out += loft([oct_yz(4.76, 2.06, cz), oct_yz(5.28, 2.06, cz), oct_yz(5.40, 1.92, cz)], lambda j, i: "white_dk" if j == 0 else "white", wind=True)
    out += loft([oct_yz(5.40, 1.92, cz), oct_yz(5.57, 1.82, cz), oct_yz(5.57, 1.45, cz), oct_yz(5.42, 1.36, cz)], lambda j, i: ("rust_dk", "rust", "rust_dk")[j], wind=True)
    out += face(oct_yz(5.42, 1.36, cz), "slate_dk", towards=(1, 0, 0))
    port = ring(0, cz, 0, 0.66, 0.98, "steel_dk", n=10, depth=0.12, side="slate") + disc(0, cz, -0.01, 0.66, "glass_dd", n=10, depth=0.02) + disc(0, cz, -0.035, 0.34, "glass_dk", n=8, depth=0.01, d=1)
    out += port.rot(90, "Z").move(5.42, 0, 0)
    out += box(4.80, -2.55, 0.0, 5.55, 2.55, 0.22, "graphite", c=0.04, skip="d")

    if lk.LOD == 0:
        for i in range(8):
            a = i * math.pi / 4
            out += box(5.55, math.cos(a) * 1.64 - 0.07, cz + math.sin(a) * 1.64 - 0.07, 5.60, math.cos(a) * 1.64 + 0.07, cz + math.sin(a) * 1.64 + 0.07, "copper", skip="l")

    return out


def dome():
    out = part()
    n = (16, 16, 10)[lk.LOD]
    out += lathe([(6.11, 0.0, "graphite_dk"), (6.11, 0.34, "graphite"), (5.78, 0.46, "slate_dk"), (5.78, 0.86, "slate"), (5.5, 1.0, "slate_lt"), (5.38, 1.0, "slate_lt")], n, smooth=False, phase=math.pi / 16)
    level = (2, 2, 1)[lk.LOD]
    vs, fs = lk.ico(level)
    def place(v, k=1.0):
        return Vector((v.x * 5.62 * k, v.y * 5.62 * k, 0.62 + v.z * 6.68 * k))

    def clip(pts, zmin):
        res = []

        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]

            if a.z >= zmin:
                res.append(a)

            if (a.z >= zmin) != (b.z >= zmin):
                res.append(a.lerp(b, (zmin - a.z) / (b.z - a.z)))

        return res

    for k, (a, b, c) in enumerate(fs):
        tri = [place(vs[a]), place(vs[b]), place(vs[c])]
        pts = clip(tri, 0.98)

        if len(pts) < 3:
            continue

        mid = sum(pts, Vector()) / len(pts)
        h = lk.hash01(k, 9.4)
        col = "white" if h > 0.55 else ("white_dk" if h > 0.18 else "panel")
        outward = mid - Vector((0, 0, 0.62))

        if lk.LOD == 0:
            inset = [p.lerp(mid, 0.075) + outward.normalized() * 0.035 for p in pts]
            out += face([tuple(p) for p in inset], col, towards=tuple(outward))

            for i in range(len(pts)):
                j = (i + 1) % len(pts)
                out += face([tuple(pts[i]), tuple(pts[j]), tuple(inset[j]), tuple(inset[i])], "steel_lt", cast=False, towards=tuple(outward))
        else:
            out += face([tuple(p) for p in pts], col, towards=tuple(outward))

    out += puck((0, 0, 7.16), 0.74, 0.22, "steel", sides=8, top="steel_lt")
    out += puck((0, 0, 7.36), 0.38, 0.14, "slate_lt", sides=8, top="white_dk", d=1)
    hatch = [(math.cos(2 * math.pi * i / 8 + math.pi / 8) * 2.25 / C8, 2.25 + math.sin(2 * math.pi * i / 8 + math.pi / 8) * 2.25 / C8) for i in range(8)]
    inner_h = [(y * 0.9, 2.25 + (z - 2.25) * 0.9) for y, z in hatch]
    out += extrude(inner_h, -5.55, -4.2, "white_dk", side=lambda i, a, b: "white" if min(a[1], b[1]) > 3.0 else "panel", force=True, caps="f")
    out += extrude(inner_h, -5.62, -5.25, "rust_dk", force=True, caps="")
    out += ring(0, 2.25, -5.62, 1.66, 2.25 / C8, "rust", n=8, depth=0.36, side="rust_dk")
    out += disc(0, 2.25, -5.52, 1.70, "graphite", n=8, depth=0.07)
    out += disc(0, 2.25, -5.59, 1.50, "steel_dk", n=8, depth=0.07, rim="slate")
    out += box(-0.69, -5.75, 2.26, 0.69, -5.66, 3.26, "slate_lt", c=0.025, skip="b")
    out += plate(-0.56, 0.56, 2.40, 3.12, -5.754, "glass_dd", cast=True)
    out += face([(-0.40, -5.758, 2.48), (-0.20, -5.758, 2.48), (0.18, -5.758, 3.04), (-0.02, -5.758, 3.04)], "teal_dk", d=0, cast=False, towards=(0, -1, 0))
    out += box(-0.50, -5.85, 1.18, 0.50, -5.74, 1.30, "steel_lt", c=0.025, d=1)

    for x in (-0.42, 0.42):
        out += box(x - 0.05, -5.76, 1.18, x + 0.05, -5.66, 1.30, "slate", skip="b", d=0)

    out += plate(0.75, 1.05, 1.9, 2.3, -5.665, "screen", d=1)
    out += box(-1.9, -6.0, 0.0, 1.9, -5.4, 0.22, "slate_lt", c=0.04, skip="d")
    out += box(-1.5, -5.75, 0.2, 1.5, -5.35, 0.46, "slate", c=0.04, skip="d", d=1)

    if lk.LOD == 0:
        for i in range(8):
            a = i * math.pi / 4
            out += disc(math.cos(a) * 1.96, 2.25 + math.sin(a) * 1.96, -5.98, 0.07, "copper", n=6, depth=0.02)

    for i in (1, 3, 5, 7, 9, 11, 13, 15):
        a = i * math.pi * 2 / 16

        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.6:
            continue

        v = part()
        v += louvres(-0.55, 0.55, 0.50, 0.82, -5.77, 3, "steel_dk", back="black", depth=0.03, d=0)
        out += v.rot(math.degrees(a) + 90, "Z")

    return out


def reactor():
    out = part()

    def oct_c(h, z, cut=None):
        cut = h * 0.22 if cut is None else cut

        return [(-h + cut, -h, z), (h - cut, -h, z), (h, -h + cut, z), (h, h - cut, z), (h - cut, h, z), (-h + cut, h, z), (-h, h - cut, z), (-h, -h + cut, z)]

    levels = [(5.38, 0.0), (5.52, 0.18), (5.52, 0.62), (5.60, 0.70), (5.60, 1.72), (5.52, 1.85), (5.46, 1.9), (5.46, 4.08), (5.26, 4.16), (5.2, 4.18), (5.2, 4.42), (5.44, 4.44), (5.50, 4.50), (5.50, 4.62), (5.46, 4.66), (5.46, 7.10), (5.52, 7.30), (5.56, 7.80), (5.05, 8.40), (4.13, 8.40), (4.0, 7.95)]
    cols = ("graphite_dk", "graphite", "rust_dk", "rust", "rust_lt", "slate_dk", "white_dk", "panel", "graphite", "black", "graphite", "steel", "white", "panel_dk", "white_dk", "panel", "white", "white_dk", "steel_lt", "slate_lt")
    out += loft([oct_c(h, z) for h, z in levels], lambda j, i: cols[j], wind=True)
    out += face(oct_c(4.0, 7.95), "slate", towards=(0, 0, 1))
    out += prism(ngon(2.5, 8), 7.94, 8.14, "steel_dk", c=0.08, top="steel")

    if lk.LOD < 2:
        out += fan(0.0, 0.0, 8.18, 1.7)

        for x in (-3.1, 3.1):
            out += box(x - 0.35, -1.2, 7.94, x + 0.35, 1.2, 8.22, "slate_lt", c=0.07, skip="d")

    zc = 2.82
    out += ring(0, zc, -5.40, 1.38, 1.95, "rust", n=8, depth=0.20, side="rust_dk")
    out += ring(0, zc, -5.42, 1.18, 1.42, "graphite", n=8, depth=0.10, side="graphite_dk", d=1)
    out += disc(0, zc, -5.455, 1.40, "black", n=8, depth=0.01)

    for i in range(5):
        z = zc - 0.9 + i * 0.45
        w = 1.18 - abs(z - zc) * 0.4
        out += box(-w, -5.55, z - 0.07, w, -5.47, z + 0.07, "graphite", skip="b", d=1)

    if lk.LOD == 0:
        for i in range(8):
            a = i * math.pi / 4
            out += disc(math.cos(a) * 1.72, zc + math.sin(a) * 1.72, -5.58, 0.08, "copper", n=6, depth=0.04)

    out += box(-2.3, -5.60, 5.85, 1.7, -5.50, 6.62, "white", c=0.045, skip="b")
    out += box(-2.08, -5.615, 6.03, 1.48, -5.59, 6.44, "black", skip="b")
    out += plate(-1.85, -0.4, 6.18, 6.24, -5.619, "teal", d=1)
    out += box(2.0, -5.55, 3.46, 3.30, -5.44, 3.98, "slate_dk", c=0.035, skip="b")
    out += plate(2.14, 3.16, 3.58, 3.86, -5.554, "teal_dk")
    out += plate(2.22, 2.75, 3.68, 3.74, -5.556, "screen", d=1)
    out += box(2.25, -5.55, 2.32, 3.25, -5.44, 2.92, "panel", c=0.035, skip="b", d=1)
    out += box(2.45, -5.59, 2.54, 3.05, -5.53, 2.70, "graphite", skip="b", d=1)

    for x in (-3.4, -2.55):
        out += front(x, x + 0.7, 2.25, 3.9, -5.46, "white_dk", depth=0.05, c=0.02, d=1)
        out += handle(x + 0.55, 3.05, 0.4, -5.51, "slate", vertical=True)

    for x in (-3.2, -1.6, 0.0, 1.6, 3.2):
        out += plate(x - 0.02, x + 0.02, 4.86, 5.7, -5.466, "panel_dk", d=0)
        out += plate(x - 0.45, x + 0.45, 1.05, 1.30, -5.602, "rust_dk", d=1)

    for ang in (90, 270):
        f = part()

        for z0, z1, num in ((2.05, 3.85, 4), (4.95, 7.0, 6)):
            y = -5.46
            f += plate(-3.14, 3.14, z0, z1, y - 0.004, "black", cast=True)
            step = (z1 - z0) / num
            k = num if lk.LOD == 0 else max(2, num // 2)
            step = (z1 - z0) / k

            for i in range(k):
                za = z0 + step * i + step * 0.2
                f += box(-3.14, y - 0.11, za, 3.14, y - 0.004, za + step * 0.48, "graphite", skip="b", top="slate")

            f += frame(-3.34, 3.34, z0 - 0.18, z1 + 0.08, y, 0.18, "steel_lt" if z0 > 4 else "panel", depth=0.12, d=1)
            f += box(-0.07, y - 0.13, z0, 0.07, y - 0.004, z1, "slate_lt", skip="b", d=0)

        out += f.rot(ang, "Z")

    back = part()
    back += frame(-2.4, 2.4, 2.1, 3.9, -5.46, 0.12, "panel", depth=0.06, d=1)

    for x0, x1 in ((-2.2, -0.1), (0.1, 2.2)):
        back += front(x0, x1, 2.25, 3.75, -5.46, "panel_dk", depth=0.045, c=0.018)
        back += handle(x0 + 0.25 if x0 > 0 else x1 - 0.25, 3.0, 0.5, -5.505, "graphite", vertical=True)

    back += louvres(-2.0, 2.0, 5.2, 6.7, -5.465, 6, "slate_lt", back="graphite", depth=0.07)
    back += frame(-2.15, 2.15, 5.05, 6.85, -5.46, 0.12, "steel_lt", depth=0.1, d=1)

    for x in (-3.0, 3.0):
        back += tube([(x, -5.42, 1.85), (x, -5.59, 2.2), (x, -5.59, 3.8), (x, -5.3, 4.15)], 0.13, 6, "rust", caps=(False, False), smooth=False)

    out += back.rot(180, "Z")

    for ang in (45, 135, 225, 315):
        f = part()
        r = 5.46 * (2 - 0.22) / math.sqrt(2)
        f += box(-0.55, -r - 0.09, 2.1, 0.55, -r + 0.02, 3.9, "panel_dk", c=0.035, skip="b", d=1)
        f += plate(-0.35, 0.35, 3.35, 3.55, -r - 0.094, "teal_dk", d=0)
        out += f.rot(ang, "Z")

    return out


from yard import fan

OPTS = {"ao": 0.42, "reach": 2.4, "grime": 0.1, "grime_h": 1.2, "errors": (0.05, 0.16)}

ALL = {
    "ctower": (ctower, OPTS),
    "otower": (otower, OPTS),
    "glass": (glass, {"ao": 0.34, "reach": 2.0, "grime": 0.1, "grime_h": 1.0, "errors": (0.05, 0.16)}),
    "gmod": (gmod, {"ao": 0.34, "reach": 2.0, "grime": 0.1, "grime_h": 1.0, "errors": (0.05, 0.16)}),
    "dome": (dome, OPTS),
    "reactor": (reactor, OPTS),
}
