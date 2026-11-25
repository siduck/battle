# Materials

Files: src/client/assets/textures/mat0..mat4.png (1024 px, 4 greyscale detail maps per RGBA image, mipmapped, trilinear, repeat).
They are luminance only, centred on mid grey, low contrast, so they multiply over vertex colours and never change a palette hue.
Shader: lit_fs, functions matTap(id, uv), matTri(id, worldPos, normal, scale) (world-space triplanar), matF(v) = 0.62 + v * 0.76.
Fade: full detail up to 35 m, gone by 70 m. Desktop only; off on Android and on Prism. DF_NOMAT=1 disables it for A/B tests.

## IDs
0 plaster, 1 plaster2, 2 adobe, 3 brick, 4 stonewall, 5 paving, 6 cobble, 7 roof tiles, 8 wood planks, 9 painted wood,
10 metal plates, 11 corrugated metal, 12 concrete, 13 asphalt, 14 sand, 15 grass, 16 dirt, 17 rock, 18 snow, 19 thatch

## Where they apply
- Terrain (detail mode 1): grass 15, sand 14, dirt 16, grey ground 12, steep slopes 17, picked from the face colour and slope.
- Facility panels (detail mode 2): floors 12, walls auto.
- Instanced props (detail mode 4, the Blender kits): auto by colour unless a matId is set:
  green -> none, grey light -> 12, grey dark -> 10, terracotta red -> 7 on top faces else 3, dark brown -> 8, blue/teal -> 9, other warm -> 0 on top faces else 1.

## Assigning a material to a kit piece
Before drawing a batch: r.setMatId(id) (float id, -1 = auto), and r.setMatId(-1) after. Use it per prop kind in propart.draw, e.g. paving slabs 5, cobbles 6, adobe walls 2, roof tiles 7, thatch 19.
Credits: src/client/assets/textures/CREDITS.txt (ambientCG, CC0).

## Per-kit materials (propart.zig kit_mats)
r.setMatId takes side * 32 + top (one material for vertical faces, one for upward faces); green parts stay untextured. Kits matched by name prefix in kit_mats, e.g. iv_hut planks/thatch, iv_compound adobe, iv_ruin stone wall, cliffs and ridges rock, mil_container corrugated, mil_bunker concrete, metal machinery metal plates. Unlisted kinds (including dk_ desert kits) use auto.
Large-scale wear (matWear in the shader) adds low-frequency stains and patches on top.
