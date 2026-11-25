import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Matrix, noise

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
PREV = args[1]
ONLY = args[2].split(",") if len(args) > 2 else None

os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

T = 0.35
STOREY = 3.3
SLAB = 0.28
STAIR_LEN = 4.4
STAIR_W = 1.3


def rgb(r, g, b):
    return (r / 255, g / 255, b / 255)


PLASTER = [rgb(238, 212, 172), rgb(234, 198, 160), rgb(242, 222, 186), rgb(230, 192, 150), rgb(240, 206, 168), rgb(236, 216, 178)]
SHUTTER = [rgb(38, 128, 132), rgb(46, 150, 150), rgb(186, 84, 56), rgb(38, 128, 132), rgb(214, 160, 58), rgb(46, 150, 150)]
CLOTH = [rgb(186, 84, 56), rgb(38, 128, 132), rgb(222, 168, 62), rgb(196, 104, 64), rgb(46, 150, 150), rgb(206, 120, 70)]
WOOD = rgb(112, 70, 42)
DOOR = [rgb(36, 118, 124), rgb(182, 80, 54), rgb(42, 138, 140), rgb(96, 62, 38), rgb(36, 118, 124), rgb(210, 152, 52)]
TILE = [rgb(38, 128, 132), rgb(244, 232, 208), rgb(186, 84, 56), rgb(222, 168, 62)]
BAND = [rgb(74, 128, 128), rgb(88, 142, 138), rgb(82, 112, 134), rgb(74, 128, 128), rgb(168, 104, 78), rgb(88, 142, 138)]
STONE = rgb(200, 176, 140)
IRON = rgb(52, 52, 54)
RECESS = rgb(58, 42, 34)
SAFFRON = rgb(222, 168, 62)
TERRA = rgb(186, 84, 56)
TEAL = rgb(38, 128, 132)
PAVE = [rgb(198, 178, 144), rgb(192, 172, 140), rgb(203, 183, 149), rgb(188, 168, 136)]
MAT = {}


def tag(col, m):
    MAT[tuple(round(c, 3) for c in col)] = m


def mat_of(col):
    return MAT.get(tuple(round(c, 3) for c in col), 0)
LAMP = rgb(255, 214, 130)
WOOD_DARK = rgb(84, 52, 32)
TANK = rgb(140, 144, 138)
POT = rgb(190, 96, 60)
LEAF = rgb(104, 132, 70)
STRATA = [rgb(118, 92, 74), rgb(142, 110, 85), rgb(158, 124, 96), rgb(176, 142, 110), rgb(196, 166, 130)]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


class Kit:
    def __init__(self, height, seed=1):
        self.objs = []
        self.height = height
        self.rng = random.Random(seed)

    def mesh(self, bm, col, bevel=0.0, shade=True, grad=True):
        me = bpy.data.meshes.new("m")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("o", me)
        bpy.context.scene.collection.objects.link(ob)
        ob["col"] = col
        ob["grad"] = 1 if grad else 0
        ob["mat"] = mat_of(col)

        if bevel > 0:
            mod = ob.modifiers.new("b", "BEVEL")
            mod.width = bevel
            mod.segments = 1
            mod.limit_method = "ANGLE"
            mod.angle_limit = math.radians(40)

        self.objs.append(ob)

        return ob

    def box(self, lo, hi, col, bevel=0.0, grad=True):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        s = [max(hi[i] - lo[i], 0.002) for i in range(3)]

        for v in bm.verts:
            v.co = Vector((c[0] + v.co.x * s[0], c[1] + v.co.y * s[1], c[2] + v.co.z * s[2]))

        return self.mesh(bm, col, bevel, grad=grad)

    def cyl(self, a, b, r, col, n=8, r2=None, bevel=0.0):
        bm = bmesh.new()
        a = Vector(a)
        b = Vector(b)
        axis = (b - a)
        length = axis.length
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=length)
        rot = axis.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=bm.verts)

        return self.mesh(bm, col, bevel)

    def blob(self, rx, ry=None, cx=0.0, cy=0.0, z=0.025):
        ry = rx if ry is None else ry
        bm = bmesh.new()
        c = bm.verts.new((cx, cy, z))
        ring = [bm.verts.new((cx + math.cos(j / 14 * 6.283) * rx, cy + math.sin(j / 14 * 6.283) * ry, z)) for j in range(14)]

        for j in range(14):
            bm.faces.new((c, ring[j], ring[(j + 1) % 14]))

        ob = self.mesh(bm, (0, 0, 0), 0, grad=False)
        ob["blob"] = (cx, cy, rx, ry)

        return ob

    def rock(self, center, size, col_k=1.0, seed=0, flat=0.6):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        off = Vector((seed * 3.1, seed * 1.7, seed * 0.9))

        for v in bm.verts:
            d = noise.noise(v.co * 1.3 + off) * 0.28
            v.co = v.co * (1 + d)
            v.co.z *= flat

            if v.co.z < -0.15 * flat:
                v.co.z = -0.15 * flat

            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)

        ob = self.mesh(bm, (0, 0, 0))
        ob["strata"] = col_k

        return ob

    def subtract(self, target, cutters):
        for c in cutters:
            mod = target.modifiers.new("cut", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            mod.object = c

        bpy.context.view_layer.objects.active = target

        for m in list(target.modifiers):
            if m.type == "BOOLEAN":
                bpy.ops.object.modifier_apply(modifier=m.name)

        for c in cutters:
            self.objs.remove(c)
            bpy.data.objects.remove(c, do_unlink=True)

    def finish(self, name, zmin=0.0):
        dg = bpy.context.evaluated_depsgraph_get()
        meshes = []

        for ob in self.objs:
            ev = ob.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev)
            me.transform(ob.matrix_world)
            col = tuple(ob["col"])
            grad = ob["grad"]
            strata = ob.get("strata")
            blob = ob.get("blob")
            ma = 1.0 - ob.get("mat", 0) / 16.0
            attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

            jit = 1 + (self.rng.random() - 0.5) * 0.04
            cloth = ob.get("cloth")

            for poly in me.polygons:
                face_j = 1 + (self.rng.random() - 0.5) * 0.03

                if blob is not None:
                    for li in poly.loop_indices:
                        co = me.vertices[me.loops[li].vertex_index].co
                        dd = math.hypot((co.x - blob[0]) / blob[2], (co.y - blob[1]) / blob[3])
                        t = min(dd, 1)
                        dark = (150 / 255, 130 / 255, 100 / 255)
                        sand = (206 / 255, 186 / 255, 146 / 255)
                        attr.data[li].color = tuple(dark[i] + (sand[i] - dark[i]) * t for i in range(3)) + (ma,)

                    continue

                for li in poly.loop_indices:
                    z = me.vertices[me.loops[li].vertex_index].co.z
                    h = min(max((z - zmin) / max(self.height, 0.5), 0), 1)
                    base = col

                    if strata is not None:
                        zc = poly.center.z
                        band = int(min(max((zc - zmin) / max(self.height, 0.5) * len(STRATA), 0), len(STRATA) - 1))
                        base = tuple(c * strata for c in STRATA[band])

                    k = jit * face_j

                    if grad:
                        k *= 0.88 + 0.16 * h
                        k *= 0.9 + 0.1 * min(max((z - zmin) / 0.45, 0), 1)

                    if cloth is not None:
                        k = 1.0 if poly.normal.z > 0 else 1.18
                    elif poly.normal.z > 0.7:
                        k *= 1.05
                    elif poly.normal.z < -0.7:
                        k *= 0.94

                    attr.data[li].color = (min(base[0] * k, 1), min(base[1] * k, 1), min(base[2] * k, 1), ma)

            meshes.append(me)

        for ob in list(self.objs):
            bpy.data.objects.remove(ob, do_unlink=True)

        bm = bmesh.new()

        for me in meshes:
            bm.from_mesh(me)

        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()

        cull_hidden(me)

        for p in me.polygons:
            p.use_smooth = False

        bake_ao(me, zmin)

        mat = bpy.data.materials.new("kit")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.95
        me.materials.append(mat)
        me.color_attributes.active_color = me.color_attributes["Col"]

        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.color_attributes.render_color_index = 0

        for o in bpy.context.scene.objects:
            o.select_set(o == ob)

        bpy.context.view_layer.objects.active = ob
        path = os.path.join(OUT, name + ".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT")
        render(ob, name)
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        print("PIECE", name, os.path.getsize(path), len(me.polygons), "gltf_min", (round(lo[0], 3), round(lo[2], 3), round(-hi[1], 3)), "gltf_max", (round(hi[0], 3), round(hi[2], 3), round(-lo[1], 3)))
        bpy.data.objects.remove(ob, do_unlink=True)


def cull_hidden(me):
    from mathutils.bvhtree import BVHTree

    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    hidden = set()

    for p in me.polygons:
        n = p.normal
        pts = [p.center] + [me.vertices[v].co * 0.7 + p.center * 0.3 for v in p.vertices]
        covered = True

        for q in pts:
            loc, _, idx, dist = tree.ray_cast(q + n * 0.002, n, 0.015)

            if loc is None:
                covered = False
                break

        if covered:
            hidden.add(p.index)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in hidden], context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    print("CULL", len(hidden))


def bake_ao(me, zmin):
    from mathutils.bvhtree import BVHTree

    verts = [v.co.copy() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    g = len(verts)
    pad = 30.0
    verts += [Vector((lo.x - pad, lo.y - pad, zmin)), Vector((hi.x + pad, lo.y - pad, zmin)), Vector((hi.x + pad, hi.y + pad, zmin)), Vector((lo.x - pad, hi.y + pad, zmin))]
    polys.append((g, g + 1, g + 2, g + 3))
    tree = BVHTree.FromPolygons(verts, polys)
    rng = random.Random(7)
    dirs = []

    while len(dirs) < 24:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))

        if 0.05 < d.length <= 1:
            dirs.append(d.normalized())

    attr = me.color_attributes["Col"]
    reach = 1.6

    cache = {}

    for p in me.polygons:
        n = p.normal
        key_n = (round(n.x, 2), round(n.y, 2), round(n.z, 2))

        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            key = (vi, key_n)

            if key not in cache:
                origin = me.vertices[vi].co * 0.92 + p.center * 0.08 + n * 0.01
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
            k = 1 - 0.4 * occ
            c = attr.data[li].color
            attr.data[li].color = (c[0] * k, c[1] * k * (1 - 0.03 * occ), c[2] * k * (1 - 0.07 * occ), c[3])


def render(ob, name):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = False
    sh.show_shadows = True
    sh.shadow_intensity = 0.25
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.62, 0.72, 0.8)
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


def B(u, v, y):
    return (-u, v, y)


def house(name, w, d, floors, var):
    reset()
    top = STOREY * floors
    k = Kit(top + SLAB + 1.0, seed=var * 17 + floors)
    plaster = PLASTER[var % len(PLASTER)]
    shutter = SHUTTER[var % len(SHUTTER)]
    cloth = CLOTH[(var * 2 + 1) % len(CLOTH)]
    trim = tuple(min(c * 1.05, 1) for c in plaster)
    plinth = (plaster[0] * 0.78, plaster[1] * 0.72, plaster[2] * 0.66)
    band = BAND[var % len(BAND)]
    band_edge = tuple(c * 0.72 for c in band)
    tag(plaster, 1)
    tag(trim, 3)
    tag(plinth, 3)
    tag(band, 2)
    tag(band_edge, 2)
    dv = d / 2

    def ub(ua, v0, ubb, v1, y0, y1, col, bevel=0.0, grad=True):
        a = B(ua, v0 - dv, y0)
        b = B(ubb, v1 - dv, y1)

        return k.box((min(a[0], b[0]), min(a[1], b[1]), y0), (max(a[0], b[0]), max(a[1], b[1]), y1), col, bevel, grad)

    def opening(along_u, c, ow, lo, hi, cpos, y):
        if along_u:
            return ub(c - ow / 2, cpos - 0.5, c + ow / 2, cpos + T + 0.5, y + lo, y + hi, plaster)

        return ub(cpos - 0.5, c - ow / 2, cpos + T + 0.5, c + ow / 2, y + lo, y + hi, plaster)

    def frame_u(c, ow, lo, hi, v_face, out, door):
        a = c - ow / 2
        z = c + ow / 2
        v0, v1 = (v_face - 0.09, v_face) if out < 0 else (v_face, v_face + 0.09)
        s0, s1 = (v_face - 0.17, v_face + 0.05) if out < 0 else (v_face - 0.05, v_face + 0.17)
        ub(a - 0.15, v0, a, v1, lo, hi, WOOD, 0, False)
        ub(z, v0, z + 0.15, v1, lo, hi, WOOD, 0, False)
        ub(a - 0.24, v0 - (0.03 if out < 0 else 0), z + 0.24, v1 + (0.03 if out > 0 else 0), hi, hi + 0.2, WOOD_DARK, 0.02, False)

        if door:
            paint = DOOR[var % len(DOOR)]

            for side in (-1, 1):
                la = a - 0.17 - 0.8 if side < 0 else z + 0.17
                ub(la, v0 - 0.05, la + 0.8, v0 - 0.0, lo + 0.02, hi - 0.06, paint, 0, False)

            ub(a - 0.2, -0.55, z + 0.2, 0, -0.1, 0.1, plinth, 0.02, False)
            ub(z + 0.95, v0 - 0.22, z + 1.13, v0 - 0.04, hi - 0.35, hi - 0.05, WOOD_DARK, 0, False)
            ub(z + 0.97, v0 - 0.2, z + 1.11, v0 - 0.06, hi - 0.33, hi - 0.15, LAMP, 0, False)

            return

        ub(a - 0.12, s0, z + 0.12, s1, lo - 0.1, lo, trim, 0, False)

        for side in (-1, 1):
            sa = a - 0.52 if side < 0 else z + 0.16
            ub(sa, v0, sa + 0.36, v1, lo + 0.03, hi - 0.03, shutter, 0, False)

    def recess(c, ow, lo, hi, v_out, y, depth):
        if v_out <= 0:
            return ub(c - ow / 2, -0.5, c + ow / 2, depth, y + lo, y + hi, plaster)

        return ub(c - ow / 2, d - depth, c + ow / 2, d + 0.5, y + lo, y + hi, plaster)

    def blind(c, ow, lo, hi, v_face, out, depth):
        back = v_face + depth if out < 0 else v_face - depth
        ub(c - ow / 2, min(back, back - 0.02 * out), c + ow / 2, max(back, back - 0.02 * out), lo, hi, RECESS, 0, False)

        for j in range(4):
            gx = c - ow / 2 + ow * (j + 0.5) / 4
            ub(gx - 0.02, min(v_face, v_face - 0.06 * out), gx + 0.02, max(v_face, v_face - 0.06 * out) , lo + 0.02, hi - 0.02, IRON, 0, False)

        for gy in (lo + (hi - lo) * 0.33, lo + (hi - lo) * 0.66):
            ub(c - ow / 2, min(v_face, v_face - 0.06 * out), c + ow / 2, max(v_face, v_face - 0.06 * out), gy - 0.02, gy + 0.02, IRON, 0, False)

        if out > 0:
            frame_u(c, ow, lo, hi, v_face, out, False)

            return

        a_, z_ = c - ow / 2, c + ow / 2
        ub(a_ - 0.15, v_face - 0.09, a_, v_face, lo, hi, STONE, 0, False)
        ub(z_, v_face - 0.09, z_ + 0.15, v_face, lo, hi, STONE, 0, False)
        ub(a_ - 0.22, v_face - 0.12, z_ + 0.22, v_face, hi, hi + 0.18, STONE, 0.02, False)
        ub(a_ - 0.14, v_face - 0.17, z_ + 0.14, v_face, lo - 0.1, lo, STONE, 0.02, False)

    def frame_v(c, ow, lo, hi, u_face, out):
        a = c - ow / 2
        z = c + ow / 2
        u0, u1 = (u_face - 0.09, u_face) if out < 0 else (u_face, u_face + 0.09)
        s0, s1 = (u_face - 0.17, u_face + 0.05) if out < 0 else (u_face - 0.05, u_face + 0.17)
        ub(u0, a - 0.15, u1, a, lo, hi, WOOD, 0, False)
        ub(u0, z, u1, z + 0.15, lo, hi, WOOD, 0, False)
        ub(u0, a - 0.24, u1, z + 0.24, hi, hi + 0.2, WOOD_DARK, 0.02, False)
        ub(s0, a - 0.12, s1, z + 0.12, lo - 0.1, lo, trim, 0, False)

        for side in (-1, 1):
            sa = a - 0.52 if side < 0 else z + 0.16
            ub(u0, sa, u1, sa + 0.36, lo + 0.03, hi - 0.03, shutter, 0, False)

    ub(-w / 2 - 0.08, -0.08, w / 2 + 0.08, d + 0.08, -0.6, 0.5, plinth, 0.03)
    ub(-w / 2 + 0.01, 0.01, w / 2 - 0.01, d - 0.01, -0.6, 0.12, rgb(178, 146, 100), 0, False)

    first_hole = (-w / 2 + T, d - T - STAIR_W, -w / 2 + T + STAIR_LEN, d - T)
    second_hole = (w / 2 - T - STAIR_LEN, T, w / 2 - T, T + STAIR_W)

    for level in range(floors):
        yb = STOREY * level + (0.12 if level == 0 else SLAB)
        ye = STOREY * (level + 1)
        y_base = STOREY * level + (0.12 if level == 0 else SLAB)

        walls = [
            (ub(-w / 2, 0, w / 2, T, yb, ye, plaster), True, 0),
            (ub(-w / 2, d - T, w / 2, d, yb, ye, plaster), True, d - T),
            (ub(-w / 2, T, -w / 2 + T, d - T, yb, ye, plaster), False, -w / 2),
            (ub(w / 2 - T, T, w / 2, d - T, yb, ye, plaster), False, w / 2 - T),
        ]

        for wall, along_u, cpos in walls:
            cuts = []

            if along_u and cpos == 0:
                if level == 0:
                    cuts.append(opening(True, 0.4, 1.6, 0, 2.5, cpos, yb))

                    if w >= 7:
                        cuts.append(recess(-w / 4 - 0.45, 1.0, 1.15, 2.25, 0, yb, 0.22))
                else:
                    cuts.append(opening(True, -w / 4, 1.1, 1.0, 1.9, cpos, yb))
                    cuts.append(opening(True, w / 4, 1.1, 1.0, 1.9, cpos, yb))
            elif along_u:
                if level == 0:
                    cuts.append(recess(-w / 4, 1.0, 1.15, 2.25, 1, yb, 0.22))
                    cuts.append(recess(w / 4, 1.0, 1.15, 2.25, 1, yb, 0.22))

                if level > 0:
                    cuts.append(opening(True, -w / 4, 1.1, 1.0, 1.9, cpos, yb))
                    cuts.append(opening(True, w / 4, 1.1, 1.0, 1.9, cpos, yb))
            else:
                cuts.append(opening(False, d / 2, 1.0, 1.1, 2.0, cpos, yb))

            bmw = bmesh.new()
            bmw.from_mesh(wall.data)
            vert_edges = [e for e in bmw.edges if abs((e.verts[0].co - e.verts[1].co).z) > 0.5]
            bmesh.ops.bevel(bmw, geom=vert_edges, offset=0.06, segments=1, affect="EDGES")
            bmw.to_mesh(wall.data)
            bmw.free()

            if cuts:
                k.subtract(wall, cuts)

        if level == 0:
            frame_u(0.4, 1.6, y_base, y_base + 2.5, 0, -1, True)

            if w >= 7:
                blind(-w / 4 - 0.45, 1.0, y_base + 1.03, y_base + 2.13, 0, -1, 0.22)

            for c in (-w / 4, w / 4):
                blind(c, 1.0, y_base + 1.03, y_base + 2.13, d, 1, 0.22)
        else:
            for c in (-w / 4, w / 4):
                frame_u(c, 1.1, y_base + 1.0, y_base + 1.9, 0, -1, False)
                frame_u(c, 1.1, y_base + 1.0, y_base + 1.9, d, 1, False)

        frame_v(d / 2, 1.0, y_base + 1.1, y_base + 2.0, -w / 2, -1)
        frame_v(d / 2, 1.0, y_base + 1.1, y_base + 2.0, w / 2, 1)

        steps = 12
        du = STAIR_LEN / steps
        up = level == 0
        hole = first_hole if level == 0 else second_hole
        ua = hole[0]

        prof = [(ua, yb)]

        for i in range(steps):
            st_top = yb + (ye + SLAB - yb) * (i + 1) / steps
            if up:
                prof += [(ua + i * du, st_top), (ua + (i + 1) * du, st_top)]
            else:
                prof += [(ua + STAIR_LEN - (i + 1) * du, st_top), (ua + STAIR_LEN - i * du, st_top)]

        if up:
            prof.append((ua + STAIR_LEN, yb))
        else:
            prof = [(ua + STAIR_LEN, yb)] + prof[1:] + [(ua, yb)]
            prof = list(reversed(prof))

        bm = bmesh.new()
        sides = []

        for vv in (hole[1], hole[1] + STAIR_W):
            sides.append([bm.verts.new(B(pu_, vv - dv, py_)) for pu_, py_ in prof])

        n_p = len(prof)

        for i in range(n_p):
            bm.faces.new((sides[0][i], sides[0][(i + 1) % n_p], sides[1][(i + 1) % n_p], sides[1][i]))

        bm.faces.new(sides[0])
        bm.faces.new(list(reversed(sides[1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        k.mesh(bm, rgb(206, 176, 118), 0)

        slab_col = plaster if level + 1 == floors else rgb(178, 146, 100)

        for p in ((-w / 2, 0, w / 2, hole[1]), (-w / 2, hole[3], w / 2, d), (-w / 2, hole[1], hole[0], hole[3]), (hole[2], hole[1], w / 2, hole[3])):
            ub(p[0], p[1], p[2], p[3], ye, ye + SLAB, slab_col, 0, False)

        if level + 1 < floors:
            ub(-w / 2 - 0.06, -0.06, w / 2 + 0.06, 0, ye + 0.02, ye + 0.22, trim, 0.02)
            ub(-w / 2 - 0.06, d, w / 2 + 0.06, d + 0.06, ye + 0.02, ye + 0.22, trim, 0.02)
            ub(-w / 2 - 0.06, 0, -w / 2, d, ye + 0.02, ye + 0.22, trim, 0.02)
            ub(w / 2, 0, w / 2 + 0.06, d, ye + 0.02, ye + 0.22, trim, 0.02)

    rt = top + SLAB

    for p in ((-w / 2, 0, w / 2, 0.25), (-w / 2, d - 0.25, w / 2, d), (-w / 2, 0.25, -w / 2 + 0.25, d - 0.25), (w / 2 - 0.25, 0.25, w / 2, d - 0.25)):
        ub(p[0], p[1], p[2], p[3], rt, rt + 0.85, plaster, 0.03)
        ub(p[0] - 0.06, p[1] - 0.06, p[2] + 0.06, p[3] + 0.06, rt + 0.85, rt + 0.98, trim, 0.025)

    for cu in (-w / 2, w / 2 - 0.55):
        for cv in (0, d - 0.55):
            ub(cu - 0.04, cv - 0.04, cu + 0.59, cv + 0.59, rt + 0.98, rt + 1.38, plaster, 0.03)
            ub(cu - 0.08, cv - 0.08, cu + 0.63, cv + 0.63, rt + 1.38, rt + 1.48, trim, 0.02)

    ub(-w / 2 + 0.6, -0.03, w / 2 - 0.6, 0.0, rt + 0.38, rt + 0.56, TILE[var % 2 * 2], 0, False)
    n_t = int((w - 1.4) / 0.8)

    for j in range(n_t):
        tu = -w / 2 + 0.7 + j * (w - 1.4) / n_t + 0.25
        ub(tu, -0.06, tu + 0.22, -0.03, rt + 0.36, rt + 0.58, TILE[(j + var) % len(TILE)] if j % 2 == 0 else TILE[1], 0, False)

    u = -w / 2 + 0.6

    while u < w / 2 - 0.4:
        for v0, v1 in ((-0.42, 0.06), (d - 0.06, d + 0.42)):
            ub(u - 0.09, v0, u + 0.09, v1, top - 0.28, top - 0.1, WOOD, 0, False)

        u += 0.9

    lo_y = 2.62
    ub(-0.85, -1.15, -0.75, -1.05, 0.12, lo_y, WOOD, 0.01, False)
    ub(1.55, -1.15, 1.65, -1.05, 0.12, lo_y, WOOD, 0.01, False)
    bm = bmesh.new()
    pts = [B(-0.95, -1.25 - dv, lo_y), B(1.75, -1.25 - dv, lo_y), B(1.75, 0.0 - dv, 2.95), B(-0.95, 0.0 - dv, 2.95)]
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.05)
    k.mesh(bm, cloth, 0, grad=False)

    for j in range(5):
        x = -0.95 + j * 0.675
        bm = bmesh.new()
        a = B(x, -1.25 - dv, lo_y)
        b = B(x + 0.34, -1.25 - dv, lo_y)
        c = B(x + 0.17, -1.25 - dv, lo_y - 0.22)
        vs = [bm.verts.new(p) for p in (a, b, c)]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
        k.mesh(bm, cloth, 0, grad=False)

    rng = k.rng

    if var % 3 != 2:
        cu, cv = w / 2 - 1.3, 1.2

        for o in ((-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)):
            ub(cu + o[0] - 0.05, cv + o[1] - 0.05, cu + o[0] + 0.05, cv + o[1] + 0.05, rt, rt + 0.6, WOOD_DARK, 0, False)

        k.cyl(B(cu, cv - dv, rt + 0.6), B(cu, cv - dv, rt + 1.7), 0.55, TANK, 10, bevel=0.03)
        k.cyl(B(cu, cv - dv, rt + 1.7), B(cu, cv - dv, rt + 1.82), 0.2, TANK, 8)

    pu, pv = w / 2 - 0.9, d - 0.9
    k.cyl(B(pu, pv - dv, rt), B(pu, pv - dv, rt + 0.5), 0.26, POT, 8, r2=0.32)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.42)

    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.y, v.co.z * 1.2)) + Vector(B(pu, pv - dv, rt + 0.85))

    k.mesh(bm, LEAF, 0, grad=False)

    if var % 2 == 0:
        ru, rv = -w / 2 + 1.6, d / 2
        ub(ru - 1.0, rv - 0.7, ru + 1.0, rv + 0.7, rt, rt + 0.03, CLOTH[(var + 3) % len(CLOTH)], 0, False)

    ub(-w / 2 + 0.5, 0.3, -w / 2 + 1.2, 1.0, rt, rt + 0.6, WOOD, 0.03)

    bind_details(k, ub, w, d, floors, var, plaster, band, band_edge, top, rt)

    k.finish(name, zmin=-0.6)


def bind_details(k, ub, w, d, floors, var, plaster, band, band_edge, top, rt):
    tag(STONE, 3)
    tag(IRON, 8)
    tag(RECESS, 9)

    worn = tuple(min(c * 1.12 + 0.03, 1) for c in band)
    tag(worn, 2)

    for a, b in ((-w / 2, -0.55), (1.3, w / 2)):
        ub(a, -0.02, b, 0, 0.5, 1.06, band, 0, False)
        ub(a + 0.4, -0.025, a + 0.95, 0, 0.62, 0.9, worn, 0, False)
        ub(a, -0.035, b, 0, 1.06, 1.12, band_edge, 0, False)

    ub(-w / 2, d, w / 2, d + 0.02, 0.5, 1.06, band, 0, False)
    ub(-w / 2, d, w / 2, d + 0.035, 1.06, 1.12, band_edge, 0, False)

    for u0 in (-w / 2 - 0.02, w / 2):
        ub(u0, 0, u0 + 0.02, d, 0.5, 1.06, band, 0, False)
        ub(u0 - 0.015 if u0 < 0 else u0, 0, u0 + 0.02 + (0.0 if u0 < 0 else 0.015), d, 1.06, 1.12, band_edge, 0, False)

    cx, top_y, r = 0.4, 2.82, 0.86
    n = 9

    for j in range(n):
        a0 = math.pi * j / n
        a1 = math.pi * (j + 1) / n
        x0, x1 = cx + math.cos(a0) * r, cx + math.cos(a1) * r
        y0, y1 = top_y + math.sin(a0) * r * 0.55, top_y + math.sin(a1) * r * 0.55
        ub(min(x0, x1) - 0.06, -0.07, max(x0, x1) + 0.06, 0, min(y0, y1) - 0.06, max(y0, y1) + 0.1, STONE, 0, False)

    ub(cx - r * 0.85, -0.03, cx + r * 0.85, 0, top_y, top_y + r * 0.42, DOOR[var % len(DOOR)], 0, False)
    ub(cx - 1.15, -0.95, cx + 1.15, -0.55, -0.28, -0.04, STONE, 0.02)

    if floors >= 2:
        c = -w / 4
        yb = STOREY + SLAB
        ub(c - 0.95, -0.78, c + 0.95, 0, yb + 0.78, yb + 0.95, STONE, 0.02)

        for j in range(3):
            bx = c - 0.7 + j * 0.7
            ub(bx - 0.06, -0.5, bx + 0.06, 0, yb + 0.45, yb + 0.78, WOOD_DARK, 0, False)

        ub(c - 0.92, -0.76, c + 0.92, -0.7, yb + 1.68, yb + 1.76, IRON, 0, False)

        for j in range(13):
            px = c - 0.88 + j * (1.76 / 12)
            ub(px - 0.015, -0.75, px + 0.015, -0.71, yb + 0.95, yb + 1.68, IRON, 0, False)

        for e in (-1, 1):
            ub(c + e * 0.9 - 0.015, -0.76, c + e * 0.9 + 0.015, 0, yb + 0.95, yb + 1.68, IRON, 0, False)

        lu = w / 2 - 0.9
        ly = STOREY + 2.6
        ub(lu - 0.03, -0.55, lu + 0.03, 0, ly, ly + 0.05, IRON, 0, False)
        k.cyl(B(lu, -0.5 - d / 2, ly), B(lu, -0.5 - d / 2, ly - 0.25), 0.012, IRON, 4)
        ub(lu - 0.12, -0.62, lu + 0.12, -0.38, ly - 0.55, ly - 0.25, IRON, 0, False)
        ub(lu - 0.09, -0.59, lu + 0.09, -0.41, ly - 0.52, ly - 0.28, LAMP, 0, False)

    pu = w / 2 - 0.16
    k.cyl(B(pu, -0.12 - d / 2, 0.05), B(pu, -0.12 - d / 2, top + 0.2), 0.055, IRON, 6)

    for py in (0.9, top * 0.5, top - 0.2):
        ub(pu - 0.08, -0.14, pu + 0.08, 0, py, py + 0.05, IRON, 0, False)

    av = d * 0.72
    ay = STOREY * floors - 1.05
    ub(-w / 2 - 0.46, av - 0.42, -w / 2, av + 0.42, ay, ay + 0.52, rgb(214, 214, 206), 0.02)

    for j in range(6):
        gy = ay + 0.08 + j * 0.065
        ub(-w / 2 - 0.47, av - 0.36, -w / 2 - 0.45, av + 0.36, gy, gy + 0.025, IRON, 0, False)

    for o in (-0.25, 0.25):
        ub(-w / 2 - 0.4, av + o - 0.03, -w / 2, av + o + 0.03, ay - 0.1, ay, IRON, 0, False)

    if var % 2 == 1:
        sv = d * 0.22
        ub(w / 2, sv - 0.62, w / 2 + 0.06, sv + 0.62, 2.25, 2.8, WOOD_DARK, 0, False)
        ub(w / 2 + 0.06, sv - 0.55, w / 2 + 0.08, sv + 0.55, 2.3, 2.75, SAFFRON if var % 4 == 1 else TEAL, 0, False)

        for j in range(4):
            dv_ = sv - 0.42 + j * 0.28
            ub(w / 2 + 0.08, dv_ - 0.06, w / 2 + 0.095, dv_ + 0.06, 2.4, 2.65, TERRA if var % 4 == 1 else SAFFRON, 0, False)

    if var % 3 == 0:
        ub(-w / 2 + 0.9, -0.06, -w / 2 + 2.3, -0.02, rt - 0.95, rt + 0.92, CLOTH[(var + 2) % len(CLOTH)], 0, False)

        for j in range(4):
            yy = rt - 0.8 + j * 0.45
            ub(-w / 2 + 0.9, -0.075, -w / 2 + 2.3, -0.06, yy, yy + 0.08, SAFFRON if j % 2 == 0 else TEAL, 0, False)

    for side in (-1, 1):
        pu_ = cx + side * 1.45 if side > 0 else cx - 1.5
        k.cyl(B(pu_, -0.45 - d / 2, -0.1), B(pu_, -0.45 - d / 2, 0.45), 0.2, POT, 8, r2=0.26)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.3)

        for v in bm.verts:
            v.co = Vector((v.co.x, v.co.y, v.co.z * 1.3)) + Vector(B(pu_, -0.45 - d / 2, 0.75))

        k.mesh(bm, LEAF, 0, grad=False)

    if floors >= 2 or var % 2 == 0:
        gu, gv = -w / 2 + 1.2, d - 1.6

        for o in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)):
            ub(gu + o[0] - 0.05, gv + o[1] - 0.05, gu + o[0] + 0.05, gv + o[1] + 0.05, rt, rt + 2.2, WOOD_DARK, 0, False)

        for o in (-0.9, 0.9):
            ub(gu - 1.0, gv + o - 0.05, gu + 1.0, gv + o + 0.05, rt + 2.2, rt + 2.3, WOOD, 0, False)

        for j in range(7):
            pu2 = gu - 0.95 + j * 0.32
            ub(pu2 - 0.03, gv - 1.0, pu2 + 0.03, gv + 1.0, rt + 2.3, rt + 2.36, WOOD, 0, False)


def buildings():
    variants = [(7.2, 6.6, 1), (8.4, 7.4, 1), (7.6, 7.0, 2), (8.6, 7.8, 2), (8.8, 6.6, 1), (7.0, 7.2, 2)]

    for i, (w, d, f) in enumerate(variants):
        name = f"house_{i}"

        if ONLY and name not in ONLY:
            continue

        house(name, w, d, f, i)
        print("HOUSE", name, w, d, f)


def rocks():
    for i in range(6):
        name = f"rocks_{i}"

        if ONLY and name not in ONLY:
            continue

        reset()
        rng = random.Random(i * 31 + 5)
        k = Kit(2.6 + i * 0.3, seed=i)
        n = 3 + i % 3

        for j in range(n):
            ang = j / n * 6.28 + rng.random()
            dist = 0 if j == 0 else rng.uniform(1.0, 2.0)
            s = 1.6 if j == 0 else rng.uniform(0.5, 1.0)
            k.rock((math.cos(ang) * dist, math.sin(ang) * dist, 0), (s * rng.uniform(1.0, 1.4), s * rng.uniform(0.8, 1.2), s * rng.uniform(1.1, 1.7)), 1.0, seed=i * 7 + j, flat=0.9)

        k.finish(name, zmin=-0.3)


def mesas():
    for i in range(3):
        name = f"mesa_{i}"

        if ONLY and name not in ONLY:
            continue

        reset()
        rng = random.Random(i * 13 + 2)
        layers = 4 + i % 2
        height = 26 + i * 6
        k = Kit(height, seed=i)
        base_r = 22 + i * 6
        n = 9

        for L in range(layers):
            z0 = L * height / layers
            z1 = (L + 1) * height / layers
            r0 = base_r * (1 - L * 0.12) * (1.15 if L == 0 else 1)
            r1 = base_r * (1 - L * 0.12) * (0.92 if L < layers - 1 else 0.9)
            bm = bmesh.new()
            bottom = []
            topv = []

            for j in range(n):
                a = j / n * 6.283 + i
                wob = 1 + (noise.noise(Vector((math.cos(a) * 2 + i, math.sin(a) * 2, L * 0.7))) * 0.35)
                sx = 1.35 if i != 1 else 1.0
                bottom.append(bm.verts.new((math.cos(a) * r0 * wob * sx, math.sin(a) * r0 * wob, z0)))
                topv.append(bm.verts.new((math.cos(a) * r1 * wob * sx * 0.97, math.sin(a) * r1 * wob * 0.97, z1)))

            for j in range(n):
                bm.faces.new((bottom[j], bottom[(j + 1) % n], topv[(j + 1) % n], topv[j]))

            bm.faces.new(list(reversed(bottom)))
            bm.faces.new(topv)
            ob = k.mesh(bm, (0, 0, 0))
            ob["strata"] = 1.0

        for j in range(5):
            a = rng.uniform(0, 6.28)
            rr = base_r * rng.uniform(1.0, 1.3)
            k.rock((math.cos(a) * rr, math.sin(a) * rr, 0), (rng.uniform(3, 5), rng.uniform(2.5, 4), rng.uniform(3, 5)), 1.0, seed=i * 11 + j, flat=0.8)

        k.finish(name, zmin=0)


def stall():
  for sv in range(3):
    name = f"stall_{sv}"

    if ONLY and name not in ONLY:
        continue

    reset()
    k = Kit(3.0, seed=4)

    for x in (-1.4, 1.4):
        for y in (-0.9, 0.9):
            k.box((x - 0.07, y - 0.07, 0), (x + 0.07, y + 0.07, 2.5 if y > 0 else 2.2), WOOD, 0, False)

    k.box((-1.5, -1.0, 0.75), (1.5, 0.2, 0.9), WOOD, 0.02, False)
    k.box((-1.4, -0.95, 0.0), (1.4, 0.1, 0.75), WOOD_DARK, 0.02)

    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-1.65, -1.3, 2.15), (1.65, -1.3, 2.15), (1.65, 1.1, 2.6), (-1.65, 1.1, 2.6))]
    bm.faces.new(vs)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.05)
    k.mesh(bm, CLOTH[[0, 1, 2][sv]], 0, grad=False)

    for j in range(6):
        x = -1.65 + j * 0.55
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in ((x, -1.3, 2.15), (x + 0.275, -1.3, 2.15), (x + 0.1375, -1.3, 1.95))]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
        k.mesh(bm, CLOTH[[2, 3, 0][sv]] if j % 2 else CLOTH[[0, 1, 2][sv]], 0, grad=False)

    goods = [rgb(214, 164, 72), rgb(196, 98, 62), rgb(112, 146, 70), rgb(226, 196, 142)]

    for j in range(5):
        x = -1.1 + j * 0.55
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.2)

        for v in bm.verts:
            v.co = Vector((v.co.x + x, v.co.y - 0.4, v.co.z * 0.7 + 1.02))

        k.mesh(bm, goods[j % len(goods)], 0, grad=False)

    k.blob(2.6, 1.7, 0.3, -0.2)
    k.cyl((1.9, 0.2, 0), (1.9, 0.2, 0.7), 0.3, POT, 8, r2=0.22)
    k.cyl((2.3, -0.4, 0), (2.3, -0.4, 0.5), 0.22, rgb(150, 82, 52), 8, r2=0.3)
    k.finish(name, zmin=0)


def palms():
    for pv in range(2):
        name = f"palm_{pv}"

        if ONLY and name not in ONLY:
            continue

        reset()
        H = 7.5 if pv == 0 else 5.0
        k = Kit(H + 1.5, seed=pv + 20)
        rng = random.Random(pv + 3)
        segs = 9 if pv == 0 else 7
        lean = 1.1 if pv == 0 else 0.7
        bark = [rgb(132, 100, 70), rgb(112, 84, 60)]
        prev = Vector((0, 0, -0.3))
        top = prev

        for j in range(segs):
            t1 = (j + 1) / segs
            p1 = Vector((lean * t1 * t1, 0, -0.3 + (H + 0.3) * t1))
            r0 = 0.3 - 0.13 * j / segs
            ob = k.cyl(prev, p1, r0, bark[j % 2], 6, r2=r0 * 0.8)
            ob["grad"] = 1
            prev = p1
            top = p1

        k.cyl(top - Vector((0, 0, 0.15)), top + Vector((0, 0, 0.35)), 0.26, rgb(98, 112, 66), 6, r2=0.12)
        k.blob(1.6 if pv == 0 else 1.2, cx=0.3)

        for j in range(3):
            a = j * 2.1 + 0.4
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.14)

            for v in bm.verts:
                v.co += top + Vector((math.cos(a) * 0.24, math.sin(a) * 0.24, -0.2))

            k.mesh(bm, rgb(120, 88, 52), 0, grad=False)

        greens = [rgb(63, 90, 58), rgb(84, 112, 66), rgb(111, 138, 78)]
        n_f = 8 if pv == 0 else 7

        for layer in range(2):
            for j in range(n_f):
                a = j / n_f * 6.283 + layer * 0.4 + rng.uniform(-0.12, 0.12)
                L = (2.9 if pv == 0 else 2.2) * (1 - 0.18 * layer) * rng.uniform(0.9, 1.1)
                droop = (0.9 if layer == 0 else 0.35) * rng.uniform(0.8, 1.2)
                dirv = Vector((math.cos(a), math.sin(a), 0))
                side = Vector((-math.sin(a), math.cos(a), 0))
                bm = bmesh.new()
                n_s = 4
                mid = []
                left = []
                right = []

                for sgi in range(n_s + 1):
                    t = sgi / n_s
                    c = top + dirv * (L * t) + Vector((0, 0, 0.25 + layer * 0.2 + 0.6 * t - (droop + 0.6) * t * t))
                    wdt = 0.45 * math.sin(math.pi * min(t * 1.15, 1)) + 0.04
                    mid.append(bm.verts.new(c + Vector((0, 0, 0.06))))
                    left.append(bm.verts.new(c + side * wdt - Vector((0, 0, 0.12 * t))))
                    right.append(bm.verts.new(c - side * wdt - Vector((0, 0, 0.12 * t))))

                for sgi in range(n_s):
                    bm.faces.new((mid[sgi], mid[sgi + 1], left[sgi + 1], left[sgi]))
                    bm.faces.new((mid[sgi], right[sgi], right[sgi + 1], mid[sgi + 1]))

                bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.025)
                k.mesh(bm, greens[(j + layer) % 3], 0, grad=False)

        k.finish(name, zmin=-0.3)


def camp():
    if not ONLY or "tent" in ONLY:
        reset()
        k = Kit(2.6, seed=31)
        fabric = [rgb(110, 88, 70), rgb(200, 182, 146)]
        L, W, H, E = 2.6, 2.0, 2.2, 1.1

        for x in (-L, 0, L):
            k.cyl((x, 0, 0), (x, 0, H), 0.06, WOOD_DARK, 5)

        for sgn in (-1, 1):
            for x in (-L, L):
                k.cyl((x, sgn * W, 0), (x, sgn * W, E), 0.05, WOOD_DARK, 5)

        strips = 6

        for sgn in (-1, 1):
            for j in range(strips):
                x0 = -L - 0.2 + j * (2 * L + 0.4) / strips
                x1 = x0 + (2 * L + 0.4) / strips
                bm = bmesh.new()
                vs = [bm.verts.new(p) for p in ((x0, 0, H + 0.05), (x1, 0, H + 0.05), (x1, sgn * (W + 0.3), E - 0.1), (x0, sgn * (W + 0.3), E - 0.1))]
                bm.faces.new(vs if sgn > 0 else list(reversed(vs)))
                bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.04)
                k.mesh(bm, fabric[j % 2], 0, grad=False)

        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in ((-L - 0.1, -W, 0.0), (-L - 0.1, W, 0.0), (-L - 0.1, 0, H))]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.04)
        k.mesh(bm, fabric[0], 0, grad=False)
        k.blob(3.4, 2.8, z=0.012)
        k.box((-1.6, -1.2, 0), (1.2, 1.0, 0.03), CLOTH[0], 0, False)
        k.box((-1.0, -0.6, 0.03), (0.6, 0.4, 0.06), CLOTH[2], 0, False)
        k.finish("tent", zmin=0)

    if not ONLY or "truck_wreck" in ONLY:
        reset()
        k = Kit(2.2, seed=41)
        paint = rgb(104, 128, 120)
        rust = rgb(150, 96, 66)
        dark = rgb(52, 50, 48)
        k.blob(3.2, 1.8)
        k.box((-2.4, -0.95, 0.55), (2.3, 0.95, 0.75), dark, 0.03)
        k.box((0.9, -0.95, 0.75), (2.4, 0.95, 1.35), paint, 0.06)
        k.box((0.95, -0.9, 1.35), (1.25, 0.9, 1.4), paint, 0.02)
        k.box((-0.4, -0.95, 0.75), (0.9, 0.95, 2.05), paint, 0.06)
        k.box((0.55, -0.85, 1.45), (0.95, 0.85, 1.95), rgb(70, 82, 86), 0.01)
        k.box((-2.5, -1.0, 0.75), (-0.45, -0.88, 1.35), rust, 0.02)
        k.box((-2.5, 0.88, 0.75), (-0.45, 1.0, 1.35), paint, 0.02)
        k.box((-2.55, -1.0, 0.75), (-2.43, 1.0, 1.3), rust, 0.02)
        k.box((-2.3, -0.85, 0.75), (-0.5, 0.85, 0.82), rgb(118, 80, 50), 0, False)
        k.box((2.35, -0.9, 0.6), (2.5, 0.9, 0.9), dark, 0.02)

        for x, sink in ((-1.6, 0.0), (1.6, 0.25)):
            for sgn in (-1, 1):
                k.cyl((x, sgn * 0.85, 0.45 - sink), (x, sgn * 1.12, 0.45 - sink), 0.45, dark, 8)
                k.cyl((x, sgn * 1.12, 0.45 - sink), (x, sgn * 1.14, 0.45 - sink), 0.22, rgb(120, 118, 110), 8)

        k.box((-1.2, -0.5, 0.82), (-0.6, 0.1, 1.3), WOOD, 0.03)
        k.cyl((-1.8, 0.4, 0.82), (-1.8, 0.4, 1.6), 0.3, rgb(112, 124, 92), 8)
        k.finish("truck_wreck", zmin=0)


def hangar():
    if ONLY and "hangar" not in ONLY:
        return

    reset()
    k = Kit(7, seed=51)
    R, L = 7.0, 22.0
    metal = [rgb(150, 146, 132), rgb(138, 134, 122)]
    n = 10

    for j in range(n):
        a0 = math.pi * j / n
        a1 = math.pi * (j + 1) / n
        bm = bmesh.new()
        pts = [(-L / 2, math.cos(a0) * R, math.sin(a0) * R * 0.95), (L / 2, math.cos(a0) * R, math.sin(a0) * R * 0.95), (L / 2, math.cos(a1) * R, math.sin(a1) * R * 0.95), (-L / 2, math.cos(a1) * R, math.sin(a1) * R * 0.95)]
        vs = [bm.verts.new(p) for p in pts]
        bm.faces.new(list(reversed(vs)))
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.12)
        k.mesh(bm, metal[j % 2], 0)

    for x in (-L / 2, -L / 4, 0, L / 4, L / 2 - 0.25):
        for j in range(n):
            a0 = math.pi * j / n
            a1 = math.pi * (j + 1) / n
            k.cyl((x, math.cos(a0) * (R + 0.08), math.sin(a0) * (R + 0.08) * 0.95), (x, math.cos(a1) * (R + 0.08), math.sin(a1) * (R + 0.08) * 0.95), 0.1, rgb(112, 108, 98), 4)

    bm = bmesh.new()
    back = [bm.verts.new((L / 2 - 0.1, math.cos(math.pi * j / n) * R, math.sin(math.pi * j / n) * R * 0.95)) for j in range(n + 1)]
    bm.faces.new(back)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.15)
    k.mesh(bm, PLASTER[3], 0)

    for sgn in (-1, 1):
        k.box((-L / 2 - 0.3, sgn * (R - 1.2) - 0.25, 0), (-L / 2 + 0.1, sgn * (R - 1.2) + 0.25, 5.6), rgb(168, 67, 47), 0.04, False)

    k.box((-L / 2 - 0.3, -R + 1.0, 5.6), (-L / 2 + 0.1, R - 1.0, 6.0), rgb(168, 67, 47), 0.04, False)
    k.box((-L / 2 + 0.4, -R + 0.8, -0.05), (L / 2 - 0.4, R - 0.8, 0.02), rgb(120, 116, 108), 0, False)
    k.blob(L / 2 + 2.5, R + 1.8, z=0.01)
    k.finish("hangar", zmin=0)


def outskirts():
    for i in range(3):
        name = f"drift_{i}"

        if ONLY and name not in ONLY:
            continue

        reset()
        k = Kit(1.0, seed=i)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=8, y_segments=5, size=1.0)
        L = 4.0 + i * 1.5
        W = 2.0 + i * 0.5

        for v in bm.verts:
            x, y = v.co.x, v.co.y
            e = max(0.0, 1 - (x * x + y * y))
            crest = 0.65 + 0.25 * i
            h = crest * e ** 0.8 * (1.0 + 0.35 * max(0, -y))
            v.co = Vector((x * L + y * y * 0.6, y * W, h - 0.05))

        ob = k.mesh(bm, rgb(206, 186, 146), 0, grad=True)
        k.finish(name, zmin=-0.05)

    if not ONLY or "scrub" in ONLY:
        reset()
        k = Kit(0.9, seed=5)
        rng = random.Random(3)

        for j in range(6):
            a = j / 6 * 6.28
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.35)

            for v in bm.verts:
                v.co = Vector((v.co.x * rng.uniform(0.9, 1.3) + math.cos(a) * 0.35, v.co.y + math.sin(a) * 0.35, max(v.co.z, -0.1) * rng.uniform(0.9, 1.5) + 0.25))

            k.mesh(bm, rgb(122, 122, 85) if j % 2 else rgb(140, 136, 92), 0)

        k.blob(1.1)
        k.finish("scrub", zmin=0)

    if not ONLY or "ruin_wall" in ONLY:
        reset()
        k = Kit(2.6, seed=8)
        P = PLASTER[5]
        bm = bmesh.new()
        prof = [(-3, 0), (-3, 2.2), (-2.2, 2.5), (-1.4, 1.7), (-0.6, 1.9), (0.2, 1.1), (1.0, 1.4), (1.8, 0.7), (3, 0.6), (3, 0)]
        front = [bm.verts.new((x, -0.2, z - 0.3)) for x, z in prof]
        back = [bm.verts.new((x, 0.2, z - 0.3)) for x, z in prof]
        n = len(prof)

        for j in range(n):
            bm.faces.new((front[j], front[(j + 1) % n], back[(j + 1) % n], back[j]))

        bm.faces.new(list(reversed(front)))
        bm.faces.new(back)
        k.mesh(bm, P, 0.05)

        for j, (x, y, s_) in enumerate(((1.6, -0.7, 0.35), (2.2, 0.6, 0.3), (-0.4, -0.8, 0.25), (2.7, -0.5, 0.22))):
            k.box((x - s_, y - s_ * 0.8, -0.1), (x + s_, y + s_ * 0.8, s_ * 1.1), P, 0.04)

        k.blob(3.8, 1.6, 0.2, -0.1)
        k.finish("ruin_wall", zmin=-0.3)


def smalls():
    pieces = {
        "crate": lambda k: [k.box((-0.5, -0.5, 0), (0.5, 0.5, 1.0), WOOD, 0.04)] + [k.box((-0.52, -0.52, z), (0.52, 0.52, z + 0.1), WOOD_DARK, 0.01, False) for z in (0.08, 0.82)],
        "barrel": lambda k: [k.cyl((0, 0, 0), (0, 0, 1.1), 0.38, rgb(112, 124, 92), 10, bevel=0.02)] + [k.cyl((0, 0, z), (0, 0, z + 0.06), 0.395, rgb(80, 82, 76), 10) for z in (0.22, 0.82)],
        "sacks": lambda k: [sack(k, p) for p in ((0, 0, 0), (0.6, 0.1, 0), (0.3, 0.05, 0.42))],
        "crate_stack": lambda k: [k.box((x - 0.5, y - 0.5, z), (x + 0.5, y + 0.5, z + 1.0), WOOD if (i % 2 == 0) else rgb(132, 96, 62), 0.04) for i, (x, y, z) in enumerate(((0, 0, 0), (1.05, 0.1, 0), (0.5, 0.05, 1.0), (-0.2, 1.05, 0)))] + [k.box((1.5, -0.6, 0), (2.3, 0.2, 0.18), rgb(122, 96, 64), 0.02)],
        "pots": lambda k: [k.cyl((x, y, 0), (x, y, h), r, c, 8, r2=r * 0.7) for x, y, h, r, c in ((0, 0, 0.9, 0.32, POT), (0.6, 0.2, 0.6, 0.24, rgb(150, 82, 52)), (0.2, 0.6, 0.45, 0.2, rgb(214, 164, 118)))],
    }

    blobs = {"crate": (0.95, 0.95, 0, 0), "barrel": (0.75, 0.75, 0, 0), "sacks": (1.0, 0.75, 0.3, 0), "pots": (0.9, 0.9, 0.25, 0.25), "crate_stack": (1.9, 1.5, 0.3, 0)}

    for name, fn in pieces.items():
        if ONLY and name not in ONLY:
            continue

        reset()
        k = Kit(1.2, seed=len(name))
        fn(k)
        b_ = blobs[name]
        k.blob(b_[0], b_[1], b_[2], b_[3])
        k.finish(name, zmin=0)


def sack(k, p):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.35)

    for v in bm.verts:
        v.co = Vector((v.co.x * 1.1 + p[0], v.co.y * 0.8 + p[1], max(v.co.z, -0.2) * 0.75 + 0.15 + p[2]))

    return k.mesh(bm, rgb(206, 180, 130), 0)


def vault(k, x0, x1, cy, r, z, col, n=8):
    bm = bmesh.new()
    front = []
    back = []

    for j in range(n + 1):
        a = math.pi * j / n
        front.append(bm.verts.new((x0, cy + math.cos(a) * r, z + math.sin(a) * r * 0.75)))
        back.append(bm.verts.new((x1, cy + math.cos(a) * r, z + math.sin(a) * r * 0.75)))

    for j in range(n):
        bm.faces.new((front[j], back[j], back[j + 1], front[j + 1]))

    bm.faces.new(list(reversed(front)))
    bm.faces.new(back)

    return k.mesh(bm, col, 0.03)


def landmarks():
    if not ONLY or "caravanserai" in ONLY:
        reset()
        k = Kit(9, seed=3)
        P = PLASTER[1]
        trim = tuple(min(c * 1.07, 1) for c in P)
        wall = k.box((-7, -7, -0.5), (7, 7, 5.2), P)
        cuts = []

        for ax in range(4):
            ang = ax * math.pi / 2
            dx, dy = round(math.cos(ang)), round(math.sin(ang))

            for off in (-4.2, 0, 4.2):
                px, py = dx * 7 - dy * off, dy * 7 + dx * off
                hw = 1.2 if off == 0 else 0.6
                hh = 3.4 if off == 0 else 2.3
                z0 = 0 if off == 0 else 1.2
                lo = (px - (0.6 if dx else hw), py - (hw if dx else 0.6), z0)
                hi = (px + (0.6 if dx else hw), py + (hw if dx else 0.6), hh)
                cuts.append(k.box(lo, hi, P))

        k.subtract(wall, cuts)
        mod = wall.modifiers.new("b", "BEVEL")
        mod.width = 0.06
        mod.limit_method = "ANGLE"

        for ax in range(4):
            ang = ax * math.pi / 2
            dx, dy = round(math.cos(ang)), round(math.sin(ang))
            px, py = dx * 7, dy * 7
            ox, oy = dx * 0.12, dy * 0.12

            for sgn in (-1, 1):
                a = (px - dy * sgn * 1.2 + ox, py + dx * sgn * 1.2 + oy)
                k.box((min(a[0], a[0] - dy * sgn * 0.22 + ox), min(a[1], a[1] + dx * sgn * 0.22 + oy), 0), (max(a[0], a[0] - dy * sgn * 0.22 + ox) + 0.01, max(a[1], a[1] + dx * sgn * 0.22 + oy) + 0.01, 3.4), TILE[0], 0.02, False)

            k.box((px - abs(dy) * 1.45 - abs(dx) * 0.2 + ox, py - abs(dx) * 1.45 - abs(dy) * 0.2 + oy, 3.4), (px + abs(dy) * 1.45 + abs(dx) * 0.2 + ox, py + abs(dx) * 1.45 + abs(dy) * 0.2 + oy, 3.75), TILE[0], 0.02, False)

        k.box((-7.3, -7.3, -0.5), (7.3, 7.3, 0.4), tuple(c * 0.74 for c in P), 0.04)
        k.box((-7.3, -7.3, 5.2), (7.3, 7.3, 5.5), trim, 0.04)

        for j in range(12):
            x = -6.5 + j * 13.0 / 12 + 0.38

            for sgn in (-1, 1):
                k.box((x, sgn * 7.0 - 0.05, 4.6), (x + 0.32, sgn * 7.0 + 0.05, 4.92), TILE[j % len(TILE)], 0, False)
                k.box((sgn * 7.0 - 0.05, x, 4.6), (sgn * 7.0 + 0.05, x + 0.32, 4.92), TILE[(j + 1) % len(TILE)], 0, False)

        for cy in (-4.6, 0, 4.6):
            vault(k, -7.1, 7.1, cy, 2.3, 5.5, PLASTER[0])

        for cx in (-7.2, 7.2):
            for cy in (-7.2, 7.2):
                k.box((cx - 0.7, cy - 0.7, -0.5), (cx + 0.7, cy + 0.7, 6.6), PLASTER[2], 0.05)
                k.box((cx - 0.85, cy - 0.85, 6.6), (cx + 0.85, cy + 0.85, 6.85), trim, 0.03)

                for m in ((-0.55, -0.55), (0.25, -0.55), (-0.55, 0.25), (0.25, 0.25)):
                    k.box((cx + m[0], cy + m[1], 6.85), (cx + m[0] + 0.3, cy + m[1] + 0.3, 7.25), PLASTER[2], 0)

        for sgn in (-1, 1):
            k.box((-1.6, sgn * 7.35 - 0.25, 3.3), (1.6, sgn * 7.35 + 0.25, 3.45), WOOD, 0.02, False)
            bm = bmesh.new()
            y0, y1 = sgn * 7.0, sgn * 8.6
            vs = [bm.verts.new(p) for p in ((-1.7, y0, 3.5), (1.7, y0, 3.5), (1.7, y1, 3.05), (-1.7, y1, 3.05))]
            bm.faces.new(vs)
            bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.05)
            k.mesh(bm, CLOTH[0], 0, grad=False)

        k.finish("caravanserai", zmin=-0.5)

    if not ONLY or "watchtower" in ONLY:
        reset()
        k = Kit(15, seed=9)
        P = PLASTER[3]
        trim = tuple(min(c * 1.07, 1) for c in P)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)

        for v in bm.verts:
            t = v.co.z + 0.5
            w = 2.6 - t * 0.45
            v.co = Vector((v.co.x * 2 * w, v.co.y * 2 * w, -0.5 + t * 12.5))

        k.mesh(bm, P, 0.07)
        k.box((-2.8, -2.8, -0.5), (2.8, 2.8, 0.6), tuple(c * 0.74 for c in P), 0.05)
        k.box((-2.45, -2.45, 12.0), (2.45, 2.45, 12.4), trim, 0.04)
        k.box((-2.35, -2.35, 8.2), (2.35, 2.35, 8.45), TILE[0], 0.02, False)

        for j in range(4):
            a = -2.1 + j * 1.2
            for side in range(4):
                if side == 0:
                    lo, hi = (a, -2.45, 12.4), (a + 0.6, -1.9, 13.2)
                elif side == 1:
                    lo, hi = (a, 1.9, 12.4), (a + 0.6, 2.45, 13.2)
                elif side == 2:
                    lo, hi = (-2.45, a, 12.4), (-1.9, a + 0.6, 13.2)
                else:
                    lo, hi = (1.9, a, 12.4), (2.45, a + 0.6, 13.2)
                k.box(lo, hi, P, 0.04)

        for z in (3.4, 6.6, 9.8):
            w = 2.6 - (z + 0.5) / 12.5 * 0.45

            for ax in range(4):
                ang = ax * math.pi / 2
                dx, dy = round(math.cos(ang)), round(math.sin(ang))
                cx, cy = dx * w, dy * w
                k.box((cx - abs(dy) * 0.12 - abs(dx) * 0.05, cy - abs(dx) * 0.12 - abs(dy) * 0.05, z), (cx + abs(dy) * 0.12 + abs(dx) * 0.05, cy + abs(dx) * 0.12 + abs(dy) * 0.05, z + 0.9), WOOD_DARK, 0, False)

        for j in range(5):
            u = -1.9 + j * 0.95
            for sgn in (-1, 1):
                k.cyl((u, sgn * 2.1, 11.6), (u, sgn * 2.75, 11.6), 0.09, WOOD, 5)

        k.box((-0.7, -2.42, 0.4), (0.7, -2.3, 2.6), DOOR[0], 0.02, False)
        k.box((-0.9, -2.5, 2.6), (0.9, -2.3, 2.85), WOOD_DARK, 0.02, False)
        k.cyl((1.6, 1.6, 13.2), (1.6, 1.6, 16.5), 0.05, WOOD_DARK, 5)
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in ((1.6, 1.6, 16.4), (1.6, 3.0, 16.15), (1.6, 3.0, 15.5), (1.6, 1.6, 15.6))]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
        k.mesh(bm, CLOTH[0], 0, grad=False)
        k.finish("watchtower", zmin=-0.5)

    if not ONLY or "water_tower" in ONLY:
        reset()
        k = Kit(12, seed=2)
        rust = rgb(170, 110, 76)

        for x in (-1.6, 1.6):
            for y in (-1.6, 1.6):
                k.cyl((x, y, 0), (x * 0.8, y * 0.8, 7.5), 0.12, WOOD_DARK, 6)
                k.box((x - 0.3, y - 0.3, -0.3), (x + 0.3, y + 0.3, 0.2), PLASTER[4], 0.03)

        for z in (2.5, 5.0):
            s_ = 1.6 - z / 7.5 * 0.32
            for ax in range(4):
                a = ax * math.pi / 2
                k.cyl((math.cos(a) * s_ - math.sin(a) * s_, math.sin(a) * s_ + math.cos(a) * s_, z), (math.cos(a) * s_ + math.sin(a) * s_, math.sin(a) * s_ - math.cos(a) * s_, z), 0.07, WOOD, 5)

        k.cyl((0, 0, 7.5), (0, 0, 7.8), 2.0, WOOD, 12)
        k.cyl((0, 0, 7.8), (0, 0, 10.8), 1.75, rust, 12, bevel=0.03)

        for z in (8.4, 9.6):
            k.cyl((0, 0, z), (0, 0, z + 0.12), 1.79, rgb(120, 80, 60), 12)

        k.cyl((0, 0, 10.8), (0, 0, 12.0), 1.95, rgb(196, 98, 62), 12, r2=0.15)
        k.blob(3.2)
        k.box((1.7, -0.25, 0.2), (1.78, -0.2, 10.8), WOOD_DARK, 0, False)
        k.box((1.7, 0.2, 0.2), (1.78, 0.25, 10.8), WOOD_DARK, 0, False)

        for j in range(20):
            z = 0.6 + j * 0.5
            k.box((1.71, -0.22, z), (1.77, 0.22, z + 0.05), WOOD_DARK, 0, False)

        k.finish("water_tower", zmin=0)




def sag(k, length, drop, z, col, cols=None, width=0.0, segs=12, flags=0):
    pts = []

    for i in range(segs + 1):
        t = i / segs
        x = -length / 2 + length * t
        pts.append((x, z - drop * 4 * t * (1 - t)))

    for i in range(segs):
        k.cyl((pts[i][0], 0, pts[i][1]), (pts[i + 1][0], 0, pts[i + 1][1]), 0.012, col, 4)

    if width > 0:
        for i in range(segs):
            c = cols[i % len(cols)] if cols else col
            bm = bmesh.new()
            vs = [bm.verts.new(p) for p in ((pts[i][0], -width / 2, pts[i][1] - 0.02), (pts[i + 1][0], -width / 2, pts[i + 1][1] - 0.02), (pts[i + 1][0], width / 2, pts[i + 1][1] - 0.02), (pts[i][0], width / 2, pts[i][1] - 0.02))]
            bm.faces.new(vs)
            bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
            ob = k.mesh(bm, c, 0, grad=False)
            ob["cloth"] = 1

    for f in range(flags):
        t = (f + 0.5) / flags
        x = -length / 2 + length * t
        y = z - drop * 4 * t * (1 - t)
        c = cols[f % len(cols)]
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in ((x - 0.14, 0, y), (x + 0.14, 0, y), (x, 0, y - 0.32))]
        bm.faces.new(vs)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
        k.mesh(bm, c, 0, grad=False)


def bind_props():
    tag(TERRA, 7)
    tag(SAFFRON, 7)
    tag(TEAL, 7)
    tag(IRON, 8)
    tag(STONE, 3)
    tag(WOOD, 4)
    tag(WOOD_DARK, 4)
    tag(POT, 5)

    for p in PAVE:
        tag(p, 6)

    def want(n):
        return not ONLY or n in ONLY

    if want("canopy"):
        reset()
        k = Kit(1.0, seed=3)
        sag(k, 7.0, 0.7, 0.0, rgb(200, 190, 170), [rgb(240, 196, 110), rgb(250, 238, 214), rgb(214, 128, 92), rgb(250, 238, 214)], width=2.6, segs=10)
        k.finish("canopy", zmin=-1.0)

    if want("bunting"):
        reset()
        k = Kit(1.0, seed=4)
        sag(k, 7.0, 0.6, 0.0, rgb(60, 56, 52), [TERRA, SAFFRON, TEAL, rgb(242, 228, 200)], segs=10, flags=14)
        k.finish("bunting", zmin=-1.0)

    if want("lamp_post"):
        reset()
        k = Kit(3.4, seed=5)
        k.box((-0.16, -0.16, 0), (0.16, 0.16, 0.3), STONE, 0.03)
        k.cyl((0, 0, 0.3), (0, 0, 3.0), 0.05, IRON, 8)
        k.cyl((0, 0, 2.9), (0.5, 0, 3.05), 0.025, IRON, 6)
        k.box((0.36, -0.15, 2.55), (0.64, 0.15, 2.95), IRON, 0.01)
        k.box((0.39, -0.12, 2.58), (0.61, 0.12, 2.92), LAMP, 0, False)
        k.cyl((0.5, 0, 2.95), (0.5, 0, 3.1), 0.12, IRON, 6, r2=0.02)
        k.blob(0.5)
        k.finish("lamp_post", zmin=0)

    if want("bench"):
        reset()
        k = Kit(0.9, seed=6)

        for x in (-0.75, 0.75):
            k.box((x - 0.06, -0.22, 0), (x + 0.06, 0.22, 0.42), IRON, 0.01)

        for j in range(3):
            y = -0.2 + j * 0.15
            k.box((-0.95, y - 0.06, 0.42), (0.95, y + 0.06, 0.47), WOOD, 0.01)

        k.box((-0.95, 0.2, 0.5), (0.95, 0.26, 0.85), WOOD, 0.01)
        k.blob(1.1, 0.45)
        k.finish("bench", zmin=0)

    if want("cart"):
        reset()
        k = Kit(1.3, seed=7)
        k.box((-0.9, -0.55, 0.45), (0.9, 0.55, 0.55), WOOD, 0.02)

        for s_ in (-1, 1):
            k.box((-0.9, s_ * 0.55 - 0.03, 0.55), (0.9, s_ * 0.55 + 0.03, 0.85), WOOD, 0.01)
            k.cyl((-0.1, s_ * 0.66, 0.4), (-0.1, s_ * 0.6, 0.4), 0.4, WOOD_DARK, 12)
            k.cyl((-0.1, s_ * 0.67, 0.4), (-0.1, s_ * 0.59, 0.4), 0.08, IRON, 8)

        for s_ in (-1, 1):
            k.box((0.9, s_ * 0.3 - 0.03, 0.48), (1.9, s_ * 0.3 + 0.03, 0.54), WOOD, 0.01)

        k.box((-0.8, -0.45, 0.55), (-0.1, 0.05, 0.95), rgb(200, 150, 90), 0.02)
        k.cyl((0.2, -0.2, 0.55), (0.2, -0.2, 0.95), 0.22, SAFFRON, 8)
        k.cyl((0.6, 0.2, 0.55), (0.6, 0.2, 0.9), 0.2, TERRA, 8)
        k.cyl((0.25, 0.25, 0.55), (0.25, 0.25, 0.85), 0.18, TEAL, 8)
        k.blob(1.5, 0.9)
        k.finish("cart", zmin=0)

    if want("planter"):
        reset()
        k = Kit(1.4, seed=8)
        k.box((-0.6, -0.3, 0), (0.6, 0.3, 0.55), POT, 0.03)
        k.box((-0.64, -0.34, 0.55), (0.64, 0.34, 0.62), STONE, 0.02)

        for j, x in enumerate((-0.35, 0.0, 0.35)):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.32)

            for v in bm.verts:
                v.co = Vector((v.co.x, v.co.y * 0.9, v.co.z * 1.1)) + Vector((x, 0, 0.85 + j % 2 * 0.1))

            k.mesh(bm, LEAF if j != 1 else rgb(120, 150, 78), 0, grad=False)

        k.blob(0.8, 0.45)
        k.finish("planter", zmin=0)

    if want("paving"):
        reset()
        k = Kit(0.1, seed=9)
        n = 5
        s_ = 4.0 / n

        for i in range(n):
            for j in range(n):
                x0 = -2 + i * s_ + (0.5 * s_ if j % 2 else 0) - (s_ if j % 2 and i == n - 1 else 0)
                y0 = -2 + j * s_
                w_ = s_ if not (j % 2 and i == n - 1) else s_
                c = PAVE[k.rng.randrange(len(PAVE))]
                k.box((max(x0 + 0.03, -2), y0 + 0.03, -0.1), (min(x0 + w_ - 0.03, 2), y0 + s_ - 0.03, 0.03), c, 0.015, False)

        k.box((-2, -2, -0.12), (2, 2, 0.005), rgb(150, 132, 104), 0, False)
        tag(rgb(150, 132, 104), 6)
        k.finish("paving", zmin=-0.12)

    if want("kerb"):
        reset()
        k = Kit(0.3, seed=10)

        for j in range(4):
            k.box((-2 + j + 0.01, -0.14, -0.1), (-1 + j - 0.01, 0.14, 0.16), STONE if j % 2 == 0 else rgb(212, 190, 152), 0.02)

        tag(rgb(212, 190, 152), 3)
        k.finish("kerb", zmin=-0.1)


if not ONLY or any(n.startswith("house") for n in ONLY):
    buildings()

bind_props()
