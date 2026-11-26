---
name: dronefire-assets
description: >
  Make new 3D game assets for Dronefire in Blender with the project's own toolkit: buildings,
  windows, doors, roofs, stairs, railings, crates, barrels, military and environment props,
  weapons and vehicles. Covers art direction, polygon budgets, the reference-image loop, export
  to GLB with vertex colours, LODs, and verifying the asset inside the actual game. Use whenever
  the user asks for a new model, prop, building, weapon, vehicle or asks to rebuild one from a
  reference image. No animate beings.
---

# Dronefire asset production

Assets are code. Every asset is a Python recipe under `tools/blender/assets/` that rebuilds it
from scratch with `tools/blender/kit/dfkit.py`. Never hand-edit a GLB; edit the recipe and
rerun it.

## Run

Blender must run with a clean environment, or its Python can't find its standard library:

```
env PATH=/usr/bin:/bin OUT=<dir> blender -b --factory-startup --python tools/blender/assets/<asset>.py
```

Each recipe prints `STATS` (tris, metres, budget), writes `<name>.glb` and a 4-view contact
sheet `<name>_sheet.png`.

## Toolkit (`tools/blender/kit/dfkit.py`)

It is built on the LPM builders (`.claude/skills/blender-lpm/scripts/lpm.py`), with Dronefire's
export added.

| Call | Makes |
|---|---|
| `box`, `beveled_box`, `prism`, `lathe`, `sweep`, `plate` | primitives (metres, Z up, front is -Y, `at` is base centre) |
| `chamfer(ob, width)` | bevels hard edges once (the POLYGON look). `beveled_box` skips parts under 12 cm, where it is invisible and costs triangles |
| `wall(name, w, h, t, at, openings=[(x, z, w, h)])` | wall split into piers and lintels around openings, no booleans |
| `window(...)`, `door(...)` | frame, sill, lintel, glass, mullions, optional shutters, door panels, knob, step |
| `gable_roof(...)` | one extruded roof section with standing seams, ridge cap, gable ends and fascia |
| `pilaster`, `stairs`, `railing`, `_bar(a, b, r)` | architectural pieces and pipes or braces between two points |
| `crate`, `barrel` | props with trim, brackets, bands |
| `move`, `rotate`, `scale`, `taper`, `mirror_x`, `paint` | deformers on a part before `finish` |
| `finish(name, parts, budget)` | joins, grounds, centres, writes palette colours to the `Col` vertex colours, flat shading, one white material |
| `export(ob, path)` | GLB matching the map pipeline (`pf.py`): vertex colours, no texture coordinates, Y up |
| `preview([ob], png)` | Workbench vertex-colour renders, 4 views in one sheet |
| `c("plaster")` | palette index. Add colours to `PALETTE`, never inline hex in recipes |

Colours are sRGB values stored straight into `Col`, the same as `pf.py`. The game multiplies the
vertex colour by sun shading, so pick palette colours a little darker than the target look.

## Art direction

Benchmark: POLYGON-style stylised low-to-mid poly (Synty POLYGON Military).
- **Shapes over texture:** detail is geometry (frames, sills, trim, panels, brackets, bands). No
  textures, so no texture memory.
- **Chamfered edges** on every large shape catch the light. A plain sharp box reads as 2000s.
- **Layering:** base plinth, wall, floor band, cornice, roof trim. Every face that is a big flat
  plane needs a break (band, pilaster, panel line, downpipe).
- **Controlled palette:** 3 to 5 colours per asset from `PALETTE`. Separate neighbouring parts by
  value (wood next to steel, plaster next to trim).
- **Real scale:** door 2.3 m, storey about 3.2 m, window 1.2 to 1.5 m, crate about 1 m, drum 0.9 m.
- **No animate beings,** statues of beings, religious buildings or symbols, or faces.

## Budgets (triangles, before LOD)

| Asset | Target | Hard cap |
|---|---|---|
| Small prop (crate, drum, cone, sign) | 300 to 800 | 1,000 |
| Medium prop (generator, barrier, tent) | 800 to 2,500 | 3,000 |
| Building, small or medium | 3,000 to 6,000 | 8,000 |
| Landmark building | 6,000 to 12,000 | 15,000 |
| Weapon (first person) | 2,000 to 5,000 | 6,000 |
| Vehicle | 5,000 to 12,000 | 15,000 |

Then run `tools/lod.sh <props dir>` for the 25% LOD. Many instances of one prop matter more than
one big asset: a 600-triangle crate placed 200 times is 120,000 triangles. Check the map's total
with `DF_TRIS=1` (see `dronefire-performance`).

## Workflow for a new asset

1. **Brief:** what it is, real size in metres, budget class, 3 to 5 palette colours, where it's
   seen from (eye level, distance).
2. **Part list:** decompose into components from the toolkit. Add a reusable builder to
   `dfkit.py` if the part will recur (a new window type, a hip roof), never one-off geometry in
   the toolkit.
3. **Recipe:** `tools/blender/assets/<asset>.py`, then run it.
4. **Look at the sheet,** every view, not just the flattering one. Typical faults: floating or
   rotated parts, parts poking through, gaps at joins, z-fighting coplanar faces, wrong scale.
   Fix and rerun. Three passes are normal.
5. **Numbers:** tris against budget, dimensions against the brief.
6. **In game:** `DF_ASSET=a.glb,b.glb tools/shot.sh <map> out.jpg` places the files in front of
   the player with the game's renderer. Check scale against cars and doors, colours under the sun
   shading, and that nothing looks flat or washed out.
7. **Into a map:** use the GLB path as a source in `tools/blender/maps/<map>.py`
   (`make_building`/`make_prop` accept absolute paths), run `tools/mapkit.sh <map>`, then
   `tools/lod.sh` and `tools/pvs.sh`.

## From a reference image

Use `blender-image-to-3d` (gated phases, silhouette overlap against the reference from a
matched camera) or `blender-lpm` `references/reference-to-lowpoly.md` (audit table: parts to
builders, proportions as ratios). Image scripts need Pillow: run them with
`~/.cache/battle/venv/bin/python`. Never use the paid turnaround or image-to-mesh services. The
loop is: silhouette and proportions first, then parts, then detail; compare against the
reference from the same angle at gameplay pixel size; write mismatches as numbers ("roof 15%
too low") and fix them in the recipe.

## Mistakes already made (don't repeat)

- **Rotating separate roof slabs** about an axis put them in a V above the house. Build roofs as
  one extruded cross-section (`sweep`) and rotate the whole thing once.
- **Rotation signs:** `rotate(p, 90, "Y")` turns +Z into +X. Check direction before moving a part
  along the new axis.
- **Chamfering everything** took a building from 7,000 to 11,800 triangles with no visible gain.
- **Blender 5.0 API:** `mesh.uv_layers.clear()` doesn't exist; remove the layers one by one.
- **Running Blender from the agent shell** without `env PATH=/usr/bin:/bin` breaks its Python
  (`No module named 'math'`).
- **The model viewer (`DF_VIEW`)** uses raylib's default shader, not the game's lighting. Verify
  with `DF_ASSET` instead.

## Reference examples

| Recipe | Result |
|---|---|
| `tools/blender/assets/outpost.py` | 2-storey outpost: plinth, shuttered windows, door with canopy and steps, pilasters, floor band, cornice, seamed gable roof, chimney, AC units, downpipes. 7,092 tris, 9.2 × 7.6 × 9.7 m |
| `tools/blender/assets/supplies.py` | supply crate (612 tris, 1.19 × 0.83 × 0.75 m) and fuel drum (488 tris, Ø 0.62 × 0.9 m) |

Related skills: `blender-lpm` (builders and low-poly rules), `blender-hardsurface-modeling`
(bevels, segment budgets), `blender-game-optimization`, `blender-asset-qa` (mesh checks),
`blender-environment-kits` (modular grid rules), `blender-image-to-3d` (reference
reconstruction), `blender-core` (Blender API rules).
