#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
props=$root/src/client/assets/props/alpine
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig

env PATH=/usr/bin:/bin OUT="$props" ONLY="${ONLY:-}" blender -b --factory-startup --python-exit-code 1 --python "$root/tools/blender/alpinekit/build.py" 2>&1 | grep -E "^BUILT|Error|Traceback"

du -sh "$props"
cd "$root"

if [ -z "${NOPVS:-}" ]; then
	$zig build -Drelease -j2
	fdfile=$(mktemp)
	Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
	xpid=$!

	for _ in $(seq 50); do
		[ -s "$fdfile" ] && break
		sleep 0.1
	done

	DISPLAY=:$(head -n1 "$fdfile") DF_MUTE=1 DF_WIN=640x360 DF_MAP=alpine DF_PVSGEN="$root/src/client/assets/pvs" timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
	kill "$xpid" 2>/dev/null
	rm -f "$fdfile"
fi
