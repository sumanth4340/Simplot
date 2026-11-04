---
name: sensors
description: >
  RTX and physics sensor bring-up on Isaac Sim 6 — depth, lidar, IMU,
  contact, and motion tracking plus RTX radar detections and acoustic
  echo structure with writer-based GMO capture. Use when adding a camera,
  lidar, radar, acoustic, IMU, or contact sensor, debugging silent GMO,
  or validating detections against known geometry.
metadata:
  validated: 2026-11-04
  validated_by: S1-S4/V7/X7 + R1/R2 all green on Isaac Sim 6.0.0/Kit 110
---

# sensors

## Purpose

Two layers, validated live on Isaac Sim 6.0.0 / Kit 110 (RTX +
PhysX, Windows):

- `base/` — depth (S1), lidar GMO (S2), IMU + contact (S3),
  motion tracking (S4) + V7 exam + X7 cross-val.
- `radac/` — RTX radar on known geometry (R1: TI config,
  28 dets/frame, 89% on-face) + RTX acoustic echo structure
  with liveness proof (R2: 960 samples/frame, 3.7x geometry
  response). Writer-based GMO capture throughout.

Merged 2026-11-04 from the `sensors` and `radac` packs; drill
tags are namespaced per part (base S1-S4/V7, radac R1-R2).

## Routing

| Signal | Part | Drills |
|---|---|---|
| Depth, lidar xyz, IMU, contact, tracking | `base/` | S1-S4, V7, X7 |
| Radar detections, acoustic echoes, GMO silence | `radac/` | R1, R2 |

## Prerequisites

- Isaac Sim 6 / Kit 110, RTX render mode.
- `isaac-sim-sensor` (RTX GMO concepts); NVIDIA's
  `test_radar_sensor.py` / `test_acoustic_sensor.py` as oracles.
- Sim booted with `--/renderer/raytracingMotion/enabled=true`
  for radar (see radac F1); depth/IMU/contact need no flags.

## Limitations

- Installed physics-sensor API drifts from sketches: no
  tick_rate (IMU) / annotators (sensors); get_data() -> dict.
  Probe first.
- Generic bare-constructor radar is SILENT in this build (use
  the TI vendor config). TI GMO carries no Doppler and no
  header bounds; gate geometry + scalar only.
- Acoustic id/offset metadata is degenerate (all-zero); gate
  structure + amplitude, not ids.
- Radar elevation coverage is partial (upper face missing);
  gate the on-face fraction, not coverage.

## Key procedures

### Depth + lidar mapping (base S1/S2)

Depth: (H,W,1) annotator; center-ray exact to 1 mm; tracks
known motion exactly. LiDAR GMO (x,y,z) = (azimuth_deg,
elevation_deg, range_m): validate the mapping on known
geometry FIRST (100% on cube top). Writer-based consumption
only; author/move sensors stopped.

### IMU + contact (base S3)

Resting contact: disableSleeping + report API @0.0 + sensor
as direct child; prime + retry the first read (R7/R8).
Virgin boot ships /Environment/defaultLight @3000 (R5 suspect).

### Radar working recipe (radac R1)

Boot the sim with the MBVH flag; NEVER flip
`/renderer/raytracingMotion/enabled` live on a running
renderer (wedges Hydra: viewport dead, 1.4 MB log/10 s).
Build scripts must ASSERT boot-time MBVH, never set it.
`Radar.create(path, config="IWRL6432AOP", ...,
attributes={"outputFrameOfReference": "WORLD"}, aux="BASIC")`.
Wrap the nested `<path>/sensor` child. Targets need
`NonVisualMaterial` (bare geometry is radar-invisible).
One `RadarSensor` per prim, created and played in the drive
script: a sensor created at prim birth (never played) wedges
later re-wraps to zero detections. GMO is WORLD SPHERICAL
(x=az deg, y=el deg, z=range m) + sensor offset.

### Ghost-floor fingerprinting (radac R1)

The 5 bit-identical phantom detections (material-independent)
are the sensor's stable false-alarm floor: fingerprint their
(az,el,r) in the verifier AND gate >=80% on-face. Validate
the mapping against QUERIED geometry (live bbox), never
assumed sizes.

### Acoustic recipe (radac R2)

Bare `Acoustic()` is the only path (no vendor configs):
3 mounts + 2 rxGroups + 51.2 kHz + tick 30 + BASIC,
`AcousticSensor` with `annotators=["generic-model-output"]`,
writer capture. Bare cubes echo fine. Prove liveness by
geometry removal (smax 4380 -> 1186 empty-floor); gate peak
amplitude with 2x margins plus NVIDIA's structure asserts.

## Drills

| Drill | Claim | Verifier |
|---|---|---|
| base S1 depth | dshape 240x320x1, dctr 3.738 exact | `base/scripts/verify_s1.py` |
| base S2 lidar | 132258 pts, ontop 1.0000 | `base/scripts/verify_s2.py` |
| base S3 IMU+contact | amag 9.81, force 9.8098, n=4 | `base/scripts/verify_s3.py` |
| base S4 tracking | delta 1.068 exact | `base/scripts/verify_s4.py` |
| base V7 exam | 9/9 on a new 3-modality scene | `base/scripts/verify_v7.py` |
| radac R1 radar | 57/57 frames, n=28, 89% on-face, 5/5 ghosts | `radac/scripts/verify_r1.py` |
| radac R2 acoustic | 87/87 frames, n=960, echo-live | `radac/scripts/verify_r2.py` |

Cross-val: base X7 (7/7 across stage/model/phys/sense/rig).

## Related skills

- RECEIVES from: `isaac-sim-sensor` (GMO concepts, oracles).
- PRODUCES for: `ros-navigation` (range sensing, /scan
  substrate), `articulation-robots` (IMU/contact feedback).

## Failure index

Details, bisection logs, and ruled-out causes: `failures.md`
(base R1-R8, R6 open; radac F1-F5 + TI/acoustic limits).

## References

- Base tools: `base/scripts/sN_build/sN_run`, `v7_build/v7_run`,
  `verify_sN/verify_v7`, `probes/` (agent probes).
- Radac tools: `radac/scripts/r1_build.py`, `r1_drive.py`,
  `verify_r1.py`, `r2_build.py`, `r2_drive.py`, `verify_r2.py`.
- Evidence: `base/evidence/`, `radac/evidence/`.
- Upstream: `$ISAAC_SIM_DIR/standalone_examples/.../inspect_radar_gmo.py`,
  `inspect_acoustic_gmo.py`, `test_radar_sensor.py`,
  `test_acoustic_sensor.py`.

## Iteration Log

- v1.0 2026-11-04: merged `sensors` + `radac` packs into
  `sensors` (base/radac); drill scripts and evidence unchanged
  apart from path updates.
- v0.1 2026-11-04: `radac` distilled from R1/R2 drills (MSF Capture).
