import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import nature_kit as nk
import jp

OUT = os.environ.get("OUT") or os.path.join(HERE, "..", "..", "..", ".cache-forest", "mid")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
MODULES = ("forest_trees", "forest_nature", "forest_buildings", "forest_props", "forest_camp")
REG = {}

for mod in MODULES:
    try:
        REG.update(importlib.import_module(mod).ALL)
    except ModuleNotFoundError as e:
        if e.name != mod:
            raise

os.makedirs(OUT, exist_ok=True)

for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue

    ob = fn()
    path = jp.export(ob, OUT, name)
    print("BUILT", name, ob["tris"], path)
