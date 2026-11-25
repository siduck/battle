import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bmesh
import math
from mathutils import Vector
from veh import Kit, G, hexc, render

OUT = os.environ.get("CARS_OUT", "/tmp/cars_out")
ONLY = [s for s in os.environ.get("CARS_ONLY", "").split(",") if s]

GLASS = "26313D"
TYRE = "34383E"
RIM = "A9ADB1"
TRIM = "4A4E55"
CREAM = "EDE3C4"
TAIL = "B0473C"
AMBER = "D69A3C"
WELL = "2C3035"


def flat(o):
    o["grad"] = False

    return o


def prism(k, prof, hw, col, bev=0.04, seg=3, grad=True):
    bm = bmesh.new()
    left = [bm.verts.new(G(-hw(y), y, z)) for z, y in prof]
    right = [bm.verts.new(G(hw(y), y, z)) for z, y in prof]
    n = len(prof)
    bm.faces.new(list(reversed(left)))
    bm.faces.new(right)

    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([left[i], left[j], right[j], right[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("p")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("p", me)
    bpy.context.collection.objects.link(o)

    if bev > 0:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bev
        b.segments = seg
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(25)

    k.tag(o, col, grad)

    return o


def cut_arches(o, axles, r, width):
    for z in axles:
        bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=r, depth=width, location=G(0, r * 0.92, z))
        c = bpy.context.active_object
        c.rotation_euler = G(1, 0, 0).to_track_quat("Z", "Y").to_euler()
        m = o.modifiers.new("arch", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        m.object = c
        c.hide_viewport = True
        c.hide_render = True
        o["cutters"] = list(o.get("cutters", [])) + [c.name]

    bev = o.modifiers.get("b")

    if bev:
        w = bev.width
        o.modifiers.remove(bev)
        b = o.modifiers.new("b", "BEVEL")
        b.width = w
        b.segments = 4
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(30)
        b.harden_normals = False


def wells(k, axles, r, w):
    for z in axles:
        k.cyl((0, r * 1.02, z), (1, 0, 0), r - 0.01, w * 0.72, WELL, seg=24)


def car_wheel(path, r, width=0.24, rim=RIM, spokes=5, deep=False):
    k = Kit()
    t = r * 0.3
    k.torus((0, 0, 0), (1, 0, 0), r - t, t, TYRE, seg=36, mseg=10, sx=width / (2 * t))
    rr = r - t * 1.6
    k.cyl((0, 0, 0), (1, 0, 0), rr, width * 0.8, rim, seg=36, bevel=0.01)
    k.cyl((-width * 0.41, 0, 0), (1, 0, 0), rr * 0.86, 0.01, "4E5359", seg=36)
    k.cyl((-width * 0.43, 0, 0), (1, 0, 0), rr * 0.22, 0.03, rim, seg=16, bevel=0.006)

    for i in range(spokes):
        a = i / spokes * math.tau + 0.3
        p = (-width * 0.44, math.sin(a) * rr * 0.5, math.cos(a) * rr * 0.5)
        k.box(p, (0.04, rr * 0.86, rr * 0.24), rim, rot=(-a, 0, 0), bev=0.25, seg=2)

    k.finish(path, ymin=-r, height=2 * r)


def lights(k, zf, zr, y, x, front=CREAM, rear=TAIL, size=(0.32, 0.1, 0.06)):
    for s in (-1, 1):
        flat(k.box((s * x, y, zf), size, front, bev=0.3, seg=2))
        flat(k.box((s * x, y, zr), size, rear, bev=0.3, seg=2))


def bumpers(k, zf, zr, y, w, col=TRIM, h=0.16, d=0.18):
    k.box((0, y, zf), (w, h, d), col, bev=0.35, seg=3)
    k.box((0, y, zr), (w, h, d), col, bev=0.35, seg=3)


def mirrors(k, z, y, x, col):
    for s in (-1, 1):
        k.box((s * x, y, z), (0.14, 0.1, 0.07), col, bev=0.3, seg=2)


def greenhouse(k, base, zf_base, zf_top, zr_top, zr_base, roof, hw_base, hw_top, body, pillars=True, roof_lip=0.03, glass=GLASS, bpos=None):
    prof = [(zr_base, base), (zf_base, base), (zf_top, roof), (zr_top, roof)]

    def hw(y):
        t = (y - base) / max(roof - base, 1e-3)
        return hw_base + (hw_top - hw_base) * t

    prism(k, prof, hw, glass, bev=0.03, seg=2, grad=False)
    k.box((0, roof + roof_lip * 0.5, (zf_top + zr_top) / 2), (hw_top * 2 + 0.05, roof_lip + 0.03, zf_top - zr_top + 0.08), body, bev=0.4, seg=3)

    if pillars:
        for s in (-1, 1):
            k.line((s * (hw_base + 0.005), base, zf_base), (s * (hw_top + 0.01), roof, zf_top), 0.045, body, seg=8)
            k.line((s * (hw_base + 0.005), base, zr_base), (s * (hw_top + 0.01), roof, zr_top), 0.06, body, seg=8)
            zb = bpos if bpos is not None else (zf_top + zr_top) / 2 - 0.05
            k.line((s * (hw_base + 0.012), base, zb), (s * (hw_top + 0.012), roof, zb), 0.04, body, seg=8)
        k.box((0, base + 0.01, (zf_base + zr_base) / 2), (hw_base * 2 + 0.03, 0.04, zf_base - zr_base), body, bev=0.4, seg=2)


def sedan_like(name, L, W, H, r, fz, rz, body, accent=None, kind="sedan", lower=None):
    k = Kit()
    hw = W / 2 - 0.02
    zf = L / 2
    zr = -L / 2
    belt = H * 0.62
    sill = r * 0.55

    if kind == "hatch":
        prof = [(zr, sill + 0.05), (zr + 0.05, belt + 0.02), (zf - 0.25, belt - 0.06), (zf, belt - 0.2), (zf + 0.02, sill + 0.15), (zf - 0.15, sill)]
    elif kind == "wedge":
        prof = [(zr, sill + 0.1), (zr + 0.04, belt + 0.06), (zf - 0.6, belt - 0.06), (zf, sill + 0.2), (zf - 0.15, sill)]
    elif kind == "muscle":
        prof = [(zr, sill + 0.06), (zr + 0.05, belt + 0.03), (zf - 0.15, belt), (zf, belt - 0.12), (zf + 0.02, sill + 0.12), (zf - 0.15, sill)]
    else:
        prof = [(zr, sill + 0.06), (zr + 0.05, belt + 0.04), (zf - 0.3, belt - 0.02), (zf, belt - 0.16), (zf + 0.02, sill + 0.12), (zf - 0.15, sill)]

    o = prism(k, prof, lambda y: hw, lower or body, bev=0.11)
    cut_arches(o, (fz, rz), r + 0.05, W + 0.4)
    wells(k, (fz, rz), r, W)

    if lower and lower != body:
        prism(k, [(zr + 0.02, belt - 0.22), (zf - 0.05, belt - 0.22), (zf - 0.3, belt), (zr + 0.05, belt + 0.02)], lambda y: hw + 0.01, body, bev=0.03)

    if kind == "hatch":
        greenhouse(k, belt, zf - 0.9, zf - 1.75, zr + 0.2, zr + 0.1, H, hw - 0.03, hw - 0.18, body)
    elif kind == "wedge":
        greenhouse(k, belt, zf - 0.95, zf - 1.7, zr + 1.3, zr + 0.75, H, hw - 0.12, hw - 0.3, body, bpos=zr + 1.6)
    elif kind == "muscle":
        greenhouse(k, belt, zf - 1.55, zf - 2.2, zr + 0.95, zr + 0.45, H, hw - 0.06, hw - 0.22, body)
    else:
        greenhouse(k, belt, zf - 1.25, zf - 1.95, zr + 1.05, zr + 0.6, H, hw - 0.05, hw - 0.2, body)

    lights(k, zf - 0.02, zr + 0.02, belt - 0.12, hw - 0.28)
    bumpers(k, zf + 0.02, zr - 0.02, sill + 0.08, W - 0.08)
    mirrors(k, zf - 1.3 if kind != "wedge" else zf - 1.0, belt + 0.08, hw + 0.06, body)
    k.box((0, belt - 0.22, zf + 0.01), (W * 0.42, 0.12, 0.05), TRIM, bev=0.3, seg=2)

    if kind == "wedge":
        k.box((0, belt + 0.18, zr + 0.12), (W - 0.2, 0.04, 0.3), TRIM, bev=0.3, seg=2)

        for s in (-1, 1):
            k.box((s * 0.6, belt + 0.06, zr + 0.18), (0.05, 0.14, 0.12), TRIM, bev=0.3, seg=2)
            k.box((s * (hw + 0.005), belt - 0.2, zr + 1.35), (0.04, 0.22, 0.6), TRIM, bev=0.3, seg=2)

    if accent:
        accent(k, L, W, H, belt, hw, zf, zr)

    return k


def boxy(name, L, W, H, r, fz, rz, body, cab_len, rear_kind, extra=None, roof=None):
    k = Kit()
    hw = W / 2 - 0.02
    zf = L / 2
    zr = -L / 2
    belt = 1.0 if H > 1.5 else H * 0.62
    sill = r * 0.6
    cab_back = zf - cab_len
    prof = [(cab_back, sill), (cab_back, belt + 0.02), (zf - 0.25, belt), (zf, belt - 0.16), (zf + 0.02, sill + 0.1), (zf - 0.15, sill - 0.02)]
    o = prism(k, prof, lambda y: hw, body, bev=0.1)
    cut_arches(o, (fz,), r + 0.05, W + 0.4)
    greenhouse(k, belt, zf - 0.78, zf - 1.25, cab_back + 0.12, cab_back + 0.05, roof or (belt + 0.62), hw - 0.04, hw - 0.12, body)
    k.box((0, sill + 0.06, (cab_back + zr) / 2), (W - 0.3, 0.16, cab_back - zr), TRIM, bev=0.3, seg=2)
    wells(k, (fz, rz), r, W)

    if rear_kind == "bed":
        bed_top = belt + 0.02
        k.box((0, sill + 0.17, (cab_back + zr) / 2 - 0.02), (W - 0.06, 0.08, cab_back - zr - 0.06), body, bev=0.3, seg=2)

        for s in (-1, 1):
            side = k.box((s * (hw - 0.04), (sill + bed_top) / 2 + 0.05, (cab_back + zr) / 2 - 0.02), (0.08, bed_top - sill - 0.1, cab_back - zr - 0.06), body, bev=0.3, seg=2)

        k.box((0, (sill + bed_top) / 2 + 0.05, zr + 0.04), (W - 0.06, bed_top - sill - 0.1, 0.08), body, bev=0.3, seg=2)
        flare = prism(k, [(cab_back - 0.04, sill - 0.02), (cab_back - 0.04, sill + 0.35), (zr + 0.06, sill + 0.35), (zr + 0.06, sill - 0.02)], lambda y: hw + 0.02, body, bev=0.04)
        cut_arches(flare, (rz,), r + 0.05, W + 0.4)
    elif rear_kind == "utility":
        top = belt + 0.42
        o2 = prism(k, [(cab_back - 0.06, sill - 0.04), (cab_back - 0.06, top), (zr + 0.02, top), (zr, sill - 0.04)], lambda y: hw + 0.04, body, bev=0.05)
        cut_arches(o2, (rz,), r + 0.05, W + 0.6)

        for s in (-1, 1):
            for i in range(3):
                zc = cab_back - 0.42 - i * ((cab_back - zr - 0.5) / 3)

                if abs(zc - rz) < r + 0.25:
                    continue

                k.box((s * (hw + 0.045), (sill + top) / 2 + 0.05, zc), (0.02, top - sill - 0.2, (cab_back - zr) / 3 - 0.12), "BDB8AE", bev=0.2, seg=1)
                k.box((s * (hw + 0.06), (sill + top) / 2 + 0.05, zc + 0.12), (0.03, 0.05, 0.12), TRIM, bev=0.3, seg=1)

        k.box((0, top + 0.03, (cab_back + zr) / 2), (W - 0.1, 0.05, cab_back - zr - 0.1), "9EA2A6", bev=0.3, seg=1)

        for i in range(4):
            z = cab_back - 0.3 - i * 0.75
            k.line((-hw + 0.1, top + 0.05, z), (hw - 0.1, top + 0.05, z), 0.025, "8A8E92", seg=6)
            for s in (-1, 1):
                k.line((s * (hw - 0.1), top + 0.05, z), (s * (hw - 0.1), top + 0.32, z), 0.025, "8A8E92", seg=6)

        for s in (-1, 1):
            k.line((s * (hw - 0.1), top + 0.32, cab_back - 0.3), (s * (hw - 0.1), top + 0.32, cab_back - 0.3 - 2.25), 0.025, "8A8E92", seg=6)
    elif rear_kind == "box":
        top = H + 0.85
        o2 = prism(k, [(cab_back - 0.08, sill + 0.1), (cab_back - 0.08, top), (zr, top), (zr, sill + 0.1)], lambda y: hw + 0.06, body if roof is None else "C9C4B8", bev=0.05)
        k.box((0, sill + 0.12, zr - 0.05), (W - 0.2, 0.12, 0.12), TRIM, bev=0.3, seg=1)
        k.box((0, (sill + top) / 2, zr - 0.012), (0.04, top - sill - 0.3, 0.02), TRIM, bev=0.3, seg=1)

    lights(k, zf - 0.02, zr + 0.03, belt - 0.14, hw - 0.25)
    bumpers(k, zf + 0.03, zr - 0.04, sill + 0.06, W - 0.04)
    mirrors(k, zf - 0.85, belt + 0.12, hw + 0.1, body)
    k.box((0, belt - 0.24, zf + 0.012), (W * 0.55, 0.22, 0.05), TRIM, bev=0.3, seg=2)

    if extra:
        extra(k, L, W, H, belt, hw, zf, zr)

    return k


def police_bits(k, L, W, H, belt, hw, zf, zr):
    for s in (-1, 1):
        k.box((s * (hw + 0.012), belt - 0.22, 0.0), (0.02, 0.3, 1.9), "2E3D5C", bev=0.3, seg=2)
    k.box((0, H + 0.07, -0.2), (1.0, 0.08, 0.24), TRIM, bev=0.4, seg=2)
    flat(k.box((-0.27, H + 0.13, -0.2), (0.42, 0.07, 0.2), "4A6BB0", bev=0.4, seg=2))
    flat(k.box((0.27, H + 0.13, -0.2), (0.42, 0.07, 0.2), "B0544A", bev=0.4, seg=2))
    k.box((0, belt - 0.3, zf + 0.1), (W - 0.2, 0.3, 0.06), "3A3E45", bev=0.3, seg=2)


def taxi_bits(k, L, W, H, belt, hw, zf, zr):
    k.box((0, H + 0.1, -0.3), (0.62, 0.17, 0.26), "E8DDB8", bev=0.4, seg=2)

    for s in (-1, 1):
        for i in range(6):
            k.box((s * (hw + 0.012), belt - 0.15, -0.9 + i * 0.36), (0.02, 0.07, 0.16), "3A3E45" if i % 2 == 0 else "E8DDB8", bev=0.2, seg=1)


def build(name, k, parts_dir, r, wheel_style):
    os.makedirs(os.path.join(OUT, parts_dir), exist_ok=True)
    k.finish(os.path.join(OUT, parts_dir, "body.glb"), ymin=0.0, height=1.8)
    car_wheel(os.path.join(OUT, parts_dir, "wheel.glb"), r, **wheel_style)


CARS = {
    "utility": lambda: boxy("utility", 5.37, 2.0, 1.6, 0.356, 1.785, -1.376, "CFCBC2", 1.95, "utility"),
    "pickup": lambda: boxy("pickup", 5.22, 2.1, 1.6, 0.351, 1.743, -1.271, "7E4B40", 2.45, "bed"),
    "sedan": lambda: sedan_like("sedan", 4.54, 1.8, 1.42, 0.298, 1.346, -1.25, "5C7F9C"),
    "hatch": lambda: sedan_like("hatch", 3.84, 1.83, 1.45, 0.298, 1.102, -1.303, "7C8F5A", kind="hatch"),
    "police": lambda: sedan_like("police", 4.36, 1.88, 1.6, 0.348, 1.326, -1.349, "D9D6CE", accent=police_bits),
    "taxi": lambda: sedan_like("taxi", 5.27, 2.09, 1.6, 0.322, 1.523, -1.333, "C8A45C", accent=taxi_bits),
    "van": lambda: boxy("van", 5.18, 2.1, 1.6, 0.35, 1.804, -1.331, "B9B3A6", 1.6, "box", roof=None),
    "boxtruck": lambda: boxy("boxtruck", 4.6, 2.0, 1.6, 0.273, 1.367, -1.188, "4F6A7E", 1.7, "box", roof=1),
    "jdm": lambda: sedan_like("jdm", 4.68, 1.97, 1.35, 0.325, 1.356, -1.363, "3D5A86", kind="muscle"),
    "phoenix": lambda: sedan_like("phoenix", 4.89, 2.09, 1.33, 0.322, 1.544, -1.197, "A2462F", kind="muscle"),
    "aventador": lambda: sedan_like("aventador", 4.96, 2.1, 1.14, 0.32, 1.321, -1.491, "9DA3A8", kind="wedge"),
}

WHEELS = {
    "utility": dict(width=0.26, rim="9EA2A6", spokes=6),
    "pickup": dict(width=0.28, rim="A9ADB1", spokes=6),
    "sedan": dict(width=0.22, rim="A9ADB1", spokes=5),
    "hatch": dict(width=0.21, rim="A9ADB1", spokes=4),
    "police": dict(width=0.24, rim="5A5F66", spokes=6),
    "taxi": dict(width=0.23, rim="A9ADB1", spokes=5),
    "van": dict(width=0.25, rim="9EA2A6", spokes=6),
    "boxtruck": dict(width=0.25, rim="9EA2A6", spokes=8),
    "jdm": dict(width=0.25, rim="5A5F66", spokes=5),
    "phoenix": dict(width=0.27, rim="A9ADB1", spokes=5),
    "aventador": dict(width=0.29, rim="5A5F66", spokes=5),
}

RADII = {"utility": 0.356, "pickup": 0.351, "sedan": 0.298, "hatch": 0.298, "police": 0.348, "taxi": 0.322, "van": 0.35, "boxtruck": 0.273, "jdm": 0.325, "phoenix": 0.322, "aventador": 0.32}

for name, make in CARS.items():
    if ONLY and name not in ONLY:
        continue

    k = make()
    build(name, k, name, RADII[name], WHEELS[name])

    if os.environ.get("CARS_RENDER"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        L = {"utility": 5.37, "pickup": 5.22}.get(name, 4.6)
        fz = {"utility": 1.785, "pickup": 1.743, "sedan": 1.346, "hatch": 1.102, "police": 1.326, "taxi": 1.523, "van": 1.804, "boxtruck": 1.367, "jdm": 1.356, "phoenix": 1.544, "aventador": 1.321}[name]
        rz = {"utility": -1.376, "pickup": -1.271, "sedan": -1.25, "hatch": -1.303, "police": -1.349, "taxi": -1.333, "van": -1.331, "boxtruck": -1.188, "jdm": -1.363, "phoenix": -1.197, "aventador": -1.491}[name]
        xw = {"utility": 0.79, "pickup": 0.7}.get(name, 0.75)
        r = RADII[name]
        wf = os.path.join(OUT, name, "wheel.glb")
        render([(os.path.join(OUT, name, "body.glb"), (0, 0, 0)), (wf, (-xw, r, fz)), (wf, (-xw, r, rz))], os.path.join(OUT, name, "prev.png"), cam=(-5.2, 2.2, 4.4), look=(0, 0.6, 0))
