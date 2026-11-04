# Rendering-Lighting TOOLS_REF — Full Tool Mastery (2026-11-04)

Scope: pack `action-reasoner/skills/rendering-lighting/`, Isaac Sim 6.0.0 / Kit 110,
RTX RealTimePathTracing, Windows. Pack has NO SKILL.md — README.md is the skill doc [verified].
All 11 scripts read FULLY (r1_build, r2_cap, r3_light, r4_expo, v6_build, v6_cap,
verify_r1/r2/r3/r4/v6) + README + failures.md + discovery.md + TOOLS.md [verified].
Claim tags: [verified] = live-verified or directly shown in pack; [probable] = strongly
implied by repeated in-pack pattern / API convention, not explicitly gated; [theoretical] =
general API knowledge, NOT demonstrated in pack. Signatures: call FORM is [verified] from
scripts; param NAMES/defaults beyond shown positionals are [probable/theoretical].
DATATYPE pass: every signature carries exact param types + return type + units +
defaults, grounded in script call sites (script:line); unshown slots are marked
[probable]/[theoretical]; unknowable slots are marked [unknown] (5 total, see Totals).

## T1. pxr.UsdLux (in-sim lights)

DOES: Defines/reads DomeLight + DistantLight prims and their intensity attrs [verified].

FUNCTIONS (8, all typed):
- F1 `UsdLux.DomeLight.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdLux.DomeLight` — call form [verified r1_build:26, v6_build:26]; `stage: Usd.Stage` from `get_stage()` (unit n/a, no default) [verified r1_build:11]; `path: str` literal "/World/R1Dome" (unit n/a identity, no default) [verified]; `Sdf.Path` accepted [probable USD convention]; returns schema object supporting `.GetPrim()`/`.GetIntensityAttr()` [verified by chaining r1_build:26-27].
- F2 `UsdLux.DistantLight.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdLux.DistantLight` — same shape as F1 [verified r1_build:28, v6_build:28].
- F3 `UsdLux.DomeLight.Get(stage: Usd.Stage, path: str | Sdf.Path) -> UsdLux.DomeLight` — read proxy for during-play live sets [verified r1_build:54, r3_light:62, v6_cap:53]; invalid proxy if prim missing [theoretical].
- F4 `UsdLux.DistantLight.Get(stage: Usd.Stage, path: str | Sdf.Path) -> UsdLux.DistantLight` [verified r1_build:55, r3_light:61, v6_cap:54].
- F5 `schema.GetPrim() -> Usd.Prim` — no params; underlying prim for Xformable ops [verified r1_build:30].
- F6 `schema.GetIntensityAttr() -> Usd.Attribute[float]` — no params; float attr (dome: unitless multiplier [probable]; sun: lux [theoretical]) [verified all build/cap scripts].
- F7 `attr.Set(value: float, time: Usd.TimeCode = Usd.TimeCode.Default()) -> bool` — `value` in attr units (see F6), no default [verified drilled 0/100/300/400 dome, 1200/1500/3000/4500 sun r1_build:27,29 r3_light:63,66,69 v6_build:27,29 v6_cap:53-54]; `time` never passed in pack [theoretical default]; return bool unused in pack [verified].
- F8 `attr.Get(time: Usd.TimeCode = Usd.TimeCode.Default()) -> float` — called with zero args [verified r1_build:58-59]; `time` [theoretical]; returns attr-unit float [verified].

KNOBS (3, all typed):
- K1 dome intensity: attr type `float` [verified Set/Get of 400.0/100.0 floats]; unit unitless multiplier [probable]; USD-spec default 1.0 [theoretical]; pack drills 0/100/300/400: 100->400 moves frame mean 110.2->143.4, ratio 1.302 — THE light lever [verified README/r3_light/discovery]. 400->100 symmetric (-33pts) [verified r3 docstring].
- K2 sun intensity: attr type `float` [verified]; unit lux [theoretical]; USD-spec default 500.0 [theoretical]; pack drills 1200/1500/3000/4500: 1500->4500 (3x) moves mean only ~7% (143.6->146.2 @dome400; 110.1->116.2 @dome100; 94.8->101.3 @dome0) [verified failures R5]. Dead lever in this view.
- K3 light prim path ("/World/R1Dome", "/World/R1Sun", V6 parallels): type `str` (unit n/a, identity only; no default — required at Define) [verified]; no measured photometric effect of path choice [verified pattern; no-effect probable].

EKB RULES (3):
- E1 IF a drill needs a brightness lever THEN use dome (K1) or filmIso (T7.K1), NOT sun,
  BECAUSE sun 3x moves pixels only ~7% in the drilled view [verified failures R5].
- E2 IF changing intensity mid-run THEN `Get()`+`Set()` during play + 90-120 settle steps,
  with NO stop/set/play re-parse, BECAUSE sets apply live and re-parse adds nothing for
  lights while spamming stale-handle warnings [verified discovery/r3_light].
- E3 IF adopting any new light lever THEN prove its ratio with a gate first, BECAUSE an
  assumed lever can be near-dead (sun) and silently void the drill [verified failures R5].

LIMITS (3): L1 sun 3x -> ~7%: sun contributes little to drilled view [verified failures R5
OPEN]. L2 ~95pt floor persists at dome=0 (cause unknown: hidden ambient vs sun)
[verified observation failures R5]. L3 ONLY `intensity` drilled; color/exposure/angle/
diffuse/specular attrs untouched [verified scope].

UNKNOWN (4, all theoretical): U1 why sun contributes so little (direction lights unseen
faces? ambient floor?). U2 both-lights-to-0 discriminator outcome (black=sun is floor;
bright=hidden ambient). U3 whether sun leverage improves at rotation != (-50,20,0). U4
effect ranges of all non-intensity UsdLux attrs.

## T2. pxr.UsdGeom (in-sim geometry, camera, xforms)

DOES: Defines ground plane, test cubes, USD camera, and xform ops [verified].

FUNCTIONS (16, all typed):
- F1 `UsdGeom.Plane.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Plane` [verified r1_build:32, v6_build:31]; param types as T1.F1 [verified same call shape].
- F2 `plane.CreateWidthAttr() -> Usd.Attribute[float]; .Set(width: float) -> bool` — zero-arg Create [verified r1_build:33, v6_build:32]; full form `(defaultValue: float = <USD-spec default> [theoretical], writeSparsely: bool = False [theoretical])`; Set value in stage linear units = metres here, no default [probable]; drilled 20.0 [verified]; Get form unused [theoretical].
- F3 `plane.CreateLengthAttr() -> Usd.Attribute[float]; .Set(length: float) -> bool` — same shape as F2 [verified r1_build:34, v6_build:33]; drilled 20.0 [verified].
- F4 `UsdGeom.Cube.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Cube` [verified r1_build:35, v6_build:36].
- F5 `UsdGeom.Cube.Get(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Cube` for read-back [verified r1_build:62].
- F6 `cube.GetSizeAttr() -> Usd.Attribute[float]; .Set(size: float) -> bool; .Get() -> float` — size in metres, no default [probable]; drilled 1.0/0.5/1.2 [verified r1_build:36,62, v6_build:37]; USD-spec default 2.0 [theoretical].
- F7 `UsdGeom.Camera.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Camera` [verified r1_build:48, v6_build:49].
- F8 `UsdGeom.Camera.Get(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Camera` for read-back [verified r1_build:63].
- F9 `cam.GetFocalLengthAttr() -> Usd.Attribute[float]; .Set(f_mm: float) -> bool; .Get() -> float` — focal length in millimetres, no default [probable]; drilled 24.0 [verified r1_build:49,63, v6_build:50]; USD-spec default 50.0 [theoretical].
- F10 `UsdGeom.Xformable(prim: Usd.Prim) -> UsdGeom.Xformable` — wraps prim for xform ops; unit n/a, no default [verified r1_build:30,37,51,60,65].
- F11 `xform.AddTranslateOp(opSuffix: str = "") -> UsdGeom.XformOp` — called with zero args [verified r1_build:37, v6_build:38]; suffix type+default [theoretical, never shown]; op value type double3 in metres [probable].
- F12 `xform.AddRotateXYZOp(opSuffix: str = "") -> UsdGeom.XformOp; op.Set(rot_deg: Gf.Vec3f) -> bool` — suffix [theoretical]; Set takes XYZ degrees [verified Gf.Vec3f(-50,20,0) r1_build:30, v6_build:30].
- F13 `xform.MakeMatrixXform() -> UsdGeom.XformOp; op.Set(m: Gf.Matrix4d) -> bool` — no-arg Make [verified r1_build:51, v6_build:51]; matrix rows 0-2 unitless basis, row 3 (x,y,z) metres + 1 [probable per T3.K1]; pose Set [verified r1_build:51-52, v6_build:51-52].
- F14 `xformOp.Set(value: Gf.Vec3f | Gf.Vec3d | Gf.Matrix4d, time: Usd.TimeCode = Usd.TimeCode.Default()) -> bool` — `value` type per op kind, no default [verified all builds]; `time` never passed [theoretical].
- F15 `xform.GetOrderedXformOps() -> list[UsdGeom.XformOp]` — no params [verified r1_build:60-61,65-67]; empty list if no ops [theoretical].
- F16 `xformOp.Get(time: Usd.TimeCode = Usd.TimeCode.Default()) -> Gf.Vec3f | Gf.Vec3d | Gf.Matrix4d` — zero-arg calls [verified r1_build:60-61,65-67]; return type per op (rotate Vec3f / translate Vec3d / matrix Matrix4d) [verified read-backs].

KNOBS (7, all typed):
- K1/K2 ground width/length 20.0: attr type `float` (double) [probable]; unit metres (stage linear units) [probable]; USD-spec default [theoretical, value never observed — always Set]; fixed; frames the lit floor, no variation drilled [verified].
- K3 cube size: attr type `float` [verified]; unit metres [probable]; USD-spec default 2.0 [theoretical]; R1 1.0; V6 0.5/1.2 — exam varies it, verifiers gate exact values [verified].
- K4 cube position: type `Gf.Vec3d` (3 doubles) [verified]; unit metres [probable]; default n/a (no translate until op added) [probable]; (0,0,0.5) R1; (0.8,0,0.25)/(-0.9,0.3,0.6) V6 [verified].
- K5 focal length 24.0: attr type `float` [verified]; unit mm [probable]; USD-spec default 50.0 [theoretical]; fixed everywhere (USD cam AND RtxCamera) [verified].
- K6 sun rotation (-50,20,0): type `Gf.Vec3f` (3 floats) [verified]; unit degrees XYZ [verified use]; default n/a (no rotate op until added) [probable]; fixed; only drilled angle [verified].
- K7 camera matrix from look-at eye/target (R1 eye (3,-3,2); V6 eye (-3.5,2.5,2.5), tgt
  (0,0,0.5)): type `Gf.Matrix4d` (16 doubles) [verified]; unit mixed (unitless basis + metres row 3) [probable]; default n/a (identity until op Set) [probable]; defines the view ALL light ratios are measured in [verified].

EKB RULES (3):
- E1 IF authoring a USD camera matrix from numpy look-at THEN pass `mat.T` (transpose),
  BECAUSE Gf.Matrix4d is row-major (basis ROWS 0-2, eye ROW 3); untransposed reads
  campos=[0,0,0] and faces wrong [verified failures R2].
- E2 IF reading back camera position THEN `GetOrderedXformOps()[0].Get()[3][:3]`,
  BECAUSE eye lives in matrix row 3 [verified r1_build:65-67].
- E3 IF writing an exam build THEN use NEW sizes/eye (not R1 copies), BECAUSE verify_v6
  gates distinct values (300/1200/0.5/1.2/-3.5) [verified v6_build/verify_v6].

LIMITS (2): L1 row-major transpose mandatory (R2) [verified]. L2 ONLY Plane/Cube/Camera +
translate/rotate/matrix drilled [verified scope].

UNKNOWN (2, theoretical): U1 all non-drilled schemas (Sphere, Mesh, Cylinder...). U2 focal
lengths != 24 and their framing/exposure interaction.

## T3. pxr.Gf (math value types)

DOES: Matrix/vector values consumed by UsdGeom xform ops [verified].

FUNCTIONS (3, all typed):
- F1 `Gf.Matrix4d(m00: float, m01: float, m02: float, m03: float, m10: float, m11: float, m12: float, m13: float, m20: float, m21: float, m22: float, m23: float, m30: float, m31: float, m32: float, m33: float) -> Gf.Matrix4d` — SIXTEEN scalar args, NOT one tuple [verified r1_build:51-52, v6_build:51-52, failures R1]; all required, no defaults, each `float` (rows 0-2 unitless, m30/m31/m32 metres) [probable]; unpack form `Gf.Matrix4d(*vals)` [verified r1_build:51-52]; row-major layout [verified R2].
- F2 `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` — all required, no defaults [probable]; sun rotation degrees (-50,20,0) [verified r1_build:30, v6_build:30].
- F3 `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` — all required, no defaults [probable]; translations in metres [probable]; also `Gf.Vec3d(*pos)` unpack [verified r1_build:37, v6_build:38].

KNOBS (3, all typed): K1 the 16 matrix scalars: type `float` (double) each [verified float(v) cast r1_build:52]; unit mixed (rows 0-2 unitless, row 3 xyz metres) [probable]; default n/a (required ctor args) [probable]; rows 0-2 = basis, row 3 = eye+1 [verified R2].
K2 Vec3f components: type `float` x3 [probable]; unit degrees in drilled use [verified]; default n/a (required ctor args) [probable]. K3 Vec3d components: type `float` (double) x3 [probable]; unit metres [probable]; default n/a (required ctor args) [probable]. Effect-of-change: any scalar change moves/rotates the prim rigidly [probable].

EKB RULES (1): E1 IF constructing Matrix4d THEN unpack 16 scalars (`Gf.Matrix4d(*vals)`),
BECAUSE the tuple form raises TypeError (no converter to vector<double>) [verified R1].

LIMITS (2): L1 tuple-of-16 rejected (R1) [verified]. L2 row-major: basis ROWS, eye ROW 3
(R2) [verified].

UNKNOWN: none open for the drilled constructors [verified].

## T4. omni.usd (in-sim stage access)

DOES: Live stage handle; prim lookup + removal for clean-slate and stale-cam cleanup [verified].

FUNCTIONS (5, all typed):
- F1 `omni.usd.get_context() -> UsdContext` — no params [verified all in-sim scripts r1_build:11 r3_light:53 r4_expo:49 v6_build:11 v6_cap:45].
- F2 `context.get_stage() -> Usd.Stage` — no params [verified same lines].
- F3 `stage.GetPrimAtPath(path: str | Sdf.Path) -> Usd.Prim` — `path: str` literal, unit n/a, no default [verified r1_build:22, v6_build:22, r3_light:54, r4_expo:50, v6_cap:46]; `Sdf.Path` accepted [probable]; invalid prim if missing (guard with F4) [verified pattern r1/v6/r3/r4].
- F4 `prim.IsValid() -> bool` — no params; existence guard before RemovePrim [verified r1_build:23 etc.].
- F5 `stage.RemovePrim(path: str | Sdf.Path) -> bool` — `path: str`, unit n/a, no default [verified r1_build:24 etc.]; deletes prim subtree; used for clean slate + stale RtxCamera removal [verified]; return value unused in pack (true-if-removed [theoretical]) [verified].

KNOBS (2, all typed): K1 clean-slate path list: type `tuple[str, ...]` literal (unit n/a, no default — call-site constant) [verified r1_build:12-21]; R1 clears M1-M4/Y/PhysicsScene leftovers + R1 prims [verified r1_build:12-21]; V6 clears R1-R4 + R2ProbeCam(2) + V6 prims [verified v6_build:12-21] — cross-drill leftovers MUST be listed or they persist [probable]. K2
stale capture-cam path ("/World/R3Cam", "/World/R4Cam", "/World/V6Cap"): type `str` (unit n/a, no default) [verified]; removed before re-creating RtxCamera [verified r3/r4/v6_cap].

EKB RULES (2):
- E1 IF a build script THEN `GetPrimAtPath`+`IsValid`-guarded `RemovePrim` for every known
  leftover path BEFORE defining, BECAUSE prior drills' prims persist on the live stage and
  corrupt reads [verified r1_build/v6_build pattern].
- E2 IF re-running a capture script THEN remove the stale RtxCamera prim first, BECAUSE
  re-creating sensors on a live prim spams stale-handle warnings [verified discovery].

LIMITS (1): L1 re-parse/re-create legs spam stale-handle warnings on sensor re-creation
[verified discovery].

UNKNOWN (1, theoretical): U1 whether re-creating CameraSensor on a LIVE RtxCamera (no
RemovePrim) avoids the stale-handle warnings.

## T5. isaacsim.sensors.experimental.rtx — RtxCamera + CameraSensor (capture path)

DOES: Poses an RTX camera and captures annotated RGB frames from the live renderer [verified].

FUNCTIONS (5, all typed):
- F1 `RtxCamera(path: str, positions: list[list[float]] = <installed default unobserved> [unknown], orientations: list[list[float]] = <installed default unobserved> [unknown]) -> RtxCamera` — drilled call `RtxCamera("/World/R2Cam", positions=[eye.tolist()], orientations=[_mat_to_wxyz(R)])` [verified r2_cap:52-53, r3_light:57-58, r4_expo:53-54, v6_cap:49-50]; `path: str` (unit n/a, no default); `positions` outer per-camera, inner [x,y,z] metres [probable]; `orientations` inner [w,x,y,z] unitless quat [verified quat math r2_cap:23-49]; `cam.camera` sub-object holds lens setters [verified r2_cap:54]. NO `aux_output_level` kwarg in 6.0.0 (TypeError) [verified R3].
- F2 `cam.camera.set_focal_lengths(f_mm: float | list[float]) -> None` — scalar 24.0 drilled, unit mm, no default [probable] [verified r2_cap:54, r3_light:59, r4_expo:55, v6_cap:51]; plural name suggests sequence accepted [theoretical].
- F3 `cam.camera.set_clipping_ranges(near_m: float, far_m: float) -> None` — (near, far) in metres, no defaults [probable]; drilled (0.01, 1000.0) [verified r2_cap:55, r3_light:60, r4_expo:56, v6_cap:52].
- F4 `CameraSensor(cam: RtxCamera, resolution: list[int] = <installed default unobserved> [unknown], annotators: list[str] = <installed default unobserved> [unknown]) -> CameraSensor` — `cam: RtxCamera` (unit n/a, no default) [verified r2_cap:57]; `resolution: list[int]` [H, W] pixels, MUST be LIST [verified R3 + r2_cap:57 r3_light:65 r4_expo:60 v6_cap:57]; `annotators: list[str]` drilled ["rgb"] [verified]; tuple resolution CRASHES [verified R3].
- F5 `sensor.get_data(key: str) -> list[wp.array]` — `key: str` drilled "rgb" (unit n/a, no default) [verified r2_cap:62, r3_light:47, r4_expo:43, v6_cap:59]; per-camera LIST, unwrap [0] [verified R4 + all cap scripts].

KNOBS (8, all typed):
- K1 cam path ("/World/R2Cam", R3/R4/V6Cap): type `str`; unit n/a; default n/a (required ctor arg, identity only) [verified].
- K2 positions [[x,y,z]] eye: type `list[list[float]]`; unit metres [probable]; pack values R1 (3,-3,2), V6 (-3.5,2.5,2.5) [verified]; installed default unobserved (always passed — see F1).
- K3 orientations [[w,x,y,z]] from `_mat_to_wxyz(R)` (trace-branch quat, 4 variants across
  scripts, same math): type `list[list[float]]`; unit unitless quat [verified r2:23-49, r3:27-43, r4, v6_cap]; installed default unobserved (see F1).
- K4 focal 24.0: type `float`; unit mm [probable]; pack value 24.0 fixed, matches USD cam [verified]; installed default unobserved (always Set).
- K5 clipping range (0.01, 1000.0): type two positional `float`s; unit metres [probable]; pack fixed; scene depth (~5m) well inside [verified/probable]; installed default unobserved.
- K6 resolution [240, 320] = [H, W]: type `list[int]`; unit pixels [verified]; pack fixed; installed default unobserved (see F4); tuple form CRASHES broadcast_to [verified R3].
- K7 annotators ["rgb"]: type `list[str]`; unit n/a; pack fixed → uint8-like HxWx3 frames [verified]; installed default unobserved (see F4).
- K8 get_data key "rgb": type `str`; unit n/a; default n/a (required arg) [verified]; must match an annotator [probable; only "rgb" drilled].

EKB RULES (3):
- E1 IF Isaac Sim 6.0.0 THEN bare `RtxCamera(path, positions=, orientations=)` with NO
  `aux_output_level`, BECAUSE the installed API rejects that sketched kwarg [verified R3].
- E2 IF passing resolution THEN a LIST `[H, W]`, BECAUSE a tuple crashes `broadcast_to`
  ("Invalid indexing in slice: 240") [verified R3].
- E3 IF reading `get_data` THEN `d[0]` unwrap + `.numpy()` (Skill 5 R2 rule), BECAUSE the
  return is a per-camera LIST of warp arrays and `np.asarray()` directly on it dies
  (warp raises RuntimeError, not IndexError, out-of-bounds) [verified R4].

LIMITS (4): L1 no `aux_output_level` in 6.0.0 — probe signatures live [verified R3]. L2
resolution list-only (R3) [verified]. L3 unwrap-[0]+`.numpy()` mandatory (R4) [verified].
L4 captures are BIT-DETERMINISTIC (143.6 hit 3x; 94.8/101.3 repeated across variants):
divergence means changed inputs, not noise [verified discovery].

UNKNOWN (3, theoretical): U1 annotators other than "rgb" (depth/normals/...). U2
resolutions other than 240x320. U3 multi-camera positions/orientations lists (len>1).

## T6. isaacsim.core.experimental.utils.app as app_utils (timeline control)

DOES: Plays the timeline and advances fixed settle steps so the renderer converges [verified].

FUNCTIONS (2, all typed):
- F1 `app_utils.play(commit: bool = True) -> None` — `commit: bool` (unit n/a); scripts always pass `commit=True` [verified r2_cap:58, r3_light:64, r4_expo:59, v6_cap:56]; default True [probable — never called bare]; other signature extras [theoretical, none observed].
- F2 `await app_utils.update_app_async(steps: int) -> None` — coroutine, MUST be awaited [verified r2_cap:59, r3_light:67,70, r4_expo:61,64, v6_cap:58]; `steps: int` in steps/frames, no default (always passed) [verified]; drilled steps=120 (initial) and 90/120 (after change) [verified]; awaitable resolves to None [probable].

KNOBS (2, all typed): K1 `commit`: type `bool`, unit n/a, default True [probable]; fixed True everywhere [verified]; effect of False [theoretical].
K2 `steps`: type `int`, unit steps/frames, default n/a (always passed) [verified]; 120 initial settle; 90 after a light/exposure change (r4 second leg), 120 in
r3 legs — all converge for these small scenes [verified discovery/r3/r4].

EKB RULES (2):
- E1 IF capturing THEN `play(commit=True)` + `await update_app_async(steps=120)` BEFORE
  first grab, BECAUSE the path tracer must converge or frames read dark/noisy [verified
  all cap scripts; dark-if-skipped probable].
- E2 IF light/exposure changed during play THEN `await update_app_async(steps>=90)` before
  re-grab, BECAUSE the new level needs settle frames to stabilize [verified r3/r4].

LIMITS (1): L1 120/90 scoped to SMALL scenes; skill sketch says 200 for warehouses —
unverified by this pack [verified discovery].

UNKNOWN (1, theoretical): U1 minimum settle steps for warehouse-scale scenes.

## T7. carb.settings (in-sim renderer settings: exposure)

DOES: Sets live RTX post/tonemap exposure; drilled lever is filmIso [verified].

FUNCTIONS (3, all typed):
- F1 `carb.settings.get_settings() -> carb.settings.ISettings` — no params [verified r4_expo:57, v6_cap:55].
- F2 `settings.set(key: str, value: float) -> None` — `key: str` drilled only `"/rtx/post/tonemap/filmIso"` (unit n/a, no default) [verified r4_expo:58,63,67, v6_cap:55]; `value: float` drilled 100.0/400.0, unit ISO sensitivity, no default [verified]; other value-type overloads (int/str/bool) [theoretical, never used].
- F3 `settings.get(key: str) -> Any` — `key: str` [probable shape]; NEVER called in surviving scripts [verified absence]; full signature [theoretical]; discovery's default-state note (rendermode/op/filmIso/no-autoExposure) implies probe reads happened [probable].

KNOBS (1, all typed): K1 `/rtx/post/tonemap/filmIso`: type `float` [verified 100.0/400.0 sets]; unit ISO sensitivity (unitless scale) [probable]; observed default 100.0 (pinned, not inherited) [verified discovery]; 100->400 moves frame mean 143.6->213.2, ratio
1.485 — STRONG lever, rules out tonemap compression as the R5 cause [verified r4/README/
failures R5]. Other observed settings (pinned, not inherited): rendermode=RealTimePathTracing (`str`), tonemap op=6 (`int`), NO autoExposure key [verified discovery].

EKB RULES (2):
- E1 IF a drill touches exposure THEN pin filmIso at start AND restore 100.0 at end
  (r4) / pin per-drill (v6), BECAUSE drills must pin, not inherit, render settings
  [verified r4_expo:67, v6_cap:55, discovery].
- E2 IF a light lever looks dead (R5) THEN run a filmIso 4x leg as control, BECAUSE a
  strong filmIso response (1.49x) rules out downstream tonemap compression [verified R5].

LIMITS (2): L1 ONLY filmIso drilled; no other `/rtx/post/*` key touched [verified scope].
L2 ONLY 100-400 drilled [verified scope].

UNKNOWN (3, theoretical): U1 tonemap operator values != 6. U2 filmIso outside 100-400
(clip/blowout behavior). U3 any other `/rtx/post/*` key incl. autoExposure (absent by default).

## T8. warp as wp (in-sim sensor array container)

DOES: Array type returned by `CameraSensor.get_data`; converted to numpy for stats/PNG [verified].

FUNCTIONS (2, all typed):
- F1 `wp.array` — TYPE object only: `isinstance(x: Any, wp.array) -> bool` checks [verified r2_cap:63,65, r3_light:48,50, r4_expo:44,46, v6_cap:60,62]; element dtype uint8 [probable], shape (H,W,3) = (240,320,3) [verified]; never constructed in pack — constructor signature [unknown] (1 slot).
- F2 `arr.numpy() -> np.ndarray` — no params; the ONLY sanctioned warp->numpy path [verified r2_cap:65, r3_light:50, r4_expo:46, v6_cap:62]; returns uint8 (240,320,3) ndarray (shape verified R2-REPORT; dtype probable).

KNOBS (0): pure container; shape (H,W,3) set by CameraSensor, not by warp calls [verified].

EKB RULES (1): E1 IF holding sensor data THEN `.numpy()`, NEVER `np.asarray()` directly,
BECAUSE numpy iterates `__getitem__` and warp raises RuntimeError (not IndexError)
out-of-bounds, killing iteration ("Invalid indexing in slice: 240") [verified R4, Skill 5 R2].

LIMITS (1): L1 direct `np.asarray(wp_array)` dies — always unwrap+convert explicitly
[verified R4].

UNKNOWN: none open for the drilled `.numpy()` path [verified].

## T9. numpy as np (in-sim math + frame stats)

DOES: Look-at basis construction, rotmat->quat conversion, frame mean/max stats [verified].

FUNCTIONS (12, all typed):
- F1 `np.array(object: list[float] | list[list[float]], dtype: np.dtype | None = None, copy: bool = True, order: str = "K", subok: bool = False, ndmin: int = 0) -> np.ndarray` — `object` eye/tgt/up float lists [verified r1_build:39-40,42]; effective dtype float64 [probable numpy default]; extra kwargs never passed [theoretical stdlib signature].
- F2 `np.linalg.norm(x: np.ndarray, ord: int | str | None = None, axis: int | tuple[int, int] | None = None, keepdims: bool = False) -> float` — `x` 3-vectors [verified r1_build:41,43]; returns float in input units (m or unitless) [probable]; extras never passed [theoretical].
- F3 `np.cross(a: np.ndarray, b: np.ndarray, axisa: int = -1, axisb: int = -1, axisc: int = -1, axis: int | None = None) -> np.ndarray` — 3-vector inputs (unitless dirs / metres) [verified r1_build:42,44]; right = fwd x up; up = right x fwd [verified]; extras [theoretical].
- F4 `np.eye(N: int, M: int | None = None, k: int = 0, dtype: np.dtype = float64, order: str = "C") -> np.ndarray` — `N: int` = 4, unitless, no default [verified r1_build:45, v6_build:46]; look-at matrix seed (USD-cam path only); extras [theoretical].
- F5 `np.column_stack(tup: list[np.ndarray]) -> np.ndarray` — single param, list of three (3,) vectors → (3,3) R local-axes-in-world (Rtx path only) [verified r2_cap:20, r3_light:24, r4_expo:20, v6_cap:23].
- F6 `np.trace(a: np.ndarray, offset: int = 0, axis1: int = 0, axis2: int = 1, dtype: np.dtype | None = None) -> float` — `a` is (3,3) R unitless [verified r2_cap:24, r3_light:28, r4_expo:24, v6_cap:27]; quat trace branch in `_mat_to_wxyz`; extras [theoretical].
- F7 `np.asarray(a: Any, dtype: np.dtype | None = None, order: str | None = None) -> np.ndarray` — `a` is post-`.numpy()` array [verified r2_cap:65, r3_light:50, r4_expo:46, v6_cap:62]; AFTER `.numpy()` unwrap only [verified]; extras [theoretical].
- F8 `rgb.mean(axis: None | int | tuple[int, int] = None, dtype: np.dtype | None = None, out: np.ndarray | None = None, keepdims: bool = False) -> float` — zero-arg calls [verified r2_cap:70, r3_light:68,72, r4_expo:62,66, v6_cap:66]; returns px-intensity mean 0-255 [verified]; THE photometric readout (all ratios derive from it).
- F9 `rgb.max(axis: None | int | tuple[int, int] = None, out: np.ndarray | None = None, keepdims: bool = False, initial: int | None = None, where: bool | np.ndarray = True) -> np.uint8` — zero-arg calls [verified]; clipping guard readout [verified].
- F10 `rgb.shape -> tuple[int, int, int]` — ATTRIBUTE (no call); (H, W, C) in pixels; gated as literal `[240, 320, 3]` [verified r2_cap:69-70].
- F11 `rgb.astype(dtype: np.dtype | type, order: str = "K", casting: str = "unsafe", subok: bool = True, copy: bool = True) -> np.ndarray` — `dtype=np.uint8`, no default [verified r2_cap:67, v6_cap:64]; before `Image.fromarray` [verified]; extras [theoretical].
- F12 `eye.tolist() -> list[float]` — no params; positions kwarg payload in metres [probable] [verified r2_cap:52, r3_light:57, r4_expo:53, v6_cap:49].

KNOBS (3, all typed): K1 eye: type `np.ndarray` shape (3,) float64 [probable]; unit metres [probable]; default n/a (call-site constant); (3,-3,2) R1 / (-3.5,2.5,2.5) V6 [verified]. K2 target: same type `np.ndarray` (3,) [verified]; unit metres [probable]; default n/a; (0,0,0.5) both [verified]. K3 up hint (0,0,1): type `np.ndarray` (3,) [verified]; unit unitless direction [probable]; default n/a [verified]. Effect: V6's new rig+scene reads mean 184.5 vs R2 143.6 — uncontrolled comparison (scene AND rig differ), so no per-knob delta proven [verified numbers README; attribution probable].

EKB RULES (1): E1 IF posing cameras THEN build look-at ONCE per convention — `mat.T`+Gf
for USD cams, `column_stack`+`_mat_to_wxyz` quat for RtxCamera — BECAUSE the two camera
APIs consume incompatible pose forms (row-major matrix vs wxyz quat) [verified r1 vs r2].

LIMITS: none — pure local math; the transpose requirement is a Gf limit (T3.L2) [verified].

UNKNOWN: none open [verified].

## T10. PIL.Image (in-sim PNG writer)

DOES: Saves captured RGB frames to evidence/ as PNG [verified].

FUNCTIONS (2, all typed):
- F1 `Image.fromarray(obj: np.ndarray, mode: str | None = None) -> PIL.Image.Image` — `obj: np.ndarray` uint8 (H,W,3) (unit: px intensity, no default) [verified r2_cap:67, v6_cap:64]; uint8 astype FIRST [verified]; `mode` never passed (derived "RGB" [probable]); other dtypes/modes [theoretical].
- F2 `img.save(fp: str, format: str | None = None) -> None` — `fp: str` absolute Windows path into evidence/ (unit n/a, no default) [verified r2_cap:67, v6_cap:64]; `format` never passed (inferred PNG from extension [probable]); format-specific extra kwargs exist in PIL but are unlisted here [theoretical].

KNOBS (2, all typed): K1 EV path (`.../evidence/r2_frame.png`, `v6_frame.png`, absolute `C:/...`): type `str` [verified r2_cap:12, v6_cap:15]; unit n/a; default n/a (module constant) [verified]. K2 dtype uint8: type `np.dtype` (`np.uint8`) [verified r2_cap:67]; unit n/a; default n/a (explicit astype) [verified]. Effect: R2 PNG 33KB (mean 143.6, max 203); V6 PNG
40KB (mean 184.5) [verified README + evidence/*.png sizes].

EKB RULES (1): E1 IF saving a frame THEN `rgb.astype(np.uint8)` before `fromarray`,
BECAUSE fromarray derives image mode from array dtype and float arrays would mis-save
[verified pattern; because probable (PIL semantics)].

LIMITS: none recorded [verified]. UNKNOWN: none open [verified].

## T11. os / json / re (local verifier stdlib)

DOES: Local evaluators (verify_rN/verify_v6, run LOCALLY not in-sim) parse saved
`*-REPORT` outputs from evidence/*.json and gate drills [verified].

FUNCTIONS (6, all typed):
- F1 `open(file: str, mode: str = "r", buffering: int = -1, encoding: str | None = None, errors: str | None = None, newline: str | None = None, closefd: bool = True, opener: Callable | None = None) -> TextIOWrapper` — `file: str` relative `action-reasoner/skills/rendering-lighting/evidence/*.json`, unit n/a, no default [verified all verifiers verify_r1:4 verify_r2:4 verify_r3:4 verify_r4:4 verify_v6:4-5]; single-positional calls, mode "r" [probable stdlib default]; extras [theoretical].
- F2 `json.load(fp: TextIO, cls: type | None = None, object_hook: Callable | None = None, parse_float: Callable | None = None, parse_int: Callable | None = None, parse_constant: Callable | None = None, object_pairs_hook: Callable | None = None) -> dict[str, Any]; ["output"] -> str` — report text extraction [verified verify_r1:4 etc.];
  verify_v6 reads TWO files (build + cap) [verified verify_v6:4-5]; extras [theoretical].
- F3 `re.search(pattern: str, string: str, flags: int = 0) -> re.Match | None` — float/int/shape extraction; wrapped in `f(pat: str, i: int = 1) -> float` helper returning `float("nan")` on miss [verified all verifiers verify_r1:6-8]; `flags` never passed [theoretical].
- F4 `match.group(*groups: int | str) -> str | tuple[str, ...]` — scripts pass exactly one `int` (`m.group(i)`, i>1 for 2nd/3rd vec components) → `str` [verified verify_r1:8,13-21]; zero-arg whole-match and multi-group tuple forms [theoretical].
- F5 `os.path.exists(path: str) -> bool` + F6 `os.path.getsize(path: str) -> int` — `path: str` PNG relative path (unit n/a, no default) [verified verify_r2:5,15, verify_v6:6,21]; getsize returns bytes [verified]; PNG gate (>20KB; actual 33KB/40KB) [verified].

KNOBS (3, all typed): K1 evidence JSON path per drill (r1_build/r2_cap/r3_light/r4_expo/v6_build+
v6_cap): type `str` (relative path) [verified]; unit n/a; default n/a (module constant per verifier) [verified]. K2 regex per report field (`dome=`, `sun=`, `sunrot=`, `cubesize=`,
`focal=`, `campos=`, `shape=`, `mean=`, `max=`, `size=`, `mean1/2`, `ratio=`, `max2=`,
`sizeA/B`, `eye=`, `iso=`): type `str` pattern [verified]; unit n/a; default n/a (inline literal) [verified]. K3 thresholds: type `float`/`int` [verified]; units px intensity (mean/max bands), bytes (png size), unitless (ratios) [verified]; exact-with-tolerance (dome/sun/size/
focal/eye 1e-6, campos 1e-3) [verified verify_r1]; shape literal `shape=[240, 320, 3]`
[verified]; mean bands 10..220, max>100, png>20KB [verified r2/v6]; r3 ratio 1.2..3.0
(actual 1.302) [verified]; r4 ratio>1.15 (actual 1.485) + no-full-clip
(max2<255 OR mean2<250) [verified]; v6 10 checks incl. iso pinned 100 [verified].
NOTE: verify_r3 docstring says "doubling sun" but the drill varies DOME — stale docstring,
gate (ratio 1.2..3.0) matches dome behavior [verified r3_light.py:1-10 vs verify_r3.py:1].

EKB RULES (2):
- E1 IF parsing a report field THEN `re.search` + `float(nan)` fallback (never bare
  `.group` on a possible None), BECAUSE a missing field must FAIL the gate, not crash the
  verifier [verified all verifiers' `f()` helper].
- E2 IF gating exact floats THEN tolerance compare (1e-6 for attributes, 1e-3 for campos),
  BECAUSE reports print rounded decimals [verified verify_r1].

LIMITS: none — local text checks; exit 0 on pass per README [verified]. SUPERSEDES
TOOLS.md "verify_r2/r3/r4 skimmed" note: all five verifiers now read FULLY [verified].

UNKNOWN: none open [verified].

## T12. isaacsim_send.py bridge (execution transport; referenced, not in pack)

DOES: Ships r*/v6 scripts into the live Isaac Sim session (README: "in-sim via
isaacsim_send.py unless noted") [verified README:24].

FUNCTIONS (0): no direct calls in any pack script; transport layer only. Evidence *.json
files store each shipped script's reported output [verified].

KNOBS (0): none visible in pack.

EKB RULES (1): E1 IF a script header says "runs INSIDE Isaac Sim" THEN ship it via the
bridge; IF "runs LOCALLY" (verify_*) THEN run it locally against evidence/*.json,
BECAUSE only the bridge reaches the live stage/renderer [verified README convention].

LIMITS: none recorded in this pack's failures.md [verified].

UNKNOWN (1, theoretical): U1 bridge CLI flags / API surface — never shown anywhere in pack.

## T13. inspect (live API probing; cited, no surviving script)

DOES: `inspect.signature` / `inspect.getsource` used during training to probe installed
6.0.0 RtxCamera/CameraSensor signatures (found no-aux-quirk + list-resolution) [verified
failures R3 recovery note].

FUNCTIONS (2, all typed, cited-not-shown):
- F1 `inspect.signature(obj: Callable, follow_wrapped: bool = True, globals: dict | None = None, locals: dict | None = None, eval_str: bool = False) -> inspect.Signature` — `obj` the probed ctor (unit n/a, no default) [probable from R3 context]; full signature [theoretical invocation; lesson verified R3].
- F2 `inspect.getsource(object: Any) -> str` — `object` module/class/function (unit n/a, no default) [probable]; [theoretical invocation; lesson verified R3].

KNOBS (1, all typed): K1 probe target (RtxCamera, CameraSensor): type `type | Callable` (class/ctor object) [probable from R3 context]; unit n/a; default n/a (required arg) [probable].

EKB RULES (1): E1 IF installed API may differ from skill sketches THEN probe live
signatures BEFORE trusting examples, BECAUSE 6.0.0 rejected sketched kwargs and crashed
on sketched tuple resolution [verified lesson R3; exact invocations theoretical].

LIMITS: none recorded beyond the R3 finding itself [verified].

UNKNOWN (1, theoretical): U1 exact probe invocations — no surviving script (R2ProbeCam/
R2ProbeCam2 cleanup hints in v6_build:14 suggest probe scripts existed but are absent).

## Cross-tool notes

- Canonical capture chain (all cap scripts): T9 look-at -> T5.RtxCamera -> T5 lens setters
  -> T6.play -> T5.CameraSensor -> T6.settle -> T5.get_data -> T8.numpy -> T9 stats ->
  T10 PNG -> T1/T7 live levers between legs [verified].
- Canonical build chain: T4 clean-slate -> T1 lights -> T2 geometry -> T2/T3 camera matrix
  -> T1/T2 read-back REPORT [verified r1/v6_build].
- Canonical verify chain: T12 evidence JSON -> T11 parse+gate [verified all verify_*].
- Absent-but-cited: cross-val `x6_live.py` + `verify_x6.py` (README Tools) NOT in pack
  scripts/ — presumably live elsewhere [verified absent; 11 scripts on disk].

## Totals

13 tools · 66 functions (8+16+3+5+5+2+3+2+12+2+6+0+2), ALL typed · 35 knobs
(3+7+3+2+8+2+1+0+3+2+3+0+1), ALL typed · 23 EKB rules (3+3+1+2+3+2+2+1+1+1+2+1+1) ·
16 substantive limits (3+2+2+1+4+1+2+1) · 16 unknowns (4+2+0+1+3+1+3+0+0+0+0+1+1).
DATATYPE: signatures typed 66/66 · knobs typed 35/35 · still-unknown slots 5
(T5.F1 positions default, T5.F1 orientations default, T5.F4 resolution default,
T5.F4 annotators default, T8.F1 wp.array ctor) — all marked [unknown] inline.
