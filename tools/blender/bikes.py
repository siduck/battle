import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/hb")

import math
import os
from veh import Kit, wheel, render

OUT = sys.argv[sys.argv.index("--") + 1]
PREV = sys.argv[sys.argv.index("--") + 2]

slate = "3E4349"
seat = "2F3338"
tyre = "34373B"
chrome = "B9BCBD"
steel = "7A7E80"
rim = "8A8F93"
lamp = "E8D9B5"
plastic = "D9D3C6"


def dirt(name, accent, wr, fz, rz):
    k = Kit()
    head_top = (0, 0.88, 0.47)
    head_bot = (0, 0.7, 0.53)

    k.line(head_top, head_bot, 0.032, slate, seg=14)

    for s in (-1, 1):
        k.line((s * 0.07, 0.94, 0.45), (s * 0.07, 0.6, 0.6), 0.028, chrome, seg=14)
        k.line((s * 0.07, 0.62, 0.595), (s * 0.07, wr, fz), 0.022, "C49A3A", seg=14)
        k.tube([(s * 0.09, 0.43, -0.13), (s * 0.095, 0.36, -0.42), (s * 0.08, wr, rz)], 0.02, steel)
        k.tube([(s * 0.11, 0.42, 0.06), (s * 0.15, 0.4, 0.05)], 0.012, steel)

    k.box((0, 0.92, 0.47), (0.2, 0.035, 0.07), steel, bev=0.3)
    k.box((0, 0.76, 0.5), (0.2, 0.03, 0.07), steel, bev=0.3)
    k.tube([(-0.36, 1.0, 0.4), (-0.2, 0.98, 0.43), (0, 0.97, 0.45), (0.2, 0.98, 0.43), (0.36, 1.0, 0.4)], 0.012, slate)

    for s in (-1, 1):
        k.line((s * 0.28, 0.995, 0.41), (s * 0.38, 1.0, 0.395), 0.019, seat, seg=12)

    k.tube([(0, 0.86, 0.45), (0, 0.84, 0.2), (0, 0.8, -0.02), (0, 0.8, -0.3), (0, 0.79, -0.55)], 0.022, slate)
    k.tube([(0, 0.7, 0.51), (0, 0.45, 0.36), (0, 0.27, 0.18), (0, 0.25, -0.02), (0, 0.42, -0.14), (0, 0.78, -0.08)], 0.02, slate)
    k.box((0, 0.42, 0.12), (0.2, 0.26, 0.3), steel, bev=0.18)
    k.box((0, 0.6, 0.16), (0.17, 0.12, 0.16), steel, bev=0.2)

    for i in range(4):
        k.box((0, 0.56 + i * 0.03, 0.16), (0.2, 0.008, 0.18), "8C9093", bev=0.3)

    k.cyl((0.12, 0.4, 0.06), (1, 0, 0), 0.08, 0.04, "6A7275", seg=24, bevel=0.01)
    k.egg((0, 0.85, 0.25), (0.14, 0.1, 0.2), accent)

    for s in (-1, 1):
        k.box((s * 0.12, 0.79, 0.33), (0.025, 0.15, 0.24), accent, rot=(0.0, 0, s * -0.12), bev=0.3)
        k.box((s * 0.11, 0.77, -0.32), (0.025, 0.12, 0.28), plastic, rot=(0.15, 0, 0), bev=0.3)

    k.box((0, 0.915, -0.18), (0.2, 0.06, 0.74), seat, rot=(0.05, 0, 0), bev=0.35)
    k.egg((0, 0.84, -0.74), (0.1, 0.05, 0.36), accent, rot=(-0.16, 0, 0), seg=16)
    k.box((0, 0.86, -0.62), (0.2, 0.05, 0.3), accent, rot=(-0.12, 0, 0), bev=0.45)
    k.box((0, 0.63, 0.76), (0.15, 0.035, 0.44), plastic, rot=(0.2, 0, 0), bev=0.35)
    k.box((0, 0.84, 0.6), (0.24, 0.2, 0.025), plastic, rot=(0.35, 0, 0), bev=0.4)
    k.cyl((0, 0.85, 0.615), (0, 0.33, 1), 0.045, 0.02, lamp, seg=20)
    k.line((0, 0.79, -0.15), (0, 0.5, -0.36), 0.03, accent, seg=14)
    k.line((0, 0.77, -0.16), (0, 0.52, -0.35), 0.018, chrome, seg=10)
    k.tube([(0.06, 0.48, 0.26), (0.1, 0.36, 0.22), (0.14, 0.4, 0.0), (0.15, 0.58, -0.3)], 0.022, steel)
    k.cyl((0.16, 0.7, -0.55), (0, -0.35, -1), 0.05, 0.4, chrome, seg=20, bevel=0.01)

    for s in (-1, 1):
        k.box((s * 0.15, 0.34, -0.02), (0.08, 0.02, 0.04), steel, bev=0.3)

    k.finish(f"{OUT}/{name}/body.glb", 0.2, 0.8)

    for part in ("wheelF", "wheelR"):
        k = Kit()
        wheel(k, wr, 0.05, 0.045, rim, tyre, 24, steel, knobs=True, disc=steel if part == "wheelF" else None)
        k.finish(f"{OUT}/{name}/{part}.glb", -wr, 2 * wr)


def bicycle(name, style, frame, wr, fz, rz):
    k = Kit()
    bb = (0, wr + 0.01, -0.03)
    head_top = (0, wr + 0.6, fz - 0.17)
    head_bot = (0, wr + 0.44, fz - 0.12)
    seat_top = (0, wr + 0.56, -0.2)

    if style == "mtb":
        head_top = (0, wr + 0.52, fz - 0.2)
        head_bot = (0, wr + 0.34, fz - 0.13)
        seat_top = (0, wr + 0.48, -0.17)
    sz = rz

    if style == "city":
        k.tube([head_bot, (0, wr + 0.3, fz - 0.3), (0, wr + 0.06, 0.05), bb], 0.022, frame)
        k.tube([head_top, (0, wr + 0.42, fz - 0.35), (0, wr + 0.12, 0.0)], 0.018, frame)
    else:
        k.line(head_top, seat_top, 0.019 if style == "road" else 0.024, frame)
        k.line(head_bot, bb, 0.022 if style == "road" else 0.028, frame)

    k.line(bb, seat_top, 0.019, frame)
    k.line(head_top, head_bot, 0.024, frame)

    for s in (-1, 1):
        k.line((s * 0.05, wr, sz), bb, 0.011, frame, seg=8)
        k.line((s * 0.05, wr, sz), (s * 0.015, seat_top[1] - 0.03, seat_top[2] - 0.02), 0.01, frame, seg=8)
        fork_r = 0.022 if style == "mtb" else 0.013
        k.tube([(s * 0.04, head_bot[1] - 0.02, head_bot[2] + 0.01), (s * 0.045, wr + 0.2, fz - 0.03), (s * 0.045, wr, fz)], fork_r, chrome if style == "mtb" else frame)

    post_top = (0, seat_top[1] + 0.12, seat_top[2] - 0.05)
    k.line(seat_top, post_top, 0.012, chrome)
    k.box((0, post_top[1] + 0.02, post_top[2] - 0.02), (0.12, 0.045, 0.24), seat, rot=(0.0, 0, 0), bev=0.4)
    stem = (0, head_top[1] + 0.08, head_top[2] - 0.02)
    k.line(head_top, stem, 0.016, chrome)

    if style == "road":
        k.tube([(-0.2, stem[1], stem[2] + 0.06), (-0.21, stem[1] - 0.04, stem[2] + 0.14), (-0.2, stem[1] - 0.14, stem[2] + 0.1), (-0.2, stem[1] - 0.16, stem[2] + 0.02)], 0.012, seat)
        k.tube([(0.2, stem[1], stem[2] + 0.06), (0.21, stem[1] - 0.04, stem[2] + 0.14), (0.2, stem[1] - 0.14, stem[2] + 0.1), (0.2, stem[1] - 0.16, stem[2] + 0.02)], 0.012, seat)
        k.line((-0.2, stem[1], stem[2] + 0.06), (0.2, stem[1], stem[2] + 0.06), 0.012, seat)
        k.line(stem, (0, stem[1], stem[2] + 0.06), 0.014, chrome)
    else:
        back = -0.08 if style == "city" else 0.0
        bar = [(-0.3, stem[1] + 0.02, stem[2] + back), (-0.15, stem[1], stem[2] + 0.04), (0.15, stem[1], stem[2] + 0.04), (0.3, stem[1] + 0.02, stem[2] + back)]
        k.tube(bar, 0.012, chrome if style == "city" else seat)

        for s in (-1, 1):
            k.line((s * 0.24, bar[0][1], bar[0][2] + 0.01), (s * 0.33, bar[0][1] + 0.005, bar[0][2] - 0.01), 0.017, seat, seg=12)

    k.cyl((0.07, bb[1], bb[2]), (1, 0, 0), 0.09, 0.008, steel, seg=28)
    k.cyl((0.07, bb[1], bb[2]), (1, 0, 0), 0.05, 0.012, "6A7275", seg=20)

    for s, ang in ((1, 0.5), (-1, 0.5 + math.pi)):
        tip = (s * 0.1, bb[1] + math.sin(ang) * -0.16, bb[2] + math.cos(ang) * 0.16)
        k.line((s * 0.08, bb[1], bb[2]), tip, 0.01, steel, seg=8)
        k.box((s * 0.14, tip[1], tip[2]), (0.08, 0.02, 0.05), seat, bev=0.3)

    k.line((0.07, bb[1] + 0.09, bb[2]), (0.06, wr + 0.04, sz), 0.004, "55595C", seg=4)
    k.line((0.07, bb[1] - 0.09, bb[2]), (0.06, wr - 0.04, sz), 0.004, "55595C", seg=4)

    if style == "city":
        for zc, a0, a1 in ((fz, 0.12, 0.72), (sz, 0.3, 0.95)):
            pts = []

            for i in range(9):
                a = math.pi * (a0 + (a1 - a0) * i / 8)
                pts.append((0, wr + math.sin(a) * (wr + 0.04), zc + math.cos(a) * (wr + 0.04)))

            k.tube(pts, 0.028, frame, res=1)

        k.box((0, wr + 0.36, sz + 0.06), (0.16, 0.015, 0.34), steel, bev=0.3)

        for s in (-1, 1):
            k.line((s * 0.07, wr + 0.36, sz - 0.08), (s * 0.05, wr, sz), 0.008, steel, seg=6)

        k.box((0.07, bb[1] + 0.02, (bb[2] + sz) / 2 + 0.05), (0.02, 0.12, 0.5), frame, bev=0.4)
        k.box((0, stem[1] - 0.12, stem[2] + 0.2), (0.3, 0.2, 0.24), "8C6A44", bev=0.15)
        k.cyl((0, stem[1] - 0.06, stem[2] + 0.12), (0, 0, 1), 0.035, 0.03, lamp, seg=16)

    if style == "mtb":
        k.line((0, seat_top[1] - 0.08, seat_top[2] + 0.02), (0, wr + 0.2, sz + 0.2), 0.022, "C49A3A", seg=12)

    k.finish(f"{OUT}/{name}/body.glb", 0.0, wr + 0.7)

    for part in ("wheelF", "wheelR"):
        k = Kit()

        if style == "road":
            wheel(k, wr, 0.016, 0.014, rim, tyre, 24, steel)
        elif style == "city":
            wheel(k, wr, 0.022, 0.02, rim, tyre, 24, steel)
        else:
            wheel(k, wr, 0.034, 0.034, rim, tyre, 24, steel, knobs=True, disc=steel if part == "wheelF" else None)

        k.finish(f"{OUT}/{name}/{part}.glb", -wr, 2 * wr)


def moto(name, style, main, second, wr, fz, rz):
    k = Kit()
    zc = (fz + rz) / 2
    rake = 0.34 if style == "chopper" else 0.2
    head_bot = (0, wr + 0.36, fz - 0.16)
    head_top = (0, wr + 0.56, fz - 0.16 - rake * 0.6)

    if style == "chopper":
        head_bot = (0, wr + 0.44, fz - 0.3)
        head_top = (0, wr + 0.62, fz - 0.44)

    k.line(head_top, head_bot, 0.034, slate, seg=14)

    for s in (-1, 1):
        k.line((s * 0.075, head_top[1] + 0.04, head_top[2] - 0.02), (s * 0.075, wr, fz), 0.024 if style != "cruiser" else 0.03, chrome, seg=14)
        k.tube([(s * 0.095, wr + 0.14, zc - 0.12), (s * 0.1, wr + 0.06, (zc + rz) / 2), (s * 0.085, wr, rz)], 0.022, steel if style not in ("chopper", "cruiser") else chrome)
        if style not in ("sport", "police"):
            k.line((s * 0.08, wr + 0.5, rz + 0.3), (s * 0.09, wr + 0.08, rz + 0.18), 0.022, second, seg=12)

    k.box((0, head_top[1] + 0.04, head_top[2]), (0.2, 0.035, 0.07), steel, bev=0.3)
    k.box((0, head_bot[1] - 0.02, head_bot[2] + 0.02), (0.2, 0.03, 0.07), steel, bev=0.3)

    bar_y = head_top[1] + 0.1
    bar_z = head_top[2] - 0.06

    if style in ("sport", "police"):
        for s in (-1, 1):
            k.line((s * 0.08, head_top[1] + 0.02, head_top[2] - 0.02), (s * 0.3, head_top[1] - 0.01, head_top[2] - 0.08), 0.014, slate, seg=10)
            k.line((s * 0.24, head_top[1] - 0.005, head_top[2] - 0.07), (s * 0.32, head_top[1] - 0.012, head_top[2] - 0.09), 0.019, seat, seg=12)
    else:
        rise = 0.16 if style == "chopper" else 0.0
        bar = [(-0.36, bar_y + rise, bar_z - 0.12), (-0.18, bar_y + rise * 0.7, bar_z - 0.02), (0, bar_y, bar_z), (0.18, bar_y + rise * 0.7, bar_z - 0.02), (0.36, bar_y + rise, bar_z - 0.12)]
        k.tube(bar, 0.012, chrome if style in ("chopper", "cruiser", "street") else slate)

        for s in (-1, 1):
            e = bar[0] if s < 0 else bar[-1]
            k.line((s * 0.27, e[1] - 0.003, e[2] + 0.03), (s * 0.38, e[1], e[2] - 0.02), 0.019, seat, seg=12)

    spine = [head_top, (0, wr + 0.5, zc + 0.25), (0, wr + 0.46, zc - 0.1), (0, wr + 0.48, rz + 0.3)]
    down = [head_bot, (0, wr + 0.08, zc + 0.3), (0, wr - 0.04, zc), (0, wr + 0.12, zc - 0.14)]
    k.tube(spine, 0.022, slate)
    k.tube(down, 0.022, slate)

    eng_y = wr + 0.08
    k.box((0, eng_y, zc + 0.08), (0.26, 0.26, 0.36), steel, bev=0.18)

    if style in ("chopper", "cruiser"):
        for s, dz in ((1, 0.12), (-1, -0.06)):
            k.cyl((0, eng_y + 0.22, zc + dz + 0.06), (0, 1, s * 0.5), 0.07, 0.22, chrome, seg=20, bevel=0.008)

            for i in range(4):
                k.cyl((0, eng_y + 0.16 + i * 0.035, zc + dz + 0.06 + s * i * 0.017), (0, 1, s * 0.5), 0.085, 0.01, "9EA2A4", seg=20)
    else:
        for i in range(4):
            k.box((0, eng_y + 0.16 + i * 0.03, zc + 0.12), (0.24, 0.008, 0.2), "8C9093", bev=0.3)

    k.cyl((0.14, eng_y, zc + 0.05), (1, 0, 0), 0.09, 0.04, "6A7275", seg=24, bevel=0.01)

    for s in (-1, 1):
        k.box((s * 0.17, wr - 0.02, zc - 0.05), (0.09, 0.02, 0.05), steel, bev=0.3)

    if style in ("sport", "police"):
        fair = main if style == "sport" else plastic
        k.box((0, wr + 0.44, fz - 0.26), (0.32, 0.3, 0.4), fair, rot=(0.5, 0, 0), bev=0.42, sub=1)
        k.box((0, wr + 0.62, fz - 0.3), (0.2, 0.012, 0.2), "6A7F8C", rot=(0.9, 0, 0), bev=0.4)

        for s2 in (-1, 1):
            k.box((s2 * 0.13, wr + 0.2, zc + 0.18), (0.03, 0.24, 0.5), fair if style == "sport" else second, rot=(-0.1, 0, s2 * 0.06), bev=0.45, sub=1)

        k.box((0, wr + 0.04, zc + 0.1), (0.24, 0.06, 0.4), second if style == "sport" else slate, bev=0.4, sub=1)
        k.egg((0, wr + 0.56, zc + 0.12), (0.13, 0.08, 0.22), fair, seg=20)
        k.box((0, wr + 0.56, zc - 0.25), (0.2, 0.05, 0.38), seat, rot=(-0.08, 0, 0), bev=0.4)
        k.box((0, wr + 0.56, rz + 0.36), (0.17, 0.1, 0.36), fair, rot=(-0.22, 0, 0), bev=0.42, sub=1)
        k.line((0, wr + 0.5, zc - 0.1), (0, wr + 0.2, rz + 0.3), 0.03, second, seg=12)
        k.cyl((0, wr + 0.44, fz - 0.06), (0, 0.25, 1), 0.05, 0.03, lamp, seg=18)

        if style == "police":
            k.box((0, wr + 0.64, rz + 0.3), (0.3, 0.04, 0.05), slate, bev=0.3)
            k.box((-0.1, wr + 0.68, rz + 0.3), (0.08, 0.04, 0.045), "3F6FA8", bev=0.3)
            k.box((0.1, wr + 0.68, rz + 0.3), (0.08, 0.04, 0.045), "A8432F", bev=0.3)

        k.tube([(0.1, wr - 0.02, zc + 0.1), (0.14, wr + 0.02, zc - 0.25), (0.15, wr + 0.3, rz + 0.25)], 0.024, steel)
        k.cyl((0.15, wr + 0.32, rz + 0.18), (0, 0.4, -1), 0.045, 0.26, chrome, seg=20, bevel=0.008)
    else:
        tank = {"chopper": (0.11, 0.1, 0.22), "cruiser": (0.17, 0.12, 0.3), "street": (0.15, 0.11, 0.25), "scrambler": (0.14, 0.1, 0.24), "enduro": (0.15, 0.11, 0.24), "moped": (0.1, 0.07, 0.16)}[style]
        k.egg((0, wr + 0.53, zc + 0.27), tank, main, rot=(0.08, 0, 0), seg=22)
        k.box((0, wr + 0.6, zc + 0.22), (0.04, 0.012, 0.3), second, rot=(0.08, 0, 0), bev=0.4)
        seat_len = 0.32 if style == "chopper" else 0.6
        seat_y = wr + 0.42 if style in ("chopper", "cruiser") else wr + 0.55
        k.box((0, seat_y, zc - 0.22), (0.24 if style == "cruiser" else 0.21, 0.07, seat_len), seat if style != "scrambler" else "8C6A44", rot=(0.04, 0, 0), bev=0.4)
        k.cyl((0, head_top[1] - 0.02, head_top[2] + 0.13), (0, 0, 1), 0.075 if style != "moped" else 0.055, 0.07, chrome, seg=22, bevel=0.01)
        k.cyl((0, head_top[1] - 0.02, head_top[2] + 0.165), (0, 0, 1), 0.06 if style != "moped" else 0.045, 0.01, lamp, seg=22)

        fender_r = wr + 0.05
        cover = (0.35, 0.85) if style in ("cruiser", "chopper") else (0.45, 0.8)

        for zcen, a0, a1, w in ((fz, 0.18, 0.62, 0.075), (rz, cover[0], cover[1], 0.09)):
            pts = []

            for i in range(9):
                a = math.pi * (a0 + (a1 - a0) * i / 8)
                pts.append((0, wr + math.sin(a) * fender_r, zcen + math.cos(a) * fender_r))

            k.tube(pts, w if style == "cruiser" else w * 0.8, main if style in ("cruiser", "street", "moped") else slate, res=1)

        hi = style == "scrambler"
        k.tube([(0.08, wr + 0.1, zc + 0.25), (0.15, wr + (0.4 if hi else 0.0), zc + 0.05), (0.16, wr + (0.46 if hi else 0.06), zc - 0.35)], 0.025, chrome)
        k.cyl((0.16, wr + (0.5 if hi else 0.1), rz + 0.12), (0, 0.15 if hi else 0.05, -1), 0.055, 0.42, chrome, seg=20, bevel=0.01)

        if style == "cruiser":
            k.box((0, head_top[1] + 0.16, head_top[2] + 0.1), (0.4, 0.26, 0.012), "6A7F8C", rot=(-0.3, 0, 0), bev=0.4)

            for s in (-1, 1):
                k.box((s * 0.23, wr + 0.3, rz + 0.22), (0.14, 0.26, 0.42), second, bev=0.3)

        if style == "moped":
            k.cyl((0.07, wr - 0.02, zc), (1, 0, 0), 0.07, 0.01, steel, seg=20)

            for s in (-1, 1):
                k.line((s * 0.08, wr - 0.02, zc), (s * 0.1, wr - 0.1, zc + s * 0.1), 0.01, steel, seg=6)
                k.box((s * 0.14, wr - 0.1, zc + s * 0.1), (0.08, 0.02, 0.05), seat, bev=0.3)

            k.box((0, wr + 0.5, rz + 0.18), (0.18, 0.015, 0.3), steel, bev=0.3)

    k.finish(f"{OUT}/{name}/body.glb", 0.0, wr + 0.8)

    for part in ("wheelF", "wheelR"):
        k = Kit()
        fat = 1.4 if style in ("chopper", "cruiser") and part == "wheelR" else 1.0

        if style in ("sport", "police"):
            wheel(k, wr, 0.05, 0.05, rim, tyre, 0, steel, disc=steel if part == "wheelF" else None, cast=5)
        elif style in ("scrambler", "enduro"):
            wheel(k, wr, 0.048, 0.042, rim, tyre, 24, steel, knobs=True, disc=steel if part == "wheelF" else None)
        else:
            wheel(k, wr, 0.05 * fat, 0.042 * fat, chrome if style in ("chopper", "cruiser") else rim, tyre, 28, steel, disc=steel if part == "wheelF" else None)

        k.finish(f"{OUT}/{name}/{part}.glb", -wr, 2 * wr)


def scooter(name, main, wr, fz, rz):
    k = Kit()
    zc = (fz + rz) / 2
    head = (0, wr + 0.62, fz - 0.14)

    for s in (-1, 1):
        k.line((s * 0.05, head[1] - 0.2, head[2] + 0.02), (s * 0.04, wr, fz), 0.02, steel, seg=12)

    k.box((0, wr + 0.4, fz - 0.14), (0.36, 0.52, 0.08), main, rot=(0.22, 0, 0), bev=0.45, sub=2)
    k.box((0, wr + 0.08, fz + 0.04), (0.12, 0.05, 0.3), main, rot=(-0.2, 0, 0), bev=0.45, sub=1)
    k.box((0, wr + 0.1, zc + 0.05), (0.3, 0.05, 0.6), main, bev=0.3)
    k.egg((0, wr + 0.32, rz + 0.18), (0.21, 0.2, 0.36), main, seg=24)
    k.box((0, wr + 0.53, rz + 0.22), (0.22, 0.07, 0.44), seat, bev=0.4)
    k.egg((0, head[1] + 0.04, head[2]), (0.16, 0.06, 0.09), main, seg=20)
    k.cyl((0, head[1] + 0.05, head[2] + 0.08), (0, 0, 1), 0.05, 0.02, lamp, seg=18)
    k.tube([(-0.33, head[1] + 0.05, head[2] - 0.03), (0, head[1] + 0.06, head[2]), (0.33, head[1] + 0.05, head[2] - 0.03)], 0.012, chrome)

    for s in (-1, 1):
        k.line((s * 0.26, head[1] + 0.05, head[2] - 0.02), (s * 0.35, head[1] + 0.05, head[2] - 0.04), 0.018, seat, seg=12)

    k.box((0, wr + 0.42, rz - 0.06), (0.16, 0.08, 0.16), steel, bev=0.3)
    k.cyl((0.14, wr - 0.02, rz + 0.2), (0, 0, 1), 0.04, 0.3, chrome, seg=16, bevel=0.008)
    k.cyl((0, wr + 0.55, rz - 0.1), (0, 0.2, -1), 0.03, 0.02, "A8432F", seg=14)
    k.finish(f"{OUT}/{name}/body.glb", 0.0, wr + 0.8)

    for part in ("wheelF", "wheelR"):
        k = Kit()
        wheel(k, wr, 0.055, 0.05, rim, tyre, 0, steel, cast=5)
        k.finish(f"{OUT}/{name}/{part}.glb", -wr, 2 * wr)


specs = {
    "moto2": lambda: moto("moto2", "street", "4F6B8A", "C49A3A", 0.29, 0.7, -0.66),
    "scrambler": lambda: moto("scrambler", "scrambler", "6F7350", "C49A3A", 0.291, 0.69, -0.69),
    "sport97a": lambda: moto("sport97a", "sport", "A8432F", "3E4349", 0.284, 0.74, -0.731),
    "sport97b": lambda: moto("sport97b", "police", "D9D3C6", "3B4A63", 0.284, 0.74, -0.731),
    "chopper": lambda: moto("chopper", "chopper", "7A3B3B", "B9BCBD", 0.306, 0.791, -0.755),
    "enduro95": lambda: moto("enduro95", "enduro", "B8A06A", "3E4349", 0.309, 0.702, -0.598),
    "moped102": lambda: moto("moped102", "moped", "C49A3A", "8C6A44", 0.309, 0.63, -0.641),
    "cruiser90": lambda: moto("cruiser90", "cruiser", "3F5A3A", "8C6A44", 0.346, 0.86, -0.771),
    "scooter30": lambda: scooter("scooter30", "8FB5A3", 0.209, 0.735, -0.551),
    "dirt97": lambda: dirt("dirt97", "C0652F", 0.285, 0.703, -0.703),
    "cyc97a": lambda: bicycle("cyc97a", "city", "4F7F82", 0.294, 0.589, -0.589),
    "cyc97b": lambda: bicycle("cyc97b", "road", "A8432F", 0.294, 0.589, -0.589),
    "bike5": lambda: bicycle("bike5", "mtb", "8C7A3A", 0.213, 0.433, -0.433),
}
placement = {
    "moto2": (0.29, 0.7, -0.66),
    "scrambler": (0.291, 0.69, -0.69),
    "sport97a": (0.284, 0.74, -0.731),
    "sport97b": (0.284, 0.74, -0.731),
    "chopper": (0.306, 0.791, -0.755),
    "enduro95": (0.309, 0.702, -0.598),
    "moped102": (0.309, 0.63, -0.641),
    "cruiser90": (0.346, 0.86, -0.771),
    "scooter30": (0.209, 0.735, -0.551),
    "dirt97": (0.285, 0.703, -0.703),
    "cyc97a": (0.294, 0.589, -0.589),
    "cyc97b": (0.294, 0.589, -0.589),
    "bike5": (0.213, 0.433, -0.433),
}

for name in sys.argv[sys.argv.index("--") + 3:]:
    os.makedirs(f"{OUT}/{name}", exist_ok=True)
    specs[name]()
    wr, fz, rz = placement[name]
    Kit()
    render([(f"{OUT}/{name}/body.glb", (0, 0, 0)), (f"{OUT}/{name}/wheelF.glb", (0, wr, fz)), (f"{OUT}/{name}/wheelR.glb", (0, wr, rz))], f"{PREV}/{name}.png")
