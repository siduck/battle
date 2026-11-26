#!/usr/bin/env bash
set -eu

mode=${1:-low}
root=$(cd "$(dirname "$0")/.." && pwd)
own=$root/.cache-suburb/$mode
mid=0
[ "$mode" = mid ] && mid=1

mkdir -p "$own"
env PATH=/usr/bin:/bin MID=$mid OUT="$own" ONLY="${ONLY:-}" blender -b --factory-startup --python "$root/tools/blender/suburb/build.py" 2>&1 | grep -E "^BUILT|Error|Traceback" || true
env -u ONLY OWN="$own" "$root/tools/mapkit.sh" japan
"$root/tools/lod.sh" "$root/src/client/assets/props/japan/" | grep -v "^LOD" || true
"$root/tools/meshlod.sh" "$root/src/client/assets/props/japan/"
cd "$root"
far=$root/.cache-suburb/far
mkdir -p "$far"
env PATH=/usr/bin:/bin FAR=1 MID=0 OUT="$far" ONLY=parlour,apartment,tower,barhut,konbini,corner,shop3,shop2,wide,roof blender -b --factory-startup --python "$root/tools/blender/suburb/build.py" 2>&1 | grep -E "Error|Traceback" || true
env PATH=/usr/bin:/bin FARONLY=1 OWN="$far" BPYLIB="${BPYLIB:-$HOME/.cache/battle/bpylib}" ROOT="$root" PF="$HOME/.cache/polyfork/japan" blender -b --python "$root/tools/blender/maps/japan.py" 2>&1 | grep -E "^DONE|Error|Traceback" || true
~/.local/opt/zig-x86_64-linux-0.17.1/zig build -Drelease -j2 2>&1 | grep -A3 "error:" || true
fdfile=$(mktemp)
Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$fdfile" ] && break
	sleep 0.1
done

DISPLAY=:$(head -n1 "$fdfile") DF_MUTE=1 DF_WIN=640x360 DF_MAP=japan DF_PVSGEN="$root/src/client/assets/pvs" timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
kill "$xpid" 2>/dev/null
rm -f "$fdfile"
~/.local/opt/zig-x86_64-linux-0.17.1/zig build -Drelease -j2 2>&1 | grep -A3 "error:" || true
