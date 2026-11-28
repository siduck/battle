#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
props=${OUT:-$root/src/client/assets/props/construction}
lib="$HOME/.cache/battle/libmeshopt.so"
bpylib=${BPYLIB:-$HOME/.cache/battle/bpylib}
big=(tower tower2 crane cabins frame)
mid=(pilewall silo formwork framebay scaffold fence hoarding barrier lamp core genset skip lights mixer sign vault pipes ibc rebar timber scafstack precast pallet bag blocks)
soft=(box_red box_blue box_green drums spool sandbags)

mkdir -p "$props"
[ -n "${ONLY:-}" ] || rm -f "$props"/*.glb "$props"/*.lods
env PATH=/usr/bin:/bin OUT="$props" ONLY="${ONLY:-}" blender -b --factory-startup --python "$root/tools/blender/maps/construction.py" 2>&1 | grep -E -A8 "^(DONE|TRIS)|Error|Traceback" | grep -v "^Blender quit" || true

[ -f "$lib" ] || "$root/tools/meshlod.sh" "$props/" >/dev/null 2>&1 || [ -f "$lib" ]

lod() {
	local errors=$1
	shift
	local files=()

	for n in "$@"; do
		[ -f "$props/$n.glb" ] && files+=("$props/$n.glb")
	done

	[ ${#files[@]} -eq 0 ] || MESHOPT_LIB="$lib" PYTHONPATH="$bpylib" PAINT_EDGE="${PAINT_EDGE:-0.3}" LOD_ERRORS="$errors" python3 -P "$root/tools/meshlod/meshlod.py" "${files[@]}"
}

lod "${BIG_ERRORS:-0.07}" "${big[@]}"
lod "${MID_ERRORS:-0.045}" "${mid[@]}"
lod "${SOFT_ERRORS:-0.065}" "${soft[@]}"

du -sb "$props"
