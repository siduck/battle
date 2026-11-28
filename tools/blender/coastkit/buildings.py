import math

import arch as a
import ck


def foundation(poly, z0=-1.5, z1=0.12):
    return a.band(poly, z0, z1, 0.0, "stone_dk", c=0.03, top="stone")


def terrace(wall, wall_lt, wall_dk, accent, accent_b, roof, style, seed):
    out = ck.Part()
    x0, x1 = -2.0, 2.48
    yf, ys, yb = -3.94, -3.56, 3.96
    cx = (x0 + x1) / 2
    base = a.rect(x0 + 0.02, ys, x1 - 0.02, yb)
    shop = a.rect(x0 + 0.02, yf, x1 - 0.02, ys + 0.05)
    out += foundation(a.rect(x0, yf, x1, yb + 0.02))
    left = seed % 2 == 0
    dx = x0 + 0.95 if left else x1 - 0.95
    sx = x1 - 1.62 if left else x0 + 1.62
    shop_ops = [a.door(dx - x0 - 0.02, 0.98, 2.45, leaf=accent, lintel="flat", depth=0.26, glazed=seed % 3 == 0), a.win(sx - x0 - 0.02, 0.62, 2.34, 1.83, n=3, sill=True, lintel="flat", trim="trim", depth=0.2)]
    out += a.facade((x0 + 0.02, yf), (x1 - 0.02, yf), 0.1, 3.36, wall_dk, shop_ops)
    out += a.facade((x1 - 0.02, yf), (x1 - 0.02, ys), 0.1, 3.36, wall_dk)
    out += a.facade((x0 + 0.02, ys), (x0 + 0.02, yf), 0.1, 3.36, wall_dk)
    out += ck.box(sx - 1.17, yf - 0.03, 0.14, sx + 1.17, yf, 0.48, accent, c=0.015, d=1, skip="b")

    for px in (x0 + 0.17, x1 - 0.17, (dx + sx) / 2 + (0.0 if left else 0.0)):
        w = 0.2 if abs(px - (dx + sx) / 2) < 0.01 else 0.28
        px = (dx + (0.64 if left else -0.64)) if w == 0.2 else px
        out += ck.box(px - w / 2, yf - 0.07, 0.1, px + w / 2, yf, 2.58, "trim", c=0.025, d=1, skip="bd")
        out += ck.box(px - w / 2 - 0.03, yf - 0.1, 0.1, px + w / 2 + 0.03, yf, 0.42, "trim_dk", c=0.025, d=0, skip="bd")

    out += ck.box(x0 + 0.06, yf - 0.11, 2.62, x1 - 0.06, yf, 3.06, accent, c=0.03, d=2, skip="b")
    out += a.letters(cx - 1.2, cx + 1.2, yf - 0.115, 2.72, 0.24, "canvas", seed=seed)
    out += a.band(shop, 3.22, 3.46, 0.1, "trim", c=0.035, top=wall_dk, detail=1)
    out += a.slab(shop, 3.36, wall_dk)
    side = [a.win(2.2, 4.1, 0.7, 1.15, bars="h", lintel="flat"), a.win(5.4, 1.1, 0.7, 1.0, bars="h")]
    back = [a.win(1.15, 0.95, 1.0, 1.2, bars="v"), a.door(3.2, 0.95, 2.2, leaf=accent_b), a.win(1.15, 4.05, 1.0, 1.3, bars="h"), a.win(3.2, 4.05, 1.0, 1.3, bars="h")]
    upper = []

    if style in ("bay", "dutch"):
        pass
    else:
        for wx in (cx - 1.0, cx + 1.0):
            upper.append(a.win(wx - x0 - 0.02, 4.0, 0.86, 1.5, bars="h", lintel="hood" if style == "para" else "arch", shutters=accent if style == "para" else None, box=style == "gable"))

    out += a.facade(base[0], base[1], 0.1, 5.95, wall, upper)
    out += a.facade(base[1], base[2], 0.1, 5.95, ck.shade(wall, 0.94), side)
    out += a.facade(base[2], base[3], 0.1, 5.95, wall, back)
    out += a.facade(base[3], base[0], 0.1, 5.95, ck.shade(wall, 0.94), side)

    if style in ("bay", "dutch"):
        bw, fw = 1.55, 0.95
        bay = [(cx - bw, ys + 0.02), (cx - fw, yf), (cx + fw, yf), (cx + bw, ys + 0.02)]
        sidew = math.hypot(bw - fw, yf - ys)
        out += a.facade(bay[0], bay[1], 3.46, 5.7, wall_lt, [a.win(sidew / 2, 3.98, 0.44, 1.35, bars="none", lintel="none", depth=0.1, sill=False)])
        out += a.facade(bay[1], bay[2], 3.46, 5.7, wall_lt, [a.win(fw, 3.98, 1.52, 1.35, n=2, lintel="flat", depth=0.12)])
        out += a.facade(bay[2], bay[3], 3.46, 5.7, wall_lt, [a.win(sidew / 2, 3.98, 0.44, 1.35, bars="none", lintel="none", depth=0.1, sill=False)])
        out += a.band(bay, 3.82, 3.9, 0.06, "trim", c=0.02, detail=0)
        top = [(cx - bw * 0.7, ys + 0.04), (cx - fw * 0.65, ys - 0.12), (cx + fw * 0.65, ys - 0.12), (cx + bw * 0.7, ys + 0.04)]
        out += a.hip(a.offset(bay, 0.1), top, 5.7, 6.0 if style == "bay" else 5.98, roof, rows=2, under=True)

    for z0, z1, d in ((5.82, 6.12, 0.14),):
        out += a.band(base, z0, z1, d, "trim", c=0.045, top=wall_dk)

    for qx in (x0 + 0.17, x1 - 0.17):
        for i in range(5):
            w = 0.34 if i % 2 == 0 else 0.24
            sgn = 1 if qx < cx else -1
            ex = qx - sgn * 0.15
            out += ck.box(min(ex, ex + sgn * w), ys - 0.05, 3.5 + i * 0.46, max(ex, ex + sgn * w), ys + 0.02, 3.5 + i * 0.46 + 0.4, wall_lt, d=1, skip="b")

    for i in range(7):
        bx = x0 + 0.4 + i * (x1 - x0 - 0.8) / 6
        out += ck.box(bx - 0.06, ys - 0.12, 5.66, bx + 0.06, ys, 5.82, "trim_dk", d=0, skip="bt")

    out += a.downpipe(x1 - 0.1 if left else x0 + 0.1, ys - 0.08, 3.46, 5.72)

    if style == "bay":
        out += a.gable(x0 + 0.3, x1 - 0.3, ys + 0.08, yb - 0.1, 6.12, 1.2, roof, wall, axis="y", over=0.22, rows=5)
        out += a.disc((cx, ys + 0.04, 6.62), 0.27, "trim", 10, 0.06)
        out += a.disc((cx, ys + 0.01, 6.62), 0.17, "glass", 10, 0.04, d=1)
        out += a.chimney(x0 + 0.55, 1.6, 6.0, 7.42)
    elif style == "dutch":
        pts = [(x0 + 0.12, 6.12), (x1 - 0.12, 6.12), (x1 - 0.12, 6.35), (x1 - 0.75, 6.42), (cx + 0.95, 6.98), (cx + 0.45, 7.05), (cx + 0.32, 7.38), (cx - 0.32, 7.38), (cx - 0.45, 7.05), (cx - 0.95, 6.98), (x0 + 0.75, 6.42), (x0 + 0.12, 6.35)]
        out += ck.extrude(pts, ys - 0.02, ys + 0.24, wall, force=True, side="trim")
        out += a.disc((cx, ys - 0.04, 6.62), 0.3, "trim", 10, 0.06)
        out += a.disc((cx, ys - 0.07, 6.62), 0.2, "glass", 10, 0.04, d=1)
        out += ck.blob((cx, ys + 0.11, 7.42), (0.1, 0.1, 0.1), "trim", sub=0, d=0)
        out += a.hip(a.rect(x0 + 0.1, ys + 0.22, x1 - 0.1, yb), [(x0 + 1.2, ys + 1.4), (x1 - 1.2, ys + 1.4), (x1 - 1.2, yb - 1.5), (x0 + 1.2, yb - 1.5)], 6.12, 7.12, roof, rows=4)
        out += a.chimney(x1 - 0.6, 1.2, 6.2, 7.44)
    elif style == "para":
        out += a.parapet(base, 6.12, 0.52, wall, "trim")
        out += a.slab(a.offset(base, -0.2), 6.14, roof)
        out += ck.box(cx - 0.9, ys - 0.06, 6.62, cx + 0.9, ys + 0.2, 7.12, wall, c=0.03)
        out += ck.box(cx - 1.0, ys - 0.1, 7.12, cx + 1.0, ys + 0.24, 7.25, "trim", c=0.035)
        out += a.letters(cx - 0.68, cx + 0.68, ys - 0.065, 6.74, 0.24, accent, seed=seed + 5)

        for ux in (x0 + 0.24, x1 - 0.24):
            out += ck.lathe([(0.1, 0, "trim"), (0.16, 0.14, "trim"), (0.08, 0.3, "trim"), (0.0, 0.36, "trim")], 6, (ux, ys + 0.1, 6.78), smooth=False, d=1)

        out += a.chimney(x0 + 0.6, 2.2, 6.1, 7.44)
        out += ck.box(0.5, 0.2, 6.14, 1.6, 1.5, 6.6, "steel", c=0.05, d=1)
    else:
        out += a.gable(ys + 0.0, yb - 0.1, -x1 + 0.2, -x0 - 0.2, 6.12, 1.2, roof, wall, axis="y", over=0.2, rows=5).rot(90)
        out += ck.box(cx - 0.62, ys + 0.25, 6.2, cx + 0.62, ys + 1.5, 6.88, wall_lt, c=0.025)
        out += a.facade((cx - 0.62, ys + 0.24), (cx + 0.62, ys + 0.24), 6.2, 6.88, wall_lt, [a.win(0.62, 6.34, 0.76, 0.46, lintel="none", depth=0.08)])
        out += a.gable(cx - 0.62, cx + 0.62, ys + 0.24, ys + 1.9, 6.88, 0.42, roof, wall_lt, axis="y", over=0.14, rows=2, thick=0.08)
        out += a.chimney(x0 + 0.5, 0.9, 6.2, 7.44)

    return out


def terrace_a():
    return terrace("cream", "cream_lt", "cream_dk", "navy", "teal", "slate", "bay", 2)


def terrace_b():
    return terrace("sage", "sage_lt", "sage_dk", "red", "navy", "tile", "para", 3)


def terrace_c():
    return terrace("coral", "coral_lt", "coral_dk", "teal", "navy", "slate", "gable", 4)


def terrace_d():
    return terrace("ochre", "ochre_lt", "ochre_dk", "teal_dk", "red", "slate_dk", "dutch", 7)


def corner():
    out = ck.Part()
    poly = [(-4.42, -4.42), (1.58, -4.42), (4.54, -1.62), (4.54, 4.54), (-4.42, 4.54)]
    out += foundation(poly)
    inner = a.offset(poly, -0.06)

    def width(i):
        p, q = inner[i], inner[(i + 1) % len(inner)]

        return math.hypot(q[0] - p[0], q[1] - p[1])

    shop = {
        0: [a.win(width(0) * 0.27, 0.6, 2.2, 1.9, n=3, lintel="flat"), a.win(width(0) * 0.74, 0.6, 2.2, 1.9, n=3, lintel="flat")],
        1: [a.door(width(1) / 2, 1.7, 2.7, leaf="red", glazed=True, depth=0.34, lintel="arch")],
        2: [a.win(1.75, 0.6, 2.2, 1.9, n=3, lintel="flat"), a.win(4.4, 0.6, 1.7, 1.9, n=2, lintel="flat")],
        3: [a.win(2.0, 1.1, 1.0, 1.2, frame=False), a.door(4.6, 1.0, 2.3, leaf="red_dk", lintel="hood"), a.win(7.0, 1.1, 1.0, 1.2, frame=False)],
        4: [a.win(2.4, 1.0, 1.1, 1.3, frame=False), a.win(6.4, 1.0, 1.1, 1.3, frame=False)],
    }
    out += a.shell(inner, 0.1, 3.3, "blue_dk", shop)
    out += a.onto(inner[3], inner[4], ck.box(0.05, -0.07, 0.1, 3.9, 0.0, 0.62, "stone_dk", c=0.025, d=1, skip="bd") + ck.box(5.3, -0.07, 0.1, width(3) - 0.05, 0.0, 0.62, "stone_dk", c=0.025, d=1, skip="bd"))
    out += a.onto(inner[4], inner[0], ck.box(0.05, -0.07, 0.1, width(4) - 0.05, 0.0, 0.62, "stone_dk", c=0.025, d=1, skip="bd"))
    upper = {}

    for i in range(5):
        w = width(i)

        if i == 1:
            upper[i] = [a.win(w / 2, 3.95, 1.5, 1.55, n=2, lintel="arch", box=True)]

            continue

        n = max(2, int(w / 2.1))
        ops = []

        for k in range(n):
            front = i in (0, 2)
            ops.append(a.win(w * (k + 0.5) / n, 3.95, 0.92, 1.5, bars="h", lintel="hood" if front else "flat", shutters="navy" if front and w / n > 2.0 else None, box=front and k % 2 == 0, frame=front))

        upper[i] = ops

    out += a.shell(inner, 3.3, 6.0, "blue", upper)
    out += a.band(inner, 3.3, 3.58, 0.2, "trim", c=0.05, top="blue_dk")
    out += a.band(inner, 5.9, 6.22, 0.18, "trim", c=0.05, top="blue_dk")

    for i in (0, 1, 2):
        p, q = inner[i], inner[(i + 1) % 5]
        w = width(i)
        fascia = ck.box(0.16, -0.1, 2.78, w - 0.16, 0.0, 3.24, "navy" if i != 1 else "red_dk", c=0.03, skip="b")
        fascia += a.letters(w * 0.2, w * 0.8, -0.105, 2.9, 0.23, "canvas", seed=i + 3)

        for px in (0.14, w - 0.14):
            fascia += ck.box(px - 0.13, -0.09, 0.1, px + 0.13, 0.0, 2.75, "trim", c=0.03, d=1, skip="bd")

        if i == 0:
            for cxx in (w * 0.27, w * 0.74):
                fascia += a.striped_awning(cxx - 1.25, cxx + 1.25, -0.08, 2.76, 0.7, 0.32, "red", "canvas", valance=0.14)

        if i == 2:
            for px in (0.5, 2.75, 3.4, w - 0.6):
                fascia += ck.box(px - 0.09, -0.11, 3.24, px + 0.09, 0.0, 3.34, "gold", d=0, skip="b")

        for k in range(int(w / 0.75)):
            bx = 0.4 + k * (w - 0.8) / max(int(w / 0.75) - 1, 1)
            fascia += ck.box(bx - 0.07, -0.14, 5.72, bx + 0.07, 0.0, 5.9, "trim_dk", d=0, skip="bt")

        out += a.onto(p, q, fascia)

    for p in (inner[0], inner[1], inner[2]):
        for k in range(5):
            out += ck.cbox(0.3 if k % 2 == 0 else 0.22, 0.3 if k % 2 == 0 else 0.22, 0.4, (p[0], p[1], 3.66 + k * 0.45), "blue_lt", d=1, skip="d")

    out += a.parapet(inner, 6.22, 0.42, "blue", "trim", thick=0.24)
    out += a.slab(a.offset(inner, -0.2), 6.24, "slate_dk")
    mid = ((inner[1][0] + inner[2][0]) / 2 - 0.62, (inner[1][1] + inner[2][1]) / 2 + 0.62)
    octo = ck.ngon(1.18, 8, mid[0], mid[1])
    out += a.shell(octo, 6.24, 6.5, "trim")
    out += a.hip(a.offset(octo, 0.14), ck.ngon(0.04, 8, mid[0], mid[1]), 6.5, 6.92, "tile", rows=3)
    out += ck.blob((mid[0], mid[1], 6.96), (0.12, 0.12, 0.12), "gold", sub=0, d=1)
    out += a.chimney(-3.5, 2.8, 6.2, 6.98, w=0.8)
    out += a.chimney(2.8, 3.4, 6.2, 6.98, w=0.8)
    out += ck.box(-2.2, -1.4, 6.24, -0.8, 0.1, 6.7, "steel", c=0.06, d=1)
    out += ck.cyl((-1.5, -0.65, 6.7), 0.42, 0.07, "iron", sides=10, d=1)
    out += ck.box(0.1, 1.6, 6.24, 1.5, 2.9, 6.62, "stone", c=0.05, d=1)
    out += ck.box(0.2, 1.7, 6.62, 1.4, 2.8, 6.68, "glass_lt", c=0.02, d=0)
    out += a.downpipe(-4.38, -4.34, 0.2, 5.8)

    return out


def hotel():
    out = ck.Part()
    x0, x1, y0, y1 = -3.6, 3.88, -2.14, 3.86
    main = a.rect(x0, y0, x1, y1)
    out += foundation(a.rect(x0, -3.1, x1, y1 + 0.02))
    floors = (3.35, 6.1, 8.85)
    front = []
    wide = x1 - x0
    front.append(a.win(0.78, 0.8, 0.95, 1.75, bars="h", lintel="arch"))

    for fz in floors:
        front.append(a.win(0.78, fz + 0.55, 0.95, 1.6, bars="h", lintel="hood", box=fz < 4))

    side = []

    for sx in (1.5, 4.5):
        side.append(a.win(sx, 0.85, 1.0, 1.6, bars="h", lintel="flat"))

        for fz in floors:
            side.append(a.win(sx, fz + 0.55, 1.0, 1.6, bars="h", lintel="flat", key=fz > 6))

    back = []

    for sx in (1.4, 3.74, 6.1):
        back.append(a.win(sx, 0.85, 1.0, 1.5, bars="v", frame=False, lintel="none"))

        for fz in floors:
            back.append(a.win(sx, fz + 0.55, 1.0, 1.55, bars="h", frame=False, lintel="none"))

    out += a.facade(main[0], main[1], 0.1, 11.45, "cream", front)
    out += a.facade(main[1], main[2], 0.1, 11.45, "cream_lt", side)
    out += a.facade(main[2], main[3], 0.1, 11.45, "cream", back)
    out += a.facade(main[3], main[0], 0.1, 11.45, "cream_lt", side)
    out += a.band(main, 0.1, 0.62, 0.07, "stone", c=0.04)

    for fz in floors:
        out += a.band(main, fz - 0.02, fz + 0.2, 0.1, "trim", c=0.035, top="cream_dk")

    out += a.band(main, 11.32, 11.72, 0.24, "trim", c=0.07, top="cream_dk")

    for p in (main[0], main[1], main[2], main[3]):
        for k in range(0, 20):
            out += ck.cbox(0.36 if k % 2 == 0 else 0.26, 0.36 if k % 2 == 0 else 0.26, 0.44, (p[0], p[1], 0.72 + k * 0.52), "cream_dk", d=1, skip="d")

    for bx, hw in ((-0.55, 1.45), (2.42, 1.45)):
        y_back, y_face, fw = y0 + 0.02, -3.04, 0.82
        bay = [(bx - hw, y_back), (bx - fw, y_face), (bx + fw, y_face), (bx + hw, y_back)]
        side_w = math.hypot(hw - fw, y_face - y_back)
        faces = [[], [], []]

        for fz in floors:
            faces[0].append(a.win(side_w / 2, fz + 0.55, 0.56, 1.65, bars="none", lintel="none", depth=0.12, sill=False))
            faces[1].append(a.win(fw, fz + 0.55, 1.26, 1.65, n=2, lintel="flat", depth=0.14))
            faces[2].append(a.win(side_w / 2, fz + 0.55, 0.56, 1.65, bars="none", lintel="none", depth=0.12, sill=False))

        for i in range(3):
            out += a.facade(bay[i], bay[i + 1], 2.55, 11.25, "cream_lt", faces[i])

        for fz in floors:
            out += a.band(bay, fz - 0.02, fz + 0.26, 0.09, "trim", c=0.035, top="cream_dk")
            out += a.band(bay, fz + 0.3, fz + 0.4, 0.03, "navy", c=0.012, detail=0)

        out += a.band(bay, 11.05, 11.34, 0.15, "trim", c=0.05)
        top = [(bx - 0.7, y0 + 0.05), (bx - 0.35, y0 - 0.35), (bx + 0.35, y0 - 0.35), (bx + 0.7, y0 + 0.05)]
        out += a.hip(a.offset(bay, 0.12), top, 11.34, 12.0, "tile", rows=3)
        out += ck.blob((bx, y0 - 0.32, 12.06), (0.1, 0.1, 0.12), "gold", sub=0, d=1)
        out.append(ck.Poly([(p[0], p[1], 2.55) for p in reversed(bay)], "cream_dk"))

    ground = a.rect(-1.1, -3.04, 3.88, y0 + 0.03)
    out += a.facade(ground[0], ground[1], 0.1, 2.55, "cream_dk", [a.win(1.05, 0.55, 1.45, 1.75, n=2, lintel="flat"), a.door(2.95, 1.55, 2.35, leaf="navy", glazed=True, depth=0.3), a.win(4.4, 0.55, 0.8, 1.75, bars="h")])
    out += a.facade(ground[1], ground[2], 0.1, 2.55, "cream_dk")
    out += a.facade(ground[3], ground[0], 0.1, 2.55, "cream_dk")
    porch = a.rect(-1.14, -3.58, 3.88, y0)
    out += a.band(porch, 2.55, 3.02, 0.0, "navy", c=0.05, top="slate_dk")
    out.append(ck.Poly([(p[0], p[1], 2.55) for p in reversed(porch)], "trim_dk"))
    out += a.band(porch, 3.02, 3.14, 0.07, "trim", c=0.03)
    out += a.letters(0.0, 2.8, -3.585, 2.66, 0.28, "gold", seed=11, n=5)

    for px in (-0.95, 0.95, 2.75, 3.7):
        out += ck.cyl((px, -3.4, 0.3), 0.11, 2.12, "trim", sides=8, rt=0.095, d=2)
        out += ck.cbox(0.34, 0.34, 0.3, (px, -3.4, 0.0), "stone", c=0.035)
        out += ck.cbox(0.3, 0.3, 0.14, (px, -3.4, 2.42), "trim", c=0.03, d=0)

    out += ck.box(0.9, -3.55, 0.0, 2.8, -3.0, 0.12, "stone_lt", c=0.025)
    out += ck.box(-2.85, y0 - 0.06, 2.62, -1.5, y0, 2.9, "navy", c=0.02, d=1)
    out += a.letters(-2.75, -1.6, y0 - 0.065, 2.68, 0.15, "gold", seed=4)
    mansard = a.offset(main, -0.1)
    top = a.offset(main, -1.05)
    out += a.hip(mansard, top, 11.72, 13.75, "slate", rows=5, cap="slate_dk")
    out += a.ridge_caps(mansard, top, 11.72, 13.75, "slate_lt")
    out += a.band(top, 13.72, 13.95, 0.12, "trim", c=0.04, top="slate_dk")
    out += a.slab(a.offset(top, 0.02), 13.9, "slate_dk")

    for dx in (-2.55, 0.15, 2.85):
        for sgn, face_y in ((-1, y0 + 0.2),):
            if sgn < 0 and dx > -2:
                face_y = y0 + 0.24

            dm = ck.box(dx - 0.5, 0.0, 12.1, dx + 0.5, 0.85, 13.0, "cream_lt", c=0.025)
            dm += a.facade((dx - 0.5, -0.01), (dx + 0.5, -0.01), 12.1, 13.0, "cream_lt", [a.win(0.5, 12.24, 0.6, 0.68, lintel="none", depth=0.08, bars="v")])
            dm += a.gable(dx - 0.5, dx + 0.5, -0.01, 1.0, 13.0, 0.34, "slate_dk", "cream_lt", over=0.12, rows=2, thick=0.07)
            dm.move(0, face_y, 0)

            if sgn > 0:
                dm.rot(180, "Z", (dx, face_y, 0))

            out += dm

    for cxx, cy in ((-2.35, 1.9), (2.6, 1.9), (0.2, 0.0)):
        out += a.chimney(cxx, cy, 13.6, 15.33 if cxx != 0.2 else 14.9, w=0.9, dp=0.5, pots=3)

    return out


def tavern():
    out = ck.Part()
    x0, x1, y0, y1 = -3.44, 3.48, -2.52, 2.94
    main = a.rect(x0, y0, x1, y1)
    out += foundation(a.rect(x0, -2.96, x1, 2.98))
    gf_front = [a.win(1.35, 0.75, 1.5, 1.35, n=3, lintel="arch", lintel_col="stone"), a.door(3.46, 1.2, 2.45, leaf="red_dk", lintel="flat", depth=0.28, lintel_col="stone"), a.win(5.57, 0.75, 1.5, 1.35, n=3, lintel="arch", lintel_col="stone")]
    side = [a.win(1.6, 0.85, 0.95, 1.15, lintel_col="stone"), a.win(3.9, 0.85, 0.95, 1.15, lintel_col="stone")]
    back = [a.win(1.4, 0.85, 1.1, 1.2), a.door(3.6, 1.0, 2.2, leaf="wood_dk"), a.win(5.5, 0.85, 1.1, 1.2)]
    out += a.shell(main, 0.1, 2.9, "brick", {0: gf_front, 1: side, 2: back, 3: side})

    for i in range(46):
        face = i % 4
        p, q = main[face], main[(face + 1) % 4]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        u = 0.25 + ck.hash01(i, 1.7) * (ln - 0.5)
        z = 0.25 + int(ck.hash01(i, 5.1) * 17) * 0.15
        ops = {0: gf_front, 1: side, 2: back, 3: side}[face]

        if any(abs(u - o["x"]) < o["w"] / 2 + 0.3 and o["z"] - 0.2 < z < o["z"] + o["h"] + 0.5 for o in ops):
            continue

        out += a.onto(p, q, ck.box(u - 0.17, -0.025, z, u + 0.17, 0.0, z + 0.12, "brick_dk" if i % 3 else "coral_dk", d=0, skip="b"))

    upper = a.rect(x0 - 0.0, y0 - 0.2, x1, y1)
    uf = [a.win(1.25, 3.6, 1.15, 1.25, n=2, shutters="teal", lintel="flat", lintel_col="wood_dk", trim="wood_dk"), a.win(3.46, 3.6, 0.8, 1.25, bars="h", lintel="flat", lintel_col="wood_dk", trim="wood_dk"), a.win(5.67, 3.6, 1.15, 1.25, n=2, shutters="teal", lintel="flat", lintel_col="wood_dk", trim="wood_dk")]
    us = [a.win(1.7, 3.6, 0.95, 1.2, lintel_col="wood_dk", trim="wood_dk"), a.win(4.0, 3.6, 0.95, 1.2, lintel_col="wood_dk", trim="wood_dk")]
    ub = [a.win(1.9, 3.6, 1.0, 1.2, trim="wood_dk"), a.win(5.0, 3.6, 1.0, 1.2, trim="wood_dk")]
    out += a.shell(upper, 2.9, 5.7, "cream", {0: uf, 1: us, 2: ub, 3: us})
    out.append(ck.Poly([(p[0], p[1], 2.9) for p in reversed(upper)], "wood_dk"))
    out += a.band(upper, 2.86, 3.1, 0.07, "wood_dk", c=0.03, top="wood")
    out += a.band(upper, 5.46, 5.7, 0.06, "wood_dk", c=0.03)

    for p, q in ((upper[0], upper[1]), (upper[2], upper[3])):
        ln = abs(q[0] - p[0])

        for u in (0.12, 2.38, 4.54, ln - 0.12):
            out += a.onto(p, q, ck.box(u - 0.09, -0.05, 3.1, u + 0.09, 0.0, 5.46, "wood_dk", c=0.018, d=1, skip="b"))

    for i in range(9):
        bx = x0 + 0.3 + i * (x1 - x0 - 0.6) / 8
        out += ck.box(bx - 0.08, y0 - 0.34, 2.68, bx + 0.08, y0, 2.86, "wood_dk", c=0.025, d=1, skip="b")

    out += a.gable(-y1, -(y0 - 0.2), x0 + 0.05, x1 - 0.05, 5.7, 2.55, "tile", "cream", over=0.2, rows=8, trim="wood_dk").rot(90)

    for dx in (-1.75, 1.8):
        yd = -1.95
        dm = ck.box(dx - 0.55, yd, 6.2, dx + 0.55, yd + 1.2, 7.0, "cream", c=0.025)
        dm += a.facade((dx - 0.55, yd - 0.01), (dx + 0.55, yd - 0.01), 6.2, 7.0, "cream", [a.win(0.55, 6.34, 0.66, 0.58, lintel="none", depth=0.08, trim="wood_dk")])
        dm += a.gable(dx - 0.55, dx + 0.55, yd - 0.01, yd + 1.5, 7.0, 0.5, "tile_dk", "cream", over=0.14, rows=2, trim="wood_dk", thick=0.08)
        out += dm

    for sx in (x0 + 0.5, x1 - 0.5):
        out += a.chimney(sx, 1.1, 6.4, 8.88, w=0.75, dp=0.55)

    out += a.disc((0.0, y0 - 0.26, 6.55), 0.34, "wood_dk", 10, 0.07)
    out += a.disc((0.0, y0 - 0.3, 6.55), 0.24, "glass_warm", 10, 0.05, d=1)
    out += ck.box(-1.45, y0 - 0.32, 3.0, 1.45, y0 - 0.22, 3.5, "navy", c=0.035)
    out += a.letters(-1.15, 1.15, y0 - 0.325, 3.12, 0.26, "gold", seed=9)
    out += ck.box(-0.8, -2.96, 0.0, 0.8, y0, 0.1, "stone_lt", c=0.025)

    for bx in (-1.05, 1.05):
        out += ck.box(bx - 0.04, y0 - 0.16, 2.1, bx + 0.04, y0, 2.18, "iron", d=1)
        out += ck.box(bx - 0.1, y0 - 0.28, 1.78, bx + 0.1, y0 - 0.1, 2.1, "glass_warm", c=0.04, d=1)
        out += ck.box(bx - 0.13, y0 - 0.31, 2.1, bx + 0.13, y0 - 0.07, 2.17, "iron_dk", c=0.025, d=1)

    for bx, by in ((-3.02, -2.74), (-2.55, -2.72), (3.05, -2.74)):
        out += ck.lathe([(0.0, 0.0, "wood_dk"), (0.17, 0.0, "wood"), (0.21, 0.2, "iron_dk"), (0.222, 0.27, "wood"), (0.222, 0.48, "iron_dk"), (0.21, 0.55, "wood"), (0.17, 0.74, "wood_lt"), (0.0, 0.72, "wood_lt")], 8, (bx, by, 0.0), smooth=False)

    out += a.downpipe(x1 - 0.12, y0 - 0.08, 0.2, 2.8)

    return out


def arcade():
    out = ck.Part()
    left = a.rect(-3.96, -0.92, -2.5, 2.44)
    main = a.rect(-2.5, -0.52, 4.46, 2.44)
    out += foundation(a.rect(-3.98, -0.94, 4.48, 2.46), -1.0, 0.1)
    out += a.shell(left, 0.1, 4.0, "teal", {0: [a.win(0.73, 0.9, 0.85, 1.4, bars="h", lintel="arch", tymp="glass_warm")], 3: [a.win(0.8, 1.0, 0.8, 1.35, lintel="arch", tymp="glass_warm", bars="h"), a.win(2.55, 1.0, 0.8, 1.35, lintel="arch", tymp="glass_warm", bars="h")], 2: [a.door(0.73, 0.8, 2.1, leaf="red_dk", fan=0.0)]})
    out += a.band(left, 0.1, 0.62, 0.05, "teal_dk", c=0.025, detail=1)
    out += a.band(left, 3.0, 3.16, 0.07, "trim", c=0.025, top="teal_dk", detail=1)
    out += a.onto(left[3], left[0], a.disc((1.68, -0.03, 3.55), 0.3, "gold", 10, 0.06) + a.disc((1.68, -0.07, 3.55), 0.2, "red", 10, 0.04, d=1))
    out += a.band(left, 3.86, 4.12, 0.1, "trim", c=0.04)
    out += a.hip(a.offset(left, -0.02), a.rect(-3.3, 0.5, -3.16, 1.0), 4.12, 4.48, "slate", rows=2)
    front = [a.door(1.6, 1.9, 2.75, leaf="red_dk", glazed=True, depth=0.45, fan=0.5), a.door(3.78, 2.0, 2.75, leaf="navy", glazed=True, depth=0.45, fan=0.5), a.win(5.9, 0.75, 1.5, 1.75, n=3, glass="glass_warm", lintel="flat")]
    side = [a.win(0.8, 0.9, 0.9, 1.3, bars="h"), a.win(2.2, 0.9, 0.9, 1.3, bars="h")]
    back = [a.door(1.4, 1.0, 2.2, leaf="iron"), a.win(4.5, 1.6, 1.2, 0.8)]
    out += a.facade(main[0], main[1], 0.1, 3.5, "cream", front)
    out += a.facade(main[1], main[2], 0.1, 3.5, "cream_dk", side)
    out += a.facade(main[2], main[3], 0.1, 3.5, "cream_dk", back)
    out += a.band(main, 3.4, 3.62, 0.12, "trim", c=0.04, top="slate_dk")
    out += a.slab(a.offset(main, -0.04), 3.56, "slate_dk")

    for px in (-2.32, -0.0, 2.25, 4.32):
        out += ck.box(px - 0.14, -0.62, 0.1, px + 0.14, -0.5, 3.4, "red", c=0.03, d=1, skip="bd")

    sign = [(-2.4, 3.15), (4.4, 3.15), (4.4, 3.9), (3.0, 3.9), (2.6, 4.3), (1.7, 4.46), (0.3, 4.46), (-0.6, 4.3), (-1.0, 3.9), (-2.4, 3.9)]
    out += ck.extrude(sign, -0.98, -0.6, "red", force=True, side="gold")
    out += a.letters(-1.8, 3.8, -0.985, 3.36, 0.42, "canvas", seed=21, n=6)
    out += a.disc((1.0, -1.0, 4.14), 0.22, "gold", 10, 0.06)

    bulbs = 17 if ck.LOD == 0 else 9

    for i in range(bulbs):
        bx = -2.25 + i * 6.5 / (bulbs - 1)

        for bz in (3.24,):
            out += ck.blob((bx, -1.01, bz), (0.07, 0.06, 0.07), "glass_warm", sub=0, d=1, seed=i, jitter=0.0)

    for i, (bx, bz) in enumerate(((-0.5, 4.22), (0.15, 4.34), (1.85, 4.34), (2.5, 4.22))):
        out += ck.blob((bx, -1.0, bz), (0.07, 0.06, 0.07), "glass_warm", sub=0, d=1, seed=i, jitter=0.0)

    out += a.striped_awning(-2.35, 2.28, -0.56, 2.98, 1.1, 0.28, "navy", "canvas", valance=0.18)

    for px in (-2.3, 2.2):
        out += ck.cyl((px, -1.86, 0.0), 0.06, 2.7, "trim", sides=6)
        out += ck.cbox(0.24, 0.24, 0.16, (px, -1.86, 0.0), "iron", c=0.03, d=1)

    for bx, c in ((2.95, "teal"), (3.85, "ochre")):
        out += ck.box(bx - 0.34, -1.55, 0.1, bx + 0.34, -0.75, 1.15, c, c=0.05)
        out += ck.box(bx - 0.28, -1.5, 1.15, bx + 0.28, -0.8, 1.7, "glass_lt", c=0.04, taper=(0.8, 0.7))
        out += ck.box(bx - 0.36, -1.57, 1.7, bx + 0.36, -0.73, 1.9, "red_dk", c=0.05, d=1)
        out += ck.box(bx - 0.2, -1.58, 0.65, bx + 0.2, -1.54, 0.9, "canvas", d=0)
        out += ck.box(bx - 0.18, -1.57, 0.25, bx + 0.18, -1.54, 0.45, "void", d=0)

    out += ck.box(-2.0, -1.95, 0.0, 1.9, -0.52, 0.09, "pave_band", c=0.02)
    out += ck.box(-0.4, 0.6, 3.56, 1.4, 1.9, 4.0, "steel", c=0.06, d=1)
    out += ck.cyl((2.9, 1.2, 3.56), 0.45, 0.42, "iron_lt", sides=8, rt=0.35, d=1)

    return out


def clock():
    out = ck.Part()
    cx, cy = 0.09, 0.09

    def sq(h):
        return a.rect(cx - h, cy - h, cx + h, cy + h)

    out += foundation(sq(1.72))
    out += a.band(sq(1.72), 0.1, 0.42, 0.0, "stone", c=0.05)
    door = [a.door(1.45, 1.1, 2.35, leaf="navy", lintel="arch", depth=0.3, lintel_col="stone_lt")]
    slit = [a.win(1.45, 1.1, 0.6, 1.3, bars="h", lintel="arch", lintel_col="stone_lt")]
    out += a.shell(sq(1.45), 0.42, 3.1, "stone", {0: door, 1: slit, 2: slit, 3: slit})
    out += a.band(sq(1.45), 3.05, 3.4, 0.2, "stone_lt", c=0.07)
    mid = [a.win(1.15, 4.0, 0.7, 1.35, bars="h", lintel="arch", lintel_col="trim"), a.win(1.15, 6.4, 0.7, 1.35, bars="h", lintel="arch", lintel_col="trim")]
    out += a.shell(sq(1.15), 3.4, 8.3, "coral", {i: mid for i in range(4)})
    out += a.band(sq(1.15), 5.85, 6.03, 0.1, "trim", c=0.035, top="coral_dk")

    for p in sq(1.15):
        for k in range(10):
            w = 0.34 if k % 2 == 0 else 0.25
            out += ck.cbox(w, w, 0.42, (p[0], p[1], 3.46 + k * 0.48), "trim", d=1, skip="d")

    out += a.band(sq(1.15), 8.25, 8.65, 0.3, "stone_lt", c=0.09, top="stone")
    out += a.shell(sq(1.3), 8.65, 10.9, "cream")

    for p in sq(1.3):
        out += ck.cbox(0.34, 0.34, 2.25, (p[0], p[1], 8.65), "trim", c=0.06, d=2)

    for i in range(4):
        face = ck.Part()
        fy = cy - 1.3
        face += a.disc((cx, fy - 0.03, 9.78), 0.92, "navy", 16, 0.08)
        face += a.disc((cx, fy - 0.08, 9.78), 0.74, "canvas", 16, 0.05, d=2)

        for k in range(12):
            ang = k * math.pi / 6
            rr = 0.06 if k % 3 == 0 else 0.032
            face += a.disc((cx + math.sin(ang) * 0.6, fy - 0.11, 9.78 + math.cos(ang) * 0.6), rr, "iron_dk", 6, 0.02, d=0)

        for ang, ln, w in ((-58, 0.38, 0.1), (58, 0.54, 0.07)):
            hand = ck.extrude([(-w / 2, -0.04), (w / 2, -0.04), (w * 0.2, ln), (-w * 0.2, ln)], fy - 0.145, fy - 0.115, "iron_dk", d=1)
            hand.rot(ang, "Y").move(cx, 0, 9.78)
            face += hand

        face += a.disc((cx, fy - 0.15, 9.78), 0.07, "gold", 8, 0.04, d=1)
        face.rot(90 * i, "Z", (cx, cy, 0))
        out += face

    out += a.band(sq(1.3), 10.85, 11.2, 0.25, "trim", c=0.08, top="stone")
    belfry = ck.ngon(1.05, 8, cx, cy)
    out += a.slab(belfry, 11.2, "stone")

    for p in belfry:
        out += ck.cyl((p[0], p[1], 11.2), 0.09, 0.95, "trim", sides=6, d=2)

    out += ck.cyl((cx, cy, 11.2), 0.5, 0.95, "void", sides=8, smooth=False)
    out += a.band(belfry, 12.1, 12.32, 0.14, "trim", c=0.05)
    out += a.hip(a.offset(belfry, 0.2), ck.ngon(0.4, 8, cx, cy), 12.32, 13.05, "teal", rows=3)
    out += a.hip(ck.ngon(0.4, 8, cx, cy), ck.ngon(0.05, 8, cx, cy), 13.05, 13.75, "teal_lt", rows=2, under=False)
    out += ck.blob((cx, cy, 13.9), (0.17, 0.17, 0.17), "gold", sub=1, jitter=0.0)

    return out


def kiosk():
    out = ck.Part()
    body = [(-1.0, -1.12), (1.5, -1.12), (2.0, -0.5), (2.0, 1.0), (1.5, 1.55), (-1.0, 1.55), (-1.5, 1.0), (-1.5, -0.5)]
    out += a.band(body, -0.5, 0.14, 0.08, "stone", c=0.035, top="stone_lt")
    w0 = 2.5
    openings = {0: [a.win(w0 / 2, 1.05, 2.15, 1.2, bars="none", glass="void", lintel="flat", depth=0.3, sill=False)], 2: [a.win(0.75, 1.15, 1.1, 1.0, n=2, glass="glass_warm")], 4: [a.door(1.25, 0.95, 2.15, leaf="red")], 6: [a.win(0.75, 1.15, 1.1, 1.0, n=2, glass="glass_warm")]}
    out += a.shell(body, 0.14, 2.45, "canvas", openings)
    n = len(body)

    for i in range(n):
        p, q = body[i], body[(i + 1) % n]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        stripes = max(2, int(ln / 0.32))
        part = ck.Part()

        if i != 4:
            for k in range(stripes):
                if k % 2 == 0:
                    part += ck.box(k * ln / stripes, -0.03, 0.18, (k + 1) * ln / stripes, 0.0, 0.92, "teal", d=1, skip="b")

        out += a.onto(p, q, part)

    out += ck.box(-0.72, -1.4, 0.94, 1.22, -1.0, 1.06, "wood_lt", c=0.03)

    for bx in (-0.5, 1.0):
        out += ck.box(bx - 0.05, -1.32, 0.68, bx + 0.05, -1.1, 0.94, "wood_dk", d=1, taper=(1.0, 1.6))

    for i, (bx, c) in enumerate(((-0.45, "red"), (-0.15, "gold"), (0.18, "canvas"), (0.75, "teal_lt"))):
        out += ck.cyl((bx, -1.2, 1.06), 0.08, 0.2 + 0.04 * (i % 2), c, sides=6, d=0)

    out += a.striped_awning(-1.05, 1.55, -1.12, 2.55, 0.85, 0.34, "red", "canvas", valance=0.18)
    out += a.band(body, 2.45, 2.68, 0.16, "navy", c=0.045)
    top = [(-0.15, -0.2), (0.65, -0.2), (0.75, -0.05), (0.75, 0.45), (0.65, 0.6), (-0.15, 0.6), (-0.25, 0.45), (-0.25, -0.05)]
    out += a.hip(a.offset(body, 0.2), top, 2.68, 3.06, "teal", rows=3, cap="teal_dk")
    out += ck.box(-0.75, -1.0, 2.72, 1.25, -0.82, 3.12, "cream_lt", c=0.04)
    out += a.letters(-0.55, 0.65, -1.005, 2.82, 0.2, "red_dk", seed=6)
    out += ck.tube([(0.98, -1.08, 2.82), (0.98, -1.08, 3.1)], [0.012, 0.13], 8, "ochre", caps=(False, True), smooth=False)
    out += ck.blob((0.98, -1.08, 3.17), (0.15, 0.13, 0.13), "bloom_lt", sub=1, jitter=0.08, d=1)
    out += ck.blob((0.98, -1.08, 3.33), (0.1, 0.1, 0.11), "cream_lt", sub=0, jitter=0.08, d=1)
    out += ck.cyl((0.25, 0.2, 3.06), 0.16, 0.38, "iron_lt", sides=6, d=1)
    out += ck.box(-1.98, -1.92, 0.0, -1.35, -1.3, 0.86, "trim", c=0.06)
    out += ck.box(-1.95, -1.89, 0.86, -1.38, -1.33, 0.95, "navy_lt", c=0.03, d=1)
    out += ck.box(-1.88, -1.945, 0.3, -1.45, -1.92, 0.65, "red_lt", d=0)
    out += ck.box(1.75, -1.75, 0.0, 2.35, -1.65, 0.95, "wood_dk", c=0.02, shear=(0.0, 0.18))
    out += ck.box(1.82, -1.77, 0.18, 2.28, -1.72, 0.85, "iron_dk", d=1, shear=(0.0, 0.14))

    return out


def toilets():
    out = ck.Part()
    main = a.rect(-1.9, -0.95, 2.4, 1.92)
    out += foundation(a.rect(-1.98, -1.0, 2.46, 1.98), -0.8, 0.1)
    front = [a.door(0.75, 0.95, 2.1, leaf="navy", lintel="flat", depth=0.28, fan=0.0), a.door(3.55, 0.95, 2.1, leaf="red", lintel="flat", depth=0.28, fan=0.0), a.win(2.15, 1.75, 0.9, 0.45, n=3, lintel="flat")]
    high = [a.win(1.45, 1.75, 1.2, 0.45, n=3)]
    out += a.shell(main, 0.1, 1.2, "teal", {0: [front[0], front[1]]})
    out += a.shell(main, 1.2, 2.55, "cream", {0: front, 1: high, 2: [a.win(2.15, 1.75, 1.6, 0.45, n=4)], 3: high})
    out += a.band(main, 1.14, 1.26, 0.04, "trim", c=0.015, top="teal_dk", detail=1)

    for i in range(4):
        p, q = main[i], main[(i + 1) % 4]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        part = ck.Part()

        for k in range(1, int(ln / 0.36)):
            u = k * ln / int(ln / 0.36)

            if i == 0 and (abs(u - 0.75) < 0.6 or abs(u - 3.55) < 0.6):
                continue

            part += ck.box(u - 0.012, -0.012, 0.12, u + 0.012, 0.0, 1.14, "teal_dk", d=0, skip="btd")

        out += a.onto(p, q, part)

    out += a.band(a.rect(-1.9, -0.95, 2.4, 1.92), 2.55, 2.76, 0.06, "trim", c=0.04)
    roof = a.rect(-2.0, -1.46, 2.46, 1.98)
    out += a.hip(roof, a.rect(-1.2, -0.2, 1.66, 0.7), 2.76, 3.2, "slate", rows=3, cap="slate_dk")
    out += ck.box(0.55, 0.0, 3.18, 0.95, 0.45, 3.2, "glass_lt", d=0)

    for px in (-1.8, 0.25, 2.25):
        out += ck.cyl((px, -1.34, 0.0), 0.085, 2.76, "trim", sides=8, rt=0.07, d=2)
        out += ck.cbox(0.26, 0.26, 0.24, (px, -1.34, 0.0), "stone", c=0.03, d=1)

    for dx, c in ((-1.15, "navy_lt"), (1.65, "red_lt")):
        out += a.disc((dx - 0.0, -0.99, 2.36), 0.15, c, 10, 0.05, d=1)
        out += a.disc((dx, -1.02, 2.36), 0.06, "canvas", 6, 0.03, d=0)

    out += ck.box(-0.45, -1.45, 0.0, 1.0, -1.0, 0.08, "walk", c=0.02)
    out += ck.cyl((0.25, 1.2, 2.9), 0.18, 0.28, "steel", sides=8, d=1)

    return out


def bandstand():
    out = ck.Part()
    base = ck.ngon(3.98, 8)
    deck = ck.ngon(3.72, 8)
    out += a.band(base, 0.0, 0.22, -0.02, "stone", c=0.04, top="stone_lt")
    out += a.band(deck, 0.22, 0.4, 0.02, "trim", c=0.04, cap=False)
    r = 3.72
    pts = ck.ngon(r, 8)

    for i in range(8):
        p, q = pts[i], pts[(i + 1) % 8]
        out.append(ck.Poly([(0, 0, 0.4), (p[0], p[1], 0.4), (q[0], q[1], 0.4)], "wood_lt" if i % 2 == 0 else "wood"))

    cols = ck.ngon(3.36, 8)

    for p in cols:
        out += ck.cbox(0.32, 0.32, 0.34, (p[0], p[1], 0.4), "navy_dk", c=0.04, d=1)
        out += ck.cyl((p[0], p[1], 0.7), 0.105, 2.95, "trim", sides=8, rt=0.085, d=2)
        out += ck.cbox(0.28, 0.28, 0.14, (p[0], p[1], 3.58), "trim", c=0.035, d=1)

    for i in range(8):
        p, q = cols[i], cols[(i + 1) % 8]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])

        if i not in (5,):
            part = ck.box(0.1, -0.05, 1.22, ln - 0.1, 0.07, 1.32, "navy", c=0.025, d=2)
            part += ck.box(0.1, -0.04, 0.4, ln - 0.1, 0.06, 0.5, "navy", c=0.02, d=1)
            n = 8 if ck.LOD == 0 else 4

            for k in range(n):
                u = 0.1 + (k + 0.5) * (ln - 0.2) / n
                part += ck.tube([(u, 0.01, 0.5), (u, 0.01, 0.86), (u, 0.01, 1.22)], [0.022, 0.05, 0.022], 4, "trim", caps=(False, False), smooth=False, d=1)

            out += a.onto(p, q, part)

        frieze = ck.box(0.0, -0.06, 3.62, ln, 0.08, 3.92, "teal", c=0.03)
        n = 7

        for k in range(n):
            u = 0.15 + (k + 0.5) * (ln - 0.3) / n
            frieze += ck.extrude([(u - 0.13, 3.62), (u - 0.07, 3.46), (u, 3.4), (u + 0.07, 3.46), (u + 0.13, 3.62)], -0.04, 0.0, "trim", d=1)

        out += a.onto(p, q, frieze)

    eave = ck.ngon(3.92, 8)
    knee = ck.ngon(2.3, 8)
    top = ck.ngon(0.9, 8)
    out += a.band(ck.ngon(3.8, 8), 3.92, 4.08, 0.04, "trim", c=0.035, cap=False)
    out.append(ck.Poly([(p[0], p[1], 3.92) for p in reversed(ck.ngon(3.84, 8))], "trim_dk"))

    for ring0, ring1, z0, z1 in ((eave, knee, 4.08, 4.62), (knee, top, 4.62, 5.48)):
        for i in range(8):
            j = (i + 1) % 8
            col = "red" if i % 2 == 0 else "canvas"
            out.append(ck.Poly([(ring0[i][0], ring0[i][1], z0), (ring0[j][0], ring0[j][1], z0), (ring1[j][0], ring1[j][1], z1), (ring1[i][0], ring1[i][1], z1)], col))

    out += a.ridge_caps(eave, knee, 4.08, 4.62, "trim", 0.06)
    out += a.ridge_caps(knee, top, 4.62, 5.48, "trim", 0.06)
    drum = ck.ngon(0.93, 8)
    out += a.shell(drum, 5.45, 5.72, "teal_dk")
    out += a.hip(ck.ngon(1.02, 8), ck.ngon(0.06, 8), 5.72, 6.2, "teal", rows=3)
    out += ck.cyl((0, 0, 6.15), 0.04, 0.16, "gold", sides=5, d=1)
    out += ck.blob((0, 0, 6.34), (0.13, 0.13, 0.13), "gold", sub=1, jitter=0.0, d=1)
    out += ck.box(-0.9, -3.97, 0.0, 0.9, -3.55, 0.16, "stone_lt", c=0.025)

    return out


ALL = {
    "terrace_a": (terrace_a, {}),
    "terrace_b": (terrace_b, {}),
    "terrace_c": (terrace_c, {}),
    "terrace_d": (terrace_d, {}),
    "corner": (corner, {}),
    "hotel": (hotel, {}),
    "tavern": (tavern, {}),
    "arcade": (arcade, {}),
    "clock": (clock, {}),
    "kiosk": (kiosk, {}),
    "toilets": (toilets, {}),
    "bandstand": (bandstand, {}),
}
