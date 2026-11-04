# Sensors Tool Knowledge (2026-11-04)

> Exhaustive reference: `TOOLS_REF.md` — 17 tools (T1–T17, T1 split a–e) · ~80 functions with signatures · ~78 knobs with effect-of-change · ~46 EKB rules · 43 limits · 35 unknowns · every claim tagged verified/probable/theoretical.

Pack: `action-reasoner/skills/sensors/` (parts: `base/` S1-S4/V7, `radac/` R1-R2).
Validated live on Isaac Sim 6.0.0 / Kit 110 (RTX + PhysX, Windows).

## Tools

### isaacsim.sensors.experimental.rtx — RTX sensor prims + GMO parsing
DOES: authors camera/lidar/radar/acoustic prims, wraps them in sensors, parses GenericModelOutput frames.
FUNCTIONS USED:
- `RtxCamera(path, positions=[...], orientations=[wxyz])` + `cam.camera.set_focal_lengths(24.0)` / `set_clipping_ranges(0.01, 1000.0)` (s1_cap, s4_run, v7_run)
- `CameraSensor(cam, resolution=[240, 320], annotators=[...])` + `sensor.get_data(name)` returning warp array / list (s1_cap, s4_run, v7_run)
- `Lidar.create(path, config="Example_Rotary", tick_rate, accumulate_outputs, positions)` + `LidarSensor(lidar, annotators=[])` (s2_lidar, r1_xcheck)
- `Radar.create(path, config="IWRL6432AOP", translations, orientations, attributes, aux_output_level="BASIC")` + `Radar(child_path)` re-wrap + `RadarSensor(radar, annotators=["generic-model-output"])` (r1_build, r1_drive, r1_ti)
- `Acoustic(path, aux_output_level, tick_rate, attributes={mounts/rxGroups/freq})` + `AcousticSensor(acoustic, annotators=["generic-model-output"])` (r2_build, r2_drive)
- `parse_generic_model_output_data(raw)` -> frame with `numElements, x, y, z, scalar, rv_ms, modality, elementsCoordsType, numSamplesPerSgw, frameStart/frameEnd, timeOffsetNs, header bounds` (s2_lidar, r1_drive, r2_drive)
LIMITS-live-verified:
- GMO (x,y,z) is SPHERICAL (az_deg, el_deg, range_m), not cartesian — cartesian read gives a "phantom ring" (failures.md base R3; radac F5 re-proves WORLD SPHERICAL + sensor offset).
- Consume GMO via Writer only; `get_data` polling drops/dupes under multitick (discovery.md RTX LiDAR).
- Author/move RTX sensors while STOPPED; live moves and live creates emit nothing until stop/play re-parse (failures.md base R5).
- GMO id/metadata arrays can exist but be zero-size — guard every reduction with `size == 0` (failures.md base R4).
- Depth annotator shape is (H,W,1), not (H,W) (failures.md base R1); frame-content gates must derive from FOV math (failures.md base R2).
- Bare-constructor generic radar is SILENT (50+ empty frames even debug-forced); only the TI vendor config detects (failures.md radac F2).
- `Radar.create(config=...)` leaves an Xform at path; must wrap the nested `OmniRadar` `<path>/sensor` child — wrapping the Xform raises ValueError (failures.md radac F2).
- Bare geometry is radar-invisible; targets need `NonVisualMaterial` or only 5 phantom dets/frame appear (failures.md radac F3).
- Sensor created at prim birth (never played) wedges the prim: later re-wraps tick frames but see zero detections (failures.md radac F4). Build authors prim only; drive creates the single sensor and plays it.
- TI GMO: `rv_ms` (Doppler) EMPTY, header bounds (maxRangeM, az/el limits) all 0.0, `scalar` (RCS) can be NEGATIVE; elevation coverage partial (upper face + far lower face missing) (failures.md radac "Known TI limitations").
- Acoustic id/offset metadata degenerate: tx/rx/channel ids all (0,0,0) save one sample, timeOffsetNs all zero (failures.md radac R2 notes).
- `Cube(scales=[2,2,2])` is a 4 m cube — validate GMO against QUERIED bbox, never assumed sizes (failures.md radac F5).

### isaacsim.sensors.experimental.physics — IMU + contact sensors
DOES: authors physics (non-render) IMU and contact-report sensors and reads dict frames.
FUNCTIONS USED:
- `IMU.create(path=...)` + `IMUSensor(imu)` + `get_data()` -> dict (`linear_acceleration, angular_velocity, ...`) (s3_run, v7_run)
- `Contact.create(path, min_threshold=0.0, max_threshold=1e6, radius=-1)` + `ContactSensor(con)` + `get_data()` -> dict (`in_contact, force, time, physics_step, number_of_contacts`) (s3_run, v7_run)
LIMITS-live-verified:
- Installed API drifts from sketches: `IMU.create` takes NO `tick_rate`, `IMUSensor` takes NO `annotators`, `get_data()` returns dict — probe signatures first (discovery.md physics sensors; SKILL.md Limitations).
- Sleeping pairs emit NO contact reports: resting contact needs scene `disableSleeping=True` + `PhysxContactReportAPI` threshold 0.0 on the sensed body + sensor as DIRECT child of the rigid body (sibling path raises ValueError) (failures.md base R7).
- First contact read can be a partial frame (only time/physics_step keys, KeyError 'in_contact'): prime right after play + retry until `in_contact` present (failures.md base R8).

### omni.replicator.core — writer-based GMO capture
DOES: attaches `GenericModelOutput` annotators to sensor render products and streams frames through custom writers.
FUNCTIONS USED:
- `rep.annotators.get("GenericModelOutput")` in `Writer.annotators` with `data_structure = "renderProduct"` (s2_lidar, r1_drive, r2_drive, diag2_beams)
- `rep.WriterRegistry.register(MyWriter)` + `sensor.attach_writer("MyWriter")` (s2_lidar, r1_drive, r2_drive)
- `write(data)` reading `data["renderProducts"][rp]["GenericModelOutput"]` (dict-or-raw unwrap) (s2_lidar, r1_drive, r2_drive)
LIMITS-live-verified:
- `rep.orchestrator.step_async()` in-session hung the bridge (semaphore timeout) — never retried; `app_utils.update_app_async` steps drive the writer fine (failures.md radac "Ruled OUT").
- `annotators=[]` vs `["generic-model-output"]` on the sensor did not fix silence alone (failures.md radac "Ruled OUT") — explicit annotator kept to mirror NVIDIA tests.

### isaacsim.core.experimental.utils.app — sim transport
DOES: plays/stops the timeline and steps the app so sensors tick and writers fire.
FUNCTIONS USED:
- `app_utils.play(commit=True)` / `app_utils.play()` / `app_utils.stop()` (s1_cap, s2_lidar, s3_run, s4_run, v7_run, r1_drive, r2_drive)
- `await app_utils.update_app_async(steps=N)` (in-sim async stepping, 60-180 steps per drill) (all run/drive scripts)
- `app_utils.update_app(steps=N)` sync stepping (probes contact_mega1/2)

### omni.usd + pxr (UsdGeom/UsdLux/UsdPhysics/PhysxSchema/Gf) — scene authoring
DOES: builds drill scenes (ground, cubes, domes, physics) and moves/queries prims.
FUNCTIONS USED:
- `omni.usd.get_context().get_stage()` + `GetPrimAtPath / RemovePrim / GetChildren / GetTypeName` (all build scripts, r1_drive child search, diag1_inventory)
- `UsdGeom.Cube/Plane/Xformable.Define`, `XformOp` translate set (s1-s4/v7 builds, s4_run live slide)
- `UsdLux.DomeLight.Define` (s1-s4/v7 builds)
- `UsdPhysics.Scene.Define` + gravity dir/mag attrs, `RigidBodyAPI/CollisionAPI/MassAPI.Apply` (s3_build, v7_build)
- `PhysxSchema.PhysxContactReportAPI.Apply + CreateThresholdAttr(0.0)`; `physxScene:disableSleeping=True` custom attr (s3_build, v7_build)
- `Gf.Vec3f/Vec3d` (builds, s4_run)
LIMITS-live-verified:
- Virgin boot ships `/Environment/defaultLight` (DistantLight 3000) — suspect for ambient floors; no `/PhysicsScene` at boot, drills define their own (discovery.md stage facts; failures.md base R5 note in SKILL.md).
- Sliding a NON-sensor cube live works (S4 depth tracks it); sliding an RTX SENSOR live breaks output until re-parse (failures.md base R5 vs s4_run green).

### isaacsim.core.experimental.objects — Cube helper
DOES: one-line rigid cube authoring for radar/acoustic targets.
FUNCTIONS USED:
- `Cube(path, positions, scales, sizes)` (r1_build, r1_mat, r1_xcheck, r2_build)
LIMITS-live-verified:
- `scales=[2,2,2]` yields a 4 m cube (scale multiplies the 2 m default), not 2 m — query the live bbox (failures.md radac F5).

### isaacsim.core.experimental.materials — NonVisualMaterial
DOES: gives prims radar cross-section so RTX radar returns detections.
FUNCTIONS USED:
- `NonVisualMaterial(path, bases="aluminum", coatings="paint", attributes="emissive")` + `cube.apply_visual_materials(mat)` (r1_build, r1_mat, r1_scene)
LIMITS-live-verified:
- Without it the cube yields only the 5 bit-identical ghost dets; with it 28/frame, ~89% on-face (failures.md radac F3).
- Must be re-applied every rebuild (build deletes the cube) (failures.md radac F3).
- Acoustic does NOT need it — bare cubes echo fine (failures.md radac R2 notes).

### carb.settings — renderer flag read
DOES: reads the boot-time motion-BVH flag the radar drill requires.
FUNCTIONS USED:
- `carb.settings.get_settings().get("/renderer/raytracingMotion/enabled")` + assert (r1_build); `import carb` also in r1_diag, r1_ext, r1_probe
LIMITS-live-verified:
- NEVER set `/renderer/raytracingMotion/enabled` live on a running renderer: wedges Hydra (viewport dead, 1.4 MB log/10 s, bridge timeouts, sim had to be killed). Boot with the flag; build scripts ASSERT it (failures.md radac F1).

### Boot CLI flag `--/renderer/raytracingMotion/enabled=true`
DOES: enables motion raytracing (MBVH) at sim boot so RTX radar detects.
FUNCTIONS USED:
- Passed as a boot arg; verified live as `motion-bvh: True` (r1_build, SKILL.md Prerequisites)
LIMITS-live-verified:
- Required for radar; harmless to acoustic (acoustic has no MBVH requirement per NVIDIA test) (failures.md radac F1 + R2 notes).

### isaacsim.core.simulation_manager (probes only)
DOES: interrogates sim backend/dt during contact diagnosis.
FUNCTIONS USED:
- `SimulationManager.get_physics_dt()`, `get_backend()` (contact_mega1/2/3, skimmed)

### omni.physx (probes only)
DOES: low-level physics interrogation during contact diagnosis.
FUNCTIONS USED:
- Imported as `_px` in contact_mega1/3 (skimmed; exact calls not enumerated)

### omni.kit.app (r1_ext, skimmed)
DOES: app-handle access in the radar extension probe.
FUNCTIONS USED:
- `import omni.kit.app` alongside `carb` (r1_ext, skimmed)

### warp — GPU-array unwrap
DOES: sensor frames arrive as `wp.array`; drills unwrap to numpy.
FUNCTIONS USED:
- `isinstance(d, wp.array)` -> `.numpy()`, `np.asarray(...)` (s1_cap, s2_lidar, s3_run, s4_run, v7_run)

### numpy — frame math
DOES: pose math, spherical->world conversion, gate statistics.
FUNCTIONS USED:
- `linalg.norm/cross/column_stack/trace`, `radians/cos/sin`, `column_stack/concatenate`, reductions (s1_cap, s2_lidar, s4_run, r1/r2 drives)

### Bridge sender (probes/sync_send.py, skimmed)
DOES: sync localhost sender for the Isaac Sim python_server wire protocol.
FUNCTIONS USED:
- `socket` + `json` + `sys`: send source bytes, shutdown(SHUT_WR), read-all, parse JSON (avoids asyncio proactor block in sandboxed shells)

### Local verifiers (stdlib json/re/math/sys)
DOES: gate drill evidence JSON files against geometry-derived thresholds (run locally, not in sim).
FUNCTIONS USED:
- `verify_s1/s2/s3/s4/v7.py` (regex gates on `*-REPORT` lines in `base/evidence/`); `verify_r1.py` (ghost fingerprint + >=80% on-face on `radac/evidence/r1_gmo.json`); `verify_r2.py` (NVIDIA-structure asserts + smax liveness on `radac/evidence/r2_gmo.json`)

### Upstream oracles (referenced, not in pack)
DOES: NVIDIA ground-truth recipes the drills mirror.
FUNCTIONS USED:
- `$ISAAC_SIM_DIR/standalone_examples/.../inspect_radar_gmo.py`, `inspect_acoustic_gmo.py`, `test_radar_sensor.py`, `test_acoustic_sensor.py` (SKILL.md References; R2 mirrors the acoustic test verbatim: 3 mounts, 2 rxGroups, 51.2 kHz, tick 30, BASIC)

## Unverified

- Generic-radar silence ROOT CAUSE: unknown backend reason (header stays zero even debug-forced); proven radar-specific by lidar cross-check, but why it never produces is not drill-proven (failures.md radac F2).
- Sensor-at-birth wedge ROOT CAUSE: unknown backend binding-order effect; second prims, stale sensors, and rewrap reruns ruled out, but the mechanism is not drill-proven (failures.md radac F4).
- Doppler (`rv_ms`) is unverifiable on BOTH paths today: TI GMO leaves it empty, generic (which fills it per NVIDIA's test) is silent in this build (failures.md radac TI limits).
- R6 OPEN: Example_Rotary wedge never sweeps (24/24 identical frames, az frozen at cube width) + zero ground returns; the 180-deg-yaw discriminator is recorded but NOT YET RUN; full-surround scans blocked (failures.md base R6).
- Whether `annotators=[]` fully equals `["generic-model-output"]` on radar: kept explicit, did not fix silence alone — equivalence not proven (failures.md radac Ruled OUT).
- `rep.orchestrator.step_async()` outside a Hydra storm: hung once, never retried (failures.md radac Ruled OUT).
- Sensor-frame (`outputFrameOfReference` != WORLD) GMO: identical here only because rotation is identity; non-identity frames not drilled (failures.md radac Ruled OUT).
- Acoustic on an MBVH-OFF sim: R2 ran on MBVH-on (harmless); MBVH-off acoustic not explicitly drilled (failures.md radac R2 notes).
- Acoustic timing/identity metadata: `timeOffsetNs` all zero and ids all (0,0,0) — no usable timing or channel identity proven (failures.md radac R2 notes).
- Ghost-floor stability across configs/scenes: 5 phantoms fingerprinted for THIS TI config + scene only; other configs not drilled (failures.md radac F3).
- Physics-sensor API surface beyond drilled calls: IMU kwargs besides path, Contact `radius` values besides -1, thresholds besides 0.0, `read_gravity` variants — unexplored (discovery.md physics sensors).
- Lidar configs besides `Example_Rotary`, radar configs besides `IWRL6432AOP` (`SUPPORTED_ACOUSTIC_CONFIGS` is empty — no acoustic vendor configs exist) (failures.md radac F2 + R2 notes).
- Camera AOVs besides `rgb` / `distance_to_image_plane`; resolutions besides 240x320 (s1_cap only).
- Tracking beyond S4: camera fixed + cube slid once; moving-camera tracking and multi-object tracking not drilled.
- Probe-only APIs (`SimulationManager` beyond dt/backend reads, `omni.physx` calls, `omni.kit.app` usage) were diagnostic scaffolding, not gated drill contracts.

## Sources-read

FULL reads (11):
- `action-reasoner/skills/sensors/SKILL.md`
- `action-reasoner/skills/sensors/failures.md`
- `action-reasoner/skills/sensors/discovery.md`
- `action-reasoner/skills/sensors/base/scripts/s1_cap.py` (S1 depth capture)
- `action-reasoner/skills/sensors/base/scripts/s2_lidar.py` (S2 lidar GMO writer)
- `action-reasoner/skills/sensors/base/scripts/s3_run.py` (S3 IMU+contact)
- `action-reasoner/skills/sensors/base/scripts/s4_run.py` (S4 depth tracking)
- `action-reasoner/skills/sensors/radac/scripts/r1_build.py` (R1 TI radar build)
- `action-reasoner/skills/sensors/radac/scripts/r1_drive.py` (R1 GMO drive)
- `action-reasoner/skills/sensors/radac/scripts/r2_build.py` (R2 acoustic build)
- `action-reasoner/skills/sensors/radac/scripts/r2_drive.py` (R2 GMO drive)

SKIMMED by name + imports + headers/greps (42 scripts):
- base builds: `s1_build.py`, `s2_build.py`, `s3_build.py`, `s4_build.py`, `v7_build.py`, `v7_run.py`
- base verifiers: `verify_s1.py`, `verify_s2.py`, `verify_s3.py`, `verify_s4.py`, `verify_v7.py`
- base probes: `probes/contact_mega1.py`, `probes/contact_mega2.py`, `probes/contact_mega3.py`, `probes/contact_mega4.py`, `probes/diag1_inventory.py`, `probes/diag2_beams.py`, `probes/sync_send.py`
- radac r1 diags/probes: `r1_attrs.py`, `r1_bbox.py`, `r1_birth.py`, `r1_birthdrive.py`, `r1_clean.py`, `r1_diag.py`, `r1_diag2.py`, `r1_diag3.py`, `r1_drive.py` (FULL, see above), `r1_ext.py`, `r1_force.py`, `r1_mat.py`, `r1_pose.py`, `r1_pose2.py`, `r1_probe.py`, `r1_scene.py`, `r1_stale.py`, `r1_ti.py`, `r1_two.py`, `r1_xcheck.py`
- radac r2 + verifiers: `r2_empty.py`, `verify_r1.py`, `verify_r2.py`
