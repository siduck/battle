import math

from mathutils import Matrix, Vector

import arch
import ck

M = 4.4
TIER = 3.3
W = 2.14
PATTERN = [[("door", 0.31), ("win", 0.76)], [("win", 0.5)], [("win", 0.23), ("door", 0.69)], []]


def quad(pts, col, ao=True, cast=True):
    return ck.Poly(pts, col, False, ao, cast)


def plinth(face, doors, width, col):
    out = ck.Part()
    spans = []
    cur = 0.0

    for x, w in sorted(doors):
        spans.append((cur, x - w / 2 - 0.11))
        cur = x + w / 2 + 0.11

    spans.append((cur, width))

    for a, b in spans:
        if b - a > 0.05:
            out += ck.box(a, -0.04, 0.0, b, 0.01, 0.3, col, c=0.018, d=1, skip="bd")

    return arch.orient(out, *face)


def patch(x, z, seed):
    out = ck.Part()

    if ck.LOD > 0:
        return out


    for r, (start, n) in enumerate(((0.0, 3), (0.14, 2), (0.08, 1))):
        u = x + start

        for i in range(n):
            w = 0.2 + 0.1 * ck.hash01(seed, r, i)
            tone = ck.mix("wall_dk", ("stone", "stone_lt", "trim_dk")[int(ck.hash01(seed, i, r, 2.0) * 3) % 3], 0.5)
            out.append(arch.flat(u, u + w, z + r * 0.135, z + r * 0.135 + 0.115, -0.004, tone))
            u += w + 0.022

    return out


def spout(x, z):
    return ck.box(x - 0.07, -0.06, z, x + 0.07, 0.02, z + 0.09, "tile", c=0.015, d=0, skip="b") + ck.box(x - 0.025, -0.012, z - 0.45, x + 0.025, 0.0, z, "wall_dk", d=0, skip="bdt")


def lantern(x, z):
    out = ck.box(x - 0.015, -0.07, z + 0.16, x + 0.015, 0.0, z + 0.19, "iron", d=0, skip="b")
    out += ck.box(x - 0.055, -0.075, z - 0.02, x + 0.055, -0.01, z + 0.13, "glass_warm", d=0, taper=(1.2, 1.2))
    out += ck.box(x - 0.08, -0.095, z + 0.13, x + 0.08, 0.0, z + 0.17, "iron", c=0.012, d=0)

    return out


def ledge(x, z):
    out = ck.box(x - 0.66, -0.075, z - 0.11, x + 0.66, 0.02, z, "stone_lt", c=0.025, d=1, skip="b")

    for bx in (x - 0.5, x + 0.5):
        out += ck.box(bx - 0.06, -0.05, z - 0.26, bx + 0.06, 0.005, z - 0.11, "stone", c=0.015, d=0, skip="bt")

    return out


def chimney(cx, cy, top, wall):
    out = ck.box(cx - 0.29, cy - 0.29, top, cx + 0.29, cy + 0.29, top + 1.0, wall, skip="dt")
    out += ck.box(cx - 0.38, cy - 0.38, top + 1.0, cx + 0.38, cy + 0.38, top + 1.12, "trim", c=0.025)
    out += ck.box(cx - 0.25, cy - 0.25, top + 1.12, cx + 0.25, cy + 0.25, top + 1.25, "shadow", d=1, skip="dt")

    for sx in (-1, 1):
        for sy in (-1, 1):
            out += ck.box(cx + sx * 0.22 - 0.06, cy + sy * 0.22 - 0.06, top + 1.12, cx + sx * 0.22 + 0.06, cy + sy * 0.22 + 0.06, top + 1.26, wall, d=1, skip="dt")

    out += ck.box(cx - 0.34, cy - 0.34, top + 1.25, cx + 0.34, cy + 0.34, top + 1.4, "tile", d=1, taper=(0.5, 0.5))

    return out


def flat_roof(top, wall, seed):
    out = arch.flags(-1.94, -1.94, 1.94, 1.94, top, ("pave_lt", "pave", "wall_dk"), seed, rows=3, per=3, grout=0.035, gcol="pave_dk")

    for p0, p1 in arch.faces(1.94):
        out.append(quad([(p1[0], p1[1], top), (p0[0], p0[1], top), (p0[0], p0[1], top + 0.2), (p1[0], p1[1], top + 0.2)], ck.shade(wall, 0.94)))

    out += arch.ring(2.2, 1.94, top + 0.2, top + 0.33, "trim", "trim", c=0.035)

    return out


def pergola(top):
    out = ck.Part()

    for px in (-1.86, 1.86):
        for py in (-1.86, 0.2):
            out += ck.box(px - 0.075, py - 0.075, top, px + 0.075, py + 0.075, top + 2.28, "wood", c=0.022, skip="d", d=2)
            out += ck.box(px - 0.12, py - 0.12, top, px + 0.12, py + 0.12, top + 0.12, "stone_lt", c=0.02, d=0, skip="d")

        out += ck.box(px - 0.08, -2.08, top + 2.2, px + 0.08, 0.42, top + 2.32, "wood_dk", c=0.02, d=2)

    for k in range(7):
        y = -2.0 + k * 0.38
        out += ck.box(-2.1, y - 0.04, top + 2.32, 2.1, y + 0.04, top + 2.4, "wood_lt", d=1)

    for k in range(18):
        x = -1.75 + (k * 0.71) % 3.5
        y = -1.85 + (k * 0.53) % 2.1
        tones = ("bloom_lt", "bloom", "bloom_dk") if k % 3 == 0 else ("leaf_lt", "leaf", "leaf_dk")
        out += ck.blob((x, y, top + 2.45), (0.34, 0.28, 0.15), tones, sub=0, seed=k + 3, d=2)

    for k in range(5):
        out += ck.blob((-1.9 + 0.04 * (k % 2), -1.9, top + 2.18 - k * 0.27), (0.17 - k * 0.018, 0.17 - k * 0.018, 0.19), ("bloom_lt", "bloom", "leaf_dk"), sub=0, seed=40 + k, d=0)

    return out


def vault(cx_half, ry, rz, z, col, wall, n):
    out = ck.Part()
    pts = [(math.cos(math.pi * i / n) * ry, z + math.sin(math.pi * i / n) * rz) for i in range(n + 1)]

    for i in range(n):
        (ya, za), (yb, zb) = pts[i], pts[i + 1]
        tone = ck.shade(col, 1.05 if i % 2 else 0.96)
        out.append(quad([(-cx_half, ya, za), (-cx_half, yb, zb), (cx_half, yb, zb), (cx_half, ya, za)], tone))

    for s in (-1, 1):
        x = s * cx_half
        face = [(x, p[0], p[1]) for p in pts]

        if s < 0:
            face.reverse()

        out.append(quad(face, wall))

        for i in range(n):
            (ya, za), (yb, zb) = pts[i], pts[i + 1]
            k = 1.07
            oa = (ya * k, z + (za - z) * k)
            ob = (yb * k, z + (zb - z) * k)
            xo = x + s * 0.09
            ring = [(xo, ya * 0.93, z + (za - z) * 0.93), (xo, yb * 0.93, z + (zb - z) * 0.93), (xo, ob[0], ob[1]), (xo, oa[0], oa[1])]
            lip = [(xo, oa[0], oa[1]), (xo, ob[0], ob[1]), (x - s * 0.02, ob[0], ob[1]), (x - s * 0.02, oa[0], oa[1])]
            under = [(xo, yb * 0.93, z + (zb - z) * 0.93), (xo, ya * 0.93, z + (za - z) * 0.93), (x, ya * 0.93, z + (za - z) * 0.93), (x, yb * 0.93, z + (zb - z) * 0.93)]

            for quad_pts in (ring, lip, under):
                if s > 0:
                    quad_pts.reverse()

                out.append(quad(quad_pts, "trim"))

        if ck.LOD < 2:
            m = 8
            for r, c, dx in ((0.27, "trim", 0.025), (0.18, "glass", 0.032)):
                ring = [(x + s * dx, math.cos(2 * math.pi * i / m) * r, z + rz * 0.42 + math.sin(2 * math.pi * i / m) * r) for i in range(m)]

                if s < 0:
                    ring.reverse()

                out.append(quad(ring, c, True, False))

    return out


def house(floors, spin, accent, wall, dome=False, pergo=False, seed=0):
    out = ck.Part()
    top = floors * TIER
    width = W * 2

    for i, face in enumerate(arch.faces(W)):
        openings = []
        extra = ck.Part()
        ground_doors = []
        has_any = False

        for f in range(floors):
            for kind, u in PATTERN[(i - spin - f) % 4]:
                x = u * width
                has_any = True

                if kind == "win":
                    openings.append(arch.win(x, f * TIER + 1.08, accent=accent))
                elif f == 0:
                    openings.append(arch.door(x, accent=accent))
                    ground_doors.append((x, 1.0))
                    extra += ck.box(x - 0.66, -0.075, 0.0, x + 0.66, 0.02, 0.09, "stone", c=0.025, d=1, skip="bd")
                    extra += lantern(x + (0.82 if u < 0.5 else -0.82), 1.78)
                else:
                    openings.append(arch.door(x, h=2.0, z=f * TIER + 0.14, accent=accent))
                    extra += ledge(x, f * TIER + 0.14)

        if PATTERN[(i - spin) % 4] and any(k == "door" for k, _ in PATTERN[(i - spin) % 4]):
            vx = width * 0.54
            extra += ck.box(vx - 0.15, -0.035, top - 0.62, vx + 0.15, 0.005, top - 0.36, "trim", c=0.012, d=0, skip="b")
            extra.append(arch.flat(vx - 0.09, vx + 0.09, top - 0.56, top - 0.42, -0.037, "void"))

        if not has_any:
            extra += patch(0.35 + ck.hash01(seed, i) * 0.5, 0.42, seed * 11 + i)
            extra += spout(width * 0.62, top - 0.12)
        elif len(PATTERN[(i - spin) % 4]) == 1:
            extra += patch(0.14, 0.36, seed * 13 + i)
            extra += spout(width - 0.45, top - 0.12)

        out += arch.facade(face[0], face[1], 0.0, top + 0.2, wall, openings, extra)
        out += plinth(face, ground_doors, width, "trim_dk")

    for f in range(1, floors):
        out += arch.ring(2.19, W - 0.01, f * TIER - 0.08, f * TIER + 0.04, "trim", "trim", c=0.025)

    out += flat_roof(top, wall, seed + 5)

    if dome:
        out += ck.box(-1.36, -1.36, top, 1.36, 1.36, top + 0.58, wall, skip="dt")
        out += ck.box(-1.45, -1.45, top + 0.56, 1.45, 1.45, top + 0.7, "trim", c=0.035)
        out += vault(1.3, 1.25, 1.12, top + 0.7, "dome", "dome", 10 if ck.LOD == 0 else 6 if ck.LOD == 1 else 4)

        for i in (0, 2):
            part = ck.Part()

            for x in (0.8, 1.92):
                part += ck.box(x - 0.22, -0.035, top + 0.14, x + 0.22, 0.005, top + 0.48, accent, c=0.012, d=1, skip="b")
                part.append(arch.flat(x - 0.15, x + 0.15, top + 0.2, top + 0.42, -0.037, "glass"))

            out += arch.orient(part, *arch.faces(1.36)[i])
    else:
        sx = 1.3 if spin % 2 else -1.3
        out += chimney(sx, 1.5, top, wall)

    if pergo:
        out += pergola(top)

    return out


def arched_gable(face_w, z0, spring, rise, n, col):
    pts = [(0, z0), (face_w, z0)]
    tall = spring > z0 + 1e-3

    if tall:
        pts.append((face_w, spring))

    for i in range(1, n):
        a = math.pi * i / n
        pts.append((face_w / 2 + math.cos(a) * face_w / 2, spring + math.sin(a) * rise))

    if tall:
        pts.append((0, spring))

    return ck.Part([quad([(p[0], 0, p[1]) for p in pts], col)])


def coping_arc(half, spring, rise, y0, y1, n, col, thick=0.17):
    out = ck.Part()
    pts = [(math.cos(math.pi * i / n) * half, spring + math.sin(math.pi * i / n) * rise) for i in range(n + 1)]

    for i in range(n):
        (xa, za), (xb, zb) = pts[i], pts[i + 1]
        tone = ck.shade(col, 1.0 if i % 2 else 0.94)
        out.append(quad([(xa, y0, za), (xb, y0, zb), (xb, y0, zb + thick), (xa, y0, za + thick)][::-1], tone))
        out.append(quad([(xa, y1, za), (xb, y1, zb), (xb, y1, zb + thick), (xa, y1, za + thick)], tone))
        out.append(quad([(xa, y0, za + thick), (xa, y1, za + thick), (xb, y1, zb + thick), (xb, y0, zb + thick)], tone))
        out.append(quad([(xa, y0, za), (xa, y1, za), (xb, y1, zb), (xb, y0, zb)][::-1], ck.shade(tone, 0.9)))

    for k, (x, z) in enumerate((pts[0], pts[-1])):
        ring = [(x, y0, z), (x, y1, z), (x, y1, z + thick), (x, y0, z + thick)]

        if k:
            ring.reverse()

        out.append(quad(ring, col))

    return out


def barrel_shell(half, spring, rise, y0, y1, n, col):
    out = ck.Part()
    pts = [(math.cos(math.pi * i / n) * half, spring + math.sin(math.pi * i / n) * rise) for i in range(n + 1)]

    for i in range(n):
        (xa, za), (xb, zb) = pts[i], pts[i + 1]
        tone = ck.shade(col, 1.03 if i % 2 else 0.95)
        out.append(quad([(xa, y0, za), (xa, y1, za), (xb, y1, zb), (xb, y0, zb)], tone))

    return out


def cave():
    out = ck.Part()
    spring = 2.62
    rise = 0.5
    n = 10 if ck.LOD == 0 else 6 if ck.LOD == 1 else 3
    width = W * 2

    for i, face in enumerate(arch.faces(W)):
        openings = []
        extra = ck.Part()

        if i == 0:
            openings = [arch.door(1.59, w=1.14, h=1.66, accent="blue", lintel="arch", rise=0.57), arch.win(3.42, 1.05, 0.6, 0.62, accent="blue", lintel="arch", rise=0.3, shutters=False)]
            extra += ck.box(0.85, -0.075, 0.0, 2.33, 0.02, 0.09, "stone", c=0.025, d=1, skip="bd")
            extra += lantern(2.52, 1.55)
        elif i == 1:
            openings = [arch.win(1.2, 1.1, 0.55, 0.65, accent="blue", lintel="arch", rise=0.27, shutters=False)]
            extra += patch(2.7, 0.4, 31)
        else:
            extra += patch(0.5 + i * 0.4, 0.45, 40 + i)
            extra += spout(width * 0.7, 2.4)

        out += arch.facade(face[0], face[1], 0.0, spring, "wall", openings, extra)
        out += plinth(face, [(1.59, 1.14)] if i == 0 else [], width, "trim_dk")

    for i in (0, 2):
        face = arch.faces(W)[i]
        out += arch.orient(arched_gable(width, spring, spring, rise, n, "wall"), *face)

    for i in (1, 3):
        face = arch.faces(W)[i]
        out += arch.orient(ck.box(0.0, -0.05, spring - 0.06, width, 0.04, spring + 0.07, "trim", c=0.025, skip="b"), *face)

    out += barrel_shell(2.1, spring, rise - 0.03, -1.96, 1.96, n, "wall_lt")

    for y0, y1 in ((-2.2, -1.9), (1.9, 2.2)):
        out += coping_arc(2.2, spring - 0.02, rise, y0, y1, n, "trim")

    out += ck.box(-0.06, -1.9, 3.08, 0.06, 1.9, 3.17, "trim", c=0.02, d=0, skip="d")

    return out


def passage():
    out = ck.Part()
    half = 1.36
    spring = 1.5
    rise = 1.38
    top = 3.5
    n = 12 if ck.LOD == 0 else 6 if ck.LOD == 1 else 4
    curve = [(math.cos(math.pi * i / n) * half, spring + math.sin(math.pi * i / n) * rise) for i in range(n + 1)]

    for y, s in ((-W, -1), (W, 1)):
        faces = [[(-W, 0), (-half, 0), (-half, top), (-W, top)], [(half, 0), (W, 0), (W, top), (half, top)]]
        faces[0] = [(-W, 0), (-half, 0), (-half, spring), (-half, top), (-W, top)]
        faces[1] = [(half, 0), (W, 0), (W, top), (half, top), (half, spring)]

        for i in range(n):
            (xa, za), (xb, zb) = curve[i], curve[i + 1]
            faces.append([(xb, zb), (xa, za), (xa, top), (xb, top)])

        for f in faces:
            pts = [(p[0], y, p[1]) for p in f]

            if s > 0:
                pts.reverse()

            out.append(quad(pts, "wall"))

        if ck.LOD < 2:
            yo = y + s * 0.055
            outer = [(math.cos(math.pi * i / n) * (half + 0.22), spring + math.sin(math.pi * i / n) * (rise + 0.22)) for i in range(n + 1)]

            for i in range(n):
                ring = [(curve[i][0], yo, curve[i][1]), (outer[i][0], yo, outer[i][1]), (outer[i + 1][0], yo, outer[i + 1][1]), (curve[i + 1][0], yo, curve[i + 1][1])]
                edge = [(outer[i][0], yo, outer[i][1]), (outer[i][0], y, outer[i][1]), (outer[i + 1][0], y, outer[i + 1][1]), (outer[i + 1][0], yo, outer[i + 1][1])]
                soffit = [(curve[i][0], y, curve[i][1]), (curve[i][0], yo, curve[i][1]), (curve[i + 1][0], yo, curve[i + 1][1]), (curve[i + 1][0], y, curve[i + 1][1])]
                tone = ("stone_lt", "stone")[i % 2]

                for q in (ring, edge, soffit):
                    if s > 0:
                        q.reverse()

                    out.append(quad(q, tone))

            for sx in (-1, 1):
                for k in range(3):
                    z = k * 0.5
                    w = 0.34 if k % 2 == 0 else 0.24
                    x0, x1 = sorted((sx * half, sx * (half + w)))
                    out += ck.box(x0, min(y, yo), z + 0.02, x1, max(y, yo), z + 0.47, ("stone", "stone_lt")[k % 2], c=0.018, d=1, skip=("b" if s < 0 else "f"))

    for s in (-1, 1):
        x = s * half
        jamb = [(x, -W, 0.0), (x, W, 0.0), (x, W, spring), (x, -W, spring)]

        if s > 0:
            jamb.reverse()

        out.append(quad(jamb, "wall_dk"))

    for i in range(n):
        (xa, za), (xb, zb) = curve[i], curve[i + 1]
        out.append(quad([(xa, -W, za), (xb, -W, zb), (xb, W, zb), (xa, W, za)], ck.shade("wall_dk", 1.03 if i % 2 else 0.97)))

    sides = arch.faces(W)

    for i in (1, 3):
        extra = patch(0.4 if i == 1 else 2.9, 0.42, 60 + i) + spout(3.5 if i == 1 else 0.8, 3.15)
        out += arch.facade(sides[i][0], sides[i][1], 0.0, top, "wall", [arch.win(2.14, 1.2, 0.62, 0.8, accent="blue")], extra)
        out += plinth(sides[i], [], W * 2, "trim_dk")

    out += arch.flags(-half, -2.2, half, 2.2, 0.035, ("stone_lt", "stone", "pave"), 77, rows=6, per=3, grout=0.05)
    out += flat_roof(TIER, "wall", 9)

    for y in (-0.9, 0.9):
        out += ck.box(-1.3, y - 0.07, 2.76, 1.3, y + 0.07, 2.88, "wood_dk", c=0.02, d=1)

    out += ck.box(-0.012, -0.012, 2.56, 0.012, 0.012, 2.9, "iron", d=0)
    out += ck.box(-0.09, -0.09, 2.34, 0.09, 0.09, 2.54, "glass_warm", d=0, taper=(1.15, 1.15))
    out += ck.box(-0.13, -0.13, 2.54, 0.13, 0.13, 2.6, "iron", c=0.015, d=0, taper=(0.6, 0.6))

    return out


def block():
    out = arch.flags(-2.17, -2.17, 2.17, 2.17, 0.0, ("pave", "pave_lt", "pave", "pave_dk"), 3, rows=4, per=3, grout=0.05)
    out += arch.ring(2.24, 2.17, -0.3, 0.0, "stone_lt", "stone_lt", c=0.035, under=True)

    for i, face in enumerate(arch.faces(2.2)):
        part = ck.Part([arch.flat(0.0, 4.4, -2.7, -0.3, 0.0, "wall")])
        part += arch.courses(4.4, -2.7, (0.46, 0.46), ("stone", "stone_lt", "stone", "stone_dk"), 11 + i, grout=0.04, stone=1.15)
        part.append(arch.flat(0.0, 4.4, -6.0, -3.62, 0.0, "stone_dk"))

        if ck.LOD == 0:
            part += ck.box(0.0, -0.035, -2.74, 4.4, 0.005, -2.62, "stone_lt", c=0.02, skip="blr")

        out += arch.orient(part, *face)

    return out


def quay():
    out = arch.flags(-2.17, -2.17, 2.17, 2.17, 0.0, ("stone_lt", "pave", "stone_lt", "stone"), 21, rows=3, per=3, grout=0.06)
    out += arch.ring(2.24, 2.17, -0.28, 0.0, "pave_lt", "pave_lt", c=0.04)

    for i, face in enumerate(arch.faces(2.2)):
        part = arch.courses(4.4, -0.28, (0.38, 0.38, 0.38), ("stone", "stone_lt", "stone", "grey"), 31 + i, grout=0.045, stone=1.1)
        part += arch.courses(4.4, -1.42, (0.5,), ("grey_dk", "stone_dk"), 51 + i, grout=0.04, stone=1.4)

        if ck.LOD < 2:
            for x in (1.1, 3.3):
                part += ck.box(x - 0.09, -0.04, -1.5, x + 0.09, 0.01, -0.3, "wood_dk", c=0.025, d=1, skip="b")

        out += arch.orient(part, *face)

    return out


def stair():
    out = ck.Part()
    n = 12
    d = M / n
    r = TIER / n
    w = 1.3
    h = M / 2
    top = TIER + 0.9

    for i in range(n):
        y0 = -i * d
        y1 = -(i + 1) * d
        z = (i + 1) * r
        tone = ("stone_lt", "pave", "stone_lt", "pave_lt")[i % 4]
        out.append(quad([(-w, y0, z - r), (-w, y0, z - 0.07), (w, y0, z - 0.07), (w, y0, z - r)], "wall_dk"))
        out += ck.box(-w, y1, z - 0.07, w, y0 + 0.045, z, tone, c=0.018, skip="lrbd")

        for s in (-1, 1):
            x = s * w
            pts = [(x, y0, z), (x, y1, z), (x, y1, top), (x, y0, top)]

            if s < 0:
                pts.reverse()

            out.append(quad(pts, "wall"))

    for s in (-1, 1):
        xa, xb = sorted((s * w, s * h))
        out += ck.box(xa, -M, -1.0, xb, 0.0, top, "wall", skip="dt" + ("l" if s > 0 else "r"))
        out += ck.box(xa - 0.03, -M - 0.03, top, xb + 0.03, 0.045, top + 0.11, "trim", c=0.035)

        if ck.LOD < 2:
            x = s * 1.25
            out += ck.bar((x, -0.35, 1.18), (x, -3.85, 3.8), 0.028, "iron", sides=4, d=1)

            for k in range(3):
                y = -0.55 - k * 1.5
                z = 1.18 + (-0.35 - y) * (2.62 / 3.5)
                out += ck.box(min(x, s * w), y - 0.025, z - 0.07, max(x, s * w), y + 0.025, z - 0.01, "iron", d=0)

        face = ((h, -h), (h, h)) if s > 0 else ((-h, h), (-h, -h))
        side = patch(0.5, 2.5, 70 + s) + spout(3.4, 3.9)
        out += arch.orient(side, *face).move(0, -h, 0)

    return out


def parapet():
    h = M / 2
    out = ck.box(-h, -0.17, 0.0, h, 0.17, 0.82, "wall", skip="dt")
    out += ck.box(-2.23, -0.22, 0.82, 2.23, 0.22, 0.95, "trim", c=0.04)
    out += ck.box(-h, -0.2, 0.0, h, 0.2, 0.13, "trim_dk", c=0.02, d=0, skip="dlr")

    for y, s in ((-0.172, -1), (0.172, 1)):
        for k in range(4):
            x = -1.65 + k * 1.1
            pts = [(x - 0.13, y, 0.38), (x + 0.13, y, 0.38), (x, y, 0.62)]

            if s > 0:
                pts.reverse()

            if ck.LOD == 0:
                out.append(quad(pts, "shadow", True, False))

    return out


def windmill():
    out = ck.Part()
    out += ck.box(-2.75, -2.75, 0.0, 2.75, 2.75, 0.2, "stone", c=0.05, skip="d")
    out += ck.lathe([(2.72, 0.2, "stone_lt"), (2.68, 0.44, "stone_lt"), (2.58, 0.52, "wall"), (2.46, 3.6, "wall"), (2.34, 6.75, "trim"), (2.52, 6.85, "trim"), (2.52, 7.05, "trim"), (2.3, 7.08, "trim")], 18)

    door_y = -2.6
    out += ck.box(-0.72, door_y - 0.04, 0.2, 0.72, -2.3, 0.52, "stone_lt", c=0.04, d=1, skip="bd")
    part = ck.Part()

    for i in range(5 if ck.LOD == 0 else 1):
        a = -0.52 + 1.04 * i / (5 if ck.LOD == 0 else 1)
        b = -0.52 + 1.04 * (i + 1) / (5 if ck.LOD == 0 else 1)
        part.append(arch.flat(a, b, 0.52, 2.0, door_y - 0.02, ck.shade("blue", 1.08 if i % 2 else 0.92)))

    part += arch.arch_head(0.0, 2.0, 0.52, 0.52, "blue", "stone_lt", y=door_y + 0.01, ring=0.18)

    for sx in (-1, 1):
        part += ck.box(min(sx * 0.52, sx * 0.7), door_y - 0.08, 0.52, max(sx * 0.52, sx * 0.7), -2.35, 2.0, "stone", c=0.025, skip="bd")

    part += ck.box(0.28, door_y - 0.08, 1.2, 0.36, door_y - 0.02, 1.3, "gold", d=0, skip="b")
    out += part

    for x, z in ((1.5, 4.25), (-1.45, 3.1)):
        r = 2.58 - (z - 0.5) * 0.04
        ang = math.degrees(math.asin(x / r))
        w = ck.Part([arch.flat(-0.24, 0.24, z, z + 0.62, -r - 0.045, "glass")])
        w += arch.arch_head(0.0, z + 0.62, 0.24, 0.2, "glass", "blue", y=-r - 0.01, ring=0.1)

        for sx in (-1, 1):
            w += ck.box(min(sx * 0.24, sx * 0.34), -r - 0.08, z, max(sx * 0.24, sx * 0.34), -r + 0.18, z + 0.62, "blue", skip="bd")

        w += ck.box(-0.025, -r - 0.065, z, 0.025, -r - 0.04, z + 0.62, "blue", d=0, skip="b")
        w += ck.box(-0.4, -r - 0.13, z - 0.12, 0.4, -r + 0.14, z, "stone_lt", c=0.025, d=1, skip="b")
        out += w.rot(ang)

    roof = [(2.68, 7.0, None), (2.2, 7.5, None), (2.3, 7.52, None), (1.62, 8.1, None), (1.72, 8.12, None), (0.98, 8.7, None), (1.06, 8.72, None), (0.12, 9.42, None)]
    tones = ("umber", "umber_lt", "umber_dk")
    profile = [(r, z, (lambda i, j=j: tones[(i + j // 2) % 3] if ck.hash01(i, j) > 0.5 else tones[j // 2 % 2])) for j, (r, z, _) in enumerate(roof)]

    if ck.LOD == 2:
        profile = [profile[0], profile[-1]]

    out += ck.lathe(profile, 18, smooth=False)
    out += ck.lathe([(2.68, 7.0, "umber_dk"), (2.35, 7.06, "umber_dk")][::-1], 18, smooth=False)
    out += ck.blob((0, 0, 9.46), (0.18, 0.18, 0.22), "wood_dk", sub=0, seed=2)

    hub = Vector((0.0, -3.42, 7.4))
    out += ck.tube([(0, -2.0, 7.4), (0, -3.5, 7.4)], 0.19, 8, "wood_dk", caps=(False, True))
    out += ck.tube([(0, -3.28, 7.4), (0, -3.55, 7.4)], [0.38, 0.3], 8, "wood", caps=(True, True), smooth=False)
    tips = []

    for k in range(8):
        a = math.radians(22.5 + k * 45)
        u = Vector((math.sin(a), 0, math.cos(a)))
        v = Vector((math.cos(a), 0, -math.sin(a)))
        tip = hub + u * 4.95
        tips.append(tip)
        out += ck.bar(hub + u * 0.25, tip, 0.1, "wood", sides=4, taper=0.6, d=2)
        base = Vector((0, 0.03, 0))
        p0 = hub + u * 1.45 + base
        p1 = hub + u * 4.75 + base
        p2 = hub + u * 4.5 + v * 1.38 + base
        p3 = hub + u * 1.65 + v * 0.62 + base
        mid = (p0 + p1 + p2 + p3) / 4 + Vector((0, 0.08, 0))
        tone = "canvas" if k % 2 else "wall_lt"

        for a, b, c in ((p0, p3, p2), (p0, p2, p1)) if ck.LOD else ((p0, p3, mid), (p3, p2, mid), (p2, p1, mid), (p1, p0, mid)):
            out.append(quad([a, b, c], tone, True, False))
            out.append(quad([c + Vector((0, 0.012, 0)), b + Vector((0, 0.012, 0)), a + Vector((0, 0.012, 0))], ck.shade(tone, 0.9), True, False))

        out += ck.bar(p2, p1, 0.025, "wood_lt", sides=3, d=0, caps=(False, False))
        out += ck.bar(p3, p2, 0.025, "wood_lt", sides=3, d=0, caps=(False, False))

    for k in range(8):
        out += ck.bar(tips[k], tips[(k + 1) % 8], 0.022, "rope_dk", sides=3, d=1, caps=(False, False))

    return out


def lighthouse():
    out = ck.Part()
    out += ck.box(-2.6, -2.6, 0.0, 2.6, 2.6, 0.2, "stone", c=0.05, skip="dt")
    out += arch.flags(-2.55, -2.55, 2.55, 2.55, 0.2, ("pave", "stone_lt", "pave_lt"), 90, rows=5, per=4, grout=0.05)
    out += ck.lathe([(1.42, 0.2, "stone"), (1.38, 0.62, "stone_lt"), (1.16, 0.72, "wall"), (0.9, 4.0, "trim"), (1.02, 4.12, "trim"), (1.3, 4.3, "stone_lt"), (1.34, 4.46, "stone_lt"), (0.7, 4.47, "stone_lt")], 8, smooth=False, phase=math.pi / 8)

    for z, tone in ((2.55, "blue"),):
        r = 1.16 - (z - 0.72) * 0.079
        out += ck.lathe([(r + 0.025, z, tone), (r - 0.012, z + 0.45, tone)], 8, smooth=False, phase=math.pi / 8)

    d = ck.Part()
    fy = -1.33
    d += ck.box(-0.52, fy - 0.02, 0.2, 0.52, -0.9, 1.75, "stone_lt", c=0.03, skip="bd")

    for i in range(4 if ck.LOD == 0 else 1):
        a = -0.38 + 0.76 * i / (4 if ck.LOD == 0 else 1)
        b = -0.38 + 0.76 * (i + 1) / (4 if ck.LOD == 0 else 1)
        d.append(arch.flat(a, b, 0.22, 1.5, fy - 0.025, ck.shade("wood", 1.08 if i % 2 else 0.9)))

    d += arch.arch_head(0.0, 1.5, 0.38, 0.32, "wood", "stone", y=fy - 0.01, ring=0.13)
    out += d

    for k, z in ((1, 3.1), (5, 3.4), (3, 1.9)):
        r = (1.16 - (z - 0.72) * 0.079) * math.cos(math.pi / 8)
        w = ck.box(-0.17, -r - 0.045, z, 0.17, -r + 0.05, z + 0.42, "trim", c=0.012, d=1, skip="b")
        w.append(arch.flat(-0.1, 0.1, z + 0.06, z + 0.36, -r - 0.047, "glass"))
        out += w.rot(k * 45)

    ring = ck.ngon(1.24, 8, phase=math.pi / 8)

    for i in range(8):
        a = Vector((ring[i][0], ring[i][1], 4.46))
        b = Vector((ring[(i + 1) % 8][0], ring[(i + 1) % 8][1], 4.46))
        out += ck.bar(a, a + Vector((0, 0, 0.66)), 0.033, "iron", sides=4, d=1)
        out += ck.bar((a + b) / 2, (a + b) / 2 + Vector((0, 0, 0.64)), 0.018, "iron", sides=3, d=0, caps=(False, False))
        out += ck.bar(a + Vector((0, 0, 0.66)), b + Vector((0, 0, 0.66)), 0.035, "blue_dk", sides=4, d=2, caps=(False, False))

    out += ck.lathe([(0.74, 4.46, "iron"), (0.72, 4.62, "iron"), (0.66, 4.63, "glass_warm"), (0.66, 5.42, "iron"), (0.74, 5.44, "iron"), (0.74, 5.52, "iron")], 8, smooth=False, phase=math.pi / 8)

    for i in range(8):
        p = ck.ngon(0.69, 8, phase=math.pi / 8)[i]
        out += ck.bar((p[0], p[1], 4.62), (p[0], p[1], 5.44), 0.028, "blue_dk", sides=4, d=0, caps=(False, False))

    out += ck.lathe([(1.0, 5.5, "blue_dk"), (0.98, 5.6, "blue"), (0.7, 5.92, "blue"), (0.34, 6.14, "blue_lt"), (0.1, 6.24, "blue_dk"), (0.07, 6.32, "blue_dk")], 8, smooth=False, phase=math.pi / 8)
    out += ck.lathe([(0.72, 5.5, "blue_dk"), (1.0, 5.5, "blue_dk")], 8, smooth=False, phase=math.pi / 8)
    out += ck.blob((0, 0, 6.39), (0.11, 0.11, 0.11), "gold", sub=0, seed=4)

    return out


def boathouse():
    out = ck.Part()
    hx, hy = 2.12, 4.32
    spring, rise = 3.5, 2.12
    n = 12 if ck.LOD == 0 else 8 if ck.LOD == 1 else 5
    poly = [((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))]

    for i, face in enumerate(poly):
        long = i in (1, 3)
        width = hy * 2 if long else hx * 2
        openings = []
        extra = ck.Part()

        if i == 0:
            openings = [arch.door(hx, w=2.5, h=2.35, accent="blue", lintel="arch", rise=1.05, depth=0.24)]
            extra += ck.box(hx - 0.03, 0.14, 0.0, hx + 0.03, 0.23, 2.35, "blue_dk", d=0, skip="b")
        elif long:
            openings = [arch.win(width * 0.3, 1.65, 0.6, 0.7, accent="blue", shutters=False), arch.win(width * 0.7, 1.65, 0.6, 0.7, accent="blue", shutters=False)]
            extra += patch(width * 0.46, 1.15, 80 + i)
        else:
            openings = [arch.win(hx, 1.7, 0.75, 0.9, accent="blue")]

        part = arch.wall_face(width, 0.0, spring, openings, "wall")

        for o in openings:
            part += arch.fill(o, "wall")

        part += extra
        doors = [(hx, 2.5)] if i == 0 else []
        spans = [(0.0, width)] if not doors else [(0.0, hx - 1.36), (hx + 1.36, width)]

        for a, b in spans:
            base = arch.courses(b - a, 0.92, (0.46, 0.46), ("stone", "stone_lt", "stone_dk"), 83 + i + int(a), grout=0.04, stone=0.9, y=-0.045)
            base.append(ck.Poly([(0, -0.045, 0.92), (b - a, -0.045, 0.92), (b - a, 0.0, 0.92), (0, 0.0, 0.92)], "stone_lt"))

            for sx, flip in ((0.0, False), (b - a, True)):
                cap = [(sx, 0.0, 0.0), (sx, -0.045, 0.0), (sx, -0.045, 0.92), (sx, 0.0, 0.92)]
                base.append(ck.Poly(cap[::-1] if flip else cap, "stone"))

            part += base.move(a, 0, 0)

        out += arch.orient(part, *face)

        if not long:
            out += arch.orient(arched_gable(width, spring, spring, rise - 0.06, n, "wall"), *face)
        else:
            out += arch.orient(ck.box(0.0, -0.07, spring - 0.08, width, 0.05, spring + 0.09, "trim", c=0.03, skip="b"), *face)

    out += barrel_shell(2.14, spring, rise - 0.03, -4.2, 4.2, n, "wall_lt")

    for y0, y1 in ((-4.4, -4.14), (4.14, 4.4)):
        out += coping_arc(2.19, spring - 0.02, rise, y0, y1, n, "trim")

    if ck.LOD < 2:
        for y in (-1.4, 1.4):
            out += coping_arc(2.14, spring - 0.02, rise - 0.02, y - 0.09, y + 0.09, n, "wall", thick=0.07)

    out += ck.box(-1.55, -4.4, 0.0, 1.55, -4.3, 0.07, "stone", c=0.02, d=1, skip="bd")

    return out


def solar():
    out = ck.Part()
    lo = Vector((0.0, -0.7, 0.34))
    hi = Vector((0.0, 0.3, 1.74))
    up = (hi - lo).normalized()
    nrm = Vector((0.0, -up.z, up.y))

    def slab(x0, x1, t0, t1, off, col):
        a = lo.lerp(hi, t0) + nrm * off
        b = lo.lerp(hi, t1) + nrm * off

        return quad([(x0, a.y, a.z), (x1, a.y, a.z), (x1, b.y, b.z), (x0, b.y, b.z)], col)

    out.append(slab(-0.98, 0.98, 0.0, 1.0, 0.03, "steel_lt"))
    strips = 6 if ck.LOD == 0 else 2

    for i in range(strips):
        x0 = -0.92 + 1.84 * i / strips
        x1 = x0 + 1.84 / strips - (0.025 if ck.LOD == 0 else 0)
        out.append(slab(x0, x1, 0.04, 0.96, 0.042, "glass" if i % 2 else ck.mix("glass", "blue_dk", 0.5)))

    back = slab(-0.98, 0.98, 0.0, 1.0, -0.02, "grey_dk")
    back.pts.reverse()
    out.append(back)

    for x in (-0.9, 0.9):
        out += ck.bar((x, -0.7, 0.0), (x, -0.7, 0.34), 0.03, "iron_lt", sides=4, d=1)
        out += ck.bar((x, 0.42, 0.0), (x, 0.42, 2.0), 0.035, "iron_lt", sides=4, d=2)
        out += ck.bar((x, -0.7, 0.06), (x, 0.6, 0.06), 0.025, "iron_lt", sides=4, d=0)
        out += ck.bar(lo + Vector((x, 0.04, 0)), hi + Vector((x, 0.04, 0)), 0.025, "iron_lt", sides=4, d=0)
        out += ck.box(x - 0.06, 0.28, 1.84, x + 0.06, 0.62, 1.96, "iron", d=1)

    out += ck.tube([(-0.98, 0.44, 2.17), (-0.88, 0.44, 2.17), (0.88, 0.44, 2.17), (0.98, 0.44, 2.17)], [0.16, 0.285, 0.285, 0.16], 12, "wall_lt", caps=(True, True), smooth=False)

    for x in (-0.55, 0.55):
        out += ck.tube([(x - 0.04, 0.44, 2.17), (x + 0.04, 0.44, 2.17)], 0.298, 12, "steel", caps=(True, True), d=1, smooth=False)

    out += ck.tube([(0.99, 0.44, 2.17), (0.99, 0.5, 1.9), (0.9, 0.42, 1.2)], 0.022, 4, "tile", caps=(False, False), d=0)

    return out


def laundry():
    out = ck.Part()

    for x in (-1.92, 1.92):
        out += ck.bar((x, 0.0, 0.0), (x, 0.0, 1.19), 0.055, "wood", sides=6, taper=0.8, d=2)
        out += ck.box(x - 0.13, -0.13, 0.0, x + 0.13, 0.13, 0.11, "stone", c=0.025, d=1, skip="d")

    def sag(x):
        return 1.15 - 0.13 * (1 - (x / 1.92) ** 2)

    line = [(-1.92 + 3.84 * i / 6, 0.0, sag(-1.92 + 3.84 * i / 6)) for i in range(7)]
    out += ck.tube(line, 0.012, 3, "rope_dk", caps=(False, False), d=1)

    def cloth(x0, x1, drop, col, flare=0.0, split=False, phase=0.0):
        cols = 4
        grid = []

        for r in range(3):
            row = []

            for c in range(cols + 1):
                u = c / cols
                x = x0 + (x1 - x0) * u + flare * (u - 0.5) * r / 2
                z = sag(x0 + (x1 - x0) * u) - drop * r / 2 + 0.005
                y = math.sin(u * 7 + phase) * 0.055 * (r / 2)
                row.append((x, y, z))

            grid.append(row)

        part = ck.sheet(grid, col, thick=0.008)

        if ck.LOD == 0:
            for x in (x0 + 0.04, x1 - 0.04):
                part += ck.box(x - 0.018, -0.025, sag(x) - 0.03, x + 0.018, 0.025, sag(x) + 0.045, "wood_lt")

        return part

    out += cloth(-1.72, -1.12, 0.62, "wall_lt", phase=1.0)
    out += cloth(-1.02, -0.72, 0.42, "terra_lt", flare=0.24, phase=2.0)
    out += cloth(-0.5, 0.34, 0.7, "canvas", phase=0.4)
    out += cloth(0.48, 0.66, 0.66, "blue_dk", phase=3.0)
    out += cloth(0.69, 0.87, 0.66, "blue", phase=3.5)
    out += cloth(1.04, 1.34, 0.5, "butter", flare=0.3, phase=0.8)
    out += cloth(1.46, 1.74, 0.36, "teal_lt", phase=2.4)

    return out


def lens(cx, cy, length, width, z, col, skew=0.0):
    pts = [(cx - length / 2, cy, z), (cx - length * 0.28 + skew, cy - width / 2, z), (cx + length * 0.24 + skew, cy - width * 0.42, z), (cx + length / 2, cy, z), (cx + length * 0.28 + skew, cy + width / 2, z), (cx - length * 0.24 + skew, cy + width * 0.42, z)]

    return quad(pts, col, False, False)


def foam():
    out = ck.Part()
    lod = ck.LOD
    near = ck.mix("foam", (0.463, 0.839, 0.808), 0.22)
    segs = 28 if lod == 0 else 10
    last = None

    for i in range(segs + 1):
        t = i / segs
        x = -3.5 + 7.0 * t
        y = math.sin(t * 12.6 + 1) * 0.14 + math.sin(t * 31.0) * 0.035
        gap = math.sin(t * math.pi * 4.0 + 0.4)
        w = max(0.0, abs(gap) - 0.25) * (0.1 + 0.05 * ck.hash01(i, 3.1))
        here = ((x, y - w / 2, 0.022), (x, y + w / 2, 0.022))

        if last is not None and last[1][1] - last[0][1] + w > 0.004:
            pts = [last[0], here[0], here[1], last[1]]
            clean = [p for k, p in enumerate(pts) if math.dist(p, pts[k - 1]) > 1e-4]

            if len(clean) > 2:
                out.append(ck.Poly(clean, near, False, False, False))

        last = here

    count = 34 if lod == 0 else 12

    for k in range(count):
        t = (k + 0.15 + 0.7 * ck.hash01(k, 1.7)) / count
        x = -3.45 + 6.9 * t
        side = (ck.hash01(k, 5.3) - 0.5) * 2.0
        y = math.sin(t * 12.6 + 1) * 0.14 + side * abs(side) * 0.5 + (0.07 if side > 0 else -0.07)
        far = min(1.0, abs(side))
        size = (0.035 + 0.075 * ck.hash01(k, 8.9) * (1.0 - 0.55 * far)) * (1.0 if lod == 0 else 1.3)
        sides = (7 if size > 0.07 else 6) if lod == 0 else 4
        col = ck.mix("foam", (0.463, 0.839, 0.808), 0.12 + 0.5 * far)
        z = 0.024 + 0.00025 * k
        ring = []

        for j in range(sides):
            a = math.tau * j / sides + ck.hash01(k, 2.2) * 6.0
            ring.append((x + math.cos(a) * size * 1.35, y + math.sin(a) * size * 0.8, z))

        out.append(ck.Poly(ring, col, False, False, False))

    return out


def ripple():
    out = ck.Part()
    marks = ((-3.6, 0.2, 1.6), (-2.1, -0.28, 1.1), (-0.4, 0.34, 1.8), (1.3, -0.12, 1.3), (2.5, 0.38, 0.9), (3.5, -0.32, 1.5))

    for k, (x, y, ln) in enumerate(marks):
        if ck.LOD == 0 or k % 2 == 0:
            out.append(lens(x, y, ln, 0.09, 0.02, ck.mix("ripple", (0.463, 0.839, 0.808), 0.35), 0.12 if k % 2 else -0.1))

    return out


FLAT = {"ground": False, "ao": 0.0, "grime": 0.0, "under": 0.0, "speckle": 0.0}
HOUSE = {"reach": 1.1, "ao": 0.5, "grime": 0.12, "grime_h": 0.7}
SUNK = {"ground": False, "ao": 0.4, "reach": 0.8}


def houses():
    return {
        "cube1": (lambda: house(1, 0, "blue", "wall", seed=1), HOUSE),
        "cube1b": (lambda: house(1, 1, "green", "wall", seed=2), HOUSE),
        "cube1c": (lambda: house(1, 2, "terra", "cream", seed=3), HOUSE),
        "cube1p": (lambda: house(1, 1, "blue_dk", "wall", pergo=True, seed=4), HOUSE),
        "cube2": (lambda: house(2, 0, "blue", "wall", seed=5), HOUSE),
        "cube2b": (lambda: house(2, 1, "green", "wall_lt", seed=6), HOUSE),
        "cube2c": (lambda: house(2, 2, "ochre", "butter", seed=7), HOUSE),
        "cube3": (lambda: house(3, 3, "teal", "wall", seed=8), HOUSE),
        "dome1": (lambda: house(1, 0, "blue", "wall", dome=True, seed=9), HOUSE),
        "dome2": (lambda: house(2, 0, "blue", "wall", dome=True, seed=10), HOUSE),
    }


ALL = {
    **houses(),
    "cave1": (cave, HOUSE),
    "arch": (passage, HOUSE),
    "block": (block, SUNK),
    "quay": (quay, SUNK),
    "stair": (stair, {"ground": False, "ao": 0.5, "reach": 1.1}),
    "parapet": (parapet, {"reach": 0.6, "ao": 0.4, "grime_h": 0.3}),
    "windmill": (windmill, {"reach": 1.4, "ao": 0.5, "grime_h": 1.0}),
    "light": (lighthouse, {"reach": 1.1, "ao": 0.5}),
    "boathouse": (boathouse, HOUSE),
    "solar": (solar, {"reach": 0.6, "ao": 0.4, "grime_h": 0.3}),
    "laundry": (laundry, {"reach": 0.5, "ao": 0.35, "grime": 0.0}),
    "foam": (foam, FLAT),
    "ripple": (ripple, FLAT),
}
