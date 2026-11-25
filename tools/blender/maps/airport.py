import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "airport")
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


def main():
    root = os.environ.get("ROOT", os.getcwd())
    global OUT
    OUT = os.path.join(root, "src/client/assets/props/airport")
    import pf
    pf.OUT = OUT
    os.makedirs(OUT, exist_ok=True)

    for f in os.listdir(OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(OUT, f))

    only = os.environ.get("ONLY")
    infos = {}
    jobs = [
        ("hangar", lambda: build("hangar", "maintenance-hangar-6fab99", skip=r"door-leaf", dist=10, strength=0.6, split=6, dy=1.5)),
        ("cargo", lambda: build("cargo", "cargo-shed-bcb2a8", dist=6, split=5, dy=1.5)),
        ("fire", lambda: build("fire", "airport-fire-station-92c6b7", dist=6, split=5, dy=1.5)),
        ("tower", lambda: build("tower", "control-tower-c95a65", dist=6, split=5, dy=2.0)),
        ("hotel", lambda: build("hotel", "airport-hotel-1a1e0a", dist=6, split=6, dy=3.0)),
        ("carpark", lambda: build("carpark", "multi-storey-car-park-021465", dist=5, split=5, dy=0.25, strength=0.6, fill=False)),
        ("tank", lambda: build("tank", "fuel-farm-tank-ed67f0", dist=5, split=4, dy=4.0, cell=1.0)),
        ("gatehouse", lambda: build("gatehouse", "security-gatehouse-fd00c8", dist=3, split=3)),
        ("lounge", lambda: build("lounge", "gate-lounge-module-5ebc23", dist=4, split=4, dy=0.25, fill=False)),
        ("facade", lambda: build("facade", "terminal-facade-module-5574b6", dist=3, split=3, dy=0.5, fill=False)),
        ("canopy", lambda: build("canopy", "departures-kerb-canopy-run-d1ed9e", dist=3, split=3, dy=0.5, fill=False, min_area=0.1)),
        ("bridge", lambda: build("bridge", "jet-bridge-4f39c0", dist=3, split=4, dy=1.5, cell=0.75, min_area=0.3)),
        ("radar", lambda: build("radar", "air-traffic-radar-mast-3e5642", dist=4, dy=3.0, cell=1.0)),
        ("vor", lambda: build("vor", "vor-navigation-beacon-9b32ff", dist=3, split=3, dy=2.0, cell=1.0)),
        ("flood", lambda: build("flood", "apron-floodlight-mast-e0d04a", dist=2, dy=2.0)),
        ("localizer", lambda: build("localizer", "ils-localizer-antenna-array-f094b7", dist=2, dy=1.5, cell=1.0)),
        ("deflector", lambda: build("deflector", "jet-blast-deflector-run-393c60", dist=2.5, split=2)),
        ("uld", lambda: prop("uld", "uld-container-a055c6")),
        ("chock", lambda: prop("chock", "wheel-chock-9b0894", collide="none")),
        ("cone", lambda: prop("cone", ex("site-traffic-cone-d3ce94"), collide="none", scale=1.0)),
        ("trolley", lambda: prop("trolley", "passenger-luggage-trolley-2e11d7", collide="none")),
        ("bollards", lambda: prop("bollards", "drop-off-bollard-run-228eeb")),
        ("twysign", lambda: prop("twysign", "lit-taxiway-sign-206955")),
        ("edge", lambda: prop("edge", "runway-edge-light-run-ebe7e1", collide="none", scale=1.4)),
        ("windsock", lambda: prop("windsock", "windsock-d5df79", collide="cylinder")),
        ("barrier", lambda: prop("barrier", "lifting-barrier-arm-64a343")),
        ("fence", lambda: prop("fence", ex("chain-link-fence-run-6c3d68"), scale=1.25)),
        ("crashbar", lambda: prop("crashbar", ex("crash-barrier-run-b47d1d"))),
        ("tree", lambda: prop("tree", ex("broad-canopy-shade-tree-e7c4a2"), group="tree", collide="trunk", dist=3, strength=0.55, sky=0.3)),
        ("pine", lambda: prop("pine", ex("tall-pine-tree-ab4108"), group="tree", collide="trunk", dist=3, strength=0.5, sky=0.35)),
        ("shrub", lambda: prop("shrub", ex("columnar-evergreen-shrub-35a00b"), group="bush", collide="cylinder", sky=0.3)),
        ("hedge", lambda: prop("hedge", ex("clipped-boundary-hedge-run-c9027b"), group="bush", sky=0.3)),
        ("lamp", lambda: prop("lamp", ex("cobra-head-street-light-3e25b8"), collide="cylinder")),
        ("checkin", lambda: prop("checkin", "check-in-desk-run-b96c12")),
        ("seats", lambda: prop("seats", "gate-seating-row-cc0ff3")),
        ("kiosk", lambda: prop("kiosk", "self-check-in-kiosk-3fe1c1")),
        ("arch", lambda: prop("arch", "walk-through-security-arch-5c2a43", collide="none")),
        ("depboard", lambda: prop("depboard", "departures-board-7b85c8")),
    ]

    for name, fn in jobs:
        if only and name not in only.split(","):
            continue

        infos[name] = fn()

    emit("airport", infos, os.path.join(root, "src/shared/maps/airport_kit.zig"))


main()
