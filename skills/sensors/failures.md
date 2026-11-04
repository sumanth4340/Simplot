# sensors — Failure Catalog (live-verified)

Failure IDs are namespaced per part: base R1-R8 (R6 open), radac F1-F5. Script paths below are relative to each part dir.

---

# Part: base (merged from `sensors`)

# Sensors — Failure Catalog (live-verified)

## R8: first contact read can return a partial frame (KeyError)
- FAILURE: V7's first get_data() had only time/physics_step keys
  (KeyError 'in_contact'); 30 steps later the frame was complete
  (force=19.6201 exact).
- CAUSE: Frame keys lag sensor creation (warm-up race).
- RECOVERY: Prime read right after play + retry loop (3x30 steps)
  until 'in_contact' present.
- PREVENTION: Never trust the first contact read; prime + retry.

## R7: sleeping pairs emit NO contact reports
- FAILURE: Valid Contact readings (live time/step) but in_contact=0,
  force=0, n=0 on a genuinely resting cube. Drop-test, radius 1.0,
  and report-API(threshold 1.0) all still zero.
- CAUSE: PhysX sleeping. The cube falls asleep ~20-34 steps after
  settling; sleeping pairs generate no contact reports. Causal proof:
  disableSleeping=True -> 9.81N stable; sleep re-enabled -> silence.
- RECOVERY (physics-agent recipe, live-proven): scene
  physxScene:disableSleeping=True + PhysxContactReportAPI threshold
  0.0 on the sensed body (single side suffices) + sensor as DIRECT
  child of the rigid body (sibling path raises ValueError).
- PREVENTION: Any resting-contact drill must disable sleeping and
  opt the body into contact reports; drop + settle before reading.

## R6: Example_Rotary rotor looks stuck; ground returns absent (OPEN)
- FACTS: 24/24 frames non-empty, all returns on the cube top;
  spherical azimuth never leaves +-15.5deg (the cube's width);
  zero ground returns (expected 5.8m+ at -15deg channels).
- READING: wedge never sweeps => scan-state frozen (or equivalent);
  ground blindness unexplained (colliders change nothing).
- DISCRIMINATOR (recorded, not yet run): yaw the sensor 180deg -
  returns follow the sensor => live rotor; returns stay => stuck.
- IMPACT: none on S2 (cube-top validation is exact); full-surround
  scans need this resolved first.

## R5: moving an RTX sensor while live breaks its output
- FAILURE: Translating S2Lidar 1.5->3.0 live gave EMPTY (60 steps);
  fresh prim created during play also started EMPTY.
- CAUSE: Sensor binding/transform parsed at play; live moves and
  live creates need a stop/play re-parse to emit.
- RECOVERY: Move-back + capture worked (same stale binding); clean
  stop/remove/play/create emits immediately.
- PREVENTION: Author/move RTX sensors while stopped; re-parse after.

## R4: GMO id fields can exist but be zero-size
- FAILURE: matId/entityId hasattr True but zero-size arrays killed
  min/max reductions (ValueError).
- RECOVERY: Guard reductions with v.size == 0 checks.
- PREVENTION: Never reduce a sensor field without a size guard.

## R3: Example_Rotary GMO (x,y,z) is SPHERICAL, not cartesian
- FAILURE: Treated x/y/z as world positions => "phantom ring" at
  12-21m matching no geometry (7 identical readings, rmin=12.022).
- CAUSE: Fields are (azimuth_deg, elevation_deg, range_m).
  Proof: spherical map lands 100.0% of 8255 returns exactly on the
  known cube top (x 1.80-2.40, y +-0.50, z=1.00).
- RECOVERY: Convert via world = pos + r*(cos el cos az, cos el sin
  az, sin el); validate fractions on known surfaces.
- PREVENTION: Never assume GMO frame/units; validate the mapping
  against known geometry FIRST (one cube-top test).

## R2: narrow-FOV framing breaks assumed gates
- FAILURE: dmax gate (>5.0, "far ground") failed: focal-24 FOV shows
  only the cube (depths 3.69-3.78).
- RECOVERY: Gate the actual framing (spread < 0.5) instead.
- PREVENTION: Derive frame-content gates from FOV math, not hope.

## R1: depth annotator shape has a channel dim
- FAILURE: Expected (240,320), got (240,320,1).
- RECOVERY: Gate dshape=[240, 320, 1].
- PREVENTION: Print shapes before gating them.

---

# Part: radac (merged from `radac`)

# radac R1+R2 -- Failure Catalog (live-verified, Isaac Sim 6.0 / Kit 110)

## F1: live motion-BVH flip wedges Hydra (viewport dead, log storm)
- FAILURE: setting `/renderer/raytracingMotion/enabled=true` live on a
  running renderer -> Hydra engine recreation loop
  (`failed to create Hydra Engine thread for viewport`, 1.4MB log
  spam / 10s); bridge semaphore timeouts; sim unusable, had to kill.
- CAUSE: motion raytracing rebuilds Hydra engines; live rebuild
  fails once the renderer is fully running with a viewport.
- RECOVERY: boot flag `--/renderer/raytracingMotion/enabled=true`
  (verified: `motion-bvh: True` at boot, radar works).
- PREVENTION: r1_build.py ASSERTS boot-time MBVH and never sets it
  live. (Kit-test suites set it live only on empty pre-render stages.)

## F2: bare-constructor Generic RadarWPMDMAT is silent (use TI config)
- FAILURE: `Radar(path, aux=BASIC)` ticks 50+ GMO frames, all
  numElements=0, all-zero header -- even with `debugForceDetection`
  forced, aluminum targets, and MBVH on.
- CAUSE: the generic default model never produces (unknown backend
  reason; header stays zero). Proven radar-specific: identical
  Lidar(GMO) cross-check on the same sim gave 10/10 x 86k returns.
- RECOVERY: `Radar.create(path, config="IWRL6432AOP", ...)` detects
  on the first run (87/87 frames x 28 dets).
- PREVENTION: R1 builds the TI vendor config only. Note
  `Radar.create(config=...)` leaves an Xform at the path with the
  real OmniRadar at `<path>/sensor`: the drive must wrap the child
  (wrapping the Xform raises ValueError).

## F3: bare geometry is radar-invisible (NonVisualMaterial required)
- FAILURE: aluminum-less cube -> 5 detections/frame, all bit-identical
  phantoms floating off-geometry (x~=3.0, z=1.2-2.6, face at x=3).
- CAUSE: radar cross-section comes from NonVisualMaterial; default
  visual materials have ~zero RCS. The 5 ghosts are the sensor's
  stable false-alarm floor (present with and without material).
- RECOVERY: `NonVisualMaterial(bases="aluminum", ...)` applied to the
  cube -> 28/frame, 25 on the face (89%).
- PREVENTION: build applies the material (it must be re-applied every
  rebuild: build deletes the cube). Verifier fingerprints the 5 known
  ghosts AND gates >=80% on-face. Do not chase the ghosts.

## F4: sensor-at-birth wedges the prim for later re-wraps
- FAILURE: RadarSensor created in the same script as Radar.create
  (never played) -> a later drive re-wraps the prim, writer ticks,
  zero detections. Reproduced 2/2 (exec-280 + R1Birth).
- CAUSE: unknown backend binding order effect. Ruled OUT as causes:
  second radar prim on stage (harmless, 57/57), stale unplayed sensor
  created post-hoc on an already-played prim (harmless, 57/57),
  re-wrap-after-re-wrap (drive reruns green 5x).
- RECOVERY: build authors the prim ONLY; the drive creates the single
  RadarSensor and plays it in the same script.
- PREVENTION: r1_build.py prints PRIM and asserts no sensor; drive
  wraps `<path>/sensor`. If a prim goes mysteriously silent, rebuild
  it (do not stack more sensors).

## F5: Cube(scales=[2,2,2]) is 4m, not 2m (verify geometry, not memory)
- FAILURE: detections mapped to a "wall at x=3.06" that matched no
  assumed geometry (face assumed at x=4.0, 0/28 on-face).
- CAUSE: experimental Cube with scales 2 = 4m cube (bbox 3.0-7.0).
  The "offset wall" WAS the face all along (25/28 on-face at x=3.0).
- RECOVERY: queried the live world bbox; verifier uses true face
  (x=3.0, |y|<=2, |z|<=2, tol 0.15).
- PREVENTION: S2 rule stands: validate the GMO mapping against QUERIED
  geometry (bbox), never assumed sizes. GMO here is WORLD SPHERICAL:
  x=az deg, y=el deg, z=range m + sensor offset (0,0,1).

## Known TI limitations (not failures; do not gate)
- `rv_ms` (Doppler) array is EMPTY on TI GMO (field exists, zero
  length) while x/y/z carry 28 dets. The generic radar fills rv_ms
  (per NVIDIA's test) but is silent in this build -- so Doppler is
  unverifiable on either path today. R1 gates geometry + scalar only.
- Elevation coverage gap: upper face (el +5..+18 deg) and far lower
  face (el < -32 deg) yield no returns; detections cluster el -32..0
  deg + ghosts. Gate the fraction, not the coverage.
- GMO header bounds (maxRangeM, min/maxAz/ElRad, ...) read 0.0 even on
  detecting frames. Frontend config attrs on the prim are correct
  (TI: +-75 deg, 15m); the parsed header is just unfilled.
- `scalar` (RCS) values can be NEGATIVE (observed +7.7..-10.7);
  gate nonzero, not positive.

## Ruled OUT during F1-F5 (do not chase)
- Writer/annotator plumbing: writer fired 50+ frames throughout; lidar
  GMO on the same sim/products/writer pattern fully works.
- `annotators=[]` vs `["generic-model-output"]`: kept the explicit
  annotator (mirrors NVIDIA's test) but it did not fix silence alone.
- `outputFrameOfReference` WORLD vs sensor frame: identical here
  (identity rotation); WORLD kept for verifier simplicity.
- Second radar prim / stale sensor / rewrap reruns: all harmless.
- `rep.orchestrator.step_async()` in-session: hung the bridge call
  (semaphore timeout) while Hydra was storming; never retried -- app
  updates drive the writer fine (57 frames / 60 steps).

---

# R2 acoustic notes (no failures; first-try green via R1 recipe)

- Bare `Acoustic()` + explicit mounts/rxGroups is the ONLY path:
  `SUPPORTED_ACOUSTIC_CONFIGS` is empty (no vendor configs). Recipe
  mirrored from NVIDIA `test_acoustic_sensor.py` verbatim (3 mounts,
  2 rxGroups, 51.2 kHz, tick 30, BASIC, bare cubes at
  (3,0)/(5,2)/(4,-2)): 87/87 frames x 960 samples on the first run.
- R1/F4 reused without re-proof: build authors the prim only, the
  drive creates the single AcousticSensor + writer and plays it.
  Drive reruns green (3/3 bit-identical: 83520 samples each).
- Liveness proven by geometry removal, not assumed from structure:
  targets present -> smax 4380.8; targets removed -> smax 1185.5
  (3.7x collapse). Verifier gates smax > 2000 (2x margins).
- Degenerate metadata (do not gate values): tx/rx/channel id arrays
  are all (0,0,0) save one sample; timeOffsetNs all zero (passes the
  test's >=0/<dur checks, carries no timing). Structure (n=960 =
  3 ways x 320 sgw), modality, coords, finiteness, frame order all
  match NVIDIA's asserts and ARE gated (12/12).
- No motion-BVH requirement for acoustic (test never sets it); our
  MBVH-on sim is harmless to it. No NonVisualMaterial needed either
  (bare cubes echo fine -- unlike radar).
