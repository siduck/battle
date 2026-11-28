import math
import random

from mathutils import Matrix, Vector

import ak
from ak import Part, Poly, box, tube, extrude, hash01

V = Vector


def lod():
    return ak.LOD


def face(part, side, dist, along=0.0, z=0.0):
    part.move(along, -dist, z)

    return part.rot({"f": 0, "r": 90, "b": 180, "l": -90}[side])


def flip(part):
    for f in part:
        f.pts.reverse()

    return part


def poly(pts, col, d=None, out=None, cast=True):
    part = Part()

    if d is not None and ak.LOD > d:
        return part

    p = Poly(pts, col, False, True, cast)

    if out is not None and p.normal().dot(V(out)) < 0:
        p.pts.reverse()

    part.append(p)

    return part


def beam(a, b, w, h, col, c=0.0, d=None, up=(0, 0, 1), ext=0.0, cast=True):
    a = V(a)
    b = V(b)
    t = b - a
    ln = t.length
    t.normalize()
    u = V(up)

    if abs(u.dot(t)) > 0.97:
        u = V((0, 1, 0))

    s = u.cross(t).normalized()
    u = t.cross(s).normalized()
    part = box(-ext, -w / 2, -h / 2, ln + ext, w / 2, h / 2, col, c=c, d=d, cast=cast)
    m = Matrix(((t.x, s.x, u.x, a.x), (t.y, s.y, u.y, a.y), (t.z, s.z, u.z, a.z), (0, 0, 0, 1)))

    return part.xform(m)


def log(a, b, r, col="wood", end="end", sides=6, d=None, ends=(True, True), phase=0.0):
    n = sides

    return tube([a, b], [r, r], n, col, caps=(end if ends[0] else False, end if ends[1] else False), smooth=False, d=d, phase=phase)


def ring(rx, ry, z, n, seed, jit=0.0, cx=0.0, cy=0.0, phase=0.0, zj=0.0):
    r = random.Random(seed)
    out = []

    for i in range(n):
        a = 2 * math.pi * i / n + phase
        k = 1 + r.uniform(-jit, jit)
        out.append(V((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k, z + r.uniform(-zj, zj))))

    return out


def loft(rings, cols, top=None, apex=None, cast=True, smooth=False):
    part = Part()

    for j in range(len(rings) - 1):
        a = rings[j]
        b = rings[j + 1]
        n = len(a)

        for i in range(n):
            k = (i + 1) % n
            c = cols[j](i) if callable(cols[j]) else cols[j]

            for tri in ((a[i], a[k], b[k]), (a[i], b[k], b[i])):
                if (tri[1] - tri[0]).cross(tri[2] - tri[0]).length > 1e-6:
                    part.append(Poly(tri, c, smooth, True, cast))

    last = rings[-1]

    if apex is not None:
        c = top or cols[-1]

        for i in range(len(last)):
            part.append(Poly([last[i], last[(i + 1) % len(last)], V(apex)], c(i) if callable(c) else c, smooth, True, cast))
    elif top is not None:
        part.append(Poly(last, top, False, True, cast))

    return part


def mound(at, rx, ry, h, seed=0, col="snow", d=None, n=10, jit=0.07):
    if d is not None and ak.LOD > d:
        return Part()

    x, y, z = at
    n = (n, 7, 5)[ak.LOD]
    steps = (((1.0, 0.0), (0.82, 0.55), (0.47, 0.9)), ((1.0, 0.0), (0.7, 0.72)), ((1.0, 0.0), (0.6, 0.8)))[ak.LOD]
    rings = [ring(rx * k, ry * k, z + h * q, n, seed + j, jit if j else jit * 0.5, x, y, j * 0.3) for j, (k, q) in enumerate(steps)]

    return loft(rings, [col] * len(rings), apex=(x + rx * 0.05, y, z + h), smooth=True)


def rock(at, rx, ry, h, seed=0, tones=("rock", "rock_d", "rock_l"), cap=True, n=7, lean=(0.0, 0.0), d=None, top=0.6, capcol="snow"):
    if d is not None and ak.LOD > d:
        return Part()

    x, y, z = at
    n = (n, max(5, n - 2), 5)[ak.LOD]
    steps = ((0.92, 0.0, 0.0), (1.06, 0.34, 0.06), (0.86, 0.72, 0.08), (top, 1.0, 0.07))

    if ak.LOD == 2:
        steps = ((1.0, 0.0, 0.0), (0.95, 0.55, 0.04), (top, 1.0, 0.05))

    rings = [ring(rx * k, ry * k, z + h * q, n, seed * 7 + j, 0.17, x + lean[0] * q, y + lean[1] * q, j * 0.37, zj * h if j else 0.0) for j, (k, q, zj) in enumerate(steps)]

    def tone(j):
        return lambda i: tones[int(hash01(seed, i, j) * 2.99)]

    out = loft(rings, [tone(j) for j in range(len(rings) - 1)])
    crown = rings[-1]
    mid = sum(crown, V((0, 0, 0))) / len(crown)

    if not cap:
        return out + loft([crown], [], top=tones[2], apex=mid + V((0, 0, h * 0.05)))

    thick = min(0.32, max(0.06, h * 0.11))
    lip = [mid + (p - mid) * 1.1 + V((0, 0, -thick * (0.35 + hash01(seed, i, 9) * 0.9))) for i, p in enumerate(crown)]
    edge = [mid + (p - mid) * 1.08 + V((0, 0, thick * 0.35)) for p in crown]
    inner = [mid + (p - mid) * 0.66 + V((0, 0, thick)) for p in crown]
    cols = ["snow_s", "snow", capcol]

    if ak.LOD == 2:
        return out + loft([lip, inner], [capcol], apex=mid + V((0, 0, thick * 1.2)), top=capcol)

    return out + loft([lip, edge, inner], cols, apex=mid + V((rx * 0.08, 0, thick * 1.25)), top=capcol)


def pad(x0, y0, x1, y1, z, h, col="snow", seed=0, d=None, bevel=None, jit=0.06):
    part = Part()

    if d is not None and ak.LOD > d:
        return part

    r = random.Random(seed + 11)
    b = bevel if bevel is not None else min(h * 0.9, min(x1 - x0, y1 - y0) * 0.3)
    nx = max(1, int((x1 - x0) / 0.9)) if ak.LOD == 0 else 1
    ny = max(1, int((y1 - y0) / 0.9)) if ak.LOD == 0 else 1
    base = []

    for i in range(nx):
        base.append((x0 + (x1 - x0) * i / nx, y0))

    for i in range(ny):
        base.append((x1, y0 + (y1 - y0) * i / ny))

    for i in range(nx):
        base.append((x1 - (x1 - x0) * i / nx, y1))

    for i in range(ny):
        base.append((x0, y1 - (y1 - y0) * i / ny))

    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2

    def inset(p, k, amount):
        px, py = p
        qx = min(max(px, x0 + amount), x1 - amount)
        qy = min(max(py, y0 + amount), y1 - amount)

        return V((qx, qy, k))

    j = jit if ak.LOD == 0 else 0.0
    low = [inset(p, z, 0.0) for p in base]
    mid = [inset((p[0] + r.uniform(-j, j), p[1] + r.uniform(-j, j)), z + h * (0.55 + r.uniform(-0.15, 0.1)), b * 0.12) for p in base]
    high = [inset(p, z + h * (0.96 + r.uniform(-0.08, 0.12)), b) for p in base]
    rings = [low, mid, high] if ak.LOD == 0 else [low, high]

    wide = min(x1 - x0, y1 - y0)

    if ak.LOD == 0 and wide > 1.6:
        rings.append([V((cx + (p.x - cx) * 0.55, cy + (p.y - cy) * 0.55, z + h * (1.09 + r.uniform(-0.015, 0.02)))) for p in high])

    return loft(rings, ["snow_s" if col == "snow" else col] + [col] * 3, apex=(cx, cy, z + h * 1.13))


def drift(x0, x1, y, depth, h, seed=0, d=None):
    part = Part()

    if d is not None and ak.LOD > d:
        return part

    n = max(2, int((x1 - x0) / 0.8)) if ak.LOD == 0 else 2
    r = random.Random(seed + 5)
    rows = []

    for i in range(n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u
        k = 0.12 if i in (0, n) else 1.0 + r.uniform(-0.25, 0.15)
        rows.append([V((x, y, 0.0)), V((x, y, h * k)), V((x, y - depth * 0.45 * k - 0.03, h * k * 0.72)), V((x, y - depth * k - 0.06, 0.0))])

    for i in range(n):
        a = rows[i]
        b = rows[i + 1]

        for j, c in ((1, "snow"), (2, "snow_s")):
            part += poly([a[j], b[j], b[j + 1], a[j + 1]], c, out=(0, -0.7, 0.7))

        part += poly([a[0], b[0], b[1], a[1]], "snow_s", out=(0, 1, 0))

    part += poly(rows[0], "snow_s", out=(-1, 0, 0))
    part += poly(rows[n], "snow_s", out=(1, 0, 0))

    return part


def slope_snow(e0, e1, r1, r0, th, seed=0, start=0.06, ridge=True, wave=0.07, cell=1.15, col="snow", d=None):
    part = Part()

    if d is not None and ak.LOD > d:
        return part

    e0, e1, r1, r0 = V(e0), V(e1), V(r1), V(r0)
    along = (e1 - e0).length
    up = (r0 - e0).length
    n = (e1 - e0).cross(r0 - e0).normalized()

    if n.z < 0:
        n = -n

    nu = (max(2, int(round(along / cell))), max(2, int(round(along / cell / 2.2))), 1)[ak.LOD]
    nv = (max(2, min(4, int(round(up / cell)))), 2, 1)[ak.LOD]
    r = random.Random(seed + 31)
    starts = [max(0.0, start + r.uniform(-wave, wave)) for _ in range(nu + 1)]
    ridge_k = [r.uniform(-0.18, 0.22) for _ in range(nu + 1)]
    eu = min(0.45, th * 1.1) / along
    ev = min(0.45, th * 1.4) / up

    def at(u, v):
        return e0.lerp(e1, u).lerp(r0.lerp(r1, u), v)

    top = []
    base = []

    for i in range(nu + 1):
        col_t = []
        col_b = []

        for j in range(nv + 1):
            u = i / nu
            q = j / nv
            v = starts[i] + (1 - starts[i]) * q
            ut = min(max(u, eu), 1 - eu)
            vt = max(v, starts[i] + ev * (0.55 if j == 0 else 0))
            edge = j == 0 or i in (0, nu)
            k = 0.72 if edge else 1.0 + r.uniform(-0.2, 0.25)

            if ridge and j == nv:
                p = at(ut, 1.0) + V((0, 0, th * (1.0 + ridge_k[i]) / max(n.z, 0.35)))
            else:
                p = at(ut, vt) + n * (th * k)

            col_t.append(p)
            col_b.append(at(u, v) + n * (th * 0.08))

        top.append(col_t)
        base.append(col_b)

    for i in range(nu):
        for j in range(nv):
            quad_ = [top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]]
            part += poly([quad_[0], quad_[1], quad_[2]], col, out=n)
            part += poly([quad_[0], quad_[2], quad_[3]], col, out=n)

        down = e0 - r0
        part += poly([base[i][0], base[i + 1][0], top[i + 1][0], top[i][0]], "snow_s", out=down.normalized() + n * 0.3)

    side = (e0 - e1).normalized()

    for j in range(nv):
        part += poly([base[0][j], base[0][j + 1], top[0][j + 1], top[0][j]], "snow_s", out=side + n * 0.3)
        part += poly([base[nu][j], base[nu][j + 1], top[nu][j + 1], top[nu][j]], "snow_s", out=-side + n * 0.3)

    return part


def courses(e0, e1, r1, r0, col, alt, n=6, lift=0.05, seed=0, split=1.6):
    part = Part()
    e0, e1, r1, r0 = V(e0), V(e1), V(r1), V(r0)
    nr = (e1 - e0).cross(r0 - e0).normalized()

    if nr.z < 0:
        nr = -nr

    if ak.LOD > 0:
        return poly([e0 + nr * 0.02, e1 + nr * 0.02, r1 + nr * 0.02, r0 + nr * 0.02], col, out=nr)

    along = (e1 - e0).length
    m = max(1, int(along / split))

    for j in range(n):
        v0 = j / n
        v1 = (j + 1) / n
        off = (j % 2) * 0.5
        cuts = [0.0] + [min(1.0, max(0.0, (i + off) / m)) for i in range(1, m)] + [1.0]

        for i in range(len(cuts) - 1):
            a, b = cuts[i], cuts[i + 1]

            if b - a < 0.01:
                continue

            p0 = e0.lerp(e1, a).lerp(r0.lerp(r1, a), v0) + nr * lift
            p1 = e0.lerp(e1, b).lerp(r0.lerp(r1, b), v0) + nr * lift
            p2 = e0.lerp(e1, b).lerp(r0.lerp(r1, b), v1) + nr * 0.008
            p3 = e0.lerp(e1, a).lerp(r0.lerp(r1, a), v1) + nr * 0.008
            c = alt if hash01(seed, i, j) > 0.68 else col
            part += poly([p0, p1, p2, p3], c, out=nr)
            part += poly([p0 - nr * lift, p1 - nr * lift, p1, p0], ak.shade(c, 0.72), out=e0 - r0)

    return part


def gable_roof(hx, y0, y1, eave, ridge, deck="slate", wood="wood", under="wood_d", th=0.2, snow=0.34, start=0.1, seed=0, bare=True, rafters=True, cx=0.0, tile=None, cell=1.15):
    part = Part()
    hl, hr = hx if isinstance(hx, tuple) else (hx, hx)
    el, er = eave if isinstance(eave, tuple) else (eave, eave)
    outline = [(-hl, el), (0, ridge), (hr, er), (hr, er - th), (0, ridge - th), (-hl, el - th)]

    def side(i, a, b):
        return deck if (a[1] + b[1]) / 2 > (min(el, er) + ridge) / 2 - th * 0.5 else under

    part += extrude([(x + cx, z) for x, z in outline], y0, y1, under, side=side, force=True)

    for s, hx, eave in ((-1, hl, el), (1, hr, er)):
        e0 = (cx + s * hx, y0, eave)
        e1 = (cx + s * hx, y1, eave)
        r1 = (cx, y1, ridge)
        r0 = (cx, y0, ridge)

        if bare:
            part += courses(e0, e1, r1, r0, deck, tile or ak.shade(deck, 1.13), n=5, seed=seed + s)

        if snow:
            part += slope_snow((cx + s * hx, y0 + 0.07, eave + 0.03), (cx + s * hx, y1 - 0.07, eave + 0.03), (cx, y1 - 0.07, ridge + 0.03), (cx, y0 + 0.07, ridge + 0.03), snow, seed=seed, start=start, cell=cell)

        for y, o in ((y0, -1), (y1, 1)):
            part += beam((cx + s * (hx + 0.04), y + o * 0.03, eave - th * 0.55), (cx, y + o * 0.03, ridge - th * 0.45), 0.14, th * 1.25, wood, c=0.025, ext=0.06)

        part += beam((cx + s * (hx - 0.02), y0, eave - th * 0.7), (cx + s * (hx - 0.02), y1, eave - th * 0.7), 0.1, th * 0.8, wood, d=1)

        if rafters:
            n = max(2, int((y1 - y0) / 1.25))
            slope = (ridge - eave) / hx

            for i in range(n + 1):
                y = y0 + 0.35 + (y1 - y0 - 0.7) * i / n
                part += beam((cx + s * (hx - 0.06), y, eave - th - 0.05), (cx + s * (hx - 0.75), y, eave - th - 0.05 + slope * 0.69), 0.14, 0.14, under, d=0)

    return part


def boards(x0, x1, z0, z1, tones, h=0.3, holes=(), out=0.045, seed=0, clip=None):
    part = Part()

    if ak.LOD > 0:
        h = (z1 - z0) / max(1, int(round((z1 - z0) / (h * 3)))) if ak.LOD == 1 else z1 - z0

    n = max(1, int(round((z1 - z0) / h)))
    step = (z1 - z0) / n

    for j in range(n):
        a = z0 + j * step
        b = a + step
        spans = [(x0, x1)]

        if clip is not None:
            lo, hi = clip(b)
            spans = [(max(x0, lo), min(x1, hi))]

        if ak.LOD == 0:
            for hx0, hx1, hz0, hz1 in holes:
                if b <= hz0 + 0.02 or a >= hz1 - 0.02:
                    continue

                cut = []

                for s0, s1 in spans:
                    if hx1 <= s0 or hx0 >= s1:
                        cut.append((s0, s1))
                        continue

                    if hx0 > s0:
                        cut.append((s0, hx0))

                    if hx1 < s1:
                        cut.append((hx1, s1))

                spans = cut

        for i, (s0, s1) in enumerate(spans):
            if s1 - s0 < 0.04:
                continue

            c = tones[int(hash01(seed, j, i) * len(tones) * 0.999)]
            y = -out
            part += poly([(s0, y, a), (s1, y, a), (s1, -0.008, b), (s0, -0.008, b)], c, out=(0, -1, 0.1))

            if ak.LOD == 0:
                part += poly([(s0, 0.0, a), (s1, 0.0, a), (s1, y, a), (s0, y, a)], ak.shade(c, 0.7), out=(0, 0, -1))

    return part


def planks(x0, x1, z0, z1, tones, w=0.34, holes=(), out=0.045, seed=0, top=None):
    part = Part()
    height = top or (lambda x: z1)

    if ak.LOD > 0:
        mid = (x0 + x1) / 2

        return poly([(x0, -out * 0.5, z0), (x1, -out * 0.5, z0), (x1, -out * 0.5, height(x1)), (mid, -out * 0.5, height(mid)), (x0, -out * 0.5, height(x0))], tones[0], out=(0, -1, 0))

    n = max(1, int(round((x1 - x0) / w)))
    step = (x1 - x0) / n

    for i in range(n):
        a = x0 + i * step
        b = a + step - 0.025
        spans = [(z0, None)]

        for hx0, hx1, hz0, hz1 in holes:
            if b <= hx0 + 0.02 or a >= hx1 - 0.02:
                continue

            cut = []

            for s0, s1 in spans:
                end = s1 if s1 is not None else max(height(a), height(b))

                if hz1 <= s0 or hz0 >= end:
                    cut.append((s0, s1))
                    continue

                if hz0 > s0:
                    cut.append((s0, hz0))

                if hz1 < end:
                    cut.append((hz1, s1))

            spans = cut

        c = tones[int(hash01(seed, i, 2) * len(tones) * 0.999)]

        for s0, s1 in spans:
            za = s1 if s1 is not None else height(a)
            zb = s1 if s1 is not None else height(b)
            y = -out

            if min(za, zb) - s0 < 0.03:
                continue

            part += poly([(a, y, s0), (b, y, s0), (b, y, zb), (a, y, za)], c, out=(0, -1, 0))
            part += poly([(b, y, s0), (b, 0, s0), (b, 0, zb), (b, y, zb)], ak.shade(c, 0.72), out=(1, 0, 0))

    return part


def window(w, h, frame="wood_l", shutters=None, sill=True, panes=2, rows=1, glass="glass", snow=True, f=0.1):
    part = Part()
    part += poly([(-w / 2, -0.07, 0), (w / 2, -0.07, 0), (w / 2, -0.07, h), (-w / 2, -0.07, h)], glass, out=(0, -1, 0))
    part += poly([(-w / 2, -0.074, h * 0.45), (-w * 0.08, -0.074, h), (-w * 0.34, -0.074, h), (-w / 2, -0.074, h * 0.74)], "glass_l", d=0, out=(0, -1, 0))

    for s in (-1, 1):
        part += box(s * w / 2 - f / 2, -0.15, -f / 2, s * w / 2 + f / 2, -0.0, h + f / 2, frame, skip="b", d=1)

    part += box(-w / 2 - f * 1.2, -0.18, h - f / 2, w / 2 + f * 1.2, 0.0, h + f, frame, c=0.025, skip="b", d=1)
    part += box(-w / 2 - f * 1.4, -0.22, -f, w / 2 + f * 1.4, 0.0, f * 0.2, frame, skip="b", d=1)

    for i in range(1, panes):
        x = -w / 2 + w * i / panes
        part += box(x - 0.035, -0.11, 0, x + 0.035, -0.06, h, frame, skip="bdt", d=0)

    for i in range(1, rows):
        z = h * i / rows
        part += box(-w / 2, -0.105, z - 0.03, w / 2, -0.06, z + 0.03, frame, skip="blr", d=0)

    if sill and snow:
        part += pad(-w / 2 - f, -0.27, w / 2 + f, -0.05, f * 0.15, 0.09, d=0, seed=int(w * 100))

    if shutters:
        sw = w * 0.48

        for s in (-1, 1):
            xa = s * (w / 2 + f * 0.7)
            xb = s * (w / 2 + f * 0.7 + sw)
            a, b = min(xa, xb), max(xa, xb)

            if ak.LOD == 0:
                for k in range(2):
                    p = a + (b - a) * k / 2
                    part += box(p + 0.008, -0.1, -0.02, p + (b - a) / 2 - 0.008, 0.0, h + 0.02, shutters if k == 0 else ak.shade(shutters, 0.9), skip="bd")

                for z in (h * 0.14, h * 0.76):
                    part += box(a + 0.03, -0.135, z, b - 0.03, -0.09, z + h * 0.1, ak.shade(shutters, 0.72), skip="b")
            else:
                part += poly([(a, -0.07, 0), (b, -0.07, 0), (b, -0.07, h), (a, -0.07, h)], shutters, out=(0, -1, 0))

    return part


def door(w, h, col="wood", frame="wood_d", handle=True, n=4, f=0.14, ledges=True):
    part = Part()

    if ak.LOD == 0:
        for k in range(n):
            a = -w / 2 + w * k / n
            part += box(a + 0.008, -0.09, 0, a + w / n - 0.008, 0.0, h, col if k % 2 == 0 else ak.shade(col, 0.88), c=0.015, skip="bd")
    else:
        part += poly([(-w / 2, -0.07, 0), (w / 2, -0.07, 0), (w / 2, -0.07, h), (-w / 2, -0.07, h)], col, out=(0, -1, 0))

    for s in (-1, 1):
        part += box(s * w / 2 + (0 if s > 0 else -f), -0.17, 0, s * w / 2 + (f if s > 0 else 0), 0.0, h, frame, c=0.025, skip="bd", d=1)

    part += box(-w / 2 - f * 1.3, -0.2, h, w / 2 + f * 1.3, 0.0, h + f * 1.2, frame, c=0.03, skip="b", d=1)

    if ledges:
        for z in (h * 0.16, h * 0.74):
            part += box(-w / 2 + 0.06, -0.125, z, w / 2 - 0.06, -0.08, z + 0.13, ak.shade(col, 0.7), skip="b", d=0)

    if handle:
        part += box(w * 0.24, -0.17, h * 0.44, w * 0.31, -0.09, h * 0.54, "black", skip="b", d=0)

    return part


def stones(x0, x1, z0, z1, tones=("stone", "stone_d", "stone_l"), rows=2, w=0.75, out=0.09, holes=(), seed=0):
    part = Part()

    if ak.LOD > 0:
        cuts = [(x0, x1)]

        for hx0, hx1, hz0, hz1 in holes:
            if hz0 < z1 and hz1 > z0:
                cuts = [s for a, b in cuts for s in ((a, min(b, hx0)), (max(a, hx1), b)) if s[1] - s[0] > 0.05]

        for a, b in cuts:
            part += poly([(a, -out * 0.6, z0), (b, -out * 0.6, z0), (b, -out * 0.6, z1), (a, -out * 0.6, z1)], tones[0], out=(0, -1, 0))

        return part

    step = (z1 - z0) / rows
    r = random.Random(seed + 3)

    for j in range(rows):
        a = z0 + step * j
        x = x0

        while x < x1 - 0.05:
            ww = w * r.uniform(0.7, 1.3)
            b = min(x1, x + ww)

            if x1 - b < w * 0.35:
                b = x1

            blocked = any(b > h0 and x < h1 and a < h3 and a + step > h2 for h0, h1, h2, h3 in holes)

            if blocked:
                for h0, h1, h2, h3 in holes:
                    if b > h0 and x < h0:
                        b = h0
                        blocked = False
                    elif x < h1 and b > h1:
                        x = h1
                        blocked = False

            if not blocked and b - x > 0.06:
                o = out * r.uniform(0.7, 1.25)
                g = 0.02
                k = 0.07
                base = [V((x + g, 0, a + g)), V((b - g, 0, a + g)), V((b - g, 0, a + step - g)), V((x + g, 0, a + step - g))]
                front = [V((x + g + k, -o, a + g + k)), V((b - g - k, -o, a + g + k)), V((b - g - k, -o, a + step - g - k)), V((x + g + k, -o, a + step - g - k))]
                c = tones[int(r.random() * len(tones) * 0.999)]
                part += poly(front, c, out=(0, -1, 0))

                for i, n_ in enumerate(((0, -1, -1), (1, -1, 0), (0, -1, 1), (-1, -1, 0))):
                    i2 = (i + 1) % 4
                    part += poly([base[i], base[i2], front[i2], front[i]], c, out=n_)

            x = max(b, x + 0.05)

    return part


def plinth(x0, y0, x1, y1, col="stone_d", z1=0.04):
    return box(x0, y0, -1.0, x1, y1, z1, col, skip="d")


def core(x0, y0, x1, y1, z0, z1, col):
    return box(x0, y0, z0, x1, y1, z1, col, skip="d")


def icicles(a, b, n, h, seed=0):
    part = Part()

    if ak.LOD > 0:
        return part

    a = V(a)
    b = V(b)

    for i in range(n):
        p = a.lerp(b, (i + hash01(seed, i) * 0.8) / n)
        ln = h * (0.45 + hash01(seed, i, 4))
        part += tube([p, p - V((0, 0, ln))], [0.05, 0.004], 4, "ice", caps=(False, False), smooth=False)

    return part


def cable(a, b, r=0.025, col="steel_d", d=None, sides=3):
    return tube([a, b], [r, r], sides, col, caps=(False, False), smooth=False, d=d)


def wheel(center, R, col="blue", axis="Z", segs=14, spokes=6, w=0.14):
    part = Part()
    c = V(center)
    n = (segs, 10, 7)[ak.LOD]

    def pt(a, r, h):
        x, y = math.cos(a) * r, math.sin(a) * r

        if axis == "Z":
            return c + V((x, y, h))

        if axis == "X":
            return c + V((h, x, y))

        return c + V((x, h, y))

    ax = {"Z": V((0, 0, 1)), "X": V((1, 0, 0)), "Y": V((0, 1, 0))}[axis]

    for i in range(n):
        a = 2 * math.pi * i / n
        b = 2 * math.pi * (i + 1) / n
        mid = (pt((a + b) / 2, 1.0, 0) - c).normalized()

        for r, o, tone in ((R, mid, ak.shade(col, 0.8)), (R * 0.8, -mid, ak.shade(col, 0.65))):
            part += poly([pt(a, r, -w / 2), pt(b, r, -w / 2), pt(b, r, w / 2), pt(a, r, w / 2)], tone, out=o)

        for h, s in ((-w / 2, -1), (w / 2, 1)):
            part += poly([pt(a, R * 0.8, h), pt(b, R * 0.8, h), pt(b, R, h), pt(a, R, h)], col, out=ax * s)

    for i in range(spokes if ak.LOD < 2 else 3):
        a = 2 * math.pi * i / (spokes if ak.LOD < 2 else 3) + 0.2
        part += beam(pt(a, R * 0.1, 0), pt(a, R * 0.82, 0), R * 0.09, w * 0.55, ak.shade(col, 0.9), up=ax)

    part += tube([c - ax * w * 0.7, c + ax * w * 0.7], [R * 0.17, R * 0.17], 8, "steel_d", caps=(True, True), smooth=False)

    return part


def rail(pts, h, col="wood", post=0.1, step=0.9, d=None, snow=False, base=0.0, mid=True):
    part = Part()

    if d is not None and ak.LOD > d:
        return part

    pts = [V(p) for p in pts]

    for a, b in zip(pts, pts[1:]):
        ln = (b - a).length
        n = max(1, int(round(ln / step)))

        if ak.LOD > 0:
            n = 1

        for i in range(n + 1):
            p = a.lerp(b, i / n)
            part += box(p.x - post / 2, p.y - post / 2, p.z + base, p.x + post / 2, p.y + post / 2, p.z + h, col, skip="d")

        part += beam(a + V((0, 0, h)), b + V((0, 0, h)), post * 1.15, post * 0.9, col, ext=post * 0.5)

        if mid:
            part += beam(a + V((0, 0, h * 0.52)), b + V((0, 0, h * 0.52)), post * 0.6, post * 0.6, col, d=0)

        if snow and ak.LOD == 0:
            part += beam(a + V((0, 0, h + post * 0.75)), b + V((0, 0, h + post * 0.75)), post * 0.9, post * 0.6, "snow", c=0.02, ext=post * 0.3)

    return part
