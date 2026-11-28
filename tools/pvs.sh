#!/usr/bin/env bash
set -eu

prefix=${1:-zig-out}
out=src/client/assets/pvs
maps=(desert islands airport alpine coast construction japan forest nyc racing lab stadium)

for map in "${maps[@]}"; do
    DF_MAP="$map" DF_MUTE=1 DF_PVSGEN="$out" "$prefix/bin/dronefire"
done
