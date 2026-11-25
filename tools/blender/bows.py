import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
import os
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)

PAL = {
    "wood": ((0.42, 0.31, 0.24), 0.7, 0.0),
    "wood_light": ((0.6, 0.47, 0.34), 0.65, 0.0),
    "wood_dark": ((0.27, 0.21, 0.17), 0.75, 0.0),
    "metal": ((0.2, 0.21, 0.23), 0.42, 0.45),
    "steel": ((0.6, 0.62, 0.64), 0.35, 0.5),
    "leather": ((0.16, 0.13, 0.12), 0.8, 0.0),
    "accent": ((0.68, 0.57, 0.33), 0.5, 0.1),
    "string": ((0.86, 0.84, 0.78), 0.8, 0.0),
    "red": ((0.66, 0.3, 0.22), 0.55, 0.0),
    "glow": ((1.0, 0.55, 0.18), 0.4, 0.0),
}


def lin(c):
    return tuple(min(1.0, x / 0.9) for x in c)


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
        zs = [v.co.z for v in me.vertices] or [0]
        lo, hi = min(zs), max(zs)
        span = max(hi - lo, 1e-4)
        attr = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")

        for v in me.vertices:
            up = v.normal.z * 0.5 + 0.5
            h = (v.co.z - lo) / span
            k = 0.74 + 0.16 * up + 0.1 * h
            attr.data[v.index].color = (k, k, k, 1.0)

        me.color_attributes.active_color = attr


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


def finish(o, m, bevel=0.0, segs=2, sub=0):
    o.data.materials.append(mat(m))

    if bevel > 0:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = segs
        b.limit_method = "ANGLE"

    if sub > 0:
        s = o.modifiers.new("s", "SUBSURF")
        s.levels = sub
        s.render_levels = sub

    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    o.select_set(False)

    return o


def box(loc, size, m, bevel=0.004, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)

    return finish(o, m, bevel)


def cyl(p0, p1, r, m, verts=16, bevel=0.0, r1=None):
    p0 = Vector(p0)
    p1 = Vector(p1)
    d = p1 - p0

    if r1 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r1, depth=d.length, location=(p0 + p1) / 2)

    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.normalized().to_track_quat("Z", "Y")

    return finish(o, m, bevel)


def sphere(loc, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)

    return finish(o, m)


def sweep(points, radii, m, xscale=1.0, res=3, ring=8, yscale=1.0):
    cu = bpy.data.curves.new("c", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = max(1, ring // 4 - 1)
    cu.use_fill_caps = True
    cu.resolution_u = res
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)

    for bp, p, r in zip(sp.bezier_points, points, radii):
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
        bp.radius = r

    o = bpy.data.objects.new("sweep", cu)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.scale = (xscale, yscale, 1)
    bpy.ops.object.transform_apply(scale=True)
    o.select_set(False)

    return finish(o, m)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def limb_profile(height, tips_back, recurve):
    pts = []

    for t in [0.0, 0.15, 0.3, 0.45, 0.6, 0.72, 0.82, 0.9, 0.95, 1.0]:
        y = -tips_back * (t ** 1.6)

        if recurve and t > 0.7:
            y += recurve * ((t - 0.7) / 0.3) ** 2.2

        pts.append((y, t * height))

    return pts


def bow(height, tips_back, recurve, limb_mat, riser_mat, tip_mat, width):
    prof = limb_profile(height, tips_back, recurve)

    for side in (1, -1):
        pts = [(0, y, z * side) for y, z in prof[1:]]
        pts.insert(0, (0, prof[1][0] * 0.5, 0.07 * side))
        radii = [1.0 - 0.6 * (i / (len(pts) - 1)) ** 1.3 for i in range(len(pts))]
        sweep(pts, [r * 0.0105 for r in radii], limb_mat, xscale=width, res=5, ring=12)
        tip = pts[-1]
        sphere(tip, 0.0075, tip_mat, scale=(1.3, 1, 1.5))

    sweep([(0, 0.004, -0.11), (0, 0.016, -0.04), (0, 0.016, 0.04), (0, 0.004, 0.11)], [0.016, 0.019, 0.019, 0.016], riser_mat, xscale=1.15, res=8, ring=16)
    sweep([(0, 0.012, -0.05), (0, 0.022, 0.0), (0, 0.012, 0.05)], [0.0185, 0.021, 0.0185], "leather", xscale=1.2, res=8, ring=16)

    for i in range(7):
        z = -0.045 + i * 0.015
        y = 0.012 + 0.01 * (1 - (z / 0.05) ** 2)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0195, minor_radius=0.0022, major_segments=16, minor_segments=6, location=(0, y, z))
        o = bpy.context.object
        o.scale = (1.2, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        finish(o, "wood_dark")
    box((0.016, 0.02, 0.06), (0.006, 0.018, 0.012), riser_mat, 0.002)

    print("TIPS", height, -prof[-1][0])


def arrow(length=0.61, scale=1.0):
    s = scale
    cyl((0, -0.30 * s, 0), (0, 0.25 * s, 0), 0.0055 * s, "wood", verts=8)
    cyl((0, 0.25 * s, 0), (0, 0.31 * s, 0), 0.012 * s, "steel", verts=8, r1=0.0)
    cyl((0, -0.31 * s, 0), (0, -0.29 * s, 0), 0.007 * s, "accent", verts=8)

    for a in (0, 120, 240):
        r = math.radians(a)
        d = Vector((math.cos(r), 0, math.sin(r)))
        bpy.ops.mesh.primitive_cube_add(size=1)
        o = bpy.context.object
        o.scale = (0.022 * s, 0.065 * s, 0.0015 * s)
        o.location = Vector((0, -0.255 * s, 0)) + d * 0.013 * s
        o.rotation_euler = (0, -r, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        finish(o, "red", 0.001)


def tiller(front, back, top, body_mat):
    sweep([(0, back, top - 0.02), (0, (back + front) * 0.5, top - 0.017), (0, front, top - 0.02)], [0.02, 0.021, 0.019], body_mat, xscale=0.85)
    box((0, (back + front) * 0.5, top - 0.003), (0.008, front - back, 0.006), "metal", 0.0015)


def stock(y0, y1, z, m):
    sweep([(0, y0 + 0.02, z - 0.02), (0, (y0 + y1) / 2, z - 0.033), (0, y1, z - 0.048)], [0.02, 0.025, 0.032], m, xscale=0.75)
    box((0, y1 - 0.005, z - 0.05), (0.03, 0.02, 0.07), "leather", 0.006)


def grip_trigger(y, z, m):
    box((0, y, z - 0.065), (0.022, 0.028, 0.07), m, 0.007, rot=(math.radians(-14), 0, 0))
    sweep([(0, y + 0.03, z - 0.03), (0, y + 0.05, z - 0.055), (0, y + 0.01, z - 0.062)], [0.003, 0.003, 0.003], "metal")
    box((0, y + 0.035, z - 0.04), (0.005, 0.006, 0.02), "metal", 0.0015)


def prod(y, z, span, back, m, tip_m):
    for side in (1, -1):
        pts = [(0.02 * side, y, z), (span * 0.5 * side, y - back * 0.35, z), (span * side, y - back, z)]
        sweep(pts, [0.013, 0.011, 0.008], m, xscale=1.0)
        sphere((span * side, y - back, z), 0.009, tip_m)

    box((0, y, z), (0.05, 0.03, 0.03), "metal", 0.005)

    return (span, y - back)


def crossbow():
    top = 0.022
    tiller(0.2, -0.17, top, "wood")
    stock(-0.17, -0.3, top, "wood")
    grip_trigger(-0.12, top, "wood_dark")
    tx, ty = prod(0.17, top - 0.005, 0.22, 0.07, "metal", "accent")
    latch = (0, -0.04, top + 0.002)

    for side in (1, -1):
        cyl((tx * side, ty, top - 0.005), latch, 0.0018, "string", verts=6)

    box((0, -0.04, top + 0.006), (0.016, 0.014, 0.01), "metal", 0.003)
    box((0, 0.21, top - 0.02), (0.03, 0.016, 0.03), "metal", 0.005)
    cyl((-0.025, 0.205, top - 0.03), (0.025, 0.205, top - 0.03), 0.006, "accent", verts=10)


def rapid():
    top = 0.022
    tiller(0.17, -0.16, top, "metal")
    stock(-0.16, -0.26, top, "wood_dark")
    grip_trigger(-0.11, top, "wood_dark")
    tx, ty = prod(0.15, top - 0.005, 0.17, 0.05, "wood_dark", "accent")
    latch = (0, -0.02, top + 0.002)

    for side in (1, -1):
        cyl((tx * side, ty, top - 0.005), latch, 0.0018, "string", verts=6)

    sweep([(0, -0.035, top + 0.012), (0, 0.0, top + 0.03), (0, 0.06, top + 0.032), (0, 0.1, top + 0.016)], [0.012, 0.016, 0.016, 0.011], "wood", xscale=1.0, yscale=1.0, res=8, ring=16)
    sweep([(0, -0.02, top + 0.034), (0, 0.02, top + 0.045), (0, 0.06, top + 0.046), (0, 0.09, top + 0.03)], [0.004, 0.004, 0.004, 0.004], "accent", res=6, ring=8)
    sweep([(0.012, -0.06, top + 0.002), (0.016, -0.09, top + 0.03), (0.016, -0.11, top + 0.05)], [0.004, 0.004, 0.0035], "metal", res=6, ring=8)
    sphere((0.016, -0.112, top + 0.052), 0.008, "accent")
    sphere((0, -0.03, top + 0.03), 0.004, "red")


def torch():
    cyl((-0.05, 0, 0.02), (0.36, 0, 0.02), 0.03, "metal", verts=20, bevel=0.003)
    cyl((0.36, 0, 0.02), (0.5, 0, 0.02), 0.016, "steel", verts=16)
    cyl((0.5, 0, 0.02), (0.56, 0, 0.02), 0.024, "metal", verts=16, r1=0.03)
    cyl((0.395, 0, 0.02), (0.41, 0, 0.02), 0.034, "accent", verts=20, bevel=0.002)
    cyl((0.295, 0, 0.02), (0.31, 0, 0.02), 0.034, "accent", verts=20, bevel=0.002)
    sphere((0.535, 0.0, -0.014), 0.008, "glow")
    cyl((0.52, 0, -0.005), (0.52, 0, -0.016), 0.005, "metal", verts=8)
    sweep([(-0.04, 0, 0.02), (-0.14, 0, 0.005), (-0.23, 0, -0.015)], [0.024, 0.027, 0.032], "metal", yscale=0.75)
    box((-0.235, 0, -0.02), (0.02, 0.036, 0.075), "leather", 0.006)
    box((0.06, 0, -0.04), (0.028, 0.022, 0.08), "wood_dark", 0.007, rot=(0, math.radians(12), 0))
    box((0.27, 0, -0.035), (0.022, 0.02, 0.06), "wood_dark", 0.006, rot=(0, math.radians(-8), 0))
    cyl((0.06, -0.075, -0.04), (0.28, -0.075, -0.04), 0.045, "accent", verts=24, bevel=0.004)
    sphere((0.06, -0.075, -0.04), 0.045, "accent", scale=(0.4, 1, 1))
    sphere((0.28, -0.075, -0.04), 0.045, "accent", scale=(0.4, 1, 1))
    cyl((0.12, -0.075, -0.04), (0.128, -0.075, -0.04), 0.047, "metal", verts=24)
    cyl((0.212, -0.075, -0.04), (0.22, -0.075, -0.04), 0.047, "metal", verts=24)
    box((0.17, -0.075, -0.04), (0.24, 0.093, 0.008), "metal", 0.002)
    sweep([(0.29, -0.06, -0.04), (0.33, -0.03, -0.01), (0.34, 0, 0.0)], [0.006, 0.006, 0.006], "leather")
    cyl((0.18, -0.075, 0.005), (0.18, -0.075, 0.02), 0.008, "metal", verts=8)
    box((0.12, 0, 0.055), (0.05, 0.012, 0.014), "metal", 0.003)


def export(name):
    tones()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_apply=True, export_materials="EXPORT", export_texcoords=False, export_normals=True, use_selection=False, export_vertex_color="ACTIVE")


def preview(name, view, tag=""):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_shadows = True
    scene.display.shading.shadow_intensity = 0.3
    scene.display.shading.show_specular_highlight = True
    scene.render.resolution_x = 480
    scene.render.resolution_y = 360
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.46, 0.53, 0.62)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))

    for o in bpy.data.objects:
        if o.type != "MESH":
            continue

        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(min(lo[i], w[i]) for i in range(3))
            hi = Vector(max(hi[i], w[i]) for i in range(3))

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 50
    scene.collection.objects.link(cam)
    scene.camera = cam
    center = (lo + hi) / 2
    size = max(hi - lo)
    cam.location = center + Vector(view).normalized() * size * 2.1
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out, name + tag + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


side = (1.0, 0.25, 0.2)
quarter = (0.9, -0.7, 0.35)

for name, fn, view in [
    ("Bow_Recurve", lambda: bow(0.36, 0.1, 0.05, "wood_light", "wood_dark", "accent", 2.3), side),
    ("Bow_Longbow", lambda: bow(0.44, 0.085, 0.012, "wood_light", "wood", "accent", 1.8), side),
    ("Bow_Crossbow", crossbow, quarter),
    ("Bow_Rapid", rapid, quarter),
    ("Mid_Torch", torch, (0.3, -1.0, 0.35)),
    ("Bow_Arrow", lambda: arrow(), (1.0, 0.0, 0.25)),
    ("Bow_String", lambda: cyl((0, 0, 0), (0, 0, 1), 1.0, "string", verts=6), (1.0, 0.0, 0.25)),
    ("Bow_Bolt", lambda: arrow(scale=0.6), (1.0, 0.0, 0.25)),
]:
    reset()
    fn()
    export(name)
    preview(name, view)
    preview(name, (0.6, -0.8, 0.45), "_q")
