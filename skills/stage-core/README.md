# Skill 2 STAGE & USD CORE — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, Windows. Fresh `new`
template carries 12 prims (World, Render scope, 4 cameras, no lights).

## Verified facts (do not guess these)
- Save/open round-trips exactly; opening a file auto-adds the 4-prim
  viewport light rig (failures.md L1). Assert by path-set, not count.
- Prims: Cube size attr IS edge length; Sphere/Cylinder/Cone/Plane params
  verified; hand-authored Mesh (points/counts/indices) verified.
- Properties: translate/rotateXYZ/scale ops, size, displayColor/Opacity,
  visibility invisible<->inherited, purpose guide/render, custom attrs.
- Purpose "render"/"proxy" needs explicit bbox query purposes (sense V1).
- Sublayers stack above weaker layers only; root direct opinions always
  win over sublayers (L2). Win + revert proven via property stack.
- References + variant selection on the referencing prim verified;
  payload Load/Unload/Load cycle verified. Author variants with the
  UsdVariantSets API, never hand-written USDA (L3).
- GetVariantEditContext() edits the SELECTED variant (takes no name).

## Dataset (evidence/ + stages/, replayable)
- S1 round-trip: 12 -> save -> 12 -> reopen 12+1+rig.
- S2 lifecycle: 6 types exact, deleted clean.
- S3 matrix: 12 ops exact + transformed bbox exact.
- S4 layers: 1.0 -> 3.0 (stack top override) -> 1.0 (stack top base).
- S5 comp: ref small 1.0 -> large 4.0; payload load/unload/load.
- V2 exam: sublayer + direct + referenced-variant scene, saved + reopened.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- s1_make_cube, s2_make_prims/s2_delete, s3_props, s4_layers, s5_comp,
  s5_diag, v2_build: in-sim authorship + execution.
- verify_sN/verify_v2: local evaluators, exit 0 on pass.

## Eval
Suite: S1 S2 S3 S4 S5 V2 (6/6 green at graduation).

## Failure catalog
See failures.md (L1..L3). S3 also drove sense probe fix V1.
