import math

from construction_core import Mesh, V, c, mul, newell


def corrugate(m, x0, x1, y0, y1, z, depth, pitch, col, side):
    n = max(1, int(round((x1 - x0) / pitch)))
    step = (x1 - x0) / n

    for i in range(n):
        a = x0 + step * i
        pts = [(a, z), (a + step * 0.3, z), (a + step * 0.5, z - depth * side), (a + step * 0.8, z - depth * side), (a + step, z)]
        tones = [1.0, 0.84, 0.92, 1.08]

        for k in range(4):
            (u0, w0), (u1, w1) = pts[k], pts[k + 1]
            q = [(u0, y0, w0), (u1, y0, w1), (u1, y1, w1), (u0, y1, w0)]
            m.face(q, mul(col, tones[k]), m_vec((u0 + u1) / 2, (y0 + y1) / 2, z - side * 2))


def m_vec(x, y, z):
    return V((x, y, z))


def pallet(m, x, y, z, w, d, col="wd_l"):
    for i in range(3):
        zz = z - d / 2 + 0.07 + i * (d - 0.14) / 2
        m.box((x - w / 2, y, zz - 0.06), (x + w / 2, y + 0.03, zz + 0.06), c("wd_d"), skip="-y")

        for xx in (x - w / 2 + 0.07, x, x + w / 2 - 0.07):
            m.box((xx - 0.07, y + 0.03, zz - 0.06), (xx + 0.07, y + 0.11, zz + 0.06), c("wd_d"), skip="-y,+y")

    n = max(3, int(w / 0.2))
    step = w / n

    for i in range(n):
        xa = x - w / 2 + step * i
        m.box((xa + 0.012, y + 0.11, z - d / 2), (xa + step - 0.012, y + 0.15, z + d / 2), m.shade(c(col), 0.1), skip="-y")


def container(body, dark, light):
    m = Mesh(11)
    col, dk, lt = c(body), c(dark), c(light)
    x0, x1, z0, z1, H = -3.03, 3.03, -1.22, 1.22, 2.59

    for side, z in ((1, z1 - 0.02), (-1, z0 + 0.02)):
        corrugate(m, x0 + 0.16, x1 - 0.16, 0.16, H - 0.14, z, 0.042, 0.44, col, side)

    m.push(yaw=-math.pi / 2)
    corrugate(m, z0 + 0.16, z1 - 0.16, 0.16, H - 0.14, -x0 - 0.02, 0.04, 0.42, col, 1)
    m.pop()

    for cx in (x0, x1 - 0.18):
        for cz in (z0, z1 - 0.18):
            m.box((cx, 0.12, cz), (cx + 0.18, H - 0.12, cz + 0.18), dk, bevel=0.025, skip="-y,+y")

            for cy in (0.0, H - 0.13):
                m.box((cx - 0.005, cy, cz), (cx + 0.19, cy + 0.13, cz + 0.18), c("stl_dd"))
                hz = z0 - 0.006 if cz < 0 else z1 + 0.006
                m.disc((cx + 0.09, cy + 0.065, hz), (0, 0, 1 if cz > 0 else -1), 0.045, c("void"))

    for z in (z0 + 0.01, z1 - 0.13):
        m.box((x0 + 0.17, 0.0, z), (x1 - 0.17, 0.17, z + 0.12), dk, bevel=0.02, skip="-y,-x,+x")
        m.box((x0 + 0.17, H - 0.15, z), (x1 - 0.17, H - 0.01, z + 0.12), dk, bevel=0.02, skip="-x,+x")

    for x in (x0 + 0.01, x1 - 0.13):
        m.box((x, 0.0, z0 + 0.17), (x + 0.12, 0.17, z1 - 0.17), dk, bevel=0.02, skip="-y,-z,+z")
        m.box((x, H - 0.15, z0 + 0.17), (x + 0.12, H - 0.01, z1 - 0.17), dk, bevel=0.02, skip="-z,+z")

    for xx in (-1.4, 1.4):
        for z in (z0, z1):
            m.box((xx - 0.18, 0.035, z - 0.012), (xx + 0.18, 0.115, z + 0.012), c("void"))

    m.box((x0 + 0.1, H - 0.08, z0 + 0.1), (x1 - 0.1, H - 0.05, z1 - 0.1), mul(col, 0.9), skip="-y")

    for i in range(7):
        xa = x0 + 0.45 + i * 0.77
        m.box((xa, H - 0.05, z0 + 0.16), (xa + 0.42, H - 0.02, z1 - 0.16), mul(col, 1.07), skip="-y")

    m.box((x1 - 0.08, 0.16, z0 + 0.16), (x1 - 0.05, H - 0.14, z1 - 0.16), dk, skip="-x")

    for a, b in ((z0 + 0.18, -0.015), (0.015, z1 - 0.18)):
        m.box((x1 - 0.05, 0.19, a), (x1 - 0.02, H - 0.17, b), col, bevel=0.012, skip="-x")

        for yy in (0.5, 1.72):
            m.box((x1 - 0.02, yy, a + 0.08), (x1 - 0.005, yy + 0.09, b - 0.08), lt, skip="-x")

        for t in (0.28, 0.72):
            zz = a + (b - a) * t
            m.tube((x1 + 0.012, 0.1, zz), (x1 + 0.012, H - 0.08, zz), 0.022, c("stl_l"))
            m.box((x1 - 0.01, 1.12, zz - 0.015), (x1 + 0.03, 1.17, zz + 0.2 * (1 if t < 0.5 else -1)), c("stl_dd"))

            for yy in (0.17,):
                m.box((x1 - 0.02, yy, zz - 0.05), (x1 + 0.03, yy + 0.07, zz + 0.05), c("stl_d"), skip="-x")

    for z, s in ((z1 - 0.005, 1), (z0 + 0.005, -1)):
        xs = -1.9 if s > 0 else 0.7
        m.box((xs, 1.5, z - 0.012 * s), (xs + 1.2, 2.02, z + 0.012 * s), c("wht_d"), skip="-z" if s > 0 else "+z")

        for k, (w, yy) in enumerate(((0.9, 1.84), (0.66, 1.7), (0.8, 1.58))):
            m.box((xs + 0.12, yy, z + 0.008 * s), (xs + 0.12 + w, yy + 0.07, z + 0.02 * s), dk, skip="-z" if s > 0 else "+z")

    return m, {"reach": 0.7, "strength": 0.55}


def box_red():
    return container("red", "red_d", "red_l")


def box_blue():
    return container("blu", "blu_d", "blu_l")


def box_green():
    return container("grn", "grn_d", "grn_l")


def pipes():
    m = Mesh(3)
    r = 0.56
    pos = [(-1.13, 0.66), (0.0, 0.66), (1.13, 0.66), (-0.565, 1.63), (0.565, 1.63)]

    for i, (x, y) in enumerate(pos):
        col = c(("con", "con_l", "con", "con_l", "con")[i])
        z = -1.2 + (0.04 if i % 2 else 0.0)
        seg = 10
        prof = [(0.43, 0.04), (0.46, 0.0), (r - 0.02, 0.0), (r, 0.04), (r, 0.24), (r - 0.045, 0.3), (r - 0.045, 2.29), (r - 0.065, 2.33), (0.45, 2.33), (0.42, 2.29)]
        cols = [mul(col, 1.1), col, mul(col, 1.1), col, mul(col, 0.8), col, mul(col, 1.1), col, mul(col, 1.05)]
        m.lathe((x, y, z), prof, cols, seg=seg, axis=(0, 0, 1))
        m.lathe((x, y, z), [(0.42, 2.29), (0.41, 1.2), (0.43, 0.04)], [c("con_dd"), c("con_d")], seg=seg, axis=(0, 0, 1))

        for ring in (1.2,):
            m.lathe((x, y, z + ring), [(r - 0.045, 0.0), (r - 0.025, 0.02), (r - 0.025, 0.08), (r - 0.045, 0.1)], mul(col, 0.78), seg=seg, axis=(0, 0, 1))

    for z in (-0.75, 0.75):
        m.box((-1.78, 0.0, z - 0.09), (1.78, 0.11, z + 0.09), c("wd"), bevel=0.02, skip="-y")

        for s in (-1, 1):
            m.extrude([(s * 1.5, 0.11), (s * 1.82, 0.11), (s * 1.82, 0.34), (s * 1.74, 0.34)], z - 0.08, z + 0.08, c("wd_l"), axis="z")

    return m, {"reach": 1.0, "strength": 0.75}


def drums():
    m = Mesh(4)
    pallet(m, -0.0, 0.0, -0.5, 2.2, 1.0)
    pallet(m, -0.0, 0.0, 0.52, 2.2, 0.96, "wd")
    cols = [("blu", "blu_d"), ("blu_l", "blu"), ("ox", "ox_d"), ("yel", "yel_d")]

    for i, (x, z) in enumerate(((-0.52, -0.5), (0.52, -0.5), (-0.52, 0.5), (0.52, 0.5))):
        col, dk = c(cols[i][0]), c(cols[i][1])
        prof = [(0.295, 0.0), (0.295, 0.27), (0.32, 0.31), (0.295, 0.35), (0.295, 0.55), (0.32, 0.59), (0.295, 0.63), (0.3, 0.87), (0.27, 0.855)]
        m.lathe((x, 0.15, z), prof, [col, dk, dk, col, dk, dk, col, mul(col, 1.1)], seg=10)
        m.cyl((x, 0.99, z), (x, 1.005, z), 0.27, mul(col, 0.92), seg=10, caps="b")
        m.cyl((x + 0.12, 1.0, z + 0.07), (x + 0.12, 1.02, z + 0.07), 0.045, c("stl_dd"), seg=6, caps="b")

    return m, {"reach": 0.7, "strength": 0.65}


def spool():
    m = Mesh(5)

    for s in (-1, 1):
        a = s * 0.7
        b = s * 0.56
        m.cyl((min(a, b), 0.85, 0), (max(a, b), 0.85, 0), 0.85, c("wd_l"), seg=14, chamfer=0.035)
        face = s * 0.7
        m.lathe((face - s * 0.012, 0.85, 0), [(0.62, 0.0), (0.62, 0.022), (0.55, 0.022), (0.55, 0.0)], c("wd_d"), seg=14, axis=(s, 0, 0))
        m.cyl((face - s * 0.01, 0.85, 0), (face + s * 0.004, 0.85, 0), 0.26, c("blu"), seg=10, caps="ab")
        m.cyl((face - s * 0.01, 0.85, 0), (face + s * 0.012, 0.85, 0), 0.08, c("void"), seg=8)

        for k in range(6):
            a = k * math.tau / 6 + 0.26
            p = (face, 0.85 + math.sin(a) * 0.42, math.cos(a) * 0.42)
            m.disc((p[0] + s * 0.014, p[1], p[2]), (s, 0, 0), 0.05, c("stl_d"))

    prof = [(0.54, 0.0)]
    cols = []

    for k in range(5):
        h = k * 0.224
        prof += [(0.61, h + 0.07), (0.61, h + 0.154), (0.54, h + 0.224)]
        cols += [c("dark"), c("rubber"), c("dark")]

    m.lathe((-0.56, 0.85, 0), prof, cols, seg=12, axis=(1, 0, 0))

    for s in (-1, 1):
        m.extrude([(s * 0.42, 0.0), (s * 0.83, 0.0), (s * 0.83, 0.3), (s * 0.42, 0.045)], -0.5, 0.5, c("wd_d"), axis="x")

    return m, {"reach": 0.7, "strength": 0.65}


def blocks():
    m = Mesh(6)

    for row in range(2):
        off = 0.0 if row == 0 else 0.8

        for i in range(3):
            if row == 1 and i == 2:
                continue

            x = -2.4 + off + i * 1.6
            y = row * 0.8
            col = m.shade(c("con" if (i + row) % 2 else "con_d"), 0.04)
            m.box((x + 0.02, y, -0.4), (x + 1.58, y + 0.77, 0.4), col, bevel=0.07, skip="-y")

            for q in (0.44, 1.16):
                m.cyl((x + q, y + 0.76, 0), (x + q, y + 0.87, 0), 0.19, col, seg=8, r2=0.17, caps="b", chamfer=0.025)

            for s in (-1, 1):
                m.box((x + 0.18, y + 0.5, s * 0.395), (x + 1.42, y + 0.55, s * 0.408), mul(col, 0.8))
                m.box((x + 0.72, y + 0.18, s * 0.395), (x + 0.88, y + 0.3, s * 0.41), c("void"))

    return m, {"reach": 0.8, "strength": 0.65}


def timber():
    m = Mesh(9)

    for z in (-0.82, 0.0, 0.82):
        m.box((-1.75, 0.0, z - 0.08), (-1.5, 0.11, z + 0.08), c("wd_d"), skip="-y")
        m.box((1.5, 0.0, z - 0.08), (1.75, 0.11, z + 0.08), c("wd_d"), skip="-y")

    m.box((-1.7, 0.02, -0.9), (-1.55, 0.1, 0.9), c("wd_d"))
    m.box((1.55, 0.02, -0.9), (1.7, 0.1, 0.9), c("wd_d"))
    tones = ("wd", "wd_l", "wd_l", "wd_ll")

    for layer in range(5):
        y = 0.11 + layer * 0.165
        count = 8 if layer < 4 else 5

        for i in range(count):
            z = -1.01 + i * 0.253
            ln = m.rng.uniform(-0.12, 0.12)
            col = m.shade(c(m.rng.choice(tones)), 0.05)
            a = (-2.0 + ln, y, z + 0.008)
            b = (2.0 + ln, y + 0.155, z + 0.238)

            if layer == 4 or i in (0, count - 1):
                m.box(a, b, col, bevel=0.018, skip="-y")
            else:
                m.box(a, b, col, skip="-y,+y,-z,+z")

            for s, x in ((-1, a[0]), (1, b[0])):
                fx = x + s * 0.004
                m.face([(fx, y + 0.03, z + 0.05), (fx, y + 0.125, z + 0.05), (fx, y + 0.125, z + 0.195), (fx, y + 0.03, z + 0.195)], mul(c("wd_ll"), 1.05), m_vec(x - s, y, z))

    for x in (-1.0, 1.0):
        m.box((x - 0.05, 0.11, -1.025), (x + 0.05, 0.9, -1.012), c("blu_d"))
        m.box((x - 0.05, 0.11, 1.012), (x + 0.05, 0.9, 1.025), c("blu_d"))
        m.box((x - 0.05, 0.935, -1.02), (x + 0.05, 0.945, 0.26), c("blu_d"))

    return m, {"reach": 0.7, "strength": 0.6}


def stirrups(m, x, z, half, ys, col, r=0.014):
    for y in ys:
        pts = [(x - half, y, z - half), (x + half, y, z - half), (x + half, y, z + half), (x - half, y, z + half)]

        for i in range(4):
            m.beam(pts[i], pts[(i + 1) % 4], r * 2, r * 2, col, caps=False)


def starter():
    m = Mesh(12)
    m.box((-0.8, 0.0, -0.8), (0.8, 0.45, 0.8), c("con_d"), bevel=0.07, skip="-y")
    m.box((-0.62, 0.45, -0.62), (0.62, 0.5, 0.62), c("con"), bevel=0.02, skip="-y")
    m.box((-0.36, 0.5, -0.36), (0.36, 0.66, 0.36), c("wd_l"), bevel=0.02, skip="-y")
    m.box((-0.3, 0.66, -0.3), (0.3, 1.5, 0.3), c("con"), bevel=0.05, skip="-y")

    for x in (-0.18, 0.18):
        for z in (-0.18, 0.18):
            m.tube((x, 1.5, z), (x, 2.55, z), 0.028, c("rb"))
            m.box((x - 0.04, 2.52, z - 0.04), (x + 0.04, 2.6, z + 0.04), c("ora"), bevel=0.012, skip="-y")

    stirrups(m, 0, 0, 0.2, (1.72, 2.02, 2.32), c("rb_l"))

    for s in (-1, 1):
        for q in (-0.45, 0.45):
            m.tube((q, 0.5, s * 0.5), (q, 0.72, s * 0.5), 0.022, c("rb_d"), caps="b")

    return m, {"reach": 0.8, "strength": 0.6}


def rebarmat():
    m = Mesh(13)

    for i in range(13):
        x = -3.0 + i * 0.5
        m.tube((x, 0.14, -1.6), (x, 0.14, 1.6), 0.028, m.shade(c("rb"), 0.12), caps="ab")

    for i in range(7):
        z = -1.5 + i * 0.5
        m.tube((-3.1, 0.178, z), (3.1, 0.178, z), 0.026, m.shade(c("rb_l"), 0.1), caps="ab")

    for x in (-2.5, 0.0, 2.5):
        for z in (-1.0, 1.0):
            m.box((x - 0.07, 0.0, z - 0.07), (x + 0.07, 0.11, z + 0.07), c("con_d"), bevel=0.02, skip="-y")

    return m, {"reach": 0.4, "strength": 0.4, "grime": 0.0, "low": 0.7}


def bag():
    m = Mesh(14)

    def ring(y, half, cut):
        return [(-half + cut, y, -half), (half - cut, y, -half), (half, y, -half + cut), (half, y, half - cut), (half - cut, y, half), (-half + cut, y, half), (-half, y, half - cut), (-half, y, -half + cut)]

    rings = [ring(0.0, 0.42, 0.09), ring(0.1, 0.47, 0.1), ring(0.4, 0.49, 0.12), ring(0.7, 0.455, 0.1), ring(0.82, 0.44, 0.08)]
    tones = [c("wht_d"), c("wht"), c("wht"), c("wht_d")]
    mid = m_vec(0, 0.4, 0)

    for k in range(4):
        for i in range(8):
            j = (i + 1) % 8
            col = tones[k] if i % 2 == 0 else mul(tones[k], 0.92)
            m.face([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]], col, mid)

    lip = rings[4]
    inner = ring(0.76, 0.39, 0.07)
    heap = ring(0.93, 0.2, 0.08)
    up = m_vec(0, -1, 0)

    for i in range(8):
        j = (i + 1) % 8
        m.face([lip[i], lip[j], inner[j], inner[i]], c("wht_d"), up)
        m.face([inner[i], inner[j], heap[j], heap[i]], m.shade(c("sand"), 0.12), up)

    for i in range(8):
        m.face([heap[i], heap[(i + 1) % 8], (0.03, 0.98, -0.02)], m.shade(c("sand_l"), 0.1), up)

    for sx in (-1, 1):
        for sz in (-1, 1):
            a = (sx * 0.43, 0.7, sz * 0.32)
            b = (sx * 0.4, 1.12, sz * 0.3)
            cc = (sx * 0.3, 1.13, sz * 0.4)
            d = (sx * 0.32, 0.7, sz * 0.43)

            for p, q in ((a, b), (b, cc), (cc, d)):
                m.beam(p, q, 0.06, 0.03, c("blu"), caps=False)

    for s in (-1, 1):
        m.box((-0.22, 0.24, s * 0.487), (0.22, 0.56, s * 0.497), c("ora"))
        m.box((-0.16, 0.42, s * 0.495), (0.16, 0.47, s * 0.503), c("wht"))
        m.box((-0.16, 0.32, s * 0.495), (0.06, 0.36, s * 0.503), c("wht"))

    return m, {"reach": 0.6, "strength": 0.55}


def pallet_load():
    m = Mesh(15)
    pallet(m, 0, 0, 0, 1.2, 1.0)

    for layer in range(4):
        y = 0.15 + layer * 0.225
        turn = layer % 2

        for i in range(3):
            col = m.shade(c(("ox", "ox_l", "ox")[(i + layer) % 3]), 0.07)

            if turn:
                a = -0.56 + i * 0.375
                m.box((a, y, -0.46), (a + 0.36, y + 0.21, 0.46), col, bevel=0.022 if layer == 3 else 0.016, skip="-y")
            else:
                a = -0.47 + i * 0.317
                m.box((-0.55, y, a), (0.55, y + 0.21, a + 0.3), col, bevel=0.016, skip="-y")

    for x in (-0.3, 0.3):
        for s in (-1, 1):
            m.box((x - 0.035, 0.15, s * 0.48), (x + 0.035, 1.07, s * 0.492), c("blu_d"))

        m.box((x - 0.035, 1.068, -0.49), (x + 0.035, 1.088, 0.49), c("blu_d"))

    return m, {"reach": 0.6, "strength": 0.6}


def precast():
    m = Mesh(16)
    y = 0.0

    for layer in range(3):
        m.box((-1.45, y, -0.72), (-1.2, y + 0.08, 0.72), c("wd"), skip="-y")
        m.box((1.2, y, -0.72), (1.45, y + 0.08, 0.72), c("wd"), skip="-y")
        y += 0.08
        shift = (0.0, 0.06, -0.05)[layer]

        for s, z in enumerate((-0.38, 0.38)):
            col = m.shade(c("con_l" if (layer + s) % 2 else "con"), 0.04)
            a = (-2.0 + abs(shift) + shift, y, z - 0.36)
            b = (2.0 - abs(shift) + shift, y + 0.18, z + 0.36)

            if layer == 2 and s == 1:
                b = (b[0] - 0.9, b[1], b[2])

            m.box(a, b, col, bevel=0.035)

            for ex, sgn in ((a[0], -1), (b[0], 1)):
                for k in (-0.21, 0.0, 0.21):
                    m.disc((ex + sgn * 0.004, y + 0.09, z + k), (sgn, 0, 0), 0.06, c("con_dd"))

            if layer == 2:
                for x in (a[0] + 0.5, b[0] - 0.5):
                    m.tube((x - 0.1, y + 0.17, z), (x - 0.04, y + 0.235, z), 0.016, c("rb_d"))
                    m.tube((x - 0.04, y + 0.235, z), (x + 0.04, y + 0.235, z), 0.016, c("rb_d"))
                    m.tube((x + 0.04, y + 0.235, z), (x + 0.1, y + 0.17, z), 0.016, c("rb_d"))

        y += 0.18

    return m, {"reach": 0.6, "strength": 0.65}


def scafstack():
    m = Mesh(17)

    for x in (-1.5, 1.5):
        m.box((x - 0.07, 0.0, -0.75), (x + 0.07, 0.1, 0.75), c("blu_d"), bevel=0.015, skip="-y")

        for z in (-0.71, -0.02, 0.71):
            m.box((x - 0.045, 0.1, z - 0.035), (x + 0.045, 0.56, z + 0.035), c("blu"), bevel=0.012, skip="-y")

    for row in range(4):
        for i in range(5):
            z = -0.62 + i * 0.125 + (0.055 if row % 2 else 0.0)
            ln = m.rng.uniform(-0.14, 0.14)
            y = 0.16 + row * 0.112
            m.cyl((-1.86 + ln, y, z), (1.86 + ln, y, z), 0.058, m.shade(c("stl_l" if (i + row) % 3 else "stl"), 0.06), seg=6, capcol=c("stl_dd"))

    for k in range(3):
        y = 0.1 + k * 0.085

        for j, z in enumerate((0.07, 0.4)):
            if k == 2 and j == 1:
                continue

            ln = m.rng.uniform(-0.1, 0.1)
            m.box((-1.9 + ln, y, z), (1.9 + ln, y + 0.07, z + 0.28), m.shade(c("wd_l" if (k + j) % 2 else "wd"), 0.08), bevel=0.012, skip="-y")

            for x in (-1.9 + ln, 1.9 + ln):
                m.box((x - 0.04, y - 0.004, z - 0.004), (x + 0.04, y + 0.074, z + 0.284), c("stl_d"))

    return m, {"reach": 0.5, "strength": 0.65}


def rebar():
    m = Mesh(18)

    for x in (-0.75, 0.75):
        m.box((x - 0.1, 0.0, -1.0), (x + 0.1, 0.12, 1.0), c("wd_d"), bevel=0.02, skip="-y")

    for x, z, h in ((-0.5, -0.5, 2.0), (0.5, -0.46, 1.72)):
        for ox in (-0.28, 0.28):
            for oz in (-0.28, 0.28):
                m.tube((x + ox, 0.12, z + oz), (x + ox, h, z + oz), 0.025, c("rb"), caps="b")

        for ox, oz in ((0, -0.28), (0, 0.28), (-0.28, 0), (0.28, 0)):
            m.tube((x + ox, 0.12, z + oz), (x + ox, h - 0.04, z + oz), 0.02, c("rb_d"), caps="b")

        n = int((h - 0.3) / 0.3)
        stirrups(m, x, z, 0.3, [0.28 + i * 0.3 for i in range(n + 1)], c("rb_l"), 0.016)

    for row in range(3):
        for i in range(7 - row):
            z = 0.12 + i * 0.1 + row * 0.05
            ln = m.rng.uniform(-0.06, 0.06)
            y = 0.16 + row * 0.085
            m.tube((-0.93 + ln, y, z), (0.93 + ln, y, z), 0.045, m.shade(c("rb" if row % 2 else "rb_d"), 0.12), caps="ab")

    for x in (-0.4, 0.4):
        m.box((x - 0.03, 0.12, 0.05), (x + 0.03, 0.21, 0.79), c("blu"), skip="-y")
        m.box((x - 0.03, 0.21, 0.15), (x + 0.03, 0.38, 0.69), c("blu"), skip="-y")

    return m, {"reach": 0.5, "strength": 0.5, "low": 0.6}


def ibc():
    m = Mesh(19)
    m.box((-0.6, 0.0, -0.5), (0.6, 0.05, 0.5), c("stl_d"), bevel=0.012, skip="-y")

    for x in (-0.52, 0.0, 0.52):
        for z in (-0.42, 0.42):
            m.box((x - 0.07, 0.05, z - 0.07), (x + 0.07, 0.13, z + 0.07), c("stl_dd"), skip="-y,+y")

    m.box((-0.6, 0.13, -0.5), (0.6, 0.18, 0.5), c("stl_d"), bevel=0.012)
    m.box((-0.545, 0.18, -0.445), (0.545, 1.08, 0.445), c("wht"), bevel=0.09, skip="-y")

    for x in (-0.57, -0.19, 0.19, 0.57):
        for z in (-0.47, 0.47):
            m.beam((x, 0.18, z), (x, 1.04, z), 0.024, 0.024, c("stl_l"), caps="b")

    for z in (-0.16, 0.16):
        for x in (-0.57, 0.57):
            m.beam((x, 0.18, z), (x, 1.04, z), 0.024, 0.024, c("stl_l"), caps="b")

    for y in (0.45, 0.74, 1.03):
        pts = [(-0.57, y, -0.47), (0.57, y, -0.47), (0.57, y, 0.47), (-0.57, y, 0.47)]

        for i in range(4):
            m.beam(pts[i], pts[(i + 1) % 4], 0.028, 0.028, c("stl_l"), caps=False)

    m.cyl((0.18, 1.07, 0.1), (0.18, 1.16, 0.1), 0.13, c("blu"), seg=8, chamfer=0.018, caps="b")
    m.box((-0.3, 0.52, 0.462), (0.12, 0.7, 0.476), c("yel"))
    m.box((-0.24, 0.62, 0.475), (0.06, 0.65, 0.482), c("dark"))
    m.cyl((0.3, 0.28, 0.43), (0.3, 0.28, 0.5), 0.07, c("ox"), seg=8, caps="b")

    return m, {"reach": 0.5, "strength": 0.55}


def wrap():
    m = Mesh(20)
    pallet(m, 0, 0, 0, 1.04, 0.84)
    film = (0.6, 0.66, 0.68)
    y = 0.15

    for layer, (h, ix, iz) in enumerate(((0.36, 0.49, 0.39), (0.34, 0.475, 0.375), (0.34, 0.46, 0.365))):
        m.box((-ix, y, -iz), (ix, y + h, iz), mul(film, (1.0, 1.06, 0.97)[layer]), bevel=0.05, skip="-y")
        y += h

        for s in (-1, 1):
            m.box((-ix + 0.07, y - 0.03, s * (iz - 0.004)), (ix - 0.07, y - 0.005, s * (iz + 0.006)), mul(film, 0.74))

    m.box((-0.4, 1.19, -0.3), (0.4, 1.211, 0.3), c("wd_l"), skip="-y")

    for x in (-0.24, 0.24):
        for s in (-1, 1):
            m.box((x - 0.03, 0.15, s * 0.387), (x + 0.03, 1.15, s * 0.4), c("yel"))

        m.box((x - 0.03, 1.205, -0.31), (x + 0.03, 1.215, 0.31), c("yel"))

    for s in (-1, 1):
        m.box((s * 0.47, 0.58, -0.18), (s * 0.5, 0.82, 0.18), c("wht"))

    return m, {"reach": 0.5, "strength": 0.5}


def sandbags():
    m = Mesh(21)
    y = 0.0

    for row in range(5):
        h = 0.24
        n = 6 if row % 2 == 0 else 5
        width = 4.0 / 6
        start = -2.0 if row % 2 == 0 else -2.0 + width / 2
        d = 0.3 - row * 0.018
        items = [(start + i * width, start + (i + 1) * width) for i in range(n)]

        if row % 2:
            items = [(-2.0, start)] + items + [(start + n * width, 2.0)]

        for a, b in items:
            col = m.shade(c(m.rng.choice(("sand", "sand", "sand_d", "sand_l"))), 0.06)
            dz = m.rng.uniform(-0.02, 0.02)
            dd = d + m.rng.uniform(-0.015, 0.004)
            lo = max(-2.0, a + 0.004)
            hi = min(2.0, b - 0.004)
            out = [(-dd * 0.66, y), (dd * 0.66, y), (dd, y + h * 0.5), (dd * 0.6, y + h), (-dd * 0.6, y + h), (-dd, y + h * 0.5)]
            m.push(at=(0, 0, dz))
            m.extrude(out, lo + 0.05, hi - 0.05, col, axis="x", caps=False)
            cy = y + h / 2

            for x0, x1 in ((lo + 0.05, lo), (hi - 0.05, hi)):
                inner = [(x0, v, u) for u, v in out]
                outer = [(x1, cy + (v - cy) * 0.62, u * 0.62) for u, v in out]
                mid = m_vec((x0 * 3 - x1) / 2, cy, 0)

                for i in range(1, 6):
                    j = (i + 1) % 6
                    m.face([inner[i], inner[j], outer[j], outer[i]], mul(col, 0.94), mid)

                m.face(outer, mul(col, 0.87), mid)

            m.pop()

        y += h

    return m, {"reach": 0.35, "strength": 0.7, "low": 0.55}


def spoil():
    m = Mesh(22)
    seg = 14
    levels = [(1.0, 0.0), (0.85, 0.36), (0.68, 0.9), (0.49, 1.37), (0.27, 1.67)]
    rings = []

    for k, (r, y) in enumerate(levels):
        ring = []

        for i in range(seg):
            a = (i + 0.5 * (k % 2)) * math.tau / seg
            j = m.rng.uniform(0.9, 1.03) if k else m.rng.uniform(0.93, 1.0)
            yy = y + (m.rng.uniform(-0.06, 0.06) if k else 0.0)
            ring.append(V((math.cos(a) * 1.68 * r * j, yy, math.sin(a) * 1.59 * r * j)))

        rings.append(ring)

    apex = V((0.04, 1.75, -0.03))
    faces = []

    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]

        for i in range(seg):
            j = (i + 1) % seg
            faces += [(a[i], a[j], b[i]), (a[j], b[j], b[i])] if k % 2 == 0 else [(a[i], a[j], b[j]), (a[i], b[j], b[i])]

    faces += [(rings[-1][i], rings[-1][(i + 1) % seg], apex) for i in range(seg)]
    mid = V((0, 0.1, 0))
    normals = {}

    for f in faces:
        n = newell(list(f))

        if n.dot((f[0] + f[1] + f[2]) / 3 - mid) < 0:
            n = -n

        for p in f:
            normals[p.to_tuple(4)] = normals.get(p.to_tuple(4), V((0, 0, 0))) + n

    tones = {}

    for f in faces:
        for p in f:
            key = p.to_tuple(4)

            if key not in tones:
                base = c("dirt_l") if p.y > 1.2 else c("dirt")
                tones[key] = m.shade(base, 0.05)

        col = tones[f[0].to_tuple(4)]
        m.face(list(f), col, mid, [normals[p.to_tuple(4)].normalized() for p in f])

    for _ in range(14):
        a = m.rng.uniform(0, math.tau)
        r = m.rng.uniform(0.55, 0.92)
        y = (1 - r) * 1.7
        s = m.rng.uniform(0.07, 0.15)
        m.rock((math.cos(a) * r * 1.52, y, math.sin(a) * r * 1.43), s, s * 0.7, s, c(m.rng.choice(("dirt_l", "dirt", "dirt_d"))))

    m.beam((-0.2, 0.9, 0.62), (0.75, 1.3, 0.95), 0.1, 0.05, c("wd_l"))

    return m, {"reach": 0.8, "strength": 0.45, "low": 0.65}


def tplate():
    m = Mesh(23)
    m.box((-1.25, 0.0, -0.75), (1.25, 0.09, 0.75), c("stl_d"), bevel=0.035, skip="-y")
    m.box((-1.12, 0.09, -0.62), (1.12, 0.1, 0.62), c("stl"), skip="-y")

    for i in range(7):
        for j in range(4):
            x = -0.93 + i * 0.31
            z = -0.45 + j * 0.3
            s = 1 if (i + j) % 2 else -1
            m.beam((x - 0.08, 0.112, z - 0.05 * s), (x + 0.08, 0.112, z + 0.05 * s), 0.04, 0.025, c("stl_l"))

    for x in (-1.04, 1.04):
        for z in (-0.55, 0.55):
            m.cyl((x, 0.09, z), (x, 0.108, z), 0.07, c("void"), seg=8, caps="b")

    for x in (-0.75, 0.75):
        m.box((x - 0.14, 0.1, 0.65), (x + 0.14, 0.155, 0.72), c("yel"), bevel=0.012, skip="-y")

    return m, {"reach": 0.3, "strength": 0.3, "grime": 0.0, "low": 0.75}


def flat(m, pts, y, col):
    m.face([(x, y, z) for x, z in pts], col, m_vec(0, -5, 0))


def tracks():
    m = Mesh(24)

    for side in (-0.95, 0.95):
        for k in range(10):
            z0 = -5 + k
            cx = side + math.sin(k * 0.4) * 0.1
            w = 0.34 + m.rng.uniform(-0.03, 0.03)
            flat(m, [(cx - w, z0), (cx + w, z0), (cx + w * 0.92, z0 + 1.0), (cx - w * 0.92, z0 + 1.0)], 0.028, mul(c("dirt"), 0.86))

        for k in range(18):
            z0 = -4.85 + k * 0.55
            cx = side + math.sin((z0 + 5) * 0.4) * 0.1
            flat(m, [(cx - 0.27, z0), (cx, z0 + 0.14), (cx + 0.27, z0), (cx + 0.27, z0 + 0.14), (cx, z0 + 0.28), (cx - 0.27, z0 + 0.14)], 0.034, c("dirt_d"))

    return m, {"bake": False}


def puddle():
    m = Mesh(25)
    n = 14
    pts = []

    for i in range(n):
        a = i / n * math.tau
        r = 1.6 + math.sin(a * 3 + 1) * 0.3 + m.rng.uniform(-0.12, 0.12)
        pts.append((math.cos(a) * r * 1.3, math.sin(a) * r))

    flat(m, pts, 0.026, c("dirt_d"))
    flat(m, [(x * 0.82, z * 0.82) for x, z in pts], 0.032, (0.33, 0.32, 0.31))
    flat(m, [(x * 0.42 + 0.35, z * 0.3 - 0.25) for x, z in pts], 0.038, (0.47, 0.49, 0.5))

    return m, {"bake": False}


def gravel():
    m = Mesh(26)

    for i in range(38):
        x = m.rng.uniform(-1.65, 1.65)
        z = m.rng.uniform(-1.62, 1.45)

        if x * x + z * z > 3.0:
            continue

        r = m.rng.uniform(0.07, 0.14)
        a = m.rng.uniform(0, 1.2)
        col = m.shade(c(m.rng.choice(("grav", "grav_d", "grav_d", "dirt_l"))), 0.07)
        base = [(x + math.cos(a + k * math.tau / 5) * r, 0.0, z + math.sin(a + k * math.tau / 5) * r) for k in range(5)]
        top = [(x + (p[0] - x) * 0.55, r * 0.42, z + (p[2] - z) * 0.55) for p in base]
        mid = m_vec(x, -0.1, z)

        for k in range(5):
            j = (k + 1) % 5
            m.face([base[k], base[j], top[j], top[k]], mul(col, 0.9), mid)

        m.face(top, mul(col, 1.08), mid)

    return m, {"bake": False}


ALL = {
    "box_red": box_red,
    "box_blue": box_blue,
    "box_green": box_green,
    "pipes": pipes,
    "drums": drums,
    "spool": spool,
    "blocks": blocks,
    "timber": timber,
    "starter": starter,
    "rebarmat": rebarmat,
    "bag": bag,
    "pallet": pallet_load,
    "precast": precast,
    "scafstack": scafstack,
    "rebar": rebar,
    "ibc": ibc,
    "wrap": wrap,
    "sandbags": sandbags,
    "spoil": spoil,
    "tplate": tplate,
    "tracks": tracks,
    "puddle": puddle,
    "gravel": gravel,
}
