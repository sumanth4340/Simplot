# App-Session TOOLS_REF (FULL-TOOL-MASTERY, 2026-11-04)

Claim tags: [verified] = drilled live in this pack's evidence, [probable] = read in library source but not drilled here, [theoretical] = inferred, not observed, [unknown] = type/value unobserved anywhere (no source annotation, no call site).
DATATYPE pass (2026-11-04): 80/80 signatures typed (0 bare, 0 `(...)`), 44/44 knobs typed (type+unit+default), 13 still-unknown. Call-site cites use pack `scripts/*.py` lines and bridge-library source lines.

## 1. isaacsim_send.py (bridge CLI, local)

DOES: [verified] Sends inline code / stdin / `--file` scripts from OUTSIDE into the running sim's python_server (loopback TCP `127.0.0.1:8226`) and returns a JSON envelope `{status, output, traceback, ...}`.

Functions + full signatures (annotations per source; call grounding cited):
- `send_and_receive(host: str, port: int, source: str, timeout: float = 60.0) -> dict` — source isaacsim_send.py:72. `timeout` unit seconds. Pack never calls directly (goes via CLI: SEND `--timeout 120/150`, a1_run.py:12-15, a2_run.py:11-14); return envelope dict grounded in `json.loads(p.stdout)` + `body.get("output"/"traceback")` (a1_run.py:22-26).
- `_parse_arg_value(value: str) -> Any` — source isaacsim_send.py:85 (`value: str` annotated; return `Any`: `ast.literal_eval` literal or raw-str fallback, [probable] inferred from :91-94). `"60"` -> int 60, `"True"` -> bool, `"play"` -> str. Internal use :106,123,145. No pack call site.
- `_inject_args(source: str, args: list[str]) -> str` — source isaacsim_send.py:97. No units. Prepends `key = repr(parsed)` lines. Internal use :251,257. No pack call site [probable].
- `_wrap_isolated(source: str, args: list[str]) -> str` — source isaacsim_send.py:110. Wraps `--file` body in `async def _isolated_script():` + `await _isolated_script()`; args become function locals. Top-level `await` works inside. Internal use :253. No pack call site [probable].
- `_parse_args_kv(arg_list: list[str]) -> dict[str, Any]` — source isaacsim_send.py:138 (`-> dict`; value-type Any [probable] via `_parse_arg_value` :145). k=v list to typed dict (envelope mode); undrilled.
- `_needs_envelope(args: argparse.Namespace) -> bool` — source isaacsim_send.py:149. True if `--json-envelope/--context/--fire-and-forget/--execution-timeout/--args-json/--introspect`. Internal use :250,256,266.
- `async main() -> None` — source isaacsim_send.py:161. No params (argv-driven). CLI entry; process exit 0 iff `status == "ok"` (:331).

Knobs (CLI flags) + type/unit/default + effect-of-change:
- `--file/-f <path: str>` default None [verified]: script file to send (a1_run.py:32 passes SIMCTL str; a2_run.py:34). Without it, positional `code: str` (default None, isaacsim_send.py:163) or stdin is sent.
- `--arg/-a k=v` (repeatable) [verified]: `list[str]`, default [] (append action, isaacsim_send.py:166). Each element `str` "k=v"; value re-typed via literal_eval (a1_run.py:48 `num_steps=60` arrives int).
- `--raw` [verified]: `bool` flag (store_true, default False, isaacsim_send.py:171). Prints raw JSON envelope; pack always sets it (a1_run.py:15).
- `--timeout <seconds: float>` default 60.0 [verified: pack uses 120/150]: client TCP wait in seconds (a1_run.py:15 `"120"`; a2_run.py:14 `"150"`). Exceeding raises `asyncio.TimeoutError` -> exit 1.
- `--host <str>` default "127.0.0.1" / `--port <int>` default 8226 [probable]: endpoint (isaacsim_send.py:168-169). No pack call site overrides them. Wrong port -> `ConnectionRefusedError` -> exit 1.
- `--dry-run` [probable]: `bool` flag, default False (:172-176). Prints payload, no connect. No pack call site.
- `--no-isolate` [probable]: `bool` flag, default False (:177-181). Skips function-wrap; script shares executor globals. No pack call site.
- Envelope mode [probable, all undrilled]: `--context/-c <str | None>` default None (:186-188); `--fire-and-forget/--ff <bool>` default False (:189-195); `--execution-timeout/-t <seconds: float | None>` default None (:196-203); `--args-json <JSON-object-str | None>` default None (:204-208); `--json-envelope/-j <bool>` default False (:185); `--introspect <CMD: str | None>` default None (:209-216; CMD in `status|contexts|context|tasks|task|delete_context`).

EKB rules:
- IF sending a `--file` script with `--arg k=v` THEN the sim sees `k` as a typed global BECAUSE `_wrap_isolated`/`_inject_args` prepend `k = repr(literal_eval(v))` [verified].
- IF `--raw` is passed THEN parse stdout with `json.loads` and read `body["output"]` + `body["traceback"]` BECAUSE raw mode prints the full envelope as JSON [verified].
- IF two scripts must not share state THEN use default isolation (no `--no-isolate`) BECAUSE the executor shares globals and wrapping scopes each script [probable].
- IF a call may take >60 s THEN raise `--timeout` AND the local `subprocess` timeout together BECAUSE either can fire first (pack uses 120/150 send + 150/180 subprocess) [verified].

LIMITS:
- [verified] Envelope parse contract: `body.get("output","") + "".join(body.get("traceback",[]) or [])`; traceback may be None -> `or []` guard required (a1_run.py).
- [probable] `--file` read with bare `open(args.file)` (no encoding) — non-UTF8-default locales could misread exotic script bytes (source line 248).
- [probable] Exit code is the only machine signal in non-raw mode; pack always uses `--raw` + JSON parse instead.

UNKNOWN (theoretical): retry/backoff behavior on transient failure (zero hiccups observed); `--context` namespace lifetime across sim restarts; `--fire-and-forget` task result retrieval flow beyond `task_id` ACK; max payload size.

## 2. simulation_control.py (bridge library, in-sim)

DOES: [verified] Drives the timeline state machine (play/pause/stop/step) and reports session status. Runs inside the sim via `--file ... --arg action=...`.

Injected globals (knobs; all arrive via `--arg k=v` + literal_eval):
- `action: str` default `"status"` [verified] — one of `status|play|pause|stop|step` (simulation_control.py:27-28; drilled a1_run.py:36-42,48-49). Unknown value prints `ERROR: Unknown action ...` (no exception).
- `num_steps: int` default `1` [verified] — step count for `step`, unit physics steps (simulation_control.py:29-30,93 `int(num_steps)`). Pack uses 60 (a1_run.py:48).
- `dt: float | None` default `None` [probable] — physics timestep, unit seconds; if set with `play`, calls `SimulationManager.setup_simulation(dt=float(dt))` first (simulation_control.py:31-32,67-70). Never drilled in this pack.

Per-action behavior ([verified] unless noted):
- `status`: prints `Simulation state: {PLAYING|PAUSED|STOPPED}` (from `is_playing()/is_paused()`), then `Physics DT`, `Simulation time`, `Physics steps`, `Is simulating`, `Backend`, `Device`, `Physics scenes` (via SimulationManager; failure prints `SimulationManager info: {e}`).
- `play`: `app_utils.play()` + `update_app(steps=5)`; prints `Simulation: PLAYING`.
- `pause`: `app_utils.pause()` + `update_app(steps=2)`; prints `Simulation: PAUSED`.
- `stop`: `app_utils.stop()` + `update_app(steps=5)`; prints `Simulation: STOPPED`.
- `step`: if not playing, `play()` + pump 2 (auto-play); `update_app(steps=int(num_steps))`; prints `Advanced N simulation step(s)` + time/steps.

Knobs + type/unit/default + effect-of-change:
- `action: str = "status"` [verified]: selects transition. Verified cycle STOPPED->PLAYING->PAUSED->STOPPED (A1).
- `num_steps: int = 1`, unit steps [verified]: 60 steps ~= 1.0 sim-second at dt 1/60. Larger N = longer call; keep `--timeout` above it.
- `dt: float | None = None`, unit seconds [probable]: resets physics timestep on play. Changing it changes sim-time-per-step.

EKB rules:
- IF you need N sim-seconds THEN send `action=step --arg num_steps=N*60` at dt 1/60 BECAUSE each update step advances one physics dt [verified].
- IF stepping from STOPPED THEN no prior `play` is needed BECAUSE `step` auto-plays first [verified].
- IF gating sim-time in a transcript THEN match the LAST `Simulation time:` line BECAUSE `status` repeats it and earlier lines are stale (discovery.md) [verified].
- IF a driver ends THEN send `action=stop` last BECAUSE the next drill expects a clean STOPPED handoff [verified].

LIMITS:
- [verified] `step` leaves the sim PLAYING (it auto-played); drivers must explicitly `stop` after (a1_run, v13_run).
- [probable] Sync `update_app` blocks the executor; very large `num_steps` risks client `--timeout` — chunk or raise timeout.
- [probable] `dt` path untested here; `setup_simulation` mid-session may reset sim state.

UNKNOWN (theoretical): behavior of `step` with `num_steps=0`/negative; `pause` from STOPPED; `play` when already PLAYING; multi-scene `status` output shape; non-PhysX backend/device strings.

## 3. open_stage.py (bridge library, in-sim)

DOES: [verified] Stage lifecycle over absolute USD paths: new/open/save/info. Async (`await _run()` at top level).

Injected globals (knobs):
- `action: str` default `"open"` [verified] — `open|new|save|info` (open_stage.py:27-28; drilled a2_run.py:37-43).
- `usd_path: str | None` default `None` [verified] — absolute USD path (open_stage.py:29-30; drilled a2_run.py:39,42). Required for `open` (raises `ValueError` if missing); optional for `save` (absent -> `save_stage()` in place, prints `Stage saved`).
- `template: str` default `"empty"` [probable] — `new` template, options `"empty"|"default"` (open_stage.py:31-32,52). Only default drilled (pack never passes `--arg template=...`).

Per-action behavior ([verified]):
- `open`: `await open_stage_async(usd_path)` + pump 10; success prints `Opened: {path}` + `Stage prims: N`; falsy result prints `ERROR: Failed to open`.
- `new`: `await create_new_stage_async(template=template)` + pump 10; prints `Created new stage (template: {template})`. Wipes authored prims (prim count drops).
- `save` with path: `omni.usd.get_context().save_as_stage(usd_path)` returns bool; prints `Saved as: {path}` or `ERROR: Failed to save`.
- `info`: prints `Stage URL`, `Up axis`, `Units (meters per unit)`, `Prim count`, `Stage loading`; no stage -> `No stage open`.

Knobs + type/unit/default + effect-of-change:
- `usd_path: str | None = None` (absolute path) [verified]: MUST be absolute with forward slashes (`C:/...`). Backslashes/relative paths undrilled.
- `template: str = "empty"` [probable]: `empty` vs `default` changes the fresh-stage prim set; verify_a2 gates on `(template: empty)` (verify_a2.py:13).

EKB rules:
- IF round-tripping a stage THEN sequence `new -> define -> save -> new (wipe) -> open -> check` BECAUSE the middle `new` proves the file (not memory) carries the data [verified].
- IF comparing wipe-vs-loaded THEN gate `Prim count:` pairs strictly ordered (wiped < loaded) BECAUSE any authored prim raises the loaded count [verified].
- IF saving THEN prefer explicit `usd_path` over in-place save BECAUSE `save_as_stage` returns a bool you can gate on [verified].

LIMITS:
- [verified] `open` with missing `usd_path` raises ValueError (traceback in envelope, not a clean ERROR line).
- [probable] `save_as_stage` bool False on bad path/permissions — gate the `Saved as:` string, not silence.
- [probable] `open_stage_async`/`create_new_stage_async` need the post pump (10 steps in source) before counts stabilize.

UNKNOWN (theoretical): `template="default"` prim contents; `save` with no prior filename; `open` of missing/corrupt USD beyond the falsy branch; USD paths with backslashes, relative paths, spaces, non-ASCII; `is_stage_loading` True-window duration.

## 4. stage_info.py (bridge library, in-sim)

DOES: [verified] Inspects stage contents: full tree, type-filtered list, single-prim detail. No stage -> `ERROR: No stage open`.

Injected globals (knobs):
- `mode: str` default `"tree"` [verified] — `tree` (indented hierarchy via `generate_stage_representation`) or `list` (flat paths) (stage_info.py:36-37; drilled a4_run.py:29-31). Unknown -> `ERROR: Unknown mode`.
- `prim_path: str | None` default `None` [verified] — USD prim path; when set, takes over entirely: prints `Path/Type/Active/Applied schemas/Children/Attributes` block (stage_info.py:38-39,55-82; drilled a4_run.py:32). Missing prim -> `ERROR: Prim not found`.
- `filter_type: str | None` default `None` [verified] — exact USD type name, e.g. `Cube`; with `mode=list` located A2Marker (stage_info.py:40-41,121; drilled a4_run.py:30-31). Appends a `--- Filtered prims (type=...) ---` section.
- `max_depth: int | None` default `None` [probable] — depth cap in path levels (`path.count("/")-1 > int(max_depth)` skipped, stage_info.py:42-43,117-119); applies only in the filtered section, NOT the tree/list dump. No pack call site.
- `show_attrs: bool` default `False` [probable] — per-prim attribute dump (values truncated to 100 chars) in the filtered section (stage_info.py:44-45,124-134). No pack call site.
- `exclude_render: bool` default `True` [probable] — strips `/Render` subtree from output (stage_info.py:46-47,86-106,115). No pack call site.

Knobs + type/unit/default + effect-of-change:
- `mode: str = "tree"` + `filter_type: str | None = None` [verified]: `mode=list` + `filter_type=Cube` is the type-query recipe (A4, a4_run.py:30-31).
- `prim_path: str | None = None` [verified]: `/World/...` is the detail recipe (a4_run.py:32); gated on `Path: /World/A2Marker` (verify_a4.py:10).
- `show_attrs: bool = False` [probable]: verbose per-prim dump; large stages -> large transcripts.
- `max_depth: int | None = None`, unit path levels [probable]: `max_depth=1` keeps only root + direct children in filtered section.

EKB rules:
- IF you need one prim's schema/attrs THEN use `prim_path` alone BECAUSE it bypasses tree+filter entirely and prints the detail block [verified].
- IF you need all prims of a type THEN use `mode=list --arg filter_type=<Type>` BECAUSE tree mode has no type filter [verified].
- IF the transcript may contain tree art THEN `open(path, mode, encoding="utf-8")` for BOTH write and read BECAUSE box-drawing chars raise UnicodeEncodeError under cp1252 (failures.md R2) [verified].
- IF gating A4-style THEN split transcript on `"$ send"` and check segment indices BECAUSE each send appends one block [verified].

LIMITS:
- [verified] R2: tree output contains non-cp1252 box-drawing chars; default-locale file IO crashes on Windows.
- [probable] `filter_type` is an exact `GetTypeName()` string match — no subclasses, no wildcards (source line 121).
- [probable] `max_depth` does NOT limit the main tree/list dump, only the filtered section — a full tree of a huge stage is unbounded.
- [probable] Attribute values truncate at 120 chars (detail) / 100 chars (filtered); `<unreadable>` on exception.

UNKNOWN (theoretical): `mode=list` + `exclude_render=False` output volume on production stages; `filter_type` for applied schemas vs type names; prims with non-ASCII paths.

## 5. viewport_screenshot.py (bridge library, in-sim)

DOES: [verified] Captures the viewport to a PNG at `output_path` (1280x720 verified). Reuses Skill 8; works immediately after reopen+step with no extra warm-up.

Injected globals (knobs):
- `output_path: str` default `<tempdir>/viewport_capture.png` [verified via explicit path] — absolute `.png` file path (viewport_screenshot.py:26-27; drilled v13_run.py:44-45). MUST be non-empty and end in `.png` or raises `ValueError` (:29-30).

Behavior ([probable] from source, outcome [verified]): `async _capture() -> None` (viewport_screenshot.py:33, no params) enables `isaacsim.test.utils` if needed (pump 5 after enable), calls `await capture_viewport_screenshot_async(output_path: str [probable]) -> None [probable]` (:49; param str grounded in the `output_path` str, return unobserved), prints `Saved viewport screenshot: {path}`; failure raises `RuntimeError("viewport screenshot capture failed for {path}: {exc}")` (:51).

Knobs + type/unit/default + effect-of-change:
- `output_path: str = <tempdir>/viewport_capture.png` (absolute `.png` path) [verified]: verified 1280x720 non-black via png_stats (V13 9/9).

EKB rules:
- IF capturing after a stage change THEN reopen + step 60 first BECAUSE the step pumps the frame the capture reads (v13_run) [verified].
- IF gating the shot THEN check `SHOT_BYTES > 20000`, `w == 1280 and h == 720`, `mean > 30.0` BECAUSE those together prove present/sized/non-black (verify_v13) [verified].

LIMITS:
- [verified] Only the default 1280x720 PNG drilled; no resolution/format args exist on this script (single-knob tool).
- [probable] `.png` suffix enforced by ValueError; other formats impossible through this script.
- [probable] First call pays an extension-enable + 5-pump cost if `isaacsim.test.utils` is off.

UNKNOWN (theoretical): headless (`--no-window`) capture behavior; capture while PAUSED vs PLAYING vs STOPPED differences; multi-viewport selection; deterministic pixel equality across runs.

## 6. omni.timeline (in-sim API)

DOES: [verified] Direct timeline time control from inside the sim.

Functions used (all params/returns typed; call sites in a1_time.py):
- `omni.timeline.get_timeline_interface() -> <timeline handle> [theoretical: exact class unverified]` [verified] — no params; returns the timeline handle `tl` (a1_time.py:8).
- `tl.set_current_time(seconds: float) -> None [probable: return unobserved]` [verified] — `seconds: float`, unit sim-seconds; requests time 2.5 (a1_time.py:9). DEFERRED: applies on next frame pump, not instantly.
- `tl.get_current_time() -> float` [verified] — no params; returns sim-seconds; exact 2.500 after pump (a1_time.py:11; gated verify_a1.py:16).

Knobs + type/unit/default + effect-of-change:
- `seconds: float` (unit sim-seconds, no default — required arg) [verified]: target time. 2.5 round-trips exact to 1e-6 (verify_a1).

EKB rules:
- IF setting time THEN pump 2 steps between set and get BECAUSE the change is deferred to the next frame update; immediate get returned 0.000 (failures.md R1) [verified].

LIMITS:
- [verified] R1: set-then-immediate-get reads STALE time (0.000). Always pump before get.
- [probable] Only 2.5 drilled; negative/out-of-range times untested.

UNKNOWN (theoretical): minimum pump count (1 vs 2); set while PLAYING vs STOPPED; interaction with `simulation_control step` time advance; time-range clamping.

## 7. isaacsim.core.experimental.utils.app (in-sim API)

DOES: [verified] Pumps the Kit app forward (`update_app`) so deferred changes apply; play/pause/stop/is_* state calls used inside simulation_control.

Functions used (call sites cited; unobserved defaults/returns marked):
- `await app_utils.update_app_async(steps: int = <[unknown] default>) -> None [probable]` [verified] — async pump; `steps: int`, unit app-update iterations (frames-vs-physics [theoretical]); `steps=2` used between timeline set and get (a1_time.py:10; also steps=5 in viewport_screenshot.py:44). No call site omits `steps`, so the default is [unknown]. Return unobserved -> None [probable].
- `app_utils.update_app(steps: int) -> None [probable]` [verified via library] — sync pump; `steps: int` required [probable: always passed explicitly], same unit; steps=2/5/10/N inside simulation_control (simulation_control.py:74,79,84,91,94) and 10 inside open_stage (open_stage.py:43,53).
- `app_utils.play() -> None [probable]` / `pause() -> None [probable]` / `stop() -> None [probable]` [verified via library] — no params; state transitions (simulation_control.py:73,78,83).
- `app_utils.is_playing() -> bool` / `is_paused() -> bool` / `is_stopped() -> bool` [verified via library] — no params; state predicates for `status` (simulation_control.py:37-39; bool grounded in `if playing and not paused` / `elif paused` :41-43).
- `app_utils.is_extension_enabled(name: str) -> bool`, `app_utils.enable_extension(name: str) -> bool` [probable] — `name: str` extension id; used by viewport_screenshot for `isaacsim.test.utils` (viewport_screenshot.py:41-42; bool grounded in the `if not ...` tests).

Knobs + type/unit/default + effect-of-change:
- `steps: int` (unit app-update iterations; async default [unknown], sync required [probable]) [verified]: pump length. 2 suffices for timeline set/get; libraries use 5 (play/stop), 10 (stage ops), N (step count).

EKB rules:
- IF awaiting inside an in-sim snippet THEN use `update_app_async` BECAUSE `--file` scripts run in an async scope supporting top-level `await` [verified].
- IF writing a short library call THEN sync `update_app` is fine BECAUSE the simulation_control pattern does it without deadlock [verified].
- IF a get reads stale after a set THEN insert `update_app_async(steps=2)` between them BECAUSE Kit defers the apply to the next pump (R1) [verified].

LIMITS:
- [verified] 2 pumped steps required between `set_current_time` and `get_current_time` or the get reads stale time.
- [probable] Sync `update_app` with huge N blocks the executor — client timeout risk.

UNKNOWN (theoretical): exact semantics of `steps` (render frames vs physics steps vs both); `is_paused` while STOPPED; `enable_extension` failure modes beyond bool.

## 8. omni.usd + isaacsim stage/prim utils (in-sim API)

DOES: [verified] Stage access for marker/scene authoring and validity checks.

Functions used (call sites cited):
- `omni.usd.get_context() -> <USD context handle> [probable: exact class unverified]` [verified] — no params (a2_check.py:3; a2_marker.py:4; v13_build.py:4; v13_check.py:3).
- `context.get_stage() -> <Usd.Stage | None> [probable]` [verified] — no params (a2_check.py:3; None-case guarded in open_stage.py:71 `if not stage`).
- `context.get_stage_url() -> str` [verified via open_stage info] — no params; returns stage URL string (open_stage.py:76, printed `Stage URL:` line).
- `context.save_as_stage(usd_path: str) -> bool` [verified] — `usd_path: str` absolute path; returns success bool, gated via `Saved as:` (open_stage.py:60-64).
- `stage.GetPrimAtPath(path: str) -> <Usd.Prim> [probable]` [verified] — `path: str` prim path (Sdf.Path overload [theoretical]); returns prim handle; `.IsValid()` gates post-reopen presence (a2_check.py:4; v13_check.py:5; v13_build.py:16).
- `stage_utils.get_current_stage() -> <Usd.Stage | None> [probable]` [probable] — no params; library variant of stage handle (open_stage.py:45,70; stage_info.py:52).
- `stage_utils.get_stage_up_axis() -> <axis token> [theoretical: str vs enum unverified]` [verified via info output] — no params (open_stage.py:77 `Up axis:` line).
- `stage_utils.get_stage_units() -> float [probable]` [verified via info output] — no params; meters per unit (open_stage.py:78,82 `Units (meters per unit):` line).
- `stage_utils.is_stage_loading() -> bool [probable]` [verified via info output] — no params (open_stage.py:84 `Stage loading:` line).
- `stage_utils.open_stage_async(path: str) -> bool [probable]` [verified via behavior] — async; `path: str` absolute USD path; truthy/falsy result gates `Opened:` vs `ERROR: Failed to open` (open_stage.py:42-49).
- `stage_utils.create_new_stage_async(template: str = <[unknown] API default>) -> <unobserved> [unknown]` [verified via behavior] — async; `template: str` in `empty|default` (open_stage.py:52 passes the `template` knob); API-level default unobserved (pack always passes explicitly); return discarded at :52.
- `stage_utils.save_stage() -> <unobserved> [unknown]` [verified via behavior] — no params; in-place save path (open_stage.py:66-67; return discarded).
- `stage_utils.generate_stage_representation(mode: str = "tree" [probable]) -> str` [probable] — `mode: str` in `tree|list`; returns the rendered hierarchy string (stage_info.py:85 passes `mode`; str grounded in `output.split("\n")` :87 and `line.startswith` :92). Default "tree" [probable: matches stage_info default :37].
- `prim_utils.get_prim_at_path(path: str) -> <Usd.Prim | None> [probable]` [probable] — `path: str`; falsy-checked (stage_info.py:56-58).
- `prim_utils.get_prim_attribute_names(path: str) -> list[str] [probable]` [probable] — `path: str`; iterated + `sorted()` + `len()` (stage_info.py:71-74,125-126).
- `prim_utils.get_prim_attribute_value(path: str, name: str) -> Any` [probable] — `path: str`, `name: str` attr name; `repr()`-ed, so Any (stage_info.py:76,128).

Knobs + type/unit/default: `usd_path: str | None = None` (save/open target), `template: str = "empty"` (fresh-stage flavor) — see open_stage (§3).

EKB rules:
- IF gating post-reopen presence THEN use `stage.GetPrimAtPath(p).IsValid()` BECAUSE it returns False (not throw) for missing prims [verified].
- IF authoring markers THEN `Define` + `Set` attrs then `GetPrim().IsValid()` in the same snippet BECAUSE the echo line proves define-time validity (a2_marker) [verified].

LIMITS:
- [probable] `get_stage()` may return None with no stage — `open_stage info` guards with `if not stage`.
- [probable] `save_as_stage` bool is the only success signal; always gate its print.

UNKNOWN (theoretical): `get_stage_url` for unsaved stages; `is_stage_loading` timing; Traverse() cost on huge stages.

## 9. pxr UsdGeom / UsdLux / Gf (in-sim API)

DOES: [verified] Defines the round-trip marker (Cube 0.70 at (1,2,0.35)) and V13 exam scene (Dome 3000 + two Cubes).

Functions used (call sites cited):
- `UsdGeom.Cube.Define(stage: <Usd.Stage> [probable], path: str) -> <UsdGeom.Cube> [probable]` [verified] — defines `/World/A2Marker`, `/World/V13PropA/B` (a2_marker.py:5; v13_build.py:7,11). Return is the Cube schema object (has GetSizeAttr/GetPrim).
- `cube.GetSizeAttr() -> <Usd.Attribute over float> [probable]` [verified] — no params; `.Set(value: float) -> <unobserved> [unknown]` with `value` in stage linear units, meters here (a2_marker.py:6 `0.7`); `.Get() -> float [probable]` meters (a2_marker.py:10 `float()` wrap); size 0.70 survives save/wipe/reopen (A2 8/8, verify_a2.py:14).
- `UsdLux.DomeLight.Define(stage: <Usd.Stage> [probable], path: str) -> <UsdLux.DomeLight> [probable]` [verified] (v13_build.py:5) + `dome.GetIntensityAttr() -> <Usd.Attribute over float> [probable]` (no params) / `.Set(value: float) -> <unobserved> [unknown]` with `value: float` intensity units [theoretical] (v13_build.py:6 `3000.0`) — exam lighting.
- `UsdGeom.Xformable(prim: <Usd.Prim> [probable]) -> <UsdGeom.Xformable> [probable]` [verified] + `.AddTranslateOp() -> <UsdGeom.XformOp> [probable]` (no params) + `op.Set(value: Gf.Vec3d) -> <unobserved> [unknown]` with `value` in stage linear units, meters [probable] — placement (a2_marker.py:7-8; v13_build.py:9-10,13-14).
- `Gf.Vec3d(x: float, y: float, z: float) -> <Gf.Vec3d> [probable]` [verified] — meters (a2_marker.py:8; ints accepted too: v13_build.py:10 `Gf.Vec3d(-0.8, 0, 0.5)` passes int 0).
- `schema.GetPrim() -> <Usd.Prim> [probable]` [verified] — no params (a2_marker.py:9) + `prim.IsValid() -> bool` [verified] — no params; define-time validity echo + post-reopen gate (a2_marker.py:9-10; a2_check.py:5; verify_a2.py:14,20).

Knobs + type/unit/default + effect-of-change:
- `size: float`, unit meters [verified values; USD default [unknown]]: 0.70 marker / 1.0 / 0.6 props (a2_marker.py:6; v13_build.py:8,12). Changing size changes `size=%.2f` echo and filter/type identity (still Cube).
- `intensity: float`, unit intensity [theoretical; default [unknown]] [verified value]: 3000.0 lights the V13 shot (v13_build.py:6); lowering risks the `mean > 30` non-black gate (verify_v13.py:27).
- translate `(x: float, y: float, z: float)`, unit meters [verified values; default [theoretical] (0,0,0)]: (1,2,0.35), (-0.8,0,0.5), (0.9,0.3,0.3) (a2_marker.py:8; v13_build.py:10,14). Placement only; no rotation/scale drilled.

EKB rules:
- IF proving round-trip THEN echo `valid=%s size=%.2f` at define time AND `IsValid()` after reopen BECAUSE the pair separates define-failure from save/load-failure [verified].
- IF lighting an exam shot THEN add a DomeLight at intensity ~3000 BECAUSE the V13 non-black gate depends on it [verified].

LIMITS:
- [probable] Only Cube/DomeLight/translate drilled; rotation/scale ops, other schemas untested here.
- [probable] `AddTranslateOp` appends an op each call — repeated defines on the same prim could stack ops.

UNKNOWN (theoretical): size 0/negative; DomeLight other attrs (exposure, color); Xformable on non-Xformable schemas.

## 10. omni.kit.app extension manager (in-sim API)

DOES: [verified] Proves the bridge's own dependency is enabled; counts loaded extensions. A3 doubles as a bridge self-check (no python_server -> no bridge at all).

Functions used (call sites in a3_probe.py):
- `omni.kit.app.get_app() -> <app handle> [theoretical: exact class unverified]` [verified] — no params (a3_probe.py:5).
- `app.get_extension_manager() -> <extension-manager handle> [theoretical: exact class unverified]` [verified] — no params (a3_probe.py:5).
- `mgr.is_extension_enabled(name: str) -> bool` [verified] — `name: str` extension id, with or without `-version` suffix; `isaacsim.code_editor.python_server` True; `no.such.extension-0.0.0` False (negative control) (a3_probe.py:6-7; gated verify_a3.py:11-12).
- `mgr.get_extensions() -> list [probable: element type [unknown]]` [verified] — no params; sized collection, `len(<ext list>) == 659` on this build (gate is `> 50`) (a3_probe.py:8; verify_a3.py:13).

EKB rules:
- IF the bridge fails to connect THEN check `pyserver=True` first BECAUSE a disabled python_server kills the bridge entirely [verified].
- IF asserting extension state THEN include a bogus-name False control BECAUSE it proves the query path isn't stubbed-True [verified].

LIMITS:
- [verified] Only `is_extension_enabled` + `get_extensions` probed; count 659 is build-specific (gate on `> 50`, not exact).
- [probable] Extension list snapshot cost trivial at 659; larger registries untested.

UNKNOWN (theoretical): `enable_extension/disable_extension` flows; startup-order races (query before registry ready); per-context (headless) extension sets.

## 11. carb.settings (in-sim API)

DOES: [verified] Settings key round-trip probe on a custom key.

Functions used (call sites in a3_probe.py):
- `carb.settings.get_settings() -> <settings handle> [theoretical: exact class unverified]` [verified] — no params (a3_probe.py:9).
- `settings.set(key: str, value: str) -> <unobserved> [unknown]` [verified] — drilled with `("/app/muse_drill_probe", "hello-a3")` (a3_probe.py:10); other value types undrilled; return unobserved.
- `settings.get(key: str) -> str [probable]` [verified] — `key: str`; echoes `hello-a3` (a3_probe.py:11; gated verify_a3.py:14). Return type follows stored type; only str drilled.

EKB rules:
- IF probing settings THEN use a namespaced custom key (`/app/muse_drill_probe`) BECAUSE built-in keys may have validators/side effects [verified].

LIMITS:
- [verified] Only the custom key round-tripped; built-in keys untouched.

UNKNOWN (theoretical): `get` on missing key (None? throw?); type coercion on set; persistence across restart; built-in key side effects.

## 12. isaacsim.core.simulation_manager (in-sim API, via simulation_control)

DOES: [probable] Backend query surface behind `status`: dt, sim time, steps, backend, device, scenes.

Functions used (all [probable] from library source; outputs [verified]; call sites in simulation_control.py):
- `SimulationManager.get_physics_dt() -> float [probable]` — no params; unit seconds; 1/60 this build (simulation_control.py:54).
- `SimulationManager.get_simulation_time() -> float [probable]` — no params; unit sim-seconds; gated LAST line `> 0.5` after 60 steps (simulation_control.py:55,100; verify_a1.py:18-19 parses float).
- `SimulationManager.get_num_physics_steps() -> int [probable]` — no params; unit steps; step counter (simulation_control.py:56,101).
- `SimulationManager.is_simulating() -> bool [probable]` — no params; simulating flag (simulation_control.py:57).
- `SimulationManager.get_backend() -> str [probable]` / `get_device() -> str [probable]` — no params; PhysX/local strings this session (simulation_control.py:58-59).
- `SimulationManager.get_physics_scenes() -> list [probable: element type [unknown]]` — no params; printed only if non-empty (simulation_control.py:60-62).
- `SimulationManager.setup_simulation(dt: float) -> <unobserved> [unknown]` — `dt: float`, unit seconds (simulation_control.py:70 `dt=float(dt)`); dt path undrilled (pack never passes `--arg dt=...`).

EKB rules:
- IF reporting session state THEN print all seven fields BECAUSE dt/time/steps/backend/device/scenes together pin the session config [verified].

LIMITS:
- [probable] All SimulationManager reads wrapped in try/except in `status` — failure degrades to one info line, not a crash.

UNKNOWN (theoretical): `setup_simulation` mid-session effects; multi-scene list shape; non-PhysX backend strings; `is_simulating` vs PLAYING/PAUSED mapping.

## 13. Python stdlib driver stack (local)

DOES: [verified] Local multi-send session flows: each send is one action, transcript is the evidence.

Functions used (call sites in pack drivers/verifiers):
- `subprocess.run(args: list[str], capture_output: bool = True, text: bool = True, timeout: float = 150|180) -> subprocess.CompletedProcess [probable]` [verified] — one bridge call per send; `args` = SEND + per-send args (SEND = `[sys.executable, isaacsim_send.py, --raw, --timeout, 120|150]`); `timeout` unit seconds, int literal passed (a1_run.py:22-23 `timeout=150`; a2_run.py:24-25 `timeout=180`; a4_run.py:20-21; v13_run.py:25-26). Remaining stdlib params at defaults [probable]. Return `.stdout: str` parsed (a1_run.py:24).
- `json.loads(s: str) -> dict [probable: dict for envelope payloads]` [verified] — single positional str (a1_run.py:24; a2_run.py:26; a4_run.py:22; v13_run.py:27). Envelope parse: `body.get("output","") + "".join(body.get("traceback",[]) or [])`.
- `dict.get(key: str, default: Any) -> Any` [verified] — `body.get("output", "") -> str`, `body.get("traceback", []) -> list[str] | None` (None-case needs the `or []` guard) (a1_run.py:25-26).
- `str.join(iterable: list[str]) -> str` [verified] — `"".join(<traceback lines>)` (a1_run.py:25-26).
- `sys.executable: str` [verified] — local interpreter path (value, not a call; a1_run.py:12).
- `os.path.exists(path: str) -> bool` [verified] (a2_run.py:18,45; v13_run.py:19); `os.path.getsize(path: str) -> int` [verified], unit bytes (a2_run.py:46; v13_run.py:47-48); `os.remove(path: str) -> None` [verified] (a2_run.py:19; v13_run.py:20) — USD/PNG pre-clean + exists/size gates.
- `re.search(pattern: str, string: str) -> re.Match | None` [verified] (verify_a1.py:7 `f()`); `re.findall(pattern: str, string: str) -> list[str]` [verified] (LAST sim-time `[-1]` verify_a1.py:19; counts verify_a2.py:10) — verifier gates incl. transition ORDER via `T.index`.
- `open(file: str, mode: str = "r", encoding: str | None = None) -> TextIOWrapper [probable]` [verified] — drilled: `open(path, "w")` default-locale write (a1_run.py:50-51) and `open(path, "w"/read, encoding="utf-8")` (a4_run.py:33-34; verify_a4.py:4-5; v13_run.py:49-50).

Knobs + type/unit/default + effect-of-change:
- send `--timeout: float = 120|150`, unit seconds [verified]: a2/v13 (stage IO + 60 steps) use 150 (a2_run.py:14; v13_run.py:15); a1/a4 use 120 (a1_run.py:15; a4_run.py:13). Raising tolerates slower sim calls.
- `subprocess timeout: int = 150|180`, unit seconds [verified]: always 30 s above the send timeout (a1_run.py:23; a2_run.py:25) so the client timeout fires first with a clean error.
- transcript slice `args[-3:] | args[-2:] | args`, type `list[str]` slice (display-only) [verified]: cosmetic; a2/v13 log last 3 args (a2_run.py:29), a4 last 2 (a4_run.py:25), a1 full (a1_run.py:27).

EKB rules:
- IF driving multi-send flows THEN write LOCAL drivers (not in-sim scripts) BECAUSE each send is one action and the transcript is the evidence (discovery.md) [verified].
- IF writing/reading any transcript that may contain tree art THEN pass `encoding="utf-8"` on BOTH sides BECAUSE cp1252 crashes on box-drawing chars (R2) [verified].
- IF the subprocess timeout fires THEN the send timeout was too low OR the sim hung BECAUSE subprocess (150/180) is set 30 s above send (120/150) [verified].
- IF gating ordered transitions THEN compare `T.index` positions BECAUSE presence alone can't prove cycle ORDER [verified].

LIMITS:
- [verified] a1/a2 reports use default-locale `open(path, "w")` write (a1_run.py:50-51; a2_run.py:47-48) — safe only because their transcripts contain no tree art; a4/v13 use UTF-8.
- [probable] `json.loads(p.stdout)` throws if the bridge prints non-JSON (connection errors go to stderr, so stdout stays parseable — but a crash could still break it).

UNKNOWN (theoretical): optimal timeout margins for loaded machines; concurrent-driver behavior (two local drivers, one sim).

## 14. verify_a1/a2/a3/a4/verify_v13 + png_stats (pack-local evaluators)

DOES: [verified] Local pass/fail gates over evidence transcripts; exit 0 on pass. Suites: A1 7/7, A2 8/8, A3 4/4, A4 4/4, V13 9/9.

Functions + signatures (helpers fully typed):
- `verify_a1.py` [verified]: script (no callable signature); `T: str` transcript (verify_a1.py:4); gates STOPPED/PLAYING/PAUSED seen + cycle ORDER (`T.index`) + `TIME-SET-GET 2.5` (1e-6) + `Advanced 60 simulation step(s)` + LAST `Simulation time > 0.5`. Helper `f(pat: str, i: int = 1) -> float` (verify_a1.py:6-8; returns float or nan; called :16).
- `verify_a2.py` [verified]: same helper `f(pat: str, i: int = 1) -> float` (verify_a2.py:6-8); gates `Created new stage (template: empty)` + `A2-MARKER valid=True size=0.70` + `Saved as:` + `USD_EXISTS=True` + `USD_BYTES > 0` + wipe-shrinks (`len(counts)==2 and counts[0] < counts[1]`, `counts: list[int]` :10) + `Opened:` + `A2-CHECK valid=True`.
- `verify_a3.py` [verified]: helper `f(pat: str, i: int = 1) -> float` (verify_a3.py:6-8); reads `evidence/a3_run.json["output"]` (`R: str`, :4; JSON envelope, not txt) — gates `pyserver=True` + `bogus=False` + `count > 50` + `echo=hello-a3`.
- `verify_a4.py` [verified]: no helper; UTF-8 read (`T: str`, verify_a4.py:4-5); gates per-`$ send` segment (`A2Marker` in [1], `/World/A2Marker` in [2], `Path: /World/A2Marker` in [3]) + `ERROR not in T`.
- `verify_v13.py` [verified]: helper `f(pat: str, i: int = 1) -> float` (verify_v13.py:12-14); UTF-8 read + `png_stats(shot)` (`shot: str` path, `s: dict`, :16-17); gates built/saved/reopened/props-survive/stepped-60 + `SHOT_BYTES > 20000` + `w==1280 and h==720` + `mean > 30.0` + `ends stopped` (third-from-last line `== "Simulation: STOPPED"`).
- `png_stats.png_stats(path: str) -> dict` [verified]: stdlib PNG parse (IHDR w/h, IDAT inflate, filter reversal); `path: str` file path (verify_v13.py:16-17); returns `{"w": int (px), "h": int (px), "mean": float (0-255 levels), "std": float (levels), "bytes": int (file bytes), "raw": bytes (RGB[A] pixels), "ch": int (3|4)}` (png_stats.py:20,78-79; `s["w"]/s["h"]/s["mean"]` gated verify_v13.py:26-27). Asserts 8-bit ctype 2/6.
- `png_stats.mean_abs_diff(a_path: str, b_path: str) -> float` [probable]: `a_path/b_path: str` PNG paths; returns mean abs RGB diff in 0-255 levels (png_stats.py:82-92); asserts equal size. No pack call site. CLI: `stats <png: str>` / `diff <a_png: str> <b_png: str>` via `main() -> None` (no params, png_stats.py:95-109); UNUSED by this pack's verifiers.

Knobs + type/unit/default + effect-of-change:
- Thresholds [verified]: `1e-6: float` (seconds tolerance, verify_a1.py:16); `0.5: float` (sim-seconds, verify_a1.py:18-19); `20000: int` (bytes, verify_v13.py:25); `30.0: float` (0-255 levels, verify_v13.py:27); `50.0: float` (count compare vs `count: int`, verify_a3.py:13); `counts[0] < counts[1]: list[int]` (prim counts, verify_a2.py:10,18). Tightening risks flakes; loosening risks false-pass.

EKB rules:
- IF verifying A3 THEN read `a3_run.json["output"]`, not a txt transcript BECAUSE a3_probe output was saved as the raw envelope [verified].
- IF gating "ends stopped" THEN check the third-from-last stripped line BECAUSE two `*_BYTES` lines are appended after the final stop [verified].
- IF checking non-black THEN use `mean > 30.0` (not `> 0`) BECAUSE near-black noise floors need margin [verified].

LIMITS:
- [verified] `verify_a1` time gate is exact (1e-6) — any pump regression fails loudly.
- [probable] `png_stats` supports 8-bit truecolor/truecolor+alpha ONLY; other PNGs assert-fail.
- [probable] `verify_a4` segment indices assume exactly 3 sends in order — adding a query shifts gates.

UNKNOWN (theoretical): png_stats performance on 4K+ shots; `mean_abs_diff` threshold for "same scene" (unused here); flake rate of exact-float gates across builds.

## Sources-read (all full)

- README.md (no SKILL.md present), failures.md (R1-R2), discovery.md, TOOLS.md
- Pack scripts (15): a1_run, a1_time, a2_run, a2_marker, a2_check, a3_probe, a4_run, v13_build, v13_check, v13_run, verify_a1, verify_a2, verify_a3, verify_a4, verify_v13
- Bridge library (6): isaacsim_send, simulation_control, open_stage, stage_info, viewport_screenshot, png_stats
