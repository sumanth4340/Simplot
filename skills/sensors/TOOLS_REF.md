# sensors — TOOLS_REF (exhaustive tool reference, 2026-11-04)

Datatype pass (2026-11-04): signatures typed 67/67 entries (150 individually-typed `) ->` callable forms; T9/T17 N/A — CLI arg / external oracles); knobs typed 76/76 table rows across 14 tables (T1e/T10–T14/T16 prose-typed, no tables); still-unknown 78 `[unknown]` markers (unobserved defaults + types without call sites; same unknown may appear in both its signature and its knob row).

Pack: `action-reasoner/skills/sensors/` (parts: `base/` S1-S4/V7, `radac/` R1-R2).
Validated live on Isaac Sim 6.0.0 / Kit 110 (RTX + PhysX, Windows).
Companion index: `TOOLS.md` (summary). This file is the exhaustive reference:
for EVERY tool — DOES / every function + full signature / every knob +
effect-of-change / EKB rules / LIMITS with cites / UNKNOWNs.

Claim tags: **[verified]** = gated green by a drill/verifier or live probe
output quoted in pack; **[probable]** = observed in script behavior or
consistent across multiple scripts but not explicitly gated; **[theoretical]**
= inferred from API shape, NVIDIA oracle docs, or single un-gated
observation — do NOT build contracts on it.

Script paths below are relative to `action-reasoner/skills/sensors/`
unless noted. "FULL" = fully read; "skim" = header/imports/grep skim.

---

## T1 — isaacsim.sensors.experimental.rtx (RTX sensor prims + GMO parsing)

DOES: authors camera/lidar/radar/acoustic USD prims, wraps them in
sensor objects bound to render products, and parses GenericModelOutput
frames [verified].

### T1a — RtxCamera + CameraSensor (depth/rgb)

Functions (as-called in pack; installed signatures not introspected):

- `RtxCamera(path: str, positions: list[list[float]] [m, outer len 1] = [unknown — always passed], orientations: list[list[float]] [w,x,y,z quat, unitless, outer len 1] = [unknown — always passed]) -> RtxCamera` [probable — kwargs observed in `base/scripts/s1_cap.py:52` FULL, `s4_run.py:57` FULL, `v7_run.py:53` FULL; defaults unknown]
  - `path: str` (USD prim path, positional) e.g. `"/World/S1Cam"`. Pre-existing prim at path is removed first via `stage.RemovePrim` in all three run scripts [verified].
  - `positions=[eye.tolist()]` — `list[list[float]]`, single 3-vector in a list, meters [m]; eye e.g. `[0,-4,2]` [verified: s1_cap.py:13,52; s4_run.py:14,57; v7_run.py:14,53].
  - `orientations=[wxyz]` — `list[list[float]]`, single quaternion `[w,x,y,z]` (unitless) in a list, built from a look-at rotation matrix by a `_mat_to_wxyz(m: np.ndarray[(3,3), float] [unitless]) -> list[float] len 4` helper (trace-branch conversion, duplicated in all three scripts: s1_cap.py:22-38, s4_run.py:23-39, v7_run.py:24-40) [verified].
  - Returns `RtxCamera` object with `.camera` handle exposing `set_focal_lengths` / `set_clipping_ranges` [verified].
- `cam.camera.set_focal_lengths(f: float [probable mm] = [unknown — always passed as 24.0]) -> None` — called as `set_focal_lengths(24.0)` in all three scripts (s1_cap.py:54, s4_run.py:59, v7_run.py:55) [verified].
- `cam.camera.set_clipping_ranges(near: float [m, probable] = [unknown — always passed], far: float [m, probable] = [unknown — always passed]) -> None` — called as `set_clipping_ranges(0.01, 1000.0)` in all three scripts (s1_cap.py:55, s4_run.py:60, v7_run.py:56) [verified].
- `CameraSensor(cam: RtxCamera, resolution: list[int] len 2 [H, W in pixels] = [unknown — always passed], annotators: list[str] = [unknown — always passed]) -> CameraSensor` [probable — kwargs observed; defaults unknown]
  - Called as `CameraSensor(cam, resolution=[240, 320], annotators=["rgb", "distance_to_image_plane"])` (s1_cap.py:57-58) or `annotators=["distance_to_image_plane"]` (s4_run.py:62-63, v7_run.py:63-64) [verified].
- `sensor.get_data(name: str) -> wp.array | list[wp.array] | np.ndarray` — called as `sensor.get_data("rgb")`, `sensor.get_data("distance_to_image_plane")` (s1_cap.py:42,60-61; s4_run.py:43; v7_run.py:67) [verified]. Return is unwrapped: if list/tuple take `[0]`; if `wp.array` call `.numpy()` (`_grab(sensor: CameraSensor, name: str) -> np.ndarray` in s1/s4 per s1_cap.py:41-45, `_w(a: wp.array | np.ndarray) -> np.ndarray` in v7 per v7_run.py:43-46) [verified]. Depth values meters [m] [verified: center-ray gates]; rgb values unitless 0–255 [probable].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `positions` (eye) | `list[list[float]]` [m] def=[unknown — always passed] | `[0,-4,2]` (s1/s4), `[4,0,2]` (v7) | Moves viewpoint; center-ray depth follows exactly: s1 dctr 3.738 exact, v7 dctr ~3.602, s4 d1 3.738 [verified: `verify_s1/s4/v7.py`] |
| `orientations` (wxyz look-at) | `list[list[float]]` [quat w,x,y,z unitless] def=[unknown — always passed] | look-at matrix quat | Rotates view axis; wrong quat = wrong framing, gates fail (R2 lesson: derive gates from FOV math) [verified: failures.md base R2] |
| `set_focal_lengths` | `float` [probable mm] def=[unknown — always 24.0] | 24.0 | Focal-24 FOV is narrow: 1 m cube at 3.7 m fills the frame (depths 3.69–3.78, no ground visible) [verified: failures.md R2, discovery.md]. Larger focal = narrower FOV [theoretical — only 24.0 drilled] |
| `set_clipping_ranges` | `(float, float)` [m, probable] def=[unknown — always passed] | (0.01, 1000.0) | Near/far clip of depth; geometry outside is clipped [theoretical — only one value drilled; consistent with clipping semantics] |
| `resolution` | `list[int]` len 2 [H,W pixels] def=[unknown — always passed] | [240, 320] | Output shape is (H, W, 1) = (240, 320, 1) [verified: failures.md R1; `verify_s1/v7.py`]. Other resolutions not drilled [verified-absent: TOOLS.md Unverified] |
| `annotators` | `list[str]` [unitless names] def=[unknown — always passed] | rgb, distance_to_image_plane | Multi-annotator attach works; each name is a separate `get_data` channel [verified: s1_cap.py, discovery.md]. AOVs besides these two not drilled [verified-absent] |
| `get_data` polling (camera) | call cadence [steps/frames] def=N/A (manual call) | per-read after 90–180 steps | WORKS for camera annotators (unlike GMO): s1/s4/v7 all poll `get_data` directly [verified]. Do NOT generalize to GMO (Writer-only there) [verified: discovery.md] |

EKB rules:

- IF depth shape gate fails with (240,320,1) vs (240,320) THEN gate the 3-D shape (channel dim exists) BECAUSE the annotator always emits (H,W,1) [verified: failures.md R1].
- IF depth min/max gates fail on a new framing THEN re-derive gates from FOV math (focal + pose + target size) BECAUSE focal-24 shows only what it frames (all-cube frame: spread < 0.5) [verified: failures.md R2].
- IF a depth value looks wrong THEN compute the center-ray analytic prediction first (t = Δ/optical-axis-cosine) BECAUSE center-ray is exact to 1 mm when geometry is known (3.738/3.738) [verified: discovery.md].
- IF tracking a moving object with depth THEN move the OBJECT live (works), never the camera live (breaks binding until re-parse) BECAUSE S4 slid the cube live and depth tracked exactly (delta 1.068) while R5 proves live sensor moves emit nothing [verified: s4_run.py vs failures.md R5].

LIMITS (with cites):

- L1a-1: Depth shape is (H,W,1), never (H,W) [verified: failures.md R1].
- L1a-2: Camera must be authored while STOPPED; live sensor moves/creates emit nothing until stop/play re-parse [verified: failures.md R5].
- L1a-3: Only `rgb` + `distance_to_image_plane` AOVs and 240x320 resolution are drilled [verified: TOOLS.md Unverified].

UNKNOWN (all [theoretical]):

- U1a-1: Other focal lengths' exact FOV mapping; other resolutions; other AOVs.
- U1a-2: Moving-camera tracking and multi-object tracking (S4 = fixed camera + one slide of one cube).
- U1a-3: `RtxCamera`/`CameraSensor` constructor defaults and full kwarg surface (never introspected).

### T1b — Lidar + LidarSensor (RTX lidar GMO)

Functions (as-called):

- `Lidar.create(path: str, config: str = [unknown — always passed], tick_rate: float [Hz, probable] = [unknown — 10.0 or omitted], accumulate_outputs: bool [unitless] = [unknown — True or omitted], positions: list[list[float]] [m, outer len 1] = [unknown — omitted in xcheck]) -> Lidar` [probable — kwargs observed; defaults unknown]
  - Called as `Lidar.create(path="/World/S2Lidar", config="Example_Rotary", tick_rate=10.0, accumulate_outputs=True, positions=[[0.0, 0.0, 1.5]])` in `base/scripts/s2_lidar.py:50-52` FULL and `base/scripts/probes/diag2_beams.py:73-75` skim [verified].
  - Called as `Lidar.create("/World/R1XLidar", config="Example_Rotary_2D")` (config only; `path: str` positional, `tick_rate`/`accumulate_outputs`/`positions` omitted) in `radac/scripts/r1_xcheck.py:18` FULL [verified].
  - `Lidar(path: str) -> Lidar` re-wrap of an existing prim observed in diag2_beams (`Lidar("/World/S2Lidar")`, reuse branch diag2_beams.py:70) [probable — skim].
- `LidarSensor(lidar: Lidar, annotators: list[str] [unitless names] = [unknown — always passed]) -> LidarSensor` [probable]
  - Called with `annotators=[]` (s2_lidar.py:53, diag2_beams.py:77) and with `annotators=["generic-model-output"]` (r1_xcheck.py:19) [verified]. BOTH forms produce GMO through the Writer path [verified: s2 green + xcheck 10/10 x 86k].
- `parse_generic_model_output_data(raw: GMOHandle | dict) -> GMO frame` — see T1e for the frame contract [verified: s2_lidar.py:40].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `config` | `str` [unitless name] def=[unknown — always passed] | `Example_Rotary` (S2: 132258 pts cited / 8255+ returns per capture, ontop 1.0000 [verified: SKILL.md, failures.md R3]) | `Example_Rotary_2D` also detects (10/10 x 86k returns on same sim [verified: failures.md F2, r1_xcheck.py]). Any other config unexplored [verified-absent] |
| `tick_rate` | `float` [Hz, probable] def=[unknown — 10.0 or omitted] | 10.0 | Ticks/frame pacing of the lidar model [theoretical — only 10.0 drilled; GMO multitick drop/dupe behavior under polling is why Writer is mandatory] |
| `accumulate_outputs` | `bool` [unitless] def=[unknown — True or omitted] | True | Accumulates returns across ticks into the frame [theoretical — only True drilled; False would plausibly yield fewer points per frame] |
| `positions` | `list[list[float]]` [m] def=[unknown — omitted in xcheck] | [[0,0,1.5]] | Sensor origin; applies correctly (0,0,1.5 confirmed [verified: discovery.md]); spherical->world conversion adds this offset (wz = 1.5 + r·sin el) [verified: s2_lidar.py] |
| `annotators` on LidarSensor | `list[str]` [unitless names] def=[unknown — always passed] | [] and ["generic-model-output"] | Both work with Writer capture [verified]. No behavioral difference proven [probable] |
| Beam geometry (read-only) | `float` near/far [m], `int` channels, `float` el fan [deg]; def=N/A (config-owned) | nearRangeM=1.0, farRangeM=200, 128ch, el -15..+10 (Example_Rotary) [verified: discovery.md] | Returns outside [near, far] or outside the elevation fan do not appear [probable — inferred from config semantics + R6 ground-absence anomaly] |

EKB rules:

- IF lidar returns look like a "phantom ring" at 12–21 m THEN you read GMO as cartesian — convert spherical: world = pos + r·(cos el·cos az, cos el·sin az, sin el) BECAUSE GMO (x,y,z) = (az_deg, el_deg, range_m), proven by 100.0% on-cube-top mapping [verified: failures.md R3].
- IF consuming lidar GMO THEN use a Writer, never `get_data` polling BECAUSE polling drops/dupes under multitick [verified: discovery.md].
- IF moving/creating a lidar THEN do it while STOPPED and re-parse (stop/play) BECAUSE live moves/creates emit EMPTY until re-parse [verified: failures.md R5].
- IF reducing any GMO id/metadata array THEN guard `size == 0` first BECAUSE matId/entityId can exist-but-zero-size and kill min/max [verified: failures.md R4].
- IF validating a new lidar config THEN run the one-cube-top spherical test FIRST BECAUSE the mapping (frame/units) must be proven before any gate trusts it [verified: failures.md R3].

LIMITS (with cites):

- L1b-1: GMO (x,y,z) is SPHERICAL (az_deg, el_deg, range_m), not cartesian [verified: failures.md R3].
- L1b-2: Writer-only consumption; `get_data` polling drops/dupes [verified: discovery.md].
- L1b-3: Author/move while STOPPED; live ops emit nothing until re-parse [verified: failures.md R5].
- L1b-4: GMO id/metadata arrays can be zero-size — guard reductions [verified: failures.md R4].
- L1b-5 (OPEN R6): Example_Rotary wedge never sweeps (24/24 identical frames, az frozen at cube width) + zero ground returns; the 180-deg-yaw discriminator is recorded but NOT run; full-surround scans blocked [verified-open: failures.md R6].

UNKNOWN (all [theoretical] unless noted):

- U1b-1: R6 root cause (frozen scan-state vs equivalent; ground blindness unexplained — colliders change nothing) [verified-open, mechanism theoretical].
- U1b-2: All lidar configs besides Example_Rotary / Example_Rotary_2D.
- U1b-3: Effect of tick_rate != 10.0, accumulate_outputs=False.
- U1b-4: nearRangeM/farRangeM/channel-count overrides (read in diag1 attr dump, never written).

### T1c — Radar + RadarSensor (RTX radar GMO, TI vendor path)

Functions (as-called; `Radar.__init__` / `RadarSensor.__init__`
signatures printed by `radac/scripts/r1_probe.py` skim but output not
captured in pack, so printed signatures are NOT available — all
signatures below are as-called [probable]):

- `Radar.create(path: str, config: str, translations: np.ndarray[(3,), float64] [m] = [unknown — always passed], orientations: np.ndarray[(4,), float64] [w,x,y,z quat, unitless] = [unknown — omitted in ti/birth/two], attributes: dict[str, str] [unitless] = [unknown — omitted in birth/two], aux_output_level: str [unitless] = [unknown — always "BASIC"]) -> Radar` [probable]
  - Called as `Radar.create("/World/R1Radar", config="IWRL6432AOP", translations=np.array([0,0,1]), orientations=np.array([1,0,0,0]), attributes={"omni:sensor:WpmDmat:outputFrameOfReference": "WORLD"}, aux_output_level="BASIC")` in `radac/scripts/r1_build.py:32-37` FULL [verified].
  - Variants: without `orientations` (r1_ti.py:13-17 FULL), without `attributes`/`orientations` (r1_birth.py:10-12, r1_two.py:9-11 skim) — all TI, all create fine [verified].
  - Returns object with `.paths[0]: str` (prim path string) and `.prims[0]: Usd.Prim` (USD prim; `GetTypeName() -> str` observed) [verified: r1_build.py:42, r1_ti.py:18].
  - Leaves an **Xform** at `path` with the real `OmniRadar` nested at `<path>/sensor` [verified: failures.md F2; r1_drive.py:59-63 child search].
- `Radar(path: str) -> Radar` re-wrap — called as `Radar(_radar_path: str)` on the nested child (r1_drive.py:65 FULL), `Radar("/World/R1Radar/sensor")` (r1_scene.py:45, r1_stale.py:7, r1_birthdrive.py:28 skim), `Radar("/World/R1Birth")` (r1_birth skim) and `Radar("/World/R1Radar")` on the Xform (r1_mat.py:47, r1_diag.py:26, r1_diag2.py:23, r1_force.py:46, r1_diag3.py:40 skim) [verified]. Wrapping the Xform raises ValueError per failures.md F2, though several skim probes do it (their outputs uncaptured — treat Xform-wrap as FORBIDDEN per the failure catalog, not per probe success) [verified: failures.md F2].
- `RadarSensor(radar: Radar, annotators: list[str] [unitless names] = [unknown — always passed]) -> RadarSensor` [probable]
  - Called with `annotators=["generic-model-output"]` (r1_drive.py:66 FULL + all skim drives) and `annotators=[]` (r1_diag.py:27, r1_diag2.py:24 skim) [verified].
  - Exposes `sensor.render_product_path: str [probable — USD path]` / `sensor.render_product: UsdRenderProduct [probable — prim handle]` attrs (probed in r1_diag.py:28-29, r1_diag2.py:25-26 skim) [probable — skim only, outputs uncaptured].
  - Exposes `sensor.get_data(name: str) -> dict | wp.array [theoretical — return shape uncaptured]` (r1_diag.py:35 skim tried `get_data("generic-model-output")`; output uncaptured) [theoretical — never a gated path; Writer is the proven path].
- `sensor.attach_writer(name: str) -> None [probable]` — see T3 [verified: r1_drive.py:67].
- Debug-force attrs (set directly on the prim, `radac/scripts/r1_force.py:13-16` skim): `prim.GetAttribute(name: str) -> Usd.Attribute` then `.Set(value: bool) -> None` for `omni:sensor:WpmDmat:scan:s001:debugForceDetection=True`, `.Set(value: float) -> None` for `debugForceRange=20.0 [m, probable]`, `debugForceAz=0.0 [deg, probable]`, `debugForceEl=0.0 [deg, probable]` — did NOT rescue the silent generic radar (still 0 dets) [verified: failures.md F2].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `config` | `str` [unitless name] def=[unknown — always passed] | `IWRL6432AOP` | THE working path: 87/87 frames x 28 dets first run; 57/57 frames, n=28, 89% on-face, 5/5 ghosts gated [verified: SKILL.md, verify_r1.py]. Bare constructor `Radar(path, aux=BASIC)` is SILENT: 50+ empty frames even debug-forced + aluminum + MBVH [verified: failures.md F2] |
| `translations` | `np.ndarray[(3,)]` [m] def=[unknown — always passed] | [0,0,1] (R1), [0,±2,1] (birth/two scratch) | Sensor origin; GMO ranges are WORLD SPHERICAL + this offset (verifier adds SENSOR=(0,0,1)) [verified: failures.md F5, verify_r1.py] |
| `orientations` | `np.ndarray[(4,)]` [quat w,x,y,z unitless] def=[unknown — omitted in ti/birth/two] | [1,0,0,0] identity (R1) / omitted (ti/birth/two) | Identity rotation = WORLD and sensor frames coincide; non-identity frames NOT drilled [verified: TOOLS.md Unverified] |
| `attributes outputFrameOfReference` | `dict[str,str]` value `str` [unitless] def=[unknown — omitted in birth/two] | WORLD (R1, ti) / omitted (birth/two) | WORLD kept for verifier simplicity; WORLD vs sensor-frame identical here (identity rotation) [verified: failures.md Ruled OUT] |
| `aux_output_level` | `str` [unitless] def=[unknown — always "BASIC"] | BASIC everywhere | Only level drilled [verified]. Other levels unexplored [verified-absent] |
| `annotators` on RadarSensor | `list[str]` [unitless names] def=[unknown — always passed] | ["generic-model-output"] (drives) / [] (diag/diag2) | Explicit kept to mirror NVIDIA tests; did NOT fix silence alone [verified: failures.md Ruled OUT]. Equivalence unproven [verified-absent] |
| TI frontend attrs (read-only) | `float` az/el fan [deg], `float` maxRange [m]; def=N/A (vendor-config-owned) | ±75 deg az/el, 15 m maxRange (prim attrs correct) | Frontend config is correct on the prim while the parsed GMO header reads 0.0 — trust prim attrs, not header [verified: failures.md TI limits] |
| debugForce* attrs | `bool` Detection; `float` Range [m, probable], Az/El [deg, probable]; def=[unknown] | Detection=True, Range=20, Az=0, El=0 | No effect on silent generic radar (still 0/frame) — proves pipeline-dead, not aiming/threshold [verified: failures.md F2, r1_force.py] |
| Target material | `NonVisualMaterial` handle [unitless] def=N/A (must apply) | NonVisualMaterial aluminum (T7) | Without: 5 ghost dets/frame only. With: 28/frame, 25 on-face (89%) [verified: failures.md F3, verify_r1.py] |
| Ghost floor | 5×`(float az [deg], float el [deg], float r [m])` fingerprints; def=N/A (observed) | 5 bit-identical phantoms (az,el,r fingerprinted) | Stable false-alarm floor, material-independent; fingerprint AND gate >=80% on-face [verified: verify_r1.py, failures.md F3] |

EKB rules:

- IF radar GMO is all-empty THEN check (1) vendor config used? (2) MBVH booted? (3) material applied? (4) wrapped the `<path>/sensor` CHILD? (5) sensor created at prim birth? BECAUSE each is a proven independent silence cause (F2/F1/F3/F2/F4) [verified: failures.md F1–F5].
- IF `Radar.create` just ran THEN wrap `<path>/sensor` (search children for `OmniRadar`), never the top path BECAUSE the top is an Xform and wrapping it raises ValueError [verified: failures.md F2, r1_drive.py:56-65].
- IF building a radar script THEN author the prim ONLY in build; create the ONE sensor + writer + play in the drive BECAUSE sensor-at-birth wedges the prim for later re-wraps (0 dets, reproduced 2/2) [verified: failures.md F4].
- IF a prim goes mysteriously silent THEN rebuild it; do NOT stack more sensors BECAUSE rewrap-reruns on a wedged prim stay silent while rebuilds detect [verified: failures.md F4].
- IF gating TI detections THEN gate on-face fraction (>=80%) + ghost fingerprint + scalar-nonzero, never Doppler/header/coverage BECAUSE rv_ms is empty, header bounds are 0.0, RCS can be negative, and elevation coverage is partial [verified: failures.md TI limits, verify_r1.py].
- IF mapping TI detections THEN use WORLD SPHERICAL + sensor offset against QUERIED bbox BECAUSE the "offset wall" was the true face all along (Cube scales=[2,2,2] = 4 m cube, face x=3.0) [verified: failures.md F5].

LIMITS (with cites):

- L1c-1: Bare-constructor generic radar is SILENT in this build; only the TI vendor config detects [verified: failures.md F2].
- L1c-2: `Radar.create` leaves Xform at path; must wrap nested `OmniRadar` child [verified: failures.md F2].
- L1c-3: Bare geometry is radar-invisible; NonVisualMaterial required [verified: failures.md F3].
- L1c-4: Sensor-at-birth wedges the prim for later re-wraps [verified: failures.md F4].
- L1c-5: TI GMO `rv_ms` EMPTY; header bounds all 0.0; `scalar` can be NEGATIVE; elevation coverage partial (el +5..+18 and < -32 missing) [verified: failures.md TI limits].
- L1c-6: GMO is WORLD SPHERICAL (x=az deg, y=el deg, z=range m) + sensor offset [verified: failures.md F5].

UNKNOWN (all [theoretical] unless noted):

- U1c-1: Generic-silence ROOT CAUSE (header zero even debug-forced; radar-specific per lidar xcheck, mechanism unknown) [verified-open: failures.md F2].
- U1c-2: Birth-wedge ROOT CAUSE (binding-order effect; second prims/stale sensors/rewraps ruled out) [verified-open: failures.md F4].
- U1c-3: Doppler unverifiable on both paths today [verified-open: failures.md TI limits].
- U1c-4: Radar configs besides IWRL6432AOP; aux levels besides BASIC; non-identity output frames; ghost-floor stability across configs/scenes.
- U1c-5: Whether `annotators=[]` fully equals `["generic-model-output"]` on radar.

### T1d — Acoustic + AcousticSensor (RTX acoustic GMO)

Functions (as-called):

- `Acoustic(path: str, aux_output_level: str [unitless] = [unknown — always "BASIC"], tick_rate: float [Hz, probable] = [unknown — always 30.0], attributes: dict[str, float | tuple[float, float, float] | list[int]] = [unknown — always passed]) -> Acoustic` [probable — kwargs observed; defaults unknown]
  - Called as `Acoustic("/World/R2Acous", aux_output_level="BASIC", tick_rate=30.0, attributes={<9 keys enumerated next line>})` in `radac/scripts/r2_build.py:18-33` FULL [verified]. NO vendor-config kwarg exists: `SUPPORTED_ACOUSTIC_CONFIGS` is empty — bare constructor is the ONLY path [verified: failures.md R2 notes].
  - `attributes` keys drilled with types: `...:centerFrequency: float = 51200.0 [Hz]`; `...:sensorMount:m001/m002/m003:position: tuple[float,float,float] = (0,∓0.05/0,0) [m]`; `:rotation: tuple[float,float,float] = (0,0,0)` x3 [deg, probable]; `...:rxGroup:g001:receiverIndices: list[int] = [0,1]`; `...:rxGroup:g002:receiverIndices: list[int] = [1,2]` [unitless indices] [verified: r2_build.py:22-32].
  - Returns object with `.paths[0]: str` and `.prims[0]: Usd.Prim` (prim type printed via `.GetTypeName() -> str`, value uncaptured in pack text) [verified: r2_build.py:37].
- `Acoustic(path: str) -> Acoustic` re-wrap — `Acoustic("/World/R2Acous")` in r2_drive.py:58 FULL and r2_empty.py:44 FULL [verified]. NOTE: unlike `Radar.create`, the bare `Acoustic()` constructor leaves the prim directly at path — NO nested `<path>/sensor` child search is done in either drive [verified: r2_drive.py:58, r2_empty.py:44].
- `AcousticSensor(acoustic: Acoustic, annotators: list[str] [unitless names] = [unknown — always passed]) -> AcousticSensor` — called with `annotators=["generic-model-output"]` in both drives (r2_drive.py:59, r2_empty.py:44-45) [verified]. `annotators=[]` never tried on acoustic [verified-absent].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| mounts m001/m002/m003 positions | `tuple[float,float,float]` [m] def=[unknown — always passed] | (0,-0.05,0), (0,0,0), (0,0.05,0) | 3-element linear array, 5 cm spacing; array geometry sets the echo aperture [probable — mirrored verbatim from NVIDIA `test_acoustic_sensor.py`; only this spacing drilled] |
| mounts rotations | `tuple[float,float,float]` [deg, probable] def=[unknown — always passed] | (0,0,0) x3 | Elements co-aimed [probable — only value drilled] |
| rxGroup g001/g002 receiverIndices | `list[int]` [unitless indices] def=[unknown — always passed] | [0,1] / [1,2] | 2 overlapping receiver pairs; with 3 mounts this yields n=960 = 3 ways x 320 sgw [verified: failures.md R2 notes, verify_r2.py sgw-struct gate] |
| centerFrequency | `float` [Hz] def=[unknown — always passed] | 51200.0 Hz | Transducer center frequency; 51.2 kHz per NVIDIA test [verified]. Other frequencies unexplored [verified-absent] |
| tick_rate | `float` [Hz, probable] def=[unknown — always 30.0] | 30.0 | Acoustic tick rate [verified]. Other rates unexplored [verified-absent] |
| aux_output_level | `str` [unitless] def=[unknown — always "BASIC"] | BASIC | Only level drilled [verified] |
| Targets | 3×`(float x [m], float y [m])` placements + `float` size [m]; def=N/A (scene content) | 3 bare cubes (sizes=1.0) at (3,0)/(5,2)/(4,-2) | Present: smax 4380.8. Removed: smax 1185.5 (3.7x collapse) — the liveness proof [verified: failures.md R2 notes, r2_empty.py] |
| MBVH flag | `bool` boot flag [unitless] def=False (absent) | on (sim booted with it) | Harmless to acoustic; acoustic has NO MBVH requirement per NVIDIA test [verified: failures.md R2 notes]. MBVH-off acoustic not explicitly drilled [verified-absent] |
| NonVisualMaterial | `NonVisualMaterial` handle [unitless] def=N/A (not applied) | NOT applied | Bare cubes echo fine — unlike radar, acoustic needs no RCS material [verified: failures.md R2 notes] |

EKB rules:

- IF building acoustic THEN mirror the NVIDIA test recipe verbatim (3 mounts + 2 rxGroups + 51.2 kHz + tick 30 + BASIC) BECAUSE it went green first try (87/87 frames x 960) [verified: failures.md R2 notes].
- IF proving acoustic liveness THEN remove the geometry and require amplitude collapse (smax > 2000 with targets vs 1186 floor, 2x margins) BECAUSE structure alone (n=960, modality, coords) passes even on an empty scene [verified: failures.md R2 notes, r2_empty.py, verify_r2.py].
- IF reusing the R1 build/drive split for acoustic THEN keep it (prim-only build, single sensor+play in drive) BECAUSE drive reruns are green 3/3 bit-identical (83520 samples each) — F4 reused WITHOUT re-proof [verified: failures.md R2 notes].
- IF gating acoustic metadata THEN gate structure + amplitude + finiteness + frame order, never id/offset values BECAUSE tx/rx/channel ids are all (0,0,0) and timeOffsetNs all zero (degenerate) [verified: failures.md R2 notes, verify_r2.py 12/12].

LIMITS (with cites):

- L1d-1: Bare `Acoustic()` is the ONLY path — no vendor configs exist (`SUPPORTED_ACOUSTIC_CONFIGS` empty) [verified: failures.md R2 notes].
- L1d-2: id/offset metadata degenerate: ids all (0,0,0) save one sample, timeOffsetNs all zero — no usable timing or channel identity [verified: failures.md R2 notes].
- L1d-3: No nested `<path>/sensor` child (unlike Radar.create) — wrap the path directly [verified: r2_drive.py, r2_empty.py].
- L1d-4: F4 birth-wedge avoidance reused without re-proof (drive reruns green, but at-birth wedge never explicitly tested on acoustic) [verified: failures.md R2 notes].

UNKNOWN (all [theoretical] unless noted):

- U1d-1: Mount counts/spacings/rotations besides the 3x5cm linear array; rxGroup topologies besides [0,1]/[1,2]; frequencies besides 51.2 kHz; tick rates besides 30.
- U1d-2: Acoustic on MBVH-off sim (R2 ran MBVH-on) [verified-absent].
- U1d-3: Whether an at-birth AcousticSensor wedges the prim (F4 never re-proven on acoustic).
- U1d-4: `Acoustic`/`AcousticSensor` constructor defaults and full kwarg surface.

### T1e — parse_generic_model_output_data (GMO frame contract)

Functions:

- `parse_generic_model_output_data(raw: GMOHandle | dict) -> GMO frame` where `raw` is `rp_data["GenericModelOutput"]` unwrapped from dict (`raw.get("data")`) if needed [verified: s2_lidar.py:35-40 FULL, r1_drive.py:21-24 FULL, r2_drive.py:23-26 FULL]. `raw: GMOHandle` (opaque annotator payload) or `dict` with `"data"` key; returns frame object (see attrs below).
  - Returns frame object with attrs (union observed across pack, all read-only): `numElements: int` [count]; `x, y, z: wp.array[float]` ([deg, deg, m] spherical on lidar/radar [verified: R3/F5]; acoustic sample coords unit [theoretical]); `scalar: wp.array[float]` [theoretical units — RCS-ish on radar, amplitude on acoustic]; `rv_ms: wp.array[float]` [m/s]; `modality: Modality enum` [unitless]; `elementsCoordsType: CoordsType enum` [unitless]; `numSamplesPerSgw: int` [samples]; `frameStart.timestampNs, frameEnd.timestampNs: int` [ns]; `timeOffsetNs: wp.array[int]` [ns]; `maxRangeM: float` [m]; `minAzRad, maxAzRad, minElRad, maxElRad: float` [rad]; `minVelMps, maxVelMps: float` [m/s]; `scanIdx, cycleCnt, sensorID: int` [unitless] (+ dir-dumped rest in r1_diag3.py:32-33, values uncaptured) [verified: s2/r1/r2 drives FULL, r1_diag3 skim].
  - Per-modality contracts: lidar GMO (x,y,z)=(az,el,r) [verified: R3]; TI radar WORLD SPHERICAL + offset [verified: F5]; acoustic n=960, modality=`Modality.ACOUSTIC`, coords=`CoordsType.NOT_APPLICABLE`, frame ordered t0<t1, all-finite scalar [verified: verify_r2.py].

Knobs: none (pure parser; no params) [verified]. Effect-of-change N/A.

EKB rules:

- IF parsing GMO THEN unwrap dict-or-raw (`isinstance(raw, dict)` -> `raw.get("data")`) and skip `None` BECAUSE the Writer payload shape varies [verified: s2_lidar.py:36-39].
- IF slicing per-element arrays THEN cap `k = min(n, 400)` (radar) / `min(n, 4000)` (acoustic) BECAUSE frames can be large and evidence JSON must stay small [verified: r1_drive.py:35, r2_drive.py:38].
- IF reading header bounds THEN wrap in try/except (getattr per-field) BECAUSE fields exist-but-zero on TI and may be absent elsewhere [verified: r1_drive.py:27-33].

LIMITS (with cites):

- L1e-1: TI header bounds read 0.0 even on detecting frames [verified: failures.md TI limits].
- L1e-2: TI `rv_ms` empty; acoustic `timeOffsetNs` all zero [verified: failures.md TI limits + R2 notes].
- L1e-3: GMO id arrays can exist-but-zero-size [verified: failures.md R4].

UNKNOWN: U1e-1: full attr surface beyond the union above (r1_diag3 dir-dump output uncaptured) [theoretical].

---

## T2 — isaacsim.sensors.experimental.physics (IMU + contact)

DOES: authors physics (non-render) IMU and contact-report sensors and reads dict frames [verified].

Functions (as-called):

- `IMU.create(path: str = [unknown — always passed]) -> IMU` — called as `IMU.create(path="/World/S3Cube/imu")` (s3_run.py:39 FULL), `IMU.create(path="/World/V7Cube/imu")` (v7_run.py:57 FULL) [verified]. `path: str` USD prim path (child of the rigid body). Takes NO `tick_rate` kwarg (installed API drifts from sketches) [verified: discovery.md, TOOLS.md].
- `IMUSensor(imu: IMU) -> IMUSensor` — called as `IMUSensor(imu)` with NO `annotators` kwarg [verified: s3_run.py:40, v7_run.py:58, discovery.md].
- `isens.get_data(read_gravity: bool [unitless] = [unknown — bare call observed]) -> dict[str, wp.array | np.ndarray]` — called with NO args in s3/v7 runs (s3_run.py:46, v7_run.py:72) [verified]. discovery.md:31 ALSO documents `get_data(read_gravity=True) -> dict` [probable — documented in discovery.md but no in-pack call site read shows the kwarg; s3_run/v7_run call bare `get_data()`].
  - Dict keys observed with types: `linear_acceleration: wp.array[float]` [m/s²], `angular_velocity: wp.array[float]` [rad/s, probable], plus orientation/others dumped by `_fields(frame: dict) -> str` (s3_run.py:20-36 prints all keys; resting values: accel [0,0,9.81] exact, angvel 0, orient identity) [verified: s3_run.py, discovery.md].
- `Contact.create(path: str = [unknown — always passed], min_threshold: float [N, probable] = [unknown — always passed], max_threshold: float [N, probable] = [unknown — always passed], radius: float [m; -1 = use body shape] = [unknown — omitted in mega1/2 P4a]) -> Contact` [probable — kwargs observed; defaults unknown]
  - Called as `Contact.create(path="/World/S3Cube/contact", min_threshold=0.0, max_threshold=1e6, radius=-1)` (s3_run.py:41-42 FULL) and V7 twin (v7_run.py:59-60 FULL) [verified]. Called WITHOUT `radius` in `probes/contact_mega1.py:500`, `contact_mega2.py:408,432`, `contact_mega3.py:224` (skim) [probable].
- `ContactSensor(con: Contact | str) -> ContactSensor` — `ContactSensor(con)` with `Contact` object [verified: s3_run.py:43, v7_run.py:61]; `ContactSensor(SENSOR_PATH: str)` with prim-path string in `probes/contact_mega1.py:179`, `contact_mega2.py:144`, `contact_mega3.py:109`, `contact_mega4.py:47` (skim) [probable].
- `csens.get_data() -> dict[str, wp.array | np.ndarray]` — keys with types: `in_contact: array[bool|int]` [unitless flag], `force: array[float]` [N], `time: array[float]` [s, probable], `physics_step: array[int]` [steps], `number_of_contacts: array[int]` [count] [verified: s3_run.py:47-54, discovery.md]. Proven readings: 1 kg -> 9.8098 N n=4; 2 kg -> 19.6201/19.62 N [verified: discovery.md, verify_s3/v7.py].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| IMU `path` | `str` [USD path] def=[unknown — always passed] | `/World/{S3,V7}Cube/imu` (child of rigid body) | IMU rides the body; resting reads gravity vector [0,0,9.81] [verified: s3_run.py, discovery.md] |
| IMU `read_gravity` | `bool` [unitless] def=[unknown — bare call observed] | default (bare call) | Bare `get_data()` returns gravity-inclusive accel (amag 9.81) [verified]. `read_gravity=True` explicitly documented [probable: discovery.md]. False/unset effect unexplored [verified-absent] |
| Contact `path` | `str` [USD path] def=[unknown — always passed] | `/World/{S3,V7}Cube/contact` DIRECT child of the rigid body | Sibling path raises ValueError [verified: failures.md R7, contact_mega3 skim section X] |
| Contact `min_threshold` | `float` [N, probable] def=[unknown — always passed] | 0.0 | Report floor; 0.0 reports resting weight (9.81 N) [verified]. Threshold 1.0 still reported 9.81 awake (filter proof) but sleeping pairs report NOTHING regardless [verified: failures.md R7, contact_mega4 skim section D] |
| Contact `max_threshold` | `float` [N, probable] def=[unknown — always passed] | 1e6 | Report ceiling; only value drilled [verified]. Lower values unexplored [verified-absent] |
| Contact `radius` | `float` [m; -1 = shape] def=[unknown — omitted in mega P4a] | -1 (= shape) | -1 = use the body shape [verified: s3_run.py docstring]. radius 1.0 tried during R7 diagnosis — still zero while asleep (sleep, not radius, was the cause) [verified: failures.md R7]. Radius-unset recreate explored in mega1/2 skim P4a [probable — skim] |
| Scene `physxScene:disableSleeping` | `bool` [unitless] def=False (USD default [theoretical]) | True | THE fix: False/asleep -> in_contact=0/force=0/n=0 on genuinely resting cube (cube sleeps ~20–34 steps after settling); True -> 9.81 N stable; re-enable sleep -> silence (causal proof) [verified: failures.md R7, contact_mega4 skim section C] |
| `PhysxContactReportAPI` threshold on sensed body | `float` [N, probable] def=[unknown] | 0.0, single side suffices | Required alongside no-sleep; ground-report ablation (mega4 skim B) shows single-side suffices [verified: failures.md R7; probable: mega4 skim] |
| Drop + settle steps | `int` [steps/frames] def=N/A (script loop count) | 120–180 steps before read | Settle proves rest contact from motion, not spawn touch (fresh drop baseline, mega1 skim P1) [probable — skim + s3/v7 180-step settles verified] |
| Prime + retry | `int` retries × `int` steps [frames] def=N/A (script logic) | prime read right after play + 3x30-step retry until `in_contact` present | First read can be partial (only time/physics_step keys); retry completes it (force=19.6201 exact 30 steps later) [verified: failures.md R8, v7_run.py:65-78] |

EKB rules:

- IF resting contact reads all-zero with live time/step THEN disable sleeping + set report-API threshold 0.0 + verify direct-child path BECAUSE sleeping pairs emit NOTHING (causal proof: no-sleep -> 9.81 N, sleep back on -> silence) [verified: failures.md R7].
- IF placing a Contact sensor THEN author it as a DIRECT child of the rigid body BECAUSE sibling paths raise ValueError [verified: failures.md R7].
- IF reading contact THEN prime right after play and retry until `in_contact` present BECAUSE the first frame can be partial (KeyError 'in_contact') [verified: failures.md R8].
- IF probing physics-sensor APIs THEN introspect installed signatures first BECAUSE the installed API drifts from sketches (no tick_rate/annotators, dict frames) [verified: discovery.md].
- IF validating contact force THEN drop + settle, then compare against mass·g (1 kg -> 9.8098 N, 2 kg -> 19.6201 N) BECAUSE spawn-touch readings are not rest proofs [verified: discovery.md; probable: mega1 P1 skim].

LIMITS (with cites):

- L2-1: No `tick_rate` (IMU.create) / `annotators` (IMUSensor) kwargs; `get_data()` returns dict [verified: discovery.md].
- L2-2: Sleeping pairs emit NO contact reports [verified: failures.md R7].
- L2-3: Sensor must be DIRECT child of the rigid body [verified: failures.md R7].
- L2-4: First contact read can be partial — prime + retry [verified: failures.md R8].

UNKNOWN (all [theoretical] unless noted):

- U2-1: IMU kwargs besides path; Contact `radius` values besides -1 (1.0 tried only while asleep); thresholds besides 0.0/1.0; `read_gravity` variants beyond documented-True [verified-absent: TOOLS.md Unverified].
- U2-2: GPU-dynamics interplay (mega3 skim G1 toggled it; outcome uncaptured) [theoretical].
- U2-3: Newton-backend contact behavior (mega2 skim PN dumped/switched engines; outcome uncaptured) [theoretical].

---

## T3 — omni.replicator.core (writer-based GMO capture)

DOES: attaches `GenericModelOutput` annotators to sensor render
products and streams frames through custom writers [verified].

Functions (as-called):

- `rep.annotators.get(name: str) -> Annotator` — called as `rep.annotators.get("GenericModelOutput")` with `name: str` [unitless annotator name]; in every GMO `Writer.annotators` list [verified: s2_lidar.py:29 FULL, r1_drive.py:17 FULL, r2_drive.py:19 FULL, diag2_beams.py:28 + all r1/r2 skim writers].
- `class MyWriter(Writer): __init__(self) -> None` sets `self.data_structure: str = "renderProduct"` and `self.annotators: list[Annotator] = [rep.annotators.get("GenericModelOutput")]` [verified: s2_lidar.py:27-29, r1_drive.py:15-17, r2_drive.py:17-19, diag2_beams.py:26-28 FULL].
- `write(self, data: dict[str, dict[str, dict[str, Any]]]) -> None` — `data` maps `"renderProducts" -> {rp_path: str -> {annotator: str -> payload}}`; reads `data["renderProducts"][rp]["GenericModelOutput"]` with dict-or-raw unwrap; guard missing `renderProducts` key (s2/diag2: s2_lidar.py:32-33, diag2_beams.py:31-32) or `.get("renderProducts", {})` (r1/r2: r1_drive.py:20, r2_drive.py:22) [verified: all drives FULL].
- `rep.WriterRegistry.register(writer_cls: type[Writer]) -> None [probable]` — wrapped in try/except printing `REG-NOTE` in r1/r2 drives (re-registration across reruns raises, harmless) [verified: r1_drive.py:50-53 FULL, r2_drive.py:54-57 FULL]. s2_lidar.py registers bare (no guard) [verified: s2_lidar.py:54].
- `sensor.attach_writer(name: str [unitless writer name]) -> None [probable]` — lidar (s2_lidar.py:55), radar (r1_drive.py:67 + all skim drives), acoustic (r2_drive.py:60, r2_empty.py:46) [verified: all drives FULL].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `data_structure` | `str` [unitless] def=[unknown — always "renderProduct"] | "renderProduct" everywhere | Only value drilled [verified]. Other structures unexplored [verified-absent] |
| Writer annotator | `Annotator` from `rep.annotators.get(name: str)`; def=N/A (required list member) | GenericModelOutput | Only annotator drilled on the Writer path [verified] |
| Register guard | `try/except Exception` [unitless control flow] def=N/A (script pattern) | try/except REG-NOTE (r1/r2) vs bare (s2) | Guarded re-register survives drive reruns (5x green); bare works on first run [verified: r1/r2 drives, failures.md F4] |
| Steps per capture | `int` [steps/frames] def=N/A (call arg) | 60 (r1/r2 xcheck), 90 (r2, s4-leg2, ti), 120 (s1/s4), 150 (s2/diag2), 180 (s3/v7) | More steps = more frames (57 frames/60 steps; 87/87; 132258 pts/150 steps); frame yield ≈ steps minus warmup [verified: drives + SKILL.md] |
| `rep.orchestrator.step_async() -> None [theoretical — hung, never observed return]` | `() -> Coroutine` [unitless] def=N/A | tried once in r1_diag2.py:32 | HUNG the bridge (semaphore timeout) during a Hydra storm — never retried, never use in-session [verified: failures.md Ruled OUT] |

EKB rules:

- IF capturing GMO THEN Writer + `update_app_async` stepping, never polling or orchestrator steps BECAUSE polling drops/dupes and orchestrator hung the bridge [verified: discovery.md, failures.md Ruled OUT].
- IF registering a Writer in a re-runnable drive THEN guard with try/except REG-NOTE BECAUSE re-registration raises and reruns must stay green [verified: r1_drive.py, r2_drive.py].
- IF the writer sees no `renderProducts` key THEN return/skip silently BECAUSE warmup ticks can deliver empty payloads [verified: s2_lidar.py:32-33].

LIMITS (with cites):

- L3-1: `rep.orchestrator.step_async()` in-session hung the bridge — never retried [verified: failures.md Ruled OUT].
- L3-2: `annotators=[]` vs `["generic-model-output"]` did not fix silence alone [verified: failures.md Ruled OUT].

UNKNOWN: U3-1: orchestrator stepping outside a Hydra storm (hung once, never retried) [verified-open]. U3-2: data structures besides "renderProduct" [theoretical].

---

## T4 — isaacsim.core.experimental.utils.app (sim transport)

DOES: plays/stops the timeline and steps the app so sensors tick and writers fire [verified].

Functions (as-called):

- `app_utils.play(commit: bool [unitless] = [unknown — True or omitted]) -> None` — called as `play(commit=True)` (s1_cap.py:56, s2_lidar.py:56, s3_run.py:44, s4_run.py:61, v7_run.py:62, diag2_beams.py:83) and bare `play()` (r1_drive.py:68, r2_drive.py:61, r1_ti.py:50, r1_mat.py:50, r1_xcheck.py:44, r2_empty.py:47 + all skim drives) [verified]. Both forms tick sensors + writers [verified]. `commit` semantics unexplored [verified-absent].
- `app_utils.stop() -> None` — called at end of r1/r2 drives (r1_drive.py:70, r2_drive.py:63) + skim drives; NOT called in s1–s4/v7 runs (bridge session ends instead) [verified].
- `await app_utils.update_app_async(steps: int [steps/frames]) -> None` — 10–180 steps per call across pack; THE stepping primitive (60–180 per drill) [verified: s1_cap.py:59, s2_lidar.py:57, s3_run.py:45, s4_run.py:64/70, v7_run.py:66/77, r1_drive.py:69, r2_drive.py:62, diag2_beams.py:84, all run/drive scripts].
- `app_utils.update_app(steps: int [steps/frames]) -> None [probable]` sync stepping — contact_mega1.py:245/264/360/444/448/546, contact_mega2.py:214/229/276/350/354/476, contact_mega3.py:138/156/186/354, contact_mega4.py:69/86/121/123/125/141/155/170/180/182 skim only [probable — skim].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `play(commit=True)` vs `play()` | `commit: bool` [unitless] def=[unknown — True or omitted] | both used | No behavioral difference observed (both tick + fire writers) [probable — never A/B-compared] |
| `update_app_async` steps | `steps: int` [steps/frames] def=N/A (required arg) | 10–180 | Frame/point yield scales with steps (57 frames/60 steps; 150 steps -> 132k lidar pts) [verified]. Too few = no/warmup-only frames [probable] |
| `stop()` | `() -> None` [unitless] def=N/A | end of r1/r2 drives | Returns stage to stopped state so the next build/drive can author cleanly [probable]. Omitting it (s1–v7) is fine when the session ends [verified] |

EKB rules:

- IF driving any sensor THEN `play` + `update_app_async(steps=N)` + (optionally) `stop` BECAUSE this is the only stepping path proven across all 7 drills [verified: all run/drive scripts].
- IF re-running a drive THEN stop first / ensure stopped state BECAUSE live re-authorship emits nothing until re-parse [verified: failures.md R5].

LIMITS: L4-1: `play(commit: bool)` semantics unknown; both spellings work [probable]. L4-2: sync `update_app` only in skim probes, never a gated drill [probable].

UNKNOWN: U4-1: `commit=True` vs `commit=False` vs omitted — meaning and effect [theoretical]. U4-2: minimum warmup steps per modality [theoretical].

---

## T5 — omni.usd + pxr (UsdGeom/UsdLux/UsdPhysics/PhysxSchema/Gf) — scene authoring

DOES: builds drill scenes (ground, cubes, domes, physics) and moves/queries prims [verified].

Functions (as-called):

- `omni.usd.get_context() -> UsdContext` then `.get_stage() -> Usd.Stage` — every build/run/drive script [verified: e.g. s1_build.py:9, r1_build.py:17, r1_drive.py:57].
- `stage.GetPrimAtPath(path: str | Sdf.Path) -> Usd.Prim` (+ `prim.IsValid() -> bool`), `stage.RemovePrim(path: str | Sdf.Path) -> bool [probable]` — cleanup preamble in every build script (10–20 paths each) [verified: s1/s2/s3/s4/v7_build.py FULL, r1/r2_build.py FULL; e.g. s1_build.py:21-23, r1_build.py:20-21, contact_mega3.py:227 uses `Sdf.Path`].
- `prim.GetChildren() -> list[Usd.Prim]` — r1_drive child search for OmniRadar [verified: r1_drive.py:59 FULL]; r1_scene world inventory [probable — r1_scene.py:14 skim].
- `prim.GetTypeName() -> str` — r1_drive (`== "OmniRadar"`, r1_drive.py:60), r1_attrs.py:5, r1_scene.py:15, r1_bbox.py:7, r1_ti.py:18, r2_build.py:37 skim [verified].
- `prim.GetAttributes() -> list[Usd.Attribute]` / `prim.GetAttribute(name: str) -> Usd.Attribute` / `prim.GetAuthoredAttributes() -> list[Usd.Attribute]` / `prim.GetAppliedSchemas() -> list[str]` — attr dumps (r1_attrs.py:6, r1_pose2.py:13, diag1_inventory.py:39/46/59 skim), disableSleeping set (s3_build.py:27-28, v7_build.py:27-28 FULL), debug-force set (r1_force.py:13-16 skim) [verified]. `attr.Get() -> Any`, `attr.Set(value: Any) -> None`, `attr.GetName() -> str` as used at each site.
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: str) -> UsdGeom.Cube` + `.GetSizeAttr() -> Usd.Attribute` + `.Set(size: float [m]) -> None` called with 1.0/1.2 — s1–s4 (1.0: s1_build.py:30-31, s2_build.py:32-33, s3_build.py:35-36, s4_build.py:27-28), v7 (1.2: v7_build.py:35-36) FULL [verified]. NOTE: USD `UsdGeom.Cube` size attr is the true edge length — unlike experimental `Cube` scales (T6) [verified: failures.md F5 contrast].
- `UsdGeom.Plane.Define(stage: Usd.Stage, path: str) -> UsdGeom.Plane` + `.CreateWidthAttr() -> Usd.Attribute` / `.CreateLengthAttr() -> Usd.Attribute` + `.Set(width: float [m]) -> None` called with 20.0 — grounds [verified: s1_build.py:27-29, s2_build.py:29-31, s3_build.py:31-33, s4_build.py:24-26, v7_build.py:31-33 FULL]. (As-called: `CreateWidthAttr()` takes NO arg in pack; width passed via `.Set(20.0)`.)
- `UsdGeom.Xformable(prim: Usd.Prim).AddTranslateOp() -> UsdGeom.XformOp` + `.Set(value: Gf.Vec3d [m]) -> None` — placement [verified: s1_build.py:32, s2_build.py:34, s3_build.py:37, s4_build.py:29, v7_build.py:37 FULL]; live slide in s4_run via `xp.GetOrderedXformOps() -> list[UsdGeom.XformOp]` + `op.GetOpType() -> UsdGeom.XformOp.Type` + `op.Set(Gf.Vec3d(0,1.0,0.5) [m]) -> None` on the translate op [verified: s4_run.py:66-69 FULL].
- `UsdLux.DomeLight.Define(stage: Usd.Stage, path: str) -> UsdLux.DomeLight` + `.GetIntensityAttr() -> Usd.Attribute` + `.Set(intensity: float [theoretical units — renderer exposure scale]) -> None` — s1–s4 @400 (s1_build.py:25-26 et al), v7 @300 (v7_build.py:29-30) [verified: builds FULL, verify_v7.py gates dome=300].
- `UsdPhysics.Scene.Define(stage: Usd.Stage, path: str) -> UsdPhysics.Scene` + `.CreateGravityDirectionAttr() -> Usd.Attribute` + `.Set(dir: Gf.Vec3f [unitless direction]) -> None` called with (0,0,-1) + `.CreateGravityMagnitudeAttr() -> Usd.Attribute` + `.Set(g: float [m/s²]) -> None` called with 9.81 — s3_build.py:23-25, v7_build.py:24-26 FULL [verified].
- `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI` / `UsdPhysics.CollisionAPI.Apply(prim: Usd.Prim) -> UsdPhysics.CollisionAPI` / `UsdPhysics.MassAPI.Apply(prim: Usd.Prim) -> UsdPhysics.MassAPI` + `.GetMassAttr() -> Usd.Attribute` + `.Set(mass: float [kg]) -> None` called with 1.0/2.0 — s3 (1 kg: s3_build.py:38-40), v7 (2 kg: v7_build.py:38-40) [verified: s3/v7_build.py FULL, verify_s3/v7.py force gates].
- `PhysxSchema.PhysxContactReportAPI.Apply(prim: Usd.Prim) -> PhysxSchema.PhysxContactReportAPI` + `PhysxSchema.PhysxContactReportAPI(prim: Usd.Prim).CreateThresholdAttr(threshold: float [N, probable] = 0.0) -> Usd.Attribute` — s3_build.py:41-42, v7_build.py:41-42 FULL [verified: failures.md R7].
- `stage.GetPrimAtPath(path: str) -> Usd.Prim` + `.GetAttribute("physxScene:disableSleeping") -> Usd.Attribute` + `.Set(value: bool [unitless]) -> None` called with True — s3_build.py:27-28, v7_build.py:27-28 FULL [verified: failures.md R7].
- `UsdGeom.XformCache().GetLocalToWorldTransform(prim: Usd.Prim) -> Gf.Matrix4d` + `.ExtractTranslation() -> Gf.Vec3d [m]` / `.ExtractRotation() -> Gf.Rotation` (+ `.GetQuat() -> Gf.Quatd [probable — exact precision class uncaptured]` with `.GetReal() -> float`, `.GetImaginary() -> Gf.Vec3 [probable]`) — r1_pose.py:6-10, r1_pose2.py:6-11 skim (pose/quat of nested sensor), diag1_inventory.py:29-31 skim [probable — skim].
- `UsdGeom.Imageable(prim: Usd.Prim).ComputeWorldBound(time: Usd.TimeCode | int | float [s], purpose: str) -> UsdGeom.BBox3d` + `.ComputeAlignedBox() -> Gbx.Range3d` + `.GetMin()/.GetMax() -> Gf.Vec3d [m]` — r1_bbox.py:8-11 skim (true 4 m cube bbox 3.0–7.0; called as `ComputeWorldBound(0, "default")`) [verified: failures.md F5]; `UsdGeom.BBoxCache(time: Usd.TimeCode, includedPurposes: list[str], useExtentsHint: bool) -> UsdGeom.BBoxCache` variant in diag1_inventory.py:8 (`includedPurposes=["render"]`) / diag2_beams.py:54 (`includedPurposes=["default","render"], useExtentsHint=True`) skim (purpose "render" alone returned EMPTY boxes; default+render works) [probable — skim].
- `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` / `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` [units per use: m for placements, unitless for gravity dir] — placements, gravity dir [verified: s1_build.py:32, s3_build.py:24/37, s4_run.py:69].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| Cube size attr | `float` [m edge length] def=[unknown — always Set] | 1.0 (s1–s4), 1.2 (v7) | True edge length; depth/contact gates scale with it (v7 dctr 3.602, force 19.62) [verified: builds + verifiers] |
| Cube placement | `Gf.Vec3d` [m] def=[unknown — always Set] | (0,0,0.5/0.6/0.7), (2,0,0.5) | Known geometry that all gates derive from; s3 spawns at z=0.6 then drops to rest 0.5 [verified: builds] |
| Dome intensity | `float` [theoretical units] def=[unknown — always Set] | 400 (s1–s4), 300 (v7) | Lights rgb (rgbmean gate 10–220); v7's 300 is an EXAM novelty, still passes [verified: verify_s1/v7.py] |
| Gravity magnitude | `float` [m/s²] + `Gf.Vec3f` dir [unitless]; def=[unknown — always Set] | 9.81, dir (0,0,-1) | Sets IMU amag (9.81) and contact force (mass·9.81) [verified: verify_s3/v7.py] |
| Mass | `float` [kg] def=[unknown — always Set] | 1.0 (s3), 2.0 (v7) | Force scales linearly (9.8098 N / 19.6201 N) [verified: discovery.md] |
| Live slide of NON-sensor cube | `Gf.Vec3d` target [m] def=N/A (one-shot op.Set) | s4 leg 2 | Works: depth tracks exactly (delta 1.068) [verified: s4_run.py, verify_s4.py] |
| Live slide of RTX SENSOR | `float` z [m] 1.5->3.0 def=N/A (probe move) | S2Lidar 1.5->3.0 | Breaks output (EMPTY 60 steps) until re-parse [verified: failures.md R5] |

EKB rules:

- IF authoring drill geometry THEN clean all known paths first (RemovePrim preamble) BECAUSE stale prims from prior drills pollute gates [verified: every build script].
- IF querying geometry for a gate THEN query the LIVE bbox (ComputeWorldBound/Imageable), never assumed sizes BECAUSE assumed sizes caused the F5 "offset wall" miss [verified: failures.md F5].
- IF using BBoxCache THEN include purposes ["default","render"] BECAUSE "render" alone returned empty boxes [probable: diag2_beams skim header].
- IF sliding anything live THEN slide only NON-sensor prims BECAUSE sensor slides break bindings (R5) while object slides track exactly (S4) [verified].

LIMITS (with cites):

- L5-1: Virgin boot ships `/Environment/defaultLight` (DistantLight 3000) — ambient-floor suspect; no `/PhysicsScene` at boot [verified: discovery.md].
- L5-2: Live sensor moves break output; live object moves fine [verified: failures.md R5, s4_run.py].

UNKNOWN: U5-1: Dome intensities besides 300/400 vs rgb-gate margins [theoretical]. U5-2: Gravity/mass values besides drilled (linearity beyond 1–2 kg unproven) [theoretical].

---

## T6 — isaacsim.core.experimental.objects (Cube helper)

DOES: one-line rigid cube authoring for radar/acoustic targets [verified].

Functions (as-called):

- `Cube(path: str, positions: np.ndarray[(3,), float64] [m] = [unknown — always passed except path-only re-wrap], scales: np.ndarray[(3,), float64] [unitless multiplier on 2 m default] = [unknown — passed in r1/r1x only], sizes: float [m] = [unknown — passed in r2 only]) -> Cube` [probable — kwargs observed; defaults unknown]
  - `Cube("/World/R1Cube", positions=np.array([5,0,0]), scales=np.array([2,2,2]))` (r1_build.py:22-23 FULL) [verified].
  - `Cube("/World/R1XCube", positions=np.array([5.0, 0.0, 0.0]), scales=np.array([2.0, 2.0, 2.0]))` same shape (r1_xcheck.py:16-17 FULL) [verified].
  - `Cube("/World/R2T%d", sizes=1.0, positions=np.array([x,y,0.0]))` (r2_build.py:15-17 FULL) [verified].
  - `Cube("/World/R1Cube")` path-only re-wrap for material application (r1_mat.py:12 FULL, r1_scene.py:51 skim) [verified].
- `cube.apply_visual_materials(mat: NonVisualMaterial) -> None [probable]` — applies NonVisualMaterial (r1_build.py:28 FULL, r1_mat.py:15 FULL, r1_scene.py:54 skim) [verified].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `scales` | `np.ndarray[(3,)]` [unitless ×2 m] def=[unknown — r1/r1x only] | [2,2,2] | MULTIPLIES the 2 m default -> 4 m cube (bbox 3.0–7.0), NOT 2 m [verified: failures.md F5, r1_bbox skim]. The single most expensive misread in the pack (0/28 on-face until corrected) |
| `sizes` | `float` [m] def=[unknown — r2 only] | 1.0 | R2 cubes: 1 m (acoustic targets) [verified: r2_build.py]. sizes-vs-scales interaction unexplored [verified-absent] |
| `positions` | `np.ndarray[(3,)]` [m] def=[unknown — omitted only in path-only re-wrap] | [5,0,0], [(3,0),(5,2),(4,-2)] | Target placement; radar face plane x=3.0 derives from center 5.0 minus half-edge 2.0 [verified: verify_r1.py] |
| path-only re-wrap | `path: str` only [USD path] def=N/A (re-wrap form) | `Cube(path)` | Re-attaches to an existing prim for material ops without re-authoring [verified: r1_mat.py] |

EKB rules:

- IF using experimental `Cube` THEN verify the live bbox before gating BECAUSE `scales` multiplies the 2 m default (scales=2 -> 4 m cube) [verified: failures.md F5].
- IF radar targets need RCS THEN `Cube(path)` re-wrap + `apply_visual_materials(NonVisualMaterial)` BECAUSE build deletes the cube, so material must be (re-)applied every rebuild [verified: failures.md F3].

LIMITS (with cites):

- L6-1: `scales=[2,2,2]` = 4 m cube — query the live bbox [verified: failures.md F5].

UNKNOWN: U6-1: `sizes` x `scales` combined semantics; defaults of either [theoretical]. U6-2: Whether path-only `Cube(path)` on a missing path creates or raises [theoretical].

---

## T7 — isaacsim.core.experimental.materials (NonVisualMaterial)

DOES: gives prims radar cross-section so RTX radar returns detections [verified].

Functions (as-called):

- `NonVisualMaterial(path: str, bases: str [unitless preset] = [unknown — always "aluminum"], coatings: str [unitless preset] = [unknown — always "paint"], attributes: str [unitless preset] = [unknown — always "emissive"]) -> NonVisualMaterial` [probable — kwargs observed; defaults unknown]
  - Called as `NonVisualMaterial("/World/R1Cube/material", bases="aluminum", coatings="paint", attributes="emissive")` in r1_build.py:26-27 FULL, r1_mat.py:13-14 FULL, r1_scene.py:52-53 skim [verified]. `path: str` USD material path (positional).
- `cube.apply_visual_materials(mat: NonVisualMaterial) -> None [probable]` — see T6 [verified: r1_build.py:28, r1_mat.py:15].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `bases` | `str` [unitless preset] def=[unknown — always "aluminum"] | "aluminum" | With: 28/frame, 25 on-face (89%). Without (bare): 5 ghost dets/frame only [verified: failures.md F3, verify_r1.py]. Other bases unexplored [verified-absent] |
| `coatings` | `str` [unitless preset] def=[unknown — always "paint"] | "paint" | Only value drilled [verified]. Effect unexplored [verified-absent] |
| `attributes` | `str` [unitless preset] def=[unknown — always "emissive"] | "emissive" | Only value drilled [verified]. Effect unexplored [verified-absent] |
| Re-application | call cadence [per rebuild] def=N/A (script order) | every rebuild | Build deletes the cube, so material MUST be re-applied every rebuild (r1_build does it inline) [verified: failures.md F3] |
| Acoustic targets | `NonVisualMaterial` handle [unitless] def=N/A (not applied) | material NOT applied | Bare cubes echo fine — acoustic does NOT need NonVisualMaterial [verified: failures.md R2 notes] |

EKB rules:

- IF radar sees only 5 bit-identical off-geometry dets THEN apply NonVisualMaterial aluminum to the target BECAUSE bare geometry is radar-invisible (~zero RCS); the 5 ghosts are the stable floor, not the target [verified: failures.md F3].
- IF rebuilding a radar scene THEN re-apply the material in the same build script BECAUSE build deletes the cube (material dies with it) [verified: failures.md F3].
- IF the target is acoustic-only THEN skip the material BECAUSE bare cubes echo fine [verified: failures.md R2 notes].

LIMITS (with cites):

- L7-1: Without material: 5 ghosts/frame; with: 28/frame ~89% on-face [verified: failures.md F3].
- L7-2: Must be re-applied every rebuild [verified: failures.md F3].
- L7-3: Acoustic does NOT need it [verified: failures.md R2 notes].

UNKNOWN: U7-1: bases besides aluminum; coatings/attributes effects; RCS magnitude scaling [theoretical].

---

## T8 — carb.settings (renderer flag read)

DOES: reads the boot-time motion-BVH flag the radar drill requires [verified].

Functions (as-called):

- `carb.settings.get_settings() -> carb.Settings` [verified: r1_build.py:10 FULL, r1_diag.py:9, r1_probe.py:9, r1_ext.py:12 skim].
- `settings.get(key: str) -> Any` — called with `key: str = "/renderer/raytracingMotion/enabled"` returning `bool` [unitless] (r1_build.py:14-15 FULL asserts truthy; r1_diag.py:8-9, r1_probe.py:10 skim print it); other keys in r1_ext.py:13-17 return `str | int | bool [probable]` (values uncaptured) [verified].
- `settings.set(key: str, value: Any) -> None [theoretical — signature inferred, NEVER called in pack]` — setting MBVH live is FORBIDDEN (wedges Hydra) [verified: failures.md F1]. No call site exists; param names `key`/`value` [theoretical].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| `/renderer/raytracingMotion/enabled` read | `bool` [unitless] def=False at boot unless flag passed [verified] | True (boot flag) | r1_build ASSERTS it and aborts otherwise ("reboot with MBVH flag") [verified: r1_build.py:14-15]. False = radar cannot detect (F1 recovery is the boot flag) [verified: failures.md F1] |
| live `set(key: str, value: bool)` | `(str, bool)` [unitless] def=N/A (never called) | NEVER (forbidden) | Wedges Hydra: engine-recreation storm, viewport dead, 1.4 MB log/10 s, bridge timeouts, sim killed [verified: failures.md F1] |

EKB rules:

- IF a radar build starts THEN assert boot-time MBVH, never set it BECAUSE the live flip kills the renderer while the boot flag works [verified: failures.md F1].
- IF diagnosing radar silence THEN print (not set) the MBVH setting first BECAUSE it is the cheapest discriminator (r1_diag/r1_probe pattern) [verified: r1_diag.py/r1_probe.py skim].

LIMITS (with cites): L8-1: NEVER set MBVH live on a running renderer [verified: failures.md F1].

UNKNOWN: U8-1: Whether MBVH can be flipped live on an empty pre-render stage in this build (Kit-test suites do; pack never tries) [theoretical].

---

## T9 — Boot CLI flag `--/renderer/raytracingMotion/enabled=true`

DOES: enables motion raytracing (MBVH) at sim boot so RTX radar detects [verified].

Functions: N/A (CLI arg, not a call — no signature to type). Verified live as `motion-bvh: True` at boot [verified: r1_build.py:14, SKILL.md Prerequisites]. Flag value type: `bool` (`true`/`false` CLI token) [verified].

Knobs + effect-of-change:

| Knob | Type / unit / default | Drilled value | Effect of change |
|---|---|---|---|
| flag present | `bool` CLI token [unitless] def=false (absent) | true | Radar detects (87/87 x 28) [verified: failures.md F1/F2]. Harmless to acoustic [verified: failures.md R2 notes] and to depth/lidar/IMU/contact (no flag needed, none harmed) [probable — base drills ran on flagged sims without issue] |
| flag absent | `bool` CLI token [unitless] def=false (absent) | (radar fails) | Radar path unproven without it; r1_build refuses to run [verified: r1_build.py:15] |

EKB rules: IF running ANY radar drill THEN boot with the flag BECAUSE it is the only proven way to enable motion-BVH (live flip wedges Hydra) [verified: failures.md F1].

LIMITS (with cites): L9-1: Required for radar; harmless to acoustic (no MBVH requirement per NVIDIA test) [verified: failures.md F1 + R2 notes].

UNKNOWN: U9-1: MBVH-off acoustic (not explicitly drilled); MBVH effect on lidar sweep anomaly R6 [theoretical].

---

## T10 — isaacsim.core.simulation_manager (probes only)

DOES: interrogates sim backend/dt during contact diagnosis [probable — skim].

Functions (as-called in skim): `SimulationManager.get_physics_dt() -> float [s, probable]`, `SimulationManager.get_backend() -> str [probable]`, `SimulationManager.is_simulating() -> bool [probable]` (contact_mega1.py:49/138/532, contact_mega2.py:49/129, contact_mega3.py:92 skim) [probable — skim, outputs uncaptured; return types inferred from names/use in log strings]. All take zero params.

Knobs: none (read-only interrogation) [probable].

EKB rules: IF contact misbehaves across engine switches THEN dump dt/backend alongside the scene-solver attrs BECAUSE backend/dt is the cheapest engine discriminator (mega3 E0 pattern) [probable — skim].

LIMITS: L10-1: Diagnostic scaffolding only, not a gated drill contract [verified: TOOLS.md Unverified].

UNKNOWN: U10-1: All behaviors (outputs uncaptured) [theoretical].

---

## T11 — omni.physx (probes only)

DOES: low-level physics interrogation during contact diagnosis [probable — skim].

Functions (as-called in skim): `import omni.physx as _px` then `_px.get_physx_interface() -> PhysXInterface [probable]` (contact_mega1.py:152-153), `px.get_rigidbody_transformation(path: str [USD path]) -> Gf.Matrix4d | tuple [theoretical — output uncaptured]` and `px.get_rigidbody_linear_velocity(path: str [USD path]) -> Gf.Vec3d | tuple [m/s, theoretical — output uncaptured]` (contact_mega1.py:154-156, called as `getattr(px, fn)(CUBE)` with `CUBE: str` prim path in a loop) [probable — skim, outputs uncaptured].

Knobs: none observed (read-only interrogation; no params set) [probable]. EKB: none (no gated behavior).

LIMITS: L11-1: Diagnostic scaffolding only [verified: TOOLS.md Unverified].

UNKNOWN: U11-1: Everything (calls + effects uncaptured) [theoretical].

---

## T12 — omni.kit.app (r1_ext, skimmed)

DOES: app-handle access in the radar extension probe [probable — skim].

Functions (as-called in skim): `omni.kit.app.get_app() -> KitApp [probable]` + `.get_extension_manager() -> ExtensionManager [probable]` + `em.is_extension_enabled(name: str [unitless extension name]) -> bool [probable]` for `omni.sensors.nv.radar/lidar/acoustic`, `isaacsim.sensors.experimental.rtx`, `omni.replicator.core` (r1_ext.py:6-11); plus `settings.get(key: str) -> Any` reads of `/renderer/active`, `/rtx/rendermode`, `/renderer/raytracingMotion/enabled`, `/app/renderer/activeRaytracer` (r1_ext.py:12-17) [probable — `radac/scripts/r1_ext.py` skim, output uncaptured].

Knobs: none (read-only) [probable].

EKB rules: IF radar is silent AND MBVH is on AND config/material/wrap are right THEN check backend-extension enablement via this probe BECAUSE a disabled `omni.sensors.nv.*` backend would explain pipeline-dead silence [theoretical — probe exists, no silence was ever attributed to it].

LIMITS: L12-1: Diagnostic scaffolding only [verified: TOOLS.md Unverified].

UNKNOWN: U12-1: All outputs uncaptured; no gate depends on it [theoretical].

---

## T13 — warp (GPU-array unwrap)

DOES: sensor frames arrive as `wp.array`; drills unwrap to numpy [verified].

Functions (as-called): `isinstance(d: Any, wp.array) -> bool` then `d.numpy() -> np.ndarray` for warp arrays; `np.asarray(a: ArrayLike, dtype: np.dtype = float) -> np.ndarray` fallback for non-warp [verified: s1_cap.py:41-45 (`_grab`), s2_lidar.py:20-23 (`_w`), s3_run.py:14-17, s4_run.py:42-46, v7_run.py:43-46 FULL]. Full helper shape: `_w(a: wp.array | np.ndarray | list) -> np.ndarray [dtype float]` (s2_lidar.py:20-23, s3_run.py:14-17, v7_run.py:43-46).

Knobs: none [verified]. Effect-of-change N/A.

EKB rules: IF reading ANY sensor frame THEN unwrap list/tuple -> wp.array -> numpy via the `_w`/`_grab` pattern BECAUSE frames arrive in all three shapes across modalities [verified: all run scripts].

LIMITS: none observed. UNKNOWN: none material (stdlib-level unwrap) [theoretical-trivial].

---

## T14 — numpy (frame math)

DOES: pose math, spherical->world conversion, gate statistics [verified].

Functions (as-called): `np.linalg.norm(x: np.ndarray) -> float`, `np.cross(a: np.ndarray[(3,)], b: np.ndarray[(3,)]) -> np.ndarray[(3,)]`, `np.column_stack(tup: sequence[np.ndarray]) -> np.ndarray`, `np.concatenate(arrays: sequence[np.ndarray]) -> np.ndarray`, `np.trace(m: np.ndarray) -> float`, `np.radians(x: float [deg]) -> float [rad]` / `np.cos/sin(x: float [rad]) -> float`, `np.asarray(a: ArrayLike, dtype: np.dtype = float) -> np.ndarray`, reductions `arr.min()/max()/mean()/sum() -> float`, `np.degrees(x: float [rad]) -> float [deg]` / `np.arctan2(y: float, x: float) -> float [rad]` / `np.arcsin(x: float) -> float [rad]` / `np.sqrt(x: float) -> float` (diag2_beams.py:88-95 skim) [verified: s1_cap.py:15-19, s2_lidar.py:58-70, s4_run.py:14-20, v7_run.py:14-21, r1_drive.py:36-46, r2_drive.py:38-50 FULL].

Knobs: conversion formulas are load-bearing and modality-specific [verified]:
- Lidar/radar world mapping: `wx: float [m] = px: float [m] + r: float [m]·cos(el: float [rad])·cos(az: float [rad])`, `wy = py + r·cos(el)·sin(az)`, `wz = pz + r·sin(el)` with az/el in RADIANS [verified: s2_lidar.py:59-64, verify_r1.py:23-27].
- Look-at quat: `_mat_to_wxyz(m: np.ndarray[(3,3), float] [unitless]) -> list[float] len 4 [w,x,y,z quat, unitless]` trace-branch helper (s1/s4/v7, duplicated) [verified: s1_cap.py:22-38].

EKB rules: IF converting GMO THEN radians first, then cos/sin, then add the SENSOR offset BECAUSE degrees-in/trig and missing-offset are the two classic mapping bugs (F5) [verified: s2_lidar.py, verify_r1.py, failures.md F5].

LIMITS: none (math lib). UNKNOWN: none material [theoretical-trivial].

---

## T15 — Bridge sender (probes/sync_send.py, skimmed)

DOES: sync localhost sender for the Isaac Sim python_server wire protocol [verified — skim].

Functions: `socket.create_connection(address: tuple[str, int] (host, port), timeout: float [s]) -> socket.socket` (sync_send.py:17) + `s.settimeout(timeout: float [s]) -> None` (:18) + `s.sendall(payload: bytes) -> None` (:19) + `s.shutdown(how: int = socket.SHUT_WR) -> None` (:20) + read-all `s.recv(bufsize: int = 65536 [bytes]) -> bytes` loop (:23-26) + `s.close() -> None` (:27) + `json.loads(data: str) -> dict` (:29); payload `str` wraps source as `async def _isolated_script(): ...; await _isolated_script()` (:14-15); argv `host: str = sys.argv[1]`, `port: int = int(sys.argv[2])`, `timeout: float [s] = float(sys.argv[3])`, `path: str = sys.argv[4]` (:11); `sys.exit(code: int) -> NoReturn` with exit 0 iff `status == "ok"` (:31) [verified: `base/scripts/probes/sync_send.py` skim — full 973-byte file read].

Knobs + effect-of-change:

| Knob | Type / unit / default | Effect of change |
|---|---|---|
| sync socket vs asyncio | `socket.socket` blocking [unitless] def=N/A (stdlib default) | Sync avoids the asyncio proactor self-pipe block in sandboxed shells [verified: sync_send.py docstring] |
| `shutdown(SHUT_WR)` after send | `s.shutdown(how: int = SHUT_WR) -> None` [unitless] def=N/A | Signals end-of-source so the server executes and replies; without it the read blocks [probable — wire-protocol semantics] |
| `timeout` / `port` / `recv bufsize` | `timeout: float` [s], `port: int` [unitless], `bufsize: int` [bytes] def=N/A (argv/literal) | CLI-driven; `recv(65536)` chunks until empty [verified: sync_send.py:11,23] |

EKB rules: IF sending in-sim scripts from a sandboxed shell THEN use the sync sender BECAUSE asyncio's proactor pipe is blocked there [verified: sync_send.py docstring].

LIMITS: none observed. UNKNOWN: none material [theoretical-trivial].

---

## T16 — Local verifiers (stdlib json/re/math/sys)

DOES: gate drill evidence JSON files against geometry-derived thresholds (run locally, not in sim) [verified].

Functions (as-called; all FULL reads except base verifiers skim — but each is <40 lines and was read in full text via batch output). Local helper shape (verify_r1.py:19-20, verify_r2.py:12-13): `gate(name: str, ok: bool [unitless], detail: str = "") -> None`; geometry helpers (verify_r1.py:23-32): `to_world(az: float [deg], el: float [deg], r: float [m]) -> tuple[float, float, float] [m]` and `on_face(p: tuple[float, float, float] [m]) -> bool`; evidence load `json.load(open(EV: str [path])) -> dict`.

- `verify_s1.py`: 5 gates (rgb lit 10–220 [unitless 0–255], rgbmax>50, dshape=[240,320,1] [pixels], dctr≈3.738±0.15 [m], all-cube spread<0.5 [m]) on `base/evidence/s1_cap.json` [verified].
- `verify_s2.py`: 5 gates (frames>=1 [count], points>=1000 [count], ontop>=0.95 [fraction], rmin≈1.93±0.15 [m], rmax<3.0 [m]) on `s2_lidar.json` [verified].
- `verify_s3.py`: 5 gates (amag≈9.81±0.3 [m/s²], wmag<0.2 [rad/s, probable], in_contact True [flag], force≈9.81±1.0 [N], ncontacts>=1 [count]) on `s3_run.json` [verified].
- `verify_s4.py`: 3 gates (d1≈3.738±0.15 [m], d2≈4.806±0.2 [m], delta in 0.9–1.25 [m]) on `s4_run.json` [verified].
- `verify_v7.py`: 9 gates (EXAM dome/size/mass exact + depth/IMU/contact like s1–s3 with 2 kg force≈19.62±1.5 [N]) on `v7_build.json` + `v7_run.json` [verified].
- `verify_r1.py` FULL: 7 gates (frames>=10 [count], all-nonempty, count==28 [count], on-face>=80% [fraction], 5/5 ghosts ±0.02 ([deg,deg,m] per ghost axis), scalar all-nonzero len==n) on `radac/evidence/r1_gmo.json`; geometry truth face x=3.0 [m] |y|,|z|<=2 [m] tol 0.15/2.1 [m] [verified].
- `verify_r2.py` FULL: 12 gates (frames>=10 [count], all-nonempty, count-stable 960 [count], count==960, sgw-struct n%sgw==0 [samples], modality ACOUSTIC, coords NOT_APPLICABLE, frame-ordered t0<t1 [ns], finite==1.0 [fraction], echo-live smax>2000 [amplitude units], offsets-nonneg [ns], id-arrays len==n) on `r2_gmo.json` [verified].

Knobs: gate thresholds ARE the knobs (tolerances above: `float`/`int` per gate, units as annotated, defaults N/A — literals); tightening beyond proven margins (1 mm center-ray, 2x amplitude, ±0.02 ghost) risks false reds [probable].

EKB rules: IF writing a new verifier THEN derive every threshold from queried geometry + observed margins (never round hopes) BECAUSE R2/F5 both burned assumed gates [verified: failures.md R2/F5].

LIMITS: L16-1: Base verifiers grep `*-REPORT` stdout lines inside evidence JSON (`["output"]`), so REPORT-format changes break them [verified: verifier sources]. L16-2: r1/r2 verifiers read structured `r*_gmo.json` (frames/nonempty/sample) written by the drives [verified].

UNKNOWN: none material [theoretical-trivial].

---

## T17 — Upstream oracles (referenced, not in pack)

DOES: NVIDIA ground-truth recipes the drills mirror [verified: SKILL.md References].

Functions (referenced, never executed by the pack — no signatures to type): `$ISAAC_SIM_DIR/standalone_examples/.../inspect_radar_gmo.py`, `inspect_acoustic_gmo.py`, `test_radar_sensor.py`, `test_acoustic_sensor.py` [verified].

Knobs + effect-of-change:

| Knob | Type / unit / default | Effect of change |
|---|---|---|
| R2 mirrors `test_acoustic_sensor.py` verbatim (3 mounts, 2 rxGroups, 51.2 kHz, tick 30, BASIC) | recipe mirror: `int` counts, `float` freq [Hz], `float` tick [Hz], `str` level; def=N/A (external file) | First-try green (87/87 x 960) — verbatim mirroring is the proven strategy for new modalities [verified: failures.md R2 notes] |
| Generic radar fills rv_ms per NVIDIA's test | `rv_ms: array[float]` [m/s] per oracle; def=N/A (oracle behavior) | Unusable here: generic is silent in this build, so Doppler stays unverifiable [verified: failures.md TI limits] |
| Acoustic test never sets MBVH | `bool` flag absence [unitless] def=N/A (oracle behavior) | Basis for "no MBVH requirement" claim [verified: failures.md R2 notes] |

EKB rules: IF bringing up a NEW sensor modality THEN mirror the matching NVIDIA test verbatim before innovating BECAUSE verbatim mirroring went first-try green (R2) while innovation-first (generic radar) burned a full bisection [verified: failures.md F2 vs R2 notes].

LIMITS: L17-1: Oracles live outside the pack (`$ISAAC_SIM_DIR`) and may drift from the installed build (cf. physics-API drift) [probable].

UNKNOWN: U17-1: Oracle contents beyond what the pack quotes (never read into the pack) [theoretical].

---

## Sources-read

FULL reads (24 = 4 docs + 20 scripts):

- `action-reasoner/skills/sensors/SKILL.md`
- `action-reasoner/skills/sensors/TOOLS.md`
- `action-reasoner/skills/sensors/failures.md`
- `action-reasoner/skills/sensors/discovery.md`
- `base/scripts/s1_cap.py`, `s2_lidar.py`, `s3_run.py`, `s4_run.py`
- `base/scripts/s1_build.py`, `s2_build.py`, `s3_build.py`, `s4_build.py`, `v7_build.py`, `v7_run.py`
- `radac/scripts/r1_build.py`, `r1_drive.py`, `r2_build.py`, `r2_drive.py`
- `radac/scripts/r1_ti.py`, `r1_mat.py`, `r1_xcheck.py`, `r2_empty.py`
- `radac/scripts/verify_r1.py`, `verify_r2.py`

SKIMMED (22 scripts): `base/scripts/verify_s1/s2/s3/s4/v7.py` (full text via batch read),
`base/scripts/probes/contact_mega1/2/3/4.py` (grep: imports/sections/calls),
`probes/diag1_inventory.py`, `probes/diag2_beams.py` (full/header read),
`probes/sync_send.py` (full 973-byte read),
`radac/scripts/r1_attrs.py`, `r1_bbox.py`, `r1_birth.py`, `r1_birthdrive.py`,
`r1_clean.py`, `r1_diag.py`, `r1_diag2.py`, `r1_diag3.py`, `r1_ext.py`,
`r1_force.py`, `r1_pose.py`, `r1_pose2.py`, `r1_probe.py`, `r1_scene.py`,
`r1_stale.py`, `r1_two.py` (full text via batch reads).
