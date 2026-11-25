# First-person hands and arms

Rules for Dronefire's viewmodel arms. Web sources on exact proportions are thin (most results are asset listings and forum threads), so these rules combine what the sources say with how shipped shooters frame their hands (CoD MW, Valorant, CS2, Fortnite first person, Krunker, Poxel.io, Pixel Gun 3D, Bullet Echo).

## What the sources say

- The viewmodel is the hands holding the current weapon, drawn with its own narrow field of view (TF2 defaults to 54, max 70), separate from the world camera. Ours: `viewmodelProjection` in `gfx.zig`, 54 degrees. https://wiki.teamfortress.com/wiki/Viewmodel
- Engines render first-person meshes with a custom FOV and a scale factor so they sit close to the camera without clipping into walls. Thick forearms clip first, so keep them slim. https://dev.epicgames.com/documentation/unreal-engine/first-person-rendering
- Players move the hands toward the screen edge and lower so the weapon covers less of the view; CS2 exposes x/y/z offsets for this. Hands should never crowd the centre. https://cs.money/blog/esports/csgo-settings-viewmodel/
- Arm proportions by length: upper arm 5 units, forearm 4, hand 3. The forearm is wide across the front and narrow across the side when the palm faces in. https://clipstudio.net/how-to-draw/archives/164594
- Game-ready first-person arm packs keep the gloves as part of one continuous arm mesh (no separate floating hand), at roughly 1.7k (stylised) to 11k (realistic) triangles. https://www.cgtrader.com/3d-models/character/anatomy/first-person-hands-and-arms-with-gloves
- Stylised glove sets use padded knuckles, palm pads and a wrist strap as the readable details. https://www.cgtrader.com/3d-models/character/clothing/stylized-gloves-set
- Developers asking the same question settle on showing the wrist and a short piece of sleeve, not the elbow. https://devforum.roblox.com/t/how-should-the-viewmodel-looks-like/3236092

## Proportions (adult hand, glove adds about 2 mm per side)

- Hand length (wrist crease to middle fingertip): 19 cm. Palm length 10.5 cm, palm width 8.5 cm without the thumb, palm thickness 3 cm.
- Fingers: middle 9.5 cm, index and ring 8.5 to 9 cm, pinky 7 cm. Segment ratio proximal : middle : distal about 5 : 3 : 2.3. Finger width 1.8 to 1.9 cm at the base, tapering 15 to 20 percent to the tip.
- Thumb: 6 cm free length in two segments, rooted low on the palm near the wrist, never in line with the fingers.
- Wrist 6 cm wide by 4 cm deep. Forearm just below the wrist is about 1.2 times the wrist, rising to 1.6 times at mid forearm. A sleeve adds 1 to 1.5 cm per side.
- The hand is about 25 percent of a rifle's length and about 1.5 times a pistol's grip height. A hand bigger than the receiver reads as cartoon "mitts".

## Framing

- The gun owns the screen; hands are supporting. Combined hands and sleeves stay under about 15 percent of the screen at rest.
- Show the hand, the wrist and 8 to 20 cm of sleeve. The forearm leaves the frame within that distance, at the bottom edge or the bottom-right corner, angled toward the camera so its far end is never seen.
- Right hand: wraps the grip, trigger finger along the frame, forearm runs down and back toward the bottom-right corner.
- Left hand (rifles): under the handguard, palm up, fingers wrapping the far side, thumb along the near side. From the camera you see the thumb, the side of the hand and the heel; the forearm runs down-left and back.
- Pistol: the right hand is the main shape, bottom-right, forearm leaving the bottom-right edge. The pistol and hand together, not the hand alone, fill the corner.
- No hand ever floats: fingers touch the gun, the palm sits against it.

## Shape language

- One continuous arm per side: fingers merge into the palm, the palm into the wrist, the glove cuff into the sleeve. No balls at joints (they read as sausages), no blobs.
- Fingers are slim, slightly squared, tapered tubes with gentle knuckle bends; joints show as bends, not bulges.
- Palm is a flattened rounded block, thicker at the heel, thinner at the knuckles; the knuckle row is a straight, slightly fanned line.
- Glove details that read at viewmodel distance: knuckle pad strip, palm or heel pad, wrist strap, cuff edge. Nothing smaller.
- Sleeve: slim, with a rolled or banded cuff; a slight taper toward the wrist. Never a straight cylinder ("pole").
- Low-poly stylisation: chamfer the edges, keep curvature smooth, keep the silhouette clean; stylised hands are slightly simplified, not inflated.

## Colour

- The glove must contrast the gun's main colour in value, and the sleeve must contrast the glove.
- Our guns are mostly tan, gold and dark navy, so: warm mid-dark glove (ranger brown), lighter coyote pads, darker strap, olive drab sleeve with a darker rolled cuff.
- No pure black (reads as a hole), no blue-grey (merges with the navy guns), no saturated colours.
- Three tones per material: lighter on top, base, darker underneath and in creases.
