# From CAD to the finished product film

The refined `blender/tyto_scene.blend` is already built and saved, so no setup script needs to be run. Open it directly in Blender 4.2+; the Python source is optional regeneration material only. `renders/02-tyto-blend-preview.png` shows the native scene at frame 170.

## Part 2 — how real companies make these animations

1. **CAD model.** Industrial designers and engineers build the exact product in SolidWorks, Fusion 360, Alias or Rhino. A STEP export preserves real geometry, seams, screw seats and part boundaries.
2. **Cleanup and tessellation.** The STEP assembly is converted to meshes in Blender, Cinema 4D or KeyShot. Bevels, knurl, grille apertures and other sub-millimetre details are added or procedurally generated.
3. **Look development.** Artists tune anodized metal, fabric, glass and emissive LED materials under neutral studio lighting before committing to the hero shot.
4. **Lighting.** A virtual studio uses large softboxes, strip lights, flags and reflective cards. Metal product lighting is really the art of shaping reflections.
5. **Animation.** Camera orbits, dollies and macro pushes are keyframed. Product beats cover exploded views, parts assembling, the ring turning and the LED line switching on.
6. **Rendering.** Offline path tracers—Cycles, Arnold, Redshift, Octane or V-Ray—render beauty and utility passes, commonly at high sample counts.
7. **Compositing and grading.** After Effects, Nuke or DaVinci Resolve add emission-only glow, depth of field, lens effects, subtle grain, vignette, colour grade and sound design.

## Part 3 — Blender implementation for TYTO

`blender/build_tyto.py` turns the supplied production notes into a regenerable procedural scene:

| Element | Implementation |
| --- | --- |
| Shell | Metaballs fuse a central pebble lobe with a tapered logarithmic-spiral tail; voxel remesh welds the volume, followed by smoothing and subdivision fillets. The mouth is tucked into the shell with a soft trumpet flare. |
| Spiral channel | Front-surface-projected ribbon with a narrow groove, machined inner edge, polished raised eye and short lower-body parting curve. |
| LED | Thin emission curve with `bevel_factor_end` keyframed from 0 to 1 so the amber line draws from the centre to the ring tick. Restrained emission strength and a high-threshold Fog Glow keep bloom as an accent. |
| Ring | Separate annular cylinder with machined bevels and a polished front lip, plus crossed-wave procedural diamond-knurl bump and real crossed-wire knurl geometry. |
| Grille | Recessed circular disk with high-frequency crossed weave waves feeding colour and bump, overlaid with real orthogonal woven-wire curves. |
| Materials | Principled BSDF: satin dark bronze with noise-driven roughness variation; matte black soft-touch channel; lighter bronze micro-reflective ring; near-black woven mesh; controlled amber emission. |
| Studio | Smooth subdivided warm-grey cyclorama, large upper-left key, rear-right strip rim, soft fill, rolling top highlight and gentle front shaping light, with a low-strength world. |
| Camera | 85–95 mm animated macro push on an orbit rig, f/5.6 depth of field focused on the spiral centre/ring area. |
| Render | Cycles, 256 samples, denoising, Filmic view transform, 4K default or 7680 × 4320 with `--ultra`, and a high-threshold glare compositor node. |

### Animation beats in the script

- Frames 1–240: slow camera orbit and subtle 85 → 95 mm macro push.
- Frames ~40–150: amber spiral draws itself outward; the ring tick ignites as the line arrives.
- Frames ~90–160: knurled ring rotates slightly and the recessed grille slides into its final position.

Running the optional builder always regenerates and overwrites `tyto_scene.blend`. `--still` renders one PNG; `--animate` renders a PNG sequence by default, or an H.264 MP4 when combined with `--video`. These are optional production outputs—the saved `.blend` is the direct-open deliverable.

## Common mistakes that kill realism

Perfectly sharp edges, flat/even lighting, over-glowing LEDs, pure black or pure white materials, perfectly uniform roughness, no contact shadow, noisy or uneven knurling, floating backdrop seams, duplicated parts and a spiral whose growth rate changes abruptly. Always bevel, vary roughness at a microscopic scale, keep highlights controlled, keep surface details attached to the product, and let the emission bloom remain an accent rather than a light source.
