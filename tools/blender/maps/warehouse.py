import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pf import *

BUILDINGS = [
    ("bay", "warehouse-roof-bay-c8aa9a"),
]

PROPS = [
    ("pallet", "timber-eur-pallet-a1f655"),
    ("load", "stretch-wrapped-pallet-load-b4169b"),
    ("tote", "ibc-tote-88385a"),
    ("barrier", "pedestrian-safety-barrier-run-2afeca"),
    ("cage", "roll-cage-trolley-0ccae7"),
    ("jack", "manual-pallet-jack-1a842e", {"collide": "none"}),
]

run("warehouse", BUILDINGS, PROPS)
