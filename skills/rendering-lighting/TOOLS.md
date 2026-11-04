# Rendering-Lighting Tool Knowledge (2026-11-04)
> FULL REFERENCE: TOOLS_REF.md — 13 tools, 66 functions, 35 knobs, 23 EKB rules, 16 limits, 16 unknowns (all 11 scripts read fully; no SKILL.md in pack, README.md is the skill doc).

## Tools

### pxr.UsdLux (in-sim scene authoring: lights)
- DOES: Defines and reads DomeLight / DistantLight prims and their intensities.
- FUNCTIONS USED:
  - `UsdLux.DomeLight.Define(stage, path)` + `.GetIntensityAttr().Set(400.0)` (r1_build, v6_build)
  - `UsdLux.DistantLight.Define(stage, path)` + `.GetIntensityAttr().Set(1500.0)` (r1_build, v6_build)
  - `UsdLux.DomeLight.Get(stage, path)` / `UsdLux.DistantLight.Get(stage, path)` + `.GetIntensityAttr().Set()` for during-play live sets (r3_light, v6_cap)
  - `.GetIntensityAttr().Get()` for read-back reports (r1_build)
- LIMITS-live-verified:
  - DistantLight 3x intensity swings move captured mean only ~7% in the drilled view (sun contributes little; dome is the proven lever) — failures.md R5 (OPEN).
  - During-play intensity sets apply live (dome proven; sun sets apply but contribute little); stop/set/play re-parse legs add nothing for lights — failures.md R5, discovery.md.
- UNKNOWN:
  - Why a ~95pt ambient floor persists with dome=0 (hidden ambient vs sun) — failures.md R5 discriminator (both-lights-to-0) not yet run.
  - Whether sun leverage improves with different sun rotation angles (only (-50,20,0) drilled).

### pxr.UsdGeom (in-sim scene authoring: geometry, camera, xforms)
- DOES: Defines ground plane, test cubes, USD camera, and xform ops (translate/rotate/matrix).
- FUNCTIONS USED:
  - `UsdGeom.Plane.Define` + `CreateWidthAttr().Set(20.0)` / `CreateLengthAttr().Set(20.0)` (r1_build, v6_build)
  - `UsdGeom.Cube.Define` + `GetSizeAttr().Set()` / `.Get()` (r1_build, v6_build)
  - `UsdGeom.Camera.Define` + `GetFocalLengthAttr().Set(24.0)` / `.Get()` (r1_build, v6_build)
  - `UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(...))` (r1_build, v6_build)
  - `UsdGeom.Xformable(prim).AddRotateXYZOp().Set(Gf.Vec3f(-50,20,0))` for sun orientation (r1_build, v6_build)
  - `UsdGeom.Xformable(prim).MakeMatrixXform().Set(Gf.Matrix4d(...))` for look-at camera pose (r1_build, v6_build)
  - `UsdGeom.Xformable(prim).GetOrderedXformOps()[0].Get()` for read-back (r1_build)
- LIMITS-live-verified:
  - USD camera matrix is row-major: numpy column-vector look-at output MUST be transposed (`mat.T`), else campos reads [0,0,0] and camera faces wrong way — failures.md R2.
- UNKNOWN:
  - Nothing open; Plane/Cube/Camera/translate/rotate paths all drill-proven. Non-drilled UsdGeom schemas (e.g. Sphere, Mesh) untested in this pack.

### pxr.Gf (math types for USD authoring)
- DOES: Provides matrix/vector value types consumed by UsdGeom xform ops.
- FUNCTIONS USED:
  - `Gf.Matrix4d(*16_scalars)` — unpacked scalar form (r1_build, v6_build)
  - `Gf.Vec3f(-50, 20, 0)` for sun rotation; `Gf.Vec3d(x, y, z)` for translations (r1_build, v6_build)
- LIMITS-live-verified:
  - `Gf.Matrix4d` takes 16 scalars, NOT one tuple-of-16 (tuple form raises TypeError, no converter to vector\<double\>) — failures.md R1.
  - `Gf.Matrix4d` is row-major: basis vectors are ROWS 0-2, eye is ROW 3 — failures.md R2.
- UNKNOWN:
  - Nothing open for the drilled constructors.

### omni.usd (in-sim stage access)
- DOES: Gets the live stage; looks up and removes prims (clean-slate + stale-cam removal).
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()` (r1_build, r3_light, r4_expo, v6_build, v6_cap)
  - `stage.GetPrimAtPath(path)` + `prim.IsValid()` guard (all build/cap scripts)
  - `stage.RemovePrim(path)` for clean slate and stale RtxCamera removal (all build/cap scripts)
- LIMITS-live-verified:
  - Re-parse legs spam stale-handle warnings on sensor re-creation (re-creating RtxCamera prims is noisy) — discovery.md.
- UNKNOWN:
  - Whether re-creating CameraSensor on a live RtxCamera (vs removing the prim first) avoids the stale-handle warnings.

### isaacsim.sensors.experimental.rtx: RtxCamera + CameraSensor (in-sim capture path)
- DOES: Poses an RTX camera and captures annotated RGB frames from the live renderer.
- FUNCTIONS USED:
  - `RtxCamera(path, positions=[eye.tolist()], orientations=[[w,x,y,z]])` — bare constructor + pose kwargs (r2_cap, r3_light, r4_expo, v6_cap)
  - `cam.camera.set_focal_lengths(24.0)`; `cam.camera.set_clipping_ranges(0.01, 1000.0)` (r2_cap, r3_light, r4_expo, v6_cap)
  - `CameraSensor(cam, resolution=[240, 320], annotators=["rgb"])` — resolution as LIST [H, W] (r2_cap, r3_light, r4_expo, v6_cap)
  - `sensor.get_data("rgb")` — returns per-camera LIST of warp arrays; unwrap [0] + `.numpy()` (r2_cap, r3_light, r4_expo, v6_cap)
- LIMITS-live-verified:
  - Installed 6.0.0 API has NO `aux_output_level` kwarg (TypeError if passed); probe signatures live before trusting examples — failures.md R3.
  - `resolution` MUST be a LIST `[H, W]`; a tuple crashes `broadcast_to` ("Invalid indexing in slice: 240") — failures.md R3.
  - `get_data` returns `[wp.array(H,W,3)]`, not one array; `np.asarray()` directly on it dies ("Invalid indexing in slice: 240", warp RuntimeError) — must unwrap [0] then `.numpy()` — failures.md R4.
  - Captures are bit-deterministic (143.6 baseline hit 3x; R3 legs repeated 94.8/101.3 across script variants) — discovery.md.
- UNKNOWN:
  - Annotators other than `"rgb"` (depth/normals/etc.) not drilled in this pack.
  - Resolutions other than 240x320 not drilled.

### isaacsim.core.experimental.utils.app as app_utils (in-sim timeline control)
- DOES: Plays the timeline and advances fixed settle steps so the renderer converges before capture.
- FUNCTIONS USED:
  - `app_utils.play(commit=True)` (r2_cap, r3_light, r4_expo, v6_cap)
  - `await app_utils.update_app_async(steps=120)` initial settle; `steps=90` after a light/exposure change (r2_cap, r3_light, r4_expo, v6_cap)
- LIMITS-live-verified:
  - 120 settle steps suffice for these small scenes (skill's 200 is for warehouses); 90 after a light/exposure change — discovery.md.
- UNKNOWN:
  - Minimum settle steps for larger/warehouse scenes not drilled here (skill sketch says 200, unverified by this pack).

### carb.settings (in-sim renderer settings: exposure)
- DOES: Sets live RTX post/tonemap exposure; the drilled exposure lever is filmIso.
- FUNCTIONS USED:
  - `carb.settings.get_settings().set("/rtx/post/tonemap/filmIso", 100.0|400.0)` (r4_expo, v6_cap)
- LIMITS-live-verified:
  - filmIso 100->400 moves captured mean 143.6->213.2 (1.49x) — strong lever, rules out tonemap compression as the R5 cause — failures.md R5, discovery.md.
  - Default headless state: rendermode=RealTimePathTracing, tonemap op=6, filmIso=100; NO autoExposure key present — discovery.md.
  - Drills must PIN (not inherit) render settings: R4 restores filmIso 100; V6 pins its own exposure — discovery.md.
- UNKNOWN:
  - Tonemap operator values other than 6, and any other `/rtx/post/*` keys, not drilled.
  - Effect of filmIso outside 100–400 not drilled.

### warp as wp (in-sim array type from sensors)
- DOES: Array container returned by `CameraSensor.get_data`; converted to numpy for stats/PNG.
- FUNCTIONS USED:
  - `isinstance(d, wp.array)` check; `d.numpy()` conversion (r2_cap, r3_light, r4_expo, v6_cap)
- LIMITS-live-verified:
  - Never `np.asarray()` a warp array directly (Skill 5 R2 rule: numpy iterates `__getitem__`, warp raises RuntimeError out-of-bounds) — failures.md R4.
- UNKNOWN:
  - Nothing open for the drilled `.numpy()` path.

### numpy as np (in-sim math + frame stats)
- DOES: Look-at basis construction, rotation-matrix→quaternion conversion, and frame mean/max stats.
- FUNCTIONS USED:
  - `np.array`, `np.linalg.norm`, `np.cross`, `np.eye(4)`, `np.column_stack`, `np.trace` (look-at + `_mat_to_wxyz`) (all execution scripts)
  - `np.asarray(...)`, `rgb.mean()`, `rgb.max()`, `rgb.shape`, `rgb.astype(np.uint8)` (r2_cap, r3_light, r4_expo, v6_cap)
- LIMITS-live-verified:
  - None (pure local math; the USD transpose requirement is a Gf limit, failures.md R2).
- UNKNOWN:
  - Nothing open.

### PIL.Image (in-sim PNG writer)
- DOES: Saves captured RGB frames to evidence/ as PNG.
- FUNCTIONS USED:
  - `Image.fromarray(rgb.astype(np.uint8)).save(EV)` (r2_cap, v6_cap)
- LIMITS-live-verified:
  - R2 frame: 240x320x3, mean 143.6, max 203, 33KB PNG; V6 frame: mean 184.5, 40KB PNG — README.md dataset.
- UNKNOWN:
  - Nothing open.

### os / json / re (local verifier stdlib)
- DOES: Local evaluators (verify_rN/verify_v6) parse saved `*-REPORT` outputs from evidence/*.json and gate drills.
- FUNCTIONS USED:
  - `json.load(open("...evidence/*.json"))["output"]`; `re.search(pat, EV)` float extraction; `os.path.getsize(PNG)` / `os.path.exists(PNG)` (verify_r1, verify_v6 read fully; verify_r2/r3/r4 skimmed — same imports)
- LIMITS-live-verified:
  - None (local text checks; exit 0 on pass per README).
- UNKNOWN:
  - Nothing open; verify_r2/r3/r4 bodies skimmed by imports only (same json/re pattern as verify_r1).

### isaacsim_send.py bridge (execution transport; referenced, not in pack)
- DOES: Ships the r*/v6 scripts into the live Isaac Sim session for execution (README: "in-sim via isaacsim_send.py unless noted").
- FUNCTIONS USED:
  - (No direct calls in scripts/; transport layer only. Evidence *.json files store the shipped script's reported output.)
- LIMITS-live-verified:
  - None recorded in this pack's failures.md.
- UNKNOWN:
  - Bridge CLI flags / API surface not documented anywhere in this pack (no script or doc shows the send invocation).

### inspect (live API probing; referenced in failures.md R3, no in-pack script)
- DOES: `inspect.signature` / `inspect.getsource` used during training to probe the installed 6.0.0 RtxCamera/CameraSensor signatures.
- FUNCTIONS USED:
  - `inspect.signature(...)`, `inspect.getsource(...)` (cited in failures.md R3 recovery; no surviving script demonstrates the calls — R2ProbeCam cleanup hints in v6_build suggest probe scripts existed but are absent from scripts/).
- LIMITS-live-verified:
  - None recorded beyond the R3 finding itself (installed API lags/leads sketches).
- UNKNOWN:
  - Exact probe invocations (not drill-preserved in this pack).

## Unverified

- DistantLight leverage: why sun 3x moves mean only ~7%; both-lights-to-0 discriminator not run (failures.md R5 OPEN).
- Hidden ambient floor (~95pts at dome=0) unexplained (failures.md R5 OPEN).
- Non-`rgb` annotators, non-240x320 resolutions, non-24 focal lengths, non-(-50,20,0) sun angles: none drilled.
- `/rtx/post/*` keys beyond filmIso (tonemap op values ≠ 6, autoExposure absent by default): not drilled.
- filmIso outside 100–400: not drilled.
- Settle steps for warehouse-scale scenes (sketch says 200): not drilled here.
- `isaacsim_send.py` CLI/API surface: referenced but never shown in-pack.
- `inspect` probe invocations: cited but no surviving script.
- verify_r2.py / verify_r3.py / verify_r4.py bodies: skimmed (imports only), not read fully.
- Cross-val `x6_live.py` + `verify_x6.py` (cited in README Tools): NOT present in this pack's scripts/ — presumably live elsewhere.

## Sources-read

- action-reasoner/skills/rendering-lighting/README.md (full)
- action-reasoner/skills/rendering-lighting/failures.md (full)
- action-reasoner/skills/rendering-lighting/discovery.md (full)
- action-reasoner/skills/rendering-lighting/scripts/r1_build.py (full)
- action-reasoner/skills/rendering-lighting/scripts/r2_cap.py (full)
- action-reasoner/skills/rendering-lighting/scripts/r3_light.py (full)
- action-reasoner/skills/rendering-lighting/scripts/r4_expo.py (full)
- action-reasoner/skills/rendering-lighting/scripts/v6_build.py (full)
- action-reasoner/skills/rendering-lighting/scripts/v6_cap.py (full)
- action-reasoner/skills/rendering-lighting/scripts/verify_r1.py (full)
- action-reasoner/skills/rendering-lighting/scripts/verify_v6.py (full)
- Import grep across all 11 scripts in scripts/ (verify_r2/r3/r4 skimmed by name + imports only)
