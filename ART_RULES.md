# Map art rules

User overrides: no cast shadows (user rejected them), no reflections, sun around 45-55 degrees so turned-away faces stay readable, maps 500 m, everything modelled in Blender, more beautiful and dazzling than reference games.

## Palette and value
- Value before hue; large surfaces close in value; strongest contrast only at focal and gameplay spots.
- Three tones per material in vertex colours: base, lighter top/edge, darker base/crevice. One flat colour per object is the main childish tell.
- Saturation: walls and ground 15-35%, props a bit higher, one accent 50-60% per area.
- Life comes from warm light vs cool shade and value contrast, not saturation. Never pure white, pure black or primaries.
- One distinct coloured landmark object per area.
- Desert: sand C8B48C/A8916A, rock 8E6E55/5E4A3E, scrub 7A7A55, horizon E3D9C6, sky 9FB3C0, accent A8432F
- Tropical: dry sand D6CBAA, wet sand A99C7E, grass 6F8A4E, foliage 3F5A3A, rock 6E6A62, shallows 5E9A94, deep 2F5E68, accent C27C3A
- Valley: grass 6B7F4F, dry grass 9A9468, rock 7A7A74/4F5154, conifer 3A4A3C, snow DCDDDA, haze A9B6BD, accent 8C3B2E
- Military: concrete 9A978E/6C6A64, asphalt 4A4A48, olive 5D6146, sandbag 9C8F6C, gunmetal 6A7275, hazard C9A23A (small)
- Industrial: floor 6E6D69, wall 8A8C88, steel 5A6166, rust 7D5440, machinery 4F6B6E, hazard C5A23C, lamp E8D9B5, shadow 2E3236

## Lighting
- Warm key light, cool gradient sky ambient with warm ground bounce, never black.
- AO baked into vertex colours in Blender (darker in creases, where props meet ground, under overhangs). This replaces shadows for depth.
- Fog colour = horizon colour; distance layers lighter and bluer; low height fog in valleys.
- Grade: slight desaturation, warm highlights, cool shade.

## Geometry
- Chamfer every hard edge: 2-5 cm props, 5-10 cm walls.
- Slight irregularity; nothing perfectly straight; vary rotation and scale.
- Even triangle density across assets; spend polygons on silhouettes.
- Real sizes: player 1.8 m, doors 2.1-2.3 x 1.1-1.4 m with 10-20 cm frames, walls 20 cm thick, 3-4 m per storey, stairs 15-20 cm rise 30 cm run.
- Trims and modular pieces; no paper-thin walls.

## Detail and density
- Big anchor + 2-3 medium + small scatter per cluster; a cluster every 8-15 m along paths; a ground break every 2-4 m; calm areas between busy ones.
- Props tell a story; fine detail above head height or outside lanes.
- One tall landmark per zone, visible from afar; add life: flags, birds, smoke, swaying grass.

## Terrain
- Cliffs, mesas and mountains are modelled Blender meshes, not heightmap noise.
- Playable ground smooth with large gentle facets; detail at edges with rock pieces covering ground-wall seams.
- Colour by slope and height; darken where ground meets walls and rocks; distant silhouettes in lighter bluer layers.

## Never
Saturated primaries, one flat colour per object, unbevelled boxes, paper-thin walls, even spreads with dead space, noisy faceted terrain.

## Blockfield lessons (researched 2026-11-25)
- One strong theme per map, 3-5 hue palette chosen first; saturated blue sky against warm ground.
- Face value jitter of 5-8% plus darker vertex AO at wall bases and crevices instead of textures.
- Dark soft blob decals under props and vehicles to ground them (we have no cast shadows).
- A 15 m+ landmark per zone, visible from spawn.
- Props clustered at cover points, 5-15 per node, with clear lanes between.
- A silhouette-rich backdrop ring to close sightlines.
- One gameplay accent colour per map (awnings, doors, containers) to mark routes.
- Cheap motion: dust, leaves, snow particles, swaying foliage, scrolling water.
- Emissive vertex colour for windows, screens, neon on interiors.
- 2-3 heights per zone: rooftops, balconies, stairs, ramps.
- Structure 500 m maps as linked 60-100 m arena pockets, each a sub-theme, joined by corridors; Blockfield density only holds at arena scale.
