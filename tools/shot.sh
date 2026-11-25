#!/usr/bin/env bash
set -u

if [ $# -lt 2 ]; then
	echo "usage: tools/shot.sh <map> <out.jpg> [x,y,z,yaw,pitch] [prefix]" >&2
	exit 1
fi

map=$1
out=$2
cam=${3:-}
prefix=${4:-zig-out}
bin=$prefix/bin/dronefire
wait=${SHOT_WAIT:-20}
size=${SHOT_SIZE:-1280x720}

mkdir -p "$(dirname "$out")"

fdfile=$(mktemp)
Xvfb -displayfd 3 -screen 0 "${size}x24" 3>"$fdfile" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$fdfile" ] && break
	sleep 0.1
done

disp=:$(head -n1 "$fdfile")
rm -f "$fdfile"

envs=(DISPLAY="$disp" DF_WIN="$size")
[ "$map" = menu ] || envs+=(DF_MAP="$map")
[ -n "$cam" ] && envs+=(DF_CAM="$cam")
[ -n "${SHOT_HUD:-}" ] || envs+=(DF_NOHUD=1)

env "${envs[@]}" "$bin" >/dev/null 2>&1 &
gpid=$!

sleep "$wait"

win=$(DISPLAY=$disp xdotool search --name dronefire 2>/dev/null | head -n1)

if [ -n "$win" ]; then
	DISPLAY=$disp maim -i "$win" "$out"
else
	DISPLAY=$disp maim "$out"
fi

status=$?

kill "$gpid" 2>/dev/null
wait "$gpid" 2>/dev/null
kill "$xpid" 2>/dev/null
wait "$xpid" 2>/dev/null

[ $status -eq 0 ] && echo "$out"
exit $status
