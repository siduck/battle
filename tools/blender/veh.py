import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import bmesh
import math
import os
from mathutils import Vector


def hexc(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def G(x, y, z):
    return Vector((x, -z, y))


class Kit:
    def __init__(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.objs = []

    def tag(self, o, col, grad=True):
        o["col"] = hexc(col) if isinstance(col, str) else col
        o["grad"] = grad
        self.objs.append(o)

        return o

    def tube(self, pts, r, col, res=2, caps=True, radii=None):
        cu = bpy.data.curves.new("t", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 1.0
        cu.bevel_resolution = res
        cu.use_fill_caps = caps
        cu.resolution_u = 6
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)

        for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
            bp.co = G(*p)
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
            bp.radius = radii[i] if radii else r

        if radii is None:
            cu.bevel_depth = r

            for bp in sp.bezier_points:
                bp.radius = 1.0

        o = bpy.data.objects.new("t", cu)
        bpy.context.collection.objects.link(o)

        return self.tag(o, col)

    def line(self, a, b, r, col, seg=10):
        a = G(*a)
        b = G(*b)
        d = b - a
        bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=d.length, location=(a + b) / 2)
        o = bpy.context.active_object
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

        return self.tag(o, col)

    def cyl(self, p, axis, r, depth, col, seg=24, bevel=0.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=depth, location=G(*p))
        o = bpy.context.active_object
        o.rotation_euler = G(*axis).to_track_quat("Z", "Y").to_euler()

        if bevel > 0:
            b = o.modifiers.new("b", "BEVEL")
            b.width = bevel
            b.segments = 2
            b.limit_method = "ANGLE"

        return self.tag(o, col)

    def torus(self, p, axis, R, r, col, seg=32, mseg=10, sx=1.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=mseg, location=G(*p))
        o = bpy.context.active_object
        o.rotation_euler = G(*axis).to_track_quat("Z", "Y").to_euler()
        o.scale = (1, 1, sx)

        return self.tag(o, col)

    def box(self, p, s, col, rot=(0, 0, 0), bev=0.3, sub=0, seg=3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=G(*p))
        o = bpy.context.active_object
        o.scale = (s[0], s[2], s[1])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o.rotation_euler = (rot[0], -rot[2], rot[1])
        b = o.modifiers.new("b", "BEVEL")
        b.width = min(s) * bev
        b.segments = seg
        b.limit_method = "NONE"

        if sub:
            m = o.modifiers.new("s", "SUBSURF")
            m.levels = sub

        return self.tag(o, col)

    def egg(self, p, s, col, rot=(0, 0, 0), seg=20):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=G(*p))
        o = bpy.context.active_object
        o.scale = (s[0], s[2], s[1])
        o.rotation_euler = (rot[0], -rot[2], rot[1])

        return self.tag(o, col)

    def finish(self, path, ymin=0.0, height=1.0):
        dg = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()

        for ob in self.objs:
            ev = ob.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev)
            me.transform(ob.matrix_world)
            col = tuple(ob["col"])
            grad = ob["grad"]
            attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
            me.calc_loop_triangles()

            for poly in me.polygons:
                for li in poly.loop_indices:
                    z = me.vertices[me.loops[li].vertex_index].co.z
                    h = min(max((z - ymin) / height, 0), 1)
                    k = (0.84 + 0.22 * h) if grad else 1.0

                    if poly.normal.z > 0.6:
                        k *= 1.06
                    elif poly.normal.z < -0.6:
                        k *= 0.78

                    attr.data[li].color = (min(col[0] * k, 1), min(col[1] * k, 1), min(col[2] * k, 1), 1.0)

            me.color_attributes.active_color = attr
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)

        for ob in list(self.objs):
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)

        self.objs = []
        me = bpy.data.meshes.new(os.path.basename(path))
        bm.to_mesh(me)
        bm.free()
        mat = bpy.data.materials.new("veh")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.8
        me.materials.append(mat)
        me.color_attributes.active_color = me.color_attributes["Col"]
        ob = bpy.data.objects.new(os.path.basename(path), me)
        bpy.context.scene.collection.objects.link(ob)

        for o in bpy.context.scene.objects:
            o.select_set(o == ob)

        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT")
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        print("OUT", path, tris, os.path.getsize(path))
        bpy.data.objects.remove(ob, do_unlink=True)


def wheel(k, r, tyre, width, rim_col, tyre_col, spokes, hub_col, knobs=False, disc=None, cast=0):
    k.torus((0, 0, 0), (1, 0, 0), r - tyre, tyre, tyre_col, seg=32, mseg=8, sx=width / tyre)

    if knobs:
        for i in range(18):
            a = i / 18 * math.tau
            p = (0, math.sin(a) * (r - tyre * 0.1), math.cos(a) * (r - tyre * 0.1))
            k.box(p, (width * 1.9, tyre * 0.42, tyre * 0.5), tyre_col, rot=(-a, 0, 0), bev=0.0, seg=1)

    rim_r = r - tyre * 1.85
    k.torus((0, 0, 0), (1, 0, 0), rim_r, tyre * 0.3, rim_col, seg=32, mseg=5, sx=1.6)
    k.cyl((0, 0, 0), (1, 0, 0), r * 0.1, width * 3.2, hub_col, seg=12)

    if cast:
        for i in range(cast):
            a = i / cast * math.tau
            k.box((0, math.sin(a) * rim_r * 0.55, math.cos(a) * rim_r * 0.55), (width * 0.9, rim_r * 0.9, rim_r * 0.12), rim_col, rot=(-a, 0, 0), bev=0.2, seg=1)
    elif spokes > 0:
        for i in range(spokes):
            a = i / spokes * math.tau
            side = 1 if i % 2 else -1
            k.line((side * width * 1.2, 0, 0), (side * width * 0.3, math.sin(a) * rim_r, math.cos(a) * rim_r), 0.0028, rim_col, seg=3)

    if disc:
        k.cyl((width * 1.5, 0, 0), (1, 0, 0), r * 0.42, 0.006, disc, seg=20)


def render(parts, path, cam=(2.6, 1.3, 1.9), look=(0, 0.5, 0)):
    for f, at in parts:
        bpy.ops.import_scene.gltf(filepath=f)

        for o in bpy.context.selected_objects:
            if o.parent is None:
                o.location = G(*at)

    for m in bpy.data.materials:
        if m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
            m.diffuse_color = m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value

    bpy.ops.object.camera_add(location=G(*cam))
    c = bpy.context.active_object
    c.rotation_euler = (G(*look) - G(*cam)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = 50
    sc = bpy.context.scene
    sc.camera = c
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "VERTEX"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 900
    sc.render.resolution_y = 600
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
