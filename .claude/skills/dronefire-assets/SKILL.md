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

## Lessons from studying good stylized assets

Polyfork kits, measured with `tools/blender/study/analyze.py`, and POLYGON Military screenshots:
- **Whole buildings are cheap:** 800 to 2,900 tris (family house 1,027, corner shop 2,887). Richness
  comes from colour and silhouette, not part count. My first outpost was 7,092 and looked plainer.
- **8 to 22 colours per asset,** not 3 to 5. Bright trim against a darker wall, navy glass,
  accent colours (striped awnings, painted doors).
- **Bevel everything, once:** 40 to 60% of their triangles are thin single-segment chamfer strips.
- **Cheap richness tricks:** a few protruding bricks scattered on walls, keystones on lintels,
  cornice brackets, alternating face colours for stripes, dormers.
- **POLYGON-level density comes from clutter:** rooftop AC units, water tanks, dishes, antennas,
  laundry lines, cables between buildings, awnings, balconies, external stairs, parapets with
  coping, deep window recesses. Grime and wear are colour (darker faces low down and in corners).
- **Props and weapons are blocky, simplified silhouettes** with exact proportions: an AK is about
  15 to 25 tapered, chamfered prisms; small props are 100 to 600 tris with 2 to 3 colours. A scene
  looks rich from quantity and variety, not from per-prop detail.
- **Pressed or embossed surfaces** (jerry can X): model the raised panels as extruded outlines;
  thin bars for grooves read as wire.

## Art direction: Synty POLYGON (project standard, required for every asset)

Battle's visual target is the shared DNA of Synty's POLYGON packs, not any one pack. Every
building, vehicle, prop, road and nature asset follows it. A box with flat colours is not done.

**Shape**
- Chunky, deliberate geometry with slightly exaggerated proportions: thick walls (0.35 to 0.45 m),
  deep reveals, oversized trim, beams, sills and lintels.
- Silhouette first: every building gets a feature that breaks the box (arcade, balcony, outdoor
  stair, roof room, beam ends, awning, tank).
- Hand-made, not machine-perfect: `k.jitter` on walls, parapets and slabs (2 to 3 cm), soft rounded
  parapets (`k.chamfer(ob, 0.09, 30, 2)`). Never jitter big concave caps (arcades, stairs); they streak.
- Openings are deep, dark holes (`void` inside), with frames set back and lintels proud.
- Small details are geometry: planks, slats, bricks, spindles, beam ends. One box each, consistent size.

**Colour**
- One main material hue at three values (body, a darker step for ledges, bases and insides, a
  lighter step for caps). Trim is a value step of the same hue, never a second near-white.
- One accent hue, roughly opposite the main hue (teal against terracotta), used sparingly:
  shutters, cloth, a door.
- Keep plaster and paint dusty: about 25 to 35% saturation (Synty measured: tan 216,185,162).
  43% read as salmon pink in the game. Check colours in the game, not in the Workbench preview.
- Wood dark and warm, metal neutral, voids near black. No pure white, no pure black on surfaces.
- Wear: brick patches in the wall's dark step with a few bricks, plus base grime and baked AO.

**Quality check before an asset is done**
1. Silhouette reads at 30 m in the game (screenshot with `DF_ASSET`, `DF_ASSET_DIST`, `DF_ASSET_YAW`).
2. Palette: body, dark step, light step, one accent, wood. Nothing else fighting.
3. Studio render (`tools/blender/studio.py <recipe> <out.png>`: sun, dark background, colours shown as in game) next to the reference sheets in
   `~/gamess/design`. Would it sit in a Synty layout sheet without standing out?
4. Every face has a reason; no flat wall wider than about 3 m without an opening, beam or patch.
5. Triangle budget and on-device FPS as in the performance skill.

Reference build: `tools/blender/assets/adobe_house.py`.

## What POLYGON packs really are (157 marketing images studied, Nov 2026)

Military, War, Sci-Fi Space, Sci-Fi City, Nature and Farm packs:
- **The geometry is low poly** (props hundreds of tris, buildings and vehicles a few thousand),
  but the screenshots owe much of their look to the engine: real-time shadows, ambient occlusion,
  bloom, colour grading, depth of field, fog, emissive neon and particles. Dronefire has none of
  those by rule, so match the models, and get the occlusion look by **baking AO into vertex
  colours** (darken corners, undersides and contact faces once in Blender; zero runtime cost).
- **One shared gradient colour atlas** for everything, plus real textures only for signs, posters,
  decals and markings (numbers, stars, stencils).
- **Nature is not pure low poly:** foliage uses alpha-textured cards and the terrain is
  hand-painted. Flat faceted trees and rocks are the Farm-pack style and fit our pipeline.
- **Modular kits:** wall, floor, roof and trim pieces on a grid; weapons split into parts (receiver,
  barrel, stock, magazine, sight) that recombine into many guns; vehicles in variants (camo, rust).
- **Density sells it:** layout sheets show hundreds of props per pack, and scenes are packed with
  clutter on every surface.
- **Palette per pack:** Military is desert sand and khaki with saturated accents (awnings, rugs,
  water tanks); Farm is warm and saturated (red barns, yellow crops); Sci-Fi is dark metal with
  neon emissive strips. Pick one per map and keep every asset in it.
- **Weapons:** chunky prisms with exact silhouettes, wood against gunmetal; small details (bolt,
  sights, rails) as single boxes.
- **Vehicles:** boxy hulls with bevels, separate wheels, markings as decals.
- **Characters, animate beings, religious buildings and hate symbols in these packs are out of
  scope** for Dronefire.

## Side-by-side with POLYGON Military buildings (Nov 2026)

Our outpost v2 against their layout sheets: their buildings have fewer parts than ours, and still
look better. The gap is surface, shape and light, not part count:
- **Wear:** chipped plaster showing brick, cracks, stains and speckle, painted into the texture.
  Our flat vertex colours look brand new and plastic. Fix: a small shared wear atlas (UV-mapped
  patches) or wear geometry (chipped corners, broken plaster plates, brick clusters set into
  recesses), not flat stickers.
- **Hand-made shapes:** edges slightly soft and uneven, parapets rounded, nothing perfectly
  straight. Our boxes are machine-perfect. Fix: jitter vertices a few cm, round the parapet tops.
- **Deep dark openings:** windows and doors are deep holes into dark interiors, often with no
  glass. Our glass sits nearly flush and reads flat.
- **Local character:** beam ends sticking out under the roof line, outside stairs built into the
  mass, arcades. Our corner stones and cornice read European, not desert.
- **Light:** their shadows and AO do half the work. Without shadows in the game, the depth
  has to come from deeper geometry and darker baked recesses.

## Measured reference comparison (how to do it right)

```
k.preview([ob], "x.png", views=("elevation",), res=960, ortho=True, transparent=True)
~/.cache/battle/venv/bin/python .claude/skills/blender-image-to-3d/scripts/compose_review.py \
    --ref ref.png --render x_elevation.png --out cmp.png --measure
```
- **The camera must match the reference.** An elevation drawing needs a level orthographic
  `elevation` view. My tilted `front` view made the house look 25% too narrow.
- **The render needs a real alpha channel** (`transparent=True` saves RGBA), or the whole frame
  counts as the object and the score is meaningless (I got 0.41 from that bug).
- **Crop the reference to the object:** ground lines, labels and frames count as silhouette.
- **Read the band widths, not just the score:** they say where the error is (roof bands narrow,
  walls fine), and that tells you which constant to change.
- **Chimneys and other parts that sit on a sloped roof** must start from the slope's height at
  their position. Placing them at the ridge end made them float.
- **A slab added "around" a window covered the glass.** Surrounds are frames (4 strips), never a
  solid plate in front.

## Reference examples

| Recipe | Result |
|---|---|
| `tools/blender/assets/outpost.py` | 2-storey outpost: plinth, shuttered windows, door with canopy and steps, pilasters, floor band, cornice, seamed gable roof, chimney, AC units, downpipes. 7,092 tris, 9.2 × 7.6 × 9.7 m |
| `tools/blender/assets/jerrycan.py` | WWII jerry can rebuilt from a real photo (Wikimedia): rounded body, pressed X panels, seam, 3 handles, spout with lever cap. 892 tris, 0.35 × 0.19 × 0.54 m. Three passes |
| `tools/blender/assets/rowhouse.py` | two-storey house from an architectural elevation (Wikimedia): hip roof, chimneys on the hips, 16 framed windows with pediments, pilasters, quoins, diamond panels. Outline overlap 0.73 after 5 passes (target 0.85 not reached: missing side wing, stepped chimney bases, carved ornament). 4,452 tris |
| `tools/blender/assets/supplies.py` | supply crate (612 tris, 1.19 × 0.83 × 0.75 m) and fuel drum (488 tris, Ø 0.62 × 0.9 m) |

Related skills: `blender-lpm` (builders and low-poly rules), `blender-hardsurface-modeling`
(bevels, segment budgets), `blender-game-optimization`, `blender-asset-qa` (mesh checks),
`blender-environment-kits` (modular grid rules), `blender-image-to-3d` (reference
reconstruction), `blender-core` (Blender API rules).
