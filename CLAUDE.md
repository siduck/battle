# Dronefire

Zig 0.17 + raylib 6 FPS for Linux and Android (GLES 3). The Android test device is a Xiaomi Pad 6
(Adreno 650, 120 Hz).

## Performance engineering (required)

Performance is a feature here, not a later pass. These rules are permanent:

- **Checklist first.** Before writing code that runs per frame or adds content (rendering,
  shaders, maps, props, vehicles, bots, effects, physics, UI, networking), load the
  `dronefire-performance` skill and answer its pre-implementation checklist in your plan. For
  shaders, render targets, MSAA, clears or textures on Android, also load `gles-mobile-gpu`.
- **Targets:**
  - the device's full refresh rate (8.3 ms at 120 Hz)
  - under 300 MB RAM on Android
  - per-map asset budgets as listed in the skill
- **Measure on the device.** After any change to rendering, maps or assets, measure on the
  tablet and report before and after numbers. A change that lowers FPS or raises memory is a
  bug, not a trade-off.
- **Never brute force.** No per-entity loops over all world pieces, props or placements. Use the
  spatial grid. Everything drawn is frustum-culled, occlusion-culled where possible, and
  distance-limited.
- **raylib does not optimise for you.** No culling, no batching. `DrawMeshInstanced` creates a
  VBO per call. `UpdateModelAnimation` can fall back to CPU skinning. Use the project's own paths
  listed in the skill.
- **Regenerate visibility after map changes:** run `tools/pvs.sh` and commit
  `src/client/assets/pvs/*.bin`.
- **Never trade looks for speed:**
  - no Low mode
  - no hardcoded resolution caps
  - lighting stays sun plus hemisphere fill, with no shadows, reflections or post effects

## Making assets

New buildings, props, weapons and vehicles are made with the project's own Blender toolkit, not
downloaded packs: load the `dronefire-assets` skill. Every asset is a recipe in
`tools/blender/assets/`, built from `tools/blender/kit/dfkit.py`, previewed, checked against its
triangle budget, and verified in the game with `DF_ASSET`.

## Other rules

- Test on hidden Xvfb displays only, never the user's display. Kill only processes you started.
- Map building rules live in `MAPS_HOWTO.md`.
