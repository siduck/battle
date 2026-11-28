#!/usr/bin/env bash
set -u

root=$(cd "$(dirname "$0")/.." && pwd)
own=${OUT:-$root/.cache-stadium}
lock=${LOCK:-$HOME/projects/dronefire/tools/blenderlock.sh}
log=$(mktemp)

mkdir -p "$own"

for _ in $(seq 80); do
	"$lock" env PATH=/usr/bin:/bin MID=1 OUT="$own" ONLY="${ONLY:-}" blender -b --factory-startup --python "$root/tools/blender/midkit/stadium_build.py" > "$log" 2>&1
	rc=$?
	[ $rc -ne 75 ] && break
	sleep 15
done

grep -E "^BUILT|Error|Traceback|File |line |\[lpm\].*OVER" "$log" || true
rm -f "$log"
