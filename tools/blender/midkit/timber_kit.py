import math
import random

import nature_kit as nk
from mathutils import Vector

k = nk.k
idx = nk.idx


def face_to(items, face, x=0.0, y=0.0, z=0.0):
    ang = {"f": 0, "r": 90, "b": 180, "l": -90}[face]

    for it in items:
        if ang:
            k.rotate(it, ang)

        k.move(it, x, y, z)

    return items


def log_pick(seed, base="fo_log", lt="fo_log_lt", dk="fo_log_dk"):
    def pick(i, j):
        h = nk.hash01(i, j, seed)

        return lt if h < 0.25 else dk if h > 0.8 else base

    return pick


def segments(a, b, cuts):
    out = []
    cur = a

    for c0, c1 in sorted(cuts):
        if c0 > cur:
            out.append((cur, min(c0, b)))

        cur = max(cur, c1)

    if cur < b:
        out.append((cur, b))

    return [s for s in out if s[1] - s[0] > 0.05]


def log_wall(axis, a, b, fixed, z0, height, r=0.21, openings=(), seed=0, shift=0.0, over=0.0, sides=6, step=None):
    items = []
    step = step or r * 1.78
    n = int((height - r) / step) + 1
    rnd = random.Random(seed)

    for c in range(n):
        z = z0 + r + c * step + shift

        if z + r > z0 + height + 0.02:
            break

        cuts = [(o[0], o[1]) for o in openings if o[2] < z + r * 0.7 and o[3] > z - r * 0.7]

        for s0, s1 in segments(a - over, b + over, cuts):
            wob = rnd.uniform(-0.012, 0.012)
            p0 = (s0, fixed + wob, z) if axis == "x" else (fixed + wob, s0, z)
            p1 = (s1, fixed + wob, z) if axis == "x" else (fixed + wob, s1, z)
            rr = r * rnd.uniform(0.94, 1.04)
            items.append(nk.tube("log", [p0, p1], [rr, rr], sides, log_pick(seed + c), cap_top="fo_log_end", cap_bottom="fo_log_end", seed=c))

    return items


def plank_wall(axis, a, b, fixed, z0, height, openings=(), seed=0, plank=0.46, thick=0.22, colors=("fo_wood_gray", "fo_wood", "fo_wood_dk"), batten=True):
    items = []
    rnd = random.Random(seed)
    n = max(1, int(round((b - a) / plank)))
    w = (b - a) / n

    for i in range(n):
        u0 = a + i * w
        u1 = u0 + w
        cuts = [(o[2], o[3]) for o in openings if o[0] < u1 and o[1] > u0]
        pieces = segments(z0, z0 + height, cuts)
        col = colors[0] if nk.hash01(i, seed, 1) > 0.25 else colors[1]

        for v0, v1 in pieces:
            t = thick + rnd.uniform(-0.015, 0.015)
            cx = (u0 + u1) / 2

            if axis == "x":
                items.append(nk.bevbox((w * 0.97, t, v1 - v0), (cx, fixed, v0), col, 0.0))
            else:
                items.append(nk.bevbox((t, w * 0.97, v1 - v0), (fixed, cx, v0), col, 0.0))

    return items


def win(w, h, depth=0.34, shutters=False, glass="fo_glass", frame="fo_wood_dk", panes=2):
    t = 0.09
    items = [
        nk.plain((w, depth * 0.3, h), (0, depth * 0.12, 0), "fo_void"),
        nk.plain((w - 0.06, 0.03, h - 0.06), (0, depth * 0.05, 0.03), glass),
        nk.plain((w - 0.06, 0.032, (h - 0.06) * 0.4), (0, depth * 0.04, 0.03 + (h - 0.06) * 0.6), "fo_glass_lt"),
        nk.bevbox((w + 2 * t, depth, t), (0, 0, h), frame, 0.015),
        nk.bevbox((w + 2 * t + 0.1, depth + 0.14, t), (0, -0.05, -t), "fo_wood_lt", 0.015),
        nk.bevbox((t, depth, h), (-w / 2 - t / 2, 0, 0), frame, 0.015),
        nk.bevbox((t, depth, h), (w / 2 + t / 2, 0, 0), frame, 0.015),
    ]

    for i in range(1, panes):
        x = -w / 2 + w * i / panes
        items.append(nk.plain((0.05, depth * 0.55, h), (x, -0.01, 0), frame))

    if shutters:
        for s in (-1, 1):
            sx = s * (w / 2 + t + w * 0.22)
            items.append(nk.bevbox((w * 0.42, 0.05, h), (sx, -depth / 2 - 0.02, 0), "fo_door", 0.01))
            items.append(nk.plain((w * 0.34, 0.03, 0.05), (sx, -depth / 2 - 0.05, h * 0.3), "fo_door_dk"))
            items.append(nk.plain((w * 0.34, 0.03, 0.05), (sx, -depth / 2 - 0.05, h * 0.65), "fo_door_dk"))

    return items


def door(w, h, depth=0.34, leaf="fo_door", frame="fo_wood_dk", step=True):
    t = 0.1
    items = [
        nk.plain((w, depth * 0.3, h), (0, depth * 0.12, 0), "fo_void"),
        nk.bevbox((w - 0.06, 0.07, h - 0.04), (0, -0.02, 0), leaf, 0.015),
        nk.bevbox((w + 2 * t, depth, t * 1.2), (0, 0, h), frame, 0.015),
        nk.bevbox((t, depth, h), (-w / 2 - t / 2, 0, 0), frame, 0.015),
        nk.bevbox((t, depth, h), (w / 2 + t / 2, 0, 0), frame, 0.015),
        nk.bevbox((w - 0.2, 0.04, 0.09), (0, -0.07, h * 0.18), "fo_door_dk", 0.01),
        nk.bevbox((w - 0.2, 0.04, 0.09), (0, -0.07, h * 0.78), "fo_door_dk", 0.01),
        nk.bar((w * 0.32, -0.1, h * 0.5), (w * 0.38, -0.1, h * 0.5), 0.03, "fo_metal", 5),
    ]

    if step:
        items.append(nk.bevbox((w + 0.5, 0.55, 0.14), (0, -0.4, -0.02), "fo_stone", 0.03))

    return items


def paint_bands(ob, at_y, half, bands=("fo_shingle", "fo_shingle_lt", "fo_shingle_dk", "fo_shingle"), band=0.42):
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        if p.normal.z > 0.25:
            row = int(abs(p.center.y - at_y) / band)
            h = nk.hash01(p.center.x, p.center.y, p.center.z, 4)
            attr.data[p.index].value = idx(bands[row % len(bands)] if h > 0.18 else bands[(row + 1) % len(bands)])


def shingle_roof(length, span, rise, at, overhang=0.4, bands=("fo_shingle", "fo_shingle_lt", "fo_shingle_dk", "fo_shingle"), ridge="fo_shingle_dk", trim="fo_wood", rows=None):
    x, y, z = at
    half = span / 2 + overhang
    drop = overhang * rise / (span / 2)
    rows = rows or max(5, int(half / 0.36))
    parts = []

    for side in (-1, 1):
        ob = k.sweep("roofside", jp_profile(half, rise, -drop, rows, side), length + 0.04, (0, 0, 0), idx(bands[0]), axis="y")
        k.rotate(ob, 90)
        attr = ob.data.attributes["lpm_color"]

        for p in ob.data.polygons:
            if p.normal.z > 0.2:
                row = int(abs(p.center.y) / (half / rows))
                attr.data[p.index].value = idx(bands[row % len(bands)])

        parts.append(ob)

    parts.append(nk.bevbox((length + 0.1, 0.34, 0.2), (0, 0, rise - 0.06), ridge, 0.03))

    for sx in (-1, 1):
        tri = k.sweep("gable", [(-span / 2, 0), (span / 2, 0), (0, rise - 0.08)], 0.2, (0, 0, 0), idx(trim), axis="y")
        k.rotate(tri, 90)
        k.move(tri, sx * (length / 2 - 0.1), 0, 0)
        parts.append(tri)

        for side in (-1, 1):
            barge = k.sweep("barge", [(0, rise + 0.02), (side * half, -drop + 0.02), (side * half, -drop - 0.1), (0, rise - 0.1)], 0.08, (0, 0, 0), idx("fo_wood_dk"), axis="y")
            k.rotate(barge, 90)
            k.move(barge, sx * (length / 2 + 0.04), 0, 0.03)
            parts.append(barge)

    for p in parts:
        k.move(p, x, y, z)

    return parts


def jp_profile(run, top, bottom, rows, side):
    import jp

    return jp.slope_profile(run, top, bottom, rows, side, th=0.14, step=0.05)


def gable(name, length, span, rise, at, overhang=0.4, color="fo_shingle", ridge="fo_shingle_dk", trim="fo_wood", bands=None, seams=1.0, shingle=False):
    if shingle:
        return shingle_roof(length, span, rise, at, overhang, bands or ("fo_shingle", "fo_shingle_lt", "fo_shingle_dk", "fo_shingle"), ridge, trim)

    return k.gable_roof(name, length, span, rise, at, overhang=overhang, thickness=0.16, color=color, trim=trim, ridge=ridge, seams=seams)


def post(x, y, z0, z1, r=0.1, color=("fo_wood", "fo_wood_lt"), sides=6):
    return nk.tube("post", [(x, y, z0), (x, y, z1)], [r, r * 0.92], sides, list(color), cap_top="fo_wood_dk", cap_bottom=True)


def rail(x0, y0, x1, y1, z, h=0.95, posts=4, color="fo_wood"):
    items = []

    for i in range(posts + 1):
        t = i / posts
        items.append(nk.bar((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z + h), 0.045, color, 5))

    items.append(nk.bar((x0, y0, z + h), (x1, y1, z + h), 0.05, color, 5))
    items.append(nk.bar((x0, y0, z + h * 0.45), (x1, y1, z + h * 0.45), 0.035, color, 5))

    return items


def stone_stack(x, y, z0, z1, w, d, seed, taper=0.0, color=("fo_stone", "fo_stone_lt", "fo_stone_dk")):
    items = []
    rnd = random.Random(seed)
    z = z0
    row = 0

    while z < z1 - 0.1:
        hh = rnd.uniform(0.28, 0.38)
        hh = min(hh, z1 - z)
        kk = 1 - taper * (z - z0) / max(z1 - z0, 0.1)
        n = 3 if row % 2 == 0 else 2
        ww = w * kk / n

        for i in range(n):
            ox = -w * kk / 2 + ww * (i + 0.5)
            items.append(nk.bevbox((ww * 0.97, d * kk, hh * 0.96), (x + ox + rnd.uniform(-0.02, 0.02), y, z), color[rnd.randrange(3)], 0.03))

        z += hh
        row += 1

    return items


def foundation(w, d, x=0.0, y=0.0, h=0.32, color="fo_stone"):
    items = [nk.bevbox((w, d, h), (x, y, 0), color, 0.04)]
    rnd = random.Random(7)

    for i in range(int((w + d) * 0.6)):
        t = rnd.random()
        tone = "fo_stone_lt" if i % 2 else "fo_stone_dk"

        if i % 2:
            items.append(nk.plain((rnd.uniform(0.3, 0.55), 0.06, h * 0.6), (x + (t - 0.5) * w, y + (d / 2 if i % 4 == 1 else -d / 2), 0.02), tone))
        else:
            items.append(nk.plain((0.06, rnd.uniform(0.3, 0.55), h * 0.6), (x + (w / 2 if i % 4 == 0 else -w / 2), y + (t - 0.5) * d, 0.02), tone))

    return items


def shed_roof(length, run, rise, at_back, z, bands=("fo_shingle", "fo_shingle_lt", "fo_shingle_dk", "fo_shingle")):
    rows = max(4, int(run / 0.36))
    ob = k.sweep("shed", jp_profile(run, rise, 0.0, rows, -1), length, (0, 0, 0), idx(bands[0]), axis="y")
    k.rotate(ob, 90)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        if p.normal.z > 0.2:
            row = int(abs(p.center.y) / (run / rows))
            attr.data[p.index].value = idx(bands[row % len(bands)])

    k.move(ob, 0, at_back, z)
    side = [nk.bevbox((0.1, run + 0.06, 0.2), (sx * (length / 2 + 0.04), at_back - run / 2, z), "fo_wood_dk", 0.02) for sx in (-1, 1)]

    return [ob] + side
