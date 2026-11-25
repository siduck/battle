import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
import os
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)

PAL = {
    "body": ((0.25, 0.27, 0.3), 0.5, 0.2),
    "dark": ((0.15, 0.16, 0.18), 0.55, 0.2),
    "rail": ((0.33, 0.35, 0.38), 0.45, 0.3),
    "accent": ((0.78, 0.6, 0.3), 0.45, 0.1),
    "rim": ((0.85, 0.32, 0.22), 0.4, 0.0),
    "glow": ((0.95, 0.28, 0.2), 0.4, 0.0),
    "lens": ((0.3, 0.55, 0.62), 0.2, 0.0),
}

GLOW = {"glow": 0.15, "lens": 0.75}


def lin(c):
    return tuple(min(1.0, x / 0.9) for x in c)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def mat(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    rgb, rough, metal = PAL[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*lin(rgb), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*lin(rgb), 1)

    return m


def finish(o, m, bevel=0.0, segs=2):
    o.data.materials.append(mat(m))

    if bevel > 0:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = segs
        b.limit_method = "ANGLE"

    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    o.select_set(False)

    return o


def box(loc, size, m, bevel=0.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)

    return finish(o, m, bevel)


def tube(y0, y1, z, r, m, verts=14, bevel=0.0, r1=None, hole=0.0):
    depth = abs(y1 - y0)
    loc = (0, (y0 + y1) / 2, z)

    if r1 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=(math.pi / 2, 0, 0))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r1, depth=depth, location=loc, rotation=(-math.pi / 2, 0, 0))

    o = bpy.context.object

    if hole > 0:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=hole, depth=depth * 1.2, location=loc, rotation=(math.pi / 2, 0, 0))
        cut = bpy.context.object
        mod = o.modifiers.new("h", "BOOLEAN")
        mod.object = cut
        mod.operation = "DIFFERENCE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="h")
        bpy.data.objects.remove(cut, do_unlink=True)

    return finish(o, m, bevel)


def ring(y, z, r, w, m, verts=14):
    return tube(y - w / 2, y + w / 2, z, r, m, verts, 0.0, None, r - 0.0025)


def mount(length, height):
    box((0, 0, 0.004), (0.022, length, 0.008), "rail", 0.0015)
    for k in range(int(length / 0.02)):
        y = -length / 2 + 0.006 + k * 0.02
        box((0, y, 0.0095), (0.024, 0.005, 0.003), "dark", 0.0008)
    box((0, 0, 0.008 + height / 2), (0.018, length * 0.7, height), "body", 0.002)
    box((0.014, 0, 0.012), (0.006, length * 0.5, 0.01), "dark", 0.0015)


def tones():
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            continue

        bpy.context.view_layer.objects.active = o
        o.select_set(True)

        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)

        o.select_set(False)
        me = o.data
        name = me.materials[0].name if me.materials else ""
        g = GLOW.get(name, 1.0)
        zs = [v.co.z for v in me.vertices] or [0]
        lo, hi = min(zs), max(zs)
        span = max(hi - lo, 1e-4)
        attr = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")

        for v in me.vertices:
            up = v.normal.z * 0.5 + 0.5
            h = (v.co.z - lo) / span
            k = 0.74 + 0.16 * up + 0.1 * h
            attr.data[v.index].color = (k, k, k, g)

        me.color_attributes.active_color = attr


def export(name):
    tones()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_apply=True, export_materials="EXPORT", export_texcoords=False, export_normals=True, use_selection=False, export_vertex_color="ACTIVE")


def red_dot():
    clear()
    mount(0.05, 0.006)
    box((0, 0.004, 0.022), (0.026, 0.032, 0.014), "body", 0.003)
    tube(-0.014, 0.014, 0.034, 0.016, "body", 14, 0.0, None, 0.0135)
    ring(-0.014, 0.034, 0.0165, 0.003, "rim")
    box((0.017, 0.004, 0.026), (0.008, 0.014, 0.01), "dark", 0.002)
    box((0, 0.012, 0.034), (0.0025, 0.002, 0.0025), "glow", 0.0005)
    export("Optic_Dot")


def holo():
    clear()
    mount(0.06, 0.006)
    box((0, 0.01, 0.02), (0.034, 0.05, 0.012), "body", 0.003)
    box((0.0155, -0.012, 0.038), (0.004, 0.006, 0.026), "body", 0.0015)
    box((-0.0155, -0.012, 0.038), (0.004, 0.006, 0.026), "body", 0.0015)
    box((0, -0.012, 0.0515), (0.035, 0.006, 0.004), "body", 0.0015)
    box((0.0155, 0.018, 0.034), (0.004, 0.006, 0.018), "body", 0.0015)
    box((-0.0155, 0.018, 0.034), (0.004, 0.006, 0.018), "body", 0.0015)
    box((0, 0.018, 0.0445), (0.035, 0.006, 0.004), "body", 0.0015)
    box((0, -0.014, 0.0515), (0.022, 0.002, 0.0012), "rim", 0.0003)
    box((0, 0.025, 0.02), (0.012, 0.012, 0.006), "accent", 0.0015)
    export("Optic_Holo")


def scope(name, length, r_tube, r_obj, r_eye, turrets, bell):
    clear()
    rise = 0.016 + r_obj * 0.4
    zc = 0.012 + rise
    mount(length * 0.55, 0.004)
    for y in (-length * 0.18, length * 0.18):
        box((0, y, 0.012 + rise / 2), (0.016, 0.012, rise), "body", 0.002)
        ring(y, zc, r_tube + 0.0025, 0.012, "dark")
    front = -length / 2
    back = length / 2
    tube(-length * 0.22, length * 0.22, zc, r_tube, "body", 14, 0.0, None, r_tube - 0.003)
    tube(front, front + bell, zc, r_obj, "body", 14, 0.0, r_tube, r_obj - 0.0035 if not turrets else 0.0)
    if turrets:
        tube(front + 0.001, front + 0.004, zc, r_obj - 0.002, "lens", 14)
    ring(front + 0.002, zc, r_obj + 0.0006, 0.004, "rim")
    tube(back - length * 0.18, back, zc, r_eye, "body", 14, 0.0, None, r_eye - 0.003)
    tube(length * 0.22, back - length * 0.18, zc, r_tube, "body", 14, 0.0, r_eye, r_tube - 0.003)
    ring(back - 0.002, zc, r_eye + 0.0006, 0.004, "accent")
    ring(front + bell + 0.004, zc, r_tube + 0.0012, 0.004, "accent")
    if turrets:
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.0085, depth=0.014, location=(0, 0, zc + r_tube + 0.006))
        finish(bpy.context.object, "dark", 0.0015)
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.0085, depth=0.014, location=(r_tube + 0.006, 0, zc), rotation=(0, math.pi / 2, 0))
        finish(bpy.context.object, "dark", 0.0015)
        box((0, 0, zc + r_tube + 0.0135), (0.01, 0.002, 0.0015), "accent", 0.0004)
    export(name)


red_dot()
holo()
scope("Optic_Scope2", 0.12, 0.011, 0.015, 0.0135, False, 0.026)
scope("Optic_Scope4", 0.18, 0.012, 0.02, 0.0145, True, 0.04)
scope("Optic_Scope8", 0.25, 0.013, 0.026, 0.015, True, 0.06)


def preview_all():
    import glob
    for f in sorted(glob.glob(os.path.join(out, "Optic_*.glb"))):
        clear()
        bpy.ops.import_scene.gltf(filepath=f)
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_cavity = True
        scene.render.resolution_x = 400
        scene.render.resolution_y = 300
        scene.display.shading.background_type = "VIEWPORT"
        scene.display.shading.background_color = (0.46, 0.53, 0.62)
        lo = Vector((1e9, 1e9, 1e9))
        hi = Vector((-1e9, -1e9, -1e9))
        for o in bpy.data.objects:
            if o.type != "MESH":
                continue
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
        mid = (lo + hi) / 2
        size = max((hi - lo).length, 0.05)
        bpy.ops.object.camera_add(location=mid + Vector((size * 1.1, size * 0.9, size * 0.6)))
        cam = bpy.context.object
        cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens_unit = "FOV"
        cam.data.angle = math.radians(40)
        scene.camera = cam
        scene.render.filepath = f.replace(".glb", ".png")
        bpy.ops.render.render(write_still=True)


if "--preview" in sys.argv:
    preview_all()
