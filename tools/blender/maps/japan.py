import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "japan")
from pf import *
from mathutils.bvhtree import BVHTree

EXTRA = os.path.join(P, "extra")


def hemisphere(n):
    dirs = []
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        u = (i + 0.5) / n
        r = math.sqrt(u)
        a = i * golden
        dirs.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(1 - u))))

    return dirs


RAYS = hemisphere(28)


GLASS = re.compile(r"glass|glazing|window|pane", re.I)


def glassy(c):
    lum = (c[0] + c[1] + c[2]) / 3

    return lum < 0.3 and c[2] > c[0] + 0.02


def sky_glass(co, lo, hi):
    h = max(hi.z - lo.z, 0.01)
    f = min(1.0, max(0.0, (co.z - lo.z) / h))
    s = 0.5 + 0.5 * math.sin(co.x * 0.35 + co.y * 0.35 + co.z * 0.12)
    a = 0.25 + 0.55 * f + 0.2 * s
    lo_c = (0.24, 0.33, 0.42)
    hi_c = (0.6, 0.72, 0.82)

    return tuple(lo_c[i] + (hi_c[i] - lo_c[i]) * a for i in range(3))


def load_skip(path, skip=None, glass=False):
    reset()
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()
    extra = re.compile(skip, re.I) if skip else None

    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        if SKIP.search(o.name) or (extra and extra.search(o.name)):
            continue

        me = o.data
        src = me.color_attributes[0] if len(me.color_attributes) else None
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)

        for layer in list(tmp.loops.layers.float_color):
            tmp.loops.layers.float_color.remove(layer)
        for layer in list(tmp.loops.layers.color):
            tmp.loops.layers.color.remove(layer)

        col = tmp.loops.layers.float_color.new("Col")
        tmp.faces.ensure_lookup_table()
        named = glass and GLASS.search(o.name)

        for f, p in zip(tmp.faces, me.polygons):
            for l, li in zip(f.loops, p.loop_indices):
                c = src.data[li].color_srgb if src is not None else (0.8, 0.8, 0.8, 1)
                l[col] = (c[0], c[1], c[2], 1.0)

        if glass:
            tmp.normal_update()
            glo, ghi = bounds(tmp)

            for f in tmp.faces:
                if abs(f.normal.z) > 0.7:
                    continue

                if named or all(glassy(l[col]) for l in f.loops):
                    for l in f.loops:
                        g = sky_glass(l.vert.co, glo, ghi)
                        l[col] = (g[0], g[1], g[2], 1.0)

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    return bm


def split_long(bm, limit):
    for _ in range(3):
        long = [e for e in bm.edges if e.calc_length() > limit]

        if not long:
            return

        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])


def ao(bm, dist, strength, ground=True, floor=0.0, sky=0.0):
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    lo, hi = bounds(bm)
    height = max(hi.z - lo.z, 0.01)
    cache = {}

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()

        for l in f.loops:
            key = (l.vert.index, round(n.x, 2), round(n.y, 2), round(n.z, 2))
            k = cache.get(key)

            if k is None:
                sides = []

                for sn in (1, -1):
                    p = l.vert.co + (c - l.vert.co) * 0.04 + n * (0.02 * sn)
                    o = 0.0

                    for d in RAYS:
                        w = t * d.x + b * d.y + n * (d.z * sn)
                        hit = tree.ray_cast(p, w, dist)

                        if hit[0] is not None:
                            o += 1 - hit[3] / dist
                        elif ground and w.z < -0.02:
                            tt = (floor - p.z) / w.z

                            if 0 < tt < dist:
                                o += 1 - tt / dist

                    sides.append(o)

                occ = min(sides)

                k = 1 - strength * min(1.0, occ / len(RAYS) * 1.6)

                if sky:
                    k *= 1 - sky + sky * min(1.0, max(0.0, (l.vert.co.z - lo.z) / height))

                cache[key] = k

            cc = l[col]
            l[col] = (cc[0] * k, cc[1] * k, cc[2] * k, 1.0)


def grade(bm, sat=1.0, k=(1, 1, 1), lift=0.0):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            g = (c[0] + c[1] + c[2]) / 3
            r = [min(1.0, max(0.0, (g + (c[i] - g) * sat) * k[i] + lift)) for i in range(3)]
            l[col] = (r[0], r[1], r[2], 1.0)


def shell(bm, y0, y1, cell):
    lo, hi = bounds(bm)
    nx = int(math.ceil((hi.x - lo.x) / cell)) + 2
    ny = int(math.ceil((hi.y - lo.y) / cell)) + 2
    ox = lo.x - cell
    oy = lo.y - cell
    grid = [[0] * ny for _ in range(nx)]

    def mark(px, py):
        i = int((px - ox) / cell)
        j = int((py - oy) / cell)

        if 0 <= i < nx and 0 <= j < ny:
            grid[i][j] = 1

    for f in bm.faces:
        vs = [v.co for v in f.verts]

        if max(v.z for v in vs) < y0 or min(v.z for v in vs) > y1:
            continue

        pts = []

        for a, b in zip(vs, vs[1:] + vs[:1]):
            for tt in (y0, y1):
                if (a.z - tt) * (b.z - tt) < 0:
                    u = (tt - a.z) / (b.z - a.z)
                    pts.append(a + (b - a) * u)

            if y0 <= a.z <= y1:
                pts.append(a.copy())

        if not pts:
            continue

        for a in pts:
            for b in pts:
                d = (b - a).length
                n = max(1, int(d / (cell * 0.4)))

                for st in range(n + 1):
                    q = a + (b - a) * (st / n)
                    mark(q.x, q.y)

        if len(pts) >= 3 and abs(f.normal.z) > 0.3:
            cx = sum(q.x for q in pts) / len(pts)
            cy = sum(q.y for q in pts) / len(pts)
            ring = sorted(pts, key=lambda q: math.atan2(q.y - cy, q.x - cx))
            i = int((min(q.x for q in ring) - ox) / cell)
            x1 = max(q.x for q in ring)
            jy0 = int((min(q.y for q in ring) - oy) / cell)
            y1r = max(q.y for q in ring)

            while ox + i * cell < x1:
                j = jy0

                while oy + j * cell < y1r:
                    px = ox + (i + 0.5) * cell
                    py = oy + (j + 0.5) * cell
                    inside = True

                    for a, b in zip(ring, ring[1:] + ring[:1]):
                        if (b.x - a.x) * (py - a.y) - (b.y - a.y) * (px - a.x) < -1e-6:
                            inside = False

                            break

                    if inside:
                        mark(px, py)

                    j += 1

                i += 1

    used = [[0] * ny for _ in range(nx)]
    boxes = []

    for i in range(nx):
        for j in range(ny):
            if not grid[i][j] or used[i][j]:
                continue

            w = 1

            while i + w < nx and grid[i + w][j] and not used[i + w][j]:
                w += 1

            h = 1

            while j + h < ny and all(grid[i + kk][j + h] and not used[i + kk][j + h] for kk in range(w)):
                h += 1

            for a in range(w):
                for b in range(h):
                    used[i + a][j + b] = 1

            boxes.append((ox + i * cell, oy + j * cell, ox + (i + w) * cell, oy + (j + h) * cell))

    return boxes


def solids(bm, dy=1.0, start=0.25, cell=0.5, min_area=0.0, fill=True):
    import pf as pfm
    pfm.CELL = cell
    lo, hi = bounds(bm)
    runs = {}
    out = []
    y = start
    prev = set()

    while y < hi.z - 0.05:
        y1 = min(y + dy, hi.z)
        rects = set()

        for r in (footprint(bm, y, y1) if fill else shell(bm, y, y1, cell)):
            if (r[2] - r[0]) * (r[3] - r[1]) < min_area:
                continue

            rects.add(tuple(round(v, 3) for v in r))

        for r in prev - rects:
            out.append(runs.pop(r))

        for r in rects:
            if r in runs:
                runs[r][5] = y1
            else:
                runs[r] = [r[0], -r[3], r[2], -r[1], y if y > start else -0.5, y1]

        prev = rects
        y = y1

    out += runs.values()
    pfm.CELL = 0.5

    return [[round(v, 3) for v in s] for s in out]


def finish(bm, name, info_extra):
    info = export(bm, name)
    info.update(info_extra)
    print("DONE", name, info["tris"], len(info.get("solids", [])))

    return info


def build(name, src, skip=None, scale=1.0, k=None, dist=4.0, strength=0.55, split=0.0, dy=1.0, voxel=True, sky=0.18, sat=1.0, cell=0.5, min_area=0.0, spin=0.0, fill=True, glass=True):
    bm = load_skip(src_path(src), skip, glass)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale, rot=spin)

    if split:
        split_long(bm, split)

    grade(bm, sat=sat)
    ao(bm, dist, strength, sky=sky)
    extra = {"kind": "prop", "group": "building", "collide": "none"}

    if voxel:
        extra["solids"] = solids(bm, dy=dy, min_area=min_area, cell=cell, fill=fill)

    return finish(bm, name, extra)


def prop(name, src, scale=1.0, k=None, group="street", collide="box", dist=1.5, strength=0.5, skip=None, sat=1.0, spin=0.0, sky=0.12, glass=False):
    bm = load_skip(src_path(src), skip, glass)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale, rot=spin)
    grade(bm, sat=sat)
    ao(bm, dist, strength, sky=sky)

    return finish(bm, name, {"kind": "prop", "group": group, "collide": collide})


def emit(map_name, infos, path):
    names = list(infos.keys())
    out = ["const api = @import(\"api.zig\");", "", "pub const K = enum {"]
    out += ["    %s," % n for n in names]
    out += ["};", "", "pub const kit = api.Kit(K);", "", "pub const table = [_]api.Info{"]

    for n in names:
        i = infos[n]
        mn = ", ".join(zig_f(v) for v in i["min"])
        mx = ", ".join(zig_f(v) for v in i["max"])
        out.append("    .{ .file = \"%s\", .scale = 1.00, .collide = .%s, .group = .%s, .foliage = false, .min = .{ %s }, .max = .{ %s } }," % (i["file"], i["collide"], i["group"], mn, mx))

    out += ["};", "", "pub const solids = [_][]const [6]f32{"]

    for n in names:
        s = infos[n].get("solids", [])
        out.append("    &.{ %s }," % ", ".join(".{ %s }" % ", ".join(zig_f(v) for v in b) for b in s))

    out += ["};", ""]
    tris = sum(infos[n]["tris"] for n in names)
    print("TRIS", map_name, tris, "KINDS", len(names), "SOLIDS", sum(len(infos[n].get("solids", [])) for n in names))

    with open(path, "w") as f:
        f.write("\n".join(out))


def ex(name):
    return os.path.join(EXTRA, name + ".glb")


def assemble(name, parts, dist=5.0, strength=0.55, split=4.0, dy=1.5, cell=0.5, sky=0.18):
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    for src, at, rot in parts:
        piece = load_skip(src_path(src), None, True)
        lo, hi = bounds(piece)
        c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        piece.transform(Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Translation(-c))
        me = bpy.data.meshes.new("p")
        piece.to_mesh(me)
        piece.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    normalize(bm, scale=1.0)

    if split:
        split_long(bm, split)

    ao(bm, dist, strength, sky=sky)

    return finish(bm, name, {"kind": "prop", "group": "building", "collide": "none", "solids": solids(bm, dy=dy, cell=cell)})


def main():
    root = os.environ.get("ROOT", os.getcwd())
    global OUT
    OUT = os.path.join(root, "src/client/assets/props/japan")
    import pf
    pf.OUT = OUT
    os.makedirs(OUT, exist_ok=True)

    for f in os.listdir(OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(OUT, f))

    only = os.environ.get("ONLY")
    infos = {}
    apt = "apartment-block-6445af"
    roof = "tiled-roof-section-6f1121"
    jobs = [
        ("parlour", lambda: build("parlour", "amusement-parlour-7eb45f", dist=4, split=3)),
        ("apartment", lambda: build("apartment", apt, dist=4, split=3)),
        ("tower", lambda: assemble("tower", [(apt, (0, 0, 0), 0), (apt, (0, 0, 9.4), 0)])),
        ("bath", lambda: build("bath", "bathhouse-4ac41a", dist=4, split=3)),
        ("barhut", lambda: build("barhut", "alley-bar-hut-3e41f8", dist=3, split=2)),
        ("konbini", lambda: build("konbini", "convenience-store-c30e1d", dist=3, split=2)),
        ("corner", lambda: build("corner", "corner-shophouse-ad15c2", dist=3, split=3)),
        ("shop3", lambda: build("shop3", "three-storey-shophouse-2f6378", dist=3, split=3)),
        ("shop2", lambda: build("shop2", "two-storey-shophouse-183790", dist=3, split=3)),
        ("wide", lambda: build("wide", "wide-shophouse-089f20", dist=3, split=3)),
        ("roof", lambda: build("roof", roof, dist=2, split=2, voxel=False)),
        ("ac", lambda: prop("ac", "air-con-unit-9fadc2")),
        ("crate", lambda: prop("crate", "beverage-crate-c195c9", collide="none")),
        ("bikerack", lambda: prop("bikerack", "bicycle-parking-rack-282058", collide="none")),
        ("cherry", lambda: prop("cherry", "cherry-blossom-tree-3f7ab7", group="tree", collide="trunk", dist=3, sky=0.3, scale=1.35)),
        ("bike", lambda: prop("bike", "city-bicycle-5b67d1", collide="none")),
        ("taxi", lambda: prop("taxi", "city-taxi-eefa91", group="car")),
        ("tram", lambda: prop("tram", "city-tram-0d092d", group="car", dist=2.5)),
        ("blockwall", lambda: prop("blockwall", "concrete-block-wall-02c715")),
        ("mirror", lambda: prop("mirror", "convex-traffic-mirror-a64d15", collide="cylinder")),
        ("moped", lambda: prop("moped", "delivery-moped-1aa2ce", collide="none")),
        ("awning", lambda: prop("awning", "fabric-awning-4d6acc", collide="none")),
        ("planter", lambda: prop("planter", "flower-planter-550bfb")),
        ("rock", lambda: prop("rock", "garden-rock-2d3b51", group="rock")),
        ("guardrail", lambda: prop("guardrail", "guardrail-section-68c3c4")),
        ("keivan", lambda: prop("keivan", "kei-van-211ed5", group="car")),
        ("meter", lambda: prop("meter", "meter-box-1e6e42", collide="none")),
        ("noren", lambda: prop("noren", "noren-curtain-7b9e53", collide="none")),
        ("lantern", lambda: prop("lantern", "paper-lantern-3387e9", collide="none")),
        ("drum", lambda: prop("drum", "plastic-drum-da992f", collide="cylinder")),
        ("potted", lambda: prop("potted", "potted-shrub-43bd21", collide="cylinder")),
        ("ramen", lambda: prop("ramen", "ramen-yatai-stall-53974b")),
        ("postbox", lambda: prop("postbox", "red-post-box-f12045", collide="cylinder")),
        ("shutter", lambda: prop("shutter", "roller-shutter-c58b4f", collide="none")),
        ("board", lambda: prop("board", "sandwich-board-sign-cb5e7c", collide="none")),
        ("stonefence", lambda: prop("stonefence", "stone-fence-panel-56d138")),
        ("bin", lambda: prop("bin", "street-bin-770173", collide="cylinder")),
        ("lamp", lambda: prop("lamp", "street-lamp-29f365", collide="cylinder")),
        ("cone", lambda: prop("cone", "traffic-cone-247748", collide="none")),
        ("signal", lambda: prop("signal", "traffic-signal-2a517e", collide="cylinder")),
        ("pole", lambda: prop("pole", "utility-pole-574130", collide="cylinder", dist=1.0, strength=0.3)),
        ("vending", lambda: prop("vending", "vending-machine-471c29")),
        ("kanji", lambda: prop("kanji", "vertical-kanji-signboard-cc5162", collide="none")),
        ("bench", lambda: prop("bench", "wooden-bench-661da4")),
        ("track", lambda: prop("track", "tram-track-tile-f3c69a", group="road", collide="none", dist=0.5, strength=0.2)),
        ("tree", lambda: prop("tree", ex("broad-canopy-shade-tree-e7c4a2"), group="tree", collide="trunk", dist=3, strength=0.55, sky=0.3, scale=0.9)),
        ("maple", lambda: prop("maple", ex("maple-tree-65fa12"), group="tree", collide="trunk", dist=3, sky=0.3)),
        ("bush", lambda: prop("bush", ex("round-bush-cd2ac0"), group="bush", collide="none", sky=0.3)),
        ("hatch", lambda: prop("hatch", ex("compact-hatchback-386417"), group="car")),
        ("wheelie", lambda: prop("wheelie", ex("roll-out-wheelie-bin-3b540e"))),
    ]

    for name, fn in jobs:
        if only and name not in only.split(","):
            continue

        infos[name] = fn()

    emit("japan", infos, os.path.join(root, "src/shared/maps/japan_kit.zig"))


main()


