#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
zig=${ZIG:-$HOME/.local/opt/zig-x86_64-linux-0.17.1/zig}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

lock=()

for candidate in "$root/tools/blenderlock.sh" "$HOME/projects/dronefire/tools/blenderlock.sh"; do
	if [ -x "$candidate" ]; then
		lock=(env NEED_MB=1500 "$candidate")
		break
	fi
done

"${lock[@]}" "$zig" build-exe -O ReleaseFast --dep shared -Mroot="$root/tools/mapaudit.zig" -Mshared="$root/src/shared/root.zig" --cache-dir "$HOME/.cache/dfassetcheck" -femit-bin="$work/mapaudit"

maps=$(sed -n 's/^ *pub const \([a-z0-9_]*\) = @import("\1\.zig");$/\1/p' "$root/src/shared/maps/registry.zig")

[ -n "$maps" ] || { echo "assetcheck: no maps in registry.zig" >&2; exit 1; }

for map in $maps; do
	"${lock[@]}" "$work/mapaudit" "$map" --kinds 2>"$work/$map.kinds" || { cat "$work/$map.kinds" >&2; exit 1; }
done

python3 -I - "$root" "$work" "$maps" "$@" <<'PY'
import json
import os
import posixpath
import re
import struct
import sys
import zipfile
import zlib

root, work, maps = sys.argv[1], sys.argv[2], sys.argv[3].split()
targets = sys.argv[4:]
assets = os.path.join(root, "src", "client", "assets")
client = os.path.join(root, "src", "client")
need = {}
errors = []


def source(path):
    with open(os.path.join(client, path)) as f:
        return f.read()


def want(rel, why):
    need.setdefault(posixpath.normpath(rel), set()).add(why)


def has(rel):
    path = os.path.join(assets, rel)

    return os.path.isfile(path) and os.path.getsize(path) > 0


def model(rel, why):
    want(rel, why)

    if not has(rel):
        return

    with open(os.path.join(assets, rel), "rb") as f:
        data = f.read()

    try:
        if rel.endswith(".glb"):
            if data[:4] != b"glTF" or struct.unpack_from("<I", data, 8)[0] != len(data):
                raise ValueError("bad header or truncated")

            doc = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
        else:
            doc = json.loads(data)
    except (ValueError, struct.error) as e:
        errors.append(f"broken {rel} ({why}): {e}")
        return

    if not doc.get("meshes"):
        errors.append(f"no meshes in {rel} ({why})")

    for item in doc.get("buffers", []) + doc.get("images", []):
        uri = item.get("uri", "")

        if uri and not uri.startswith("data:"):
            want(posixpath.join(posixpath.dirname(rel), uri.replace("%20", " ")), why)


placed = 0

for name in maps:
    with open(os.path.join(work, name + ".kinds")) as f:
        kinds = [line.split(" ", 1)[1].strip() for line in f if line.startswith("KIND ")]

    if not kinds:
        errors.append(f"no placed kinds listed for {name}")

    placed += len(kinds)

    for kind in kinds:
        rel = "props/" + kind
        stem = rel.rsplit(".", 1)[0]
        model(rel, name)

        if has(stem + ".lods"):
            want(stem + ".lods", name)

            with open(os.path.join(assets, stem + ".lods")) as f:
                steps = f.read().split()

            for k in range(len(steps)):
                model(f"{stem}.lod{k + 1}.glb", name)
        elif has(stem + ".lod1.glb"):
            errors.append(f"{stem}.lods missing but {stem}.lod1.glb exists ({name})")

        if has(stem + ".lod.glb"):
            model(stem + ".lod.glb", name)

    want(f"pvs/{name}.bin", name)
    want(f"ui/maps/{name}.png", name)

fleet = source("fleet.zig")
heroes = re.findall(r'\.dir = "(\w+)".*?\.split = (true|false)', fleet)

for folder, split in heroes:
    model(f"cars/{folder}/body.glb", "vehicle")

    if split == "true":
        model(f"cars/{folder}/wheel.glb", "vehicle")

    if has(f"cars/{folder}/wheelR.glb"):
        model(f"cars/{folder}/wheelR.glb", "vehicle")

crafts = re.findall(r'\.name = "[^"]+", \.dir = "(\w+)"', source("air.zig"))

for folder in crafts:
    model(f"air/{folder}/body.glb", "aircraft")
    model(f"air/{folder}/gear.glb", "aircraft")

if not heroes or not crafts:
    errors.append("could not read vehicle lists from fleet.zig and air.zig")

gunart = source("gunart.zig")
guns = set(re.findall(r'\.file = "(\w+)"', gunart)) | set(re.findall(r'load(?:Glb)?\(dir, "(\w+)"\)', gunart))

for gun in sorted(guns):
    model(f"guns/{gun}.glb", "weapon")

    for extra in os.listdir(os.path.join(assets, "guns")):
        if re.fullmatch(re.escape(gun) + r"\.m\d+\.etc", extra):
            want("guns/" + extra, "weapon")

clips = re.search(r"pub const Clip = enum \{(.*?)\};", source("audio.zig"), re.S).group(1)

for clip in re.findall(r"^\s*(\w+),", clips, re.M):
    want(f"sounds/{'switch' if clip == 'swap' else clip}.ogg", "sound")

for path in os.listdir(client):
    if path.endswith(".zig"):
        for rel in re.findall(r'"((?:sounds|sky|textures|characters)/[\w.-]+\.\w+)"', source(path)):
            if rel.endswith(".glb"):
                model(rel, path)
            else:
                want(rel, path)

want("textures/ground.png", "ground")

for i in range(int(re.search(r"mats: \[(\d+)\]rl\.Texture2D", source("gfx.zig")).group(1))):
    want(f"textures/mat{i}.png", "ground")

for folder, _, files in os.walk(assets):
    for file in sorted(files):
        if not file.endswith(".glb"):
            continue

        path = os.path.join(folder, file)

        with open(path, "rb") as f:
            data = f.read()

        try:
            doc = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
        except (ValueError, struct.error) as e:
            errors.append(f"broken {os.path.relpath(path, assets)}: {e}")
            continue

        for mesh in doc.get("meshes", []):
            for prim in mesh["primitives"]:
                count = doc["accessors"][prim["attributes"]["POSITION"]]["count"]

                if "indices" in prim and count > 65536:
                    errors.append(f"{os.path.relpath(path, assets)}: {count} indexed vertices in one primitive, raylib truncates to 16 bit (tools/glbsplit.py)")

for rel, why in sorted(need.items()):
    if not has(rel):
        errors.append(f"missing {rel} ({', '.join(sorted(why))})")

def crc(path):
    with open(path, "rb") as f:
        return zlib.crc32(f.read())


for target in targets:
    if target.endswith(".apk"):
        with zipfile.ZipFile(target) as z:
            sums = {i.filename: i.CRC for i in z.infolist()}

        found = lambda rel: sums.get("assets/" + rel)
    else:
        base = os.path.join(target, "share", "dronefire")

        found = lambda rel, base=base: crc(os.path.join(base, rel)) if os.path.isfile(os.path.join(base, rel)) else None

    for rel in sorted(need):
        if not has(rel):
            continue

        got = found(rel)

        if got is None:
            errors.append(f"{target}: missing {rel}")
        elif got != crc(os.path.join(assets, rel)):
            errors.append(f"{target}: stale {rel}")

for e in errors:
    print("assetcheck:", e)

print(f"assetcheck: {len(maps)} maps, {placed} placed kinds, {len(need)} files, {len(targets)} packages, {len(errors)} problems")
sys.exit(1 if errors else 0)
PY
