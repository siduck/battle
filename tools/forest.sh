#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
own=$root/.cache-forest/mid
props=$root/src/client/assets/props/forest
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig
trees=oak,maple,birch,pine,young,dead,pines,stump,roots,bush,fern,tuft,reeds,cattail,flower,toadstool,lily

mkdir -p "$own"
rm -f "$own"/*.glb
env PATH=/usr/bin:/bin MID=1 OUT="$own" ONLY="${ONLY:-}" blender -b --factory-startup --python "$root/tools/blender/midkit/forest_build.py" 2>&1 | grep -E "^BUILT|Error|Traceback" || true

rm -f "$props"/*.glb "$props"/*.lods
env -u ONLY OWN="$own" "$root/tools/mapkit.sh" forest

lib="$HOME/.cache/battle/libmeshopt.so"
[ -f "$lib" ] || "$root/tools/meshlod.sh" "$props/" >/dev/null

soft=()
hard=()

for f in "$props"/*.glb; do
	n=$(basename "$f" .glb)

	case ",$trees," in
	*",$n,"*) soft+=("$f") ;;
	*) hard+=("$f") ;;
	esac
done

MESHOPT_LIB="$lib" LOD0=1 PAINT_EDGE="${SOFT_EDGE:-0.45}" CREASE="${SOFT_CREASE:-14}" LOD_ERRORS="${TREE_ERRORS:-0.04 0.16}" python3 -I "$root/tools/meshlod/meshlod.py" "${soft[@]}"
MESHOPT_LIB="$lib" LOD0=1 PAINT_EDGE="${HARD_EDGE:-0.3}" CREASE=38 python3 -I "$root/tools/meshlod/meshlod.py" "${hard[@]}"

for n in tuft flower lily stone cattail toadstool stump fern; do
	rm -f "$props/$n".lod?.glb "$props/$n.lods"
done

du -sh "$props"
cd "$root"
$zig build -Drelease -j2 2>&1 | grep -A3 "error:" || true

if [ -z "${NOPVS:-}" ]; then
	fdfile=$(mktemp)
	Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
	xpid=$!

	for _ in $(seq 50); do
		[ -s "$fdfile" ] && break
		sleep 0.1
	done

	DISPLAY=:$(head -n1 "$fdfile") DF_MUTE=1 DF_WIN=640x360 DF_MAP=forest DF_PVSGEN="$root/src/client/assets/pvs" timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
	kill "$xpid" 2>/dev/null
	rm -f "$fdfile"
	$zig build -Drelease -j2 2>&1 | grep -A3 "error:" || true
fi
