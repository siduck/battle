#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
props=$root/src/client/assets/props/frontier
cache=$root/.zig-cache/frontier
lib=${MESHOPT_LIB:-$HOME/.cache/battle/libmeshopt.so}

mkdir -p "$cache" "$props"
env PATH=/usr/bin:/bin INFO="$cache" ONLY="${ONLY:-}" blender -b --factory-startup --python-exit-code 1 --python "$root/tools/blender/frontier/fr_build.py" 2>&1 | grep -E "^(BUILT|TOTAL)|Error|Traceback"
[ -f "$lib" ] || "$root/tools/meshlod.sh" "$props/" >/dev/null
MESHOPT_LIB="$lib" python3 "$root/tools/blender/frontier/fr_lods.py" "$props"
du -sh "$props"
