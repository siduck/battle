import midkit_core as m
from midkit_structures import k_rot


def plain_wall(width, height, at, color, facing=0.0, thick=0.3, band=None, band_z=None, band_color=None, plinth=0.0, plinth_color="ap_sand_d", cap=None):
    x, y, z = at
    items = [m.bx((width, thick, height), (0, thick / 2, 0), color, 0.04)]

    if plinth:
        items.append(m.bx((width + 0.06, thick + 0.1, plinth), (0, thick / 2 - 0.02, 0), plinth_color, 0.03))

    if band:
        items.append(m.bx((width + 0.06, thick + 0.1, band), (0, thick / 2 - 0.03, band_z), band_color or color, 0.025))

    if cap:
        items.append(m.bx((width + 0.2, thick + 0.2, 0.18), (0, thick / 2 - 0.05, height), cap, 0.03))

    for it in items:
        k_rot(it, facing)
        m.k.move(it, x, y, z)

    return items


def downpipe(at, height, color="ap_steel_d", r=0.07):
    x, y, z = at

    return [m.bar((x, y, z), (x, y, z + height), r, color, 6), m.bx((0.22, 0.12, 0.1), (x, y, z + height - 0.1), color, 0.01)] + [m.bx((0.16, 0.12, 0.06), (x, y, z + i * height / 3), color, 0.01) for i in range(1, 3)]


def ac_unit(at, facing=0.0, size=(1.0, 0.7, 0.8)):
    x, y, z = at
    sx, sy, sz = size
    fan = m.cyl(sz * 0.38, 0.05, (0, 0, 0), "ap_dark", 12)
    m.k.rotate(fan, 90, "X")
    m.k.move(fan, 0, -sy / 2 - 0.02, sz / 2)
    items = [m.bx(size, (0, 0, 0), "ap_steel_l", 0.03), fan]

    for i in range(4):
        items.append(m.flat((sx * 0.5, 0.03, 0.02), (sx * 0.2, -sy / 2 - 0.02, sz * 0.2 + i * 0.12), "ap_steel_d"))

    for it in items:
        m.k.rotate(it, facing)
        m.k.move(it, x, y, z)

    return items


def vent_hood(at, w=0.8, h=0.6, color="ap_steel_l"):
    x, y, z = at

    return [m.bx((w, w, h * 0.5), (x, y, z), "ap_steel_d", 0.03), m.cyl(w * 0.55, 0.06, (x, y, z + h * 0.5), color, 10), m.cyl(w * 0.18, h * 0.5, (x, y, z + h * 0.5), "ap_steel_d", 8)]
