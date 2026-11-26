import os, sys, json, struct
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


X = os.path.expanduser("~/.cache/polyfork/cprc_x")


def xp(i):
    return os.path.join(X, i + ".glb")


def container(c):
    def go():
        bm = fresh()
        dark = (c[0] * 0.7, c[1] * 0.7, c[2] * 0.7)
        add_box(bm, (-3.0, -1.2, 0.0), (3.0, 1.2, 2.6), c)

        for i in range(13):
            x = -2.9 + i * 0.48
            add_box(bm, (x, -1.26, 0.15), (x + 0.2, 1.26, 2.45), dark)

        for x in (-3.04, 2.96):
            add_box(bm, (x, -1.24, 0.0), (x + 0.08, 1.24, 2.62), (0.22, 0.22, 0.24))

        add_box(bm, (-3.04, -1.24, 2.55), (3.04, 1.24, 2.64), dark)
        add_box(bm, (2.97, -0.5, 0.4), (3.03, -0.45, 2.2), (0.75, 0.75, 0.72))
        add_box(bm, (2.97, 0.45, 0.4), (3.03, 0.5, 2.2), (0.75, 0.75, 0.72))

        return bm

    return go


def jersey():
    bm = fresh()

    for i in range(2):
        x0 = -2.0 + i * 2.0
        c = (0.82, 0.8, 0.76) if i == 0 else (0.76, 0.74, 0.7)
        add_box(bm, (x0 + 0.02, -0.32, 0.0), (x0 + 1.98, 0.32, 0.25), c)
        add_box(bm, (x0 + 0.02, -0.2, 0.25), (x0 + 1.98, 0.2, 0.6), c)
        add_box(bm, (x0 + 0.02, -0.12, 0.6), (x0 + 1.98, 0.12, 0.85), c)
        add_box(bm, (x0 + 0.3, -0.13, 0.62), (x0 + 0.9, 0.13, 0.8), (0.86, 0.16, 0.12))
        add_box(bm, (x0 + 1.1, -0.13, 0.62), (x0 + 1.7, 0.13, 0.8), (0.95, 0.94, 0.92))

    return bm


def tyrewall():
    bm = fresh()
    cols = [(0.86, 0.16, 0.12), (0.95, 0.94, 0.92)]

    for i in range(5):
        for j in range(3):
            x = -2.0 + i * 0.8 + 0.4
            c = cols[(i + j) % 2] if j == 2 else (0.13, 0.13, 0.14)
            add_box(bm, (x - 0.36, -0.36, j * 0.3), (x + 0.36, 0.36, j * 0.3 + 0.28), c)

    add_box(bm, (-2.0, 0.37, 0.05), (2.0, 0.42, 0.85), (0.2, 0.42, 0.72))

    return bm


def squeeze(path):
    raw = open(path, "rb").read()
    jlen = struct.unpack("<I", raw[12:16])[0]
    doc = json.loads(raw[20:20 + jlen])
    bin0 = raw[20 + jlen + 8:]
    acc = doc["accessors"]
    views = doc["bufferViews"]
    sizes = {5126: 4, 5123: 2, 5125: 4, 5121: 1}
    comps = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}

    def read(i):
        a = acc[i]
        v = views[a["bufferView"]]
        n = comps[a["type"]]
        ct = a["componentType"]
        fmt = {5126: "f", 5123: "H", 5125: "I", 5121: "B"}[ct]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", sizes[ct] * n)
        out = []

        for k in range(a["count"]):
            out.append(struct.unpack_from("<%d%s" % (n, fmt), bin0, off + k * stride))

        if a.get("normalized"):
            d = {5123: 65535.0, 5121: 255.0}[ct]
            out = [tuple(x / d for x in t) for t in out]

        return out

    blob = bytearray()
    new_views = []
    new_acc = []

    def push(data, target):
        while len(blob) % 4:
            blob.append(0)

        new_views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)

        return len(new_views) - 1

    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            pos = read(at["POSITION"])
            nor = read(at["NORMAL"]) if "NORMAL" in at else [(0.0, 1.0, 0.0)] * len(pos)
            col = read(at["COLOR_0"]) if "COLOR_0" in at else [(1.0, 1.0, 1.0, 1.0)] * len(pos)
            idx = [t[0] for t in read(prim["indices"])] if "indices" in prim else list(range(len(pos)))
            seen = {}
            vp, vn, vc, out = [], [], [], []

            for i in idx:
                p = pos[i]
                n = nor[i]
                c = tuple(max(0, min(255, int(round(x * 255)))) for x in col[i][:3])
                key = (round(p[0], 4), round(p[1], 4), round(p[2], 4), round(n[0], 2), round(n[1], 2), round(n[2], 2), c)
                j = seen.get(key)

                if j is None:
                    j = len(vp)
                    seen[key] = j
                    vp.append(p)
                    vn.append(n)
                    vc.append(c)

                out.append(j)

            big = len(vp) > 65535
            base = len(new_acc)
            pv = push(b"".join(struct.pack("<3f", *p) for p in vp), 34962)
            nv = push(b"".join(struct.pack("<3f", *n) for n in vn), 34962)
            cv = push(b"".join(struct.pack("<4B", c[0], c[1], c[2], 255) for c in vc), 34962)
            iv = push(struct.pack("<%d%s" % (len(out), "I" if big else "H"), *out), 34963)
            mn = [min(p[k] for p in vp) for k in range(3)]
            mx = [max(p[k] for p in vp) for k in range(3)]
            new_acc.append({"bufferView": pv, "componentType": 5126, "count": len(vp), "type": "VEC3", "min": mn, "max": mx})
            new_acc.append({"bufferView": nv, "componentType": 5126, "count": len(vp), "type": "VEC3"})
            new_acc.append({"bufferView": cv, "componentType": 5121, "normalized": True, "count": len(vp), "type": "VEC4"})
            new_acc.append({"bufferView": iv, "componentType": 5125 if big else 5123, "count": len(out), "type": "SCALAR"})
            prim["attributes"] = {"POSITION": base, "NORMAL": base + 1, "COLOR_0": base + 2}
            prim["indices"] = base + 3

    while len(blob) % 4:
        blob.append(0)

    doc["accessors"] = new_acc
    doc["bufferViews"] = new_views
    doc["buffers"] = [{"byteLength": len(blob)}]
    js = json.dumps(doc, separators=(",", ":")).encode()

    while len(js) % 4:
        js += b" "

    total = 12 + 8 + len(js) + 8 + len(blob)

    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(blob), 0x004E4942))
        f.write(blob)


def squeeze_dir(d):
    for f in sorted(os.listdir(d)):
        if f.endswith(".glb"):
            squeeze(os.path.join(d, f))



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
    p("gazebo", xp("welcome-week-tent-stall-c27020"), 1.4, group="building", collide="none"),
    p("shade", xp("shade-sail-canopy-66c4e4"), 1.6, group="building", collide="none"),
    p("redflag", xp("flagpole-7b7806"), 1.2, collide="cylinder"),
    p("camtower", xp("scaffold-camera-platform-b6702c"), 1.4, group="building"),
    p("snack", xp("container-snack-kiosk-7036e5"), 1.2, group="building"),
    p("fence", xp("terrace-barrier-set-30dd76"), 1.0, collide="none"),
    p("wrap", xp("stretch-wrapped-pallet-load-b4169b")),
    p("ibc", xp("ibc-tote-88385a")),
    p("speed", xp("speed-limit-sign-1c55a2"), collide="cylinder"),
    g("box_red", container((0.7, 0.24, 0.16)), "building", "box"),
    g("box_blue", container((0.18, 0.34, 0.56)), "building", "box"),
    g("box_white", container((0.82, 0.8, 0.76)), "building", "box"),
    g("jersey", jersey, "street", "box"),
    g("tyrewall", tyrewall, "street", "box"),
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
    squeeze_dir(pf.OUT)


main()
