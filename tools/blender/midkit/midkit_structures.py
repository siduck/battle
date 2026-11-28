import math

import midkit_core as m


def gable_roof_y(w, d, eave, rise, at=(0, 0), color="ap_steel_l", ridge="ap_steel_d", overhang=0.4, thick=0.18, rib_gap=1.5, rib_color=None, gutter="ap_steel_d"):
    x, y = at
    hw = w / 2
    t = rise / hw
    ov = overhang
    out = [(-hw - ov, eave - ov * t), (0, eave + rise), (hw + ov, eave - ov * t), (hw + ov, eave - ov * t - thick), (0, eave + rise - thick * 1.15), (-hw - ov, eave - ov * t - thick)]
    items = [m.sweep_xz(out, d + 2 * ov, (x, y, 0), color)]
    n = max(2, int(d / rib_gap))
    rc = rib_color or color

    for i in range(n + 1):
        yy = y - d / 2 + i * d / n

        for s in (-1, 1):
            items.append(m.bar((x + s * (hw + ov * 0.9), yy, eave - ov * t * 0.9 + 0.04), (x + s * 0.12, yy, eave + rise + 0.03), 0.05, rc, 4))

    items.append(m.bx((0.7, d + 2 * ov + 0.1, 0.3), (x, y, eave + rise - 0.2), ridge, 0.05))

    for s in (-1, 1):
        items.append(m.bar((x + s * (hw + ov), y - d / 2 - ov, eave - ov * t - thick - 0.1), (x + s * (hw + ov), y + d / 2 + ov, eave - ov * t - thick - 0.1), 0.09, gutter, 6))

    return items


def gable_end(w, eave, rise, at, color, trim=None, facing=0.0, depth=0.25, ribs=0.0, rib_color=None):
    x, y, z = at
    hw = w / 2
    items = [m.sweep_xz([(-hw, 0), (hw, 0), (0, rise)], depth, (x, y, z + eave), color)]

    if ribs:
        n = int(w / ribs)

        for i in range(1, n):
            rx = -hw + i * ribs
            h = rise * (1 - abs(rx) / hw) - 0.2

            if h > 0.4:
                items.append(m.flat((0.1, 0.07, h), (x + rx, y - depth / 2 - 0.02, z + eave + 0.05), rib_color or color))

    if trim:
        t = rise / hw
        ang = math.degrees(math.atan2(rise, hw))

        for s in (-1, 1):
            a = (x + s * hw, y - depth / 2 - 0.05, z + eave)
            b = (x, y - depth / 2 - 0.05, z + eave + rise)
            items.append(m.bar(a, b, 0.07, trim, 4))

    return items


def clad_wall(width, height, at, color, pitch=1.2, facing=0.0, depth=0.12, base="ap_sand_d", plinth=0.5):
    x, y, z = at
    items = []

    if plinth:
        items.append(m.bx((width, 0.3, plinth), (0, -0.04, 0), base, 0.03))

    sheet = m.corrugated(width, height - plinth, (0, 0, plinth), color, pitch=pitch, depth=depth)

    for it in sheet:
        m.k.rotate(it, 180)

    items += sheet

    for it in items:
        k_rot(it, facing)
        m.k.move(it, x, y, z)

    return items


def k_rot(it, facing):
    if facing:
        m.k.rotate(it, facing)


def pilaster_row(length, height, at, step, color="ap_sand", axis="x", depth=0.4, width=0.5, side=-1):
    x, y, z = at
    n = max(1, int(length / step))
    items = []

    for i in range(n + 1):
        p = -length / 2 + i * length / n

        if axis == "x":
            items.append(m.bx((width, depth, height), (x + p, y + side * depth / 2, z), color, 0.04))
        else:
            items.append(m.bx((depth, width, height), (x + side * depth / 2, y + p, z), color, 0.04))

    return items


def door_roller(w, h, at, color="ap_steel_l", frame="ap_orange", rib=0.12, open_frac=0.0, facing=0.0):
    x, y, z = at
    items = [m.flat((w, 0.1, h), (0, 0.06, 0), "ap_void")]
    top = h * (1 - open_frac)
    n = int(top / rib)

    for i in range(n):
        items.append(m.flat((w - 0.2, 0.05 + 0.015 * (i % 2), rib - 0.005), (0, 0.02, h - (i + 1) * rib), color))

    for s in (-1, 1):
        items.append(m.bx((0.22, 0.28, h + 0.2), (s * (w / 2 + 0.11), -0.04, 0), frame, 0.03))

    items.append(m.bx((w + 0.7, 0.4, 0.4), (0, -0.08, h), frame, 0.05))

    for it in items:
        k_rot(it, facing)
        m.k.move(it, x, y, z)

    return items


def fluorescent(len_, at, color="ap_white"):
    x, y, z = at

    return [m.bar((x - len_ / 2, y, z), (x + len_ / 2, y, z), 0.06, color, 4)]
