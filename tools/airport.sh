#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
own=$root/.cache-airport
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig

mkdir -p "$own"
env PATH=/usr/bin:/bin OUT="$own" ONLY="${ONLY:-}" blender -b --factory-startup --python "$root/tools/blender/midkit/airport_build.py" 2>&1 | grep -E "^BUILT|Error|Traceback" || true
env -u ONLY OWN="$own" "$root/tools/mapkit.sh" airport
"$root/tools/lod.sh" "$root/src/client/assets/props/airport/" | grep -v "^LOD" || true
"$root/tools/meshlod.sh" "$root/src/client/assets/props/airport/"
cd "$root"
"$zig" build -Drelease -j2 2>&1 | grep -A3 "error:" || true
fdfile=$(mktemp)
Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$fdfile" ] && break
	sleep 0.1
done

DISPLAY=:$(head -n1 "$fdfile") DF_MUTE=1 DF_WIN=640x360 DF_MAP=airport DF_PVSGEN="$root/src/client/assets/pvs" timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
kill "$xpid" 2>/dev/null
rm -f "$fdfile"
"$zig" build -Drelease -j2 2>&1 | grep -A3 "error:" || true
