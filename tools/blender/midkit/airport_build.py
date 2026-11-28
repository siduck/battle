import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import midkit_core as m

MODULES = ("airport_hangars", "airport_towers", "airport_terminal", "airport_airfield", "airport_ground", "airport_nature")
OUT = os.environ.get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".cache-airport")
ONLY = [n for n in os.environ.get("ONLY", "").split(",") if n]
SHEETS = os.environ.get("SHEETS", "")
REG = {}

for name in MODULES:
    try:
        REG.update(importlib.import_module(name).ALL)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise

os.makedirs(OUT, exist_ok=True)

if SHEETS:
    os.makedirs(SHEETS, exist_ok=True)

for name, fn in REG.items():
    if ONLY and name not in ONLY:
        continue

    ob = fn()
    m.export(ob, OUT, name)
    st = m.k.stats(ob)
    print("BUILT", name, st["tris"], st["dims_m"])

    if SHEETS:
        m.k.preview([ob], os.path.join(SHEETS, name + ".png"), views=("three_quarter", "front"), res=int(os.environ.get("RES", "420")))
