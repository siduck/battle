#!/usr/bin/env bash
set -u

map=${1:-nyc}
root=$(cd "$(dirname "$0")/.." && pwd)
own=${OWN:-/tmp/claude-1000/${map}_midkit}
far=$own.far
farout=$own.farout
lock=${LOCK-$HOME/projects/dronefire/tools/blenderlock.sh}
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig
props=$root/src/client/assets/props/$map/
far_error=${FAR_ERROR:-0.05}
buildings=$(cd "$root/tools/blender/midkit" && python3 -c "import ast; t = ast.parse(open('buildings_ny.py').read()); print(','.join(f.name for f in t.body if isinstance(f, ast.FunctionDef) and any(getattr(d, 'id', '') == 'reg' for d in f.decorator_list)))")
meshopt="$HOME/.cache/battle/libmeshopt.so"

run() {
	local rc

	while true; do
		"$lock" "$@"
		rc=$?
		[ $rc -ne 75 ] && return $rc
		sleep 20
	done
}

rm -rf "$own" "$far" "$farout"
mkdir -p "$own" "$far" "$farout"
run env PATH=/usr/bin:/bin MID=1 OUT="$own" blender -b --factory-startup --python "$root/tools/blender/midkit/build.py" 2>&1 | grep -E "^BUILT|Error|Traceback" | awk '{t+=$3} END {print "BUILT tris", t}'
run env OWN="$own" "$root/tools/mapkit.sh" "$map"
run env PATH=/usr/bin:/bin FAR=1 MID=0 ONLY="$buildings" OUT="$far" blender -b --factory-startup --python "$root/tools/blender/midkit/build.py" 2>&1 | grep -E "Error|Traceback"
run env PATH=/usr/bin:/bin FAROUT="$farout" OWN="$far" PF="$HOME/.cache/polyfork/$map" BPYLIB="${BPYLIB:-$HOME/.cache/battle/bpylib}" ROOT="$root" blender -b --python "$root/tools/blender/maps/$map.py" 2>&1 | grep -E "Error|Traceback"
run bash "$root/tools/lod.sh" "$props" | grep -v "^LOD" || true
run bash "$root/tools/meshlod.sh" "$props"

for f in "$farout"/*.glb; do
	cp "$f" "$props/$(basename "$f" .glb).far.glb"
done

for f in "$farout"/*.glb; do
	name=$(basename "$f" .glb)
	rm -f "$props/$name.lod.glb" "$props/$name.lod1.glb" "$props/$name.lod2.glb"
	mv "$props/$name.far.glb" "$props/$name.lod1.glb"
	echo "$far_error" > "$props/$name.lods"
done

MESHOPT_LIB="$meshopt" python3 -I "$root/tools/meshlod/glbpack.py" "$props"/*.glb | awk '{n++} END {print "packed", n}'
run "$zig" build -Drelease -j2 2>&1 | grep -A3 "error:" || true
du -sh "$props"
