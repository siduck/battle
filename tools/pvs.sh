#!/usr/bin/env bash
set -u

prefix=${1:-zig-out}
maps=(desert islands airport alpine coast construction japan forest nyc pirate prehistoric racing lab salvage stadium warehouse)
fdfile=$(mktemp)
Xvfb -displayfd 3 -screen 0 640x360x24 3>"$fdfile" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$fdfile" ] && break
	sleep 0.1
done

disp=:$(head -n1 "$fdfile")
rm -f "$fdfile"

for m in "${maps[@]}"; do
	DISPLAY=$disp DF_MUTE=1 DF_WIN=640x360 DF_MAP=$m DF_PVSGEN=src/client/assets/pvs "$prefix/bin/dronefire" 2>&1 | grep "^pvs" &
done

wait $(jobs -p | grep -v "^$xpid$") 2>/dev/null
kill "$xpid" 2>/dev/null
