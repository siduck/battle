import colorsys
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "suburb"))

import jp
import props_street as ps
from jp import add, c, k
from mathutils import Vector

B = ps.B
F = ps.F
R = ps.R
cyl = ps.cyl
turn = ps.turn
disc = ps.disc
side_disc = ps.side_disc
tilted = ps.tilted


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)

    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


ARENA_PALETTE = {
    "st_blue_l": hsl(212, 0.24, 0.72),
    "st_blue": hsl(212, 0.27, 0.54),
    "st_blue_d": hsl(212, 0.30, 0.36),
    "st_blue_dd": hsl(212, 0.30, 0.24),
    "st_conc_l": hsl(38, 0.07, 0.76),
    "st_conc": hsl(38, 0.06, 0.62),
    "st_conc_d": hsl(38, 0.06, 0.46),
    "st_conc_dd": hsl(38, 0.07, 0.30),
    "st_red": hsl(8, 0.40, 0.48),
    "st_red_d": hsl(8, 0.42, 0.34),
    "st_white": hsl(45, 0.14, 0.88),
    "st_char": hsl(215, 0.10, 0.18),
    "st_steel": hsl(210, 0.08, 0.64),
    "st_steel_d": hsl(210, 0.10, 0.42),
    "st_wood": hsl(28, 0.28, 0.44),
    "st_wood_d": hsl(28, 0.30, 0.30),
    "st_wood_l": hsl(30, 0.26, 0.58),
    "st_mustard": hsl(42, 0.40, 0.54),
    "st_pine": hsl(140, 0.24, 0.28),
    "st_pine_l": hsl(130, 0.24, 0.38),
    "st_pine_d": hsl(150, 0.24, 0.20),
    "st_glass": hsl(205, 0.24, 0.30),
    "st_glass_l": hsl(205, 0.22, 0.52),
    "st_net": hsl(40, 0.06, 0.82),
    "st_roof": hsl(212, 0.20, 0.42),
    "st_roof_dark": hsl(212, 0.24, 0.30),
    "st_roof_light": hsl(212, 0.20, 0.52),
}

for _name, _hex in ARENA_PALETTE.items():
    if _name not in k._INDEX:
        k._INDEX[_name] = len(k.PALETTE)
        k.PALETTE.append((_name, _hex))


BEVEL_SEGMENTS = int(os.environ.get("BEVEL_SEGMENTS", "1"))


def chamfer(ob, width=0.02, angle=30.0, segments=1):
    import bmesh

    width *= 1.7
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle)]

    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=BEVEL_SEGMENTS, profile=0.5, affect="EDGES", clamp_overlap=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    return ob


k.chamfer = chamfer


def setup(seed=3):
    jp.setup(seed)
    k.KEY = None
    k.KEY_MIX = 0.0
    k.ACCENTS = set()


def done(name, budget):
    return jp.finish(name, budget * 3, fuse_soft=False)


def flat(size, at, color):
    return add(jp.flat(size, at, color))


def rod(a, b, r, color, sides=4):
    return add(jp.bar(a, b, r, color, sides))


def profile_yz(outline, width, color, x=0.0):
    ob = k.sweep("prof", outline, width, (0, 0, 0), c(color), axis="y")
    k.rotate(ob, 90)
    k.move(ob, x, 0, 0)

    return add(ob)


def profile_xz(outline, depth, color, y=0.0):
    ob = k.sweep("prof", outline, depth, (0, y, 0), c(color), axis="y")

    return add(ob)


def stepped_outline(depth, rise, rows):
    dy = depth / rows
    out = [(-depth / 2, 0.0)]
    tops = []

    for i in range(rows):
        ya = -depth / 2 + i * dy
        yb = ya + dy
        zt = rise * ((ya + yb) / 2 + depth / 2) / depth
        out += [(ya, zt), (yb, zt)]
        tops.append((ya, yb, zt))

    out += [(depth / 2, 0.0)]

    return out, tops


def terrace_body(width, depth, rise, rows, body="st_conc", lip="st_conc_l", riser="st_conc_d"):
    outline, tops = stepped_outline(depth, rise, rows)
    profile_yz(outline, width, body)

    for ya, yb, zt in tops:
        flat((width, 0.14, 0.05), (0, ya + 0.07, zt - 0.005), lip)
        flat((width, 0.03, 0.12), (0, ya + 0.015, max(zt - 0.2, 0.0)), riser)

    return tops


SEAT = [(0.28, 0.34), (0.56, 0.34), (0.56, 0.0), (0.66, 0.0), (0.66, 0.34), (0.74, 0.34), (0.79, 0.82), (0.70, 0.82), (0.60, 0.42), (0.28, 0.42)]


def seat_row(width, ya, zt, n, color, accent=None, accent_at=()):
    pitch = width / n
    sw = pitch - 0.07
    prof = [(ya + p[0], zt + p[1]) for p in SEAT]

    for i in range(n):
        x = -width / 2 + pitch * (i + 0.5)
        profile_yz(prof, sw, accent if accent and i in accent_at else color, x)

    for i in range(n + 1):
        x = -width / 2 + pitch * i
        flat((0.035, 0.34, 0.05), (min(max(x, -width / 2 + 0.02), width / 2 - 0.02), ya + 0.45, zt + 0.52), "st_blue_dd")


def handrail(p0, p1, h=1.0, post=0.8, r=0.025, color="st_steel_d", mid=True, sides=6):
    a = Vector(p0)
    b = Vector(p1)
    d = b - a
    n = max(1, int(d.length / post))
    up = Vector((0, 0, h))
    rod(a + up, b + up, r, color, sides)

    if mid:
        rod(a + up * 0.5, b + up * 0.5, r * 0.7, color, 4)

    for i in range(n + 1):
        p = a + d * (i / n)
        rod(p, p + up, r * 0.8, color, 4)


def truss_yz(p0, p1, height, x, panels, member=0.035, chord=0.05, color="st_steel_d", chord_color="st_steel"):
    a = Vector((x, p0[0], p0[1]))
    b = Vector((x, p1[0], p1[1]))
    d = b - a
    up = Vector((0, 0, height))
    rod(a, b, chord, chord_color, 4)
    rod(a - up, b - up, chord, chord_color, 4)

    for i in range(panels + 1):
        p = a + d * (i / panels)
        rod(p, p - up, member, color, 4)

    for i in range(panels):
        p = a + d * (i / panels)
        q = a + d * ((i + 1) / panels)

        if i % 2:
            rod(p, q - up, member, color, 4)
        else:
            rod(p - up, q, member, color, 4)


def lamp_bank(w, h, at, cols, rows, depth=0.3, body="st_steel_d", lens="st_white"):
    x, y, z = at
    B((w, depth, h), (x, y, z), body, 0.03)
    cw = w / cols
    ch = h / rows

    for i in range(cols):
        for j in range(rows):
            px = x - w / 2 + cw * (i + 0.5)
            pz = z + ch * j + ch * 0.1
            flat((cw * 0.8, 0.06, ch * 0.76), (px, y - depth / 2 - 0.03, pz), "st_steel")
            flat((cw * 0.6, 0.04, ch * 0.56), (px, y - depth / 2 - 0.07, pz + ch * 0.1), lens)


def glazing(w, h, at, panes=4, y_out=-0.02, frame="st_blue_d"):
    x, y, z = at
    flat((w, 0.05, h), (x, y, z), frame)
    pw = (w - 0.1) / panes

    for i in range(panes):
        px = x - w / 2 + 0.05 + pw * (i + 0.5)
        flat((pw - 0.06, 0.03, h * 0.55 - 0.05), (px, y + y_out, z + 0.05), "st_glass")
        flat((pw - 0.06, 0.03, h * 0.45 - 0.05), (px, y + y_out, z + h * 0.55), "st_glass_l")


def vent_grille(w, h, at, slats=5, color="st_steel_d", back="st_char"):
    x, y, z = at
    flat((w, 0.06, h), (x, y, z), back)

    for i in range(slats):
        zz = z + h * (i + 0.5) / slats - 0.01
        tilted((w - 0.06, 0.07, 0.018), (x, y - 0.045, zz), 28, color)


def punched_wall(w, h, thick, openings, color, at=(0, 0, 0), back="st_char", facing=0.0):
    x, y, z = at
    pieces = k.wall("w", w, h, thick, (0, 0, 0), openings, color, 0.0, bevel=0)

    for ox, oz, ow, oh in openings:
        pieces.append(jp.flat((ow, 0.04, oh), (ox, thick * 0.15, oz), back))

    for p in pieces:
        k.rotate(p, facing)
        k.move(p, x, y, z)
        add(p)

    return pieces


def louvre_slots(x0, x1, z0, z1, y, n, color="st_char"):
    h = (z1 - z0) / n

    for i in range(n):
        flat((x1 - x0, 0.05, h * 0.45), ((x0 + x1) / 2, y, z0 + i * h + h * 0.2), color)
