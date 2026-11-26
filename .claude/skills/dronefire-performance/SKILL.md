---
name: dronefire-performance
description: >
  Performance rules, budgets and measuring workflow for Dronefire (Zig 0.17 + raylib 6, Linux and
  Android GLES 3). Use before adding or changing anything that runs per frame or adds content:
  rendering, shaders, maps, props, vehicles, bots, effects, physics, UI, networking. Also use for
  low FPS, stutter, high RAM or when profiling on the Android tablet.
---

# Dronefire performance

raylib is a thin OpenGL wrapper, not an engine. It does no culling, no batching and no LOD, and
several of its convenience calls are slow on phones. Everything that keeps the game fast lives
in our code, so every new system has to be designed for it from the start.

## Budgets

- **Frame rate:** the device's full refresh rate, never "60 is fine". The test tablet is 120 Hz,
  so 8.3 ms per frame. Keep CPU and GPU each under about 7 ms for thermal headroom.
- **RAM:** under 300 MB PSS on Android (`dumpsys meminfo`). GL textures count.
- **Per map:**
  - props directory 6 MB or less
  - about 150k triangles or fewer
  - about 60 prop kinds or fewer
- **Draw calls:** a few hundred per frame on mobile.
- **Never meet a budget by making the game look worse:**
  - no Low mode
  - no hardcoded resolution caps
  - no shadows, reflections or post effects added back

## Pre-implementation checklist

Answer each item in your plan before writing code for a new rendering or gameplay system. Say
"n/a" when it doesn't apply, never skip silently.

1. **Scaling.** What runs every frame, and how does its cost grow with bots, props, vehicles or
   map size? Nothing may loop over all of `world.pieces`, `world.placements` or all props per
   entity. Use `shared.grid` (`grid.rect`, `grid.ray`) for spatial queries.
2. **Visibility.** Is it culled?
   - frustum: `gfx.sphereVisible`
   - occlusion: `pvs.visible`
   - distance: a per-group reach
   - detail by distance (LOD)
   Anything drawn needs all applicable ones.
3. **GPU residency.** Is static data uploaded once? Never re-upload per frame what doesn't
   change. Use `gfx.uploadStatic` and `drawStaticRange`, not `rl.DrawMeshInstanced` (it creates
   and deletes a VBO every call).
4. **Draw calls.** How many does it add per frame? Merge meshes that share a material
   (`mesh.mergeFlat`), instance repeated meshes, and avoid models split into many small meshes.
5. **Shader cost.** Per-pixel loops, procedural noise, extra texture taps, full-screen passes.
   Bake to a texture when possible (the sky clouds are a baked texture). Never `discard` in
   opaque shaders (it breaks Adreno LRZ).
6. **CPU animation.** Skinning stays on the GPU (`Renderer.enableSkinning`, the `skinned`
   uniform). `rl.UpdateModelAnimation*` without a bone-aware material shader falls back to CPU
   skinning and re-uploads the mesh every frame.
7. **Per-frame allocation and lookups.** No allocations in the frame loop. Cache
   `GetShaderLocation` results; they are string lookups.
8. **Memory.**
   - texture size and format; prefer compressed on Android
   - drop CPU copies after upload (`mesh.dropCpu`)
   - no per-map duplicates
9. **Android.** GLES 3 shaders. Touch arrives as mouse input, and `EnableCursor()` or
   `DisableCursor()` re-centre the mouse on Android, so never call them every frame. Assets must
   be packed in the APK list in `build.zig`.
10. **Measure.** Record numbers on the tablet before and after (see Measuring). Report the
    numbers in the reply. A change that drops FPS is a bug.

## Systems that already exist (use them, don't reinvent)

| Need | Use |
|---|---|
| Collision or ray queries against the world | `shared.grid` via `movement.*` and `vehicle.*` (8 m spatial hash, built lazily) |
| Frustum test | `gfx.sphereVisible(center, radius)`, set up in `Renderer.begin` |
| Occlusion test | `pvs.visible(eye, center, radius)`, a precomputed per-map visibility table |
| Static prop drawing | `propart` slots, 32 m cells, a static instance VBO, culled ranges merged into one draw |
| Vehicles | `vehicleart`: merged flat parts, distance LOD for wheels and calipers |
| Frame timing breakdown | `frameStats` in `main.zig` logs "frame fps / cpu / sim / scene / swap" and "parts" to logcat every 2 s |
| GPU frame time | `gputime.zig` (EXT_disjoint_timer_query) logs "gpu scene" every 2 s. On a tile GPU only the frame total is meaningful, not the split between passes |
| A/B one part at runtime | `adb shell setprop debug.df.skip <bits>` turns off scene parts with no rebuild: 1 sky, 2 chunks, 4 props, 8 cover, 16 world, 32 soldiers, 64 viewmodel, 128 HUD, 256 backdrop, 512 final copy. Compare against a baseline in the same session, because the device heats up |
| Prop LOD | `tools/lod.sh [props dir]` writes `<name>.lod.glb` at 25% of the triangles with Blender decimate. `propart` uses it once a model is under 100 px on screen, and skips models under 5 px entirely. Rerun it after re-exporting a map kit |

### Visibility files (PVS) must be regenerated after map changes

`src/client/assets/pvs/<map>.bin` stores a hash of the map's collision pieces. When the hash
doesn't match, the file is ignored and occlusion culling silently turns off for that map. After
editing any map, run:

```
zig build -Drelease && tools/pvs.sh
```

Commit the new `.bin` files with the map change.

## Measuring

Desktop shots on Xvfb use software rendering. Use them for correctness only, never for speed.

- **Tablet:** `adb connect <ip:port>` (wireless debugging; pairing codes come from the user).
- **Build and install:**
  - `zig build -Dandroid -Drelease` (add `-Dkeep-symbols` for profiling)
  - then `adb install -r zig-out/dronefire.apk`
- **Frame breakdown:**
  ```
  adb logcat -c; <play a match>
  adb logcat -d | grep -E "frame fps|parts"
  ```
  - `cpu` is the main-thread time until the end of drawing.
  - `swap` is the wait in `EndDrawing`, GPU time plus vsync wait.
  - With vsync on, frame rates quantise to the display. Treat it as GPU-bound when swap stays
    high with low CPU, and confirm with lower render scale.
- **CPU hotspots:**
  ```
  adb shell simpleperf record --app com.dronefire.game --duration 8 -o /data/local/tmp/perf.data
  adb shell simpleperf report -i /data/local/tmp/perf.data --sort dso,symbol --percent-limit 0.7
  ```
  The manifest has `<profileable android:shell="true"/>`.
- **Memory:** `adb shell dumpsys meminfo $(adb shell pidof com.dronefire.game)`. Look at TOTAL PSS
  and GL mtrack.
- **Thermal:** compare the first and fifteenth minute of play before calling something fast.

Fixes found this way so far:
- brute-force collision (4.6 ms to 0.2 ms)
- CPU skinning (7.7 ms to 1.5 ms)
- a VBO created per instanced draw
- full-screen fbm sky noise
- no frustum culling

Together they took the tablet from 45 to about 66 FPS.

## Lessons from measuring

- **Draw order matters on a tile GPU.** The full-screen sky and the backdrop disc drawn first cost 1.1 ms and 2.2 ms. Opaque geometry goes first, roughly nearest first; sky and backdrop come last with depth testing (the sky sits at the far plane through `gl_Position = p.xyww`).
- **Fragment precision.** The lit shaders run mediump on GLES (`fastShader`). Anything derived from world position, such as texture coordinates or distances used for UVs, must be `highp`, or it shows as blocky ground. The sky needs highp.
- **Ground items.** Dropped weapons and pickups were drawn with no culling at all, costing over 2 ms of CPU.
- **Bounding boxes after `dropCpu`.** `GetModelBoundingBox` returns zero once CPU vertices are freed. Measure before dropping.
- **raylib GLES bone matrices.** `rlSetUniformMatrices` doesn't transpose on GLES, which twists skinned meshes. Upload with `glUniformMatrix4fv` and `flatMatrix`.
- **Thermals.** The tablet reaches 80 °C or more after repeated runs, and GPU time grows 20 to 30%. Compare A/B results inside one session.

## Open items

- `discard` in the shared lit shader: measured, removing it gained nothing on Adreno 650 (81 vs 82 FPS), so it stays.
- Textures are uncompressed, about 300 MB GL. Move to ETC2 or ASTC.
- Batching: merge static props per cell into fewer draws.
- The post-processing MSAA path resolves through a blit (anti-pattern). Fix it before enabling.

See also: `gles-mobile-gpu` (tile GPU rules) and `performance-optimization` (general method).
