import sys

sys.path.insert(0, "/tmp/claude-1000/-home-siduck/98cd7806-baef-42ae-a165-289c42478511/scratchpad/bpylib")

import bpy
import bmesh
import math
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
outdir = args[0]
parts = []


def G(x, y, z):
    return Vector((x, -z, y))


def mat(name, rgb, rough=0.85):
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
        "glove": mat("glove", (0.33, 0.29, 0.235)),
        "pad": mat("pad", (0.5, 0.42, 0.31), 0.7),
        "strap": mat("strap", (0.18, 0.165, 0.15)),
        "sleeve": mat("sleeve", (0.36, 0.37, 0.25), 0.95),
        "cuff": mat("cuff", (0.28, 0.29, 0.19), 0.95),
    }


K = 1 / 0.45


class Meta:
    def __init__(self, name, m):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = 0.0016
        self.mb.threshold = 0.6
        self.o = bpy.data.objects.new(name, self.mb)
        bpy.context.collection.objects.link(self.o)
        self.o.data.materials.append(m)

    def ball(self, p, r):
        e = self.mb.elements.new()
        e.co = p
        e.radius = r * K
        e.stiffness = 2.0

    def capsule(self, a, b, r):
        d = b - a
        e = self.mb.elements.new()
        e.type = "CAPSULE"
        e.co = (a + b) / 2
        e.radius = r * K
        e.size_x = d.length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
        e.stiffness = 2.0

    def ellipsoid(self, c, ax_w, ax_l, half):
        ax_w = ax_w.normalized()
        ax_l = (ax_l - ax_w * ax_l.dot(ax_w)).normalized()
        ax_n = ax_w.cross(ax_l).normalized()
        e = self.mb.elements.new()
        e.type = "ELLIPSOID"
        e.co = c
        m = Matrix((ax_w, ax_l, ax_n)).transposed()
        e.rotation = m.to_quaternion()
        base = min(half)
        e.radius = base * K
        e.size_x = half[0] / base
        e.size_y = half[1] / base
        e.size_z = half[2] / base
        e.stiffness = 2.0

    def done(self):
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = self.o
        self.o.select_set(True)
        bpy.ops.object.convert(target="MESH")
        o = bpy.context.active_object
        dm = o.modifiers.new("d", "DECIMATE")
        dm.ratio = 0.7
        bpy.ops.object.modifier_apply(modifier="d")
        parts.append(o)

        return o


def tube(points, radii, m, res=3):
    cu = bpy.data.curves.new("t", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    cu.resolution_u = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)

    for bp, q, rr in zip(sp.bezier_points, points, radii):
        bp.co = q
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
        bp.radius = rr

    o = bpy.data.objects.new("t", cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    parts.append(bpy.context.active_object)


def digit(meta, pts, base_r, tip_r):
    n = len(pts)
    radii = [base_r + (tip_r - base_r) * i / (n - 1) for i in range(n)]
    tube(pts, radii, meta.o.data.materials[0], 4)


def sleeve(m, wrist, d, r_wrist, length):
    a = wrist + d * 0.035
    tube([wrist - d * 0.015, wrist + d * 0.015, a], [r_wrist * 0.96, r_wrist, r_wrist * 1.04], m["glove"])
    tube([a - d * 0.004, a + d * 0.016], [r_wrist * 1.12, r_wrist * 1.12], m["strap"])
    c0 = a + d * 0.012
    c1 = c0 + d * 0.032
    tube([c0, c0 + d * 0.016, c1], [r_wrist * 1.3, r_wrist * 1.38, r_wrist * 1.34], m["cuff"])
    end = c1 + d * length
    tube([c1 - d * 0.012, c1 + d * (length * 0.4), end], [r_wrist * 1.22, r_wrist * 1.42, r_wrist * 1.58], m["sleeve"])


def shade_vertex_colors(o):
    me = o.data

    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "POINT")

    ca = me.color_attributes["Col"]
    me.color_attributes.active_color = ca
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    bpy.ops.paint.vertex_color_dirt(blur_strength=0.6, blur_iterations=2, clean_angle=180, dirt_angle=0, dirt_only=False, normalize=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    for i, v in enumerate(me.vertices):
        c = ca.data[i].color
        dirt = c[0]
        up = v.normal.z * 0.5 + 0.5
        k = (0.62 + 0.38 * dirt) * (0.86 + 0.14 * up)
        k = min(1.0, k * 1.05)
        ca.data[i].color = (k, k, k, 1)


def export(path):
    bpy.ops.object.select_all(action="DESELECT")

    for o in parts:
        o.select_set(True)

    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="DESELECT")

    for o in parts:
        o.select_set(True)

    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    shade_vertex_colors(o)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("TRIS", path, tris)

    try:
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_vertex_color="ACTIVE")
    except TypeError:
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_colors=True)

    return o


def render(path, eye, look):
    bpy.ops.object.camera_add(location=eye)
    cam = bpy.context.active_object
    cam.rotation_euler = (Vector(look) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 40
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.render.resolution_x = 600
    sc.render.resolution_y = 600
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def right_arm():
    m = reset()
    slant = 0.25
    gw = 0.019
    gd = 0.026
    hand = Meta("hand", m["glove"])

    def g(x, y, z):
        return G(x, y, z + (-y) * slant)

    for y, scale, r in ((-0.016, 1.0, 0.0090), (-0.034, 0.95, 0.0086), (-0.051, 0.82, 0.0078)):
        k0 = g(gw + 0.008, y, -0.014)
        p1 = g(gw * 0.1, y - 0.002, -(gd + r) * scale)
        p2 = g(-(gw + r), y - 0.003, -0.012 * scale)
        p3 = g(-(gw + r) + 0.003, y - 0.003, 0.008)
        digit(hand, [g(gw + 0.014, y, 0.006), k0, p1, p2, p3], r * 1.05, r * 0.82)

    ki = g(gw + 0.006, 0.003, -0.014)
    digit(hand, [g(gw + 0.012, 0.002, 0.008), ki, g(gw + 0.002, 0.005, -0.046), g(gw, 0.004, -0.07), g(gw - 0.002, 0.001, -0.086)], 0.0092, 0.0074)
    digit(hand, [g(gw - 0.004, -0.056, 0.054), g(-gw * 0.3, -0.036, 0.04), g(-(gw + 0.01), -0.016, 0.02), g(-(gw + 0.012), -0.004, -0.006), g(-(gw + 0.01), 0.0, -0.026)], 0.0125, 0.0085)
    hand.ellipsoid(g(gw + 0.012, -0.03, 0.02), G(0, 1, 0), G(0, 0, 1), (0.034, 0.036, 0.0125))
    hand.ellipsoid(g(gw + 0.006, -0.058, 0.048), G(0, 1, 0), G(0, 0, 1), (0.02, 0.02, 0.014))
    hand.done()
    wrist = g(gw + 0.006, -0.074, 0.066)
    d = Vector((0.12, -0.3, 0.42)).normalized()
    d = G(d.x, d.y, d.z)
    sleeve(m, wrist, d, 0.026, 0.42)
    export(f"{outdir}/arm_r.glb")
    render(f"{outdir}/arm_r.png", G(0.42, 0.25, 0.3), G(0, -0.05, 0))


def left_arm():
    m = reset()
    hr = 0.025
    hand = Meta("hand", m["glove"])

    def ring(phi, z, r):
        t = math.radians(phi)
        R = hr + r

        return G(math.cos(t) * R, math.sin(t) * R, z)

    for z, scale, r in ((-0.036, 0.82, 0.0078), (-0.018, 0.95, 0.0085), (0.0, 1.0, 0.009), (0.018, 0.96, 0.0088)):
        span = 135 * scale
        pts = [G(-0.006, -0.036, z + 0.008)] + [ring(-100 + span * t, z, r) for t in (0.0, 0.3, 0.55, 0.78, 1.0)]
        digit(hand, pts, r * 1.05, r * 0.82)

    t0 = hr + 0.0105
    digit(hand, [G(-0.02, -0.044, 0.038), G(-t0 + 0.002, -0.026, 0.02), G(-t0, -0.008, 0.0), G(-t0 + 0.004, 0.004, -0.018), G(-t0 + 0.009, 0.01, -0.032)], 0.0115, 0.0085)
    hand.ellipsoid(G(-0.006, -(hr + 0.0125), -0.004), G(1, -0.15, 0), G(0, 0, -1), (0.034, 0.036, 0.0125))
    hand.ellipsoid(G(-0.016, -(hr + 0.02), 0.032), G(1, -0.15, 0), G(0, 0, -1), (0.02, 0.02, 0.014))
    hand.done()
    wrist = G(-0.02, -(hr + 0.03), 0.054)
    d = Vector((-0.2, -0.24, 0.5)).normalized()
    d = G(d.x, d.y, d.z)
    sleeve(m, wrist, d, 0.025, 0.42)
    export(f"{outdir}/arm_l.glb")
    render(f"{outdir}/arm_l.png", G(-0.4, 0.2, 0.35), G(0, -0.03, 0))


right_arm()
left_arm()
