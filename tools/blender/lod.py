import os
import sys

sys.path.insert(0, os.environ.get("BPYLIB", os.path.expanduser("~/.cache/battle/bpylib")))

import bpy

files = sys.argv[sys.argv.index("--") + 1:]
ratio = float(os.environ.get("LOD_RATIO", "0.25"))
min_tris = int(os.environ.get("LOD_MIN_TRIS", "600"))


def clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def tris(obs):
    return sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs)


for path in files:
    clear()
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [ob for ob in bpy.context.scene.objects if ob.type == "MESH"]

    if not meshes:
        continue

    before = tris(meshes)

    if before < min_tris:
        continue

    for ob in meshes:
        mod = ob.modifiers.new("lod", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)

    out = path[:-4] + ".lod.glb"

    bpy.ops.object.select_all(action="SELECT")
    kw = dict(filepath=out, export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=True)

    try:
        bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_colors=True, **kw)

    print("LOD", os.path.basename(path), before, tris(meshes))
