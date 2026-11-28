#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
props=${OUT:-$root/src/client/assets/props/lab}
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig

env PATH=/usr/bin:/bin OUT="$props" ONLY="${ONLY:-}" blender -b --factory-startup --python-exit-code 1 --python "$root/tools/blender/labkit/build.py" 2>&1 | grep -E "^BUILT|Error|Traceback|File \""

du -sh "$props"
cd "$root"

if [ -z "${NOPVS:-}" ]; then
	$zig build -Drelease -j2
	n=140

	while [ -e "/tmp/.X11-unix/X$n" ] || [ -e "/tmp/.X$n-lock" ]; do n=$((n + 1)); done

	Xvfb ":$n" -screen 0 640x360x24 >/dev/null 2>&1 &
	xpid=$!
	sleep 1
	DISPLAY=":$n" DF_MUTE=1 DF_WIN=640x360 DF_MAP=lab DF_PVSGEN="$root/src/client/assets/pvs" timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
	kill "$xpid" 2>/dev/null
fi
