import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
preview = args[1] if len(args) > 1 else None

parts = []


def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    m.diffuse_color = (*rgb, 1)

    return m


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts.clear()

    return {
        "glove": mat("glove", (0.2, 0.21, 0.235)),
        "seam": mat("seam", (0.13, 0.135, 0.15)),
        "pad": mat("pad", (0.4, 0.41, 0.43), 0.7),
        "cuff": mat("cuff", (0.3, 0.32, 0.37)),
    }


def tube(points, radii, m, res=2):
    cu = bpy.data.curves.new("t", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    cu.resolution_u = 1
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)

    for p, q, rr in zip(sp.points, points, radii):
        p.co = (*q, 1)
        p.radius = rr

    o = bpy.data.objects.new("t", cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    parts.append(o)

    return o


def ball(p, r, m, squash=(1, 1, 1), seg=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2 + 1, radius=r, location=p)
    o = bpy.context.active_object
    o.scale = squash
    o.data.materials.append(m)
    parts.append(o)

    return o


def slab(p, s, m, rot=(0, 0, 0), bev=0.4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=p, rotation=rot)
    o = bpy.context.active_object
    o.scale = s
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new("b", "BEVEL")
    b.width = min(s) * bev
    b.segments = 3
    b.limit_method = "NONE"
    sub = o.modifiers.new("s", "SUBSURF")
    sub.levels = 1
    o.data.materials.append(m)
    parts.append(o)

    return o


def ring(p, axis, r, thick, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=thick, major_segments=16, minor_segments=6, location=p)
    o = bpy.context.active_object
    o.rotation_euler = Vector(axis).to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m)
    parts.append(o)

    return o


def lerp(a, b, t):
    return a + (b - a) * t


def finger(points, r, m, knuckle=True):
    pts = [Vector(p) for p in points]
    n = len(pts)
    dense = []
    radii = []

    for i in range(n - 1):
        for k in range(4):
            t = k / 4
            taper = lerp(1.0, 0.84, (i + t) / max(1, n - 1))
            pinch = 0.9 + 0.1 * math.sin(math.pi * t)
            dense.append(pts[i].lerp(pts[i + 1], t))
            radii.append(r * taper * pinch)

    dense.append(pts[-1])
    radii.append(r * 0.84 * 0.9)
    tube(dense, radii, m["glove"])
    ball(pts[-1], radii[-1], m["glove"], seg=12)
    ball(pts[0], radii[0], m["glove"], seg=12)


def arc(center, radius, axis, start, end, h, steps=3):
    pts = []

    for k in range(steps + 1):
        t = math.radians(start + (end - start) * k / steps)

        if axis == "z":
            pts.append((center[0] + math.cos(t) * radius, center[1] + math.sin(t) * radius, h))
        else:
            pts.append((center[0] + math.cos(t) * radius, h, center[2] + math.sin(t) * radius))

    return pts


def export(path):
    bpy.ops.object.select_all(action="DESELECT")

    for o in parts:
        o.select_set(True)

    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    parts[:] = [o for o in bpy.context.selected_objects]
    bpy.ops.object.select_all(action="DESELECT")

    for o in parts:
        o.select_set(True)

    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    bpy.ops.object.shade_smooth()
    o = bpy.context.active_object
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("TRIS", path, tris)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True)

    return o


def render(o, path, view):
    bpy.ops.object.camera_add(location=view[0])
    cam = bpy.context.active_object
    d = Vector(view[1]) - Vector(view[0])
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 700
    sc.render.resolution_y = 700
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


m = reset()
grip_r = 0.017
wrap = grip_r + 0.0072

slab((0.006, -0.03, 0.0), (0.03, 0.022, 0.058), m["glove"], (math.radians(8), 0, 0), 0.45)
slab((0.006, -0.0415, 0.004), (0.02, 0.008, 0.036), m["pad"], (math.radians(8), 0, 0), 0.45)

for i, h in enumerate([0.013, -0.003, -0.019]):
    finger(arc((0, 0), wrap, "z", -40, 175, h), 0.0068 - i * 0.0003, m)

finger([(0.022, -0.012, 0.03), (0.02, 0.012, 0.034), (0.012, 0.03, 0.03), (0.004, 0.038, 0.024)], 0.0068, m)
finger([(-0.012, -0.024, 0.02), (-0.026, -0.004, 0.032), (-0.022, 0.016, 0.04)], 0.0082, m, False)
tube([(0.004, -0.036, -0.02), (0.004, -0.04, -0.03)], [0.022, 0.021], m["glove"], 5)
tube([(0.004, -0.04, -0.03), (0.004, -0.05, -0.062)], [0.021, 0.022], m["cuff"], 5)
ring((0.004, -0.041, -0.033), (0, -0.3, -1), 0.0215, 0.0022, m["seam"])
o = export(out + "/hand_r.glb")

if preview:
    render(o, preview + "/hand_r.png", ((0.16, -0.16, 0.07), (0.0, -0.01, -0.005)))

m = reset()
guard_r = 0.022
wrap = guard_r + 0.0072

slab((0.0, 0.0, -0.033), (0.034, 0.05, 0.02), m["glove"], bev=0.45)
slab((0.0, 0.0, -0.044), (0.024, 0.036, 0.008), m["pad"], bev=0.45)

for i, y in enumerate([0.019, 0.005, -0.009, -0.023]):
    finger(arc((0, 0, 0), wrap, "y", -110, 15, y), 0.0064, m)

finger([(-0.016, 0.02, -0.03), (-0.03, 0.028, -0.012), (-0.032, 0.04, 0.006)], 0.008, m, False)
tube([(-0.004, -0.03, -0.045), (-0.012, -0.05, -0.065)], [0.019, 0.02], m["glove"], 5)
tube([(-0.012, -0.05, -0.065), (-0.018, -0.065, -0.085)], [0.02, 0.022], m["cuff"], 5)
ring((-0.012, -0.05, -0.065), (-0.3, -0.7, -0.9), 0.0205, 0.0022, m["seam"])
o = export(out + "/hand_l.glb")

if preview:
    render(o, preview + "/hand_l.png", ((0.0, 0.17, -0.12), (0.0, 0.0, -0.03)))
