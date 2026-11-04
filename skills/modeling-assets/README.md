# Skill 3 MODELING & ASSETS — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, Windows.

## Verified facts (do not guess these)
- Indexed mesh authoring: points/counts/indices; outward-CCW winding
  verified by cross products (see m1_mesh.py face table).
- URDF import is OFFLINE: `URDFImporter(config).import_urdf()` writes a
  USD package and leaves the live stage untouched; reference the output
  root into the live stage yourself. Reruns version the output dir
  (m2_bot, m2_bot_1, ...) instead of overwriting.
- Imported hierarchy: child links NEST under parents
  (`Geometry/base/arm`); joints under `Physics/`; visuals + collision
  copies (`box`, `box_1`). Transformer emits base/robot/physics split.
- Materials: UsdPreviewSurface + MaterialBindingAPI.Bind; bindings on
  referenced prims author as overs and persist through save/open; clones
  inherit source bindings.
- GridCloner(spacing, num_per_row): define_base_env + generate_paths +
  clone(source, paths) -> positions; 3x3=9 verified at distinct spots.

## Dataset (evidence/ + assets/ + stages/, replayable)
- M1 mesh: 2x1x0.5 box, 8 points, red, exact bounds.
- M2 urdf: 2-link arm imported; links + revolute shoulder verified.
- M3 material: red bound, values exact, prims sensed.
- M4 clone: 9/9 clones at distinct grid spots.
- V3 exam: ref + bind + 4 clones + save/reopen, bindings persist.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- m1_mesh, m2_import (+assets/m2_bot.urdf), m3_material, m4_clone,
  v3_build, v3_check: in-sim authorship + execution.
- verify_mN/verify_v3: local evaluators, exit 0 on pass.

## Eval
Suite: M1 M2 M3 M4 V3 (5/5 green at graduation).

## Failure catalog
See failures.md (A1..A2).
