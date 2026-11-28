#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIG = os.path.expanduser("~/.local/opt/zig-x86_64-linux-0.17.1/zig")
LOCK = next((p for p in [os.path.join(ROOT, "tools", "blenderlock.sh"), os.path.expanduser("~/projects/dronefire/tools/blenderlock.sh")] if os.path.exists(p)), "")

MAPS = [
    ("desert", "Frontier Town", "rural town"),
    ("islands", "Islands", "village + nature"),
    ("airport", "Airport", "open airfield"),
    ("alpine", "Alpine", "nature"),
    ("coast", "Boardwalk", "suburban/coast"),
    ("construction", "Construction", "industrial"),
    ("japan", "Suburb", "suburban"),
    ("forest", "Forest Camp", "nature"),
    ("nyc", "Downtown", "dense urban"),
    ("racing", "Highway", "open/vehicle"),
    ("lab", "Research Lab", "industrial"),
    ("stadium", "Stadium", "arena"),
]


def locked(cmd, need_mb):
    env = dict(os.environ, NEED_MB=str(need_mb))

    while True:
        p = subprocess.run([LOCK, *cmd], env=env, capture_output=True, text=True)

        if p.returncode != 75:
            return p

        print("waiting for RAM...", file=sys.stderr)
        time.sleep(30)


def build(binary):
    cmd = [ZIG, "build-exe", "-O", "ReleaseFast", "--dep", "shared", "-Mroot=" + os.path.join(ROOT, "tools/mapaudit.zig"), "-Mshared=" + os.path.join(ROOT, "src/shared/root.zig"), "-femit-bin=" + binary]
    p = locked(cmd, 1500)

    if p.returncode != 0:
        sys.exit(p.stderr)


COLORS = {"#": (46, 46, 52), ",": (222, 84, 60), ".": (196, 196, 186), " ": (246, 244, 236), "~": (120, 160, 212), "^": (150, 128, 100)}


def save_raster(rows, path):
    n = len(rows)
    ppm = path + ".ppm"

    with open(ppm, "wb") as f:
        f.write(f"P6 {n} {n} 255\n".encode())

        for row in reversed(rows):
            f.write(b"".join(bytes(COLORS.get(ch, (255, 0, 255))) for ch in row))

    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", ppm, path], check=False)
    os.remove(ppm)


def audit_all(binary, tags, raster_dir=None, half=0):
    flag = (" --raster" if raster_dir else "") + (f" --half={half}" if half else "")
    loop = " ".join(f'"{binary}" {t}{flag};' for t in tags)
    p = locked(["bash", "-c", loop], 800)
    results = []
    rows = []

    for line in p.stderr.splitlines():
        if line.startswith("RASTER"):
            rows = []
        elif line.startswith("R") and raster_dir:
            rows.append(line[1:])
        elif line.startswith("{"):
            r = json.loads(line)
            results.append(r)

            if raster_dir and rows:
                os.makedirs(raster_dir, exist_ok=True)
                save_raster(rows, os.path.join(raster_dir, f"{r['map']}_blocked.png"))
                rows = []

    missing = set(tags) - {r["map"] for r in results}

    if missing:
        print(f"no result for {sorted(missing)}\n{p.stderr[-2000:]}", file=sys.stderr)

    return results


def score(r):
    return r["blocked_pct"] * 1.0 + r["cover15"] * 0.6 + (100 - r["open12_pct"]) * 0.25 + r["solid_props_ha"] * 0.05


def table(results):
    rows = sorted(results, key=score, reverse=True)
    head = "| # | Map (tag) | Archetype | props/ha | solid props/ha | blocked % | width p50 m | walkable <2 m wide % | open >=12 m % | cover objs 15 m | nearest cover p50 m | sight p50 m | sight >50 m % | dead-end slots/ha | drive net % | landmarks | play half m | terrain half m | players/ha @12 | props total | props outside play | pieces | rays <10 m % |"
    out = [head, "|" + "|".join(["---"] * (head.count("|") - 1)) + "|"]
    arch = {m[0]: m[2] for m in MAPS}

    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['name']} ({r['map']}) | {arch.get(r['map'], '')} | {r['props_ha']:.0f} | {r['solid_props_ha']:.0f} | {r['blocked_pct']:.1f} | {r['width_p50']:.1f} | {r.get('width_under2_pct', 0):.0f} | {r['open12_pct']:.0f} | {r['cover15']:.1f} | {r['nearest_cover_p50']:.1f} | {r['sight_p50']:.0f} | {r['sight_over50_pct']:.0f} | {r['dead_ends_ha']:.2f} | {r['drive_pct']:.0f} | {r['landmarks']} | {r['play']:.0f} | {r.get('terrain_half', 0):.0f} | {12 / r['ha']:.1f} | {r.get('all_props', 0)} | {r.get('out_play', 0)} | {r['pieces']} | {r['sight_bands'][0] if isinstance(r.get('sight_bands'), list) else r.get('sight_bands', {})} |")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Measure prop density, blocked ground, route widths, cover and sightlines for every map")
    ap.add_argument("maps", nargs="*", help="map tags (default: all 16)")
    ap.add_argument("--bin", default="/tmp/claude-1000/audit_scratch/bin/mapaudit")
    ap.add_argument("--out", default="mapaudit.json")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--raster", metavar="DIR", help="write a top-down PNG per map: dark = blocked, red = 0.7 to 2 m slots, light grey = walkable, white = inside a free 12 m disc, blue = water")
    ap.add_argument("--half", type=float, default=0, help="audit an origin-centred window of this half-size instead of the map's play square")
    ap.add_argument("--heat", action="store_true", help="print 10x10 blocked-ground heatmaps (digit = blocked share in tenths)")
    a = ap.parse_args()

    if not a.no_build:
        build(a.bin)

    tags = a.maps or [m[0] for m in MAPS]
    results = audit_all(a.bin, tags, a.raster, a.half)

    for r in results:
        print(f"{r['map']}: blocked {r['blocked_pct']:.1f}% props {r['props_ha']:.0f}/ha", file=sys.stderr)

    with open(a.out, "w") as f:
        json.dump(results, f, indent=1)

    print(table(results))

    if a.heat:
        for r in results:
            print(f"\n{r['name']} blocked heat (north at bottom, x to the right)")

            for row in r["heat"]:
                print("  " + row)


if __name__ == "__main__":
    main()
