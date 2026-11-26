import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k
from mathutils import Vector

OUT = os.environ.get("OUT", "/tmp/dfkit")

W, D, H = 0.34, 0.165, 0.47
paint = k.c("sand_paint")
dark = k.c("sand_dark")

k.reset()
parts = []

body = k.box("body", (W, D, H), (0, 0, 0), paint)
k.chamfer(body, 0.022, segments=2)
parts.append(body)

seam = k.box("seam", (W + 0.008, 0.01, H - 0.03), (0, 0, 0.015), dark)
k.chamfer(seam, 0.004)
parts.append(seam)

for side in (-1, 1):
    y = side * (D / 2)
    x0, x1, z0, z1 = -W / 2 + 0.035, W / 2 - 0.035, 0.04, H - 0.06
    cx, cz = 0.0, (z0 + z1) / 2
    hw, hh = 0.045, 0.045
    panels = [
        [(x0 + 0.03, z1), (x1 - 0.03, z1), (cx + hw * 0.6, cz + hh + 0.02), (cx - hw * 0.6, cz + hh + 0.02)],
        [(x0 + 0.03, z0), (cx - hw * 0.6, cz - hh - 0.02), (cx + hw * 0.6, cz - hh - 0.02), (x1 - 0.03, z0)],
        [(x0, z0 + 0.03), (x0, z1 - 0.03), (cx - hw - 0.02, cz + hh * 0.6), (cx - hw - 0.02, cz - hh * 0.6)],
        [(x1, z0 + 0.03), (cx + hw + 0.02, cz - hh * 0.6), (cx + hw + 0.02, cz + hh * 0.6), (x1, z1 - 0.03)],
        [(cx - hw, cz - hh), (cx + hw, cz - hh), (cx + hw, cz + hh), (cx - hw, cz + hh)],
    ]

    for i, outline in enumerate(panels):
        pl = k.sweep(f"panel{side}{i}", outline, 0.012, (0, y + side * 0.006, 0), paint, axis="y")
        k.chamfer(pl, 0.004, angle=20)
        parts.append(pl)

for hx in (-0.075, 0.0, 0.075):
    for hy in (-1, 1):
        parts.append(k._bar(f"post{hx}{hy}", Vector((hx, hy * 0.045, H - 0.005)), Vector((hx, hy * 0.045, H + 0.045)), 0.008, paint, sides=6))

    parts.append(k._bar(f"grip{hx}", Vector((hx, -0.05, H + 0.045)), Vector((hx, 0.05, H + 0.045)), 0.011, paint, sides=8))

spout_base = Vector((-W / 2 + 0.06, 0, H - 0.01))
spout_tip = spout_base + Vector((-0.012, 0, 0.032))
parts.append(k._bar("spout", spout_base, spout_tip, 0.024, dark, sides=10))
parts.append(k._bar("cap", spout_tip, spout_tip + Vector((-0.005, 0, 0.022)), 0.03, dark, sides=10))
parts.append(k.box("lever", (0.075, 0.03, 0.014), (-W / 2 + 0.1, 0, H + 0.052), dark))
parts.append(k.box("clip", (0.014, 0.03, 0.05), (-W / 2 + 0.135, 0, H + 0.005), dark))

ob = k.finish("df_jerrycan", parts, budget=900)
print("STATS", k.stats(ob))
k.export(ob, os.path.join(OUT, "df_jerrycan.glb"))
print("SHEET", k.preview([ob], os.path.join(OUT, "df_jerrycan_sheet.png")))
k.VIEWS["photo"] = (0.55, -1, 0.35)
print("PHOTO", k.preview([ob], os.path.join(OUT, "df_jerrycan_photo.png"), views=("photo",), res=600))
