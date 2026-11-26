import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k

OUT = os.environ.get("OUT", "/tmp/dfkit")

k.reset()

W, D = 8.0, 6.0
H1, H2 = 3.2, 3.0
T = 0.3
parts = []

parts.append(k.beveled_box("plinth", (W + 0.5, D + 0.5, 0.45), (0, 0, 0), k.c("concrete"), 0.03))
parts.append(k.beveled_box("plinth_cap", (W + 0.6, D + 0.6, 0.08), (0, 0, 0.45), k.c("concrete_dark"), 0.02))

z0 = 0.53
front_open = [(-2.4, 0.9, 1.3, 1.5), (0, 0, 1.2, 2.3), (2.4, 0.9, 1.3, 1.5)]
upper_open = [(-2.4, 0.8, 1.3, 1.5), (0, 0.8, 1.3, 1.5), (2.4, 0.8, 1.3, 1.5)]
side_open = [(-1.3, 0.9, 1.2, 1.5), (1.3, 0.9, 1.2, 1.5)]
side_upper = [(-1.3, 0.8, 1.2, 1.5), (1.3, 0.8, 1.2, 1.5)]

for name, width, y, facing, low, high in (("front", W, -D / 2 + T / 2, 0, front_open, upper_open), ("back", W, D / 2 - T / 2, 180, [(-2.4, 0.9, 1.3, 1.5), (2.4, 0.9, 1.3, 1.5)], upper_open), ("left", D - T * 2, 0, 90, side_open, side_upper), ("right", D - T * 2, 0, -90, side_open, side_upper)):
    x = 0

    if name == "left":
        x, y = -W / 2 + T / 2, 0
    if name == "right":
        x, y = W / 2 - T / 2, 0

    parts += k.wall(name + "_g", width, H1, T, (x, y, z0), low, "plaster", math.radians(facing))
    parts += k.wall(name + "_u", width, H2, T, (x, y, z0 + H1 + 0.25), high, "plaster_dark" if name in ("left", "right") else "plaster", math.radians(facing))

parts.append(k.beveled_box("floor_band", (W + 0.16, D + 0.16, 0.25), (0, 0, z0 + H1), k.c("trim"), 0.02))
parts.append(k.beveled_box("cornice", (W + 0.3, D + 0.3, 0.18), (0, 0, z0 + H1 + 0.25 + H2), k.c("trim"), 0.025))

for sx in (-1, 1):
    for sy in (-1, 1):
        parts += k.pilaster(f"corner{sx}{sy}", 0.4, H1 + H2 + 0.25, 0.4, (sx * (W / 2), sy * (D / 2), z0), "stone")

for ox, oz, ow, oh in front_open:
    if oh > 2:
        parts += k.door("door", ow, oh, (ox, -D / 2 + 0.02, z0), 0, colors={"leaf": "olive", "panel": "olive_dark"})
    else:
        parts += k.window(f"fw{ox}", ow, oh, (ox, -D / 2 + 0.02, z0 + oz), 0, mullions=(2, 2), shutters=True)

for ox, oz, ow, oh in upper_open:
    parts += k.window(f"fu{ox}", ow, oh, (ox, -D / 2 + 0.02, z0 + H1 + 0.25 + oz), 0, mullions=(2, 2), shutters=True)
    parts += k.window(f"bu{ox}", ow, oh, (ox, D / 2 - 0.02, z0 + H1 + 0.25 + oz), math.pi, mullions=(2, 2))

for ox in (-2.4, 2.4):
    parts += k.window(f"bw{ox}", 1.3, 1.5, (ox, D / 2 - 0.02, z0 + 0.9), math.pi, mullions=(2, 2))

for side, xw, f in ((-1, -W / 2 + 0.02, -math.pi / 2), (1, W / 2 - 0.02, math.pi / 2)):
    for oy in (-1.3, 1.3):
        parts += k.window(f"sw{side}{oy}", 1.2, 1.5, (xw, -oy * side, z0 + 0.9), f, mullions=(2, 2))
        parts += k.window(f"su{side}{oy}", 1.2, 1.5, (xw, -oy * side, z0 + H1 + 0.25 + 0.8), f, mullions=(2, 2))

canopy = k.beveled_box("canopy", (2.0, 1.1, 0.1), (0, -D / 2 - 0.5, z0 + 2.65), k.c("roof_metal"), 0.02)
k.rotate(canopy, -8, "X", (0, -D / 2, z0 + 2.7))
parts.append(canopy)

for sx in (-1, 1):
    parts.append(k._bar(f"brace{sx}", k.Vector((sx * 0.85, -D / 2, z0 + 2.2)), k.Vector((sx * 0.85, -D / 2 - 0.95, z0 + 2.62)), 0.025, k.c("steel_dark")))

parts += k.stairs("steps", 1.8, 3, 0.18, 0.32, (0, -D / 2 - 0.25, 0), 0, "concrete", rails=True)

roof_z = z0 + H1 + 0.25 + H2 + 0.18
parts += k.gable_roof("roof", W, D, 1.9, (0, 0, roof_z), overhang=0.4)

parts.append(k.beveled_box("chimney", (0.6, 0.6, 2.4), (2.4, 1.2, roof_z), k.c("brick"), 0.02))
parts.append(k.beveled_box("chimney_cap", (0.8, 0.8, 0.12), (2.4, 1.2, roof_z + 2.4), k.c("concrete_dark"), 0.02))

for sy in (-1, 1):
    parts.append(k.beveled_box(f"ac{sy}", (0.8, 0.55, 0.6), (-W / 2 - 0.3, sy * 1.6, z0 + H1 + 1.1), k.c("steel"), 0.02))
    parts.append(k.beveled_box(f"acgrill{sy}", (0.04, 0.45, 0.45), (-W / 2 - 0.71, sy * 1.6, z0 + H1 + 1.17), k.c("steel_dark"), 0.005))

parts.append(k.beveled_box("sign", (2.2, 0.08, 0.45), (0, -D / 2 - 0.05, z0 + H1 - 0.2), k.c("olive"), 0.015))
parts.append(k.box("sign_text", (1.6, 0.02, 0.18), (0, -D / 2 - 0.1, z0 + H1 - 0.07), k.c("white")))

for sx in (-1, 1):
    parts.append(k.prism(f"pipe{sx}", 8, 0.06, H1 + H2 + 0.6, (sx * (W / 2 - 0.45), -D / 2 - 0.08, z0), k.c("steel_dark")))

ob = k.finish("df_outpost", parts, budget=12000)
print("STATS", k.stats(ob))
k.export(ob, os.path.join(OUT, "df_outpost.glb"))
print("SHEET", k.preview([ob], os.path.join(OUT, "df_outpost_sheet.png")))
