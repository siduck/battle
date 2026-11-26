import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k
import bpy
from mathutils import Vector

OUT = os.environ.get("OUT", "/tmp/dfkit")

W, D = 8.0, 7.0
T = 0.4
Z0 = 0.25
H1, SLAB, H2 = 3.3, 0.3, 2.9
ZU = Z0 + H1 + SLAB
ZT = ZU + H2
PORCH = 1.9
FRONT = -D / 2
rng = random.Random(11)

k.reset()
MID = os.environ.get("MID") == "1"
k.set_mid(MID)
N = 2 if MID else 1

if os.environ.get("SHUTTER"):
    main, dark = os.environ["SHUTTER"].split(",")
    k.PALETTE[k.c("shutter")] = ("shutter", main)
    k.PALETTE[k.c("shutter_dark")] = ("shutter_dark", dark)

k.harmonize(os.environ.get("KEY", "#cdb48a"), 0.2, accents=("shutter", "shutter_dark", "clay"), accent_amount=0.15)
parts = []
soft = []


def place(items, x, y, z, facing):
    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)
        parts.append(it)


def window(w, h, sill_z, shutters=True, bars=False):
    items = [
        k.box("void", (w, 0.05, h), (0, T - 0.06, sill_z), k.c("void")),
        k.box("sideL", (0.04, T - 0.1, h), (-w / 2 + 0.02, (T - 0.1) / 2, sill_z), k.c("adobe_dark")),
        k.box("sideR", (0.04, T - 0.1, h), (w / 2 - 0.02, (T - 0.1) / 2, sill_z), k.c("adobe_dark")),
        k.beveled_box("lintel", (w + 0.5, 0.2, 0.16), (0, -0.04, sill_z + h), k.c("beam"), 0.02),
        k.beveled_box("sill", (w + 0.16, 0.22, 0.08), (0, -0.06, sill_z - 0.08), k.c("adobe_dark"), 0.02),
    ]

    for fx in (-w / 2 + 0.04, w / 2 - 0.04):
        items.append(k.box("frame", (0.07, 0.07, h), (fx, 0.16, sill_z), k.c("shutter")))

    items.append(k.box("frameT", (w, 0.07, 0.07), (0, 0.16, sill_z + h - 0.07), k.c("shutter")))
    items.append(k.box("mull", (0.05, 0.05, h), (0, 0.17, sill_z), k.c("shutter")))

    if bars:
        for i in range(4):
            items.append(k.box("bar", (0.03, 0.03, h), (-w / 2 + w * (i + 0.5) / 4, 0.06, sill_z), k.c("tank_black")))

    if shutters:
        for side in (-1, 1):
            sh = k.beveled_box("shutter", (w / 2, 0.05, h), (side * w * 0.75, -0.04, sill_z), k.c("shutter"), 0.012)
            k.rotate(sh, side * -18, "Z", (side * w / 2, -0.02, 0))
            items.append(sh)

            slats = 9 if MID else 3

            for j in range(slats):
                sl = k.box("slat", (w / 2 - 0.08, 0.02, 0.05 if not MID else 0.035), (side * w * 0.75, -0.075, sill_z + 0.15 + j * (h - 0.3) / (slats - 1)), k.c("shutter_dark"))
                k.rotate(sl, side * -18, "Z", (side * w / 2, -0.02, 0))
                items.append(sl)

    return items


def door(w, h, double=False):
    items = [
        k.box("dvoid", (w, 0.05, h), (0, T - 0.04, 0), k.c("void")),
        k.beveled_box("dlintel", (w + 0.6, 0.22, 0.18), (0, -0.05, h), k.c("beam"), 0.02),
        k.box("dsideL", (0.04, T, h), (-w / 2 + 0.02, T / 2, 0), k.c("adobe_dark")),
        k.box("dsideR", (0.04, T, h), (w / 2 - 0.02, T / 2, 0), k.c("adobe_dark")),
    ]
    planks = 6 if double else 4
    pw = (w - 0.06) / planks

    for i in range(planks):
        px = -w / 2 + 0.03 + pw * (i + 0.5)
        items.append(k.beveled_box("plank", (pw - 0.015, 0.06, h - 0.04), (px, 0.2, 0), k.c("beam_light" if i % 3 == 1 else "beam"), 0.008))

    for bz in (0.35, h - 0.45):
        items.append(k.box("brace", (w - 0.1, 0.03, 0.12), (0, 0.155, bz), k.c("beam")))

    items.append(k.beveled_box("step", (w + 0.3, 0.4, 0.14), (0, -0.2, -0.14), k.c("adobe_dark"), 0.02))

    return items


def brick_patch(cx, cz, w, h):
    n = 9
    pts = []

    for i in range(n):
        a = 2 * math.pi * i / n
        r = 0.75 + 0.35 * rng.random()
        pts.append((w / 2 * r * math.cos(a), h / 2 * r * math.sin(a)))

    items = [k.sweep("patch", pts, 0.03, (cx, -0.015, cz), k.c("adobe_dark"), axis="y")]
    rows = max(2, int(h / 0.13))

    for row in range(rows):
        z = cz - h / 2 * 0.7 + row * 0.13
        span = w * 0.6 * (1 - abs(row - rows / 2) / rows)
        x = cx - span / 2 + (0.12 if row % 2 else 0)

        while x < cx + span / 2:
            items.append(k.beveled_box("brick", (0.22, 0.05, 0.085), (x, -0.035, z), k.c("adobe_brick" if rng.random() > 0.3 else "adobe_brick_dark"), 0.012))
            x += 0.25

    return items


def wall(width, height, openings, wear=()):
    pieces = k.wall("w", width, height, T, (0, T / 2, 0), openings, "adobe", 0.0, bevel=0)
    soft.extend(pieces)
    items = list(pieces)

    for cx, cz, pw, ph in wear:
        items += brick_patch(cx, cz, pw, ph)

    return items


def vigas(length, z, every=0.9):
    items = []
    n = int(length / every)

    for i in range(n):
        x = -length / 2 + every * (i + 0.5)
        if MID:
            v = k.prism("viga", 8, 0.085, 0.42, (0, 0, 0), k.c("beam"), rotate=22.5)
            k.chamfer(v, 0.015, 30, 2)
            k.rotate(v, 90, "X")
            k.move(v, x, -0.42 + 0.22, z + 0.08)
            items.append(v)
        else:
            items.append(k.beveled_box("viga", (0.16, 0.42, 0.16), (x, -0.2, z), k.c("beam"), 0.02))

    return items


def facade(width, height, spec, wear=()):
    openings = []
    items = []

    for kind, x, z, w, h in spec:
        openings.append((x, z, w, h))
        made = door(w, h, w > 1.1) if kind == "door" else window(w, h, 0, kind != "plain", kind == "bars")

        for it in made:
            k.move(it, x, 0, z)

        items += made

    return wall(width, height, openings, wear) + items


inner = W - 2 * T
place(facade(inner, H1, [("door", 0, 0, 1.3, 2.3), ("win", -2.1, 1.0, 0.9, 1.15), ("bars", 2.1, 1.0, 0.9, 1.15)], [(1.0, 2.6, 0.6, 0.45)]), 0, FRONT + PORCH, Z0, 0)
place(facade(W, H2, [("win", -2.5, 0.9, 1.0, 1.3), ("door", 0, 0, 1.0, 2.2), ("win", 2.5, 0.9, 1.0, 1.3)], [(-1.3, 2.05, 0.9, 0.6), (3.3, 0.55, 0.8, 0.55), (-3.4, 0.45, 0.6, 0.45)]) + vigas(W, H2 - 0.55), 0, FRONT, ZU, 0)
place(facade(W, H1, [("bars", -2.0, 1.3, 0.8, 0.9), ("bars", 2.0, 1.3, 0.8, 0.9)], [(0.2, 0.8, 1.0, 0.6), (-3.2, 2.5, 0.7, 0.5)]), 0, D / 2, Z0, 180)
place(facade(W, H2, [("win", -2.0, 0.9, 0.9, 1.2), ("plain", 2.0, 1.1, 0.6, 0.6)], [(0.4, 1.6, 0.9, 0.6)]) + vigas(W, H2 - 0.55), 0, D / 2, ZU, 180)

ground_side = D - PORCH
place(facade(ground_side, H1, [("win", 0.6, 1.0, 0.9, 1.15)], [(-1.4, 1.2, 0.55, 0.5)]), -W / 2, FRONT + PORCH + ground_side / 2, Z0, -90)
place(facade(D, H2, [("win", -1.5, 0.9, 0.9, 1.2), ("win", 1.6, 0.9, 0.9, 1.2)], [(0.1, 0.6, 0.8, 0.5), (2.9, 2.2, 0.6, 0.45)]) + vigas(D, H2 - 0.55), -W / 2, 0, ZU, -90)
place(facade(ground_side, H1, [], [(0.5, 0.9, 0.7, 0.5)]), W / 2, FRONT + PORCH + ground_side / 2, Z0, 90)
place(facade(D, H2, [("win", -1.6, 0.9, 0.9, 1.2), ("door", 2.55, 0, 0.95, 2.1)]) + vigas(D, H2 - 0.55), W / 2, 0, ZU, 90)

by = FRONT - 0.55

for bx in (-0.9, -0.3, 0.3, 0.9):
    parts.append(k.beveled_box("bjoist", (0.16, 1.3, 0.16), (bx, FRONT - 0.45, ZU - 0.16), k.c("beam"), 0.02))

parts.append(k.beveled_box("bdeck", (2.2, 1.0, 0.08), (0, by, ZU), k.c("beam_light"), 0.015))

for i in range(9):
    px = -1.05 + i * 2.1 / 8
    parts.append(k.box("bspindle", (0.05, 0.05, 0.8), (px, by - 0.45, ZU + 0.08), k.c("beam")))

for side in (-1, 1):
    for j in range(4):
        parts.append(k.box("bspindleS", (0.05, 0.05, 0.8), (side * 1.05, by - 0.45 + j * 0.3, ZU + 0.08), k.c("beam")))

    parts.append(k.beveled_box("brailS", (0.08, 1.0, 0.08), (side * 1.05, by, ZU + 0.88), k.c("beam_light"), 0.01))

parts.append(k.beveled_box("brail", (2.2, 0.08, 0.08), (0, by - 0.47, ZU + 0.88), k.c("beam_light"), 0.01))

front_arc = k.arcade("arcade", W, H1, T, 3, 0.55, 1.75, k.c("adobe"), segs=8 * N, inner=k.c("adobe_dark"))
k.move(front_arc, 0, FRONT + T / 2, Z0)
parts.append(front_arc)

sa = k.arcade("sidearc", PORCH, H1, T, 1, 0.45, 1.6, k.c("adobe"), segs=8 * N, inner=k.c("adobe_dark"))
k.rotate(sa, -90)
k.move(sa, -(W / 2 - T / 2), FRONT + PORCH / 2, Z0)
parts.append(sa)
place(wall(PORCH, H1, []), W / 2, FRONT + PORCH / 2, Z0, 90)

for i, (bx, by, bw, bd) in enumerate(((0, FRONT + PORCH / 2 + 0.1, W - 0.1, PORCH - 0.2),)):
    parts.append(k.beveled_box("porchfloor", (bw, bd, 0.12), (bx, by, Z0 - 0.02), k.c("adobe_dark"), 0.02))

slab = k.beveled_box("slab", (W + 0.16, D + 0.16, SLAB), (0, 0, Z0 + H1), k.c("adobe_dark"), 0.03)
parts.append(slab)
soft.append(slab)
parts.append(k.box("porchceil", (W - 2 * T, PORCH - T, 0.02), (0, FRONT + T + (PORCH - T) / 2, Z0 + H1 - 0.02), k.c("adobe_dark")))
parts.append(k.beveled_box("plinth", (W + 0.2, D + 0.2, Z0), (0, 0, 0), k.c("adobe_dark"), 0.03))
parts.append(k.box("roof", (W - 0.1, D - 0.1, 0.12), (0, 0, ZT - 0.06), k.c("adobe_dark")))

for i, (px, py, lx, ly) in enumerate(((0, FRONT + 0.15, W, 0.3), (0, D / 2 - 0.15, W, 0.3), (-W / 2 + 0.15, 0, 0.3, D - 0.6), (W / 2 - 0.15, 0, 0.3, D - 0.6))):
    p = k.box(f"parapet{i}", (lx, ly, 0.75), (px, py, ZT), k.c("adobe"))
    k.chamfer(p, 0.09, 30, 2)
    parts.append(p)
    soft.append(p)

for i in range(6):
    x = -W / 2 + 0.35 + i * 1.45
    parts.append(k.box(f"scupper{i}", (0.14, 0.5, 0.1), (x, FRONT - 0.15, ZT + 0.05), k.c("beam")))

room = (-1.9, 1.6)
rm = k.box("roomwall", (2.8, 2.6, 2.3), (room[0], room[1], ZT), k.c("adobe"))
k.chamfer(rm, 0.05, 30, 1)
parts.append(rm)
soft.append(rm)
rc = k.box("roomcap", (3.0, 2.8, 0.16), (room[0], room[1], ZT + 2.3), k.c("adobe_light"))
k.chamfer(rc, 0.06, 30, 2)
parts.append(rc)
place(door(0.9, 1.95), room[0] + 0.6, room[1] - 1.3, ZT, 0)
place(vigas(2.8, 1.9, 0.7), room[0], room[1] - 1.3, ZT, 0)

tank = (2.4, 2.2)

for lx in (-0.42, 0.42):
    for ly in (-0.42, 0.42):
        parts.append(k._bar("tleg", Vector((tank[0] + lx, tank[1] + ly, ZT)), Vector((tank[0] + lx, tank[1] + ly, ZT + 1.0)), 0.045, k.c("beam"), sides=4 * N))

parts.append(k.beveled_box("tdeck", (1.1, 1.1, 0.1), (tank[0], tank[1], ZT + 1.0), k.c("beam_light"), 0.015))
parts.append(k.lathe("tank", [(0, 0), (0.5, 0), (0.52, 0.2), (0.5, 0.4), (0.52, 0.6), (0.5, 0.8), (0.52, 1.0), (0.45, 1.2), (0.15, 1.25), (0.15, 1.35), (0, 1.35)], 12 * N, (tank[0], tank[1], ZT + 1.1), k.c("tank_black")))

stair_w = 1.05
rise, run, steps = 0.2, 0.29, int((ZU - 0.02) / 0.2)
run_len = steps * run
profile = [(0, 0), (run_len + 1.2, 0), (run_len + 1.2, ZU)]

for i in range(steps, 0, -1):
    profile.append((i * run, i * rise))
    profile.append(((i - 1) * run, i * rise))

stair = k.sweep("stair", profile, stair_w, (0, 0, 0), k.c("adobe"), axis="y")
rail = k.sweep("stairrail", [(0, 0.2), (run_len, ZU), (run_len + 1.2, ZU), (run_len + 1.2, ZU + 0.75), (run_len, ZU + 0.75), (0, 0.95)], 0.16, (0, -stair_w / 2 + 0.08, 0), k.c("adobe"), axis="y")
cap = k.sweep("stairtop", [(0, 0.95), (run_len, ZU + 0.75), (run_len + 1.2, ZU + 0.75), (run_len + 1.2, ZU + 0.83), (run_len, ZU + 0.83), (0, 1.03)], 0.2, (0, -stair_w / 2 + 0.08, 0), k.c("adobe_light"), axis="y")
start_y = D / 2 - 0.15 - run_len - 1.2

for ob in (stair, rail, cap):
    k.earclip(ob)
    k.rotate(ob, 90)
    k.move(ob, W / 2 + stair_w / 2, start_y, 0)
    parts.append(ob)

canopy_at = (-W / 2 - 1.3, FRONT + 2.0)

for i, (dx, dy) in enumerate(((-0.9, -1.1), (-0.9, 1.1))):
    parts.append(k._bar("pole", Vector((canopy_at[0] + dx, canopy_at[1] + dy, 0)), Vector((canopy_at[0] + dx, canopy_at[1] + dy, 2.3)), 0.05, k.c("beam"), sides=5 * N))

for i in range(8):
    y0 = canopy_at[1] - 1.2 + i * 0.3
    strip = k.box(f"cloth{i}", (2.2, 0.3, 0.03), (canopy_at[0] + 0.15, y0 + 0.15, 0), k.c("shutter" if i % 2 == 0 else "cloth_light"))
    k.rotate(strip, -11, "Y", (canopy_at[0] + 1.25, 0, 0))
    k.move(strip, 0, 0, 2.3 + 0.21 - 0.06 * math.sin(math.pi * (i + 0.5) / 8))
    parts.append(strip)

for i, (px, py, r, h) in enumerate(((-1.0, FRONT + PORCH - 0.4, 0.26, 0.6), (-1.55, FRONT + PORCH - 0.35, 0.2, 0.45), (1.1, FRONT + PORCH - 0.4, 0.24, 0.55), (-W / 2 - 1.6, FRONT + 1.6, 0.3, 0.7))):
    parts.append(k.lathe(f"pot{i}", [(0, 0), (r * 0.6, 0), (r, h * 0.45), (r * 0.8, h * 0.85), (r * 0.55, h * 0.9), (r * 0.62, h), (0, h * 0.95)], 9 * N, (px, py, Z0 if py > FRONT + 0.1 else 0), k.c("clay")))

for i, (cx, cy, cz, sw, sh, col) in enumerate(((-W / 2 - 1.6, FRONT + 2.6, 0, 0.7, 0.5, "beam_light"), (-W / 2 - 1.55, FRONT + 2.55, 0.5, 0.55, 0.4, "beam"), (-W / 2 - 0.9, FRONT + 2.8, 0, 0.5, 0.45, "beam_light"))):
    cr = k.beveled_box(f"crate{i}", (sw, sw * 0.9, sh), (cx, cy, cz), k.c(col), 0.03)
    k.rotate(cr, rng.uniform(-12, 12), "Z", (cx, cy, 0))
    parts.append(cr)

parts.append(k.beveled_box("bench", (1.6, 0.4, 0.08), (2.4, FRONT + PORCH - 0.45, Z0 + 0.42), k.c("beam_light"), 0.015))

for bx in (1.75, 3.05):
    parts.append(k.beveled_box("benchleg", (0.08, 0.36, 0.42), (bx, FRONT + PORCH - 0.45, Z0), k.c("beam"), 0.01))

for ob in soft:
    k.jitter(ob, 0.025)

if MID:
    gone = {id(o) for o in soft[1:]}
    parts = [p for p in parts if id(p) not in gone]
    k.fuse(soft, bevel=0.06, segments=3)

ob = k.finish("df_adobe_house", parts, budget=30000 if MID else 9000)
k.height_gradient(ob)
k.shade_volume(ob, (-W / 2 + T, FRONT + T - 0.01, -0.1), (W / 2 + 0.3, FRONT + PORCH + T + 0.05, Z0 + H1), 0.6)
k.grime(ob, 0.7, 0.75)
k.bake_ao(ob, strength=0.8, distance=1.2)
print("STATS", k.stats(ob))
NAME = "df_adobe_house_mid" if MID else "df_adobe_house"
k.export(ob, os.path.join(OUT, NAME + ".glb"))
k.VIEWS["hero"] = (1.0, -1.35, 0.55)
print("SHEET", k.preview([ob], os.path.join(OUT, NAME + "_sheet.png"), views=("hero", "front", "right", "back")))
