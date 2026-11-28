#!/usr/bin/env bash
set -u

root=$(cd "$(dirname "$0")/.." && pwd)
lock=${LOCK:-$HOME/projects/dronefire/tools/blenderlock.sh}
own=$root/.cache-stadium
zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig
props=$root/src/client/assets/props/stadium/

locked() {
	local rc

	for _ in $(seq 80); do
		"$lock" "$@"
		rc=$?
		[ $rc -ne 75 ] && return $rc
		sleep 15
	done

	return 75
}

"$root/tools/stadium_kit.sh"
OWN="$own" locked "$root/tools/mapkit.sh" stadium
rm -f "$props"*.lod*.glb "$props"*.lods

if [ -n "${FAR_LOD:-}" ]; then
	locked "$root/tools/lod.sh" "$props" | grep -v "^LOD" || true
fi

REBASE=1 LOD_ERRORS="${LOD_ERRORS:-0.01 0.04}" "$root/tools/meshlod.sh" "$props" | tail -1
cd "$root"
locked "$zig" build -Drelease -j2 2>&1 | grep -A3 "error:" || true

fdfile=$(mktemp)
Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$fdfile" ] && break
	sleep 0.1
done

DISPLAY=:$(head -n1 "$fdfile") DF_MUTE=1 DF_WIN=640x360 DF_MAP=stadium DF_PVSGEN="$root/src/client/assets/pvs" locked timeout 300 "$root/zig-out/bin/dronefire" 2>&1 | grep "^pvs" || true
kill "$xpid" 2>/dev/null
rm -f "$fdfile"
locked "$zig" build -Drelease -j2 2>&1 | grep -A3 "error:" || true
du -sh "$props"
