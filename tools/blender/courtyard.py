import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
import os
import random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
ZIG = args[1]

os.makedirs(OUT, exist_ok=True)


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


SAND = rgb(232, 192, 148)
SAND_DEEP = rgb(214, 170, 126)
SAGE = rgb(150, 184, 138)
TERRA = rgb(204, 112, 88)
TERRA_FLOOR = rgb(216, 150, 124)
FLOOR = rgb(228, 228, 224)
WOOD = rgb(206, 164, 108)
SOIL = rgb(120, 104, 74)
OUTER = rgb(230, 206, 166)
ROAD = rgb(206, 198, 186)
WATER = rgb(108, 186, 196)
LAWN = rgb(178, 204, 152)
ROOF = rgb(228, 166, 134)
WOOD_DARK = rgb(150, 110, 70)

SUN = Vector((0.7, 0.62, 0.35)).normalized()
SHADE = (0.6, 0.65, 0.8)
TILE = 50.0
TN = 6
HALF = 150.0
STEP = 0.8

verts = []
faces = []
face_col = []
occluders_v = []
occluders_f = []
boxes = []
ramps = []
palms = []
spawns = []
weapons = []


def add_face(pts, col):
    base = len(verts)
    verts.extend(pts)
    faces.append(tuple(range(base, base + len(pts))))
    face_col.append(col)


def grid(o, u, v, want, col, step=STEP):
    o = Vector(o)
    u = Vector(u)
    v = Vector(v)

    if u.cross(v).dot(Vector(want)) < 0:
        u, v = v, u

    nu = max(1, math.ceil(u.length / step))
    nv = max(1, math.ceil(v.length / step))
    idx = {}

    for i in range(nu + 1):
        for j in range(nv + 1):
            idx[(i, j)] = len(verts)
            verts.append(o + u * (i / nu) + v * (j / nv))

    for i in range(nu):
        for j in range(nv):
            faces.append((idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
            face_col.append(col)


def visual_box(x0, y0, z0, x1, y1, z1, col, bottom=False):
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    grid((x0, y1, z0), (dx, 0, 0), (0, 0, dz), (0, 1, 0), col)
    grid((x0, y0, z0), (dx, 0, 0), (0, dy, 0), (0, 0, -1), col)
    grid((x0, y0, z1), (dx, 0, 0), (0, dy, 0), (0, 0, 1), col)
    grid((x0, y0, z0), (0, 0, dz), (0, dy, 0), (-1, 0, 0), col)
    grid((x1, y0, z0), (0, 0, dz), (0, dy, 0), (1, 0, 0), col)

    if bottom:
        grid((x0, y0, z0), (dx, 0, 0), (0, 0, dz), (0, -1, 0), col)


def box(x0, y0, z0, x1, y1, z1, col, solid=True):
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    visual_box(x0, y0, z0, x1, y1, z1, col, bottom=y0 > 0.05)

    if solid:
        boxes.append((x0, y0, z0, x1, y1, z1))


def frame(axis, cs, ct, s, y, t):
    if axis == "x":
        return Vector((cs + s, y, ct + t))

    return Vector((ct + t, y, cs + s))


def arch(axis, cs, ct, width, span, ys, top, depth, col):
    r = span / 2
    hw = width / 2
    hd = depth / 2

    def sbox(s0, y0, t0, s1, y1, t1):
        a = frame(axis, cs, ct, s0, y0, t0)
        b = frame(axis, cs, ct, s1, y1, t1)
        box(a.x, a.y, a.z, b.x, b.y, b.z, col)

    sbox(-hw, 0, -hd, -r, ys, hd)
    sbox(r, 0, -hd, hw, ys, hd)

    corner_l = math.atan2(top - ys, -hw)
    corner_r = math.atan2(top - ys, hw)
    angles = [math.pi * (1 - k / 24) for k in range(25)]
    angles = sorted(set([round(a, 6) for a in angles + [corner_l, corner_r]]), reverse=True)

    def outer(a):
        c, sn = math.cos(a), math.sin(a)
        ts = []

        if c < -1e-6:
            ts.append(-hw / c)

        if c > 1e-6:
            ts.append(hw / c)

        if sn > 1e-6:
            ts.append((top - ys) / sn)

        t = min(ts) if ts else hw

        return (c * t, ys + sn * t)

    for side in (1, -1):
        tt = hd * side
        n = frame(axis, 0, 0, 0, 0, side) - frame(axis, 0, 0, 0, 0, 0)

        for i in range(len(angles) - 1):
            a0, a1 = angles[i], angles[i + 1]
            p0 = (r * math.cos(a0), ys + r * math.sin(a0))
            p1 = (r * math.cos(a1), ys + r * math.sin(a1))
            q0 = outer(a0)
            q1 = outer(a1)

            for k in range(3):
                f0, f1 = k / 3, (k + 1) / 3
                pts2 = [
                    (p0[0] + (q0[0] - p0[0]) * f0, p0[1] + (q0[1] - p0[1]) * f0),
                    (p1[0] + (q1[0] - p1[0]) * f0, p1[1] + (q1[1] - p1[1]) * f0),
                    (p1[0] + (q1[0] - p1[0]) * f1, p1[1] + (q1[1] - p1[1]) * f1),
                    (p0[0] + (q0[0] - p0[0]) * f1, p0[1] + (q0[1] - p0[1]) * f1),
                ]
                pts = [frame(axis, cs, ct, p[0], p[1], tt) for p in pts2]
                nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0])

                if nrm.dot(n) < 0:
                    pts.reverse()

                add_face(pts, col)


    for i in range(len(angles) - 1):
        a0, a1 = angles[i], angles[i + 1]
        p0 = (r * math.cos(a0), ys + r * math.sin(a0))
        p1 = (r * math.cos(a1), ys + r * math.sin(a1))
        pts = [frame(axis, cs, ct, p0[0], p0[1], -hd), frame(axis, cs, ct, p1[0], p1[1], -hd), frame(axis, cs, ct, p1[0], p1[1], hd), frame(axis, cs, ct, p0[0], p0[1], hd)]
        mid = (pts[0] + pts[2]) / 2
        centre = frame(axis, cs, ct, 0, ys, 0)
        inward = centre - Vector((mid.x, mid.y, mid.z))
        nrm = (pts[1] - pts[0]).cross(pts[3] - pts[0])

        if nrm.dot(inward) < 0:
            pts.reverse()

        add_face(pts, col)

    a = frame(axis, cs, ct, -hw, top, -hd)
    b = frame(axis, cs, ct, hw, top, hd)
    lo = Vector((min(a.x, b.x), top, min(a.z, b.z)))
    hi = Vector((max(a.x, b.x), top, max(a.z, b.z)))
    grid((lo.x, top, lo.z), (hi.x - lo.x, 0, 0), (0, 0, hi.z - lo.z), (0, 1, 0), col)

    for sgn in (-1, 1):
        e0 = frame(axis, cs, ct, sgn * hw, ys, -hd)
        e1 = frame(axis, cs, ct, sgn * hw, ys, hd)
        out = frame(axis, 0, 0, sgn, 0, 0) - frame(axis, 0, 0, 0, 0, 0)
        grid((e0.x, ys, e0.z), (e1.x - e0.x, 0, e1.z - e0.z), (0, top - ys, 0), (out.x, 0, out.z), col)

    def solid(s0, y0, t0, s1, y1, t1):
        a = frame(axis, cs, ct, s0, y0, t0)
        b = frame(axis, cs, ct, s1, y1, t1)
        boxes.append((min(a.x, b.x), y0, min(a.z, b.z), max(a.x, b.x), y1, max(a.z, b.z)))

    solid(-hw, ys, -hd, -r + 0.5, top, hd)
    solid(r - 0.5, ys, -hd, hw, top, hd)
    solid(-hw, ys + r * 0.92, -hd, hw, top, hd)


def stairs(x0, z0, x1, z1, y0, rise, direction, col):
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    n = max(2, round(rise / 0.25))

    for k in range(n):
        f0 = k / n
        f1 = (k + 1) / n
        h = y0 + rise * f1

        if direction == "pos_z":
            box(x0, y0, z0 + (z1 - z0) * f0, x1, h, z1, col, solid=False)
        elif direction == "neg_z":
            box(x0, y0, z0, x1, h, z1 - (z1 - z0) * f0, col, solid=False)
        elif direction == "pos_x":
            box(x0 + (x1 - x0) * f0, y0, z0, x1, h, z1, col, solid=False)
        else:
            box(x0, y0, z0, x1 - (x1 - x0) * f0, h, z1, col, solid=False)

    ramps.append(((x0, y0, z0), (x1, y0 + rise, z1), direction))


def crate(x, y, z, s):
    h = s / 2
    t = 0.07
    box(x - h + 0.02, y, z - h + 0.02, x + h - 0.02, y + s - 0.02, z + h - 0.02, WOOD)
    boxes.pop()
    boxes.append((x - h, y, z - h, x + h, y + s, z + h))

    for a in (-1, 1):
        for b in (-1, 1):
            visual_box(x + a * h - (t if a > 0 else 0), y, z + b * h - (t if b > 0 else 0), x + a * h + (0 if a > 0 else t), y + s, z + b * h + (0 if b > 0 else t), WOOD_DARK)
            visual_box(x - h, y + (s - t if a > 0 else 0), z + b * h - (t if b > 0 else 0), x + h, y + (s if a > 0 else t), z + b * h + (0 if b > 0 else t), WOOD_DARK)
            visual_box(x + b * h - (t if b > 0 else 0), y + (s - t if a > 0 else 0), z - h, x + b * h + (0 if b > 0 else t), y + (s if a > 0 else t), z + h, WOOD_DARK)

    for k in (1, 2):
        yy = y + s * k / 3
        visual_box(x - h + t, yy - 0.03, z + h - 0.01, x + h - t, yy + 0.03, z + h + 0.02, WOOD_DARK)
        visual_box(x - h + t, yy - 0.03, z - h - 0.02, x + h - t, yy + 0.03, z - h + 0.01, WOOD_DARK)
        visual_box(x + h - 0.01, yy - 0.03, z - h + t, x + h + 0.02, yy + 0.03, z + h - t, WOOD_DARK)
        visual_box(x - h - 0.02, yy - 0.03, z - h + t, x - h + 0.01, yy + 0.03, z + h - t, WOOD_DARK)


def planter(x, z, kind):
    box(x - 1.2, 0, z - 1.2, x + 1.2, 0.8, z + 1.2, TERRA)
    visual_box(x - 1.0, 0.8, z - 1.0, x + 1.0, 0.86, z + 1.0, SOIL)
    palms.append((x, 0.8, z, kind))


def palm_occluder(x, y, z, kind):
    top = 7.6 if kind == 0 else 5.3
    lean = 1.1 if kind == 0 else 0.7
    rad = 2.8 if kind == 0 else 2.1
    tx, ty = x + lean, y + top
    base = len(occluders_v)
    seg = 6

    for k in range(seg):
        a = 2 * math.pi * k / seg
        occluders_v.append(Vector((x + 0.18 * math.cos(a), y, z + 0.18 * math.sin(a))))
        occluders_v.append(Vector((tx + 0.15 * math.cos(a), ty, z + 0.15 * math.sin(a))))

    for k in range(seg):
        a = 2 * k
        b = 2 * ((k + 1) % seg)
        occluders_f.append((base + a, base + b, base + b + 1, base + a + 1))

    for k in range(7):
        a = 2 * math.pi * k / 7
        dx, dz = math.cos(a), math.sin(a)
        px, pz = -dz, dx
        b2 = len(occluders_v)
        w = 0.55
        occluders_v.append(Vector((tx + px * 0.1, ty, z + pz * 0.1)))
        occluders_v.append(Vector((tx + dx * rad * 0.55 + px * w, ty - 0.2, z + dz * rad * 0.55 + pz * w)))
        occluders_v.append(Vector((tx + dx * rad, ty - 1.0, z + dz * rad)))
        occluders_v.append(Vector((tx + dx * rad * 0.55 - px * w, ty - 0.2, z + dz * rad * 0.55 - pz * w)))
        occluders_f.append((b2, b2 + 1, b2 + 2, b2 + 3))


def build():
    def sym(kind, *a):
        sym_list.append((kind, a))

    sym_list = []
    S = sym

    def roof(x0, z0, x1, z1, y, sides="nsew", extras=()):
        S("box", x0 - 0.2, y, z0 - 0.2, x1 + 0.2, y + 0.25, z1 + 0.2, ROOF)
        top = y + 0.25

        if "n" in sides:
            S("box", x0 - 0.2, top, z1 - 0.1, x1 + 0.2, top + 0.5, z1 + 0.2, TERRA)

        if "s" in sides:
            S("box", x0 - 0.2, top, z0 - 0.2, x1 + 0.2, top + 0.5, z0 + 0.1, TERRA)

        if "w" in sides:
            S("box", x0 - 0.2, top, z0 - 0.2, x0 + 0.1, top + 0.5, z1 + 0.2, TERRA)

        if "e" in sides:
            S("box", x1 - 0.1, top, z0 - 0.2, x1 + 0.2, top + 0.5, z1 + 0.2, TERRA)

        for kind, ex, ez in extras:
            if kind == "tank":
                S("box", ex - 0.9, top, ez - 0.9, ex + 0.9, top + 0.5, ez + 0.9, SAND_DEEP)
                S("box", ex - 0.7, top + 0.5, ez - 0.7, ex + 0.7, top + 1.9, ez + 0.7, SAGE)
                S("box", ex - 0.8, top + 1.9, ez - 0.8, ex + 0.8, top + 2.1, ez + 0.8, TERRA)
            else:
                S("box", ex - 0.4, top, ez - 0.4, ex + 0.4, top + 1.3, ez + 0.4, SAND)
                S("box", ex - 0.5, top + 1.3, ez - 0.5, ex + 0.5, top + 1.5, ez + 0.5, TERRA)

    for side in ((-150.4, 146.8, 150.4, 150.4), (-150.4, -150.4, 150.4, -146.8), (-150.4, -146.8, -146.8, 146.8), (146.8, -146.8, 150.4, 146.8)):
        x0, z0, x1, z1 = side
        box(x0, 0, z0, x1, 9, z1, SAND)
        box(x0 - 0.2, 9, z0 - 0.2, x1 + 0.2, 9.35, z1 + 0.2, TERRA, solid=False)

    box(-2.8, 0, -2.8, 2.8, 17, 2.8, SAGE)
    box(-3.2, 17, -3.2, 3.2, 17.5, 3.2, TERRA)

    for px, pz in ((-2.8, -2.8), (1.9, -2.8), (-2.8, 1.9), (1.9, 1.9)):
        box(px, 17.5, pz, px + 0.9, 21, pz + 0.9, SAND)

    box(-3.4, 21, -3.4, 3.4, 21.7, 3.4, TERRA)
    box(-1.8, 21.7, -1.8, 1.8, 22.6, 1.8, SAND)

    for px, pz, k in ((-6.5, -5, 0), (6.5, 5, 1), (-6.5, 5, 1), (6.5, -5, 0)):
        planter(px, pz, k)

    for a, b in ((-75, -58), (-46, -14)):
        S("box", a, 0, 72, b, 8, 75, SAND)
        S("box", a - 0.2, 8, 71.8, b + 0.2, 8.35, 75.2, TERRA)

    S("box", 14, 0, 72, 46, 8, 75, SAND)
    S("box", 13.8, 8, 71.8, 46.2, 8.35, 75.2, TERRA)
    S("box", 58, 0, 72, 75, 8, 75, SAND)
    S("box", 57.8, 8, 71.8, 75.2, 8.35, 75.2, TERRA)

    for a, b in ((-72, -50), (-38, -10), (10, 38), (50, 72)):
        S("box", -75, 0, a, -72, 8, b, SAND)
        S("box", -75.2, 8, a - 0.2, -71.8, 8.35, b + 0.2, TERRA)

    S("box", -60, 0, 60, -46, 11, 72, SAGE)
    S("box", -70, 0, 38, -64, 15, 44, TERRA)
    S("box", -72, 0, -30, -62, 10, -14, SAGE)
    S("box", 20, 0, 62, 44, 7, 70, SAND_DEEP)

    for cx in (-9, 0, 9):
        S("arch", "x", cx, 16, 9, 6, 4.5, 8.5, 1.4, SAND)

    S("box", -22, 0, 15.3, -13.5, 5, 16.7, SAND)
    S("box", 13.5, 0, 15.3, 22, 5, 16.7, SAND)

    S("box", -30, 0, 6, -22, 6, 40, SAND)
    S("box", -30, 0, -40, -22, 6, -6, SAND)
    S("box", -30.2, 6, 5.8, -21.8, 6.25, 40.2, TERRA)
    S("box", -30.2, 6, -40.2, -21.8, 6.25, -5.8, TERRA)
    S("arch", "z", 0, -26, 12, 8, 3, 8, 8, SAGE)
    S("box", -23, 6, 8, -22, 7.1, 38, SAND)
    S("box", -30, 6, 22, -29, 7.1, 38, SAND)
    S("box", -23, 6, -38, -22, 7.1, -8, SAND)
    S("stairs", -34, -38, -30, -26, 0, 6, "pos_z", SAND_DEEP)

    S("box", -62, 0, 22, -40, 1.5, 40, SAND_DEEP)
    S("stairs", -56, 17, -48, 22, 0, 1.5, "pos_z", SAND_DEEP)
    S("stairs", -40, 29, -35, 35, 0, 1.5, "neg_x", SAND_DEEP)
    S("box", -62, 1.5, 22, -53, 2.7, 22.8, SAGE)

    for c in ((-58, 1.5, 36, 1.4), (-56.6, 1.5, 36, 1.4), (-57.3, 2.9, 36, 1.4), (-46, 1.5, 26, 1.2), (-44, 1.5, 38, 1.4)):
        S("crate", *c)

    S("box", -55, 0, -12, -45, 1.3, -11.2, SAND)
    S("box", -40, 0, -24, -38.8, 1.3, -14, SAND)

    for c in ((-50, 0, 2, 1.4), (-48.6, 0, 2, 1.4), (-36, 0, -34, 1.2), (-60, 0, -40, 1.4), (-58.6, 0, -41, 1.4)):
        S("crate", *c)

    S("arch", "x", -48, -45, 14, 8, 4, 8, 1.6, SAGE)
    S("box", -72, 0, -45.8, -55, 6, -44.2, SAND)
    S("box", -41, 0, -45.8, -34.5, 6, -44.2, SAND)

    for p in ((-14, 30, 0), (14, 30, 1), (-64, 4, 1), (-38, 54, 0), (-66, -58, 1), (-44, -31, 0), (-36, 22, 1)):
        S("planter", *p)

    for c in ((-4, 0, 26, 1.4), (-2.6, 0, 26, 1.4), (-3.3, 1.4, 26, 1.4), (6, 0, 40, 1.2), (18, 0, 44, 1.4), (-10, 0, 58, 1.4), (10, 0, 62, 1.4)):
        S("crate", *c)

    S("box", -8, 0, 46, 8, 1.3, 46.8, SAGE)
    S("box", -20.7, 0, 47.3, -19.3, 6, 48.7, SAGE)
    S("box", 19.3, 0, 47.3, 20.7, 6, 48.7, SAGE)

    for k in range(11):
        cx = -97.5 + 5 * k
        S("arch", "x", cx, 94.5, 5, 3.4, 2.4, 4.6, 1.0, SAND)
        S("arch", "x", cx, 83.5, 5, 3.4, 2.4, 4.6, 1.0, SAND)

    for x0 in (-100, -89, -78, -67, -56):
        S("box", x0, 0, 95, x0 + 11, 6.5, 100.4, SAND if (x0 // 11) % 2 == 0 else SAND_DEEP)
        roof(x0, 95, x0 + 11, 100.4, 6.5, "nsew", (("chimney", x0 + 3, 98.5),) if (x0 // 11) % 2 == 0 else (("tank", x0 + 7, 98),))
        S("box", x0, 0, 77, x0 + 11, 6.5, 83, SAND_DEEP if (x0 // 11) % 2 == 0 else SAND)
        roof(x0, 77, x0 + 11, 83, 6.5, "nsew", (("tank", x0 + 4, 79.5),) if (x0 // 11) % 2 == 0 else (("chimney", x0 + 8, 79),))

    for c in ((-90, 0, 88, 1.4), (-88.6, 0, 88, 1.4), (-70, 0, 90, 1.2), (-58, 0, 87, 1.4), (-58, 1.4, 87, 1.4), (-80, 0, 87.5, 1.2)):
        S("crate", *c)

    S("planter", -75, 89, 1)

    S("box", 40, 0, 99, 100, 3.6, 100.2, SAGE)
    S("box", 40, 0, 76, 64, 3.6, 77.2, SAGE)
    S("box", 76, 0, 76, 100, 3.6, 77.2, SAGE)
    S("box", 40, 0, 77.2, 41.2, 3.6, 84, SAGE)
    S("box", 40, 0, 92, 41.2, 3.6, 99, SAGE)
    S("box", 98.8, 0, 77.2, 100, 3.6, 99, SAGE)

    for x0, z0, x1, z1 in ((60, 84, 80, 84.6), (60, 91.4, 80, 92), (60, 84.6, 60.6, 91.4), (79.4, 84.6, 80, 91.4)):
        S("box", x0, 0, z0, x1, 0.5, z1, TERRA)

    for p in ((52, 80, 0), (88, 80, 1), (52, 96, 1), (88, 96, 0), (46, 94, 0), (94, 82, 1)):
        S("planter", *p)

    for x0, z0, x1, z1 in ((44, 86, 50, 87.2), (90, 90, 96, 91.2)):
        S("box", x0, 0, z0, x1, 1.2, z1, SAGE)

    S("box", -100, 0, -40, -88, 6, -22, SAND)
    roof(-100, -40, -88, -22, 6.0, "sw", (("tank", -96.5, -37), ("chimney", -91, -37.5)))
    S("box", -96, 0, -12, -84, 8, 8, SAGE)
    roof(-96, -12, -84, 8, 8.0, "ew", (("chimney", -86.5, -2),))
    S("box", -100, 0, 18, -88, 6, 40, SAND_DEEP)
    roof(-100, 18, -88, 40, 6.0, "nw", (("tank", -96.5, 37), ("chimney", -91, 37.5)))
    S("stairs", -94, -22, -91, -12, 6.3, 2.0, "pos_z", TERRA)
    S("stairs", -94, 8, -91, 18, 6.3, 2.0, "neg_z", TERRA)
    S("stairs", -88, -36, -78, -32, 0, 6.3, "neg_x", SAND_DEEP)
    S("stairs", -88, 30, -78, 34, 0, 6.3, "neg_x", SAND_DEEP)
    S("box", -100, 6.3, -40, -99, 7.3, -22, SAND)
    S("box", -100, 6.3, 18, -99, 7.3, 40, SAND)

    for x0, x1 in ((-24, -5), (5, 24)):
        S("box", x0, 0, 82, x1, 5, 83.5, SAGE)

    S("arch", "x", 0, 82.75, 10, 6, 3, 7, 1.5, SAGE)
    S("box", -24, 0, 98.5, -4, 5, 100, SAGE)
    S("box", 4, 0, 98.5, 24, 5, 100, SAGE)
    S("box", -24, 0, 83.5, -22.5, 5, 98.5, SAGE)
    S("box", 22.5, 0, 83.5, 24, 5, 98.5, SAGE)

    for cx, cz in ((-24, 82), (24, 82), (-24, 100), (24, 100)):
        S("box", cx - 2.2, 0, cz - 2.2, cx + 2.2, 9, cz + 2.2, SAND)
        S("box", cx - 2.5, 9, cz - 2.5, cx + 2.5, 9.4, cz + 2.5, TERRA)

    S("box", -8, 0, 88, 8, 1.2, 94, SAND_DEEP)
    S("stairs", -4, 85, 4, 88, 0, 1.2, "pos_z", SAND_DEEP)

    for c in ((-6, 1.2, 92, 1.4), (5, 1.2, 90, 1.2), (-18, 0, 87, 1.4), (-16.6, 0, 87, 1.4), (17, 0, 95, 1.4)):
        S("crate", *c)

    for k in range(5):
        a = -95 + 40 * k
        S("box", a, 0, 101, a + 22, 1.1, 101.6, SAND)
        S("box", a, 0, 112.4, a + 22, 1.1, 113, SAND)

    for k in range(5):
        a = -95 + 40 * k
        S("box", -101.6, 0, a, -101, 1.1, a + 22, SAND)

    for x, z, w, d in ((-60, 128, 14, 7), (30, 132, 12, 6), (-110, 126, 10, 8), (90, 124, 12, 6), (-128, 60, 7, 14), (-130, -20, 8, 12), (128, 100, 7, 10)):
        S("box", x - w / 2, 0, z - d / 2, x + w / 2, 0.8, z + d / 2, OUTER)
        S("box", x - w / 4, 0.8, z - d / 4, x + w / 4, 1.6, z + d / 4, OUTER)

    for p in ((-40, 124, 0), (60, 140, 1), (-138, 100, 0), (-136, 20, 1), (-120, -80, 0), (120, 132, 1)):
        S("planter", *p)

    for x0, z0, x1, z1 in ((-80, 138, -70, 138.8), (-134, 40, -133.2, 52)):
        S("box", x0, 0, z0, x1, 1.2, z1, SAND)

    S("arch", "x", 0, 118, 14, 8, 4, 9, 2, SAND)
    S("box", -7.3, 9, 116.8, 7.3, 9.35, 119.2, TERRA)

    for sx in (-1, 1):
        S("box", min(sx * 7, sx * 22), 0, 117.2, max(sx * 7, sx * 22), 3, 118.8, SAND_DEEP)
        S("box", min(sx * 7, sx * 22) - 0.1, 3, 117.1, max(sx * 7, sx * 22) + 0.1, 3.25, 118.9, TERRA)
        S("planter", sx * 11, 123, 0 if sx < 0 else 1)
        S("crate", sx * 18, 0, 126, 1.4)
        S("crate", sx * 19.4, 0, 126, 1.4)
        S("crate", sx * 18.7, 1.4, 126, 1.4)
        S("box", sx * 28 - 3, 0, 124, sx * 28 + 3, 1.1, 124.8, SAND)

    rng = random.Random(5)
    taken = [(-60, 128), (30, 132), (-110, 126), (90, 124), (-128, 60), (-130, -20), (128, 100), (-40, 124), (60, 140), (-138, 100), (-136, 20), (-120, -80), (120, 132), (-75, 138), (-134, 46)]
    cells = [(x, z) for z in (122, 140) for x in range(-140, 141, 20)] + [(x, z) for x in (-122, -140) for z in range(-100, 101, 20)]
    kinds = ["ridge", "ruin", "palms", "arch"]
    pick = 0

    for cx, cz in cells:
        if cz > 113 and abs(cx) < 34:
            continue

        x = cx + rng.uniform(-4, 4)
        z = cz + rng.uniform(-3, 3)

        if any((x - tx) ** 2 + (z - tz) ** 2 < 81 for tx, tz in taken):
            continue

        taken.append((x, z))
        kind = kinds[pick % 4]
        pick += 1
        along_x = cz > 113

        if kind == "ridge":
            L, W = (16, 5) if along_x else (5, 16)
            S("box", x - L / 2, 0, z - W / 2, x + L / 2, 0.7, z + W / 2, OUTER)
            S("box", x - L / 3, 0.7, z - W / 3, x + L / 3, 1.4, z + W / 3, OUTER)
            S("box", x - L / 6, 1.4, z - W / 6, x + L / 6, 2.0, z + W / 6, OUTER)
        elif kind == "ruin":
            h1 = rng.uniform(2.0, 3.6)
            h2 = rng.uniform(1.0, 2.4)

            if along_x:
                S("box", x - 5, 0, z - 0.5, x - 1, h1, z + 0.5, SAND)
                S("box", x + 0.5, 0, z - 0.5, x + 4, h2, z + 0.5, SAND_DEEP)
                S("box", x + 1, 0, z + 1.5, x + 2.6, 0.8, z + 2.6, SAND)
            else:
                S("box", x - 0.5, 0, z - 5, x + 0.5, h1, z - 1, SAND)
                S("box", x - 0.5, 0, z + 0.5, x + 0.5, h2, z + 4, SAND_DEEP)
                S("box", x + 1.5, 0, z + 1, x + 2.6, 0.8, z + 2.6, SAND)
        elif kind == "palms":
            for k in range(3):
                S("palm", x + rng.uniform(-3, 3), z + rng.uniform(-3, 3), k % 2)

            S("box", x - 3.6, 0, z - 3.6, x + 3.6, 0.3, z + 3.6, LAWN)
        else:
            S("arch", "x" if along_x else "z", x if along_x else z, z if along_x else x, 6, 3.6, 2.4, 4.6, 1.0, SAND)
            S("box", (x + 4) if along_x else (x + 1.5), 0, (z + 1.5) if along_x else (z + 4), (x + 5.6) if along_x else (x + 3.1), 0.9, (z + 3.1) if along_x else (z + 5.6), SAND)

    for flip in (1, -1):
        for kind, a in sym_list:
            a = list(a)

            if flip == -1:
                if kind == "box":
                    a = [-a[3], a[1], -a[5], -a[0], a[4], -a[2], a[6]]
                elif kind == "arch":
                    a[1], a[2] = -a[1], -a[2]
                elif kind == "stairs":
                    opp = {"pos_z": "neg_z", "neg_z": "pos_z", "pos_x": "neg_x", "neg_x": "pos_x"}
                    a = [-a[2], -a[3], -a[0], -a[1], a[4], a[5], opp[a[6]], a[7]]
                elif kind == "crate":
                    a[0], a[2] = -a[0], -a[2]
                elif kind == "planter":
                    a[0], a[1] = -a[0], -a[1]
                elif kind == "palm":
                    a[0], a[1] = -a[0], -a[1]

            if kind == "box":
                box(*a)
            elif kind == "arch":
                arch(*a)
            elif kind == "stairs":
                stairs(*a)
            elif kind == "crate":
                crate(*a)
            elif kind == "planter":
                planter(*a)
            elif kind == "palm":
                palms.append((a[0], 0.3, a[1], a[2]))

    zones = []

    def zone(x0, z0, x1, z1, col):
        zones.append((x0, z0, x1, z1, col))
        zones.append((-x1, -z1, -x0, -z0, col))

    zone(-6, 55, 6, 61, TERRA_FLOOR)
    zone(-8, -8, 8, 8, TERRA_FLOOR)
    zone(-62, -6, -44, 6, TERRA_FLOOR)
    zone(-100, 84, -45, 94, TERRA_FLOOR)
    zone(60.6, 84.6, 79.4, 91.4, WATER)
    zone(41.2, 77.2, 98.8, 99, LAWN)
    zone(-22.5, 83.5, 22.5, 98.5, TERRA_FLOOR)
    zone(-150, 101, 150, 113, ROAD)
    zone(-113, -101, -101, 101, ROAD)
    zone(-150, 113, 150, 150, OUTER)
    zone(-150, -113, -113, 113, OUTER)

    solids_flat = [b for b in boxes if b[1] <= 0.01 and b[4] > 0.4]
    n = int(2 * HALF)
    floor_ids = {}

    for i in range(n):
        for j in range(n):
            x0 = -HALF + i
            z0 = -HALF + j
            cx, cz = x0 + 0.5, z0 + 0.5

            if any(b[0] < cx < b[3] and b[2] < cz < b[5] for b in solids_flat if b[0] - 1 < cx < b[3] + 1):
                continue

            col = FLOOR

            for zx0, zz0, zx1, zz1, zc in zones:
                if zx0 <= cx <= zx1 and zz0 <= cz <= zz1:
                    col = zc

                    break

            ids = []

            for px, pz in ((x0, z0), (x0, z0 + 1), (x0 + 1, z0 + 1), (x0 + 1, z0)):
                key = (px, pz, col)

                if key not in floor_ids:
                    floor_ids[key] = len(verts)
                    verts.append(Vector((px, 0, pz)))

                ids.append(floor_ids[key])

            faces.append(tuple(ids))
            face_col.append(col)

    for lo, hi in (((-175, -175), (175, -HALF)), ((-175, HALF), (175, 175)), ((-175, -HALF), (-HALF, HALF)), ((HALF, -HALF), (175, HALF))):
        grid((lo[0], 0, lo[1]), (hi[0] - lo[0], 0, 0), (0, 0, hi[1] - lo[1]), (0, 1, 0), OUTER, step=7.0)

    for p in palms:
        palm_occluder(*p)

    for k in range(6):
        x = -25 + 10 * k
        spawns.append((x, 0, 136 if k % 2 == 0 else 130, math.pi))
        spawns.append((-x, 0, -136 if k % 2 == 0 else -130, 0.0))

    wl = [(-51, 1.5, 31), (-26, 0, 0), (-45, 0, -20), (-26, 6, -20), (-10, 0, 36), (-60, 0, 12), (0, 0, 10), (-40, 0, 50),
          (-80, 0, 89), (-62, 0, 89), (70, 0, 80), (92, 0, 88), (-94, 6.3, -30), (-90, 8, -2), (0, 1.2, 91), (-60, 0, 107), (60, 0, 107), (-120, 0, 70), (-107, 0, 0)]

    for w in wl:
        weapons.append(w)
        weapons.append((-w[0], w[1], -w[2]))


def bake():
    tv = list(verts) + occluders_v
    tf = [tuple(f) for f in faces] + [tuple(i + len(verts) for i in f) for f in occluders_f]
    tree = BVHTree.FromPolygons(tv, tf)
    rng = random.Random(11)
    hemi = []

    while len(hemi) < 10:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))

        if 0.1 < d.length <= 1:
            hemi.append(d.normalized())

    jit = []

    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        o = Vector((math.cos(a), 0, math.sin(a))) * 0.035
        jit.append((SUN + o).normalized())

    colours = {}
    cache = {}

    for fi, f in enumerate(faces):
        p0, p1, p3 = verts[f[0]], verts[f[1]], verts[f[-1]]
        n = (p1 - p0).cross(p3 - p0).normalized()
        col = face_col[fi]
        out = []

        for vi in f:
            q = verts[vi]
            key = (round(q.x, 3), round(q.y, 3), round(q.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2))

            if key not in cache:
                origin = verts[vi] + n * 0.04
                lit = 1.0

                if n.dot(SUN) > 0.02:
                    seen = 0

                    for d in jit:
                        loc, _, _, _ = tree.ray_cast(origin, d, 160.0)

                        if loc is None:
                            seen += 1

                    lit = seen / len(jit)

                occ = 0.0
                total = 0

                for d in hemi:
                    if d.dot(n) < 0:
                        d = -d

                    if d.dot(n) < 0.08:
                        continue

                    total += 1
                    loc, _, _, dist = tree.ray_cast(origin, d, 2.6)

                    if loc is not None:
                        occ += 1 - dist / 2.6

                occ = occ / max(total, 1)
                cache[key] = (lit, occ)

            lit, occ = cache[key]
            ao = 1 - 0.42 * occ
            out.append(tuple(col[c] * (SHADE[c] + (1 - SHADE[c]) * lit) * ao for c in range(3)))

        colours[fi] = out

    return colours


def export(colours):
    tiles = {}

    for fi, f in enumerate(faces):
        c = sum((verts[v] for v in f), Vector()) / len(f)
        tx = min(max(int((c.x + HALF) // TILE), 0), TN - 1)
        tz = min(max(int((c.z + HALF) // TILE), 0), TN - 1)
        tiles.setdefault(tz * TN + tx, []).append(fi)

    info = []

    for t in range(TN * TN):
        tx, tz = t % TN, t // TN
        cx = -HALF + (tx + 0.5) * TILE
        cz = -HALF + (tz + 0.5) * TILE
        fl = tiles.get(t, [])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        me = bpy.data.meshes.new("t")
        pts = []
        polys = []
        loop_cols = []

        local = {}

        for fi in fl:
            f = faces[fi]
            poly = []

            for k, vi in enumerate(f):
                if vi not in local:
                    p = verts[vi]
                    local[vi] = len(pts)
                    pts.append((p.x - cx, -(p.z - cz), p.y))

                poly.append(local[vi])
                loop_cols.append(colours[fi][k])

            polys.append(tuple(poly))

        me.from_pydata(pts, [], polys)
        me.update()
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

        for li, lp in enumerate(me.loops):
            c = loop_cols[li]
            attr.data[li].color = (min(c[0], 1), min(c[1], 1), min(c[2], 1), 1.0)

        ob = bpy.data.objects.new("t", me)
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        mat = bpy.data.materials.new("courtyard")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        me.materials.append(mat)
        me.color_attributes.active_color = me.color_attributes["Col"]
        me.color_attributes.render_color_index = me.color_attributes.find("Col")
        path = os.path.join(OUT, "t%d.glb" % t)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT", export_attributes=True)
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        info.append((t, cx, cz, (lo[0], lo[2], -hi[1]), (hi[0], hi[2], -lo[1]), os.path.getsize(path), len(me.polygons)))
        print("TILE", t, os.path.getsize(path), len(me.polygons))

    return info


def write_zig(info):
    L = []
    L.append("const geom = @import(\"geom.zig\");")
    L.append("")
    L.append("pub const Ramp = struct { min: [3]f32, max: [3]f32, rise: geom.Rise };")
    L.append("")
    L.append("pub const boxes = [_][6]f32{")

    for b in boxes:
        L.append("    .{ %s }," % ", ".join("%.3f" % v for v in b))

    L.append("};")
    L.append("")
    L.append("pub const ramps = [_]Ramp{")

    for lo, hi, d in ramps:
        L.append("    .{ .min = .{ %.3f, %.3f, %.3f }, .max = .{ %.3f, %.3f, %.3f }, .rise = .%s }," % (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2], d))

    L.append("};")
    L.append("")
    L.append("pub const palms = [_][4]f32{")

    for p in palms:
        L.append("    .{ %.3f, %.3f, %.3f, %d }," % p)

    L.append("};")
    L.append("")
    L.append("pub const spawns = [_][4]f32{")

    for s in spawns:
        L.append("    .{ %.3f, %.3f, %.3f, %.4f }," % s)

    L.append("};")
    L.append("")
    L.append("pub const weapons = [_][3]f32{")

    for w in weapons:
        L.append("    .{ %.3f, %.3f, %.3f }," % w)

    L.append("};")
    L.append("")
    L.append("pub const tiles = [_][2]f32{")

    for t in info:
        L.append("    .{ %.3f, %.3f }," % (t[1], t[2]))

    L.append("};")

    with open(ZIG, "w") as fh:
        fh.write("\n".join(L) + "\n")

    for t in info:
        lo, hi = t[3], t[4]
        print("PROPINFO    .{ .file = \"courtyard/t%d.glb\", .scale = 1.00, .collide = .none, .group = .building, .foliage = false, .min = .{ %.3f, %.3f, %.3f }, .max = .{ %.3f, %.3f, %.3f } }," % (t[0], lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


build()
print("GEOM", len(verts), len(faces), len(boxes), len(ramps))
cols = bake()
print("BAKED")
write_zig(export(cols))
