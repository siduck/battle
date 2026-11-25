# Map palettes

Target: Valorant-style eye candy. Warm sun, cool tinted shade, rich mids, vivid but not neon, no beige on beige. Values are linear multipliers used in `src/client/main.zig` (sun is scaled by the HDR sky's average). Shadows: soft 2-cascade, shade = 0.42 of sun, tinted by `shade_tint`; Prism and the Facility hangar are excluded.

| Map | Sun dir | Sun colour | Ambient sky | Ambient ground | Shade tint | Sky zenith | Fog | Grade tint | Grade sat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Desert | 0.55, 0.64, 0.53 | 1.18, 0.98, 0.78 (#FFE0B8) | 0.95, 1.00, 1.18 | 0.88, 0.70, 0.52 | 0.90, 0.92, 1.05 | #0D3394 | #D1D1D1 | 1.05, 1.00, 0.92 | 1.18 |
| Valley | -0.60, 0.64, 0.47 | 1.20, 1.00, 0.78 | 0.90, 0.98, 1.18 | 0.74, 0.70, 0.52 | 0.90, 0.93, 1.05 | #0D3D9E | #A8BDD1 | 1.04, 1.00, 0.94 | 1.12 |
| Islands | 0.58, 0.65, -0.49 | 1.15, 1.02, 0.86 | 0.92, 1.00, 1.18 | 0.76, 0.74, 0.58 | 0.90, 0.94, 1.05 | #0A42A8 | #A8D1F5 | 1.03, 1.00, 0.96 | 1.14 |
| Conquest | 0.55, 0.62, 0.56 | 1.22, 0.98, 0.74 | 0.92, 0.98, 1.15 | 0.82, 0.70, 0.52 | 0.90, 0.92, 1.05 | #0F3894 | #CCCCC2 | 1.05, 1.00, 0.93 | 1.12 |
| Facility | 0.50, 0.66, 0.56 | 1.10, 1.02, 0.92 | 1.08, 1.06, 1.04 | 0.98, 0.90, 0.80 | 0.98, 0.98, 1.00 | #0F3D99 | #B8C7D6 | 1.03, 1.00, 0.96 | 1.10 |

Accent hues per map (for kits, from ART_RULES and the Valorant refs):
- Desert: terracotta #B5502F, teal #2F8C8A, saffron #D9A233
- Valley: barn red #8C3B2E, pine #3A4A3C, river teal #3FA6A0
- Islands: coral orange #E07A3A, lagoon #3FB5B0, flower pink #D96A9A
- Conquest: olive #5D6146, rust #A0522D, signal yellow #C9A23A
- Facility: hazard yellow #C5A23C, teal #4F8C8E, warm lamp #E8D9B5
