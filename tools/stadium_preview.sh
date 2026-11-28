#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
src=${SRC:-$root/.cache-stadium}
out=${OUTDIR:-/tmp/claude-1000/stadium_scratch/pv}
lock=${LOCK:-$HOME/projects/dronefire/tools/blenderlock.sh}
cols=${COLS:-3}
sheet=$1
shift
mkdir -p "$out"
rm -f "$out"/pv_*.png
files=()

for n in "$@"; do
	files+=("$src/$n.glb")
done

"$lock" env PATH=/usr/bin:/bin blender -b --factory-startup --python "$root/tools/blender/midkit/preview.py" -- "${files[@]}" "$out/pv" 2>&1 | grep -E "Error|Traceback" || true
ls "$out"/pv_*.png | wc -l
rows=$(( ($(ls "$out"/pv_*.png | wc -l) + cols - 1) / cols ))
ffmpeg -loglevel error -y -pattern_type glob -i "$out/pv_*.png" -vf "tile=${cols}x${rows}" -frames:v 1 "$sheet"
