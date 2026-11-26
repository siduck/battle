import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4
SKY = [(0.0, (42, 27, 74)), (0.34, (110, 44, 104)), (0.52, (214, 86, 82)), (0.66, (236, 116, 78)), (1.0, (244, 136, 84))]
SUN_TOP = (255, 232, 150)
SUN_BOTTOM = (255, 156, 72)
DUNE_BACK = (184, 82, 62)
DUNE_MID = (132, 52, 66)
DUNE_FRONT = (78, 34, 62)
DRONE = (30, 22, 48)
DRONE_EDGE = (74, 56, 104)
ROTOR = (30, 22, 48, 150)
LENS_RING = (255, 122, 58)
LENS_CORE = (255, 214, 130)


def ramp(stops, t):
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            k = (t - a) / (b - a)

            return tuple(ca[i] + (cb[i] - ca[i]) * k for i in range(3))

    return stops[-1][1]


def vertical(size, stops, top=0.0, bottom=1.0):
    ys = np.linspace(0, 1, size)
    ts = np.clip((ys - top) / (bottom - top), 0, 1)
    rows = np.array([ramp(stops, t) for t in ts], dtype=np.float32)
    img = np.repeat(rows[:, None, :], size, axis=1).astype(np.uint8)

    return Image.fromarray(img, "RGB").convert("RGBA")


def dune(size, base, amp, freq, phase, tilt):
    u = size / 1000
    pts = [(0, size)]

    for i in range(0, 1001, 4):
        x = i / 1000
        y = base + amp * math.sin(x * math.tau * freq + phase) + tilt * (x - 0.5)
        pts.append((i * u, y * u))

    pts.append((size, size))

    return pts


def background(size):
    u = size / 1000
    img = vertical(size, SKY)
    sun_c, sun_r = (500, 610), 300
    sun = vertical(size, [(0.0, SUN_TOP), (1.0, SUN_BOTTOM)], (sun_c[1] - sun_r) / 1000, (sun_c[1] + sun_r) / 1000)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)

    md.ellipse([(sun_c[0] - sun_r) * u, (sun_c[1] - sun_r) * u, (sun_c[0] + sun_r) * u, (sun_c[1] + sun_r) * u], fill=255)

    y, gap = 600, 8

    while y < sun_c[1] + sun_r:
        md.rectangle([0, y * u, size, (y + gap) * u], fill=0)
        y += gap + 30
        gap += 7

    glow = mask.filter(ImageFilter.GaussianBlur(60 * u))
    img = Image.composite(Image.new("RGBA", (size, size), (255, 170, 90, 255)), img, glow.point(lambda v: v * 0.35))
    img = Image.composite(sun, img, mask)
    d = ImageDraw.Draw(img)

    d.polygon(dune(size, 760, 26, 1.1, 0.6, -60), fill=DUNE_BACK)
    d.polygon(dune(size, 835, 30, 0.8, 2.4, 70), fill=DUNE_MID)
    d.polygon(dune(size, 915, 22, 1.3, 4.0, -40), fill=DUNE_FRONT)

    return img


def drone(size, scale, cx, cy):
    u = size / 1000
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def p(x, y):
        return (cx + (x - 500) * scale) * u, (cy + (y - 470) * scale) * u

    def box(x0, y0, x1, y1):
        a, b = p(x0, y0), p(x1, y1)

        return [a[0], a[1], b[0], b[1]]

    def w(v):
        return max(1, round(v * scale * u))

    def arm(x0, y0, x1, y1, t):
        d.line([p(x0, y0), p(x1, y1)], fill=DRONE, width=w(t))

    def rotor(x, y, rw, rh):
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)

        ld.ellipse(box(x - rw, y - rh, x + rw, y + rh), fill=ROTOR)
        ld.ellipse(box(x - rw, y - rh, x + rw, y + rh), outline=DRONE + (255,), width=w(10))
        img.alpha_composite(layer)
        d.line([p(x - rw * 0.78, y + rh * 0.22), p(x + rw * 0.78, y - rh * 0.22)], fill=DRONE, width=w(14))
        d.rounded_rectangle(box(x - 9, y - 8, x + 9, y + 34), radius=w(6), fill=DRONE)

    def motor(x, y, mw, mh):
        d.rounded_rectangle(box(x - mw, y - mh, x + mw, y + mh), radius=w(14), fill=DRONE)

    arm(500, 450, 300, 372, 34)
    arm(500, 450, 700, 372, 34)
    motor(300, 378, 24, 26)
    motor(700, 378, 24, 26)
    rotor(300, 336, 96, 22)
    rotor(700, 336, 96, 22)
    arm(500, 470, 205, 418, 46)
    arm(500, 470, 795, 418, 46)
    motor(205, 424, 30, 34)
    motor(795, 424, 30, 34)
    rotor(205, 372, 128, 24)
    rotor(795, 372, 128, 24)
    d.polygon([p(392, 440), p(608, 440), p(636, 500), p(584, 556), p(416, 556), p(364, 500)], fill=DRONE)
    d.rounded_rectangle(box(420, 404, 580, 452), radius=w(22), fill=DRONE)
    d.line([p(436, 412), p(564, 412)], fill=DRONE_EDGE, width=w(8))
    d.line([p(440, 548), p(410, 610)], fill=DRONE, width=w(16))
    d.line([p(560, 548), p(590, 610)], fill=DRONE, width=w(16))
    d.line([p(380, 612), p(450, 612)], fill=DRONE, width=w(14))
    d.line([p(550, 612), p(620, 612)], fill=DRONE, width=w(14))
    d.ellipse(box(458, 456, 542, 540), fill=LENS_RING)
    d.ellipse(box(474, 472, 526, 524), fill=DRONE)
    d.ellipse(box(486, 484, 514, 512), fill=LENS_CORE)

    return img


def rounded(img, radius):
    size = img.size[0]
    mask = Image.new("L", (size, size), 0)

    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius * size, fill=255)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    out.paste(img, (0, 0), mask)

    return out


def full(size):
    big = size * SS
    img = background(big)

    img.alpha_composite(drone(big, 1.08, 500, 485))

    return rounded(img, 0.22).resize((size, size), Image.LANCZOS)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


ADAPTIVE = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
"""


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    icon_dir = os.path.join(root, "src/client/assets/icon")
    res = os.path.join(root, "src/client/android/res")
    master = full(1024)

    save(master, os.path.join(icon_dir, "icon.png"))

    for s in (512, 256):
        save(full(s), os.path.join(icon_dir, f"icon-{s}.png"))

    master.save(os.path.join(icon_dir, "dronefire.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    big = 432 * SS
    bg = background(big)
    fg = drone(big, 0.8, 500, 505)

    for name, legacy in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        layer = legacy * 9 // 4
        folder = os.path.join(res, f"mipmap-{name}")

        save(full(legacy), os.path.join(folder, "ic_launcher.png"))
        save(bg.resize((layer, layer), Image.LANCZOS), os.path.join(folder, "ic_launcher_background.png"))
        save(fg.resize((layer, layer), Image.LANCZOS), os.path.join(folder, "ic_launcher_foreground.png"))

    os.makedirs(os.path.join(res, "mipmap-anydpi-v26"), exist_ok=True)

    with open(os.path.join(res, "mipmap-anydpi-v26", "ic_launcher.xml"), "w") as f:
        f.write(ADAPTIVE)


main()
