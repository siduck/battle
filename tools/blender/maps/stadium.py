import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "midkit"))
import pf
from pf import *
import bmesh
import mid_bake

OWN = os.environ.get("OWN", "")
CUR = {"dist": 1.5, "strength": 0.5, "sky": 0.12}


def export_baked(bm, name):
    mid_bake.ao(bm, CUR["dist"], CUR["strength"], sky=CUR["sky"])

    return _export(bm, name)


_export = pf.export
pf.export = export_baked


def own(name):
    return os.path.join(OWN, name + ".glb")


BUILDINGS = [
    ("clubhouse", {}),
    ("firstaid", {}),
    ("toilets", {}),
    ("pressbox", {}),
    ("kiosk", {}),
    ("booth", {}),
    ("turnstile", {}),
    ("tunnel", {}),
    ("gate", {"plinth": None}),
    ("store", {}),
    ("snackbox", {}),
]

PROPS = [
    ("seats", {"group": "building", "collide": "none", "dist": 2.5, "strength": 0.6, "sky": 0.1}),
    ("roof", {"group": "building", "collide": "none", "dist": 2.5, "strength": 0.5, "sky": 0.1}),
    ("terrace", {"group": "building", "collide": "none", "dist": 2.5, "strength": 0.6, "sky": 0.1}),
    ("gable", {"group": "building", "collide": "none", "dist": 3.0, "strength": 0.55, "sky": 0.15}),
    ("flood", {"group": "building", "collide": "cylinder", "dist": 2.5, "strength": 0.5, "sky": 0.1}),
    ("mesh", {"group": "street", "collide": "box"}),
    ("wall", {"group": "street", "collide": "box"}),
    ("goal", {"group": "street", "collide": "none"}),
    ("tgoal", {"group": "street", "collide": "none"}),
    ("tarp", {"group": "street", "collide": "box"}),
    ("dummy", {"group": "street", "collide": "cylinder"}),
    ("sled", {"group": "street", "collide": "box"}),
    ("rack", {"group": "street", "collide": "box"}),
    ("medtent", {"group": "street", "collide": "box"}),
    ("scaffold", {"group": "street", "collide": "box"}),
    ("inflatable", {"group": "street", "collide": "box"}),
    ("dugout", {"group": "street", "collide": "box"}),
    ("bench", {"group": "street", "collide": "box"}),
    ("scoreboard", {"group": "street", "collide": "box"}),
    ("flagpole", {"group": "street", "collide": "cylinder"}),
    ("bin", {"group": "street", "collide": "cylinder"}),
    ("kitbag", {"group": "ground", "collide": "none"}),
    ("crate", {"group": "ground", "collide": "box"}),
    ("tactics", {"group": "street", "collide": "box"}),
    ("cones", {"group": "ground", "collide": "none"}),
    ("hurdle", {"group": "street", "collide": "none"}),
    ("discus", {"group": "street", "collide": "none"}),
    ("highjump", {"group": "street", "collide": "box"}),
    ("cornerflag", {"group": "street", "collide": "none"}),
    ("parasol", {"group": "street", "collide": "cylinder"}),
    ("picnic", {"group": "street", "collide": "box"}),
    ("ptoilet", {"group": "street", "collide": "box"}),
    ("generator", {"group": "street", "collide": "box"}),
    ("jersey", {"group": "street", "collide": "box"}),
    ("waterbar", {"group": "street", "collide": "box"}),
    ("stall", {"group": "street", "collide": "box"}),
    ("pallet", {"group": "street", "collide": "box"}),
    ("planter", {"group": "street", "collide": "box"}),
    ("banner", {"group": "street", "collide": "cylinder"}),
    ("fence", {"group": "street", "collide": "box"}),
    ("shelter", {"group": "street", "collide": "none"}),
    ("rail", {"group": "street", "collide": "box"}),
    ("oak", {"group": "tree", "collide": "trunk", "dist": 3.0, "sky": 0.3}),
    ("birch", {"group": "tree", "collide": "trunk", "dist": 3.0, "sky": 0.3}),
    ("pine", {"group": "tree", "collide": "trunk", "dist": 3.0, "sky": 0.3}),
    ("bush", {"group": "bush", "collide": "none", "sky": 0.3}),
    ("ad_red", {"group": "street", "collide": "box"}),
    ("ad_navy", {"group": "street", "collide": "box"}),
    ("ad_gold", {"group": "street", "collide": "box"}),
    ("sback_gate", {"group": "street", "collide": "box"}),
    ("sback_wall", {"group": "street", "collide": "box"}),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "stadium")
    os.environ["DIR"] = "stadium"
    os.makedirs(pf.OUT, exist_ok=True)
    infos = {}

    for name, opts in BUILDINGS:
        CUR.update({"dist": 3.5, "strength": 0.55, "sky": 0.18})
        infos[name] = make_building(name, own(name), **opts)

    for name, opts in PROPS:
        opts = dict(opts)
        CUR.update({"dist": opts.pop("dist", 1.5), "strength": opts.pop("strength", 0.5), "sky": opts.pop("sky", 0.12)})
        infos[name] = make_prop(name, own(name), **opts)

    keep = {n + ".glb" for n in infos}

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb") and f not in keep:
            os.remove(os.path.join(pf.OUT, f))

    emit_zig("stadium", infos, os.path.join(root, "src/shared/maps", "stadium_kit.zig"))

    with open(os.path.join(root, "tools/blender/maps", "stadium.json"), "w") as f:
        json.dump(infos, f, indent=1)


main()
