import math
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.cache/battle/bpylib"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))

import bpy
import dfkit as k
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SRC = os.environ.get("SRC", os.path.join(ROOT, "src/client/assets/characters/soldier.glb"))
OUT = os.environ.get("OUT", os.path.join(ROOT, ".cache-suburb/soldier.glb"))
MID = os.environ.get("MID") == "1"
N = 2 if MID else 1
k.set_mid(MID)

UNIFORM = "olive"
UNIFORM_DARK = "olive_dark"
VEST = "khaki"
VEST_DARK = "sand_dark"
GEAR = "steel_dark"
BOOT = "wood_dark"
GLOVE = "black"
HOOD = "steel_dark"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]

for o in [o for o in bpy.data.objects if o.type != "ARMATURE"]:
    bpy.data.objects.remove(o)

for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

B = {b.name: (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm.data.bones}
parts = []


def on(bone, ob):
    parts.append((bone, ob))

    return ob


def c(name):
    return k.c(name)


def limb(bone, r0, r1, color, sides=6, pad0=0.0, pad1=0.0):
    a, b = B[bone]
    d = b - a
    length = d.length + pad0 + pad1
    ob = k.prism(bone, sides * N, r0, length, (0, 0, 0), c(color), radius_top=r1, rotate=180 / (sides * N))
    k.chamfer(ob, 0.012, 30, 1)
    q = d.normalized().to_track_quat("Z", "Y")
    ob.data.transform(q.to_matrix().to_4x4())
    start = a - d.normalized() * pad0
    k.move(ob, start.x, start.y, start.z)

    return on(bone, ob)


def box(bone, size, at, color, bevel=0.015, taper=(1.0, 1.0)):
    ob = k.box(bone, size, at, c(color), taper)

    if min(size) > 0.04:
        k.chamfer(ob, bevel, 30, 1)

    return on(bone, ob)


def lathe(bone, profile, at, color, seg=8):
    return on(bone, k.lathe(bone, profile, seg * N, at, c(color)))


box("DEF-hips", (0.34, 0.22, 0.2), (0, 0.02, 0.86), UNIFORM, 0.03, (1.0, 0.95))
box("DEF-hips", (0.37, 0.25, 0.07), (0, 0.02, 0.98), GEAR, 0.012)

for sx in (-1, 1):
    box("DEF-hips", (0.08, 0.06, 0.1), (sx * 0.15, -0.11, 0.9), VEST_DARK, 0.012)

box("DEF-spine.001", (0.32, 0.2, 0.14), (0, 0.02, 1.04), UNIFORM, 0.03)
box("DEF-spine.002", (0.36, 0.22, 0.16), (0, 0.01, 1.17), UNIFORM, 0.03)
box("DEF-spine.003", (0.42, 0.24, 0.17), (0, 0.0, 1.31), UNIFORM, 0.035, (0.92, 0.9))
box("DEF-spine.002", (0.42, 0.3, 0.36), (0, 0.0, 1.09), VEST, 0.03, (1.0, 0.92))
box("DEF-spine.003", (0.36, 0.26, 0.09), (0, 0.0, 1.38), VEST_DARK, 0.02)

for i, x in enumerate((-0.12, 0.0, 0.12)):
    box("DEF-spine.002", (0.1, 0.07, 0.12), (x, -0.17, 1.12), VEST_DARK, 0.012)
    box("DEF-spine.002", (0.1, 0.075, 0.025), (x, -0.172, 1.235), GEAR, 0.004)

box("DEF-spine.002", (0.07, 0.06, 0.1), (0.16, -0.16, 1.27), VEST_DARK, 0.01)

for sx in (-1, 1):
    box("DEF-spine.003", (0.06, 0.28, 0.04), (sx * 0.12, 0.0, 1.45), VEST_DARK, 0.008)

box("DEF-spine.003", (0.3, 0.18, 0.36), (0, 0.24, 1.08), UNIFORM_DARK, 0.03, (0.95, 0.9))
box("DEF-spine.003", (0.32, 0.2, 0.08), (0, 0.24, 1.42), UNIFORM, 0.02)
box("DEF-spine.003", (0.22, 0.06, 0.16), (0, 0.35, 1.12), VEST_DARK, 0.012)
on("DEF-spine.003", k._bar("antenna", Vector((0.1, 0.27, 1.44)), Vector((0.1, 0.3, 1.78)), 0.008, c("black"), sides=4))

for side, sx in (("L", 1), ("R", -1)):
    box(f"DEF-shoulder.{side}", (0.13, 0.17, 0.11), (sx * 0.2, 0.0, 1.4), VEST, 0.025)
    limb(f"DEF-upper_arm.{side}", 0.068, 0.058, UNIFORM, pad0=0.03)
    box(f"DEF-upper_arm.{side}", (0.09, 0.15, 0.13), (sx * 0.32, 0.07, 1.375), UNIFORM_DARK, 0.02)
    limb(f"DEF-forearm.{side}", 0.06, 0.05, UNIFORM, pad0=0.02)
    lathe(f"DEF-forearm.{side}", [(0, 0), (0.062, 0), (0.065, 0.04), (0.062, 0.07), (0, 0.07)], (0, 0, 0), UNIFORM_DARK)
    parts[-1][1].data.transform(__import__("mathutils").Matrix.Rotation(math.radians(90 * sx), 4, "Y"))
    k.move(parts[-1][1], sx * 0.45, 0.07, 1.44)
    lathe(f"DEF-forearm.{side}", [(0, 0), (0.058, 0), (0.06, 0.06), (0, 0.06)], (0, 0, 0), GLOVE)
    parts[-1][1].data.transform(__import__("mathutils").Matrix.Rotation(math.radians(90 * sx), 4, "Y"))
    k.move(parts[-1][1], sx * 0.69, 0.07, 1.44)
    box(f"DEF-hand.{side}", (0.13, 0.11, 0.045), (sx * 0.81, 0.07, 1.415), GLOVE, 0.015)
    box(f"DEF-hand.{side}", (0.06, 0.04, 0.035), (sx * 0.8, 0.0, 1.405), GLOVE, 0.01)

    limb(f"DEF-thigh.{side}", 0.098, 0.08, UNIFORM, pad0=0.02)
    box(f"DEF-thigh.{side}", (0.07, 0.12, 0.14), (sx * 0.17, -0.0, 0.66), UNIFORM_DARK, 0.015)
    limb(f"DEF-shin.{side}", 0.075, 0.064, UNIFORM, pad0=0.03)
    box(f"DEF-shin.{side}", (0.13, 0.08, 0.14), (sx * 0.09, -0.07, 0.47), GEAR, 0.025)
    lathe(f"DEF-shin.{side}", [(0, 0), (0.075, 0), (0.078, 0.2), (0.072, 0.24), (0, 0.24)], (sx * 0.09, 0.03, 0.06), BOOT)
    box(f"DEF-foot.{side}", (0.13, 0.34, 0.11), (sx * 0.09, -0.09, 0.0), BOOT, 0.03, (0.96, 0.85))
    box(f"DEF-foot.{side}", (0.14, 0.36, 0.03), (sx * 0.09, -0.09, 0.0), "black", 0.008)

lathe("DEF-head", [(0, 0), (0.095, 0), (0.11, 0.06), (0.112, 0.13), (0.1, 0.17), (0, 0.18)], (0, -0.005, 1.615), HOOD)
lathe("DEF-head", [(0, 0), (0.15, 0), (0.16, 0.02), (0.155, 0.07), (0.13, 0.12), (0.08, 0.155), (0, 0.165)], (0, 0.0, 1.735), UNIFORM)
box("DEF-head", (0.3, 0.3, 0.025), (0, 0.0, 1.735), UNIFORM_DARK, 0.008)
box("DEF-head", (0.2, 0.07, 0.05), (0, -0.14, 1.84), "black", 0.01)
box("DEF-head", (0.18, 0.04, 0.03), (0, -0.165, 1.85), "glass", 0.006)

for sx in (-1, 1):
    box("DEF-head", (0.05, 0.1, 0.1), (sx * 0.145, 0.0, 1.66), GEAR, 0.012)

box("DEF-head", (0.08, 0.05, 0.05), (0, 0.155, 1.76), VEST_DARK, 0.01)
total = 0
objs = []

for bone, ob in parts:
    me = ob.data
    attr = me.attributes.get("lpm_color")
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

    for poly in me.polygons:
        rgb = k._keyed(attr.data[poly.index].value) if attr else (0.5, 0.5, 0.5)

        for li in poly.loop_indices:
            col.data[li].color = (rgb[0], rgb[1], rgb[2], 1.0)

        poly.use_smooth = MID

    if attr:
        me.attributes.remove(attr)

    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)

    vg = ob.vertex_groups.new(name=bone)
    vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    total += len(me.polygons)
    objs.append(ob)

for o in bpy.context.scene.objects:
    o.select_set(o in objs)

bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Body"
body.data.name = "Body"

if MID:
    body.data.set_sharp_from_angle(angle=math.radians(38))

mat = bpy.data.materials.new("kit")
mat.use_nodes = True

for n in mat.node_tree.nodes:
    if n.type == "BSDF_PRINCIPLED":
        n.inputs["Base Color"].default_value = (1, 1, 1, 1)
        n.inputs["Roughness"].default_value = 1.0

body.data.materials.append(mat)
body.data.color_attributes.active_color = body.data.color_attributes["Col"]
body.parent = arm
mod = body.modifiers.new("Armature", "ARMATURE")
mod.object = arm

for o in bpy.context.scene.objects:
    o.select_set(o in (arm, body))

bpy.context.view_layer.objects.active = arm
os.makedirs(os.path.dirname(OUT), exist_ok=True)
kw = dict(filepath=OUT, export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=False, export_skins=True, export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True)

try:
    bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
except TypeError:
    bpy.ops.export_scene.gltf(export_colors=True, **kw)

print("SOLDIER", total * 2 if not MID else total, "faces", len(body.data.polygons), "tris~", sum(len(p.vertices) - 2 for p in body.data.polygons), OUT)
