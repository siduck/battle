import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "islands")
from pf import *

CUBE = "cube-house-module-a9b8e8"
STAIR = "exterior-staircase-run-4e34ea"
CAVE = "cave-house-front-ed6b36"
SOLAR = "solar-water-heater-db1039"
M = 4.4
PLASTER = (0.95, 0.93, 0.89)
SHADE = (0.86, 0.84, 0.8)
GROUT = (0.6, 0.57, 0.52)
STONES = [(0.86, 0.81, 0.72), (0.82, 0.77, 0.68), (0.89, 0.85, 0.77), (0.8, 0.75, 0.66)]
BLUE = (0.13, 0.36, 0.72)
SEA = (0.16, 0.55, 0.66)
FOAM = (0.42, 0.74, 0.8)


def fresh():
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    return bm


def tiles(bm, x0, y0, x1, y1, z, n, seed):
    add_box(bm, (x0, y0, z - 0.12), (x1, y1, z - 0.02), GROUT)
    sx = (x1 - x0) / n
    sy = (y1 - y0) / n
    k = seed

    for i in range(n):
        for j in range(n):
            k = (k * 1103515245 + 12345) & 0x7FFFFFFF
            c = STONES[k % len(STONES)]
            add_box(bm, (x0 + i * sx + 0.04, y0 + j * sy + 0.04, z - 0.1), (x0 + (i + 1) * sx - 0.04, y0 + (j + 1) * sy - 0.04, z), c)


def block():
    bm = fresh()
    h = M / 2
    add_box(bm, (-h, -h, -17.0), (h, h, -0.3), PLASTER)
    add_box(bm, (-h - 0.04, -h - 0.04, -0.34), (h + 0.04, h + 0.04, -0.1), SHADE)
    tiles(bm, -h, -h, h, h, 0.0, 4, 7)

    return bm


def plaza():
    bm = fresh()
    h = M / 2
    tiles(bm, -h, -h, h, h, 0.0, 4, 3)

    return bm


def recolor(bm, accent, wall):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            mx = max(c[0], c[1], c[2])
            mn = min(c[0], c[1], c[2])

            if mx - mn > 0.15 and c[2] > c[0]:
                k = (c[0] + c[1] + c[2]) / 3 / 0.4
                l[col] = (min(1, accent[0] * k), min(1, accent[1] * k), min(1, accent[2] * k), 1.0)
            elif mn > 0.7:
                l[col] = (c[0] * wall[0], c[1] * wall[1], c[2] * wall[2], 1.0)


def house(floors, dome=False, accent=None, wall=(1, 1, 1), spin=0):
    bm = fresh()

    for f in range(floors):
        part(bm, CUBE, (0, 0, f * 3.0), spin * math.pi / 2 if f == 0 else ((spin + 1) % 4) * math.pi / 2)

    if accent is not None or wall != (1, 1, 1):
        recolor(bm, accent or BLUE, wall)

    lo, hi = bounds(bm)
    c = (lo + hi) / 2
    bm.transform(Matrix.Scale(1.1, 4) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z))))

    top = floors * 3.3
    e = 2.2
    add_box(bm, (-e, -e, top), (e, -e + 0.22, top + 0.28), SHADE)
    add_box(bm, (-e, e - 0.22, top), (e, e, top + 0.28), SHADE)
    add_box(bm, (-e, -e, top), (-e + 0.22, e, top + 0.28), SHADE)
    add_box(bm, (e - 0.22, -e, top), (e, e, top + 0.28), SHADE)

    if not dome:
        sx = 1.3 if spin % 2 else -1.3
        add_box(bm, (sx - 0.3, 1.2, top), (sx + 0.3, 1.8, top + 1.1), PLASTER)
        add_box(bm, (sx - 0.38, 1.12, top + 1.1), (sx + 0.38, 1.88, top + 1.22), SHADE)

    if dome:
        add_box(bm, (-1.3, -1.3, top), (1.3, 1.3, top + 0.7), PLASTER)
        d = bmesh.new()
        dc = d.loops.layers.float_color.new("Col")
        bmesh.ops.create_uvsphere(d, u_segments=16, v_segments=8, radius=1.45)
        bmesh.ops.delete(d, geom=[v for v in d.verts if v.co.z < -0.01], context="VERTS")

        for v in d.verts:
            v.co.z += top + 0.7

        for f in d.faces:
            for l in f.loops:
                l[dc] = (BLUE[0], BLUE[1], BLUE[2], 1.0)

        me = bpy.data.meshes.new("d")
        d.to_mesh(me)
        d.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        add_box(bm, (-0.08, -0.08, top + 2.1), (0.08, 0.08, top + 2.6), (0.92, 0.9, 0.86))

    return bm


def module(src, accent=None):
    bm = fresh()
    part(bm, src, (0, 0, 0), 0)

    if accent is not None:
        recolor(bm, accent, (1, 1, 1))

    lo, hi = bounds(bm)
    c = (lo + hi) / 2
    bm.transform(Matrix.Scale(1.1, 4) @ Matrix.Translation(Vector((-c.x, -c.y, -lo.z))))
    lo, hi = bounds(bm)
    e = 2.2
    top = hi.z
    add_box(bm, (-e, -e, top), (e, -e + 0.22, top + 0.28), SHADE)
    add_box(bm, (-e, e - 0.22, top), (e, e, top + 0.28), SHADE)

    return bm


def stair():
    bm = fresh()
    n = 12
    run = 2 * M
    rise = 3.3
    d = run / n
    r = rise / n
    w = 1.4
    h = M / 2

    for i in range(n):
        y0 = -i * d
        y1 = -(i + 1) * d
        top = (i + 1) * r
        add_box(bm, (-w, y1, -1.0), (w, y0, top - 0.08), PLASTER)
        add_box(bm, (-w, y1, top - 0.08), (w, y0, top), STONES[i % 2])
        add_box(bm, (-h, y1, -1.0), (-w, y0, top + 0.95), PLASTER if i % 2 else SHADE)
        add_box(bm, (w, y1, -1.0), (h, y0, top + 0.95), PLASTER if i % 2 else SHADE)

    return bm


def water():
    bm = fresh()
    s = 3 * M / 2
    add_box(bm, (-s, -s, -0.2), (s, s, 0.0), SEA)

    for k, (x, y, l) in enumerate([(-3, -2, 4), (2, 3, 3), (-1, 4.5, 2.5), (3.5, -3.5, 3), (-4, 1, 2)]):
        add_box(bm, (x - l / 2, y - 0.08, 0.0), (x + l / 2, y + 0.08, 0.01), FOAM)

    return bm


def parapet():
    bm = fresh()
    h = M / 2
    add_box(bm, (-h, -0.18, 0.0), (h, 0.18, 0.85), PLASTER)
    add_box(bm, (-h - 0.03, -0.22, 0.85), (h + 0.03, 0.22, 0.95), SHADE)

    return bm


def solar():
    bm = load(os.path.join(P, SOLAR + ".glb"))
    normalize(bm, scale=1.0)

    return bm


def run():
    os.makedirs(OUT, exist_ok=True)
    infos = {}
    pieces = [
        ("block", block),
        ("plaza", plaza),
        ("cube1", lambda: house(1)),
        ("cube1b", lambda: house(1, accent=(0.2, 0.5, 0.38), spin=1)),
        ("cube1c", lambda: house(1, accent=(0.66, 0.3, 0.2), wall=(1.0, 0.95, 0.86), spin=2)),
        ("cube1d", lambda: house(1, accent=(0.1, 0.5, 0.6), spin=3)),
        ("cube2", lambda: house(2)),
        ("cube2b", lambda: house(2, accent=(0.2, 0.5, 0.38), wall=(1.0, 0.96, 0.9), spin=1)),
        ("solar", lambda: solar()),
        ("dome1", lambda: house(1, dome=True)),
        ("dome2", lambda: house(2, dome=True)),
        ("stair", stair),
        ("cave1", lambda: module(CAVE)),
        ("cave1b", lambda: module(CAVE, accent=(0.2, 0.5, 0.38))),
        ("water", water),
        ("parapet", parapet),
    ]

    for name, fn in pieces:
        bm = fn()
        infos[name] = export(bm, name)
        bm.free()
        print("DONE", name, infos[name]["tris"])

    with open(os.environ["JSON"], "w") as f:
        json.dump(infos, f, indent=1)


run()
