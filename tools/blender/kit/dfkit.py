import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "blender-lpm", "scripts"))
sys.path.insert(0, os.environ.get("BPYLIB", os.path.expanduser("~/.cache/battle/bpylib")))

import bmesh
import bpy
import lpm
from mathutils import Matrix, Vector

box = lpm.box
prism = lpm.prism
lathe = lpm.lathe
sweep = lpm.sweep
plate = lpm.plate
move = lpm.move
rotate = lpm.rotate
scale = lpm.scale
taper = lpm.taper
mirror_x = lpm.mirror_x
paint = lpm.paint

PALETTE = [
    ("plaster", "#d9cdb4"),
    ("plaster_dark", "#b8a98c"),
    ("concrete", "#9c9a92"),
    ("concrete_dark", "#6f6d68"),
    ("brick", "#9a5440"),
    ("stone", "#b3aa98"),
    ("roof", "#7d3b2c"),
    ("roof_dark", "#5c2a20"),
    ("roof_metal", "#5f6b6d"),
    ("wood", "#7a5233"),
    ("wood_light", "#a87a4c"),
    ("wood_dark", "#4f3422"),
    ("trim", "#ece4d0"),
    ("glass", "#2f4552"),
    ("glass_light", "#5d7d8c"),
    ("steel", "#8d949b"),
    ("steel_dark", "#4a4f55"),
    ("olive", "#5b6340"),
    ("olive_dark", "#3f452d"),
    ("khaki", "#a99a6c"),
    ("canvas", "#8f8462"),
    ("rust", "#8b4a2b"),
    ("yellow", "#d4a62a"),
    ("red", "#a23a2c"),
    ("black", "#232323"),
    ("white", "#efece4"),
    ("leaf", "#5d7a3a"),
    ("leaf_dark", "#425a2a"),
    ("bark", "#5a4330"),
    ("sand_paint", "#c9bb98"),
    ("sandstone", "#d8b98c"),
    ("sandstone_dark", "#b8956a"),
    ("pink_plaster", "#d9a48f"),
    ("pink_dark", "#b9826f"),
    ("teal", "#3f8f8c"),
    ("tank_green", "#6f8a5c"),
    ("awning_red", "#c2442f"),
    ("cream", "#efe1c2"),
    ("sand_dark", "#9c8e6d"),
]

_INDEX = {n: i for i, (n, _) in enumerate(PALETTE)}


def c(name):
    return _INDEX[name]


def _srgb(hexs):
    h = hexs.lstrip("#")

    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def reset():
    lpm.reset()


def chamfer(ob, width=0.02, angle=30.0, segments=1):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle)]

    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    return ob


MIN_BEVEL_SIZE = 0.12


def beveled_box(name, size, at=(0, 0, 0), color=0, bevel=0.02, taper_top=(1.0, 1.0)):
    b = box(name, size, at, color, taper_top)

    if bevel <= 0 or min(size) < MIN_BEVEL_SIZE:
        return b

    return chamfer(b, bevel)


def window(name, width, height, at, facing=0.0, depth=0.12, frame=0.07, mullions=(1, 1), sill=True, shutters=False, colors=None):
    k = colors or {}
    x, y, z = at
    frame_col = c(k.get("frame", "trim"))
    glass_col = c(k.get("glass", "glass"))
    parts = []
    parts.append(beveled_box(name + "_glass", (width - frame, depth * 0.3, height - frame), (0, depth * 0.35, frame / 2), glass_col, 0.004))
    parts.append(beveled_box(name + "_top", (width + frame, depth, frame), (0, 0, height - frame / 2), frame_col, 0.012))
    parts.append(beveled_box(name + "_bot", (width + frame, depth, frame), (0, 0, -frame / 2), frame_col, 0.012))
    parts.append(beveled_box(name + "_l", (frame, depth, height), (-width / 2, 0, 0), frame_col, 0.012))
    parts.append(beveled_box(name + "_r", (frame, depth, height), (width / 2, 0, 0), frame_col, 0.012))

    cols, rows = mullions

    for i in range(1, cols):
        px = -width / 2 + width * i / cols
        parts.append(box(name + f"_mv{i}", (frame * 0.45, depth * 0.6, height - frame), (px, depth * 0.1, frame / 2), frame_col))

    for j in range(1, rows):
        pz = height * j / rows
        parts.append(box(name + f"_mh{j}", (width - frame, depth * 0.6, frame * 0.45), (0, depth * 0.1, pz - frame * 0.22), frame_col))

    if sill:
        parts.append(beveled_box(name + "_sill", (width + frame * 2.2, depth * 1.9, frame * 0.8), (0, -depth * 0.45, -frame * 1.2), frame_col, 0.012))
        parts.append(beveled_box(name + "_lintel", (width + frame * 2.6, depth * 1.6, frame * 1.2), (0, -depth * 0.3, height + frame * 0.2), frame_col, 0.012))

    if shutters:
        sc = c(k.get("shutter", "olive"))

        for side in (-1, 1):
            sx = side * (width / 2 + frame + width * 0.26)
            s = beveled_box(name + f"_sh{side}", (width * 0.5, 0.04, height), (sx, -depth * 0.55, 0), sc, 0.008)
            parts.append(s)

            for n in range(3):
                parts.append(box(name + f"_sl{side}{n}", (width * 0.46, 0.02, 0.03), (sx, -depth * 0.55 - 0.03, height * (0.25 + 0.25 * n)), c(k.get("shutter_line", "olive_dark"))))

    for p in parts:
        rotate(p, math.degrees(facing))
        move(p, x, y, z)

    return parts


def door(name, width, height, at, facing=0.0, depth=0.16, frame=0.09, panels=2, colors=None, step=True):
    k = colors or {}
    x, y, z = at
    frame_col = c(k.get("frame", "trim"))
    leaf_col = c(k.get("leaf", "wood"))
    parts = []
    parts.append(beveled_box(name + "_leaf", (width - frame, 0.05, height - frame / 2), (0, depth * 0.3, 0), leaf_col, 0.01))

    for i in range(panels):
        pz = 0.15 + (height - 0.35) * i / panels
        ph = (height - 0.35) / panels - 0.12
        parts.append(beveled_box(name + f"_panel{i}", (width - frame * 3.2, 0.03, ph), (0, depth * 0.3 - 0.035, pz), c(k.get("panel", "wood_dark")), 0.012))

    parts.append(prism(name + "_knob", 8, 0.03, 0.06, (width * 0.3, depth * 0.3 - 0.08, height * 0.45), c("steel"), rotate=0))
    rotate(parts[-1], 90, "X", (width * 0.3, depth * 0.3 - 0.08, height * 0.45))
    parts.append(beveled_box(name + "_top", (width + frame * 2, depth, frame * 1.3), (0, 0, height), frame_col, 0.014))
    parts.append(beveled_box(name + "_l", (frame, depth, height), (-width / 2 - frame / 2, 0, 0), frame_col, 0.014))
    parts.append(beveled_box(name + "_r", (frame, depth, height), (width / 2 + frame / 2, 0, 0), frame_col, 0.014))

    if step:
        parts.append(beveled_box(name + "_step", (width + frame * 4, 0.45, 0.16), (0, -0.28, -0.16), c(k.get("step", "concrete")), 0.02))

    for p in parts:
        rotate(p, math.degrees(facing))
        move(p, x, y, z)

    return parts


def wall(name, width, height, thickness, at, openings=(), color="plaster", facing=0.0, bevel=0.015):
    x0, y0, z0 = at
    cuts = sorted(openings, key=lambda o: o[0])
    parts = []
    col = c(color)
    edges = [-width / 2]
    spans = []

    for ox, oz, ow, oh in cuts:
        spans.append((edges[-1], ox - ow / 2))
        edges.append(ox + ow / 2)
        if oz > 0.001:
            parts.append(beveled_box(name + f"_below{len(parts)}", (ow, thickness, oz), (ox, 0, 0), col, bevel))
        if oz + oh < height - 0.001:
            parts.append(beveled_box(name + f"_above{len(parts)}", (ow, thickness, height - oz - oh), (ox, 0, oz + oh), col, bevel))

    spans.append((edges[-1], width / 2))

    for a, b in spans:
        if b - a > 0.001:
            parts.append(beveled_box(name + f"_pier{len(parts)}", (b - a, thickness, height), ((a + b) / 2, 0, 0), col, bevel))

    for p in parts:
        rotate(p, math.degrees(facing))
        move(p, x0, y0, z0)

    return parts


def gable_roof(name, width, depth, rise, at, overhang=0.35, thickness=0.14, color="roof", trim="trim", ridge="roof_dark", seams=0.6):
    x, y, z = at
    ang = math.atan2(rise, depth / 2)
    half = depth / 2 + overhang
    eave = -overhang * math.tan(ang)
    tv = thickness / math.cos(ang)
    length = width + overhang * 2
    parts = []

    def section(lift, thick):
        return [(-half, eave + lift), (half, eave + lift), (half, eave + lift - thick), (0, rise + lift - thick), (-half, eave + lift - thick), (0, rise + lift)]

    outline = [(-half, eave), (0, rise), (half, eave), (half, eave - tv), (0, rise - tv), (-half, eave - tv)]
    slab = sweep(name + "_slab", outline, length, (0, 0, 0), c(color), axis="y")
    rotate(slab, 90, "Z")
    parts.append(chamfer(slab, 0.025))

    n = int(length / seams)

    for i in range(1, n):
        sx = -length / 2 + length * i / n
        seam_out = [(-half, eave + 0.04), (0, rise + 0.04), (half, eave + 0.04), (half, eave), (0, rise), (-half, eave)]
        seam = sweep(name + f"_seam{i}", seam_out, 0.05, (0, 0, 0), c(ridge), axis="y")
        rotate(seam, 90, "Z")
        move(seam, sx, 0, 0)
        parts.append(seam)

    cap = prism(name + "_ridge", 6, 0.12, length + 0.1, (0, 0, 0), c(ridge), rotate=30)
    rotate(cap, 90, "Y")
    move(cap, -(length + 0.1) / 2, 0, rise + 0.02)
    parts.append(cap)

    for side in (-1, 1):
        tri = sweep(name + f"_gable{side}", [(-depth / 2, 0), (depth / 2, 0), (0, rise - tv * 0.5)], 0.22, (0, 0, 0), c(trim), axis="y")
        rotate(tri, 90, "Z")
        move(tri, side * (width / 2 - 0.11), 0, 0)
        parts.append(chamfer(tri, 0.02))

        board = [(-half, eave + 0.03), (0, rise + 0.03), (half, eave + 0.03), (half, eave - tv - 0.1), (0, rise - tv - 0.1), (-half, eave - tv - 0.1)]
        fascia = sweep(name + f"_fascia{side}", board, 0.09, (0, 0, 0), c(trim), axis="y")
        rotate(fascia, 90, "Z")
        move(fascia, side * (length / 2 + 0.045), 0, 0)
        parts.append(fascia)

    for p in parts:
        move(p, x, y, z)

    return parts


def hip_roof(name, width, depth, rise, at, overhang=0.4, thickness=0.18, color="roof"):
    x, y, z = at
    w = width / 2 + overhang
    d = depth / 2 + overhang
    ridge = max(width - depth, 0.01) / 2
    drop = overhang * rise / (depth / 2)
    pts = [(-w, -d, -drop), (w, -d, -drop), (w, d, -drop), (-w, d, -drop), (-w, -d, -drop - thickness), (w, -d, -drop - thickness), (w, d, -drop - thickness), (-w, d, -drop - thickness), (-ridge, 0, rise), (ridge, 0, rise)]
    bm = bmesh.new()
    verts = [bm.verts.new(Vector(p)) for p in pts]
    bmesh.ops.convex_hull(bm, input=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = lpm._object(name, bm, c(color))
    chamfer(ob, 0.03)
    move(ob, x, y, z)

    return [ob]


def pilaster(name, width, height, depth, at, color="trim", capital=True):
    x, y, z = at
    parts = [beveled_box(name, (width, depth, height), (x, y, z), c(color), 0.015)]

    if capital:
        parts.append(beveled_box(name + "_cap", (width * 1.35, depth * 1.35, 0.14), (x, y, z + height - 0.14), c(color), 0.02))
        parts.append(beveled_box(name + "_base", (width * 1.3, depth * 1.3, 0.2), (x, y, z), c(color), 0.02))

    return parts


def stairs(name, width, steps, rise, run, at, facing=0.0, color="concrete", rails=True):
    x, y, z = at
    parts = []

    for i in range(steps):
        p = beveled_box(name + f"_s{i}", (width, run * (steps - i), rise), (0, -run * (steps - i) / 2, rise * i), c(color), 0.015)
        parts.append(p)

    if rails:
        for side in (-1, 1):
            for i in (0, steps - 1):
                parts.append(prism(name + f"_post{side}{i}", 6, 0.03, 0.9, (side * (width / 2 - 0.05), -run * (steps - i) + run / 2, rise * (i + 1)), c("steel_dark")))

            top0 = Vector((side * (width / 2 - 0.05), -run * steps + run / 2, rise + 0.9))
            top1 = Vector((side * (width / 2 - 0.05), -run / 2, rise * steps + 0.9))
            parts.append(_bar(name + f"_rail{side}", top0, top1, 0.03, c("steel_dark")))

    for p in parts:
        rotate(p, math.degrees(facing))
        move(p, x, y, z)

    return parts


def railing(name, length, height, at, posts=5, facing=0.0, color="steel_dark"):
    x, y, z = at
    parts = []

    for i in range(posts):
        px = -length / 2 + length * i / max(posts - 1, 1)
        parts.append(prism(name + f"_p{i}", 6, 0.025, height, (px, 0, 0), c(color)))

    for k, hz in enumerate((height, height * 0.5)):
        parts.append(_bar(name + f"_r{k}", Vector((-length / 2, 0, hz)), Vector((length / 2, 0, hz)), 0.022, c(color)))

    for p in parts:
        rotate(p, math.degrees(facing))
        move(p, x, y, z)

    return parts


def _bar(name, a, b, radius, color, sides=6):
    d = b - a
    p = prism(name, sides, radius, d.length, (0, 0, 0), color)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    p.data.transform(Matrix.Translation(a) @ rot)

    return p


def crate(name, size, at=(0, 0, 0), color="wood", trim="wood_dark", metal="steel_dark", stencil="khaki"):
    sx, sy, sz = size
    x, y, z = at
    b = 0.045
    parts = [beveled_box(name + "_body", (sx - b, sy - b, sz - b), (x, y, z + b / 2), c(color), 0.01)]

    for axis in ("x", "y"):
        for side in (-1, 1):
            for zz in (0, sz - b):
                if axis == "x":
                    parts.append(beveled_box(name + f"_e{axis}{side}{zz}", (sx, b, b), (x, y + side * (sy - b) / 2, z + zz), c(trim), 0.008))
                else:
                    parts.append(beveled_box(name + f"_e{axis}{side}{zz}", (b, sy, b), (x + side * (sx - b) / 2, y, z + zz), c(trim), 0.008))

    for sxn in (-1, 1):
        for syn in (-1, 1):
            parts.append(beveled_box(name + f"_post{sxn}{syn}", (b, b, sz), (x + sxn * (sx - b) / 2, y + syn * (sy - b) / 2, z), c(trim), 0.008))

            for zz in (0, sz - 0.12):
                parts.append(beveled_box(name + f"_corner{sxn}{syn}{zz}", (0.12, 0.12, 0.12), (x + sxn * (sx / 2 - 0.05), y + syn * (sy / 2 - 0.05), z + zz), c(metal), 0.01))

    for side in (-1, 1):
        parts.append(beveled_box(name + f"_slat{side}", (sx * 0.98, 0.02, b), (x, y + side * (sy / 2 + 0.005), z + sz * 0.5 - b / 2), c(trim), 0.006))
        parts.append(box(name + f"_stencil{side}", (sx * 0.32, 0.01, sz * 0.16), (x - sx * 0.18, y + side * (sy / 2 + 0.008), z + sz * 0.62), c(stencil)))

    for side in (-1, 1):
        handle = beveled_box(name + f"_handle{side}", (0.05, 0.16, 0.035), (x + side * (sx / 2 + 0.02), y, z + sz * 0.7), c(metal), 0.008)
        parts.append(handle)

    return parts


def barrel(name, radius, height, at=(0, 0, 0), color="olive", band="olive_dark", sides=16):
    x, y, z = at
    r = radius
    profile = [(0, 0), (r * 0.92, 0), (r, 0.03), (r, height - 0.03), (r * 0.92, height), (r * 0.78, height), (r * 0.78, height - 0.015), (0, height - 0.015)]
    parts = [lathe(name + "_body", profile, sides, (x, y, z), c(color))]

    for hz in (0.04, height * 0.33, height * 0.66, height - 0.05):
        parts.append(prism(name + f"_band{hz:.2f}", sides, r * 1.025, 0.035, (x, y, z + hz - 0.017), c(band)))

    parts.append(prism(name + "_bung", 8, r * 0.09, 0.03, (x + r * 0.5, y, z + height - 0.015), c("steel")))
    parts.append(prism(name + "_cap", 8, r * 0.06, 0.035, (x - r * 0.45, y + r * 0.2, z + height - 0.015), c("steel_dark")))

    return parts


def finish(name, parts, budget=None):
    ob = lpm.finish(name, parts, lpm.Palette([(n, h) for n, h in PALETTE]), budget=budget)
    me = ob.data
    attr = me.attributes.get("lpm_color")
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)

    me.materials.clear()

    for ca in list(me.color_attributes):
        me.color_attributes.remove(ca)

    col = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")

    for poly in me.polygons:
        rgb = _srgb(PALETTE[attr.data[poly.index].value][1]) if attr else (0.8, 0.8, 0.8)

        for li in poly.loop_indices:
            col.data[li].color = (rgb[0], rgb[1], rgb[2], 1.0)

        poly.use_smooth = False

    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = 0
    mat = bpy.data.materials.new("kit")
    mat.use_nodes = True

    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (1, 1, 1, 1)
            n.inputs["Roughness"].default_value = 1.0

    me.materials.append(mat)

    if attr:
        me.attributes.remove(me.attributes["lpm_color"])

    return ob


def stats(ob):
    ob.data.calc_loop_triangles()
    d = ob.dimensions

    return {"name": ob.name, "tris": len(ob.data.loop_triangles), "dims_m": [round(d.x, 3), round(d.y, 3), round(d.z, 3)], "budget": ob.get("lpm_budget")}


def export(ob, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    for o in bpy.context.scene.objects:
        o.select_set(o == ob)

    bpy.context.view_layer.objects.active = ob
    kw = dict(filepath=os.path.abspath(path), export_format="GLB", use_selection=True, export_texcoords=False, export_normals=True, export_materials="EXPORT", export_yup=True, export_apply=True)

    try:
        bpy.ops.export_scene.gltf(export_vertex_color="ACTIVE", **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(export_colors=True, **kw)

    return os.path.abspath(path)


VIEWS = {"elevation": (0, -1, 0.0), "front": (0, -1, 0.25), "right": (1, 0, 0.25), "back": (0, 1, 0.25), "three_quarter": (1, -1, 0.6)}


def preview(obs, out, views=("front", "right", "three_quarter", "back"), res=640, ortho=False, transparent=False):
    import numpy as np

    sc = bpy.context.scene
    r = sc.render
    sh = sc.display.shading
    r.engine = "BLENDER_WORKBENCH"
    r.resolution_x = r.resolution_y = res
    r.resolution_percentage = 100
    r.image_settings.file_format = "PNG"
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sh.show_object_outline = False
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(p) for o in obs for p in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.01)
    cam_data = bpy.data.cameras.new("df_cam")
    cam_data.lens = 50

    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) * 1.08

    r.film_transparent = transparent
    r.image_settings.color_mode = "RGBA" if transparent else "RGB"
    cam = bpy.data.objects.new("df_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    fov = 2 * math.atan(cam_data.sensor_width / (2 * cam_data.lens))
    dist = radius / math.sin(fov / 2) * 1.02
    cam_data.clip_end = dist * 4
    cam_data.clip_start = dist / 1000
    paths = []
    base = os.path.splitext(os.path.abspath(out))[0]

    for v in views:
        d = Vector(VIEWS[v]).normalized()
        cam.location = center + d * dist
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        p = f"{base}_{v}.png"
        r.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)

    tiles = []

    for p in paths:
        im = bpy.data.images.load(p, check_existing=False)
        a = np.empty(res * res * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        tiles.append(a.reshape(res, res, 4))
        bpy.data.images.remove(im)

    cols = 2
    rows = math.ceil(len(tiles) / cols)
    sheet = np.ones((rows * res, cols * res, 4), dtype=np.float32)

    for i, a in enumerate(tiles):
        rr, cc = rows - 1 - i // cols, i % cols
        sheet[rr * res:(rr + 1) * res, cc * res:(cc + 1) * res] = a

    im = bpy.data.images.new("df_sheet", cols * res, rows * res, alpha=True)
    im.pixels.foreach_set(sheet.ravel())
    im.filepath_raw = os.path.abspath(out)
    im.file_format = "PNG"
    im.save()
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cam_data)

    return os.path.abspath(out)


def bake_ao(ob, strength=0.55, samples=24, distance=1.5):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.device = "CPU"
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = distance
    me = ob.data
    base = me.color_attributes["Col"]
    ao = me.color_attributes.new("AO", "BYTE_COLOR", "CORNER")
    me.color_attributes.active_color = ao

    for o in sc.objects:
        o.select_set(o == ob)

    bpy.context.view_layer.objects.active = ob
    bake = sc.render.bake
    bake.target = "VERTEX_COLORS"
    bake.margin = 0
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")

    for i, d in enumerate(base.data):
        a = ao.data[i].color[0]
        k = 1.0 - strength * (1.0 - a)
        c = d.color
        d.color = (c[0] * k, c[1] * k, c[2] * k, 1.0)

    me.color_attributes.remove(me.color_attributes["AO"])
    me.color_attributes.active_color = me.color_attributes["Col"]
    me.color_attributes.render_color_index = 0
    sc.render.engine = "BLENDER_WORKBENCH"

    return ob


def grime(ob, height=0.9, dark=0.72):
    me = ob.data
    col = me.color_attributes["Col"]

    for poly in me.polygons:
        z = min(me.vertices[v].co.z for v in poly.vertices)

        if z > height:
            continue

        k = dark + (1 - dark) * (z / height)

        for li in poly.loop_indices:
            c = col.data[li].color
            col.data[li].color = (c[0] * k, c[1] * k, c[2] * k, 1.0)

    return ob
