#!/usr/bin/env bash
set -eu

if [ $# -lt 1 ]; then
	echo "usage: tools/polyfork_fetch.sh <kit-slug> [dir]" >&2
	echo "kit slugs: curl -s https://api.github.com/repos/lucas-martinic/polyfork-catalog/contents/kits | grep -o '\"name\": \"[^\"]*\.md' | cut -d'\"' -f4" >&2
	exit 1
fi

kit=$1
dir=${2:-$HOME/.cache/polyfork/$kit}
base=https://raw.githubusercontent.com/lucas-martinic/polyfork-catalog/main

mkdir -p "$dir"

page=$(curl -fsSL "$base/kits/$kit.md")

curl -fsSL "$base/covers/$kit.jpg" -o "$dir/cover.jpg" || true

echo "$page" | grep -o '<td[^>]*>.*</td>' | sed 's/<\/td>/\n/g' | while read -r cell; do
	id=$(echo "$cell" | grep -o 'polyfork.dev/cdn/[^"]*\.glb' | head -n1 | sed 's|polyfork.dev/cdn/||; s|\.glb$||')
	name=$(echo "$cell" | grep -o 'alt="[^"]*"' | head -n1 | cut -d'"' -f2)

	[ -n "$id" ] || continue

	printf '%s\t%s\n' "$id" "$name"
done > "$dir/index.tsv"

while IFS=$'\t' read -r id name; do
	[ -s "$dir/$id.glb" ] && continue

	curl -fsSL "https://polyfork.dev/cdn/$id.glb" -o "$dir/$id.glb" || echo "failed $id" >&2
	curl -fsSL "https://polyfork.dev/files/$id/renders/hero.png" -o "$dir/$id.png" 2>/dev/null || true
done < "$dir/index.tsv"

echo "$dir"
wc -l < "$dir/index.tsv"
