import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k

OUT = os.environ.get("OUT", "/tmp/dfkit")

W, D, H = 18.5, 11.5, 6.6
RISE = 3.1
k.reset()
parts = []

parts.append(k.beveled_box("plinth", (W + 0.3, D + 0.3, 0.6), (0, 0, 0), k.c("stone"), 0.03))
parts.append(k.beveled_box("walls", (W, D, H - 0.6), (0, 0, 0.6), k.c("concrete"), 0.03))
parts.append(k.beveled_box("band", (W + 0.16, D + 0.16, 0.22), (0, 0, 3.45), k.c("trim"), 0.02))
parts.append(k.beveled_box("cornice", (W + 0.5, D + 0.5, 0.3), (0, 0, H - 0.3), k.c("trim"), 0.03))
parts.append(k.beveled_box("frieze", (W + 0.3, D + 0.3, 0.3), (0, 0, H - 0.6), k.c("plaster_dark"), 0.02))
parts += k.hip_roof("roof", W, D, RISE, (0, 0, H), overhang=1.0, color="roof_metal")

for cx in (-4.1, 4.1):
    ridge_end = (W - D) / 2
    surface = H + RISE * (1 - (abs(cx) - ridge_end) / (D / 2))
    parts.append(k.beveled_box(f"chimbase{cx}", (1.2, 0.9, 0.55), (cx, 0, surface - 0.3), k.c("trim"), 0.02))
    parts.append(k.beveled_box(f"chimney{cx}", (0.75, 0.6, H + RISE + 0.75 - surface), (cx, 0, surface), k.c("trim"), 0.02))
    parts.append(k.beveled_box(f"chimcap{cx}", (0.95, 0.8, 0.16), (cx, 0, H + RISE + 0.75), k.c("concrete_dark"), 0.02))

groups = [(-7.0, 2), (-0.2, 3), (6.0, 3)]
xs = []

for gx, n in groups:
    for i in range(n):
        xs.append(gx + (i - (n - 1) / 2) * 1.75)

y = -D / 2

for x in xs:
    for zf, wz in ((1.0, 1.55), (4.15, 1.55)):
        parts += k.window(f"w{x}{zf}", 1.0, wz, (x, y + 0.02, zf), 0, mullions=(2, 3), colors={"frame": "white"})
        for name, size, at in (("l", (0.22, 0.07, wz + 0.9), (x - 0.64, y - 0.03, zf - 0.35)), ("r", (0.22, 0.07, wz + 0.9), (x + 0.64, y - 0.03, zf - 0.35)), ("b", (1.5, 0.07, 0.3), (x, y - 0.03, zf - 0.35)), ("t", (1.5, 0.07, 0.3), (x, y - 0.03, zf + wz + 0.25))):
            parts.append(k.box(f"surround{name}{x}{zf}", size, at, k.c("concrete_dark")))
        ped = k.sweep(f"ped{x}{zf}", [(-0.75, 0), (0.75, 0), (0, 0.32)], 0.12, (x, y - 0.08, zf + wz + 0.18), k.c("trim"))
        parts.append(ped)

        for sx in (-1, 1):
            parts.append(k.beveled_box(f"sidepl{x}{zf}{sx}", (0.14, 0.1, wz + 0.3), (x + sx * 0.66, y - 0.05, zf - 0.15), k.c("trim"), 0.01))

        if zf < 2:
            continue

        for dx in (-0.55, 0.0, 0.55):
            panel = k.box(f"dia{x}{dx}", (0.34, 0.08, 0.34), (x + dx, y - 0.03, 2.85), k.c("concrete_dark"))
            k.rotate(panel, 45, "Y", (x + dx, y - 0.03, 3.02))
            parts.append(panel)

for bx in (-W / 2 + 0.25, -4.85, 2.85, W / 2 - 0.25):
    parts.append(k.beveled_box(f"pil{bx}", (0.5, 0.2, H - 1.2), (bx, y - 0.08, 0.6), k.c("trim"), 0.02))

    for n in range(5):
        parts.append(k.box(f"quoin{bx}{n}", (0.36, 0.06, 0.4), (bx, y - 0.2, 1.0 + n * 1.0), k.c("plaster_dark")))

ob = k.finish("df_rowhouse", parts, budget=8000)
print("STATS", k.stats(ob))
k.export(ob, os.path.join(OUT, "df_rowhouse.glb"))
print("SHEET", k.preview([ob], os.path.join(OUT, "df_rowhouse_sheet.png")))
print("ORTHO", k.preview([ob], os.path.join(OUT, "df_rowhouse_ortho.png"), views=("elevation",), res=960, ortho=True, transparent=True))
