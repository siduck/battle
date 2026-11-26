---
name: gles-mobile-gpu
description: >
  Tile-based mobile GPU rules (Qualcomm Adreno, ARM Mali, PowerVR) for OpenGL ES 3 rendering:
  GMEM loads and stores, LRZ early-Z, on-tile MSAA, frame pacing on 90-144 Hz panels, GPU culling,
  texture streaming and LOD, Snapdragon Profiler counters. Use when changing shaders, render
  targets, MSAA, clears, draw order or texture formats in Dronefire's Android build, or when the
  game is GPU-bound on a phone.
---

# Mobile GPU (GLES 3, tile-based)

A trimmed vendor copy of the MIT-licensed `oahc09/gles-rendering-expert-skill` (see LICENSE). Only
the files relevant to Dronefire are kept. The original's C++ RAII, ANGLE, video and benchmark
material is left out because this game is Zig on raylib.

Dronefire's Android build runs raylib on OpenGL ES 3. The test device is a Xiaomi Pad 6 (Adreno
650, 120 Hz). Every rule here is about not wasting tile memory bandwidth or fragment work.

## Golden rules

1. Clear or invalidate every attachment at the start of a render pass. A partial or scissored clear
   forces a GMEM load.
2. Invalidate depth and stencil at the end of a pass when nothing reads them later.
3. Resolve MSAA on-tile (`EXT_multisampled_render_to_texture`), never through a multisample
   buffer followed by `glBlitFramebuffer`.
4. Keep LRZ alive: draw opaque geometry roughly front to back, with no `discard` and no
   `gl_FragDepth` in opaque shaders. Draw alpha-tested and transparent geometry afterwards.
5. Prefer fewer fragments over cheaper fragments. Use dynamic resolution only when the frame is
   GPU-bound, and never as a fixed cap.
6. Prove every change on the device. The emulator and the desktop GPU say nothing about tile
   bandwidth.

## Known issues in this codebase

- The lit shaders in `src/client/gfx.zig` (`lit_fs_body`, the depth shader) `discard` below
  alpha 0.45 for every draw, opaque ones included. That disables LRZ for the whole scene. Split
  them into an opaque variant without `discard` and an alpha-cutout variant for foliage and
  fences.
- `Post.loadMultisample` in `gfx.zig` builds an RGBA16F multisample renderbuffer and resolves it
  with `glBlitFramebuffer`. That is the anti-pattern in rule 3. The post path is currently off;
  fix this before turning MSAA or post effects back on for Android.
- Textures are uploaded uncompressed (RGB8 and RGBA8), so about 300 MB of GL memory on the
  tablet. ETC2 (core in GLES 3) or ASTC would cut that by 4 to 8 times. See
  `references/rules/texture-streaming-lod.md`.

## Load on demand

| Task | File |
|---|---|
| Clears, render targets, bandwidth | `references/rules/adreno/gmem-load-store.md` |
| Overdraw, draw order, `discard`, depth formats | `references/rules/adreno/lrz-and-flexrender.md` |
| Anti-aliasing on Android | `references/rules/adreno/efficient-msaa.md` |
| Overview and vocabulary | `references/rules/adreno/README.md` (it links to two files not kept here: VRS and frame extrapolation) |
| Stutter, 120 Hz cadence, swap interval | `references/rules/frame-pacing.md` |
| GPU-side culling, occlusion queries | `references/rules/gpu-culling.md` |
| Texture memory, mips, compression | `references/rules/texture-streaming-lod.md` |
| Which profiler and which counters | `references/rules/profiling-tools.md` |

Load only the file the task needs.
