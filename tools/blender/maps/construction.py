import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "midkit"))
sys.dont_write_bytecode = True

import construction_core as core
import construction_materials
import construction_site
import construction_tall

OUT = os.environ.get("OUT") or os.path.join(ROOT, "src/client/assets/props/construction")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]


def kit_table():
    text = open(os.path.join(ROOT, "src/shared/maps/construction_kit.zig")).read()
    bounds = {}
    solids = {}

    for name, lo, hi in re.findall(r'construction/(\w+)\.glb".*?\.min = \.\{(.*?)\}, \.max = \.\{(.*?)\}', text):
        bounds[name] = ([float(v) for v in lo.split(",")], [float(v) for v in hi.split(",")])

    for name, body in re.findall(r"pub const (\w+) = \[_\]\[7\]f32\{\n(.*?)\n    \};", text, re.S):
        solids[name] = sorted(tuple(round(float(v), 2) for v in row.split(",")) for row in re.findall(r"\.\{(.*?)\}", body))

    return bounds, solids


def main():
    registry = {}

    for mod in (construction_tall, construction_materials, construction_site):
        registry.update(mod.ALL)

    os.makedirs(OUT, exist_ok=True)
    bounds, solids = kit_table()
    total = 0

    for name, fn in registry.items():
        if ONLY and name not in ONLY:
            continue

        mesh, opts = fn()

        if opts.pop("bake", True):
            tris = core.bake(mesh, **opts)
        else:
            tris = [(p, [n, n, n], [col, col, col]) for p, n, col, _, _ in core.triangulate(mesh.polys)]

        count, lo, hi = core.write_glb(os.path.join(OUT, name + ".glb"), tris)
        total += count
        off = max(max(abs(lo[i] - bounds[name][0][i]), abs(hi[i] - bounds[name][1][i])) for i in range(3))
        print("DONE %s %d min %s max %s off %.2f" % (name, count, [round(v, 2) for v in lo], [round(v, 2) for v in hi], off))

        if mesh.solids and name in solids:
            mine = sorted(tuple(round(float(v), 2) for v in row) for row in mesh.solids)
            kit = solids[name]
            miss = [s for s in kit if not any(max(abs(a - b) for a, b in zip(s, t)) < 0.03 for t in mine)]
            extra = [s for s in mine if not any(max(abs(a - b) for a, b in zip(s, t)) < 0.03 for t in kit)]

            if miss or extra:
                print("DONE solids differ %s kit-only %d recipe-only %d %s %s" % (name, len(miss), len(extra), miss[:4], extra[:4]))

    print("TRIS total", total)


main()
