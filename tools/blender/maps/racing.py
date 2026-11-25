import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DIR"] = "racing"
import pf
from pf import *
from mathutils.bvhtree import BVHTree

pf.SKIP = re.compile(pf.SKIP.pattern + r"|^icosphere|shadow|ground.?plane|^plane|attendant|waitress|tripper|officer|clerk|trucker", re.I)

CACHE = os.path.dirname(P.rstrip("/"))
FOAM = (0.93, 0.97, 0.98)


def src_of(src):
    if src.startswith("/"):
        return src

    for d in ("racing", "racing_x", "coast_x", "islands_x"):
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


def kerb():
    bm = fresh()

    for i in range(4):
        c = (0.86, 0.16, 0.12) if i % 2 == 0 else (0.95, 0.94, 0.92)
        add_box(bm, (-2.0 + i, -0.6, -0.3), (-1.0 + i, 0.6, 0.08), c)

    return bm


def curb():
    bm = fresh()
    add_box(bm, (-2.0, -0.2, -0.6), (2.0, 0.2, 0.16), (0.72, 0.7, 0.66))
    add_box(bm, (-2.0, -0.22, 0.1), (2.0, 0.22, 0.18), (0.84, 0.82, 0.78))

    return bm


def startline():
    bm = fresh()

    for i in range(14):
        for j in range(2):
            c = (0.95, 0.95, 0.93) if (i + j) % 2 == 0 else (0.12, 0.12, 0.13)
            add_box(bm, (-7.0 + i, -1.0 + j, 0.0), (-6.0 + i, 0.0 + j, 0.02), c)

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


PIECES = [
    b("motel", "motel-office-104c3a"),
    b("rooms", "motel-room-run-089f71"),
    b("canopy", "pump-island-canopy-c3aa62"),
    b("garage", "service-bay-garage-aaf8e0"),
    b("diner", "streamline-diner-car-de9777"),
    b("gifts", "souvenir-stand-4ab3f6"),
    b("vending", "vending-alcove-f786aa"),
    b("shops", "one-storey-shop-row-83c958"),
    b("corner", "corner-shop-5aec8c"),
    b("repair", "auto-repair-garage-b91464"),
    b("ranch", "single-storey-ranch-house-3880ea"),
    b("ticket", "ticket-booth-d127f8"),
    p("tower", "water-tower-7eb7ec", group="building", collide="none"),
    p("stand", "grandstand-seating-run-fc9023", group="building", collide="none"),
    p("roof", "stand-roof-run-cfd457", group="building", collide="none"),
    p("billboard", "roadside-billboard-c3c053", group="building", collide="none"),
    p("pylon", "price-sign-pylon-0305a8", collide="cylinder"),
    p("mesa", "mesa-backdrop-cbadea", group="building", collide="none"),
    p("outcrop", "sandstone-outcrop-75800b", 1.4, group="rock"),
    p("joshua", "joshua-tree-867a2c", group="tree", collide="trunk"),
    p("creosote", "creosote-bush-5b17d5", 1.8, group="bush", collide="none"),
    p("saguaro", "saguaro-cactus-8b588d", group="bush", collide="cylinder"),
    p("weed", "tumbleweed-077954", collide="none"),
    p("pump", "globe-gas-pump-b8e80d"),
    p("rail", "guardrail-d3bd42", collide="none"),
    p("flag", "checkered-flag-81784a", 1.4, collide="none"),
    p("dsign", "diner-sign-ab5f0a", 1.3, collide="cylinder"),
    p("drum", "oil-drum-386c30"),
    p("phone", "phone-booth-10967f"),
    p("picnic", "picnic-table-4ee33a"),
    p("planter", "planter-f0dab0", 2.6),
    p("cone", "traffic-cone-c421e4", collide="none"),
    p("tyres", "tyre-stack-ad4692", 1.2),
    p("light", "traffic-light-5e5ae6", collide="cylinder"),
    p("lamp", "street-lamp-b4fa26", collide="cylinder"),
    p("soda", "soda-vending-machine-4a5347"),
    p("ice", "ice-chest-83c9ed"),
    p("cans", "oil-can-rack-f68976"),
    p("shield", "route-shield-sign-462947", collide="cylinder"),
    p("mileage", "mileage-sign-post-823c56", collide="cylinder"),
    p("lift", "hydraulic-car-lift-a5dd34", collide="none"),
    p("sidewalk", "sidewalk-tile-09d894", group="ground", collide="none", ao=False, k=(0.92, 0.9, 0.86)),
    p("lot", "lane-marking-decal-d1a212", group="ground", collide="none", ao=False),
    g("kerb", kerb, "road", "none", ao=False),
    g("curb", curb, "road", "none", ao=False),
    g("line", road_line, "road", "none", ao=False),
    g("start", startline, "road", "none", ao=False),
]


def main():
    root = os.environ.get("ROOT", os.getcwd())
    pf.OUT = os.path.join(root, "src/client/assets/props/racing")
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

    emit_zig("racing", infos, os.path.join(root, "src/shared/maps/racing_kit.zig"))


main()
