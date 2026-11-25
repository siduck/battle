import sys, os, json, math, re
sys.path.insert(0, os.environ.get("BPYLIB", ""))
import bpy, bmesh
from mathutils import Matrix, Vector

P = os.environ.get("PF", "")
OUT = os.environ.get("OUT", "")
CELL = 0.5
PLINTH = (0.55, 0.44, 0.33)
SKIP = re.compile(r"smoke|cigar|wanted|poster|horse|mule|donkey|figure|person|people|man-|woman|human|worker|scientist|pilot|driver|crowd|spectator|player|chef|doctor|nurse|child|girl|dino|saur|raptor|dragon|animal|bird|gull|parrot|fish(?!ing)|octopus|crab|shark|whale|dolphin|cow-|sheep|goat|chicken|insect|butterfly|statue|skeleton|skull|church|chapel", re.I)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def bounds(bm):
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]

    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def normalize(bm, height=None, scale=None, rot=0.0):
    lo, hi = bounds(bm)
    k = scale if scale else height / max(hi.z - lo.z, 1e-4)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bm.transform(Matrix.Rotation(rot, 4, "Z") @ Matrix.Scale(k, 4) @ Matrix.Translation(-c))

    return bm


def add_box(bm, lo, hi, c):
    tmp = bmesh.new()
    col = tmp.loops.layers.float_color.new("Col")
    bmesh.ops.create_cube(tmp, size=1.0)

    for v in tmp.verts:
        v.co = Vector(tuple(lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)))

    for f in tmp.faces:
        for l in f.loops:
            l[col] = (c[0], c[1], c[2], 1.0)

    me = bpy.data.meshes.new("b")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def export(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("kit")
    mat.use_nodes = True

    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (1, 1, 1, 1)
            n.inputs["Roughness"].default_value = 1.0
    me.materials.append(mat)

    for ca in [c for c in me.color_attributes if c.name != "Col"]:
        me.color_attributes.remove(ca)

    me.color_attributes.active_color = me.color_attributes["Col"]
    me.color_attributes.render_color_index = 0

    for o in bpy.context.scene.objects:
        o.select_set(o == ob)

    bpy.context.view_layer.objects.active = ob
    kw = dict(filepath=os.path.join(OUT, name + ".glb"), export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=True)

    try:
        bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_colors=True, **kw)

    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)

    return {"file": os.environ.get("DIR", "kd") + "/" + name + ".glb", "min": [min(xs), min(zs), -max(ys)], "max": [max(xs), max(zs), -min(ys)], "tris": tris}


def footprint(bm, y0=0.35, y1=2.3):
    lo, hi = bounds(bm)
    nx = int(math.ceil((hi.x - lo.x) / CELL)) + 2
    ny = int(math.ceil((hi.y - lo.y) / CELL)) + 2
    ox = lo.x - CELL
    oy = lo.y - CELL
    grid = [[0] * ny for _ in range(nx)]

    def mark(p):
        i = int((p.x - ox) / CELL)
        j = int((p.y - oy) / CELL)

        if 0 <= i < nx and 0 <= j < ny:
            grid[i][j] = 1

    for f in bm.faces:
        vs = [v.co for v in f.verts]
        pts = []

        for a, b in zip(vs, vs[1:] + vs[:1]):
            for t in (y0, y1, (y0 + y1) / 2):
                if (a.z - t) * (b.z - t) < 0:
                    u = (t - a.z) / (b.z - a.z)
                    pts.append(a + (b - a) * u)

            if y0 <= a.z <= y1:
                pts.append(a.copy())

        if len(pts) < 1:
            continue

        for a in pts:
            for b in pts:
                d = (b - a).length
                n = max(1, int(d / (CELL * 0.4)))

                for s in range(n + 1):
                    mark(a + (b - a) * (s / n))

    seen = [[0] * ny for _ in range(nx)]
    stack = [(0, 0)]

    while stack:
        i, j = stack.pop()

        if not (0 <= i < nx and 0 <= j < ny) or seen[i][j] or grid[i][j]:
            continue

        seen[i][j] = 1
        stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]

    solid = [[1 if not seen[i][j] else 0 for j in range(ny)] for i in range(nx)]
    used = [[0] * ny for _ in range(nx)]
    boxes = []

    for i in range(nx):
        for j in range(ny):
            if not solid[i][j] or used[i][j]:
                continue

            w = 1

            while i + w < nx and solid[i + w][j] and not used[i + w][j]:
                w += 1

            h = 1

            while j + h < ny and all(solid[i + k][j + h] and not used[i + k][j + h] for k in range(w)):
                h += 1

            for a in range(w):
                for b in range(h):
                    used[i + a][j + b] = 1

            boxes.append((ox + i * CELL, oy + j * CELL, ox + (i + w) * CELL, oy + (j + h) * CELL))

    return boxes


def column_height(bm, box):
    best = 2.4

    for v in bm.verts:
        if box[0] - 0.1 <= v.co.x <= box[2] + 0.1 and box[1] - 0.1 <= v.co.y <= box[3] + 0.1:
            best = max(best, v.co.z)

    return best


def load(path, door_to=None):
    reset()
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()
    door = None

    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        if SKIP.search(o.name):
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

        for f, p in zip(tmp.faces, me.polygons):
            for l, li in zip(f.loops, p.loop_indices):
                c = src.data[li].color_srgb if src is not None else (0.8, 0.8, 0.8, 1)
                l[col] = (c[0], c[1], c[2], 1.0)

        if "door" in o.name and door is None:
            door = sum((v.co for v in tmp.verts), Vector()) / max(len(tmp.verts), 1)

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    if door_to is not None and door is not None:
        lo, hi = bounds(bm)
        c = (lo + hi) / 2
        ang = math.atan2(door.y - c.y, door.x - c.x)
        bm.transform(Matrix.Translation(c) @ Matrix.Rotation(door_to - ang, 4, "Z") @ Matrix.Translation(-c))

    return bm


def tint(bm, k):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            l[col] = (c[0] * k[0], c[1] * k[1], c[2] * k[2], 1.0)


def part(bm, src, at, rot=0.0):
    piece = load(os.path.join(P, src + ".glb"))
    lo, hi = bounds(piece)
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    piece.transform(Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Translation(-c))
    me = bpy.data.meshes.new("p")
    piece.to_mesh(me)
    piece.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)




def src_path(src):
    return src if os.path.isabs(src) else os.path.join(P, src + ".glb")


def make_building(name, parts, scale=1.0, plinth=PLINTH, door_to=None):
    if isinstance(parts, str):
        bm = load(src_path(parts), door_to=door_to)
    else:
        reset()
        bm = bmesh.new()
        bm.loops.layers.float_color.new("Col")

        for src, at, rot in parts:
            part(bm, src, at, rot)

    normalize(bm, scale=scale)
    boxes = footprint(bm)
    lo, hi = bounds(bm)
    blocks = []

    for b in boxes:
        h = column_height(bm, b)
        small = (b[2] - b[0]) * (b[3] - b[1]) < 1.2

        if plinth:
            add_box(bm, (b[0] + 0.02, b[1] + 0.02, -1.0), (b[2] - 0.02, b[3] - 0.02, 0.03), plinth)

        blocks.append([round(b[0], 3), round(-b[3], 3), round(b[2], 3), round(-b[1], 3), round(min(h, 3.2) if small else h, 3)])

    info = export(bm, name)
    info["blocks"] = blocks
    info["w"] = round(max(hi.x - lo.x, 1), 2)
    info["d"] = round(max(hi.y - lo.y, 1), 2)
    info["kind"] = "building"
    print("DONE", name, info["tris"], len(blocks))

    return info


def make_prop(name, src, scale=1.0, k=None, group="street", collide="box"):
    bm = load(src_path(src))

    if k:
        tint(bm, k)

    normalize(bm, scale=scale)
    info = export(bm, name)
    info["kind"] = "prop"
    info["group"] = group
    info["collide"] = collide
    print("DONE", name, info["tris"])

    return info


def zig_f(v):
    return "%.3f" % v


def emit_zig(map_name, infos, path):
    names = list(infos.keys())
    out = ["const api = @import(\"api.zig\");", "", "pub const K = enum {"]
    out += ["    %s," % n for n in names]
    out += ["};", "", "pub const kit = api.Kit(K);", "", "pub const table = [_]api.Info{"]

    for n in names:
        i = infos[n]
        group = i.get("group", "building")
        collide = "none" if i.get("kind") == "building" else i.get("collide", "box")
        mn = ", ".join(zig_f(v) for v in i["min"])
        mx = ", ".join(zig_f(v) for v in i["max"])
        out.append("    .{ .file = \"%s\", .scale = 1.00, .collide = .%s, .group = .%s, .foliage = false, .min = .{ %s }, .max = .{ %s } }," % (i["file"], collide, group, mn, mx))

    out += ["};", "", "pub const buildings = [_]api.Building{"]

    for n in names:
        i = infos[n]

        if i.get("kind") != "building":
            continue

        blocks = ", ".join(".{ %s }" % ", ".join(zig_f(v) for v in b) for b in i["blocks"])
        out.append("    .{ .kind = kit.of(.%s), .w = %s, .d = %s, .blocks = &.{ %s } }," % (n, zig_f(i["w"]), zig_f(i["d"]), blocks))

    out += ["};", ""]
    tris = sum(infos[n]["tris"] for n in names)
    print("TRIS", map_name, tris)

    with open(path, "w") as f:
        f.write("\n".join(out))


def run(map_name, buildings=(), props=()):
    root = os.environ.get("ROOT", os.getcwd())
    global OUT
    OUT = os.path.join(root, "src/client/assets/props", map_name)
    os.environ["DIR"] = map_name
    os.makedirs(OUT, exist_ok=True)
    infos = {}

    for entry in buildings:
        name, parts = entry[0], entry[1]
        opts = entry[2] if len(entry) > 2 else {}
        infos[name] = make_building(name, parts, **opts)

    for entry in props:
        name, src = entry[0], entry[1]
        opts = entry[2] if len(entry) > 2 else {}
        infos[name] = make_prop(name, src, **opts)

    emit_zig(map_name, infos, os.path.join(root, "src/shared/maps", map_name + "_kit.zig"))

    with open(os.path.join(root, "tools/blender/maps", map_name + ".json"), "w") as f:
        json.dump(infos, f, indent=1)
