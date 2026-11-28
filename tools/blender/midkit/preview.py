import math
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.cache/battle/bpylib"))

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
prefix = args.pop()
views = [tuple(float(v) for v in s.split(",")) for s in os.environ.get("VIEWS", "0.8,-1.0,0.55").split(";")]
rx = int(os.environ.get("RX", "640"))
ry = int(os.environ.get("RY", "480"))
dist = float(os.environ.get("DIST", "1.25"))
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
names = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in names else "BLENDER_EEVEE"
sc.render.resolution_x = rx
sc.render.resolution_y = ry
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.58, 0.68, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sc.collection.objects.link(sun)
sun.data.energy = 4.0
sun.data.color = (1, 0.93, 0.82)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 40
sc.view_settings.view_transform = "Standard"
ground = bpy.data.meshes.new("g")
gv = [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)]
ground.from_pydata(gv, [], [(0, 1, 2, 3)])
gob = bpy.data.objects.new("g", ground)
gm = bpy.data.materials.new("gm")
gm.diffuse_color = (0.45, 0.5, 0.35, 1)
ground.materials.append(gm)
sc.collection.objects.link(gob)

for i, path in enumerate(args):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]

    for o in new:
        o.data.materials.clear()
        o.data.materials.append(mat)

        if len(o.data.color_attributes):
            attr.layer_name = o.data.color_attributes[0].name

    bpy.context.view_layer.update()
    lo = Vector((min((o.matrix_world @ Vector(cc))[j] for o in new for cc in o.bound_box) for j in range(3)))
    hi = Vector((max((o.matrix_world @ Vector(cc))[j] for o in new for cc in o.bound_box) for j in range(3)))
    ctr = (lo + hi) / 2
    size = (hi - lo).length
    stem = os.path.basename(path)[:-4]

    for vi, v in enumerate(views):
        d = Vector(v).normalized()
        cam.location = ctr + d * size * dist
        cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%s_%d.png" % (prefix, stem, vi)
        bpy.ops.render.render(write_still=True)

    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
