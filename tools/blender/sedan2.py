import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bmesh
import math
from mathutils import Vector
from veh import G, hexc

OUT = os.environ.get("CARS_OUT", "/tmp/cars_out")
OLD = os.environ.get("OLD_DIR", "")

PAL = {
    "body": "5C7F9C",
    "glass": "26313D",
    "trim": "3A3E45",
    "dark": "2A2E33",
    "chrome": "A9ADB1",
    "cream": "EDE3C4",
    "tail": "B0473C",
    "amber": "D69A3C",
    "tyre": "34383E",
    "rim": "B4B8BC",
    "dish": "6E7378",
    "plate": "D8D2BE",
}
MATS = list(PAL.keys())


def mi(name):
    return MATS.index(name)


def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)

    for m in MATS:
        mat = bpy.data.materials.get(m) or bpy.data.materials.new(m)
        o.data.materials.append(mat)

    return o


def prep(o):
    if not o.data.materials:
        for m in MATS:
            o.data.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))

    return o


def set_mat(o, name):
    prep(o)

    for p in o.data.polygons:
        p.material_index = mi(name)

    return o


def loft(stations, name="body", crease=(2, 4), amount=0.85):
    bm = bmesh.new()
    rings = []
    cl = bm.edges.layers.float.new("crease_edge")

    for z, half, mats in stations:
        pts = []

        for x, y in half:
            pts.append((x, y))

        full = pts + [(-x, y) for x, y in reversed(pts[1:-1])]
        rings.append([bm.verts.new(G(x, y, z)) for x, y in full])

    n = len(rings[0])
    half_n = len(stations[0][1])

    for i in range(len(rings) - 1):
        a = rings[i]
        b = rings[i + 1]
        mats = stations[i][2]

        for j in range(n):
            k = (j + 1) % n
            f = bm.faces.new([a[j], a[k], b[k], b[j]])
            jj = j if j < half_n else n - j

            if jj in crease:
                e = bm.edges.get([a[j], b[j]])

                if e:
                    e[cl] = amount
            seg = j if j < half_n - 1 else n - 1 - j
            f.material_index = mi(mats.get(seg, "body"))

    bm.faces.new(list(reversed(rings[0]))).material_index = mi("body")
    bm.faces.new(rings[-1]).material_index = mi("body")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    return new_obj(name, bm)


def apply_mods(o):
    bpy.context.view_layer.objects.active = o

    for o2 in bpy.context.scene.objects:
        o2.select_set(o2 == o)

    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def subsurf(o, lv=2):
    m = o.modifiers.new("s", "SUBSURF")
    m.levels = lv
    m.render_levels = lv
    apply_mods(o)

    return o


def boolean(o, cutter, op="DIFFERENCE"):
    m = o.modifiers.new("b", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.object = cutter
    apply_mods(o)
    bpy.data.objects.remove(cutter, do_unlink=True)


def cyl(p, axis, r, depth, mat, seg=36, bevel=0.0, bseg=2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=depth, location=G(*p))
    o = bpy.context.active_object
    o.rotation_euler = G(*axis).to_track_quat("Z", "Y").to_euler()

    if bevel > 0:
        b = o.modifiers.new("bv", "BEVEL")
        b.width = bevel
        b.segments = bseg
        b.limit_method = "ANGLE"

    return set_mat(o, mat)


def box(p, s, mat, rot=(0, 0, 0), bev=0.3, seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=G(*p))
    o = bpy.context.active_object
    o.scale = (s[0], s[2], s[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.rotation_euler = (rot[0], -rot[2], rot[1])

    if bev > 0:
        b = o.modifiers.new("bv", "BEVEL")
        b.width = min(s) * bev
        b.segments = seg
        b.limit_method = "NONE"

    return set_mat(o, mat)


def egg(p, s, mat, rot=(0, 0, 0), seg=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=G(*p))
    o = bpy.context.active_object
    o.scale = (s[0], s[2], s[1])
    o.rotation_euler = (rot[0], -rot[2], rot[1])

    return set_mat(o, mat)


def tube(pts, r, mat, res=3):
    cu = bpy.data.curves.new("t", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    cu.resolution_u = 8
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)

    for bp, p in zip(sp.bezier_points, pts):
        bp.co = G(*p)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"

    o = bpy.data.objects.new("t", cu)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o

    for o2 in bpy.context.scene.objects:
        o2.select_set(o2 == o)

    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object

    return set_mat(o, mat)


def arch_flare(z, r, hw, y0, sill):
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.06, minor_radius=0.055, major_segments=40, minor_segments=8, location=G(0, y0, z))
    o = bpy.context.active_object
    o.rotation_euler = G(1, 0, 0).to_track_quat("Z", "Y").to_euler()
    o.scale = (1, 1, (hw * 2 + 0.06) / 0.11)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = [v for v in bm.verts if (v.co.z < sill + 0.02) or (abs(v.co.x) < hw - 0.06)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()

    return set_mat(o, "body")


def sedan(L=4.54, W=1.8, H=1.42, r=0.298, fz=1.346, rz=-1.25):
    hw = W / 2
    sill = 0.24
    belt = 0.80
    deck = 0.86
    top = H
    zf = L / 2
    zr = -L / 2

    def ring(bh, sh, bw, tw, ty, side=None):
        return [(0, sill - 0.02), (bw - 0.07, sill - 0.02), (bw, sill + 0.14), (bw + 0.01, (sill + bh) * 0.5), (bw - 0.005, bh), (tw, ty), (0, ty + (0.02 if ty > 1.2 else 0.01))]

    lower = {}
    cabin = {4: "glass"}
    wind = {4: "glass", 5: "glass"}
    pillar = {}

    stations = [
        (zr, [(0, sill + 0.06), (hw - 0.22, sill + 0.06), (hw - 0.16, sill + 0.2), (hw - 0.13, 0.5), (hw - 0.14, belt - 0.02), (hw - 0.3, deck - 0.02), (0, deck - 0.01)], lower),
        (zr + 0.14, ring(belt + 0.02, 0, hw - 0.04, hw - 0.12, deck + 0.02), lower),
        (zr + 0.7, ring(belt + 0.02, 0, hw - 0.01, hw - 0.1, deck + 0.03), lower),
        (zr + 0.98, ring(belt + 0.02, 0, hw, hw - 0.1, deck + 0.04), wind),
        (zr + 1.38, ring(belt + 0.01, 0, hw, hw - 0.16, top - 0.03), cabin),
        (zr + 2.0, ring(belt + 0.01, 0, hw, hw - 0.16, top), pillar),
        (zr + 2.1, ring(belt + 0.01, 0, hw, hw - 0.16, top), cabin),
        (zr + 2.6, ring(belt, 0, hw, hw - 0.17, top - 0.01), wind),
        (zr + 3.22, ring(belt - 0.01, 0, hw, hw - 0.1, deck + 0.0), lower),
        (zr + 3.75, ring(belt - 0.05, 0, hw - 0.02, hw - 0.12, deck - 0.07), lower),
        (zf - 0.16, ring(belt - 0.12, 0, hw - 0.08, hw - 0.2, deck - 0.15), lower),
        (zf, [(0, sill + 0.08), (hw - 0.3, sill + 0.08), (hw - 0.24, sill + 0.2), (hw - 0.2, 0.45), (hw - 0.22, belt - 0.16), (hw - 0.34, deck - 0.18), (0, deck - 0.17)], lower),
    ]
    body = loft(stations)
    subsurf(body, 2)

    for z in (fz, rz):
        c = cyl((0, r * 1.0, z), (1, 0, 0), r + 0.055, W + 0.5, "body", seg=48)
        boolean(body, c)

    parts = [body]

    for z in (fz, rz):
        parts.append(arch_flare(z, r, hw - 0.005, r * 1.0, sill + 0.06))
        well = cyl((0, r * 1.02, z), (1, 0, 0), r + 0.03, W - 0.25, "dark", seg=32)
        parts.append(well)

    for s in (-1, 1):
        parts.append(box((s * (hw - 0.03), sill + 0.03, (fz + rz) / 2), (0.08, 0.09, fz - rz - 2 * r - 0.3), "trim", bev=0.2))
        for zz in (0.42, -0.62):
            parts.append(tube([(s * (hw + 0.006), sill + 0.18, zz), (s * (hw + 0.008), belt - 0.03, zz + 0.02)], 0.006, "dark", res=1))
        for zz in (0.25, -0.8):
            parts.append(box((s * (hw + 0.012), belt - 0.1, zz), (0.025, 0.035, 0.16), "trim", bev=0.4, seg=2))
        parts.append(tube([(s * (hw + 0.004), belt - 0.03, zr + 0.6), (s * (hw + 0.004), belt - 0.04, zf - 0.95)], 0.006, "dark", res=1))
        parts.append(box((s * (hw + 0.07), belt + 0.11, zr + 2.55), (0.12, 0.09, 0.05), "body", bev=0.35))
        parts.append(box((s * (hw + 0.07), belt + 0.11, zr + 2.575), (0.1, 0.07, 0.01), "glass", bev=0.3))
        parts.append(box((s * (hw + 0.015), belt + 0.08, zr + 2.53), (0.05, 0.03, 0.06), "body", bev=0.3))
        parts.append(box((s * (hw - 0.4), belt - 0.18, zf - 0.005), (0.3, 0.085, 0.06), "cream", rot=(0, s * 0.12, 0), bev=0.3))
        parts.append(box((s * (hw - 0.4), belt - 0.18, zf - 0.02), (0.33, 0.11, 0.05), "dark", rot=(0, s * 0.12, 0), bev=0.3))
        parts.append(box((s * (hw - 0.34), belt - 0.07, zr - 0.01), (0.36, 0.1, 0.06), "tail", rot=(0, -s * 0.08, 0), bev=0.3))
        parts.append(box((s * (hw - 0.2), belt - 0.18, zf - 0.13), (0.06, 0.05, 0.1), "amber", rot=(0, s * 0.6, 0), bev=0.3))

    parts.append(box((0, sill + 0.13, zf - 0.06), (W - 0.5, 0.2, 0.14), "body", bev=0.3))
    parts.append(box((0, sill + 0.09, zf + 0.005), (W - 0.8, 0.07, 0.04), "dark", bev=0.3))
    parts.append(box((0, belt - 0.19, zf + 0.0), (W * 0.3, 0.08, 0.05), "dark", bev=0.3))
    parts.append(box((0, sill + 0.14, zr + 0.06), (W - 0.42, 0.2, 0.14), "body", bev=0.3))
    parts.append(box((0, sill + 0.05, zr + 0.06), (W - 0.7, 0.05, 0.1), "trim", bev=0.3))
    parts.append(box((0, sill + 0.34, zr + 0.07), (0.38, 0.1, 0.02), "plate", bev=0.2))
    parts.append(box((0, sill + 0.15, zf + 0.02), (0.36, 0.09, 0.02), "plate", bev=0.2))
    parts.append(cyl((-0.45, sill + 0.06, zr - 0.08), (0, 0, 1), 0.035, 0.12, "chrome", seg=12))

    return parts


def wheel(r=0.298, width=0.22, spokes=5):
    parts = []
    t = r * 0.27
    bpy.ops.mesh.primitive_torus_add(major_radius=r - t, minor_radius=t, major_segments=48, minor_segments=14, location=(0, 0, 0))
    o = bpy.context.active_object
    o.rotation_euler = G(1, 0, 0).to_track_quat("Z", "Y").to_euler()
    o.scale = (1, 1, width / (2 * t))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    parts.append(set_mat(o, "tyre"))
    rr = r - t * 1.55
    parts.append(cyl((0, 0, 0), (1, 0, 0), rr + 0.01, width * 0.86, "dish", seg=48, bevel=0.012))
    parts.append(cyl((-width * 0.36, 0, 0), (1, 0, 0), rr, 0.03, "rim", seg=48, bevel=0.008))
    face = -width * 0.44

    for i in range(spokes):
        a = i / spokes * math.tau
        tip = (face, math.sin(a) * rr * 0.93, math.cos(a) * rr * 0.93)
        base = (face - 0.015, math.sin(a) * rr * 0.2, math.cos(a) * rr * 0.2)
        bm = bmesh.new()
        w0 = rr * 0.2
        w1 = rr * 0.15
        nx, ny = math.cos(a), -math.sin(a)
        quad = []

        for (x, y, z), w in ((base, w0), (tip, w1)):
            for d in (-1, 1):
                for dx in (0, 0.045):
                    quad.append(bm.verts.new(G(x + dx, y + d * w * ny, z + d * w * nx)))

        v = quad
        faces = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (0, 1, 3, 2), (4, 6, 7, 5)]

        for f in faces:
            bm.faces.new([v[i] for i in f])

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = new_obj("spoke", bm)
        b = o.modifiers.new("bv", "BEVEL")
        b.width = 0.008
        b.segments = 2
        parts.append(set_mat(o, "rim"))

    parts.append(cyl((face - 0.005, 0, 0), (1, 0, 0), rr * 0.24, 0.04, "rim", seg=24, bevel=0.012))
    parts.append(egg((face - 0.03, 0, 0), (0.02, rr * 0.11, rr * 0.11), "dark", seg=12))

    for i in range(5):
        a = i / 5 * math.tau + 0.6
        parts.append(cyl((face - 0.022, math.sin(a) * rr * 0.16, math.cos(a) * rr * 0.16), (1, 0, 0), 0.008, 0.012, "chrome", seg=8))

    return parts


def export(parts, path, ymin=0.0, height=1.5):
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    cols = [hexc(PAL[m]) for m in MATS]

    for ob in parts:
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        me.transform(ob.matrix_world)
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

        for poly in me.polygons:
            col = cols[min(poly.material_index, len(cols) - 1)]
            flat = MATS[min(poly.material_index, len(cols) - 1)] in ("cream", "tail", "amber", "glass", "plate")

            for li in poly.loop_indices:
                z = me.vertices[me.loops[li].vertex_index].co.z
                h = min(max((z - ymin) / height, 0), 1)
                k = 1.0 if flat else 0.82 + 0.24 * h

                if poly.normal.z > 0.55:
                    k *= 1.05
                elif poly.normal.z < -0.5:
                    k *= 0.72

                attr.data[li].color = (min(col[0] * k, 1), min(col[1] * k, 1), min(col[2] * k, 1), 1.0)

        for p in me.polygons:
            p.material_index = 0

        bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    for ob in list(parts):
        bpy.data.objects.remove(ob, do_unlink=True)

    me = bpy.data.meshes.new(os.path.basename(path))
    bm.to_mesh(me)
    bm.free()

    while len(me.materials):
        me.materials.pop()

    mat = bpy.data.materials.new("veh")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    me.materials.append(mat)
    me.color_attributes.active_color = me.color_attributes["Col"]
    ob = bpy.data.objects.new(os.path.basename(path), me)
    bpy.context.scene.collection.objects.link(ob)

    for o in bpy.context.scene.objects:
        o.select_set(o == ob)

    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True, export_vertex_color="ACTIVE", export_normals=True, export_materials="EXPORT")
    print("OUT", path, sum(len(p.vertices) - 2 for p in me.polygons), os.path.getsize(path))
    bpy.data.objects.remove(ob, do_unlink=True)


def shot(files, path, cam, look, texture=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    for f, at in files:
        bpy.ops.import_scene.gltf(filepath=f)

        for o in bpy.context.selected_objects:
            if o.parent is None:
                o.location = G(*at[:3])

                if len(at) > 3:
                    o.rotation_euler[2] += at[3]

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    pl = bpy.context.active_object
    pl.color = (0.86, 0.82, 0.74, 1)
    bpy.ops.object.camera_add(location=G(*cam))
    c = bpy.context.active_object
    c.rotation_euler = (G(*look) - G(*cam)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = 55
    sc = bpy.context.scene
    sc.camera = c
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE" if texture else "VERTEX"
    sc.display.shading.show_cavity = True
    sc.display.shading.show_shadows = True
    sc.render.resolution_x = 900
    sc.render.resolution_y = 560
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    body = os.path.join(OUT, "body.glb")
    wf = os.path.join(OUT, "wheel.glb")
    export(sedan(), body, 0.0, 1.45)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    export(wheel(), wf, -0.3, 0.6)

    r = 0.298
    fz = 1.346
    rz = -1.25
    xw = 0.724


    def car(bodyf, wheelf, dx):
        return [(bodyf, (dx, 0, 0)), (wheelf, (dx - xw, r, fz)), (wheelf, (dx - xw, r, rz)), (wheelf, (dx + xw, r, fz, math.pi)), (wheelf, (dx + xw, r, rz, math.pi))]


    views = {"front": ((-5.0, 2.0, 5.2), (0, 0.55, 0.2)), "rear": ((-5.0, 2.0, -5.2), (0, 0.55, -0.2))}

    for v, (cam, look) in views.items():
        shot(car(body, wf, 0), os.path.join(OUT, "new_" + v + ".png"), cam, look)

        if OLD:
            shot(car(os.path.join(OLD, "body.glb"), os.path.join(OLD, "wheel.glb"), 0), os.path.join(OUT, "old_" + v + ".png"), cam, look, texture=True)


if __name__ == "__main__":
    main()
