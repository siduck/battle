import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k
from mathutils import Vector

OUT = os.environ.get("OUT", "/tmp/dfkit")

W, D = 9.0, 7.0
H1, H2 = 3.2, 3.0
T = 0.3
Z0 = 0.4
ZT = Z0 + H1 + 0.25 + H2
FRONT = -D / 2

k.reset()
parts = []
P = []


def add(items):
    parts.extend(items if isinstance(items, list) else [items])


add(k.beveled_box("plinth", (W + 0.4, D + 0.4, Z0), (0, 0, 0), k.c("stone"), 0.03))

ground_front = [(-2.0, 0, 1.9, 2.5), (2.3, 0.95, 1.3, 1.4)]
upper_front = [(-2.6, 0.8, 1.2, 1.4), (0.2, 0, 1.0, 2.2), (2.8, 0.8, 1.2, 1.4)]
side_low = [(-1.2, 0.95, 1.1, 1.3)]
side_up = [(1.2, 0.8, 1.1, 1.4), (-1.6, 0, 0.95, 2.2)]
back = [(-2.0, 0.95, 1.1, 1.3), (2.0, 0.95, 1.1, 1.3)]

walls = (
    ("front", W, (0, FRONT + T / 2), 0, ground_front, upper_front),
    ("back", W, (0, D / 2 - T / 2), 180, back, back),
    ("left", D - 2 * T, (-W / 2 + T / 2, 0), 90, side_low, side_low),
    ("right", D - 2 * T, (W / 2 - T / 2, 0), -90, side_low, side_up),
)

for name, width, (x, y), facing, low, high in walls:
    add(k.wall(name + "_g", width, H1, T, (x, y, Z0), low, "sandstone", math.radians(facing), bevel=0))
    add(k.wall(name + "_u", width, H2, T, (x, y, Z0 + H1 + 0.25), high, "sandstone", math.radians(facing), bevel=0))

add(k.beveled_box("band", (W + 0.14, D + 0.14, 0.25), (0, 0, Z0 + H1), k.c("cream"), 0.02))
add(k.beveled_box("roofslab", (W, D, 0.2), (0, 0, ZT - 0.05), k.c("concrete"), 0.02))

for side, (sx, sy, lx, ly) in enumerate(((0, FRONT + 0.125, W, 0.25), (0, D / 2 - 0.125, W, 0.25), (-W / 2 + 0.125, 0, 0.25, D), (W / 2 - 0.125, 0, 0.25, D))):
    add(k.beveled_box(f"parapet{side}", (lx, ly, 0.85), (sx, sy, ZT), k.c("sandstone"), 0.02))
    add(k.beveled_box(f"coping{side}", (lx + 0.14, ly + 0.14, 0.1), (sx, sy, ZT + 0.85), k.c("cream"), 0.02))


def deep_window(tag, x, z, w, h, wall_y, facing, bars=False):
    items = k.window(tag, w, h, (x, wall_y, z), facing, depth=0.1, frame=0.06, mullions=(2, 1), sill=False, colors={"frame": "cream", "glass": "glass"})
    out = Vector((0, -1, 0))
    out.rotate(k.Matrix.Rotation(facing, 3, "Z"))
    inset = out * -0.12

    for it in items:
        k.move(it, inset.x, inset.y, 0)

    sill = k.beveled_box(tag + "_sill", (w + 0.3, 0.32, 0.1), (0, -0.1, -0.12), k.c("cream"), 0.02)
    lintel = k.beveled_box(tag + "_lintel", (w + 0.36, 0.24, 0.22), (0, -0.06, h), k.c("cream"), 0.02)

    for it in (sill, lintel):
        k.rotate(it, math.degrees(facing))
        k.move(it, x, wall_y, z)
        items.append(it)

    if bars:
        for i in range(5):
            bx = -w / 2 + w * (i + 0.5) / 5
            b = k.box(tag + f"_bar{i}", (0.03, 0.03, h), (bx, -0.05, 0), k.c("steel_dark"))
            k.rotate(b, math.degrees(facing))
            k.move(b, x, wall_y, z)
            items.append(b)

    return items


add(deep_window("gw", 2.3, Z0 + 0.95, 1.3, 1.4, FRONT, 0, bars=True))
add(deep_window("u1", -2.6, Z0 + H1 + 0.25 + 0.8, 1.2, 1.4, FRONT, 0))
add(deep_window("u3", 2.8, Z0 + H1 + 0.25 + 0.8, 1.2, 1.4, FRONT, 0))

for gx in (-2.0, 2.0):
    add(deep_window(f"bk{gx}", -gx, Z0 + 0.95, 1.1, 1.3, D / 2, math.pi, bars=True))
    add(deep_window(f"bku{gx}", -gx, Z0 + H1 + 0.25 + 0.95, 1.1, 1.3, D / 2, math.pi))

for side, xw, f in ((-1, -W / 2, -math.pi / 2), (1, W / 2, math.pi / 2)):
    for it in deep_window(f"s{side}", xw, Z0 + 0.95, 1.1, 1.3, 0, f, bars=True):
        k.move(it, 0, 1.2 * side, 0)
        parts.append(it)

for it in deep_window("sl_l", -W / 2, Z0 + H1 + 0.25 + 0.8, 1.1, 1.4, 0, -math.pi / 2):
    k.move(it, 0, -1.2, 0)
    parts.append(it)

for it in deep_window("sl_r", W / 2, Z0 + H1 + 0.25 + 0.8, 1.1, 1.4, 0, math.pi / 2):
    k.move(it, 0, -1.2, 0)
    parts.append(it)

add(k.beveled_box("shutterbox", (2.1, 0.3, 0.35), (-2.0, FRONT - 0.1, Z0 + 2.15), k.c("steel_dark"), 0.02))

for i in range(12):
    add(k.box(f"shutter{i}", (1.85, 0.04 + 0.02 * (i % 2), 0.1), (-2.0, FRONT + 0.02, Z0 + 1.0 + i * 0.096), k.c("steel" if i % 2 else "concrete")))

add(k.box("shopdark", (1.85, 0.05, 1.0), (-2.0, FRONT + 0.1, Z0), k.c("black")))

for sx in (-3.0, -1.0):
    add(k.beveled_box(f"shopjamb{sx}", (0.16, 0.24, 2.5), (sx, FRONT - 0.04, Z0), k.c("cream"), 0.02))

add(k.door("balc", 0.95, 2.15, (0.2, FRONT + 0.05, Z0 + H1 + 0.25), 0, colors={"leaf": "teal", "panel": "teal", "frame": "cream"}, step=False))
add(k.door("side", 0.9, 2.15, (W / 2 - 0.05, 1.6, Z0 + H1 + 0.25), math.pi / 2, colors={"leaf": "wood", "panel": "wood_dark", "frame": "cream"}, step=False))

for i in range(9):
    sx = -2.95 + i * 0.24
    slat = k.box(f"awn{i}", (0.24, 1.25, 0.05), (sx, 0, 0), k.c("awning_red" if i % 2 == 0 else "cream"))
    k.move(slat, 0, -0.62, 0)
    k.rotate(slat, 22, "X")
    k.move(slat, 0, FRONT, Z0 + 2.85)
    parts.append(slat)

add(k.beveled_box("valance", (2.2, 0.04, 0.2), (-2.0, FRONT - 1.16, Z0 + 2.2), k.c("awning_red"), 0.01))

for sx in (-3.05, -0.95):
    parts.append(k._bar(f"awnarm{sx}", Vector((sx, FRONT, Z0 + 2.85)), Vector((sx, FRONT - 1.15, Z0 + 2.38)), 0.02, k.c("steel_dark")))

add(k.beveled_box("sign", (2.6, 0.1, 0.55), (-2.0, FRONT - 0.07, Z0 + 3.05), k.c("teal"), 0.02))
lx = -2.95

for i, lw in enumerate((0.16, 0.12, 0.16, 0.14, 0.05, 0.16, 0.13, 0.16, 0.12, 0.15)):
    if i == 4:
        lx += lw + 0.1
        continue

    add(k.box(f"letter{i}", (lw, 0.03, 0.26), (lx + lw / 2, FRONT - 0.13, Z0 + 3.17), k.c("cream")))
    lx += lw + 0.07

balc_z = Z0 + H1 + 0.25
add(k.beveled_box("balcony", (2.6, 1.2, 0.16), (0.2, FRONT - 0.6, balc_z - 0.16), k.c("concrete"), 0.02))

for bx in (-0.95, 1.35):
    parts.append(k._bar(f"strut{bx}", Vector((bx, FRONT - 0.02, balc_z - 0.9)), Vector((bx, FRONT - 1.0, balc_z - 0.17)), 0.035, k.c("steel_dark"), sides=4))

add(k.railing("brail", 2.5, 0.95, (0.2, FRONT - 1.15, balc_z), posts=6))
add(k.railing("brailL", 1.1, 0.95, (-1.05, FRONT - 0.6, balc_z), posts=3, facing=math.pi / 2))
add(k.railing("brailR", 1.1, 0.95, (1.45, FRONT - 0.6, balc_z), posts=3, facing=math.pi / 2))

steps = 12
rise = (H1 + 0.25) / steps

for i in range(steps):
    add(k.beveled_box(f"st{i}", (1.0, 0.32, rise), (W / 2 + 0.6, -2.6 + i * 0.32, Z0 + i * rise), k.c("concrete"), 0.015))

add(k.beveled_box("landing", (1.1, 1.3, 0.16), (W / 2 + 0.6, 1.6, balc_z - 0.16), k.c("concrete"), 0.02))
parts.append(k._bar("stairrail", Vector((W / 2 + 1.08, -2.6, Z0 + 1.0)), Vector((W / 2 + 1.08, 1.0, balc_z + 0.95)), 0.025, k.c("steel_dark")))

for i in range(0, steps, 3):
    parts.append(k._bar(f"stpost{i}", Vector((W / 2 + 1.08, -2.6 + i * 0.32, Z0 + i * rise)), Vector((W / 2 + 1.08, -2.6 + i * 0.32, Z0 + i * rise + 1.0)), 0.022, k.c("steel_dark")))

hut = (-2.2, 1.6)
add(k.beveled_box("hut", (2.4, 2.2, 2.4), (hut[0], hut[1], ZT + 0.15), k.c("pink_plaster"), 0.03))
add(k.beveled_box("hutroof", (2.7, 2.5, 0.14), (hut[0], hut[1], ZT + 2.55), k.c("cream"), 0.02))
add(k.door("hutdoor", 0.9, 2.0, (hut[0] + 0.5, hut[1] - 1.12, ZT + 0.15), 0, colors={"leaf": "steel", "panel": "steel_dark", "frame": "cream"}, step=False))

tank = (2.5, 1.8)
tz = ZT + 0.15

for lx in (-0.45, 0.45):
    for ly in (-0.45, 0.45):
        parts.append(k._bar(f"leg{lx}{ly}", Vector((tank[0] + lx, tank[1] + ly, tz)), Vector((tank[0] + lx, tank[1] + ly, tz + 1.2)), 0.04, k.c("steel_dark")))

add(k.beveled_box("tankdeck", (1.2, 1.2, 0.08), (tank[0], tank[1], tz + 1.2), k.c("steel_dark"), 0.01))
add(k.lathe("tank", [(0, 0), (0.62, 0), (0.62, 1.35), (0.5, 1.5), (0.1, 1.55), (0, 1.55)], 12, (tank[0], tank[1], tz + 1.28), k.c("tank_green")))

for hz in (0.35, 0.95):
    add(k.prism(f"tankband{hz}", 12, 0.635, 0.05, (tank[0], tank[1], tz + 1.28 + hz), k.c("olive_dark")))

for i, (ax, ay) in enumerate(((0.2, -1.6), (1.4, -1.6), (-3.6, -1.9))):
    add(k.beveled_box(f"ac{i}", (0.85, 0.6, 0.62), (ax, ay, tz), k.c("steel"), 0.02))
    add(k.prism(f"fan{i}", 10, 0.2, 0.02, (ax, ay - 0.31, tz + 0.31), k.c("steel_dark")))
    k.rotate(parts[-1], 90, "X", (ax, ay - 0.31, tz + 0.31))

dish_at = Vector((-0.8, 2.2, tz))
parts.append(k._bar("dishpole", dish_at, dish_at + Vector((0, 0, 0.9)), 0.03, k.c("steel_dark")))
dish = k.lathe("dish", [(0, 0), (0.25, 0.04), (0.5, 0.16), (0.52, 0.18), (0, 0.06)], 12, (0, 0, 0), k.c("white"))
k.rotate(dish, 60, "X")
k.rotate(dish, 200, "Z")
k.move(dish, dish_at.x, dish_at.y, dish_at.z + 0.9)
parts.append(dish)

mast = Vector((3.9, -2.9, tz))
parts.append(k._bar("mast", mast, mast + Vector((0, 0, 2.6)), 0.03, k.c("steel_dark")))

for i, hz in enumerate((1.6, 2.1, 2.5)):
    parts.append(k._bar(f"yagi{i}", mast + Vector((-0.4 + i * 0.1, 0, hz)), mast + Vector((0.4 - i * 0.1, 0, hz)), 0.015, k.c("steel_dark")))

add(k.beveled_box("rc1", (0.9, 0.7, 0.6), (-0.4, -0.4, tz), k.c("wood"), 0.03))
add(k.beveled_box("rc2", (0.7, 0.6, 0.5), (-0.35, -0.4, tz + 0.6), k.c("olive"), 0.03))
add(k.prism("rb", 10, 0.28, 0.85, (0.6, -0.2, tz), k.c("awning_red")))
add(k.prism("rbband", 10, 0.29, 0.05, (0.6, -0.2, tz + 0.55), k.c("rust")))

prev = Vector((hut[0] + 1.2, hut[1] - 1.0, ZT + 2.2))

for i in range(1, 7):
    t = i / 6
    a = Vector((hut[0] + 1.2, hut[1] - 1.0, ZT + 2.2))
    b = Vector((W / 2 + 0.5, FRONT - 0.2, ZT + 0.7))
    p = a.lerp(b, t) - Vector((0, 0, 0.5 * math.sin(math.pi * t)))
    parts.append(k._bar(f"cable{i}", prev, p, 0.012, k.c("black"), sides=4))
    prev = p

for qx, qy, face in ((-W / 2, FRONT, "x"), (W / 2, FRONT, "x"), (-W / 2, D / 2, "x"), (W / 2, D / 2, "x")):
    sx = 1 if qx > 0 else -1
    sy = 1 if qy > 0 else -1

    for j in range(int((ZT - Z0) / 0.5)):
        long = j % 2 == 0
        qz = Z0 + 0.95 + j * 0.5

        if qz + 0.42 > ZT:
            break

        add(k.beveled_box(f"q{qx}{qy}{j}", (0.62 if long else 0.4, 0.62 if not long else 0.4, 0.42), (qx - sx * (0.26 if long else 0.15), qy - sy * (0.15 if long else 0.26), qz), k.c("cream"), 0.03))

for i, (bx, by, bw, bd) in enumerate((((-W / 2 - 3.0) / 2 - 0.025, FRONT + 0.15, -3.0 + W / 2 + 0.05, 0.4), ((W / 2 - 1.0) / 2 + 0.025, FRONT + 0.15, W / 2 + 1.0 + 0.05, 0.4), (0, D / 2 - 0.15, W + 0.1, 0.4), (-W / 2 + 0.15, 0, 0.4, D), (W / 2 - 0.15, 0, 0.4, D))):
    add(k.beveled_box(f"base{i}", (bw, bd, 0.95), (bx, by, Z0), k.c("sandstone_dark"), 0.02))

for lvl, (gw, gh) in enumerate(((0.12, 0.14), (0.24, 0.12))):
    add(k.beveled_box(f"cornice{lvl}", (W + gw * 2, D + gw * 2, gh), (0, 0, ZT - 0.2 + lvl * 0.14), k.c("cream"), 0.02))

for bx, bz in ((-4.05, 1.45), (-3.85, 1.6), (-3.65, 1.45), (3.95, 4.8), (3.75, 4.95), (-0.95, 5.85), (-0.75, 5.7)):
    add(k.beveled_box(f"brick{bx}{bz}", (0.24, 0.08, 0.11), (bx, FRONT - 0.03, bz), k.c("brick"), 0.015))

ac = k.beveled_box("wallac", (0.9, 0.6, 0.55), (2.3, FRONT - 0.3, Z0 + 2.45), k.c("white"), 0.03)
parts.append(ac)
add(k.prism("wallacfan", 12, 0.2, 0.03, (2.55, FRONT - 0.6, Z0 + 2.72), k.c("steel_dark")))
k.rotate(parts[-1], 90, "X", (2.55, FRONT - 0.6, Z0 + 2.72))

for sx in (1.95, 2.65):
    parts.append(k._bar(f"acbr{sx}", Vector((sx, FRONT, Z0 + 2.1)), Vector((sx, FRONT - 0.55, Z0 + 2.45)), 0.025, k.c("steel_dark"), sides=4))

parts.append(k._bar("drain", Vector((2.9, FRONT - 0.5, Z0 + 2.45)), Vector((2.9, FRONT - 0.5, 0.1)), 0.02, k.c("black"), sides=4))
add(k.beveled_box("meter", (0.45, 0.18, 0.6), (0.4, FRONT - 0.09, Z0 + 1.3), k.c("steel"), 0.02))
parts.append(k._bar("conduit", Vector((0.4, FRONT - 0.06, Z0 + 1.9)), Vector((0.4, FRONT - 0.06, Z0 + H1 + 0.1)), 0.025, k.c("steel_dark"), sides=4))
lamp = Vector((-2.0, FRONT - 0.3, Z0 + 2.75))
add(k.lathe("lamp", [(0, 0), (0.18, 0), (0.12, 0.12), (0.03, 0.16), (0, 0.16)], 8, (lamp.x, lamp.y, lamp.z - 0.4), k.c("steel_dark")))
parts.append(k._bar("lampcord", lamp, lamp - Vector((0, 0, 0.24)), 0.01, k.c("black"), sides=4))

for i, (cx, cy) in enumerate(((-3.3, FRONT - 0.5), (-3.25, FRONT - 1.15))):
    add(k.prism(f"gas{i}", 10, 0.16, 0.85, (cx, cy, Z0), k.c("teal" if i else "awning_red")))
    add(k.prism(f"gastop{i}", 8, 0.06, 0.12, (cx, cy, Z0 + 0.85), k.c("steel")))

for i, (cx, cy, cz, cw) in enumerate(((-0.7, FRONT - 0.5, Z0, 0.7), (-0.6, FRONT - 0.5, Z0 + 0.5, 0.55), (-0.15, FRONT - 0.95, Z0, 0.5))):
    add(k.beveled_box(f"fcrate{i}", (cw, 0.5, 0.5 if i < 2 else 0.4), (cx, cy, cz), k.c("wood" if i != 1 else "wood_light"), 0.03))

for i, (px, py) in enumerate(((-1.3, FRONT - 1.6), (-0.95, FRONT - 1.55))):
    add(k.prism(f"produce{i}", 8, 0.22, 0.12, (px, py, Z0 + 0.38), k.c("yellow" if i else "awning_red")))
    add(k.beveled_box(f"produceb{i}", (0.45, 0.45, 0.38), (px, py, Z0), k.c("wood_light"), 0.02))

add(k.prism("streetbarrel", 10, 0.3, 0.9, (W / 2 - 0.5, FRONT - 0.6, Z0), k.c("olive")))
add(k.prism("streetbarrelband", 10, 0.31, 0.05, (W / 2 - 0.5, FRONT - 0.6, Z0 + 0.6), k.c("olive_dark")))

parts.append(k.prism("pipe", 8, 0.06, ZT + 0.6, (W / 2 - 0.4, D / 2 + 0.08, 0), k.c("steel_dark")))

ob = k.finish("df_outpost_v2", parts, budget=8000)
k.grime(ob, 1.0, 0.7)
k.bake_ao(ob, strength=0.85, distance=1.2)
print("STATS", k.stats(ob))
k.export(ob, os.path.join(OUT, "df_outpost_v2.glb"))
k.VIEWS["hero"] = (1.0, -1.35, 0.55)
print("SHEET", k.preview([ob], os.path.join(OUT, "df_outpost_v2_sheet.png"), views=("hero", "front", "right", "back")))
