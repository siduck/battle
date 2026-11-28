import math
import random

from mathutils import Vector

import ak
from ak import Part, box, cyl, tube, extrude, prism, ngon, torus, blob, hash01, shade
from kit import *

V = Vector


def pick(seq, *key):
    return seq[int(hash01(*key) * len(seq) * 0.999)]


def logs():
    out = []
    r = 0.165

    for y in (-0.5, 0.5):
        out.append(log((-1.0, y, 0.09), (1.0, y, 0.09), 0.09, "wood_k", "end_d", sides=6))

    rows = ((6, 0.3), (5, 0.585), (4, 0.87))

    for j, (n, z) in enumerate(rows):
        for i in range(n):
            x = (i - (n - 1) / 2) * r * 1.93
            a = -0.72 + 0.05 * hash01(j, i)
            b = 0.72 - 0.05 * hash01(j, i, 3)
            col = pick(("bark", "bark_d", "wood_d"), j, i, 5)
            out.append(log((x, a, z), (x, b, z), r, col, pick(("end", "end_d", "wood_l"), j, i), sides=(8, 6, 4)[ak.LOD], phase=hash01(j, i, 8)))

            if ak.LOD == 0:
                out.append(tube([(x, a - 0.008, z), (x, a - 0.014, z)], [r * 0.45, r * 0.45], 6, "end_d", caps=(False, True), smooth=False))

    top = 1.0
    out.append(pad(-0.52, -0.7, 0.52, 0.7, top, 0.15, seed=3, bevel=0.17, jit=0.05))

    for s in (-1, 1):
        for x, z in ((0.7, 0.74), (0.94, 0.45)):
            out.append(pad(s * x - 0.11, -0.66, s * x + 0.11, 0.66, z, 0.07, seed=int(x * 9) + s, d=1))

    return out


def cordwood():
    out = []

    for x in (-0.93, 0.93):
        for y in (-0.2, 0.2):
            out.append(box(x - 0.055, y - 0.05, 0.0, x + 0.055, y + 0.05, 1.04 if y > 0 else 0.92, "wood_k", c=0.02, skip="d"))

        out.append(box(x - 0.04, -0.2, 0.52, x + 0.04, 0.2, 0.6, "wood_d", d=0))

    for y in (-0.15, 0.15):
        out.append(box(-0.98, y - 0.05, 0.02, 0.98, y + 0.05, 0.11, "wood_k", d=1))

    if ak.LOD == 0:
        for j in range(4):
            z = 0.21 + j * 0.18

            for i in range(8 if j % 2 else 9):
                x = -0.78 + i * 0.195 + (0.0975 if j % 2 else 0.0)
                r = 0.105 + 0.012 * hash01(i, j)
                a = -0.215 - 0.025 * hash01(i, j, 2)
                end = pick(("split", "split_l", "end_d", "split"), i, j, 7)
                out.append(log((x, a, z), (x, 0.2, z), r, pick(("wood_d", "bark", "wood"), i, j), end, sides=5, phase=hash01(i, j, 9) * 6))
    else:
        out.append(box(-0.87, -0.2, 0.11, 0.87, 0.2, 0.86, "wood", c=0.0))

        for j in range(3):
            z = 0.13 + j * 0.245

            for i in range(5 if ak.LOD == 1 else 3):
                w = 1.74 / (5 if ak.LOD == 1 else 3)
                x = -0.87 + i * w
                out.append(poly([(x + 0.02, -0.215, z), (x + w - 0.02, -0.215, z), (x + w - 0.02, -0.215, z + 0.22), (x + 0.02, -0.215, z + 0.22)], pick(("split", "split_l", "end_d"), i, j), out=(0, -1, 0)))

    out.append(pad(-0.88, -0.22, 0.88, 0.22, 0.9, 0.09, seed=5, d=1))

    return out


def fence():
    out = []
    lean = lambda z: -0.02 + z * 0.24

    for x in (-0.93, 0.93):
        out.append(beam((x, lean(0.0), 0.0), (x, lean(1.6), 1.6), 0.12, 0.12, "steel", c=0.025))
        out.append(box(x - 0.08, lean(1.58) - 0.08, 1.56, x + 0.08, lean(1.58) + 0.08, 1.66, "snow", c=0.03, d=1))
        out.append(beam((x, lean(1.2), 1.2), (x, 0.66, 0.0), 0.08, 0.08, "wood_k", d=2))

    for i in range(11):
        x = -0.76 + i * 0.152
        h = 1.52 - 0.07 * hash01(i, 4)
        out.append(beam((x, lean(0.12), 0.12), (x, lean(h), h), 0.092, 0.035, "tin" if i % 3 else "tin_d", d=2, up=(0, -1, 0)))

        if ak.LOD == 0 and i % 2 == 0:
            out.append(box(x - 0.045, lean(h) - 0.035, h - 0.01, x + 0.045, lean(h) + 0.035, h + 0.045, "snow", c=0.015, d=0))

    for z in (0.62, 1.14):
        out.append(beam((-0.99, lean(z) - 0.075, z), (0.99, lean(z) - 0.075, z), 0.055, 0.13, "wood", c=0.015))
        out.append(beam((-0.97, lean(z) - 0.08, z + 0.085), (0.97, lean(z) - 0.08, z + 0.085), 0.06, 0.04, "snow", d=0))

    out.append(drift(-0.99, 0.99, 0.04, 0.68, 0.46, seed=4))
    out.append(drift(-0.9, 0.5, 0.1, -0.0, 0.2, seed=9, d=0))

    return out


def net():
    out = [mound((0.0, 0.05, 0.0), 0.98, 0.84, 0.7, seed=6, n=12, jit=0.1)]
    out.append(mound((-0.45, -0.45, 0.0), 0.52, 0.48, 0.42, seed=9, d=1))

    for s in (-1, 1):
        x = s * 0.9
        out.append(tube([(x, 0, 0), (x * 0.99, 0, 2.2)], [0.07, 0.06], (8, 6, 4)[ak.LOD], "steel", caps=(False, True), smooth=False))
        out.append(cyl((x * 0.99, 0, 1.94), 0.09, 0.2, "orange", sides=8, smooth=False, caps=(True, True), d=1))
        out.append(rock((x * 0.99, 0, 2.19), 0.12, 0.12, 0.13, seed=s + 5, tones=("snow", "snow_s", "snow"), cap=False, n=6, d=1))

        for y in (-0.92, 0.92):
            out.append(cable((x * 0.99, 0, 2.02), (s * 0.94, y, 0.06), 0.014, d=0))
            out.append(box(s * 0.94 - 0.05, y - 0.07, 0.0, s * 0.94 + 0.05, y + 0.07, 0.16, "steel_d", c=0.02, d=0))

    sag = lambda x: 2.02 - 0.16 * (1 - (x / 0.9) ** 2)
    n = (6, 3, 2)[ak.LOD]

    for i in range(n):
        a = -0.9 + 1.8 * i / n
        b = -0.9 + 1.8 * (i + 1) / n
        out.append(beam((a, -0.02, sag(a)), (b, -0.02, sag(b)), 0.06, 0.13, "orange", d=2))
        out.append(beam((a, -0.02, sag(a) + 0.09), (b, -0.02, sag(b) + 0.09), 0.07, 0.05, "snow", d=0))

    for k, z in enumerate((0.62, 0.88, 1.14, 1.4, 1.66)):
        if ak.LOD < 2 or k % 2 == 0:
            out.append(poly([(-0.9, -0.006, z), (0.9, -0.006, z), (0.9, -0.006, z + 0.028), (-0.9, -0.006, z + 0.028)], "tin_d", out=(0, -1, 0)))

    for i in range(8):
        x = -0.72 + i * 0.205

        if ak.LOD == 0 or (ak.LOD == 1 and i % 2 == 0):
            out.append(poly([(x - 0.013, -0.002, 0.5), (x + 0.013, -0.002, 0.5), (x + 0.013, -0.002, sag(x)), (x - 0.013, -0.002, sag(x))], "tin_d", out=(0, -1, 0)))

    back = []

    for p in out[-16:]:
        back.append(p.copy().rot(180))

    return out + back


def fort():
    out = []
    courses_n = 3
    r = 1.0
    h = 0.34

    for j in range(courses_n):
        n = 9
        span = math.radians(292)
        start = math.radians(-56)

        for i in range(n):
            a = start + span * (i + (0.5 if j % 2 else 0.0)) / n
            b = a + span / n - 0.025

            if j % 2 and i == n - 1:
                continue

            if j == 2 and i in (0, 7):
                continue

            m = (a + b) / 2
            w = 2 * math.sin((b - a) / 2) * (r + 0.05)
            jit = 0.04 * hash01(i, j)
            col = pick(("snow", "snow_s", "snow", "snow_d"), i, j, 3)

            if ak.LOD == 2 and j:
                continue

            part = box(-w / 2, -0.17, 0.0, w / 2, 0.17, h - 0.015 if ak.LOD < 2 else 0.98, col, c=0.06, top="snow")
            part.rot(math.degrees(m) + 90).move(math.cos(m) * (r * (1.14 if abs(math.cos(m)) > 0.7 else 0.9) + jit), math.sin(m) * (r * 0.9 + jit), j * h)
            out.append(part)

    for i, a in enumerate((20, 62, 118, 160, 200)):
        m = math.radians(a)
        out.append(mound((math.cos(m) * 1.05, math.sin(m) * 0.9, 1.0), 0.24, 0.2, 0.14, seed=i, n=7, d=1))

    for i, (x, y, s) in enumerate(((0.2, -0.75, 0.15), (-0.3, -0.6, 0.11), (1.2, -0.85, 0.2), (-1.18, -0.82, 0.16))):
        out.append(rock((x, y, 0.0), s, s, s * 1.1, seed=i + 4, tones=("snow", "snow_s", "snow_d"), cap=False, n=6, d=1 if i else None))

    return out


def trough():
    out = []

    for y in (-0.62, 0.62):
        out.append(box(-0.33, y - 0.18, 0.0, 0.33, y + 0.18, 0.17, "stone_d", c=0.05))
        out.append(box(-0.28, y - 0.15, 0.17, 0.28, y + 0.15, 0.32, "stone", c=0.05))

    n = (7, 5, 3)[ak.LOD]
    y0, y1 = -0.84, 0.86

    def arc(y, r, i):
        a = math.pi + math.pi * i / n

        return V((math.cos(a) * r, y, 0.62 + math.sin(a) * r * 0.98))

    for i in range(n):
        mid = (arc(0, 1, i) + arc(0, 1, i + 1)) / 2 - V((0, 0, 0.62))
        out.append(poly([arc(y0, 0.33, i), arc(y0, 0.33, i + 1), arc(y1, 0.33, i + 1), arc(y1, 0.33, i)], "wood_d" if i % 2 else "wood", out=mid))

        for y, o in ((y0, -1), (y1, 1)):
            out.append(poly([arc(y, 0.33, i), arc(y, 0.33, i + 1), arc(y, 0.24, i + 1), arc(y, 0.24, i)], "end_d", out=(0, o, 0)))
            out.append(poly([V((0, y, 0.62)), arc(y, 0.24, i), arc(y, 0.24, i + 1)], "end", out=(0, o, 0)))

    for s in (-1, 1):
        out.append(box(s * 0.33 - (0.09 if s > 0 else 0), y0, 0.57, s * 0.33 + (0 if s > 0 else 0.09), y1, 0.66, "wood_l", c=0.02))
        out.append(box(s * 0.345 - 0.02, y0 + 0.2, 0.4, s * 0.345 + 0.02, y0 + 0.28, 0.67, "steel_d", d=0))
        out.append(box(s * 0.345 - 0.02, y1 - 0.28, 0.4, s * 0.345 + 0.02, y1 - 0.2, 0.67, "steel_d", d=0))

    out.append(poly([(-0.25, y0 + 0.04, 0.58), (0.25, y0 + 0.04, 0.58), (0.25, y1 - 0.04, 0.58), (-0.25, y1 - 0.04, 0.58)], "ice_d", out=(0, 0, 1)))
    out.append(poly([(-0.2, -0.5, 0.586), (0.08, -0.62, 0.586), (0.17, -0.1, 0.586), (-0.12, 0.08, 0.586)], "ice", out=(0, 0, 1), d=1))
    out.append(mound((0.0, 0.66, 0.58), 0.34, 0.33, 0.33, seed=3, n=9))
    out.append(pad(-0.33, -0.84, -0.22, 0.3, 0.65, 0.07, seed=4, d=1))
    out.append(box(-0.065, -0.98, 0.0, 0.065, -0.85, 0.84, "wood_k", c=0.02, skip="d"))
    out.append(cable((0, -0.9, 0.74), (0, -0.68, 0.74), 0.035, "steel_d", sides=5))
    out.append(tube([(0, -0.7, 0.75), (0, -0.68, 0.58)], [0.03, 0.045], 5, "ice", caps=(False, False), smooth=False, d=1))
    out.append(pad(-0.09, -1.0, 0.09, -0.83, 0.83, 0.07, d=1))

    return out


def drum():
    out = []

    for x in (-0.38, 0.38):
        for y in (-0.42, 0.42):
            out.append(box(x - 0.075, y - 0.07, 0.0, x + 0.075, y + 0.07, 0.44 if y < 0 else 0.5, "wood", c=0.025, skip="d"))
            out.append(pad(x - 0.085, y - 0.085, x + 0.085, y + 0.075, 0.43 if y < 0 else 0.49, 0.07, d=0, seed=int(x * 9 + y * 3)))

        out.append(box(x - 0.06, -0.42, 0.2, x + 0.06, 0.42, 0.31, "wood_d", c=0.02))

    out.append(beam((-0.38, 0.4, 0.12), (0.38, 0.4, 0.12), 0.07, 0.09, "wood_d", d=1))
    n = (12, 8, 6)[ak.LOD]
    z = 0.6
    out.append(tube([(-0.47, 0, z), (0.47, 0, z)], [0.33, 0.33], n, "green", caps=("green_d", "green_d"), smooth=False, phase=math.pi / 12))

    for x in (-0.45, -0.17, 0.17, 0.45):
        out.append(tube([(x - 0.028, 0, z), (x + 0.028, 0, z)], [0.355, 0.355], n, "green_d", caps=(True, True), smooth=False, phase=math.pi / 12, d=1))

    out.append(tube([(0.47, 0, z), (0.5, 0, z)], [0.11, 0.1], 8, "green", caps=(False, True), smooth=False, d=0))
    out.append(cyl((0.05, 0.0, 0.9), 0.065, 0.13, "steel", sides=8, smooth=False, caps=(False, True), d=1))
    out.append(box(0.0, -0.045, 0.98, 0.1, 0.045, 1.08, "steel_d", c=0.02, d=1))
    out.append(tube([(0.05, 0, 1.06), (0.28, -0.12, 1.08), (0.44, -0.3, 0.9), (0.46, -0.37, 0.45)], [0.022] * 4, 5, "black", caps=(False, True), smooth=False, d=1))
    out.append(box(0.42, -0.4, 0.34, 0.5, -0.34, 0.47, "steel", d=0))
    out.append(box(-0.22, -0.5, 0.0, 0.22, -0.2, 0.07, "steel_d", c=0.02))
    out.append(mound((-0.25, 0.0, 0.86), 0.24, 0.24, 0.19, seed=7, n=8))

    return out


def winch():
    out = []

    for s in (-1, 1):
        out.append(box(-0.58, s * 0.5 - 0.07, 0.07, 0.58, s * 0.5 + 0.07, 0.2, "steel", c=0.03))
        out.append(box(s * 0.5 - 0.07, -0.58, 0.06, s * 0.5 + 0.07, 0.58, 0.18, "steel_d", c=0.03))

        for t in (-1, 1):
            out.append(box(s * 0.5 - 0.11, t * 0.5 - 0.11, 0.0, s * 0.5 + 0.11, t * 0.5 + 0.11, 0.08, "wood_k", c=0.02))
            out.append(cyl((s * 0.51, t * 0.51, 0.18), 0.065, 0.27, "black", sides=(8, 6, 4)[ak.LOD], rt=0.012, smooth=False))

    out.append(box(-0.2, -0.45, 0.17, 0.2, 0.45, 0.25, "steel_d", c=0.02))
    out.append(beam((0.05, 0.05, 0.28), (-0.5, -0.3, 0.7), 0.16, 0.1, "steel", c=0.03))
    out.append(beam((-0.18, -0.09, 0.5), (-0.46, -0.27, 0.72), 0.19, 0.05, "tin", d=1))
    out.append(beam((0.08, 0.1, 0.18), (-0.14, -0.04, 0.42), 0.08, 0.08, "steel_d", d=1))

    for y in (0.12, 0.42):
        out.append(torus((0.26, y, 0.43), 0.15, 0.045, "black", segs=10, sides=5, axis="Y"))

    out.append(tube([(0.26, 0.12, 0.43), (0.26, 0.42, 0.43)], [0.1, 0.1], 8, "steel_l", caps=(True, True), smooth=False))
    out.append(box(0.18, 0.1, 0.18, 0.34, 0.44, 0.34, "steel_d", c=0.02, d=1))
    out.append(box(-0.52, 0.18, 0.2, -0.42, 0.46, 0.56, "steel_d", c=0.02))
    out.append(poly([(-0.526, 0.21, 0.25), (-0.526, 0.43, 0.25), (-0.526, 0.43, 0.51), (-0.526, 0.21, 0.51)], "canvas", out=(-1, 0, 0)))
    out.append(cable((-0.5, -0.3, 0.7), (0.26, 0.2, 0.55), 0.012, d=0))
    out.append(pad(0.1, -0.5, 0.45, -0.2, 0.18, 0.08, d=1, seed=3))

    return out


def exploder():
    out = [box(-0.98, -1.1, 0.0, 0.98, 1.36, 0.2, "steel_d", c=0.05, top="steel")]

    for s in (-1, 1):
        out.append(box(s * 0.82 - 0.14, -1.06, 0.2, s * 0.82 + 0.14, 1.3, 0.3, "steel_d", c=0.03, d=1))

        for y in (-0.75, 0.95):
            out.append(beam((s * 0.74, y, 0.22), (s * 0.3, -0.28 + y * 0.18, 2.02), 0.15, 0.15, "steel", c=0.03))

        out.append(beam((s * 0.62, -0.62, 0.72), (s * 0.62, 0.78, 0.72), 0.09, 0.09, "steel_d", d=1))
        out.append(box(s * 0.36 - 0.08, -0.5, 1.88, s * 0.36 + 0.08, 0.02, 2.28, "steel", c=0.03))
        out.append(box(s * 0.62 - 0.16, -0.5, 0.2, s * 0.62 + 0.16, -0.24, 0.34, "canvas_d", c=0.03, d=0))

    out.append(beam((-0.62, -0.62, 0.72), (0.62, -0.62, 0.72), 0.1, 0.1, "steel_d"))
    out.append(beam((-0.5, -0.5, 1.32), (0.5, -0.5, 1.32), 0.09, 0.09, "steel", d=1))
    out.append(box(-0.34, -0.76, 1.02, 0.34, -0.66, 1.5, "canvas", c=0.03))
    out.append(box(-0.26, -0.79, 1.1, 0.26, -0.76, 1.42, "white", d=0))
    a = V((0.0, 0.55, 2.04))
    b = V((0.0, -1.36, 2.62))
    t = (b - a).normalized()
    n = (10, 8, 6)[ak.LOD]
    out.append(tube([a, b], [0.34, 0.31], n, "black", caps=("steel_d", False), smooth=False))

    for u, r in ((0.08, 0.39), (0.42, 0.37), (0.97, 0.43)):
        p = a.lerp(b, u)
        out.append(tube([p - t * 0.07, p + t * 0.07], [r, r], n, "steel" if u > 0.9 else "steel_d", caps=(True, u < 0.9), smooth=False, d=2 if u > 0.9 else 1))

    mouth = a.lerp(b, 0.97) + t * 0.07
    out.append(tube([mouth, mouth + t * 0.004], [0.43, 0.24], n, "steel_l", caps=(False, False), smooth=False))
    out.append(flip(tube([mouth - t * 0.12, mouth + t * 0.004], [0.2, 0.24], n, "black", caps=(False, False), smooth=False)))
    out.append(tube([mouth - t * 0.13, mouth - t * 0.12], [0.21, 0.21], n, "black", caps=(False, True), smooth=False))
    out.append(box(-0.1, -0.12, 2.48, 0.1, 0.18, 2.6, "steel", c=0.03, d=1))
    out.append(mound((0.05, 0.5, 0.18), 0.66, 0.72, 0.75, seed=12, n=11))
    out.append(pad(-0.95, 0.9, -0.35, 1.34, 0.19, 0.12, d=1, seed=2))

    return out


def cannon():
    out = [mound((-2.72, 0.0, 0.0), 1.72, 1.36, 0.46, seed=4, n=14)]
    out.append(box(-3.25, -0.5, 0.22, -2.4, 0.35, 0.52, "stone", c=0.08))
    out.append(box(-3.18, -0.44, 0.5, -2.62, 0.22, 1.06, "tin", c=0.07))
    out.append(box(-3.08, -0.47, 0.62, -2.76, -0.44, 0.94, "black", d=0))
    out.append(pad(-3.2, -0.46, -2.6, 0.24, 1.05, 0.13, d=1, seed=6))
    out.append(cyl((-2.78, 0.0, 0.4), 0.17, 2.3, "steel_d", sides=(10, 7, 5)[ak.LOD], smooth=False, rt=0.12))
    out.append(cyl((-2.78, 0.0, 1.75), 0.17, 0.18, "blue_d", sides=8, smooth=False, caps=(True, True), d=1))
    out.append(box(-3.0, -0.2, 2.55, -2.56, 0.2, 2.74, "steel", c=0.05))
    n = (14, 10, 6)[ak.LOD]
    a = V((-3.45, 0.0, 3.2))
    b = V((-2.0, 0.0, 3.42))
    t = (b - a).normalized()

    for s in (-1, 1):
        out.append(beam((-2.78, s * 0.2, 2.65), (-2.76, s * 0.6, 3.3), 0.14, 0.1, "steel", c=0.025))
        out.append(tube([(-2.76, s * 0.55, 3.3), (-2.76, s * 0.68, 3.3)], [0.13, 0.13], 8, "steel_d", caps=(True, True), smooth=False, d=1))

    out.append(tube([a, b], [0.5, 0.54], n, "tin", caps=(False, False), smooth=False))
    out.append(tube([a, a.lerp(b, 0.26)], [0.55, 0.57], n, "orange", caps=("steel_d", True), smooth=False))
    out.append(tube([a.lerp(b, 0.82), b + t * 0.1], [0.59, 0.62], n, "orange", caps=(True, False), smooth=False))
    out.append(tube([b + t * 0.1, b + t * 0.104], [0.62, 0.46], n, "orange_d", caps=(False, False), smooth=False))
    out.append(flip(tube([b - t * 0.22, b + t * 0.104], [0.4, 0.46], n, "black", caps=(False, False), smooth=False)))
    out.append(tube([b - t * 0.23, b - t * 0.22], [0.41, 0.41], n, "black", caps=(False, True), smooth=False))
    out.append(tube([a - t * 0.14, a], [0.26, 0.4], n, "steel_d", caps=(True, False), smooth=False))

    if ak.LOD < 2:
        for i in range(10):
            q = i * math.pi / 5
            p = b + t * 0.06 + V((0, math.cos(q) * 0.54, math.sin(q) * 0.54))
            out.append(box(p.x - 0.05, p.y - 0.035, p.z - 0.035, p.x + 0.1, p.y + 0.035, p.z + 0.035, "steel_l", d=0))

    out.append(tube([(-3.15, 0.3, 0.45), (-3.5, 0.5, 1.4), (-3.45, 0.2, 2.5), (-3.4, 0.0, 3.0)], [0.04] * 4, 5, "black", caps=(False, False), smooth=False, d=1))
    rnd = random.Random(31)
    count = (30, 18, 8)[ak.LOD]

    for i in range(count):
        u = (i + 0.5) / count
        x = -1.55 + 5.75 * u
        spread = 0.18 + 1.0 * u
        y = rnd.uniform(-spread, spread * 0.72) - 0.1 * u
        z = 3.45 + 0.5 * math.sin(u * 2.4) - 1.75 * u * u + rnd.uniform(-0.28, 0.28) * u
        s = (0.12 + 0.12 * u) * rnd.uniform(0.7, 1.15) * (1.0 if ak.LOD == 0 else 1.25)
        out.append(blob((x, y, min(3.85, z)), (s * 1.35, s, s * 0.55), ("snow_w", "snow", "snow_s"), sub=0, jitter=0.2, seed=i + 90, d=2))

    for p in out[-count:]:
        for f in p:
            f.cast = False
            f.ao = False

    return out


def flood():
    out = [box(-0.64, -0.37, 0.0, 0.6, 0.84, 0.18, "stone", c=0.06), pad(-0.66, -0.4, 0.14, 0.44, 0.15, 0.22, seed=3, d=1)]
    out.append(box(0.05, 0.35, 0.0, 0.58, 0.82, 0.62, "steel", c=0.07))
    out.append(box(0.12, 0.33, 0.18, 0.5, 0.35, 0.48, "steel_d", d=0))
    out.append(pad(0.05, 0.35, 0.58, 0.82, 0.6, 0.13, seed=8, d=1))
    base = V((-0.26, 0.05, 0.2))
    top = V((-0.2, 0.08, 5.3))
    out.append(tube([base, top], [0.15, 0.09], (8, 6, 4)[ak.LOD], "steel", caps=(False, True), smooth=False))

    for u in (0.03, 0.42, 0.8):
        p = base.lerp(top, u)
        out.append(cyl((p.x, p.y, p.z), 0.19 - u * 0.07, 0.12, "steel_d", sides=8, smooth=False, caps=(True, True), d=1))

    out.append(tube([(0.25, 0.4, 0.55), (-0.02, 0.2, 1.1), (-0.07, 0.19, 3.2), (-0.1, 0.18, 5.2)], [0.025] * 4, 4, "black", caps=(False, False), smooth=False, d=1))
    out.append(box(-0.62, -0.06, 5.18, 0.28, 0.2, 5.34, "steel_d", c=0.03))

    for s in (-1, 1):
        out.append(box(s * 0.47 - 0.42, -0.36, 5.3, s * 0.47 + 0.42, 0.14, 5.9, "steel_d", c=0.1))
        out.append(tube([(s * 0.47, -0.36, 5.6), (s * 0.47, -0.42, 5.6)], [0.27, 0.27], (12, 8, 6)[ak.LOD], "steel_l", caps=(False, True), smooth=False))
        out.append(tube([(s * 0.47, -0.425, 5.6), (s * 0.47, -0.43, 5.6)], [0.22, 0.22], (12, 8, 6)[ak.LOD], "ice", caps=(False, True), smooth=False))
        out.append(box(s * 0.47 - 0.36, -0.56, 5.82, s * 0.47 + 0.36, -0.34, 5.88, "black", d=0))

    out.append(pad(-0.9, -0.38, 0.9, 0.16, 5.88, 0.17, seed=5))

    return out


def pylon():
    out = [box(-1.06, -0.98, 0.0, 1.06, 0.98, 0.34, "stone", c=0.1), box(-0.56, -0.56, 0.32, 0.56, 0.56, 0.54, "stone_d", c=0.06)]
    out.append(pad(-1.04, -0.96, -0.2, -0.25, 0.32, 0.16, seed=3, d=1))
    out.append(pad(0.3, 0.2, 1.04, 0.96, 0.32, 0.18, seed=6, d=1))
    n = (10, 7, 5)[ak.LOD]
    out.append(tube([(0, 0, 0.5), (0, 0, 9.1)], [0.36, 0.23], n, "steel", caps=(False, False), smooth=False, phase=math.pi / 10))

    for z, r in ((0.6, 0.43), (3.5, 0.36), (6.4, 0.31)):
        out.append(cyl((0, 0, z), r, 0.14, "steel_d", sides=n, smooth=False, caps=(True, True), d=1))

    for s in (-0.22, 0.22):
        out.append(cable((s, -0.62, 0.6), (s, -0.4, 7.2), 0.03, d=1, sides=4))

    if ak.LOD == 0:
        for i in range(17):
            u = i / 17
            z = 0.85 + i * 0.38
            y = -0.62 + 0.22 * (z - 0.6) / 6.6
            out.append(box(-0.22, y - 0.025, z, 0.22, y + 0.025, z + 0.04, "steel_l", d=0))

            if i % 4 == 0:
                out.append(box(-0.04, y, z, 0.04, -0.28, z + 0.04, "steel_d", d=0))

    out.append(box(-0.76, -0.74, 7.18, 0.76, 0.5, 7.3, "steel_d", c=0.03))
    out.append(rail([(-0.26, -0.7, 7.3), (-0.72, -0.7, 7.3), (-0.72, 0.46, 7.3), (0.72, 0.46, 7.3), (0.72, -0.7, 7.3), (0.26, -0.7, 7.3)], 0.72, "steel_l", post=0.06, step=1.0, d=1))
    out.append(box(-1.94, -0.17, 9.08, 1.94, 0.17, 9.4, "steel", c=0.07))
    out.append(pad(-1.6, -0.16, 1.6, 0.16, 9.38, 0.13, seed=4, d=1))

    for s in (-1, 1):
        out.append(beam((s * 0.24, 0, 8.4), (s * 1.15, 0, 9.12), 0.11, 0.11, "steel_d", d=2))
        out.append(box(s * 1.82 - 0.14, -0.98, 9.22, s * 1.82 + 0.14, 0.98, 9.5, "steel_d", c=0.05))
        out.append(pad(s * 1.82 - 0.13, -0.8, s * 1.82 + 0.13, 0.8, 9.48, 0.14, seed=s + 9, d=1))

        for y in (-0.72, -0.25, 0.25, 0.72):
            out.append(box(s * 1.82 - 0.04, y - 0.05, 8.92, s * 1.82 + 0.04, y + 0.05, 9.24, "steel", d=0))
            out.append(wheel((s * 1.82, y, 8.9), 0.21, "blue", axis="X", segs=9, spokes=0, w=0.16))

        out.append(box(s * 1.82 - 0.06, -0.78, 8.98, s * 1.82 + 0.06, 0.78, 9.06, "steel", d=1))

    out.append(box(-0.18, -0.46, 2.0, 0.18, -0.4, 2.4, "yellow", d=1))

    return out


def rope():
    out = []
    n = (10, 5, 3)[ak.LOD]

    for s in (-1, 1):
        pts = []

        for i in range(n + 1):
            y = -6.0 + 12.0 * i / n
            z = 0.035 + 0.4 * (y / 6.0) ** 2
            pts.append((s * 1.82, y, z))

        out.append(tube(pts, [0.028] * len(pts), 4 if ak.LOD == 0 else 3, "steel_d", caps=(False, False), smooth=False, d=2))

        for y in (-5.2, 5.2):
            z = 0.035 + 0.4 * (y / 6.0) ** 2
            out.append(box(s * 1.82 - 0.045, y - 0.18, z - 0.035, s * 1.82 + 0.045, y + 0.18, z + 0.035, "black", d=1))

    return out


def chair():
    s = (6, 5, 3)[ak.LOD]
    out = [box(-0.15, -0.2, 3.62, 0.15, 0.18, 3.86, "steel", c=0.05), box(-0.11, -0.16, 3.84, 0.11, 0.14, 3.94, "steel_l", c=0.03, d=1)]
    out.append(tube([(0, 0, 3.66), (0, 0.0, 3.2), (0, 0.32, 2.75), (0, 0.52, 2.35), (0, 0.5, 2.0), (0, 0.36, 1.82)], [0.07] * 6, s + 2, "black", caps=(False, True), smooth=False))
    out.append(box(-0.17, 0.26, 1.68, 0.17, 0.5, 1.9, "steel", c=0.04))

    for x in (-0.95, 0.95):
        out.append(tube([(x * 0.18, 0.38, 1.78), (x * 0.82, 0.38, 1.76), (x, 0.36, 1.58), (x, 0.28, 0.98), (x, 0.1, 0.82), (x, -0.34, 0.82)], [0.045] * 6, s, "steel_d", caps=(False, True), smooth=False))
        out.append(tube([(x, 0.24, 1.18), (x, -0.4, 1.2), (x, -0.5, 1.05), (x * 0.86, -0.54, 0.3), (x * 0.72, -0.56, 0.08)], [0.03] * 5, s, "steel_l", caps=(False, False), smooth=False, d=1))

    for i, y in enumerate((-0.34, -0.17, 0.0, 0.17)):
        out.append(box(-0.9, y - 0.07, 0.82, 0.9, y + 0.07, 0.89, "wood_l" if i % 2 else "wood", c=0.02, d=2 if i == 1 else 1))

    out.append(box(-0.9, -0.38, 0.77, 0.9, 0.22, 0.82, "steel_d", d=2))
    out.append(box(-0.86, 0.26, 1.04, 0.86, 0.33, 1.52, "black", c=0.03))
    out.append(box(-0.36, 0.24, 1.14, 0.36, 0.27, 1.42, "white", d=0))
    out.append(pad(-0.8, 0.24, 0.8, 0.36, 1.5, 0.07, d=0))
    out.append(cable((-0.86, -0.54, 0.32), (0.86, -0.54, 0.32), 0.028, "steel_l", d=1, sides=5))

    for x in (-0.55, 0.0, 0.55):
        out.append(cable((x, -0.54, 0.32), (x, -0.56, 0.03), 0.022, "steel", d=0))
        out.append(box(x - 0.16, -0.59, 0.0, x + 0.16, -0.52, 0.05, "black", d=0))

    return out


def octo(w, d, c):
    return [(-w + c, -d), (w - c, -d), (w, -d + c), (w, d - c), (w - c, d), (-w + c, d), (-w, d - c), (-w, -d + c)]


def gondola():
    c = 0.26
    out = [prism(octo(0.64, 0.64, c), 0.04, 0.32, "steel_d", c=0.05, bottom=True)]
    out.append(prism(octo(0.74, 0.74, c), 0.3, 1.22, "canvas_d", c=0.02))
    out.append(prism(octo(0.71, 0.71, c), 1.2, 2.52, "glass"))

    for z, col, w in ((0.34, "wood_d", 0.775), (1.14, "wood_l", 0.785), (2.5, "wood", 0.79)):
        out.append(prism(octo(w, w, c), z, z + 0.14, col, c=0.03, bottom=True, d=2 if z > 1 else 1))

    pts = octo(0.725, 0.725, c)

    for i, (x, y) in enumerate(pts):
        out.append(box(x - 0.045, y - 0.045, 1.22, x + 0.045, y + 0.045, 2.52, "wood_k", d=1))

    for side in "fblr":
        out.append(face(box(-0.025, -0.012, 1.26, 0.025, 0.0, 2.5, "wood_k", d=1), side, 0.722))
        out.append(face(poly([(-0.4, -0.004, 1.34), (-0.1, -0.004, 2.4), (-0.28, -0.004, 2.4), (-0.4, -0.004, 1.98)], "glass_l", d=0, out=(0, -1, 0)), side, 0.718))

        for x in (-0.22, 0.22):
            out.append(face(box(x - 0.17, -0.02, 0.52, x + 0.17, 0.0, 1.08, "canvas", c=0.008, skip="b", d=0), side, 0.742))

    out.append(prism(octo(0.8, 0.8, c), 2.64, 2.9, "tin_d", c=0.1, bottom=True))
    out.append(pad(-0.62, -0.62, 0.62, 0.62, 2.88, 0.2, seed=4, bevel=0.25))
    out.append(box(-0.07, -0.07, 3.0, 0.07, 0.07, 4.34, "steel_d", c=0.025, skip="d"))
    out.append(box(-0.15, -0.13, 4.26, 0.15, 0.09, 4.5, "steel", c=0.05))
    out.append(box(-0.1, -0.1, 4.48, 0.1, 0.06, 4.55, "steel_l", d=1))

    for y in (-0.28, 0.28):
        out.append(box(-0.8, y - 0.06, 0.45, -0.75, y + 0.06, 1.7, "black", c=0.015, d=1))

    return out


def tow():
    out = [box(-0.6, -0.68, 0.0, 0.88, 0.8, 0.64, "stone", c=0.08), box(-0.64, -0.72, 0.56, 0.92, 0.84, 0.72, "stone_l", c=0.04)]
    out.append(box(-0.5, 0.52, 0.7, 0.8, 0.62, 2.4, "wood_d", skip="d"))
    out.append(face(planks(-0.52, 0.82, 0.72, 2.38, ("wood", "wood_d", "wood"), w=0.22, seed=3), "f", -0.52))
    out.append(face(planks(-0.82, 0.52, 0.72, 2.38, ("wood", "wood_d"), w=0.22, seed=4), "b", 0.62))
    out.append(box(0.72, -0.45, 0.7, 0.82, 0.56, 2.4, "wood", skip="d"))
    out.append(face(planks(-0.48, 0.58, 0.72, 2.38, ("wood_d", "wood"), w=0.21, seed=6), "r", 0.82))
    out.append(box(0.83, -0.12, 1.45, 0.87, 0.2, 1.82, "black", d=1))
    out.append(box(0.83, -0.18, 1.36, 0.93, 0.26, 1.44, "wood_l", c=0.015, d=0))

    for x, y in ((-0.52, -0.52), (0.8, -0.52), (-0.52, 0.58), (0.8, 0.58)):
        out.append(box(x - 0.065, y - 0.065, 0.7, x + 0.065, y + 0.065, 2.42, "wood_l", c=0.02, skip="d"))

    e = [(-0.95, -0.82, 2.36), (0.96, -0.82, 2.36), (0.96, 0.78, 2.54), (-0.95, 0.78, 2.54)]
    out.append(loft([[V(p) - V((0, 0, 0.1)) for p in e], [V(p) for p in e]], ["wood_d"], top="shingle"))
    out.append(poly([V(p) - V((0, 0, 0.1)) for p in reversed(e)], "wood_k", out=(0, 0, -1)))
    out.append(slope_snow(e[0], e[1], e[2], e[3], 0.16, seed=11, ridge=False, start=0.03, wave=0.03, cell=0.55))
    out.append(wheel((0.1, -0.12, 1.62), 0.52, "blue", axis="Y", segs=14, spokes=6, w=0.13))
    out.append(box(0.02, -0.04, 1.54, 0.18, 0.54, 1.7, "steel_d", d=1))
    out.append(pad(-0.55, 0.6, 0.88, 0.83, 0.7, 0.2, seed=5, d=1))

    for z in (2.13, 1.11):
        out.append(cable((0.1, -0.12, z), (-0.96, -0.8, z + 0.08), 0.022, d=2 if z > 2 else 1))

    out.append(box(-0.78, -0.62, 1.1, -0.56, -0.46, 1.46, "tin", c=0.03))
    out.append(box(-0.73, -0.65, 1.26, -0.66, -0.62, 1.33, "red", d=0))

    return out


def marker():
    out = [mound((0, 0, 0), 0.5, 0.5, 0.3, seed=2, n=10)]
    n = (8, 6, 4)[ak.LOD]
    out.append(cyl((0, 0, 0.2), 0.065, 0.2, "steel_d", sides=n, smooth=False, caps=(False, True)))
    spans = ((0.38, 1.25, "orange"), (1.25, 1.45, "orange_d"), (1.45, 1.82, "white"), (1.82, 2.1, "orange"))

    for a, b, col in spans:
        out.append(cyl((0, 0, a), 0.042, b - a, col, sides=n, smooth=False, caps=(False, False), d=2))

    out.append(cyl((0, 0, 2.09), 0.055, 0.11, "yellow", sides=n, smooth=False, caps=(True, True)))

    return out


def gate():
    out = [mound((0.0, 0.03, 0.0), 0.93, 0.92, 0.62, seed=14, n=13, jit=0.1)]
    out.append(mound((0.38, -0.45, 0.0), 0.5, 0.5, 0.36, seed=19, d=1))
    n = (8, 6, 4)[ak.LOD]

    for x in (-0.4, 0.4):
        out.append(cyl((x, 0, 0.2), 0.04, 2.7, "steel_l", sides=n, smooth=False, caps=(False, True), d=2))
        out.append(cyl((x, 0, 2.88), 0.055, 0.09, "orange_d", sides=n, smooth=False, caps=(True, True), d=1))
        out.append(cyl((x, 0, 0.55), 0.07, 0.14, "steel_d", sides=n, smooth=False, caps=(False, True), d=1))

    m = 4 if ak.LOD == 0 else 1

    for i in range(m):
        a = -0.4 + 0.8 * i / m
        b = -0.4 + 0.8 * (i + 1) / m
        ya = -0.04 * math.sin(math.pi * i / m)
        yb = -0.04 * math.sin(math.pi * (i + 1) / m)
        sag = lambda x: -0.05 * (1 - (x / 0.4) ** 2)

        for dy, o in ((-0.012, -1), (0.012, 1)):
            out.append(poly([(a, ya + dy, 2.12 + sag(a)), (b, yb + dy, 2.12 + sag(b)), (b, yb + dy, 2.8 + sag(b)), (a, ya + dy, 2.8 + sag(a))], "orange" if i % 2 == 0 else "orange_d", out=(0, o, 0)))

    for dy, o in ((-0.058, -1), (0.058, 1)):
        out.append(poly([(-0.17, -0.04 + dy, 2.28), (0.17, -0.04 + dy, 2.28), (0.17, -0.04 + dy, 2.6), (-0.17, -0.04 + dy, 2.6)], "yellow", d=1, out=(0, o, 0)))

    return out


def arm(z, deg, x0, x1, h, col, t=0.05, snow=True, tip=0.14):
    shape = [(x0, z - h / 2), (x1 - tip, z - h / 2), (x1, z), (x1 - tip, z + h / 2), (x0, z + h / 2)]
    part = extrude(shape, -t / 2, t / 2, col, side=shade(col, 0.82), force=True)

    if ak.LOD == 0:
        part += extrude([(x0 + 0.1, z - h * 0.1), (x1 - tip - 0.05, z - h * 0.1), (x1 - tip - 0.05, z + h * 0.06), (x0 + 0.1, z + h * 0.06)], -t / 2 - 0.008, t / 2 + 0.008, "wood_k" if col in ("white", "wood_l") else "canvas", force=True)

        if snow:
            part += box(x0, -t * 0.7, z + h / 2 - 0.005, x1 - tip, t * 0.7, z + h / 2 + 0.04, "snow", c=0.015)

    return part.rot(deg)


def finger():
    out = [mound((0, 0, 0), 0.52, 0.5, 0.25, seed=5, n=10)]
    out.append(box(-0.08, -0.08, 0.1, 0.08, 0.08, 2.34, "wood", c=0.03, skip="d"))
    out.append(box(-0.11, -0.11, 2.32, 0.11, 0.11, 2.4, "wood_d", c=0.025))
    out.append(pad(-0.11, -0.11, 0.11, 0.11, 2.39, 0.065, d=1))
    out.append(arm(2.16, 162, 0.07, 0.76, 0.2, "white"))
    out.append(arm(1.88, -18, 0.07, 0.76, 0.2, "white"))
    out.append(arm(1.6, -140, 0.07, 0.74, 0.2, "white"))
    out.append(arm(1.38, 42, 0.07, 0.72, 0.18, "white"))
    out.append(box(-0.1, -0.1, 0.95, 0.1, 0.1, 1.07, "blue", c=0.015, d=1))

    return out


def wayfinder():
    out = [mound((0, 0, 0), 0.55, 0.48, 0.24, seed=7, n=10)]
    out.append(box(-0.09, -0.07, 0.1, 0.09, 0.09, 2.54, "wood_d", c=0.03, skip="d"))
    out.append(box(-0.12, -0.1, 0.12, 0.12, 0.12, 0.42, "steel_d", c=0.03))
    out.append(pad(-0.11, -0.1, 0.11, 0.12, 2.53, 0.11, d=1))

    for z, s, w in ((2.3, 1, "wood"), (1.94, -1, "wood_l"), (1.58, 1, "wood")):
        part = arm(z, 0 if s > 0 else 180, -0.44, 0.56, 0.3, w, t=0.07, tip=0.17)
        out.append(part.move(0, -0.11, 0))

    out.append(tube([(0, -0.06, 1.12), (0, -0.12, 1.12)], [0.14, 0.14], (10, 8, 6)[ak.LOD], "blue", caps=(False, True), smooth=False))
    out.append(tube([(0, -0.121, 1.12), (0, -0.126, 1.12)], [0.065, 0.065], 3, "white", caps=(False, True), smooth=False, d=0))

    return out


def mast():
    out = [box(-0.42, -0.42, 0.0, 0.42, 0.42, 0.2, "stone_d", c=0.06), mound((0.0, 0.0, 0.12), 0.46, 0.44, 0.2, seed=4, d=1)]
    corner = [(math.cos(a) * 1.0, math.sin(a) * 1.0) for a in (0.5236, 2.618, 4.712)]

    def leg(i, z):
        a = i * 2 * math.pi / 3 + 0.52
        r = 0.27 - 0.1 * z / 4.2

        return V((math.cos(a) * r, math.sin(a) * r, z))

    for i in range(3):
        out.append(beam(leg(i, 0.15), leg(i, 4.2), 0.05, 0.05, "tin", d=2))

        for k in range(6):
            z = 0.4 + k * 0.62
            j = (i + 1) % 3
            out.append(beam(leg(i, z), leg(j, z), 0.028, 0.028, "tin_d", d=0))
            p, q = (i, j) if k % 2 else (j, i)

            if k < 5:
                out.append(beam(leg(p, z), leg(q, z + 0.62), 0.022, 0.022, "steel", d=0))

        gx, gy = corner[i][0] * 0.99, corner[i][1] * 0.99
        gx = max(-0.96, min(0.96, gx))
        out.append(cable((leg(i, 3.7).x, leg(i, 3.7).y, 3.7), (gx, gy, 0.05), 0.01, d=1))
        out.append(box(gx - 0.05, gy - 0.05, 0.0, gx + 0.05, gy + 0.05, 0.11, "steel_d", d=1))

    for k in range(3):
        out.append(cyl((0, 0, 4.16 + k * 0.11), 0.24 - k * 0.01, 0.075, "white", sides=(10, 7, 5)[ak.LOD], smooth=False, caps=(True, True)))

    out.append(cyl((0, 0, 4.45), 0.03, 0.4, "steel_d", sides=5, smooth=False))

    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.2
        p = V((math.cos(a) * 0.3, math.sin(a) * 0.3, 4.84))
        out.append(beam((0, 0, 4.84), p, 0.025, 0.025, "steel_l", d=1))
        out.append(blob(p, (0.075, 0.075, 0.06), "black", sub=0, jitter=0.0, seed=k, d=1))

    out.append(cable((0.0, 0.0, 4.6), (0.34, -0.16, 4.62), 0.016, "steel_l", d=1))
    out.append(poly([(0.2, -0.1, 4.6), (0.36, -0.17, 4.54), (0.36, -0.17, 4.76), (0.24, -0.12, 4.7)], "orange", d=1, out=(-0.4, -1, 0)))
    out.append(poly([(0.24, -0.11, 4.7), (0.36, -0.16, 4.76), (0.36, -0.16, 4.54), (0.2, -0.09, 4.6)], "orange_d", d=1, out=(0.4, 1, 0)))
    out.append(box(0.22, -0.32, 1.5, 0.66, -0.26, 2.1, "blue_d", c=0.015))
    out.append(box(0.25, -0.33, 1.54, 0.63, -0.318, 2.06, "blue", d=0))
    out.append(cable((0.1, -0.1, 1.8), (0.4, -0.27, 1.8), 0.025, d=1))
    out.append(box(-0.3, -0.3, 0.9, 0.05, -0.1, 1.4, "tin", c=0.04))
    out.append(cyl((-0.68, -0.55, 0.0), 0.03, 1.3, "white", sides=6, smooth=False, caps=(False, True)))

    for z in (0.5, 0.9):
        out.append(cyl((-0.68, -0.55, z), 0.036, 0.18, "black", sides=6, smooth=False, caps=(False, False), d=1))

    out.append(mound((-0.68, -0.55, 0.0), 0.28, 0.26, 0.24, seed=8, n=8, d=1))

    return out


def bench():
    out = []

    for x in (-0.76, 0.76):
        out.append(box(x - 0.13, -0.26, 0.0, x + 0.13, 0.24, 0.42, "stone_d", c=0.06, taper=(0.9, 0.84)))
        out.append(beam((x, 0.18, 0.4), (x, 0.31, 0.98), 0.09, 0.07, "steel_d", c=0.015))

    for i, y in enumerate((-0.25, -0.07, 0.11)):
        out.append(box(-0.99, y - 0.08, 0.42, 0.99, y + 0.08, 0.49, "wood" if i % 2 == 0 else "wood_l", c=0.022))

    for i, z in enumerate((0.58, 0.74, 0.9)):
        y = 0.15 + z * 0.16
        out.append(box(-0.97, y - 0.035, z, 0.97, y + 0.02, z + 0.11, "wood" if i % 2 == 0 else "wood_l", c=0.018))

    out.append(pad(-0.96, -0.34, 0.5, 0.17, 0.485, 0.09, seed=2, bevel=0.09))
    out.append(pad(-0.95, 0.25, 0.95, 0.33, 1.0, 0.04, seed=5, d=1))
    out.append(mound((0.88, 0.05, 0.0), 0.22, 0.28, 0.2, seed=3, n=8, d=1))

    return out


def skirack():
    out = []

    for x in (-0.84, 0.84):
        for y in (-0.45, 0.45):
            out.append(beam((x, y, 0.0), (x, y * 0.12, 1.42), 0.11, 0.11, "wood_gd", c=0.025))

        out.append(box(x - 0.05, -0.28, 0.5, x + 0.05, 0.28, 0.6, "wood_g", d=1))

    out.append(box(-0.99, -0.12, 1.3, 0.99, 0.12, 1.46, "wood_g", c=0.04))
    out.append(pad(-0.97, -0.13, 0.97, 0.13, 1.44, 0.12, seed=3))

    for y in (-0.3, 0.3):
        out.append(box(-0.9, y - 0.04, 0.48, 0.9, y + 0.04, 0.57, "wood_g", c=0.015))
        out.append(box(-0.88, y - 0.035, 0.57, 0.88, y + 0.035, 0.6, "snow", d=0))

    for i in range(8):
        x = -0.66 + i * 0.19

        for s in (-1, 1):
            out.append(box(x - 0.035, s * 0.12, 1.32, x + 0.035, s * 0.27, 1.39, "wood_l", skip="d", d=1))

    out.append(mound((0.82, -0.3, 0.0), 0.18, 0.2, 0.18, seed=6, n=8, d=1))

    return out


def snowboard(x, y, lean, col, trim):
    out = Part()
    outline = [(-0.1, 0.06), (-0.05, 0.0), (0.05, 0.0), (0.1, 0.06), (0.135, 0.2), (0.105, 0.78), (0.135, 1.42), (0.1, 1.55), (0.04, 1.62), (-0.04, 1.62), (-0.1, 1.55), (-0.135, 1.42), (-0.105, 0.78), (-0.135, 0.2)]

    if ak.LOD:
        outline = [(-0.1, 0.0), (0.1, 0.0), (0.13, 1.45), (0.0, 1.62), (-0.13, 1.45)]

    out += extrude(outline, -0.02, 0.02, col, side=trim, force=True)

    for z in (0.44, 1.02):
        out += box(-0.14, -0.065, z, 0.14, -0.02, z + 0.11, "black", c=0.015, d=1)
        out += box(-0.1, -0.09, z + 0.02, 0.04, -0.06, z + 0.09, "steel_d", d=0)

    out += poly([(-0.07, -0.022, 0.66), (0.07, -0.022, 0.78), (0.07, -0.022, 0.9), (-0.07, -0.022, 0.78)], "white", d=0, out=(0, -1, 0))

    return out.rot(lean, "X").move(x, y, 0.18)


def boards_rack():
    out = []

    for x in (-0.92, 0.92):
        out.append(box(x - 0.055, 0.1, 0.06, x + 0.055, 0.22, 2.22, "steel_d", c=0.02, skip="d"))
        out.append(box(x - 0.06, -0.48, 0.0, x + 0.06, 0.45, 0.11, "steel", c=0.025))

    for z in (0.55, 0.85, 1.15, 1.45, 1.75):
        out.append(box(-0.92, 0.14, z, 0.92, 0.2, z + 0.05, "steel", d=1))

    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):
        out.append(box(x - 0.022, 0.18, 0.5, x + 0.022, 0.22, 2.05, "steel_d", d=0))

    out.append(box(-0.99, 0.06, 2.1, 0.99, 0.26, 2.26, "steel_d", c=0.04))
    out.append(pad(-0.96, 0.05, 0.96, 0.28, 2.25, 0.14, seed=6))

    for i in range(6):
        x = -0.72 + i * 0.288
        out.append(box(x - 0.035, -0.18, 2.0, x + 0.035, 0.1, 2.08, "tin", c=0.012, d=1))
        out.append(box(x - 0.032, -0.19, 2.08, x + 0.032, -0.06, 2.12, "snow", d=0))

    out.append(box(-0.95, -0.4, 0.12, 0.95, -0.32, 0.22, "steel", c=0.02))

    for x, col, trim in ((-0.5, "blue", "blue_d"), (0.02, "red", "red_d"), (0.52, "blue_d", "blue")):
        out.append(snowboard(x, -0.24, -11, col, trim))

    out.append(drift(-0.92, 0.92, 0.0, 0.3, 0.14, seed=2, d=1))

    return out


def skis():
    out = []

    for i, (x, lean, col, trim) in enumerate(((-0.48, -3.0, "wood", "wood_l"), (0.02, 5.0, "wood_d", "orange"), (0.5, 2.0, "wood", "yellow"))):
        for s in (-1, 1):
            pair = Part()
            h = 1.72 - 0.06 * hash01(i, 3)
            outline = [(-0.042, 0.0), (0.042, 0.0), (0.036, h * 0.45), (0.048, h - 0.16), (0.012, h), (-0.012, h), (-0.048, h - 0.16), (-0.036, h * 0.45)]

            if ak.LOD:
                outline = [(-0.045, 0.0), (0.045, 0.0), (0.045, h - 0.15), (0.0, h), (-0.045, h - 0.15)]

            pair += extrude(outline, -0.016, 0.016, col, side=trim, force=True)
            pair += box(-0.03, -0.022, h * 0.62, 0.03, -0.015, h * 0.86, trim, d=0)
            pair += box(-0.038, -0.055, h * 0.37, 0.038, -0.014, h * 0.47, "black", c=0.01, d=1)
            pair += box(-0.03, -0.045, h * 0.28, 0.03, -0.014, h * 0.32, "steel", d=0)
            out.append(pair.rot(lean, "Y").move(x + s * 0.052, 0.015, 0.02))

        for s in (-1, 1):
            px = x + s * 0.17
            tip = px + s * 0.04 + math.sin(math.radians(lean)) * 0.9
            out.append(cable((px, -0.08, 0.02), (tip, -0.02, 1.12), 0.013, "steel_l", d=2, sides=4))
            out.append(cable((px + (tip - px) * 0.86, -0.028, 0.96), (tip, -0.02, 1.13), 0.028, "black", d=1, sides=5))
            out.append(tube([(px + 0.003, -0.078, 0.1), (px + 0.005, -0.077, 0.125)], [0.06, 0.06], 6, "black", caps=(True, True), smooth=False, d=1))

        out.append(mound((x, -0.01, 0.0), 0.24, 0.155, 0.08, seed=i + 2, n=8, d=1))

    return out


def flame(x, y, z, r, h, col, seed):
    n = (6, 5, 4)[ak.LOD]
    rings = [ring(r * 0.6, r * 0.6, z, n, seed, 0.1, x, y), ring(r, r, z + h * 0.24, n, seed + 1, 0.2, x, y, 0.4), ring(r * 0.52, r * 0.52, z + h * 0.58, n, seed + 2, 0.22, x + r * 0.25, y, 0.8)]
    part = loft(rings, [col, col], apex=(x - r * 0.15, y - r * 0.1, z + h), top=col, cast=False)

    for f in part:
        f.ao = False

    return part


def firepit():
    out = []
    n = 12

    for i in range(n if ak.LOD < 2 else 8):
        m = n if ak.LOD < 2 else 8
        a = 2 * math.pi * i / m
        w = 2 * math.pi / m * 0.93
        seg = box(-math.sin(w / 2), -0.11, 0.0, math.sin(w / 2), 0.11, 0.2, pick(("stone_l", "stone", "stone_l"), i, 2), c=0.045, top="snow" if i % 3 else "snow_s", taper=(0.94, 0.8))
        out.append(seg.rot(math.degrees(a) + 90).move(math.cos(a) * 0.86, math.sin(a) * 0.86, 0.0))

    out.append(prism(ngon(0.8, (12, 10, 8)[ak.LOD]), 0.0, 0.06, "black"))

    for i in range(11):
        a = i * 0.571 + 0.2
        d = 0.5 if i % 2 else 0.38
        out.append(rock((math.cos(a) * d, math.sin(a) * d, 0.04), 0.14, 0.13, 0.2 + 0.1 * hash01(i, 5), seed=i + 3, tones=("rock_d", "black", "stone_k"), cap=False, n=5, d=None if i % 2 else 1))

    out.append(prism(ngon(0.27, 8), 0.05, 0.14, "red_d", c=0.04, top="orange_d"))

    for i, a in enumerate((0.3, 1.9, 3.6, 5.0)):
        out.append(log((math.cos(a) * 0.46, math.sin(a) * 0.46, 0.12), (math.cos(a) * -0.04, math.sin(a) * -0.04, 0.38), 0.06, "wood_k", "end_d", sides=5))

    out.append(flame(-0.04, -0.03, 0.18, 0.15, 0.88, "flame", 4))
    out.append(flame(0.09, 0.03, 0.18, 0.11, 0.6, "flame_h", 9))
    out.append(flame(-0.1, 0.09, 0.16, 0.09, 0.44, "orange", 14))

    return out


def probe():
    out = [mound((0.0, 0.0, 0.0), 0.58, 0.54, 0.44, seed=22, n=11)]

    for i in range(4 if ak.LOD == 0 else 1):
        z = 0.34 + i * 0.3
        top = z + 0.28 if ak.LOD == 0 else 1.54
        out.append(cyl((-0.06, 0.02, z), 0.017, top - z, "steel_l", sides=5, smooth=False, caps=(False, True), d=2))
        out.append(cyl((-0.06, 0.02, top - 0.02), 0.027, 0.04, "red" if i % 2 == 0 else "steel_d", sides=6, smooth=False, caps=(True, True), d=0))

    out.append(torus((-0.06, 0.02, 1.58), 0.05, 0.018, "black", segs=10, sides=4, axis="Y", d=1))
    blade = extrude([(-0.13, 0.0), (0.13, 0.0), (0.15, 0.22), (0.1, 0.3), (-0.1, 0.3), (-0.15, 0.22)], -0.025, 0.025, "steel_d", force=True)
    shovel = blade
    shovel += cyl((0, 0, 0.28), 0.028, 0.46, "orange", sides=6, smooth=False, caps=(False, False))

    for a, b in (((0, 0, 0.72), (-0.1, 0, 0.88)), ((0, 0, 0.72), (0.1, 0, 0.88)), ((-0.1, 0, 0.88), (0.1, 0, 0.88))):
        shovel += cable(a, b, 0.026, "orange", sides=5)

    out.append(shovel.rot(13, "Y").move(0.22, -0.2, 0.22))

    for i, (x, y, s) in enumerate(((-0.6, -0.35, 0.1), (0.62, -0.28, 0.09), (-0.5, 0.52, 0.08), (0.48, 0.5, 0.11), (0.1, -0.64, 0.07))):
        out.append(rock((x, y, 0.0), s, s * 0.9, s, seed=i + 33, tones=("snow", "snow_s", "snow_d"), cap=False, n=5, d=1 if i % 2 else 0))

    return out


def runner(x, y_back, y_front, rise, w, th, col, z=0.0, curl=1.0):
    pts = [(y_back, z), (y_front + 0.22 * curl, z), (y_front + 0.08 * curl, z + rise * 0.28), (y_front, z + rise * 0.68), (y_front + 0.04 * curl, z + rise)]
    out = Part()

    for a, b in zip(pts, pts[1:]):
        out += beam((x, a[0], a[1] + th / 2), (x, b[0], b[1] + th / 2), w, th, col, ext=th * 0.25)

    return out


def toboggan():
    out = []

    for x in (-0.2, 0.2):
        out.append(runner(x, 0.47, -0.485, 0.27, 0.05, 0.035, "wood_d", curl=0.75))
        out.append(box(x - 0.02, -0.28, 0.025, x + 0.02, -0.22, 0.17, "wood", d=1))
        out.append(box(x - 0.02, 0.28, 0.025, x + 0.02, 0.34, 0.17, "wood", d=1))
        out.append(beam((x, -0.4, 0.2), (x, 0.44, 0.19), 0.04, 0.035, "wood", d=1))

    if ak.LOD == 2:
        out.append(poly([(-0.2, -0.32, 0.2), (0.2, -0.32, 0.2), (0.2, 0.46, 0.2), (-0.2, 0.46, 0.2)], "wood", out=(0, 0, 1)))

        for x in (-0.2, 0.2):
            out.append(poly([(x, -0.45, 0.24), (x, -0.4, 0.0), (x, 0.47, 0.0), (x, 0.47, 0.2)], "wood_d", out=(x, 0, 0)))

    for i, x in enumerate((-0.16, -0.08, 0.0, 0.08, 0.16)):
        out.append(box(x - 0.033, -0.32, 0.17, x + 0.033, 0.46, 0.2, "wood_l" if i % 2 else "wood", c=0.008))

    for y in (-0.44, -0.25, 0.31):
        out.append(beam((-0.21, y, 0.215 if y < -0.3 else 0.205), (0.21, y, 0.215 if y < -0.3 else 0.205), 0.04, 0.025, "wood_d", d=1))

    out.append(tube([(-0.2, -0.45, 0.24), (-0.07, -0.49, 0.1), (0.08, -0.49, 0.09), (0.2, -0.45, 0.24)], [0.009] * 4, 4, "canvas", caps=(False, False), smooth=False, d=0))
    out.append(pad(-0.15, 0.18, 0.12, 0.44, 0.2, 0.06, d=0, seed=4))

    return out


def akja():
    out = []
    shape = [(-0.12, -0.8), (0.12, -0.8), (0.3, -0.58), (0.38, -0.2), (0.39, 0.5), (0.32, 0.84), (0.14, 0.95), (-0.14, 0.95), (-0.32, 0.84), (-0.39, 0.5), (-0.38, -0.2), (-0.3, -0.58)]

    if ak.LOD:
        shape = [(-0.14, -0.8), (0.14, -0.8), (0.39, -0.1), (0.34, 0.9), (-0.34, 0.9), (-0.39, -0.1)]

    def band(k, z, lift=0.1):
        return [V((x * k, y * (k * 0.5 + 0.5), z + (lift * max(0.0, -y - 0.45) / 0.35))) for x, y in shape]

    outer = [band(0.7, 0.08), band(0.98, 0.18), band(1.06, 0.29)]
    lip = "orange"
    out.append(loft(outer, [lip, lip]))
    out.append(loft([band(1.12, 0.285), band(1.12, 0.315), band(0.94, 0.325)], ["orange_d", "orange"]))
    out.append(loft([band(0.94, 0.325), band(0.76, 0.17, 0.08)], ["orange_d"]))
    out.append(pad(-0.3, 0.55, 0.05, 0.8, 0.31, 0.06, d=0, seed=3))
    out.append(poly(band(0.76, 0.17, 0.08), "red_d", out=(0, 0, 1)))
    out.append(poly(list(reversed(band(0.7, 0.08))), "orange_d", out=(0, 0, -1)))

    for y in (-0.22, 0.34):
        out.append(box(-0.41, y - 0.05, 0.315, 0.41, y + 0.05, 0.345, "canvas", d=1))
        out.append(box(0.08, y - 0.065, 0.34, 0.2, y + 0.065, 0.37, "steel_d", d=0))

    out.append(box(-0.22, 0.44, 0.18, 0.22, 0.78, 0.31, "red_d", c=0.05, d=1))

    for x in (-0.3, 0.3):
        out.append(runner(x, 0.88, -0.78, 0.16, 0.05, 0.03, "steel_d"))

        for y in (-0.4, 0.5):
            out.append(box(x * 0.82 - 0.02, y - 0.03, 0.02, x * 0.82 + 0.02, y + 0.03, 0.12, "steel_d", d=1))

        out.append(cable((x * 0.55, -0.74, 0.27), (x * 0.45, -0.99, 0.2), 0.016, "steel_l", d=1, sides=4))

    out.append(cable((-0.135, -0.99, 0.2), (0.135, -0.99, 0.2), 0.022, "orange_d", d=1, sides=5))

    return out


def sled():
    out = []

    for x in (-0.43, 0.43):
        out.append(runner(x, 1.27, -1.27, 0.52, 0.1, 0.07, "wood_d", curl=1.5))
        out.append(box(x - 0.05, 1.18, 0.07, x + 0.05, 1.28, 0.16, "steel_d", d=0))

        for y in (-0.68, 0.1, 0.92):
            out.append(box(x * 0.93 - 0.045, y - 0.05, 0.06, x * 0.93 + 0.045, y + 0.05, 0.25, "wood_k", c=0.015, d=1))

        out.append(box(x * 0.93 - 0.04, -0.92, 0.24, x * 0.93 + 0.04, 1.2, 0.32, "wood", c=0.02))

    for i in range(10):
        y = -0.83 + i * 0.215
        out.append(box(-0.45, y - 0.095, 0.31, 0.45, y + 0.095, 0.36, "wood_l" if i % 2 else "wood", c=0.012, d=1))

    out.append(box(-0.44, -0.9, 0.29, 0.44, 1.16, 0.32, "wood_d", d=2))
    out.append(cable((-0.43, -1.19, 0.5), (0.43, -1.19, 0.5), 0.035, "wood", sides=6))
    out.append(box(-0.38, 0.28, 0.36, 0.38, 0.98, 0.83, "wood", c=0.035))

    for z in (0.44, 0.69):
        out.append(box(-0.395, 0.265, z, 0.395, 0.995, z + 0.07, "wood_d", c=0.012, d=1))

    out.append(pad(-0.37, 0.3, 0.37, 0.96, 0.82, 0.14, seed=3))
    out.append(box(-0.34, -0.58, 0.36, 0.34, 0.18, 0.64, "canvas", c=0.12, top="canvas_d", taper=(0.82, 0.88)))
    out.append(tube([(-0.35, -0.38, 0.7), (0.35, -0.38, 0.7)], [0.11, 0.11], (8, 6, 5)[ak.LOD], "green", caps=("green_d", "green_d"), smooth=False))

    for x in (-0.18, 0.18):
        out.append(box(x - 0.025, -0.52, 0.64, x + 0.025, -0.24, 0.825, "black", d=0))
        out.append(box(x - 0.025, -0.59, 0.36, x + 0.025, 0.19, 0.655, "black", d=0))

    out.append(box(-0.3, -0.84, 0.36, 0.02, -0.62, 0.58, "red", c=0.04, d=1))
    out.append(box(0.1, -0.86, 0.36, 0.34, -0.64, 0.52, "steel", c=0.05, d=1))
    out.append(pad(-0.32, -0.12, 0.3, 0.16, 0.62, 0.08, seed=8, d=1))

    return out


def trailsign():
    out = []

    for x in (-1.1, 1.1):
        out.append(box(x - 0.1, -0.09, 0.0, x + 0.1, 0.09, 2.62, "wood_d", c=0.035, skip="d"))
        out.append(box(x - 0.13, -0.12, 0.0, x + 0.13, 0.12, 0.3, "wood_k", c=0.035))
        out.append(mound((x * 1.02, -0.02, 0.0), 0.24, 0.3, 0.17, seed=int(x * 3) + 9, n=8, d=1))

    out.append(box(-1.02, -0.07, 1.02, 1.02, 0.07, 2.32, "wood", c=0.025))

    for z in (0.96, 2.32):
        out.append(box(-1.04, -0.11, z, 1.04, 0.11, z + 0.11, "wood_l", c=0.025))

    out.append(box(-0.86, -0.095, 1.14, 0.86, -0.07, 2.24, "map", d=2))

    def spot(pts, col, lift=0.0):
        return poly([(x, -0.099 - lift, z) for x, z in pts], col, d=1, out=(0, -1, 0))

    out.append(spot(((-0.74, 1.8), (-0.52, 1.68), (-0.3, 1.82), (-0.38, 2.08), (-0.66, 2.1)), "moss"))
    out.append(spot(((-0.72, 1.24), (-0.4, 1.2), (-0.28, 1.42), (-0.6, 1.5)), "pine_l"))
    out.append(spot(((0.28, 1.26), (0.66, 1.3), (0.74, 1.54), (0.46, 1.64), (0.24, 1.46)), "blue"))
    out.append(spot(((0.36, 1.84), (0.62, 1.78), (0.74, 2.04), (0.46, 2.12)), "moss"))
    path = ((-0.46, 1.34), (-0.12, 1.5), (0.02, 1.74), (-0.14, 1.92), (0.12, 2.1), (0.5, 1.96))

    for a, b in zip(path, path[1:]):
        out.append(beam((a[0], -0.104, a[1]), (b[0], -0.104, b[1]), 0.012, 0.035, "wood_k", d=0, up=(0, 1, 0)))

    for x, z in (path[0], path[-1]):
        out.append(tube([(x, -0.1, z), (x, -0.118, z)], [0.055, 0.055], 8, "red", caps=(False, True), smooth=False, d=0))

    for s in (-1, 1):
        e0, e1 = (-1.27, s * 0.44, 2.6), (1.27, s * 0.44, 2.6)
        r1, r0 = (1.27, 0.0, 2.92), (-1.27, 0.0, 2.92)
        out.append(courses(e0, e1, r1, r0, "wood_gd", "wood_g", n=3, lift=0.04, seed=s + 4, split=0.5))
        out.append(poly([(x, y, z - 0.07) for x, y, z in (e0, r0, r1, e1)], "wood_k", out=(0, 0, -1)))
        out.append(beam((-1.27, s * 0.44, 2.565), (1.27, s * 0.44, 2.565), 0.05, 0.08, "wood_d"))
        out.append(slope_snow((-1.24, s * 0.37, 2.66), (1.24, s * 0.37, 2.66), (1.24, 0, 2.93), (-1.24, 0, 2.93), 0.13, seed=14, start=0.14, cell=0.55))

    for x in (-1.1, 1.1):
        out.append(poly([(x - 0.08, -0.4, 2.55), (x - 0.08, 0.4, 2.55), (x - 0.08, 0.0, 2.86)], "wood", out=(-1, 0, 0)))
        out.append(poly([(x + 0.08, -0.4, 2.55), (x + 0.08, 0.4, 2.55), (x + 0.08, 0.0, 2.86)], "wood", out=(1, 0, 0)))

    out.append(box(-1.12, -0.05, 2.5, 1.12, 0.05, 2.6, "wood_d", d=1))
    out.append(arm(0.7, 0, -0.34, 0.4, 0.18, "wood", t=0.05, snow=False))

    for x in (-0.24, 0.2):
        out.append(cable((x, 0.0, 0.98), (x, 0.0, 0.77), 0.012, "steel_d", d=0))

    return out


def picnic():
    out = []

    for i, y in enumerate((-0.32, -0.16, 0.0, 0.16, 0.32)):
        out.append(box(-1.08, y - 0.072, 0.76, 1.08, y + 0.072, 0.84, "wood" if i % 2 else "wood_r", c=0.022))

    for s in (-1, 1):
        for i, y in enumerate((0.6, 0.78)):
            out.append(box(-1.08, s * y - 0.08, 0.42, 1.08, s * y + 0.08, 0.5, "wood_r" if i else "wood", c=0.022))

        for x in (-0.78, 0.78):
            out.append(beam((x, s * 0.58, 0.0), (x, s * 0.24, 0.77), 0.1, 0.13, "wood_d", c=0.025))

    for x in (-0.78, 0.78):
        out.append(box(x - 0.045, -0.88, 0.32, x + 0.045, 0.88, 0.43, "wood_k", c=0.02))
        out.append(box(x - 0.06, -0.4, 0.68, x + 0.06, 0.4, 0.77, "wood_k", d=1))

    out.append(beam((-0.76, 0.0, 0.38), (0.0, 0.0, 0.72), 0.08, 0.08, "wood_d", d=1))
    out.append(beam((0.76, 0.0, 0.38), (0.0, 0.0, 0.72), 0.08, 0.08, "wood_d", d=1))
    out.append(pad(-0.9, -0.3, -0.05, 0.34, 0.835, 0.075, seed=3))
    out.append(pad(0.45, -0.22, 0.98, 0.26, 0.835, 0.06, seed=7, d=1))
    out.append(pad(-0.4, 0.55, 0.65, 0.86, 0.495, 0.07, seed=9, d=1))
    out.append(pad(-1.0, -0.86, -0.42, -0.56, 0.495, 0.055, seed=12, d=1))

    return out


OPT = dict(errors=(0.008, 0.03), reach=0.8, ao=0.48, grime=0.08, grime_h=0.45, under=0.16)
TALL = dict(OPT, grime_h=0.9, reach=1.0)

ALL = {n: (f, dict(OPT)) for n, f in (("logs", logs), ("cordwood", cordwood), ("fence", fence), ("net", net), ("fort", fort), ("trough", trough), ("drum", drum), ("winch", winch), ("marker", marker), ("gate", gate), ("finger", finger), ("wayfinder", wayfinder), ("bench", bench), ("skirack", skirack), ("boards", boards_rack), ("skis", skis), ("firepit", firepit), ("probe", probe), ("toboggan", toboggan), ("akja", akja), ("sled", sled), ("picnic", picnic))}
ALL.update({n: (f, dict(TALL)) for n, f in (("exploder", exploder), ("cannon", cannon), ("flood", flood), ("pylon", pylon), ("gondola", gondola), ("tow", tow), ("mast", mast), ("trailsign", trailsign))})
ALL.update({n: (f, dict(OPT, ground=False)) for n, f in (("rope", rope), ("chair", chair))})
ALL["pylon"][1]["errors"] = (0.012, 0.07)
