# Modeling & Assets — Failure Catalog (live-verified)

## A1: import_urdf() leaves the live stage untouched
- FAILURE: M2 v1 expected /m2_bot on the live stage after import; the
  stage still held the previous scene while 6 .usd files landed on disk.
- CAUSE: The converter works offline (opens the flattened file in its
  own context, runs the transformer, saves the package). Ext tests use
  their own harness stage, not the live app stage.
- RECOVERY: Reference the emitted package root into the live stage
  yourself (`m2_out/m2_bot/m2_bot.usda` at /World/M2Bot). Verified green.
- PREVENTION: After any importer call, reference-then-sense; never
  assume the live stage changed. Reruns version output dirs (m2_bot_1..).

## A2: imported child links nest under parents
- FAILURE: M2 v2 expected /World/M2Bot/Geometry/arm; actual path is
  /World/M2Bot/Geometry/base/arm.
- CAUSE: The importer preserves the URDF tree: child links compose under
  their parent link prims. Visuals/collisions double as box/box_1.
- RECOVERY: Address nested paths; sense the subtree after import.
- PREVENTION: Always enumerate the composed tree once per new asset.
