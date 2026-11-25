import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bmesh
import math
from mathutils import Vector
import sedan2 as S
from veh import G, hexc

OUT = os.environ.get("CARS_OUT", "/tmp/cars_out")
OLD = os.environ.get("OLD_DIR", "")

S.PAL.update({
    "body": "C2622E",
    "stripe": "2E3238",
    "aero": "3B4047",
    "glass": "1F2730",
    "cream": "F2E9CF",
    "tail": "C8463A",
    "rim": "8C9298",
    "dish": "6A7178",
    "tyre": "30343A",
    "dark": "24282D",
})
for k in ("stripe", "aero"):
    if k not in S.MATS:
        S.MATS.append(k)

L = 4.96
W = 2.1
r = 0.32
fz = 1.321
rz = -1.491
hw = W / 2


def ring(sill, belt, roof, bw, tw, top_w=None, flare=0.0):
    return [
        (0, sill),
        (bw - 0.16, sill),
        (bw - 0.03 + flare, sill + 0.12),
        (bw + flare, (sill + belt) * 0.5 + 0.06),
        (bw - 0.02, belt),
        (tw, roof - 0.02),
        (0.16, roof),
        (0, roof + 0.005),
    ]


def car():
    zf = L / 2
    zr = -L / 2
    sill = 0.12
    low = {}
    cab = {4: "glass"}
    ws = {4: "glass", 5: "glass", 6: "glass"}
    top = {6: "stripe"}
    st = [
        (zr, [(0, 0.3), (hw - 0.3, 0.3), (hw - 0.22, 0.38), (hw - 0.14, 0.52), (hw - 0.16, 0.74), (hw - 0.4, 0.8), (0.16, 0.81), (0, 0.81)], top),
        (zr + 0.25, ring(sill + 0.06, 0.8, 0.86, hw - 0.02, hw - 0.3), top),
        (zr + 0.9, ring(sill, 0.84, 0.92, hw, hw - 0.28, flare=0.03), top),
        (zr + 1.55, ring(sill, 0.86, 1.02, hw, hw - 0.34, flare=0.02), top),
        (zr + 2.05, ring(sill, 0.78, 1.1, hw - 0.05, hw - 0.42), cab),
        (zr + 2.6, ring(sill, 0.72, 1.14, hw - 0.07, hw - 0.4), ws),
        (zr + 3.25, ring(sill, 0.66, 0.8, hw - 0.04, hw - 0.3, flare=0.02), top),
        (zr + 3.9, ring(sill, 0.6, 0.68, hw - 0.02, hw - 0.26, flare=0.03), top),
        (zf - 0.25, ring(sill + 0.02, 0.5, 0.58, hw - 0.1, hw - 0.34), top),
        (zf, [(0, sill + 0.06), (hw - 0.4, sill + 0.06), (hw - 0.3, sill + 0.12), (hw - 0.26, 0.26), (hw - 0.3, 0.4), (hw - 0.5, 0.46), (0.16, 0.47), (0, 0.47)], low),
    ]
    body = S.loft(st, crease=())
    b = body.modifiers.new("bv", "BEVEL")
    b.width = 0.025
    b.segments = 2
    b.limit_method = "ANGLE"
    b.angle_limit = math.radians(20)
    S.apply_mods(body)

    for z in (fz, rz):
        c = S.cyl((0, r, z), (1, 0, 0), r + 0.05, W + 0.6, "body", seg=10)
        c.rotation_euler.rotate_axis("Z", math.radians(18))
        S.boolean(body, c)

    parts = [body]

    for z in (fz, rz):
        parts.append(S.cyl((0, r * 1.02, z), (1, 0, 0), r + 0.02, W - 0.3, "dark", seg=24))

    for s in (-1, 1):
        bm = bmesh.new()
        pts = [(s * (hw + 0.035), 0.28, rz + 0.55), (s * (hw + 0.035), 0.74, rz + 0.62), (s * (hw + 0.02), 0.7, rz + 1.35), (s * (hw + 0.025), 0.3, rz + 1.1)]
        v = [bm.verts.new(G(*p)) for p in pts]
        bm.faces.new(v if s > 0 else list(reversed(v)))
        o = S.new_obj("intake", bm)
        sol = o.modifiers.new("so", "SOLIDIFY")
        sol.thickness = 0.06
        S.set_mat(o, "dark")
        parts.append(o)
        parts.append(S.box((s * (hw + 0.045), 0.52, rz + 0.9), (0.02, 0.32, 0.03), "aero", rot=(0.4, 0, 0), bev=0.3))
        parts.append(S.box((s * (hw + 0.045), 0.44, rz + 0.95), (0.02, 0.3, 0.03), "aero", rot=(0.4, 0, 0), bev=0.3))
        parts.append(S.box((s * (hw - 0.05), sill - 0.02, (fz + rz) / 2), (0.16, 0.06, fz - rz - 2 * r - 0.3), "aero", bev=0.25))
        parts.append(S.box((s * (hw - 0.015), 0.5, rz + 2.62), (0.02, 0.5, 0.012), "dark", rot=(-0.35, 0, 0), bev=0.0))
        parts.append(S.box((s * (hw + 0.012), 0.47, rz + 1.42), (0.02, 0.36, 0.012), "dark", rot=(0.25, 0, 0), bev=0.0))
        parts.append(S.box((s * (hw + 0.004), 0.55, rz + 1.9), (0.02, 0.04, 0.9), "stripe", bev=0.2))
        parts.append(S.box((s * (hw + 0.07), 0.86, zf - 1.95), (0.14, 0.06, 0.09), "body", rot=(0, s * 0.3, 0), bev=0.3))
        parts.append(S.box((s * (hw + 0.02), 0.84, zf - 1.9), (0.08, 0.025, 0.03), "aero", bev=0.3))

        hx = s * (hw - 0.34)
        hz = zf - 0.42
        hy = 0.56
        tilt = 0.32
        parts.append(S.box((hx, hy, hz), (0.4, 0.03, 0.3), "dark", rot=(tilt, s * 0.3, 0), bev=0.2))

        for ang, ln in ((0.0, 0.26), (1.0, 0.16), (-1.0, 0.16)):
            parts.append(S.box((hx + s * math.sin(ang) * 0.06, hy + 0.025, hz + math.cos(ang) * 0.06 - 0.03), (0.04, 0.02, ln), "cream", rot=(tilt, s * 0.3 + ang * s, 0), bev=0.2))

        tz = zr + 0.0
        ty = 0.66
        tx = s * (hw - 0.36)
        parts.append(S.box((tx, ty, tz + 0.02), (0.5, 0.2, 0.04), "dark", bev=0.2))

        for ang, ln in ((0.0, 0.34), (0.9, 0.16), (-0.9, 0.16)):
            parts.append(S.box((tx - s * (0.0 if ang == 0 else 0.1), ty + (0 if ang == 0 else 0.04 * (1 if ang > 0 else -1)), tz - 0.005), (ln, 0.032, 0.03), "tail", rot=(0, 0, ang), bev=0.2))

        parts.append(S.box((s * 0.42, 0.9, zr + 0.3), (0.05, 0.14, 0.12), "aero", rot=(-0.3, 0, 0), bev=0.3))

    parts.append(S.box((0, 0.99, zr + 0.24), (W - 0.36, 0.035, 0.34), "aero", rot=(0.12, 0, 0), bev=0.3))

    for s in (-1, 1):
        parts.append(S.box((s * (W / 2 - 0.19), 0.95, zr + 0.24), (0.02, 0.12, 0.36), "aero", bev=0.3))

    parts.append(S.box((0, sill + 0.02, zf - 0.05), (W - 0.2, 0.04, 0.32), "aero", bev=0.3))
    parts.append(S.box((0, sill + 0.14, zf + 0.0), (W - 0.9, 0.08, 0.06), "dark", bev=0.3))

    for s in (-1, 1):
        parts.append(S.box((s * (hw - 0.42), sill + 0.16, zf - 0.12), (0.34, 0.12, 0.06), "dark", rot=(0, s * 0.25, 0), bev=0.3))

    parts.append(S.box((0, 0.24, zr + 0.06), (W - 0.5, 0.16, 0.2), "aero", bev=0.25))

    for i in range(6):
        x = -0.6 + i * 0.24
        parts.append(S.box((x, 0.21, zr + 0.02), (0.02, 0.14, 0.22), "aero", bev=0.3))

    for s in (-1, 1):
        parts.append(S.cyl((s * 0.12, 0.34, zr + 0.0), (0, 0, 1), 0.05, 0.1, "dish", seg=6))

    for i in range(5):
        parts.append(S.box((0, 0.94, zr + 0.95 + i * 0.12), (0.7, 0.015, 0.04), "aero", rot=(0.2, 0, 0), bev=0.3))

    return parts


def wheel():
    parts = []
    t = r * 0.16
    width = 0.3
    bpy.ops.mesh.primitive_torus_add(major_radius=r - t, minor_radius=t, major_segments=48, minor_segments=12, location=(0, 0, 0))
    o = bpy.context.active_object
    o.rotation_euler = G(1, 0, 0).to_track_quat("Z", "Y").to_euler()
    o.scale = (1, 1, width / (2 * t))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    parts.append(S.set_mat(o, "tyre"))
    rr = r - t * 1.6
    parts.append(S.cyl((0, 0, 0), (1, 0, 0), rr + 0.005, width * 0.88, "dish", seg=48, bevel=0.01))
    parts.append(S.cyl((-width * 0.4, 0, 0), (1, 0, 0), rr, 0.025, "rim", seg=48, bevel=0.008))
    face = -width * 0.45

    for i in range(10):
        a = i / 10 * math.tau
        p0 = (face, math.sin(a) * rr * 0.22, math.cos(a) * rr * 0.22)
        p1 = (face + 0.03, math.sin(a + 0.08) * rr * 0.96, math.cos(a + 0.08) * rr * 0.96)
        parts.append(S.box(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2), (0.03, 0.035, rr * 0.76), "rim", rot=(-(a + 0.04), 0, 0), bev=0.3, seg=2))

    parts.append(S.cyl((face - 0.005, 0, 0), (1, 0, 0), rr * 0.26, 0.05, "rim", seg=24, bevel=0.012))
    parts.append(S.cyl((face - 0.03, 0, 0), (1, 0, 0), rr * 0.1, 0.02, "body", seg=12))
    parts.append(S.cyl((-width * 0.15, rr * 0.35, rr * 0.45), (1, 0, 0), 0.07, 0.04, "body", seg=10))

    return parts


bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(OUT, exist_ok=True)
body = os.path.join(OUT, "body.glb")
wf = os.path.join(OUT, "wheel.glb")
S.export(car(), body, 0.0, 1.15)
bpy.ops.wm.read_factory_settings(use_empty=True)
S.export(wheel(), wf, -0.32, 0.64)

xw = 0.865


def setup(bodyf, wheelf, xf, xr, zfa, zra, ra):
    return [(bodyf, (0, 0, 0)), (wheelf, (-xf, ra, zfa)), (wheelf, (-xr, ra, zra))]


views = {"front": ((-5.2, 1.8, 5.6), (0, 0.45, 0.2)), "rear": ((-5.2, 1.8, -5.6), (0, 0.45, -0.2)), "side": ((-8.5, 0.9, 0.0), (0, 0.45, 0.0))}

for v, (cam, look) in views.items():
    S.shot(setup(body, wf, xw, 0.894, fz, rz, r), os.path.join(OUT, "new_" + v + ".png"), cam, look)

    if OLD:
        S.shot(setup(os.path.join(OLD, "body.glb"), os.path.join(OLD, "wheel.glb"), 0.865, 0.894, 1.321, -1.491, 0.322), os.path.join(OUT, "old_" + v + ".png"), cam, look, texture=True)
