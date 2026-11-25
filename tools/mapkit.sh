#!/usr/bin/env bash
set -eu

if [ $# -lt 1 ]; then
	echo "usage: tools/mapkit.sh <map> [polyfork-dir]" >&2
	exit 1
fi

map=$1
root=$(cd "$(dirname "$0")/.." && pwd)
script=$root/tools/blender/maps/$map.py
pf=${2:-$HOME/.cache/polyfork/$map}

[ -f "$script" ] || { echo "missing $script" >&2; exit 1; }

env PATH=/usr/bin:/bin BPYLIB="${BPYLIB:-$HOME/.cache/battle/bpylib}" ROOT="$root" PF="$pf" blender -b --python "$script" 2>&1 | grep -E "^(DONE|TRIS)|Error|Traceback" || true

ls -la "$root/src/shared/maps/${map}_kit.zig"
du -sh "$root/src/client/assets/props/$map"
