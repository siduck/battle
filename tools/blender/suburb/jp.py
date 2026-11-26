import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))

import bpy
import dfkit as k
from mathutils import Vector

MID = os.environ.get("MID") == "1"
FAR = os.environ.get("FAR") == "1"
N = 2 if MID else 1
T = 0.25
KEY = "#e9d7b6"
ACCENTS = ("jp_red", "jp_red_dark", "jp_indigo", "jp_yellow", "jp_green", "jp_cherry", "jp_cherry_light", "jp_cherry_dark", "jp_maple", "jp_maple_light")

parts = []
soft = []
rng = random.Random(3)


def setup(seed=3):
    global parts, soft, rng

    k.reset()
    k.set_mid(MID)
    k.harmonize(KEY, 0.14, accents=ACCENTS, accent_amount=0.06)
    parts = []
    soft = []
    rng = random.Random(seed)


def c(name):
    return k.c(name)


def add(items):
    if isinstance(items, (list, tuple)):
        parts.extend(items)
    else:
        parts.append(items)

    return items


def place(items, x, y, z, facing=0.0):
    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)
        parts.append(it)

    return items


def shift(items, x=0.0, y=0.0, z=0.0):
    for it in items:
        k.move(it, x, y, z)

    return items


def bx(size, at, color, bevel=0.02):
    return k.beveled_box("b", size, at, c(color), bevel)


def flat(size, at, color):
    return k.box("f", size, at, c(color))


def bar(a, b, r, color, sides=6):
    return k._bar("bar", Vector(a), Vector(b), r, c(color), sides=sides * N if sides > 4 else sides)


def wall(width, height, openings, color, thick=T):
    if FAR:
        piece = flat((width, thick, height), (0, thick / 2, 0), color)
        soft.append(piece)

        return [piece]

    pieces = k.wall("w", width, height, thick, (0, thick / 2, 0), openings, color, 0.0, bevel=0)
    soft.extend(pieces)

    return pieces


def window(w, h, wall_color, rail=False, frame="jp_alu", panes=2, screen=False):
    if FAR:
        return [flat((w, 0.02, h * 0.55), (0, -0.012, 0), "jp_glass"), flat((w, 0.02, h * 0.45), (0, -0.012, h * 0.55), "jp_glass_light"), flat((w + 0.1, 0.1, 0.05), (0, -0.05, -0.05), frame)]

    dark = wall_color + "_dark" if wall_color + "_dark" in k._INDEX else "jp_grey_dark"
    items = [
        flat((w, 0.04, h), (0, T - 0.03, 0), "void"),
        flat((0.03, T - 0.04, h), (-w / 2 + 0.015, (T - 0.04) / 2, 0), dark),
        flat((0.03, T - 0.04, h), (w / 2 - 0.015, (T - 0.04) / 2, 0), dark),
        flat((w, T - 0.04, 0.03), (0, (T - 0.04) / 2, h - 0.03), dark),
    ]
    pw = (w - 0.1) / panes

    for i in range(panes):
        px = -w / 2 + 0.05 + pw * (i + 0.5)
        items.append(flat((pw - 0.03, 0.02, h * 0.62 - 0.05), (px, 0.13, 0.05), "jp_glass"))
        items.append(flat((pw - 0.03, 0.02, h * 0.38 - 0.06), (px, 0.13, h * 0.62), "jp_glass_light"))

    for fx in (-w / 2 + 0.025, w / 2 - 0.025):
        items.append(flat((0.05, 0.06, h), (fx, 0.11, 0), frame))

    items.append(flat((w, 0.06, 0.05), (0, 0.11, 0), frame))
    items.append(flat((w, 0.06, 0.05), (0, 0.11, h - 0.05), frame))

    for i in range(1, panes):
        items.append(flat((0.04, 0.06, h), (-w / 2 + 0.05 + pw * i, 0.1, 0), frame))

    items.append(bx((w + 0.12, 0.12, 0.05), (0, -0.04, -0.05), frame, 0.01))

    if rail:
        rz = h * 0.42

        for z in (rz, rz * 0.35):
            items.append(bar((-w / 2 + 0.02, -0.13, z), (w / 2 - 0.02, -0.13, z), 0.015, "jp_alu_dark", 4))

        for i in range(int(w / 0.12) + 1):
            x = -w / 2 + 0.04 + i * (w - 0.08) / int(w / 0.12)
            items.append(flat((0.02, 0.02, rz), (x, -0.13, 0), "jp_alu_dark"))

        for x in (-w / 2 + 0.02, w / 2 - 0.02):
            items.append(flat((0.03, 0.13, 0.03), (x, -0.07, rz - 0.015), "jp_alu_dark"))

    if screen:
        items.append(bx((w + 0.1, 0.16, 0.14), (0, -0.06, h + 0.02), "jp_alu_dark", 0.01))

    return items


def door(w, h, color="jp_wood", frame="jp_alu", glass=False):
    if FAR:
        return [flat((w, 0.02, h), (0, -0.012, 0), color)]

    items = [
        flat((w, 0.04, h), (0, T - 0.03, 0), "void"),
        bx((w - 0.08, 0.05, h - 0.04), (0, 0.15, 0), color, 0.008),
    ]

    if glass:
        items.append(flat((w * 0.5, 0.02, h * 0.35), (0, 0.12, h * 0.5), "jp_glass"))
    else:
        for z in (0.25, h * 0.55):
            items.append(flat((w - 0.24, 0.02, h * 0.3), (0, 0.12, z), color + "_dark" if color + "_dark" in k._INDEX else color))

    items.append(flat((0.04, 0.04, 0.14), (w * 0.3, 0.1, h * 0.45), "jp_alu"))

    for fx in (-w / 2 + 0.025, w / 2 - 0.025):
        items.append(flat((0.05, 0.08, h), (fx, 0.08, 0), frame))

    items.append(flat((w, 0.08, 0.06), (0, 0.08, h - 0.06), frame))

    return items


def glassfront(w, h, frame="jp_alu_dark", bays=3, kick="jp_alu_dark"):
    if FAR:
        return [flat((w, 0.02, h * 0.6), (0, -0.012, 0), "jp_glass"), flat((w, 0.02, h * 0.4), (0, -0.012, h * 0.6), "jp_glass_light")]

    items = [flat((w, 0.04, h), (0, T - 0.03, 0), "void")]
    bw = w / bays

    for i in range(bays):
        x = -w / 2 + bw * (i + 0.5)
        items.append(flat((bw - 0.08, 0.02, h * 0.58 - 0.2), (x, 0.13, 0.22), "jp_glass"))
        items.append(flat((bw - 0.08, 0.02, h * 0.42 - 0.08), (x, 0.13, h * 0.58), "jp_glass_light"))
        items.append(flat((bw - 0.06, 0.05, 0.2), (x, 0.12, 0), kick))

    for i in range(bays + 1):
        items.append(flat((0.06, 0.08, h), (-w / 2 + bw * i + (0.03 if i == 0 else -0.03 if i == bays else 0), 0.1, 0), frame))

    items.append(flat((w, 0.08, 0.07), (0, 0.1, h - 0.07), frame))
    items.append(flat((w, 0.08, 0.05), (0, 0.1, h * 0.58), frame))

    return items


def shutter(w, h, open_frac=0.35):
    if FAR:
        top = h * (1 - open_frac)

        return [flat((w, 0.02, h - top), (0, -0.012, 0), "void"), flat((w, 0.02, top), (0, -0.012, h - top), "jp_alu"), flat((w + 0.1, 0.3, 0.3), (0, -0.04, h), "jp_alu_dark")]

    items = [flat((w, 0.04, h), (0, T - 0.03, 0), "void")]
    top = h * (1 - open_frac)
    rib = 0.09 if not MID else 0.06
    n = int(top / rib)

    for i in range(n):
        z = h - (i + 1) * rib
        items.append(flat((w - 0.04, 0.03 + 0.015 * (i % 2), rib), (0, 0.08, z), "jp_alu" if i % 2 else "jp_alu_dark"))

    items.append(flat((w - 0.04, 0.05, 0.06), (0, 0.07, h - n * rib - 0.06), "jp_alu_dark"))

    for fx in (-w / 2 + 0.03, w / 2 - 0.03):
        items.append(flat((0.06, 0.1, h), (fx, 0.06, 0), "jp_alu_dark"))

    items.append(bx((w + 0.1, 0.32, 0.3), (0, -0.04, h), "jp_alu_dark", 0.02))

    return items


def sign(w, h, base="jp_sign", ink="jp_indigo", depth=0.1, letters=None):
    items = [bx((w, depth, h), (0, -depth / 2, 0), base, 0.015)]

    if FAR:
        items.append(flat((w * 0.7, 0.02, h * 0.45), (0, -depth - 0.01, h * 0.28), ink))

        return items

    n = letters or max(2, int(w / 0.42))
    lw = (w - 0.3) / n

    for i in range(n):
        x = -w / 2 + 0.15 + lw * (i + 0.5)
        hh = h * rng.uniform(0.45, 0.62)
        items.append(flat((lw * 0.7, 0.02, hh), (x, -depth - 0.01, (h - hh) / 2), ink))

        if rng.random() > 0.45:
            items.append(flat((lw * 0.22, 0.021, hh * 0.5), (x + lw * 0.18, -depth - 0.015, (h - hh) / 2 + hh * 0.3), base))

    return items


def vsign(h, w=0.5, base="jp_yellow", ink="jp_red_dark"):
    items = [bx((0.12, w, h), (0, 0, 0), base, 0.015)]
    n = max(2, int(h / 0.5))

    for i in range(n):
        z = 0.15 + i * (h - 0.3) / n
        for sx in (-1, 1):
            items.append(flat((0.02, w * 0.6, (h - 0.3) / n * 0.65), (sx * 0.07, 0, z), ink))

    items.append(flat((0.05, 0.05, h + 0.2), (0, -w / 2 - 0.05, -0.1), "jp_alu_dark"))

    return items


def awning(w, depth, a="jp_red", b="jp_sign", slope=18):
    items = []
    n = max(4, int(w / 0.3))
    sw = w / n

    for i in range(n):
        s = flat((sw, depth, 0.04), (-w / 2 + sw * (i + 0.5), -depth / 2, 0), a if i % 2 == 0 else b)
        k.rotate(s, slope, "X")
        items.append(s)

    drop = depth * math.sin(math.radians(slope))
    out = -depth * math.cos(math.radians(slope))

    for i in range(n):
        items.append(flat((sw, 0.03, 0.22), (-w / 2 + sw * (i + 0.5), out, -drop - 0.2), a if i % 2 == 0 else b))

    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        items.append(bar((x, 0, -0.6), (x, out, -drop), 0.015, "jp_alu_dark", 4))

    return items


def hisashi(w, depth, color="jp_tile", rows=3):
    items = []
    depth = max(depth, 0.75)
    slope = 24
    rw = depth / rows

    for i in range(rows):
        s = flat((w, rw + 0.03, 0.1), (0, -rw * (i + 0.5), 0), color if i % 2 == 0 else color + "_dark")
        k.rotate(s, slope, "X")
        k.move(s, 0, 0, -i * 0.012)
        items.append(s)

    drop = depth * math.sin(math.radians(slope))
    items.append(flat((w, 0.04, 0.1), (0, -depth * math.cos(math.radians(slope)), -drop - 0.06), "jp_char"))

    for x in (-w / 2 + 0.2, w / 2 - 0.2):
        items.append(bar((x, 0, -0.35), (x, -depth * 0.8, -drop * 0.8), 0.025, "jp_char", 4))

    return items


def ac_unit(at, facing=0.0):
    x, y, z = at

    if FAR:
        it = flat((0.8, 0.3, 0.56), (0, 0, 0), "jp_cream_light")
        k.rotate(it, facing)
        k.move(it, x, y, z)

        return [it]
    items = [
        bx((0.8, 0.3, 0.56), (0, 0, 0), "jp_cream_light", 0.025),
        k.prism("fan", 8 * N, 0.19, 0.02, (0.13, -0.15, 0.28), c("jp_alu_dark")),
        flat((0.18, 0.02, 0.4), (-0.24, -0.155, 0.08), "jp_alu"),
    ]
    k.rotate(items[1], 90, "X", (0.13, -0.15, 0.28))

    for i in range(3):
        items.append(flat((0.38, 0.015, 0.02), (0.13, -0.17, 0.16 + i * 0.12), "jp_alu_dark"))

    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)

    return items


def railing(w, h, at, posts=None, color="jp_alu_dark", bars=True):
    x0, y0, z0 = at

    if FAR:
        return [flat((w, 0.04, h), (x0, y0, z0), color)]

    items = [bar((x0 - w / 2, y0, z0 + h), (x0 + w / 2, y0, z0 + h), 0.025, color, 4)]

    if bars:
        n = posts or max(3, int(w / 0.11))

        for i in range(n + 1):
            x = x0 - w / 2 + i * w / n
            items.append(flat((0.02, 0.02, h), (x, y0, z0), color))

        items.append(bar((x0 - w / 2, y0, z0 + 0.08), (x0 + w / 2, y0, z0 + 0.08), 0.015, color, 4))
    else:
        items.append(flat((w, 0.03, h - 0.1), (x0, y0, z0 + 0.05), color))

    return items


def balcony(w, depth, z, wall_y, rail_color="jp_alu_dark", ac=True, laundry=False, solid=False):
    items = [bx((w, depth, 0.14), (0, wall_y - depth / 2, z - 0.14), "jp_concrete", 0.02)]

    if solid:
        items.append(flat((w, 0.06, 0.95), (0, wall_y - depth + 0.03, z), "jp_slate"))
        items.append(flat((w + 0.04, 0.1, 0.05), (0, wall_y - depth + 0.03, z + 0.95), rail_color))

        for sx in (-1, 1):
            items.append(flat((0.06, depth - 0.06, 0.95), (sx * (w / 2 - 0.03), wall_y - depth / 2, z), "jp_slate"))
    else:
        items += railing(w - 0.04, 0.95, (0, wall_y - depth + 0.03, z), posts=max(4, int(w / 0.2)), color=rail_color)

    for sx in (-1, 1) if not solid else ():
        items += [flat((0.03, depth - 0.05, 0.03), (sx * (w / 2 - 0.02), wall_y - depth / 2, z + 0.95), rail_color)]

        for i in range(4):
            items.append(flat((0.02, 0.02, 0.95), (sx * (w / 2 - 0.02), wall_y - depth + 0.05 + i * (depth - 0.1) / 3, z), rail_color))

    if ac:
        items += ac_unit((w / 2 - 0.55, wall_y - 0.25, z))

    if laundry and not FAR:
        items.append(bar((-w / 2 + 0.1, wall_y - depth * 0.55, z + 1.55), (w / 2 - 0.1, wall_y - depth * 0.55, z + 1.55), 0.015, "jp_alu", 4))

        for i in range(4):
            col = ("jp_sign", "jp_indigo", "jp_cherry", "jp_yellow")[i % 4]
            items.append(flat((0.32, 0.02, 0.45), (-w / 2 + 0.4 + i * 0.42, wall_y - depth * 0.55, z + 1.1), col))

    return items


def slope_profile(run, top, bottom, rows, side, th=0.12, step=0.05):
    pts = []

    for i in range(rows):
        u0 = i / rows
        u1 = (i + 1) / rows
        ya, za = side * run * u0, top + (bottom - top) * u0
        yb, zb = side * run * u1, top + (bottom - top) * u1
        pts.append((ya, za))
        pts.append((yb, zb + step))

    pts.append((side * run, bottom - th))
    pts.append((0, top - th))

    return pts


def gable_roof(w, d, rise, z, overhang=0.3, wall_color="jp_cream", rows=None, color="jp_tile", ends=True):
    rows = 1 if FAR else rows or max(4, int((d / 2 + overhang) / 0.38)) * N
    half = d / 2 + overhang
    drop = overhang * rise / (d / 2)
    out = []

    for side in (-1, 1):
        ob = k.sweep("roofside", slope_profile(half, rise, -drop, rows, side), w + 0.04, (0, 0, 0), c(color), axis="y")
        k.rotate(ob, 90)
        k.move(ob, 0, 0, z)
        out.append(ob)

    gap = 0.3 if not MID else 0.22
    nrib = int((w - 0.1) / gap)

    for side in (-1, 1) if not FAR else ():
        for i in range(nrib + 1):
            x = -w / 2 + 0.05 + i * (w - 0.1) / nrib
            out.append(k._bar("rib", Vector((x, side * 0.12, z + rise + 0.02)), Vector((x, side * (half - 0.02), z - drop + 0.08)), 0.032, c(color + "_light" if i % 2 else color + "_dark"), sides=4 if not MID else 6))

    out.append(bx((w + 0.08, 0.3, 0.2), (0, 0, z + rise - 0.06), color + "_dark", 0.03))

    if ends:
        for sx in (-1, 1):
            out.append(bx((0.26, 0.4, 0.32), (sx * (w / 2 + 0.02), 0, z + rise - 0.1), color + "_dark", 0.03))

    for sx in (-1, 1):
        tri = k.sweep("gable", [(-d / 2, 0), (d / 2, 0), (0, rise - 0.08)], 0.2, (0, 0, 0), c(wall_color), axis="y")
        k.rotate(tri, 90)
        k.move(tri, sx * (w / 2 - 0.1), 0, z)
        out.append(tri)
        soft.append(tri)

        for side in (-1, 1):
            barge = k.sweep("barge", [(0, rise + 0.02), (side * half, -drop + 0.02), (side * half, -drop - 0.1), (0, rise - 0.1)], 0.08, (0, 0, 0), c("jp_char"), axis="y")
            k.rotate(barge, 90)
            k.move(barge, sx * (w / 2 + 0.04), 0, z + 0.03)
            out.append(barge)

    for sy in (-1, 1):
        out.append(bx((w + 0.04, 0.06, 0.14), (0, sy * (half - 0.02), z - drop - 0.14), "jp_char", 0.01))

    return out


def flat_roof(w, d, z, parapet=0.6, color="jp_cream", cap="jp_alu"):
    items = [flat((w - 0.05, d - 0.05, 0.1), (0, 0, z - 0.05), "jp_concrete")]

    for i, (px, py, lx, ly) in enumerate(((0, -d / 2 + 0.1, w, 0.2), (0, d / 2 - 0.1, w, 0.2), (-w / 2 + 0.1, 0, 0.2, d - 0.4), (w / 2 - 0.1, 0, 0.2, d - 0.4))):
        p = flat((lx, ly, parapet), (px, py, z), color)
        soft.append(p)
        items.append(p)
        items.append(bx((lx + (0.06 if lx > 1 else 0.06), ly + (0.06 if ly > 1 else 0.06), 0.06), (px, py, z + parapet), cap, 0.01))

    return items


def tank(at):
    x, y, z = at
    items = []

    for lx in (-0.35, 0.35):
        for ly in (-0.35, 0.35):
            items.append(bar((x + lx, y + ly, z), (x + lx, y + ly, z + 0.8), 0.03, "jp_alu_dark", 4))

    items.append(flat((0.9, 0.9, 0.06), (x, y, z + 0.8), "jp_alu_dark"))
    items.append(k.lathe("tank", [(0, 0), (0.42, 0), (0.44, 0.15), (0.42, 0.8), (0.3, 0.95), (0.08, 1.0), (0, 1.0)], 10 * N, (x, y, z + 0.86), c("jp_cream_light")))
    items.append(k.prism("band", 10 * N, 0.445, 0.05, (x, y, z + 1.2), c("jp_slate")))

    return items


def lantern(at, color="jp_red", h=0.55, r=0.2):
    x, y, z = at
    body = k.lathe("lantern", [(0, 0), (r * 0.7, 0), (r, h * 0.25), (r * 1.02, h * 0.5), (r, h * 0.75), (r * 0.7, h), (0, h)], 10 * N, (x, y, z), c(color))
    items = [body]

    for zz in (0, h):
        items.append(k.prism("cap", 10 * N, r * 0.72, 0.05, (x, y, z + zz - 0.025), c("jp_char")))

    items.append(flat((r * 1.3, 0.01, h * 0.45), (x, y - r * 1.01, z + h * 0.28), "jp_sign"))
    items.append(bar((x, y, z + h), (x, y, z + h + 0.25), 0.012, "jp_char", 4))

    return items


def pipe(x, y, z0, z1, color="jp_alu_dark"):
    if FAR:
        return []

    return [bar((x, y, z0), (x, y, z1), 0.04, color, 6), flat((0.16, 0.12, 0.06), (x, y + 0.04, z1 - 0.06), color)]


def meter(at):
    if FAR:
        return []

    x, y, z = at

    return [bx((0.32, 0.12, 0.42), (x, y, z), "jp_alu", 0.015), flat((0.16, 0.02, 0.14), (x, y - 0.065, z + 0.22), "jp_glass_light")]


def finish(name, budget=None, fuse_soft=True, gradient=True, shade=None):
    global parts

    for ob in soft:
        k.jitter(ob, 0.012)

    if MID and fuse_soft and len(soft) > 1:
        gone = {id(o) for o in soft[1:]}
        parts = [p for p in parts if id(p) not in gone]
        k.fuse(list(soft), bevel=0.035, segments=3)

    ob = k.finish(name, parts, budget=budget)
    k.cull_hidden(ob)

    if gradient:
        k.height_gradient(ob, 0.9, 1.03)

    for lo, hi, f in shade or ():
        k.shade_volume(ob, lo, hi, f)

    k.grime(ob, 0.5, 0.82)

    return ob


def export(ob, out_dir, name):
    path = os.path.join(out_dir, name + ".glb")
    k.export(ob, path)

    return path
