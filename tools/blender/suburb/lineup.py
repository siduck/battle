import math
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.cache/battle/bpylib"))

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out = args.pop()
cols = int(os.environ.get("COLS", "5"))
gap = float(os.environ.get("GAP", "3"))
view = os.environ.get("VIEW", "0.75,-1.25,0.55")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
mat = bpy.data.materials.new("vc")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
attr = nt.nodes.new("ShaderNodeVertexColor")
attr.layer_name = "Col"
gam = nt.nodes.new("ShaderNodeGamma")
gam.inputs[1].default_value = 2.2
nt.links.new(attr.outputs[0], gam.inputs[0])
nt.links.new(gam.outputs[0], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
groups = []

for path in args:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]

    for o in new:
        o.data.materials.clear()
        o.data.materials.append(mat)

    groups.append(new)

    for o in new:
        if len(o.data.color_attributes):
            attr.layer_name = o.data.color_attributes[0].name

x = 0.0
row_y = 0.0
widths = []

for i, g in enumerate(groups):
    bpy.context.view_layer.update()
    lo = Vector((min((o.matrix_world @ Vector(cc))[j] for o in g for cc in o.bound_box) for j in range(3)))
    hi = Vector((max((o.matrix_world @ Vector(cc))[j] for o in g for cc in o.bound_box) for j in range(3)))
    w = hi.x - lo.x

    if i and i % cols == 0:
        x = 0.0
        row_y += 14.0

    for o in g:
        o.location.x += x - lo.x
        o.location.y += row_y

    x += w + gap

bpy.context.view_layer.update()
allo = [o for g in groups for o in g]
lo = Vector((min((o.matrix_world @ Vector(cc))[j] for o in allo for cc in o.bound_box) for j in range(3)))
hi = Vector((max((o.matrix_world @ Vector(cc))[j] for o in allo for cc in o.bound_box) for j in range(3)))
ctr = (lo + hi) / 2
size = (hi - lo).length
names = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in names else "BLENDER_EEVEE"
sc.render.resolution_x = int(os.environ.get("RX", "1800"))
sc.render.resolution_y = int(os.environ.get("RY", "900"))
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.04, 0.035, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sc.collection.objects.link(sun)
sun.data.energy = 4.5
sun.data.color = (1, 0.93, 0.82)
sun.data.angle = 0.08
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = float(os.environ.get("LENS", "45"))
d = Vector(tuple(float(v) for v in view.split(","))).normalized()
cam.location = ctr + d * size * float(os.environ.get("DIST", "0.85"))
cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.view_settings.view_transform = "AgX"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
