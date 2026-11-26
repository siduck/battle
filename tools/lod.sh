#!/usr/bin/env bash
set -u

root=$(cd "$(dirname "$0")/.." && pwd)
dirs=("$@")
[ ${#dirs[@]} -gt 0 ] || dirs=("$root"/src/client/assets/props/*/)

for d in "${dirs[@]}"; do
	mapfile -t files < <(find "$d" -maxdepth 1 -name "*.glb" ! -name "*.lod.glb" | sort)
	[ ${#files[@]} -gt 0 ] || continue
	env PATH=/usr/bin:/bin blender -b --python "$root/tools/blender/lod.py" -- "${files[@]}" 2>&1 | grep -E "^LOD|Error|Traceback"
done
