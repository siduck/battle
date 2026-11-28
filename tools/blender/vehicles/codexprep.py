import json
import math
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.cache/battle/bpylib"))

import bpy
import mathutils

SRC = os.environ["SRC"]
OUT = os.environ["OUT"]
STYLE = os.environ["STYLE"]

TRUCK = [(s * 1.015, y, 0.5, 0.5, 0.405) for s in (-1, 1) for y in (-1.62, 1.63)]
CARRIER = [(s * 1.015, y, 0.5, 0.5, 0.405) for s in (-1, 1) for y in (-1.62, 1.81)]
TRACTOR = [(s * x, y, r, r, w) for s in (-1, 1) for x, y, r, w in ((0.84, -1.19, 0.407, 0.29), (1.03, 1.12, 0.783, 0.5))]
WHEELS = {"pickup": TRUCK, "carrier": CARRIER, "tractor": TRACTOR}
SAMPLES = int(os.environ.get("SAMPLES", "96"))
AO = float(os.environ.get("AO", "0.27"))
LOW = float(os.environ.get("LOW", "0.9"))
TOP = float(os.environ.get("TOP", "1.0"))

GLASS = (0.009, 0.018, 0.024)
RUBBER = (0.019, 0.021, 0.023)
GLASS_LOW = (84, 100, 114)
GLASS_TOP = (128, 144, 158)
SCREEN_LOW = (150, 165, 178)
SCREEN_TOP = (198, 208, 216)
TYRE = (44, 46, 50)
SIDEWALL = (66, 68, 73)
SHARED = {
    GLASS: GLASS_LOW,
    RUBBER: TYRE,
    (0.022, 0.03, 0.034): (62, 68, 74),
    (0.093, 0.102, 0.109): (118, 124, 130),
    (0.638, 0.03, 0.028): (205, 52, 44),
    (0.784, 0.913, 1.0): (225, 238, 248),
    (1.0, 0.305, 0.024): (250, 160, 52),
}
PAINT = {
    "pickup": {(0.27, 0.105, 0.042): (212, 136, 94), (0.141, 0.044, 0.02): (162, 98, 66)},
    "carrier": {(0.105, 0.144, 0.093): (144, 168, 126), (0.051, 0.07, 0.047): (100, 120, 92)},
    "tractor": {(0.413, 0.238, 0.042): (218, 172, 96), (0.044, 0.112, 0.078): (66, 126, 100)},
}


def srgb(c):
    c = max(0.0, min(1.0, c))

    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def bounds(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
    lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
    hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])

    return lo, hi


def join(objs):
    bpy.ops.object.select_all(action="DESELECT")

    for o in objs:
        o.select_set(True)

    bpy.context.view_layer.objects.active = objs[0]

    if len(objs) > 1:
        bpy.ops.object.join()

    return bpy.context.view_layer.objects.active


def target(rgb):
    table = {**SHARED, **PAINT[STYLE]}
    key = min(table, key=lambda k: sum((a - b) ** 2 for a, b in zip(k, rgb)))

    if sum((a - b) ** 2 for a, b in zip(key, rgb)) < 0.0004:
        return key, tuple(v / 255 for v in table[key])

    return None, tuple(srgb(c) for c in rgb)


def recolour(ob, white):
    me = ob.data
    src = me.color_attributes["Color"]
    values = [tuple(d.color) for d in src.data]
    me.color_attributes.new("Base", "FLOAT_COLOR", "CORNER")
    me.attributes.new("Kind", "INT", "CORNER")
    base = me.color_attributes["Base"]
    kind = me.attributes["Kind"]
    codes = {GLASS: 1, RUBBER: 2}

    for i, (r, g, b, _) in enumerate(values):
        key, rgb = target((r, g, b))
        base.data[i].color = (*rgb, 1.0)
        kind.data[i].value = codes.get(key, 0)

    me.color_attributes.remove(me.color_attributes["Color"])
    me.materials.clear()
    me.materials.append(white)


def bake(ob, others, z0, z1):
    sc = bpy.context.scene
    me = ob.data

    for o in others:
        o.hide_render = True

    me.color_attributes.new("AO", "BYTE_COLOR", "CORNER")
    me.color_attributes.active_color = me.color_attributes["AO"]

    for o in sc.objects:
        o.select_set(o == ob)

    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")

    for o in others:
        o.hide_render = False

    ao = me.color_attributes["AO"]
    base = me.color_attributes["Base"]
    me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    ao = me.color_attributes["AO"]
    base = me.color_attributes["Base"]
    kind = me.attributes["Kind"]
    col = me.color_attributes["Col"]
    mw = ob.matrix_world
    glass_z = [mw @ me.vertices[me.loops[i].vertex_index].co for i in range(len(me.loops)) if kind.data[i].value == 1]
    g0 = min((p.z for p in glass_z), default=0)
    g1 = max((p.z for p in glass_z), default=1)

    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()

        for li in poly.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            t = (p.z - z0) / max(z1 - z0, 1e-4)
            grad = LOW + (TOP - LOW) * min(1.0, t * 1.3)
            a = ao.data[li].color_srgb[0]
            k = (1.0 - AO * (1.0 - a)) * grad * (1.0 + 0.025 * max(0.0, n.z))
            rgb = list(base.data[li].color[:3])
            code = kind.data[li].value

            if code == 1:
                u = (p.z - g0) / max(g1 - g0, 1e-4)
                low, top = (SCREEN_LOW, SCREEN_TOP) if abs(n.y) > 0.5 else (GLASS_LOW, GLASS_TOP)
                rgb = [(lo + (hi - lo) * u) / 255 for lo, hi in zip(low, top)]
                k = 0.6 + 0.4 * k
            elif code == 2 and abs(n.x) > 0.6:
                rgb = [v / 255 for v in SIDEWALL]

            col.data[li].color = (*[max(0.0, min(1.0, v * k)) for v in rgb], 1.0)

    me.color_attributes.remove(me.color_attributes["AO"])
    me.color_attributes.remove(me.color_attributes["Base"])
    me.attributes.remove(me.attributes["Kind"])
    me.color_attributes.active_color = me.color_attributes["Col"]


def setup_bake():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.device = "CPU"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 4
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 0.6
    sc.render.bake.target = "VERTEX_COLORS"
    sc.render.bake.margin = 0
    floor = bpy.data.meshes.new("floor")
    floor.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new("floor", floor)
    sc.collection.objects.link(fo)

    return fo


def export(ob, name):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), export_format="GLB", use_selection=True, export_yup=True, export_texcoords=False, export_normals=True, export_vertex_color="ACTIVE")


def tris(o):
    o.data.calc_loop_triangles()

    return len(o.data.loop_triangles)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    white = bpy.data.materials.new("White")
    white.diffuse_color = (1, 1, 1, 1)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    ob = join(meshes)
    mw = ob.matrix_world.copy()
    ob.parent = None
    ob.matrix_world = mw
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    recolour(ob, white)
    lo, hi = bounds([ob])
    shift = mathutils.Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    ob.data.transform(mathutils.Matrix.Translation(shift))
    wheels = [(mathutils.Vector((x, y, z)) + shift, r, w) for x, y, z, r, w in WHEELS[STYLE]]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    members = [[] for _ in wheels]
    body = []

    for p in parts:
        plo, phi = bounds([p])
        c = (plo + phi) / 2
        sz = phi - plo
        home = None

        for i, (wc, r, w) in enumerate(wheels):
            yz = math.hypot(c.y - wc.y, c.z - wc.z) + max(sz.y, sz.z) / 2
            if yz <= r * 1.12 and plo.x >= wc.x - w * 0.75 and phi.x <= wc.x + w * 0.75:
                home = i
                break

        if home is None:
            body.append(p)
        else:
            members[home].append(p)

    front = min((i for i, (wc, _, _) in enumerate(wheels) if wc.x < 0), key=lambda i: wheels[i][0].y)
    rear = max((i for i, (wc, _, _) in enumerate(wheels) if wc.x < 0), key=lambda i: wheels[i][0].y)
    split_rear = abs(wheels[front][1] - wheels[rear][1]) > 0.01
    keep = {front, rear} if split_rear else {front}
    out_parts = {}

    body_ob = join(body)
    wheel_obs = [join(ps) for ps in members]
    floor = setup_bake()
    z0, z1 = 0.0, hi.z - lo.z
    bake(body_ob, [], z0, z1)

    for i, w in enumerate(wheel_obs):
        if i in keep:
            bake(w, [body_ob, floor] + [o for o in wheel_obs if o != w], z0, z1)
            w.data.transform(mathutils.Matrix.Translation(-wheels[i][0]))
            out_parts[i] = w
        else:
            bpy.data.objects.remove(w)

    bpy.data.objects.remove(floor)
    os.makedirs(OUT, exist_ok=True)
    export(body_ob, "body")
    export(out_parts[front], "wheel")

    if split_rear:
        export(out_parts[rear], "wheelR")

    fc, fr, _ = wheels[front]
    rc, rr, _ = wheels[rear]
    info = {
        "front": [round(fc.x, 3), round(fc.z, 3), round(-fc.y, 3)],
        "rear": [round(rc.x, 3), round(rc.z, 3), round(-rc.y, 3)],
        "radius": [round(fr, 3), round(rr, 3)],
        "wheel_parts": [len(m) for m in members],
        "body_tris": tris(body_ob),
        "wheel_tris": tris(out_parts[front]),
        "body_verts": len(body_ob.data.vertices),
        "dims": [round(v, 3) for v in (hi - lo)],
    }
    json.dump(info, open(os.path.join(OUT, "fleet.json"), "w"))
    print("PREP", json.dumps(info))


main()
