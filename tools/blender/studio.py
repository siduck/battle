import bpy, math, sys, os
from mathutils import Vector
import runpy
recipe, out = sys.argv[-2], sys.argv[-1]
runpy.run_path(recipe, run_name="__main__")
for o in list(bpy.context.scene.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o)
obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mat = bpy.data.materials.new("vc"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
attr = nt.nodes.new("ShaderNodeVertexColor"); attr.layer_name = "Col"
gam = nt.nodes.new("ShaderNodeGamma"); gam.inputs[1].default_value = 2.2
nt.links.new(attr.outputs[0], gam.inputs[0]); nt.links.new(gam.outputs[0], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.9
for o in obs:
    o.data.materials.clear(); o.data.materials.append(mat)
lo = Vector((min(v[i] for o in obs for v in [o.matrix_world @ Vector(c) for c in o.bound_box]) for i in range(3)))
hi = Vector((max(v[i] for o in obs for v in [o.matrix_world @ Vector(c) for c in o.bound_box]) for i in range(3)))
ctr = (lo + hi) / 2; size = (hi - lo).length
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.04, 0.035, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.5; sun.data.color = (1, 0.93, 0.82); sun.data.angle = 0.08
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
d = Vector((1.0, -1.35, 0.55)).normalized()
cam.location = ctr + d * size * 1.15
cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.view_settings.view_transform = "AgX"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
