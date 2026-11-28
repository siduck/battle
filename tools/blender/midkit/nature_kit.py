import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "suburb"))
sys.path.insert(0, os.path.join(HERE, "..", "kit"))

import bmesh
import bpy
import dfkit as k
import jp
from mathutils import Matrix, Vector

N = jp.N
FLAT = set()


def register(entries, flat=()):
    for name, hexs in entries:
        if name not in k._INDEX:
            k.PALETTE.append((name, hexs))
            k._INDEX[name] = len(k.PALETTE) - 1

    FLAT.update(flat)


def setup(seed=3, key="#cdc6a8", amount=0.1, accents=(), accent_amount=0.05):
    jp.setup(seed)
    k.harmonize(key, amount, accents=accents, accent_amount=accent_amount)


def add(items):
    return jp.add(items)


def hash01(*vals):
    h = 2166136261

    for v in vals:
        h = ((h ^ int(round(v * 997))) * 16777619) & 0xFFFFFFFF

    return ((h >> 8) & 0xFFFF) / 65535.0


def idx(color):
    return color if isinstance(color, int) else k.c(color)


def object_from(name, bm, colors):
    ob = k.lpm._object(name, bm, idx(colors) if not callable(colors) else 0)

    if callable(colors):
        attr = ob.data.attributes["lpm_color"]

        for p in ob.data.polygons:
            attr.data[p.index].value = idx(colors(p))

    return ob


def tube(name, pts, radii, sides=8, colors="fo_bark", cap_top=True, cap_bottom=False, squash=(1.0, 1.0), jit=0.0, seed=0, twist=0.0):
    pts = [Vector(p) for p in pts]
    r = random.Random(seed)
    bm = bmesh.new()
    rings = []
    count = len(pts)
    names = []

    for j, p in enumerate(pts):
        t = (pts[min(j + 1, count - 1)] - pts[max(j - 1, 0)]).normalized()
        a = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
        u = t.cross(a).normalized()
        v = t.cross(u).normalized()
        ring = []

        for i in range(sides):
            ang = 2 * math.pi * i / sides + twist * j
            rr = radii[j] * (1 + jit * (r.random() - 0.5))
            ring.append(bm.verts.new(p + u * (math.cos(ang) * rr * squash[0]) + v * (math.sin(ang) * rr * squash[1])))

        rings.append(ring)

    def col(i, j):
        if callable(colors):
            return colors(i, j)

        if isinstance(colors, (list, tuple)):
            return colors[(i + j * 2) % len(colors)]

        return colors

    for j in range(count - 1):
        for i in range(sides):
            i2 = (i + 1) % sides

            try:
                bm.faces.new((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]))
                names.append(col(i, j))
            except ValueError:
                pass

    if cap_bottom:
        bm.faces.new(rings[0])
        names.append(col(0, 0) if not isinstance(cap_bottom, str) else cap_bottom)

    if cap_top:
        bm.faces.new(list(reversed(rings[-1])))
        names.append(cap_top if isinstance(cap_top, str) else col(0, count - 2))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = k.lpm._object(name, bm, 0)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        attr.data[p.index].value = idx(names[p.index])

    return ob


def refine(pts, radii, per):
    out = []
    rr = []

    for i in range(len(pts) - 1):
        a = Vector(pts[i])
        b = Vector(pts[i + 1])

        for s in range(per):
            t = s / per
            out.append(tuple(a + (b - a) * t))
            rr.append(radii[i] + (radii[i + 1] - radii[i]) * t)

    out.append(tuple(pts[-1]))
    rr.append(radii[-1])

    return out, rr


def bar(a, b, r, color="fo_wood", sides=6, taper=1.0, cap=True, squash=(1.0, 1.0)):
    a = Vector(a)
    b = Vector(b)

    return tube("bar", [a, b], [r, r * taper], sides, color, cap_top=cap, cap_bottom=cap, squash=squash)


def bevel_edges(ob, width, segments=1, angle=28.0):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle)]

    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    return ob


def bevbox(size, at, color="fo_wood", bevel=0.02, taper=(1.0, 1.0), segments=1):
    b = k.box("b", size, at, idx(color), taper)

    if bevel > 0 and min(size) >= 0.12 and not jp.FAR:
        bevel_edges(b, min(bevel, min(size) * 0.3), segments)

    return b


def slab(size, at, color="fo_wood", bevel=0.012):
    return bevbox(size, at, color, bevel)


def plain(size, at, color="fo_wood"):
    return k.box("f", size, at, idx(color))


def tone_by_normal(light, mid, dark, sun=(0.5, -0.5), top=0.5, low=-0.35, mix=0.14, seed=0, accent=None, accent_p=0.0):
    def painter(p):
        n = p.normal
        c = p.center
        h = hash01(c.x, c.y, c.z, seed)
        side = n.x * sun[0] + n.y * sun[1]

        if accent and h < accent_p and n.z > -0.1:
            return accent

        if n.z > top or (n.z > 0.05 and side > 0.22):
            base = 0
        elif n.z > low:
            base = 1
        else:
            base = 2

        if h > 1 - mix and base < 2:
            base += 1
        elif h < mix * 0.6 and base > 0 and not (accent and h < accent_p):
            base -= 1

        return (light, mid, dark)[base]

    return painter


def blob(at, size, tones, sub=1, jitter=0.12, seed=0, flat_bottom=0.0, squash=1.0, accent=None, accent_p=0.0, mix=0.14, top=0.5):
    r = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=max(1, sub), radius=1.0)

    for v in bm.verts:
        n = v.co.normalized()
        f = 1.0 + r.uniform(-jitter, jitter)
        z = n.z * size[2] * f

        if flat_bottom and z < -flat_bottom * size[2]:
            z = -flat_bottom * size[2]

        v.co = Vector((n.x * size[0] * f, n.y * size[1] * f * squash, z))

    bm.transform(Matrix.Translation(Vector(at)))

    return object_from("blob", bm, tone_by_normal(*tones, seed=seed, accent=accent, accent_p=accent_p, mix=mix, top=top))


def chips(at, size, n, tones, seed, length=0.3, spread=0.8):
    r = random.Random(seed)
    bm = bmesh.new()
    names = []

    for _ in range(n):
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 0.8)))
        d.normalize()

        if d.z < -0.25:
            d.z = -d.z

        p = Vector((d.x * size[0], d.y * size[1], d.z * size[2])) * spread
        t = d.cross(Vector((0, 0, 1)))

        if t.length < 0.1:
            t = Vector((1, 0, 0))

        t.normalize()
        s = d.cross(t)
        w = length * r.uniform(0.5, 0.8)
        a = p + t * w
        b = p - t * w * 0.5 + s * w * 0.8
        c = p - t * w * 0.5 - s * w * 0.8
        tip = p + d * length * r.uniform(0.8, 1.3)
        va, vb, vc, vt = (bm.verts.new(x + Vector(at)) for x in (a, b, c, tip))

        for tri in ((va, vb, vt), (vb, vc, vt), (vc, va, vt)):
            bm.faces.new(tri)
            names.append(tones[0] if d.z > 0.3 else tones[1])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = k.lpm._object("chips", bm, 0)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        attr.data[p.index].value = idx(names[p.index])

    return ob


def tier(at, radius, height, sides=8, ragged=0.22, drop=0.14, colors=("fo_pine", "fo_pine_hi", "fo_pine_dk"), seed=0, mid_r=0.5, mid_z=0.42, lift=0.0):
    r = random.Random(seed)
    bm = bmesh.new()
    x, y, z = at
    rim = []
    mid = []
    count = sides * 2

    for i in range(count):
        a = 2 * math.pi * i / count + r.uniform(-0.06, 0.06)
        outer = i % 2 == 0
        rr = radius * (1.0 if outer else 1.0 - ragged) * r.uniform(0.92, 1.05)
        zz = z - (height * drop if outer else 0) + r.uniform(-0.02, 0.02) * height
        rim.append(bm.verts.new((x + rr * math.cos(a), y + rr * math.sin(a), zz)))
        mr = radius * mid_r * r.uniform(0.9, 1.1)
        mid.append(bm.verts.new((x + mr * math.cos(a + 0.02), y + mr * math.sin(a + 0.02), z + height * mid_z + (height * 0.06 if outer else 0))))

    apex = bm.verts.new((x, y, z + height))
    under = bm.verts.new((x, y, z + height * (0.1 + lift)))
    names = []

    for i in range(count):
        i2 = (i + 1) % count
        bm.faces.new((rim[i], rim[i2], mid[i2], mid[i]))
        names.append(colors[0] if i % 2 else colors[1])
        bm.faces.new((mid[i], mid[i2], apex))
        names.append(colors[1] if (i // 2) % 2 else colors[0])
        bm.faces.new((rim[i2], rim[i], under))
        names.append(colors[2])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = k.lpm._object("tier", bm, 0)
    attr = ob.data.attributes["lpm_color"]

    for p in ob.data.polygons:
        attr.data[p.index].value = idx(names[p.index])

    return ob


def hull(at, size, npts=14, seed=0, bevel=0.05, segments=2, painter=None, base_cut=0.3, irregular=0.18, strata=0.0, rot=0.0, taper=0.0):
    r = random.Random(seed)
    bm = bmesh.new()
    pts = []

    for _ in range(npts):
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1)))
        d.normalize()
        f = 1 + r.uniform(-irregular, irregular)
        p = Vector((d.x * size[0] / 2 * f, d.y * size[1] / 2 * f, d.z * size[2] / 2 * f))

        if p.z < -size[2] * base_cut / 2:
            p.z = -size[2] * base_cut / 2

        if strata:
            p.z = round(p.z / strata) * strata

        if taper:
            k_ = 1 - taper * (p.z / size[2] + 0.5)
            p.x *= k_
            p.y *= k_

        pts.append(p)

    for p in pts:
        bm.verts.new(p)

    res = bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)

    for v in list(bm.verts):
        if not v.link_faces:
            bm.verts.remove(v)

    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))

    sx = size[0] / max(hi.x - lo.x, 1e-4)
    sy = size[1] / max(hi.y - lo.y, 1e-4)
    sz = size[2] / max(hi.z - lo.z, 1e-4)
    mid = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bm.transform(Matrix.Translation(-mid))
    bm.transform(Matrix.Diagonal((sx, sy, sz, 1.0)))
    bm.transform(Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot, 4, "Z"))
    ob = object_from("hull", bm, painter or "fo_stone")

    if bevel > 0:
        bevel_edges(ob, bevel, segments, 20.0)

        if painter:
            attr = ob.data.attributes["lpm_color"]

            for p in ob.data.polygons:
                attr.data[p.index].value = idx(painter(p))

    return ob


def blades(at, n, radius, height, color, seed=0, lean=0.35, width=0.05, tip="fo_grass_tip", sides=3, curve=0.35, hmin=0.55, tiles=None):
    r = random.Random(seed)
    parts = []

    for i in range(n):
        a = r.uniform(0, 2 * math.pi)
        d = radius * math.sqrt(r.random())
        bx = at[0] + math.cos(a) * d
        by = at[1] + math.sin(a) * d
        h = height * r.uniform(hmin, 1.0)
        la = a + r.uniform(-0.5, 0.5)
        lx = math.cos(la) * lean * h * r.uniform(0.4, 1.0)
        ly = math.sin(la) * lean * h * r.uniform(0.4, 1.0)
        w = width * r.uniform(0.8, 1.2)
        c = color if not tiles else tiles[i % len(tiles)]
        pts = [(bx, by, at[2]), (bx + lx * 0.35, by + ly * 0.35, at[2] + h * 0.5), (bx + lx, by + ly, at[2] + h)]
        parts.append(tube("blade", pts, [w, w * 0.65, w * 0.05], sides, [c, c, tip], cap_top=False))

    return parts


def finish(name, budget=None, cull=True, speckle=0.05, flat=True, gradient=(0.93, 1.04), grime=(0.5, 0.86), seed=1):
    ob = k.finish(name, jp.parts, budget=budget)
    me = ob.data
    col = me.color_attributes["Col"]

    if flat and FLAT:
        keyed = {tuple(round(c, 3) for c in k._keyed(k.c(n))) for n in FLAT}

        for p in me.polygons:
            c = col.data[p.loop_indices[0]].color

            if tuple(round(x, 3) for x in c[:3]) in keyed:
                p.use_smooth = False

    if cull:
        k.cull_hidden(ob)

    me = ob.data
    col = me.color_attributes["Col"]

    if speckle:
        for p in me.polygons:
            ctr = p.center
            f = 1 + (hash01(ctr.x, ctr.y, ctr.z, seed) - 0.5) * 2 * speckle

            for li in p.loop_indices:
                c = col.data[li].color
                col.data[li].color = (min(c[0] * f, 1), min(c[1] * f, 1), min(c[2] * f, 1), 1.0)

    if gradient:
        k.height_gradient(ob, gradient[0], gradient[1])

    if grime:
        k.grime(ob, grime[0], grime[1])

    ob.data.calc_loop_triangles()
    ob["tris"] = len(ob.data.loop_triangles)

    return ob
