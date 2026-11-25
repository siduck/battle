import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DIR"] = "coast"
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|^icosphere|shadow|ground.?plane|^plane|fisherman|holidaymaker|lifeguard$|swimmer|gull|crab", re.I)

CACHE = os.path.dirname(P.rstrip("/"))
FOAM = (0.93, 0.97, 0.98)


def src_of(src):
    if src.startswith("/"):
        return src

    for d in ("coast", "coast_x", "racing", "islands_x"):
        p = os.path.join(CACHE, d, src + ".glb")

        if os.path.exists(p):
            return p

    return os.path.join(P, src + ".glb")


def fresh():
    reset()
    bm = bmesh.new()
    bm.loops.layers.float_color.new("Col")

    return bm


def desat(bm, amount, k=(1, 1, 1)):
    col = bm.loops.layers.float_color["Col"]

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            g = (c[0] + c[1] + c[2]) / 3
            l[col] = tuple(min(1.0, (c[i] + (g - c[i]) * amount) * k[i]) for i in range(3)) + (1.0,)


def swap(src, dst, tol=0.09):
    def go(bm):
        col = bm.loops.layers.float_color["Col"]

        for f in bm.faces:
            for l in f.loops:
                c = l[col]

                if max(abs(c[i] - src[i]) for i in range(3)) < tol:
                    k = sum(c[:3]) / max(sum(src), 1e-3)
                    l[col] = (min(1, dst[0] * k), min(1, dst[1] * k), min(1, dst[2] * k), 1.0)

    return go


def hemisphere(n):
    out = []
    golden = math.pi * (3 - math.sqrt(5))

    for i in range(n):
        z = 1 - (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * golden
        out.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))

    return out


DIRS = hemisphere(28)


def bake_ao(bm, reach=2.2, strength=0.6, floor=0.35, floor_h=0.9, sky=0.12):
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    col = bm.loops.layers.float_color["Col"]
    lo, hi = bounds(bm)
    shade = {}

    for v in bm.verts:
        n = v.normal if v.normal.length > 0.5 else Vector((0, 0, 1))
        t = n.orthogonal().normalized()
        bt = n.cross(t)
        p = v.co + n * 0.015
        hit = 0.0

        for d in DIRS:
            w = t * d.x + bt * d.y + n * d.z
            loc, nor, idx, dist = bvh.ray_cast(p, w, reach)

            if loc is not None:
                hit += (1 - dist / reach) ** 0.5

        occ = hit / len(DIRS)
        k = 1 - strength * occ
        k *= 1 - floor * max(0.0, 1 - (v.co.z - lo.z) / floor_h) * (1 - max(0.0, n.z))
        k *= 1 - sky * max(0.0, -n.z)
        shade[v.index] = max(0.3, k)

    for f in bm.faces:
        for l in f.loops:
            c = l[col]
            k = shade[l.vert.index]
            l[col] = (c[0] * k, c[1] * k, c[2] * k, 1.0)


def ext(src, scale=1.0, k=None, rot=0.0, post=None):
    bm = load(src_of(src))

    if post:
        post(bm)

    if k:
        tint(bm, k)

    normalize(bm, scale=scale, rot=rot)

    return bm


def foam(length=7.0, width=0.9, seed=1):
    bm = fresh()
    n = 14
    k = seed

    for i in range(n):
        k = (k * 1103515245 + 12345) & 0x7FFFFFFF
        x0 = -length / 2 + i * length / n
        x1 = x0 + length / n + 0.05
        w = width * (0.55 + (k % 100) / 220)
        y = math.sin(i * 0.9 + seed) * 0.18
        add_box(bm, (x0, y - w / 2, 0.0), (x1, y + w / 2, 0.035), FOAM)

        if k % 3 == 0:
            add_box(bm, (x0 + 0.1, y + w / 2 + 0.25, 0.0), (x1 - 0.1, y + w / 2 + 0.5, 0.025), (0.8, 0.92, 0.94))

    return bm


def ripple(length=9.0, seed=4):
    bm = fresh()

    for i in range(10):
        x0 = -length / 2 + i * length / 10
        x1 = x0 + length / 10 * 0.8
        y = math.sin(i * 0.7 + seed) * 0.4
        add_box(bm, (x0, y - 0.12, 0.0), (x1, y + 0.12, 0.02), (0.62, 0.86, 0.88))

    return bm


def piles():
    bm = fresh()

    for x in (-1.8, 1.8):
        for y in (-1.8, 1.8):
            add_box(bm, (x - 0.16, y - 0.16, -6.0), (x + 0.16, y + 0.16, 0.0), (0.36, 0.3, 0.25))

    add_box(bm, (-2.0, -1.9, -2.4), (2.0, -1.75, -2.2), (0.42, 0.35, 0.28))
    add_box(bm, (-2.0, 1.75, -2.4), (2.0, 1.9, -2.2), (0.42, 0.35, 0.28))

    for y in (-1.8, 1.8):
        add_box(bm, (-2.0, y - 0.1, -0.35), (2.0, y + 0.1, -0.1), (0.4, 0.33, 0.27))

    return bm


def deck():
    bm = fresh()
    k = 5

    for i in range(10):
        k = (k * 1103515245 + 12345) & 0x7FFFFFFF
        c = [(0.62, 0.53, 0.42), (0.56, 0.47, 0.37), (0.66, 0.58, 0.47)][k % 3]
        y0 = -2.0 + i * 0.4
        add_box(bm, (-2.0, y0 + 0.02, -0.1), (2.0, y0 + 0.38, 0.0), c)

    add_box(bm, (-2.0, -2.0, -0.3), (2.0, 2.0, -0.1), (0.36, 0.3, 0.25))

    return bm


def rail():
    bm = fresh()
    add_box(bm, (-2.0, -0.05, 1.0), (2.0, 0.05, 1.1), (0.94, 0.93, 0.9))
    add_box(bm, (-2.0, -0.04, 0.55), (2.0, 0.04, 0.62), (0.94, 0.93, 0.9))

    for x in (-1.9, 0.0):
        add_box(bm, (x - 0.06, -0.06, 0.0), (x + 0.06, 0.06, 1.15), (0.3, 0.42, 0.5))

    return bm


def kerb():
    bm = fresh()
    add_box(bm, (-2.0, -0.2, -0.6), (2.0, 0.2, 0.18), (0.72, 0.7, 0.66))
    add_box(bm, (-2.0, -0.22, 0.12), (2.0, 0.22, 0.2), (0.82, 0.8, 0.76))

    return bm


def road_line():
    bm = fresh()
    add_box(bm, (-1.2, -0.08, 0.0), (1.2, 0.08, 0.02), (0.92, 0.9, 0.82))

    return bm


def b(name, src, scale=1.0, post=None, k=None, rot=0.0):
    return (name, lambda: ext(src, scale, k, rot, post), {"group": "building", "collide": "none", "kind": "building"})


def p(name, src, scale=1.0, group="street", collide="box", post=None, k=None, ao=True, rot=0.0):
    return (name, lambda: ext(src, scale, k, rot, post), {"group": group, "collide": collide, "ao": ao})


def g(name, fn, group="street", collide="none", ao=True):
    return (name, fn, {"group": group, "collide": collide, "ao": ao})


SIDING = (0.56, 0.75, 0.85)
WALL = (0.78, 0.66, 0.49)

PIECES = [
    b("terrace_a", "townhouse-row-unit-b9544b"),
    b("terrace_b", "townhouse-row-unit-b9544b", post=swap(SIDING, (0.6, 0.84, 0.72))),
    b("terrace_c", "townhouse-row-unit-b9544b", post=swap(SIDING, (0.95, 0.72, 0.72))),
    b("terrace_d", "townhouse-row-unit-b9544b", post=swap(SIDING, (0.97, 0.86, 0.55))),
    b("villa", "two-storey-family-house-c63c4a", 0.85),
    b("cottage", "crossing-keeper-s-cottage-de49a4"),
    b("corner", "corner-shop-5aec8c"),
    b("hotel", "brownstone-row-house-1b84fd", 0.9),
    b("tavern", "cove-tavern-5861a6"),
    b("arcade", "amusement-arcade-front-e1caee"),
    b("clock", "clock-tower-752081", 1.1),
    b("boatshed", "boat-shed-74c94f"),
    b("hmhut", "harbour-master-s-hut-226f34"),
    b("toilets", "seafront-toilet-block-c3f643"),
    b("bandstand", "promenade-bandstand-1a71b5"),
    b("kiosk", "beach-cafe-kiosk-9e8f6d"),
    p("hut", "beach-hut-fc7649", group="building"),
    p("hut_b", "beach-hut-fc7649", group="building", post=swap((0.96, 0.95, 0.92), (0.96, 0.74, 0.7), 0.05)),
    p("tower", "lifeguard-tower-183c37", group="building", collide="none"),
    p("cubicles", "changing-cubicle-row-5bac7f", group="building"),
    p("shelter", "promenade-shelter-788f46", group="building", collide="none"),
    p("icecream", "ice-cream-kiosk-on-40a568"),
    p("pierhead", "pier-head-platform-63662b", group="building", collide="none"),
    p("seawall", "sea-wall-run-91e459", group="building", collide="none"),
    p("groyne", "groyne-run-971623", group="building", collide="none"),
    p("revet", "rock-armour-revetment-aea1ca", group="rock", collide="none"),
    p("slipway", "slipway-ramp-1e595f", group="building", collide="none"),
    p("walkover", "dune-walkover-afa2c0", group="street", collide="none"),
    p("dunefence", "dune-fence-run-120153", collide="none"),
    p("bollard", "mooring-bollard-2d4bc9", 0.8, collide="cylinder"),
    p("lamp", "seafront-lamp-post-28bada", collide="cylinder"),
    p("bench", "back-to-back-promenade-8c153b"),
    p("bin", "seafront-litter-bin-2e001f", collide="cylinder"),
    p("buoy", "lifebuoy-on-a-post-57421b", collide="cylinder"),
    p("flag", "beach-flag-pole-2bf334", collide="cylinder"),
    p("parasol", "beach-parasol-fd4530", collide="cylinder"),
    p("windbreak", "beach-windbreak-090d8c", collide="none"),
    p("lounger", "sun-lounger-2b2603"),
    p("driftwood", "driftwood-log-89a68f"),
    p("dinghy", "rowing-dinghy-022673"),
    p("fishboat", "small-fishing-boat-4ac0e3"),
    p("pots", "lobster-pot-stack-d870f0"),
    p("nets", "net-pile-0bd489", collide="none"),
    p("bunting", "bunting-run-2ac207", collide="none", ao=False),
    p("marram", "marram-grass-tuft-8c7a99", 1.2, group="bush", collide="none", ao=False),
    p("phone", "phone-booth-10967f", collide="box"),
    p("picket", "picket-fence-run-9310c1", collide="none"),
    p("fence", "board-privacy-fence-run-319bef", collide="none"),
    p("shed", "backyard-garden-shed-38d79f", 0.75, group="building"),
    p("paving", "promenade-paving-tile-5656ce", group="ground", collide="none", ao=False, k=(0.86, 0.8, 0.72)),
    p("sidewalk", "sidewalk-tile-09d894", group="ground", collide="none", ao=False, k=(0.92, 0.9, 0.86)),
    p("planter", "flower-planter-500ed2", 2.2),
    p("bikes", "campus-bike-rack-386d4d", collide="none"),
    p("newsstand", "newsstand-6dfd65"),
    p("tree", "street-tree-0d33f3", 1.0, group="tree", collide="trunk"),
    p("pine", "sculpted-pine-e45d4f", 2.2, group="tree", collide="trunk", k=(0.86, 0.92, 0.8)),
    p("shrub", "trimmed-foundation-shrub-616ce0", 1.3, group="bush", collide="none", k=(0.72, 0.84, 0.56)),
    p("camper", "camper-van-8d10e2", group="car"),
    p("hatch", "hatchback-80s-e95554", group="car"),
    p("sedan", "boxy-sedan-70s-7d55f7", group="car"),
    g("deck", deck, "building", "none"),
    g("piles", piles, "building", "none"),
    g("rail", rail, "street", "none"),
    g("kerb", kerb, "road", "none", ao=False),
    g("line", road_line, "road", "none", ao=False),
    g("foam", lambda: foam(7.0, 0.9, 1), "ground", "none", ao=False),
    g("ripple", lambda: ripple(9.0, 4), "ground", "none", ao=False),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props/coast")
    os.makedirs(pf.OUT, exist_ok=True)
    infos = {}

    for name, fn, opts in PIECES:
        bm = fn()
        building = opts.get("kind") == "building"
        blocks = []

        if building:
            boxes = footprint(bm)

            for bx in boxes:
                h = column_height(bm, bx)
                small = (bx[2] - bx[0]) * (bx[3] - bx[1]) < 1.2
                add_box(bm, (bx[0] + 0.02, bx[1] + 0.02, -1.5), (bx[2] - 0.02, bx[3] - 0.02, 0.03), (0.62, 0.58, 0.54))
                blocks.append([round(bx[0], 3), round(-bx[3], 3), round(bx[2], 3), round(-bx[1], 3), round(min(h, 3.2) if small else h, 3)])

        if opts.get("ao", True):
            bake_ao(bm)

        lo, hi = bounds(bm)
        info = export(bm, name)
        bm.free()
        info["kind"] = "building" if building else "prop"
        info["group"] = opts["group"]
        info["collide"] = opts["collide"]

        if building:
            info["blocks"] = blocks
            info["w"] = round(max(hi.x - lo.x, 1), 2)
            info["d"] = round(max(hi.y - lo.y, 1), 2)

        infos[name] = info
        print("DONE", name, info["tris"], [round(v, 2) for v in info["min"]], [round(v, 2) for v in info["max"]], len(blocks))

    emit_zig("coast", infos, os.path.join(root, "src/shared/maps/coast_kit.zig"))


main()
