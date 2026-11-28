import json
import os
import struct
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
folder, out, view, cols = args[0], args[1], args[2], int(args[3])
names = args[4].split(",")

def load(path, name):
    raw = open(path, "rb").read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + jlen])
    blob = raw[28 + jlen:]
    fmt = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}

    def read(i):
        a = doc["accessors"][i]
        v = doc["bufferViews"][a["bufferView"]]
        f = fmt[a["componentType"]]
        n = width[a["type"]]
        stride = v.get("byteStride", struct.calcsize(f) * n)
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        out = [struct.unpack_from("<%d%s" % (n, f), blob, off + k * stride) for k in range(a["count"])]

        if a.get("normalized") and f == "B":
            out = [tuple(x / 255.0 for x in t) for t in out]

        return out

    verts, faces, cols = [], [], []

    for node in doc["nodes"]:
        if "mesh" not in node:
            continue

        s = node.get("scale", [1, 1, 1])
        t = node.get("translation", [0, 0, 0])

        for p in doc["meshes"][node["mesh"]]["primitives"]:
            pos = read(p["attributes"]["POSITION"])
            col = read(p["attributes"]["COLOR_0"])
            idx = [i[0] for i in read(p["indices"])] if "indices" in p else range(len(pos))
            base = len(verts)

            for q in pos:
                x, y, z = (q[k] * s[k] + t[k] for k in range(3))
                verts.append((x, -z, y))

            cols.extend(col)
            idx = list(idx)

            for k in range(0, len(idx), 3):
                faces.append((base + idx[k], base + idx[k + 1], base + idx[k + 2]))

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")

    for i, d in enumerate(attr.data):
        c = cols[i]
        d.color_srgb = (c[0], c[1], c[2], 1.0)

    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)

    return ob


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
cell = 0.0
rows = (len(names) + cols - 1) // cols
dirs = {"front": Vector((0.0, -1.0, 0.42)), "tq": Vector((0.75, -1.0, 0.55)), "back": Vector((-0.7, 1.0, 0.55)), "side": Vector((1.0, -0.15, 0.4))}
d = dirs[view].normalized()
rot = (-d).to_track_quat("-Z", "Y")
right = rot @ Vector((1, 0, 0))
up = rot @ Vector((0, 1, 0))

for i, name in enumerate(names):
    path = os.path.join(folder, name + ".glb")

    if not os.path.exists(path):
        continue

    new = [load(path, name)]
    pts = [v.co.copy() for v in new[0].data.vertices]
    pts = [p for p in pts if p.z > -0.3] or pts
    us = [p.dot(right) for p in pts]
    vs = [p.dot(up) for p in pts]
    mid = Vector(((max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2))
    size = max(max(us) - min(us), max(vs) - min(vs)) or 1
    k = 0.9 / size
    centre = right * mid.x + up * mid.y
    centre = centre + d * (sum(p.dot(d) for p in pts) / len(pts))
    c, r = i % cols, i // cols
    target = right * c - up * r

    for o in new:
        if o.parent is None:
            o.scale = tuple(s * k for s in o.scale)
            o.location = target + (o.location - centre) * k

cam = bpy.data.cameras.new("c")
cam.type = "ORTHO"
cam.ortho_scale = max(cols, rows)
ob = bpy.data.objects.new("c", cam)
scene.collection.objects.link(ob)
mid = right * (cols - 1) / 2 - up * (rows - 1) / 2
ob.location = mid + d * 50
ob.rotation_euler = rot.to_euler()
scene.camera = ob
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "VERTEX"
sh.show_backface_culling = True
scene.view_settings.view_transform = "Standard"
scene.world = bpy.data.worlds.new("w")
scene.world.color = (0.2, 0.24, 0.27)
scene.render.film_transparent = False
size = int(os.environ.get("CELL", "360"))
scene.render.resolution_x = size * cols
scene.render.resolution_y = size * rows
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 88
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
