# TYTO — native Blender scene

![Selected TYTO hero render](renders/01-tyto-hero.png)

**Open `blender/tyto_scene.blend` directly in Blender 4.2 or newer.** There is nothing to run, import, or set up first. The refined native scene was written with Blender's Python API without launching the Blender GUI or executable.

![Preview of the refined native Blender scene](renders/02-tyto-blend-preview.png)

## Main deliverable

- `blender/tyto_scene.blend` — a complete, directly openable Blender scene containing:
  - a solid pebble-like nautilus shell built from a fused spiral volume, with a smooth flared tail
  - a narrow soft-touch spiral channel, raised polished spiral eye, subtle lower parting seam and controlled amber LED line/tick
  - a lighter-bronze machined ring with real crossed knurl geometry, procedural diamond knurl and crisp micro-reflections
  - a recessed woven mic grille with both a fine weave shader and real orthogonal wire geometry
  - satin dark-bronze, soft-touch, polished bronze, woven-mesh and restrained emission materials
  - a smooth warm-grey cyclorama, five area lights, a low-strength world and a soft contact shadow
  - an 85–95 mm animated macro camera with depth of field and a 240-frame animation
  - Cycles, 3840 × 2160 render settings, Filmic colour management, denoising and high-threshold emission-only glare
  - frame 170 set as the current frame, with the LED fully drawn

The file was verified by reopening it: 26 objects, 8 meshes, 9 curves, 11 materials, 7 animation actions, 5 lights, a hero camera and a 3840 × 2160 Cycles setup.

## Other files

- `renders/01-tyto-hero.png` — the selected photorealistic concept render.
- `renders/02-tyto-blend-preview.png` — a direct preview of the refined native `.blend` scene at frame 170.
- `references/` — the three supplied sketches/references.
- `PROMPT.md` — reproducible hero brief and the optional TYTO-C brief, including the avoid list. The optional variant render was not selected, so no TYTO-C image is included.
- `WORKFLOW.md` — the CAD-to-composite pipeline and the Blender implementation plan behind Parts 2–3.
- `blender/build_tyto.py` — **optional source only**. It documents how the `.blend` was generated; you do not need to run it.
- `.gitignore` — keeps backup files and temporary render outputs out of Git; the deliverable `.blend` is intentionally tracked.

## Opening the file

1. Open Blender 4.2 or newer.
2. Choose **File → Open**.
3. Select `tyto-product/blender/tyto_scene.blend`.

Press **Space** to play the animation, or scrub to frame 170 for the fully lit hero pose. The render settings are already configured; no Python execution is required.
