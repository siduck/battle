#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
lib="$HOME/.cache/battle/libmeshopt.so"
src="$root/tools/meshlod/meshoptimizer"

if [ ! -f "$lib" ] || [ -n "$(find "$src" -newer "$lib" -name '*.cpp' | head -1)" ]; then
	mkdir -p "$(dirname "$lib")"
	(cd "$src" && zig c++ -shared -fPIC -O2 -std=c++11 -fno-exceptions -fno-rtti -o "$lib" ./*.cpp)
fi

dirs=("$@")
[ ${#dirs[@]} -gt 0 ] || dirs=("$root"/src/client/assets/props/*/)

for d in "${dirs[@]}"; do
	mapfile -t files < <(find "$d" -maxdepth 1 -name "*.glb" ! -name "*.lod*.glb" | sort)
	[ ${#files[@]} -gt 0 ] || continue
	MESHOPT_LIB="$lib" python3 -I "$root/tools/meshlod/meshlod.py" "${files[@]}"
done
