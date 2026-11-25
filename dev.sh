#!/bin/sh
cd "$(dirname "$0")" || exit 1

zig=~/.local/opt/zig-x86_64-linux-0.17.1/zig
stamp=.dev-stamp
game=

launch() {
	[ -n "$game" ] && kill "$game" 2>/dev/null
	./zig-out/bin/dronefire &
	game=$!
}

trap '[ -n "$game" ] && kill "$game" 2>/dev/null; rm -f "$stamp"; exit' INT TERM

"$zig" build -Drelease && launch
touch "$stamp"

while :; do
	sleep 1

	if [ -n "$(find src build.zig -newer "$stamp" -type f 2>/dev/null | head -1)" ]; then
		sleep 2
		touch "$stamp"

		if "$zig" build -Drelease 2>&1 | tail -20; [ "$(find zig-out/bin/dronefire -newer "$stamp" 2>/dev/null)" ] || "$zig" build -Drelease >/dev/null 2>&1; then
			launch
		fi
	elif [ -n "$game" ] && ! kill -0 "$game" 2>/dev/null; then
		launch
	fi
done
