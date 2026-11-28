import math

import midkit_core as m
import midkit_structures as st
import midkit_walls as wl


def hangar():
    m.setup()
    W, D, E, R = 54.6, 46.6, 17.5, 6.8
    hw, hd = W / 2, D / 2
    P = []
    P.append(m.bx((W - 0.4, D - 0.4, 0.15), (0, 0, 0), "ap_sand_d", 0.02))

    for sx in (-1, 1):
        P.append(m.flat((0.25, D - 2, 0.02), (sx * (hw - 3.0), 0, 0.15), "ap_yellow"))

    P.append(m.flat((W - 6, 0.25, 0.02), (0, -hd + 4.0, 0.15), "ap_yellow"))
    P += st.clad_wall(W, E, (0, hd, 0), "ap_sand_l", facing=180)
    P += st.clad_wall(D, E, (-hw, 0, 0), "ap_sand_l", facing=-90)
    P += st.clad_wall(D, E, (hw, 0, 0), "ap_sand_l", facing=90)
    P += st.clad_wall(hw - 22, E, (-(22 + (hw - 22) / 2), -hd, 0), "ap_sand_l")
    P += st.clad_wall(hw - 22, E, ((22 + (hw - 22) / 2), -hd, 0), "ap_sand_l")
    P += st.clad_wall(44, E - 14, (0, -hd, 14), "ap_sand_l", plinth=0)
    P.append(m.bx((46, 0.9, 1.1), (0, -hd - 0.25, 14.0), "ap_orange", 0.06))
    P.append(m.bx((46, 0.35, 0.3), (0, -hd - 0.35, 13.75), "ap_steel_d", 0.04))

    for sx in (-1, 1):
        P.append(m.bx((0.9, 0.8, 14.2), (sx * 22.45, -hd - 0.2, 0), "ap_orange", 0.06))

    P += st.gable_end(W, E, R, (0, -hd, 0), "ap_sand_l", trim="ap_steel_d", ribs=1.8)
    back = st.gable_end(W, E, R, (0, 0, 0), "ap_sand_l", trim="ap_steel_d", ribs=1.8)
    m.rot(back, 180)
    m.mv(back, 0, hd, 0)
    P += back
    P += st.gable_roof_y(W, D, E, R, color="ap_steel", ridge="ap_steel_d", overhang=0.4, rib_gap=3.0, rib_color="ap_steel_l")

    for sx in (-1, 1):
        P += st.pilaster_row(D, E, (sx * hw, 0, 0), 6.0, color="ap_steel_d", axis="y", depth=0.35, width=0.45, side=sx)

    for sx in (-1, 1):
        for i in range(7):
            yy = -hd + 3.0 + i * 6.2 + 3.1

            if yy > hd - 2:
                continue

            P += m.window_on(3.0, 2.2, (sx * hw, yy, 12.6), facing=-90 * sx, panes=3)

    for side in (-1, 1):
        for j in range(2):
            xc = side * (19.5 - j * 5.0)
            yy = -hd - 0.75 - j * 0.65
            P.append(m.bx((4.9, 0.4, 14.0), (xc, yy, 0.0), "ap_steel_l", 0.04))
            P.append(m.bx((5.1, 0.5, 0.25), (xc, yy, 13.9), "ap_steel_d", 0.03))

            for r in range(1, 7):
                P.append(m.flat((4.6, 0.06, 0.1), (xc, yy - 0.22, r * 1.9), "ap_steel_d"))

            P.append(m.bx((0.18, 0.3, 14.0), (xc - 2.35, yy - 0.05, 0.0), "ap_orange", 0.02))

    P.append(m.bx((44.0, 0.25, 0.3), (0, -hd - 0.1, 0.0), "ap_sand_d", 0.02))

    for i in range(6):
        yy = -hd + 5.0 + i * 8.0

        for s in (-1, 1):
            P.append(m.bx((0.5, 0.5, E - 0.2), (s * (hw - 0.6), yy, 0.15), "ap_steel_d", 0.04))
            P.append(m.bar((s * (hw - 0.6), yy, E - 0.4), (s * 0.4, yy, E + R - 0.8), 0.3, "ap_steel", 4))

        P.append(m.bar((-hw + 0.6, yy, E - 0.4), (hw - 0.6, yy, E - 0.4), 0.14, "ap_steel_d", 4))

        for lx in (-12, 12):
            P.append(m.bar((lx, yy, E + R * (1 - abs(lx) / hw) - 1.3), (lx, yy, E + R * (1 - abs(lx) / hw) - 2.8), 0.04, "ap_steel_d", 4))
            P.append(m.bx((3.0, 0.4, 0.22), (lx, yy, E + R * (1 - abs(lx) / hw) - 3.0), "ap_white", 0.03))

    door = m.bx((0.2, 1.1, 2.15), (hw + 0.2, hd - 10.0, 0.0), "ap_steel_d", 0.02)
    P.append(door)
    P.append(m.bx((1.3, 1.9, 0.12), (hw + 0.55, hd - 10.0, 2.45), "ap_orange", 0.03))
    P.append(m.bx((0.7, 1.5, 0.15), (hw + 0.45, hd - 10.0, 0.0), "ap_sand_d", 0.02))

    for i in range(5):
        vy = -hd + 6 + i * 9
        P += wl.vent_hood((0.0, vy, E + R - 0.05), w=1.1, h=1.2)

    for s in (-1, 1):
        P += wl.downpipe((s * (hw + 0.1), -hd + 0.5, 0.5), E - 0.8)
        P += wl.downpipe((s * (hw + 0.1), hd - 0.5, 0.5), E - 0.8)

    P += m.bolts([(x, -hd - 0.5, 0.1) for x in (-hw + 0.4, -22.4, 22.4, hw - 0.4)], r=0.07, h=0.06)
    ob = m.finish("hangar", P, budget=14000)

    return ob


def cargo():
    m.setup()
    W, D, E, R = 30.4, 22.4, 7.8, 1.8
    hw, hd = W / 2, D / 2
    P = []
    P.append(m.bx((W - 0.4, D - 0.4, 0.15), (0, 0, 0), "ap_sand_d", 0.02))
    P += st.clad_wall(W, E, (0, hd, 0), "ap_sand_l", facing=180, pitch=1.0)
    P += st.clad_wall(D, E, (-hw, 0, 0), "ap_sand_l", facing=-90, pitch=1.0)
    P += st.clad_wall(D, E, (hw, 0, 0), "ap_sand_l", facing=90, pitch=1.0)
    P += st.clad_wall(5.6, E, (-hw + 2.8, -hd, 0), "ap_sand_l", pitch=1.0)
    P += st.clad_wall(5.6, E, (hw - 2.8, -hd, 0), "ap_sand_l", pitch=1.0)
    P += st.clad_wall(W - 11.2, 3.6, (0, -hd, E - 3.6), "ap_sand_l", pitch=1.0, plinth=0)
    P.append(m.bx((W, 1.2, 0.8), (0, -hd - 0.2, E - 0.4), "ap_orange", 0.05))
    P += st.gable_end(W, E, R, (0, -hd, 0), "ap_sand_l", trim="ap_steel_d", ribs=1.6)
    back = st.gable_end(W, E, R, (0, 0, 0), "ap_sand_l", trim="ap_steel_d", ribs=1.6)
    m.rot(back, 180)
    m.mv(back, 0, hd, 0)
    P += back
    P += st.gable_roof_y(W, D, E, R, color="ap_steel", ridge="ap_steel_d", overhang=0.35, rib_gap=2.5, rib_color="ap_steel_l")
    open_x = [-6.0, 0.0, 6.0]

    for x in open_x:
        P += st.door_roller(4.0, 4.4, (x, -hd - 0.3, 0.0), open_frac=0.0)
        P.append(m.bx((4.0, 0.7, 0.3), (x, -hd - 0.6, 0.2), "ap_dark", 0.03))

    P.append(m.bx((W - 4.0, 1.0, 0.9), (0, -hd - 0.65, 0.0), "ap_sand", 0.04))

    for bx_ in (-8.0, -3.0, 3.0, 8.0):
        P.append(m.bx((0.5, 0.5, 0.9), (bx_, -hd - 1.3, 0.0), "ap_rubber", 0.05))

    P.append(m.bx((W - 3.0, 0.1, 0.2), (0, -hd - 0.3, 3.6), "ap_steel_d", 0.01))

    for sx in (-1, 1):
        for i in range(4):
            P += m.window_on(1.6, 1.1, (sx * hw, -hd + 4.0 + i * 5.2, 5.6), facing=-90 * sx, panes=2)

    for sx in (-1, 1):
        P += st.pilaster_row(D, E, (sx * hw, 0, 0), 5.8, color="ap_steel_d", axis="y", depth=0.3, width=0.4, side=sx)

    P.append(m.bx((0.2, 1.1, 2.15), (hw + 0.2, hd - 5.0, 0.0), "ap_steel_d", 0.02))
    P.append(m.bx((1.3, 1.9, 0.12), (hw + 0.55, hd - 5.0, 2.45), "ap_orange", 0.03))
    P.append(m.bx((0.9, 1.5, 0.15), (hw + 0.5, hd - 5.0, 0.0), "ap_sand_d", 0.02))

    for i in range(3):
        P += wl.vent_hood((0.0, -hd + 5 + i * 7, E + R - 0.05), w=1.0, h=1.0)

    for sx in (-1, 1):
        P += wl.downpipe((sx * (hw + 0.1), -hd + 0.4, 0.5), E - 0.8)
        P += wl.downpipe((sx * (hw + 0.1), hd - 0.4, 0.5), E - 0.8)

    P += wl.ac_unit((hw + 0.5, 4.0, 1.2), facing=90)
    ob = m.finish("cargo", P, budget=9000)

    return ob


def fire():
    m.setup()
    P = []
    P.append(m.bx((23.6, 19.6, 0.15), (0, 0, 0), "ap_sand_d", 0.02))
    bw, bd, bh = 24.0, 14.0, 7.2
    by = -10 + bd / 2
    f = by - bd / 2
    P += wl.plain_wall(bw, bh, (0, f, 0), "ap_sand_l", plinth=0.8, cap="ap_sand", band=0.4, band_z=bh - 1.0, band_color="ap_orange")
    openings = []

    for s in (-1, 1):
        P += wl.plain_wall(bd, bh, (s * (bw / 2 - 0.15), by, 0), "ap_sand_l", facing=-90 * s, plinth=0.8, cap="ap_sand")

    P += wl.plain_wall(bw, bh, (0, f + bd, 0), "ap_sand_l", facing=180, plinth=0.8, cap="ap_sand")
    P.append(m.bx((bw - 0.2, bd - 0.2, 0.3), (0, by, bh), "ap_steel_d", 0.04))
    P.append(m.bx((bw + 0.4, bd + 0.4, 0.3), (0, by, bh + 0.3), "ap_sand", 0.05))

    for x in (-7.8, 0.0, 7.8):
        P += st.door_roller(5.2, 4.6, (x, f - 0.15, 0.0), frame="ap_orange", color="ap_steel_l")

    P.append(m.bx((bw - 2, 0.5, 0.35), (0, f - 0.3, 5.0), "ap_orange", 0.03))

    for x in (-7.8, 0.0, 7.8):
        P += m.window_on(4.2, 1.0, (x, f, 5.5), panes=3)

    for s in (-1, 1):
        for i in range(3):
            P += m.window_on(1.6, 1.3, (s * (bw / 2), f + 3.0 + i * 4.0, 2.6), facing=-90 * s, panes=2)

    wy0 = f + bd
    ww, wd, wh = 14.0, 5.0, 10.0
    P += wl.plain_wall(ww, wh, (-4.0, wy0 + wd, 0), "ap_sand_l", facing=180, plinth=0.8)
    P += wl.plain_wall(wd, wh, (-4.0 - ww / 2 + 0.15, wy0 + wd / 2, 0), "ap_sand_l", facing=-90, plinth=0.8)
    P += wl.plain_wall(wd, wh, (-4.0 + ww / 2 - 0.15, wy0 + wd / 2, 0), "ap_sand_l", facing=90, plinth=0.8)
    P.append(m.bx((ww + 0.4, wd + 0.4, 0.3), (-4.0, wy0 + wd / 2, wh), "ap_sand", 0.05))
    P.append(m.bx((ww - 0.4, wd - 0.4, 0.2), (-4.0, wy0 + wd / 2, wh - 0.25), "ap_steel_d", 0.02))

    for i in range(4):
        P += m.window_on(1.5, 1.4, (-4.0 - 4.5 + i * 3.0, wy0 + wd, 4.5), facing=180, panes=2)
        P += m.window_on(1.5, 1.4, (-4.0 - 4.5 + i * 3.0, wy0 + wd, 7.4), facing=180, panes=2)

    tx, ty = 9.0, wy0 + 3.5
    tw = 4.2
    P += wl.plain_wall(tw, 14.0, (tx, ty - tw / 2, 0), "ap_sand", plinth=0.8)
    P += wl.plain_wall(tw, 14.0, (tx, ty + tw / 2, 0), "ap_sand", facing=180, plinth=0.8)
    P += wl.plain_wall(tw, 14.0, (tx - tw / 2 + 0.15, ty, 0), "ap_sand", facing=-90, plinth=0.8)
    P += wl.plain_wall(tw, 14.0, (tx + tw / 2 - 0.15, ty, 0), "ap_sand", facing=90, plinth=0.8)

    for z in (3.0, 6.0, 9.0):
        P.append(m.bx((tw + 0.3, tw + 0.3, 0.25), (tx, ty, z), "ap_orange" if z == 9.0 else "ap_sand_d", 0.03))

    for s in (0, 90, 180, -90):
        P += m.window_on(1.1, 1.8, (tx + (0 if s in (0, 180) else (-tw / 2 if s == -90 else tw / 2)), ty + (-tw / 2 if s == 0 else tw / 2 if s == 180 else 0), 10.3), facing=s, panes=1)

    P.append(m.bx((tw + 0.8, tw + 0.8, 0.4), (tx, ty, 14.0), "ap_steel_d", 0.05))
    P.append(m.bx((tw + 0.2, tw + 0.2, 1.3), (tx, ty, 14.4), "ap_sand", 0.05))
    P += m.railing(tw + 0.8, 1.0, (tx, ty - tw / 2 - 0.4, 14.4), "ap_steel_d", axis="x")
    P += m.railing(tw + 0.8, 1.0, (tx, ty + tw / 2 + 0.4, 14.4), "ap_steel_d", axis="x")
    P += m.railing(tw + 0.8, 1.0, (tx - tw / 2 - 0.4, ty, 14.4), "ap_steel_d", axis="y")
    P += m.railing(tw + 0.8, 1.0, (tx + tw / 2 + 0.4, ty, 14.4), "ap_steel_d", axis="y")
    P.append(m.cyl(0.09, 2.5, (tx + 1.0, ty + 1.0, 14.8), "ap_steel_d", 6))
    P.append(m.bx((1.2, 1.2, 0.2), (tx, ty, 15.7), "ap_steel", 0.03))
    P.append(m.cyl(0.12, 1.4, (tx, ty, 15.9), "ap_steel_d", 6))
    P.append(m.bx((0.3, 0.3, 0.3), (tx, ty, 16.8), "ap_orange", 0.03))

    for x in (-10.8, 10.8):
        P += wl.downpipe((x, f - 0.1, 0.5), bh - 0.8)

    P += wl.ac_unit((-9.0, wy0 + wd + 0.5, 0.0), facing=180)
    P += wl.vent_hood((-6.0, by - 1.0, bh + 0.6), w=1.2, h=1.0)
    P += wl.vent_hood((6.0, by + 2.0, bh + 0.6), w=1.2, h=1.0)
    P += wl.vent_hood((-4.0, wy0 + wd / 2, wh + 0.5), w=1.0, h=1.0)
    ob = m.finish("fire", P, budget=9000)

    return ob


ALL = {"hangar": hangar, "cargo": cargo, "fire": fire}
