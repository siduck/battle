import json
import math
import os
import sys

sys.path.insert(0, os.environ.get("BPYLIB", os.path.expanduser("~/.cache/battle/bpylib")))

import bmesh
import bpy

files = sys.argv[sys.argv.index("--") + 1:]
rows = []

for path in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]

    if not meshes:
        continue

    bm = bmesh.new()
    colors = set()
    mats = set()

    for o in meshes:
        me = o.data
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        ca = me.color_attributes[0] if len(me.color_attributes) else None

        if ca is not None:
            for d in ca.data:
                c = d.color_srgb
                colors.add((round(c[0] * 15), round(c[1] * 15), round(c[2] * 15)))

        for m in me.materials:
            if m:
                mats.add(m.name)
                bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.node_tree else None

                if bsdf and ca is None:
                    c = bsdf.inputs["Base Color"].default_value
                    colors.add((round(c[0] * 15), round(c[1] * 15), round(c[2] * 15)))

        me2 = bpy.data.meshes.new("t")
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)

    bmesh.ops.triangulate(bm, faces=bm.faces)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    area = sum(f.calc_area() for f in bm.faces)
    size = max(dims)
    thin = 0
    thin_area = 0.0

    for f in bm.faces:
        e = sorted(x.calc_length() for x in f.edges)

        if e[0] < size * 0.012 and e[2] > e[0] * 6:
            thin += 1
            thin_area += f.calc_area()

    seen = set()
    islands = 0
    bm.verts.ensure_lookup_table()

    for v in bm.verts:
        if v.index in seen:
            continue

        islands += 1
        stack = [v]
        seen.add(v.index)

        while stack:
            a = stack.pop()

            for e in a.link_edges:
                b = e.other_vert(a)

                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)

    rows.append({
        "file": os.path.basename(path),
        "tris": len(bm.faces),
        "dims": [round(d, 2) for d in dims],
        "parts": islands,
        "colors": len(colors),
        "mats": len(mats),
        "tris_per_m2": round(len(bm.faces) / max(area, 1e-3), 1),
        "bevel_tri_share": round(thin / max(len(bm.faces), 1), 2),
        "bevel_area_share": round(thin_area / max(area, 1e-6), 3),
    })
    bm.free()

print("ROWS" + json.dumps(rows))
