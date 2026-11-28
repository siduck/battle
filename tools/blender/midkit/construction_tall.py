import math
import random

from construction_core import Mesh, V, c, mul
from construction_materials import m_vec
from construction_site import ibeam, louvres

F = [0.3, 3.9, 7.5, 11.1, 14.7]

MAIN_WALLS = [
    (1, -11.9, 3.0, -6.0, 3.0, 2.0),
    (1, -2.0, -4.0, -2.0, 3.0, 1.2),
    (1, -4.5, 5.0, 1.5, 5.0, 2.4),
    (2, -11.9, -3.0, -5.0, -3.0, 1.3),
    (2, -1.0, 2.0, -1.0, 8.6, 2.6),
    (2, 1.5, -4.0, 4.5, -4.0, 1.0),
    (3, -8.0, 1.0, -8.0, 8.6, 1.6),
    (3, -3.0, -5.5, 3.0, -5.5, 2.2),
    (0, -11.9, -5.5, -11.9, 1.5, 2.4),
    (0, 1.0, 8.75, 4.5, 8.75, 1.6),
    (0, -3.0, -1.0, -3.0, 4.5, 1.1),
]

SMALL_WALLS = [
    (0, -7.9, -2.5, -7.9, 0.5, 2.1),
    (0, 1.0, -1.0, 6.0, -1.0, 1.2),
    (0, -4.0, 2.0, -4.0, 5.9, 2.4),
    (1, -6.0, 1.0, -1.0, 1.0, 2.0),
    (1, 3.0, -5.9, 7.9, -5.9, 1.4),
    (2, -2.0, -2.0, -2.0, 2.5, 1.6),
    (2, 2.0, -1.0, 7.0, -1.0, 2.4),
    (3, -7.0, 1.5, -3.0, 1.5, 1.0),
]


def rail_run(m, x0, z0, x1, z1, y, solid=True):
    h = 1.1
    lx = abs(x1 - x0)
    lz = abs(z1 - z0)
    n = max(1, int(round(max(lx, lz) / 2.5)))

    for i in range(n + 1):
        t = i / n
        px = x0 + (x1 - x0) * t
        pz = z0 + (z1 - z0) * t
        m.beam((px, y, pz), (px, y + h - 0.02, pz), 0.08, 0.08, c("yel_d"), caps=False)

    for hh, th, col in ((h - 0.035, 0.07, "yel"), (0.55, 0.05, "yel_l")):
        m.beam((x0, y + hh, z0), (x1, y + hh, z1), th, th, c(col), caps=False)

    if lx >= lz:
        m.box((min(x0, x1), y, z0 - 0.02), (max(x0, x1), y + 0.15, z0 + 0.02), c("wd"), skip="-y")

        if solid:
            m.solid((min(x0, x1), y, z0 - 0.08), (max(x0, x1), y + h, z0 + 0.08))
    else:
        m.box((x0 - 0.02, y, min(z0, z1)), (x0 + 0.02, y + 0.15, max(z0, z1)), c("wd"), skip="-y")

        if solid:
            m.solid((x0 - 0.08, y, min(z0, z1)), (x0 + 0.08, y + h, max(z0, z1)))


def blockwall(m, x0, z0, x1, z1, y, h, rng):
    course = 0.3
    rows = int(h / course)
    along_x = abs(x1 - x0) >= abs(z1 - z0)
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    a = min(x0, x1) if along_x else min(z0, z1)
    t = 0.1
    full = rows - 2
    tones = ("con_l", "con", "con_l", "con_d")

    def rect(s0, e0, ya, yb, inset=0.0):
        if along_x:
            return (a + s0, ya, z0 - t + inset), (a + e0, yb, z0 + t - inset)

        return (x0 - t + inset, ya, a + s0), (x0 + t - inset, yb, a + e0)

    for r in range(rows):
        lim = length if r < full else length * rng.uniform(0.35, 0.95)
        s = 0.0 if r % 2 == 0 else -0.6
        yy = y + r * course

        while s < lim:
            e = min(s + 1.2, lim)
            s0 = max(s, 0)

            if e - s0 > 0.06:
                lo, hi = rect(s0 + 0.01, e - 0.01, yy + 0.014, yy + course - 0.006)
                hidden = "-y,+y" if r < rows - 1 else "-y"
                m.box(lo, hi, m.shade(c(rng.choice(tones)), 0.03), skip=hidden)

            s = e

        lo, hi = rect(0, lim, yy, yy + course - 0.01, 0.022)
        m.box(lo, hi, c("con_dd"), skip="-y")

        if r >= full:
            lo, hi = rect(0, lim, yy, yy + course)
            m.solid(lo, hi)

    lo, hi = rect(0, length, y, y + full * course)
    m.solid(lo, hi)


def stair(m, x0, x1, z0, z1, y0, y1):
    n = int(round((y1 - y0) / 0.3))
    run = (x1 - x0) / n
    rise = (y1 - y0) / n

    for i in range(n):
        xa = x0 + run * i
        xb = x0 + run * (i + 1)
        top = y0 + rise * (i + 1)
        m.box((min(xa, xb), top - rise - 0.03, z0), (max(xa, xb), top, z1), c("con_l" if i % 2 else "con"), skip="-y")

    mid = (z0 + z1) / 2
    m.beam((x0 + run * 0.6, y0 + 0.02, mid), (x1, y1 - 0.42, mid), z1 - z0 - 0.12, 0.16, c("con_d"), caps="a")

    for z in (z0 - 0.045, z1 + 0.045):
        m.beam((x0, y0 + 0.08, z), (x1, y1 - 0.12, z), 0.08, 0.34, c("con_dd"))

    m.ramp((min(x0, x1), y0, z0), (max(x0, x1), y1, z1), "px" if x1 > x0 else "nx")
    zr = z0 - 0.04

    for i in range(0, n + 1, 3):
        px = x0 + run * i
        m.beam((px, y0 + rise * i - 0.1, zr), (px, y0 + rise * i + 1.02, zr), 0.06, 0.06, c("yel_d"), caps="b")

    m.beam((x0, y0 + 0.99, zr), (x1, y1 + 0.99, zr), 0.06, 0.06, c("yel"))


def cuts(lo, hi, holes, i):
    return sorted({lo, hi} | {h[i] for h in holes if lo < h[i] < hi} | {h[i + 1] for h in holes if lo < h[i + 1] < hi})


def slab(m, y, x0, x1, z0, z1, holes, deck=False, outer=(True, True, True, True)):
    cx = cuts(x0, x1, holes, 0)
    cz = cuts(z0, z1, holes, 2)

    def solid_cell(i, j):
        if i < 0 or j < 0 or i >= len(cx) - 1 or j >= len(cz) - 1:
            return False

        mx = (cx[i] + cx[i + 1]) / 2
        mz = (cz[j] + cz[j + 1]) / 2

        return not any(h[0] <= mx <= h[1] and h[2] <= mz <= h[3] for h in holes)

    for i in range(len(cx) - 1):
        for j in range(len(cz) - 1):
            if not solid_cell(i, j):
                continue

            ax, bx = cx[i], cx[i + 1]
            az, bz = cz[j], cz[j + 1]
            m.solid((ax, y - 0.3, az), (bx, y, bz))
            under = m_vec((ax + bx) / 2, y + 5, (az + bz) / 2)
            over = m_vec((ax + bx) / 2, y - 5, (az + bz) / 2)
            sides = []

            for di, dj, quad, edge in (
                (-1, 0, [(ax, az), (ax, bz)], 0),
                (1, 0, [(bx, bz), (bx, az)], 1),
                (0, -1, [(bx, az), (ax, az)], 2),
                (0, 1, [(ax, bz), (bx, bz)], 3),
            ):
                if solid_cell(i + di, j + dj):
                    continue

                at_edge = (i + di < 0) or (i + di >= len(cx) - 1) or (j + dj < 0) or (j + dj >= len(cz) - 1)

                if at_edge and not outer[edge]:
                    continue

                sides.append((quad, at_edge, di, dj))

            for quad, at_edge, di, dj in sides:
                (px, pz), (qx, qz) = quad
                inside = m_vec(px - di * 1.0, y - 0.15, pz - dj * 1.0)

                if at_edge:
                    m.face([(px, y - 0.3, pz), (qx, y - 0.3, qz), (qx, y - 0.2, qz), (px, y - 0.2, pz)], c("con_dd"), inside)
                    m.face([(px, y - 0.2, pz), (qx, y - 0.2, qz), (qx, y, qz), (px, y, pz)], c("wd") if deck else c("con_l"), inside)
                else:
                    m.face([(px, y - 0.3, pz), (qx, y - 0.3, qz), (qx, y, qz), (px, y, pz)], c("con_d"), inside)

            bottom = [(ax, y - 0.3, az), (bx, y - 0.3, az), (bx, y - 0.3, bz), (ax, y - 0.3, bz)]
            m.grid(bottom, c("con_d" if not deck else "stl_d"), under, 4.5)

            if not deck:
                top = [(ax, y, az), (bx, y, az), (bx, y, bz), (ax, y, bz)]
                m.grid(top, c("con"), over, 4.5)
                continue

            m.face([(ax, y - 0.05, az), (bx, y - 0.05, az), (bx, y - 0.05, bz), (ax, y - 0.05, bz)], c("stl"), over)
            r = ax + 0.25

            while r < bx - 0.25:
                m.box((r, y - 0.05, az + 0.05), (r + 0.17, y - 0.022, bz - 0.05), c("stl_l"), skip="-y,-z,+z")
                r += 0.62

            r = az + 0.35

            while r < bz - 0.2:
                m.tube((ax + 0.1, y + 0.004, r), (bx - 0.1, y + 0.004, r), 0.026, c("rb"))
                r += 0.7

            r = ax + 0.55

            while r < bx - 0.2:
                m.tube((r, y + 0.026, az + 0.1), (r, y + 0.026, bz - 0.1), 0.022, c("rb_l"))
                r += 1.3


def column(m, x, y0, y1, z):
    m.beam((x, y0, z), (x, y1, z), 0.5, 0.5, m.shade(c("con_l"), 0.03), bevel=0.09, caps=False)
    m.box((x - 0.28, y0, z - 0.28), (x + 0.28, y0 + 0.12, z + 0.28), c("con_d"), skip="-y")


def cage(m, x, y0, y1, z, rings=1):
    for ox in (-0.15, 0.15):
        for oz in (-0.15, 0.15):
            m.tube((x + ox, y0, z + oz), (x + ox, y1, z + oz), 0.028, c("rb"), caps="b")

    for k in range(rings):
        y = y0 + (y1 - y0) * (k + 0.6) / (rings + 0.2)
        pts = [(x - 0.17, y, z - 0.17), (x + 0.17, y, z - 0.17), (x + 0.17, y, z + 0.17), (x - 0.17, y, z + 0.17)]

        for i in range(4):
            m.beam(pts[i], pts[(i + 1) % 4], 0.028, 0.028, c("rb_l"), caps=False)


def core_shaft(m, cbox, top_y):
    cx0, cx1, cz0, cz1 = cbox
    top = top_y + 4.2

    for a, b, skip in (((cx0, 0.3, cz0), (cx1, top, cz0 + 0.3), "-y"), ((cx0, 0.3, cz1 - 0.3), (cx1, top, cz1), "-y"), ((cx0, 0.3, cz0 + 0.3), (cx0 + 0.3, top, cz1 - 0.3), "-y,-z,+z"), ((cx1 - 0.3, 0.3, cz0 + 0.3), (cx1, top, cz1 - 0.3), "-y,-z,+z")):
        m.box(a, b, c("con"), bevel=0.05, skip=skip)

    m.solid((cx0, 0.3, cz0), (cx1, top, cz1))

    for y in F[1:5]:
        if y < top_y - 0.1:
            for z, s in ((cz0, -1), (cz1, 1)):
                m.box((cx0 + 0.1, y - 0.1, z + s * 0.0), (cx1 - 0.1, y - 0.04, z + s * 0.03), c("con_dd"), skip="-z" if s > 0 else "+z")

    y0, y1 = top - 2.6, top + 0.6

    for a, b, s in ((cz0 - 0.28, cz0, -1), (cz1, cz1 + 0.28, 1)):
        width = (cx1 - cx0 + 0.7) / 4

        for i in range(4):
            xa = cx0 - 0.35 + width * i
            m.box((xa + 0.015, y0, a), (xa + width - 0.015, y1, b), m.shade(c("ox"), 0.05))

            for x in (xa + 0.18, xa + width - 0.28):
                m.box((x, y0 + 0.06, (a - 0.05) if s < 0 else b), (x + 0.1, y1 - 0.06, a if s < 0 else (b + 0.05)), c("ox_d"), skip="+z" if s < 0 else "-z")

        zo = a - 0.09 if s < 0 else b + 0.09

        for y in (y0 + 0.7, y1 - 0.7):
            m.beam((cx0 - 0.35, y, zo), (cx1 + 0.35, y, zo), 0.09, 0.12, c("yel"))

        z0, z1 = (a - 0.62, a) if s < 0 else (b, b + 0.62)

        for k in range(3):
            za = z0 + 0.62 * k / 3
            m.box((cx0 - 0.35, y1 + 0.02, za + 0.006), (cx1 + 0.35, y1 + 0.1, za + 0.2), m.shade(c("wd_l"), 0.08))

        edge = z0 + 0.04 if s < 0 else z1 - 0.04

        for k in range(4):
            x = cx0 - 0.3 + (cx1 - cx0 + 0.6) * k / 3
            m.beam((x, y1 + 0.1, edge), (x, y1 + 1.06, edge), 0.06, 0.06, c("yel_d"), caps="b")
            m.beam((x, y1 - 0.7, a if s < 0 else b), (x, y1 + 0.03, edge), 0.06, 0.06, c("stl_d"), caps=False)

        for y in (y1 + 0.55, y1 + 1.03):
            m.beam((cx0 - 0.33, y, edge), (cx1 + 0.33, y, edge), 0.05, 0.05, c("yel"))

    for a, b in ((cx0 - 0.28, cx0), (cx1, cx1 + 0.28)):
        m.box((a, y0, cz0 - 0.02), (b, y1, cz1 + 0.02), c("ox"), bevel=0.035)

        for y in (y0 + 0.7, y1 - 0.7):
            x = a - 0.07 if a < cx0 else b + 0.07
            m.beam((x, y, cz0 - 0.3), (x, y, cz1 + 0.3), 0.09, 0.12, c("yel"))

    for x in (cx0 + 0.8, cx1 - 0.8):
        m.beam((x, y0, cz0 - 0.4), (x, y1 + 0.1, cz0 - 0.4), 0.12, 0.12, c("yel_d"), bevel=0.025)

    for x in (cx0 + 0.15, cx0 + 1.4, cx0 + 2.7, cx0 + 4.0, cx1 - 0.15):
        for z in (cz0 + 0.15, cz1 - 0.15):
            m.tube((x, top, z), (x, top + 0.9, z), 0.028, c("rb"), caps="b")

    door_x = cx0 + 0.6
    m.box((door_x, F[1], cz0 - 0.035), (door_x + 1.6, F[1] + 2.4, cz0), c("blu_d"), bevel=0.012, skip="+z")
    m.box((door_x + 0.1, F[1] + 0.1, cz0 - 0.05), (door_x + 1.5, F[1] + 2.3, cz0 - 0.03), c("blu"), skip="+z")
    m.box((door_x + 1.25, F[1] + 1.05, cz0 - 0.07), (door_x + 1.34, F[1] + 1.25, cz0 - 0.045), c("wht"), skip="+z")


def tower(name, X0, X1, Z0, Z1, nf, core, partial, walls, seed):
    m = Mesh(seed + 100)
    rng = random.Random(seed)
    W = X1 - X0
    hole_a = (X0 + 1.8, X0 + 8.7, Z0 + 0.4, Z0 + 2.8)
    hole_b = (X1 - 8.7, X1 - 1.8, Z1 - 2.8, Z1 - 0.4)
    cbox = (5.2, 10.6, -1.4, 5.4) if core else None
    mid = round(X0 + W * 0.58)
    mx = (X0 + X1) / 2
    mz = (Z0 + Z1) / 2
    top_y = F[nf]

    m.box((X0 - 0.6, -1.0, Z0 - 0.6), (X1 + 0.6, 0.18, Z1 + 0.6), c("con_dd"), bevel=0.08, skip="-y,+y")
    m.grid([(X0 - 0.52, 0.18, Z0 - 0.52), (X1 + 0.52, 0.18, Z0 - 0.52), (X1 + 0.52, 0.18, Z1 + 0.52), (X0 - 0.52, 0.18, Z1 + 0.52)], c("con_d"), m_vec(0, -9, 0), 6)
    m.box((X0 - 0.2, 0.18, Z0 - 0.2), (X1 + 0.2, 0.3, Z1 + 0.2), c("con"), skip="-y,+y", bevel=0.03)
    m.grid([(X0 - 0.17, 0.3, Z0 - 0.17), (X1 + 0.17, 0.3, Z0 - 0.17), (X1 + 0.17, 0.3, Z1 + 0.17), (X0 - 0.17, 0.3, Z1 + 0.17)], c("con"), m_vec(0, -9, 0), 4)
    m.solid((X0 - 0.6, -1.0, Z0 - 0.6), (X1 + 0.6, 0.3, Z1 + 0.6))

    for i in range(1, nf):
        slab(m, F[i], X0, X1, Z0, Z1, [hole_a if i % 2 else hole_b])

    top_hole = hole_a if nf % 2 else hole_b

    if partial:
        slab(m, top_y, X0, mid, Z0, Z1, [top_hole], outer=(True, False, True, True))
        slab(m, top_y, mid, X1, Z0, Z1, [top_hole] + ([cbox] if cbox else []), deck=True, outer=(False, True, True, True))
        m.box((mid - 0.04, top_y - 0.3, Z0), (mid + 0.04, top_y + 0.04, Z1), c("wd_d"), skip="")
    else:
        slab(m, top_y, X0, X1, Z0, Z1, [top_hole])

    nx = max(2, round(W / 8)) + 1
    nz = max(2, round((Z1 - Z0) / 9)) + 1
    cols_x = [X0 + 0.25 + (W - 0.5) * k / (nx - 1) for k in range(nx)]
    cols_z = [Z0 + 0.25 + (Z1 - Z0 - 0.5) * k / (nz - 1) for k in range(nz)]

    def in_core(cx, cz):
        return cbox and cbox[0] - 0.2 < cx < cbox[1] + 0.2 and cbox[2] - 0.2 < cz < cbox[3] + 0.2

    for i in range(1, nf + 1):
        for cz in cols_z:
            end = mid if partial and i == nf else X1 - 0.05
            m.box((X0 + 0.05, F[i] - 0.52, cz - 0.15), (end, F[i] - 0.3, cz + 0.15), c("con"), skip="+y")

    for i in range(nf):
        for cx in cols_x:
            for cz in cols_z:
                if in_core(cx, cz):
                    continue

                column(m, cx, F[i], F[i + 1] - 0.3, cz)
                m.solid((cx - 0.25, F[i], cz - 0.25), (cx + 0.25, F[i + 1] - 0.3, cz + 0.25))

    for cx in cols_x:
        for cz in cols_z:
            if in_core(cx, cz):
                continue

            poured = not partial or cx < mid
            h = 0.9 if poured else 0.0

            if poured:
                m.box((cx - 0.25, top_y, cz - 0.25), (cx + 0.25, top_y + h, cz + 0.25), c("con_l"), bevel=0.07, skip="-y")

            cage(m, cx, top_y + h, top_y + h + 1.2, cz)
            m.solid((cx - 0.25, top_y, cz - 0.25), (cx + 0.25, top_y + h + 1.2, cz + 0.25))

    if cbox:
        core_shaft(m, cbox, top_y)

    for i in range(nf):
        if i % 2 == 0:
            stair(m, X0 + 2.0, X0 + 8.5, Z0 + 0.6, Z0 + 2.6, F[i], F[i + 1])
        else:
            stair(m, X1 - 2.0, X1 - 8.5, Z1 - 2.6, Z1 - 0.6, F[i], F[i + 1])

    for i in range(1, nf + 1):
        h = hole_a if i % 2 else hole_b
        y = F[i]

        if i % 2:
            rail_run(m, h[0], h[3], h[1] - 1.4, h[3], y)
            rail_run(m, h[0], h[2], h[0], h[3], y)
        else:
            rail_run(m, h[0] + 1.4, h[2], h[1], h[2], y)
            rail_run(m, h[1], h[2], h[1], h[3], y)

    for i in range(1, nf + 1):
        y = F[i]
        rail_run(m, X0, Z1 + 0.05, mx - 1.5, Z1 + 0.05, y)
        rail_run(m, mx + 1.5, Z1 + 0.05, X1, Z1 + 0.05, y)
        rail_run(m, X1 + 0.05, Z0 + 0.5, X1 + 0.05, mz - 1.5, y)
        rail_run(m, X1 + 0.05, mz + 1.5, X1 + 0.05, Z1, y)

        if i > 1:
            rail_run(m, X0 - 0.05, Z0 + 0.5, X0 - 0.05, Z0 + 6.5, y)

        rail_run(m, X0 - 0.05, Z0 + 7.5, X0 - 0.05, Z1, y)

    scaffold_front(m, X0, X1, Z0, nf)
    walkway(m, X0, Z0)

    for lvl, x0, z0, x1, z1, h in walls:
        blockwall(m, x0, z0, x1, z1, F[lvl], h, rng)

    for i in range(1, nf):
        for q in range(8):
            x = rng.uniform(X0 + 1, X1 - 3)
            z = rng.uniform(Z0 + 1, Z1 - 2)
            w = rng.uniform(0.6, 1.6)
            d = rng.uniform(0.6, 1.4)
            col = c(("con_d", "sand_d", "con_l", "dirt_l")[q % 4])
            m.face([(x + w * 0.2, F[i] + 0.006, z), (x + w, F[i] + 0.006, z + d * 0.25), (x + w * 0.8, F[i] + 0.006, z + d), (x, F[i] + 0.006, z + d * 0.7)], mul(col, 0.97), m_vec(x, -9, z))

            if q < 3:
                for k in range(3):
                    m.rock((x + k * 0.22, F[i] + 0.03, z + (k % 2) * 0.2), 0.12, 0.09, 0.11, c("con_d"))

    return m, {"reach": 3.2, "strength": 0.72, "low": 0.46, "grime": 0.8, "rays": 18}


def scaffold_front(m, X0, X1, Z0, nf):
    top_y = F[nf]
    sx0, sx1 = X0 - 1.0, X1 + 1.0
    sz0, sz1 = Z0 - 1.55, Z0 - 0.15
    std = [sx0 + q * 2.6 for q in range(int((sx1 - sx0) / 2.6) + 1)]
    sx1 = std[-1]
    steel = c("stl_l")
    cap = top_y + 2.0

    for x in std:
        for z in (sz0, sz1):
            m.tube((x, 0.0, z), (x, cap, z), 0.045, steel, caps="b")
            m.box((x - 0.12, 0.0, z - 0.12), (x + 0.12, 0.07, z + 0.12), c("wd_d"), skip="-y")
            m.solid((x - 0.05, 0.0, z - 0.05), (x + 0.05, cap, z + 0.05))

    for z in (sz0, sz1):
        m.tube((sx0, cap - 0.03, z), (sx1, cap - 0.03, z), 0.03, steel)

    for x in std:
        m.tube((x, cap - 0.03, sz0), (x, cap - 0.03, sz1), 0.03, steel)

    for i in range(1, nf + 1):
        y = F[i]

        for q in range(5):
            zz = sz0 + 0.1 + q * 0.26
            m.box((sx0, y - 0.05, zz), (sx1, y, zz + 0.236), m.shade(c(("wd", "wd_l", "wd_l")[(q + i) % 3]), 0.07), skip="" if q in (0, 4) else "-z,+z")

        m.solid((sx0, y - 0.06, sz0), (sx1, y, sz1))
        m.box((sx0, y, sz0 + 0.03), (sx1, y + 0.16, sz0 + 0.065), c("yel"), skip="-y")

        for hh in (0.55, 1.05):
            m.tube((sx0, y + hh, sz0 - 0.05), (sx1, y + hh, sz0 - 0.05), 0.03, steel)

        m.solid((sx0, y, sz0 - 0.1), (sx1, y + 1.1, sz0))
        m.solid((sx0 - 0.1, y, sz0), (sx0, y + 1.1, sz1))
        m.solid((sx1, y, sz0), (sx1 + 0.1, y + 1.1, sz1))

        for k, x in enumerate(std):
            m.tube((x, y - 0.1, sz0), (x, y - 0.1, sz1), 0.028, steel)

            if (k + i) % 2:
                continue

            m.box((x - 0.075, y - 0.14, sz0 - 0.09), (x + 0.075, y - 0.02, sz0 + 0.03), c("yel_d"), skip="+z")

        for x in (sx0, sx1):
            for hh in (0.55, 1.05):
                m.tube((x, y + hh, sz0), (x, y + hh, sz1), 0.025, steel)

        if i < nf:
            for q in range(0, len(std) - 1, 2):
                a, b = (std[q], std[q + 1]) if i % 2 else (std[q + 1], std[q])
                m.tube((a, y + 0.1, sz0 - 0.085), (b, F[i + 1] - 0.15, sz0 - 0.085), 0.027, c("stl"))

    for q in range(0, len(std) - 1, 2):
        m.tube((std[q], 0.15, sz0 - 0.085), (std[q + 1], F[1] - 0.15, sz0 - 0.085), 0.027, c("stl"))

    for level, phase in ((2, 1), (1, 3), (3, 4)):
        if level >= nf:
            continue

        for i, x in enumerate(std[:-1]):
            if i % 5 != phase % 5:
                continue

            y = F[level]
            a, b = x + 0.07, x + 2.53

            for k in range(3):
                m.box((a + k * 0.82, y + 0.17, sz0 - 0.15), (a + k * 0.82 + 0.82, y + 1.9, sz0 - 0.12 - 0.012 * (k % 2)), mul(c("blu"), (1.0, 1.1, 0.95)[k]))

            m.box((a, y + 1.36, sz0 - 0.172), (b, y + 1.66, sz0 - 0.145), c("wht"))
            m.box((a + 0.24, y + 0.55, sz0 - 0.172), (a + 1.2, y + 0.75, sz0 - 0.145), c("ora"))
            m.box((a + 0.24, y + 0.36, sz0 - 0.172), (a + 1.7, y + 0.45, sz0 - 0.145), c("wht"))


def walkway(m, X0, Z0):
    wx0, wx1 = X0 - 2.6, X0 - 0.2
    za0 = Z0 + 7.0
    run = 9.0
    n = 12

    for k in range(5):
        xa = wx0 + (wx1 - wx0) * k / 5
        m.box((xa + 0.006, F[1] - 0.25, Z0 - 0.2), (xa + (wx1 - wx0) / 5 - 0.006, F[1], za0), m.shade(c("wd_l"), 0.09))

    m.solid((wx0, F[1] - 0.25, Z0 - 0.2), (wx1, F[1], za0))

    for q in range(n):
        za = za0 + run * q / n
        zb = za0 + run * (q + 1) / n
        yy = F[1] - (q + 1) * F[1] / n
        m.box((wx0 + 0.1, yy - 0.07, za), (wx1 - 0.1, yy + 0.012, zb - 0.01), m.shade(c(("wd", "wd_l", "wd_l")[q % 3]), 0.06))
        m.box((wx0 + 0.1, yy + 0.012, zb - 0.07), (wx1 - 0.1, yy + 0.05, zb - 0.02), c("yel"), skip="-y")

    m.ramp((wx0, 0.0, za0), (wx1, F[1], za0 + run), "nz")

    for x in (wx0, wx1):
        m.beam((x, F[1] - 0.22, za0), (x, -0.02, za0 + run), 0.12, 0.26, c("stl_d"), bevel=0.02)

    for z in (za0, za0 + 3, za0 + 6):
        yy = (za0 + run - z) / run * F[1]
        m.beam((wx0, 0, z), (wx0, yy + 1.03, z), 0.08, 0.08, c("stl_l"), caps="b")
        m.beam((wx1, 0, z), (wx1, yy - 0.1, z), 0.08, 0.08, c("stl_l"), caps=False)

    m.beam((wx0, F[1] + 1.0, za0), (wx0, 1.0, za0 + run), 0.06, 0.06, c("yel"))
    m.solid((wx0 - 0.1, 0.0, za0), (wx0, F[1] + 1.1, za0 + run))
    z = Z0 - 0.2
    m.beam((wx0, 0, z), (wx0, F[1] + 1.1, z), 0.08, 0.08, c("stl_l"), caps="b")
    m.beam((wx1, 0, z), (wx1, F[1], z), 0.08, 0.08, c("stl_l"), caps=False)
    rail_run(m, wx0, Z0 - 0.2, wx0, za0, F[1])


def tower_main():
    return tower("tower", -12, 12, -9, 9, 4, True, True, MAIN_WALLS, 11)


def tower_small():
    return tower("tower2", -8, 8, -6, 6, 3, False, False, SMALL_WALLS, 5)


def crane():
    m = Mesh(51)
    yel, yel_d, yel_l = c("yel"), c("yel_d"), c("yel_l")

    for x in (-3.0, 3.0):
        for z in (-3.0, 3.0):
            m.box((x - 0.9, 0.0, z - 0.9), (x + 0.9, 0.9, z + 0.9), c("con_d"), bevel=0.1, skip="-y")
            m.box((x - 0.55, 0.9, z - 0.55), (x + 0.55, 1.05, z + 0.55), c("stl_dd"), bevel=0.03, skip="-y")
            sx, sz = math.copysign(1, x), math.copysign(1, z)
            m.beam((x - sx * 0.1, 1.15, z - sz * 0.1), (sx * 1.3, 1.15, sz * 1.3), 0.42, 0.3, yel_d, bevel=0.07)
            m.beam((x - sx * 0.25, 1.25, z - sz * 0.25), (sx * 1.3, 5.2, sz * 1.3), 0.2, 0.2, yel, caps=False)
            m.solid((x - 0.9, 0.0, z - 0.9), (x + 0.9, 0.9, z + 0.9))

    m.solid((-2.0, 0, -2.0), (2.0, 42.5, 2.0))
    half = 1.28
    y0, y1 = 1.0, 42.5

    for x in (-half, half):
        for z in (-half, half):
            m.beam((x, y0, z), (x, y1, z), 0.3, 0.3, yel, bevel=0.07, caps="a")

    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    levels = 15
    step = (y1 - 1.2) / levels

    for k in range(levels + 1):
        y = 1.2 + step * k

        for i in range(4):
            (ax, az), (bx, bz) = corners[i], corners[(i + 1) % 4]
            m.beam((ax, y, az), (bx, y, bz), 0.12, 0.12, yel_d, caps=False)

            if k < levels:
                p = (ax, y, az) if k % 2 == 0 else (bx, y, bz)
                q = (bx, y + step, bz) if k % 2 == 0 else (ax, y + step, az)
                m.beam(p, q, 0.11, 0.11, yel, caps=False)

    for y in (14.5, 28.4):
        for x in (-half, half):
            for z in (-half, half):
                m.box((x - 0.21, y - 0.22, z - 0.21), (x + 0.21, y + 0.22, z + 0.21), c("stl_dd"), bevel=0.05)

        m.box((-0.95, y + 0.1, -0.95), (0.15, y + 0.18, 0.95), c("stl_d"))

    for x in (0.55, 1.0):
        m.beam((x, 1.1, 0.0), (x, 42.4, 0.0), 0.06, 0.06, c("stl_l"), caps=False)

    for k in range(46):
        y = 1.6 + k * 0.9
        m.beam((0.55, y, 0.0), (1.0, y, 0.0), 0.04, 0.04, c("stl_l"), caps=False)

    m.box((-1.55, 42.4, -1.55), (1.55, 42.8, 1.55), yel_d, bevel=0.12)
    m.cyl((0, 42.75, 0), (0, 43.3, 0), 1.35, c("stl_dd"), seg=12, chamfer=0.1, caps="")
    m.box((-1.75, 43.25, -1.3), (10.55, 43.7, 1.3), yel, bevel=0.12)
    m.box((1.8, 43.15, -1.15), (9.9, 43.26, 1.15), c("stl_dd"), skip="+y")

    for s in (-1, 1):
        z = s * 1.24

        for x in (-0.2, 1.4, 2.9, 7.7, 9.2, 10.45):
            m.beam((x, 43.7, z), (x, 44.75, z), 0.08, 0.08, c("stl_d"), caps="b")

        for a, b in ((-0.2, 2.9), (7.7, 10.45)):
            for y in (44.2, 44.72):
                m.beam((a, y, z), (b, y, z), 0.06, 0.06, c("stl_d"))

    m.box((3.2, 43.7, -1.18), (7.4, 45.95, 1.18), c("wht"), bevel=0.2, skip="-y")
    m.box((3.12, 45.65, -1.22), (7.48, 45.85, 1.22), yel, bevel=0.06)

    for s in (-1, 1):
        louvres(m, 3.65, 5.0, 44.05, 45.3, s * 1.19, s, 5)
        m.box((5.4, 44.0, s * 1.19 - 0.02), (6.9, 45.35, s * 1.19 + 0.02), c("wht_d"))
        m.box((5.6, 44.5, s * 1.21 - 0.02), (6.7, 44.75, s * 1.21 + 0.02), c("blu"))

    for k in range(3):
        x = 7.9 + k * 0.96
        m.box((x, 41.4, -1.45), (x + 0.86, 43.2, 1.45), c("con_d" if k % 2 else "con"), bevel=0.14)
        m.box((x + 0.28, 43.15, -0.5), (x + 0.58, 43.3, 0.5), c("stl_dd"))

    m.box((-1.7, 40.85, 1.35), (0.55, 41.1, 2.8), yel_d, bevel=0.07)
    m.box((-1.6, 41.1, 1.45), (0.45, 41.85, 2.7), yel, bevel=0.08)
    m.box((-1.56, 41.85, 1.49), (0.41, 43.0, 2.66), c("glass"), bevel=0.05, skip="-y,+y")

    for x in (-1.56, -0.62, 0.41):
        for z in (1.49, 2.66):
            m.beam((x, 41.85, z), (x, 43.0, z), 0.09, 0.09, c("wht"), caps=False)

    m.box((-1.72, 42.98, 1.36), (0.57, 43.22, 2.8), c("wht"), bevel=0.09)
    apex = (3.3, 50.8, 0.0)

    for s in (-1, 1):
        m.beam((0.2, 43.65, s * 1.0), (apex[0] - 0.15, apex[1], s * 0.3), 0.28, 0.28, yel, bevel=0.06)
        m.beam((6.7, 45.8, s * 0.95), (apex[0] + 0.2, apex[1] - 0.1, s * 0.3), 0.18, 0.18, yel_d, bevel=0.04)
        m.beam((apex[0], apex[1], s * 0.28), (10.3, 43.75, s * 1.05), 0.08, 0.08, c("stl_dd"), caps=False)

    for t in (0.35, 0.68):
        y = 43.65 + (apex[1] - 43.65) * t
        x = 0.2 + (apex[0] - 0.35) * t
        w = 1.0 - 0.7 * t
        m.beam((x, y, -w), (x, y, w), 0.14, 0.14, yel_d, caps=False)

    m.box((apex[0] - 0.45, apex[1] - 0.2, -0.46), (apex[0] + 0.35, apex[1] + 0.3, 0.46), c("stl_dd"), bevel=0.1)
    base = V((-1.45, 44.0, 0.0))
    tip = V((-39.3, 57.6, 0.0))
    axis = (tip - base).normalized()
    up = V((-axis.y, axis.x, 0.0))

    if up.y < 0:
        up = -up

    count = 15

    def node(t, side):
        p = base.lerp(tip, t)
        taper = min(1.0, t / 0.1, (1 - t) / 0.14)
        taper = 0.28 + 0.72 * max(0.0, taper)

        if side == 0:
            return p + up * (1.35 * taper)

        return p + V((0, 0, side * 0.88 * taper))

    ts = [i / count for i in range(count + 1)]

    for i in range(count):
        a, b = ts[i], ts[i + 1]
        red = i >= count - 2
        main = c("ora") if red else yel

        for side in (-1, 1, 0):
            m.beam(node(a, side), node(b, side), 0.2, 0.2, main, bevel=0.045 if side == 0 else 0.0, caps=False)

        h = (a + b) / 2

        for side in (-1, 1):
            m.beam(node(a, side), node(h, 0), 0.09, 0.09, c("ora_d") if red else yel_d, caps=False)
            m.beam(node(h, 0), node(b, side), 0.09, 0.09, c("ora_d") if red else yel_d, caps=False)

        p, q = (node(a, -1), node(b, 1)) if i % 2 == 0 else (node(a, 1), node(b, -1))
        m.beam(p, q, 0.08, 0.08, yel_d, caps=False)

    for s in (-1, 1):
        m.beam((-1.45, 43.65, s * 0.9), (base.x - 0.1, base.y + 0.1, s * 0.25), 0.34, 0.34, c("stl_dd"), bevel=0.07)
        m.beam((apex[0] - 0.1, apex[1], s * 0.2), node(0.8, 0) + V((0, 0, s * 0.12)), 0.07, 0.07, c("stl_dd"), caps=False)

    head = tip + axis * 0.25
    m.cyl((head.x, head.y, -0.34), (head.x, head.y, 0.34), 0.55, c("stl_dd"), seg=10, chamfer=0.08)
    m.cyl((head.x, head.y, -0.42), (head.x, head.y, 0.42), 0.16, yel_l, seg=8)
    hx = head.x - 0.52
    m.beam((hx, head.y, 0.0), (hx, 35.4, 0.0), 0.07, 0.07, c("rubber"), caps=False)
    m.box((hx - 0.42, 34.2, -0.28), (hx + 0.42, 35.5, 0.28), yel, bevel=0.2)
    m.box((hx - 0.44, 34.65, -0.3), (hx + 0.44, 34.95, 0.3), c("dark"), bevel=0.05)
    pts = [(hx, 34.25), (hx, 33.6), (hx - 0.36, 33.25), (hx - 0.18, 32.9), (hx + 0.22, 33.0), (hx + 0.32, 33.36)]

    for a, b in zip(pts, pts[1:]):
        m.beam((a[0], a[1], 0), (b[0], b[1], 0), 0.17, 0.17, c("stl_dd"), bevel=0.04)

    m.beam((apex[0] - 0.3, apex[1] + 0.2, 0.0), (head.x + 0.2, head.y + 0.55, 0.0), 0.05, 0.05, c("rubber"), caps=False)

    return m, {"reach": 1.4, "strength": 0.55, "grime": 0.5, "rays": 14, "low": 0.55}


def window_panel(m, x0, x1, y0, y1, z, s, bars=True):
    out = "-z" if s > 0 else "+z"
    m.box((x0, y0, z - 0.04), (x1, y1, z + 0.04), c("wht"), skip=out)
    m.box((x0 + 0.08, y0 + 0.08, z + s * 0.036 - 0.008), (x1 - 0.08, y1 - 0.08, z + s * 0.036 + 0.008), c("glass"), skip=out)
    m.face([(x0 + 0.1, y1 - 0.1, z + s * 0.046), (x0 + 0.45, y1 - 0.1, z + s * 0.046), (x0 + 0.1, y1 - 0.55, z + s * 0.046)], c("glass_l"), m_vec(x0, y0, z - s * 4))

    if bars:
        n = int((x1 - x0) / 0.34)

        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            m.beam((x, y0 + 0.06, z + s * 0.062), (x, y1 - 0.06, z + s * 0.062), 0.025, 0.025, c("stl_d"), caps=False)

    m.box((x0 - 0.05, y0 - 0.07, z - 0.07), (x1 + 0.05, y0, z + 0.07), c("blu_d"), skip=out)


def cabin(m, x, y, idx):
    x0, x1, z0, z1 = x - 1.98, x + 1.98, -3.99, 1.99
    wall = c("wht") if idx % 2 == 0 else c("wht_d")
    m.box((x0, y, z0), (x1, y + 0.16, z1), c("stl_dd"), bevel=0.04, skip="-y")
    m.box((x0 + 0.06, y + 0.16, z0 + 0.07), (x1 - 0.06, y + 3.18, z1 - 0.07), wall, skip="-y,+y")
    m.box((x0 + 0.04, y + 0.16, z0 + 0.05), (x1 - 0.04, y + 0.92, z1 - 0.05), c("blu"), bevel=0.025, skip="-y")
    m.box((x0, y + 3.14, z0), (x1, y + 3.39, z1), c("blu_d"), bevel=0.07)

    for cx in (x0, x1 - 0.16):
        for cz in (z0 + 0.01, z1 - 0.17):
            m.box((cx, y + 0.14, cz), (cx + 0.16, y + 3.16, cz + 0.16), c("blu_d"), bevel=0.035, skip="-y,+y")

    for s, z in ((1, z1 - 0.06), (-1, z0 + 0.06)):
        for k in range(1, 5):
            px = x0 + 3.96 * k / 5
            m.box((px - 0.015, y + 0.95, z - 0.012), (px + 0.015, y + 3.12, z + 0.012), c("wht_d"))

    for s in (-1, 1):
        sx = x + s * 1.92

        for k in range(1, 6):
            pz = z0 + 5.98 * k / 6
            m.box((sx - 0.014, y + 0.95, pz - 0.018), (sx + 0.014, y + 3.12, pz + 0.018), c("wht_d"))

    zf = z1 - 0.05
    m.box((x - 0.3, y + 0.16, zf - 0.04), (x + 0.82, y + 2.42, zf + 0.04), c("blu_d"), bevel=0.02, skip="-z")
    m.box((x - 0.22, y + 0.2, zf + 0.02), (x + 0.74, y + 2.34, zf + 0.055), c("blu_l"), bevel=0.012, skip="-z")
    m.box((x + 0.02, y + 1.55, zf + 0.04), (x + 0.5, y + 2.05, zf + 0.07), c("glass"), skip="-z")
    m.box((x + 0.55, y + 1.08, zf + 0.05), (x + 0.65, y + 1.24, zf + 0.09), c("stl_dd"))
    window_panel(m, x - 1.66, x - 0.55, y + 1.25, y + 2.38, zf, 1)
    window_panel(m, x + 1.04, x + 1.68, y + 1.45, y + 2.38, zf, 1)

    for wx in (-1.5, 0.3):
        window_panel(m, x + wx, x + wx + 1.15, y + 1.3, y + 2.35, z0 + 0.05, -1, bars=False)

    m.box((x - 0.4, y + 2.55, zf - 0.02), (x + 0.9, y + 2.88, zf + 0.05), c("ora"), bevel=0.015, skip="-z")
    m.box((x - 0.2, y + 2.67, zf + 0.04), (x + 0.7, y + 2.76, zf + 0.062), c("wht"), skip="-z")


def cabins():
    m = Mesh(52)

    for k in range(3):
        cabin(m, k * 4.1, 0.0, k)
        m.solid((k * 4.1 - 2.0, 0.0, -4.0), (k * 4.1 + 2.0, 3.39, 2.0))

    for k in range(2):
        cabin(m, k * 4.1 + 2.05, 3.4, k + 1)
        m.solid((k * 4.1 + 0.05, 3.39, -4.0), (k * 4.1 + 4.05, 6.78, 2.0))

    y = 3.4
    m.box((-2.05, y - 0.14, 2.0), (10.25, y - 0.02, 3.8), c("stl_d"), bevel=0.03)
    m.solid((-2.05, y - 0.14, 2.0), (10.25, y, 3.8))

    for k in range(14):
        x = -2.0 + k * 0.875
        m.box((x, y - 0.02, 2.04), (x + 0.84, y, 3.76), c("stl" if k % 2 else "stl_l"), skip="-y")

    rail_run(m, -2.05, 3.8, 10.25, 3.8, y)
    rail_run(m, 10.25, 2.0, 10.25, 3.8, y)

    for x in (-2.0, 2.0, 6.0, 10.2):
        m.beam((x, 0.0, 3.69), (x, y - 0.14, 3.69), 0.14, 0.14, c("stl_dd"), bevel=0.03, caps=False)
        m.box((x - 0.13, 0.0, 3.56), (x + 0.13, 0.06, 3.82), c("con_d"), skip="-y")
        m.solid((x - 0.07, 0.0, 3.62), (x + 0.07, y - 0.14, 3.76))

    n = 12
    x0 = -2.05 - n * 0.6

    for k in range(n):
        xa = x0 + k * 0.6
        yy = y * (k + 1) / n
        m.box((xa, yy - 0.06, 2.14), (xa + 0.6, yy, 3.68), c("stl" if k % 2 else "stl_l"))
        m.box((xa + 0.5, yy, 2.14), (xa + 0.6, yy + 0.014, 3.68), c("yel"), skip="-y")

    for z in (2.1, 3.73):
        m.beam((x0, 0.05, z), (-2.05, y - 0.15, z), 0.08, 0.3, c("stl_dd"))

    for k in (3, 7, 11):
        xa = x0 + k * 0.6
        yy = y * (k + 1) / n
        m.beam((xa + 0.3, 0.0, 3.73), (xa + 0.3, yy - 0.2, 3.73), 0.09, 0.09, c("stl_dd"), caps=False)

    m.ramp((x0, 0.0, 2.05), (-2.05, y, 3.75), "px")

    for k in (0, 4, 8, 12):
        xa = x0 + k * 0.6
        yy = y * k / n
        m.beam((xa, max(0.0, yy - 0.1), 3.82), (xa, yy + 1.12, 3.82), 0.07, 0.07, c("yel_d"), caps="b")

    m.beam((x0, 1.09, 3.82), (-2.05, y + 1.09, 3.82), 0.07, 0.07, c("yel"))
    m.solid((x0, 0.0, 3.8), (-2.05, y + 1.1, 3.9))

    return m, {"reach": 1.6, "strength": 0.65, "grime": 0.7}


def frame():
    m = Mesh(53)
    H = 3.6
    nx, nz = 5, 3
    lift_a = (0, 0)
    lift_b = (4, 0)
    open_top = {(0, 2), (2, 1), (4, 2), (1, 0)}
    beams = set()
    braces = []

    for li in range(2):
        for i in range(nx):
            for j in range(nz):
                if li == 1 and (i, j) in ((4, 2), (0, 2)):
                    continue

                for seg in (((i, j), (i + 1, j)), ((i, j + 1), (i + 1, j + 1)), ((i, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1))):
                    beams.add((li, seg))

                if (i + j + li) % 4 == 1 and (j == 0 or j == nz - 1):
                    braces.append((li, i, j))

    def P(i, j):
        return i * 4.0 - 2.0, j * 4.0 - 2.0

    for li, (a, b) in sorted(beams):
        y = (li + 1) * H - 0.22
        ax, az = P(*a)
        bx, bz = P(*b)
        dx = 0.12 if ax != bx else 0.0
        dz = 0.12 if az != bz else 0.0
        ibeam(m, (ax + dx, y, az + dz), (bx - dx, y, bz - dz), 0.24, 0.22, c("ox_l" if a[1] == b[1] else "ox"), caps=False)

    for li, i, j in braces:
        x, z = P(i, j)

        if j:
            z += 4.0

        y = (li + 1) * H
        lo, hi = li * H + 0.1, y - 0.38
        a, b = (x + 0.15, x + 3.85) if (i + li) % 2 == 0 else (x + 3.85, x + 0.15)
        m.beam((a, lo, z), (b, hi, z), 0.1, 0.1, c("yel"), bevel=0.022)

        for px, py in ((a, lo + 0.1), (b, hi - 0.1)):
            m.box((px - 0.17, py - 0.17, z - 0.07), (px + 0.17, py + 0.17, z + 0.07), c("yel_d"), bevel=0.02)

    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = P(i, j)
            top = H if (i, j) in ((5, 3), (0, 3)) else 2 * H
            ibeam(m, (x, 0.06, z), (x, top - 0.1, z), 0.28, 0.26, c("ox_d"), up=(0, 0, 1), caps=False)
            m.box((x - 0.15, top - 0.1, z - 0.14), (x + 0.15, top - 0.004, z + 0.14), c("ox"), skip="-y")
            m.box((x - 0.3, 0.0, z - 0.3), (x + 0.3, 0.07, z + 0.3), c("con_d"), skip="-y")

            for d in (-0.21, 0.21):
                m.disc((x + d, 0.072, z + d), (0, 1, 0), 0.045, c("stl_dd"))

            if top > H:
                m.box((x - 0.17, H - 0.4, z - 0.16), (x + 0.17, H - 0.06, z + 0.16), c("stl_d"), bevel=0.02)

            m.solid((x - 0.14, 0.0, z - 0.14), (x + 0.14, top, z + 0.14))

    for li in (1, 2):
        y = li * H

        for i in range(nx):
            for j in range(nz):
                if li == 1 and (i, j) == lift_a:
                    continue

                if li == 2 and ((i, j) in open_top or (i, j) == lift_b):
                    continue

                if li == 2 and (i, j) in ((4, 2), (0, 2)):
                    continue

                x, z = P(i, j)
                m.box((x + 0.02, y - 0.1, z + 0.02), (x + 3.98, y - 0.025, z + 3.98), c("stl_d"), skip="+y")
                m.face([(x + 0.02, y - 0.025, z + 0.02), (x + 3.98, y - 0.025, z + 0.02), (x + 3.98, y - 0.025, z + 3.98), (x + 0.02, y - 0.025, z + 3.98)], c("stl"), m_vec(x, -9, z))

                for r in range(4):
                    m.box((x + r * 0.98 + 0.2, y - 0.025, z + 0.08), (x + r * 0.98 + 0.75, y, z + 3.92), m.shade(c("stl_l"), 0.05), skip="-y,-z,+z")

                m.solid((x, y - 0.12, z), (x + 4.0, y, z + 4.0))

    def flight(cell, y0, rise):
        x, z = P(*cell)
        n = 12

        for k in range(n):
            xa = x + 0.2 + k * 0.3 if rise == "px" else x + 3.8 - (k + 1) * 0.3
            yy = y0 + H * (k + 1) / n
            m.box((xa, yy - 0.08, z + 0.36), (xa + 0.3, yy, z + 1.74), c("stl" if k % 2 else "stl_l"))

        lo, hi = (y0, y0 + H) if rise == "px" else (y0 + H, y0)

        for dz in (0.31, 1.79):
            m.beam((x + 0.2, lo + 0.02, z + dz), (x + 3.8, hi - 0.1, z + dz), 0.09, 0.3, c("ox_d"))

        m.ramp((x + 0.2, y0, z + 0.3), (x + 3.8, y0 + H, z + 1.8), rise)

        for k in range(4):
            t = k / 3
            px = x + 0.2 + 3.6 * t
            py = lo + (hi - lo) * t
            m.beam((px, py - 0.05, z + 1.88), (px, py + 1.03, z + 1.88), 0.06, 0.06, c("yel_d"), caps="b")

        m.beam((x + 0.2, lo + 1.0, z + 1.88), (x + 3.8, hi + 1.0, z + 1.88), 0.06, 0.06, c("yel"))

        if y0 > 0:
            m.box((x + 0.2, y0 - 0.12, z + 0.3), (x + 3.8, y0 - 0.085, z + 1.8), c("stl_d"))

    flight(lift_a, 0.0, "px")
    flight(lift_b, H, "nx")

    for li in (1, 2):
        y = li * H

        for i in range(nx):
            if not (li == 1 and i == 0):
                rail_run(m, i * 4.0 - 2.0, -2.05, i * 4.0 + 2.0, -2.05, y)

            if li == 1 or i not in (0, 4):
                rail_run(m, i * 4.0 - 2.0, nz * 4.0 - 1.95, i * 4.0 + 2.0, nz * 4.0 - 1.95, y)

        for j in range(nz):
            if not (li == 1 and j == 0) and not (li == 2 and j == 2):
                rail_run(m, -2.05, j * 4.0 - 2.0, -2.05, j * 4.0 + 2.0, y)

            if not (li == 2 and j == 2):
                rail_run(m, nx * 4.0 - 1.95, j * 4.0 - 2.0, nx * 4.0 - 1.95, j * 4.0 + 2.0, y)

    for k in range(6):
        x = 1.0 + k * 0.5
        ibeam(m, (x + 0.2, H + 0.12, 7.0), (x + 0.2, H + 0.12, 9.0), 0.24, 0.3, c("ox_l" if k % 2 else "stl"))

    return m, {"reach": 1.6, "strength": 0.65, "grime": 0.6, "rays": 16}


def pilewall():
    m = Mesh(54)
    L = 8.0
    n = 13
    step = L / n

    for i in range(n):
        x = -L / 2 + step * i
        pts = [(x, -0.12), (x + step * 0.32, -0.12), (x + step * 0.5, 0.2), (x + step * 0.82, 0.2), (x + step, -0.12)]
        tint = m.rng.uniform(0.93, 1.06)

        for y0, y1, col in ((-7.2, -4.6, "ox_d"), (-4.6, -2.0, "stl_d"), (-2.0, 0.4, "stl")):
            for k, tone in enumerate((1.0, 1.12, 1.04, 0.82)):
                (ax, az), (bx, bz) = pts[k], pts[k + 1]
                m.face([(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)], mul(c(col), tone * tint), m_vec((ax + bx) / 2, (y0 + y1) / 2, -3))

        m.box((x + step * 0.54, 0.4, 0.14), (x + step * 0.78, 0.46, 0.2), c("stl_dd"), skip="-y")

    m.face([(-L / 2, -7.2, -0.12), (L / 2, -7.2, -0.12), (L / 2, 0.4, -0.12), (-L / 2, 0.4, -0.12)], c("stl_d"), m_vec(0, -3, 3))
    m.box((-L / 2, 0.36, -0.12), (L / 2, 0.48, 0.1), c("con_d"), bevel=0.03, skip="-x,+x")

    for y in (-1.2, -3.6, -6.0):
        ibeam(m, (-L / 2, y + 0.2, 0.4), (L / 2, y + 0.2, 0.4), 0.4, 0.3, c("yel"), caps=False)

        for x in (-3.2, -0.6, 2.0, 3.5):
            m.extrude([(0.2, y - 0.28), (0.5, y), (0.2, y)], x - 0.06, x + 0.06, c("stl_dd"), axis="x")
            m.box((x - 0.2, y + 0.06, 0.53), (x + 0.2, y + 0.34, 0.6), c("yel_d"), bevel=0.015, skip="-z")

    for x in (-2.6, 1.4):
        ibeam(m, (x + 0.12, -3.7, 0.65), (x + 0.12, -1.1, 0.65), 0.2, 0.22, c("ox"), up=(0, 0, 1))

    m.solid((-L / 2, -7.2, -0.12), (L / 2, 0.4, 0.3))

    return m, {"reach": 1.0, "strength": 0.6, "floor": -7.2, "grime": 0.0}


def silo():
    m = Mesh(55)
    body = c("wht")

    for x in (-1.26, 1.26):
        for z in (-1.26, 1.26):
            m.beam((x, 0.12, z), (x, 5.0, z), 0.26, 0.26, c("stl_d"), bevel=0.06, caps=False)
            m.box((x - 0.34, 0.0, z - 0.34), (x + 0.34, 0.16, z + 0.34), c("con_d"), bevel=0.04, skip="-y")

    ring = [(-1.26, -1.26), (1.26, -1.26), (1.26, 1.26), (-1.26, 1.26)]

    for i in range(4):
        (ax, az), (bx, bz) = ring[i], ring[(i + 1) % 4]

        for y in (1.5, 4.0):
            m.beam((ax, y, az), (bx, y, bz), 0.12, 0.12, c("stl"), caps=False)

        p, q = ((ax, az), (bx, bz)) if i % 2 == 0 else ((bx, bz), (ax, az))
        m.beam((p[0], 1.5, p[1]), (q[0], 4.0, q[1]), 0.1, 0.1, c("stl"), caps=False)

    prof = [(0.28, 2.0), (0.36, 2.12), (0.36, 2.3), (1.55, 4.5), (1.6, 4.62), (1.6, 7.3), (1.63, 7.34), (1.63, 7.62), (1.6, 7.66), (1.6, 10.3), (1.63, 10.34), (1.63, 10.62), (1.6, 10.66), (1.6, 13.35), (1.65, 13.4), (1.65, 13.68), (1.35, 13.82), (0.5, 14.0)]
    cols = [c("stl_dd"), c("stl_dd"), c("wht_d"), c("stl"), body, c("yel_d"), c("yel"), c("yel_d"), mul(body, 0.97), c("yel_d"), c("yel"), c("yel_d"), body, c("stl"), c("stl_d"), c("wht_d"), c("wht_d")]
    m.lathe((0, 0, 0), prof, cols, seg=16)
    m.cyl((0, 13.98, 0), (0, 14.06, 0), 0.5, c("stl"), seg=10, caps="b")
    m.cyl((0, 1.55, 0), (0, 2.05, 0), 0.22, c("yel"), seg=8, chamfer=0.03)

    for k in range(10):
        a = (k + 0.5) * math.tau / 10
        b = (k + 1.5) * math.tau / 10
        p = (math.cos(a) * 1.5, 13.68, math.sin(a) * 1.5)
        q = (math.cos(b) * 1.5, 13.68, math.sin(b) * 1.5)
        m.beam(p, (p[0], 14.3, p[2]), 0.06, 0.06, c("yel_d"), caps="b")
        m.beam((p[0], 14.27, p[2]), (q[0], 14.27, q[2]), 0.05, 0.05, c("yel"), caps=False)

    for x in (-0.27, 0.27):
        m.beam((x, 0.35, 1.72), (x, 14.3, 1.72), 0.06, 0.06, c("stl_d"), caps="b")

    for k in range(26):
        y = 0.6 + k * 0.52
        m.beam((-0.27, y, 1.72), (0.27, y, 1.72), 0.035, 0.035, c("stl_l"), caps=False)

    for y in (4.9, 9.0, 13.1):
        for x in (-0.27, 0.27):
            m.beam((x, y, 1.55), (x, y, 1.72), 0.05, 0.05, c("stl_d"), caps=False)

    m.cyl((1.1, 0.12, -0.9), (1.1, 13.6, -1.28), 0.09, c("stl_l"), seg=6, caps="")
    m.box((-0.55, 6.0, -1.65), (0.55, 6.9, -1.57), c("blu"), bevel=0.02)
    m.box((-0.4, 6.55, -1.668), (0.4, 6.7, -1.64), body)
    m.box((-0.4, 6.28, -1.668), (0.15, 6.39, -1.64), body)

    return m, {"reach": 1.5, "strength": 0.55}


ALL = {
    "tower": tower_main,
    "tower2": tower_small,
    "crane": crane,
    "cabins": cabins,
    "frame": frame,
    "pilewall": pilewall,
    "silo": silo,
}
