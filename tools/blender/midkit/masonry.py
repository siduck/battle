import math

import common as m
import jp
from common import add, bx, flat, bar, place, shift, solid, storey, grid, band, plinth, cornice, parapet, k


def lite(w, h, wall, **o):
    if m.FAR:
        return m.flush(w, h, 0.58) + [flat((w + 0.2, 0.22, 0.1), (0, -0.09, -0.1), o.get("trim", "ny_lime"))]

    items = [m.quad(w, h * 0.58, (0, m.T - 0.12, 0), "ny_glass"), m.quad(w, h * 0.42, (0, m.T - 0.12, h * 0.58), "ny_glass_light")]
    items.append(bx((w + 0.2, 0.22, 0.1), (0, -0.09, -0.1), o.get("trim", "ny_lime"), 0.015))

    return items


m.OPENINGS["lite"] = lite


def ground_specs(kind, bw, gh, cols=3, door_x=None):
    if kind == "store":
        w = bw - 1.0

        return [("store", 0, 0.45, w, gh - 1.05, {"bays": max(2, int(w / 2.0))})]

    if kind == "storedoor":
        dx = door_x if door_x is not None else bw * 0.3
        sw = bw * 0.6 - 0.5

        return [("store", -bw * 0.18, 0.45, sw, gh - 1.05, {"bays": max(2, int(sw / 1.8))}), ("door", dx, 0.5, 1.3, 2.6, {})]

    if kind == "door":
        return [("door", 0, 0.5, 1.4, 2.7, {})] + [("sash", x, 1.2, 1.1, 1.7, {}) for x in (-bw * 0.3, bw * 0.3)]

    if kind == "windows":
        return grid(bw, cols, 1.2, 1.8, 1.2, 0.5)

    return []


def masonry(name, w, d, H, gh=4.2, parap=0.7, color="ny_brick", trim="ny_lime", cols=3, win=(1.1, 1.9), ground="store", seed=1, side_cols=2, fire=False, awning=None, cornice_on=True, roof=3, tank=False,
            stoop_rise=0.0, bands=True, bay=None, back_cols=None, extra=None, door_x=None, ground_side=None, corner=False, tall_win=None):
    m.setup(seed)
    out = 0.3 if cornice_on else 0.1
    bw = w - 2 * out
    bd = d - 2 * out
    n = max(1, round((H - gh - parap - 0.4) / 3.2))
    fh = (H - gh - parap - 0.4) / n
    sill = (fh - win[1]) * 0.35
    plinth(bw, bd, 0.5, "ny_conc_dark", 0.06)
    gs = ground_specs(ground, bw, gh, cols, door_x)

    if stoop_rise:
        gs = [("door", bw * 0.2, stoop_rise + 0.1, 1.4, 2.5, {}), ("sash", -bw * 0.2, stoop_rise + 0.7, 1.2, 1.9, {"bars": True})]

    side_ground = ground_specs(ground_side if ground_side is not None else "none", bd, gh, 2)
    bk = back_cols or side_cols
    storey(bw, bd, 0, gh, "ny_conc_dark" if ground in ("store", "storedoor") else trim if ground == "door" else color,
           front=gs, back=[("lite", x, 1.2, 1.1, 1.7, {"trim": trim}) for x in jp_cols(bw, bk)], left=side_ground, right=side_ground)

    if bands:
        band(bw, bd, gh - 0.1, trim, 0.3, 0.12)

    for i in range(n):
        z = gh + i * fh + 0.2
        front = grid(bw, cols, win[0], win[1], sill, 0.6, "sash", trim="ny_lime_light" if color != "ny_brown" else "ny_brown_dark")
        back = [("lite", x, sill, win[0], win[1], {"trim": trim}) for x in jp_cols(bw, bk)]
        left = [("lite", x, sill, win[0], win[1], {"trim": trim}) for x in jp_cols(bd - 0.5, side_cols)]
        right = list(left)

        if corner:
            left = [("sash", x, sill, win[0], win[1], {"trim": "ny_lime_light"}) for x in jp_cols(bd - 0.5, side_cols)]

        storey(bw, bd, z - 0.2, fh, color, front=front, back=back, left=left, right=right)

        if bands and i % 3 == 2 and i < n - 1:
            band(bw, bd, z + fh - 0.35, trim, 0.2, 0.06)

    H_body = gh + n * fh + 0.4

    if cornice_on:
        cornice(bw, bd, H_body - 0.1, trim, 0.55, 0.3)

    parapet(bw, bd, H_body + 0.35, parap, color, trim)

    if fire:
        place(m.fire_escape(min(2.6, bw * 0.45), n, fh, 0, z0=gh - 0.6, x=bw * 0.2 if bw > 6 else 0.0, depth=1.0), 0, -bd / 2, 0, 0)

    if awning:
        a, b = awning
        place(m.striped_awning(min(bw - 1.0, 5.0), 1.3, a, b), 0, -bd / 2, gh - 0.55, 0)

    if stoop_rise:
        place(m.stoop(1.6, stoop_rise, "ny_lime"), bw * 0.2, -bd / 2, 0, 0)

    if roof:
        m.roof_gear(bw, bd, H_body + 0.4, roof, tank, seed)

    if extra:
        extra(bw, bd, gh, fh, n)

    solid(-bw / 2, -bd / 2, bw / 2, bd / 2, -0.5, H_body + 0.4 + parap)
    ob = m.finish(name)

    return ob


def jp_cols(width, cols, margin=0.6):
    gap = (width - 2 * margin) / cols

    return [-width / 2 + margin + gap * (i + 0.5) for i in range(cols)]
