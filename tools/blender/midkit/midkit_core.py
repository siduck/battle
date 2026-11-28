import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))

import bmesh
import bpy
import dfkit as k
from mathutils import Vector

PALETTES = {
    "airport": [
        ("ap_sand_l", "#e6dcc4"),
        ("ap_sand", "#d0c3a4"),
        ("ap_sand_d", "#a99e82"),
        ("ap_orange", "#c9774a"),
        ("ap_orange_d", "#a05c38"),
        ("ap_steel_l", "#cdd2d1"),
        ("ap_steel", "#a5acae"),
        ("ap_steel_d", "#6c767b"),
        ("ap_dark", "#383b3e"),
        ("ap_rubber", "#2a2b2d"),
        ("ap_glass", "#46606f"),
        ("ap_glass_l", "#86a0ad"),
        ("ap_void", "#1b191a"),
        ("ap_white", "#e4e0d6"),
        ("ap_yellow", "#d3ad3e"),
        ("ap_red", "#a9473b"),
        ("ap_green", "#5d7a55"),
        ("ap_green_d", "#445d40"),
        ("ap_leaf", "#5b7e3a"),
        ("ap_leaf_d", "#3f5f2c"),
        ("ap_leaf_l", "#79984a"),
        ("ap_bark", "#5b4633"),
        ("ap_wood", "#7a5c3f"),
        ("ap_wood_l", "#a2815a"),
        ("ap_blue", "#47677f"),
        ("ap_blue_d", "#344d62"),
        ("ap_asphalt", "#4a4b4c"),
        ("ap_olive", "#6b6f50"),
    ],
}

SIDES = 8
CUR = {"clad": None}


def setup(palette="airport"):
    k.reset()
    k.set_mid(True)
    k.KEY = None
    k.KEY_MIX = 0.0
    k.ACCENTS = set()

    for name, hexs in PALETTES[palette]:
        if name not in k._INDEX:
            k._INDEX[name] = len(k.PALETTE)
            k.PALETTE.append((name, hexs))


def c(name):
    return k.c(name)


def bevel_ob(ob, width, segments):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(30)]

    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    return ob


def bx(size, at, color, bevel=0.03, seg=None):
    b = k.box("b", size, at, c(color))
    small = min(size)

    if bevel <= 0 or small < 0.1:
        return b

    return bevel_ob(b, min(bevel * 1.6, small * 0.25), seg or (2 if small >= 0.7 else 1))


def flat(size, at, color):
    return k.box("f", size, at, c(color))


def bxc(size, at, color, bevel=0.03):
    sx, sy, sz = size
    x, y, z = at

    return bx(size, (x, y, z - sz / 2), color, bevel)


def cyl(r, h, at, color, sides=12, top=None):
    return k.prism("c", sides, r, h, at, c(color), radius_top=top)


def bar(a, b, r, color, sides=6):
    return k._bar("bar", Vector(a), Vector(b), r, c(color), sides=sides)


def lathe(profile, at, color, sides=16):
    return k.lathe("l", profile, sides, at, c(color))


def sweep_xz(outline, depth, at, color):
    return k.sweep("s", outline, depth, at, c(color), axis="y")


def sweep_xy(outline, height, at, color):
    return k.sweep("s", outline, height, at, c(color), axis="z")


def rot(items, deg, axis="Z", about=(0, 0, 0)):
    for it in items:
        k.rotate(it, deg, axis, about)

    return items


def mv(items, x=0.0, y=0.0, z=0.0):
    for it in items:
        k.move(it, x, y, z)

    return items


def grp(items):
    return items if isinstance(items, list) else [items]


def corrugated(width, height, at, color, pitch=0.5, depth=0.09, base=0.06, axis="x"):
    x0, y0, z0 = at
    n = max(2, int(round(width / pitch)))
    p = width / n
    pts = [(-width / 2, 0.0)]

    for i in range(n):
        xa = -width / 2 + i * p

        pts += [(xa + p * 0.08, 0.0), (xa + p * 0.25, depth), (xa + p * 0.5, depth), (xa + p * 0.67, 0.0)]

    pts += [(width / 2, 0.0), (width / 2, -base), (-width / 2, -base)]
    ob = k.sweep("clad", pts, height, (0, 0, 0), c(color), axis="z")

    if axis == "y":
        k.rotate(ob, 90)

    k.move(ob, x0, y0, z0)

    return [ob]


def ribbed(width, height, at, color, pitch=0.5, depth=0.06, thick=0.08, face="front"):
    x, y, z = at
    items = [bx((width, thick, height), (x, y, z), color, 0.0)]
    n = int(width / pitch)
    ys = -1 if face == "front" else 1

    for i in range(n):
        rx = x - width / 2 + pitch * (i + 0.5)
        items.append(flat((0.08, depth, height - 0.1), (rx, y + ys * (thick / 2 + depth / 2 - 0.005), z + 0.05), color))

    return items


def window(w, h, at, wall_color="ap_sand_d", depth=0.22, panes=2, frame="ap_steel_d", facing=0.0, sill=True):
    x, y, z = at
    items = [
        flat((w, 0.04, h), (0, depth - 0.08, 0), "ap_void"),
        flat((w - 0.1, 0.02, h * 0.58), (0, depth - 0.12, 0.05), "ap_glass"),
        flat((w - 0.1, 0.02, h * 0.38), (0, depth - 0.12, h * 0.6), "ap_glass_l"),
        flat((0.06, 0.1, h), (-w / 2 + 0.03, depth - 0.15, 0), frame),
        flat((0.06, 0.1, h), (w / 2 - 0.03, depth - 0.15, 0), frame),
        flat((w, 0.1, 0.06), (0, depth - 0.15, h - 0.06), frame),
        flat((w, 0.1, 0.06), (0, depth - 0.15, 0), frame),
    ]

    for i in range(1, panes):
        items.append(flat((0.05, 0.1, h), (-w / 2 + w * i / panes, depth - 0.15, 0), frame))

    if sill:
        items.append(bx((w + 0.18, 0.16, 0.07), (0, -0.01, -0.07), "ap_sand_l", 0.012))

    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)

    return items


def window_on(w, h, at, facing=0.0, frame="ap_steel_d", panes=2, depth=0.12, sill="ap_sand_l"):
    x, y, z = at
    t = 0.07
    items = [
        flat((w, 0.03, h), (0, -0.03, 0), "ap_glass"),
        flat((w, 0.032, h * 0.4), (0, -0.032, h * 0.6), "ap_glass_l"),
        bx((t, depth, h), (-w / 2 + t / 2, -depth / 2, 0), frame, 0.01),
        bx((t, depth, h), (w / 2 - t / 2, -depth / 2, 0), frame, 0.01),
        bx((w, depth, t), (0, -depth / 2, 0), frame, 0.01),
        bx((w, depth, t), (0, -depth / 2, h - t), frame, 0.01),
    ]

    for i in range(1, panes):
        items.append(bx((0.05, depth * 0.8, h), (-w / 2 + w * i / panes, -depth * 0.4, 0), frame, 0.0))

    if sill:
        items.append(bx((w + 0.2, depth + 0.1, 0.07), (0, -(depth + 0.1) / 2, -0.07), sill, 0.012))

    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)

    return items


def louvre(w, h, at, color="ap_steel_d", slats=None, facing=0.0):
    x, y, z = at
    n = slats or int(h / 0.09)
    items = [bx((w, 0.05, h), (0, 0, 0), "ap_dark", 0.01)]

    for i in range(n):
        items.append(flat((w - 0.08, 0.06, 0.04), (0, -0.03, 0.05 + i * (h - 0.1) / n), color))

    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)

    return items


def railing(length, height, at, color="ap_steel_d", posts=None, axis="x", mid=2):
    x, y, z = at
    n = posts or max(2, int(length / 0.9))
    items = []

    if axis == "x":
        items.append(bar((x - length / 2, y, z + height), (x + length / 2, y, z + height), 0.025, color, 6))

        for j in range(1, mid + 1):
            zz = z + height * j / (mid + 1)
            items.append(bar((x - length / 2, y, zz), (x + length / 2, y, zz), 0.014, color, 4))

        for i in range(n + 1):
            xx = x - length / 2 + i * length / n
            items.append(bar((xx, y, z), (xx, y, z + height), 0.022, color, 6))
    else:
        items.append(bar((x, y - length / 2, z + height), (x, y + length / 2, z + height), 0.025, color, 6))

        for j in range(1, mid + 1):
            zz = z + height * j / (mid + 1)
            items.append(bar((x, y - length / 2, zz), (x, y + length / 2, zz), 0.014, color, 4))

        for i in range(n + 1):
            yy = y - length / 2 + i * length / n
            items.append(bar((x, yy, z), (x, yy, z + height), 0.022, color, 6))

    return items


def ladder(height, at, width=0.45, color="ap_steel_d", rung=0.3, axis="y"):
    x, y, z = at
    items = []

    for s in (-1, 1):
        items.append(bar((x + s * width / 2, y, z), (x + s * width / 2, y, z + height), 0.025, color, 4))

    for i in range(int(height / rung)):
        items.append(bar((x - width / 2, y, z + 0.2 + i * rung), (x + width / 2, y, z + 0.2 + i * rung), 0.015, color, 4))

    return items


def stairs_run(width, rise, run, steps, at, color="ap_steel_d", tread="ap_steel", rail=True, axis="y", sign=1):
    x, y, z = at
    sr = rise / steps
    sd = run / steps
    items = []

    for i in range(steps):
        items.append(bx((width, sd * 0.98, 0.05), (x, y + sign * (i + 0.5) * sd, z + (i + 1) * sr - 0.05), tread, 0.008))

    for s in (-1, 1):
        a = (x + s * (width / 2 + 0.02), y, z + 0.1)
        b = (x + s * (width / 2 + 0.02), y + sign * run, z + rise + 0.1)
        items.append(bar(a, b, 0.04, color, 6))

        if rail:
            items.append(bar((a[0], a[1], a[2] + 0.95), (b[0], b[1], b[2] + 0.95), 0.025, color, 6))
            n = max(2, steps // 3)

            for i in range(n + 1):
                t = i / n
                items.append(bar((a[0], a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t), (a[0], a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t + 0.95), 0.016, color, 4))

    return items


def tire(r, w, at, rim="ap_steel", sides=12, axis="x"):
    x, y, z = at
    t = k.lathe("t", [(0, -w / 2), (r * 0.55, -w / 2), (r * 0.95, -w * 0.4), (r, -w * 0.15), (r, w * 0.15), (r * 0.95, w * 0.4), (r * 0.55, w / 2), (0, w / 2)], sides, (0, 0, 0), c("ap_rubber"))
    hub = k.prism("h", sides, r * 0.5, w * 1.04, (0, 0, -w * 0.52), c(rim))

    if axis == "x":
        k.rotate(t, 90, "Y")
        k.rotate(hub, 90, "Y")
    else:
        k.rotate(t, 90, "X")
        k.rotate(hub, 90, "X")

    k.move(t, x, y, z)
    k.move(hub, x, y, z)

    return [t, hub]


def bolts(points, color="ap_steel_d", r=0.025, h=0.03, normal="z"):
    items = []

    for p in points:
        if normal == "z":
            items.append(cyl(r, h, p, color, 6))
        else:
            b = cyl(r, h, (0, 0, 0), color, 6)
            k.rotate(b, 90, "X" if normal == "y" else "Y")
            k.move(b, *p)
            items.append(b)

    return items


def box_stripes(w, h, at, a, b, n, tilt=0.0):
    x, y, z = at
    items = []
    sw = w / n

    for i in range(n):
        items.append(flat((sw, 0.02, h), (x - w / 2 + sw * (i + 0.5), y, z), a if i % 2 == 0 else b))

    return items


def hazard(w, h, at, depth=0.02, n=None, a="ap_yellow", b="ap_dark", axis_x=True):
    x, y, z = at
    n = n or max(2, int(w / h))
    sw = w / n
    items = []

    for i in range(n):
        col = a if i % 2 == 0 else b

        if axis_x:
            items.append(flat((sw, depth, h), (x - w / 2 + sw * (i + 0.5), y, z), col))
        else:
            items.append(flat((depth, sw, h), (x, y - w / 2 + sw * (i + 0.5), z), col))

    return items


def finish(name, parts, budget=None, gradient=(0.9, 1.03), grime=(0.45, 0.8), cull=True, shade=None):
    ob = k.finish(name, parts, budget=budget)

    if cull:
        k.cull_hidden(ob)

    if gradient:
        k.height_gradient(ob, *gradient)

    for lo, hi, f in shade or ():
        k.shade_volume(ob, lo, hi, f)

    if grime:
        k.grime(ob, *grime)

    return ob


def export(ob, out_dir, name):
    path = os.path.join(out_dir, name + ".glb")
    k.export(ob, path)

    return path
