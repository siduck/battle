import common as m
from common import add, bx, flat, place, quad, rng


def ribs(w, z0, z1, floor_h, bay, pier="ny_lime", spandrel="ny_lime_dark", pier_w=0.5, sp_h=0.9, out=0.28, glass="ny_glass", mullion=False, lit=0.12):
    items = []
    r = rng()
    n = max(1, int(round((z1 - z0) / floor_h)))
    fh = (z1 - z0) / n
    cols = max(1, int(round(w / bay)))
    gw = w / cols
    band = sp_h * 0.9

    if m.FAR:
        items.append(quad(w, z1 - z0, (0, -0.02, z0), glass))

    for f in range(n):
        for i in range(0 if m.FAR else cols):
            x = -w / 2 + gw * (i + 0.5)
            gl = "ny_glass_light" if r.random() < lit else glass
            items.append(quad(gw - pier_w, fh - band, (x, -0.02, z0 + f * fh + band), gl))

            if mullion:
                items.append(flat((0.06, 0.1, fh - band), (x, -0.06, z0 + f * fh + band), "ny_iron_light"))

        items.append(flat((w, out, band), (0, -out / 2, z0 + f * fh), spandrel))

    for i in range(cols + 1):
        x = -w / 2 + gw * i
        items.append(flat((pier_w, out + 0.1, z1 - z0), (min(max(x, -w / 2 + pier_w / 2), w / 2 - pier_w / 2), -(out + 0.1) / 2, z0), pier))

    return items


def tier(w, d, z0, z1, floor_h, bay, side_bay=None, color="ny_lime", pier="ny_lime", spandrel="ny_lime_dark", **o):
    out = o.get("out", 0.28)
    add(flat((w, d, 0.14), (0, 0, z1 - 0.14), color))
    post = out + 0.4
    off = (out + 0.1 - 0.3) / 2

    for sx in (-1, 1):
        for sy in (-1, 1):
            add(flat((post, post, z1 - z0), (sx * (w / 2 + off), sy * (d / 2 + off), z0), pier))

    place(ribs(w - 0.04, z0, z1, floor_h, bay, pier, spandrel, **o), 0, -d / 2, 0, 0)
    place(ribs(w - 0.04, z0, z1, floor_h, bay, pier, spandrel, **o), 0, d / 2, 0, 180)
    sb = side_bay or bay
    place(ribs(d - 0.04, z0, z1, floor_h, sb, pier, spandrel, **o), -w / 2, 0, 0, -90)
    place(ribs(d - 0.04, z0, z1, floor_h, sb, pier, spandrel, **o), w / 2, 0, 0, 90)
