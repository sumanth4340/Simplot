# Viewport-UI Tool Knowledge (2026-11-04)

> FULL DETAIL: [TOOLS_REF.md](TOOLS_REF.md) — 10 tools, ~60 functions/signatures, ~45 knobs, ~40 EKB rules, ~35 limits, 8 unknowns (13 scripts read fully + 13 evidence JSONs).

## Tools

### isaacsim_send.py (remote bridge CLI, local)
- DOES: Sends in-sim scripts to the running Isaac Sim python_server and returns status/output JSON.
- FUNCTIONS USED:
  - CLI invocation with script path + `--arg key=value` (passes `output_path` to library scripts; evidence `*_shot.json` / `*_get.json` / `*_set.json` hold its replies).
  - Reply contract consumed by verifiers: `status == "ok"` plus output markers ("Saved viewport screenshot", "Saved app screenshot", "Selected 1 prim(s)").
- LIMITS-live-verified:
  - Sim can crash mid-probe (one crash observed during a viewport screenshot; discovery.md "GUI vs headless") — recovery is taskkill tree + relaunch + health poll; evidence on disk survives.
- UNKNOWN:
  - Exact CLI flags/retry semantics (no drill in this pack exercises them directly; the pack only consumes reply JSON).

### viewport_screenshot.py (isaac-sim-remote library, in-sim via --arg)
- DOES: Captures the viewport render to `output_path`.
- FUNCTIONS USED:
  - Script arg `output_path`; emits "Saved viewport screenshot" on success.
- LIMITS-live-verified:
  - Fixed 1280x720 RGBA in GUI mode; works identically headless (discovery.md; evidence `w1_viewport.png` 171821 bytes).
  - One sim crash observed during a viewport screenshot (discovery.md "GUI vs headless").
- UNKNOWN:
  - Behavior with multiple viewports, non-default resolution settings, or capture-while-paused.

### app_screenshot.py (isaac-sim-remote library, in-sim via --arg)
- DOES: Captures the full application window including UI chrome to `output_path`.
- FUNCTIONS USED:
  - Script arg `output_path`; emits "Saved app screenshot" on success.
- LIMITS-live-verified:
  - Output size follows the window (958x981 in the GUI session; discovery.md, evidence `w3_app.png` 164993 bytes, `v8_app.png` 215780 bytes).
- UNKNOWN:
  - Headless behavior (window may not exist); multi-monitor/window-focus effects.

### camera_control.py (isaac-sim-remote library, in-sim via --arg)
- DOES: Gets/sets the active viewport camera pose; aims it at a target.
- FUNCTIONS USED:
  - `get` — prints `Position (x, y, z): [...]` parsed by verify_w2 with 0.05 tolerance.
  - `set` / `look_at` with eye/target — implemented via `ViewportManager.set_camera_view(eye/target)` + 30 update steps (discovery.md).
  - `list_cameras` — enumerates cameras (named in discovery.md; no drill output in this pack).
- LIMITS-live-verified:
  - Active camera is the root-level default `/OmniverseKit_Persp` (README.md, discovery.md).
  - Pose set is exact to <0.05 per axis (verify_w2 checks x~3, y~-3, z~2).
- UNKNOWN:
  - `list_cameras` output format (never captured in evidence/); behavior when a non-Persp camera is active; whether the 30 update steps suffice for heavy scenes.

### select_prim.py (isaac-sim-remote library, in-sim via --arg)
- DOES: Manipulates the USD stage selection set.
- FUNCTIONS USED:
  - `set` — selects prim(s); acks "Selected 1 prim(s)".
  - `get` — prints current selection (must contain the prim path, e.g. `/World/W1Cube`).
  - `clear` / `all` — named in discovery.md; no drill output in this pack.
- LIMITS-live-verified:
  - Set/get round-trips exactly (verify_w3: set W1Cube -> get shows W1Cube; verify_v8: `/World/V8CubeB`).
- UNKNOWN:
  - `clear`/`all` output contracts; multi-prim selection ordering; behavior on invalid paths.

### omni.usd (in-sim Python API)
- DOES: Provides stage access for scene authorship inside build scripts.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()` — stage handle in w1_build.py and v8_build.py.
  - `stage.GetPrimAtPath(p)` + `stage.RemovePrim(p)` — idempotent cleanup of stale prims before rebuild.
- LIMITS-live-verified:
  - None recorded in this pack (cleanup loop never failed here).
- UNKNOWN:
  - Undo/redo interaction; behavior on locked or instance-proxy prims.

### pxr UsdGeom / UsdLux / Gf (in-sim Python API)
- DOES: Authors lights, ground, and cubes for screenshot scenes.
- FUNCTIONS USED:
  - `UsdLux.DomeLight.Define` + `GetIntensityAttr().Set(...)` (W1 400, V8 300).
  - `UsdLux.DistantLight.Define` + intensity (W1 1500, V8 1200) + `AddRotateXYZOp().Set(Gf.Vec3f(-50, 20, 0))` sun angle.
  - `UsdGeom.Plane.Define` + width/length 20.0 (ground).
  - `UsdGeom.Cube.Define` + `GetSizeAttr().Set(...)` + `AddTranslateOp().Set(Gf.Vec3d(...))` (cube placement).
- LIMITS-live-verified:
  - None recorded in this pack.
- UNKNOWN:
  - Nothing beyond these six call patterns (materials, physics, and articulation live in other packs).

### pngstats.py (pack-local stdlib PNG reader)
- DOES: Decodes Kit PNGs and compares views without PIL.
- FUNCTIONS USED:
  - `png_stats(path)` — returns w/h/mean/std/bytes/raw/ch via `struct` (IHDR) + `zlib` (IDAT) + scanline unfilter (filters 0-4 incl. Paeth).
  - `mean_abs_diff(a_path, b_path)` — mean absolute RGB pixel difference; asserts equal sizes.
- LIMITS-live-verified:
  - Supports 8-bit truecolor / truecolor+alpha only (what Kit screenshots write); asserts otherwise (code + failures.md R1).
  - Mean-only comparison is UNSOUND: symmetric opposite views had means 183.4 vs 183.8 (delta 0.4) with different content — always gate on `mean_abs_diff > 3.0` (measured 7.59; failures.md R2).
  - Validated against a 1280x720 Kit screenshot (failures.md R1).
- UNKNOWN:
  - Performance on very large (>4K) captures; behavior on interlaced or 16-bit PNGs (asserts, untested).

### verify_w1/w2/w3/w4/verify_v8 (pack-local evaluators)
- DOES: Local pass/fail gates over evidence JSON + PNGs; exit text `WN-PASS/WN-FAIL`.
- FUNCTIONS USED:
  - `json` (load `evidence/*.json`), `os.path.getsize` (PNG byte floors: 50KB shots, 20KB exam), `re` (parse camera poses / build markers), `sys.path` insert + `pngstats` import.
  - Gates: PNG >= 640x480, mean in 5..250 (W1 10..245), std > 1.0 (aimed views > 5.0), frames differ (mean delta > 2.0 for W2, pixel MAD > 3.0 for W4).
- LIMITS-live-verified:
  - None recorded in this pack (5/5 green at graduation per README.md).
- UNKNOWN:
  - Threshold robustness across GPUs/tone-mapping settings (single-machine calibration).

## Unverified
- `camera_control.py list_cameras` output format and multi-camera behavior — named in discovery.md, zero evidence samples.
- `select_prim.py clear` / `all` contracts — named in discovery.md, zero evidence samples.
- `app_screenshot.py` in headless mode — only GUI captures evidenced (`w3_app.png`, `v8_app.png`).
- `cross-val x8_live.py + verify_x8.py` mentioned in README.md Tools but no such files exist in scripts/ — co-validation snapshot not present in this pack.
- Verifier thresholds (mean/std/byte floors) calibrated on one machine/GPU only — portability unproven.
- isaacsim_send.py CLI flags, timeouts, and retry semantics — pack consumes only its reply JSON.

## Sources-read
- action-reasoner/skills/viewport-ui/README.md (SKILL.md absent; README.md is the pack doc)
- action-reasoner/skills/viewport-ui/failures.md (R1-R2)
- action-reasoner/skills/viewport-ui/discovery.md
- action-reasoner/skills/viewport-ui/scripts/pngstats.py (full)
- action-reasoner/skills/viewport-ui/scripts/w1_build.py (full)
- action-reasoner/skills/viewport-ui/scripts/v8_build.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w1.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w2.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w3.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w4.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_v8.py (full)
