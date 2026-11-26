# From CAD to the finished product film

The native `blender/tyto_scene.blend` is already built and saved, so no setup script needs to be run. Open it directly in Blender 4.2+; the Python source is optional regeneration material only.

## Part 2 — how real companies make these animations

1. **CAD model.** Industrial designers and engineers build the exact product in SolidWorks, Fusion 360, Alias or Rhino. A STEP export preserves real geometry, seams, screw seats and part boundaries.
2. **Cleanup and tessellation.** The STEP assembly is converted to meshes in Blender, Cinema 4D or KeyShot. Bevels, knurl, grille apertures and other sub-millimetre details are added or procedurally generated.
3. **Look development.** Artists tune anodized metal, fabric, glass and emissive LED materials under neutral studio lighting before committing to the hero shot.
4. **Lighting.** A virtual studio uses large softboxes, strip lights, flags and reflective cards. Metal product lighting is really the art of shaping reflections.
5. **Animation.** Camera orbits, dollies and macro pushes are keyframed. Product beats cover exploded views, parts assembling, the ring turning and the LED line switching on.
6. **Rendering.** Offline path tracers—Cycles, Arnold, Redshift, Octane or V-Ray—render beauty and utility passes, commonly at high sample counts.
7. **Compositing and grading.** After Effects, Nuke or DaVinci Resolve add emission-only glow, depth of field, lens effects, subtle grain, vignette, colour grade and sound design.

## Part 3 — Blender implementation for TYTO

`blender/build_tyto.py` turns the supplied production notes into a runnable procedural scene:

| Element | Implementation |
| --- | --- |
| Shell | Variable-radius logarithmic spiral curve converted to a mesh, voxel-remeshed, smoothed, flattened and subdivided into a pebble-like volume. |
| Spiral channel | Surface-projected ribbon plus a dark groove curve; a small raised bronze spiral forms the centre eye. |
| LED | Thin emission curve with `bevel_factor_end` keyframed from 0 to 1 so the amber line draws from centre to the ring tick. High-threshold Fog Glow provides restrained bloom. |
| Ring | Separate annular cylinder with machined bevels, polished front lip and a crossed-wave procedural diamond-knurl bump. |
| Grille | Recessed circular disk with crossed high-frequency weave waves feeding both colour and bump. |
| Materials | Principled BSDF: metallic dark bronze with noise-driven roughness variation; matte black soft-touch channel; lighter bronze micro-reflective ring; near-black woven mesh; amber emission. |
| Seam | Radial ray-cast onto the lower body produces a fine closed seam curve rather than a floating ellipse. |
| Studio | Seamless curved cyclorama, warm-grey gradient, large area key, rectangular rim strip, soft fill, off-camera reflective cards and a low-strength world. |
| Camera | 85–95 mm animated macro push on an orbit rig, f/5.6 depth of field focused on the spiral centre/ring area. |
| Render | Cycles, adaptive sampling, denoising, AgX/Filmic view transform, 4K default or 7680 × 4320 with `--ultra`, and a high-threshold glare compositor node. |

### Animation beats in the script

- Frames 1–240: slow camera orbit and subtle 85 → 95 mm macro push.
- Frames ~40–150: amber spiral draws itself outward; the ring tick ignites as the line arrives.
- Frames ~90–160: knurled ring rotates slightly and the recessed grille slides into its final position.

The script outputs a PNG sequence by default (best for compositing passes) or an H.264 preview with `--video`.

## Common mistakes that kill realism

Perfectly sharp edges, flat/even lighting, over-glowing LEDs, pure black or pure white materials, perfectly uniform roughness, no contact shadow, noisy or uneven knurling, and a spiral whose growth rate changes abruptly. Always bevel, vary roughness at a microscopic scale, keep highlights controlled, and let the emission bloom remain an accent rather than a light source.
