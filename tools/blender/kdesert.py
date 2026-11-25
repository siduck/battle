import sys, os, json, math, colorsys, random
sys.path.insert(0, os.environ.get("BPYLIB", ""))
import bpy, bmesh
from mathutils import Matrix, Vector

KITS = os.environ["KITS"]
OUT = os.environ["OUT"]
S = 4.6
STOREY = 0.625 * S

MB = os.path.join(KITS, "modular-buildings/Models/GLB format")
FT = os.path.join(KITS, "fantasy-town-kit/Models/GLB format")
PI = os.path.join(KITS, "pirate-kit/Models/GLB format")
SV = os.path.join(KITS, "survival-kit/Models/GLB format")
NA = os.path.join(KITS, "nature-kit/Models/GLTF format")

WALLS = [(0.94, 0.90, 0.81), (0.92, 0.80, 0.60), (0.90, 0.74, 0.64), (0.82, 0.58, 0.44), (0.80, 0.86, 0.86), (0.95, 0.86, 0.70)]
ACCENTS = [(0.67, 0.28, 0.20), (0.18, 0.46, 0.45), (0.78, 0.58, 0.25), (0.24, 0.40, 0.57), (0.60, 0.36, 0.42)]
TRIM = (0.55, 0.38, 0.26)
WOOD = (0.47, 0.32, 0.22)
DARK = (0.27, 0.21, 0.18)
GLASS = (0.17, 0.24, 0.26)
STONE = (0.74, 0.64, 0.50)
STONE_D = (0.56, 0.46, 0.37)
ROCK = (0.62, 0.47, 0.36)
ROCK_D = (0.47, 0.35, 0.28)
LEAF = (0.42, 0.52, 0.26)
LEAF_D = (0.30, 0.40, 0.20)
CLOTH = (0.88, 0.82, 0.70)

rng = random.Random(7)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hsv(c):
    return colorsys.rgb_to_hsv(*c)


def family(c):
    h, s, v = hsv(c)

    if s < 0.12:
        if v > 0.86:
            return "white"
        if v > 0.45:
            return "grey"
        if v > 0.2:
            return "grey_d"
        return "dark"
    if 0.5 <= h < 0.72:
        return "blue"
    if 0.72 <= h < 0.95:
        return "purple"
    if h >= 0.95 or h < 0.03:
        return "red"
    if 0.2 <= h < 0.5:
        return "green"
    if 0.12 <= h < 0.2:
        return "yellow"
    if v > 0.82 and s < 0.4:
        return "cream"
    if s > 0.55 and v > 0.8:
        return "orange"
    if v > 0.6:
        return "tan"
    return "brown"


DEFAULTS = {"white": CLOTH, "grey": STONE, "grey_d": STONE_D, "dark": DARK, "blue": GLASS, "purple": ACCENTS[4], "red": ACCENTS[0], "green": LEAF, "yellow": ACCENTS[2], "cream": WALLS[0], "orange": ACCENTS[2], "tan": TRIM, "brown": WOOD}


def remap(c, style):
    f = family(c)

    return style.get(f, DEFAULTS[f]), f


REF = {"cream": 0.85, "blue": 0.72, "green": 0.52, "red": 0.5, "orange": 0.55, "tan": 0.55, "brown": 0.38, "yellow": 0.7, "purple": 0.6}


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def shade(base, src, fam):
    ref = REF.get(fam)

    if ref is None:
        return base

    k = min(max(1.0 + 1.2 * (lum(src) - ref) / ref, 0.78), 1.15)

    return tuple(min(1.0, x * k) for x in base)


def sample(img, uv):
    w, h = img.size
    x = min(w - 1, max(0, int(uv[0] * w)))
    y = min(h - 1, max(0, int(uv[1] * h)))
    i = (y * w + x) * 4
    px = img["_px"]

    return (px[i], px[i + 1], px[i + 2])


def base_color(mat):
    img = None
    col = (1, 1, 1)

    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                img = n.image
            if n.type == "BSDF_PRINCIPLED":
                col = tuple(n.inputs["Base Color"].default_value[:3])

    if img is not None and "_px" not in img:
        img.colorspace_settings.name = "Non-Color"
        img["_px"] = list(img.pixels)

    return img, tuple(x ** (1 / 2.2) for x in col)


def load(path, style, height=None, scale=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bm = bmesh.new()

    for o in meshes:
        me = o.data
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)

        for layer in list(tmp.loops.layers.float_color) + list(tmp.loops.layers.color):
            tmp.loops.layers.float_color.remove(layer) if layer in list(tmp.loops.layers.float_color) else tmp.loops.layers.color.remove(layer)

        for layer in list(tmp.verts.layers.float_color) + list(tmp.verts.layers.color):
            tmp.verts.layers.float_color.remove(layer) if layer in list(tmp.verts.layers.float_color) else tmp.verts.layers.color.remove(layer)
        uv = tmp.loops.layers.uv.active
        col = tmp.loops.layers.float_color.new("Col")

        for f in tmp.faces:
            mat = me.materials[f.material_index] if me.materials else None
            img, flat = base_color(mat)

            if img is not None and uv is not None:
                cu = Vector((0, 0))

                for l in f.loops:
                    cu += l[uv].uv

                src = sample(img, cu / len(f.loops))
                t, fam = remap(src, style)

                for l in f.loops:
                    corner = sample(img, l[uv].uv * 0.85 + cu / len(f.loops) * 0.15)
                    c = shade(t, corner if family(corner) == fam else src, fam)
                    l[col] = (c[0], c[1], c[2], 1.0)
            else:
                t, fam = remap(flat, style)
                c = shade(t, flat, fam)

                for l in f.loops:
                    l[col] = (c[0], c[1], c[2], 1.0)

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)

    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    k = 1.0

    if height:
        k = height / max(hi.z - lo.z, 1e-4)
    elif scale:
        k = scale

    bm.transform(Matrix.Scale(k, 4))

    return bm


class Asm:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new("Col")

    def add(self, src, loc=(0, 0, 0), rot=0.0, scl=1.0):
        me = bpy.data.meshes.new("p")
        src.to_mesh(me)
        me.transform(Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Scale(scl, 4))
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def box(self, lo, hi, c):
        bm = bmesh.new()
        col = bm.loops.layers.float_color.new("Col")
        bmesh.ops.create_cube(bm, size=1.0)
        lo = Vector(lo)
        hi = Vector(hi)

        for v in bm.verts:
            v.co = Vector((lo.x + (v.co.x + 0.5) * (hi.x - lo.x), lo.y + (v.co.y + 0.5) * (hi.y - lo.y), lo.z + (v.co.z + 0.5) * (hi.z - lo.z)))

        for f in bm.faces:
            for l in f.loops:
                l[col] = (c[0], c[1], c[2], 1.0)

        me = bpy.data.meshes.new("b")
        bm.to_mesh(me)
        bm.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def export(self, name):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        mat = bpy.data.materials.new("kit")
        mat.use_backface_culling = False
        mat.use_nodes = True
        mat.diffuse_color = (1, 1, 1, 1)

        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (1, 1, 1, 1)
                n.inputs["Roughness"].default_value = 1.0
        me.materials.append(mat)
        for ca in [c for c in me.color_attributes if c.name != "Col"]:
            me.color_attributes.remove(ca)

        for at in [a for a in me.attributes if a.name not in ("position", "Col") and not a.name.startswith(".") and a.domain in ("POINT", "CORNER") and a.data_type in ("FLOAT_COLOR", "BYTE_COLOR")]:
            me.attributes.remove(at)

        me.color_attributes.active_color = me.color_attributes["Col"]
        me.color_attributes.render_color_index = 0
        print("ATTRS", [(a.name, a.domain, a.data_type) for a in me.attributes])

        for o in bpy.context.scene.objects:
            o.select_set(o == ob)

        bpy.context.view_layer.objects.active = ob
        path = os.path.join(OUT, name + ".glb")
        kw = dict(filepath=path, export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=True)

        try:
            bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
        except TypeError:
            bpy.ops.export_scene.gltf(export_colors=True, **kw)

        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        zs = [v.co.z for v in me.vertices]
        bounds = [min(xs), min(zs), -max(ys), max(xs), max(zs), -min(ys)]
        bpy.data.objects.remove(ob, do_unlink=True)
        self.bm.free()

        return {"file": "kd/" + name + ".glb", "min": bounds[:3], "max": bounds[3:], "tris": sum(len(p.vertices) - 2 for p in me.polygons)}


def g2b(x, y, z):
    return (x, -z, y)


def face_rot(nx, nz):
    return math.atan2(nx, nz)


HOUSES = [
    ["11", "11"],
    ["22"],
    ["112", "111"],
    ["22", "21"],
    ["111"],
    ["3"],
    ["21", "11"],
    ["222", "111"],
]

DOORS = ["building-door", "building-door-window", "building-edges-door"]
LOW = ["building-window", "building-window-awnings", "building-window-sill", "building-windows-sills", "building-window-wide-sill", "building-windows"]
HIGH = ["building-window-balcony", "building-windows-sills-round", "building-window-sill", "building-windows-round", "building-window-left-sill", "building-windows-high-top-round"]


def house(index, cache):
    grid = HOUSES[index]
    rows = len(grid)
    cols = len(grid[0])
    wall = WALLS[index % len(WALLS)]
    accent = ACCENTS[(index * 3 + 1) % len(ACCENTS)]
    style = {"cream": wall, "white": tuple(min(1, x * 1.08) for x in wall), "green": accent, "red": accent, "tan": TRIM, "orange": TRIM, "yellow": accent}
    key = "w%d" % index

    def piece(name):
        k = key + name

        if k not in cache:
            cache[k] = load(os.path.join(MB, name + ".glb"), style, scale=S)

        return cache[k]

    a = Asm()
    blocks = []
    hgt = lambda r, c: int(grid[r][c]) if 0 <= r < rows and 0 <= c < cols else 0
    w = cols * S
    d = rows * S
    rr = random.Random(index * 31 + 5)

    for r in range(rows):
        for c in range(cols):
            h = hgt(r, c)
            x = -w / 2 + (c + 0.5) * S
            z = d / 2 - (r + 0.5) * S
            blocks.append([x - S / 2, z - S / 2, x + S / 2, z + S / 2, h * STOREY])

            for f in range(h):
                outs = []

                for dc, dr, nx, nz in ((0, -1, 0, 1), (1, 0, 1, 0), (-1, 0, -1, 0), (0, 1, 0, -1)):
                    if hgt(r + dr, c + dc) <= f:
                        outs.append((nx, nz))

                if not outs:
                    name = "building-block"
                    n = (0, 1)
                else:
                    n = outs[0] if (f == 0 or rr.random() < 0.6) else outs[rr.randrange(len(outs))]

                    if f == 0 and n == (0, 1) and c == cols // 2 and r == 0:
                        name = DOORS[index % len(DOORS)]
                    elif f == 0:
                        name = LOW[rr.randrange(len(LOW))]
                    else:
                        name = HIGH[rr.randrange(len(HIGH))]

                a.add(piece(name), g2b(x, f * STOREY, z), face_rot(n[0], n[1]))

            a.box(g2b(x - S / 2 - 0.04, -0.9, z + S / 2 + 0.04), g2b(x + S / 2 + 0.04, 0.35, z - S / 2 - 0.04), (0.64, 0.50, 0.38))
            top = h * STOREY
            a.box(g2b(x - S / 2 + 0.02, top - 0.02, z + S / 2 - 0.02), g2b(x + S / 2 - 0.02, top + 0.08, z - S / 2 + 0.02), tuple(x_ * 0.9 for x_ in wall))

            for dc, dr, nx, nz in ((0, -1, 0, 1), (1, 0, 1, 0), (-1, 0, -1, 0), (0, 1, 0, -1)):
                if hgt(r + dr, c + dc) >= h:
                    continue

                t = 0.28
                ph = 0.55

                if nx == 0:
                    zz = z + nz * (S / 2 - t / 2)
                    lo = (x - S / 2, top, zz - t / 2)
                    hi = (x + S / 2, top + ph, zz + t / 2)
                else:
                    xx = x + nx * (S / 2 - t / 2)
                    lo = (xx - t / 2, top, z - S / 2)
                    hi = (xx + t / 2, top + ph, z + S / 2)

                a.box(g2b(lo[0], lo[1], hi[2]), g2b(hi[0], hi[1], lo[2]), wall)
                a.box(g2b(lo[0] - 0.05, hi[1], hi[2] + 0.05), g2b(hi[0] + 0.05, hi[1] + 0.1, lo[2] - 0.05), tuple(min(1, x_ * 1.05) for x_ in wall))

            if h > 0 and rr.random() < 0.55:
                ac = piece(rr.choice(["detail-ac-a", "detail-ac-b"]))
                a.add(ac, g2b(x + rr.uniform(-1, 1), top + 0.08, z + rr.uniform(-1, 1)), rr.choice([0, 1.57, 3.14]))

    for r in range(rows):
        for c in range(cols):
            if r == 0 and hgt(r, c) > 0 and rr.random() < 0.5:
                x = -w / 2 + (c + 0.5) * S
                z = d / 2

                for i, u in enumerate((-1.2, -0.4, 0.4, 1.2)):
                    a.box(g2b(x + u - 0.04, 2.55, z + 1.4), g2b(x + u + 0.04, 2.62, z), WOOD)

                a.box(g2b(x - 1.7, 2.62, z + 1.5), g2b(x + 1.7, 2.68, z - 0.02), accent)

    info = a.export("house_%d" % index)
    info["blocks"] = blocks
    info["w"] = w
    info["d"] = d

    return info


PROPS = [
    ("palm_0", PI, "palm-detailed-straight", 8.5, {"orange": (0.58, 0.43, 0.30), "tan": (0.50, 0.37, 0.26)}),
    ("palm_1", PI, "palm-detailed-bend", 7.5, {"orange": (0.58, 0.43, 0.30), "tan": (0.50, 0.37, 0.26)}),
    ("palm_2", NA, "tree_palmTall", 9.0, {"orange": (0.58, 0.43, 0.30), "tan": (0.50, 0.37, 0.26), "brown": (0.50, 0.37, 0.26), "white": (0.60, 0.45, 0.32), "cream": (0.62, 0.47, 0.33), "grey": (0.55, 0.41, 0.29), "grey_d": (0.45, 0.33, 0.24)}),
    ("rock_0", PI, "rocks-sand-a", 1.6, {"grey": ROCK, "grey_d": ROCK_D, "cream": (0.80, 0.70, 0.52), "tan": ROCK}),
    ("rock_1", PI, "rocks-sand-b", 2.2, {"grey": ROCK, "grey_d": ROCK_D, "cream": (0.80, 0.70, 0.52), "tan": ROCK}),
    ("rock_2", PI, "rocks-sand-c", 2.8, {"grey": ROCK, "grey_d": ROCK_D, "cream": (0.80, 0.70, 0.52), "tan": ROCK}),
    ("rock_3", NA, "rock_tallB", 4.5, {"grey": ROCK, "grey_d": ROCK_D, "white": (0.76, 0.62, 0.48)}),
    ("mesa_0", NA, "rock_tallA", 34.0, {"grey": ROCK, "grey_d": ROCK_D, "white": (0.76, 0.62, 0.48)}),
    ("mesa_1", NA, "rock_tallC", 28.0, {"grey": ROCK, "grey_d": ROCK_D, "white": (0.76, 0.62, 0.48)}),
    ("mesa_2", NA, "rock_tallE", 30.0, {"grey": ROCK, "grey_d": ROCK_D, "white": (0.76, 0.62, 0.48)}),
    ("rock_4", NA, "rock_largeA", 1.3, {"grey": ROCK, "grey_d": ROCK_D, "white": (0.76, 0.62, 0.48)}),
    ("cactus_0", NA, "cactus_tall", 2.8, {}),
    ("cactus_1", NA, "cactus_short", 1.4, {}),
    ("scrub", NA, "grass_large", 0.7, {"green": (0.56, 0.55, 0.34)}),
    ("tent_0", SV, "tent-canvas", 2.5, {}),
    ("tent_1", NA, "tent_detailedOpen", 2.8, {"blue": ACCENTS[0], "purple": ACCENTS[0]}),
    ("stall_0", FT, "stall-red", 2.8, {}),
    ("stall_1", FT, "stall-green", 2.8, {"green": ACCENTS[1]}),
    ("stall_2", FT, "stall", 2.8, {}),
    ("bench", FT, "stall-bench", 0.5, {}),
    ("cart", FT, "cart", 1.7, {}),
    ("barrel", SV, "barrel", 1.0, {"red": (0.56, 0.36, 0.25), "orange": (0.56, 0.36, 0.25), "purple": (0.36, 0.33, 0.31), "blue": (0.36, 0.33, 0.31)}),
    ("crate", SV, "box", 0.8, {}),
    ("box", SV, "box-large", 1.0, {}),
    ("chest", PI, "chest", 0.7, {}),
    ("fence", SV, "fence-fortified", 1.4, {}),
    ("lantern", FT, "lantern", 2.6, {}),
    ("fountain", FT, "fountain-round-detail", 1.4, {"blue": (0.30, 0.58, 0.60), "grey": STONE, "grey_d": STONE_D}),
    ("arch", FT, "wall-arch", 4.2, {"grey": STONE, "grey_d": STONE_D, "purple": STONE_D, "blue": STONE, "white": (0.86, 0.78, 0.64)}),
    ("wall_broken", FT, "wall-broken", 3.4, {"grey": STONE, "grey_d": STONE_D, "purple": STONE_D, "blue": STONE, "white": (0.86, 0.78, 0.64)}),
    ("pillar", FT, "pillar-stone", 4.2, {"grey": STONE, "grey_d": STONE_D, "purple": STONE_D, "blue": STONE, "white": (0.86, 0.78, 0.64)}),
    ("column", NA, "statue_columnDamaged", 4.0, {"grey": STONE, "grey_d": STONE_D, "white": (0.86, 0.78, 0.64)}),
    ("obelisk", NA, "statue_obelisk", 9.0, {"grey": STONE, "grey_d": STONE_D, "white": (0.86, 0.78, 0.64)}),
    ("banner", FT, "banner-red", 3.2, {}),
    ("flag", PI, "flag-high-pennant", 5.5, {"white": ACCENTS[0], "grey": WOOD}),
    ("signpost", SV, "signpost", 1.9, {}),
    ("campfire", SV, "campfire-pit", 0.5, {}),
    ("patch_0", PI, "patch-sand", 0.25, {"cream": (0.76, 0.64, 0.47), "tan": (0.70, 0.58, 0.42), "orange": (0.72, 0.60, 0.44)}),
    ("patch_1", PI, "patch-sand-foliage", 0.6, {"cream": (0.76, 0.64, 0.47), "tan": (0.70, 0.58, 0.42), "orange": (0.72, 0.60, 0.44), "green": (0.50, 0.52, 0.30)}),
    ("stairs", FT, "stairs-wide-stone", 1.0, {"grey": STONE, "grey_d": STONE_D, "purple": STONE_D, "blue": STONE, "white": (0.86, 0.78, 0.64)}),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    reset()
    infos = {}
    cache = {}

    for i in range(len(HOUSES)):
        infos["house_%d" % i] = house(i, cache)
        print("DONE house", i)

    for name, kit, src, height, style in PROPS:
        ext = ".glb"
        a = Asm()
        a.add(load(os.path.join(kit, src + ext), style, height=height))
        infos[name] = a.export(name)
        print("DONE", name, infos[name]["tris"])

    with open(os.environ["JSON"], "w") as f:
        json.dump(infos, f, indent=1)


main()
