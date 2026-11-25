import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIR", "kd")
from pf import *

HOUSES = [
    "bank-414f6b",
    "general-store-a2187a",
    "hotel-b43f66",
    "saloon-6dda1c",
    "sheriff-s-office-and-294314",
    "stage-and-freight-office-c5a38a",
    "barber-and-bath-house-e0ff5c",
    "telegraph-and-post-office-71d3ff",
    "blacksmith-s-shop-9c5f43",
    "livery-stable-c01ee0",
    "one-room-schoolhouse-107ec9",
    "miner-s-shack-68b196",
]

PROPS = [
    ("palm_0", "dead-cottonwood-edbde8", 1.2, (0.78, 0.66, 0.54)),
    ("palm_1", "dead-cottonwood-edbde8", 0.95, (0.78, 0.66, 0.54)),
    ("palm_2", "saguaro-cactus-6b27eb", 1.1),
    ("cactus_0", "saguaro-cactus-6b27eb", 0.8),
    ("cactus_1", "prickly-pear-cactus-57e065", 0.8),
    ("scrub", "sagebrush-700b03", 1.0),
    ("tent_0", "ore-chute-and-bin-8375ac", 1.1),
    ("tent_1", "mine-headframe-735cf4", 1.1),
    ("stall_0", "stagecoach-94db88", 1.1),
    ("stall_1", "buckboard-wagon-59ec16", 1.1),
    ("stall_2", "windmill-pump-2993a4", 1.1),
    ("bench", "hitching-rail-run-fc2f66", 1.1),
    ("cart", "mine-cart-21d7f0", 1.1),
    ("crate", "freight-crate-and-sack-f49cbb", 1.1),
    ("box", "freight-crate-and-sack-f49cbb", 1.35),
    ("barrel", "whiskey-barrel-7bb83f", 1.15),
    ("chest", "saddle-on-a-rack-f034cd", 1.1),
    ("fence", "split-rail-fence-run-87da39", 1.2),
    ("lantern", "street-oil-lamp-d246ea", 1.0),
    ("fountain", "water-tower-on-a-dbc730", 1.0),
    ("obelisk", "mine-headframe-735cf4", 1.2),
    ("flag", "telegraph-pole-line-95e382", 1.0),
    ("patch_0", "mine-spoil-gravel-tile-40ae10", 1.3),
    ("patch_1", "tumbleweed-2caa1a", 1.4),
    ("walk", "boardwalk-run-461f03", 1.0),
]


def desert():
    scale = float(os.environ.get("HOUSE_SCALE", "1.25"))
    infos = {}

    for i, src in enumerate(HOUSES):
        name = "house_%d" % i
        bm = load(os.path.join(P, src + ".glb"), door_to=-math.pi / 2)
        normalize(bm, scale=scale)
        boxes = footprint(bm)
        lo, hi = bounds(bm)
        blocks = []

        for b in boxes:
            h = column_height(bm, b)
            small = (b[2] - b[0]) * (b[3] - b[1]) < 1.2
            add_box(bm, (b[0] + 0.02, b[1] + 0.02, -1.0), (b[2] - 0.02, b[3] - 0.02, 0.03), PLINTH)
            blocks.append([round(b[0], 3), round(-b[3], 3), round(b[2], 3), round(-b[1], 3), round(min(h, 3.2) if small else h, 3)])

        info = export(bm, name)
        info["blocks"] = blocks
        info["w"] = round(max(hi.x - lo.x, 1), 2)
        info["d"] = round(max(hi.y - lo.y, 1), 2)
        infos[name] = info
        print("DONE", name, info["tris"], len(blocks))

    for entry in PROPS:
        name, src, k = entry[:3]
        bm = load(os.path.join(P, src + ".glb"))

        if len(entry) > 3:
            tint(bm, entry[3])

        normalize(bm, scale=k)
        infos[name] = export(bm, name)
        print("DONE", name, infos[name]["tris"])

    return infos




def main():
    os.makedirs(OUT, exist_ok=True)
    infos = desert()

    with open(os.environ["JSON"], "w") as f:
        json.dump(infos, f, indent=1)


main()
