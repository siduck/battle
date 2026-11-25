import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
PREV = args[1]
ONLY = args[2].split(",") if len(args) > 2 else None

os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


PALE = rgb(206, 236, 232)
LIGHT = rgb(168, 220, 218)
MID = rgb(112, 186, 190)
DEEP = rgb(58, 132, 144)
INK = rgb(34, 92, 106)
GLOW = rgb(214, 255, 250)
AMBER = rgb(246, 168, 78)
GLASS = rgb(196, 244, 242)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


class Kit:
    def __init__(self, height):
        self.parts = []
        self.height = height

    def add(self, bm, col, bevel=0.08, segs=3, glow=0.0, grad=True, smooth=True):
        me = bpy.data.meshes.new("m")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("o", me)
        bpy.context.scene.collection.objects.link(ob)

        if bevel > 0:
            mod = ob.modifiers.new("b", "BEVEL")
            mod.width = bevel
            mod.segments = segs
            mod.limit_method = "ANGLE"
            mod.angle_limit = math.radians(35)
            mod.harden_normals = True

        if smooth:
            for p in me.polygons:
                p.use_smooth = True

        ob["col"] = col
        ob["glow"] = glow
        ob["grad"] = 1 if grad else 0
        self.parts.append(ob)

        return ob

    def box(self, lo, hi, col, bevel=0.08, segs=3, glow=0.0, grad=True):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        s = [max(hi[i] - lo[i], 0.002) for i in range(3)]

        for v in bm.verts:
            v.co = Vector((c[0] + v.co.x * s[0], c[1] + v.co.y * s[1], c[2] + v.co.z * s[2]))

        b = min(bevel, min(s) * 0.45)

        return self.add(bm, col, b, segs, glow, grad)

    def cyl(self, a, b, r, col, n=32, bevel=0.06, glow=0.0, r2=None):
        bm = bmesh.new()
        a = Vector(a)
        b = Vector(b)
        axis = b - a
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=axis.length)
        rot = axis.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=bm.verts)

        return self.add(bm, col, bevel, 3, glow)

    def torus(self, center, major, minor, col, glow=0.0, n=48, m=16):
        bm = bmesh.new()
        verts = []

        for i in range(n):
            a = 2 * math.pi * i / n
            row = []

            for j in range(m):
                t = 2 * math.pi * j / m
                r = major + minor * math.cos(t)
                row.append(bm.verts.new((center[0] + r * math.cos(a), center[1] + minor * math.sin(t), center[2] + r * math.sin(a))))

            verts.append(row)

        for i in range(n):
            for j in range(m):
                bm.faces.new((verts[i][j], verts[(i + 1) % n][j], verts[(i + 1) % n][(j + 1) % m], verts[i][(j + 1) % m]))

        bm.normal_update()

        return self.add(bm, col, 0, 1, glow)

    def cut(self, target, cutter):
        mod = target.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cutter
        target.modifiers.move(len(target.modifiers) - 1, 0)
        cutter.hide_render = True
        self.parts.remove(cutter)
        cutter["cutter"] = 1

    def finish(self, name, zmin=0.0, ao=True):
        for ob in bpy.context.scene.objects:
            ob.select_set(False)

        dg = bpy.context.evaluated_depsgraph_get()
        built = []

        for ob in self.parts:
            ev = ob.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
            me.transform(ob.matrix_world)
            nob = bpy.data.objects.new("p", me)
            bpy.context.scene.collection.objects.link(nob)
            col = tuple(ob["col"])
            glow = ob["glow"]
            grad = ob["grad"]
            attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
            gattr = me.attributes.new("_glow", "FLOAT", "POINT")

            for gi in range(len(me.vertices)):
                gattr.data[gi].value = glow

            for poly in me.polygons:
                for li in poly.loop_indices:
                    z = me.vertices[me.loops[li].vertex_index].co.z
                    h = min(max((z - zmin) / max(self.height, 0.5), 0), 1)
                    k = 1.0

                    if grad and glow == 0:
                        k *= 0.86 + 0.2 * h
                        k *= 0.9 + 0.1 * min(max((z - zmin) / 0.6, 0), 1)

                    attr.data[li].color = (min(col[0] * k, 1), min(col[1] * k, 1), min(col[2] * k, 1), 1.0 - glow)

            built.append(nob)

        for ob in list(bpy.data.objects):
            if ob not in built:
                bpy.data.objects.remove(ob, do_unlink=True)

        for ob in built:
            ob.select_set(True)

        bpy.context.view_layer.objects.active = built[0]

        if len(built) > 1:
            bpy.ops.object.join()

        ob = bpy.context.view_layer.objects.active
        ob.name = name
        me = ob.data

        if ao:
            bake_ao(me, zmin)

        mat = bpy.data.materials.new("prism")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.5
        me.materials.clear()
        me.materials.append(mat)
        me.color_attributes.active_color = me.color_attributes["Col"]
        me.color_attributes.render_color_index = me.color_attributes.find("Col")

        for o in bpy.context.scene.objects:
            o.select_set(o == ob)

        path = os.path.join(OUT, name + ".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT", export_attributes=True)
        render(ob, name)
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        print("PIECE", name, os.path.getsize(path), len(me.polygons), "min", (round(lo[0], 3), round(lo[2], 3), round(-hi[1], 3)), "max", (round(hi[0], 3), round(hi[2], 3), round(-lo[1], 3)))
        bpy.data.objects.remove(ob, do_unlink=True)


def bake_ao(me, zmin):
    from mathutils.bvhtree import BVHTree

    verts = [v.co.copy() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    g = len(verts)
    pad = 20.0
    verts += [Vector((lo.x - pad, lo.y - pad, zmin)), Vector((hi.x + pad, lo.y - pad, zmin)), Vector((hi.x + pad, hi.y + pad, zmin)), Vector((lo.x - pad, hi.y + pad, zmin))]
    polys.append((g, g + 1, g + 2, g + 3))
    tree = BVHTree.FromPolygons(verts, polys)
    rng = random.Random(7)
    dirs = []

    while len(dirs) < 20:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))

        if 0.05 < d.length <= 1:
            dirs.append(d.normalized())

    attr = me.color_attributes["Col"]
    reach = 1.4
    cache = {}
    normals = [l.normal.copy() for l in me.loops] if hasattr(me.loops[0], "normal") else None

    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            n = normals[li] if normals else p.normal
            key = (vi, round(n.x, 1), round(n.y, 1), round(n.z, 1))

            if key not in cache:
                origin = me.vertices[vi].co + n * 0.02
                hits = 0
                total = 0

                for d in dirs:
                    if d.dot(n) <= 0.05:
                        d = d - n * (2 * d.dot(n))

                    if d.dot(n) <= 0.05:
                        continue

                    total += 1
                    loc, _, idx, dist = tree.ray_cast(origin, d, reach)

                    if loc is not None:
                        hits += 1 - dist / reach

                cache[key] = hits / max(total, 1)

            occ = cache[key]
            k = 1 - 0.5 * occ
            c = attr.data[li].color

            if c[3] < 0.99:
                continue

            attr.data[li].color = (c[0] * k * (1 - 0.06 * occ), c[1] * k, c[2] * k, c[3])


def render(ob, name):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = False
    sh.show_shadows = False
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.55, 0.82, 0.84)
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.view_settings.view_transform = "Standard"

    lo = Vector([min(v.co[i] for v in ob.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in ob.data.vertices) for i in range(3)])
    c = (lo + hi) / 2
    r = (hi - lo).length / 2

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 40
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    d = r * 2.7
    cam.location = c + Vector((d * 0.62, -d * 0.7, d * 0.45))
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(PREV, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def strip_x(k, x0, x1, y, z, t=0.06, d=0.04):
    k.box((x0, y - d, z - t), (x1, y + d, z + t), GLOW, bevel=0.02, segs=1, glow=0.85)


def pillar():
    k = Kit(7.0)
    k.box((-0.95, -0.95, 0), (0.95, 0.95, 0.45), DEEP, bevel=0.14)
    k.box((-0.7, -0.7, 0.4), (0.7, 0.7, 6.6), LIGHT, bevel=0.2)
    k.box((-0.92, -0.92, 6.55), (0.92, 0.92, 7.0), MID, bevel=0.14)

    for s in (-1, 1):
        k.box((s * 0.71 - 0.03, -0.12, 0.8), (s * 0.71 + 0.03, 0.12, 6.2), GLOW, bevel=0.02, segs=1, glow=0.8)

    k.finish("pillar")


def slab():
    k = Kit(0.6)
    k.box((-4, -4, 0), (4, 4, 0.6), PALE, bevel=0.16)

    for s in (-1, 1):
        k.box((-3.6, s * 4.0 - 0.04, 0.24), (3.6, s * 4.0 + 0.04, 0.34), GLOW, bevel=0.015, segs=1, glow=0.85)
        k.box((s * 4.0 - 0.04, -3.6, 0.24), (s * 4.0 + 0.04, 3.6, 0.34), GLOW, bevel=0.015, segs=1, glow=0.85)

    k.finish("slab")


def plaza():
    k = Kit(2.0)
    k.box((-14.6, -14.6, 0), (14.6, 14.6, 0.5), DEEP, bevel=0.2)
    k.box((-14, -14, 0.4), (14, 14, 2.0), PALE, bevel=0.3)

    for s in (-1, 1):
        k.box((-13.2, s * 14 - 0.05, 1.45), (13.2, s * 14 + 0.05, 1.6), GLOW, bevel=0.02, segs=1, glow=0.85)
        k.box((s * 14 - 0.05, -13.2, 1.45), (s * 14 + 0.05, 13.2, 1.6), GLOW, bevel=0.02, segs=1, glow=0.85)

    for i in range(-2, 3):
        k.box((i * 5.6 - 0.04, -12, 1.99), (i * 5.6 + 0.04, 12, 2.02), LIGHT, bevel=0.0, grad=False)
        k.box((-12, i * 5.6 - 0.04, 1.99), (12, i * 5.6 + 0.04, 2.02), LIGHT, bevel=0.0, grad=False)

    k.finish("plaza")


def stair(name, width, length, rise, steps):
    k = Kit(rise)
    run = length / steps
    hgt = rise / steps

    for i in range(steps):
        k.box((-width / 2, i * run, 0), (width / 2, (i + 1) * run + 0.02, (i + 1) * hgt), PALE if i % 2 == 0 else LIGHT, bevel=0.06, segs=2)

    for s in (-1, 1):
        bm = bmesh.new()
        x0 = s * (width / 2) - (0.0 if s > 0 else 0.35)
        x1 = x0 + 0.35
        pts = [(0, 0), (length, 0), (length, rise + 0.9), (length - 0.6, rise + 0.9), (0, 0.9)]
        top = [bm.verts.new((x0, y, z)) for y, z in pts]
        bot = [bm.verts.new((x1, y, z)) for y, z in pts]
        bm.faces.new(top[::-1])
        bm.faces.new(bot)

        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((top[i], top[j], bot[j], bot[i]))

        bm.normal_update()
        k.add(bm, MID, 0.08, 3)
        bm2 = bmesh.new()
        xs = x0 - 0.02 if s < 0 else x1 + 0.02
        a = Vector((xs, 0.5, 0.55))
        b = Vector((xs, length - 0.5, rise + 0.55))
        bmesh.ops.create_cube(bm2, size=1.0)
        L = (b - a).length

        for v in bm2.verts:
            v.co = Vector((v.co.x * 0.05, v.co.y * L, v.co.z * 0.1))

        rot = Matrix.Rotation(math.atan2(rise, length), 4, "X")
        bmesh.ops.transform(bm2, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=bm2.verts)
        k.add(bm2, GLOW, 0.01, 1, glow=0.85)

    k.finish(name)


def bridge():
    k = Kit(1.6)
    k.box((-2.2, -8, 0), (2.2, 8, 0.6), PALE, bevel=0.15)
    k.box((-1.6, -7.6, -0.6), (1.6, 7.6, 0.05), DEEP, bevel=0.2)

    for s in (-1, 1):
        k.box((s * 2.05 - 0.14, -8, 0.55), (s * 2.05 + 0.14, 8, 1.6), LIGHT, bevel=0.1)
        k.box((s * 2.05 - 0.02, -7.6, 1.15), (s * 2.05 + 0.02, 7.6, 1.25), GLOW, bevel=0.01, segs=1, glow=0.85)
        k.box((s * 2.2 - 0.03, -7.8, 0.22), (s * 2.2 + 0.03, 7.8, 0.34), GLOW, bevel=0.01, segs=1, glow=0.85)

    k.finish("bridge", ao=False)


def rail():
    k = Kit(1.1)
    k.box((-2, -0.16, 0), (2, 0.16, 1.1), LIGHT, bevel=0.12)
    k.box((-1.8, -0.18, 0.75), (1.8, 0.18, 0.83), GLOW, bevel=0.01, segs=1, glow=0.85)
    k.finish("rail")


def glass():
    k = Kit(2.4)
    k.box((-2, -0.05, 0.2), (2, 0.05, 2.4), GLASS, bevel=0.03, segs=2, grad=False)
    k.finish("glass_pane", ao=False)
    k = Kit(2.5)
    k.box((-2.15, -0.22, 0), (2.15, 0.22, 0.25), MID, bevel=0.08)

    for s in (-1, 1):
        k.box((s * 2.05 - 0.12, -0.12, 0.1), (s * 2.05 + 0.12, 0.12, 2.5), LIGHT, bevel=0.06)

    k.box((-2.15, -0.1, 2.38), (2.15, 0.1, 2.5), GLOW, bevel=0.02, segs=1, glow=0.85)
    k.finish("glass_frame")


def cube():
    k = Kit(2.4)
    k.box((-1.2, -1.2, 0), (1.2, 1.2, 2.4), LIGHT, bevel=0.3, segs=4)
    k.box((-1.21, -0.06, 0.4), (1.21, 0.06, 2.0), GLOW, bevel=0.02, segs=1, glow=0.85)
    k.finish("cube")


def ring():
    k = Kit(12)
    k.torus((0, 0, 6), 5.4, 0.45, MID)
    k.torus((0, 0, 6), 4.85, 0.12, GLOW, glow=0.9, m=8)
    k.finish("ring", zmin=0, ao=False)


def monolith():
    k = Kit(18)
    k.box((-2.6, -1.4, 0), (2.6, 1.4, 0.6), DEEP, bevel=0.15)
    k.box((-2, -1, 0.5), (2, 1, 18), LIGHT, bevel=0.35, segs=4)

    for x in (-1.2, 1.2):
        k.box((x - 0.07, -1.02, 1.4), (x + 0.07, 1.02, 16.8), GLOW, bevel=0.02, segs=1, glow=0.85)

    k.box((-2.02, -0.1, 17.2), (2.02, 0.1, 17.4), GLOW, bevel=0.02, segs=1, glow=0.85)
    k.finish("monolith")


def cover():
    k = Kit(1.2)
    k.box((-1.5, -0.55, 0), (1.5, 0.55, 1.2), LIGHT, bevel=0.22, segs=3)
    k.box((-1.3, -0.56, 0.78), (1.3, 0.56, 0.86), GLOW, bevel=0.01, segs=1, glow=0.85)
    k.finish("cover")


def wall():
    k = Kit(3.2)
    k.box((-4, -0.4, 0), (4, 0.4, 3.2), PALE, bevel=0.25, segs=3)
    k.box((-4.2, -0.5, 0), (4.2, 0.5, 0.3), DEEP, bevel=0.1)
    k.box((-3.7, -0.42, 2.5), (3.7, 0.42, 2.6), GLOW, bevel=0.01, segs=1, glow=0.85)
    k.finish("wall")


def arch():
    k = Kit(8)
    body = k.box((-5, -0.8, 0), (5, 0.8, 8), PALE, bevel=0.0)
    hole = k.box((-3.4, -2, -1), (3.4, 2, 4.6), PALE, bevel=0.0)
    top = k.cyl((0, -2, 4.6), (0, 2, 4.6), 3.4, PALE, n=48, bevel=0.0)
    k.cut(body, hole)
    k.cut(body, top)
    mod = body.modifiers.new("b", "BEVEL")
    mod.width = 0.18
    mod.segments = 3
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35)
    mod.harden_normals = True

    for p in body.data.polygons:
        p.use_smooth = True

    k.box((-5.3, -1.1, 0), (-3.1, 1.1, 0.5), DEEP, bevel=0.12)
    k.box((3.1, -1.1, 0), (5.3, 1.1, 0.5), DEEP, bevel=0.12)
    k.box((-5.2, -1.0, 7.6), (5.2, 1.0, 8.2), MID, bevel=0.15)
    k.box((-0.5, -0.82, 7.0), (0.5, 0.82, 7.6), AMBER, bevel=0.06, glow=0.35)

    for s in (-1, 1):
        k.box((s * 4.2 - 0.06, -0.82, 0.8), (s * 4.2 + 0.06, 0.82, 7.3), GLOW, bevel=0.01, segs=1, glow=0.85)

    k.finish("arch")


def pad():
    k = Kit(0.2)
    k.cyl((0, 0, 0), (0, 0, 0.12), 1.6, AMBER, n=40, bevel=0.04, glow=0.35)
    k.cyl((0, 0, 0.1), (0, 0, 0.16), 1.1, rgb(255, 210, 140), n=40, bevel=0.02, glow=0.8)
    k.finish("pad", ao=False)


def strip():
    k = Kit(0.1)
    k.box((-4, -0.12, 0), (4, 0.12, 0.05), GLOW, bevel=0.02, segs=1, glow=0.85)
    k.finish("strip", ao=False)


def plinth():
    k = Kit(1.0)
    k.cyl((0, 0, 0), (0, 0, 0.8), 0.9, MID, n=40, bevel=0.12)
    k.cyl((0, 0, 0.78), (0, 0, 0.86), 0.7, AMBER, n=40, bevel=0.02, glow=0.6)
    k.finish("plinth")


def tower():
    k = Kit(6.6)

    for x in (-6.5, 6.5):
        for y in (-6.5, 6.5):
            k.box((x - 0.8, y - 0.8, 0), (x + 0.8, y + 0.8, 6.0), LIGHT, bevel=0.22)
            k.box((x - 1.05, y - 1.05, 0), (x + 1.05, y + 1.05, 0.4), DEEP, bevel=0.12)

    k.box((-8, -8, 6.0), (8, 8, 6.6), PALE, bevel=0.18)
    k.box((-7.4, -7.4, 5.4), (7.4, 7.4, 6.05), MID, bevel=0.2)

    for s in (-1, 1):
        k.box((-7.4, s * 8 - 0.04, 6.22), (7.4, s * 8 + 0.04, 6.34), GLOW, bevel=0.01, segs=1, glow=0.85)
        k.box((s * 8 - 0.04, -7.4, 6.22), (s * 8 + 0.04, 7.4, 6.34), GLOW, bevel=0.01, segs=1, glow=0.85)

    k.finish("tower")


PIECES = {
    "pillar": pillar,
    "slab": slab,
    "plaza": plaza,
    "stair_lo": lambda: stair("stair_lo", 6, 6, 2, 8),
    "stair_hi": lambda: stair("stair_hi", 4, 12, 6, 18),
    "bridge": bridge,
    "rail": rail,
    "glass": glass,
    "cube": cube,
    "ring": ring,
    "monolith": monolith,
    "cover": cover,
    "wall": wall,
    "arch": arch,
    "pad": pad,
    "strip": strip,
    "plinth": plinth,
    "tower": tower,
}

for name, fn in PIECES.items():
    if ONLY and name not in ONLY:
        continue

    reset()
    fn()
