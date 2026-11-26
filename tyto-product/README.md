# TYTO — native Blender file

![Selected TYTO hero render](renders/01-tyto-hero.png)

**Open `blender/tyto_scene.blend` directly in Blender 4.2 or newer.** There is nothing to run, import, or set up first. The native scene was written without launching the Blender application and without rendering anything here.

## Main deliverable

- `blender/tyto_scene.blend` — a complete, directly openable Blender scene containing:
  - the rounded nautilus shell, spiral channel, raised eye and lower seam
  - the knurled ring, woven grille and amber LED line/tick
  - dark-bronze, soft-touch, knurled-metal, woven-mesh and emission materials
  - a seamless studio, four area lights, reflection cards and world lighting
  - an 85–95 mm camera with depth of field and a 240-frame animation
  - Cycles, 4K/8K render settings, AgX colour management and emission-only glare
  - frame 170 set as the current frame, with the LED fully drawn

The file was verified by reopening it: 23 objects, 9 meshes, 6 curves, 10 materials, 7 animation actions, 4 lights, a hero camera and a 3840 × 2160 Cycles setup.

## Other files

- `renders/01-tyto-hero.png` — the selected photorealistic concept render.
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
