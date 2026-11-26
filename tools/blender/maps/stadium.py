import os, sys, re, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pf
from pf import *
import bmesh
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|wisp|steam|icosphere", re.I)

RAYS = 16


def hemisphere(n):
    out = []

    for i in range(n):
        u = (i + 0.5) / n
        r = math.sqrt(u)
        a = i * 2.399963
        out.append((r * math.cos(a), r * math.sin(a), math.sqrt(1 - u)))

    return out


DIRS = hemisphere(RAYS)


def bake_ao(bm, strength=0.62):
    bm.normal_update()
    bm.verts.index_update()
    lo, hi = bounds(bm)
    size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    reach = min(max(size * 0.28, 0.6), 3.2)
    tree = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    cache = {}

    for f in bm.faces:
        n = f.normal

        if n.length < 0.5:
            continue

        t = n.orthogonal().normalized()
        b = n.cross(t)
        c = f.calc_center_median()

        for l in f.loops:
            key = (l.vert.index, round(n.x, 1), round(n.y, 1), round(n.z, 1))
            occ = cache.get(key)

            if occ is None:
                o = l.vert.co + (c - l.vert.co) * 0.1 + n * 0.012
                s = 0.0

                for d in DIRS:
                    w = t * d[0] + b * d[1] + n * d[2]
                    hit = tree.ray_cast(o, w, reach)
                    dist = hit[3] if hit[0] is not None else None

                    if w.z < -0.05 and o.z > 0.0:
                        g = o.z / -w.z

                        if g < reach and (dist is None or g < dist):
                            dist = g

                    if dist is not None:
                        s += 1 - dist / reach

                occ = min(s / len(DIRS) * 1.5, 1.0)
                cache[key] = occ

            k = 1 - strength * occ
            cc = l[col]
            l[col] = (cc[0] * k, cc[1] * k, cc[2] * k, 1.0)


_export = pf.export


def export_baked(bm, name):
    bake_ao(bm)

    return _export(bm, name)


pf.export = export_baked

F = os.path.expanduser("~/.cache/polyfork/forest/")
X = os.path.expanduser("~/.cache/polyfork/stadium_x/")

FONT = {
    "A": ["010", "101", "111", "101", "101"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "I": ["111", "010", "010", "010", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "N": ["101", "111", "111", "101", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "V": ["101", "101", "101", "101", "010"],
    "X": ["101", "101", "010", "101", "101"],
    "Z": ["111", "001", "010", "100", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["110", "001", "010", "100", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "+": ["000", "010", "111", "010", "000"],
    " ": ["000", "000", "000", "000", "000"],
}

WHITE = (0.93, 0.93, 0.9)
DARK = (0.13, 0.14, 0.16)
STEEL = (0.42, 0.45, 0.5)


def fresh():
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    return bm


def box(bm, x0, y0, z0, x1, y1, z1, c):
    add_box(bm, (min(x0, x1), min(y0, y1), min(z0, z1)), (max(x0, x1), max(y0, y1), max(z0, z1)), c)


def text_width(s, px):
    return (len(s) * 4 - 1) * px


def text(bm, s, x0, z0, px, y, c, depth=0.012):
    x = x0

    for ch in s:
        rows = FONT[ch]

        for r, bits in enumerate(rows):
            zt = z0 + (4 - r) * px
            i = 0

            while i < 3:
                if bits[i] != "1":
                    i += 1
                    continue

                j = i

                while j < 3 and bits[j] == "1":
                    j += 1

                box(bm, x + i * px, y, zt, x + j * px, y - depth, zt + px, c)
                i = j

        x += 4 * px


def panel_face(bm, x0, x1, z0, z1, y, design):
    bg, fg, acc, word = design
    box(bm, x0, y, z0, x1, y - 0.01, z1, bg)
    h = z1 - z0
    px = h * 0.12
    w = text_width(word, px)
    cx = (x0 + x1) / 2
    text(bm, word, cx - w / 2 + h * 0.3, z0 + h * 0.2, px, y - 0.01, fg)
    lx = cx - w / 2 - h * 0.55

    box(bm, lx - h * 0.28, y - 0.01, z0 + h * 0.22, lx + h * 0.28, y - 0.025, z1 - h * 0.22, acc)
    box(bm, lx - h * 0.12, y - 0.025, z0 + h * 0.36, lx + h * 0.12, y - 0.035, z1 - h * 0.36, bg)
    box(bm, x0, y - 0.01, z0, x1, y - 0.02, z0 + h * 0.08, acc)

    for s in (-1, 1):
        ex = cx + s * (w / 2 + h * 1.4)

        if x0 + 0.3 < ex < x1 - 0.3:
            box(bm, ex - h * 0.05, y - 0.01, z0 + h * 0.2, ex + h * 0.05, y - 0.02, z1 - h * 0.2, fg)


ADS = {
    "ad_red": ((0.78, 0.13, 0.12), WHITE, (0.98, 0.78, 0.16), "VOLTA"),
    "ad_navy": ((0.09, 0.17, 0.44), WHITE, (0.2, 0.72, 0.86), "NORDA AIR"),
    "ad_gold": ((0.96, 0.74, 0.12), (0.1, 0.1, 0.12), (0.8, 0.16, 0.12), "KICKZ"),
}


def make_adboard(name, design):
    bm = fresh()
    box(bm, -3, -0.06, 0.08, 3, 0.06, 1.0, DARK)
    panel_face(bm, -2.94, 2.94, 0.14, 0.94, -0.06, design)
    back = (0.3, 0.32, 0.36)
    box(bm, -2.94, 0.06, 0.14, 2.94, 0.07, 0.94, back)
    box(bm, -2.94, 0.07, 0.8, 2.94, 0.08, 0.9, design[0])

    for x in (-2.4, 0, 2.4):
        box(bm, x - 0.05, 0.06, 0, x + 0.05, 0.55, 0.9, STEEL)
        box(bm, x - 0.06, -0.1, 0, x + 0.06, 0.6, 0.06, STEEL)

    return finish(bm, name, "box")


def make_standback(name, kind):
    bm = fresh()
    concrete = (0.6, 0.6, 0.57)
    clad = [(0.72, 0.74, 0.76), (0.62, 0.65, 0.69)]
    navy = (0.09, 0.17, 0.44)
    box(bm, -3, 0, 0, 3, 0.45, 0.7, concrete)
    box(bm, -3, -0.06, 0, 3, 0, 0.12, (0.48, 0.48, 0.46))

    for i in range(6):
        box(bm, -3 + i, 0.05, 0.7, -2 + i, 0.4, 5.4, clad[i % 2])
        box(bm, -3 + i - 0.03, 0.02, 0.7, -3 + i + 0.03, 0.05, 5.4, (0.36, 0.38, 0.42))

    box(bm, -3, 0, 5.4, 3, 0.4, 6.5, navy)
    box(bm, -3, -0.02, 6.5, 3, 0.4, 6.68, WHITE)
    box(bm, -3, -0.08, 6.68, 3, 0.45, 6.95, (0.3, 0.32, 0.35))
    box(bm, -3, -0.03, 5.62, 3, 0, 5.7, (0.78, 0.14, 0.12))

    if kind == "gate":
        box(bm, -1.3, -0.08, 0.12, 1.3, 0.05, 3.3, STEEL)
        box(bm, -1.15, -0.1, 0.12, 1.15, -0.08, 3.15, (0.5, 0.53, 0.56))

        for k in range(13):
            z = 0.3 + k * 0.22
            box(bm, -1.15, -0.12, z, 1.15, -0.1, z + 0.05, (0.38, 0.4, 0.44))

        box(bm, -1.5, -0.4, 3.3, 1.5, 0.05, 3.42, DARK)
        box(bm, -1.1, -0.12, 3.55, 1.1, 0.05, 4.35, navy)
        text(bm, "GATE 4", -1.1 + (2.2 - text_width("GATE 4", 0.1)) / 2, 3.7, 0.1, -0.12, WHITE)

        for s in (-1, 1):
            box(bm, s * 2.2 - 0.35, -0.08, 1.0, s * 2.2 + 0.35, 0.05, 2.4, (0.3, 0.32, 0.36))

            for k in range(6):
                z = 1.1 + k * 0.22
                box(bm, s * 2.2 - 0.3, -0.12, z, s * 2.2 + 0.3, -0.08, z + 0.08, (0.55, 0.58, 0.62))

        box(bm, 1.6, -0.1, 2.7, 2.1, 0.05, 2.95, (0.14, 0.6, 0.3))
        box(bm, 1.75, -0.12, 2.76, 1.95, -0.1, 2.89, WHITE)
    else:
        box(bm, -2.7, -0.06, 3.6, 2.7, 0.05, 4.7, STEEL)

        for i in range(4):
            x = -2.6 + i * 1.33
            box(bm, x, -0.09, 3.7, x + 1.2, -0.06, 4.6, (0.16, 0.22, 0.3))
            box(bm, x + 0.58, -0.1, 3.7, x + 0.62, -0.09, 4.6, STEEL)

        for s in (-1, 1):
            box(bm, s * 1.6 - 0.6, -0.08, 0.9, s * 1.6 + 0.6, 0.05, 2.6, (0.3, 0.32, 0.36))

            for k in range(7):
                z = 1.0 + k * 0.22
                box(bm, s * 1.6 - 0.55, -0.12, z, s * 1.6 + 0.55, -0.08, z + 0.08, (0.55, 0.58, 0.62))

        box(bm, -0.35, -0.08, 0.7, 0.35, 0.05, 2.2, (0.34, 0.46, 0.32))
        box(bm, -0.42, -0.1, 0.7, 0.42, -0.08, 0.76, DARK)
        box(bm, -0.25, -0.1, 2.35, 0.25, 0.05, 2.55, (0.14, 0.6, 0.3))
        box(bm, 2.8, -0.2, 0.1, 2.92, -0.08, 6.5, (0.25, 0.27, 0.3))
        box(bm, 2.72, -0.25, 6.3, 3.0, -0.05, 6.45, (0.25, 0.27, 0.3))

    for s in (-1, 1):
        box(bm, s * 2.75 - 0.1, -0.25, 4.95, s * 2.75 + 0.1, 0.0, 5.15, DARK)
        box(bm, s * 2.75 - 0.12, -0.32, 4.86, s * 2.75 + 0.12, -0.18, 4.95, (0.95, 0.92, 0.76))

    return finish(bm, name, "box")


def finish(bm, name, collide):
    info = pf.export(bm, name)
    info["kind"] = "prop"
    info["group"] = "street"
    info["collide"] = collide
    print("DONE", name, info["tris"])

    return info


BUILDINGS = [
    ("clubhouse", "clubhouse-8570d2", {"scale": 1.3}),
    ("firstaid", "first-aid-room-module-56b78b", {"scale": 1.25}),
    ("toilets", "toilet-block-da51a4", {"scale": 1.25}),
    ("pressbox", "press-box-55553b", {"scale": 1.3}),
    ("kiosk", "refreshment-kiosk-406f65", {"scale": 1.25}),
    ("booth", "ticket-booth-d127f8", {"scale": 1.25}),
    ("turnstile", "turnstile-bank-9294b4", {"scale": 1.25}),
    ("tunnel", "players-tunnel-4a210b", {"scale": 1.3}),
    ("gate", "main-entrance-gate-bb6357", {"scale": 1.4, "plinth": None}),
    ("store", "groundsman-s-store-shed-5b6996", {"scale": 1.3}),
    ("snackbox", X + "container-snack-kiosk-7036e5.glb", {"scale": 1.0}),
]

PROPS = [
    ("seats", "grandstand-seating-run-fc9023", {"group": "building", "collide": "none", "scale": 1.5}),
    ("roof", "stand-roof-run-cfd457", {"group": "building", "collide": "none", "scale": 1.5}),
    ("terrace", "terrace-step-run-b631a9", {"group": "building", "collide": "none", "scale": 1.5}),
    ("gable", "stand-gable-end-53847a", {"group": "building", "collide": "none", "scale": 1.5}),
    ("flood", "floodlight-mast-4482be", {"group": "building", "collide": "cylinder", "scale": 1.6}),
    ("mesh", "mesh-perimeter-fence-run-ffce82", {"group": "street", "collide": "box", "scale": 1.2}),
    ("wall", "perimeter-wall-run-adc811", {"group": "street", "collide": "box", "scale": 1.2}),
    ("goal", "match-goal-a98b60", {"group": "street", "collide": "none", "scale": 1.0}),
    ("tgoal", "training-goal-50f1ca", {"group": "street", "collide": "none", "scale": 1.0}),
    ("tarp", "rolled-pitch-tarpaulin-c8a93f", {"group": "street", "collide": "box", "scale": 1.6}),
    ("dummy", "tackle-dummy-06aba2", {"group": "street", "collide": "cylinder", "scale": 1.1}),
    ("sled", "blocking-sled-d83edd", {"group": "street", "collide": "box", "scale": 1.3}),
    ("rack", "equipment-rack-3b617e", {"group": "street", "collide": "box", "scale": 1.3}),
    ("medtent", "sideline-medical-tent-ce1649", {"group": "street", "collide": "box", "scale": 1.2}),
    ("scaffold", "scaffold-camera-platform-b6702c", {"group": "street", "collide": "box", "scale": 1.2}),
    ("inflatable", "inflatable-team-tunnel-c71c5c", {"group": "street", "collide": "box", "scale": 1.1}),
    ("dugout", "team-dugout-ddb70c", {"group": "street", "collide": "box", "scale": 1.2}),
    ("bench", "substitutes-bench-ea0ef7", {"group": "street", "collide": "box", "scale": 1.2}),
    ("scoreboard", "match-scoreboard-58f51e", {"group": "street", "collide": "box", "scale": 1.6}),
    ("flagpole", "flag-pole-015e53", {"group": "street", "collide": "cylinder", "scale": 1.0}),
    ("bin", "ground-litter-bin-aaaba0", {"group": "street", "collide": "cylinder", "scale": 1.3}),
    ("kitbag", "kit-bag-7d617f", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("crate", "water-bottle-crate-78c8db", {"group": "ground", "collide": "box", "scale": 1.4}),
    ("tactics", "tactics-board-21cfd2", {"group": "street", "collide": "box", "scale": 1.2}),
    ("cones", "marker-cone-set-8fab80", {"group": "ground", "collide": "none", "scale": 1.3}),
    ("hurdle", "athletics-hurdle-164f6f", {"group": "street", "collide": "none", "scale": 1.1}),
    ("discus", "discus-cage-2e0e7b", {"group": "street", "collide": "none", "scale": 1.1}),
    ("highjump", "high-jump-apparatus-84ac1d", {"group": "street", "collide": "box", "scale": 1.1}),
    ("cornerflag", "corner-flag-0b43b0", {"group": "street", "collide": "none", "scale": 1.0}),
    ("parasol", X + "cafe-parasol-61a313.glb", {"group": "street", "collide": "cylinder", "scale": 1.0}),
    ("picnic", X + "picnic-table-4ee33a.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("ptoilet", X + "portable-toilet-a3f1a2.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("generator", X + "site-generator-298792.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("jersey", X + "skated-jersey-barrier-7f0a04.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("waterbar", X + "crash-barrier-run-b47d1d.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("stall", X + "welcome-week-tent-stall-c27020.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("pallet", X + "stretch-wrapped-pallet-load-b4169b.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("planter", X + "campus-planter-box-10970a.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("banner", X + "campus-banner-pole-5fdf90.glb", {"group": "street", "collide": "cylinder", "scale": 1.0}),
    ("fence", X + "mesh-site-fence-run-a798a0.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("shelter", X + "park-picnic-shelter-9548a3.glb", {"group": "street", "collide": "none", "scale": 1.0}),
    ("rail", X + "terrace-barrier-set-30dd76.glb", {"group": "street", "collide": "box", "scale": 1.0}),
    ("oak", F + "broadleaf-oak-997c22.glb", {"group": "tree", "collide": "trunk"}),
    ("birch", F + "birch-tree-181b33.glb", {"group": "tree", "collide": "trunk"}),
    ("pine", F + "tall-pine-tree-ab4108.glb", {"group": "tree", "collide": "trunk"}),
    ("bush", F + "round-bush-cd2ac0.glb", {"group": "bush", "collide": "none", "scale": 2.2}),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props", "stadium")
    os.environ["DIR"] = "stadium"
    os.makedirs(pf.OUT, exist_ok=True)
    infos = {}

    for name, parts, opts in BUILDINGS:
        infos[name] = make_building(name, parts, **opts)

    for name, src, opts in PROPS:
        infos[name] = make_prop(name, src, **opts)

    for name, design in ADS.items():
        infos[name] = make_adboard(name, design)

    infos["sback_gate"] = make_standback("sback_gate", "gate")
    infos["sback_wall"] = make_standback("sback_wall", "wall")

    keep = {n + ".glb" for n in infos}

    for f in os.listdir(pf.OUT):
        if f.endswith(".glb") and f not in keep:
            os.remove(os.path.join(pf.OUT, f))

    emit_zig("stadium", infos, os.path.join(root, "src/shared/maps", "stadium_kit.zig"))

    with open(os.path.join(root, "tools/blender/maps", "stadium.json"), "w") as f:
        json.dump(infos, f, indent=1)


main()
