import math

from construction_core import Mesh, V, c, mul, newell
from construction_materials import m_vec


def feet(m, x, depth, col="rubber"):
    prof = [(-depth, 0.0), (depth, 0.0), (depth, 0.07), (depth - 0.13, 0.15), (-depth + 0.13, 0.15), (-depth, 0.07)]
    m.extrude(prof, x - 0.13, x + 0.13, c(col), axis="x")
    m.box((x - 0.135, 0.055, depth - 0.3), (x + 0.135, 0.075, depth - 0.18), c("ora"), skip="-y")
    m.box((x - 0.135, 0.055, -depth + 0.18), (x + 0.135, 0.075, -depth + 0.3), c("ora"), skip="-y")


def fence():
    m = Mesh(31)

    for x in (-1.72, 1.72):
        feet(m, x, 0.54)

    for x0, x1 in ((-1.98, -0.02), (0.02, 1.98)):
        for x in (x0 + 0.03, x1 - 0.03):
            m.beam((x, 0.12, 0), (x, 2.019, 0), 0.06, 0.06, c("stl_l"), caps="b")

        for y in (0.24, 1.99):
            m.beam((x0 + 0.06, y, 0), (x1 - 0.06, y, 0), 0.055, 0.055, c("stl_l"), caps=False)

        for i in range(1, 10):
            x = x0 + 0.06 + (x1 - x0 - 0.12) * i / 10
            m.beam((x, 0.265, 0), (x, 1.965, 0), 0.018, 0.018, c("stl"), caps=False)

        for y in (0.62, 1.12, 1.62):
            m.beam((x0 + 0.06, y, 0.008), (x1 - 0.06, y, 0.008), 0.022, 0.022, c("stl_l"), caps=False)

    for y in (0.6, 1.5):
        m.box((-0.07, y, -0.045), (0.07, y + 0.09, 0.045), c("stl_d"), bevel=0.012)

    m.box((0.68, 1.2, 0.015), (1.28, 1.56, 0.045), c("wht_d"), bevel=0.01)
    m.box((0.76, 1.42, 0.043), (1.2, 1.49, 0.052), c("blu_d"), skip="-z")
    m.box((0.76, 1.29, 0.043), (1.04, 1.35, 0.052), c("stl_d"), skip="-z")

    return m, {"reach": 0.4, "strength": 0.4, "grime": 0.4, "low": 0.65}


def hoarding():
    m = Mesh(32)

    for x in (-1.96, -0.65, 0.65, 1.96):
        m.beam((x, 0.0, -0.08), (x, 2.28, -0.08), 0.08, 0.09, c("wd_d"), caps="b")

    for x in (-0.65, 0.65):
        m.beam((x, 1.55, -0.1), (x, 0.09, -0.43), 0.07, 0.07, c("wd"))
        m.box((x - 0.12, 0.0, -0.469), (x + 0.12, 0.09, -0.34), c("con_d"), bevel=0.02, skip="-y")
        m.beam((x, 0.12, -0.1), (x, 0.12, -0.4), 0.06, 0.06, c("wd_d"), caps=False)

    m.box((-2.0, 0.0, -0.035), (2.0, 0.24, 0.055), c("dark"), bevel=0.02, skip="-y")

    for x in (-1.3, 0.0, 1.3):
        m.extrude([(0.05, 0.0), (0.469, 0.0), (0.469, 0.1), (0.3, 0.2), (0.05, 0.2)], x - 0.24, x + 0.24, c("con_d"), axis="x")
        m.box((x - 0.245, 0.06, 0.36), (x + 0.245, 0.09, 0.475), c("yel"), skip="-y")

    for i in range(4):
        a = -2.0 + i
        b = a + 1.0
        col = m.shade(c("blu_d" if i % 2 else "blu"), 0.025)
        m.box((a + 0.008, 0.24, -0.03), (b - 0.008, 1.08, 0.025), col, bevel=0.012, skip="-y,+y")
        m.box((a + 0.008, 1.08, -0.03), (b - 0.008, 1.16, 0.03), c("wht_d"), skip="-y,+y")
        m.box((a + 0.008, 1.16, -0.03), (b - 0.008, 2.29, 0.025), m.shade(c("wd_l"), 0.07), bevel=0.012, skip="-y,+y")

        for x in (a + 0.09, b - 0.09):
            for y in (0.36, 0.96, 2.18):
                m.box((x - 0.016, y - 0.016, 0.022), (x + 0.016, y + 0.016, 0.034), c("blu_d" if y < 1.1 else "wd_d"), skip="-z")

    m.box((-2.0, 2.29, -0.13), (2.0, 2.4, 0.065), c("wd"), bevel=0.025, skip="-x,+x")
    m.box((-1.78, 1.28, 0.025), (-0.86, 2.04, 0.04), c("wht"), skip="-z")
    m.box((-1.7, 1.82, 0.038), (-0.94, 1.96, 0.048), c("ora"), skip="-z")
    m.extrude([(-1.62, 1.36), (-1.3, 1.72), (-1.12, 1.52), (-0.96, 1.68), (-0.96, 1.36)], 0.038, 0.047, c("blu_d"), axis="z")

    for k, (w, y) in enumerate(((0.62, 1.72), (0.44, 1.56))):
        m.box((0.2, y, 0.025), (0.2 + w, y + 0.08, 0.036), c("wd_d"), skip="-z")

    return m, {"reach": 0.6, "strength": 0.55}


def barrier():
    m = Mesh(33)
    prof = [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.2), (0.2, 0.36), (0.13, 0.98), (0.09, 1.04), (-0.09, 1.04), (-0.13, 0.98), (-0.2, 0.36), (-0.3, 0.2)]

    for i in range(4):
        a = -2.0 + i
        col = c("ora" if i % 2 == 0 else "wht")
        m.extrude(prof, a + 0.025, a + 0.975, col, axis="x")

        for s in (-1, 1):
            for x0, x1 in ((a + 0.14, a + 0.4), (a + 0.6, a + 0.86)):
                m.face([(x0, 0.06, s * 0.304), (x1, 0.06, s * 0.304), (x1 - 0.03, 0.19, s * 0.304), (x0 + 0.03, 0.19, s * 0.304)], c("void"), m_vec(a + 0.5, 0.1, 0))

            band = c("wht" if i % 2 == 0 else "ora")
            m.face([(a + 0.12, 0.6, s * 0.176), (a + 0.88, 0.6, s * 0.176), (a + 0.88, 0.8, s * 0.154), (a + 0.12, 0.8, s * 0.154)], band, m_vec(a + 0.5, 0.7, 0))

        for x in (a + 0.27, a + 0.73):
            m.box((x - 0.09, 1.04, -0.08), (x + 0.09, 1.16, 0.08), mul(col, 0.9), bevel=0.03, skip="-y")

        m.cyl((a + 0.5, 1.04, 0), (a + 0.5, 1.085, 0), 0.055, c("dark"), seg=6, caps="b")

    for i in (0, 2):
        x = -1.5 + i
        m.box((x - 0.07, 1.16, -0.05), (x + 0.07, 1.235, 0.05), c("yel_l"), bevel=0.025, skip="-y")

    return m, {"reach": 0.5, "strength": 0.5, "grime": 0.6}


def cone():
    m = Mesh(34)
    m.box((-0.175, 0.0, -0.175), (0.175, 0.055, 0.175), c("rubber"), bevel=0.018, skip="-y")
    prof = [(0.135, 0.055), (0.12, 0.09), (0.095, 0.3), (0.07, 0.5), (0.046, 0.7), (0.035, 0.75)]
    m.lathe((0, 0, 0), prof, [c("ora_d"), c("ora"), c("wht"), c("ora"), c("ora_l")], seg=8)
    m.cyl((0, 0.749, 0), (0, 0.75, 0), 0.035, c("ora_d"), seg=8, caps="b")

    return m, {"reach": 0.3, "strength": 0.45, "grime": 0.4}


def wheel(m, x, y, z, r, w, hub="stl"):
    s = 1 if z > 0 else -1
    m.cyl((x, y, z - w / 2), (x, y, z + w / 2), r, c("rubber"), seg=8, chamfer=0.025)
    face = z + s * (w / 2 + 0.006)
    m.cyl((x, y, face - s * 0.02), (x, y, face), r * 0.5, c(hub), seg=8, caps="b" if s > 0 else "a", phase=0.0)


def lights():
    m = Mesh(35)
    m.box((-0.55, 0.17, -0.34), (0.55, 0.66, 0.34), c("yel"), bevel=0.07)
    m.box((-0.46, 0.66, -0.27), (0.46, 0.7, 0.27), c("yel_d"), bevel=0.012, skip="-y")
    m.box((-0.4, 0.26, 0.335), (0.4, 0.56, 0.35), c("yel_d"), skip="-z")

    for k in range(3):
        m.box((-0.32, 0.31 + k * 0.08, 0.348), (0.08, 0.34 + k * 0.08, 0.358), c("dark"), skip="-z")

    m.box((0.18, 0.36, 0.348), (0.32, 0.46, 0.36), c("wht"), skip="-z")

    for x in (-0.34, 0.34):
        for z in (-0.42, 0.42):
            wheel(m, x, 0.17, z, 0.17, 0.15)

    for x in (-0.585, 0.585):
        m.box((x - 0.035, 0.0, -0.06), (x + 0.035, 0.28, 0.06), c("dark"), skip="-y")

    m.cyl((0, 0.7, 0), (0, 0.82, 0), 0.11, c("stl_d"), seg=8, chamfer=0.02)
    m.cyl((0, 0.8, 0), (0, 1.5, 0), 0.055, c("stl_l"), seg=8, caps="")
    m.box((-0.21, 1.47, -0.16), (0.21, 2.4, 0.14), c("dark"), bevel=0.055)

    for k, col in enumerate(((0.76, 0.25, 0.18), (0.86, 0.62, 0.2), (0.3, 0.62, 0.36))):
        y = 2.17 - k * 0.27
        m.cyl((0, y, 0.135), (0, y, 0.155), 0.095, col, seg=10, caps="b")
        m.lathe((0, y, 0.14), [(0.118, 0.0), (0.126, 0.11)], c("rubber"), seg=10, axis=(0, 0.1, 1))

    return m, {"reach": 0.4, "strength": 0.55, "grime": 0.5}


def skip():
    m = Mesh(36)
    outer = [(-1.25, 0.14), (1.25, 0.14), (1.74, 1.2), (-1.74, 1.2)]
    mid = m_vec(0, 0.7, 0)
    col = c("yel")

    for s in (-1, 1):
        m.face([(x, y, s * 0.79) for x, y in outer], col, mid)
        m.face([(x * 0.97, max(0.24, y), s * 0.73) for x, y in outer], c("yel_d"), m_vec(0, 0.7, s * 2))

    for s in (-1, 1):
        m.face([(s * 1.25, 0.14, -0.79), (s * 1.25, 0.14, 0.79), (s * 1.74, 1.2, 0.79), (s * 1.74, 1.2, -0.79)], mul(col, 0.94), mid)
        m.face([(s * 1.21, 0.24, -0.73), (s * 1.21, 0.24, 0.73), (s * 1.69, 1.2, 0.73), (s * 1.69, 1.2, -0.73)], c("yel_d"), m_vec(s * 4, 0.5, 0))

    for s in (-1, 1):
        m.box((-1.8, 1.19, s * 0.85 - 0.12 * (s > 0)), (1.8, 1.316, s * 0.85 + 0.12 * (s < 0)), c("yel_l"), bevel=0.03)
        m.box((s * 1.66 - 0.07, 1.19, -0.73), (s * 1.66 + 0.07, 1.3, 0.73), c("yel_l"), bevel=0.025, skip="-z,+z")

        for t in (-0.8, 0.0, 0.8):
            m.beam((t, 0.16, s * 0.815), (t * 1.34, 1.19, s * 0.815), 0.11, 0.055, c("yel_d"), caps=False, up=(0, 0, 1))

        m.cyl((s * 1.43, 0.78, 0.76 * 1), (s * 1.43, 0.78, 0.85), 0.07, c("dark"), seg=8, caps="b")
        m.cyl((s * 1.43, 0.78, -0.76), (s * 1.43, 0.78, -0.85), 0.07, c("dark"), seg=8, caps="b")

    for x in (-0.9, 0.9):
        m.box((x - 0.12, 0.0, -0.76), (x + 0.12, 0.14, 0.76), c("dark"), bevel=0.025, skip="-y")

    m.box((-1.24, 0.14, -0.76), (1.24, 0.25, 0.76), c("yel_d"), skip="-y")

    for i in range(16):
        x = m.rng.uniform(-1.15, 1.15)
        z = m.rng.uniform(-0.48, 0.48)
        s = m.rng.uniform(0.2, 0.34)
        y = m.rng.uniform(0.68, 0.94)
        m.rock((x, y, z), s, s * 0.7, s * 0.75, c(m.rng.choice(("con", "con_d", "ox_d", "grav_d"))))

    m.face([(-1.4, 0.7, -0.73), (1.4, 0.7, -0.73), (1.4, 0.7, 0.73), (-1.4, 0.7, 0.73)], c("dirt_d"), m_vec(0, -3, 0))
    m.beam((-0.9, 0.9, 0.1), (0.5, 1.26, -0.35), 0.12, 0.05, c("wd_l"))
    m.beam((0.1, 0.92, 0.35), (1.35, 1.25, 0.15), 0.1, 0.045, c("wd"))

    return m, {"reach": 0.6, "strength": 0.6}


def louvres(m, x0, x1, y0, y1, z, s, n, col="dark"):
    m.box((x0, y0, z - 0.006), (x1, y1, z + 0.006), c("stl_dd"), skip="-z" if s > 0 else "+z")

    for i in range(n):
        y = y0 + (y1 - y0) * (i + 0.25) / n
        m.box((x0 + 0.03, y, z + s * 0.004), (x1 - 0.03, y + (y1 - y0) / n * 0.45, z + s * 0.022), c(col), skip="-z" if s > 0 else "+z")


def genset():
    m = Mesh(37)

    for z in (-0.4, 0.4):
        m.box((-1.25, 0.0, z - 0.09), (1.25, 0.13, z + 0.09), c("dark"), bevel=0.025, skip="-y")

    m.box((-1.22, 0.13, -0.5), (1.22, 0.24, 0.5), c("stl_dd"), bevel=0.025)
    m.box((-1.16, 0.24, -0.47), (1.16, 1.5, 0.47), c("wht"), bevel=0.09, skip="-y")
    m.box((-1.19, 0.24, -0.493), (1.19, 0.42, 0.493), c("yel"), bevel=0.025, skip="-y")
    m.box((-1.19, 1.42, -0.495), (1.19, 1.53, 0.495), c("yel"), bevel=0.03)

    for s in (-1, 1):
        z = s * 0.472
        louvres(m, -1.0, -0.38, 0.56, 1.28, z, s, 5)

        for x0, x1 in ((-0.26, 0.38), (0.42, 1.06)):
            m.box((x0, 0.52, z - 0.014), (x1, 1.32, z + 0.014), c("wht_d"), skip="-z" if s > 0 else "+z")
            m.box((x1 - 0.14, 0.86, z + s * 0.01), (x1 - 0.07, 1.02, z + s * 0.035), c("dark"))

    m.box((0.5, 0.96, 0.48), (0.96, 1.26, 0.505), c("stl_dd"), skip="-z")

    for k, col in enumerate(("ora", "grn_l", "wht")):
        m.box((0.57 + k * 0.13, 1.14, 0.503), (0.64 + k * 0.13, 1.2, 0.513), c(col), skip="-z")

    m.box((0.57, 1.01, 0.503), (0.89, 1.09, 0.51), c("glass_l"), skip="-z")
    m.cyl((-0.75, 1.52, 0.0), (-0.75, 1.76, 0.0), 0.11, c("stl_dd"), seg=8, chamfer=0.015, caps="")
    m.cyl((-0.75, 1.74, 0.0), (-0.75, 1.864, 0.0), 0.14, c("dark"), seg=8, chamfer=0.025)
    m.cyl((0.75, 1.52, -0.18), (0.75, 1.59, -0.18), 0.09, c("stl"), seg=8, chamfer=0.015, caps="b")

    for x in (-0.3, 0.3):
        m.box((x - 0.04, 1.52, -0.05), (x + 0.04, 1.66, 0.05), c("stl_dd"), skip="-y")

    m.box((-0.34, 1.65, -0.06), (0.34, 1.71, 0.06), c("stl_dd"), bevel=0.02)

    for x in (-1.168, 1.168):
        m.box((x - 0.008, 0.6, -0.3), (x + 0.008, 1.22, 0.3), c("stl_dd"))

        for k in range(4):
            m.box((x - 0.016, 0.66 + k * 0.14, -0.27), (x + 0.016, 0.72 + k * 0.14, 0.27), c("wht_d"))

    return m, {"reach": 0.5, "strength": 0.55}


def vault():
    m = Mesh(38)

    for x in (-0.72, 0.72):
        m.box((x - 0.14, 0.0, -0.58), (x + 0.14, 0.13, 0.58), c("dark"), bevel=0.025, skip="-y")

    m.box((-0.98, 0.13, -0.55), (0.98, 1.2, 0.55), c("grn"), bevel=0.06)
    m.extrude([(-0.583, 1.19), (0.583, 1.19), (0.57, 1.3), (-0.05, 1.5), (-0.57, 1.44)], -1.006, 1.006, c("grn_l"), axis="x")

    for x in (-0.99, -0.34, 0.34, 0.99):
        m.beam((x, 1.31, 0.575), (x, 1.512 - 0.016, -0.06), 0.07, 0.035, c("grn_d"))

    for s in (-1, 1):
        z = s * 0.552

        for x in (-0.93, 0.87):
            m.box((x, 0.2, z - 0.012), (x + 0.06, 1.14, z + 0.012), c("grn_d"))

        m.box((-0.8, 0.32, z - 0.008), (0.8, 0.4, z + 0.014 * s + 0.002), c("grn_d"))

    for x in (-0.5, 0.5):
        m.box((x - 0.14, 0.94, 0.545), (x + 0.14, 1.16, 0.575), c("stl_dd"), bevel=0.012)
        m.box((x - 0.04, 0.98, 0.57), (x + 0.04, 1.06, 0.583), c("yel"), skip="-z")

    m.box((-0.3, 0.55, 0.55), (0.3, 0.8, 0.562), c("wht"), skip="-z")
    m.box((-0.22, 0.7, 0.56), (0.22, 0.74, 0.568), c("grn_d"), skip="-z")
    m.box((-0.22, 0.61, 0.56), (0.08, 0.65, 0.568), c("grn_d"), skip="-z")

    for s in (-1, 1):
        for z in (-0.18, 0.18):
            m.box((s * 0.975 - 0.02, 0.82, z - 0.03), (s * 0.975 + 0.02, 0.96, z + 0.03), c("stl_dd"))

        m.box((s * 0.995 - 0.012, 0.92, -0.2), (s * 0.995 + 0.012, 0.96, 0.2), c("stl_l"))

    return m, {"reach": 0.5, "strength": 0.55}


def lamp():
    m = Mesh(39)

    for z in (-0.55, 0.55):
        m.box((-0.95, 0.0, z - 0.1), (0.95, 0.12, z + 0.1), c("dark"), bevel=0.025, skip="-y")

    m.box((-1.0, 0.12, -0.72), (1.0, 0.28, 0.72), c("stl_dd"), bevel=0.04)
    m.box((-0.9, 0.28, -0.64), (0.9, 1.32, 0.64), c("yel"), bevel=0.1, skip="-y")
    m.box((-0.94, 1.28, -0.68), (0.94, 1.4, 0.68), c("yel_d"), bevel=0.035)

    for s in (-1, 1):
        louvres(m, -0.66, -0.06, 0.52, 1.1, s * 0.645, s, 4)
        m.box((0.1, 0.46, s * 0.645 - 0.008), (0.72, 1.14, s * 0.645 + 0.008), c("yel_l"))
        m.box((0.58, 0.76, s * 0.66 - 0.012), (0.65, 0.9, s * 0.66 + 0.012), c("dark"))

        for x in (-0.78, 0.78):
            m.beam((x * 0.9, 0.2, s * 0.6), (x, 0.2, s * 1.62), 0.11, 0.11, c("stl_d"), bevel=0.02, caps=False)
            m.cyl((x, 0.04, s * 1.62), (x, 0.3, s * 1.62), 0.045, c("stl_l"), seg=6, caps="b")
            m.cyl((x, 0.0, s * 1.62), (x, 0.05, s * 1.62), 0.13, c("dark"), seg=8, chamfer=0.015, caps="b")

    for y0, y1, half in ((1.38, 3.9, 0.17), (3.8, 6.1, 0.13), (6.0, 8.0, 0.095)):
        m.box((-half, y0, -half), (half, y1, half), c("stl"), bevel=half * 0.35, skip="-y")
        m.box((-half - 0.035, y1 - 0.18, -half - 0.035), (half + 0.035, y1 - 0.04, half + 0.035), c("stl_dd"), bevel=0.025)

    m.beam((0.2, 1.4, 0.0), (0.15, 5.6, 0.0), 0.045, 0.045, c("rubber"), caps=False)
    m.extrude([(-0.1, 7.55), (0.1, 7.55), (0.82, 7.93), (-0.82, 7.93)], -0.07, 0.07, c("stl_d"), axis="z")
    m.box((-1.0, 7.9, -0.1), (1.0, 8.997, 0.08), c("stl_d"), bevel=0.04)
    m.box((-0.97, 8.4, -0.112), (0.97, 8.49, -0.09), c("yel"), skip="+z")

    for row, y in enumerate((8.0, 8.49)):
        for k in range(3):
            x = -0.92 + k * 0.63
            m.box((x, y, 0.05), (x + 0.57, y + 0.43, 0.24), c("stl_d"), bevel=0.04, skip="-z")
            m.face([(x + 0.07, y + 0.07, 0.246), (x + 0.5, y + 0.07, 0.246), (x + 0.5, y + 0.36, 0.246), (x + 0.07, y + 0.36, 0.246)], (0.93, 0.9, 0.78), m_vec(x, y, -2))
            m.box((x + 0.1, y + 0.08, -0.17), (x + 0.47, y + 0.32, -0.09), c("stl"), bevel=0.025, skip="+z")

    return m, {"reach": 0.6, "strength": 0.5, "grime": 0.6, "low": 0.55}


def sign():
    m = Mesh(40)

    for x in (-0.76, 0.76):
        m.beam((x, 0.07, -0.05), (x, 1.5, -0.05), 0.09, 0.09, c("stl_d"), caps=False)
        m.box((x - 0.16, 0.0, -0.25), (x + 0.16, 0.1, 0.25), c("rubber"), bevel=0.025, skip="-y")

    m.box((-1.0, 0.78, -0.02), (1.0, 2.2, 0.04), c("stl_dd"), bevel=0.018)
    m.box((-0.94, 0.84, 0.035), (0.94, 2.14, 0.055), c("wht"), skip="-z")
    m.box((-0.92, 0.86, -0.032), (0.92, 2.12, -0.018), c("stl"), skip="+z")
    m.box((-0.5, 1.68, -0.044), (0.5, 1.96, -0.03), c("yel"), skip="+z")
    m.box((-0.94, 1.86, 0.05), (0.94, 2.14, 0.065), c("blu"), skip="-z")
    m.box((-0.78, 1.97, 0.062), (0.5, 2.05, 0.072), c("wht"), skip="-z")
    out = m_vec(0, 1, -4)

    def tri(cx, cy, r, z, col):
        m.face([(cx - r, cy - r * 0.8, z), (cx + r, cy - r * 0.8, z), (cx, cy + r, z)], col, out)

    def disc(cx, cy, r, z, col, seg=10):
        m.face([(cx + math.cos(k * math.tau / seg) * r, cy + math.sin(k * math.tau / seg) * r, z) for k in range(seg)], col, out)

    tri(-0.62, 1.6, 0.21, 0.066, c("dark"))
    tri(-0.62, 1.6, 0.155, 0.07, c("yel_l"))
    disc(-0.62, 1.22, 0.16, 0.066, c("blu"))
    disc(-0.62, 1.245, 0.075, 0.07, c("wht"))
    m.box((-0.72, 1.12, 0.066), (-0.52, 1.17, 0.072), c("wht"), skip="-z")
    disc(-0.62, 0.99, 0.1, 0.066, c("red"))
    disc(-0.62, 0.99, 0.065, 0.07, c("wht"))

    for y, w in ((1.66, 1.16), (1.53, 0.84), (1.28, 1.02), (1.15, 0.7), (1.0, 0.94), (0.9, 0.6)):
        m.box((-0.3, y, 0.052), (-0.3 + w, y + 0.06, 0.064), c("stl_d"), skip="-z")

    for x in (-0.76, 0.76):
        m.box((x - 0.1, 1.1, -0.09), (x + 0.1, 1.2, -0.015), c("stl"))

    return m, {"reach": 0.4, "strength": 0.4, "grime": 0.35, "low": 0.65}


def formwork():
    m = Mesh(41)

    for i in range(4):
        a = -2.0 + i
        b = a + 0.99
        face = m.shade(c("wd_d"), 0.06)
        m.box((a + 0.07, 0.07, 0.0), (b - 0.07, 3.0, 0.07), mul(face, 1.08), skip="-y,+y,-x,+x")

        for x in (a, b - 0.085):
            m.box((x, 0.0, -0.05), (x + 0.085, 3.06, 0.11), c("ox"), bevel=0.016, skip="-y")

        for y in (0.0, 1.5, 2.975):
            m.box((a + 0.085, y, -0.05), (b - 0.085, y + 0.085, 0.1), c("ox"), bevel=0.016, skip="-x,+x")

        for y in (0.75, 2.25):
            for x in (a + 0.3, b - 0.3):
                m.disc((x, y + 0.2, 0.074), (0, 0, 1), 0.05, c("void"))

        for y in (0.75, 2.25):
            m.box((a + 0.085, y, -0.045), (b - 0.085, y + 0.06, 0.0), c("ox_d"), skip="-x,+x,+z")

    for y in (0.62, 2.32):
        m.box((-2.0, y, -0.18), (2.0, y + 0.13, -0.05), c("yel"), bevel=0.022)

        for x in (-1.5, -0.5, 0.5, 1.5):
            m.box((x - 0.06, y - 0.03, -0.2), (x + 0.06, y + 0.16, -0.17), c("stl_dd"))

    for x in (-1.0, 1.0):
        m.cyl((x, 2.05, 0.11), (x, 0.1, 0.94), 0.045, c("stl_l"), seg=6, caps="")
        m.cyl((x, 1.22, 0.463), (x, 0.88, 0.608), 0.065, c("yel_d"), seg=6, caps="ab")
        m.box((x - 0.15, 0.0, 0.7), (x + 0.15, 0.1, 1.0), c("stl_dd"), bevel=0.025, skip="-y")

    for x in (-1.45, 1.45):
        m.cyl((x, 2.35, -0.2), (x, 0.1, -0.94), 0.045, c("stl_l"), seg=6, caps="")
        m.cyl((x, 0.68, -0.2), (x, 0.1, -0.8), 0.035, c("stl"), seg=6, caps="")
        m.cyl((x, 1.5, -0.485), (x, 1.08, -0.62), 0.065, c("yel_d"), seg=6, caps="ab")
        m.box((x - 0.15, 0.0, -1.004), (x + 0.15, 0.1, -0.7), c("stl_dd"), bevel=0.025, skip="-y")

    for x in (-1.9, -0.65, 0.65, 1.9):
        m.beam((x, 2.78, -0.06), (x, 2.78, -0.86), 0.07, 0.07, c("stl_d"))
        m.beam((x, 2.35, -0.1), (x, 2.75, -0.62), 0.045, 0.045, c("stl_d"), caps=False)
        m.beam((x, 2.78, -0.83), (x, 3.775, -0.83), 0.055, 0.055, c("yel"), caps="b")

    for k in range(3):
        z = -0.8 + k * 0.24
        m.box((-1.98, 2.81, z), (1.98, 2.87, z + 0.22), m.shade(c("wd_l"), 0.08), bevel=0.012)

    for y in (3.31, 3.72):
        m.beam((-1.92, y + 0.027, -0.83), (1.92, y + 0.027, -0.83), 0.055, 0.055, c("yel"))

    m.box((-1.95, 2.87, -0.84), (1.95, 3.0, -0.81), c("ox_d"))

    return m, {"reach": 0.9, "strength": 0.65}


def core_wall():
    m = Mesh(42)

    for lift, (y0, y1) in enumerate(((0.0, 3.25), (3.31, 6.4))):
        for i in range(4):
            a = -2.0 + i
            col = m.shade(c("con" if (i + lift) % 2 else "con_l"), 0.03)
            m.box((a + 0.006, y0, -0.15), (a + 0.994, y1, 0.15), col, bevel=0.022, skip="-y")

            for x, y in ((a + 0.25, y0 + 0.7), (a + 0.75, y0 + 2.4)):
                for s in (-1, 1):
                    m.disc((x, y, s * 0.153), (0, 0, s), 0.055, c("con_dd"))

    m.box((-2.0, 3.23, -0.125), (2.0, 3.33, 0.125), c("con_dd"), skip="-y,+y")

    for s in (-1, 1):
        for x in (-1.5, 0.0, 1.5):
            m.box((x - 0.14, 3.02, s * 0.15 - 0.008), (x + 0.14, 3.2, s * 0.15 + 0.008), c("ox"))

    for k in range(9):
        x = -1.82 + k * 0.455

        for z in (-0.08, 0.08):
            h = m.rng.uniform(6.52, 6.637)
            m.tube((x, 6.39, z), (x, h, z), 0.024, c("rb"), caps="b")

    for z in (-0.08, 0.08):
        m.tube((-1.88, 6.5, z), (1.88, 6.5, z), 0.016, c("rb_l"), caps="ab")

    return m, {"reach": 0.7, "strength": 0.5, "lift": 0.04}


def scaffold():
    m = Mesh(43)
    tube = c("stl_l")
    deck = 2.0

    for x in (-1.94, 1.94):
        for z in (-0.65, 0.65):
            m.box((x - 0.06, 0.0, z - 0.062), (x + 0.06, 0.045, z + 0.062), c("stl_dd"), skip="-y")
            m.tube((x, 0.04, z), (x, 3.1, z), 0.04, tube, caps="b")

            for y in (0.2, deck - 0.07, 3.03):
                m.box((x - 0.06, y - 0.05, z - 0.06), (x + 0.06, y + 0.05, z + 0.06), c("yel_d"))

        for y in (0.2, deck - 0.07, 3.07):
            m.tube((x, y, -0.65), (x, y, 0.65), 0.03, tube)

    for z in (-0.65, 0.65):
        for y in (0.2, deck - 0.07):
            m.tube((-1.94, y, z), (1.94, y, z), 0.032, tube)

        m.tube((-1.94, 2.52, z), (1.94, 2.52, z), 0.028, tube)
        m.tube((-1.94, 3.072, z), (1.94, 3.072, z), 0.028, tube)
        m.box((-1.9, deck, z - 0.03 * (1 if z > 0 else -1) - 0.015), (1.9, deck + 0.15, z - 0.03 * (1 if z > 0 else -1) + 0.015), c("yel"))

    for k in range(4):
        z = -0.6 + k * 0.302
        m.box((-1.97, deck - 0.045, z + 0.008), (1.97, deck + 0.008, z + 0.292), m.shade(c("wd_l" if k % 2 else "wd"), 0.08), bevel=0.012)

        for x in (-1.972, 1.972):
            m.box((x - 0.03, deck - 0.05, z + 0.004), (x + 0.028, deck + 0.012, z + 0.296), c("stl_d"))

    m.tube((-1.94, 0.22, -0.69), (1.94, deck - 0.1, -0.69), 0.028, c("stl"))

    for x in (1.62, 1.9):
        m.tube((x, 0.0, 0.712 - 0.02), (x, deck - 0.05, 0.712 - 0.02), 0.018, c("yel"))

    for k in range(6):
        y = 0.3 + k * 0.3
        m.tube((1.62, y, 0.692), (1.9, y, 0.692), 0.014, c("yel"))

    return m, {"reach": 0.5, "strength": 0.5, "grime": 0.4, "low": 0.6}


def ibeam(m, a, b, depth, width, col, up=(0, 1, 0), caps=True):
    pa = V(a)
    pb = V(b)
    d = (pb - pa).normalized()
    side = d.cross(V(up)).normalized()
    u = side.cross(d).normalized()
    hw = width / 2
    hd = depth / 2
    t = depth * 0.14
    w = depth * 0.07
    prof = [(-hw, -hd), (hw, -hd), (hw, -hd + t), (w, -hd + t), (w, hd - t), (hw, hd - t), (hw, hd), (-hw, hd), (-hw, hd - t), (-w, hd - t), (-w, -hd + t), (-hw, -hd + t)]
    ra = [pa + side * x + u * y for x, y in prof]
    rb = [pb + side * x + u * y for x, y in prof]

    for i in range(12):
        j = (i + 1) % 12
        e = (prof[j][0] - prof[i][0], prof[j][1] - prof[i][1])
        out = side * e[1] - u * e[0]
        q = [ra[i], ra[j], rb[j], rb[i]]

        if newell(q).dot(out) < 0:
            q.reverse()

        m.poly(q, mul(col, 0.82) if i in (2, 3, 4, 8, 9, 10) else col)

    if caps:
        for end, ring, sign in ((pa, ra, -1), (pb, rb, 1)):
            for ids in ((0, 1, 2, 11), (10, 3, 4, 9), (8, 5, 6, 7)):
                m.face([ring[i] for i in ids], col, end - d * sign)


def framebay():
    m = Mesh(44)
    h = 3.095
    col = c("ox")

    for x in (-1.84, 1.84):
        for z in (-1.84, 1.84):
            m.box((x - 0.16, 0.0, z - 0.16), (x + 0.16, 0.05, z + 0.16), c("con_d"), bevel=0.015, skip="-y")
            ibeam(m, (x, 0.05, z), (x, h - 0.025, z), 0.24, 0.2, col, up=(0, 0, 1), caps=False)
            m.box((x - 0.14, h - 0.025, z - 0.14), (x + 0.14, h, z + 0.14), c("ox_d"))

            for dx in (-0.1, 0.1):
                for dz in (-0.1, 0.1):
                    m.box((x + dx - 0.022, 0.05, z + dz - 0.022), (x + dx + 0.022, 0.1, z + dz + 0.022), c("stl_dd"), skip="-y")

    for z in (-1.84, 1.84):
        ibeam(m, (-1.72, h - 0.14, z), (1.72, h - 0.14, z), 0.23, 0.16, c("ox_l"), caps=False)
        m.beam((-1.76, h - 0.85, z), (-1.15, h - 0.24, z), 0.09, 0.09, c("ox_d"), caps=False)

    for x in (-1.84, 1.84):
        ibeam(m, (x, h - 0.14, -1.72), (x, h - 0.14, 1.72), 0.23, 0.16, c("ox_l"), caps=False)
        m.beam((x, h - 0.85, 1.76), (x, h - 0.24, 1.15), 0.09, 0.09, c("ox_d"), caps=False)

        for z in (-1.84, 1.84):
            for s in (-1, 1):
                m.box((x + s * 0.12 - 0.012, h - 0.28, z - 0.07), (x + s * 0.12 + 0.012, h - 0.02, z + 0.07), c("stl_d"))

    for x in (-0.62, 0.62):
        ibeam(m, (x, h - 0.12, -1.76), (x, h - 0.12, 1.76), 0.16, 0.1, col, caps=False)

    m.box((-1.74, h - 0.035, -1.74), (0.62, h - 0.004, 1.74), c("stl"), skip="")

    for k in range(7):
        x = -1.64 + k * 0.32
        m.box((x, h - 0.006, -1.7), (x + 0.13, h, 1.7), c("stl_d"), skip="-y")

    return m, {"reach": 0.8, "strength": 0.6, "grime": 0.5}


def pedbar():
    m = Mesh(45)

    for x in (-0.8, 0.8):
        m.box((x - 0.09, 0.0, -0.13), (x + 0.09, 0.055, 0.13), c("rubber"), bevel=0.015, skip="-y")

    for x in (-0.97, 0.97):
        m.beam((x, 0.12, 0), (x, 1.1, 0), 0.06, 0.06, c("wht"), caps="b")

    for x in (-0.8, 0.8):
        m.beam((x, 0.04, 0), (x, 0.22, 0), 0.06, 0.06, c("wht_d"), caps=False)

    for y in (0.2, 1.07):
        m.beam((-0.97, y, 0), (0.97, y, 0), 0.06, 0.06, c("wht"), caps=False)

    m.box((-0.94, 0.62, -0.022), (0.94, 0.98, 0.022), c("wht"), skip="-x,+x")

    for s in (-1, 1):
        z = s * 0.027

        for k in range(5):
            x = -0.94 + k * 0.38
            m.face([(x, 0.62, z), (x + 0.19, 0.62, z), (x + 0.33, 0.98, z), (x + 0.14, 0.98, z)], c("ora"), m_vec(x, 0.8, -s * 3))

    for k in range(11):
        x = -0.8 + k * 0.16
        m.beam((x, 0.23, 0), (x, 0.62, 0), 0.026, 0.026, c("wht_d"), caps=False)

    return m, {"reach": 0.35, "strength": 0.4, "grime": 0.4, "low": 0.65}


def mixer():
    m = Mesh(46)
    frame_col = c("dark")

    for x in (-0.38, 0.38):
        m.beam((x, 0.03, 0.46), (x * 0.9, 0.74, 0.02), 0.07, 0.07, frame_col, bevel=0.015)
        m.beam((x, 0.15, -0.34), (x * 0.9, 0.74, -0.02), 0.07, 0.07, frame_col, bevel=0.015)
        m.beam((x * 0.97, 0.3, 0.3), (x * 0.97, 0.22, -0.31), 0.05, 0.05, frame_col, caps=False)
        m.box((x - 0.06, 0.0, 0.38), (x + 0.06, 0.05, 0.499), c("rubber"), bevel=0.014, skip="-y")

    for x in (-0.44, 0.44):
        m.cyl((x - 0.06, 0.17, -0.329), (x + 0.06, 0.17, -0.329), 0.17, c("rubber"), seg=10, chamfer=0.025)
        face = x + math.copysign(0.062, x)
        m.disc((face, 0.17, -0.329), (math.copysign(1, x), 0, 0), 0.085, c("stl_l"), seg=8)

    m.beam((-0.44, 0.17, -0.329), (0.44, 0.17, -0.329), 0.05, 0.05, c("stl_d"), caps=False)
    axis = V((0.0, 0.72, 0.62)).normalized()
    centre = V((0.0, 0.82, 0.0))
    base = centre - axis * 0.42
    prof = [(0.19, 0.0), (0.38, 0.14), (0.42, 0.28), (0.42, 0.46), (0.27, 0.74), (0.285, 0.76), (0.285, 0.8), (0.23, 0.8)]
    m.lathe(base, prof, [c("ora_d"), c("ora"), c("ora"), c("ora_l"), c("stl_d"), c("stl_l"), c("stl_d")], seg=12, axis=axis)
    m.disc(base + axis * 0.76, axis, 0.24, c("void"), seg=12)
    m.disc(base, -axis, 0.19, c("ora_d"), seg=12)
    m.lathe(base, [(0.425, 0.33), (0.455, 0.35), (0.455, 0.41), (0.425, 0.43)], c("stl_dd"), seg=12, axis=axis)

    for x in (-0.465, 0.465):
        m.box((x - 0.035, 0.66, -0.1), (x + 0.035, 0.84, 0.1), c("yel_d"), bevel=0.02)
        m.beam((x * 0.74, 0.72, 0.0), (x, 0.75, 0.0), 0.08, 0.08, c("stl_d"), caps=False)

    m.box((0.17, 0.2, -0.16), (0.46, 0.52, 0.22), c("yel"), bevel=0.06)
    louvres(m, 0.22, 0.41, 0.26, 0.46, 0.226, 1, 3)
    m.cyl((-0.47, 0.75, 0.0), (-0.5, 0.75, 0.0), 0.16, c("stl_dd"), seg=10, chamfer=0.008)

    return m, {"reach": 0.45, "strength": 0.55, "grime": 0.6}


ALL = {
    "mixer": mixer,
    "fence": fence,
    "hoarding": hoarding,
    "barrier": barrier,
    "cone": cone,
    "lights": lights,
    "skip": skip,
    "genset": genset,
    "vault": vault,
    "lamp": lamp,
    "sign": sign,
    "formwork": formwork,
    "core": core_wall,
    "scaffold": scaffold,
    "framebay": framebay,
    "pedbar": pedbar,
}
