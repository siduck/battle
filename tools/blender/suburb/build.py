import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jp
import buildings

OUT = os.environ.get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".cache-suburb", "mid" if jp.MID else "low")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
REG = dict(buildings.ALL)

for mod in ("props_street", "props_yard", "nature"):
    try:
        REG.update(__import__(mod).ALL)
    except ModuleNotFoundError as e:
        if e.name != mod:
            raise

os.makedirs(OUT, exist_ok=True)

for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue

    ob = fn()
    path = jp.export(ob, OUT, name)
    print("BUILT", name, len(ob.data.polygons), path)
