import math

from mathutils import Matrix, Vector

import ck

DEPTH = 0.17


def win(x, z, w=0.74, h=1.05, **style):
    d = {"x": x, "z": z, "w": w, "h": h, "kind": "win"}
    d.update(style)

    return d


def door(x, w=1.0, h=2.22, z=0.0, **style):
    d = {"x": x, "z": z, "w": w, "h": h, "kind": "door"}
    d.update(style)

    return d


def flat(x0, x1, z0, z1, y, col, ao=True):
    return ck.Poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col, False, ao, False)


def wall_face(width, z0, z1, openings, col):
    out = ck.Part()

    if ck.LOD >= 2:
        out.append(ck.Poly([(0, 0, z0), (width, 0, z0), (width, 0, z1), (0, 0, z1)], col))

        return out

    rects = [(o["x"] - o["w"] / 2, o["x"] + o["w"] / 2, max(o["z"], z0), min(o["z"] + o["h"], z1)) for o in openings]
    zs = sorted({z0, z1, *[r[2] for r in rects], *[r[3] for r in rects]})
    spans = []

    for za, zb in zip(zs, zs[1:]):
        if zb - za < 1e-4:
            continue

        zm = (za + zb) / 2
        cuts = sorted((r[0], r[1]) for r in rects if r[2] < zm < r[3])
        cur = 0.0
        row = []

        for a, b in cuts:
            if a > cur + 1e-4:
                row.append((cur, a))

            cur = max(cur, b)

        if width > cur + 1e-4:
            row.append((cur, width))

        for a, b in row:
            for s in spans:
                if abs(s[0] - a) < 1e-4 and abs(s[1] - b) < 1e-4 and abs(s[3] - za) < 1e-4:
                    s[3] = zb
                    break
            else:
                spans.append([a, b, za, zb])

    for a, b, za, zb in spans:
        out.append(ck.Poly([(a, 0, za), (b, 0, za), (b, 0, zb), (a, 0, zb)], col))

    return out


def shutters(o, col):
    out = ck.Part()
    x0, x1 = o["x"] - o["w"] / 2, o["x"] + o["w"] / 2
    z0, z1 = o["z"], o["z"] + o["h"]
    sw = o["w"] * 0.46

    for a, b in ((x0 - 0.1 - sw, x0 - 0.1), (x1 + 0.1, x1 + 0.1 + sw)):
        out += ck.box(a, -0.055, z0 - 0.02, b, 0.0, z1 + 0.02, col, d=1, skip="b")
        n = 5

        for i in range(n):
            zz = z0 + 0.08 + i * (o["h"] - 0.16) / n
            out += ck.box(a + 0.055, -0.072, zz + 0.025, b - 0.055, -0.05, zz + (o["h"] - 0.16) / n * 0.66, ck.shade(col, 1.14), d=0, skip="bd")

    return out


def fill(o, col):
    out = ck.Part()
    x0, x1 = o["x"] - o["w"] / 2, o["x"] + o["w"] / 2
    z0, z1 = o["z"], o["z"] + o["h"]
    accent = o.get("accent", "blue")
    trim = o.get("trim", "trim")
    kind = o["kind"]
    depth = o.get("depth", DEPTH)

    if ck.LOD >= 2:
        leaf = accent if kind == "door" else "glass"
        out.append(flat(x0, x1, z0, z1, -0.045, leaf, False))

        if kind == "win" and o.get("shutters", True):
            sw = o["w"] * 0.46

            for a, b in ((x0 - 0.1 - sw, x0 - 0.1), (x1 + 0.1, x1 + 0.1 + sw)):
                out.append(flat(a, b, z0, z1, -0.045, accent, False))

        return out

    reveal = ck.shade(col, 0.86)
    out.append(ck.Poly([(x0, 0, z0), (x0, depth, z0), (x0, depth, z1), (x0, 0, z1)], reveal))
    out.append(ck.Poly([(x1, 0, z0), (x1, 0, z1), (x1, depth, z1), (x1, depth, z0)], reveal))
    out.append(ck.Poly([(x0, 0, z1), (x0, depth, z1), (x1, depth, z1), (x1, 0, z1)], reveal))

    if z0 > 0.02:
        out.append(ck.Poly([(x0, 0, z0), (x1, 0, z0), (x1, depth, z0), (x0, depth, z0)], trim))

    if kind == "void":
        out.append(flat(x0, x1, z0, z1, depth, "void"))

        return out

    if kind == "door":
        f = 0.075
        out.append(flat(x0, x0 + f, z0, z1, depth - 0.001, ck.shade(accent, 0.72)))
        out.append(flat(x1 - f, x1, z0, z1, depth - 0.001, ck.shade(accent, 0.72)))
        out.append(flat(x0 + f, x1 - f, z1 - f, z1, depth - 0.001, ck.shade(accent, 0.72)))
        a, b = x0 + f, x1 - f
        n = 6 if ck.LOD == 0 else 2

        for i in range(n):
            u0, u1 = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
            tone = ck.shade(accent, 1.07 if i % 2 else 0.94)
            gap = 0.014 if ck.LOD == 0 else 0.0
            out.append(flat(u0, u1 - gap, z0, z1 - f, depth - 0.001, tone))

            if gap:
                out.append(flat(u1 - gap, u1, z0, z1 - f, depth - 0.001, ck.shade(accent, 0.62)))

        kx = x1 - 0.2
        out += ck.box(kx - 0.035, depth - 0.075, z0 + 1.0, kx + 0.035, depth - 0.001, z0 + 1.12, "gold", c=0.012, d=0, skip="b")
    else:
        f = 0.07
        mid = (x0 + x1) / 2
        y = depth - 0.001
        frame = accent
        out.append(flat(x0, x0 + f, z0, z1, y, frame))
        out.append(flat(x1 - f, x1, z0, z1, y, frame))
        out.append(flat(x0 + f, x1 - f, z0, z0 + f, y, ck.shade(frame, 1.08)))
        out.append(flat(x0 + f, x1 - f, z1 - f, z1, y, ck.shade(frame, 0.84)))
        out.append(flat(mid - f / 2, mid + f / 2, z0 + f, z1 - f, y, frame))
        out.append(flat(x0 + f, mid - f / 2, z0 + f, z1 - f, y, "glass"))
        zm = z0 + o["h"] * 0.5
        out.append(ck.Poly([(mid + f / 2, y, z0 + f), (x1 - f, y, z0 + f), (x1 - f, y, zm - 0.1)], "glass", False, True, False))
        out.append(ck.Poly([(mid + f / 2, y, z0 + f), (x1 - f, y, zm - 0.1), (x1 - f, y, z1 - f), (mid + f / 2, y, zm + 0.15)], "glass_lt", False, True, False))
        out.append(ck.Poly([(mid + f / 2, y, zm + 0.15), (x1 - f, y, z1 - f), (mid + f / 2, y, z1 - f)], "glass", False, True, False))

    if kind == "win" and o.get("sill", True):
        out += ck.box(x0 - 0.1, -0.075, z0 - 0.11, x1 + 0.1, 0.02, z0, o.get("sill_col", "stone_lt"), c=0.02, d=1, skip="b")

    lintel = o.get("lintel", "flat")

    if lintel == "flat":
        out += ck.box(x0 - 0.1, -0.055, z1, x1 + 0.1, 0.01, z1 + 0.13, trim, c=0.018, d=1, skip="b")

        if kind == "door":
            for a, b in ((x0 - 0.11, x0), (x1, x1 + 0.11)):
                out += ck.box(a, -0.04, z0, b, 0.01, z1, trim, c=0.012, d=1, skip="bd")
    elif lintel == "arch":
        out += arch_head(o["x"], z1, o["w"] / 2, o.get("rise", o["w"] * 0.5), accent, trim)

    if kind == "win" and o.get("shutters", True):
        out += shutters(o, accent)

    return out


def arch_points(cx, z, r, rise, n):
    return [(cx + math.cos(math.pi * i / n) * r, z + math.sin(math.pi * i / n) * rise) for i in range(n + 1)]


def arch_head(cx, z, r, rise, accent, trim, y=0.0, ring=0.13):
    out = ck.Part()
    n = 8 if ck.LOD == 0 else 4
    inner = arch_points(cx, z, r, rise, n)
    outer = arch_points(cx, z, r + ring, rise + ring, n)

    for i in range(n):
        a, b, c, d = inner[i], inner[i + 1], outer[i + 1], outer[i]
        tone = ck.shade(trim, 1.0 if i % 2 else 0.93)
        out.append(ck.Poly([(d[0], y - 0.055, d[1]), (c[0], y - 0.055, c[1]), (b[0], y - 0.055, b[1]), (a[0], y - 0.055, a[1])], tone, False, True, False))
        out.append(ck.Poly([(d[0], y, d[1]), (c[0], y, c[1]), (c[0], y - 0.055, c[1]), (d[0], y - 0.055, d[1])], trim, False, True, False))

    out.append(ck.Poly([(p[0], y - 0.03, p[1]) for p in inner], ck.shade(accent, 0.9), False, True, False))

    if ck.LOD == 0:
        for i in (2, 6):
            p = inner[i]
            dx, dz = p[0] - cx, p[1] - z
            side = Vector((-dz, dx)).normalized() * 0.014
            out.append(ck.Poly([(cx - side.x, y - 0.036, z + 0.02 - side.y), (cx + dx * 0.96 - side.x, y - 0.036, z + dz * 0.96 - side.y), (cx + dx * 0.96 + side.x, y - 0.036, z + dz * 0.96 + side.y), (cx + side.x, y - 0.036, z + 0.02 + side.y)], trim, False, False, False))

    return out


def orient(part, p0, p1):
    a = Vector((p0[0], p0[1], 0))
    t = Vector((p1[0], p1[1], 0)) - a
    t.normalize()
    inward = Vector((-t.y, t.x, 0))
    m = Matrix(((t.x, inward.x, 0, a.x), (t.y, inward.y, 0, a.y), (0, 0, 1, 0), (0, 0, 0, 1)))

    return part.xform(m)


def facade(p0, p1, z0, z1, col, openings=(), extra=None):
    width = (Vector((p1[0], p1[1])) - Vector((p0[0], p0[1]))).length
    part = wall_face(width, z0, z1, list(openings), col)

    for o in openings:
        part += fill(o, col)

    if extra:
        part += extra

    return orient(part, p0, p1)


def faces(h):
    return [((-h, -h), (h, -h)), ((h, -h), (h, h)), ((h, h), (-h, h)), ((-h, h), (-h, -h))]


def ring(h_out, h_in, z0, z1, side, top, inner=None, c=0.03, under=True):
    out = ck.Part()
    ch = c if ck.LOD == 0 else 0.0
    levels = [(h_out - ch, z0), (h_out, z0 + ch), (h_out, z1 - ch), (h_out - ch, z1)] if ch else [(h_out, z0), (h_out, z1)]

    def sq(h, z):
        return [(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z)]

    for (ha, za), (hb, zb) in zip(levels, levels[1:]):
        a, b = sq(ha, za), sq(hb, zb)

        for i in range(4):
            j = (i + 1) % 4
            out.append(ck.Poly([a[i], a[j], b[j], b[i]], side))

    a, b = sq(levels[-1][0], z1), sq(h_in, z1)

    for i in range(4):
        j = (i + 1) % 4
        out.append(ck.Poly([a[i], a[j], b[j], b[i]], top))

    a, b = sq(h_in, z1), sq(h_in, z0)

    for i in range(4):
        j = (i + 1) % 4
        out.append(ck.Poly([a[i], a[j], b[j], b[i]], inner or side))

    if under and ck.LOD < 2:
        a, b = sq(h_in, z0), sq(levels[0][0], z0)

        for i in range(4):
            j = (i + 1) % 4
            out.append(ck.Poly([a[i], a[j], b[j], b[i]], side))

    return out


def courses(width, z_top, rows, tones, seed, grout=0.035, gcol="grout", y=0.0, stone=1.0):
    out = ck.Part()
    z = z_top

    for r, h in enumerate(rows):
        z0 = z - h

        if ck.LOD >= 2:
            out.append(flat(0, width, z0, z, y, tones[r % len(tones)]))
            z = z0
            continue

        x = 0.0
        i = 0

        while x < width - 1e-3:
            w = stone * (0.75 + 0.6 * ck.hash01(seed, r, i))

            if width - (x + w) < stone * 0.55:
                w = width - x

            col = tones[int(ck.hash01(seed, r, i, 5.0) * len(tones)) % len(tones)]
            g = grout if ck.LOD == 0 and x + w < width - 1e-3 else 0.0
            gh = grout if ck.LOD == 0 else 0.0
            out.append(flat(x, x + w - g, z0 + gh, z, y, col))

            if g:
                out.append(flat(x + w - g, x + w, z0 + gh, z, y, gcol))

            x += w
            i += 1

        if ck.LOD == 0:
            out.append(flat(0, width, z0, z0 + grout, y, gcol))

        z = z0

    return out


def flags(x0, y0, x1, y1, z, tones, seed, rows=4, per=3, grout=0.05, gcol="grout"):
    out = ck.Part()

    def quad(a, b, c, d, col):
        out.append(ck.Poly([(a, b, z), (c, b, z), (c, d, z), (a, d, z)], col, False, False, True))

    if ck.LOD >= 1:
        quad(x0, y0, x1, y1, tones[0])

        return out

    dy = (y1 - y0) / rows

    for r in range(rows):
        ya, yb = y0 + r * dy, y0 + (r + 1) * dy
        cuts = [x0]

        for i in range(1, per):
            cuts.append(x0 + (x1 - x0) * (i + (ck.hash01(seed, r, i) - 0.5) * 0.7) / per)

        cuts.append(x1)

        for i in range(per):
            a, b = cuts[i], cuts[i + 1]
            col = tones[int(ck.hash01(seed, r, i, 9.0) * len(tones)) % len(tones)]
            g = grout if i < per - 1 else 0.0
            quad(a, ya, b - g, yb - grout, col)

            if g:
                quad(b - g, ya, b, yb - grout, gcol)

        quad(x0, yb - grout, x1, yb, gcol)

    return out
