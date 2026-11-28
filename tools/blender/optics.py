import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
import os
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]

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


def merge():
    groups = {}

    for o in bpy.data.objects:
        if o.type == "MESH":
            groups.setdefault(o.data.materials[0].name, []).append(o)

    for parts in groups.values():
        bpy.ops.object.select_all(action="DESELECT")

        for o in parts:
            o.select_set(True)

        bpy.context.view_layer.objects.active = parts[0]

        if len(parts) > 1:
            bpy.ops.object.join()

        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def export(name):
    tones()
    merge()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_apply=True, export_materials="EXPORT", export_texcoords=False, export_normals=True, use_selection=False, export_vertex_color="ACTIVE")


def barrel(y0, y1, z, outer, inner, m, bevel=0.0008):
    return tube(y0, y1, z, outer, m, 24, bevel, None, inner)


def knob(loc, axis, r, depth, m):
    turn = {"x": (0, math.pi / 2, 0), "z": (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=r, depth=depth, location=loc, rotation=turn)

    return finish(bpy.context.object, m, 0.0008)


def red_dot():
    clear()
    zc = 0.034
    mount(0.044, 0.004)
    box((0, 0, 0.0126), (0.018, 0.02, 0.004), "dark", 0.001)
    barrel(-0.012, -0.006, zc, 0.0212, 0.0186, "dark")
    barrel(-0.006, 0.006, zc, 0.02, 0.0182, "body", 0.0)
    barrel(0.006, 0.012, zc, 0.0206, 0.0174, "dark")
    knob((-0.0235, 0.0, zc), "x", 0.0062, 0.008, "dark")
    knob((-0.0285, 0.0, zc), "x", 0.0045, 0.003, "rail")
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
        post = rise - r_tube + 0.0015
        box((0, y, 0.012 + post / 2), (0.016, 0.012, post), "body", 0.002)
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


def shell(zc, profile, m, sides=28, phase=0.0):
    verts = []
    faces = []
    count = len(profile)

    for k in range(sides):
        a = phase + math.tau * k / sides
        verts += [(r * math.cos(a), y, zc + r * math.sin(a)) for y, r in profile]

    for k in range(sides):
        for i in range(count):
            a = k * count + i
            b = k * count + (i + 1) % count
            c = ((k + 1) % sides) * count + (i + 1) % count
            d = ((k + 1) % sides) * count + i
            faces.append((a, b, c, d))

    me = bpy.data.meshes.new("shell")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new("shell", me)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    o.select_set(False)

    return finish(o, m)


def band(zc, y0, y1, outer, depth, m):
    shell(zc, [(y1, outer), (y0, outer), (y0, outer - depth), (y1, outer - depth)], m)


def turret(zc, side, y, base, r, depth, cap):
    at = {"right": lambda d: (-(base + d), y, zc), "left": lambda d: (base + d, y, zc), "top": lambda d: (0, y, zc + base + d)}[side]
    axis = "z" if side == "top" else "x"
    knob(at(depth * 0.5), axis, r, depth, "dark")
    knob(at(depth + cap * 0.5), axis, r * 1.12, cap, "body")
    knob(at(depth + cap + cap * 0.35), axis, r * 0.66, cap * 0.7, "dark")

    for k in range(10):
        a = math.tau * k / 10
        c, s = math.cos(a) * r * 1.12, math.sin(a) * r * 1.12
        p = at(depth + cap * 0.5)

        if side == "top":
            box((p[0] + c, p[1] + s, p[2]), (r * 0.2, r * 0.2, cap * 0.8), "dark", 0.0003)
        else:
            box((p[0], p[1] + c, p[2] + s), (cap * 0.8, r * 0.2, r * 0.2), "dark", 0.0003)


def body(length, eye, rear_in, rear_out, front_in, front_out, waist):
    half = length / 2
    lip = length * 0.22
    shell(eye, [(half, rear_out), (half - lip, rear_out), (half - lip - 0.002, waist), (-half + lip + 0.002, waist), (-half + lip, front_out), (-half, front_out), (-half, front_in), (half - 0.0015, rear_in), (half, rear_in + 0.0008)], "dark")
    mount(length * 0.92, 0.002)
    gap = eye - waist
    box((0, 0, 0.009 + gap / 2), (0.019, length * 0.6, max(gap - 0.001, 0.003)), "body", 0.0015)

    for y in (-length * 0.2, length * 0.2):
        knob((-0.0115, y, 0.0075), "x", 0.0036, 0.004, "dark")


def sight_x2():
    clear()
    eye = 0.028
    body(0.04, eye, 0.0168, 0.0212, 0.0208, 0.0232, 0.0208 + 0.0006)
    band(eye, -0.0128, -0.0104, 0.0238, 0.0016, "body")
    turret(eye, "right", 0.002, 0.0222, 0.0072, 0.0058, 0.0028)
    turret(eye, "top", 0.002, 0.0218, 0.0058, 0.0045, 0.0025)
    band(eye, 0.0196, 0.0207, 0.0197, 0.0007, "body")
    front = -0.0212
    foot = eye - 0.0212
    tip = eye - 0.0096
    box((0, front, (foot + tip) / 2), (0.0014, 0.0016, tip - foot), "dark", 0.0003)
    box((0, front, tip), (0.0028, 0.002, 0.0016), "dark", 0.0004)

    for x in (-0.0052, 0.0052):
        box((x, front, foot + 0.0045), (0.0012, 0.0016, 0.0085), "dark", 0.0003)

    export("Sight_X2")


def sight_x4():
    clear()
    eye = 0.041
    body(0.046, eye, 0.0215, 0.033, 0.028, 0.0318, 0.029)
    band(eye, 0.017, 0.0235, 0.0342, 0.0022, "body")
    band(eye, -0.0225, -0.019, 0.0326, 0.0018, "body")
    turret(eye, "right", 0.003, 0.033, 0.0128, 0.0095, 0.0046)
    band(eye, 0.0226, 0.0239, 0.0303, 0.0012, "body")
    band(eye, 0.0226, 0.0235, 0.0258, 0.0006, "rail")
    turret(eye, "left", 0.003, 0.0322, 0.0072, 0.0042, 0.0028)
    box((0, 0.004, eye + 0.0345), (0.019, 0.03, 0.0075), "body", 0.0022)
    box((0, 0.004, eye + 0.0399), (0.008, 0.022, 0.0044), "dark", 0.0012)

    for x in (-0.0058, 0.0058):
        box((x, 0.019, eye + 0.0372), (0.0034, 0.005, 0.0034), "rail", 0.0008)

    export("Sight_X4")


def sight_x8():
    clear()
    eye = 0.054
    body(0.056, eye, 0.029, 0.046, 0.0418, 0.0462, 0.0432)
    band(eye, 0.023, 0.0285, 0.0478, 0.0028, "dark")
    band(eye, 0.0145, 0.0175, 0.0472, 0.003, "body")
    band(eye, -0.006, -0.0015, 0.0446, 0.002, "rail")
    band(eye, -0.0285, -0.023, 0.0478, 0.0024, "body")
    turret(eye, "right", 0.004, 0.047, 0.0145, 0.0105, 0.005)
    band(eye, 0.0275, 0.0292, 0.0432, 0.0024, "body")
    band(eye, 0.0275, 0.0288, 0.0372, 0.001, "rail")
    band(eye, 0.0275, 0.0284, 0.0332, 0.0007, "body")
    turret(eye, "left", 0.004, 0.0465, 0.011, 0.0065, 0.0042)
    turret(eye, "top", 0.004, 0.0462, 0.012, 0.008, 0.0045)
    export("Sight_X8")


for name, make in (
    ("Optic_Dot", red_dot),
    ("Optic_Holo", holo),
    ("Optic_Scope2", lambda: scope("Optic_Scope2", 0.12, 0.011, 0.015, 0.0135, False, 0.026)),
    ("Optic_Scope4", lambda: scope("Optic_Scope4", 0.18, 0.012, 0.02, 0.0145, True, 0.04)),
    ("Optic_Scope8", lambda: scope("Optic_Scope8", 0.25, 0.013, 0.026, 0.015, True, 0.06)),
    ("Sight_X2", sight_x2),
    ("Sight_X4", sight_x4),
    ("Sight_X8", sight_x8),
):
    if not ONLY or name in ONLY:
        make()


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
