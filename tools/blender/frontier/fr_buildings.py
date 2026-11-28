import math

import fr_parts as p
from fr_kit import Mesh


def side(m, which, x0, x1, y0, y1):
    if which == "f":
        return m.at((x0 + x1) / 2, y0, 0), x1 - x0

    if which == "r":
        return m.at(x1, (y0 + y1) / 2, 0, yaw=90), y1 - y0

    if which == "b":
        return m.at((x0 + x1) / 2, y1, 0, yaw=180), x1 - x0

    return m.at(x0, (y0 + y1) / 2, 0, yaw=-90), y1 - y0


def shell(m, x0, x1, y0, y1, z0, z1, style, fam, openings=None, seed=0, sides="frbl"):
    openings = openings or {}

    for i, s in enumerate(sides):
        frame, length = side(m, s, x0, x1, y0, y1)

        with frame:
            style(m, -length / 2, length / 2, z0, z1, fam, openings.get(s, ()), seed + i)


def windows(m, which, x0, x1, y0, y1, items, **kw):
    frame, _ = side(m, which, x0, x1, y0, y1)

    with frame:
        for cx, z, w, h in items:
            p.window(m, cx, z, w, h, **kw)


def back(m, x0, x1, y0, y1, wins=(), door=None, double=False, **kw):
    frame, _ = side(m, "b", x0, x1, y0, y1)

    with frame:
        for cx, z, w, h in wins:
            p.window(m, cx, z, w, h, **dict(kw, hood=False))

        if door:
            u, z, w, h = door
            p.door(m, u, z, w, h, "wood", kw.get("frame", "cream"), glazed=False, double=double)


def porch_roof(m, x0, x1, yw, depth, low, high, kind="shingle", fam="shingle", seed=5):
    p.slope(m, x0, x1, (yw - depth - 0.12, low), (yw + 0.02, high), kind, fam, seed=seed, row=0.45)
    m.box((x0 + 0.06, yw - depth + 0.04, low - 0.22), (x1 - 0.06, yw - depth + 0.22, low - 0.04), "wood_d", 0.02)


def front_porch(m, hw, yw, depth, top, col="wood_d", n=4, door_gap=True):
    p.deck(m, -hw, hw, yw - depth, yw, 0.2)
    p.stairs(m, 0.0, yw - depth - 0.03, 2.0, 1, 0.2, 0.24)
    xs = [-hw + 0.14 + (2 * hw - 0.28) * i / (n - 1) for i in range(n)]
    p.posts(m, xs, yw - depth + 0.14, 0.2, top, col)
    m.block(-hw, yw - depth, hw, yw, 0.1)


def flat_roof(m, x0, x1, y0, y1, z, fam="stone"):
    n = max(1, int((x1 - x0) / 0.9))
    w = (x1 - x0) / n

    for i in range(n):
        m.quad((x0 + i * w, y0, z), (x0 + (i + 1) * w, y0, z), (x0 + (i + 1) * w, y1, z), (x0 + i * w, y1, z), fam if i % 2 else fam + "_d")


def parapet(m, x0, x1, y0, y1, z0, z1, fam, cap, sides="rbl"):
    t = 0.2

    for s in sides:
        frame, length = side(m, s, x0, x1, y0, y1)

        with frame:
            m.box((-length / 2, -0.01, z0), (length / 2, t, z1), fam, 0.02, skip="z")
            m.box((-length / 2 - 0.07, -0.08, z1), (length / 2 + 0.07, t + 0.06, z1 + 0.12), cap, 0.025)


def roof_clutter(m, x, y, z):
    p.barrel(m, x, y, z, 0.42, 0.95, 10, "gray")
    p.crate(m, x - 1.3, y + 0.2, z, 0.8, 0.8, 0.6, 20, "wood", False)


def bank():
    m = Mesh(10)
    hw, yf, yb = 4.45, -5.2, 5.55
    p.foundation(m, -hw - 0.1, yf - 0.1, hw + 0.1, yb + 0.1)
    ground = [(-2.65, 0.9, 1.35, 1.75), (2.65, 0.9, 1.35, 1.75), (0, 0.12, 1.7, 2.45)]
    side_low = [(-2.8, 1.0, 1.2, 1.5), (1.6, 1.0, 1.2, 1.5)]
    rear = [(-2.2, 1.0, 1.2, 1.5), (0.1, 1.0, 1.0, 1.5)]
    rear_door = (2.4, 0.12, 1.1, 2.2)
    shell(m, -hw, hw, yf, yb, 0.12, 3.2, p.stone, "stone", {"f": ground, "r": side_low, "l": side_low, "b": rear + [rear_door]}, 3)
    upper = [(-2.65, 3.95, 1.05, 1.5), (0, 3.95, 1.05, 1.5), (2.65, 3.95, 1.05, 1.5)]
    side_up = [(-2.8, 3.95, 1.0, 1.45), (1.6, 3.95, 1.0, 1.45)]
    shell(m, -hw, hw, yf, yb, 3.2, 6.15, p.plaster, "plas", {"f": upper, "r": side_up, "l": side_up, "b": upper}, 8)
    back(m, -hw, hw, yf, yb, rear, rear_door, frame="stone_l", bars=True)
    back(m, -hw, hw, yf, yb, upper, frame="stone_l", shutter="red")
    flat_roof(m, -hw, hw, yf, yb, 6.14)
    parapet(m, -hw, hw, yf, yb, 6.15, 6.6, "plas", "stone_l")
    windows(m, "f", -hw, hw, yf, yb, ground[:2], frame="stone_l", bars=True, hood=True)
    windows(m, "f", -hw, hw, yf, yb, upper, frame="stone_l", shutter="red")

    for s in "rl":
        windows(m, s, -hw, hw, yf, yb, side_low, frame="stone_l", bars=True)
        windows(m, s, -hw, hw, yf, yb, side_up, frame="stone_l", shutter="red")

    with m.at(0, yf, 0):
        p.door(m, 0, 0.12, 1.7, 2.45, "red", "stone_l", glazed=False, double=True)

        for u in (-hw + 0.17, -1.42, 1.42, hw - 0.17):
            m.box((u - 0.22, -0.2, 0.12), (u + 0.22, 0.02, 0.42), "stone_d", 0.04, skip="Yz")
            m.box((u - 0.15, -0.14, 0.42), (u + 0.15, 0.02, 3.05), "stone_l", 0.03, skip="Yz")
            m.box((u - 0.13, -0.12, 3.42), (u + 0.13, 0.02, 5.85), "cream", 0.03, skip="Y")

        p.cornice(m, -hw, hw, 3.2, "stone_l", 0.3, 1.1, False)
        p.cornice(m, -hw, hw, 5.95, "cream", 0.32, 0.85)
        p.false_front(m, [(-hw, 6.05), (hw, 6.05), (hw, 6.85), (2.1, 6.85), (1.5, 7.3), (-1.5, 7.3), (-2.1, 6.85), (-hw, 6.85)], "plas", "stone_l", 0.24, "plas_d")
        m.quad((-hw, -0.004, 6.05), (hw, -0.004, 6.05), (hw, -0.004, 6.85), (-hw, -0.004, 6.85), "plas")
        m.quad((-1.5, -0.002, 6.85), (1.5, -0.002, 6.85), (1.05, -0.002, 7.25), (-1.05, -0.002, 7.25), "plas")
        p.sign(m, 0, 6.17, 3.4, 0.72, "BANK", "red_d", "gold", "stone_l")
        p.disc(m, 0, 7.12, 0.17, -0.03, "gold")

        for s in (-1, 1):
            m.prism((s * (hw - 0.25), -0.02), 6.97, 7.25, 0.16, 0.09, 8, "stone_l")
            p.lamp(m, s * 1.42, -0.32, 2.2, 0.8)
            m.box((s * 1.42 - 0.04, -0.34, 2.56), (s * 1.42 + 0.04, -0.12, 2.62), "iron", skip="Y")

        for i in range(2):
            m.box((-1.5 - i * 0.25, -0.28 - i * 0.24, -0.1), (1.5 + i * 0.25, -0.02 - i * 0.24, 0.12 - i * 0.07), "stone_l" if i == 0 else "stone", 0.02, skip="Yz")

    p.chimney(m, 2.6, 3.0, 6.14, 7.4, 0.6, "rust")
    roof_clutter(m, -1.8, 2.2, 6.14)
    m.block(-hw, yf, hw, yb, 6.4)

    return m


def goods():
    m = Mesh(11)
    hw, yw, yb, depth = 4.15, -3.85, 5.3, 1.55
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    front = [(-2.45, 0.75, 2.1, 1.75), (2.45, 0.75, 2.1, 1.75), (0, 0.2, 1.4, 2.4)]
    flank = [(-2.0, 1.1, 1.1, 1.3), (1.8, 1.1, 1.1, 1.3)]
    rear = [(1.6, 1.1, 1.1, 1.3)]
    rear_door = (-1.8, 0.12, 1.1, 2.2)
    shell(m, -hw, hw, yw, yb, 0.12, 3.7, p.clap, "teal", {"f": front, "r": flank, "l": flank, "b": rear + [rear_door]}, 2)
    back(m, -hw, hw, yw, yb, rear, rear_door, frame="cream")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 3.7)
    windows(m, "f", -hw, hw, yw, yb, front[:2], frame="cream", hood=False)

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="cream", shutter="red")

    p.roof_y(m, -hw, hw, yw + 0.55, yb, [(-hw - 0.15, 3.68), (0, 5.25), (hw + 0.15, 3.68)], "tin", "tin", 4, 0.18, "wood_d")

    with m.at(0, yb, 0, yaw=180):
        p.gable_wall(m, [(-hw, 3.68), (0, 5.2), (hw, 3.68)], 3.68, "teal", [(0, 3.9, 0.8, 0.65)], 6)
        p.window(m, 0, 3.9, 0.8, 0.65, "cream")

    with m.at(0, yw, 0):
        p.door(m, 0, 0.2, 1.4, 2.4, "ochre", "cream", double=True, step=False)
        outline = [(-hw, 3.7), (hw, 3.7), (hw, 5.55), (2.7, 5.55), (2.7, 6.1), (-2.7, 6.1), (-2.7, 5.55), (-hw, 5.55)]
        p.false_front(m, outline, "teal", "cream", 0.22, "teal_d")
        p.clap(m, -hw, hw, 3.7, 5.55, "teal", [(0, 4.35, 5.0, 1.15)], 9)
        p.clap(m, -2.7, 2.7, 5.55, 6.08, "teal", [(0, 4.35, 5.0, 1.15)], 12)
        p.sign(m, 0, 4.42, 4.8, 1.0, "GOODS", "cream", "red_d", "wood_d")
        p.cornice(m, -hw, hw, 3.72, "cream", 0.22, 1.2, False)

        for s in (-1, 1):
            m.box((s * (hw - 0.02) - 0.1, -0.12, 3.7), (s * (hw - 0.02) + 0.1, 0.06, 5.75), "cream", 0.025, skip="Y")

    front_porch(m, hw + 0.05, yw, depth, 2.95, "cream", 4)
    p.slope(m, -hw - 0.12, hw + 0.12, (yw - depth - 0.15, 2.98), (yw - 0.06, 3.5), "cream", "red")
    m.box((-hw, yw - depth + 0.05, 2.78), (hw, yw - depth + 0.23, 2.95), "cream_d", 0.02)
    p.barrel(m, -3.55, yw - 0.45, 0.2, 0.3, 0.82)
    p.barrel(m, -2.9, yw - 0.38, 0.2, 0.26, 0.72, 10, "gray")
    p.crate(m, 3.4, yw - 0.5, 0.2, 0.75, 0.6, 0.55, 6)
    p.sack(m, 2.65, yw - 0.45, 0.2, 0.95, 20)
    p.sack(m, 3.35, yw - 0.5, 0.75, 0.8, -30)
    p.stovepipe(m, 2.4, 3.4, 4.0, 5.9)
    m.block(-hw, yw, hw, yb, 4.6)

    return m


def saloon():
    m = Mesh(13)
    hw, yw, yb, depth = 4.2, -3.8, 5.3, 1.65
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    low = [(-2.55, 0.95, 1.4, 1.5), (2.55, 0.95, 1.4, 1.5), (0, 0.2, 1.7, 2.35)]
    flank = [(-2.0, 1.05, 1.0, 1.35), (1.9, 1.05, 1.0, 1.35)]
    flank_up = [(-2.0, 4.05, 0.95, 1.25), (1.9, 4.05, 0.95, 1.25)]
    rear = [(-1.8, 1.05, 1.0, 1.35)]
    rear_door = (2.2, 0.12, 1.1, 2.2)
    shell(m, -hw, hw, yw, yb, 0.12, 3.35, p.clap, "red", {"f": low, "r": flank, "l": flank, "b": rear + [rear_door]}, 21)
    up = [(-2.55, 3.46, 1.0, 1.9), (0, 3.46, 1.0, 1.9), (2.55, 3.46, 1.0, 1.9)]
    shell(m, -hw, hw, yw, yb, 3.35, 5.95, p.clap, "red", {"f": up, "r": flank_up, "l": flank_up, "b": flank_up}, 29)
    back(m, -hw, hw, yw, yb, rear, rear_door, frame="cream")
    back(m, -hw, hw, yw, yb, flank_up, frame="cream")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 5.95)
    windows(m, "f", -hw, hw, yw, yb, low[:2], frame="cream", shutter="teal")

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="cream", shutter="teal")
        windows(m, s, -hw, hw, yw, yb, flank_up, frame="cream")

        frame, length = side(m, s, -hw, hw, yw, yb)

        with frame:
            p.cornice(m, -length / 2, length / 2, 3.3, "cream", 0.12, 1.0, False)

    p.roof_y(m, -hw, hw, yw + 0.5, yb, [(-hw - 0.15, 5.93), (0, 6.75), (hw + 0.15, 5.93)], "tin", "rust", 14, 0.16, "wood_d")

    with m.at(0, yb, 0, yaw=180):
        p.gable_wall(m, [(-hw, 5.93), (0, 6.72), (hw, 5.93)], 5.93, "red", (), 16)

    with m.at(0, yw, 0):
        p.batwing(m, 0, 0.2, 1.7, 2.35)

        for cx, z, w, h in up:
            p.door(m, cx, z, w, h, "teal", "cream", step=False)

        outline = [(-hw, 5.95), (hw, 5.95), (hw, 6.5), (2.75, 6.5), (2.55, 6.95), (1.6, 7.3), (0, 7.42), (-1.6, 7.3), (-2.55, 6.95), (-2.75, 6.5), (-hw, 6.5)]
        p.false_front(m, outline, "red", "cream", 0.22, "red_d")
        m.face([(u, -0.004, z) for u, z in outline], "red")
        p.sign(m, 0, 6.12, 4.6, 0.92, "SALOON", "cream", "red_d", "ochre")
        p.cornice(m, -hw, hw, 5.9, "cream", 0.22, 0.95)

        for s in (-1, 1):
            p.lamp(m, s * 1.25, -0.28, 1.95, 0.8)
            m.box((s * 1.25 - 0.04, -0.3, 2.3), (s * 1.25 + 0.04, 0.0, 2.36), "iron", skip="Y")

    front_porch(m, hw, yw, depth, 3.08, "cream", 4)
    m.box((-hw - 0.05, yw - depth - 0.02, 3.08), (hw + 0.05, yw - 0.02, 3.26), "wood_d", 0.025)
    p.deck(m, -hw, hw, yw - depth, yw - 0.02, 3.4, "wood", "y")
    p.balusters(m, -hw + 0.07, hw - 0.07, yw - depth + 0.07, 3.38, 1.0, "cream", 0.34)

    for s in (-1, 1):
        with m.at(s * (hw - 0.07), 0, 0, yaw=90):
            m.box((yw - depth + 0.07, -0.05, 4.29), (yw, 0.05, 4.38), "cream", 0.02)

            for i in range(1, 5):
                u = yw - depth + 0.07 + (depth - 0.1) * i / 5
                m.box((u - 0.03, -0.03, 3.4), (u + 0.03, 0.03, 4.29), "cream", skip="zZ")

    p.posts(m, [-hw + 0.14, -1.35, 1.35, hw - 0.14], yw - depth + 0.2, 4.38, 5.55, "cream", 0.13, False)
    p.slope(m, -hw - 0.08, hw + 0.08, (yw - depth + 0.0, 5.55), (yw - 0.02, 5.92), "shingle", "shingle", seed=19, row=0.36)
    p.barrel(m, -3.7, yw - 0.45, 0.2)
    p.barrel(m, -3.1, yw - 0.35, 0.2, 0.24, 0.66, 8, "gray")
    p.bench(m, 2.7, yw - 0.35, 0.2, 1.5)
    p.chimney(m, -2.6, 3.6, 5.6, 7.35, 0.55, "rust")
    m.block(-hw, yw, hw, yb, 6.1)

    return m


def jail():
    m = Mesh(14)
    hw, yf, yb = 3.62, -4.05, 4.85
    p.foundation(m, -hw - 0.12, yf - 0.12, hw + 0.12, yb + 0.12)
    front = [(-2.15, 1.25, 1.15, 1.2), (2.15, 1.25, 1.15, 1.2), (0, 0.12, 1.25, 2.35)]
    flank = [(-2.2, 1.7, 0.8, 0.7), (0.2, 1.7, 0.8, 0.7), (2.6, 1.7, 0.8, 0.7)]
    rear = [(-1.8, 1.7, 0.8, 0.7), (1.8, 1.7, 0.8, 0.7)]
    shell(m, -hw, hw, yf, yb, 0.12, 2.95, p.stone, "stone", {"f": front, "r": flank, "l": flank, "b": rear}, 31)
    back(m, -hw, hw, yf, yb, rear, frame="stone_l", bars=True, hood=False)
    shell(m, -hw, hw, yf, yb, 2.95, 4.15, p.plaster, "plas", None, 36)
    flat_roof(m, -hw, hw, yf, yb, 4.14)
    parapet(m, -hw, hw, yf, yb, 4.15, 4.5, "plas", "stone")
    windows(m, "f", -hw, hw, yf, yb, front[:2], frame="stone_l", bars=True)

    for s in "rl":
        windows(m, s, -hw, hw, yf, yb, flank, frame="stone_l", bars=True, hood=False)

    for s in "frbl":
        frame, length = side(m, s, -hw, hw, yf, yb)

        with frame:
            m.box((-length / 2 - 0.05, -0.1, 2.9), (length / 2 + 0.05, 0.03, 3.05), "stone_l", 0.025, skip="Y")

            for i in range(int(length / 0.85)):
                u = -length / 2 + 0.5 + i * 0.85
                m.beam((u, 0.0, 3.82), (u, -0.25, 3.82), 0.17, 0.17, "wood_d", skip="x")

    with m.at(0, yf, 0):
        p.door(m, 0, 0.12, 1.25, 2.35, "iron", "wood_d", glazed=False)

        for v in (0.5, 1.2, 1.95):
            m.box((-0.58, 0.04, v), (0.58, 0.08, v + 0.1), "iron_d", skip="Y")

        p.false_front(m, [(-2.5, 4.15), (2.5, 4.15), (2.5, 5.05), (1.7, 5.05), (1.7, 5.4), (-1.7, 5.4), (-1.7, 5.05), (-2.5, 5.05)], "plas", "stone_l", 0.2, "plas_d")
        m.face([(u, -0.004, z) for u, z in [(-2.5, 4.15), (2.5, 4.15), (2.5, 5.05), (1.7, 5.05), (1.7, 5.4), (-1.7, 5.4), (-1.7, 5.05), (-2.5, 5.05)]], "plas")
        p.sign(m, 0, 4.28, 2.8, 0.85, "JAIL", "wood_x", "cream", "stone_l")
        p.star(m, 0, 3.42, 0.36, -0.05)

    porch_depth = 1.2
    p.deck(m, -2.0, 2.0, yf - porch_depth, yf, 0.14)
    p.posts(m, [-1.86, 1.86], yf - porch_depth + 0.14, 0.14, 2.78, "wood_d")
    porch_roof(m, -2.15, 2.15, yf, porch_depth, 2.8, 3.15, "shingle", "shingle", 33)
    m.block(-2.0, yf - porch_depth, 2.0, yf, 0.0)
    p.barrel(m, -3.0, yf - 0.5, 0.0, 0.32, 0.9, 10, "gray")
    p.bench(m, 2.8, yf - 0.35, 0.0, 1.3, "gray")
    roof_clutter(m, 1.9, 2.8, 4.14)
    p.stovepipe(m, -2.2, 2.0, 4.1, 5.55)
    m.block(-hw, yf, hw, yb, 4.45)

    return m


def barber():
    m = Mesh(16)
    hw, yw, yb, depth = 3.58, -3.95, 5.3, 1.4
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    front = [(-2.1, 0.95, 1.5, 1.55), (0.2, 0.2, 1.15, 2.35), (2.3, 0.2, 1.0, 2.35)]
    flank = [(-2.3, 1.1, 1.0, 1.3), (0.1, 1.1, 1.0, 1.3), (2.5, 1.1, 1.0, 1.3)]
    rear = [(-1.6, 1.1, 1.0, 1.3)]
    rear_door = (1.8, 0.12, 1.0, 2.2)
    shell(m, -hw, hw, yw, yb, 0.12, 3.55, p.clap, "sage", {"f": front, "r": flank, "l": flank, "b": rear + [rear_door]}, 41)
    back(m, -hw, hw, yw, yb, rear, rear_door, frame="cream", shutter="ochre")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 3.55)
    windows(m, "f", -hw, hw, yw, yb, front[:1], frame="cream")

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="cream", shutter="ochre")

    profile = [(-hw - 0.12, 3.52), (0, 6.15), (hw + 0.12, 3.52)]
    p.roof_y(m, -hw, hw, yw, yb, profile, "shingle", "shingle", 44, 0.28, "cream")

    for yaw, y in ((0, yw), (180, yb)):
        with m.at(0, y, 0, yaw=yaw):
            p.gable_wall(m, [(-hw, 3.55), (0, 6.08), (hw, 3.55)], 3.55, "cream", [(0, 3.98, 0.95, 1.0)], 46, 0.38)
            p.window(m, 0, 3.98, 0.95, 1.0, "sage_d")
            m.box((-hw, -0.09, 3.46), (hw, 0.02, 3.64), "sage_d", 0.025, skip="Y")

    with m.at(0, yw, 0):
        p.door(m, 0.2, 0.2, 1.15, 2.35, "red", "cream", step=False)
        p.door(m, 2.3, 0.2, 1.0, 2.35, "ochre", "cream", glazed=False, step=False)
        p.disc(m, 0, 5.4, 0.17, -0.04, "ochre")

    front_porch(m, hw + 0.05, yw, depth, 2.82, "cream", 3)
    porch_roof(m, -hw - 0.15, hw + 0.15, yw, depth, 2.84, 3.35, "shingle", "shingle", 47)

    with m.at(0, yw - depth - 0.02, 0):
        p.sign(m, 0, 2.86, 3.2, 0.62, "ROOMS", "cream", "red_d", "red")

    p.barrel(m, -3.1, yw - 0.45, 0.2, 0.34, 0.8, 10, "gray")
    p.bench(m, -1.7, yw - 0.35, 0.2, 1.4, "wood")
    p.stovepipe(m, -2.0, 2.8, 4.4, 6.35)
    p.chimney(m, 2.1, 3.6, 4.2, 6.2, 0.5, "rust")
    m.block(-hw, yw, hw, yb, 4.6)

    return m


def mail():
    m = Mesh(17)
    hw, yw, yb, depth = 3.55, -2.95, 4.15, 1.4
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    low = [(-2.1, 0.95, 1.35, 1.5), (2.1, 0.95, 1.35, 1.5), (0, 0.2, 1.2, 2.35)]
    up = [(-1.6, 3.9, 1.0, 1.35), (1.6, 3.9, 1.0, 1.35)]
    flank = [(-1.4, 1.05, 0.95, 1.3), (1.6, 1.05, 0.95, 1.3)]
    flank_up = [(-1.4, 3.9, 0.95, 1.25), (1.6, 3.9, 0.95, 1.25)]
    rear = [(1.5, 1.05, 0.95, 1.3)]
    rear_door = (-1.5, 0.12, 1.05, 2.2)
    shell(m, -hw, hw, yw, yb, 0.12, 3.3, p.clap, "slate", {"f": low, "r": flank, "l": flank, "b": rear + [rear_door]}, 51)
    shell(m, -hw, hw, yw, yb, 3.3, 5.75, p.clap, "slate", {"f": up, "r": flank_up, "l": flank_up, "b": up}, 55)
    back(m, -hw, hw, yw, yb, rear, rear_door, frame="cream")
    back(m, -hw, hw, yw, yb, up, frame="cream", shutter="ochre")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 5.75)
    windows(m, "f", -hw, hw, yw, yb, low[:2], frame="cream", shutter=None)
    windows(m, "f", -hw, hw, yw, yb, up, frame="cream", shutter="ochre")

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="cream")
        windows(m, s, -hw, hw, yw, yb, flank_up, frame="cream", shutter="ochre")
        frame, length = side(m, s, -hw, hw, yw, yb)

        with frame:
            p.cornice(m, -length / 2, length / 2, 3.3, "cream", 0.12, 1.0, False)

    p.roof_y(m, -hw, hw, yw + 0.5, yb, [(-hw - 0.15, 5.73), (0, 6.75), (hw + 0.15, 5.73)], "shingle", "shingle", 57, 0.2, "wood_d")

    with m.at(0, yb, 0, yaw=180):
        p.gable_wall(m, [(-hw, 5.73), (0, 6.7), (hw, 5.73)], 5.73, "slate", (), 58)

    with m.at(0, yw, 0):
        p.door(m, 0, 0.2, 1.2, 2.35, "red", "cream", step=False)
        outline = [(-hw, 5.75), (hw, 5.75), (hw, 6.45), (2.6, 6.45), (2.6, 7.05), (1.75, 7.05), (1.75, 7.65), (0.8, 7.95), (-0.8, 7.95), (-1.75, 7.65), (-1.75, 7.05), (-2.6, 7.05), (-2.6, 6.45), (-hw, 6.45)]
        p.false_front(m, outline, "slate", "cream", 0.22, "slate_d")
        m.face([(u, -0.004, z) for u, z in outline], "slate")
        p.sign(m, 0, 6.05, 3.1, 0.85, "SUPPLY", "cream", "slate_d", "wood_d")
        p.disc(m, 0, 7.42, 0.3, -0.04, "cream")
        p.disc(m, 0, 7.42, 0.17, -0.07, "red")
        p.cornice(m, -hw, hw, 5.65, "cream", 0.22, 0.9)
        m.box((1.0, -0.14, 1.15), (1.38, 0.0, 1.6), "red_d", 0.025, skip="Y")
        m.quad((1.07, -0.143, 1.42), (1.31, -0.143, 1.42), (1.31, -0.143, 1.47), (1.07, -0.143, 1.47), "void")

    front_porch(m, hw + 0.05, yw, depth, 2.92, "cream", 4)
    porch_roof(m, -hw - 0.15, hw + 0.15, yw, depth, 2.94, 3.55, "shingle", "shingle", 59)
    p.bench(m, -2.2, yw - 0.35, 0.2, 1.5, "wood")
    p.crate(m, 2.9, yw - 0.45, 0.2, 0.65, 0.55, 0.5, -8)
    p.sack(m, 2.2, yw - 0.4, 0.2, 0.85, 40, "canvas")
    p.sack(m, 2.9, yw - 0.45, 0.7, 0.7, 5, "canvas")
    p.chimney(m, 2.2, 2.7, 5.4, 7.2, 0.5, "rust")
    m.block(-hw, yw, hw, yb, 5.9)

    return m


def forge():
    m = Mesh(18)
    hw, yw, yb = 3.55, -1.35, 3.62
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    front = [(-1.15, 0.12, 2.2, 2.55)]
    flank = [(0.0, 1.3, 1.1, 0.9)]
    rear = [(-1.5, 1.3, 1.1, 0.9), (1.5, 1.3, 1.1, 0.9)]
    shell(m, -hw, hw, yw, yb, 0.12, 3.45, p.planks, "gray", {"f": front, "r": flank, "l": flank, "b": rear}, 61)
    back(m, -hw, hw, yw, yb, rear, frame="wood_d", hood=False)
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 3.45, "wood_d", 0.12)
    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="wood_d", hood=False)

    profile = [(-hw - 0.14, 3.43), (0, 5.35), (hw + 0.14, 3.43)]
    p.roof_y(m, -hw, hw, yw, yb, profile, "tin", "tin", 63, 0.14, "wood_d")

    for yaw, y in ((0, yw), (180, yb)):
        with m.at(0, y, 0, yaw=yaw):
            p.gable_wall(m, [(-hw, 3.45), (0, 5.3), (hw, 3.45)], 3.45, "wood", (), 66)
            m.box((-hw, -0.09, 3.37), (hw, 0.02, 3.53), "wood_d", 0.025, skip="Y")

    with m.at(0, yw, 0):
        p.reveal(m, -1.15, 0.12, 2.2, 2.55, 0.35, "wood_x", False)
        m.quad((-2.25, 0.34, 0.12), (-0.05, 0.34, 0.12), (-0.05, 0.34, 2.67), (-2.25, 0.34, 2.67), "void")

        for u, w in ((-1.72, 1.06), (-0.25, 0.4)):
            for i in range(max(1, int(w / 0.26))):
                n = max(1, int(w / 0.26))
                a = u - w / 2 + w * i / n
                m.box((a + 0.005, -0.04, 0.14), (a + w / n - 0.005, 0.04, 2.62), p.pick("red", i, u), 0.012, skip="Yz")

            for v in (0.35, 2.25):
                m.box((u - w / 2, -0.075, v), (u + w / 2, -0.04, v + 0.14), "wood_x", skip="Y")

            if w > 0.8:
                m.beam((u - w / 2 + 0.05, -0.062, 0.49), (u + w / 2 - 0.05, -0.062, 2.25), 0.03, 0.12, "wood_x", skip="xX")

        m.box((-2.4, -0.12, 2.67), (0.1, 0.02, 2.85), "wood_d", 0.025, skip="Y")

    depth = 1.95
    p.deck(m, -hw, hw, yw - depth, yw, 0.06, "gray")
    p.posts(m, [-hw + 0.16, 0.45, hw - 0.16], yw - depth + 0.16, 0.06, 2.78, "wood_d", 0.2)
    p.slope(m, -hw - 0.12, hw + 0.12, (yw - depth - 0.12, 2.8), (yw + 0.02, 3.42), "tin", "rust", seed=65)
    m.box((-hw + 0.06, yw - depth + 0.06, 2.6), (hw - 0.06, yw - depth + 0.26, 2.78), "wood_d", 0.02)

    with m.at(-1.4, yw - depth - 0.02, 2.5):
        m.box((-0.5, -0.05, 0.0), (0.5, 0.06, 0.86), "wood_x", 0.03)
        arc = [(math.cos(a) * 0.25, math.sin(a) * 0.27 + 0.45) for a in (math.radians(-58 + 296 * i / 8) for i in range(9))]

        for (xa, za), (xb, zb) in zip(arc, arc[1:]):
            m.beam((xa, -0.085, za), (xb, -0.085, zb), 0.06, 0.12, "tin_l")

    fx, fy = 1.9, yw - 0.62
    m.box((fx - 0.75, fy - 0.45, 0.06), (fx + 0.75, fy + 0.45, 0.82), "stone", 0.05, skip="z")
    m.box((fx - 0.82, fy - 0.52, 0.82), (fx + 0.82, fy + 0.52, 0.94), "stone_d", 0.03)

    for i in range(9):
        cx = fx - 0.4 + (i % 3) * 0.4
        cy = fy - 0.24 + (i // 3) * 0.24
        m.prism((cx, cy), 0.94, 0.99 + 0.04 * (i % 2), 0.14, 0.05, 5, "ember" if i % 3 == 1 else "iron_d")

    m.loft([m.ring((fx, fy + 0.12), 0.74, 1.85, 4, math.pi / 4, 0.7), m.ring((fx, fy + 0.2), 0.3, 2.6, 4, math.pi / 4, 0.8)], "iron", "iron_d", "void")
    m.box((fx - 0.2, fy + 0.04, 2.55), (fx + 0.2, fy + 0.44, 2.95), "iron_d", skip="z")
    ax, ay = -0.4, yw - depth + 0.75
    m.prism((ax, ay), 0.06, 0.55, 0.28, 0.24, 8, "wood_d")
    m.box((ax - 0.18, ay - 0.12, 0.55), (ax + 0.18, ay + 0.12, 0.66), "iron", 0.02)
    m.box((ax - 0.1, ay - 0.09, 0.66), (ax + 0.1, ay + 0.09, 0.76), "iron_d", skip="zZ")
    m.box((ax - 0.34, ay - 0.13, 0.76), (ax + 0.26, ay + 0.13, 0.9), "iron_l", 0.025)
    m.prism((ax + 0.38, ay), 0.78, 0.88, 0.11, 0.1, 6, "iron_l", bottom=True)
    p.barrel(m, -2.85, yw - 0.6, 0.06, 0.36, 0.82)
    m.prism((-2.85, yw - 0.6), 0.82, 0.83, 0.29, 0.29, 10, "water")
    p.crate(m, -1.9, yw - 0.4, 0.06, 0.6, 0.5, 0.45, 10)

    p.chimney(m, 1.9, 0.1, 3.4, 7.7, 0.8, "stone")

    for u in (-2.0, -1.55, -1.1):
        with m.at(hw + 0.06, u + 1.6, 1.6, yaw=90):
            p.disc(m, 0, 0.25, 0.19, 0.0, "iron", 8, 0.04)
            p.disc(m, 0, 0.25, 0.11, -0.04, "rust_d", 8, 0.02)

    m.block(-hw, yw, hw, yb, 4.2)
    m.block(fx - 0.78, fy - 0.48, fx + 0.78, fy + 0.48, 0.85)
    m.block(-3.2, yw - 0.95, -2.5, yw - 0.25, 0.75)
    m.block(ax - 0.3, ay - 0.2, ax + 0.4, ay + 0.2, 0.75)

    return m


def feed():
    m = Mesh(20)
    hw, yw, yb = 3.9, -4.85, 5.05
    p.foundation(m, -hw - 0.1, yw - 0.1, hw + 0.1, yb + 0.1)
    front = [(0, 0.12, 3.1, 3.2), (-2.75, 1.3, 0.85, 1.1), (2.75, 1.3, 0.85, 1.1)]
    flank = [(-2.8, 1.5, 1.0, 1.2), (0.2, 1.5, 1.0, 1.2), (3.0, 1.5, 1.0, 1.2)]
    rear = [(-2.7, 1.5, 0.9, 1.1), (2.7, 1.5, 0.9, 1.1)]
    rear_door = (0, 0.12, 1.4, 2.4)
    shell(m, -hw, hw, yw, yb, 0.12, 5.1, p.planks, "ochre", {"f": front, "r": flank, "l": flank, "b": rear + [rear_door]}, 71)
    back(m, -hw, hw, yw, yb, rear, rear_door, True, frame="cream")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 5.1, "cream", 0.13)
    windows(m, "f", -hw, hw, yw, yb, front[1:], frame="cream")

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="cream", shutter="wood")
        frame, length = side(m, s, -hw, hw, yw, yb)

        with frame:
            m.box((-length / 2, -0.08, 3.9), (length / 2, 0.02, 4.06), "cream", 0.025, skip="Y")

    profile = [(-hw - 0.2, 5.05), (-2.85, 7.9), (0, 9.75), (2.85, 7.9), (hw + 0.2, 5.05)]
    p.roof_y(m, -hw, hw, yw, yb, profile, "shingle", "shingle", 74, 0.26, "cream")
    gable = [(-hw, 5.1), (-2.85, 7.85), (0, 9.68), (2.85, 7.85), (hw, 5.1)]

    for yaw, y in ((0, yw), (180, yb)):
        with m.at(0, y, 0, yaw=yaw):
            p.gable_wall(m, gable, 5.1, "ochre", [(0, 5.55, 1.5, 1.65)], 76)
            m.box((-hw, -0.11, 5.0), (hw, 0.02, 5.2), "cream", 0.025, skip="Y")
            p.reveal(m, 0, 5.55, 1.5, 1.65, 0.25, "wood_x")
            m.quad((-0.75, 0.2, 5.55), (0.75, 0.2, 5.55), (0.75, 0.2, 7.2), (-0.75, 0.2, 7.2), "wood_d")

            for v in (5.8, 6.82):
                for a, b in ((-0.68, -0.08), (0.08, 0.68)):
                    m.box((a, 0.15, v), (b, 0.2, v + 0.11), "cream", skip="Y")

            m.box((-0.025, 0.17, 5.55), (0.025, 0.2, 7.2), "wood_x", skip="YzZ")

            for u in (-0.86, 0.75):
                m.box((u, -0.09, 5.55), (u + 0.11, 0.02, 7.2), "cream", 0.02, skip="Y")

            m.box((-0.95, -0.12, 7.2), (0.95, 0.02, 7.35), "cream", 0.025, skip="Y")
            m.box((-0.95, -0.2, 5.42), (0.95, 0.02, 5.55), "cream", 0.025, skip="Y")

    with m.at(0, yw, 0):
        p.reveal(m, 0, 0.12, 3.1, 3.2, 0.2, "wood_x", False)

        for s in (-1, 1):
            u = s * 0.78

            for i in range(5):
                a = u - 0.76 + i * 0.304
                m.box((a + 0.004, 0.06, 0.14), (a + 0.3, 0.14, 3.28), p.pick("red", i, s), 0.012, skip="Yz")

            for v in (0.3, 3.02):
                m.box((u - 0.76, 0.02, v), (u + 0.76, 0.065, v + 0.16), "cream", 0.012, skip="Y")

            m.beam((u - s * 0.66, 0.045, 0.5), (u + s * 0.66, 0.045, 2.98), 0.03, 0.15, "cream", skip="xX")
            m.box((s * 0.22 - 0.04, -0.02, 1.35), (s * 0.22 + 0.04, 0.03, 1.62), "iron_d", skip="Y")

        for u in (-1.7, 1.55):
            m.box((u, -0.1, 0.12), (u + 0.15, 0.02, 3.32), "cream", 0.025, skip="Yz")

        m.box((-1.85, -0.18, 3.32), (1.85, 0.02, 3.46), "iron", 0.02, skip="Y")
        p.sign(m, 0, 3.78, 3.4, 0.92, "FEED", "cream", "red_d", "wood_d")

    p.barrel(m, -3.3, yw - 0.4, 0.0, 0.3, 0.85)

    for i, (u, z) in enumerate(((2.55, 0.0), (3.25, 0.0), (2.9, 0.42))):
        m.box((u - 0.34, yw - 0.5, z), (u + 0.34, yw - 0.07, z + 0.42), "straw" if i % 2 else "straw_l", 0.07, skip="z")

        for d in (-0.17, 0.15):
            m.box((u + d, yw - 0.515, z - 0.0), (u + d + 0.035, yw - 0.06, z + 0.432), "wood_x", skip="Yz")

    m.block(-hw, yw, hw, yb, 6.8)

    return m


def shack():
    m = Mesh(21)
    hw, yw, yb, depth = 2.65, -1.95, 2.75, 0.95
    p.foundation(m, -hw - 0.08, yw - 0.08, hw + 0.08, yb + 0.08)
    front = [(-0.85, 0.14, 1.05, 2.2), (1.35, 1.05, 1.0, 1.0)]
    flank = [(0.5, 1.15, 0.9, 0.85)]
    rear = [(0.8, 1.15, 0.9, 0.85)]
    shell(m, -hw, hw, yw, yb, 0.12, 2.8, p.planks, "wood", {"f": front, "r": flank, "l": flank, "b": rear}, 81)
    back(m, -hw, hw, yw, yb, rear, frame="gray_l", hood=False, shutter="teal")
    p.corner_boards(m, -hw, yw, hw, yb, 0.12, 2.8, "wood_d", 0.09)
    windows(m, "f", -hw, hw, yw, yb, front[1:], frame="gray_l", shutter="teal")

    for s in "rl":
        windows(m, s, -hw, hw, yw, yb, flank, frame="gray_l", hood=False)

    profile = [(-hw - 0.18, 2.76), (0, 4.15), (hw + 0.18, 2.76)]
    p.roof_y(m, -hw, hw, yw, yb, profile, "tin", "tin", 83, 0.18, "wood_d")

    for yaw, y in ((0, yw), (180, yb)):
        with m.at(0, y, 0, yaw=yaw):
            p.gable_wall(m, [(-hw, 2.8), (0, 4.1), (hw, 2.8)], 2.8, "gray", (), 86, 0.36)
            m.box((-hw, -0.07, 2.73), (hw, 0.02, 2.87), "wood_d", 0.02, skip="Y")

    with m.at(0, yw, 0):
        p.door(m, -0.85, 0.14, 1.05, 2.2, "red", "gray_l", glazed=False, step=False)

    p.deck(m, -hw, hw, yw - depth, yw, 0.1, "gray")
    p.posts(m, [-hw + 0.12, hw - 0.12], yw - depth + 0.11, 0.1, 2.38, "wood_d", 0.15)
    p.slope(m, -hw - 0.15, hw + 0.15, (yw - depth - 0.06, 2.4), (yw + 0.02, 2.72), "tin", "rust", seed=88)
    p.stovepipe(m, 1.4, 1.1, 3.0, 5.2)
    p.barrel(m, 2.2, yw - 0.42, 0.1, 0.27, 0.72)

    for i in range(9):
        row = 0 if i < 4 else 1 if i < 7 else 2
        k = i - (0, 4, 7)[row]
        u = -2.45 + k * 0.24 + row * 0.12
        z = 0.22 + row * 0.2
        with m.at(u, yw - 0.35, z):
            m.beam((0, -0.28, 0), (0, 0.28, 0), 0.19, 0.19, "wood_d" if i % 2 else "wood", 0.045)
            m.quad((-0.06, -0.285, -0.06), (0.06, -0.285, -0.06), (0.06, -0.285, 0.06), (-0.06, -0.285, 0.06), "straw_l")

    p.lamp(m, 0.05, yw - 0.18, 1.7, 0.65)
    m.block(-hw, yw, hw, yb, 3.4)

    return m


ALL = {
    "house_0": bank,
    "house_1": goods,
    "house_3": saloon,
    "house_4": jail,
    "house_6": barber,
    "house_7": mail,
    "house_8": forge,
    "house_10": feed,
    "house_11": shack,
}
