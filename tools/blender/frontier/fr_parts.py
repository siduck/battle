import math

from mathutils import Vector

from fr_kit import FONT, hash01, pick


def spans(a, b, cuts):
    out = []
    cur = a

    for c0, c1 in sorted(cuts):
        if c0 > cur:
            out.append((cur, min(c0, b)))

        cur = max(cur, c1)

    if cur < b:
        out.append((cur, b))

    return [s for s in out if s[1] - s[0] > 0.04]


def bands(z0, z1, openings, step):
    marks = {z0, z1}
    z = z0 + step

    while z < z1 - 0.08:
        marks.add(round(z, 3))
        z += step

    for _, oz, _, oh in openings:
        for v in (oz, oz + oh):
            if z0 < v < z1:
                marks.add(v)

    marks = sorted(marks)

    return list(zip(marks, marks[1:]))


def cuts_for(openings, v0, v1):
    return [(cx - w / 2, cx + w / 2) for cx, oz, w, h in openings if oz < v1 - 1e-4 and oz + h > v0 + 1e-4]


def clap(m, a, b, z0, z1, fam, openings=(), seed=0, step=0.34):
    for v0, v1 in bands(z0, z1, openings, step):
        if v1 - v0 < 0.01:
            continue

        col = pick(fam, int((v0 - z0) / step), seed, 3)

        for s0, s1 in spans(a, b, cuts_for(openings, v0, v1)):
            m.quad((s0, -0.045, v0), (s1, -0.045, v0), (s1, -0.008, v1), (s0, -0.008, v1), col)
            m.quad((s0, 0.0, v0), (s1, 0.0, v0), (s1, -0.045, v0), (s0, -0.045, v0), fam + "_d")


def slices(a, b, openings):
    marks = {a, b}

    for cx, _, w, _ in openings:
        for u in (cx - w / 2, cx + w / 2):
            if a + 0.015 < u < b - 0.015:
                marks.add(u)

    marks = sorted(marks)

    return list(zip(marks, marks[1:]))


def planks(m, a, b, z0, z1, fam, openings=(), seed=0, width=0.46, batten=2):
    n = max(1, int(round((b - a) / width)))
    w = (b - a) / n

    for i in range(n):
        u0 = a + i * w
        u1 = u0 + w
        col = pick(fam, i, seed, 7)
        depth = -0.018 if i % 2 else -0.006

        for lo, hi in slices(u0, u1, openings):
            mid = (lo + hi) / 2
            cuts = [(oz, oz + oh) for cx, oz, ow, oh in openings if cx - ow / 2 < mid < cx + ow / 2]

            for v0, v1 in spans(z0, z1, cuts):
                m.quad((lo, depth, v0), (hi, depth, v0), (hi, depth, v1), (lo, depth, v1), col)

        if batten and i % batten == 0 and i > 0:
            for v0, v1 in spans(z0, z1, [(oz, oz + oh) for cx, oz, ow, oh in openings if cx - ow / 2 - 0.05 < u0 < cx + ow / 2 + 0.05]):
                m.box((u0 - 0.035, -0.05, v0), (u0 + 0.035, -0.005, v1), fam + "_d", skip="YzZ")


def stone(m, a, b, z0, z1, fam, openings=(), seed=0, row=0.48, length=1.2):
    for v0, v1 in bands(z0, z1, openings, row):
        r = int((v0 - z0) / row + 0.5)

        for s0, s1 in spans(a, b, cuts_for(openings, v0, v1)):
            m.quad((s0, 0.0, v0), (s1, 0.0, v0), (s1, 0.0, v1), (s0, 0.0, v1), fam + "_d")
            u = s0 + (length * 0.5 if r % 2 else 0.0)
            first = s0

            while first < s1 - 0.05:
                end = u + length * (0.8 + 0.45 * hash01(r, u, seed)) if u > first else first + length * 0.5
                end = min(end, s1)

                if s1 - end < 0.2:
                    end = s1

                g = 0.022
                col = pick(fam, r, first, seed)
                m.quad((first + g, -0.04, v0 + g), (end - g, -0.04, v0 + g), (end - g, -0.02, v1 - g), (first + g, -0.02, v1 - g), col)
                m.quad((first + g, 0.0, v0 + g), (end - g, 0.0, v0 + g), (end - g, -0.04, v0 + g), (first + g, -0.04, v0 + g), fam + "_d")
                first = end
                u = end


def plaster(m, a, b, z0, z1, fam, openings=(), seed=0, chips=6):
    for v0, v1 in bands(z0, z1, openings, 99):
        for s0, s1 in spans(a, b, cuts_for(openings, v0, v1)):
            m.quad((s0, -0.008, v0), (s1, -0.008, v0), (s1, -0.008, v1), (s0, -0.008, v1), fam)

    for i in range(chips):
        side = -1 if i % 2 else 1
        u = (a + 0.35) if side < 0 else (b - 0.35)
        u += side * -0.5 * hash01(i, seed)
        z = z0 + 0.25 + (z1 - z0 - 0.6) * hash01(i, seed, 5)

        if any(abs(u - cx) < w / 2 + 0.35 and oz - 0.2 < z < oz + h + 0.1 for cx, oz, w, h in openings):
            continue

        for j, (du, dz) in enumerate(((0, 0), (0.16, 0.13), (-0.12, 0.13))):
            if j and hash01(i, j, seed) < 0.4:
                continue

            m.box((u + du - 0.13, -0.035, z + dz), (u + du + 0.13, -0.004, z + dz + 0.11), pick("rust", i, j), skip="Y")


def reveal(m, cx, z, w, h, depth, col, floor=True):
    a, b = cx - w / 2, cx + w / 2
    t = z + h
    m.orient([(a, -0.01, z), (a, depth, z), (a, depth, t), (a, -0.01, t)], (1, 0, 0), col)
    m.orient([(b, -0.01, z), (b, depth, z), (b, depth, t), (b, -0.01, t)], (-1, 0, 0), col)
    m.orient([(a, -0.01, t), (b, -0.01, t), (b, depth, t), (a, depth, t)], (0, 0, -1), col)

    if floor:
        m.orient([(a, -0.01, z), (b, -0.01, z), (b, depth, z), (a, depth, z)], (0, 0, 1), col)


def pane(m, cx, z, w, h, y, a="glass", b="glass_l"):
    x0, x1 = cx - w / 2, cx + w / 2
    m.quad((x0, y, z), (x1, y, z), (x1, y, z + h), (x0, y, z + h), a)
    m.quad((x0 + w * 0.12, y - 0.006, z + h * 0.08), (x0 + w * 0.36, y - 0.006, z + h * 0.08), (x0 + w * 0.82, y - 0.006, z + h * 0.92), (x0 + w * 0.58, y - 0.006, z + h * 0.92), b)


def window(m, cx, z, w, h, frame="cream", shutter=None, hood=True, bars=False, sill=True):
    t = 0.09
    reveal(m, cx, z, w, h, 0.14, "wood_x")
    pane(m, cx, z, w, h, 0.13)

    for s in (-1, 1):
        u = cx + s * (w / 2 + t / 2 - 0.01)
        m.box((u - t / 2, -0.07, z), (u + t / 2, 0.02, z + h), frame, skip="YzZ")

    m.box((cx - w / 2 - t, -0.07, z + h), (cx + w / 2 + t, 0.02, z + h + t), frame, skip="Y")

    if sill:
        m.box((cx - w / 2 - t - 0.06, -0.15, z - 0.09), (cx + w / 2 + t + 0.06, 0.02, z), frame, 0.02, skip="Y")

    if hood:
        m.box((cx - w / 2 - t - 0.09, -0.15, z + h + t), (cx + w / 2 + t + 0.09, 0.0, z + h + t + 0.09), frame, skip="Y")

    if bars:
        n = max(2, int(w / 0.29))

        for i in range(1, n):
            u = cx - w / 2 + w * i / n
            m.box((u - 0.022, -0.035, z), (u + 0.022, 0.005, z + h), "iron_d", skip="zZ")
    elif w > 1.5:
        for u in (cx - w / 6, cx + w / 6):
            m.box((u - 0.03, 0.06, z), (u + 0.03, 0.125, z + h), frame, skip="YzZ")
    else:
        m.box((cx - w / 2, 0.06, z + h * 0.52), (cx + w / 2, 0.125, z + h * 0.52 + 0.06), frame, skip="YxX")

    if shutter:
        sw = w * 0.46

        for s in (-1, 1):
            u = cx + s * (w / 2 + t + sw / 2 + 0.03)
            m.box((u - sw / 2, -0.075, z), (u + sw / 2, -0.015, z + h), shutter, skip="Y")

            for k in (0.14, 0.55):
                m.quad((u - sw / 2 + 0.06, -0.078, z + h * k), (u + sw / 2 - 0.06, -0.078, z + h * k), (u + sw / 2 - 0.06, -0.078, z + h * (k + 0.3)), (u - sw / 2 + 0.06, -0.078, z + h * (k + 0.3)), shutter + "_d")


def door(m, cx, z, w, h, fam="wood", frame="cream", glazed=True, double=False, step=True):
    t = 0.12
    reveal(m, cx, z, w, h, 0.14, "wood_x", floor=False)
    leaves = [(cx - w / 4, w / 2 - 0.02), (cx + w / 4, w / 2 - 0.02)] if double else [(cx, w)]

    for u, lw in leaves:
        m.quad((u - lw / 2, 0.11, z), (u + lw / 2, 0.11, z), (u + lw / 2, 0.11, z + h), (u - lw / 2, 0.11, z + h), fam)
        inner = lw - 0.24
        m.box((u - inner / 2, 0.075, z + 0.18), (u + inner / 2, 0.115, z + h * 0.45), fam + "_l", skip="Y")

        if glazed:
            pane(m, u, z + h * 0.55, inner, h * 0.34, 0.1)
        else:
            m.box((u - inner / 2, 0.075, z + h * 0.55), (u + inner / 2, 0.115, z + h * 0.9), fam + "_l", skip="Y")

        knob = u + (lw / 2 - 0.1) * (1 if u <= cx else -1)
        m.box((knob - 0.035, 0.05, z + h * 0.47), (knob + 0.035, 0.11, z + h * 0.52), "gold", skip="Y")

    for s in (-1, 1):
        u = cx + s * (w / 2 + t / 2 - 0.01)
        m.box((u - t / 2, -0.08, z), (u + t / 2, 0.02, z + h), frame, skip="Yz")

    m.box((cx - w / 2 - t - 0.06, -0.12, z + h), (cx + w / 2 + t + 0.06, 0.02, z + h + 0.18), frame, 0.025, skip="Y")

    if step:
        m.box((cx - w / 2 - 0.15, -0.32, z - 0.14), (cx + w / 2 + 0.15, 0.02, z), "gray", 0.02, skip="Y")


def batwing(m, cx, z, w, h):
    reveal(m, cx, z, w, h, 0.28, "wood_x", floor=False)
    m.quad((cx - w / 2, 0.27, z), (cx + w / 2, 0.27, z), (cx + w / 2, 0.27, z + h), (cx - w / 2, 0.27, z + h), "void")
    lw = w / 2 - 0.07

    for s in (-1, 1):
        u = cx + s * (lw / 2 + 0.04)
        m.box((u - lw / 2, -0.01, z + 0.75), (u + lw / 2, 0.06, z + 0.9), "ochre", 0.02)
        m.box((u - lw / 2, -0.01, z + 1.72), (u + lw / 2, 0.06, z + 1.9), "ochre", 0.02)

        for e in (-1, 1):
            m.box((u + e * (lw / 2 - 0.04) - 0.04, -0.01, z + 0.9), (u + e * (lw / 2 - 0.04) + 0.04, 0.06, z + 1.72), "ochre", skip="zZ")

        for i in range(5):
            v = z + 0.94 + i * 0.155
            m.quad((u - lw / 2 + 0.08, 0.0, v), (u + lw / 2 - 0.08, 0.0, v), (u + lw / 2 - 0.08, 0.04, v + 0.1), (u - lw / 2 + 0.08, 0.04, v + 0.1), "ochre_d")

    for s in (-1, 1):
        u = cx + s * (w / 2 + 0.07)
        m.box((u - 0.08, -0.09, z), (u + 0.08, 0.02, z + h), "cream", 0.02, skip="Yz")

    m.box((cx - w / 2 - 0.2, -0.13, z + h), (cx + w / 2 + 0.2, 0.02, z + h + 0.2), "cream", 0.025, skip="Y")


def sign(m, cx, z, w, h, word, bg="cream", fg="wood_x", trim="wood_d", y=-0.06):
    m.box((cx - w / 2, y - 0.08, z), (cx + w / 2, y + 0.08, z + h), bg, 0.02, skip="Y")

    for v in (z - 0.07, z + h):
        m.box((cx - w / 2 - 0.08, y - 0.12, v), (cx + w / 2 + 0.08, y + 0.06, v + 0.07), trim, 0.015, skip="Y")

    for u in (cx - w / 2 - 0.08, cx + w / 2):
        m.box((u, y - 0.11, z), (u + 0.08, y + 0.06, z + h), trim, skip="YzZ")

    px = h * 0.64 / 7
    span = (sum(len(FONT[c][0]) + 1 for c in word) - 1) * px
    size = h * 0.64 * min(1.0, (w - 0.35) / span)
    m.text(word, cx, z + (h - size) / 2, size, fg, y - 0.087)


def cornice(m, a, b, z, col="cream", deep=0.24, spacing=0.9, brackets=True):
    m.box((a - 0.08, -deep, z), (b + 0.08, 0.04, z + 0.12), col, 0.025, skip="Y")
    m.box((a - 0.03, -deep * 0.55, z - 0.1), (b + 0.03, 0.02, z), "cream_d" if col == "cream" else "wood_d", skip="YZ")

    if brackets:
        n = max(2, int((b - a) / spacing) + 1)

        for i in range(n):
            u = a + 0.12 + (b - a - 0.24) * i / (n - 1)
            m.extrude([(u - 0.06, z - 0.32), (u + 0.06, z - 0.32), (u + 0.06, z - 0.1), (u - 0.06, z - 0.1)], -deep * 0.5, 0.0, col, back=False)


def posts(m, xs, y, z0, z1, col, size=0.18, braces=True, bw=0.4):
    for i, u in enumerate(xs):
        m.box((u - size / 2, y - size / 2, z0), (u + size / 2, y + size / 2, z1), col, 0.03, skip="zZ")
        m.box((u - size * 0.72, y - size * 0.72, z0), (u + size * 0.72, y + size * 0.72, z0 + 0.14), col + "_d" if col in ("wood", "gray", "red", "teal", "sage", "slate", "ochre") else "wood_d", 0.02, skip="z")

        if braces:
            for s in (-1, 1):
                if (s < 0 and i == 0) or (s > 0 and i == len(xs) - 1):
                    continue

                m.beam((u, y, z1 - bw - 0.05), (u + s * bw, y, z1 - 0.03), 0.09, 0.09, col, skip="xX")


def deck(m, x0, x1, y0, y1, z=0.2, fam="wood", along="y"):
    n = max(1, int((x1 - x0) / 0.42))
    w = (x1 - x0) / n

    for i in range(n):
        u = x0 + i * w
        m.quad((u + 0.012, y0, z), (u + w - 0.012, y0, z), (u + w - 0.012, y1, z), (u + 0.012, y1, z), pick(fam, i, y0))

    m.quad((x0, y0, z - 0.025), (x1, y0, z - 0.025), (x1, y1, z - 0.025), (x0, y1, z - 0.025), "wood_x")
    m.box((x0, y0 - 0.05, z - 0.16), (x1, y0 + 0.04, z - 0.004), "wood_d", 0.015, skip="Y")

    for u in (x0, x1):
        m.box((u - 0.04, y0, z - 0.16), (u + 0.04, y1, z - 0.004), "wood_d", skip="y")


    if z < 1.0:
        m.box((x0 + 0.1, y0 + 0.08, -0.3), (x1 - 0.1, y0 + 0.12, z - 0.03), "wood_x", skip="Yz")


def balusters(m, a, b, y, z, h=1.0, col="cream", step=0.3):
    m.box((a, y - 0.05, z + h - 0.09), (b, y + 0.05, z + h), col)
    m.box((a, y - 0.03, z + 0.1), (b, y + 0.03, z + 0.16), col, skip="xX")
    n = max(1, int((b - a) / step))

    for i in range(1, n):
        u = a + (b - a) * i / n
        m.box((u - 0.03, y - 0.03, z + 0.16), (u + 0.03, y + 0.03, z + h - 0.09), col, skip="zZ")

    for u in (a, b):
        m.box((u - 0.07, y - 0.07, z), (u + 0.07, y + 0.07, z + h), col, 0.02, skip="z")


def slope(m, x0, x1, low, high, kind="shingle", fam="shingle", under="wood_x", thick=0.09, seed=0, row=0.5, rib=0.55):
    ya, za = low
    yb, zb = high
    d = Vector((0, yb - ya, zb - za))
    length = d.length
    n = Vector((1, 0, 0)).cross(d).normalized()

    if n.z < 0:
        n = -n

    def at(x, t, lift=0.0):
        return (x, ya + d.y * t + n.y * lift, za + d.z * t + n.z * lift)

    up = (0, n.y, n.z)

    if kind == "shingle":
        rows = max(2, int(length / row))

        for i in range(rows):
            t0 = i / rows
            t1 = (i + 1) / rows
            cuts = [x0]
            u = x0 + (x1 - x0) * (0.2 + 0.6 * hash01(i, seed))
            cuts += [u, x1]

            for j in range(len(cuts) - 1):
                col = pick(fam, i, j, seed)
                a, b = cuts[j], cuts[j + 1]
                m.orient([at(a, t0, 0.055), at(b, t0, 0.055), at(b, t1, 0.008), at(a, t1, 0.008)], up, col)

            m.orient([at(x0, t0, 0.0), at(x1, t0, 0.0), at(x1, t0, 0.055), at(x0, t0, 0.055)], (0, -d.y, -d.z), fam + "_d")
    elif kind == "tin":
        count = max(1, int((x1 - x0) / rib))
        w = (x1 - x0) / count

        for i in range(count):
            a = x0 + i * w
            col = pick(fam, i, seed)

            if hash01(i, seed, 9) < 0.18:
                col = "rust" if fam == "tin" else "rust_l"

            prof = [(a, 0.012), (a + w * 0.58, 0.012), (a + w * 0.7, 0.07), (a + w * 0.88, 0.07), (a + w, 0.012)]

            for (p, h0), (q, h1) in zip(prof, prof[1:]):
                m.orient([at(p, 0, h0), at(q, 0, h1), at(q, 1, h1), at(p, 1, h0)], up, col)

            m.orient([at(prof[1][0], 0, 0.012), at(prof[2][0], 0, 0.07), at(prof[3][0], 0, 0.07), at(prof[4][0], 0, 0.012)], (0, -d.y, -d.z), fam + "_d")
    else:
        count = max(1, int((x1 - x0) / 0.5))
        w = (x1 - x0) / count

        for i in range(count):
            a = x0 + i * w
            col = fam if i % 2 == 0 else kind
            m.orient([at(a, 0, 0.012), at(a + w, 0, 0.012), at(a + w, 1, 0.012), at(a, 1, 0.012)], up, col)
            drop = [(a, 0.0), (a + w / 2, -0.16), (a + w, 0.0)]
            p0, p1, p2 = [(x, ya - 0.004, za + dz) for x, dz in drop]
            m.orient([(a, ya - 0.004, za + 0.02), p0, p1, p2, (a + w, ya - 0.004, za + 0.02)], (0, -1, 0), col)

    m.orient([at(x0, 0, -thick), at(x1, 0, -thick), at(x1, 1, -thick), at(x0, 1, -thick)], (0, -n.y, -n.z), under)

    for x, s in ((x0, -1), (x1, 1)):
        m.orient([at(x, 0, -thick - 0.03), at(x, 1, -thick - 0.03), at(x, 1, 0.075), at(x, 0, 0.075)], (s, 0, 0), "wood_d")

    for t, s in ((0, -1), (1, 1)):
        m.orient([at(x0, t, -thick - 0.03), at(x1, t, -thick - 0.03), at(x1, t, 0.012), at(x0, t, 0.012)], (0, s * d.y, s * d.z), "wood_d")


def roof_y(m, x0, x1, y0, y1, profile, kind, fam, seed=0, over=0.25, trim="cream"):
    for side in (-1, 1):
        with m.at(0, 0, 0, yaw=90):
            pts = [(x, z) for x, z in profile if x * side <= 1e-6]
            pts.sort(key=lambda p: -abs(p[0]))

            for i in range(len(pts) - 1):
                (xa, za), (xb, zb) = pts[i], pts[i + 1]
                low = (-xa, za)
                high = (-xb, zb)
                slope(m, y0 - over, y1 + over, low, high, kind, fam, seed=seed + i + side)

    for i in range(len(profile) - 1):
        (xa, za), (xb, zb) = profile[i], profile[i + 1]

        for y in (y0 - over, y1 + over):
            m.beam((xa, y, za - 0.04), (xb, y, zb - 0.04), 0.1, 0.2, trim, skip="")

    top = max(z for _, z in profile)
    m.box((-0.12, y0 - over - 0.06, top - 0.02), (0.12, y1 + over + 0.06, top + 0.12), fam + "_d", 0.03)


def gable_wall(m, profile, z0, fam, openings=(), seed=0, width=0.46):
    xa = profile[0][0]
    xb = profile[-1][0]
    n = max(1, int(round((xb - xa) / width)))
    w = (xb - xa) / n

    def top(x):
        for (a, za), (b, zb) in zip(profile, profile[1:]):
            if a - 1e-6 <= x <= b + 1e-6:
                return za + (zb - za) * (x - a) / max(b - a, 1e-6)

        return z0

    for i in range(n):
        left = xa + i * w
        depth = -0.018 if i % 2 else -0.006
        col = pick(fam, i, seed, 11)

        for a, b in slices(left, left + w, openings):
            mid = (a + b) / 2
            mids = [x for x, _ in profile if a + 1e-4 < x < b - 1e-4]
            edge = [a] + mids + [b]
            low = z0

            for c0, c1 in sorted((oz, oz + oh) for cx, oz, ow, oh in openings if cx - ow / 2 < mid < cx + ow / 2):
                if c0 > low:
                    m.quad((a, depth, low), (b, depth, low), (b, depth, c0), (a, depth, c0), col)

                low = max(low, c1)

            crown = [(x, depth, max(top(x) - 0.06, low)) for x in reversed(edge)]

            if max(q[2] for q in crown) <= low + 0.02:
                continue

            clean = []

            for q in [(a, depth, low), (b, depth, low)] + crown:
                if not clean or (Vector(q) - Vector(clean[-1])).length > 1e-4:
                    clean.append(q)

            if len(clean) > 2 and (Vector(clean[0]) - Vector(clean[-1])).length < 1e-4:
                clean.pop()

            if len(clean) > 2:
                m.face(clean, col)


def false_front(m, outline, fam, trim="cream", thick=0.22, back="wood_d"):
    z_base = min(z for _, z in outline)
    m.extrude(outline, 0.012, thick, back)
    tops = [p for p in outline if p[1] > z_base + 0.01]
    tops.sort()

    for (a, za), (b, zb) in zip(tops, tops[1:]):
        if abs(a - b) < 0.02:
            continue

        m.beam((a - 0.05, thick / 2 - 0.04, za + 0.04), (b + 0.05, thick / 2 - 0.04, zb + 0.04), thick + 0.16, 0.14, trim, 0.025)


def chimney(m, x, y, z0, z1, size=0.55, fam="rust"):
    m.box((x - size / 2, y - size / 2, z0), (x + size / 2, y + size / 2, z1 - 0.2), fam, 0.03, skip="z")

    for i in range(int((z1 - z0) / 0.55)):
        v = z0 + 0.35 + i * 0.55

        if v < z1 - 0.4:
            m.box((x - size / 2 - 0.025, y - size / 2 - 0.025, v), (x + size / 2 + 0.025, y + size / 2 + 0.025, v + 0.07), fam + "_d", skip="z")

    m.box((x - size / 2 - 0.09, y - size / 2 - 0.09, z1 - 0.2), (x + size / 2 + 0.09, y + size / 2 + 0.09, z1 - 0.06), "stone_d", 0.03)
    m.box((x - size * 0.26, y - size * 0.26, z1 - 0.06), (x + size * 0.26, y + size * 0.26, z1), "iron_d", skip="z")


def stovepipe(m, x, y, z0, z1, r=0.13):
    m.prism((x, y), z0, z1 - 0.18, r, r, 8, "iron", top=False)
    m.prism((x, y), z0 + (z1 - z0) * 0.55, z0 + (z1 - z0) * 0.55 + 0.08, r * 1.2, r * 1.2, 8, "iron_d")
    m.prism((x, y), z1 - 0.2, z1 - 0.02, r * 1.9, 0.03, 8, "iron_d", top=False, bottom=True)


def barrel(m, x, y, z=0.0, r=0.3, h=0.8, n=10, fam="wood"):
    prof = [(r * 0.84, z), (r * 0.99, z + h * 0.3), (r, z + h * 0.5), (r * 0.99, z + h * 0.7), (r * 0.84, z + h)]
    m.lathe((x, y), prof, n, lambda i, j: pick(fam, i, x, y), top=False)

    for k in (0.13, 0.8):
        rr = r * 0.93
        m.prism((x, y), z + h * k, z + h * (k + 0.075), rr + 0.012, rr + 0.012, n, "iron", top="iron", bottom=True)

    m.prism((x, y), z + h - 0.05, z + h - 0.035, r * 0.8, r * 0.8, n, fam + "_d")


def crate(m, x, y, z, sx, sy, sz, yaw=0.0, fam="wood", brace=True):
    with m.at(x, y, z, yaw=yaw):
        hx, hy = sx / 2, sy / 2
        t = min(sx, sy, sz) * 0.13
        m.box((-hx + 0.025, -hy + 0.025, 0.0), (hx - 0.025, hy - 0.025, sz - 0.025), fam, skip="z")

        for ex in (-1, 1):
            for ey in (-1, 1):
                m.box((ex * hx - (t if ex > 0 else 0), ey * hy - (t if ey > 0 else 0), 0.0), (ex * hx + (0 if ex > 0 else t), ey * hy + (0 if ey > 0 else t), sz), fam + "_d", 0.014, skip="z")

        for v in (0.0, sz - t):
            for ey in (-1, 1):
                m.box((-hx + t, ey * hy - (t if ey > 0 else 0), v), (hx - t, ey * hy + (0 if ey > 0 else t), v + t), fam + "_l", skip="xXz" if v == 0 else "xX")

            for ex in (-1, 1):
                m.box((ex * hx - (t if ex > 0 else 0), -hy + t, v), (ex * hx + (0 if ex > 0 else t), hy - t, v + t), fam + "_l", skip="yYz" if v == 0 else "yY")

        if brace:
            for ey in (-1, 1):
                m.beam((-hx + t, ey * (hy - 0.018), t), (hx - t, ey * (hy - 0.018), sz - t), 0.028, t * 0.85, fam + "_l", skip="xX")

            for ex in (-1, 1):
                m.beam((ex * (hx - 0.018), -hy + t, t), (ex * (hx - 0.018), hy - t, sz - t), 0.028, t * 0.85, fam + "_l", skip="xX")

        n = max(2, int(sx / 0.28))

        for i in range(n):
            a = -hx + t + (sx - 2 * t) * i / n
            b = a + (sx - 2 * t) / n
            m.quad((a + 0.008, -hy + t, sz - 0.018), (b - 0.008, -hy + t, sz - 0.018), (b - 0.008, hy - t, sz - 0.018), (a + 0.008, hy - t, sz - 0.018), pick(fam, i, x))


def sack(m, x, y, z, s=1.0, yaw=0.0, fam="canvas"):
    with m.at(x, y, z, yaw=yaw):
        rings = [(0.24, 0.0), (0.31, 0.12), (0.29, 0.34), (0.17, 0.5), (0.07, 0.56), (0.11, 0.66)]
        m.loft([m.ring((0, 0), r * s, h * s, 8, 0.4, 0.82) for r, h in rings], lambda i, j: fam + "_d" if j == 3 else pick(fam, i // 3, x), fam + "_l")


def trough(m, x, y, w=1.6, d=0.45, h=0.55):
    m.box((x - w / 2, y - d / 2, 0.12), (x + w / 2, y - d / 2 + 0.07, h), "wood", 0.015)
    m.box((x - w / 2, y + d / 2 - 0.07, 0.12), (x + w / 2, y + d / 2, h), "wood", 0.015)

    for s in (-1, 1):
        u = x + s * (w / 2 - 0.035)
        m.box((u - 0.035, y - d / 2 + 0.07, 0.12), (u + 0.035, y + d / 2 - 0.07, h), "wood_l", skip="yY")
        m.box((x + s * (w / 2 - 0.22) - 0.06, y - d / 2 - 0.02, 0.0), (x + s * (w / 2 - 0.22) + 0.06, y + d / 2 + 0.02, 0.16), "wood_d", 0.015, skip="z")

    m.quad((x - w / 2 + 0.07, y - d / 2 + 0.07, h - 0.08), (x + w / 2 - 0.07, y - d / 2 + 0.07, h - 0.08), (x + w / 2 - 0.07, y + d / 2 - 0.07, h - 0.08), (x - w / 2 + 0.07, y + d / 2 - 0.07, h - 0.08), "water")


def bench(m, x, y, z, w=1.5, fam="wood"):
    m.box((x - w / 2, y - 0.2, z + 0.4), (x + w / 2, y + 0.18, z + 0.47), fam + "_l", 0.015)
    m.box((x - w / 2, y + 0.15, z + 0.62), (x + w / 2, y + 0.2, z + 0.86), fam, 0.012)

    for s in (-1, 1):
        u = x + s * (w / 2 - 0.12)
        m.box((u - 0.04, y - 0.16, z), (u + 0.04, y - 0.09, z + 0.4), fam + "_d", skip="zZ")
        m.box((u - 0.04, y + 0.11, z), (u + 0.04, y + 0.18, z + 0.86), fam + "_d", skip="z")


def lamp(m, x, y, z, s=1.0):
    m.prism((x, y), z, z + 0.05 * s, 0.1 * s, 0.13 * s, 6, "iron_d", bottom=True)
    m.prism((x, y), z + 0.05 * s, z + 0.3 * s, 0.1 * s, 0.14 * s, 6, "lamp", top=False)
    m.prism((x, y), z + 0.3 * s, z + 0.44 * s, 0.19 * s, 0.03 * s, 6, "iron_d", bottom=True)


def stairs(m, x, y, w, n=2, top=0.2, depth=0.28, fam="wood"):
    for i in range(n):
        h = top * (n - i) / (n + 1)
        m.box((x - w / 2, y - depth * (i + 1), -0.1), (x + w / 2, y - depth * i, h), fam + "_l" if i % 2 else fam, 0.02, skip="zY")


def star(m, x, z, r, y, col="gold"):
    pts = []

    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, z + math.sin(a) * rr))

    m.extrude(pts, y - 0.05, y, col, back=False)


def disc(m, x, z, r, y, col, n=12, thick=0.05):
    pts = [(x + math.cos(2 * math.pi * i / n) * r, z + math.sin(2 * math.pi * i / n) * r) for i in range(n)]
    m.extrude(pts, y - thick, y, col, back=False)


def foundation(m, x0, y0, x1, y1, h=0.12, fam="stone"):
    m.box((x0, y0, -1.0), (x1, y1, h), fam + "_d", 0.03, skip="z")


def corner_boards(m, x0, y0, x1, y1, z0, z1, col="cream", s=0.1):
    for x in (x0, x1):
        for y in (y0, y1):
            m.box((x - s, y - s, z0), (x + s, y + s, z1), col, 0.025, skip="z")
