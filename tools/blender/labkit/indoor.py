import math

import lk
from common import *


def cabinet_front(x0, x1, y, kind, z0=0.12, z1=0.84):
    out = part()

    if kind == "drawers":
        n = 4
        step = (z1 - z0) / n

        for i in range(n):
            a = z0 + step * i + 0.008
            b = z0 + step * (i + 1) - 0.008
            out += front(x0 + 0.012, x1 - 0.012, a, b, y, "white", depth=0.018)
            out += handle((x0 + x1) / 2, b - 0.04, (x1 - x0) * 0.46, y - 0.018, "steel_dk")
    elif kind == "glass":
        out += frame(x0 + 0.012, x1 - 0.012, z0 + 0.008, z1 - 0.008, y, 0.05, "white", depth=0.018)
        out += plate(x0 + 0.062, x1 - 0.062, z0 + 0.058, z1 - 0.058, y - 0.005, "glass_dd")
        out += plate(x0 + 0.09, x0 + 0.115, z0 + 0.18, z1 - 0.1, y - 0.007, "glass_dk", d=0)
        out += plate(x0 + 0.062, x1 - 0.062, z0 + 0.34, z0 + 0.36, y - 0.007, "slate_dk", d=0)
        out += handle(x1 - 0.045, (z0 + z1) / 2 + 0.1, 0.16, y - 0.018, "steel_dk", vertical=True)
    else:
        out += front(x0 + 0.012, x1 - 0.012, z0 + 0.008, z1 - 0.008, y, "white", depth=0.018, c=0.008)
        out += handle(x1 - 0.055, z1 - 0.14, 0.14, y - 0.018, "steel_dk", vertical=True)
        out += plate(x0 + 0.07, x1 - 0.07, z0 + 0.07, z0 + 0.082, y - 0.019, "panel_dk", d=0)

    return out


def faucet(x, y, z, toward, col="steel_lt"):
    out = part()
    out += puck((x, y, z), 0.028, 0.035, "steel", sides=6, d=0)
    out += tube([(x, y, z + 0.03), (x, y, z + 0.2), (x, y + toward * 0.05, z + 0.245), (x, y + toward * 0.12, z + 0.225), (x, y + toward * 0.13, z + 0.18)], 0.012, 5, col, caps=(False, True), smooth=False, d=1)
    out += box(x - 0.045, y - 0.009, z + 0.07, x + 0.045, y + 0.009, z + 0.086, "teal", d=0)

    return out


def outlet(x, y, z, sign, col):
    out = part()

    if sign < 0:
        out += box(x - 0.06, y - 0.012, z - 0.032, x + 0.06, y, z + 0.032, "white_dk", skip="b", d=1)
        out += plate(x - 0.035, x + 0.035, z - 0.018, z + 0.018, y - 0.014, col, d=0)
    else:
        out += box(x - 0.06, y, z - 0.032, x + 0.06, y + 0.012, z + 0.032, "white_dk", skip="f", d=1)
        out += plate(x - 0.035, x + 0.035, z - 0.018, z + 0.018, y - 0.014, col, d=0).rot(180, "Z", (x, y, 0))

    return out


def bottle(x, y, z, h, r, col, cap="graphite", sides=6, d=0):
    out = part()

    if lk.LOD:
        out += box(x - r, y - r, z, x + r, y + r, z + h * 0.8, col, skip="d", d=1)

        return out

    out += cyl((x, y, z), r, h * 0.68, col, sides=sides, smooth=False, caps=(False, False))
    out += cyl((x, y, z + h * 0.68), r, h * 0.14, col, sides=sides, rt=r * 0.45, smooth=False, caps=(False, False))
    out += cyl((x, y, z + h * 0.82), r * 0.45, h * 0.18, cap, sides=sides, smooth=False, caps=(False, True))

    return out


def island():
    out = part()
    out += box(-0.54, -0.80, 0.0, -0.22, 0.80, 0.09, "black", skip="d")
    out += box(0.26, -0.80, 0.0, 0.54, 0.80, 0.09, "black", skip="d")
    out += box(-0.59, -0.86, 0.08, -0.20, 0.86, 0.86, "white_dk", c=0.012, skip="t")
    out += box(0.24, -0.86, 0.08, 0.59, 0.86, 0.86, "white_dk", c=0.012, skip="t")
    out += box(-0.20, -0.04, 0.08, 0.24, 0.04, 0.86, "panel_dk", skip="lrdt")
    out += box(-0.20, -0.86, 0.76, 0.24, -0.80, 0.86, "white_dk", skip="lrt")
    out += box(-0.20, 0.80, 0.76, 0.24, 0.86, 0.86, "white_dk", skip="lrt")
    out += cabinet_front(-0.59, -0.21, -0.86, "glass")
    out += cabinet_front(0.25, 0.59, -0.86, "drawers")
    back = cabinet_front(-0.59, -0.21, -0.86, "glass") + cabinet_front(0.25, 0.59, -0.86, "drawers")
    out += mirror_y(back)

    for s, x in ((-1, -0.59), (1, 0.59)):
        for ya, yb in ((-0.80, -0.30), (-0.27, 0.27), (0.30, 0.80)):
            out += side(ya, yb, 0.17, 0.78, x + s * 0.002, s, "panel", d=1)
            out += side(ya + 0.025, yb - 0.025, 0.195, 0.755, x + s * 0.004, s, "white", d=0)
            out += side((ya + yb) / 2 - 0.09, (ya + yb) / 2 + 0.09, 0.69, 0.715, x + s * 0.006, s, "steel_dk", d=0)

        out += side(-0.82, 0.82, 0.80, 0.825, x + s * 0.003, s, "teal", d=1)

    out += box(-0.60, -0.90, 0.845, 0.60, 0.90, 0.93, "graphite_dk", c=0.016, top="graphite")
    out += deck(-0.21, 0.21, -0.62, -0.38, 0.931, "steel_dk", d=1)
    out += deck(-0.18, 0.18, -0.595, -0.405, 0.932, "slate_dk", d=1)
    out += deck(-0.21, 0.21, 0.38, 0.62, 0.931, "steel_dk", d=1)
    out += deck(-0.18, 0.18, 0.405, 0.595, 0.932, "slate_dk", d=1)

    for x in (-0.55, 0.55):
        out += box(x - 0.035, -0.085, 0.93, x + 0.035, 0.085, 1.76, "white_dk", skip="d")
        out += box(x - 0.016, -0.2, 1.44, x + 0.016, 0.2, 1.465, "steel_dk", d=0)
        out += box(x - 0.016, -0.2, 1.68, x + 0.016, 0.2, 1.705, "steel_dk", d=0)

    for z in (1.465, 1.705):
        out += box(-0.6, -0.22, z, 0.6, 0.22, z + 0.028, "white")

        for y in (-0.215, 0.215):
            out += box(-0.6, y - 0.008, z + 0.028, 0.6, y + 0.008, z + 0.062 if z < 1.6 else z + 0.075, "steel_lt", d=1)

    out += box(-0.55, -0.06, 1.19, 0.55, 0.06, 1.32, "panel", skip="lr")

    for x, col in ((-0.25, "red"), (0.0, "blue"), (0.25, "red")):
        out += outlet(x, -0.06, 1.26, -1, col)
        out += outlet(x, 0.06, 1.26, 1, col)

    out += faucet(0.0, -0.22, 0.93, -1)
    out += faucet(0.0, 0.22, 0.93, 1)

    return out


def wallbench():
    out = part()
    out += box(-0.55, -0.27, 0.0, -0.20, 0.33, 0.09, "black", skip="d")
    out += box(0.35, -0.27, 0.0, 0.55, 0.33, 0.09, "black", skip="d")
    out += box(-0.59, -0.31, 0.08, -0.16, 0.34, 0.86, "white_dk", c=0.012, skip="t")
    out += box(0.31, -0.31, 0.08, 0.59, 0.34, 0.86, "white_dk", c=0.012, skip="t")
    out += box(-0.16, 0.28, 0.08, 0.31, 0.34, 0.86, "panel_dk", skip="lrt")
    out += box(-0.16, -0.30, 0.76, 0.31, -0.25, 0.86, "white_dk", skip="lrt")

    for x0, x1 in ((-0.59, -0.16), (0.31, 0.59)):
        out += cabinet_front(x0, x1, -0.31, "door", 0.12, 0.69)
        out += front(x0 + 0.012, x1 - 0.012, 0.705, 0.84, -0.31, "white", depth=0.018, c=0.006)
        out += handle((x0 + x1) / 2, 0.80, (x1 - x0) * 0.45, -0.328, "steel_dk")

    out += box(-0.60, -0.35, 0.845, 0.60, 0.35, 0.93, "graphite_dk", c=0.014, top="graphite")
    out += box(-0.60, 0.24, 0.93, 0.60, 0.35, 1.25, "panel", skip="d")

    for x, col in ((-0.25, "red"), (0.04, "blue"), (0.25, "red")):
        out += outlet(x, 0.24, 1.06, -1, col)

    out += plate(-0.55, 0.55, 1.16, 1.18, 0.238, "panel_dk", d=0)
    out += box(-0.59, 0.31, 1.22, 0.59, 0.35, 1.78, "white_dk")

    for x in (-0.575, 0.575):
        out += box(x - 0.015, 0.07, 1.22, x + 0.015, 0.31, 1.78, "white_dk", skip="b")

    out += box(-0.56, 0.08, 1.22, 0.56, 0.31, 1.25, "white", skip="lrb")
    out += box(-0.56, 0.12, 1.48, 0.56, 0.31, 1.50, "steel", skip="lrb", d=0)
    out += plate(-0.555, 0.555, 1.25, 1.75, 0.305, "glass_dd")
    r = rng(5)

    for z in (1.25, 1.50):
        for x in (-0.45, -0.33, -0.2, 0.12, 0.26, 0.40):
            h = 0.11 + r.random() * 0.05
            out += bottle(x + r.random() * 0.03, 0.20, z, h, 0.035, ("bottle", "white_dk", "teal_lt", "slate_lt")[r.randrange(4)], sides=5)

    out += frame(-0.55, -0.005, 1.25, 1.75, 0.09, 0.035, "white", depth=0.022)
    out += frame(0.005, 0.55, 1.25, 1.75, 0.09, 0.035, "white", depth=0.022)

    for x0, x1 in ((-0.51, -0.30), (0.05, 0.26)):
        out += face([(x0 + 0.03, 0.07, 1.30), (x0 + 0.07, 0.07, 1.30), (x1 - 0.02, 0.07, 1.70), (x1 - 0.06, 0.07, 1.70)], "glass", d=0, ao=False, cast=False, towards=(0, -1, 0))

    out += handle(-0.045, 1.36, 0.12, 0.068, "steel_dk", vertical=True)
    out += handle(0.045, 1.36, 0.12, 0.068, "steel_dk", vertical=True)
    out += box(-0.60, 0.02, 1.78, 0.60, 0.35, 1.86, "white", c=0.022)
    out += deck(0.14, 0.50, -0.2, 0.1, 0.931, "steel_dk", d=1)
    out += deck(0.17, 0.47, -0.17, 0.07, 0.932, "slate_dk", d=1)
    out += faucet(0.40, 0.15, 0.93, -1)

    return out


def desk():
    out = part()
    out += box(-0.90, -0.45, 0.697, 0.90, 0.45, 0.75, "white", c=0.012)
    out += box(-0.90, -0.455, 0.715, 0.90, -0.44, 0.735, "teal_dk", skip="b", d=1)
    out += box(0.845, -0.43, 0.0, 0.89, 0.42, 0.71, "white_dk", c=0.01, skip="dt")
    out += box(-0.40, 0.385, 0.34, 0.85, 0.41, 0.71, "panel_dk", skip="lrt")
    out += box(-0.85, -0.40, 0.0, -0.43, 0.38, 0.05, "black", skip="d")
    out += box(-0.88, -0.42, 0.045, -0.40, 0.42, 0.71, "white_dk", c=0.012, skip="t")

    for a, b in ((0.08, 0.40), (0.42, 0.55), (0.56, 0.69)):
        out += front(-0.862, -0.418, a, b, -0.42, "white", depth=0.015, c=0.005)
        out += box(-0.73, -0.455, b - 0.065, -0.55, -0.435, b - 0.038, "graphite", skip="b", d=1)

    for x in (-0.85, 0.85):
        out += box(x - 0.022, 0.23, 0.75, x + 0.022, 0.44, 1.09, "white_dk", c=0.008, skip="d")

    out += box(-0.83, 0.25, 0.97, 0.83, 0.44, 1.0, "white", c=0.008)
    out += box(-0.19, 0.20, 0.75, 0.03, 0.32, 0.763, "graphite", d=1)
    out += box(-0.105, 0.245, 0.76, -0.055, 0.275, 0.93, "graphite", skip="d", d=1)
    out += box(-0.39, 0.17, 0.87, 0.23, 0.205, 1.26, "graphite_dk", c=0.008)
    out += plate(-0.365, 0.205, 0.90, 1.235, 0.167, "glass_dd")
    out += plate(-0.34, -0.12, 1.13, 1.20, 0.165, "teal", d=0)
    out += plate(-0.34, 0.12, 1.06, 1.085, 0.165, "screen", d=0)
    out += plate(-0.34, 0.02, 1.00, 1.02, 0.165, "glass_dk", d=0)
    out += plate(-0.34, 0.17, 0.945, 0.965, 0.165, "glass_dk", d=0)

    for x0, col in ((-0.76, "red"), (-0.675, "blue")):
        out += box(x0, -0.05, 0.75, x0 + 0.078, 0.23, 1.05, col, c=0.006, skip="d")
        out += plate(x0 + 0.018, x0 + 0.06, 0.93, 0.99, -0.052, "white", d=0)
        out += plate(x0 + 0.025, x0 + 0.053, 0.80, 0.83, -0.052, "graphite", d=0)

    out += box(-0.30, -0.30, 0.75, 0.14, -0.15, 0.775, "graphite_dk", skip="d")

    for i in range(3):
        out += deck(-0.285, 0.125, -0.285 + i * 0.044, -0.255 + i * 0.044, 0.776, "slate", d=0)

    out += box(0.22, -0.29, 0.75, 0.29, -0.18, 0.782, "graphite", c=0.012, skip="d", d=1)
    out += deck(0.07, 0.27, -0.12, 0.12, 0.7515, "slate_dk", d=1)

    for x, h, r in ((0.66, 0.17, 0.048), (0.76, 0.12, 0.036)):
        out += cyl((x, 0.03, 0.75), r, h * 0.35, "teal_lt", sides=6, smooth=False, caps=(False, False), d=1)
        out += cyl((x, 0.03, 0.75 + h * 0.35), r, h * 0.35, "glass_lt", sides=6, rt=r * 0.3, smooth=False, caps=(False, False), d=1)
        out += cyl((x, 0.03, 0.75 + h * 0.7), r * 0.3, h * 0.3, "glass_lt", sides=6, smooth=False, caps=(False, True), d=1)

    out += tube([(-0.0, 0.32, 0.77), (0.02, 0.40, 0.752), (0.18, 0.42, 0.60)], 0.007, 3, "black", caps=(False, False), smooth=False, d=0)

    return out


def jug(x, y, z, w, h, col):
    out = part()
    out += box(x - w / 2, y - 0.085, z, x + w / 2, y + 0.085, z + h * 0.78, col, c=0.028, skip="d")
    out += cyl((x + w * 0.18, y, z + h * 0.76), 0.028, h * 0.2, "graphite", sides=5, smooth=False, caps=(False, True), d=0)
    out += plate(x - w * 0.28, x + w * 0.28, z + h * 0.22, z + h * 0.46, y - 0.087, "teal_lt", d=0)

    return out


def shelf():
    out = part()

    for s in (-1, 1):
        out += box(s * 0.60, -0.30, 0.0, s * 0.545, 0.30, 1.80, "white_dk", c=0.012, skip="d")

        for z in (0.14, 0.54, 0.94, 1.34):
            out += plate(s * 0.582, s * 0.563, z - 0.02, z + 0.02, -0.302, "steel_dk", d=0)

    out += box(-0.55, -0.285, 1.72, 0.55, 0.28, 1.755, "white", skip="lr")
    out += box(-0.55, 0.265, 0.11, 0.55, 0.285, 1.72, "panel_dk", skip="lrtd")

    for z in (0.11, 0.51, 0.91, 1.31):
        out += box(-0.55, -0.25, z + 0.02, 0.55, 0.265, z + 0.052, "panel", skip="lrb")
        out += box(-0.55, -0.265, z, 0.55, -0.245, z + 0.062, "steel_lt", skip="lr", d=1)

    for z, items in ((0.17, ("j", -0.40, -0.13, "j2", 0.40)), (0.57, ("jw", "bx", "br", 0.28)), (0.97, ("bo", "bx2")), (1.37, ("bo", "bx2"))):
        if z == 0.17:
            out += jug(-0.40, -0.12, z, 0.23, 0.27, "panel")
            out += jug(-0.13, -0.12, z, 0.23, 0.27, "white_dk")
            out += jug(0.40, -0.12, z, 0.23, 0.27, "panel")
        elif z == 0.57:
            out += jug(-0.415, -0.12, z, 0.22, 0.27, "white_dk")
            out += box(-0.28, -0.22, z, -0.06, 0.0, z + 0.12, "white", c=0.01, skip="d")
            out += plate(-0.25, -0.09, z + 0.04, z + 0.08, -0.222, "blue", d=0)

            for x in (0.08, 0.25, 0.41):
                out += bottle(x, -0.14, z, 0.26, 0.075, "bottle", sides=6, d=1)
                out += plate(x - 0.04, x + 0.04, z + 0.07, z + 0.13, -0.216, "canvas", d=0)
        else:
            for x in (-0.455, -0.29, -0.125, 0.04):
                if x < -0.35 or x > -0.2:
                    out += bottle(x, -0.14, z, 0.27, 0.075, "bottle" if x < 0 else "bottle_dk", sides=6, d=1)
                    out += plate(x - 0.04, x + 0.04, z + 0.07, z + 0.13, -0.216, "canvas", d=0)
                else:
                    out += bottle(x, -0.10, z, 0.22, 0.065, "bottle_dk", sides=5, d=1)

            out += box(0.20, -0.22, z, 0.50, 0.05, z + 0.15, "white", c=0.012, skip="d")
            out += plate(0.26, 0.44, z + 0.05, z + 0.1, -0.222, "teal", d=0)

    return out


def lockers():
    out = part()
    xs = [(-0.60, -0.30), (-0.30, 0.0), (0.0, 0.30), (0.30, 0.60)]
    out += box(-0.60, -0.15, 0.0, -0.30, 0.40, 1.76, "panel", c=0.012, skip="dt")
    out += box(0.0, -0.15, 0.0, 0.60, 0.40, 1.76, "panel", c=0.012, skip="dt")
    out += box(-0.30, 0.37, 0.0, 0.0, 0.40, 1.76, "slate_dk", skip="lrtdf")
    out += box(-0.30, -0.15, 0.0, -0.28, 0.37, 1.76, "slate", skip="bdt")
    out += box(-0.02, -0.15, 0.0, 0.0, 0.37, 1.76, "slate", skip="bdt")
    out += box(-0.28, -0.15, 0.0, -0.02, 0.37, 0.05, "slate", skip="lrbd")
    out += plate(-0.279, -0.021, 0.05, 1.76, 0.368, "slate_dk")

    for x0, x1 in xs:
        out += face([(x0 + 0.006, -0.17, 1.76), (x1 - 0.006, -0.17, 1.76), (x1 - 0.006, 0.20, 1.97), (x0 + 0.006, 0.20, 1.97)], "white", towards=(0, -1, 1))
        out += deck(x0 + 0.006, x1 - 0.006, 0.20, 0.40, 1.97, "white_dk", cast=True)
        out += face([(x0 + 0.006, -0.17, 1.76), (x0 + 0.006, 0.20, 1.97), (x0 + 0.006, 0.40, 1.97), (x0 + 0.006, 0.40, 1.76)], "panel_dk", cast=True, towards=(-1, 0, 0))
        out += face([(x1 - 0.006, -0.17, 1.76), (x1 - 0.006, 0.20, 1.97), (x1 - 0.006, 0.40, 1.97), (x1 - 0.006, 0.40, 1.76)], "panel_dk", cast=True, towards=(1, 0, 0))
        out += face([(x0, 0.40, 1.76), (x1, 0.40, 1.76), (x1, 0.40, 1.97), (x0, 0.40, 1.97)], "panel_dk", towards=(0, 1, 0))

    out += box(-0.60, -0.175, 1.75, 0.60, -0.14, 1.775, "steel", skip="b", d=1)

    for x0, x1 in (xs[0], xs[2], xs[3]):
        out += front(x0 + 0.02, x1 - 0.02, 0.05, 1.75, -0.15, "white", depth=0.022, c=0.008)

        for z0 in (0.16, 1.54):
            if lk.LOD == 0:
                for i in range(4):
                    out += plate(x0 + 0.07, x1 - 0.07, z0 + i * 0.033, z0 + i * 0.033 + 0.016, -0.174, "graphite")
            else:
                out += plate(x0 + 0.07, x1 - 0.07, z0, z0 + 0.12, -0.174, "slate", d=1)

        out += handle(x1 - 0.07, 0.96, 0.14, -0.172, "graphite", vertical=True, d=1)
        out += plate(x0 + 0.09, x1 - 0.09, 1.40, 1.45, -0.174, "teal", d=0)

    door = part()
    door += box(-0.265, -0.40, 0.05, -0.235, -0.15, 1.75, "white", c=0.008, skip="d")

    for z0 in (0.16, 1.54):
        for i in range(4):
            door += side(-0.35, -0.22, z0 + i * 0.033, z0 + i * 0.033 + 0.016, -0.233, 1, "graphite", d=0)

    door += box(-0.235, -0.38, 0.9, -0.215, -0.36, 1.04, "graphite", skip="l", d=0)
    out += door
    out += box(-0.28, -0.1, 1.65, -0.02, 0.36, 1.68, "steel_dk", skip="lrb", d=1)
    out += tube([(-0.15, 0.03, 1.65), (-0.15, 0.03, 1.60)], 0.006, 3, "steel_lt", caps=(False, False), d=0)
    out += prism([(-0.25, -0.03), (-0.19, -0.05), (-0.09, -0.04), (-0.05, 0.08), (-0.2, 0.1)], 1.0, 1.50, "navy", c=0.04)
    out += box(-0.19, -0.02, 1.50, -0.11, 0.05, 1.58, "navy", c=0.02, d=1)

    for x in (-0.22, -0.105):
        out += box(x - 0.05, -0.11, 0.05, x + 0.045, 0.15, 0.17, "bottle_dk", c=0.03, skip="d", d=1)

    return out


def fridge():
    out = part()
    out += box(-0.27, -0.12, 0.0, 0.27, 0.37, 0.07, "black", skip="d")
    out += box(-0.30, -0.15, 0.06, 0.30, 0.40, 0.44, "white_dk", c=0.014)
    out += box(-0.30, -0.15, 1.50, 0.30, 0.40, 1.80, "white", c=0.022)
    out += box(-0.30, -0.15, 0.44, -0.265, 0.40, 1.50, "white_dk", skip="td")
    out += box(0.265, -0.15, 0.44, 0.30, 0.40, 1.50, "white_dk", skip="td")
    out += plate(-0.266, 0.266, 0.44, 1.50, 0.36, "slate")
    out += box(-0.266, 0.36, 0.44, 0.266, 0.40, 1.50, "white_dk", skip="lrtdf")
    out += front(-0.285, 0.285, 0.09, 0.41, -0.15, "panel", depth=0.016, c=0.006)
    out += louvres(-0.22, 0.22, 0.12, 0.24, -0.166, 4, "steel")
    out += front(-0.27, 0.27, 1.55, 1.75, -0.15, "panel", depth=0.012)
    out += plate(-0.12, 0.08, 1.62, 1.70, -0.164, "graphite_dk", d=1)
    out += plate(-0.09, 0.02, 1.645, 1.675, -0.166, "screen", d=0)

    for x in (0.13, 0.19):
        out += plate(x - 0.015, x + 0.015, 1.645, 1.675, -0.164, "teal", d=0)

    r = rng(11)

    for z in (0.47, 0.68, 0.88, 1.07, 1.27):
        if z > 0.5:
            out += box(-0.265, -0.11, z - 0.012, 0.265, 0.36, z, "steel_lt", skip="lrb", d=1)

        for x in (-0.14, 0.09):
            if r.random() < 0.2:
                continue

            h = 0.05 + r.random() * 0.08
            col = ("white", "teal_lt", "navy", "glass_lt", "slate_lt")[r.randrange(5)]
            out += box(x - 0.09, -0.07, z, x + 0.08 + r.random() * 0.03, 0.1, z + h, col, skip="db", d=1)

            if h < 0.09:
                out += bottle(x - 0.03, -0.03, z + h, 0.08, 0.028, "teal", "white", sides=5)

    door = part()
    door += frame(-0.285, 0.285, 0.445, 1.495, -0.15, 0.05, "white", depth=0.035)
    door += plate(-0.235, -0.185, 0.52, 1.42, -0.172, "glass", d=1)
    door += plate(-0.14, -0.115, 0.60, 1.30, -0.172, "glass_lt", d=0)
    door += box(0.19, -0.222, 0.62, 0.215, -0.20, 1.32, "steel_lt", d=1)

    for z in (0.64, 1.30):
        door += box(0.19, -0.205, z - 0.015, 0.215, -0.18, z + 0.015, "steel", d=0)

    door.rot(-24, "Z", (-0.285, -0.15, 0.0))
    out += door

    return out


def freezer():
    out = part()
    out += box(-0.43, -0.32, 0.0, 0.43, 0.43, 0.07, "black", skip="d")
    out += box(-0.45, -0.34, 0.07, 0.45, 0.45, 1.95, "white_dk", c=0.026)
    out += box(-0.45, -0.41, 0.40, 0.45, -0.348, 1.92, "white", c=0.02)
    out += plate(-0.43, 0.43, 0.42, 1.90, -0.344, "graphite")
    out += frame(-0.36, 0.30, 0.62, 1.38, -0.41, 0.035, "panel", depth=0.012)
    out += plate(-0.325, 0.265, 0.655, 1.345, -0.413, "graphite_dk")
    out += face([(-0.30, -0.415, 0.69), (-0.22, -0.415, 0.69), (0.02, -0.415, 1.31), (-0.06, -0.415, 1.31)], "slate_dk", d=0, ao=False, cast=False, towards=(0, -1, 0))

    for z in (0.86, 1.09):
        out += plate(-0.325, 0.265, z, z + 0.012, -0.416, "slate", d=0)

    out += box(0.355, -0.45, 0.80, 0.385, -0.43, 1.30, "teal", d=1)

    for z in (0.82, 1.28):
        out += box(0.355, -0.435, z - 0.018, 0.385, -0.41, z + 0.018, "steel", skip="b", d=0)

    out += plate(-0.30, 0.10, 1.55, 1.72, -0.412, "panel", d=1)
    out += plate(-0.26, -0.06, 1.60, 1.69, -0.414, "graphite_dk", d=1)
    out += plate(-0.235, -0.12, 1.625, 1.665, -0.416, "screen", d=0)

    for x in (-0.02, 0.04):
        out += plate(x - 0.015, x + 0.015, 1.62, 1.65, -0.416, "teal", d=0)

    for z in (0.55, 1.72):
        out += box(-0.45, -0.39, z - 0.05, -0.425, -0.33, z + 0.05, "steel", d=0)

    out += louvres(-0.38, 0.38, 0.12, 0.35, -0.34, 5, "steel_lt")

    for s in (-1, 1):
        out += side(-0.2, 0.3, 0.2, 0.62, s * 0.451, s, "panel", d=1)
        out += side(-0.2, 0.3, 0.66, 0.69, s * 0.452, s, "teal_dk", d=0)

    out += box(-0.25, 0.0, 1.95, 0.25, 0.3, 1.952, "panel_dk", d=0, skip="d")

    return out


def bsc():
    out = part()

    for x in (-0.70, 0.70):
        for y in (-0.36, 0.48):
            out += box(x - 0.03, y - 0.03, 0.05, x + 0.03, y + 0.03, 0.62, "steel_lt", skip="td")
            out += box(x - 0.045, y - 0.045, 0.0, x + 0.045, y + 0.045, 0.06, "graphite", c=0.012, skip="d", d=1)

        out += box(x - 0.02, -0.33, 0.07, x + 0.02, 0.45, 0.12, "steel", skip="fb", d=1)

    out += box(-0.68, 0.15, 0.10, 0.68, 0.57, 0.62, "panel", c=0.018, skip="t")
    out += louvres(0.20, 0.62, 0.18, 0.50, 0.148, 5, "steel_lt")
    out += louvres(-0.62, -0.20, 0.18, 0.50, 0.148, 5, "steel_lt")
    out += box(-0.75, -0.46, 0.60, 0.75, 0.60, 0.80, "white_dk", c=0.018)
    out += box(-0.67, -0.50, 0.70, 0.67, -0.455, 0.80, "teal", c=0.012, skip="b")
    out += plate(-0.55, -0.35, 0.73, 0.77, -0.502, "glass_lt", d=0)

    for x in (0.30, 0.37, 0.44):
        out += plate(x - 0.018, x + 0.018, 0.732, 0.768, -0.502, "white", d=0)

    out += box(-0.69, -0.60, 0.93, 0.69, -0.46, 0.955, "steel_lt", c=0.006)
    out += box(-0.67, -0.50, 0.80, 0.67, -0.46, 0.955, "steel", skip="bt", d=1)

    for s in (-1, 1):
        out += box(s * 0.75, 0.12, 0.80, s * 0.69, 0.60, 1.50, "white_dk", skip="d")
        out += box(s * 0.75, -0.46, 0.80, s * 0.69, -0.39, 1.50, "white", skip="d")
        out += side(-0.39, 0.12, 0.81, 1.48, s * 0.718, s, "glass")
        out += side(-0.30, -0.22, 0.9, 1.4, s * 0.72, s, "glass_lt", d=0)
        out += side(-0.39, 0.12, 0.81, 1.48, s * 0.714, -s, "glass_dk", d=0)

    out += plate(-0.70, 0.70, 0.80, 1.56, 0.20, "steel_lt")
    out += box(-0.70, 0.20, 0.80, 0.70, 0.60, 1.52, "white_dk", skip="lrdtf")
    out += louvres(-0.55, 0.55, 1.15, 1.38, 0.198, 4, "steel", back="slate")
    out += deck(-0.69, 0.69, -0.46, 0.2, 0.802, "steel", cast=True)

    for x, y, h, r, col in ((-0.25, -0.03, 0.10, 0.07, "teal_dk"), (0.27, 0.06, 0.17, 0.045, "steel"), (0.12, -0.14, 0.06, 0.08, "slate_lt")):
        out += cyl((x, y, 0.80), r, h, col, sides=6, smooth=False, caps=(False, "glass_lt"), d=1)

    out += face([(-0.69, -0.462, 1.10), (0.69, -0.462, 1.10), (0.69, -0.455, 1.50), (-0.69, -0.455, 1.50)], "glass", ao=False, cast=False, towards=(0, -1, 0))
    out += box(-0.69, -0.48, 1.08, 0.69, -0.455, 1.11, "steel_lt", d=1)

    for x0 in (-0.50, 0.22):
        out += face([(x0, -0.466, 1.16), (x0 + 0.08, -0.466, 1.16), (x0 + 0.26, -0.462, 1.45), (x0 + 0.18, -0.462, 1.45)], "glass_lt", d=0, ao=False, cast=False, towards=(0, -1, 0))

    out += box(-0.75, -0.46, 1.50, 0.75, 0.60, 1.62, "white_dk", skip="t")
    out += loft([[(-0.75, -0.52, 1.58), (0.75, -0.52, 1.58), (0.75, 0.60, 1.58), (-0.75, 0.60, 1.58)], [(-0.75, -0.30, 2.16), (0.75, -0.30, 2.16), (0.75, 0.60, 2.16), (-0.75, 0.60, 2.16)], [(-0.71, -0.24, 2.20), (0.71, -0.24, 2.20), (0.71, 0.56, 2.20), (-0.71, 0.56, 2.20)]], "white", caps=("panel_dk", "white_dk"))
    out += face([(-0.20, -0.437, 1.80), (0.10, -0.437, 1.80), (0.10, -0.39, 1.925), (-0.20, -0.39, 1.925)], "graphite", towards=(0, -1, 0.3), d=1)
    out += face([(-0.17, -0.431, 1.83), (0.01, -0.431, 1.83), (0.01, -0.401, 1.905), (-0.17, -0.401, 1.905)], "screen", towards=(0, -1, 0.3), d=0, cast=False)
    out += box(-0.55, -0.36, 1.54, 0.55, -0.22, 1.57, "graphite", d=1)
    out += box(-0.69, -0.49, 1.54, 0.69, -0.47, 1.60, "steel_lt", d=1)

    for x in (-0.69, 0.665):
        out += box(x, -0.485, 0.955, x + 0.025, -0.465, 1.54, "steel", d=1)

    out += box(-0.05, -0.50, 0.955, 0.05, -0.47, 0.98, "graphite", d=0)

    return out


def hood():
    out = part()
    out += box(-0.86, -0.42, 0.0, 0.86, 0.56, 0.09, "black", skip="d")
    out += box(-0.90, -0.48, 0.08, 0.90, 0.60, 0.90, "white_dk", c=0.016)

    for i, (x0, x1) in enumerate(((-0.84, -0.29), (-0.27, 0.27), (0.29, 0.84))):
        out += front(x0, x1, 0.14, 0.84, -0.48, "teal", depth=0.018, c=0.008)
        out += handle(x1 - 0.08 if i < 2 else x0 + 0.08, 0.52, 0.16, -0.498, "steel_lt", vertical=True, d=1)
        out += plate(x0 + 0.08, x1 - 0.08, 0.18, 0.20, -0.50, "teal_dk", d=0)

    out += box(-0.90, -0.60, 0.90, 0.90, 0.60, 0.96, "steel_lt", c=0.016)
    out += deck(-0.74, 0.74, -0.44, 0.40, 0.962, "graphite", cast=True)

    for s in (-1, 1):
        out += box(s * 0.90, 0.40, 0.96, s * 0.84, 0.60, 2.20, "white_dk", skip="d")
        out += box(s * 0.90, -0.50, 0.96, s * 0.76, -0.42, 2.12, "white", c=0.012, skip="d")
        out += side(-0.42, 0.40, 1.0, 2.14, s * 0.86, s, "glass")
        out += side(-0.30, -0.18, 1.1, 2.0, s * 0.862, s, "glass_lt", d=0)
        out += side(-0.42, 0.40, 1.0, 2.14, s * 0.856, -s, "glass_dk", d=0)
        out += box(s * 0.88, -0.44, 0.96, s * 0.835, 0.42, 1.01, "white_dk", d=1)

    out += plate(-0.86, 0.86, 0.96, 2.20, 0.38, "slate_dk")
    out += box(-0.86, 0.38, 0.96, 0.86, 0.60, 2.14, "white_dk", skip="lrdtf")

    for z in (1.12, 1.75):
        out += plate(-0.6, 0.6, z, z + 0.07, 0.376, "black", d=1)

    for x, h, r, col in ((-0.50, 0.2, 0.05, "glass_lt"), (-0.28, 0.1, 0.07, "teal_lt"), (0.44, 0.07, 0.08, "steel_dk")):
        out += cyl((x, 0.02, 0.962), r, h, col, sides=6, smooth=False, caps=(False, True), d=1)

    out += rod((0.44, 0.21, 0.96), (0.44, 0.21, 1.46), 0.012, "steel_lt", d=0)
    out += box(0.30, 0.19, 1.30, 0.46, 0.22, 1.33, "steel", d=0)
    out += loft([[(-0.90, -0.54, 2.05), (0.90, -0.54, 2.05), (0.90, 0.60, 2.05), (-0.90, 0.60, 2.05)], [(-0.90, -0.54, 2.17), (0.90, -0.54, 2.17), (0.90, 0.60, 2.17), (-0.90, 0.60, 2.17)], [(-0.84, -0.38, 2.35), (0.84, -0.38, 2.35), (0.84, 0.56, 2.35), (-0.84, 0.56, 2.35)]], lambda j, i: "white" if j else "white_dk", caps=("panel_dk", "white_dk"))
    out += plate(0.42, 0.66, 2.08, 2.15, -0.543, "graphite", d=1)
    out += plate(0.45, 0.57, 2.095, 2.135, -0.545, "screen", d=0)
    out += plate(-0.66, -0.30, 2.095, 2.135, -0.543, "teal", d=0)
    out += box(-0.79, -0.485, 1.12, 0.79, -0.455, 1.17, "steel_lt", c=0.006)
    out += box(-0.40, -0.52, 1.125, 0.40, -0.485, 1.15, "graphite", d=1)

    for x in (-0.775, 0.745):
        out += box(x, -0.475, 1.16, x + 0.03, -0.445, 2.06, "steel", d=1)

    out += box(-0.76, -0.47, 1.34, 0.76, -0.45, 1.39, "steel_lt", d=1)

    out += plate(-0.75, 0.75, 1.36, 2.06, -0.44, "glass")

    for x0 in (-0.62, 0.20):
        out += face([(x0, -0.452, 1.44), (x0 + 0.07, -0.452, 1.44), (x0 + 0.33, -0.452, 2.0), (x0 + 0.26, -0.452, 2.0)], "glass_lt", d=0, ao=False, cast=False, towards=(0, -1, 0))

    out += box(-0.35, -0.22, 2.35, 0.35, 0.30, 2.72, "panel", c=0.05, skip="d")
    out += louvres(-0.24, 0.08, 2.44, 2.62, -0.221, 3, "steel_lt", d=0)
    out += puck((0.41, 0.04, 2.56), 0.075, 0.02, "slate", sides=8, d=0)
    out += box(0.35, -0.04, 2.49, 0.46, 0.12, 2.63, "steel", c=0.025, d=1)
    out += cyl((-0.52, 0.32, 2.34), 0.095, 0.55, "steel_lt", sides=8, smooth=False, caps=(False, False))
    out += cyl((-0.52, 0.32, 2.56), 0.112, 0.04, "steel_dk", sides=8, smooth=False, caps=(True, True), d=0)
    out += cyl((-0.52, 0.32, 2.86), 0.115, 0.06, "slate_lt", sides=8, smooth=False, caps=(True, "graphite"), d=1)

    return out


def gas_cylinder():
    out = part()
    cx = -0.115
    out += lathe([(0.118, 0.0, "slate_lt"), (0.135, 0.025, "white_dk"), (0.135, 0.76, "white_dk"), (0.138, 0.76, "teal"), (0.135, 0.82, "teal"), (0.115, 0.875, "teal"), (0.06, 0.915, "teal_dk"), (0.045, 0.94, "teal_dk"), (0.0, 0.945, "teal_dk")], 12, at=(cx, 0, 0), smooth=False)
    out += cyl((cx, 0, 0.055), 0.14, 0.035, "steel", sides=12, smooth=False, caps=(True, True), d=0)
    out += plate(cx - 0.05, cx + 0.05, 0.36, 0.56, -0.137, "canvas", d=1)
    out += plate(cx - 0.035, cx + 0.035, 0.46, 0.49, -0.139, "teal_dk", d=0)
    out += lk.torus((cx, 0, 0.95), 0.108, 0.012, "slate", segs=10, sides=4, axis="Z")
    out += lk.torus((cx, 0, 1.285), 0.108, 0.015, "slate_lt", segs=10, sides=4, axis="Z")

    for i in range(6):
        a = math.pi * 2 * i / 6 + 0.2
        x = cx + math.cos(a) * 0.108
        y = math.sin(a) * 0.108
        out += rod((x, y, 0.92), (x, y, 1.285), 0.014, "slate", d=1)

    out += cyl((cx, 0, 0.94), 0.045, 0.07, "steel_lt", sides=6, smooth=False, d=1)
    out += cyl((cx, 0, 1.01), 0.025, 0.07, "steel_dk", sides=6, smooth=False, d=1)
    out += cyl((cx, 0, 1.075), 0.052, 0.03, "graphite", sides=8, smooth=False, caps=(True, True), d=1)
    out += rod((cx, 0, 1.0), (0.12, 0, 1.0), 0.016, "steel", d=1)
    out += box(0.10, -0.02, 0.94, 0.25, 0.022, 1.09, "slate_lt", c=0.012)
    out += disc(0.175, 1.015, -0.02, 0.054, "copper", n=8, d=1)
    out += disc(0.175, 1.015, -0.032, 0.035, "canvas", n=8, d=0, depth=0.003)

    return out


def canister():
    out = part()
    out += lathe([(0.21, 0.0, "black"), (0.255, 0.07, "slate_dk"), (0.262, 0.07, "white_dk"), (0.27, 0.35, "white_dk"), (0.282, 0.35, "teal"), (0.282, 0.59, "teal"), (0.27, 0.59, "white"), (0.268, 0.76, "white"), (0.23, 0.86, "panel"), (0.17, 0.885, "panel"), (0.16, 0.92, "steel"), (0.0, 0.92, "steel")], 12, smooth=False)

    for z in (0.36, 0.57):
        out += cyl((0, 0, z), 0.288, 0.018, "teal_dk", sides=12, smooth=False, caps=(False, False), d=0)

    out += box(-0.14, -0.022, 0.915, 0.14, 0.022, 0.95, "slate_lt", d=1)

    for ang in (0, 90, 180, 270):
        arm = part()
        arm += box(-0.032, -0.318, 0.78, 0.032, -0.235, 0.86, "slate", c=0.01)
        arm += box(-0.032, -0.318, 0.86, 0.032, -0.262, 1.045, "slate_dk", c=0.012, skip="d")
        arm += box(-0.032, -0.30, 1.03, 0.032, -0.17, 1.08, "slate", c=0.012)
        out += arm.rot(ang, "Z")

    for z0, col in ((0.65, "screen"), (0.16, "glass")):
        out += box(-0.065, -0.29, z0, 0.065, -0.255, z0 + 0.11, "slate_dk", c=0.008, skip="b", d=1)
        out += plate(-0.04, 0.04, z0 + 0.028, z0 + 0.082, -0.292, col, d=0)

    side_box = part()
    side_box += box(-0.07, -0.298, 0.41, 0.07, -0.268, 0.52, "steel_lt", c=0.008, skip="b", d=1)
    side_box += plate(-0.045, 0.045, 0.44, 0.49, -0.30, "graphite", d=0)
    out += side_box.rot(90, "Z")

    for z in (0.20, 0.68):
        h = part()
        h += box(-0.02, -0.30, z - 0.04, 0.02, -0.25, z + 0.04, "graphite", d=0)
        out += h.rot(-90, "Z")

    return out


OPTS = {"ao": 0.5, "reach": 0.6, "grime": 0.08, "grime_h": 0.25, "errors": (0.011, 0.04)}

ALL = {
    "island": (island, OPTS),
    "wallbench": (wallbench, OPTS),
    "desk": (desk, OPTS),
    "shelf": (shelf, OPTS),
    "lockers": (lockers, OPTS),
    "fridge": (fridge, OPTS),
    "freezer": (freezer, OPTS),
    "bsc": (bsc, OPTS),
    "hood": (hood, OPTS),
    "cylinder": (gas_cylinder, OPTS),
    "canister": (canister, OPTS),
}
