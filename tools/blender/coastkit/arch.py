import math

from mathutils import Matrix, Vector

import ck

DEPTH = 0.18


def win(x, z, w, h, **style):
    d = {"x": x, "z": z, "w": w, "h": h, "kind": "win"}
    d.update(style)

    return d


def door(x, w=1.0, h=2.35, **style):
    d = {"x": x, "z": 0.0, "w": w, "h": h, "kind": "door"}
    d.update(style)

    return d


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


def fill(o, col):
    out = ck.Part()
    x0, x1 = o["x"] - o["w"] / 2, o["x"] + o["w"] / 2
    z0, z1 = o["z"], o["z"] + o["h"]
    trim = o.get("trim", "trim")
    glass = o.get("glass", "glass")
    reveal = o.get("reveal", ck.shade(col, 0.72))
    kind = o["kind"]
    depth = o.get("depth", DEPTH)

    if ck.LOD >= 2:
        c = o.get("leaf", "navy") if kind == "door" else "void" if kind == "void" else glass

        if o["w"] > 0.5:
            e = 0.12
            out.append(ck.Poly([(x0 - e, -0.03, z0 - e if kind == "win" else z0), (x1 + e, -0.03, z0 - e if kind == "win" else z0), (x1 + e, -0.03, z1 + e), (x0 - e, -0.03, z1 + e)], trim, False, False, False))

        out.append(ck.Poly([(x0, -0.055, z0), (x1, -0.055, z0), (x1, -0.055, z1), (x0, -0.055, z1)], c, False, False, False))

        return out

    back = depth
    out.append(ck.Poly([(x0, 0, z0), (x0, back, z0), (x0, back, z1), (x0, 0, z1)], reveal))
    out.append(ck.Poly([(x1, 0, z0), (x1, 0, z1), (x1, back, z1), (x1, back, z0)], reveal))
    out.append(ck.Poly([(x0, 0, z1), (x0, back, z1), (x1, back, z1), (x1, 0, z1)], reveal))
    out.append(ck.Poly([(x0, 0, z0), (x1, 0, z0), (x1, back, z0), (x0, back, z0)], trim))

    if kind == "void":
        out.append(ck.Poly([(x0, back, z0), (x1, back, z0), (x1, back, z1), (x0, back, z1)], "void"))

        return out

    if kind == "door":
        leaf = o.get("leaf", "navy")
        fan = o.get("fan", 0.35) if o["h"] > 2.2 else 0.0
        zl = z1 - fan
        out.append(ck.Poly([(x0, back, z0), (x1, back, z0), (x1, back, zl), (x0, back, zl)], leaf))

        if fan:
            out.append(ck.Poly([(x0, back, zl), (x1, back, zl), (x1, back, z1), (x0, back, z1)], "glass_lt"))
            out += ck.box(x0, back - 0.07, zl - 0.05, x1, back, zl + 0.03, trim, d=0)

        w = x1 - x0
        leaves = 2 if w > 1.45 else 1

        for i in range(leaves):
            lx0 = x0 + w * i / leaves
            lx1 = x0 + w * (i + 1) / leaves
            m = (lx1 - lx0) * 0.18

            for pz0, pz1, pc in ((z0 + 0.18, z0 + (zl - z0) * 0.4, ck.shade(leaf, 0.82)), (z0 + (zl - z0) * 0.5, zl - 0.2, "glass" if o.get("glazed") else ck.shade(leaf, 0.82))):
                out += ck.box(lx0 + m, back - 0.03, pz0, lx1 - m, back, pz1, pc, c=0.012, d=0, skip="b")

            kx = lx1 - 0.14 if i == 0 else lx0 + 0.14
            out += ck.box(kx - 0.03, back - 0.08, z0 + 1.0, kx + 0.03, back - 0.02, z0 + 1.1, "gold", d=0, skip="b")

        if leaves == 2:
            out += ck.box((x0 + x1) / 2 - 0.025, back - 0.045, z0, (x0 + x1) / 2 + 0.025, back, zl, ck.shade(leaf, 0.65), d=0, skip="b")
    else:
        lit = "glass_lt" if glass == "glass" else ck.shade(glass, 1.12)
        style_bars = o.get("bars", "v")

        if style_bars == "v" and o.get("n", 2) > 1:
            n = o.get("n", 2)

            for i in range(n):
                u0, u1 = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
                out.append(ck.Poly([(u0, back, z0), (u1, back, z0), (u1, back, z1), (u0, back, z1)], lit if i % 2 else ck.mix(glass, lit, 0.35)))
        else:
            zm = z0 + o["h"] * (0.52 if style_bars == "h" else 0.62)
            out.append(ck.Poly([(x0, back, z0), (x1, back, z0), (x1, back, zm), (x0, back, zm)], glass))
            out.append(ck.Poly([(x0, back, zm), (x1, back, zm), (x1, back, z1), (x0, back, z1)], lit))

    fw = o.get("fw", 0.07) if o.get("frame", True) else 0.0
    fy0, fy1 = back - 0.06, back

    if fw:
        out += ck.box(x0, fy0, z0, x0 + fw, fy1, z1, trim, d=0, skip="bl")
        out += ck.box(x1 - fw, fy0, z0, x1, fy1, z1, trim, d=0, skip="br")
        out += ck.box(x0 + fw, fy0, z1 - fw, x1 - fw, fy1, z1, trim, d=0, skip="bt")

        if kind == "win":
            out += ck.box(x0 + fw, fy0, z0, x1 - fw, fy1, z0 + fw, trim, d=0, skip="bd")

    if kind == "win":
        bars = o.get("bars", "v")

        if bars == "v":
            n = o.get("n", 2)

            for i in range(1, n):
                bx = x0 + (x1 - x0) * i / n
                out += ck.box(bx - 0.03, fy0 - 0.005, z0 + fw, bx + 0.03, fy1, z1 - fw, trim, d=0, skip="btd")
        elif bars == "h":
            zb = z0 + o["h"] * 0.52
            out += ck.box(x0 + fw, fy0 - 0.005, zb - 0.035, x1 - fw, fy1, zb + 0.035, trim, d=0, skip="blr")

    if o.get("sill", kind == "win"):
        out += ck.box(x0 - 0.09, -0.11, z0 - 0.11, x1 + 0.09, 0.04, z0, o.get("sill_col", trim), d=1, skip="b")

    lintel = o.get("lintel", "flat")

    if lintel == "flat":
        out += ck.box(x0 - 0.08, -0.07, z1, x1 + 0.08, 0.03, z1 + 0.14, o.get("lintel_col", trim), d=1, skip="b")

        if o.get("key", False):
            out += ck.box(o["x"] - 0.09, -0.11, z1 - 0.03, o["x"] + 0.09, 0.0, z1 + 0.19, o.get("lintel_col", trim), d=0, taper=(1.25, 1.0), skip="b")
    elif lintel == "arch":
        n = 8 if ck.LOD == 0 else 4
        r = o["w"] / 2 + 0.1
        rise = min(0.42, o["w"] * 0.32)
        pts = [(o["x"] + math.cos(math.pi * i / n) * r, z1 + math.sin(math.pi * i / n) * rise) for i in range(n + 1)]
        out += ck.extrude(pts, -0.08, 0.03, o.get("lintel_col", trim), caps="f", force=True)
        inner = [(o["x"] + math.cos(math.pi * i / n) * (r - 0.16), z1 + 0.02 + math.sin(math.pi * i / n) * max(rise - 0.15, 0.05)) for i in range(n + 1)]
        out += ck.extrude(inner, -0.095, -0.08, o.get("tymp", "glass"), caps="f", force=True)
    elif lintel == "hood":
        out += ck.box(x0 - 0.16, -0.2, z1 + 0.08, x1 + 0.16, 0.0, z1 + 0.2, o.get("lintel_col", trim), c=0.025, d=1, skip="b")

        for bx in (x0 - 0.07, x1 + 0.07):
            out += ck.box(bx - 0.05, -0.13, z1 - 0.14, bx + 0.05, 0.0, z1 + 0.08, o.get("lintel_col", trim), d=0, skip="bt")

    sh = o.get("shutters")

    if sh:
        sw = o["w"] * 0.4

        for s, edge in ((-1, x0), (1, x1)):
            a = edge + s * 0.1
            b = edge + s * (0.1 + sw)
            out += ck.box(min(a, b), -0.07, z0, max(a, b), 0.0, z1, sh, d=1, skip="b")
            n = 4

            for i in range(n):
                zz = z0 + 0.12 + i * (o["h"] - 0.24) / n
                out += ck.box(min(a, b) + 0.05, -0.095, zz, max(a, b) - 0.05, -0.06, zz + (o["h"] - 0.24) / n * 0.55, ck.shade(sh, 0.82), d=0, skip="b")

    if o.get("box"):
        out += ck.box(x0 - 0.02, -0.24, z0 - 0.34, x1 + 0.02, -0.02, z0 - 0.12, "wood_dk", d=1, skip="b")

        n = max(3, int(o["w"] / 0.32))

        for i in range(n):
            bx = x0 + 0.14 + i * (o["w"] - 0.28) / max(n - 1, 1)
            out += ck.blob((bx, -0.13, z0 - 0.1), (0.15, 0.11, 0.1), ("leaf_lt", "leaf", "leaf_dk"), sub=0, seed=i + int(o["x"] * 7), d=1)

            if i % 2 == 0:
                out += ck.blob((bx + 0.03, -0.18, z0 - 0.04), (0.07, 0.07, 0.06), "bloom" if i % 4 == 0 else "gold", sub=0, seed=i, d=0)

    return out


def facade(p0, p1, z0, z1, col, openings=()):
    a = Vector((p0[0], p0[1], 0))
    b = Vector((p1[0], p1[1], 0))
    t = (b - a)
    width = t.length
    t.normalize()
    inward = Vector((-t.y, t.x, 0))
    ops = []

    for o in openings:
        o = dict(o)

        if o["x"] < 0:
            o["x"] += width

        ops.append(o)

    part = wall_face(width, z0, z1, ops, col)

    for o in ops:
        part += fill(o, col)

    m = Matrix(((t.x, inward.x, 0, a.x), (t.y, inward.y, 0, a.y), (0, 0, 1, 0), (0, 0, 0, 1)))

    return part.xform(m)


def onto(p0, p1, part):
    a = Vector((p0[0], p0[1], 0))
    t = Vector((p1[0], p1[1], 0)) - a
    t.normalize()
    inward = Vector((-t.y, t.x, 0))
    m = Matrix(((t.x, inward.x, 0, a.x), (t.y, inward.y, 0, a.y), (0, 0, 1, 0), (0, 0, 0, 1)))

    return part.xform(m)


def shell(poly, z0, z1, col, openings=None):
    out = ck.Part()
    n = len(poly)

    for i in range(n):
        ops = openings.get(i, ()) if openings else ()
        out += facade(poly[i], poly[(i + 1) % n], z0, z1, col, ops)

    return out


def offset(poly, d):
    n = len(poly)
    out = []

    for i in range(n):
        p = Vector((poly[(i - 1) % n][0], poly[(i - 1) % n][1]))
        c = Vector((poly[i][0], poly[i][1]))
        q = Vector((poly[(i + 1) % n][0], poly[(i + 1) % n][1]))
        t0 = (c - p).normalized()
        t1 = (q - c).normalized()
        n0 = Vector((t0.y, -t0.x))
        n1 = Vector((t1.y, -t1.x))
        m = n0 + n1
        k = d / max(1 + n0.dot(n1), 0.2)
        out.append((c.x + m.x * k, c.y + m.y * k))

    return out


def band(poly, z0, z1, d, col, c=0.025, top=None, cap=True, detail=None):
    out = ck.Part()

    if detail is not None and ck.LOD > detail:
        return out

    ring = offset(poly, d)
    ch = c if ck.LOD == 0 else 0.0
    low = offset(poly, d - ch)
    n = len(poly)
    levels = [(low, z0), (ring, z0 + ch), (ring, z1 - ch), (low, z1)] if ch else [(ring, z0), (ring, z1)]

    for (r0, a), (r1, b) in zip(levels, levels[1:]):
        for i in range(n):
            j = (i + 1) % n
            out.append(ck.Poly([(r0[i][0], r0[i][1], a), (r0[j][0], r0[j][1], a), (r1[j][0], r1[j][1], b), (r1[i][0], r1[i][1], b)], col))

    top_ring = levels[-1][0]

    if cap:
        out.append(ck.Poly([(p[0], p[1], z1) for p in top_ring], top or col))

    bottom_ring = levels[0][0]
    inner = offset(poly, -0.02)

    for i in range(n):
        j = (i + 1) % n
        out.append(ck.Poly([(inner[i][0], inner[i][1], z0), (inner[j][0], inner[j][1], z0), (bottom_ring[j][0], bottom_ring[j][1], z0), (bottom_ring[i][0], bottom_ring[i][1], z0)], col))

    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def slab(poly, z, col):
    out = ck.Part()
    out.append(ck.Poly([(p[0], p[1], z) for p in poly], col))

    return out


def parapet(poly, z, h, col, cap, thick=0.22):
    out = ck.Part()
    inner = offset(poly, -thick)
    n = len(poly)

    for i in range(n):
        j = (i + 1) % n
        out.append(ck.Poly([(poly[i][0], poly[i][1], z), (poly[j][0], poly[j][1], z), (poly[j][0], poly[j][1], z + h), (poly[i][0], poly[i][1], z + h)], col))
        out.append(ck.Poly([(inner[j][0], inner[j][1], z), (inner[i][0], inner[i][1], z), (inner[i][0], inner[i][1], z + h), (inner[j][0], inner[j][1], z + h)], ck.shade(col, 0.8)))

    ring_o = offset(poly, 0.09)
    ring_i = offset(poly, -thick - 0.07)

    for i in range(n):
        j = (i + 1) % n
        zc = z + h
        zt = zc + 0.14
        out.append(ck.Poly([(ring_o[i][0], ring_o[i][1], zc), (ring_o[j][0], ring_o[j][1], zc), (ring_o[j][0], ring_o[j][1], zt), (ring_o[i][0], ring_o[i][1], zt)], cap))
        out.append(ck.Poly([(ring_i[j][0], ring_i[j][1], zc), (ring_i[i][0], ring_i[i][1], zc), (ring_i[i][0], ring_i[i][1], zt), (ring_i[j][0], ring_i[j][1], zt)], cap))
        out.append(ck.Poly([(ring_o[i][0], ring_o[i][1], zt), (ring_o[j][0], ring_o[j][1], zt), (ring_i[j][0], ring_i[j][1], zt), (ring_i[i][0], ring_i[i][1], zt)], cap))

    return out


def hip(poly, top, z0, z1, col, rows=5, lip=0.045, cap=None, under=True):
    out = ck.Part()
    n = len(poly)
    rows = rows if ck.LOD == 0 else max(1, rows // 3) if ck.LOD == 1 else 1
    lip = lip if ck.LOD == 0 else 0.0
    prev = None

    def ring(t):
        return [(poly[i][0] + (top[i][0] - poly[i][0]) * t, poly[i][1] + (top[i][1] - poly[i][1]) * t) for i in range(n)]

    for r in range(rows):
        a = ring(r / rows)
        b = ring((r + 1) / rows)
        za = z0 + (z1 - z0) * r / rows
        zb = z0 + (z1 - z0) * (r + 1) / rows
        colour = col if r % 2 == 0 or ck.LOD else ck.shade(col, 0.9)

        for i in range(n):
            j = (i + 1) % n
            zl = za + (lip if r else 0.0)
            pts = [(a[i][0], a[i][1], zl), (a[j][0], a[j][1], zl), (b[j][0], b[j][1], zb), (b[i][0], b[i][1], zb)]
            quad_pts = [pts[0], pts[1], pts[2]]

            if (Vector(pts[2]) - Vector(pts[3])).length > 1e-4:
                quad_pts.append(pts[3])

            out.append(ck.Poly(quad_pts, colour))

            if r and lip:
                out.append(ck.Poly([(a[i][0], a[i][1], za), (a[j][0], a[j][1], za), (a[j][0], a[j][1], zl), (a[i][0], a[i][1], zl)], ck.shade(col, 0.72)))

    t = ring(1.0)
    area = sum(t[i][0] * t[(i + 1) % n][1] - t[(i + 1) % n][0] * t[i][1] for i in range(n))

    if abs(area) > 0.02:
        out.append(ck.Poly([(p[0], p[1], z1) for p in t], cap or col))

    if under:
        out.append(ck.Poly([(p[0], p[1], z0) for p in reversed(poly)], ck.shade(col, 0.6)))

    return out


def ridge_caps(poly, top, z0, z1, col, r=0.07):
    out = ck.Part()

    for i in range(len(poly)):
        out += ck.tube([(poly[i][0], poly[i][1], z0 + 0.03), (top[i][0], top[i][1], z1 + 0.03)], r, 5, col, caps=(True, True), smooth=False, d=0)

    return out


def gable(x0, x1, y0, y1, z, rise, col, wall, axis="y", over=0.25, rows=6, trim="trim", ridge=None, thick=0.14):
    out = ck.Part()

    if axis == "x":
        part = gable(-y1, -y0, x0, x1, z, rise, col, wall, "y", over, rows, trim, ridge, thick)

        return part.rot(90)

    cx = (x0 + x1) / 2
    half = (x1 - x0) / 2 + over
    drop = over * rise / ((x1 - x0) / 2)
    zr = z + rise
    ze = z - drop
    rows = rows if ck.LOD == 0 else 2 if ck.LOD == 1 else 1
    step = 0.05 if ck.LOD == 0 else 0.0
    ya, yb = y0 - over * 0.7, y1 + over * 0.7

    for side in (-1, 1):
        for r in range(rows):
            u0 = r / rows
            u1 = (r + 1) / rows
            xa = cx + side * half * u0
            xb = cx + side * half * u1
            za = zr + (ze - zr) * u0 + thick
            zb = zr + (ze - zr) * u1 + thick + (step if r < rows - 1 else step)
            colour = col if r % 2 == 0 or ck.LOD else ck.shade(col, 0.9)
            face = [(xa, ya, za), (xb, ya, zb), (xb, yb, zb), (xa, yb, za)]

            if side < 0:
                face.reverse()

            out.append(ck.Poly(face, colour))

            if step and r < rows - 1:
                nxt = zr + (ze - zr) * u1 + thick
                lipf = [(xb, ya, nxt), (xb, yb, nxt), (xb, yb, zb), (xb, ya, zb)]

                if side < 0:
                    lipf.reverse()

                out.append(ck.Poly(lipf, ck.shade(col, 0.7)))

        xe = cx + side * half
        for yy, face_y in ((ya, -1), (yb, 1)):
            f = ck.Poly([(cx, yy, zr + thick + step), (xe, yy, ze + thick + step), (xe, yy, ze - 0.02), (cx, yy, zr - 0.02)], trim)

            if f.normal().y * face_y < 0:
                f.pts.reverse()

            out.append(f)

        eave = ck.Poly([(xe, ya, ze - 0.02), (xe, yb, ze - 0.02), (xe, yb, ze + thick + step), (xe, ya, ze + thick + step)], trim)

        if eave.normal().x * side < 0:
            eave.pts.reverse()

        out.append(eave)
        under = ck.Poly([(cx, ya, zr - 0.02), (xe, ya, ze - 0.02), (xe, yb, ze - 0.02), (cx, yb, zr - 0.02)], ck.shade(col, 0.55))

        if under.normal().z > 0:
            under.pts.reverse()

        out.append(under)

    out += ck.box(cx - 0.1, ya - 0.03, zr + thick - 0.04, cx + 0.1, yb + 0.03, zr + thick + 0.11, ridge or ck.shade(col, 0.78), c=0.035, d=1)

    if wall:
        for yy, face_y in ((y0, -1), (y1, 1)):
            f = ck.Poly([(x0, yy, z), (x1, yy, z), (cx, yy, zr)], wall)

            if f.normal().y * face_y < 0:
                f.pts.reverse()

            out.append(f)

    return out


def chimney(x, y, z0, z1, col="brick", cap="stone", w=0.55, dp=0.42, pots=2):
    out = ck.box(x - w / 2, y - dp / 2, z0, x + w / 2, y + dp / 2, z1 - 0.34, col, c=0.025, skip="d")
    out += ck.box(x - w / 2 - 0.06, y - dp / 2 - 0.06, z1 - 0.34, x + w / 2 + 0.06, y + dp / 2 + 0.06, z1 - 0.22, cap, c=0.025)

    for i in range(pots):
        px = x - w / 2 + w * (i + 0.5) / pots
        out += ck.cyl((px, y, z1 - 0.22), 0.085, 0.22, "tile", sides=6, rt=0.065, caps=(False, "void"), d=1)

    return out


def downpipe(x, y, z0, z1, col="iron_lt"):
    out = ck.tube([(x, y, z0), (x, y, z1)], 0.05, 5, col, d=0)
    out += ck.box(x - 0.1, y - 0.08, z1 - 0.05, x + 0.1, y + 0.08, z1 + 0.12, col, c=0.02, d=0)

    return out


def panel(x0, x1, z0, z1, yf, yb, col, c=0.05):
    out = ck.Part()

    if ck.LOD > 0:
        c = 0.0

    face = [(x0 + c, yf, z0 + c), (x1 - c, yf, z0 + c), (x1 - c, yf, z1 - c), (x0 + c, yf, z1 - c)]
    ring = [(x0, yf + c, z0), (x1, yf + c, z0), (x1, yf + c, z1), (x0, yf + c, z1)]
    back = [(x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1)]
    out.append(ck.Poly(face, col))

    for i in range(4):
        j = (i + 1) % 4

        if c:
            out.append(ck.Poly([ring[i], ring[j], face[j], face[i]], col))

        out.append(ck.Poly([back[i], back[j], ring[j], ring[i]], col))

    return out


def striped_awning(x0, x1, y_wall, z, depth, drop, a, b, n=None, valance=0.18, cheeks=True):
    out = ck.Part()
    n = n or max(3, int(round((x1 - x0) / 0.38)))

    if ck.LOD == 2:
        n = 3

    w = (x1 - x0) / n
    yf = y_wall - depth
    zf = z - drop
    ym = y_wall - depth * 0.55
    zm = z - drop * 0.35

    for i in range(n):
        u0 = x0 + i * w
        u1 = u0 + w
        col = a if i % 2 == 0 else b
        out += ck.sheet([[(u0, yf, zf), (u1, yf, zf)], [(u0, ym, zm), (u1, ym, zm)], [(u0, y_wall, z), (u1, y_wall, z)]] if ck.LOD == 0 else [[(u0, yf, zf), (u1, yf, zf)], [(u0, y_wall, z), (u1, y_wall, z)]], col, thick=0.025)

        if valance:
            if ck.LOD == 0:
                pts = [(u0, zf), (u0, zf - valance * 0.6), (u0 + w * 0.25, zf - valance * 0.92), ((u0 + u1) / 2, zf - valance), (u1 - w * 0.25, zf - valance * 0.92), (u1, zf - valance * 0.6), (u1, zf)]
            else:
                pts = [(u0, zf), (u0, zf - valance * 0.8), (u1, zf - valance * 0.8), (u1, zf)]

            out += ck.extrude(pts, yf - 0.015, yf + 0.012, col, force=True, side=lambda i, p, q: None)

    if cheeks and ck.LOD < 2:
        for x, s in ((x0, -1), (x1, 1)):
            f = ck.Poly([(x, y_wall, z), (x, yf, zf), (x, yf, zf - valance * 0.5), (x, y_wall, z - drop - valance * 0.2)], ck.shade(a, 0.9))
            g = ck.Poly(list(reversed(f.pts)), ck.shade(a, 0.9))
            g.pts = [p - Vector((s * 0.012, 0, 0)) for p in g.pts]
            out.append(f if f.normal().x * s > 0 else ck.Poly(list(reversed(f.pts)), f.col))
            out.append(g if g.normal().x * s < 0 else ck.Poly(list(reversed(g.pts)), g.col))

    return out


def letters(x0, x1, y, z, h, col, seed=1, n=None):
    out = ck.Part()

    if ck.LOD > 0:
        out.append(ck.Poly([(x0, y, z + h * 0.2), (x1, y, z + h * 0.2), (x1, y, z + h * 0.8), (x0, y, z + h * 0.8)], col, False, False, False))

        return out

    n = n or (2 if x1 - x0 < 2.0 else 3)
    weights = [0.7 + ck.hash01(i, seed, 2.3) for i in range(n)]
    gap = h * 0.5
    dot = h * 0.22
    span = x1 - x0 - 4 * dot - 2 * gap - gap * (n - 1)
    cur = x0 + 2 * dot + gap

    for w in weights:
        wide = span * w / sum(weights)
        zl, zh, c = z + h * 0.2, z + h * 0.8, h * 0.2
        pts = [(cur, zl + c), (cur + c, zl), (cur + wide - c, zl), (cur + wide, zl + c), (cur + wide, zh - c), (cur + wide - c, zh), (cur + c, zh), (cur, zh - c)]
        out += ck.extrude(pts, y - 0.035, y, col, force=True, caps="f", ao=False, cast=False)
        cur += wide + gap

    for cx in (x0 + dot, x1 - dot):
        pts = [(cx + math.cos(i * math.pi / 4) * dot, z + h * 0.5 + math.sin(i * math.pi / 4) * dot) for i in range(8)]
        out += ck.extrude(pts, y - 0.035, y, col, force=True, caps="f", ao=False, cast=False)

    return out


def disc(center, r, col, sides=12, depth=0.05, axis="Y", d=None):
    c = Vector(center)

    if axis == "Y":
        return ck.tube([c + Vector((0, depth / 2, 0)), c - Vector((0, depth / 2, 0))], r, sides, col, caps=(False, True), smooth=False, d=d)

    return ck.tube([c - Vector((depth / 2, 0, 0)), c + Vector((depth / 2, 0, 0))], r, sides, col, caps=(False, True), smooth=False, d=d)
