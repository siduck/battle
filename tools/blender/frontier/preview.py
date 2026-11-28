import math
import os
import sys

import bpy
from mathutils import Vector


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out, cols, paths = args[0], int(args[1]), args[2:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    cell = float(os.environ.get("CELL", "0")) or None
    objs = []

    for p in paths:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=p)
        new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
        objs.append(new)

    rows = math.ceil(len(objs) / cols)
    tile = int(os.environ.get("TILE", "420"))
    r = sc.render
    r.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = False
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"
    r.resolution_x = r.resolution_y = tile
    r.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.color = (0.55, 0.62, 0.72)
    cam_data = bpy.data.cameras.new("c")
    cam_data.lens = 60
    cam = bpy.data.objects.new("c", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    view = Vector(tuple(float(v) for v in os.environ.get("VIEW", "0.55,-1,0.45").split(","))).normalized()
    tiles = []

    for i, group in enumerate(objs):
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.hide_render = o not in group

        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(c) for o in group for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), max(min(p.z for p in pts), 0)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        center = (lo + hi) / 2
        radius = max((hi - lo).length / 2, 0.05)
        fov = 2 * math.atan(cam_data.sensor_width / (2 * cam_data.lens))
        dist = radius / math.sin(fov / 2) * 0.98
        cam.location = center + view * dist
        cam.rotation_euler = (-view).to_track_quat("-Z", "Y").to_euler()
        cam_data.clip_end = dist * 6
        path = out + f".{i}.png"
        r.filepath = path
        bpy.ops.render.render(write_still=True)
        tiles.append(path)

    import numpy as np

    sheet = np.ones((rows * tile, cols * tile, 4), dtype=np.float32)

    for i, p in enumerate(tiles):
        im = bpy.data.images.load(p)
        a = np.empty(tile * tile * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        rr, c = rows - 1 - i // cols, i % cols
        sheet[rr * tile:(rr + 1) * tile, c * tile:(c + 1) * tile] = a.reshape(tile, tile, 4)
        bpy.data.images.remove(im)
        os.remove(p)

    im = bpy.data.images.new("s", cols * tile, rows * tile, alpha=True)
    im.pixels.foreach_set(sheet.ravel())
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88
    im.filepath_raw = out
    im.file_format = "JPEG"
    im.save()


sys.path.insert(0, os.environ.get("BPYLIB") or os.path.expanduser("~/.cache/battle/bpylib"))
main()
