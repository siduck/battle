import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import arena_parts
import jp

MODULES = ("stadium_stands", "stadium_buildings", "stadium_street", "stadium_field", "stadium_nature")
OUT = os.environ.get("OUT") or os.path.join(HERE, "..", "..", "..", ".cache-stadium")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
REG = {}

for mod in MODULES:
    try:
        m = __import__(mod)
    except ModuleNotFoundError as e:
        if e.name != mod:
            raise

        continue

    REG.update(m.ALL)

os.makedirs(OUT, exist_ok=True)

for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue

    ob = fn()
    path = jp.export(ob, OUT, name)
    print("BUILT", name, len(ob.data.polygons), path)
