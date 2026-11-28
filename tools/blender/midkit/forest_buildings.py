import math
import random

import nature_kit as nk
import timber_kit as tk
from mathutils import Vector

import forest_palette as fp

k = nk.k


def setup(seed):
    fp.setup(seed)


def opening(cx, w, z0, h):
    return (cx - w / 2 - 0.02, cx + w / 2 + 0.02, z0, z0 + h)


def finish(name, budget):
    return nk.finish(name, budget, flat=False, speckle=0.035, gradient=(0.92, 1.04), grime=(0.45, 0.8))


def logcabin():
    setup(61)
    W, D, P, H, F = 7.4, 5.6, 3.0, 3.1, 0.32
    items = tk.foundation(W + 0.3, D + 0.3, 0, D / 2)
    items.append(nk.bevbox((W, P, 0.2), (0, -P / 2, 0.12), "fo_wood_lt", 0.02))
    wins = [opening(-2.5, 1.3, 1.1, 1.1), opening(2.5, 1.3, 1.1, 1.1)]
    door_o = opening(0.0, 1.1, 0.0, 2.15)
    items += tk.log_wall("x", -W / 2, W / 2, 0.0, F, H, openings=[wins[0], wins[1], door_o], seed=1, over=0.22)
    items += tk.log_wall("x", -W / 2, W / 2, D, F, H, openings=[opening(-1.8, 1.2, 1.1, 1.1), opening(1.8, 1.2, 1.1, 1.1)], seed=2, over=0.22)
    items += tk.log_wall("y", 0, D, -W / 2, F, H, openings=[opening(D / 2, 1.2, 1.1, 1.1)], seed=3, shift=0.19, over=0.22)
    items += tk.log_wall("y", 0, D, W / 2, F, H, openings=[opening(D / 2, 1.2, 1.1, 1.1)], seed=4, shift=0.19, over=0.22)

    for o in wins:
        cx = (o[0] + o[1]) / 2
        items += tk.face_to(tk.win(1.3, 1.1, shutters=True), "f", cx, 0.0, F + 1.1 - 0.0)

    items += tk.face_to(tk.door(1.1, 2.15), "f", 0.0, 0.0, F)
    items += tk.face_to(tk.win(1.2, 1.1), "b", -1.8, D, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "b", 1.8, D, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "r", W / 2, D / 2, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "l", -W / 2, D / 2, F + 1.1)
    top = F + H
    span = D + P
    cy = (D - P) / 2
    items += tk.gable("roof", W + 0.9, span, 3.1, (0, cy, top), overhang=0.45, shingle=True)

    for x in (-W / 2 + 0.25, -2.9, 2.9, W / 2 - 0.25):
        items.append(tk.post(x, -P + 0.2, 0.2, top, 0.11))

    items += tk.rail(-W / 2 + 0.25, -P + 0.2, -0.95, -P + 0.2, 0.22, 0.9, 3)
    items += tk.rail(0.95, -P + 0.2, W / 2 - 0.25, -P + 0.2, 0.22, 0.9, 3)
    items += tk.rail(-W / 2 + 0.25, -P + 0.2, -W / 2 + 0.25, -0.1, 0.22, 0.9, 2)
    items += tk.rail(W / 2 - 0.25, -P + 0.2, W / 2 - 0.25, -0.1, 0.22, 0.9, 2)

    for i in range(3):
        items.append(nk.bevbox((1.5 - i * 0.08, 0.38, 0.12), (0, -P - 0.2 - i * 0.34 + 0.4, 0.0 + 0.0), "fo_stone" if i % 2 == 0 else "fo_stone_lt", 0.025))

    items += tk.stone_stack(W / 2 + 0.55, D / 2, 0.0, top + 3.6, 1.5, 1.4, 5, taper=0.18)
    items.append(nk.bevbox((1.8, 1.7, 0.18), (W / 2 + 0.55, D / 2, top + 3.6), "fo_stone_dk", 0.03))
    nk.add(items)

    return finish("logcabin", 7000)


def porch():
    setup(62)
    W, D, P, H, F = 8.6, 5.4, 3.0, 3.0, 0.32
    items = tk.foundation(W + 0.3, D + 0.3, 0, D / 2)
    items.append(nk.bevbox((W, P, 0.2), (0, -P / 2, 0.12), "fo_wood_lt", 0.02))
    wins = [opening(-3.4, 1.3, 1.1, 1.1), opening(3.4, 1.3, 1.1, 1.1), opening(-1.5, 1.2, 1.1, 1.1), opening(1.5, 1.2, 1.1, 1.1)]
    items += tk.log_wall("x", -W / 2, W / 2, 0.0, F, H, openings=wins + [opening(0, 1.1, 0.0, 2.15)], seed=11, over=0.22)
    items += tk.log_wall("x", -W / 2, W / 2, D, F, H, openings=[opening(-2.5, 1.2, 1.1, 1.1), opening(2.5, 1.2, 1.1, 1.1)], seed=12, over=0.22)
    items += tk.log_wall("y", 0, D, -W / 2, F, H, openings=[opening(D / 2, 1.2, 1.1, 1.1)], seed=13, shift=0.19, over=0.22)
    items += tk.log_wall("y", 0, D, W / 2, F, H, openings=[opening(D / 2, 1.2, 1.1, 1.1)], seed=14, shift=0.19, over=0.22)

    for o in wins:
        items += tk.face_to(tk.win(o[1] - o[0] - 0.04, 1.1, shutters=o in wins[:2]), "f", (o[0] + o[1]) / 2, 0.0, F + 1.1)

    items += tk.face_to(tk.door(1.1, 2.15), "f", 0.0, 0.0, F)
    items += tk.face_to(tk.win(1.2, 1.1), "b", -2.5, D, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "b", 2.5, D, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "r", W / 2, D / 2, F + 1.1)
    items += tk.face_to(tk.win(1.2, 1.1), "l", -W / 2, D / 2, F + 1.1)
    top = F + H
    items += tk.gable("roof", W + 0.9, D + P, 3.4, (0, (D - P) / 2, top), overhang=0.45, color="fo_roof_green", ridge="fo_roof_green_dk", bands=("fo_roof_green", "fo_roof_green_lt", "fo_roof_green_dk", "fo_roof_green"))

    for x in (-W / 2 + 0.3, -W / 6, W / 6, W / 2 - 0.3):
        items.append(tk.post(x, -P + 0.2, 0.2, top, 0.12))

    for a, b in ((-W / 2 + 0.3, -1.0), (1.0, W / 2 - 0.3)):
        items += tk.rail(a, -P + 0.2, b, -P + 0.2, 0.22, 0.9, 4)

    items += tk.rail(-W / 2 + 0.3, -P + 0.2, -W / 2 + 0.3, -0.1, 0.22, 0.9, 3)
    items += tk.rail(W / 2 - 0.3, -P + 0.2, W / 2 - 0.3, -0.1, 0.22, 0.9, 3)

    for i in range(3):
        items.append(nk.bevbox((1.8 - i * 0.1, 0.38, 0.12), (0, -P - 0.15 - i * 0.34 + 0.4, 0.0), "fo_stone" if i % 2 == 0 else "fo_stone_lt", 0.025))

    items += tk.stone_stack(-W / 2 + 1.2, D - 0.7, 0.0, top + 3.4, 1.3, 1.2, 15, taper=0.15)
    items.append(nk.bevbox((1.6, 1.5, 0.18), (-W / 2 + 1.2, D - 0.7, top + 3.4), "fo_stone_dk", 0.03))
    nk.add(items)

    return finish("porch", 8000)


def board_house(name, seed, W, D, P, H, roof, ridge, bands, walls, door_x, wins, hip=False, rise=2.0, chimney=True, shutters=True):
    F = 0.32
    items = tk.foundation(W + 0.25, D + 0.25, 0, D / 2)
    openings = [opening(cx, w, 1.0, 1.15) for cx, w in wins]
    d_o = opening(door_x, 1.1, 0.0, 2.2)
    items += tk.plank_wall("x", -W / 2, W / 2, 0.0, F, H, openings=openings + [d_o], seed=seed, colors=walls)
    items += tk.plank_wall("x", -W / 2, W / 2, D, F, H, openings=[opening(-W / 4, 1.2, 1.0, 1.15), opening(W / 4, 1.2, 1.0, 1.15)], seed=seed + 1, colors=walls)
    items += tk.plank_wall("y", 0, D, -W / 2, F, H, openings=[opening(D / 2, 1.2, 1.0, 1.15)], seed=seed + 2, colors=walls)
    items += tk.plank_wall("y", 0, D, W / 2, F, H, openings=[opening(D / 2, 1.2, 1.0, 1.15)], seed=seed + 3, colors=walls)

    for cx, w in wins:
        items += tk.face_to(tk.win(w, 1.15, shutters=shutters), "f", cx, 0.0, F + 1.0)

    items += tk.face_to(tk.door(1.1, 2.2), "f", door_x, 0.0, F)
    items += tk.face_to(tk.win(1.2, 1.15), "b", -W / 4, D, F + 1.0)
    items += tk.face_to(tk.win(1.2, 1.15), "b", W / 4, D, F + 1.0)
    items += tk.face_to(tk.win(1.2, 1.15), "r", W / 2, D / 2, F + 1.0)
    items += tk.face_to(tk.win(1.2, 1.15), "l", -W / 2, D / 2, F + 1.0)

    for c in (-W / 2, W / 2):
        for y in (0.0, D):
            items.append(nk.bevbox((0.22, 0.22, H), (c, y, F), "fo_wood_dk", 0.02))

    top = F + H
    span = D + P

    if hip:
        items += k.hip_roof("roof", W, D, rise, (0, D / 2, top), overhang=0.5, thickness=0.18, color=roof)
    else:
        items += tk.gable("roof", W + 0.8, span, rise, (0, (D - P) / 2, top), overhang=0.45, color=roof, ridge=ridge, trim="fo_wood_gray", bands=bands)

    if P > 0.3:
        n = 4 if W > 7 else 3

        for i in range(n):
            items.append(tk.post(-W / 2 + 0.3 + i * (W - 0.6) / (n - 1), -P + 0.2, 0.2, top, 0.1))

        items.append(nk.bevbox((W, P, 0.18), (0, -P / 2, 0.12), "fo_wood_lt", 0.02))

        for i in range(2):
            items.append(nk.bevbox((1.6 - i * 0.1, 0.36, 0.12), (door_x, -P - 0.1 - i * 0.34 + 0.35, 0.0), "fo_stone" if i == 0 else "fo_stone_lt", 0.025))

    if chimney:
        items += tk.stone_stack(W / 2 - 1.0, D * 0.7, top, top + rise * 0.7 + 1.1, 0.8, 0.8, seed, taper=0.0)
        items.append(nk.bevbox((1.0, 1.0, 0.14), (W / 2 - 1.0, D * 0.7, top + rise * 0.7 + 1.1), "fo_stone_dk", 0.025))

    nk.add(items)

    return finish(name, 6000)


def ranger():
    setup(63)

    return board_house("ranger", 71, 7.2, 3.4, 1.8, 3.0, "fo_roof_green", "fo_roof_green_dk", ("fo_roof_green", "fo_roof_green_lt", "fo_roof_green_dk", "fo_roof_green"), ("fo_wood_gray", "fo_wood", "fo_wood_dk"), 0.0, [(-2.8, 1.3), (2.8, 1.3), (-1.4, 0.0001)][:2], rise=1.7)


def hiproof():
    setup(64)

    return board_house("hiproof", 72, 8.8, 4.0, 0.0, 3.0, "fo_roof_green", "fo_roof_green_dk", None, ("fo_wood", "fo_wood_lt", "fo_wood_gray"), 0.0, [(-3.4, 1.3), (3.4, 1.3), (-1.8, 1.2), (1.8, 1.2)], hip=True, rise=3.0)


def washhouse():
    setup(65)
    W, D, H, F = 8.4, 3.8, 2.9, 0.32
    items = tk.foundation(W + 0.25, D + 0.25, 0, D / 2)
    doors = [-3.3, -1.1, 1.1, 3.3]
    ops = [opening(x, 1.0, 0.0, 2.1) for x in doors]
    items += tk.plank_wall("x", -W / 2, W / 2, 0.0, F, H, openings=ops, seed=81, colors=("fo_wood", "fo_wood_lt", "fo_wood_dk"))
    items += tk.plank_wall("x", -W / 2, W / 2, D, F, H, openings=[opening(x, 0.9, 1.5, 0.6) for x in (-3.3, -1.1, 1.1, 3.3)], seed=82, colors=("fo_wood", "fo_wood_lt", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, -W / 2, F, H, seed=83, colors=("fo_wood", "fo_wood_lt", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, W / 2, F, H, openings=[opening(D / 2, 1.0, 1.4, 0.7)], seed=84, colors=("fo_wood", "fo_wood_lt", "fo_wood_dk"))

    for i, x in enumerate(doors):
        items += tk.face_to(tk.door(1.0, 2.1, leaf="fo_door" if i % 2 == 0 else "fo_door_dk", step=True), "f", x, 0.0, F)

    for x in (-3.3, -1.1, 1.1, 3.3):
        items += tk.face_to(tk.win(0.9, 0.6, panes=1), "b", x, D, F + 1.5)

    items += tk.face_to(tk.win(1.0, 0.7, panes=1), "r", W / 2, D / 2, F + 1.4)

    for x in (-W / 2, -W / 6 * 0 - 2.4, 0.0, 2.4, W / 2):
        items.append(nk.bevbox((0.2, 0.2, H), (x, 0.0, F), "fo_wood_dk", 0.015))

    top = F + H
    items += tk.gable("roof", W + 0.9, D + 1.2, 1.35, (0, D / 2 - 0.3, top), overhang=0.45, color="fo_roof_green", ridge="fo_roof_green_dk", bands=("fo_roof_green", "fo_roof_green_lt", "fo_roof_green_dk", "fo_roof_green"))

    for x in (-W / 2 + 0.3, -3.0, 0.0, 3.0, W / 2 - 0.3):
        items.append(tk.post(x, -0.9, 0.2, top - 0.05, 0.09))

    items.append(nk.bevbox((W, 0.9, 0.16), (0, -0.45, 0.12), "fo_wood_lt", 0.02))
    items.append(nk.bevbox((0.4, 0.4, 1.4), (W / 2 - 0.9, D * 0.6, top), "fo_metal", 0.03))
    nk.add(items)

    return finish("washhouse", 6000)


def woodshed():
    setup(66)
    W, D, H, F = 4.6, 2.2, 3.0, 0.2
    items = [nk.bevbox((W + 0.2, D + 0.2, F), (0, D / 2, 0), "fo_stone", 0.04)]
    items += tk.plank_wall("x", -W / 2, W / 2, D, F, H, seed=91, colors=("fo_wood_gray", "fo_wood", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, -W / 2, F, H - 0.3, seed=92, colors=("fo_wood_gray", "fo_wood", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, W / 2, F, H - 0.3, seed=93, colors=("fo_wood_gray", "fo_wood", "fo_wood_dk"))

    for x in (-W / 2, 0.0, W / 2):
        items.append(tk.post(x, 0.0, F, F + H - 0.3, 0.1))

    r = random.Random(5)

    for row in range(5):
        for i in range(9 - row % 2):
            x = -2.0 + i * 0.5 + (0.25 if row % 2 else 0.0)
            z = F + 0.15 + row * 0.28
            items.append(nk.tube("log", [(x, 0.5, z), (x, D - 0.3, z)], [0.14, 0.14], 5, ["fo_log", "fo_log_lt", "fo_log_dk"], cap_top="fo_log_end", cap_bottom="fo_log_end", seed=row + i))

    items += tk.shed_roof(W + 0.8, D + 1.1, 0.9, D + 0.55, F + H - 0.3)
    nk.add(items)

    return finish("woodshed", 3500)


def outhouse():
    setup(67)
    W, D, H, F = 2.3, 2.3, 2.5, 0.2
    items = [nk.bevbox((W + 0.2, D + 0.2, F), (0, D / 2, 0), "fo_stone", 0.04)]
    items += tk.plank_wall("x", -W / 2, W / 2, 0.0, F, H, openings=[opening(0, 1.0, 0.0, 2.0)], seed=101, plank=0.3, colors=("fo_wood", "fo_wood_gray", "fo_wood_dk"))
    items += tk.plank_wall("x", -W / 2, W / 2, D, F, H, seed=102, plank=0.3, colors=("fo_wood", "fo_wood_gray", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, -W / 2, F, H, openings=[opening(1.6, 0.5, 1.9, 0.18)], seed=103, plank=0.3, colors=("fo_wood", "fo_wood_gray", "fo_wood_dk"))
    items += tk.plank_wall("y", 0, D, W / 2, F, H, seed=104, plank=0.3, colors=("fo_wood", "fo_wood_gray", "fo_wood_dk"))
    items += tk.face_to(tk.door(1.0, 2.0, step=False), "f", 0.0, 0.0, F)

    for c in (-W / 2, W / 2):
        for y in (0.0, D):
            items.append(nk.bevbox((0.16, 0.16, H), (c, y, F), "fo_wood_dk", 0.015))

    items += tk.gable("roof", W + 0.6, D + 0.2, 1.0, (0, D / 2, F + H), overhang=0.3, shingle=True)
    nk.add(items)

    return finish("outhouse", 2000)


def leanto():
    setup(68)
    W, D, H, F = 3.6, 2.7, 2.0, 0.16
    items = [nk.bevbox((W, D, F), (0, 0, 0), "fo_wood_lt", 0.03)]
    items += tk.log_wall("x", -W / 2, W / 2, D / 2, F, H + 0.9, seed=111, over=0.15)
    items += tk.log_wall("y", -D / 2, D / 2, -W / 2, F, H + 0.5, seed=112, shift=0.19, over=0.15)
    items += tk.log_wall("y", -D / 2, D / 2, W / 2, F, H + 0.5, seed=113, shift=0.19, over=0.15)

    for x in (-W / 2 + 0.1, W / 2 - 0.1):
        items.append(tk.post(x, -D / 2 + 0.1, F, F + H - 0.1, 0.1))

    items += tk.shed_roof(W + 0.7, D + 0.9, 1.0, D / 2 + 0.45, F + H + 0.1)

    for i in range(5):
        items.append(nk.bar((-W / 2 + 0.3 + i * (W - 0.6) / 4, D / 2 - 0.1, F + 0.3), (-W / 2 + 0.3 + i * (W - 0.6) / 4, -D / 2 + 0.3, F + 0.3), 0.07, "fo_log_lt", 5))

    items.append(nk.bevbox((W - 0.6, 1.0, 0.18), (0, D / 2 - 0.8, F + 0.3), "fo_canvas", 0.04))
    nk.add(items)

    return finish("leanto", 2500)


def aframe():
    setup(69)
    W, D, H, F = 4.6, 8.4, 8.2, 0.9
    items = tk.foundation(W + 0.5, D + 0.4, 0, 0, h=0.34)
    deck = nk.bevbox((W + 0.6, 2.2, 0.16), (0, -D / 2 - 1.1 + 0.2, 0.34), "fo_wood_lt", 0.025)
    items.append(deck)
    rise = H
    roof = k.gable_roof("roof", D + 0.9, W, rise, (0, 0, 0.34), overhang=0.0, thickness=0.2, color="fo_roof_green", trim="fo_wood", ridge="fo_roof_green_dk", seams=1.1)

    for p in roof:
        k.rotate(p, 90)

    items += roof
    fy = -D / 2 - 0.45

    for gx in (-1.4, 1.4, 0.0):
        h = H - 0.9 - abs(gx) * (H - 0.9) / (W / 2) - 0.5
        items.append(nk.plain((0.14, 0.12, h), (gx, fy - 0.05, 0.34 + 0.5), "fo_wood_dk"))

    items.append(k.sweep("glass", [(-W / 2 + 0.55, 1.1), (W / 2 - 0.55, 1.1), (0.0, H - 1.9)], 0.06, (0, fy - 0.02, 0.34 + 0.9), nk.idx("fo_glass"), axis="y"))
    items.append(k.sweep("glass2", [(-W / 2 + 0.9, 1.9), (W / 2 - 0.9, 1.9), (0.0, H - 2.9)], 0.06, (0, fy - 0.06, 0.34 + 1.2), nk.idx("fo_glass_lt"), axis="y"))
    items += tk.face_to(tk.door(1.1, 2.1, step=False), "f", 1.3, fy, 0.4)

    for sx in (-1, 1):
        items.append(nk.bevbox((0.18, 0.18, 1.4), (sx * (W / 2 + 0.4), -D / 2 - 1.2, 0.34), "fo_wood_dk", 0.02))

    items += tk.rail(-W / 2 - 0.4, -D / 2 - 1.2, W / 2 + 0.4, -D / 2 - 1.2, 0.5, 0.9, 5)
    items.append(nk.bar((W / 2 - 0.9, D / 2 - 1.0, 3.0), (W / 2 - 0.9, D / 2 - 1.0, H - 0.2), 0.14, "fo_metal", 8))
    items.append(nk.bevbox((0.46, 0.46, 0.1), (W / 2 - 0.9, D / 2 - 1.0, H - 0.2), "fo_metal_dk", 0.02))

    nk.add(items)

    return finish("aframe", 5000)


def lookout():
    setup(70)
    items = []
    base, top_w, legs_h = 2.75, 1.55, 8.7
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    levels = [0.0, 0.9, 3.4, 6.0, legs_h]

    def half(z):
        return base + (top_w - base) * z / legs_h

    for sx, sy in corners:
        pts = [(sx * half(z), sy * half(z), z) for z in (0, 2, 4, 6, 8, legs_h)]
        items.append(nk.tube("leg", pts, [0.2, 0.18, 0.16, 0.15, 0.14, 0.13], 6, ["fo_wood_dk", "fo_wood"], cap_top="fo_wood_dk", cap_bottom="fo_wood_dk"))
        items.append(nk.bevbox((0.7, 0.7, 0.25), (sx * base, sy * base, 0.0), "fo_stone", 0.04))

    for z in levels:
        h = half(z)

        for i in range(4):
            (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
            items.append(nk.bar((ax * h, ay * h, z + 0.15), (bx * h, by * h, z + 0.15), 0.1, "fo_wood", 5))

    for lvl in range(len(levels) - 1):
        z0, z1 = levels[lvl], levels[lvl + 1]

        if z1 - z0 < 1.0:
            continue

        for i in (0, 1):
            (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
            flip = (lvl + i) % 2 == 0
            za, zb = (z0, z1) if flip else (z1, z0)
            items.append(nk.bar((ax * half(za), ay * half(za), za + 0.15), (bx * half(zb), by * half(zb), zb + 0.15), 0.075, "fo_wood_lt", 5))

    for i in range(19):
        z = 0.2 + i * 0.45
        items.append(nk.bevbox((1.0, 0.42, 0.07), (0, -half(z) + 0.55, z), "fo_wood_lt", 0.01))

    for sx in (-0.55, 0.55):
        items.append(nk.bar((sx, -half(0.1) + 0.55, 0.1), (sx, -half(8.6) + 0.55, 8.6), 0.05, "fo_wood_dk", 5))

    cab_z = legs_h + 0.15
    cw = 3.7
    items.append(nk.bevbox((cw + 1.8, cw + 1.8, 0.22), (0, 0, cab_z), "fo_wood_lt", 0.03))
    items += tk.rail(-cw / 2 - 0.85, -cw / 2 - 0.85, cw / 2 + 0.85, -cw / 2 - 0.85, cab_z + 0.22, 0.95, 6)
    items += tk.rail(-cw / 2 - 0.85, cw / 2 + 0.85, cw / 2 + 0.85, cw / 2 + 0.85, cab_z + 0.22, 0.95, 6)
    items += tk.rail(-cw / 2 - 0.85, -cw / 2 - 0.85, -cw / 2 - 0.85, cw / 2 + 0.85, cab_z + 0.22, 0.95, 6)
    items += tk.rail(cw / 2 + 0.85, -cw / 2 - 0.85, cw / 2 + 0.85, cw / 2 + 0.85, cab_z + 0.22, 0.95, 6)
    ch = 2.3
    cz = cab_z + 0.22
    items.append(nk.bevbox((cw, cw, 0.9), (0, 0, cz), "fo_wood", 0.03))

    for face, ax, ay in (("f", 0.0, -cw / 2), ("b", 0.0, cw / 2), ("r", cw / 2, 0.0), ("l", -cw / 2, 0.0)):
        items += tk.face_to(tk.win(cw - 1.0, 1.15, panes=3), face, ax, ay, cz + 0.9)

    items.append(nk.bevbox((cw + 0.2, cw + 0.2, 0.18), (0, 0, cz + 0.9 + 1.15), "fo_wood_dk", 0.03))
    items += k.hip_roof("roof", cw + 0.5, cw + 0.5, 1.5, (0, 0, cz + 2.4), overhang=0.7, thickness=0.2, color="fo_shingle")
    items.append(nk.bar((0, 0, cz + 3.8), (0, 0, cz + 4.7), 0.05, "fo_metal", 5))
    items.append(nk.bevbox((0.5, 0.5, 0.14), (0, 0, cz + 3.88), "fo_metal_dk", 0.02))
    nk.add(items)

    return finish("lookout", 8000)


ALL = {
    "logcabin": logcabin,
    "ranger": ranger,
    "lookout": lookout,
    "woodshed": woodshed,
    "outhouse": outhouse,
    "leanto": leanto,
    "aframe": aframe,
    "porch": porch,
    "washhouse": washhouse,
    "hiproof": hiproof,
}
