import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "suburb"))
sys.path.insert(0, os.path.join(HERE, "..", "kit"))

import bmesh
import bpy
import jp
import dfkit as k
from jp import add, flat, bar, place, shift, c, N, T, MID, FAR
from mathutils import Vector

NY_KEY = "#d6c6a8"
NY_ACCENTS = ("ny_red", "ny_red_dark", "ny_yellow", "ny_orange", "ny_green", "ny_green_dark", "ny_navy", "ny_leaf", "ny_leaf_dark", "ny_leaf_light", "ny_copper")
SOLIDS = []


def bx(size, at, color, bevel=0.03):
    if FAR or min(size) < 0.15:
        return k.box("f", size, at, c(color))

    return k.beveled_box("b", size, at, c(color), bevel, mid=False)


def setup(seed=1, key=NY_KEY, mix=0.0, accents=NY_ACCENTS, accent_amount=0.04):
    jp.setup(seed)
    k.harmonize(key, mix, accents=accents, accent_amount=accent_amount)
    SOLIDS.clear()


def rng():
    return jp.rng


def solid(x0, y0, x1, y1, z0, z1):
    SOLIDS.append((x0, y0, x1, y1, z0, z1))


def quad(w, h, at, color, facing=-1):
    ob = k.box("glassq", (w, 0.02, h), (0, 0, 0), c(color))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    drop = [f for f in bm.faces if f.normal.y * facing < 0.5]
    bmesh.ops.delete(bm, geom=drop, context="FACES_ONLY")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    k.move(ob, *at)

    return ob


def flush(w, h, split=0.55, low="ny_glass", high="ny_glass_light"):
    return [quad(w, h * split, (0, -0.012, 0), low), quad(w, h * (1 - split), (0, -0.012, h * split), high)]


def sash(w, h, wall, trim="ny_lime_light", panes=2, rows=2, arch=False, sill=True, lintel=True, shutters=False, bars=False):
    if FAR:
        items = flush(w, h)

        if sill:
            items.append(flat((w + 0.3, 0.3, 0.12), (0, -0.12, -0.12), trim))

        if lintel:
            items.append(flat((w + 0.24, 0.2, 0.18), (0, -0.07, h), trim))

        if shutters:
            for sx in (-1, 1):
                items.append(quad(w * 0.42, h, (sx * (w / 2 + w * 0.24), -0.04, 0), "ny_green_dark"))

        return items

    items = [quad(w, h * 0.55, (0, T - 0.12, 0), "ny_glass"), quad(w, h * 0.45, (0, T - 0.12, h * 0.55), "ny_glass_light")]
    items.append(flat((w, 0.05, 0.06), (0, 0.05, h * 0.5 - 0.03), trim))
    items.append(flat((0.06, 0.05, h), (0, 0.05, 0), trim))

    if panes > 2:
        for i in (-1, 1):
            items.append(flat((0.04, 0.05, h), (i * w / 3, 0.05, 0), trim))

    items.append(flat((w, 0.05, 0.06), (0, 0.05, h - 0.06), trim))

    if bars:
        for i in range(-2, 3):
            items.append(flat((0.03, 0.03, h), (i * w / 5, 0.02, 0), "ny_iron"))

    if sill:
        items.append(bx((w + 0.3, 0.3, 0.12), (0, -0.12, -0.12), trim, 0.02))

    if lintel:
        items.append(bx((w + 0.24, 0.2, 0.18), (0, -0.07, h), trim, 0.02))

    if shutters:
        for sx in (-1, 1):
            items.append(bx((w * 0.42, 0.06, h), (sx * (w / 2 + w * 0.24), -0.02, 0), "ny_green_dark", 0.01))

    if w < 1.6 and rng().random() < 0.14:
        unit = rng().choice(("ny_cream", "ny_lime_light", "ny_conc"))
        items.append(bx((0.66, 0.5, 0.4), (0, -0.16, 0.02), unit, 0.02))
        items.append(flat((0.5, 0.02, 0.28), (0, -0.42, 0.08), "ny_iron_light"))

        for i in range(4):
            items.append(flat((0.5, 0.03, 0.025), (0, -0.44, 0.1 + i * 0.07), "ny_iron"))

    return items


def storefront(w, h, frame="ny_iron", bays=3, kick="ny_conc_dark", door=True):
    if FAR:
        return [quad(w, 0.45, (0, -0.012, 0), kick), quad(w, h * 0.7 - 0.45, (0, -0.012, 0.45), "ny_glass"), quad(w, h * 0.3 - 0.3, (0, -0.012, h * 0.7), "ny_glass_light"),
                flat((w + 0.1, 0.24, 0.3), (0, -0.05, h - 0.3), frame)]

    items = [flat((w, 0.04, h), (0, T - 0.03, 0), "void")]
    bw = w / bays

    for i in range(bays):
        x = -w / 2 + bw * (i + 0.5)
        items.append(quad(bw - 0.12, h * 0.7 - 0.45, (x, T - 0.14, 0.45), "ny_glass"))
        items.append(quad(bw - 0.12, h * 0.3 - 0.1, (x, T - 0.139, h * 0.7), "ny_glass_light"))
        items.append(bx((bw - 0.04, 0.12, 0.42), (x, 0.02, 0), kick, 0.01))

    for i in range(bays + 1):
        edge = (0.07 if i == 0 else -0.07 if i == bays else 0)
        items.append(flat((0.1, 0.16, h), (-w / 2 + bw * i + edge, 0.02, 0), frame))

    items.append(bx((w + 0.1, 0.24, 0.3), (0, -0.05, h - 0.3), frame, 0.015))
    items.append(flat((w - 0.1, 0.1, 0.07), (0, 0.04, h * 0.7 - 0.04), frame))

    return items


def glazed_door(w, h, color="ny_iron"):
    if FAR:
        return [quad(w, h, (0, -0.012, 0), color)]

    return [flat((w, 0.04, h), (0, T - 0.03, 0), "void"), quad(w - 0.2, h - 0.45, (0, T - 0.14, 0.12), "ny_glass"), bx((w, 0.1, 0.1), (0, 0.02, h - 0.1), color, 0.01),
            flat((0.08, 0.1, h), (-w / 2 + 0.04, 0.03, 0), color), flat((0.08, 0.1, h), (w / 2 - 0.04, 0.03, 0), color), flat((0.06, 0.1, h * 0.55), (0, 0.03, 0.1), color)]


def stoop(w, rise=1.0, color="ny_lime"):
    items = []
    n = max(2, int(rise / 0.2))

    for i in range(n):
        items.append(bx((w, 0.3, rise / n), (0, -0.15 - 0.3 * (n - 1 - i) - 0.12, i * rise / n), color, 0.012))

    items.append(bx((w, 0.4, 0.14), (0, -0.2 - 0.3 * n - 0.1, rise - 0.14), color, 0.015))

    return items


def louver(w, h, color="ny_iron_light"):
    if FAR:
        return [quad(w, h, (0, -0.012, 0), color)]

    items = [flat((w, 0.04, h), (0, T - 0.03, 0), "void"), flat((w + 0.1, 0.1, 0.08), (0, 0.02, -0.04), "ny_conc")]
    n = max(3, int(h / 0.16))

    for i in range(n):
        items.append(flat((w - 0.1, 0.06, 0.05), (0, 0.1, 0.08 + i * (h - 0.12) / n), color))

    return items


def garage_door(w, h, color="ny_conc"):
    if FAR:
        return [quad(w, h, (0, -0.012, 0), color)]

    items = [flat((w, 0.04, h), (0, T - 0.03, 0), "void"), bx((w - 0.15, 0.1, h - 0.1), (0, 0.1, 0), color, 0.01)]

    for i in range(1, 5):
        items.append(flat((w - 0.2, 0.04, 0.05), (0, 0.04, h * i / 5), "ny_conc_dark"))

    for sx in (-1, 1):
        items.append(flat((0.14, 0.14, h), (sx * (w / 2 - 0.07), 0.02, 0), "ny_iron"))

    return items


OPENINGS = {
    "sash": sash,
    "store": storefront,
    "door": glazed_door,
    "louver": louver,
    "garage": garage_door,
}


def opening(kind, w, h, wall, **o):
    if kind in ("sash", "lite"):
        return OPENINGS[kind](w, h, wall, **o)

    if kind == "door":
        return glazed_door(w, h)

    return OPENINGS[kind](w, h, **o)


def facade(width, height, wall_color, spec=(), extra=()):
    holes = []
    items = []

    for kind, x, z, w, h, o in spec:
        holes.append((x, z, w, h))
        items += shift(opening(kind, w, h, wall_color, **o), x, 0, z)

    return jp.wall(width, height, holes, wall_color) + items + list(extra)


def storey(w, d, z, h, color, front=(), back=(), left=(), right=(), fx=(), bxx=(), lx=(), rx=()):
    fy = -d / 2
    place(facade(w, h, color, front, fx), 0, fy, z, 0)
    place(facade(w, h, color, back, bxx), 0, -fy, z, 180)
    side = d - 2 * T
    place(facade(side, h, color, left, lx), -w / 2, 0, z, -90)
    place(facade(side, h, color, right, rx), w / 2, 0, z, 90)


def grid(width, cols, w, h, z, margin=0.0, kind="sash", **o):
    gap = (width - 2 * margin) / cols

    return [(kind, -width / 2 + margin + gap * (i + 0.5), z, w, h, o) for i in range(cols)]


def band(w, d, z, color, h=0.25, out=0.1):
    b = bx((w + out * 2, d + out * 2, h), (0, 0, z), color, 0.025)
    jp.soft.append(b)
    add(b)


def plinth(w, d, h=0.5, color="ny_conc_dark", out=0.08):
    add(bx((w + out * 2, d + out * 2, h), (0, 0, -0.02), color, 0.03))


def cornice(w, d, z, color="ny_lime", h=0.5, out=0.4, brackets=True):
    add(bx((w + out * 2, d + out * 2, h * 0.55), (0, 0, z + h * 0.45), color, 0.04))
    add(bx((w + out, d + out, h * 0.5), (0, 0, z), color + "_dark" if color + "_dark" in k._INDEX else color, 0.03))

    if brackets and not FAR:
        n = max(3, int(w / 0.9))

        for i in range(n):
            x = -w / 2 + (i + 0.5) * w / n
            add(bx((0.22, out * 0.9, h * 0.5), (x, -d / 2 - out * 0.45, z), color, 0.015))


def parapet(w, d, z, h=0.7, color="ny_brick", cap="ny_lime"):
    t = 0.3

    for px, py, lx, ly in ((0, -d / 2 + t / 2, w, t), (0, d / 2 - t / 2, w, t), (-w / 2 + t / 2, 0, t, d - 2 * t), (w / 2 - t / 2, 0, t, d - 2 * t)):
        p = flat((lx, ly, h), (px, py, z), color)
        jp.soft.append(p)
        add(p)
        add(bx((lx + 0.12, ly + 0.12, 0.12), (px, py, z + h), cap, 0.02))

    add(flat((w - 0.2, d - 0.2, 0.08), (0, 0, z - 0.04), "ny_tar"))


def ac_box(at, facing=0.0, color="ny_conc"):
    x, y, z = at
    items = [bx((0.9, 0.5, 0.6), (0, 0, 0), color, 0.03), flat((0.5, 0.02, 0.4), (0.1, -0.26, 0.1), "ny_iron_light"), flat((0.2, 0.02, 0.4), (-0.3, -0.26, 0.1), "ny_conc_dark")]

    if not FAR:
        items.append(k.prism("fan", 8 * N, 0.17, 0.02, (0.1, -0.26, 0.3), c("ny_iron")))
        k.rotate(items[-1], 90, "X", (0.1, -0.26, 0.3))

    for it in items:
        k.rotate(it, facing)
        k.move(it, x, y, z)

    return items


def vent_stack(x, y, z, h=0.9, r=0.18):
    return [k.prism("v", 8, r, h, (x, y, z), c("ny_iron_light")), k.prism("vc", 8, r * 1.5, 0.08, (x, y, z + h), c("ny_iron"), radius_top=r * 0.4)]


def watertank(at, scale=1.0):
    x, y, z = at
    s = scale
    items = []

    for lx in (-0.7, 0.7):
        for ly in (-0.7, 0.7):
            items.append(bar((x + lx * s, y + ly * s, z), (x + lx * s * 0.9, y + ly * s * 0.9, z + 1.8 * s), 0.05 * s, "ny_iron", 4))

    items.append(flat((1.7 * s, 1.7 * s, 0.1 * s), (x, y, z + 1.8 * s), "ny_wood_dark"))
    items.append(k.prism("tank", 12 * N, 1.2 * s, 2.0 * s, (x, y, z + 1.9 * s), c("ny_wood")))

    for zz in (0.5, 1.0, 1.5):
        items.append(k.prism("hoop", 12 * N, 1.24 * s, 0.07 * s, (x, y, z + (1.9 + zz) * s), c("ny_iron")))

    items.append(k.prism("lid", 12 * N, 1.3 * s, 0.7 * s, (x, y, z + 3.9 * s), c("ny_wood_dark"), radius_top=0.05 * s))

    return items


def bulkhead(at, w=2.2, d=2.0, h=2.4, color="ny_brick"):
    x, y, z = at
    items = [bx((w, d, h), (x, y, z), color, 0.04), bx((w + 0.3, d + 0.3, 0.14), (x, y, z + h), "ny_conc", 0.02), bx((0.9, 0.12, 1.9), (x, y - d / 2 - 0.04, z), "ny_iron", 0.01)]

    return items


def roof_gear(w, d, z, count=3, tank=False, seed=0):
    r = rng()
    spots = [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 0), (0, -1), (0, 1)]
    r.shuffle(spots)
    placed = 0

    if tank:
        sx, sy = spots.pop()
        add(watertank((sx * w * 0.2, sy * d * 0.2, z)))
        placed += 1

    for sx, sy in spots:
        if placed >= count:
            break

        x = sx * (w / 2 - 1.4) * 0.8
        y = sy * (d / 2 - 1.4) * 0.8
        which = r.choice(("ac", "vent", "bulk", "ac"))

        if which == "ac":
            add(ac_box((x, y, z), r.choice((0, 90, 180)), r.choice(("ny_conc", "ny_lime_dark"))))
        elif which == "vent":
            add(vent_stack(x, y, z))
        else:
            add(bulkhead((x, y, z), 1.8, 1.6, 2.2))

        placed += 1


def fire_escape(w, floors, floor_h, wall_y, z0=0.0, x=0.0, depth=1.0, ladder=True, color="ny_iron"):
    items = []
    yf = wall_y - depth
    ztop = z0 + floors * floor_h

    for f in range(floors):
        z = z0 + (f + 1) * floor_h - 0.55
        items.append(bx((w, depth, 0.07), (x, wall_y - depth / 2, z), color, 0.01))

        if not FAR:
            n = max(4, int(w / 0.5))

            for i in range(n + 1):
                items.append(flat((0.03, 0.03, 0.95), (x - w / 2 + i * w / n, yf, z), color))

            for sx in (-1, 1):
                for j in range(1, 4):
                    items.append(flat((0.03, 0.03, 0.95), (x + sx * w / 2, wall_y - j * depth / 4, z), color))

        items.append(bar((x - w / 2, yf, z + 0.95), (x + w / 2, yf, z + 0.95), 0.025, color, 4))
        items.append(bar((x - w / 2, yf, z + 0.45), (x + w / 2, yf, z + 0.45), 0.018, color, 4))

        for sx in (-1, 1):
            items.append(bar((x + sx * w / 2, yf, z + 0.95), (x + sx * w / 2, wall_y, z + 0.95), 0.025, color, 4))

        if f:
            sx = 1 if f % 2 else -1
            items.append(bar((x + sx * (w / 2 - 0.3), yf + 0.05, z - floor_h + 0.05), (x - sx * (w / 2 - 0.3), yf + 0.05, z), 0.04, color, 4))
            items.append(bar((x + sx * (w / 2 - 0.5), yf + 0.2, z - floor_h + 0.05), (x - sx * (w / 2 - 0.5), yf + 0.2, z), 0.04, color, 4))

    if ladder:
        items.append(bar((x + w / 2 - 0.15, yf, z0 + 1.0), (x + w / 2 - 0.15, yf + 0.05, z0 + floor_h - 0.5), 0.03, color, 4))

    return items


def sign_box(w, h, base="ny_navy", ink="ny_cream", depth=0.14, letters=None):
    items = [bx((w, depth, h), (0, -depth / 2, 0), base, 0.02)]
    n = letters or max(3, int(w / 0.5))
    lw = (w - 0.3) / n
    r = rng()

    for i in range(n):
        x = -w / 2 + 0.15 + lw * (i + 0.5)
        hh = h * r.uniform(0.4, 0.6)
        items.append(flat((lw * 0.65, 0.02, hh), (x, -depth - 0.01, (h - hh) / 2), ink))

    return items


def striped_awning(w, depth, a="ny_red", b="ny_white", drop=0.9, slope=24, n=None, valance=0.28):
    items = []
    n = n or max(6, int(w / 0.28))
    sw = w / n
    rad = math.radians(slope)
    run = depth * math.cos(rad)
    fall = depth * math.sin(rad)

    for i in range(n):
        col = a if i % 2 == 0 else b
        s = flat((sw, depth, 0.05), (-w / 2 + sw * (i + 0.5), -depth / 2, 0), col)
        k.rotate(s, slope, "X")
        items.append(s)
        items.append(flat((sw, 0.04, valance), (-w / 2 + sw * (i + 0.5), -run, -fall - valance + 0.02), col))

    for sx in (-1, 1):
        items.append(bar((sx * (w / 2 - 0.05), 0, -fall * 0.2), (sx * (w / 2 - 0.05), -run, -fall - 0.1), 0.02, "ny_iron", 4))

    return items


def finish(name, budget=None, fuse_soft=True):
    jp.FUSE_SEG = int(os.environ.get("SEG", "1"))
    if os.environ.get("PROF"):
        tot = {}

        for o in list(jp.parts) + list(jp.soft):
            o.data.calc_loop_triangles()
            tot[o.name.rstrip(".0123456789")] = tot.get(o.name.rstrip(".0123456789"), 0) + len(o.data.loop_triangles)

        print("PROF", len(jp.parts), len(jp.soft), sorted(tot.items(), key=lambda t: -t[1])[:8])

    jp.CENTER = False
    quads = [p for p in jp.parts if p.name.startswith("glassq")]
    jp.parts = [p for p in jp.parts if not p.name.startswith("glassq")]
    lo = min(v.co.z for p in jp.parts + jp.soft for v in p.data.vertices)
    ob = jp.finish(name, budget=budget, fuse_soft=fuse_soft)
    attach(ob, quads, -lo)
    gone = cull_enclosed(ob)

    if os.environ.get("PROF"):
        print("ENCLOSED", name, gone)

    return ob


def attach(ob, quads, dz):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    col = bm.loops.layers.float_color["Col"]

    for q in quads:
        attr = q.data.attributes["lpm_color"]

        for poly in q.data.polygons:
            vs = [bm.verts.new(q.data.vertices[i].co + Vector((0, 0, dz))) for i in poly.vertices]
            f = bm.faces.new(vs)
            f.smooth = False
            rgb = k._keyed(attr.data[poly.index].value)

            for l in f.loops:
                l[col] = (rgb[0], rgb[1], rgb[2], 1.0)

        bpy.data.objects.remove(q, do_unlink=True)

    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def _rays(n=26):
    out = [Vector((0, 0, 1))]
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n - 1):
        u = (i + 0.5) / (n - 1)
        z = 1 - u * 0.97
        r = math.sqrt(1 - z * z)
        a = i * golden
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))

    return out


RAYS = _rays()


def cull_enclosed(ob, near=0.3, far=400.0):
    from mathutils.bvhtree import BVHTree

    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    doomed = []

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()
        vs = [v.co for v in f.verts]
        pts = [c] + [v + (c - v).normalized() * 0.003 for v in vs] + [(a + b2) / 2 + (c - (a + b2) / 2).normalized() * 0.003 for a, b2 in zip(vs, vs[1:] + vs[:1])]
        hidden = True

        for p in pts:
            start = p + n * 0.002
            hit = tree.ray_cast(start, n, far)

            if hit[0] is None or hit[3] < near:
                hidden = False
                break

            for d in RAYS[1:]:
                w = t * d.x + b * d.y + n * d.z

                if tree.ray_cast(start, w, far)[0] is None:
                    hidden = False
                    break

            if not hidden:
                break

        if hidden:
            doomed.append(f)

    bmesh.ops.delete(bm, geom=doomed, context="FACES_ONLY")
    bm.to_mesh(me)
    bm.free()
    me.update()

    return len(doomed)


def export(ob, out_dir, name, roof=None):
    path = jp.export(ob, out_dir, name)
    side = {"solids": [[round(v, 3) for v in s] for s in SOLIDS]}

    if roof is not None:
        side["roof"] = roof

    with open(os.path.join(out_dir, name + ".json"), "w") as f:
        json.dump(side, f)

    return path
