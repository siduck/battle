#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
out=${OUT:-$root/src/client/assets/ui/maps}
game=${GAME:-$root/zig-out/bin/dronefire}
work=$(mktemp -d)
xpid=
gpid=

cleanup() {
	[ -n "$gpid" ] && kill "$gpid" 2>/dev/null
	[ -n "$xpid" ] && kill "$xpid" 2>/dev/null
	wait 2>/dev/null
	rm -rf "$work"
}

trap cleanup EXIT

mkdir -p "$work/home/.config/dronefire" "$out"

views="
desert 45 118 44 -0.28
islands 0 128 44 -0.27
airport 45 118 44 -0.28
alpine 180 100 74 -0.54
coast -40 118 44 -0.28
construction 45 112 42 -0.28
japan 45 112 46 -0.30
forest 0 100 74 -0.54
nyc 45 128 88 -0.50
racing 45 118 44 -0.28
lab 45 112 42 -0.28
stadium 0 100 70 -0.52
"

xvfb_log=$work/display
Xvfb -displayfd 3 -screen 0 1920x1200x24 3>"$xvfb_log" >/dev/null 2>&1 &
xpid=$!

for _ in $(seq 50); do
	[ -s "$xvfb_log" ] && break
	sleep 0.1
done

export DISPLAY=:$(head -n1 "$xvfb_log")

while read -r map azimuth dist height pitch; do
	[ -n "$map" ] || continue

	case " ${ONLY:-$map} " in
	*" $map "*) ;;
	*) continue ;;
	esac

	cam=$(awk -v a="$azimuth" -v d="$dist" -v h="$height" -v p="$pitch" 'BEGIN { r = a * 3.14159265 / 180; printf "%.2f,%.2f,%.2f,%.4f,%.3f", -sin(r) * d, h, -cos(r) * d, r, p }')
	printf 'tuning=1\nfov=%s\nshow_fps=0\n' "${FOV:-50}" >"$work/home/.config/dronefire/settings.ini"
	env -u XDG_CONFIG_HOME HOME="$work/home" DF_MUTE=1 DF_NOHUD=1 DF_HOLDCAM=1 DF_WIN=960x480 DF_MAP="$map" DF_CAM="$cam" "$game" </dev/null >"$work/$map.log" 2>&1 &
	gpid=$!
	sleep "${WAIT:-25}"
	window=$(xdotool search --name dronefire | head -n1)
	maim -u -i "$window" "$work/$map.png"
	kill "$gpid" 2>/dev/null
	wait "$gpid" 2>/dev/null || true
	gpid=
	ffmpeg -nostdin -loglevel error -y -i "$work/$map.png" -vf scale=480:240:flags=lanczos -pix_fmt rgb24 -compression_level 9 -pred mixed "$out/$map.png"
	echo "$map $cam $(stat -c%s "$out/$map.png")"
done <<<"$views"
