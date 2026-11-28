import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common as m

OUT = os.environ.get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".cache-midkit", "nyc")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
PREVIEW = os.environ.get("PREVIEW")
REG = {}

for mod in ("buildings_ny", "props_ny"):
    try:
        REG.update(__import__(mod).ALL)
    except ModuleNotFoundError as e:
        if e.name != mod:
            raise

os.makedirs(OUT, exist_ok=True)
built = []

for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue

    ob = fn()
    path = m.export(ob, OUT, name)
    ob.data.calc_loop_triangles()
    print("BUILT", name, len(ob.data.loop_triangles), path)
    built.append(ob)

    if PREVIEW:
        m.k.preview([ob], os.path.join(PREVIEW, name + ".png"), views=("three_quarter",), res=int(os.environ.get("RES", "520")))
