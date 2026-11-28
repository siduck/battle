import math

import arch as a
import ck
import common as c

W = ck.Part


def L():
    return ck.LOD


def sign(x0, x1, y0, y1, z0, z1, frame, face, words, h, back=False, lamps=True):
    out = ck.box(x0, y0, z0, x1, y1, z1, frame, c=0.06)
    zt = (z0 + z1) / 2 - h / 2
    out += c.plate(x0 + 0.09, x1 - 0.09, z0 + 0.09, z1 - 0.09, y0 - 0.006, face)
    total = sum(len(w) for w, _ in words) + len(words) - 1
    cur = x0 + 0.16
    span = x1 - x0 - 0.32

    for word, col in words:
        share = span * len(word) / total
        out += c.text(word, cur + share / 2, y0 - 0.018, zt, h, col, w=share)
        cur += share + span / total

    if back:
        out += c.plate(x0 + 0.09, x1 - 0.09, z0 + 0.09, z1 - 0.09, y1 + 0.006, face, 1)

    if lamps:
        n = int((x1 - x0) / 0.28)
        out += c.bulbs([(x0 + 0.1 + (x1 - x0 - 0.2) * i / n, z) for i in range(n + 1) for z in (z0 + 0.045, z1 - 0.045)], y0 - 0.008, 0.03, "mustard")

    return out


def wallpoly(poly, z0, z1, col, openings=None):
    out = W()
    n = len(poly)

    for i in range(n):
        ops = (openings or {}).get(i, ())
        out += a.facade(poly[i], poly[(i + 1) % n], z0, z1, col, ops)

    return out


def rounded(x0, y0, x1, y1, r, z0, z1, col, front=None, back=None, left=None, right=None, frontcol=None):
    poly = c.roundrect(x0, y0, x1, y1, r, 4)
    n = len(poly)
    seg = n // 4
    straight = {seg - 1: "right", 2 * seg - 1: "back", 3 * seg - 1: "left", n - 1: "front"}
    ops = {"front": front, "back": back, "left": left, "right": right}
    out = W()

    for i in range(n):
        side = straight.get(i)
        p, q = poly[i], poly[(i + 1) % n]
        colour = frontcol if side == "front" and frontcol else col

        if side and ops[side]:
            out += a.facade(p, q, z0, z1, colour, ops[side])
        else:
            out += c.face([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)], colour, (q[1] - p[1], p[0] - q[0], 0))

    return out


def motel():
    out = W()
    teal = "teal"
    front = [a.win(3.5 - 0.96, 0.68, 2.9, 1.58, n=3, trim=teal, sill_col=teal, lintel_col=teal, fw=0.1),
             a.door(3.5 + 1.67, 0.92, 2.22, leaf="white_dk", trim=teal, glazed=True, lintel_col=teal, fan=0)]
    back = [a.door(5.9, 0.95, 2.2, leaf="teal_dk", trim="white_dk", lintel_col="white_dk")]
    side = [a.win(2.2, 1.45, 0.9, 0.8, trim=teal, sill_col=teal, lintel_col=teal),
            a.win(4.9, 1.45, 0.9, 0.8, trim=teal, sill_col=teal, lintel_col=teal)]
    out += rounded(-4.0, -3.35, 4.0, 4.0, 0.5, 0.0, 2.9, "white", front, back, side, side, frontcol="white_dk")
    base = c.roundrect(-4.0, -3.35, 4.0, 4.0, 0.5, 3)
    out += c.ledge(base, 0.0, 0.14, 0.06, "stone_dk", c=0.02)
    out += c.ledge(base, 2.86, 3.08, 0.1, teal, c=0.05)
    out += c.ledge(base, 3.08, 3.14, 0.03, "teal_deep", c=0.0)
    out += a.parapet(base, 3.08, 0.36, "white", "white_lt", thick=0.24)
    out += c.slabs([(a.offset(base, -0.22), 3.22), (a.offset(base, -0.22), 3.221)], "char", top="char_lt")

    for x in (-3.43, 3.43):
        out += ck.box(x - 0.16, -3.42, 0.14, x + 0.16, -3.3, 2.86, "white", c=0.05)
        out += ck.box(x - 0.05, -3.445, 0.2, x + 0.05, -3.41, 2.8, teal, d=0)

    out += ck.box(0.85, -4.0, 0.0, 2.5, -3.35, 0.1, "conc", c=0.03)
    out += ck.box(-2.5, -3.5, 0.5, 0.55, -3.36, 0.62, teal, c=0.02, d=0)
    out += sign(0.55, 2.8, -3.52, -3.3, 2.5, 3.18, "rust", "sign", [("OFFICE", "orange")], 0.36)
    out += sign(-1.89, 0.78, -3.2, -2.96, 3.7, 4.34, "rust", "sign", [("NO", "red"), ("VACANCY", "teal_lt")], 0.3, back=True)

    for x in (-1.45, 0.35):
        out += ck.box(x - 0.05, -3.13, 3.4, x + 0.05, -3.03, 3.72, "steel_dk")

    out += c.lantern(2.5, -3.35, 1.8)
    out += c.ac_unit(-1.8, 1.0, 3.22, 1.2, 0.9, 0.5)
    out += c.vent_pipe(2.2, 2.4, 3.22, 0.45)
    out += c.wall_vent(-2.6, 4.0, 2.2, facing=1)
    out += c.wall_vent(1.4, 4.0, 0.7, 0.6, 0.45, facing=1)
    out += a.downpipe(-3.2, 4.07, 0.0, 2.9, "steel_dk")

    return out


def rooms():
    out = W()
    doors = [-7.0, -3.0, 1.0, 5.0, 9.0]
    wins = [-8.92, -4.92, -0.92, 3.08, 7.08]
    fy = -2.0
    front = []

    for dx, wx in zip(doors, wins):
        front.append(a.win(wx + 10.0, 1.05, 1.6, 1.28, n=2, trim="wood", sill_col="wood_lt", lintel_col="wood", glass="glass"))
        front.append(a.door(dx + 10.0, 0.9, 2.24, leaf="teal_dk", trim="teal", lintel_col="teal", fan=0, depth=0.12))

    back = [a.win(2.0 + 4.0 * i, 2.0, 0.55, 0.35, n=1, trim="white_dk", sill=False, lintel=None) for i in range(5)]
    side = [a.win(3.0, 1.2, 1.0, 0.9, trim="teal", sill_col="teal", lintel_col="teal")]
    out += a.shell(a.rect(-10.0, fy, 10.0, 4.0), 0.0, 2.75, "white", {0: front, 2: back, 1: side, 3: side})
    out += ck.box(-10.0, -4.0, 0.0, 10.0, fy, 0.15, "mortar", c=0.03, skip="b")

    if L() == 0:
        for i in range(21):
            x = -10.0 + i
            out += c.face([(x - 0.015, -4.0, 0.153), (x + 0.015, -4.0, 0.153), (x + 0.015, fy, 0.153), (x - 0.015, fy, 0.153)], "joint", (0, 0, 1), cast=False)

    for x in (-9.85, -6.0, -2.0, 2.0, 6.0, 9.85):
        out += ck.box(x - 0.065, -3.92, 0.15, x + 0.065, -3.79, 2.75, "teal_dk", c=0.025)
        out += ck.box(x - 0.12, -3.97, 0.15, x + 0.12, -3.74, 0.33, "white_dk", c=0.03, d=0)
        out += c.beam((x, -3.84, 2.4), (x, -3.45, 2.74), 0.06, "teal_dk", d=0)

    roof = a.rect(-10.0, -4.0, 10.0, 4.0)
    out += c.ledge(roof, 2.75, 3.0, 0.02, "teal", top="white_dk", c=0.04)
    out += c.ledge(a.rect(-9.9, -3.9, 9.9, 3.9), 2.99, 3.03, 0.0, "white_lt", top="white", c=0.0)

    for i in range(5):
        dx, wx = doors[i], wins[i]
        out += ck.box(wx - 0.38, fy - 0.2, 0.42, wx + 0.38, fy + 0.02, 0.9, "steel_lt", c=0.04, d=1)

        for k in range(3):
            out += ck.box(wx - 0.3, fy - 0.215, 0.5 + k * 0.12, wx + 0.3, fy - 0.19, 0.545 + k * 0.12, "iron_lt", d=0, skip="b")

        for s in (-1, 1):
            x = wx + s * 0.58
            out.extend(c.plate(x - 0.17, x + 0.17, 1.1, 2.28, fy + 0.11, "awn_rust" if i % 2 else "tan", d=0))

        out += ck.box(dx - 0.14, fy - 0.04, 2.38, dx + 0.14, fy, 2.62, "off_white", c=0.02, d=0)
        out += c.text(str(i + 1), dx, fy - 0.052, 2.42, 0.17, "sign")
        out += c.lantern(dx - 0.72, fy, 1.7)
        out += ck.box(dx - 0.5, fy - 0.55, 0.15, dx + 0.5, fy - 0.05, 0.18, "awn_rust", d=0)
        out += ck.box(2.0 + 4.0 * i - 10.0 - 0.5, 3.98, 0.0, 2.0 + 4.0 * i - 10.0 + 0.5, 4.04, 0.5, "white_dk", c=0.02, d=0)

    for i in range(6):
        x = -10.0 + 4.0 * i + (0.1 if i == 0 else -0.1 if i == 5 else 0)
        out += ck.box(x - 0.1, fy - 0.07, 0.15, x + 0.1, fy + 0.02, 2.75, "white_dk", c=0.025, d=1)

    return out


def canopy():
    out = W()
    deck = c.roundrect(-5.93, -3.93, 5.93, 3.93, 2.4, 6)
    out += c.slabs([(a.offset(deck, -0.05), 4.5), (deck, 4.55)], "off_white")
    out += c.slabs([(deck, 4.55), (deck, 4.64), (a.offset(deck, -0.02), 4.64)], "off_white")
    out += c.slabs([(a.offset(deck, -0.02), 4.64), (a.offset(deck, -0.02), 5.32)], "teal_deep")
    out += c.ledge(deck, 5.32, 5.46, 0.06, "off_white", top="off_white", c=0.03)
    out += c.ledge(deck, 4.88, 5.08, 0.0, "teal", c=0.0)
    out += c.slabs([(a.offset(deck, -0.3), 5.46), (a.offset(deck, -0.55), 5.6), (a.offset(deck, -1.5), 5.66)], "iron_lt", top="iron_lt")
    out += c.slabs([(a.offset(deck, -0.02), 5.462), (a.offset(deck, -0.3), 5.462)], "iron")
    out += c.face([(p[0], p[1], 4.5) for p in a.offset(deck, -0.05)], "white_dk", (0, 0, -1))
    out += c.text("GAS", 0.0, -4.02, 4.72, 0.52, "off_white")

    for x in (-4.5, -1.5, 1.5, 4.5):
        for y in (-2.4, 2.4):
            out += ck.box(x - 0.42, y - 0.47, 4.44, x + 0.42, y + 0.47, 4.52, "steel", c=0.02, d=1)
            out += c.face([(x - 0.32, y - 0.36, 4.435), (x + 0.32, y - 0.36, 4.435), (x + 0.32, y + 0.36, 4.435), (x - 0.32, y + 0.36, 4.435)], "lamp_glass", (0, 0, -1), ao=False)

    for x in (-2.0, 2.0):
        isle = c.roundrect(x - 0.6, -3.0, x + 0.6, 3.0, 0.45, 4)
        out += c.slabs([(isle, 0.0), (isle, 0.1), (a.offset(isle, -0.05), 0.15)], "conc_lt", top="conc_lt")

        for y in (-2.62, 2.62):
            for k in range(3):
                col = "red" if k % 2 == 0 else "off_white"
                out += ck.box(x - 0.36 + k * 0.24, y - 0.13, 0.15, x - 0.12 + k * 0.24, y + 0.13, 0.19, col, d=0)

        for y in (-1.6, 1.6):
            out += ck.lathe([(0.27, 0.14, "off_white"), (0.27, 0.24, "off_white"), (0.235, 0.3, "off_white"), (0.235, 0.9, "steel_lt"), (0.2, 0.98)], 10, (x, y, 0), smooth=False)
            out += ck.cyl((x, y, 0.96), 0.17, 3.45, "iron_lt", sides=10)
            out += ck.box(x - 0.29, y - 0.31, 4.36, x + 0.29, y + 0.31, 4.5, "steel", c=0.04)
            out += ck.cyl((x, y, 1.45), 0.2, 0.12, "teal", sides=10, d=1)

        out += ck.box(x - 0.12, -0.18, 0.15, x + 0.12, 0.18, 1.0, "teal_dk", c=0.05, d=1)
        out += ck.box(x - 0.16, -0.22, 1.0, x + 0.16, 0.22, 1.08, "off_white", c=0.02, d=0)

    return out


def garage():
    out = W()
    poly = c.roundrect(-3.96, -3.96, 3.96, 3.96, 0.5, 4)
    n = len(poly)
    seg = n // 4
    straight = {seg - 1: "right", 2 * seg - 1: "back", 3 * seg - 1: "left", n - 1: "front"}
    side_ops = [a.win(3.2 + k * 0.95, 3.15, 0.6, 0.72, n=1, trim="iron_lt", sill_col="steel", lintel=None) for k in range(3)]
    side_ops.append(a.door(1.0, 0.85, 2.15, leaf="rust_dk", trim="steel", lintel_col="steel", fan=0))

    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        side = straight.get(i)

        if side == "front":
            width = q[0] - p[0]
            hole = {"x0": -1.76 - p[0], "x1": 1.76 - p[0]}
            out += a.onto(p, q, a.wall_face(hole["x0"], 0.0, 4.7, [], "white"))
            out += a.onto(p, q, a.wall_face(width - hole["x1"], 0.0, 4.7, [], "white").move(x=hole["x1"]))
            out += c.plate(-1.76, 1.76, 3.4, 4.7, p[1], "white")
        elif side == "right":
            out += a.facade(p, q, 0.0, 4.7, "white", side_ops)
        else:
            out += c.face([(p[0], p[1], 0), (q[0], q[1], 0), (q[0], q[1], 4.7), (p[0], p[1], 4.7)], "white", (q[1] - p[1], p[0] - q[0], 0))

    x0, x1, y0, y1, zc = -3.5, 3.5, -3.4, 3.4, 4.62
    out += c.plate(x0, x1, 0.0, zc, y1, "tan_dk", -1)
    out += c.face([(x0, y0, 0), (x0, y1, 0), (x0, y1, zc), (x0, y0, zc)], "char_lt", (1, 0, 0))
    out += c.face([(x1, y0, 0), (x1, y1, 0), (x1, y1, zc), (x1, y0, zc)], "char_lt", (-1, 0, 0))
    out += c.face([(x0, y0, zc), (x1, y0, zc), (x1, y1, zc), (x0, y1, zc)], "wood_dk", (0, 0, -1))
    out += c.plate(x0, -1.76, 0.0, zc, y0, "char", 1)
    out += c.plate(1.76, x1, 0.0, zc, y0, "char", 1)
    out += c.plate(-1.76, 1.76, 3.4, zc, y0, "char", 1)

    for s in (-1, 1):
        x = s * 1.76
        out += c.face([(x, -3.96, 0), (x, y0, 0), (x, y0, 3.4), (x, -3.96, 3.4)], "conc_dk", (-s, 0, 0))
        out += ck.box(x - 0.07, -4.02, 0.0, x + 0.07, -3.9, 3.68, "iron_lt", c=0.02)

        for k in range(5):
            out += ck.box(x - 0.075 + s * 0.14, -4.0, 0.15 + k * 0.2, x + 0.075 + s * 0.14, -3.95, 0.25 + k * 0.2, "mustard" if k % 2 == 0 else "sign", d=0, skip="b")

    out += c.face([(-1.76, -3.96, 3.4), (1.76, -3.96, 3.4), (1.76, y0, 3.4), (-1.76, y0, 3.4)], "char", (0, 0, -1))
    out += ck.box(-1.76, -3.9, 0.0, 1.76, y0, 0.02, "iron_lt", d=0)
    out += c.face([(x0, y0, 0.02), (x1, y0, 0.02), (x1, y1, 0.02), (x0, y1, 0.02)], "iron_lt", (0, 0, 1))
    out += ck.box(-1.82, -4.04, 3.4, 1.82, -3.9, 3.7, "mortar", c=0.04)

    for k in range(6 if L() == 0 else 2):
        step = 0.115 if L() == 0 else 0.345
        z = 2.71 + k * step
        out += ck.box(-1.72, -3.9, z, 1.72, -3.8, z + step - 0.012, "steel_lt" if k % 2 == 0 else "steel", c=0.018)

    out += ck.box(-1.72, -3.93, 2.65, 1.72, -3.79, 2.72, "iron", d=1)
    teal = c.roundrect(-3.97, -3.97, 3.97, 3.97, 0.52, 4)
    out += c.ledge(teal, 4.62, 4.74, 0.0, "teal_dk", c=0.0)
    out += c.slabs([(teal, 4.74), (a.offset(teal, 0.03), 4.9), (a.offset(teal, 0.03), 5.72), (a.offset(teal, -0.03), 5.9), (a.offset(teal, -0.14), 6.0), (a.offset(teal, -0.27), 5.96), (a.offset(teal, -0.32), 4.95)], ["teal", "teal", "teal", "teal_lt", "teal_lt", "teal_deep"])
    out += c.face([(p[0], p[1], 4.95) for p in a.offset(teal, -0.31)], "tar_lt", (0, 0, 1))
    out += c.ledge(teal, 5.15, 5.23, 0.05, "off_white", c=0.0)
    out += c.text("SERVICE", 0.0, -4.07, 4.25, 0.34, "teal_deep")

    for x in (-3.05, -2.45, 2.45, 3.05):
        out += ck.box(x - 0.09, -4.0, 0.25, x + 0.09, -3.93, 4.55, "white_dk", c=0.025, d=1)

    for x in (-2.0, 0.0, 2.0):
        out += ck.box(x - 0.09, 3.93, 0.25, x + 0.09, 4.0, 4.55, "white_dk", c=0.025, d=1)

    for s in (-1, 1):
        out += ck.box(min(s * 1.9, s * 3.55), -4.0, 0.0, max(s * 1.9, s * 3.55), -3.92, 0.22, "mortar", c=0.02, d=1)

    out += ck.box(-3.5, 2.75, 0.82, 0.9, y1, 0.92, "wood_lt", c=0.02)
    out += ck.box(-3.5, 1.1, 0.82, -2.9, 2.75, 0.92, "wood_lt", c=0.02)
    out += ck.box(-3.45, 2.85, 0.22, 0.85, y1, 0.27, "wood", d=0)

    for x, y in ((-3.1, 2.8), (-1.4, 2.8), (0.8, 2.8), (-2.95, 1.15)):
        out += ck.box(x - 0.04, y, 0.0, x + 0.04, y + 0.08, 0.82, "wood", d=0)

    out += ck.box(-3.35, y1 - 0.05, 1.08, 0.55, y1, 2.28, "tan", d=1)

    if L() == 0:
        for i, (x, w, h) in enumerate(((-3.0, 0.09, 0.6), (-2.7, 0.08, 0.5), (-2.35, 0.3, 0.14), (-1.8, 0.07, 0.7), (-1.5, 0.07, 0.55), (-1.0, 0.45, 0.45), (-0.3, 0.1, 0.62), (0.15, 0.25, 0.2))):
            out += ck.box(x, y1 - 0.09, 1.9 - h, x + w, y1 - 0.04, 1.9, "iron" if i % 3 else "red_dk", c=0.02)
            out += ck.box(x - 0.03, y1 - 0.08, 1.9, x + w + 0.03, y1 - 0.04, 2.0, "steel", d=0)

        out += ck.torus((2.7, y1 - 0.14, 1.9), 0.36, 0.11, "rubber", segs=12, sides=5, axis="Y")

    out += ck.box(-2.6, 2.85, 0.92, -1.9, 3.25, 1.22, "red", c=0.04, d=1)
    out += ck.box(-0.8, 2.9, 0.92, -0.45, 3.2, 1.1, "drum", c=0.03, d=1)
    out += ck.cyl((2.9, 2.8, 0.02), 0.32, 0.9, "drum", sides=10, d=1)
    out += ck.cyl((2.2, 3.0, 0.02), 0.28, 0.75, "red_dk", sides=10, d=1)
    out += c.lantern(2.5, -3.97, 2.7)
    out += a.downpipe(3.2, 4.04, 0.0, 4.7, "steel_dk")
    out += c.ac_unit(1.6, 1.4, 4.95, 1.2, 1.0, 0.55)
    out += c.vent_pipe(-2.2, 2.0, 4.95, 0.5)

    return out


def porthole(x, y, z, r, facing, frame="steel_lt"):
    out = W()
    n = 10 if L() == 0 else 6
    ring = [(x + math.cos(2 * math.pi * i / n) * r, z + math.sin(2 * math.pi * i / n) * r) for i in range(n)]
    inner = [(x + math.cos(2 * math.pi * i / n) * r * 0.64, z + math.sin(2 * math.pi * i / n) * r * 0.64) for i in range(n)]
    yf = y + facing * 0.06

    if L() < 2:
        for i in range(n):
            j = (i + 1) % n
            out += c.face([(ring[i][0], y, ring[i][1]), (ring[j][0], y, ring[j][1]), (inner[j][0], yf, inner[j][1]), (inner[i][0], yf, inner[i][1])], frame, (0, facing, 0))

    out += c.face([(p[0], y + facing * 0.03, p[1]) for p in inner], "glass", (0, facing, 0))

    return out


def diner():
    out = W()
    body = c.roundrect(-7.9, -2.9, 7.9, 3.45, 1.15, 6)
    foot = a.offset(body, -0.1)
    out += c.slabs([(foot, 0.0), (foot, 0.34)], "rust_dk")
    out += c.slabs([(a.offset(body, -0.05), 0.34), (body, 0.45), (body, 1.55)], "off_white", bottom="iron")
    out += c.slabs([(a.offset(body, -0.02), 1.55), (a.offset(body, -0.02), 2.8)], "white_lt")
    out += c.slabs([(body, 2.8), (body, 3.0)], "off_white")

    for z0, z1, col in ((0.56, 0.7, "tile"), (0.86, 1.0, "tile"), (1.16, 1.22, "tile"), (1.5, 1.6, "steel"), (2.72, 2.8, "steel")):
        out += c.ledge(body, z0, z1, 0.05, col, c=0.025)

    eave = a.offset(body, 0.12)
    out += c.slabs([(body, 3.0), (eave, 3.08), (eave, 3.18), (body, 3.24), (a.offset(body, -0.12), 3.55), (a.offset(body, -0.42), 3.78), (a.offset(body, -0.55), 3.82)], "off_white", top="white_lt")
    top = c.roundrect(-7.0, -2.15, 7.0, 2.7, 0.7, 4)
    out += c.slabs([(top, 3.8), (top, 4.14), (a.offset(top, -0.12), 4.26), (a.offset(top, -0.5), 4.3)], "white", top="white")

    def framed(x, y, w, z0, z1, facing):
        yy = y + facing * 0.05
        part = ck.box(x - w / 2 - 0.08, min(y, yy), z0 - 0.08, x + w / 2 + 0.08, max(y, yy), z1 + 0.08, "off_white", c=0.03, d=1, skip="b" if facing < 0 else "f")
        part += c.plate(x - w / 2, x + w / 2, z0, z1, yy + facing * 0.006, "glass", facing)
        part += c.plate(x - w / 2, x + w / 2, z0 + (z1 - z0) * 0.62, z1, yy + facing * 0.012, "glass_lt", facing, d=0)

        return part

    for facing, y in ((-1, -2.92), (1, 3.47)):
        for x in (-3.83, 3.83):
            out += framed(x, y, 1.35, 1.72, 2.58, facing)

        spots = [-5.9, -1.75, 1.75, 5.9] + ([] if facing < 0 else [0.0])

        for x in spots:
            out += porthole(x, y, 2.15, 0.46, facing)

        for x in (-6.8, -4.9, -2.78, -0.82, 0.82, 2.78, 4.9, 6.8):
            out += ck.box(x - 0.045, min(y, y + facing * 0.07), 1.6, x + 0.045, max(y, y + facing * 0.07), 2.74, "steel", c=0.02, d=0)

    for s in (-1, 1):
        x = s * 7.92

        for y, w in ((-1.25, 1.05), (1.8, 1.05)):
            xa, xb = sorted((x, x + s * 0.05))
            out += ck.box(xa, y - w / 2 - 0.08, 1.64, xb, y + w / 2 + 0.08, 2.66, "off_white", d=1)
            out += c.face([(x + s * 0.056, y - w / 2, 1.72), (x + s * 0.056, y + w / 2, 1.72), (x + s * 0.056, y + w / 2, 2.58), (x + s * 0.056, y - w / 2, 2.58)], "glass", (s, 0, 0))

        out += porthole(0, 0, 2.15, 0.46, -1).rot(90 * s).move(x, 0.28, 0)

    n = len(body)

    for i in range(n):
        p, q = body[i], body[(i + 1) % n]
        corner = abs(p[0]) > 6.7 and (p[1] < -1.7 or p[1] > 2.2) and abs(q[0]) > 6.7 and (q[1] < -1.7 or q[1] > 2.2)

        if corner and abs(p[0] - q[0]) < 1.5:
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            nx, ny = q[1] - p[1], p[0] - q[0]
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln * 0.012, ny / ln * 0.012
            k = 0.9
            pa = (mx + (p[0] - mx) * k + nx, my + (p[1] - my) * k + ny)
            pb = (mx + (q[0] - mx) * k + nx, my + (q[1] - my) * k + ny)
            out += c.face([(pa[0], pa[1], 1.68), (pb[0], pb[1], 1.68), (pb[0], pb[1], 2.64), (pa[0], pa[1], 2.64)], "glass", (nx, ny, 0))

    out += ck.box(-0.62, -3.0, 0.45, 0.62, -2.86, 2.68, "steel", c=0.03)

    for i in range(2):
        for k in range(8):
            col = "sign" if (i + k) % 2 == 0 else "off_white"
            out += c.plate(-0.48 + i * 0.48, i * 0.48, 0.5 + k * 0.26, 0.76 + k * 0.26, -3.008, col)

    out += ck.box(0.42, -3.07, 1.3, 0.5, -3.0, 1.72, "steel_lt", c=0.02, d=0)
    out += ck.box(-0.85, -3.55, 0.0, 0.85, -2.9, 0.2, "conc", c=0.03)
    out += ck.box(-0.7, -3.28, 0.2, 0.7, -2.9, 0.43, "conc_lt", c=0.03)
    board = [(-2.2, 4.42), (-1.9, 4.3), (1.9, 4.3), (2.2, 4.42), (2.5, 4.75), (2.5, 5.35), (2.2, 5.64), (1.8, 5.72), (-1.8, 5.72), (-2.2, 5.64), (-2.5, 5.35), (-2.5, 4.75)]
    out += ck.extrude(board, 0.14, 0.38, "off_white", force=True)
    inner = [(x * 0.9, 5.01 + (z - 5.01) * 0.82) for x, z in board]
    mid = [(x * 0.86, 5.01 + (z - 5.01) * 0.72) for x, z in board]

    for facing, y in ((-1, 0.14), (1, 0.38)):
        out += c.face([(x, y + facing * 0.008, z) for x, z in inner], "awn_blue", (0, facing, 0))
        out += c.face([(x, y + facing * 0.016, z) for x, z in mid], "mustard", (0, facing, 0))
        word = c.text("DINER", 0.0, -0.03, 4.72, 0.58, "awn_blue", t=0.1)

        if facing > 0:
            word.rot(180)

        out += word.move(y=y + facing * 0.012)
        out += c.bulbs([(x * 0.95, 5.01 + (z - 5.01) * 0.91) for x, z in board], y + facing * 0.02, 0.05, "gold")

    for s in (-1, 1):
        for k, z in enumerate((4.7, 4.95, 5.2)):
            x0, x1 = sorted((s * 2.45, s * (3.35 - abs(k - 1) * 0.25)))
            out += ck.box(x0, 0.2, z, x1, 0.32, z + 0.09, "teal", d=1)

        out += ck.box(s * 1.6 - 0.07, 0.19, 3.9, s * 1.6 + 0.07, 0.33, 4.34, "steel_dk")

    for x, y in ((-5.0, 1.4), (5.2, -0.9)):
        out += c.ac_unit(x, y, 4.28, 1.3, 1.0, 0.42)

    out += c.vent_pipe(-3.2, -1.2, 4.28, 0.4)

    return out


def awning_run(x0, x1, y, z, col):
    return a.striped_awning(x0, x1, y, z, 1.0, 0.44, col, ck.shade(ck.rgb(col), 0.86), n=7, valance=0.24)


def gifts():
    out = W()

    for i in range(10 if L() == 0 else 1):
        w = 4.0 / (10 if L() == 0 else 1)
        y0 = -2.0 + i * w
        out += ck.box(-2.0, y0, 0.0, 2.0, y0 + w - 0.015, 0.15, "plank" if i % 2 == 0 else "wood_lt", c=0.015)

    def zr(y):
        return 3.2 - (y + 0.6) / 2.6 * 0.62

    def boards(p0, p1, z0, zt0, zt1, n, normal, lo="wood_dk", hi="wood"):
        part = W()
        n = n if L() == 0 else 1

        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            qa = (p0[0] + (p1[0] - p0[0]) * u0, p0[1] + (p1[1] - p0[1]) * u0)
            qb = (p0[0] + (p1[0] - p0[0]) * u1, p0[1] + (p1[1] - p0[1]) * u1)
            za = zt0 + (zt1 - zt0) * u0
            zb = zt0 + (zt1 - zt0) * u1
            part += c.face([(qa[0], qa[1], z0), (qb[0], qb[1], z0), (qb[0], qb[1], zb), (qa[0], qa[1], za)], lo if i % 2 == 0 else hi, normal)

        return part

    xl, xr, yf, yb = -1.84, 1.84, -0.55, 1.86
    out += boards((xl, yf), (xl, yb), 0.15, zr(yf), zr(yb), 9, (-1, 0, 0))
    out += boards((xl + 0.03, yf), (xl + 0.03, yb), 0.15, zr(yf), zr(yb), 6, (1, 0, 0), "wood_dk", "shingle_lt")
    out += boards((xr - 0.03, yf), (xr - 0.03, yb), 0.15, zr(yf), zr(yb), 6, (-1, 0, 0), "wood_dk", "shingle_lt")
    out += boards((xr, yf), (xr, yb), 0.15, zr(yf), zr(yb), 9, (1, 0, 0))
    out += boards((xl, yb), (xr, yb), 0.15, zr(yb), zr(yb), 14, (0, 1, 0))
    out += boards((xl, yb - 0.06), (xr, yb - 0.06), 0.15, zr(yb), zr(yb), 10, (0, -1, 0), "wood_dk", "shingle_lt")
    out += boards((xl, -0.58), (xr, -0.58), 0.15, 1.1, 1.1, 12, (0, -1, 0))
    out += c.face([(xl, -0.58, 1.09), (xr, -0.58, 1.09), (xr, -0.45, 1.09), (xl, -0.45, 1.09)], "wood", (0, 0, 1))

    for s in (-1, 1):
        x = s * 1.8
        out += ck.box(x - 0.09, -0.66, 0.15, x + 0.09, -0.46, 3.18, "wood_dk", c=0.025)
        out += ck.box(x - 0.08, 1.76, 0.15, x + 0.08, 1.93, zr(1.84) + 0.02, "wood_dk", c=0.025, d=1)

    out += ck.box(-1.86, -0.98, 1.08, 1.86, -0.5, 1.16, "plank", c=0.02)

    for x in (-1.4, 0.0, 1.4):
        out += c.beam((x, -0.6, 0.75), (x, -0.92, 1.08), 0.05, "iron", d=0)

    for k in range(3):
        out += ck.box(-1.5, -0.88, 1.16 + k * 0.09, -1.06, -0.58, 1.24 + k * 0.09, "awn_blue" if k % 2 == 0 else "tile", c=0.02, d=1)
        out += ck.box(-0.98, -0.86, 1.16 + k * 0.075, -0.58, -0.6, 1.225 + k * 0.075, "teal_dk" if k % 2 else "awn_rust", c=0.02, d=0)

    out += ck.torus((-0.18, -0.74, 1.2), 0.13, 0.035, "teal", segs=10, sides=5, axis="Z") if L() == 0 else W()
    out += ck.cyl((-0.18, -0.74, 1.16), 0.035, 0.22, "teal", sides=6, d=0)
    out += ck.box(0.62, -0.86, 1.16, 1.04, -0.66, 1.4, "sign", c=0.02, d=1)

    for i in range(3):
        for k in range(2):
            out += c.plate(0.65 + i * 0.13, 0.75 + i * 0.13, 1.18 + k * 0.11, 1.27 + k * 0.11, -0.866, "tan", d=0)

    out += ck.lathe([(0.07, 1.16, "rust"), (0.14, 1.24, "rust"), (0.13, 1.34, "rust"), (0.07, 1.4, "rust_dk"), (0.09, 1.45)], 8, (1.42, -0.74, 0), smooth=False)

    for z in (1.55, 2.05):
        out += ck.box(-1.5, 1.62, z, 1.5, 1.8, z + 0.05, "plank", d=1)

        for i in range(7):
            x = -1.3 + i * 0.43
            col = ("awn_rust", "teal_dk", "tan", "awn_blue", "cactus")[(i + int(z * 3)) % 5]
            out += ck.cyl((x, 1.68, z + 0.05), 0.1, 0.16 + 0.1 * (i % 3), col, sides=6, rt=0.07, caps=(False, True), d=0)

    slats = 11 if L() == 0 else 1
    w = 4.0 / slats

    for i in range(slats):
        x0, x1 = -2.0 + i * w, -2.0 + (i + 1) * w - (0.02 if slats > 1 else 0)
        lift = 0.0 if i % 2 == 0 else 0.025
        col = "plank" if i % 3 == 0 else "wood_lt"
        za, zb = zr(-0.6) + lift, zr(2.0) + lift
        out += c.face([(x0, -0.6, za + 0.05), (x1, -0.6, za + 0.05), (x1, 2.0, zb + 0.05), (x0, 2.0, zb + 0.05)], col, (0, 0, 1))
        out += c.face([(x0, -0.6, za - 0.02), (x1, -0.6, za - 0.02), (x1, 2.0, zb - 0.02), (x0, 2.0, zb - 0.02)], "wood_dk", (0, 0, -1))
        out += c.face([(x0, 2.0, zb - 0.02), (x1, 2.0, zb - 0.02), (x1, 2.0, zb + 0.05), (x0, 2.0, zb + 0.05)], col, (0, 1, 0))

        for xx, s in ((x0, -1), (x1, 1)):
            out += c.face([(xx, -0.6, za - 0.02), (xx, 2.0, zb - 0.02), (xx, 2.0, zb + 0.05), (xx, -0.6, za + 0.05)], "wood", (s, 0, 0))

    out += a.striped_awning(-1.86, 1.86, -0.62, 2.94, 1.02, 0.36, "awn_rust", "canvas", n=10, valance=0.2, cheeks=False)

    for x in (-1.83, 1.83):
        out += c.rod((x, -1.6, 2.56), (x, -0.62, 2.2), 0.025, "iron", d=1)

    out += ck.box(-1.9, -0.7, 3.02, 1.9, -0.6, 3.97, "tan", c=0.03)
    out += ck.box(-1.94, -0.72, 3.9, 1.94, -0.58, 3.98, "wood_lt", c=0.02, d=1)
    out += ck.box(-1.94, -0.72, 3.0, 1.94, -0.58, 3.08, "wood_lt", c=0.02, d=1)
    out += c.text("GIFTS", 0.0, -0.715, 3.23, 0.54, "letter_brown", t=0.11)

    for x in (-1.5, 1.5):
        out += ck.box(x - 0.05, -0.62, 3.0, x + 0.05, -0.52, 3.85, "wood", d=1)

    out += ck.box(-1.93, 0.69, 0.15, -1.83, 1.47, 2.19, "teal", c=0.02)

    for k in range(4):
        y = 0.72 + k * 0.19
        out += ck.box(-1.945, y, 0.2, -1.925, y + 0.165, 2.12, "teal_lt" if k % 2 else "teal", d=0)

    for z in (0.5, 1.75):
        out += ck.box(-1.965, 0.72, z, -1.94, 1.2, z + 0.06, "iron_dk", d=0)

    out += c.face([(1.846, 0.0, 1.35), (1.846, 1.25, 1.35), (1.846, 1.25, 2.25), (1.846, 0.0, 2.25)], "void", (1, 0, 0))

    for y0, y1, z0, z1 in ((-0.08, 0.0, 1.27, 2.33), (1.25, 1.33, 1.27, 2.33), (0.0, 1.25, 1.25, 1.35), (0.0, 1.25, 2.25, 2.35)):
        out += ck.box(1.82, y0, z0, 1.9, y1, z1, "teal", d=1)

    for i, y in enumerate((0.25, 0.65, 1.0)):
        out += ck.cyl((1.9, y, 1.35), 0.09, 0.22 + 0.08 * (i % 2), ("awn_rust", "tan", "awn_blue")[i], sides=6, d=0)

    for i, (x, s) in enumerate(((-1.3, 0.28), (1.0, 0.22))):
        out += ck.blob((x, -1.62, 0.2), (s, s * 0.7, 0.11), ("rock_lt", "rock_sand", "rock_dk"), sub=0, seed=i + 3, d=1)

    out += ck.box(1.15, -1.5, 0.15, 1.7, -1.0, 0.65, "wood_lt", c=0.03, d=1)
    out += ck.box(1.2, -1.45, 0.65, 1.62, -1.1, 0.95, "plank", c=0.03, d=0)

    return out


def vending():
    out = W()

    for x0, x1 in ((-2.0, -0.01), (0.01, 2.0)):
        out += ck.box(x0, -2.0, 0.0, x1, 2.0, 0.15, "mortar", c=0.03)

    zr = 2.75
    out += ck.box(-1.5, 1.5, 0.15, 2.0, 2.0, zr, "white", c=0.06)
    out += ck.box(1.5, -0.05, 0.15, 2.0, 1.5, zr, "white", c=0.06, skip="b")
    out += ck.box(-2.0, -0.05, 0.15, -1.5, 2.0, zr, "white", c=0.06)
    out += c.plate(-1.5, 1.5, 0.15, zr, 1.49, "wood", -1)
    out += c.face([(-1.49, -0.0, 0.15), (-1.49, 1.5, 0.15), (-1.49, 1.5, zr), (-1.49, 0.0, zr)], "wood_lt", (1, 0, 0))
    out += c.face([(1.49, -0.0, 0.15), (1.49, 1.5, 0.15), (1.49, 1.5, zr), (1.49, 0.0, zr)], "wood_lt", (-1, 0, 0))
    nx, ny = (10, 6) if L() == 0 else (1, 1)
    out += c.face([(-1.5, 0.0, 0.155), (1.5, 0.0, 0.155), (1.5, 1.5, 0.155), (-1.5, 1.5, 0.155)], "brick_deep", (0, 0, 1))

    if L() == 0:
        for i in range(nx):
            for k in range(ny):
                x0 = -1.5 + i * 0.3 + (0.15 if k % 2 else 0)
                y0 = k * 0.25
                x1 = min(x0 + 0.28, 1.5)
                out += c.face([(x0, y0 + 0.015, 0.162), (x1, y0 + 0.015, 0.162), (x1, y0 + 0.235, 0.162), (x0, y0 + 0.235, 0.162)], ("tile", "brick", "brick_lt")[(i * 5 + k * 3) % 3], (0, 0, 1), cast=False)

    for x, col in ((-0.75, "teal_dk"), (0.75, "soda")):
        out += ck.box(x - 0.55, 1.36, 0.15, x + 0.55, 1.5, 2.05, col, c=0.04, skip="b")
        out += c.plate(x - 0.45, x + 0.15, 0.85, 1.85, 1.352, "glass")

        for k in range(3):
            for i in range(3):
                out += c.plate(x - 0.4 + i * 0.18, x - 0.28 + i * 0.18, 0.95 + k * 0.3, 1.12 + k * 0.3, 1.346, ("mustard", "off_white", "awn_red")[(i + k) % 3], d=0)

        out += ck.box(x + 0.23, 1.33, 1.1, x + 0.45, 1.37, 1.55, "steel_lt", d=0)
        out += ck.box(x - 0.4, 1.33, 0.35, x + 0.1, 1.37, 0.6, "void", d=1)

    out += ck.box(-1.5, 0.32, 0.92, -1.32, 0.72, 1.56, "steel", c=0.03, d=1)
    out += ck.box(-0.24, 0.54, 2.34, 0.24, 1.02, 2.5, "iron_lt", c=0.04, d=1)
    out += ck.box(-0.17, 0.62, 2.3, 0.17, 0.94, 2.345, "lamp_glass", d=0)
    out += c.rod((0.0, 0.78, 2.5), (0.0, 0.78, 2.76), 0.025, "iron", d=0)
    roof = a.rect(-1.97, -1.97, 1.97, 1.97)
    out += ck.box(-2.0, -2.0, 2.75, 2.0, 2.0, 3.0, "white", c=0.05, top="white_dk")
    out += c.ledge(a.rect(-2.0, -2.0, 2.0, 2.0), 2.75, 2.93, 0.03, "teal", c=0.03)

    for x in (-1.93, 1.93):
        out += ck.box(x - 0.05, -1.97, 0.15, x + 0.05, -1.87, 2.75, "teal_dk", c=0.015)
        out += ck.box(x - 0.1, -2.0, 0.15, x + 0.1, -1.82, 0.27, "white_dk", d=0)

    out += sign(-1.05, 1.05, -1.98, -1.72, 3.15, 3.87, "rust", "sign", [("VENDING", "teal_lt")], 0.38, back=True)

    for x in (-0.75, 0.75):
        out += ck.box(x - 0.045, -1.9, 2.98, x + 0.045, -1.8, 3.18, "steel_dk")

    out += ck.box(-0.45, 1.99, 0.15, 0.45, 2.05, 2.15, "teal_dk", c=0.015)
    out += ck.box(-0.55, 1.98, 2.15, 0.55, 2.07, 2.25, "white_dk", d=1)
    out += ck.box(0.24, 2.04, 1.1, 0.32, 2.09, 1.16, "gold", d=0)

    for x in (-1.15, 1.2):
        out += c.wall_vent(x, 2.0, 0.55, 0.5, 0.5, facing=1)

    for x in (-1.99, 1.99):
        out += ck.box(x - 0.03, -0.1, 2.55, x + 0.03, 2.0, 2.65, "teal_dk", d=1)

    return out


def shops():
    out = W()
    yf, yb, hw = -3.4, 4.35, 5.9
    front = []

    for s in (-1, 1):
        for x in (5.07, 2.93):
            front.append(a.win(hw + s * x, 0.56, 1.22, 1.62, n=2, trim="stone_dk", sill_col="stone", lintel=None, glass="glass"))

        front.append(a.door(hw + s * 4.0, 0.84, 2.38, leaf="wood", trim="stone_dk", glazed=True, depth=0.8, fan=0, lintel=None, reveal="brick_deep"))

    front.append({"x": hw, "z": 0.1, "w": 3.32, "h": 2.6, "kind": "void", "depth": 0.14, "trim": "stone_dk", "lintel": None})
    back = [a.door(hw, 1.0, 2.35, leaf="iron_lt", trim="stone_dk", lintel_col="stone", fan=0)]

    for x in (-3.8, 3.8):
        back.append(a.win(hw + x, 1.2, 1.05, 0.85, n=4, trim="steel_dk", sill_col="stone", lintel_col="stone"))

    out += a.shell(a.rect(-hw, yf, hw, yb), 0.0, 4.0, "brick", {0: front, 2: back})

    for k in range(13 if L() == 0 else 3):
        step = 0.2 if L() == 0 else 0.866
        z = 0.1 + k * step
        out += ck.box(-1.62, yf + 0.04, z, 1.62, yf + 0.13, z + step - 0.02, "shutter_lt" if k % 2 == 0 else "shutter", c=0.02, skip="blr")

    out += ck.box(-0.2, yf - 0.02, 0.16, 0.2, yf + 0.06, 0.28, "iron_dk", d=0)

    for x in (-5.82, -2.0, 2.0, 5.82):
        out += ck.box(x - 0.18, yf - 0.1, 0.0, x + 0.18, yf + 0.02, 2.75, "brick_dk", c=0.03)
        out += ck.box(x - 0.22, yf - 0.14, 0.0, x + 0.22, yf + 0.02, 0.5, "char_lt", c=0.03, d=1)
        out += ck.box(x - 0.23, yf - 0.16, 2.72, x + 0.23, yf + 0.02, 2.86, "stone", c=0.03, d=1, skip="b")
        out += ck.box(x - 0.16, yf - 0.08, 2.86, x + 0.16, yf + 0.02, 3.42, "brick_lt", c=0.02, d=1, skip="b")

    for s in (-1, 1):
        for x in (5.07, 2.93):
            out += ck.box(s * x - 0.68, yf - 0.06, 0.1, s * x + 0.68, yf + 0.02, 0.46, "wood_dk", c=0.02, d=1, skip="b")

        out += ck.box(s * 4.0 - 0.55, -3.8, 0.0, s * 4.0 + 0.55, yf, 0.09, "conc_dk", c=0.02)

    for x0, x1, col, word in ((-5.8, -2.2, "awn_red", "BOOKS"), (-1.8, 1.8, "awn_blue", "PARTS"), (2.2, 5.8, "awn_green", "BAKERY")):
        out += awning_run(x0, x1, yf - 0.04, 2.7, col)
        cx = (x0 + x1) / 2
        out += ck.box(cx - 1.6, yf - 0.1, 2.88, cx + 1.6, yf + 0.02, 3.36, "brick_deep", c=0.03, skip="b")
        out += c.text(word, cx, yf - 0.115, 2.97, 0.29, "stone", w=2.7)

    out += c.ledge(a.rect(-hw, yf, hw, yb), 3.45, 3.58, 0.09, "stone", c=0.03)
    out += c.ledge(a.rect(-hw, yf, hw, yb), 4.0, 4.18, 0.1, "stone", c=0.04)

    if L() == 0:
        for i in range(24):
            x = -5.6 + i * 0.487
            out += ck.box(x - 0.08, yf - 0.1, 3.84, x + 0.08, yf + 0.02, 4.0, "brick_lt", skip="bt")

        r = c.rng(7)

        for _ in range(14):
            x = r.uniform(-5.4, 5.4)
            z = r.uniform(3.6, 3.78)
            out.extend(c.plate(x - 0.14, x + 0.14, z, z + 0.08, yf - 0.006, "brick_lt" if r.random() < 0.5 else "tile"))

    for x in (-3.9, 0.0, 3.9):
        out += c.plate(x - 1.5, x + 1.5, 3.0, 3.55, yb + 0.012, "brick_dk", 1)

    for z in (1.9, 3.05):
        for s in (-1, 1):
            xa, xb = sorted((s * hw, s * (hw + 0.035)))
            out += ck.box(xa, yf, z, xb, yb, z + 0.09, "brick_dk", d=1)

    for x in (-2.6, 0.9, 2.6):
        out += ck.box(x - 0.09, yb, 0.0, x + 0.09, yb + 0.1, 2.9, "brick_dk", d=1)

    out += a.parapet(a.rect(-hw, yf, hw, yb), 4.18, 0.34, "brick", "stone", thick=0.22)
    out += c.face([(p[0], p[1], 4.182) for p in a.rect(-hw + 0.015, yf + 0.015, hw - 0.015, yb - 0.015)], "tar", (0, 0, 1))

    for i in range(4):
        for k in range(2):
            x0, y0 = -1.98 + i * 1.0, 1.4 + k * 1.1
            out += ck.box(x0, y0, 4.18, x0 + 0.96, y0 + 1.04, 4.25, "stone", c=0.02, d=1)

    for x in (-1.5, 1.5):
        out += c.vent_pipe(x, -2.1, 4.18, 0.45)

    out += c.ac_unit(0.0, -1.3, 4.18, 1.05, 1.0, 0.42)
    out += c.ac_unit(-4.0, 1.2, 4.18, 1.3, 1.1, 0.45)
    out += a.downpipe(5.5, yb + 0.07, 0.0, 3.9, "iron_lt")
    out += c.lantern(0.85, yb, 2.0, facing=1)

    return out


def corner():
    out = W()
    poly = [(-4.25, -3.45), (1.6, -3.45), (3.45, -1.6), (3.45, 4.25), (-4.25, 4.25)]
    shopwin = dict(trim="wood_dk", sill_col="stone", lintel=None, glass="glass", fw=0.09)
    upper = dict(trim="char_dk", sill_col="stone", lintel_col="stone", bars="h")
    ground = {
        0: [a.win(1.93, 0.55, 3.25, 1.6, n=3, **shopwin), a.win(4.85, 0.55, 1.6, 1.6, n=2, **shopwin)],
        1: [a.door(1.31, 1.62, 2.38, leaf="wood_dk", trim="stone_dk", glazed=True, lintel_col="stone", fan=0)],
        2: [a.win(1.0, 0.55, 1.6, 1.6, n=2, **shopwin), a.win(3.92, 0.55, 3.25, 1.6, n=3, **shopwin)],
        3: [a.door(6.0, 1.0, 2.35, leaf="iron_lt", trim="stone_dk", lintel_col="stone", fan=0), a.win(1.5, 1.0, 0.85, 1.3, **upper), a.win(3.0, 1.0, 0.85, 1.3, **upper)],
    }
    top = {
        0: [a.win(x, 3.72, 0.82, 1.42, **upper) for x in (1.05, 2.6, 4.4)],
        1: [a.win(1.31, 3.72, 0.95, 1.42, **upper)],
        2: [a.win(x, 3.72, 0.82, 1.42, **upper) for x in (0.9, 2.3, 3.7, 5.0)],
        3: [a.win(x, 3.72, 0.82, 1.42, **upper) for x in (1.3, 2.8, 4.9, 6.4)],
    }
    out += wallpoly(poly, 0.0, 3.0, "brick_dk", ground)
    out += wallpoly(poly, 3.0, 6.0, "brick", top)
    for x in (-4.12, -0.42, 1.55):
        out += ck.box(x - 0.13, -3.53, 0.0, x + 0.13, -3.43, 2.98, "brick_dk", c=0.03, skip="b")
        out += ck.box(x - 0.09, -3.5, 3.12, x + 0.09, -3.43, 5.66, "brick_dk", c=0.02, d=1, skip="b")

    for y in (-1.55, 0.42, 4.12):
        out += ck.box(3.43, y - 0.13, 0.0, 3.53, y + 0.13, 2.98, "brick_dk", c=0.03, skip="l")
        out += ck.box(3.43, y - 0.09, 3.12, 3.5, y + 0.09, 5.66, "brick_dk", c=0.02, d=1, skip="l")

    out += c.ledge(poly, 2.94, 3.1, 0.1, "stone", c=0.035)
    out += c.ledge(poly, 5.66, 5.82, 0.07, "brick_lt", c=0.02)
    out += c.ledge(poly, 5.82, 6.02, 0.14, "stone", c=0.05)

    if L() == 0:
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            ln = math.hypot(q[0] - p[0], q[1] - p[1])
            n = int(ln / 0.45)

            for k in range(n):
                u = (k + 0.5) / n * ln
                out += a.onto(p, q, ck.box(u - 0.07, -0.1, 5.5, u + 0.07, 0.01, 5.66, "brick_lt", skip="bt"))

        r = c.rng(11)

        for i in (0, 2, 3, 4):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            ln = math.hypot(q[0] - p[0], q[1] - p[1])

            for _ in range(5):
                u = r.uniform(0.5, ln - 0.6)
                z = r.choice((5.3, 3.3, 5.4)) if i != 4 else r.uniform(0.6, 5.3)
                part = W()

                for k in range(3):
                    part += c.plate(u + (k % 2) * 0.14, u + (k % 2) * 0.14 + 0.24, z + k * 0.09, z + k * 0.09 + 0.075, -0.006, "brick_lt" if k % 2 else "tile")

                out += a.onto(p, q, part)

    for z in (2.2, 4.35):
        out += ck.box(-4.29, -3.45, z, -4.24, 4.25, z + 0.09, "brick_dk", d=1)

    for x0, x1 in ((-4.12, -0.52), (-0.32, 1.53)):
        out += a.striped_awning(x0, x1, -3.5, 2.72, 0.95, 0.5, "awn_red", "off_white", n=max(4, int((x1 - x0) / 0.36)), valance=0.2)

    for y0, y1 in ((-1.53, 0.32), (0.52, 4.12)):
        local = a.striped_awning(y0 + 1.6, y1 + 1.6, -0.05, 2.72, 0.95, 0.5, "awn_red", "off_white", n=max(4, int((y1 - y0) / 0.36)), valance=0.2)
        out += a.onto(poly[2], poly[3], local)

    blade = W()
    blade += ck.box(0.25, -0.2, 2.5, 2.37, -0.04, 2.9, "stone", c=0.03, d=1)
    blade += c.text("CAFE", 1.31, -0.215, 2.58, 0.24, "brick_deep")
    out += a.onto(poly[1], poly[2], blade)
    step = ck.box(0.35, -0.42, 0.0, 2.27, 0.0, 0.1, "conc", c=0.025)
    out += a.onto(poly[1], poly[2], step)
    out += a.parapet(poly, 6.0, 0.86, "brick", "stone", thick=0.24)
    deck = a.offset(poly, -0.2)
    out += c.face([(p[0], p[1], 6.05) for p in deck], "tar_dk", (0, 0, 1))

    for x in (-1.6, 1.0):
        out += c.face([(x, -3.0, 6.058), (x + 0.07, -3.0, 6.058), (x + 0.07, 4.0, 6.058), (x, 4.0, 6.058)], "tar_lt", (0, 0, 1))

    out += ck.box(-3.55, 2.6, 6.05, -2.55, 3.55, 6.42, "stone_dk", c=0.05, d=1)

    for x, y in ((-3.6, -0.3), (0.95, 3.6)):
        out += c.vent_pipe(x, y, 6.05, 0.5, "mortar")

    out += c.ac_unit(-0.8, 0.8, 6.05, 1.3, 1.1, 0.5)
    out += a.chimney(-2.7, -1.9, 6.05, 7.0, "brick_lt", "stone", 0.7, 0.5, 2)
    out += a.downpipe(-3.6, 4.32, 0.0, 5.7, "iron_lt")
    out += c.wall_vent(-0.2, 4.25, 1.8, facing=1)

    return out


def repair():
    out = W()
    yf, yb, hw = -3.45, 3.5, 5.95
    upper = dict(n=2, trim="brick_dk", sill_col="char_trim", lintel_col="char_trim")
    front = [a.win(hw + x, 3.9, 1.0, 1.5, **upper) for x in (-4.85, -3.15, -0.85, 0.85, 3.15, 4.85)]

    for x in (-4.0, 0.0):
        front.append({"x": hw + x, "z": 0.12, "w": 3.08, "h": 2.58, "kind": "void", "depth": 0.14, "trim": "char_trim", "lintel": None})

    front.append(a.door(hw + 2.95, 0.95, 2.45, leaf="wood", trim="char_trim", glazed=True, lintel_col="char_trim", fan=0))
    front.append(a.win(hw + 4.85, 0.9, 1.0, 1.5, **upper))
    back = [a.door(hw + 3.7, 1.0, 2.4, leaf="wood", trim="char_trim", lintel_col="char_trim", fan=0)]
    back += [a.win(hw + x, 3.9, 1.0, 1.5, **upper) for x in (-3.6, 0.0, 3.6)]
    back += [a.win(hw + x, 1.0, 1.0, 1.4, **upper) for x in (-3.6, 0.0)]
    out += a.shell(a.rect(-hw, yf, hw, yb), 0.0, 6.0, "char", {0: front, 2: back})

    for x in (-4.0, 0.0):
        for k in range(12 if L() == 0 else 3):
            step = 0.205 if L() == 0 else 0.82
            z = 0.14 + k * step
            out += ck.box(x - 1.5, yf + 0.04, z, x + 1.5, yf + 0.13, z + step - 0.025, "shutter_lt" if k % 2 == 0 else "shutter", c=0.02, skip="blr")

        out += ck.box(x - 1.65, yf - 0.1, 2.7, x + 1.65, yf + 0.02, 2.92, "steel_dk", c=0.04, d=1, skip="b")
        out += ck.box(x - 0.25, yf - 0.01, 0.2, x + 0.25, yf + 0.05, 0.3, "iron_dk", d=0)

    for x0, x1 in ((-5.99, -5.56), (-2.45, -1.55), (1.56, 2.3), (3.6, 4.15), (5.55, 5.99)):
        out += ck.box(x0, yf - 0.09, 0.0, x1, yf + 0.02, 0.62, "brick_deep", c=0.03)

        for k in range(8 if L() == 0 else 0):
            z = 0.66 + k * 0.28
            out += ck.box(x0 + 0.04, yf - 0.06, z, x1 - 0.04, yf + 0.02, z + 0.2, "char_trim" if k % 2 == 0 else "char_lt", c=0.02, skip="b")

        if L() > 0:
            out += c.plate(x0 + 0.04, x1 - 0.04, 0.66, 2.82, yf - 0.03, "char_lt")

    for x in (-5.8, -2.0, 2.0, 5.8):
        out += ck.box(x - 0.18, yf - 0.07, 3.1, x + 0.18, yf + 0.02, 5.6, "char_dk", c=0.025, d=1, skip="b")

    rect = a.rect(-hw, yf, hw, yb)
    out += c.ledge(rect, 2.92, 3.12, 0.08, "char_trim", c=0.04)
    out += c.ledge(rect, 5.62, 5.76, 0.07, "char_trim", c=0.03)
    out += c.ledge(rect, 5.98, 6.16, 0.1, "char_trim", c=0.04)

    if L() == 0:
        for i in range(23):
            x = -5.6 + i * 0.51
            out += ck.box(x - 0.06, yf - 0.13, 5.76, x + 0.06, yf + 0.01, 5.98, "char_trim", c=0.015, skip="bt")

        r = c.rng(5)

        for _ in range(16):
            x = r.uniform(-5.4, 5.2)
            z = r.choice((3.35, 3.55, 5.5))
            out.extend(c.plate(x, x + 0.26, z, z + 0.075, yf - 0.006, "char_trim" if r.random() < 0.4 else "char_lt"))

    out += ck.box(-5.35, yf - 0.12, 3.18, -2.65, yf + 0.01, 3.72, "rust", c=0.04, skip="b")
    out += c.text("REPAIR", -4.0, yf - 0.135, 3.28, 0.34, "off_white", w=2.3)
    out += ck.box(-1.35, yf - 0.12, 3.18, 1.35, yf + 0.01, 3.72, "teal_deep", c=0.04, skip="b")
    out += c.text("TYRES", 0.0, yf - 0.135, 3.28, 0.34, "off_white", w=2.3)

    for z in (2.0, 4.2):
        for s in (-1, 1):
            xa, xb = sorted((s * hw, s * (hw + 0.04)))
            out += ck.box(xa, yf, z, xb, yb, z + 0.1, "char_dk", d=1)

    for s in (-1, 1):
        for y in (-1.2, 1.4):
            xa, xb = sorted((s * hw, s * (hw + 0.05)))
            out += ck.box(xa, y - 0.55, 4.45, xb, y + 0.55, 5.45, "char_trim", d=1)
            out += c.face([(s * (hw + 0.056), y - 0.45, 4.55), (s * (hw + 0.056), y + 0.45, 4.55), (s * (hw + 0.056), y + 0.45, 5.35), (s * (hw + 0.056), y - 0.45, 5.35)], "glass", (s, 0, 0))
            out += ck.box(min(xa, s * (hw + 0.09)), y - 0.03, 4.55, max(xb, s * (hw + 0.09)), y + 0.03, 5.35, "char_trim", d=0)

    out += a.parapet(rect, 6.16, 0.9, "char", "char_trim", thick=0.22)
    out += c.face([(-hw + 0.015, yf + 0.015, 6.162), (hw - 0.015, yf + 0.015, 6.162), (hw - 0.015, yb - 0.015, 6.162), (-hw + 0.015, yb - 0.015, 6.162)], "tar", (0, 0, 1))
    out += ck.box(1.3, -2.9, 6.16, 5.3, 0.7, 6.23, "stone", c=0.025)

    for k in range(1, 4):
        out += ck.box(1.3 + k - 0.025, -2.9, 6.23, 1.3 + k + 0.025, 0.7, 6.26, "stone_dk", d=0)

    for x in (-3.85, 0.2):
        out += c.vent_pipe(x, 2.35, 6.16, 0.55)

    out += c.ac_unit(-2.2, -0.8, 6.16, 1.4, 1.2, 0.55)
    out += a.downpipe(-5.35, yb + 0.08, 0.0, 5.5, "steel_dk")
    out += c.lantern(2.15, yf - 0.06, 2.2)
    out += c.wall_vent(2.0, yb, 2.3, facing=1)

    return out


def ranch():
    out = W()
    hw, hd = 5.9, 3.05
    frame = dict(trim="wood_trim", sill_col="wood_trim", lintel_col="wood_trim", fw=0.1, reveal="shingle_lt")
    front = [a.win(hw - 2.97, 0.98, 3.4, 1.2, n=2, **frame), a.win(hw + 2.78, 0.98, 0.86, 1.22, n=1, **frame), a.win(hw + 4.52, 0.98, 0.86, 1.22, n=1, **frame),
             a.door(hw + 0.55, 0.94, 2.12, leaf="wood", trim="wood_trim", lintel_col="wood_trim", fan=0)]
    back = [a.win(hw + x, 1.1, 0.9, 1.2, n=1, **frame) for x in (-3.6, 0.0, 3.6)]
    side = [a.win(x, 1.1, 0.8, 1.15, n=1, **frame) for x in (1.6, 4.5)]
    out += a.shell(a.rect(-hw, -hd, hw, hd), 0.0, 3.05, "siding", {0: front, 1: side, 2: back, 3: side})
    rect = a.rect(-hw, -hd, hw, hd)
    base = [(0, front), (1, side), (2, back), (3, side)]

    for i, ops in base:
        p, q = rect[i], rect[(i + 1) % 4]
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        cuts = sorted((o["x"] - o["w"] / 2 - 0.1, o["x"] + o["w"] / 2 + 0.1, o["z"], o["z"] + o["h"]) for o in ops)

        for z0, z1, col, dp in [(0.0, 0.82, "ranch_red", 0.06)] + [(0.98 + k * 0.3, 1.04 + k * 0.3, "siding_lt", 0.035) for k in range(7)]:
            if z0 > 0 and L() > 0:
                continue

            spans, cur = [], 0.0

            for x0, x1, oz0, oz1 in cuts:
                if oz0 < z1 and oz1 > z0:
                    spans.append((cur, x0))
                    cur = x1

            spans.append((cur, ln))
            ext = dp if i in (0, 2) else 0.0

            for u0, u1 in spans:
                if u1 - u0 > 0.05:
                    lo = u0 - ext if u0 <= 0 else u0
                    hi = u1 + ext if u1 >= ln else u1
                    out += a.onto(p, q, ck.box(lo, -dp, z0, hi, 0.005, z1, col, c=0.015 if z0 == 0 else 0.0, skip="b"))

        out += a.onto(p, q, ck.box(0.0, -0.075, 0.82, ln, 0.0, 0.9, "ranch_red_dk", d=1, skip="b")) if i != 0 else W()

    for x in (-hw, hw):
        for y in (-hd, hd):
            out += ck.box(x - 0.11, y - 0.11, 0.0, x + 0.11, y + 0.11, 3.05, "wood_trim", c=0.04)

    out += ck.box(-0.2, -3.7, 0.0, 1.3, -3.05, 0.12, "ranch_red", c=0.03)
    out += ck.box(1.38, -3.12, 1.5, 1.72, -3.05, 1.72, "gold", c=0.02, d=0)
    out += c.lantern(-0.3, -hd, 1.75)
    out += ck.box(-4.75, -3.3, 0.78, -1.2, -3.06, 0.96, "wood", c=0.03, d=1)

    if L() == 0:
        for i in range(10):
            x = -4.55 + i * 0.35
            out += ck.blob((x, -3.2, 1.0), (0.2, 0.12, 0.1), ("leaf_lt", "leaf", "leaf_dk"), sub=0, seed=i)

    eave = a.rect(-6.0, -4.0, 6.0, 4.0)
    top = [(-2.7, -0.02), (2.7, -0.02), (2.7, 0.02), (-2.7, 0.02)]
    out += c.ledge(a.rect(-5.97, -3.97, 5.97, 3.97), 3.0, 3.24, 0.02, "shingle_lt", top="shingle_lt", c=0.04)
    out += c.face([(-5.95, -3.95, 3.0), (5.95, -3.95, 3.0), (5.95, 3.95, 3.0), (-5.95, 3.95, 3.0)], "wood_dk", (0, 0, -1))
    out += a.hip(a.offset(eave, -0.04), top, 3.24, 4.86, "shingle", rows=9, lip=0.05, cap="shingle_lt", under=False)
    out += a.ridge_caps(a.offset(eave, -0.04), top, 3.24, 4.86, "shingle_lt", r=0.085)
    out += ck.box(-2.8, -0.09, 4.82, 2.8, 0.09, 4.95, "shingle_lt", c=0.03, d=1)

    for x in (-4.5, -3.0, -1.5, 0.0, 1.5, 3.0, 4.5):
        for y, s in ((-3.55, -1), (3.55, 1)):
            out += ck.box(x - 0.06, min(y, y - s * 0.5), 2.88, x + 0.06, max(y, y - s * 0.5), 3.0, "wood", d=0)

    out += a.chimney(3.65, -1.15, 2.95, 5.9, "ranch_red_dk", "ranch_red", 0.74, 0.74, 1)
    out += a.downpipe(-5.7, 3.13, 0.0, 2.9, "wood_dk")

    return out


def ticket():
    out = W()
    body = c.roundrect(-0.83, -0.6, 0.83, 0.83, 0.16, 1)
    base = a.offset(body, 0.07)
    out += c.slabs([(base, 0.0), (base, 0.24), (body, 0.32)], "timber")
    front = [{"x": 0.425, "z": 0.9, "w": 0.7, "h": 0.64, "kind": "win", "trim": "iron", "n": 1, "sill": False, "lintel": None, "depth": 0.09},
             {"x": 1.215, "z": 0.9, "w": 0.16, "h": 0.64, "kind": "win", "trim": "iron", "n": 1, "sill": False, "lintel": None, "depth": 0.07, "fw": 0.02}]
    side = [a.win(x, 0.92, 0.42, 0.6, n=1, trim="iron_lt", sill_col="steel", lintel=None, depth=0.07, fw=0.04) for x in (0.31, 0.84)]
    back = [a.door(0.65, 0.65, 1.7, leaf="iron_lt", trim="steel", lintel=None, fan=0, depth=0.08)]
    n = len(body)
    straight = {1: (side, None), 3: (back, None), 5: (side, None), 7: (front, None)}

    for i in range(n):
        p, q = body[i], body[(i + 1) % n]

        if i in straight:
            out += a.facade(p, q, 0.32, 1.95, "white", straight[i][0])
        else:
            out += c.face([(p[0], p[1], 0.32), (q[0], q[1], 0.32), (q[0], q[1], 1.95), (p[0], p[1], 1.95)], "white", (q[1] - p[1], p[0] - q[0], 0))

    roof = c.roundrect(-1.0, -0.77, 1.0, 1.0, 0.24, 1)
    out += c.slabs([(a.offset(roof, -0.08), 1.93), (roof, 1.99), (roof, 2.1), (a.offset(roof, -0.09), 2.19)], "iron_lt", top="iron", bottom="iron_dk")
    out += c.ledge(a.offset(roof, -0.02), 2.0, 2.05, 0.03, "teal", c=0.0)
    out += ck.box(-0.66, -0.66, 1.62, 0.62, -0.59, 1.9, "sign", c=0.025, d=1, skip="b")
    out += c.text("TICKETS", -0.02, -0.674, 1.675, 0.17, "off_white", w=1.1)
    out += ck.box(-0.68, -1.0, 0.82, 0.19, -0.58, 0.88, "wood_lt", c=0.015)

    for x in (-0.55, 0.06):
        out += c.beam((x, -0.6, 0.62), (x, -0.88, 0.82), 0.035, "iron", d=0)

    out += ck.box(-0.52, -0.86, 0.88, -0.24, -0.64, 1.04, "steel", c=0.02, d=0)
    out += ck.box(-0.05, -0.8, 0.88, 0.07, -0.7, 0.98, "tan", d=0)
    out += c.plate(0.2, 0.34, 1.12, 1.46, -0.615, "off_white")

    for k in range(4):
        out += c.plate(0.22, 0.32, 1.16 + k * 0.07, 1.19 + k * 0.07, -0.622, "red_dk", d=0)

    out += porthole(-0.25, -0.52, 1.4, 0.09, -1, "steel_lt") if L() == 0 else W()

    return out


FOOT = {"motel", "rooms", "canopy", "garage", "diner", "gifts", "vending", "shops", "corner", "repair", "ranch", "ticket"}
ALL = {f.__name__: (f, {"building": True}) for f in (motel, rooms, canopy, garage, diner, gifts, vending, shops, corner, repair, ranch, ticket)}
